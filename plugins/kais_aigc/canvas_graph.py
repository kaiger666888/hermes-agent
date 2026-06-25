"""canvas_graph.py — Pure FlowGraph mutation functions.

Phase 37 Plan 02 — Python port of the FlowGraph-mutation subset of
Node.js ``lib/canvas-sync-hook.js`` (upsertNode, ensureLink,
computeNodePosition, defaultPhaseMapper) and the skeleton-builder logic
in ``canvas-content-sync.js saveGraph`` / Node.js ``loadGraph || {}``.

Scope (D-37-03):
  - Every function here is **pure** — no ``import httpx``, no logging, no I/O.
  - The HTTP orchestration lives in ``canvas_sync.py`` (the subscriber that
    builds a FlowGraph via these functions then persists via the Phase 32
    ``CanvasClient``).
  - Trivially unit-testable: dict in, dict out, no mocking required.

Behavioral parity:
  - CF-37-04: ``default_phase_mapper`` regex is the verbatim port of the
    Node.js phase-grouping logic.
  - CF-37-05: ``compute_node_position`` lane layout (research x=100,
    story x=1200, production x=2000, post x=2800, 3-per-row wrap) is the
    verbatim port.
"""

from __future__ import annotations

import time
from typing import Any

# ─── phase-group prefixes (CF-37-04 verbatim port) ──────────────────────

# Node.js regex: /^(pain|topic|outline|script|character|scene|spatio)/
_PHASE_GROUP_RESEARCH_PREFIXES: tuple[str, ...] = (
    "pain",
    "topic",
    "outline",
    "script",
    "character",
    "scene",
    "spatio",
)

# Node.js regex: /^(seed|motion|ai-preview|consistency|render|final)/
_PHASE_GROUP_PRODUCTION_PREFIXES: tuple[str, ...] = (
    "seed",
    "motion",
    "ai-preview",
    "consistency",
    "render",
    "final",
)

# Node.js computeNodePosition laneX map (CF-37-05).
_LANE_X: dict[str, int] = {
    "research": 100,
    "story": 1200,
    "production": 2000,
    "post": 2800,
}


def default_phase_mapper(phase: dict[str, Any]) -> dict[str, Any]:
    """Map a pipeline phase dict to canvas node metadata.

    Verbatim port of Node.js ``defaultPhaseMapper`` (canvas-sync-hook.js
    lines 41-57). Infers ``phaseGroup`` (research / story / production)
    from the phase's ``stage`` prefix; ``research`` if ``stage_order <= 5``
    else ``story``.

    Args:
        phase: ``{id, name, stage, stage_order, review, output_files}``.
            Snake-case keys are accepted as aliases to the Node.js
            camelCase originals (the v5.0 Python pipeline emits
            ``stage_order`` / ``output_files``).

    Returns:
        ``{label, phase, tags, filePath}`` for canvas ``node.data``.
    """
    # Node.js: ``const stage = phase.stage || phase.id || ''``
    stage = phase.get("stage") or phase.get("id") or ""
    stage_order = phase.get("stage_order", phase.get("stageOrder", 99))

    phase_group = "production"
    if isinstance(stage, str) and stage.startswith(_PHASE_GROUP_RESEARCH_PREFIXES):
        phase_group = "research" if stage_order <= 5 else "story"
    elif isinstance(stage, str) and stage.startswith(_PHASE_GROUP_PRODUCTION_PREFIXES):
        phase_group = "production"

    output_files = phase.get("output_files", phase.get("outputFiles", [])) or []
    file_path = ", ".join(output_files) if output_files else None

    return {
        "label": phase.get("name") or phase.get("id", ""),
        "phase": phase_group,
        "tags": ["需审核"] if phase.get("review") else [],
        "filePath": file_path,
    }


def compute_node_position(phase_group: str, stage_order: int) -> dict[str, int]:
    """Compute a lane-layout position for a canvas node.

    Verbatim port of Node.js ``computeNodePosition`` (canvas-sync-hook.js
    lines 142-152). Four lanes (research / story / production / post),
    three nodes per row, 200px row height, 350px column delta.

    Args:
        phase_group: One of ``research`` / ``story`` / ``production`` /
            ``post`` (unknown groups fall back to the production lane).
        stage_order: Zero-based index within the lane. Controls both the
            column (``stage_order % 3``) and the row (``stage_order // 3``).

    Returns:
        ``{"x": int, "y": int}``.
    """
    x = _LANE_X.get(phase_group, 2000) + (stage_order % 3) * 350
    y = 100 + (stage_order // 3) * 200
    return {"x": x, "y": y}


def upsert_node(
    graph: dict[str, Any],
    node_id: str,
    node_data: dict[str, Any],
) -> dict[str, Any]:
    """Insert or merge a node into ``graph`` by id.

    Port of Node.js ``upsertNode`` (canvas-sync-hook.js lines 156-175):
      - Find existing node by ``id``.
      - If found: shallow-merge top-level fields, deep-merge ``data``,
        preserve existing ``position`` when the new payload omits it.
      - Else: append ``{id, **node_data}``.

    The graph is mutated in place and returned for chaining.

    Args:
        graph: FlowGraph dict (must contain a ``nodes`` list).
        node_id: Node ``id`` to upsert by.
        node_data: Fields to merge / insert (excluding ``id``).

    Returns:
        The (mutated) ``graph``.
    """
    nodes = graph.setdefault("nodes", [])
    existing_idx = next(
        (i for i, n in enumerate(nodes) if n.get("id") == node_id),
        None,
    )

    if existing_idx is not None:
        existing = nodes[existing_idx]
        merged = {**existing, **node_data}
        # Deep-merge the data dict (Node.js: data: {...existing.data, ...nodeData.data})
        merged_data = {**existing.get("data", {}), **node_data.get("data", {})}
        merged["data"] = merged_data
        # Node.js: position: nodeData.position || existing.position
        if "position" not in node_data and "position" in existing:
            merged["position"] = existing["position"]
        nodes[existing_idx] = merged
    else:
        nodes.append({"id": node_id, **node_data})

    return graph


def ensure_link(
    graph: dict[str, Any],
    link_id: str,
    source: str,
    target: str,
) -> dict[str, Any]:
    """Add a link to ``graph`` if no link with ``link_id`` exists yet.

    Port of Node.js ``ensureLink`` (canvas-sync-hook.js lines 179-190).
    No-op when the link id is already present (idempotent).

    Args:
        graph: FlowGraph dict (must contain a ``links`` list).
        link_id: Unique link id (e.g. ``"l-p01-p02"``).
        source: Source node id.
        target: Target node id.

    Returns:
        The (possibly mutated) ``graph``.
    """
    links = graph.setdefault("links", [])
    if any(l.get("id") == link_id for l in links):
        return graph
    links.append({
        "id": link_id,
        "source": source,
        "target": target,
        "branchId": "main",
        "dataType": "flow",
    })
    return graph


def empty_graph(project_id: int, episodes_id: int) -> dict[str, Any]:
    """Construct a valid empty FlowGraph skeleton.

    The shape mirrors the Node.js fallback graph
    (``{nodes: [], links: [], branches: [...], variantGroups: []}``)
    plus the ``meta`` block the save-v2 endpoint expects
    (version=2, projectId, episodesId, timestamps in ms epoch).

    Args:
        project_id: Canvas project id.
        episodes_id: Canvas episodes id.

    Returns:
        A fresh FlowGraph dict with all five top-level keys populated.
    """
    now_ms = int(time.time() * 1000)
    return {
        "nodes": [],
        "links": [],
        "branches": [
            {
                "id": "main",
                "label": "主线",
                "status": "active",
                "createdAt": now_ms,
                "updatedAt": now_ms,
            }
        ],
        "variantGroups": [],
        "meta": {
            "version": "2",
            "projectId": project_id,
            "episodesId": episodes_id,
            "createdAt": now_ms,
            "updatedAt": now_ms,
        },
    }


def normalize_loaded_graph(
    loaded: dict[str, Any] | None,
    project_id: int,
    episodes_id: int,
) -> dict[str, Any]:
    """Defensively normalize the result of ``CanvasClient.load_canvas()``.

    - If ``loaded`` is ``None`` or not a dict → return ``empty_graph(...)``.
    - Else: ensure every one of the five FlowGraph top-level keys exists
      (``nodes``, ``links``, ``branches``, ``variantGroups``, ``meta``).
      Missing keys are filled with empty containers / a fresh meta block.

    Defensive by design: the load-v2 endpoint may return legacy graphs
    missing keys, or a degrade envelope dict. The subscriber must never
    crash while iterating.

    Args:
        loaded: Raw return value of ``CanvasClient.load_canvas()``
            (typically a FlowGraph dict, ``None``, or a degrade envelope).
        project_id: Canvas project id (used when constructing a skeleton).
        episodes_id: Canvas episodes id.

    Returns:
        A dict with all five FlowGraph keys present.
    """
    if not isinstance(loaded, dict):
        return empty_graph(project_id, episodes_id)

    graph = loaded
    graph.setdefault("nodes", [])
    if not isinstance(graph["nodes"], list):
        graph["nodes"] = []
    graph.setdefault("links", [])
    if not isinstance(graph["links"], list):
        graph["links"] = []
    graph.setdefault("branches", [])
    if not isinstance(graph["branches"], list):
        graph["branches"] = []
    graph.setdefault("variantGroups", [])
    if not isinstance(graph["variantGroups"], list):
        graph["variantGroups"] = []
    meta = graph.get("meta")
    if not isinstance(meta, dict):
        now_ms = int(time.time() * 1000)
        graph["meta"] = {
            "version": "2",
            "projectId": project_id,
            "episodesId": episodes_id,
            "createdAt": now_ms,
            "updatedAt": now_ms,
        }
    return graph
