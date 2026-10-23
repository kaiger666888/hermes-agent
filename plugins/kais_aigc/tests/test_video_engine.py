"""TDD tests for the VideoEngine strategy pattern (P1-2 scriptability upgrade).

Mirrors ``test_preview_engine.py``: every engine is constructed with
``transport=httpx.MockTransport(handler)`` so no real network call is made, and
the D-09 degrade / raise contract is enforced identically to ``LTXVideoEngine``.

Coverage:
- ``TestVideoEngineABC``: ABC shape, ``VideoEngineError``, ``select_video_engine``
  factory dispatch.
- ``TestH3VideoEngine``: mocked httpx multipart POST + D-09 contract + multipart
  field set (1:1 with the retired curl template) + download + P0-4 frame gate.
- ``TestFrameMath``: ``_compute_expected_frames`` H3 grid alignment.
"""

from __future__ import annotations

import re
import sys
import threading
from pathlib import Path

import httpx
import pytest

# Ensure hermes-agent root is importable so ``plugins.kais_aigc.*`` resolves.
HERMES_ROOT = Path(__file__).resolve().parents[3]
if str(HERMES_ROOT) not in sys.path:
    sys.path.insert(0, str(HERMES_ROOT))

from plugins.kais_aigc.video_engine import (  # noqa: E402
    H3VideoEngine,
    VDN_PROFILE,
    VideoEngine,
    VideoEngineError,
    _compute_expected_frames,
    select_video_engine,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_multipart(request: httpx.Request) -> tuple[dict, dict]:
    """Parse a ``multipart/form-data`` request body.

    Returns ``(fields, files)`` where ``fields`` maps form-field name → value
    and ``files`` maps file-part name → list of filenames. Used to assert the
    engine builds the same field set the retired curl template did.
    """
    ctype = request.headers.get("content-type", "")
    if "boundary=" not in ctype:
        return {}, {}
    boundary = ctype.split("boundary=", 1)[1].strip().encode()
    body = request.content
    fields: dict = {}
    files: dict = {}
    for raw_part in body.split(b"--" + boundary):
        part = raw_part.strip(b"-").strip()
        if not part or part == b"--" or b"\r\n\r\n" not in part:
            continue
        header_blob, _, value = part.partition(b"\r\n\r\n")
        header_text = header_blob.decode("utf-8", "replace")
        name_m = re.search(r'name="([^"]+)"', header_text)
        if not name_m:
            continue
        name = name_m.group(1)
        file_m = re.search(r'filename="([^"]+)"', header_text)
        if file_m:
            files.setdefault(name, []).append(file_m.group(1))
        else:
            fields[name] = value.decode("utf-8", "replace").rstrip("\r\n")
    return fields, files


def _png_bytes() -> bytes:
    """Minimal valid-ish PNG header so the file part has real content."""
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def _wav_bytes() -> bytes:
    return b"RIFF" + b"\x00" * 40


def _ok_handler(
    video_bytes: bytes = b"FAKE_MP4_BODY",
    video_url: str = "http://test-h3/files/shot.mp4",
    captured: list | None = None,
):
    """MockTransport handler: POST returns video_url, GET streams video_bytes."""

    def handler(request: httpx.Request) -> httpx.Response:
        if captured is not None:
            captured.append(request)
        if request.method == "POST":
            return httpx.Response(200, json={"video_url": video_url})
        # GET — the clip download.
        return httpx.Response(200, content=video_bytes)

    return handler


def _client(handler, **kw):
    """Build an H3VideoEngine with a mock transport + a frame validator that
    always passes (real ffprobe is unavailable in the test env)."""
    return H3VideoEngine(
        base_url="http://test-h3",
        transport=httpx.MockTransport(handler),
        frame_validator=lambda clip_path, expected: (True, "ok"),
        **kw,
    )


# ---------------------------------------------------------------------------
# ABC + factory
# ---------------------------------------------------------------------------


class TestVideoEngineABC:
    def test_video_engine_is_abc(self):
        from abc import ABC

        assert issubclass(VideoEngine, ABC)

    def test_video_engine_cannot_be_instantiated_directly(self):
        with pytest.raises(TypeError):
            VideoEngine()

    def test_render_is_abstract_method(self):
        assert getattr(VideoEngine.render, "__isabstractmethod__", False) is True

    def test_video_engine_error_is_exception_subclass(self):
        assert issubclass(VideoEngineError, Exception)


class TestSelectVideoEngine:
    def test_default_returns_h3_video_engine(self, monkeypatch):
        monkeypatch.delenv("KAIS_VIDEO_ENGINE", raising=False)
        engine = select_video_engine()
        assert isinstance(engine, H3VideoEngine)
        engine.close()

    def test_env_h3_returns_h3_video_engine(self):
        engine = select_video_engine(env="h3")
        assert isinstance(engine, H3VideoEngine)
        engine.close()

    def test_unknown_env_falls_back_to_h3_with_warn(self, caplog):
        import logging

        with caplog.at_level(logging.WARNING, logger="plugins.kais_aigc.video_engine"):
            engine = select_video_engine(env="totally-bogus-value")
        assert isinstance(engine, H3VideoEngine)
        joined = " ".join(rec.getMessage() for rec in caplog.records)
        assert "totally-bogus-value" in joined
        assert "h3" in joined.lower()
        engine.close()

    def test_reads_env_at_call_time_not_import_time(self, monkeypatch):
        monkeypatch.delenv("KAIS_VIDEO_ENGINE", raising=False)
        first = select_video_engine()
        assert isinstance(first, H3VideoEngine)
        first.close()
        monkeypatch.setenv("KAIS_VIDEO_ENGINE", "h3")
        second = select_video_engine()
        assert isinstance(second, H3VideoEngine)
        second.close()


# ---------------------------------------------------------------------------
# H3VideoEngine — happy path + multipart body + download
# ---------------------------------------------------------------------------


class TestH3VideoEngineHappyPath:
    def test_render_success_envelope(self, tmp_path):
        out = str(tmp_path / "shot.mp4")
        with _client(_ok_handler()) as engine:
            result = engine.render(
                shot={"shot_id": "S01", "ltx_prompt": "a scene", "duration_sec": 5.0},
                output_path=out,
            )
        assert result.get("engine") == "h3"
        assert result.get("clip_path") == out
        assert "degraded" not in result
        assert isinstance(result.get("generation_time_ms"), int)
        assert result["generation_time_ms"] >= 0
        # The clip was actually downloaded to output_path.
        assert Path(out).read_bytes() == b"FAKE_MP4_BODY"

    def test_render_missing_output_path_degrades(self):
        with _client(_ok_handler()) as engine:
            result = engine.render(
                shot={"shot_id": "S01", "ltx_prompt": "x"},
                output_path="",
            )
        assert result.get("degraded") is True
        assert "output_path" in result["reason"]

    def test_render_missing_prompt_degrades(self, tmp_path):
        out = str(tmp_path / "shot.mp4")
        with _client(_ok_handler()) as engine:
            result = engine.render(
                shot={"shot_id": "S01"},  # no ltx_prompt / prompt
                output_path=out,
            )
        assert result.get("degraded") is True
        assert "prompt" in result["reason"]


class TestH3MultipartFields:
    """The multipart field set must match the retired curl template
    (``_form_factor_render_args_h3``) 1:1: projectId / prompt / mode / profile /
    width / height / length / filenamePrefix + refImages[] / ttsAudio / image."""

    def test_post_carries_all_data_fields(self, tmp_path):
        turnaround = tmp_path / "tr.png"
        turnaround.write_bytes(_png_bytes())
        scene = tmp_path / "scene.png"
        scene.write_bytes(_png_bytes())
        voice = tmp_path / "v.wav"
        voice.write_bytes(_wav_bytes())
        captured: list[httpx.Request] = []
        out = str(tmp_path / "shot.mp4")
        with _client(_ok_handler(captured=captured)) as engine:
            engine.render(
                shot={"shot_id": "S02_001", "ltx_prompt": "raw prompt", "duration_sec": 6.0},
                output_path=out,
                turnaround_paths=[str(turnaround)],
                scene_ref_path=str(scene),
                voice_clip_path=str(voice),
                prompt="ENHANCED PROMPT",
                episode_config={"form_factor": "landscape"},
            )
        post_req = captured[0]
        assert post_req.method == "POST"
        assert post_req.url.path == "/api/production/minimax-h3/generate"
        fields, files = _parse_multipart(post_req)
        assert fields["projectId"] == "1"
        assert fields["prompt"] == "ENHANCED PROMPT"
        assert fields["mode"] == "ref2va"
        # Default (no h3_useCase/h3_profile on shot/episode) → final-shot
        # (2026-08-17 useCase 入口迁移; legacy 默认映射 final-shot =
        # native-sage 36 步 + 完整 Foley+TTS, KAP 侧解析, 引擎不再平铺
        # profile/native/tespeed/steps).
        assert fields["useCase"] == "final-shot"
        assert "profile" not in fields
        assert "native" not in fields
        assert "tespeed" not in fields
        assert "steps" not in fields
        assert fields["width"] == "1344"   # landscape
        assert fields["height"] == "768"
        assert fields["filenamePrefix"] == "S02_001"
        # length is the H3 frame grid snap of 6.0s -> 141.
        assert fields["length"] == "141"

    def test_post_attaches_refimages_and_ttsaudio(self, tmp_path):
        turnaround = tmp_path / "tr.png"
        turnaround.write_bytes(_png_bytes())
        scene = tmp_path / "scene.png"
        scene.write_bytes(_png_bytes())
        voice = tmp_path / "v.wav"
        voice.write_bytes(_wav_bytes())
        captured: list[httpx.Request] = []
        with _client(_ok_handler(captured=captured)) as engine:
            engine.render(
                shot={"shot_id": "S03", "ltx_prompt": "x", "duration_sec": 5.0},
                output_path=str(tmp_path / "out.mp4"),
                turnaround_paths=[str(turnaround)],
                scene_ref_path=str(scene),
                voice_clip_path=str(voice),
            )
        _, files = _parse_multipart(captured[0])
        # refImages[] carries both the turnaround and the scene background.
        ref_names = files.get("refImages", [])
        assert "tr.png" in ref_names
        assert "scene.png" in ref_names
        assert "v.wav" in files.get("ttsAudio", [])

    def test_post_omits_ttsaudio_when_no_voice_clip(self, tmp_path):
        scene = tmp_path / "scene.png"
        scene.write_bytes(_png_bytes())
        captured: list[httpx.Request] = []
        with _client(_ok_handler(captured=captured)) as engine:
            engine.render(
                shot={"shot_id": "S04", "ltx_prompt": "x", "duration_sec": 5.0},
                output_path=str(tmp_path / "out.mp4"),
                scene_ref_path=str(scene),
            )
        _, files = _parse_multipart(captured[0])
        assert "ttsAudio" not in files

    def test_portrait_resolution(self, tmp_path):
        captured: list[httpx.Request] = []
        with _client(_ok_handler(captured=captured)) as engine:
            engine.render(
                shot={"shot_id": "S05", "ltx_prompt": "x", "duration_sec": 5.0,
                      "form_factor": "portrait"},
                output_path=str(tmp_path / "out.mp4"),
            )
        fields, _ = _parse_multipart(captured[0])
        assert fields["width"] == "768"
        assert fields["height"] == "1344"


# ---------------------------------------------------------------------------
# Token-budget-aware resolution ladder (KAP gate)
# ---------------------------------------------------------------------------


class TestH3ResolutionBudget:
    """``_resolve_resolution`` must price a render at ``w*h*length`` tokens and
    stay under the KAP safeLine (300M; crashLine 340M is an RTX 3090 C++ abort
    that cannot be caught).

    Root cause: ep-shencongshenyuan-ep01 S02_B02 (portrait, 15s, 362 frames)
    unconditionally got 768×1344 → 373,653,504 tokens → guaranteed HTTP 400,
    the shot could never render. The ladder takes the top 32-multiple rung
    that fits; ``resolution_override`` is the operator's manual knob."""

    def test_portrait_short_shot_keeps_top_rung(self):
        # 175 frames: 768*1344*175 = 180,633,600 tokens — in budget, no downgrade.
        w, h = H3VideoEngine._resolve_resolution({"shot_id": "S01"}, None, 175)
        assert (w, h) == (768, 1344)

    def test_portrait_15s_shot_downgrades_one_rung(self):
        # The incident shot: 362 frames. 768*1344*362 = 373,653,504 > safeLine;
        # 672*1216*362 = 295,809,024 ≤ 300M.
        w, h = H3VideoEngine._resolve_resolution({"shot_id": "S02_B02"}, None, 362)
        assert (w, h) == (672, 1216)

    def test_landscape_15s_shot_downgrades_one_rung(self):
        w, h = H3VideoEngine._resolve_resolution(
            {"shot_id": "S03", "form_factor": "landscape"}, None, 362,
        )
        assert (w, h) == (1216, 672)

    def test_resolution_override_wins_over_ladder(self):
        shot = {"shot_id": "S04", "resolution_override": "640x1152"}
        w, h = H3VideoEngine._resolve_resolution(shot, None, 362)
        assert (w, h) == (640, 1152)

    def test_valid_override_skips_budget_check_entirely(self):
        # The operator knob owns the tradeoff: even an over-budget override is
        # sent verbatim (KAP's 400 will say so honestly).
        shot = {"shot_id": "S05", "resolution_override": "768x1344"}
        w, h = H3VideoEngine._resolve_resolution(shot, None, 362)
        assert (w, h) == (768, 1344)

    def test_invalid_override_falls_back_to_ladder(self):
        # 700 and 1200 are not 32-multiples — override ignored, ladder runs.
        shot = {"shot_id": "S06", "resolution_override": "700x1200"}
        w, h = H3VideoEngine._resolve_resolution(shot, None, 362)
        assert (w, h) == (672, 1216)

    def test_unknown_frames_keeps_top_rung(self):
        # frames=None / 0 — legacy pre-budget behavior (top rung).
        assert H3VideoEngine._resolve_resolution({"shot_id": "S07"}, None) == (768, 1344)
        assert H3VideoEngine._resolve_resolution({"shot_id": "S07"}, None, 0) == (768, 1344)

    def test_all_rungs_over_budget_uses_lowest(self):
        # 500 frames: even 640*1152*500 = 368,640,000 > safeLine — take the
        # lowest rung and let KAP's 400 speak truth.
        w, h = H3VideoEngine._resolve_resolution({"shot_id": "S08"}, None, 500)
        assert (w, h) == (640, 1152)

    def test_downgrade_logs_rung_and_tokens(self, caplog):
        import logging

        with caplog.at_level(logging.INFO, logger="plugins.kais_aigc.video_engine"):
            H3VideoEngine._resolve_resolution({"shot_id": "S02_B02"}, None, 362)
        joined = " ".join(rec.getMessage() for rec in caplog.records)
        assert "S02_B02" in joined
        assert "768x1344" in joined and "672x1216" in joined
        assert "373653504" in joined  # the exact token count that crashed KAP

    def test_e2e_multipart_carries_budgeted_resolution(self, tmp_path):
        """End-to-end through _build_multipart: a portrait 15s shot (the S02_B02
        incident shape) must POST width=672 height=1216 length=362, not the
        budget-blowing 768×1344."""
        captured: list[httpx.Request] = []
        with _client(_ok_handler(captured=captured)) as engine:
            engine.render(
                shot={"shot_id": "S02_B02", "ltx_prompt": "x", "duration_sec": 15.0},
                output_path=str(tmp_path / "out.mp4"),
            )
        fields, _ = _parse_multipart(captured[0])
        assert fields["length"] == "362"
        assert fields["width"] == "672"
        assert fields["height"] == "1216"


# ---------------------------------------------------------------------------
# blockCache passthrough (KAP MiniMaxH3BlockCacheT8, 2026-08-27)
# ---------------------------------------------------------------------------


class TestH3BlockCache:
    """``h3_blockCache`` / ``h3_blockCacheThreshold`` shot/episode passthrough
    for the KAP MiniMaxH3BlockCacheT8 injection switch (Case08 high-dynamics
    15s/362f A/B: −52.5% wall time, 23/41 block hits, SSIM 0.7145).

    Red line: a shot without blockCache config must POST the exact pre-change
    field sequence — no extra fields, no reordered names. The switch is
    additive and opt-in only; KAP consumes it on the native-sage chain and
    silently ignores it on turbo/T8."""

    # -- red line: default field sequence unchanged ------------------------

    def test_default_shot_field_sequence_unchanged(self, tmp_path):
        # 无 blockCache 配置 → 字段名序列与改动前基线逐项一致。
        captured: list[httpx.Request] = []
        with _client(_ok_handler(captured=captured)) as engine:
            engine.render(
                shot={"shot_id": "S10", "ltx_prompt": "x", "duration_sec": 5.0},
                output_path=str(tmp_path / "out.mp4"),
            )
        fields, files = _parse_multipart(captured[0])
        assert list(fields) == [
            "projectId", "prompt", "mode", "width", "height",
            "length", "filenamePrefix", "useCase",
        ]
        assert files == {}
        assert "blockCache" not in fields
        assert "blockCacheThreshold" not in fields

    def test_configured_usecase_but_no_blockcache_still_clean(self, tmp_path):
        # h3_useCase/h3_motion 已配置 (preview-lock 多一个 motion 字段) 但
        # blockCache 未配置 → 序列同样不受影响。
        captured: list[httpx.Request] = []
        with _client(_ok_handler(captured=captured)) as engine:
            engine.render(
                shot={"shot_id": "S11", "ltx_prompt": "x", "duration_sec": 5.0,
                      "h3_useCase": "preview-lock", "h3_motion": "low"},
                output_path=str(tmp_path / "out.mp4"),
            )
        fields, _ = _parse_multipart(captured[0])
        assert list(fields) == [
            "projectId", "prompt", "mode", "width", "height",
            "length", "filenamePrefix", "useCase", "motion",
        ]
        assert "blockCache" not in fields

    # -- flag resolution: shot > episode, explicit both directions ----------

    def test_flag_truthy_forms_accepted(self):
        # round-5 对齐 KAP 线缆侧解析: 大小写不敏感 + 去首尾空白 + 数字 1
        # 同义; bool True 直接通过。
        for raw in (True, "on", "true", "1", "ON", "True", " ON ", 1):
            assert H3VideoEngine._resolve_block_cache({"h3_blockCache": raw}, None) is True
        # 其余值一律不发字段 (规格红线): false 族/垃圾值/近似但非法的字面量
        # 都不在白名单 ("1.0"/"10" 不是数字 1)。
        for raw in (False, "off", "OFF", "0", "yes", 0, "", "   ", "1.0", "10", None):
            assert H3VideoEngine._resolve_block_cache({"h3_blockCache": raw}, None) is False

    def test_shot_level_flag_overrides_episode_level_both_directions(self):
        # 双向显式表达: shot=true 压过 episode=false; shot=false 抑制
        # episode=true (presence-based, 非 truthiness 链式 or)。
        assert H3VideoEngine._resolve_block_cache(
            {"h3_blockCache": True}, {"h3_blockCache": False},
        ) is True
        assert H3VideoEngine._resolve_block_cache(
            {"h3_blockCache": False}, {"h3_blockCache": True},
        ) is False
        assert H3VideoEngine._resolve_block_cache({}, {"h3_blockCache": "on"}) is True
        assert H3VideoEngine._resolve_block_cache({}, None) is False

    def test_episode_level_flag_reaches_every_shot(self, tmp_path):
        # episode 级开 → 每个 shot 的 POST 都带 blockCache=true。
        captured: list[httpx.Request] = []
        with _client(_ok_handler(captured=captured)) as engine:
            for sid in ("S12", "S13"):
                engine.render(
                    shot={"shot_id": sid, "ltx_prompt": "x", "duration_sec": 5.0},
                    output_path=str(tmp_path / f"{sid}.mp4"),
                    episode_config={"h3_blockCache": True},
                )
        assert len(captured) == 4  # 2 POST + 2 GET 下载
        for req in captured:
            if req.method != "POST":
                continue
            fields, _ = _parse_multipart(req)
            assert fields["blockCache"] == "true"

    def test_shot_level_false_suppresses_episode_true_e2e(self, tmp_path, caplog):
        import logging

        with caplog.at_level(logging.INFO, logger="plugins.kais_aigc.video_engine"):
            captured: list[httpx.Request] = []
            with _client(_ok_handler(captured=captured)) as engine:
                engine.render(
                    shot={"shot_id": "S14", "ltx_prompt": "x", "duration_sec": 5.0,
                          "h3_blockCache": False},
                    output_path=str(tmp_path / "out.mp4"),
                    episode_config={"h3_blockCache": True},
                )
        fields, _ = _parse_multipart(captured[0])
        assert "blockCache" not in fields
        # 未生效也不打生效日志。
        assert not any("blockCache" in rec.getMessage() for rec in caplog.records)

    # -- threshold resolution: valid [0,1] float only, junk tolerated -------

    def test_threshold_valid_values_pass_through(self):
        r = H3VideoEngine._resolve_block_cache_threshold
        assert r({"h3_blockCacheThreshold": 0.85}, None) == 0.85
        assert r({"h3_blockCacheThreshold": "0.4"}, None) == 0.4
        assert r({"h3_blockCacheThreshold": 0}, None) == 0.0
        assert r({"h3_blockCacheThreshold": "1"}, None) == 1.0
        assert r({}, {"h3_blockCacheThreshold": 0.2}) == 0.2
        assert r({"h3_blockCacheThreshold": 0.9}, {"h3_blockCacheThreshold": 0.1}) == 0.9
        assert r({}, None) is None

    def test_threshold_invalid_values_silently_dropped(self):
        # "abc"/1.5/-0.2/NaN/inf/None/空串/列表 全部静默 None, 不抛异常。
        r = H3VideoEngine._resolve_block_cache_threshold
        for bad in ("abc", 1.5, -0.2, float("nan"), float("inf"), None, "", [0.5]):
            assert r({"h3_blockCacheThreshold": bad}, None) is None
        # 非法 shot 级值不回落 episode 级 —— shot 键存在即独占该决定权。
        assert r({"h3_blockCacheThreshold": "abc"}, {"h3_blockCacheThreshold": 0.5}) is None

    def test_threshold_wire_encoding_e2e(self, tmp_path):
        captured: list[httpx.Request] = []
        with _client(_ok_handler(captured=captured)) as engine:
            engine.render(
                shot={"shot_id": "S15", "ltx_prompt": "x", "duration_sec": 5.0,
                      "h3_blockCache": True, "h3_blockCacheThreshold": 0.85},
                output_path=str(tmp_path / "out.mp4"),
            )
        fields, _ = _parse_multipart(captured[0])
        assert fields["blockCache"] == "true"
        assert fields["blockCacheThreshold"] == "0.85"

    def test_invalid_threshold_does_not_break_render(self, tmp_path):
        # 非法阈值静默忽略: blockCache 仍生效, 阈值字段不发, 渲染不崩。
        captured: list[httpx.Request] = []
        with _client(_ok_handler(captured=captured)) as engine:
            result = engine.render(
                shot={"shot_id": "S16", "ltx_prompt": "x", "duration_sec": 5.0,
                      "h3_blockCache": True, "h3_blockCacheThreshold": "abc"},
                output_path=str(tmp_path / "out.mp4"),
            )
        assert "degraded" not in result
        fields, _ = _parse_multipart(captured[0])
        assert fields["blockCache"] == "true"
        assert "blockCacheThreshold" not in fields

    # -- coexistence with h3_useCase / h3_motion ----------------------------

    def test_coexists_with_usecase_and_motion_fields(self, tmp_path):
        # 叠加用例: preview-lock + motion + blockCache + 阈值共存; blockCache
        # 字段位于 useCase/motion 之后、refImages 之前。
        turnaround = tmp_path / "tr.png"
        turnaround.write_bytes(_png_bytes())
        captured: list[httpx.Request] = []
        with _client(_ok_handler(captured=captured)) as engine:
            engine.render(
                shot={"shot_id": "S17", "ltx_prompt": "x", "duration_sec": 5.0,
                      "h3_useCase": "preview-lock", "h3_motion": "low",
                      "h3_blockCache": "on"},
                output_path=str(tmp_path / "out.mp4"),
                turnaround_paths=[str(turnaround)],
                episode_config={"h3_blockCacheThreshold": 0.3},
            )
        fields, files = _parse_multipart(captured[0])
        assert list(fields) == [
            "projectId", "prompt", "mode", "width", "height", "length",
            "filenamePrefix", "useCase", "motion", "blockCache",
            "blockCacheThreshold",
        ]
        assert fields["motion"] == "low"
        assert fields["blockCache"] == "true"
        assert fields["blockCacheThreshold"] == "0.3"
        # 二进制部件仍在全部文本字段之后。
        assert "tr.png" in files.get("refImages", [])

    def test_block_cache_logs_shot_id_and_threshold(self, tmp_path, caplog):
        import logging

        with caplog.at_level(logging.INFO, logger="plugins.kais_aigc.video_engine"):
            with _client(_ok_handler()) as engine:
                engine.render(
                    shot={"shot_id": "S18", "ltx_prompt": "x", "duration_sec": 5.0,
                          "h3_blockCache": True, "h3_blockCacheThreshold": 0.85},
                    output_path=str(tmp_path / "out.mp4"),
                )
        joined = " ".join(rec.getMessage() for rec in caplog.records)
        assert "S18" in joined
        assert "0.85" in joined


# ---------------------------------------------------------------------------
# D-09 degrade / raise contract (mirrors LTXVideoEngine._request tests)
# ---------------------------------------------------------------------------


class TestH3DegradeContract:
    def test_connect_error_degrades(self, tmp_path):
        def handler(request):
            raise httpx.ConnectError("no server")

        with _client(handler) as engine:
            result = engine.render(
                shot={"shot_id": "S", "ltx_prompt": "x", "duration_sec": 5.0},
                output_path=str(tmp_path / "out.mp4"),
            )
        assert result.get("degraded") is True
        assert "ConnectError" in result["reason"]

    def test_timeout_degrades(self, tmp_path):
        def handler(request):
            raise httpx.TimeoutException("timed out")

        with _client(handler) as engine:
            result = engine.render(
                shot={"shot_id": "S", "ltx_prompt": "x", "duration_sec": 5.0},
                output_path=str(tmp_path / "out.mp4"),
            )
        assert result.get("degraded") is True
        assert "TimeoutException" in result["reason"]

    def test_5xx_degrades(self, tmp_path):
        def handler(request):
            return httpx.Response(503, text="upstream down")

        with _client(handler) as engine:
            result = engine.render(
                shot={"shot_id": "S", "ltx_prompt": "x", "duration_sec": 5.0},
                output_path=str(tmp_path / "out.mp4"),
            )
        assert result.get("degraded") is True
        assert "503" in result["reason"]

    def test_429_degrades(self, tmp_path):
        def handler(request):
            return httpx.Response(429, text="slow down")

        with _client(handler) as engine:
            result = engine.render(
                shot={"shot_id": "S", "ltx_prompt": "x", "duration_sec": 5.0},
                output_path=str(tmp_path / "out.mp4"),
            )
        assert result.get("degraded") is True
        assert "429" in result["reason"]

    def test_4xx_raises_video_engine_error(self, tmp_path):
        def handler(request):
            return httpx.Response(400, text="bad request")

        with _client(handler) as engine:
            with pytest.raises(VideoEngineError, match="400"):
                engine.render(
                    shot={"shot_id": "S", "ltx_prompt": "x", "duration_sec": 5.0},
                    output_path=str(tmp_path / "out.mp4"),
                )

    def test_invalid_json_2xx_raises(self, tmp_path):
        def handler(request):
            if request.method == "POST":
                return httpx.Response(200, text="<html>not json</html>")
            return httpx.Response(200, content=b"x")

        with _client(handler) as engine:
            with pytest.raises(VideoEngineError, match="Invalid JSON"):
                engine.render(
                    shot={"shot_id": "S", "ltx_prompt": "x", "duration_sec": 5.0},
                    output_path=str(tmp_path / "out.mp4"),
                )

    def test_missing_video_url_degrades(self, tmp_path):
        def handler(request):
            if request.method == "POST":
                return httpx.Response(200, json={"oops": "no url"})
            return httpx.Response(200, content=b"x")

        with _client(handler) as engine:
            result = engine.render(
                shot={"shot_id": "S", "ltx_prompt": "x", "duration_sec": 5.0},
                output_path=str(tmp_path / "out.mp4"),
            )
        assert result.get("degraded") is True
        assert "video_url" in result["reason"]


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------


class TestH3Download:
    def test_download_4xx_degrades(self, tmp_path):
        def handler(request):
            if request.method == "POST":
                return httpx.Response(200, json={"video_url": "http://test-h3/files/x.mp4"})
            return httpx.Response(404, text="gone")

        with _client(handler) as engine:
            result = engine.render(
                shot={"shot_id": "S", "ltx_prompt": "x", "duration_sec": 5.0},
                output_path=str(tmp_path / "out.mp4"),
            )
        assert result.get("degraded") is True
        assert "download failed" in result["reason"]
        # Error-source discrimination (ep-demo-pixar fix): an HTTP 4xx must
        # surface as "http 404", not be conflated with a local fs failure.
        assert "http 404" in result["reason"]

    def test_download_local_fs_error_degrades_with_fs_reason(
        self, tmp_path, monkeypatch,
    ):
        """makedirs PermissionError must report 'local fs error' — the
        ep-demo-pixar bug where a root-absolute output_path made every
        variant degrade as a misleading 'download failed for <url>'."""

        def handler(request):
            if request.method == "POST":
                return httpx.Response(200, json={"video_url": "/files/x.mp4"})
            return httpx.Response(200, content=b"X")

        def _boom(path, exist_ok=False):
            raise PermissionError(13, "Permission denied", path)

        with _client(handler) as engine:
            monkeypatch.setattr("plugins.kais_aigc.video_engine.os.makedirs", _boom)
            result = engine.render(
                shot={"shot_id": "S", "ltx_prompt": "x", "duration_sec": 5.0},
                output_path=str(tmp_path / "out.mp4"),
            )
        assert result.get("degraded") is True
        assert "local fs error" in result["reason"]
        assert "Permission denied" in result["reason"]

    def test_download_relative_url_resolves_again_base(self, tmp_path):
        def handler(request):
            if request.method == "POST":
                # Relative URL — engine must resolve against base_url.
                return httpx.Response(200, json={"video_url": "/files/rel.mp4"})
            return httpx.Response(200, content=b"REL_BODY")

        out = str(tmp_path / "out.mp4")
        with _client(handler) as engine:
            result = engine.render(
                shot={"shot_id": "S", "ltx_prompt": "x", "duration_sec": 5.0},
                output_path=out,
            )
        assert result.get("clip_path") == out
        assert Path(out).read_bytes() == b"REL_BODY"


# ---------------------------------------------------------------------------
# P0-4 frame gate
# ---------------------------------------------------------------------------


class TestH3FrameGate:
    def test_frame_validator_pass_returns_success(self, tmp_path):
        out = str(tmp_path / "shot.mp4")
        with H3VideoEngine(
            base_url="http://test-h3",
            transport=httpx.MockTransport(_ok_handler()),
            frame_validator=lambda clip_path, expected: (True, "ok"),
        ) as engine:
            result = engine.render(
                shot={"shot_id": "S", "ltx_prompt": "x", "duration_sec": 5.0},
                output_path=out,
            )
        assert result.get("engine") == "h3"
        assert result.get("frame_count") == _compute_expected_frames(
            {"duration_sec": 5.0}
        )

    def test_frame_validator_fail_degrades_and_removes_clip(self, tmp_path):
        out = str(tmp_path / "shot.mp4")

        def failing_validator(clip_path, expected):
            return False, "trim_bypass: actual=5 expected=124"

        with H3VideoEngine(
            base_url="http://test-h3",
            transport=httpx.MockTransport(_ok_handler()),
            frame_validator=failing_validator,
        ) as engine:
            result = engine.render(
                shot={"shot_id": "S", "ltx_prompt": "x", "duration_sec": 5.0},
                output_path=out,
            )
        assert result.get("degraded") is True
        assert "frame validation failed" in result["reason"]
        assert "trim_bypass" in result["reason"]
        # The bad clip is removed so a re-render isn't masked by a stale file.
        assert not Path(out).exists()


# ---------------------------------------------------------------------------
# Lifecycle + WR-01 concurrency
# ---------------------------------------------------------------------------


class TestH3Lifecycle:
    def test_context_manager_closes_client(self):
        engine = H3VideoEngine(
            base_url="http://test-h3",
            transport=httpx.MockTransport(_ok_handler()),
            frame_validator=lambda c, e: (True, "ok"),
        )
        assert engine._client.is_closed is False
        with engine:
            assert engine._client.is_closed is False
        # After exit the httpx connection pool is released (CR-02 / p10b parity:
        # long-running daemons must not leak one Client per episode).
        assert engine._client.is_closed is True

    def test_concurrent_renders_serialize_under_lock(self, tmp_path):
        """WR-01: the _lock serializes POSTs so concurrent worker threads don't
        corrupt httpx connection state. Two renders run concurrently; the handler
        asserts it never sees overlapping POSTs (no re-entrancy)."""
        in_flight = {"count": 0, "max": 0}
        lock = threading.Lock()

        def handler(request):
            if request.method != "POST":
                return httpx.Response(200, content=b"x")
            with lock:
                in_flight["count"] += 1
                in_flight["max"] = max(in_flight["max"], in_flight["count"])
            # Simulate a tiny bit of work so concurrency would surface if the
            # lock were absent.
            import time as _t
            _t.sleep(0.01)
            with lock:
                in_flight["count"] -= 1
            return httpx.Response(200, json={"video_url": "http://test-h3/files/x.mp4"})

        engine = H3VideoEngine(
            base_url="http://test-h3",
            transport=httpx.MockTransport(handler),
            frame_validator=lambda c, e: (True, "ok"),
        )
        try:
            threads = []
            for i in range(4):
                t = threading.Thread(target=engine.render, kwargs={
                    "shot": {"shot_id": f"S{i}", "ltx_prompt": "x", "duration_sec": 5.0},
                    "output_path": str(tmp_path / f"out{i}.mp4"),
                })
                threads.append(t)
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        finally:
            engine.close()
        # The _lock serializes POSTs → never more than one in flight at once.
        assert in_flight["max"] == 1, (
            f"WR-01 violated: {in_flight['max']} overlapping POSTs (expected 1)"
        )


# ---------------------------------------------------------------------------
# Frame-grid math
# ---------------------------------------------------------------------------


class TestFrameMath:
    def test_six_seconds_snaps_to_141(self):
        # H3DurationAdapter doc example: 6.0s -> 144 raw -> snap 141 (141%17==5).
        assert _compute_expected_frames({"duration_sec": 6.0}) == 141

    def test_result_is_grid_aligned(self):
        for dur in (3.0, 4.5, 5.0, 7.0, 8.0, 10.0, 12.5):
            n = _compute_expected_frames({"duration_sec": dur})
            assert n % 17 == 5, f"{dur}s -> {n} not on n%17==5 grid"
            assert 5 <= n <= 362

    def test_fallback_when_adapter_unavailable(self, monkeypatch):
        """When the pipeline.engine_adapters import fails, the inline snap runs."""
        import builtins

        real_import = builtins.__import__

        def blocking_import(name, *args, **kwargs):
            if name.startswith("pipeline.engine_adapters"):
                raise ImportError("blocked for test")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", blocking_import)
        n = _compute_expected_frames({"duration_sec": 6.0})
        assert n == 141  # inline snap matches the adapter


# ---------------------------------------------------------------------------
# final 档 vdn-8 自动路由副档 (2026-09-16 定谳落地)
# ---------------------------------------------------------------------------


def _final_detail_shot(**over) -> dict:
    """final 档细节镜基准 shot: 单人 + 对白 + 中动 + 5s (124f ≤ 226f 边界内)。

    camera_movement="push_in" 无关键词命中 → medium (p11a 默认档);
    h3_useCase 不设 —— 默认 final-shot, 即自动路由的真实生产形态。
    """
    shot: dict = {
        "shot_id": "S20",
        "ltx_prompt": "x",
        "duration_sec": 5.0,
        "character_refs": [{"name": "Aria", "turnaround_path": "aria.png"}],
        "dialogue_text": "你终于来了。",
        "camera_movement": "push_in",
    }
    shot.update(over)
    return shot


class TestH3VdnFinalRouting:
    """``_route_vdn_final`` 判据表 + ``_resolve_h3vdn`` 三层解析 +
    multipart/render 接线 (0916 gpunoise 四臂盲选定谳: vdn-8 得分率 72.2%
    全场最高, 与 lxv 对拍质量平局, 速度快 1.3-1.4× —— final 档细节镜的
    quality-parity 速度副档)。

    红线: 预览档永不自动 vdn; 显式 h3_vdn 配置全量开行为不变; >226f 硬边界
    (KAP 241f, 0907 OOM 定谳) 细节镜留 legacy 链原长渲染; 无信号 shot
    multipart 与基线逐字节等价。
    """

    # -- _route_vdn_final 判据表 -------------------------------------------

    def test_final_single_person_dialogue_auto_routes(self):
        # 细节信号一: 对白镜 (单人 + 对白, final 档) → 自动路由。
        assert H3VideoEngine._route_vdn_final(
            _final_detail_shot(), None, "final-shot") is True

    def test_final_single_person_closeup_scale_auto_routes(self):
        # 细节信号二: 特写景别 —— shot_scale 大写化子串含 CU (MCU/BCU 同命中)。
        shot = _final_detail_shot(dialogue_text="", shot_scale="MCU")
        assert H3VideoEngine._route_vdn_final(
            shot, None, "final-shot") is True

    def test_final_closeup_shot_type_fallback_and_casing(self):
        # shot_scale 缺失回落 shot_type; 小写/带空白规整后命中 (同 p09
        # shot_scale 规整法 strip().upper())。
        assert H3VideoEngine._route_vdn_final(
            _final_detail_shot(dialogue_text="", shot_type=" insert "),
            None, "final-shot") is True
        assert H3VideoEngine._route_vdn_final(
            _final_detail_shot(dialogue_text="", shot_scale=" cu "),
            None, "final-shot") is True

    def test_final_single_person_low_motion_auto_routes(self):
        # 细节信号三: 低动 (静止/极慢 —— 细节敏感, 速度收益最稳)。
        shot = _final_detail_shot(
            dialogue_text="", camera_movement="locked_off")
        assert H3VideoEngine._route_vdn_final(
            shot, None, "final-shot") is True

    def test_preview_never_auto_routes(self):
        # 预览档永不自动 vdn —— 同信号 use_case=preview-lock 直接 False,
        # 回退 preview-lock 动态路由现有链。
        assert H3VideoEngine._route_vdn_final(
            _final_detail_shot(), None, "preview-lock") is False

    def test_final_multi_person_no_route(self):
        # 人物数判据: character_refs 长度 2 → False (工单 a)。
        shot = _final_detail_shot(
            character_refs=[{"name": "Aria"}, {"name": "Bo"}])
        assert H3VideoEngine._route_vdn_final(
            shot, None, "final-shot") is False

    def test_final_medium_motion_no_detail_signal_no_route(self):
        # 单人 + 中动 + 非特写 (WS) + 无对白: 细节信号零命中 → 保守回退 False。
        shot = _final_detail_shot(dialogue_text="", shot_scale="WS")
        assert H3VideoEngine._route_vdn_final(
            shot, None, "final-shot") is False

    def test_boundary_unsafe_length_no_route(self):
        # 硬边界保护 (工单 c): 钳前 >226f → False —— 15s→362f / 10s→243f
        # (226 之后下一格), 不吃降档截断, 留 legacy 链原长渲染。
        assert H3VideoEngine._route_vdn_final(
            _final_detail_shot(duration_sec=15.0), None, "final-shot") is False
        assert H3VideoEngine._route_vdn_final(
            _final_detail_shot(duration_sec=10.0), None, "final-shot") is False

    def test_boundary_safe_length_routes(self):
        # 钳后 ≤226f → True: 5s→124f; 9.4s 恰好 snap 到网格最大 226f (等界
        # 亦安全)。
        assert H3VideoEngine._route_vdn_final(
            _final_detail_shot(), None, "final-shot") is True
        assert H3VideoEngine._route_vdn_final(
            _final_detail_shot(duration_sec=9.4), None, "final-shot") is True

    def test_route_ignores_episode_config(self):
        # episode_config 不参与判定 (判据均为 shot 级信号 + 档位;
        # 抑制语义归 _resolve_h3vdn 显式层)。
        assert H3VideoEngine._route_vdn_final(
            _final_detail_shot(), {"h3_vdn": False}, "final-shot") is True

    def test_route_logs_use_case_and_hit_signals(self, caplog):
        # 工单: 日志带 use_case 与命中信号 (scene-route h3_vdn_final=)。
        import logging

        with caplog.at_level(
                logging.INFO, logger="plugins.kais_aigc.video_engine"):
            H3VideoEngine._route_vdn_final(
                _final_detail_shot(shot_id="S20"), None, "final-shot")
        joined = caplog.text
        assert "S20" in joined
        assert "scene-route h3_vdn_final=True" in joined
        assert "use_case=final-shot" in joined
        assert "characters=1" in joined
        assert "dialogue=True" in joined
        assert "frames=124" in joined

    # -- _resolve_h3vdn 三层解析 (shot > episode > auto) ---------------------

    def test_shot_false_suppresses_episode_true_and_auto(self):
        # 键存在即独占决定权: 显式 False 既不回落 episode 级 true, 也不回落
        # 自动路由 (即使 auto 信号全命中)。
        assert H3VideoEngine._resolve_h3vdn(
            _final_detail_shot(h3_vdn=False), {"h3_vdn": True}, "final-shot",
        ) is False
        assert H3VideoEngine._resolve_h3vdn(
            _final_detail_shot(h3_vdn="off"), None, "final-shot",
        ) is False

    def test_shot_true_full_volume_even_in_preview(self):
        # shot 级显式 True: preview 档也 True —— 显式开关不受 final 门限制
        # (行为不变)。
        assert H3VideoEngine._resolve_h3vdn(
            _final_detail_shot(h3_vdn=True), None, "preview-lock") is True

    def test_episode_true_full_volume_when_no_shot_override(self):
        # episode 级 h3_vdn=true: 无 shot 覆盖 → 全量 True (preview 也 vdn,
        # 行为不变)。
        assert H3VideoEngine._resolve_h3vdn(
            {"shot_id": "S21", "ltx_prompt": "x"}, {"h3_vdn": True},
            "preview-lock") is True

    def test_auto_engages_when_both_explicit_layers_absent(self):
        # 两层显式配置均缺 → 自动路由判定 (原 _resolve_vdn 语义变化点)。
        assert H3VideoEngine._resolve_h3vdn(
            _final_detail_shot(), None, "final-shot") is True
        assert H3VideoEngine._resolve_h3vdn(
            _final_detail_shot(), {}, "final-shot") is True

    def test_resolve_logs_three_state_source(self, caplog):
        # 渲染消费点日志注明三态来源 (source=shot/episode/auto)。
        import logging

        with caplog.at_level(
                logging.INFO, logger="plugins.kais_aigc.video_engine"):
            H3VideoEngine._resolve_h3vdn(
                _final_detail_shot(h3_vdn=True, shot_id="SA"), None, "final-shot")
            H3VideoEngine._resolve_h3vdn(
                _final_detail_shot(shot_id="SB"), {"h3_vdn": True}, "final-shot")
            H3VideoEngine._resolve_h3vdn(
                _final_detail_shot(shot_id="SC"), None, "final-shot")
        joined = caplog.text
        assert "SA h3_vdn=on (source=shot)" in joined
        assert "SB h3_vdn=on (source=episode)" in joined
        assert "SC h3_vdn=on (source=auto" in joined

    # -- multipart / render 接线 --------------------------------------------

    def _build(self, shot: dict, episode_config: dict | None = None) -> list:
        """裸实例直调 _build_multipart (不触网), 返回 multipart 段表。"""
        return H3VideoEngine()._build_multipart(
            shot, prompt=None, episode_config=episode_config,
            turnaround_paths=[], scene_ref_path=None,
            voice_clip_path=None, first_frame=None,
        )

    def test_auto_routed_final_shot_posts_vdn_profile(self):
        # 无显式配置 + final 细节镜 → profile=vdn-8 替代 useCase/motion。
        files = self._build(_final_detail_shot())
        fields = {n: p[1] for n, p in files if p[0] is None}
        assert fields["profile"] == VDN_PROFILE
        assert "useCase" not in fields
        assert "motion" not in fields

    def test_preview_same_signals_keeps_dynamic_route(self, tmp_path):
        # preview + 同信号: 不自动 vdn, 走 preview-lock 动态路由现有链。
        # (h3_rh=False 隔离 rh 自动路由 —— rh 判据无档位门, 是既有行为。)
        captured: list[httpx.Request] = []
        with _client(_ok_handler(captured=captured)) as engine:
            result = engine.render(
                shot=_final_detail_shot(h3_rh=False),
                output_path=str(tmp_path / "out.mp4"),
                episode_config={"h3_useCase": "preview-lock"},
            )
        assert not result.get("degraded"), result
        fields, _ = _parse_multipart(captured[0])
        assert "profile" not in fields
        assert fields["useCase"] == "preview-lock"
        assert "motion" in fields

    def test_auto_overlap_axis_vdn_beats_rh(self):
        # 自动重叠轴 (单人+对白细节镜同时命中两条自动路由): vdn > rh ——
        # render 分支既有顺序零改动 (0916 定谳: 质量平局 + 更快的 vdn-8
        # 审定蓝图臂 > rh-v4 快速档)。
        files = self._build(_final_detail_shot())
        assert {n: p[1] for n, p in files if p[0] is None}["profile"] == VDN_PROFILE

    def test_rh_suppression_does_not_block_vdn_auto(self):
        # 交叉 pin: h3_rh=False 抑制只作用于 rh 臂, vdn 自动路由独立判定
        # (单人对白细节镜 → 仍进 vdn-8)。
        files = self._build(_final_detail_shot(h3_rh=False))
        assert {n: p[1] for n, p in files if p[0] is None}["profile"] == VDN_PROFILE

    def test_boundary_unsafe_detail_shot_renders_legacy_chain(self, tmp_path):
        # 硬边界保护 e2e: 15s (362f > 226f) 低动细节镜不自动 vdn —— 边界
        # 一票否决后落 legacy 链原长渲染 (低动不在 rh 判据内, rh 不接;
        # useCase=final-shot, length=362, 无 profile, P0-4 门按未钳 362 判)。
        captured: list[httpx.Request] = []
        with _client(_ok_handler(captured=captured)) as engine:
            result = engine.render(
                shot=_final_detail_shot(
                    dialogue_text="", camera_movement="locked_off",
                    duration_sec=15.0),
                output_path=str(tmp_path / "out.mp4"),
            )
        assert not result.get("degraded"), result
        assert result["frame_count"] == 362  # 原值 snap, 未钳
        fields, _ = _parse_multipart(captured[0])
        assert "profile" not in fields
        assert fields["useCase"] == "final-shot"
        assert fields["length"] == "362"

    def test_boundary_unsafe_dialogue_shot_falls_to_rh(self):
        # 边界超界细节镜若 rh 判据可接 (单人对白中动) → 让位 rh-v4 快速档,
        # length 原值透传 (rh 无预钳) —— 不吃 vdn 226 降档截断。
        files = self._build(_final_detail_shot(duration_sec=15.0))
        fields = {n: p[1] for n, p in files if p[0] is None}
        assert fields["profile"] == "rh-v4"
        assert fields["length"] == "362"

    def test_explicit_double_on_vdn_beats_rh_regression(self):
        # 显式双开 vdn>rh 优先级回归 (render 分支既有顺序, 工单钉死)。
        files = self._build(_final_detail_shot(h3_vdn=True, h3_rh=True))
        assert {n: p[1] for n, p in files if p[0] is None}["profile"] == VDN_PROFILE

    def test_signal_free_shot_multipart_byte_equivalent_baseline(self):
        # 红线: 无路由信号 shot (自动路由判 False) 的全量 part 元组与改动前
        # 逐字节等价 —— 默认零行为变化。
        files = self._build({"shot_id": "S22", "ltx_prompt": "x",
                             "duration_sec": 5.0})
        assert files == [
            ("projectId", (None, "1")),
            ("prompt", (None, "x")),
            ("mode", (None, "ref2va")),
            ("width", (None, "768")),
            ("height", (None, "1344")),
            ("length", (None, "124")),
            ("filenamePrefix", (None, "S22")),
            ("useCase", (None, "final-shot")),
        ]

    def test_auto_routed_render_gates_on_uncapped_length(self, tmp_path):
        # 自动路由 5s 细节镜密闭渲染: P0-4 帧门按 124 (边界内无预钳) 判,
        # POST 携带 profile=vdn-8。
        posted: list[bytes] = []
        gate_expected: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "POST":
                posted.append(request.content)
                return httpx.Response(
                    200, json={"code": 200,
                               "data": {"videoUrl": "/oss/vdn_final.mp4"}})
            return httpx.Response(200, content=b"fake-mp4-bytes")

        def fake_gate(clip_path: str, expected: int) -> tuple[bool, str]:
            gate_expected.append(expected)
            return True, f"ok (frames={expected})"

        engine = H3VideoEngine(
            transport=httpx.MockTransport(handler), frame_validator=fake_gate,
        )
        result = engine.render(
            shot=_final_detail_shot(),
            output_path=str(tmp_path / "S20.mp4"),
        )
        assert not result.get("degraded"), result
        assert result["frame_count"] == 124
        assert gate_expected == [124]
        body = posted[0]
        assert b'name="profile"' in body and b"vdn-8" in body
        assert b'name="useCase"' not in body
