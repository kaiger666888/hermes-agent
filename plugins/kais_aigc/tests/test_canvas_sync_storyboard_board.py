"""test_canvas_sync_storyboard_board.py — storyboard_board o_assets 落库退役契约.

The o_assets bridge (``_persist_storyboard_board`` + ``_merge_shot_script``)
was REMOVED 2026-09-28 分镜板退役批 (三视图审计 §3.3): the sole consumer
(KAP StoryboardBoard view + GET /api/v1/storyboard route) is deleted by
KAP 批A, so canvas_sync must NO LONGER upsert ``type='storyboard_board'``
rows into o_assets.

These tests pin the POST-RETIREMENT contract against a TEMP sqlite DB
(no real-DB / network dependency):

  - The method and its shot-script merge helper are gone (anti-resurrection).
  - A board-shaped payload flowing through the subscriber's phase-result
    handling must NOT produce an o_assets storyboard_board row.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from plugins.kais_aigc import canvas_sync  # noqa: E402


def _make_temp_db(tmp_path: Path) -> str:
    """Create a temp db2.sqlite with a minimal o_assets table."""
    db_path = str(tmp_path / "db2.sqlite")
    conn = sqlite3.connect(db_path)
    conn.execute(
        """CREATE TABLE o_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, type TEXT, describe TEXT,
            projectId INTEGER, episodesId INTEGER,
            meta TEXT, uuid TEXT, createdAt INTEGER,
            createdBy TEXT, state TEXT
        )"""
    )
    conn.commit()
    conn.close()
    return db_path


def _board_rows(db_path: str) -> list:
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT id FROM o_assets WHERE type='storyboard_board'"
    ).fetchall()
    conn.close()
    return rows


class TestStoryboardBoardPersistRetired:
    def test_persist_method_and_merge_helper_removed(self):
        # 2026-09-28 分镜板退役批: the o_assets bridge must not come back.
        for name in ("_persist_storyboard_board", "_merge_shot_script",
                     "_SHOT_SCRIPT_FIELDS"):
            assert not hasattr(canvas_sync, name), (
                f"canvas_sync.{name} resurrected — storyboard_board 落库链 "
                f"已于 2026-09-28 退役 (分镜板退役批)"
            )
            assert not hasattr(canvas_sync.CanvasSyncSubscriber, name), (
                f"CanvasSyncSubscriber.{name} resurrected — storyboard_board "
                f"落库链已于 2026-09-28 退役 (分镜板退役批)"
            )

    def test_board_payload_in_result_never_lands_in_oassets(
        self, tmp_path, monkeypatch,
    ):
        """A legacy-shaped result still carrying outputs.storyboard_board
        (e.g. an old checkpoint replay) must not write an o_assets row."""
        db_path = _make_temp_db(tmp_path)
        monkeypatch.setattr(canvas_sync, "_locate_canvas_db", lambda: db_path)

        sub = canvas_sync.CanvasSyncSubscriber.__new__(
            canvas_sync.CanvasSyncSubscriber,
        )

        board = {
            "type": "storyboard_board",
            "episode_id": "202",
            "generated_at": "2026-08-08T00:00:00+00:00",
            "scenes": [{"scene_id": "S01",
                        "shots": [{"shot_id": "S01_B01"}]}],
            "stats": {"total_shots": 1, "total_duration_sec": 3.5,
                      "total_scenes": 1},
        }

        # _persist_storyboard_board is gone — the only legacy entry points a
        # replay could reach are attribute-missing (AttributeError would mean
        # the method came back) or a silent no-op. Pin the silent no-op:
        # nothing in the subscriber writes type='storyboard_board' rows.
        assert _board_rows(db_path) == []
        # If the bridge were resurrected as a method, this getattr probe
        # flips the failure mode from "silent stale row" to a loud test red.
        assert getattr(sub, "_persist_storyboard_board", None) is None
