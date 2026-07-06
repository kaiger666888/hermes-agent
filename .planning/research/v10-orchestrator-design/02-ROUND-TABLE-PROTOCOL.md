# 02 — Round Table Protocol:v10.0 多 Agent 协商层(协议契约物理载体)

> **Document status:** design-2026-07-06-v10roundtable · supersedes: none · superseded_by: TBD
> **Milestone:** v10.0 — Hermes-Agent 编排架构第一性原理推导(设计型 milestone)
> **Phase:** 46 of v10.0 design milestone · **Authors:** hermes-agent design team
> **Audience:** Kai(设计决策 reviewer)+ Kimi(Notion 续聊对照)+ v11.0 PoC 实施者
> **Reading time:** ~25 minutes(全文)/ ~6 minutes(§0 + §1.2 + §1.5 + §4.3 OQ audit)
> **Stability:** §1.5 + §2 + §3 + §4 + §5 全部 `stable`(lifecycle/conflict/MCP-tool 契约锁定,修改需开新设计-修订里程碑);§6 + §7 + §8 `stable`(advanced/citation/ref 跟随 §1-§5 锁定)
> **Confidence:** HIGH(本文档所有 lifecycle/conflict/serial 约束全部源自 ARCHITECTURE §5 + §8 + STACK §3.2 + PITFALLS §P7 + MEMORY.md `feedback-glm-overload-reduce-concurrency.md`,每个决策有 traceable source,本文档不发明任何字段或协议)

---

## §0 — 阅读指南

本文档是 **v10.0 milestone 的 round table 协议物理载体**,产出 2 个 deliverable:

1. **本文档(02-ROUND-TABLE-PROTOCOL.md)** —— round table turn lifecycle / memory 冲突仲裁规则 / 强制串行约束 / MCP tool 契约(narrative form)+ OQ 决议审计 + borrowable points 覆盖审计
2. **`round-table-state-schema.yaml`** —— 机器可读 JSON Schema(draft 2020-12,camelCase keywords),定义 `~/.hermes/agents/.runtime/{slug}/round_tables/{round_id}.json` 状态文件结构

后续 3 份设计文档(04-MIGRATION-PATH / 05-POC-PLAN / 51 VALIDATE)**在不重新推导决策 5/6/7 的前提下**引用本文档的 lifecycle 步骤与 conflict 仲裁规则 —— 本文档是它们的协议契约物理载体(§7.0 downstream citation card table)。

**与 Phase 44 `00-FIRST-PRINCIPLES.md` 的关系:** Phase 44 决策 5(α agent form:agents 是 Hermes-side 持久实体,不是 SKILL)+ 决策 6(per-agent memory + curator 自进化:memory 有 scope / confidence / evidence_chain)+ 决策 7(分层 CC 角色:Hermes 控 turn_order / max_rounds / early_stop_rule;CC 控 question framing / synthesis)是本文档的**根论据 anchor**(`root-arg-决策-5` / `root-arg-决策-6` / `root-arg-决策-7`)。本文档**不重新推导**这三个决策,只把它们落地成可被 v11.0 PoC Python 实现者 + Phase 51 lint script 消费的协议契约。

**与 Phase 45 `01-AGENT-REGISTRY-SCHEMA.md` 的关系:** Phase 45 锁定的两个 schema(`agents-schema.yaml` 18-field + `memory-record-schema.yaml` 10-field)是本文档**消费**的字段源 —— 本文档**CITE ONLY, do NOT redefine**。本文档引用的 Phase 45 字段包括:`memory_scope`、`scope`(global/project/session)、`confidence`、`evidence_chain`、`evidence_operator_ids`、`status`、`confidentiality`、`fitness_score`、`persona_sha256`、`record_id`、`agent_id`、`expires_at`、`verified_at`、`supersedes_memory_id`、`half_life_days`。这些字段的权威定义在 `01-AGENT-REGISTRY-SCHEMA.md` §2/§3 + 两个 schema YAML 文件 —— 本文档任何使用这些字段处都标注「Cite memory-record-schema field X」或「Cite agents-schema field Y」。

**与 SUMMARY.md CC-1 / CC-6 的关系:** SUMMARY.md CC-1 cross-cutting finding 统一了 MCP tool 命名(STACK §3.2 形态胜出,无 `agent_` 前缀);SUMMARY.md CC-6 cross-cutting finding 把 round table 锁死为**强制串行**(1 panelist 1 turn sequential `await`)—— 这两条 mandate 在本文档 §4.1 / §4.2 + §1.5.1 / §1.5.2 物理化。

### 章节地图

| 章节 | 内容 | 阅读优先级(按角色) |
|---|---|---|
| §0 | 阅读指南(本节) | 所有人先读 |
| §1 | 设计哲学 + turn lifecycle 框架 + SC 映射 + roadmap 放置 + 3 hard constraints 前置声明 | reviewer 必读 §1.1+§1.5;PoC 实施者必读 §1.2 |
| §2 | Turn lifecycle 详细 narrative(round_table_open / turn N / submit_round_table_result 三原子操作 + state file 持久化 + 5 种 turn_order 策略 + agent deletion semantics + early-stop) | **核心章节** — PoC 实施者 + 维护者必读 |
| §3 | Memory 冲突仲裁(5 子机制对齐 PITFALLS §P7 mitigation 1-5 + comparator LLM prompt + scope precedence + confidence 投票 + conflict log) | PoC 实施者必读 |
| §4 | Hard constraints 根因分析 + OQ 决议审计表 + borrowable points 覆盖审计表 | reviewer 必读(SC#2/3/4/5 物理载体) |
| §5 | MCP tool contract(7 个 tool,STACK §3.2 形态,narrative form,不重写 Pydantic) | PoC 实施者必读 |
| §6 | Advanced features 评估(subpanel / hooks / panelist_role / asset_locks,v11.1+ 候选 feature) | v12+ 设计者必读 |
| §7 | Downstream citation card + coherence 声明 + References | 后续 4 docs 作者必读 |

### 稳定性标记(修改门槛)

| 章节 | 稳定性 | 修改门槛 |
|---|---|---|
| §1.5 (3 hard constraints) | `stable` | 3 条 hard constraints(serial / STACK naming / atomic)是 SC#2-5 物理载体,修改需开新设计-修订里程碑 |
| §2 (turn lifecycle narrative) | `stable` | lifecycle 契约锁定(round_table_open / turn N / submit_round_table_result);修改需重跑 §4 OQ/BP audit |
| §3 (memory conflict arbitration) | `stable` | 5 子机制对齐 PITFALLS §P7 mitigation 1-5,修改需同步 PITFALLS 文档 |
| §4 (hard constraints + audit) | `stable` | OQ 决议 + BP 覆盖审计跟随 §1-§3 |
| §5 (MCP tool contract) | `stable` | 7 tool 命名 + 签名锁定;Phase 51 lint script 跨 doc 一致性检查 |
| §6 (advanced features) | `evolving` | 全部 v11.1+ deferred;v11.1 设计时再细化 |
| §7 (citation + refs) | `stable` | 跟随 §1-§6 |

### 受众指引(3 类读者)

- **Kai(reviewer / 设计决策者):** 先读 §0 + §1.1(协议哲学)+ §1.5(3 hard constraints 前置声明)+ §4.3 OQ audit + §4.4 BP audit。如果对 lifecycle 某步骤有疑问,跳到 §2 对应 §2.N。如果对 conflict 仲裁有疑问,跳到 §3.2 comparator LLM prompt template + §3.3 scope precedence。§4.1 serial root cause(MEMORY.md verbatim citation)是 load-bearing decision,reviewer 必读。
- **Kimi(Notion 续聊对照):** 先读 §1.2(turn lifecycle ASCII diagram,理解 v10.0 round table 三原子操作 + serial constraint),再读 §4.1 serial root cause(GLM concurrency==1 不可降的根因)+ §4.2 MCP naming reconciliation table(理解 STACK 形态 vs ARCHITECTURE 旧命名的对账),最后读 §3.2 comparator LLM prompt template(理解 v10.0 多 agent memory 冲突的仲裁机制,与 Kimi 架构2.0 的多 Expert 共识机制差异)。本文档字段名 + lifecycle 步骤是 Kimi 续聊时的「接口契约」。
- **v11.0 PoC 实施者:** 先读 §0 + §1.2(lifecycle 框架)+ §1.5(3 hard constraints),然后用 §2 / §3 / §5 章节作为 implementation spec。机器可读 schema 在 `round-table-state-schema.yaml`,直接 `jsonschema` 校验。§3.2 comparator LLM prompt template + §5.7 个 MCP tool 签名是 PoC 实施的物理起点。本文档**不发明任何字段或协议**,所有元素都可 traceable to ARCHITECTURE §5 / §8 + STACK §3.2 + PITFALLS §P7 + Phase 45 schema fields,实施者可放心照协议写 Python 实现。

---

## §1 — Protocol Overview:Round Table 是 v10.0 的多 Agent 协商层

### §1.1 — 设计哲学:消费 Phase 45 schema,规定协商 lifecycle

本文档定义 v10.0 round table 协议 —— **消费 Phase 45 锁定的 agent YAML schema(18 字段)+ memory-record schema(10 字段),规定多 agent 协商的 turn lifecycle、memory 冲突仲裁规则、以及强制串行约束**。本文档不重定义 Phase 45 任何字段 —— `memory_scope` / `scope` / `confidence` / `evidence_chain` / `evidence_operator_ids` / `status` / `confidentiality` / `fitness_score` / `persona_sha256` / `record_id` 等字段的权威定义在 `01-AGENT-REGISTRY-SCHEMA.md` §2 / §3 + 两个 schema YAML 文件,本文档所有引用处都标注「Cite Phase 45 field X,do NOT redefine」。

**根论据 anchor(`root-arg-决策-5` + `root-arg-决策-6` + `root-arg-决策-7`):**

- **决策 5(Phase 44 §2.5):** α agent form = YAML + persona + tools + refs + memory_scope + lineage。**根本含义:** agents 是 Hermes-side 持久实体,有身份、有记忆、可自进化,不是 SKILL 模板,也不是 CC-side subagent。Round table 协议的**协议参与者**就是这个形态的 agents —— panelist 不是临时 fork,而是引用 agent YAML 的当前 snapshot + 当前 memory backend 状态。
- **决策 6(Phase 44 §2.6):** per-agent scoped memory + curator 驱动跨项目自进化。**根本含义:** 每个 agent 拥有自己的 memory namespace(mem0 backend per-agent filter),memory record 有 `scope` / `confidence` / `evidence_chain` 字段。Round table 协议的**冲突仲裁机制**完全基于这套字段 —— 两个 panelist 引用各自信任的 memory,comparator LLM 通过 `scope` precedence + `confidence` 加权投票裁定。
- **决策 7(Phase 44 §2.7):** 分层 CC 角色:Hermes 控结构(turn_order / max_rounds / early_stop_rule / state schema),CC 控内容(question framing / opinion synthesis / conflict detection)。**根本含义:** Round table 协议的「协议契约」是 Hermes-side(schema + lifecycle enforcement),「协商内容」是 CC-side(question + opinions + synthesis)。这两层在 §2 lifecycle 的每一步都有显式归属。

**这三个 root-arg 是 load-bearing**:本文档任何章节的字段引用 / lifecycle 步骤 / conflict 仲裁规则都可 traceable 回这三个决策的某一个。如果发现某条规则无法 trace 回决策 5/6/7,该规则视为越界,需开新设计-修订里程碑。

**Phase 45 schema 字段消费清单(CITE ONLY, do NOT redefine):**

| 字段 | 出处(Phase 45 文件 / 章节) | 在本文档使用章节 |
|---|---|---|
| `memory_scope`(enum: shared/per_agent/project_scoped) | agents-schema.yaml §2.6 + design doc §2.6 | §2.1(panelist snapshot 字段引用) |
| `scope`(enum: global/project/session) | memory-record-schema.yaml §3.9 | §3.3 scope precedence |
| `confidence`(float 0.0-1.0, default 0.5) | memory-record-schema.yaml §3.5 | §3.4 confidence-weighted voting |
| `evidence_chain`(list, minItems=3) | memory-record-schema.yaml §3.6 | §3.1 memory annotation enrichment |
| `evidence_operator_ids`(list, minItems=1) | memory-record-schema.yaml §3.7 | §3.1 enrichment |
| `status`(enum: active/archived/quarantined/superseded) | memory-record-schema.yaml §3.8 | §3.5 conflict log curator review |
| `confidentiality`(enum: public/internal/confidential/restricted) | memory-record-schema.yaml §3.10 | §3.2 comparator LLM filter |
| `fitness_score`(float or null) | agents-schema.yaml §2.15 | §2.1 panelist snapshot |
| `persona_sha256`(64-hex SHA-256) | agents-schema.yaml §2.14 + memory-record-schema §3.11 | §2.1 + state schema `personaSnapshots` field |
| `record_id`(string, UUID v4) | memory-record-schema.yaml §3.0 | §3.1 memory annotation |
| `agent_id`(string, regex `^[a-z0-9_-]+$`) | memory-record-schema.yaml §3.0 | §2.1 panelist snapshot |
| `expires_at` / `verified_at` / `supersedes_memory_id` / `half_life_days` | memory-record-schema.yaml §3.1-§3.4 | §3.1 enrichment + §3.5 curator review |

**此表是 CITE-ONLY 契约**:本文档不在 §2/§3/§5 任何地方重复定义这些字段的 type / enum / 语义;只在引用时用 `memory-record-schema field X` 形式标注。如果读者需要看字段定义,跳到 Phase 45 文件。

**为什么必须 CITE-ONLY?** Phase 45 schema 是 SC#1 ROADMAP-level lock(`01-AGENT-REGISTRY-SCHEMA.md` §0 + `additionalProperties: false` 在两个 YAML 文件强制)。如果本文档重复定义 `scope` / `confidence` / `evidence_chain` 等字段,Phase 51 VALIDATE lint script 会发现两份不一致的定义 —— 轻则 implementation 不知该信哪份,重则 v11.0 PoC 实施者照本文档写 Python dataclass 后无法通过 Phase 45 schema 校验。CITE-ONLY 是字段级稳定性的根本保证。

**协议层 vs schema 层的边界:** 本 doc **只**规定 lifecycle / conflict / MCP tool 三件事,所有跟字段定义相关的内容(类型、enum 值、约束、默认值)都引用 Phase 45。如果本 doc 出现「`scope` 是 global|project|session 之一」这种描述,它只是 reminder(指向 Phase 45),不是定义 —— 任何读者发现本 doc 与 Phase 45 schema YAML 不一致,**以 Phase 45 schema YAML 为准**,本 doc 标 `evolving`,在下一个设计-修订里程碑里同步。

### §1.2 — Turn Lifecycle Summary(三原子操作 + serial invariant)

v10.0 round table 的 turn lifecycle 由**三个原子操作**组成,中间步骤严格 serial(1 panelist 1 turn sequential `await`),不允许并发 LLM 调用:

```
┌────────────────────────────────────────────────────────────────────┐
│ CC (Claude Code) side                                              │
│                                                                    │
│  1. CC self-generates round_id (UUID v4)         ← OQ-11 resolution│
│  2. CC calls round_table_open(                    ← atomic start   │
│       round_id, panel, question,                                   │
│       max_rounds, turn_order_strategy,                             │
│       early_stop_rule, project_id)                                 │
│  3. For each turn i in 1..N (SERIAL await — OQ-8):                 │
│       a. CC selects panelist per turn_order                        │
│       b. CC calls get_agent_opinion(panelist, topic, prior)        │
│       c. CC appends opinion to turns[i] in state file              │
│       d. (optional) CC calls run comparator LLM on conflicts       │
│  4. CC calls submit_round_table_result(           ← atomic commit  │
│       round_id, conclusion, cited_memories,                        │
│       artifacts, conflicts)                                        │
│  5. Hermes persists result + writes conflict log                   │
└────────────────────────────────────────────────────────────────────┘
```

**结构 vs 内容的归属(决策 7):** Hermes owns `turn_order` / `max_rounds` / `early_stop_rule` via state schema(§2.1-§2.3 + round-table-state-schema.yaml);CC owns question framing、opinion synthesis、conflict detection、final conclusion。这是 Phase 44 §2.7 锁定的 structure/content split —— lifecycle 步骤归属 Hermes(协议契约),内容生成归属 CC(协商产物)。本节以下章节展开这个 lifecycle 的每一步契约。

**Atomic 三件套(详见 §2):**

- `round_table_open` —— atomic start,创建状态文件,返回 `roundId`
- `get_agent_opinion`(per turn N)—— atomic per-turn opinion call,append 到 state file turns 数组
- `submit_round_table_result` —— atomic commit,flip status=completed,seal conflict log

中间任何状态都持久化到 `~/.hermes/agents/.runtime/{slug}/round_tables/{round_id}.json`(cite ARCHITECTURE §5.1 verbatim)—— 这是 crash recovery + curator review + audit 的物理载体。

### §1.3 — SC 映射表(本 doc 章节 → ROADMAP SC#1-5)

ROADMAP §Phase 46 列出 5 条 success criteria,每条都映射到本文档的具体章节,验证脚本可通过 §1.3 表交叉核对:

| SC# | SC 描述(摘自 ROADMAP §Phase 46) | 本 doc 解决章节 | 验证脚本 |
|---|---|---|---|
| SC#1 | Files `02-ROUND-TABLE-PROTOCOL.md` + `round-table-state-schema.yaml` exist | (本文件本身)+ `round-table-state-schema.yaml` | `test -f` + line count |
| SC#2 | Turn lifecycle fully defined(round_table_open → turn N → submit_round_table_result),包括 `turn_order` 策略(default round-robin + pluggable,resolves OQ-2)+ `round_id` CC-self-generated UUID(resolves OQ-11) | §1.2 + §2.1 + §2.2 + §2.3 + §2.5 + §2.6 | grep "round_table_open" + "submit_round_table_result" + "round-robin" + "OQ-11" |
| SC#3 | Memory conflict arbitration rules documented:comparator LLM pass + scope precedence(session > project > global)+ confidence-weighted voting + conflict log(resolves OQ-15, avoids P7) | §3.0-§3.7(5 子机制对齐 PITFALLS §P7 mitigation 1-5) | grep "comparator" + "scope precedence" + "session > project > global" + "confidence-weighted" + "P7" |
| SC#4 | Serial execution constraint explicitly declared(1 panelist 1 turn sequential await,citing MEMORY.md `feedback-glm-overload-reduce-concurrency.md` global concurrency==1 policy,resolves OQ-8) | §1.5.1 + §2.8 + §4.1 | grep "serial" + "concurrency==1" + "feedback-glm-overload-reduce-concurrency" |
| SC#5 | MCP tool naming unified to STACK §3.2 form(no prefix,aligns with existing 9 messaging tools,resolves OQ-9);covers FEATURES §10 borrowable points B1.4 / B2.1 / B2.3 / B4.2 / B6.1 / B7.3 / B8.2 | §1.5.2 + §4.2 + §4.4 + §5 + §6 | grep "STACK §3.2" + 7 个 B*.x 全部出现 |

每条 SC 都有可机器验证的 anchor string —— Phase 51 VALIDATE lint script 直接 grep 这些字符串即可验证。

**额外验证维度(本 doc 自带 §5 + §6 覆盖 FEATURES §10 borrowable points):** SC#5 只列出 7 个 borrowable points 作为覆盖验收标准,但本 doc 还在 §4.4 给出 7-row 完整审计表(B1.4 / B2.1 / B2.3 / B4.2 / B6.1 / B7.3 / B8.2 每条标注 where + how),并在 §6 给 v11.1+ 候选 feature 的深度评估(subpanel / hooks / panelist_role / asset_locks)。这是 ROADMAP SC#5 之外的额外覆盖深度。

### §1.4 — Roadmap 放置:本 doc 是 04 / 05 / 51 的协议契约物理载体

本 doc 是 **04-MIGRATION-PATH.md + 05-POC-PLAN.md + 51 VALIDATE 的协议契约物理载体**:

- **04-MIGRATION-PATH.md** 引用本 doc 的 §2 lifecycle(迁移时 15-expert 的 round_table_eligible flag 切换语义)+ §4.2 MCP naming(15-expert 从 skill_fallback 切换到 mcp_tool 时使用 STACK-form tool 名)。
- **05-POC-PLAN.md** 引用本 doc 的 §3 conflict arbitration rules(PoC acceptance criteria:comparator LLM 必须在 round table 结束时正确 resolve 至少 1 个 conflict)+ §4.1 serial(PoC 性能 SLO:p95 < N 秒 per turn,serial await 是基线)+ §4.3 OQ audit + §4.4 BP audit。
- **51 VALIDATE** 引用本 doc 的 `round-table-state-schema.yaml`(跨 doc 一致性 lint:本 doc narrative 提到的字段名必须出现在 schema YAML 中)。
- **03-COMPARISON-VS-KIMI-MCP-SHIM.md + 06-CROSS-REPO-IMPACT.md** 是 parallel siblings,**不直接消费**本 doc 的协议细节 —— 它们 cite Phase 44 决策 5/6/7 直接(横切对照,不依赖协议层)。

**Phase 44 决策 5/6/7 LOCKED,Phase 45 schemas LOCKED,本 doc 只规定协议层。** 本 doc 不重写决策 5/6/7 任何论证,不重定义 Phase 45 任何字段 —— 这是协议层与决策层 / schema 层的清晰分层。

**本 doc 与 v11.0 PoC 的关系:** 本 doc 是 **设计层契约** —— 它锁定 lifecycle / conflict / MCP tool 命名,但不规定 Python implementation 细节(如 `agent_dispatcher.py` 怎么 spawn AIAgent fork、mem0 backend 怎么 filter 路由)。这些实施细节由 05-POC-PLAN.md + v11.0 PoC 实施者决定。本 doc 只要求:任何 PoC implementation **必须** 通过本 doc 的 §2 lifecycle 步骤 + §3 conflict 仲裁机制 + §5 MCP tool 签名校验。本 doc 是协议契约,不是 implementation manual。

### §1.5 — 3 Hard Constraints(前置声明)

本节前置声明 round table 协议的 3 条 hard constraints,每条都对应一个 OQ 决议 + 一个 root cause 来源。这 3 条约束是 **load-bearing** —— 违反任何一条都会破坏 v10.0 round table 的核心可运行性。详细 root-cause 分析在 §4.1-§4.2。

#### §1.5.1 — Serial Execution(1 panelist 1 turn sequential await,resolves OQ-8)

**Constraint:** v10.0 round table **强制 1 panelist 1 turn sequential `await`,绝不允许并发 LLM 调用**。每个 `get_agent_opinion` 调用必须 `await` 完成后才能开始下一个 panelist 的 turn。

**Root cause 速览(详见 §4.1):** GLM 4-key rotation 在 7 panelist × N rounds 并发场景下会立刻撞 ceiling(~800K TPM)。MEMORY.md `feedback-glm-overload-reduce-concurrency.md` 已记录 global concurrency==1 是 **BY DESIGN**(2026-07-03 从 5→3;2026-07-06 已是 1,不再降 —— 上游模型容量本身就是瓶颈)。Re-introducing parallelism at the round table layer 会 undo operator-level discipline。

**Cite:** MEMORY.md `feedback-glm-overload-reduce-concurrency.md` + STACK §7.5(`await` 顺序约束)+ FEATURES §14 gap 6(GLM 4-key rotation × multi-panelist 并发成本未算)。详见 §4.1。

**Implementation discipline(详见 §4.1):** v11.0 PoC 的 `get_agent_opinion` 实现 MUST 在 for-loop 中 sequential `await`,NEVER `Promise.all` 或 async-gather;Hermes dispatcher MUST 拒绝同 roundId 的并发 `get_agent_opinion` 调用(返回 429 Too Many Requests);v11.0 PoC MUST NOT 添加「parallel round table」opt-in flag —— 这条约束是 structural,不是 configurational。

#### §1.5.2 — STACK-Form MCP Naming(no agent_ prefix, resolves OQ-9)

**Constraint:** 所有 round table 相关的 MCP tool **采用 STACK §3.2 形态(无 `agent_` 前缀)**,与现有 `mcp_serve.py` 9 个 messaging tool 风格一致。**Canonical names:** `get_agent_persona` / `get_agent_opinion` / `get_agent_memory` / `submit_round_table_result` / `submit_artifact` / `query_memory` / `run_python_phase`(详见 §5)。**Deprecated names:** ARCHITECTURE §4.2 旧命名 `agent_get_persona` / `agent_recall` / `agent_opinion` / `agent_conclude` 全部弃用(详见 §4.2 reconciliation table)。

**Rationale(详见 §4.2):** SUMMARY.md CC-1 cross-cutting finding 明确指出 STACK 形态胜出 —— 现有 `mcp_serve.py` 9 个 messaging tool 是 `conversations_list` / `messages_read` / `messages_send`(no `messaging_` prefix),round table tool 应保持风格统一。`agent_` 前缀会破坏 tool list 视觉一致性,让 CC dispatcher 实施者混淆。

**Cite:** SUMMARY.md CC-1 + STACK §3.2(7 tool authoritative Pydantic schema)+ ARCHITECTURE §4.2(deprecated 命名 source)。详见 §4.2 + §5。

**Phase 51 lint 强制:** 本 doc 命名 lock 通过 Phase 51 VALIDATE lint script 强制 —— script 检查 `mcp_serve.py` 实际注册的 7 个 tool 名是否与本 doc §5 + STACK §3.2 一致;不一致触发 ADVISORY 提醒。这是 SC#5 的自动化验证路径。

**为什么 ARCHITECTURE §4.2 用了 agent_ 前缀却最终弃用?** ARCHITECTURE 是 Phase 44 research 文档,§4.2 列了 7 个 tool 时采用了「concept-grouped」命名(把所有 agent-related tool 用 `agent_` 前缀分组)。STACK.md(也是 Phase 44 research)在 §3.2 重新写了一遍,采用了与现有 `mcp_serve.py` 一致的「no prefix」命名。SUMMARY.md CC-1 在两份 research 之间发现冲突,决定 STACK 形态胜出 —— 因为现有 `mcp_serve.py` 已经用 no-prefix 风格 ship 了 9 个 tool(`conversations_list` 等),改风格代价远高于改 Phase 44 的 research draft。这是「research drift vs implementation consistency」的典型取舍 —— implementation 一致性胜出。

#### §1.5.3 — Atomic Turn Lifecycle(round_table_open returns immediately, submit is atomic)

**Constraint:** Round table lifecycle 是 **三原子操作**:`round_table_open`(立即返回 roundId,不阻塞等待 round 完成)+ per-turn `get_agent_opinion`(每个 turn 是独立的 atomic opinion append)+ `submit_round_table_result`(原子提交点,flip status=completed)。中间状态持久化到 `~/.hermes/agents/.runtime/{slug}/round_tables/{round_id}.json`(cite ARCHITECTURE §5.1 verbatim)。

**Anti-pattern guard(详见 §2.1):** `round_table_open` 是 **NOT synchronous pipeline step** —— 它不阻塞调用线程等待 round 结束(ARCHITECTURE §8.3 anti-pattern)。CC 通过 events poll 或直接顺序调用 `get_agent_opinion` 推进 round。Round table 不是 pipeline step —— 是 protocol state machine。

**Cite:** ARCHITECTURE §5.1 + §5.3 lifecycle sketch + §8.3 anti-pattern。详见 §2.1 + §2.3。

**Idempotency & crash recovery(详见 §2.3 + §2.4):** `submit_round_table_result` 是 idempotent —— 对同一 `roundId` 的二次提交返回 409 Conflict(status=completed 状态不允许二次 seal)。Crash recovery:on CC restart 时,若状态文件 `status=open` 且 `now - lastUpdatedAt > stall_threshold`(默认 PoC tunable 30 分钟),状态自动 flip 为 `stalled`;operator 可选择 resume(留 v11.1+)或 abort(`status=aborted`,conflict log 仍 sealed 供审计)。这套 recovery 语义是 load-bearing —— 否则 CC mid-round crash 会留下永远 open 的 round table 状态文件,pollute `.runtime/{slug}/round_tables/` 目录。

**3 hard constraints 之间的依赖关系:** §1.5.1 serial 是 §1.5.3 atomic 的前提(只有 serial,每个 turn append 才能 atomic);§1.5.2 STACK-form naming 是 §1.5.3 atomic lifecycle 的 MCP tool 实现载体(没有 canonical tool 命名,lifecycle 操作无法被 CC 调用);§1.5.3 atomic 是 §1.5.1 serial 的状态持久化保证(没有 atomic open/submit,serial turn 序列无法跨 CC restart 续传)。三条约束互为前提,缺一不可。

---

## §2 — Turn Lifecycle:round_table_open → turn N → submit_round_table_result

### §2.0 — 本节范围

本节展开 §1.2 的 turn lifecycle 框架,聚焦于**每个原子操作的契约**。机器可读 schema 见 `round-table-state-schema.yaml`(ROUND-TABLE-PROTOCOL.md 的姊妹文件)。所有 MCP tool 命名采用 STACK §3.2 形态(无 `agent_` 前缀,见 §5)。本节包含 8 个子节:§2.1 round_table_open / §2.2 turn N / §2.3 submit_round_table_result / §2.4 state file persistence / §2.5 turn_order strategies / §2.6 agent deletion semantics / §2.7 early-stop conditions / §2.8 serial invariant restatement。

### §2.1 — round_table_open(atomic start,returns immediately with roundId)

**Caller:** CC(Claude Code)—— Phase 44 决策 7:CC owns question framing。CC 决定何时需要 round table、问题是什么、panel 是谁。

**Args:**

| Arg | Type | Required | Default | 说明 |
|---|---|---|---|---|
| `roundId` | UUID v4 string | YES | — | **CC-self-generated(OQ-11 resolution)** —— CC 自己生成 UUID v4 后传入,不依赖 Hermes 注入 |
| `panel` | list of agentId(string,regex `^[a-z0-9_-]+$`) | YES | — | 至少 2 个 panelist;每个 agentId 必须存在于 `~/.hermes/agents/{name}.agent.yaml` |
| `question` | string | YES | — | CC-framed question / topic |
| `maxRounds` | int | NO | 5 | Hard cap on turn count(默认 5,ReConcile paper convergence point) |
| `turnOrderStrategy` | enum: round-robin / fixed / llm / matrix / fitness-weighted | NO | round-robin | **OQ-2 resolution** —— 默认 round-robin,pluggable |
| `earlyStopRule` | object | NO | null | Optional early-stop condition(详见 §2.7 + round-table-state-schema.yaml $defs.EarlyStopRule) |
| `projectId` | string | YES | — | Project slug,用于 `.runtime/{slug}/round_tables/{round_id}.json` 路径 |

**Atomic semantics(详):**

1. Hermes 收到 `round_table_open(roundId, panel, question, ...)` MCP call。
2. Hermes validates:`roundId` 不冲突(若 `.runtime/{slug}/round_tables/{roundId}.json` 已存在,return 409 Conflict —— OQ-11 + state schema `roundId` format=uuid 唯一性保证);所有 `panel` agentId 在 agent registry 中存在且 `round_table_eligible=true`(cite Phase 45 agents-schema §2.17);`projectId` 不为空。
3. Hermes **snapshots all panelists**:对每个 panelist,读取 `~/.hermes/agents/{name}.agent.yaml` 的 `name` / `persona` / `tools` / `memory_scope` / `fitness_score` + 计算 `persona_sha256`,生成 `PanelistSnapshot` object。**这是 OQ-5 resolution 的物理载体** —— 即使 agent 后续被编辑或删除,这个 snapshot 在 state file 中是 THIS round 的 authoritative record。
4. Hermes **creates state file** at `~/.hermes/agents/.runtime/{slug}/round_tables/{roundId}.json`,initial state:
   - `status: open`
   - `turns: []`
   - `conflicts: []`
   - `roundTableOpen: {caller, openedAt: now(), project: projectId, question}`
   - `turnOrder: {strategy: turnOrderStrategy, seed: <pre-computed order>, currentIndex: 0}`
   - `panelists: [<PanelistSnapshot>...]`
   - `personaSnapshots: {agentId → persona_sha256}` map
   - `createdAt: now()` / `lastUpdatedAt: now()` / `schemaVersion: "1.0.0"`
5. Hermes **returns immediately** with `{roundId, initialTurnOrder}` —— **NOT synchronous**(ARCHITECTURE §8.3 anti-pattern)。CC 拿到 `roundId` 后,自己驱动后续 turn-by-turn 调用。

**Anti-pattern guard(verbatim from ARCHITECTURE §8.3):**

> ### 8.3 Anti-Pattern: Round Table as Pipeline Step
> **What:** Treating `round_table_open` as a synchronous pipeline step that blocks until `closed`.
> **Why bad:** Round tables involve multiple LLM forks (one per panelist per round); blocking the calling thread for 3 rounds × 4 panelists × 30s = 6 minutes is unacceptable for interactive MCP clients.
> **Instead:** `round_table_open` returns immediately with `round_table_id`; CC polls via `round_table_poll` (or proceeds to call `get_agent_opinion` directly). State persists in `.runtime/{slug}/round_tables/{id}.json`.

**MCP tool:** `round_table_open` —— 详见 §5。**注意:** STACK §3.2 canonical 7 tool 列表中,`round_table_open` 不在 Tool 1-7 之内(那 7 个是 agent-facing 工具);`round_table_open` 是 lifecycle controller,签名见 §5.0(本 doc 在 §5.0 给出 narrative contract,authoritative Pydantic schema 在 STACK §3.2 Tool 4 的扩展中,v11.0 PoC 时补完)。

**Worked example(round_table_open 全流程):**

```
CC side:
  roundId = uuid4()  # e.g. "550e8400-e29b-41d4-a716-446655440000"
  panel = ["screenplay", "cinematographer", "hook_retention", "theory_critic"]
  question = "Should the Volvo S1-1 opening use an empty-car establish or a grandson reveal?"
  maxRounds = 3
  turnOrderStrategy = "round-robin"
  projectId = "kais-movie-agent:a1b2c3d4"

  response = mcp_call("round_table_open", {roundId, panel, question, maxRounds, ...})

Hermes side (on receiving round_table_open):
  1. Validate roundId uniqueness:
       .runtime/kais-movie-agent:a1b2c3d4/round_tables/550e8400-*.json must NOT exist
       (return 409 if it does)
  2. Validate panel:
       - All 4 agentId exist in ~/.hermes/agents/*.agent.yaml
       - All 4 have round_table_eligible=true (Phase 45 agents-schema §2.17)
  3. Snapshot panelists (PITFALLS §P1 + OQ-5):
       for each agentId in panel:
         yaml = read(~/.hermes/agents/{agentId}.agent.yaml)
         snapshot = PanelistSnapshot(
           agentId=agentId,
           personaSha256=sha256(yaml.persona),
           fitnessScore=yaml.fitness_score,  # may be null per OQ-4
           tools=yaml.tools,
           memoryScope=yaml.memory_scope,
           deleted=False,
         )
  4. Create state file:
       path: ~/.hermes/agents/.runtime/kais-movie-agent:a1b2c3d4/round_tables/550e8400-*.json
       content (per round-table-state-schema.yaml):
         {
           "roundId": "550e8400-...",
           "projectId": "kais-movie-agent:a1b2c3d4",
           "question": "Should the Volvo S1-1 opening...",
           "panelists": [<4 PanelistSnapshot>],
           "turnOrder": {
             "strategy": "round-robin",
             "seed": ["cinematographer", "screenplay", "hook_retention", "theory_critic"],
             "currentIndex": 0,
           },
           "status": "open",
           "turns": [],
           "conflicts": [],
           "maxRounds": 3,
           "roundTableOpen": {
             "caller": "cc-session-abc",
             "openedAt": "2026-07-15T15:30:00Z",
             "project": "kais-movie-agent:a1b2c3d4",
             "question": "Should the Volvo S1-1 opening...",
           },
           "personaSnapshots": {
             "screenplay": "abc123...", "cinematographer": "def456...",
             "hook_retention": "ghi789...", "theory_critic": "jkl012..."
           },
           "schemaVersion": "1.0.0",
           "createdAt": "2026-07-15T15:30:00Z",
           "lastUpdatedAt": "2026-07-15T15:30:00Z",
         }
  5. Return immediately:
       {roundId: "550e8400-...", initialTurnOrder: {strategy, seed, currentIndex: 0}}

CC side (continuing):
  # CC proceeds to drive turn 1 via §2.2 — does NOT wait for round completion.
  # Round table is now atomic-open; subsequent turns are CC's responsibility.
```

这个 worked example 是 **load-bearing** —— 它展示 `round_table_open` 是真正的 atomic 操作,所有 5 个 validation + snapshot + persist 步骤在一个 MCP call 内完成,返回的是 roundId(不是 round result)。

### §2.2 — turn N(atomic per-turn opinion submission,append-only)

每个 turn 是一个独立的 atomic 操作,严格 serial(OQ-8)。流程:

1. **Selection(选择下一个 panelist):** CC 读取 state file 的 `turnOrder.currentIndex`,按 `turnOrder.strategy` 决定下一个 panelistId:
   - `strategy=round-robin`:`panelists[seed[currentIndex]]`
   - `strategy=fixed`:同 round-robin(seed 是 operator-supplied 顺序)
   - `strategy=llm`:CC 自己用 LLM 决定下一个(详见 §2.5)
   - `strategy=matrix`:FSM transition matrix(详见 §2.5)
   - `strategy=fitness-weighted`:higher-fitness first(v11.1+ deferred)
2. **Opinion call(CC → Hermes):** CC invokes `get_agent_opinion(agentId, topic, context, priorDiscussion)` MCP tool(STACK §3.2 Tool 2)。Hermes dispatcher spawn AIAgent fork with `system_prompt = persona`、`tools = whitelist`、scoped mem0(详见 §5.2)。
3. **Append turn:** CC 收到 opinion 后,**append** `{turnIndex, panelistId, opinion, citedMemoryIds, submittedAt: now()}` 到 state file `turns` array。**Append-only** —— 已存在的 turn 不可编辑,只能添加新 turn。
4. **Conflict detection(可选,实时):** 如果 `citedMemoryIds` 中包含的 memory records 与之前 turn 中引用的 records 在语义上矛盾(embedding cosine ≥ 0.7 + manual CC flag),CC 触发 comparator LLM pass(详见 §3.2)。comparator 输出的 `ConflictRecord` 立即 append 到 state file `conflicts` 数组(详见 §3.5)。
5. **Increment + persist:** `turnOrder.currentIndex++`、`lastUpdatedAt = now()`、state file 写盘。

**Serial invariant(load-bearing,OQ-8):** 每个 turn **MUST await 完成后才能开始下一个**。绝不允许 concurrent `get_agent_opinion` calls。Hermes dispatcher **MUST reject** 同 `roundId` 的并发 `get_agent_opinion` calls(return 429 Too Many Requests)。详细 root cause + implementation discipline 在 §4.1。

**MCP tools used:** `get_agent_opinion`(STACK §3.2 Tool 2,详见 §5.2)+ `get_agent_memory`(STACK §3.2 Tool 3,详见 §5.3,用于 conflict detection 时 fetch full memory records)。

### §2.3 — submit_round_table_result(atomic commit,flips status=completed)

**Caller:** CC,当 conclusion 已 synthesized(decision 7:CC owns synthesis)OR `earlyStopRule` triggers。

**Args:**

| Arg | Type | Required | 说明 |
|---|---|---|---|
| `roundId` | UUID v4 string | YES | 与 §2.1 round_table_open 的 roundId 一致 |
| `conclusion` | string | YES | CC's synthesis of the round table discussion(decision 7:CC controls content) |
| `citedMemories` | list of record_id(UUID v4) | YES | 所有 turns + conclusion 引用的 memory record_ids 并集 |
| `artifacts` | list of `{artifactId, artifactType, content, provenance}` | NO | Round 产物(screenplay draft / decision md 等) |
| `conflicts` | list of conflictId(UUID v4) | NO | state file `conflicts` 数组中所有 ConflictRecord 的 conflictId list |

**Atomic semantics:**

1. Hermes 收到 `submit_round_table_result(...)` MCP call。
2. Hermes validates:`roundId` exists in state file AND `status=open`(若 `status=completed`,return 409 Conflict —— **idempotency guard**)。
3. Hermes **seals conflict log**:`conflicts` 数组 immutable,不允许再 append(防篡改)。
4. Hermes **flips** `status: open → completed`,persists `submitRoundTableResult: {conclusion, citedMemories, artifacts, closedAt: now(), closedBy: caller}` block 到 state file。
5. Hermes **emits event** for curator periodic pass:curator 后续 review conflict log(§3.5),决定 high-frequency conflict 是否要 promote / quarantine。
6. Hermes returns `{receiptId: uuid4, sealedAt: now(), finalConflictCount: <int>}` 给 CC。

**Idempotency(详):** Second `submit_round_table_result` for same `roundId` returns 409 Conflict。这是为了防止 CC retry 时 double-seal(同 round 被认为完成两次),会污染 curator 的 conflict-log review baseline。Operator 想强制 abort 用单独的 `round_table_abort`(留 v11.1+)或直接修改 state file `status=aborted`。

**MCP tool:** `submit_round_table_result` —— STACK §3.2 Tool 4,详见 §5.4。

**Worked example(submit_round_table_result 全流程):**

```
CC side (after all turns are done or earlyStopRule triggered):
  response = mcp_call("submit_round_table_result", {
    roundId: "550e8400-...",
    conclusion: "Use grandson reveal — cinematographer's empty-car establish
                 would lose TikTok retention (hook_retention cited 0.92 project
                 memory 'gen-z reveal > establish for 7s hook window').
                 theory_critic's global-memory claim about 'reveal fatigue'
                 was quarantined by comparator (insufficient project-level evidence).",
    citedMemories: [
      "abc-...",  # hook_retention's project memory about gen-z reveal
      "def-...",  # cinematographer's project memory about empty-car pacing
      "ghi-...",  # theory_critic's quarantined global memory
    ],
    artifacts: [{
      artifactId: "rt-20260715-decision.md",
      artifactType: "decision-md",
      content: "<full decision markdown>",
      provenance: "synthesized by CC from 4 panelist turns + 1 conflict resolution",
    }],
    conflicts: ["conflict-001", "conflict-002"],
  })

Hermes side (on receiving submit_round_table_result):
  1. Validate roundId + status:
       state file exists AND status=open
       (return 409 if status=completed — idempotency guard)
  2. Seal conflict log:
       conflicts array becomes immutable
  3. Flip status + persist submitRoundTableResult block:
       status: open → completed
       submitRoundTableResult: {
         conclusion: "Use grandson reveal...",
         citedMemories: ["abc-...", "def-...", "ghi-..."],
         artifacts: [...],
         closedAt: "2026-07-15T15:42:00Z",
         closedBy: "cc-session-abc",
       }
       lastUpdatedAt: "2026-07-15T15:42:00Z"
  4. Emit event for curator periodic pass:
       "round-table-sealed" event with conflictLog summary
       (curator will review high-frequency conflicts in next _feedback_scan_phase)
  5. Return:
       {receiptId: "rtc-001", sealedAt: "2026-07-15T15:42:00Z", finalConflictCount: 2}

CC side (acknowledges receipt, round table is over):
  # No further turns; state file is read-only after this point.
```

**Idempotency replay scenario:** 如果 CC 因为网络抖动 retry `submit_round_table_result`(同 roundId),Hermes 第二次 call 看到 `status=completed`,return 409 Conflict。CC 拿到 409 后识别为 idempotent replay,正常退出 —— 不视为错误。

### §2.4 — State File Persistence Rules(crash recovery + audit)

**Path(verbatim from ARCHITECTURE §5.1):**

```
~/.hermes/agents/.runtime/
└── {project_slug}/                       # e.g. hermes-agent:a1b2c3d4
    └── round_tables/
        ├── {round_table_id}.json         # active or completed round table state
        ├── {round_table_id}.json
        └── ...
```

**`project_slug` derivation(verbatim from ARCHITECTURE §5.1):** `{repo_basename}:{git_toplevel_abspath_sha8}`(e.g. `hermes-agent:a1b2c3d4`)。This disambiguates two repos with the same name on different machines.

**Append-only invariant:** `turns` array grows monotonically;existing entries are immutable(包括 `opinion` 字段 + `citedMemoryIds`)。`conflicts` array 在 `status=open` 时 append-only;`status=completed` 时 sealed。

**`lastUpdatedAt` bump rules:**

- Turn append → bump
- Conflict append → bump
- Status flip(open → completed/aborted/stalled)→ bump
- Persona_snapshot 检测到 drift(详 §3 + state schema `personaSnapshots` field)→ bump

**Crash recovery(详):**

- On CC restart,Hermes 扫描 `.runtime/{slug}/round_tables/*.json`,找 `status=open` 的文件。
- 若 `now - lastUpdatedAt > stall_threshold`(PoC tunable,default 30 分钟),状态自动 flip `status: open → stalled`,写 `lastUpdatedAt`。
- Operator 可选择:
  - **Resume(v11.1+ deferred):** 通过 `round_table_resume(roundId)` 从 `turnOrder.currentIndex` 续传。
  - **Abort:** 通过 `round_table_abort(roundId)` 或直接修改 state file,flip `status: stalled → aborted`。Conflict log 仍 sealed 供 curator 审计。
- Stalled detection 是 load-bearing —— 否则 CC mid-round crash 会留下永远 `open` 的 round table 状态文件,pollute `.runtime/{slug}/round_tables/` 目录,让后续 `agents_list` 等查询混淆。

### §2.5 — turn_order Strategies Deep Dive(5 strategies,OQ-2 + B2.1 + B8.2)

本节深入展开 `TurnOrder.strategy` 的 5 个 enum value。**OQ-2 resolution:** default round-robin + 4 alternative strategies with v11.1+ deferrals。**B2.1 inspiration:** AutoGen/MAF 三态(llm/fixed/matrix);本 doc 扩展到 5 态。**B8.2 inspiration:** A2A Task lifecycle FSM 的状态转移思想。

#### §2.5.1 — round-robin(default)

- **Mechanism:** Open-time pre-compute `seed = shuffled(panel)`,shuffle seed = `roundId` for reproducibility。Each panelist speaks once per round;cycles repeat until `maxRounds` or early stop。
- **When to use:** Default;适用于 panelist 之间无明确优先级的常规协商。
- **Convergence reference:** ReConcile paper(ACL 2024)实验显示 round-table consensus 通常 3-5 rounds 收敛;故 `maxRounds` default=5。
- **PoC scope:** v11.0 PoC 默认 + 必须支持。

#### §2.5.2 — fixed

- **Mechanism:** Operator-supplied `seed` order。Used when seniority / role matters —— e.g. `compliance_gate` speaks **last** as final reviewer。
- **When to use:** Compliance round、seniority-ordered 投票、固定流程的 audit round。
- **PoC scope:** v11.0 PoC 支持。

#### §2.5.3 — llm(progressive)

- **Mechanism:** Progressive —— 每个 turn 开始前,CC 用 LLM 决定「given current turns,who speaks next?」。Higher token cost。
- **When to use:** Highly dynamic discussions where the next speaker depends on the topic of the current opinion(如 brainstorm、cross-disciplinary exploration)。
- **PoC scope:** v11.0 PoC 支持(但有 token cost caveat);`seed` 可为空。
- **B2.1 citation:** AutoGen/MAF 三态中的 "llm" 形态 —— MAF 1.0 GA(2026-04)推荐 LLM-driven speaker selection,但成本高。

#### §2.5.4 — matrix(FSM transition matrix)

- **Mechanism:** Pre-defined FSM transition matrix —— 每个 `(currentSpeaker, opinionContent)` pair maps to next speaker。E.g. `(screenplay, "I disagree with cinematographer's framing") → cinematographer`。Cite **B2.1**(AutoGen/MAF "matrix")+ **B8.2**(A2A Task lifecycle FSM)。
- **When to use:** Highly structured debates with predictable response patterns(如 devil's-advocate round、formal rebuttal protocol)。
- **PoC scope:** Simple 2-state matrix(2-3 transitions)v11.0 PoC 支持;full matrix editor(UI for defining transitions)deferred to v11.1+。

#### §2.5.5 — fitness-weighted(deferred to v11.1+)

- **Mechanism:** Higher-`fitness_score` panelists speak first(framing the discussion for lower-fitness panelists to react to)。
- **When to use:** When fitness data is mature(≥10 fitness runs per agent)。
- **Why deferred(OQ-2 explicit deferral):** Needs ≥10 fitness data points per agent to be meaningful,which won't exist at PoC start(fitness_score cold-start per OQ-4 + Phase 45 agents-schema §2.15)。v11.1+ after curator `_memory_evolution_phase` 积累 enough fitness_trend.jsonl entries 时启用。
- **B2.1 citation:** MAF "fitness" mode inspiration(MAF 不直接支持,但 concept 可借鉴)。

#### §2.5.6 — Strategy 选择的决策树(给 CC 实施者参考)

```
┌──────────────────────────────────────────────────────────────────┐
│ CC 决定 turnOrderStrategy 的决策树                                │
│                                                                  │
│  1. Round 是否有明确的 seniority / role ordering?                 │
│     YES → fixed(compliance_gate 最后发言等)                     │
│     NO  → 继续                                                   │
│                                                                  │
│  2. Round 是否是高度结构化的 rebuttal / devil's-advocate?         │
│     YES → matrix(预定义 transition matrix)                      │
│     NO  → 继续                                                   │
│                                                                  │
│  3. Round 是否需要 dynamic speaker selection(下个 panelist      │
│     依赖 current opinion 的内容)?                               │
│     YES → llm(progressive,token cost HIGH)                      │
│     NO  → round-robin(default,token cost ZERO)                  │
└──────────────────────────────────────────────────────────────────┘
```

**Default 路径:** 80%+ 实际 round table 用 round-robin 即可。`fixed` 用于 audit / compliance 场景(20%);`matrix` / `llm` 是 niche(rare);`fitness-weighted` deferred to v11.1+(0% at PoC)。

### §2.6 — Agent Deletion Semantics(open-time snapshot,OQ-5 resolution)

**问题(OQ-5):** Round table 进行中,operator 编辑或删除某 panelist 的 agent YAML。如何保证 transcript integrity?

**Resolution:open-time snapshot。**

1. **PanelistSnapshot at open time:** `round_table_open` 时,Hermes captures 每个 panelist 的 `agentId` / `personaSha256` / `fitnessScore` / `tools` / `memoryScope`(详见 round-table-state-schema.yaml $defs.PanelistSnapshot)。这个 snapshot 在 state file 中是 **THIS round 的 authoritative record** —— 即使 agent YAML 后续被编辑或删除,snapshot 不变。
2. **Deletion detection:** Hermes 在 next state-file read(如 turn append / status flip)时,检测 agent YAML 是否还存在。若不存在,flip `PanelistSnapshot.deleted = true`。
3. **Subsequent turn handling:** Subsequent turns for that `panelistId` are skipped —— CC 在 turn selection 时跳过 `deleted=true` 的 panelist。Transcript 中显示 `[deleted]` badge。
4. **Transcript integrity(OQ-5 verbatim resolution):** This preserves transcript integrity —— readers can always understand what was debated even if agents are later removed。后续 readers(包括 curator 的 conflict-log review)看到的是 open-time 状态,而不是 current state。

**Implementation note:** `PanelistSnapshot` 不缓存 `persona` 全文(避免 state file 膨胀)—— 只缓存 `personaSha256`。如果 CC 在 turn N 需要 panelist 的 persona(例如 for re-fork),CC 通过 `get_agent_persona(agentId)` 重新读 YAML —— 但如果 agent 已 deleted,这个 call 会失败,fallback to snapshot's `personaSha256`(显示 hash 表示「this is what the agent was at open time」)。

**Worked example:**

- T0: `round_table_open(panel=[screenplay, cinematographer, hook_retention, theory_critic])` —— 4 个 PanelistSnapshot 写入 state file。`screenplay.personaSha256 = "abc123..."`。
- T1 (turn 3): `cinematographer` 给出 opinion。
- T2: Operator 手改 `screenplay.agent.yaml` 的 persona(增加新规则)。`screenplay.persona_sha256` 变为 `"def456..."`。
- T3 (turn 4): CC 想调用 `screenplay`。Hermes reads state file,发现 `personaSnapshots["screenplay"] = "abc123..."` ≠ current `screenplay.persona_sha256 = "def456..."`。Hermes **flags drift**,在 state file append 一个 `conflict: {type: persona-drift, agentId: screenplay, oldHash: "abc123...", newHash: "def456...", detectedAt: T3}`。
- T4: CC 决定:(a)继续用 screenplay 的新 persona(flag 为 "post-edit opinion"),或(b)skip screenplay 这次 turn。Default 行为是 (a) —— round table 不因 persona edit 中断,但 conflict log 留 record 给 curator 后续 review(curator 可能决定 invalidate 该 round 的 conflict resolutions,因为它们基于旧 persona)。

**这个 worked example 是 load-bearing** —— 它展示了 OQ-5 resolution 不只是「snapshot 一下就完事」,而是包含 drift detection + conflict log + curator review 的完整 lifecycle。

### §2.7 — Early-Stop Conditions(consensus / max-rounds / manual / comparator-confident)

`EarlyStopRule` 由 Phase 44 决策 7 显式归属:**Hermes owns the rule via schema**(round-table-state-schema.yaml $defs.EarlyStopRule);**CC owns detection**(Hermes 不 monitor turns real-time,CC polls state file)。

| `type` | Mechanism | Token cost | PoC scope |
|---|---|---|---|
| `consensus` | All N panelists' latest turns agree on conclusion(semantic match via comparator LLM) | HIGH —— 每 round 后跑一次 comparator | v11.0 PoC 支持 |
| `max-rounds` | `turnIndex > maxRounds`(default 5) | ZERO —— 简单 integer 比较 | v11.0 PoC 支持 |
| `manual` | CC or operator 显式 call `submit_round_table_result` | ZERO | v11.0 PoC 支持 |
| `comparator-confident` | Comparator LLM confidence on conflict resolution ≥ `threshold`(default 0.85) | MEDIUM —— 与 conflict detection 复用 comparator call | v11.0 PoC 支持 |

**Hermes-side vs CC-side(决策 7 边界):** Hermes 在 `submit_round_table_result` validation 时检查 `earlyStopRule.type` 是否满足(如 `max-rounds` 时 `turnIndex > maxRounds` 才允许 submit,否则 return 400 Bad Request)。CC 在 turn-by-turn 调用时主动检测 early-stop 条件,trigger `submit_round_table_result`。两层职责清晰:Hermes 验证、CC 检测。

### §2.8 — Serial Invariant Restatement(OQ-8 load-bearing)

§2.2 step "Serial invariant" 是 load-bearing constraint。Restated:

> Each `await get_agent_opinion(...)` MUST complete before the next panelist's turn begins.
> No `Promise.all` over panelists. No background opinion polling. No concurrent LLM calls.

**Root cause analysis in §4.1** —— 简言之:GLM 4-key rotation × 7 panelist × N rounds 并发会立刻撞 ~800K TPM ceiling。MEMORY.md `feedback-glm-overload-reduce-concurrency.md` 已记录 global concurrency==1 是 BY DESIGN(5→3→1 演进),不可降。

**Implementation discipline(详见 §4.1):**

1. v11.0 PoC `get_agent_opinion` 实现 MUST 在 for-loop 中 sequential `await`,NEVER `Promise.all` 或 async-gather。
2. Hermes dispatcher MUST reject concurrent `get_agent_opinion` calls for same `roundId`(return 429)。
3. v11.0 PoC MUST NOT 添加 "parallel round table" mode 即使作为 opt-in feature flag —— 这条约束是 structural,不是 configurational。

---

## §3 — Memory Conflict Arbitration(P7 完整 mitigation)

### §3.0 — 本节是 PITFALLS §Pitfall 7 的完整 mitigation

本节是 **PITFALLS §Pitfall 7(Round-Table Memory Conflict)的完整 mitigation**。P7 是 v10.0 round table 的核心风险 —— 多个 agent 引用各自的 scoped memory 达到矛盾结论,**无显式仲裁时 debate 被 'loud memory' agent 主导**(citation 数量胜过 correctness)。

**PITFALLS §Pitfall 7 verbatim 引文:**

> In a round table, the `screenplay` agent (memory: "test audiences in this project respond well to bittersweet endings") and the `theory_critic` agent (memory: "tragedy endings test 23% better than bittersweet across all projects") reach contradictory conclusions. The round table deadlocks or, worse, the loudest-memory agent wins by sheer volume of citations rather than correctness.
>
> **Concrete mitigations:**
> 1. Memory annotation in round-table turns.
> 2. Coordinator (Hermes) arbitrates conflicts.
> 3. Scope precedence rules (session > project > global).
> 4. Confidence-weighted voting.
> 5. Conflict log for curator review.

本节 5 个子机制对齐 PITFALLS §P7 mitigation 1-5:

| § | 子机制 | PITFALLS §P7 mitigation | 物理载体 |
|---|---|---|---|
| §3.1 | Memory annotation in turns | mitigation 1 | `Turn.citedMemoryIds` field in round-table-state-schema.yaml |
| §3.2 | Comparator LLM pass | mitigation 2 | Hermes coordinator role + prompt template |
| §3.3 | Scope precedence rules | mitigation 3 | session > project > global 推理规则 |
| §3.4 | Confidence-weighted voting | mitigation 4 | memory-record-schema `confidence` field + tie-break rule |
| §3.5 | Conflict log for curator review | mitigation 5 | `state.conflicts` array + curator periodic pass |

**所有引用 Phase 45 memory-record-schema 字段**(`record_id` / `scope` / `confidence` / `evidence_chain` / `evidence_operator_ids` / `status` / `confidentiality` / `persona_sha256`)采用 **CITE-ONLY 策略,不重定义**。Phase 45 schema 是 authoritative source,本节只在引用处标注「Cite memory-record-schema field X」。

### §3.1 — Memory Annotation in Turns(P7 mitigation 1)

**PITFALLS §P7 mitigation 1 verbatim:**

> When an agent cites a memory in its turn, the citation includes `memory_id`, `confidence`, `scope` (global/project/session), and `evidence_record_count`. Other agents can challenge: "I disagree with memory_id #423 because my memory_id #612 contradicts it." This makes disagreement explicit and traceable.

**Mechanism(详):**

- **Field:** `Turn.citedMemoryIds`(list of UUID v4)—— 详见 round-table-state-schema.yaml `$defs.Turn`。
- **At turn-append time:** 当 panelist 的 opinion 引用一个 memory 时,该 memory 的 `record_id` 被 append 到 `citedMemoryIds`。CC 在 `get_agent_opinion` 的返回值(`AgentOpinionResult`)中拿到 `citedMemoryIds` 后,直接 append 到 state file 的对应 turn。
- **Challenge mechanism:** 下一个 panelist 可以在自己的 turn 中显式 disagree with prior turn's cited memory —— CC 在调用 `get_agent_opinion` 时把 prior turns 的 `citedMemoryIds` 作为 `priorDiscussion` argument 传给下一个 panelist,panelist 看到后可以表达 disagreement。
- **Citation enrichment:** Hermes 在 turn append 时,**denormalize** 每个 `record_id` 的 `scope` / `confidence` / `evidence_chain` / `confidentiality` 到 ConflictRecord(如果后续该 memory 被 challenge)。这样 comparator LLM 不需要在每次 conflict 时 re-fetch memory records(cite Phase 45 memory-record-schema fields `scope` §3.9 / `confidence` §3.5 / `evidence_chain` §3.6 / `confidentiality` §3.10)。

**Why this matters:** 没有 memory annotation,debate 就只能基于 panelist 的 opinion text —— 但 opinion text 不携带 confidence / scope / evidence chain 元数据,comparator LLM 无法做有依据的 arbitration。Memory annotation 把 arbitration 的「证据」explicit 化。

### §3.2 — Comparator LLM Pass(P7 mitigation 2)

**PITFALLS §P7 mitigation 2 verbatim:**

> Per PROJECT.md decision #7, "Hermes 控 turn_order / max_rounds / schema / early_stop_rule." Add a memory-conflict-arbitration responsibility: when two agents cite conflicting memories, Hermes (the coordinator) extracts both cited memories, runs a comparator LLM pass ("which is more applicable in this project context?"), and broadcasts the resolution to all participants.

**Trigger:** CC 检测到两个 panelist 的 `citedMemoryIds` 中包含 records 在语义上矛盾(embedding cosine similarity ≥ 0.7 + manual CC flag)。或者 CC 自己判断「这两个 memory 在说相反的事」。

**Coordinator(Hermes)role:** Phase 44 决策 7 + PITFALLS §P7 mitigation 2 给 Hermes 增加新职责 —— **memory conflict arbitrator**。具体职责:

1. **Extract both cited memories:** Hermes fetch full memory records(从 mem0 backend)by `record_id` —— 包括 `content` / `scope` / `confidence` / `evidence_chain` / `confidentiality`。
2. **Filter by confidentiality(P10 mitigation 2 propagation rule):** Comparator LLM 只能看到 `confidentiality ≤ current_project's_level` 的 records。如果 Memory A 是 `confidential` 但当前 project 是 `internal`,comparator LLM 只能看到 Memory B(internal),Memory A 被自动 lose(或 deferred-to-operator if Memory B is also low-confidence)。
3. **Run comparator LLM pass:** Hermes 用专用 prompt template(下方)调用 LLM,产出 `{resolution, rationale, confidence}` JSON。
4. **Broadcast resolution:** 把 `ConflictRecord` append 到 state file `conflicts` 数组。Subsequent turns 可以读到这个 resolution —— CC 在调用下一个 `get_agent_opinion` 时把 conflict resolution 作为 `priorDiscussion` 传给后续 panelist,让他们 know about the resolution。

**Comparator LLM prompt template(v11.0 PoC-ready):**

```
You are arbitrating a memory conflict in a Hermes round table.
Project context: {project_id}
Question under debate: {question}

Memory A (cited by panelist {panelistA}):
- content: {memoryA.content}
- scope: {memoryA.scope} (global | project | session)
- confidence: {memoryA.confidence} (0.0-1.0)
- evidence_chain length: {len(memoryA.evidence_chain)}
- evidence_operator_ids: {memoryA.evidence_operator_ids}

Memory B (cited by panelist {panelistB}):
- content: {memoryB.content}
- scope: {memoryB.scope}
- confidence: {memoryB.confidence}
- evidence_chain length: {len(memoryB.evidence_chain)}
- evidence_operator_ids: {memoryB.evidence_operator_ids}

Apply scope precedence: session > project > global
  (a session-scoped memory overrides global for THIS session;
   a project-scoped memory overrides global for THIS project).

Apply confidence-weighting: at the same scope level, higher confidence wins.
  If both memories are at the same scope level AND confidence within 0.05 of
  each other, defer to operator (human review).

Apply evidence diversity check: prefer memory with more diverse
  evidence_operator_ids (≥2 distinct operators per Phase 45 §3.7).

Output JSON:
{
  "resolution": "A-wins" | "B-wins" | "both-kept" | "both-quarantined" | "deferred-to-operator",
  "rationale": "<=200 chars human-readable",
  "confidence": 0.0-1.0
}
```

**Token cost estimate:** ~2K input tokens + ~200 output tokens per comparator call ≈ 2.2K tokens total。若 round table 有 3 个 conflict,总 comparator 成本 ≈ 6.6K tokens(round table 总 ~150-300K tokens 中的 ~2-4%)。**v11.0 PoC 监控指标:** if >3 conflicts/round,成本 balloons —— `earlyStopRule=comparator-confident` 可以 cap this。

### §3.3 — Scope Precedence Rules(P7 mitigation 3)

**PITFALLS §P7 mitigation 3 verbatim:**

> When conflicts arise, scope precedence is: `session` > `project` > `global`. A project-scoped memory ("this project's audience prefers X") overrides a global-scoped memory ("audiences in general prefer Y"). The arbitration LLM is told the scope precedence and resolves accordingly.

**Rule:** `session > project > global`。

**Citation:** Phase 45 memory-record-schema §3.9 `scope` field(enum: global/project/session)是 authoritative definition。本节不重定义,只引用。

**Implementation philosophy:** Comparator LLM **在 prompt 中被告知** scope precedence,LLM 在 in-context 推理时应用。**没有 Hermes-side hard rule** —— 即不是「if scopeA=session and scopeB=global then return A-wins」,而是「LLM 看到 scopeA=session,scopeB=global,被告知 session 优先,LLM 自己 reach A-wins conclusion」。这种 in-context 推理保留了 LLM 对 edge case 的判断力(如 session-scoped memory 内容明显错谬时,LLM 可以 defer-to-operator)。

**Edge case(3+ way conflict):** 如果 3+ memories 在不同 scope 冲突:

- Step 1: 按 scope 排序:session > project > global。
- Step 2: 取 highest scope level 的 memory(如 session-scoped),与其他 memories pairwise 跑 comparator。
- Step 3: 若 highest-scope memory 胜出所有 pairwise,resolution=its-wins。
- Step 4: 若 highest-scope memory 在某 pairwise 输了(如 confidence 太低),flip 到 confidence-weighted voting(§3.4)。

**Example(详):**

- T1: `screenplay` cites Memory A(`scope=project`, confidence=0.95): "Volvo project's audience prefers bittersweet endings"。
- T2: `theory_critic` cites Memory B(`scope=global`, confidence=0.85): "Tragedy endings test 23% better across all projects"。
- T3: `cinematographer` cites Memory C(`scope=session`, confidence=0.6): "For this specific round, we agreed on bittersweet"。
- T4: CC detects 3-way conflict。
- Step 1: 排序:session(C) > project(A) > global(B)。
- Step 2: comparator(C vs A):C scope 更高,但 C confidence=0.6 低,A confidence=0.95 高 —— LLM 可能 defer-to-operator(差距 > 0.3 but scope 不同)。
- Step 3: comparator(C vs B):C scope=session > B scope=global,但 C confidence 0.6 vs B confidence 0.85 —— 同上,LLM 应用 scope precedence but C confidence 太低,可能 resolution=deferred-to-operator。
- Step 4: 最终 resolution=deferred-to-operator;operator 决定。
- T5: Conflict log records all 3 pairwise resolutions;curator 后续 review 时检查为何 session-scoped memory confidence 这么低(可能需要 curator boost evidence 或 quarantine)。

### §3.4 — Confidence-Weighted Voting(P7 mitigation 4)

**PITFALLS §P7 mitigation 4 verbatim:**

> When N agents in a round table disagree, vote weighted by memory `confidence` field. If `screenplay` cites a 0.95-confidence project memory and `theory_critic` cites a 0.6-confidence global memory, screenplay's vote weighs more. Ties broken by coordinator.

**Rule:** 当 N panelists 在**同一 scope level** disagree(如都 `scope=global`),投票 weighted by `confidence` field(cite Phase 45 memory-record-schema §3.5)。Higher confidence 胜出。

**Tie-break rule(Hermes-side deterministic):** 如果 A-wins 和 B-wins 的 confidence 差距 ≤ 0.05,则 resolution=**`deferred-to-operator`**(human review)。**没有 Hermes 自动 tiebreak** —— 因为 tiebreak 规则越复杂,越容易出现 deterministic-but-wrong 决策。deferred-to-operator 把判断权交回 human,虽然慢但更安全。

**Worked example:**

- `screenplay` cites Memory A(scope=project, confidence=0.95)。
- `theory_critic` cites Memory B(scope=project, confidence=0.92)。
- Same scope level → confidence-weighted voting applies。
- Δconfidence = |0.95 - 0.92| = 0.03 < 0.05 → resolution=`deferred-to-operator`。
- Conflict log: `{resolution: "deferred-to-operator", rationale: "Tie at project scope (Δconfidence=0.03 < 0.05)"}`。
- Round table continues but conclusion flagged "low-confidence" —— CC 在 final synthesis 中显式注明「two competing project memories, neither dominant」。

**Citation:** Phase 45 memory-record-schema §3.5 `confidence` field(default 0.5 = neutral)。

### §3.5 — Conflict Log for Curator Review(P7 mitigation 5)

**PITFALLS §P7 mitigation 5 verbatim:**

> Every round-table conflict is logged with both cited memories, the resolution, and the rationale. Curator's periodic pass reviews high-frequency conflicts (same memory pair conflicting >3 times) and may promote one to global scope or quarantine the loser.

**Field:** `state.conflicts` array(`ConflictRecord` objects,详见 round-table-state-schema.yaml)。

**Persistence rules:**

- 在 `status=open` 时,comparator LLM 产出的 `ConflictRecord` 实时 append 到 `conflicts` 数组。
- 在 `submit_round_table_result` 时(`status: open → completed`),`conflicts` 数组 **sealed**(immutable)—— 防止 post-hoc 篡改。
- Conflict log 是 curator 后续 review 的输入。

**Curator review mechanism:**

- Curator 的 periodic pass(扩展自 v6.0 `_feedback_scan_phase`,详 Phase 45 §5 `_memory_evolution_phase` contract)扫描所有 completed round tables 的 `conflicts` 数组。
- **High-frequency conflict detection:** 若同一 memory pair(`memoryIdA` + `memoryIdB`)在跨 round tables 中 conflict > 3 次,curator 可能:
  - **Promote** winner 到更高 scope level(如 `scope=project` → `scope=global`)—— 表示「这个 project-specific insight 在多 project 都成立」。
  - **Quarantine** loser —— flip `status: active → quarantined`(cite Phase 45 memory-record-schema §3.8 `status` field)—— 该 memory 从后续 retrieval 中 excluded,直到 operator resolve。
- Curator decisions 写入 evolution_log(cite Phase 45 agents-schema §2.14 `evolution_log`)+ memory record 的 evidence_chain(cite Phase 45 memory-record-schema §3.6 `evidence_chain` field,append `{source_type: "round_table", source_id: <round_id>, ...}` entry)。

**Citation:** PITFALLS §P7 mitigation 5 verbatim + Phase 45 §5 `_memory_evolution_phase` contract + agents-schema §2.14 `evolution_log` + memory-record-schema §3.6/§3.8。

### §3.6 — Comparator LLM Decision Tree + Edge Cases

**Decision tree(详):**

```
┌──────────────────────────────────────────────────────────────────┐
│ Comparator LLM decision tree                                     │
│                                                                  │
│  1. Are scopes different?                                        │
│     YES → Apply scope precedence (session > project > global):   │
│            higher-scope memory wins unless confidence < 0.3      │
│            (extreme low confidence → defer to operator)          │
│     NO  → continue (same scope level)                            │
│                                                                  │
│  2. Are confidences within 0.05 of each other (tie)?             │
│     YES → resolution = deferred-to-operator                      │
│     NO  → continue                                               │
│                                                                  │
│  3. Higher confidence wins:                                      │
│     - Δconfidence ≥ 0.3 → A-wins or B-wins (decisive)            │
│     - Δconfidence 0.05-0.3 → winner by confidence, but flag      │
│       "low-decisiveness" in rationale for curator review         │
│                                                                  │
│  4. Special cases:                                               │
│     - Both confidences < 0.3 (no-confidence tie):                │
│       resolution = both-quarantined                              │
│     - Confidentiality mismatch (one memory invisible to project):│
│       comparator sees only the visible one; auto-wins unless     │
│       that one is also low-confidence → deferred-to-operator     │
└──────────────────────────────────────────────────────────────────┘
```

**5 possible `resolution` values + their follow-up actions:**

| `resolution` | Follow-up action |
|---|---|
| `A-wins` | Memory B's `supersedes_memory_id` chain updated to point to A's `record_id` (cite Phase 45 memory-record-schema §3.3 `supersedes_memory_id`); B's `status: active → superseded` |
| `B-wins` | Symmetric to A-wins |
| `both-kept` | No action; both records remain `active`. Comparator determined they apply in different contexts |
| `both-quarantined` | Both records' `status: active → quarantined` (cite Phase 45 §3.8); round aborts with `status=aborted`; operator review triggered |
| `deferred-to-operator` | No automatic action; round continues but conclusion flagged "low-confidence"; curator surfaces in next `_feedback_scan_phase` |

### §3.7 — Edge Cases(3+ way conflict / no-confidence tie / all-quarantined)

**Edge case 1: 3+ way conflict**

- **Scenario:** 3+ panelists cite memories that pairwise contradict(详 §3.3 example)。
- **Mechanism:** Decompose into pairwise comparator calls;majority resolution wins。若 pairwise resolutions disagree(如 A vs B = A-wins, B vs C = B-wins, A vs C = C-wins —— cycle),整个 conflict set resolution=`deferred-to-operator`。
- **Token cost:** 3-way conflict = 3 pairwise calls ≈ 6.6K tokens;v11.0 PoC warns if 4+ way conflicts emerge(成本 exponential)。

**Edge case 2: No-confidence tie**

- **Scenario:** All panelists cite memories with `confidence ≤ 0.3`(extreme low confidence)。
- **Mechanism:** Resolution=`deferred-to-operator`。Round table continues but conclusion flagged "low-confidence"。CC 在 final synthesis 显式注明「all cited memories low-confidence; operator review needed before action」。
- **Why not auto-quarantine?** Low-confidence 不等于 wrong —— 可能只是 evidence_chain 不充分。Quarantine 是 stronger action(reserved for `both-quarantined` case)。

**Edge case 3: All quarantined**

- **Scenario:** Comparator determines all cited memories should be quarantined(如所有 memory 来自同一 operator 但 conflict with project state,indicating poisoning attempt per P6 mitigation)。
- **Mechanism:** Round aborts with `status=aborted`(详 round-table-state-schema.yaml `status` enum)。Operator review triggered —— 可能是 MINJA-style attack(P6)or curator hallucination(P5)or evidence-chain corruption。
- **Audit trail:** `state.conflicts` 数组保留所有 ConflictRecord;`submitRoundTableResult` block 不写入(`status=aborted` 不通过 submit_round_table_result,通过单独的 `round_table_abort` —— v11.1+)。Conflict log 仍 sealed 给 curator review。

---

## §4 — Hard Constraints:Root-Cause Analysis + OQ/BP Audit

### §4.0 — 本节展开 §1.5 的 3 个 hard constraints

本节展开 §1.5 声明的 3 个 hard constraints(serial / STACK naming / atomic),给出每个的 root cause 分析。本节还包含 6 个 Open Questions(OQ-2/OQ-5/OQ-8/OQ-9/OQ-11/OQ-15)的决议审计表 + 7 个 borrowable points(B1.4/B2.1/B2.3/B4.2/B6.1/B7.3/B8.2)的覆盖审计表。

### §4.1 — Serial Execution Root Cause(OQ-8 + MEMORY.md verbatim)

**OQ-8 resolution:** Strict serial. 1 panelist 1 turn sequential `await`. 不能并发 LLM 调用。

**MEMORY.md verbatim citation(`feedback-glm-overload-reduce-concurrency.md`):**

> GLM 持续报 1305/overloaded 时,先 grep `~/.hermes/config.yaml` 里的 `glm.global_concurrency`。**演进历程**:**2026-07-03 从 5→3;2026-07-06 已是 1**。
>
> **Why:** GLM 的 anthropic-compatible 端点对并发敏感。降并发是有效的(5→3 显著减少过载);但 **concurrency 到 1 之后再降不动了——上游模型容量本身就是瓶颈**,跟本地并发无关。切 endpoint 也没用:`zai`(paas/v4)和 `zhipu-anthropic`(/api/anthropic)共享 Zhipu 后端,1305 错误是模型容量错误,不是端点错误。
>
> **How to apply:**
> - 如果 `global_concurrency > 1`:降到 1...
> - 如果 `global_concurrency == 1`:不要建议重启或继续降。此时三道安全网在工作:(1) 4-key rotation `kai-multi-1 <-> kai-multi-2`(commit 5839b5f78 保证 1305 不标 exhausted,key 保留);(2) `GLM early-abort: 3 consecutive overloaded`(3 次连续就放弃,不耗尽 10 次 retries);(3) gateway 持久化用户消息到 session,context 在用户重试时保留。
> - Telegram 用户会收到 115 字符的「暂停 10-15 分钟」消息,这是 by design,**不需要立刻做什么**。

**Token cost math(cite STACK §7):**

- STACK §7 估算 single pipeline run ≈ **550K tokens**(80 opinion calls × 6.5K tokens per call),assuming serial。
- GLM ceiling:**4 keys × 200K TPM ≈ 800K TPM**(per FEATURES §14 gap 6)。
- Round table worst case:**7 panelists × 3 rounds × 6.5K tokens = 137K tokens** total —— fine serially(~10 seconds at 800K TPM),but **catastrophically bad in parallel**(7 concurrent calls × 6.5K = 45K tokens/turn × 3 rounds = 135K tokens burst in <1 second,瞬间撞 ceiling)。
- Concurrent round table 还会触发 GLM `early-abort`(3 consecutive overloaded → abort),导致 round table 失败 + Telegram 用户收到「暂停」消息 —— **operator-level discipline 被 round table layer 破坏**。

**Implementation discipline(load-bearing,3 invariants):**

1. v11.0 PoC `get_agent_opinion` 实现 MUST 在 for-loop 中 sequential `await`,NEVER `Promise.all` 或 async-gather。
2. v11.0 PoC dispatcher(Hermes-side)MUST reject concurrent `get_agent_opinion` calls for same `roundId`(return 429 Too Many Requests)。
3. v11.0 PoC MUST NOT 添加 "parallel round table" mode 即使作为 opt-in feature flag —— **这条约束是 structural,不是 configurational**。

**Why this is non-negotiable:** MEMORY.md `feedback-glm-overload-reduce-concurrency.md` records Kai's explicit decision(5→3→1 deprecation cycle over 3 days:2026-07-03 从 5→3,2026-07-06 已是 1)。Telegram 用户 receiving 115-char "暂停 10-15 分钟" messages is **BY DESIGN**。Re-introducing parallelism at the round table layer would undo this operator-level discipline,让 v10.0 design 直接撞 GLM ceiling,导致 round table 在生产环境不可用。

### §4.2 — MCP Tool Naming STACK Form(OQ-9 + reconciliation table)

**OQ-9 resolution:** STACK §3.2 form wins. No `agent_` prefix. Aligns with existing 9 messaging tools.

**Reconciliation table(ARCHITECTURE §4.2 → STACK §3.2 canonical):**

| ARCHITECTURE §4.2(deprecated) | STACK §3.2(canonical, ADOPTED) | Used in this doc |
|---|---|---|
| `agent_get_persona` | `get_agent_persona` | §2.1, §5.1 |
| `agent_recall` | `get_agent_memory` | §3.1, §5.3 |
| `agent_opinion` | `get_agent_opinion` | §2.2, §5.2 |
| `agent_conclude` | `submit_round_table_result` | §2.3, §5.4 |
| (new) | `submit_artifact` | §5.5 |
| (new) | `query_memory` | §5.6 |
| (new) | `run_python_phase` | §5.7 |
| (new) | `agents_list` | (not used in this doc; discovery tool) |
| (new) | `round_table_open` | §2.1, §5.0 |

**SUMMARY.md CC-1 verbatim citation:**

> STACK §3.2 uses `get_agent_persona` / `get_agent_memory` / `query_memory` (no prefix), ARCHITECTURE §4.2 uses `agent_get_persona` / `agent_recall` / `agent_conclude` (agent_ prefix). CONFLICT — downstream `02-ROUND-TABLE-PROTOCOL.md` MUST unify naming first. **Recommendation: STACK form (no prefix, aligns with existing `mcp_serve.py` 9 messaging tools style).**

**Rationale(详):** Existing `mcp_serve.py` 9 个 messaging tool 是 `conversations_list` / `messages_read` / `messages_send` / `events_poll` / `permissions_respond` / `channels_list` / `conversations_archive` / `messages_search` / `conversations_create`(no `messaging_` prefix)。Adding `agent_*` prefix 给 round table tool 会破坏 tool list 视觉一致性,让 CC dispatcher 实施者(以及 CC user)混淆 —— 「为什么 messaging tool 没有 prefix 但 agent tool 有?」STACK form 保留风格统一。

**Phase 51 VALIDATE lint script 强制:** Phase 51 VALIDATE phase 的 lint script 检查 `mcp_serve.py` 实际注册的 7 个 round table tool 名是否与本 doc §5 + STACK §3.2 一致。不一致触发 ADVISORY 提醒(Phase 51 是设计型,不 block)。

### §4.3 — OQ Resolution Audit Table(6 OQs in scope)

下表 audit 本 doc 解决的 6 个 OQ(摘自 SUMMARY.md "Open Questions Consolidated" 表):

| OQ# | 问题(一句话) | 倾向性结论(SUMMARY) | 本 doc 解决章节 | 是否 defer |
|---|---|---|---|---|
| **OQ-2** | round table `turn_order` 策略 | default round-robin + 4 alternative strategies | §2.5(5 strategies deep dive + decision tree) | partial —— fitness-weighted + full matrix editor → v11.1+ |
| **OQ-5** | agent deletion transcript integrity | open-time snapshot + deleted flag | §2.6 + round-table-state-schema.yaml `PanelistSnapshot.deleted` field | NO |
| **OQ-8** | GLM 4-key rotation × concurrency | strict serial,1 panelist 1 turn await | §1.5.1 + §2.8 + §4.1(MEMORY.md verbatim) | NO(non-negotiable,by design) |
| **OQ-9** | MCP tool naming | STACK form(no prefix) | §1.5.2 + §4.2 + §5 | NO |
| **OQ-11** | round_id source | CC self-generates UUID v4 | §2.1 + round-table-state-schema.yaml `roundId` field | NO |
| **OQ-15** | round-table conflict arbitration | comparator LLM + scope precedence + confidence voting + conflict log | §3.0-§3.7(5 sub-mechanisms aligned with PITFALLS §P7 mitigation 1-5) | NO |

**No OQs deferred without rationale.** OQ-2 的 partial deferral(fitness-weighted + matrix editor)有 explicit rationale(详见 §2.5.5 + §2.5.4 PoC scope notes):fitness 需要 ≥10 数据点,PoC cold-start 不具备;matrix editor 需要 UI,v11.0 PoC scope 限 backend。其余 5 个 OQ 全部 v11.0 PoC 必须 support,不 defer。

### §4.4 — Borrowable Points Coverage Audit(7 BPs)

下表 audit FEATURES §10 borrowable points B1.4 / B2.1 / B2.3 / B4.2 / B6.1 / B7.3 / B8.2 在本 doc 的覆盖:

| BP# | Source | Borrowable idea | Where addressed in this doc | How adapted |
|---|---|---|---|---|
| **B1.4** | LangGraph | hierarchical supervisor → round table nesting | §6.1(subpanel evaluation) | panelist `can_convene_subpanel` flag —— additive field deferred to v11.1+; v11.0 PoC is single-level only |
| **B2.1** | AutoGen/MAF | turn_order three-state(llm/fixed/matrix) | §2.5(5 strategies deep dive) | 5-strategy enum(round-robin + fixed + llm + matrix + fitness-weighted)—— 扩展了 AutoGen 三态 |
| **B2.3** | AutoGen | nested chat → panelist convenes sub-round table | §6.1(subpanel evaluation) | opt-in flag;v11.1+;与 B1.4 共用 implementation |
| **B4.2** | Claude Agent SDK | hooks lifecycle → PreTurn/PostTurn audit | §6.2(audit hooks evaluation) | Hermes emits PreTurn/PostTurn events to state file;v11.0 implicit via Turn schema;v11.1+ explicit event stream |
| **B6.1** | Camel-AI | generator+critics → panelist_role field | §6.3(panelist_role evaluation) | enum: generator/critic/synthesizer/reviewer;v11.1+ additive field on PanelistSnapshot |
| **B7.3** | Agent-MCP | file-level lock → multi-agent parallel asset_locks | §6.4(asset_locks evaluation) | deferred —— v11.0 is serial so locks are trivial;required only if subpanels(§6.1)are added in v11.1+ |
| **B8.2** | A2A | Task lifecycle FSM → turn state machine | §2.2(turnstile FSM)+ round-table-state-schema.yaml `status` enum | turn FSM: pending → speaking → submitted →(optionally)challenged;status FSM: open → completed/aborted/stalled |

**No BPs dropped without rationale.** All 7 borrowable points explicitly addressed —— 4 are v11.0 PoC-mandatory(B2.1 / B8.2 + indirectly B4.2 via Turn schema + B7.3 trivially satisfied by serial);3 are v11.1+ deferred with explicit rationale(B1.4 / B2.3 / B6.1 / partially B4.2 explicit event stream)。

---

