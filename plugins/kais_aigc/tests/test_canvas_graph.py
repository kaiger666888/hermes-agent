"""Pure-function unit tests for plugins.kais_aigc.canvas_graph.

No HTTP, no MockTransport — every function under test is pure
(D-37-03). These tests assert behavioral parity with the Node.js
``lib/canvas-sync-hook.js`` reference (CF-37-04 / CF-37-05).
"""

from __future__ import annotations

from plugins.kais_aigc import canvas_graph


# ─── upsert_node ────────────────────────────────────────────────────────


class TestUpsertNode:
    def test_upsert_node_new_appends(self):
        graph = {"nodes": [], "links": []}
        canvas_graph.upsert_node(graph, "n-p01", {"state": "success"})
        assert len(graph["nodes"]) == 1
        node = graph["nodes"][0]
        assert node["id"] == "n-p01"
        assert node["state"] == "success"

    def test_upsert_node_existing_merges(self):
        graph = {
            "nodes": [
                {"id": "n-p01", "state": "running", "data": {"label": "old"}}
            ],
            "links": [],
        }
        canvas_graph.upsert_node(
            graph, "n-p01", {"state": "success", "data": {"score": 9}}
        )
        assert len(graph["nodes"]) == 1
        node = graph["nodes"][0]
        # Top-level field overwritten.
        assert node["state"] == "success"
        # Data dict merged, not replaced (label preserved, score added).
        assert node["data"]["label"] == "old"
        assert node["data"]["score"] == 9

    def test_upsert_node_position_preserved_if_not_provided(self):
        graph = {
            "nodes": [
                {
                    "id": "n-p01",
                    "position": {"x": 100, "y": 200},
                    "data": {"label": "first"},
                }
            ],
            "links": [],
        }
        canvas_graph.upsert_node(graph, "n-p01", {"data": {"label": "second"}})
        node = graph["nodes"][0]
        # Position unchanged because new payload omitted it.
        assert node["position"] == {"x": 100, "y": 200}

    def test_upsert_node_position_overwritten_when_provided(self):
        graph = {
            "nodes": [
                {
                    "id": "n-p01",
                    "position": {"x": 100, "y": 200},
                    "data": {"label": "first"},
                }
            ],
            "links": [],
        }
        canvas_graph.upsert_node(
            graph, "n-p01", {"position": {"x": 999, "y": 999}}
        )
        node = graph["nodes"][0]
        assert node["position"] == {"x": 999, "y": 999}


# ─── ensure_link ────────────────────────────────────────────────────────


class TestEnsureLink:
    def test_ensure_link_new_adds(self):
        graph = {"nodes": [], "links": []}
        canvas_graph.ensure_link(graph, "l-p01-p02", "n-p01", "n-p02")
        assert len(graph["links"]) == 1
        link = graph["links"][0]
        assert link["id"] == "l-p01-p02"
        assert link["source"] == "n-p01"
        assert link["target"] == "n-p02"
        assert link["branchId"] == "main"

    def test_ensure_link_duplicate_noop(self):
        graph = {
            "nodes": [],
            "links": [
                {
                    "id": "l-p01-p02",
                    "source": "n-p01",
                    "target": "n-p02",
                    "branchId": "main",
                }
            ],
        }
        canvas_graph.ensure_link(graph, "l-p01-p02", "n-p01", "n-p02")
        assert len(graph["links"]) == 1


# ─── compute_node_position ──────────────────────────────────────────────


class TestComputeNodePosition:
    def test_compute_node_position_research_lane(self):
        pos = canvas_graph.compute_node_position("research", 0)
        # Lane x=100, stage_order % 3 == 0 → no column delta.
        assert pos == {"x": 100, "y": 100}

    def test_compute_node_position_wraps_3_per_row(self):
        # stage_order 3 → row 1 (//3 == 1), column 0 (%3 == 0).
        pos = canvas_graph.compute_node_position("production", 3)
        # Production lane x=2000; y = 100 + 1*200 = 300.
        assert pos["x"] == 2000
        assert pos["y"] == 300

    def test_compute_node_position_unknown_group_falls_back(self):
        pos = canvas_graph.compute_node_position("unknown-group", 0)
        # Falls back to production lane (2000).
        assert pos["x"] == 2000
        assert pos["y"] == 100


# ─── default_phase_mapper ───────────────────────────────────────────────


class TestDefaultPhaseMapper:
    def test_default_phase_mapper_research_prefix(self):
        # stage="topic", stage_order=1 → research (order <= 5).
        mapped = canvas_graph.default_phase_mapper(
            {"id": "p01", "name": "主题选择", "stage": "topic", "stage_order": 1}
        )
        assert mapped["phase"] == "research"
        assert mapped["label"] == "主题选择"

    def test_default_phase_mapper_story_prefix_high_order(self):
        # stage="scene", stage_order=7 → story (research prefix, order > 5).
        mapped = canvas_graph.default_phase_mapper(
            {"id": "p07", "name": "场景设计", "stage": "scene", "stage_order": 7}
        )
        assert mapped["phase"] == "story"

    def test_default_phase_mapper_production_prefix(self):
        # stage="render" → production.
        mapped = canvas_graph.default_phase_mapper(
            {"id": "p11", "name": "渲染", "stage": "render", "stage_order": 10}
        )
        assert mapped["phase"] == "production"

    def test_default_phase_mapper_review_adds_tag(self):
        mapped = canvas_graph.default_phase_mapper(
            {"id": "p03", "name": "剧本", "stage": "script", "review": True}
        )
        assert "需审核" in mapped["tags"]

    def test_default_phase_mapper_file_path_from_output_files(self):
        mapped = canvas_graph.default_phase_mapper(
            {
                "id": "p01",
                "stage": "topic",
                "output_files": ["output/p01.json", "output/p01.md"],
            }
        )
        assert mapped["filePath"] == "output/p01.json, output/p01.md"


# ─── empty_graph + normalize_loaded_graph ───────────────────────────────


class TestEmptyGraph:
    def test_empty_graph_shape(self):
        graph = canvas_graph.empty_graph(1, 1)
        # All five top-level keys present.
        for key in ("nodes", "links", "branches", "variantGroups", "meta"):
            assert key in graph, f"missing key: {key}"
        # Main branch present.
        assert len(graph["branches"]) == 1
        assert graph["branches"][0]["id"] == "main"
        assert graph["branches"][0]["label"] == "主线"
        # Meta versioned.
        assert graph["meta"]["version"] == "2"
        assert graph["meta"]["projectId"] == 1
        assert graph["meta"]["episodesId"] == 1


class TestNormalizeLoadedGraph:
    def test_normalize_loaded_graph_none(self):
        graph = canvas_graph.normalize_loaded_graph(None, 1, 1)
        # Falls back to a full skeleton.
        assert "nodes" in graph and graph["nodes"] == []
        assert "branches" in graph and len(graph["branches"]) == 1
        assert graph["meta"]["version"] == "2"

    def test_normalize_loaded_graph_partial(self):
        # Loaded graph missing variantGroups + meta.
        loaded = {"nodes": [{"id": "n1"}], "links": []}
        graph = canvas_graph.normalize_loaded_graph(loaded, 7, 8)
        assert graph["variantGroups"] == []
        assert isinstance(graph["meta"], dict)
        assert graph["meta"]["projectId"] == 7
        assert graph["meta"]["episodesId"] == 8

    def test_normalize_loaded_graph_degrade_envelope(self):
        # A degrade envelope dict (not None, but not a FlowGraph) must
        # still be normalized without crashing.
        loaded = {"degraded": True, "reason": "connect error"}
        graph = canvas_graph.normalize_loaded_graph(loaded, 1, 1)
        assert graph["nodes"] == []
        assert graph["links"] == []
