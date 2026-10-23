"""test_canvas_sync_voice_join.py — P04 voice-asset sync SQL contract.

ep-demo-pixar B.3 (matrix #5): the voice-asset sync block queried
``filePath`` directly from ``o_assets`` — a column that only exists on
``o_image`` — so EVERY P04 sync raised ``no such column: filePath`` and
the exception was swallowed into a warning (voice assets never reached the
canvas).

These tests pin the corrected JOIN contract against a TEMP sqlite DB with
the REAL ``o_assets`` + ``o_image`` column layout (read-only for the sync —
the block SELECTs, never writes):

  - Voice rows join ``o_image.filePath`` via ``o_assets.imageId``.
  - ``filePath`` NULL (no linked image) falls back to
    ``meta.ref_audio_path``.
  - The old broken query shape (filePath selected from o_assets alone)
    fails against this schema — guarded by an explicit regression test.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from plugins.kais_aigc import canvas_sync  # noqa: E402


class _ClientStub:
    """Minimal canvas client stub exposing the project/episode ids."""

    def __init__(self, project_id, episodes_id):
        self._project_id = project_id
        self._episodes_id = episodes_id


def _make_subscriber(project_id=101, episodes_id=202):
    sub = canvas_sync.CanvasSyncSubscriber.__new__(canvas_sync.CanvasSyncSubscriber)
    sub._client = _ClientStub(project_id, episodes_id)
    return sub


# Real db2.sqlite column layout (subset sufficient for the voice-sync JOIN;
# verified against the production schema 2026-08-15).
_O_ASSETS_DDL = """
CREATE TABLE o_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, prompt TEXT, remark TEXT, type TEXT, describe TEXT,
    scriptId INTEGER, imageId INTEGER, assetsId INTEGER,
    projectId INTEGER, flowId INTEGER,
    characterId TEXT, isPrimaryView INTEGER, state TEXT,
    meta TEXT, createdAt INTEGER, createdBy TEXT, episodesId INTEGER
)
"""

_O_IMAGE_DDL = """
CREATE TABLE o_image (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filePath TEXT, type TEXT, assetsId INTEGER, model TEXT,
    resolution TEXT, state TEXT, errorReason TEXT
)
"""


def _make_temp_db(tmp_path: Path) -> str:
    db_path = str(tmp_path / "db2.sqlite")
    conn = sqlite3.connect(db_path)
    conn.execute(_O_ASSETS_DDL)
    conn.execute(_O_IMAGE_DDL)
    conn.commit()
    conn.close()
    return db_path


def _seed_voice_rows(db_path: str) -> None:
    """Two voice assets: one with a linked o_image, one without (NULL)."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO o_image (filePath) VALUES (?)",
        ("amao/amao_image.png",),
    )
    conn.execute(
        "INSERT INTO o_assets (name, type, projectId, episodesId, "
        "characterId, imageId, isPrimaryView, state, meta) "
        "VALUES (?, 'voice', 101, 202, ?, ?, 1, 'active', ?)",
        ("阿毛 声纹参考", "阿毛", 1,
         json.dumps({"voice_id": "v-1", "instruct": "约5岁男童"})),
    )
    conn.execute(
        "INSERT INTO o_assets (name, type, projectId, episodesId, "
        "characterId, imageId, isPrimaryView, state, meta) "
        "VALUES (?, 'voice', 101, 202, ?, NULL, 0, 'active', ?)",
        ("花青 声纹参考", "花青",
         json.dumps({"ref_audio_path": "/refs/huaqing.flac"})),
    )
    # A non-voice asset in the same project/episode — must be excluded.
    conn.execute(
        "INSERT INTO o_assets (name, type, projectId, episodesId, "
        "characterId, imageId, isPrimaryView, state, meta) "
        "VALUES (?, 'image', 101, 202, NULL, NULL, 0, 'active', NULL)",
        ("unrelated image",),
    )
    # A voice asset from ANOTHER episode — must be excluded.
    conn.execute(
        "INSERT INTO o_assets (name, type, projectId, episodesId, "
        "characterId, imageId, isPrimaryView, state, meta) "
        "VALUES (?, 'voice', 101, 999, ?, NULL, 0, 'active', NULL)",
        ("别集 声纹", "别人"),
    )
    conn.commit()
    conn.close()


class TestVoiceSyncJoin:
    def test_voice_rows_join_o_image_filepath(self, tmp_path, monkeypatch):
        db_path = _make_temp_db(tmp_path)
        _seed_voice_rows(db_path)
        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT a.name, i.filePath FROM o_assets a "
            "LEFT JOIN o_image i ON a.imageId = i.id "
            "WHERE a.projectId = ? AND a.type = 'voice' AND a.episodesId = ?",
            (101, 202),
        ).fetchall()
        conn.close()
        by_name = dict(rows)
        assert by_name["阿毛 声纹参考"] == "amao/amao_image.png"
        # No linked image → NULL filePath (meta fallback applies in sync).
        assert by_name["花青 声纹参考"] is None
        # Episode scoping: only this episode's voice rows returned.
        assert len(rows) == 2

    def test_old_query_shape_fails_against_real_schema(self, tmp_path):
        """Regression guard: selecting filePath from o_assets alone raises
        ``no such column`` — the exact ep-demo-pixar production failure."""
        db_path = _make_temp_db(tmp_path)
        conn = sqlite3.connect(db_path)
        with pytest.raises(sqlite3.OperationalError, match="no such column"):
            conn.execute(
                "SELECT filePath FROM o_assets WHERE type = 'voice'"
            ).fetchall()
        conn.close()

    def test_extract_artifacts_p04_syncs_voice_assets(self, tmp_path, monkeypatch):
        """The real integration path: _extract_artifacts('p04_*') runs the
        voice-asset sync block against the temp DB and emits audio artifacts
        (JOIN filePath for the linked row, meta fallback for the NULL row)."""
        db_path = _make_temp_db(tmp_path)
        _seed_voice_rows(db_path)
        monkeypatch.setattr(canvas_sync, "_locate_canvas_db", lambda: db_path)
        sub = _make_subscriber()
        arts = sub._extract_artifacts("p04_character_design", {"outputs": {}})
        voice_arts = [a for a in arts if a.get("assetType") == "voice"]
        by_char = {a.get("characterId"): a for a in voice_arts}
        assert set(by_char) == {"阿毛", "花青"}  # other episode/type excluded
        assert by_char["阿毛"]["filePath"] == "amao/amao_image.png"
        # NULL o_image.filePath → meta.ref_audio_path fallback.
        assert by_char["花青"]["filePath"] == "/refs/huaqing.flac"
        assert by_char["阿毛"]["instruct"] == "约5岁男童"

    def test_extract_artifacts_p06_missing_db_is_noop(self, monkeypatch):
        # Degraded environment (no db) must not raise out of _extract_artifacts.
        monkeypatch.setattr(canvas_sync, "_locate_canvas_db", lambda: None)
        sub = _make_subscriber()
        arts = sub._extract_artifacts("p06_blackboard", {"outputs": {}})
        assert isinstance(arts, list)
