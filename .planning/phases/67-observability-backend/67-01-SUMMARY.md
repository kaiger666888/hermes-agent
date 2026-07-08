---
phase: 67-observability-backend
plan: 01
subsystem: observability
tags: [observability, metrics, ring-buffer, agent-registry, foundation, tdd]
requires: []
provides:
  - "agent.observability.MetricsBuffer (shared ring-buffer primitive)"
  - "agent.observability.get_agent_registry_metrics (OBSRV-01 snapshot)"
  - "agent.observability._check_lineage (lineage integrity predicate)"
affects:
  - "Plans 67-02/03/04 (consume MetricsBuffer + agent.observability package)"
  - "Phase 68 CLI (consumes get_agent_registry_metrics)"
tech-stack:
  added: []
  patterns:
    - "module-level singleton + threading.Lock (mirrors agent/i18n._catalog_cache)"
    - "collections.deque(maxlen=N) for bounded auto-evicting ring buffer"
    - "pure data-shaping function for snapshot collectors (no caching layer)"
    - "TDD RED/GREEN per task (test commit precedes feat commit)"
key-files:
  created:
    - path: "agent/observability/__init__.py"
      lines: 22
      purpose: "Package marker; re-exports get_agent_registry_metrics"
    - path: "agent/observability/_ring_buffer.py"
      lines: 115
      purpose: "MetricsBuffer[T] generic thread-safe bounded ring buffer"
    - path: "agent/observability/agent_registry_metrics.py"
      lines: 121
      purpose: "OBSRV-01 collector + _check_lineage predicate"
    - path: "tests/agent/observability/__init__.py"
      lines: 0
      purpose: "Test package marker"
    - path: "tests/agent/observability/test_ring_buffer.py"
      lines: 145
      purpose: "6 SHARED tests: eviction, thread safety, snapshot semantics"
    - path: "tests/agent/observability/test_agent_registry_metrics.py"
      lines: 275
      purpose: "11 OBSRV-01 tests: shape, lineage flagging, passthroughs"
  modified: []
decisions:
  - id: "D-67-01-1"
    decision: "Use collections.deque(maxlen=N) for auto-eviction instead of hand-rolled list+pop(0)"
    rationale: "RESEARCH 'Don't Hand-Roll' row 1: deque(maxlen=N) is C-level atomic for append, O(1), and bounded-by-construction. Hand-rolling risks off-by-one eviction bugs."
  - id: "D-67-01-2"
    decision: "Guard both append and snapshot with a single threading.Lock (not just rely on deque atomicity)"
    rationale: "RESEARCH Pitfall 2: deque.append is GIL-atomic, but list(deque) iteration during snapshot can tear if the GIL switches mid-iteration. The lock is held for microseconds (O(1) ops) so contention is negligible."
  - id: "D-67-01-3"
    decision: "OBSRV-01 collector is a pure function -- no module-level buffer, no caching"
    rationale: "The loader (agent.registry_loader.load_agent_registry_with_warnings) already caches via _REGISTRY_CACHE. Re-caching at the collector would risk staleness divergence. The collector is called live on each endpoint hit (Plan 67-04)."
  - id: "D-67-01-4"
    decision: "Lineage check is vacuously True on empty entries list"
    rationale: "Standard predicate logic: 'for all e in []: P(e)' is true for any P. Matches user expectation that an unloaded registry does not flag a lineage alarm (no entries to fail). Tested by test_lineage_check_empty_entries_vacuously_true."
  - id: "D-67-01-5"
    decision: "Missing/None lineage field handled via 'entry.get('lineage') or {}' idiom"
    rationale: "Handles three failure modes uniformly: missing 'lineage' key (KeyError avoidance), lineage: None (AttributeError avoidance), lineage: {} (empty-dict short-circuit). All three correctly fail the integrity check."
metrics:
  duration: "5m 23s"
  completed: "2026-07-08"
  tasks_total: 2
  tasks_completed: 2
  tests_added: 17
  tests_passing: 17
  files_created: 6
  files_modified: 0
  lines_added: 678
---

# Phase 67 Plan 01: Wave 0 Foundation (MetricsBuffer + OBSRV-01 Collector) Summary

Wave 0 foundation for Phase 67 observability: ships the shared thread-safe `MetricsBuffer` ring-buffer primitive and the pure-function OBSRV-01 agent-registry collector, plus 17 unit tests (6 SHARED + 11 OBSRV-01). All 3 downstream plans (67-02 round table, 67-03 memory, 67-04 endpoint) import from `agent.observability`.

## What Was Built

### `agent/observability/_ring_buffer.py` — MetricsBuffer[T]

Generic, bounded, thread-safe ring buffer backed by `collections.deque(maxlen=N)`.

- `MetricsBuffer(maxlen=100)` — default maxlen matches CONTEXT.md G3 (count-based window, last 100 ops)
- `append(entry)` — thread-safe (acquires `threading.Lock`)
- `snapshot() -> list[T]` — thread-safe point-in-time copy (acquires same lock; returns fresh list, no aliasing)
- `__len__()` — current entry count, bounded by maxlen
- `maxlen` (read-only property) — configured bound

**Threat mitigations:**
- T-67-01-thread (Tampering: concurrent append+snapshot torn read) — single `threading.Lock` on both `append` and `snapshot`
- T-67-01-mem (DoS: unbounded growth) — `deque(maxlen=N)` bounded by construction

### `agent/observability/agent_registry_metrics.py` — OBSRV-01 collector

Pure data-shaping function (no I/O, no caching, no module-level state).

- `get_agent_registry_metrics(entries, missing_experts, schema_ok) -> dict` — returns the 6-key OBSRV-01 snapshot:
  - `agents_loaded: int` — `len(entries)`
  - `schema_validation_ok: bool` — passthrough of `schema_ok`
  - `missing_experts: list[str]` — passthrough (order preserved, defensive copy)
  - `lineage_integrity_ok: bool` — `_check_lineage(entries)`
  - `agent_names: list[str]` — sorted names; entries without `name` contribute `""`
  - `snapshot_at_iso: str` — `datetime.now(timezone.utc).isoformat()`
- `_check_lineage(entries) -> bool` — True iff every entry has non-empty `lineage.source_sha256` AND `lineage.transform_rule_id`. Defensive against missing/None lineage via `entry.get("lineage") or {}`. Vacuously True on empty entries.

### `agent/observability/__init__.py` — package marker

Re-exports `get_agent_registry_metrics` so consumers do `from agent.observability import get_agent_registry_metrics`. Plans 67-02/67-03 will append their re-exports (`get_round_table_metrics`, `get_memory_backend_metrics`) without rewriting this block.

## How to Use

```python
from agent.observability import get_agent_registry_metrics
from agent.observability._ring_buffer import MetricsBuffer

# OBSRV-01 snapshot (Plan 67-04 endpoint calls this live on each request)
from agent.registry_loader import load_agent_registry_with_warnings
entries, missing = load_agent_registry_with_warnings()
snapshot = get_agent_registry_metrics(entries, missing, schema_ok=True)
# -> {agents_loaded: 21, schema_validation_ok: True, missing_experts: [],
#     lineage_integrity_ok: True, agent_names: [...], snapshot_at_iso: "..."}

# Shared ring buffer (Plans 67-02/03 use this for time-series collectors)
buf: MetricsBuffer[MyMetricEntry] = MetricsBuffer(maxlen=100)
buf.append(entry)
snap = buf.snapshot()  # fresh list copy, thread-safe
```

## Deviations from Plan

None — plan executed exactly as written. The only intentional scope expansion was writing more thorough test coverage than the plan minimums:

- **Plan asked for:** 4 ring_buffer tests + 5 agent_registry tests = 9 tests
- **Shipped:** 6 ring_buffer tests + 11 agent_registry tests = 17 tests
- **Extra tests added:** `test_default_maxlen_is_100` (verifies CONTEXT.md G3 contract), `test_concurrent_append_and_snapshot_interleaved` (extended thread-safety coverage), 6 additional lineage edge cases (missing transform_rule_id, missing lineage key, lineage=None, vacuous-truth empty, missing name key, sorted verification).

These additions are within the spirit of the plan (the `<behavior>` blocks listed minimum scenarios; covering the edge cases explicitly is defensive correctness per CLAUDE.md "Be defensive"). No new files outside strict scope were created.

## TDD Gate Compliance

Per-task TDD cycle followed strictly. Gate sequence verified in git log:

| Task | Phase | Commit | Hash |
|------|-------|--------|------|
| 1 | RED (test) | `test(67-01): add failing tests for MetricsBuffer primitive` | `27a4fccc9` |
| 1 | GREEN (feat) | `feat(67-01): implement MetricsBuffer ring-buffer primitive` | `74ecbbb7c` |
| 2 | RED (test) | `test(67-01): add failing tests for OBSRV-01 agent registry collector` | `403d6e789` |
| 2 | GREEN (feat) | `feat(67-01): implement OBSRV-01 agent registry collector` | `575fd755c` |

No REFACTOR phase needed — implementation is already clean (single-responsibility functions, defensive accessors, documented contracts).

## Verification Results

**Wave 0 full suite:** `python -m pytest tests/agent/observability/ -v`
- 17 tests collected, 17 passed in 0.47s
- Well under the 5s feedback-latency budget (VALIDATION.md)

**Manual smoke test** (from plan `<verification>`):
```
$ python3 -c "from agent.observability import get_agent_registry_metrics; print(get_agent_registry_metrics([], [], True))"
{'agents_loaded': 0, 'schema_validation_ok': True, 'missing_experts': [],
 'lineage_integrity_ok': True, 'agent_names': [],
 'snapshot_at_iso': '2026-07-08T05:08:11.292099+00:00'}
```

**CLAUDE.md compliance verified:**
- `from __future__ import annotations` at top of all 3 source modules
- No `open()` calls in scope (PLW1514 trivially satisfied)
- No `logger.*` calls in source (pure data-shaping modules)
- Specific exception binding in tests (`except BaseException as exc:`)
- 4-space indent, double-quoted strings throughout

## Scope Boundary Adherence

This was a **re-execution** after a prior worktree's merge conflict on `tests/run_agent/test_run_agent.py` (an UNRELATED file the prior executor had accidentally modified). The strict scope guard was honored:

- 6 files created, 0 files modified outside the allowed list
- `tests/run_agent/test_run_agent.py` NOT touched
- `tests/test_mcp_serve.py` NOT touched
- `STATE.md` / `ROADMAP.md` / `REQUIREMENTS.md` NOT touched (per orchestrator instruction)
- `agent/registry_loader.py` NOT modified (consumer-side changes are Plan 67-04)

`git diff --name-only <base> HEAD` shows exactly the 6 files in the plan's `files_modified` frontmatter — 1:1 match.

## Known Stubs

None. Both modules are fully implemented per their contracts; no placeholder values, TODOs, or unwired data paths.

## Threat Flags

None. No new trust-boundary surface introduced by Wave 0 — `MetricsBuffer` is process-internal and `get_agent_registry_metrics` is a pure function. The HTTP endpoint (Plan 67-04) is where auth applies (T-67-01 in Plan 04, deferred).

## Unblocks

- **Plan 67-02** (OBSRV-02 round table metrics) — imports `MetricsBuffer` from `agent.observability._ring_buffer`
- **Plan 67-03** (OBSRV-03 memory backend metrics) — imports `MetricsBuffer`
- **Plan 67-04** (FastAPI `/orchestrator/agents/status` endpoint) — imports `get_agent_registry_metrics` from `agent.observability`

## Self-Check: PASSED

- [x] `agent/observability/__init__.py` exists (FOUND)
- [x] `agent/observability/_ring_buffer.py` exists (FOUND)
- [x] `agent/observability/agent_registry_metrics.py` exists (FOUND)
- [x] `tests/agent/observability/__init__.py` exists (FOUND)
- [x] `tests/agent/observability/test_ring_buffer.py` exists (FOUND)
- [x] `tests/agent/observability/test_agent_registry_metrics.py` exists (FOUND)
- [x] Commit `27a4fccc9` exists (RED Task 1)
- [x] Commit `74ecbbb7c` exists (GREEN Task 1)
- [x] Commit `403d6e789` exists (RED Task 2)
- [x] Commit `575fd755c` exists (GREEN Task 2)
- [x] `python -m pytest tests/agent/observability/ -x` exits 0 (17 passed in 0.47s)
- [x] `git diff --name-only <base> HEAD` matches strict scope (6 files, 1:1)
- [x] No modifications to forbidden files (`tests/run_agent/test_run_agent.py`, `tests/test_mcp_serve.py`, `STATE.md`, `ROADMAP.md`, `REQUIREMENTS.md`)
