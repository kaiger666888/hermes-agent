<!-- refreshed: 2026-06-14 -->
# Architecture

**Analysis Date:** 2026-06-14

## System Overview

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                         ENTRY POINTS / SURFACES                              │
├─────────────────┬─────────────────┬─────────────────┬────────────────────────┤
│  CLI / REPL     │  TUI (Rust +    │  Gateway        │  Programmatic / MCP    │
│  `cli.py`       │  TS)            │  `gateway/run.py`│  `mcp_serve.py`        │
│  `hermes_cli/   │  `tui_gateway/` │  (long-running   │  (stdio MCP server)    │
│   main.py`      │  `ui-tui/`      │   daemon)        │                        │
│  `run_agent.py  │  `apps/desktop/`│                  │  `apps/desktop/`       │
│   __main__`     │                 │                  │  (Electron + Tauri)    │
└────────┬────────┴────────┬────────┴────────┬─────────┴──────────┬─────────────┘
         │                 │                  │                    │
         ▼                 ▼                  ▼                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          AGENT RUNTIME LAYER                                  │
│   `run_agent.AIAgent` (orchestrator)  ·  `agent/agent_init.init_agent`         │
│   `agent/conversation_loop.run_conversation` (model call + tool dispatch loop) │
│   `agent/prompt_builder.build_*`  ·  `agent/system_prompt.build_system_prompt` │
│   `agent/context_compressor.ContextCompressor`  ·  `agent/curator.run_curator` │
└────────┬─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│              PROVIDER + TRANSPORT LAYER (multi-provider)                      │
│   `providers/` (ProviderProfile registry)  ·  `plugins/model-providers/*`     │
│   `agent/transports/` (ProviderTransport: anthropic, bedrock, codex,          │
│                        chat_completions)                                      │
│   `agent/anthropic_adapter.py` · `agent/bedrock_adapter.py`                   │
│   `agent/gemini_*_adapter.py` · `agent/codex_runtime.py`                      │
└────────┬─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│              TOOL / SKILL / PLUGIN LAYER                                      │
│   `tools/registry.py` (self-registering tools)  ·  `tools/*_tool.py`          │
│   `toolsets.py` (toolset aliases)  ·  `model_tools.py` (dispatch entry)        │
│   `agent/tool_executor.py` (concurrent/sequential)                            │
│   `skills/<category>/<skill>/SKILL.md` (markdown skills, agentskills.io)      │
│   `plugins/<name>/plugin.yaml + __init__.py` (PluginManager, PluginContext)    │
└────────┬─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│              STATE & EXTERNAL STORAGE                                         │
│   `hermes_state.SessionDB` (SQLite, sessions/conversations)                   │
│   `~/.hermes/` (HERMES_HOME: config.yaml, sessions.db, logs, plugins, plans)  │
│   `gateway/session.SessionStore` (per-platform session routing)               │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `AIAgent` | Orchestrator class — owns client construction, conversation state, provider switching, calls `agent_init.init_agent` to wire dependencies, forwards `run_conversation` to extracted module | `run_agent.py:294` |
| Conversation loop | Single user turn through model call + tool dispatch + retries + fallbacks + compression + post-turn hooks | `agent/conversation_loop.py:351` |
| System prompt assembly | Three-tier prompt (stable/context/volatile); cached for prefix-cache warmth | `agent/system_prompt.py:61`, `agent/prompt_builder.py:1039` |
| Context compression | Sliding-window summarization of tool results when context nears limit; strips media, summarizes, preserves recent | `agent/context_compressor.py:522` (`ContextCompressor`) |
| Trajectory compression | Aggressive compression of historical tool results into trajectory format | `trajectory_compressor.py` |
| Curator | Background review of session history, absorbs/removes/renames skills based on usage | `agent/curator.py:1388` (`run_curator_review`) |
| Prompt builder | Builds skills system prompt, environment hints, context file (AGENTS.md, SOUL.md, .cursorrules) loader | `agent/prompt_builder.py` |
| Tool executor | Concurrent and sequential tool-call execution against `tools.registry` | `agent/tool_executor.py:110` (`execute_tool_calls_concurrent`), `:542` (`_sequential`) |
| Tool registry | Self-registering tool modules; AST-scanned for `registry.register(...)` calls | `tools/registry.py` |
| Toolset definitions | Named aliases mapping to tool groups (research, full_stack, etc.) | `toolsets.py:88` (`TOOLSETS`) |
| Provider profile registry | Lazy plugin discovery for `ProviderProfile` instances (auth, endpoints, quirks) | `providers/__init__.py:140` (`_discover_providers`) |
| Provider transports | Per-api_mode conversion: messages → provider-native, response → `NormalizedResponse` | `agent/transports/base.py:16` (`ProviderTransport` ABC) |
| Gateway daemon | Long-running multi-platform message router; session store, stream consumer, run loop | `gateway/run.py`, `gateway/session.py:668` (`SessionStore`), `gateway/stream_consumer.py:79` (`GatewayStreamConsumer`) |
| Platform adapters | Per-platform connection, send/receive, typing indicators, media handling | `gateway/platforms/base.py`, `gateway/platforms/{telegram,slack,discord,...}.py` |
| Platform plugin system | Zero-core-edit adapter registration via `plugin.yaml + register(ctx)` | `gateway/platform_registry.py:162` (`PlatformRegistry`), `plugins/platforms/` |
| Skills loader | Walks `skills/<category>/<name>/SKILL.md`, parses frontmatter, surfaces to LLM | `tools/skills_tool.py`, `agent/skill_utils.py`, `agent/skill_commands.py`, `agent/skill_bundles.py` |
| Plugin manager | Discovers bundled/user/project/pip plugins; invokes lifecycle hooks | `hermes_cli/plugins.py:1004` (`PluginManager`), `hermes_cli/plugins.py:286` (`PluginContext`) |
| MCP serve | Exposes messaging sessions + send/receive as MCP tools for Claude Code/Cursor/Codex | `mcp_serve.py` |
| TUI gateway | JSON-RPC bridge between TypeScript/Rust TUI frontend and Python backend | `tui_gateway/server.py`, `tui_gateway/transport.py:67` (`Transport` protocol) |

## Pattern Overview

**Overall:** Modular monolith with plugin/skill extension points. Single-process Python (async where needed) with multiple entry points sharing the same `AIAgent` core. Strong convention of "extracted internals": large functions originally in `run_agent.py` were pulled into `agent/*.py` modules while preserving test-patch contracts via `_ra()` lazy indirection (`agent/conversation_loop.py:111`, `agent/agent_init.py:62`, `agent/agent_runtime_helpers.py:44`).

**Key Characteristics:**
- **Self-registration over central registries**: Tools call `registry.register(...)` at module import; providers call `register_provider(profile)`; platforms call `ctx.register_platform(...)`. Discovery is AST-scanning + import-side-effect.
- **Lazy plugin discovery**: First call triggers scan of `plugins/`, `~/.hermes/plugins/`, `.hermes/plugins/`, and `pip` entry points (`hermes_cli/plugins.py`).
- **Three-tier system prompt caching**: Stable / context / volatile to keep upstream provider prefix caches warm (`agent/system_prompt.py:61`).
- **Forwarder shim pattern**: `AIAgent.run_conversation` is a 3-line forwarder to `agent/conversation_loop.run_conversation`; this preserves the public API while letting the implementation live in a 4,000-line extracted module.
- **Patch contract preservation**: `_ra()` returns the `run_agent` module lazily so `mock.patch("run_agent.X")` keeps working in tests after extraction (`agent/conversation_loop.py:111`).

## Layers

**Entry-point layer:**
- Purpose: Multiple user-facing surfaces share one runtime.
- Location: `cli.py`, `hermes_cli/main.py`, `gateway/run.py`, `tui_gateway/server.py`, `mcp_serve.py`, `apps/desktop/electron/`
- Contains: argparse/CLI dispatch, REPL loop, daemon main, MCP server, JSON-RPC handlers
- Depends on: `run_agent.AIAgent`, `agent.*`, `gateway/session.SessionStore`
- Used by: End users, MCP clients (Claude Code, Cursor), TUI frontend, desktop app

**Agent runtime layer:**
- Purpose: One user turn = build prompt → call model → dispatch tools → loop until done → compress if needed → persist.
- Location: `run_agent.py`, `agent/conversation_loop.py`, `agent/prompt_builder.py`, `agent/system_prompt.py`, `agent/agent_init.py`, `agent/agent_runtime_helpers.py`, `agent/tool_executor.py`, `agent/context_compressor.py`, `agent/curator.py`
- Contains: Orchestration, retry/failover logic, prompt assembly, context management
- Depends on: `providers/`, `agent/transports/`, `tools/`, `toolsets.py`, `hermes_state.SessionDB`
- Used by: All entry points

**Provider + transport layer:**
- Purpose: Decouple "what the model expects" (OpenAI chat-completions format internally) from "what the provider speaks" (Anthropic messages, Bedrock, Codex responses, Gemini, etc.).
- Location: `providers/__init__.py`, `providers/base.py`, `plugins/model-providers/*/`, `agent/transports/{anthropic,bedrock,codex,chat_completions}.py`
- Contains: `ProviderProfile` dataclass (auth/endpoints/quirks), `ProviderTransport` ABC (convert_messages / convert_tools / build_kwargs / normalize_response)
- Depends on: Provider SDKs (`anthropic`, `openai`, `boto3`, `google-genai`), `agent/transports/types.NormalizedResponse`
- Used by: `run_agent.AIAgent`, `agent/agent_runtime_helpers.create_openai_client`

**Tool / skill / plugin layer:**
- Purpose: Extend agent capabilities with file/web/browser/code tools, markdown skills, and plugin-defined commands.
- Location: `tools/` (Python tools), `skills/` (markdown skills), `plugins/` (Python plugins)
- Contains: Tool handlers + schemas, skill markdown with YAML frontmatter, plugin `register(ctx)` entrypoints
- Depends on: `tools/registry.py`, `agent/skill_utils.py`, `hermes_cli/plugins.PluginContext`
- Used by: `model_tools.handle_function_call`, `agent/tool_executor.execute_tool_calls_concurrent`

**State / persistence layer:**
- Purpose: Sessions, conversations, credentials, profiles, plans persist across runs.
- Location: `hermes_state.py:364` (`SessionDB`), `gateway/session.py:668` (`SessionStore`), `~/.hermes/` (HERMES_HOME)
- Contains: SQLite schema, session routing, transcript storage, profile/config YAML
- Depends on: `sqlite3` stdlib, `hermes_constants.get_hermes_home`
- Used by: All entry points and runtime layer

## Data Flow

### Primary Request Path (CLI REPL)

1. **Entry**: `python cli.py` or `hermes` invokes `hermes_cli/main.py:11738` (`main()`), parses subcommand, dispatches to `cmd_chat(args)` (`hermes_cli/main.py:1733`).
2. **Agent construction**: `cmd_chat` calls `run_agent.AIAgent(...)` (`run_agent.py:294`) which calls `agent.agent_init.init_agent` (`agent/agent_init.py:136`) to load config, model metadata, providers, toolsets.
3. **Prompt assembly**: `agent.system_prompt.build_system_prompt` (`agent/system_prompt.py:348`) joins three tiers — stable (SOUL.md, tool guidance, skills manifest, environment hints), context (AGENTS.md, .cursorrules, caller's system_message), volatile (memory snapshot, USER.md, timestamp). Cached on `agent._cached_system_prompt`.
4. **Conversation loop**: `agent.conversation_loop.run_conversation` (`agent/conversation_loop.py:351`) — sends messages to provider via `agent.agent_runtime_helpers` (which constructs an OpenAI-compatible client and applies transport conversions from `agent/transports/`).
5. **Streaming + tool dispatch**: When model returns tool calls, `agent.tool_executor.execute_tool_calls_concurrent` (`agent/tool_executor.py:110`) dispatches each to `model_tools.handle_function_call` (`model_tools.py:802`), which looks up the handler in `tools/registry.py`. Tool results are appended to messages and the model is called again.
6. **Context compression**: If estimated request tokens approach the model's context window, `agent.context_compressor.ContextCompressor` (`agent/context_compressor.py:522`) summarizes older tool results, strips media, preserves recent N turns.
7. **Persistence**: Each turn is written to `hermes_state.SessionDB` (`hermes_state.py:364`) under the current session ID.
8. **Background curator**: `agent.curator.maybe_run_curator` (`agent/curator.py:1782`) periodically forks a review pass that absorbs/removes/renames skills based on usage patterns.

### Gateway Flow (Multi-Platform Daemon)

1. **Start**: `hermes gateway` (`hermes_cli/main.py:1918` → `cmd_gateway`) launches `gateway/run.py` as a foreground process or service.
2. **Adapter construction**: `gateway/platform_registry.PlatformRegistry` (`gateway/platform_registry.py:162`) instantiates adapters for each enabled platform from `gateway/platforms/<name>.py` (built-in) or `plugins/platforms/<name>/` (plugin).
3. **Inbound message**: Platform adapter calls `self.handle_message(event)` which routes to the gateway run loop in `gateway/run.py`.
4. **Session routing**: `gateway/session.SessionStore` (`gateway/session.py:668`) resolves the inbound event to a `SessionEntry` (`gateway/session.py:425`) keyed by platform + chat ID. Session history is replayed into `messages`.
5. **Agent invocation**: The gateway constructs an `AIAgent` (or reuses one pooled per session), calls `run_conversation`, streams output via `gateway/stream_consumer.GatewayStreamConsumer` (`gateway/stream_consumer.py:79`).
6. **Reply delivery**: The final response text + any media are sent back through the originating adapter's `send/send_image/send_voice` methods. `gateway/delivery.py` handles chunking and rate limits.

### TUI Flow

1. `hermes` (no subcommand) launches the TypeScript TUI at `ui-tui/src/` which spawns `tui_gateway/server.py` as a subprocess.
2. Communication is JSON-RPC over stdio (`tui_gateway/transport.py:100` `StdioTransport`).
3. The TUI sends requests like `session.create`, `chat.send`, `interrupt`; `tui_gateway/server.py:466` `handle_request` dispatches them to `run_agent.AIAgent` or `hermes_state.SessionDB`.
4. Streaming responses emit `chat.delta`, `chat.message`, `tool.start`, `tool.end`, `status.update` events.

### Skill Invocation Flow (Slashes)

1. User types `/<skill>` in any surface. Gateway/cli resolves it via `agent/skill_commands.resolve_skill_command_key` (`agent/skill_commands.py:409`) or `agent/skill_bundles.resolve_bundle_command_key` (`agent/skill_bundles.py:208`).
2. `agent/skill_commands._load_skill_payload` (`agent/skill_commands.py:53`) reads `skills/<category>/<name>/SKILL.md`, parses YAML frontmatter via `agent/skill_utils.parse_frontmatter` (`agent/skill_utils.py:88`).
3. The skill body is injected as a user message; the conversation loop runs as normal with the skill content shaping the model's behavior.

**State Management:**
- **Session state**: SQLite (`~/.hermes/sessions.db`) via `hermes_state.SessionDB`. One row per turn.
- **In-memory state**: `AIAgent.messages` list, `AIAgent._cached_system_prompt`, `IterationBudget` (`agent/iteration_budget.py`).
- **Process state**: Gateway is a long-running asyncio loop; CLI is a per-invocation process; TUI is parent (TS) + child (Python via JSON-RPC).
- **Thread state**: Tool execution uses `concurrent.futures.ThreadPoolExecutor`; plugin tool whitelists use `contextvars` (`hermes_cli/plugins.py:1654`).

## Key Abstractions

**ProviderProfile** (`providers/base.py:39`):
- Purpose: Declarative description of an inference provider (auth, endpoints, model catalog, quirks).
- Examples: `plugins/model-providers/alibaba/__init__.py`, `plugins/model-providers/anthropic/__init__.py`, `plugins/model-providers/openrouter/__init__.py`
- Pattern: Dataclass registered at import time via `register_provider(profile)`. Lazy discovery on first `get_provider_profile()` call.

**ProviderTransport** (`agent/transports/base.py:16`):
- Purpose: Owns data conversion for one `api_mode` (chat_completions, anthropic_messages, bedrock, codex_responses).
- Examples: `agent/transports/anthropic.py`, `agent/transports/bedrock.py`, `agent/transports/codex.py`, `agent/transports/chat_completions.py`
- Pattern: ABC with `convert_messages`, `convert_tools`, `build_kwargs`, `normalize_response` → `NormalizedResponse`.

**NormalizedResponse** (`agent/transports/types.py`):
- Purpose: Single internal type for parsed provider responses (text, tool calls, usage, finish reason).

**ToolRegistry** (`tools/registry.py`):
- Purpose: Tools self-register at import; `model_tools.get_tool_definitions` queries the registry.
- Examples: Every `tools/<name>_tool.py` (e.g. `tools/file_tools.py`, `tools/web_tools.py`, `tools/browser_tool.py`, `tools/terminal_tool.py`).
- Pattern: Module-level `registry.register(name=..., handler=..., schema=..., toolset=..., check_fn=...)`.

**Skill** (`skills/<category>/<name>/SKILL.md`):
- Purpose: Markdown document with YAML frontmatter that shapes the model's behavior when invoked.
- Examples: `skills/movie-experts/screenplay/SKILL.md`, `skills/software-development/plan/SKILL.md`, `skills/creative/comfyui/SKILL.md`.
- Pattern: Frontmatter declares `name`, `description`, `prerequisites`, `metadata.hermes.{tags, related_skills, expert_id, metrics}`. Loader is `tools/skills_tool.py` + `agent/skill_utils.py`. Skill body is injected as a user message.

**PluginManifest** (`hermes_cli/plugins.py:233`):
- Purpose: Declarative plugin descriptor (`plugin.yaml`) plus runtime `register(ctx)` function.
- Examples: `plugins/model-providers/alibaba/plugin.yaml`, `plugins/memory/mem0/`, `plugins/platforms/discord/`.
- Pattern: `PluginContext` (`hermes_cli/plugins.py:286`) exposes `register_tool`, `register_platform`, `register_command`, `register_hook`, `register_memory_provider`, etc. Discovery scans bundled + user + project + pip-entrypoint sources.

**PlatformAdapter** (`gateway/platforms/base.py` — `BasePlatformAdapter`):
- Purpose: One class per messaging platform (Telegram, Slack, Discord, WhatsApp, Matrix, Signal, etc.).
- Examples: `gateway/platforms/telegram.py`, `gateway/platforms/slack.py`, `gateway/platforms/api_server.py:680` (`APIServerAdapter`).
- Pattern: ABC requiring `connect`, `disconnect`, `send`, `send_typing`, `send_image`, `get_chat_info`. Built-ins live in `gateway/platforms/`; community plugins in `plugins/platforms/<name>/adapter.py` register via `ctx.register_platform(...)`.

**SessionStore / SessionEntry** (`gateway/session.py:668`, `:425`):
- Purpose: Routes inbound events to per-chat conversation state. One `SessionEntry` per (platform, chat_id).

## Entry Points

**CLI / REPL:**
- Location: `cli.py` (standalone REPL), `hermes_cli/main.py:11738` (full CLI dispatcher with subcommands)
- Triggers: `hermes`, `hermes chat`, `python cli.py`
- Responsibilities: Arg parsing, REPL prompt loop, model setup wizard, status display, TUI launcher

**run_agent.py main:**
- Location: `run_agent.py:4600` (`main()`)
- Triggers: `python run_agent.py "query"` — direct script invocation
- Responsibilities: Minimal CLI wrapper using `fire` library; instantiates `AIAgent`, runs one conversation, prints result.

**Gateway daemon:**
- Location: `gateway/run.py`, launched by `hermes_cli/main.py:1918` `cmd_gateway`
- Triggers: `hermes gateway`, `hermes gateway start` (service)
- Responsibilities: Long-running async loop; instantiates platform adapters, routes inbound, runs agent per session, delivers replies.

**MCP server:**
- Location: `mcp_serve.py`
- Triggers: `hermes mcp serve`
- Responsibilities: stdio FastMCP server exposing 9+ tools (`conversations_list`, `messages_read`, `messages_send`, `events_poll`, `permissions_respond`, `channels_list`, etc.) for MCP-aware clients.

**TUI gateway:**
- Location: `tui_gateway/server.py:466` (`handle_request`), `tui_gateway/entry.py`
- Triggers: Spawned as subprocess by `ui-tui/` TUI frontend (TypeScript)
- Responsibilities: JSON-RPC over stdio; methods include `session.create`, `chat.send`, `interrupt`, `tool.call`.

**Bootstrap installer / desktop:**
- Location: `apps/bootstrap-installer/` (Tauri installer), `apps/desktop/` (Electron desktop app)
- Triggers: Native desktop launches
- Responsibilities: Installer wraps `setup-hermes.sh`; desktop wraps the TUI + gateway.

## Architectural Constraints

- **Threading**: CLI runs the agent in the main thread; tools execute in `ThreadPoolExecutor` via `agent/tool_executor.py:110`. Gateway runs an asyncio event loop in one thread with platform adapters dispatching sync work to executors. The TUI gateway uses a JSON-RPC pump thread.
- **Global state**: Module-level registries are intentionally global — `_REGISTRY` in `providers/__init__.py:43`, `_REGISTRY` in `agent/transports/__init__.py:17`, `platform_registry` singleton in `gateway/platform_registry.py:260`, the `ToolRegistry` instance in `tools/registry.py`. These are write-once at import time.
- **HERMES_HOME**: `~/.hermes/` is the canonical state root — resolved by `hermes_constants.get_hermes_home()`. Holds `config.yaml`, `sessions.db`, `logs/`, `plugins/`, `plans/`, `SOUL.md`, `USER.md`. Override via `HERMES_HOME` env var.
- **Circular imports**: Heavily mitigated via `_ra()` lazy indirection. `agent/*` modules that need symbols from `run_agent` resolve them lazily through `_ra()` (`agent/conversation_loop.py:111`, `agent/system_prompt.py:46`, `agent/agent_init.py:62`, `agent/agent_runtime_helpers.py:44`). Do not import `run_agent` at module top in `agent/*`.
- **Plugin import order**: `providers/__init__.py:140` (`_discover_providers`) and `hermes_cli/plugins.py:1633` (`discover_plugins`) must run before any `get_provider_profile` / `PluginManager` lookup. Both are idempotent and gated by a `_discovered` flag.
- **System prompt immutability within a session**: `agent._cached_system_prompt` is built once and never re-rendered mid-session — only context compression triggers a rebuild (`agent/system_prompt.py:61` docstring). This is load-bearing for upstream provider prefix-cache hit rates.
- **UTF-8 stdio**: `hermes_bootstrap.py` MUST be the first import in every entry point (`cli.py`, `run_agent.py`, `gateway/run.py`, `batch_runner.py`, `cron/scheduler.py`). POSIX is no-op; Windows reconfigures stdio + child-process env.
- **Skill file naming**: Each skill directory must contain exactly `SKILL.md` (uppercase). Lowercase variants are not discovered. Frontmatter parsed by `agent/skill_utils.parse_frontmatter` (`agent/skill_utils.py:88`).
- **Tool registration via AST scan**: `tools/registry.py:78` (`_module_registers_tools`) inspects each `tools/*.py` module's top-level AST for `registry.register(...)` calls to decide whether to import it. Helper modules that only call `registry.register` inside functions are skipped.

## Anti-Patterns

### Direct cross-layer imports of run_agent symbols

**What happens:** Code in `agent/*` reaches for `run_agent.OpenAI` or `run_agent.handle_function_call` directly.
**Why it's wrong:** Test fixtures patch these on the `run_agent` module via `mock.patch("run_agent.OpenAI", ...)`. A direct import binds the original reference and the patch is invisible to the `agent/*` module.
**Do this instead:** Use the `_ra()` lazy-indirection pattern (`agent/conversation_loop.py:111`): define a local `_ra()` returning `import run_agent`, then call `_ra().OpenAI` etc. at call time. The docstring at `agent/system_prompt.py:46` explains the contract.

### Eager plugin/provider imports

**What happens:** Calling `import plugins.memory` or `import providers.alibaba` at module top of a hot path.
**Why it's wrong:** Plugin discovery must run in order (bundled → user → project → pip) and is gated by `_discovered`. Premature imports break override precedence and may import partial plugins.
**Do this instead:** Always go through the public registry: `from providers import get_provider_profile` (`providers/__init__.py:65`) or `from hermes_cli.plugins import get_plugin_manager` (`hermes_cli/plugins.py:1625`). These trigger lazy discovery on first call.

### Mutating agent._cached_system_prompt

**What happens:** Adding "just one more line" to the cached prompt mid-session (e.g. appending platform hints after the first turn).
**Why it's wrong:** Anthropic and OpenAI prefix-cache by exact byte match of the system prompt prefix. Mid-session mutation invalidates the cache and triples token billing.
**Do this instead:** Put volatile content in the `volatile` tier built fresh each turn (`agent/system_prompt.py:61`). If a new stable component is needed, add it to `build_system_prompt_parts` and call `invalidate_system_prompt(agent)` (`agent/system_prompt.py:367`) to force one-time rebuild.

### Calling registry.register inside a function

**What happens:** A helper module calls `registry.register(...)` inside `def setup():` rather than at module top level.
**Why it's wrong:** `tools/registry.py:78` `_module_registers_tools` AST-scans only top-level `registry.register(...)` calls. Function-wrapped registrations are skipped during discovery and the tool silently never loads.
**Do this instead:** Always call `registry.register(...)` at module level (top of file, outside any function). See any file in `tools/*_tool.py` for the pattern.

## Error Handling

**Strategy:** Layered — classify at the edges, recover where possible, surface to user as friendly text.

**Patterns:**
- **Classification**: `agent/error_classifier.classify_api_error` (`agent/error_classifier.py`) returns a `FailoverReason` enum (rate_limit, auth_failed, network, context_too_small, model_overloaded, ...).
- **Retry with jittered backoff**: `agent/retry_utils.jittered_backoff` (`agent/retry_utils.py`) for transient errors.
- **Credential pool failover**: `agent/agent_runtime_helpers.recover_with_credential_pool` (`agent/agent_runtime_helpers.py:530`) rotates API keys on auth errors.
- **Transport failover**: `agent/agent_runtime_helpers.try_recover_primary_transport` (`agent/agent_runtime_helpers.py:710`) swaps transport (e.g. Anthropic → OpenAI-compat shim) on persistent errors.
- **Model switch**: `agent/agent_runtime_helpers.switch_model` (`agent/agent_runtime_helpers.py:1339`) drops to a fallback model.
- **Context compression on overflow**: When the provider returns "context length exceeded", `agent/context_compressor.ContextCompressor` summarizes and retries.
- **Surrogate / non-ASCII sanitization**: `agent/message_sanitization.py` scrubs invalid Unicode before sending to providers; tests cover round-trip safety.
- **Gateway exception handler**: `gateway/run.py:187` (`_gateway_loop_exception_handler`) catches unhandled exceptions in the daemon loop, logs forensics, and emits a user-facing redacted reply rather than crashing.
- **TUI crash logger**: `tui_gateway/server.py:50` (`_panic_hook`) appends unhandled exceptions to `~/.hermes/logs/tui_gateway_crash.log` because stdout is the JSON-RPC pipe.

## Cross-Cutting Concerns

**Logging**: Stdlib `logging` with module-level `logger = logging.getLogger(__name__)`. Setup in `hermes_logging.py` with session context (`set_session_context`). Logs go to `~/.hermes/logs/agent.log` + stderr (CLI only). Set `HERMES_PLUGINS_DEBUG=1` (`hermes_cli/plugins.py:174`) to surface plugin-discovery logs to stderr.

**Validation**:
- Tool arguments: `model_tools.coerce_tool_args` (`model_tools.py:606`) coerces strings to expected types per JSON schema.
- Provider responses: `agent/transports/base.py:67` `validate_response` is an opt-in transport hook.
- Skills: `agent/skill_utils.skill_matches_platform` (`agent/skill_utils.py:128`) filters by OS; `tools/skills_guard.py` AST-augments skill bodies for safety.
- Plugin manifests: `hermes_cli/plugins.py:233` `PluginManifest` validates `plugin.yaml` schema.

**Authentication**: Provider auth via env vars declared in `ProviderProfile.env_vars` (`providers/base.py:53`). OAuth flows (Copilot, Google, Qwen portal) handled by `hermes_cli/auth.py`. Credential pool rotates keys (`agent/credential_pool.py`). Plugin LLM calls go through `agent/plugin_llm.PluginLlm` (`agent/plugin_llm.py:598`) with trust policies (`_TrustPolicy`, `:164`).

**Internationalization**: `agent/i18n.py` provides `t(key)` translation lookup; locales live in `locales/<lang>/LC_MESSAGES/`.

**Redaction**: `agent/redact.redact_sensitive_text` (`agent/redact.py`) strips phone numbers, tokens, API keys from log output and user-facing error text.

---

*Architecture analysis: 2026-06-14*
