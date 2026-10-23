"""test_canvas_sync_gate_b_zero_duration.py — Gate B falsy 降级回归。

Background (ep-ccport-test01, 2026-08-19 审计):
    H3 引擎渲染不回报时长 → p11b video_clips 的 ``duration_sec: 0``。
    Gate B 降级守卫用 falsy 判断 ``not data.get(f)``，0 被误判为缺失，
    一跑 37 个媒体节点全量降级 script（video 9 / storyboard 26 /
    audio 2）——生产视频/成片在画布上以文本卡示人（无封面、不能播、
    不进视频泳道），前端 0 处消费 ``_original_type``。

修复契约:
    * duration_sec=0（int/float）= 合法值，媒体节点**不再**降级；
    * 真缺失（键不存在 / None / 空串）仍然降级 script 并写
      ``_original_type``（防御 save-v2 400 的原语义保留）。

配套: kais-aigc-platform canvasAssetSchema.ts 的 duration_sec
`.positive()` → `.min(0)`（否则 save-v2 会拒收 0，降级守卫只是
挡了另一头的 400）。
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from plugins.kais_aigc import canvas_sync  # noqa: E402


class _ClientStub:
    def __init__(self, project_id=101, episodes_id=202):
        self._project_id = project_id
        self._episodes_id = episodes_id


def _make_subscriber():
    sub = canvas_sync.CanvasSyncSubscriber.__new__(
        canvas_sync.CanvasSyncSubscriber
    )
    sub._client = _ClientStub()
    sub._child_counters = {}
    return sub


def _build_video_node(sub, clip_overrides: dict) -> dict:
    """Drive a p11b video_clips artifact through _build_artifact_node."""
    clip = {
        "id": "S01_B01",
        "label": "S01_B01",
        "type": "video",
        "filePath": "/oss/pipeline/611772d2/S01_B01.mp4",
        "shot_id": "S01_B01",
        "engine": "h3",
        "duration_sec": 0,
        "resolution": "768x1344",
        "description": "P11 视频片段 · S01_B01 · h3 视频生成",
        "_origin_key": "video_clips",
        "selected": True,
    }
    clip.update(clip_overrides)
    return sub._build_artifact_node("p11b_final_render", clip)


class TestZeroDurationNotDegraded:
    def test_int_zero_keeps_video_type(self):
        sub = _make_subscriber()
        node = _build_video_node(sub, {"duration_sec": 0})
        assert node["type"] == "video", (
            "duration_sec=0（引擎未回报时长）是合法值，video 节点不得降级 "
            "script（ep-ccport-test01 一跑 9 个视频节点全变文本卡）"
        )
        assert node["data"].get("_original_type") is None

    def test_float_zero_keeps_video_type(self):
        sub = _make_subscriber()
        node = _build_video_node(sub, {"duration_sec": 0.0})
        assert node["type"] == "video"

    def test_storyboard_zero_duration_keeps_type(self):
        sub = _make_subscriber()
        art = {
            "id": "S01_B01",
            "label": "分镜 S01_B01",
            "type": "storyboard",
            "shot_id": "S01_B01",
            "shot_type": "MS",
            "duration_sec": 0,
            "description": "分镜 S01_B01",
            "_origin_key": "shot_list",
            "selected": True,
        }
        node = sub._build_artifact_node("p09_shot_breakdown", art)
        assert node["type"] == "storyboard"


class TestGenuinelyMissingStillDegrades:
    def test_missing_engine_degrades_with_original_type(self):
        sub = _make_subscriber()
        node = _build_video_node(sub, {"engine": None})
        assert node["type"] == "script"
        assert node["data"].get("_original_type") == "video"

    def test_empty_string_shot_id_degrades(self):
        sub = _make_subscriber()
        node = _build_video_node(sub, {"shot_id": ""})
        assert node["type"] == "script"
        assert node["data"].get("_original_type") == "video"

    def test_absent_duration_degrades(self):
        clip = {
            "id": "S02_B01", "label": "S02_B01", "type": "video",
            "filePath": "/oss/x/S02_B01.mp4", "shot_id": "S02_B01",
            "engine": "h3", "resolution": "768x1344",
            "description": "d", "_origin_key": "video_clips", "selected": True,
        }
        sub = _make_subscriber()
        node = sub._build_artifact_node("p11b_final_render", clip)
        assert node["type"] == "script"
        assert node["data"].get("_original_type") == "video"
