"""kais_aigc tool schemas + stub handlers (Phase 31 skeleton).

Schemas declare the *target* parameter shape Phase 32 will accept. Phase 32
only swaps handler bodies — no schema renegotiation. Handler stubs return a
degrade-style JSON envelope so ``register()`` succeeds at discovery time and
so Phase 32 executors can grep for ``"status": "not_implemented"`` to find
every stub they need to fill in.
"""

from __future__ import annotations

from tools.registry import tool_result


def _stub(plugin: str, tool: str, implementing_phase: str, args: dict) -> str:
    """Uniform degrade-style stub envelope for all kais_aigc tools."""
    return tool_result({
        "status": "not_implemented",
        "plugin": plugin,
        "tool": tool,
        "implementing_phase": implementing_phase,
        "args_received": args,
    })


# ---------------------------------------------------------------------------
# Schemas (interface-first — Phase 32 accepts this exact shape)
# ---------------------------------------------------------------------------

KAIS_GOLD_TEAM_SUBMIT_SCHEMA = {
    "name": "kais_gold_team_submit",
    "description": (
        "Submit a task to gold-team GPU cluster (:8002). Phase 32 implements "
        "X-API-Key auth + async polling + SSE."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "task_type": {
                "type": "string",
                "enum": ["image_draw", "video_final", "tts_zh", "upscale"],
                "description": (
                    "Task category. Phase 32 expands to the full 17-type enum "
                    "(image_draw / video_final / tts_zh / upscale shown as "
                    "representatives here)."
                ),
            },
            "payload": {
                "type": "object",
                "description": "Task-specific parameters forwarded to gold-team.",
            },
            "wait": {
                "type": "boolean",
                "default": False,
                "description": "If true, poll until completion before returning.",
            },
        },
        "required": ["task_type"],
    },
}

KAIS_REVIEW_SUBMIT_SCHEMA = {
    "name": "kais_review_submit",
    "description": (
        "Submit a review to review-platform. Phase 32 implements JWT bearer auth "
        "+ HMAC-SHA256 callback signature verification."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "asset_type": {"type": "string", "description": "Type of asset under review."},
            "asset_id":   {"type": "string", "description": "Identifier of the asset under review."},
            "reviewer_role": {"type": "string", "description": "Reviewer role (e.g. director / script / voice / shot / render / post / qc / release)."},
            "callback_url":  {"type": "string", "description": "Optional webhook URL for async review resolution."},
        },
        "required": ["asset_type", "asset_id"],
    },
}

KAIS_CANVAS_SYNC_SCHEMA = {
    "name": "kais_canvas_sync",
    "description": (
        "Sync asset to canvas via HTTP API v2 (:10588). Phase 32 implements "
        "saveGraph HTTP + degrade-tolerant fallback (no sqlite direct write)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "node_id":   {"type": "string", "description": "Canvas node id to sync."},
            "node_type": {"type": "string", "description": "Canvas node type (e.g. character / scene / script)."},
            "payload":   {"type": "object", "description": "Node payload to persist via saveGraph."},
        },
        "required": ["node_id", "node_type"],
    },
}

KAIS_JIMENG_CALL_SCHEMA = {
    "name": "kais_jimeng_call",
    "description": (
        "Invoke jimeng-free-api (:5100) subcommand. Phase 32 implements 6 "
        "subcommands + session rotation + exponential backoff."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "subcommand": {
                "type": "string",
                "enum": [
                    "text2image",
                    "image2image",
                    "multimodal2video",
                    "multiframe2video",
                    "frames2video",
                    "image_upscale",
                ],
                "description": "jimeng-free-api subcommand to dispatch.",
            },
            "payload": {
                "type": "object",
                "description": "Subcommand-specific parameters (prompt / image / frames etc.).",
            },
        },
        "required": ["subcommand"],
    },
}


# ---------------------------------------------------------------------------
# Handlers (stubs — Phase 32 fills in real HTTP clients)
# ---------------------------------------------------------------------------

def _handle_kais_gold_team_submit(args: dict, **kw) -> str:
    """Phase 31 skeleton stub — Phase 32 implements real gold-team :8002 client."""
    return _stub("kais_aigc", "kais_gold_team_submit", "Phase 32", args)


def _handle_kais_review_submit(args: dict, **kw) -> str:
    """Phase 31 skeleton stub — Phase 32 implements real review-platform client."""
    return _stub("kais_aigc", "kais_review_submit", "Phase 32", args)


def _handle_kais_canvas_sync(args: dict, **kw) -> str:
    """Phase 31 skeleton stub — Phase 32 implements real canvas :10588 client."""
    return _stub("kais_aigc", "kais_canvas_sync", "Phase 32", args)


def _handle_kais_jimeng_call(args: dict, **kw) -> str:
    """Phase 31 skeleton stub — Phase 32 implements real jimeng :5100 client."""
    return _stub("kais_aigc", "kais_jimeng_call", "Phase 32", args)
