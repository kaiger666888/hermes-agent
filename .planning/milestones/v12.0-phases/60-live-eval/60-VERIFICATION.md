---
phase: 60-live-eval
verified: 2026-07-08T06:15:00Z
status: human_needed
score: 3/3 autonomous truths verified (5/5 must-haves: 3 wired + 2 deferred operator)
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: n/a
  gaps_closed: []
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "EVAL-01 live mem0 latency benchmark — seed 500 records + run --backend mem0 --runs 100 + populate latency-baseline.md §2.2"
    expected: "latency-baseline.md §2.2 500-record row filled with empirical p50/p95/p99 + Date + Operator; if p95 ≥ 500ms, 物理分区-triggers.md authored with 5 sections per Phase 48 §3"
    why_human: "Requires MEM0_API_KEY (operator secret). Cannot run live mem0 Platform API calls in CI or verifier sandbox. Plan 60-01 Task 3 is explicitly checkpoint:human-verify gate=blocking."
  - test: "EVAL-02 real-mode fitness battery — run scripts/compute_fitness_baseline.py against live GLM aux pool + author fitness-battery-baseline.md"
    expected: "fitness_trend.jsonl has 2 new entries (persona_aligned + generic_llm with mode field, battery_version=v1-screenplay-baseline-real). fitness-battery-baseline.md exists with 7 sections + discrimination verdict (PASS if delta ≥ 0.3 AND persona mean ≥ 0.7)."
    why_human: "Requires GLM_AUX_API_KEY_1..4 in ~/.hermes/.env (operator secret) + ~10-25min wall-clock + ~400K tokens + ~0.20 CNY. Plan 60-02 Task 3 is explicitly checkpoint:human-verify gate=blocking. Cannot run GLM API calls from verifier sandbox."
---

# Phase 60: LIVE-EVAL Verification Report

**Phase Goal:** Run deferred v11.0 EVAL handoffs against live backends.
**Verified:** 2026-07-08T06:15:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

The Phase 60 SCs explicitly contain "live run" semantics that require operator credentials. Per the verification focus directive, **Task 3 of both plans is deferred to operator with live GLM/mem0**. This verification assesses the **infrastructure readiness** that the autonomous Tasks 1+2 of both plans shipped.

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Operator with MEM0_API_KEY can seed 500 screenplay-scoped records to live mem0 backend via a single idempotent script | VERIFIED (infra) | `scripts/seed_mem0_backend.py` (212 lines) dry-run emits 100 "would seed" lines + `backend.add()` path checks `is_available()` first, exits 2 with documented message if missing. Spot-check: `--dry-run --count 100` succeeded, 101 output lines. |
| 2 | Operator can run a 100-call p95 latency benchmark against seeded live backend and receive a JSON result file | VERIFIED (infra) | `scripts/run_latency_benchmark.py --backend mem0` flag present + mutually-exclusive with `--fixture`. Spot-check: `--backend mem0 --out /tmp/test.json` exited 2 with documented "MEM0_API_KEY not set" message. Mutual exclusion enforced (`--fixture 100 --backend mem0` rejected by argparse). Fixture regression preserved (p95=0.022ms, slo_verdict=pass). |
| 3 | Live p50/p95/p99 numbers populate latency-baseline.md §2.2 (replacing TBD placeholders) | DEFERRED (operator) | `.planning/research/v11-poc-eval/latency-baseline.md §2.2` rows 100/500/1000 still show `TBD` (3 rows × 5 cells). Needs operator with `MEM0_API_KEY` to run Task 3. |
| 4 | Operator with GLM keys can run the full 8-scenario fitness battery in real-mode end-to-end | VERIFIED (infra) | `agent/fitness_battery.py` baseline_mode dispatch path implemented: `_dispatch_real_mode` routes through `auxiliary_client.call_llm`; `_extract_user_message` + `_load_persona_system_prompt` helpers present; `BATTERY_VERSION` bumped to `v1-screenplay-baseline-real`. 11 hermetic dispatch tests pass. |
| 5 | Discrimination delta ≥ 0.3 documented in fitness-battery-baseline.md | DEFERRED (operator) | `.planning/research/v12-poc-eval/` directory does not exist. `fitness-battery-baseline.md` not yet authored. Last 2 entries in `~/.hermes/eval/fitness_trend.jsonl` are v11.0 shadow runs (`battery_version=v1-screenplay-baseline`, mean_score 0.0125/0.01875). Needs operator with `GLM_AUX_API_KEY_1..4` to run Task 3. |

**Score:** 3/5 truths verified (infrastructure); 2/5 deferred to operator human-verify checkpoint.

### Deferred Items

The 2 deferred truths are operator-action checkpoints, not deferred to a later milestone phase. They are the **preconditions** for Phase 61 VALIDATE's audit verdict but are NOT explicitly re-scoped in Phase 61's goal/success criteria.

| # | Item | Addressed In | Evidence |
|---|------|--------------|----------|
| 1 | Live mem0 p50/p95/p99 numbers + 物理分区-triggers.md (if p95 ≥ 500ms) | Not deferred to later phase | Phase 61 VALIDATE relies on these numbers but its goal is "v12.0 close-out — audit + production smoke". The live numbers must land in Phase 60 itself (Task 3 of 60-01). |
| 2 | Real-mode fitness battery run + discrimination verdict | Not deferred to later phase | Same — Phase 61 audit depends on it but does not produce it. Phase 60 Task 3 of 60-02 must run. |

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `scripts/seed_mem0_backend.py` | NEW idempotent seeder with --dry-run, --count [100,500,1000], --agent-id, --idempotency-key | VERIFIED | 212 lines. `def main()` at line 146. dry-run emits 100+ "would seed" lines without key. Exit code 2 path on missing key verified. |
| `scripts/run_latency_benchmark.py` | MODIFIED with --backend mem0 flag, mutually-exclusive with --fixture | VERIFIED | 324 lines. `--backend` + `--agent-id` + `--record-count` args + `add_mutually_exclusive_group(required=True)` at line 227. `_load_live_backend` at line 113. JSON output adds `backend` + `agent_id` fields (additive, Phase 54 fields preserved). |
| `scripts/compute_fitness_baseline.py` | NEW dual-mode orchestrator with 6 documented flags | VERIFIED | 329 lines. `def main()` at line 174. `--battery`, `--persona-sha256`, `--out`, `--model-id`, `--provider`, `--skip-generic`, `--trend-path` all present (`--help` output has 7 lines, ≥4 done criterion). |
| `agent/fitness_battery.py` | MODIFIED with baseline_mode kwarg + 3 dispatch paths + BATTERY_VERSION bump | VERIFIED | 655 lines. `BATTERY_VERSION = "v1-screenplay-baseline-real"` at line 36. `baseline_mode` kwarg on `_dispatch_agent` (line 149) + `run_battery` (line 576). `_extract_user_message` (line 77) + `_load_persona_system_prompt` (line 106) + `_dispatch_real_mode` (line 252) all present. |
| `plugins/memory/mem0/__init__.py` | MODIFIED with _BackendAdapter class + backend singleton | VERIFIED | 500 lines total. `_BackendAdapter` class at line 395; `is_available()`, `search()` (keyword-only: query, agent_id, top_k), `add()` (keyword-only: content, agent_id, scope, confidence) all present. Module-level `backend = _BackendAdapter()` at line 500. |
| `tests/scripts/test_seed_mem0_backend.py` | NEW 12 tests | VERIFIED | 264 lines, 12 tests pass. |
| `tests/scripts/test_run_latency_benchmark_backend_flag.py` | NEW 7 tests | VERIFIED | 214 lines, 7 tests pass. |
| `tests/v11-fitness-battery/test_baseline_mode_dispatch.py` | NEW 11 tests | VERIFIED | 299 lines, 11 tests pass. |
| `.planning/research/v11-poc-eval/latency-baseline.md §2.2` | POPULATED with live p50/p95/p99 | DEFERRED | §2.2 rows 100/500/1000 still show `TBD`. Awaiting operator Task 3. |
| `.planning/research/v12-poc-eval/fitness-battery-baseline.md` | NEW doc with 7 sections + verdict | DEFERRED | Directory `.planning/research/v12-poc-eval/` does not exist yet. Awaiting operator Task 3. |
| `~/.hermes/eval/fitness_trend.jsonl` real-mode entries | 2 new entries with mode field + battery_version=v1-screenplay-baseline-real | DEFERRED | Last 2 entries are v11.0 shadow runs (battery_version=v1-screenplay-baseline, mean 0.0125/0.01875). Awaiting operator Task 3. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `agent.memory_arbitration._get_mem0_backend` | `plugins.memory.mem0.backend` | `from plugins.memory.mem0 import backend as _backend` at line 579 | WIRED | Verified by direct import: `from plugins.memory.mem0 import backend; backend.is_available()` returns False without key (correct — no exception raised). |
| `agent.memory_arbitration.memory_retrieve_scoped` | `backend.search` | `backend.search(query=query, agent_id=effective_agent_id, top_k=top_k)` at line 429 | WIRED | Keyword-only args match adapter signature. |
| `agent.memory_arbitration.memory_submit_record` | `backend.add` | `backend.add(...)` at line 499 | WIRED | Keyword-only args match adapter signature. |
| `agent.memory_scoped_retrieval.timed_retrieval` | `backend.search` | `backend.search(query=query, agent_id=agent_id, top_k=top_k)` at line 125 | WIRED | Keyword-only args match. |
| `scripts/seed_mem0_backend.py` | `backend.add` | `backend.add(content=..., agent_id=..., scope=..., confidence=...)` at line 181 | WIRED | Keyword args match adapter signature. |
| `scripts/run_latency_benchmark.py` | `timed_retrieval` with `backend=` | `timed_retrieval(query, agent_id, backend=backend, top_k=5)` at line 178/181 | WIRED | `backend=` kwarg supported by `timed_retrieval` contract. |
| `scripts/compute_fitness_baseline.py` | `agent.fitness_battery.run_battery` | `run_battery(..., baseline_mode=baseline_mode, ...)` at line 147/152 | WIRED | `baseline_mode` kwarg threads through `run_battery` → `_dispatch_agent` → `_dispatch_real_mode` → `auxiliary_client.call_llm`. |
| `agent.fitness_battery._dispatch_real_mode` | `agent.auxiliary_client.call_llm` | `call_llm(task="fitness_battery_agent", provider="glm", messages=..., max_tokens=2048, timeout=60.0)` | WIRED | Per MEMORY.md feedback-glm-5-2-only.md: locked to `provider="glm"`. Verified in source. |

### Data-Flow Trace (Level 4)

Not applicable — all 5 shipped artifacts are scripts/runners/adapters/dispatchers, not render-time data components. The live data flow (real GLM responses, real mem0 hits) is the deferred operator portion.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Backend adapter importable + has 3 methods | `python3 -c "from plugins.memory.mem0 import backend; assert hasattr(backend, 'is_available') and hasattr(backend,'search') and hasattr(backend,'add')"` | `backend adapter importable + has all 3 methods` | PASS |
| Seeder dry-run emits "would seed" lines without key | `python3 scripts/seed_mem0_backend.py --dry-run --count 100 --agent-id screenplay \| wc -l` | 101 lines (100 records + summary) | PASS |
| Seeder live mode without key exits 2 | `python3 scripts/seed_mem0_backend.py --count 100 --agent-id screenplay` | exit 2 with "MEM0_API_KEY not set. Run with --dry-run..." | PASS |
| Latency benchmark fixture regression | `python3 scripts/run_latency_benchmark.py --fixture 500 --runs 5 --out /tmp/bench-fixture-regression.json` | `p50=0.020ms p95=0.022ms p99=0.023ms slo_verdict=pass` | PASS |
| Latency benchmark live mode without key exits 2 | `python3 scripts/run_latency_benchmark.py --backend mem0 --out /tmp/test.json` | exit 2 with "MEM0_API_KEY not set. Set it in ~/.hermes/.env or use --fixture for CI runs." | PASS |
| `--fixture` and `--backend` mutual exclusion | `python3 scripts/run_latency_benchmark.py --fixture 100 --backend mem0` | argparse rejects: "argument --backend: not allowed with argument --fixture" | PASS |
| `compute_fitness_baseline.py --help` lists required flags | `python3 scripts/compute_fitness_baseline.py --help \| grep -c "persona-sha256\|--battery\|--out\|--skip-generic"` | 7 (≥ 4 done criterion) | PASS |
| Test gate green | `python3 -m pytest tests/scripts/test_seed_mem0_backend.py tests/scripts/test_run_latency_benchmark_backend_flag.py tests/v11-fitness-battery/test_baseline_mode_dispatch.py -x` | 30 passed in 1.45s | PASS |

### Probe Execution

No probes declared in Phase 60 plans or conventional `scripts/*/tests/probe-*.sh` directory. Step 7c SKIPPED.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| EVAL-01 | 60-01 | Production mem0 Backend Latency p95 Benchmark | STRUCTURALLY SATISFIED (infra) — live run DEFERRED | Seeder + `--backend mem0` flag + adapter all wired; operator-action handoff in Task 3 (live `MEM0_API_KEY` run) explicitly deferred. |
| EVAL-02 | 60-02 | Fitness Battery Real-Mode Baseline | STRUCTURALLY SATISFIED (infra) — live run DEFERRED | `baseline_mode` dispatch + dual-mode orchestrator + 11 hermetic tests all wired; operator-action handoff in Task 3 (live GLM aux pool run) explicitly deferred. |

No orphaned requirements found for Phase 60.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| (none) | - | - | - | - |

No `TBD`/`FIXME`/`XXX` markers in any of the 8 shipped files. No `TODO`/`HACK`/`PLACEHOLDER` markers in shipped source. One grep hit on "not available" in `run_latency_benchmark.py:118` is docstring text describing expected behavior, not a placeholder.

### Human Verification Required

#### 1. EVAL-01 Live mem0 Latency Benchmark Run

**Test:** Operator with `MEM0_API_KEY` runs:
```bash
cd /data/workspace/hermes-agent
python scripts/seed_mem0_backend.py --agent-id screenplay --count 500
python scripts/run_latency_benchmark.py --backend mem0 --record-count 500 --runs 100 --out /tmp/bench-live-500.json
```
Then populates `.planning/research/v11-poc-eval/latency-baseline.md §2.2` 500-record row with empirical p50/p95/p99 + Date + Operator. If `slo_verdict == "fail"` (p95 ≥ 500ms), authors `.planning/research/v12-poc-eval/物理分区-triggers.md` with 5 sections per Phase 48 §3.

**Expected:**
- `latency-baseline.md §2.2` 500-record row filled with empirical numbers (replaces TBD).
- If p95 < 500ms: no further doc needed. If p95 ≥ 500ms: `物理分区-triggers.md` exists with 5 sections (`grep -c "^## " 物理分区-triggers.md` returns 5).
- Single doc-update commit on main: `docs(60-01): populate EVAL-01 live mem0 latency baseline (p95=X.Xms, verdict=pass|fail)`.

**Why human:** Requires `MEM0_API_KEY` (operator secret in `~/.hermes/.env`). Cannot run live mem0 Platform API calls from CI or verifier sandbox. Plan 60-01 Task 3 is explicitly `checkpoint:human-verify gate=blocking`.

**Resume signal:** Operator invokes Task 3 of 60-01 explicitly with `MEM0_API_KEY` set; emits one of `approved` / `deferred: <reason>` / `p95-fail: <value>ms`.

---

#### 2. EVAL-02 Real-Mode Fitness Battery Run

**Test:** Operator with `GLM_AUX_API_KEY_1..4` (or `GLM_API_KEY` fallback) runs:
```bash
cd /data/workspace/hermes-agent
# Recommend: systemctl --user stop hermes-gateway.service (frees GLM RPM quota)
python scripts/compute_fitness_baseline.py \
    --battery tests/v11-fitness-battery/scenarios \
    --out /tmp/fitness-baseline-phase60.json 2>&1 | tee /tmp/fitness-baseline-phase60.log
# After: systemctl --user start hermes-gateway.service
```
Then authors `.planning/research/v12-poc-eval/fitness-battery-baseline.md` mirroring `latency-baseline.md` style with 7 sections (criterion, persona-aligned results, generic-LLM results, discrimination analysis, token cost, v12.0 implications verdict, references).

**Expected:**
- `~/.hermes/eval/fitness_trend.jsonl` has 2 new entries with `mode: "persona_aligned"` and `mode: "generic_llm"`, `battery_version: "v1-screenplay-baseline-real"` (no shadow stub markers).
- `.planning/research/v12-poc-eval/fitness-battery-baseline.md` exists with 7 sections (`grep -c "^## " fitness-battery-baseline.md` returns at least 7).
- Verdict recorded in §6: PASS if `delta ≥ 0.3 AND persona mean ≥ 0.7`; `tech_debt` if persona mean < 0.7 but delta ≥ 0.3; `design_concern` if delta < 0.3.
- Expected runtime: ~10-25 min wall-clock, ~400K tokens, ~0.20 CNY at glm-5.2 pricing.
- Single doc commit on main: `docs(60-02): ship EVAL-02 real-mode fitness baseline (persona=X.XX, generic=Y.YY, delta=D.DD, verdict=meaningful|not_meaningful)`.

**Why human:** Requires `GLM_AUX_API_KEY_1..4` (operator secret in `~/.hermes/.env`) + 10-25min wall-clock + ~0.20 CNY spend. Cannot run live GLM API calls from CI or verifier sandbox. Plan 60-02 Task 3 is explicitly `checkpoint:human-verify gate=blocking`. Per MEMORY.md `feedback-glm-overload-reduce-concurrency.md`: global_concurrency == 1; recommend pausing hermes-gateway during the run per MEMORY.md `hermes-gateway-systemd.md`.

**Resume signal:** Operator invokes Task 3 of 60-02 explicitly with GLM aux pool keys provisioned; emits one of `approved` / `partial: <reason>` / `deferred: <reason>`.

### Gaps Summary

**No gaps in the autonomous scope.** Tasks 1+2 of both plans (60-01, 60-02) shipped all infrastructure required for the operator to execute the deferred live runs:

- **EVAL-01 infra:** `_BackendAdapter` singleton + idempotent seeder + `--backend mem0` flag with mutual-exclusion + `--record-count` + `--agent-id`. All call sites wired with keyword args matching the adapter's keyword-only signature. Fixture regression preserved (p95 sub-ms, slo_verdict=pass). Missing-key gate exits 2 with documented message. 19 new tests pass.
- **EVAL-02 infra:** `baseline_mode` kwarg (`None` / `persona_aligned` / `generic_llm`) on `_dispatch_agent` + `run_battery`. `_extract_user_message` + `_load_persona_system_prompt` helpers handle all 8 scenario shapes + persona YAML loading via `hermes_constants.get_hermes_home()` (CLAUDE.md anti-pattern compliant). `BATTERY_VERSION` bumped to `v1-screenplay-baseline-real` to distinguish real-mode from shadow. `compute_fitness_baseline.py` orchestrates both runs sequentially + computes delta + writes JSON. 11 hermetic tests pass.
- **Test gate:** 30/30 tests pass (12 seed_mem0 + 7 run_latency_benchmark + 11 baseline_mode_dispatch).
- **Commits verified:** 5 commits landed — `523b2e425`, `61d56ce7e`, `0820e884e` (60-01); `a988bd4e8`, `0361b6170` (60-02).

**Two operator-action handoffs documented for human verification** (status `human_needed`):

1. EVAL-01 live mem0 benchmark — needs `MEM0_API_KEY`.
2. EVAL-02 live GLM fitness battery — needs `GLM_AUX_API_KEY_1..4`.

Both are formally declared as `checkpoint:human-verify gate=blocking` Task 3 in their respective plans. Neither is a code gap; both are operator-time gaps. The infrastructure is operator-ready: a single CLI command in each case produces the deferred output.

---

_Verified: 2026-07-08T06:15:00Z_
_Verifier: Claude (gsd-verifier)_
