"""test_canvas_sync_subtype.py — F-1: o_assets.meta subtype 生产者（2026-08-16）.

审计 F-1（/home/kai/shared/2026-08-16/kmc-canvas-sync-auto-effect-review.md）：
前端 assetManager 的 getGroupKey / inferSubtype 都先读 ``meta.subtype``
（parseMetaSubtype 短路在所有按 type 分支之前），但 KMC 自动链路
（``_sync_asset_to_oassets_oimage``）此前从不写它——canvas-sync 写的
99 行 subtype 全空，角色资产塌缩进 concept 大组、声纹/turnaround 无法
分层互斥。

修复：写 meta 时经 ``_infer_asset_subtype`` 从 artifact / node data 推导
subtype，值空间对齐前端 AssetSubtype 联合类型与 KAP 手工脚本
（register_turnaround_b2.py 的 "turnaround_sheet"）。

本文件验证：
  1. 纯推导函数的分支覆盖（显式标记 / turnaround_sheet / viewAngle /
     costume / voice / scene / keyframe first-last / 未知返回 None）；
  2. 端到端：三层同步写入后 o_assets.meta 确实带 subtype；
  3. 已有 subtype 的历史 meta 不被覆盖（COALESCE 语义）。
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from plugins.kais_aigc import canvas_sync  # noqa: E402


# ═══════════════════════════════════════════════════════════════════
# Part 1 — pure derivation function
# ═══════════════════════════════════════════════════════════════════

class TestInferAssetSubtype:
    _infer = canvas_sync.CanvasSyncSubscriber._infer_asset_subtype

    def test_explicit_subtype_passthrough(self):
        """data 已带显式 subtype → 原样透传（下游标记优先）。"""
        assert self._infer(
            {"subtype": "midframe"}, {}, "keyframe",
        ) == "midframe"
        assert self._infer(
            {}, {"frame_type": "first"}, "keyframe",
        ) == "first"

    def test_turnaround_sheet_field(self):
        """P04 l1_anchors 带 turnaround_sheet 路径字段 → turnaround_sheet。"""
        assert self._infer(
            {"turnaround_sheet": "assets/turnaround_sheets/base_turnaround_amao.png"},
            {}, "character",
        ) == "turnaround_sheet"

    def test_view_angle_split_views(self):
        """crops 拆分视角（front/side/back/three_quarter）→ turnaround_view。"""
        for va in ("front", "side", "back", "three_quarter"):
            assert self._infer(
                {"viewAngle": va}, {}, "character",
            ) == "turnaround_view", va
        # 非拆分视角（场景扩展角度 est/mast）不归 turnaround_view。
        assert self._infer({"viewAngle": "est"}, {}, "character") is None

    def test_costume_paths(self):
        """costume_turnaround / l2 合身图路径 → costume 类 subtype。"""
        assert self._infer(
            {"filePath": "/oss/p/d1558d83/costume_turnaround_amao.png"},
            {}, "character",
        ) == "costume_turnaround"
        assert self._infer(
            {"filePath": "/oss/p/9c4e6620/l2_amao_S1.png"}, {}, "character",
        ) == "costume_temporal_variant"
        assert self._infer(
            {}, {"costume_set": "ceremony_gold"}, "character",
        ) == "costume_turnaround"

    def test_voice_print(self):
        assert self._infer({}, {}, "voice") == "voice_print"

    def test_scene_base(self):
        for t in ("scene", "scene_image", "scene_variant"):
            assert self._infer({}, {}, t) == "scene_base", t

    def test_keyframe_first_last(self):
        assert self._infer(
            {"label": "S01_B01_first"}, {}, "keyframe",
        ) == "keyframe_first"
        assert self._infer(
            {"label": "S01_B01_last"}, {}, "keyframe",
        ) == "keyframe_last"
        # 推断不出 → None（前端按 name 兜底）。
        assert self._infer(
            {"label": "mid extras"}, {}, "keyframe",
        ) is None

    def test_character_concept_left_to_frontend(self):
        """character 概念图不越权标注——前端启发式链自己判 concept/bible。"""
        assert self._infer(
            {"filePath": "/oss/p/x/amao.webp"}, {}, "character",
        ) is None


# ═══════════════════════════════════════════════════════════════════
# Part 2 — end-to-end: three-layer sync writes meta.subtype
# ═══════════════════════════════════════════════════════════════════

class _ClientStub:
    def __init__(self, project_id=101, episodes_id=202):
        self._project_id = project_id
        self._episodes_id = episodes_id


def _make_temp_db(tmp_path: Path) -> str:
    """Create a temp db2.sqlite with the o_image + o_assets tables."""
    db_path = str(tmp_path / "db2.sqlite")
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE o_image (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filePath TEXT, type TEXT, state TEXT, assetsId INTEGER
        );
        CREATE TABLE o_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, prompt TEXT, type TEXT, imageId INTEGER,
            projectId INTEGER, characterId TEXT, viewAngle TEXT,
            isPrimaryView INTEGER, tags TEXT, state TEXT, meta TEXT,
            uuid TEXT, createdAt INTEGER, createdBy TEXT, episodesId INTEGER
        );
        """
    )
    conn.commit()
    conn.close()
    return db_path


def _make_subscriber(project_id=101, episodes_id=202):
    sub = canvas_sync.CanvasSyncSubscriber.__new__(
        canvas_sync.CanvasSyncSubscriber,
    )
    sub._client = _ClientStub(project_id, episodes_id)
    return sub


class TestSubtypeWrittenToMeta:
    def test_turnaround_row_carries_subtype(self, tmp_path, monkeypatch):
        db_path = _make_temp_db(tmp_path)
        monkeypatch.setattr(canvas_sync, "_locate_canvas_db", lambda: db_path)
        sub = _make_subscriber()

        # P04 l1_anchor artifact（demo-pixar 实测形态）。
        out = sub._sync_asset_to_oassets_oimage(
            {
                "id": "character_assets-l1_anchors-0",
                "label": "amao",
                "assetType": "character",
                "characterId": "amao",
                "filePath": "/oss/pipeline/9c4e6620/base_turnaround_amao.png",
                "turnaround_sheet": "assets/turnaround_sheets/base_turnaround_amao.png",
            },
            None,
        )
        assert out is not None and out.get("o_assets_id")

        conn = sqlite3.connect(db_path)
        meta_raw = conn.execute(
            "SELECT meta FROM o_assets WHERE id=?", (out["o_assets_id"],),
        ).fetchone()[0]
        conn.close()
        meta = json.loads(meta_raw)
        assert meta.get("subtype") == "turnaround_sheet", (
            f"F-1: expected meta.subtype='turnaround_sheet', got {meta!r} — "
            f"asset-manager grouping stays collapsed into concept bucket"
        )

    def test_existing_subtype_not_overwritten(self, tmp_path, monkeypatch):
        """历史 meta 已带 subtype（如手工脚本写的行）→ 不覆盖。"""
        db_path = _make_temp_db(tmp_path)
        monkeypatch.setattr(canvas_sync, "_locate_canvas_db", lambda: db_path)
        sub = _make_subscriber()

        # Pre-seed an o_image + o_assets row whose meta already has a
        # subtype written by the KAP manual script path.
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO o_image (filePath, type, state) VALUES (?,?,?)",
            ("/oss/p/x/legacy.webp", "character", "success"),
        )
        img_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        legacy_meta = json.dumps(
            {"subtype": "costume_turnaround", "batch": "b2"},
        )
        conn.execute(
            "INSERT INTO o_assets (name, type, imageId, projectId, meta,"
            " uuid, createdAt, createdBy) VALUES (?,?,?,?,?,?,?,?)",
            ("legacy 行", "character", img_id, 101, legacy_meta,
             "ast-legacy", 1, "register_turnaround_b2.py"),
        )
        conn.commit()
        conn.close()

        # Same filePath + name → reuses the legacy row (idempotent match).
        sub._sync_asset_to_oassets_oimage(
            {
                "id": "some-artifact",
                "label": "legacy 行",
                "assetType": "character",
                "filePath": "/oss/p/x/legacy.webp",
            },
            None,
        )

        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT meta FROM o_assets WHERE name='legacy 行'"
        ).fetchall()
        conn.close()
        assert len(rows) == 1
        meta = json.loads(rows[0][0])
        assert meta.get("subtype") == "costume_turnaround", (
            "existing historical meta.subtype must NOT be overwritten"
        )
        assert meta.get("batch") == "b2"

    def test_scene_row_carries_scene_base(self, tmp_path, monkeypatch):
        db_path = _make_temp_db(tmp_path)
        monkeypatch.setattr(canvas_sync, "_locate_canvas_db", lambda: db_path)
        sub = _make_subscriber()

        out = sub._sync_asset_to_oassets_oimage(
            {
                "id": "scene_images-0",
                "label": "场景图 1",
                "assetType": "scene",
                "filePath": "/oss/pipeline/abc/S01_front.png",
            },
            None,
        )
        conn = sqlite3.connect(db_path)
        meta_raw = conn.execute(
            "SELECT meta FROM o_assets WHERE id=?", (out["o_assets_id"],),
        ).fetchone()[0]
        conn.close()
        assert json.loads(meta_raw).get("subtype") == "scene_base"
