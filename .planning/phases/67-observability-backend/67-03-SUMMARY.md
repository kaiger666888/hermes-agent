---
phase: 67-observability-backend
plan: 03
subsystem: observability
tags: [observability, metrics, mem0, memory-backend, instrumentation, tdd]
requires:
  - "agent.observability.MetricsBuffer (Wave 0 ring-buffer primitive)"
provides:
  - "agent.observability.memory_backend_metrics.MemoryOpMetricEntry"
  - "agent.observability.memory_backend_metrics._memory_op_capture (ctx mgr)"
  - "agent.observability.memory_backend_metrics.record_conflict"
  - "agent.observability.memory_backend_metrics.record_memory_op_entry"
  - "agent.observability.memory_backend_metrics.get_memory_backend_metrics"
  - "Instrumentation in plugins.memory.mem0._BackendAdapter.search/.add"
  - "Instrumentation in agent.memory_arbitration.append_conflict_record"
affects:
  - "Plan 67-04 (FastAPI endpoint consumes get_memory_backend_metrics)"
  - "Phase 68 CLI (reads memory_backend section from /orchestrator/agents/status)"
tech-stack:
  added: []
  patterns:
    - "context-manager instrumentation with caller-signalled failure (mark_failure)"
    - "dedicated threading.Lock for counter independent of buffer lock"
    - "lazy import inside method body to avoid circular imports (RESEARCH Pitfall 6)"
    - "in-place deque.clear() for test-only state reset (preserves module singleton identity)"
    - "TDD RED/GREEN per task (test commit precedes feat commit)"
key-files:
  created:
    - path: "agent/observability/memory_backend_metrics.py"
      lines: 422
      purpose: "OBSRV-03 collector: MemoryOpMetricEntry + _memory_op_capture ctx mgr + record_conflict + get_memory_backend_metrics + _reset_for_test"
    - path: "tests/agent/observability/test_memory_backend_metrics.py"
      lines: 197
      purpose: "8 OBSRV-03 unit tests: search/add capture, exception path, conflict counter, empty-buffer Pitfall 1, full-buffer p95, status transitions"
  modified:
    - path: "plugins/memory/mem0/__init__.py"
      lines_instrumented: "_BackendAdapter.search + .add (lazy import + _memory_op_capture wrap + mark_failure in except)"
      purpose: "Capture search/add latency, hit_count, and error_type into the metrics buffer"
    - path: "agent/memory_arbitration.py"
      lines_instrumented: "append_conflict_record (record_conflict() call near top of body)"
      purpose: "Increment conflict counter on every observed memory conflict"
decisions:
  - id: "D-67-03-1"
    decision: "Add cap.mark_failure(exc) as a caller-signalled failure path on _CaptureState"
    rationale: "Plan assumed exceptions propagate through the with-block to __exit__, but the mem0 adapter's outer try/except swallows exceptions to preserve the 'never raise' contract (T-67-03-adapter). Without mark_failure, the ctx manager sees normal exit and records success=True on every adapter failure -- a Rule 1 bug. mark_failure lets the adapter's except branch explicitly signal failure so the metrics entry is correctly recorded. Threat T-67-03-adapter mitigation is preserved by the dual-path design (path 1: exception propagation for non-adapter callers; path 2: mark_failure for the adapter)."
  - id: "D-67-03-2"
    decision: "Reset _reset_for_test via in-place deque.clear() rather than rebinding the module global"
    rationale: "Rebinding _BUFFER = MetricsBuffer(...) broke callers that imported the reference via 'from agent.observability.memory_backend_metrics import _BUFFER' -- their reference became stale, pointing at the evicted deque. In-place clear preserves the singleton identity. deque.clear() preserves maxlen."
  - id: "D-67-03-3"
    decision: "Duplicate the _percentile_p95 helper in memory_backend_metrics rather than importing from sibling round_table_metrics"
    rationale: "Plan 67-02 (round_table_metrics) was executing in parallel and had not shipped when this plan started. Per plan Task 1 action item 7: 'Prefer duplication over cross-plan coupling within the same wave.' The helper is 8 lines; a later sweep can refactor to a shared module."
  - id: "D-67-03-4"
    decision: "report compaction_triggers as a constant 0 with inline comment citing RESEARCH A1"
    rationale: "Mem0 Platform performs server-side compaction that is not client-observable. Honest zero rather than fabricated metric (threat T-67-03-compaction mitigation). Revisit in v14 if we move to self-hosted mem0."
  - id: "D-67-03-5"
    decision: "Call record_conflict() near top of append_conflict_record body, before JSONL write"
    rationale: "Per plan Task 2 action: 'so even a failed write still counts as a conflict observed.' The canonical entry point; tests calling append_conflict_record directly are also legitimately counting conflicts (no double-count risk)."
metrics:
  duration: "6m 40s"
  completed: "2026-07-08"
  tasks_total: 2
  tasks_completed: 2
  tests_added: 8
  tests_passing: 8
  files_created: 2
  files_modified: 2
  lines_added: 619
---

# Phase 67 Plan 03: OBSRV-03 Memory Backend Metrics Collector Summary

Ships the OBSRV-03 memory backend metrics collector plus instrumentation in the mem0 adapter and `append_conflict_record`. Operators can now observe mem0 read/write p95 latency, conflict-arbitration rate, and error rate via the in-process ring buffer that the Plan 67-04 endpoint will expose.

## What Was Built

### `agent/observability/memory_backend_metrics.py` — OBSRV-03 collector

Module surface (422 lines):

- `MemoryOpMetricEntry` — `@dataclass(slots=True)` with `op_type`, `started_at_iso`, `duration_ms`, `success`, `hit_count`, `error_type`
- `record_memory_op_entry(entry)` — low-level thread-safe buffer append
- `record_conflict()` — thread-safe conflict-counter increment (uses dedicated `_CONFLICT_LOCK`, not the buffer lock)
- `get_memory_backend_metrics() -> dict` — pull-model snapshot returning `{search_p95_ms, add_p95_ms, search_count, add_count, error_rate, conflict_count, compaction_triggers, status}`
- `_memory_op_capture(op_type)` — `@contextmanager` yielding a `_CaptureState`; caller sets `cap.hit_count` on success or calls `cap.mark_failure(exc)` in their except branch
- `_CaptureState` — yielded state with `hit_count` (caller-mutable) and `mark_failure(exc)` method
- `_reset_for_test()` — test-only helper clearing the buffer + counter in place
- `_percentile_p95(samples)` — returns p95 via `statistics.quantiles(samples, n=100)[94]`; returns `0.0` for `< 2` samples (Pitfall 1)

Threat mitigations (per plan threat_model):
- **T-67-03-counter** — dedicated `threading.Lock` on the conflict counter (independent of the buffer's lock)
- **T-67-03-adapter** — dual-path failure detection: path 1 (exception propagation for non-adapter callers) + path 2 (`mark_failure` for the adapter's swallowing try/except). Verified by runtime test.
- **T-67-03-compaction** — inline comment + honest zero for `compaction_triggers` (RESEARCH A1)
- **T-67-03-torn** — inherits Wave 0 `MetricsBuffer` threading.Lock

### Instrumentation — `plugins/memory/mem0/_BackendAdapter`

Minimal-diff instrumentation preserving the adapter's "never raise" contract:

- `search` (lines 416-471): wraps entire body in `with _memory_op_capture("search") as cap:`; sets `cap.hit_count = len(out)` on success path; calls `cap.mark_failure(exc)` inside the existing `except Exception as exc: return []` branch. Lazy import at top of method body per Pitfall 6.
- `add` (lines 473-516): same pattern with `op_type="add"`; `cap.hit_count` stays at default 0 (add has no hits).

### Instrumentation — `agent/memory_arbitration.append_conflict_record`

One-line addition near the top of the function body (after docstring, before JSONL write):

```python
from agent.observability.memory_backend_metrics import record_conflict
record_conflict()  # Phase 67 OBSRV-03
```

Lazy import per Pitfall 6. Called BEFORE the JSONL write so even a failed write still counts as a conflict observed.

## How to Use

```python
# Pull snapshot (Plan 67-04 endpoint will call this on each HTTP GET)
from agent.observability.memory_backend_metrics import get_memory_backend_metrics
metrics = get_memory_backend_metrics()
# -> {search_p95_ms: 95.05, add_p95_ms: 0.0, search_count: 100, add_count: 0,
#     error_rate: 0.0, conflict_count: 12, compaction_triggers: 0, status: "ok"}

# Direct buffer access (tests, debugging)
from agent.observability.memory_backend_metrics import _BUFFER, record_memory_op_entry, MemoryOpMetricEntry
record_memory_op_entry(MemoryOpMetricEntry(
    op_type="search", started_at_iso="...", duration_ms=12.5,
    success=True, hit_count=2, error_type=None,
))
snap = _BUFFER.snapshot()  # last 100 entries, oldest-to-newest

# Conflict counter (called automatically by append_conflict_record instrumentation)
from agent.observability.memory_backend_metrics import record_conflict
record_conflict()  # increments _CONFLICT_COUNT
```

Adapter callers do not need to change — the instrumentation is transparent:

```python
# These calls now emit metrics entries automatically:
from plugins.memory.mem0 import backend
results = backend.search(query="user preferences", agent_id="screenplay", top_k=5)
record_id = backend.add(content="user likes noir", agent_id="screenplay")
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan's instrumentation assumption didn't match the adapter pattern**
- **Found during:** Task 2 (runtime verification of failure path)
- **Issue:** Plan Task 2 action §3 asserted "the context manager will already have set success=False, error_type=... because the exception propagates through the with." But the mem0 adapter's outer `try: ... except Exception: return []` SWALLOWS the exception (per its documented "never raise" contract) before it reaches `_memory_op_capture.__exit__`. Result: every adapter failure was being recorded as `success=True`, contradicting the plan's must-have truth #5 ("On exception inside search/add, an entry is STILL recorded with success=False").
- **Fix:** Added `cap.mark_failure(exc)` to `_CaptureState`; callers in except branches call it to explicitly signal failure. The ctx manager checks `state._error_type` on normal exit and overrides success/error_type if set. Dual-path design: path 1 (exception propagation) handles non-adapter callers; path 2 (`mark_failure`) handles the adapter's swallowing try/except.
- **Files modified:** `agent/observability/memory_backend_metrics.py` (+44 lines for `mark_failure` + dual-path logic), `plugins/memory/mem0/__init__.py` (+2 calls to `cap.mark_failure(exc)` in the except branches)
- **Commit:** `4376f8a96`
- **Verification:** Runtime test confirms `error_rate == 1.0` and `entry.success is False` after mocked adapter failure (previously `error_rate == 0.0`, `entry.success is True`)

**2. [Rule 1 - Bug] `_reset_for_test` broke imported references**
- **Found during:** Task 2 (runtime verification, IndexError on `_BUFFER.snapshot()[0]`)
- **Issue:** Original `_reset_for_test` rebound the module global `_BUFFER = MetricsBuffer(...)`. Callers that did `from agent.observability.memory_backend_metrics import _BUFFER` (including the test file and the runtime verification script) kept their stale reference to the evicted deque, seeing an empty buffer even after the adapter appended entries.
- **Fix:** Switched to in-place `_BUFFER._buf.clear()` (deque.clear() preserves maxlen). Reaches into the Wave 0 MetricsBuffer's private `_buf` -- acceptable for a test-only helper. Preserves the singleton identity.
- **Files modified:** `agent/observability/memory_backend_metrics.py` (`_reset_for_test` rewritten, -10/+13 lines)
- **Commit:** `4376f8a96`

### Deferred Issues

None.

## TDD Gate Compliance

Task 1 followed strict RED/GREEN cycle. Gate sequence verified in git log:

| Task | Phase | Commit | Hash |
|------|-------|--------|------|
| 1 | RED (test) | `test(67-03): add failing tests for OBSRV-03 memory backend metrics` | `054e221ee` |
| 1 | GREEN (feat) | `feat(67-03): implement OBSRV-03 memory backend metrics collector` | `39800e0b1` |
| 2 | (feat) | `feat(67-03): instrument mem0 adapter + append_conflict_record (OBSRV-03)` | `4376f8a96` |

Task 2 was not TDD-tagged (instrumentation of existing modules — verified by `inspect.getsource()` source inspection rather than unit tests, per plan `<verify>` block).

No REFACTOR phase needed.

## Verification Results

**Unit tests:** `python -m pytest tests/agent/observability/test_memory_backend_metrics.py -x`
- 8 tests collected, 8 passed in 0.27s
- Covers: search/add happy path, exception path, conflict counter, empty buffer (Pitfall 1), full buffer p95, status transitions, direct append primitive

**Full Phase 67 suite so far:** `python -m pytest tests/agent/observability/ -x`
- 25 tests collected (Wave 0 17 + Plan 03 8), 25 passed in 0.58s

**Instrumentation source inspection** (per plan `<verify>`):
```
$ python -c "import inspect; from plugins.memory.mem0 import _BackendAdapter; ..."
OBSRV-03 instrumentation verified
```

**Runtime smoke (adapter contract preserved):**
- Failure path: `backend.search(...)` returns `[]` on simulated RuntimeError; metrics buffer records `success=False, error_type="RuntimeError"`, `error_rate=1.0`
- Failure path: `backend.add(...)` returns `None` on simulated RuntimeError; metrics records failure
- Happy path: `backend.search(...)` returns 2 results; metrics records `success=True, hit_count=2`
- Happy path: `backend.add(...)` returns synthesized id; metrics records success
- Conflict counter: 3 calls to `append_conflict_record` → `conflict_count == 3`

**CLAUDE.md compliance verified:**
- `from __future__ import annotations` at top of new module
- No `open()` calls in new code (PLW1514 trivially satisfied in new module)
- No `logger.*` calls with f-strings in new code (none in new module at all)
- Specific exception binding (`except BaseException as exc:`)
- 4-space indent, double-quoted strings throughout
- Lazy import of `agent.observability` from `plugins.memory.mem0` method bodies (Pitfall 6)
- Lazy import of `agent.observability` from `agent.memory_arbitration` function body

## Scope Boundary Adherence

Strict scope guard honored. `git diff --name-only <base> HEAD` shows exactly the 4 files in the plan's `files_modified` frontmatter — 1:1 match:

- `agent/observability/memory_backend_metrics.py` (NEW)
- `tests/agent/observability/test_memory_backend_metrics.py` (NEW)
- `plugins/memory/mem0/__init__.py` (instrumented)
- `agent/memory_arbitration.py` (instrumented)

**Not touched (verified):**
- `agent/observability/__init__.py` — owned by Plan 01 (Wave 0) and Plan 04 (Wave 2 re-export)
- `mcp_serve.py` — owned by Plan 67-02 (parallel sibling)
- `STATE.md` / `ROADMAP.md` / `REQUIREMENTS.md` — per orchestrator instruction
- `tests/test_mcp_serve.py`, `tests/run_agent/test_run_agent.py` — unrelated
- Any file under `tests/` other than `tests/agent/observability/`

## Known Stubs

None. All modules fully implemented per contract; no placeholder values, TODOs, or unwired data paths.

The `compaction_triggers: 0` is an intentional honest-zero (RESEARCH A1: Mem0 Platform server-side compaction is not client-observable), not a stub.

## Threat Flags

None. No new trust-boundary surface introduced by Plan 03 beyond what the plan's `<threat_model>` already enumerated (T-67-03-counter, T-67-03-adapter, T-67-03-compaction, T-67-03-torn — all mitigated). The HTTP endpoint that exposes these metrics is Plan 67-04's responsibility.

## Unblocks

- **Plan 67-04** (FastAPI `/orchestrator/agents/status` endpoint) — imports `get_memory_backend_metrics` from `agent.observability.memory_backend_metrics` (Plan 04's `__init__.py` update will add the re-export)
- **Phase 68 CLI** — reads `memory_backend` section from the endpoint's JSON response
- **v14 Prometheus exporter** — the pull-model dict is directly scrape-able

## Self-Check: PASSED

- [x] `agent/observability/memory_backend_metrics.py` exists (FOUND)
- [x] `tests/agent/observability/test_memory_backend_metrics.py` exists (FOUND)
- [x] `plugins/memory/mem0/__init__.py` references `_memory_op_capture` (FOUND in both search and add)
- [x] `agent/memory_arbitration.py` references `record_conflict` (FOUND in append_conflict_record)
- [x] Commit `054e221ee` exists (RED Task 1)
- [x] Commit `39800e0b1` exists (GREEN Task 1)
- [x] Commit `4376f8a96` exists (Task 2 instrumentation)
- [x] `python -m pytest tests/agent/observability/test_memory_backend_metrics.py -x` exits 0 (8 passed in 0.27s)
- [x] `python -m pytest tests/agent/observability/ -x` exits 0 (25 passed in 0.58s)
- [x] `git diff --name-only <base> HEAD` matches strict scope (4 files, 1:1)
- [x] No modifications to forbidden files (`mcp_serve.py`, `STATE.md`, `ROADMAP.md`, `agent/observability/__init__.py`, tests outside `tests/agent/observability/`)
