"""test_camera_move_intent.py — camera_move 意图驱动 auto_attach 接线验收 (批次2, 2026-09-28).

KAP 侧批次1 (commit 8c794fcf) 在 /api/production/minimax-h3/generate 上线
意图驱动 auto_attach: camera_move 字段 → registry ``auto_attach.trigger``
查表挂载, 装配任何失败降级 prompt-only。本文件证明 KMC 消费端全链路:

  1. 映射表契约: 键集 = crash_zoom 族白名单精确清单 (宁缺毋滥 —— 日常
     运镜不入表), 值域 = registry 在册 trigger, 且无一字超出 564 镜实况
     词表;
  2. ``resolve_camera_move_trigger``: 命中 / 未命中 None / camera_movement
     旧拼写兼容 / camera_move 优先 / 空 shot / 非法值 (纯函数无 raise
     路径, 一律 None 降级);
  3. ``_build_multipart`` 集成: 意图命中 → camera_move 字段透传 (追加位 =
     lora 装配区之后、blockCache 之前); 未命中 → 字段序列与改动前逐字节
     等价 (红线, 同 test_video_engine_lora T1 口径); 显式 h3_lora 在场 →
     即使 camera_move 命中也不发该字段 (显式 > 自动)。

桩法参照 test_video_engine_lora.py: 裸实例直调 _build_multipart, 不触
transport; registry 走 env 针对性 setenv (本路径无读盘, fixture 是防未来
回归的卫生锚)。

运行口径 (自纠偏, 见 docs/auto-attach-kmc-batch2.md §边界披露): 一律仓根
起跑 ``cd <仓根> && python3 -m pytest plugins/kais_aigc/tests/…``。本机
venv 带 hermes-agent editable 安装会遮蔽 ``plugins`` 命名空间, 且从
plugins/kais_aigc 目录起跑时 pytest 以 ``kais_aigc.tests.*`` 包路径导入,
``kais_aigc/__init__`` 的 tools.registry import 被 cwd 的 tools.py 文件
遮蔽 —— 既有套件 (test_qwen_eye / test_canvas_graph 等) 在该目录同报
collection error, 结构性不可修 (修 conftest/__init__ 均越工单白名单)。
仓根自举保证本套件解析到本仓 plugins/kais_aigc 而非 hermes-agent 拷贝。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from plugins.kais_aigc.camera_move_intent import (  # noqa: E402
    CAMERA_MOVE_TRIGGERS,
    resolve_camera_move_trigger,
)
from plugins.kais_aigc.video_engine import H3VideoEngine  # noqa: E402

_LOGGER = "plugins.kais_aigc.video_engine"


# ---------------------------------------------------------------------------
# fixture: registry 真源注入 (env 覆盖 —— 测试不触真机路径)
# ---------------------------------------------------------------------------

@pytest.fixture
def lora_registry_env(tmp_path, monkeypatch) -> Path:
    """卫生锚: _build_multipart 本路径不读 registry (lora 由形参传入),
    setenv 保证即使未来读盘也只触 tmp —— 与 test_video_engine_lora 的
    lora_registry fixture 同款 env 口径 (D-06: 调用时读, 每调用重读)。"""
    path = tmp_path / "h3-lora-registry.json"
    path.write_text(json.dumps({"loras": []}), encoding="utf-8")
    monkeypatch.setenv("H3_KMC_LORA_REGISTRY_PATH", str(path))
    return path


def _build(
    shot: dict,
    episode_config: dict | None = None,
    lora: tuple | None = None,
) -> list:
    """裸实例直调 _build_multipart (不触碰 transport), 返回 multipart 段表。"""
    return H3VideoEngine()._build_multipart(
        shot,
        prompt=None,
        episode_config=episode_config,
        turnaround_paths=[],
        scene_ref_path=None,
        voice_clip_path=None,
        first_frame=None,
        lora=lora,
    )


def _fields(files: list) -> dict:
    return {name: part[1] for name, part in files if part[0] is None}


def _names(files: list) -> list:
    return [name for name, _part in files]


# 唯一可挂臂形态: preview-lock (motion 缺省 medium)。与
# test_video_engine_lora.PREVIEW_SHOT 同款 —— 保证两套件字段序列基线一致。
PREVIEW_SHOT = {
    "shot_id": "S01",
    "ltx_prompt": "x",
    "duration_sec": 5.0,
    "h3_useCase": "preview-lock",
}

# 改动前 (b4d589e5) 的字段名序列基线 —— 「逐字节等价」红线的锚。
LEGACY_NAMES = [
    "projectId", "prompt", "mode", "width", "height",
    "length", "filenamePrefix", "useCase", "motion",
]

# 564 镜实况词表 (operator 侦查 2026-09-28, 中文枚举 23 项全量):
# 固定140 缓慢推进99 手持62 跟随47 缓慢拉远36 变焦推31 上仰25 升降下22
# 升降上21 下俯20 快速推进18 平稳跟随9 斯坦尼康8 右摇6 左摇6 变焦拉3
# 环绕3 变焦拉远3 推移2 甩镜2 快速拉远1 下降1 上升1
VOCABULARY_564 = {
    "固定", "缓慢推进", "手持", "跟随", "缓慢拉远", "变焦推", "上仰",
    "升降下", "升降上", "下俯", "快速推进", "平稳跟随", "斯坦尼康", "右摇",
    "左摇", "变焦拉", "环绕", "变焦拉远", "推移", "甩镜", "快速拉远",
    "下降", "上升",
}


# ---------------------------------------------------------------------------
# 1. 映射表契约 (宁缺毋滥 —— 白名单精确清单)
# ---------------------------------------------------------------------------


class TestMappingTableContract:
    def test_keys_are_exact_whitelist(self):
        # 工单 C1 白名单: 变焦推/快速推进/快速拉远/甩镜 —— 一项不多一项不少。
        assert set(CAMERA_MOVE_TRIGGERS) == {
            "变焦推", "快速推进", "快速拉远", "甩镜",
        }

    def test_values_all_crash_zoom(self):
        # registry 当前唯一 auto_attach trigger 是 crash_zoom; 新 trigger
        # 上线时按「确定语义」标准扩表并同步本断言。
        assert set(CAMERA_MOVE_TRIGGERS.values()) == {"crash_zoom"}

    def test_keys_subset_of_564_vocabulary(self):
        # 拼写防呆: 键无一字超出 564 镜实况词表 (写错枚举即测试失败)。
        assert set(CAMERA_MOVE_TRIGGERS) <= VOCABULARY_564

    def test_daily_moves_excluded(self):
        # 决策律: 日常运镜 prompt 本来就能执行, 挂 LoRA 违反「宁缺毋滥」——
        # 为覆盖率把它们塞进表里正是本批要防的事。
        for daily in [
            "固定", "手持", "跟随", "缓慢推进", "缓慢拉远", "上仰", "下俯",
            "环绕", "斯坦尼康", "平稳跟随", "推移",
        ]:
            assert daily not in CAMERA_MOVE_TRIGGERS


# ---------------------------------------------------------------------------
# 2. resolve_camera_move_trigger — 纯函数解析
# ---------------------------------------------------------------------------


class TestResolveCameraMoveTrigger:
    @pytest.mark.parametrize("move", sorted(CAMERA_MOVE_TRIGGERS))
    def test_whitelist_hits_both_spellings(self, move):
        assert resolve_camera_move_trigger(
            {"camera_move": move}) == "crash_zoom"
        assert resolve_camera_move_trigger(
            {"camera_movement": move}) == "crash_zoom"

    @pytest.mark.parametrize("move", sorted(VOCABULARY_564 - set(CAMERA_MOVE_TRIGGERS)))
    def test_non_whitelist_vocabulary_returns_none(self, move):
        # 词表内非白名单项 (全部日常运镜) 一律 None。
        assert resolve_camera_move_trigger({"camera_move": move}) is None

    @pytest.mark.parametrize("move", ["", "未知运镜", "快速 推进", "crash_zoom"])
    def test_unknown_or_malformed_returns_none(self, move):
        assert resolve_camera_move_trigger({"camera_move": move}) is None

    def test_camera_move_takes_priority_over_legacy(self):
        # P09 L2 口径 camera_move 是真值, camera_movement 旧拼写只兜底。
        shot = {"camera_move": "变焦推", "camera_movement": "固定"}
        assert resolve_camera_move_trigger(shot) == "crash_zoom"

    def test_no_fuzzy_matching(self):
        # 精确匹配红线: 包含/前缀/去空白式匹配会把「缓慢推进」误升级成
        # crash_zoom —— 用「快速推进」的变体证明没有暗搓搓的模糊逻辑。
        for probe in ["快速推进 ", " 快速推进", "快速推进。", "X快速推进X"]:
            assert resolve_camera_move_trigger({"camera_move": probe}) is None

    @pytest.mark.parametrize("bad", [None, 42, 1.5, ["变焦推"], {"k": "v"}])
    def test_non_string_values_return_none(self, bad):
        # 纯函数无 raise 路径: 非 str 值守卫降级 None, 不炸调用方。
        assert resolve_camera_move_trigger({"camera_move": bad}) is None
        assert resolve_camera_move_trigger({"camera_movement": bad}) is None

    def test_empty_or_missing_shot(self):
        assert resolve_camera_move_trigger({}) is None
        assert resolve_camera_move_trigger(None) is None

    def test_shot_not_mutated(self):
        shot = {"camera_move": "变焦推", "camera_movement": "固定"}
        snapshot = json.loads(json.dumps(shot))
        resolve_camera_move_trigger(shot)
        assert shot == snapshot


# ---------------------------------------------------------------------------
# 3. _build_multipart 集成 (追加位 + 显式优先 + 逐字节等价红线)
# ---------------------------------------------------------------------------


class TestCameraMoveMultipartWiring:
    def test_intent_hit_appends_camera_move(self, lora_registry_env, caplog):
        shot = {**PREVIEW_SHOT, "camera_move": "变焦推"}
        with caplog.at_level("INFO", logger=_LOGGER):
            files = _build(shot)
        assert _names(files) == [*LEGACY_NAMES, "camera_move"]
        assert _fields(files)["camera_move"] == "crash_zoom"
        assert ("h3_engine: S01 camera_move=crash_zoom → auto_attach trigger"
                "（装配失败由 KAP 侧降级）") in caplog.text

    def test_miss_keeps_legacy_field_sequence(self, lora_registry_env):
        # 红线: 未命中 (含词表内日常运镜) / 无字段 / 空值 —— 字段名序列与
        # 改动前逐字节等价 (同 test_video_engine_lora T1 口径)。
        for shot in [
            {**PREVIEW_SHOT, "camera_move": "固定"},
            {**PREVIEW_SHOT, "camera_move": "缓慢推进"},
            {**PREVIEW_SHOT, "camera_move": "手持"},
            {**PREVIEW_SHOT, "camera_move": ""},
            {**PREVIEW_SHOT, "camera_move": "未知运镜"},
            dict(PREVIEW_SHOT),
        ]:
            assert _names(_build(shot)) == LEGACY_NAMES

    def test_legacy_spelling_camera_movement_appends_too(self, lora_registry_env):
        files = _build({**PREVIEW_SHOT, "camera_movement": "甩镜"})
        assert _fields(files)["camera_move"] == "crash_zoom"

    def test_explicit_lora_suppresses_camera_move(self, lora_registry_env, caplog):
        # 显式 > 自动: lora 在场 (render() 的 _route_lora 预检产物经形参
        # 传入) 时跳过意图解析 —— 即使 camera_move 命中也不发该字段。
        shot = {**PREVIEW_SHOT, "camera_move": "甩镜"}
        with caplog.at_level("INFO", logger=_LOGGER):
            files = _build(shot, lora=("combat-v2", 0.8, 20, "per-shot"))
        assert _names(files) == [
            *LEGACY_NAMES, "lora", "lora_strength", "lora_steps",
        ]
        assert "camera_move" not in _names(files)
        assert "auto_attach trigger" not in caplog.text

    def test_position_after_lora_zone_before_blockcache(self, lora_registry_env):
        # 追加位: lora 装配区之后、blockCache 之前 (无显式 lora 时直接落
        # useCase/motion 之后 —— 同族字段同一装配区, 仿 blockCache 先例)。
        shot = {**PREVIEW_SHOT, "camera_move": "变焦推", "h3_blockCache": True}
        files = _build(shot, {"h3_blockCacheThreshold": 0.85})
        assert _names(files) == [
            *LEGACY_NAMES, "camera_move", "blockCache", "blockCacheThreshold",
        ]

    def test_no_arm_gating_vdn_profile_still_forwards(self, lora_registry_env):
        # 边界口径: 意图透传不做臂门控 (红线1 —— 引擎侧臂判定只服务于显式
        # lora 预检, 不外溢到 auto 路径)。vdn/rh/final-shot 臂上的装配可行性
        # 归 KAP 侧降级 (工单 §0: 装配任何失败 = prompt-only, 绝不 400)。
        shot = {**PREVIEW_SHOT, "camera_move": "变焦推", "h3_vdn": True}
        files = _build(shot)
        fields = _fields(files)
        assert fields["profile"]  # vdn 臂 profile-only 形态照旧
        assert fields["camera_move"] == "crash_zoom"
