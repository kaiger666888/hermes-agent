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

import re
import time
from typing import Any


# Extracts the full phase prefix from a phase_id, preserving any trailing
# letter: p09b_shot_audit → "p09b", p10c_quality_audit → "p10c", p10_voice → "p10".
# Use this instead of phase_id[:3], which truncates p09b→p09 / p10c→p10.
_PHASE_PREFIX_RE = re.compile(r"^(p\d+[a-z]?)")


def _phase_prefix(phase_id: str) -> str:
    """Return the full phase prefix of ``phase_id`` (e.g. ``"p09b"``).

    Falls back to ``""`` when ``phase_id`` is empty / None / unparseable.
    """
    m = _PHASE_PREFIX_RE.match(phase_id or "")
    return m.group(1) if m else ""

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
    file_path = ", ".join(output_files) if output_files else ""

    out = {
        "label": phase.get("name") or phase.get("id", ""),
        "phase": phase_group,
        "tags": ["需审核"] if phase.get("review") else [],
    }
    if file_path:
        out["filePath"] = file_path
    return out


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
        # 71-02 (v3.2 F05/COX-02,两仓统一):kmc 重同步 = 该节点产物真值已
        # 更新,data.stale 一并清除。deep-merge 会把旧 stale 键永久保留
        # (n-* 节点 stale 永久残留的根因);kap 侧 52-02 的 stale 置位走
        # kap 自己的 save 链,不经本函数——此处清除不影响画布编辑链。
        merged_data.pop("stale", None)
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
    *,
    data_type: str = "output",
) -> dict[str, Any]:
    """Add a link to ``graph`` if no link with ``link_id`` exists yet.

    Port of Node.js ``ensureLink`` (canvas-sync-hook.js lines 179-190).
    No-op when the link id is already present (idempotent).

    The ``data_type`` parameter controls the link semantics:

    * ``"output"`` (default) — pipeline flow: artifact produced by phase.
      Rendered as a solid arrow by the frontend.
    * ``"reference"`` — cross-phase/cross-artifact reference: one artifact
      was used as input/reference when generating another (e.g. a P04
      character sheet used as reference for a P07 scene image). Rendered
      as a dashed line by the frontend.
    * ``"review"`` — gate/review relationship. Rendered with a distinct
      style.

    Args:
        graph: FlowGraph dict (must contain a ``links`` list).
        link_id: Unique link id (e.g. ``"l-p01-p02"``).
        source: Source node id.
        target: Target node id.
        data_type: Link semantic type (``"output"`` / ``"reference"`` /
            ``"review"``). Defaults to ``"output"`` for backward
            compatibility.

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
        "dataType": data_type,
    })
    return graph


def ensure_reference_link(
    graph: dict[str, Any],
    source_node_id: str,
    target_node_id: str,
    *,
    ref_type: str = "reference",
) -> dict[str, Any]:
    """Add a ``dataType="reference"`` link between two existing nodes.

    Unlike ``ensure_link``, the link id is derived from the source + target
    node ids + ``ref_type`` (so the same pair can have multiple reference
    types if needed, but duplicate same-type references are idempotent).

    The frontend renders reference links as dashed lines, visually distinct
    from the solid pipeline-flow (``dataType="output"``) arrows.

    Use cases (V4 canvas):
    * P04 character sheet → P07 scene image (character reference)
    * P07 scene image → P09 shot (starting image reference)
    * P07 multi-angle reference → P07 individual angle images
    * P04 character sheets → P04 L2 crops (internal decomposition)

    Args:
        graph: FlowGraph dict.
        source_node_id: The reference source (e.g. ``"a-p04-laolin"``).
        target_node_id: The reference consumer (e.g. ``"a-p07-scene-01"``).
        ref_type: Reference sub-type for link id namespacing. Defaults to
            ``"reference"``. Can be ``"character_ref"`` /
            ``"scene_ref"`` etc. for finer-grained grouping.

    Returns:
        The (possibly mutated) ``graph``.
    """
    link_id = f"ref-{ref_type}-{source_node_id}-{target_node_id}"
    return ensure_link(
        graph, link_id, source_node_id, target_node_id,
        data_type="reference",
    )


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
                "parentId": "",
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


# ─── v2 schema enums (must match flowgraph-v2-schema.ts) ───────────────

# Valid node types per Canvas API v2 zod schema.
_V2_VALID_NODE_TYPES: frozenset[str] = frozenset({
    "script", "asset", "storyboard", "video", "audio",
    "3d", "variant", "reference", "upscale", "face_restore",
    "suggestion", "zone",
})

# Valid node states per Canvas API v2 zod schema.
_V2_VALID_NODE_STATES: frozenset[str] = frozenset({
    "idle", "pending", "running", "success", "error", "skipped",
})

# Valid branch statuses per Canvas API v2 zod schema.
_V2_VALID_BRANCH_STATUSES: frozenset[str] = frozenset({
    "draft", "active", "paused", "completed", "archived", "rejected",
})

# Mapping from known legacy/v1 node types to the closest v2-valid type.
# This covers types produced by older versions of the frontend or
# manual API usage that predate the strict v2 schema.
_NODE_TYPE_MIGRATION_MAP: dict[str, str] = {
    # Legacy compound types → base v2 types
    "script_phase": "script",
    "asset_batch": "asset",
    "character": "asset",
    "scene": "asset",
    "shot": "storyboard",
    "audio_batch": "audio",
    "video_batch": "video",
    "reference_image": "reference",
    # Map "3d" is already valid, but handle uppercase variants
    "3D": "3d",
    "3d_model": "3d",
}

# Mapping from legacy node states to v2-valid states.
_NODE_STATE_MIGRATION_MAP: dict[str, str] = {
    "cached": "success",
    "completed": "success",
    "failed": "error",
    "awaiting_review": "pending",
    "awaiting_audit": "pending",
    "waiting": "pending",
    "done": "success",
}


def sanitize_v2_graph(graph: dict[str, Any]) -> dict[str, Any]:
    """Normalize all node/branch fields to Canvas API v2-valid values.

    The v2/save-v2 endpoint enforces a strict zod schema on node ``type``,
    node ``state``, and branch ``status``. When the subscriber loads an
    existing graph that contains legacy v1-era values (e.g.
    ``type="script_phase"``, ``state="cached"``), the save-v2 call fails
    with HTTP 400 and the **entire** graph — including the newly upserted
    node — is silently rejected (CANVAS-IN-HERMES-03 degrade-tolerant
    swallow-all).

    This function walks every node and branch in ``graph``, mapping known
    legacy values to their v2-valid equivalents and falling back to safe
    defaults for unrecognized values. It MUST be called after
    ``normalize_loaded_graph`` + ``upsert_node``/``ensure_link`` and
    BEFORE ``CanvasClient.save_canvas``.

    The graph is mutated in place and returned for chaining.

    Args:
        graph: FlowGraph dict with ``nodes`` and ``branches`` lists.

    Returns:
        The same ``graph`` dict with all fields v2-valid.
    """
    # ── Top-level Zod-required keys ──────────────────────────────────
    # FlowGraphV2Schema requires: meta (object), nodes (array),
    # links (array), branches (array), variantGroups (array).
    # All four array keys MUST exist or save-v2 returns HTTP 400.
    # NOTE: the key is "links", NOT "edges" — legacy code sometimes uses
    # "edges"; migrate it here.
    if "links" not in graph or not isinstance(graph.get("links"), list):
        edges = graph.get("edges")
        graph["links"] = edges if isinstance(edges, list) else []
        graph.pop("edges", None)
    elif not isinstance(graph["links"], list):
        graph["links"] = []
    if not isinstance(graph.get("nodes"), list):
        graph["nodes"] = []
    if not isinstance(graph.get("branches"), list):
        graph["branches"] = []
    if not isinstance(graph.get("variantGroups"), list):
        graph["variantGroups"] = []

    # ── meta block (FlowMetaV2Schema) ────────────────────────────────
    # Required: version="2", projectId:number, episodesId:number,
    # createdAt:number, updatedAt:number. save_canvas() stamps updatedAt
    # but the other four must be present before save-v2 accepts the graph.
    meta = graph.get("meta")
    if not isinstance(meta, dict):
        meta = {}
        graph["meta"] = meta
    now_ms = int(time.time() * 1000)
    # version must be exactly the literal "2" (z.literal("2")).
    if meta.get("version") != "2":
        meta["version"] = "2"
    # projectId / episodesId: coerce to int; if missing, fall back to
    # the client context if embedded in graph, else 0. (save_canvas's
    # _require_context already ensures these are set on the client, but
    # the graph meta itself must carry them too for the v2 schema.)
    if not isinstance(meta.get("projectId"), (int, float)):
        meta["projectId"] = meta.get("projectId") or 0
    if not isinstance(meta.get("episodesId"), (int, float)):
        meta["episodesId"] = meta.get("episodesId") or 0
    if not isinstance(meta.get("createdAt"), (int, float)):
        meta["createdAt"] = now_ms
    # updatedAt is also stamped by save_canvas(), but ensure it exists
    # here so the graph is valid even if save_canvas's stamp path is
    # somehow skipped (defense-in-depth).
    if not isinstance(meta.get("updatedAt"), (int, float)):
        meta["updatedAt"] = now_ms

    nodes = graph.get("nodes")
    if isinstance(nodes, list):
        for node in nodes:
            if not isinstance(node, dict):
                continue
            # ── node-level Zod-required fields (FlowNodeV2Schema) ──
            # Required: id, type, branchId, phaseIndex, phaseName,
            # position, size, state, data.
            if "branchId" not in node or not isinstance(node.get("branchId"), str):
                node["branchId"] = "main"
            if not isinstance(node.get("phaseIndex"), int):
                # phaseIndex defaults to 0 (schema: z.number().int().min(0))
                pi = node.get("phaseIndex")
                if isinstance(pi, (int, float)):
                    node["phaseIndex"] = int(pi)
                else:
                    node["phaseIndex"] = 0
            if not isinstance(node.get("phaseName"), str) or not node.get("phaseName"):
                node["phaseName"] = node.get("id", "phase")
            size = node.get("size")
            if not isinstance(size, dict):
                node["size"] = {"width": 240, "height": 200}
            else:
                if not isinstance(size.get("width"), (int, float)):
                    size["width"] = 240
                if not isinstance(size.get("height"), (int, float)):
                    size["height"] = 200
            pos = node.get("position")
            if not isinstance(pos, dict):
                node["position"] = {"x": 0, "y": 0}
            else:
                if not isinstance(pos.get("x"), (int, float)):
                    pos["x"] = 0
                if not isinstance(pos.get("y"), (int, float)):
                    pos["y"] = 0
            if not isinstance(node.get("data"), dict):
                node["data"] = {}

            # ── node.type ──
            ntype = node.get("type", "")
            if ntype not in _V2_VALID_NODE_TYPES:
                # Try legacy migration map first, then heuristic fallback.
                migrated = _NODE_TYPE_MIGRATION_MAP.get(ntype)
                if migrated is None:
                    # Heuristic: if type contains a known valid type as substring.
                    ntype_lower = str(ntype).lower()
                    for valid in _V2_VALID_NODE_TYPES:
                        if valid in ntype_lower:
                            migrated = valid
                            break
                if migrated is None:
                    # Last resort: infer from data.assetType or phaseName.
                    data = node.get("data", {})
                    if isinstance(data, dict):
                        asset_type = str(data.get("assetType", "")).lower()
                        if "scene" in asset_type or "character" in asset_type or "role" in asset_type:
                            migrated = "asset"
                        elif "storyboard" in asset_type or "shot" in asset_type:
                            migrated = "storyboard"
                        elif "video" in asset_type:
                            migrated = "video"
                        elif "audio" in asset_type or "voice" in asset_type:
                            migrated = "audio"
                        else:
                            migrated = "script"
                    else:
                        migrated = "script"
                node["type"] = migrated

            # ── node.state ──
            nstate = node.get("state", "")
            if nstate not in _V2_VALID_NODE_STATES:
                migrated_state = _NODE_STATE_MIGRATION_MAP.get(nstate, "idle")
                node["state"] = migrated_state

    branches = graph.get("branches")
    if isinstance(branches, list):
        _now_ms = int(time.time() * 1000)
        for branch in branches:
            if not isinstance(branch, dict):
                continue
            bstatus = branch.get("status", "")
            if bstatus not in _V2_VALID_BRANCH_STATUSES:
                branch["status"] = "active"
            # Zod requires: id, name, label, status, createdAt, updatedAt
            if not isinstance(branch.get("label"), str):
                branch["label"] = branch.get("name") or branch.get("id") or "Main"
            if not isinstance(branch.get("createdAt"), (int, float)):
                branch["createdAt"] = _now_ms
            if not isinstance(branch.get("updatedAt"), (int, float)):
                branch["updatedAt"] = _now_ms

    # Strip None-valued filePath/thumbnailUrl — canvas save-v2 rejects them
    # with HTTP 400. This is a defense-in-depth backstop; the source builders
    # also avoid writing None, but legacy graphs loaded from disk may carry
    # stale None entries.
    # Behavior: if the key is PRESENT with a None value, delete it (the
    # save-v2 schema marks these optional for script nodes — adding ""
    # pollutes the canvas detail panel with empty file rows). Don't add
    # the key when it's absent.
    # Also ensure ``label`` and ``description`` are always non-None strings:
    # the v2 canvasAssetSchema requires BOTH on script nodes (and asset nodes
    # require label) and rejects ``undefined``/``None``/empty with HTTP 400
    # ("script node requires description" / "asset node requires label"). We
    # backfill label from the node id / phaseName, then description from label.
    for node in (graph.get("nodes") or []):
        if isinstance(node, dict) and isinstance(node.get("data"), dict):
            _d = node["data"]
            for _k in ("filePath", "thumbnailUrl"):
                if _k in _d and _d[_k] is None:
                    del _d[_k]
            # Backfill label first (description depends on it).
            _lbl = _d.get("label")
            if not isinstance(_lbl, str) or _lbl == "":
                _lbl = str(node.get("phaseName") or node.get("id") or "node")
                _d["label"] = _lbl
            _desc = _d.get("description")
            if not isinstance(_desc, str) or _desc == "":
                _d["description"] = _lbl

            # ── Array-type field enforcement ──────────────────────────
            # Canvas save-v2 zod schemas require certain fields to be arrays
            # (e.g. ``views: z.array(z.string())``). When phase outputs
            # passthrough a dict/object for these fields (e.g. P07 scene_images
            # has ``views`` as a dict of angle→url), the save fails with
            # HTTP 400 ("期望数组，实际接收 object").
            #
            # We coerce: dict → list of its values; scalar → wrap in [scalar];
            # empty/None → delete the key entirely (most are .optional()).
            for _arr_key in ("views",):
                _av = _d.get(_arr_key)
                if _av is None:
                    _d.pop(_arr_key, None)
                elif isinstance(_av, list):
                    pass  # already array
                elif isinstance(_av, dict):
                    # dict → list of stringified values
                    _d[_arr_key] = [str(v) for v in _av.values()]
                else:
                    # scalar → wrap
                    _d[_arr_key] = [str(_av)]

            # ── String-type field coercion ────────────────────────────
            # Canvas zod schemas declare many fields as z.string(). When the
            # phase output passthrough delivers a number (e.g. scene_ref=1
            # instead of "S01") or other non-string, save-v2 rejects with
            # "期望 string，实际接收 数字". Coerce known string fields.
            for _str_key in ("shot_id", "scene_ref", "shot_type", "axis_line",
                              "camera_movement", "emotion", "ltx_prompt",
                              "video_prompt",
                              "engine", "resolution", "codec", "murch_grade",
                              "assetType", "scene_id", "style_vector",
                              "turnaround_path", "clip_type", "speaker"):
                _sv = _d.get(_str_key)
                if _sv is not None and not isinstance(_sv, str):
                    _d[_str_key] = str(_sv)

            # ── Number-type field coercion ────────────────────────────
            # Canvas zod schemas declare duration_sec as z.number().positive().
            # When passthrough delivers a string (e.g. "2.0"), coerce to float.
            for _num_key in ("duration_sec",):
                _nv = _d.get(_num_key)
                if _nv is not None and not isinstance(_nv, (int, float)):
                    try:
                        _d[_num_key] = float(_nv)
                    except (ValueError, TypeError):
                        _d.pop(_num_key, None)  # unparseable → drop

            # ── Storyboard node field defaults (A-1) ──────────────────
            # Storyboard (shot) nodes have required-ish fields that the
            # canvas v2 schema validates. When the phase output omits them
            # or delivers unparseable values, apply safe defaults instead
            # of letting save-v2 reject the entire graph with HTTP 400.
            _node_type = node.get("type", "")
            if _node_type == "storyboard":
                # duration_sec: null/missing/unparseable → 2.0 (float)
                _dv = _d.get("duration_sec")
                if _dv is None:
                    _d["duration_sec"] = 2.0
                elif not isinstance(_dv, (int, float)):
                    try:
                        _d["duration_sec"] = float(_dv)
                    except (ValueError, TypeError):
                        _d["duration_sec"] = 2.0
                # shot_type: null/missing → "medium"
                _st = _d.get("shot_type")
                if not _st or not isinstance(_st, str):
                    _d["shot_type"] = "medium"
                # scene_ref: number → str(number)
                _sr = _d.get("scene_ref")
                if isinstance(_sr, (int, float)) and not isinstance(_sr, bool):
                    _d["scene_ref"] = str(_sr)
                # shot_id: null/missing → label or f"shot-{index}"
                _si = _d.get("shot_id")
                if not _si or not isinstance(_si, str):
                    _idx_hint = _d.get("label") or ""
                    if _idx_hint:
                        _d["shot_id"] = str(_idx_hint)
                    else:
                        # Use the node's position in the list as a fallback index
                        _node_list = graph.get("nodes") or []
                        _sidx = 0
                        for _ni, _nn in enumerate(_node_list):
                            if _nn is node:
                                _sidx = _ni
                                break
                        _d["shot_id"] = f"shot-{_sidx}"

            # ── Audio/Video node field defaults (scan-fallback safety) ──
            # Same defensive principle as storyboard above. The canvas v2
            # schema requires shot_id/duration_sec (+engine; +resolution for
            # video) for media nodes. The filesystem-scan fallback in
            # canvas_sync._extract_artifacts builds audio/video nodes from a
            # bare filename — they carry filePath but NO shot_id/duration_sec/
            # engine. Left as-is, save-v2 rejects the ENTIRE graph with HTTP
            # 400 (see ep-xiaojianghu-demo1 p11_video_render failure), which
            # _try_canvas_sync re-raises, halting the episode. Apply safe
            # defaults for genuinely-missing values; structured nodes that
            # already carry real values are untouched (the number/string
            # coercion blocks above run first and leave valid values alone).
            elif _node_type in ("audio", "video"):
                # shot_id: missing → derive from label (filename stem)
                _si = _d.get("shot_id")
                if not _si or not isinstance(_si, str):
                    _lab = _d.get("label") or ""
                    _d["shot_id"] = str(_lab) if _lab else "unknown"
                # duration_sec: null/missing/unparseable → 2.0 (float)
                _dv = _d.get("duration_sec")
                if _dv is None:
                    _d["duration_sec"] = 2.0
                elif not isinstance(_dv, (int, float)):
                    try:
                        _d["duration_sec"] = float(_dv)
                    except (ValueError, TypeError):
                        _d["duration_sec"] = 2.0
                # engine: missing → "unknown"
                if not _d.get("engine"):
                    _d["engine"] = "unknown"
                # resolution: missing (video only) → "unknown"
                if _node_type == "video" and not _d.get("resolution"):
                    _d["resolution"] = "unknown"

    return graph


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
    # Ensure every branch has required Canvas API v2 fields (parentId, timestamps).
    now_ms = int(time.time() * 1000)
    for branch in graph["branches"]:
        if isinstance(branch, dict):
            branch.setdefault("parentId", "")
            branch.setdefault("createdAt", now_ms)
            branch.setdefault("updatedAt", now_ms)
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


# ─── Zone (phase ellipse) node management ──────────────────────────────

# Ordered list of V8.6 pipeline phases. Each entry: (prefix, label, phase_group).
ZONE_PHASES: list[tuple[str, str, str]] = [
    ("p01", "P01 · 选题+钩子", "research"),
    ("p02", "P02 · 大纲", "research"),
    ("p03", "P03 · 剧本+审计", "story"),
    # P03.5 86ke 戏剧事件打磨（micro-phase, 2026-08-15）— story lane, p03/p04 之间。
    ("p035", "P03.5 · 戏剧事件打磨", "story"),
    # ICA M2 (2026-08-25): P03.6 钩子再实例化 — story lane, p035/p04 之间。
    # C4b 派生失效协议：从锁定剧本再实例化 hook-spec。
    ("p036", "P03.6 · 钩子再实例化", "story"),
    ("p04", "P04 · 角色设计", "story"),
    ("p05", "P05 · 痛点发现", "story"),
    ("p06", "P06 · 运镜+终审", "production"),
    ("p07", "P07 · 视觉+风格化", "production"),
    ("p08", "P08 · 场景选择", "production"),
    ("p09", "P09 · 分镜拆解", "production"),
    ("p09b", "P09b · 分镜审计", "production"),
    ("p09c", "P09c · 分镜故事板", "production"),
    ("p10", "P10 · 语音", "post"),
    ("p10c", "P10c · 语音审计", "post"),
    ("p10b", "P10b · 快速预览", "post"),
    ("p11", "P11 · 视频渲染", "post"),
    ("p11a", "P11a · 预览片段", "post"),
    # P11a.5 预演音频+成片 (2026-08-24 a046d47; 2026-08-25 PRG-02 补 zone) —
    # post lane, p11a/p11b 之间的预演位(环境音床+混音+粗剪拼片)。
    ("p11a5", "P11a.5 · 预演音频+成片", "post"),
    ("p11b", "P11b · 最终渲染", "post"),
    # P11c 视频智能质检 (qwen-eye, 2026-08-15) — post lane, p11b/p12a 之间。
    ("p11c", "P11c · 视频质检", "post"),
    ("p12", "P12 · 合成", "post"),
    # P12 split (2026-08-09): p12a (timeline EDL) → p12b (audio synthesis),
    # replacing the monolithic p12 position in the zone lane.
    ("p12a", "P12a · 时间线合成", "post"),
    ("p12b", "P12b · 音频合成", "post"),
    ("p13", "P13 · 交付", "post"),
    ("p14", "P14 · 质量审计", "post"),
    # p15_feedback (cross-episode reflection) — previously absent, its nodes
    # fell to the end-of-canvas fallback position (caught by the registry↔
    # mapping consistency test).
    ("p15", "P15 · 跨集反思", "post"),
]

# Quick lookup: prefix → (label, phase_group).
_ZONE_LOOKUP: dict[str, tuple[str, str]] = {
    p[0]: (p[1], p[2]) for p in ZONE_PHASES
}

# X-spacing between consecutive zones (pixels).
_ZONE_X_STEP = 1200  # Each phase lane is one zone wide (must match V4_ZONE_WIDTH)
# Y-position for zone ellipse nodes (above children).
_ZONE_Y = -80


def compute_zone_position(phase_prefix: str) -> dict[str, int]:
    """Compute the canvas position for a zone (phase ellipse) node.

    Zones are laid out left-to-right based on phase order.

    Args:
        phase_prefix: 3-char phase prefix (e.g. ``"p01"``, ``"p04"``).

    Returns:
        ``{"x": int, "y": int}`` position dict.
    """
    for i, (prefix, _, _) in enumerate(ZONE_PHASES):
        if prefix == phase_prefix:
            return {"x": i * _ZONE_X_STEP, "y": _ZONE_Y}
    # Unknown prefix: place at end.
    return {"x": len(ZONE_PHASES) * _ZONE_X_STEP, "y": _ZONE_Y}


def ensure_zone_node(
    graph: dict[str, Any],
    phase_prefix: str,
) -> str:
    """Ensure a zone (phase ellipse) node exists in the graph.

    Creates the node if missing, updates label/phase if it exists.
    Returns the zone node id (== ``phase_prefix``).

    Args:
        graph: FlowGraph dict.
        phase_prefix: 3-char phase prefix (e.g. ``"p04"``).

    Returns:
        The zone node id.
    """
    label, phase_group = _ZONE_LOOKUP.get(
        phase_prefix, (phase_prefix, "production"),
    )
    position = compute_zone_position(phase_prefix)
    zone_data: dict[str, Any] = {
        "type": "zone",
        "position": position,
        "size": {"width": 1200, "height": 300},
        "state": "success",
        "branchId": "main",
        "phaseIndex": 0,
        "phaseName": label,
        "data": {
            "label": label,
            "phase": phase_group,
            "state": "success",
        },
    }
    upsert_node(graph, phase_prefix, zone_data)
    return phase_prefix


def ensure_zone_chain(graph: dict[str, Any]) -> dict[str, Any]:
    """Create sequential links between existing consecutive zones.

    Links p01→p02→p03→...→p13, but only for zones that already exist
    in the graph. Idempotent.

    Args:
        graph: FlowGraph dict.

    Returns:
        The (mutated) graph.
    """
    nodes = graph.get("nodes", [])
    existing_zone_ids = {
        n["id"] for n in nodes
        if isinstance(n, dict) and n.get("type") == "zone"
    }
    # Get ordered list of existing zones.
    ordered = [
        prefix for prefix, _, _
        in ZONE_PHASES if prefix in existing_zone_ids
    ]
    for i in range(len(ordered) - 1):
        src, tgt = ordered[i], ordered[i + 1]
        ensure_link(graph, f"zl-{src}-{tgt}", src, tgt)
    return graph


def ensure_zone_to_child(
    graph: dict[str, Any],
    zone_id: str,
    child_id: str,
) -> dict[str, Any]:
    """Link a zone → child node if no such link exists yet.

    This ensures every node under a zone has at least one incoming edge
    from its phase ellipse. Idempotent.

    Args:
        graph: FlowGraph dict.
        zone_id: Zone node id (e.g. ``"p04"``).
        child_id: Child node id.

    Returns:
        The (possibly mutated) graph.
    """
    link_id = f"zc-{zone_id}-{child_id}"
    return ensure_link(graph, link_id, zone_id, child_id)


# ─── Candidate / review node helpers ───────────────────────────────────


def add_candidate_node(
    graph: dict[str, Any],
    phase_id: str,
    candidate_id: str,
    label: str,
    *,
    selected: bool = False,
    description: str = "",
    thumbnail_url: str | None = None,
    file_path: str | None = None,
    position: dict[str, int] | None = None,
    extra_data: dict[str, Any] | None = None,
) -> str:
    """Add a candidate (multi-choice) artifact node to the graph.

    Candidates are visualized with a distinct state:
    - ``selected=True`` → ``reviewStatus="approved"``, tag ``"✅ 已选"``
    - ``selected=False`` → ``reviewStatus="rejected"``, tag ``"未选"``

    The node is linked to the zone for ``phase_id``.

    Args:
        graph: FlowGraph dict.
        phase_id: Phase identifier (e.g. ``"p02_outline"``).
        candidate_id: Unique candidate id within this phase.
        label: Display label.
        selected: Whether this candidate was chosen.
        description: Optional description.
        thumbnail_url: Optional thumbnail path.
        file_path: Optional file path.
        position: Optional position dict. If omitted, computed from phase.
        extra_data: Optional structured scalar fields (hook_type /
            visual_concept / …) merged into node data — the candidate
            payload's own fields, so the detail panel's raw-field section
            can render them instead of only the synthesized description
            (variant 节点无 NODE_SCHEMA，靠穿透字段呈现结构化信息).

    Returns:
        The candidate node id.
    """
    phase_prefix = _phase_prefix(phase_id)
    node_id = f"c-{phase_prefix}-{candidate_id}"
    if position is None:
        phase_group = _ZONE_LOOKUP.get(phase_prefix, ("", "production"))[1]
        phase_idx = next(
            (i for i, (p, _, _) in enumerate(ZONE_PHASES) if p == phase_prefix),
            len(ZONE_PHASES),
        )
        position = {
            "x": phase_idx * _ZONE_X_STEP + 150,
            "y": 150 + (hash(candidate_id) % 5) * 120,
        }
    tags = ["✅ 已选"] if selected else ["未选"]
    node_data: dict[str, Any] = {
        "type": "variant",
        "position": position,
        "size": {"width": 240, "height": 200},
        "state": "success" if selected else "idle",
        "branchId": "main",
        "phaseIndex": 0,
        "phaseName": phase_id,
        "data": {
            "label": label,
            "description": description,
            "state": "success" if selected else "idle",
            "tags": tags,
            "reviewStatus": "approved" if selected else "rejected",
            "phase": _ZONE_LOOKUP.get(phase_prefix, ("", "production"))[1],
        },
    }
    # Conditionally write thumbnailUrl/filePath — canvas save-v2 rejects
    # None-valued keys (HTTP 400).
    for _k, _v in (("thumbnailUrl", thumbnail_url), ("filePath", file_path)):
        if _v:
            node_data["data"][_k] = _v
    # Structured scalar passthrough (2026-08-18): merge candidate payload
    # fields into node data. Scalar-only guard (str/int/float/bool) —
    # nested dicts/lists would bloat the row and RawDataSection skips
    # objects anyway; the caller pre-flattens what matters into
    # description.
    if extra_data:
        for _k, _v in extra_data.items():
            if (
                isinstance(_v, (str, int, float, bool))
                and _v not in ("", None)
                and _k not in node_data["data"]
            ):
                node_data["data"][_k] = _v
    upsert_node(graph, node_id, node_data)
    # Link zone → candidate.
    if phase_prefix:
        zone_id = ensure_zone_node(graph, phase_prefix)
        ensure_zone_to_child(graph, zone_id, node_id)
    return node_id


# ─── V4 semantic layout (character/scene grouping) ─────────────────────

# Layout constants for the V4 semantic grid.
# Zone width in pixels (wide enough for 4 columns of 240px nodes + gaps).
V4_ZONE_WIDTH: int = 1200

# Maximum nodes per row before wrapping to the next row.
V4_MAX_NODES_PER_ROW: int = 4

# Column spacing (node width 240 + 80px gap).
V4_COL_SPACING: int = 300

# Row spacing (node height 260 + 30px gap).
V4_ROW_SPACING: int = 290

# Initial Y offset for the first row of artifacts under a zone.
V4_BASE_Y: int = 60


def compute_grouped_position(
    phase_prefix: str,
    group_index: int,
    item_index: int,
) -> dict[str, int]:
    """Compute a semantic-grid position for an artifact node.

    The V4 canvas groups artifacts by character/scene identity: artifacts
    sharing the same ``characterId`` (or ``sceneId``) are placed on the
    same row so the viewer can visually trace a character's evolution
    across phases.

    Layout grid:
    * X: ``phase_column * V4_ZONE_WIDTH`` (each phase gets a 1200px lane)
      + ``group_index * V4_COL_SPACING`` offset within the lane.
    * Y: ``V4_BASE_Y + row * V4_ROW_SPACING`` where ``row = group_index
      // V4_MAX_NODES_PER_ROW`` if groups are large, or ``row =
      item_index // V4_MAX_NODES_PER_ROW`` for sequential layout.

    This replaces the old ``hash(id) % 3`` random scatter with a
    deterministic, semantically meaningful grid.

    Args:
        phase_prefix: 3-char phase prefix (e.g. ``"p04"``).
        group_index: Zero-based group index within the phase (e.g.
            character 0 = laolin, character 1 = driver). Items in the
            same group share a row.
        item_index: Zero-based item index within the group (e.g.
            angle 0 = front, angle 1 = side_left). Items advance
            horizontally then wrap.

    Returns:
        ``{"x": int, "y": int}`` position dict.
    """
    phase_idx = next(
        (i for i, (p, _, _) in enumerate(ZONE_PHASES) if p == phase_prefix),
        len(ZONE_PHASES),
    )
    col = item_index % V4_MAX_NODES_PER_ROW
    row = item_index // V4_MAX_NODES_PER_ROW
    # Group offset: each group starts on a new row.
    group_row = group_index * 2  # 2 rows per group (main + overflow)
    x = phase_idx * V4_ZONE_WIDTH + col * V4_COL_SPACING + 100
    y = V4_BASE_Y + (group_row + row) * V4_ROW_SPACING
    return {"x": x, "y": y}


# ─── Character name normalization ──────────────────────────────────────

# Known character name aliases → canonical name.
# This maps variant spellings to a single canonical form so artifacts
# from different phases/sources that reference the same character are
# correctly grouped together on the canvas.
_CHARACTER_NAME_MAP: dict[str, str] = {
    # Example mappings (populated from actual project data):
    # "老林-1975": "老林",
    # "laolin_middle": "老林",
    # "laolin middle": "老林",
    # "driver": "司机",
}


def normalize_character_name(raw: str | None) -> str | None:
    """Normalize a character name to its canonical form.

    Applies a lookup table (``_CHARACTER_NAME_MAP``) and falls back to
    the raw name stripped of common suffixes/prefixes. Returns ``None``
    for ``None`` / empty input.

    The normalization is intentionally conservative: it only maps known
    aliases. Unknown names pass through unchanged so the system degrades
    gracefully for new projects with different characters.

    Args:
        raw: Raw character name (e.g. ``"老林-1975"``).

    Returns:
        Canonical name (e.g. ``"老林"``), or ``raw`` if no mapping.
    """
    if not raw:
        return None
    key = str(raw).strip().lower()
    if key in _CHARACTER_NAME_MAP:
        return _CHARACTER_NAME_MAP[key]
    return str(raw).strip()


def add_review_node(
    graph: dict[str, Any],
    phase_id: str,
    gate_id: str,
    decision: str,
    *,
    note: str = "",
) -> str:
    """Add a review/gate result node to the graph.

    Shows the review decision for a phase as a distinct node.

    Args:
        graph: FlowGraph dict.
        phase_id: Phase identifier.
        gate_id: Gate identifier.
        decision: ``"approve"`` / ``"reject"`` / ``"contest"``.
        note: Optional reviewer note.

    Returns:
        The review node id.
    """
    phase_prefix = _phase_prefix(phase_id)
    node_id = f"r-{gate_id}"
    label = f"✅ {gate_id}" if decision == "approve" else f"⛔ {gate_id}"
    description = f"Gate {gate_id}: {decision}"
    if note:
        description += f" — {note}"
    zone_pos = compute_zone_position(phase_prefix) if phase_prefix else {"x": 0, "y": 0}
    node_data: dict[str, Any] = {
        "type": "suggestion",
        "position": {"x": zone_pos["x"], "y": zone_pos["y"] - 100},
        "size": {"width": 200, "height": 80},
        "state": "success" if decision == "approve" else "error",
        "branchId": "main",
        "phaseIndex": 0,
        "phaseName": f"Gate: {gate_id}",
        "data": {
            "label": label,
            "description": description,
            "content": description,
            "tags": ["gate", decision],
            "state": "success" if decision == "approve" else "error",
            "reviewStatus": "approved" if decision == "approve" else "rejected",
            "gateId": gate_id,
        },
    }
    upsert_node(graph, node_id, node_data)
    return node_id
