# 00 — 第一性原理推导:v10.0 Hermes-Agent 编排架构(设计型 milestone 根论据)

> **Document status:** design-2026-07-06-v10prfp · supersedes: none · superseded_by: TBD
> **Milestone:** v10.0 — Hermes-Agent 编排架构第一性原理推导(设计型)
> **Phase:** 44 of v10.0 design milestone · **Authors:** hermes-agent design team
> **Audience:** Kai (设计决策 reviewer) + Kimi(Notion 续聊对照)+ 未来 v11.0 PoC 实施者
> **Reading time:** ~30 minutes(全文)/ ~8 minutes(§0 + §1.2 + §3.1 总表)
> **Stability:** §1.2 + §2 + §3 + §4 全部 `stable`(修改需开新设计-修订里程碑,类比 v2.0 PRFP §1.1 修改门槛);§5 + §6 `stable`(下游引用指南 + 风险登记,跟随 §1-§4 锁定);References `stable`
> **Confidence:** HIGH(基于 4 个 research 子任务:STACK / FEATURES / ARCHITECTURE / PITFALLS,SUMMARY §Confidence Assessment 给出 HIGH overall)

---

## §0 — 阅读指南

本文档是 **v10.0 设计型 milestone 的根论据文档(root argument)**,产出从 7 个已锁设计决策的 first-principles 推导链 + 「v10.0 显式拒绝」总表 + FEATURES §10 borrowable points 评估 + 后续 6 份设计文档(01-06)的引用指南。后续 6 份文档**在不重新推导决策的前提下**引用本文档作根论据。

**与 v2.0 PRFP 的关系:** v2.0 PRFP `00-FIRST-PRINCIPLES.md`(1638 行)是本文档方法论源 —— Musk 第一性原理 / Aristotle 根 / 认识论标签 / Steelman-the-Elimination / MADR alternatives log 全部在 v2.0 PRFP §1.1-§1.5 完整建立。本文档**引用 v2.0 PRFP 作为方法论 source**(§1.1),不重复完整 Aristotle 引文。本文档**专注 v10.0-specific 加严**与 **7 决策推导 + 显式拒绝总表 + borrowable 评估**。

### 章节地图

| 章节 | 内容 | 阅读优先级(按角色) |
|---|---|---|
| §0 | 阅读指南(本节) | 所有人先读 |
| §1 | 方法论框架(简化)+ 7 决策清单 + paradigm shift 声明 | 维护者必读;reviewer 必读 §1.2 + §1.3 |
| §2 | 7 决策 first-principles 推导链(§2.1-§2.7) | **核心章节** — 维护者 + PoC 实施者必读 |
| §3 | 「v10.0 显式拒绝」总表(≥10 行,3-source 合并) | 所有下游设计文档作者必读 |
| §4 | FEATURES §10 borrowable points 评估(B1.3/B3.5/B4.1/B7.2/B5.1) | 决策 #5/#6/#7 推导的业界对照 |
| §5 | 后续 6 份设计文档的引用指南(citation cards) | 所有下游设计文档作者必读 |
| §6 | Coherence 声明 + 风险登记表 + milestone 挂钩 | v11.0 PoC 实施者必读 §6.2 |
| References | 全部引用源(4 v10.0 research docs + v2.0 PRFP + PROJECT.md + Notion) | 被引文出处挑战时查 |

### 稳定性标记(修改门槛)

| 章节 | 稳定性 | 修改门槛 |
|---|---|---|
| §1.2 (7 决策清单) | `stable` | 决策已锁(PROJECT.md §Current Milestone v10.0),修改需开新设计-修订里程碑 |
| §1.3 (paradigm shift 声明) | `stable` | 同上(paradigm-shift-claim-1..4 anchor) |
| §2 (7 决策推导链) | `stable` | 修改需开新设计-修订里程碑;每决策 5-段 scaffold 必须重跑;§5 引用 entry points 必须同步更新 |
| §3 (显式拒绝总表) | `stable` | 拒绝项 re-litigation 需开新里程碑(类比 v2.0 PRFP §1.1 修改门槛) |
| §4 (borrowable 评估) | `stable` | 赞同/拒绝/改造结论锁定;评估方法论可在下游细化 |
| §5 (下游引用指南) | `stable` | 锁定下游 doc 的引用 entry points;新加设计文档需补 §5.X 引用卡 |
| §6 (总结 + 风险登记 + milestone 挂钩) | `stable` | 跟随 §1-§4 |

### 受众指引(3 类读者)

- **Kai(reviewer / 设计决策者):** 先读 §0 + §1.2 + §1.3 + §3.1 总表 + §6.1 coherence 声明。如果对某条决策推导有疑问,跳到 §2 对应 §2.N。如果对某条拒绝项有疑问,跳到 §3.1 + §3.2 使用指南。§4 borrowable 评估是业界对照的快查表。
- **Kimi(Notion 续聊对照 / Kimi 架构2.0 作者):** 先读 §1.3 paradigm shift 声明(理解 Kimi 方案与 v10.0 设计的本质差异),再读 §3.1 总表(理解 v10.0 显式拒绝了哪些业界形态,包括 Kimi 的 `.claude/agents/*.md` subagent 形态),最后读 §4.3(B4.1 — Claude Agent SDK subagent 否决论据)。这些是续聊 Notion 架构2.0 时直接对照的根论据。
- **未来 v11.0 PoC 实施者:** 先读 §0 + §1.2 + §5(下游 6 docs 引用指南),然后用 §5.X 索引跳到对应下游设计文档。本文档的决策已锁,v11.0 PoC 实施时**不重新推导**(类比 v2.0 PRFP §1.1 stability marker)。如果实施过程中发现某决策推导有漏洞,记录到 deferred-items.md,在设计-修订里程碑中处理。

---

## §1 — 方法论框架(简化版)

> 本节声明本文档使用的全部方法论工具。完整方法论 canon(Musk 第一性原理 / Aristotle 根 / Epistemic-status taxonomy / Steelman-the-Elimination / MADR alternatives log)在 **v2.0 PRFP §1.1-§1.6** 建立。本文档引用 v2.0 PRFP 作为方法论 source,不重复完整 Aristotle 引文,只加 v10.0-specific 加严。

### §1.1 — 方法论 source 引用(简化版)

本文档使用 v2.0 PRFP §1.1-§1.6 已建立的全部方法论工具,具体包括:

| 方法论工具 | v2.0 PRFP source | 本文档使用方式 |
|---|---|---|
| Musk 式第一性原理(还原→重构) | v2.0 PRFP §1.1 | 每决策推导从「根本需求」出发,显式拒绝「业界都用 X 所以我们用 X」式类比论证 |
| Aristotle 根(哲学根源) | v2.0 PRFP §1.2 | 引用「对我们可知 vs 按本性可知」区分;不在本文档重复 Aristotle 原文 |
| Epistemic-status taxonomy | v2.0 PRFP §1.3 | 每决策标注 confidence(HIGH / MEDIUM)+ 立场来源(STACK/FEATURES/ARCHITECTURE/PITFALLS) |
| Contingent vs Validated-in-Invariant | v2.0 PRFP §1.4 | 7 决策的「锁定选型」视为 `validated`(已 cross-validation);候选选项中被排除的视为 `contingent` |
| Steelman-the-Elimination | v2.0 PRFP §1.5 | 每决策 §2.N.3 必须有 steelman 排除论证,从「根本需求」推排除理由 |
| MADR alternatives log | v2.0 PRFP §1.6 | 每决策 §2.N.2 列候选选项;§2.N.3 列排除理由(具体失败模式,不是「较不优选」) |

**完整方法论 canon 引用:** 详见 `.planning/research/v2-pipeline-design/00-FIRST-PRINCIPLES.md` §1.1-§1.6。本文档任何论证越界(超出 v2.0 PRFP §1 框架)即视为第一性原理伪装。

#### v10.0 设计型 milestone 的加严

v2.0 PRFP §1.1 的 Musk 第一性原理纪律在 v10.0 设计型 milestone 中**进一步加严**:每条决策推导必须从「Hermes-Agent 平台的根本需求」出发,显式拒绝「业界 framework X 这么做所以我们这么做」式类比论证。

**为什么 v10.0 需要加严?**

v10.0 是**设计型 milestone**(零代码改动,产出 7 份设计文档指导 v11.0 PoC)。设计型 milestone 的最大风险是 **"业界 framework X 这么做所以我们抄 X"** 式伪装类比论证 —— 这种论证在 v2.0 PRFP 里被 PITFALLS §1.1("第一性原理伪装")显式拒绝,但在 v10.0 加严到 **每条决策推导必须 explicitly state 根本需求 + explicitly reject 类比论证** 的程度。Musk 第一性原理的核心是 **还原→重构**,不是「抄最热门的」。 STACK.md §1 / FEATURES.md §1-§8 / ARCHITECTURE.md / PITFALLS.md 四份 research 提供了业界对照,但**对照的目的**是**验证 v10.0 的根本需求推导是否站得住脚**,不是「选最热门的 framework 抄过来」。

**具体加严规则(本文档 §2 推导链必须遵守):**

1. **每决策 §2.N.1 必须从「根本需求」陈述出发**,而非从「业界 framework X 提供 Y 能力」出发。
2. **每决策 §2.N.3 Steelman 排除论证必须从根本需求推排除理由**,而非从「业界没人这么做」推。
3. **每决策 §2.N.5 Cross-Validation Evidence 引用 4 research source 是验证手段,不是论证主体**。论证主体是 §2.N.1 + §2.N.3。如果 §2.N.5 引用与 §2.N.1-§2.N.3 推导矛盾,以推导为准,research source 标 `evolving`(留待设计-修订里程碑重审)。
4. **显式拒绝「业界都用 X 所以我们用 X」式类比**。具体禁止表述:
   - ❌ "LangGraph 这么做的,我们抄"
   - ❌ "CrewAI 字段表 30+ 项是 industry standard,我们也加这么多"
   - ❌ "Claude Agent SDK 的 subagent 是 Anthropic 官方推荐,所以 v10.0 也用 subagent"
5. **允许的表述形式:**
   - ✅ "v10.0 根本需求是 X(STACK §Y 验证);业界 framework A 的某机制(B1.3 借鉴点)与根本需求一致,采纳其设计思路"
   - ✅ "v10.0 根本需求是 X;业界 framework B 的某形态(B4.1 反例)违反根本需求,显式拒绝(详见 §3.1 总表 row N)"
   - ✅ "v10.0 根本需求是 X;4 research source 的 cross-validation(SUMMARY.md 'Design Decisions Validated' 表)确认此选型有强支持 / 中性 / 警告"

**审查规则:** 任一决策推导被发现违反加严规则,标记为 PITFALLS §1.1 违规,必须在设计-修订里程碑中重写。

### §1.2 — 7 决策清单总览(锁定选型 + 根本需求)

下表是 v10.0 milestone 已锁定的 7 个设计决策,摘自 SUMMARY.md "Design Decisions Validated" 表 + PROJECT.md §Current Milestone v10.0。**「根本需求」一列是本文档新增的 load-bearing addition** —— 它声明每决策**要解决的根本问题**(WHAT),独立于任何选项比较(HOW)。

| # | 决策类别 | 锁定选型 | 根本需求(要解决的根本问题) | v10.0 推导章节 |
|---|---------|---------|----------------------------|----------------|
| **1** | T6 协议(协议层) | Hermes MCP server(扩展现有 `mcp_serve.py`)+ tmux dispatch(复用 coding-agent)+ CC native MCP client for callbacks | Hermes 与 CC 之间需要**稳定、低故障面、可演进**的通信通道 —— 任何自定义 RPC / cross-vendor 协议都增加故障面 | §2.1 |
| **2** | B3a Python runner(执行分工) | delegate-only phase(9 个创意 step)迁 CC;ComfyUI-calling phase(4 个生成 step)+ Step 0/6.5/15 保留 Python runner | 既**保留 v3-v9 五 milestone 硬化的 ComfyUI 集成 + asset bus + GoalBuilder**,又**把适合 CC 推理的创意决策环节迁出**(决策分工) | §2.2 |
| **3** | D2 storyboard-first-class(并行调度) | V8.6 编号保留,在 orchestrator 调度层做 round-based parallel(跨场景,不跨 step) | 在**不破坏 V8.6 编号契约(FOUND-08)**的前提下,获得**真实有价值的并行加速** | §2.3 |
| **4** | G2 通用编排框架(扩展性) | 抽象 pipeline orchestration pattern,kais-movie-pipeline 作为首个 sample | **v12+ 扩展 music video / long-form 时不需要重写编排器** —— 通用框架分离编排逻辑与具体 domain | §2.4 |
| **5** | α agent form(agent 形态) | YAML + persona prompt + tools + refs + memory_scope + lineage,物理位置 `~/.hermes/agents/{name}.agent.yaml` | agent 是**有持久身份、有记忆、可自进化的实体**,不是 prompt 模板 —— 这是 v10.0 paradigm shift 最核心的载体 | §2.5 |
| **6** | per-agent memory(记忆 + 自进化) | per-agent scoped memory(扩展 mem0 backend),curator 驱动跨项目自进化 | **agent 随项目越多越有经验**(v10.0 paradigm shift 核心诉求)—— 业界没有任何主流框架把 per-agent scoped memory + curator-driven 自进化作为原生组合 | §2.6 |
| **7** | (vi) 分层 CC 角色(协作分工) | Hermes 控 turn_order / max_rounds / schema / early_stop_rule;CC 控 question framing + synthesis | **审计性 + 可重现 + token 成本可控 + 充分用 CC 推理能力** —— 单层全控(CC 全控或 Hermes 全控)都会失衡 | §2.7 |

**关键观察:** 7 决策的根本需求相互呼应 —— 决策 #5(agent 形态)定义「agent 是什么」,决策 #6(per-agent memory)定义「agent 如何变好」,决策 #7(分层 CC)定义「agent 之间如何协作」。这三个决策构成 v10.0 paradigm shift 的**核心三件套**;决策 #1-#4 是支撑三件套的基础设施(协议 / 执行 / 调度 / 扩展性)。

**7 决策 explicit enumeration(供 §2 推导链索引):**

- 决策 1(T6 协议)→ §2.1
- 决策 2(B3a Python runner)→ §2.2
- 决策 3(D2 storyboard)→ §2.3
- 决策 4(G2 通用框架)→ §2.4
- 决策 5(α agent form)→ §2.5
- 决策 6(per-agent memory)→ §2.6
- 决策 7((vi) 分层 CC)→ §2.7

每条决策已锁(PROJECT.md §Current Milestone v10.0),本文档 §2 提供 first-principles 推导链作根论据。

### §1.3 — Paradigm Shift 声明(v10.0 与 Kimi 方案的本质差异)

本节 verbatim 引用 PROJECT.md §"关键范式声明(与 Kimi 方案的本质差异)"(lines 51-57),每段标记 `paradigm-shift-claim-N` anchor,下游设计文档可按 anchor 引用。

#### paradigm-shift-claim-1:Kimi 默认 vs v10.0 设计(CC 角色定位)

> **Kimi 默认:** CC 是 agent 容器 + 执行器(`.claude/agents/*.md` Teammates)。
> **v10.0 设计:** Hermes 是 agent 容器(新形态),CC 仅是**场地 + 协调员 + 结构化助手**。

**根本差异:** Kimi 方案把 agent 塞进 CC(`.claude/agents/*.md` filesystem subagent);v10.0 把 agent 留在 Hermes-side(`~/.hermes/agents/{name}.agent.yaml`),CC 只做场地。这不是「Kimi 抄 Claude Agent SDK subagent 形态,v10.0 不抄」的差异 —— 而是 **agent 身份归属的根本差异**:agent 是 Hermes 的(Hermes-side 持久实体,跨项目自进化),还是 CC 的(CC-side subagent,30 天 transcript 自动清理)?决策 #5 α agent form 推导(§2.5)+ §3 row 1(拒绝 subagent 容器)是这条 paradigm shift 的物理载体。

#### paradigm-shift-claim-2:Agent vs Skill 分层

> Agent vs Skill 分层:**不是把现有 SKILL 当 agent 用**,也**不是把 agent 塞进 CC**;agent 是 Hermes-side 独立 YAML 实体,有 per-agent memory + 自进化能力。

**根本差异:** v1-v9 把 movie-experts 当 SKILL 用法(model 是 agent,SKILL.md 是 user-message prompt injection);v10.0 引入**新的 agent 形态**(system-prompt fragment persona + per-agent memory + curator-driven evolution)。SKILL 形态作 fallback 保留(决策 #5 `default_invocation: skill_fallback`)。决策 #5 + 决策 #6 是这条 paradigm shift 的物理载体;ARCHITECTURE §1.1 18-field schema(其中 `persona` 字段是「rewritten system-prompt fragment」vs SKILL body 是「user-message」)是字段级实现。

#### paradigm-shift-claim-3:CC 的 Team Lead 配置极薄

> CC 的 Team Lead 配置极薄:**不定义 Expert,只描述 round table 协调员工作流**。

**根本差异:** Kimi 方案的 CC 配置是「定义 N 个 Expert(subagent)」;v10.0 的 CC 配置是「定义 1 个 round table 协调员」。Expert 数量的差异反映的是**控制权分布**:Kimi 方案 CC 自己包含 N 个 Expert,每个 Expert 都能直接被 CC 调用;v10.0 CC 只有一个协调员,真正的 Expert 是 Hermes-side agent,通过 MCP tool 调用。决策 #7 (vi) 分层 CC 推导(§2.7)+ §3 row 1(拒绝 subagent 容器)是这条 paradigm shift 的物理载体;ARCHITECTURE §5.3 round table lifecycle 是协议级实现。

#### paradigm-shift-claim-4:Agent 是 Hermes-side 独立 YAML 实体

> Agent 是 Hermes-side 独立 YAML 实体,有 per-agent memory + 自进化能力。

**根本差异:** 这是 paradigm-shift-claim-2 的强化版,强调**独立性**(independent entity,不是 CC 的 subagent,也不是 SKILL 的 alias)。agent YAML 的物理位置 `~/.hermes/agents/{name}.agent.yaml` 是独立性的物理载体;`lineage` 字段(记录从哪个 SKILL.md 转化而来 + skill_sha256)是独立性的溯源机制;`evolution_log` + `fitness_score` 是自进化的审计载体。决策 #5 + 决策 #6 + 决策 #7(三层实体 / 记忆 / 协作)是这条 paradigm shift 的物理载体。

#### paradigm-shift-claim 总览

| claim | 核心声明 | 物理载体(决策 #) | 物理载体(字段 / 协议) |
|---|---|---|---|
| paradigm-shift-claim-1 | Hermes 是 agent 容器,CC 仅是场地 | 决策 #5 + 决策 #7 | `~/.hermes/agents/*.agent.yaml` + round table 协议 |
| paradigm-shift-claim-2 | Agent 与 SKILL 分层,SKILL 作 fallback | 决策 #5 + 决策 #6 | `persona` system-prompt fragment + `default_invocation: skill_fallback` |
| paradigm-shift-claim-3 | CC Team Lead 极薄,不定义 Expert | 决策 #7 | ARCHITECTURE §5.3 round table lifecycle |
| paradigm-shift-claim-4 | Agent 是独立 YAML 实体,有 memory + 自进化 | 决策 #5 + 决策 #6 + 决策 #7 | `lineage` + `evolution_log` + `fitness_score` |

下游设计文档(01-06)在引用 paradigm shift 时,**必须用 paradigm-shift-claim-N anchor**,不重新陈述 paradigm shift 内容(防 drift)。

---

## §2 — 7 决策 first-principles 推导链

> 本节是本文档的**核心章节**。每决策推导链遵循 5-段 scaffold(根本需求 / 候选选项 / Steelman 排除 / 锁定选型 / Cross-Validation Evidence),严守 §1.1 加严规则(显式拒绝类比论证)。

### §2.0 — 推导方法声明

**推导 scaffold(每决策 5 段,缺一不可):**

1. **§2.N.1 根本需求** — 决策要解决的**根本问题**(WHAT),独立于任何选项比较。从 v10.0 paradigm shift(§1.3)推出,不从「业界 framework 提供 X 能力」推出。
2. **§2.N.2 候选选项** — 枚举 2-4 个真实候选,每个候选引用 research source(STACK/FEATURES/ARCHITECTURE/PITFALLS 的具体章节号)。
3. **§2.N.3 Steelman 排除论证** — 对每个被排除候选,从**根本需求**推排除理由(具体失败模式),不从「业界没人这么做」推。
4. **§2.N.4 锁定选型 + Rationale** — 一段话陈述存活选项 + 一句话 rationale anchored in 根本需求 + cross-validation 引用。
5. **§2.N.5 Cross-Validation Evidence** — 4 research source 的支持/反对/警告(摘自 SUMMARY.md "Design Decisions Validated" 表)。

**Steelman-the-Elimination 纪律(v2.0 PRFP §1.5):** 排除论证必须给**实质的钢人反驳**,不是 strawman。「X 不流行」是 strawman;「X 违反根本需求 Y」是 steelman。每条 §2.N.3 必须 explicitly state「X 违反 Y 因为 Z」。

**Cross-Validation Evidence 是验证手段,不是论证主体:** §2.N.5 引用 4 research source 是为了**交叉验证** §2.N.1-§2.N.4 的推导。如果 research source 与推导矛盾,以推导为准,research source 标 `evolving`(类比 v2.0 PRFP §1.4 contingent vs validated-in-invariant 分类)。

**MADR alternatives log 纪律(v2.0 PRFP §1.6):** §2.N.2 候选选项枚举采用 MADR "Considered Options" 结构。每候选标注 CHOSEN / REJECTED + 具体失败模式(不是「较不优选」)。

---

### §2.1 — 决策 1: T6 协议层(Hermes MCP server + tmux dispatch + CC native MCP client)

**锁定选型:** 扩展现有 `mcp_serve.py`(FastMCP)+ tmux dispatch(复用 coding-agent skill v7.0 ship)+ CC native MCP client(`~/.claude.json` 已配置 stdio + ✓ Connected)。

#### §2.1.1 — 根本需求

**根本需求:** Hermes-Agent(主 agent + 编排器)与 Claude Code(CC,执行场)之间需要**稳定、低故障面、可演进**的通信通道。

**从 paradigm shift 推出:** paradigm-shift-claim-1 声明「Hermes 是 agent 容器,CC 仅是场地」—— 这个分层要求 Hermes 与 CC 之间有**清晰、稳定、低故障面**的协议边界。任何引入大量自定义代码 / 跨厂商依赖 / 多进程协调的协议层都会增加故障面,违反「低故障面」根本需求。任何 lock-in 到某一 LLM 厂商的协议(如 Kimi 全 MCP shim 依赖 Kimi server)都会限制「可演进」根本需求(v10.0 不应假设 v11.0 PoC 仍用 Kimi)。

**与 v3-v9 实战经验对照:** v3-v9 五 milestone 都基于「Hermes MCP server + tmux dispatch」的稳定通道 —— v3 Skills-to-DAG、v4 methodology backfill、v5 V8.6 sync、v6 self-evolution、v9 platform slice 都通过这条通道工作。换协议层 = 推倒重来,违反「稳定、可演进」根本需求。

#### §2.1.2 — 候选选项

| 候选 | 描述 | Research source |
|------|------|-----------------|
| **(a) T6 Hermes MCP server**(CHOSEN) | 扩展现有 `mcp_serve.py`(FastMCP 单 server)+ tmux dispatch + CC native stdio client | STACK §1-§5(强支持,零架构改动)+ ARCHITECTURE §4.2(dispatch path)+ SUMMARY.md Decision 1 行 |
| **(b) A2A 跨厂商协议** | 用 A2A(Google → Linux Foundation)做 Hermes ↔ CC 通讯 | FEATURES §7.4 B7.1 + §8 B8.1 / B8.3(跨厂商协议层)|
| **(c) Kimi 全 MCP shim** | 把 Kimi Notion 架构2.0 的「CC subagent + MCP server shim」全套搬过来 | FEATURES §4 B4.1(Claude Agent SDK subagent 形态)+ Kimi Notion page |
| **(d) Custom RPC over HTTP** | 自己设计 HTTP RPC 协议 | (无 research source 直接覆盖 —— 自定义方案)|

#### §2.1.3 — Steelman 排除论证

**排除 (b) A2A 跨厂商协议:** A2A 是为「跨厂商 agent-to-agent 通讯」设计的协议(FEATURES §8.1)。v10.0 是**单厂商内部协作**(Hermes + CC,Anthropic CC 是已知 endpoint),不需要 cross-vendor discovery / negotiation。引入 A2A 增加 agent card 发布 / task lifecycle / negotiation 等概念开销,违反「低故障面」根本需求。Microsoft multi-agent-patterns 指引(FEATURES §7.4 B7.1)明确推荐「internal flow → platform-native;tool → MCP;cross-platform → A2A」—— A2A 在 v10.0 范围是**过度工程化**。**排除理由:违反「低故障面」根本需求(A2A 概念开销对单厂商内部协作是 over-engineering)。**

**排除 (c) Kimi 全 MCP shim:** Kimi 方案的完整评估 deferred 到 Phase 47(03-COMPARISON-VS-KIMI-MCP-SHIM.md),但在决策 #1 层面,可以预先排除「全套搬过来」路径 —— 因为 Kimi 方案的核心是「CC 是 agent 容器」(paradigm-shift-claim-1 显式拒绝),把 Kimi 全套搬过来等于把 paradigm shift 也搬过来反转。**排除理由:违反 paradigm-shift-claim-1(Hermes 是 agent 容器,不是 CC)。** 详细对照在 Phase 47。

**排除 (d) Custom RPC over HTTP:** 自己设计 HTTP RPC 协议意味着重新发明 MCP 的 tool discovery / schema 派生 / transport 抽象 —— STACK §2.4 显示 FastMCP + Pydantic Model 已经免费提供 JSON Schema 自动派生、ToolAnnotations 副作用声明、stdio/HTTP/SSE 三 transport 切换。重发明违反「低故障面」+「可演进」根本需求(MCP 是 Anthropic 主推的开放标准,生态在演进;自研协议无人维护)。**排除理由:违反「低故障面」+「可演进」(reinviting MCP 是 NIH syndrome,无生态红利)。**

**Steelman 反驳最强候选 (b) A2A:** 「A2A 是 Linux Foundation 治理、Google + Microsoft + Salesforce 背书的开放标准,用 A2A 等于『站在巨人肩膀上』」。**我方回应:** A2A 解决的根本问题是「跨厂商 agent 互操作」,不是「单厂商内部编排」。v10.0 不需要跨厂商互操作(Kai 当前是单人开发 + 单 CC 实例 + 单 Hermes 实例)。Microsoft 自己的 multi-agent-patterns 指引(FEATURES §7.4 B7.1)明确说 internal flow 用 platform-native,不用 A2A —— 这是「业界最佳实践」与「v10.0 根本需求」一致的证据,不是类比论证。

#### §2.1.4 — 锁定选型 + Rationale

**锁定 (a) T6 Hermes MCP server。**

**Rationale:** T6 是 v10.0 paradigm shift 要求的「稳定、低故障面、可演进」通道的**唯一同时满足三者的选项**:稳定性来自 MCP 1.0 spec stable + FastMCP 1.26 ship(STACK §1-§4 实测 ✓ Connected);低故障面来自单 stdio 进程 + 零自定义协议代码(STACK §4.2 推导);可演进来自 MCP 是 Anthropic 主推开放标准 + tool 动态发现(注册新 tool 仅需重启 CC 一次,STACK §6.2)。

**Cross-validation(SUMMARY.md Decision 1):** STACK 强支持(§1-§5 全文证明 FastMCP stable);FEATURES 强支持(§7.4 Microsoft 三层协议分层验证);ARCHITECTURE 中性(假设 T6 已锁);PITFALLS §P10 警告(MCP 单进程 stdio 是隐私正面,但 round-table coordinator 跨 project 聚合上下文仍是攻击面 —— 留给 Phase 46 解决)。

#### §2.1.5 — Cross-Validation Evidence(4 research sources)

| Source | 章节 | 立场 | 引用要点 |
|--------|------|------|----------|
| **STACK** | §1-§5(全文) | **强支持** | FastMCP `@mcp.tool()` 是 stable API;mcp==1.26.0 已 ship;`mcp_serve.py` 扩展是零架构改动 additive patch(~450 LOC);stdio transport v11.0 PoC 唯一推荐 |
| **FEATURES** | §7.4 B7.1 + §8 | **强支持** | Microsoft 三层协议分层(PLATFORM §7.4)直接验证 "internal → platform-native;tool → MCP;cross-platform → A2A" —— v10.0 是 internal + tool 层,A2A(§8)不在范围 |
| **ARCHITECTURE** | §4.2(dispatch path) | **中性** | 假设 T6 已锁,只在 dispatch path(`agent_registry` → MCP tool)上展开;STACK 与 ARCHITECTURE 在 MCP tool 命名上轻微冲突(`get_agent_persona` vs `agent_get_persona`,CC-1),留给 Phase 46 解决 |
| **PITFALLS** | §P10(privacy) | **警告(可缓解)** | MCP 单进程 stdio 是隐私正面(无网络面);但 round-table coordinator 跨 project 聚合上下文仍是攻击面 —— Phase 46 必须设计 confidentiality propagation |

**决策 #1 状态:** `validated-in-invariant`(4 research source 一致强支持,PITFALLS 警告有明确缓解路径)。

---

### §2.2 — 决策 2: B3a Python runner 增量迁移

**锁定选型:** delegate-only phase(9 个创意 step,如 creative_source / screenplay / cinematographer 等)迁 CC;ComfyUI-calling phase(4 个生成 step,如 visual_executor / audio_pipeline 等)+ Step 0/6.5/15 保留 Python runner。

#### §2.2.1 — 根本需求

**根本需求:** 既**保留 v3-v9 五 milestone 硬化的 ComfyUI 集成 + asset bus + GoalBuilder**,又**把适合 CC 推理的创意决策环节迁出**。

**从 paradigm shift 推出:** v10.0 paradigm shift(§1.3)只声明 agent 形态 / CC 角色 / per-agent memory 三件套,**没有声明「Python runner 必须全废」**。ComfyUI 集成是 v3-v9 五 milestone 的核心硬化产出(V8.6 13-step pipeline + dreamina CLI + Step 7 character asset library + Step 14 platform slice + Step 6.5 LTX2.3 preview + Step 15 platform API 收敛)—— 推倒重来违反「保留硬化产出」根本需求。但纯创意决策环节(剧本评估 / 镜头意图 / 风格选择)适合 CC 推理(CC 是 Anthropic 顶级 reasoning 模型),不迁出 = 浪费 CC 能力,违反「充分用 CC 推理」根本需求(与决策 #7 同源)。

**与 Kimi 方案对照:** Kimi Notion 架构2.0 倾向「全迁 CC」(Kimi 默认 CC 是 agent 容器 + 执行器,paradigm-shift-claim-1 显式拒绝);v10.0 选 B3a 增量迁移是**对 Kimi 方案的修正**。

#### §2.2.2 — 候选选项

| 候选 | 描述 | Research source |
|------|------|-----------------|
| **(a) B3a 增量迁移**(CHOSEN) | 9 delegate-only phase 迁 CC,4 ComfyUI phase + Step 0/6.5/15 保留 Python runner | PROJECT.md §Current Milestone(锁定)+ STACK §3.2 Tool 7 `run_python_phase` 作 boundary tool |
| **(b) B3b 全迁 CC** | 13 step 全迁 CC,ComfyUI 调用通过 CC tool 暴露 | (与 paradigm-shift-claim-1 冲突,被 PROJECT.md 显式拒绝) |
| **(c) B1 status quo** | Python runner 全保留,CC 不参与 pipeline | (不获得 CC 推理能力,违反决策 #7 根本需求) |
| **(d) B3c ComfyUI 全迁 CC** | 把 ComfyUI 调用迁到 CC tool | (ComfyUI CLI 是 Python subprocess,迁 CC 等于多一层 MCP 包裹,无收益) |

#### §2.2.3 — Steelman 排除论证

**排除 (b) B3b 全迁 CC:** 全迁 = 推倒 v3-v9 五 milestone 硬化的 ComfyUI 集成 + asset bus + GoalBuilder —— v9 platform slice(Step 14)+ LTX2.3 preview(Step 6.5)+ formula tuning(Step 15)全部需要 Python runner 与 ComfyUI / dreamina CLI / 平台 API 直接交互。这些 step 迁 CC 等于让 CC 通过 MCP tool 间接调用 ComfyUI —— 增加故障面,违反决策 #1「低故障面」根本需求。**排除理由:违反「保留 v3-v9 硬化产出」根本需求。**

**排除 (c) B1 status quo:** Status quo = 不获得 CC 推理能力,创意决策环节继续用 Python runner 内的 LLM 调用(hermes_llm tool)。这违反决策 #7「充分用 CC 推理能力」根本需求(CC 是 Anthropic 顶级 reasoning 模型,适合剧本评估 / 镜头意图 / 风格选择等需要多轮思考 + 长上下文的创意决策)。**排除理由:违反决策 #7「充分用 CC 推理」根本需求。**

**排除 (d) B3c ComfyUI 全迁 CC:** ComfyUI 是 Python subprocess 调用(dreamina CLI / ComfyUI API),迁到 CC tool 等于在 MCP server 里包 Python subprocess —— 多一层 MCP 协议开销,零能力增益。STACK §3.2 Tool 7 `run_python_phase` 已经是 boundary tool(`openWorldHint=True`),允许 CC 通过 MCP 调用 Python runner 中的 ComfyUI step —— 这是 B3a 的设计,B3c 是 B3a 的退化形式。**排除理由:B3c 是 B3a 的退化形式,无新增能力,徒增 MCP 协议开销。**

**Steelman 反驳最强候选 (b) B3b:** 「全迁 CC = 单一执行器,代码统一,维护成本低」。**我方回应:** 「单一执行器」是表面优势;实际上 ComfyUI subprocess + dreamina CLI + 平台 API 在 CC 内部仍需 Python 调用,等于在 CC 内重新实现 Python runner —— v3-v9 五 milestone 的硬化产出(配方库 / 审核门 / 平台母版切片 / 数据收敛)全部需要重新实现。这是 NIH syndrome,违反「保留硬化产出」根本需求。

#### §2.2.4 — 锁定选型 + Rationale

**锁定 (a) B3a 增量迁移。**

**Rationale:** B3a 是**唯一同时保留 v3-v9 硬化产出 + 充分用 CC 推理能力**的选项。boundary 设计:9 个 delegate-only phase 通过 CC 的 round table 协议(决策 #7)调用;4 个 ComfyUI-calling phase + Step 0/6.5/15 通过 STACK §3.2 Tool 7 `run_python_phase` 作 MCP boundary tool,CC 仍可 dispatch 但执行在 Python runner 内。STACK §3.2 Tool 7 的 `openWorldHint=True` annotation 显式声明「与外部世界交互」,这是 B3a 设计的字段级实现。

**Cross-validation(SUMMARY.md Decision 2):** STACK 强支持(§3.2 Tool 7 boundary tool 设计);FEATURES / ARCHITECTURE / PITFALLS 不直接覆盖(此决策主要论据来自 PROJECT.md paradigm shift + STACK §3.2)。

#### §2.2.5 — Cross-Validation Evidence(4 research sources)

| Source | 章节 | 立场 | 引用要点 |
|--------|------|------|----------|
| **STACK** | §3.2 Tool 7 + §11.2 | **强支持** | `run_python_phase` 是 boundary tool,`openWorldHint=True` 标注 ComfyUI 调用;retained-phases allowlist 在 `round-table-schema.yaml` 中定义 |
| **FEATURES** | (不直接覆盖) | **中性** | FEATURES 调研的是 multi-agent framework,不直接覆盖 Python runner 迁移决策;§4.4 B4.4 Workflow tool 间接相关(v12+ 大规模编排候选) |
| **ARCHITECTURE** | §4.2 dispatcher | **支持** | Agent dispatcher(`agent/agent_dispatcher.py` v11.0 目标)spawn AIAgent fork 与 Python runner 通过 MCP tool 协作 |
| **PITFALLS** | (不直接覆盖) | **中性** | PITFALLS 关注 per-agent memory 失败模式,不直接覆盖 runner 迁移;§P14(schema migration breaks memory store)间接相关 |

**决策 #2 状态:** `validated-in-invariant`(STACK 强支持,其他 source 中性;PROJECT.md paradigm shift 提供主要论据)。

---

### §2.3 — 决策 3: D2 storyboard-first-class(orchestrator 层 round-based parallel)

**锁定选型:** V8.6 编号保留(FOUND-08),在 orchestrator 调度层做 round-based parallel(跨场景,不跨 step)。

#### §2.3.1 — 根本需求

**根本需求:** 在**不破坏 V8.6 编号契约(FOUND-08)**的前提下,获得**真实有价值的并行加速**。

**从 paradigm shift 推出:** 决策 #3 不直接涉及 paradigm shift,但与决策 #7(分层 CC)+ 决策 #6(per-agent memory)相关 —— 跨场景并行意味着多个 round table 同时跑,每个 round table 内部仍有 memory conflict 协调(§P7)。V8.6 编号契约(FOUND-08 frozen rule,详见 v3.0 / v5.0 milestone audit)是 v3-v9 五 milestone 守护的核心不变量 —— 任何破坏它的「并行优化」都是 regression,不是优化。

**真实有价值的并行加速:** v9 platform slice(Step 14)证明「跨平台并行」(1 master → 7 variants)是真实加速;同理,「跨场景并行」(同 step,不同 scene)也是真实加速。但「step 内并行」(同 scene 同 step,多个 agent 同时发言)违反 round table 的串行语义(决策 #7 + CC-6 强制串行约束)。

#### §2.3.2 — 候选选项

| 候选 | 描述 | Research source |
|------|------|-----------------|
| **(a) D2 storyboard round-parallel**(CHOSEN) | V8.6 编号保留,orchestrator 层跨场景 dispatch 多个独立 round table | PROJECT.md(锁定)+ STACK §7.5(强制串行约束,CC-6)|
| **(b) D1 step-level parallel** | 同 scene 同 step 内多 agent 并行发言 | FEATURES §2.3 B2.3(nested chat)+ FEATURES §9.3 协作模式速查 |
| **(c) D3 no parallel** | 完全串行 13-step pipeline | (v9 之前的状态) |
| **(d) D2+ nested parallel** | 跨场景并行 + step 内并行混合 | (违反 CC-6 强制串行)|

#### §2.3.3 — Steelman 排除论证

**排除 (b) D1 step-level parallel:** V8.6 编号契约(FOUND-08)要求 step 内严格串行 —— 13 step 是线性 DAG(creative_source → screenplay → character → ... → slice),step 内并行 = 破坏 V8.6 编号。同时,STACK §7.5 + CC-6 finding 显示 GLM 4-key rotation × multi-panelist 并发有硬 ceiling(4 key × 200K TPM ≈ 800K TPM,7 panelist 并发立即撞 ceiling)。**排除理由:违反「V8.6 编号契约(FOUND-08)」根本需求 + 违反 CC-6 强制串行约束。**

**排除 (c) D3 no parallel:** Status quo = 完全串行 13-step pipeline,不获得跨场景并行加速。v9 platform slice(Step 14)已经证明跨平台并行是真实加速 —— 跨场景同理。**排除理由:违反「真实有价值的并行加速」根本需求(放弃已验证的加速机会)。**

**排除 (d) D2+ nested parallel:** D2+ = D1 + D2 混合,既保留 step 内并行又加跨场景并行 —— 违反 CC-6 强制串行 + V8.6 编号契约。**排除理由:同时违反 §2.3.3 (b) + (c) 的排除理由。**

**Steelman 反驳最强候选 (b) D1 step-level parallel:** 「AutoGen GroupChat(FEATURES §2.3 B2.3)支持 nested chat sub-panel,业界已经做了 step 内并行」。**我方回应:** AutoGen GroupChat 的 sub-panel 是「多 agent 协商同一个 step」,不是「step 内并行发言」 —— sub-panel 内部仍是串行 turn-based(§P7 round-table memory conflict 要求)。同时,GLM 4-key rotation 是 v10.0 的硬约束(MEMORY.md `feedback-glm-overload-reduce-concurrency.md` 全局 concurrency==1),任何 step 内并行都会撞 ceiling。

#### §2.3.4 — 锁定选型 + Rationale

**锁定 (a) D2 storyboard round-parallel。**

**Rationale:** D2 是**唯一同时满足 V8.6 编号契约 + 真实并行加速 + CC-6 强制串行**的选项。设计:orchestrator 层(决策 #7 Hermes 控结构)在 storyboard step 完成后,把不同 scene 分发给不同的独立 round table;每个 round table 内部仍按决策 #7 串行(1 panelist 1 turn,顺序 await);跨 round table 之间可以并行(STACK §7.5 估算 ~550K tokens / pipeline run 基于 13 个 round table 串行,跨场景并行可减半 wall-clock 时间)。

**Cross-validation(SUMMARY.md Decision 3):** STACK 不直接覆盖;FEATURES 部分(§2.3 AutoGen nested chat 支持但 sub-panel 内仍串行);ARCHITECTURE 不直接覆盖;PITFALLS 间接警告(CC-6:round table 不能真并发)。

#### §2.3.5 — Cross-Validation Evidence(4 research sources)

| Source | 章节 | 立场 | 引用要点 |
|--------|------|------|----------|
| **STACK** | §7.5 + §11.4(OQ-12)| **间接支持** | 估算 ~550K tokens / pipeline run 基于串行;CC-6 显示 GLM 4-key rotation 是硬约束;round table 内部必须串行,跨 round table 可并行 |
| **FEATURES** | §2.3 B2.3 + §9.3 | **部分支持** | AutoGen GroupChat nested chat 支持 sub-panel;但 sub-panel 内部仍串行;§9.3 协作模式速查显示 round table 模式天然串行 |
| **ARCHITECTURE** | §5.1 + §5.3 | **支持** | Round table state 是 per-project per-round-table(`.runtime/{slug}/round_tables/{id}.json`);lifecycle 是 turn-based 串行,但可同时存在多个 active round table(不同 scene) |
| **PITFALLS** | §P7(round-table memory conflict)| **间接警告** | 跨 round table 之间 memory 冲突需要 coordinator 仲裁;若两 scene 共享 memory(如同角色出场),并行可能放大 §P7 失败模式 |

**决策 #3 状态:** `validated-in-invariant`(STACK + ARCHITECTURE 支持;FEATURES 部分支持;PITFALLS 间接警告有明确缓解路径)。

---

### §2.4 — 决策 4: G2 通用编排框架(kais-movie-pipeline 作首个 sample)

**锁定选型:** 抽象 pipeline orchestration pattern,kais-movie-pipeline 作为首个 sample。

#### §2.4.1 — 根本需求

**根本需求:** **v12+ 扩展 music video / long-form 时不需要重写编排器**。

**从 paradigm shift 推出:** v10.0 paradigm shift 不直接涉及通用框架,但 v3-v9 五 milestone 的实战经验显示:**kais-movie-pipeline(V8.6 13-step)是 v10.0 的首个 sample,不是 v10.0 的全部**。如果编排器与 kais-movie-pipeline 强耦合,v12+ 扩展(音乐视频 / 长 form / 多角色剧情)时需要重写编排器 —— 违反「可演进」根本需求(与决策 #1 同源)。

**G2 vs G1 的根本差异:** G1(kais-movie-pipeline 专属)是 v9 状态;G2(抽象 + sample)是 v10.0 设计目标。G2 的核心是**分离编排逻辑(orchestrator)与 domain 逻辑(pipeline definition)** —— 编排器只懂「round table / agent invocation / state persistence」,不懂「电影 / 音乐视频」。

#### §2.4.2 — 候选选项

| 候选 | 描述 | Research source |
|------|------|-----------------|
| **(a) G2 抽象 + sample**(CHOSEN) | 抽象 pipeline orchestration pattern,kais-movie-pipeline 作首个 sample | PROJECT.md(锁定)+ FEATURES §10(27 borrowable points 作 G2 设计原料)|
| **(b) G1 kais-movie-pipeline 专属** | 编排器直接 hardcode V8.6 13-step | (v3-v9 状态,v12+ 重写成本高) |
| **(c) 直接用 LangGraph** | 用 LangGraph StateGraph 做 v10.0 编排器 | FEATURES §1(LangGraph 是 framework-of-frameworks)|
| **(d) 直接用 MAF AgentWorkflow** | 用 Microsoft Agent Framework 的 AgentWorkflow | FEATURES §2(MAF 是 .NET + Python 双语言)|

#### §2.4.3 — Steelman 排除论证

**排除 (b) G1 kais-movie-pipeline 专属:** G1 = 编排器 hardcode V8.6 13-step,v12+ 扩展 music video / long-form 时需要重写编排器。这违反「v12+ 不重写编排器」根本需求。同时,G1 与决策 #5 α agent form 冲突 —— 如果编排器 hardcode 13-step,agent YAML 的 `tools` 字段无法泛化(每 agent 的 tool 集合依赖具体 step)。**排除理由:违反「v12+ 不重写编排器」根本需求 + 与决策 #5 冲突。**

**排除 (c) 直接用 LangGraph:** LangGraph 是「framework-of-frameworks」(FEATURES §1.1),提供 StateGraph + Checkpointer + Store 原语 —— 但不内置 agent 模板。v10.0 仍需自己设计 agent form(决策 #5 α form)+ memory scope(决策 #6)+ round table 协议(决策 #7)。LangGraph 是 G2 抽象的**借鉴对象**(B1.1 namespace 元组、B1.2 Checkpointer vs Store 双层、B1.3 supervisor 路由器),不是 G2 本身。同时,LangGraph 是 Python 生态(v10.0 Hermes 是 Python,这点兼容);但 LangGraph 的 StateGraph 是图编排,v10.0 的 round table 是 turn-based 协商 —— 抽象层级不匹配。**排除理由:LangGraph 是 G2 的借鉴对象(B1.x),不是 G2 本身;抽象层级不匹配(StateGraph 图编排 vs round table turn-based)。**

**排除 (d) 直接用 MAF AgentWorkflow:** MAF 是 .NET + Python 双语言(FEATURES §2.1),v10.0 是 Python-only —— 引入 MAF 等于引入 .NET 依赖,违反「低故障面」根本需求。同时,MAF 是 Microsoft 主推(2026-04 GA),但 v10.0 是 Kai 个人 agent 平台,不应绑死到单一厂商 framework。**排除理由:违反「低故障面」(.NET 依赖)+ 违反 paradigm-shift-claim-4(agent 是 Hermes-side 独立实体,不是 MAF agent)。**

**Steelman 反驳最强候选 (c) LangGraph:** 「LangGraph 是 LangChain 出品,生态最丰富,StateGraph + supervisor 是 production-proven」。**我方回应:** LangGraph 提供**原语**(StateGraph / Checkpointer / Store),不提供**完整编排器**。v10.0 的 round table + per-agent memory + curator 自进化是 LangGraph 没有的原语 —— 直接用 LangGraph 等于在 LangGraph 上重新实现 v10.0。G2 抽象 + sample 是**借鉴 LangGraph 原语 + 自己设计 v10.0-specific 抽象**,这才是「站在巨人肩膀上」而非「绑死到巨人身上」。

#### §2.4.4 — 锁定选型 + Rationale

**锁定 (a) G2 抽象 + sample。**

**Rationale:** G2 是**唯一同时满足 v12+ 不重写 + 保持 v10.0 paradigm shift 完整性**的选项。G2 的核心是分离编排逻辑(`agent/agent_registry.py` + `agent/agent_dispatcher.py` + `mcp_serve.py` 7 个 round table tool)与 domain 逻辑(`kais-hermes-skills` repo 的 15 expert YAML + kais-movie-pipeline 定义)。v12+ 扩展 music video 时,只需新增 music-video-specific agent YAML + music-video pipeline 定义,编排器不动。

**Cross-validation(SUMMARY.md Decision 4):** FEATURES 核心支持(§10 的 27 borrowable points 是 G2 的设计原料);ARCHITECTURE 支持(§4 sibling registry + §5 round-table state layer 是 G2 的 Hermes 实例化);STACK / PITFALLS 间接支持。

#### §2.4.5 — Cross-Validation Evidence(4 research sources)

| Source | 章节 | 立场 | 引用要点 |
|--------|------|------|----------|
| **STACK** | (不直接覆盖) | **间接支持** | STACK 调研 MCP 协议层,G2 是编排框架抽象;但 STACK §3.2 的 7 个 MCP tool 是 G2 编排器的 agent-facing API |
| **FEATURES** | §10(27 borrowable points)| **核心支持** | 27 个 borrowable points(B1.x LangGraph / B2.x MAF / B3.x CrewAI / B4.x Claude Agent SDK / B5.x Swarm / B6.x Camel-AI / B7.x MCP / B8.x A2A)是 G2 的设计原料;§11 anti-features 是 G2 显式拒绝的 negative design space |
| **ARCHITECTURE** | §4 + §5 | **支持** | §4.1 sibling registry pattern + §5.1 round table state layer 是 G2 在 Hermes 内的实例化;§7 Patterns to Follow(§7.1 sibling registry / §7.2 additive curator phase / §7.3 filter-based memory scoping / §7.4 project slug)是 G2 的设计模式 |
| **PITFALLS** | §P1-§P14(全文)| **间接支持** | 整个 PITFALLS 是 G2 必须处理的失败模式;G2 设计必须为每条 pitfall 提供字段级或协议级缓解 |

**决策 #4 状态:** `validated-in-invariant`(FEATURES 核心支持,ARCHITECTURE 支持;STACK / PITFALLS 间接支持;PROJECT.md paradigm shift 提供主要论据)。

---

### §2.5 — 决策 5: α agent form(YAML + persona + tools + refs + memory_scope + lineage)

**锁定选型:** YAML + persona prompt + tools + refs + memory_scope + lineage,物理位置 `~/.hermes/agents/{name}.agent.yaml`。

> **这是 7 决策中最 load-bearing 的推导。** 决策 #5 定义「agent 是什么」—— 是 v10.0 paradigm shift 最核心的载体(paradigm-shift-claim-2 / claim-4)。

#### §2.5.1 — 根本需求

**根本需求:** agent 是**有持久身份、有记忆、可自进化的实体**,不是 prompt 模板。

**从 paradigm shift 推出:** paradigm-shift-claim-2 声明「Agent 与 SKILL 分层」—— SKILL body 是 user-message prompt injection(imperative-second-person: "You are X. Do Y."),agent persona 是 system-prompt fragment(first-person: "I am X. I do Y.")。paradigm-shift-claim-4 声明「Agent 是 Hermes-side 独立 YAML 实体,有 per-agent memory + 自进化能力」—— 这是 v10.0 paradigm shift 最核心的诉求。

**「实体 vs 模板」的根本差异:** 模板(SKILL)是静态 markdown,每次调用从零开始;实体(agent)有持久身份(name + persona + lineage)、有记忆(per-agent memory_scope)、可自进化(evolution_log + fitness_score + curator-driven memory updates)。**业界没有任何主流框架把这三个属性作为原生组合**(FEATURES §9.2 memory 模式速查表)—— v10.0 是真正的差异化设计。

#### §2.5.2 — 候选选项

| 候选 | 描述 | Research source |
|------|------|-----------------|
| **(a) α YAML-first Hermes-side**(CHOSEN) | `~/.hermes/agents/{name}.agent.yaml`,18-field schema(ARCHITECTURE §1.1) | ARCHITECTURE §1(18-field schema)+ §2(15-expert transform mapping)|
| **(b) Claude Agent SDK subagent `.claude/agents/*.md`** | filesystem subagent,Markdown + YAML frontmatter | FEATURES §4 B4.1 + §11 row 1 |
| **(c) CrewAI role/goal/backstory JSONC** | CrewAI agents/<name>.jsonc,30+ 字段 | FEATURES §3 B3.1 + §3.3 |
| **(d) LangGraph Python class** | `@node` 装饰器 + StateGraph | FEATURES §1.1 |
| **(e) A2A Agent Card** | JSON Agent Card,通过 URL 发布 | FEATURES §8 B8.1 |

#### §2.5.3 — Steelman 排除论证

**排除 (b) Claude Agent SDK subagent `.claude/agents/*.md`:** 这是 Kimi 方案的形态,**最需要显式否决**。Claude Agent SDK subagent 有三个属性违反「agent 是有持久身份、有记忆、可自进化的实体」根本需求:

1. **Subagent default context-isolated**(FEATURES §4.3 + B4.1):「The only channel from parent to subagent is the Agent tool's prompt string」—— subagent 不天然适合做 round table panelist(panelist 需要看完整历史)。**违反「持久身份」根本需求**(身份不连续,每次 invocation 是新 context)。
2. **`memory` 字段不是 namespace scoped**(FEATURES §4.3 + B4.1):`memory: 'user' | 'project' | 'local'` 是 source-scoped(从哪个 CLAUDE.md 加载),不是 agent-scoped(每个 agent 独立 namespace)。**违反「有记忆」根本需求**(无法 per-agent namespace 隔离)。
3. **Subagent transcripts 30 天自动清理**(FEATURES §4.3):跨项目经验持久化不稳定,30 天后 transcript 消失。**违反「可自进化」根本需求**(没有跨项目累积的 evolution_log)。

**排除理由:三条同时违反根本需求(context-isolated / memory 不 namespace scoped / 30 天 TTL)—— 这是 elimination-by-fundamental-constraint,不是「业界用 subagent 我们不用」式类比论证。**

**排除 (c) CrewAI role/goal/backstory JSONC:** CrewAI 的 30+ 字段表(FEATURES §3.3)是「industry standard」但太厚 —— 维护成本高,且 `memory: true` boolean flag 不够细(无 per-agent namespace,FEATURES §3.3 B3.3)。CrewAI 的 role/goal/backstory 三件套是**最小必需**(可作 v10.0 persona 字段的子集参考,B3.1),但完整形态违反「可维护性」+「per-agent namespace」根本需求。**排除理由:30+ 字段过厚(维护成本高)+ memory boolean 不 namespace scoped(违反决策 #6)。**

**排除 (d) LangGraph Python class:** LangGraph agent 是 Python 函数(`@node` 装饰器,FEATURES §1.1),没有原生 YAML 格式。这违反 paradigm-shift-claim-4「Agent 是 Hermes-side 独立 YAML 实体」—— Python class 是 code-as-config,operator 改 agent 需要改 Python 代码,违反「operator-owned」(agent YAML 应像 SKILL.md 一样 operator 可直接编辑)。**排除理由:Python class 不是 YAML(违反 paradigm-shift-claim-4 独立 YAML 实体);operator 不可直接编辑。**

**排除 (e) A2A Agent Card:** Agent Card 是 JSON 描述 capability / inputs / outputs(FEATURES §8.1),用于 cross-vendor discovery。但 Agent Card **只描述 capability,不描述 persona**(FEATURES §9.1)—— 这违反「agent 是有持久身份」根本需求。同时,A2A 是跨厂商协议,引入 A2A Agent Card 等于引入跨厂商 discovery 开销,违反决策 #1「低故障面」根本需求。**排除理由:Agent Card 只描述 capability,不描述 persona(违反「持久身份」)+ 引入跨厂商协议开销(违反决策 #1)。**

**Steelman 反驳最强候选 (b) Claude Agent SDK subagent:** 「Claude Agent SDK 是 Anthropic 官方推荐,Kimi 方案用它,等于『Anthropic 背书 + Kimi 验证』」。**我方回应:** 这是**类比论证**(§1.1 加严规则显式拒绝)。三个具体失败模式(context-isolated / memory 不 scoped / 30 天 TTL)是 Anthropic 官方 docs 明确说的(FEATURES §4.3 引用 code.claude.com 官方 docs),不是我们的臆测 —— 这些失败模式直接违反 v10.0 paradigm shift 三件套(持久身份 + per-agent memory + 自进化)。「Anthropic 推荐」不等于「适合 v10.0 paradigm」—— Anthropic 推荐 subagent 是为了「task delegation」场景(主 agent 调 subagent 做子任务),不是「round table 协商 + per-agent memory + curator 自进化」场景。

#### §2.5.4 — 锁定选型 + Rationale

**锁定 (a) α YAML-first Hermes-side。**

**Rationale:** α form 是**唯一同时满足持久身份 + per-agent memory + 自进化 + operator-owned**的形态。18-field schema(ARCHITECTURE §1.1)的字段级实现:`persona`(system-prompt fragment,非 user-message)+ `tools`(runtime whitelist)+ `refs`(RAG reference)+ `memory_scope`(per_agent / shared / project_scoped)+ `lineage`(从 SKILL 转化的溯源)+ `evolution_log`(curator-driven memory updates)+ `fitness_score`(quality metric)。物理位置 `~/.hermes/agents/{name}.agent.yaml` 是 paradigm-shift-claim-4「Hermes-side 独立 YAML 实体」的字段级实现。

**Cross-validation(SUMMARY.md Decision 5):** STACK 支持(§3.2 Tool 1 假设此形态);FEATURES 强支持(§3 CrewAI / §4 Claude Agent SDK 对照后,v10.0 的 YAML-first + persona + memory_scope + lineage 是业界独有组合;§11 显式否决 Claude Agent SDK subagent);ARCHITECTURE 强支持(§1 18-field schema + §2 15-expert transform mapping);PITFALLS 修正(§P1 persona drift 要求 `persona_sha256` + tiered memory)。

#### §2.5.5 — Cross-Validation Evidence(4 research sources)

| Source | 章节 | 立场 | 引用要点 |
|--------|------|------|----------|
| **STACK** | §3.2 Tool 1 `get_agent_persona` | **支持** | Tool schema 假设 `~/.hermes/agents/{agent_id}.agent.yaml` 存在;input validation `^[a-z0-9_-]+$` regex;`AgentPersonaResult` Pydantic Model |
| **FEATURES** | §3 + §4 + §9.1 + §11 + §12 | **强支持** | §3 CrewAI / §4 Claude Agent SDK 对照 → v10.0 YAML-first + persona + memory_scope + lineage 是业界独有组合(§9.1 速查表);§11 row 1 显式否决 subagent 形态;§12.2 Differentiators 列出 `lineage` 是「无业界先例」|
| **ARCHITECTURE** | §1.1(18-field schema)+ §2(15-expert transform) | **强支持** | 18-field schema 完整规范;15-expert transform mapping 5-field pattern(COPY / DROP / REWRITE / FLATTEN / DERIVE / INITIALIZE);FOUND-08 preservation rule(expert_id copy verbatim) |
| **PITFALLS** | §P1(persona drift) | **修正** | 18-field schema 不够 —— 必须加 `persona_sha256`(P1 mitigation 1)+ `core_memory` / `archival_memory` tiered memory(P1 mitigation 3);这些字段在 01-AGENT-REGISTRY-SCHEMA.md 中固化 |

**决策 #5 状态:** `validated-in-invariant`(4 research source 一致强支持;PITFALLS 修正已在 01-AGENT-REGISTRY-SCHEMA.md scope 内)。

#### §2.5.6 — 决策 #5 字段级实现(供 01-AGENT-REGISTRY-SCHEMA.md 引用)

18-field schema(ARCHITECTURE §1.1)是决策 #5 的字段级实现。下表列出与「持久身份 + per-agent memory + 自进化 + operator-owned」根本需求对应的字段:

| 根本需求 | 对应字段 | 字段说明 |
|---------|---------|---------|
| 持久身份 | `name` + `persona` + `expert_id` | name 是稳定标识(`[a-z0-9_-]+`);persona 是 first-person system-prompt fragment(非 user-message);expert_id 是 v1-v9 backward-compat anchor(FOUND-08) |
| 持久身份(不变量保护) | `persona_sha256`(P1 修正) | 冻结 persona 内容的 sha256;curator-driven patches MUST NOT alter persona section(`_check_persona_section_intact` AST check) |
| per-agent memory | `memory_scope` + `lineage` | memory_scope: `shared` / `per_agent` / `project_scoped`(决策 #6 物理载体);lineage: 溯源到 SKILL.md + skill_sha256 |
| per-agent memory(分层) | `core_memory` / `archival_memory` 字段(P1 修正,在 memory-record-schema) | core_memory: 小、persona-aligned、手动 curated,projected into system prompt;archival_memory: 大、auto-curated,retrieved on demand |
| 自进化 | `evolution_log` + `fitness_score` | evolution_log: append-only `{ts, sha256, diff_summary, fitness_delta, trigger}` chain(tamper-evident);fitness_score: 0.0-1.0 rolling quality,null 直到首次 curator pass |
| 自进化(curator-driven) | `_memory_evolution_phase`(ARCHITECTURE §3.4) | curator `run_curator_review` 加第三 phase(在 `_feedback_scan_phase` 之后),LLM-distill memory delta,append 到 evolution_log |
| operator-owned | 物理位置 `~/.hermes/agents/{name}.agent.yaml` + `default_invocation` | operator 直接编辑 YAML(无需改 Python 代码);default_invocation: `mcp_tool` / `skill_fallback` / `disabled`(SKILL 形态作 fallback 保留) |

**关键设计决策(供 01 引用):**

- **`persona` 不是 SKILL body copy-paste(ARCHITECTURE §8.1 anti-pattern):** SKILL body 是 user-message(imperative-second-person: "You are X. Do Y.");persona 是 system-prompt fragment(first-person: "I am X. I do Y.")。混合 register 违反 paradigm-shift-claim-2。
- **`tools` 是 runtime whitelist,与 `prerequisites.tools` 不同(ARCHITECTURE §1.1 field 5 + field 12):** tools 是 runtime grants(被 dispatcher 强制);prerequisites.tools 是 activation conditions(声明依赖,不强制)。两者不可混淆。
- **`lineage` 是 v10.0 独创(无业界先例,FEATURES §12.2 Differentiators):** 支持溯源审计 + curator drift detection(`_detect_skill_agent_drift` 在 ARCHITECTURE §6.2);operator 改 SKILL.md 后,curator 检测 sha256 drift,advisory(不自动 re-transform,防覆盖 operator 调整)。
- **`evolution_log` 是 tamper-evident chain(类比 v6.0 `agent/curator_audit.py`):** 每条 entry 的 sha256 = sha256(prev_entry.sha256 + new_delta);篡改历史 entry 会破坏 chain,`hermes curator audit-log --verify` 检测。

#### §2.5.7 — 决策 #5 失败模式 + 01-AGENT-REGISTRY-SCHEMA.md 衍生论据

决策 #5 在 v11.0 PoC 实施时可能遇到以下失败模式(每个有字段级缓解,在 01 中固化):

| 失败模式 | PITFALLS reference | 字段级缓解(在 01 固化) |
|---------|-------------------|------------------------|
| persona drift(accumulated memory 稀释 persona) | §P1 | `persona_sha256` 不变量 + tiered memory(core/archival)+ persona-drift probe(每 50 runs 跑 benchmark) |
| YAML 作 prompt dump(把 SKILL body copy-paste 到 persona) | ARCHITECTURE §8.1 | persona 长度限制 5-15 lines + first-person 语法检查 |
| auto-re-transform on drift(自动覆盖 operator 调整) | ARCHITECTURE §8.2 | drift 触发 advisory(不自动 re-transform);operator 决定是否 re-transform |
| subagent 形态(违反 paradigm-shift-claim-1) | §3 row 1 + §4.3 B4.1 | 物理位置 `~/.hermes/agents/*.agent.yaml`(非 `.claude/agents/`)+ dispatch via MCP tool(非 subagent) |
| expert_id 静默重命名(违反 FOUND-08) | ARCHITECTURE §2 + v3-v9 audit | expert_id 字段 verbatim copy + lineage.derived_from_skill_id 溯源 |

**01-AGENT-REGISTRY-SCHEMA.md 应 derive(不在 00 范围):**
- 18-field schema 的 JSON Schema 正式定义(`agents-schema.yaml`,OQ-14)
- memory-record-schema(`expires_at` / `verified_at` / `supersedes_memory_id` / `confidence` / `half_life_days` / `evidence_chain` / `evidence_operator_ids` / `status` / `confidentiality` / `scope`)
- 15 expert 5-field transform 映射表(从 ARCHITECTURE §2 拷贝)
- `tools` 字段是否枚举(OQ-13: YES,runtime whitelist enforced by dispatcher)
- `persona_sha256` 不变量的 AST check 实现
- core_memory / archival_memory 分层 memory tier 规范

**01-AGENT-REGISTRY-SCHEMA.md 不应 re-derive(已 locked 在 00):**
- 决策 #5 推导链(§2.5)
- subagent 形态否决(§3 row 1 + §4.3 B4.1)
- 18-field schema 字段集(已在 ARCHITECTURE §1.1 定义,01 只做 JSON Schema 形式化)

---

---

### §2.6 — 决策 6: per-agent memory + curator-driven 自进化

**锁定选型:** per-agent scoped memory(扩展 mem0 backend),curator 驱动跨项目自进化。

> **这是 7 决策中 v10.0 paradigm shift 最核心的诉求实现**(paradigm-shift-claim-4: agent 有 per-agent memory + 自进化能力)。

#### §2.6.1 — 根本需求

**根本需求:** **agent 随项目越多越有经验**(v10.0 paradigm shift 核心诉求)。

**从 paradigm shift 推出:** paradigm-shift-claim-4 声明「Agent 是 Hermes-side 独立 YAML 实体,有 per-agent memory + 自进化能力」。这个声明有两层:(a) per-agent memory —— 每个 agent 有独立的 namespace(不是 shared global memory);(b) 自进化 —— agent 通过项目经验累积,自动改进(不是 operator 手动 curate)。

**与 v1-v9 对比:** v1-v9 的 movie-experts SKILL 是静态知识层(operator 手动 curate refs);v6.0 引入反馈闭环(`agent/curator.py:_feedback_scan_phase`),但是 **skill-level feedback-driven evolution**,不是 per-agent memory。v10.0 是**第一次**引入 per-agent memory + curator-driven 自进化 —— 这是 v10.0 的核心差异化(FEATURES §9.2 显示业界没有原生组合)。

#### §2.6.2 — 候选选项

| 候选 | 描述 | Research source |
|------|------|-----------------|
| **(a) per-agent mem0 namespace + curator**(CHOSEN) | 单 mem0 backend + `agent_id` filter 路由 + curator `_memory_evolution_phase` | ARCHITECTURE §3.1 + §3.2 Option B + §3.4 + SUMMARY.md Decision 6 |
| **(b) per-agent mem0 workspace(物理分区)** | 每 agent 一个 mem0 workspace | PITFALLS §P3 mitigation 1(物理分区 over 逻辑过滤)|
| **(c) shared memory** | 所有 agent 共享 global memory,无 per-agent scope | (违反 per-agent 根本需求) |
| **(d) LangGraph Store namespace tuple** | 用 LangGraph Store 的 namespace 元组做 per-agent scope | FEATURES §1.3 B1.1 |
| **(e) CrewAI boolean memory flag** | `memory: true` boolean,无 namespace | FEATURES §3.3 B3.3 |

#### §2.6.3 — Steelman 排除论证

**排除 (b) per-agent mem0 workspace(物理分区):** 物理分区是 PITFALLS §P3 mitigation 1 推荐的方案,但在 v11.0 PoC 规模(15 agent × 单项目)是**过度工程化** —— 15 个 mem0 workspace 意味着 15 套 collection + 15 套 API key + 15 套 rate limit。ARCHITECTURE §3.2 Option B(filter 路由)在 v11.0 PoC 规模完全够用(mem0 server-side filter 是 O(1))。物理分区是 v12+(50+ agent × 100+ project)的迁移触发条件(CC-4 finding),不是 v10.0 的选型。**排除理由:v11.0 PoC 规模过度工程化(CC-4 明确「v11.0 PoC: Option B;v12+: 物理分区」)。**

**排除 (c) shared memory:** Shared memory = 所有 agent 看同一份 memory,无 namespace 隔离。这违反 paradigm-shift-claim-4「per-agent memory」—— 决策 #6 根本需求是「agent 随项目越多越有经验」,shared memory 等于「所有 agent 共享同一份经验」,无法区分 screenplay 的经验 vs cinematographer 的经验。同时违反 §P4(cross-project leakage)+ §P12(cross-agent contamination)。**排除理由:违反 paradigm-shift-claim-4 + 违反 §P4 + §P12。**

**排除 (d) LangGraph Store namespace tuple:** LangGraph Store 用 namespace 元组做 per-agent scope 是干净的(B1.1 borrowable point),但 LangGraph 是 Python framework,v10.0 已经选 mem0 作 memory backend(v7.0 ship)—— 换 backend = 推倒 v7.0 硬化产出,违反「保留硬化产出」根本需求(与决策 #2 同源)。同时,LangGraph Store 没有 curator-driven 自进化(v10.0 paradigm shift 核心诉求)。**排除理由:换 backend 违反「保留 v7.0 mem0 硬化产出」+ 无 curator-driven 自进化。**

**排除 (e) CrewAI boolean memory flag:** `memory: true` 是 boolean(FEATURES §3.3 B3.3),无 namespace 概念,memory 跨 agent 可能串扰。这违反 paradigm-shift-claim-4「per-agent memory」。**排除理由:boolean flag 不 namespace scoped(违反 per-agent memory 根本需求)。**

**Steelman 反驳最强候选 (b) 物理分区:** 「PITFALLS §P3 明确说物理分区 over 逻辑过滤,mem0 HNSW 全局图 + post-filter 在 18-agent × 100-project 规模会崩溃」。**我方回应:** PITFALLS §P3 说的「崩溃」是**规模触发**的(900K records),不是 v11.0 PoC 规模(15 agent × 单项目 × <500 records = <7.5K records)。CC-4 finding 明确「v11.0 PoC: Option B(filter 路由);v12+(50+ agent × 100+ project): 物理分区」—— 物理分区是 v12+ 的迁移触发条件,不是 v10.0 设计选型。v10.0 设计文档(06-CROSS-REPO-IMPACT.md)记录迁移触发条件,v11.0 PoC 用 Option B。

#### §2.6.4 — 锁定选型 + Rationale

**锁定 (a) per-agent mem0 namespace + curator。**

**Rationale:** Option B 是**唯一同时满足 v11.0 PoC 规模 + 保留 v7.0 mem0 硬化产出 + curator-driven 自进化**的选项。设计:mem0 backend 单实例(v7.0 ship);`agent_id` filter 路由(ARCHITECTURE §3.2 Option B 的 `_read_filters()` / `_write_filters()` additive extension);curator `_memory_evolution_phase`(类比 v6.0 `_feedback_scan_phase`,ARCHITECTURE §3.4)在 feedback-scan 之后跑,LLM-distill memory delta,append 到 agent YAML 的 `evolution_log`。

**关键事实(ARCHITECTURE §3.1):** mem0 v7.0 backend 的 `_write_filters()` 已经返回 `{"user_id", "agent_id"}` —— writes 已经 agent-attributed。**per-agent memory 是路由约定,不是 backend change**。读路径是 gap(`_read_filters()` 只返 `user_id`),需要 additive extension(§3.3)。

**Cross-validation(SUMMARY.md Decision 6):** STACK 支持(§3.2 Tool 3/6 假设 mem0 backend 已 per-agent scope,但 filter 行为未实测 — M 置信);FEATURES 强支持(§9.2 显示业界没有原生组合, v10.0 是真正差异化);ARCHITECTURE 强支持 + 修正(§3.1-§3.4 完整推导 + §3.4 curator phase);PITFALLS 核心警告(整个 PITFALLS 都是 #6 失败模式,7 个 load-bearing pitfalls P1/P2/P4/P5/P6/P8/P10)。

#### §2.6.5 — Cross-Validation Evidence(4 research sources)

| Source | 章节 | 立场 | 引用要点 |
|--------|------|------|----------|
| **STACK** | §3.2 Tool 3 `get_agent_memory` + Tool 6 `query_memory` | **支持(M 置信)** | Tool schema 假设 mem0 backend 已 per-agent scope;`scope: Literal["agent", "lineage", "global"]` 字段;但 mem0 Platform API 真实 filter 行为未实测(OQ-12 gap)|
| **FEATURES** | §9.2 memory 模式速查表 + §11 row 6 | **强支持(差异化)** | §9.2 显示业界没有任何主流框架把 per-agent scoped memory + curator-driven 自进化作为原生组合;§11 row 6 显式否决 `memory: true` boolean flag;v10.0 是真正的差异化设计点 |
| **ARCHITECTURE** | §3.1-§3.4 | **强支持 + 修正** | §3.1 现有 mem0 `_read_filters()` 只返 `user_id`,需 §3.3 additive extension 加 `_scoped_agent_id`;§3.4 curator 加 `_memory_evolution_phase`;§3.2 Option B vs Option C 推导 |
| **PITFALLS** | §P1-§P14(全文,7 个 load-bearing) | **核心警告** | P1 persona drift / P2 stale memory / P4 cross-project leakage / P5 curator failure / P6 memory poisoning / P8 no fitness signal / P10 privacy —— 全部 load-bearing,01-AGENT-REGISTRY-SCHEMA.md 必须固化字段级缓解 |

**决策 #6 状态:** `validated-in-invariant`(4 research source 一致支持;PITFALLS 7 个 load-bearing pitfall 是 v11.0 PoC 硬风险,01-AGENT-REGISTRY-SCHEMA.md + 05-POC-PLAN.md 解决)。

#### §2.6.6 — 决策 #6 字段级实现(供 01-AGENT-REGISTRY-SCHEMA.md 引用)

per-agent memory + curator-driven 自进化的字段级实现涉及**两个 schema 层**(CC-2 finding):

| Schema 层 | 字段(供 01 引用) | 说明 |
|-----------|------------------|------|
| **agent YAML schema**(18-field) | `memory_scope` + `evolution_log` + `fitness_score` | 见 §2.5.6 |
| **memory-record schema**(独立,CC-2 gap) | `expires_at` / `verified_at` / `supersedes_memory_id` / `confidence` / `half_life_days` / `evidence_chain` / `evidence_operator_ids` / `status` / `confidentiality` / `scope` | **18-field agent YAML 不包含这些字段**(CC-2 finding);01 必须显式区分两层 schema |

**memory-record schema 10 字段(每个对应一个 load-bearing pitfall,在 01 固化):**

| 字段 | 对应 pitfall | 字段说明 |
|------|-------------|---------|
| `expires_at: datetime \| None` | §P2 stale memory | domain-rule memory 默认 `now + 90 days`;preference memory `None`(永不过期);retrieve-time filter `WHERE expires_at IS NULL OR expires_at > now()` |
| `verified_at: datetime` + `verification_source: str` | §P2 | 类比 v1 ref `verified_date` convention;curator 周期性 re-verification pass(90 天触发) |
| `supersedes_memory_id: str \| None` | §P2 + v6.0 supersession | 显式失效:新 memory 写入时标记被替代的旧 memory ID;retrieve-time filter 排除 superseded |
| `confidence: float [0,1]` + `half_life_days: int` | §P2 | time-decay:`confidence(now) = base * exp(-age_days / half_life_days)`;domain rules `half_life_days=90`;preferences `half_life_days=3650`;`<0.1` auto-archive |
| `evidence_chain: list[feedback_record_id]` | §P5 curator failure | 每条 curator-generated memory 必须有 ≥3 distinct feedback records 支持;`_check_evidence_coverage` embedding cosine ≥ 0.7 验证 |
| `evidence_operator_ids: list[str]` | §P5 + §P6 | operator 多样性:至少 2 distinct operators(防 bias amplification + poisoning);`hermes curator stats --bias-audit` 暴露 over-represented operators |
| `status: "active" \| "archived" \| "quarantined"` | §P5 + §P6 | curator 只 archive(never hard-delete);quarantine on detected poisoning(outlier detection flags operator) |
| `confidentiality: "public" \| "internal" \| "confidential" \| "nda"` | §P10 privacy | 默认 `internal`;`confidential` / `nda` 排除 cross-project retrieval(即使 scope=global);redact in stats JSON output |
| `scope: "global" \| "project" \| "session"` | §P4 cross-project leakage | 默认 `project`(conservative);`global` 需 curator review + operator approval(3+ distinct projects cited + LLM confidence ≥ 0.8) |
| `project_id: str` (required) | §P4 + §P10 | API contract: `retrieve(query, agent_id, project_id)` — project_id required(非 optional);round-table protocol 强制传 project_id 给每 participant |

**per-agent memory tier(三层,P1 mitigation 3 + §P9 size growth):**

| Tier | 上限 | 注入方式 | curator 可写? |
|------|------|---------|----------------|
| `core_memory`(persona-aligned,手动 curated) | ≤10 records | always projected into system prompt | NO(operator approval required,类比 v6.0 bundled-skill gating) |
| `working_memory`(recent operational context) | ≤100 records | retrieved on demand via mem0 search, top-5 injected | YES(curator `_memory_evolution_phase`) |
| `archival_memory`(long-term archive) | ≤10000 records(or per `memory.max_records: 500` hard cap,P3 mitigation 3) | retrieved only via explicit `memory_recall` tool for deep research | YES(curator compaction pass) |

#### §2.6.7 — 决策 #6 curator `_memory_evolution_phase` 字段契约

curator `_memory_evolution_phase`(ARCHITECTURE §3.4)类比 v6.0 `_feedback_scan_phase`,执行顺序 + dry-run-by-default + try/except 隔离边界(OQ-16 在 01 解决):

**执行顺序(在 `run_curator_review._llm_pass()` 中):**

1. `_consolidate_pass`(已有,umbrella-building LLM fork)
2. `_feedback_scan_phase`(v6.0 ship,scan FeedbackStore for new feedback)
3. **`_memory_evolution_phase`(v10.0 NEW,walk `~/.hermes/agents/*.agent.yaml` for per-agent memory updates)**

**`_memory_evolution_phase(start: datetime) -> Dict[str, Any]` per-agent 流程:**

1. Aggregate feedback for this agent from `FeedbackStore`(扩展 `_scan_for_hot_skills` 同时 scan agent_ids)
2. Compute `fitness_delta` from new feedback verdicts since last `evolution_log` entry(用 v6.0 `_compute_confidence` two-signal gate: `mean_delta` + `evidence_count`)
3. If `fitness_delta >= threshold`(default `0.1`):generate LLM-distilled **memory delta**(single concise fact)
4. Append to `evolution_log`:`{ts, sha256(prev_entry + new_delta), diff_summary, fitness_delta, trigger: "feedback_scan"}`
5. Optionally write to mem0 via `mem0_conclude` scoped to this agent's `agent_id`

**dry-run-by-default 不变量(类比 v6.0 CURATOR_DRY_RUN_BANNER):**

- curator memory-write path **dry-run by default**,requires explicit `--apply-memory` flag for live writes
- AST-walk invariant(`TestNonBypassableHumanInLoop` 扩展):`apply_memory_delta` only callable from `hermes_cli/curator.py:_cmd_apply_memory`(single caller)
- 失败隔离:per-phase try/except 包裹,失败不阻塞其他 phase

#### §2.6.8 — 决策 #6 失败模式 + 01/05 衍生论据

| 失败模式 | PITFALLS reference | 缓解所在 doc |
|---------|-------------------|------------------|
| persona drift(accumulated memory 稀释 persona) | §P1 | 01(`persona_sha256` + tiered memory) |
| stale memory(cites obsolete rules) | §P2 | 01(`expires_at` / `verified_at` / `supersedes_memory_id` / `confidence` / `half_life_days`) + 05(re-verification pass) |
| scoped retrieval perf collapse | §P3 | 05(latency SLO p95 < 500ms acceptance criterion) + 06(per-agent workspace migration trigger) |
| cross-project leakage | §P4 | 01(`scope: global\|project\|session` + `project_id` required) + 02(propagate project_id) |
| curator failure(false-delete / hallucinate / bias amplify) | §P5 | 01(`evidence_chain` + `evidence_operator_ids`) + 05(bias canary) |
| memory poisoning(MINJA-style persistent attack) | §P6 | 01(`operator_signature` HMAC + `status="quarantined"`) + 05(outlier detection) + 06(operator key management) |
| no fitness signal(can't tell if getting better) | §P8 | 01(`fitness_battery` field + `fitness_trend.jsonl`) + 05(regression auto-quarantine) |

**01-AGENT-REGISTRY-SCHEMA.md 应 derive(不在 00 范围):**
- `agents-schema.yaml`(JSON Schema 形式化,18-field + persona_sha256 + memory tier)
- `memory-record-schema.yaml`(独立 schema,10 字段 + 3-tier memory 规范)
- 15 expert 5-field transform 映射表
- OQ-1(persona 版本控制):diff only + memory record 带 persona_sha256 快照
- OQ-4(fitness_score 冷启动):null = neutral 0.5 for ordering,UI 显示 "untested"
- OQ-7(memory.max_records):default 500,curator 每 N tick compaction pass
- OQ-13(tools 字段枚举):YES,runtime whitelist enforced by dispatcher
- OQ-14(JSON Schema 正式定义):YES,`agents-schema.yaml` 文件
- OQ-16(curator evolution phase 边界):见 §2.6.7

**01-AGENT-REGISTRY-SCHEMA.md 不应 re-derive(已 locked 在 00):**
- 决策 #6 推导链(§2.6)
- per-agent memory + curator-driven 自进化 是 v10.0 差异化(FEATURES §9.2)
- 7 load-bearing pitfall 列表(P1/P2/P4/P5/P6/P8/P10)

---

---

### §2.7 — 决策 7: (vi) 分层 CC 角色(Hermes 控结构,CC 控内容)

**锁定选型:** Hermes 控 turn_order / max_rounds / schema / early_stop_rule;CC 控 question framing + synthesis。

#### §2.7.1 — 根本需求

**根本需求:** **审计性 + 可重现 + token 成本可控 + 充分用 CC 推理能力**。

**从 paradigm shift 推出:** paradigm-shift-claim-1 声明「Hermes 是 agent 容器,CC 仅是场地」+ paradigm-shift-claim-3 声明「CC Team Lead 配置极薄」。这两条 paradigm shift 要求 Hermes 与 CC 之间有**清晰的控制权分工** —— 不是 CC 全控(违反 paradigm-shift-claim-1),也不是 Hermes 全控(违反「充分用 CC 推理能力」,CC 是场地 = CC 在场地内仍要有推理自主权)。

**「单层全控」的失衡:**
- CC 全控(i):Hermes 失去对 turn_order / max_rounds / schema 的控制,无法审计 + 无法重现 + token 成本失控(CC 自己决定调多少次 LLM)。
- Hermes 全控(ii):失去 CC 推理能力(CC 沦为被动作答,不能 question framing / synthesis)。

(vi) 分层是**两者之间的平衡**:Hermes 控「结构」(turn_order / max_rounds / schema / early_stop_rule),CC 控「内容」(question framing / synthesis)。

#### §2.7.2 — 候选选项

| 候选 | 描述 | Research source |
|------|------|-----------------|
| **(a) (vi) 分层**(CHOSEN) | Hermes 控结构,CC 控内容 | PROJECT.md(锁定)+ ARCHITECTURE §5.3 lifecycle + SUMMARY.md Decision 7 |
| **(b) (i) CC 全控** | CC 决定 turn_order / max_rounds / 何时 synthesizer | (Kimi 方案倾向)|
| **(c) (ii) Hermes 全控** | Hermes 决定 question framing + synthesis 内容 | (违反「充分用 CC 推理能力」) |
| **(d) LangGraph supervisor pattern** | LangGraph supervisor 是路由器,worker agent 是干活 | FEATURES §1.3 B1.3 |

#### §2.7.3 — Steelman 排除论证

**排除 (b) (i) CC 全控:** CC 全控 = Hermes 沦为被动的 MCP tool provider,无法控制 turn_order / max_rounds / schema / early_stop_rule。这违反「审计性」根本需求(无法重现 round table —— CC 每次决策不同)+ 「可重现」根本需求(无固定 turn_order)+ 「token 成本可控」根本需求(CC 决定调多少次 LLM,Hermes 无法预算)。同时,违反 paradigm-shift-claim-1「Hermes 是 agent 容器」—— 如果 CC 全控,CC 才是 agent 容器,Hermes 沦为 tool。**排除理由:违反「审计性 / 可重现 / token 成本可控」+ 违反 paradigm-shift-claim-1。**

**排除 (c) (ii) Hermes 全控:** Hermes 全控 = Hermes 决定 question framing + synthesis 内容,CC 沦为被动作答。这违反「充分用 CC 推理能力」根本需求 —— CC 是 Anthropic 顶级 reasoning 模型,question framing(把 round table 问题分解为 per-panelist question)+ synthesis(综合多 panelist 意见成决策)是 CC 的强项。Hermes 全控等于浪费 CC 能力。**排除理由:违反「充分用 CC 推理能力」根本需求。**

**排除 (d) LangGraph supervisor pattern(直接套用):** LangGraph supervisor 是路由器(FEATURES §1.3 B1.3),与决策 #7 同构 —— 「Hermes 像 LangGraph supervisor(路由),CC 像 worker agent(干活)」。但 LangGraph supervisor 是 Python framework,v10.0 已经选 T6 MCP 协议层(决策 #1)—— 直接套用 LangGraph supervisor 等于把 LangGraph 引入 Hermes runtime,违反「低故障面」根本需求(增加 LangChain 依赖)。同时,LangGraph supervisor 没有 round table 概念(只有 router),v10.0 round table 需要 turn_order / max_rounds / early_stop_rule 等 round-table-specific 字段。**排除理由:LangGraph supervisor 是同构借鉴对象(B1.3),不是直接套用对象 —— 直接套用违反决策 #1 + 缺 round-table-specific 字段。**

**Steelman 反驳最强候选 (b) (i) CC 全控:** 「CC 是 Anthropic 顶级 reasoning 模型,让 CC 自己决定 turn_order / synthesis 是『充分用 CC 推理能力』」。**我方回应:** 「充分用 CC 推理能力」是指 CC 在**内容层**(question framing + synthesis)有自主权,不是指 CC 在**结构层**(turn_order / max_rounds / schema)有自主权。结构层的稳定性是审计性 + 可重现 + token 成本可控的根本需求 —— CC 每次 round table 决定不同 turn_order,无法审计 / 重现 / 预算。(vi) 分层是结构层 Hermes 控(稳定)+ 内容层 CC 控(灵活)的平衡。

#### §2.7.4 — 锁定选型 + Rationale

**锁定 (a) (vi) 分层。**

**Rationale:** (vi) 分层是**唯一同时满足审计性 + 可重现 + token 成本可控 + 充分用 CC 推理能力**的选项。设计:Hermes 通过 round table state JSON(`.runtime/{slug}/round_tables/{id}.json`)控 turn_order / max_rounds / early_stop_rule / state schema(ARCHITECTURE §5.1);CC 通过 `get_agent_opinion` MCP tool 调用每个 panelist,控 question framing(把 round table 问题分解)+ synthesis(综合多 panelist 意见)。

**关键事实:** LangGraph supervisor pattern(B1.3 borrowable point)是 (vi) 分层的**业界同构验证** —— 「Hermes 像 LangGraph supervisor(路由),CC 像 worker agent(干活)」。这是 v10.0 设计与业界最佳实践一致的证据,不是类比论证(v10.0 根本需求「审计性 + 可重现 + token 成本可控 + 充分用 CC 推理能力」推出 (vi) 分层,LangGraph supervisor 是事后验证)。

**Cross-validation(SUMMARY.md Decision 7):** STACK 支持(§3.2 turn_order 由 Hermes 通过 schema 控制;CC 通过 `prior_discussion` 控上下文折叠);FEATURES 强支持(§1.3 LangGraph supervisor + §4 Claude Agent SDK subagent 不适合 panelist);ARCHITECTURE 支持(§5.3 lifecycle sketch);PITFALLS §P7 要求 Hermes 增加新职责(coordinator arbitrates memory conflicts)。

#### §2.7.5 — Cross-Validation Evidence(4 research sources)

| Source | 章节 | 立场 | 引用要点 |
|--------|------|------|----------|
| **STACK** | §3.2(get_agent_opinion Tool 2)+ §7.5(强制串行) | **支持** | Tool 2 `prior_discussion` 参数让 CC 控上下文折叠;turn_order 由 Hermes 通过 round table state schema 控制;§7.5 强制串行(1 panelist 1 turn,顺序 await)|
| **FEATURES** | §1.3 B1.3 + §4 B4.1 + §9.3 | **强支持** | §1.3 LangGraph supervisor 是路由器不是协调员(与决策 #7 同构);§4 Claude Agent SDK subagent 默认 context-isolated 不适合 round table panelist;§9.3 协作模式速查显示 v10.0 round table 是「Hermes 控结构 + CC 控内容」|
| **ARCHITECTURE** | §5.3 lifecycle + §8.3 anti-pattern | **支持** | §5.3 lifecycle sketch:Hermes 控 turn_order / max_rounds / early_stop_rule;CC 控 question framing / synthesis;§8.3 anti-pattern「round table as pipeline step」显式禁止 |
| **PITFALLS** | §P7(round-table memory conflict) | **修正** | §P7 mitigation 2 要求 Hermes 增加新职责:coordinator arbitrates memory conflicts —— 这是 (vi) 分层原本没明说的 Hermes 仲裁 memory 冲突职责;02-ROUND-TABLE-PROTOCOL.md 解决 |

**决策 #7 状态:** `validated-in-invariant`(4 research source 一致支持;PITFALLS §P7 修正已在 02-ROUND-TABLE-PROTOCOL.md scope 内)。

---

**§2 推导链总结:** 7 决策全部从根本需求推出,无类比论证(§1.1 加严规则合规)。每决策 5-段 scaffold 完整。4 research source 的 cross-validation 一致支持(部分有修正,已在下游设计文档 scope 内)。SUMMARY.md "Design Decisions Validated" 表的「STACK 支持 / FEATURES 支持 / ARCHITECTURE 支持 / PITFALLS 警告」4 列在 §2.N.5 中显式引用,作为 cross-validation evidence。

---

## §3 — 「v10.0 显式拒绝」总表(3-source 合并)

> 本节合并 FEATURES §11 业界 anti-features + ARCHITECTURE §8 Hermes 内部 anti-patterns + PITFALLS 行业失败模式,作为后续 6 docs 的 negative design space。SUMMARY.md CC-5 finding mandate 此合并。

### §3.0 — 动机声明(三源合并)

**SUMMARY.md CC-5 verbatim:**

> 三处都列了「不要做什么」,但维度互补:**FEATURES §11** 是从业界 framework 抄来的反面教材(subagent 作容器 / 短命 agent / handoff 作 round table / crew pipeline 作协商 / memory:boolean);**ARCHITECTURE §8** 是 Hermes 内部反模式(YAML 作 prompt dump / auto-re-transform on drift / round table as pipeline step / per-agent mem0 instance / cross-layer import);**PITFALLS** 是 memory subsystem 的失败模式(persona drift / stale memory / scoped retrieval perf collapse 等)。**`00-FIRST-PRINCIPLES.md` 应把这三层 anti-features/anti-patterns 合并成一张「v10.0 显式拒绝」总表**,每条引用三个 source 中的具体章节号。

**合并动机:**

- **FEATURES §11**(业界抄来的反面教材):列 7 行,是 v10.0 显式不抄业界 multi-agent framework 的选择。维度是「framework-level anti-pattern」。
- **ARCHITECTURE §8**(Hermes 内部反模式):列 5 行,是 v10.0 实施时必须避免的 Hermes-specific 设计陷阱。维度是「implementation-level anti-pattern」。
- **PITFALLS**(行业 memory subsystem 失败模式):列 14 pitfall(7 load-bearing),是 per-agent memory + curator-driven 自进化的 production 失败模式。维度是「runtime failure mode」。

**三层互补:** FEATURES §11 回答「为什么不抄业界」;ARCHITECTURE §8 回答「Hermes 实施时避免什么」;PITFALLS 回答「production 跑起来会怎么崩」。**v10.0 显式拒绝总表合并三层**,作为后续 6 docs 的 negative design space —— 任何下游设计文档在引入新设计点时,必须先 grep 本表确认不在显式拒绝列表。

**本节是 DESIGN-01 SC#2 的 load-bearing deliverable**(ROADMAP Phase 44 Success Criteria #2:「v10.0 显式拒绝」总表 ≥10 条,每条引用三个 source 的具体章节号)。

### §3.1 — 「v10.0 显式拒绝」总表(12 行 > 10 minimum required)

下表 12 行覆盖 FEATURES §11 全部 7 行 + ARCHITECTURE §8 全部 5 行 + PITFALLS 7 个 load-bearing pitfall。每行 5 列:拒绝项 / 一句话描述 / FEATURES §X(业界反例) / ARCHITECTURE §Y(Hermes 内部护栏) / PITFALLS §Pitfall Z(失败模式 case)。

| # | 拒绝项 | 一句话描述 | FEATURES source | ARCHITECTURE source | PITFALLS source |
|---|--------|-----------|-----------------|---------------------|-----------------|
| **1** | **Subagent 作 agent 容器(`.claude/agents/*.md`)** | Kimi 方案用的形态;subagent context-isolated + memory 不 namespace scoped + 30 天 transcript TTL,违反 paradigm-shift-claim-1 + claim-4 | §11 row 1 + §4.4 B4.1(Claude Agent SDK subagent 形态)| §8.1 anti-pattern(variant:persona dump —— subagent markdown 把 SKILL body copy-paste,违反 first-person persona 语法) | PITFALLS §Pitfall 1(persona drift —— subagent 30 天 TTL 后身份不连续,违反持久身份根本需求) |
| **2** | **短命 agent(完成即销毁)** | Agent-MCP 模式(agent 完成任务即销毁);违反 paradigm-shift-claim-4「agent 随项目越多越有经验」核心诉求 | §11 row 2 + §7.2 B7.2(Agent-MCP "短命 agent + 共享 knowledge graph") | (implicit —— long-life 是 v10.0 design intent,无对应 §8 章节但有 paradigm-shift-claim-4 anchor) | PITFALLS §Pitfall 2(stale memory inversion —— 短命 agent 无机会累积 memory,违反「可自进化」根本需求) |
| **3** | **Handoff 作 round table 替代** | OpenAI Swarm 模式(handoff 是控制权移交,不是协商);v10.0 round table 是协商场景,handoff 是反面教材 | §11 row 3 + §5.1 B5.1(Swarm handoff 是控制权移交,不是协商) | §8.3 anti-pattern(round table as pipeline step —— 把 round table 做成同步阻塞,违反 async 语义) | PITFALLS §Pitfall 7(round-table conflict unresolved —— handoff 模式无 conflict 仲裁机制,违反决策 #7 Hermes 仲裁职责) |
| **4** | **Crew task pipeline 作协商** | CrewAI 模式(task 在 agent 之间流转,无多 agent 同回合协商);v10.0 round table 不抄 CrewAI 协作模式 | §11 row 4 + §3.5 B3.5(CrewAI crew 不是 round table,是 task pipeline) | §8.3 anti-pattern(same as row 3 —— round table as pipeline step) | — (CrewAI 无 round-table failure mode —— CrewAI 根本没 round table 概念) |
| **5** | **A2A 跨厂商协议(v10.0 范围内)** | A2A 是为跨厂商 agent-to-agent 通讯设计;v10.0 是单厂商内部,引入 A2A 是过度工程化(v12+ 扩展位) | §11 row 5 + §7.4 B7.1(Microsoft 三层协议分层)+ §8 B8.3(A2A 是 v12+ 扩展位,不在 v10.0) | — (cross-vendor not in Hermes scope —— ARCHITECTURE §6 三 location 都是 Hermes-side / kais-hermes-skills / operator,无 cross-vendor) | — (A2A 不引入 memory subsystem,无对应 pitfall) |
| **6** | **`memory: true` boolean flag(无 namespace)** | CrewAI 模式(memory 是 boolean,无 per-agent namespace 概念);违反决策 #6 per-agent memory 根本需求 | §11 row 6 + §3.3 B3.3(CrewAI `memory: true` 不够细) | §8.4 anti-pattern(per-agent mem0 instance —— wrong solution direction,会撞 mem0 rate-limit;正确方向是单 backend + agent_id filter) | PITFALLS §Pitfall 3(scoped retrieval perf collapse)+ PITFALLS §Pitfall 4(cross-project leakage)+ PITFALLS §Pitfall 12(cross-agent contamination) |
| **7** | **CrewAI 30+ 字段全抄** | CrewAI agents.jsonc 30+ 字段是「industry standard」但太厚;v10.0 抄 5-7 个核心字段(role/goal/backstory + max_turns/timeout + memory_scope) | §11 row 7 + §3.3(CrewAI 字段表 30+ 项) | §8.1 anti-pattern(YAML 作 prompt dump —— 30+ 字段维护成本高,operator 难直接编辑) | — (字段厚度不直接对应 memory 失败模式) |
| **8** | **YAML 作 prompt dump(SKILL body copy-paste 到 persona)** | 把 SKILL.md body(imperative-second-person user-message)copy-paste 到 agent persona(first-person system-prompt fragment);混合 register | (implicit —— FEATURES §11 row 7 间接覆盖,CrewAI 字段表厚 = prompt dump 倾向) | §8.1 anti-pattern(完整 section,明确禁止 SKILL body copy-paste 到 persona) | PITFALLS §Pitfall 1(persona drift —— persona 与 SKILL body 混淆,身份不清晰,加速 drift) |
| **9** | **Auto-re-transform on drift** | curator 检测 skill_sha256 drift 后自动 regenerate agent YAML;覆盖 operator 手动调整 | (implicit —— FEATURES 不直接覆盖 curator drift detection) | §8.2 anti-pattern(完整 section,明确禁止 auto-re-transform;drift 触发 advisory,operator 决定) | PITFALLS §Pitfall 5(curator failure modes —— 自动 re-transform 失去 operator ownership,违反 dry-run-first 不变量) |
| **10** | **Per-agent mem0 backend instance(物理分区过早)** | 每 agent 一个 mem0 backend instance;在 v11.0 PoC 规模(15 agent)是过度工程化 + 撞 mem0 rate-limit | (implicit —— FEATURES §1.3 LangGraph Store namespace 是 filter 路由替代,不是物理分区) | §8.4 anti-pattern(完整 section,明确禁止 per-agent mem0 instance) | PITFALLS §Pitfall 3(scoped retrieval perf —— 物理分区是 v12+ mitigation,v11.0 PoC 用 Option B 即可)+ PITFALLS §Pitfall 12(cross-agent contamination 物理分区可缓解,但 v11.0 PoC 规模不达触发条件) |
| **11** | **Cross-layer import of `run_agent` in agent modules** | `agent/agent_registry.py` 或 `agent/agent_dispatcher.py` import `run_agent.AIAgent` at module top;破坏 `_ra()` lazy indirection pattern,导致 circular import | (implicit —— FEATURES 不覆盖 Hermes 内部 import 模式) | §8.5 anti-pattern(完整 section,要求 lazy import inside function bodies,类比 `agent/curator.py:_run_llm_review` line 2330) | — (circular import 是 Hermes-internal hazard,无对应 pitfall) |
| **12** | **Round table as synchronous pipeline step** | 把 `round_table_open` 做成同步阻塞调用(等 closed 才返回);违反 async 语义,3 rounds × 4 panelists × 30s = 6 分钟阻塞 interactive MCP client | (implicit —— FEATURES §11 row 3 variant,handoff 作 round table 替代的同步语义) | §8.3 anti-pattern(完整 section,要求 `round_table_open` 立即返回 round_table_id,CC 通过 `round_table_poll` 异步获取) | PITFALLS §Pitfall 7(round-table conflict unresolved under sync semantics —— 同步阻塞下 conflict 仲裁无机会介入) |

**12 行 > 10 minimum required(SC#2 合规)。**

**覆盖审计:**

| Source | 章节 | 行号 | 覆盖? |
|--------|------|------|-------|
| FEATURES §11 row 1(subagent 容器) | §3 row 1 | ✅ |
| FEATURES §11 row 2(短命 agent) | §3 row 2 | ✅ |
| FEATURES §11 row 3(handoff 作 round table) | §3 row 3 | ✅ |
| FEATURES §11 row 4(crew pipeline 作协商) | §3 row 4 | ✅ |
| FEATURES §11 row 5(A2A v10.0 范围) | §3 row 5 | ✅ |
| FEATURES §11 row 6(memory boolean) | §3 row 6 | ✅ |
| FEATURES §11 row 7(CrewAI 30+ 字段) | §3 row 7 | ✅ |
| ARCHITECTURE §8.1(YAML 作 prompt dump) | §3 row 8 + row 7(variant) | ✅ |
| ARCHITECTURE §8.2(auto-re-transform) | §3 row 9 | ✅ |
| ARCHITECTURE §8.3(round table as pipeline step) | §3 row 12 + row 3 + row 4(variant) | ✅ |
| ARCHITECTURE §8.4(per-agent mem0 instance) | §3 row 10 + row 6(variant) | ✅ |
| ARCHITECTURE §8.5(cross-layer import) | §3 row 11 | ✅ |

**FEATURES §11 全 7 行 + ARCHITECTURE §8 全 5 行 = 12 source rows 全部覆盖。** PITFALLS 7 load-bearing pitfall 在「PITFALLS source」列引用(部分 pitfall 对应多行,部分行无对应 pitfall —— 这是预期的,因为 FEATURES §11 / ARCHITECTURE §8 的反模式不一定都有 production 失败模式案例)。

### §3.2 — 使用指南(下游 6 docs 如何用本表)

**下游设计文档(01-06)在引入任何新设计点时,必须遵守以下流程:**

1. **grep 本表确认不在显式拒绝列表。** 如果新设计点与本表某行匹配,**不可引入**(该反模式已被显式拒绝,论据在 §3.0 + §2 推导链 + research source 章节)。
2. **若认为某拒绝项需要 re-litigate**,需开**新的设计-修订 milestone**(类比 v2.0 PRFP §1.1 修改门槛 discipline)。Re-litigation 流程:
   - (a) 在新 milestone 的 00-FIRST-PRINCIPLES-revision.md 中显式引用本表 row # + 论据
   - (b) 提供「根本需求变化」的具体证据(不是「业界现在都这么做」—— 这是类比论证,§1.1 加严规则禁止)
   - (c) 4 research source 重新 cross-validation
   - (d) 新 milestone 的 DESIGN-XX requirement 显式 supersede 本表 row #
3. **新设计点不在本表 = 允许引入。** 但引入时必须在下游设计文档显式引用本表「不冲突」(e.g.「本设计点不在 §3 显式拒绝列表,引入合规」)。
4. **本表是 `stable`(修改门槛:开新设计-修订 milestone)。** 不允许在 v10.0 设计 milestone 内部修改本表 —— 任何新增 / 删除 / 修改拒绝项都需要新 milestone。

**典型用法示例(下游文档作者参考):**

- **01-AGENT-REGISTRY-SCHEMA.md:** 在设计 18-field schema 时,作者想加 `subagent_invocation: true` 字段让 agent 可作为 CC subagent 调用。**grep §3.1 row 1**(subagent 作 agent 容器 = 显式拒绝)→ **不可加此字段**。如果作者认为「作为 subagent 调用」与「subagent 作容器」不同,需在新 milestone re-litigate row 1。
- **02-ROUND-TABLE-PROTOCOL.md:** 作者想设计 `round_table_open` 为同步阻塞(等 closed 才返回)。**grep §3.1 row 12**(round table as synchronous pipeline step = 显式拒绝)→ **必须改为异步**(`round_table_open` 立即返回 round_table_id,CC 通过 `round_table_poll` 异步)。
- **04-MIGRATION-PATH.md:** 作者想设计 curator 检测 skill drift 后自动 re-transform agent YAML。**grep §3.1 row 9**(auto-re-transform on drift = 显式拒绝)→ **必须改为 advisory**(drift 触发 curator report,operator 决定是否 re-transform)。

---

## §4 — FEATURES §10 borrowable points 评估

> 本节逐点评估 FEATURES §10 中对 v10.0 设计最有影响的 5 个 borrowable points(plan mandated coverage: B1.3 / B3.5 / B4.1 / B7.2 / B5.1)。每点给赞同 / 拒绝 / 改造结论。

### §4.0 — 声明

FEATURES §10 列出 27 个 borrowable design points(从 8 个 framework 提炼),喂给下游设计文档作设计原料。本节**只评估对 v10.0 设计最有影响的 5 个**(plan mandated);其他 22 点可在下游设计文档按需引用本节方法论(从根本需求推出赞同/拒绝/改造,不从「业界抄」推)。

**评估方法论(每点 4 段):**

1. **借鉴点摘要** — 一句话 summary + FEATURES §章节号
2. **v10.0 结论** — 赞同 / 拒绝 / 改造 + 一句话 rationale
3. **论据** — 2-3 段 cross-reference §2 推导链 + §3 拒绝表(不重新推导,指向已锁论据)
4. **下游使用** — 哪个设计文档(01-06)消费此结论 + 如何使用

---

### §4.1 — B1.3 LangGraph supervisor 是路由器不是协调员

**借鉴点摘要:** LangGraph supervisor 的职责是 **routing and delegation**,不是内容生产([langgraph-supervisor 文档],FEATURES §1.3 B1.3)。

**v10.0 结论:** **赞同** —— 这与决策 #7 (vi) 分层 CC 高度同构,Hermes 像 LangGraph supervisor(路由),CC 像 worker agent(干活)。

**论据:**

§2.7 决策 #7 推导链已锁:(vi) 分层是「Hermes 控结构(turn_order / max_rounds / schema / early_stop_rule),CC 控内容(question framing / synthesis)」—— 这正是 LangGraph supervisor pattern 的「路由器 vs worker」分工。这不是「业界用 LangGraph supervisor 所以 v10.0 也用」式类比论证,而是「v10.0 根本需求(审计性 + 可重现 + token 成本可控 + 充分用 CC 推理能力)推出 (vi) 分层,LangGraph supervisor 是事后同构验证」(§2.7.4 Rationale)。

**与 §3 显式拒绝的关系:** B1.3 不与任何 §3 row 冲突。LangGraph supervisor pattern 是**借鉴对象**,不是「直接套用 LangGraph」(§2.7.3 排除候选 (d) 已说明:v10.0 不引入 LangChain 依赖,只借鉴 supervisor 概念)。

**下游使用:**

- **02-ROUND-TABLE-PROTOCOL.md** 引用本结论设计 turn lifecycle:Hermes 通过 round table state schema(控 turn_order)扮演 supervisor 角色;CC 通过 `get_agent_opinion` MCP tool 调用每个 panelist(扮演 worker agent)。
- **02** 不 re-derive 决策 #7(已锁在 §2.7),只 design turn lifecycle 字段(`turn_order` / `max_rounds` / `early_stop_rule`)的协议级实现。

---

### §4.2 — B3.5 CrewAI crew 不是 round table, 是 task pipeline

**借鉴点摘要:** CrewAI 没有「多 agent 同时讨论同一个问题」的原语,只有「任务在 agent 之间流转」(FEATURES §3.5 B3.5)。CrewAI 是 task pipeline,不是 round table。

**v10.0 结论:** **赞同(作为 anti-pattern 引用)** —— v10.0 round table 概念应从 AutoGen GroupChat(FEATURES §2)+ LangGraph network(FEATURES §1)借鉴,**不**从 CrewAI 借鉴。CrewAI 的 crew 模式适合 v10.0 的 fallback 形态(顺序 pipeline,而非协商)。

**论据:**

§3.1 row 4 显式拒绝「Crew task pipeline 作协商」。理由:CrewAI 没有「多 agent 同回合协商」原语,把 CrewAI crew 当 round table = 把「task 流转」误认为「多 agent 讨论」—— 这是概念混淆。v10.0 round table 的根本需求是「多 panelist 协商同一个问题」(§2.7 + §2.3 D2 storyboard 场景),CrewAI task pipeline 不满足此需求。

**与 §2 推导链的关系:** §2.3 决策 #3(D2 storyboard)明确「跨场景 dispatch 多个独立 round table」—— 每个 round table 内部仍是协商(决策 #7 turn-based 串行),不是 task pipeline。CrewAI task pipeline 是 v10.0 的 fallback 形态(`default_invocation: skill_fallback` 触发时,agent 通过 SKILL 形态顺序处理,而非 round table 协商)。

**下游使用:**

- **02-ROUND-TABLE-PROTOCOL.md** 引用本结论作为「为什么不抄 CrewAI 协作模式」的根论据。02 设计 turn lifecycle 时,显式避免 CrewAI task pipeline 语义(no `next_agent` field,no task handoff);改用 round table 语义(`turn_order` list + `current_speaker_index`)。
- **02** 可在「anti-patterns」子节引用本结论 + §3 row 4 作为 negative design space。

---

### §4.3 — B4.1 Claude Agent SDK subagent 形态必须显式拒绝

**借鉴点摘要:** Claude Agent SDK `.claude/agents/*.md` subagent 是 Kimi 方案用的形态;subagent **default context-isolated** + **memory 字段不是 namespace scoped** + **transcripts 30 天自动清理**(FEATURES §4.4 B4.1)。

**v10.0 结论:** **赞同(Kimi 方案的反例)** —— v10.0 显式拒绝 subagent 形态;agent 是 Hermes-side 独立 YAML 实体(`~/.hermes/agents/*.agent.yaml`),不是 CC-side subagent。

**论据:**

§2.5 决策 #5 α agent form 推导链详细论证了 subagent 形态的三条具体失败模式(§2.5.3 排除候选 (b)):

1. **Context-isolated** 违反「持久身份」根本需求(panelist 需要看完整历史,subagent 不天然适合)
2. **Memory 不 namespace scoped** 违反「有记忆」根本需求(`memory: 'user'|'project'|'local'` 是 source-scoped,不是 agent-scoped)
3. **30 天 TTL** 违反「可自进化」根本需求(跨项目经验持久化不稳定)

§3.1 row 1 显式拒绝「subagent 作 agent 容器」。这三条是 Anthropic 官方 docs 明确说的(FEATURES §4.3 引用 code.claude.com),不是 v10.0 的臆测 —— 这是 **elimination-by-fundamental-constraint**,不是「业界用 subagent 我们不用」式类比论证。

**与 paradigm shift 的关系:** §1.3 paradigm-shift-claim-1(Kimi 默认 vs v10.0 设计)直接否决了 subagent 形态 —— Kimi 方案把 agent 塞进 CC(`.claude/agents/*.md`),v10.0 把 agent 留在 Hermes-side(`~/.hermes/agents/`)。B4.1 是这个 paradigm shift 的字段级实现论据。

**下游使用:**

- **03-COMPARISON-VS-KIMI-MCP-SHIM.md** 引用本结论作为「Kimi 方案否决」的根论据。03 在 7 维度对照表中,「agent 形态」维度直接引用 §2.5 + §3 row 1 + §4.3(B4.1)三处论据。
- **01-AGENT-REGISTRY-SCHEMA.md** 在设计 `persona` 字段时引用本结论,明确「persona 是 first-person system-prompt fragment(非 user-message subagent prompt)」,违反则触发 §3 row 8(YAML 作 prompt dump)+ §3 row 1 variant。

---

### §4.4 — B7.2 Agent-MCP 短命 agent + 共享 knowledge graph = v10.0 反面教材

**借鉴点摘要:** Agent-MCP 主张 agent 完成任务即销毁(short-lived),context 集中在项目级 knowledge graph(FEATURES §7.2 B7.2)。

**v10.0 结论:** **赞同** —— Agent-MCP 的「短命 agent + 共享 graph」模式与 v10.0 决策 #6(per-agent memory + curator 自进化)正好相反;v10.0 选**长生命周期 agent**(per-project memory 跨项目累积)。

**论据:**

§2.6 决策 #6 推导链明确「per-agent memory + curator-driven 自进化」是 v10.0 paradigm shift 核心诉求(paradigm-shift-claim-4)。Agent-MCP 的「短命 agent」违反此诉求 —— agent 完成任务即销毁,没有机会累积 memory,没有 curator-driven evolution。

§3.1 row 2 显式拒绝「短命 agent(完成即销毁)」。Agent-MCP 模式是这一拒绝项的业界实例。

**关键差异:** Agent-MCP 把 context 集中在「项目级 knowledge graph」(RAG-over-MCP),所有 agent 共享;v10.0 把 memory 分散到「per-agent scoped memory」(每个 agent 独立 namespace + curator 自进化)。这是**两种 fundamentally 不同的 memory architecture** —— Agent-MCP 是「共享 graph + 短命 agent」,v10.0 是「per-agent memory + 长寿命 agent」。

**下游使用:**

- **01-AGENT-REGISTRY-SCHEMA.md** 引用本结论作为「agent 是长生命周期实体,不是 single-task ephemeral」的根论据。01 在设计 `evolution_log` + `fitness_score` 字段时,引用 §2.6 + §3 row 2 + §4.4(B7.2)三处论据,明确 agent YAML 是持久实体(跨项目累积 memory)。
- **05-POC-PLAN.md** 在 PoC acceptance criteria 中引用本结论:agent 必须在多 project 之间保持 memory(`scope: global` memory 跨 project visible),证明「长寿命 agent」不是口号而是可验证的行为。

---

### §4.5 — B5.1 OpenAI Swarm handoff 是控制权移交, 不是协商

**借鉴点摘要:** OpenAI Swarm 的 handoff function 是「agent A 通过返回指向 agent B 的函数,把对话交给 agent B」—— handoff 是控制权移交,不是协商(FEATURES §5.1 B5.1)。Swarm 适合**串行专家接力的客服场景**,不适合多专家同台讨论。

**v10.0 结论:** **赞同(作为 anti-pattern 引用)** —— v10.0 round table 是协商场景(多 panelist 同回合讨论同一问题),handoff 模式是反面教材。

**论据:**

§3.1 row 3 显式拒绝「Handoff 作 round table 替代」。理由:handoff 是「控制权移交」(agent A → agent B,A 不再参与),v10.0 round table 是「协商」(多 panelist 同时在场,按 turn_order 轮流发言,所有人看完整 history)。这是两种 fundamentally 不同的协作模式 —— handoff 适合「串行专家接力」(客户 → triage → billing → close),round table 适合「多专家同台讨论」(剧本评估 → 多 panelist 给意见 → synthesizer 综合)。

**与 §2.7 决策 #7 的关系:** 决策 #7 (vi) 分层要求「Hermes 控 turn_order / max_rounds / early_stop_rule」—— handoff 模式没有 turn_order 概念(每次 handoff 是单向控制权移交),无法满足「审计性 + 可重现」根本需求。同时,§2.7.3 排除候选 (b) (i) CC 全控时已说明:CC 决定何时 handoff 等于 Hermes 失去结构控制权。

**Swarm 的可借鉴部分(B5.2,本节不展开):** Swarm 的「轻量」哲学可借鉴用于 v10.0 的 fallback 形态 —— 当 round table 不必要(单 agent 即可解决)时,v10.0 应有「handoff-style」快速路径(agent A 调用 agent B 通过 MCP tool,B 返回 final answer,A 继续)。这是 v10.0 的 `fallback_pipeline` 形态(顺序而非协商),在 02-ROUND-TABLE-PROTOCOL.md 中设计。

**下游使用:**

- **02-ROUND-TABLE-PROTOCOL.md** 引用本结论排除 handoff 协议设计。02 在设计 turn lifecycle 时,显式避免 handoff 语义(no `handoff_to: agent_id` field,no control transfer);改用 round table 语义(`current_speaker` + `next_speaker` 由 Hermes 通过 `turn_order` 控)。
- **02** 可在「fallback pipeline mode」子节引用 B5.2(轻量 handoff 哲学)设计 `default_invocation: skill_fallback` 触发时的快速路径。

---

**§4 评估总结:** 5 mandated borrowable points 全部评估。3 点赞同(B1.3 / B4.1 / B7.2,作正面或反例论据),2 点赞同作 anti-pattern 引用(B3.5 / B5.1)。无「拒绝」结论(所有 5 点都有可借鉴价值,即使作为反例)。每点 cross-reference §2 推导链 + §3 拒绝表,无重新推导。

---

## §5 — 后续 6 docs 引用指南(citation cards)

> 后续 6 份设计文档(01-06)在不重新推导决策的前提下引用本文档作根论据。本节列出每份文档的引用 entry points。

### §5.0 — 声明

后续 6 docs 在引用本文档时,**必须用 §X.Y 章节号 + 决策号(决策 N)+ 拒绝项 row # + paradigm-shift-claim-N anchor**,不重新陈述内容(防 drift)。每 doc 的「不应 re-derive」+「应该 derive」清单见各 §5.X。

下游 doc 引用格式约定:

- 「per 00-FIRST-PRINCIPLES.md §2.5」 = 引用决策 #5 推导链
- 「per 00-FIRST-PRINCIPLES.md §3 row 1」 = 引用 subagent 否决论据
- 「per 00-FIRST-PRINCIPLES.md §4.3」 = 引用 B4.1 评估结论
- 「per 00-FIRST-PRINCIPLES.md paradigm-shift-claim-4」 = 引用 paradigm shift 第 4 条

### §5.1 — 01-AGENT-REGISTRY-SCHEMA.md 引用卡

**本文档可引用的根论据:**

- §1.2 决策清单(选 #5 α form + #6 per-agent memory 适用)
- §2.5 决策 #5 推导链(含 §2.5.6 字段级实现 + §2.5.7 失败模式)
- §2.6 决策 #6 推导链(含 §2.6.6 2-schema-layer + §2.6.7 curator phase 契约 + §2.6.8 失败模式)
- §3 rows 1 / 6 / 7 / 8 / 9 / 10 / 11(显式拒绝项)
- §4.3(B4.1 subagent 否决)+ §4.4(B7.2 短命 agent 否决)

**本 doc 不应 re-derive(已 LOCKED 在 00):**

- 决策 #5 推导(α form 选型)
- 决策 #6 推导(per-agent memory + curator-driven 自进化)
- subagent 形态否决(§3 row 1 + §4.3 B4.1)
- 短命 agent 否决(§3 row 2 + §4.4 B7.2)
- 18-field schema 字段集(已在 ARCHITECTURE §1.1 定义)

**本 doc 应该 derive(不在 00 范围):**

- 18-field schema 的 JSON Schema 正式定义(`agents-schema.yaml`)
- memory-record-schema.yaml(10 字段:expires_at / verified_at / supersedes_memory_id / confidence / half_life_days / evidence_chain / evidence_operator_ids / status / confidentiality / scope)
- 15 expert 5-field transform 映射表(从 ARCHITECTURE §2 拷贝)
- per-agent memory tier 规范(core / working / archival 三层 + `memory.max_records` 上限,解决 OQ-7)
- curator `_memory_evolution_phase` 字段契约(执行顺序 + dry-run-by-default + try/except 边界,解决 OQ-16)
- 6 Open Questions(OQ-1 / OQ-4 / OQ-7 / OQ-13 / OQ-14 / OQ-16)显式解决或 defer 到 v11.0
- 7 load-bearing pitfalls(P1 / P2 / P4 / P5 / P8 / P10 / P14)字段级缓解

### §5.2 — 02-ROUND-TABLE-PROTOCOL.md 引用卡

**本文档可引用的根论据:**

- §1.2 决策清单(选 #3 D2 storyboard + #7 分层 CC 适用)
- §2.3 决策 #3 推导链(D2 storyboard round-parallel)
- §2.7 决策 #7 推导链((vi) 分层 CC 角色)
- §3 rows 3 / 4 / 11 / 12(显式拒绝项:handoff / crew pipeline / cross-layer import / sync round table)
- §4.1(B1.3 LangGraph supervisor 同构)+ §4.2(B3.5 CrewAI 否决)+ §4.5(B5.1 handoff 否决)

**本 doc 不应 re-derive:**

- 决策 #3(D2 storyboard)
- 决策 #7((vi) 分层 CC)
- LangGraph supervisor 同构(§4.1)
- CrewAI task pipeline 否决(§3 row 4 + §4.2)
- handoff 否决(§3 row 3 + §4.5)

**本 doc 应该 derive:**

- turn lifecycle 状态机(pending / speaking / waiting_input / done / failed)
- `turn_order` 字段三态(llm / fixed / matrix,B2.1 borrowable point)
- memory conflict arbitration 规则(coordinator arbitration + scope precedence + confidence-weighted voting,§Pitfall 7 mitigation 2)
- confidentiality propagation(§Pitfall 10 mitigation 4)
- `project_id` 必传(API contract,§Pitfall 4 mitigation 4)
- 强制串行约束(1 panelist 1 turn,GLM 4-key rotation,CC-6)
- 7 MCP tool 契约(STACK §3.2 Tool 1-7,统一命名无前缀,CC-1)
- `round_table_state_schema.yaml`(JSON Schema 形式化)

### §5.3 — 03-COMPARISON-VS-KIMI-MCP-SHIM.md 引用卡

**本文档可引用的根论据:**

- §1.2 决策清单(选 #1 T6 + #5 α form + #7 分层 CC 适用)
- §1.3 paradigm-shift-claim-1(Kimi 默认 vs v10.0 设计)+ paradigm-shift-claim-3(CC Team Lead 极薄)
- §2.1 决策 #1 推导链(T6 协议)
- §2.5 决策 #5 推导链(α form,含 §2.5.3 排除候选 (b) Claude Agent SDK subagent)
- §2.7 决策 #7 推导链((vi) 分层 CC)
- §3 rows 1 / 5(显式拒绝项:subagent 容器 / A2A v10.0 范围)
- §4.3(B4.1 subagent 否决论据)

**本 doc 不应 re-derive:**

- 决策 #1(T6 协议选型)
- 决策 #5(α form 选型)
- 决策 #7((vi) 分层 CC 选型)
- subagent 形态否决(§3 row 1 + §4.3 B4.1)
- A2A v10.0 范围否决(§3 row 5 + §2.1.3 排除 (b))

**本 doc 应该 derive:**

- 7 维度对照表(协议 / dispatch / callback / state / 多 agent / 实现成本 / 稳定性)逐维度 T6 vs Kimi 方案优劣势
- Microsoft 三层协议分层验证(FEATURES §7.4 B7.1:internal → platform-native;tool → MCP;cross-platform → A2A)
- Kimi 方案中可借鉴部分(如有)显式列出 + 借鉴条件评估
- subagent 形态否决横向验证(引用 §2.5 + §3 row 1 + §4.3 三处论据)

### §5.4 — 04-MIGRATION-PATH.md 引用卡

**本文档可引用的根论据:**

- §1.2 决策清单(选 #2 B3a Python runner + #5 α form 适用)
- §2.2 决策 #2 推导链(B3a 增量迁移)
- §2.5 决策 #5 推导链(含 §2.5.6 lineage 字段)
- §3 row 9(auto-re-transform on drift 显式拒绝)

**本 doc 不应 re-derive:**

- 决策 #2(B3a 增量迁移)
- 决策 #5(α form,特别是 lineage 字段)
- auto-re-transform 否决(§3 row 9)

**本 doc 应该 derive:**

- 15 expert 5-field transform 规则(COPY / DROP / REWRITE / FLATTEN / DERIVE / INITIALIZE)
- `default_invocation: skill_fallback → mcp_tool` 切换规则
- memory schema 迁移(v7.0 `agent_id=hermes` 默认 memory → per-agent `agent_id=screenplay` 等;OQ-3 遗留 memory 不迁移)
- retained-phases allowlist(9 delegate-only phase + 4 ComfyUI phase + Step 0/6.5/15)
- `run_python_phase` retained-phases allowlist 定义位置(OQ-10:`round-table-schema.yaml`)
- schema_version 字段 + memory schema migration dry-run(P14 缓解)

### §5.5 — 05-POC-PLAN.md 引用卡

**本文档可引用的根论据:**

- §6.2 风险登记表(7 load-bearing pitfalls)
- §3 全部 12 拒绝项(PoC 必须证明避免)
- §2.6 决策 #6 推导链(7 load-bearing pitfall 字段级缓解)
- §4.4(B7.2 短命 agent 反例,PoC 必须证明 agent 长寿命)

**本 doc 不应 re-derive:**

- 任何决策(全部锁定在 §2)
- 任何拒绝项(全部锁定在 §3)
- 7 load-bearing pitfall(已在 §6.2 风险登记)

**本 doc 应该 derive:**

- v11.0 PoC acceptance criteria 清单:
  - fitness battery(每 agent 10-20 frozen prompts,§P8 mitigation 1)
  - latency SLO(mem0 read p95 < 500ms,§P3 mitigation 4)
  - bias canary(5 single-operator-preference prompts,§P5 mitigation 4)
  - compaction pass(三 tier memory 触发条件,§P9 mitigation 2)
  - threshold tuning(feedback_threshold_count 自适应,§P13 mitigation 1)
  - dry-run-first invariant(`--apply-memory` flag,§P5 mitigation 5)
  - schema migration dry-run(`hermes agent memory migrate --dry-run`,§P14 mitigation 3)
- PoC 工作量估算(基于 STACK §7 token 成本 ~550K/pipeline run)
- 垂直切片选择(建议:screenplay agent 单 agent PoC,验证 per-agent memory + curator-driven evolution E2E)

### §5.6 — 06-CROSS-REPO-IMPACT.md 引用卡

**本文档可引用的根论据:**

- §1.2 决策清单(选 #1 T6 + #6 per-agent memory 适用)
- §2.1 决策 #1 推导链(T6 协议,影响 hermes-agent repo vs kais-hermes-skills repo 协作)
- §2.6 决策 #6 推导链(per-agent memory,影响 mem0 backend 部署)
- §3 row 5(A2A v12+ 扩展位)+ §3 row 10(per-agent mem0 instance 物理分区)

**本 doc 不应 re-derive:**

- 决策 #1(T6 协议)
- 决策 #6(per-agent memory)
- A2A v12+ 扩展位(§3 row 5)
- 物理分区迁移触发条件(§3 row 10 + CC-4 finding)

**本 doc 应该 derive:**

- 3-location(hermes-agent repo / kais-hermes-skills repo / `~/.hermes/`)同步策略(ARCHITECTURE §6.3)
- Option B(v11.0 PoC filter 路由)vs 物理分区(v12+ 每 agent 一 workspace)迁移触发条件(CC-4 finding:50+ agent × 100+ project 是触发线)
- OQ-3 旧 memory 遗留(v7.0 `agent_id=hermes` memory 不迁移)
- OQ-6 project slug 稳定性(接受 breakage,long-term 用 `.hermes/project.id` stable ID)
- operator key management(§P6 mitigation 1:`operator_signature` HMAC,operator key 在 `~/.hermes/` 下管理)

---

**§5 引用指南总结:** 6 downstream docs 全部覆盖。每 doc 有「可引用根论据」+「不应 re-derive」+「应该 derive」三段清单。下游 doc 作者按 §5.X 引用卡执行,确保不重新推导已锁决策。

---

## §6 — 总结 + 风险登记表 + milestone 挂钩

### §6.1 — Coherence 声明(v10.0 milestone-level negative + positive design space)

**v10.0 设计型 milestone 的 design space 由本文档锁定:**

- **Positive design space(7 决策锁定):** §2 推导链给出 7 个已锁决策的 first-principles 论据 —— 决策 #1 T6 协议 / 决策 #2 B3a 增量迁移 / 决策 #3 D2 storyboard / 决策 #4 G2 通用框架 / 决策 #5 α agent form / 决策 #6 per-agent memory + curator / 决策 #7 (vi) 分层 CC。每决策从根本需求推出,无类比论证(§1.1 加严规则合规)。

- **Negative design space(12 显式拒绝项锁定):** §3 总表给出 12 个 v10.0 显式拒绝的 anti-features / anti-patterns —— subagent 容器 / 短命 agent / handoff 作 round table / crew pipeline 作协商 / A2A v10.0 范围 / memory boolean / CrewAI 30+ 字段全抄 / YAML 作 prompt dump / auto-re-transform / per-agent mem0 instance(过早)/ cross-layer import / round table 同步阻塞。每拒绝项引用 FEATURES §X + ARCHITECTURE §Y + PITFALLS §Pitfall Z 三 source。

- **Borrowable design space(5 点评估锁定):** §4 给出 5 个 FEATURES §10 borrowable points 的赞同/拒绝/改造结论 —— B1.3 LangGraph supervisor(赞同)+ B3.5 CrewAI task pipeline(赞同作 anti-pattern)+ B4.1 Claude Agent SDK subagent(赞同作 Kimi 反例)+ B7.2 Agent-MCP 短命 agent(赞同作反面教材)+ B5.1 Swarm handoff(赞同作 anti-pattern)。

**后续 6 docs 在此 design space 内做具体设计,不可越界。** 任何越界(引入与决策冲突的设计 / 引入显式拒绝的反模式 / 重新推导已锁论据)需开新设计-修订 milestone(§3.2 + §1.1 加严规则)。

**Coherence check:** 7 决策 + 12 拒绝项 + 5 borrowable 评估 = **相互一致的正负 design space**。决策 #5(α form)的 field-level 实现与 §3 row 1(subagent 否决)+ §4.3(B4.1)一致;决策 #6(per-agent memory)的 2-schema-layer 实现与 §3 row 6(memory boolean 否决)+ §4.4(B7.2 短命 agent 否决)一致;决策 #7((vi) 分层 CC)的 turn lifecycle 实现与 §3 row 3(handoff 否决)+ §3 row 12(sync round table 否决)+ §4.1(B1.3 LangGraph supervisor 同构)+ §4.5(B5.1 handoff 否决)一致。无内部矛盾。

### §6.2 — 风险登记表(7 load-bearing pitfall,v11.0 PoC 硬风险)

下表从 SUMMARY.md §Risk Register + PITFALLS.md 摘出 7 个 load-bearing pitfall,每行标注「在哪个下游 doc 解决」+「本文档提供的根论据」:

| Risk ID | Pitfall | Severity | 在哪个下游 doc 解决 | 本文档提供的根论据 |
|---------|---------|----------|---------------------|---------------------|
| **P1** | persona drift(agent forgets role after accumulating memory) | HIGH | 01-AGENT-REGISTRY-SCHEMA.md(`persona_sha256` + tiered memory core/archival) + 02-ROUND-TABLE-PROTOCOL.md(persona-drift probe scheduling) | §2.6 决策 #6 推导 + §3 row 8(YAML 作 prompt dump 否决)+ §4.3(B4.1 subagent 否决,30 天 TTL 是 persona drift 的业界案例) |
| **P2** | stale memory(cites platform rules that no longer apply) | HIGH | 01(`expires_at` / `verified_at` / `supersedes_memory_id` / `confidence` / `half_life_days`)+ 05(re-verification pass as PoC acceptance) | §2.6 决策 #6 推导 + §3 row 6(memory boolean 不 namespace scoped,无法 time-decay) |
| **P4** | cross-project memory leakage | HIGH | 01(`scope: global\|project\|session` + `project_id` required) + 02(propagate project_id) | §2.6 决策 #6 推导(Option B filter 路由不隔离 project)+ §3 row 6(memory boolean 无 scope) |
| **P5** | curator failure(false-delete / hallucinate / bias amplify) | HIGH | 01(`evidence_chain` ≥3 + `evidence_operator_ids` 多样性) + 05(bias canary as PoC acceptance) | §2.6 决策 #6 推导 + §3 row 9(auto-re-transform 否决,curator 失去 operator ownership 是 curator failure 的字段级案例) |
| **P6** | memory poisoning(MINJA-style persistent attack) | HIGH | 01(`operator_signature` HMAC + `status="quarantined"`)+ 05(outlier detection)+ 06(operator key management) | §2.6 决策 #6 推导(per-agent memory 是攻击面)+ §3 row 2(短命 agent 反面教材,共享 graph 更易 poisoning) |
| **P7** | round-table memory conflict | MEDIUM | 02(coordinator arbitration + scope precedence + confidence-weighted voting + conflict log) | §2.7 决策 #7 推导 + §3 row 3(handoff 否决,无 conflict 仲裁)+ §3 row 12(sync round table 否决,同步阻塞下 conflict 仲裁无机会) |
| **P8** | no fitness signal(can't tell if agent getting better) | HIGH | 01(`fitness_battery` field + `fitness_trend.jsonl`)+ 05(regression auto-quarantine as PoC acceptance) | §2.6 决策 #6 推导(curator-driven 自进化需要 fitness signal 作 gate)+ §3 row 2(短命 agent 无 fitness signal 累积) |

**额外 7 个非 load-bearing pitfall** 在 PITFALLS §Risk Register Summary 标注「PoC-acceptable deferral」(P3 / P9 / P10 partial / P11 / P12 / P13 / P14)。这些在 v11.0 PoC 可部分 defer,但 01 / 05 必须在 schema 字段 / acceptance criteria 中预留缓解位。

### §6.3 — v11.0 PoC + milestone 挂钩

**本文档作为 v10.0 milestone 的不可移根论据:**

- **稳定性:** §1.2(7 决策清单)+ §2(7 推导链)+ §3(12 拒绝项)+ §4(5 borrowable 评估)全部 `stable`(修改门槛:开新设计-修订里程碑,类比 v2.0 PRFP §1.1 修改门槛 discipline)。
- **v11.0 PoC 实施时引用本文档作为决策已锁的依据,不重新推导。** 如果 v11.0 PoC 实施过程中发现某决策推导有漏洞,记录到 `deferred-items.md`(在 phase 目录),在设计-修订里程碑中处理(类比 v2.0 PRFP §7 Open Questions → 后续研究 phase)。
- **本文档的下游消费者:** 6 份设计文档(01-06)按 §5 引用卡消费本文档;v11.0 PoC 实施者按 §6.2 风险登记表 + §5.5(05-POC-PLAN.md 引用卡)实施 PoC acceptance criteria。

**与 v2.0 PRFP 的方法论连贯性:** 本文档的方法论 canon 引用 v2.0 PRFP §1.1-§1.6(§1.1 简化版),确保 v10.0 与 v2.0 在第一性原理方法论上一脉相承。v2.0 PRFP 的稳定性标记(§1 stable + §3+§4 evolving)是本文档的范式 —— v10.0 选「全部 stable」是因为 7 决策已 cross-validation 锁定,无 evolving 空间(任何 evolution 需新 milestone)。

**v10.0 milestone 之后:** v11.0 PoC 实施时,本文档作为不可移根论据;v12+ 扩展(music video / long-form / 多 agent 系统协作)时,本文档的 §3 row 5(A2A v12+ 扩展位)+ §3 row 10(per-agent mem0 instance v12+ 物理分区)+ §5.6(06-CROSS-REPO-IMPACT.md 引用卡)是扩展的 entry point。

---

## References(本文档引用的全部 source)

### v10.0 research sources(4 docs,HIGH confidence)

- **STACK.md** — `.planning/research/v10-orchestrator-design/STACK.md`(commit `d647110a1`):MCP 协议层 API 表面 + 7 个新 tool schema + transport 选型 + token 成本分析
- **FEATURES.md** — `.planning/research/v10-orchestrator-design/FEATURES.md`(commit `8f315a473`):2026 multi-agent orchestration frameworks landscape(8 framework 对照 + 27 borrowable design points + 7 anti-features)
- **ARCHITECTURE.md** — `.planning/research/v10-orchestrator-design/ARCHITECTURE.md`(commit `c7030aba8`):Hermes-native agent registry + round table orchestrator architecture(18-field schema + 15-expert transform + per-agent memory + curator evolution phase)
- **PITFALLS.md** — `.planning/research/v10-orchestrator-design/PITFALLS.md`(commit `98672f0d3`):per-agent scoped memory + curator-driven self-evolution 失败模式(14 pitfall,7 load-bearing)
- **SUMMARY.md** — `.planning/research/v10-orchestrator-design/SUMMARY.md`(commit `de12d5f74`):4 research source 综合执行摘要 + Design Decisions Validated 表 + Open Questions + Roadmap Implications + Risk Register

### 方法论 source(v2.0 PRFP,HIGH confidence)

- **v2.0 PRFP `00-FIRST-PRINCIPLES.md`** — `.planning/research/v2-pipeline-design/00-FIRST-PRINCIPLES.md`(1638 行):Musk 第一性原理 / Aristotle 根 / Epistemic-status taxonomy / Steelman-the-Elimination / MADR alternatives log 完整 canon(§1.1-§1.6)。本文档 §1.1 简化版引用此 source。

### 项目 context(HIGH confidence)

- **PROJECT.md** — `.planning/PROJECT.md`:v10.0 milestone 上下文 + 7 锁定决策表 + paradigm shift 4 段声明(§1.3 verbatim 引用 lines 51-57)
- **ROADMAP.md** — `.planning/ROADMAP.md`:Phase 44-51 设计文档依赖图 + DESIGN-01..07 requirement mapping
- **REQUIREMENTS.md** — `.planning/REQUIREMENTS.md`:DESIGN-01 first-principles derivation 验收条件
- **STATE.md** — `.planning/STATE.md`:v10.0 milestone 当前状态

### Kimi 方案 source(NOTION,引用但显式拒绝)

- **Kimi Notion 架构2.0 page** — page_id `39511082-af8e-80d7-83b6-e5df50d3f07c`(Kimi 2026-07-06 生成):CC 是 agent 容器 + 执行器(`.claude/agents/*.md` Teammates)的 Kimi 默认方案。本文档 §1.3(paradigm-shift-claim-1)+ §2.5(决策 #5 排除候选 (b))+ §3 row 1(subagent 容器否决)+ §4.3(B4.1 评估)显式拒绝此方案;详细对照 deferred 到 Phase 47(03-COMPARISON-VS-KIMI-MCP-SHIM.md)。

### Hermes 内部 codebase(v11.0 PoC 实施时直接读)

- `mcp_serve.py`(907 lines):v11.0 PoC 实施时扩展 7 个 round table MCP tool(STACK §5 伪代码 patch)
- `agent/curator.py`(2467 lines):v6.0 `_feedback_scan_phase` + v10.0 `_memory_evolution_phase` add(ARCHITECTURE §3.4)
- `plugins/memory/mem0/__init__.py`(375 lines):v7.0 mem0 backend + v10.0 `_read_filters` additive extension(ARCHITECTURE §3.3)
- `agent/skill_utils.py`(740 lines):SKILL discovery primitive,v10.0 generalizes 为 agent YAML scanner(ARCHITECTURE §4.1)

---

*End of 00-FIRST-PRINCIPLES.md. Document status: stable(§1-§6 全部 stable,修改需开新设计-修订里程碑)。Authors: v10.0 Phase 44 design team. Stability marker analog: v2.0 PRFP §1.1(modification threshold = new milestone).*
