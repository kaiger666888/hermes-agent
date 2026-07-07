# Phase 59: AUX-POOL-ISOLATION - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase)

<domain>
## Phase Boundary

Eliminate the "gateway burst exhausts keys for round table" failure mode by isolating auxiliary credential pool from main agent pool. Add per-key TPM tracking so `acquire_slot` can pick the freshest key.

**THROTTLE built the rate-limit gate (Phase 58); POOL gives that gate its own keys to gate.**

</domain>

<decisions>
## Implementation Decisions

### Locked

1. **Named pools** — `agent/credential_pool.py` extended to support multiple named pools. New pool name `auxiliary` (alongside existing default).
2. **Env vars** — `GLM_AUX_API_KEY_1..4` (fallback to `GLM_API_KEY` if unset). Operator can use same 4 keys for both pools initially; separate keys when scaling.
3. **Per-key TPM tracking** — sliding 60s window. Each key tracks: `tokens_this_minute`, `window_start`. Reset when window slides.
4. **Key selection** — `acquire_slot` picks the key with most remaining TPM. If all < `tpm_warning_threshold` (default 10%), brief sleep + retry.
5. **Throttle layer integration** — Phase 58's `acquire_slot(task)` calls into the `auxiliary` pool for `provider=glm` tasks. Main agent uses default pool.
6. **No config breaking change** — `GLM_API_KEY` (single key) still works for default pool. New env vars are additive.

### Claude's Discretion

- Module structure: extend `agent/credential_pool.py` OR new `agent/auxiliary_pool.py`. Recommend extend (single source of truth for credential logic).
- Pool name enum: hardcoded string `"auxiliary"` OR config-driven. Recommend hardcoded for v12.0.
- TPM window implementation: `time.monotonic()` + dict; OR `collections.deque` with timestamps. Recommend the former (simpler).

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- `agent/credential_pool.py` (Phase 52) — current single-pool implementation. Reference for `mark_exhausted` + `rotate` pattern.
- `agent/glm_throttle.py` (Phase 58 NEW) — calls into pool. Needs pool-name parameter.
- `agent/auxiliary_client.py` (Phase 52/57/58) — uses `auxiliary` pool when calling GLM.
- MEMORY.md `feedback-glm-overload-reduce-concurrency.md` — 4-key rotation context.

### Integration Points

- `agent/credential_pool.py` modification (named pools + per-key TPM)
- `agent/glm_throttle.py` modification (pool name parameter)
- `agent/auxiliary_client.py` modification (use auxiliary pool name)
- `cli-config.yaml.example` documentation

</code_context>

<specifics>
## Specific Ideas

3 SCs per ROADMAP §Phase 59:
1. `GLM_AUX_API_KEY_1..4` env vars (fallback to `GLM_API_KEY`); auxiliary calls never share main pool.
2. Per-key TPM in sliding 60s window; `acquire_slot` picks key with most remaining TPM.
3. Test verifies main pool exhaustion does NOT affect auxiliary calls.

</specifics>

<deferred>
## Deferred Ideas

- Per-key RPM tracking (separate from TPM) — TPM is the bigger ceiling for round tables.
- Failover to default pool when auxiliary pool exhausted — keep strict isolation.
- Configurable per-key TPM cap — hardcode at GLM 200K/key for v12.0.

</deferred>
