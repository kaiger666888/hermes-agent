"""canvas_sync.py — Python port of Node.js ``lib/canvas-sync-hook.js``.

Phase 37 Plan 02 — the subscriber half of the canvas-sync migration.

Scope (D-37-03 split architecture):
  - ``canvas_graph.py`` (this plan's sibling module) holds the **pure**
    FlowGraph mutation logic — no I/O.
  - ``canvas_sync.py`` (this module) holds the **subscriber** — it does
    HTTP I/O via the Phase 32 ``CanvasClient`` (reused, not duplicated,
    per CF-37-01) and delegates graph mutation to ``canvas_graph``.

Trigger points:
  - ``on_phase_complete(episode_id, phase_id, result)`` — fires when the
    v5.0 runner finishes a phase (Phase 37-01 wires this into
    ``RunnerConfig.on_phase_complete``).
  - ``on_gate_resolved(episode_id, gate_id, decision, payload)`` — fires
    when a review gate is approved/rejected (Phase 37-01 wires this into
    ``runner_hooks.set_gate_resolved_hook``).

Degrade-tolerant contract (CANVAS-IN-HERMES-03):
  Every public method wraps its body in ``try/except Exception``. Canvas
  is observability tooling — pipeline correctness MUST NOT depend on
  canvas availability. The ``CanvasClient`` already returns degrade
  envelopes on connect/timeout/5xx; this layer adds defense-in-depth so
  even unforeseen bugs (KeyError, malformed graph) never crash the
  episode.

No Node.js runtime dependency (D-37-05): pure Python + httpx via
``CanvasClient``. No ``openclaw`` / ``Toonflow`` / sqlite references.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from plugins.kais_aigc import canvas_graph
from plugins.kais_aigc.canvas import CanvasClient

logger = logging.getLogger(__name__)


class CanvasSyncSubscriber:
    """Subscriber that mirrors pipeline progress to the kais-aigc canvas.

    Python port of Node.js ``createCanvasSync()`` (canvas-sync-hook.js).
    One instance per episode — instance state (``_prev_phase_id``) tracks
    the previous phase for link drawing (PATTERN 6).

    Public methods (``on_phase_complete``, ``on_gate_resolved``) are
    degrade-tolerant: they log a WARNING on any failure and return
    without raising.
    """

    def __init__(self, canvas: CanvasClient, agent_name: str = ""):
        """
        Args:
            canvas: Phase 32 ``CanvasClient`` configured with
                project_id + episodes_id. HTTP I/O is delegated to it
                (CF-37-01: reused, not duplicated).
            agent_name: Optional label prefix (mirrors Node.js agentName).
        """
        self._client = canvas
        self._agent_name = agent_name
        # Tracks the previous phase id so consecutive phase nodes get
        # linked. Per-instance → safe for concurrent episodes.
        self._prev_phase_id: Optional[str] = None

    # ─── public trigger handlers ───────────────────────

    def on_phase_complete(
        self,
        episode_id: str,
        phase_id: str,
        result: dict[str, Any],
    ) -> None:
        """Phase-completion handler.

        Loads the current canvas graph, upserts a node for ``phase_id``
        built from ``result``, draws a link from the previous phase
        (if any), and saves. Degrade-tolerant — never raises.

        Args:
            episode_id: Episode identifier (for logging).
            phase_id: Phase identifier (e.g. ``"p01_hook_topic"``).
            result: Phase result dict. Conventionally
                ``{summary, metrics, review, output_files, ...}`` but
                defensive ``.get`` is used throughout.
        """
        try:
            loaded = self._client.load_canvas()
            graph = canvas_graph.normalize_loaded_graph(
                loaded, self._client._project_id, self._client._episodes_id
            )

            node_data = self._build_phase_node(phase_id, result)
            canvas_graph.upsert_node(graph, f"n-{phase_id}", node_data)

            if self._prev_phase_id is not None:
                canvas_graph.ensure_link(
                    graph,
                    f"l-{self._prev_phase_id}-{phase_id}",
                    f"n-{self._prev_phase_id}",
                    f"n-{phase_id}",
                )

            self._client.save_canvas(graph)
            self._prev_phase_id = phase_id
        except Exception:  # noqa: BLE001 — CANVAS-IN-HERMES-03 swallow-all
            logger.warning(
                "canvas sync on_phase_complete degraded "
                "(episode=%s phase=%s)",
                episode_id,
                phase_id,
                exc_info=True,
            )

    def on_gate_resolved(
        self,
        episode_id: str,
        gate_id: str,
        decision: str,
        payload: dict[str, Any],
    ) -> None:
        """Gate-resolution handler.

        On ``decision == "approve"``: writes/updates a gate-resolution
        canvas node (``g-{gate_id}``) with ``reviewStatus=approved``.
        On reject/contest: marks the associated phase node as ``error``
        state so the canvas UI reflects the rejection.

        Degrade-tolerant — never raises.

        Args:
            episode_id: Episode identifier (for logging).
            gate_id: Gate identifier.
            decision: ``"approve"`` / ``"reject"`` / ``"contest"``.
            payload: Gate outcome payload. ``payload["phase_id"]`` (if
                present) identifies the phase node to mark on reject.
        """
        try:
            loaded = self._client.load_canvas()
            graph = canvas_graph.normalize_loaded_graph(
                loaded, self._client._project_id, self._client._episodes_id
            )

            if decision == "approve":
                node_data = self._build_gate_node(gate_id, payload, approved=True)
                canvas_graph.upsert_node(graph, f"g-{gate_id}", node_data)
            else:
                # reject / contest — mark the associated phase node error.
                phase_id = payload.get("phase_id") or gate_id
                canvas_graph.upsert_node(
                    graph,
                    f"n-{phase_id}",
                    {
                        "state": "error",
                        "data": {
                            "state": "error",
                            "tags": ["rejected"],
                        },
                    },
                )

            self._client.save_canvas(graph)
        except Exception:  # noqa: BLE001 — CANVAS-IN-HERMES-03 swallow-all
            logger.warning(
                "canvas sync on_gate_resolved degraded "
                "(gate=%s decision=%s)",
                gate_id,
                decision,
                exc_info=True,
            )

    # ─── private node builders ─────────────────────────

    def _build_phase_node(
        self,
        phase_id: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Translate ``phase_id`` + ``result`` into canvas ``node_data``.

        Port of Node.js ``onPhaseComplete`` node construction
        (canvas-sync-hook.js lines 225-281). Builds a rich description
        from ``result.summary`` + ``result.metrics`` + ``result.review``,
        computes a lane-layout position, and sets the node ``state``
        based on whether the phase is awaiting review.

        Args:
            phase_id: Phase identifier.
            result: Phase result dict (defensive ``.get``).

        Returns:
            ``node_data`` dict ready for ``canvas_graph.upsert_node``.
        """
        # Derive the phase dict the mapper expects. ``stage`` is inferred
        # from the phase_id prefix (e.g. "p01_topic" → "topic") — same
        # heuristic the Node.js path uses when the pipeline doesn't pass
        # an explicit stage.
        stage = _infer_stage(phase_id)
        stage_order = int(result.get("stage_order", result.get("stageOrder", 0)))
        review_flag = bool(result.get("review"))

        phase_dict = {
            "id": phase_id,
            "name": result.get("name") or phase_id,
            "stage": stage,
            "stage_order": stage_order,
            "review": review_flag,
            "output_files": result.get("output_files", result.get("outputFiles", [])),
        }
        mapped = canvas_graph.default_phase_mapper(phase_dict)
        phase_group = mapped["phase"] or "production"
        position = canvas_graph.compute_node_position(phase_group, stage_order)

        # Build rich description (Node.js onPhaseComplete lines 231-245).
        desc_parts: list[str] = []
        summary = result.get("summary") or {}
        if isinstance(summary, dict):
            if summary.get("description"):
                desc_parts.append(str(summary["description"]))
            if summary.get("selectedTopic"):
                desc_parts.append(f"选定: {summary['selectedTopic']}")
            if summary.get("score") is not None:
                desc_parts.append(f"评分: {summary['score']}")
            if summary.get("variantCount") is not None:
                desc_parts.append(f"{summary['variantCount']} 个变体")
        metrics = result.get("metrics") or {}
        if isinstance(metrics, dict):
            if metrics.get("duration"):
                desc_parts.append(f"耗时 {metrics['duration']}")
        review = result.get("review") or {}
        if isinstance(review, dict) and review.get("action") == "awaiting_review":
            desc_parts.append("⏳ 等待审核")

        description = "\n".join(desc_parts) or mapped["label"]

        awaiting = isinstance(review, dict) and review.get("action") == "awaiting_review"
        node_state = "pending" if awaiting else "success"

        # reviewStatus mirrors Node.js: pending if awaiting, else
        # 'approved' when the phase is review-gated, else undefined.
        if awaiting:
            review_status = "pending"
        elif review_flag:
            review_status = "approved"
        else:
            review_status = None

        score = (metrics or {}).get("score") if isinstance(metrics, dict) else None
        if score is None and isinstance(summary, dict):
            score = summary.get("score")

        node_data: dict[str, Any] = {
            "type": "script",
            "position": position,
            "size": {"width": 260, "height": 180},
            "state": node_state,
            "branchId": "main",
            "data": {
                "label": mapped["label"],
                "phase": phase_group,
                "description": description,
                "tags": mapped["tags"] or [],
                "filePath": mapped["filePath"],
                "score": score,
                "content": description,
                "state": node_state,
                "phaseName": phase_id,
            },
        }
        if review_status is not None:
            node_data["data"]["reviewStatus"] = review_status
        return node_data

    def _build_gate_node(
        self,
        gate_id: str,
        payload: dict[str, Any],
        approved: bool,
    ) -> dict[str, Any]:
        """Build a gate-resolution canvas node (``g-{gate_id}``).

        On approve the node carries ``reviewStatus=approved`` + a
        ``success`` state; the canvas UI renders it as a confirmed
        milestone.

        Args:
            gate_id: Gate identifier.
            payload: Gate outcome payload (may carry ``note`` / ``judge``).
            approved: True on approve, False otherwise.

        Returns:
            ``node_data`` dict for ``canvas_graph.upsert_node``.
        """
        note = payload.get("note", "")
        description = f"✅ Gate {gate_id} approved" if approved else f"⛔ Gate {gate_id} rejected"
        if note:
            description += f": {note}"
        return {
            "type": "gate",
            "state": "success" if approved else "error",
            "branchId": "main",
            "data": {
                "label": f"Gate: {gate_id}",
                "description": description,
                "content": description,
                "tags": ["gate", "approved" if approved else "rejected"],
                "state": "success" if approved else "error",
                "reviewStatus": "approved" if approved else "rejected",
                "gateId": gate_id,
                "category": "gate",
            },
        }


# ─── helpers ───────────────────────────────────────────────────────────


def _infer_stage(phase_id: str) -> str:
    """Best-effort stage inference from a phase id.

    The Node.js path receives an explicit ``stage`` field; the v5.0
    runner currently passes only ``phase_id``. This helper extracts the
    suffix after the first underscore (``"p01_hook_topic" → "hook_topic"``)
    so ``default_phase_mapper``'s prefix match still works. Falls back
    to the full id.
    """
    if "_" in phase_id:
        # Drop the leading p01_ / p02_ prefix, keep the rest.
        return phase_id.split("_", 1)[1]
    return phase_id


# ─── registration API ─────────────────────────────────────────────────


def register_canvas_sync(
    *,
    base_url: Optional[str],
    project_id: int,
    episodes_id: int,
    runner_config: Any,
    transport: Optional[httpx.BaseTransport] = None,
    agent_name: str = "",
) -> CanvasSyncSubscriber:
    """Construct client + subscriber and wire both trigger callbacks.

    Single registration call wires both trigger paths (PATTERN 7):
      1. ``runner_config.on_phase_complete`` ← subscriber handler
      2. ``runner_config.on_gate_resolved`` ← subscriber handler
      3. ``runner_hooks.set_gate_resolved_hook(...)`` ← same handler
         (module-level gate hook — D-37-07).

    Args:
        base_url: Canvas platform base URL. ``None`` falls back to
            ``KAIS_CANVAS_URL`` env var then ``CanvasClient.DEFAULT_BASE_URL``.
        project_id: Canvas project id.
        episodes_id: Canvas episodes id.
        runner_config: Object with settable ``on_phase_complete`` /
            ``on_gate_resolved`` attributes (duck-typed to avoid the
            circular import with the runner module).
        transport: Optional ``httpx.BaseTransport`` for test injection.
        agent_name: Optional label prefix.

    Returns:
        The constructed ``CanvasSyncSubscriber``. Callers should hold
        the reference (prevents GC of the callback target).
    """
    client = CanvasClient(
        base_url=base_url,
        project_id=project_id,
        episodes_id=episodes_id,
        transport=transport,
    )
    sub = CanvasSyncSubscriber(client, agent_name=agent_name)
    runner_config.on_phase_complete = sub.on_phase_complete
    runner_config.on_gate_resolved = sub.on_gate_resolved
    # Module-level gate hook (D-37-07). Imported lazily so this module
    # remains importable even when review_gates isn't installed.
    try:
        from plugins.review_gates import runner_hooks

        runner_hooks.set_gate_resolved_hook(sub.on_gate_resolved)
    except ImportError:
        logger.debug(
            "review_gates.runner_hooks not importable — "
            "gate-resolved hook not registered (canvas sync still wired "
            "for phase completion via runner_config)"
        )
    return sub
