---
phase: 52-infra-foundation
plan: 04
subsystem: agent-runtime
tags: [serial-execution, asyncio-lock, concurrency, glm-compat, infra-04]
requires:
  - 52-03 (mcp_serve.py get_agent_opinion closure body — wrap target)
  - MEMORY.md/feedback-glm-overload-reduce-concurrency.md (serial policy root)
provides:
  - agent.round_table_executor.acquire_round_or_reject
  - agent.round_table_executor.release_round_lock
  - agent.round_table_executor._serial_violation_response
  - get_agent_opinion lock-guarded closure (mcp_serve.py)
affects:
  - mcp_serve.py::get_agent_opinion
  - tests/agent/test_round_table_executor.py (new)
  - tests/agent/test_mcp_serve_round_table.py (extended with TestSerialEnforcementMcpIntegration)
tech-stack:
  added: []
  patterns:
    - asyncio.Lock per-roundId registry (distinct from threading.Semaphore in glm_concurrency_guard)
    - check-then-acquire TOCTOU-safe pattern under asyncio cooperative scheduling
    - try/finally lock release (T-52-15 DoS mitigation)
key-files:
  created:
    - agent/round_table_executor.py
    - tests/agent/test_round_table_executor.py
  modified:
    - mcp_serve.py
    - tests/agent/test_mcp_serve_round_table.py
decisions:
  - asyncio.Lock (not threading.Semaphore) — distinct layer from glm_concurrency_guard.py which handles blocking SDK calls in ThreadPoolExecutor workers; the two layers COMPOSE
  - Check-then-acquire pattern (`if lock.locked(): return None; await lock.acquire()`) safe under asyncio cooperative scheduling because no await can interleave between the check and the acquire
  - Rejection NOT queueing per SC#4 mandate — queueing would violate the GLM 4-key rotation compatibility constraint
  - Lazy import of round_table_executor inside the closure (avoids any import-time coupling)
metrics:
  duration: ~12m
  completed: 2026-07-07
  tasks_completed: 3
  files_created: 2
  files_modified: 2
  tests_added: 6 (4 unit + 2 integration)
---

# Phase 52 Plan 04: INFRA-04 Serial Execution Enforcement Summary

Per-roundId `asyncio.Lock` registry that rejects concurrent `get_agent_opinion` calls for the same roundId with a 429 + MEMORY.md-citing serial-violation response — the GLM concurrency safety layer that keeps the round-table runtime compatible with the 4-key rotation policy locked in user memory.

---

## What Shipped

### 1. `agent/round_table_executor.py` (NEW)

Module-level per-roundId `asyncio.Lock` registry with three public exports:

- **`acquire_round_or_reject(round_id) -> Optional[asyncio.Lock]`** — returns the lock on success; returns `None` if contended (rejection, NOT queueing, per SC#4). Uses the check-then-acquire pattern which is TOCTOU-safe under asyncio cooperative scheduling (no `await` between `lock.locked()` and `await lock.acquire()`).
- **`release_round_lock(round_id) -> None`** — symmetric release helper; defensive double-release detection.
- **`_serial_violation_response(round_id) -> str`** — JSON-encoded 429 response with the load-bearing literal substring `feedback-glm-overload-reduce-concurrency.md` (SC#4 acceptance contract).

The module docstring explicitly cites the policy root (MEMORY.md `feedback-glm-overload-reduce-concurrency.md`), documents `agent/glm_concurrency_guard.py` as the DISTINCT API-call-level throttling layer (uses sync `Semaphore` for blocking SDK calls in `ThreadPoolExecutor` workers), and warns against collapsing the two layers.

### 2. `mcp_serve.py::get_agent_opinion` (MODIFIED)

The closure body is now lock-guarded:

1. Lazy import of `acquire_round_or_reject`, `release_round_lock`, `_serial_violation_response` at the very top of the closure.
2. `lock = await acquire_round_or_reject(round_id)` before any state file I/O.
3. `if lock is None: return _serial_violation_response(round_id)` — concurrent submission rejected immediately.
4. The rest of the closure body (state-path construction, `read_and_recover_state`, `append_turn`, return JSON) is wrapped in `try: ... finally: await release_round_lock(round_id)` — T-52-15 mitigation guarantees the lock is released on every path (happy, error, AND `asyncio.CancelledError`) so an exception cannot permanently block that roundId.

### 3. `tests/agent/test_round_table_executor.py` (NEW — 4 tests, TDD RED → GREEN)

`class TestSerialEnforcement:` covering SC#4 at the lock-primitive level:

- `test_concurrent_submission_rejected` (async) — second concurrent acquire for same roundId returns `None`
- `test_sequential_submission_succeeds` (async) — acquire → release → acquire same roundId works (lock reusable)
- `test_429_message_cites_memory_md` (sync) — response contains literal substring `feedback-glm-overload-reduce-concurrency.md` + `429` + `serial_violation`
- `test_different_roundids_use_different_locks` (async) — independent roundIds acquire concurrently

### 4. `tests/agent/test_mcp_serve_round_table.py` (EXTENDED — 2 new async tests)

`class TestSerialEnforcementMcpIntegration:` verifying the lock wiring at the MCP tool surface:

- `test_concurrent_get_agent_opinion_rejected_with_429` — pre-acquires the lock via the public API, then invokes the MCP `get_agent_opinion` tool and asserts the 429 `serial_violation` response with the MEMORY.md citation substring in the message
- `test_get_agent_opinion_happy_path_unaffected_by_lock` — regression: single sequential invocation still returns `status: ok` with the placeholder opinion intact

---

## TDD Gate Compliance

This plan executed as three TDD-structured tasks (`tdd="true"` on Tasks 1 & 2; plain auto on Task 3):

| Gate | Commit | Type | Description |
|------|--------|------|-------------|
| RED | `4e677c810` | `test(52-04)` | 4 async/sync tests in `test_round_table_executor.py` — fail with `ModuleNotFoundError` because `agent.round_table_executor` does not exist yet |
| GREEN | `3688dc509` | `feat(52-04)` | `agent/round_table_executor.py` ships the 3 public exports — all 4 RED tests flip to PASSED |
| GREEN (wiring) | `4908aded9` | `feat(52-04)` | lock wired into `mcp_serve.py::get_agent_opinion` + 2 new MCP integration tests |

RED gate commit exists and precedes the GREEN gate commit. Gate sequence valid.

---

## Acceptance Criteria Status

All plan-level acceptance criteria from `52-04-PLAN.md` `<success_criteria>` verified:

- [x] SC#4: concurrent second `get_agent_opinion` for same roundId is rejected with 429 + MEMORY.md citation
- [x] SC#4: single sequential submission proceeds and returns the panelist opinion
- [x] asyncio.Lock primitive (NOT threading.Semaphore) — `grep -c "threading" agent/round_table_executor.py` returns 0
- [x] Lock released in `finally` (no permanent roundId block on exception) — T-52-15 mitigated
- [x] Distinct layer from `agent/glm_concurrency_guard.py` (composes, does not collapse)
- [x] All Phase 52 tests pass together (39/39 across plans 01-04)

Per-task acceptance criteria from `52-04-PLAN.md` `<tasks>` all satisfied.

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Critical] Avoided literal `threading` word in module docstring**
- **Found during:** Task 2 ( GREEN implementation)
- **Issue:** Task 2 acceptance spec uses a literal automated check `grep -c "threading" agent/round_table_executor.py` returns 0. The original draft docstring contained the phrase "uses `threading.Semaphore`" as part of the cross-reference to `glm_concurrency_guard.py` — that would have failed the strict grep check.
- **Fix:** Rephrased the docstring sentence to "`glm_concurrency_guard` uses a sync `Semaphore` to throttle" — preserves the cross-reference semantics (still names the module by filename and identifies the primitive as a `Semaphore`) while passing the literal grep acceptance check.
- **Files modified:** `agent/round_table_executor.py` (docstring only, no logic change)
- **Commit:** `3688dc509` (fix landed within the GREEN commit before push)

No other deviations. Plan executed essentially as written.

---

## Test Verification

| Suite | Result | Command |
|-------|--------|---------|
| Executor unit tests | 4/4 PASSED | `pytest tests/agent/test_round_table_executor.py -x -v` |
| MCP integration tests | 15/15 PASSED | `pytest tests/agent/test_mcp_serve_round_table.py -x -v` |
| Full Phase 52 suite | 39/39 PASSED | `pytest tests/agent/test_round_table_executor.py tests/agent/test_mcp_serve_round_table.py tests/agent/test_round_table_state.py tests/agent/test_registry_loader.py -q` |
| 429 substring smoke | ok | `python -c "from agent.round_table_executor import _serial_violation_response; r = _serial_violation_response('x'); assert 'feedback-glm-overload-reduce-concurrency.md' in r and '429' in r; print('ok')"` |
| asyncio-only primitive | ok | `grep -c "threading" agent/round_table_executor.py` → 0 |
| ruff (both files) | clean | `ruff check agent/round_table_executor.py mcp_serve.py` |

---

## Known Stubs

None. All implemented code is final for Phase 52 scope (no `TODO`, `FIXME`, or "phase53_not_implemented" markers introduced by this plan).

---

## Threat Flags

None. The changes match the plan's `<threat_model>` register exactly:

- **T-52-14 (Tampering — race condition)**: mitigated via the asyncio.Lock wrapping the entire `get_agent_opinion` closure body.
- **T-52-15 (DoS — lock never released)**: mitigated via the `try: ... finally: await release_round_lock(round_id)` structure that guarantees release on every path including `asyncio.CancelledError`.
- **T-52-16 (DoS — unbounded `_ROUND_LOCKS` dict)**: accepted per plan (PoC scope ≤10 round tables; v12+ adds periodic GC).
- **T-52-17 (Repudiation — caller identity)**: accepted per plan (single-user stdio MCP, no auth in scope); INFO-level logging records winner/loser roundId.

No new threat surface introduced beyond the plan's register.

---

## Self-Check: PASSED

**Files created:**
- [x] FOUND: agent/round_table_executor.py
- [x] FOUND: tests/agent/test_round_table_executor.py

**Files modified:**
- [x] FOUND: mcp_serve.py (get_agent_opinion closure lines ~1088-1208)
- [x] FOUND: tests/agent/test_mcp_serve_round_table.py (new TestSerialEnforcementMcpIntegration class)

**Commits:**
- [x] FOUND: 4e677c810 (test(52-04) RED)
- [x] FOUND: 3688dc509 (feat(52-04) GREEN)
- [x] FOUND: 4908aded9 (feat(52-04) lock wiring)

**Test status at commit:**
- [x] 4/4 executor tests PASSED at HEAD
- [x] 15/15 MCP integration tests PASSED at HEAD
- [x] 39/39 full Phase 52 suite PASSED at HEAD
