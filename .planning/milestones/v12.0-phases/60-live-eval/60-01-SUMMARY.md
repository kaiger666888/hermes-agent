---
phase: 60-live-eval
plan: 01
subsystem: testing
tags: [mem0, latency, benchmark, slo, production-backend, p95, eval]

requires:
  - phase: 54-eval-fitness
    provides: run_latency_benchmark.py fixture-mode + timed_retrieval wrapper + seed_500_records.py
  - phase: 53-creative
    provides: memory_retrieve_scoped routing + _get_mem0_backend resolver
provides:
  - scripts/seed_mem0_backend.py idempotent 100/500/1000-record live seeder with --dry-run gate
  - plugins.memory.mem0.backend adapter singleton satisfying _get_mem0_backend contract
  - scripts/run_latency_benchmark.py --backend mem0 flag (mutually-exclusive with --fixture)
affects: [60-live-eval, 61-validate, v13-migration]

tech-stack:
  added: []  # no new dependencies — uses existing mem0 + Mem0MemoryProvider
  patterns:
    - "_BackendAdapter shell pattern — module-level singleton that lazy-initializes Mem0MemoryProvider per call (no eager client at import)"
    - "argparse mutually-exclusive group for backend selection (fixture vs live)"

key-files:
  created:
    - scripts/seed_mem0_backend.py
    - tests/scripts/test_seed_mem0_backend.py
    - tests/scripts/test_run_latency_benchmark_backend_flag.py
  modified:
    - plugins/memory/mem0/__init__.py
    - scripts/run_latency_benchmark.py

key-decisions:
  - "Strict --count choices [100,500,1000] kept (plan specified these match latency-baseline.md §2.2 three-row table); plan's verify command used --count 5 as smoke but the smallest valid choice is 100 — documented as a minor verify-cmd-vs-spec deviation in Deviations."
  - "_BackendAdapter constructs a fresh Mem0MemoryProvider per call (no client caching at the adapter layer) — inherits provider's existing circuit breaker + filter logic without duplicating state."
  - "JSON output schema extended with backend + agent_id fields (additive; Phase 54 fields record_count/percentiles/slo_verdict unchanged)."

patterns-established:
  - "_BackendAdapter pattern: module-level singleton adapter that never raises; degrades to [] / None on any provider exception so the benchmark loop survives transient API failures."
  - "Mutually-exclusive CLI group: --fixture (CI) vs --backend mem0 (production) makes operator intent explicit."

requirements-completed: [EVAL-01]  # structural satisfaction; live validation is Task 3 (DEFERRED)

duration: 45min
completed: 2026-07-08
---

# Phase 60 Plan 01: EVAL-01 Live mem0 Backend Latency Benchmark — Tasks 1+2 Summary

**Wired the production mem0 backend adapter + idempotent seeder + `--backend mem0` benchmark flag — all logic in place; only the operator-run with live `MEM0_API_KEY` (Task 3) is deferred.**

## Performance

- **Duration:** ~45 min
- **Tasks completed:** 2 of 3 (Task 3 DEFERRED — needs `MEM0_API_KEY`)
- **Files modified:** 2 source + 2 test files (602 + 345 lines added)
- **Tests:** 19 new tests, all passing; 77 total memory/scripts tests green

## Accomplishments
- Added `_BackendAdapter` singleton in `plugins.memory.mem0` exposing the `is_available()` / `search()` / `add()` contract that `agent.memory_arbitration._get_mem0_backend` expects (Phase 53 resolver line 579). Adapter never raises — degrades to `[]` / `None` on any provider exception.
- Created `scripts/seed_mem0_backend.py`: idempotent 100/500/1000-record seeder for the live mem0 backend. Supports `--dry-run` (no `MEM0_API_KEY` required), `--agent-id` (default `screenplay` per 60-CONTEXT.md decision #2), and `--idempotency-key` for re-run dedup.
- Extended `scripts/run_latency_benchmark.py` with `--backend mem0` flag as a mutually-exclusive alternative to `--fixture`. Added `--agent-id` + `--record-count` for live-mode operation. JSON output extended with `backend` + `agent_id` fields (additive; Phase 54 fields unchanged).
- Confirmed Phase 54 fixture-path regression: `--fixture 500` still produces sub-ms p95 with `slo_verdict=pass`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire mem0 backend adapter + create scripts/seed_mem0_backend.py** — `523b2e425` (feat)
2. **Task 2: Extend run_latency_benchmark with --backend mem0 flag** — `61d56ce7e` (feat)
3. **Task 3: Run live benchmark + populate latency-baseline.md §2.2** — **DEFERRED** (see Task 3 section below)

## Files Created/Modified

- `plugins/memory/mem0/__init__.py` (MODIFIED) — Added `_BackendAdapter` class + module-level `backend = _BackendAdapter()` singleton at the end of the file. Back-references Phase 60 plan 01 Task 1 + the consumer at `agent/memory_arbitration.py:579`.
- `scripts/seed_mem0_backend.py` (NEW, executable) — Idempotent seeder. Dry-run mode emits "would seed" lines without touching the network; live mode calls `backend.add()` per record with `scope="per_agent"` (CR-01: coerced to "session" at arbitration time).
- `scripts/run_latency_benchmark.py` (MODIFIED) — Added `_load_live_backend()` helper, `--backend` flag (mutually-exclusive with `--fixture`), `--agent-id`, `--record-count`. Updated docstring + stdout summary line to include `backend=` token.
- `tests/scripts/test_seed_mem0_backend.py` (NEW) — 12 tests: backend adapter contract (7), dry-run path (4), missing-key exit-2 gate (1).
- `tests/scripts/test_run_latency_benchmark_backend_flag.py` (NEW) — 7 tests: fixture regression (2), live-mode missing-key gate (2), mutual exclusion (2), live-mode JSON shape with mocked backend (1).

## Decisions Made

1. **Strict `--count` choices kept** — Plan's Task 1 verify command used `--count 5` as a smoke test, but the plan body specified `choices=[100,500,1000]`. Kept the strict choices (matches `latency-baseline.md §2.2` three-row table) and adjusted the verify command to use `--count 100` (smallest valid choice). Documented in Deviations.
2. **Fresh `Mem0MemoryProvider` per adapter call** — The `_BackendAdapter` does not cache a provider instance; each `search()` / `add()` constructs a fresh provider. Rationale: inherits the provider's existing circuit-breaker logic without duplicating adapter-level state. The cost is one object construction per call (~µs) — negligible vs the 50-300ms network round-trip.
3. **JSON output schema extended additively** — Added `backend` ("fixture" | "mem0") and `agent_id` fields. Phase 54 fields (`record_count`, `runs`, `samples_ms`, `statuses`, `percentiles`, `slo_threshold_ms`, `slo_verdict`) unchanged. This preserves the Phase 54 test contract.

## Deviations from Plan

### Minor: Task 1 verify command `--count` mismatch

**1. [Documentation] Task 1 verify command used `--count 5` smoke; script restricts to [100,500,1000]**
- **Found during:** Task 1 verification
- **Issue:** The plan's `<verify><automated>` block ran `python scripts/seed_mem0_backend.py --dry-run --count 5 --agent-id smoke-test | grep -c "would seed"`. The plan body (Task 1 action step 4) specified `--count` choices `[100, 500, 1000]` (matching `latency-baseline.md §2.2` three-row table). These contradict.
- **Resolution:** Kept the strict `choices=[100,500,1000]` (the substantive spec — it ensures operators only seed counts that have a corresponding baseline-table row for the eventual Task 3 numbers). The verify command was run with `--count 100` instead of `--count 5`. All Task 1 done criteria met: dry-run mode works without `MEM0_API_KEY`; "would seed" lines emit for every record; live-mode path checks `is_available()` before calling `backend.add()`.
- **Files affected:** `scripts/seed_mem0_backend.py` only.
- **Committed in:** `523b2e425` (Task 1 commit).

### No other deviations

Plan executed exactly as written for both Task 1 and Task 2 bodies.

## Task 3 — DEFERRED

**Task 3 (`checkpoint:human-verify`, gate=`blocking`) is deferred per the executor's sequential-execution directive.** Task 3 requires:

- A live `MEM0_API_KEY` set in `~/.hermes/.env`.
- Operator runs `scripts/seed_mem0_backend.py --agent-id screenplay --count 500` (1-4 minutes of API calls).
- Operator runs `python scripts/run_latency_benchmark.py --backend mem0 --record-count 500 --runs 100 --out /tmp/bench-live-500.json`.
- Operator populates `latency-baseline.md §2.2` 500-record row with empirical p50/p95/p99 + Date + Operator.
- If `slo_verdict == "fail"` (p95 >= 500ms): operator authors `.planning/research/v12-poc-eval/物理分区-triggers.md` (NEW) per Phase 48 §3 trigger conditions.

**Resume procedure** (from the plan's Task 3 `<action>`):

1. Verify `MEM0_API_KEY` is set: `grep MEM0_API_KEY ~/.hermes/.env`.
2. Seed: `python scripts/seed_mem0_backend.py --agent-id screenplay --count 500`.
3. Benchmark: `python scripts/run_latency_benchmark.py --backend mem0 --record-count 500 --runs 100 --out /tmp/bench-live-500.json`.
4. Populate `.planning/research/v11-poc-eval/latency-baseline.md §2.2` 500-record row.
5. If p95 >= 500ms: author `.planning/research/v12-poc-eval/物理分区-triggers.md`.
6. Commit: `git commit -m "docs(60-01): populate EVAL-01 live mem0 latency baseline (p95=X.Xms, verdict=pass|fail)"`.

Resume signal: `approved` | `deferred: <reason>` | `p95-fail: <value>ms`.

## Verification

- [x] `plugins.memory.mem0.backend` singleton importable; has `is_available()`, `search()`, `add()` methods.
- [x] `scripts/seed_mem0_backend.py --dry-run` works without `MEM0_API_KEY`, exits 0, emits "would seed" lines.
- [x] `scripts/seed_mem0_backend.py` live mode without `MEM0_API_KEY` exits 2 with documented stderr message.
- [x] `scripts/run_latency_benchmark.py --fixture 500 --runs 5` regression: sub-ms p95, `slo_verdict=pass` (Phase 54 contract preserved).
- [x] `scripts/run_latency_benchmark.py --backend mem0` (no key) exits 2 with documented stderr message.
- [x] `--fixture` and `--backend` are mutually exclusive (argparse rejects both).
- [x] 19 new tests passing across `tests/scripts/test_seed_mem0_backend.py` + `tests/scripts/test_run_latency_benchmark_backend_flag.py`.
- [x] 77 total memory/scripts tests green (Phase 54 + Phase 60 + mem0 v2 regression).
- [ ] `latency-baseline.md §2.2` populated with live numbers — **DEFERRED** (Task 3).

## Self-Check: PASSED

**Files verified:**
- FOUND: `scripts/seed_mem0_backend.py`
- FOUND: `tests/scripts/test_seed_mem0_backend.py`
- FOUND: `tests/scripts/test_run_latency_benchmark_backend_flag.py`
- FOUND: `plugins/memory/mem0/__init__.py` (modified — `_BackendAdapter` + `backend` singleton appended)
- FOUND: `scripts/run_latency_benchmark.py` (modified — `--backend` flag + `_load_live_backend`)

**Commits verified:**
- FOUND: `523b2e425` (Task 1 commit)
- FOUND: `61d56ce7e` (Task 2 commit)

**Test suite verified:**
- 77 tests pass (12 Task 1 tests + 7 Task 2 tests + 58 regression tests across memory_arbitration, mem0 v2, v11-latency-bench, v11-fitness-battery, v11-bias-canary).

## Known Stubs

None. Both Task 1 and Task 2 deliver production-ready logic. The only "incomplete" piece is Task 3 (operator-action required to run the live benchmark + populate the baseline doc) — documented above as DEFERRED, not stubbed.

## Threat Flags

None. The threat surface added by this plan (live mem0 Platform API HTTPS calls, `MEM0_API_KEY` env handling) is fully covered by the plan's existing `<threat_model>` register (T-60-01-SC, T-60-01-DO, T-60-01-IZ, T-60-01-SP, T-60-01-RE). The `_BackendAdapter` "never raise" contract directly mitigates T-60-01-SC. The existing `Mem0MemoryProvider` circuit breaker (threshold=5, cooldown=120s) mitigates T-60-01-DO. No new surface introduced beyond the plan's threat model.
