"""kais_aigc plugin — Phase 31 skeleton scaffold.

Registers 4 tools (kais_gold_team_submit / kais_review_submit / kais_canvas_sync /
kais_jimeng_call) into the ``kais_aigc`` toolset. Phase 31 ships **stub handlers**
that return a degrade-style JSON envelope (``status: not_implemented``). Phase 32
will swap in real HTTP clients (gold-team :8002, review-platform, canvas :10588,
jimeng-free-api :5100) without renegotiating the tool schemas declared here.

Mirrors the standalone multi-tool pattern established by ``plugins/spotify/``:

- ``__init__.py`` exports ``register(ctx)`` — the plugin loader entry point.
- ``tools.py`` holds schema dicts + handler functions.
- ``plugin.yaml`` declares the manifest (kind: standalone → opt-in via
  ``plugins.enabled``, will not auto-load into existing sessions during the
  v5.0 rollout).
"""

from __future__ import annotations

from plugins.kais_aigc.tools import (
    KAIS_CANVAS_SYNC_REGISTER_SCHEMA,
    KAIS_CANVAS_SYNC_SCHEMA,
    KAIS_GOLD_TEAM_SUBMIT_SCHEMA,
    KAIS_JIMENG_CALL_SCHEMA,
    KAIS_REVIEW_SUBMIT_SCHEMA,
    _handle_kais_canvas_sync,
    _handle_kais_canvas_sync_register,
    _handle_kais_gold_team_submit,
    _handle_kais_jimeng_call,
    _handle_kais_review_submit,
)

# (name, schema, handler, emoji) — Phase 32 swaps handler bodies, not this list.
# Phase 37-03 adds kais_canvas_sync_register for subscriber wiring.
_TOOLS = (
    ("kais_gold_team_submit", KAIS_GOLD_TEAM_SUBMIT_SCHEMA, _handle_kais_gold_team_submit, "GP"),
    ("kais_review_submit",   KAIS_REVIEW_SUBMIT_SCHEMA,   _handle_kais_review_submit,   "RV"),
    ("kais_canvas_sync",     KAIS_CANVAS_SYNC_SCHEMA,     _handle_kais_canvas_sync,     "CN"),
    ("kais_canvas_sync_register", KAIS_CANVAS_SYNC_REGISTER_SCHEMA, _handle_kais_canvas_sync_register, "CS"),
    ("kais_jimeng_call",     KAIS_JIMENG_CALL_SCHEMA,     _handle_kais_jimeng_call,     "JM"),
)


def register(ctx) -> None:
    """Register all kais_aigc tools. Called once by the hermes-agent plugin loader.

    check_fn=None because stubs are always "available" — Phase 32 may add an
    availability gate (e.g. KAIS_GOLD_TEAM_URL env presence) once real clients
    land.
    """
    for name, schema, handler, emoji in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="kais_aigc",
            schema=schema,
            handler=handler,
            check_fn=None,
            emoji=emoji,
        )
