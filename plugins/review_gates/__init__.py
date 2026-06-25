"""review_gates plugin — Phase 31 skeleton scaffold.

Registers 4 tools (gate_submit / gate_wait / gate_resolve / gates_list) into
the ``review_gates`` toolset. Phase 31 ships **stub handlers** that return a
degrade-style JSON envelope (``status: not_implemented``). Phase 34 will swap
in the real HIL gate state machine + delegate_task approval callback + 8 V8.6
gate YAML config loader without renegotiating the tool schemas declared here.

Mirrors the standalone multi-tool pattern established by ``plugins/spotify/``:

- ``__init__.py`` exports ``register(ctx)`` — the plugin loader entry point.
- ``tools.py`` holds schema dicts + handler functions.
- ``plugin.yaml`` declares the manifest (kind: standalone → opt-in via
  ``plugins.enabled``).
"""

from __future__ import annotations

from plugins.review_gates.tools import (
    GATE_RESOLVE_SCHEMA,
    GATE_SUBMIT_SCHEMA,
    GATE_WAIT_SCHEMA,
    GATES_LIST_SCHEMA,
    _handle_gate_resolve,
    _handle_gate_submit,
    _handle_gate_wait,
    _handle_gates_list,
)

# (name, schema, handler, emoji) — Phase 34 swaps handler bodies, not this list.
_TOOLS = (
    ("gate_submit",  GATE_SUBMIT_SCHEMA,  _handle_gate_submit,  "GS"),
    ("gate_wait",    GATE_WAIT_SCHEMA,    _handle_gate_wait,    "GW"),
    ("gate_resolve", GATE_RESOLVE_SCHEMA, _handle_gate_resolve, "GR"),
    ("gates_list",   GATES_LIST_SCHEMA,   _handle_gates_list,   "GL"),
)


def register(ctx) -> None:
    """Register all review_gates tools. Called once by the hermes-agent plugin loader."""
    for name, schema, handler, emoji in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="review_gates",
            schema=schema,
            handler=handler,
            check_fn=None,
            emoji=emoji,
        )
