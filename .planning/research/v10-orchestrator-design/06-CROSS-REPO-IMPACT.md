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

---

## §2 3-Location Sync Strategy (Per-Artifact Elaboration of ARCHITECTURE §6 + §6.4)

### §2.0 Elaboration 声明 (SC#2 Framing)

本节是 **ROADMAP SC#2 的完整论证**. ARCHITECTURE §6 已给 3-location owner/contents 表 + §6.4 已给 v10.0/v11.0/v12+ deliverable 矩阵 —— 这两张表都是 phase-deliverable 粒度 (e.g. "hermes-agent repo: 7 design docs / agent_registry.py / hermes agent transform CLI").

本节把这两张表 **细化到可执行粒度** —— 当 v11.0 PoC 实施者或 v12+ architecture owner 问 "谁能写这个 artifact? 这个 artifact 怎么 sync 到其他 location?", 本节回答. 细化维度:

- **(a) Write Authority (写权限):** 谁可以 create / modify / delete 每个 artifact class.
- **(b) Sync Direction (同步方向):** 信息流方向 + 机制 + 频率.
- **(c) Lineage Relationships:** artifacts 如何 trace 回 sources (见 §3 deep-dive).

### §2.1 Location 1 — `hermes-agent` Repo Deep-Dive

- **Owner:** Kai + future contributors (standard git workflow via PR merge).
- **v10.0 deliverable:** 7 design docs under `.planning/research/v10-orchestrator-design/` (本 doc + `00-FIRST-PRINCIPLES.md` + `01-AGENT-REGISTRY-SCHEMA.md` + `02-ROUND-TABLE-PROTOCOL.md` + `03-COMPARISON-VS-KIMI-MCP-SHIM.md` + 未来的 `04-MIGRATION-PATH.md` + `05-POC-PLAN.md`). Zero code.
- **v11.0 PoC deliverable:**
  - `agent/agent_registry.py` (new — sibling to `tools/registry.py` per ARCHITECTURE §7.1 Pattern)
  - `agent/agent_dispatcher.py` (new — owns `agent_id` routing + tmux session lifecycle)
  - `mcp_serve.py` MCP tool additions (additive — 7 new tools per STACK §3.2: `get_agent_persona` / `get_agent_memory` / `query_memory` / `round_table_open` / `submit_round_table_result` / `run_python_phase` / `agent_decide`)
  - `plugins/memory/mem0/__init__.py` per-agent filter (additive `_scoped_agent_id` extension per ARCHITECTURE §3.3 — `_read_filters()` returns `{"user_id", "agent_id"}` when scoped)
  - `agent/curator.py` `_memory_evolution_phase` (additive third phase after `_feedback_scan_phase`)
- **v12+ deliverable:** `hermes agent transform --from skill --to agent --name <name>` CLI + dashboard Agents tab + (optional) A2A agent card exposition.
- **Write Authority:** git-tracked; PR-merge via standard hermes-agent workflow.
- **NO agent YAMLs live here** (ARCHITECTURE §6 verbatim) —— `~/.hermes/agents/*.agent.yaml` 是 operator-owned, gitignored from hermes-agent repo.
- **Sync Direction:**
  - **Outbound only** —— hermes-agent code 是 `~/.hermes/` runtime 的 upstream.
  - **Frequency:** each hermes-agent release (pip install / git pull of hermes-agent; runtime reads `~/.hermes/agents/` at startup per ARCHITECTURE §6.3 row 2).
  - **Inbound sync from `~/.hermes/` runtime state to hermes-agent code is FORBIDDEN** —— anti-pattern: agent YAML drift leaking into code, per ARCHITECTURE §8.2 spirit (auto-re-transform forbidden).
- **Lineage:** hermes-agent code 是 **runtime owner** —— 它定义 schema (agents-schema.yaml) + protocol (round-table-state-schema.yaml) + dispatch path (`agent_dispatcher.py`), 但 **不 own 运行时数据**. Design docs (本 file + siblings) 是所有 v11.0+ implementation 的 upstream.

### §2.2 Location 2 — `kais-hermes-skills` Repo Deep-Dive

- **Owner:** Kai only (via kais-hermes-skills repo workflow). Per MEMORY.md `kais-movie-agent-v5-hermes-native-migration.md` (2026-07-02): cross-repo migration moved `skills/movie-experts` + 4 plugins 到 kais-hermes-skills repo. hermes-agent repo 现仅保留 GSD `.planning/` 工件 + runtime code.
- **v10.0 deliverable:** NONE (read-only source).
- **v11.0 PoC deliverable:** NONE (SKILLs remain as fallback per `default_invocation: skill_fallback` decision per Phase 45 / ARCHITECTURE §6.4 row 2 v11.0 column).
- **v12+ deliverable:** Optional —— add `agent_transform_notes` frontmatter field to SKILLs that have been transformed (ARCHITECTURE §6.4 row 2 v12+ column).
- **Write Authority:** git-tracked via kais-hermes-skills repo.
- **hermes-agent runtime / curator / v10.0 design NEVER modify SKILL.md.** Read-only from hermes-agent's perspective.
- **Sync Direction:**
  - **Outbound only** —— SKILL.md 被 `~/.hermes/agents/*.agent.yaml` 通过 `lineage.derived_from_skill_id` + `skill_sha256` reference (Phase 45 agents-schema.yaml lineage block).
  - **Transform procedure (ARCHITECTURE §6.1) reads SKILL.md, never writes back.**
  - **Backport agent YAML → SKILL.md is OUT OF SCOPE forever** (per ARCHITECTURE §6.3 closing statement verbatim "explicitly out of scope for v10.0 (and likely forever — agents and skills are different layers, as declared in PROJECT.md paradigm shift)"; reinforced by §3.5 invariant L4 below).
- **Lineage:** SKILL.md 是 **transform source** —— 每个 agent YAML 通过 `lineage` block 追溯到 exactly 一个 SKILL.md.
  - **Forward chain:** SKILL.md → (transform procedure §3.2) → agent YAML. 见 §3.2.
  - **Backward chain:** agent YAML → `lineage.derived_from_skill_id` → resolve SKILL.md path → read content + compute sha256. 见 §3.3.

### §2.3 Location 3 — `~/.hermes/agents/` Deep-Dive

- **Owner:** Operator (Kai). Canonical state root via `hermes_constants.get_hermes_home()` (per CLAUDE.md + MEMORY.md `hermes-gateway-systemd.md`: `~/.hermes/` 是 canonical state root).
- **v10.0 deliverable:** NONE (directory doesn't exist yet —— agent YAMLs 是 v11.0 PoC artifact).
- **v11.0 PoC deliverable:**
  - 15 `*.agent.yaml` files created by manual transform (ARCHITECTURE §6.1 procedure, 5 steps, ~5-10 min per agent)
  - `.runtime/{slug}/round_tables/*.json` state files created by dispatcher
  - `evolution_log` initial empty (curator 周期性 append, 见下)
- **v12+ deliverable:**
  - Curator-managed `evolution_log` + `fitness_score` mutations (per Phase 45 SC#3 dry-run-first invariant)
  - Potential physical-partition mem0 workspaces (见 §4.2 + §4.4 Class A threshold)
- **Write Authority SPLIT across actors (key elaboration beyond ARCHITECTURE §6):**
  - **Operator (Kai):** Creates `*.agent.yaml` via manual transform. Hand-tunes `persona` (operator owns the persona — first-person 5-15 lines per ARCHITECTURE §8.1 anti-pattern). Can delete agent YAML (orphan handling per Phase 46 §3 OQ-5: "open 时 snapshot identity, deleted agent 在 transcript 显示 'deleted' badge").
  - **Curator:** Mutates ONLY `evolution_log` (append) + `fitness_score` (update) + `last_fitness_battery_run_at` (update). **Cannot modify** `persona` / `persona_sha256` / `tools` / `memory_scope` / `lineage`. Dry-run-by-default per Phase 45 SC#3.
  - **Dispatcher (Hermes runtime):** Appends `.runtime/{slug}/round_tables/*.json` only. **NEVER touches** `*.agent.yaml` (per Phase 44 决策 7 — Hermes 控结构, CC 控内容, 但 agent YAML 是 operator-owned identity, 不是 Hermes 的结构层).
  - **mem0 plugin:** Writes per-agent memory records (separate store — mem0 backend, NOT in `~/.hermes/agents/`. 见 §4 Option B vs Physical Partition).
- **Sync Direction:**
  - **Inbound from hermes-agent code** —— runtime reads schema + dispatch logic each Hermes startup.
  - **Inbound from kais-hermes-skills** —— via transform procedure (manual v11.0 / scripted v12+).
  - **Outbound to mem0 backend** —— via dispatcher `agent_id` routing (Option B) or workspace selection (Physical Partition, v12+).
  - **Outbound to curator** —— for `_memory_evolution_phase` (LLM-distills memory delta from feedback → appends to `evolution_log`).
- **Lineage:** `~/.hermes/agents/*.agent.yaml` 是 **runtime truth** —— 每个 round-table turn + 每个 mem0 memory record + 每个 curator evolution delta 都追溯到一个 YAML here.

### §2.4 Per-Artifact-Class Write Authority Matrix

7 artifact classes × 5 actor columns. ✅ = allowed; ❌ = forbidden (with rationale); 🔒 = locked-by-design (would violate invariant).

| Artifact Class | Operator (Kai) | Curator | Dispatcher | Hermes code (PR-merge) | External contributor |
|----------------|----------------|---------|------------|------------------------|----------------------|
| **(1) `*.agent.yaml`** in `~/.hermes/agents/` | ✅ Create / modify / delete (manual transform + hand-tune persona) | 🔒 Cannot modify `persona` / `persona_sha256` / `tools` / `memory_scope` / `lineage` (would violate Phase 45 SC#1 `persona_sha256` invariant + PITFALLS §P1 mitigation 4). ✅ Can modify `evolution_log` + `fitness_score` (see row 4/5) | ❌ Dispatcher never writes YAML files directly (per 决策 7 — Hermes 控结构, 但 YAML 是 operator-owned identity) | ❌ Hermes repo gitignores `~/.hermes/agents/` (ARCHITECTURE §6) | ❌ Same as Hermes code |
| **(2) Per-agent mem0 memory records** | ✅ Manually via `mem0_profile` MCP tool (debug only) | ✅ Curator `_memory_evolution_phase` writes memory deltas (per ARCHITECTURE §3.4 + Phase 45 `evidence_chain` ≥3 invariant) | ✅ Dispatcher routes via `agent_id` filter on every `mem0.add()` (Option B) or workspace select (Physical Partition) | n/a — mem0 plugin runtime code is in Hermes repo, but data is in mem0 backend | ❌ No direct mem0 access (mem0 API key operator-only) |
| **(3) `.runtime/{slug}/round_tables/*.json`** | ❌ Operator never hand-edits state files (binary structure) | ❌ Curator reads for context but never writes | ✅ Dispatcher appends turn records via atomic write-temp-rename (per Phase 46 §4 invariant) | n/a — state is runtime data, not code | ❌ Filesystem perms |
| **(4) `evolution_log` entries** (inside agent YAML) | ❌ Operator should not hand-write (curator's domain) | ✅ Curator `_memory_evolution_phase` appends (dry-run-by-default per Phase 45 SC#3) | ❌ Dispatcher never mutates YAML | n/a | ❌ |
| **(5) `fitness_score` field** (inside agent YAML) | ❌ Operator does not hand-edit (curator's domain) | ✅ Curator `fitness_battery` pass updates (per PITFALLS §P8 mitigation 1) | ❌ | n/a | ❌ |
| **(6) `.planning/research/v10-orchestrator-design/*.md`** design docs | ✅ Kai + contributors via git PR | ❌ Curator has no design-doc access | ❌ | ✅ Standard hermes-agent PR merge | ✅ Standard PR |
| **(7) `skills/movie-experts/*/SKILL.md`** in kais-hermes-skills repo | ✅ Kai only (via kais-hermes-skills workflow) | ❌ Curator never writes to kais-hermes-skills | ❌ | ❌ hermes-agent runtime never writes SKILL.md | ❌ Cross-repo boundary |

**Key 🔒 (locked-by-design) cells:**

- (1) Curator cannot modify `persona` — would violate `persona_sha256` invariant (Phase 45 SC#1 + PITFALLS §P1 mitigation 4: persona drift defense).
- (1) Dispatcher never writes YAML — would break operator ownership of persona (决策 5: α form is operator-owned identity).
- (3) Operator never hand-edits state JSON — would corrupt atomic-write invariant (Phase 46 §4).
- (7) All non-Kai actors forbidden from SKILL.md — kais-hermes-skills 是 separate repo, only Kai has write access (per MEMORY.md `kais-movie-agent-v5-hermes-native-migration.md`).

### §2.5 Cross-Project Sharing Rules (ARCHITECTURE §5.2 Reference + Interpretation)

**Cite ARCHITECTURE §5.2 verbatim** (5-row table):

| Artifact | Scope | Rationale |
|----------|-------|-----------|
| Agent YAML (`~/.hermes/agents/*.agent.yaml`) | **Cross-project** (operator-owned) | Persona + tools + lineage are stable identity, not project state. |
| Per-agent memory (mem0 with `agent_id` filter) | **Cross-project** (operator-owned) | "Cinematographer learned LHD declaration from Volvo case" applies everywhere cinematographer is invoked. |
| Round table state (`~/.hermes/agents/.runtime/{slug}/round_tables/*.json`) | **Per-project** | Each project has its own questions, panel configs, and synthesis outcomes. |
| Evolution log entries (in agent YAML) | **Cross-project** | Memory deltas accumulate across all projects (this is the "agent gets better with more projects" value prop). |
| Fitness score (in agent YAML) | **Cross-project** | Same — single rolling quality number per agent. |

本 doc **完全继承** ARCHITECTURE §5.2 这张表, **不重定义**.

**Key insight for SC#4 (round-table state per-project):** round-table state 是 per-project 因为每个 project 有自己的 question / panel configs / synthesis outcomes. `.runtime/{slug}/round_tables/` 路径反映这一点 —— **slug 隔离是 load-bearing**. 见 §6.3 的具体例子 (kais-movie-pipeline Volvo S1-1 question 不能跨 project 共享).

**Subtle implication (ARCHITECTURE §5.2 closing paragraph):** round-table turn snapshots 在 turn time 捕获 `fitness_score`, 所以 transcript 是 reproducible 即使 agent's current score 在 round table 结束前 drift 了. Dispatcher writes snapshot (不是 reference) —— 这 invariant 是 by-design preserved.

**对 §2.4 write authority matrix 的 implication:**

- Artifact class (1) + (4) + (5) 是 cross-project —— 任何 actor 写它们时要意识到改动影响所有 project.
- Artifact class (3) 是 per-project —— 写 `.runtime/{slug}/round_tables/*.json` 只影响一个 project.
- 这种 scope 区分解释了为什么 dispatcher (3) 可以并发写不同 project 的 state, 但 curator (1/4/5) 必须 serialize agent YAML 写入.

---

## §3 Lineage Relationships (Agent YAML ↔ SKILL.md Traceability Chain)

### §3.0 Elaboration 声明

本节是 **lineage 关系维度的完整规范**. ARCHITECTURE §6.1 给了 transform procedure 的 5 步, §6.2 给了 drift detection curator 侧 check. 本节把这些拼成 **完整 forward chain + backward chain + drift detection + 5 个不变式**, 形成 auditor-friendly traceability 规范.

### §3.1 Lineage Field Schema 引用 (Phase 45 — CITE ONLY)

**Phase 45 agents-schema.yaml `lineage` block (do NOT redefine):**

```yaml
lineage:
  derived_from_skill_id: string, required
    # format: {repo}/{path} (e.g. "kais-hermes-skills/skills/movie-experts/screenplay")
  derived_from_repo: string, required
    # enum: [kais-hermes-skills] (v10.0-v12+ single source)
    # future: additional source repos allowed if Kai designates them
  transform_date: string, required
    # ISO 8601 date (e.g. "2026-07-15")
  skill_sha256: string, required
    # 64-char hex string = sha256 of source SKILL.md content at transform time
    # encoding="utf-8" per CLAUDE.md PLW1514 rule
```

**Note:** Phase 45 可能加了额外 sub-fields (e.g. `transform_tool_version` 用于 v12+ CLI 版本追踪). 以 Phase 45 schema 为准. 本 doc 不重定义.

### §3.2 Forward Chain (SKILL.md → Agent YAML)

**Procedure (ARCHITECTURE §6.1 verbatim + elaboration):**

1. **Read source SKILL.md** from `kais-hermes-skills` repo at operator's checkout path (e.g. `/data/workspace/kais-hermes-skills/skills/movie-experts/screenplay/SKILL.md`).
2. **Compute `skill_sha256`** = `hashlib.sha256(skill_md_content.encode("utf-8")).hexdigest()`. encoding 显式 (per CLAUDE.md PLW1514 rule — Windows 默认 cp1252 会 silent corrupt non-ASCII).
3. **Generate agent YAML** per Phase 45 SC#4 15-expert transform mapping (5-field mapping table — details in 04-MIGRATION-PATH, **不在本 doc**).
4. **Write to** `~/.hermes/agents/{name}.agent.yaml`.
5. **Record lineage block** (per §3.1 schema).

**v10.0 / v11.0 PoC:** Manual —— operator runs steps by hand, ~5-10 minutes per agent. Total: 15 agents × ~7 min = ~2 hours one-time work at v11.0 PoC kickoff.

**v12+:** Scripted via `hermes agent transform --from skill --to agent --name <name>` CLI (ARCHITECTURE §6.1 closing + §6.4 row 1 v12+ column).

**Frequency:**

- Once at v11.0 PoC kickoff per agent (one-time bulk).
- Re-transform only when curator flags drift (§3.4).
- Re-transform 是 **manual** even in v12+ —— CLI 只是 automates steps 1-5, 仍 operator-initiated, 仍 respects operator's persona hand-tuning (ARCHITECTURE §8.2 anti-pattern: auto-re-transform forbidden).

### §3.3 Backward Chain (Agent YAML → SKILL.md)

**Use case:** Auditor (Kai 或 future contributor) 问 "这个 agent 的 persona 来自哪个 SKILL? 源内容在 transform time 是什么? 源是否变过?"

**Resolution chain:**

1. Read `~/.hermes/agents/{name}.agent.yaml` `lineage.derived_from_skill_id` (e.g. `kais-hermes-skills/skills/movie-experts/screenplay`).
2. Resolve source repo path: operator's `kais-hermes-skills` checkout (typically `/data/workspace/kais-hermes-skills/` per MEMORY.md context).
3. Read current SKILL.md content at `{checkout_path}/{derived_from_skill_id_without_repo_prefix}/SKILL.md`.
4. Compute current sha256 (`hashlib.sha256(content.encode("utf-8")).hexdigest()`).
5. Compare to `lineage.skill_sha256`:
   - **Match:** source unchanged since transform. agent YAML reflects current SKILL.
   - **Mismatch:** drift detected (§3.4).

**Two-anchor design rationale:**

- `derived_from_skill_id` (**path anchor**) —— 不够, 因为 repo 可能 moved / renamed.
- `skill_sha256` (**content anchor**) —— 不够, 因为 SKILL.md 可能 legitimately edited (operator-approved kais-hermes-skills PR).
- **Two anchors together** provide robust traceability: path 给 resolution 起点, content sha256 给 drift 信号.

**Anti-pattern (§3.5 invariant L6 reinforcement):** 单靠 `derived_from_skill_id` 路径不验证内容 —— typo 或 malicious actor 可以 spoof 路径. content sha256 是 cryptographic guard.

### §3.4 Drift Detection Chain

**Cite ARCHITECTURE §6.2 `_detect_skill_agent_drift()` function skeleton verbatim:**

```python
def _detect_skill_agent_drift() -> List[Dict[str, Any]]:
    """Detect SKILL.md changes since last transform.

    For each ~/.hermes/agents/*.agent.yaml with lineage.derived_from_skill_id:
      1. Resolve source SKILL.md path in the recorded repo.
      2. Compute current sha256.
      3. Compare to lineage.skill_sha256.
      4. If mismatch: append to drift report.

    Returns list of {agent_name, skill_path, old_sha, new_sha, drift_age_days}.
    """
```

**Drift triggers ADVISORY, NOT auto-re-transform:** operator 决定是否 re-run transform with fresh persona rewrite. 这 preserves **operator ownership of persona** (hand-tuned beyond initial transform —— operator 可能在 persona 里加了 "cite Volvo S1-1 case" 这种 v9.0 lesson).

**Drift advisory delivery:**

- **v11.0 PoC:** curator log (`~/.hermes/logs/agent.log` + `errors.log` per CLAUDE.md logging conventions).
- **v12+:** dashboard notification (Agents tab per ARCHITECTURE §6.4 row 1 v12+ column).

**Drift frequency expectation:** Low —— kais-hermes-skills SKILLs 是 stable post-v9.0 ship. Major SKILL edits trigger vN+ milestone work (e.g. v5.0 kais-movie-agent V8.6 sync), 不是 ambient drift.

**Anti-pattern (ARCHITECTURE §8.2):** Auto-re-transform on drift. Explicitly forbidden —— 会 overwrite operator's hand-tuned persona, 违反 决策 5 (α form is operator-owned identity) + PITFALLS §P1 mitigation 4 (persona drift defense).

### §3.5 Lineage 不变式声明 (L1-L5)

5 个 explicit invariants —— 每个 with rationale + source citation:

#### L1: Every `~/.hermes/agents/*.agent.yaml` MUST have non-empty `lineage` block

- **Rationale:** Traceability 是 load-bearing for audit + drift detection. 没有 lineage 的 YAML 是 orphan, 无法追溯 source.
- **Source:** Phase 45 agents-schema.yaml (`lineage` required field).
- **Enforcement:** Schema validation at agent_registry load time.

#### L2: `lineage.derived_from_repo` MUST be `kais-hermes-skills` for v10.0-v12+ agents

- **Rationale:** Single transform source repo (per ARCHITECTURE §6 row 2). 未来: additional source repos allowed if Kai designates them (e.g. 第三方 agent library).
- **Source:** ARCHITECTURE §6.
- **Enforcement:** Schema enum check.

#### L3: `lineage.skill_sha256` MUST match current SKILL.md content OR trigger drift advisory

- **Rationale:** Drift detection invariant. curator 每 `_memory_evolution_phase` pass 跑 `_detect_skill_agent_drift()` check.
- **Source:** ARCHITECTURE §6.2.
- **Enforcement:** Curator periodic check. Mismatch triggers advisory (§3.4), not auto-re-transform.

#### L4: Backport agent YAML → SKILL.md is OUT OF SCOPE forever

- **Rationale:** Agents 和 skills 是 different layers per PROJECT.md paradigm shift declaration (skills 是 Hermes-side prompt injection; agents 是 operator-owned identity with per-agent memory + curator-driven evolution).
- **Source:** ARCHITECTURE §6.3 closing statement verbatim "explicitly out of scope for v10.0 (and likely forever)".
- **Enforcement:** 设计层面 —— 没有 code path 实现 backport. 如果未来需要, 是新 milestone 决策, 不是本 doc 范围.

#### L5: Agent YAML `persona` field is operator-owned; curator CANNOT modify

- **Rationale:** `persona_sha256` invariant (Phase 45 SC#1 + PITFALLS §P1 mitigation 4: persona drift defense). Curator 只能修改 `evolution_log` + `fitness_score`.
- **Source:** 决策 5 (α form is operator-owned identity) + Phase 45 SC#1 + PITFALLS §P1 mitigation 4.
- **Enforcement:** §2.4 write authority matrix row 1 + curator code path explicit field whitelist (`evolution_log` / `fitness_score` / `last_fitness_battery_run_at` —— 其他 fields rejected).

