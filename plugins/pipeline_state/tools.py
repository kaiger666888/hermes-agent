"""pipeline_state tool schemas + dispatch handlers (Phase 33 implementation).

Schemas declare the parameter shape Phase 33 accepts — Phase 31 locked the
contract, Phase 33 only swapped handler bodies (no schema renegotiation).

Dispatch mirrors Phase 32-05: each handler reads required args, constructs the
relevant Wave 1 module (PipelineStateStore / AssetBus) via a factory helper,
calls the right method, and wraps the result in ``tool_result`` / ``tool_error``.

Factory helpers use ``os.getcwd()`` as the workdir default — callers chdir to
the episode workdir before invoking the tool. Tests use ``monkeypatch.chdir``.
"""

from __future__ import annotations

import os

from plugins.pipeline_state.asset_bus import AssetBus, AssetBusError
from plugins.pipeline_state.store import PipelineStateStore
from tools.registry import tool_error, tool_result


# ---------------------------------------------------------------------------
# Factory helpers (mirror Phase 32-05 _gold_team_client() pattern)
# ---------------------------------------------------------------------------


def _state_store(workdir: str | None = None) -> PipelineStateStore:
    """Construct a PipelineStateStore over ``workdir`` (default: cwd).

    The factory is module-level so tests can ``monkeypatch.setattr`` it to
    inject a fake store without touching the real filesystem.
    """
    return PipelineStateStore(workdir or os.getcwd())


def _asset_bus(workdir: str | None = None) -> AssetBus:
    """Construct an AssetBus over ``workdir`` (default: cwd).

    The factory is module-level so tests can ``monkeypatch.setattr`` it to
    inject a fake bus without touching the real filesystem.
    """
    return AssetBus(workdir or os.getcwd())


# ---------------------------------------------------------------------------
# Schemas (interface-first — Phase 33 accepts this exact shape)
# ---------------------------------------------------------------------------

PIPELINE_CHECKPOINT_SAVE_SCHEMA = {
    "name": "pipeline_checkpoint_save",
    "description": (
        "Persist pipeline state for episode (phase cursor + intermediate outputs). "
        "Atomic write to .pipeline-state.json at workdir root."
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
        "Returns status=no_checkpoint when episode has no saved state."
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
        "finetune-dataset / review-outcomes). JSONL slot returns a list; "
        "JSON slots return the unwrapped payload."
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
        "Write to asset bus V3 typed slot with envelope + atomic write. "
        "JSONL slot (finetune-dataset) appends one line; JSON slots "
        "replace atomically with envelope wrap."
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
                "description": "Envelope entry to write/append atomically.",
            },
        },
        "required": ["episode_id", "slot", "entry"],
    },
}


# ---------------------------------------------------------------------------
# Handlers (Phase 33 implementation — dispatch to Wave 1 modules)
# ---------------------------------------------------------------------------


def _handle_pipeline_checkpoint_save(args: dict, **kw) -> str:
    """Persist a phase checkpoint via PipelineStateStore.save_checkpoint."""
    episode_id = args.get("episode_id")
    phase = args.get("phase")
    payload = args.get("payload") or {}

    if not episode_id or not phase:
        return tool_error("episode_id and phase are required")

    try:
        store = _state_store()
        store.save_checkpoint(episode_id, phase, payload)
        return tool_result({
            "status": "saved",
            "episode_id": episode_id,
            "phase": phase,
        })
    except Exception as exc:
        return tool_error(
            f"checkpoint_save failed: {type(exc).__name__}: {exc}"
        )


def _handle_pipeline_checkpoint_load(args: dict, **kw) -> str:
    """Load the most-recent checkpoint via PipelineStateStore.load_latest_checkpoint."""
    episode_id = args.get("episode_id")
    if not episode_id:
        return tool_error("episode_id is required")

    try:
        store = _state_store()
        checkpoint = store.load_latest_checkpoint(episode_id)
        if checkpoint is None:
            return tool_result({
                "status": "no_checkpoint",
                "episode_id": episode_id,
            })
        return tool_result({
            "status": "loaded",
            "episode_id": episode_id,
            "checkpoint": checkpoint,
        })
    except Exception as exc:
        return tool_error(
            f"checkpoint_load failed: {type(exc).__name__}: {exc}"
        )


def _handle_asset_bus_read(args: dict, **kw) -> str:
    """Read from an AssetBus slot, dispatching to read_lines for JSONL slots."""
    episode_id = args.get("episode_id")
    slot = args.get("slot")
    if not episode_id or not slot:
        return tool_error("episode_id and slot are required")

    try:
        bus = _asset_bus()
        if slot in AssetBus.JSONL_SLOTS:
            data = bus.read_lines(slot)
        else:
            data = bus.read(slot)
        return tool_result({
            "status": "read",
            "episode_id": episode_id,
            "slot": slot,
            "data": data,
        })
    except AssetBusError as exc:
        # Programmer error (unknown slot / format mismatch).
        return tool_error(str(exc))
    except Exception as exc:
        return tool_error(
            f"asset_bus_read failed: {type(exc).__name__}: {exc}"
        )


def _handle_asset_bus_write(args: dict, **kw) -> str:
    """Write/append to an AssetBus slot, dispatching to append_line for JSONL."""
    episode_id = args.get("episode_id")
    slot = args.get("slot")
    entry = args.get("entry")
    if not episode_id or not slot or entry is None:
        return tool_error("episode_id, slot, and entry are required")

    try:
        bus = _asset_bus()
        if slot in AssetBus.JSONL_SLOTS:
            path = bus.append_line(slot, entry)
        else:
            path = bus.write(slot, entry, envelope=True)
        return tool_result({
            "status": "written",
            "episode_id": episode_id,
            "slot": slot,
            "path": path,
        })
    except AssetBusError as exc:
        # Programmer error (unknown slot / format mismatch).
        return tool_error(str(exc))
    except Exception as exc:
        return tool_error(
            f"asset_bus_write failed: {type(exc).__name__}: {exc}"
        )
