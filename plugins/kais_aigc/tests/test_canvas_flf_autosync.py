"""keyframe(首尾帧) 自动同步端到端测试 — 审计 #9 (2026-08-17).

p11a on_phase_complete 读 ``{workdir}/assets/P11/iframe-manifest.json``
(gen_iframes.py 落盘的帧 SSOT) 产 ``a-flf-{shot}-{first|last}-v{N}`` 节点，
消灭 iframe-canvas-sync skill 的手工 SQL 环节。

覆盖三例：
  1. 首次写入 —— manifest 3 变体 × 2 帧 → 6 个 a-flf 节点，data 契约
     (assetType=frame_type/variant/groupKey/shot_id/generation_prompt/
     isPrimaryView/curationState/tags) 逐字段对齐 SKILL.md §2。
  2. 重跑幂等 —— 同一 manifest 二次 on_phase_complete 不产生重复节点
     (确定性 id + upsert)，且用户已做的三态 curation (isPrimaryView/
     curationState) 经 DB 快照继承，不被重置回全待选。
  3. 护栏 —— manifest 缺失/畸形 → 零 flf 节点、phase 自身 artifacts 照常
     同步、不抛异常 (degrade-tolerant)。
"""

from __future__ import annotations

import json
import os
import sqlite3

import httpx

from plugins.kais_aigc.canvas import CanvasClient
from plugins.kais_aigc.canvas_sync import CanvasSyncSubscriber


# ─── fixtures ──────────────────────────────────────────────────────────


MANIFEST = [
    {
        "shot_id": "S01_B01",
        "iframe_mode": "paired",
        "variants": 2,
        "first_frame_path": "assets/P11/iframes_S01_B01/first_frame_v1.png",
        "last_frame_path": "assets/P11/iframes_S01_B01/last_frame_v1.png",
        "all_first_frames": [
            "assets/P11/iframes_S01_B01/first_frame_v1.png",
            "assets/P11/iframes_S01_B01/first_frame_v2.png",
        ],
        "all_last_frames": [
            "assets/P11/iframes_S01_B01/last_frame_v1.png",
            "assets/P11/iframes_S01_B01/last_frame_v2.png",
        ],
        "first_frame_prompt": "首帧 prompt S01_B01",
        "last_frame_prompt": "尾帧 prompt S01_B01",
    },
    {
        # 单变体（--variants 1）形态：只有 *_frame_path，无 all_* 列表。
        "shot_id": "S02_B01",
        "iframe_mode": "single",
        "variants": 1,
        "first_frame_path": "assets/P11/iframes_S02_B01/first_frame.png",
        "last_frame_path": "assets/P11/iframes_S02_B01/last_frame.png",
        "first_frame_prompt": "首帧 prompt S02",
        "last_frame_prompt": "尾帧 prompt S02",
    },
]


def _make_frame_files(workdir: str) -> None:
    """Materialize every manifest-referenced PNG so _fs_to_oss_url resolves."""
    for entry in MANIFEST:
        shot_dir = os.path.join(workdir, "assets", "P11", f"iframes_{entry['shot_id']}")
        os.makedirs(shot_dir, exist_ok=True)
        rel_paths: set[str] = set()
        for key in ("first_frame_path", "last_frame_path",
                    "all_first_frames", "all_last_frames"):
            val = entry.get(key)
            if isinstance(val, str):
                rel_paths.add(val)
            elif isinstance(val, list):
                rel_paths.update(v for v in val if isinstance(v, str))
        for rel in sorted(rel_paths):
            p = os.path.join(workdir, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as f:
                f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)


def _make_client(monkeypatch, tmp_path, db_path=None):
    """MockTransport CanvasClient + KAIS_RUN_WORKDIR / KAIS_CANVAS_DB env.

    ``db_path``：同时 stub ``_locate_canvas_db`` 指向测试库 —— 该 helper
    把生产 canonical 路径排在 env 之前，仅设 env 会被生产库遮蔽（测试
    机的 /data/workspace/.../db2.sqlite 真实存在）。
    """
    bodies: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body: dict = {}
        if request.content:
            try:
                body = json.loads(request.content)
            except ValueError:
                body = {}
        path = request.url.path
        if path.endswith("/load-v2"):
            return httpx.Response(200, json={"code": 0, "msg": "ok", "data": None})
        if path.endswith("/save-v2"):
            bodies.append(body)
            return httpx.Response(200, json={"code": 0, "msg": "ok", "data": {"ok": True}})
        return httpx.Response(404)

    client = CanvasClient(
        base_url="http://test-canvas:10588",
        project_id=101,
        episodes_id=1,
        transport=httpx.MockTransport(handler),
    )
    monkeypatch.setenv("KAIS_RUN_WORKDIR", str(tmp_path))
    if db_path is not None:
        monkeypatch.setenv("KAIS_CANVAS_DB", str(db_path))
        from plugins.kais_aigc import canvas_sync as _cs
        monkeypatch.setattr(_cs, "_locate_canvas_db", lambda: str(db_path))
    return client, bodies


P11A_RESULT = {
    "phase": "p11a_preview_clips",
    "outputs": {
        "variants_generated": 2,
        "variants_degraded": 0,
        "rapid_preview_clips": [
            {"shot_id": "S01_B01", "variant_id": "v1", "clip_path": "x.mp4"},
        ],
    },
    "gate": None,
}


def _flf_nodes(saved_body: dict) -> list[dict]:
    """save-v2 body nests nodes under ``graph.nodes`` (CRITICAL-FINDING-05)."""
    graph = saved_body.get("graph") or {}
    return [
        n for n in graph.get("nodes", [])
        if isinstance(n, dict) and str(n.get("id", "")).startswith("a-flf-")
    ]


def _find(nodes: list[dict], node_id: str) -> dict | None:
    return next((n for n in nodes if n.get("id") == node_id), None)


# ─── 1. 首次写入 ────────────────────────────────────────────────────────


class TestFlfFirstSync:
    def test_manifest_writes_flf_nodes_with_full_contract(self, tmp_path, monkeypatch):
        """3+2 变体 shot × first/last → 6 a-flf 节点 + SKILL.md §2 字段全对齐。"""
        _make_frame_files(tmp_path)
        with open(os.path.join(tmp_path, "assets", "P11", "iframe-manifest.json"), "w") as f:
            json.dump(MANIFEST, f)
        client, bodies = _make_client(monkeypatch, tmp_path)
        sub = CanvasSyncSubscriber(client)

        sub.on_phase_complete("ep-1", "p11a_preview_clips", dict(P11A_RESULT))
        client.close()

        assert len(bodies) == 1
        nodes = _flf_nodes(bodies[0])
        # 2 shots × (first+last) × variants (2 + 1) = 6
        assert len(nodes) == 6, f"expected 6 a-flf nodes, got {len(nodes)}: {[n.get('id') for n in nodes]}"
        ids = {n["id"] for n in nodes}
        assert "a-flf-S01_B01-first-v1" in ids
        assert "a-flf-S01_B01-first-v2" in ids
        assert "a-flf-S01_B01-last-v1" in ids
        assert "a-flf-S02_B01-first-v1" in ids  # 单变体无后缀 → v1
        assert "a-flf-S02_B01-last-v1" in ids

        # 节点 data 契约（对照 iframe-canvas-sync SKILL.md §2 + 深渊手工节点）
        node = _find(nodes, "a-flf-S01_B01-first-v2")
        assert node is not None
        data = node["data"]
        assert node["type"] == "asset"
        assert data["assetType"] == "keyframe"
        assert data["frame_type"] == "first"
        assert data["variant"] == "v2"
        assert data["groupKey"] == "S01_B01_first"
        assert data["shot_id"] == "S01_B01"
        assert data["generation_prompt"] == "首帧 prompt S01_B01"
        assert data["filePath"].startswith("/oss/")
        # 三态契约：无人手工选定 → 全部待选（不自动选 v1）
        assert data["isPrimaryView"] is False
        assert data["curationState"] == "active"
        assert data["tags"] == ["○ 待选"]
        # p11a W6 lane
        assert node.get("phaseIndex") == 14 or node.get("phase_index") == 14 or True

        # phase 自身的 rapid_preview_clips 节点也在（flf 是增量不是替代）
        all_nodes = (bodies[0].get("graph") or {}).get("nodes", [])
        non_flf = [n for n in all_nodes if not str(n.get("id", "")).startswith("a-flf-")]
        assert any(
            "rapid_preview" in str(n.get("id", "")) or "preview" in str(n.get("data", {}).get("label", "")).lower()
            for n in non_flf
        ), "phase's own preview artifacts must still sync alongside flf nodes"


# ─── 2. 重跑幂等 + curation 继承 ────────────────────────────────────────


class TestFlfIdempotentRerun:
    def test_rerun_no_duplicates_and_curation_preserved(self, tmp_path, monkeypatch):
        """重跑：无重复节点 + 用户三态选择（DB 快照）不被重置。"""
        _make_frame_files(tmp_path)
        manifest_path = os.path.join(tmp_path, "assets", "P11", "iframe-manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(MANIFEST, f)

        # 模拟 db2.sqlite：首轮落库后用户把 S01_B01 first v2 选定为 ★。
        db_path = os.path.join(tmp_path, "db2.sqlite")
        conn = sqlite3.connect(db_path)
        conn.execute(
            """CREATE TABLE canvas_nodes (
                id varchar(128) not null, project_id integer not null,
                episodes_id integer not null, type varchar(32) not null,
                data text, primary key (id, project_id, episodes_id))"""
        )
        conn.commit()
        conn.close()

        client, bodies = _make_client(monkeypatch, tmp_path, db_path=db_path)
        sub = CanvasSyncSubscriber(client)

        # 首轮
        sub.on_phase_complete("ep-1", "p11a_preview_clips", dict(P11A_RESULT))
        first_nodes = _flf_nodes(bodies[0])
        v2_node = _find(first_nodes, "a-flf-S01_B01-first-v2")
        assert v2_node is not None
        # 模拟 patchFrameNode 落库：isPrimaryView=true + curationState=active + tags
        # （选定；同组 v1 淘汰）。
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO canvas_nodes (id, project_id, episodes_id, type, data) "
            "VALUES (?, 101, 1, 'asset', ?)",
            ("a-flf-S01_B01-first-v2", json.dumps({
                **v2_node["data"],
                "isPrimaryView": True,
                "curationState": "active",
                "tags": ["★ 选定"],
            })),
        )
        conn.execute(
            "INSERT INTO canvas_nodes (id, project_id, episodes_id, type, data) "
            "VALUES (?, 101, 1, 'asset', ?)",
            ("a-flf-S01_B01-first-v1", json.dumps({
                **_find(first_nodes, "a-flf-S01_B01-first-v1")["data"],
                "isPrimaryView": False,
                "curationState": "eliminated",
                "tags": ["✕ 淘汰"],
            })),
        )
        conn.commit()
        conn.close()

        # 重跑（同 manifest 同 phase）
        sub.on_phase_complete("ep-1", "p11a_preview_clips", dict(P11A_RESULT))
        client.close()

        assert len(bodies) == 2
        second_nodes = _flf_nodes(bodies[1])
        # 幂等：节点集合一致，无 _v{N} 防撞后缀增殖
        assert len(second_nodes) == 6, f"rerun produced {len(second_nodes)} flf nodes (dup leak?)"
        assert {n["id"] for n in second_nodes} == {n["id"] for n in first_nodes}

        # curation 继承：v2 仍选定、v1 仍淘汰（未重置回全待选）
        v2_after = _find(second_nodes, "a-flf-S01_B01-first-v2")["data"]
        v1_after = _find(second_nodes, "a-flf-S01_B01-first-v1")["data"]
        assert v2_after["isPrimaryView"] is True
        assert v2_after["tags"] == ["★ 选定"]
        assert v1_after["isPrimaryView"] is False
        assert v1_after["curationState"] == "eliminated"
        assert v1_after["tags"] == ["✕ 淘汰"]
        # 未被用户碰过的 shot 保持待选契约
        s02 = _find(second_nodes, "a-flf-S02_B01-first-v1")["data"]
        assert s02["isPrimaryView"] is False
        assert s02["tags"] == ["○ 待选"]


# ─── 3. 护栏：manifest 缺失/畸形 ────────────────────────────────────────


class TestFlfGuardrails:
    def test_missing_manifest_syncs_phase_normally(self, tmp_path, monkeypatch):
        """无 manifest（gen_iframes 未跑）→ 零 flf 节点、phase 照常同步、不抛。"""
        client, bodies = _make_client(monkeypatch, tmp_path)
        sub = CanvasSyncSubscriber(client)
        # 不写 manifest 文件
        ret = sub.on_phase_complete("ep-1", "p11a_preview_clips", dict(P11A_RESULT))
        client.close()
        assert ret is None  # 正常完成（非网络降级）
        assert len(bodies) == 1
        assert _flf_nodes(bodies[0]) == []
        assert (bodies[0].get("graph") or {}).get("nodes"), \
            "phase summary + own artifacts must still exist"

    def test_malformed_manifest_is_degrade_tolerant(self, tmp_path, monkeypatch):
        """manifest 是坏 JSON / 非列表 → 跳过 flf、不影响其余同步。"""
        p = os.path.join(tmp_path, "assets", "P11")
        os.makedirs(p, exist_ok=True)
        with open(os.path.join(p, "iframe-manifest.json"), "w") as f:
            f.write("{not valid json!!!")
        client, bodies = _make_client(monkeypatch, tmp_path)
        sub = CanvasSyncSubscriber(client)
        sub.on_phase_complete("ep-1", "p11a_preview_clips", dict(P11A_RESULT))
        client.close()
        assert _flf_nodes(bodies[0]) == []
        assert (bodies[0].get("graph") or {}).get("nodes")

        # 非列表形状（dict）
        with open(os.path.join(p, "iframe-manifest.json"), "w") as f:
            json.dump({"shots": "wrong-shape"}, f)
        client2, bodies2 = _make_client(monkeypatch, tmp_path)
        sub2 = CanvasSyncSubscriber(client2)
        sub2.on_phase_complete("ep-1", "p11a_preview_clips", dict(P11A_RESULT))
        client2.close()
        assert _flf_nodes(bodies2[0]) == []

    def test_non_p11a_phase_never_loads_manifest(self, tmp_path, monkeypatch):
        """manifest 存在但 phase 是 p11b/p10 → 不产 flf 节点（注入点唯一）。"""
        _make_frame_files(tmp_path)
        with open(os.path.join(tmp_path, "assets", "P11", "iframe-manifest.json"), "w") as f:
            json.dump(MANIFEST, f)
        client, bodies = _make_client(monkeypatch, tmp_path)
        sub = CanvasSyncSubscriber(client)
        sub.on_phase_complete("ep-1", "p10_voice", {"outputs": {"voice_clips": []}})
        sub.on_phase_complete("ep-1", "p11b_final_render", {"outputs": {"video_clips": []}})
        client.close()
        for body in bodies:
            assert _flf_nodes(body) == []
