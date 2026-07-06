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

