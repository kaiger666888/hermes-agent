# Roadmap: Hermes Agent — Kai's Personal Agent Platform

## Overview

v11.0 (Hermes-Native Expert Agents PoC) shipped 2026-07-07 — implemented the v10.0 design suite as runtime code. **317 automated tests green; audit verdict `passed`; 5 operator-action smoke tests verified (4 PASSED + 1 SHADOW-VERIFIED).**

**v12.0 (Production Hardening)** in progress on `v12.0-dev` branch — fixes 4 hardening gaps exposed by v11.0 real-GLM smoke tests + runs deferred live-backend benchmarks. 5 phases (57-61), 8 reqs, 6.5 person-days.

## Milestones

- ✅ **v1.0 Movie-Experts Suite v2** - Phases 0-6 (shipped 2026-06-15)
- ✅ **v2.0 PRFP Pipeline Design** - Phases 7-12 (shipped 2026-06-16)
- ✅ **v3.0 Skills-to-DAG Alignment** - Phases 13-18 (shipped 2026-06-17)
- ✅ **v4.0 Methodology Backfill** - Phases 19-21 (shipped 2026-06-18)
- ✅ **v5.0 V8.6 Adaptation** - Phases 22-27 (shipped 2026-06-19)
- ✅ **v6.0 Self-Evolution Feedback Loop** - Phases 28-33 (shipped 2026-06-24)
- ✅ **v7.0 openclaw → hermes Migration** - Phases 34-37 (shipped 2026-06-25)
- ✅ **v9.0 kais-movie-pipeline 闭环深化** - Phases 38-43 (shipped 2026-06-27)
- ✅ **v10.0 Hermes-Agent 编排架构第一性原理推导(设计型)** - Phases 44-51 (shipped 2026-07-07, tag `v10.0`)
- ✅ **v11.0 Hermes-Native Expert Agents PoC Implementation** - Phases 52-56 (shipped 2026-07-07, tag `v11.0`)
- 🚧 **v12.0 Production Hardening** - Phases 57-61 (in planning on `v12.0-dev` branch)

---

## v12.0: Production Hardening (In Planning)

**Milestone Goal:** Fix the 4 hardening gaps that v11.0 real-GLM smoke tests exposed + run deferred live-backend benchmarks. v11.0 PoC 已证 round table 跑通, v12.0 把它 production-ready.

**Hardening gaps targeted (from v11.0 smoke-test-report §3):**
1. Synthesis endpoint timeout (z.ai coding plan 30s cap → 5x retry → fallback to anthropic-compat) → ENDPOINT-01
2. RPM rate limit burst (v11.0 only has hardcoded `asyncio.sleep` Strategy A) → THROTTLE-01 + THROTTLE-02
3. Auxiliary traffic shares credential pool with main agent (gateway burst exhausts keys) → POOL-01 + POOL-02
4. Fitness battery real-mode + live mem0 benchmark unrun → EVAL-01 + EVAL-02

**Acceptance budget:** ~6.5 person-days total per REQUIREMENTS.md traceability (8 reqs · 5 phases)

**Scope discipline (cite v11.0 smoke-test-report, do not expand):**
- 复用 v11.0 PoC runtime,只硬化不重写
- 15-expert 全量 transform 留 v13.0
- Curator self-evolution 闭环留 v13.0
- Round table 异步并发 留 v13.0(取决于 GLM 上游容量)

**Phase Numbering:** continues from v11.0 Phase 56 → v12.0 starts at **Phase 57**

## Phases

- [ ] **Phase 57: ENDPOINT-ROUTING** - Long-prompt-aware endpoint routing (synthesis + compaction → anthropic-compat)
- [ ] **Phase 58: RPM-THROTTLING** - Per-task RPM token bucket + per-round-table TPM budget
- [ ] **Phase 59: AUX-POOL-ISOLATION** - Separate auxiliary credential pool + per-key TPM tracking
- [ ] **Phase 60: LIVE-EVAL** - Production mem0 p95 benchmark + fitness battery real-mode baseline
- [ ] **Phase 61: VALIDATE** - Milestone audit + production smoke (target <240s vs v11.0's 490s)

---

## Phase Details

### Phase 57: ENDPOINT-ROUTING

**Goal**: Route long-prompt LLM calls (synthesis, memory_compaction, memory_comparator) to `open.bigmodel.cn/api/anthropic` (anthropic-compat, no 30s cap); keep short-prompt calls (round_table_opinion panelists) on `z.ai/api/coding/paas/v4` (lower cost).
**Depends on**: Nothing (first phase of v12.0)
**Requirements**: ENDPOINT-01
**Success Criteria**:
  1. `auxiliary_client.call_llm` auto-selects endpoint based on prompt token count (threshold configurable, default 4096).
  2. v11.0 SC#2 smoke test latency drops from 490s to <240s.
  3. All v11.0 + v12.0 unit tests pass.
**Plans**:
- [x] 57-01-PLAN.md — Add prompt-length-aware endpoint routing (helper + wire-in + tests + config docs)

### Phase 58: RPM-THROTTLING

**Goal**: Replace v11.0's hardcoded `asyncio.sleep(2.5)` Strategy A with proper rate-aware pacing.
**Depends on**: Phase 57
**Requirements**: THROTTLE-01, THROTTLE-02
**Success Criteria**:
  1. `agent/glm_throttle.py` (NEW) implements token bucket per auxiliary task.
  2. `round_table_open` accepts `token_budget`; budget_warning + budget_exceeded events.
  3. v11.0 SC#2 smoke runs without manual sleep + zero `RateLimitError`.
**Plans**:
- [x] 58-01-PLAN.md — Per-task RPM token bucket (THROTTLE-01): NEW agent/glm_throttle.py + wire-in to auxiliary_client.call_llm + driver script sleep removal
- [x] 58-02-PLAN.md — Per-round-table TPM budget (THROTTLE-02): token_budget field + budget_warning/exceeded events + receipt cost_usd_estimate

### Phase 59: AUX-POOL-ISOLATION

**Goal**: Isolate auxiliary credential pool from main agent pool. Per-key TPM tracking.
**Depends on**: Phase 58
**Requirements**: POOL-01, POOL-02
**Success Criteria**:
  1. `GLM_AUX_API_KEY_1..4` env vars (fallback to `GLM_API_KEY`).
  2. Per-key TPM in sliding 60s window; auto-pick freshest key.
  3. Test verifies pool isolation.
**Plans**:
- [x] 59-01-PLAN.md — Named pools (POOL-01): load_aux_pool + load_named_pool + _seed_aux_env (GLM_AUX_API_KEY_1..4 + GLM_API_KEY fallback) + isolation tests
- [x] 59-02-PLAN.md — Per-key TPM tracking (POOL-02): sliding 60s window + select_freshest_tpm + record_usage + tpm_warning emission in acquire_slot

### Phase 60: LIVE-EVAL

**Goal**: Run deferred v11.0 EVAL handoffs against live backends.
**Depends on**: Phase 59
**Requirements**: EVAL-01, EVAL-02
**Success Criteria**:
  1. Production mem0 p50/p95/p99 in `latency-baseline.md §2.2`.
  2. If p95 > 500ms, document 物理分区 trigger decision.
  3. Fitness battery 8 scenarios real-mode; discrimination baseline (0.7+ vs 0.4-0.5).
**Plans**:
- [x] 60-01-PLAN.md — EVAL-01 live mem0 backend p95 benchmark (NEW seeder + --backend mem0 flag + populate §2.2 + conditional 物理分区-triggers.md)
- [x] 60-02-PLAN.md — EVAL-02 fitness battery real-mode baseline (persona-aligned vs generic-LLM discrimination, aux pool, fitness-battery-baseline.md)

### Phase 61: VALIDATE

**Goal**: v12.0 close-out — audit + production smoke with hardening in place.
**Depends on**: All previous phases (strictly LAST)
**Requirements**: VALIDATE-01
**Success Criteria**:
  1. `.planning/milestones/v12.0-MILESTONE-AUDIT.md` with verdict.
  2. `production-smoke-report.md` shows <240s round table + zero RateLimitError.
  3. Git tag `v12.0`.
**Plans**:
- [ ] 61-01-PLAN.md — VALIDATE-01 milestone audit + production smoke (extend run_milestone_audit.py with --milestone v12.0 + author v12.0-MILESTONE-AUDIT.md + author production-smoke-report.md + update REQUIREMENTS.md traceability)

---

---

## Shipped Milestone Details

<details>
<summary>✅ v11.0 Hermes-Native Expert Agents PoC Implementation (Phases 52-56) - SHIPPED 2026-07-07</summary>

**Stats:** 5 phases · 12 plans · 128 commits · 149 files · 39,256 insertions · 15/15 reqs ✓ · Tag `v11.0` · Audit `passed`

**One sentence:** Implemented the v10.0 design suite as runtime code — agent registry + 7 MCP tools + round table state machine + serial executor + 9 sample agent YAMLs + screenplay Step 3 driver + memory conflict arbitration + 7 acceptance criteria (fitness battery, latency SLO, bias canary, compaction, threshold tuning, dry-run-first, schema migration dry-run).

| Phase | Name | Status |
|-------|------|--------|
| 52 | INFRA-FOUNDATION — agent registry + 7 MCP tools + state machine + serial enforcement | SHIPPED (4 plans, 2026-07-07) |
| 53 | CREATIVE-SLICE — 9 agent YAMLs + Step 3 round table + conflict arbitration | SHIPPED (3 plans, 2026-07-07) |
| 54 | EVAL-HARNESS-1 — fitness battery + latency SLO + bias canary | SHIPPED (3 plans, 2026-07-07) |
| 55 | EVAL-HARNESS-2 — compaction + threshold tuning + dry-run-first + schema migration | SHIPPED (4 plans, 2026-07-07) |
| 56 | VALIDATE — milestone audit + smoke test report | SHIPPED (1 plan, 2026-07-07) |

See `.planning/milestones/v11.0-ROADMAP.md` for full archive + `.planning/milestones/v11.0-MILESTONE-AUDIT.md` for audit (status: passed, 15/15 reqs, 5 operator-action handoffs deferred per VALIDATE-01 spec).

</details>

<details>
<summary>✅ v10.0 Hermes-Agent 编排架构第一性原理推导 (Phases 44-51) - SHIPPED 2026-07-07</summary>

**Stats:** 8 phases · 8 plans · 9/9 reqs ✓ · Tag `v10.0` · Design-only (zero code changes)

**One sentence:** 从第一性原理推导 Hermes 三层编排架构(总调度器 + native expert agents + CC 执行场),产 7 design docs + 3 schemas + 1 lint script,作为 v11.0 PoC 实施蓝本。

| Phase | Name | Status |
|-------|------|--------|
| 44 | FIRST-PRINCIPLES — 7 决策推导 + 显式拒绝总表 | SHIPPED (Plan 01, 2026-07-06) |
| 45 | AGENT-SCHEMA — 18-field YAML + memory-record-schema | SHIPPED (Plan 01, 2026-07-06) |
| 46 | ROUND-TABLE-PROTOCOL — Turn lifecycle + conflict arbitration | SHIPPED (Plan 01, 2026-07-06) |
| 47 | KIMI-COMPARISON — T6 vs Kimi 7-dim contrast | SHIPPED (Plan 01, 2026-07-06) |
| 48 | CROSS-REPO-IMPACT — 3-location sync + Option B vs partition | SHIPPED (Plan 01, 2026-07-06) |
| 49 | MIGRATION-PATH — 15 expert transform + memory migration | SHIPPED (Plan 01, 2026-07-06) |
| 50 | POC-PLAN — v11.0 PoC acceptance criteria + risk register | SHIPPED (Plan 01, 2026-07-06) |
| 51 | VALIDATE — Cross-doc lint + milestone audit | SHIPPED (Plan 01, 2026-07-07) |

See `.planning/milestones/v10.0-ROADMAP.md` for full archive + `.planning/milestones/v10.0-MILESTONE-AUDIT.md` for audit.

</details>

<details>
<summary>✅ v9.0 kais-movie-pipeline 闭环深化 (Phases 38-43) - SHIPPED 2026-06-27</summary>

**Stats:** 6 phases · 13 plans · 22/22 reqs ✓ · Tag `v9.0` (anchored at `599ef61a8`)

**One sentence:** 把 Notion "创作方向" Tier B+C 落地为 kais-movie-pipeline 的 4 个新能力(平台母版切片 / 配方库 v0 / LTX2.3 预览闭环 / 数据收敛回流)+ 3 个跨平台红线审核门,完成「创意→生产→分发→反馈」全闭环。

See `.planning/milestones/v9.0-MILESTONE-AUDIT.md` for full audit.

</details>

<details>
<summary>✅ v7.0 openclaw → hermes Migration (Phases 34-37) - SHIPPED 2026-06-25</summary>

</details>

---

*Last updated: 2026-07-08 — Phase 61 (VALIDATE) planned: 1 plan, 3 tasks, VALIDATE-01. v12.0 milestone audit + production smoke close-out (strictly LAST phase). Next: `/gsd:execute-phase 61` then operator §3 handoffs + git tag v12.0.*
