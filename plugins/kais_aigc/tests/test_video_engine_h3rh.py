"""test_video_engine_h3rh.py — rh-v4 快速档通道 + 场景路由引擎层验收 (2026-09-12).

KAP 平台侧 0911 已全注册 profile=rh-v4 (H3_EXPOSED_PROFILES 白名单 +
H3_RH_V4 预射蓝图: 4 步恒定 + 14_lora LoRA 恒载), 本批引擎侧接入、KAP 零
改动。本文件证明管线侧 ``H3VideoEngine`` 的 rh-v4 通道全链路:

  1. ``_resolve_h3rh`` 解析优先级: shot.h3_rh > episode_config.h3_rh >
     _route_rh 自动路由 > off; 显式 False 是 per-shot 抑制不回落 (既不回落
     episode 级 true, 也不回落自动路由 —— _resolve_vdn 语义家族);
  2. ``_route_rh`` 判据表 (0911 盲测定谳: rh-v4 反超轴 = 单人口型 + 非人物
     高速, 渲染快 1.6-2.5×; LXV 保有多人对白/多人追逐): 单人+对白+中/高动
     → True; 多人 → False; 非人物高速 → True; 低动 → False; 信号缺失保守
     回退 False;
  3. 接线形态 = profile-only (``profile=rh-v4`` 替代 useCase/motion, 同 vdn
     先例: useCase 在场会劫持步数/音频预射, 偏离 4 步蓝图); 非 rh 臂字段
     序列与基线逐字节等价 (红线: 默认零行为变化 —— 无路由信号的 shot
     全量 part 元组与改动前逐项相等);
  4. length 原值透传 (rh-v4 蓝图无帧网格条款, 不做 vdn 式 226 预钳);
  5. vdn > rh 优先级: 两开关同开时 profile=vdn-8 (vdn-8 审定 8 步蓝图臂
     > rh-v4 快速档, 工单 C1 裁决);
  6. render() 密闭链路 (httpx.MockTransport, D-04 注入点): h3_rh 臂 POST
     body 断言 + P0-4 帧门按未钳 length 判。

参照 test_video_engine_vdn.py 桩法: 裸实例直调 _build_multipart +
MockTransport 密闭渲染。
"""
from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

HERMES_ROOT = Path(__file__).resolve().parents[3]
if str(HERMES_ROOT) not in sys.path:
    sys.path.insert(0, str(HERMES_ROOT))

from plugins.kais_aigc.video_engine import (  # noqa: E402
    H3VideoEngine,
    RH_V4_PROFILE,
    VDN_PROFILE,
)


def _build(shot: dict, episode_config: dict | None = None) -> list:
    """裸实例直调 _build_multipart (不触碰 transport), 返回 multipart 段表。"""
    return H3VideoEngine()._build_multipart(
        shot,
        prompt=None,
        episode_config=episode_config,
        turnaround_paths=[],
        scene_ref_path=None,
        voice_clip_path=None,
        first_frame=None,
    )


def _fields(files: list) -> dict:
    """文本段名→值 (二进制段 refImages/ttsAudio/image 不在本测试路径)。"""
    return {name: part[1] for name, part in files if part[0] is None}


def _names(files: list) -> list:
    return [name for name, _part in files]


def _routable_shot(**over) -> dict:
    """判据全满足的 shot (单人 + 对白 + 中动) —— 自动路由应命中。

    character_refs 用 dict 元素 (p11b _extract_character_names 同源形态);
    camera_movement="push_in" 无关键词命中 → medium (p11a 默认档)。
    """
    shot: dict = {
        "shot_id": "S07",
        "ltx_prompt": "x",
        "duration_sec": 5.0,
        "character_refs": [{"name": "Aria", "turnaround_path": "aria.png"}],
        "dialogue_text": "你终于来了。",
        "camera_movement": "push_in",
    }
    shot.update(over)
    return shot


# ---------------------------------------------------------------------------
# 1. _resolve_h3rh 解析优先级 (shot > episode > 自动路由 > off)
# ---------------------------------------------------------------------------


class TestResolveH3rhPriority:
    def test_shot_true_wins_over_episode_false(self):
        assert H3VideoEngine._resolve_h3rh({"h3_rh": True}, {"h3_rh": False}) is True

    def test_episode_true_when_shot_key_absent(self):
        assert H3VideoEngine._resolve_h3rh(
            {"shot_id": "S01"}, {"h3_rh": True}) is True

    def test_auto_route_engages_when_both_absent(self):
        # 自动路由档: 无显式配置 + 判据全满足 → True。
        assert H3VideoEngine._resolve_h3rh(_routable_shot(), None) is True

    def test_auto_route_off_for_signal_free_shot(self):
        # 无显式配置 + 无路由信号 → False (保守回退)。
        assert H3VideoEngine._resolve_h3rh(
            {"shot_id": "S01", "ltx_prompt": "x"}, None) is False

    def test_explicit_false_suppresses_episode_true_no_fallback(self):
        # shot 键存在即独占决定权 —— 显式 False 不回落 episode 级 true。
        assert H3VideoEngine._resolve_h3rh({"h3_rh": False}, {"h3_rh": True}) is False

    def test_explicit_false_suppresses_auto_route(self):
        # 显式 False 同样不回落自动路由 —— per-shot 抑制是终局。
        assert H3VideoEngine._resolve_h3rh(_routable_shot(h3_rh=False), None) is False

    def test_episode_false_suppresses_auto_route(self):
        assert H3VideoEngine._resolve_h3rh(
            _routable_shot(), {"h3_rh": False}) is False

    @pytest.mark.parametrize("raw", [True, "true", "True", " 1 ", "on", "ON", 1])
    def test_truthy_forms(self, raw):
        assert H3VideoEngine._resolve_h3rh({"h3_rh": raw}, None) is True

    @pytest.mark.parametrize("raw", [False, "off", "no", "", 0, None, "garbage", 2])
    def test_falsy_or_garbage_forms_are_off(self, raw):
        assert H3VideoEngine._resolve_h3rh({"h3_rh": raw}, None) is False

    def test_string_false_suppresses_episode_true(self):
        # 字符串抑制同构: "off" 在 shot 键内即终局, 不回落。
        assert H3VideoEngine._resolve_h3rh({"h3_rh": "off"}, {"h3_rh": True}) is False

    def test_episode_level_string_truthy(self):
        assert H3VideoEngine._resolve_h3rh(
            {"shot_id": "S01"}, {"h3_rh": "true"}) is True


# ---------------------------------------------------------------------------
# 2. _route_rh 判据表 (0911 盲测定谳路由轴)
# ---------------------------------------------------------------------------


class TestRouteRhMatrix:
    def test_single_person_dialogue_medium_routes(self):
        # C03 轴: 单人竖屏独白口型 —— rh-v4 反超 (PK 轮优)。
        assert H3VideoEngine._route_rh(_routable_shot()) is True

    def test_single_person_dialogue_high_routes(self):
        assert H3VideoEngine._route_rh(
            _routable_shot(camera_movement="tracking")) is True

    def test_multi_person_never_routes(self):
        # LXV 保有多人对白 (LMH 轮 C02 / PK 轮 C01) —— character_refs≥2 直接出局。
        assert H3VideoEngine._route_rh(_routable_shot(character_refs=[
            {"name": "Aria"}, {"name": "Bo"}])) is False

    def test_non_person_high_motion_routes(self):
        # C05 轴: 非人物高速 —— rh-v4 反超 (PK 轮优)。
        assert H3VideoEngine._route_rh(_routable_shot(
            character_refs=[], dialogue_text="", camera_movement="crash_zoom",
        )) is True

    def test_non_person_medium_routes(self):
        # 非人物不需要对白判据 (无人物则无口型保真需求); medium 可路由。
        assert H3VideoEngine._route_rh(_routable_shot(
            character_refs=[], dialogue_text="")) is True

    def test_single_person_low_motion_no_route(self):
        # low (静止/极慢) 不路由 —— 极低动不缺速度且细节敏感。
        assert H3VideoEngine._route_rh(
            _routable_shot(camera_movement="locked_off")) is False

    def test_non_person_low_motion_no_route(self):
        assert H3VideoEngine._route_rh(_routable_shot(
            character_refs=[], dialogue_text="", camera_movement="static",
        )) is False

    def test_single_person_no_dialogue_no_route(self):
        # 判据 2: 单人无对白 (且非非人物) → 不路由。
        assert H3VideoEngine._route_rh(
            _routable_shot(dialogue_text="")) is False

    def test_missing_fields_conservative_false(self):
        # 路由信号全缺 → 保守回退 False (红线: 默认零行为变化)。
        assert H3VideoEngine._route_rh({"shot_id": "S01"}) is False
        assert H3VideoEngine._route_rh({"shot_id": "S01"}, {}) is False

    def test_missing_refs_counted_as_single(self):
        # 工单 C2.1: character_refs 缺字段按 1 算 —— 无明确多人证据不当多人
        # 排除, 但也不当非人物 (判据 2 仍需对白)。
        shot = _routable_shot()
        del shot["character_refs"]
        assert H3VideoEngine._route_rh(shot) is True

    def test_missing_camera_movement_defaults_medium(self):
        # p11a _classify_motion 同构: 空/缺失 → medium (判据 3 可过)。
        shot = _routable_shot()
        del shot["camera_movement"]
        assert H3VideoEngine._route_rh(shot) is True

    def test_dialogue_note_counts(self):
        # 对白信号同源字段: dialogue_note 非空同样算对白/口型镜头。
        assert H3VideoEngine._route_rh(
            _routable_shot(dialogue_text="", dialogue_note="低声自语")) is True

    def test_whitespace_dialogue_not_counted(self):
        assert H3VideoEngine._route_rh(
            _routable_shot(dialogue_text="   ")) is False

    def test_legacy_camera_motion_alias(self):
        # p11a 兼容旧拼写: camera_motion / camera_intent 同样参与分级。
        shot = _routable_shot()
        del shot["camera_movement"]
        shot["camera_motion"] = "handheld"
        assert H3VideoEngine._route_rh(shot) is True

    def test_high_keyword_precedence_over_low(self):
        # p11a 先查 high 再查 low: 同串双命中时 high 胜 → 可路由。
        assert H3VideoEngine._route_rh(
            _routable_shot(camera_movement="handheld slow_pan")) is True

    def test_route_logs_basis_and_verdict(self, caplog):
        # 工单 C2: 日志打判定依据 (人物数/对白/运动档) + 路由结果。
        with caplog.at_level("INFO", logger="plugins.kais_aigc.video_engine"):
            H3VideoEngine._route_rh(_routable_shot(shot_id="S07"))
        assert "S07" in caplog.text
        assert "characters=1" in caplog.text
        assert "dialogue=True" in caplog.text
        assert "motion=medium" in caplog.text
        assert "h3_rh=True" in caplog.text


# ---------------------------------------------------------------------------
# 3. _build_multipart 接线形态 (profile-only) + 默认零行为变化专项断言
# ---------------------------------------------------------------------------


class TestRhMultipartWiring:
    def test_rh_shot_sends_profile_not_usecase(self):
        files = _build({"shot_id": "S07", "ltx_prompt": "x",
                        "duration_sec": 5.0, "h3_rh": True})
        fields = _fields(files)
        assert fields["profile"] == RH_V4_PROFILE
        assert "useCase" not in fields
        assert "motion" not in fields

    def test_rh_suppresses_usecase_even_when_configured(self):
        # P11a/P11b 的 shot.setdefault("h3_useCase", ...) 与 h3_motion 在场时,
        # rh 分支仍独占 —— profile-only, 不并发。
        files = _build({"shot_id": "S07", "ltx_prompt": "x",
                        "duration_sec": 5.0, "h3_rh": True,
                        "h3_useCase": "preview-lock", "h3_motion": "high"},
                       {"h3_motion": "high"})
        fields = _fields(files)
        assert fields["profile"] == RH_V4_PROFILE
        assert "useCase" not in fields
        assert "motion" not in fields

    def test_episode_level_rh_drives_profile(self):
        files = _build({"shot_id": "S07", "ltx_prompt": "x", "duration_sec": 5.0},
                       {"h3_rh": True})
        assert _fields(files)["profile"] == RH_V4_PROFILE

    def test_auto_routed_shot_drives_profile(self):
        # 无显式配置 + 判据命中 → 自动路由进 rh-v4 臂。
        # (0916 起 final 细节镜 vdn 自动路由上线: 单人对白细节镜重叠轴按
        # vdn > rh 优先级归 vdn-8 —— 见 test_video_engine.py
        # TestH3VdnFinalRouting; rh 自动路由轴收敛到其独占反超轴 —— 非人物
        # 中/高速, vdn 细节信号 [对白/特写/低动] 不覆盖。)
        files = _build(_routable_shot(
            character_refs=[], dialogue_text="", camera_movement="crash_zoom"))
        fields = _fields(files)
        assert fields["profile"] == RH_V4_PROFILE
        assert "useCase" not in fields

    def test_shot_false_suppresses_episode_true_usecase_path(self):
        files = _build({"shot_id": "S07", "ltx_prompt": "x",
                        "duration_sec": 5.0, "h3_rh": False},
                       {"h3_rh": True})
        fields = _fields(files)
        assert "profile" not in fields
        assert fields["useCase"] == "final-shot"  # legacy 默认档

    def test_shot_false_suppresses_auto_route_usecase_path(self):
        # 判据全满足但显式 h3_rh=False → 抑制自动路由, 走 useCase 默认链。
        # (shot 换 rh 独占轴 —— 非人物高速: 0916 起单人对白细节镜即使 rh 被
        # 抑制也会由 vdn 自动路由接住, 不再落 useCase 链, 见
        # test_video_engine.py TestH3VdnFinalRouting。)
        files = _build(_routable_shot(
            character_refs=[], dialogue_text="", camera_movement="crash_zoom",
            h3_rh=False))
        fields = _fields(files)
        assert "profile" not in fields
        assert fields["useCase"] == "final-shot"

    def test_signal_free_shot_multipart_byte_equivalent_to_baseline(self):
        # 工单 C2 专项断言: 无任何新字段/路由信号的 shot, 全量 part 元组
        # (名+值+顺序) 与改动前逐字节等价 —— 默认零行为变化。
        files = _build({"shot_id": "S05", "ltx_prompt": "x", "duration_sec": 5.0})
        assert files == [
            ("projectId", (None, "1")),
            ("prompt", (None, "x")),
            ("mode", (None, "ref2va")),
            ("width", (None, "768")),
            ("height", (None, "1344")),
            ("length", (None, "124")),
            ("filenamePrefix", (None, "S05")),
            ("useCase", (None, "final-shot")),
        ]

    def test_preview_lock_shot_keeps_motion_field(self):
        # 非 rh 的 preview-lock 路由零改动: useCase + motion 照旧。
        files = _build({"shot_id": "S05", "ltx_prompt": "x", "duration_sec": 5.0,
                        "h3_useCase": "preview-lock", "h3_motion": "low"})
        assert _names(files) == [
            "projectId", "prompt", "mode", "width", "height",
            "length", "filenamePrefix", "useCase", "motion",
        ]
        assert _fields(files)["motion"] == "low"

    def test_rh_coexists_with_blockcache_passthrough(self):
        # blockCache 透传不被 rh 臂门控 (与 vdn 先例一致的 "按配置透传")。
        files = _build({"shot_id": "S07", "ltx_prompt": "x",
                        "duration_sec": 5.0, "h3_rh": True,
                        "h3_blockCache": True},
                       {"h3_blockCacheThreshold": 0.85})
        fields = _fields(files)
        assert fields["profile"] == RH_V4_PROFILE
        assert fields["blockCache"] == "true"
        assert fields["blockCacheThreshold"] == "0.85"


# ---------------------------------------------------------------------------
# 4. length 原值透传 (无 vdn 式预钳)
# ---------------------------------------------------------------------------


class TestRhLengthPassthrough:
    def test_rh_shot_full_duration_length_uncapped(self):
        # 15.0s → 362f (网格最大)。vdn 会预钳 226; rh-v4 蓝图无帧网格条款
        # (0911 双批 229f/243f 均过 400 守卫) → 原值透传。
        files = _build({"shot_id": "S09", "ltx_prompt": "x",
                        "duration_sec": 15.0, "h3_rh": True})
        assert _fields(files)["length"] == "362"

    def test_auto_routed_shot_length_uncapped(self):
        files = _build(_routable_shot(duration_sec=15.0))
        assert _fields(files)["length"] == "362"

    def test_rh_shot_short_duration_untouched(self):
        # 5.0s → snap 上取 124 (120%17=1, delta_up=4 < delta_down=16)。
        files = _build({"shot_id": "S09", "ltx_prompt": "x",
                        "duration_sec": 5.0, "h3_rh": True})
        assert _fields(files)["length"] == "124"


# ---------------------------------------------------------------------------
# 5. vdn > rh 优先级 (两臂同开裁决)
# ---------------------------------------------------------------------------


class TestVdnRhPrecedence:
    def test_both_explicit_on_vdn_wins(self):
        files = _build({"shot_id": "S08", "ltx_prompt": "x",
                        "duration_sec": 5.0, "h3_vdn": True, "h3_rh": True})
        assert _fields(files)["profile"] == VDN_PROFILE  # vdn-8, 非 rh-v4

    def test_both_episode_level_on_vdn_wins(self):
        files = _build({"shot_id": "S08", "ltx_prompt": "x", "duration_sec": 5.0},
                       {"h3_vdn": True, "h3_rh": True})
        assert _fields(files)["profile"] == VDN_PROFILE

    def test_explicit_vdn_beats_auto_routed_rh(self):
        # 显式 vdn vs 自动路由 rh: 审定蓝图臂优先, 自动路由让位。
        files = _build(_routable_shot(h3_vdn=True))
        assert _fields(files)["profile"] == VDN_PROFILE

    def test_vdn_priority_logged(self, caplog):
        with caplog.at_level("INFO", logger="plugins.kais_aigc.video_engine"):
            _build({"shot_id": "S08", "ltx_prompt": "x", "duration_sec": 5.0,
                    "h3_vdn": True, "h3_rh": True})
        assert "h3_vdn 优先" in caplog.text


# ---------------------------------------------------------------------------
# 6. render() 密闭链路 (MockTransport, D-04 注入点)
# ---------------------------------------------------------------------------


class TestRhRenderEndToEnd:
    def test_rh_render_posts_profile_and_gates_on_raw_length(self, tmp_path):
        """15s rh shot 密闭渲染: multipart 携带 profile=rh-v4 无 useCase;
        P0-4 帧门按未钳的 362 判 (rh 无预钳 —— 门与请求帧数一致)。"""
        posted: list[bytes] = []
        gate_expected: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "POST":
                posted.append(request.content)
                return httpx.Response(
                    200, json={"code": 200,
                               "data": {"videoUrl": "/oss/rh_fake.mp4"}})
            return httpx.Response(200, content=b"fake-mp4-bytes")

        def fake_gate(clip_path: str, expected: int) -> tuple[bool, str]:
            gate_expected.append(expected)
            return True, f"ok (frames={expected})"

        engine = H3VideoEngine(
            transport=httpx.MockTransport(handler), frame_validator=fake_gate,
        )
        result = engine.render(
            shot={"shot_id": "S09", "ltx_prompt": "x",
                  "duration_sec": 15.0, "h3_rh": True},
            output_path=str(tmp_path / "S09.mp4"),
        )

        assert not result.get("degraded"), result
        assert result["frame_count"] == 362  # 原值 snap, 未钳
        assert gate_expected == [362]  # 门与请求帧数一致
        assert len(posted) == 1
        body = posted[0]
        assert b'name="profile"' in body and b"rh-v4" in body
        assert b'name="useCase"' not in body
        assert b'name="motion"' not in body

    def test_auto_routed_render_posts_profile(self, tmp_path):
        # (shot 换 rh 独占轴 —— 非人物高速: 单人对白细节镜重叠轴 0916 起归
        # vdn 自动路由, 见 test_video_engine.py TestH3VdnFinalRouting。)
        posted: list[bytes] = []

        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "POST":
                posted.append(request.content)
                return httpx.Response(
                    200, json={"code": 200,
                               "data": {"videoUrl": "/oss/rh_auto.mp4"}})
            return httpx.Response(200, content=b"fake-mp4-bytes")

        engine = H3VideoEngine(
            transport=httpx.MockTransport(handler),
            frame_validator=lambda p, e: (True, "ok"),
        )
        result = engine.render(
            shot=_routable_shot(
                character_refs=[], dialogue_text="",
                camera_movement="crash_zoom"),
            output_path=str(tmp_path / "S07.mp4"),
        )
        assert not result.get("degraded"), result
        assert b'name="profile"' in posted[0] and b"rh-v4" in posted[0]
        assert b'name="useCase"' not in posted[0]

    def test_signal_free_render_still_posts_usecase(self, tmp_path):
        posted: list[bytes] = []

        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "POST":
                posted.append(request.content)
                return httpx.Response(
                    200, json={"code": 200,
                               "data": {"videoUrl": "/oss/fake.mp4"}})
            return httpx.Response(200, content=b"fake-mp4-bytes")

        engine = H3VideoEngine(
            transport=httpx.MockTransport(handler),
            frame_validator=lambda p, e: (True, "ok"),
        )
        result = engine.render(
            shot={"shot_id": "S10", "ltx_prompt": "x", "duration_sec": 5.0},
            output_path=str(tmp_path / "S10.mp4"),
        )
        assert not result.get("degraded"), result
        assert b'name="useCase"' in posted[0]
        assert b'name="profile"' not in posted[0]
