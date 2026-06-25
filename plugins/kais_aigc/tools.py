"""kais_aigc tool schemas + dispatch handlers (Phase 32 implementation).

Schemas declare the public parameter shape; handlers dispatch to real HTTP
clients (gold_team / review_platform / canvas / jimeng) and return results
through ``tool_result`` or errors through ``tool_error``. The four clients
each implement their own degrade-first envelope (returned, never raised on
network/5xx), while 4xx errors raise typed client errors which the
``_kais_tool_error`` mapper converts to ``tool_error`` JSON.
"""

from __future__ import annotations

from typing import Any

from plugins.kais_aigc.canvas import CanvasClient, CanvasClientError
from plugins.kais_aigc.gold_team import GoldTeamClient, GoldTeamError
from plugins.kais_aigc.jimeng import JimengClient, JimengError
from plugins.kais_aigc.review_platform import ReviewClientError, ReviewPlatformClient
from tools.registry import tool_error, tool_result


# ---------------------------------------------------------------------------
# Client factory functions (read config from env; mirror _spotify_client)
# ---------------------------------------------------------------------------

def _gold_team_client() -> GoldTeamClient:
    """Build a GoldTeamClient from KAIS_GOLD_TEAM_URL / KAIS_GOLD_TEAM_API_KEY env."""
    return GoldTeamClient()


def _review_platform_client() -> ReviewPlatformClient:
    """Build a ReviewPlatformClient from KAIS_REVIEW_URL / JWT / CALLBACK env."""
    return ReviewPlatformClient()


def _canvas_client() -> CanvasClient:
    """Build a CanvasClient from KAIS_CANVAS_URL env."""
    return CanvasClient()


def _jimeng_client() -> JimengClient:
    """Build a JimengClient from KAIS_JIMENG_URL / KAIS_JIMENG_SESSION_ID env."""
    return JimengClient()


# ---------------------------------------------------------------------------
# Error mapper (mirror _spotify_tool_error)
# ---------------------------------------------------------------------------

_CLIENT_ERRORS = (GoldTeamError, ReviewClientError, CanvasClientError, JimengError)


def _kais_tool_error(client: str, exc: Exception) -> str:
    """Map a client exception to tool_error JSON.

    Typed client errors (4xx, unrecoverable) carry a ``status`` attribute and
    are surfaced verbatim. Unexpected exceptions are wrapped with the client
    name + type for diagnosis.
    """
    if isinstance(exc, _CLIENT_ERRORS):
        status = getattr(exc, "status", None) or 500
        return tool_error(str(exc), status_code=status)
    return tool_error(f"{client} tool failed: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Schemas (interface-first — only task_type enum expanded in Phase 32)
# ---------------------------------------------------------------------------

KAIS_GOLD_TEAM_SUBMIT_SCHEMA = {
    "name": "kais_gold_team_submit",
    "description": (
        "Submit a task to gold-team GPU cluster (:8002). Dispatches via "
        "GoldTeamClient with X-API-Key auth + optional synchronous polling."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "task_type": {
                "type": "string",
                "enum": [
                    "image_draw", "image_refine", "video_final", "wan_i2v",
                    "tts_zh", "tts_en", "tts_bilingual", "tts_generation",
                    "upscale", "face_restore",
                    "image_pulid", "controlnet_depth",
                    "image_to_3d", "image_to_3d_mv",
                    "image_composition", "video_generation", "seedance_video",
                ],
                "description": (
                    "GPU task type (17 types — gold-team task dispatch). "
                    "REQUIREMENTS GPU-DIRECT-01 lists 13 + Node.js ref adds 4 "
                    "(tts_generation / image_composition / video_generation / "
                    "seedance_video)."
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
        "Submit a review to review-platform. Dispatches via "
        "ReviewPlatformClient with JWT bearer auth + HMAC-SHA256 callback "
        "signature verification."
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
        "Sync asset to canvas via HTTP API v2 (:10588). Dispatches via "
        "CanvasClient.save_canvas_degraded — HTTP-only, degrade-tolerant "
        "(no sqlite direct write)."
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
        "Invoke jimeng-free-api (:5100) subcommand. Dispatches via JimengClient "
        "with session rotation + exponential backoff on 429."
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
# Handlers — real dispatch to Wave 1 clients (Phase 32)
# ---------------------------------------------------------------------------

def _handle_kais_gold_team_submit(args: dict, **kw) -> str:
    """Dispatch to GoldTeamClient.submit_task (+ optional wait_for_task)."""
    task_type = args.get("task_type")
    if not task_type:
        return tool_error("task_type is required")
    payload = args.get("payload") or {}
    wait = bool(args.get("wait", False))
    try:
        with _gold_team_client() as c:
            result = c.submit_task(task_type=task_type, params=payload)
            if wait and isinstance(result, dict) and result.get("task_id"):
                result = c.wait_for_task(result["task_id"])
        return tool_result(result)
    except Exception as exc:
        return _kais_tool_error("gold_team", exc)


def _handle_kais_review_submit(args: dict, **kw) -> str:
    """Dispatch to ReviewPlatformClient.submit_review."""
    asset_type = args.get("asset_type")
    asset_id = args.get("asset_id")
    if not asset_type or not asset_id:
        return tool_error("asset_type and asset_id are required")
    reviewer_role = args.get("reviewer_role")
    callback_url = args.get("callback_url")
    metadata: Any = {"reviewer_role": reviewer_role} if reviewer_role else None
    try:
        with _review_platform_client() as c:
            result = c.submit_review(
                type=asset_type,
                content_ref=asset_id,
                metadata=metadata,
                callback_url=callback_url,
            )
        return tool_result(result)
    except Exception as exc:
        return _kais_tool_error("review_platform", exc)


def _handle_kais_canvas_sync(args: dict, **kw) -> str:
    """Dispatch to CanvasClient.save_canvas_degraded (HTTP-only)."""
    node_id = args.get("node_id")
    node_type = args.get("node_type")
    if not node_id or not node_type:
        return tool_error("node_id and node_type are required")
    payload = args.get("payload") or {}
    graph = {"nodes": [{"id": node_id, "type": node_type, "data": payload}]}
    try:
        with _canvas_client() as c:
            result = c.save_canvas_degraded(graph)
        return tool_result(result)
    except Exception as exc:
        return _kais_tool_error("canvas", exc)


def _handle_kais_jimeng_call(args: dict, **kw) -> str:
    """Dispatch to JimengClient.call(subcommand, payload)."""
    subcommand = args.get("subcommand")
    if not subcommand:
        return tool_error("subcommand is required")
    payload = args.get("payload") or {}
    try:
        with _jimeng_client() as c:
            result = c.call(subcommand, payload.copy())
        return tool_result(result)
    except Exception as exc:
        return _kais_tool_error("jimeng", exc)
