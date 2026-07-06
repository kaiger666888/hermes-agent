# Technology Stack — v10.0 Orchestrator Design (T6 协议层)

**Project:** Hermes-Agent v10.0 — Hermes-Agent 编排架构第一性原理推导(设计型 milestone)
**Scope of this document:** T6 协议层选型 —— MCP Python SDK API 表面、`mcp_serve.py` 扩展 patch 样例、CC 端 `claude mcp add` 配置、transport 选型、7 个新 tool 的 input/output schema
**Researched:** 2026-07-06
**Overall confidence:** HIGH(most API 表面来自已安装 mcp==1.26.0 的运行时内省 + 现有 `mcp_serve.py` 实读)

---

## TL;DR(v11.0 PoC 实施者必读)

- **MCP SDK:** `mcp==1.26.0`(本 repo `pyproject.toml:197` 已锁),**FastMCP 是 stable API**(`@mcp.tool()` decorator + 类型自动派生 JSON Schema),**low-level `mcp.server.Server` 是 legacy 路径**不要走。
- **现有 `mcp_serve.py` 扩展:** **零架构改动**,在同一个 `FastMCP("hermes")` 实例上叠加 7 个 `@mcp.tool()` 函数即可。`create_mcp_server()` 末尾的 `return mcp` 之前是注册边界,EventBridge 已有的 background polling 不动。
- **Transport:** **stdio 是 v11.0 PoC 唯一推荐** —— CC `claude mcp add` 默认 stdio;round table 长跑靠 `events_wait` long-poll + tmux dispatch,不靠 transport 本身。SSE / Streamable HTTP 在 v11.0 PoC 范围之外(见 §4 详细分析)。
- **CC 端配置:** `~/.claude.json` 已含 hermes server 配置,**只需在 7 个新 tool 注册后重启 CC 一次**(local scope 自动 reconnect)。MCP `tools/list` 是动态发现,无需改 config。
- **Token 成本:** 1 个 round table ≈ 7 个 expert × 3 turns × 1-2 MCP call/turn ≈ **21-42 MCP call / round table**。每个 MCP call input ~2-5KB(含 prior discussion),output ~1-3KB(opinion)。**总 token: ~150-300KB input / ~50-100KB output / round table**。

---

## 1. Recommended Stack(MCP 协议层)

### Core Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **`mcp` Python SDK** | `==1.26.0`(已锁) | MCP server + tool registration + transport | 官方 SDK;FastMCP 高层 API 在 1.26 是 stable 路径,deprecation 风险最低;本 repo 已用,无新依赖 |
| **`mcp.server.fastmcp.FastMCP`** | 同上 | Tool 注册 + decorator-based API | 单类暴露 `.tool()` / `.add_tool()` / `.run_stdio_async()` / `.run_streamable_http_async()` / `.run_sse_async()`,API 表面简洁、无样板代码 |
| **`mcp.server.fastmcp.Context`** | 同上 | tool 内 progress reporting / logging / elicitation(2026 新增) | long-running tool 可向 CC push progress;`ctx.info/debug/warning/error` 写 CC 终端日志;Elicitation(`ctx.elicit`)允许 server 向 CC 用户问表单(2025 末加的能力) |
| **`mcp.types`** | 同上 | `Tool` / `ToolAnnotations` / `CallToolResult` / `ContentBlock` 等 schema 类型 | 类型化协议契约;`ToolAnnotations` 含 `readOnlyHint` / `destructiveHint` / `idempotentHint` / `openWorldHint`,可声明 tool 副作用语义给 CC 看 |
| **Pydantic** | `==2.13.4`(已锁) | tool 输入/输出 schema 派生 + `structured_output=True` | FastMCP 用 `pydantic.model_json_schema()` 把 Python type hint → JSON Schema,无需手写 |
| **Claude Code CLI** | `2.1.143`(已安装) | MCP client side,通过 `claude mcp add` 配置 | CC 的 stdio MCP client 已与 hermes 通过 `~/.claude.json` projects 段配置好并 ✓ Connected(`claude mcp list` 实测) |

### Database / State Layer(7 个新 tool 用到的)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **`~/.hermes/agents/{name}.agent.yaml`** | (新文件) | agent YAML 实体(persona + tools + refs + memory_scope + lineage) | 决策 #5(α) 锁定的物理位置;`get_agent_persona` / `get_agent_opinion` 读取 |
| **`~/.hermes/state.db`** | SQLite,沿用 | EventBridge 已在 poll | round table 中间产物(receipt_id, status)落 SQLite,无需新基础设施 |
| **mem0 plugin** | v6.0 已 ship | per-agent scoped memory | 决策 #6 锁定;`get_agent_memory` / `query_memory` 走 mem0 backend |
| **existing `tools.send_message_tool`** | 沿用 | CC 把结果回推给 gateway 用户 | round table 完成时通知用户(复用现成 messaging bridge,无新代码) |

### Infrastructure(零新增)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **tmux** | 系统包 | dispatch long-running CC subagent | v7.0 `coding-agent` skill 已 ship 的 dispatch 模式;`tmux new-session -d -s hermes-round-table-{id} ...` |
| **FastAPI / Uvicorn** | 已锁 | dashboard API server | **不动**;7 个新 tool 不依赖 FastAPI,直接走 MCP FastMCP |
| **starlette==1.0.1** | 已锁(CVE-2026-48710 pin) | MCP `streamable-http` / `sse` transport 底层 | 现有 pin 已合规;若 v11.0 PoC 走 stdio,根本用不到,但 pin 留着无害 |

### Supporting Libraries(零新增)

无新依赖。v10.0 是设计型 milestone,产出文档不产代码;v11.0 PoC 也**不需要**新增任何 PyPI 包 —— mcp + pydantic + ruamel.yaml(agent YAML 解析)+ 现有 send_message_tool 足够。

---

## 2. MCP Python SDK — 当前 stable API 表面

> **来源:** 对 `/home/kai/.local/lib/python3.12/site-packages/mcp/` 的运行时内省 + `inspect.signature()` + `inspect.getsource()`。这是 mcp==1.26.0 实际安装包,与 uv.lock 中 `name = "mcp"` / `version = "1.26.0"` 一致。**Confidence: HIGH。**

### 2.1 FastMCP 构造器(完整 signature)

```python
FastMCP(
    name: str | None = None,
    instructions: str | None = None,
    website_url: str | None = None,
    icons: list[Icon] | None = None,
    auth_server_provider: OAuthAuthorizationServerProvider | None = None,
    token_verifier: TokenVerifier | None = None,
    event_store: EventStore | None = None,
    retry_interval: int | None = None,
    *,
    tools: list[Tool] | None = None,            # 1.26 新增:启动期一次性注入工具列表
    debug: bool = False,
    log_level: Literal['DEBUG','INFO','WARNING','ERROR','CRITICAL'] = 'INFO',
    host: str = '127.0.0.1',                     # HTTP/SSE transport only
    port: int = 8000,                            # HTTP/SSE transport only
    mount_path: str = '/',
    sse_path: str = '/sse',                      # SSE endpoint path
    message_path: str = '/messages/',            # legacy SSE message path
    streamable_http_path: str = '/mcp',          # 2025 Streamable HTTP spec
    json_response: bool = False,                 # 1.26 新:HTTP transport 返回 JSON 而非 SSE 流
    stateless_http: bool = False,                # 1.26 新:无状态 HTTP(每次请求自带 session)
    warn_on_duplicate_tools: bool = True,
    warn_on_duplicate_resources: bool = True,
    warn_on_duplicate_prompts: bool = True,
    dependencies: Collection[str] = (),
    lifespan: Callable | None = None,            # 启动/关闭钩子
    auth: AuthSettings | None = None,
    transport_security: TransportSecuritySettings | None = None,
)
```

**v11.0 PoC 关注的 3 个参数:**
- `name` —— 现有 `mcp_serve.py:459` 已传 `"hermes"`,保持不变
- `instructions` —— 现有传 messaging bridge 描述,v11.0 PoC 应**扩展**为同时描述 round-table 能力(影响 CC 的 tool 选择 heuristic)
- `tools=` —— **不推荐用**,会让 `create_mcp_server()` 难读;继续用 `@mcp.tool()` decorator

### 2.2 Tool 注册的 3 种 API(都 stable,但优先用 #1)

#### API #1:`@mcp.tool()` decorator(推荐 / 现有代码用法)

```python
@mcp.tool()                              # 不传任何参数,函数名 + docstring + type hint 全自动
def get_agent_persona(agent_id: str) -> str:
    """Return the persona YAML for a registered agent.

    Args:
        agent_id: Agent identifier (e.g. "screenplay", "cinematographer")
    """
    return _read_agent_yaml(agent_id)
```

Decorator signature(完整):
```python
FastMCP.tool(
    self,
    name: str | None = None,              # 默认 = 函数名
    title: str | None = None,             # 人类可读标题(1.26 新)
    description: str | None = None,       # 默认从 docstring 第一行
    annotations: ToolAnnotations | None = None,  # 副作用声明
    icons: list[Icon] | None = None,
    meta: dict[str, Any] | None = None,
    structured_output: bool | None = None,  # None=自动从返回类型推断
)
```

**关键事实:** `@mcp.tool()` **必须加括号调用**(`@mcp.tool` 裸用会 `TypeError`,见 `FastMCP.tool` 源码 line 71-74 的显式 guard)。现有 `mcp_serve.py` 全部 10 个 tool 都用 `@mcp.tool()` 形式。

#### API #2:`mcp.add_tool(fn, ...)`(命令式)

适合**条件性注册**场景(如某些 tool 仅在特定 plugin 加载后注册):

```python
def _maybe_register_round_table_tools(mcp: FastMCP) -> None:
    """Register v10.0 round-table tools only if agent registry exists."""
    registry_path = Path.home() / ".hermes" / "agents"
    if not registry_path.exists():
        logger.warning("Agent registry not found; round-table tools not registered")
        return

    mcp.add_tool(
        _get_agent_persona_impl,
        name="get_agent_persona",
        description="Return the persona YAML for a registered agent.",
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    # ... 6 more
```

#### API #3:`FastMCP(tools=[...])` 启动期注入(不推荐)

构造器接受 `tools: list[Tool]`,需要预先从函数构造 `Tool.from_function(fn, ...)`。**优点:** 注册集中一处易审计;**缺点:** 工具列表过长时 `create_mcp_server()` 难读,且现有 `mcp_serve.py` 风格是 decorator 内联,引入新风格不一致。

### 2.3 Tool 内可用的 Context API(2026 完整表面)

> 任何 tool 函数加一个 `ctx: Context` 参数,FastMCP 自动注入(类型注解驱动,参数名任意但 `ctx` 是约定)。

```python
from mcp.server.fastmcp import Context

@mcp.tool()
async def get_agent_opinion(
    agent_id: str,
    topic: str,
    context: str,
    prior_discussion: str | None = None,
    ctx: Context = None,                    # 自动注入
) -> str:
    await ctx.report_progress(0.0, total=3.0, message="Loading persona")
    persona = _read_agent_yaml(agent_id)
    await ctx.report_progress(1.0, total=3.0, message="Querying agent memory")
    memory = _query_mem0(agent_id, topic)
    await ctx.report_progress(2.0, total=3.0, message="Synthesizing opinion")
    opinion = await _llm_call(persona, topic, context, memory, prior_discussion)
    await ctx.report_progress(3.0, total=3.0, message="Done")
    ctx.info(f"agent={agent_id} opinion_len={len(opinion)}")  # 写到 CC stderr
    return opinion
```

**Context 完整方法表面(从 mcp==1.26.0 实测):**

| 方法 / 属性 | 用途 | v11.0 是否用 |
|-----------|------|------------|
| `ctx.report_progress(value, total=None, message=None)` | push 进度到 CC UI(progress bar 形式) | **用** —— long opinion 合成时报告进度 |
| `ctx.info / debug / warning / error(message, **extra)` | 写日志到 CC stderr,不污染 stdout(MCP 协议管道) | **用** —— 调试 + 审计 |
| `ctx.log(level, message, *, logger_name=None)` | 通用日志方法,等价上面 4 个 | 备用 |
| `ctx.read_resource(uri)` | 读 MCP resource(本 server 或远端) | **不用** —— 7 个新 tool 不需要 resource 抽象 |
| `ctx.session` | 当前 ServerSession 对象,可拿 client_id 等 | **不用** |
| `ctx.request_id` / `ctx.request_context` / `ctx.client_id` | 请求元数据 | **不用** |
| `ctx.elicit(message, schema)` | **2026 新**:向 CC 用户问表单(MCP 1.0 spec Elicitation) | **可能用** —— `run_python_phase` 在 ComfyUI 失败时向用户问 retry 策略 |
| `ctx.close_sse_stream()` / `close_standalone_sse_stream()` | SSE transport 专用 | **不用**(走 stdio) |

### 2.4 JSON Schema 自动派生(关键事实)

> **来源:** `inspect.getsource(Tool.from_function)` 显示 `parameters = func_arg_metadata.arg_model.model_json_schema(by_alias=True)` —— FastMCP 用 Pydantic V2 把 Python 类型 → JSON Schema,**零样板代码**。

| Python type hint | 生成的 JSON Schema |
|-----------------|-------------------|
| `agent_id: str` | `{"type": "string"}` |
| `limit: int = 50` | `{"type": "integer", "default": 50}` |
| `topic: str \| None = None` | `{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}` |
| `metadata: dict[str, str]` | `{"type": "object", "additionalProperties": {"type": "string"}}` |
| `tags: list[str]` | `{"type": "array", "items": {"type": "string"}}` |
| `union: Literal["screenplay", "cinematographer"]` | `{"enum": ["screenplay", "cinematographer"], "type": "string"}` |
| Pydantic Model 返回类型 + `structured_output=True` | `outputSchema` 自动填充(MCP 2025-06 spec 新字段) |

**v11.0 PoC 实施者提示:** 7 个新 tool 的 schema 不需要手写,但**强烈建议**每个 tool 用 Pydantic Model 做返回类型 + `@mcp.tool(structured_output=True)`,这样 CC 端能看到结构化 `outputSchema`(CC 2025-06 起支持结构化输出展示)。

### 2.5 ToolAnnotations(声明副作用给 CC 看)

> **来源:** `mcp.types.ToolAnnotations` 是 Pydantic model,字段实测为 `['title', 'readOnlyHint', 'destructiveHint', 'idempotentHint', 'openWorldHint']`。

```python
from mcp.types import ToolAnnotations

@mcp.tool(annotations=ToolAnnotations(
    readOnlyHint=True,         # 告诉 CC 此 tool 不改状态,可缓存
    openWorldHint=True,        # 告诉 CC 此 tool 与外部世界交互(LLM/mem0)
))
def get_agent_persona(agent_id: str) -> str: ...

@mcp.tool(annotations=ToolAnnotations(
    destructiveHint=False,     # 不删数据,但写 receipt(非纯读)
    idempotentHint=False,      # 重复提交会产生多个 receipt
))
def submit_artifact(file_path: str, status: str, metadata: dict) -> dict: ...
```

**v11.0 PoC 7 个 tool 的 annotations 推荐映射:** 见 §3 表格。

### 2.6 Transport 三选一(FastMCP.run 完整 signature)

```python
FastMCP.run(
    self,
    transport: Literal["stdio", "sse", "streamable-http"] = "stdio",
    mount_path: str | None = None,
)
```

三种 transport 都由 `anyio.run()` 包同步入口,均 stable。**但 v11.0 PoC 选 stdio**(详见 §4)。

---

## 3. 7 个新 MCP Tool — Schema 设计

> 这是 v10.0 设计产出,不是 v11.0 PoC 实施代码。所有 schema 用 Python type hint 表达,实际 JSON Schema 由 FastMCP 自动派生。

### 3.1 全局约定

- **agent_id 字段:** 字符串,匹配 `~/.hermes/agents/{agent_id}.agent.yaml` 文件名(不含 `.agent.yaml` 后缀)。**约束:** 仅 `[a-z0-9_-]+`(与 SKILL.md `name` 字段约定一致)。
- **receipt 模式:** 任何写入类 tool 返回 `{"receipt_id": str, "status": "ok|warn|error", "ts": iso8601}`,receipt_id 用于审计回溯。
- **错误返回:** 与现有 `mcp_serve.py` 风格一致 —— tool 不 raise,而是返回 `{"error": "..."}` JSON 字符串(CC 能正常解析,不会触发 transport-level error)。
- **structured_output:** v11.0 PoC 应**全部启用**,CC 端会展示更友好的 UI。

### 3.2 7 个 tool 完整 schema

#### Tool 1: `get_agent_persona`

```python
from pydantic import BaseModel, Field
from mcp.types import ToolAnnotations
from mcp.server.fastmcp import FastMCP

class AgentPersonaResult(BaseModel):
    """Structured output for get_agent_persona."""
    agent_id: str = Field(..., description="Agent identifier")
    persona_yaml: str = Field(..., description="Full persona YAML content (utf-8)")
    version: str = Field(..., description="Agent YAML version field")
    found: bool = Field(True, description="False if agent_id not registered")

@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        openWorldHint=False,        # 纯本地 YAML 读
    ),
    structured_output=True,
)
def get_agent_persona(agent_id: str) -> AgentPersonaResult:
    """Return the persona YAML for a registered Hermes agent.

    Reads from ~/.hermes/agents/{agent_id}.agent.yaml. Use this to load
    an agent's persona prompt, tools list, refs, and memory_scope before
    asking for its opinion in a round table.

    Args:
        agent_id: Agent identifier (e.g. "screenplay", "cinematographer",
            "hook_retention"). Must match a YAML file under
            ~/.hermes/agents/ without the .agent.yaml suffix.

    Returns:
        AgentPersonaResult with persona_yaml as the raw YAML string.
        If agent_id is not registered, returns found=False and empty
        persona_yaml.
    """
```

JSON Schema (auto-derived, given as reference):
```json
{
  "type": "object",
  "properties": {
    "agent_id": {"type": "string", "pattern": "^[a-z0-9_-]+$"}
  },
  "required": ["agent_id"],
  "additionalProperties": false
}
```

#### Tool 2: `get_agent_opinion`

```python
class AgentOpinionResult(BaseModel):
    agent_id: str
    topic: str                          # mirror back for audit
    opinion: str                        # free-form markdown opinion
    confidence: float = Field(..., ge=0.0, le=1.0, description="LLM self-reported confidence 0..1")
    cited_refs: list[str] = Field(default_factory=list, description="ref filenames cited")
    memory_hits: list[str] = Field(default_factory=list, description="memory IDs recalled")
    cost_usd: float | None = None       # optional cost tracking
    round_id: str | None = None         # set by orchestrator when called inside a round

@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=False,             # 内部会写 agent memory(opinion 被记住)
        openWorldHint=True,             # 调用 LLM + mem0
    ),
    structured_output=True,
)
async def get_agent_opinion(
    agent_id: str,
    topic: str,
    context: str,
    prior_discussion: str | None = None,
    round_id: str | None = None,
    ctx: Context = None,
) -> AgentOpinionResult:
    """Ask a registered agent for its opinion on a topic.

    Loads the agent persona, queries its scoped memory, then calls the
    configured LLM (Hermes credential pool) to synthesize an opinion.
    The opinion is automatically persisted to the agent's memory scope.

    Args:
        agent_id: Agent to consult (e.g. "screenplay").
        topic: One-sentence topic or question (e.g. "Is the opening
            hook strong enough to retain viewers past second 3?").
        context: Multi-paragraph context (script excerpt, prior
            decisions, asset list). Up to ~8KB.
        prior_discussion: Optional prior round-table transcript
            (so this agent can react to others). Up to ~16KB.
        round_id: Optional round-table identifier; if provided, the
            opinion is tagged with it for later reconciliation.

    Returns:
        AgentOpinionResult with opinion as markdown.
    """
```

**关键设计点:**
- `prior_discussion` 是**完整 round table 历史**(markdown blob,不是结构化 message list)—— 让 CC 在每次 call 之间负责 framing / 折叠(MCP tool 不持有 round 状态)。
- `confidence` 由 LLM 在 prompt 里被要求输出 JSON 末尾的 `"confidence": 0.X`( Hermes 端解析,失败 fallback 0.5)。
- `cited_refs` 是 agent persona 加载的 refs 列表里被 LLM 显式引用的子集 —— 用 prompt 指令要求 LLM 在 opinion 里用 `[ref:filename.md]` 标记。

#### Tool 3: `get_agent_memory`

```python
class MemoryHit(BaseModel):
    memory_id: str
    content: str
    score: float                        # similarity 0..1
    created_at: str                     # iso8601
    scope: str                          # agent_id or "global"

class AgentMemoryResult(BaseModel):
    agent_id: str
    query: str
    hits: list[MemoryHit]
    truncated: bool = False             # True if hits exceeded limit

@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        openWorldHint=True,             # mem0 backend
    ),
    structured_output=True,
)
def get_agent_memory(
    agent_id: str,
    scope: Literal["agent", "lineage", "global"] = "agent",
    query: str,
    limit: int = 10,
) -> AgentMemoryResult:
    """Query an agent's scoped memory.

    Agents in v10.0 have three memory scopes (per decision #6):
      - "agent": this agent's own accumulated experience
      - "lineage": memories inherited from parent agents (lineage field)
      - "global": cross-agent shared memories (platform guidelines, etc.)

    Args:
        agent_id: Agent whose memory to query.
        scope: Memory scope (default "agent").
        query: Natural-language query (e.g. "horizontal video failed on
            TikTok last week").
        limit: Max hits (default 10, max 50).

    Returns:
        AgentMemoryResult with ranked hits.
    """
```

#### Tool 4: `submit_round_table_result`

```python
class RoundTableReceipt(BaseModel):
    receipt_id: str                     # uuid4
    round_id: str
    status: Literal["ok", "warn", "error"]
    accepted_at: str                    # iso8601
    artifact_paths: list[str]           # paths where synthesis was written
    warnings: list[str] = Field(default_factory=list)

@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,           # 重复提交会创建多个 receipt
        openWorldHint=False,
    ),
    structured_output=True,
)
def submit_round_table_result(
    round_id: str,
    result_json: str,                   # 完整 round table 输出 JSON
    output_dir: str | None = None,      # 默认 ~/.hermes/round_tables/{round_id}/
) -> RoundTableReceipt:
    """Persist the final synthesis of a round table.

    CC calls this once at the end of every round table. Hermes writes
    the synthesis to disk, updates the round table audit log, and
    returns a receipt that CC can use for traceability.

    Args:
        round_id: Round-table identifier (set by orchestrator).
        result_json: Full JSON synthesis. Schema is defined in
            round-table-schema.yaml (v10.0 design artifact).
        output_dir: Optional override; defaults to
            ~/.hermes/round_tables/{round_id}/.

    Returns:
        RoundTableReceipt with receipt_id for audit chain.
    """
```

#### Tool 5: `submit_artifact`

```python
class ArtifactReceipt(BaseModel):
    receipt_id: str
    file_path: str
    status: Literal["ok", "warn", "error"]
    sha256: str
    size_bytes: int
    accepted_at: str
    metadata_echo: dict[str, str]

@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,            # 同 path + 同 sha256 二次提交 = no-op
        openWorldHint=False,
    ),
    structured_output=True,
)
def submit_artifact(
    file_path: str,
    status: Literal["draft", "final", "rejected", "needs_revision"],
    metadata: dict[str, str] | None = None,
) -> ArtifactReceipt:
    """Register an artifact (script, storyboard frame, audio stem) with Hermes.

    Used by CC at the end of each pipeline step to report what was
    produced. Hermes computes sha256, appends to the artifact ledger,
    and optionally triggers downstream listeners (e.g. ComfyUI queue).

    Args:
        file_path: Absolute path to the artifact file.
        status: Lifecycle status.
        metadata: Optional metadata (e.g. {"step": "5", "scene": "S3",
            "agent": "drawer"}).

    Returns:
        ArtifactReceipt with sha256 for FOUND-08-style byte-intact audits.
    """
```

#### Tool 6: `query_memory`(通用,非 agent-scoped)

```python
class GlobalMemoryResult(BaseModel):
    query: str
    hits: list[MemoryHit]               # 复用 Tool 3 的 MemoryHit
    truncated: bool

@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        openWorldHint=True,
    ),
    structured_output=True,
)
def query_memory(
    query: str,
    limit: int = 10,
    scope_filter: list[str] | None = None,
) -> GlobalMemoryResult:
    """Query Hermes global memory (cross-agent, cross-project).

    Unlike get_agent_memory, this searches across all agent scopes and
    the global pool. Useful for CC to find prior decisions, prior
    failures, or platform-specific learnings without knowing which
    agent owns them.

    Args:
        query: Natural-language query.
        limit: Max hits (default 10, max 50).
        scope_filter: Optional list of scopes to restrict (e.g.
            ["global", "platform_guidelines"]).

    Returns:
        GlobalMemoryResult with ranked hits across all matching scopes.
    """
```

#### Tool 7: `run_python_phase`(B3a 增量迁移的 boundary tool)

```python
class PythonPhaseResult(BaseModel):
    phase_id: str                       # e.g. "step_5_visual_generation"
    status: Literal["ok", "warn", "error", "skipped"]
    outputs: dict[str, str]             # artifact_path -> sha256
    logs_tail: str                      # last 100 lines, truncated
    duration_sec: float
    error: str | None = None

@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,          # 不删产物,但可能写新文件
        idempotentHint=False,           # 重复运行会产生不同 sha256
        openWorldHint=True,             # 调用 ComfyUI / dreamina CLI
    ),
    structured_output=True,
)
async def run_python_phase(
    phase_id: str,
    inputs: dict[str, str],
    output_path: str,
    timeout_sec: int = 600,
    ctx: Context = None,
) -> PythonPhaseResult:
    """Invoke a retained Python-runner phase (B3a decision).

    Per v10.0 design decision #2 (B3a), 4 ComfyUI-calling steps + Step
    0/6.5/15 stay on the Python runner. CC dispatches them via this
    tool. The tool blocks until completion (or timeout) and reports
    structured result.

    Long-running phases (>30s) should use ctx.report_progress via
    background polling of the Python phase's progress file.

    Args:
        phase_id: Phase identifier (must be in the retained-phases
            allowlist: see round-table-schema.yaml).
        inputs: Input artifact paths and parameters (e.g.
            {"storyboard_json": "/path/...", "style_genome": "..."}).
        output_path: Directory for outputs.
        timeout_sec: Max runtime (default 600 = 10 min, max 3600).

    Returns:
        PythonPhaseResult with outputs map and logs tail.
    """
```

### 3.3 Tool 注册顺序建议

按**依赖关系**注册(注册顺序不影响功能,影响 `tools/list` 输出顺序,CC UI 可能按此展示):

```python
# 1. 读类 (低风险)
@mcp.tool() def get_agent_persona(...)         # 必须最先,其它依赖它
@mcp.tool() def get_agent_memory(...)          # 读
@mcp.tool() def query_memory(...)              # 读

# 2. 调用类 (中风险,触发 LLM)
@mcp.tool() async def get_agent_opinion(...)   # 核心调用

# 3. 写类 (中风险,落盘)
@mcp.tool() def submit_artifact(...)
@mcp.tool() def submit_round_table_result(...)

# 4. 边界类 (高风险,触发 ComfyUI)
@mcp.tool() async def run_python_phase(...)
```

---

## 4. Transport 选型

### 4.1 三候选对比

| Criterion | **stdio**(推荐) | **Streamable HTTP** | **SSE**(legacy) |
|-----------|----------------|---------------------|-----------------|
| **MCP spec 状态** | stable(MCP 1.0 起) | **2025-06 spec 新**,1.20+ 默认 | **deprecated**(MCP 2025-06 标记 deprecated,1.26 仍可用但建议迁 Streamable HTTP) |
| **CC 支持** | ✓ 默认,`claude mcp add` 不传 `--transport` 即 stdio | ✓ `claude mcp add --transport http <name> <url>` | ✓ `claude mcp add --transport sse <name> <url>` |
| **现有 `mcp_serve.py` 状态** | ✓ 已用(`run_mcp_server()` 调 `run_stdio_async()`) | 未启用 | 未启用 |
| **进程模型** | CC 直接 fork Hermes 作为子进程 | Hermes 需独立 daemon(uvicorn 起 Starlette app) | 同 HTTP |
| **生命周期** | CC 启动则启,CC 退出则退 | 需要单独 systemd / supervisor / s6 服务 | 同 HTTP |
| **审计性** | 单进程,所有日志到 CC stderr(干净) | 多进程,需独立日志路径 | 同 HTTP |
| **Hermes gateway 协同** | 不需要 gateway;mcp_serve 独立读 SQLite/JSON | 需要协调端口、CORS、auth | 同 HTTP |
| **长跑 round table 支持** | ✓ 通过 `events_wait` long-poll + `ctx.report_progress` + tmux dispatch 实现 | ✓ 自然(每次 call 独立 HTTP 请求) | ⚠ SSE 连接容易被代理 / 防火墙断 |
| **Token 成本(每 round table)** | 21-42 MCP call,每个 ~2-5KB | 同 stdio | 同 stdio |
| **延迟(每 MCP call)** | <50ms(本地 IPC) | 50-200ms(loopback HTTP + JSON parse) | 100-500ms(SSE handshake + chunked) |
| **多 CC 客户端** | 1 CC = 1 Hermes subprocess(无法多客户端共享) | ✓ 多 CC 客户端共享一个 Hermes HTTP server | ✓ 同 HTTP |
| **PoC 复杂度** | **零**(已 wired) | 高(需新 daemon 配置 + 端口管理) | 中 |
| **v11.0 PoC 推荐** | **✓ 强推** | ✗ 不推荐(范围爆炸) | ✗ deprecated |

### 4.2 选型结论 + 推导

**v11.0 PoC 强推 stdio**,推导:

1. **现有零改动可复用** —— `~/.claude.json` 已配置 `{"type": "stdio", "command": ".../hermes", "args": ["mcp", "serve"]}` 且 ✓ Connected。任何新 tool 注册后只需重启 CC 一次(local scope 自动 reconnect)。
2. **MCP spec 2025-06 起 SSE deprecated** —— 走 SSE 是死路;Streamable HTTP 是替代但**需要 Hermes 跑独立 daemon**,与 v11.0 PoC「最小可行验证」目标冲突。
3. **进程模型简单 = 故障域小** —— stdio 模式下,CC fork Hermes,CC 退出 Hermes 也退,无 daemon 维护成本;日志全到 CC stderr,无端口冲突,无 CORS 配置。
4. **长跑 round table 不靠 transport 靠协议** —— 关键洞察:21-42 次 MCP call 之间 CC 是**主动 dispatch**的(每次 call 是一个 stdio request-response),不需要 transport 维持长连接。`events_wait` 已支持 30s+ long-poll(`timeout_ms`),足够覆盖 round table 内单次 opinion 合成的等待。
5. **多 CC 客户端需求暂未出现** —— Kai 当前是单 CC 实例(hermes-gateway via systemd)。若 v12+ 出现「多个 CC 实例共享一个 Hermes」,再迁 Streamable HTTP。
6. **失败回退路径清晰** —— 若 stdio 不够用,迁移到 Streamable HTTP 仅需:
   - 加 `run_streamable_http_async()` 入口
   - 配 systemd unit 跑 hermes-mcp-http.service
   - CC 端 `claude mcp add --transport http hermes http://localhost:8000/mcp`
   - 7 个 tool 函数体**完全不动**(transport-agnostic)

### 4.3 何时不选 stdio(给 v12+ 留的迁移条件)

迁移到 Streamable HTTP 的触发条件(任一满足):
- 多 CC 客户端并发(round table 多个 CC 实例同时跑)
- Hermes HTTP server 已是部署单元(eg dashboard 已在 8000 端口,mount `/mcp` 几乎零成本)
- 出现需要 Hermes 主进程长驻的 round table(eg Hermes 端有 background curator 在跑)

---

## 5. 现有 `mcp_serve.py` 扩展 patch 样例

> 这是 v10.0 设计产出 —— v11.0 PoC 实施时参考,**v10.0 milestone 本身不动任何代码**。

### 5.1 最小改动清单

| 改动点 | 文件 | 性质 | LOC |
|-------|------|------|-----|
| 加 7 个 `@mcp.tool()` 函数 | `mcp_serve.py` | additive(在 `create_mcp_server()` 内、`return mcp` 之前) | ~250 |
| 加 `_read_agent_yaml()` 等 helper | `mcp_serve.py` 顶部 helpers 区 | additive | ~80 |
| 加 `from mcp.types import ToolAnnotations` import | `mcp_serve.py` line ~50 | additive(1 行) | 1 |
| 加 `from mcp.server.fastmcp import Context` import | `mcp_serve.py` line ~50 | additive(1 行) | 1 |
| 扩展 `FastMCP("hermes", instructions=...)` 字符串 | `mcp_serve.py:460` | 文本改 | 0(纯字符串编辑) |
| 加 Pydantic 返回模型 7 个 | 新文件 `mcp_serve_schemas.py`(可选,或内联) | additive | ~120 |

**总改动:** ~450 LOC add, 0 LOC delete, 0 architecture change。

### 5.2 伪代码 patch(关键片段)

```python
# === mcp_serve.py 顶部 imports 区(在现有 from mcp.server.fastmcp import FastMCP 之后) ===
from mcp.server.fastmcp import Context       # 新加
from mcp.types import ToolAnnotations        # 新加
from typing import Literal                    # 已有 Optional,加 Literal

# === helpers 区(在 _load_channel_directory 之后) ===

_AGENT_REGISTRY_DIR = None  # lazy

def _get_agent_registry_dir() -> Path:
    """Return ~/.hermes/agents/, creating if missing."""
    global _AGENT_REGISTRY_DIR
    if _AGENT_REGISTRY_DIR is None:
        try:
            from hermes_constants import get_hermes_home
            _AGENT_REGISTRY_DIR = get_hermes_home() / "agents"
        except ImportError:
            _AGENT_REGISTRY_DIR = Path(
                os.environ.get("HERMES_HOME", Path.home() / ".hermes")
            ) / "agents"
    return _AGENT_REGISTRY_DIR


def _read_agent_yaml(agent_id: str) -> str | None:
    """Read agent persona YAML, return None if not registered."""
    # Input validation: only [a-z0-9_-]+ (path traversal guard)
    if not re.fullmatch(r"[a-z0-9_-]+", agent_id):
        return None
    yaml_path = _get_agent_registry_dir() / f"{agent_id}.agent.yaml"
    if not yaml_path.exists():
        return None
    with open(yaml_path, "r", encoding="utf-8") as f:
        return f.read()


# === create_mcp_server() 内,在 permissions_respond 之后、return mcp 之前 ===

# =============================================================================
# v10.0 Round-Table Protocol Tools (added P44)
# =============================================================================

@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    structured_output=True,
)
def get_agent_persona(agent_id: str) -> str:
    """Return the persona YAML for a registered Hermes agent.

    Reads from ~/.hermes/agents/{agent_id}.agent.yaml. Use this to load
    an agent's persona prompt, tools list, refs, and memory_scope before
    asking for its opinion in a round table.

    Args:
        agent_id: Agent identifier (e.g. "screenplay", "cinematographer").
    """
    persona = _read_agent_yaml(agent_id)
    if persona is None:
        return json.dumps({
            "agent_id": agent_id,
            "persona_yaml": "",
            "version": "",
            "found": False,
        })
    # Quick version extraction (ruamel.yaml lazy parse, no schema enforcement here)
    try:
        import yaml
        meta = yaml.safe_load(persona) or {}
        version = str(meta.get("version", ""))
    except Exception:
        version = ""
    return json.dumps({
        "agent_id": agent_id,
        "persona_yaml": persona,
        "version": version,
        "found": True,
    }, indent=2)


@mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=False, openWorldHint=True),
    structured_output=True,
)
async def get_agent_opinion(
    agent_id: str,
    topic: str,
    context: str,
    prior_discussion: str | None = None,
    round_id: str | None = None,
    ctx: Context = None,
) -> str:
    """Ask a registered agent for its opinion on a topic.

    Loads persona, queries scoped memory, calls LLM, returns structured opinion.

    Args:
        agent_id: Agent to consult.
        topic: One-sentence topic / question.
        context: Multi-paragraph context (up to ~8KB).
        prior_discussion: Optional prior round-table transcript.
        round_id: Optional round-table identifier.
    """
    # Phase 1: load persona
    if ctx:
        await ctx.report_progress(0.0, total=3.0, message="Loading persona")
    persona = _read_agent_yaml(agent_id)
    if persona is None:
        return json.dumps({"error": f"Agent not found: {agent_id}"})

    # Phase 2: query memory
    if ctx:
        await ctx.report_progress(1.0, total=3.0, message="Querying memory")
    memory_hits = _query_agent_memory_mem0(agent_id, topic)  # helper, lazy import mem0

    # Phase 3: call LLM via Hermes credential pool
    if ctx:
        await ctx.report_progress(2.0, total=3.0, message="Synthesizing")
    try:
        from agent.runtime_helpers import call_llm_with_failover  # existing util
        opinion, cost = await call_llm_with_failover(
            persona_prompt=persona,
            user_prompt=_build_opinion_prompt(topic, context, prior_discussion, memory_hits),
        )
    except Exception as e:
        return json.dumps({"error": f"LLM call failed: {e}"})

    # Persist opinion to agent memory (decision #6: per-agent scoped memory)
    _persist_opinion_to_memory(agent_id, topic, opinion, round_id)

    if ctx:
        await ctx.report_progress(3.0, total=3.0, message="Done")
        ctx.info(f"get_agent_opinion agent={agent_id} round={round_id} cost=${cost:.4f}")

    return json.dumps({
        "agent_id": agent_id,
        "topic": topic,
        "opinion": opinion,
        "confidence": 0.5,  # TODO: parse from opinion tail
        "cited_refs": [],   # TODO: extract [ref:xxx] markers
        "memory_hits": [h["id"] for h in memory_hits],
        "cost_usd": cost,
        "round_id": round_id,
    }, indent=2)


# ... 5 more tools following the same pattern ...

@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=False, destructiveHint=False,
        idempotentHint=False, openWorldHint=False,
    ),
    structured_output=True,
)
def submit_round_table_result(
    round_id: str,
    result_json: str,
    output_dir: str | None = None,
) -> str:
    """Persist the final synthesis of a round table."""
    import uuid
    receipt_id = str(uuid.uuid4())
    out = Path(output_dir) if output_dir else (
        _get_hermes_home() / "round_tables" / round_id
    )
    out.mkdir(parents=True, exist_ok=True)
    (out / "synthesis.json").write_text(result_json, encoding="utf-8")
    (out / "receipt.json").write_text(json.dumps({
        "receipt_id": receipt_id,
        "round_id": round_id,
        "accepted_at": _now_iso(),
        "artifact_paths": [str(out / "synthesis.json")],
    }, indent=2), encoding="utf-8")
    return json.dumps({
        "receipt_id": receipt_id,
        "round_id": round_id,
        "status": "ok",
        "accepted_at": _now_iso(),
        "artifact_paths": [str(out / "synthesis.json")],
        "warnings": [],
    }, indent=2)


# === return mcp 保持在文件末尾(不变) ===
return mcp
```

### 5.3 注册时机 / 错误处理约定

| 关注点 | 现有 `mcp_serve.py` 风格 | v11.0 PoC 沿用建议 |
|-------|-------------------------|------------------|
| **input 验证** | 用 `_coerce_int()` 在 tool 入口 clamp,不 raise | `agent_id` 加 `[a-z0-9_-]+` regex 检查,失败返回 `{"error": ...}` JSON,不 raise |
| **错误返回** | tool 函数体不 raise,捕获所有异常,返回 `{"error": str(e)}` JSON | 沿用 —— CC 端能解析 JSON,不会触发 transport-level error |
| **import 错误** | 现有 `_MCP_SERVER_AVAILABLE` flag 模式 | 沿用 —— mem0 / LLM 模块 lazy import 在 tool 函数体内 |
| **logging** | `logger.debug()` 详细、`logger.warning()` 重要、`logger.error()` 严重 | 沿用 —— 加上 `ctx.info()` 让 CC 端也能看到关键里程碑 |
| **background task** | EventBridge 是 daemon thread 在 `run_mcp_server()` 启动 | 7 个新 tool 不需要新 background task(LLM 调用是同步 await) |
| **重复注册 guard** | `warn_on_duplicate_tools=True`(FastMCP 默认) | 沿用 —— 重复注册会 warn 但不 crash |

### 5.4 单 server vs 双 server

| Criterion | 单 server(扩 `mcp_serve.py`) | 双 server(新 `mcp_serve_round_table.py`) |
|----------|------------------------------|---------------------------------------|
| **代码改动** | +450 LOC in `mcp_serve.py` | +450 LOC 新文件 + `hermes_cli/main.py` 加 subcommand |
| **CC 配置** | 1 个 stdio server(已 wired) | 2 个 stdio server,CC 要 `claude mcp add hermes-round-table ...` |
| **进程数** | 1 个 Hermes MCP subprocess per CC | 2 个 |
| **tool 命名空间** | 全局(`mcp.tools/list` 一起返回) | 分离 |
| **故障隔离** | messaging bug 影响 round table | 隔离 |
| **推荐** | **✓ 强推** | ✗ 过度工程化 |

**选单 server。** 理由:
1. messaging tool 与 round table tool 共享 EventBridge(虽然 v11.0 PoC 不一定用,但保留可能性)
2. 共享 SQLite / mem0 backend 实例(避免多进程 DB 锁竞争)
3. 减少进程数 = 减少故障面
4. CC 单 stdio 连接开销更低

---

## 6. CC 端 `claude mcp add` 配置

### 6.1 现有配置(实测)

`~/.claude.json` 项目段(`/data/workspace/hermes-agent` key 下)已含:

```json
{
  "mcpServers": {
    "hermes": {
      "type": "stdio",
      "command": "/data/workspace/hermes-agent/.venv/bin/hermes",
      "args": ["mcp", "serve"],
      "env": {}
    }
  }
}
```

**`claude mcp list` 实测输出:**
```
hermes: /data/workspace/hermes-agent/.venv/bin/hermes mcp serve - ✓ Connected
```

### 6.2 v11.0 PoC 配置改动

**零改动。** 因为 MCP `tools/list` 是动态发现协议 —— CC 启动 stdio MCP server 后会发 `tools/list` request,Hermes 返回所有已注册 tool(包括 7 个新的)。CC 拿到列表后即可调用。

**唯一需要做的事:** 注册 7 个新 tool 后**重启 CC 一次**(或新开一个 CC session)。CC 会在启动时重新发 `tools/list`,发现新增 tool。

### 6.3 三种 scope 的物理位置(参考)

`claude mcp add -s <scope>` 三种 scope 的配置落点:

| Scope | 物理位置 | 何时用 |
|-------|---------|-------|
| **`local`(默认)** | `~/.claude.json` 的 `projects.<cwd>.mcpServers` | 单项目单用户(当前 hermes 配置就在这里) |
| **`user`** | `~/.claude.json` 顶层 `mcpServers` 字段 | 跨所有项目可用 |
| **`project`** | `<repo>/.mcp.json`(checked into git) | 团队共享(repo 内所有人都能用) |

### 6.4 三种 transport 的 `claude mcp add` 命令样例

```bash
# stdio(推荐 / 现状)
claude mcp add -s local hermes -- /data/workspace/hermes-agent/.venv/bin/hermes mcp serve

# Streamable HTTP(v11.0 PoC 不推荐,v12+ 备选)
claude mcp add -s local --transport http hermes http://localhost:8000/mcp

# SSE(deprecated,不推荐)
claude mcp add -s local --transport sse hermes http://localhost:8000/sse

# stdio with env vars(若 v11.0 PoC 需要传特殊 env)
claude mcp add -s local -e HERMES_AGENT_MODE=round_table hermes -- /data/.../hermes mcp serve

# stdio with subprocess flags
claude mcp add -s local hermes -- /data/.../hermes mcp serve --verbose
```

### 6.5 `.mcp.json` 项目级共享配置(可选,v11.0 PoC 不需要)

若要让 hermes-agent repo 内**所有人**都能用 hermes MCP server,可在 repo 根加 `.mcp.json`:

```json
{
  "mcpServers": {
    "hermes": {
      "type": "stdio",
      "command": "${HERMES_BIN:-hermes}",
      "args": ["mcp", "serve"]
    }
  }
}
```

**注意:** `.mcp.json` 提交后,CC 会在新 clone 的 repo 第一次启动时弹「是否信任此项目的 MCP server」对话框。**v11.0 PoC 不建议加** —— Kai 当前是单人开发,local scope 已足够。

### 6.6 验证步骤(v11.0 PoC 实施者跑)

```bash
# 1. 注册 7 个新 tool 后(改完 mcp_serve.py),重启 CC
claude mcp list                          # 应显示 ✓ Connected

# 2. 单独跑 hermes mcp serve 验证 tool 注册
/data/workspace/hermes-agent/.venv/bin/hermes mcp serve --verbose 2>&1 | head -30
# 应看到 "Registered tool: get_agent_persona" 等 7 条 debug 日志

# 3. 在 CC 内调用新 tool(测试)
# 在 CC REPL 内: "Use the get_agent_persona tool with agent_id='screenplay'"
# CC 会自动调 MCP tool,看到 YAML 输出

# 4. 手动 JSON-RPC 验证(脱钩 CC)
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | /data/.../hermes mcp serve
# 应返回 server capabilities
```

---

## 7. Token 成本 / 延迟分析

### 7.1 单 round table 的 MCP call 数(估算)

> 基于 V8.6 13-step pipeline + 决策 #7(Hermes 控 turn_order)+ 假设每 step 触发 1 个 round table。

| 阶段 | round table 触发 | 平均 expert 数 | 平均 turns | MCP call / expert / turn | 小计 |
|------|-----------------|--------------|-----------|-------------------------|------|
| Step 1(creative_source)| 1 | 3 | 2 | 2(get_persona + get_opinion)| 12 |
| Step 3(screenplay)| 1 | 5 | 3 | 2 | 30 |
| Step 5(visual_executor)| 1 | 4 | 2 | 2 | 16 |
| ... 13 个 step 平均 ... | 13 | 4 | 2.5 | 2 | ~260 |
| **总计 / 13-step pipeline** | | | | | **~260 MCP call / pipeline run** |
| 加 submit_artifact / submit_round_table_result / query_memory 平均 | | | | | +~80 |
| **grand total** | | | | | **~340 MCP call / pipeline run** |

### 7.2 单 MCP call 的 token 成本

| Tool | input tokens(平均) | output tokens(平均) | 备注 |
|------|--------------------|---------------------|------|
| `get_agent_persona` | 50 | 2000 | persona YAML 全文返回 |
| `get_agent_opinion` | 5000(context + prior + persona)| 1500 | 主要 token 消耗 |
| `get_agent_memory` | 100 | 800 | 5-10 hits,每个 ~150 tokens |
| `query_memory` | 100 | 800 | 同上 |
| `submit_round_table_result` | 200 | 100 | receipt |
| `submit_artifact` | 100 | 100 | receipt |
| `run_python_phase` | 200 | 500 | logs tail |

### 7.3 单 pipeline run 总 token 估算

```
MCP-level(协议开销):
  ~340 MCP call × (50 + 50) tokens overhead = ~34K tokens

LLM-level(get_agent_opinion 内部):
  ~80 opinion call × (5000 + 1500) tokens = ~520K tokens

Total per pipeline run: ~550K tokens
```

**单 round table(13 个 step 中的一个)平均:**
```
MCP: 340/13 ≈ 26 call × 100 = 2.6K tokens
LLM: 520K/13 ≈ 40K tokens
```

### 7.4 延迟拆解(单 MCP call)

| 阶段 | stdio | Streamable HTTP | SSE |
|------|-------|----------------|-----|
| CC → MCP server round-trip | <5ms | 30-100ms | 50-200ms |
| MCP server 内部 dispatch(FastMCP)| <10ms | 同 | 同 |
| Tool 函数体(纯本地)| <50ms | 同 | 同 |
| Tool 函数体(LLM call)| 2-15s | 同 | 同 |
| Tool 函数体(ComfyUI)| 30s-10min | 同 | 同 |

**结论:** transport 选择对 LLM-bound tool 的延迟影响可忽略(<1%)。**stdio 的优势在运维简单,不在延迟。**

### 7.5 批量化建议

| Tool | 是否需要批量化 | 理由 |
|------|-------------|------|
| `get_agent_opinion` | **可选 v1.1** | 当前设计是 1 call = 1 opinion。可加 `get_agent_opinions(agent_ids: list[str], ...)` 批量版,FastMCP 顺序 await 7 个 LLM call。**但** 每个 opinion 需要 prior_discussion 反映前一个 opinion,无法真并行。建议 v11.0 PoC 不批量化,保留串行语义 |
| `get_agent_persona` | **可批量** | 1 个 round table 内 7 个 persona 是独立的,加 `get_agent_personas(agent_ids: list[str])` 一次拉完,省 6 个 MCP round-trip(~30ms) |
| `submit_artifact` | **可批量** | round table 末尾可能 submit 多个 artifact,加 `submit_artifacts(items: list[dict])` 批量版 |
| 其它 | 不需要 | 单 call 语义清晰 |

**v11.0 PoC 建议:** 7 个 tool 全部单 call 版,先跑通;v11.1+ 视实测延迟决定是否加批量化。

---

## 8. Installation(v11.0 PoC 实施时)

### 8.1 依赖

```bash
# 零新增依赖。mcp==1.26.0 已在 pyproject.toml [mcp] extra,已 lock 在 uv.lock
# 现有 hermes venv 已 install:
/data/workspace/hermes-agent/.venv/bin/python3 -c "import mcp; print(mcp.__version__ if hasattr(mcp, '__version__') else 'no version attr')"
# 实测可导入
```

### 8.2 实施步骤(v11.0 PoC,不是 v10.0)

1. 写 `mcp_serve.py` patch(参考 §5.2 伪代码)
2. 在 `~/.hermes/agents/` 下创建 1-2 个测试 agent YAML(eg `test-screenplay.agent.yaml`)
3. 重启 hermes-gateway systemd unit(让 `mcp_serve` 模块重新加载)
4. 在 CC 内 `claude mcp list` 确认 ✓ Connected
5. 在 CC REPL 测试:`Use get_agent_persona with agent_id="test-screenplay"`
6. 跑 1 个最小 round table(3 expert × 1 turn)验证 E2E

### 8.3 v10.0 设计 milestone 本身不动任何代码

v10.0 产出**仅设计文档**(7 个 .md),`mcp_serve.py` 实际 patch 在 v11.0 PoC 实施。

---

## 9. Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| MCP server API | **FastMCP `@mcp.tool()`** | Low-level `mcp.server.Server` + `@server.call_tool()` + `@server.list_tools()` | Low-level 是 0.x 时代 API,样板代码量大(register_handler pattern),FastMCP 是 1.x stable 路径且向后兼容 |
| MCP server API | **FastMCP `@mcp.tool()`** | `FastMCP(tools=[Tool.from_function(fn), ...])` 启动期注入 | 与现有 `mcp_serve.py` 风格不一致(decorator 内联);注册集中难读 |
| Transport | **stdio** | Streamable HTTP | 需要独立 daemon + systemd unit,与 v11.0 PoC 最小可行目标冲突;现有 stdio 已 wired 且 ✓ Connected |
| Transport | **stdio** | SSE | MCP 2025-06 spec 标记 deprecated,走死路 |
| Server 数 | **单 server**(`mcp_serve.py` 扩) | 双 server(messaging + round_table) | 过度工程化,增加进程数 + DB 锁竞争 + CC 配置复杂度 |
| Schema 来源 | **Pydantic Model + auto-derived** | 手写 JSON Schema dict | 手写易错,Pydantic 提供类型安全 + V2 `model_json_schema()` 是 stable API |
| Tool 注册时机 | **import-time decorator** | runtime conditional add_tool | 现有 `mcp_serve.py` 风格是 import-time;若需要 conditional(如某些 tool 仅在 plugin 加载后),用 `_maybe_register_*()` helper |
| CC scope | **local**(当前) | user(全局) | round-table tool 仅在 hermes-agent repo 上下文有意义,user scope 会让所有 repo 的 CC 都看到这 7 个 tool,造成噪音 |
| Agent persona 存储 | **`~/.hermes/agents/*.agent.yaml`**(决策 #5) | SKILL.md 内嵌 | 决策 #5 已锁 agent YAML 是独立实体形态,SKILL 是 fallback 形态 |

---

## 10. Pitfalls(详见 v10.0 PITFALLS.md,此处仅 STACK 相关)

| Pitfall | 风险 | 缓解 |
|---------|-----|------|
| `@mcp.tool` 裸用(不加 `()`) | `TypeError` | FastMCP 源码已 guard,会报清晰错误;CI lint 加 `grep -n "@mcp.tool$" mcp_serve.py` 应返回空 |
| `agent_id` 路径遍历(eg `../etc/passwd`)| 安全 | 入口 regex `^[a-z0-9_-]+$` 校验 |
| `prior_discussion` 超 16KB | MCP message size 限制 / CC context 爆 | tool 入口 clamp 到 16KB + 提示 CC 折叠 |
| LLM call 内 raise 导致 tool crash | transport-level error | tool 函数体全部 try/except,返回 `{"error": str(e)}` JSON |
| mem0 lazy import 失败 | tool 报错 | 与现有 `send_message_tool` import 模式一致,`{"error": "mem0 plugin not available"}` JSON |
| stdio server 被 CC 多次 fork | 多进程同时写 mem0 / SQLite | mem0 backend 内部应有锁;SQLite WAL 模式天然支持并发读;若出现竞争,加 file lock |
| 重启 CC 后 tool 列表不更新 | CC 缓存旧 `tools/list` 结果 | 重启 hermes-gateway systemd 后,**新开 CC session**(不要 resume 旧 session) |
| Streamable HTTP 误用 | 范围爆炸 | v11.0 PoC 严格 stdio,在 02-ROUND-TABLE-PROTOCOL.md 显式记录"transport = stdio only" |

---

## 11. Open Questions(留给 v10.0 其它设计文档 / v11.0 PoC)

1. **agent persona YAML 的 lineage 字段如何注入到 prompt?** —— 是 `get_agent_persona` 透传 lineage 元数据,还是 `get_agent_opinion` 内部展开?→ 02-ROUND-TABLE-PROTOCOL.md 决定。
2. **`run_python_phase` 的 retained-phases allowlist 在哪定义?** —— `round-table-schema.yaml` 还是单独 `python_phases.yaml`?→ 04-MIGRATION-PATH.md 决定。
3. **CC 端如何拿到 round_id?** —— 是 Hermes 通过 prompt 注入,还是 CC 自己生成 uuid?→ 02-ROUND-TABLE-PROTOCOL.md 决定。
4. **mem0 backend 是否需要 per-agent collection 隔离?** —— mem0 现有 API 是否支持 namespace?→ 03-COMPARISON-VS-KIMI-MCP-SHIM.md 调研。
5. **agent persona YAML schema 是否需要 `tools` 字段枚举?** —— 限制每个 agent 只能调特定 MCP tool?→ 01-AGENT-REGISTRY-SCHEMA.md 决定。

---

## 12. Sources

| Source | URL / Path | Confidence | 用途 |
|--------|-----------|-----------|------|
| **mcp==1.26.0 installed package** | `/home/kai/.local/lib/python3.12/site-packages/mcp/` | HIGH | API 表面、decorator signature、Context 方法、transport 选项 |
| **`uv.lock` mcp 段** | `/data/workspace/hermes-agent/uv.lock` (line "name = mcp" / "version = 1.26.0") | HIGH | 版本验证 |
| **`pyproject.toml` mcp 依赖** | `/data/workspace/hermes-agent/pyproject.toml:197, 206` | HIGH | 版本锁定 + extra 配置 |
| **现有 `mcp_serve.py`** | `/data/workspace/hermes-agent/mcp_serve.py` (907 lines, 全文实读) | HIGH | tool 注册模式、EventBridge、helper 风格 |
| **CC CLI 2.1.143** | `claude mcp --help`, `claude mcp add --help`, `claude mcp list`(实测) | HIGH | 配置 scope、transport 选项、现状 |
| **`~/.claude.json`** | `/home/kai/.claude.json` projects 段(实测 dump) | HIGH | 现有 hermes MCP 配置格式 |
| **`coding-agent` SKILL.md** | `/data/workspace/hermes-agent/skills/autonomous-ai-agents/coding-agent/SKILL.md` | HIGH | tmux dispatch 模式(v7.0 ship) |
| **`claude-code` SKILL.md** | `/data/workspace/hermes-agent/skills/autonomous-ai-agents/claude-code/SKILL.md:131-137` | HIGH | `claude mcp` subcommand 参考 |
| **Python introspection** | `inspect.signature()` + `inspect.getsource()` on FastMCP / Context / Tool | HIGH | API 表面第一手证据 |
| **`.planning/PROJECT.md`** | `/data/workspace/hermes-agent/.planning/PROJECT.md` v10.0 段 | HIGH | 7 决策锁定 + milestone scope |

**Confidence assessment:**
- **API 表面:** HIGH(installed mcp==1.26.0 实测)
- **现有 `mcp_serve.py` 模式:** HIGH(全文实读)
- **CC 配置格式:** HIGH(CLI 实测 + `~/.claude.json` 实测)
- **transport 选型推导:** HIGH(基于 1-3 的第一手证据)
- **token 成本估算:** MEDIUM(基于 V8.6 pipeline 假设,未实测 round table)
- **schema 设计:** MEDIUM(v10.0 设计产出,v11.0 PoC 实施时可能调整)
