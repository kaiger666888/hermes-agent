# FEATURES — 2026 Multi-Agent Orchestration Frameworks Landscape

> **Document status:** research-2026-07-06 · supersedes: none · superseded_by: TBD
> **Milestone:** v10.0 (Hermes-Agent 编排架构第一性原理推导,设计型)
> **Phase:** 44 of v10.0 design milestone
> **Mode:** Ecosystem research (comparison-flavored)
> **Audience:** v10.0 设计套件作者(Kai + Kimi + 未来 v11.0 PoC 实施者)
> **Reading time:** ~25 minutes(full)/ ~5 minutes(§0 + §7 + §8)
> **Stability:** `stable` for factual framework descriptions;`evolving` for "borrowable design points" sections(later design docs may refine)

---

## §0 — 阅读指南 / Scope

本文档是 v10.0 设计套件的 **FEATURES.md**,目标是对照 2026 年 7 月主流的 multi-agent orchestration frameworks,为 `00-FIRST-PRINCIPLES.md` / `01-AGENT-REGISTRY-SCHEMA.md` / `02-ROUND-TABLE-PROTOCOL.md` 提供业界模式调研底料。

### 范围声明

| 在范围内 | 不在范围 |
|---|---|
| 8 个主流 + 新兴 multi-agent 框架的 agent 定义格式 / memory 模式 / 协作模式 / 调度粒度 | 单 agent 框架(如 plain LangChain、vanilla Claude Code CLI) |
| MCP-based multi-agent 实践案例(Agent-MCP、Microsoft 多 agent 模式指引) | MCP 协议本身(由 `00-FIRST-PRINCIPLES.md` 单独覆盖) |
| 与 v10.0 设计决策的对照(7 个可借鉴设计点) | 实际代码改造(本里程碑零代码改动) |
| 2026 年的版本/API 表面验证(Context7 + 官方 docs) | 历史 / 已 EOL 框架版本 |

### 调研问题(每框架必答)

对每个框架,本文档给出 7 个对比轴的具体回答:

1. **agent 定义格式**:YAML / Python class / JSON / Markdown?
2. **per-agent memory**:原生支持?scope / persistence / 自进化机制?
3. **multi-agent 协作模式**:round table / graph / pipeline / market / role-playing?
4. **调度粒度**:turn-based / event-based / message-passing / handoff?
5. **工具/技能机制**:MCP / function calling / 自定义 RPC?
6. **与 CC / Claude 生态的兼容性**:可直连 / 需 shim?
7. **可借鉴到 v10.0 的具体设计点**(最重要)

### 框架清单(本调研覆盖)

| # | 框架 | 类型 | 调研优先级 |
|---|------|------|------------|
| 1 | **LangGraph + langgraph-supervisor** | 图编排 + 中心化 supervisor | ⭐⭐⭐⭐⭐ |
| 2 | **Microsoft Agent Framework (MAF)** | AutoGen + Semantic Kernel 的官方继任者(2026-04 GA) | ⭐⭐⭐⭐⭐ |
| 3 | **CrewAI** | YAML-first 角色定义 + Crew 任务编排 | ⭐⭐⭐⭐⭐ |
| 4 | **Anthropic Claude Agent SDK** | subagents + hooks + filesystem `.claude/agents/` | ⭐⭐⭐⭐⭐ |
| 5 | **OpenAI Swarm / Agents SDK** | 教育性 + handoff 模式 | ⭐⭐⭐⭐ |
| 6 | **Camel-AI** | Role-playing 双 agent 协商 | ⭐⭐⭐ |
| 7 | **MCP-based multi-agent (Agent-MCP)** | 用 MCP 做 agent-to-agent 通讯 | ⭐⭐⭐⭐⭐ |
| 8 | **A2A (Google → Linux Foundation)** | 跨厂商 agent-to-agent 协议 | ⭐⭐⭐⭐⭐ |

### 置信度声明

| 框架 | 置信度 | 主要来源 |
|------|--------|----------|
| LangGraph | HIGH | 官方 docs + langgraph-supervisor reference |
| MAF | HIGH | learn.microsoft.com + devblogs.microsoft.com 1.0 GA 公告 |
| CrewAI | HIGH | docs.crewai.com/v1.15.1 + GitHub repo |
| Claude Agent SDK | HIGH | code.claude.com 官方 docs(overview + subagents 页) |
| OpenAI Swarm | MEDIUM | GitHub repo + OpenAI community forum(框架仍标 experimental) |
| Camel-AI | MEDIUM | GitHub README + arXiv 2303.17760;2026 专属 docs 检索稀疏 |
| Agent-MCP | MEDIUM | GitHub README(社区项目,非厂商背书) |
| A2A | HIGH | learn.microsoft.com multi-agent-patterns + Google Cloud 启动文档 |

---

## §1 — LangGraph + langgraph-supervisor (LangChain 出品)

> **置信度:** HIGH · **主源:** [langchain.com/langgraph](https://www.langchain.com/langgraph), [docs.langchain.com/oss/python/langgraph/persistence](https://docs.langchain.com/oss/python/langgraph/persistence), [reference.langchain.com/python/langgraph-supervisor](https://reference.langchain.com/python/langgraph-supervisor)

### §1.1 — 框架定位

LangGraph 是 LangChain 团队推出的**低层级图编排框架**(low-level orchestration framework),把 multi-agent 系统建模为 **StateGraph**:

- **节点(node)** = agent / tool / decision function
- **边(edge)** = control flow(可条件化、可循环)
- **状态(state)** = 共享 schema(TypedDict / dataclass),流过整图

LangGraph 1.x 是当前稳定版(2026 多个教程引用 1.1),采用"框架的框架"定位 —— 它**不内置 agent 模板**,而是提供 graph + state + persistence 原语,让上层(如 langgraph-supervisor、langgraph-swarm)实现具体协作模式。

### §1.2 — 7 个对比轴

| 轴 | 回答 |
|---|---|
| **agent 定义格式** | **Python class / function**(`@node` 装饰器 + `StateGraph`),没有原生 YAML 格式;agent = 一个接收 state、返回 state patch 的函数 |
| **per-agent memory** | **双层原生支持**:(1) **Checkpointer**(短期,thread-scoped,`MemorySaver` / Redis / Postgres 后端,保存完整 graph state);(2) **Store / BaseStore**(长期,cross-thread,JSON 文档在 namespace + key 下)—— **每个 agent 用独立 namespace 即可实现 per-agent memory** |
| **multi-agent 协作模式** | 三种官方模式:(a) **Supervisor**(中心化 router,[langgraph-supervisor](https://reference.langchain.com/python/langgraph-supervisor) 库提供 `create_supervisor()` 帮手);(b) **Hierarchical supervisor(supervisor 嵌套 supervisor)**;(c) **Network / swarm**(去中心化,agent 之间直接 handoff) |
| **调度粒度** | **graph execution**:control flow 由 edge 决定,既不是 turn-based 也不是 event-based,而是**显式 graph walk**;支持 conditional edges、cycles、parallel branches |
| **工具/技能机制** | 通过 **LangChain tools**(`@tool` decorator)、function calling;**MCP 通过 `langchain-mcp-adapters` 接入**,把 MCP server 暴露为 LangChain tool |
| **与 CC 兼容性** | LangChain 自己跑 agent loop,**CC 不是一等公民**;可通过 MCP 做桥(LangGraph agent 暴露为 MCP server 给 CC 调用) |
| **2026 API 表面** | `StateGraph(StateSchema)`, `graph.add_node()`, `graph.add_edge()`, `graph.add_conditional_edges()`, `compile(checkpointer=..., store=...)`,`create_supervisor(agents=[...], model=...)` |

### §1.3 — Memory 模式深入(关键可借鉴点)

LangGraph 的**双层 memory 抽象**是业界最干净的:

```python
# 短期:checkpointer 保存 thread 内完整 state
graph = builder.compile(
    checkpointer=MemorySaver(),         # or PostgresSaver, RedisSaver
    store=InMemoryStore(),               # long-term, cross-thread
)

# 长期:Store 按 namespace 组织,可做 per-agent scope
store.put(namespace=("agents", "screenwriter", "session_42"),
          key="style_preferences",
          value={"tone": "noir", "pacing": "fast"})
```

**关键洞察:** LangGraph 的 Store 用 **namespace 元组**(tuple of strings)做层级隔离。每个 agent 拿 `(agents, <agent_id>, <scope>)` 作为自己的 namespace,即得 per-agent memory。**没有显式 curator**,但 Store 是公开 API,可写外部后台进程做整理。

### §1.4 — 可借鉴到 v10.0 的具体设计点

**B1.1 — Namespace 元组做 per-agent memory scope 的模式。**
v10.0 的 `~/.hermes/agents/{name}.agent.yaml` 应声明 `memory_scope` 字段,对应到 mem0 backend 的 namespace 元组(类比 LangGraph Store 的 `("agents", agent_id, project_or_session)`)。这给 v10.0 决策 #6(per-agent memory)提供了**具体存储拓扑参照**,不需要发明新概念。

**B1.2 — Checkpointer vs Store 的双层切分。**
v10.0 应显式区分:
- **Checkpointer-style**(短期):round table 进行中的 turn-by-turn state(Hermes `~/.hermes/roundtables/<rt_id>.json`)
- **Store-style**(长期):agent 跨项目经验(Hermes mem0 backend)
不要把两者混进一个存储(常见 anti-pattern,见 §9 PITFALL)。

**B1.3 — Supervisor 不是"协调员",是"路由器"。**
[langgraph-supervisor 文档](https://reference.langchain.com/python/langgraph-supervisor) 明确定义 supervisor 的职责是 **routing and delegation**,不是内容生产。这跟 v10.0 决策 #7(Hermes 控结构 / CC 控内容)高度同构 —— **Hermes 像 LangGraph supervisor(路由),CC 像 worker agent(干活)**。

**B1.4 — Hierarchical supervisor 模式可用 round table 嵌套。**
v10.0 `02-ROUND-TABLE-PROTOCOL.md` 应支持 round table 嵌套(顶层 round table 中某个 panelist 自己是一个子 round table 的召集人),与 LangGraph 的 hierarchical supervisors 同构。

---

## §2 — Microsoft Agent Framework (MAF):AutoGen + Semantic Kernel 的 2026-04 GA 继任者

> **置信度:** HIGH · **主源:** [learn.microsoft.com/en-us/agent-framework/overview](https://learn.microsoft.com/en-us/agent-framework/overview/), [devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/), [learn.microsoft.com/en-us/agents/architecture/multi-agent-patterns](https://learn.microsoft.com/en-us/agents/architecture/multi-agent-patterns)

### §2.1 — 框架定位(2026 年最重要的行业事件)

**Microsoft Agent Framework (MAF)** 是 2025-10 宣布、**2026-04-03 1.0 GA** 的统一框架,把 AutoGen(多 agent 对话编排)和 Semantic Kernel(企业级 plugin / function calling)**合并成单一 SDK**(.NET + Python 双语言)。AutoGen 不再演进,微软发布正式迁移指引。

> "Semantic Kernel and AutoGen pioneered the concepts of AI agents and multi-agent orchestration. The Agent Framework is the direct successor..." — [learn.microsoft.com/en-us/agent-framework/overview](https://learn.microsoft.com/en-us/agent-framework/overview/)

**对 v10.0 调研的含义:** AutoGen 0.2 的 `ConversableAgent` / `GroupChat` / `GroupChatManager` 概念仍是业界面熟的设计语言,但 v10.0 引用时必须改引 MAF 而非 AutoGen(否则显得过时)。

### §2.2 — 7 个对比轴(融合 AutoGen 历史概念 + MAF 现状)

| 轴 | 回答 |
|---|---|
| **agent 定义格式** | **Python / .NET class**(`AgentBase` 子类,带 `instructions` / `tools`);**没有官方 YAML 格式**,配置走代码 + Azure AI Foundry 资源模型 |
| **per-agent memory** | **不原生 per-agent**:MAF 提供 `ChatHistory` / `Aggregator` 抽象,memory 走外部 store(Azure AI Foundry thread、CosmosDB、自定义);需要应用层自己做 per-agent scope |
| **multi-agent 协作模式** | (AutoGen 经典)Two-agent chat / Sequential chat / **GroupChat**(用 `GroupChatManager` 选下一发言者)/ Nested chat;MAF 加入了 **AgentWorkflow** 编排器(类似 graph) |
| **调度粒度** | **Turn-based with manager**:GroupChatManager 决定每轮谁发言(自动或手动模式);agent 之间通过 message passing |
| **工具/技能机制** | Semantic Kernel 风格 **plugins**(函数组),function calling;**MCP 支持作为 first-class**(MAF 文档显式覆盖) |
| **与 CC 兼容性** | MAF 自己跑 loop,不直连 CC;**但 MAF 把 A2A 列为一等公民**(`AgentMetadata` / agent card),可被 A2A client 调用 |
| **2026 API 表面** | `Agent`, `AgentThread`, `AgentWorkflow`, `ChatHistoryAgent`(.NET + Python 同名);GroupChat 概念在 MAF 中以 `AgentWorkflow.add_agent()` + selection policy 表达 |

### §2.3 — GroupChat 的"selection policy"(关键可借鉴点)

AutoGen 0.2 的 GroupChatManager 的核心是 **`select_speaker` 逻辑**:
- `auto`(默认):LLM 看历史,选下一发言者
- `manual`:外部 caller 控制
- `round_robin` / 自定义 transition matrix

[AutoGen 0.2 agent_chat 文档](https://microsoft.github.io/autogen/0.2/docs/Use-Cases/agent_chat/) 还提到 **Finite State Machine 转移矩阵** 模式:用户喂一个有向 transition matrix,指定哪些 agent → agent 转移是合法的。这正是 v10.0 决策 #7 的 "Hermes 控 turn_order" 的工业级表达。

### §2.4 — 可借鉴到 v10.0 的具体设计点

**B2.1 — `turn_order` 既可以是 `auto`(LLM 决定)也可以是 `matrix`(FSM 转移矩阵)。**
v10.0 `02-ROUND-TABLE-PROTOCOL.md` 的 `turn_order` 字段应支持三种值:
- `"llm"`(默认,round table 召集人 LLM 决定)
- `"fixed:[a,b,c,a,b,c]"`(轮询)
- `"matrix"`(配合 transitions.yaml,指定合法转移)

这是直接借鉴 AutoGen GroupChat + LangGraph conditional edges 的设计。

**B2.2 — MAF 的"A2A 一等公民"立场验证了 v10.0 不依赖 A2A 是合理的。**
MAF 把 A2A 当作跨厂商集成接口(发布 agent card 让外部 A2A client 调用)。v10.0 是**单厂商内部**(Hermes + CC)的编排,**不需要 A2A**;用 MCP 做 Hermes↔CC 桥(决策 #1 T6)是更轻量、更稳定的选择。MAF 的立场反过来支持 v10.0 的取舍。

**B2.3 — GroupChat 的 "nested chat" 模式 = round table 嵌套。**
AutoGen 0.2 文档列出 "Nested chat like in conversational chess" 作为 group chat 的合法子模式。v10.0 应支持 `panelist.can_convene_subpanel = true`,让某 panelist 在自己回合内召集子 round table(类比 LangGraph hierarchical supervisor,见 B1.4)。

---

## §3 — CrewAI:YAML-first Role-Goal-Backstory + Crew 任务编排

> **置信度:** HIGH · **主源:** [docs.crewai.com/v1.15.1/en/concepts/agents](https://docs.crewai.com/v1.15.1/en/concepts/agents), [github.com/crewaiinc/crewai](https://github.com/crewaiinc/crewai)

### §3.1 — 框架定位

CrewAI 是**最高声量的"开箱即用"multi-agent 框架**,定位是 **role-playing autonomous AI agents that work together collaboratively**(GitHub 描述)。它把 agent / task / crew 三件事**都做成 YAML 一等公民**,是 v10.0 `α` 形态(YAML agent 定义)最直接的对照。

### §3.2 — 7 个对比轴

| 轴 | 回答 |
|---|---|
| **agent 定义格式** | **JSONC(新) / YAML(classic) / Python(三种都支持)**。新项目用 `agents/<name>.jsonc`(JSONC = JSON with comments),classic 项目用 `config/agents.yaml` + `@CrewBase` 装饰器自动加载 |
| **per-agent memory** | **agent 级 `memory: true` flag**(开箱 short-term conversation history);**crew 级 long-term memory**(跨 crew run,需要 embedder 配置);**没有显式 per-agent namespace**,memory scope 跟 agent instance 绑定 |
| **multi-agent 协作模式** | **Task-driven pipeline**(task list 顺序执行,每个 task 分配给 agent);agent 间通过 `allow_delegation: true` 做 delegation;**不是 round table**(无中心召集人,无多 agent 同回合协商) |
| **调度粒度** | **Task-based**:crew 按任务列表推进,每个 agent 完成自己 task 后传给下一个;不是 turn-based,也不是 event-based |
| **工具/技能机制** | `tools: [BaseTool]`(CrewAI Toolkit 或 LangChain Tools);**MCP 没有原生一等支持**(2026-07 仍需通过 LangChain tool 桥接) |
| **与 CC 兼容性** | CrewAI 自己跑 loop,不直连 CC |
| **2026 API 表面** | `Agent(role, goal, backstory, llm, tools, ...)`,`Task(description, expected_output, agent)`,`Crew(agents, tasks, process=Process.sequential \| hierarchical)` |

### §3.3 — Agent YAML schema(关键可借鉴点)

CrewAI 1.15.1 的 `agents/<name>.jsonc` 完整字段(节选自官方 docs):

```jsonc
{
  "role": "{topic} Senior Data Researcher",
  "goal": "Uncover cutting-edge developments in {topic}",
  "backstory": "You find the most relevant information and present it clearly.",
  "llm": "openai/gpt-4o",
  "tools": ["SerperDevTool"],
  "settings": {
    "verbose": true,
    "allow_delegation": false,
    "max_iter": 20,
    "memory": true,
    "respect_context_window": true,
    "reasoning": false,
    "knowledge_sources": []
  }
}
```

字段非常多(30+ 项),包括:
- **身份三件套:** `role` / `goal` / `backstory`(CrewAI 的招牌)
- **执行控制:** `max_iter` / `max_rpm` / `max_execution_time` / `max_retry_limit`
- **memory & context:** `memory` / `respect_context_window`(超 window 自动摘要) / `knowledge_sources`(domain knowledge)
- **reasoning:** `reasoning: true` + `max_reasoning_attempts`(先 plan 再 act)
- **协作:** `allow_delegation`(可委托他人)
- **specialization:** `multimodal` / `inject_date` / `code_execution_mode: "safe" | "unsafe"`

### §3.4 — 可借鉴到 v10.0 的具体设计点

**B3.1 — CrewAI 的 `role/goal/backstory` 三件套太薄,v10.0 应保留并扩展。**
v10.0 决策 #5 的 agent YAML schema 应把 CrewAI 三件套当作**最小必需**(`persona.role` / `persona.goal` / `persona.backstory`),但 v10.0 在此之上加:
- `persona.expertise_summary`(RAG-aware 的领域知识摘要,从 refs 自动派生)
- `persona.dos_and_donts`(明确边界,类比 system prompt 的 do/don't 段)
- `lineage`(从哪些 v9 skills / v2 节点 / 行业经验抽出,来源可追溯)

**B3.2 — CrewAI 的 `max_iter` / `max_rpm` / `max_execution_time` 三件套是好的"执行护栏"。**
v10.0 agent YAML 应有 `execution_limits` 子段:
```yaml
execution_limits:
  max_turns: 20      # 单次 agent 调用最大循环
  max_rounds: 6      # 在一个 round table 中最多发言几轮
  timeout_sec: 600   # 硬超时
```

**B3.3 — CrewAI 的 `memory: true` flag 不够,v10.0 必须做 namespace-scoped memory。**
CrewAI 的 agent memory 是 boolean(`memory: true`),没有 namespace 概念,memory 跨 agent 可能串扰。v10.0 决策 #6 要求 per-agent memory,**借鉴 LangGraph Store 的 namespace 模式**(B1.1),不是 CrewAI 的 boolean flag。

**B3.4 — CrewAI 的 `respect_context_window: true` 是必备。**
v10.0 agent YAML 应有 `context_management.respect_window: true`,超 window 时触发 Hermes 现有的 `ContextCompressor`(`agent/context_compressor.py`)。这是与 hermes-agent 现有架构对齐的关键。

**B3.5 — CrewAI 不是 round table,是 task pipeline。v10.0 不要抄它的协作模式。**
CrewAI 没有"多 agent 同时讨论同一个问题"的原语,只有"任务在 agent 之间流转"。v10.0 的 round table 概念应从 AutoGen GroupChat(§2)和 LangGraph network(§1)借鉴,**不**从 CrewAI 借鉴。CrewAI 的 crew 模式适合 v10.0 的 fallback 形态(顺序 pipeline,而非协商)。

---

## §4 — Anthropic Claude Agent SDK:subagents + hooks + filesystem agents

> **置信度:** HIGH · **主源:** [code.claude.com/docs/en/agent-sdk/overview](https://code.claude.com/docs/en/agent-sdk/overview), [code.claude.com/docs/en/agent-sdk/subagents](https://code.claude.com/docs/en/agent-sdk/subagents)

### §4.1 — 框架定位

Claude Agent SDK 是 Anthropic 把 Claude Code 的内部基础设施**作为库暴露**的官方 SDK(Python + TypeScript),2026 年位于 [code.claude.com/docs/en/agent-sdk](https://code.claude.com/docs/en/agent-sdk/overview)。它**不是 multi-agent 框架**(强调:它不内置 GroupChat / Crew 概念),但提供两个核心原语:**subagents**(分工)和 **hooks**(生命周期拦截)。

### §4.2 — 7 个对比轴

| 轴 | 回答 |
|---|---|
| **agent 定义格式** | **三选一**:(a) **Programmatic**(`AgentDefinition` Python dataclass);(b) **Filesystem-based**(`.claude/agents/<name>.md` Markdown + YAML frontmatter);(c) **Built-in**(`general-purpose` 默认可用)。**v10.0 关注 filesystem 形态,因为这是 Kimi 方案用的形态** |
| **per-agent memory** | **`memory` 字段**(`'user' \| 'project' \| 'local'`),决定 agent 从哪个 CLAUDE.md / 设置源加载 memory;**subagent 默认不继承父对话历史**(context isolation);**subagent 有独立 session 文件**,parent compaction 不影响 subagent transcript |
| **multi-agent 协作模式** | **不原生支持 multi-agent**。Claude 自己作为 main agent,可调 `Agent` tool 派生 subagent 做子任务,subagent 返回 final message;**不是 round table**(无多 subagent 互发言) |
| **调度粒度** | **Tool-call dispatch**:main agent 通过 `Agent` tool 显式调用 subagent;v2.1.198+ subagent 默认 background,可并发 |
| **工具/技能机制** | **MCP 是一等公民**(`mcp_servers` 配置);`tools` 字段限定 agent 可用工具;subagent 可继承父工具集 |
| **与 CC 兼容性** | **完全原生**(就是 CC 的库形态);通过 `permissionMode` 控制权限 |
| **2026 API 表面** | `query(prompt, options=ClaudeAgentOptions(...))`,`ClaudeAgentOptions(allowed_tools, agents, hooks, mcp_servers, ...)`;`AgentDefinition(description, prompt, tools, model, memory, mcpServers, maxTurns, background, effort)` |

### §4.3 — Subagent 关键细节(关键可借鉴点 / 关键"否决点")

从 [subagents docs](https://code.claude.com/docs/en/agent-sdk/subagents) 提取的**v10.0 必须知道的事实**:

1. **Subagent 默认 context-isolated**:"The only channel from parent to subagent is the Agent tool's prompt string"。这意味着 **subagent 不天然适合做 round table panelist**(panelist 需要看完整历史)。
2. **`memory` 字段限定 source**:`'user'` / `'project'` / `'local'`,**不是 namespace scoped memory**(对比 LangGraph Store 的 namespace 元组,这弱很多)。
3. **Subagent transcripts 持久化在独立文件**,main conversation compaction 不影响 subagent;30 天后自动清理。
4. **`Workflow` tool**(TypeScript SDK v0.3.149+)用于"协调几十到几百个 agent"的大规模编排,超出 turn-by-turn subagent delegation 的范畴。

### §4.4 — 可借鉴到 v10.0 的具体设计点

**B4.1 — Claude Agent SDK 的 `AgentDefinition` 是 Kimi 方案用的形态,v10.0 必须显式拒绝。**
Kimi 方案 2.0 把 Expert 写成 `.claude/agents/<name>.md`(filesystem-based subagent)。**v10.0 决策:** 这恰好是 v10.0 要否决的形态(决策 #5 / #7)。理由(从官方 docs 提取):
- Subagent **default context-isolated** → 不适合 round table panelist
- Subagent **memory 字段不是 namespace scoped** → 不能做 per-agent 自进化 memory
- Subagent **transcripts 30 天自动清理** → 跨项目经验持久化不稳定

v10.0 应在 `00-FIRST-PRINCIPLES.md` 显式引用 Claude Agent SDK subagent docs 作为"为什么 agent 不应该塞进 CC"的反例。

**B4.2 — `hooks` 模式可借鉴用于 v10.0 的"审计钩子"。**
Claude Agent SDK 的 hooks(`PreToolUse`, `PostToolUse`, `Stop`, `SessionStart`, `SessionEnd`)是**生命周期拦截器**模式。v10.0 round table 协议可在每个回合前后插入 hook(类比 `PreTurn` / `PostTurn`),用于:审计日志、token cost 累计、early-stop-rule 检查、redline 检查。

**B4.3 — `effort: 'low' | 'medium' | 'high' | 'xhigh' | 'max'` 是好的 agent 级 reasoning 控制。**
v10.0 agent YAML 应有 `reasoning_effort` 字段,让重要 agent(如 screenplay / cinematographer)用 `high` / `xhigh`,辅助 agent(如 glossary checker)用 `low`。这是与 GLM/Claude 的 reasoning_effort 参数对齐的低成本设计。

**B4.4 — `Workflow` tool 的"超大规模编排"模式超出 v10.0 v1 范围,但应在 `05-POC-PLAN.md` 标记为 v12+ 候选。**
Workflow tool 适合"几十到几百个 agent",v10.0 的 round table(5-7 panelists)用 subagent delegation 即可。但 Workflow tool 是未来扩展音乐视频 / 长 form 时(多场景并行,几十个 agent)的候选。

---

## §5 — OpenAI Swarm / Agents SDK:handoff 模式

> **置信度:** MEDIUM(Swarm 仍标 experimental)· **主源:** [github.com/openai/swarm](https://github.com/openai/swarm), [community.openai.com/t/openai-swarm-for-agents-and-agent-handoffs](https://community.openai.com/t/openai-swarm-for-agents-and-agent-handoffs/976579)

### §5.1 — 框架定位

OpenAI Swarm 是 2024-10 发布的**教育性 / 实验性**轻量框架,2026-07 仍标 "educational"(非生产)。它的核心概念是 **handoff function**:agent A 通过返回一个指向 agent B 的函数,把对话"交给"agent B。**OpenAI Agents SDK** 是其生产化继任(2025-2026 主推),但 Swarm 仍是社区教学参照。

### §5.2 — 7 个对比轴(Swarm 视角)

| 轴 | 回答 |
|---|---|
| **agent 定义格式** | **Python class / dataclass**(`Agent(name, instructions, functions)`);没有原生 YAML 格式 |
| **per-agent memory** | **几乎没有**:Swarm 维护单一 conversation context,handoff 时 context 跟着走,**没有 per-agent namespace**;这正是 Swarm 的"轻量"代价 |
| **multi-agent 协作模式** | **Handoff-based**:agent 通过 function call 把控制权交给另一个 agent;"only the last handoff function will be used"(多 handoff 并发不被支持) |
| **调度粒度** | **Client-side turn-based**:几乎全在 client,server 只做 LLM 调用 |
| **工具/技能机制** | Python functions 自动转 function schema;**MCP 不原生支持**(2026-07) |
| **与 CC 兼容性** | 不兼容(Swarm 是 OpenAI-only) |
| **2026 API 表面** | `Agent(name, instructions, functions)`,`run(agent, messages)`;handoff function 返回 `Agent` 实例 |

### §5.3 — 可借鉴到 v10.0 的具体设计点

**B5.1 — Handoff 是"控制权移交",不是"协商"。v10.0 不要用 handoff 做 round table。**
Swarm 适合做**串行专家接力的客服场景**(客户进来 → triage agent → billing agent → close),不适合多专家同台讨论。v10.0 的 round table 是协商场景,**handoff 模式是反面教材**。

**B5.2 — Swarm 的"轻量"哲学可借鉴用于 v10.0 的 fallback 形态。**
当 round table 不必要(单 agent 即可解决)时,v10.0 应有"handoff-style"快速路径:agent A 调用 agent B(通过 MCP tool),B 返回 final answer,A 继续。这是 v10.0 的 `fallback_pipeline` 形态(顺序而非协商)。

---

## §6 — Camel-AI:Role-playing 双 agent 协商

> **置信度:** MEDIUM · **主源:** [github.com/camel-ai/camel](https://github.com/camel-ai/camel), [arxiv.org/abs/2303.17760](https://arxiv.org/abs/2303.17760), [docs.camel-ai.org/cookbooks/basic_concepts/create_your_first_agents_society](https://docs.camel-ai.org/cookbooks/basic_concepts/create_your_first_agents_society)

### §6.1 — 框架定位

Camel-AI 是**最早**的 multi-agent role-playing 框架(2023 论文 [arxiv 2303.17760](https://arxiv.org/abs/2303.17760)),核心抽象是 **`RolePlaying()`**:一个 user-agent(提任务) + 一个 assistant-agent(执行),通过多轮协商解决任务。它的研究重点是 **scaling laws of agents**(大规模 agent society 的涌现行为)。

### §6.2 — 7 个对比轴

| 轴 | 回答 |
|---|---|
| **agent 定义格式** | **Python class**(`ChatAgent`),配置走代码;近期支持部分 YAML 但不是 first-class |
| **per-agent memory** | `ChatAgent.memory` 维护对话历史;**长期 memory 通过外部 vector DB**(CAMEL 集成多家) |
| **multi-agent 协作模式** | **Role-playing 双 agent** 是招牌;后续扩展到 `RolePlayingWithCritics` / `Society` 模式(多 agent) |
| **调度粒度** | **Turn-based message exchange**:每轮 user-agent 发,assistant-agent 回,直到 task complete |
| **工具/技能机制** | function calling + CAMEL Toolkit;**MCP 通过社区适配器支持** |
| **与 CC 兼容性** | 不兼容 |
| **2026 API 表面** | `RolePlaying(initiate_agent, assistant_agent, task_prompt, ...)`,`step()` 推进一轮 |

### §6.3 — 可借鉴到 v10.0 的具体设计点

**B6.1 — "Role-playing as primary mode" 不适合 v10.0 的多 panelist 场景,但 "critic" 子模式可借鉴。**
Camel 的 `RolePlayingWithCritics` 让一个 generator agent + 多个 critic agent 协商。这与 v10.0 round table 中"主创 agent + 多审核门 agent"的结构同构。v10.0 可在 `02-ROUND-TABLE-PROTOCOL.md` 定义 `panelist_role: "generator" | "critic" | "synthesizer"`,借鉴 Camel 的 critic 模式。

**B6.2 — Camel 的 task-completion 检测可用作 v10.0 early_stop_rule 的参考。**
Camel 用 LLM-as-judge 检测 "task complete",触发对话终止。v10.0 的 `early_stop_rule` 字段可支持 `task_complete_judge: true`,让一个独立的 judge agent 在每回合后判断是否已达成 round table 目标。

---

## §7 — MCP-based multi-agent patterns(Agent-MCP + Microsoft 指引)

> **置信度:** MEDIUM(Agent-MCP 是社区项目)/ HIGH(Microsoft multi-agent-patterns 是官方指引)· **主源:** [github.com/rinadelph/Agent-MCP](https://github.com/rindelph/Agent-MCP), [learn.microsoft.com/en-us/agents/architecture/multi-agent-patterns](https://learn.microsoft.com/en-us/agents/architecture/multi-agent-patterns), [arxiv.org/html/2504.21030v1](https://arxiv.org/html/2504.21030v1)

### §7.1 — 模式定位

**MCP-based multi-agent** 不是单一框架,而是 2025-2026 年兴起的**架构模式**:用 MCP(Model Context Protocol,Anthropic 2024-11 推出的开放标准)同时做 (a) agent ↔ tool 通讯,(b) agent ↔ agent 通讯。代表性实现:

- **Agent-MCP**([github.com/rinadelph/Agent-MCP](https://github.com/rinadelph/Agent-MCP)):开源框架,把多个 AI agent 通过 MCP 协调,核心卖点是"persistent knowledge graph + agent fleet management + 文件级 lock"。
- **Microsoft 多 agent 模式指引**([learn.microsoft.com/.../multi-agent-patterns](https://learn.microsoft.com/en-us/agents/architecture/multi-agent-patterns)):官方推荐"prefer platform-native orchestration for internal flows, MCP for tool access, A2A for cross-platform"。

### §7.2 — Agent-MCP 的 7 个对比轴

| 轴 | 回答 |
|---|---|
| **agent 定义格式** | **运行时定义**(通过 `create_agent` MCP tool,role + specialization 字符串);**没有静态 YAML** |
| **per-agent memory** | **共享 knowledge graph**(RAG-over-MCP);**agent 级短暂记忆**(60 秒 idle 即杀);**长期 memory 集中在项目级 graph** |
| **multi-agent 协作模式** | **Admin agent + worker agents**(hub-and-spoke);worker 通过 MCP tool 调用 admin;**短命 agent**(single task,完成即销毁);文件级 lock 防冲突 |
| **调度粒度** | **MCP tool call**:admin agent 调 `assign_task`、`create_agent`、`query_project_context` 等 MCP tool |
| **工具/技能机制** | **MCP 一等公民**(就是 MCP server) |
| **与 CC 兼容性** | **完全兼容**(设计目标就是 Claude Code / Cursor) |
| **2026 API 表面** | MCP tools:`create_agent`, `assign_task`, `view_tasks`, `update_task_status`, `ask_project_rag`, `send_agent_message`, `broadcast_message` |

### §7.3 — Microsoft multi-agent-patterns 的官方分层(关键可借鉴点)

[Microsoft 指引](https://learn.microsoft.com/en-us/agents/architecture/multi-agent-patterns) 明确给出**协议分层**:

> - **Platform-native orchestration** for internal flows(平台原生,最低成本)
> - **MCP** for tool and data access(MCP 做 agent ↔ tool)
> - **A2A** for cross-platform agent-to-agent messaging(A2A 做 agent ↔ agent,跨厂商)

并给出 MCP vs A2A 选择表(节选):

| 能力 | MCP | A2A |
|------|-----|-----|
| Multimodality | 需 host 支持 | 显式 advertisement |
| Multi-turn interactions | host 持 context | `contextId` 跨 agent |
| Orchestration | host orchestrate | invoked agent 自己 reason |
| Negotiation | client 更新才支持 | 动态 negotiation |

### §7.4 — 可借鉴到 v10.0 的具体设计点

**B7.1 — Microsoft 的"三层协议"分层直接验证了 v10.0 决策 #1 (T6)。**
v10.0 决策 #1 选 "Hermes MCP server + tmux dispatch + CC native MCP client"。这跟 Microsoft 推荐的"internal flow → platform-native(Hermes); tool access → MCP; cross-platform → A2A(不需要)"**完全一致**。v10.0 不需要 A2A,因为 Hermes 和 CC 是单厂商内部协作。

**B7.2 — Agent-MCP 的"短命 agent + 共享 knowledge graph"模式是 v10.0 的反面教材。**
Agent-MCP 主张 agent 完成任务即销毁,context 集中在项目级 graph。**v10.0 决策 #6 (per-agent memory + curator 自进化)正好相反** —— agent 应该是**长生命周期**的(per-project memory 跨项目积累)。v10.0 应在 `00-FIRST-PRINCIPLES.md` 引用 Agent-MCP 作为"短命 agent 模式"的反例,解释为什么 v10.0 选长生命周期。

**B7.3 — Agent-MCP 的"文件级 lock"机制可借鉴用于 v10.0 多 agent 并行编辑场景。**
v10.0 决策 #3 (D2)支持"跨场景并行"(多 agent 同时处理不同 scene)。Agent-MCP 的文件级 lock(`Agent requests file access → check lock → if locked, wait or pick other task`)是成熟的并发控制模式。v10.0 `02-ROUND-TABLE-PROTOCOL.md` 应有 `asset_locks` 子模式:同一时间只有一个 agent 能改 `scene_05/storyboard.json`。

**B7.4 — Microsoft 的"A2A 用于跨厂商"立场给 v10.0 v12+ 留扩展位。**
v10.0 不需要 A2A,但 `06-CROSS-REPO-IMPACT.md` 应记录:若未来 hermes-agent 要和外部 agent(如 Kai 的另一个项目)协作,A2A 是正确的协议,不是 MCP。

---

## §8 — A2A 协议(Google → Linux Foundation)

> **置信度:** HIGH · **主源:** [learn.microsoft.com/en-us/agents/architecture/multi-agent-patterns](https://learn.microsoft.com/en-us/agents/architecture/multi-agent-patterns), [deeplearning.ai/courses/a2a-the-agent2agent-protocol](https://www.deeplearning.ai/courses/a2a-the-agent2agent-protocol)

### §8.1 — 协议定位

A2A(Agent2Agent Protocol)是 Google Cloud 2025-04 启动、**捐给 Linux Foundation** 的开放标准,专门做**跨厂商 agent-to-agent 通讯**。与 MCP 形成互补:

- **MCP**:agent ↔ tool / data(纵向)
- **A2A**:agent ↔ agent(横向)

核心概念:
- **Agent Card**:每个 agent 发布 JSON 描述自己的 capabilities、endpoint、auth
- **Task**:有生命周期的协作单元(submitted / working / input-required / completed / failed)
- **Artifact**:task 产出(可以是 multimodal)
- **contextId**:跨多 turn 的 context 标识

### §8.2 — 7 个对比轴

| 轴 | 回答 |
|---|---|
| **agent 定义格式** | **Agent Card**(JSON,通过 URL 发布) |
| **per-agent memory** | 不在协议范围(memory 由各 agent 自己实现) |
| **multi-agent 协作模式** | **Task-based peer coordination**:discovery → invoke → task lifecycle → artifact |
| **调度粒度** | **Message-passing**(HTTP / SSE / webhook) |
| **工具/技能机制** | Agent 自己处理;A2A 只关心 agent-to-agent |
| **与 CC 兼容性** | 暂无(CC 不原生支持 A2A client) |
| **2026 状态** | Linux Foundation 治理,微软 + Google + Salesforce 等背书 |

### §8.3 — 可借鉴到 v10.0 的具体设计点

**B8.1 — Agent Card 概念可借鉴,但 v10.0 不需要 A2A 协议层。**
v10.0 的 agent YAML 应有 `agent_card` 子段(类比 A2A Agent Card),描述 capabilities / inputs / outputs,用于 round table panelist 自动匹配。**但传输层用 MCP(决策 #1),不用 A2A** —— 因为 v10.0 是单厂商内部。

**B8.2 — Task lifecycle 状态机可借鉴用于 round table turn 状态。**
A2A 的 task 状态机(submitted → working → input-required → completed / failed)是工业级标准。v10.0 round table 的每个 turn 可借用:`turn_status: pending \| speaking \| waiting_input \| done \| failed`。

**B8.3 — A2A 是 v12+ 的扩展位,不是 v10.0 的依赖。**
若 Kai 未来想让 hermes-agent 与外部 agent 系统协作,A2A 是正确协议。v10.0 应在 `06-CROSS-REPO-IMPACT.md` 记录这一扩展位,但**不在 v10.0 设计 A2A 接入**。

---

## §9 — 业界模式横向对比(7 轴速查表)

### §9.1 — Agent 定义格式速查

| 框架 | 主格式 | YAML 一等? | 备注 |
|------|--------|------------|------|
| **LangGraph** | Python 函数(`@node`) | 否 | graph = stateful function composition |
| **MAF** | Python / .NET class | 否 | 配置走代码 + Azure 资源模型 |
| **CrewAI** | JSONC(新)/ YAML(classic)/ Python | **是** | agents.yaml 是经典形态;新项目走 JSONC |
| **Claude Agent SDK** | Markdown + YAML frontmatter / Python dataclass | **半**(filesystem 形态) | `.claude/agents/<name>.md` |
| **OpenAI Swarm** | Python class | 否 | 教育性 |
| **Camel-AI** | Python class | 否 | 早期无 YAML |
| **Agent-MCP** | 运行时字符串 | 否 | 通过 MCP tool 创建 |
| **A2A** | JSON Agent Card | 是 | 但只描述 capability,不描述 persona |
| **v10.0 α 形态(目标)** | **YAML** | **是** | 借鉴 CrewAI + Claude Agent SDK filesystem,但更丰富(persona + memory_scope + lineage) |

### §9.2 — Memory 模式速查

| 框架 | 短期 | 长期 | Per-agent scope? | Curator / 自进化? |
|------|------|------|------------------|---------------------|
| **LangGraph** | Checkpointer | Store(BaseStore + namespace 元组) | ✅ 通过 namespace 元组 | ❌(需自己写后台) |
| **MAF** | ChatHistory / Thread | 外部 store | ❌ 需应用层自做 | ❌ |
| **CrewAI** | agent `memory: true` | crew-level + embedder | ❌ boolean flag | ❌ |
| **Claude Agent SDK** | session JSONL | filesystem(`memory: 'user'\|'project'\|'local'`) | ❌ 弱(source-scoped 非 agent-scoped) | ❌ |
| **OpenAI Swarm** | single context | ❌ | ❌ | ❌ |
| **Camel-AI** | `ChatAgent.memory` | vector DB | 部分 | ❌ |
| **Agent-MCP** | 60s idle 短命 agent | 项目级 knowledge graph | ❌(项目级共享)| 部分(graph GC) |
| **v10.0 目标** | round table JSON | mem0 backend + namespace | ✅ per-agent namespace | ✅ curator-driven |

**关键发现:** **没有一个主流框架把 per-agent scoped memory + curator-driven 自进化作为原生组合**。LangGraph 提供了 namespace(但需自写 curator);CrewAI / Claude Agent SDK 在 memory 维度都比 v10.0 弱。**v10.0 的决策 #6 是真正的差异化设计点**,不是"业界已普遍在做的事"。

### §9.3 — 协作模式速查

| 框架 | 模式 | 谁控结构? | 谁控内容? | 适合 round table? |
|------|------|-----------|-----------|---------------------|
| **LangGraph** | graph + supervisor | 开发者(graph topology) | worker agent | ✅ supervisor 变体可做 |
| **MAF (AutoGen)** | GroupChat + GroupChatManager | manager(`select_speaker`) | agents | ✅ **最贴近 round table** |
| **CrewAI** | task pipeline | crew 配置 | agents | ❌(无协商,只有 task 流转) |
| **Claude Agent SDK** | tool-call dispatch(subagent) | main agent | subagent | ❌(subagent 不互见) |
| **OpenAI Swarm** | handoff | client | current agent | ❌(串行,非协商) |
| **Camel-AI** | role-playing 2-agent | implicit | both | 部分(双 agent 太少) |
| **Agent-MCP** | admin + workers | admin agent | workers | ❌(hub-spoke,非圆桌) |
| **A2A** | task lifecycle | requester | invoked | N/A(协议层) |
| **v10.0 目标** | round table + 嵌套 | **Hermes**(turn_order / matrix) | **CC**(question framing / synthesis) | ✅ |

**关键发现:** **AutoGen GroupChat 是 v10.0 round table 的最直接对照**。CrewAI 不是 round table(是 pipeline),Claude Agent SDK 不是 round table(是 dispatch),Agent-MCP 不是 round table(是 hub-spoke)。v10.0 `02-ROUND-TABLE-PROTOCOL.md` 的首要借鉴对象是 **AutoGen GroupChat + LangGraph supervisor 的 hybrid**。

---

## §10 — 综合:可借鉴设计点汇总(给下游设计文档的索引)

下表把 §1-§8 的 "B*.x" 借鉴点汇总,标注它们分别喂给哪个 v10.0 设计文档:

| 借鉴点 ID | 来自框架 | 设计点 | 喂给文档 |
|-----------|----------|--------|----------|
| B1.1 | LangGraph | namespace 元组做 per-agent memory scope 拓扑 | `01-AGENT-REGISTRY-SCHEMA.md` |
| B1.2 | LangGraph | Checkpointer(短期)vs Store(长期)双层切分 | `00-FIRST-PRINCIPLES.md` |
| B1.3 | LangGraph | supervisor 是路由器,不是协调员 | `00-FIRST-PRINCIPLES.md`(决策 #7 推导) |
| B1.4 | LangGraph | hierarchical supervisor → round table 嵌套 | `02-ROUND-TABLE-PROTOCOL.md` |
| B2.1 | AutoGen / MAF | `turn_order` 三态(llm / fixed / matrix) | `02-ROUND-TABLE-PROTOCOL.md` |
| B2.2 | MAF | "A2A 一等公民"立场验证 v10.0 不依赖 A2A | `03-COMPARISON-VS-KIMI-MCP-SHIM.md` |
| B2.3 | AutoGen | nested chat → panelist 召集子 round table | `02-ROUND-TABLE-PROTOCOL.md` |
| B3.1 | CrewAI | role/goal/backstory 三件套是必需,v10.0 在此之上扩展 | `01-AGENT-REGISTRY-SCHEMA.md` |
| B3.2 | CrewAI | max_iter / max_rpm / timeout 三件套执行护栏 | `01-AGENT-REGISTRY-SCHEMA.md` |
| B3.3 | CrewAI | `memory: true` 不够,必须 namespace scoped | `00-FIRST-PRINCIPLES.md`(决策 #6 推导) |
| B3.4 | CrewAI | `respect_context_window` 必备,对齐 hermes ContextCompressor | `01-AGENT-REGISTRY-SCHEMA.md` |
| B3.5 | CrewAI | crew 不是 round table(反面教材) | `02-ROUND-TABLE-PROTOCOL.md` |
| B4.1 | Claude Agent SDK | subagent 形态 = Kimi 方案 = 必须显式否决 | `00-FIRST-PRINCIPLES.md`(决策 #5 推导) |
| B4.2 | Claude Agent SDK | hooks 生命周期拦截 → round table PreTurn/PostTurn | `02-ROUND-TABLE-PROTOCOL.md` |
| B4.3 | Claude Agent SDK | `effort: low\|medium\|high\|xhigh\|max` agent 级 reasoning | `01-AGENT-REGISTRY-SCHEMA.md` |
| B4.4 | Claude Agent SDK | `Workflow` tool 是 v12+ 大规模编排候选 | `05-POC-PLAN.md` |
| B5.1 | OpenAI Swarm | handoff 是控制权移交,不是协商(反面教材) | `02-ROUND-TABLE-PROTOCOL.md` |
| B5.2 | OpenAI Swarm | handoff 哲学可用于 v10.0 fallback 顺序 pipeline | `02-ROUND-TABLE-PROTOCOL.md` |
| B6.1 | Camel-AI | generator + critics 模式 → `panelist_role` 字段 | `02-ROUND-TABLE-PROTOCOL.md` |
| B6.2 | Camel-AI | task_complete_judge → `early_stop_rule` 字段 | `02-ROUND-TABLE-PROTOCOL.md` |
| B7.1 | MS 指引 | 三层协议分层(platform / MCP / A2A)验证 T6 | `03-COMPARISON-VS-KIMI-MCP-SHIM.md` |
| B7.2 | Agent-MCP | "短命 agent + 共享 graph" = v10.0 反面教材 | `00-FIRST-PRINCIPLES.md`(决策 #6 推导) |
| B7.3 | Agent-MCP | 文件级 lock → v10.0 多 agent 并行 asset_locks | `02-ROUND-TABLE-PROTOCOL.md` |
| B7.4 | MS 指引 | A2A 是 v12+ 跨厂商扩展位 | `06-CROSS-REPO-IMPACT.md` |
| B8.1 | A2A | Agent Card 概念借鉴(不用 A2A 协议层) | `01-AGENT-REGISTRY-SCHEMA.md` |
| B8.2 | A2A | Task lifecycle 状态机 → turn 状态 | `02-ROUND-TABLE-PROTOCOL.md` |
| B8.3 | A2A | A2A 是 v12+ 扩展位,不在 v10.0 范围 | `06-CROSS-REPO-IMPACT.md` |

---

## §11 — Anti-Features:业界流行但 v10.0 显式拒绝的模式

借鉴 CrewAI 的 "Anti-Features" 表风格,以下是 v10.0 **显式不抄业界**的选择:

| 业界模式 | 出处 | v10.0 拒绝理由 | v10.0 替代 |
|----------|------|----------------|------------|
| **Subagent 作为 agent 容器** | Claude Agent SDK `.claude/agents/*.md` | subagent context-isolated,memory 弱,30 天清理 | Hermes-side YAML agent(`~/.hermes/agents/`) |
| **短命 agent** | Agent-MCP "agent 完成即销毁" | 违反"agent 随项目越多越有经验"核心诉求 | 长生命周期 agent + per-agent memory |
| **Handoff 作 round table 替代** | OpenAI Swarm | handoff 是串行控制权移交,不是协商 | 真正的 round table(AutoGen GroupChat 风格) |
| **Crew task pipeline 作协商** | CrewAI Crew | crew 是顺序任务,无多 agent 同回合 | round table with turn_order |
| **A2A 跨厂商协议** | Google A2A | v10.0 是单厂商内部,无需跨厂商 | Hermes MCP server + CC native client |
| **`memory: true` boolean** | CrewAI | 不够细,无 per-agent namespace | namespace-scoped mem0 backend |
| **CrewAI 30+ 字段全抄** | CrewAI | 字段太多,维护成本高 | 抄 5-7 个核心字段(role/goal/backstory + max_turns/timeout + memory_scope) |

---

## §12 — 表中表 / Stakes vs Differentiators(为 02-ROUND-TABLE-PROTOCOL 提供)

参考 FEATURES.md 模板的"Table Stakes vs Differentiators"结构:

### §12.1 — Table Stakes(agent YAML 必备字段,业界共识)

| 字段 | 出处 | v10.0 必须支持 |
|------|------|----------------|
| `name` / `description` | 所有框架 | ✅ |
| `role` / `goal` / `backstory`(或等价 persona) | CrewAI 招牌 | ✅(在 `persona.*` 下) |
| `tools` / `function_calling` | 所有框架 | ✅ |
| `model` | CrewAI / Claude Agent SDK | ✅ |
| `max_turns` / `max_iter` | CrewAI / Claude Agent SDK | ✅(在 `execution_limits.*` 下) |
| `memory`(任何形态) | 所有框架 | ✅(但 v10.0 选 namespace scoped) |

### §12.2 — Differentiators(v10.0 独有,业界没有原生组合)

| 字段 / 概念 | 业界最接近的 | v10.0 的差异化 |
|-------------|--------------|----------------|
| `memory_scope`(namespace 元组) | LangGraph Store namespace | v10.0 把它和 agent YAML 绑定(LangGraph 是手动应用) |
| `lineage`(从哪些 skills / v2 nodes 抽出) | **无业界先例** | v10.0 独创,支持溯源审计 |
| `curator-driven` 自进化 | LangGraph "需要自己写后台" | v10.0 复用 hermes-agent `agent/curator.py`(v6.0 已 ship) |
| `panelist_role: generator\|critic\|synthesizer` | Camel-AI critics 模式 | v10.0 把它放进 round table 协议(不止 2 agent) |
| `turn_order: llm\|fixed\|matrix` | AutoGen GroupChat | v10.0 三态合一 |
| round table 嵌套(subpanel) | LangGraph hierarchical supervisor + AutoGen nested chat | v10.0 把它做成显式协议字段 |

---

## §13 — 置信度声明 / Confidence Assessment

| 框架 | 置信度 | 主要不确定性 |
|------|--------|--------------|
| LangGraph | HIGH | 2026 年小版本 API 微调可能(但 StateGraph + Store + supervisor 大概念稳定) |
| MAF | HIGH | 1.0 GA(2026-04)稳定,但部分高级功能(Agent Harness / hosted)还在演进 |
| CrewAI | HIGH | v1.15.1 字段表稳定;v2+ 可能引入 breaking change(未发生) |
| Claude Agent SDK | HIGH | 官方 docs 完整;`AgentDefinition` 字段在 v2.1.x 演进(`memory` 字段是较新加入) |
| OpenAI Swarm | MEDIUM | 标 experimental,可能被 Agents SDK 完全替代 |
| Camel-AI | MEDIUM | 2026 专属 docs 稀疏;framework 持续演进 |
| Agent-MCP | MEDIUM | 社区项目,非厂商背书;设计哲学鲜明但 production case 不多 |
| A2A | HIGH | 协议本身稳定;CC 不原生支持 |

### §13.1 — Low-confidence 风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| MAF 在 v10.0 ship 后大幅改 API | v10.0 引用显得过时 | 引用时锁定版本号(MAF 1.0 GA,2026-04) |
| Claude Agent SDK subagent 形态被 Anthropic 大改 | 决策 #5(否决 subagent 形态)的论据失效 | 引用官方 docs + 时间戳,论据即使失效也保留历史决策价值 |
| A2A 在 CC 中获得一等公民支持 | 决策 #1(不用 A2A)需要重审 | `06-CROSS-REPO-IMPACT.md` 标记为 v12+ 扩展位,留后路 |

---

## §14 — Gaps to Address(留给后续 phase 的 open question)

1. **round table 召集人 LLM 的具体 prompt 模板**:本 FEATURES.md 只列出协议字段,没设计具体 prompt(留给 `02-ROUND-TABLE-PROTOCOL.md`)。
2. **agent YAML schema 的 JSON Schema 正式定义**:本 FEATURES.md 给出字段表和借鉴理由,JSON Schema 留给 `01-AGENT-REGISTRY-SCHEMA.md` + `agents-schema.yaml`。
3. **curator 如何感知 round table 历史**:v6.0 curator 是单 agent feedback-driven,v10.0 的 round table turn-by-turn history 怎么进 curator 的 scan 队列?需要 `00-FIRST-PRINCIPLES.md` 推导。
4. **CC 在 round table 中具体怎么被驱动**:本 FEATURES.md 说"CC 控 question framing / synthesis",但 CC 的具体调用形态(MCP tool? tmux dispatch? subagent?)留给 `03-COMPARISON-VS-KIMI-MCP-SHIM.md` 和 `04-MIGRATION-PATH.md`。
5. **panelist 之间如何 handoff asset(不只是 lock)**:本 FEATURES.md 提了 `asset_locks`,但 asset 的实际流转(producer → consumer)没设计,留给 `02-ROUND-TABLE-PROTOCOL.md`。
6. **GLM 4-key rotation 跟 round table 多 panelist 并发的 cost 模型**:v10.0 设计型,但 v11.0 PoC 需要算 token 成本,留给 `05-POC-PLAN.md`。

---

## §15 — Sources(全部 URL,带置信度)

### §15.1 — HIGH 置信度(官方 docs / 一手源)

- LangGraph 官方产品页(含 memory 持久化描述): https://www.langchain.com/langgraph
- LangGraph Persistence 文档(checkpointer + store 双层): https://docs.langchain.com/oss/python/langgraph/persistence
- LangGraph Memory 概念文档(namespace 元组): https://docs.langchain.com/oss/python/concepts/memory
- langgraph-supervisor 官方 reference(`create_supervisor()`): https://reference.langchain.com/python/langgraph-supervisor
- LangGraph GitHub: https://github.com/langchain-ai/langgraph
- Microsoft Agent Framework overview(官方): https://learn.microsoft.com/en-us/agent-framework/overview/
- Microsoft Agent Framework v1.0 GA 公告(2026-04-03): https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/
- AutoGen → MAF 迁移指引(官方): https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/
- Microsoft multi-agent patterns(协议分层指引): https://learn.microsoft.com/en-us/agents/architecture/multi-agent-patterns
- AutoGen 0.2 GroupChat 文档(概念源): https://microsoft.github.io/autogen/0.2/docs/Use-Cases/agent_chat
- CrewAI Agents v1.15.1 官方 docs(字段表权威源): https://docs.crewai.com/v1.15.1/en/concepts/agents
- CrewAI GitHub: https://github.com/crewaiinc/crewai
- Claude Agent SDK overview(官方): https://code.claude.com/docs/en/agent-sdk/overview
- Claude Agent SDK subagents(官方,含 AgentDefinition 字段表): https://code.claude.com/docs/en/agent-sdk/subagents
- A2A DeepLearning.AI 课程: https://www.deeplearning.ai/courses/a2a-the-agent2agent-protocol

### §15.2 — MEDIUM 置信度(社区项目 / 单篇深度文章)

- Agent-MCP GitHub(社区项目): https://github.com/rindelph/Agent-MCP
- OpenAI Swarm GitHub(experimental): https://github.com/openai/swarm
- OpenAI Swarm community discussion(教育性定位说明): https://community.openai.com/t/openai-swarm-for-agents-and-agent-handoffs/976579
- Camel-AI GitHub: https://github.com/camel-ai/camel
- Camel-AI arXiv 论文(2303.17760): https://arxiv.org/abs/2303.17760
- Camel-AI "Create Your First Agents Society" cookbook: https://docs.camel-ai.org/cookbooks/basic_concepts/create_your_first_agents_society
- MCP 多 agent 学术调研(arxiv 2504.21030): https://arxiv.org/html/2504.21030v1
- LangGraph vs CrewAI vs AutoGen 2026 对比(dev.to): https://dev.to/pockit_tools/langgraph-vs-crewai-vs-autogen-the-complete-multi-agent-ai-orchestration-guide-for-2026-2d63
- 8 Frameworks 2026 比较(MorphLLM,提及 Claude Agent SDK hooks + subagents): https://www.morphllm.com/ai-agent-framework

### §15.3 — LOW 置信度(辅助参考)

- 各框架教程 / Medium 文章(用于交叉验证 2026 状态,未单列)

---

## §16 — 文档元数据

- **创建:** 2026-07-06(by v10.0 Phase 44 research sub-agent)
- **下游消费者:**
  - `00-FIRST-PRINCIPLES.md`(§10 借鉴点表 + §11 anti-features)
  - `01-AGENT-REGISTRY-SCHEMA.md`(§3 CrewAI / §4 Claude Agent SDK / §9.1 字段速查 + §12 表中表)
  - `02-ROUND-TABLE-PROTOCOL.md`(§1 LangGraph / §2 AutoGen-MAF / §9.3 协作模式速查 + §10 借鉴点)
  - `03-COMPARISON-VS-KIMI-MCP-SHIM.md`(§7.4 Microsoft 三层协议 + §8 A2A 立场)
  - `05-POC-PLAN.md`(§4.4 Workflow tool v12+ 候选)
  - `06-CROSS-REPO-IMPACT.md`(§7.4 + §8.3 A2A 扩展位)
- **稳定性:** §1-§9 `stable`(框架事实描述);§10-§12 `evolving`(借鉴点可能在下游设计文档细化);§13-§14 `evolving`
- **下次更新触发:** (a) v10.0 任一下游设计文档引用本文档时发现错误;(b) 2026-Q4 任一框架大版本发布(MAF v2 / LangGraph v2 / CrewAI v2)
