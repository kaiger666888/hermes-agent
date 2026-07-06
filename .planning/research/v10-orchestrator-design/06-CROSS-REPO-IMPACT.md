---
title: "v10.0 Design Doc #06 — Cross-Repo Impact: 3-Location Sync Strategy + Option B vs Physical Partition + Project Slug Stability"
status: LOCKED-for-v11.0-PoC
phase: 48-cross-repo-impact
plan: 01
type: design-doc
audience: [Kai (reviewer), v11.0 PoC implementer, v12+ architecture owner]
reading_time: 45 min
stability:
  frame: LOCKED   # 3-location frame inherited from ARCHITECTURE §6 — not re-derived
  elaborations: LOCKED   # write-authority / sync-direction / lineage tables — citable downstream
  triggers: STARTING-POINT   # §4.4 migration thresholds are revisable in Phase 51 audit
  slug_policy: LOCKED-short-term / DESIGN-long-term   # §5.2 short-term breakage accepted; §5.3-§5.6 long-term design
confidence: HIGH
sources:
  - ARCHITECTURE.md (§3.2, §3.3, §5.1, §5.2, §5.3, §6, §6.1, §6.2, §6.3, §6.4, §7.4, §8, §10.6)
  - PITFALLS.md (§P3, §P4, §P12)
  - SUMMARY.md (CC-4, OQ-6, OQ-12)
  - 00-FIRST-PRINCIPLES.md (§2.1, §2.5, §2.6, §2.7 — 决策 1, 5, 6, 7)
  - 01-AGENT-REGISTRY-SCHEMA.md (lineage field, agent_id, scope)
  - 02-ROUND-TABLE-PROTOCOL.md (project_slug required, .runtime/ path)
  - STACK.md (§3.2 Tool 3, §11.4)
  - FEATURES.md (§8 B8.1, §10 B7.4)
---

# v10.0 Design Doc #06 — Cross-Repo Impact

> 3-Location Sync Strategy (hermes-agent repo / kais-hermes-skills repo / `~/.hermes/`) + Lineage Chain (Agent YAML ↔ SKILL.md) + Option B (v11.0 PoC mem0 single backend + `agent_id` filter) vs Physical Partition (v12+ per-agent workspace) Migration Trigger Conditions + Project Slug Stability Policy + Round Table State Per-Project Path.

---

## §0 阅读指南 (Reading Guide)

### 章节地图 (Chapter Map)

| § | 标题 | 主要读者 | 稳定性 |
|---|------|---------|--------|
| §0 | 阅读指南 | 所有读者 | — |
| §1 | Framing + Scope + SC 映射 + Roadmap 定位 | Kai (reviewer) | LOCKED |
| §2 | 3-Location 同步策略 (per-artifact deep-dive of ARCHITECTURE §6 + §6.4) | v11.0 PoC implementer | LOCKED |
| §3 | Lineage Chain (Agent YAML ↔ SKILL.md traceability) | v11.0 PoC implementer + auditor | LOCKED |
| §4 | Option B vs Physical Partition Migration Trigger Conditions (resolves OQ-12 + CC-4) | v11.0 PoC implementer + v12+ architecture owner | §4.4 triggers STARTING-POINT; 其余 LOCKED |
| §5 | Project Slug Stability Policy (resolves OQ-6) | operator (Kai) + v12+ architecture owner | short-term LOCKED / long-term DESIGN |
| §6 | Round Table State Per-Project Path (ARCHITECTURE §5.1 + §5.2 elaboration) | v11.0 PoC implementer | LOCKED |
| §7 | Phase 44 7 决策 Cross-Validation Audit + OQ/CC Resolution | Kai (reviewer) + Phase 51 VALIDATE lint | LOCKED |
| §8 | Downstream Citation Guide + Coherence 声明 + References | 所有下游文档作者 | LOCKED |

### 3-Audience Guide

- **Kai (reviewer):** §1 → §7 (cross-validation audit) → §4.4 (trigger thresholds, revisable) → §5.2 (breakage acceptance). Skim §2/§3/§6 if any row in §7 audit needs spot-check.
- **v11.0 PoC implementer:** §2.4 (write authority matrix — who can write what) → §3.2-§3.4 (lineage chain — how to record `skill_sha256` + drift detection) → §4.1-§4.5 (Option B definition + PoC acceptance criteria) → §5.1 (slug derivation) → §6.1-§6.4 (round-table state path + crash recovery).
- **v12+ architecture owner:** §4.4 (migration trigger thresholds — when to switch Option B → Physical Partition) → §4.6 (migration path) → §5.3-§5.6 (stable ID mechanism adoption roadmap) → §7.4 (P3/P12 risk levels at v12+ scale).

### 稳定性 markers (Stability Markers)

- **LOCKED:** 本 doc 论证的内容在 v10.0 milestone 范围内锁定,下游文档 (04-MIGRATION-PATH / 05-POC-PLAN / 51 VALIDATE) 可直接 cite. 修改 LOCKED 内容需要新的 research phase + Kai 显式 approval.
- **STARTING-POINT:** §4.4 的 numeric thresholds 是基于 PITFALLS §P3 业界数据 + STACK §11.4 latency SLO 推导的初始值. Phase 51 audit 会根据 v11.0 PoC 实测数据 revises.
- **DESIGN-only:** §5.3-§5.6 的 `.hermes/project.id` long-term fix 是设计文档,不在 v10.0 / v11.0 PoC / v12 范围内实施.

### 本 doc 从 Phase 44/45/46 + ARCHITECTURE §5/§6 消费什么 (Consumption Preamble)

本 doc 是 **elaboration + trigger heuristics**, 不是 re-derivation. 它从以下已 LOCKED 的工件消费 (CITE-ONLY, do NOT redefine):

- **Phase 44 §2.1-§2.7 (00-FIRST-PRINCIPLES.md) 决策 1-7:** T6 协议层 / B3a Python runner / D2 storyboard-first-class / G2 通用编排框架 / α agent form / per-agent memory / 分层 CC 角色 —— 本 doc 的所有论证都假设这 7 决策已锁,只在 §7 做一次 cross-validation audit.
- **Phase 45 (01-AGENT-REGISTRY-SCHEMA.md) schema 字段:** `lineage` block (sub-fields: `derived_from_skill_id`, `derived_from_repo`, `transform_date`, `skill_sha256`) + memory-record-schema `agent_id` (required) + `scope` (global|project|session) + `memory_scope` —— 本 doc 的 §3 lineage chain 完整引用, 不重定义.
- **Phase 46 (02-ROUND-TABLE-PROTOCOL.md) protocol 不变量:** `round_table_open` 的 `project_slug` required field + state file path `~/.hermes/agents/.runtime/{slug}/round_tables/{round_table_id}.json` (atomic / append-only / crash-recoverable) —— 本 doc 的 §6 完整引用, 不重定义.
- **ARCHITECTURE.md:** §3.2 Option B 定义 + §3.3 `_scoped_agent_id` extension + §5.1 round-table state file layout + §5.2 cross-project sharing rules + §5.3 lifecycle sketch + §6 (Cross-Repo Coordination 完整表) + §6.1 transform procedure + §6.2 drift detection + §6.3 sync strategy + §6.4 Repo Impact Summary + §7.4 Project Slug Pattern + §8 anti-patterns + §10.6 OQ-6 —— 本 doc 引用 section number, 不重定义.
- **PITFALLS.md:** §P3 (Pitfall 3: Scoped Retrieval Performance Collapse — Option B ceiling) + §P4 (Pitfall 4: Cross-Project Memory Leakage) + §P12 (Pitfall 12: Cross-Agent Memory Contamination via Shared mem0 Workspace — Option B bleed risk) —— 本 doc 的 §4 引用 mitigation 1, 不重定义.
- **STACK.md:** §3.2 (Tool 3 `get_agent_memory` — `agent_id` parameter contract) + §11.4 (OQ-12 deferral — mem0 partition timing) —— §4.3 cites §3.2 for API 不变性; §4.5 cites §11.4 for latency SLO.
- **SUMMARY.md:** CC-4 (Option B lifecycle decision) + OQ-6 (slug stability) + OQ-12 (mem0 partition timing) —— 本 doc 显式 resolve 这 3 条 open question.

---

## §1 Framing + Scope + SC Mapping + Roadmap Placement

### §1.1 Framing (部署拓扑落实)

本文档定义 **v10.0 决策 5 (α agent form: YAML + persona + tools + refs + memory_scope + lineage) + 决策 6 (per-agent memory + curator-driven 自进化)** 在物理部署层面的落实 —— 把 **ARCHITECTURE §6** 已有的 3-location 表 (hermes-agent repo / kais-hermes-skills repo / `~/.hermes/`) 细化到 **write authority / sync direction / lineage 关系** 的可执行粒度, 同时锁定 **Option B (v11.0 PoC mem0 单 backend + `agent_id` filter 路由) vs Physical Partition (v12+ 每 agent 一 workspace, per PITFALLS §P3 mitigation 1)** 的迁移触发条件 + **project slug 稳定性** short-term/long-term 策略, 解决 **OQ-6 + OQ-12 + CC-4**.

本 doc 的 root-argument anchors 是 Phase 44 已锁的 4 决策 (cite by 决策号, do NOT re-derive):

- **决策 1 (T6 协议 — §2.1 of 00-FIRST-PRINCIPLES.md):** Hermes MCP server (`mcp_serve.py` stdio) + tmux dispatch + CC native MCP client. **这条决定了 hermes-agent repo 是 runtime owner** —— 所有 v11.0 PoC runtime code (`agent/agent_registry.py` / `agent/agent_dispatcher.py` / `mcp_serve.py` extensions / `plugins/memory/mem0/__init__.py` filter / `agent/curator.py` `_memory_evolution_phase`) 都 commit 到 hermes-agent repo.
- **决策 5 (α agent form — §2.5):** YAML + persona + tools + refs + memory_scope + lineage. **这条决定了 `lineage` 字段把 agent YAML 锚定到 kais-hermes-skills SKILL.md 源** —— `lineage.derived_from_skill_id` + `skill_sha256` 是 §3 lineage chain 的物理载体.
- **决策 6 (per-agent memory + curator-driven 自进化 — §2.6):** 每个 agent 有自己的 memory scope + curator 周期性跑 `_memory_evolution_phase` 写 memory delta. **这条决定了 Option B vs Physical Partition 的 migration trigger 条件是 load-bearing** —— per-agent scope 既可以 filter 路由 (Option B) 也可以物理分区 (Physical Partition), 选哪个由规模 / latency / 安全阈值决定.
- **决策 7 (分层 CC 角色 — §2.7):** Hermes 控结构 (turn_order / max_rounds / early_stop_rule / state schema), CC 控内容 (question framing / synthesis). **这条决定了 Hermes owns `.runtime/` state files, CC 永远不直接 touch** —— `~/.hermes/agents/.runtime/{slug}/round_tables/*.json` 由 Hermes dispatcher 写, CC 通过 MCP tool 间接交互.

**3 个 physical locations** (本 frame 继承自 ARCHITECTURE §6, **不是本 doc 重新推导的** —— 本 doc 的贡献是把 §6 的 owner/contents 粒度细化到 write authority / sync direction / lineage 关系 (§2) + Option B vs 物理分区迁移触发条件 (§4) + project slug 稳定性策略 (§5)):

- **Location 1 — `hermes-agent` repo** (`/data/workspace/hermes-agent/`): Design + runtime code.
  - **v10.0 deliverable:** 7 design docs under `.planning/research/v10-orchestrator-design/` (本文件 + 6 siblings). Zero code.
  - **v11.0 PoC deliverable:** `agent/agent_registry.py` (new) + `agent/agent_dispatcher.py` (new) + `mcp_serve.py` MCP tool additions (additive) + `plugins/memory/mem0/__init__.py` per-agent filter (additive `_scoped_agent_id` extension per ARCHITECTURE §3.3) + `agent/curator.py` `_memory_evolution_phase` (additive phase).
  - **v12+ deliverable:** `hermes agent transform` CLI + dashboard Agents tab + (optional) A2A Agent Card exposition.
  - **NO agent YAMLs live here** (ARCHITECTURE §6 verbatim) —— `~/.hermes/agents/*.agent.yaml` 是 operator-owned, gitignored from hermes-agent repo.
- **Location 2 — `kais-hermes-skills` repo** (`/data/workspace/kais-hermes-skills/`): SKILL lineage source.
  - **v10.0/v11.0/v12+ deliverable:** NONE modification (read-only source). `skills/movie-experts/{15 dirs}/SKILL.md` 是 agent YAML 的 **transform source**. Referenced by `lineage.derived_from_skill_id` + `skill_sha256`.
  - **v12+ optional:** add `agent_transform_notes` frontmatter field to SKILLs that have been transformed (ARCHITECTURE §6.4 row 2).
- **Location 3 — `~/.hermes/agents/`** (operator-side, runtime, canonical via `hermes_constants.get_hermes_home()` per CLAUDE.md + MEMORY.md `hermes-gateway-systemd.md`): Operator (Kai) owned.
  - **v10.0 deliverable:** NONE (directory 还不存在 —— agent YAMLs 是 v11.0 PoC artifact).
  - **v11.0 PoC deliverable:** 15 `*.agent.yaml` files via manual transform (ARCHITECTURE §6.1 procedure) + `.runtime/{slug}/round_tables/*.json` state files via dispatcher.
  - **v12+ deliverable:** curator-managed `evolution_log` + `fitness_score` mutations + (optional) physical-partition mem0 workspaces (见 §4).

### §1.2 Scope Rules (CITE-ONLY, do NOT redefine)

本 doc **细化 ARCHITECTURE §6 3-location 表到可执行粒度, 不重定义 3-location 框架本身**.

本 doc **不讨论:**

- (a) **15-expert transform 规则本身** (5-field mapping table) —— 留给 04-MIGRATION-PATH.md.
- (b) **mem0 `_scoped_agent_id` additive extension 实现细节** (contextvars vs threading.local, `_read_filters()` code patch) —— 留给 v11.0 PoC. 本 doc 只声明 API 不变性 (§4.3).
- (c) **Round table 协议字段细节** (`turn_order` 策略, `early_stop_rule`, conflict arbitration) —— 留给 02-ROUND-TABLE-PROTOCOL.md (Phase 46 已 ship).
- (d) **Live round table 执行** —— deferred to v11.0 PoC.
- (e) **A2A 协议展开** —— §4.8 只声明扩展位, 完整 A2A 是 post-v12+.

本 doc **采用 CITE-ONLY 策略引用:**

- **Phase 44 决策 1-7** (00-FIRST-PRINCIPLES.md §2.1-§2.7) —— 引用 决策号 (e.g. "决策 5"), 不重推导.
- **Phase 45 schema 字段** —— `lineage.derived_from_skill_id` + `derived_from_repo` + `transform_date` + `skill_sha256` + memory-record-schema `agent_id` (required) + `scope` (global|project|session) + `memory_scope` —— 引用字段名 + Phase 45 SC 出处, 不重定义语义.
- **Phase 46 protocol 不变量** —— `project_slug` required in `round_table_open` + state file path `~/.hermes/agents/.runtime/{slug}/round_tables/{round_table_id}.json` + atomic / append-only / crash-recoverable invariants.
- **ARCHITECTURE.md** §3.2 + §3.3 + §5.1 + §5.2 + §5.3 + §6 + §6.1 + §6.2 + §6.3 + §6.4 + §7.4 + §8 + §10.6 —— 引用 section number.
- **PITFALLS.md** §P3 + §P4 + §P12 —— 引用 mitigation 1 (物理分区) + mitigation 4 (filter enforcement).

### §1.3 SC#1-5 Mapping Table

ROADMAP Phase 48 SC#1-5 → 本 doc 章节:

| SC# | 描述 | 本 doc 解决章节 | 验证脚本 (Phase 51 VALIDATE) |
|-----|------|----------------|------------------------------|
| SC#1 | `06-CROSS-REPO-IMPACT.md` exists | §0 + §1 (本 doc 全文) | `test -f 06-CROSS-REPO-IMPACT.md && wc -l ≥ 1300` |
| SC#2 | 3-location sync strategy table complete (stored content + write authority + sync direction + lineage per location) | §1.6 quick-glance + §2 full deep-dive + §3 lineage chain | grep `write authority` + `sync direction` + `lineage` 在 §2/§3 出现 |
| SC#3 | Option B vs Physical Partition migration trigger conditions explicit (resolves OQ-12 + prevents P3/P12) | §4 full deep-dive (§4.0-§4.8) | grep `Class [ABC]` + numeric thresholds |
| SC#4 | Round table state per-project persistence path (`.runtime/{slug}/round_tables/`, references ARCHITECTURE §5.1) | §6 full deep-dive (§6.0-§6.5) | grep `ARCHITECTURE §5.1` + `.runtime/{slug}/round_tables/` |
| SC#5 | Project slug stability policy documented (resolves OQ-6) | §5 full deep-dive (§5.0-§5.6) | grep `.hermes/project.id` + `breakage` |

### §1.4 Roadmap Placement + 下游消费者

本 doc 在 v10.0 design doc 图中的位置:

```
00-FIRST-PRINCIPLES.md ─┬─> 01-AGENT-REGISTRY-SCHEMA.md ─┬─> 02-ROUND-TABLE-PROTOCOL.md ──> 04-MIGRATION-PATH.md ──> 05-POC-PLAN.md
                        │                                │
                        └─> 03-COMPARISON-VS-KIMI-MCP-SHIM.md (parallel, Phase 47, SHIPPED)
                        └─> 06-CROSS-REPO-IMPACT.md (本 doc, Phase 48, parallel — only consumes 7 决策 + ARCHITECTURE §6 skeleton)
```

本 doc 是以下下游文档的 **prerequisite**:

- **04-MIGRATION-PATH.md 的 "deployment topology prerequisite":** 15-expert transform 规则需要 3-location 表 (§2) + lineage 字段约定 (`derived_from_skill_id` + `skill_sha256`, §3) 才能定义 transform 规则的源 / 目标 / 写权限. 04 不重定义 3-location frame, 直接 cite §2.4 write authority matrix + §3.2 forward chain.
- **05-POC-PLAN.md 的 "Option B acceptance criterion source":** Option B 定义 (§4.1) + 触发条件 (§4.4) + PoC 验收条件 (§4.5) = PoC week-1 latency benchmark 阈值. 05 不重推导 Option B 生命周期, 直接 cite §4.1-§4.5.
- **Phase 51 VALIDATE 的 lint 脚本:** cross-check 本 doc 的 ARCHITECTURE §X 引用 + OQ-6/OQ-12 resolution 声明 一致 + Phase 44 决策 1-7 audit table 完整.

**LOCKED 状态声明:**

- Phase 44 决策 1-7: **LOCKED** (本 doc 只 cross-validate, 见 §7).
- Phase 45 schemas: **LOCKED** (本 doc cite-only).
- Phase 46 protocol: **LOCKED** (本 doc cite-only).
- ARCHITECTURE §6 3-location skeleton: **LOCKED** (本 doc 只 elaborate 到 write-authority / sync-direction / lineage 粒度).
- ARCHITECTURE §3.2 Option B + PITFALLS §P3 mitigation 1: **LOCKED** (本 doc 只加 migration trigger heuristics —— §4.4 是 net-new 贡献).
- ARCHITECTURE §5.1 round-table state path: **LOCKED** (本 doc 只引用 + 补充 crash recovery 设计).

### §1.5 3 个 Load-Bearing Elaborations 声明 (Beyond ARCHITECTURE §6)

本 doc 在 ARCHITECTURE §6 已有内容之外, 提供 **3 个 load-bearing elaborations**:

#### §1.5.1 3-Location Elaboration (→ §2 + §3 deep-dive)

**Cites verbatim:** ARCHITECTURE §6 (3-location owner/contents table) + §6.4 (Repo Impact Summary — v10.0/v11.0/v12+ deliverable columns).

**Existing coverage in ARCHITECTURE §6:** owner + contents at phase-deliverable granularity (v10.0/v11.0/v12+ columns).

**本 doc elaboration:** 细化到 (a) **write authority** (who can create / modify / delete each artifact class) + (b) **sync direction** (which direction information flows + mechanism + frequency) + (c) **lineage relationships** (how artifacts trace back to sources).

→ 见 §2.4 (per-artifact write authority matrix) + §3 (lineage chain).

#### §1.5.2 Option B vs Physical Partition Migration Triggers (→ §4 deep-dive, resolves OQ-12 + CC-4)

**Cites verbatim:** ARCHITECTURE §3.2 (Option B definition) + PITFALLS §P3 mitigation 1 (Physical Partition definition) + PITFALLS §P12 (cross-agent contamination bleed risk) + STACK §3.2 Tool 3 (`get_agent_memory` `agent_id` parameter) + STACK §11.4 (latency SLO) + SUMMARY CC-4 (lifecycle decision).

**Existing coverage:** ARCHITECTURE §3.2 推荐 Option B 用于 v11.0 PoC (15 agent, 单项目); PITFALLS §P3 mitigation 1 推荐 Physical Partition 用于 v12+ 规模 (18+ agent × 100+ project).

**GAP:** 两者都没给 **具体触发条件** —— "什么时候从 Option B 切到 Physical Partition?"

**本 doc elaboration (net-new 贡献):** §4.4 给出 **3 类阈值** (规模 / latency / 安全) 共 8 个 numeric triggers (A1-A3 + B1-B3 + C1-C2). 这是本 doc 唯一的 net-new 设计内容 (其余都是 cite + elaborate). CC-4 显式要求 "这个生命周期决策要在 `06-CROSS-REPO-IMPACT.md` 显式记录, 避免 v12 实施者重新讨论一遍" —— 本 doc 完成.

→ 见 §4 full deep-dive.

#### §1.5.3 Project Slug Stability Short-term/Long-term (→ §5 deep-dive, resolves OQ-6)

**Cites verbatim:** ARCHITECTURE §7.4 (Project Slug Pattern) + §10.6 (OQ-6 open question) + SUMMARY OQ-6.

**Existing coverage:** ARCHITECTURE §7.4 定义 `project_slug = {repo_basename}:{git_toplevel_abspath_sha8}` 用于 disambiguate same-name repos on different machines. ARCHITECTURE §10.6 列出 slug 重命名稳定性为 open question.

**本 doc elaboration:** §5 给出 **短期 (接受 breakage + manual recovery) + 长期 (`.hermes/project.id` stable ID)** 双轨策略 + adoption roadmap. 解决 SUMMARY OQ-6.

→ 见 §5 full deep-dive.

### §1.6 3-Location Quick-Glance Table (TL;DR)

Elevator-pitch 版本 (§2 + §3 展开 per-artifact detail):

| Location | Owner | Stores (v10.0 / v11.0 PoC / v12+) | Write Authority | Sync Direction |
|----------|-------|-----------------------------------|-----------------|----------------|
| `hermes-agent` repo (`/data/workspace/hermes-agent/`) | Kai + future contributors (git) | v10.0: 7 design docs (zero code) / v11.0 PoC: agent_registry.py + agent_dispatcher.py + mcp_serve.py extensions + mem0 filter + curator _memory_evolution_phase / v12+: `hermes agent transform` CLI + dashboard Agents tab | git PR-merge; **NO agent YAMLs live here** (gitignored) | Outbound only — hermes-agent code 是 `~/.hermes/` runtime 的 upstream; **Inbound sync from `~/.hermes/` runtime state to hermes-agent code is FORBIDDEN** |
| `kais-hermes-skills` repo (`/data/workspace/kais-hermes-skills/`) | Kai only (per MEMORY.md `kais-movie-agent-v5-hermes-native-migration.md`) | v10.0/v11.0/v12+: NONE modification (read-only); `skills/movie-experts/{15 dirs}/SKILL.md` 是 transform source | git via kais-hermes-skills workflow; hermes-agent runtime / curator / v10.0 design **NEVER modify SKILL.md** | Outbound only — SKILL.md 被 `~/.hermes/agents/*.agent.yaml` 通过 `lineage.derived_from_skill_id` + `skill_sha256` reference; **Backport agent YAML → SKILL.md is OUT OF SCOPE forever** |
| `~/.hermes/agents/` (operator-side, runtime) | Operator (Kai); canonical via `hermes_constants.get_hermes_home()` | v10.0: NONE / v11.0 PoC: 15 `*.agent.yaml` + `.runtime/{slug}/round_tables/*.json` state / v12+: curator mutations + potential physical mem0 workspaces | **SPLIT:** Operator creates `*.agent.yaml`; Curator mutates only `evolution_log` + `fitness_score`; Dispatcher appends `.runtime/...` JSON; mem0 plugin writes memory records (separate store) | Inbound from hermes-agent code + inbound from kais-hermes-skills via transform + outbound to mem0 via dispatcher `agent_id` routing + outbound to curator for evolution |

### §1.7 Out-of-Scope Declaration

本 doc **不覆盖:**

- **15-expert transform 规则 (5-field mapping table)** → 04-MIGRATION-PATH.md.
- **mem0 `_scoped_agent_id` additive extension 实现细节** (contextvars / thread-local / `_read_filters()` patch) → v11.0 PoC implementation.
- **Round table 协议字段细节** (`turn_order` 策略 / `early_stop_rule` / conflict arbitration / `early_stop_triggered` semantics) → 02-ROUND-TABLE-PROTOCOL.md (Phase 46 LOCKED).
- **Live round table 执行** (实际跑 multi-round panel) → v11.0 PoC deferred.
- **A2A 协议展开** (跨厂商 agent card endpoint) → §4.8 只声明扩展位; 完整 A2A 是 post-v12+ (per FEATURES §10 B7.4 + 03-COMPARISON-VS-KIMI-MCP-SHIM.md §4.5).
- **15 个 SKILL.md 的具体内容** → 见 `kais-hermes-skills` repo.
- **mem0 workspace provisioning 的 v12+ ops runbook** (monitoring / backup / gc × N backends) → v12+ design milestone.

