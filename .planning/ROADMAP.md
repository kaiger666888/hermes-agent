# Roadmap: Hermes Agent — Kai's Personal Agent Platform

## Overview

v10.0 (design-only milestone) shipped 2026-07-07 — Hermes-Agent orchestrator + Hermes-native expert agents + Claude Code execution场 three-layer architecture derived from first principles. **v11.0 is the implementation milestone** that turns the v10.0 design suite (`00-FIRST-PRINCIPLES` through `06-CROSS-REPO-IMPACT` + 3 schemas + 1 lint script) into runtime code: 2 vertical slices (infra + creative) + 7 acceptance criteria. Phases 52-56 implement the v10.0 PoC blueprint per `.planning/research/v10-orchestrator-design/05-POC-PLAN.md` §3-§6.

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
- 🚧 **v11.0 Hermes-Native Expert Agents PoC Implementation** - Phases 52-56 (in planning)

---

## v11.0: Hermes-Native Expert Agents PoC Implementation (In Planning)

**Milestone Goal:** 按 v10.0 设计套件实施 vertical slice(1 creative phase + 1 infra phase),验证三层架构 runtime 可行性。v11.0 是 v10.0 设计的**实施 milestone** —— 不再产出设计文档,而是把 `00-FIRST-PRINCIPLES` 到 `06-CROSS-REPO-IMPACT` 的设计落地为 Python 代码 + agent YAML + mem0 extensions。

**Vertical slice (per `05-POC-PLAN.md` §3):**
- **Creative slice:** screenplay Step 3 round table(9-agent HOOK-09 edge case)
- **Infra slice:** agent registry + 1 round table invocation(7 MCP tool wire-up)

**Acceptance budget:** ~12-17 person-days total per `05-POC-PLAN.md` §2.4 + REQUIREMENTS.md traceability(15 reqs · 19.5 person-days incl. MIGR-01 + close-out)

**Scope discipline (cite v10.0, do not re-derive):**
- 复用 v10.0 设计,不重新推导 7 决策(cite `00-FIRST-PRINCIPLES.md` §2)
- 强制串行(1 panelist 1 turn `await`)兼容 GLM 4-key rotation(INFRA-04 hard constraint)
- dry-run-first invariant(curator 默认 dry-run,所有 schema 迁移默认 dry-run,EVAL-06 hard constraint)
- Phase 56 VALIDATE strictly LAST(类比 v10.0 Phase 51 / v5.0 Phase 27 close-out pattern)

**Phase Numbering:** continues from v10.0 Phase 51 → v11.0 starts at **Phase 52**. Decimal phases reserved for urgent insertions only.

## Phases

- [ ] **Phase 52: INFRA-FOUNDATION** - Agent registry YAML loader + 7 MCP tools wire-up + round table state machine + serial execution enforcement
- [ ] **Phase 53: CREATIVE-SLICE** - 9 sample agent YAMLs (MIGR-01) + screenplay Step 3 round table end-to-end + memory conflict arbitration runtime
- [ ] **Phase 54: EVAL-HARNESS-1** - Fitness battery design + latency SLO p95<500ms + bias canary(curator hallucination detection)
- [ ] **Phase 55: EVAL-HARNESS-2** - Compaction pass + threshold tuning + dry-run-first invariant + schema migration dry-run
- [ ] **Phase 56: VALIDATE** - Milestone audit + vertical slice end-to-end smoke test(strictly LAST)

---

## Phase Details

### Phase 52: INFRA-FOUNDATION
**Goal**: Build the Hermes-side runtime layer that loads agent YAMLs, wires the 7 MCP tools into `mcp_serve.py`, persists round table state with crash recovery, and enforces the hard serial-execution constraint — so that downstream phases (53-55) can build creative + eval artifacts on a working registry + state machine foundation.
**Depends on**: Nothing (first phase of v11.0; consumes v10.0 design suite as blueprint)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04
**Success Criteria** (what must be TRUE):
  1. A user can place a YAML at `~/.hermes/agents/{name}.agent.yaml` and `agents_list` MCP tool returns it; a malformed YAML is rejected by Phase 45 `agents-schema.yaml` with a specific schema-violation error message.
  2. A Claude Code (or other MCP client) round trip through `round_table_open` → 1 `get_agent_opinion` → `submit_round_table_result` lifecycle completes end-to-end against a single synthetic agent; the lifecycle is atomic (interrupted submit does not leave `status: in_progress`).
  3. A `round_table_open` invocation that crashes mid-turn (3 failure modes: partial-write, mid-turn crash, orphaned session) recovers on next access — the state machine transitions cleanly to `closed` or `error` without operator hand-intervention.
  4. A concurrent second `get_agent_opinion` submission against the same `roundId` is **rejected** with a clear serial-violation error (cites `feedback-glm-overload-reduce-concurrency.md`); a single sequential submission proceeds and returns the panelist opinion successfully.
**Plans**: 4 plans across 3 waves (Wave 1: 52-01; Wave 2: 52-02 + 52-03 parallel; Wave 3: 52-04)

Plans:
- [ ] 52-01-PLAN.md — INFRA-01 Agent Registry YAML Loader (registry_loader.py + jsonschema validation + lazy cache)
- [ ] 52-02-PLAN.md — INFRA-03 Round Table State Machine (open/append/submit + atomic writes + 3 crash-recovery modes)
- [ ] 52-03-PLAN.md — INFRA-02 7 MCP Tools Wire-up (FastMCP closures in mcp_serve.py + memory_arbitration stub)
- [ ] 52-04-PLAN.md — INFRA-04 Serial Execution Enforcement (per-roundId asyncio.Lock + 429 + MEMORY.md citation)

---

### Phase 53: CREATIVE-SLICE
**Goal**: Deliver the creative vertical slice end-to-end — transform 9 sample movie-expert SKILL.md to agent YAML (sufficient for screenplay Step 3 round table), wire the 9-agent round table invocation lifecycle, and implement memory conflict arbitration — so that a real GLM API call can produce a screenplay Step 3 artifact via round table deliberation.
**Depends on**: Phase 52 (consumes agent registry loader + 7 MCP tools + state machine + serial executor)
**Requirements**: MIGR-01, CREATIVE-01, CREATIVE-02
**Success Criteria** (what must be TRUE):
  1. 9 agent YAML files at `~/.hermes/agents/*.agent.yaml` validate against Phase 45 `agents-schema.yaml` (camelCase keywords, 18 fields, lineage block populated with `derived_from_skill_id` + `skill_sha256`); the transform log documents which SKILL frontmatter field mapped to which agent YAML field per Phase 49 §2 75-cell rules.
  2. Running `scripts/run_screenplay_step3_roundtable.py` produces a JSON artifact that validates against the screenplay Step 3 schema (HOOK-09 emotion_curve marker contract), with latency < 30s on a real GLM API call (no mocks), exercising the full `round_table_open` → 9 sequential `get_agent_opinion` calls → 1 `submit_round_table_result` lifecycle.
  3. A 2-conflict test scenario (e.g. cinematographer asserts false vs. style_genome dissents) produces the correct arbitration outcome per Phase 46 §3 contract: comparator LLM pass detects the conflict, `session > project > global` scope precedence is honored, confidence-weighted voting picks a winner, and an entry is appended to `.runtime/{slug}/round_tables/{round_id}/conflicts.jsonl`.
**Plans**: TBD

Plans:
- [ ] 53-01: TBD

---

### Phase 54: EVAL-HARNESS-1
**Goal**: Build the first wave of PoC acceptance criteria — fitness battery (P1/P8 mitigation), latency SLO benchmark (Option B mem0 filter viability gate), and bias canary (curator `_memory_evolution_phase` hallucination detector) — so the runtime produced in Phases 52-53 has measurable regression-detection + safety guards before any curator tick is allowed to transition from dry-run to live.
**Depends on**: Phase 53 (consumes running vertical slice + memory layer + curator hook points)
**Requirements**: EVAL-01, EVAL-02, EVAL-03
**Success Criteria** (what must be TRUE):
  1. A user can run `scripts/run_fitness_battery.py` and get a per-scenario score for each of the 5-10 battery scenarios (screenplay Step 3 quality + conflict resolution correctness dimensions); the battery persists to `tests/v11-fitness-battery/` as data files with expected-output + scoring rubric, and produces a baseline `fitness_trend.jsonl` entry.
  2. A user can run the latency benchmark and observe `memory_retrieve_scoped` MCP tool p95 latency **< 500ms** across 100 sequential retrievals on a populated 500-record memory store (excluding LLM call); the benchmark is instrumented in code, produces a results JSON + `.planning/research/v11-poc-eval/latency-baseline.md` documenting baseline + bottleneck analysis.
  3. A user can run `scripts/run_bias_canary.py` and observe that 4/5 known-bad synthetic memory records (low `evidence_chain`, low `confidence`, unsupported claims) are flagged by the curator `_memory_evolution_phase` in dry-run mode; the bias canary is wired as an extension of `agent/curator.py` and emits a canary report.
**Plans**: TBD

Plans:
- [ ] 54-01: TBD

---

### Phase 55: EVAL-HARNESS-2
**Goal**: Build the second wave of PoC acceptance criteria — compaction pass, threshold tuning documentation, dry-run-first invariant enforcement, and schema migration dry-run script — so that memory tiering works at scale, defaults are documented for v12.0 operators, curator + migration tools default to safe dry-run mode (P5/P14 mitigation), and v6.0 FeedbackStore JSONL can be migrated without silent drops.
**Depends on**: Phase 54 (consumes fitness battery as regression-detection foundation; per `05-POC-PLAN.md` §6.1 implementation path: fitness battery FIRST → schema migration dry-run SECOND → bias canary THIRD — bias canary already done in 54, this phase completes the remaining items)
**Requirements**: EVAL-04, EVAL-05, EVAL-06, EVAL-07
**Success Criteria** (what must be TRUE):
  1. Triggering compaction at exactly `memory.max_records=500` produces a valid post-compaction 3-tier state (core ≤10 / working ≤100 / archival ≤10000); oldest archival-tier records are archived and working-tier is summarized into core-tier per Phase 46 memory tiering contract.
  2. The 3 thresholds (`memory.max_records`, `confidence_threshold_for_promotion`, `evidence_chain_min_for_acceptance`) are documented with initial defaults (from v10.0 schemas) + tuning methodology for v12.0 operators in `.planning/research/v11-poc-eval/threshold-tuning.md`; the config schema fields are verified present in `agents-schema.yaml`.
  3. Invoking curator without explicit `dry_run: false` flag and invoking `scripts/migrate_v6_feedback_to_memory_schema.py` without `--apply` flag both produce **zero** state mutation (no memory writes, no schema migration writes); dry-run-first is enforced as a default value in code, not just a CLI convention.
  4. Running `scripts/migrate_v6_feedback_to_memory_schema.py --dry-run` on a sample v6.0 FeedbackStore JSONL produces a diff report (what would change) without writing; the dry-run output accounts for every source record (zero silent drops, P14 mitigation); the output format matches `.planning/research/v11-poc-eval/migration-dry-run-format.md` spec.
**Plans**: TBD

Plans:
- [ ] 55-01: TBD

---

### Phase 56: VALIDATE
**Goal**: v11.0 milestone close-out — audit all 15 requirements satisfied, run the vertical slice end-to-end smoke test on real GLM API (no mocks), publish latency benchmark + bias canary report, and produce milestone audit verdict (PASS / tech_debt / FAIL).
**Depends on**: All previous phases (52-55), **strictly LAST**(analog to v10.0 Phase 51 / v5.0 Phase 27 close-out pattern; cannot run until all deliverables exist).
**Requirements**: VALIDATE-01
**Success Criteria** (what must be TRUE):
  1. `.planning/milestones/v11.0-MILESTONE-AUDIT.md` exists and verifies **15/15** requirements satisfied (INFRA-01..04 + CREATIVE-01..02 + EVAL-01..07 + MIGR-01 + VALIDATE-01), with per-req evidence pointers to deliverables (file paths + commit SHAs).
  2. `.planning/research/v11-poc-eval/smoke-test-report.md` exists documenting the vertical slice end-to-end run on a real GLM API call (no mocks) — round_table_open → 9 panelists → submit_round_table_result — with the screenplay Step 3 JSON artifact attached and timestamped.
  3. Audit verdict is `passed` or `tech_debt` (not `failed`); any `tech_debt` items are documented with v12.0+ deferral rationale + operator-action-handoff notes (analog to v9.0 close-out operator handoffs).
**Plans**: TBD

Plans:
- [ ] 56-01: TBD

---

## Critical Path & Dependencies

```
                                                                                              ┌──────────────────────┐
                                                                                              │ Phase 56 (VALIDATE)   │
                                                                                              │ strictly LAST         │
                                                                                              └──────────▲───────────┘
                                                                                                         │
                                                                                ┌──── Phase 55 (EVAL-2) ─┘
                                                                                │   compaction + tuning +
                                                                                │   dry-run-first + migration
                                                                                │
                                                  ┌──── Phase 54 (EVAL-1) ─────┘
                                                  │   fitness battery + latency +
                                                  │   bias canary
                                                  │
                  ┌──── Phase 53 (CREATIVE) ─────┘
                  │   9 agent YAMLs + round table +
                  │   conflict arbitration
                  │
Phase 52 ─────────┘
(INFRA-FOUNDATION)
agent registry + 7 MCP tools +
state machine + serial enforcement
```

**Critical path:** 52 → 53 → 54 → 55 → 56 (5 sequential steps; no parallel waves — runtime implementation milestone, each phase consumes prior phase's code).

**Hard dependencies:**
- Phase 53 (CREATIVE-SLICE) → needs Phase 52 (INFRA) agent registry + 7 MCP tools + state machine + serial executor
- Phase 54 (EVAL-1) → needs Phase 53 vertical slice running (fitness battery scores screenplay output, latency benchmarks memory layer populated by creative slice)
- Phase 55 (EVAL-2) → needs Phase 54 fitness battery as regression-detection foundation (per `05-POC-PLAN.md` §6.1 sequencing rationale)
- Phase 56 (VALIDATE) → strictly LAST; runs cross-phase audit + smoke test on all prior deliverables

**Implementation path alignment (per `05-POC-PLAN.md` §6.1):**
The v10.0 PoC plan specifies fitness battery FIRST → schema migration dry-run SECOND → bias canary THIRD as the implementation sequence. This roadmap adapts that sequence to phase structure where INFRA (Phase 52) + CREATIVE (Phase 53) come first because they produce the runtime that the eval harness then measures. Within the EVAL phases:
- Phase 54 covers fitness battery (FIRST in §6.1) + bias canary (THIRD in §6.1) + latency SLO
- Phase 55 covers compaction + tuning + dry-run-first + schema migration dry-run (SECOND in §6.1)

The `05-POC-PLAN.md` §6.1 sequence rationale (fitness battery = regression-detection foundation must exist before any curator tick) is preserved: Phase 54 ships before Phase 55.

---

## Progress

**Execution Order:**
Phases execute in numeric order: 52 → 53 → 54 → 55 → 56 (no decimal insertions planned; no parallel waves).

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 52. INFRA-FOUNDATION | 0/TBD | Not started | - |
| 53. CREATIVE-SLICE | 0/TBD | Not started | - |
| 54. EVAL-HARNESS-1 | 0/TBD | Not started | - |
| 55. EVAL-HARNESS-2 | 0/TBD | Not started | - |
| 56. VALIDATE | 0/TBD | Not started | - |

---

## Shipped Milestone Details

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

See `.planning/milestones/v10.0-ROADMAP.md` for full archive + `.planning/v10.0-MILESTONE-AUDIT.md` for audit (status: passed, 9/9 reqs, 8/8 phases, design-only).

</details>

<details>
<summary>✅ v9.0 kais-movie-pipeline 闭环深化 (Phases 38-43) - SHIPPED 2026-06-27</summary>

**Stats:** 6 phases · 13 plans · 22/22 reqs ✓ · Tag `v9.0` (anchored at `599ef61a8`)

**One sentence:** 把 Notion "创作方向" Tier B+C 落地为 kais-movie-pipeline 的 4 个新能力(平台母版切片 / 配方库 v0 / LTX2.3 预览闭环 / 数据收敛回流)+ 3 个跨平台红线审核门,完成「创意→生产→分发→反馈」全闭环。

| Phase | Name | Status |
|-------|------|--------|
| 38 | SLICE — 平台母版切片 (Step 14) | SHIPPED (Plan 01, 2026-06-27) |
| 39 | FORM — 配方库 v0 (new plugin) | SHIPPED (Plans 01+02+03, 2026-06-27) |
| 40 | GATE — 3 新审核门 | SHIPPED (Plans 01+02+03, 2026-06-26) |
| 41 | PREVIEW — LTX2.3 Step 6.5 | SHIPPED (Plan 01, 2026-06-27) |
| 42 | DATA — 数据收敛 (Step 15) | SHIPPED (Plans 01+02+03+04, 2026-06-27) |
| 43 | VALIDATE — 集成验证 + close-out | SHIPPED (Plan 01, 2026-06-27) |

See `.planning/milestones/v9.0-MILESTONE-AUDIT.md` for full audit (status: passed, 22/22 reqs, 6/6 phases, FOUND-08 preserved milestone-wide).

</details>

<details>
<summary>✅ v7.0 openclaw → hermes Migration (Phases 34-37) - SHIPPED 2026-06-25</summary>

**Stats:** 4 phases · 7 plans · 14/14 reqs ✓ · Tag `v7.0`

| Phase | Name | Status |
|-------|------|--------|
| 34 | Skills Migration (coding-agent + tmux-agents) | SHIPPED |
| 35 | SOUL.md Identity Enhancement | SHIPPED |
| 36 | Memory Ingestion (USER.md + mem0 scripts) | SHIPPED |
| 37 | Validation + Migration Report | SHIPPED |

</details>

<details>
<summary>✅ v6.0 Self-Evolution Feedback Loop (Phases 28-33) - SHIPPED 2026-06-24</summary>

**Stats:** 6 phases · 13 plans · 26/26 reqs ✓ · Tag `v6.0`

| Phase | Name | Status |
|-------|------|--------|
| 28 | INGEST — Multi-source Feedback | SHIPPED |
| 29 | STORE — Durable FeedbackStore | SHIPPED |
| 30 | GATE — Eval gate | SHIPPED |
| 31 | EVOL — Knowledge evolution | SHIPPED |
| 32 | CURATE — Curator upgrade + EVOL-02 | SHIPPED |
| 33 | OBS — Observability + close-out | SHIPPED |

</details>

<details>
<summary>✅ Earlier milestones (v1-v5) - SHIPPED 2026-06-15 → 2026-06-19</summary>

- **v5.0 V8.6 Adaptation** (Phases 22-27, shipped 2026-06-19): 30/30 reqs ✓
- **v4.0 Methodology Backfill** (Phases 19-21, shipped 2026-06-18): 14/14 reqs ✓
- **v3.0 Skills-to-DAG Alignment** (Phases 13-18, shipped 2026-06-17): 12/12 reqs ✓
- **v2.0 PRFP Pipeline Design** (Phases 7-12, shipped 2026-06-16): 52/52 reqs ✓ (design-only)
- **v1.0 Movie-Experts Suite v2** (Phases 0-6, shipped 2026-06-15): all v1 reqs ✓

</details>

---

*Last updated: 2026-07-07 — v11.0 PoC roadmap created (15 reqs mapped across Phases 52-56). Phase 56 VALIDATE strictly LAST per v10.0 precedent. Awaiting user approval to start planning Phase 52 (INFRA-FOUNDATION).*
