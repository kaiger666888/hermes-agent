"""test_canvas_sync_variant_suffix.py — _add_artifact 去重后缀契约。

Kai 2026-08-16 shot_id 标准化：同一 phase output 里出现重复 artifact id 时，
``_add_artifact`` 原先追加 ``-{len(seen_ids)}`` 连字符后缀（产生
``S1_0012-3`` 这类游离于标准之外的 id）。标准化后冗余变体统一为
``{base_id}_v{n}``（n 从 2 起，v1 隐含不写）。

测试通过 ``_extract_artifacts`` 端到端驱动（_add_artifact 是闭包，无法直接
调用）：用 p11a 的 rapid_preview_clips list output 构造重复 shot_id 的
记录，断言产出的 artifact id 后缀序列。
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
    return sub


def _preview_record(shot_id: str, variant_id: str) -> dict:
    """One rapid_preview_clips record (subset of the 6-field contract)."""
    return {
        "shot_id": shot_id,
        "variant_id": variant_id,
        "clip_path": f"/preview/{variant_id}.mp4",
        "generation_time_ms": 1234,
        "engine": "slideshow",
    }


class TestVariantSuffixDedup:
    def test_duplicate_ids_get_v2_v3_suffixes(self):
        """3 records sharing one shot_id → base, _v2, _v3 (never -2/-3)."""
        sub = _make_subscriber()
        arts = sub._extract_artifacts("p11a_preview_clips", {"outputs": {
            "rapid_preview_clips": [
                _preview_record("S01_B01", "S01_B01"),
                _preview_record("S01_B01", "S01_B01_v2"),
                _preview_record("S01_B01", "S01_B01_v3"),
            ],
        }})
        ids = [a["id"] for a in arts]
        assert ids == [
            "rapid_preview_clips-S01_B01",
            "rapid_preview_clips-S01_B01_v2",
            "rapid_preview_clips-S01_B01_v3",
        ], f"dedup suffixes must be _v{{n}}; got {ids}"
        assert not any(i.split("-")[-1].isdigit() for i in ids if "_" not in i.split("-")[-1]), (
            f"legacy '-N' suffix must not appear; got {ids}"
        )

    def test_suffix_skips_ids_already_occupied(self):
        """When base_v2 already exists as a real id, the duplicate of base
        must skip to _v3 (the while-loop collision scan), not overwrite."""
        sub = _make_subscriber()
        arts = sub._extract_artifacts("p11a_preview_clips", {"outputs": {
            "rapid_preview_clips": [
                _preview_record("S02_B01", "S02_B01"),
                _preview_record("S02_B01", "S02_B01_v2"),   # occupies _v2
                _preview_record("S02_B01", "S02_B01"),      # dup of base → _v3
            ],
        }})
        ids = [a["id"] for a in arts]
        assert ids == [
            "rapid_preview_clips-S02_B01",
            "rapid_preview_clips-S02_B01_v2",
            "rapid_preview_clips-S02_B01_v3",
        ], f"collision scan must skip occupied _v2; got {ids}"
        assert len(set(ids)) == 3, "ids must stay unique"

    def test_unique_ids_untouched(self):
        """No duplicates → no suffix appended at all."""
        sub = _make_subscriber()
        arts = sub._extract_artifacts("p11a_preview_clips", {"outputs": {
            "rapid_preview_clips": [
                _preview_record("S01_B01", "S01_B01"),
                _preview_record("S01_B02", "S01_B02"),
            ],
        }})
        assert [a["id"] for a in arts] == [
            "rapid_preview_clips-S01_B01",
            "rapid_preview_clips-S01_B02",
        ]
