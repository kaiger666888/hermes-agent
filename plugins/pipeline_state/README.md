# pipeline_state plugin

**Phase 31 skeleton scaffold** for the pipeline-state surface (checkpoint resume
+ AssetBus V3 typed slots). This plugin registers 4 tools into the
`pipeline_state` toolset; tool handlers are degrade-style stubs returning
`{"status": "not_implemented", ...}`. Phase 33 swaps in real
PipelineStateStore + AssetBus V3 + CreativeHistoryTracker implementations
without renegotiating the tool schemas declared in `tools.py`.

## Exposed tools

- `pipeline_checkpoint_save` — persist pipeline state for an episode (atomic JSONL)
- `pipeline_checkpoint_load` — load most-recent checkpoint for resume
- `asset_bus_read` — read from a typed asset bus V3 slot
- `asset_bus_write` — append to a typed asset bus V3 slot atomically

## Status

- **Phase 31 (this commit):** scaffolding only — manifest + `register(ctx)` +
  schemas + stub handlers. `kind: standalone` → opt-in via `plugins.enabled`.
- **Phase 33:** real PipelineStateStore + AssetBus V3 implementations land here.

See `PATTERNS.md` in the planning root for the full pattern mapping.
