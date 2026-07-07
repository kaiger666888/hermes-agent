# Phase 57: ENDPOINT-ROUTING - Context

**Gathered:** 2026-07-07
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase)

<domain>
## Phase Boundary

Fix the synthesis endpoint timeout that v11.0 SC#2 smoke test exposed. The z.ai coding-plan endpoint (`api.z.ai/api/coding/paas/v4`) has a 30s request timeout that causes synthesis (long-prompt call ~5K input + 2K output) to fail with 5x retry storm before falling back to `open.bigmodel.cn/api/anthropic`. Solution: route long-prompt calls to anthropic-compat endpoint natively, keep short-prompt calls on z.ai coding plan.

</domain>

<decisions>
## Implementation Decisions

### Locked

1. **Threshold-based routing**: prompts with `input_tokens >= 4096` route to anthropic-compat; below threshold stays on z.ai coding plan.
2. **Configurable threshold**: `auxiliary.endpoint_routing.token_threshold` in `cli-config.yaml` (default 4096).
3. **Endpoint config**: Two named endpoints in `~/.hermes/config.yaml`:
   - `auxiliary.endpoint_routing.short_prompt` → `glm` (resolves to zai coding plan via existing alias)
   - `auxiliary.endpoint_routing.long_prompt` → `zhipu-anthropic` (resolves to open.bigmodel.cn/api/anthropic)
4. **Token estimation**: use `len(messages_content) // 4` heuristic (no expensive tokenizer call per dispatch) — accurate enough at the 4K threshold.
5. **Affected tasks**: `round_table_opinion` synthesis (panelists stay on short), `memory_compaction`, `memory_comparator`. Panelist calls already short.

### Claude's Discretion

- Module structure: extend `agent/auxiliary_client.py::_resolve_task_provider_model` OR new helper `_select_endpoint_by_prompt_length`. Recommend latter (single-responsibility).
- Test fixtures: synthesize 3K-token + 6K-token mock prompts; verify routing decision.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- `agent/auxiliary_client.py::_resolve_task_provider_model` (line 4795) — current resolver, returns (provider, model, base_url, api_key, api_mode)
- `agent/auxiliary_client.py::call_llm` (line 5168) — entry point
- `~/.hermes/config.yaml` — already has `auxiliary.title_generation.provider: zhipu-anthropic` showing both endpoints coexist
- v11.0 smoke log shows fallback chain: z.ai → open.bigmodel.cn/api/anthropic succeeded after 5x retry

### Integration Points

- `agent/auxiliary_client.py` modification (endpoint selection logic + tests)
- `cli-config.yaml.example` documentation for `endpoint_routing` block
- `~/.hermes/config.yaml` operator-side config (local only, not in repo)

</code_context>

<specifics>
## Specific Ideas

The 1 SC (per ROADMAP §Phase 57):

- **SC#1:** `auxiliary_client.call_llm` auto-selects endpoint based on prompt token count. Threshold configurable, default 4096.
- **SC#2:** v11.0 SC#2 smoke test latency drops from 490s to <240s (no synthesis retry storm).
- **SC#3:** All v11.0 + v12.0 unit tests pass; no regressions.

</specifics>

<deferred>
## Deferred Ideas

- Per-task override (force long-prompt endpoint for specific task regardless of size) — not needed in v12.0, threshold-based is enough.
- Multiple endpoint candidates (round-robin / failover beyond 2 endpoints) — overkill for v12.0.
- Token-accurate tokenizer integration — heuristic is sufficient at 4K boundary.

</deferred>
