# Milestone v10.0 Requirements — Hermes-Agent 编排架构第一性原理推导(设计型)

**Goal:** 借鉴 Kimi Notion 架构2.0,结合本 repo 已 ship 的 coding-agent / GSD / curator / mem0,从第一性原理推导 Hermes-Agent 总调度器 + Hermes-native expert agents + Claude Code 执行场的三层架构 —— 产出可指导 v11.0 PoC 的设计套件,**不动任何代码**。

**Scope:** 仅设计文档(`.planning/research/v10-orchestrator-design/`),零代码改动,单 repo(hermes-agent)。

**Predecessors:**
- PROJECT.md §Current Milestone v10.0(7 锁定决策 + paradigm shift 声明)
- `.planning/research/v10-orchestrator-design/SUMMARY.md`(synthesis of STACK/FEATURES/ARCHITECTURE/PITFALLS research)
- Notion "架构2.0" page_id `39511082-af8e-80d7-83b6-e5df50d3f07c`(Kimi 2026-07-06 设计)

---

## Design Documents(7 reqs)

### DESIGN-01: First Principles Derivation

产 `00-FIRST-PRINCIPLES.md`,从 7 锁定决策推导 + 合并 FEATURES §11 / ARCHITECTURE §8 / PITFALLS 行业案例为「v10.0 显式拒绝」总表(每条引用 3 source 章节号)。

**Deliverables:**
- 7 决策的 first-principles 推导链(每决策从根本需求 → 推到选型)
- 「v10.0 显式拒绝」总表(≥10 条 anti-features / anti-patterns,每条引用 FEATURES §X + ARCHITECTURE §Y + PITFALLS §Z)
- 至少覆盖 FEATURES borrowable design points:B1.3 / B3.5 / B4.1 / B7.2 / B5.1

### DESIGN-02: Agent Registry Schema

产 `01-AGENT-REGISTRY-SCHEMA.md` + `agents-schema.yaml` + `memory-record-schema.yaml`。

**Deliverables:**
- 18-field agent YAML schema(完整 JSON Schema 定义,`agents-schema.yaml`)
- Memory record schema(`memory-record-schema.yaml`,独立于 agent schema,包含 `expires_at` / `verified_at` / `supersedes_memory_id` / `confidence` / `half_life_days` / `evidence_chain` / `evidence_operator_ids` / `status` / `confidentiality` / `scope`)
- Per-agent memory tier 规范(core / working / archival 三层)
- Curator `_memory_evolution_phase` 字段契约(类比 v6.0 `_feedback_scan_phase`)
- 15 expert 转化映射(从 ARCHITECTURE §2 拷贝)

**必须解决 Open Questions:** OQ-1(persona 版本控制)/ OQ-4(fitness_score 冷启动)/ OQ-7(memory.max_records 上限)/ OQ-13(tools 字段枚举)/ OQ-14(JSON Schema 正式定义)/ OQ-16(curator evolution phase 边界)

**必须涵盖字段级缓解(7 load-bearing pitfalls):** P1 persona drift / P2 stale memory / P4 cross-project leakage / P5 curator failure modes / P8 no fitness signal / P10 privacy(部分)/ P14 schema migration

### DESIGN-03: Round Table Protocol

产 `02-ROUND-TABLE-PROTOCOL.md` + `round-table-state-schema.yaml`。

**Deliverables:**
- Turn lifecycle(`round_table_open` → turn N → `submit_round_table_result`)
- Memory conflict arbitration 规则(comparator LLM pass + scope precedence(session > project > global)+ confidence-weighted voting + conflict log)
- Confidentiality propagation(public / internal / confidential / nda)
- `project_id` 必传规则
- 强制串行约束(GLM 4-key rotation 兼容,引用 MEMORY.md `feedback-glm-overload-reduce-concurrency.md`)
- MCP tool 命名统一(采用 STACK 形态,无前缀)

**必须解决 Open Questions:** OQ-2(turn_order 策略)/ OQ-5(agent 删除 orphan)/ OQ-9(MCP tool 命名)/ OQ-11(round_id 生成)/ OQ-15(conflict 仲裁)

**必须避免:** P7 round-table memory conflict / P11 recall-vs-use

**必须 addresses FEATURES borrowable points:** B1.4 / B2.1 / B2.3 / B4.2 / B6.1 / B7.3 / B8.2

### DESIGN-04: Comparison vs Kimi MCP Shim

产 `03-COMPARISON-VS-KIMI-MCP-SHIM.md`,T6 vs Kimi 全 MCP shim 方案逐维度对照表。

**Deliverables:**
- 7 维度对照表(协议 / dispatch / callback / state / 多 agent / 实现成本 / 稳定性)
- Subagent 形态否决论据(引用 FEATURES §11 B4.1)
- Microsoft 三层协议分层验证(引用 FEATURES §7.4 B7.1:internal → platform-native;tool → MCP;cross-platform → A2A)
- Kimi 方案中可借鉴的部分(列出 + 评估)

### DESIGN-05: Migration Path

产 `04-MIGRATION-PATH.md`,Python runner 增量迁移计划。

**Deliverables:**
- 15 expert × 5-field transform 规则(从 SKILL frontmatter 到 agent YAML)
- `default_invocation: skill_fallback → mcp_tool` 切换机制
- Memory schema 迁移(从 v6.0 FeedbackStore 到新 memory-record-schema)
- Retained-phases allowlist(`run_python_phase` 只接受 Step 7/10/11/12/0/6.5/15)
- `schema_version` 字段 + dry-run migration

**必须解决 Open Questions:** OQ-3(v7.0 mem0 `agent_id=hermes` 旧 memory 遗留)/ OQ-10(retained-phases allowlist 位置)

**必须避免:** P14 schema migration breaks memory store

### DESIGN-06: PoC Plan

产 `05-POC-PLAN.md`,v11.0 PoC 验收条件 + 实施计划。

**Deliverables:**
- PoC 目标(vertical slice 选 1 个 creative phase + 1 个 infra phase)
- 验收条件清单:
  - Fitness battery 设计(引用 PITFALLS §P8)
  - Latency SLO(p95 < 500ms,mem0 scoped retrieval)
  - Bias canary(curator `_memory_evolution_phase` hallucination 检测)
  - Compaction pass(`memory.max_records` 触发)
  - Threshold tuning(初始默认值 + 调优路径)
  - Dry-run-first invariant(curator 默认 dry-run)
  - Schema migration dry-run
- 工作量估算(每验收条件 1-3 天)
- Risk register(7 load-bearing pitfalls × PoC deferral 评估)

### DESIGN-07: Cross-Repo Impact

产 `06-CROSS-REPO-IMPACT.md`,3-location 同步策略。

**Deliverables:**
- 3-location 表(hermes-agent repo / kais-hermes-skills repo / `~/.hermes/`)
- Option B(v11.0 PoC:filter 路由)vs 物理分区(v12+:每 agent 一 workspace)迁移触发条件
- Agent YAML 跨 repo 同步策略(lineage追溯到 kais-hermes-skills SKILL)
- Round table state per-project(`.runtime/{slug}/round_tables/`)
- Project slug 稳定性(`.hermes/project.id` long-term fix)

**必须解决 Open Questions:** OQ-6(project slug 重命名) / OQ-12(mem0 backend 物理分区时机)

---

## Validation & Close-out(2 reqs)

### VALIDATE-01: Milestone Audit

产 `.planning/milestones/v10.0-MILESTONE-AUDIT.md`,核对:
- 9/9 reqs 满足(逐 req 核对 deliverables)
- 7 design docs cross-reference 一致(术语 / schema / 决策 across docs 不矛盾)
- 16 Open Questions(SUMMARY.md OQ-1..OQ-16)全部解决或显式 defer 到 v11.0
- 7 load-bearing pitfalls 全部有字段级缓解(在 DESIGN-02 / DESIGN-03 / DESIGN-06 中)
- 4 research 引用链完整(每个 design doc 引用的 STACK/FEATURES/ARCHITECTURE/PITFALLS 章节可追溯)

### VALIDATE-02: Cross-Doc Consistency Check

产 `scripts/v10-consistency-check.py`(lint 脚本),自动检查 7 design docs 的:
- 术语一致(`agent` / `skill` / `round table` / `panel` / `turn` 等)
- Schema 引用一致(`agents-schema.yaml` 字段名 == design docs 中提及的字段名)
- 决策号引用一致(决策 1-7 在每个 doc 中描述一致)
- MCP tool 命名一致(统一 STACK 形态)

**Note:** 若 v10.0 后期发现 lint 脚本过度工程,可在 plan-phase 时降级为 manual check。

---

## Traceability

| REQ-ID | Phase | Status | 文档 | OQ 解决 | Pitfall 避免 | Research 引用 |
|--------|-------|--------|------|--------|-------------|--------------|
| DESIGN-01 | Phase 44 | Complete | 00-FIRST-PRINCIPLES.md | — | — | FEATURES §10,11 + ARCHITECTURE §8 + PITFALLS 全文 |
| DESIGN-02 | Phase 45 | Complete | 01-AGENT-REGISTRY-SCHEMA.md + agents-schema.yaml + memory-record-schema.yaml | OQ-1,4,7,13,14,16 | P1,P2,P4,P5,P8,P10,P14 | ARCHITECTURE §1,2,3,4 + PITFALLS 全文 + STACK §3.2 |
| DESIGN-03 | Phase 46 | Complete | 02-ROUND-TABLE-PROTOCOL.md + round-table-state-schema.yaml | OQ-2,5,9,11,15 | P7,P11 | STACK §3.2 + ARCHITECTURE §4,5 + FEATURES §1.3,2.3,10 + PITFALLS §P7,11 |
| DESIGN-04 | Phase 47 | Complete | 03-COMPARISON-VS-KIMI-MCP-SHIM.md | — | — | FEATURES §4,7.4,11 + STACK §1-5 + Kimi Notion 架构2.0 |
| DESIGN-05 | Phase 49 | Pending | 04-MIGRATION-PATH.md | OQ-3,10 | P14 | ARCHITECTURE §2,6 + STACK §3.2 Tool 7 |
| DESIGN-06 | Phase 50 | Pending | 05-POC-PLAN.md | — | P1-P14(全部 PoC 验收) | PITFALLS 全文 + STACK §7 + FEATURES §14 |
| DESIGN-07 | Phase 48 | Complete | 06-CROSS-REPO-IMPACT.md | OQ-6,12 | P3,P12 | ARCHITECTURE §6 + STACK §3.2 |
| VALIDATE-01 | Phase 51 | Pending | v10.0-MILESTONE-AUDIT.md | 全部核对 | 全部覆盖 | 全部 |
| VALIDATE-02 | Phase 51 | Pending | scripts/v10-consistency-check.py | — | — | 全部 |

**Coverage:** 9 / 9 mapped ✓ · Phases 44-51 · No orphans.

---

## Out of Scope

- **任何代码改动** —— 不动 SKILL.md / Python / plugin manifest / `mcp_serve.py` / `agent/curator.py` / `plugins/memory/mem0/`。所有代码工作 deferred 到 v11.0 PoC
- **kais-hermes-skills repo 改动** —— 设计文档仅引用其 SKILL.md 作 lineage 源,不改 SKILL
- **新建独立 repo(如 kais-orchestrator)** —— 单 repo 收敛(hermes-agent),设计完成后 v11.0 PoC 再决定是否拆 repo
- **live round table 执行** —— v10.0 仅设计协议,v11.0 PoC 才真跑
- **per-agent memory 实测** —— v10.0 仅设计 schema + 字段,v11.0 PoC 跑 latency benchmark

---

*Last updated: 2026-07-06 — Traceability table updated with Phase mapping (9/9 reqs → 8 phases 44-51). VALIDATE-01 + VALIDATE-02 merged into Phase 51 (lint script is audit's tool). ROADMAP.md created.*
