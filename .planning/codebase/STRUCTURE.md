# Codebase Structure

**Analysis Date:** 2026-06-14

## Directory Layout

```
hermes-agent/
├── agent/                     # Agent runtime internals (extracted from run_agent.py)
├── apps/                      # Desktop + installer frontends (Electron, Tauri)
│   ├── bootstrap-installer/   # Tauri-based installer app
│   ├── desktop/               # Electron desktop GUI
│   └── shared/                # Shared TS code between apps
├── acp_adapter/               # Agent Client Protocol adapter
├── acp_registry/              # ACP server registry
├── assets/                    # Static images/icons for branding
├── cron/                      # Cron scheduler for scheduled agent runs
├── datagen-config-examples/   # Example configs for synthetic data generation
├── docker/                    # Docker build assets + entrypoints
├── docs/                      # Top-level docs (architecture deep-dives)
├── gateway/                   # Multi-platform messaging gateway daemon
│   ├── platforms/             # Per-platform adapters (telegram, slack, ...)
│   ├── builtin_hooks/         # Gateway lifecycle hooks
│   └── assets/                # Gateway static assets
├── hermes_cli/                # Full CLI: subcommands, config, setup wizard
├── infographic/               # Infographic generation skill assets
├── locales/                   # i18n translations (zh_CN, etc.)
├── nix/                       # Nix packaging modules
├── optional-mcps/             # Optional MCP server implementations (linear, n8n)
├── optional-skills/           # Optional skill bundles (finance, health, security, ...)
├── packaging/                 # Platform packaging scripts (deb, rpm, pkg)
├── plugins/                   # Bundled plugins (model-providers, memory, web, platforms, ...)
│   ├── browser/               # Browser automation plugins
│   ├── context_engine/        # Context-engine plugins
│   ├── image_gen/             # Image-generation provider plugins
│   ├── kanban/                # Kanban board plugin
│   ├── memory/                # Memory provider plugins (mem0, honcho, hindsight, ...)
│   ├── model-providers/       # Inference provider profiles (alibaba, anthropic, ...)
│   ├── platforms/             # Community platform adapters (discord, irc, line, ...)
│   ├── video_gen/             # Video-generation provider plugins
│   └── web/                   # Web search plugins (brave, tavily, exa, firecrawl, ...)
├── providers/                 # ProviderProfile base + registry (lazy plugin discovery)
├── scripts/                   # Build/release/install/diagnostic scripts
├── skills/                    # Markdown skills (agentskills.io compatible)
│   ├── apple/                 # Apple ecosystem skills
│   ├── autonomous-ai-agents/  # Self-directed agent skills
│   ├── creative/              # Creative content (ASCII art, ComfyUI, excalidraw, ...)
│   ├── data-science/          # Data analysis skills
│   ├── devops/                # DevOps workflows
│   ├── diagramming/           # Diagram generation
│   ├── dogfood/               # Hermes-on-Hermes testing skills
│   ├── domain/                # Domain-specific skills
│   ├── email/                 # Email composition
│   ├── gaming/                # Game-related skills
│   ├── gifs/                  # GIF generation
│   ├── github/                # GitHub workflow skills
│   ├── index-cache/           # Cached skills index (generated)
│   ├── inference-sh/          # Inference platform skills
│   ├── mcp/                   # MCP-related skills
│   ├── media/                 # Media (spotify, youtube, ...)
│   ├── mlops/                 # ML ops skills (training, eval, inference, ...)
│   ├── movie-experts/         # AI film production expert system (14 experts)
│   ├── note-taking/           # Note-taking (obsidian, ...)
│   ├── productivity/          # Office productivity (notion, airtable, gworkspace)
│   ├── red-teaming/           # Security red-team skills
│   ├── research/              # Research skills
│   ├── smart-home/            # Smart home (homeassistant)
│   ├── social-media/          # Social media skills
│   ├── software-development/  # Dev workflow skills (plan, debug, TDD, ...)
│   └── yuanbao/               # Yuanbao (Baidu) integration skills
├── tests/                     # Test suite (pytest)
├── tools/                     # Tool implementations (file, web, browser, terminal, ...)
│   ├── computer_use/          # Computer-use tool (CUA backend)
│   └── environments/          # Execution backends (local, docker, ssh, modal, daytona)
├── tui_gateway/               # JSON-RPC bridge for TUI frontend
├── ui-tui/                    # TypeScript/React TUI frontend
├── web/                       # Web dashboard (Vite + React)
├── website/                   # Docusaurus marketing/docs site
├── cli.py                     # Standalone REPL entry (subset of hermes_cli)
├── run_agent.py               # AIAgent class + main() (213K lines)
├── mcp_serve.py               # MCP stdio server entry
├── hermes_bootstrap.py        # UTF-8 stdio bootstrap (import first)
├── hermes_state.py            # SessionDB SQLite layer (158K)
├── hermes_constants.py        # Constants + get_hermes_home()
├── hermes_logging.py          # Logging setup + session context
├── hermes_time.py             # Time/timezone helpers
├── batch_runner.py            # Batch job runner
├── model_tools.py             # Tool dispatch entry (handle_function_call)
├── toolsets.py                # Toolset alias definitions
├── toolset_distributions.py   # Toolset distribution metadata
├── trajectory_compressor.py   # Aggressive trajectory compression
├── mini_swe_runner.py         # Mini SWE-bench runner
├── utils.py                   # Shared utilities
├── pyproject.toml             # Python project + deps
├── package.json               # Root npm workspace (ui-tui, web, apps)
├── Dockerfile                 # Production image
├── docker-compose.yml         # Compose stack
└── setup-hermes.sh            # One-shot installer
```

## Directory Purposes

**`agent/`** (90+ files, the agent runtime extracted from `run_agent.py`):
- Purpose: All agent-internal modules — conversation loop, prompt assembly, context compression, transport adapters, error classification, credential management, skills loading, plugin LLM, memory management, model metadata, redaction, rate limiting.
- Contains: Pure-Python modules organized by concern (one file per concern).
- Key files: `agent/conversation_loop.py` (261K — the run_conversation body), `agent/prompt_builder.py` (71K), `agent/context_compressor.py` (96K), `agent/curator.py` (76K), `agent/agent_init.py` (83K — bootstraps AIAgent), `agent/agent_runtime_helpers.py` (102K — client construction, failover, model switching), `agent/tool_executor.py` (51K), `agent/system_prompt.py` (18K), `agent/transports/` (provider format conversion).

**`skills/`** (markdown skills):
- Purpose: agentskills.io-compatible skills organized by category.
- Contains: `<category>/<skill-name>/SKILL.md` (+ optional `references/`, `templates/`, `assets/`).
- Key files: 104 SKILL.md files across 26 category directories.
- Special: `skills/movie-experts/` is a recently added 14-expert AI film production system (`screenplay`, `style_genome`, `drawer`, `animator`, `editor`, `colorist`, `composer`, `performer`, `scene_builder`, `foley`, `spatial_audio`, `mixer`, `voicer`, `continuity`). Each expert has only a `SKILL.md` (no Python code). They declare cross-expert collaboration in YAML frontmatter under `metadata.hermes.related_skills` and an `expert_id` plus quality `metrics`.

**`plugins/`** (Python plugins):
- Purpose: Self-contained extensions registered at import time via `plugin.yaml` + `__init__.py:register(ctx)`.
- Contains: Subdirectories grouped by capability domain.
- Key subdirs:
  - `plugins/model-providers/` (29 providers: alibaba, anthropic, azure-foundry, bedrock, copilot, deepseek, gemini, gmi, huggingface, kimi-coding, minimax, nous, novita, nvidia, ollama-cloud, openai-codex, opencode-zen, openrouter, qwen-oauth, stepfun, xai, xiaomi, zai, ...). Each provider has `plugin.yaml` + `__init__.py` with a `ProviderProfile`.
  - `plugins/memory/` (memory providers: mem0, honcho, hindsight, holographic, byterover, openviking, retaindb, supermemory).
  - `plugins/web/` (search providers: brave_free, ddgs, exa, firecrawl, parallel, searxng, tavily, xai).
  - `plugins/platforms/` (community platform adapters: discord, google_chat, irc, line, mattermost, ntfy, simplex, teams).
  - `plugins/image_gen/`, `plugins/video_gen/` (generation providers).
  - `plugins/browser/` (browserbase, browser_use, firecrawl).
  - `plugins/kanban/`, `plugins/memory/`, `plugins/observability/`, `plugins/security-guidance/`, `plugins/spotify/`, `plugins/teams_pipeline/`, `plugins/hermes-achievements/`, `plugins/dashboard_auth/`, `plugins/disk-cleanup/`, `plugins/google_meet/`.

**`gateway/`** (multi-platform messaging daemon):
- Purpose: Long-running service that connects to messaging platforms and routes inbound messages to `AIAgent` instances.
- Contains: Platform adapters, session store, stream consumer, config parser, hooks, pairing, status reporting, memory monitor.
- Key files: `gateway/run.py` (913K — the gateway main loop), `gateway/platforms/base.py` (`BasePlatformAdapter`), `gateway/platforms/{telegram,slack,discord,whatsapp,matrix,signal,feishu,wecom,weixin,yuanbao,email,sms,bluebubbles,dingtalk,homeassistant,api_server,webhook}.py`, `gateway/session.py:668` (`SessionStore`), `gateway/stream_consumer.py:79` (`GatewayStreamConsumer`), `gateway/config.py:42` (`Platform` enum), `gateway/platform_registry.py:162` (`PlatformRegistry`), `gateway/platforms/ADDING_A_PLATFORM.md` (integration guide).

**`tools/`** (Python tool implementations):
- Purpose: Each file registers one or more tools with `tools/registry.py` at import time.
- Contains: Tool handlers + JSON schemas for everything the agent can call.
- Key files: `tools/registry.py` (central registry), `tools/file_tools.py` + `tools/file_operations.py`, `tools/web_tools.py`, `tools/browser_tool.py` (164K), `tools/terminal_tool.py` (114K), `tools/code_execution_tool.py`, `tools/delegate_tool.py` (subagents), `tools/send_message_tool.py` (cross-platform messaging), `tools/mcp_tool.py` (MCP client), `tools/skills_tool.py` + `tools/skills_hub.py` + `tools/skills_sync.py` (skill management), `tools/vision_tools.py`, `tools/tts_tool.py`, `tools/transcription_tools.py`, `tools/video_generation_tool.py`, `tools/image_generation_tool.py`, `tools/kanban_tools.py`, `tools/memory_tool.py`, `tools/voice_mode.py`.
- Subdirs: `tools/environments/` (execution backends: `local.py`, `docker.py`, `ssh.py`, `modal.py`, `daytona.py`, `singularity.py`), `tools/computer_use/` (CUA backend).

**`hermes_cli/`** (full CLI implementation):
- Purpose: Subcommand dispatcher + all `hermes <cmd>` handlers.
- Contains: argparse subparsers + per-command modules.
- Key files: `hermes_cli/main.py:11738` (`main()` — subcommand dispatch), `hermes_cli/config.py:1` (config.yaml loader, 263K), `hermes_cli/plugins.py:1004` (`PluginManager`), `hermes_cli/plugins_cmd.py` (`hermes plugins install/remove`), `hermes_cli/auth.py` (OAuth flows), `hermes_cli/gateway.py` (gateway management), `hermes_cli/models.py` + `hermes_cli/model_switch.py` (model picker), `hermes_cli/kanban.py` + `hermes_cli/kanban_db.py` (kanban board), `hermes_cli/profiles.py` (named profiles), `hermes_cli/setup.py` (interactive setup wizard), `hermes_cli/web_server.py` (web dashboard backend), `hermes_cli/doctor.py` (config doctor), `hermes_cli/mcp_config.py` + `hermes_cli/mcp_catalog.py` (MCP server catalog).

**`providers/`** (provider profile registry):
- Purpose: Houses the `ProviderProfile` base class and the lazy discovery registry.
- Contains: `providers/base.py` (`ProviderProfile`), `providers/__init__.py` (registry + discovery), `providers/README.md`.
- Note: Per-provider profiles live in `plugins/model-providers/<name>/`, NOT here. This dir is intentionally small.

**`tui_gateway/`** (JSON-RPC bridge for TUI):
- Purpose: Subprocess that exposes Python-agent operations to the TypeScript TUI via JSON-RPC over stdio.
- Contains: `tui_gateway/server.py:466` (`handle_request`), `tui_gateway/transport.py:67` (`Transport` protocol + `StdioTransport`), `tui_gateway/entry.py`, `tui_gateway/ws.py` (WebSocket variant), `tui_gateway/slash_worker.py`, `tui_gateway/event_publisher.py`.

**`ui-tui/`** (TUI frontend, TypeScript):
- Purpose: Rich terminal UI built with TypeScript (Ink / React for CLIs).
- Contains: `ui-tui/src/` (React-style components), `ui-tui/packages/`, `ui-tui/scripts/`.
- Note: Built with Vite; bundled and launched by `hermes_cli/main.py:_launch_tui`.

**`apps/`** (native desktop apps):
- Purpose: Installer + desktop GUI wrappers around the Python core.
- Contains: `apps/bootstrap-installer/` (Tauri installer), `apps/desktop/` (Electron app with `apps/desktop/electron/`, `apps/desktop/src/`), `apps/shared/` (shared TS).

**`web/`** (web dashboard):
- Purpose: Vite + React dashboard served by `hermes_cli/web_server.py`.
- Contains: `web/src/` (React app), `web/public/`, `web/vite.config.ts`.

**`tests/`** (pytest test suite):
- Purpose: Unit + integration tests for every layer.
- Contains: Per-module test files + `tests/conftest.py`, `tests/fakes/`, `tests/integration/`, `tests/e2e/`, `tests/stress/`, `tests/run_interrupt_test.py`. Subdirs mirror source structure: `tests/agent/`, `tests/gateway/`, `tests/hermes_cli/`, `tests/skills/`, `tests/plugins/`, `tests/providers/`, `tests/run_agent/`, `tests/acp_adapter/`, `tests/cron/`, `tests/docker/`.

**`scripts/`** (build + ops scripts):
- Purpose: Build, release, install, and diagnostic utilities.
- Contains: `scripts/release.py`, `scripts/install.sh` + `scripts/install.cmd` + `scripts/install.ps1`, `scripts/build_skills_index.py` (`scripts/build_skills_index.py:1` generates `skills/index-cache/`), `scripts/build_model_catalog.py`, `scripts/run_tests_parallel.py`, `scripts/contributor_audit.py`, `scripts/check-windows-footguns.py`, `scripts/lint_diff.py`, `scripts/discord-voice-doctor.py`.

**`optional-skills/`** and **`optional-mcps/`**:
- Purpose: Heavier / less-common skills and MCP servers not installed by default.
- `optional-skills/` includes `finance/`, `health/`, `security/`, `blockchain/`, `migration/`, plus duplicates of `autonomous-ai-agents/`, `creative/`, `devops/`, `mlops/`, `productivity/`, `research/`, `software-development/`, `web-development/`.
- `optional-mcps/` includes `linear/` and `n8n/`.

**`cron/`** (scheduled jobs):
- Purpose: Cron scheduler for recurring agent invocations.
- Used by: `hermes cron` commands, `cron/scheduler.py`.

**`website/`** (Docusaurus site):
- Purpose: Marketing + developer docs site.
- Contains: `website/docs/`, `website/src/`, `website/i18n/`, `website/sidebars.ts`.

## Key File Locations

**Entry Points:**
- `cli.py`: Standalone interactive REPL (lighter than `hermes_cli/main.py`).
- `hermes_cli/main.py:11738`: Full CLI dispatcher (`hermes`, `hermes chat`, `hermes gateway`, `hermes setup`, `hermes cron`, `hermes doctor`, `hermes plugins`, `hermes models`, `hermes acp`, `hermes sessions`, ...).
- `run_agent.py:294` (`AIAgent`): Programmatic agent class; `run_agent.py:4600` (`main`) for direct script invocation.
- `gateway/run.py`: Gateway daemon main.
- `mcp_serve.py`: MCP stdio server.
- `tui_gateway/server.py:466`: TUI JSON-RPC handler.
- `hermes_bootstrap.py`: UTF-8 stdio setup, imported FIRST by every entry point.
- `hermes` (shell script at repo root): bin shim that invokes `hermes_cli/main.py`.

**Configuration:**
- `pyproject.toml`: Python project, dependencies, build config.
- `package.json`: Root npm workspace coordinating `ui-tui/`, `web/`, `apps/`.
- `.env.example`: Documented environment variables (do NOT read `.env` contents).
- `cli-config.yaml.example`: Example gateway/agent config.
- `Dockerfile`, `docker-compose.yml`: Container build + orchestration.
- `setup-hermes.sh`: One-shot installer for POSIX.
- `flake.nix` + `flake.lock`: Nix flake for reproducible builds.
- `hermes_constants.py`: `get_hermes_home()` resolves `~/.hermes/` (or `$HERMES_HOME`).

**Core Logic:**
- `agent/conversation_loop.py:351` (`run_conversation`): One user turn through the agent.
- `agent/system_prompt.py:348` (`build_system_prompt`): Three-tier prompt assembly.
- `agent/prompt_builder.py:1039` (`build_skills_system_prompt`): Skills manifest in prompt.
- `agent/context_compressor.py:522` (`ContextCompressor`): Sliding-window summarization.
- `agent/tool_executor.py:110` (`execute_tool_calls_concurrent`): Tool dispatch.
- `model_tools.py:802` (`handle_function_call`): Tool handler lookup.
- `agent/curator.py:1388` (`run_curator_review`): Background skill review.
- `gateway/run.py`: Gateway daemon loop (913K lines, the largest file in the repo).
- `gateway/session.py:668` (`SessionStore`): Per-platform session routing.

**Testing:**
- `tests/conftest.py`: Shared pytest fixtures.
- `tests/fakes/`: In-memory fakes for tests.
- Per-module tests under `tests/<area>/`.

## Naming Conventions

**Python files (snake_case):**
- All `.py` files use `snake_case.py` — e.g. `run_agent.py`, `mcp_serve.py`, `agent/conversation_loop.py`, `tools/file_tools.py`, `gateway/platform_registry.py`.
- Test files mirror source: `tests/agent/test_conversation_loop.py`.

**Skill directories (kebab-case or snake_case):**
- Skill category dirs: `kebab-case` or single words — `movie-experts/`, `software-development/`, `data-science/`, `note-taking/`, `smart-home/`.
- Individual skill dirs: usually `snake_case` (e.g. `scene_builder`, `style_genome`) but may be single words (`screenplay`, `editor`, `colorist`, `drawer`). Match the convention of siblings in the same category.
- Skill body file: ALWAYS uppercase `SKILL.md` (uppercase is required by the loader).
- Description files in category dirs: `DESCRIPTION.md` (uppercase).

**Plugin directories (kebab-case or snake_case):**
- `plugins/model-providers/<name>/`: kebab-case (`alibaba-coding-plan`, `azure-foundry`, `ollama-cloud`, `openai-codex`, `qwen-oauth`) or single words (`alibaba`, `anthropic`, `gemini`, `nous`, `xai`).
- `plugins/platforms/<name>/`: kebab-case (`google_chat`, `mattermost`) or single words (`discord`, `irc`, `line`, `teams`).
- `plugins/memory/<name>/`, `plugins/web/<name>/`: lowercase, mostly single words.
- Plugin manifest: `plugin.yaml` (lowercase).
- Plugin entry: `__init__.py` exposing `register(ctx)`.

**TypeScript / web files (kebab-case + PascalCase for components):**
- `ui-tui/src/` and `web/src/`: React conventions — `PascalCase.tsx` for components, `kebab-case.ts` for utilities.
- Config: `eslint.config.mjs`, `tsconfig.json`, `vite.config.ts`.

**Module-level constants:**
- `UPPER_SNAKE_CASE`: `TOOLSETS`, `_HERMES_CORE_TOOLS` (`toolsets.py:32`), `DEFAULT_AGENT_IDENTITY` (`agent/prompt_builder.py`).
- Private module vars prefixed with `_`: `_REGISTRY` (`providers/__init__.py:43`), `_discovered` (`providers/__init__.py:45`).

**Class names:**
- `PascalCase`: `AIAgent`, `ContextCompressor`, `ProviderProfile`, `ProviderTransport`, `PluginManager`, `PluginContext`, `SessionStore`, `SessionEntry`, `PlatformRegistry`, `BasePlatformAdapter`, `GatewayStreamConsumer`, `StdioTransport`, `IterationBudget`.

## Where to Add New Code

**New tool (file/web/browser/etc.):**
1. Create `tools/<name>_tool.py`.
2. At module top level (NOT inside a function), call:
   ```python
   from tools import registry
   registry.register(
       name="<tool_name>",
       handler=<callable>,
       schema={<JSON schema>},
       toolset="<toolset_name>",
       check_fn=<requirements_check>,
   )
   ```
   See `tools/todo_tool.py` for a minimal example; `tools/file_tools.py` for a large one.
3. The AST scan in `tools/registry.py:78` will pick it up automatically.
4. Add tests under `tests/test_<name>_tool.py`.

**New skill:**
1. Pick a category under `skills/<existing-or-new-category>/` (or `optional-skills/` for heavy opt-in skills).
2. Create `skills/<category>/<skill-name>/SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: <skill-name>
   description: "<one-line description for skills_list>"
   version: 1.0.0
   platforms: [linux, macos, windows]
   prerequisites:
     tools: [<required hermes tool names>]
   metadata:
     hermes:
       tags: [<search tags>]
       related_skills: [<sibling skill names>]
       expert_id: <unique id>
       metrics: [<quality metrics>]
   ---
   # Skill Title
   <body>
   ```
3. Optional supporting files: `references/*.md`, `templates/*`, `assets/*`.
4. The skill is automatically discovered by `agent/skill_utils.iter_skill_index_files` and surfaced in `skills_list` / via `/<skill-name>` slash invocation.

**For the movie-experts pattern (collaborative expert system):**
1. All experts live as siblings under `skills/movie-experts/<expert>/SKILL.md`.
2. Cross-expert collaboration is declared in YAML: `metadata.hermes.related_skills: [list, of, sibling, experts]`.
3. Each expert owns one matrix/encoding (e.g. `style_genome` = 5D, `colorist` = CxSxZ, `editor` = FxRxT, `performer` = ExBxSxP, `foley` = 7D).
4. To add a new movie expert: drop a new `skills/movie-experts/<expert>/SKILL.md` and reference it from `related_skills` of upstream/downstream experts.

**New model provider:**
1. Create `plugins/model-providers/<provider-name>/`.
2. Add `plugin.yaml`:
   ```yaml
   name: <provider-name>-provider
   kind: model-provider
   version: 1.0.0
   description: <human description>
   ```
3. Add `__init__.py` that instantiates `ProviderProfile(...)` and calls `register_provider(profile)`:
   ```python
   from providers import register_provider
   from providers.base import ProviderProfile

   my_provider = ProviderProfile(
       name="<provider-name>",
       aliases=("<alias1>",),
       env_vars=("<API_KEY_ENV>",),
       base_url="https://api.example.com/v1",
       fallback_models=("model-1", "model-2"),
   )
   register_provider(my_provider)
   ```
4. See `plugins/model-providers/alibaba/__init__.py` for a minimal example; `plugins/model-providers/gemini/__init__.py` for a complex one.
5. If the provider needs a non-OpenAI transport, add `agent/transports/<provider>.py` implementing `ProviderTransport` and register it via `register_transport(api_mode, TransportCls)`.

**New platform adapter (community plugin):**
1. Create `plugins/platforms/<platform-name>/`.
2. Add `plugin.yaml` and `adapter.py` subclassing `BasePlatformAdapter` from `gateway/platforms/base.py`.
3. Add `register(ctx)` function calling `ctx.register_platform(...)` with optional hooks (`env_enablement_fn`, `apply_yaml_config_fn`, `cron_deliver_env_var`, `standalone_sender_fn`).
4. See `plugins/platforms/discord/`, `plugins/platforms/irc/`, `plugins/platforms/line/` for complete examples.
5. Read `gateway/platforms/ADDING_A_PLATFORM.md` for the full hook surface.

**New platform adapter (built-in, core contributors):**
1. Add `gateway/platforms/<platform>.py` with a `BasePlatformAdapter` subclass.
2. Add the platform to the `Platform` enum in `gateway/config.py`.
3. Add `check_<platform>_requirements()` function.
4. Register in `gateway/platforms/__init__.py`.

**New plugin (general capability — memory provider, web search provider, image gen, etc.):**
1. Create `plugins/<capability>/<name>/`.
2. Add `plugin.yaml` (manifest) + `__init__.py` with `register(ctx)` function.
3. Use the appropriate `PluginContext` registration method (`register_tool`, `register_command`, `register_memory_provider`, `register_hook`, ...).
4. See `plugins/memory/mem0/`, `plugins/web/tavily/`, `plugins/image_gen/` for examples.
5. See `hermes_cli/plugins.py:286` (`PluginContext`) for the full surface.

**New MCP server (optional):**
1. Create `optional-mcps/<name>/` with the MCP server implementation.
2. Register it in the catalog consumed by `hermes_cli/mcp_catalog.py`.

**New agent-internal module:**
1. Add `agent/<concern>.py` (one concern per file).
2. If the module needs symbols from `run_agent`, import via the `_ra()` lazy-indirection pattern (see `agent/conversation_loop.py:111`).
3. Do NOT import `run_agent` at module top level (circular import + breaks test patches).

**New CLI subcommand:**
1. Add `hermes_cli/<command>.py` with the command implementation.
2. Add a `cmd_<command>(args)` dispatcher in `hermes_cli/main.py`.
3. Wire the subparser in `hermes_cli/main.py:11738` (`main()`) using `subparsers.add_parser("<name>", ...)`.

**New test:**
1. Mirror source path under `tests/` — `tests/agent/test_<concern>.py` for `agent/<concern>.py`.
2. Use `tests/conftest.py` fixtures + `tests/fakes/` mocks.
3. Patch `run_agent` symbols via `mock.patch("run_agent.<name>", ...)` — the `_ra()` pattern in `agent/*` makes these patches propagate.

## Special Directories

**`~/.hermes/` (HERMES_HOME, runtime state — NOT committed):**
- Purpose: All per-user runtime state.
- Generated: Yes (created by `setup-hermes.sh` / `hermes setup`).
- Committed: No.
- Key contents: `config.yaml` (user config), `sessions.db` (SQLite session/conversation store), `logs/agent.log`, `plugins/` (user-installed plugins override bundled), `plans/` (plan-mode output), `SOUL.md` (persona), `USER.md` (user profile), `.env` (secrets — NEVER read contents).

**`skills/index-cache/` (generated index):**
- Purpose: Cached skills index built by `scripts/build_skills_index.py`.
- Generated: Yes.
- Committed: Yes (regenerated on release).
- Do not edit by hand.

**`hermes_agent.egg-info/` (packaging metadata):**
- Purpose: Generated by `pip install -e .` for editable installs.
- Generated: Yes.
- Committed: Sometimes (depends on install workflow).

**`.venv/` (virtualenv):**
- Purpose: Local Python virtualenv (uv-managed).
- Generated: Yes.
- Committed: No.

**`.planning/` (GSD planning docs):**
- Purpose: Where this document lives. Output of `/gsd:map-codebase`.
- Generated: Yes (by Claude Code GSD workflow).
- Committed: Per-team policy.

**`website/i18n/` (translations):**
- Purpose: Localized docs (zh-CN etc.).
- Generated: Partially (some auto-translated).
- Committed: Yes.

**`tools/environments/` (execution backends):**
- Purpose: Pluggable sandboxing backends for the `terminal` + `code_execution` tools.
- Key files: `local.py`, `docker.py`, `ssh.py`, `modal.py` (+ `modal_utils.py`), `daytona.py`, `singularity.py`, `managed_modal.py`, `base.py` (ABC), `file_sync.py`.
- Selected via `terminal_backend` config.

---

*Structure analysis: 2026-06-14*
