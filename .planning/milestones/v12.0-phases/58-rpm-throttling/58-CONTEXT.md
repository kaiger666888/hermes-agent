# Phase 58: RPM-THROTTLING - Context

**Gathered:** 2026-07-07
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase)

<domain>
## Phase Boundary

Replace v11.0's hardcoded `asyncio.sleep(2.5)` "Strategy A" RPM pacing with proper rate-aware throttling. Two related mechanisms bundled:

1. **THROTTLE-01 — Per-Task RPM Token Bucket** (`agent/glm_throttle.py` NEW module): each auxiliary task name (`round_table_opinion`, `memory_compaction`, `fitness_judge`, `bias_canary_claim_check`, `memory_comparator`) gets its own refillable token bucket. Default 30 RPM/task — well under GLM single-key ceiling. `acquire_slot(task)` blocks until a slot is available.

2. **THROTTLE-02 — Per-Round-Table TPM Budget**: `round_table_open` accepts optional `token_budget` parameter (default 100K). After each `get_agent_opinion`, subtract actual input + output tokens. If remaining < 2× expected next call → emit `budget_warning`. If remaining < 1× expected → abort with `status: budget_exceeded`, persist partial state for resume. Receipt in `submit_round_table_result` includes `tokens_consumed` + `cost_usd_estimate`.

</domain>

<decisions>
## Implementation Decisions

### Locked

1. **NEW module `agent/glm_throttle.py`** — single responsibility for RPM throttling.
2. **Token bucket algorithm**: classic Leaky Bucket — capacity N tokens, refills 1 token every (60/RPM) seconds.
3. **Default RPM = 30/task** — well under GLM single-key RPM ceiling (typically 60 RPM/key × 4 keys = 240 RPM pool, but burst is the issue, not steady-state).
4. **Configurable per-task**: `auxiliary.{task}.rpm` in `cli-config.yaml` overrides default.
5. **Token budget default 100K** — covers 9 panelists × ~5K + synthesis 10K + 25K retry slack.
6. **Budget events persisted**: `budget_warning` + `budget_exceeded` written to state file `events` array.
7. **Receipt field**: `submit_round_table_result` response gets new `tokens_consumed: int` + `cost_usd_estimate: float` fields.
8. **Phase 57 endpoint routing integrates**: when call routes to anthropic-compat (long prompt), still goes through same throttle bucket (no per-endpoint bucket — keep simple).
9. **Driver script update**: `scripts/run_screenplay_step3_roundtable.py` removes the `asyncio.sleep(2.5)` + `asyncio.sleep(5.0)` v11.0 patch (Phase 53 RPM pacing); throttle handles pacing automatically.

### Claude's Discretion

- Throttle data structure: in-memory dict keyed by task name; lazy-init on first call.
- Block vs try-acquire: provide both APIs. `auxiliary_client.call_llm` uses blocking `acquire_slot`. `round_table_open` uses `try_acquire_slot` to fail-fast if no quota.
- Cost estimation: hardcode `glm-5.2` pricing at 0.5 CNY per 1M tokens (configurable later).
- Test strategy: deterministic time mocking (freezegun or monkeypatch `time.monotonic`).

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- `agent/auxiliary_client.py::call_llm` (Phase 57 wire-in point) — throttle acquire happens BEFORE endpoint routing decision.
- `agent/round_table_executor.py::acquire_round_or_reject` (Phase 52 INFRA-04 serial lock) — different concern (per-roundId async lock for serial execution); throttle is per-task RPM, orthogonal.
- `agent/round_table_state.py::{open_round_table, append_turn, submit_round_table_result}` (Phase 52) — `token_budget` parameter added to `open_round_table`; receipt extended.
- `scripts/run_screenplay_step3_roundtable.py:240` (v11.0 RPM pacing patch — Phase 53 `fix(53): add RPM pacing`) — to be removed.
- `agent/credential_pool.py` (Phase 52) — separate concern (key rotation); throttle is per-task, not per-key.

### Integration Points

- `agent/glm_throttle.py` (NEW)
- `agent/auxiliary_client.py` modification (1-line acquire_slot call)
- `agent/round_table_state.py` modification (token_budget param + events array)
- `agent/round_table_executor.py` modification (token tracking + budget enforcement)
- `scripts/run_screenplay_step3_roundtable.py` modification (remove hardcoded sleep, rely on throttle)
- `cli-config.yaml.example` documentation

</code_context>

<specifics>
## Specific Ideas

The 2 SCs (per ROADMAP §Phase 58):

- **SC#1:** `agent/glm_throttle.py` implements token bucket per task; `acquire_slot(task)` blocks until slot available. Configurable via `auxiliary.{task}.rpm`.
- **SC#2:** `round_table_open` accepts `token_budget`; events emitted; receipt includes tokens_consumed + cost_usd_estimate.
- **SC#3:** v11.0 SC#2 smoke runs without manual sleep + zero `RateLimitError`.

</specifics>

<deferred>
## Deferred Ideas

- Per-key RPM tracking (separate from per-task) — that's POOL-02 in Phase 59.
- Adaptive RPM (slow down on 429) — keep simple at fixed RPM in v12.0.
- Multi-bucket (e.g., one bucket per provider instead of per task) — overkill.
- Cost tracking with real GLM pricing API — hardcode for now, fetch later.

</deferred>
