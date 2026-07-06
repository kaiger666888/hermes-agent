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

## §2 — Kimi 方案 Reconstruction(Steelman Before Rebuttal)

### §2.0 — 本节是 Kimi 方案的 steelman

本节把 **Kimi Notion 架构2.0 的「full MCP shim」方案以最强形态陈述**,不预设评判。评判在 §3-§6 dimension-by-dimension 对照。**Kai 与 Kimi 的 Notion 续聊是协作行为,与本节架构 reconstruction 正交** —— 本节不评判续聊节奏,只 reconstruction Kimi 提出的架构选型的「最强 version」。

**Steelman-the-Elimination 纪律(Phase 44 §1.1 引用 v2.0 PRFP §1.5):** 排除论证必须给**实质的钢人反驳**,不是 strawman。本节先把对方立场最强形态摆出来 —— Kimi 方案在哪些维度有吸引力、为什么 Anthropic 官方 SDK 推这种形态、工程量上有什么优势 —— 然后在 §3-§6 中以 Phase 44 决策为 anchor 逐维对照。若本节 steelman 过强(甚至看起来要 overturn 决策),§7 cross-validation audit 会 surface 偏差;预期 7/7 一致(本 doc 是 horizontal validation,不是 re-derivation)。

### §2.1 — Kimi 方案的 SDK origin:Claude Agent SDK filesystem-based subagent

**Form(verbatim from FEATURES §4.2 row 1 + §4.4 B4.1):** Kimi 方案的 agent 实体采用 Claude Agent SDK 的 **filesystem-based subagent** 形态,物理位置 `.claude/agents/<name>.md`(Markdown 文件 + YAML frontmatter)。Anthropic 官方 SDK 提供 `AgentDefinition` Python dataclass(也支持 TypeScript 等价物),核心字段:

| `AgentDefinition` 字段 | Type | 用途 |
|------------------------|------|------|
| `description` | string | 给 main agent 看的「这个 subagent 能做什么」描述 |
| `prompt` | string | subagent 的 system prompt —— 整个 persona + 工作流指令 |
| `tools` | list of string | subagent 可用的工具白名单 |
| `model` | string | subagent 使用的 model alias |
| `memory` | `'user' \| 'project' \| 'local'` | 决定 subagent 从哪个 CLAUDE.md / 设置源加载 memory(source-scoped) |
| `mcpServers` | list | subagent 可用的 MCP server 配置 |
| `maxTurns` | int | subagent 单次 invocation 的最大 turn 数 |
| `background` | bool | v2.1.198+ 是否后台运行(可并发) |
| `effort` | `'low' \| 'medium' \| 'high' \| 'xhigh' \| 'max'` | reasoning effort 等级 |

**为什么这个形态有吸引力:**

1. **Anthropic 官方 SDK** —— 不是社区项目,是 Anthropic 自己推出的官方 subagent 形态,长期维护有保障
2. **官方推的 filesystem 形态** —— `.claude/agents/<name>.md` 是 Anthropic 文档明确推荐的 agent 定义方式([code.claude.com/docs/en/agent-sdk/subagents](https://code.claude.com/docs/en/agent-sdk/subagents))
3. **CC 原生支持** —— Claude Code CLI 直接识别 `.claude/agents/` 目录,无需额外 runtime
4. **零额外 runtime** —— 不需要 Hermes-side agent registry / dispatcher / mem0 filter,agent 就是 markdown 文件
5. **工程量极小** —— 写一个 agent 就是写一个 markdown 文件,~30-50 行 frontmatter + prompt

**Citation:** FEATURES §4.2(7-axis 表)+ §4.3(三个关键 fact)+ §4.4 B4.1(Kimi 方案用的形态)。本 doc §5 给完整 subagent rejection 论证;§2 范围内只 reconstruction SDK origin。

### §2.2 — Kimi 方案的 dispatch 模型:CC main agent 调 Agent tool 派生 subagent

**Pattern(verbatim from FEATURES §4.2 row 4 + §4.2 row 3):**

- **调度粒度(row 4):** Tool-call dispatch —— main agent(CC)通过 `Agent` tool 显式调用 subagent。v2.1.198+ subagent 默认 background,可并发。
- **Multi-agent 协作模式(row 3,verbatim):** 「**不原生支持 multi-agent**。Claude 自己作为 main agent,可调 `Agent` tool 派生 subagent 做子任务,subagent 返回 final message;**不是 round table**(无多 subagent 互发言)」。

**Dispatch 流程:**

```
1. CC main agent 接到任务,决定需要某个 expert
2. CC 调 Agent tool: Agent(name="screenplay", prompt="<task description + context>")
3. subagent "screenplay" 在自己的 CC session 跑(effort high / maxTurns 10 / tools [..])
4. subagent 完成 → returns final message(string)给 main agent
5. main agent 读 final message,决定下一步
```

**Subagent context isolation(FEATURES §4.3 fact 1 verbatim):** 「**Subagent 默认 context-isolated**:'The only channel from parent to subagent is the Agent tool's prompt string'」 —— subagent 看不到 main agent 的对话历史,只能看到 `Agent` tool 调用时传入的 prompt 字符串。main agent 必须把所有需要的 context(task description + prior discussion + project context)序列化进 prompt string。

**Multi-agent 不支持但 fan-out 支持:** CC main agent 可以同时调用多个 `Agent` tool(v2.1.198+ background),让多个 subagent 并发跑 —— 这是「fan-out」,不是「round table」。subagent 之间不通讯,main agent 收集所有 final messages 后做 synthesis。

**Citation:** FEATURES §4.2 row 3 + row 4 + §4.3 fact 1。本 doc §3.2 dispatch 维度对照 T6 与 Kimi 的 dispatch 模型;§5.3 论证为什么 context-isolated subagent 不适合做 round table panelist。

### §2.3 — Kimi 方案的 memory 模型:source-scoped + 30-day cleanup

**Scope(verbatim from FEATURES §4.2 row 2 + §4.3 fact 2):**

- **`memory` 字段(§4.2 row 2):** `'user' | 'project' | 'local'` 三选一 —— 决定 subagent 从哪个 CLAUDE.md / 设置源加载 memory。这是 **source-scoped**(哪个 markdown 文件作 memory 源),不是 **namespace-scoped**(哪个 agent 的经验积累)。
- **§4.3 fact 2 verbatim:** 「`memory` 字段限定 source:`'user'` / `'project'` / `'local'`,**不是 namespace scoped memory**(对比 LangGraph Store 的 namespace 元组,这弱很多)」。

**Persistence(§4.3 fact 3 verbatim):**

- 「**Subagent transcripts 持久化在独立文件**,main conversation compaction 不影响 subagent;**30 天后自动清理**」。

**对比 v10.0 决策 6 的根本差异:**

| 维度 | Kimi `memory: source-scoped` | v10.0 Phase 45 memory-record-schema |
|------|------------------------------|-------------------------------------|
| Scoping 维度 | source file(`.claude/CLAUDE.md` etc.) | `agent_id` + `scope: global\|project\|session`(namespace 元组) |
| Memory record schema | N/A(就是读 CLAUDE.md 内容) | `record_id` / `agent_id` / `scope` / `confidence` / `evidence_chain` / `evidence_operator_ids` / `status` / `confidentiality` / `expires_at` / `verified_at` |
| 写入路径 | operator 手改 CLAUDE.md | curator `_memory_evolution_phase` 自动 aggregate feedback 写 record |
| 持久性 | CLAUDE.md 文件持久;subagent transcripts 30 天清理 | agent YAML 持久 + mem0 backend memory record 持久(无 cleanup)+ curator `evolution_log` 持久 |
| Cross-project | N/A(`memory: 'project'` 是当前 project 的 CLAUDE.md) | `scope: global` records 跨 project 共享 + `scope: project` 隔离 |

**Citation:** FEATURES §4.2 row 2 + §4.3 fact 2 + fact 3。本 doc §3.4 state 维度 + §5.4(source-scoped 不能自进化)+ §5.5(30-day cleanup 违反决策 6 长生命周期)给完整对照论证。

### §2.4 — Kimi 方案的「全 MCP shim」含义:everything-as-MCP-tool

**Pattern(verbatim from FEATURES §7.1 + §7.2):** Kimi 方案的「full MCP shim」借鉴自 Agent-MCP(github.com/rinadelph/Agent-MCP)模式 —— 把 agent ↔ tool 通讯 **AND** agent ↔ agent 通讯 **都塞进 MCP**。

**MCP tool 全集(§7.2 row 7,verbatim):**

```
create_agent / assign_task / view_tasks / update_task_status
ask_project_rag / send_agent_message / broadcast_message
```

**Knowledge graph 模式(§7.2 row 2):**

- **共享 knowledge graph**(RAG-over-MCP)—— 项目级单一 graph,所有 agent 共享
- **Agent 级短暂记忆** —— 60 秒 idle 即杀(短命 agent 模式)
- **长期 memory 集中在项目级 graph** —— 不是 per-agent scoped

**为什么这个模式有吸引力:**

1. **单 protocol 覆盖所有交互** —— 不需要区分 agent ↔ tool 与 agent ↔ agent,都是 MCP call
2. **无需额外 runtime** —— agent 就是 MCP tool 调用结果,不需要 Hermes-side agent entity
3. **共享 knowledge graph 节省基础设施** —— 一个 graph server vs N 个 per-agent mem0 backends
4. **短命 agent 节省 token cost** —— agent 完成-即销毁,不留长期 context

**Citation:** FEATURES §7.1(模式定位)+ §7.2(7-axis 表)。本 doc §3.1 协议维度 + §3.4 state 维度 + §4.3 Microsoft 三层 violation analysis 给完整对照论证。

### §2.5 — Steelman 合理性陈述:为什么 Kimi 方案在「最小工程量」目标下是合理的

**Kimi 方案的总体吸引力(minimize engineering effort 视角):**

- **CC 原生** —— 不需要 Hermes-side runtime 改动,CC 已支持 `.claude/agents/` + `Agent` tool
- **零额外 runtime** —— 不需要 agent registry / dispatcher / mem0 filter extension / curator `_memory_evolution_phase`
- **工程量极小** —— 15 个 expert × 50 行 markdown = 750 行 markdown;对照 T6 的 extend `mcp_serve.py`(~500-800 LOC Python)+ agent registry + curator 扩展,工程量约为 T6 的 1/5
- **`.claude/agents/` 是 Anthropic 官方推的形态** —— 长期维护有保障,不是社区项目
- **共享 knowledge graph 节省基础设施** —— 一个 graph server + RAG 嵌入成本 vs 15 个 per-agent mem0 backends + filter routing + curator
- **短命 agent 节省 token cost** —— agent 完成-即销毁,不留长期 context(memory 不积累,token cost 低)

**Steelman closing(本节不评判,评判留给 §3-§6):**

如果 v10.0 的目标是「**minimize engineering effort while getting multi-agent behavior**」—— 即在最小工程量下获得「看起来像 multi-agent」的能力 —— **Kimi 方案是合理的**。它在 Anthropic 官方 SDK 之上,以最小工程量把 CC 变成 multi-agent 系统:`.claude/agents/*.md` filesystem form + `Agent` tool 派生 + 共享 knowledge graph + 短命 agent。这个组合在「minimize engineering effort」目标下是 well-engineered 的。

**但 v10.0 的目标不是「minimize engineering effort」** —— v10.0 的核心 paradigm shift 是「**agent 随项目越多越有经验**」(Phase 44 §Executive Summary + 决策 6)+ 「**Hermes 控结构 / CC 控内容**」(决策 7)+ 「**agent 是 Hermes-side 持久实体,有身份、有记忆、可自进化**」(决策 5)。这三个目标与 Kimi 方案的「CC 是 agent 容器 + 短命 agent + source-scoped memory + 共享 graph」根本不同 —— 不是 Kimi 方案不好,而是服务的 paradigm 不同。

§3-§6 dimension-by-dimension 对照把这个论证做实:每维度从 Phase 44 决策号推 T6 的选型论据,然后对照 Kimi 方案在该维度的形态,显示 Kimi 方案违反决策的具体方式。§5 给 subagent 形态的完整 rejection 论据;§6 给 Kimi-side borrowable evaluation(承认 Kimi 方案中确实有 4 条可借鉴的设计点 —— Agent Card / hooks / effort / file-level lock)。

---

## §3 — 7-Dimension Contrast(Prose Expansion of §1.6 TL;DR)

### §3.0 — 本节范围

本节展开 §1.6 的 TL;DR table,每维度 4 段结构:**(a) T6 描述** + **(b) Kimi 描述** + **(c) T6 pros+cons** + **(d) Kimi pros+cons**,收尾「**选型论据**」段引用 Phase 44 决策号。维度 1-4 在本 task(协议 / dispatch / callback / state),维度 5-7 在 Task 3(多 agent / 实现成本 / 稳定性)。

**每段描述都引用 STACK / FEATURES / ARCHITECTURE / PITFALLS / Phase 45 / Phase 46 的具体 section** —— 本 doc 不发明任何论据,所有 claim 都 traceable 到 Phase 44 research 或锁定决策。

**Steelman 纪律重申(Phase 44 §1.1 引用 v2.0 PRFP §1.5):** 本节对照 Kimi 方案时严守 steelman 纪律 —— 不写 strawman(如「Kimi 方案不好」「Kimi 方案没经验」),只写 steelman(如「Kimi 方案在 minimize engineering effort 目标下是合理的,但 v10.0 服务的是不同 paradigm,具体违反决策 N 的方式是 X」)。§2 已把 Kimi 方案最强形态摆出,本节是逐维对照论据。

**选型论据引用决策号的纪律:**

- 引用「决策 N」时永远写中文 numeral(决策 1 / 决策 2 / ... / 决策 7),与 Phase 44 §1.2 锁定列表一致
- 不写「决策 8」「决策 0」等不存在的决策号(本 doc §7 audit 会 cross-check)
- 一个维度可能引用多条决策(如 §3.2 dispatch 引用决策 5 + 7)—— 这是预期的,因为 7 决策之间存在依赖关系(Phase 44 §1.2 关键观察:「决策 #5 定义 agent 是什么,决策 #6 定义 agent 如何变好,决策 #7 定义 agent 之间如何协作;决策 #1-#4 是支撑三件套的基础设施」)
- 每条选型论据都给一句话 summary(为什么 T6 更好服务引用的决策),不重述决策推导链(推导在 Phase 44 §2.N)

### §3.1 — 维度 1:协议(Protocol Layer)

#### T6 描述

T6 的协议层是 **Hermes MCP server(单 server,stdio transport)** —— 通过扩展现有 `mcp_serve.py`(FastMCP,907 lines,v7.0 ship)加 **7 个 STACK-form MCP tools**(`get_agent_persona` / `get_agent_opinion` / `get_agent_memory` / `submit_round_table_result` / `submit_artifact` / `query_memory` / `run_python_phase`,STACK §3.2 authoritative Pydantic schema)。CC 通过 `~/.claude.json` 配置 stdio MCP client(已 ✓ Connected per STACK §1 实测),CC 是 MCP client,Hermes 是 MCP server。

**Transport(STACK §4.1):** stdio(单进程,零网络面)—— 不走 HTTP / SSE / WebSocket。这意味着 Hermes MCP server 与 CC 跑在同一 host(localhost),没有跨 host 网络层。

**MCP tool 风格统一(STACK §3.2 + SUMMARY.md CC-1):** 7 个新 tool 与现有 `mcp_serve.py` 9 个 messaging tool(`conversations_list` / `messages_read` / `messages_send` etc.)风格一致 —— 都是「no prefix」命名(STACK 形态胜出,详见 Phase 46 §4.2 reconciliation table)。

#### Kimi 描述

Kimi 方案的协议层是 **full MCP shim** —— 把 agent registry / dispatch / memory / coordination **全部塞进 MCP tool**。Agent-MCP §7.2 模式给出 7+ MCP tools(`create_agent` / `assign_task` / `view_tasks` / `update_task_status` / `ask_project_rag` / `send_agent_message` / `broadcast_message`),覆盖 agent lifecycle + agent ↔ agent 协调。

**Protocol = MCP,但 overloaded:** MCP 在 Kimi 方案中同时承担 (a) agent ↔ tool 通讯(MCP 设计原意)+ (b) agent ↔ agent 协调(create_agent / send_agent_message 等)+ (c) 项目级 RAG(`ask_project_rag`)。MCP 协议层被赋予 3 种语义负载。

**Transport:** MCP(具体 transport 未限定 —— stdio 或 HTTP/SSE 都可,但 Kimi 方案隐含 stdio for CC compatibility)。

#### T6 pros

(a) **MCP 单一承担 tool-access layer(Microsoft §7.4 B7.1 三层分层一致)** —— MCP 只做 agent ↔ tool,不做 agent ↔ agent。Platform-native(Hermes Python runtime)承担 internal orchestration,A2A 留给未来 cross-platform 协作(本 doc §4 deep-dive)。
(b) **stdio transport 零网络面(PITFALLS §P10 privacy 正面)** —— 单进程 stdio 不暴露网络端口,attack surface 最小。MCP server 与 CC 同 host,无 MITM / replay 风险。
(c) **与现有 9 个 messaging tool 风格一致(Phase 46 §4.2 STACK form)** —— 维护成本低,CC dispatcher 实施者不需要学两套命名风格。
(d) **复用现有 FastMCP 实施路径(STACK §1)** —— `mcp_serve.py` 已用 `mcp.server.fastmcp.FastMCP`,加 7 tool 是 `@mcp.tool()` decorator + Pydantic schema,无新依赖。

#### T6 cons

(a) **tmux dispatch 需要 Hermes-managed subprocess(STACK §1 Infrastructure)** —— long-running CC sessions(`hermes-round-table-{id}` tmux session)是额外 runtime 组件,Hermes 负责启动 / 监控 / gc。
(b) **stdio 不能跨 host** —— 未来 A2A 走 HTTP / 跨 host 协作时,需要换 transport(STACK §4.3 给迁移条件);但这是 v12+ 的事,v10.0/v11.0 单 host 不需要。

#### Kimi pros

(a) **单 protocol 覆盖所有交互** —— 概念模型简单(都是 MCP call),实施者不需区分 protocol 层次。
(b) **无需 tmux 等额外组件** —— 全部走 MCP,无 Hermes-managed subprocess。

#### Kimi cons

(a) **违反 Microsoft §7.4 B7.1 三层分层(§4.3 violation 1)** —— Microsoft 明确「MCP for tool access」单一职责,Kimi 把 agent ↔ agent 塞进 MCP 是 anti-pattern。Microsoft 是业界权威指引(HIGH 置信度 source),违反三层分层意味着 v10.0 与业界共识脱节。
(b) **MCP tool 爆炸** —— `create_agent` / `assign_task` / `send_agent_message` / `broadcast_message` 全是 MCP tool,CC tool registry 膨胀。CC 看到 ~20+ MCP tools(7 messaging + 7+ Kimi agent-coordination + 7 STACK v10.0),decision-tree 复杂度上升。
(c) **Agent ↔ agent 走 MCP 意味着每次都序列化整个 message** —— `send_agent_message(from=A, to=B, content=...)` 每次都序列化 message content 进 MCP request,高 token cost(对比 T6 的 round table state file append-only,turns 共享一个 state file,序列化一次)。
(d) **Kimi 把 agent identity 放在 CC filesystem(`.claude/agents/*.md`),不是 platform-native** —— 违反 Microsoft 三层中的「Platform-native orchestration for internal flows」(§4.3 violation 2)。

#### 选型论据

**决策 1(T6 协议)。** T6 让 MCP 单一承担 tool-access layer,与 Microsoft §7.4 B7.1 三层分层 + Phase 44 决策 1 推导链(Phase 44 §2.1)一致。Kimi 全 MCP shim 违反 Microsoft 三层(MCP 不该承载 agent ↔ agent)+ 违反「Platform-native orchestration」(agent identity 应在 platform runtime,不在 client filesystem)。**T6 在协议维度更好服务决策 1。**

### §3.2 — 维度 2:dispatch

#### T6 描述

T6 的 dispatch 模型是 **Hermes Python runtime 是 agent container** —— agent YAML 实体(`~/.hermes/agents/{name}.agent.yaml` per Phase 45 18-field schema)lives in Hermes process,作为 Hermes-side 持久数据结构。Dispatcher(ARCHITECTURE §4 `agent/agent_registry.py` + `agent/agent_dispatcher.py`)读 agent YAML,应用 `tools` 字段 whitelist(Phase 45 agents-schema §2.5),routes 到 Hermes-side executor。

**tmux dispatch 仅用于 long-running CC sessions** —— round table panelist 需要 sustained context 时,dispatcher 启动 tmux session(`tmux new-session -d -s hermes-round-table-{id} ...` per STACK §1 Infrastructure)并 spawn CC 子进程通过 stdio MCP 与 Hermes 通信。CC 在 tmux 里跑,但是 **CC 不拥有 agent** —— agent identity 在 Hermes YAML。

**Hermes 控 dispatch 结构(决策 7):** Dispatcher 决定 panelist 顺序(`turn_order` per Phase 46 §2.5)、max rounds、early stop rule —— 这些是「structure」,Hermes-side 强制。CC 决定 question framing、opinion synthesis —— 这些是「content」,CC-side 自由。

#### Kimi 描述

Kimi 方案的 dispatch 模型是 **CC 是 agent container** —— subagent lives in CC process as `.claude/agents/<name>.md`。Main CC agent invokes `Agent` tool → 派生 subagent → subagent runs in its own CC session → returns final message。

**No Hermes-side agent entity** —— agent 就是 `.claude/agents/` 目录下的 markdown 文件,Hermes 不知道哪些 agent 存在(除非 Hermes 扫 `.claude/agents/`,但这是 CC 的工作目录,不是 Hermes 的)。

**CC main agent 控 dispatch(违反决策 7):** Main agent 决定何时调用 `Agent` tool、调哪个 subagent、传什么 prompt、是否 background fan-out —— 这些都是 CC-side 控制,Hermes 不参与 dispatch 决策。

#### T6 pros

(a) **Agent 是 Hermes-side persistent entity(决策 5 — α form)** —— agent YAML 跨 CC session 存活,跨 project 存活,跨 CC version 升级存活。重启 CC 不影响 agent identity。
(b) **Hermes 控 tools whitelist / memory_scope / execution_limits(决策 7 — Hermes 控结构)** —— Phase 45 agents-schema 的 `tools` / `memory_scope` / `max_turns` / `timeout_s` 字段是 Hermes-side enforced,CC 不能绕过。
(c) **CC 仅做场地 + 协调员 + 结构化助手(决策 7)** —— CC 不拥有 agent,只是调用 Hermes MCP tool(`get_agent_opinion` etc.)的 client。Hermes 拥有 agent identity + lifecycle。

#### T6 cons

(a) **Hermes 必须 extend `mcp_serve.py` 加 7 tools(STACK §3.2)** —— 工程量比「只写 `.claude/agents/*.md` markdown」大(~500-800 LOC Python vs ~750 行 markdown)。
(b) **tmux session 管理(启动 / 监控 / gc)是 Hermes 责任** —— Hermes 要处理 tmux session 崩溃、孤儿进程、CC restart 后的 state recovery(Phase 46 §2.4 crash recovery rules)。

#### Kimi pros

(a) **零 Hermes-side runtime 改动** —— agent 是 markdown 文件,不需要 extend `mcp_serve.py` / 写 `agent_registry.py` / 写 `agent_dispatcher.py`。
(b) **CC 原生 lifecycle 管理 subagent** —— CC 自己处理 subagent 启动 / 监控 / cleanup,包括 30 天 transcript 自动清理(FEATURES §4.3 fact 3)。

#### Kimi cons

(a) **Agent lifecycle 绑 CC session —— subagent transcripts 30 天清理(FEATURES §4.3 fact 3),违反决策 6 「agent 随项目越多越有经验」** —— operator 投入调 persona / 喂 feedback / 跑 fitness battery 在 30 天后丢失。这是不可接受的(operator 投入的累积经验应跨年持久)。
(b) **Tools whitelist 由 CC Agent tool 控制(`AgentDefinition.tools` 字段),不是 Hermes** —— 违反决策 7「Hermes 控结构」。CC 是 agent container 意味着 tools whitelist 是 CC-side enforced,Hermes 不能 audit / override。
(c) **Memory 字段 `'user'|'project'|'local'` 是 source-scoped 不是 namespace-scoped(FEATURES §4.3 fact 2),违反决策 6 per-agent scoped memory** —— subagent 的 memory 是从哪个 CLAUDE.md 读,不是哪个 agent 的经验积累。决策 6 要求 per-agent namespace(`agent_id` filter in mem0 backend),Kimi 不能表达这个。
(d) **`.claude/agents/` 在 CC 工作目录,不跨 project 同步(除非 symlink,增加运维复杂度)** —— Phase 48 06-CROSS-REPO-IMPACT.md 会处理这个;但 Kimi 方案在跨 project 时是 broken 的默认行为。

#### 选型论据

**决策 5 + 7。** T6 把 agent 拥有权放在 Hermes(YAML 持久 + tools whitelist Hermes-enforced + memory_scope namespace-scoped),与决策 5(α form:agent 是 Hermes-side 持久实体)+ 决策 7(Hermes 控结构)一致。Kimi 方案把 agent 拥有权放在 CC(30 天 cleanup + tools whitelist CC-enforced + memory source-scoped),违反决策 5 + 6 + 7。**T6 在 dispatch 维度更好服务决策 5 + 7。**

### §3.3 — 维度 3:callback

#### T6 描述

T6 的 callback 模型是 **Round table 原子 lifecycle**(Phase 46 §2):三个原子操作 `round_table_open(roundId, panel, question, maxRounds, turnOrderStrategy, earlyStopRule, projectId)` → turn N(`get_agent_opinion(agentId, topic, context, priorDiscussion)` per turnOrder,sequential await)→ `submit_round_table_result(roundId, conclusion, citedMemories, artifacts, conflicts)` 原子提交。

**Callback 是显式 MCP tool 调用,不是隐式 subagent return。** 每个 turn 是一次 `get_agent_opinion` MCP call —— CC 显式调用,Hermes 显式 append 到 state file `turns` 数组。`submit_round_table_result` 是显式 commit point —— flip status=completed,seal conflict log,通知用户 via 现有 `tools.send_message_tool`。

**Hermes 控 turn_order / max_rounds / early_stop_rule(决策 7):** 这些是 state file schema 字段(Phase 46 round-table-state-schema),Hermes-side enforced。CC 控 question framing + opinion synthesis + conflict detection —— 这些是「content」,CC-side 自由。

**Memory conflict arbitration(Phase 46 §3):** 当两个 panelist 的 `citedMemoryIds` 在语义上矛盾(embedding cosine similarity ≥ 0.7),Hermes coordinator 跑 comparator LLM pass + scope precedence(session > project > global)+ confidence-weighted voting + conflict log append。

#### Kimi 描述

Kimi 方案的 callback 模型是 **Subagent 完成-即返回-final-message** —— main agent 调 `Agent` tool,subagent 跑完返回 final message string 给 main agent。

**No round table concept** —— subagent return 是单次 invocation 完成信号,不是 lifecycle step。Main agent 读 final message 后决定下一步(可能再调另一个 subagent,可能结束),但 **没有 turn lifecycle / multi-turn coordination / conflict arbitration** 概念。

**Turn_order 由 main agent(CC)决定** —— main agent 决定何时调用哪个 subagent,顺序由 CC reasoning 决定,违反决策 7「Hermes 控 turn_order」。

#### T6 pros

(a) **显式 round table lifecycle 支持决策 3(D2 — orchestrator 层做 round-based parallel)** —— Phase 46 §2 三原子操作是 D2 storyboard-first-class 的物理载体(决策 3 要求 round-based parallel,跨场景,不跨 step)。
(b) **`submit_round_table_result` 是原子 commit point,支持 Phase 46 §3 memory conflict arbitration** —— turn N 的 `citedMemoryIds` 在 state file 中持久,comparator LLM 可读 + arbitration 可执行。Kimi 的 subagent return 不带 citedMemoryIds。
(c) **CC 控 question framing + synthesis(决策 7),Hermes 控 turn_order / max_rounds / early_stop_rule(决策 7)** —— 两层分层清晰。Hermes 通过 state schema 控制 lifecycle 骨架,CC 通过 prompt engineering 控制 content。

#### T6 cons

(a) **Round table state file(`~/.hermes/agents/.runtime/{slug}/round_tables/{id}.json`)需要 gc pass** —— v11.0 PoC 未定 gc 频率(Phase 46 §2.4 给 crash recovery rules,但 completed round table 的 retention policy 留 v11.1+)。
(b) **7 个 MCP tool 的 contract 学习曲线** —— CC dispatcher 实施者要学 7 个 tool 的 Pydantic schema(Phase 46 §5),Kimi 方案只需学 1 个 `Agent` tool。

#### Kimi pros

(a) **极简 —— 无 lifecycle 概念,main agent 自由组合** —— CC main agent 决定何时调 Agent tool、调几次、传什么 prompt,无 Hermes-side lifecycle 约束。

#### Kimi cons

(a) **无法表达 round table —— FEATURES §4.2 row 3 verbatim:「不是 round table(无多 subagent 互发言)」** —— subagent 不互发言意味着没有协商,只有 fan-out + main agent synthesis。决策 3 D2 storyboard-first-class 要求 round-based parallel,Kimi 不能表达。
(b) **无法做 memory conflict arbitration(Phase 46 §3 的 P7 mitigation 需要 turn N 的 `citedMemoryIds`)** —— Kimi 的 subagent return 是 final message string,不带 citedMemoryIds metadata。comparator LLM 无法提取 / 对比 cited memory。这意味着 Kimi 方案不能 mitigate P7(round-table memory conflict),load-bearing pitfall。
(c) **CC 既要控结构又要控内容,违反决策 7 分层** —— turn_order 由 CC main agent reasoning 决定(structure),question framing 也由 CC 决定(content),两层混在 CC 一边。

#### 选型论据

**决策 7 + 3。** T6 的显式 callback(round table lifecycle 三原子操作)支持决策 7(Hermes 控结构:turn_order / max_rounds / early_stop_rule)+ 决策 3(D2 round-based parallel:跨场景协商)。Kimi 的 subagent-return 模型无法表达 round table(无 turn lifecycle)+ 无法做 memory conflict arbitration(无 citedMemoryIds)+ CC 既要控结构又要控内容(违反决策 7)。**T6 在 callback 维度更好服务决策 3 + 7。**

### §3.4 — 维度 4:state

#### T6 描述

T6 的 state 是 **三层持久化**:

1. **Agent identity = Hermes-side YAML** —— `~/.hermes/agents/*.agent.yaml` per Phase 45 18-field schema。18 字段包括 `name` / `persona` / `persona_sha256` / `tools` / `memory_scope` / `default_invocation` / `fitness_score` / `evolution_log` / `lineage` / `agent_card` / `reasoning_effort` / `execution_limits` / `round_table_eligible` / `skill_fallback` / `skill_sha256` / `created_at` / `last_modified_at` / `schema_version`。Agent identity 跨 CC session 持久,跨 project 持久,跨 CC version 升级持久。

2. **Per-agent memory = mem0 backend with `agent_id` filter** —— Phase 45 memory-record-schema 10 字段(`record_id` / `agent_id` / `content` / `scope: global\|project\|session` / `confidence: 0.0-1.0` / `evidence_chain: list, minItems=3` / `evidence_operator_ids` / `status: active\|archived\|quarantined\|superseded` / `confidentiality: public\|internal\|confidential\|restricted` / `expires_at` / `verified_at` / `supersedes_memory_id` / `half_life_days`)。mem0 backend 实施路径走 Option B(ARCHITECTURE §3.2 + §3.3 additive extension `_scoped_agent_id` via `contextvars` in ThreadPoolExecutor)。

3. **Round table state = `~/.hermes/agents/.runtime/{slug}/round_tables/{id}.json`** —— cite **ARCHITECTURE §5.1 state file layout** + **ARCHITECTURE §5.3 lifecycle sketch**(Phase 44 research 内的 state file 物理路径 + lifecycle 描述,Phase 46 §2.1-§2.3 把它落地为协议契约)。Phase 46 round-table-state-schema(`roundId` / `turnOrder` / `turns[]` / `conflicts[]` / `panelists[]` / `personaSnapshots` / `status: open\|completed\|aborted\|stalled`)。Append-only + crash-recoverable(Phase 46 §2.4 persistence rules;ARCHITECTURE §5.2 cross-project sharing rules)。

#### Kimi 描述

Kimi 方案的 state 是 **两层(transient + project-shared)**:

1. **Agent identity = `.claude/agents/<name>.md` markdown** —— Kimi-side filesystem(Claude Agent SDK `AgentDefinition` 9-field subset)。Identity 绑 CC session —— subagent transcripts 30 天自动清理(FEATURES §4.3 fact 3)。

2. **Memory = subagent transcripts 独立文件 + 共享 project-level knowledge graph** —— subagent transcripts 30 天清理;长期 memory 在 Agent-MCP §7.2 row 2 描述的「共享 knowledge graph」(RAG-over-MCP),项目级单一 graph,所有 agent 共享。

3. **Round table state = N/A(Kimi 无 round table)** —— subagent return 模型,无 lifecycle state file。

#### T6 pros

(a) **Per-agent scoped memory with namespace + scope + confidence + evidence_chain(决策 6 完整 support)** —— Phase 45 memory-record-schema 是决策 6(per-agent memory + curator-driven 自进化)的字段级物理载体。`agent_id` filter 让每个 agent 有自己的 namespace;`scope` 区分 global/project/session;`confidence` + `evidence_chain` + `evidence_operator_ids` 支持 curator self-evolution + bias canary。
(b) **Agent identity 持久(跨 CC session 跨 project)** —— operator 投入(调 persona / 喂 feedback / 跑 fitness battery)在 agent YAML + mem0 backend + `evolution_log` 三层持久,无 30-day cleanup。决策 6 「agent 随项目越多越有经验」是物理可行。
(c) **Round table state append-only + crash-recoverable** —— Phase 46 §2.4 + state schema 的 `status` enum 支持 CC mid-round crash 后的 recovery(`stalled` → resume or abort),无永远 open 的孤儿 state file。
(d) **字段级 mitigation for P1/P2/P5/P7/P8/P10/P12(14 PITFALLS 中 7 个 load-bearing)** —— `persona_sha256` mitigates P1(persona drift);`expires_at` + `verified_at` + `supersedes_memory_id` mitigates P2(stale memory);`evidence_chain` + dry-run-first mitigates P5(curator failure modes);`scope` + `project_id` mitigates P4(cross-project leakage);`scope` precedence + confidence voting mitigates P7(round-table memory conflict);`fitness_score` mitigates P8(no fitness signal);`confidentiality` mitigates P10(privacy);`agent_id` filter + namespace mitigates P12(cross-agent contamination)。

#### T6 cons

(a) **mem0 backend filter behavior 在 18-agent × 100-project 规模下未实测(OQ-12,defer 到 Phase 48 + v11.0 PoC)** —— ARCHITECTURE §3.2 推荐 Option B(filter 路由),PITFALLS §3 mitigation 1 推荐 v12+ 物理分区(每 agent 一个 mem0 workspace)。v11.0 PoC week-1 跑 latency benchmark,若 p95 > 500ms 立即触发物理分区切换(CC-4)。
(b) **三层 state 意味着三个数据源,consistency 需 curator 协调** —— agent YAML(Identity)+ mem0 backend(memory)+ round_tables/{id}.json(lifecycle)三层任何一层 drift 都需要 curator detection + reconciliation。curator `_memory_evolution_phase` 是 load-bearing(Phase 45 §3.4 + Phase 46 §3.5 conflict log review)。

#### Kimi pros

(a) **共享 knowledge graph 节省基础设施(一个 graph server vs N mem0 backends)** —— 项目级单一 graph server + RAG 嵌入,所有 agent 共享。infra 成本低,运维简单。

#### Kimi cons

(a) **Subagent transcripts 30 天清理 → agent 长期经验不稳定,违反决策 6「agent 随项目越多越有经验」** —— operator 投入(persona 调整 / feedback 喂养 / fitness battery)在 30 天后丢失。这是不可接受的 —— 决策 6 是 v10.0 paradigm shift 最核心的载体(Phase 44 §Executive Summary)。
(b) **共享 graph → agent 间 memory bleed-through(PITFALLS §P12 cross-agent contamination)** —— 共享 knowledge graph 意味着 screenplay agent 可能检索到 cinematographer agent 的 memory(如果 RAG filter 不严),违反决策 6 per-agent scope。PITFALLS §P12 的 mitigation 是「per-agent 物理分区」,与 Kimi 的「共享 graph」根本对立。
(c) **`.claude/agents/` 在 CC 工作目录,不跨 project 同步(除非 symlink,增加运维复杂度)** —— v10.0 是 multi-project(每个 project 有自己的 agent subset preferences),Kimi 的 `.claude/agents/` 是 per-CC-working-directory 的,跨 project 同步需要 symlink 或外部 sync 机制(增加运维负担)。Phase 48 06-CROSS-REPO-IMPACT.md 处理这个 —— v10.0 决策 5 把 agent 放在 `~/.hermes/agents/`(Hermes-side,跨 project 自然共享)避免了这个问题。
(d) **无 curator self-evolution(决策 6 unavailable)** —— Kimi 方案没有 curator `_memory_evolution_phase`(因为 memory 是 source-scoped CLAUDE.md + subagent transcripts,不是 per-agent memory records),决策 6 「curator 驱动跨项目自进化」完全 unavailable。

#### 选型论据

**决策 5 + 6。** T6 的三层 state(agent identity YAML 持久 + per-agent mem0 backend namespace-scoped + round_tables/{id}.json append-only)把 agent identity + per-agent memory + round table state 都做成持久层,与决策 5(α form:Hermes-side 持久实体)+ 决策 6(per-agent scoped memory + curator-driven 自进化)一致。Kimi 的 30-day cleanup + 共享 graph + source-scoped memory + 无 curator 与决策 6 直接矛盾(memory 不持久 / scope 不对 / 无 self-evolution)。**T6 在 state 维度更好服务决策 5 + 6。**

#### 维度 4 cross-validation(与 Phase 44 §2.5 + §2.6 推导链一致)

本节选型论据与 Phase 44 §2.5(决策 5 推导链)+ §2.6(决策 6 推导链)的 cross-validation:

- **Phase 44 §2.5 Steelman 排除论证(subagent form):** 「subagent lifecycle 绑 CC session,transcripts 30 天清理,违反『agent 随项目越多越有经验』核心诉求」 —— 本节 §3.4 Kimi cons (a) verbatim 引用这个排除论证。
- **Phase 44 §2.6 根本需求(per-agent memory + curator):** 「agent 随项目越多越有经验(v10.0 paradigm shift 核心诉求)—— 业界没有任何主流框架把 per-agent scoped memory + curator-driven 自进化作为原生组合」 —— 本节 §3.4 T6 pros (a) 显式标注「决策 6 完整 support」,与 Phase 44 §2.6 推导一致。
- **Phase 44 §2.6 Cross-Validation Evidence(SUMMARY.md 'Design Decisions Validated' 决策 6 行):** 「FEATURES §9.2 memory 模式速查表显示『没有一个主流框架把 per-agent scoped memory + curator-driven 自进化作为原生组合』,v10.0 是真正的差异化」 —— 本节 §3.4 选型论据「Kimi source-scoped memory + 无 curator 与决策 6 直接矛盾」与 Phase 44 §2.6 cross-validation 一致。

**Cross-validation 结论:** 本节选型论据 100% align Phase 44 §2.5 + §2.6 锁定的决策推导,本 doc §7 audit 时决策 5 + 6 的引用都标 ✅(详见 §7.1 audit table row 5 + row 6)。

---

### §3.4-summary — 维度 4 state 总结(三层持久化的 paradigm 含义)

**Paradigm-level 总结:** T6 的三层 state 不是「技术细节」,是 v10.0 paradigm shift 的物理载体 —— Phase 44 §Executive Summary verbatim:「v10.0 不写一行业码,而是把『agent 随项目越多越有经验』推导成 7 份设计文档」。这句话的字面含义是:agent 必须持久(agent YAML)+ agent 的经验必须持久(per-agent mem0 backend memory records)+ agent 的协商历史必须持久(round_tables/{id}.json)。**三层缺一不可**,任何一层 30-day cleanup 或 shared graph 都打破 paradigm。

**Kimi 方案 paradigm-level 评估:** Kimi 方案在 state 维度的形态(subagent transcripts 30-day + shared knowledge graph + source-scoped CLAUDE.md)服务的 paradigm 是「single-session task completion」—— 一次任务跑完,subagent 销毁,下次重头开始。这与 OpenAI Swarm 的 ephemeral 轻量哲学(Phase 44 §3 row 5 + FEATURES §5)同构,不是 v10.0 paradigm。

**Operator 投入角度:** 在 v10.0 paradigm 下,operator(Kai)的投入包括:调 persona / 喂 feedback / 跑 fitness battery / review curator evolution_log —— 这些投入累积成 agent 的「行业经验」(类比 Phase 44 §1.2 根本需求列「让每个 movie-expert skill 都能用检索增强的方式调用行业知识库」)。Kimi 方案的 30-day cleanup 意味着 operator 投入每月归零,这是 v10.0 paradigm 不可接受的。

**OQ-12 在本维度的张力:** ARCHITECTURE §3.2 + PITFALLS §3 mitigation 1 揭示 T6 三层 state 的一个未实测张力 —— `agent_id` filter 在 mem0 backend Option B(filter 路由)部署下,18-agent × 100-project 规模是否真能保持 p95 < 500ms(OQ-12,defer 到 Phase 48 + v11.0 PoC week-1 latency benchmark)。这是 T6 自身的 weak point —— Kimi 方案的「共享 knowledge graph」在 infra 复杂度上反而简单(一个 graph server + RAG)。但即便如此,本 doc 仍选 T6,因为「per-agent scoped memory」是决策 6 的根本需求(非协商性),「infra 复杂度」是工程量维度(决策 4 + §3.6);OQ-12 的 latency benchmark 是 PoC 验收条件(Phase 50),不是选型否决条件 —— 若 p95 > 500ms 触发物理分区切换(每 agent 一个 mem0 workspace,ARCHITECTURE §3.2 Option C),不是切回 Kimi 共享 graph 模式。

**字段级 mitigation 映射(本节 §3.4 T6 pros (d) 的展开):**

| PITFALL | Phase 45 字段(本 doc CITE ONLY) | 在 Kimi 方案是否可 mitigation? |
|---------|---------------------------------|-------------------------------|
| P1 persona drift | `persona_sha256`(agents-schema §2.14) | ❌ Kimi AgentDefinition 无此字段 |
| P2 stale memory | `expires_at` + `verified_at` + `supersedes_memory_id`(memory-record-schema §3.1-§3.4) | ❌ Kimi memory 是 CLAUDE.md 静态文件,无 staleness 字段 |
| P4 cross-project leakage | `scope: global\|project\|session` + `project_id` required(memory-record-schema §3.9) | ❌ Kimi `memory: 'project'` 是 source-file 选,不是 namespace scope |
| P5 curator failure modes | `evidence_chain` + dry-run-first | ❌ Kimi 无 curator(决策 6 unavailable) |
| P7 round-table memory conflict | Phase 46 §3.1-§3.5 5 子机制(基于 `citedMemoryIds`) | ❌ Kimi subagent return 不带 citedMemoryIds |
| P8 no fitness signal | `fitness_score`(agents-schema §2.15) | ❌ Kimi AgentDefinition 无此字段 |
| P10 privacy | `confidentiality`(memory-record-schema §3.10) | ❌ Kimi memory 是 CLAUDE.md plaintext |
| P12 cross-agent contamination | `agent_id` filter(per-agent namespace) | ❌ Kimi 共享 graph,filter 不严 |

8/8 PITFALLS 字段级 mitigation T6 都有,Kimi 方案 8/8 都没有 —— state 维度是 T6 vs Kimi 差距最大的维度。

---


### §3.5 — 维度 5:多 agent(Multi-Agent Coordination)

#### T6 描述

T6 的多 agent 模型是 **Round table 协议**(Phase 46):5-strategy `turn_order`(round-robin default + fixed / llm / matrix / fitness-weighted,v11.1+ deferred per Phase 46 §2.5.5)+ memory conflict arbitration(Phase 46 §3,5 子机制对齐 PITFALLS §P7 mitigation 1-5)+ **强制串行**(1 panelist 1 turn sequential `await`,Phase 46 §1.5.1 + §2.8 + §4.1 root-cause analysis)。

**Round table 三原子操作(Phase 46 §2):**

1. `round_table_open(roundId, panel, question, maxRounds, turnOrderStrategy, earlyStopRule, projectId)` —— atomic start,返回 roundId(立即返回,不阻塞)。
2. turn N(`get_agent_opinion(agentId, topic, context, priorDiscussion)` per turnOrder,sequential await,append 到 state file turns 数组)。
3. `submit_round_table_result(roundId, conclusion, citedMemories, artifacts, conflicts)` —— atomic commit,flip status=completed,seal conflict log。

**Memory conflict arbitration(Phase 46 §3):** 当两个 panelist 的 `citedMemoryIds` 在语义上矛盾,comparator LLM pass + scope precedence(session > project > global)+ confidence-weighted voting + conflict log append(供 curator review)。这是 P7(round-table memory conflict)的完整 mitigation。

**强制串行(Phase 46 §1.5.1 + §4.1 root-cause):** GLM 4-key rotation 在 7 panelist × N rounds 并发场景下会立刻撞 ceiling(~800K TPM)。MEMORY.md `feedback-glm-overload-reduce-concurrency.md`(2026-07-06)记录 global concurrency==1 是 **BY DESIGN**(2026-07-03 从 5→3;2026-07-06 已是 1,不再降 —— 上游模型容量本身就是瓶颈)。Round table 强制 serial 是这个 policy 的物理载体。

#### Kimi 描述

Kimi 方案的多 agent 模型是 **Subagent 不互发言** —— FEATURES §4.2 row 3 verbatim:「**不原生支持 multi-agent**。Claude 自己作为 main agent,可调 `Agent` tool 派生 subagent 做子任务,subagent 返回 final message;**不是 round table**(无多 subagent 互发言)」。

Main agent 可以 **fan-out 多 subagent**(v2.1.198+ background 默认,可并发),但 subagent 之间不通讯。Main agent 收集所有 final messages 后做 synthesis —— 这是 hub-and-spoke,不是 round table。

**无 memory conflict arbitration 概念** —— subagent return 是 final message string,不带 `citedMemoryIds`;main agent synthesis 时若发现矛盾,只能靠 LLM reasoning 自行解决,没有结构化 arbitration 机制。

#### T6 pros

(a) **真正的 round table 协议(决策 3 — D2 storyboard-first-class requires round-based parallel)** —— Phase 46 §2 三原子操作是 D2 的物理载体。决策 3 要求「在不破坏 V8.6 编号契约(FOUND-08)的前提下,获得真实有价值的并行加速(跨场景,不跨 step)」—— round table 让多个 panelist(screenplay / cinematographer / scene_builder etc.)就同一 scene 协商。
(b) **Memory conflict arbitration 避免 P7(loud-memory agent wins)** —— Phase 46 §3 comparator LLM + scope precedence + confidence voting 让 conflict 不是「谁嗓门大谁赢」,而是结构化裁定。Kimi 方案无此机制。
(c) **Serial constraint 兼容 GLM 4-key rotation(Phase 46 §4.1 + MEMORY.md feedback-glm-overload-reduce-concurrency.md)** —— v10.0 强制 serial 与 operator-level concurrency==1 policy 一致,不会撞 GLM ceiling。这是 by-design,不是限制。

#### T6 cons

(a) **Serial execution means 7 panelist × 3 rounds ≈ 21 sequential LLM calls** —— ~137K tokens,~10s serial latency(STACK §7 token cost ~550K/pipeline run 估算)。这是 acceptable(STACK §7.5 verbatim:顺序 `await`,不并发)。
(b) **Conflict arbitration 是新机制,v11.0 PoC 需 bias canary** —— Phase 50 acceptance criterion:bias canary 必须跑通,确保 comparator LLM 不偏向高 confidence 但 low evidence 的 memory。

#### Kimi pros

(a) **Background subagent 可以并发(但 GLM 4-key rotation 会立刻撞 ceiling —— FEATURES §14 gap 6 + CC-6)** —— 表面上「并发更快」,但 v10.0 GLM 政策下并发不可行。

#### Kimi cons

(a) **无法表达 round table,决策 3(D2)无法实施** —— subagent 不互发言意味着没有协商,只有 fan-out + synthesis。决策 3 要求 round-based parallel,Kimi 不能表达。
(b) **Subagent 间无通讯意味着 panelist 看不到彼此的 cited memory —— memory conflict 无法 arbitration** —— Phase 46 §3 的 5 子机制都基于「panelist 在 turn N 引用 citedMemoryIds,comparator LLM 跨 panelist 对比」,Kimi subagent return 不带 citedMemoryIds。
(c) **Background 并发与 GLM concurrency==1 policy 矛盾** —— Kimi 方案的「background fan-out」在 v10.0 GLM 4-key rotation 政策下不可行,会撞 ceiling 触发 1305 错误。

#### 选型论据

**决策 3 + 7。** T6 的 round table 协议是决策 3(D2 storyboard-first-class)的物理载体 —— 真正的 round-based parallel,跨场景协商。Kimi 的 subagent fan-out 无法表达协商(subagent 不互发言)。Phase 46 §4.1 serial invariant 与 MEMORY.md `feedback-glm-overload-reduce-concurrency.md` 一致 —— Kimi 的 background 并发违反这个 policy。**T6 在多 agent 维度更好服务决策 3 + 7。**

### §3.6 — 维度 6:实现成本(Implementation Cost)

#### T6 描述

T6 的实现成本(从 STACK §3.2 + ARCHITECTURE §3-§5 + Phase 46 §5 估算):

1. **Extend `mcp_serve.py` 加 7 MCP tools(STACK §3.2)** —— Pydantic schema 已 spec'd(STACK §3.2 给完整 7 tool schema),实施量 ~500-800 LOC Python(v11.0 PoC 估算)。
2. **Hermes agent registry(ARCHITECTURE §4 — `agent/agent_registry.py` + `agent/agent_dispatcher.py`)** —— load YAML + dispatch via tmux + tools whitelist enforcement。~400-600 LOC Python。
3. **mem0 backend additive extension(ARCHITECTURE §3.3)** —— `_scoped_agent_id` filter via `contextvars` in ThreadPoolExecutor。~50-100 LOC Python(在现有 v7.0 mem0 plugin 375 lines 之上加 additive)。
4. **Round table state file gc pass(defer v11.1+)** —— completed round table retention policy + crash recovery gc。~100 LOC Python,v11.1+ ship。
5. **Curator `_memory_evolution_phase`(ARCHITECTURE §3.4 + Phase 45 §5)** —— 在 v6.0 `_feedback_scan_phase` 之后跑,独立 try/except 包裹,dry-run-by-default。~200-300 LOC Python(extend v6.0 curator)。

**v10.0 设计型 milestone:** 零代码,产出文档。**v11.0 PoC 工程量估算:** ~2-3 人周(1250-1800 LOC Python,复用 v6.0 curator + v7.0 mem0 + 现有 `mcp_serve.py` FastMCP)。

#### Kimi 描述

Kimi 方案的实现成本:

1. **写 `.claude/agents/*.md` per expert** —— markdown,~30-50 lines frontmatter + prompt each × 15 experts = 450-750 lines markdown。
2. **共享 knowledge graph server(额外基础设施,Agent-MCP §7.2 模式)** —— RAG server + embedding cost + graph gc + sync。这是新基础设施,v10.0 没有(决策 6 用 mem0 backend)。
3. **把 agent ↔ agent 协调塞进 MCP tools(`create_agent` / `assign_task` / `send_agent_message` etc. per Agent-MCP §7.2)** —— 设计 7+ MCP tools 的 schema + tests。工程量 ~500-800 LOC Python(与 T6 的 7 tool 工程量相当,但语义不同 —— Kimi 是 agent ↔ agent,T6 是 agent ↔ tool)。

#### T6 pros

(a) **复用现有 `mcp_serve.py`(907 lines 实读,extension 而非 rewrite)** —— v7.0 ship 的 FastMCP server,加 7 tool 是 decorator + Pydantic schema,无新依赖。
(b) **复用现有 mem0 plugin(v7.0 ship,375 lines)** —— additive extension `_scoped_agent_id` 不是新 backend,是 filter routing。
(c) **复用现有 curator(v6.0 ship,2467 lines)** —— extend `_feedback_scan_phase` 加 `_memory_evolution_phase` sibling,不是新模块。
(d) **决策 4(G2 通用编排)means kais-movie-pipeline 是首个 sample,工程量摊薄** —— G2 抽象 pipeline orchestration pattern,kais-movie-pipeline 是 sample;后续 music video / long-form 不需要重写编排器。T6 的工程量在多个 domain 摊薄。

#### T6 cons

(a) **7 个新 MCP tool 的 Pydantic schema 设计 + 测试(v10.0 已 spec,v11.0 PoC 实施)** —— 工程量 ~500-800 LOC,加上 schema test / runtime test / integration test。
(b) **mem0 backend filter 行为未实测(OQ-12)** —— v11.0 PoC week-1 latency benchmark 必跑,若 p95 > 500ms 触发物理分区切换(增加额外工程量)。

#### Kimi pros

(a) **markdown 文件工程量极小(15 files × 50 lines = 750 lines markdown)** —— 写 agent 就是写 markdown,无 Python 代码。
(b) **无需 extend Hermes runtime** —— agent 就是文件,CC 原生识别 `.claude/agents/`。

#### Kimi cons

(a) **共享 knowledge graph 是新基础设施(RAG server,embedding cost,gc)** —— 不是「零 Hermes-side runtime」,而是「换了一个不同的 Hermes-side runtime」。Agent-MCP 模式需要 graph server + embedding + sync,工程量被低估。
(b) **把 agent ↔ agent 塞进 MCP 意味着设计 7+ MCP tools(`create_agent` etc.)—— 工程量不比 T6 小** —— Kimi 方案的 MCP tool 工程量 ~500-800 LOC,与 T6 相当。
(c) **决策 4(G2 通用编排)在 Kimi 方案下难以实施 —— 共享 graph 是 project-scoped,跨 project 编排需要额外机制** —— G2 要求「v12+ 扩展 music video / long-form 时不需要重写编排器」,Kimi shared graph 是 project-scoped,跨 project 编排需要每 project 部署 graph server,违反 G2 抽象。

#### 选型论据

**决策 4。** T6 复用现有 v6.0/v7.0 设施(curator + mem0 + FastMCP),与决策 4(G2 通用编排)一致 —— 工程量在多个 domain 摊薄。Kimi 方案需要新基础设施(shared graph)且工程量被低估(`.claude/agents/` markdown 之外还有 graph server + 7+ MCP tools),且决策 4 在 Kimi 方案下难以实施。**T6 在实现成本维度更好服务决策 4。**

### §3.7 — 维度 7:稳定性(Stability / Pitfall Mitigation)

#### T6 描述

T6 的稳定性是 **多层 defense-in-depth**:

1. **Hermes-side persistent agent(YAML 持久,跨 CC session,跨 project)** —— 决策 5 物理载体。
2. **Per-agent scoped memory with curator-driven self-evolution(决策 6)** —— mem0 backend + `_scoped_agent_id` filter + curator `_memory_evolution_phase`(Phase 45 §5)。
3. **Curator dry-run-by-default + bias canary(Phase 45 §5 + Phase 50 acceptance criterion)** —— curator 写 memory record 默认 dry-run,operator review 后才真写;bias canary 在每 N tick 跑,确保 curator 不偏向某 operator / 某 agent。
4. **Memory record schema with `expires_at` / `verified_at` / `confidence` / `evidence_chain` / `supersedes_memory_id` / `half_life_days`(Phase 45 memory-record-schema)** —— 字段级 mitigation for P2(stale memory)—— `expires_at` + `verified_at` 让 memory 自动过期;`confidence` + `evidence_chain` 让低质 memory 被自然降权;`supersedes_memory_id` 让新 memory 正式替换旧 memory;`half_life_days` 让 confidence 时间衰减。
5. **Cross-project leakage mitigated by `scope` field(Phase 45) + filter routing(Option B per ARCHITECTURE §3.2)** —— `scope: global|project|session` + `project_id` required + cross-project promotion gate(Phase 46 §3.3 scope precedence)。
6. **Persona drift mitigated by `persona_sha256`(Phase 45 agents-schema §2.14)** —— 不变量:agent YAML 的 persona SHA-256 在 round table open-time snapshot 到 state file;若 curator 检测到 persona_sha256 drift,触发 advisory(ARCHITECTURE §8.2 anti-pattern guard:不 auto-re-transform,operator decides)。
7. **Round table memory conflict mitigated by Phase 46 §3 5 子机制(comparator LLM + scope precedence + confidence voting + conflict log + curator review)** —— P7 完整 mitigation。
8. **Cross-agent contamination mitigated by `agent_id` filter namespace(PITFALLS §P12)** —— per-agent namespace 隔离,screenplay agent 检索不到 cinematographer agent 的 memory。

#### Kimi 描述

Kimi 方案的稳定性:

1. **Subagent transcripts 30-day cleanup(FEATURES §4.3 fact 3)—— agent experience 不可持久** —— operator 投入 30 天后丢失。
2. **Shared knowledge graph single-point-of-failure(graph server down → all agents lose memory)** —— 共享 graph 是单 graph server,宕机 = 全 agent memory 不可用。
3. **Cross-agent contamination risk(PITFALLS §P12 — shared graph + imperfect filter = bleed-through)** —— 共享 graph 意味着 RAG filter 不严时 screenplay 可能检索到 cinematographer 的 memory。
4. **No curator self-evolution(决策 6 unavailable)** —— Kimi memory 是 CLAUDE.md 静态文件,curator 无法 read/write per-record,决策 6「curator-driven 自进化」完全 unavailable。

#### T6 pros

(a) **Per-agent memory isolation(决策 6)avoids P12 cross-agent contamination** —— screenplay agent 的 memory namespace 与 cinematographer agent 完全隔离。
(b) **`confidence` + `evidence_chain` + `expires_at` avoids P2 stale memory** —— 字段级 mitigation,不需额外机制。
(c) **`persona_sha256` avoids P1 persona drift** —— round table open-time snapshot,curator drift detection。
(d) **Curator dry-run-first avoids P5 curator failure modes** —— dry-run-by-default 让 false-delete / hallucinate / bias amplify 在 dry-run 阶段被发现,operator review。
(e) **Memory record schema 8 个 PITFALL 字段级 mitigation(P1/P2/P4/P5/P7/P8/P10/P12)** —— 见 §3.4 维度 4 字段级 mitigation 映射表。

#### T6 cons

(a) **v11.0 PoC 需 bias canary + latency benchmark(defer 到 Phase 50)** —— 字段级 mitigation 是 schema 设计,实际效果需 PoC 验证。
(b) **18-agent × 100-project 规模下 mem0 filter 行为未实测(OQ-12,defer Phase 48)** —— Option B(filter 路由)在大规模下可能崩溃,需物理分区切换。

#### Kimi pros

(a) **Shared graph 节省 per-agent memory backend 复杂度** —— 一个 graph server,运维简单。

#### Kimi cons

(a) **30-day cleanup 直接违反决策 6 「agent 随项目越多越有经验」** —— operator 投入 30 天后归零。
(b) **Shared graph 单点故障** —— graph server down = 全 agent memory 不可用。
(c) **P12 cross-agent contamination 不可 mitigation(graph 是共享的)** —— 共享 graph + RAG filter 不严 = bleed-through 不可避。
(d) **无 curator → 无 self-evolution → 决策 6 完全 unavailable** —— Kimi 方案在决策 6 维度是「完全缺失」,不是「弱实现」。

#### 选型论据

**决策 6 + PITFALLS §P5/§P12。** T6 的 per-agent scoped memory + curator 是决策 6 的物理载体,P1/P2/P5/P7/P8/P10/P12 都有字段级 mitigation(8 个 PITFALLS)。Kimi 方案直接违反决策 6(30-day cleanup + shared graph + 无 curator),且 P5/P12 无法 mitigation。**T6 在稳定性维度更好服务决策 6。** 这也是 7 维度中 T6 vs Kimi 差距最 stark 的维度 —— 字段级 mitigation 是 schema 设计,不是工程量问题,Kimi 方案即使工程量再大也无法达到同等等级。

#### 维度 7 stability 总结(stark gap 与 dry-run-first 的角色)

**为什么说稳定性是 T6 vs Kimi 差距最 stark 的维度?** 因为其他 6 个维度(协议 / dispatch / callback / state / 多 agent / 实现成本)的差距可以通过「工程量」「实施细节」「学习曲线」来衡量 —— 例如 dispatch 维度 T6 多 ~500 LOC Python,可以通过工程投入弥合。但稳定性维度的差距是 **schema-level paradigm gap**:T6 的 Phase 45 memory-record-schema(10 个字段)+ agents-schema 的 `persona_sha256` / `fitness_score` / `evolution_log` 字段是 PITFALLS 14 个失败模式的字段级 mitigation;Kimi 的 `AgentDefinition`(9 个字段,无任何 PITFALL 字段)+ source-scoped memory + shared graph 是 **结构性缺失**,不是「工程量少了」,是「schema 没有」。

**dry-run-first 在稳定性维度的角色(Phase 45 §5 + Phase 50 acceptance criterion):** T6 curator `_memory_evolution_phase` 默认 dry-run-by-default —— 写 memory record 到 dry-run 目录,operator review 后才 merge 到真实 mem0 backend。这是 P5(curator failure modes: false-delete / hallucinate / bias amplify)的 mitigation 5。Kimi 方案没有 curator 也就没有 dry-run-first 这条 defense,任何 memory write 都是 immediate + irreversible(写 CLAUDE.md 或 shared graph)。

**v11.0 PoC 验收条件(Phase 50):**

- bias canary:每 N tick 跑,确保 curator 不偏向某 operator / 某 agent(超过阈值触发 ADVISORY)
- latency benchmark:mem0 backend filter 在 18-agent × 100-project 规模下 p95 < 500ms(OQ-12)
- fitness battery:agent `fitness_score` cold-start(null)→ 经过 N 次 round table 后实际数值变化与人类判断对齐
- schema migration dry-run:从 v9.0 SKILL 形态迁到 v10.0 agent YAML 形态的 dry-run 不破坏现有 memory store

**这 4 条 PoC acceptance criteria 都是 T6 的稳定性验证** —— Kimi 方案因为没有 curator / fitness_score / schema migration 概念,无法表达这些 acceptance criteria。这是 v11.0 PoC 实施者必须理解的:**选 T6 意味着接受 v11.0 PoC 的 4 条 acceptance criteria 负担,选 Kimi 意味着放弃 stability mitigation 的 schema-level 支持。**

### §3-overall — 7-dimension contrast 总结(T6 7/7,Kimi 0/7)

**7 维度整体审计:** 把 §3.1-§3.7 的选型论据汇总,T6 在 7/7 维度都更好服务 Phase 44 决策;Kimi 在 7/7 维度都至少违反一条决策。

| 维度 | T6 选型论据(决策号) | Kimi 违反决策号 | gap 性质 |
|------|---------------------|----------------|----------|
| §3.1 协议 | 决策 1 | 决策 1(违反 Microsoft 三层)+ 决策 5(agent identity 在 CC filesystem,非 platform-native) | 业界共识 gap(Microsoft 三层) |
| §3.2 dispatch | 决策 5 + 7 | 决策 5(30-day cleanup)+ 6(source-scoped 非 namespace)+ 7(tools whitelist CC-controlled) | paradigm gap(agent 拥有权归属) |
| §3.3 callback | 决策 7 + 3 | 决策 3(无 round table)+ 7(CC 全控) | 功能 gap(无法表达协商) |
| §3.4 state | 决策 5 + 6 | 决策 6(30-day cleanup + shared graph + 无 curator) | paradigm gap(per-agent memory 不可表达) |
| §3.5 多 agent | 决策 3 + 7 | 决策 3(无协商)+ 7(违反 GLM concurrency policy) | 功能 gap + 政策 gap |
| §3.6 实现成本 | 决策 4 | 决策 4(shared graph 是 project-scoped,G2 难实施) | 工程量低估 |
| §3.7 稳定性 | 决策 6 | 决策 6(直接违反)+ 8/14 PITFALLS 字段级 mitigation 缺失 | schema-level paradigm gap(最 stark) |

**关键观察:** Kimi 方案在 7 个维度都违反决策,但**违反性质不同**:

- **功能 gap(§3.3 + §3.5):** Kimi 方案缺 round table / memory conflict arbitration 概念 —— 理论上可以通过工程投入补足(给 Kimi 方案加 round table MCP tools),但这样 Kimi 方案就变成 T6 了
- **paradigm gap(§3.2 + §3.4 + §3.7):** Kimi 方案根本不支持 per-agent scoped memory / curator self-evolution / agent 拥有权在 Hermes —— 这不是「工程量不够」,是「Kimi paradigm 不同」(CC 是 agent container vs Hermes 是 agent container)
- **业界共识 gap(§3.1):** Kimi 方案违反 Microsoft 三层 —— 这是外部权威 anchor,与 v10.0 自身决策无关
- **政策 gap(§3.5):** Kimi 方案的 background 并发与 GLM concurrency==1 policy 矛盾 —— 这是 v10.0 特定政策约束,不是 Kimi 方案本身缺陷

**这 4 种 gap 性质的 practical implication:**

- **功能 gap 可补足,但补足后 Kimi 方案 = T6** —— 即 Kimi 方案不存在独立演化路径,只能向 T6 收敛
- **paradigm gap 不可补足** —— Kimi 方案的「CC 是 agent container」与 v10.0 的「Hermes 是 agent container」根本对立,Kai user memory `hermes-native-expert-agents.md`(2026-07-06)已显式否决 Kimi paradigm
- **业界共识 gap 给 v10.0 外部 anchor** —— SC#4 验证依赖这个 anchor,本 doc §4 是这个 anchor 的完整论证
- **政策 gap 是 v10.0 特定约束** —— 若未来 GLM 容量扩展允许 concurrency > 1,这条 gap 可能消失(但其他 3 条不会)

---

---

## §4 — Microsoft Three-Layer Protocol Validation(SC#4 Deep-Dive)

### §4.0 — 本节是 ROADMAP SC#4 的完整论证

本节是 **ROADMAP SC#4(Microsoft three-layer protocol validation citing FEATURES §7.4 B7.1 proving v10.0 T6 aligns with industry consensus)** 的完整论证。§1.5.1 已声明 citation,§4 给完整 mapping + Kimi violation analysis + 业界共识论证。

**Microsoft 指引是 FEATURES §7.4 B7.1 引用的一手源(HIGH 置信度):** Microsoft multi-agent-patterns 官方指引([learn.microsoft.com/en-us/agents/architecture/multi-agent-patterns](https://learn.microsoft.com/en-us/agents/architecture/multi-agent-patterns)),由 Microsoft Agent Framework v1.0 GA(2026-04)+ Microsoft multi-agent-patterns 团队维护。这是业界权威指引,与 v10.0 设计的对照验证 T6 与业界共识一致。

### §4.1 — Microsoft 三层引用(verbatim from FEATURES §7.4)

**Citation verbatim from FEATURES §7.4 B7.1(source: Microsoft multi-agent-patterns 官方指引):**

> - **Platform-native orchestration** for internal flows(平台原生,最低成本)
> - **MCP** for tool and data access(MCP 做 agent ↔ tool)
> - **A2A** for cross-platform agent-to-agent messaging(A2A 做 agent ↔ agent,跨厂商)

**MCP vs A2A selection table(verbatim from FEATURES §7.3 source):**

| 能力 | MCP | A2A |
|------|-----|-----|
| Multimodality | 需 host 支持 | 显式 advertisement |
| Multi-turn interactions | host 持 context | `contextId` 跨 agent |
| Orchestration | host orchestrate | invoked agent 自己 reason |
| Negotiation | client 更新才支持 | 动态 negotiation |

**Source authority:** Microsoft Agent Framework v1.0 GA(2026-04)+ Microsoft multi-agent-patterns 官方指引(URL: [learn.microsoft.com/en-us/agents/architecture/multi-agent-patterns](https://learn.microsoft.com/en-us/agents/architecture/multi-agent-patterns))。FEATURES §7 置信度 HIGH —— 主源是 Microsoft 官方文档,本 doc 引用不再降级。

### §4.2 — v10.0 T6 → Microsoft 三层 mapping table

| Microsoft layer | v10.0 T6 instantiation | Phase 44 决策 | Citation |
|-----------------|------------------------|---------------|----------|
| **Platform-native(internal flows)** | Hermes Python runtime —— agent registry YAML loader, dispatcher, curator, mem0 backend | 决策 5(agent 是 Hermes-side entity)+ 6(curator-driven)+ 7(Hermes 控结构) | ARCHITECTURE §4 dispatch path;STACK §1 Recommended Stack |
| **MCP(tool access)** | Hermes MCP server extends `mcp_serve.py` with 7 STACK-form tools(STACK §3.2 STACK-form naming)—— CC calls these tools for agent persona / opinion / memory / round table lifecycle | 决策 1(T6 协议)+ 7(Hermes 暴露结构 via schema) | STACK §1 + §3.2;Phase 46 §5 MCP tool contract |
| **A2A(cross-platform)** | **Deferred —— v10.0 single-vendor internal,不需要 A2A.** v12+ 跨厂商协作时 A2A 是正确协议(per B7.4)。 | 决策 1(T6 排除 A2A for v10.0) | FEATURES §8.3 + B7.4;06-CROSS-REPO-IMPACT.md will record 扩展位 |

**Mapping 结论:** T6 完全 align Microsoft 三层 —— internal flow 走 Hermes Python runtime(platform-native,Microsoft 说「最低成本」)+ tool access 走 MCP(Hermes MCP server extends `mcp_serve.py`)+ cross-platform 不需要(v10.0 single-vendor)。这与 Phase 44 §2.1 决策 1 推导链一致。

### §4.3 — Kimi 全 MCP shim → Microsoft 三层 violation analysis

Kimi 方案在 Microsoft 三层框架下是 anti-pattern,具体违反 3 条:

**Violation 1:** Kimi 把 agent ↔ agent 协调塞进 MCP tools(`create_agent` / `assign_task` / `send_agent_message` / `broadcast_message` per Agent-MCP §7.2)。Microsoft 三层明确「**MCP for tool and data access**」—— MCP 单一职责是 agent ↔ tool,不是 agent ↔ agent。Kimi 方案在 Microsoft 框架下是 anti-pattern:agent ↔ agent 协调应走 platform-native(同 host,如 Hermes Python runtime 内部 dispatch)或 A2A(跨厂商),不应走 MCP。

**Violation 2:** Kimi 把 agent identity 放在 CC filesystem(`.claude/agents/*.md`),不是 platform-native。Microsoft「**Platform-native orchestration for internal flows**(平台原生,最低成本)」意味着 internal agent lifecycle 应由 platform runtime 管(Hermes Python),不是 client-side filesystem。`.claude/agents/` 是 CC 工作目录,不是 platform runtime —— Kimi 方案违反 Microsoft「platform-native」原则。

**Violation 3:** Kimi 不为 A2A 留扩展位 —— 共享 knowledge graph 是 project-scoped,跨厂商协作时无法切换到 A2A。T6 把 agent identity 放在 Hermes runtime,未来可暴露 A2A Agent Card(FEATURES §8.1 B8.1)。Kimi 方案的 shared graph 是 lock-in,扩展位缺失。

### §4.4 — 业界共识论证(B7.1 + B2.2 + B7.4 三条 borrowable points 一致结论)

**B7.1(Microsoft 指引):** 「三层协议分层(platform / MCP / A2A)验证 T6」 —— T6 完全 align(§4.2 mapping table)。

**B2.2(MAF "A2A 一等公民" 立场):** Microsoft Agent Framework 把 A2A 作为一等公民,但明确「**A2A for cross-platform**」—— v10.0 是 single-vendor(Hermes ↔ CC),所以不依赖 A2A 与 MAF 立场一致。MAF 推 A2A 是因为 MAF 面向 cross-vendor 场景,v10.0 不在 MAF target scenario 内。

**B7.4(MS 指引 A2A 扩展位):** 「**A2A 是 v12+ 跨厂商扩展位**」 —— T6 留扩展位(Hermes runtime 作 A2A Agent Card publisher,06-CROSS-REPO-IMPACT.md 记录),Kimi 方案不留(shared graph lock-in)。

**结论:** 三个 FEATURES borrowable points(B7.1 + B2.2 + B7.4)都指向同一结论 —— **T6 与 Microsoft / MAF 业界共识一致,Kimi 方案违反三层分层**。这不是「T6 凑巧 align Microsoft」,而是「v10.0 paradigm shift 的根本需求(决策 1 — 稳定、低故障面、可演进的通信通道)与 Microsoft 业界共识同构」—— Phase 44 §2.1 决策 1 推导从根本需求出发,Microsoft 三层从业界共识出发,两者独立得出一致结论。

### §4.5 — A2A 扩展位声明

**v10.0:** 不需要 A2A —— single-vendor Hermes ↔ CC,Microsoft「Platform-native + MCP」两层足够。

**v12+:** 若 Kai 未来想让 hermes-agent 与外部 agent 系统协作(e.g. 另一个项目 / 另一个 LLM provider / 另一个厂商的 agent framework),A2A 是正确协议。具体扩展位:

- Hermes runtime 作 A2A Agent Card publisher(暴露 `agent_card` JSON via HTTP endpoint)
- A2A Task lifecycle 状态机(submitted / working / input-required / completed / failed)映射到 round table state(Phase 46 round-table-state-schema `status` enum)
- A2A `contextId` 映射到 roundId

**Citation:** FEATURES §8 + B7.4 + B8.3。**Defer 到 06-CROSS-REPO-IMPACT.md 记录扩展位 —— 本 doc 只声明 v10.0 不需要 A2A + 留扩展位。**

### §4.6 — Microsoft 三层验证的 reviewer 角度总结

**Kai(reviewer)视角的 §4 一句话总结:** v10.0 决策 1 选 T6 协议层,与 Microsoft multi-agent-patterns 官方指引(FEATURES §7.4 B7.4 引用,HIGH 置信度 source)的「Platform-native + MCP + A2A」三层分层**完全一致**;Kimi 全 MCP shim 方案违反三层分层(agent ↔ agent 不应走 MCP / agent identity 不应在 client filesystem / shared graph 不留 A2A 扩展位)。这不是 v10.0 凑巧 align 业界,而是 v10.0 paradigm shift 的根本需求(决策 1:稳定、低故障面、可演进)+ Microsoft 业界共识**独立得出同构结论** —— Phase 44 §2.1 决策 1 推导链(从「Hermes 与 CC 之间需要稳定、低故障面、可演进的通信通道」根本需求推 T6)+ Microsoft 三层(从 cross-vendor agent ecosystem 实战经验推 platform-native / MCP / A2A 分层)是两条独立路径到达同一结论。

**Kimi 续聊对照视角的 §4 一句话总结:** 本 doc 不否定 Kimi 方案在「single-vendor + minimize engineering effort」目标下的合理性,但 Microsoft 业界共识给了一个**外部权威 anchor** —— 「internal flow → platform-native;tool access → MCP;cross-platform → A2A」。Kimi 方案把 agent ↔ agent 塞进 MCP 违反这个共识,不是因为 v10.0 说它违反,而是因为 **Microsoft 作为业界权威指引说它违反**。这是 SC#4 的核心论证:**v10.0 T6 与业界共识一致,不需要 v10.0 自我证明**。

**v11.0 PoC 实施者视角的 §4 一句话总结:** 当实施者问「为什么我们 extend `mcp_serve.py` 而不是把 agent ↔ agent 也塞进 MCP?」,§4.1 + §4.3 violation 1 是答案 —— Microsoft 业界共识说 MCP 单一职责是 tool access,把 agent ↔ agent 塞进 MCP 是 anti-pattern。当实施者问「v12+ 我们要不要切到 A2A?」,§4.5 是答案 —— v10.0 留扩展位,v12+ 跨厂商时启用,具体扩展位记录在 06-CROSS-REPO-IMPACT.md。

**Microsoft multi-agent-patterns URL citation(Phase 51 lint 用):** [learn.microsoft.com/en-us/agents/architecture/multi-agent-patterns](https://learn.microsoft.com/en-us/agents/architecture/multi-agent-patterns) —— FEATURES §7.4 B7.1 引用的一手源,HIGH 置信度。Phase 51 VALIDATE lint script 检查本 doc 是否包含此 URL(cross-doc consistency)。

**Claude Agent SDK subagents docs URL citation(§5 deep-dive 用):** [code.claude.com/docs/en/agent-sdk/subagents](https://code.claude.com/docs/en/agent-sdk/subagents) —— FEATURES §4.2 + §4.3 引用的一手源,HIGH 置信度。§5 subagent rejection deep-dive 会 verbatim 引用 §4.3 三个 fact,每个 fact 都可 trace 到此 URL。

**Microsoft Agent Framework v1.0 GA URL(供 v12+ 跨厂商协作时参考):** [learn.microsoft.com/en-us/agent-framework/overview](https://learn.microsoft.com/en-us/agent-framework/overview) —— MAF v1.0 GA(2026-04),v12+ hermes-agent 与外部 agent 系统协作时参考。本 doc §4.5 A2A 扩展位声明会引用此 URL。

**A2A 协议 URL(Google → Linux Foundation,供 v12+ 扩展位参考):** [deeplearning.ai/courses/a2a-the-agent2agent-protocol](https://www.deeplearning.ai/courses/a2a-the-agent2agent-protocol) —— A2A 协议由 Google Cloud 2025-04 启动,2025 年中捐给 Linux Foundation,Microsoft + Google + Salesforce 等背书(FEATURES §8.1 引用,HIGH 置信度)。v12+ 跨厂商协作时,A2A 是正确协议(不是 MCP,不是 Kimi 全 MCP shim)。

**Agent-MCP 项目 URL(Kimi 方案 close cousin,§2.4 引用):** [github.com/rinadelph/Agent-MCP](https://github.com/rindelph/Agent-MCP) —— Agent-MCP 是 FEATURES §7.1-§7.2 引用的社区项目,把多个 AI agent 通过 MCP 协调,核心卖点是「persistent knowledge graph + agent fleet management + 文件级 lock」。Kimi 方案的「full MCP shim」借鉴自 Agent-MCP 模式。本 doc §2.4 + §3.1 + §3.4 + §4.3 violation 1 引用。

**v11.0 PoC 实施者的 §4 总结:** §4 是 SC#4 的完整论证 —— T6 与 Microsoft 三层 100% align,v11.0 PoC 实施 `mcp_serve.py` 7 tool 扩展时不需要重新论证「为什么 MCP 是正确的协议层」,直接 cite §4.2 mapping table 即可。当 reviewer(Kai 或 Kimi 续聊)问「v10.0 协议层是否符合业界共识」,§4.4 + §4.6 是答案。



