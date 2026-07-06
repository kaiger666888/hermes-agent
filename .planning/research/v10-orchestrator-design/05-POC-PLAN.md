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

## §4 7-Item Acceptance Criteria Checklist (SC#3 Deep-Dive, 12 Person-days total)

> 本节是 ROADMAP SC#3 的完整论证. 7 项 acceptance criteria + 每项 1-3 天工作量估算 = **12 person-days total**. 每 item cite PITFALLS §PX mitigation + Phase 45 schema field + Phase 49 §4-§5 / Phase 46 protocol reference. 工作量估算基于 **first-principles task decomposition** (设计 + 实施 + 验证 三 phase per item), 不是 gut feel.

### §4.0 Acceptance Criteria Strategy

7 项 acceptance criteria 覆盖 v11.0 PoC must-pass 的 7 个维度. 每 criterion 都对应一个 PITFALLS §PX mitigation (P1/P3/P5/P8/P9/P13/P14) 的 PoC 实施验证. 这 7 个维度是:

1. **Fitness battery** (P1+P8 mitigation) —— regression-detection 信号
2. **Latency SLO** (P3 mitigation) —— mem0 scoped retrieval 性能 baseline
3. **Bias canary** (P5 mitigation) —— curator `_memory_evolution_phase` hallucination guard
4. **Compaction pass** (P9 mitigation) —— memory size 增长控制
5. **Threshold tuning** (P13 mitigation) —— curator loop 反馈阈值
6. **Dry-run-first invariant** (P5 mitigation) —— non-bypassable human-in-loop
7. **Schema migration dry-run** (P14 mitigation) —— memory schema 前向兼容

每 criterion 的工作量估算分解为 **设计 + 实施 + 验证** 三 phase, sub-task 级 day-fraction (e.g. `0.5d` / `1d`).

**为什么是这 7 项** (not arbitrary):
- 这 7 项 来自 PITFALLS §Risk Register Summary (line 470-488) + SUMMARY §Gaps to Address (line 172-178) 的 PoC-必须-验证 subset. P1/P2/P4/P5/P6/P7/P8 (SC#4 7-pitfall scope) 的 mitigations 散布在这 7 项 acceptance criteria 中 (cross-mapping 见 §4.8 + §5).
- 这 7 项 **不包括** P10/P11/P12 (Phase 51 VALIDATE + v11.1+ scope, 不在 PoC must-pass), 也不重复 P3 (latency SLO §4.2 已 cover) 或 P9 (compaction §4.4 已 cover).
- 每 item 1-3 day estimate 基于 first-principles task decomposition (设计 + 实施 + 验证 三 phase), 不是 gut feel. 总 12 person-days 是 PoC budget (§2.4 ~15-17 person-days total) 的主体.

**Cross-criterion dependency** (precondition chain):
- §4.1 fitness battery 是 §4.3 bias canary + §4.6 dry-run-first + §4.7 schema migration 的 regression-detection backstop (later criteria changes need fitness battery to detect regression)
- §4.7 schema migration dry-run 是 §4.3 bias canary 的 precondition (bias canary 需要 clean memory layer, schema migration 验证 memory layer 数据完整性)
- §4.6 dry-run-first 是 §4.3 bias canary 的姊妹 criterion (both gate P5 curator failure modes)

详细 sequencing 见 §6.1 PoC implementation path.

### §4.1 Acceptance Criterion #1 — Fitness Battery Design (3 days)

**Citations**:
- PITFALLS §P8 mitigation 1: frozen fitness battery per agent at registration (changes require new `persona_sha256`)
- PITFALLS §P8 mitigation 2: longitudinal `fitness_trend.jsonl` (schema: `{ts, battery_version, mean_score, per_prompt_scores, persona_sha256, model_id}`)
- PITFALLS §P8 mitigation 3: A/B shadow mode before applying memory change
- PITFALLS §P8 mitigation 4: distinguishing agent-drift from model-drift (every fitness run records `model_id` + `provider`)
- PITFALLS §P8 mitigation 5: fitness battery review cadence (quarterly operator review)
- Label Studio "How to Evaluate Agent Memory" (4 competencies: accurate retrieval / test-time learning / long-range understanding / conflict resolution — directly applicable to fitness battery prompt design)
- Shaped.ai "A/B Testing Retrieval" (Recall@K, NDCG, and other quantitative metrics — proves agents getting better)
- GetMaxim "A/B Testing Strategies for AI Agents" (10K-trajectories-per-arm rule of thumb — sets expectation: Hermes scale = noisy signal, fitness signals will be noisy)
- Phase 45 agents-schema.yaml field: `fitness_battery` (path to battery YAML) + `persona_sha256` (drift probe baseline)
- MEMORY.md v6-self-evolution-milestone: v6.0 fitness battery precedent (`gate.py:decide_verdict` MT-Bench position-swap; PoC 设计 leverages v6.0 patterns + adds longitudinal trend + per-agent-cross-patch baseline)

**Task decomposition**:
- (a) **0.5d 设计 battery**: design 10-20 prompt battery for screenplay agent. Battery exercises HOOK-09 emotion_curve marker contract + Snyder 15-beat + McKee value-shift + Tan interest formula (per ARCHITECTURE §2 screenplay row refs). Each prompt designed to discriminate: a generic LLM should score 0.4-0.5; a well-persona'd screenplay agent should score 0.7+. Battery prompts frozen at agent registration under `_eval/persona_probes/screenplay.yaml` per PITFALLS §P1 mitigation 2.
- (b) **0.5d 实施 CLI**: implement `hermes agent fitness <agent_id>` CLI wrapper (calls existing v6.0 `_eval/gate.py:decide_verdict` pattern, but writes to `fitness_trend.jsonl` instead of overwriting `scores.json` baseline). CLI accepts `--battery <path>` (default: agent's `fitness_battery` field) + `--shadow` flag (run against proposed memory set per PITFALLS §P8 mitigation 3 A/B shadow mode)
- (c) **1d 实施 baseline + schema**: run baseline on screenplay agent + commit `fitness_trend.jsonl` schema (per PITFALLS §P8 mitigation 2 fields). Each entry:
  ```json
  {
    "ts": "2026-07-XX",
    "battery_version": "v1-screenplay-baseline",
    "mean_score": <baseline>,
    "per_prompt_scores": {"<prompt_id>": <score>, ...},
    "persona_sha256": "<agent persona_sha256 at registration>",
    "model_id": "glm-5.2",
    "provider": "zai"
  }
  ```
- (d) **1d 实施 regression auto-quarantine**: logic that mean_score drop > 0.5 across 3 consecutive runs triggers auto-quarantine of recent memory writes (mirrors PITFALLS §P8 mitigation 2 last sentence). Auto-quarantine sets `status="quarantined"` on memory records written in the window between first and third run; operator can `hermes agent memory restore` to undo if false-positive.

**Acceptance check**: `fitness_trend.jsonl` exists with ≥1 baseline entry for screenplay. Regression logic verified on synthetic test (manually inject bad memory write → next fitness run mean_score drops > 0.5 → auto-quarantine triggers within 3 runs).

**Failure mode**: if fitness battery design fails (e.g. battery prompts don't discriminate persona drift — generic LLM scores same as persona-aligned agent), P1 (persona drift) + P8 (no fitness signal) mitigations are unverified. PoC blocks until battery redesigned with more discriminating prompts.

**Pitfall gated**: P1 (persona drift, partial — drift probe via mean_score trend) + P8 (no fitness signal, full — this is THE acceptance criterion for P8).

### §4.2 Acceptance Criterion #2 — Latency SLO p95 < 500ms (2 days)

**Citations**:
- PITFALLS §P3 mitigation 4: read-path latency SLO + observability (`_latency_ms` field in retrieval log + stats CLI p50/p95/p99 per agent)
- PITFALLS §P3 mitigation 1 (physical partitioning) + 2 (local SQLite index): related context for what to do if SLO fails
- Phase 48 §3 Option B vs 物理分区 migration trigger: latency SLO fail → 物理分区 evaluation
- SUMMARY §Gaps to Address line 174: mem0 Platform API 真实 filter 行为 (v11.0 PoC week-1 跑 latency benchmark, 若 p95 > 500ms 立即触发物理分区切换)
- STACK §7.4 line 1035-1046: latency breakdown (stdio round-trip <5ms, MCP server dispatch <10ms, tool function body LLM call 2-15s — SLO excludes LLM-bound calls)
- Phase 45 memory-record-schema.yaml fields: `agent_id` + `project_id` (filter axis)

**Task decomposition**:
- (a) **0.5d 实施 log field**: add `_latency_ms` field to memory retrieval log entry (per PITFALLS §P3 mitigation 4). Log entry already exists in `Mem0MemoryProvider.search()` return path; add timing wrapper using `time.perf_counter()` around mem0 client call.
- (b) **0.5d 实施 stats CLI**: implement `hermes curator stats --latency <agent_id>` CLI with p50/p95/p99 per-agent breakdown. CLI reads recent N=100 retrieval log entries, computes percentiles via `statistics.quantiles()` (stdlib, no scipy dep — mirrors v6.0 `_eval/gate.py` pattern).
- (c) **1d 验证 benchmark**: run week-1 benchmark on test-coordinator.agent.yaml with 3 record counts:
  - **100 records** (small, baseline): 100 sequential `get_agent_memory` calls, measure p95. Expected: <100ms (mem0 small-scale latency).
  - **500 records** (medium, SLO threshold): 100 sequential calls, measure p95. SLO: <500ms.
  - **1000 records** (large, stress test): 100 sequential calls, measure p95. Expected: <1000ms (if >1000ms, P3 mitigation 1 物理分区 evaluation triggered even at PoC scale).

**Acceptance check**: p95 < 500ms on 500-record `get_agent_memory` benchmark (excluding LLM call). SLO scopes to mem0 scoped retrieval only (`get_agent_memory` + `query_memory`); does NOT include LLM-bound tool calls (per STACK §7.4 LLM call = 2-15s, not in 500ms budget). Verify the 3-record-count progression: 100→500→1000 records should scale sub-linearly (e.g. 50ms → 200ms → 600ms, NOT 50ms → 1000ms → 5000ms which would indicate HNSW post-filter collapse per PITFALLS §P3).

**Failure mode**: if p95 > 500ms on 500-record benchmark, trigger Phase 48 §3 物理分区 evaluation (per SUMMARY §Gaps line 174). PoC blocks until either:
- (a) mem0 backend tuned to meet SLO (e.g. cache common queries per PITFALLS §P3 mitigation 5), or
- (b) 物理分区 migration plan committed (可能 defer 物理分区实施到 v11.1+, but evaluation必须在 PoC 内做 — output: documented migration trigger analysis + recommended 物理分区 deployment topology)

If progression 100→500→1000 scales super-linearly (>3x p95 jump per 2x records), this is early sign of HNSW post-filter collapse (PITFALLS §P3 root cause) and 物理分区 evaluation becomes mandatory.

**Pitfall gated**: P3 (scoped retrieval perf collapse) — full.

### §4.3 Acceptance Criterion #3 — Bias Canary (2 days)

**Citations**:
- PITFALLS §P5 mitigation 4: bias canary in eval gate (5 prompts explicitly designed to surface single-operator preferences; if patch improves operator-A's prompts but regresses on operator-B-equivalent prompts, gate fails)
- PITFALLS §P5 mitigation 2: `evidence_chain` coverage check (embedding cosine ≥ 0.7, `_check_evidence_coverage(new_memory, evidence_chain) -> bool`)
- PITFALLS §P5 mitigation 3: operator diversity (`_check_operator_diversity(feedback_records, min_distinct_operators=2)`)
- SUMMARY §Gaps to Address line 176: curator `_memory_evolution_phase` LLM aggregation hallucination rate (v11.0 PoC acceptance criterion: `evidence_chain` coverage check + bias canary 必须跑通)
- Phase 45 memory-record-schema.yaml fields: `evidence_chain` + `evidence_operator_ids`

**Task decomposition**:
- (a) **0.5d 设计 bias-canary prompts**: design 5 bias-canary prompts (single-operator preference surfacing). E.g. "Should the screenplay always end with a twist?" (one operator's preference; should not become universal rule). Each prompt designed to surface preference that 1 operator would approve but 2+ operators would dispute.
- (b) **0.5d 实施 coverage check**: implement `_check_evidence_coverage(new_memory, evidence_chain) -> bool` (per PITFALLS §P5 mitigation 2). For each `feedback_record_id` in `evidence_chain`, retrieve the record text, compute embedding cosine similarity with `new_memory.text`. If any record's cosine < 0.7, the evidence doesn't actually support the new memory → reject (hallucination guard).
- (c) **0.5d 实施 diversity check**: implement `_check_operator_diversity(feedback_records, min_distinct_operators=2)` (per PITFALLS §P5 mitigation 3). Extract `operator_id` from each feedback record (Phase 45 memory-record-schema.yaml `evidence_operator_ids` field). If `len(set(operator_ids)) < min_distinct_operators`, single-operator bias risk → reject.
- (d) **0.5d 验证**: run curator `_memory_evolution_phase` in dry-run on synthetic 10-feedback-record input (all from one operator with similar preference), verify bias canary rejects single-operator-derived insight. Also run with 10 records from 2+ operators with consistent evidence → verify acceptance (false-positive rate test).

**Acceptance check**: curator dry-run rejects single-operator-derived insight with explicit error "evidence_operator_ids has < min_distinct_operators=2 distinct operators; bias canary triggered". AND curator dry-run accepts multi-operator insight with `evidence_chain` coverage cosine ≥ 0.7 (false-positive test).

**Failure mode**: if bias canary accepts single-operator insight (false negative), P5 (curator failure modes — bias amplification) mitigation is broken. Curator silently writes biased rules → agent degrades over time. If bias canary rejects valid multi-operator insight (false positive), curator stalls — PoC iteration blocked.

**Pitfall gated**: P5 (curator failure modes — bias amplification + hallucination), partial (bias canary covers bias amplification + hallucination; full P5 also needs §4.6 dry-run-first for the non-bypassable human-in-loop on `--apply-memory` mode).

### §4.4 Acceptance Criterion #4 — Compaction Pass (1 day)

**Citations**:
- PITFALLS §P9 mitigation 1 (per-agent memory budget cap) + mitigation 2 (3-tier core/working/archival compaction)
- SUMMARY OQ-7 (memory.max_records 上限 default 500, curator 每 N tick 跑 compaction pass)
- Phase 45 agents-schema.yaml field: `memory.max_records` (default 500)

**Task decomposition**:
- (a) **0.3d 实施 cap enforcement**: enforce `agent.memory.max_records: 500` cap in dispatcher (reject write above cap with explicit error "agent.memory.max_records=500 reached; run `hermes agent memory compact <agent_id>` or remove obsolete records first"). Cap is hard ceiling per PITFALLS §P9 mitigation 1.
- (b) **0.3d 实施 compaction trigger**: implement curator compaction pass trigger (every N ticks, N=10 default per SUMMARY OQ-7). Compaction merges low-confidence / old records into summary record per PITFALLS §P9 mitigation 2 + 3 (additive summarization with `source_record_ids` preserved; originals archived, not deleted).
- (c) **0.4d 验证**: run compaction on 600-record synthetic input (above cap), verify output follows 3-tier structure per PITFALLS §P9 mitigation 2:
  - **Tier 1 (core, ≤10 records)**: manually curated, always in prompt. Personas + hard rules. e.g. "screenplay agent always preserves HOOK-09 emotion_curve marker contract"
  - **Tier 2 (working, ≤100 records)**: retrieved on demand via mem0 search. Top-5 results injected. Recent operational context.
  - **Tier 3 (archival, ≤10000 records)**: full history, only via explicit `memory_recall` tool. Long-term archive.
  - **Compaction output**: 600 records → Tier 1: 5-10 records (manually selected); Tier 2: 100 records (high-confidence recent); Tier 3: 490 records (everything else, archived with `source_record_ids` chain preserved)

**Acceptance check**: compaction pass output on 600-record input produces valid 3-tier structure (core ≤10 / working ≤100 / archival ≤10000, with originals archived not deleted per PITFALLS §P9 mitigation 3 additive summarization). Total post-compaction record count = 600 (no data loss, just tier reorganization). Compaction log entry written per PITFALLS §P9 mitigation 5.

**Failure mode**: if compaction fails or produces wrong-tier output (e.g. archival >10000, or originals deleted), P9 (memory size growth) mitigation is broken. Memory grows unbounded → context overflow + summarization detail loss.

**Pitfall gated**: P9 (memory size growth) — full.

### §4.5 Acceptance Criterion #5 — Threshold Tuning (1 day)

**Citations**:
- PITFALLS §P13 mitigation 1 (adaptive thresholds: `feedback_threshold_count = max(3, active_projects * 2)`)
- PITFALLS §P13 mitigation 2 (queue-depth backpressure)
- PITFALLS §P13 mitigation 3 (auto-reject old pending patches)
- v6.0 baseline: `DEFAULT_FEEDBACK_THRESHOLD_COUNT = 3`

**Task decomposition**:
- (a) **0.3d 文档 defaults**: document initial defaults:
  - `DEFAULT_FEEDBACK_THRESHOLD_COUNT = 3` (v6.0 baseline per `agent/curator.py`)
  - Compaction trigger `N = 10` (per SUMMARY OQ-7: curator 每 10 ticks 跑 compaction pass)
  - Bias canary `min_distinct_operators = 2` (per §4.3)
  - Auto-quarantine mean_score drop threshold = 0.5 across 3 runs (per §4.1)
  - Each threshold documented with rationale + tuning path + audit log entry schema
- (b) **0.3d 文档 tuning path**: document CLI override for each threshold (e.g. `hermes curator set --feedback-threshold-count=N`) + audit log entry when threshold changed (fields: `operator_id`, `threshold_name`, `old_value`, `new_value`, `rationale_text`, `ts`). Overrides captured in `~/.hermes-poc/curator_thresholds.yaml` for persistence.
- (c) **0.4d 验证 runaway**: run curator with `threshold=1` (overly aggressive, simulating misconfiguration) on synthetic input with 10 active_projects, verify:
  - Audit log captures "threshold too low, runaway risk" warning per PITFALLS §P13 mitigation 1 (`feedback_threshold_count < max(3, active_projects * 2)` triggers warning)
  - Queue-depth backpressure kicks in per PITFALLS §P13 mitigation 2 (review queue > 50 pending patches → curator pauses proposal generation)
  - Auto-reject of pending patches older than 30 days per PITFALLS §P13 mitigation 3

**Acceptance check**: audit log captures runaway warning + rate-limit kicks in when threshold set to overly-aggressive value (threshold=1 with active_projects=10). Backpressure pause observable in curator stats (`hermes curator stats --queue-depth`).

**Failure mode**: if no runaway protection, P13 (curator loop runaway) mitigation is broken. Operator drowns in low-quality proposals + starts rubber-stamping approvals → feedback loop degrades.

**Pitfall gated**: P13 (curator loop runaway) — full.

**Adaptive threshold formula** (per PITFALLS §P13 mitigation 1):
```
feedback_threshold_count = max(3, active_projects * 2)
```
At PoC scale (active_projects=1, `~/.hermes-poc/` single-project workspace): threshold stays at default `3`. At production scale (active_projects=10): threshold scales to `max(3, 20) = 20`, preventing single-project feedback from dominating curator proposals.

**Auto-reject old patches** (per PITFALLS §P13 mitigation 3): pending patches older than 30 days auto-rejected (`status="expired"`). Forces operator to keep up or accept that old proposals lapse. Reduces rubber-stamping risk.

**Queue-depth backpressure detail** (per PITFALLS §P13 mitigation 2): curator pauses proposal generation when review queue > 50 pending patches. Stats CLI `hermes curator stats --queue-depth` surfaces backlog. Auto-resume when queue drains below 25 (hysteresis prevents flapping).

**Why threshold tuning is only 1 day**: v6.0 已 ship `DEFAULT_FEEDBACK_THRESHOLD_COUNT=3` + audit log; PoC 仅需 add adaptive scaling + backpressure + auto-reject, all config-level changes (no new schema fields, no new tool surfaces). Verification is single synthetic test.

**Cross-criterion note**: §4.5 threshold tuning 与 §4.4 compaction pass 共享 `N=10` compaction trigger 参数. 两者 都 curator config-level, 不互相 block, 可 parallel run in Week 5 (per §4.10).

### §4.6 Acceptance Criterion #6 — Dry-Run-First Invariant (1 day)

**Citations**:
- PITFALLS §P5 mitigation 5: dry-run-first invariant (curator memory-write path is dry-run by default, requires explicit `--apply-memory` flag for live writes)
- SUMMARY OQ-16: curator `_memory_evolution_phase` dry-run-by-default (mirrors v6.0 `CURATOR_DRY_RUN_BANNER` AST-walk pattern)
- v6.0 pattern: `TestNonBypassableHumanInLoop` ast-walk invariant on `apply_patch_transaction`

**Task decomposition**:
- (a) **0.3d 实施 default dry-run**: implement curator memory-write path dry-run default (requires explicit `--apply-memory` flag for live writes, mirrors v6.0 `CURATOR_DRY_RUN_BANNER` AST-walk pattern). Default mode prints "DRY-RUN: would write N memory records to agent X" but commits zero writes.
- (b) **0.3d 实施 non-bypassable test**: implement `_check_non_bypassable_human_in_loop` test (mirrors v6.0 `TestNonBypassableHumanInLoop` in `tests/test_curator_audit.py`). AST-walk verifies memory-write code path (`apply_memory_transaction` or equivalent) only callable from `hermes_cli/memory.py:apply_memory_cmd` (the single approved entry). Test fails build if AST-walk finds bypass path.
- (c) **0.4d 验证**: run curator in default mode, verify zero memory writes (dry-run banner shows what WOULD be written, `evidence_chain` + `evidence_operator_ids` per record); run with `--apply-memory`, verify writes proceed with audit log entry per write (`action="memory_write"`, `agent_id`, `memory_id`, `operator_id`, `ts`, per PITFALLS §P6 mitigation 5 extension to memory).

**Acceptance check**: default mode = zero memory writes (dry-run banner shows what WOULD be written). `--apply-memory` mode = writes proceed with audit log entry. AST-walk test passes (no bypass path).

**Failure mode**: if dry-run-first invariant is bypassable (e.g. memory write code path callable from non-approved entry, AST-walk test fails), P5 (curator failure modes) mitigation is broken. Curator silently writes hallucinated rules. Build fails until bypass fixed.

**Pitfall gated**: P5 (curator failure modes — full when combined with §4.3 bias canary) + P6 partial (`operator_signature` schema field validated in `--apply-memory` path, see §5.5 for full P6 verdict).

### §4.7 Acceptance Criterion #7 — Schema Migration Dry-Run (2 days)

**Citations**:
- Phase 49 §4.5 dry-run migration mode: `hermes agent memory migrate --dry-run`
- Phase 49 §4.7 6-step migration execution (backup → dry-run → approval → live → shadow 30d → decommission)
- PITFALLS §P14 mitigation 1 (schema_version on every record) + mitigation 2 (safe defaults) + mitigation 3 (dry-run migration script)
- Phase 45 memory-record-schema.yaml field: `schema_version: int`

**Task decomposition**:
- (a) **0.5d 实施 dry-run script**: implement dry-run migration script `hermes agent memory migrate --dry-run` (reads v6.0 `FeedbackStore` JSONL buckets at `~/.hermes/feedback/`, no write). Script walks buckets, applies Phase 49 §4.3 mapping table (v6.0 FeedbackRecord → v10.0 memory record), outputs 5-metric plan.
- (b) **0.5d 实施 output plan**: implement dry-run output plan with 5 metrics per Phase 49 §4.5:
  - **Total source count**: number of v6.0 FeedbackRecord read
  - **Per-field default fill rate**: for each new memory-record-schema.yaml field (e.g. `scope` / `project_id` / `evidence_chain` / `confidence` / `expires_at`), what % of source records have a non-default value vs require backfill
  - **Conflict count**: records that map to multiple targets (e.g. one FeedbackRecord generates 2 memory records due to evidence_chain split)
  - **Estimated target storage**: total tokens / bytes after migration
  - **Mapping warnings**: records that require manual review (e.g. `correction` text is empty + `verdict=bad` → ambiguous, needs operator)
- (c) **0.5d 验证 dry-run**: run dry-run on synthetic 100-record `FeedbackStore` input, verify output plan correctness (each metric reasonable + no silent drops). Manual spot-check 5 random records: does the mapped memory record make sense?
- (d) **0.5d 验证 live + shadow**: run live migration on same 100-record input with backup-first (Phase 49 §4.7 Step 1 `~/.hermes/feedback.backup.YYYYMMDD/`). Then run 30-day shadow-run window (Phase 49 §4.7 Step 5): dual-read from both v6.0 FeedbackStore + v10.0 memory layer, log retrieval discrepancies. Acceptance: <1% discrepancy (≤1 record out of 100 differs).

**Acceptance check**: dry-run output plan correct on synthetic input (5 metrics reasonable + 5 spot-checks pass) + live migration shadow-run <1% retrieval discrepancy (per Phase 49 §4.7 Step 5 dual-read).

**Failure mode**: if dry-run output plan is wrong (e.g. mapping table has bugs producing nonsense records) OR live migration causes >1% retrieval discrepancy, P14 (schema migration breaks memory store) mitigation is broken. Memory schema migration is blocked until dry-run + live + shadow pass. PoC scope reduction: defer schema migration to v11.1+ (但 v11.0 PoC 必须 evaluate 失败原因 + 推荐修复 path).

**Pitfall gated**: P14 (schema migration) — full.

**Safe defaults principle** (per PITFALLS §P14 mitigation 2): unknown fields in migration default to **safest value, not most permissive**. Examples:
- Unknown `confidentiality` → default `confidential` (not `public`)
- Unknown `scope` → default `project` (not `global`, prevents cross-project leak per P4)
- Unknown `status` → default `archived` (not `active`, keeps surface area minimal)
- Unknown `confidence` → default `0.3` (low, requires re-verification)

This principle prevents silent escalation of trust on migrated records.

**Dual-read invariant** (per Phase 49 §4.7 Step 5): during the 30-day shadow-run window, both v6.0 FeedbackStore + v10.0 memory layer are read in parallel. Discrepancies logged:
- v6.0 returns record X, v10.0 doesn't → v10.0 missing (mapping table gap)
- v10.0 returns record Y, v6.0 doesn't → v10.0 over-generated (curator drift)
- Both return but content differs → mapping table bug or evidence_chain split issue

Acceptance: <1% discrepancy (≤1 record out of 100 in synthetic test). If >1%, migration is not safe to ship; PoC scope reduction: defer migration to v11.1+ with documented failure analysis.

### §4.8 Acceptance Criteria Summary Table (7 rows, 12 person-days total)

| # | Criterion | Cite | Days | Acceptance check | Pitfall gated |
|---|-----------|------|------|------------------|---------------|
| 1 | Fitness battery design | PITFALLS §P8 mitigation 1 + Label Studio + Shaped.ai + GetMaxim | 3 | `fitness_trend.jsonl` baseline + regression logic triggers on mean_score drop > 0.5 | P1 (partial) + P8 |
| 2 | Latency SLO p95<500ms | PITFALLS §P3 mitigation 4 + Phase 48 Option B + SUMMARY §Gaps line 174 | 2 | p95 < 500ms on 500-record `get_agent_memory` benchmark (excluding LLM call) | P3 |
| 3 | Bias canary | PITFALLS §P5 mitigation 4 + SUMMARY §Gaps line 176 | 2 | curator dry-run rejects single-operator insight | P5 (partial) |
| 4 | Compaction pass | PITFALLS §P9 + SUMMARY OQ-7 | 1 | 3-tier output on 600-record synthetic input | P9 |
| 5 | Threshold tuning | PITFALLS §P13 + v6.0 baseline | 1 | audit log captures runaway warning + rate-limit on threshold=1 | P13 |
| 6 | Dry-run-first invariant | PITFALLS §P5 mitigation 5 + SUMMARY OQ-16 + v6.0 `TestNonBypassableHumanInLoop` | 1 | default mode zero writes; `--apply-memory` mode writes with audit log | P5 (full when + §4.3) |
| 7 | Schema migration dry-run | Phase 49 §4.5 + PITFALLS §P14 mitigation 3 | 2 | dry-run output plan correct + live migration shadow <1% discrepancy | P14 |
| **Total** | | | **12 person-days** | | |

**Per-criterion coverage**:
- **P1** (persona drift): §4.1 (fitness battery drift probe)
- **P3** (scoped retrieval perf): §4.2 (latency SLO)
- **P5** (curator failure modes): §4.3 (bias canary) + §4.6 (dry-run-first)
- **P8** (no fitness signal): §4.1 (fitness battery)
- **P9** (memory size growth): §4.4 (compaction)
- **P13** (curator runaway): §4.5 (threshold tuning)
- **P14** (schema migration): §4.7 (migration dry-run)

**SC#4 7-pitfall cross-mapping** (see §5 for full risk register):
- **P1** (persona drift, must-fix): gated by §4.1 (drift probe via mean_score trend)
- **P2** (stale memory, must-fix): gated by §4.4 (compaction validates TTL filter in retrieve path)
- **P4** (cross-project leakage, must-fix): gated by §4.7 (schema migration populates `scope=project` + `project_id`) + §4.2 (latency benchmark uses `agent_id+project_id` filter)
- **P5** (curator failure modes, must-fix): gated by §4.3 (bias canary) + §4.6 (dry-run-first)
- **P6** (memory poisoning, PARTIAL): `operator_signature` gated by §4.6 (validated in `--apply-memory` path); outlier detection deferred with monitoring per §5.10
- **P7** (round-table conflict, must-fix): gated by §3.2 creative slice (9-agent screenplay round table exercises Phase 46 conflict arbitration)
- **P8** (no fitness signal, must-fix): gated by §4.1 (fitness battery)

**PoC SC#3 cross-validation**: 7 项 + 每项 1-3 天 + total 12 person-days. All ✓.

**Why these 7 (not 14)**: P10 (privacy) + P11 (recall-vs-use) + P12 (cross-agent contamination) 是 Phase 51 VALIDATE + v11.1+ scope, 不在 PoC must-pass (single-project PoC 不触发 P10/P12). P3 (scoped retrieval perf) + P9 (memory size growth) + P13 (curator runaway) + P14 (schema migration) 是 secondary pitfalls 已在 §4.2/§4.4/§4.5/§4.7 cover.

**Mitigation cost alignment with PITFALLS §Risk Register Summary (line 470-488)**:

| Pitfall | PITFALLS mitigation cost | PoC implementation cost (this doc) | Aligned? |
|---------|--------------------------|------------------------------------|----------|
| P1 | M (persona hash + drift probe) | §4.1 3d (includes drift probe + regression auto-quarantine) | ✅ |
| P3 | H (per-agent workspace) | §4.2 2d (latency benchmark only; 物理分区 defer to v12+) | ✅ (defer-with-monitoring) |
| P5 | M (evidence coverage + operator diversity) | §4.3 2d + §4.6 1d = 3d | ✅ |
| P8 | M (fitness battery + trend) | §4.1 3d | ✅ |
| P9 | M (tier compaction) | §4.4 1d | ✅ |
| P13 | L (adaptive thresholds) | §4.5 1d | ✅ |
| P14 | M (schema_version + safe defaults) | §4.7 2d | ✅ |

Total PoC implementation cost = 12 person-days, aligned with PITFALLS mitigation cost estimates.

### §4.9 Per-Criterion Token Cost + Concurrency Implication

每 acceptance criterion 的 token cost + concurrency 影响 (cite STACK §7.3 + §7.5). STACK §7.3 estimates ~550K tokens per full pipeline run + ~340 MCP calls; per-vertical-slice estimate ~42K tokens = 550K/13. Acceptance criteria 是 vertical slice setup 之后跑的 verification, 不直接产生 pipeline tokens —— 它们的 token cost 是 fitness battery LLM calls + curator LLM aggregation + bias canary prompts 等.

| # | Criterion | Token estimate | Concurrency pattern |
|---|-----------|----------------|---------------------|
| 1 | Fitness battery | ~10K tokens per fitness run (10-20 prompt battery × 500-1000 tokens) | 串行 (1 LLM call per prompt, no parallel within battery to keep deterministic MT-Bench position-swap baseline) |
| 2 | Latency SLO | N/A (latency 测量, not LLM token cost) | N/A |
| 3 | Bias canary | ~5K tokens per bias canary run (5 prompts × 1000 tokens) | 串行 |
| 4 | Compaction pass | ~3K tokens curator LLM aggregation (10 records → 1 summary) | 串行 |
| 5 | Threshold tuning | N/A (threshold logic, not LLM call) | N/A |
| 6 | Dry-run-first | ~0 token dry-run (no LLM call); live mode ~3K tokens per write | 串行 |
| 7 | Schema migration | ~5K tokens (dry-run + live migration LLM aggregation) | 串行 |
| **Total per PoC iteration** | | **~26K tokens** (well within 800K TPM ceiling) | 全串行 per STACK §7.5 + MEMORY.md `feedback-glm-overload-reduce-concurrency.md` global concurrency==1 |

**Concurrency note**: 全部 acceptance criteria 是串行执行 (per STACK §7.5 v11.0 PoC 建议 no batch + 串行 first). 这与 MEMORY.md `feedback-glm-overload-reduce-concurrency.md` 的 global concurrency==1 policy 一致. PoC 不需要并发, 也不触发 GLM 4-key rotation ceiling. Multi-panelist round table (creative slice screenplay Step 3) 是 1 panelist 1 turn 顺序 await per Phase 46 §4 强制串行约束, 不是 7 panelist 并行 LLM call.

**contextvars prerequisite** (per SUMMARY §Gaps line 178): curator + memory layer 必须用 `contextvars` (not `threading.local`) for per-agent `agent_id` + `project_id` context propagation in ThreadPoolExecutor (`agent/tool_executor.py:110`). v6.0 Hermes 已用 contextvars for plugin tool whitelists (`hermes_cli/plugins.py:1654`). PoC implementation MUST verify contextvars (not threading.local) for `_scoped_agent_id` — otherwise cross-agent memory contamination (P12) surfaces in PoC. Verification: add unit test `_check_contextvars_not_threading_local()` that AST-walks `plugins/memory/mem0/__init__.py` + asserts no `threading.local()` call in scoped retrieval path.

**Token budget bottom-up**:
- STACK §7.3 estimates per-pipeline-run ~550K tokens / 13 steps ≈ 42K tokens / single round table average
- PoC vertical slice token cost (§6.2):
  - Creative slice screenplay Step 3 (9 related_agents, denser than average): ~148K tokens (~4.5K MCP overhead + ~143K LLM opinion calls)
  - Infra slice 1 round table invocation (3 agents × 1 turn × 2 call): ~10K tokens
- Acceptance criteria verification token cost (§4.9 table): ~26K tokens per PoC iteration
- Total PoC iteration (vertical slice + acceptance): ~148K + ~10K + ~26K = ~184K tokens
- PoC iteration count: ~3-5 iterations (debugging + retry) = ~550K-920K tokens total PoC budget
- Within GLM 4-key × 200K TPM ≈ 800K TPM ceiling for serial execution (per §6.4)

### §4.10 Acceptance Criteria Run Order (aligned with §6 implementation path)

Acceptance criteria 不按 §4.1-§4.7 顺序跑, 而是按 §6 implementation path 的 sequencing rationale:

| Week | Criteria run | Why this order |
|------|--------------|----------------|
| Week 1 | §4.2 latency SLO | P3 mitigation validation earliest — if fails, 物理分区 evaluation 触发, 影响 PoC 整体 timeline |
| Week 2 | §4.1 fitness battery | P1+P8 mitigation — regression-detection foundation must exist before §4.3/§4.6/§4.7 curator changes |
| Week 3 | §4.7 schema migration dry-run | P14 mitigation — validates memory layer before §4.3 bias canary (which depends on clean memory layer) |
| Week 4 | §4.3 bias canary + §4.6 dry-run-first | P5 mitigation — bias canary needs fitness battery (regression detection) + clean memory layer as preconditions |
| Week 5 | §4.4 compaction + §4.5 threshold tuning | P9 + P13 mitigation — secondary criteria, depend on §4.1-§4.7 baseline |
| Week 6 | all 7 re-run + report | PoC exit, 30-day shadow-run window closes |

**Precondition chain**: §4.1 (fitness battery) → §4.7 (schema migration) → §4.3 (bias canary) is the load-bearing sequence. Other criteria can shift weeks if needed.

**Why §4.2 latency SLO runs Week 1** (before §4.1 fitness battery Week 2):
- Latency SLO 是 infrastructure concern (mem0 backend performance). Infrastructure failure 影响 PoC 整体 timeline 最多 (如果 mem0 backend 不行, 整个 v11.0 设计需 rethink). Earliest validation = earliest course-correction.
- Latency benchmark 不依赖 fitness battery (it's a pure infrastructure measurement on `get_agent_memory`).

**Why §4.1 fitness battery runs Week 2** (after §4.2 latency SLO):
- Fitness battery 是 regression-detection foundation. Without it, later criteria changes (§4.3 bias canary / §4.6 dry-run-first / §4.7 schema migration) have no signal to detect regression from.
- Fitness battery 依赖 §3.2 creative slice setup完成 (need screenplay agent + battery prompts).

**Why §4.7 schema migration dry-run runs Week 3** (after §4.1 fitness battery):
- Schema migration validates memory layer 数据完整性. Bias canary (§4.3 Week 4) depends on clean memory layer — if memory records are corrupted by bad migration, bias canary results are noise.
- Fitness battery is regression-detection backstop during the migration (if migration breaks something, fitness battery detects it).

**Why §4.3 bias canary + §4.6 dry-run-first run Week 4** (after §4.7 schema migration):
- Both gate P5 curator failure modes. Bias canary needs fitness battery (regression detection) + clean memory layer (schema migration verified) as preconditions.
- §4.6 dry-run-first 是 §4.3 bias canary 的姊妹 criterion (both gate P5); running them together allows joint P5 acceptance check.

**Why §4.4 compaction + §4.5 threshold tuning run Week 5** (last before exit):
- These are secondary criteria (P9 memory size growth + P13 curator runaway). They depend on §4.1-§4.7 baseline established in Weeks 1-4.
- They are tuning-style criteria (operators can adjust thresholds + compaction cadence iteratively even after PoC exit).

---

## §5 7-Row Risk Register (SC#4 Deep-Dive, P1/P2/P4/P5/P6/P7/P8 × PoC Verdict)

> 本节是 ROADMAP SC#4 的完整论证. 7 load-bearing pitfalls × PoC deferral verdict. Verdicts 与 **PITFALLS §Risk Register Summary (line 470-488)** + **SUMMARY §Risk Register (line 145-160)** 对齐 (no divergent verdicts). 每 pitfall: one-line risk + full mitigation citation + PoC verdict + §4 acceptance criterion gating it + failure-if-deferred.

### §5.0 Risk Register Strategy

SC#4 scope 是 **P1/P2/P4/P5/P6/P7/P8** 这 7 个 load-bearing pitfalls (per ROADMAP §Phase 50). 其他 pitfalls (P3/P9/P10/P11/P12/P13/P14) 不在 SC#4 7-row scope, 但相关 context 在 §5.10 列出 (P3 latency SLO 在 §4.2 cover, P9 compaction 在 §4.4 cover, P14 schema migration 在 §4.7 cover, P10/P11/P12 在 Phase 51 VALIDATE + v11.1+ scope).

每 pitfall 在本 doc 的 verdict 必须与两个 canonical source 对齐:

| Source | Location | Used for |
|--------|----------|----------|
| PITFALLS §Risk Register Summary | line 470-488 | 7-pitfall verdict canonical (PoC-acceptable deferral? YES/PARTIAL/NO) + mitigation cost (H/M/L) |
| SUMMARY §Risk Register | line 145-160 | 7-pitfall 必须字段/机制 + 在哪文档解决 |

### §5.1 P1 — Persona Drift (must-fix-in-PoC)

**Risk one-liner**: Agent forgets its role after accumulating memory — screenplay agent stops behaving like screenplay expert, becomes generic creative writing helper. (PITFALLS §P1 opening)

**Mitigation citations**:
- PITFALLS §P1 mitigation 1: `persona_sha256` frozen at registration; curator-driven patches MUST NOT alter lines inside `## Role & Philosophy` / `## Core Capabilities` sections
- PITFALLS §P1 mitigation 2: periodic persona-drift probe (every 50 runs, 3 benchmark prompts + 4-dim MT-Bench position-swap against persona baseline)
- PITFALLS §P1 mitigation 3: tiered memory mirroring MemGPT core/archival split (`core_memory` manually curated, `archival_memory` auto-curated)
- PITFALLS §P1 mitigation 4: persona-versioned memory records (every record carries `persona_version` at write time; retrieve-time weights 1.0 if match, 0.3 if mismatch)
- Phase 45 agents-schema.yaml field: `persona_sha256` (frozen hash)
- Phase 45 memory-record-schema.yaml field: persona_version reference

**PoC verdict**: **must-fix-in-PoC** (aligned with PITFALLS §Risk Register Summary P1 row + SUMMARY §Risk Register P1 row — both mark NO for deferral).

**PoC-week acceptance**: §4.1 fitness battery gates this — regression auto-quarantine triggers on persona drift detected via mean_score drop > 0.5 across 3 consecutive runs.

**Failure-if-deferred**: agent silently becomes generic helper, HOOK-09 emotion_curve marker contract lost, all downstream screenplay outputs wrong format, Step 6.5 storyboard assembly + Step 7 visual_executor cannot consume screenplay output. Entire creative pipeline downstream of screenplay breaks.

**Mitigation cost**: M (per PITFALLS §Risk Register Summary line 474). PoC implementation cost: 3d (§4.1).

### §5.2 P2 — Stale Memory (must-fix-in-PoC)

**Risk one-liner**: Agent cites platform rules / API quirks that no longer apply — compliance_gate agent cites obsolete 抖音 rule from 2026-Q2 in 2026-Q4, outputs rejected by platform. (PITFALLS §P2 opening)

**Mitigation citations**:
- PITFALLS §P2 mitigation 1: `expires_at: datetime | None` field; domain-rule memories default 90d TTL
- PITFALLS §P2 mitigation 2: `verified_at: datetime` + `verification_source: str` stamps mirroring v1 ref convention
- PITFALLS §P2 mitigation 3: external-change detection hooks (URL fetch + hash compare + auto-quarantine on change)
- PITFALLS §P2 mitigation 4: `supersedes_memory_id` field (extends v6.0 `_mark_superseded` pattern)
- PITFALLS §P2 mitigation 5: time-decay applied to `confidence` (independent of weight decay): `confidence(now) = base * exp(-age / half_life_days)`
- Phase 45 memory-record-schema.yaml fields: `expires_at` + `verified_at` + `supersedes_memory_id` + `confidence` + `half_life_days`

**PoC verdict**: **must-fix-in-PoC** (aligned with PITFALLS §Risk Register Summary P2 row + SUMMARY §Risk Register P2 row).

**PoC-week acceptance**: §4.4 compaction pass exercises archival/quarantine of stale records (implicitly validates TTL filter in retrieve path: `WHERE expires_at IS NULL OR expires_at > now()`). The 600-record synthetic input includes 50 records with `expires_at < now` — verify compaction auto-archives them.

**Failure-if-deferred**: agent cites obsolete platform rules, operator loses trust in agent's expertise, platform rejection rate rises after policy change. Specifically for compliance_gate agent (即使 PoC 不 exercise compliance_gate, memory schema 字段必须 ship).

**Mitigation cost**: M (per PITFALLS §Risk Register Summary line 475). PoC implementation cost: in §4.4 (1d, includes TTL filter validation).

### §5.3 P4 — Cross-Project Leakage (must-fix-in-PoC)

**Risk one-liner**: Agent applies project-A learning inappropriately to project B — style_genome agent learns Project P1 (art-house) "muted palette" preference, then applies it to Project P2 (TikTok high-energy) wrong-context. (PITFALLS §P4 opening)

**Mitigation citations**:
- PITFALLS §P4 mitigation 1: three-tier scoping in agent schema (`scope: "global" | "project" | "session"`)
- PITFALLS §P4 mitigation 2: default scope = `project` (conservative)
- PITFALLS §P4 mitigation 3: per-project override layer (retrieve global + project-P2 only; project-P1 invisible unless `global`)
- PITFALLS §P4 mitigation 4: `project_id` required in retrieve call (not optional)
- PITFALLS §P4 mitigation 5: cross-project memory promotion gate (3+ distinct projects + curator confidence ≥ 0.8)
- Phase 45 memory-record-schema.yaml fields: `scope` + `project_id`

**PoC verdict**: **must-fix-in-PoC** (aligned with PITFALLS §Risk Register Summary P4 row + SUMMARY §Risk Register P4 row).

**PoC-week acceptance**: §4.7 schema migration dry-run populates `scope=project` + `project_id` default per Phase 49 §4.3 mapping table. §4.2 latency benchmark uses `agent_id+project_id` filter (validates filter path works at scale).

**Failure-if-deferred**: PoC single-project won't surface this (single project = no leak possible), but production rollout immediately leaks Project A learning into Project B (as SUMMARY §Gaps line 176 implicitly warns). P4 是 production rollout blocker, must-fix-in-PoC 防止 v11.1+ re-litigate.

**Mitigation cost**: M (per PITFALLS §Risk Register Summary line 477). PoC implementation cost: in §4.7 + §4.2 (no standalone, just field population + filter validation).

### §5.4 P5 — Curator Failure Modes (must-fix-in-PoC)

**Risk one-liner**: Curator's automated memory-update pass makes three classes of error: false-deletion (deletes valuable memory), hallucinated-write (confabulates rules from noisy feedback), bias-amplification (single-operator preference over-represented). (PITFALLS §P5 opening)

**Mitigation citations**:
- PITFALLS §P5 mitigation 1: never hard-delete (only `status="archived"`, mirroring v6.0 invariant)
- PITFALLS §P5 mitigation 2: `evidence_chain` ≥3 coverage check (embedding cosine ≥ 0.7 via `_check_evidence_coverage`)
- PITFALLS §P5 mitigation 3: operator diversity (`_check_operator_diversity(feedback_records, min_distinct_operators=2)`)
- PITFALLS §P5 mitigation 4: bias canary in eval gate (5 prompts surface single-operator preferences)
- PITFALLS §P5 mitigation 5: dry-run-first invariant (mirrors v6.0 `CURATOR_DRY_RUN_BANNER` AST-walk)
- PITFALLS §P5 mitigation 6: bias audit log entry (`evidence_operator_ids` + `evidence_record_count`)
- Phase 45 memory-record-schema.yaml fields: `evidence_chain` + `evidence_operator_ids` + `status="archived"`

**PoC verdict**: **must-fix-in-PoC** (aligned with PITFALLS §Risk Register Summary P5 row + SUMMARY §Risk Register P5 row).

**PoC-week acceptance**: §4.3 bias canary + §4.6 dry-run-first invariant both gate this. Joint acceptance: curator dry-run rejects single-operator-derived insight + dry-run-first AST-walk test passes.

**Failure-if-deferred**: curator silently writes hallucinated rules, agent behavior degrades over time with no signal (PITFALLS §P5 industry case: Letta/MemGPT documented curator LLM rewriting core memory with hallucinated facts; AutoGen shared-state discussion amplifies single-agent biases).

**Mitigation cost**: M (per PITFALLS §Risk Register Summary line 478). PoC implementation cost: §4.3 (2d) + §4.6 (1d) = 3d.

### §5.5 P6 — Memory Poisoning (PARTIAL: signed feedback PoC must, outlier detection defer)

**Risk one-liner**: Malicious or wrong feedback permanently corrupts agent behavior — MINJA-style persistent attack via query-only injection. (PITFALLS §P6 opening)

**Mitigation citations**:
- PITFALLS §P6 mitigation 1: `operator_signature: str` (HMAC over record fields, anonymous rejected by default)
- PITFALLS §P6 mitigation 2: outlier detection on feedback patterns (per-operator stats, >2σ deviation flagged for review)
- PITFALLS §P6 mitigation 3: memory-write rate-limit per operator (`feedback.daily_memory_write_cap: 20`)
- PITFALLS §P6 mitigation 4: two-operator approval for high-impact memory
- PITFALLS §P6 mitigation 5: tamper-evidence extends to memory (audit log covers `action="memory_write"`)
- PITFALLS §P6 mitigation 6: quarantine on detected poisoning (`status="quarantined"` excluded from retrieval)
- Phase 45 memory-record-schema.yaml fields: `operator_signature` + `status="quarantined"`

**PoC verdict**: **PARTIAL** (aligned with PITFALLS §Risk Register Summary P6 row: "PARTIAL — signed feedback is PoC must; outlier detection can defer" + SUMMARY §Risk Register P6 row).

**PoC-week acceptance (signed feedback — MUST implement)**:
- §4.6 dry-run-first invariant gates the `operator_signature` schema field validation. In `--apply-memory` mode, `FeedbackRecord` validates HMAC signature; anonymous feedback rejected by default (`feedback.require_signed: true` config).
- Acceptance: FeedbackRecord without valid `operator_signature` is rejected with explicit error "anonymous feedback rejected; feedback.require_signed=true".

**PoC-week acceptance (outlier detection — DEFER with monitoring)**:
- Outlier detection (>2σ deviation from population mean) needs >10 operators to be statistically meaningful. PoC has 1-2 trusted operators, outlier risk is theoretical.
- Monitoring: audit log captures `operator_id` distribution on every memory write. If any operator's `operator_id` shows >50% of evidence chains (manual review trigger), surface warning.
- Defer to v11.1+: full outlier detection job (curator stats phase per PITFALLS §P6 mitigation 2).

**Failure-if-deferred (outlier)**: PoC trusted operators (Kai + maybe 1 collaborator), poisoning risk is theoretical. If a malicious operator compromised the feedback channel, audit log + signed-feedback trail provides forensic evidence (detection, not prevention). Production rollout with public feedback channel would re-litigate this in v11.1+.

**Mitigation cost**: H for full (per PITFALLS §Risk Register Summary line 479); M for PARTIAL (PoC only signed feedback). PoC implementation cost: §4.6 includes operator_signature validation (~0.3d).

### §5.6 P7 — Round-Table Memory Conflict (must-fix-in-PoC)

**Risk one-liner**: Agents disagree because their memories disagree — screenplay agent (memory: "test audiences in this project respond well to bittersweet endings") vs theory_critic agent (memory: "tragedy endings test 23% better across all projects") reach contradictory conclusions; round table deadlocks or loudest-memory agent wins by citation volume. (PITFALLS §P7 opening)

**Mitigation citations**:
- PITFALLS §P7 mitigation 1: memory annotation in round-table turns (`memory_id`, `confidence`, `scope`, `evidence_record_count` cited per turn)
- PITFALLS §P7 mitigation 2: coordinator (Hermes) arbitrates conflicts (comparator LLM pass: "which is more applicable in this project context?")
- PITFALLS §P7 mitigation 3: scope precedence rules (`session` > `project` > `global`)
- PITFALLS §P7 mitigation 4: confidence-weighted voting (when N agents disagree, vote weighted by memory `confidence`)
- PITFALLS §P7 mitigation 5: conflict log for curator review (same memory pair conflicting >3 times → curator promotion or quarantine)
- Phase 46 round-table-state-schema.yaml: turn lifecycle + memory citation schema
- Phase 46 §3 conflict arbitration rules

**PoC verdict**: **must-fix-in-PoC** (aligned with PITFALLS §Risk Register Summary P7 row: "NO — round-table is v10.0 core feature" + SUMMARY §Risk Register P7 row).

**PoC-week acceptance**: §3.2 creative slice screenplay Step 3 round table with 9 related_agents naturally exercises P7 conflict (9 agents with different project-scoped memory will disagree on screenplay decisions like pacing vs emotion_curve priority). Acceptance: at least 1 conflict arbitration event in the round table transcript (Phase 46 §3 scope precedence or confidence-weighted voting applied).

**Failure-if-deferred**: round table deadlocks, PoC creative slice cannot complete. P7 是 v10.0 core feature (round table is the new collaboration primitive), defer is not acceptable.

**Mitigation cost**: M (per PITFALLS §Risk Register Summary line 480). PoC implementation cost: Phase 46 已 ship coordinator arbitration + scope precedence + confidence voting; PoC 仅验证 ~0.5d in §3.2 creative slice setup.

### §5.7 P8 — No Fitness Signal (must-fix-in-PoC)

**Risk one-liner**: Agent might be getting worse, not better, and you can't tell — after 3 months of curator-driven evolution, no baseline measurement answers "is screenplay agent actually better than 3 months ago?" (PITFALLS §P8 opening)

**Mitigation citations**:
- PITFALLS §P8 mitigation 1: frozen fitness battery per agent (`fitness_battery: path/to/battery.yaml`, 10-20 prompts, FROZEN at registration)
- PITFALLS §P8 mitigation 2: longitudinal `fitness_trend.jsonl` (schema: `{ts, battery_version, mean_score, per_prompt_scores, persona_sha256, model_id}`)
- PITFALLS §P8 mitigation 3: A/B shadow mode before applying memory change
- PITFALLS §P8 mitigation 4: distinguishing agent-drift from model-drift (every fitness run records `model_id` + `provider`)
- PITFALLS §P8 mitigation 5: fitness battery review cadence (quarterly operator review)
- Phase 45 agents-schema.yaml fields: `fitness_battery` + `persona_sha256`

**PoC verdict**: **must-fix-in-PoC** (aligned with PITFALLS §Risk Register Summary P8 row: "NO — load-bearing" + SUMMARY §Risk Register P8 row).

**PoC-week acceptance**: §4.1 fitness battery gates this — this is THE acceptance criterion for P8. `fitness_trend.jsonl` baseline + regression auto-quarantine logic.

**Failure-if-deferred**: no regression signal, operator cannot tell if PoC changes are improvements or regressions, all subsequent v11.x work operates blind. v11.1+ has no way to detect silent regressions introduced by curator changes.

**Mitigation cost**: M (per PITFALLS §Risk Register Summary line 481). PoC implementation cost: §4.1 (3d).

### §5.8 Risk Register Summary Table (7 rows, aligned with PITFALLS §Risk Register Summary + SUMMARY §Risk Register)

| P# | Pitfall | Severity | Verdict | PoC §4 acceptance | Failure-if-deferred | Cost |
|----|---------|----------|---------|--------------------|----------------------|------|
| P1 | Persona drift | HIGH | **must-fix** | §4.1 fitness battery (drift probe via mean_score trend) | HOOK-09 contract lost, screenplay 输出 wrong format | M |
| P2 | Stale memory | HIGH | **must-fix** | §4.4 compaction (TTL filter on 50 expired records) | Obsolete platform rules cited, operator 失去信任 | M |
| P4 | Cross-project leakage | HIGH | **must-fix** | §4.7 + §4.2 (scope=project + project_id filter) | Production rollout leaks P1→P2 memory | M |
| P5 | Curator failure modes | HIGH | **must-fix** | §4.3 + §4.6 (bias canary + dry-run-first) | Hallucinated rules silently degrade agent | M |
| P6 | Memory poisoning | HIGH | **PARTIAL** | §4.6 (signed feedback must); outlier defer per §5.10 | Trusted operators; theoretical risk in PoC | M (PARTIAL) |
| P7 | Round-table conflict | MEDIUM | **must-fix** | §3.2 creative slice (9-agent screenplay round table) | Round table deadlocks, PoC creative slice cannot complete | M |
| P8 | No fitness signal | HIGH | **must-fix** | §4.1 fitness battery (fitness_trend.jsonl baseline) | No regression signal, all v11.x work blind | M |

**Verdict counts**:
- **must-fix**: 6 (P1/P2/P4/P5/P7/P8)
- **PARTIAL**: 1 (P6 — signed feedback must, outlier defer)
- **defer-with-monitoring**: 0 (in SC#4 7-pitfall scope; P3 + P9 + P14 是 SC#3 acceptance criteria scope, not SC#4)

### §5.9 Verdict 对齐 Declaration

本 doc 7 verdicts 与 **PITFALLS §Risk Register Summary (line 470-488)** + **SUMMARY §Risk Register (line 145-160)** 一致:

| P# | 本 doc verdict | PITFALLS verdict (line 470-488) | SUMMARY verdict (line 145-160) | Aligned? |
|----|----------------|----------------------------------|--------------------------------|----------|
| P1 | must-fix | NO (load-bearing) | NO (load-bearing) | ✅ |
| P2 | must-fix | NO (load-bearing) | NO (load-bearing) | ✅ |
| P4 | must-fix | NO (load-bearing) | NO (load-bearing) | ✅ |
| P5 | must-fix | NO (load-bearing) | NO (load-bearing) | ✅ |
| P6 | PARTIAL (signed must, outlier defer) | PARTIAL (signed feedback is PoC must; outlier detection can defer) | PARTIAL (signed feedback PoC must; outlier detection defer) | ✅ |
| P7 | must-fix | NO (round-table is v10.0 core feature) | NO (round-table is v10.0 core) | ✅ |
| P8 | must-fix | NO (load-bearing) | NO (load-bearing) | ✅ |

**No divergent verdicts.** Phase 51 VALIDATE lint 脚本可 cross-check此 table.

### §5.10 Defer-with-Monitoring Plan (P6 outlier detection + P3 latency context)

**P6 outlier detection defer plan** (per §5.5 PARTIAL verdict):
- **Monitoring**: audit log captures `operator_id` distribution on every memory write. Stats CLI `hermes curator stats --bias-audit` surfaces over-represented operators.
- **Trigger for review**: any operator's `operator_id` shows >50% of evidence chains in a rolling 30-day window → manual review trigger.
- **Threshold for v11.1+ implementation**: when operator count >10 (statistically meaningful for outlier detection per §5.5 rationale).
- **Recoverability**: if outlier detection is implemented in v11.1+ and detects malicious operator after the fact, `evidence_operator_ids` in audit log enables retroactive quarantine of all memory records citing that operator.

**P3 latency SLO context** (not in SC#4 7-pitfall scope, but related context):
- P3 是 SC#3 acceptance criterion §4.2 scope (latency SLO p95<500ms), 不是 SC#4 risk register scope.
- Defer-with-monitoring per PITFALLS §Risk Register Summary line 476: "YES — can ship with single workspace, scale later".
- Monitoring: §4.2 latency benchmark runs weekly during PoC (per §6.3 calendar Week 1 + Week 6 re-run). If p95 trends upward across weeks, trigger Phase 48 物理分区 evaluation.

**Other pitfalls (P9/P10/P11/P12/P13/P14) context**:
- P9 (memory size growth) + P13 (curator runaway) + P14 (schema migration): SC#3 acceptance criteria scope (§4.4 + §4.5 + §4.7), not SC#4 risk register scope.
- P10 (privacy/leakage) + P11 (recall-vs-use) + P12 (cross-agent contamination): Phase 51 VALIDATE + v11.1+ scope, not in PoC must-pass.

---