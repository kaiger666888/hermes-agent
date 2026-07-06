# 01 — Agent Registry Schema:v10.0 18-Field Agent YAML + 2-Layer Memory Record Schema(物理载体)

> **Document status:** design-2026-07-06-v10agentschema · supersedes: none · superseded_by: TBD
> **Milestone:** v10.0 — Hermes-Agent 编排架构第一性原理推导(设计型)
> **Phase:** 45 of v10.0 design milestone · **Authors:** hermes-agent design team
> **Audience:** Kai(设计决策 reviewer)+ Kimi(Notion 续聊对照)+ v11.0 PoC 实施者
> **Reading time:** ~25 minutes(全文)/ ~6 minutes(§0 + §1.2 + §7 审计表)
> **Stability:** §1.2 + §2 + §3 + §4 + §5 全部 `stable`(字段级锁定,修改需开新设计-修订里程碑);§6 + §7 + §8 `stable`(audit/citation/ref 跟随 §1-§5)
> **Confidence:** HIGH(本文档字段全部源自 ARCHITECTURE §1.1 + §2 + §3.4 + PITFALLS §P1/P2/P4/P5/P8/P10/P14 + SUMMARY CC-2 + 6 OQ resolutions;每个字段有 traceable source,本文档不发明任何字段)

---

## §0 — 阅读指南

本文档是 **v10.0 milestone 的 18-field agent YAML schema + 2-layer memory record schema 物理载体**,产出 3 个 deliverable:

1. **本文档(01-AGENT-REGISTRY-SCHEMA.md)** —— 设计 narrative + 字段级 PITFALLS 缓解映射 + OQ 决议审计
2. **`agents-schema.yaml`** —— 机器可读 JSON Schema(draft 2020-12),18 fields + $defs(Lineage / Prerequisites / EvolutionLogEntry)
3. **`memory-record-schema.yaml`** —— 独立 JSON Schema(非 agents-schema 的 sub-schema),10 个不变量字段 + persona_sha256(OQ-1)+ schema_version(P14)

后续 4 份设计文档(02 / 04 / 05 / 06)**在不重新推导决策 5/6 的前提下**引用本文档字段名 —— 本文档是它们的字段引用物理载体(§8.0 downstream citation card table)。

**与 Phase 44 `00-FIRST-PRINCIPLES.md` 的关系:** Phase 44 决策 5(α agent form:YAML + persona + tools + refs + memory_scope + lineage)+ 决策 6(per-agent memory + curator 自进化)是本文档的**根论据 anchor**(`root-arg-决策-5` / `root-arg-决策-6`)。本文档**不重新推导**这两个决策,只把它们落地成可被 Python dataclass generator + Phase 51 lint script 消费的 schema。

**与 SUMMARY.md CC-2 的关系:** SUMMARY.md CC-2 cross-cutting finding 指出 —— 18-field agent schema 有 8 个字段直接由 PITFALLS 反推,但 PITFALLS 还要求另外 10 个字段(expires_at / verified_at / supersedes_memory_id / confidence / half_life_days / evidence_chain / evidence_operator_ids / status / confidentiality / scope)**语义上属于 "memory record schema" 而非 "agent identity schema"**。本文档 §1.3 把这个 2-layer split 显式化 —— 这是 CC-2 mandate 的物理载体。

### 章节地图

| 章节 | 内容 | 阅读优先级(按角色) |
|---|---|---|
| §0 | 阅读指南(本节) | 所有人先读 |
| §1 | 设计哲学 + 2-layer 架构图 + 18-field 总表 + roadmap 放置 | reviewer 必读 §1.1+§1.3;PoC 实施者必读 §1.2 |
| §2 | 18-field 逐字段 narrative(§2.1-§2.18),每字段含 Type/Source/PITFALLS mitigation/Example | **核心章节** — PoC 实施者 + 维护者必读 |
| §3 | memory-record schema narrative(10 个不变量字段 + persona_sha256 + schema_version) | PoC 实施者必读 |
| §4 | per-agent memory 3-tier(core / working / archival)+ max_records cap + compaction trigger | PoC 实施者必读;resolves OQ-7 |
| §5 | curator `_memory_evolution_phase` field contract(exec order + dry-run + try/except + iteration) | curator 维护者必读;resolves OQ-16 |
| §6 | 15-expert transform mapping table(verbatim from ARCHITECTURE §2) | migration 实施者必读 |
| §7 | 6 OQs + 7 load-bearing pitfalls 字段级审计表 | reviewer 必读(SC#5 物理载体) |
| §8 | downstream citation card + coherence 声明 + References | 后续 4 docs 作者必读 |

### 稳定性标记(修改门槛)

| 章节 | 稳定性 | 修改门槛 |
|---|---|---|
| §1.2 (18-field 总表) | `stable` | 字段 add/remove 需开新设计-修订里程碑(SC#1 ROADMAP-level lock) |
| §1.3 (2-layer 架构图) | `stable` | CC-2 mandate;2-layer split 是 load-bearing,不可降级为单 layer |
| §2 (18-field narrative) | `stable` | 字段定义锁定;`additionalProperties: false` 在 agents-schema.yaml 强制 |
| §3 (memory-record narrative) | `stable` | 10 个不变量字段锁定;新增字段需开新里程碑 |
| §4 (3-tier memory) | `stable` | max_records=500 + 3-tier 划分 resolves OQ-7,修改需重跑 §4.4 rationale |
| §5 (curator phase contract) | `stable` | execution order + dry-run + try/except 三件套 resolves OQ-16,修改需同步改 `agent/curator.py` hooks(v11.0 PoC) |
| §6 (15-expert table) | `stable` | verbatim from ARCHITECTURE §2;FOUND-08 preserved |
| §7 (audit tables) | `stable` | 跟随 §1-§6 |
| §8 (citation + refs) | `stable` | 跟随 §1-§7 |

### 受众指引(3 类读者)

- **Kai(reviewer / 设计决策者):** 先读 §0 + §1.1(2-layer 哲学)+ §7.1 OQ audit + §7.2 pitfall audit。如果对某字段 PITFALLS mitigation 有疑问,跳到 §2 或 §3 对应 §X.N。如果对 OQ 倾向性结论有疑问,跳到 §7.1 看是否 defer。§4.5 compaction trigger table + §5.1 execution order pseudo-code 是 load-bearing design choice,reviewer 必读。
- **Kimi(Notion 续聊对照):** 先读 §1.3 2-layer 架构图(理解 v10.0 schema 为什么 18 + 10 = 28 字段而非单一 schema),再读 §3.9 scope + §3.10 confidentiality + §4.4 max_records(这 3 字段是 Kimi 架构2.0 没原生处理的),最后读 §7.2 pitfall audit(对照 Kimi 方案的隐私 / 跨项目 / 持久化风险)。本文档字段名是 Kimi 续聊时的"接口契约"。
- **v11.0 PoC 实施者:** 先读 §0 + §1.2(18-field 表,作为 dataclass 生成源)+ §1.4(下游引用指南),然后用 §2 / §3 / §4 / §5 章节作为字段 spec。机器可读 schema 在 `agents-schema.yaml` + `memory-record-schema.yaml`,直接 `jsonschema` 校验。本文档**不发明任何字段**,所有字段都可 traceable to ARCHITECTURE §1.1 / §2 / §3.4 + PITFALLS §P-X + SUMMARY OQ-XX,实施者可以放心照 schema 写 Python dataclass + Pydantic Model。

---

## §1 — Schema Overview:2-Layer 架构 + 18-Field 总表

### §1.1 — 设计哲学:为什么是 2-Layer Schema(不是单层)

本文档定义 v10.0 agent registry 的 **2-layer memory schema** —— **上层 agent-profile YAML(18 字段)锁定身份与工具白名单;下层 memory-record schema(10 字段)锁定跨项目记忆条目的不变量。** 这个 2-layer split 是 Phase 44 SUMMARY.md CC-2 cross-cutting finding 的物理载体:

> **CC-2 引文(verbatim from SUMMARY.md):** "18-field schema 里有 8 个字段是直接由 PITFALLS 反推出来的'防护字段'……但 PITFALLS 还要求 5 个 schema 字段在 18-field 里没出现:`expires_at` / `verified_at` / `supersedes_memory_id` / `confidence` / `half_life_days`(全部来自 PITFALL-2 stale memory)、`evidence_chain` / `evidence_operator_ids` / `status="archived|quarantined"`(PITFALL-5/6)、`confidentiality`(PITFALL-10 privacy)、`scope: "global|project|session"`(PITFALL-4 三层 scope,比 ARCHITECTURE 的 `shared|per_agent|project_scoped` 更细)。**这些字段属于 'memory record schema',不是 'agent YAML schema'** —— `01-AGENT-REGISTRY-SCHEMA.md` 必须显式区分这两层,否则会被误以为 18-field schema 不够用。"

**根论据 anchor(`root-arg-决策-5` + `root-arg-决策-6`):**

- **决策 5(Phase 44 §2.5):** α agent form = YAML + persona + tools + refs + memory_scope + lineage,物理位置 `~/.hermes/agents/{name}.agent.yaml`。**根本需求:** agent 是**有持久身份、有记忆、可自进化的实体**,不是 prompt 模板。这个"持久身份"对应 §2 的 18 个 identity fields(name / persona / tools / lineage / evolution_log / fitness_score 等)。
- **决策 6(Phase 44 §2.6):** per-agent scoped memory(扩展 mem0 backend)+ curator 驱动跨项目自进化。**根本需求:** **agent 随项目越多越有经验**。这个"经验"的物理载体是 §3 的 memory-record schema(expires_at / verified_at / supersedes_memory_id / confidence / half_life_days / evidence_chain / evidence_operator_ids / status / confidentiality / scope),不是 agent YAML —— 因为同一个 agent(v5 persona 不变)在不同时刻、不同项目积累的记忆条目是动态的、可被 supersede 的、有时效性的。

**为什么不能合并成单层 schema?** 三个论据:

1. **生命周期不同。** Agent YAML 是 operator-owned(§2 的 18 字段几乎都 operator 或 curator 写,operator 主导);memory record 是 curator + 多源(feedback / eval_gate / round_table / external)写,operator 不直接编辑。合并会模糊 ownership boundary(违反 ARCHITECTURE §6.1 transform procedure 的 operator-ownership 不变量)。
2. **不变量粒度不同。** Agent YAML 的不变量是 `name` matches filename stem + `additionalProperties: false` + sha256 chaining in evolution_log;memory record 的不变量是 time-decay(P2)+ evidence coverage(P5)+ scope isolation(P4)+ confidentiality propagation(P10)。后者的不变量更细、更动态、需要 retrieve-time filter,前者则不需要。
3. **变更频率不同。** Agent YAML 几乎不变(operator 手改 persona + curator append evolution_log);memory record 高频变化(每次 curator `_memory_evolution_phase` 都可能新增 / supersede / quarantine)。两者合并意味着每次 memory write 都要重写 YAML —— 不可接受。

**结论:** §2 18 fields 是 agent identity + runtime knobs + curator-managed metadata;§3 10 fields 是 memory record 不变量。两层通过 `agent_id`(memory record 字段)和 `persona_sha256`(memory record 字段 + evolution_log entry 字段)关联。

### §1.2 — 18-Field Agent YAML 总表(verbatim from ARCHITECTURE §1.1 + 7th column "PITFALLS mitigation")

下表是 ARCHITECTURE.md §1.1 line 31-50 的 verbatim copy + 第 7 列 "PITFALLS mitigation" 标注。**本表是 SC#1 ROADMAP-level lock —— 字段 add/remove 需开新设计-修订里程碑。** 机器可读 schema 见 `agents-schema.yaml`(JSON Schema draft 2020-12,$defs 块定义 Lineage / Prerequisites / EvolutionLogEntry 三个 reusable shapes)。

| # | Field | Type | Required | Source | Purpose | PITFALLS mitigation |
|---|-------|------|----------|--------|---------|---------------------|
| 1 | `name` | `string` (regex `^[a-z0-9_-]+$`) | YES | Agent (must match filename stem) | Primary identifier; **NOT** the same as `expert_id` (a skill may transit to an agent with a different name). | — |
| 2 | `description` | `string` | YES | SKILL `description` (copy verbatim, then refine) | One-line summary surfaced by `agents_list` MCP tool and Hermes dashboard. | — |
| 3 | `version` | `string` (semver `^X.Y.Z$`) | YES | SKILL `version` (copy) | Schema version of the agent YAML itself; bumped when fields are added. | P14(schema migration —— `version` 是 agent-YAML-side 的 schema_version,memory-record-schema 也有独立 `schema_version`) |
| 4 | `persona` | `string` (multiline) | YES | **NEW — must rewrite** | The agent's system prompt fragment. **This is the load-bearing difference from SKILL.** SKILL body is injected as a user message; persona is injected as a system-prompt fragment. | **P1(persona drift)** —— persona_sha256 carried in every `evolution_log` entry(§2.14)+ every memory record(§3.11);drift detected when recall-time hash ≠ write-time hash |
| 5 | `tools` | `list[string]` | YES | Derived from `prerequisites.tools` + agent's actual capability surface | Tool whitelist. Honored by the dispatcher when the agent is invoked via `get_agent_opinion`. | — (resolves **OQ-13**: `tools` IS runtime whitelist enforced by dispatcher) |
| 6 | `memory_scope` | `enum: shared \| per_agent \| project_scoped` | YES | **NEW** | mem0 routing convention. `shared` = global user_id; `per_agent` = `user_id=agent:{name}`; `project_scoped` = `user_id=project:{slug}+agent:{name}`. Default: `per_agent`. | **P4(cross-project leakage)** —— memory_scope=per_agent 把 records 路由到 agent_id namespace;memory-record §3.9 的 scope 字段(global/project/session)做更细粒度的 visibility 控制 |
| 7 | `lineage` | `object` | YES | **NEW** | `{derived_from_skill_id, derived_from_repo, transform_date, transform_notes, skill_sha256}`. Records provenance so curator can detect SKILL↔agent drift. | — (operator ownership —— aligned with §3.1 of ARCHITECTURE "operator-owned") |
| 8 | `refs` | `list[string]` | NO (default `[]`) | SKILL `## References` table → flattened to file paths | RAG reference docs the agent is allowed to retrieve from. | — |
| 9 | `tags` | `list[string]` (regex `^[a-z0-9-]+$`) | NO | SKILL `metadata.hermes.tags` (copy) | Lowercase hyphenated; powers `agents_list` filtering. | — |
| 10 | `expert_id` | `string` | NO | SKILL `metadata.hermes.expert_id` (copy) | Backward-compat anchor — dispatcher can route skill-by-expert_id calls to agent. **FOUND-08 preserved.** | — (FOUND-08 backward-compat,Phase 44 决策 1) |
| 11 | `metrics` | `list[string]` | NO | SKILL `metadata.hermes.metrics` (copy) | Quality dimensions for the eval gate. Carried verbatim so v6.0 eval harness still works. | — |
| 12 | `prerequisites` | `object` | NO | SKILL `prerequisites` (copy) | `{tools, skills, env}`. **Activation conditions** (≠ `tools` runtime whitelist). | — |
| 13 | `related_agents` | `list[string]` | NO | SKILL `metadata.hermes.related_skills` (copy + rename) | Collaboration DAG. Drives round table panel suggestions. | — |
| 14 | `evolution_log` | `list[object]` | NO (curator-managed; do not hand-edit) | **NEW** | Append-only chain of `{ts, sha256, diff_summary, fitness_delta, trigger, persona_sha256}`. Tamper-evident via sha256 chaining (v6.0 `agent/curator_audit.py` pattern). | **P5(curator failure modes)** —— tamper-evident sha256 chain;persona_sha256 在每条 entry(§2.14)使 persona drift 可被审计 |
| 15 | `fitness_score` | `float (0.0-1.0) \| null` | NO | **NEW** | Curator-computed rolling quality score derived from eval gate + feedback verdicts. `null` until first curator pass. **Not** operator-set. | **P8(no fitness signal)** + resolves **OQ-4**(null = neutral 0.5 for ordering,UI 显示 "untested") |
| 16 | `platforms` | `list[string]` | NO (default `[linux, macos, windows]`) | SKILL `platforms` (copy) | OS compatibility gate, enforced via `skill_utils.skill_matches_platform`. | — |
| 17 | `round_table_eligible` | `bool` | NO (default `true`) | **NEW** | Whether this agent can be invited to a round table. Set `false` for ephemeral helpers. | — |
| 18 | `default_invocation` | `enum: mcp_tool \| skill_fallback \| disabled` | NO (default `mcp_tool`) | **NEW** | Dispatcher mode. `mcp_tool` = invoke via `get_agent_opinion`; `skill_fallback` = fall through to underlying SKILL (v1-v9 behavior); `disabled` = transform-in-progress. | — (FOUND-08 additive transition:`skill_fallback` 让 SKILL 仍可被调用) |

**Total: 18 fields(7 required, 11 optional-with-default).** SC#1 ROADMAP-level lock —— 任何 add/remove 需 milestone-level decision。机器可读 schema 在 `agents-schema.yaml`(JSON Schema draft 2020-12,`additionalProperties: false`)。

**关键观察:** 7 个 load-bearing pitfalls 中 5 个有 §2 agent-YAML 字段级 mitigation(P1→persona + P4→memory_scope + P5→evolution_log + P8→fitness_score + P14→version),其余 3 个 pitfall(P2 / P10)的字段级 mitigation 在 §3 memory-record schema。这种"两层各管一部分"的结构正是 CC-2 mandate 的 2-layer split。

### §1.3 — 2-Layer 架构图(ASCII,CC-2 mandate 物理载体)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Layer 1: agent-profile YAML(18 fields,operator-owned)              │
│ Physical: ~/.hermes/agents/{name}.agent.yaml                         │
│                                                                     │
│  §2 Identity (operator-curated):                                    │
│    - name / description / version / persona / tools                 │
│    - lineage / refs / tags / expert_id / metrics                    │
│    - prerequisites / related_agents                                 │
│  §2 Runtime knobs:                                                  │
│    - memory_scope (shared|per_agent|project_scoped)                 │
│    - default_invocation (mcp_tool|skill_fallback|disabled)          │
│    - platforms / round_table_eligible                               │
│  §2 Curator-managed (append-only):                                  │
│    - evolution_log (sha256-chained, with persona_sha256 per entry)  │
│    - fitness_score (curator-computed, null=untested)                │
│                                                                     │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 │ memory_scope=per_agent routes
                                 │ memory records by agent_id namespace
                                 │ (Option B from ARCHITECTURE §3.2)
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Layer 2: memory-record schema(10 mandated fields,curator+multi-src)│
│ Physical: mem0 backend, per-agent namespace (agent_id filter)        │
│                                                                     │
│  §3 Time-decay (P2 stale memory):                                   │
│    - expires_at / verified_at / half_life_days                      │
│    - supersedes_memory_id (supersession chain)                      │
│    - confidence (time-decaying float 0.0-1.0)                       │
│  §3 Provenance (P5 curator failure):                                │
│    - evidence_chain (≥3 sources)                                    │
│    - evidence_operator_ids (≥1,diversity check)                     │
│    - status (active|archived|quarantined|superseded)                │
│  §3 Scope isolation (P4 cross-project leakage):                     │
│    - scope (global|project|session, finer than memory_scope)        │
│    - project_id / session_id (required when scope=project/session)  │
│  §3 Privacy (P10 data leakage):                                     │
│    - confidentiality (public|internal|confidential|restricted)      │
│  §3 Cross-layer invariants:                                         │
│    - persona_sha256 (OQ-1 resolution — drift detection)             │
│    - schema_version (P14 — dry-run migration mode key)              │
│    - record_id / agent_id / created_at / last_recalled_at           │
│                                                                     │
└──────────────────────────────────────────────────────────────────────┘
```

**CC-2 verbatim 引文(重申):** "18-field has 8 fields from PITFALLS reverse-inference; the OTHER 10 fields belong to memory-record schema — explicit 2-layer separation prevents the misread '18-field schema is insufficient'."(SUMMARY.md CC-2)

**图解要点:**

- **物理位置不同。** Layer 1 在 `~/.hermes/agents/*.agent.yaml`(operator 主导);Layer 2 在 mem0 backend 的 per-agent namespace(curator + feedback + round_table 多源写入)。两者通过 `agent_id`(memory record 字段)= `name`(agent YAML 字段)关联。
- **变更频率不同。** Layer 1 几乎不变(operator 手改 persona + curator append evolution_log);Layer 2 高频变化(curator 每 N tick 写新记录,supersede 旧记录,quarantine 可疑记录)。
- **不变量不同。** Layer 1 用 `additionalProperties: false` + sha256 chain;Layer 2 用 time-decay + evidence coverage + scope filter + confidentiality propagation。
- **§2.4 persona + §2.14 evolution_log entry + §3 memory record 都带 `persona_sha256`,形成 P1 persona drift 的 cross-layer detection network。** Recall-time 若 memory record 的 persona_sha256 ≠ 当前 agent YAML persona 的 sha256,记录被标记为需 re-verification。

### §1.4 — Roadmap 放置:本文档是 02/04/05/06 的字段引用物理载体

本文档是 **02-ROUND-TABLE-PROTOCOL.md / 04-MIGRATION-PATH.md / 05-POC-PLAN.md / 06-CROSS-REPO-IMPACT.md 的字段引用物理载体**。后续 4 docs 在不重新推导 Phase 44 决策 5/6 的前提下,直接引用本文档字段名 —— 引用契约见 §8.0 downstream citation card table。

**下游 doc 各自引用的字段清单(预览,详见 §8.0):**

| Downstream doc | Cite from this doc | Do NOT re-derive | Should derive |
|----------------|-------------------|------------------|---------------|
| `02-ROUND-TABLE-PROTOCOL.md` | §2.6 `memory_scope` + §3.9 `scope` + §3.10 `confidentiality` + §4 memory tier | 18-field schema, `_memory_evolution_phase` | turn lifecycle + conflict arbitration + scope precedence |
| `04-MIGRATION-PATH.md` | §2.7 `lineage` + §2.18 `default_invocation` + §6 transform table + §3.12 `schema_version` | 18-field schema | 15-expert transform rules + memory schema migration |
| `05-POC-PLAN.md` | §4.5 compaction + §5.2 dry-run + §7.2 pitfall audit | entire schema | fitness battery + latency SLO + bias canary |
| `06-CROSS-REPO-IMPACT.md` | §2.6 `memory_scope` + §3.9 `scope` + §3.12 `schema_version` | 18-field schema | 3-location sync + Option B vs 物理分区 |
| `51 VALIDATE lint` | entire schema (`agents-schema.yaml` + `memory-record-schema.yaml` as machine-checkable inputs) | entire schema | cross-doc consistency lint script |

**Phase 44 决策 5 + 决策 6 是 LOCKED:** 本文档**不重新推导**"agent 是有持久身份的实体"(决策 5)和"agent 随项目越多越有经验"(决策 6)。本文档只把它们落地成 schema —— 即"持久身份的物理形态(18 fields)"和"经验的物理形态(10 memory-record fields + 3-tier + curator phase contract)"。任何对决策 5/6 本身的 re-litigation 需开新设计-修订里程碑(类比 v2.0 PRFP §1.1 stability marker)。

**Task 1 收束声明:** §1 完成 schema 哲学 + 2-layer 架构图 + 18-field 总表 + roadmap 放置 —— 后续 §2-§8 在此框架内展开字段级 narrative、tier 规则、curator 契约、transform 映射、OQ + pitfall 审计、downstream 引用指南。本文档目标行数 800-1200(对标 Phase 44 `00-FIRST-PRINCIPLES.md` 1181 行的 rigor,但 scope 更紧 —— Phase 44 推导决策,本文档只落地 schema)。每个 §2/§3 字段都会显式标 "PITFALLS mitigation: P-X §Y" 或 "—",确保 7 个 load-bearing pitfall 的字段级缓解可被审计(§7.2 物理载体)。每个 §4/§5 设计 choice 都会标 "resolves OQ-X" 或 "deferred to v11.0",确保 6 个 OQ 全部被显式处理(§7.1 物理载体)。

**与 STACK.md / FEATURES.md 的关系:** 本文档不直接引用 STACK.md(协议层在 02-ROUND-TABLE-PROTOCOL.md 引用)或 FEATURES.md(业界对照在 Phase 44 §4 borrowable 评估已锁定)。本文档的 reference palette 是:ARCHITECTURE §1/§2/§3(字段源)+ PITFALLS §P-1/2/4/5/8/10/14(mitigation 源)+ SUMMARY CC-2 + OQ-1/4/7/13/14/16(resolution 源)+ Phase 44 §2.5/§2.6(root argument)。完整 reference 列表见 §8.2。

**Audit trail note:** 本文档每个字段都附带 source citation(ARCHITECTURE §X.Y 或 PITFALLS §P-Z 或 SUMMARY OQ-W)。这是设计型 milestone 的 reviewability 不变量 —— reviewer 可在任何字段 narrative 处反查 source,确认不是"凭空发明的字段"。这种 discipline 来自 Phase 44 §1.1 v10.0 加严规则:"不允许 'industry 用 X 所以我们抄 X' 式伪类比"。本文档**不发明任何字段**,只把 Phase 44 已锁的决策 5/6 + ARCHITECTURE 已展开的 18-field 表 + PITFALLS 已要求的字段级 mitigation 落地成可执行 schema。如 reviewer 发现某字段无 source citation,标记为"audit failure",在设计-修订里程碑中处理。

---

**End of Task 1.** Task 2 writes `agents-schema.yaml` + `memory-record-schema.yaml`(JSON Schema files)。Task 3-5 append §2-§8 to this narrative file。每个 task 独立 commit,docs(45-01) prefix。Task 5 收束时本文档 ≥ 800 行 + 3 deliverable files 全部 ready for v11.0 PoC consumption。

---




## §2 — 18-Field Agent YAML:Per-Field Narrative(PITFALLS 字段级缓解映射)

### §2.0 — 本节结构声明

本节逐字段展开 §1.2 的 18-field 表,**聚焦于 PITFALLS 字段级缓解机制 + 字段间相互引用关系**。机器可读 schema 见 `agents-schema.yaml`(JSON Schema draft 2020-12,$defs 块定义 Lineage / Prerequisites / EvolutionLogEntry 三个 reusable shapes)。每个 §2.N 子节遵循 4-block scaffold:

1. **Type + Constraints + Required + Default** —— 从 agents-schema.yaml 抄录
2. **Source + Purpose** —— 从 ARCHITECTURE §1.1 抄录
3. **PITFALLS mitigation** —— 显式字段级机制(若 applicable),否则标 "—"
4. **Example** —— YAML 片段(从 ARCHITECTURE §1.3 screenplay YAML 或新构造)

---

### §2.1 — `name`

**Type:** `string` · **Constraints:** regex `^[a-z0-9_-]+$` · **Required:** YES · **Default:** —

**Source:** ARCHITECTURE §1.1 row 1. **Purpose:** Primary identifier; MUST match filename stem of the `.agent.yaml` file. Distinct from `expert_id`(§2.10)—— 一个 SKILL 可以 transit 到一个不同 name 的 agent。

**PITFALLS mitigation:** —

**Example:**
```yaml
name: screenplay
# Resolves to ~/.hermes/agents/screenplay.agent.yaml
```

---

### §2.2 — `description`

**Type:** `string` · **Constraints:** `min_length: 10` · **Required:** YES · **Default:** —

**Source:** ARCHITECTURE §1.1 row 2(SKILL `description` copy + refine). **Purpose:** One-line summary surfaced by `agents_list` MCP tool + Hermes dashboard。15-expert transform 时直接复制 SKILL description,可适度 refine 以反映 first-person persona framing(§2.4)。

**PITFALLS mitigation:** —

**Example:**
```yaml
description: "Screenplay Expert: scene-level script generation, dialogue design, emotional arc construction for AI short film production."
```

---

### §2.3 — `version`

**Type:** `string` · **Constraints:** semver `^[0-9]+\.[0-9]+\.[0-9]+$` · **Required:** YES · **Default:** —

**Source:** ARCHITECTURE §1.1 row 3. **Purpose:** Schema version of the agent YAML itself。SKILL `version` tracks SKILL-content version;agent YAML `version` 跟踪 schema-affecting edits。Transform 时初始值 `1.0.0`,后续字段新增 / 重大 persona rewrite 时 bump。

**PITFALLS mitigation:** P14(schema migration)—— `version` 是 agent-YAML-side 的 schema version 跟踪器;memory-record-schema 的 `schema_version` 字段(§3.12)是 memory-record-side 的迁移 key。两者独立但 lockstep bump。

**Example:**
```yaml
version: 1.0.0  # initial transform
# After adding a new optional field (e.g. fitness_battery):
# version: 1.1.0
```

---

### §2.4 — `persona`(P1 load-bearing field)

**Type:** `string` (multiline) · **Constraints:** 无硬性长度限制,推荐 5-15 行 · **Required:** YES · **Default:** —

**Source:** ARCHITECTURE §1.1 row 4(NEW — must rewrite)。**Purpose:** The agent's system-prompt fragment. **This is the load-bearing difference from SKILL.**

**PITFALLS mitigation: P1(persona drift)。** Persona 是 agent 的身份 anchor;P1 风险是 agent 经 200+ memory records + 10 projects 后,additive memory mass dilute 原 persona,使 agent forget 其角色。机制:

1. **persona_sha256 invariant.** Registration 时计算 persona 的 SHA-256,写入 evolution_log 的 genesis entry(§2.14)。每次 evolution_log entry 也带当时 persona 的 sha256。Cross-layer:每条 memory record 也带 persona_sha256(§3.11)。Recall-time 若 memory record 的 persona_sha256 ≠ 当前 agent YAML 的 persona sha256,该 record 被 weight × 0.3(PITFALLS §P1 mitigation 4)。
2. **Phase 44 §3.1 row 8 rejection(YAML-not-prompt-dump)。** Persona **不是** SKILL body 的 copy-paste —— SKILL body 是 imperative-second-person user-message("You are X. Do Y.");persona 是 first-person system-prompt fragment("I am X. I do Y.")。Mixing registers 不仅混乱,且 SKILL body 的任何 edit 都会 silently 改变 effective persona —— persona 必须 hand-crafted,且 persona_sha256 锁定其内容。
3. **Curator cannot mutate persona fragment.** `_memory_evolution_phase`(§5)只能 append evolution_log entry 和 write memory record,**禁止**修改 persona YAML field。Same gating pattern as v6.0 bundled-skill protection(`_check_persona_section_intact` from PITFALLS §P1 mitigation 1)。

**Example(ARCHITECTURE §1.3 screenplay persona verbatim):**
```yaml
persona: |
  You are the Screenplay Expert in a Hermes round table. You speak in first
  person about scene structure, Snyder 15-beat adaptation, anchor-based
  emotion curves, and dialogue subtext. You cite save-the-cat-beat-sheet,
  mckee-scene-design, cn-shortdrama-structure, emotion-curve-academic,
  and dialogue-craft from your refs when justifying a recommendation.
  You defer to hook_retention on 3-second hooks and to cinematographer on
  shot intent. You never generate full scripts unprompted — you contribute
  your slice when the orchestrator asks.
```

---

### §2.5 — `tools`(resolves OQ-13:runtime whitelist)

**Type:** `list[string]` · **Constraints:** `min_items: 1` · **Required:** YES · **Default:** —

**Source:** ARCHITECTURE §1.1 row 5. **Purpose:** Runtime tool whitelist。

**PITFALLS mitigation:** —(resolves **OQ-13**)。**OQ-13 resolution:** YES, `tools` 是 runtime whitelist enforced by dispatcher。机制(ARCHITECTURE §4.3 dispatcher pseudocode):当 agent 被 `get_agent_opinion` 调用时,dispatcher spawn 一个 AIAgent fork,传入 `tools_whitelist` arg;该 fork 的 ToolRegistry view 过滤掉不在 whitelist 内的工具。**与 §2.12 `prerequisites.tools` 区别:** `tools` 是 runtime GRANTS(运行时能调什么);`prerequisites.tools` 是 activation CONDITIONS(运行前必须满足什么)。

**Example:**
```yaml
tools: [hermes_llm, read_file, search_files, write_file, patch]  # screenplay
# vs visual_executor:
# tools: [hermes_llm, dreamina_cli, read_file, write_file, patch]
```

---

### §2.6 — `memory_scope`(P4 cross-project leakage mitigation)

**Type:** `enum: shared | per_agent | project_scoped` · **Required:** YES · **Default:** `per_agent`

**Source:** ARCHITECTURE §1.1 row 6(NEW)。**Purpose:** mem0 routing convention。

**PITFALLS mitigation: P4(cross-project leakage)。** `memory_scope=per_agent` 把 records 路由到 `user_id=agent:{name}` namespace(ARCHITECTURE §3.2 Option B)。15 movie-experts 推荐 default `per_agent`。**与 §3.9 memory-record scope 字段区别:** `memory_scope` 决定 records **路由到哪个 mem0 namespace**(coarse-grained);memory-record `scope` 决定 records 在 retrieve 时的 **cross-project visibility**(fine-grained,3-tier global/project/session)。两层隔离协同:memory_scope=per_agent + scope=project = 强隔离;memory_scope=shared + scope=global = 完全共享。

**Example:**
```yaml
memory_scope: per_agent  # default for 15 movie-experts
# shared = v7.0 behavior (cross-agent global user_id)
# project_scoped = user_id=project:{slug}+agent:{name} (most isolated, future use)
```

---

### §2.7 — `lineage`(operator ownership,skill drift detection)

**Type:** `object` ($ref `#/$defs/Lineage`) · **Required:** YES · **Default:** —

**Source:** ARCHITECTURE §1.1 row 7(NEW)+ §6.1 transform procedure。**Purpose:** Records provenance:`{derived_from_skill_id, derived_from_repo, transform_date, transform_notes, skill_sha256}`。Operator-owned。

**PITFALLS mitigation:** —(P14 间接 —— skill_sha256 是 drift detection 的 anchor)。机制(ARCHITECTURE §6.2 drift detection):curator's `_memory_evolution_phase`(§5)在每次 pass 开始时 recomputes SKILL.md 的 sha256,与 `lineage.skill_sha256` 比对。Mismatch 触发 **advisory**(非 automatic re-transform —— ARCHITECTURE §8.2 anti-pattern)。

**Example(ARCHITECTURE §1.3 screenplay lineage verbatim):**
```yaml
lineage:
  derived_from_skill_id: screenplay
  derived_from_repo: kais-hermes-skills
  transform_date: 2026-07-15
  transform_notes: |
    Persona rewritten from SKILL body; SKILL preserved as fallback.
    HOOK-09 emotion_curve marker arrays remain contract-load-bearing.
  skill_sha256: <sha of SKILL.md at transform time>
```

---

### §2.8 — `refs`

**Type:** `list[string]` · **Required:** NO · **Default:** `[]`

**Source:** ARCHITECTURE §1.1 row 8。**Purpose:** RAG reference docs paths。Flattened from SKILL `## References` table。

**PITFALLS mitigation:** —

**Example:**
```yaml
refs:
  - kais-hermes-skills/skills/movie-experts/screenplay/references/save-the-cat-beat-sheet.md
  - kais-hermes-skills/skills/movie-experts/screenplay/references/mckee-scene-design.md
```

---

### §2.9 — `tags`

**Type:** `list[string]` (regex `^[a-z0-9-]+$` per item) · **Required:** NO · **Default:** `[]`

**Source:** ARCHITECTURE §1.1 row 9(SKILL `metadata.hermes.tags` copy)。**Purpose:** Lowercase hyphenated;powers `agents_list` filtering。

**PITFALLS mitigation:** —

**Example:**
```yaml
tags: [movie, screenplay, script, dialogue, narrative, emotion-curve]
```

---

### §2.10 — `expert_id`(FOUND-08 backward-compat)

**Type:** `string` · **Required:** NO · **Default:** —

**Source:** ARCHITECTURE §1.1 row 10(SKILL `metadata.hermes.expert_id` copy)。**Purpose:** Backward-compat anchor。

**PITFALLS mitigation:** —(FOUND-08 preservation rule,Phase 44 决策 1)。**Critical:** 15 个 expert_id 值 verbatim copy,**不可 mutate**。Consumer 仍可用 `expert_id: screenplay` 调用 SKILL;dispatcher 根据当前 agent 的 `default_invocation`(§2.18)决定 route 到 agent 还是 fall through 到 SKILL。

**Example:**
```yaml
expert_id: screenplay  # FOUND-08 frozen — do NOT rename
```

---

### §2.11 — `metrics`

**Type:** `list[string]` · **Required:** NO · **Default:** `[]`

**Source:** ARCHITECTURE §1.1 row 11(SKILL `metadata.hermes.metrics` copy)。**Purpose:** Quality dimensions for eval gate。Carried verbatim so v6.0 eval harness 在 agent outputs 上仍工作。

**PITFALLS mitigation:** —(间接支持 §2.15 fitness_score + P8 mitigation)。

**Example:**
```yaml
metrics: [narrative_tension, dialogue_naturalness, emotional_arc]
```

---

### §2.12 — `prerequisites`(activation conditions)

**Type:** `object` ($ref `#/$defs/Prerequisites`) · **Required:** NO · **Default:** `{}`

**Source:** ARCHITECTURE §1.1 row 12(SKILL `prerequisites` copy)。**Purpose:** Activation conditions。

**PITFALLS mitigation:** —(与 §2.5 `tools` 区别:`prerequisites.tools` 是 activation gate,`tools` 是 runtime whitelist)。

**Example:**
```yaml
prerequisites:
  tools: [hermes_llm]
  skills: []
  env: []
```

---

### §2.13 — `related_agents`(collaboration DAG)

**Type:** `list[string]` (regex `^[a-z0-9_-]+$`) · **Required:** NO · **Default:** `[]`

**Source:** ARCHITECTURE §1.1 row 13(SKILL `metadata.hermes.related_skills` copy + rename)。**Purpose:** Collaboration DAG。Drives round table panel suggestions(02-ROUND-TABLE-PROTOCOL.md consumer)。

**PITFALLS mitigation:** —

**Example:**
```yaml
related_agents: [style_genome, editor, audio_pipeline, compliance_gate, hook_retention, cinematographer, theory_critic]
```

---

### §2.14 — `evolution_log`(P5 curator failure modes mitigation)

**Type:** `list[object]` ($ref `#/$defs/EvolutionLogEntry`) · **Required:** NO · **Default:** `[]`

**Source:** ARCHITECTURE §1.1 row 14(NEW)。**Purpose:** Curator-managed, append-only, sha256-chained log。**DO NOT hand-edit —— curator is the only writer。**

**PITFALLS mitigation: P5(curator failure modes)。** 字段级机制:

1. **Tamper-evident sha256 chain.** 每 entry 的 `sha256` = SHA-256 of (prev_entry.sha256 + canonical_json(new_entry_payload))。Genesis entry sha256 = SHA-256("")。Same pattern as v6.0 `agent/curator_audit.py`(shipped)。`hermes curator audit-log --verify` walks the chain and flags breaks。
2. **persona_sha256 per entry.** 每条 entry 带当时的 persona hash;形成 P1 cross-layer detection network(与 §3.11 memory-record persona_sha256 协同)。
3. **Dry-run-by-default writes(§5.2)。** Curator 默认 dry-run;mutation 需 explicit operator flag。`TestNonBypassableHumanInLoop` ast-walk invariant extends to memory writes(same pattern as v6.0 `apply_patch_transaction`)。
4. **Evidence coverage check.** 每条 evolution_log entry 引用至少 3 个 evidence source(PITFALLS §P5 mitigation 2;实际 evidence 存在 memory record 的 evidence_chain,§3.6)。
5. **`trigger` enum.** 5 sources(feedback / eval_gate / operator_edit / round_table / external)+ bias_canary。bias canary 触发的 entry 标记 quarantined memory。

**Example(genesis entry + 1 evolution):**
```yaml
evolution_log:
  - ts: 2026-07-15T10:00:00Z
    sha256: "<sha of genesis>"
    diff_summary: "Initial transform from SKILL.md"
    fitness_delta: 0.0
    trigger: operator_edit
    persona_sha256: "<sha of v1 persona>"
  - ts: 2026-07-22T03:14:00Z
    sha256: "<sha chaining to prev>"
    diff_summary: "After Volvo S1-1 case, cinematographer learned LHD declaration"
    fitness_delta: 0.12
    trigger: feedback
    persona_sha256: "<sha of v1 persona — unchanged>"
```

---

### §2.15 — `fitness_score`(P8 + OQ-4 cold start)

**Type:** `float (0.0-1.0) | null` · **Required:** NO · **Default:** `null`

**Source:** ARCHITECTURE §1.1 row 15(NEW)。**Purpose:** Curator-computed rolling quality score。**NOT operator-set。**

**PITFALLS mitigation: P8(no fitness signal)+ OQ-4(cold start)。**

- **P8 mitigation:** `fitness_score` 是 agent-YAML-side carrier。完整 P8 mitigation(fitness battery yaml / fitness_trend.jsonl / A/B shadow mode / model_id isolation)deferred to 05-POC-PLAN.md(§7.2 audit)。
- **OQ-4 resolution:** `null = neutral 0.5` for ordering。Orchestrator 的 turn_order computation 把 `null` 当作 `0.5` 处理;UI 显示 "untested" badge。

**Example:**
```yaml
fitness_score: null  # initial state — UI shows "untested"
# After 3 curator passes:
# fitness_score: 0.78
```

---

### §2.16 — `platforms`

**Type:** `list[string]` (enum `[linux, macos, windows, termux]`) · **Required:** NO · **Default:** `[linux, macos, windows]`

**Source:** ARCHITECTURE §1.1 row 16(SKILL `platforms` copy)。**Purpose:** OS compatibility gate。

**PITFALLS mitigation:** —

**Example:**
```yaml
platforms: [linux, macos, windows]  # default — most movie-experts
```

---

### §2.17 — `round_table_eligible`

**Type:** `bool` · **Required:** NO · **Default:** `true`

**Source:** ARCHITECTURE §1.1 row 17(NEW)。**Purpose:** Whether this agent can be invited to a round table。Set `false` for ephemeral helpers / read-only analysts。

**PITFALLS mitigation:** —

**Example:**
```yaml
round_table_eligible: true  # default for 15 movie-experts
```

---

### §2.18 — `default_invocation`

**Type:** `enum: mcp_tool | skill_fallback | disabled` · **Required:** NO · **Default:** `mcp_tool`

**Source:** ARCHITECTURE §1.1 row 18(NEW)。**Purpose:** Dispatcher mode。

**PITFALLS mitigation:** —(FOUND-08 additive transition)。三个 enum 的使用场景:

- **`mcp_tool`(default):** agent round-table-ready;通过 `get_agent_opinion` MCP tool 调用。15 movie-experts 在 v11.0 PoC 完成后全部进入此状态。
- **`skill_fallback`:** fall through to underlying SKILL(v1-v9 behavior)。**Additive transition per FOUND-08** —— SKILL 在 migration 期间仍可被 `expert_id` 调用。15-expert migration(04-MIGRATION-PATH.md)期间使用此值,逐步切到 `mcp_tool`。
- **`disabled`:** agent 在 registry 中存在但不可被调用。用于 transform-in-progress 状态(如 operator 正在 rewrite persona,临时禁用 dispatcher)。

**Example:**
```yaml
default_invocation: mcp_tool  # final state for 15 movie-experts
# During migration: default_invocation: skill_fallback
```

---

## §3 — Memory-Record Schema:Layer 2 Narrative(10 mandated fields + persona_sha256 + schema_version)

### §3.0 — 本节结构声明 + 2-Layer 重申(CC-2)

memory-record schema 是**独立 layer 2**(CC-2 mandate)。每条记录存于 mem0 backend 的 per-agent namespace(`user_id=agent:{name}`),携带 10 个不变量字段 + `persona_sha256` cross-layer invariant + `schema_version` 迁移 key + audit fields + content。机器可读 schema 见 `memory-record-schema.yaml`(JSON Schema draft 2020-12,`additionalProperties: false`)。

**为什么独立 layer?(§1.1 重申)** 生命周期不同(operator-owned vs curator+multi-src)、不变量粒度不同(sha256 chain vs time-decay + evidence + scope + confidentiality)、变更频率不同(YAML 几乎不变 vs records 高频变化)。合并会模糊 ownership boundary。

每个 §3.N 子节遵循 4-block scaffold parallel to §2:

1. **Type + Constraints + Default** —— 从 memory-record-schema.yaml 抄录
2. **PITFALLS source** —— P1/P2/P4/P5/P6/P8/P10/P14
3. **Mechanism** —— explicit 字段级缓解机制
4. **Example value** —— YAML 片段

---

### §3.1 — `expires_at`(P2 hard expiry)

**Type:** `string (date-time) | null` · **Default:** `null`(preference memories)/ `now + 90 days`(domain-rule memories)

**PITFALLS source:** §P2 mitigation 1。

**Mechanism:** Hard expiry timestamp。After this timestamp, status auto-flips to `archived` by compaction pass(§4.5 of design doc)。Retrieve-time filter:`WHERE expires_at IS NULL OR expires_at > now()`。Domain-rule memories(platform guidelines, model APIs, tool versions)由 curator 在 write path 设 `expires_at = now + 90 days`(config: `memory.default_domain_ttl_days: 90`);preference memories(operator tastes, project conventions)`expires_at = null`(never expires)。

**Example:**
```yaml
expires_at: "2026-10-15T00:00:00Z"  # domain rule — 90 days TTL
# vs preference:
# expires_at: null
```

---

### §3.2 — `verified_at`(P2 periodic re-verification)

**Type:** `string (date-time) | null` · **Default:** `null`(never verified)

**PITFALLS source:** §P2 mitigation 2(mirrors v1 ref `verified_date` convention)。

**Mechanism:** Last human/curator verification timestamp。Curator's periodic re-verification pass walks memories with `verified_at > 90 days`,flags them for re-verification。External-change detection hooks(P2 mitigation 3):for memories citing upstream URL,curator fetches + hashes + compares to `source_content_sha256`;mismatch → auto-quarantine。

**Example:**
```yaml
verified_at: "2026-07-15T10:00:00Z"
```

---

### §3.3 — `supersedes_memory_id`(P2 supersession chain)

**Type:** `string | null` · **Default:** `null`

**PITFALLS source:** §P2 mitigation 4(extends v6.0 `_superseded_record_ids` from feedback_store.py)。

**Mechanism:** Points to the `record_id` this record replaces。Forms supersession chain。Example:screenplay learns "FLUX 2 replaces FLUX 1.x" → curator writes new memory with `supersedes_memory_id=<old FLUX 1 memory's record_id>`。Retrieve-time filter excludes superseded records(mirrors `_superseded_record_ids` set in feedback_store.py)。

**Example:**
```yaml
supersedes_memory_id: "01HXY9abcdefghijklmnopqrstuvwxyz012345"  # old FLUX 1 memory
```

---

### §3.4 — `confidence`(P2 time-decay + OQ-4 neutral 0.5)

**Type:** `number (0.0-1.0)` · **Default:** `0.5`

**PITFALLS source:** §P2 mitigation 5(time-decay applied to confidence)。**OQ-4 resolution:** 0.5 = neutral;mirrors fitness_score `null → 0.5` mapping in agents-schema.yaml。

**Mechanism:** Curator-assigned base confidence。**Retrieve-time time-decay formula:**
```
confidence(now) = base_confidence * exp(-age_days / half_life_days)
```
Below `confidence = 0.1` → auto-archived by compaction pass(§4.5 of design doc)。v6.0 `compute_weight(ts)` decays retrieval weight;THIS field decays **correctness**, not just retrieval weight。两个 decay 是 independent。

**Example:**
```yaml
confidence: 0.85  # base — will decay per half_life_days
```

---

### §3.5 — `half_life_days`(P2 time-decay rate)

**Type:** `integer (≥1)` · **Default:** `90`(domain-rule)/ `3650`(preference)

**PITFALLS source:** §P2 mitigation 5。

**Mechanism:** Days for confidence to halve。Domain-rule memories(platform guidelines, model APIs, tool versions):`half_life_days = 90`(short,fast decay)。Preference memories(operator tastes, project conventions):`half_life_days = 3650`(long,slow decay)。Curator's memory-write path infers `half_life_days` from the LLM aggregation step's classification(domain-rule vs preference)。

**Example:**
```yaml
half_life_days: 90  # domain rule — fast decay
# vs preference:
# half_life_days: 3650  # ~10 years — slow decay
```

---

### §3.6 — `evidence_chain`(P5 curator hallucination guard)

**Type:** `list[object]` · **Constraints:** `minItems: 3` · **Default:** —

**PITFALLS source:** §P5 mitigation 2(hallucination guard: citation coverage ≥ 3)。

**Mechanism:** ≥3 independent sources required before curator promotes a memory。Each item is `{source_type, source_id, timestamp, excerpt?}`。`source_type` enum:`feedback | eval_gate | operator_edit | round_table | external`。Curator's LLM is prompted to cite;post-hoc `_check_evidence_coverage(new_memory, evidence_chain) -> bool` verifies each cited record's text actually overlaps the new memory semantically(embedding cosine ≥ 0.7)。Failures rejected(record not written)。

**Example:**
```yaml
evidence_chain:
  - source_type: feedback
    source_id: "<sha of FeedbackRecord>"
    timestamp: "2026-07-22T03:14:00Z"
    excerpt: "Volvo S1-1 case: LHD declaration missing in initial draft"
  - source_type: round_table
    source_id: "rt_20260722_153000_a1b2c3"
    timestamp: "2026-07-22T04:00:00Z"
    excerpt: "Cinematographer + Continuity agreed on LHD rule"
  - source_type: operator_edit
    source_id: "kai@2026-07-22"
    timestamp: "2026-07-22T05:00:00Z"
    excerpt: "Confirmed: all car-interior shots need LHD declaration"
```

---

### §3.7 — `evidence_operator_ids`(P5 bias amplification guard)

**Type:** `list[string]` · **Constraints:** `minItems: 1`(recommended ≥ 2 for auto-promotion)

**PITFALLS source:** §P5 mitigation 3(operator diversity score)。

**Mechanism:** Operators who contributed evidence。Curator's pre-write check:`_check_operator_diversity(evidence_chain, 2)` requires ≥2 distinct operators before generating an insight。Single-operator feedback cannot drive automated memory writes。Bias audit log:every memory write records `evidence_operator_ids + count`;`hermes curator stats --bias-audit` surfaces over-represented operators。

**Example:**
```yaml
evidence_operator_ids: [kai, kim]  # 2 distinct — eligible for auto-promotion
```

---

### §3.8 — `status`(P5/P6 curator failure + memory poisoning)

**Type:** `enum: active | archived | quarantined | superseded` · **Default:** `active`

**PITFALLS source:** §P5 mitigation 1(never hard-delete)+ §P6 mitigation 6(quarantine on poisoning)。

**Mechanism:** Lifecycle status。`active` = eligible for retrieval。`archived` = excluded from default retrieval,kept for audit。`quarantined` = under review(bias canary / poisoning suspected / operator disputed);excluded until operator resolves。`superseded` = replaced by supersedes_memory_id chain;excluded,kept for audit(P2 mitigation 4)。**Curator can only archive,never hard-delete**(P5 mitigation 1 invariant)。

**Example:**
```yaml
status: active
# After compaction pass demotes this record:
# status: archived
```

---

### §3.9 — `scope`(P4 cross-project leakage,finer than memory_scope)

**Type:** `enum: global | project | session` · **Default:** `project`(conservative default per P4 mitigation 2)

**PITFALLS source:** §P4 mitigation 1(three-tier scoping)。**FINER than agents-schema memory_scope**(shared | per_agent | project_scoped)—— memory_scope routes records by agent_id;THIS field governs cross-project VISIBILITY at retrieve time。

**Mechanism:** `global` = eligible for cross-project retrieval(e.g. "FLUX 2 generates better faces than FLUX 1")。`project` = retrieve ONLY when `project_id` matches current context(e.g. "this project's protagonist is introspective, prefers muted palette")。`session` = ephemeral, single-conversation(mirrors current mem0 run_id semantics)。**Default = project**(P4 mitigation 2:conservative prevents inappropriate cross-project transfer)。Cross-project promotion from `project` → `global` requires curator review + operator approval(P4 mitigation 5,mirrors v6.0 `apply_patch_transaction` gating)。

**Example:**
```yaml
scope: project  # default — conservative
project_id: "hermes-agent:a1b2c3d4"  # required when scope=project
```

---

### §3.10 — `confidentiality`(P10 privacy / data leakage)

**Type:** `enum: public | internal | confidential | restricted` · **Default:** `internal`

**PITFALLS source:** §P10 mitigation 2。

**Mechanism:** Propagation rule across projects/sessions。`public` = any context。`internal` = default;only within operator's Hermes deployment。`confidential` = project-specific sensitive;excluded from cross-project retrieval even if scope=global。`restricted` = NDA / PII / secrets;excluded from all automated retrieval;only surfaced via explicit operator command。Round-table coordinator broadcasts project's confidentiality level;participants filter retrieval(`retrieve(query, project_id, confidentiality_filter="≤ current project's level")`)。

**PoC must-fix status:** v11.0 PoC ships with `public/internal/confidential`;`restricted` tier + PII vault deferred to v11.1(see §7.2 P10 row)。

**Example:**
```yaml
confidentiality: internal  # default
# vs sensitive project data:
# confidentiality: confidential
```

---

### §3.11 — `persona_sha256`(OQ-1 resolution + P1 cross-layer drift detection)

**Type:** `string` (regex `^[a-f0-9]{64}$`) · **Required:** YES · **Default:** —

**PITFALLS source:** §P1 mitigation 4(persona-versioned memory records)+ **OQ-1 resolution**(Phase 44 SUMMARY)。

**Mechanism:** SHA-256 of the agent's persona fragment AT THE TIME this record was written。**Cross-layer invariant for P1 persona drift detection:**

- At recall time,if this record's `persona_sha256` ≠ current agent YAML persona sha256 → flag for re-verification(operator may have hand-edited persona;record may no longer apply)
- Retrieve-time weight:`persona_version_match ? 1.0 : 0.3`(memory written under persona v1 doesn't dominate behavior under persona v2)
- 与 §2.4 persona_sha256 invariant + §2.14 evolution_log entry persona_sha256 协同 —— 三处 sha256 形成 cross-layer detection network

**Example:**
```yaml
persona_sha256: "a1b2c3d4e5f6...<64 chars total>"  # hex sha256 of v1 persona
```

---

### §3.12 — `schema_version`(P14 schema migration)

**Type:** `string` (semver) · **Default:** `"1.0.0"`

**PITFALLS source:** §P14 mitigation 1。

**Mechanism:** Version of memory-record schema this record conforms to。**Migration job backfills unknown fields with safe defaults**(P14 mitigation 2:"default unknown fields to the safest value,not the most permissive" —— e.g. unknown `confidentiality` → `confidential`,NOT `public`)。**Migration dry-run:** `hermes agent memory migrate --dry-run`(P14 mitigation 3,see 04-MIGRATION-PATH.md)。v11.0 PoC ships with `schema_version="1.0.0"`;subsequent field additions bump this in lockstep with agents-schema.yaml `version`。

**Example:**
```yaml
schema_version: "1.0.0"  # v11.0 PoC initial schema
```

---

## §4 — Per-Agent Memory Tier:Core / Working / Archival

### §4.0 — 本节结构声明 + 3-Tier 加严理由(P3 + P9)

v10.0 把 per-agent memory **显式分为 3 tier**(core / working / archival),不是单一 namespace。这是 PITFALLS §P3(scoped retrieval performance collapse)+ §P9(memory size growth)加严 —— 单层 mem0 namespace 在 500 records 时会因 HNSW 全局图退化(post-filter scanning 50-100× more nodes than necessary,P3 mitigation 1)。分层后:

- **Core tier** 始终 ≤ 50 records(常驻 agent persona fragment + immutable operator facts),保证 O(ms) retrieval
- **Working tier** ≤ 200 records(默认 retrieval target,mem0 status=active)
- **Archival tier** ≤ 250 records(status=archived;只在 working miss 时检索)

**Layer-2 `memory-record-schema.yaml` 的 `status` field**(`active | archived | quarantined | superseded`)对应 working / archival tier 的切换。Core tier **不是独立 mem0 namespace** —— 它是常驻 agent persona 的 immutable operator facts(写死在 YAML + persona_sha256 锁定,§2.4)。这样 core tier 不参与 HNSW retrieval 性能问题,直接拼入 system prompt。

**3-tier aggregate cap = 500 records per agent(OQ-7 resolution,详见 §4.4)。**

---

### §4.1 — Core tier(persona-aligned,always-loaded)

**Location:** Agent YAML `persona` fragment(§2.4)+ `lineage.transform_notes` immutable facts(if any)+ immutable system facts(e.g. "agent is the Screenplay Expert")。

**max_records:** ~50(effectively bounded by persona length —— operator 写 persona 时已控制)。

**Retrieval:** **Always loaded into system prompt**;no mem0 query。每次 agent 被 `get_agent_opinion` 调用时,persona 直接拼入 system_prompt_override(ARCHITECTURE §4.3 dispatcher pseudocode)。

**Writes:** **Operator-only**(YAML edits via hand-edit 或 future `hermes agent transform` CLI)。Curator 不能 mutate core tier(§2.4 P1 mitigation 3)。

**PITFALLS mitigation:**
- **P1(persona drift):** `persona_sha256` invariant locks the content。任何 persona edit 都会改变 sha256,触发 cross-layer re-verification(§3.11)
- **P5(curator failure modes):** curator 写 memory record 时不能污染 core tier —— core tier 在 YAML 不在 mem0

**Example:** 见 §2.4 screenplay persona —— 那 7 行 first-person text 就是 core tier 的内容。

---

### §4.2 — Working tier(default retrieval target,active records)

**Location:** mem0 backend,`agent_id` namespace,**`status=active` records**。`memory-record-schema.yaml` 的 `status` field 决定归属(`active` = working)。

**max_records:** ~200(default retrieval target;OQ-7 aggregate cap 500 的一部分)。

**Retrieval:** Every `get_agent_opinion` call queries this tier。Retrieve API:`retrieve(query, agent_id, project_id, scope_filter, status="active")`。返回 top-5 records 拼入 system prompt(在 persona 之后,retrieved-memory block)。

**Writes:**
- Curator `_memory_evolution_phase`(§5)writes new records here
- Round table conclusions(`trigger=round_table`)with `project_id` set
- Operator explicit `mem0_conclude` calls

**PITFALLS mitigation:**
- **P2(stale memory):** `expires_at` + `verified_at` + `half_life_days` time-decay;out-of-date records auto-demoted to archival by compaction pass(§4.5)
- **P4(cross-project leakage):** `scope=project`(default)+ `project_id` required;records 不跨 project retrieve unless scope=global
- **P5(curator failure modes):** `evidence_chain ≥ 3` + `evidence_operator_ids` diversity before write

---

### §4.3 — Archival tier(historical + low-confidence,miss-fallback)

**Location:** mem0 backend,`agent_id` namespace,**`status=archived | superseded` records**。

**max_records:** ~250(OQ-7 aggregate cap 500 的一部分)。

**Retrieval:** **Only on working-tier miss** OR explicit operator query(`hermes agent memory recall --include-archival`)。Retrieve API:`retrieve(query, agent_id, project_id, status="archived|superseded")`。

**Writes:**
- Compaction pass(§4.5)demotes working → archival when records are stale / low-confidence / superseded
- Explicit `supersedes_memory_id` chain creates `status=superseded` records

**PITFALLS mitigation:**
- **P9(memory size growth):** archival tier 提供 graceful degradation —— 旧数据不被删,只是不默认 retrieve。Operator 可手动 promote archival → working if needed。
- **P5(curator failure modes):** archived records kept for audit;`hermes curator audit-log --verify` walks supersession chains。

---

### §4.4 — max_records 上限:500 aggregate(OQ-7 resolution)

**OQ-7 resolution:** `memory.max_records` 默认 **500 records per agent**,作为 3-tier aggregate cap(working + archival;core tier 在 YAML 不计 mem0)。

**Cap breakdown(默认值,可 config 调):**

| Tier | Default cap | Source |
|------|-------------|--------|
| Core | ~50(bounded by persona length) | Operator-curated |
| Working | ~200 | PITFALLS §P3 mitigation 3 + §P9 |
| Archival | ~250 | PITFALLS §P9 |
| **Total aggregate** | **500** | **OQ-7 resolution** |

**Trigger threshold:** 当 `working + archival > 450`(90% cap)时,**触发 compaction pass**(§4.5)。

**PITFALLS citations:** §P3 mitigation 3(per-agent memory budget cap)+ §P9 mitigation 1(same,reinforcing)。Config:`agent.memory.max_records: 500`(per-agent override possible in agent YAML `prerequisites.env` or future field)。

**OQ-7 deferred to v11.0 PoC(§7.1 audit row):**
- 具体 compaction 算法(how to select which 50 working records to demote when cap exceeded)
- compaction pass 的 N tick 间隔(`interval_hours` —— v6.0 default 7 days,可能需要 v10.0 独立 cadence)
- fitness_score 与 archival promote/demote 的 coupling

---

### §4.5 — Compaction trigger + behavior

Compaction pass 是 curator's periodic maintenance job(hook into `_memory_evolution_phase`,§5.4 per-agent iteration 的最后一步)。Trigger conditions + actions:

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Aggregate cap pressure | `working + archival > 450`(90%) | Demote lowest-`confidence` working records to archival until ≤ 400 |
| Hard expiry | `record.expires_at < now` | Auto-flip `status: active → archived`;log to curator_audit |
| Time-decay collapse | `record.confidence(now) < 0.1` (after half_life decay) | Demote `working → archival` |
| Supersession | `record.status = superseded`(set by another record's `supersedes_memory_id`) | Demote `working → archival`(keep for audit) |
| Bias canary flag | Operator disputes record; bias canary triggers | Flip `status: active → quarantined`;exclude from retrieval until resolved |
| Archival overflow | `archival tier > 250` | Drop lowest-`confidence` archived records;log to curator_audit |

**Never hard-delete invariant(P5 mitigation 1):** Compaction can only demote / quarantine / drop-archived-with-lowest-confidence。Original records stay in audit log(sha256-chained)。Restore is one CLI call(`hermes agent memory restore --record-id <id>`)。

**Drop heuristic for archival overflow:** Select archived records with lowest `confidence × recall_count` score;this favors dropping records that are both low-confidence AND rarely-recalled。Log dropped record IDs + content hashes to curator_audit for traceability。

---

### §4.6 — 3-Tier ASCII Tier Diagram(retrieval + write + compaction flow)

```
┌────────────────────────────────────────────────────────────────────────┐
│ CORE TIER (operator-owned, always-loaded)                              │
│ Location: agent YAML persona (§2.4) + lineage.transform_notes          │
│ Retrieval: ALWAYS injected into system prompt (no mem0 query)          │
│ Writes: operator-only (hand-edit or future `hermes agent transform`)   │
│ PITFALLS: P1 (persona_sha256 invariant)                                │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ system prompt includes persona
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ WORKING TIER (default retrieval target, status=active)                 │
│ Location: mem0 backend, agent_id namespace                             │
│ Cap: ~200 records (default retrieval target)                           │
│ Retrieval: every get_agent_opinion call queries this tier              │
│   - WHERE agent_id=<agent> AND status=active                           │
│   - AND (expires_at IS NULL OR expires_at > now())                     │
│   - AND project_id matches (if scope=project)                          │
│   - ORDER BY confidence DESC LIMIT 5                                   │
│ Writes: curator _memory_evolution_phase / round_table / operator       │
│ PITFALLS: P2 (time-decay) + P4 (scope isolation) + P5 (evidence ≥3)    │
└────────────────────────────────────────────────────────────────────────┘
                                    │
            ┌───────────────────────┴───────────────────────┐
            │                                               │
            │ Compaction pass triggers (§4.5):              │
            │  - cap > 90% → demote lowest-confidence       │
            │  - expires_at < now → auto-archive            │
            │  - confidence < 0.1 → demote                  │
            │  - status=superseded → demote                 │
            │                                               │
            ▼                                               ▼
┌──────────────────────────────────────────────────┐  ┌──────────────────────────────────────────┐
│ ARCHIVAL TIER (miss-fallback, status=archived|   │  │ QUARANTINE (incident response,           │
│   superseded)                                    │  │   status=quarantined)                     │
│ Location: mem0 backend, same agent_id namespace  │  │ Location: mem0 backend, excluded from     │
│ Cap: ~250 records                                │  │   retrieval until operator resolves       │
│ Retrieval: ONLY on working-tier miss OR explicit │  │ Triggers: bias canary / poisoning         │
│   `--include-archival` operator query            │  │   suspected / operator disputed           │
│ PITFALLS: P9 (graceful degradation, no data loss)│  │ PITFALLS: P5 mitigation 6 + P6 mitigation 6│
└──────────────────────────────────────────────────┘  └──────────────────────────────────────────┘
```

**Flow summary:**
1. Every `get_agent_opinion` call: core tier from YAML + working tier top-5 from mem0
2. Compaction pass(§4.5)demotes working → archival / quarantine based on triggers
3. Working-tier miss → operator can explicitly query archival tier
4. Quarantine records excluded from all automated retrieval;restore requires operator command

---

## §5 — Curator `_memory_evolution_phase` Field Contract(OQ-16 resolution)

### §5.0 — 本节声明:additive extension of v6.0 `_feedback_scan_phase`

`_memory_evolution_phase` 是 v6.0 `_feedback_scan_phase` 的 **additive extension** —— 不替换、不并行,在 `_feedback_scan_phase` 之后**串行插入**。Pattern 来自:

- **v6.0 FOUND-06 additive phase discipline:** New background behaviors are added as new phases in `run_curator_review`,NOT as separate daemons(ARCHITECTURE §7.2 pattern:Additive Curator Phase)
- **Phase 44 §1.3 paradigm shift:** Agent 是 Hermes-side 独立实体,curator 是其自进化机制。Curator 既 scan SKILL feedback(v6.0),也 scan agent memory evolution(v10.0 新加)。

**Resolves OQ-16(详见 §5.1-§5.3)。**

---

### §5.1 — Execution order(AFTER `_feedback_scan_phase`,never before,never parallel)

**OQ-16 resolution:** `_memory_evolution_phase(start)` runs **immediately AFTER** `_feedback_scan_phase(start)` in `_llm_pass()`,in the same `_llm_pass` block。

**Hook location:** `agent/curator.py` lines 2081-2095 + 2207-2221(两个 `_feedback_scan_phase` hook 点 —— `_llm_pass` 函数内的两段)。新增 `_memory_evolution_phase` call 紧跟在每段 `_feedback_scan_phase` call 之后。

**Pseudo-code(agent/curator.py 的 `_llm_pass` sketch,v11.0 PoC 实施 target):**

```python
def _llm_pass(self, start: datetime):
    """v10.0 extended: feedback scan + memory evolution in sequence."""
    # ... existing v6.0 logic above ...

    # v6.0 _feedback_scan_phase (shipped)
    try:
        feedback_summary = _feedback_scan_phase(start)
        # logs to curator.log + curator_audit
    except Exception as exc:
        log_warning("_feedback_scan_phase failed: %s", exc)
        feedback_summary = {"scanned": 0, "evolved": []}

    # v10.0 NEW _memory_evolution_phase (additive, AFTER feedback_scan)
    try:
        memory_summary = _memory_evolution_phase(start)
        # logs to curator.log + curator_audit
    except Exception as exc:
        log_warning("_memory_evolution_phase failed: %s", exc)
        memory_summary = {"agents_walked": 0, "memory_facts_synthesized": 0}

    # ... existing v6.0 logic below ...

    return {
        **feedback_summary,
        "memory_evolution": memory_summary,  # additive key
    }
```

**Why AFTER and not BEFORE?** Memory evolution depends on feedback signals —— 先 feedback scan(聚合 new feedback since last pass),再 memory evolution(基于 feedback signals 决定哪些 memory 需 update)。Reverse order 会丢失本轮 feedback 的贡献。

**Why NOT parallel?** Two phases share the same LLM client(pool);parallel 会 double LLM cost + race on agent YAML writes(evolution_log append)。串行更安全。

---

### §5.2 — Dry-run-by-default contract

**Discipline:** New phase defaults `dry_run=True`。Memory writes(mem0_conclude calls)在 dry-run mode 下被 skipped;only summary dict returned。**Mutation requires explicit operator flag**(二选一):

- Env var:`HERMES_CURATOR_MEMORY_EVOLUTION_LIVE=1`
- CLI flag:`hermes curator run --live-memory-evolution`

**Sources:** v6.0 FOUND-06 discipline + PITFALLS §P5 mitigation 5(curator failure modes —— operator retains ownership of memory state)。

**Why dry-run-by-default?** Per PITFALLS §P5 mitigation 5:"curator's memory-write path is dry-run by default,requires explicit `--apply-memory` flag for live writes。Same ast-walk invariant pattern as `TestNonBypassableHumanInLoop`。" Operator 必须 explicitly opt-in to mutation,防止 curator bug silently 污染 memory store。

**Test invariant(v11.0 PoC):** `TestNonBypassableHumanInLoop` ast-walk extends to cover `_memory_evolution_phase`'s mem0_conclude calls —— only callable from `hermes_cli/feedback.py:_cmd_approve` 或 explicit `--live-memory-evolution` CLI path。

---

### §5.3 — try/except isolation contract

**Discipline:** Wrap entire `_memory_evolution_phase` body in try/except。On Exception:

1. Log warning with stack trace to `errors.log` + `curator.log`
2. Append error entry to `curator_audit.jsonl`(sha256-chained)
3. Return `{"agents_walked": 0, "memory_facts_synthesized": 0, "errors": [str(exc)]}` summary dict
4. **Never propagate up** to crash `run_curator_review`

**Boundary:** Same isolation boundary as `_feedback_scan_phase`。One phase's failure never crashes the other。

**Pseudo-code:**
```python
def _memory_evolution_phase(start: datetime) -> Dict[str, Any]:
    """ADDITIVE per-agent memory evolution phase. OQ-16 resolution."""
    try:
        # ... walk ~/.hermes/agents/*.agent.yaml ...
        # ... per-agent iteration (§5.4) ...
        return {
            "agents_walked": N,
            "memory_facts_synthesized": M,
            "memory_facts_written": W,  # 0 in dry-run
            # ... etc ...
        }
    except Exception as exc:
        logger.warning("_memory_evolution_phase failed: %s", exc, exc_info=True)
        append_audit(action="memory_evolve_error", error=str(exc))
        return {"agents_walked": 0, "memory_facts_synthesized": 0, "errors": [str(exc)]}
```

---

### §5.4 — Per-agent iteration contract

**Discipline:** Walks `~/.hermes/agents/*.agent.yaml`(ARCHITECTURE §4.1 sibling scanner)。For each agent with `memory_scope == "per_agent"`:

1. **Load YAML + evolution_log。** Parse via `agent/skill_utils.parse_frontmatter` generalization(ARCHITECTURE §4.1 `_discover_agents` pseudocode)。
2. **Walk evolution_log since last phase run**(`start` param = `last_memory_evolution_at` from `.curator_state`)。Filter entries with `trigger in (feedback, eval_gate)` —— these are candidates for memory synthesis。
3. **For each candidate entry with `trigger=feedback` or `trigger=eval_gate`:**
   - Validate `evidence_chain`(≥3 sources per P5 mitigation 2)
   - Validate `evidence_operator_ids`(≥2 distinct operators per P5 mitigation 3,recommended)
   - If valid:**synthesize memory fact via LLM consolidation**(reuse `_feedback_scan_phase` LLM helper from v6.0)
   - **Optional write:** `mem0_conclude` scoped to `agent_id` via `_scoped_agent_id` contextvars(§5.5)
4. **Append new evolution_log entry** with sha256 chain(`trigger=feedback` or `trigger=eval_gate`,`persona_sha256=<current>`,`fitness_delta=<delta>`)。
5. **Update `fitness_score`** if eval_gate evidence present(P8 mitigation)。
6. **Run compaction pass**(§4.5)if `working + archival > 450`。

**Skip agents with:** `memory_scope == "shared"`(uses global mem0 namespace,no per-agent memory to evolve)/ `default_invocation == "disabled"`(transform-in-progress,do not touch)。

---

### §5.5 — mem0_conclude integration(`_scoped_agent_id` contextvars pattern)

**Discipline:** When writing memory via `mem0_conclude`,the phase **sets `provider._scoped_agent_id = agent_name`** before the call;resets in `finally` block。Thread-safe via `contextvars`(matches `agent/tool_executor.py` ThreadPoolExecutor pattern)。

**Source:** ARCHITECTURE §3.3 `_scoped_agent_id` contextvars pattern。

**Pseudo-code:**
```python
import contextvars

_scoped_agent_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "_scoped_agent_id", default=None
)

def _set_memory_agent_scope(agent_name: Optional[str]) -> None:
    _scoped_agent_id.set(agent_name)

def invoke_agent_with_memory(agent_name: str, query: str) -> str:
    provider = _get_active_memory_provider()
    token = _scoped_agent_id.set(agent_name)
    try:
        return agent_registry.dispatch(agent_name, query)
    finally:
        _scoped_agent_id.reset(token)
```

**Why contextvars and not threading.local?** Hermes uses `ThreadPoolExecutor` for concurrent tool execution(`agent/tool_executor.py:110`)。`threading.local` 会 leak scope across task boundaries in the same worker thread;`contextvars` 自动 isolate per-task。**v11.0 PoC must use contextvars**(SUMMARY.md Gaps to Address)。

---

### §5.6 — Return shape(parallel to `_feedback_scan_phase`)

**Discipline:** Returns `Dict[str, Any]` parallel to `_feedback_scan_phase` return shape。Keys:

```python
{
    "agents_walked": int,                  # 总共 walk 多少个 agent YAML
    "memory_facts_synthesized": int,       # LLM consolidation 生成的 memory fact 总数
    "memory_facts_written": int,           # 实际写入 mem0 的数量(0 in dry-run)
    "evidence_chain_failures": int,        # 因 evidence < 3 被拒的候选数
    "operator_diversity_failures": int,    # 因 operator 单一被拒的候选数
    "fitness_score_updates": int,          # fitness_score 调整的 agent 数
    "compaction_passes_triggered": int,    # compaction 触发次数
    "errors": [str, ...],                  # per-agent error logs(if any)
    "duration_seconds": float,             # 总耗时
}
```

**Logging:** Summary dict appended to `curator_audit.jsonl`(sha256-chained,v6.0 pattern)。`hermes curator stats --memory-evolution` renders sparkline of last N runs。

**Operator observability:** Operator 可 `hermes curator stats --memory-evolution --bias-audit` 查看:

- 哪些 agent 在过去 N runs 中 fitness_score 上升 / 下降
- 哪些 operator 在 evidence_operator_ids 中占比 >50%(bias 警告)
- 哪些 memory record 因 evidence 不足被拒
- 哪些 compaction pass 触发了 drop

**Curator state extension:** `.curator_state` 新增 `"last_memory_evolution_at": ISO_ts` 字段,确保 evolution phase 每 `interval_hours` 周期最多跑一次(matches existing cadence discipline)。

---
