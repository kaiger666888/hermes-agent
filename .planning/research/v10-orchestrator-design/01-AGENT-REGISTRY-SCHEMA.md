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



