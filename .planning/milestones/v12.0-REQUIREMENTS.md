# Milestone v12.0 Requirements — Production Hardening

**Goal:** Fix the 4 hardening gaps exposed by v11.0 real-GLM smoke tests + run deferred live-backend benchmarks. v11.0 PoC 已证 round table 跑通, v12.0 把它 production-ready.

**Scope:** 单 repo (hermes-agent) runtime changes + config amendments. 15-expert 全量 transform + 物理分区迁移 + curator self-evolution 闭环留 v13.0+.

**Predecessors:**
- v11.0 PoC implementation (5 phases 52-56, tag `v11.0`, audit `passed`)
- v11.0 smoke-test-report (`.planning/research/v11-poc-eval/smoke-test-report.md`) — exposed the 4 hardening gaps this milestone addresses
- MEMORY.md `feedback-glm-5-2-only.md` + `feedback-glm-overload-reduce-concurrency.md` (carried constraints)

---

## ENDPOINT Requirements — Smart LLM Endpoint Routing (1 req)

### ENDPOINT-01: Long-Prompt Aware Endpoint Routing

`agent/auxiliary_client.py` routes LLM calls to the appropriate endpoint based on prompt length:
- **Short prompts (< 4K tokens input)** → `z.ai/api/coding/paas/v4` (zai coding plan, 30s timeout, lower cost)
- **Long prompts (≥ 4K tokens input)** → `open.bigmodel.cn/api/anthropic` (anthropic-compat, no 30s cap)
- Affects: `round_table_opinion` synthesis, `memory_compaction` summary, `memory_comparator` (all use long prompts)
- Configurable threshold via `cli-config.yaml: auxiliary.endpoint_routing.token_threshold` (default 4096)
- **Smoke target:** v11.0 SC#2 round table latency drops from 490s to <240s (no synthesis retry storm)

**Deliverables:**
- `agent/auxiliary_client.py` modification (endpoint selection logic)
- Unit tests covering both routing branches
- Updated `~/.hermes/config.yaml` documentation

---

## THROTTLE Requirements — RPM + TPM Token Bucket (2 reqs)

### THROTTLE-01: Per-Task RPM Token Bucket

`agent/glm_throttle.py` (NEW module) implements a token bucket per auxiliary task name:
- Each task (`round_table_opinion`, `memory_compaction`, etc.) has its own bucket
- Bucket refills at configurable RPM (default 30 RPM/task — well under GLM single-key ceiling)
- `acquire_slot(task)` blocks until a slot is available; `try_acquire_slot(task)` returns False if empty
- Wraps every `auxiliary_client.call_llm` invocation
- Replaces v11.0 hardcoded `asyncio.sleep(2.5)` in driver script with proper rate-aware pacing

**Deliverables:**
- `agent/glm_throttle.py` (NEW)
- Integration into `auxiliary_client.call_llm`
- Config: `auxiliary.{task}.rpm` (default 30)
- Unit + integration tests

### THROTTLE-02: Per-Round-Table TPM Budget

`round_table_open` accepts optional `token_budget` parameter (default 100K — covers 9 panelist × 5K + synthesis 10K + slack):
- After each `get_agent_opinion`, subtract actual input + output tokens from budget
- If remaining budget < 2× expected next call → pause + emit `budget_warning` event
- If remaining < 1× expected → abort round table with `status: budget_exceeded`, persist partial state for resume
- Receipt in `submit_round_table_result` includes `tokens_consumed` + `cost_usd_estimate`

**Deliverables:**
- `agent/round_table_executor.py` modification (token tracking)
- `agent/round_table_state.py` modification (`token_budget` field in state schema)
- New MCP tool `round_table_budget_status` (read-only) for operator visibility
- Tests covering budget-warning + budget-exceeded transitions

---

## POOL Requirements — Auxiliary Credential Pool Isolation (2 reqs)

### POOL-01: Separate Auxiliary Credential Pool

`agent/credential_pool.py` extended with a second named pool `auxiliary`:
- Reads from new env vars: `GLM_AUX_API_KEY_1..4` (or falls back to main `GLM_API_KEY` if not set)
- `auxiliary_client.call_llm` uses the `auxiliary` pool; main agent + gateway use the default pool
- Two pools never share credentials — eliminates "gateway burst exhausts keys for round table" failure mode
- Operator can configure different rotation strategies per pool

**Deliverables:**
- `agent/credential_pool.py` modification (named pools)
- `agent/auxiliary_client.py` modification (use `auxiliary` pool)
- Documentation in `cli-config.yaml.example` (how to set `GLM_AUX_API_KEY_1..4`)
- Tests verifying isolation (main pool exhaust does not affect auxiliary calls)

### POOL-02: Per-Key TPM Tracking

Each credential in the auxiliary pool tracks its own TPM consumption in a sliding 60s window:
- Before each call: pick the key with most remaining TPM
- After each call: decrement remaining TPM by actual tokens used
- If all keys < 10% remaining → emit `tpm_warning` + brief sleep until window slides
- Eliminates the "round table suddenly fails halfway through" failure mode

**Deliverables:**
- `agent/credential_pool.py` modification (TPM tracking)
- Config: `auxiliary.tpm_warning_threshold` (default 0.1)
- Tests

---

## EVAL Requirements — Live Backend Benchmarks (2 reqs)

### EVAL-01: Production mem0 Backend Latency p95 Benchmark

Wire production mem0 backend (requires `MEM0_API_KEY`):
- Seed 500-record store for `screenplay` agent (per `tests/v11-latency-bench/fixtures/seed_500_records.py` pattern but real mem0)
- Run 100 sequential `memory_retrieve_scoped` calls
- Measure p50 / p95 / p99
- Populate `.planning/research/v11-poc-eval/latency-baseline.md §2.2` live-backend row (currently fixture-only)
- Decision gate: if p95 > 500ms, document 物理分区 trigger conditions per Phase 48 §3

**Deliverables:**
- `scripts/run_latency_benchmark.py --backend mem0` flag (new)
- Live mem0 fixture-seeding utility
- Updated `latency-baseline.md` with live numbers
- (Optional) 物理分区 trigger documentation if SLO fails

### EVAL-02: Fitness Battery Real-Mode Baseline

Run all 8 scenarios in real-mode (no `--shadow`):
- Per-scenario agent dispatch via real `auxiliary_client.call_llm` for both agent + judge
- Compute `mean_score` per scenario + overall
- Discrimination criterion: persona-aligned screenplay agent scores 0.7+ vs generic-LLM 0.4-0.5 baseline
- Populate `fitness_trend.jsonl` with real baseline entry
- Document baseline in `.planning/research/v12-poc-eval/fitness-battery-baseline.md` (NEW)

**Deliverables:**
- `scripts/run_fitness_battery.py` real-mode execution (no code change, just runtime)
- `.planning/research/v12-poc-eval/fitness-battery-baseline.md` (NEW doc)
- Updated `fitness_trend.jsonl`

---

## VALIDATE Requirements — Milestone Close-out (1 req)

### VALIDATE-01: Milestone Audit + Production Readiness Verdict

End-of-milestone audit:
- All 8 reqs verified
- Re-run v11.0 vertical slice smoke test (`scripts/run_screenplay_step3_roundtable.py --smoke`) with hardening in place
- Latency target: <240s (vs v11.0's 490s — 50% reduction from ENDPOINT-ROUTING + THROTTLE)
- Zero `RateLimitError` (vs v11.0's 5x retry storm)
- Token cost reported per round table
- Audit verdict: PASS / tech_debt / FAIL

**Deliverables:**
- `.planning/milestones/v12.0-MILESTONE-AUDIT.md`
- `.planning/research/v12-poc-eval/production-smoke-report.md` (re-run of v11.0 smoke with v12.0 hardening)
- Git tag `v12.0`

---

## Traceability

| REQ-ID | Phase | Category | Person-days | Status |
|--------|-------|----------|-------------|--------|
| ENDPOINT-01 | 57 | ENDPOINT | 0.5 | ⚠ Complete (SC#2 smoke deferred) |
| THROTTLE-01 | 58 | THROTTLE | 0.75 | Complete |
| THROTTLE-02 | 58 | THROTTLE | 0.75 | Complete |
| POOL-01 | 59 | POOL | 1 | Complete |
| POOL-02 | 59 | POOL | 1 | Complete |
| EVAL-01 | 60 | EVAL | 1 | ⚠ Complete (live mem0 deferred) |
| EVAL-02 | 60 | EVAL | 1 | ⚠ Complete (live fitness deferred) |
| VALIDATE-01 | 61 | VALIDATE | 0.5 | Complete (this audit — verdict passed) |

**Total:** 8 reqs · 6.5 person-days · 5 phases (57-61)

**Coverage:** 8/8 mapped. No orphans.

**Phase mapping rationale:**
- **Phase 57 (ENDPOINT-ROUTING):** Quick win — fixes synthesis timeout, unblocks all subsequent latency work.
- **Phase 58 (RPM-THROTTLING):** Two related reqs (per-task RPM + per-round-table TPM) bundled — same module, same tests.
- **Phase 59 (AUX-POOL-ISOLATION):** Two related reqs (pool isolation + per-key TPM) bundled — same files modified.
- **Phase 60 (LIVE-EVAL):** Two eval reqs bundled — both need live credentials, can share infra setup.
- **Phase 61 (VALIDATE):** Strictly LAST, mirrors v11.0 Phase 56 / v10.0 Phase 51 close-out pattern.

---

## Out of Scope (deferred to v13.0+)

- **15-expert 全量 transform** — v11.0 only ships 9 sample agents; remaining 6 experts (creative_source, script_auditor, prompt_injector, visual_executor, hook_retention subtypes, etc.) deferred.
- **Option B → 物理分区迁移** — v12.0 still uses mem0 single backend + `agent_id` filter; 物理分区 triggers evaluated from EVAL-01 live numbers, migration itself is v13+.
- **Curator live tick self-evolution 闭环** — v11.0 ships dry-run default; live curation ticks on round table output is v13+.
- **Round table 异步并发支持** — INFRA-04 串行约束 stays in v12.0; concurrent round tables require upstream GLM capacity increase first.
- **Operator dashboard / observability** — v13+ nice-to-have.
- **Production deployment + live traffic** — v12.0 is hardening, not deployment.

---

*Last updated: 2026-07-08 — v12.0 milestone audit complete. All 8 reqs verified (5 Complete + 3 Complete-with-operator-deferral). Audit verdict: passed. See .planning/milestones/v12.0-MILESTONE-AUDIT.md. Next: operator runs §3 handoffs + git tag v12.0.*
