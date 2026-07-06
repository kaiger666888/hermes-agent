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
