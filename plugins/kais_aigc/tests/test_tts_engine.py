"""TDD tests for the TTSEngine in-process adapter (P1-3).

Mirrors ``tests/test_preview_engine.py`` patterns: every engine is constructed
with ``transport=httpx.MockTransport(handler)`` so no real network call is made,
and FFmpeg/docker steps use an injected ``subprocess_runner``. The D-09
degrade / raise contract is enforced identically to ``LTXVideoEngine``.

Coverage:
- ``TestTTSEngineContract`` — error class, factory, base URL resolution, CM.
- ``TestTTSEngineDesignVoice`` — Phase 1 happy path + body shape + OOM guard.
- ``TestTTSEngineCloneVoice`` — Phase 2 happy path + mute hard gate + flac→wav.
- ``TestTTSEngineD09`` — 4xx raise / 5xx degrade / timeout degrade / 429.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx
import pytest

# Ensure hermes-agent root is importable so ``plugins.kais_aigc.*`` resolves.
HERMES_ROOT = Path(__file__).resolve().parents[3]
if str(HERMES_ROOT) not in sys.path:
    sys.path.insert(0, str(HERMES_ROOT))

from plugins.kais_aigc.tts_engine import (  # noqa: E402
    MAX_INSTRUCT_CHARS,
    IndexTTS25Engine,
    TTSEngine,
    TTSEngineError,
    select_tts_engine,
)


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class _Result:
    """Minimal subprocess.CompletedProcess-like for the runner seam."""

    def __init__(self, returncode=0, stdout=b"", stderr=b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _speak_handler(*, design_url="/files/design.flac", clone_url="/files/clone.flac",
                   captured=None):
    """Build a MockTransport handler that serves POST /speak + GET /files/*.

    Records POST bodies into ``captured`` (if given) as a list of dicts.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path == "/api/v1/tts/speak":
            body = json.loads(request.content.decode())
            if captured is not None:
                captured.append(body)
            url = design_url if body.get("mode") == "voice_design" else clone_url
            return httpx.Response(200, json={"audio_url": url})
        if request.method == "GET" and request.url.path.startswith("/files/"):
            return httpx.Response(200, content=b"FAKE_FLAC_BYTES")
        return httpx.Response(404, text="not found")

    return handler


def _ffmpeg_runner(mean_volume=-23.4, convert_rc=0, volumedetect_rc=0, calls=None):
    """Fake subprocess_runner that records argv + returns canned FFmpeg output.

    Routes by argv content: ``volumedetect`` -> analysis stderr; otherwise the
    flac→wav conversion. ``calls`` (if a list) accumulates every argv seen.
    """

    def runner(argv: list[str]):
        if calls is not None:
            calls.append(list(argv))
        if "volumedetect" in argv:
            stderr = f"[Parsed_volumedetect_0 @ 0x...] mean_volume: {mean_volume} dB\n"
            return _Result(volumedetect_rc, b"", stderr.encode())
        # flac->wav conversion (or docker cp when argv[0]=='docker')
        return _Result(convert_rc, b"", b"")

    return runner


def _engine(handler=None, *, runner=None, comfyui_input_dir=None, **kw):
    return TTSEngine(
        base_url="http://test-tts",
        transport=httpx.MockTransport(handler or _speak_handler()),
        subprocess_runner=runner,
        comfyui_input_dir=comfyui_input_dir,
        **kw,
    )


# ---------------------------------------------------------------------------
# Contract / factory / lifecycle
# ---------------------------------------------------------------------------


class TestTTSEngineContract:
    def test_tts_engine_error_is_exception_subclass(self):
        assert issubclass(TTSEngineError, Exception)

    def test_default_base_url_and_timeout(self):
        eng = TTSEngine(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})))
        assert eng._base_url == TTSEngine.DEFAULT_BASE_URL
        assert eng._timeout == TTSEngine.DEFAULT_TIMEOUT
        eng.close()

    def test_base_url_kwarg_wins_over_env(self, monkeypatch):
        monkeypatch.setenv("KAIS_TTS_URL", "http://from-env:9999")
        eng = TTSEngine(base_url="http://from-kwarg",
                        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})))
        assert eng._base_url == "http://from-kwarg"
        eng.close()

    def test_base_url_env_fallback(self, monkeypatch):
        monkeypatch.setenv("KAIS_TTS_URL", "http://from-env:9999/")
        eng = TTSEngine(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})))
        assert eng._base_url == "http://from-env:9999"  # trailing slash stripped
        eng.close()

    def test_select_tts_engine_returns_tts_engine(self, monkeypatch):
        # v15.3 (2026-08-16): default engine is IndexTTS25Engine (VoiceDesign→
        # IndexTTS 2.5 via KAP). Explicit qwen_tts still yields TTSEngine.
        monkeypatch.delenv("KAIS_COMFYUI_INPUT_DIR", raising=False)
        monkeypatch.delenv("KAIS_TTS_ENGINE", raising=False)
        eng = select_tts_engine()
        assert isinstance(eng, IndexTTS25Engine)
        eng.close()
        qwen = select_tts_engine(env="qwen_tts")
        assert isinstance(qwen, TTSEngine)
        qwen.close()

    def test_select_tts_engine_unknown_env_warns_and_falls_back(self, caplog, monkeypatch):
        import logging
        # v15.3: unknown env falls back to the DEFAULT (IndexTTS25Engine).
        monkeypatch.delenv("KAIS_COMFYUI_INPUT_DIR", raising=False)
        with caplog.at_level(logging.WARNING, logger="plugins.kais_aigc.tts_engine"):
            eng = select_tts_engine(env="totally-bogus")
        assert isinstance(eng, IndexTTS25Engine)
        joined = " ".join(rec.getMessage() for rec in caplog.records)
        assert "totally-bogus" in joined
        eng.close()

    def test_context_manager_closes_client(self):
        with TTSEngine(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={}))) as eng:
            assert eng._client.is_closed is False
        assert eng._client.is_closed is True

    def test_context_manager_closes_on_exception(self):
        with pytest.raises(RuntimeError, match="boom"):
            with TTSEngine(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={}))) as eng:
                raise RuntimeError("boom")
        assert eng._client.is_closed is True


# ---------------------------------------------------------------------------
# Phase 1 — design_voice
# ---------------------------------------------------------------------------


class TestTTSEngineDesignVoice:
    def test_design_voice_happy_path_returns_ref_envelope(self, tmp_path):
        captured = []
        with _engine(_speak_handler(captured=captured),
                     runner=_ffmpeg_runner(),
                     comfyui_input_dir=str(tmp_path)) as eng:
            result = eng.design_voice(
                char="阿毛", ref_line="你好世界", instruct="约5岁男童", seed=42,
                ref_dir=str(tmp_path),
            )
        assert "degraded" not in result
        assert result["engine"] == "Qwen3-TTS-1.7B"
        assert result["ref_audio"] == "ref_阿毛.flac"
        assert isinstance(result["generation_time_ms"], int)
        # Local ref FLAC persisted.
        assert Path(result["ref_local"]).is_file()
        # Published into the shared comfyui input dir.
        assert (tmp_path / "ref_阿毛.flac").is_file()

    def test_design_voice_posts_voice_design_body_verbatim(self, tmp_path):
        captured = []
        with _engine(_speak_handler(captured=captured),
                     runner=_ffmpeg_runner(),
                     comfyui_input_dir=str(tmp_path)) as eng:
            eng.design_voice(char="amao", ref_line="REF", instruct="short", seed=42,
                             ref_dir=str(tmp_path))
        assert len(captured) == 1
        body = captured[0]
        assert body["mode"] == "voice_design"
        assert body["text"] == "REF"
        assert body["instruct"] == "short"
        assert body["seed"] == 42
        assert body["unload_model_after_generate"] is True

    def test_design_voice_degrades_on_long_instruct_oom_guard(self, tmp_path):
        long_instruct = "x" * (MAX_INSTRUCT_CHARS + 1)
        with _engine(runner=_ffmpeg_runner()) as eng:
            result = eng.design_voice(char="c", ref_line="r", instruct=long_instruct,
                                      seed=1, ref_dir=str(tmp_path))
        assert result["degraded"] is True
        # Must mention the OOM / length rationale.
        assert "instruct" in result["reason"]
        assert "OOM" in result["reason"] or str(MAX_INSTRUCT_CHARS) in result["reason"]

    def test_design_voice_degrades_on_missing_audio_url(self, tmp_path):
        def handler(request):
            if request.method == "POST":
                return httpx.Response(200, json={"audio_path": "/container/internal.flac"})
            return httpx.Response(404)
        with _engine(handler, runner=_ffmpeg_runner()) as eng:
            result = eng.design_voice(char="c", ref_line="r", instruct="ok", seed=1,
                                      ref_dir=str(tmp_path))
        assert result["degraded"] is True
        assert "audio_url" in result["reason"]


# ---------------------------------------------------------------------------
# Phase 2 — clone_voice + mute hard gate
# ---------------------------------------------------------------------------


class TestTTSEngineCloneVoice:
    def test_clone_voice_happy_path_returns_audio_envelope(self, tmp_path):
        out = str(tmp_path / "S01.wav")
        calls = []
        with _engine(_speak_handler(), runner=_ffmpeg_runner(calls=calls)) as eng:
            result = eng.clone_voice(
                text="你好", ref_audio="ref_阿毛.flac", ref_text="REF", seed=42,
                out_wav=out,
            )
        assert "degraded" not in result
        assert result["audio_path"] == out
        assert result["engine"] == "Qwen3-TTS-1.7B"
        assert isinstance(result["mean_volume"], float)
        assert result["mean_volume"] == -23.4

    def test_clone_voice_posts_voice_clone_body_verbatim(self, tmp_path):
        captured = []
        out = str(tmp_path / "S01.wav")
        with _engine(_speak_handler(captured=captured), runner=_ffmpeg_runner()) as eng:
            eng.clone_voice(text="DIALOGUE", ref_audio="ref_c.flac", ref_text="REF",
                            seed=7, out_wav=out)
        assert len(captured) == 1
        body = captured[0]
        assert body["mode"] == "voice_clone"
        assert body["text"] == "DIALOGUE"
        assert body["ref_audio"] == "ref_c.flac"
        assert body["ref_text"] == "REF"
        assert body["seed"] == 7

    def test_clone_voice_flac_to_wav_argv_is_list_form(self, tmp_path):
        # T-40-06: argv is a Python list (no shell=True); pin the exact flags.
        out = str(tmp_path / "S01.wav")
        calls = []
        with _engine(_speak_handler(), runner=_ffmpeg_runner(calls=calls)) as eng:
            eng.clone_voice(text="t", ref_audio="r.flac", ref_text="rt", seed=1,
                            out_wav=out)
        convert_calls = [c for c in calls if "volumedetect" not in c and c[0] == "ffmpeg"]
        assert len(convert_calls) == 1
        argv = convert_calls[0]
        assert argv == [
            "ffmpeg", "-y", "-i", out + ".flac",
            "-ar", "24000", "-ac", "1", out,
        ]

    def test_clone_voice_mute_hard_gate_degrades(self, tmp_path):
        # mean_volume well below the -80 dB silence threshold -> degrade.
        out = str(tmp_path / "S01.wav")
        with _engine(_speak_handler(),
                     runner=_ffmpeg_runner(mean_volume=-91.0)) as eng:
            result = eng.clone_voice(text="t", ref_audio="r.flac", ref_text="rt",
                                     seed=1, out_wav=out)
        assert result["degraded"] is True
        assert "silent" in result["reason"]
        assert "-91" in result["reason"]

    def test_clone_voice_boundary_mean_volume_ok(self, tmp_path):
        # Exactly at the threshold boundary (> -80 is OK); use -79.9.
        out = str(tmp_path / "S01.wav")
        with _engine(_speak_handler(),
                     runner=_ffmpeg_runner(mean_volume=-79.9)) as eng:
            result = eng.clone_voice(text="t", ref_audio="r.flac", ref_text="rt",
                                     seed=1, out_wav=out)
        assert "degraded" not in result
        assert result["mean_volume"] == -79.9

    def test_clone_voice_degrades_on_ffmpeg_convert_failure(self, tmp_path):
        out = str(tmp_path / "S01.wav")
        with _engine(_speak_handler(),
                     runner=_ffmpeg_runner(convert_rc=1)) as eng:
            result = eng.clone_voice(text="t", ref_audio="r.flac", ref_text="rt",
                                     seed=1, out_wav=out)
        assert result["degraded"] is True
        assert "flac" in result["reason"].lower() or "ffmpeg" in result["reason"].lower()

    def test_clone_voice_degrades_when_volumedetect_unreadable(self, tmp_path):
        # No mean_volume line in stderr -> fail-closed degrade.
        out = str(tmp_path / "S01.wav")

        def runner(argv):
            if "volumedetect" in argv:
                return _Result(0, b"", b"no volume line here\n")
            return _Result(0, b"", b"")

        with _engine(_speak_handler(), runner=runner) as eng:
            result = eng.clone_voice(text="t", ref_audio="r.flac", ref_text="rt",
                                     seed=1, out_wav=out)
        assert result["degraded"] is True
        assert "volumedetect" in result["reason"] or "non-silence" in result["reason"]

    def test_clone_voice_degrades_on_missing_out_wav(self):
        with _engine(_speak_handler(), runner=_ffmpeg_runner()) as eng:
            result = eng.clone_voice(text="t", ref_audio="r.flac", ref_text="rt",
                                     seed=1, out_wav="")
        assert result["degraded"] is True
        assert "out_wav" in result["reason"]


# ---------------------------------------------------------------------------
# D-09 degrade / raise contract
# ---------------------------------------------------------------------------


class TestTTSEngineD09:
    def test_design_voice_degrades_on_connect_error(self, tmp_path):
        def handler(request):
            raise httpx.ConnectError("conn refused", request=request)
        with _engine(handler, runner=_ffmpeg_runner()) as eng:
            result = eng.design_voice(char="c", ref_line="r", instruct="ok", seed=1,
                                      ref_dir=str(tmp_path))
        assert result["degraded"] is True
        assert "ConnectError" in result["reason"]

    def test_clone_voice_degrades_on_timeout(self, tmp_path):
        def handler(request):
            raise httpx.ReadTimeout("read timed out", request=request)
        with _engine(handler, runner=_ffmpeg_runner()) as eng:
            result = eng.clone_voice(text="t", ref_audio="r.flac", ref_text="rt",
                                     seed=1, out_wav=str(tmp_path / "x.wav"))
        assert result["degraded"] is True
        assert "Timeout" in result["reason"] or "timed out" in result["reason"]

    def test_design_voice_degrades_on_http_500(self, tmp_path):
        def handler(request):
            return httpx.Response(500)
        with _engine(handler, runner=_ffmpeg_runner()) as eng:
            result = eng.design_voice(char="c", ref_line="r", instruct="ok", seed=1,
                                      ref_dir=str(tmp_path))
        assert result["degraded"] is True
        assert "HTTP 500" in result["reason"]

    def test_clone_voice_degrades_on_http_429(self, tmp_path):
        def handler(request):
            return httpx.Response(429)
        with _engine(handler, runner=_ffmpeg_runner()) as eng:
            result = eng.clone_voice(text="t", ref_audio="r.flac", ref_text="rt",
                                     seed=1, out_wav=str(tmp_path / "x.wav"))
        assert result["degraded"] is True
        assert "HTTP 429" in result["reason"]

    def test_design_voice_raises_on_http_400(self, tmp_path):
        # 4xx is a caller bug (D-09: raise, do not degrade).
        def handler(request):
            return httpx.Response(400, text="bad request body")
        with _engine(handler, runner=_ffmpeg_runner()) as eng:
            with pytest.raises(TTSEngineError) as excinfo:
                eng.design_voice(char="c", ref_line="r", instruct="ok", seed=1,
                                 ref_dir=str(tmp_path))
        assert "HTTP 400" in str(excinfo.value)

    def test_clone_voice_raises_on_invalid_json(self, tmp_path):
        def handler(request):
            return httpx.Response(200, content=b"not json",
                                  headers={"content-type": "application/json"})
        with _engine(handler, runner=_ffmpeg_runner()) as eng:
            with pytest.raises(TTSEngineError) as excinfo:
                eng.clone_voice(text="t", ref_audio="r.flac", ref_text="rt", seed=1,
                                out_wav=str(tmp_path / "x.wav"))
        assert "json" in str(excinfo.value).lower()


# ---------------------------------------------------------------------------
# 2026-08-16 P10 double-timeout fix: vram retry backoff + async two-phase
# ---------------------------------------------------------------------------


class TestVramInsufficientRetry:
    """HTTP 503 kind=vram_insufficient → exponential backoff before degrade."""

    @staticmethod
    def _vram_503():
        return httpx.Response(
            503,
            json={"code": 400, "data": {"error": {"kind": "vram_insufficient"}},
                  "message": "vram_insufficient: engine=qwen_tts needs 8192MiB"},
        )

    def test_vram_503_retries_with_backoff_then_succeeds(self, tmp_path):
        calls = {"n": 0}
        sleeps: list[float] = []

        def handler(request):
            if request.method == "POST" and request.url.path == "/api/v1/tts/speak":
                calls["n"] += 1
                if calls["n"] <= 2:
                    return self._vram_503()
                return httpx.Response(200, json={"audio_url": "/files/ok.flac"})
            return httpx.Response(200, content=b"FAKE_FLAC")

        with TTSEngine(base_url="http://test-tts",
                       transport=httpx.MockTransport(handler),
                       subprocess_runner=_ffmpeg_runner(),
                       comfyui_input_dir=str(tmp_path),
                       sleep=sleeps.append) as eng:
            result = eng.design_voice(char="c", ref_line="r", instruct="ok",
                                      seed=1, ref_dir=str(tmp_path))
        assert "degraded" not in result
        assert calls["n"] == 3
        # Backoff schedule observed: 60s then 120s (no wall-clock — injected sleep).
        assert sleeps == [60.0, 120.0]

    def test_vram_503_degrades_after_retries_exhausted(self, tmp_path):
        calls = {"n": 0}
        sleeps: list[float] = []

        def handler(request):
            calls["n"] += 1
            return self._vram_503()

        with TTSEngine(base_url="http://test-tts",
                       transport=httpx.MockTransport(handler),
                       subprocess_runner=_ffmpeg_runner(),
                       sleep=sleeps.append) as eng:
            result = eng.design_voice(char="c", ref_line="r", instruct="ok",
                                      seed=1, ref_dir=str(tmp_path))
        assert result["degraded"] is True
        assert "vram_insufficient" in result["reason"]
        # 1 initial attempt + 3 retries, backoffs 60/120/300.
        assert calls["n"] == 4
        assert sleeps == [60.0, 120.0, 300.0]
        # engine_unavailable kind — the queue genuinely cannot drain.
        assert result["kind"] == "engine_unavailable"

    def test_plain_503_without_vram_kind_degrades_immediately(self, tmp_path):
        calls = {"n": 0}
        sleeps: list[float] = []

        def handler(request):
            calls["n"] += 1
            return httpx.Response(503, text="node not registered")

        with TTSEngine(base_url="http://test-tts",
                       transport=httpx.MockTransport(handler),
                       subprocess_runner=_ffmpeg_runner(),
                       sleep=sleeps.append) as eng:
            result = eng.design_voice(char="c", ref_line="r", instruct="ok",
                                      seed=1, ref_dir=str(tmp_path))
        assert result["degraded"] is True
        assert calls["n"] == 1  # no retries — not a vram_insufficient body
        assert sleeps == []


class TestAsyncTwoPhase:
    """async 202 → poll /status/{prompt_id} until success."""

    def test_async_202_then_status_success(self, tmp_path):
        posts = []
        status_polls = {"n": 0}

        def handler(request):
            if request.method == "POST" and request.url.path == "/api/v1/tts/speak":
                posts.append(json.loads(request.content.decode()))
                return httpx.Response(202, json={"code": 200, "data": {
                    "prompt_id": "pid-1", "queue_wait_ms": 677500}, "message": "ok"})
            if request.method == "GET" and request.url.path.startswith("/api/v1/tts/status/"):
                status_polls["n"] += 1
                if status_polls["n"] < 3:
                    return httpx.Response(200, json={"code": 200, "data": {
                        "prompt_id": "pid-1", "status": "pending"}})
                return httpx.Response(200, json={"code": 200, "data": {
                    "prompt_id": "pid-1", "status": "success",
                    "audio_url": "/files/async.flac",
                    "audio_path": "/out/async.flac"}})
            if request.method == "GET" and request.url.path.startswith("/files/"):
                return httpx.Response(200, content=b"FAKE_FLAC")
            return httpx.Response(404)

        with TTSEngine(base_url="http://test-tts",
                       transport=httpx.MockTransport(handler),
                       subprocess_runner=_ffmpeg_runner(),
                       comfyui_input_dir=str(tmp_path),
                       sleep=lambda _s: None) as eng:
            result = eng.design_voice(char="c", ref_line="r", instruct="ok",
                                      seed=1, ref_dir=str(tmp_path))
        # Submit carried async:true (single POST — no fallback re-POST).
        assert len(posts) == 1
        assert posts[0]["async"] is True
        assert status_polls["n"] == 3
        assert "degraded" not in result
        assert Path(result["ref_local"]).is_file()

    def test_async_submit_non_202_degrades_without_resubmit(self, tmp_path):
        """Old KAP without the async route (plain 503) → classify in place.

        MUST NOT re-POST: a duplicate submit would synthesize the same line
        twice. Exactly one POST, one degrade envelope.
        """
        calls = {"n": 0}

        def handler(request):
            if request.method == "POST" and request.url.path == "/api/v1/tts/speak":
                calls["n"] += 1
                return httpx.Response(503, text="old deployment, no async route")
            return httpx.Response(404)

        with TTSEngine(base_url="http://test-tts",
                       transport=httpx.MockTransport(handler),
                       subprocess_runner=_ffmpeg_runner(),
                       sleep=lambda _s: None) as eng:
            result = eng.design_voice(char="c", ref_line="r", instruct="ok",
                                      seed=1, ref_dir=str(tmp_path))
        assert result["degraded"] is True
        assert "HTTP 503" in result["reason"]
        assert calls["n"] == 1  # single submit — never duplicated

    def test_async_flag_ignored_by_old_kap_uses_sync_result(self, tmp_path):
        """2xx non-202 = old KAP ignored the async flag, answered sync — use it
        directly (no re-POST)."""
        calls = {"n": 0}

        def handler(request):
            if request.method == "POST" and request.url.path == "/api/v1/tts/speak":
                calls["n"] += 1
                return httpx.Response(200, json={"audio_url": "/files/sync.flac"})
            if request.method == "GET" and request.url.path.startswith("/files/"):
                return httpx.Response(200, content=b"FAKE_FLAC")
            return httpx.Response(404)

        with TTSEngine(base_url="http://test-tts",
                       transport=httpx.MockTransport(handler),
                       subprocess_runner=_ffmpeg_runner(),
                       comfyui_input_dir=str(tmp_path),
                       sleep=lambda _s: None) as eng:
            result = eng.design_voice(char="c", ref_line="r", instruct="ok",
                                      seed=1, ref_dir=str(tmp_path))
        assert "degraded" not in result
        assert calls["n"] == 1
        assert Path(result["ref_local"]).is_file()

    def test_async_status_error_degrades(self, tmp_path):
        def handler(request):
            if request.method == "POST":
                return httpx.Response(202, json={"code": 200, "data": {
                    "prompt_id": "pid-err"}, "message": "ok"})
            if request.url.path.startswith("/api/v1/tts/status/"):
                return httpx.Response(200, json={"code": 200, "data": {
                    "prompt_id": "pid-err", "status": "error",
                    "error": "node blew up"}})
            return httpx.Response(404)

        with TTSEngine(base_url="http://test-tts",
                       transport=httpx.MockTransport(handler),
                       subprocess_runner=_ffmpeg_runner(),
                       sleep=lambda _s: None) as eng:
            result = eng.design_voice(char="c", ref_line="r", instruct="ok",
                                      seed=1, ref_dir=str(tmp_path))
        assert result["degraded"] is True
        assert "node blew up" in result["reason"]


class TestTimeoutBudget:
    def test_default_timeout_is_7200(self):
        # 7200s = 4× KAP_GPU_QUEUE_TIMEOUT (30min) headroom over queue+job.
        assert TTSEngine.DEFAULT_TIMEOUT == 7200.0
