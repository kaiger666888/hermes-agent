# Roadmap: Hermes Agent — Kai's Personal Agent Platform

## Overview

v10.0 is a **design-only milestone** (zero code changes, analog to v2.0 PRFP). It produces 7 design docs + 2 validation artifacts that together specify the Hermes-Agent orchestrator + Hermes-native expert agents + Claude Code execution场 three-layer architecture, derived from first principles and informed by Kimi Notion 架构2.0 + the 4 in-repo research threads (STACK / FEATURES / ARCHITECTURE / PITFALLS). The design suite will guide the v11.0 PoC implementation milestone. Milestone numbering continues from v9.0 Phase 43.

## Milestones

- ✅ **v1.0 Movie-Experts Suite v2** - Phases 0-6 (shipped 2026-06-15)
- ✅ **v2.0 PRFP Pipeline Design** - Phases 7-12 (shipped 2026-06-16)
- ✅ **v3.0 Skills-to-DAG Alignment** - Phases 13-18 (shipped 2026-06-17)
- ✅ **v4.0 Methodology Backfill** - Phases 19-21 (shipped 2026-06-18)
- ✅ **v5.0 V8.6 Adaptation** - Phases 22-27 (shipped 2026-06-19)
- ✅ **v6.0 Self-Evolution Feedback Loop** - Phases 28-33 (shipped 2026-06-24)
- ✅ **v7.0 openclaw → hermes Migration** - Phases 34-37 (shipped 2026-06-25)
- ✅ **v9.0 kais-movie-pipeline 闭环深化** - Phases 38-43 (shipped 2026-06-27)
- 🚧 **v10.0 Hermes-Agent 编排架构第一性原理推导(设计型)** - Phases 44-51 (in planning)

## Phases

**Phase Numbering:**
- Integer phases (44, 45, 46...): Planned v10.0 milestone work
- Decimal phases (e.g., 45.1): Urgent insertions after planning (marked INSERTED)

- [ ] **Phase 44: FIRST-PRINCIPLES** - 7 锁定决策推导链 + 「v10.0 显式拒绝」总表(FEATURES §11 + ARCHITECTURE §8 + PITFALLS 行业案例三合一)
- [ ] **Phase 45: AGENT-SCHEMA** - 18-field agent YAML schema + memory-record-schema + curator evolution phase 契约(7 load-bearing pitfall 字段级缓解的物理载体)
- [ ] **Phase 46: ROUND-TABLE-PROTOCOL** - Turn lifecycle + memory conflict arbitration + 强制串行约束 + 7 MCP tool 契约
- [ ] **Phase 47: KIMI-COMPARISON** - T6 vs Kimi 全 MCP shim 7 维度对照 + subagent 形态否决论据 + Microsoft 三层协议验证(parallel-eligible)
- [ ] **Phase 48: CROSS-REPO-IMPACT** - 3-location 同步策略 + Option B → 物理分区迁移触发条件 + project slug 稳定性(parallel-eligible)
- [x] **Phase 49: MIGRATION-PATH** - 15 expert × 5-field transform + memory schema 迁移 + retained-phases allowlist (PLANNED)
- [ ] **Phase 50: POC-PLAN** - v11.0 PoC 验收条件清单(fitness battery / latency SLO / bias canary / compaction / dry-run-first)
- [ ] **Phase 51: VALIDATE** - Cross-doc consistency lint script + milestone audit(严格 LAST,类比 v9.0 Phase 43)

## Phase Details

### Phase 44: FIRST-PRINCIPLES
**Goal**: 锁定 7 个设计决策的第一性原理推导论据 + 合并业界 anti-features 为「v10.0 显式拒绝」总表,作为后续 6 份设计文档的共同基础
**Depends on**: Nothing (first phase of v10.0)
**Requirements**: DESIGN-01
**Success Criteria** (what must be TRUE):
  1. 文件 `.planning/research/v10-orchestrator-design/00-FIRST-PRINCIPLES.md` 存在,包含 7 个决策的 first-principles 推导链(每决策从根本需求推到选型,非类比)
  2. 「v10.0 显式拒绝」总表 ≥10 条 anti-features / anti-patterns,每条引用三个 source(FEATURES §X + ARCHITECTURE §Y + PITFALLS §Z)的具体章节号
  3. 显式覆盖 FEATURES §10 borrowable points 中至少 B1.3 / B3.5 / B4.1 / B7.2 / B5.1(每点有明确赞同/拒绝/改造结论)
  4. 后续 6 份设计文档可在不重新推导决策的前提下引用本文档作为字段/协议/迁移决策的根论据
**Plans**: 1 plan
Plans:
- [x] 44-01-PLAN.md — 7 决策 first-principles 推导 + 显式拒绝总表 + borrowable points 评估 + 后续 6 docs 引用指南 (4 tasks, single-file deliverable)
**UI hint**: no

### Phase 45: AGENT-SCHEMA
**Goal**: 定义 18-field agent YAML schema + memory-record-schema,作为所有下游设计文档(02/04/05/06)字段引用的物理载体,把 7 个 load-bearing pitfall 的字段级缓解固化
**Depends on**: Phase 44(FIRST-PRINCIPLES 锁定 anti-features 总表作为 schema 字段论据)
**Requirements**: DESIGN-02
**Success Criteria** (what must be TRUE):
  1. 文件 `01-AGENT-REGISTRY-SCHEMA.md` + `agents-schema.yaml`(完整 JSON Schema 定义,18 字段)+ `memory-record-schema.yaml`(独立 schema,含 `expires_at` / `verified_at` / `supersedes_memory_id` / `confidence` / `half_life_days` / `evidence_chain` / `evidence_operator_ids` / `status` / `confidentiality` / `scope`)全部存在
  2. per-agent memory tier 规范文档化(core / working / archival 三层 + `memory.max_records` 上限 + compaction 触发条件,解决 OQ-7)
  3. curator `_memory_evolution_phase` 字段契约文档化(类比 v6.0 `_feedback_scan_phase`,执行顺序 + dry-run-by-default + try/except 隔离边界,解决 OQ-16)
  4. 15 expert 转化映射表(从 ARCHITECTURE §2 拷贝,SKILL frontmatter → agent YAML)
  5. 6 个 Open Questions(OQ-1 / OQ-4 / OQ-7 / OQ-13 / OQ-14 / OQ-16)显式解决或显式 defer 到 v11.0;7 个 load-bearing pitfalls(P1/P2/P4/P5/P8/P10/P14)每个有对应 schema 字段级缓解
**Plans**: 1 plan
Plans:
- [x] 45-01-PLAN.md — 18-field agent YAML schema + memory-record-schema (2-layer) + per-agent memory tier + curator _memory_evolution_phase contract + 15-expert transform + OQ/pitfall audit (5 tasks, 3 deliverable files)
**UI hint**: no

### Phase 46: ROUND-TABLE-PROTOCOL
**Goal**: 定义 round table 协议(turn lifecycle / conflict arbitration / state schema),消费 45 的 agent schema,解决 memory 冲突,强制串行以兼容 GLM 4-key rotation
**Depends on**: Phase 45(AGENT-SCHEMA,agent schema 字段是协议参数)
**Requirements**: DESIGN-03
**Success Criteria** (what must be TRUE):
  1. 文件 `02-ROUND-TABLE-PROTOCOL.md` + `round-table-state-schema.yaml` 存在
  2. Turn lifecycle 完整定义(`round_table_open` → turn N → `submit_round_table_result`),包括 `turn_order` 策略(default round-robin + 可切换,解决 OQ-2)+ `round_id` CC 自生成 uuid 机制(解决 OQ-11)
  3. Memory conflict arbitration 规则文档化:comparator LLM pass + scope precedence(session > project > global)+ confidence-weighted voting + conflict log(解决 OQ-15,避免 P7)
  4. 强制串行约束显式声明(1 panelist 1 turn 顺序 `await`,引用 MEMORY.md `feedback-glm-overload-reduce-concurrency.md` 全局 concurrency==1 policy,解决 OQ-8)
  5. MCP tool 命名统一采用 STACK §3.2 形态(无前缀,与现有 9 个 messaging tool 风格一致,解决 OQ-9),涵盖 FEATURES borrowable points B1.4 / B2.1 / B2.3 / B4.2 / B6.1 / B7.3 / B8.2
**Plans**: 1 plan
Plans:
- [x] 46-01-PLAN.md — round table turn lifecycle + memory conflict arbitration (P7 mitigation) + 强制串行约束 (OQ-8) + 7 MCP tool STACK-form 契约 + 6 OQ + 7 borrowable points audit (5 tasks, 2 deliverable files)
**UI hint**: no

### Phase 47: KIMI-COMPARISON
**Goal**: 产出 T6 vs Kimi 全 MCP shim 方案的逐维度对照,作为 7 个锁定决策的横向验证 + subagent 形态否决的论据库
**Depends on**: Phase 44(FIRST-PRINCIPLES,7 决策推导链已锁定)
**Requirements**: DESIGN-04
**Success Criteria** (what must be TRUE):
  1. 文件 `03-COMPARISON-VS-KIMI-MCP-SHIM.md` 存在
  2. 7 维度对照表(协议 / dispatch / callback / state / 多 agent / 实现成本 / 稳定性)逐维度给出 T6 vs Kimi 方案的优劣势 + 选型论据
  3. Subagent 形态否决论据完整(引用 FEATURES §11 B4.1),包括 Claude Agent SDK 默认 context-isolated 不适合做 round table panelist 的具体原因
  4. Microsoft 三层协议分层验证(引用 FEATURES §7.4 B7.1:internal → platform-native;tool → MCP;cross-platform → A2A)证明 v10.0 T6 选型符合业界共识
  5. Kimi 方案中可借鉴的部分(如有)显式列出 + 评估借鉴条件
**Plans**: 1 plan
Plans:
- [x] 47-01-PLAN.md — T6 vs Kimi 全 MCP shim 7 维度对照 + subagent 形态否决论据 (FEATURES §11 B4.1) + Microsoft 三层协议验证 (FEATURES §7.4 B7.1) + Kimi-side borrowable 评估 + Phase 44 决策 1-7 cross-validation audit (5 tasks, single deliverable ~1400 lines)
**UI hint**: no

### Phase 48: CROSS-REPO-IMPACT
**Goal**: 定义 3-location(hermes-agent repo / kais-hermes-skills repo / `~/.hermes/`)同步策略 + Option B(v11.0 PoC filter 路由)vs 物理分区(v12+ 每 agent 一 workspace)迁移触发条件
**Depends on**: Phase 44(FIRST-PRINCIPLES)
**Requirements**: DESIGN-07
**Success Criteria** (what must be TRUE):
  1. 文件 `06-CROSS-REPO-IMPACT.md` 存在
  2. 3-location 同步策略表完整(每 location 列出存放内容 + 写权限 + 同步方向 + lineage 关系,例如 agent YAML lineage 追溯到 kais-hermes-skills SKILL)
  3. Option B(v11.0 PoC:mem0 单 backend + `agent_id` filter)vs 物理分区(v12+:每 agent 一 workspace)迁移触发条件显式文档化(规模阈值 / latency 阈值 / 何时切换,解决 OQ-12,避免 P3/P12)
  4. Round table state per-project 落盘路径设计(`.runtime/{slug}/round_tables/`,引用 ARCHITECTURE §5.1)
  5. Project slug 稳定性策略文档化(短期接受 breakage,long-term 用 `.hermes/project.id` stable ID,解决 OQ-6)
**Plans**: 1 plan
Plans:
- [x] 48-01-PLAN.md — 3-location sync strategy (per-artifact write authority matrix) + lineage chain (forward/backward/drift/L1-L5 invariants) + Option B vs Physical Partition migration triggers (3 threshold classes) + project slug stability (short-term breakage + long-term .hermes/project.id) + round-table state path + Phase 44 7 决策 audit + OQ-6/OQ-12/CC-4 resolution (5 tasks, single deliverable ~1300+ lines)
**UI hint**: no

### Phase 49: MIGRATION-PATH
**Goal**: 定义 Python runner 增量迁移计划 —— 15 expert 从 SKILL frontmatter 到 agent YAML 的 transform 规则 + memory schema 从 v6.0 FeedbackStore 到新 memory-record-schema 的迁移 + retained-phases allowlist
**Depends on**: Phase 45(AGENT-SCHEMA)+ Phase 46(ROUND-TABLE-PROTOCOL)
**Requirements**: DESIGN-05
**Success Criteria** (what must be TRUE):
  1. 文件 `04-MIGRATION-PATH.md` 存在
  2. 15 expert × 5-field transform 规则表完整(每 expert 列出 SKILL frontmatter → agent YAML 的 5 个字段映射 + 默认值 + edge cases)
  3. `default_invocation: skill_fallback → mcp_tool` 切换机制文档化(agent 优先用 MCP tool,失败回退 SKILL form)
  4. Memory schema 迁移计划(从 v6.0 FeedbackStore JSONL 到新 memory-record-schema),包括 `schema_version` 字段 + dry-run migration 模式(避免 P14)
  5. Retained-phases allowlist 显式声明(`run_python_phase` 只接受 Step 7/10/11/12/0/6.5/15,allowlist 位置在 `round-table-schema.yaml`,解决 OQ-10)+ 旧 v7.0 mem0 `agent_id=hermes` memory 遗留策略(解决 OQ-3)
**Plans**: 1 plan
Plans:
- [x] 49-01-PLAN.md — 15-expert 75-cell transform rules (5-field per-expert table + edge cases + FOUND-08 preserved) + default_invocation skill_fallback → mcp_tool switching (3-state enum + 12-cell failure matrix + transition path) + memory schema migration (v6.0 FeedbackStore → memory-record-schema, schema_version + dry-run + safe-default mitigates P14) + retained-phases allowlist (Steps 0/6.5/7/10/11/12/15 in round-table-state-schema.yaml) + legacy v7.0 mem0 agent_id=hermes policy + Phase 44 7 决策 audit + OQ-3/OQ-10/P14 resolution (5 tasks, single deliverable ~1300+ lines)
**UI hint**: no

### Phase 50: POC-PLAN
**Goal**: 收口 v10.0 设计 —— 汇总前 6 份文档的 pitfall 缓解,产 v11.0 PoC 的验收条件清单 + 工作量估算 + risk register,作为 v11.0 实施者直接照着写的实施蓝本
**Depends on**: Phase 49(MIGRATION-PATH,transform 规则就绪)+ 间接依赖前面所有 design docs
**Requirements**: DESIGN-06
**Success Criteria** (what must be TRUE):
  1. 文件 `05-POC-PLAN.md` 存在
  2. PoC 目标明确(vertical slice:1 个 creative phase + 1 个 infra phase,具体选择有论据)
  3. 验收条件清单完整,涵盖:fitness battery 设计(引用 PITFALLS §P8)+ latency SLO(p95 < 500ms,mem0 scoped retrieval)+ bias canary(curator `_memory_evolution_phase` hallucination 检测)+ compaction pass(`memory.max_records` 触发)+ threshold tuning(初始默认值 + 调优路径)+ dry-run-first invariant(curator 默认 dry-run)+ schema migration dry-run —— 每项 1-3 天工作量估算
  4. Risk register(7 load-bearing pitfalls P1/P2/P4/P5/P6/P7/P8 × PoC deferral 评估)完整,每 pitfall 标注 must-fix-in-PoC vs defer-with-monitoring
  5. PoC 实施路径图(从 fitness battery → schema migration dry-run → bias canary 顺序,引用 STACK §7 token 成本估算 ~550K/pipeline run)
**Plans**: 1 plan
Plans:
- [ ] 50-01-PLAN.md — v10.0 capstone PoC blueprint: vertical slice selection (creative=screenplay Step 3 + infra=agent registry + 1 round table) + 7-item acceptance criteria (12 person-days total) + 7-row risk register (P1/P2/P4/P5/P7/P8 must-fix + P6 PARTIAL) + implementation path (fitness battery → schema migration dry-run → bias canary sequence) + Phase 44 7 决策 audit + OQ-7/OQ-16/P14 resolution (5 tasks, single deliverable ~1300+ lines)
**UI hint**: no

### Phase 51: VALIDATE
**Goal**: v10.0 milestone close-out —— 产出 cross-doc consistency lint 脚本(VALIDATE-02)+ milestone audit 报告(VALIDATE-01),验证 9/9 reqs 满足 + 7 design docs cross-reference 一致 + 16 Open Questions 全部解决或显式 defer
**Depends on**: All previous phases(44-50)—— audit 必须严格 LAST,类比 v9.0 Phase 43 / v5.0 Phase 27 close-out 模式
**Requirements**: VALIDATE-01, VALIDATE-02
**Success Criteria** (what must be TRUE):
  1. `scripts/v10-consistency-check.py` lint 脚本存在,自动检查 7 design docs 的术语一致(`agent` / `skill` / `round table` / `panel` / `turn` 等)+ schema 引用一致(`agents-schema.yaml` 字段名 == design docs 提及)+ 决策号引用一致(决策 1-7 在每个 doc 描述一致)+ MCP tool 命名一致(统一 STACK 形态)
  2. lint 脚本对所有 7 design docs 跑通,零 ERROR(WARNING 可接受,需在 audit 报告列出)
  3. 文件 `.planning/milestones/v10.0-MILESTONE-AUDIT.md` 存在,9/9 reqs 逐 req 核对 deliverables(每 req 引用其 phase SUMMARY)
  4. Audit 报告核对:7 design docs cross-reference 一致(术语 / schema / 决策号 across docs 不矛盾)+ 16 Open Questions(SUMMARY.md OQ-1..OQ-16)全部解决或显式 defer 到 v11.0 + 7 load-bearing pitfalls 全部有字段级缓解(在 45 / 46 / 50 中)+ 4 research 引用链完整(每 design doc 引用的 STACK/FEATURES/ARCHITECTURE/PITFALLS 章节可追溯)
  5. Audit 报告给出 milestone-level PASS / tech_debt / FAIL 结论,带 evidence 指针(每条核对项引用具体文件 + 章节)
**Plans**: TBD
**UI hint**: no

## Critical Path & Parallel Waves

```
                                                                                                              ┌─────────────────────────────┐
                                                                                                              │ Phase 51 (VALIDATE)          │
                                                                                                              │ strictly LAST                │
                                                                                                              │ (lint script + audit)        │
                                                                                                              └────────────▲────────────────┘
                                                                                                                           │
                                                                ┌──────────────── Phase 50 (POC-PLAN) ────┘
                                                                │   收口,依赖前面所有
                                                                │
                                          ┌──── Phase 49 (MIGRATION) ───┘
                                          │     依赖 45+46
                                          │
                  ┌──── Phase 46 (ROUND-TABLE) ──┐
                  │     依赖 45                    │
                  │                               │
Phase 44 ──┬──── Phase 45 (AGENT-SCHEMA) ────────┘
(FIRST-    │
 PRINCIPLES)├──── Phase 47 (KIMI-COMPARISON) ────────────────────────────┐  PARALLEL-ELIGIBLE WAVE:
           │     独立,只依赖 44                                            │  {47, 48} 可与 {45, 46}
           └──── Phase 48 (CROSS-REPO) ───────────────────────────────────┘  并行启动(独立横切文档)
                 独立,只依赖 44
```

**Critical path:** 44 → 45 → 46 → 49 → 50 → 51(6 sequential steps)
**Parallel-eligible:** Phase 47 + Phase 48 可与 Phase 45/46 并行(独立横切文档,不依赖 schema 字段细节)

## Progress

**Execution Order:**
Phases execute in numeric order with parallel wave {47, 48} overlapping {45, 46}.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 44. FIRST-PRINCIPLES | v10.0 | 1/1 | Complete    | 2026-07-06 |
| 45. AGENT-SCHEMA | v10.0 | 1/1 | Complete    | 2026-07-06 |
| 46. ROUND-TABLE-PROTOCOL | v10.0 | 1/1 | Complete    | 2026-07-06 |
| 47. KIMI-COMPARISON | v10.0 | 1/1 | Complete    | 2026-07-06 |
| 48. CROSS-REPO-IMPACT | v10.0 | 1/1 | Complete    | 2026-07-06 |
| 49. MIGRATION-PATH | v10.0 | 1/1 | Complete    | 2026-07-06 |
| 50. POC-PLAN | v10.0 | 1/1 | Planned     | - |
| 51. VALIDATE | v10.0 | 0/TBD | Not started | - |

---

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

*Last updated: 2026-07-06 — v10.0 ROADMAP created (8 phases 44-51, 9/9 reqs mapped, design-only milestone analog to v2.0 PRFP).*
