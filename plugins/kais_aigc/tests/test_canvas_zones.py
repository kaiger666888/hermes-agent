"""Tests for zone, candidate, and review node functions in canvas_graph.py.

Covers the Phase 38 additions:
- ensure_zone_node / ensure_zone_chain / ensure_zone_to_child
- compute_zone_position
- add_candidate_node / add_review_node
- sanitize_v2_graph with zone type
"""

from __future__ import annotations

from plugins.kais_aigc import canvas_graph


# ─── zone node creation ────────────────────────────────────────────────


def test_ensure_zone_node_creates():
    graph = canvas_graph.empty_graph(1, 1)
    zone_id = canvas_graph.ensure_zone_node(graph, "p04")
    assert zone_id == "p04"
    nodes = [n for n in graph["nodes"] if n["id"] == "p04"]
    assert len(nodes) == 1
    assert nodes[0]["type"] == "zone"
    assert nodes[0]["data"]["label"] == "P04 · 角色设计"
    assert nodes[0]["data"]["phase"] == "story"


def test_ensure_zone_node_idempotent():
    graph = canvas_graph.empty_graph(1, 1)
    canvas_graph.ensure_zone_node(graph, "p01")
    canvas_graph.ensure_zone_node(graph, "p01")
    nodes = [n for n in graph["nodes"] if n["id"] == "p01"]
    assert len(nodes) == 1


def test_ensure_zone_node_unknown_prefix():
    graph = canvas_graph.empty_graph(1, 1)
    zone_id = canvas_graph.ensure_zone_node(graph, "p99")
    assert zone_id == "p99"
    assert [n for n in graph["nodes"] if n["id"] == "p99"]


def test_compute_zone_position():
    pos = canvas_graph.compute_zone_position("p01")
    assert pos["x"] == 0
    assert pos["y"] == -80

    # Lane-order invariants instead of absolute indices: inserting a phase
    # (p035 86ke polish, p036 hook_reconcile, …) shifts successors by exactly
    # one lane width — never reorders or drops existing lanes. Absolute-index
    # pins broke on every insertion; this survives them.
    step = canvas_graph._ZONE_X_STEP
    order = ["p03", "p035", "p036", "p04"]
    xs = {p: canvas_graph.compute_zone_position(p)["x"] for p in order}
    assert list(xs.values()) == sorted(xs.values()), f"lane order broken: {{xs}}"
    for a, b in zip(order, order[1:]):
        assert xs[b] - xs[a] == step, f"{{a}}→{{b}} gap != one lane width: {{xs}}"
    assert canvas_graph.compute_zone_position("p04")["y"] == -80


# ─── zone chain ────────────────────────────────────────────────────────


def test_ensure_zone_chain():
    graph = canvas_graph.empty_graph(1, 1)
    canvas_graph.ensure_zone_node(graph, "p01")
    canvas_graph.ensure_zone_node(graph, "p02")
    canvas_graph.ensure_zone_node(graph, "p04")
    canvas_graph.ensure_zone_chain(graph)

    # Should have p01→p02 and p02→p04 (skipping p03 which doesn't exist).
    link_ids = {l["id"] for l in graph["links"]}
    assert "zl-p01-p02" in link_ids
    assert "zl-p02-p04" in link_ids
    # p03 was skipped.
    assert not any("p03" in lid for lid in link_ids)


def test_ensure_zone_chain_idempotent():
    graph = canvas_graph.empty_graph(1, 1)
    canvas_graph.ensure_zone_node(graph, "p01")
    canvas_graph.ensure_zone_node(graph, "p02")
    canvas_graph.ensure_zone_chain(graph)
    canvas_graph.ensure_zone_chain(graph)
    chain_links = [l for l in graph["links"] if l["id"].startswith("zl-")]
    assert len(chain_links) == 1


# ─── zone to child ─────────────────────────────────────────────────────


def test_ensure_zone_to_child():
    graph = canvas_graph.empty_graph(1, 1)
    canvas_graph.ensure_zone_node(graph, "p04")
    canvas_graph.upsert_node(graph, "child-1", {
        "type": "asset", "position": {"x": 100, "y": 100}, "data": {},
    })
    canvas_graph.ensure_zone_to_child(graph, "p04", "child-1")

    links = [l for l in graph["links"] if l["source"] == "p04" and l["target"] == "child-1"]
    assert len(links) == 1


def test_ensure_zone_to_child_idempotent():
    graph = canvas_graph.empty_graph(1, 1)
    canvas_graph.ensure_zone_node(graph, "p04")
    canvas_graph.upsert_node(graph, "child-1", {
        "type": "asset", "position": {"x": 100, "y": 100}, "data": {},
    })
    canvas_graph.ensure_zone_to_child(graph, "p04", "child-1")
    canvas_graph.ensure_zone_to_child(graph, "p04", "child-1")
    links = [l for l in graph["links"] if l["source"] == "p04"]
    assert len(links) == 1


# ─── candidate node ────────────────────────────────────────────────────


def test_add_candidate_node_selected():
    graph = canvas_graph.empty_graph(1, 1)
    node_id = canvas_graph.add_candidate_node(
        graph, "p02_outline", "alpha",
        "大纲 Alpha — 悬疑先行",
        selected=True,
        description="像侦探片一样逐步揭露",
    )
    assert node_id == "c-p02-alpha"
    node = next(n for n in graph["nodes"] if n["id"] == node_id)
    assert node["type"] == "variant"
    assert node["data"]["tags"] == ["✅ 已选"]
    assert node["data"]["reviewStatus"] == "approved"
    assert node["state"] == "success"


def test_add_candidate_node_unselected():
    graph = canvas_graph.empty_graph(1, 1)
    node_id = canvas_graph.add_candidate_node(
        graph, "p02_outline", "beta",
        "大纲 Beta — 均衡版",
        selected=False,
    )
    node = next(n for n in graph["nodes"] if n["id"] == node_id)
    assert node["data"]["tags"] == ["未选"]
    assert node["data"]["reviewStatus"] == "rejected"
    assert node["state"] == "idle"


def test_add_candidate_node_links_to_zone():
    graph = canvas_graph.empty_graph(1, 1)
    canvas_graph.add_candidate_node(
        graph, "p02_outline", "gamma",
        "大纲 Gamma",
        selected=False,
    )
    # Zone p02 should have been auto-created.
    assert any(n["id"] == "p02" and n["type"] == "zone" for n in graph["nodes"])
    # Link zone → candidate should exist.
    assert any(
        l["source"] == "p02" and "gamma" in l["target"]
        for l in graph["links"]
    )


# ─── review node ───────────────────────────────────────────────────────


def test_add_review_node_approve():
    graph = canvas_graph.empty_graph(1, 1)
    node_id = canvas_graph.add_review_node(
        graph, "p03_script_audit", "gate-script-review",
        "approve", note="剧本审计通过",
    )
    node = next(n for n in graph["nodes"] if n["id"] == node_id)
    assert node["type"] == "suggestion"
    assert node["state"] == "success"
    assert "approve" in node["data"]["tags"]


def test_add_review_node_reject():
    graph = canvas_graph.empty_graph(1, 1)
    node_id = canvas_graph.add_review_node(
        graph, "p04_character_design", "gate-char-review",
        "reject", note="角色一致性不合格",
    )
    node = next(n for n in graph["nodes"] if n["id"] == node_id)
    assert node["state"] == "error"
    assert node["data"]["reviewStatus"] == "rejected"


# ─── sanitize zone type ────────────────────────────────────────────────


def test_sanitize_preserves_zone_type():
    graph = canvas_graph.empty_graph(1, 1)
    canvas_graph.ensure_zone_node(graph, "p04")
    canvas_graph.sanitize_v2_graph(graph)
    node = next(n for n in graph["nodes"] if n["id"] == "p04")
    assert node["type"] == "zone"  # NOT migrated to "script"


# ─── full pipeline simulation ──────────────────────────────────────────


def test_full_pipeline_simulation():
    """Simulate on_phase_complete for P01 + P02 and verify graph structure."""
    graph = canvas_graph.empty_graph(1, 1)

    # Phase 1: topic
    canvas_graph.ensure_zone_node(graph, "p01")
    canvas_graph.ensure_zone_chain(graph)
    canvas_graph.upsert_node(graph, "n-p01_topic", {
        "type": "script", "position": canvas_graph.compute_zone_position("p01"),
        "data": {"label": "Step 1 · 选题+钩子"},
    })
    canvas_graph.ensure_zone_to_child(graph, "p01", "n-p01_topic")

    # Phase 2: outline with 3 variants
    canvas_graph.ensure_zone_node(graph, "p02")
    canvas_graph.ensure_zone_chain(graph)
    canvas_graph.upsert_node(graph, "n-p02_outline", {
        "type": "script", "position": canvas_graph.compute_zone_position("p02"),
        "data": {"label": "Step 2 · 大纲"},
    })
    canvas_graph.ensure_zone_to_child(graph, "p02", "n-p02_outline")

    # Candidates
    for name, sel in [("alpha", True), ("beta", False), ("gamma", False)]:
        canvas_graph.add_candidate_node(
            graph, "p02_outline", name,
            f"大纲 {name}", selected=sel,
        )

    # Pipeline flow link
    canvas_graph.ensure_link(graph, "l-p01-p02", "n-p01_topic", "n-p02_outline")

    # Verify
    zones = [n for n in graph["nodes"] if n["type"] == "zone"]
    assert len(zones) == 2  # p01, p02

    # Zone chain
    assert any(l["source"] == "p01" and l["target"] == "p02" for l in graph["links"])

    # Phase flow link
    assert any(l["source"] == "n-p01_topic" and l["target"] == "n-p02_outline" for l in graph["links"])

    # Candidates
    variants = [n for n in graph["nodes"] if n["type"] == "variant"]
    assert len(variants) == 3
    selected = [v for v in variants if v["data"].get("reviewStatus") == "approved"]
    assert len(selected) == 1
    assert selected[0]["data"]["label"] == "大纲 alpha"

    # Zone → candidate links
    zone_cand_links = [
        l for l in graph["links"]
        if l["source"] == "p02" and "c-p02-" in l["target"]
    ]
    assert len(zone_cand_links) == 3
