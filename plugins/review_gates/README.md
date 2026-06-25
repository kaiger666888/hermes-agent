# review_gates plugin

**Phase 31 skeleton scaffold** for the HIL review gate framework. This plugin
registers 4 tools into the `review_gates` toolset; tool handlers are
degrade-style stubs returning `{"status": "not_implemented", ...}`. Phase 34
swaps in the real gate state machine (submit / wait / resolve), the
`delegate_task` approval callback, and the 8 V8.6 gate YAML config loader
without renegotiating the tool schemas declared in `tools.py`.

## Exposed tools

- `gate_submit` — submit a HIL review gate (blocking / webhook / polling)
- `gate_wait` — block until gate resolves or poll until timeout
- `gate_resolve` — resolve a gate with approve / reject / contest decision
- `gates_list` — list all configured gates (8 V8.6 gates) with phase / role / mode

## Status

- **Phase 31 (this commit):** scaffolding only — manifest + `register(ctx)` +
  schemas + stub handlers. `kind: standalone` → opt-in via `plugins.enabled`.
- **Phase 34:** real gate state machine + delegate_task approval callback land here.

See `PATTERNS.md` in the planning root for the full pattern mapping.
