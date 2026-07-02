---
phase: quick-260702-ezx
plan: 01
subsystem: infra
tags: [glm, concurrency, retry, backoff, threading, semaphore, zhipu, bigmodel]

# Dependency graph
requires: []
provides:
  - "Process-wide host-keyed concurrency throttle for *.bigmodel.cn (agent/glm_concurrency_guard.py)"
  - "Overloaded-specific jittered backoff preset (jittered_backoff_overloaded: 30s/600s)"
  - "3-strike consecutive-overloaded early-abort with operator-actionable message"
  - "TurnRetryState.consecutive_overloaded counter field"
affects: [glm-reliability, retry-loop, conversation-loop, gateway-stability]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Host-keyed process-wide threading.Semaphore for provider-specific throttling"
    - "No-op contextmanager short-circuit for non-matching endpoints (zero overhead on irrelevant paths)"
    - "Classification-driven backoff preset selection (branch on FailoverReason.overloaded)"
    - "Consecutive-reason counter on TurnRetryState for early-abort decisions"

key-files:
  created:
    - "agent/glm_concurrency_guard.py"
    - "tests/test_glm_concurrency_guard.py"
    - "tests/agent/test_retry_utils_overloaded.py"
  modified:
    - "agent/retry_utils.py"
    - "agent/conversation_loop.py"
    - "agent/turn_retry_state.py"
    - "cli-config.yaml.example"
    - "tests/agent/test_turn_retry_state.py"

key-decisions:
  - "threading.Semaphore over asyncio.Semaphore: the OpenAI SDK call inside _perform_api_call blocks the calling thread even under the gateway's asyncio loop, so a threading semaphore is the correct shared-state primitive across the main loop + ThreadPoolExecutor workers."
  - "Host-keyed (not URL-keyed): future-proofs against Zhipu routing via different *.bigmodel.cn subdomains; one throttle per upstream host."
  - "Counter on TurnRetryState (not a plain local): the existing recovery bookkeeping dataclass is the canonical home for per-attempt state, and placing it there makes the reset-on-success semantics structural (fresh instance per outer iteration)."
  - "30s/600s backoff preset: 30s floor ensures the third retry lands past the typical 1305 micro-burst; 600s cap leaves headroom under the gateway's max-iteration wall-clock."
  - "C-series tests use structural source assertions for conversation_loop integration instead of executing run_conversation (a 4000-line function requiring a fully-wired AIAgent). This trades some behavioral coverage for reliability and speed."

patterns-established:
  - "Provider-specific throttle as a no-op contextmanager wrapping the shared API-call chokepoint — pattern reusable for future provider-specific mitigations."
  - "Classification-driven backoff branching: when a FailoverReason deserves a different backoff curve, branch at the wait_time computation site rather than parameterizing jittered_backoff itself."

requirements-completed: [GLM-HARDEN-A, GLM-HARDEN-B, GLM-HARDEN-C]

# Metrics
duration: 44min
completed: 2026-07-02
---

# Quick Task 260702-ezx: GLM Concurrency Hardening Summary

**Process-wide semaphore throttling *.bigmodel.cn at N=4, 30s/600s backoff preset for 1305 overloaded responses, and 3-strike early-abort — eliminates the "model provider failed after retries" storm observed 2026-07-02 10:05-10:25 CST while staying inside the locked constraints (single endpoint, single model, no extra cost).**

## Performance

- **Duration:** 44 min (started 2026-07-02T02:58:48Z, completed 2026-07-02T03:42:23Z)
- **Tasks:** 1 (single atomic commit containing all three mitigations A+B+C)
- **Files modified:** 8 (3 created, 5 modified)
- **Commit:** `4b821c29b` on `worktree-agent-a034a0aac8c1c2a22`

## Accomplishments

- **A. Concurrency guard shipped:** `agent/glm_concurrency_guard.py` provides a process-wide `threading.Semaphore` keyed by parsed hostname, capping in-flight `*.bigmodel.cn` requests at N=4 (configurable via `glm.global_concurrency` in config.yaml or `HERMES_GLM_CONCURRENCY` env, clamped to [1, 32]). Wraps `_perform_api_call` at the single chokepoint in `conversation_loop.py`; no-op for non-GLM providers.
- **B. 1305-specific backoff shipped:** `jittered_backoff_overloaded()` in `agent/retry_utils.py` returns 30s-base / 600s-cap jittered delays. Branched in the API-error retry path only when `classified.reason == FailoverReason.overloaded`; all other reasons keep the existing 0.5s/32s path.
- **C. 3-strike early-abort shipped:** `TurnRetryState.consecutive_overloaded` counter increments on each overloaded classification, resets on any other reason and on success. At >= 3, the retry loop returns early with `"GLM model overloaded — 3 consecutive 1305/overloaded responses. Pause new requests for ~10-15 minutes and retry."` and `failure_reason: "glm_overloaded_abort"` instead of churning through all 10 retries.
- **35 new tests, 246 regression tests, all green.** Ruff clean on all 7 Python files.
- **Zero scope creep:** no changes to credential pool, fallback provider, model switch, OpenRouter, curator, title_generator, or any non-GLM code path.

## Task Commits

This was a single atomic commit containing all three mitigations (A+B+C), per the plan's explicit "ONE commit" constraint:

1. **Task 1 (TDD): GLM concurrency guard + 1305 backoff + 3-strike abort** — `4b821c29b` (fix)

The TDD RED phase wrote all test files first, confirmed they failed with ImportError, then the GREEN phase implemented the modules. No separate RED commit was made because the plan specified a single atomic commit; the RED state was verified inline before implementation began.

## Files Created/Modified

### Created
- `agent/glm_concurrency_guard.py` (221 lines) — Process-wide host-keyed semaphore module. Exports: `acquire_glm_slot`, `get_glm_semaphore`, `is_glm_endpoint`. No-op contextmanager for non-GLM endpoints.
- `tests/test_glm_concurrency_guard.py` (417 lines, 28 tests) — Covers host matching (A1), semaphore singleton per host (A2), configurable N with env/config/precedence/clamping/garbage (A3), concurrency cap high-water mark (A4), release-on-exception (A5), non-GLM passthrough (A6), consecutive-overloaded counter semantics (C1/C2/C3), and structural integration assertions for conversation_loop wiring.
- `tests/agent/test_retry_utils_overloaded.py` (71 lines, 7 tests) — Covers overloaded preset bounds (B1), default-path unchanged (B2), and no cross-contamination between preset and default.

### Modified
- `agent/retry_utils.py` — Added `jittered_backoff_overloaded(attempt)` thin wrapper (30s/600s/0.5jitter). Module docstring updated with the 2026-07-02 incident context. Existing `jittered_backoff` signature and math untouched.
- `agent/conversation_loop.py` — Three surgical edits: (1) import additions for `acquire_glm_slot` and `jittered_backoff_overloaded`; (2) `with acquire_glm_slot(...)` wrapping `run_llm_execution_middleware`; (3) counter increment + early-abort guard after `classify_api_error`, before the `max_retries` terminal check; (4) `elif classified.reason == FailoverReason.overloaded:` branch in the backoff computation; (5) counter reset on the success-path break.
- `agent/turn_retry_state.py` — Added `consecutive_overloaded: int = 0` field with docstring explaining it's a counter (not a one-shot guard).
- `cli-config.yaml.example` — Updated the commented `glm:` block with the real `open.bigmodel.cn/api/anthropic` base_url and documented `global_concurrency: 4` plus the `HERMES_GLM_CONCURRENCY` env override.
- `tests/agent/test_turn_retry_state.py` — Contract test updated: added `consecutive_overloaded` to `EXPECTED_FIELDS` and introduced `COUNTER_FIELDS` exclusion set so the all-guards-default-False assertion recognizes the counter's int/0 default.

## Decisions Made

- **`threading.Semaphore` not `asyncio.Semaphore`:** per CLAUDE.md architecture notes, the OpenAI SDK call inside `_perform_api_call` blocks the calling thread even under the gateway's asyncio loop. ThreadPoolExecutor workers (delegate_task) and asyncio-thread callers all share the same process-wide threading semaphore. Cross-process throttling is out of scope (single gateway process assumption matches `hermes-gateway.service` deployment).
- **Host-keyed, not URL-keyed:** `open.bigmodel.cn` and `alt.bigmodel.cn` get separate semaphores, but `open.bigmodel.cn/api/anthropic` and `open.bigmodel.cn/v1/chat/completions` share one. Future-proofs against Zhipu routing changes.
- **No-op short-circuit in `acquire_glm_slot`:** the context manager yields immediately for non-GLM endpoints with zero overhead (no semaphore lookup, no lock). This is critical — the wrapper sits on the main API-call chokepoint and must not slow down Anthropic/OpenAI/Bedrock paths.
- **Counter on TurnRetryState:** the existing dataclass is the canonical home for per-attempt recovery state. Placing it there makes the reset-on-success structural (fresh `TurnRetryState()` per outer iteration at line 912) plus an explicit defensive reset at the success-break for clarity.
- **Structural C-series tests:** the full abort logic lives inline in `run_conversation` (4000+ lines, requires fully-wired AIAgent). The C1/C2/C3 tests exercise the counter state machine directly via TurnRetryState and assert the integration points exist via source-text scanning. This trades some behavioral coverage for test reliability and speed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed `NameError: cfg_get` in `_resolve_glm_n`**
- **Found during:** Task 1 GREEN phase (first test run)
- **Issue:** The plan's code sketch imported `cfg_get` inside `_load_config_for_glm()` but the reference lived in `_resolve_glm_n()`, causing `NameError` at runtime.
- **Fix:** Moved the `from hermes_cli.config import cfg_get` import into `_resolve_glm_n()` (local import to keep the module importable without the full hermes_cli stack at module-load time).
- **Files modified:** `agent/glm_concurrency_guard.py`
- **Verification:** All 6 TestResolveGlmN tests pass.
- **Committed in:** `4b821c29b`

**2. [Rule 1 - Bug] Fixed incorrect test expectation for `jittered_backoff_overloaded(5)`**
- **Found during:** Task 1 GREEN phase
- **Issue:** Plan's B1 spec said `jittered_backoff_overloaded(5) >= 600.0`, but mathematically attempt=5 yields `30 * 2^4 = 480` which is below the 600 cap. The implementation is correct; the test expectation was wrong.
- **Fix:** Renamed `test_fifth_attempt_hits_cap` to `test_high_attempt_hits_cap` and bumped the attempt to 6 (where `30 * 2^5 = 960 > 600`, cap engages).
- **Files modified:** `tests/agent/test_retry_utils_overloaded.py`
- **Verification:** Test passes; math documented inline.
- **Committed in:** `4b821c29b`

**3. [Rule 1 - Bug] Updated `test_turn_retry_state.py` contract for new counter field**
- **Found during:** Task 1 regression run
- **Issue:** The existing `test_all_guards_default_false` and `test_field_set_matches_contract` tests enforced a structural invariant (all fields are bool-default-False guards, exact field set). My new `consecutive_overloaded: int = 0` field violated both.
- **Fix:** Added `consecutive_overloaded` to `EXPECTED_FIELDS` and introduced a `COUNTER_FIELDS` exclusion set so the default-False assertion recognizes int/0 defaults as valid for counters.
- **Files modified:** `tests/agent/test_turn_retry_state.py`
- **Verification:** All 4 turn_retry_state tests pass.
- **Committed in:** `4b821c29b`

---

**Total deviations:** 3 auto-fixed (3 × Rule 1 bugs — test/expectation corrections and a name-resolution fix)
**Impact on plan:** All auto-fixes necessary for correctness. No scope creep; all three were direct consequences of the plan's own code sketch or test specs.

## Issues Encountered

- **Worktree cwd drift:** My Bash calls operated from `/data/workspace/hermes-agent` (the main repo) rather than `/data/workspace/hermes-agent/.claude/worktrees/agent-a034a0aac8c1c2a22` (the worktree). All 8 task files initially landed in the main repo's working tree. Detected via the pre-commit cwd-drift assertion. Resolved by copying the files into the worktree, then `git checkout --` the modified files and `rm` the new files in the main repo to restore its pre-task state. The commit was then made from the worktree on the `worktree-agent-a034a0aac8c1c2a22` branch. The main repo's pre-existing uncommitted modifications (`.pipeline-state.json`, `agent/agent_runtime_helpers.py`, `gateway/platforms/telegram.py`) were left untouched.

## User Setup Required

None — no external service configuration required. The guard works with default N=4 out of the box. Operators who want to tune N during an incident can set `HERMES_GLM_CONCURRENCY=2` (or any value in [1, 32]) in the `hermes-gateway.service` environment and restart the service, or add `glm.global_concurrency: 2` to `~/.hermes/config.yaml`.

## Next Phase Readiness

- **Mitigation is structural and permanent:** the guard, backoff, and abort logic ship in this commit and activate automatically for any `*.bigmodel.cn` endpoint. No operator action needed at the next 1305 incident — the early-abort will fire after 3 consecutive overloaded responses with a clear message instead of churning through 10 retries.
- **Operator verification during next peak hour:** `tail -F ~/.hermes/logs/agent.log | grep -E "GLM concurrency|consecutive 1305|early-abort"` should show (a) the one-time `GLM concurrency guard enabled for open.bigmodel.cn: N=4` INFO line at gateway startup, (b) the `GLM early-abort: 3 consecutive overloaded` ERROR line if/when 3× 1305 strikes again.
- **Optional follow-ups (out of scope):** the guard currently covers the main conversation loop only. `auxiliary_client.py` paths (title_generator, curator) are lower-volume and were deliberately excluded — a follow-up commit could wrap them if 1305s are observed there.

## Threat Model Compliance

All five STRIDE threats from the plan's threat register are mitigated as specified:

| Threat | Mitigation | Verified by |
|--------|------------|-------------|
| T-GLM-01 (Tampering: config value) | Clamp to [1, 32] in `_resolve_glm_n()`; fall back to default 4 on TypeError/ValueError | `TestResolveGlmN::test_clamped_to_min_1`, `test_clamped_to_max_32`, `test_garbage_env_falls_back_to_default` |
| T-GLM-02 (DoS: N=1 operator choice) | Accepted; warning logged | `get_glm_semaphore` logs `WARNING` when `n <= 1` |
| T-GLM-03 (Tampering: env injection) | Accepted; env already requires process-level access | Clamp still applies |
| T-GLM-04 (DoS: semaphore deadlock on exception) | `try/finally` releases on exception | `TestReleaseOnException::test_semaphore_value_restored_after_exception` |
| T-GLM-05 (Repudiation: missing log trail) | INFO log on first semaphore creation, DEBUG on each acquire | `get_glm_semaphore` logs `GLM concurrency guard enabled for %s: N=%d` |

## Self-Check: PASSED

**Files verified to exist in commit `4b821c29b`:**
- `agent/glm_concurrency_guard.py` — FOUND
- `agent/retry_utils.py` — FOUND (modified)
- `agent/conversation_loop.py` — FOUND (modified)
- `agent/turn_retry_state.py` — FOUND (modified)
- `tests/test_glm_concurrency_guard.py` — FOUND
- `tests/agent/test_retry_utils_overloaded.py` — FOUND
- `tests/agent/test_turn_retry_state.py` — FOUND (modified)
- `cli-config.yaml.example` — FOUND (modified)

**Commit verified in git log:**
- `4b821c29b` — FOUND

**Test verification:**
- 35 new tests pass (tests/test_glm_concurrency_guard.py + tests/agent/test_retry_utils_overloaded.py)
- 246 regression tests pass (tests/agent/test_error_classifier.py + tests/test_retry_utils.py + tests/agent/test_turn_retry_state.py)
- 222 auxiliary_client tests pass (tests/agent/test_auxiliary_client.py)
- 115 retry/overload/backoff/recovery tests pass (tests/agent/ -k retry/overload/backoff/recovery)
- Ruff clean on all 7 modified/created Python files (PLW1514 encoding rule specifically)

---
*Quick task: 260702-ezx-glm-concurrency-hardening*
*Completed: 2026-07-02*
