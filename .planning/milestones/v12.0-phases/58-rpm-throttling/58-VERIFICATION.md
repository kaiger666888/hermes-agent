---
phase: 58-rpm-throttling
verified: 2026-07-08T00:35:00Z
status: passed
score: 3/3 must-haves verified
overrides_applied: 0
---

# Phase 58: RPM-THROTTLING Verification Report

**Phase Goal:** Replace v11.0's hardcoded `asyncio.sleep` "Strategy A" RPM pacing with proper rate-aware throttling (per-task RPM token bucket + per-round-table TPM budget).
**Verified:** 2026-07-08T00:35:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `agent/glm_throttle.py` implements token bucket per task; `acquire_slot` blocks | ✓ VERIFIED | `agent/glm_throttle.py:60` `DEFAULT_RPM=30`; `:64` `class TokenBucket` with `capacity`/`refill_interval_seconds`/`available`/`last_refill_time` + `refill()`/`try_acquire()`; `:181` `acquire_slot(task)` blocking; `:210` `try_acquire_slot(task)` non-blocking; `:114` `_BUCKETS` registry; `:159` lazy `_get_or_create_bucket`; `:223` `reset_for_testing`. Behavioral spot-check: `acquire_slot('test_task')` returns immediately on fresh bucket, per-task isolation confirmed. 9 TDD tests in `tests/agent/test_glm_throttle.py` (312 lines) all GREEN. |
| 2 | `round_table_open` accepts `token_budget`; `budget_warning` + `budget_exceeded` events emitted | ✓ VERIFIED | `agent/round_table_state.py:302` `def open_round_table(..., token_budget: int \| None = None, ...)`; `:310` keyword arg; `:394-397` state file fields `tokenBudget`/`tokensConsumed`/`events`; `:101` `DEFAULT_TOKEN_BUDGET = 100_000`; `:469` `record_token_usage` (atomic); `:510` `append_event`; `:597-601` cost formula `costUsdEstimate = round((consumed/1M) * 0.5 / 7.2, 6)`. `agent/round_table_executor.py:213` `check_budget_before_turn` + `:277` `record_panelist_tokens`. Behavioral spot-checks: warning fires at `<2× expected`, exceeded returns False + emits event at `<1×`, ample budget returns True with empty events. Receipt cost formula verified (12000 tokens → 0.000833 USD). 28 budget tests GREEN. |
| 3 | v11.0 SC#2 smoke runs without manual sleep + zero `RateLimitError` (real-GLM deferred to Phase 61) | ✓ VERIFIED | `grep -c "^\s*await\s+asyncio\.sleep" scripts/run_screenplay_step3_roundtable.py` returns **0** executable sleep calls — only docstring/comment mentions (lines 54-55, 291). `asyncio.sleep(2.5)` + `asyncio.sleep(5.0)` hardcoded blocks removed. Mocked e2e pipeline test (`tests/agent/test_round_table_budget.py::TestPhase58FullThrottlePipeline`) exercises the full driver, asserts zero `asyncio.sleep` AST calls, zero `RateLimitError`, and verifies token/cost accounting end-to-end. Real-GLM 10× acquire_slot smoke is correctly deferred to Phase 61 VALIDATE SC#2 (production-smoke-report.md). |

**Score:** 3/3 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `agent/glm_throttle.py` | TokenBucket + acquire_slot/try_acquire_slot + get_last_call_usage | ✓ VERIFIED | 230 lines, all exports present (DEFAULT_RPM, TokenBucket, acquire_slot, try_acquire_slot, reset_for_testing), ruff clean. `get_last_call_usage` lives in `agent/auxiliary_client.py:5002` (correct location per plan — single-writer there). |
| `tests/agent/test_glm_throttle.py` | TDD coverage, ≥150 lines | ✓ VERIFIED | 312 lines, 9 test classes/methods covering capacity, refill, per-task isolation, config override, lazy init, blocking behavior, RPM edge case. |
| `agent/round_table_state.py` | token_budget param + events + helpers + receipt | ✓ VERIFIED | `open_round_table` extended; `record_token_usage`, `append_event` added; `submit_round_table_result` extended with `tokensConsumed` + `costUsdEstimate` top-level fields; constants `DEFAULT_TOKEN_BUDGET`, `GLM_5_2_CNY_PER_1M_TOKENS`, `USD_CNY_RATE` declared. |
| `agent/round_table_executor.py` | check_budget_before_turn + record_panelist_tokens | ✓ VERIFIED | `:203` `DEFAULT_EXPECTED_NEXT_TOKENS=5000`; `:213` `check_budget_before_turn`; `:277` `record_panelist_tokens` delegating to `_rts.record_token_usage`. |
| `agent/auxiliary_client.py` | acquire_slot wire-in + _LAST_CALL_USAGE tracker + get_last_call_usage export | ✓ VERIFIED | `:4995` module-level `_LAST_CALL_USAGE`; `:5002` `get_last_call_usage()` returns copy; `:5044-5046` usage capture helper; `:5397-5398` `acquire_slot(task)` lazy import inside `call_llm` BEFORE Phase 57 routing block at `:5407` — wiring order verified by code reading. |
| `scripts/run_screenplay_step3_roundtable.py` | asyncio.sleep(2.5) + (5.0) removed; throttle handles pacing; record_panelist_tokens/check_budget_before_turn wired | ✓ VERIFIED | Zero executable `await asyncio.sleep` in source (AST-walked by e2e test). `:85-87` imports budget helpers; `:215` `check_budget_before_turn` before each panelist; `:255-258` `record_panelist_tokens` after each panelist using `get_last_call_usage`; `:302` budget check before synthesis (`expected_next_tokens=15_000`); `:323-326` synthesis token recording. |
| `tests/agent/test_round_table_budget.py` | TDD coverage ≥200 lines | ✓ VERIFIED | 848 lines, 37 tests across 13 test classes (open/record/append/concurrency/receipt/abort/idempotence/constants/check/record_panelist/driver-wiring/full-pipeline). |
| `cli-config.yaml.example` | auxiliary.{task}.rpm + cost_estimate docs | ✓ VERIFIED | `:561-575` Phase 58 THROTTLE-01 rpm block (commented examples for round_table_opinion/memory_compaction/fitness_judge); `:577-586` Phase 58 THROTTLE-02 cost_estimate block (formula + GLM-5.2 pricing + USD rate). |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `auxiliary_client.call_llm` | `glm_throttle.acquire_slot` | sync call before endpoint routing | ✓ WIRED | `agent/auxiliary_client.py:5397-5398`. Lazy import inside function body (avoids circular import — `glm_throttle` lazy-imports `_get_auxiliary_task_config` from this module). Verified placement: acquire runs at `:5398`, Phase 57 routing runs at `:5407` — acquire is upstream. |
| `glm_throttle._get_or_create_bucket` | `auxiliary_client._get_auxiliary_task_config` | config lookup `auxiliary.{task}.rpm` | ✓ WIRED | `agent/glm_throttle.py:114-117` reads `auxiliary.{task}.rpm` via lazy import inside helper. Per-task override confirmed via Test 5 (`test_config_override_via_auxiliary_task_rpm`). |
| `scripts/run_screenplay_step3_roundtable.py` | `round_table_executor.record_panelist_tokens` | function call after each get_agent_opinion return | ✓ WIRED | `scripts/run_screenplay_step3_roundtable.py:85-87` import + `:258` invocation `_usage.get("total_tokens", 0)` → `record_panelist_tokens(_state_path, _tokens)`. |
| `round_table_executor.record_panelist_tokens` | `round_table_state.record_token_usage` | atomic state update | ✓ WIRED | `agent/round_table_executor.py:277-287` delegates to `_rts.record_token_usage(state_path, tokens)`. |
| `round_table_state.submit_round_table_result` | cost calculation via `tokensConsumed + GLM_5_2_CNY_PER_1M + USD_RATE` | inline computation | ✓ WIRED | `agent/round_table_state.py:597-601` computes `cost_cny = (consumed/1M) * 0.5`, `cost_usd = cost_cny / 7.2`, writes both `tokensConsumed` and `costUsdEstimate` at state top level. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `auxiliary_client._LAST_CALL_USAGE` | `prompt_tokens`/`completion_tokens`/`total_tokens` | `response.usage` from `client.chat.completions.create` (real GLM HTTP response) | ✓ FLOWING | Populated at every return path in `call_llm` via `_capture_usage(response)` helper (`:5044-5046`). Graceful zero fallback when `.usage` absent. |
| `round_table_state.tokensConsumed` | running sum | `record_token_usage` adds `tokens` from `auxiliary_client.get_last_call_usage()` | ✓ FLOWING | Driver script `:255` reads `get_last_call_usage()`, `:258` records into state. Atomic via `utils.atomic_json_write`. |
| `round_table_state.costUsdEstimate` | float cost | Computed from `tokensConsumed` via hardcoded GLM-5.2 pricing | ✓ FLOWING | `:597-601` formula `(consumed/1M) * 0.5 / 7.2`. Behavioral check: 12000 tokens → 0.000833 USD matches expected formula. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `acquire_slot` immediate on fresh bucket | `python -c "import agent.glm_throttle as gt; gt.reset_for_testing(); gt.acquire_slot('test_task')"` | exits 0, no blocking | ✓ PASS |
| Receipt cost formula correctness | `python -c "...open, record 12000, submit, print costUsdEstimate..."` | `0.000833` (matches `(12000/1M)*0.5/7.2`) | ✓ PASS |
| `check_budget_before_turn` exceeded path | python script: budget=6000, consumed=2000, expected_next=5000 → returns False + emits budget_exceeded event | `False`, events=`['budget_exceeded']` | ✓ PASS |
| `check_budget_before_turn` warning path | budget=20000, consumed=12000, expected_next=5000 → returns True + emits budget_warning | `True`, events=`['budget_warning']` | ✓ PASS |
| `check_budget_before_turn` clean path | budget=100000, consumed=5000, expected_next=5000 → returns True, empty events | `True`, events=`[]` | ✓ PASS |
| Phase 58 test suite GREEN | `pytest tests/agent/test_glm_throttle.py tests/agent/test_round_table_budget.py -q` | `37 passed, 1 warning in 2.07s` | ✓ PASS |
| Cross-phase regression (Phase 52/57) | `pytest tests/agent/test_auxiliary_endpoint_routing.py tests/agent/test_round_table_state.py tests/agent/test_round_table_executor.py tests/agent/test_auxiliary_client.py -q` | `264 passed, 1 warning in 11.94s` | ✓ PASS |
| Ruff clean | `ruff check <all 7 phase-58 files>` | `All checks passed!` | ✓ PASS |
| Zero executable asyncio.sleep in driver | AST-walk for `asyncio.sleep(...)` Call nodes | 0 executable (3 docstring/comment references only — verified by grep + e2e test) | ✓ PASS |

### Probe Execution

Phase 58 PLAN does not declare `scripts/*/tests/probe-*.sh` probes and is not a migration/tooling phase. No conventional probes discovered under `scripts/`. Probe execution SKIPPED.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| THROTTLE-01 | 58-01 | Per-Task RPM Token Bucket — `agent/glm_throttle.py` with per-task refillable bucket, default 30 RPM, `acquire_slot`/`try_acquire_slot` | ✓ SATISFIED | TokenBucket class + acquire/try_acquire/reset_for_testing exports; 9 TDD tests GREEN; wired into `auxiliary_client.call_llm` BEFORE Phase 57 routing; cli-config.yaml.example documents `auxiliary.{task}.rpm` override. |
| THROTTLE-02 | 58-02 | Per-Round-Table TPM Budget — `round_table_open` accepts `token_budget`, default 100K, budget_warning + budget_exceeded events, receipt `tokensConsumed` + `costUsdEstimate` | ✓ SATISFIED | `open_round_table` extended; events array + helpers; receipt cost formula at hardcoded GLM-5.2 pricing; driver wires `record_panelist_tokens` after each panelist + `check_budget_before_turn` before each call; 28 budget tests GREEN. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `agent/round_table_state.py` | 347 | "schema-valid placeholders" comment | ℹ️ Info | Not a stub — refers to schema-default fields, not unfinished code. No action. |
| `tests/agent/test_round_table_budget.py` (e2e mocked test NOTE block, lines ~830-840) | — | Mock bypasses panelist LLM calls; only verifies `acquire_slot` at synthesis leg (1 call, not 10) | ℹ️ Info | Test explicitly documents this asymmetry; real-GLM 10× invocation deferred to Phase 61 VALIDATE per ROADMAP. Not a blocker — wire-in point is proven, regression guard is in place. |

No `TBD`/`FIXME`/`XXX` markers in any Phase 58 modified file. No `return null`/`return []`/`=> {}` stub patterns in `glm_throttle.py`. No unreferenced debt markers.

### Human Verification Required

None. Phase 58 produces unit-tested, mocked-smoke-verified backend code. The real-GLM production smoke (which would require human/API budget to invoke 10× LLM calls) is correctly scheduled for Phase 61 VALIDATE per ROADMAP SC#2. No items require human testing at this phase boundary.

### Gaps Summary

No gaps found. All 3 ROADMAP success criteria verified:

1. **SC#1:** `agent/glm_throttle.py` implements token bucket per task with blocking `acquire_slot` — VERIFIED via code reading + 9 TDD tests + behavioral spot-check.
2. **SC#2:** `round_table_open` accepts `token_budget` (default 100000); `budget_warning` + `budget_exceeded` events emitted at correct thresholds — VERIFIED via code reading + behavioral spot-checks at all three thresholds (clean/warning/exceeded) + receipt cost formula.
3. **SC#3:** v11.0 SC#2 smoke runs without manual sleep + zero `RateLimitError` — VERIFIED via AST walk (zero executable `asyncio.sleep`), driver wiring of throttle acquire + budget tracking, and mocked e2e pipeline test asserting zero `asyncio.sleep` + zero `RateLimitError`. Real-GLM 10× smoke is explicitly deferred to Phase 61 VALIDATE.

Cross-phase regression: 264 tests GREEN across Phase 52 (round-table state machine), Phase 57 (endpoint routing), Phase 58 throttle integration, and auxiliary client. Ruff clean on all 7 modified files.

**Note (informational, not a gap):** The e2e mocked pipeline test in `TestPhase58FullThrottlePipeline` only exercises `acquire_slot` on the synthesis leg (1 invocation) because the mock bypasses the 9 panelist LLM calls. The test itself documents this honestly. The wire-in point (acquire_slot inside `call_llm`) is proven by code reading + the dedicated `TestGLMThrottleIntegration` tests. Full 10× invocation evidence is the Phase 61 production smoke's job.

---

_Verified: 2026-07-08T00:35:00Z_
_Verifier: Claude (gsd-verifier)_
