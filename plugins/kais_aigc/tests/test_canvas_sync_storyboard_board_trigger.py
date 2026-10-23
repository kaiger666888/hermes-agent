"""test_canvas_sync_storyboard_board_trigger.py — board 落库触发面退役契约.

The ``_persist_storyboard_board`` o_assets bridge (originally gated on
``_phase_prefix(phase_id) == "p10b"``, later widened to ``p09c``/``p11a`` via
the 2026-08-16 P0-3 dead-trigger fix) was REMOVED 2026-09-28 分镜板退役批 —
the sole consumer (StoryboardBoard view + GET /api/v1/storyboard route) is
deleted by KAP 批A.

These tests pin the POST-RETIREMENT trigger surface through the real
``on_phase_complete`` path (MockTransport + temp sqlite — no production
DB / network dependency):

  - ``p11a_preview_clips`` result shaped like the old board carrier →
    NO o_assets storyboard_board row.
  - ``p09c_storyboard_board`` result (white-model chain, engine 缺省 off) →
    NO row either — the p09c prefix no longer triggers a persist.
  - Unrelated phases (e.g. p09b) → still no row, trivially.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import httpx

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from plugins.kais_aigc.canvas import CanvasClient  # noqa: E402
from plugins.kais_aigc.canvas_sync import CanvasSyncSubscriber  # noqa: E402


def _make_client() -> CanvasClient:
    """CanvasClient with mocked load/save endpoints."""

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith(("/load-v2", "/save-v2")):
            return httpx.Response(
                200, json={"code": 0, "msg": "ok", "data": {"ok": True}},
            )
        return httpx.Response(200, json={"code": 0, "msg": "ok", "data": {}})

    return CanvasClient(
        base_url="http://test-canvas:10588",
        project_id=101,
        episodes_id=202,
        transport=httpx.MockTransport(handler),
    )


def _make_temp_db(tmp_path: Path) -> str:
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


def _board(shots=2, scenes=1):
    """Legacy p11a board shape (pre-retirement) — must trigger nothing."""
    return {
        "type": "storyboard_board",
        "episode_id": "202",
        "generated_at": "2026-08-16T00:00:00+00:00",
        "scenes": [
            {
                "scene_id": f"S0{i+1}",
                "scene_title": f"S0{i+1}",
                "shots": [
                    {"shot_id": f"S0{i+1}_B0{j+1}"} for j in range(shots)
                ],
            }
            for i in range(scenes)
        ],
        "stats": {
            "total_shots": shots * scenes,
            "total_duration_sec": float(shots * scenes * 3.5),
            "total_scenes": scenes,
        },
    }


def _p11a_result(board) -> dict:
    return {
        "phase": "p11a_preview_clips",
        "outputs": {
            "variants_generated": 1,
            "variants_degraded": 0,
            "rapid_preview_clips": [],
            "storyboard_board": board,
        },
        "gate": None,
    }


def _board_rows(db_path: str) -> list:
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT projectId, episodesId, meta FROM o_assets "
        "WHERE type='storyboard_board'"
    ).fetchall()
    conn.close()
    return rows


class TestStoryboardBoardTriggerRetired:
    def test_p11a_result_no_longer_persists_board(
        self, tmp_path, monkeypatch,
    ):
        """2026-09-28 退役批: even a legacy board payload on the p11a path
        must NOT reach o_assets (bridge removed with the assembly chain)."""
        db_path = _make_temp_db(tmp_path)
        monkeypatch.setattr(
            "plugins.kais_aigc.canvas_sync._locate_canvas_db", lambda: db_path
        )
        client = _make_client()
        sub = CanvasSyncSubscriber(client)

        sub.on_phase_complete("ep-1", "p11a_preview_clips", _p11a_result(_board()))
        client.close()

        assert _board_rows(db_path) == [], (
            "storyboard_board o_assets row written — 落库链已退役 "
            "(2026-09-28 分镜板退役批), 触发面不得复活"
        )

    def test_p09c_result_no_longer_persists_board(
        self, tmp_path, monkeypatch,
    ):
        """The p09c prefix used to sit on the persist trigger path (no-op
        without a board payload); the whole trigger is gone now — the
        white-model chain's board must not be persisted either."""
        db_path = _make_temp_db(tmp_path)
        monkeypatch.setattr(
            "plugins.kais_aigc.canvas_sync._locate_canvas_db", lambda: db_path
        )
        client = _make_client()
        sub = CanvasSyncSubscriber(client)

        sub.on_phase_complete(
            "ep-1",
            "p09c_storyboard_board",
            {"phase": "p09c_storyboard_board",
             "outputs": {"storyboard_board": _board(),
                         "storyboard-qc": {"advisory": True}},
             "gate": None},
        )
        client.close()

        assert _board_rows(db_path) == []

    def test_unrelated_phase_never_persists(self, tmp_path, monkeypatch):
        """Even a board-shaped payload on an unrelated phase must NOT write."""
        db_path = _make_temp_db(tmp_path)
        monkeypatch.setattr(
            "plugins.kais_aigc.canvas_sync._locate_canvas_db", lambda: db_path
        )
        client = _make_client()
        sub = CanvasSyncSubscriber(client)

        sub.on_phase_complete("ep-1", "p09b_shot_audit", _p11a_result(_board()))
        client.close()

        assert _board_rows(db_path) == []
