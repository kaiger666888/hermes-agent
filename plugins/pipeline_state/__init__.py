"""pipeline_state plugin — Phase 31 skeleton scaffold.

Registers 4 tools (pipeline_checkpoint_save / pipeline_checkpoint_load /
asset_bus_read / asset_bus_write) into the ``pipeline_state`` toolset. Phase 31
ships **stub handlers** that return a degrade-style JSON envelope
(``status: not_implemented``). Phase 33 will swap in the real
PipelineStateStore + AssetBus V3 + CreativeHistoryTracker implementations
without renegotiating the tool schemas declared here.

Mirrors the standalone multi-tool pattern established by ``plugins/spotify/``:

- ``__init__.py`` exports ``register(ctx)`` — the plugin loader entry point.
- ``tools.py`` holds schema dicts + handler functions.
- ``plugin.yaml`` declares the manifest (kind: standalone → opt-in via
  ``plugins.enabled``).
"""

from __future__ import annotations

from plugins.pipeline_state.tools import (
    ASSET_BUS_READ_SCHEMA,
    ASSET_BUS_WRITE_SCHEMA,
    PIPELINE_CHECKPOINT_LOAD_SCHEMA,
    PIPELINE_CHECKPOINT_SAVE_SCHEMA,
    _handle_asset_bus_read,
    _handle_asset_bus_write,
    _handle_pipeline_checkpoint_load,
    _handle_pipeline_checkpoint_save,
)

# Phase 41-01 — re-export RecipeLibrary for plugin-level discovery.
# RecipeLibrary is a library class (NOT a tool handler); it's consumed by
# Phase 42's feedback_ingest.py and by operators via direct import
# (``from plugins.pipeline_state import RecipeLibrary``). The noqa suppresses
# the unused-import warning since this import exists purely for namespace
# visibility.
from plugins.pipeline_state.recipe_library import RecipeLibrary  # noqa: F401

# (name, schema, handler, emoji) — Phase 33 swaps handler bodies, not this list.
_TOOLS = (
    ("pipeline_checkpoint_save", PIPELINE_CHECKPOINT_SAVE_SCHEMA, _handle_pipeline_checkpoint_save, "CK"),
    ("pipeline_checkpoint_load", PIPELINE_CHECKPOINT_LOAD_SCHEMA, _handle_pipeline_checkpoint_load, "LD"),
    ("asset_bus_read",           ASSET_BUS_READ_SCHEMA,           _handle_asset_bus_read,           "BR"),
    ("asset_bus_write",          ASSET_BUS_WRITE_SCHEMA,          _handle_asset_bus_write,          "BW"),
)


def register(ctx) -> None:
    """Register all pipeline_state tools. Called once by the hermes-agent plugin loader."""
    for name, schema, handler, emoji in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="pipeline_state",
            schema=schema,
            handler=handler,
            check_fn=None,
            emoji=emoji,
        )
