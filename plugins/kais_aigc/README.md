# kais_aigc plugin

**Phase 31 skeleton scaffold** for the kais-aigc-platform client surface. This
plugin registers 4 tools into the `kais_aigc` toolset; tool handlers are
degrade-style stubs returning `{"status": "not_implemented", ...}`. Phase 32
swaps in real HTTP clients (gold-team GPU cluster `:8002`, review-platform,
canvas HTTP API v2 `:10588`, jimeng-free-api `:5100`) without renegotiating the
tool schemas declared in `tools.py`.

## Exposed tools

- `kais_gold_team_submit` — submit a task to gold-team GPU cluster
- `kais_review_submit` — submit a review to review-platform
- `kais_canvas_sync` — sync asset to canvas via HTTP API v2
- `kais_jimeng_call` — invoke a jimeng-free-api subcommand

## Status

- **Phase 31 (this commit):** scaffolding only — manifest + `register(ctx)` +
  schemas + stub handlers. `kind: standalone` → opt-in via `plugins.enabled`.
- **Phase 32:** real HTTP client implementations land here.

See `PATTERNS.md` in the planning root for the full pattern mapping.
