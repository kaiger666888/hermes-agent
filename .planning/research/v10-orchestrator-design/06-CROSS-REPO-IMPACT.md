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

#### L6: Two-anchor lineage verification (path + content sha256)

- **Rationale:** Single path anchor (e.g. `derived_from_skill_id` only) 可被 typo 或 malicious actor spoof. Single content anchor (`skill_sha256` only) breaks on legitimate SKILL.md edit. **Two anchors together** provide robust traceability —— path 给 resolution 起点, sha256 给 cryptographic verification.
- **Source:** §3.3 two-anchor design + Phase 45 lineage block sub-fields.
- **Enforcement:** §3.3 backward chain step 5 (compute current sha256, compare to `lineage.skill_sha256`).
- **Audit check (Phase 51 VALIDATE lint):** For each `~/.hermes/agents/*.agent.yaml`, run backward chain; report any drift.

### §3.6 Lineage Worked Example (kais-movie-pipeline Cinematographer)

To make the traceability chain concrete, here is a worked example using the cinematographer agent (one of the 15 movie-experts transformed in v11.0 PoC):

**Source (Location 2 — kais-hermes-skills repo):**

```
/data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/SKILL.md
```

Content (excerpt, ~250 lines total):

```yaml
---
name: cinematographer
description: 电影摄影指导专家...
metadata:
  hermes:
    tags: [movie, cinematography, ...]
    related_skills: [screenplay, drawer, ...]
    expert_id: cinematographer
    metrics: [shot_grammar, vertical_screen_framing, ...]
---
# Cinematographer Expert (摄影指导)
## When to use this skill
...
```

**Forward chain (transform procedure, ARCHITECTURE §6.1, §3.2 above):**

1. Operator reads SKILL.md → 250 lines content.
2. `skill_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()` → e.g. `"f3a2b1c8..."` (64 hex chars).
3. Generate `~/.hermes/agents/cinematographer.agent.yaml` (5-field transform per 04-MIGRATION-PATH).
4. Record lineage:

```yaml
lineage:
  derived_from_skill_id: kais-hermes-skills/skills/movie-experts/cinematographer
  derived_from_repo: kais-hermes-skills
  transform_date: "2026-07-15"
  skill_sha256: "f3a2b1c8e9d7b6a5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1"
```

**Backward chain (audit, §3.3 above):**

1. Auditor reads `lineage.derived_from_skill_id` → `kais-hermes-skills/skills/movie-experts/cinematographer`.
2. Resolves source path: `/data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/SKILL.md`.
3. Reads current SKILL.md content.
4. Computes current sha256 → e.g. `"f3a2b1c8..."` (matches L3 invariant).
5. **Result:** No drift. agent YAML reflects current SKILL.

**Drift scenario:**

- Operator pushes kais-hermes-skills PR adding new refs to cinematographer SKILL.md.
- SKILL.md content changes → current sha256 = `"e5d4c3b2..."` (differs from `lineage.skill_sha256` = `"f3a2b1c8..."`).
- Curator's next `_memory_evolution_phase` pass runs `_detect_skill_agent_drift()` → detects mismatch → appends to drift report.
- **Drift advisory** logged (§3.4) — operator decides whether to re-run transform with fresh persona rewrite (preserve hand-tuned additions to persona).



---

## §4 Option B vs Physical Partition Migration Trigger Conditions (SC#3 Deep-Dive, OQ-12 + CC-4 Resolution)

### §4.0 Elaboration 声明 (SC#3 Framing)

本节是 **ROADMAP SC#3 的完整论证** + **SUMMARY OQ-12 + CC-4 的 resolution**.

§1.5.2 已声明 citation anchors. §4 给完整论证 + **net-new 的迁移触发条件 heuristics**.

**Problem framing:**

- **ARCHITECTURE §3.2** 推荐 Option B (mem0 单 backend + `agent_id` filter) 用于 v11.0 PoC.
- **PITFALLS §P3 mitigation 1** 推荐 Physical Partition (每 agent 一 workspace) 用于 v12+ 规模.
- **但两者都没给具体触发条件** —— "什么时候切换?" 是 open question.

**本节的贡献 (net-new):** §4.4 给 **3 类阈值** (规模 / latency / 安全) 共 8 个 numeric triggers (A1-A3 + B1-B3 + C1-C2). 这是本 doc 唯一的 net-new 设计内容 (其余都是 cite + elaborate). **CC-4 显式要求** "这个生命周期决策要在 `06-CROSS-REPO-IMPACT.md` 显式记录, 避免 v12 实施者重新讨论一遍" —— 本节完成.

### §4.1 Option B 完整定义

**Cite ARCHITECTURE §3.2 verbatim:**

> Option B — `agent_id` field as scoping key (RECOMMENDED). mem0 single backend, per-call `agent_id` filter routes memory. Lightest infrastructure, no per-agent collection management.

**Implementation:**

- Additive `_scoped_agent_id` extension to existing mem0 plugin per ARCHITECTURE §3.3 code skeleton:
  - `initialize(session_id, **kwargs)` accepts optional `agent_scope: str | None` kwarg.
  - `_read_filters()` returns `{"user_id": self._user_id, "agent_id": self._scoped_agent_id}` when scoped (currently only returns `{"user_id"}`).
  - `handle_tool_call(tool_name, args, **kwargs)` accepts optional `agent_scope` from dispatcher; uses `contextvars` (per SUMMARY "Gaps to Address" + `agent/tool_executor.py` 已用 contextvars).
- Every `mem0.add()` and `mem0.search()` call routes through `contextvars` set by dispatcher (per Phase 45 memory-record-schema `agent_id` required field).

**Reuses:** v7.0 ship of `plugins/memory/mem0/__init__.py` (375 lines) —— additive, not rewrite. MEMORY.md `kais-movie-agent-v5-hermes-native-migration.md` 已确认 v7.0 ship status.

**Pros:**

- **Lightest infrastructure** —— 单 mem0 backend, 无 per-agent ops (monitoring / backup / gc × N).
- **API unchanged** from existing mem0 surface —— existing v7.0 call sites 不需修改.
- **No migration cost at v11.0 PoC kickoff** —— day-1 就可用.

**Cons:**

- **HNSW global-graph + post-filter strategy hits latency wall at scale** (per PITFALLS §P3 — per-agent scoping 是 post-retrieval filter, scanning 50-100× more nodes than necessary).
- **Shared workspace means imperfect filter = bleed-through risk** (per PITFALLS §P12 — cross-agent contamination via shared mem0 workspace).

### §4.2 Physical Partition 完整定义

**Cite PITFALLS §P3 mitigation 1 verbatim:**

> Physical partitioning over logical filtering. Don't rely on mem0's `agent_id` filter alone. Use one mem0 project/workspace per agent (mem0 supports workspace-level isolation). The filter `user_id` then narrows within the agent's workspace. This requires 18 mem0 workspaces but gives O(per-agent-records) retrieval instead of O(all-records) post-filter.

**Implementation:**

- Each `~/.hermes/agents/{name}.agent.yaml` mapped to one mem0 collection (or one mem0 instance —— deployment-dependent, v12+ design decision).
- `agent_id` field becomes workspace selector instead of filter key.
- Per-agent memory record count bounded by `memory.max_records: 500` per agent (PITFALLS §P3 mitigation 3 + Phase 45 SC#2).

**Pros:**

- **Stable latency under scale** —— no HNSW global-graph post-filter; O(per-agent-records) retrieval.
- **No cross-agent bleed-through** —— PITFALLS §P12 risk 消除 at infrastructure level (workspace isolation).
- **Per-agent backup / restore granularity** —— operational benefit at v12+ scale.

**Cons:**

- **N backends to operate** —— monitoring / backup / gc × N (N = agent count). v12+ 30+ agents 意味着 30+ mem0 workspaces.
- **Heavier initial setup** —— provisioning automation, per-agent configuration management.
- **Cross-agent queries require federated search** —— e.g. "what did screenplay and cinematographer both learn from Volvo case?" 需要 federated query across multiple workspaces (mem0 Platform API 不原生支持 federated).

### §4.3 API 不变性声明 (API Surface Invariance)

**Cite SUMMARY CC-4 + STACK §3.2 Tool 3 verbatim:**

> STACK §3.2 Tool 3: `get_agent_memory(name, topic, ...)` —— takes `name` (agentId) as required parameter. Option B interprets `name` as **filter key on single backend**; Physical Partition interprets `name` as **workspace selector**. **API surface is identical.**

**Lock-in implication:**

- **v11.0 PoC implementer writes agent YAML + dispatcher + MCP tools once.**
- **v12+ migration touches ONLY mem0 backend deployment + `_scoped_agent_id` extension internals.** Zero upstream code change.
- **决策 6 (per-agent memory) 的 API contract 不变** —— agent YAML schema / dispatcher routing / 7 MCP tool contract / round-table protocol 都 **unaffected** by backend switch.

**Test surface implication:**

- v11.0 PoC integration tests (mock mem0 backend) **remain valid for v12+ Physical Partition** (mock interface unchanged).
- v11.0 PoC 的 `agent_id` filter enforcement audit test (§4.5) 在 v12+ 变成 workspace isolation test —— 但 test 抽象层不变.

**决策 7 (分层 CC 角色) reinforcement:** Hermes 控 API contract (schema / dispatch / state), CC 通过 MCP tool 间接交互 —— backend switch 在 Hermes 层完成, CC 完全无感知.

### §4.4 迁移触发条件 Heuristics (Net-New Contribution — THREE THRESHOLD CLASSES)

**这是本 doc 的 net-new contribution.** 三类阈值, 每类给具体数值 + 监控点 + 触发动作.

#### Class A — 规模阈值 (Scale Threshold)

- **A1: Agent count ≥ 30.**
  - **Rationale:** v11.0 PoC = 15 agents (safe under Option B). v12+ projected 30+ agents (per kais-movie-pipeline + 未来 skill-to-agent transforms). HNSW global graph complexity grows superlinearly with agent count (per PITFALLS §P3 §"Mechanism").
  - **Monitoring point:** `len(agent_registry.list_agents())` at Hermes startup.
  - **Trigger action:** agent count crossing 30 = **advisory** (log warning + dashboard notification); crossing 50 = **mandatory migration evaluation** (open v12+ design milestone).

- **A2: Project count ≥ 10.**
  - **Rationale:** v11.0 PoC = 1-2 projects (kais-movie-pipeline vertical slice + 1 infra). v12+ projected 10+ active projects. Per-project memory namespace multiplicative with agent count.
  - **Monitoring point:** count distinct `project_slug` in `.runtime/*/round_tables/*.json` over last 30 days.
  - **Trigger action:** project count crossing 10 = **advisory**.

- **A3: Memory record total ≥ 5000.**
  - **Rationale:** v11.0 PoC budget = 15 agents × 500 records = 7500 max (per PITFALLS §P3 mitigation 3 + Phase 45 SC#2 `memory.max_records: 500`). HNSW graph degradation 起始 around 5K records with post-filter.
  - **Monitoring point:** `mem0.get_all()` total count, sampled weekly.
  - **Trigger action:** total records crossing 5000 = **advisory**; crossing 10000 = **mandatory**.

#### Class B — Latency 阈值 (Latency Threshold)

- **B1: p95 retrieval latency > 500ms.**
  - **Rationale:** Per STACK §11.4 + ARCHITECTURE §3.2 + Phase 50 SC#3 PoC acceptance criterion. v11.0 PoC week-1 benchmark establishes baseline.
  - **Monitoring point:** `_latency_ms` field on every memory retrieval log entry (per PITFALLS §P3 mitigation 4). Stats CLI exposes p50/p95/p99 per agent.
  - **Trigger action:** rolling 7-day p95 > 500ms = **mandatory migration evaluation**.

- **B2: p99 retrieval latency > 2000ms.**
  - **Rationale:** Tail latency 指示 HNSW graph degradation under load.
  - **Monitoring point:** same as B1.
  - **Trigger action:** rolling 7-day p99 > 2000ms = **mandatory**.

- **B3: Retrieval failure rate > 1%.**
  - **Rationale:** mem0 timeout / OOM under scale. Circuit breaker (`_BREAKER_THRESHOLD = 5`, `_BREAKER_COOLDOWN_SECS = 120` per ARCHITECTURE §3.1 + PITFALLS §P3 §"Why it happens") trips.
  - **Monitoring point:** failure count / total call count, 24-hour rolling window.
  - **Trigger action:** any 24-hour window with > 1% retrieval failure = **immediate incident** + migration evaluation.

#### Class C — 安全阈值 (Safety Threshold)

- **C1: Cross-agent contamination detected (PITFALLS §P12).**
  - **Rationale:** Any confirmed case of agent A's memory record appearing in agent B's retrieval results. PITFALLS §P12 mitigation 3 specifies periodic invariant test `_check_workspace_isolation(agent_A, agent_B)`.
  - **Monitoring point:** periodic invariant test (daily) + on-demand audit.
  - **Trigger action:** any confirmed contamination = **immediate migration to Physical Partition** (eliminates bleed at infrastructure level).

- **C2: Filter bypass vulnerability.**
  - **Rationale:** Any code path that calls `mem0.search()` without setting `agent_id` filter (per ARCHITECTURE §3.3 invariants + PITFALLS §P12 mitigation 2 "agent_id is REQUIRED on every memory write and every retrieve").
  - **Monitoring point:** code audit (CI lint) + runtime invariant check.
  - **Trigger action:** must fix in current release; if recurring (3+ bypass bugs in 6 months), migrate to Physical Partition (**defense in depth** —— 物理隔离 eliminates filter as dependency).

- **C3: Privacy audit failure.**
  - **Rationale:** Any external audit finding per-agent memory isolation insufficient (per PITFALLS §P10 privacy + Phase 45 `confidentiality` field).
  - **Monitoring point:** external audit (frequency per Kai's compliance posture).
  - **Trigger action:** case-by-case; Physical Partition 是 available mitigation option.

**Trigger presentation format (Phase 51 VALIDATE lint should verify):** each trigger as `{ID, threshold, monitoring point, trigger action, source citation}`. 见上表.

**Important note on trigger thresholds:** 这 8 个 numeric thresholds 是 **STARTING-POINT**, 不是 gospel. §7.2 偏差分析 explicit 声明: 这些 thresholds 是 revisable in Phase 51 audit based on v11.0 PoC 实测数据. v11.0 PoC implementer 不应该 because "agent count 已达 30" 就 panic-migrate —— 应该 run §4.5 acceptance benchmark 看 latency 是否真的 degrade.

#### §4.4.1 Threshold Rationale Deep-Dive (Why these specific numbers?)

Each numeric threshold in §4.4 has a derivation rationale grounded in industry data + Hermes-specific scaling projections:

**A1 (agent count ≥30):** PITFALLS §P3 §"Mechanism" cites HNSW graph degradation as superlinear in scoped-subset count. mem0 reference deployments are per-user (chatbot memory: 1 user × thousands of records). The 18-agent × 100-project matrix from PITFALLS §P3 is the documented failure case (post-filter scans 50-100× more nodes than necessary). v11.0 PoC's 15 agents is comfortably below; v12+ projects 30+ agents (kais-movie-pipeline + future skill-to-agent transforms + cross-domain agents like research/coding). 30 is the inflection point where superlinear degradation becomes measurable; 50 is where it becomes user-perceptible (p95 doubling).

**A2 (project count ≥10):** Memory namespace matrix = agents × projects. v11.0 PoC = 15 × 1 = 15 namespaces; v12+ projects 30 × 10 = 300 namespaces. mem0's `agent_id` + `user_id` filter combinations grow quadratically with cross-product. 10 projects is conservative — advisory only.

**A3 (memory records ≥5000):** PITFALLS §P3 mitigation 3 + Phase 45 SC#2 set per-agent cap at `memory.max_records: 500`. 15 agents × 500 records = 7500 max in v11.0 PoC. HNSW global graph index size scales with total records; post-filter scans degrade at ~5K records. The 5000 advisory fires before the 7500 ceiling — gives operator time to plan migration.

**B1 (p95 >500ms):** STACK §11.4 + Phase 50 SC#3 PoC acceptance criterion. 500ms is the upper bound for "interactive" latency (per Nielsen Norman Group UX research). Above 500ms, the round-table turn cadence feels sluggish to operators monitoring in dashboard.

**B2 (p99 >2000ms):** Tail latency. Even if p95 is healthy, p99 spikes indicate HNSW graph traversal worst-case (e.g. cold cache + filter mismatch + re-rank). 2 seconds is "user thinks something is broken" threshold.

**B3 (failure rate >1%):** mem0 timeout / circuit breaker trip. `_BREAKER_THRESHOLD = 5` (5 failures trigger cooldown) per ARCHITECTURE §3.1. At 1% failure rate over 24h with normal round-table cadence, circuit breaker fires multiple times per day → "memory unavailable" silent fallback → agents degrade to static refs only.

**C1 (any cross-agent contamination):** Zero-tolerance. PITFALLS §P12 mitigation 3 specifies periodic invariant test `_check_workspace_isolation(agent_A, agent_B)`. Any failure means filter routing has a bug; Physical Partition eliminates the dependency entirely.

**C2 (filter bypass):** Defense in depth. If filter enforcement fails repeatedly (3+ bypass bugs in 6 months), the filter-based approach is showing systemic fragility — Physical Partition's hardware-level isolation is more robust.

**C3 (privacy audit):** External compliance trigger. Phase 45 `confidentiality` field + PITFALLS §P10 privacy. If an external audit (e.g. GDPR, SOC 2) finds per-agent memory isolation insufficient, Physical Partition is the available mitigation.

**Cross-threshold interaction:** Class A thresholds are predictive (scale projection); Class B thresholds are measured (actual performance); Class C thresholds are reactive (confirmed incidents). An advisory Class A trigger (e.g. agent count ≥30) without corresponding Class B degradation (p95 still <500ms) suggests the system has more headroom than projected — proceed with monitoring, no migration needed. A mandatory Class B trigger (p95 >500ms sustained) at low Class A scale (only 20 agents) suggests either (a) the thresholds were too optimistic or (b) mem0 backend has a pathological workload — investigate root cause before migration.



### §4.5 v11.0 PoC 验收条件 (Acceptance Criteria)

**Latency benchmark (Phase 50 SC#3):**

- p95 < 500ms for `get_agent_memory` calls under realistic load (15 agents × 500 records × 1 project).
- **Run during v11.0 PoC week-1**, before any round-table execution. Establishes baseline for Class B threshold monitoring.

**Filter enforcement audit:**

- All `mem0.search()` call sites in hermes-agent code pass through `_scoped_agent_id` `contextvars` (per ARCHITECTURE §3.3).
- No bypass paths (CI lint + manual code review).
- Periodic invariant test `_check_workspace_isolation(agent_A, agent_B)` runs daily, asserts zero cross-agent results.

**Pass = proceed with Option B; Fail = trigger Physical Partition migration BEFORE round-table execution.**

**Cite:** STACK §11.4 (latency SLO) + ARCHITECTURE §3.2 (Option B recommendation) + Phase 50 SC#3 (PoC acceptance criterion source) as acceptance criterion source.

### §4.6 迁移路径 (Option B → Physical Partition)

One-way migration. 6 steps:

- **Step 1 — Export:** For each agent, `mem0.get_all(agent_id=X)` → JSONL dump to `~/.hermes/agents/.runtime/_migration/{agent_name}.jsonl`. encoding="utf-8" per CLAUDE.md PLW1514.
- **Step 2 — Provision:** Create per-agent mem0 workspace (collection or instance, v12+ deployment decision). Provision via `mem0` CLI or API.
- **Step 3 — Import:** Per-agent JSONL → new workspace. Verify record count + spot-check content integrity (sha256 of record content pre/post migration match).
- **Step 4 — Switch:** Update `_scoped_agent_id` extension (ARCHITECTURE §3.3) to route by **workspace selection** instead of filter. This is the only code change —— dispatcher / agent YAML / MCP tool contract 全部不变 (per §4.3 API 不变性).
- **Step 5 — Verify:** Re-run v11.0 PoC acceptance battery (§4.5) against new backend topology. Latency benchmark + filter audit (现在叫 workspace isolation audit) + cross-agent contamination check.
- **Step 6 — Decommission old backend:** After 30-day shadow period (read-only fallback for rollback), archive + delete single backend.

**Estimated effort:** 1-2 person-weeks (per Phase 50 SC#4 budget).

**Caveat (one-way):** Migration is **ONE-WAY**. Once `_scoped_agent_id` extension switches to workspace selection, downgrade back to Option B requires reverse migration (not recommended —— re-introduces P3 + P12 risk without offsetting benefit).

### §4.7 P3 + P12 风险评估更新

- **P3 (Pitfall 3: Scoped Retrieval Performance Collapse):**
  - **v11.0 PoC scale** (15 agent × 1 project × ≤500 records/agent): **LOW** risk. HNSW global graph comfortably handles this scale.
  - **v12+ scale** (30+ agent × 10+ project × ≤500 records/agent = 150K+ records): **HIGH** risk. Triggers Class A thresholds (A1/A2/A3).
  - **Resolution:** §4.4 Class A scale triggers + §4.6 migration path.

- **P12 (Pitfall 12: Cross-Agent Memory Contamination via Shared mem0 Workspace):**
  - **v11.0 PoC:** **LOW** risk IF filter enforcement audit passes (§4.5).
  - **v12+:** **MEDIUM** risk due to scale-induced filter complexity (more call sites, more chances of bypass). Physical Partition eliminates entirely.
  - **Resolution:** §4.4 Class C safety triggers (C1/C2) + §4.6 migration path.

**Cite:** PITFALLS §P3 + §P12 + Phase 51 VALIDATE risk register reconciliation (will verify field-level mitigation coverage).

### §4.8 A2A 扩展位声明 (Expansion Position Only)

**Cite 03-COMPARISON-VS-KIMI-MCP-SHIM.md §4.5 verbatim:**

> v10.0 single-vendor internal, 不需要 A2A (Agent-to-Agent protocol); v12+ 跨厂商协作时 A2A 是正确协议 (FEATURES §10 B7.4 — Microsoft 三层协议分层: internal → platform-native; tool → MCP; cross-platform → A2A).

**本节只声明扩展位:**

- `~/.hermes/agents/*.agent.yaml` 的 `agent_card` 子段 (Phase 45 已收, per FEATURES §8 B8.1 borrowable "Agent Card exposition") 是 A2A Agent Card 的前身.
- v12+ 跨厂商协作时 expose 为 A2A-compatible endpoint.
- 本 doc **不展开 A2A 协议** (out of scope for v10.0).

**Implication for 3-location sync:** A2A exposition 影响 Location 1 (hermes-agent repo) —— v12+ dashboard Agents tab 需要 expose agent_card over HTTP endpoint for cross-vendor discovery. Location 2 (kais-hermes-skills) + Location 3 (`~/.hermes/agents/`) 不变.

---

## §5 Project Slug Stability Policy (SC#5 Deep-Dive, OQ-6 Resolution)

### §5.0 Elaboration 声明

本节是 **ROADMAP SC#5 的完整论证** + **SUMMARY OQ-6 的 resolution**.

ARCHITECTURE §5.1 + §7.4 定义了 `project_slug` 的 derivation (`{repo_basename}:{git_toplevel_abspath_sha8}`). ARCHITECTURE §10.6 把 slug 稳定性列为 open question:

> **OQ-6:** project slug 重命名稳定性. 倾向性结论: 接受 breakage (已知限制), long-term 用 `.hermes/project.id` stable ID. 在 `06-CROSS-REPO-IMPACT.md` 解决.

本节给出 **短期 (接受 breakage + manual recovery) + 长期 (`.hermes/project.id` stable ID)** 双轨策略 + adoption roadmap, 解决 OQ-6.

### §5.1 project_slug 当前 Derivation 引用

**Cite ARCHITECTURE §5.1 + §7.4 verbatim:**

> `project_slug` derivation: `{repo_basename}:{git_toplevel_abspath_sha8}` (e.g. `hermes-agent:a1b2c3d4` for `/data/workspace/hermes-agent/`). Disambiguates two repos with same name on different machines.

**Pattern (ARCHITECTURE §7.4):** Project Slug for State Isolation. project_slug derived from `repo_basename` + `git_toplevel_abspath_sha8`. Disambiguates two repos with same name on different machines.

**Design intent:**

- Disambiguate same-name repos on different machines (e.g. Kai's laptop vs desktop both have `/data/workspace/hermes-agent/` clones — different abspath → different sha8 → different slug).
- Deterministic —— no operator action required to compute slug.
- Collision-resistant —— sha8 给 16M namespace.
- Recoverable from filesystem inspection.

**示例 derivation:**

```
repo_basename = "hermes-agent"
git_toplevel_abspath = "/data/workspace/hermes-agent/"
git_toplevel_abspath_sha8 = sha8("/data/workspace/hermes-agent/") = "a1b2c3d4"  # 取 sha256 abspath 的前 8 chars
project_slug = "hermes-agent:a1b2c3d4"
```

### §5.2 短期 Breakage 接受 (Short-Term Policy — LOCKED for v11.0 PoC)

**Cite SUMMARY OQ-6 verbatim:**

> 接受 breakage (已知限制), long-term 用 `.hermes/project.id` stable ID.

**3 个 breakage 场景:**

#### Scenario 1 — Repo rename

Operator renames `hermes-agent` to `hermes-agent-v11`. `repo_basename` changes (`hermes-agent` → `hermes-agent-v11`) → slug changes (`hermes-agent:a1b2c3d4` → `hermes-agent-v11:a1b2c3d4`) → 已有的 `~/.hermes/agents/.runtime/hermes-agent:a1b2c3d4/round_tables/*.json` orphaned.

**Recovery (v11.0 PoC manual):**

```bash
mv ~/.hermes/agents/.runtime/hermes-agent:a1b2c3d4/ \
   ~/.hermes/agents/.runtime/hermes-agent-v11:a1b2c3d4/
```

One-line shell command. Safe because round-table state is append-only, no concurrent writes during rename (Hermes 必须停止 round table 才能 rename).

#### Scenario 2 — Checkout move

Operator moves checkout from `/data/workspace/hermes-agent/` to `/home/kai/repos/hermes-agent/`. `git_toplevel_abspath_sha8` changes → slug changes → orphaned.

**Recovery (v11.0 PoC manual):**

```bash
# Compute new slug
new_slug=$(hermes project slug --path /home/kai/repos/hermes-agent/)
# Move state
mv ~/.hermes/agents/.runtime/hermes-agent:a1b2c3d4/ \
   ~/.hermes/agents/.runtime/${new_slug}/
```

#### Scenario 3 — Clone to second machine

Operator clones repo to laptop. `git_toplevel_abspath_sha8` likely differs (different absolute path on different machine) → different slug → laptop creates fresh `~/.hermes/agents/.runtime/{laptop_slug}/round_tables/` (no inheritance from desktop).

**Recovery:** None needed. Each machine maintains independent round-table history by design. Round-table state is per-machine-per-project —— this is correct behavior, not breakage.

#### 短期 breakage acceptance rationale

- **v11.0 PoC scope is single-machine** (Kai's primary workstation —— per MEMORY.md `hermes-gateway-systemd.md` context).
- Renames + moves 是 infrequent (months apart, 通常 around major version milestones).
- Manual recovery cost is low (one `mv` per event).
- v12+ stable ID mechanism (§5.3) eliminates breakage entirely 但 adds adoption cost —— **not justified for v11.0 PoC scale** (1-2 projects).

### §5.3 长期 Stable ID 机制 (Long-Term Fix — DESIGN for v12+)

**Design:** `.hermes/project.id` file at hermes-agent repo root (gitignored, operator-created).

**Content:** Single line = uuid4 string. e.g. `550e8400-e29b-41d4-a716-446655440000`.

**Lifecycle:**

- Operator runs `hermes project init` (v12+ CLI command) → generates uuid4 → writes `.hermes/project.id`.
- **Two adoption modes (operator's choice):**
  - **Mode A — Machine-local ID (default):** `.hermes/project.id` is gitignored (added to `.gitignore`). ID is per-clone. Each machine maintains independent round-table history. Simple, no shared state.
  - **Mode B — Team-shared ID (opt-in):** Operator commits `.hermes/project.id` to repo. All clones inherit same ID. Round-table history is shareable across machines (requires operator to manually `rsync` `.runtime/{id}/round_tables/` directories, OR a future sync mechanism). **Trade-off:** ID is now public (in git history) —— acceptable for non-adversarial context (kais-hermes-skills + hermes-agent are public-open per MEMORY.md context).

**Routing:**

- Hermes resolves `project_id` from `.hermes/project.id` (if present) at startup.
- Falls back to `project_slug` derivation (§5.1) if `.hermes/project.id` absent.
- Round-table state path uses ID when available: `~/.hermes/agents/.runtime/projects/{project_id}/round_tables/*.json` (new path structure, see §5.4).

### §5.4 Stable ID 落盘路径设计

**New path structure (v12+):**

```
~/.hermes/agents/.runtime/
└── projects/
    └── {project_id}/                      # uuid4, e.g. 550e8400-e29b-41d4-a716-446655440000
        └── round_tables/
            ├── {round_table_id}.json
            └── ...
```

**Backward compatibility (slug → ID symlink bridge):**

Existing `.runtime/{slug}/round_tables/` paths preserved via symlink:

```
~/.hermes/agents/.runtime/{slug}  →  symlink →  ~/.hermes/agents/.runtime/projects/{resolved_project_id}
```

v11.0 PoC code writing to slug path automatically lands in ID path via symlink. No v11.0 PoC code change required.

**Migration (v12+ adoption via `hermes project adopt` CLI):**

- `hermes project adopt` CLI scans `.runtime/{slug}/` directories.
- Prompts operator to confirm project_id mapping (or auto-creates new uuid4 if no `.hermes/project.id` exists yet).
- Creates symlinks.
- One-time, idempotent.

### §5.5 Stable ID Adoption Roadmap

- **v11.0 PoC:** **NOT implemented.** Uses slug-based path directly (ARCHITECTURE §5.1). v11.0 PoC scope (single-machine, single-project) does not justify adoption cost.
- **v12+:** **Implemented when either of:**
  - (a) Operator renames/moves repo for first time AND expresses pain (manual `mv` recovery is annoying), OR
  - (b) Second project is added to round-table workflow (multi-project state isolation becomes load-bearing).
  - Whichever comes first.
- **Migration effort:** ~2-3 person-days (CLI implementation + symlink bridge + migration test).

### §5.6 Dual-Path 兼容性 (Hermes Routing Rules)

- Hermes reads `project_id` **FIRST** (if `.hermes/project.id` exists), falls back to slug derivation.
- **Write path:** Hermes writes to ID-based path when ID present, slug-based path otherwise.
- **Read path:** Hermes reads from whichever path exists (ID preferred, slug fallback for legacy state).
- **Invariant:** Within a single Hermes process lifetime, routing decision is **stable** (no mid-flight switching). Operator must restart Hermes after creating `.hermes/project.id` to adopt ID routing.
- **Symlink bridge ensures v11.0 PoC + v12+ paths converge** to same physical state directory —— no migration of state JSON content required, only directory rename / symlink creation.

---

## §6 Round Table State Per-Project Path (SC#4 Deep-Dive, ARCHITECTURE §5.1 + §5.2 Reference)

### §6.0 Elaboration 声明

本节是 **ROADMAP SC#4 的完整论证**.

ARCHITECTURE §5.1 已给完整 state file layout + `project_slug` derivation. ARCHITECTURE §5.2 已给 cross-project sharing rules (round-table state per-project rationale). Phase 46 已给 round-table-state-schema.yaml `project_slug` required field + atomic / append-only / crash-recoverable invariants.

本节 **引用 + 解释 + 补充 crash recovery 设计** (ARCHITECTURE §5.3 lifecycle sketch 的细节, defer 实施到 v11.0 PoC).

### §6.1 State File 路径规范

**Cite ARCHITECTURE §5.1 verbatim:**

> Layout: `~/.hermes/agents/.runtime/{project_slug}/round_tables/{round_table_id}.json`

**完整路径 example:**

```
~/.hermes/agents/.runtime/hermes-agent:a1b2c3d4/round_tables/rt_20260715_153000_a1b2c3.json
```

**Properties (cite Phase 46 §4 invariants — LOCKED):**

- **Atomic:** Single-file JSON, written via `write_temp + rename` pattern. Rename atomicity guarantees previous state intact on partial write.
- **Append-only turn records:** Existing turns immutable; new turns appended. Mirrors event-sourcing pattern —— transcript is append-only log.
- **Crash-recoverable:** Worst-case partial write leaves previous state intact via rename atomicity. See §6.4 for full failure-mode analysis.

**Schema reference:** Phase 46 `round-table-state-schema.yaml` — fields:

- `round_table_id` (string, required, format `rt_{YYYYMMDD}_{HHMMSS}_{sha6}`)
- `project_slug` (string, required — see §6.2)
- `opened_at` (ISO 8601 timestamp, required)
- `closed_at` (ISO 8601 timestamp, nullable)
- `panel` (list of agent names, required)
- `question` (string, required)
- `turn_order` (list of agent names, required — defines speaking order)
- `max_rounds` (int, required)
- `early_stop_rule` (string, required)
- `current_round` (int, required)
- `current_speaker_index` (int, required)
- `turns[]` (list of turn records, append-only)
- `state` (enum: `in_progress` / `closed` / `abandoned`)
- `final_synthesis` (string, nullable)
- `synthesizer` (string, nullable)
- `early_stop_triggered` (bool)
- `early_stop_reason` (string, nullable)

### §6.2 project_slug 必传规则

**Cite Phase 46 §2 round-table-state-schema.yaml:** `project_slug` is **required** field in `round_table_open` MCP tool call.

**Enforcement:**

- Dispatcher (Hermes runtime) rejects `round_table_open` calls without `project_slug` (Phase 46 §4 invariant — schema validation).
- CC cannot open round table without identifying the project.

**Rationale (cite ARCHITECTURE §5.1):** Round-table state MUST be per-project —— without slug, state file has no path. The `~/.hermes/agents/.runtime/{slug}/round_tables/{round_table_id}.json` path requires slug as directory component.

**Interaction with §5 stable ID:** When `.hermes/project.id` exists (v12+), `project_slug` field in schema can carry either slug (v11.0 PoC) or project_id (v12+) —— schema field is opaque string, routing logic in dispatcher. 见 §5.6 dual-path compatibility.

### §6.3 Per-Project 隔离根因

**Cite ARCHITECTURE §5.2 verbatim:**

> Round table state — **Per-project**. Rationale: each project has its own questions, panel configs, and synthesis outcomes.

**Concrete example:**

kais-movie-pipeline project asks "Should Volvo S1-1 use empty-car establish or grandson reveal?" —— this question + its 4-panelist synthesis (cinematographer / screenplay / hook_retention / theory_critic opinions + final synthesis decision) 是 **meaningless in any other project's context**. Per-project isolation prevents cross-project question contamination.

**Contrast with agent YAML (cross-project):**

- Agent YAML 是 cross-project (operator-owned identity) —— cinematographer 是 cinematographer regardless of project. Persona + tools + memory_scope 都是 stable identity.
- But cinematographer's opinion on a **specific question** in a **specific project's round table** 是 per-project. This is exactly the round-table state isolation boundary.

**Round-table turn snapshots capture agent `fitness_score` at turn time** (per ARCHITECTURE §5.2 closing paragraph), so transcript is reproducible even if agent's current score drifts mid-round-table. Dispatcher writes snapshot, not reference.

### §6.4 Crash Recovery 设计

**Cite ARCHITECTURE §5.3 lifecycle sketch + Phase 46 §4 invariants.**

**3 个 failure modes:**

#### (a) CC crash mid-turn

- Round-table state JSON has `state: "in_progress"`, `current_round: N`, `current_speaker_index: K`.
- Hermes dispatcher detects CC process exit via tmux session end (per 决策 1 T6 协议: tmux dispatch).
- State file remains on disk —— atomic write guarantees no corruption.
- **Recovery:** Next `round_table_open` for same `project_slug` + same `round_table_id` resumes from last committed turn (turn at `current_speaker_index - 1`). Operator can also manually inspect state file via `hermes round-table show --id {round_table_id}`.

#### (b) Hermes crash mid-turn

- Same recovery as (a) —— state file on disk is authoritative.
- Hermes restart reads state file, resumes round table from last committed turn.
- Dispatcher's startup routine scans `.runtime/{slug}/round_tables/*.json` for `state: "in_progress"` entries, surfaces them in dashboard (v12+ dashboard Agents tab) or CLI (`hermes round-table list --state in_progress`).

#### (c) Disk full / write failure

- `write_temp + rename` atomicity ensures previous state intact.
- Dispatcher returns error to CC (via MCP tool response); CC decides retry or abort.
- If CC retries, dispatcher re-attempts write; if disk space freed, write succeeds, state advances normally.
- If CC aborts, dispatcher marks state as `state: "abandoned"` in next gc pass (§6.4 GC pass below).

**GC pass (deferred to v11.0 PoC — NOT implemented in v10.0):**

- Periodic scan of `.runtime/{slug}/round_tables/*.json` for state files with `state: "in_progress"` + `opened_at` older than threshold (e.g. 24h).
- Mark as `state: "abandoned"`, archive to `.runtime/{slug}/round_tables/_archived/`.
- Threshold configurable via `cli-config.yaml` (default 24h).
- **Not implemented in v10.0** (design only). v11.0 PoC implementation.

### §6.5 跨 Project 引用 Forbidden 声明

**Invariant (cite ARCHITECTURE §5.2):** Round-table state JSON for project A **MUST NOT** reference project B's round-table state, agent fitness snapshots, or memory records directly.

**Indirect reference allowed:**

- Round-table state JSON references **agent names** (e.g. `panel: ["screenplay", "cinematographer"]`).
- Agent YAMLs 是 cross-project (operator-owned) —— so the **same agent** participates in multiple projects' round tables.
- But the state JSON itself contains only **that project's** turn records + cited memory snapshot at turn time.

**Enforcement:**

- Phase 46 `round-table-state-schema.yaml` does NOT have a `cross_project_references` field.
- Dispatcher validates on every `submit_round_table_result` call —— rejects any state JSON with cross-project reference fields.
- lint script in Phase 51 VALIDATE will cross-check schema invariants.

**Rationale (cite PITFALLS §P4 — Pitfall 4: Cross-Project Memory Leakage):**

> Direct cross-project references would violate per-project scope invariant and risk P4 cross-project memory leakage. "Isolation into a memory system designed as single-tenant is painful. Per-tenant storage is cheap. Cross-tenant data leaks are not." (PITFALLS §P4 mitigation 3 reference).

Round-table state follows the same isolation principle. Cross-project leakage in round-table context would be: project A's round-table transcript citing project B's question / synthesis —— meaningless AND potentially contaminating.

### §6.6 Round-Table State Worked Example (kais-movie-pipeline Volvo S1-1)

To make the per-project isolation concrete, here is a worked example using a kais-movie-pipeline round table.

**Project context:**

- Repo: `/data/workspace/kais-movie-pipeline/` (separate from hermes-agent repo)
- `project_slug`: `kais-movie-pipeline:e7f8a9b2` (repo_basename + git_toplevel_abspath_sha8)
- Round table ID: `rt_20260715_153000_a1b2c3` (CC-generated uuid per OQ-11)

**State file path:**

```
~/.hermes/agents/.runtime/kais-movie-pipeline:e7f8a9b2/round_tables/rt_20260715_153000_a1b2c3.json
```

**State JSON content (excerpt):**

```json
{
  "round_table_id": "rt_20260715_153000_a1b2c3",
  "project_slug": "kais-movie-pipeline:e7f8a9b2",
  "opened_at": "2026-07-15T15:30:00Z",
  "closed_at": null,
  "panel": ["screenplay", "cinematographer", "hook_retention", "theory_critic"],
  "question": "Should Volvo S1-1 opening use empty-car establish or grandson reveal?",
  "turn_order": ["cinematographer", "screenplay", "hook_retention", "theory_critic"],
  "max_rounds": 3,
  "early_stop_rule": "consensus_3_of_4 OR round_2_no_change",
  "current_round": 2,
  "current_speaker_index": 1,
  "state": "in_progress",
  "turns": [
    {
      "round": 1,
      "speaker": "cinematographer",
      "ts": "2026-07-15T15:30:42Z",
      "opinion_text": "Empty-car establish better suits the introspective mood...",
      "cited_refs": ["shot-grammar.md", "vertical-screen-framing.md"],
      "fitness_score": 0.87,
      "evolution_log_tail": [...]
    }
  ],
  "final_synthesis": null,
  "synthesizer": null,
  "early_stop_triggered": false,
  "early_stop_reason": null
}
```

**Per-project isolation verification:**

- This state file lives **only** under `kais-movie-pipeline:e7f8a9b2/` —— NOT under `hermes-agent:a1b2c3d4/` (a different project).
- The same 4 agents (screenplay / cinematographer / hook_retention / theory_critic) participate in multiple projects' round tables, but each project's transcript is independent.
- The `fitness_score: 0.87` snapshot is captured **at turn time** (per ARCHITECTURE §5.2 closing paragraph) —— if cinematographer's score later updates to 0.91 via curator pass, this transcript remains reproducible.

**Crash recovery scenario (§6.4 (a)):**

- CC crashes mid-round-2 after cinematographer speaks (index 0) but before screenplay (index 1).
- State file shows `current_round: 2`, `current_speaker_index: 1` (screenplay's turn).
- Hermes detects tmux session end → logs warning.
- Operator restarts CC, opens same round_table_id: `round_table_open(round_table_id="rt_20260715_153000_a1b2c3", ...)` → Hermes reads state file, resumes from screenplay turn.



---

## §7 Phase 44 7 决策 Cross-Validation Audit + OQ/CC Resolution

### §7.0 Audit 声明

本节 audit 本 doc 的 **3-location + Option B + slug 策略 是否一致支持 Phase 44 锁定的 7 决策** (cite by 决策号 from `00-FIRST-PRINCIPLES.md` §2.1-§2.7).

**预期 = 7/7 一致** (本 doc 是 deployment-topology 落实, 不是 re-derivation).

同时声明 **OQ-6 + OQ-12 + CC-4 三条 open question 的 resolution 位置**.

### §7.1 7-Row 决策 Audit Table

| 决策 # | 决策 (一句话) | 本 doc 实现位置 | 一致? | Citation |
|--------|---------------|------------------|-------|----------|
| **决策 1** | T6 协议 (Hermes MCP server + tmux dispatch + CC native MCP client) | §2.1 Location 1 hermes-agent repo 是 runtime owner; §6.1 round-table state 路径 Hermes 拥有 (`~/.hermes/agents/.runtime/{slug}/round_tables/*.json` 由 dispatcher 写); §6.4 CC crash 检测依赖 tmux session end | ✅ | ARCHITECTURE §6 + Phase 44 §2.1 + 决策 1 |
| **决策 2** | B3a Python runner 增量迁移 (delegate-only phase 迁 CC) | §2.1 v11.0 PoC deliverable list 包括 `mcp_serve.py` extensions + `agent/agent_dispatcher.py` + `agent/curator.py` `_memory_evolution_phase` (all additive Python); v12+ `hermes agent transform` CLI 也 Python | ✅ | ARCHITECTURE §6.4 row 1 + Phase 44 §2.2 + 决策 2 |
| **决策 3** | D2 storyboard-first-class (orchestrator round-based parallel) | §6.3 round-table state per-project 隔离 支持 D2 round-based parallel (每个 project 独立 round table); §6.5 cross-project reference forbidden 保证 parallel 不会 cross-contaminate | ✅ | ARCHITECTURE §5.2 + Phase 44 §2.3 + 决策 3 |
| **决策 4** | G2 通用编排框架 (kais-movie-pipeline 首个 sample) | §2.1 + §2.3 hermes-agent repo + `~/.hermes/agents/` 共同 host G2 runtime; kais-hermes-skills repo 作 lineage source; §3 lineage chain 是 G2 transform 的 traceability 基础 | ✅ | ARCHITECTURE §6 + Phase 44 §2.4 + 决策 4 |
| **决策 5** | α agent form (YAML + persona + tools + refs + memory_scope + lineage) | §3 完整 lineage chain 规范 (forward SKILL.md→YAML + backward YAML→SKILL.md + drift detection + 5 invariants L1-L5); §2.4 write authority matrix 明确 persona operator-owned (L5) | ✅ | Phase 45 agents-schema.yaml `lineage` + ARCHITECTURE §6.1/§6.2 + Phase 44 §2.5 + 决策 5 |
| **决策 6** | per-agent memory + curator-driven 自进化 | §4 Option B vs Physical Partition migration triggers —— 完整 lifecycle 决策 (v11.0 PoC Option B, v12+ 物理分区 when Class A/B/C thresholds fire); §2.4 row 2 curator mutates evolution_log; §2.4 row 4/5 curator-owned | ✅ | ARCHITECTURE §3.2 + PITFALLS §P3 + SUMMARY CC-4 + Phase 44 §2.6 + 决策 6 |
| **决策 7** | 分层 CC 角色 (Hermes 控结构 / turn_order / max_rounds / early_stop_rule / state schema; CC 控 question framing + synthesis) | §2.3 write authority split (curator 只改 evolution_log + fitness_score, 不改 persona); §2.4 row 3 dispatcher writes state JSON, CC 通过 MCP tool 间接; §6.4 Hermes owns `.runtime/` state files, CC never touches directly; §4.3 backend switch 在 Hermes 层完成, CC 完全无感知 | ✅ | ARCHITECTURE §5.1 + §6 + Phase 44 §2.7 + 决策 7 |

**结果:** 7/7 ✅ 一致.

### §7.2 偏差分析 (Deviation Analysis)

- **预期:** 7/7 一致 (本 doc 是 deployment-topology 落实, 不是 re-derivation).
- **实际:** 7/7 一致. 本 doc 未发现 Phase 44 决策需修正.
- **声明:** "本 audit 是 horizontal validation —— 不是 re-derivation. 若 v11.0 PoC 实施中发现 3-location 表或 Option B 触发条件需调整, 应在 `05-POC-PLAN.md` 的 risk register 标注 + 在 Phase 51 audit 复审."
- **§4.4 trigger thresholds 特别声明:** 这些 numeric constants (30 agent / 10 project / 5000 records / p95 500ms / p99 2000ms / failure 1% 等) 是 **STARTING-POINT**, revisable in Phase 51 audit based on v11.0 PoC 实测数据. 7/7 audit 不包含 trigger thresholds 的 numeric 准确性 —— 那个是 revisable parameter, 不是 决策一致性.

### §7.3 OQ-6 + OQ-12 + CC-4 Resolution 声明

**OQ-6 (project slug 重命名稳定性): RESOLVED in §5.**

- Short-term (v11.0 PoC): accepts breakage with 3 documented scenarios (rename / move / clone) + manual `mv` recovery (§5.2).
- Long-term (v12+): fix via `.hermes/project.id` stable ID with adoption roadmap (§5.3-§5.6). Adoption triggered by rename pain OR 2nd project addition.
- **Stability marker:** short-term LOCKED; long-term DESIGN.

**OQ-12 (mem0 backend partition timing): RESOLVED in §4.**

- v11.0 PoC uses Option B (mem0 single backend + `agent_id` filter) per ARCHITECTURE §3.2 recommendation.
- v12+ migrates to Physical Partition (per PITFALLS §P3 mitigation 1) when trigger conditions fire (§4.4 Class A scale / Class B latency / Class C safety thresholds).
- API surface unchanged across transition (§4.3 — `get_agent_memory` `agent_id` parameter supports both modes).
- **Stability marker:** Option B + Physical Partition definitions LOCKED; §4.4 trigger thresholds STARTING-POINT (revisable).

**CC-4 (Option B lifecycle decision): RESOLVED in §4 + recorded here.**

- ARCHITECTURE §3.2 Option B ↔ PITFALLS §P3 mitigation 1 Physical Partition ↔ STACK §3.2 Tool 3 `get_agent_memory` agent_id parameter — 这条 cross-cutting finding 现在有 explicit migration triggers.
- **v12+ implementers do NOT need to re-discuss** Option B vs Physical Partition decision. CC-4 closed.
- **Migration is ONE-WAY** (§4.6 caveat): Option B → Physical Partition; reverse migration not recommended.

**Cite:** SUMMARY.md OQ table (rows OQ-6, OQ-12) + CC findings (CC-4) as resolution audit source.

### §7.4 P3 + P12 风险评估更新

**P3 (Pitfall 3: Scoped Retrieval Performance Collapse):**

- **v11.0 PoC scale** (15 agent × 1 project × ≤500 records/agent): **LOW** risk. HNSW global graph comfortably handles this scale.
- **v12+ scale** (30+ agent × 10+ project × ≤500 records/agent = 150K+ records): **HIGH** risk. Triggers Class A migration thresholds (§4.4 A1/A2/A3).
- **Resolution:** §4.4 Class A scale triggers + §4.6 migration path.

**P12 (Pitfall 12: Cross-Agent Memory Contamination via Shared mem0 Workspace):**

- **v11.0 PoC:** **LOW** risk IF filter enforcement audit passes (§4.5 — all `mem0.search()` call sites use `_scoped_agent_id`).
- **v12+:** **MEDIUM** risk due to scale-induced filter complexity (more call sites → more bypass chances). Physical Partition eliminates entirely at infrastructure level.
- **Resolution:** §4.4 Class C safety triggers (C1 contamination / C2 bypass) + §4.6 migration path.

**Cite:** PITFALLS §P3 + §P12 + Phase 51 VALIDATE risk register reconciliation (will verify field-level mitigation coverage in v11.0 PoC implementation).

---

## §8 Downstream Citation Guide + Coherence 声明 + References

### §8.0 Downstream Citation Card Table

| Downstream doc | Cite from this doc | Do NOT re-derive | Should derive (own contribution) |
|----------------|---------------------|-------------------|-----------------------------------|
| **`04-MIGRATION-PATH.md`** (Phase 49) | §2.4 write authority matrix (who can create agent YAML); §3.2 forward chain (transform source/target/sha256 recording); §2.1 v11.0 PoC deliverable list (where transform CLI lives); §3.5 L1-L5 invariants (transform must satisfy) | 3-location frame itself (cite §2 + ARCHITECTURE §6); Option B triggers (cite §4.4) | 15-expert 5-field transform rules; `default_invocation: skill_fallback → mcp_tool` switching logic; retained-phases allowlist location; memory schema migration |
| **`05-POC-PLAN.md`** (Phase 50) | §4.4 migration triggers (initial thresholds for PoC monitoring); §4.5 v11.0 PoC acceptance criteria (latency benchmark p95 <500ms + filter audit + workspace isolation test); §4.7 P3/P12 risk levels at PoC scale (LOW); §6.4 crash recovery test cases | Lineage chain detail (cite §3); slug long-term fix (cite §5.3-§5.6) | PoC fitness battery; latency SLO operationalization; bias canary; threshold tuning methodology; dry-run-first invariant test |
| **Phase 51 VALIDATE lint** | §7.1 7 决策 audit table (cross-check 7/7 一致 holds); §7.3 OQ-6/OQ-12/CC-4 resolution declarations (verify each has section pointer); §3.5 lineage invariants L1-L5 (verify each in agent YAML lint); §4.4 trigger thresholds as numeric constants (cross-check v11.0 PoC monitoring catches these) | Entire doc (it's the source of truth) | Cross-doc consistency lint script (term/schema/decision/citation checks across all 7 design docs) |

### §8.1 Coherence 声明

**ROADMAP SC#1-5 coverage:**

- **SC#1 (file exists):** §0 + §1.
- **SC#2 (3-location sync strategy):** §1.6 quick-glance + §2 full deep-dive + §3 lineage chain.
- **SC#3 (Option B vs Physical Partition triggers):** §4 full deep-dive (resolves OQ-12 + CC-4).
- **SC#4 (round-table state path):** §6 full deep-dive (references ARCHITECTURE §5.1).
- **SC#5 (project slug stability):** §5 full deep-dive (resolves OQ-6).

**完整性 声明:**

> 3-location sync strategy (§2) + lineage chain (§3) + Option B vs Physical Partition migration triggers (§4) + project slug stability (§5) + round-table state path (§6) + Phase 44 7 决策 cross-validation audit (§7) + OQ-6/OQ-12/CC-4 resolution declarations = **完整 ROADMAP SC#1-5 coverage**.

**v11.0 PoC implementer 使用 声明:**

> v11.0 PoC implementer 引用本 doc 的 §2.4 write authority matrix + §3 lineage chain + §4.4 trigger thresholds + §4.5 acceptance criteria + §5.1 slug derivation 即可 defending "where does this artifact live? who can write it? when do I migrate mem0?", **不需重新推导 Phase 44 决策或 re-literate Option B vs 物理分区**.

### §8.2 References

#### Phase 44 root arguments (00-FIRST-PRINCIPLES.md)

- `00-FIRST-PRINCIPLES.md` §2.1 (决策 1: T6 协议) + §2.5 (决策 5: α agent form) + §2.6 (决策 6: per-agent memory) + §2.7 (决策 7: 分层 CC 角色) —— cited throughout §1.1, §2, §3, §4, §7.

#### Phase 45 schema contracts (01-AGENT-REGISTRY-SCHEMA.md)

- `01-AGENT-REGISTRY-SCHEMA.md` `lineage` field spec (sub-fields: `derived_from_skill_id`, `derived_from_repo`, `transform_date`, `skill_sha256`) —— cited §3.1, §3.2, §3.5 (L1-L4).
- `memory-record-schema.yaml` `agent_id` required field + `scope` (global|project|session) + `memory_scope` —— cited §4.1, §4.3.

#### Phase 46 protocol contracts (02-ROUND-TABLE-PROTOCOL.md)

- `02-ROUND-TABLE-PROTOCOL.md` §2 round-table-state-schema.yaml `project_slug` required —— cited §6.2.
- §4 state file path `~/.hermes/agents/.runtime/{slug}/round_tables/{round_table_id}.json` + atomic/append-only/crash-recoverable invariants —— cited §6.1, §6.4.

#### Phase 47 sibling (03-COMPARISON-VS-KIMI-MCP-SHIM.md)

- `03-COMPARISON-VS-KIMI-MCP-SHIM.md` §4.5 A2A expansion position —— cited §4.8.

#### ARCHITECTURE.md

- §3.1 (Current Mem0 Backend Surface — `_read_filters()` returns only `user_id`) —— cited §4.1.
- §3.2 (Three Implementation Options — Option B RECOMMENDED) —— cited §1.5.2, §4.0, §4.1.
- §3.3 (Mem0 Backend Extension Points — additive `_scoped_agent_id`) —— cited §4.1.
- §3.4 (Curator-Driven Memory Evolution — `_memory_evolution_phase`) —— cited §2.3.
- §5.1 (Round table state file layout + project_slug derivation `{repo_basename}:{git_toplevel_abspath_sha8}`) —— cited §1.1, §5.1, §6.0, §6.1.
- §5.2 (Cross-project sharing rules — 5 artifact classes) —— cited §1.5.1, §2.5, §6.3, §6.5.
- §5.3 (Round Table Lifecycle sketch) —— cited §6.4.
- §6 (Cross-Repo Coordination — 3-location skeleton) —— cited throughout (frame).
- §6.1 (Transform Procedure 5 steps) —— cited §2.2, §3.2.
- §6.2 (Drift Detection — `_detect_skill_agent_drift()`) —— cited §3.4.
- §6.3 (Synchronization Strategy — 4 sync directions) —— cited §2.1, §2.2.
- §6.4 (Repo Impact Summary — v10.0/v11.0/v12+ deliverable matrix) —— cited §1.5.1, §2.1, §2.2.
- §7.4 (Project Slug Pattern — disambiguates same-name repos) —— cited §5.1.
- §8 (Anti-Patterns: §8.1 YAML as Prompt Dump / §8.2 Auto-Re-Transform on Drift) —— cited §2.3, §3.4.
- §10.6 (OQ-6 slug stability) —— cited §5.0.

#### FEATURES.md

- §8 B8.1 (Agent Card exposition borrowable) —— cited §4.8.
- §10 B7.4 (A2A Microsoft 三层协议分层) —— cited §1.7, §4.8.

#### STACK.md

- §3.2 Tool 3 `get_agent_memory` (`agent_id` parameter — supports both Option B and Physical Partition) —— cited §1.5.2, §4.3.
- §11.4 (OQ-12 deferral + latency SLO p95 <500ms) —— cited §4.0, §4.5.

#### PITFALLS.md

- §P3 (Pitfall 3: Scoped Retrieval Performance Collapse — Option B ceiling, mitigation 1 Physical Partition) —— cited §1.5.2, §4.0, §4.2, §4.4, §4.7, §7.4.
- §P4 (Pitfall 4: Cross-Project Memory Leakage) —— cited §6.5.
- §P12 (Pitfall 12: Cross-Agent Memory Contamination — Option B bleed risk, filter enforcement requirement) —— cited §1.5.2, §4.0, §4.7, §7.4.

#### SUMMARY.md

- CC-4 (Option B lifecycle decision: ARCHITECTURE §3.2 ↔ PITFALLS §P3 mitigation 1 ↔ STACK §3.2 Tool 3) —— cited §1.5.2, §4.0, §4.3, §7.3.
- OQ-6 (project slug 重命名稳定性 — 接受 breakage short-term, `.hermes/project.id` long-term) —— cited §5.0, §5.2, §7.3.
- OQ-12 (mem0 backend partition timing — Option B v11.0 PoC, 物理分区 v12+) —— cited §4.0, §7.3.

#### MEMORY.md (in-repo operator context)

- `kais-movie-agent-v5-hermes-native-migration.md` (2026-07-02): v5.0 ship moved `skills/movie-experts` + 4 plugins to kais-hermes-skills repo. hermes-agent repo 现仅保留 GSD `.planning/` 工件. —— cited §1.1 (3-location frame), §2.2, §4.1.
- `hermes-gateway-systemd.md` (2026-07-01): hermes-agent runtime runs under systemd supervision. `~/.hermes/` 是 canonical state root per CLAUDE.md + `hermes_constants.get_hermes_home()`. —— cited §1.1, §2.3.

#### CLAUDE.md

- HERMES_HOME (`~/.hermes/` canonical state root via `hermes_constants.get_hermes_home()`) —— cited §1.1, §2.3.
- Skill File Conventions (SKILL.md discovery rules) —— informs §3 lineage chain.
- PLW1514 (unspecified-encoding Ruff rule) —— cited §3.2 (`hashlib.sha256(... .encode("utf-8"))`).

#### Phase 44/45/46/47 commit references

- Phase 44 (`00-FIRST-PRINCIPLES.md`): commit `e7be0f45f` (2026-07-06) —— 7 决策 LOCKED.
- Phase 45 (`01-AGENT-REGISTRY-SCHEMA.md`): schema LOCKED in `agents-schema.yaml` + `memory-record-schema.yaml` —— citation throughout §3 + §4.
- Phase 46 (`02-ROUND-TABLE-PROTOCOL.md`): protocol LOCKED in `round-table-state-schema.yaml` —— citation throughout §6.
- Phase 47 (`03-COMPARISON-VS-KIMI-MCP-SHIM.md`): A2A expansion position LOCKED —— citation §4.8.

---

*End of v10.0 Design Doc #06 — Cross-Repo Impact. Synthesized 2026-07-07 in Phase 48-cross-repo-impact plan 48-01. Resolves SUMMARY OQ-6 + OQ-12 + CC-4. Phase 44 决策 1-7 cross-validation: 7/7 ✅ consistent.*






