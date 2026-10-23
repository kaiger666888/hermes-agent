"""test_canvas_sync_audio_stems.py — p12b audio_stems 四轨展开回归。

Background (2026-08-19 画布资产审计):
    p12b 的 ``audio_stems`` 是 dict ``{bgm, sfx, voice, mix}``，此前走
    「dict 不展开」分支只落 1 个容器节点（还常因无 filePath 被 media
    guard 降级 script）—— BGM/环境音效/人声合轨/混音母带从不成为独立
    audio 节点：bgm/foley/mix 泳道、时间线音轨列、资产库树入口全部
    空转，而 ``bgm.wav``/``master.mp4`` 明明在盘上。

修复契约:
    * audio_stems dict → bgm/voice/mix 各 1 个 + sfx 逐条 audio 子节点，
      ``audioType`` 精确落 bgm/foley/voice/mix（前端 migrate 按此拆
      stage → 泳道）；
    * Gate B 必填齐备（shot_id/engine/duration_sec），filePath 经
      _normalize_media_fields 归一；
    * 汇总容器节点仍产出（通用 dict 分支），嵌套 bgm/sfx/voice/mix
      数据保留给详情面板。
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


def _stems_payload() -> dict:
    return {
        "bgm": {"path": "/ep/assets/P12/bgm.wav", "mood": "温情", "bpm": 92},
        "sfx": [
            {"shot_id": "S01_B01", "effect": "咖啡机蒸汽", "path": "/ep/assets/P12/sfx_S01_B01.wav"},
            {"shot_id": "S03_B01", "effect": "杯子落桌", "path": "/ep/assets/P12/sfx_S03_B01.wav"},
        ],
        "voice": {"path": "/ep/assets/P12/voice_track.wav", "mix_level": 0.9},
        "mix": {"master_path": "/ep/assets/P12/master.mp4", "lufs": -14.2, "dynamic_range": 8.1},
    }


def _extract(sub) -> list[dict]:
    return sub._extract_artifacts(
        "p12b_audio_composition",
        {"outputs": {"audio_stems": _stems_payload()}},
    )


class TestStemExpansion:
    def test_four_stem_kinds_expand_to_audio_nodes(self):
        sub = _make_subscriber()
        arts = _extract(sub)
        by_id = {a["id"]: a for a in arts}

        bgm = by_id.get("audio_stems-bgm")
        assert bgm is not None, "BGM 音轨必须有独立 audio 节点（bgm.wav 在盘上）"
        assert bgm["type"] == "audio"
        assert bgm["audioType"] == "bgm"
        assert bgm["filePath"]
        assert bgm["engine"] and bgm["shot_id"]

        sfx1 = by_id.get("audio_stems-sfx-S01_B01")
        assert sfx1 is not None, "sfx 逐条展开"
        assert sfx1["audioType"] == "foley"

        voice = by_id.get("audio_stems-voice")
        assert voice is not None
        assert voice["audioType"] == "voice"

        mix = by_id.get("audio_stems-mix")
        assert mix is not None, "混音母带必须有独立节点（master.mp4 的音轨身份）"
        assert mix["audioType"] == "mix"

    def test_summary_container_node_still_emitted(self):
        sub = _make_subscriber()
        arts = _extract(sub)
        # _add_artifact 生成的 id 带 a- 前缀化发生在 _build 阶段之前？
        # _extract_artifacts 的 id 是裸 id；容器节点 id = out_key。
        assert any(a["id"] == "audio_stems" for a in arts), (
            "汇总容器节点仍应产出（嵌套 bgm/sfx/voice/mix 数据供详情面板）"
        )

    def test_gate_b_fields_complete_so_audio_type_survives(self):
        """展开的 stem 节点过 _build_artifact_node 后仍是 audio（不降级）。"""
        sub = _make_subscriber()
        arts = _extract(sub)
        bgm = next(a for a in arts if a["id"] == "audio_stems-bgm")
        node = sub._build_artifact_node("p12b_audio_composition", bgm)
        assert node["type"] == "audio", (
            "stem 节点 Gate B 必填齐备（shot_id/engine/duration_sec=0），"
            "不得降级 script"
        )
        assert node["data"]["audioType"] == "bgm"

    def test_empty_stems_do_not_crash(self):
        sub = _make_subscriber()
        arts = sub._extract_artifacts(
            "p12b_audio_composition",
            {"outputs": {"audio_stems": {"sfx": [], "bgm": None}}},
        )
        ids = {a["id"] for a in arts}
        assert "audio_stems-bgm" not in ids
        assert not any(i.startswith("audio_stems-sfx-") for i in ids)

    def test_legacy_p12_phase_prefix_also_expands(self):
        """旧 p12_composition（未 split 前）同 key 也展开。"""
        sub = _make_subscriber()
        arts = sub._extract_artifacts(
            "p12_composition",
            {"outputs": {"audio_stems": _stems_payload()}},
        )
        assert any(a["id"] == "audio_stems-bgm" for a in arts)
