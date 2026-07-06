# Project Research Summary — v10.0 Orchestrator Design

**Project:** Hermes-Agent v10.0 — 编排架构第一性原理推导(设计型 milestone,零代码)
**Domain:** Multi-agent orchestration framework design(per-agent scoped memory + curator-driven self-evolution + round-table protocol over MCP)
**Researched:** 2026-07-06
**Confidence:** HIGH(4 个 research 子任务均基于 in-repo 实读 + 一手业界 docs)
**Predecessors:** STACK.md (`d647110a1`) · FEATURES.md (`8f315a473`) · ARCHITECTURE.md (`c7030aba8`) · PITFALLS.md (`98672f0d3`)

---

## Executive Summary

v10.0 不写一行业码,而是把"Hermes 控结构 / CC 控内容"这套分层协作模型从 7 个已锁的设计决策推导成 7 份可被 v11.0 PoC 实施者直接照着写的设计文档。四个 research 子任务从四个不同视角交叉验证了同一组结论:**T6 协议层走 MCP stdio 单 server 扩展现有 `mcp_serve.py`(STACK),不是业界最炫但最适合 Hermes 现状;agent 形态业界没有原生组合能匹配 v10.0 的「YAML + per-agent scoped memory + curator 自进化」三件套(FEATURES),v10.0 是真正的差异化设计;18-field YAML schema + mem0 filter 路由 + curator `_memory_evolution_phase` 三层叠加在现有 v6.0/v7.0 设施上,不需新基础设施(ARCHITECTURE);但 per-agent memory + curator 自进化是业界公认的"hard problem"—— MemGPT、mem0、LangChain 全部在 production 栽过跟头,14 个 pitfall 里 10 个是 rewrite-class,P1/P2/P4/P5/P6/P8 是 v11.0 PoC 不能 defer 的硬风险(PITFALLS)。**

**推荐路径:** 先写 `00-FIRST-PRINCIPLES.md` 锁定否决/赞同业界形态的论据 → 再写 `01-AGENT-REGISTRY-SCHEMA.md`(13 个 PITFALL 字段的物理载体)→ 然后 `02-ROUND-TABLE-PROTOCOL.md`(消费 schema、解决冲突、注入 project_id)→ `03-COMPARISON-VS-KIMI-MCP-SHIM.md` 和 `06-CROSS-REPO-IMPACT.md` 是横切对照,可并行 → `04-MIGRATION-PATH.md` 依赖 01/02 → `05-POC-PLAN.md` 是收口,把所有 PITFALL 的 PoC 验收条件汇总成清单。

**关键风险:** 7 个 load-bearing pitfalls(persona drift / stale memory / cross-project leakage / curator failure modes / memory poisoning / no fitness signal / round-table memory conflict)全部汇聚在 v11.0 PoC 的内存子系统上。v10.0 设计文档必须在 `01-AGENT-REGISTRY-SCHEMA.md` 里把 `persona_sha256` + 三层 memory tier(core/working/archival)+ `scope` + `expires_at` + `confidence` + `evidence_chain` 这 7 个字段固化下来,否则 v11.0 PoC 实施者会像 LangChain / mem0 早期用户一样在 production 重新踩坑。

---

## Cross-Cutting Findings(4 个 research 之间的交叉洞察)

### CC-1: STACK §3.2 的 7 tool Pydantic schema ↔ FEATURES §10 的 27 borrowable design points ↔ ARCHITECTURE §4.2 的 MCP tool 表

三处都列了"agent-facing MCP tool",但粒度不同:**STACK §3.2** 给的是带 `ToolAnnotations` + Pydantic Model + JSON Schema 的实施级签名(7 tool);**FEATURES §10** 给的是借鉴 LangGraph/AutoGen/CrewAI 提炼的设计点(27 条);**ARCHITECTURE §4.2** 给的是 dispatch path 与 `agent_registry` 的对接(7 tool,命名略有差异,如 `agent_get_persona` vs STACK 的 `get_agent_persona`)。**冲突点:** ARCHITECTURE §4.2 用 `agent_get_persona` / `agent_recall` / `agent_conclude`(agent_ 前缀),STACK §3.2 用 `get_agent_persona` / `get_agent_memory` / `query_memory`(无前缀)。**下游 `02-ROUND-TABLE-PROTOCOL.md` 必须先统一命名**,否则 v11.0 PoC 实施者会困惑。建议采用 STACK 形态(与现有 `mcp_serve.py` 9 个 messaging tool 风格一致,无前缀)。

### CC-2: ARCHITECTURE §1.1 的 18-field schema ↔ PITFALLS 的字段级缓解

18-field schema 里有 **8 个字段是直接由 PITFALLS 反推出来的"防护字段"**:`persona`(隐含 PITFALL-1 persona drift,但 PITFALLS §1 mitigation 3 要求拆 `core_memory`/`archival_memory` —— **当前 18-field schema 没有 core/archival 分层,是 gap**),`memory_scope`(PITFALL-4 cross-project leakage mitigation 1),`evolution_log`(PITFALL-5 curator failure modes mitigation 5 dry-run-first),`fitness_score`(PITFALL-8 no fitness signal)。但 PITFALLS 还要求 5 个 schema 字段在 18-field 里没出现:`expires_at` / `verified_at` / `supersedes_memory_id` / `confidence` / `half_life_days`(全部来自 PITFALL-2 stale memory)、`evidence_chain` / `evidence_operator_ids` / `status="archived|quarantined"`(PITFALL-5/6)、`confidentiality`(PITFALL-10 privacy)、`scope: "global|project|session"`(PITFALL-4 三层 scope,比 ARCHITECTURE 的 `shared|per_agent|project_scoped` 更细)。**这些字段属于"memory record schema",不是"agent YAML schema"** —— `01-AGENT-REGISTRY-SCHEMA.md` 必须显式区分这两层,否则会被误以为 18-field schema 不够用。

### CC-3: STACK §4 的 stdio-only transport ↔ ARCHITECTURE §5.1 的 round-table state JSON ↔ FEATURES §1.3 的 LangGraph checkpointer/store 双层

三者讲的是同一个事:**短期(round-table 进行中)vs 长期(跨项目 memory)的存储分层**。STACK §4 选 stdio 意味着 round-table 不能靠 transport 维持长连接,必须靠 STACK §3.2 Tool 4 `submit_round_table_result` 落盘 + ARCHITECTURE §5.1 `~/.hermes/agents/.runtime/{slug}/round_tables/{id}.json` 持久化。这正好对应 FEATURES §1.3 LangGraph 的 Checkpointer(短期)vs Store(长期)双层抽象(B1.2 borrowable point)。**结论:** round table state JSON 文件 = Hermes 版的 Checkpointer;mem0 backend = Hermes 版的 Store。`02-ROUND-TABLE-PROTOCOL.md` 应显式引用 LangGraph 双层抽象作为设计类比。

### CC-4: ARCHITECTURE §3.2 Option B (agent_id 路由)↔ PITFALLS §3 mitigation 1(物理分区)↔ STACK §3.2 Tool 3 `get_agent_memory`

ARCHITECTURE 推荐 Option B(mem0 单 backend + `agent_id` filter),PITFALLS §3 说 Option B 在 18-agent × 100-project 规模下会因 HNSW 全局图 + post-filter 崩溃,推荐 mitigation 1(每 agent 一个 mem0 workspace)。**冲突需要在 `06-CROSS-REPO-IMPACT.md` 解决:** v11.0 PoC(15 agent,单项目)用 Option B 即可;v12+(50+ agent,多项目)必须迁到物理分区。STACK §3.2 Tool 3 `get_agent_memory` 的 `agent_id` 参数同时支持两种部署 —— API 不变,后端切换。**这个生命周期决策要在 `06-CROSS-REPO-IMPACT.md` 显式记录**,避免 v12 实施者重新讨论一遍。

### CC-5: FEATURES §11 anti-features ↔ ARCHITECTURE §8 anti-patterns ↔ PITFALLS 行业案例

三处都列了"不要做什么",但维度互补:**FEATURES §11** 是从业界 framework 抄来的反面教材(subagent 作容器 / 短命 agent / handoff 作 round table / crew pipeline 作协商 / memory:boolean);**ARCHITECTURE §8** 是 Hermes 内部反模式(YAML 作 prompt dump / auto-re-transform on drift / round table as pipeline step / per-agent mem0 instance / cross-layer import);**PITFALLS** 是 memory subsystem 的失败模式(persona drift / stale memory / scoped retrieval perf collapse 等)。**`00-FIRST-PRINCIPLES.md` 应把这三层 anti-features/anti-patterns 合并成一张"v10.0 显式拒绝"总表**,每条引用三个 source 中的具体章节号。

### CC-6: STACK §7 token 成本(~550K/pipeline run)↔ PITFALLS §3 mitigation 3(memory budget cap 500)↔ FEATURES §14 gap 6(GLM 4-key rotation × multi-panelist 并发)

STACK 估算单 pipeline run ~550K tokens(80 个 opinion call × 6.5K tokens),假设串行;PITFALLS 说每 agent memory ≤500 records;FEATURES §14 gap 6 指出 GLM 4-key rotation 跟 multi-panelist 并发的成本模型未算。这三者合起来意味着:**round table 必须是串行的(1 panelist 1 turn,不能并发),否则 GLM 4-key rotation 会在并发的 7 panelist × N rounds 里立刻撞 ceiling**。这是对 `02-ROUND-TABLE-PROTOCOL.md` 的硬约束 —— **不能做成"7 panelist 并行调用 LLM"**,必须按 STACK §7.5 顺序 `await`。MEMORY.md 里 `feedback-glm-overload-reduce-concurrency.md` 的全局 concurrency==1 policy 强化了这一约束。

---

## Design Decisions Validated(7 锁定决策 × 4 research 的支持/反对/修正)

| # | 决策 | STACK 支持 | FEATURES 支持 | ARCHITECTURE 支持 | PITFALLS 警告 |
|---|------|-----------|--------------|-------------------|---------------|
| **1** | T6 协议:Hermes MCP server + tmux dispatch + CC native MCP client | **强支持** —— §1-§5 全文证明 FastMCP + `@mcp.tool()` 是 stable,stdio 已 ✓ Connected,零架构改动 | **强支持** —— §7.4 Microsoft 三层协议分层(B7.1)直接验证 "internal → platform-native; tool → MCP; cross-platform → A2A" | 中性 —— §4.2 假设 T6 已锁,只在 dispatch path 上展开 | §P10 privacy:MCP 单进程 stdio 是隐私正面(无网络面),但 round-table coordinator 跨 project 聚合上下文仍是攻击面 |
| **2** | B3a Python runner 增量迁移 | **强支持** —— §3.2 Tool 7 `run_python_phase` 是 boundary tool,`openWorldHint=True` 标注 ComfyUI 调用 | 不直接覆盖 | 中性 | 不直接覆盖 |
| **3** | D2 storyboard-first-class | 不直接覆盖 | 部分 —— §2.3 AutoGen nested chat(B2.3)支持 sub-panel | 不直接覆盖 | **间接警告** —— CC-6 指出 round table 不能真并发,"并行"必须是 orchestrator 层 dispatch 多个独立 round table |
| **4** | G2 通用编排框架 | 不直接覆盖 | **核心支持** —— §10 的 27 borrowable design points 是 G2 的设计原料 | **支持** —— §4 sibling registry + §5 round-table state layer 是 G2 的 Hermes 实例化 | 间接 —— 整个 PITFALLS 都是 G2 必须处理的失败模式 |
| **5** | α agent form:YAML + persona + tools + refs + memory_scope + lineage | **支持** —— §3.2 Tool 1 假设此形态 | **强支持** —— §3 CrewAI / §4 Claude Agent SDK 对照后,v10.0 的 YAML-first + persona + memory_scope + lineage 是业界独有组合;§11 显式否决 Claude Agent SDK subagent 形态(B4.1) | **强支持** —— §1 18-field schema + §2 15-expert transform mapping 是 α 形态的完整规范 | **修正** —— §P1 persona drift 要求 18-field 之外加 `persona_sha256` + `core_memory`/`archival_memory` 分层;§P2 要求 memory record 加 `expires_at`/`verified_at`/`confidence`/`half_life_days` |
| **6** | per-agent memory + curator-driven 自进化 | **支持** —— §3.2 Tool 3/6 假设 mem0 backend 已能 per-agent scope,但 mem0 backend 真实 filter 行为未实测(M-置信) | **强支持** —— §9.2 memory 模式速查表显示"没有一个主流框架把 per-agent scoped memory + curator-driven 自进化作为原生组合",v10.0 是真正的差异化 | **强支持 + 修正** —— §3.1 现有 mem0 `_read_filters()` 只返 `user_id`,需 §3.3 additive extension 加 `_scoped_agent_id`;§3.4 curator 加 `_memory_evolution_phase` | **核心警告** —— 整个 PITFALLS 都是 #6 的失败模式;P1/P2/P3/P4/P5/P6/P7/P8/P9/P10 全部直接相关。**v10.0 设计文档必须在 `01-AGENT-REGISTRY-SCHEMA.md` 把这些字段固化** |
| **7** | 分层 CC 角色:Hermes 控结构,CC 控内容 | **支持** —— §3.2 turn_order 由 Hermes 通过 schema 控制;CC 通过 `prior_discussion` 控上下文折叠 | **强支持** —— §1.3 LangGraph supervisor 是路由器不是协调员(B1.3),与决策 #7 同构;§4 Claude Agent SDK subagent 默认 context-isolated,不适合做 round table panelist(B4.1) | **支持** —— §5.3 lifecycle sketch:Hermes 控 turn_order/max_rounds/early_stop_rule;CC 控 question framing/synthesis | §P7 round-table memory conflict 要求 Hermes 增加新职责:coordinator arbitrates memory conflicts(原本 #7 没明说 Hermes 仲裁 memory 冲突) |

---

## Open Questions Consolidated(去重后)

| # | 问题 | 出处 | 倾向性结论 | 在哪解决 |
|---|------|------|-----------|---------|
| **OQ-1** | persona 版本控制:operator 手改 persona 后,prior version 是 archive 进 `evolution_log` 还是只留 diff? | ARCHITECTURE §10.1 + PITFALLS §P1 mitigation 4 | **diff only**(operator 自己用 git 管 `~/.hermes/agents/`),但 memory record 必须带 `persona_sha256` 快照 | `01-AGENT-REGISTRY-SCHEMA.md` |
| **OQ-2** | round table `turn_order` 策略:round-robin / fitness-weighted / seniority / LLM / matrix? | ARCHITECTURE §10.2 + FEATURES §2.3(B2.1 三态 llm/fixed/matrix) | **default round-robin**,通过 `round_table_open` arg 可切换;fitness-weighted 留 v11.1+ | `02-ROUND-TABLE-PROTOCOL.md` |
| **OQ-3** | mem0 `agent_id` 冲突:v7.0 默认 `agent_id=hermes` 的旧 memory 怎么处理? | ARCHITECTURE §10.3 | **遗留**(不迁移),新 agent invocation 从 `agent_id=screenplay` 等开始 | `04-MIGRATION-PATH.md` |
| **OQ-4** | `fitness_score` 冷启动:agent 初始 `null`,orchestrator 怎么处理? | ARCHITECTURE §10.4 + PITFALLS §P8 | **null = neutral 0.5** for ordering;UI 显示 "untested" | `01` + `02` |
| **OQ-5** | agent 删除:historical round table state 怎么处理 orphan 引用? | ARCHITECTURE §10.5 | **open 时 snapshot identity**,deleted agent 在 transcript 显示 "deleted" badge | `02-ROUND-TABLE-PROTOCOL.md` |
| **OQ-6** | project slug 重命名稳定性 | ARCHITECTURE §10.6 | **接受 breakage**(已知限制),long-term 用 `.hermes/project.id` stable ID | `06-CROSS-REPO-IMPACT.md` |
| **OQ-7** | `memory.max_records` 上限:500 够不够?compaction 何时触发? | PITFALLS §3 mitigation 3 + §P9 | **default 500**, curator 每 N tick 跑 compaction pass | `01` + `05` |
| **OQ-8** | GLM 4-key rotation × multi-panelist 并发成本 | FEATURES §14 gap 6 + STACK §7.5 + MEMORY.md `feedback-glm-overload-reduce-concurrency.md` | **强制串行**(1 panelist 1 turn,顺序 await),不能并发 | `02` + `05` |
| **OQ-9** | MCP tool 命名:STACK `get_agent_persona` vs ARCHITECTURE `agent_get_persona`? | CC-1 above | **用 STACK 形态**(无前缀,与现有 messaging tool 风格一致) | `02-ROUND-TABLE-PROTOCOL.md` |
| **OQ-10** | `run_python_phase` 的 retained-phases allowlist 在哪定义? | STACK §11.2 | **`round-table-schema.yaml`** | `04-MIGRATION-PATH.md` |
| **OQ-11** | CC 端如何拿到 `round_id`?Hermes 注入还是 CC 自生成 uuid? | STACK §11.3 | **CC 自生成 uuid**,在 `round_table_open` 调用时传入 | `02` |
| **OQ-12** | mem0 backend 是否需要 per-agent collection/workspace 隔离? | STACK §11.4 + ARCHITECTURE §3.2 + PITFALLS §3 mitigation 1 + CC-4 | **v11.0 PoC:** Option B(filter 路由);**v12+:** 物理分区(每 agent 一 workspace) | `06-CROSS-REPO-IMPACT.md` |
| **OQ-13** | agent YAML `tools` 字段是否枚举(限制每个 agent 只能调特定 MCP tool)? | STACK §11.5 + ARCHITECTURE §1.1 field 5 | **YES** —— `tools` 是 runtime whitelist,enforced by dispatcher(ARCHITECTURE §4.3) | `01` |
| **OQ-14** | agent persona YAML schema 是否需要 JSON Schema 正式定义? | FEATURES §14 gap 2 | **YES** —— `agents-schema.yaml` 文件 | `01` |
| **OQ-15** | round-table conflict 仲裁:Hermes coordinator 用什么 LLM 策略? | PITFALLS §P7 mitigation 2 | comparator LLM pass + scope precedence(session > project > global)+ confidence-weighted voting | `02` |
| **OQ-16** | curator `_memory_evolution_phase` 跟 v6.0 `_feedback_scan_phase` 的执行顺序与隔离边界? | ARCHITECTURE §3.4 + PITFALLS §P5 mitigation 5 | **`_memory_evolution_phase` 跑在 `_feedback_scan_phase` 之后**,独立 try/except 包裹,dry-run-by-default | `01` |

---

## Roadmap Implications(为 gsd-roadmapper)

### 设计文档依赖图

```
00-FIRST-PRINCIPLES.md ─┬─> 01-AGENT-REGISTRY-SCHEMA.md ─┬─> 02-ROUND-TABLE-PROTOCOL.md ──> 04-MIGRATION-PATH.md ──> 05-POC-PLAN.md
                        │                                │
                        └─> 03-COMPARISON-VS-KIMI-MCP-SHIM.md (parallel)
                        └─> 06-CROSS-REPO-IMPACT.md (parallel)
```

### 建议的 phase 顺序

**Phase P45-a: `00-FIRST-PRINCIPLES.md`(先写)**
- **Rationale:** 锁定 7 决策的推导论据 + 业界 anti-features 合并总表
- **Delivers:** "v10.0 显式拒绝"总表(FEATURES §11 + ARCHITECTURE §8 + PITFALLS 行业案例三合一)
- **Addresses:** FEATURES §10 中至少 B1.3 / B3.5 / B4.1 / B7.2 / B5.1

**Phase P45-b: `01-AGENT-REGISTRY-SCHEMA.md`(紧随)**
- **Rationale:** 18-field agent YAML schema + memory record schema 是所有下游文档的字段载体
- **Delivers:** `agents-schema.yaml`(JSON Schema 正式定义)+ memory-record-schema.yaml + per-agent memory tier 规范 + curator `_memory_evolution_phase` 字段契约
- **Avoids:** P1 / P2 / P4 / P5 / P8 / P10 / P14(7 个 load-bearing pitfall 的字段级缓解必须在 01 里成型)

**Phase P45-c: `02-ROUND-TABLE-PROTOCOL.md`(依赖 01)**
- **Rationale:** round table 消费 agent schema 的核心场景
- **Delivers:** round-table-state-schema.yaml + turn lifecycle + memory conflict arbitration 规则 + scope precedence + confidentiality propagation + project_id 必传
- **Addresses:** FEATURES B1.4 / B2.1 / B2.3 / B4.2 / B6.1 / B7.3 / B8.2
- **Avoids:** P7 / P10(round-table 层)/ P11 + 强制串行(GLM 4-key 约束)

**Phase P45-d: `03-COMPARISON-VS-KIMI-MCP-SHIM.md`(并行,横切)**
- **Independent of:** 01/02(只消费 7 决策本身)
- **Delivers:** T6 vs Kimi MCP shim 逐维度对照表 + FEATURES B4.1 subagent 否决论据 + B7.1 Microsoft 三层协议验证

**Phase P45-e: `06-CROSS-REPO-IMPACT.md`(并行,横切)**
- **Independent of:** 01/02 的字段细节
- **Delivers:** 3-location 同步策略 + Option B(v11.0)vs 物理分区(v12+)迁移触发条件 + OQ-3 旧 memory 遗留 + OQ-6 project slug 限制

**Phase P45-f: `04-MIGRATION-PATH.md`(依赖 01/02)**
- **Delivers:** 15 expert 5-field transform 规则 + `default_invocation: skill_fallback → mcp_tool` 切换 + memory schema 迁移 + retained-phases allowlist + schema_version
- **Avoids:** P14 schema migration breaks memory store

**Phase P45-g: `05-POC-PLAN.md`(收口,依赖前面所有)**
- **Delivers:** fitness battery + latency SLO(p95 < 500ms)+ bias canary + compaction pass + threshold tuning + dry-run-first invariant + schema migration dry-run —— 全部作为 PoC acceptance criteria
- **Avoids:** 全部 14 pitfalls(PoC must demonstrate mitigations work)

### Research Flags

**需要更深 research 的 phase(建议 `/gsd:plan-phase --research-phase <id>`):**
- **P45-b** `01-AGENT-REGISTRY-SCHEMA.md` —— memory record schema 需调研 mem0 Platform API 真实 filter 行为(STACK M-置信)+ 物理分区 vs 逻辑过滤的规模阈值(PITFALLS §3 + CC-4)
- **P45-c** `02-ROUND-TABLE-PROTOCOL.md` —— turn_order 矩阵模式(FSM 转移矩阵)需调研 AutoGen 0.2 实际 API 表面(FEATURES B2.1 引用但未给 spec)
- **P45-g** `05-POC-PLAN.md` —— fitness battery 设计需调研 Label Studio/Shaped.ai/GetMaxim 的 A/B testing 量化方法(PITFALLS §P8 行业参考)

**有 well-documented patterns 可跳过 research 的 phase:**
- **P45-a** `00-FIRST-PRINCIPLES.md` —— 7 决策已锁,4 research 已提供全部论据
- **P45-d** `03-COMPARISON-VS-KIMI-MCP-SHIM.md` —— FEATURES §4 + §7.4 已提供完整对照
- **P45-e** `06-CROSS-REPO-IMPACT.md` —— ARCHITECTURE §6 已给完整 3-location 表

---

## Risk Register(7 个 load-bearing pitfall,v11.0 PoC 硬风险)

| Risk ID | Pitfall | Severity | PoC-acceptable deferral? | 必须字段/机制 | 在哪文档解决 |
|---------|---------|----------|--------------------------|---------------|--------------|
| **P1** | Persona drift(agent forgets role after accumulating memory) | HIGH | **NO**(load-bearing) | `persona_sha256` 不变量 + tiered memory(core/archival)+ persona-drift probe | `01` + `02` |
| **P2** | Stale memory(cites platform rules that no longer apply) | HIGH | **NO**(load-bearing) | `expires_at` + `verified_at` + `supersedes_memory_id` + `confidence` time-decay | `01` |
| **P4** | Cross-project memory leakage | HIGH | **NO**(load-bearing) | `scope: global\|project\|session` + `project_id` required + cross-project promotion gate | `01` + `02` |
| **P5** | Curator failure modes(false-delete / hallucinate / bias amplify) | HIGH | **NO**(load-bearing) | `evidence_chain` ≥3 + `evidence_operator_ids` 多样性 + dry-run-first + bias canary | `01` + `05` |
| **P6** | Memory poisoning(MINJA-style persistent attack) | HIGH | **PARTIAL**(signed feedback PoC must;outlier detection defer) | `operator_signature`(HMAC)+ rate-limit + quarantine on detection | `01` + `05` + `06` |
| **P8** | No fitness signal(can't tell if agent getting better) | HIGH | **NO**(load-bearing) | `fitness_battery` + `fitness_trend.jsonl` + A/B shadow mode + model_id 隔离 | `01` + `05` |
| **P7** | Round-table memory conflict | MEDIUM | **NO**(round-table is v10.0 core) | coordinator arbitration + scope precedence + confidence-weighted voting + conflict log | `02` |

**额外 7 个非 load-bearing(v11.0 可部分 defer):** P3 scoped retrieval perf / P9 memory size growth / P10 privacy(leakage)/ P11 recall-vs-use / P12 cross-agent contamination / P13 curator runaway / P14 schema migration。

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| **Stack(MCP 协议层)** | HIGH | STACK 基于 installed `mcp==1.26.0` 实测 + 现有 `mcp_serve.py` 全文实读;CC 配置 `claude mcp list` ✓ Connected 实测 |
| **Features(业界 framework 对照)** | HIGH | 4 个 HIGH 置信度框架(LangGraph/MAF/CrewAI/Claude Agent SDK)官方 docs 一手对照 |
| **Architecture(Hermes 内部设施)** | HIGH | 直接实读 v6.0 curator / v7.0 mem0 plugin / kais-hermes-skills SKILL frontmatter / Hermes tool & skill discovery —— 全部 in-repo |
| **Pitfalls(per-agent memory 失败模式)** | HIGH | 跨证于 6+ 业界项目(MemGPT/Letta、mem0、LangChain、AutoGen、ReConcile、MINJA、Echoleak) |

**Overall confidence:** **HIGH**。4 个 research 子任务独立得出一致的结论,每个结论都有 in-repo 代码 + 业界一手 docs 双重证据。

### Gaps to Address(留待 v11.0 PoC 实测)

- **mem0 Platform API 真实 filter 行为(OQ-12):** ARCHITECTURE 推荐 Option B,但 mem0 在 18-agent × 100-project 规模下的 HNSW post-filter 性能未实测。**v11.0 PoC week-1 跑 latency benchmark**,若 p95 > 500ms 立即触发物理分区切换(CC-4)。
- **GLM 4-key rotation × multi-panelist 真实并发成本(CC-6):** ~550K tokens/pipeline run 估算基于串行,GLM ceiling 是 4 key × 200K TPM ≈ 800K TPM。**v11.0 PoC 第一次 multi-round round table 会立即暴露真实成本**,需 monitor。
- **curator `_memory_evolution_phase` LLM aggregation 准确率:** v6.0 `_feedback_scan_phase` 已 ship,但 memory-write 路径是新加的,hallucination rate 未测。**v11.0 PoC acceptance criterion:`evidence_chain` coverage check + bias canary 必须跑通。**
- **round table state 在 CC crash 时的 recovery:** ARCHITECTURE §5.1 落盘到 `.runtime/{slug}/round_tables/{id}.json`,但 CC 中途 crash 后 Hermes 如何 detect + cleanup unfinished round table 没设计。**v11.0 PoC 需补 gc pass。**
- **mem0 `_scoped_agent_id` 并发安全(ARCHITECTURE §3.3):** 用 `contextvars` 还是 `threading.local` 在 ThreadPoolExecutor 下行为不同。**v11.0 PoC 实施时必须选 contextvars**(`agent/tool_executor.py` 已用)。

---

## Sources(聚合 4 research 的源,按置信度分层)

### Primary / in-repo(HIGH,STACK/ARCHITECTURE/PITFALLS 共同基石)

- `/data/workspace/hermes-agent/mcp_serve.py`(907 lines,全文实读)
- `/data/workspace/hermes-agent/agent/curator.py`(2467 lines,v6.0 `_feedback_scan_phase` 实读)
- `/data/workspace/hermes-agent/agent/feedback_store.py`(sha256 dedup + supersession + time-decay)
- `/data/workspace/hermes-agent/agent/evolution/*`(insights/diff_generator/apply/queue)
- `/data/workspace/hermes-agent/plugins/memory/mem0/__init__.py`(375 lines,v7.0 ship)
- `/data/workspace/hermes-agent/agent/skill_utils.py`(740 lines)
- `/data/workspace/hermes-agent/tools/registry.py`(AST-scan)
- `/data/workspace/hermes-agent/.planning/PROJECT.md`(7 锁定决策源)
- `/home/kai/.local/lib/python3.12/site-packages/mcp/`(installed `mcp==1.26.0` 内省)
- `/data/workspace/kais-hermes-skills/skills/movie-experts/_shared/v86-pipeline-mapping.md`(15-expert DAG)

### Industry docs(HIGH,FEATURES 主源)

- LangGraph: https://docs.langchain.com/oss/python/langgraph/persistence , https://reference.langchain.com/python/langgraph-supervisor
- MAF 1.0 GA: https://learn.microsoft.com/en-us/agent-framework/overview/ , https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/
- Microsoft multi-agent patterns: https://learn.microsoft.com/en-us/agents/architecture/multi-agent-patterns
- CrewAI v1.15.1: https://docs.crewai.com/v1.15.1/en/concepts/agents
- Claude Agent SDK: https://code.claude.com/docs/en/agent-sdk/overview , https://code.claude.com/docs/en/agent-sdk/subagents
- A2A: https://www.deeplearning.ai/courses/a2a-the-agent2agent-protocol

### Peer-reviewed research(HIGH,PITFALLS 主源)

- ReConcile (ACL 2024): https://aclanthology.org/2024.acl-long.381/
- MINJA: https://arxiv.org/html/2606.04329v1
- Black-box Persona Drift Detection: https://arxiv.org/html/2605.09863v1
- Camel-AI: https://arxiv.org/abs/2303.17760
- RoundTable: https://arxiv.org/html/2411.07161v2

### Vendor / community research(MEDIUM)

- mem0 blog: https://mem0.ai/blog/remote-memory-for-ai-agents-running-at-the-edge , https://mem0.ai/blog/ai-memory-security-best-practices
- Letta blog: https://www.letta.com/blog/memory-blocks/
- LangChain memory docs: https://reference.langchain.com/python/langchain-classic/memory/token_buffer/ConversationTokenBufferMemory
- OWASP LLM01:2025: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- Palo Alto Unit 42: https://unit42.paloaltonetworks.com/indirect-prompt-injection-poisons-ai-longterm-memory/
- Giskard Cross Session Leak: https://www.giskard.ai/knowledge/cross-session-leak-when-your-ai-assistant-becomes-a-data-breach
- Label Studio: https://labelstud.io/learningcenter/how-to-evaluate-agent-memory/
- GetMaxim: https://www.getmaxim.ai/articles/a-b-testing-strategies-for-ai-agents-how-to-optimize-performance-and-quality/

---

*Synthesized 2026-07-06 from STACK.md (`d647110a1`) + FEATURES.md (`8f315a473`) + ARCHITECTURE.md (`c7030aba8`) + PITFALLS.md (`98672f0d3`).*
