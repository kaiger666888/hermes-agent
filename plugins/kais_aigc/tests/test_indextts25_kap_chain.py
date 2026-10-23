"""test_indextts25_kap_chain.py — IndexTTS25Engine KAP-chain smoke (v15.3).

2026-08-16 Kai decision: the engine routes VoiceDesign → IndexTTS 2.5 through
the KAP API (``KAIS_TTS_BASE_URL``, default ``http://localhost:10588``) so the
KAP GPU serial queue arbitrates VRAM. These tests pin the new HTTP contract
with ``httpx.MockTransport`` — no real network:

- ``design_voice`` POSTs ``/api/production/indextts2/voice-design/voice-design``
  (JSON: character_name/instruct/text/lang/language/emotion_mode/seed), then
  downloads ``data.synthesis.audio_url`` and persists the ref wav.
- ``clone_voice`` POSTs ``/api/production/indextts2/speak/speak`` multipart with
  ``version=2.5`` (+ ``emo_text`` when emotion_text given), then downloads
  ``data.audio_url`` bytes and runs the volumedetect mute gate.
  Double ``/speak`` is REAL KAP topology: router mounted at ``.../indextts2/
  speak`` + ``router.post("/speak")`` (single path 404s in deployment).
- D-09: connect-error / 5xx → degrade envelope (never raise); 4xx → raise
  ``TTSEngineError``.
- Env: ``KAIS_TTS_BASE_URL`` wins; legacy ``INDEXTTS25_SERVER_URL`` with a
  container-IP :5110/:5111 value is IGNORED (falls to the KAP default).
- v15.4 (2026-09-04): the backend behind both endpoints is Breeze TTS 2 via
  the KAP compat layer — these compat-path pins are UNCHANGED by that swap.
  ``TestBreezeDirectBranch`` pins the opt-in ``breeze_engine=True`` branch
  (``/api/production/breezeTts/speak``, Breeze-native form: ``instruction``
  instead of ``emo_text``, ``cfg_scale`` + ``seed``, no ``version``).
- FIX (2026-10-13): ``TestDesignVoiceEmptyInstructFallback`` pins the empty
  ``instruct`` default (KAP voice-design 400s an empty instruct → narrator
  ref degrade → whole-batch clone failure, 3 QA reject rounds on
  ep-mv-guangdexiaoxi). Stubbed at the ``_post_voicedesign`` seam — no net.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import httpx
import pytest

HERMES_ROOT = Path(__file__).resolve().parents[3]
if str(HERMES_ROOT) not in sys.path:
    sys.path.insert(0, str(HERMES_ROOT))

from plugins.kais_aigc.tts_engine import (  # noqa: E402
    IndexTTS25Engine,
    TTSEngineError,
)

KAP = "http://kap-test:10588"
VD_PATH = "/api/production/indextts2/voice-design/voice-design"
SPEAK_PATH = "/api/production/indextts2/speak/speak"
BREEZE_PATH = "/api/production/breezeTts/speak"


def _kap_handler(state: dict) -> httpx.MockTransport:
    """MockTransport serving the KAP voice-design + speak + /oss download."""

    def handler(request: httpx.Request) -> httpx.Response:
        state["requests"].append((request.method, str(request.url.path)))
        if request.method == "POST" and request.url.path == VD_PATH:
            state["vd_bodies"].append(request.read().decode("utf-8"))
            return httpx.Response(200, json={
                "code": 200,
                "data": {"synthesis": {
                    "audio_url": "/oss/tts/vdesign_synth_1.wav",
                    "audio_path": "/oss/tts/vdesign_synth_1.wav",
                }},
            })
        if request.method == "POST" and request.url.path == SPEAK_PATH:
            body = request.read().decode("utf-8", errors="replace")
            state["speak_bodies"].append(body)
            return httpx.Response(200, json={
                "code": 200,
                "data": {
                    "audio_url": "/oss/tts/indextts25_1.wav",
                    "audio_path": "/oss/tts/indextts25_1.wav",
                },
            })
        if request.method == "POST" and request.url.path == BREEZE_PATH:
            # Breeze native proxy: same response envelope as the compat
            # endpoint (KAP writes the wav to its oss dir either way).
            state.setdefault("breeze_bodies", []).append(
                request.read().decode("utf-8", errors="replace")
            )
            return httpx.Response(200, json={
                "code": 200,
                "data": {
                    "audio_url": "/oss/tts/breeze_1.wav",
                    "audio_path": "/oss/tts/breeze_1.wav",
                },
            })
        if request.method == "GET" and request.url.path.startswith("/oss/tts/"):
            state["downloads"].append(request.url.path)
            return httpx.Response(200, content=b"RIFF-FAKE-WAV-BYTES")
        return httpx.Response(404, text="not found")

    return httpx.MockTransport(handler)


def _loud_runner():
    """subprocess seam: pretend volumedetect reported -18.0 dB."""

    class _R:
        returncode = 0
        stderr = "[Parsed_volumedetect] mean_volume: -18.0 dB"

    return lambda argv, timeout=60: _R()


def _engine(state: dict, **kw) -> IndexTTS25Engine:
    return IndexTTS25Engine(
        kap_base_url=KAP,
        transport=_kap_handler(state),
        subprocess_runner=_loud_runner(),
        **kw,
    )


class TestKapChainDesign:
    def test_design_posts_kap_voice_design_then_downloads(self, tmp_path):
        state = {"requests": [], "vd_bodies": [], "speak_bodies": [], "downloads": []}
        with _engine(state) as eng:
            res = eng.design_voice(
                char="阿毛", ref_line="你好世界", instruct="幼童声音",
                seed=42, ref_dir=str(tmp_path),
            )
        assert "degraded" not in res, res
        assert (state["requests"][0] == ("POST", VD_PATH))
        assert state["downloads"] == ["/oss/tts/vdesign_synth_1.wav"]
        # ref wav persisted with deterministic name
        assert os.path.isfile(res["ref_audio"])
        assert res["ref_audio"].endswith("ref_阿毛.wav")
        # KAP body contract
        body = state["vd_bodies"][0]
        for key in ("character_name", "instruct", "text", "lang",
                    "language", "emotion_mode", "seed"):
            assert key in body, f"KAP voice-design body missing {key}"
        assert '"seed":42' in body

    def test_design_reuses_existing_ref_no_http(self, tmp_path):
        state = {"requests": [], "vd_bodies": [], "speak_bodies": [], "downloads": []}
        # Pre-place a ref (Strategy B / voice_bank)
        from plugins.kais_aigc.tts_engine import _indextts_ref_filename
        (tmp_path / _indextts_ref_filename("阿毛")).write_bytes(b"EXISTING")
        with _engine(state) as eng:
            res = eng.design_voice(
                char="阿毛", ref_line="x", instruct="y",
                seed=1, ref_dir=str(tmp_path),
            )
        assert "degraded" not in res
        assert state["requests"] == [], "Strategy B must skip all HTTP"


class TestKapChainClone:
    def test_clone_posts_multipart_version_25_and_downloads(self, tmp_path):
        state = {"requests": [], "vd_bodies": [], "speak_bodies": [], "downloads": []}
        ref = tmp_path / "ref_阿毛.wav"
        ref.write_bytes(b"RIFF-REF")
        out = tmp_path / "S01.wav"
        with _engine(state) as eng:
            res = eng.clone_voice(
                text="台词", ref_audio=str(ref), ref_text="你好世界", seed=7,
                out_wav=str(out), emotion_text="悲伤压抑",
            )
        assert "degraded" not in res, res
        assert out.read_bytes() == b"RIFF-FAKE-WAV-BYTES"
        body = state["speak_bodies"][0]
        assert 'name="version"' in body and "2.5" in body
        assert 'name="text"' in body
        assert 'name="emo_text"' in body and "悲伤压抑" in body
        # v15.4: ref_text is FORWARDED (additive; Breeze clone template
        # requires it — IndexTTS 2.5 ignored it, zero-shot).
        assert 'name="ref_text"' in body and "你好世界" in body
        assert 'name="ref_audio"; filename="ref_阿毛.wav"' in body
        assert ("/oss/tts/indextts25_1.wav" in state["downloads"])

    def test_clone_without_emotion_omits_emo_text(self, tmp_path):
        state = {"requests": [], "vd_bodies": [], "speak_bodies": [], "downloads": []}
        ref = tmp_path / "ref_c.wav"
        ref.write_bytes(b"RIFF")
        with _engine(state) as eng:
            eng.clone_voice(
                text="t", ref_audio=str(ref), ref_text="", seed=1,
                out_wav=str(tmp_path / "o.wav"),
            )
        assert 'name="emo_text"' not in state["speak_bodies"][0]


class TestKapChainDegradeContract:
    def test_connect_error_design_degrades(self, tmp_path):
        def handler(request):
            raise httpx.ConnectError("refused", request=request)

        with IndexTTS25Engine(
            kap_base_url=KAP, transport=httpx.MockTransport(handler),
        ) as eng:
            res = eng.design_voice(
                char="c", ref_line="r", instruct="i",
                seed=1, ref_dir=str(tmp_path),
            )
        assert res.get("degraded") is True
        assert res.get("kind") == "engine_unavailable"

    def test_5xx_speak_degrades(self, tmp_path):
        def handler(request):
            if request.url.path == SPEAK_PATH:
                return httpx.Response(503, text="boom")
            return httpx.Response(200, content=b"RIFF")

        ref = tmp_path / "ref_c.wav"
        ref.write_bytes(b"RIFF")
        with IndexTTS25Engine(
            kap_base_url=KAP, transport=httpx.MockTransport(handler),
            subprocess_runner=_loud_runner(),
        ) as eng:
            res = eng.clone_voice(
                text="t", ref_audio=str(ref), ref_text="", seed=1,
                out_wav=str(tmp_path / "o.wav"),
            )
        assert res.get("degraded") is True
        assert res.get("kind") == "engine_unavailable"

    def test_4xx_speak_raises_engine_error(self, tmp_path):
        def handler(request):
            if request.url.path == SPEAK_PATH:
                return httpx.Response(400, text="bad field")
            return httpx.Response(200, content=b"RIFF")

        ref = tmp_path / "ref_c.wav"
        ref.write_bytes(b"RIFF")
        with IndexTTS25Engine(
            kap_base_url=KAP, transport=httpx.MockTransport(handler),
            subprocess_runner=_loud_runner(),
        ) as eng:
            with pytest.raises(TTSEngineError):
                eng.clone_voice(
                    text="t", ref_audio=str(ref), ref_text="", seed=1,
                    out_wav=str(tmp_path / "o.wav"),
                )


class TestKapBaseUrlEnv:
    def test_kais_tts_base_url_env_wins(self, monkeypatch):
        monkeypatch.setenv("KAIS_TTS_BASE_URL", "http://env-kap:10588")
        eng = IndexTTS25Engine(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})))
        assert eng._kap_base == "http://env-kap:10588"
        eng.close()

    def test_legacy_container_ip_env_ignored(self, monkeypatch):
        monkeypatch.delenv("KAIS_TTS_BASE_URL", raising=False)
        monkeypatch.setenv("INDEXTTS25_SERVER_URL", "http://172.18.0.6:5110")
        eng = IndexTTS25Engine(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})))
        assert eng._kap_base == IndexTTS25Engine.DEFAULT_KAP_BASE_URL, (
            "container-IP legacy env must NOT leak into the KAP base"
        )
        eng.close()

    def test_legacy_env_kap_shaped_value_used(self, monkeypatch):
        monkeypatch.delenv("KAIS_TTS_BASE_URL", raising=False)
        monkeypatch.setenv("INDEXTTS25_SERVER_URL", "http://legacy-kap:10588")
        eng = IndexTTS25Engine(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})))
        assert eng._kap_base == "http://legacy-kap:10588"
        eng.close()


class TestBreezeDirectBranch:
    """v15.4 opt-in direct branch (default OFF — compat endpoint IS Breeze)."""

    def _state(self) -> dict:
        return {"requests": [], "vd_bodies": [], "speak_bodies": [],
                "breeze_bodies": [], "downloads": []}

    def test_breeze_engine_true_posts_breeze_native_form(self, tmp_path):
        state = self._state()
        ref = tmp_path / "ref_阿毛.wav"
        ref.write_bytes(b"RIFF-REF")
        out = tmp_path / "S01.wav"
        with _engine(state, breeze_engine=True) as eng:
            res = eng.clone_voice(
                text="台词", ref_audio=str(ref), ref_text="你好世界", seed=7,
                out_wav=str(out), emotion_text="悲伤压抑",
            )
        assert "degraded" not in res, res
        assert state["requests"][0] == ("POST", BREEZE_PATH)
        assert out.read_bytes() == b"RIFF-FAKE-WAV-BYTES"
        body = state["breeze_bodies"][0]
        # Breeze-native fields present.
        assert 'name="text"' in body
        assert 'name="instruction"' in body and "悲伤压抑" in body
        assert 'name="cfg_scale"' in body and "4.0" in body
        assert 'name="seed"' in body and "\r\n7\r\n" in body
        # Breeze clone template REQUIRES ref_text (empty → 500 at backend).
        assert 'name="ref_text"' in body and "你好世界" in body
        assert 'name="ref_audio"; filename="ref_阿毛.wav"' in body
        # Compat-only fields absent.
        assert 'name="version"' not in body
        assert 'name="emo_text"' not in body
        assert "/oss/tts/breeze_1.wav" in state["downloads"]

    def test_breeze_branch_without_emotion_omits_instruction(self, tmp_path):
        state = self._state()
        ref = tmp_path / "ref_c.wav"
        ref.write_bytes(b"RIFF")
        with _engine(state, breeze_engine=True) as eng:
            eng.clone_voice(
                text="t", ref_audio=str(ref), ref_text="", seed=1,
                out_wav=str(tmp_path / "o.wav"),
            )
        assert 'name="instruction"' not in state["breeze_bodies"][0]

    def test_breeze_env_optin_and_optout(self, tmp_path, monkeypatch):
        state = self._state()
        ref = tmp_path / "ref_c.wav"
        ref.write_bytes(b"RIFF")
        monkeypatch.delenv("KAIS_TTS_BREEZE_ENGINE", raising=False)
        # Default OFF → compat path (version=2.5).
        with _engine(self._state()) as eng:
            assert eng._breeze_engine is False
        monkeypatch.setenv("KAIS_TTS_BREEZE_ENGINE", "1")
        with _engine(state) as eng:
            assert eng._breeze_engine is True
            eng.clone_voice(
                text="t", ref_audio=str(ref), ref_text="", seed=1,
                out_wav=str(tmp_path / "o1.wav"),
            )
        assert state["requests"][0] == ("POST", BREEZE_PATH)
        # Explicit "0" opts back out.
        state2 = self._state()
        monkeypatch.setenv("KAIS_TTS_BREEZE_ENGINE", "0")
        with _engine(state2) as eng:
            assert eng._breeze_engine is False
            eng.clone_voice(
                text="t", ref_audio=str(ref), ref_text="", seed=1,
                out_wav=str(tmp_path / "o2.wav"),
            )
        assert state2["requests"][0] == ("POST", SPEAK_PATH)

    def test_breeze_design_still_uses_compat_voice_design(self, tmp_path):
        # No direct design branch: design_voice hits the voice-design endpoint
        # regardless of breeze_engine (its backend is Breeze either way).
        state = self._state()
        with _engine(state, breeze_engine=True) as eng:
            res = eng.design_voice(
                char="阿毛", ref_line="你好世界", instruct="幼童声音",
                seed=42, ref_dir=str(tmp_path),
            )
        assert "degraded" not in res, res
        assert state["requests"][0] == ("POST", VD_PATH)

    def test_breeze_direct_5xx_degrades_same_contract(self, tmp_path):
        def handler(request):
            if request.url.path == BREEZE_PATH:
                return httpx.Response(503, text="boom")
            return httpx.Response(200, content=b"RIFF")

        ref = tmp_path / "ref_c.wav"
        ref.write_bytes(b"RIFF")
        with IndexTTS25Engine(
            kap_base_url=KAP, transport=httpx.MockTransport(handler),
            subprocess_runner=_loud_runner(), breeze_engine=True,
        ) as eng:
            res = eng.clone_voice(
                text="t", ref_audio=str(ref), ref_text="", seed=1,
                out_wav=str(tmp_path / "o.wav"),
            )
        assert res.get("degraded") is True
        assert res.get("kind") == "engine_unavailable"

    def test_breeze_direct_4xx_raises_engine_error(self, tmp_path):
        def handler(request):
            if request.url.path == BREEZE_PATH:
                return httpx.Response(400, text="bad field")
            return httpx.Response(200, content=b"RIFF")

        ref = tmp_path / "ref_c.wav"
        ref.write_bytes(b"RIFF")
        with IndexTTS25Engine(
            kap_base_url=KAP, transport=httpx.MockTransport(handler),
            subprocess_runner=_loud_runner(), breeze_engine=True,
        ) as eng:
            with pytest.raises(TTSEngineError):
                eng.clone_voice(
                    text="t", ref_audio=str(ref), ref_text="", seed=1,
                    out_wav=str(tmp_path / "o.wav"),
                )


class TestDesignVoiceEmptyInstructFallback:
    """FIX (2026-10-13): empty instruct → deterministic default pre-POST.

    KAP breezeTts voice-design hard-400s an empty instruct ("Missing required
    field: instruct (voice description)"). Narrator has no voice-design line
    by nature, so empty is a NORMAL input form — the 400 used to degrade the
    narrator ref, cascade-fail all 21 clones and loop 3 QA reject rounds on
    ep-mv-guangdexiaoxi. A non-empty instruct must pass through unchanged.
    """

    NARRATOR_DEFAULT = "温柔清晰的旁白女声"
    GENERIC_DEFAULT = "清晰自然的人声"

    def _run_design(self, monkeypatch, tmp_path, *, char, instruct, ref_sub=""):
        """design_voice with ``_post_voicedesign`` stubbed at the seam.

        Returns the captured POST body dict. The mock transport stays wired so
        ``_download`` still resolves without network; the seam assertion below
        proves the engine itself never issued the voice-design POST.
        """
        captured = {}
        state = {"requests": [], "vd_bodies": [], "speak_bodies": [], "downloads": []}

        def fake_vd(body):
            captured["body"] = dict(body)
            return {"code": 200, "data": {"synthesis": {
                "audio_url": "/oss/tts/vdesign_synth_1.wav",
            }}}

        with _engine(state) as eng:
            monkeypatch.setattr(eng, "_post_voicedesign", fake_vd)
            res = eng.design_voice(
                char=char, ref_line="你好世界", instruct=instruct,
                seed=1, ref_dir=str(tmp_path / ref_sub),
            )
        assert "degraded" not in res, res
        assert all(m != "POST" for m, _ in state["requests"]), (
            "voice-design POST must be captured at the _post_voicedesign seam"
        )
        assert state["downloads"] == ["/oss/tts/vdesign_synth_1.wav"]
        return captured["body"]

    def test_empty_instruct_narrator_gets_narration_default(
        self, monkeypatch, tmp_path, caplog,
    ):
        caplog.set_level(logging.INFO)  # root default WARNING drops logger.info
        # Empty AND pure-whitespace instruct are both "empty" per the FIX.
        for i, empty in enumerate(("", "   ")):
            body = self._run_design(
                monkeypatch, tmp_path, char="narrator", instruct=empty,
                ref_sub=f"run{i}",
            )
            assert body["instruct"] == self.NARRATOR_DEFAULT
        # Case-insensitive + 旁白/voiceover name tags hit the same default.
        for i, name in enumerate(("Narrator", "女旁白", "voiceover_2")):
            body = self._run_design(
                monkeypatch, tmp_path, char=name, instruct="",
                ref_sub=f"tag{i}",
            )
            assert body["instruct"] == self.NARRATOR_DEFAULT
        # One ledger line per fallback, carrying char + the default value.
        fallback_lines = [
            m for m in caplog.messages
            if "empty instruct" in m and self.NARRATOR_DEFAULT in m
        ]
        assert len(fallback_lines) >= 1

    def test_empty_instruct_generic_char_gets_neutral_default(
        self, monkeypatch, tmp_path,
    ):
        body = self._run_design(
            monkeypatch, tmp_path, char="alice", instruct="",
        )
        assert body["instruct"] == self.GENERIC_DEFAULT

    def test_nonempty_instruct_passthrough_unchanged(self, monkeypatch, tmp_path):
        # Zero-change regression anchor: a designed line is forwarded as-is —
        # including for narrator-style chars (fallback must NOT stomp it).
        for i, (char, instruct) in enumerate(
            (("narrator", "沙哑男声"), ("alice", "沙哑男声")),
        ):
            body = self._run_design(
                monkeypatch, tmp_path, char=char, instruct=instruct,
                ref_sub=f"pass{i}",
            )
            assert body["instruct"] == "沙哑男声"

    def test_defaults_within_oom_guard_budget(self):
        from plugins.kais_aigc.tts_engine import (
            MAX_INSTRUCT_CHARS,
            _default_instruct_for,
        )

        for char in ("narrator", "Narrator", "旁白", "voiceover_2",
                     "alice", "阿毛", ""):
            d = _default_instruct_for(char)
            assert d == _default_instruct_for(char), "must be pure/deterministic"
            assert len(d) <= MAX_INSTRUCT_CHARS, (
                f"default {d!r} exceeds the OOM-guard budget"
            )
        assert _default_instruct_for("narrator") == self.NARRATOR_DEFAULT
        assert _default_instruct_for("alice") == self.GENERIC_DEFAULT
