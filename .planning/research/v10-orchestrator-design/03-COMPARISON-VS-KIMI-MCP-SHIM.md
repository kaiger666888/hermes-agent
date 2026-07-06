# 03 — T6 vs Kimi 全 MCP Shim:7 维度对照 + Subagent 否决论据库 + Microsoft 三层协议验证

> **Document status:** design-2026-07-07-v10comparison · supersedes: none · superseded_by: TBD
> **Milestone:** v10.0 — Hermes-Agent 编排架构第一性原理推导(设计型 milestone)
> **Phase:** 47 of v10.0 design milestone · **Authors:** hermes-agent design team
> **Audience:** Kai(设计决策 reviewer)+ Kimi(Notion 续聊对照 / Kimi 架构2.0 作者)+ 未来 v11.0 PoC 实施者
> **Reading time:** ~28 minutes(全文)/ ~6 minutes(§0 + §1.1 + §1.6 TL;DR table)
> **Stability:** §1 + §3 + §4 + §5 + §6 + §7 全部 `stable`(修改需开新设计-修订里程碑);§2 steelman `stable`(Kimi 方案 reconstruction 固定);§8 citation `stable`
> **Confidence:** HIGH(本 doc 所有论据源自 Phase 44 锁定的 7 决策 + Phase 45 锁定 schema + Phase 46 锁定 protocol + 4 份 Phase 44 research docs,每个 claim 都有 section-and-line 精确 citation;本 doc 是 horizontal validation,不发明任何新决策)

---

## §0 — 阅读指南

本文档是 **v10.0 设计型 milestone 的横向验证(horizontal validation)文档**,产出**单一 deliverable**(无 schema YAML,与 Phase 45/46 不同):把 Phase 44 锁定的 7 决策、Phase 45 锁定的 schema 字段、Phase 46 锁定的 protocol 不变量,通过「与 Kimi Notion 架构2.0 的 full MCP shim 方案逐维对照」的方式,验证 T6 协议层在每个维度都更好地服务 v10.0 paradigm shift。同时为后续 v11.0 PoC 实施者提供「为什么 T6 不是 full MCP shim」「为什么 Hermes-side YAML agent 不是 CC subagent」的论据库 —— 当实施者问这些 why-not 问题时,本 doc 给出 section-and-line-precise 答案。

**与 Phase 44 `00-FIRST-PRINCIPLES.md` 的关系:** Phase 44 §2.1-§2.7 锁定的 7 决策(T6 协议 / B3a Python runner / D2 storyboard / G2 通用框架 / α agent form / per-agent memory / 分层 CC 角色)是本 doc 的**根论据 anchor**。本 doc **CITE ONLY, do NOT re-derive** 这 7 决策 —— 它们是已锁验证目标,本 doc 是横向对照验证。若本 doc 对照过程发现某决策需修正,§7.2 偏差分析会显式 surface + 提交 Phase 44 修订(预期 7/7 一致)。

**与 Phase 45 `01-AGENT-REGISTRY-SCHEMA.md` 的关系:** Phase 45 锁定的两个 schema(18-field `agents-schema.yaml` + 10-field `memory-record-schema.yaml`)是本 doc 的字段引用源 —— `memory_scope` / `scope` / `confidence` / `evidence_chain` / `evidence_operator_ids` / `status` / `confidentiality` / `fitness_score` / `persona_sha256` / `record_id` / `agent_id` / `expires_at` / `verified_at` 等字段在本文档出现时都是 CITE-ONLY,权威定义在 Phase 45 文件 + schema YAML。

**与 Phase 46 `02-ROUND-TABLE-PROTOCOL.md` 的关系:** Phase 46 锁定的协议契约(三原子操作 `round_table_open` → `get_agent_opinion` → `submit_round_table_result` + memory conflict arbitration + 强制 serial invariant)是本 doc 对照 Kimi 方案 subagent-return 模型的物理载体。本 doc §3.3 callback 维度 + §3.5 多 agent 维度 cross-reference Phase 46 §2 turn lifecycle + §3 memory conflict arbitration。

**与 Kai user memory 的关系:** Kai 在 2026-07-06(同一日 v10.0 milestone 启动)的两条 user memory 是本 doc 的 user-side 决策 anchor —— `hermes-native-expert-agents.md`(否决 Kimi CC-Teammates + 否决 "skill 当 agent",要 Hermes-side persistent agents + per-agent memory 自进化 + CC 仅做场地)和 `coding-agent-vs-mcp-shim.md`(v10.0 设计 milestone 必须把已有 coding-agent tmux 模式 vs Kimi Notion 架构2.0 MCP shim 作为竞品方案对照分析,增量演进而非重写)。本 doc §5.7 verbatim 引用这两条 user memory 作为 design-side 论证与 user-side 决策相互印证。

### 章节地图

| 章节 | 内容 | 阅读优先级(按角色) |
|---|---|---|
| §0 | 阅读指南(本节)+ 与 Phase 44/45/46 关系 + 与 Kai user memory 关系 | 所有人先读 |
| §1 | Framing:本 doc 是横向验证 + 7 决策 citation anchor + 5 SC 映射 + 3 load-bearing citations 前置声明 + §1.6 TL;DR 7-row quick-glance table | reviewer 必读 §1.1 + §1.5 + §1.6;PoC 实施者必读 §1.4 + §1.6 |
| §2 | Kimi 方案 steelman reconstruction(SDK origin / dispatch / memory / 全 MCP shim 含义 / 合理性陈述) | Kimi 续聊对照必读;reviewer 必读 §2.5(steelman closing) |
| §3 | 7-dimension contrast prose(协议 / dispatch / callback / state / 多 agent / 实现成本 / 稳定性,每维度 4 段结构 + 选型论据引用决策号) | **核心章节** — PoC 实施者 + 维护者必读 |
| §4 | Microsoft 三层协议 validation(SC#4 deep-dive,引用 FEATURES §7.4 B7.1 verbatim) | reviewer 必读;业界共识论证 |
| §5 | Subagent form rejection(SC#3 deep-dive,引用 FEATURES §11 B4.1 + §4.3 三个 fact) | reviewer 必读;v11.0 PoC 实施者必读 |
| §6 | Kimi-side borrowable parts evaluation(SC#5,7-row 借鉴条件评估表) | 决策者 + v12+ 设计者必读 |
| §7 | Phase 44 决策 1-7 cross-validation audit(7/7 ✅ 一致性声明) | reviewer 必读;Phase 51 VALIDATE lint 必读 |
| §8 | Downstream citation card + coherence 声明 + References | 04/05/06/51 docs 作者必读 |

### 稳定性标记(修改门槛)

| 章节 | 稳定性 | 修改门槛 |
|---|---|---|
| §1.1 framing(2 sides 显式枚举) | `stable` | 修改需开新设计-修订里程碑 |
| §1.5 (3 load-bearing citations 前置声明) | `stable` | 跟随 Phase 44 §3 + FEATURES §11 + ARCHITECTURE §8 |
| §1.6 (TL;DR 7-row table) | `stable` | 选型结论锁定,修改需重跑 §3-§6 论证 |
| §2 (Kimi 方案 steelman reconstruction) | `stable` | Kimi 方案 SDK origin / dispatch / memory reconstruction 固定,不随 Notion 续聊内容漂移 |
| §3 (7-dimension contrast prose) | `stable` | 选型论据锁定(决策 1-7),修改需开新设计-修订里程碑 |
| §4 (Microsoft 三层 validation) | `stable` | 跟随 FEATURES §7.4 B7.1 verbatim |
| §5 (subagent rejection) | `stable` | 跟随 FEATURES §11 B4.1 + §4.3 + Phase 46 §2/§3 + Kai user memory |
| §6 (Kimi borrowable evaluation) | `stable` | 借鉴 / 拒绝结论锁定;v11.1+ 借鉴条件可细化 |
| §7 (7 决策 cross-validation audit) | `stable` | 7/7 ✅ 一致性声明;若发现偏差必须 surface 到 §7.2 |
| §8 (citation + references) | `stable` | 跟随 §1-§7 |

### 受众指引(3 类读者)

- **Kai(reviewer / 设计决策者):** 先读 §0 + §1.1(framing)+ §1.5(3 load-bearing citations 前置声明)+ §1.6(TL;DR 7-row table)+ §7(7 决策 cross-validation audit,确认 7/7 ✅ 一致)。如果对某维度论据有疑问,跳到 §3 对应 §3.N。如果对 subagent rejection 论证有疑问,跳到 §5.1(B4.1 verbatim citation)+ §5.3(context-isolation 不适合 round table panelist 的 4 个原因)。§6.1 borrowable evaluation table 是给 v12+ 设计的快查表。

- **Kimi(Notion 续聊对照 / Kimi 架构2.0 作者):** 先读 §1.3(SC 映射,理解本 doc 解决哪些 ROADMAP SC),再读 §2(Kimi 方案 steelman reconstruction —— 本 doc 不预设评判地把对方立场最强形态摆出来),最后读 §3(7 维度逐维对照,理解每条 T6 pros / Kimi cons 都引用了 Phase 44 决策号)。本 doc 是横向验证,不是续聊对话节奏 —— Kai 与 Kimi 的 Notion 协作行为与本 doc 正交。

- **未来 v11.0 PoC 实施者:** 先读 §0 + §1.4(roadmap placement,理解本 doc 是 05-POC-PLAN 的 defense brief)+ §1.6(TL;DR table),然后用 §3 dimension table + §5 subagent rejection + §6.1 borrowable table 作为「why T6 not full MCP shim」的 defense brief —— 当 v11.0 PoC 实施者问「为什么我们 extend `mcp_serve.py` 而不是把 agent ↔ agent 也塞进 MCP?」或「为什么 agent YAML 放在 `~/.hermes/agents/` 而不是 `.claude/agents/`?」,§3.1 + §3.2 + §5.3-§5.5 给出可引用的 section-precise 答案。本 doc 不重新推导 Phase 44 决策 —— 实施者若发现某论据与决策推导矛盾,记录到 deferred-items.md。

---

## §1 — Framing:本 doc 是横向验证 + 7 决策 citation anchor

### §1.1 — 定位:本 doc 是 v10.0 决策 1 (T6) 的横向验证 + subagent 形态否决的论据库

本文档定义 v10.0 决策 1(T6 协议层)的横向验证 —— 把 **SIDE A:T6**(Hermes MCP server 扩展现有 `mcp_serve.py` + tmux dispatch 复用 v7.0 `coding-agent` skill + CC native MCP client 通过 `~/.claude.json` stdio 配置)与 **SIDE B:Kimi Notion 架构2.0 的 full MCP shim 方案**(CC subagents 作 agent container + `.claude/agents/<name>.md` Claude Agent SDK filesystem form + everything-as-MCP-tool 含 agent ↔ agent 协调 + 共享 project-level knowledge graph)在 **7 个维度**(协议 / dispatch / callback / state / 多 agent / 实现成本 / 稳定性)上逐维对照,证明 T6 在每个维度都更好地服务 Phase 44 锁定的 7 个决策。

**根论据 anchor(Phase 44 §2):**

- **决策 1(Phase 44 §2.1):** T6 协议层 = Hermes MCP server(扩展现有 `mcp_serve.py` FastMCP)+ tmux dispatch(复用 coding-agent skill v7.0 ship)+ CC native MCP client(stdio 已 ✓ Connected)。**根本需求:** Hermes 与 CC 之间需要稳定、低故障面、可演进的通信通道。本 doc 对照的 SIDE A 即此决策。
- **决策 5(Phase 44 §2.5):** α agent form = YAML + persona + tools + refs + memory_scope + lineage,物理位置 `~/.hermes/agents/{name}.agent.yaml`。**根本含义:** agents 是 Hermes-side 持久实体,不是 CC subagent,也不是 SKILL 模板。本 doc §3.2 dispatch + §3.4 state + §5 subagent rejection 论证此决策。
- **决策 6(Phase 44 §2.6):** per-agent scoped memory + curator 驱动跨项目自进化。**根本含义:** 每个 agent 拥有自己的 memory namespace(mem0 backend per-agent filter via `_scoped_agent_id`),memory record 有 `scope` / `confidence` / `evidence_chain` 字段。本 doc §3.4 state + §3.7 稳定性 论证此决策。
- **决策 7(Phase 44 §2.7):** 分层 CC 角色:Hermes 控结构(turn_order / max_rounds / early_stop_rule / state schema),CC 控内容(question framing / opinion synthesis / conflict detection)。**根本含义:** 单层全控(CC 全控或 Hermes 全控)都会失衡。本 doc §3.2 dispatch + §3.3 callback 论证此决策。

(决策 2/3/4 在对应 §3.N 中引用 —— §3.2 dispatch 引用决策 2 B3a Python runner、§3.3 callback + §3.5 多 agent 引用决策 3 D2 storyboard-first-class、§3.6 实现成本 引用决策 4 G2 通用编排框架。)

**SIDE A 与 SIDE B 显式枚举:**

| 维度 | SIDE A:T6(v10.0 锁定,Phase 44 决策 1) | SIDE B:Kimi 全 MCP shim(本 doc 显式否决) |
|------|-----------------------------------------|---------------------------------------------|
| Agent 实体物理位置 | `~/.hermes/agents/{name}.agent.yaml`(Hermes-side 持久) | `.claude/agents/<name>.md`(CC-side filesystem,30 天 transcript 自动清理) |
| Agent identity schema | Phase 45 18-field schema(name / persona / persona_sha256 / tools / memory_scope / lineage / fitness_score / evolution_log / round_table_eligible / agent_card / ...) | Claude Agent SDK `AgentDefinition` Python dataclass(description / prompt / tools / model / memory / mcpServers / maxTurns / background / effort —— 9-field subset) |
| MCP server | 扩展现有 `mcp_serve.py` 加 7 STACK-form tools(STACK §3.2) | 把 agent ↔ agent 也塞进 MCP,7+ MCP tools(`create_agent` / `assign_task` / `view_tasks` / `update_task_status` / `ask_project_rag` / `send_agent_message` / `broadcast_message` per Agent-MCP §7.2) |
| Transport | stdio(STACK §4.1,零网络面) | MCP(overloaded —— 同时承载 agent ↔ tool AND agent ↔ agent) |
| Dispatch 模型 | Hermes Python runtime 是 agent container;tmux dispatch 仅用于 long-running CC sessions | CC 是 agent container;main CC agent 调 `Agent` tool 派生 subagent,subagent 返回 final message |
| Multi-agent 模式 | Round table with turn_order + memory conflict arbitration(Phase 46) | Subagent 不互发言(FEATURES §4.2 row 3 verbatim:「不是 round table(无多 subagent 互发言)」) |
| Memory 模型 | Per-agent scoped mem0 backend(namespace + scope + confidence + evidence_chain,Phase 45 memory-record-schema) | `memory: 'user' \| 'project' \| 'local'`(source-scoped 非 namespace-scoped per FEATURES §4.3 fact 2)+ 共享 project-level knowledge graph(Agent-MCP §7.2) |
| 长期持久化 | agent YAML 持久 + mem0 backend memory record 持久(无 cleanup)+ curator 写 `evolution_log` 持久 | Subagent transcripts 30 天自动清理(FEATURES §4.3 fact 3) |
| CC 角色 | 场地 + 协调员 + 结构化助手(决策 7 — Hermes 控结构) | 容器 + 执行器(`.claude/agents/*.md` 是 CC 内部状态) |

**本 doc 对照的是架构选型,不是 Notion 续聊的对话节奏 —— 那是 Kai 与 Kimi 的协作行为,与本对比正交。** Kai 在 Notion 与 Kimi 续聊 v10.0 设计时如何 framed、如何 sync,与本 doc 的 7-dimension 对照是不同维度的事 —— 本 doc 不对协作节奏做评判,只对 Kimi 提出的「架构2.0 = full MCP shim + CC Teammates」做架构选型对照。

### §1.2 — Scope rules:本对比只对照架构选型,不对照具体实现 patch

**本 doc 范围内(架构选型维度):**

- 7 个维度(协议 / dispatch / callback / state / 多 agent / 实现成本 / 稳定性)的 T6 pros/cons + Kimi pros/cons + 选型论据引用 Phase 44 决策号
- Microsoft 三层协议(SC#4)validation:T6 与业界共识对齐,Kimi 违反
- Subagent 形态(SC#3)rejection 论据:FEATURES §11 B4.1 + §4.3 三个 fact + Phase 46 §2/§3 cross-ref
- Kimi-side borrowable(SC#5)evaluation:7-row 借鉴条件表
- Phase 44 决策 1-7 cross-validation audit(§7)

**本 doc 范围外(留给下游 docs):**

- (a) **具体实现 patch**(15-expert transform rules / retained-phases allowlist / `mcp_serve.py` 实际 patch LOC)→ 留给 `04-MIGRATION-PATH.md`
- (b) **跨 repo 同步策略**(3-location 同步 + Option B vs 物理分区切换条件)→ 留给 `06-CROSS-REPO-IMPACT.md`
- (c) **PoC 验收条件**(fitness battery / latency SLO / bias canary / schema migration dry-run)→ 留给 `05-POC-PLAN.md`
- (d) **MCP tool 实际 Pydantic schema** → 留给 STACK §3.2 + Phase 46 §5(本 doc CITE ONLY)
- (e) **Phase 44 决策推导链** → Phase 44 §2.1-§2.7(本 doc CITE ONLY,do NOT re-derive)
- (f) **Phase 45 schema 字段定义** → Phase 45 schema YAML + §2/§3 narrative(本 doc CITE ONLY)
- (g) **Phase 46 protocol lifecycle / conflict 仲裁规则** → Phase 46 §2/§3(本 doc CITE ONLY)

**Citation 纪律:** 本 doc 引用 Phase 44 决策 1-7、Phase 45 schema 字段、Phase 46 protocol 不变量采用 **CITE-ONLY 策略** —— 引用时标注「Cite 决策 N」或「Cite Phase 45 field X」或「Cite Phase 46 §Y」,不重定义类型 / enum / 语义。若读者需要看权威定义,跳到对应 Phase 44/45/46 文件。这是 cross-doc 一致性的根本保证 —— Phase 51 VALIDATE lint script 会跨 doc 检查字段名一致,本 doc 不引入定义 drift。

### §1.3 — SC 映射表(本 doc 章节 → ROADMAP SC#1-5)

ROADMAP §Phase 47 列出 5 条 success criteria,每条都映射到本 doc 的具体章节,验证脚本可通过 §1.3 表交叉核对:

| SC# | SC 描述(摘自 ROADMAP §Phase 47) | 本 doc 解决章节 | 验证脚本(grep anchor) |
|---|---|---|---|
| SC#1 | File `03-COMPARISON-VS-KIMI-MCP-SHIM.md` exists | (本文件本身) | `test -f` + `wc -l` ≥ 1400 |
| SC#2 | 7-dimension contrast table(协议 / dispatch / callback / state / 多 agent / 实现成本 / 稳定性)完整,每维度 T6 vs Kimi pros/cons + 选型论据引用 Phase 44 决策 | §1.6(TL;DR table)+ §3.1-§3.7(prose expansion) | grep "协议" + "dispatch" + "callback" + "state" + "多 agent" + "实现成本" + "稳定性" + "选型论据" + "决策 [1-7]" |
| SC#3 | Subagent form rejection 完整,引用 FEATURES §11 B4.1 + Claude Agent SDK default context-isolation unsuitable for round table panelist + cross-ref Phase 46 protocol serial constraint + memory conflict arbitration | §1.5.2(前置声明)+ §5(SC#3 deep-dive,7 子节) | grep "B4.1" + "context-isolated" + "panelist" + "Phase 46 §2" + "Phase 46 §3" |
| SC#4 | Microsoft three-layer protocol validation 引用 FEATURES §7.4 B7.1 verbatim,证明 v10.0 T6 与业界共识一致 | §1.5.1(前置声明)+ §4(SC#4 deep-dive,5 子节) | grep "B7.1" + "Platform-native" + "MCP for tool" + "A2A for cross" + "FEATURES §7.4" |
| SC#5 | Kimi-side borrowable parts 显式列出 + 借鉴条件 + 喂给哪个下游 doc | §6(SC#5 evaluation,6 子节) | grep "B8.1" + "B4.2" + "B4.3" + "B7.3" + "borrowable" + "借鉴条件" |

每条 SC 都有可机器验证的 anchor string —— Phase 51 VALIDATE lint script 直接 grep 这些字符串即可验证。

### §1.4 — Roadmap 放置:本 doc 是 05-POC-PLAN 的 defense brief + 06-CROSS-REPO-IMPACT 的 sibling 横切

本 doc 在 v10.0 设计文档依赖图中的位置:

```
00-FIRST-PRINCIPLES.md ─┬─> 01-AGENT-REGISTRY-SCHEMA.md ──> 02-ROUND-TABLE-PROTOCOL.md ──> 04-MIGRATION-PATH.md ──> 05-POC-PLAN.md
                        │       (Phase 45, LOCKED)              (Phase 46, LOCKED)
                        │
                        ├─> 03-COMPARISON-VS-KIMI-MCP-SHIM.md (本 doc, Phase 47, parallel)
                        │       ↓ defense brief
                        │   05-POC-PLAN.md
                        │
                        └─> 06-CROSS-REPO-IMPACT.md (Phase 48, parallel)
```

**本 doc 是 05-POC-PLAN.md 的 "defense brief"** —— 当 v11.0 PoC 实施者问「为什么 T6 不 full MCP shim?」「为什么 Hermes-side YAML agent 不 CC subagent?」「为什么 round table 强制 serial?」时,本 doc 提供 section-and-line-precise 答案。05-POC-PLAN.md 引用本 doc §3 dimension table + §5 subagent rejection + §6.1 borrowable table,不需重新推导 Phase 44 决策。

**06-CROSS-REPO-IMPACT.md 是 sibling 横切**(3-location 同步策略),不消费本 doc 的对照细节,但可以引用 §4.5 A2A 扩展位声明 + §5.7 user memory Kai 否决 subagent 形态(在跨 repo 同步时不要把 `.claude/agents/` 列入同步项)。

**51 VALIDATE lint cross-check:** Phase 51 milestone audit 的 lint script 会 cross-check 本 doc 的 7 决策引用号一致 —— 决策 1-7 必须在 §3 + §7 中各被引用至少一次,与 Phase 44 §2.1-§2.7 锁定的决策号完全一致。若 lint 发现引用号 drift(如本 doc 写「决策 8」),触发 ADVISORY 提醒。

**Phase 44 决策 1-7 LOCKED,Phase 45 schemas LOCKED,Phase 46 protocol LOCKED —— 本 doc 只对照,不重新推导。** 这是横向验证 vs 纵向推导的清晰分层 —— 本 doc 是 horizontal validation,Phase 44 是 vertical derivation。

### §1.5 — 3 Load-bearing citations 前置声明

本 doc 的全部论证依赖 3 个 load-bearing citations,本节前置声明,§4-§6 给完整 deep-dive。这 3 条 citations 是本 doc 的论据骨架,任何章节的 claim 都可 trace 回这 3 条的某一条 + Phase 44 决策号。

#### §1.5.1 — Microsoft 三层协议(SC#4 citation)

**Citation verbatim from FEATURES §7.4 B7.1(source: Microsoft multi-agent-patterns 官方指引):**

> - **Platform-native orchestration** for internal flows(平台原生,最低成本)
> - **MCP** for tool and data access(MCP 做 agent ↔ tool)
> - **A2A** for cross-platform agent-to-agent messaging(A2A 做 agent ↔ agent,跨厂商)

**Mapping(v10.0 T6 → Microsoft 三层):**

| Microsoft layer | v10.0 T6 instantiation | Phase 44 决策 |
|-----------------|------------------------|---------------|
| Platform-native(internal flows) | Hermes Python runtime —— agent registry YAML loader, dispatcher, curator, mem0 backend | 决策 5(agent 是 Hermes-side entity)+ 决策 6(curator-driven)+ 决策 7(Hermes 控结构) |
| MCP(tool access) | Hermes MCP server extends `mcp_serve.py` with 7 STACK-form tools | 决策 1(T6 协议)+ 决策 7(Hermes 暴露结构 via schema) |
| A2A(cross-platform) | **Deferred** —— v10.0 single-vendor internal,不需要 A2A;v12+ 跨厂商协作时 A2A 是正确协议 | 决策 1(T6 排除 A2A for v10.0) |

T6 与 Microsoft 三层完全对齐。§4 给完整 mapping + Kimi violation analysis + 业界共识论证(B7.1 + B2.2 + B7.4 三条 borrowable points 一致结论)。

#### §1.5.2 — Subagent form rejection(SC#3 citation)

**Citation verbatim from FEATURES §11 anti-feature row 1:**

> 业界模式:**Subagent 作为 agent 容器**
> 出处:Claude Agent SDK `.claude/agents/*.md`
> v10.0 拒绝理由:subagent context-isolated,memory 弱,30 天清理
> v10.0 替代:Hermes-side YAML agent(`~/.hermes/agents/`)

**Citation verbatim from FEATURES §4.3(三个 fact):**

> 1. **Subagent 默认 context-isolated**:"The only channel from parent to subagent is the Agent tool's prompt string"。这意味着 **subagent 不天然适合做 round table panelist**(panelist 需要看完整历史)。
> 2. **`memory` 字段限定 source**:`'user'` / `'project'` / `'local'`,**不是 namespace scoped memory**(对比 LangGraph Store 的 namespace 元组,这弱很多)。
> 3. **Subagent transcripts 持久化在独立文件**,main conversation compaction 不影响 subagent;30 天后自动清理。

Subagent 形态是 Kimi 方案的 agent 容器(`.claude/agents/<name>.md`),v10.0 决策 5(α form:Hermes-side YAML agent)显式否决。§5 给完整 7-子节论证(B4.1 verbatim + §4.3 三个 fact 逐条展开 + 为什么 context-isolated subagent 不适合做 round table panelist 的 4 个原因 + 与 Phase 46 §2/§3 + 决策 6/7 矛盾分析 + Phase 45 18-field schema 对照优势 + user memory Kai 显式否决引用)。

#### §1.5.3 — Anti-patterns from ARCHITECTURE §8(Kimi-side subset)

**Citation from ARCHITECTURE §8 anti-patterns(Kimi 方案违反的子集):**

- **§8.1 Anti-Pattern: Agent YAML as Prompt Dump** —— Copying the SKILL.md body verbatim into `persona`。Kimi 方案 `.claude/agents/<name>.md` filesystem form 容易把 SKILL body 直接 dump 进 `prompt` 字段,混淆 user-message 与 system-prompt fragment 寄存器。
- **§8.3 Anti-Pattern: Round Table as Pipeline Step** —— Treating `round_table_open` as a synchronous pipeline step that blocks until `closed`。Kimi 方案的 full MCP shim dispatch 诱惑把 agent ↔ agent 协调做成同步阻塞 —— main agent 调 `create_agent` MCP tool 等待 subagent 完成,违反 Phase 46 §1.5.3 atomic lifecycle 约束。
- **§8.4 Anti-Pattern: Per-Agent mem0 Backend Instance** —— Spinning up a separate mem0 client per agent。Kimi 方案的共享 knowledge graph 是另一极端(project-level 单 graph,而非 per-agent),违反决策 6 per-agent scoped memory。

§6 给 Kimi-side borrowable evaluation 时,这三条 anti-patterns 是拒绝清单的论据来源。

### §1.6 — TL;DR:7-row quick-glance table(§3 的 elevator-pitch 版)

下表是 7-dimension contrast 的 TL;DR —— 每维度 1 行,T6 vs Kimi 各 1 句话,选型论据引用 Phase 44 决策号。§3.1-§3.7 把每行展开为 4 段结构(T6 描述 / Kimi 描述 / T6 pros+cons / Kimi pros+cons)+ 收尾选型论据。

| # | 维度 | T6(v10.0 锁定) | Kimi 全 MCP shim(本 doc 否决) | 一句话结论(选型论据) |
|---|------|------------------|--------------------------------|------------------------|
| 1 | **协议**(§3.1) | 单 server stdio MCP(extends `mcp_serve.py`)+ 7 STACK-form tools(决策 1) | Full MCP shim —— 把 agent ↔ agent 也塞进 MCP(`create_agent` / `send_agent_message` etc.) | MCP 单一承担 tool-access layer,与 Microsoft §7.4 B7.1 三层分层一致(决策 1) |
| 2 | **dispatch**(§3.2) | Hermes Python runtime 是 agent container;tmux dispatch 仅 long-running CC sessions | CC 是 agent container;main agent 调 `Agent` tool 派生 subagent → returns final message | Agent 拥有权在 Hermes(决策 5 + 7),跨 CC session 持久;Kimi 绑 CC session 违反决策 6 |
| 3 | **callback**(§3.3) | Round table 原子 lifecycle:`round_table_open` → turn N → `submit_round_table_result`(Phase 46 §2) | Subagent 完成-即返回-final-message;无 round table 概念 | T6 显式 callback 支持决策 7(Hermes 控结构)+ 决策 3(D2 round-based parallel);Kimi 无法表达 round table |
| 4 | **state**(§3.4) | 三层:agent YAML 持久 + per-agent mem0 backend(Phase 45)+ round_tables/{id}.json(Phase 46) | Subagent transcripts 30 天清理 + 共享 project-level knowledge graph | T6 per-agent scoped memory 是决策 6 物理载体;Kimi 30 天 cleanup + 共享 graph 违反决策 6 |
| 5 | **多 agent**(§3.5) | Round table with 5-strategy `turn_order` + memory conflict arbitration(Phase 46 §3)+ 强制 serial | Subagent 不互发言(FEATURES §4.2 row 3);main agent 可 fan-out background subagent | T6 round table 是决策 3(D2)物理载体;Kimi 无法表达协商 |
| 6 | **实现成本**(§3.6) | Extend `mcp_serve.py`(~500-800 LOC)+ Hermes agent registry + mem0 filter + curator `_memory_evolution_phase` 复用 v6.0/v7.0 | 写 `.claude/agents/*.md`(15 files × 50 lines markdown)+ 共享 knowledge graph server + 7+ MCP tools | T6 复用现有设施,与决策 4(G2 通用编排)工程量摊薄一致;Kimi 共享 graph 是新基础设施 |
| 7 | **稳定性**(§3.7) | Per-agent memory + curator self-evolution + dry-run-first + bias canary + 14 PITFALL 字段级 mitigation | 30-day cleanup + shared graph single-point-of-failure + cross-agent contamination(P12)+ 无 curator | T6 per-agent memory + curator 是决策 6 物理载体,P1/P2/P5/P12 字段级 mitigation;Kimi 直接违反决策 6 |

**TL;DR 1-段总结:** T6 在 7 个维度都更好地服务 Phase 44 决策 1-7 —— 协议层单一职责(决策 1)、agent 拥有权在 Hermes(决策 5+7)、显式 callback 支持 round table(决策 3+7)、三层 state 持久化(决策 5+6)、真正 round table 协议(决策 3)、复用现有设施(决策 4)、字段级稳定性 mitigation(决策 6)。Kimi 方案在 7 个维度都至少违反一条决策 —— 不是因为 Kimi 方案「不好」,而是因为 v10.0 paradigm shift(Kai user memory hermes-native-expert-agents.md verbatim:「要 Hermes-side persistent agents + per-agent memory 自进化 + CC 仅做场地」)与 Kimi 方案的「CC 是 agent 容器」范式根本不同。本 doc 不是说 Kimi 方案是错的,而是说 Kimi 方案服务的是不同 paradigm(minimize engineering effort),v10.0 服务的是「agent 随项目越多越有经验」paradigm(决策 6)—— §2 steelman + §3 dimension-by-dimension 对照把这个论证做实。

### §1.7 — Phase 44 决策 1-7 显式 enumeration + 本 doc 引用索引

下表把 Phase 44 `00-FIRST-PRINCIPLES.md` §2.1-§2.7 锁定的 7 决策显式 enumerate,每条标注「本 doc 引用章节」+ 「Kimi 方案是否违反」 —— 这是 §3-§7 引用决策号的索引表,本 doc 任何章节引用「决策 N」都可回查这张表的语义。

| 决策 # | 决策(verbatim from Phase 44 §1.2 锁定选型列) | 本 doc 引用章节 | Kimi 方案是否违反? | 违反的具体方式 |
|---|---|---|---|---|
| **决策 1** | T6 协议:Hermes MCP server(扩展现有 `mcp_serve.py`)+ tmux dispatch(复用 coding-agent)+ CC native MCP client for callbacks | §3.1(协议)+ §4(Microsoft 三层 validation) | **是** | Kimi 全 MCP shim 违反 Microsoft §7.4 B7.1 三层分层(§4.3 violation 1)—— MCP 不该承载 agent ↔ agent |
| **决策 2** | B3a Python runner:delegate-only phase(9 个创意 step)迁 CC;ComfyUI-calling phase(4 个生成 step)+ Step 0/6.5/15 保留 Python runner | §3.2(dispatch,引用 STACK §3.2 Tool 7 `run_python_phase` boundary tool) | **是** | Kimi 无 boundary tool 概念,subagent 接管所有 phase —— 违反 ComfyUI 集成保留(FOUND-08) |
| **决策 3** | D2 storyboard-first-class:V8.6 编号保留,orchestrator 层做 round-based parallel(跨场景,不跨 step) | §3.3(callback)+ §3.5(多 agent) | **是** | Kimi 不支持 round table(FEATURES §4.2 row 3 verbatim:「不是 round table」)+ subagent 不互发言 |
| **决策 4** | G2 通用编排框架:抽象 pipeline orchestration pattern,kais-movie-pipeline 作为首个 sample | §3.6(实现成本) | **是** | Kimi shared graph 是 project-scoped,跨 project 编排需要额外机制 —— 与 G2 「v12+ 扩展 music video / long-form 时不需要重写编排器」目标矛盾 |
| **决策 5** | α agent form:YAML + persona + tools + refs + memory_scope + lineage,物理位置 `~/.hermes/agents/{name}.agent.yaml` | §3.2(dispatch)+ §3.4(state)+ §5(整个 SC#3 rejection) | **是** | Kimi 用 Claude Agent SDK `AgentDefinition`(9-field subset,缺 memory_scope / persona_sha256 / evolution_log / fitness_score / lineage),物理位置 `.claude/agents/`(CC-side)—— 违反「Hermes-side 持久实体」根本含义 |
| **决策 6** | per-agent memory + curator-driven 自进化 | §3.4(state)+ §3.7(稳定性)+ §5.4(source-scoped 不能自进化)+ §5.5(30-day cleanup 违反长生命周期) | **是** | Kimi memory 是 source-scoped(`'user' / 'project' / 'local'`)非 namespace-scoped + 共享 knowledge graph + subagent transcripts 30 天清理 + 无 curator —— 4 条都违反决策 6 根本含义 |
| **决策 7** | 分层 CC 角色:Hermes 控 turn_order / max_rounds / schema / early_stop_rule;CC 控 question framing + synthesis | §3.2(dispatch)+ §3.3(callback)+ §5.3(context-isolated subagent 违反分层) | **是** | Kimi CC main agent 控 turn_order(subagent fan-out 由 CC 决定)—— 违反 Hermes 控结构;CC 既要控结构又要控内容,违反分层 |

**7/7 决策都被 Kimi 方案至少一条方式违反** —— 这就是为什么本 doc 显式否决 Kimi 全 MCP shim 方案,不是「Kimi 方案有缺陷」,而是「Kimi 方案服务的 paradigm 与 v10.0 paradigm shift 完全不同」。§7 cross-validation audit 会再次 audit 这张表,确认 7/7 ✅ 一致(本 doc 对照与 Phase 44 决策推导一致)。

**本 doc 引用 Phase 44 决策的纪律:**

- 引用时永远写「决策 N」(中文)或「Decision N」(英文,仅在英文架构 term 上下文) —— 不用「§2.N 的决策」「那个关于 X 的决策」等模糊表达
- 决策 N 的权威定义在 Phase 44 §2.N —— 本 doc 引用时不重述推导链,只引用结论
- 若读者需要看推导,跳到 `00-FIRST-PRINCIPLES.md` §2.N(本 doc 在 §1.7 表的「决策」列给出 verbatim 一句话 summary,够 anchor 用)
- §7 audit 时会用这张表 cross-check 每个决策是否在本 doc 中至少被引用一次 —— 这是 SC#2 的「7-dimension contrast table 引用决策号」自动化验证

---
