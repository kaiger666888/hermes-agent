---
gsd_state_version: 1.0
milestone: v10.0
milestone_name: Hermes-Agent 编排架构第一性原理推导(设计型)
status: ready_to_plan
last_updated: 2026-07-06T19:03:20.105Z
last_activity: 2026-07-06 -- Phase 50 execution started
progress:
  total_phases: 8
  completed_phases: 6
  total_plans: 7
  completed_plans: 8
  percent: 75
stopped_at: Phase 50 complete (1/1) — ready to discuss Phase 51
---

# State: Hermes Agent — Kai's Personal Agent Platform

## Project Reference

**Project code:** MESV2 (historical; v7.0+ broadens scope beyond movie-experts)
**Name:** Hermes Agent — Kai's Personal Agent Platform
**Core value:** 让 hermes-agent 成为 Kai 的主 agent:既承载 movie-experts 这样的领域专家子系统(v1-v6 已 shipped),也具备通用 agent 必备的代码委派、自动化集成、文档协作、个人身份与记忆能力(v7.0 迁移目标)。v10.0 把这个愿景推进一步 —— 推导 Hermes 总调度器 + Hermes-native expert agents + CC 执行场的三层编排架构。
**Key docs:** `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/MILESTONES.md`, `.planning/REQUIREMENTS.md`, `.planning/research/v10-orchestrator-design/SUMMARY.md`
**Mode:** yolo (auto-advance, parallelization on)
**Granularity:** standard
**Model profile:** quality
**Current focus:** Phase 51 — validate

## Current Position

Phase: 51
Plan: Not started
Status: Ready to plan
Last activity: 2026-07-06

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

v10.0 Hermes-Agent 编排架构第一性原理推导(设计型)— in planning:
  Phase 44 (FIRST-PRINCIPLES)             [░░░░░░░░░░] 0%   7 决策推导 + anti-features 总表
  Phase 45 (AGENT-SCHEMA)                 [░░░░░░░░░░] 0%   18-field YAML + memory-record-schema(7 pitfall 字段级缓解)
  Phase 46 (ROUND-TABLE-PROTOCOL)         [░░░░░░░░░░] 0%   Turn lifecycle + memory conflict arbitration + 串行约束
  Phase 47 (KIMI-COMPARISON)              [░░░░░░░░░░] 0%   T6 vs Kimi MCP shim 7 维度对照(parallel-eligible)
  Phase 48 (CROSS-REPO-IMPACT)            [░░░░░░░░░░] 0%   3-location 同步 + Option B vs 物理分区(parallel-eligible)
  Phase 49 (MIGRATION-PATH)               [░░░░░░░░░░] 0%   15 expert transform + memory schema 迁移
  Phase 50 (POC-PLAN)                     [░░░░░░░░░░] 0%   v11.0 PoC 验收条件清单
  Phase 51 (VALIDATE)                     [░░░░░░░░░░] 0%   Lint script + milestone audit(严格 LAST)
```

**v10.0 milestone status:** PLANNING — roadmap created (8 phases 44-51), 9/9 reqs mapped, awaiting user approval. After approval, plan Phase 44.

### Phase Statuses (v10.0)

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 44 | FIRST-PRINCIPLES — 7 决策推导 + 显式拒绝总表 | **Not started** | DESIGN-01. Foundation phase — 后续 6 docs 都引用本文档作为根论据。 |
| 45 | AGENT-SCHEMA — 18-field YAML + memory-record-schema | **Not started** | DESIGN-02. 7 load-bearing pitfall 字段级缓解(P1/P2/P4/P5/P8/P10/P14)在此固化。 |
| 46 | ROUND-TABLE-PROTOCOL — Turn lifecycle + conflict arbitration | **Not started** | DESIGN-03. 消费 45 的 schema;强制串行(1 panelist 1 turn);7 MCP tool 命名统一 STACK 形态。 |
| 47 | KIMI-COMPARISON — T6 vs Kimi 全 MCP shim 对照 | **Not started** | DESIGN-04. **Parallel-eligible** — 可与 45/46 并行,只依赖 44。 |
| 48 | CROSS-REPO-IMPACT — 3-location 同步策略 | **Not started** | DESIGN-07. **Parallel-eligible** — 可与 45/46 并行,只依赖 44。 |
| 49 | MIGRATION-PATH — 15 expert transform + retained-phases | **Not started** | DESIGN-05. 依赖 45+46(transform 规则要 schema + 协议字段)。 |
| 50 | POC-PLAN — v11.0 PoC 验收条件清单 | **Not started** | DESIGN-06. 收口,依赖前面所有 design docs(尤其 49)。 |
| 51 | VALIDATE — Lint script + milestone audit | **Not started** | VALIDATE-01 + VALIDATE-02. **严格 LAST**,类比 v9.0 P43 / v5.0 P27。 |

### Critical Path

```
                                                                                              ┌──────────────────────┐
                                                                                              │ Phase 51 (VALIDATE)   │
                                                                                              │ strictly LAST         │
                                                                                              └──────────▲───────────┘
                                                                                                         │
                                                            ┌──────────── Phase 50 (POC-PLAN) ────┘
                                                            │   收口
                                                            │
                                  ┌──── Phase 49 (MIGRATION) ─┘
                                  │     依赖 45+46
                                  │
          ┌──── Phase 46 (ROUND-TABLE) ──┐
          │     依赖 45                    │
          │                               │
Phase 44 ─┼──── Phase 45 (AGENT-SCHEMA) ──┘
(FIRST-   │
 PRINCIPLES)├─ Phase 47 (KIMI-COMPARISON) ─────────────────────┐  PARALLEL-ELIGIBLE WAVE:
           │   独立,只依赖 44                                    │  {47, 48} 可与 {45, 46}
           └─ Phase 48 (CROSS-REPO) ────────────────────────────┘  并行启动(独立横切文档)
              独立,只依赖 44
```

**Critical path:** 44 → 45 → 46 → 49 → 50 → 51(6 sequential steps)
**Parallel-eligible:** Phase 47 + Phase 48 可与 Phase 45/46 并行(独立横切文档,不依赖 schema 字段细节)

**Hard dependencies:**

- Phase 45 (AGENT-SCHEMA) → needs Phase 44 anti-features 总表 as schema field 论据
- Phase 46 (ROUND-TABLE) → needs Phase 45 schema fields as protocol parameters
- Phase 49 (MIGRATION) → needs Phase 45 schema + Phase 46 protocol fields
- Phase 50 (POC-PLAN) → needs Phase 49 transform rules + indirectly all prior design docs
- Phase 51 (VALIDATE) → strictly LAST; runs cross-doc lint + milestone audit across all 7 prior phases

## Performance Metrics (v10.0)

- v10.0 phases total: 8 (Phases 44-51, continuing from v9.0 phase 43)
- v10.0 phases completed: 0
- v10.0 requirements total: 9 (DESIGN-01..07 + VALIDATE-01..02)
- v10.0 requirements mapped: 9 / 9 ✓
- v10.0 requirements orphaned: 0
- v10.0 plans completed: 0 / TBD (plan counts to be refined in plan-phase)
- **Deliverable form:** Design docs + YAML schemas + 1 lint script only. **Zero code changes** to SKILL.md / Python / plugin manifest / mcp_serve.py. Mirrors v2.0 PRFP design-only milestone pattern.
- **Granularity:** standard (8 phases — slightly above 5-8 range typical for standard, justified by 1:1 req-to-phase mapping for 7 design docs + 1 consolidated validation phase)

## Decisions (v10.0 — entered planning)

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 8 phases continuing from v9.0 phase 43 (44-51) | Project maintains sequential phase numbering; decimal phases reserved for urgent insertions only. v9.0 ended at P43; v10.0 starts at P44. | Applied 2026-07-06 — ROADMAP phase numbering 44-51 |
| 1:1 req → phase mapping for 7 design docs (Phase 44-50 = DESIGN-01..DESIGN-07 reordered per dependency graph) | Each design doc is a coherent, independently-verifiable deliverable; 1:1 mapping preserves traceability. Order optimized for dependency graph (00 → 01 → 02 → 04/05/06 dependency chain from SUMMARY §Roadmap Implications). | Applied 2026-07-06 — ROADMAP phase-req mapping table |
| Merge VALIDATE-01 (audit) + VALIDATE-02 (lint) into single Phase 51 | Lint script is the audit's tool — audit references lint output as evidence. Splitting would force a non-parallel wave between them for no value. Mirrors v9.0 P43 / v5.0 P27 single-phase close-out pattern. | Applied 2026-07-06 — Phase 51 covers both reqs |
| Phase 47 (KIMI-COMPARISON) + Phase 48 (CROSS-REPO-IMPACT) are parallel-eligible | Independent horizontal docs that only depend on Phase 44 (FIRST-PRINCIPLES), not on 45/46 schema fields. SUMMARY CC findings confirm 03/06 are横切. | Applied 2026-07-06 — ROADMAP parallel wave annotated |
| Phase 51 (VALIDATE) strictly LAST | Cross-7-phase consistency lint + milestone audit + 16 OQ + 7 pitfall coverage check. Mirrors v5.0 P27 / v6.0 P33 / v7.0 P37 / v9.0 P43 close-out pattern. | Applied 2026-07-06 — ROADMAP critical path annotated |
| **Zero code changes scope discipline** | User explicit choice — v10.0 produces design docs only (`research/v10-orchestrator-design/*.md` + YAML schemas + 1 lint script). No SKILL.md / Python / plugin / mcp_serve.py changes. Mirrors v2.0 PRFP scope discipline. | Applied 2026-07-06 — ROADMAP overview + each phase scope reminder |
| Per SUMMARY §Research Flags, three phases flagged for `--research-phase`: 45 / 46 / 50 | (a) Phase 45 needs mem0 Platform API filter behavior research (STACK M-confidence); (b) Phase 46 needs AutoGen 0.2 turn_order matrix API surface research (FEATURES B2.1); (c) Phase 50 needs fitness battery design research (PITFALLS §P8). | Watch-item — flag at plan-phase time |
| 7 design decisions locked pre-roadmap (T6 / B3a / D2 / G2 / α / per-agent memory / (vi) layered CC) | Locked in PROJECT.md §Current Milestone. SUMMARY §Design Decisions Validated table cross-verified all 7 against 4 research threads. ROADMAP derives phases from these, does not re-litigate. | Applied 2026-07-06 — Phase 44 SC#1 derives 7 decisions from first principles |

### Decisions (carried forward — relevant to v10.0)

| Decision | Rationale | Why relevant to v10.0 |
|----------|-----------|----------------------|
| `.planning/research/` is canonical design-suite location | v2.0 PRFP shipped 18 design docs to `.planning/research/v2-pipeline-design/`. Same pattern. | All v10.0 design docs land in `.planning/research/v10-orchestrator-design/`. |
| `.planning/milestones/` is canonical close-out archive location | v3-v9 all wrote milestone audit/report to `.planning/milestones/v{X}-MILESTONE-AUDIT.md`. | Phase 51 SC#3 specifies `.planning/milestones/v10.0-MILESTONE-AUDIT.md`. |
| Cross-repo migration of skills (post-v9.0 ship, 2026-06-27) | Commit `f10495332` moved `skills/kais-movie-pipeline/` + `skills/movie-experts/` + 4 plugins to独立 repo `/data/workspace/kais-hermes-skills/`. hermes-agent repo 现仅保留 GSD `.planning/` 工件. | Phase 48 (CROSS-REPO-IMPACT) design explicitly accounts for 3-location split: hermes-agent repo + kais-hermes-skills repo + `~/.hermes/`. |

## Accumulated Context

### v10.0 Goal Restatement

借鉴 Kimi Notion 架构2.0,结合本 repo 已 ship 的 coding-agent / GSD / curator / mem0,从第一性原理推导 Hermes 总调度器 + Hermes-native expert agents + Claude Code 执行场的三层架构。产出 7 份设计文档(00-06)+ 2 个 validation 工件,作为 v11.0 PoC 实施者的直接蓝本。

**7 个已锁设计决策(在 PROJECT.md + SUMMARY.md 已 cross-validated):**

| # | 决策 | 选型简述 |
|---|------|---------|
| 1 | 协议(T6) | Hermes MCP server(扩展 mcp_serve.py)+ tmux dispatch + CC native MCP client |
| 2 | Python runner(B3a 增量迁移) | delegate-only phase 迁 CC;ComfyUI-calling + Step 0/6.5/15 保留 Python |
| 3 | Storyboard-first-class(D2) | V8.6 编号保留,orchestrator 层做 round-based parallel |
| 4 | 通用 vs 专属(G2) | 抽象 pipeline orchestration pattern,kais-movie-pipeline 作首个 sample |
| 5 | Agent 形态(α) | YAML + persona + tools + refs + memory_scope + lineage |
| 6 | Agent 记忆 | per-agent scoped memory(扩展 mem0 backend)+ curator 驱动跨项目自进化 |
| 7 | CC 角色((vi) 分层) | Hermes 控 turn_order / max_rounds / schema / early_stop_rule;CC 控 framing + synthesis |

**关键范式声明(与 Kimi 方案的本质差异):**

- Kimi 默认:CC 是 agent 容器;**v10.0**:Hermes 是 agent 容器(新形态 YAML),CC 仅是场地+协调员+结构化助手
- Agent vs Skill 分层:agent 是 Hermes-side 独立 YAML 实体,有 per-agent memory + 自进化能力;SKILL 作 fallback 保留

**Scope explicitly out(与 Kai 2026-07-06 决策对齐):** 任何代码改动(不动 SKILL.md / Python / plugin / mcp_serve.py / agent/curator.py / plugins/memory/mem0/)、kais-hermes-skills repo 改动、新建独立 repo、live round table 执行、per-agent memory 实测。

### Blockers / Risks (v10.0 — new)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **mem0 Platform API filter behavior unknown (OQ-12)** | MEDIUM | HIGH (if filter doesn't scale, v11.0 PoC may need物理分区 re-architecture) | Phase 48 SC#3 documents Option B → 物理分区 migration trigger conditions; v11.0 PoC week-1 latency benchmark decides |
| **GLM 4-key rotation vs round table real concurrency (CC-6)** | HIGH | HIGH (concurrent 7 panelists × N rounds 会撞 GLM 4-key ceiling) | Phase 46 SC#4 enforces 强制串行 (1 panelist 1 turn 顺序 await); MEMORY.md `feedback-glm-overload-reduce-concurrency.md` global concurrency==1 already in force |
| **curator `_memory_evolution_phase` hallucination rate unmeasured** | MEDIUM | MEDIUM (writes bad memory to store) | Phase 50 POC-PLAN SC#3 includes bias canary as acceptance criterion; Phase 45 SC#3 dry-run-by-default |
| **18-field schema insufficient (CC-2 finding)** | LOW | HIGH (PITFALLS requires 8+ memory-record fields not in 18-field agent schema) | Phase 45 SC#1 explicitly splits `agents-schema.yaml` from `memory-record-schema.yaml` to avoid confusion |
| **Cross-doc term/schema/decision drift across 7 docs** | MEDIUM | MEDIUM (audit fails) | Phase 51 SC#1+SC#2 lint script catches automatically; VALIDATE-02 is the tool |
| **Three phases need research (--research-phase) — adds latency** | MEDIUM | LOW (research adds 1-2 phases of latency per affected phase) | SUMMARY §Research Flags identifies Phase 45 / 46 / 50 as research candidates. Plan-phase will decide. |
| **8 phases above standard granularity range (5-8)** | LOW | LOW (slightly compressed critical path) | Justified by 1:1 req-to-phase mapping for design docs + 1 consolidated validation phase; per-phase plan count expected to be 1 (single-plan phases). |

### Blockers / Risks (carried from v1-v9)

**Inherited from v9.0 close (operator-action-handoffs, NOT gaps):**

- (a) Phase 41 LTX2.3 live GPU generation testing (V9-FUTURE-02) — deferred to operator
- (b) Phase 42 5 平台 API key configuration + live data ingestion (V9-FUTURE-01) — deferred to operator

**Inherited from v7.0 close (operator smoke-tests):**

- MEM0_API_KEY config + live mem0 ingestion + SOUL routing observation + coding-agent skill invocation — all documented in v7.0-MIGRATION-REPORT.md

These do NOT block v10.0 (design-only milestone). They are listed for continuity.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260626-rq4 | flood-aware `_send_with_retry` (parse retry_after, clamp [3,60]s, default 5s) | 2026-06-26 | dda0e6c1a | [260626-rq4-flood-aware-send-retry](./quick/260626-rq4-flood-aware-send-retry/) |
| 260626-t0q | CJK error classification (port openclaw failover-matches + Zhipu 1305/1311/1113 codes) | 2026-06-26 | c9e1ca8d4 | [260626-t0q-cjk-error-classification](./quick/260626-t0q-cjk-error-classification/) |
| 260626-vzl | Encode Notion "创作方向" into kais-movie-pipeline refs | 2026-06-26 | bd53bc387 | [260626-vzl-kmp-creative-direction-refs](./quick/260626-vzl-kmp-creative-direction-refs/) |
| 260702-ezx | GLM concurrency + retry hardening | 2026-07-02 | 4b821c29b | [260702-ezx-glm-concurrency-hardening](./quick/260702-ezx-glm-concurrency-hardening/) |
| 260702-o1a | Credential-pool overloaded fix | 2026-07-02 | 5839b5f78 | [260702-o1a-credential-pool-overloaded-fix](./quick/260702-o1a-credential-pool-overloaded-fix/) |

## Deferred Items

Items acknowledged and carried forward (NOT in v10.0 scope, explicitly deferred):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| FEISHU | feishu-doc / feishu-drive / feishu-perm / feishu-wiki migration | Deferred to v8.0+ | v7.0 planning |
| AGENT | Multi hermes profile mechanism | Deferred | v7.0 planning |
| AGENT | acp-router alternative form in hermes | Deferred | v7.0 planning |
| Operator manual | Provider keys / models.json migration | Kai handles manually | v7.0 planning |
| Operator manual | Feishu channel config + ACP config | Kai handles manually | v7.0 planning |
| Storage | workspace/ GB-scale AIGC outputs | Stay in place | v7.0 planning |
| Runtime state | agents/<name>/sessions/ + auth-profiles.json | No migration value | v7.0 planning |
| **v11.0 PoC implementation** | All code work implied by v10.0 design docs | Deferred to v11.0 (next milestone after v10.0 design ships) | v10.0 planning (2026-07-06) |
| **Live round table execution** | v10.0 designs protocol; live execution is v11.0 PoC | Deferred to v11.0 PoC | v10.0 planning |
| **Per-agent memory latency benchmark** | v10.0 designs schema + fields; v11.0 PoC runs benchmark | Deferred to v11.0 PoC | v10.0 planning |

Items acknowledged at v9.0 close (2026-06-27) — operator-action-handoffs (NOT gaps):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Operator smoke-test | Phase 41 LTX2.3 live GPU generation testing (V9-FUTURE-02) | Documented in v9.0-MILESTONE-AUDIT.md | v9.0 close (2026-06-27) |
| Operator smoke-test | Phase 42 5 平台 API key configuration + live data ingestion (V9-FUTURE-01) | Documented in v9.0-MILESTONE-AUDIT.md | v9.0 close (2026-06-27) |

## Session Continuity

**If session is lost, restore context by reading:**

1. `.planning/PROJECT.md` §"Current Milestone: v10.0" — milestone goal + 7 locked design decisions + paradigm shift声明
2. `.planning/ROADMAP.md` — 8 phases (44-51), success criteria, dependency graph, parallel wave {47,48}
3. `.planning/REQUIREMENTS.md` — 9 requirements (DESIGN-01..07 + VALIDATE-01..02) with Traceability table
4. `.planning/research/v10-orchestrator-design/SUMMARY.md` — synthesis of 4 research threads (STACK/FEATURES/ARCHITECTURE/PITFALLS), 16 OQs, 7 load-bearing pitfalls, suggested phase structure
5. `.planning/research/v10-orchestrator-design/STACK.md` / `FEATURES.md` / `ARCHITECTURE.md` / `PITFALLS.md` — 4 underlying research docs (~260KB total)
6. Notion "架构2.0" page_id `39511082-af8e-80d7-83b6-e5df50d3f07c` (Kimi 2026-07-06 设计)
7. `~/.hermes/agents/` (future agent YAML location) + `~/.hermes/skills/.audit/` (v6.0 audit log)

**Next action:** After user approval of ROADMAP, plan Phase 44 (`/gsd:plan-phase 44`). Phase 44 has no `--research-phase` flag (well-documented patterns from SUMMARY).

**Resume from interrupted phase:** Not yet started — first v10.0 phase.

---

*Last updated: 2026-07-06 — v10.0 ROADMAP.md + STATE.md + REQUIREMENTS.md traceability updated. 8 phases (44-51), 9/9 reqs mapped, zero-code design-only milestone. Awaiting user approval to start planning Phase 44 (FIRST-PRINCIPLES).*

## Operator Next Steps

**v10.0 milestone is in PLANNING.** Operator actions:

1. Review `.planning/ROADMAP.md` (8 phases 44-51, 9/9 reqs mapped)
2. Review `.planning/STATE.md` (this file — accumulated context)
3. Approve roadmap (or provide revision feedback)
4. After approval: `/gsd:plan-phase 44` to start with FIRST-PRINCIPLES

**Operator-action-handoffs from v9.0 (post-tag, NOT gaps, do NOT block v10.0):**

- (a) Phase 41 LTX2.3 live GPU testing (V9-FUTURE-02)
- (b) Phase 42 5 平台 API key configuration + live data ingestion (V9-FUTURE-01)
