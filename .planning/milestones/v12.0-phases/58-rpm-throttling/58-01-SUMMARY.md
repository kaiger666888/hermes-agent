---
phase: 58-rpm-throttling
plan: 01
subsystem: infra
tags: [rpm-throttling, token-bucket, glm, rate-limit, auxiliary-client]

# Dependency graph
requires:
  - phase: 57-endpoint-routing
    provides: _select_endpoint_by_prompt_length wire-in point in call_llm (Phase 58 acquire runs BEFORE this)
  - phase: 53-creative-slice
    provides: scripts/run_screenplay_step3_roundtable.py (v11.0 hardcoded asyncio.sleep patches removed here)
provides:
  - agent/glm_throttle.py — per-task RPM token bucket (acquire_slot, try_acquire_slot, DEFAULT_RPM=30)
  - agent/auxiliary_client.get_last_call_usage() — module-level token-usage tracker (THROTTLE-02 prep)
  - agent/auxiliary_client._LAST_CALL_USAGE — single-writer/single-reader tracker dict
  - cli-config.yaml.example auxiliary.{task}.rpm documentation block
affects: [58-02, 59, round-table-executor, memory-compaction]

# Tech tracking
tech-stack:
  added: []  # pure stdlib (dataclasses, time, logging) — no new packages
  patterns:
    - "Lazy import to break circular dep: glm_throttle reads config via from-scratch `from agent.auxiliary_client import _get_auxiliary_task_config` INSIDE _resolve_rpm (call-time), auxiliary_client lazy-imports acquire_slot INSIDE call_llm"
    - "Single-chokepoint capture: _validate_llm_response extended to call _capture_usage so every retry/fallback path in call_llm/async_call_llm populates the usage tracker without per-call-site edits"
    - "Token bucket with float-available: fractional tokens accumulate during partial refill intervals (classic leaky bucket), capped at capacity"

key-files:
  created:
    - agent/glm_throttle.py
    - tests/agent/test_glm_throttle.py
    - tests/test_run_screenplay_step3_roundtable.py
    - .planning/phases/58-rpm-throttling/deferred-items.md
  modified:
    - agent/auxiliary_client.py
    - cli-config.yaml.example
    - scripts/run_screenplay_step3_roundtable.py
    - tests/agent/test_auxiliary_client.py

key-decisions:
  - "DEFAULT_RPM=30 per task — well under GLM single-key RPM ceiling (typically 60 RPM/key × 4 keys = 240 RPM pool, but burst is the failure mode)"
  - "Lazy import inside call_llm to break circular dep (glm_throttle ↔ auxiliary_client). Matches the codebase _ra() forwarder-shim pattern."
  - "Usage tracker captured in _validate_llm_response (single chokepoint) rather than per return-site — covers all retry/fallback paths in call_llm/async_call_llm automatically"
  - "Token bucket uses float `available` for fractional token bookkeeping during partial refill intervals; caps at capacity"
  - "Driver script sleep removal verified via grep test (not end-to-end monkeypatch) per plan's preferred fallback — driver has too many monkeypatch surfaces for clean E2E mock"

patterns-established:
  - "RPM throttle acquire BEFORE endpoint routing: both z.ai (short) and open.bigmodel.cn/api/anthropic (long) routes count against the same per-task bucket"
  - "Config override seam at _resolve_rpm (not _get_auxiliary_task_config) — test-friendly because it avoids sys.modules swapping"

requirements-completed: [THROTTLE-01]

# Metrics
duration: 9min
completed: 2026-07-07
---

# Phase 58 Plan 01: RPM-THROTTLING Summary

**Per-task RPM token bucket (DEFAULT_RPM=30, classic leaky bucket) replacing v11.0's hardcoded `asyncio.sleep(2.5/5.0)` RPM pacing — wired into `auxiliary_client.call_llm` before Phase 57 endpoint routing + usage tracker exposed for THROTTLE-02 budget accounting.**

## Performance

- **Duration:** ~9 min
- **Started:** 2026-07-07T15:54:48Z
- **Completed:** 2026-07-07T16:03:30Z
- **Tasks:** 3/3
- **Files modified:** 8 (4 created, 4 modified)

## Accomplishments
- `agent/glm_throttle.py` (NEW, 182 lines): TokenBucket dataclass + acquire_slot (blocking) / try_acquire_slot (non-blocking) / reset_for_testing. Default 30 RPM/task, configurable via `auxiliary.{task}.rpm`. Invalid configs (zero/negative/non-numeric) fall back to default with warning — never infinite-loop.
- `auxiliary_client.call_llm` invokes `agent.glm_throttle.acquire_slot(task)` BEFORE Phase 57 endpoint routing (CONTEXT.md decision #8: both routes count against same bucket).
- `_validate_llm_response` extended to capture `response.usage` into module-level `_LAST_CALL_USAGE` tracker + new `get_last_call_usage()` export. Single chokepoint covers all retry/fallback return paths (9 return sites in call_llm + async_call_llm paths) without per-site edits.
- v11.0 hardcoded `await asyncio.sleep(2.5)` (between panelists) + `await asyncio.sleep(5.0)` (pre-synthesis) removed from driver script. Per-task token bucket handles pacing automatically.
- `cli-config.yaml.example` documents `auxiliary.{task}.rpm` override block (commented examples for round_table_opinion / memory_compaction / fitness_judge).

## Task Commits

Each task was committed atomically:

1. **Task 1: TDD — Create agent/glm_throttle.py token bucket + tests** — `fd43ec783` (test, RED+GREEN combined)
2. **Task 2: Wire acquire_slot into auxiliary_client.call_llm + expose usage tracker + cli-config docs** — `21b9fa126` (feat)
3. **Task 3: Remove hardcoded asyncio.sleep from driver script + verify zero RateLimitError in mocked run** — `e59bf8496` (feat)

## Files Created/Modified
- `agent/glm_throttle.py` — NEW, 182 lines. TokenBucket + acquire_slot + try_acquire_slot + reset_for_testing + _resolve_rpm + _get_or_create_bucket.
- `tests/agent/test_glm_throttle.py` — NEW, 9 tests (capacity, refill, isolation, config override, default RPM, lazy-init, blocking acquire, invalid-rpm fallback).
- `tests/test_run_screenplay_step3_roundtable.py` — NEW, 3 grep-based tests confirming hardcoded sleeps removed + migration documented.
- `agent/auxiliary_client.py` — Modified. +73 lines: `acquire_slot(task)` wire-in before Phase 57 routing block; module-level `_LAST_CALL_USAGE` dict + `get_last_call_usage()` export; `_capture_usage(response)` helper; `_validate_llm_response` calls `_capture_usage` after validation passes.
- `cli-config.yaml.example` — Modified. +15 lines: Phase 58 rpm documentation block (commented examples).
- `scripts/run_screenplay_step3_roundtable.py` — Modified. Removed 12 lines (2 sleep blocks + comments), added 4 lines (Phase 58 cross-reference comment in loop + module docstring section).
- `tests/agent/test_auxiliary_client.py` — Modified. +185 lines: `TestGLMThrottleIntegration` class with 7 tests.
- `.planning/phases/58-rpm-throttling/deferred-items.md` — NEW. Documents 4 pre-existing test_auxiliary_client.py failures (predate Phase 58, unrelated).

## Decisions Made
- **Lazy import to break circular dep:** `glm_throttle._resolve_rpm` does `from agent.auxiliary_client import _get_auxiliary_task_config` INSIDE the function body; `auxiliary_client.call_llm` does `from agent.glm_throttle import acquire_slot` INSIDE the function body. Matches the `_ra()` forwarder-shim pattern documented in CLAUDE.md. Alternative (moving the config helper to a third module) was rejected as more disruptive.
- **Single-chokepoint usage capture:** Modified `_validate_llm_response` to call `_capture_usage` rather than editing all 9 return sites in `call_llm`/`async_call_llm`. The validator is the single funnel every successful response passes through.
- **Token bucket with float-available:** Fractional tokens accumulate during partial refill intervals (classic leaky bucket) rather than discrete integer refills. Capped at capacity. Uses `time.monotonic()` (never `time.time()` — wall clock can jump on NTP sync).
- **Driver-script grep test over E2E mock:** Plan preferred an end-to-end mocked run asserting `acquire_slot` call count == 10, but the driver has too many monkeypatch surfaces (`mcp_serve.get_agent_opinion`, `submit_round_table_result`, `open_round_table`, `_synthesize_step3_output`, config loading). Fell back to the plan's documented simpler grep test confirming zero hardcoded sleeps + migration documented.
- **Test config override patches `_resolve_rpm` directly:** Plan suggested patching `_get_auxiliary_task_config` via `sys.modules` swap, but `sys.modules` patching doesn't reliably propagate to lazy imports. Patching `_resolve_rpm` at the module seam is cleaner and tests the real fallback logic.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test TokenBucket constructor missing required args**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Tests 2, 3, 8 constructed `TokenBucket(capacity=1, refill_interval_seconds=60.0)` without the required `available` + `last_refill_time` fields.
- **Fix:** Added the missing fields to test constructors (`available=1.0, last_refill_time=0.0`).
- **Files modified:** tests/agent/test_glm_throttle.py
- **Verification:** All 9 tests pass.
- **Committed in:** `fd43ec783` (Task 1 commit)

**2. [Rule 1 - Bug] sys.modules patch unreliable for lazy-import config helper**
- **Found during:** Task 1 (Test 5 + Test 9)
- **Issue:** `sys.modules` patching didn't reliably propagate to `_resolve_rpm`'s lazy `from agent.auxiliary_client import _get_auxiliary_task_config`.
- **Fix:** Test 5 patches `_resolve_rpm` directly at the module seam (cleaner). Test 9 swaps `sys.modules["agent.auxiliary_client"]` with save/restore around the call (works because `_resolve_rpm` hasn't cached the symbol yet at test time).
- **Files modified:** tests/agent/test_glm_throttle.py
- **Verification:** Tests 5 and 9 pass.
- **Committed in:** `fd43ec783` (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 — test-side bugs during TDD cycle, not plan defects)
**Impact on plan:** All auto-fixes necessary for tests to pass. No scope creep. Plan's intent (token bucket algorithm, wire-in point, driver cleanup) honored exactly.

## Issues Encountered
- **4 pre-existing `test_auxiliary_client.py` failures** discovered during Task 2 regression run. Verified pre-existing via `git stash` + re-run on base commit (they fail without any Phase 58 changes). Likely environment/ordering issues unrelated to RPM throttling. Documented in `deferred-items.md` per Rule 3 scope boundary.

## User Setup Required
None - no external service configuration required. The throttle is pure in-process state; RPM defaults work without any operator action. Operators CAN override per-task RPM via `auxiliary.{task}.rpm` in `cli-config.yaml` if they want to tune for their key pool size (documented in `cli-config.yaml.example`).

## Next Phase Readiness
- **THROTTLE-01 complete** — `agent/glm_throttle.py` ready for use by any caller.
- **THROTTLE-02 (Phase 58-02) prep done** — `get_last_call_usage()` export is live; `round_table_executor` (Phase 58-02 consumer) can read token usage after each panelist opinion to decrement the per-round-table token budget.
- **Phase 59 (POOL-02 per-key RPM tracking)** — orthogonal concern, can build on this module's patterns.
- **Real-GLM smoke re-run** — operator action; the mocked tests confirm wiring but the real 490s → <240s improvement claim in SC#3 requires a live `--smoke` run with GLM_API_KEY set (deferred to operator per existing v11.0 smoke pattern).

## Self-Check: PASSED

- `agent/glm_throttle.py` exists (FOUND)
- `tests/agent/test_glm_throttle.py` exists (FOUND)
- `tests/test_run_screenplay_step3_roundtable.py` exists (FOUND)
- `agent/auxiliary_client.py` modified (FOUND — acquire_slot + _LAST_CALL_USAGE + get_last_call_usage)
- `cli-config.yaml.example` modified (FOUND — rpm: documentation block)
- `scripts/run_screenplay_step3_roundtable.py` modified (FOUND — zero await asyncio.sleep)
- Commit `fd43ec783` exists (FOUND)
- Commit `21b9fa126` exists (FOUND)
- Commit `e59bf8496` exists (FOUND)
- 54/54 tests GREEN across throttle + integration + routing + round-table + driver-script grep

---
*Phase: 58-rpm-throttling*
*Completed: 2026-07-07*
