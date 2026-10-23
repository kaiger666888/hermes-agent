"""review_gates tool schemas + dispatch handlers (Phase 34-04, Wave 2).

Phase 34-04 swaps the 4 Phase 31 stub handlers for real dispatch against the
Wave 1 modules:

* ``gate_submit``  -> ``runner_hooks.pause_for_review`` (Gate lifecycle submit
  + review-platform submission + ``awaiting_review`` state write).
* ``gate_wait``    -> thin guidance shim. Blocking inside a tool call is
  dangerous; the Phase 35 runner owns the wait/poll loop via
  ``runner_hooks.pause_for_review`` (blocking) / ``poll_until_terminal``
  (polling). This handler returns instructions instead of actually blocking.
* ``gate_resolve`` -> ``runner_hooks.resolve_direct`` (operator-side direct
  resolution; bypasses HMAC which is reserved for external callbacks via
  ``resume_from_callback``).
* ``gates_list``   -> reads ``GATE_REGISTRY`` (eager-loaded at import).

Schemas (the 4 ``*_SCHEMA`` dicts) are UNCHANGED — Phase 31 contract locked.
Only handler bodies were swapped, mirroring Phase 33-04's Wave 2 pattern.
"""

from __future__ import annotations

import logging
from typing import Any

from plugins.review_gates import runner_hooks
from plugins.review_gates.gate import GateError, GateMaxRetriesExceeded, GateMode
from plugins.review_gates.gate_config import (
    GATE_REGISTRY,
    GateConfigError,
    derive_gate_id,
)
from tools.registry import tool_error, tool_result

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schemas (interface — UNCHANGED from Phase 31. Phase 34 locked the contract.)
# ---------------------------------------------------------------------------

GATE_SUBMIT_SCHEMA = {
    "name": "gate_submit",
    "description": (
        "Submit a HIL review gate (blocking / webhook / polling modes). "
        "Delegates to runner_hooks.pause_for_review which builds the Gate "
        "from gates.yaml, submits to the review platform, and writes "
        "awaiting_review state."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "gate_id":    {"type": "string", "description": "Gate identifier (one of the 8 V8.6 gates)."},
            "episode_id": {"type": "string", "description": "Episode the gate is submitted against."},
            "mode": {
                "type": "string",
                "enum": ["blocking", "webhook", "polling"],
                "description": "Gate resolution mode (defaults to the gate's configured default_mode).",
            },
            "payload": {
                "type": "object",
                "description": "Gate submission payload (assets under review, reviewer context, etc.).",
            },
        },
        "required": ["gate_id", "episode_id"],
    },
}

GATE_WAIT_SCHEMA = {
    "name": "gate_wait",
    "description": (
        "Return guidance on how to wait on a gate. This handler does NOT "
        "actually block — blocking inside a tool call is dangerous. The "
        "Phase 35 runner owns the wait loop via runner_hooks."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "gate_id": {"type": "string", "description": "Gate identifier to wait on."},
            "timeout_sec": {
                "type": "integer",
                "default": 3600,
                "description": "Maximum seconds to wait before returning (polling mode).",
            },
        },
        "required": ["gate_id"],
    },
}

GATE_RESOLVE_SCHEMA = {
    "name": "gate_resolve",
    "description": (
        "Resolve a gate with approve / reject / contest decision. Direct "
        "operator-side resolution via runner_hooks.resolve_direct (bypasses "
        "HMAC, which is reserved for external callbacks). Writes the outcome "
        "to the asset bus review-outcomes slot and surfaces a rollback_to "
        "target on reject."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "gate_id": {"type": "string", "description": "Gate identifier being resolved."},
            "decision": {
                "type": "string",
                "enum": ["approve", "reject", "contest"],
                "description": "Resolution decision.",
            },
            "suggested_action": {
                "type": "string",
                "description": "For reject: target phase to roll back to.",
            },
        },
        "required": ["gate_id", "decision"],
    },
}

GATES_LIST_SCHEMA = {
    "name": "gates_list",
    "description": (
        "List all configured gates (8 V8.6 gates) with their phase / reviewer "
        "role / mode. Reads the eager-loaded GATE_REGISTRY."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "episode_id": {
                "type": "string",
                "description": "Optional episode filter — Phase 34 returns all 8 (filter is Phase 35 scope).",
            },
        },
        "required": [],
    },
}


# ---------------------------------------------------------------------------
# Handlers (Phase 34-04 — real dispatch)
# ---------------------------------------------------------------------------

_VALID_DECISIONS = frozenset({"approve", "reject", "contest"})


def _normalize_mode(mode: Any) -> GateMode | None:
    """Coerce a caller-supplied ``mode`` string into a ``GateMode`` (or None).

    ``None`` (the default) means "use the gate's configured default_mode".
    """
    if mode is None:
        return None
    if isinstance(mode, GateMode):
        return mode
    try:
        return GateMode(str(mode))
    except ValueError as exc:
        raise GateError(
            f"Invalid mode {mode!r} (expected blocking/webhook/polling)"
        ) from exc


# Legacy gate_id → phase_id map for backward compatibility with pre-Phase-8
# tool callers and tests. The canonical SSoT is now the derived form
# (derive_gate_id(phase_id) — e.g. "p01-gate"), but tool callers may still
# pass the historical raw gate_id. This map lets the tool API accept both
# forms without forcing every caller to migrate atomically with the
# gates.yaml schema refactor.
_LEGACY_GATE_ID_TO_PHASE_ID: dict[str, str] = {
    # 8 V8.6 gates (pre-Phase-8 raw gate_ids)
    "topic-gate": "p01_hook_topic",
    "outline-gate": "p02_outline",
    "script-gate": "p03_script_audit",
    # character-gate / scene-select-gate / shot-breakdown-gate were on phases
    # with GATE_ID=None after Phase 8 reconciliation — they no longer have
    # gates.yaml entries, so legacy lookups for them return None (correct).
    "render-gate": "p11_video_render",
    "delivery-gate": "p13_delivery",
    # 3 Phase 40 redline gates (Plan-01 detector names — kept as canonical
    # redline gate_ids since the DETECTOR_REGISTRY keys on them).
    "redline_emotion_desensitize": "p13_delivery_redline_emotion",
    "redline_no_cold_open": "p13_delivery_redline_no_cold_open",
    "redline_unfinished_ending": "p13_delivery_redline_unfinished",
}


def _resolve_gate_id_to_phase_id(gate_id: str) -> str | None:
    """Resolve a runtime gate_id to the gates.yaml phase_id key.

    Phase 8 / 08-01 (FIX-01): gates.yaml is keyed by phase_id, but the
    external tool API still exposes ``gate_id``. This helper bridges the
    two and accepts BOTH the new canonical derived form AND legacy raw
    gate_ids (for backward compatibility with tool callers / tests that
    cached old values from before the Phase 8 schema refactor).

    Args:
        gate_id: Any of the accepted forms (derived "p01-gate", legacy
            "topic-gate", or redline detector name "redline_*").

    Returns:
        phase_id key on match, else None.
    """
    if not isinstance(gate_id, str) or not gate_id:
        return None
    # 1. Legacy map first — exact-match lookup (fast path for old callers).
    legacy = _LEGACY_GATE_ID_TO_PHASE_ID.get(gate_id)
    if legacy is not None:
        return legacy
    # 2. Canonical derived form: scan registry and match derive_gate_id.
    registry = GATE_REGISTRY  # eager-loaded at module import
    for phase_key in registry.keys():
        try:
            if derive_gate_id(phase_key) == gate_id:
                # Prefer non-redline main entry (p13_delivery over sub-keys).
                if "_redline_" not in phase_key:
                    return phase_key
        except GateConfigError:
            continue
    # 3. Redline sub-keys fallback.
    for phase_key in registry.keys():
        try:
            if derive_gate_id(phase_key) == gate_id:
                return phase_key
        except GateConfigError:
            continue
    return None


def _handle_gate_submit(args: dict, **kw) -> str:
    """Dispatch gate_submit to runner_hooks.pause_for_review OR
    runner_hooks.auto_detect_and_resolve.

    Two dispatch paths (Plan 40-02 Task 3):

    * **V8.6 HIL path** (8 gates, preserved from Phase 34): builds the Gate
      from gates.yaml, submits to the review platform, writes
      ``awaiting_review`` state. The gate is left PENDING awaiting manual
      ``gate_resolve``. Returns ``status="submitted"``.
    * **Phase 40 redline auto-detect path** (3 gates, NEW): for gate_ids
      starting with ``redline_``, routes to
      ``runner_hooks.auto_detect_and_resolve`` which runs the Plan-01
      detector and auto-resolves with the detector's verdict. Returns
      ``status="auto_resolved"`` + ``decision`` + ``suggested_action``.

    On ``GateMaxRetriesExceeded`` either path marks the episode failed
    (PIPE-GUARD-01) and returns a tool_error envelope.
    """
    gate_id = args.get("gate_id")
    episode_id = args.get("episode_id")
    if not gate_id or not episode_id:
        return tool_error(
            "gate_submit requires 'gate_id' and 'episode_id'",
            received={"gate_id": gate_id, "episode_id": episode_id},
        )
    # Resolve gate_id → phase_id (Phase 8 / 08-01 schema is phase_id-keyed).
    phase_id = _resolve_gate_id_to_phase_id(gate_id)
    if phase_id is None:
        return tool_error(
            f"Unknown gate_id: {gate_id!r}",
            known=sorted(GATE_REGISTRY.keys()),
        )

    payload = args.get("payload") or {}

    # ── Phase 40 Plan 02: redline gates dispatch to auto-detect path ──
    # The 3 redline gates (R1/R3/R4) auto-resolve via DETECTOR_REGISTRY.
    # The 8 V8.6 gates keep their HIL pause_for_review path (unchanged).
    if runner_hooks.is_redline_gate(gate_id):
        try:
            outcome = runner_hooks.auto_detect_and_resolve(
                gate_id, episode_id, payload,
            )
        except GateMaxRetriesExceeded as exc:
            # PIPE-GUARD-01: same fail semantics as the V8.6 path.
            runner_hooks.mark_episode_failed(episode_id, gate_id, exc)
            return tool_error(
                str(exc),
                status="episode_failed",
                gate_id=gate_id,
                episode_id=episode_id,
            )
        except KeyError as exc:
            # T-40-05 mitigation: redline_X gate_id without a registered
            # detector. Fail loud — never silent auto-approve.
            return tool_error(
                str(exc),
                status="detector_missing",
                gate_id=gate_id,
                episode_id=episode_id,
            )
        return tool_result({
            "status": "auto_resolved",
            "gate_id": gate_id,
            "episode_id": episode_id,
            "decision": outcome.get("decision"),
            "suggested_action": outcome.get("suggested_action"),
            "rollback_to": outcome.get("rollback_to"),
            "attempt": outcome.get("attempt"),
            "resolved_at": outcome.get("resolved_at"),
        })

    # ── V8.6 HIL path (8 gates, Phase 34 behavior preserved) ──
    mode_arg = args.get("mode")
    try:
        mode = _normalize_mode(mode_arg)
    except GateError as exc:
        return tool_error(str(exc))

    try:
        result = runner_hooks.pause_for_review(
            gate_id, episode_id, payload, mode=mode,
        )
    except GateMaxRetriesExceeded as exc:
        # PIPE-GUARD-01: mark episode failed with the CONSISTENCY_BLOCKED
        # marker (carried by the exception from Plan 34-01), then surface a
        # tool_error envelope so the operator sees the failure.
        runner_hooks.mark_episode_failed(episode_id, gate_id, exc)
        return tool_error(
            str(exc),
            status="episode_failed",
            gate_id=gate_id,
            episode_id=episode_id,
        )
    except GateError as exc:
        return tool_error(str(exc))

    return tool_result({
        "status": "submitted",
        "gate_id": result.get("gate_id", gate_id),
        "episode_id": result.get("episode_id", episode_id),
        "review_id": result.get("review_id"),
        "attempt": result.get("attempt"),
        "submitted_at": result.get("submitted_at"),
        "gate_status": result.get("status"),
    })


def _handle_gate_wait(args: dict, **kw) -> str:
    """Return guidance on how to wait on a gate (does NOT block).

    Blocking inside a tool call is dangerous — a single tool handler thread
    cannot park indefinitely. The Phase 35 orchestration runner owns the
    wait loop via ``runner_hooks.pause_for_review`` (blocking mode parks the
    runner) or ``runner_hooks.poll_until_terminal`` (polling mode actively
    queries). Webhook mode is non-blocking: the runner persists
    awaiting_review state and resumes on HMAC callback.

    This handler returns the relevant instructions plus the gate's configured
    mode so the caller can route appropriately.
    """
    gate_id = args.get("gate_id")
    if not gate_id:
        return tool_error("gate_wait requires 'gate_id'", received=args)
    # Resolve gate_id → phase_id (Phase 8 / 08-01 schema is phase_id-keyed).
    phase_id = _resolve_gate_id_to_phase_id(gate_id)
    if phase_id is None:
        return tool_error(
            f"Unknown gate_id: {gate_id!r}",
            known=sorted(GATE_REGISTRY.keys()),
        )

    timeout_sec = args.get("timeout_sec", 3600)
    raw_entry = GATE_REGISTRY[phase_id]
    configured_mode = raw_entry.get("default_mode", "blocking")

    if configured_mode == "polling":
        instructions = (
            "Polling mode: call runner_hooks.poll_until_terminal("
            f"gate_id={gate_id!r}, timeout_sec={timeout_sec}) which "
            "actively queries the review platform until terminal."
        )
    elif configured_mode == "webhook":
        instructions = (
            "Webhook mode: gate_submit already wrote awaiting_review state. "
            "The runner persists state and exits; resume via HMAC callback "
            "to runner_hooks.resume_from_callback."
        )
    else:
        instructions = (
            "Blocking mode: the Phase 35 runner calls "
            "runner_hooks.pause_for_review which parks the runner until "
            "gate_resolve is invoked. To resolve now, call gate_resolve "
            f"with gate_id={gate_id!r} and a decision."
        )

    return tool_result({
        "status": "use_resume_from_callback" if configured_mode == "webhook"
        else "use_runner_loop",
        "gate_id": gate_id,
        "configured_mode": configured_mode,
        "timeout_sec": timeout_sec,
        "instructions": instructions,
    })


def _handle_gate_resolve(args: dict, **kw) -> str:
    """Dispatch gate_resolve to runner_hooks.resolve_direct.

    Direct operator-side resolution. Bypasses HMAC verification (which is
    reserved for external callbacks via ``resume_from_callback``) — the
    operator invoking this tool is already authenticated to hermes-agent.
    Writes the outcome to the asset bus review-outcomes slot (CF-04) and
    surfaces a ``rollback_to`` target on reject with suggested_action.
    """
    gate_id = args.get("gate_id")
    decision = args.get("decision")
    if not gate_id or not decision:
        return tool_error(
            "gate_resolve requires 'gate_id' and 'decision'",
            received={"gate_id": gate_id, "decision": decision},
        )
    # Resolve gate_id → phase_id (Phase 8 / 08-01 schema is phase_id-keyed).
    phase_id = _resolve_gate_id_to_phase_id(gate_id)
    if phase_id is None:
        return tool_error(
            f"Unknown gate_id: {gate_id!r}",
            known=sorted(GATE_REGISTRY.keys()),
        )
    if decision not in _VALID_DECISIONS:
        return tool_error(
            f"Invalid decision {decision!r} (expected approve/reject/contest)",
        )

    suggested_action = args.get("suggested_action")
    try:
        outcome = runner_hooks.resolve_direct(
            gate_id, decision, suggested_action,
        )
    except (GateError, KeyError) as exc:
        # GateError: no pending gate / bad state. KeyError: gate_id not in
        # the in-process _PENDING_GATES cache (Phase 35 will rebuild from
        # state; for direct operator flow the gate must have been submitted
        # earlier in the same process).
        return tool_error(str(exc))

    return tool_result({
        "status": "resolved",
        "gate_id": outcome.get("gate_id", gate_id),
        "decision": outcome.get("decision", decision),
        "suggested_action": outcome.get("suggested_action"),
        "rollback_to": outcome.get("rollback_to"),
        "attempt": outcome.get("attempt"),
        "resolved_at": outcome.get("resolved_at"),
    })


def _handle_gates_list(args: dict, **kw) -> str:
    """List all 8 configured gates from the eager-loaded GATE_REGISTRY.

    The optional ``episode_id`` filter is Phase 35 scope — Phase 34 returns
    all 8 gates (V8.6 gate applicability is per-phase, not per-episode).
    """
    # ``episode_id`` accepted per schema but not filtered in Phase 34.
    gates = [
        {
            "gate_id": derive_gate_id(phase_key),
            "phase": entry["phase"],
            "phase_id": phase_key,  # explicit phase_id echo for diagnostic clarity
            "reviewer_role": (
                ", ".join(entry["reviewer_role"])
                if isinstance(entry["reviewer_role"], list)
                else entry["reviewer_role"]
            ),
            "default_mode": entry["default_mode"],
            "timeout_sec": entry["timeout_sec"],
            "asset_bus_slots_to_lock": list(entry["asset_bus_slots_to_lock"]),
            "retry_policy": dict(entry["retry_policy"]),
        }
        for phase_key, entry in GATE_REGISTRY.items()
    ]
    return tool_result({"gates": gates, "count": len(gates)})
