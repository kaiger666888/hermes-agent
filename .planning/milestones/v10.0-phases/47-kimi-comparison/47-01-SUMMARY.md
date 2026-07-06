---
phase: 47-kimi-comparison
plan: 01
subsystem: v10-orchestrator-design
tags: [v10.0, design-doc, kimi-comparison, subagent-rejection, microsoft-three-layer, mcp-shim, horizontal-validation]
requires:
  - .planning/research/v10-orchestrator-design/00-FIRST-PRINCIPLES.md (Phase 44 — 7 决策 root arguments)
  - .planning/research/v10-orchestrator-design/01-AGENT-REGISTRY-SCHEMA.md (Phase 45 — 18-field + 10-field schemas)
  - .planning/research/v10-orchestrator-design/02-ROUND-TABLE-PROTOCOL.md (Phase 46 — turn lifecycle + memory conflict arbitration)
  - .planning/research/v10-orchestrator-design/STACK.md (T6 协议层 Recommended Stack + 7 MCP tool schema)
  - .planning/research/v10-orchestrator-design/FEATURES.md (业界 framework 对照 + §7.4 B7.1 + §11 B4.1 + §4.3 + §10 borrowable)
  - .planning/research/v10-orchestrator-design/ARCHITECTURE.md (§4 dispatch + §5 state layer + §8 anti-patterns)
  - .planning/research/v10-orchestrator-design/PITFALLS.md (§P5 curator failure + §P12 cross-agent contamination)
  - .planning/research/v10-orchestrator-design/SUMMARY.md (4 research cross-cutting findings + 7 决策 validated table)
provides:
  - .planning/research/v10-orchestrator-design/03-COMPARISON-VS-KIMI-MCP-SHIM.md (T6 vs Kimi 全 MCP shim 7-dimension contrast + subagent rejection argument library + Microsoft 三层 validation + Kimi borrowable evaluation; consumed by 04/05/06/51)
affects:
  - .planning/research/v10-orchestrator-design/ (本 doc 加入 v10.0 design docs 集,与 00-02 平行)
  - .planning/phases/48-cross-repo-impact/ (06-CROSS-REPO-IMPACT cites 本 doc §4.5 A2A 扩展位)
  - .planning/phases/49-migration-path/ (04-MIGRATION-PATH cites 本 doc §3.2 dispatch boundary tool + §3.4 三层 state)
  - .planning/phases/50-poc-plan/ (05-POC-PLAN cites 本 doc §3 + §5 + §6.1 as defense brief)
  - .planning/phases/51-validate/ (VALIDATE lint cross-checks §3 7-dimension + §5 subagent rejection + §6.1 borrowable + §7 7 决策 audit consistency)
tech-stack:
  added: []  # design-only milestone, zero code
  patterns:
    - horizontal validation (cross-validate Phase 44 7 决策 in 7-dimension contrast)
    - CITE-ONLY citation discipline (do NOT redefine Phase 44/45/46 fields/decisions/protocols)
    - Steelman-the-Elimination (§2 Kimi 方案 reconstruction before rebuttal)
    - Bilingual EN structure + 中文 prose per CLAUDE.md
key-files:
  created:
    - .planning/research/v10-orchestrator-design/03-COMPARISON-VS-KIMI-MCP-SHIM.md (1405 lines, single deliverable)
  modified: []
decisions:
  - "T6 protocol layer validated 7/7 against Phase 44 决策 1-7 (cross-validation audit §7.1)"
  - "Kimi 全 MCP shim rejected: violates Microsoft 三层 (§4.3 3 violations) + 决策 5/6/7 (state/dispatch/memory)"
  - "Subagent form (Claude Agent SDK .claude/agents/*.md) rejected: context-isolated + source-scoped memory + 30-day cleanup violates 决策 5/6/7 (§5 7-subsection deep-dive)"
  - "Kimi-side borrowable: B8.1 Agent Card + B4.2 hooks + B4.3 effort + B7.3 file-level lock borrowed (3 ✅ + 1 ⚠️ v11.1+); B7.2 short-lived agent + shared knowledge graph + subagent form rejected (3 ❌)"
  - "Microsoft 三层 protocol validation: T6 100% align industry consensus (B7.1 + B2.2 + B7.4 三条 borrowable points 一致结论)"
metrics:
  duration: ~50 minutes (5 tasks)
  completed: 2026-07-07
  tasks_completed: 5
  files_created: 1
  lines_written: 1405
---

# Phase 47 Plan 01: Kimi Comparison Summary

T6 vs Kimi 全 MCP shim 7-dimension 横向验证 + subagent 形态否决论据库 + Microsoft 三层协议 alignment 论证 —— 1405 行双语设计文档,作为 v11.0 PoC 实施者的「why T6 not full MCP shim」defense brief。

## Final Deliverable

**File:** `.planning/research/v10-orchestrator-design/03-COMPARISON-VS-KIMI-MCP-SHIM.md`
**Lines:** 1405
**Sections:** §0-§8(9 主章节,36 子章节)

## 7-Dimension Contrast Lock(协议 / dispatch / callback / state / 多 agent / 实现成本 / 稳定性)

| 维度 | T6 选型论据(决策号) | Kimi 违反决策号 |
|------|---------------------|----------------|
| §3.1 协议 | 决策 1(T6 协议层) | 决策 1(违反 Microsoft 三层) |
| §3.2 dispatch | 决策 5 + 7(Hermes 控 agent + 结构) | 决策 5(30-day)+ 6(source-scoped)+ 7(tools whitelist CC) |
| §3.3 callback | 决策 7 + 3(Hermes 控结构 + D2 round table) | 决策 3(无 round table)+ 7(违反分层) |
| §3.4 state | 决策 5 + 6(三层持久化) | 决策 6(30-day + shared graph + 无 curator) |
| §3.5 多 agent | 决策 3 + 7(round table 协议) | 决策 3(无协商)+ 7(违反 GLM concurrency policy) |
| §3.6 实现成本 | 决策 4(复用 v6.0/v7.0 + G2 工程量摊薄) | 决策 4(shared graph project-scoped,G2 难实施) |
| §3.7 稳定性 | 决策 6(per-agent memory + curator + 8 PITFALLS 字段级 mitigation) | 决策 6(直接违反,P5/P12 不可 mitigation) |

**结论:** T6 7/7 维度更好服务 Phase 44 决策;Kimi 7/7 维度都至少违反一条决策。

## Microsoft 三层 Validation Lock(SC#4)

- **§4.1 verbatim citation from FEATURES §7.4 B7.1:**「Platform-native orchestration for internal flows; MCP for tool and data access; A2A for cross-platform agent-to-agent messaging」
- **§4.2 v10.0 T6 → Microsoft 三层 mapping table:** T6 完全 align(platform-native = Hermes runtime;tool access = MCP;mcp_serve.py extension;A2A deferred to v12+)
- **§4.3 Kimi 3 violation points:** (1) agent ↔ agent 塞进 MCP;(2) agent identity 在 CC filesystem 而非 platform-native;(3) shared graph 不留 A2A 扩展位
- **§4.4 业界共识论证:** B7.1 + B2.2 + B7.4 三条 FEATURES borrowable points 一致结论(T6 align,Kimi 违反)

## Subagent Rejection Lock(SC#3)

- **§5.1 FEATURES §11 B4.1 verbatim citation:** subagent context-isolated, memory 弱, 30 天清理 → v10.0 替代 Hermes-side YAML agent
- **§5.2 FEATURES §4.3 三个 fact 逐条展开:**
  - Fact 1:context-isolated —— 「The only channel from parent to subagent is the Agent tool's prompt string」
  - Fact 2:source-scoped —— `'user' / 'project' / 'local'`,不是 namespace scoped
  - Fact 3:30-day cleanup —— transcripts 30 天自动清理
- **§5.3 context-isolated subagent 不适合 round table panelist 的 4 个原因:** token cost(~230K just for prior context)/ memory conflict arbitration 不可实施 / turn lifecycle atomicity 不兼容 / decision 7 分层违反
- **§5.4 source-scoped memory 不能做 per-agent 自进化的 4 条机制矛盾:** curator impossible / cross-project impossible / 字段缺失 / persona drift detection 缺失
- **§5.5 30-day cleanup 违反决策 6 长生命周期 agent:** operator 投入(persona tuning / feedback feeding / fitness battery)30 天后归零
- **§5.6 Hermes-side YAML 18-field schema 对照 AgentDefinition 9-field:** 缺 9 个 v10.0 必需字段(memory_scope / persona_sha256 / evolution_log / fitness_score / lineage / default_invocation / agent_card / round_table_eligible / skill_fallback)
- **§5.7 Kai user memory verbatim citation:** hermes-native-expert-agents.md(2026-07-06)+ coding-agent-vs-mcp-shim.md(2026-07-06)— Kai 已显式否决 subagent 形态
- **§5.8 Counter-argument 反驳:** 3 个 Kimi 续聊可能反驳点全部 collapse 回 T6 或违反 v10.0 政策
- **§5.9 Subagent rejection 与 7 决策 traceability matrix:** 9 行 audit,每行 trace 到决策号 + Phase 46 章节

## Kimi-Side Borrowable Evaluation Lock(SC#5)

**§6.1 7-row borrowable evaluation table:**

| Kimi-side idea | FEATURES ID | T6 兼容性 | 喂给 doc |
|----------------|-------------|-----------|----------|
| Agent Card concept | B8.1 | ✅ 兼容(Phase 45 已收) | 01-AGENT-REGISTRY-SCHEMA.md |
| Hooks lifecycle | B4.2 | ✅ 兼容(v11.1+ opt-in) | 02-ROUND-TABLE-PROTOCOL.md §6.2 |
| effort 字段 | B4.3 | ✅ 兼容(Phase 45 已收) | 01-AGENT-REGISTRY-SCHEMA.md |
| File-level lock | B7.3 | ⚠️ v11.1+ only | 02-ROUND-TABLE-PROTOCOL.md §6.4 |
| Agent-MCP short-lived agent | B7.2 | ❌ 拒绝(违反决策 6) | 00-FIRST-PRINCIPLES.md §3 |
| Shared knowledge graph | §7.2 | ❌ 拒绝(违反决策 6 per-agent scope) | 00-FIRST-PRINCIPLES.md §3 |
| `.claude/agents/` filesystem form | §4.2 | ❌ 拒绝(违反决策 5) | 00-FIRST-PRINCIPLES.md §3 + 本 doc §5 |

**分布:** 3 条 ✅ 兼容 + 1 条 ⚠️ v11.1+ + 3 条 ❌ 拒绝 = 4 借鉴 / 3 拒绝。

## Phase 44 决策 1-7 Cross-Validation Lock

**§7.1 7-row 决策 audit table:** 7/7 ✅ 一致(本 doc 未发现 Phase 44 决策需修正)。

**§7.2 偏差分析:** 实际 = 预期(7/7 一致)。未来可能偏差来源:OQ-12 mem0 filter latency / v12+ A2A 启用 / GLM capacity 扩展。

**§7.3 Phase 44 §3 显式拒绝总表与本 doc §5 + §6.6 一致性:** 三层互补(Phase 44 §3 root rejection / 本 doc §5 SC#3 deep-dive / 本 doc §6.6 SC#5 不借鉴清单)。

## SC#1-5 Coverage Confirmed

| SC# | 章节 | coverage |
|-----|------|----------|
| SC#1 | 文件存在 | ✅(1405 lines) |
| SC#2 | 7-dimension contrast | ✅(§1.6 TL;DR + §3.1-§3.7 prose + §3-overall 总结) |
| SC#3 | Subagent rejection | ✅(§1.5.2 + §5.0-§5.9 10 子节) |
| SC#4 | Microsoft 三层 validation | ✅(§1.5.1 + §4.0-§4.6 7 子节) |
| SC#5 | Kimi borrowable evaluation | ✅(§6.0-§6.7 8 子节) |

## Cross-Validation: Citation Discipline

每个 section 都 cite Phase 44 决策号 / Phase 45 schema 字段 / Phase 46 protocol 章节 / 4 research docs(STACK / FEATURES / ARCHITECTURE / PITFALLS)具体 section:

- **决策号引用:** 决策 1-7 在 §3 + §5 + §7 中各被引用至少一次(§7.1 audit 验证 7/7 ✅)
- **Phase 45 字段 CITE-ONLY:** memory_scope / scope / confidence / evidence_chain / persona_sha256 / fitness_score / evolution_log / lineage 全部引用,不重定义
- **Phase 46 协议 CITE-ONLY:** round_table_open / get_agent_opinion / submit_round_table_result 三原子操作 + memory conflict arbitration 5 子机制 引用,不重定义
- **FEATURES §X 引用:** §4 / §7.4 / §8 / §10 / §11 各 cite at least once(B4.1 + B7.1 + B8.1 + B4.2 + B4.3 + B7.3 + B7.2 + B2.2 + B7.4 + B8.3 全部出现)
- **STACK §X 引用:** §1(Recommended Stack)+ §3.2(7 MCP tool schema)+ §4(Transport)
- **ARCHITECTURE §X 引用:** §4(dispatch path)+ §5(round table state layer)+ §8(anti-patterns Kimi-side subset)
- **PITFALLS §X 引用:** §P5(curator failure)+ §P12(cross-agent contamination)+ §3(scoped retrieval perf,OQ-12)

## Methodology Audit(自检 before commit)

- ✅ 每维度 cites FEATURES §X / STACK §Y / ARCHITECTURE §Z source(不 invented)
- ✅ Phase 44 决策 1-7 cited by 决策号(§7.1 audit 7/7 ✅)
- ✅ Phase 45 schema fields cited by name(memory_scope / scope / confidence / evidence_chain / persona_sha256 / fitness_score / evolution_log / lineage),never redefined
- ✅ Phase 46 protocol invariants cited by section(serial execution / STACK-form MCP naming / atomic turn lifecycle),never redefined
- ✅ FEATURES §7.4 B7.1 + §11 B4.1 + §4.3 + §10 borrowable points each cited by section number
- ✅ Microsoft multi-agent-patterns URL appears in references(HIGH confidence source,3 occurrences)
- ✅ Bilingual: EN structure(headers / schemas / citation tags)+ 中文 prose(rationale / examples)per CLAUDE.md
- ✅ §7 audit confirms 7/7 决策 cross-validation consistent(no silent Phase 44 revision)

## Deviations from Plan

None — plan executed exactly as written. All 5 tasks completed, all verification scripts passed, all done criteria met.

## Self-Check: PASSED

**1. Created files exist:**

- `.planning/research/v10-orchestrator-design/03-COMPARISON-VS-KIMI-MCP-SHIM.md` — 1405 lines,§0-§8 完整 ✅

**2. Commits exist:**

- `5a0b8ea75` — Task 1(§0 + §1)✅
- `aa1d02b34` — Task 2(§2 + §3.1-§3.4)✅
- `a45a2b8a7` — Task 3(§3.5-§3.7 + §4)✅
- `1f2c8c944` — Task 4(§5 + §6)✅
- `613cec47f` — Task 5(§7 + §8)✅

**3. Plan verification scripts all PASSED:**

- Task 1 verify(≥250 lines + §0/§1 + 18 terms)✅
- Task 2 verify(≥600 lines + §2/§3 + 22 terms + ≥8 决策 refs)✅
- Task 3 verify(≥900 lines + §3 ≥7 subs + §4 ≥5 subs + 23 terms + §4.2 ≥3 决策 + §4.3 ≥3 violations)✅
- Task 4 verify(≥1200 lines + §5 ≥7 subs + §6 ≥6 subs + 23 terms + §6.1 ≥5 B*.x refs)✅
- Task 5 verify(≥1400 lines + §7 ≥3 subs + §8 ≥2 subs + 17 terms + §7.1 ≥7 决策 + ≥7 ✅ + MS url)✅
