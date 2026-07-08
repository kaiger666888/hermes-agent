---
phase: 67-observability-backend
plan: 02
subsystem: observability
tags: [observability, metrics, round-table, context-manager, instrumentation, tdd, glm]
requires:
  - "agent.observability.MetricsBuffer (Plan 67-01 Wave 0)"
  - "mcp_serve.get_agent_opinion + submit_round_table_result (Phase 53)"
provides:
  - "agent.observability.round_table_metrics.RoundTableMetricEntry"
  - "agent.observability.round_table_metrics.record_round_table_entry"
  - "agent.observability.round_table_metrics.get_round_table_metrics"
  - "agent.observability.round_table_metrics._turn_capture (sync ctx mgr)"
  - "agent.observability.round_table_metrics._submit_capture (sync ctx mgr)"
  - "agent.observability.round_table_metrics._percentiles (Pitfall 1 safe)"
  - "Instrumented mcp_serve.get_agent_opinion (emits per-turn entries)"
  - "Instrumented mcp_serve.submit_round_table_result (emits per-round entries)"
affects:
  - "Plan 67-04 endpoint (consumes get_round_table_metrics())"
  - "Phase 68 CLI hermes orchestrator status (reads round table section)"
tech-stack:
  added: []
  patterns:
    - "sync @contextmanager wrapping existing async control flow (INFRA-04 preserved)"
    - "mutable holder (_CaptureState) yielded by ctx mgr for post-hoc status setting"
    - "try/finally inside ctx mgr to record on every exit path (Pitfall 2)"
    - "length-check BEFORE statistics.quantiles (Pitfall 1 StatisticsError mitigation)"
    - "lazy import inside function body to avoid module-load cycle (Pitfall 6)"
    - "TDD RED/GREEN per task (test commit precedes feat commit)"
key-files:
  created:
    - path: "agent/observability/round_table_metrics.py"
      lines: 364
      purpose: "OBSRV-02 collector: RoundTableMetricEntry + record + get + _percentiles + _turn_capture + _submit_capture"
    - path: "tests/agent/observability/test_round_table_metrics.py"
      lines: 207
      purpose: "13 OBSRV-02 unit tests: percentiles edge cases, buffer ops, capture happy/exception paths"
  modified:
    - path: "mcp_serve.py"
      lines_added: 246
      lines_removed: 179
      purpose: "Instrumented get_agent_opinion + submit_round_table_result with _turn_capture / _submit_capture (mostly re-indentation)"
decisions:
  - id: "D-67-02-1"
    decision: "Use a mutable _CaptureState dataclass yielded by the context managers instead of a simpler yield-None design"
    rationale: "The caller (mcp_serve instrumentation) needs to set status / token_cost / serial_lock_wait_ms DURING the with block (after specific branches execute). A mutable holder makes this ergonomic -- cap.status = 'serial_violation' reads naturally at each return path. Alternative (return-time callback) would force restructuring every return statement."
  - id: "D-67-02-2"
    decision: "Wrap the serial_violation early return in its own short _turn_capture context (separate from the main body context)"
    rationale: "The lock-is-None path returns BEFORE the outer try/finally -- without its own capture, this path would emit no metric. The short context records status='serial_violation' + the captured lock-wait delta, giving operators visibility into lock contention rejection rate."
  - id: "D-67-02-3"
    decision: "Outer finally: release_round_lock stays INSIDE the _turn_capture with-block"
    rationale: "The metric entry should include the lock-wait time but NOT the lock-release time (release is a cleanup side-effect, not user-visible latency). Putting the finally inside the with means the context finalizes the entry (via try/finally in __exit__) BEFORE the lock release runs. Verified by reading the final source -- finally at indentation level 2 (inside with), release_round_lock at level 3 (inside finally)."
  - id: "D-67-02-4"
    decision: "Early validation returns in submit_round_table_result are NOT instrumented"
    rationale: "The slug_err / round_err / state_path-missing returns happen BEFORE any round-table state mutation. They are caller-error paths (bad input), not round-table-execution outcomes. Including them would dilute the p95 latency with input-validation noise. The plan explicitly endorses this (Task 2 action step 3)."
  - id: "D-67-02-5"
    decision: "Token cost read is gated on the happy-path return ONLY (not on every return)"
    rationale: "get_last_call_usage() reads a process-global _LAST_CALL_USAGE dict that is only meaningful after a successful call_llm. Reading it on error paths (where call_llm was never reached or failed) would record stale or zero values. The happy path reads it IMMEDIATELY before return -- before any further await -- per RESEARCH Pitfall 3."
metrics:
  duration: "7m"
  completed: "2026-07-08"
  tasks_total: 2
  tasks_completed: 2
  tests_added: 13
  tests_passing: 13
  files_created: 2
  files_modified: 1
  lines_added: 817
---

# Phase 67 Plan 02: OBSRV-02 Round Table Metrics Collector + Instrumentation Summary

Ships the OBSRV-02 round-table observability surface: a new collector module (`agent/observability/round_table_metrics.py`) with a `RoundTableMetricEntry` dataclass, thread-safe buffer, p50/p95 percentile helper (Pitfall 1 safe), and two sync context managers (`_turn_capture`, `_submit_capture`). The two MCP round-table functions (`get_agent_opinion`, `submit_round_table_result`) are instrumented via minimal-diff context-manager wraps -- no behavior change, no return-value change, INFRA-04 serial-lock constraint preserved.

## What Was Built

### `agent/observability/round_table_metrics.py` — OBSRV-02 collector (NEW, 364 lines)

- **`RoundTableMetricEntry`** (`@dataclass(slots=True)`) — 9 fields: `round_id`, `snapshot_at_iso`, `duration_ms`, `token_cost`, `cost_usd`, `turn_count`, `serial_lock_wait_ms`, `early_stop_triggered`, `status`.
- **`record_round_table_entry(entry)`** — thread-safe append to the module-level `MetricsBuffer` (Wave 0 primitive).
- **`_percentiles(samples)`** — Pitfall 1 mitigation: length-checks FIRST; returns `{p50: 0.0, p95: 0.0, count: 0}` on empty input, `{p50: x, p95: x, count: 1}` on single-element, delegates to `statistics.quantiles(data, n=100)` otherwise.
- **`get_round_table_metrics()`** — pull-model snapshot returning `{count, p50_latency_ms, p95_latency_ms, avg_token_cost, total_token_cost, status_distribution, serial_lock_wait_p95_ms, early_stop_rate, snapshot_at_iso}`.
- **`_turn_capture(round_id)` / `_submit_capture(round_id)`** — SYNC context managers (`@contextmanager`, NOT `@asynccontextmanager`). Yield a mutable `_CaptureState` so the caller can set status/token_cost/etc. during the with block. Use `try/except BaseException` to record on every exit path including exceptions (Pitfall 2), then re-raise.
- **`_reset_for_test()`** — test-only helper for cross-test buffer isolation.

### `tests/agent/observability/test_round_table_metrics.py` — 13 unit tests (NEW, 207 lines)

Four test classes:
- `TestPercentiles` (3 tests): empty/single/100-element edge cases.
- `TestRoundTableMetricsBuffer` (5 tests): record append, maxlen eviction, empty-buffer zero percentiles, status_distribution, total/avg token cost.
- `TestTurnCapture` (3 tests): happy path records `status="ok"`, exception path records `status="error"` before re-raise, caller can override status via `cap.status = ...`.
- `TestSubmitCapture` (2 tests): happy path records `status="completed"` with populated totals, exception path records `status="error"`.

All tests use an `autouse` `_reset_buffer` fixture for cross-test isolation.

### `mcp_serve.py` — instrumentation (MODIFIED, +246/-179 lines)

**`get_agent_opinion` (line ~688):**
- Lazy import of `_turn_capture` (Pitfall 6 cycle avoidance).
- Serial-lock-wait timer: `t_lock_req = perf_counter()` before `await acquire_round_or_reject`; `t_lock_acquired = perf_counter()` after. Delta exposes per-roundId lock contention.
- The `lock is None` (serial_violation) early return is wrapped in its own short `_turn_capture` context — records `status="serial_violation"` + the lock-wait delta.
- The outer `try/finally` (turn body + `release_round_lock`) is wrapped in a single `_turn_capture(round_id) as cap` context. Each return path sets `cap.status`:
  - `round_not_found` / `state_read_failed` / `round_not_open`
  - `llm_malformed_response` / `append_turn_failed`
  - `ok` (happy path — reads token cost via `get_last_call_usage()` IMMEDIATELY before return per Pitfall 3)
- The `finally: release_round_lock` runs AFTER the context finalizes the metric entry (correct ordering — metric includes lock-wait but not release).

**`submit_round_table_result` (line ~978):**
- Lazy import of `_submit_capture`.
- Wraps the `_submit(...)` call. On happy path populates `cap.token_cost` / `cap.cost_usd` / `cap.turn_count` / `cap.early_stop_triggered` from the result dict (`tokensConsumed`, `costUsdEstimate`, `turns`, `events`).
- Status classification: `completed` / `conflict_409` / `submit_error` / `submit_exception`.
- Early validation returns (slug/round/state_path) are NOT instrumented — caller-error paths, not round-table-execution metrics.

## How to Use

```python
# Plan 67-04 endpoint will call:
from agent.observability.round_table_metrics import get_round_table_metrics
snapshot = get_round_table_metrics()
# -> {count: 42, p50_latency_ms: 1234.5, p95_latency_ms: 2890.1,
#     avg_token_cost: 850.2, total_token_cost: 35700,
#     status_distribution: {"ok": 38, "serial_violation": 3, "round_not_open": 1},
#     serial_lock_wait_p95_ms: 12.4, early_stop_rate: 0.0, ...}

# Direct buffer access (test-only):
from agent.observability.round_table_metrics import (
    record_round_table_entry, RoundTableMetricEntry, _reset_for_test,
)
_reset_for_test()
record_round_table_entry(RoundTableMetricEntry(
    round_id="r1", snapshot_at_iso="...", duration_ms=10.0, token_cost=100,
    cost_usd=0.0, turn_count=1, serial_lock_wait_ms=1.0,
    early_stop_triggered=False, status="ok",
))
```

The MCP instrumentation is passive — operators don't call it directly. Every `get_agent_opinion` and `submit_round_table_result` call automatically appends an entry.

## Deviations from Plan

None — plan executed exactly as written. The re-indentation of `get_agent_opinion` (4-space shift of the body inside `with _turn_capture`) accounts for most of the +246/-179 line delta in `mcp_serve.py`; the actual instrumentation logic is ~50 lines of new code (imports, timer, status assignments, token cost read).

## TDD Gate Compliance

Per-task TDD cycle followed strictly. Gate sequence verified in git log:

| Task | Phase | Commit | Hash |
|------|-------|--------|------|
| 1 | RED (test) | `test(67-02): add failing tests for round table metrics collector` | `418fb5f2f` |
| 1 | GREEN (feat) | `feat(67-02): implement OBSRV-02 round table metrics collector` | `39dcb3330` |
| 2 | feat (instrumentation) | `feat(67-02): instrument mcp_serve get_agent_opinion + submit_round_table_result` | `19965a608` |

Task 2 was not TDD-flagged in the plan (instrumentation of existing functions; verified by smoke test rather than unit test, since unit-testing would require an asyncio runtime + real locks per plan `<action>` note).

No REFACTOR phase needed.

## Verification Results

**Unit tests:** `python -m pytest tests/agent/observability/test_round_table_metrics.py -x`
- 13 tests collected, 13 passed in 0.32s

**Full Wave 1 suite:** `python -m pytest tests/agent/observability/ -x`
- 30 tests collected (Wave 0: 17 + Plan 02: 13), 30 passed in 0.66s
- Well under the 5s feedback-latency budget (VALIDATION.md)

**Instrumentation verification:**
```
$ python -c "
import mcp_serve, inspect
src1 = inspect.getsource(mcp_serve.get_agent_opinion)
src2 = inspect.getsource(mcp_serve.submit_round_table_result)
assert '_turn_capture' in src1
assert '_submit_capture' in src2
assert 'serial_lock_wait_ms' in src1
assert 'get_last_call_usage' in src1
print('OBSRV-02 instrumentation verified')
"
OBSRV-02 instrumentation verified
```

**Function signature preservation:**
- `get_agent_opinion(round_id, project_slug, agent_id, topic, panel_context=None) -> str` (still async)
- `submit_round_table_result(round_id, project_slug, conclusion, cited_memories=None, closed_by='cc') -> str` (still async)

**INFRA-04 compliance:**
- Context managers are `@contextmanager` (sync), NOT `@asynccontextmanager`.
- All `perf_counter()` reads are sync.
- No new `asyncio.create_task` introduced.

**CLAUDE.md compliance verified:**
- `from __future__ import annotations` at top of `round_table_metrics.py`.
- Lazy imports inside MCP function bodies (avoids module-load cycle).
- `%s` positional log formatting in `logger.warning(...)` calls (preserved from original code, not introduced).
- `except Exception as exc:` / `except BaseException as exc:` bind names (in ctx mgr).
- 4-space indent, double-quoted strings throughout new code.
- No `open()` calls in scope (PLW1514 trivially satisfied).

## Scope Boundary Adherence

Strict scope guard honored — git diff shows exactly the 3 files in plan frontmatter `files_modified`:

```
$ git diff --name-only HEAD~3 HEAD
agent/observability/round_table_metrics.py
mcp_serve.py
tests/agent/observability/test_round_table_metrics.py
```

- `agent/observability/__init__.py` NOT modified (owned by Plan 04 per plan note — avoids Wave 1 file overlap with sibling Plan 67-03).
- No test files outside `tests/agent/observability/` touched.
- `STATE.md` / `ROADMAP.md` / `REQUIREMENTS.md` NOT touched (per orchestrator instruction).
- No tracked-file deletions across all 3 commits.

## Known Stubs

None. The collector module is fully implemented per its contract; both context managers record real entries on every exit path; the MCP instrumentation reads live values (`get_last_call_usage()`, `result["tokensConsumed"]`, etc.). No placeholder values, TODOs, or unwired data paths.

## Threat Flags

None new. The threat surface introduced by this plan (the module-level `_BUFFER` and the new entries flowing into it) is already covered by the plan's `<threat_model>` mitigations:

- T-67-02-torn (concurrent append+snapshot) → mitigated by `MetricsBuffer`'s internal `threading.Lock` (inherited from Wave 0).
- T-67-02-infRA04 (async dispatch violates serial constraint) → mitigated by sync `@contextmanager`.
- T-67-02-exception (exception path skips recording) → mitigated by `try/except BaseException` inside both context managers (verified by `test_capture_records_on_exception_path` + `test_submit_exception_path_records_error`).

No new network endpoints, auth paths, or schema changes at trust boundaries.

## Unblocks

- **Plan 67-04** (FastAPI `/orchestrator/agents/status` endpoint) — imports `get_round_table_metrics()` from this module. Plan 04 will also add the `from agent.observability.round_table_metrics import get_round_table_metrics` re-export to `agent/observability/__init__.py` (Plan 02 deliberately does not touch `__init__.py` to avoid file-overlap with the parallel Wave 1 sibling Plan 67-03).
- **Phase 68 CLI** (`hermes orchestrator status`) — reads the `round_table` section of the endpoint response.

## Self-Check: PASSED

- [x] `agent/observability/round_table_metrics.py` exists (FOUND, 364 lines)
- [x] `tests/agent/observability/test_round_table_metrics.py` exists (FOUND, 207 lines)
- [x] `mcp_serve.py` references `_turn_capture` (FOUND in `get_agent_opinion`)
- [x] `mcp_serve.py` references `_submit_capture` (FOUND in `submit_round_table_result`)
- [x] `mcp_serve.py` references `serial_lock_wait_ms` (FOUND in `get_agent_opinion`)
- [x] Commit `418fb5f2f` exists (RED Task 1)
- [x] Commit `39dcb3330` exists (GREEN Task 1)
- [x] Commit `19965a608` exists (Task 2 instrumentation)
- [x] `python -m pytest tests/agent/observability/test_round_table_metrics.py -x` exits 0 (13 passed in 0.32s)
- [x] `python -m pytest tests/agent/observability/ -x` exits 0 (30 passed in 0.66s)
- [x] `git diff --name-only HEAD~3 HEAD` matches strict scope (3 files, 1:1 with plan frontmatter)
- [x] Empty buffer returns `p50=0.0, p95=0.0` (Pitfall 1 test passes)
- [x] Capture records entry on exception path (Pitfall 2 test passes)
- [x] No modifications to `__init__.py`, STATE.md, ROADMAP.md, or unrelated test files
