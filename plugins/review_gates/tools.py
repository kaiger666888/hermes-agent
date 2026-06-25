"""review_gates tool schemas + stub handlers (Phase 31 skeleton).

Schemas declare the *target* parameter shape Phase 34 will accept. Phase 34
only swaps handler bodies — no schema renegotiation. Handler stubs return a
degrade-style JSON envelope so ``register()`` succeeds at discovery time and
so Phase 34 executors can grep for ``"status": "not_implemented"`` to find
every stub they need to fill in.
"""

from __future__ import annotations

from tools.registry import tool_result


def _stub(plugin: str, tool: str, implementing_phase: str, args: dict) -> str:
    """Uniform degrade-style stub envelope for all review_gates tools."""
    return tool_result({
        "status": "not_implemented",
        "plugin": plugin,
        "tool": tool,
        "implementing_phase": implementing_phase,
        "args_received": args,
    })


# ---------------------------------------------------------------------------
# Schemas (interface-first — Phase 34 accepts this exact shape)
# ---------------------------------------------------------------------------

GATE_SUBMIT_SCHEMA = {
    "name": "gate_submit",
    "description": (
        "Submit a HIL review gate (blocking / webhook / polling modes). "
        "Phase 34 implements Gate lifecycle + delegate_task approval callback."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "gate_id":    {"type": "string", "description": "Gate identifier (one of the 8 V8.6 gates)."},
            "episode_id": {"type": "string", "description": "Episode the gate is submitted against."},
            "mode": {
                "type": "string",
                "enum": ["blocking", "webhook", "polling"],
                "description": "Gate resolution mode.",
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
        "Block until gate resolves (blocking mode) or poll until timeout. "
        "Phase 34 implements pause/resume + HMAC webhook callback."
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
        "Resolve a gate with approve / reject / contest decision. Phase 34 "
        "implements write-back to asset bus review-outcomes slot + rollback trigger."
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
        "role / mode. Phase 34 loads gate YAML config."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "episode_id": {
                "type": "string",
                "description": "Optional episode filter — restricts to gates applicable to this episode.",
            },
        },
        "required": [],
    },
}


# ---------------------------------------------------------------------------
# Handlers (stubs — Phase 34 fills in real gate state machine)
# ---------------------------------------------------------------------------

def _handle_gate_submit(args: dict, **kw) -> str:
    """Phase 31 skeleton stub — Phase 34 implements Gate lifecycle + delegate_task approval."""
    return _stub("review_gates", "gate_submit", "Phase 34", args)


def _handle_gate_wait(args: dict, **kw) -> str:
    """Phase 31 skeleton stub — Phase 34 implements pause/resume + HMAC webhook callback."""
    return _stub("review_gates", "gate_wait", "Phase 34", args)


def _handle_gate_resolve(args: dict, **kw) -> str:
    """Phase 31 skeleton stub — Phase 34 implements review-outcomes write-back + rollback."""
    return _stub("review_gates", "gate_resolve", "Phase 34", args)


def _handle_gates_list(args: dict, **kw) -> str:
    """Phase 31 skeleton stub — Phase 34 loads 8 V8.6 gate YAML config."""
    return _stub("review_gates", "gates_list", "Phase 34", args)
