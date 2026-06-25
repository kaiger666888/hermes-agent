"""pipeline_state tool schemas + stub handlers (Phase 31 skeleton).

Schemas declare the *target* parameter shape Phase 33 will accept. Phase 33
only swaps handler bodies — no schema renegotiation. Handler stubs return a
degrade-style JSON envelope so ``register()`` succeeds at discovery time and
so Phase 33 executors can grep for ``"status": "not_implemented"`` to find
every stub they need to fill in.
"""

from __future__ import annotations

from tools.registry import tool_result


def _stub(plugin: str, tool: str, implementing_phase: str, args: dict) -> str:
    """Uniform degrade-style stub envelope for all pipeline_state tools."""
    return tool_result({
        "status": "not_implemented",
        "plugin": plugin,
        "tool": tool,
        "implementing_phase": implementing_phase,
        "args_received": args,
    })


# ---------------------------------------------------------------------------
# Schemas (interface-first — Phase 33 accepts this exact shape)
# ---------------------------------------------------------------------------

PIPELINE_CHECKPOINT_SAVE_SCHEMA = {
    "name": "pipeline_checkpoint_save",
    "description": (
        "Persist pipeline state for episode (phase cursor + intermediate outputs). "
        "Phase 33 implements atomic JSONL write."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "episode_id": {"type": "string", "description": "Episode identifier the checkpoint belongs to."},
            "phase": {
                "type": "string",
                "description": "Current phase cursor being checkpointed.",
            },
            "payload": {
                "type": "object",
                "description": "Checkpoint payload (phase output + intermediate artifacts).",
            },
        },
        "required": ["episode_id", "phase"],
    },
}

PIPELINE_CHECKPOINT_LOAD_SCHEMA = {
    "name": "pipeline_checkpoint_load",
    "description": (
        "Load most recent checkpoint for episode (resume after interrupt). "
        "Phase 33 implements most-recent-wins lookup."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "episode_id": {"type": "string", "description": "Episode identifier to load the latest checkpoint for."},
        },
        "required": ["episode_id"],
    },
}

ASSET_BUS_READ_SCHEMA = {
    "name": "asset_bus_read",
    "description": (
        "Read from asset bus V3 typed slot (creative-history / failed-shots / "
        "finetune-dataset). Phase 33 implements slot routing + envelope unwrap."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "episode_id": {"type": "string", "description": "Episode identifier to read from."},
            "slot": {
                "type": "string",
                "enum": ["creative-history", "failed-shots", "finetune-dataset", "review-outcomes"],
                "description": "Typed asset bus slot to read.",
            },
        },
        "required": ["episode_id", "slot"],
    },
}

ASSET_BUS_WRITE_SCHEMA = {
    "name": "asset_bus_write",
    "description": (
        "Write to asset bus V3 typed slot with envelope + atomic JSONL append. "
        "Phase 33 implements atomic write (no half-writes)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "episode_id": {"type": "string", "description": "Episode identifier to write under."},
            "slot": {
                "type": "string",
                "enum": ["creative-history", "failed-shots", "finetune-dataset", "review-outcomes"],
                "description": "Typed asset bus slot to write to.",
            },
            "entry": {
                "type": "object",
                "description": "Envelope entry to append atomically.",
            },
        },
        "required": ["episode_id", "slot", "entry"],
    },
}


# ---------------------------------------------------------------------------
# Handlers (stubs — Phase 33 fills in real PipelineStateStore + AssetBus)
# ---------------------------------------------------------------------------

def _handle_pipeline_checkpoint_save(args: dict, **kw) -> str:
    """Phase 31 skeleton stub — Phase 33 implements PipelineStateStore atomic JSONL write."""
    return _stub("pipeline_state", "pipeline_checkpoint_save", "Phase 33", args)


def _handle_pipeline_checkpoint_load(args: dict, **kw) -> str:
    """Phase 31 skeleton stub — Phase 33 implements most-recent-wins checkpoint lookup."""
    return _stub("pipeline_state", "pipeline_checkpoint_load", "Phase 33", args)


def _handle_asset_bus_read(args: dict, **kw) -> str:
    """Phase 31 skeleton stub — Phase 33 implements AssetBus V3 slot routing."""
    return _stub("pipeline_state", "asset_bus_read", "Phase 33", args)


def _handle_asset_bus_write(args: dict, **kw) -> str:
    """Phase 31 skeleton stub — Phase 33 implements AssetBus V3 atomic append."""
    return _stub("pipeline_state", "asset_bus_write", "Phase 33", args)
