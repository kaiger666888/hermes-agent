"""formula_library plugin — Phase 39-01 scaffold (FORM-01 + FORM-04 lookup half).

Registers 1 tool (``formula_lookup``) into the ``formula_library`` toolset.
Phase 39-01 ships the engine + Pydantic schema (FORM-01 + FORM-02); Plan 02
ships 10 seed formulas (FORM-03); Plan 03 wires SKILL.md Step 0
(FORM-04 SKILL half).

Mirrors the standalone multi-tool pattern established by
``plugins/review_gates/`` and ``plugins/pipeline_state/``:

- ``__init__.py`` exports ``register(ctx)`` — the plugin loader entry point.
- ``tools.py`` holds the schema dict + handler function.
- ``schema.py`` is the Pydantic v2 contract for ``library/*.json``.
- ``lookup.py`` is the ranking engine (Task 2 of this plan).
- ``plugin.yaml`` declares the manifest (kind: standalone → opt-in via
  ``plugins.enabled``).
"""

from __future__ import annotations

from plugins.formula_library.tools import (
    FORMULA_LOOKUP_SCHEMA,
    _handle_formula_lookup,
)

# (name, schema, handler, emoji) — Phase 39-01 ships the only tool; future
# plans may add formula_submit / formula_stats here without renegotiating
# the formula_lookup schema declared in tools.py.
_TOOLS = (
    ("formula_lookup", FORMULA_LOOKUP_SCHEMA, _handle_formula_lookup, "FL"),
)


def register(ctx) -> None:
    """Register all formula_library tools.

    Called once by the hermes-agent plugin loader when ``formula_library``
    appears in ``plugins.enabled`` (kind: standalone).
    """
    for name, schema, handler, emoji in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="formula_library",
            schema=schema,
            handler=handler,
            check_fn=None,
            emoji=emoji,
        )
