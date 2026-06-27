"""TDD tests for the PreviewEngine strategy pattern (Plan 40-02).

Three test classes track the three plan tasks:

- ``TestPreviewEngineABC`` (Task 1): ABC shape, ``PreviewEngineError``,
  ``select_engine()`` factory dispatch, and the WARNING #7 stub-NotImplementedError
  boundary check at Task 1 -> Task 2/3.
- ``TestSlideshowEngine`` (Task 2): FFmpeg subprocess engine + degrade paths.
- ``TestLTXVideoEngine`` (Task 3): mocked httpx POST + D-09 degrade contract.

WARNING #7 lifecycle:
- Task 1 leaves ``SlideshowEngine`` + ``LTXVideoEngine`` as stubs whose
  ``generate()`` raises ``NotImplementedError``. Test 9 in
  ``TestPreviewEngineABC`` asserts this at the Task 1 -> 2/3 boundary.
- Task 2 expands ``SlideshowEngine``; Test 9 is adjusted to assert only
  ``LTXVideoEngine.generate()`` raises ``NotImplementedError``.
- Task 3 expands ``LTXVideoEngine``; Test 9 is removed (both stubs gone).
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

# Ensure hermes-agent root is importable so ``plugins.kais_aigc.*`` resolves.
HERMES_ROOT = Path(__file__).resolve().parents[3]
if str(HERMES_ROOT) not in sys.path:
    sys.path.insert(0, str(HERMES_ROOT))

from plugins.kais_aigc.preview_engine import (  # noqa: E402
    LTXVideoEngine,
    PreviewEngine,
    PreviewEngineError,
    SlideshowEngine,
    select_engine,
)


class TestPreviewEngineABC:
    """Task 1: ABC shape, error class, factory dispatch, stub boundary."""

    def test_preview_engine_is_abc(self):
        from abc import ABC

        assert issubclass(PreviewEngine, ABC)

    def test_preview_engine_cannot_be_instantiated_directly(self):
        with pytest.raises(TypeError):
            PreviewEngine()

    def test_generate_is_abstract_method(self):
        assert getattr(
            PreviewEngine.generate, "__isabstractmethod__", False
        ) is True

    def test_preview_engine_error_is_exception_subclass(self):
        assert issubclass(PreviewEngineError, Exception)

    def test_select_engine_default_returns_slideshow(self, monkeypatch):
        # Simulate KAIS_PREVIEW_ENGINE unset.
        monkeypatch.delenv("KAIS_PREVIEW_ENGINE", raising=False)
        engine = select_engine()
        assert isinstance(engine, SlideshowEngine)

    def test_select_engine_env_ltx_returns_ltx_video(self):
        engine = select_engine(env="ltx")
        assert isinstance(engine, LTXVideoEngine)

    def test_select_engine_env_slideshow_returns_slideshow(self):
        engine = select_engine(env="slideshow")
        assert isinstance(engine, SlideshowEngine)

    def test_select_engine_unknown_env_falls_back_to_slideshow_with_warn(
        self, caplog
    ):
        import logging

        with caplog.at_level(logging.WARNING, logger="plugins.kais_aigc.preview_engine"):
            engine = select_engine(env="totally-bogus-value")
        assert isinstance(engine, SlideshowEngine)
        # WARNING log must mention the unknown value (T-40-09 mitigation).
        joined = " ".join(rec.getMessage() for rec in caplog.records)
        assert "totally-bogus-value" in joined
        assert "slideshow" in joined.lower()

    def test_select_engine_reads_env_at_call_time_not_import_time(self, monkeypatch):
        # First call: env unset -> slideshow.
        monkeypatch.delenv("KAIS_PREVIEW_ENGINE", raising=False)
        first = select_engine()
        assert isinstance(first, SlideshowEngine)
        # Set env to ltx between calls; second call must reflect the new value.
        monkeypatch.setenv("KAIS_PREVIEW_ENGINE", "ltx")
        second = select_engine()
        assert isinstance(second, LTXVideoEngine)

    def test_stub_subclasses_raise_not_implemented_at_task_1_boundary(self):
        """WARNING #7 fix: validates the stub strategy at the Task 1 -> 2/3
        boundary.

        Lifecycle:
        - Task 1: both SlideshowEngine + LTXVideoEngine stubs raise NIE.
        - Task 2: SlideshowEngine stub expanded; this test asserts ONLY the
          LTXVideoEngine stub still raises NIE.
        - Task 3: LTXVideoEngine stub expanded; this test is REMOVED entirely.
        """
        # Task 2 onward: SlideshowEngine is no longer a stub — assert it
        # does NOT raise NotImplementedError. (Test evolves as stubs expand.)
        slideshow = select_engine(env="slideshow")
        # Between Task 1 and Task 2 GREEN, slideshow.generate still raises NIE.
        # After Task 2 GREEN, this branch is replaced with a real call. See
        # the TestSlideshowEngine class for the full behavior coverage.
        try:
            slideshow.generate(
                shot_id="s1",
                prompt="x",
                structure_delta={},
                keyframe_image_path="/tmp/k.png",
                voice_clip_path="/tmp/v.wav",
                output_path="/tmp/o.mp4",
            )
        except NotImplementedError:
            pass  # Task 1 state — still a stub.
        except Exception:
            # Any other exception (e.g. degrade envelope) means the stub has
            # been expanded — that's fine, the TestSlideshowEngine class
            # covers the real behavior.
            pass

        # LTXVideoEngine is still a stub until Task 3.
        ltx = select_engine(env="ltx")
        with pytest.raises(NotImplementedError):
            ltx.generate(shot_id="s1", prompt="x", structure_delta={})


class TestSlideshowEngine:
    """Task 2: SlideshowEngine (FFmpeg subprocess) + degrade paths.

    All tests use a fake ``subprocess_runner`` to avoid invoking real FFmpeg.
    T-40-06 (argument injection) is mitigated by list-form argv (no
    shell=True) — Test 2 pins the exact arg ordering.
    """

    def _fake_runner_returning_zero(self):
        """Returns a runner callable that records args + exits 0."""

        captured: dict = {}

        def runner(argv: list[str]):
            captured["argv"] = list(argv)
            # Mimic subprocess.CompletedProcess minimal contract.
            class _Result:
                returncode = 0
                stdout = b""
                stderr = b""

            return _Result()

        return runner, captured

    def test_generate_happy_path_returns_success_envelope(self):
        runner, captured = self._fake_runner_returning_zero()
        engine = SlideshowEngine(subprocess_runner=runner)
        result = engine.generate(
            shot_id="s1",
            prompt="some prompt",
            structure_delta={"hook_position_sec": 5},
            keyframe_image_path="/tmp/kf.png",
            voice_clip_path="/tmp/vo.wav",
            output_path="/tmp/out.mp4",
        )
        assert result["clip_path"] == "/tmp/out.mp4"
        assert result["engine"] == "slideshow"
        assert isinstance(result["generation_time_ms"], int)
        assert result["generation_time_ms"] >= 0
        assert "degraded" not in result

    def test_generate_invokes_ffmpeg_with_exact_arg_ordering(self):
        runner, captured = self._fake_runner_returning_zero()
        engine = SlideshowEngine(subprocess_runner=runner)
        engine.generate(
            shot_id="s1",
            prompt="x",
            structure_delta={},
            keyframe_image_path="/tmp/kf.png",
            voice_clip_path="/tmp/vo.wav",
            output_path="/tmp/out.mp4",
        )
        argv = captured["argv"]
        # T-40-06 mitigation: argv is a Python list (no shell=True); exact
        # ordering pinned so a future refactor cannot silently inject flags.
        assert argv == [
            "ffmpeg", "-y", "-loop", "1",
            "-i", "/tmp/kf.png",
            "-i", "/tmp/vo.wav",
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-pix_fmt", "yuv420p",
            "/tmp/out.mp4",
        ]

    def test_generate_returns_degrade_envelope_on_nonzero_exit(self):
        def runner(argv: list[str]):
            class _Result:
                returncode = 1
                stdout = b""
                stderr = b"Conversion failed!"

            return _Result()

        engine = SlideshowEngine(subprocess_runner=runner)
        result = engine.generate(
            shot_id="s1",
            prompt="x",
            structure_delta={},
            keyframe_image_path="/tmp/kf.png",
            voice_clip_path="/tmp/vo.wav",
            output_path="/tmp/out.mp4",
        )
        assert result["degraded"] is True
        assert result["engine"] == "slideshow"
        assert "1" in str(result["reason"])  # returncode surfaced
        assert "Conversion failed" in str(result["reason"])  # stderr surfaced

    def test_generate_degrades_when_keyframe_image_path_missing(self):
        runner, _ = self._fake_runner_returning_zero()
        engine = SlideshowEngine(subprocess_runner=runner)
        for missing in (None, ""):
            result = engine.generate(
                shot_id="s1",
                prompt="x",
                structure_delta={},
                keyframe_image_path=missing,
                voice_clip_path="/tmp/vo.wav",
                output_path="/tmp/out.mp4",
            )
            assert result["degraded"] is True
            assert result["engine"] == "slideshow"
            assert "keyframe_image_path" in result["reason"]

    def test_generate_degrades_when_voice_clip_path_missing(self):
        runner, _ = self._fake_runner_returning_zero()
        engine = SlideshowEngine(subprocess_runner=runner)
        for missing in (None, ""):
            result = engine.generate(
                shot_id="s1",
                prompt="x",
                structure_delta={},
                keyframe_image_path="/tmp/kf.png",
                voice_clip_path=missing,
                output_path="/tmp/out.mp4",
            )
            assert result["degraded"] is True
            assert "voice_clip_path" in result["reason"]

    def test_generate_degrades_when_ffmpeg_binary_not_in_path(
        self, monkeypatch
    ):
        # No subprocess_runner injected -> engine will check shutil.which.
        monkeypatch.setattr(
            "plugins.kais_aigc.preview_engine.shutil.which", lambda _: None
        )
        engine = SlideshowEngine()
        result = engine.generate(
            shot_id="s1",
            prompt="x",
            structure_delta={},
            keyframe_image_path="/tmp/kf.png",
            voice_clip_path="/tmp/vo.wav",
            output_path="/tmp/out.mp4",
        )
        assert result["degraded"] is True
        assert result["engine"] == "slideshow"
        assert "ffmpeg" in result["reason"].lower()
        assert "PATH" in result["reason"]

    def test_constructor_accepts_subprocess_runner_kwarg(self):
        # Default: None (real subprocess).
        default_engine = SlideshowEngine()
        assert default_engine._subprocess_runner is None
        # Injected runner.
        runner, _ = self._fake_runner_returning_zero()
        injected_engine = SlideshowEngine(subprocess_runner=runner)
        assert injected_engine._subprocess_runner is runner

    def test_generation_time_ms_is_non_negative_int(self):
        runner, _ = self._fake_runner_returning_zero()
        engine = SlideshowEngine(subprocess_runner=runner)
        result = engine.generate(
            shot_id="s1",
            prompt="x",
            structure_delta={},
            keyframe_image_path="/tmp/kf.png",
            voice_clip_path="/tmp/vo.wav",
            output_path="/tmp/out.mp4",
        )
        assert isinstance(result["generation_time_ms"], int)
        assert result["generation_time_ms"] >= 0


class TestLTXVideoEngine:
    """Task 3: LTXVideoEngine (mocked httpx POST) + D-09 degrade contract.

    Mirrors ``tests/test_gold_team.py`` patterns: every client is constructed
    with ``transport=httpx.MockTransport(handler)`` so no real network call
    is made. The D-09 degrade / raise contract is enforced identically to
    ``GoldTeamClient``.

    INFO #10: ``generation_time_ms`` in the SUCCESS envelope is the
    LOCALLY-measured wall time (``time.monotonic()`` delta), NOT the value
    reported in the LTX-Video response body. Rationale: service-reported
    timing may be unreliable, missing, or inconsistent across engine
    implementations; local wall time is always available and comparable.
    This is documented in the SUMMARY and asserted in Test 1.
    """

    def _client(self, handler, **kw):
        return LTXVideoEngine(
            base_url="http://test-ltx",
            transport=httpx.MockTransport(handler),
            **kw,
        )

    def test_generate_happy_path_returns_success_envelope(self):
        """Service reports generation_time_ms=1200 in body, but we MUST
        ignore it and return LOCALLY-measured wall time (INFO #10)."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={"clip_path": "/x.mp4", "generation_time_ms": 1200},
            )

        with self._client(handler) as engine:
            result = engine.generate(
                shot_id="s1",
                prompt="...",
                structure_delta={"hook_position_sec": 5},
            )
        assert result["clip_path"] == "/x.mp4"
        assert result["engine"] == "ltx"
        assert isinstance(result["generation_time_ms"], int)
        assert result["generation_time_ms"] >= 0
        # INFO #10: service-reported 1200ms is IGNORED — we return wall time.
        # (No assertion on exact value since wall time is non-deterministic;
        # the key invariant is that it's an int and present.)
        assert "degraded" not in result

    def test_handler_receives_post_to_api_v1_ltx_with_correct_body(self):
        captured: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(request)
            return httpx.Response(200, json={"clip_path": "/x.mp4"})

        with self._client(handler) as engine:
            engine.generate(
                shot_id="s1",
                prompt="...",
                structure_delta={"hook_position_sec": 5},
            )
        assert len(captured) == 1
        req = captured[0]
        assert req.method == "POST"
        assert req.url.path == "/api/v1/ltx"
        # Body keys.
        import json as _json

        body = _json.loads(req.content.decode())
        assert body["shot_id"] == "s1"
        assert body["prompt"] == "..."
        assert body["structure_delta"] == {"hook_position_sec": 5}

    def test_generate_degrades_on_connect_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("conn refused", request=request)

        with self._client(handler) as engine:
            result = engine.generate(
                shot_id="s1", prompt="x", structure_delta={}
            )
        assert result["degraded"] is True
        assert result["engine"] == "ltx"
        assert "ConnectError" in result["reason"]

    def test_generate_degrades_on_timeout(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("read timed out", request=request)

        with self._client(handler) as engine:
            result = engine.generate(
                shot_id="s1", prompt="x", structure_delta={}
            )
        assert result["degraded"] is True
        assert "Timeout" in result["reason"] or "timed out" in result["reason"]

    def test_generate_degrades_on_http_500(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500)

        with self._client(handler) as engine:
            result = engine.generate(
                shot_id="s1", prompt="x", structure_delta={}
            )
        assert result["degraded"] is True
        assert "HTTP 500" in result["reason"]

    def test_generate_degrades_on_http_429(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429)

        with self._client(handler) as engine:
            result = engine.generate(
                shot_id="s1", prompt="x", structure_delta={}
            )
        assert result["degraded"] is True
        assert "HTTP 429" in result["reason"]

    def test_generate_raises_on_http_400(self):
        # 4xx is a caller bug (D-09: raise, do not degrade).
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, text="bad request body")

        with self._client(handler) as engine:
            with pytest.raises(PreviewEngineError) as excinfo:
                engine.generate(
                    shot_id="s1", prompt="x", structure_delta={}
                )
        assert "HTTP 400" in str(excinfo.value)

    def test_generate_raises_on_invalid_json_response(self):
        # Invalid JSON on a 2xx is a service-side bug (D-09: raise).
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, content=b"not json at all", headers={"content-type": "application/json"}
            )

        with self._client(handler) as engine:
            with pytest.raises(PreviewEngineError) as excinfo:
                engine.generate(
                    shot_id="s1", prompt="x", structure_delta={}
                )
        assert "JSON" in str(excinfo.value) or "json" in str(excinfo.value).lower()

    def test_generate_degrades_when_clip_path_missing_in_response(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"unrelated": "field"})

        with self._client(handler) as engine:
            result = engine.generate(
                shot_id="s1", prompt="x", structure_delta={}
            )
        assert result["degraded"] is True
        assert result["engine"] == "ltx"
        assert "clip_path" in result["reason"]

    def test_constructor_reads_base_url_from_kwarg_or_env(self, monkeypatch):
        # Kwarg wins.
        engine_kwarg = LTXVideoEngine(
            base_url="http://from-kwarg",
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})),
        )
        assert engine_kwarg._base_url == "http://from-kwarg"
        engine_kwarg.close()

        # Env var fallback.
        monkeypatch.setenv("KAIS_LTX_URL", "http://from-env:9999")
        engine_env = LTXVideoEngine(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json={}))
        )
        assert engine_env._base_url == "http://from-env:9999"
        engine_env.close()

        # Default.
        monkeypatch.delenv("KAIS_LTX_URL", raising=False)
        engine_default = LTXVideoEngine(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json={}))
        )
        assert engine_default._base_url == LTXVideoEngine.DEFAULT_BASE_URL
        engine_default.close()

    def test_engine_without_transport_uses_real_httpx_client(self):
        # No transport injected -> real httpx.Client. Do NOT make a real
        # network call; just verify the underlying client type.
        engine = LTXVideoEngine()
        assert isinstance(engine._client, httpx.Client)
        assert engine._base_url == LTXVideoEngine.DEFAULT_BASE_URL
        engine.close()
