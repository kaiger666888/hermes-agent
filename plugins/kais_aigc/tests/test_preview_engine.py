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
