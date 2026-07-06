---
title: "05 — PoC Plan (Capstone)"
project: hermes-agent v10.0 编排架构第一性原理推导
doc_id: 05-POC-PLAN
status: LOCKED-PENDING-VALIDATE  # design-only milestone; Phase 51 VALIDATE cross-checks
phase: 50-poc-plan
audience:
  - Kai (operator reviewer — approve PoC scope/feasibility)
  - v11.0 PoC implementer (direct blueprint consumer)
  - Phase 51 VALIDATE (cross-doc lint + risk-register alignment)
reading_time: "~45 min"
stability:
  - "vertical slice selection: STABLE (rooted in Phase 44 决策 3 D2 + 决策 1 T6)"
  - "7-item acceptance criteria: STABLE (each maps 1:1 to PITFALLS §P mitigation)"
  - "7-row risk register: STABLE (verbatim verdicts from PITFALLS §Risk Register Summary line 470-488)"
  - "PoC implementation path: STABLE (sequence rationale has hard preconditions, not arbitrary ordering)"
confidence: HIGH
predecessors:
  - 00-FIRST-PRINCIPLES.md (Phase 44 — 7 决策 root)
  - 01-AGENT-REGISTRY-SCHEMA.md (Phase 45 — agents-schema.yaml + memory-record-schema.yaml)
  - 02-ROUND-TABLE-PROTOCOL.md (Phase 46 — round-table-state-schema.yaml + conflict arbitration)
  - 03-COMPARISON-VS-KIMI-MCP-SHIM.md (Phase 47 — T6 vs Kimi defense)
  - 04-MIGRATION-PATH.md (Phase 49 — §4 memory migration + §5 retained-phases)
  - 06-CROSS-REPO-IMPACT.md (Phase 48 — Option B vs 物理分区)
  - PITFALLS.md (14 pitfalls + §Risk Register Summary line 470-488 — CANONICAL SOURCE)
  - STACK.md (§3.2 7 MCP tool + §7 token cost ~550K/pipeline run)
  - SUMMARY.md (§Risk Register line 145-160 + §Gaps to Address line 172-178)
  - MEMORY.md v6-self-evolution-milestone (fitness battery precedent)
---

# 05-POC-PLAN.md — v10.0 编排架构设计套件的收口 capstone

> **本文件是 v10.0 设计套件 (Phase 44-50) 的最后一篇 design doc.** Phase 51 VALIDATE 是 lint + audit, 不是 design doc. 本 doc 把前 6 份 design docs (00-FIRST-PRINCIPLES / 01-AGENT-REGISTRY-SCHEMA / 02-ROUND-TABLE-PROTOCOL / 03-COMPARISON-VS-KIMI-MCP-SHIM / 04-MIGRATION-PATH / 06-CROSS-REPO-IMPACT) 的 pitfall 缓解汇总成 v11.0 PoC 的实施蓝本 —— vertical slice selection + 7-item acceptance criteria + 7-row risk register + PoC implementation path —— 让 v11.0 PoC 实施者引用本 doc 即可 defending "what do I build first? what does done look like? which pitfalls can I defer?".

---

## §0 阅读指南 (Reading Guide)

### 章节地图 (Chapter Map)

| 章节 | 主题 | SC# | 主要受众 | 估读时间 |
|------|------|-----|----------|----------|
| §1 | Framing + 4 deliverables 宣告 + capstone-at-a-glance | SC#1 | 全部 | 8 min |
| §2 | PoC scope boundary — "done" 定义 + explicit exclusions | SC#1 | Kai + implementer | 6 min |
| §3 | Vertical slice selection (creative + infra) | SC#2 | implementer | 12 min |
| §4 | 7-item acceptance criteria + 12-person-day estimate | SC#3 | implementer + Kai | 12 min |
| §5 | 7-row risk register (P1/P2/P4/P5/P6/P7/P8 × verdict) | SC#4 | implementer + Phase 51 | 10 min |
| §6 | PoC implementation path (sequence + 6-week calendar) | SC#5 | implementer | 8 min |
| §7 | Phase 44 7 决策 cross-validation audit | — | Phase 51 VALIDATE | 5 min |
| §8 | Downstream citation guide + coherence + References | — | Phase 51 + implementer | 4 min |

### 三类读者的进入点 (3-Audience Entry Point)

1. **Kai (operator reviewer)** —— 若只读 5 分钟: 读 §1.6 capstone-at-a-glance + §2.4 budget (~15-17 person-days + ~6 calendar weeks) + §5.8 risk register summary. 决定是否批准 v11.0 PoC milestone.
2. **v11.0 PoC implementer** —— 若是直接照着写代码: 读 §3 (vertical slice scope) + §4 (7 acceptance criteria, 每项有 task decomposition + day estimate) + §5 (每 pitfall must-fix vs defer-with-monitoring) + §6 (6-week calendar). 不需重新推导 Phase 44 决策或 re-litigate pitfall mitigations.
3. **Phase 51 VALIDATE** —— 若是 cross-doc audit: 读 §5.8 (risk register summary, 跟 PITFALLS §Risk Register Summary line 470-488 + SUMMARY §Risk Register line 145-160 对齐) + §7.1 (7 决策 audit table) + §7.3 (OQ + pitfall resolution declarations) + §4.8 (acceptance criteria summary, 跟 ROADMAP SC#3 + DESIGN-06 deliverable 对齐).

### 稳定性 markers (Stability Declaration)

| 章节 | 稳定性 | 依据 |
|------|--------|------|
| §1 framing | LOCKED | Phase 44 决策 1-7 已 LOCKED, 不可 re-derive |
| §3 vertical slice | STABLE | 决策 1/3/5/6/7 root, 非 arbitrary |
| §4 acceptance criteria | STABLE | 每 item 1:1 映射 PITFALLS §PX mitigation |
| §5 risk register | STABLE | verdict 来自 PITFALLS §Risk Register Summary line 470-488 |
| §6 implementation path | STABLE | sequence 有硬 precondition (fitness battery before curator), 非 arbitrary |

### 本 doc 从前序文档消费什么 (What This Doc Consumes)

本 doc **不 re-derive** 任何前序 design doc 的 locked 结论, 只 **cite + aggregate**:

| 消费源 | 本 doc 引用方式 | 章节 |
|--------|-----------------|------|
| 00-FIRST-PRINCIPLES.md §2.1-§2.7 | 决策号 (1/3/5/6/7) 引用, 不重推 | §1.1, §3, §7.1 |
| 01-AGENT-REGISTRY-SCHEMA.md (agents-schema.yaml + memory-record-schema.yaml) | 字段名 (persona_sha256 / fitness_battery / evidence_chain / scope / project_id / memory.max_records) 引用 | §4, §5 |
| 02-ROUND-TABLE-PROTOCOL.md (round-table-state-schema.yaml + §3 conflict arbitration) | lifecycle + scope precedence + confidence-weighted voting 引用 | §3.2, §5.6 |
| 03-COMPARISON-VS-KIMI-MCP-SHIM.md | T6 决策论据 | §3.3 (背景), §7.1 |
| 04-MIGRATION-PATH.md §4 + §5 | `hermes agent memory migrate --dry-run` + retained-phases allowlist 引用 | §4.7, §6.3 |
| 06-CROSS-REPO-IMPACT.md §3 | Option B vs 物理分区 migration trigger 引用 | §4.2, §6.6 |
| PITFALLS.md §P1/§P2/§P4/§P5/§P6/§P7/§P8 + §P14 + §Risk Register Summary (line 470-488) | mitigation 编号引用 + verdict 对齐 | §4, §5 |
| STACK.md §3.2 (7 MCP tool) + §7 (~550K/pipeline run, ~340 MCP call) | MCP tool 名 + token cost 引用 | §3.3, §6.2 |
| SUMMARY.md §Risk Register (line 145-160) + §Gaps to Address (line 172-178) | verdict 对齐 + PoC measurable gaps 引用 | §4, §5, §6.6 |
| MEMORY.md v6-self-evolution-milestone | v6.0 fitness battery precedent 引用 | §4.1 |
| CLAUDE.md (deliverable form canon) | 双语结构 (EN headers + 中文 prose) 规则 | 全文 |

---

## §1 Framing — Capstone Purpose + 4 Deliverables

### §1.1 v10.0 设计套件的收口 (Capstone of the Design Suite)

本文档是 **v10.0 设计套件的收口 capstone** —— 汇总前 6 份 design docs 的 pitfall 缓解, 产 v11.0 PoC 的 **4 件套实施蓝本**:

- **(a) Vertical slice selection** (1 creative phase + 1 infra phase, 论据完整非任意挑) —— 见 §3
- **(b) 7-item acceptance criteria checklist** (每项 1-3 天工作量估算, 总 12 person-days) —— 见 §4
- **(c) 7-row risk register** (P1/P2/P4/P5/P6/P7/P8 × must-fix-in-PoC vs defer-with-monitoring verdict + rationale, 与 PITFALLS §Risk Register Summary line 470-488 + SUMMARY §Risk Register line 145-160 对齐) —— 见 §5
- **(d) PoC 实施路径** (fitness battery → schema migration dry-run → bias canary sequence, STACK §7 ~550K/pipeline-run token cost scoping) —— 见 §6

本 doc 是 **Phase 44 决策 6 (per-agent memory + curator-driven 自进化)** + **决策 7 (Hermes 控 structure)** 的 PoC 验收路径落实. 这两个决策是整个 PoC scope 的 root —— 决策 6 是整个 PoC 验证的核心机制 (per-agent memory 是 v10.0 的差异化设计), 决策 7 是 §4.1 fitness battery + §4.3 bias canary + §4.6 dry-run-first 三项 acceptance criteria 的 enforcement 方向 (Hermes-side, 不是 CC-side).

#### Phase 44 决策 citation (cite-only, 不 re-derive)

| 决策 # | 决策 (一句话) | 本 doc 角色 |
|--------|---------------|-------------|
| 决策 1 | T6 协议 (Hermes MCP server + tmux dispatch + CC native MCP client) | §3.3 infra vertical slice root (7 MCP tool surface) |
| 决策 3 | D2 storyboard-first-class | §3.2 creative vertical slice root (screenplay is D2-compatible) |
| 决策 5 | α agent form (YAML + persona + tools + refs + memory_scope + lineage) | §3.3 infra slice agent registry entry root |
| 决策 6 | per-agent memory + curator-driven 自进化 | **LOAD-BEARING FOR ENTIRE PoC SCOPE** —— 整个 PoC 验证决策 6 的可行性 |
| 决策 7 | 分层 CC 角色 (Hermes 控 structure; CC 控 内容) | §4.1/§4.3/§4.6 acceptance criteria 的 enforcement 方向 (Hermes-side) |

(决策 2 B3a Python runner 增量迁移 + 决策 4 G2 通用编排框架 在 §7.1 audit table 出现, 但不是 vertical slice 的直接 root.)

#### ROADMAP SC#1-5 + DESIGN-06 (本 doc 解决 5 SC)

| SC# | 描述 | 本 doc 章节 |
|-----|------|-------------|
| SC#1 | `05-POC-PLAN.md` 文件存在 | 全文 |
| SC#2 | PoC 目标明确 (vertical slice: 1 creative + 1 infra, 论据完整) | §3 |
| SC#3 | 验收条件清单完整 (7 项, 每项 1-3 天, total 12 person-days) | §4 |
| SC#4 | Risk register (7 load-bearing pitfalls × PoC deferral 评估) | §5 |
| SC#5 | PoC 实施路径图 (fitness battery → schema migration dry-run → bias canary sequence, cite STACK §7) | §6 |

(DISTINCT-VALIDATE-08 SC: Phase 51 cross-doc lint + completeness audit —— 不在本 doc 解决, 是 Phase 51 VALIDATE 的 deliverable.)

#### 净新综合 vs cite-only (What's net-new vs what's cited)

本 doc 的 **净新综合** (net-new synthesis) 是:

1. **Vertical slice 论据** —— §3.2 screenplay Step 3 + §3.3 agent registry + 1 round table 的 5-dimension selection criteria + scorecard + edge case, 非 arbitrary pick
2. **12-person-day 估算** —— §4 每项 acceptance criterion 的 task decomposition (设计 + 实施 + 验证 三 phase, sub-task 级 day-fraction estimate), 基于 first-principles 分解, 非 gut feel
3. **Sequencing rationale** —— §6.1 fitness battery FIRST → schema migration dry-run SECOND → bias canary THIRD 的硬 precondition 逻辑 (fitness battery = regression-detection foundation must exist before any curator tick)
4. **Per-pitfall PoC verdict** —— §5.1-§5.7 每 pitfall 显式标注 must-fix-in-PoC / PARTIAL / defer-with-monitoring + §4 中哪个 acceptance criterion gate 这个 mitigation
5. **Per-vertical-slice token cost** —— §6.2 screenplay Step 3 ~148K tokens / infra slice ~10K tokens 的 per-slice 估算 (基于 STACK §7.3 ~550K/13 ≈ 42K 平均值的 screenplay-density 上调)

本 doc 的 **cite-only** (consumed, not re-derived) 是:

- Phase 44 决策 1-7 (尤其决策 6 + 7)
- Phase 45 agents-schema.yaml 18 fields + memory-record-schema.yaml 10+ fields
- Phase 46 round-table-state-schema.yaml + conflict arbitration rules
- Phase 49 §4 (memory migration dry-run) + §5 (retained-phases allowlist)
- PITFALLS §P1/§P2/§P4/§P5/§P6/§P7/§P8 + §P14 mitigation 编号 + §Risk Register Summary (line 470-488)
- STACK §3.2 (7 MCP tool surface) + §7.1/§7.3 (~340 MCP call, ~550K tokens per pipeline run)
- SUMMARY §Risk Register (line 145-160) + §Gaps to Address (line 172-178)

### §1.2 范围规则 (Scope Rules)

本 doc 汇总 **PITFALLS §Risk Register Summary (line 470-488)** + **SUMMARY §Risk Register (line 145-160)** + **STACK §7 token cost** + **Phase 49 §4-§5** 到可执行 PoC 蓝图粒度.

本 doc **不讨论**:

- (a) Agent YAML schema 字段定义本身 —— 留给 Phase 45 agents-schema.yaml + memory-record-schema.yaml
- (b) Round table protocol 字段细节 —— 留给 Phase 46 round-table-state-schema.yaml
- (c) v11.0 PoC live implementation —— 本 doc 是 design-only milestone, v11.0 PoC 是下一个 milestone
- (d) mem0 backend 部署拓扑 —— 留给 Phase 48 Option B vs 物理分区决策 (本 doc §4.2 latency benchmark 可能 trigger 物理分区, 但拓扑设计本身不在本 doc)
- (e) Cross-doc lint 脚本 —— 留给 Phase 51 VALIDATE
- (f) A2A protocol —— post-v12+, 不在 v10.0 scope

引用 Phase 44 决策 1-7 + Phase 45 agents-schema.yaml 18 fields + memory-record-schema.yaml 10+ fields + Phase 46 round-table-state-schema.yaml + Phase 49 §4 memory migration + §5 retained-phases allowlist 采用 **CITE-ONLY 策略**, 不重定义.

### §1.3 SC#1-5 Mapping Table

| SC# | 描述 (ROADMAP §Phase 50) | 本 doc 解决章节 | 验证脚本 (Phase 51 VALIDATE) |
|-----|--------------------------|-----------------|------------------------------|
| SC#1 | File `05-POC-PLAN.md` exists | 全文 | `test -f .planning/research/v10-orchestrator-design/05-POC-PLAN.md` |
| SC#2 | PoC 目标明确 (vertical slice: 1 creative + 1 infra, 论据完整) | §3 (§3.2 screenplay + §3.3 infra) | `grep "screenplay Step 3" + grep "agent registry"` |
| SC#3 | 验收条件清单完整 (7 项, 每项 1-3 天, total 12 person-days) | §4 (§4.1-§4.8) | `grep "fitness battery" + grep "latency SLO" + grep "12 person-days"` |
| SC#4 | Risk register (7 load-bearing pitfalls × PoC deferral) | §5 (§5.1-§5.10) | `grep "PITFALLS §P1" + grep "must-fix" + grep "defer-with-monitoring"` |
| SC#5 | PoC 实施路径图 (fitness battery → schema migration dry-run → bias canary) | §6 (§6.1-§6.6) | `grep "fitness battery FIRST" + grep "schema migration dry-run SECOND" + grep "bias canary THIRD"` |

### §1.4 Roadmap Placement

本 doc 是 **v10.0 设计套件的 LAST design doc** (Phase 51 VALIDATE 是 lint + audit, 不是 design doc).

v11.0 PoC implementer 引用本 doc 的 §3 (vertical slice) + §4 (acceptance criteria) + §5 (risk register) + §6 (implementation path) 即可 defending:

- "**What do I build first?**" → §3.3 infra slice first (~3 days setup), then §3.2 creative slice on top (~2 days)
- "**What does 'done' look like?**" → §2.1 PoC done 定义 + §4.8 acceptance criteria summary + §6.5 PoC exit criteria
- "**Which pitfalls can I defer?**" → §5.8 risk register summary (6 must-fix + P6 PARTIAL; P3/P9/P10/P11/P12/P13/P14 不在 SC#4 7-pitfall scope, 见 §5.10)

Phase 51 VALIDATE 的 lint 脚本会 cross-check 本 doc 的:

- §5.8 risk register verdicts 与 PITFALLS §Risk Register Summary line 470-488 + SUMMARY §Risk Register line 145-160 一致
- §4 acceptance criteria 引用的 schema 字段 (`persona_sha256` / `evidence_chain` / `memory.max_records` / `scope` / `project_id`) 与 Phase 45/46/49 一致
- §7.1 7 决策 audit 与 00-FIRST-PRINCIPLES.md §2.1-§2.7 一致

**Phase 44 决策 1-7 + Phase 45 schemas + Phase 46 protocol + Phase 49 transform rules + Phase 48 cross-repo strategy 都是 LOCKED** —— 本 doc only aggregates + sequences, 不 re-derive 也不 re-litigate.

### §1.5 4 Deliverables Declared Upfront

本 doc 在 §3-§6 提供的 4 个 lockable artifacts:

#### §1.5.1 Vertical slice selection (SC#2, §3)

- **Creative slice** = screenplay Step 3 round table (决策 3 D2 storyboard-first-class; ARCHITECTURE §2 screenplay row — HOOK-09 emotion_curve marker contract load-bearing + 5 refs + 9 related_agents densest round table + tools include write_file/patch; Phase 49 §2.4 screenplay transform rules)
- **Infra slice** = agent registry + 1 round table invocation (决策 1 T6 协议; STACK §3.2 7 MCP tool surface; Phase 46 round-table-state-schema full lifecycle; Phase 45 agents-schema.yaml 18-field entry)
- **Net-new**: 论据完整非任意挑 —— 5-dimension selection criteria (round-table density / schema-field coverage / decision coverage / synthetic-input feasibility / isolation safety) + scorecard per slice + edge case per slice

#### §1.5.2 7-item acceptance criteria checklist (SC#3, §4) — 12 person-days total

| # | Criterion | Cite | Days |
|---|-----------|------|------|
| 1 | Fitness battery design | PITFALLS §P8 mitigation 1 + Label Studio + Shaped.ai | 3 |
| 2 | Latency SLO p95<500ms | PITFALLS §P3 mitigation 4 + Phase 48 Option B | 2 |
| 3 | Bias canary | PITFALLS §P5 mitigation 4 + SUMMARY §Gaps line 176 | 2 |
| 4 | Compaction pass | PITFALLS §P9 + SUMMARY OQ-7 | 1 |
| 5 | threshold tuning | PITFALLS §P13 + (P1/P2/P4/P6/P7 mitigation refs) | 1 |
| 6 | Dry-run-first invariant | PITFALLS §P5 mitigation 5 + SUMMARY OQ-16 | 1 |
| 7 | Schema migration dry-run | Phase 49 §4.5 + PITFALLS §P14 mitigation 3 | 2 |
| **Total** | | | **12** |

> Per-pitfall PoC verdict detail (cited by PITFALLS §P1/§P2/§P4/§P5/§P6/§P7/§P8 + §P14): see §5 risk register.

- **Net-new**: per-item task decomposition to 1-3 day estimate (设计 + 实施 + 验证 三 phase, sub-task 级 day-fraction)

#### §1.5.3 7-row risk register (SC#4, §5)

- **Verdicts**: P1 must-fix / P2 must-fix / P4 must-fix / P5 must-fix / **P6 PARTIAL** (signed feedback PoC must; outlier detection defer) / P7 must-fix / P8 must-fix
- **对齐**: 与 PITFALLS §Risk Register Summary line 470-488 + SUMMARY §Risk Register line 145-160 一致 (no divergent verdicts)
- **Net-new**: per-pitfall PoC-week acceptance criterion (which §4 item gates this pitfall's mitigation) + failure-if-deferred 1 sentence

#### §1.5.4 PoC implementation path (SC#5, §6)

- **Sequence**: fitness battery FIRST → schema migration dry-run SECOND → bias canary THIRD
- **Rationale**: fitness battery = regression-detection foundation must exist before any curator tick; schema migration dry-run validates memory layer before live writes (P14); bias canary gates curator `_memory_evolution_phase` transition from dry-run to live
- **Token cost scoping**: STACK §7 ~550K/pipeline run + per-vertical-slice estimate (~148K creative screenplay Step 3 / ~10K infra 1 round table)
- **Net-new**: sequencing rationale + per-vertical-slice token estimate + 6-week calendar timeline

### §1.6 Capstone-at-a-Glance (30-second answer to "which pitfalls must the PoC fix?")

> Mirrors PITFALLS §Risk Register Summary structure (line 470-488). 7-row elevator-pitch version of §5 full risk register.

| P# | Pitfall | Severity | PoC verdict | PoC acceptance § | Failure-if-deferred |
|----|---------|----------|-------------|------------------|---------------------|
| **P1** | Persona drift | HIGH | **must-fix** | §4.1 fitness battery | HOOK-09 contract lost, screenplay 输出 wrong format |
| **P2** | Stale memory | HIGH | **must-fix** | §4.4 compaction | Obsolete platform rules cited, operator 失去信任 |
| **P4** | Cross-project leakage | HIGH | **must-fix** | §4.7 + §4.2 | Production rollout leaks P1→P2 memory |
| **P5** | Curator failure modes | HIGH | **must-fix** | §4.3 + §4.6 | Hallucinated rules silently degrade agent |
| **P6** | Memory poisoning | HIGH | **PARTIAL** | §4.6 (signed) + §5.10 (outlier defer) | Trusted operators; theoretical risk in PoC |
| **P7** | Round-table conflict | MEDIUM | **must-fix** | §3.2 creative slice | Round table deadlocks, PoC creative slice cannot complete |
| **P8** | No fitness signal | HIGH | **must-fix** | §4.1 fitness battery | No regression signal, all v11.x work operates blind |

**Summary**: 6 must-fix-in-PoC (P1/P2/P4/P5/P7/P8) + 1 PARTIAL (P6 signed feedback must, outlier defer with monitoring). Verdicts 与 PITFALLS §Risk Register Summary line 470-488 + SUMMARY §Risk Register line 145-160 完全一致 —— no divergent verdicts, 见 §5.9 对齐声明. 本表每行对应 PITFALLS §P1 / PITFALLS §P2 / PITFALLS §P4 / PITFALLS §P5 / PITFALLS §P6 / PITFALLS §P7 / PITFALLS §P8 一条. PITFALLS §P14 (schema migration) 在 §4.7 + §5.3 处理.

### §1.7 Out-of-Scope Declaration

本 doc **明确不涵盖** (each with deferral pointer):

| 不涵盖主题 | 去向 |
|------------|------|
| Agent YAML schema 字段定义本身 | Phase 45 agents-schema.yaml (18 fields) + memory-record-schema.yaml (10+ fields) |
| Round table protocol 字段细节 | Phase 46 round-table-state-schema.yaml |
| v11.0 PoC live implementation | 下一个 milestone (v11.0), 本 doc 是 design-only |
| mem0 backend 部署拓扑 (Option B vs 物理分区) | Phase 48 §3 决策 (本 doc §4.2 latency benchmark 可能 trigger 物理分区, 但拓扑本身不在本 doc) |
| Cross-doc lint 脚本 | Phase 51 VALIDATE |
| A2A protocol | post-v12+, 不在 v10.0 scope |
| Operator key management (P6 operator_signature HMAC key 分发) | Phase 48 + 运维文档, 不在设计 doc scope |

---

## §2 PoC Scope + Boundary

> 本节定义 PoC 的边界 —— what 'PoC done' means (vertical slice + acceptance criteria pass + risk register verdicts 执行) + what is explicitly NOT in PoC (full 15-agent round table, mem0 物理分区, production rollout). 边界清晰的目的是避免 PoC scope creep —— v11.0 PoC 是验证 v10.0 设计的可行性, 不是 ship production.

### §2.1 PoC "Done" 定义

PoC "done" 需满足以下 4 个条件 (all-or-nothing):

**(a) 2 vertical slices 跑通** (per §3)
- Infra slice (§3.3): 7 MCP tools wired + 1 sample agent YAML + 1 successful `round_table_open` → turn 1 → `submit_round_table_result` cycle (synthetic input)
- Creative slice (§3.2): 9-agent subset YAMLs + 1 successful Step 3 screenplay round table on synthetic StoryKernel input + `fitness_trend.jsonl` baseline entry for screenplay

**(b) 7 acceptance criteria 全 pass** (per §4)
- §4.1 fitness battery design (3d): `fitness_trend.jsonl` baseline + regression auto-quarantine logic on synthetic mean_score drop > 0.5
- §4.2 latency SLO p95 < 500ms (2d): 500-record `get_agent_memory` benchmark (excluding LLM call)
- §4.3 bias canary (2d): curator `_memory_evolution_phase` dry-run rejects single-operator-derived insight
- §4.4 compaction pass (1d): 600-record synthetic input produces valid 3-tier (core ≤10 / working ≤100 / archival ≤10000) output
- §4.5 threshold tuning (1d): audit log captures "threshold too low" runaway warning + rate-limit kicks in
- §4.6 dry-run-first invariant (1d): default mode zero memory writes; `--apply-memory` mode writes with audit log
- §4.7 schema migration dry-run (2d): dry-run output plan correct + live migration shadow-run <1% retrieval discrepancy

**(c) 7 risk register verdicts 执行** (per §5)
- 6 must-fix items (P1/P2/P4/P5/P7/P8) mitigations verified in PoC
- P6 PARTIAL: `operator_signature` schema field implemented (FeedbackRecord validates signature, anonymous rejected); outlier detection deferred with audit-log monitoring per §5.10

**(d) Token cost 实测 ≈ STACK §7 估算** (within 2x)
- Full pipeline baseline: ~550K tokens / pipeline run (per STACK §7.3 line 1026)
- Per-vertical-slice estimate (per §6.2):
  - Creative slice screenplay Step 3 (9 related_agents, denser than average): ~148K tokens (~4.5K MCP overhead + ~143K LLM opinion calls)
  - Infra slice 1 round table invocation (3 agents × 1 turn × 2 call): ~10K tokens
- Acceptance: 实测 within 2x of estimate (PoC 不要求精确预测, 但要求量级一致 —— 若实测 5x, 说明 STACK §7 估算模型有结构性偏差)

**Exit condition**: PoC "done" 还要求 commit `.planning/milestones/v11.0-POC-REPORT.md` 报告, 含 (1) 7 acceptance criteria pass/fail per item, (2) 7 risk register verdicts 执行状态, (3) token cost 实测 vs estimate 对比表, (4) 30-day shadow-run <1% retrieval discrepancy 数据, (5) 下一步 (v11.1+) recommended scope.

### §2.2 PoC Explicit Exclusions

PoC **明确不做** (each with rationale):

1. **不跑 full 15-agent round table** —— PoC creative slice 只跑 9-agent subset (screenplay + 8 peers from ARCHITECTURE §2 screenplay `related_agents`). Rationale: 15-agent 全规模 round table 的 token cost + multi-round GLM 4-key rotation 风险超出 PoC budget (§2.4). 15-agent 全规模留给 v11.1+ production rollout.
2. **不迁 mem0 到 物理分区** —— PoC 用 Option B (mem0 单 backend + `agent_id` filter 路由, per ARCHITECTURE §3.2 + Phase 48 §3) baseline. 物理分区 deferred to v12+ per Phase 48 §3 决策 (PoC 单项目 18-agent 规模下 Option B 性能足够, 见 §4.2 latency SLO). §4.2 benchmark 若 p95 > 500ms 会 trigger 物理分区 early evaluation, 但 PoC 本身不实施物理分区.
3. **不动 production `~/.hermes/`** —— PoC 用 dedicated workspace `~/.hermes-poc/` (见 §2.3). 不污染 operator daily 的 production 环境.
4. **不跑 live client project** —— PoC 用 synthetic StoryKernel input (creative_source Step 1 output format, well-defined JSON). 不需要真实客户数据, 避免 NDA + privacy risk.
5. **不 ship 到 operator (Kai)** —— PoC ends at "acceptance criteria pass + PoC report committed to `.planning/milestones/v11.0-POC-REPORT.md`" report, **不是** "Kai 日常用 PoC agent 替代现有 SKILL". Production rollout 是 v11.1+ 决定, 不是 PoC 决定.

### §2.3 PoC Workspace 隔离

PoC 用 dedicated workspace:

- **目录**: `~/.hermes-poc/` (vs production `~/.hermes/`)
- **mem0 workspace**: `hermes-poc` (Option B `agent_id` filter 仍生效, 但 `user_id="hermes-poc"` 隔离 vs production `user_id="kai"`)
- **session DB**: `~/.hermes-poc/sessions.db` (独立 SQLite)
- **logs**: `~/.hermes-poc/logs/` (独立 `agent.log` / `errors.log` / `gateway.log`)
- **agent YAMLs**: `~/.hermes-poc/agents/` (infra slice `test-coordinator.agent.yaml` + creative slice 9-agent subset)

**Phase 49 §5.5 legacy v7.0 mem0 `agent_id=hermes` sunset policy** 不影响 PoC —— PoC 用 fresh namespace (`agent_id=screenplay` / `agent_id=cinematographer` / etc., 没有 `agent_id=hermes` 旧 memory 需要 sunset). 30-day sunset window (per Phase 49 §5.5-§5.6) 是 production concern, 不是 PoC concern.

**Backup / restore**: PoC workspace 是 disposable —— 任何破坏性测试 (e.g. §4.7 live migration 测试) 都可以用 `rm -rf ~/.hermes-poc/` + 重新 setup 恢复. PoC 报告 (`.planning/milestones/v11.0-POC-REPORT.md`) 是唯一需要 persist 的产物, 提交到 git.

### §2.5 SC#1 Cross-Validation

SC#1 acceptance: "File `05-POC-PLAN.md` exists + PoC scope clearly bounded."

| Requirement | Where addressed | Verdict |
|-------------|-----------------|---------|
| File exists | this file | ✅ |
| PoC done 定义 | §2.1 (4 conditions: slices / acceptance / risk verdicts / token cost) | ✅ |
| Explicit exclusions | §2.2 (5 exclusions: full 15-agent / 物理分区 / production / live client / ship to operator) | ✅ |
| Workspace isolation | §2.3 (`~/.hermes-poc/` dedicated) | ✅ |
| Budget + duration | §2.4 (~15-17 person-days + ~6 calendar weeks) | ✅ |
| Boundary rationale explicit | §2.0 (避免 scope creep, v11.0 PoC 是验证可行性, 不是 ship production) | ✅ |
| Disposable workspace | §2.3 backup/restore (`rm -rf ~/.hermes-poc/` recoverable) | ✅ |
| Token budget capped | §2.4 (~500K-800K total PoC tokens within GLM 4-key 800K TPM ceiling for serial execution) | ✅ |
| 30-day shadow-run window | §2.4 + §6.3 Week 6 (per Phase 49 §4.7 Step 5 memory migration dual-read) | ✅ |

SC#1 PASS.

---

### §2.4 PoC Duration + Budget

**Acceptance criteria**: 12 person-days (per §4 task decomposition 总和)

**Vertical slice setup**: 5 person-days
- Infra slice setup ~3 days (7 MCP tool wire-up per STACK §3.2 + 1 sample agent YAML transform per Phase 49 §2 + 1 round_table cycle)
- Creative slice setup ~2 days (on top of infra: 9-agent subset persona transform per Phase 49 §2.4 screenplay rules + Step 3 round table wiring)

**Risk register mitigation 实施**: 1-2 person-days
- P1 `persona_sha256` drift probe (1d in §4.1, 已计入 acceptance criteria)
- P2 TTL + `verified_at` (在 §4.4 compaction pass 内, 不另算)
- P4 `scope` + `project_id` required (在 §4.7 schema migration dry-run 内, 不另算)
- P5 `evidence_chain` + bias canary + dry-run-first (在 §4.3 + §4.6 内, 已计入)
- P6 `operator_signature` schema field (0.5d, 在 §4.6 dry-run-first 内)
- P7 coordinator arbitration (Phase 46 round-table-state-schema 已 ship, PoC 仅验证 0.5d)
- P8 fitness battery scaffold (在 §4.1 内, 已计入)

**Total PoC effort: ~15-17 person-days** (12 acceptance + 5 vertical slice setup - 5 重叠在 acceptance 内 + 1-2 standalone mitigation)

**Calendar timeline**: + 30-day shadow-run window (per Phase 49 §4.7 Step 5) for memory migration dual-read = total **~6 calendar weeks** (per §6.3 detailed timeline).

**Token budget** (per STACK §7.3 + §6.2):
- Full pipeline baseline run: ~550K tokens (PoC 不跑 full pipeline, 只跑 vertical slice)
- Per-vertical-slice: ~148K (creative screenplay Step 3) + ~10K (infra 1 round table) = ~160K tokens for PoC vertical slice execution
- Acceptance criteria 实施 + retry + debug: ~3-5x = ~500K-800K tokens total PoC budget
- Within GLM 4-key × 200K TPM ≈ 800K TPM ceiling for serial execution (per §6.4)

---

## §3 Vertical Slice Selection (SC#2 Deep-Dive)

> 本节是 ROADMAP SC#2 的完整论证. 2 vertical slices (creative + infra) each with **论据完整 non-arbitrary** —— 5-dimension selection criteria scorecard per slice + 决策号 + research citation + edge-case rationale. **NOT arbitrary picks.**

### §3.0 Slice Selection Strategy

PoC 选 2 vertical slices 而非 full pipeline run 的 rationale:

- **Token / time budget**: Full pipeline ~550K tokens / run × N iteration 超出 PoC 6-week budget (§2.4). Vertical slice 单 slice ~10-150K tokens, 可多次迭代.
- **Failure isolation**: Vertical slice 失败影响范围小, 易 debug. Full pipeline 失败可能由 13-step 中任一引起.
- **Schema-field coverage**: 精心选的 2 slices 可覆盖 agents-schema.yaml 18 fields + memory-record-schema.yaml 10+ fields 的 ≥80%, 不需跑 full pipeline.
- **Decision coverage**: 2 slices 精心选可覆盖 Phase 44 决策 1/3/5/6/7 (5 of 7), 不需 full pipeline.

**Slice composition**: 1 **creative phase** slice (validates per-agent memory + round table in a real-creative-flow context) + 1 **infra phase** slice (validates agent registry + MCP tool wire-up + round table lifecycle dispatch in isolation). The two slices have complementary coverage:

- Creative slice answers: "Does the per-agent memory + curator + round table actually produce better screenplay outputs?"
- Infra slice answers: "Does the 7 MCP tool surface actually dispatch correctly? Does the agent registry loader work? Does the round table state lifecycle persist?"

Both must pass for PoC to validate v10.0 设计 可行性. Creative slice alone 不验证 infra path (may paper over dispatch bugs with shortcuts); Infra slice alone 不验证 creative value (may dispatch correctly but produce garbage outputs).

### §3.1 Selection Criteria (5 Dimensions)

每 slice 按 5-dimension scorecard 评估, 每 dimension 0-10 分:

| Dimension | Why it matters for PoC | Score guide |
|-----------|------------------------|-------------|
| **(1) Round-table density** | Slice 应 exercise Phase 46 turn lifecycle + conflict arbitration (P7 mitigation). 低 density = 不 exercise round table = 不验证 v10.0 core feature | 0 = no round table; 10 = multi-turn multi-agent dense conflict |
| **(2) Schema-field coverage** | Slice 应 exercise ≥80% of agents-schema.yaml 18 fields + memory-record-schema.yaml key fields (`persona_sha256` / `fitness_battery` / `evidence_chain` / `scope` / `project_id` / `memory.max_records` / `expires_at`) | 0 = touches < 30%; 10 = touches ≥ 90% |
| **(3) Decision coverage** | Slice 应 exercise 决策 1 (T6) / 3 (D2) / 5 (α form) / 6 (per-agent memory) / 7 (Hermes控 structure) —— 5 of 7 decisions | 0 = touches 0; 10 = touches 5+ |
| **(4) Synthetic-input feasibility** | Slice 可在 synthetic StoryKernel input (no real client data) 下跑通. PoC 不能依赖 NDA 客户数据 | 0 = requires real client data; 10 = synthetic JSON input well-defined |
| **(5) Isolation safety** | Slice 在 `~/.hermes-poc/` workspace 跑不污染 production. 无网络副作用, 无外部 API dependency | 0 = touches production; 10 = fully isolated |

### §3.2 Creative Vertical Slice = Screenplay Step 3 Round Table

**Slice**: screenplay Step 3 (V8.6 13-step pipeline 中的 scene-level script generation phase) round table, 9-agent subset on synthetic StoryKernel input.

#### Selection rationale (5-dim scorecard)

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| (1) Round-table density | **9/10** | ARCHITECTURE §2 screenplay row: **9 related_agents** (densest among 15 experts). Multi-turn conflict on screenplay decisions (e.g. scene structure vs emotion curve) 自然 surfaces P7 memory conflict |
| (2) Schema-field coverage | **90%+** | Touches `persona_sha256` (P1 fitness battery drift probe), `lineage.transform_notes` + HOOK-09 emotion_curve marker contract load-bearing, `memory_scope` (per-agent), `tools` whitelist (write_file + patch for screenplay write-path) |
| (3) Decision coverage | **5/7** | 决策 1 (T6 MCP tool) + 决策 3 (D2 storyboard-first-class — screenplay is D2-compatible) + 决策 5 (α form agent registry entry) + 决策 6 (per-agent memory + curator) + 决策 7 (Hermes控 turn_order) |
| (4) Synthetic-input feasibility | **high** | StoryKernel JSON (creative_source Step 1 output format) is well-defined synthetic input, no real client data needed |
| (5) Isolation safety | **high** | `~/.hermes-poc/agents/screenplay.agent.yaml` + 8 peer YAMLs, 独立 mem0 workspace |

#### Citations

- **决策 3 D2 storyboard-first-class** (Phase 44 §2.3): screenplay is D2-compatible creative phase. D2 决策 把 storyboard (Step 6.5) 升为 first-class, 使 screenplay (Step 3) 的 HOOK-09 emotion_curve marker 成为 downstream storyboard assembly 的 contract-load-bearing 输出. 这意味着 screenplay persona 在 transform 时 MUST surface HOOK-09, 否则下游 storyboard 无法 consume.
- **ARCHITECTURE §2 screenplay row**: HOOK-09 emotion_curve marker contract load-bearing + 5 refs (save-the-cat / mckee / cn-shortdrama / emotion-curve / dialogue-craft) + **9 related_agents** (densest in 15-expert pool — cinematographer + hook_retention + theory_critic + editor + scene_builder + performer + continuity + composer) + tools `[hermes_llm, read_file, search_files, write_file, patch]` (includes write_file + patch for screenplay write-path, exercises agent write-back).
- **Phase 49 §2.4 screenplay transform rules**: agent YAML build procedure. `lineage.transform_notes` MUST surface HOOK-09 emotion_curve marker contract (具体: `lineage.transform_notes: ["HOOK-09 emotion_curve marker arrays remain contract-load-bearing"]`, 见 ARCHITECTURE §1.3 minimal example line 97).
- **Phase 46 round-table-state-schema**: turn lifecycle (`round_table_open` → turn N → `submit_round_table_result`) + §3 conflict arbitration (scope precedence session>project>global + confidence-weighted voting + conflict log). Screenplay Step 3 with 9 related_agents 自然 surfaces P7 memory conflict (9 agents with different memory will disagree on screenplay decisions like pacing vs emotion_curve priority).
- **PITFALLS §P7** (round-table memory conflict): coordinator arbitration + scope precedence + confidence voting. Screenplay 9-agent round table is the densest P7 exercise scenario in the 15-expert pool.
- **PITFALLS §P1** (persona drift): screenplay's frozen `persona_sha256` baseline at registration is the foundation for §4.1 fitness battery drift probe (P1 mitigation 2).

#### Slice scope

- **Agent subset**: 9 agents (screenplay + 8 peers from ARCHITECTURE §2 screenplay `related_agents` column). Screenplay's 9 `related_agents` per ARCHITECTURE §2 row include the natural Step 3 collaborators: cinematographer (visual translation), hook_retention (HOOK-09 marker consumer), theory_critic (scene-structure audit), editor (pacing), scene_builder (asset continuity), performer (dialogue playability), continuity (跨场景 consistency), composer (emotional arc audio mirror). This 9-agent subset is the densest collaboration graph among 15 experts.
- **Round table**: 1 Step 3 round table on synthetic StoryKernel input, ~5 turns (per STACK §7.1 Step 3 estimate: 5 experts × 3 turns × 2 call/expert/turn = ~30 MCP call; screenplay subset 9 agent 是 densest round table — 操作上 9 agents × 2-3 turns × 2 call/expert/turn ≈ 40-50 MCP call, 仍是 stack §7.1 estimate 量级)
- **Token estimate**: ~30-50 MCP call × 100 token overhead + ~22 LLM opinion call × 6500 token = ~4.5K + ~143K = **~148K tokens** (higher than STACK §7.3 average 42K because screenplay has 9 related_agents vs 4 average; PoC 不要求精确, 量级一致即可)

#### Edge case: HOOK-09 emotion_curve marker contract

**HOOK-09** is the **load-bearing contract** that screenplay's persona MUST surface in `lineage.transform_notes` per Phase 49 §2.4. If the PoC transform drops HOOK-09, the screenplay agent produces wrong-format output (emotion_curve marker arrays missing → downstream Step 6.5 storyboard assembly + Step 7 visual_executor cannot consume screenplay output).

**This is the PoC's first "did the transform work?" smoke test**: if the transformed `screenplay.agent.yaml` `lineage.transform_notes` does NOT mention HOOK-09, the transform pipeline is broken and all downstream vertical slice work is invalid. Operator (or PoC implementer) MUST verify HOOK-09 contract preservation before running Step 3 round table.

### §3.3 Infra Vertical Slice = Agent Registry + 1 Round Table Invocation

**Slice**: 7 MCP tools wired in `mcp_serve.py` per STACK §3.2 + 1 sample agent YAML `~/.hermes-poc/agents/test-coordinator.agent.yaml` (minimal α form) + 1 successful `round_table_open` → turn 1 → `submit_round_table_result` cycle on synthetic input.

#### Selection rationale (5-dim scorecard)

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| (1) Round-table density | **N/A** (sets UP the round table, doesn't exercise creative conflict) | Infra slice 的目的是验证 7 MCP tool wire-up + agent registry loading + round_table lifecycle dispatch, 不是 creative 冲突 |
| (2) Schema-field coverage | **100%** | 1 sample agent YAML touches all 18 fields of agents-schema.yaml (vs creative slice 只 touch screenplay-relevant subset) |
| (3) Decision coverage | **4/7** | 决策 1 (T6 协议 — 7 MCP tool surface) + 决策 5 (α form agent registry entry) + 决策 6 (per-agent memory `get_agent_memory` + `query_memory`) + 决策 7 (Hermes控 `round_table_open` `max_rounds` `early_stop_rule` schema) |
| (4) Synthetic-input feasibility | **high** | `test-coordinator.agent.yaml` is minimal α form (no real persona needed); synthetic input is trivial JSON |
| (5) Isolation safety | **high** | `~/.hermes-poc/` fully isolated |

#### Citations

- **决策 1 T6 协议** (Phase 44 §2.1): Hermes MCP server extension
- **STACK §3.2 7 MCP tool surface** (cite each tool's purpose):
  - `get_agent_persona` (Tool 1) — return agent YAML persona block
  - `get_agent_opinion` (Tool 2) — main LLM-call tool, CC provides question + prior_discussion
  - `get_agent_memory` (Tool 3) — scoped retrieval (mem0 backend)
  - `submit_round_table_result` (Tool 4) — turn lifecycle terminator, persists to `~/.hermes-poc/agents/.runtime/{slug}/round_tables/{id}.json`
  - `submit_artifact` (Tool 5) — agent write-path
  - `query_memory` (Tool 6) — semantic search variant of Tool 3
  - `run_python_phase` (Tool 7) — boundary tool for retained-phases per Phase 49 §5.2 allowlist
- **STACK §5.2 mcp_serve.py patch pseudocode**: implementation reference for v11.0 PoC implementer
- **Phase 46 round-table-state-schema full lifecycle**: `round_table_open` → turn N → `submit_round_table_result` → state file persistence
- **Phase 45 agents-schema.yaml 18-field**: `test-coordinator.agent.yaml` follows this schema
- **Phase 49 §2 transform procedure**: SKILL.md → agent YAML transform rules

#### Slice scope

- **MCP tools**: 7 tools wired in `mcp_serve.py` (extending existing 9 messaging tools per STACK §5.2 pseudocode pattern)
- **Agent YAML**: 1 sample `~/.hermes-poc/agents/test-coordinator.agent.yaml` (minimal α form, all 18 fields filled with test-coordinator-specific values)
- **Round table**: 1 successful `round_table_open` → turn 1 → `submit_round_table_result` cycle (synthetic input "test coordinator opinion on test topic")

#### Edge case: run_python_phase Step 6.5 storyboard assembly

Infra slice's `run_python_phase` MCP tool (Tool 7) may be invoked as part of creative slice's storyboard Step 6.5 prerequisite (per Phase 49 §5.2 retained-phases allowlist: Steps 0/6.5/7/10/11/12/15). This validates:

- **Phase 49 §5.2 allowlist enforcement**: dispatcher rejects non-allowlist step invocation with explicit error (per Phase 49 §5.4 dispatcher-layer validation, no silent fallback)
- **Phase 49 §5.4 dispatcher-layer validation**: `run_python_phase` accepts only allowlisted step IDs
- **决策 2 B3a Python runner 增量迁移** boundary: only Python-implemented steps (Steps 0/6.5/7/10/11/12/15) are eligible for `run_python_phase` dispatch; CC-side creative steps (Step 3 screenplay etc.) MUST go through `round_table_open` lifecycle, not `run_python_phase`

PoC implementer may exercise this edge case by attempting to invoke a non-allowlist step (e.g. Step 3 screenplay) via `run_python_phase` and verifying the dispatcher rejects it. This is the PoC's "did the dispatcher enforce the boundary?" smoke test.

Negative-test scenario: pass `step_id="3"` (non-allowlist) to `run_python_phase`. Expected: dispatcher rejects with `ValueError("Step 3 is not in retained_python_phases allowlist; use round_table_open instead")`. If dispatcher silently accepts or falls back, the Phase 49 §5.4 invariant is broken and T-50-04 (EoP threat) is realized.

### §3.4 Why NOT Other Slices (Rejected Alternatives)

每 rejected alternative 引用 决策号 or research section, 不是 arbitrary 排除.

| Rejected alternative | Reason | Citation |
|----------------------|--------|----------|
| (a) Creative slice = **creative_source Step 1** | Too upstream, no round-table density — only 4 `related_agents` (vs screenplay's 9). Step 1 is single-LLM ideation (Snowflake Method + SCAMPER), not round-table-driven. 不 exercise Phase 46 conflict arbitration (P7 mitigation) | ARCHITECTURE §2 creative_source row: 4 related_agents |
| (b) Creative slice = **visual_executor Step 5** | Heavy ComfyUI dependency (30s-10min per call, per STACK §7.4 latency table). PoC infra slice excludes long-running exec. ComfyUI availability is operator-dependent, breaks isolation safety (§3.1 dimension 5). Also visual_executor tools 包含 ComfyUI API call, 不在 7 MCP tool surface 内 (决策 1 T6 boundary) | STACK §7.4 + ARCHITECTURE §2 visual_executor row + 决策 1 T6 协议 |
| (c) **Full pipeline run** | Out of PoC scope per §2.4 budget. ~550K tokens / run × N iteration 超出 PoC 6-week / ~800K token budget. Full pipeline 还要求 13 step 全部 wired (包括 ComfyUI-dependent steps), 远超 vertical slice setup ~5 person-days | §2.4 + STACK §7.3 |
| (d) Creative slice = **compliance_gate / script_auditor** | Hard-gate authority requires operator policy review (compliance_gate hard-gates on `< 65% predicted_completion`; script_auditor 5-dim critic). PoC iteration would be blocked on operator policy decision, not technical feasibility. Hard-gate logic 是 operator policy concern (决策 7 Hermes控 structure 边界), 不是 v10.0 设计本身 | ARCHITECTURE §2 script_auditor + compliance_gate rows + 决策 7 |

**Pattern**: 所有 rejected alternatives 都在 5-dimension scorecard (§3.1) 上至少 1 dimension 得分 ≤ 5, 而 screenplay Step 3 + agent registry 2 slices 在所有 relevant dimensions 上得分 ≥ 8 (除 infra slice 的 round-table density N/A).

### §3.5 Slice Interaction + Sequence

Creative slice **depends on** infra slice: screenplay Step 3 round table needs agent registry + 7 MCP tools wired + `round_table_open` lifecycle dispatch path.

**Sequence**:
1. **Infra slice first** (~3 days setup, per §3.3 + §6.3 Week 1)
   - Wire 7 MCP tools in `mcp_serve.py`
   - Transform `test-coordinator.agent.yaml` per Phase 49 §2
   - Run 1 successful `round_table_open` → `submit_round_table_result` cycle (synthetic input)
   - Validates: T6 协议 (决策 1) wire-up + agents-schema.yaml 18-field loader (决策 5) + round_table lifecycle (Phase 46) + Hermes控 structure (决策 7: Hermes owns `round_table_open` schema, max_rounds, early_stop_rule)
2. **Creative slice on top** (~2 days, per §3.2 + §6.3 Week 2)
   - Transform 9-agent subset YAMLs (screenplay + 8 peers per ARCHITECTURE §2 screenplay `related_agents`)
   - Run 1 Step 3 round table on synthetic StoryKernel input
   - Commit `fitness_trend.jsonl` baseline entry for screenplay (first data point for §4.1 fitness battery)
   - Validates: per-agent memory (决策 6) — 9 agents 各自 retrieve project-scoped memory + screenplay persona_sha256 baseline (P1 mitigation 1) + Phase 46 conflict arbitration (P7 mitigation) on multi-agent screenplay decisions

**Dependency rationale**: Infra slice establishes the dispatch path + agent registry + memory layer baseline. Creative slice 复用 infra slice 的 7 MCP tool + agent YAML loader, 但增加 9-agent persona transform + Step 3 specific round table wiring. Creative slice 不能 standalone (需要 infra slice 的 MCP tool wire-up + agent registry loading).

**Total vertical slice setup: ~5 person-days** (within §2.4 budget). 这 5 days 是 vertical slice **setup** cost, 不包括 §4 acceptance criteria 实施 (acceptance criteria 在 vertical slice setup 之后跑, 见 §6.3 calendar).

### §3.6 Slice Deliverables

#### Infra slice produces 3 artifacts:

1. **7 MCP tools wired** in `mcp_serve.py` per STACK §5.2 pseudocode (extending existing 9 messaging tools: `conversations_list` / `messages_read` / `messages_send` / `events_poll` / `permissions_respond` / `channels_list` / etc.)
   - Tool 1 `get_agent_persona`: returns agent YAML persona block (per Phase 45 agents-schema.yaml field 4 + field 17 `persona_sha256`)
   - Tool 2 `get_agent_opinion`: main LLM-call tool, CC provides question + prior_discussion (per STACK §3.2)
   - Tool 3 `get_agent_memory`: scoped retrieval from mem0 backend with `agent_id` + `project_id` filter (per ARCHITECTURE §3.2 Option B)
   - Tool 4 `submit_round_table_result`: turn lifecycle terminator, persists state to `~/.hermes-poc/agents/.runtime/test-coordinator/round_tables/{id}.json` (per Phase 46 round-table-state-schema)
   - Tool 5 `submit_artifact`: agent write-path (per ARCHITECTURE §2 screenplay row tools include write_file/patch)
   - Tool 6 `query_memory`: semantic search variant of Tool 3 (per STACK §3.2 Tool 6)
   - Tool 7 `run_python_phase`: boundary tool for retained-phases per Phase 49 §5.2 allowlist (Steps 0/6.5/7/10/11/12/15), dispatcher enforcement per Phase 49 §5.4
2. **1 sample agent YAML** `~/.hermes-poc/agents/test-coordinator.agent.yaml` (minimal α form, all 18 fields filled with test-coordinator-specific values per Phase 45 agents-schema.yaml). Field highlights:
   - `name: test-coordinator` (field 1)
   - `persona_sha256: <computed at registration>` (field 17, P1 mitigation 1)
   - `memory.max_records: 500` (per SUMMARY OQ-7)
   - `memory_scope: per_agent` (per ARCHITECTURE §1.1)
   - `tools: [hermes_llm, read_file]` (minimal, test-coordinator 不需要 write_file)
   - `lineage.derived_from_skill_id: null` (test-coordinator is synthetic, 不 derived from SKILL.md)
   - `fitness_battery: null` (test-coordinator 不在 §4.1 acceptance criterion scope)
3. **1 successful `round_table_open` → `submit_round_table_result` cycle** (synthetic input "test coordinator opinion on test topic", state file persisted to `~/.hermes-poc/agents/.runtime/test-coordinator/round_tables/{id}.json` per Phase 46 round-table-state-schema)

#### Creative slice produces 3 artifacts:

1. **9-agent subset YAMLs** (screenplay + 8 peers from ARCHITECTURE §2 screenplay `related_agents`) in `~/.hermes-poc/agents/`:
   - `screenplay.agent.yaml` (HOOK-09 emotion_curve marker contract in lineage.transform_notes per Phase 49 §2.4)
   - `cinematographer.agent.yaml` (visual translation peer)
   - `hook_retention.agent.yaml` (HOOK-09 marker consumer)
   - `theory_critic.agent.yaml` (scene-structure audit peer)
   - `editor.agent.yaml` (pacing peer)
   - `scene_builder.agent.yaml` (asset continuity peer)
   - `performer.agent.yaml` (dialogue playability peer)
   - `continuity.agent.yaml` (跨场景 consistency peer)
   - `composer.agent.yaml` (emotional arc audio mirror peer)
2. **1 successful Step 3 screenplay round table** on synthetic StoryKernel input:
   - State file persisted to `~/.hermes-poc/agents/.runtime/screenplay/round_tables/{id}.json` (per Phase 46 round-table-state-schema full lifecycle)
   - Screenplay output artifact committed with **HOOK-09 emotion_curve marker contract preserved** (smoke test: lineage.transform_notes in screenplay.agent.yaml mentions HOOK-09, output artifact contains emotion_curve marker arrays)
   - Round table transcript shows at least 1 conflict arbitration event (per Phase 46 §3 — scope precedence session>project>global or confidence-weighted voting) — natural surfacing of P7 mitigation
3. **`fitness_trend.jsonl` baseline entry for screenplay** (first data point for §4.1 acceptance criterion — schema per PITFALLS §P8 mitigation 2):
   ```json
   {
     "ts": "2026-07-XX",
     "battery_version": "v1-screenplay-baseline",
     "mean_score": <baseline mean>,
     "per_prompt_scores": {<prompt_id>: <score>, ...},
     "persona_sha256": "<screenplay persona_sha256 at registration>",
     "model_id": "glm-5.2"
   }
   ```
   This baseline entry is the foundation for §4.1 regression auto-quarantine (mean_score drop > 0.5 across 3 runs triggers quarantine per PITFALLS §P8 mitigation 2).

### §3.7 Slice Selection Summary

| Slice | Round-table density | Schema coverage | Decision coverage | Synthetic-input | Isolation | Total |
|-------|---------------------|-----------------|-------------------|------------------|-----------|-------|
| Creative (§3.2 screenplay Step 3) | 9/10 | 90%+ | 5/7 (1/3/5/6/7) | high | high | **densest slice in 15-expert pool** |
| Infra (§3.3 agent registry + 1 round table) | N/A (sets up) | 100% | 4/7 (1/5/6/7) | high | high | **foundational — creative slice depends on it** |
| Rejected (a) creative_source Step 1 | 3/10 | 60% | 3/7 | high | high | low round-table density |
| Rejected (b) visual_executor Step 5 | 7/10 | 70% | 3/7 | **low** (ComfyUI dep) | **low** | ComfyUI breaks isolation |
| Rejected (c) full pipeline run | 10/10 | 100% | 7/7 | high | high | **out of budget** (~550K tokens/run × N) |
| Rejected (d) compliance_gate | 5/10 | 75% | 4/7 | medium | high | blocked on operator policy |

**结论**: Creative slice (screenplay Step 3) + Infra slice (agent registry + 1 round table) 是 SC#2 vertical slice 的最优组合 —— coverage 高, isolation safe, budget within range. 每 slice 都有 决策号 + research citation + edge-case rationale, 非 arbitrary pick.

### §3.8 SC#2 Cross-Validation

SC#2 acceptance: "PoC 目标明确 (vertical slice: 1 creative phase + 1 infra phase, 论据完整) —— creative = screenplay Step 3 round table; infra = agent registry + 1 round table invocation. Both selections cite 决策号 + research section + edge-case rationale, NOT arbitrary picks."

| Requirement | Where addressed | Verdict |
|-------------|-----------------|---------|
| 1 creative phase | §3.2 screenplay Step 3 | ✅ |
| 1 infra phase | §3.3 agent registry + 1 round table | ✅ |
| creative cites 决策号 | §3.2 citations (决策 3 D2 + 决策 5 α form + 决策 6 per-agent memory + 决策 7 Hermes控) | ✅ |
| creative cites research section | §3.2 citations (ARCHITECTURE §2 + Phase 49 §2.4 + Phase 46 round-table-state-schema + PITFALLS §P1/§P7) | ✅ |
| creative cites edge-case rationale | §3.2 edge case (HOOK-09 emotion_curve marker contract — first "did the transform work?" smoke test) | ✅ |
| infra cites 决策号 | §3.3 citations (决策 1 T6 + 决策 5 α form + 决策 6 per-agent memory + 决策 7 Hermes控) | ✅ |
| infra cites research section | §3.3 citations (STACK §3.2 7 MCP tool + §5.2 pseudocode + Phase 46 round-table-state-schema + Phase 45 agents-schema.yaml) | ✅ |
| infra cites edge-case rationale | §3.3 edge case (run_python_phase Step 6.5 dispatcher enforcement — Phase 49 §5.4 invariant) | ✅ |
| Both non-arbitrary | §3.1 5-dimension scorecard + §3.4 rejected alternatives + §3.7 summary | ✅ |

SC#2 PASS.

**Note**: SC#2 的 "论据完整非任意挑" 要求每 slice 都通过 5-dimension scorecard + 决策号 citation + edge-case rationale 三道验证. §3.2 screenplay Step 3 + §3.3 agent registry + 1 round table 都满足.

---

