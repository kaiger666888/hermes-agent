---
gsd_state_version: 1.0
milestone: v12.0
milestone_name: Production Hardening
status: ready_to_plan
last_updated: 2026-07-07T21:47:33.643Z
last_activity: 2026-07-07 -- Phase 60 execution started
progress:
  total_phases: 5
  completed_phases: 3
  total_plans: 7
  completed_plans: 23
  percent: 60
stopped_at: Phase 60 complete (2/2) — ready to discuss Phase 61
---

# State: Hermes Agent — Kai's Personal Agent Platform

## Project Reference

**Project code:** MESV2 (historical; v7.0+ broadens scope beyond movie-experts)
**Name:** Hermes Agent — Kai's Personal Agent Platform
**Core value:** 让 hermes-agent 成为 Kai 的主 agent:既承载 movie-experts 这样的领域专家子系统(v1-v6 已 shipped),也具备通用 agent 必备的代码委派、自动化集成、文档协作、个人身份与记忆能力(v7.0 迁移目标)。v10.0 推导 Hermes 总调度器 + Hermes-native expert agents + CC 执行场的三层编排架构。**v11.0 是 v10.0 设计的实施 milestone** —— 把设计落地为运行时代码。
**Key docs:** `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/MILESTONES.md`, `.planning/REQUIREMENTS.md`, `.planning/research/v10-orchestrator-design/05-POC-PLAN.md`(THE implementation blueprint)
**Mode:** yolo (auto-advance, parallelization on)
**Granularity:** standard
**Model profile:** quality
**Current focus:** Phase 61 — validate

## Current Position

Phase: 61
Plan: Not started
Status: Ready to plan
Last activity: 2026-07-07

### Progress

```
v1 movie-experts:                [██████████] 100% (Phases 0-6, shipped 2026-06-15)
v2.0 PRFP design:                [██████████] 100% (Phases 7-12, shipped 2026-06-16)
v3.0 Skills-to-DAG:              [██████████] 100% (Phases 13-18, shipped 2026-06-17)
v4.0 Methodology Backfill:       [██████████] 100% (Phases 19-21, shipped 2026-06-18)
v5.0 V8.6 Adaptation:            [██████████] 100% (Phases 22-27, shipped 2026-06-19)
v6.0 Self-Evolution Feedback:    [██████████] 100% (Phases 28-33, shipped 2026-06-24)
v7.0 openclaw → hermes Migration:[██████████] 100% (Phases 34-37, shipped 2026-06-25)
v9.0 kais-movie-pipeline 闭环深化:[██████████] 100% (Phases 38-43, shipped 2026-06-27)
v10.0 Hermes-Agent 编排架构(设计型):[██████████] 100% (Phases 44-51, shipped 2026-07-07, tag v10.0)

v11.0 Hermes-Native Expert Agents PoC Implementation — IN PLANNING:
  Phase 52 (INFRA-FOUNDATION)            [░░░░░░░░░░] 0%   agent registry + 7 MCP tools + state machine + serial enforcement
  Phase 53 (CREATIVE-SLICE)              [░░░░░░░░░░] 0%   9 agent YAMLs + Step 3 round table + conflict arbitration
  Phase 54 (EVAL-HARNESS-1)              [░░░░░░░░░░] 0%   fitness battery + latency SLO + bias canary
  Phase 55 (EVAL-HARNESS-2)              [░░░░░░░░░░] 0%   compaction + tuning + dry-run-first + schema migration
  Phase 56 (VALIDATE)                    [░░░░░░░░░░] 0%   milestone audit + smoke test(严格 LAST)
```

**v11.0 milestone status:** PLANNING — roadmap created (5 phases 52-56), 15/15 reqs mapped, awaiting user approval. After approval, plan Phase 52.

### Phase Statuses (v11.0)

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 52 | INFRA-FOUNDATION — agent registry + 7 MCP tools + state machine + serial enforcement | **Not started** | INFRA-01..04. First phase — produces runtime that 53-55 build on. Hard constraint: 强制串行 (INFRA-04) cites `feedback-glm-overload-reduce-concurrency.md`. |
| 53 | CREATIVE-SLICE — 9 sample agent YAMLs + Step 3 round table + conflict arbitration | **Not started** | MIGR-01 + CREATIVE-01..02. Vertical slice end-to-end. 9-agent round table on real GLM API call. |
| 54 | EVAL-HARNESS-1 — fitness battery + latency SLO + bias canary | **Not started** | EVAL-01..03. Per `05-POC-PLAN.md` §6.1: fitness battery FIRST → schema migration dry-run SECOND → bias canary THIRD. This phase ships fitness battery + bias canary + latency SLO. |
| 55 | EVAL-HARNESS-2 — compaction + tuning + dry-run-first + schema migration | **Not started** | EVAL-04..07. Hard constraint: dry-run-first invariant (EVAL-06) — curator default dry-run, schema migration default dry-run. |
| 56 | VALIDATE — milestone audit + smoke test | **Not started** | VALIDATE-01. **Strictly LAST**, analog to v10.0 Phase 51 / v5.0 Phase 27 close-out pattern. |

### Critical Path

```
                                                                                              ┌──────────────────────┐
                                                                                              │ Phase 56 (VALIDATE)   │
                                                                                              │ strictly LAST         │
                                                                                              └──────────▲───────────┘
                                                                                                         │
                                                                                ┌──── Phase 55 (EVAL-2) ─┘
                                                                                │
                                                  ┌──── Phase 54 (EVAL-1) ─────┘
                                                  │
                  ┌──── Phase 53 (CREATIVE) ─────┘
                  │
Phase 52 ─────────┘
(INFRA-FOUNDATION)
```

**Critical path:** 52 → 53 → 54 → 55 → 56 (5 sequential steps; no parallel waves — runtime implementation milestone).

**Hard dependencies:**

- Phase 53 → needs Phase 52 agent registry + 7 MCP tools + state machine
- Phase 54 → needs Phase 53 vertical slice running
- Phase 55 → needs Phase 54 fitness battery as regression-detection foundation
- Phase 56 → strictly LAST; cross-phase audit + smoke test

## Performance Metrics (v11.0)

- v11.0 phases total: 5 (Phases 52-56, continuing from v10.0 phase 51)
- v11.0 phases completed: 0
- v11.0 requirements total: 15 (INFRA-01..04 + CREATIVE-01..02 + EVAL-01..07 + MIGR-01 + VALIDATE-01)
- v11.0 requirements mapped: 15 / 15 ✓
- v11.0 requirements orphaned: 0
- v11.0 plans completed: 0 / TBD (plan counts to be refined in plan-phase)
- **Deliverable form:** Python code + agent YAML + mem0 extensions + test artifacts. **v11.0 is runtime implementation milestone**, NOT design. Each phase produces code (not docs). Cite v10.0 design decisions, do not re-derive.
- **Granularity:** standard (5 phases — within 5-8 range typical for standard; justified by req category clustering + 12-day PoC budget per `05-POC-PLAN.md` §2.4)

## Decisions (v11.0 — entered planning)

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 5 phases continuing from v10.0 phase 51 (52-56) | Project maintains sequential phase numbering; decimal phases reserved for urgent insertions only. v10.0 ended at P51; v11.0 starts at P52. | Applied 2026-07-07 — ROADMAP phase numbering 52-56 |
| Phase clustering by req category (52=INFRA / 53=CREATIVE+MIGR / 54=EVAL-wave-1 / 55=EVAL-wave-2 / 56=VALIDATE) | Each phase delivers one coherent capability. MIGR-01 (9 agent YAMLs) bundled into Phase 53 because CREATIVE-01 needs the 9 YAMLs as precondition — splitting would force a non-value-add dependency wall. EVAL split into 2 phases (54 + 55) to preserve `05-POC-PLAN.md` §6.1 sequencing (fitness battery FIRST → schema migration dry-run SECOND → bias canary THIRD) within phase structure. | Applied 2026-07-07 — ROADMAP phase-req mapping table |
| Phase 56 (VALIDATE) strictly LAST | Cross-15-req audit + vertical slice smoke test on real GLM API + latency/bias reports publication. Mirrors v10.0 P51 / v9.0 P43 / v5.0 P27 single-phase close-out pattern. | Applied 2026-07-07 — ROADMAP critical path annotated |
| **Hard constraint: 强制串行 (INFRA-04)** | Cites MEMORY.md `feedback-glm-overload-reduce-concurrency.md` (global concurrency==1 by design). Round table executes 1 panelist 1 turn sequential `await` — no parallel panelist execution. Compatible with GLM 4-key rotation (no concurrent API calls within a round table). | Applied 2026-07-07 — Phase 52 SC#4 + Phase 53 SC#2 enforces serial |
| **Hard constraint: dry-run-first (EVAL-06)** | Curator default `dry_run: true`. Schema migration default `dry_run: true`. P5 mitigation (curator failure modes) + P14 mitigation (silent drops). Test: invoke both without explicit `dry_run: false` flag, verify no state mutation. | Applied 2026-07-07 — Phase 55 SC#3 enforces default |
| 7 v10.0 design decisions locked, cited not re-derived | T6 protocol / B3a Python runner 增量迁移 / D2 storyboard round-parallel / G2 通用框架 / α agent YAML / per-agent memory 自进化 / (vi) 分层 CC 角色 — all locked in PROJECT.md §Current Milestone. v11.0 implements, does not re-litigate. | Applied 2026-07-07 — ROADMAP overview + each phase cites v10.0 source doc |

### Decisions (carried forward — relevant to v11.0)

| Decision | Rationale | Why relevant to v11.0 |
|----------|-----------|----------------------|
| v10.0 design suite as canonical implementation blueprint | 7 design docs + 3 schemas + 1 lint script shipped 2026-07-07 (tag `v10.0`, audit PASSED). v11.0 implements these designs. | All v11.0 phases cite v10.0 docs (e.g., Phase 52 cites `01-AGENT-REGISTRY-SCHEMA.md` + `02-ROUND-TABLE-PROTOCOL.md` §5; Phase 53 cites `04-MIGRATION-PATH.md` §2 75-cell transform table). |
| `.planning/research/v10-orchestrator-design/05-POC-PLAN.md` is THE implementation blueprint | v10.0 capstone doc — vertical slice + 7 acceptance criteria + 7-row risk register + sequencing rationale. | Phase 52-56 structure mirrors §3-§6 of POC-PLAN. Phase 54+55 split preserves §6.1 sequencing (fitness battery FIRST → schema migration dry-run SECOND → bias canary THIRD). |
| `.planning/milestones/` is canonical close-out archive location | v3-v10 all wrote milestone audit/report to `.planning/milestones/v{X}-MILESTONE-AUDIT.md`. | Phase 56 SC#1 specifies `.planning/milestones/v11.0-MILESTONE-AUDIT.md`. |
| Cross-repo migration of skills (post-v9.0 ship, 2026-06-27) | Commit `f10495332` moved `skills/kais-movie-pipeline/` + `skills/movie-experts/` + 4 plugins to 独立 repo `/data/workspace/kais-hermes-skills/`. hermes-agent repo 现仅保留 GSD `.planning/` 工件. | Phase 53 MIGR-01 transforms **9 sample** SKILL.md from kais-hermes-skills repo into agent YAMLs at `~/.hermes/agents/`. Read-only on SKILL.md (per Phase 48 + Phase 49 lineage invariants L1-L6). |

## Accumulated Context

### v11.0 Goal Restatement

按 v10.0 设计套件(`.planning/research/v10-orchestrator-design/00-` 到 `06-` + 3 schemas + 1 lint script)实施 vertical slice(1 creative phase + 1 infra phase)+ 7 项 PoC 验收(12 person-days),验证三层架构 runtime 可行性。**v11.0 是 v10.0 设计的实施 milestone** —— 把设计落地为 Python 代码 + agent YAML + mem0 extensions。

**Vertical slices (per `05-POC-PLAN.md` §3):**

- **Infra slice (Phase 52):** agent registry + 7 MCP tools + state machine + serial enforcement
- **Creative slice (Phase 53):** 9-agent screenplay Step 3 round table (HOOK-09 edge case)

**7 acceptance criteria (per `05-POC-PLAN.md` §4):**

1. Fitness battery design (3d) — Phase 54 EVAL-01
2. Latency SLO p95 < 500ms (2d) — Phase 54 EVAL-02
3. Bias canary (2d) — Phase 54 EVAL-03
4. Compaction pass (1d) — Phase 55 EVAL-04
5. Threshold tuning (1d) — Phase 55 EVAL-05
6. Dry-run-first invariant (1d) — Phase 55 EVAL-06
7. Schema migration dry-run (2d) — Phase 55 EVAL-07

**关键范式声明(与 Kimi 方案的本质差异,cite v10.0 §03 决策):**

- **Kimi 默认**:CC 是 agent 容器;**v10.0 设计(v11.0 实施)**:Hermes 是 agent 容器(新形态 YAML),CC 仅是场地+协调员+结构化助手
- Agent vs Skill 分层:agent 是 Hermes-side 独立 YAML 实体,有 per-agent memory + 自进化能力;SKILL 作 fallback 保留(`default_invocation: skill_fallback`)

**Scope explicitly out(与 Kai 2026-07-06 决策对齐 + v10.0 design carry-forward):**

- 15 expert 全量 transform(仅 9 sample 在 v11.0)
- per-agent memory benchmark 全量(仅 latency p95 测)
- Option B → 物理分区迁移(v11.0 仍用 mem0 单 backend + agent_id filter)
- live production traffic(v11.0 PoC 仅 smoke test)
- kais-hermes-skills repo 改动(v11.0 不改 SKILL.md,只读)
- new repo 创建(单 repo 收敛)
- deprecate SKILL.md form(SKILL 作 fallback 保留)

### Blockers / Risks (v11.0 — new)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **mem0 Platform API filter latency > 500ms (OQ-12 deferred from v10.0)** | MEDIUM | HIGH (if filter doesn't scale, may need物理分区 re-architecture in v12) | Phase 54 EVAL-02 latency benchmark is the gate. If p95 > 500ms, document trigger conditions for v12 物理分区 evaluation per Phase 48 §3. |
| **GLM 4-key rotation vs round table real concurrency (CC-6 from v10.0)** | HIGH | HIGH (concurrent 7 panelists × N rounds 撞 GLM 4-key ceiling) | Phase 52 INFRA-04 hard constraint: 强制串行 (1 panelist 1 turn `await`). MEMORY.md `feedback-glm-overload-reduce-concurrency.md` global concurrency==1 already in force. |
| **curator `_memory_evolution_phase` hallucination rate unmeasured** | MEDIUM | MEDIUM (writes bad memory to store) | Phase 54 EVAL-03 bias canary is the gate — must catch 4/5 known-bad records. Phase 55 EVAL-06 dry-run-first ensures default mode zero writes. |
| **9-agent transform produces invalid YAML (lineage/SHA mismatch)** | MEDIUM | MEDIUM (creative slice blocked, milestone slip) | Phase 53 SC#1 requires all 9 YAMLs pass `jsonschema.Draft202012Validator.validate()` + lineage block populated. Per-YAML transform log + audit trail per Phase 49 §2 75-cell rules. |
| **Round table state corruption on crash (3 failure modes per Phase 48 §6)** | MEDIUM | HIGH (PoC blocked, manual recovery) | Phase 52 INFRA-03 SC#3 covers all 3 failure modes (partial-write, mid-turn crash, orphaned session) with crash recovery tests. |
| **dry-run-first leaks (state mutation despite default)** | LOW | HIGH (P5/P14 mitigation voided) | Phase 55 EVAL-06 SC#3 test verifies default invocation produces zero state mutation in both curator + migration script. |
| **5 phases at lower end of standard granularity range (5-8)** | LOW | LOW (slightly less granular than typical) | Justified by 12-day PoC budget per `05-POC-PLAN.md` §2.4 + req category clustering (INFRA / CREATIVE+MIGR / EVAL-wave-1 / EVAL-wave-2 / VALIDATE). Each phase delivers one coherent capability. |

### Blockers / Risks (carried from v10.0)

**16 Open Questions from v10.0 — 14 RESOLVED in design, 2 DEFERRED to v11.0 PoC:**

- OQ-12 (mem0 Platform API filter behavior) → Phase 54 EVAL-02 latency benchmark resolves
- (OQ-15 if any other was marked DEFERRED → resolved in v11.0 PoC execution)

**Inherited from v9.0 close (operator-action-handoffs, NOT gaps):**

- (a) Phase 41 LTX2.3 live GPU generation testing (V9-FUTURE-02) — deferred to operator
- (b) Phase 42 5 平台 API key configuration + live data ingestion (V9-FUTURE-01) — deferred to operator

These do NOT block v11.0 (PoC milestone uses synthetic inputs, not production traffic).

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260626-rq4 | flood-aware `_send_with_retry` (parse retry_after, clamp [3,60]s, default 5s) | 2026-06-26 | dda0e6c1a | [260626-rq4-flood-aware-send-retry](./quick/260626-rq4-flood-aware-send-retry/) |
| 260626-t0q | CJK error classification (port openclaw failover-matches + Zhipu 1305/1311/1113 codes) | 2026-06-26 | c9e1ca8d4 | [260626-t0q-cjk-error-classification](./quick/260626-t0q-cjk-error-classification/) |
| 260626-vzl | Encode Notion "创作方向" into kais-movie-pipeline refs | 2026-06-26 | bd53bc387 | [260626-vzl-kmp-creative-direction-refs](./quick/260626-vzl-kmp-creative-direction-refs/) |
| 260702-ezx | GLM concurrency + retry hardening | 2026-07-02 | 4b821c29b | [260702-ezx-glm-concurrency-hardening](./quick/260702-ezx-glm-concurrency-hardening/) |
| 260702-o1a | Credential-pool overloaded fix | 2026-07-02 | 5839b5f78 | [260702-o1a-credential-pool-overloaded-fix](./quick/260702-o1a-credential-pool-overloaded-fix/) |

## Deferred Items

Items acknowledged and carried forward (NOT in v11.0 scope, explicitly deferred):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| **15-expert 全量 transform** | Only 9 sample agents (CREATIVE-01 用) 在 v11.0;剩余 6 expert 留 v12.0 | Deferred to v12.0 | v11.0 planning (2026-07-07) |
| **per-agent memory benchmark 全量** | Only latency p95 测;memory throughput / concurrent-agent scaling 留 v12.0 | Deferred to v12.0 | v11.0 planning (2026-07-07) |
| **Option B → 物理分区迁移** | v11.0 用 mem0 单 backend + agent_id filter;物理分区触发条件留 v12+ 监测后决定 | Deferred to v12+ | v11.0 planning (2026-07-07) |
| **live production traffic** | v11.0 PoC 仅 smoke test;production deployment 留 v12+ | Deferred to v12+ | v11.0 planning (2026-07-07) |
| **kais-hermes-skills repo 改动** | 设计文档已锁定 lineage 不动 SKILL;v11.0 不改 SKILL.md,只读 | Deferred (read-only) | v11.0 planning (2026-07-07) |
| **new repo 创建(如 kais-orchestrator)** | 单 repo 收敛决策保留;v11.0 全在 hermes-agent | Deferred (decision preserved) | v11.0 planning (2026-07-07) |
| **deprecate SKILL.md form** | v11.0 SKILL 作 fallback 保留(`default_invocation: skill_fallback`) | Deferred (additive transition) | v11.0 planning (2026-07-07) |
| **threshold tuning production data** | v11.0 仅文档化 initial defaults;tuning 用 prod data 留 v12+ | Deferred to v12+ | v11.0 planning (2026-07-07) |

Items acknowledged at v10.0 close (2026-07-07) — design milestone produced blueprint, no implementation:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| v11.0 PoC implementation | All code work implied by v10.0 design docs | v11.0 in planning | v10.0 close (2026-07-07) |
| Live round table execution | v10.0 designs protocol; live execution is v11.0 PoC | v11.0 in planning | v10.0 close (2026-07-07) |
| Per-agent memory latency benchmark | v10.0 designs schema + fields; v11.0 PoC runs benchmark | v11.0 in planning | v10.0 close (2026-07-07) |

Items acknowledged at v9.0 close (2026-06-27) — operator-action-handoffs (NOT gaps):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Operator smoke-test | Phase 41 LTX2.3 live GPU generation testing (V9-FUTURE-02) | Documented in v9.0-MILESTONE-AUDIT.md | v9.0 close (2026-06-27) |
| Operator smoke-test | Phase 42 5 平台 API key configuration + live data ingestion (V9-FUTURE-01) | Documented in v9.0-MILESTONE-AUDIT.md | v9.0 close (2026-06-27) |

## Session Continuity

**If session is lost, restore context by reading:**

1. `.planning/PROJECT.md` §"Current Milestone: v11.0" — milestone goal + vertical slice + acceptance criteria + scope discipline
2. `.planning/ROADMAP.md` — 5 phases (52-56), success criteria, critical path (52→53→54→55→56)
3. `.planning/REQUIREMENTS.md` — 15 requirements (INFRA-01..04 + CREATIVE-01..02 + EVAL-01..07 + MIGR-01 + VALIDATE-01) with Traceability table
4. `.planning/research/v10-orchestrator-design/05-POC-PLAN.md` — THE implementation blueprint (§3 vertical slice + §4 acceptance criteria + §5 risk register + §6 implementation path)
5. `.planning/research/v10-orchestrator-design/01-AGENT-REGISTRY-SCHEMA.md` + `agents-schema.yaml` — agent YAML schema (Phase 45 stable, 18 fields camelCase)
6. `.planning/research/v10-orchestrator-design/02-ROUND-TABLE-PROTOCOL.md` + `round-table-state-schema.yaml` — round table protocol + 7 MCP tool contract (§5)
7. `.planning/research/v10-orchestrator-design/04-MIGRATION-PATH.md` — 15-expert × 5-field transform rules (§2 75-cell table)
8. `~/.hermes/agents/` (target agent YAML location) + MEMORY.md `feedback-glm-overload-reduce-concurrency.md` (serial constraint policy)

**Next action:** After user approval of ROADMAP, plan Phase 52 (`/gsd:plan-phase 52`). Phase 52 has no `--research-phase` flag (well-documented design from v10.0 suite).

**Resume from interrupted phase:** Not yet started — first v11.0 phase.

---

*Last updated: 2026-07-07 — v11.0 ROADMAP.md + STATE.md + REQUIREMENTS.md traceability updated. 5 phases (52-56), 15/15 reqs mapped, runtime implementation milestone (Python code + agent YAML + mem0 extensions + test artifacts). Awaiting user approval to start planning Phase 52 (INFRA-FOUNDATION).*

## Operator Next Steps

**v11.0 milestone is in PLANNING.** Operator actions:

1. Review `.planning/ROADMAP.md` (5 phases 52-56, 15/15 reqs mapped)
2. Review `.planning/STATE.md` (this file — accumulated context + risk register)
3. Approve roadmap (or provide revision feedback)
4. After approval: `/gsd:plan-phase 52` to start with INFRA-FOUNDATION

**Operator-action-handoffs from v9.0 (post-tag, NOT gaps, do NOT block v11.0):**

- (a) Phase 41 LTX2.3 live GPU testing (V9-FUTURE-02)
- (b) Phase 42 5 平台 API key configuration + live data ingestion (V9-FUTURE-01)
