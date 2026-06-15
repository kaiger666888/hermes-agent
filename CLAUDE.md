<!-- GSD:project-start source:PROJECT.md -->
## Project

**Movie-Experts Suite v2 — 短剧/微电影创作专家增强**

Hermes Agent 的 `skills/movie-experts/` 专家体系的增强项目:在现有 14 个电影制作专家(编剧、绘图、动画、剪辑、调色、配乐、表演、场景、拟音、空间音频、混音、配音、连续性、风格基因组)基础上,通过 RAG 增强其行业经验,并补全 AI 短剧(短剧/竖屏短剧)与微电影创作全链路的关键缺口 —— 新增运镜指导、Hook & Retention、制作管理、合规与宣发 4 个专家。目标是让每个专家不再是「懂语法的模板」,而是「懂行业的专家」。

**Core Value:** 每个 movie-expert skill 都能用检索增强的方式调用行业知识库(静态 refs 为主,可选向量 RAG),让 AI 生成的短剧/微电影在专业度上接近人类创作者水平 —— 这是决定短剧生死的核心。

### Constraints

- **Tech stack**: SKILL.md + references/*.md 纯 markdown;可选调用 Hermes memory plugin(通过 prompt 指令,不修改 plugin 本身)
- **Deliverable form**: 仅 skill 内容(refs + SKILL.md + eval scripts),不改 Hermes 核心 Python/JS 代码 —— *用户明确选择以控制范围*
- **Language**: SKILL.md 双语(英文 YAML 结构 + metadata 保留英文;description 与正文采用 EN structure + 中文段落/示例);refs 以中文为主,关键术语保留英文
- **Eval**: v1 含轻量 LLM-as-judge 双盲 harness(每个 skill 有 benchmark prompts + judge 脚本 + 报告输出)
- **Knowledge sources**: 4 种 —— 专业书籍/论文、现有短剧/微电影样本(仅公开/授权)、平台指南与爆款公式、AI 生成工具实践经验
- **Copyright**: 所有 refs 必须标注来源与版权状态;只使用公开授权或合理引用(fair use)范围内的素材
- **Compatibility**: 不破坏现有 14 专家的 expert_id 与 related_skills 协作图;新增专家必须接入现有协作图
- **Scope**: v1 = 14 重构 + 4 新增 + eval harness;后续扩展(v2)再考虑制作执行编排器、自动化 ingestion 等
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- **Python 3.11+** (target: `requires-python = ">=3.11"` in `pyproject.toml`; tool.ty pinned to 3.13). Backend agent runtime, gateway, plugins, all tools, skills, MCP server, cron, tests. ~95% of the codebase.
- **TypeScript / JavaScript** — three bundled frontends under npm workspaces (`package.json`):
- **Bash** — `setup-hermes.sh`, `Dockerfile` helper scripts, `docker/*.sh`, plugin install hooks.
- **Nix** — `flake.nix`, `nix/` overlays/modules for reproducible packaging.
## Runtime
- Python 3.11 minimum (3.13 used by type-checker `ty`); the published Docker image ships Python 3.13 via the `uv:0.11.6-python3.13-trixie` source stage (`Dockerfile:1`).
- Node.js 22 LTS — copied from `node:22-bookworm-slim` into the Docker image; root `package.json` declares `"engines": { "node": ">=20.0.0" }`.
- Electron 40.9.3 ships in `apps/desktop/package.json` devDependencies for the desktop build.
- **uv 0.11.6** for Python (lockfile `uv.lock` present, ~all dependencies exact-pinned per `pyproject.toml` comments). Installed via `COPY --from=uv_source /usr/local/bin/uv /usr/local/bin/uvx` in `Dockerfile`.
- **npm** (workspaces) for JS — root `package.json` declares `"workspaces": ["apps/*"]`, with separate `package-lock.json` files at `apps/desktop/`, `ui-tui/`, `web/`. `npm_config_install_links=false` is enforced in the Dockerfile.
- Lockfiles: `uv.lock` (Python, frozen); `package-lock.json` x4 (root + each workspace).
## Frameworks
- **OpenAI Python SDK** `openai==2.24.0` — universal LLM client; every OpenAI-compatible provider (`custom`, `openrouter`, `nous`, `zai`, `kimi-coding`, `minimax`, `lmstudio`, …) goes through it. (`pyproject.toml:34`)
- **FastAPI** `>=0.104.0,<1` (core) / `fastapi==0.133.1` (`[web]` extra) — dashboard API server, gateway `api_server.py`.
- **Uvicorn** `>=0.24.0,<1` (core) / `uvicorn[standard]==0.41.0` (`[web]` extra) — ASGI server for `hermes dashboard` and the OpenAI-compatible gateway API.
- **MCP SDK** `mcp==1.26.0` — both client (tool dispatch from agent) and server (`mcp_serve.py` uses `mcp.server.fastmcp.FastMCP`).
- **Pydantic** `==2.13.4` (bumped for pydantic-core 2.46.4 to fix Responses-API thread crash — see comment in `pyproject.toml:44-48`).
- **httpx** `==0.28.1` with `[socks]` — primary async HTTP client; every provider adapter uses it for non-SDK calls (Gemini, Bedrock, OAuth, webhook platforms).
- **Anthropic SDK** `anthropic==0.86.0` — `[anthropic]` extra, used by `agent/anthropic_adapter.py` for native messages-API calls.
- **Rich** `==14.3.3` — CLI banners, panels, spinners, skin engine.
- **prompt_toolkit** `==3.0.52` — interactive CLI input (`cli.py`).
- **fire** `==0.7.1` — legacy CLI argument parsing.
- **tenacity** `==9.1.4` — retry/backoff for API calls (`agent/retry_utils.py`).
- **PyYAML** `==6.0.3` + **ruamel.yaml** `==0.18.17` — config.yaml + plugin manifests.
- **Jinja2** `==3.1.6` — prompt templating.
- **pytest** `==9.0.2` with `pytest-asyncio==1.3.0`, `pytest-timeout==2.4.0` (`[dev]` extra). Per-file subprocess parallelism via `scripts/run_tests_parallel.py`. 30s per-test timeout, `addopts` in `pyproject.toml:261`.
- **Vitest** 4.x — `ui-tui/` and `apps/desktop/` test runner.
- **ty** `==0.0.21` — type checker (Astral; `[dev]` extra, configured via `[tool.ty]` table).
- **Ruff** `==0.15.10` — linter/formatter with preview rules; only `PLW1514` (unspecified-encoding) is enabled (`[tool.ruff.lint]`).
- **debugpy** `==1.8.20` — `[dev]` extra for attach debugging.
- **setuptools** `==82.0.1` (`[dev]` extra) + `setup.py` shim — Python packaging backend (`[build-system] requires = ["setuptools>=61.0"]`).
- **Vite** 8.x (desktop), 7.x (web) — JS bundler.
- **electron-builder** `^26.8.1` — desktop distributable (dmg/zip/nsis/msi/AppImage/deb/rpm).
- **esbuild** `~0.27.0` — `ui-tui/packages/hermes-ink/` build.
- **Playwright** (Chromium, shell-only) — installed at Docker build time (`npx playwright install --with-deps chromium --only-shell`); powers browser tools.
- **uv2nix / pyproject.nix** — Nix packaging (`flake.nix`).
## Key Dependencies
- `openai==2.24.0` — every LLM call routes through the OpenAI SDK (native OpenAI-compatible, OpenRouter, Nous Portal, Codex Responses, etc.).
- `httpx[socks]==0.28.1` — async HTTP for Gemini native, Bedrock OAuth, gateway webhook platforms (Telegram, Discord, Slack, Matrix, …), and most plugins.
- `mcp==1.26.0` + `starlette==1.0.1` (CVE-2026-48710 BadHost pin) — MCP server/client; `mcp_serve.py` exposes a stdio MCP server; agent also acts as MCP client for `mcp_servers` config.
- `pydantic==2.13.4` — schema validation, settings, tool signatures.
- `fastapi>=0.104.0,<1` — dashboard + gateway HTTP API surface.
- `tenacity==9.1.4` — `agent/retry_utils.py`, every provider adapter.
- `python-dotenv==1.2.2` — `.env` loading (`~/.hermes/.env`).
- `croniter==6.0.0` — `cron/scheduler.py` (cron extra now in core).
- `PyJWT[crypto]==2.12.1` (CVE-2026-32597 pin) — Skills Hub GitHub App JWT auth.
- `psutil==7.2.2` — cross-platform PID/process-tree walking; replaces `os.kill(pid, 0)` (POSIX-only, silent killer on Windows — see `pyproject.toml:62-66`).
- `tzdata==2025.3` (Windows-only) — Olson tzdata for `zoneinfo`.
- `requests==2.33.0` (CVE-2026-25645 pin) — sync HTTP for some providers (e.g. Langfuse SDK).
- `prompt_toolkit==3.0.52`, `rich==14.3.3` — CLI UX.
- `ptyprocess==0.7.0` (POSIX) / `pywinpty==2.0.0` (Windows) — PTY allocation for terminal tool.
- `node-pty 1.1.0` — Electron desktop PTY (`apps/desktop/package.json`).
- `agent-browser ^0.26.0` (`package.json`) — bundled browser automation core for JS side.
- `@streamdown/math`, `streamdown`, `react-shiki`, `katex` — markdown/math/code rendering in desktop and TUI.
## Configuration
- Python env: `python-dotenv` reads `~/.hermes/.env` (location configurable via `HERMES_HOME`). Template at `.env.example` — ~110 documented env vars covering LLM providers, gateways, browser backends, terminal backends, OAuth, cron delivery channels.
- Config file: `cli-config.yaml` (copied from `cli-config.yaml.example`). Loaded by `hermes_cli/config.py`. YAML schema documented inline in the example: `model`, `terminal`, `browser`, `toolsets`, `platform_toolsets`, `mcp_servers`, `auxiliary`, `memory`, `compression`, `agent`, `display`, `skills`, `cronjob`, plus per-platform blocks.
- Precedence: CLI flags > env vars > `cli-config.yaml` > defaults. `--model` and `--provider` flags override at every invocation.
- Tool selection per platform via `platform_toolsets:` map (defaults: `hermes-cli`, `hermes-telegram`, `hermes-discord`, etc.).
- Plugin manifests: `plugin.yaml` / `plugin.yml` under each `plugins/*/*/` directory; declared in `[tool.setuptools.package-data]` so wheels/sdists carry them (`pyproject.toml:233-245`, `MANIFEST.in`).
- Optional MCP catalog: `optional-mcps/<name>/manifest.yaml` (currently `linear` remote OAuth MCP, `n8n` stdio git-install MCP).
- Python: `pyproject.toml` (setuptools backend, exact-pinned deps, 22+ optional-dependencies groups). Lock: `uv.lock`.
- JS: per-workspace `package.json` + `package-lock.json`. Build commands: `apps/desktop`: `npm run build` (tsc -b && vite build) then `electron-builder`. `ui-tui`: `node scripts/build.mjs` (esbuild). `web`: `tsc -b && vite build`.
- Container: `Dockerfile` (Debian 13.4 base, s6-overlay 3.2.3.0 as PID 1, multi-arch amd64/arm64). Compose: `docker-compose.yml`, `docker-compose.windows.yml`.
- Native packaging: `flake.nix` (nixpkgs + uv2nix + pyproject.nix + flake-parts). Termux constraints: `constraints-termux.txt`. Homebrew/AUR downstream packagers consume the wheel.
- Build artifacts committed for distribution: `apps/desktop/electron/`, `hermes_cli/web_dist/`, `hermes_cli/tui_dist/` (declared in `[tool.setuptools.package-data]`).
## Platform Requirements
- Python 3.11+ (3.13 for `ty` type-check), Node 20+ (22 LTS recommended), npm, uv.
- Linux / macOS / Windows / Termux (Android) — all first-class. `psutil`, `ptyprocess`/`pywinpty`, `tzdata` (Windows) ensure cross-platform parity.
- Optional native deps for `[voice]` (faster-whisper → ctranslate2, onnxruntime wheels) — Linux/macOS only; deliberately kept out of `[all]` per the policy comment (`pyproject.toml:202-208`).
- Primary deployment target: Docker container via `docker-compose.yml` (gateway + dashboard services, s6-overlay supervised).
- Also: Nix (`nix build`), Homebrew formula, AUR, Windows installer (NSIS/MSI), macOS DMG/ZIP (notarized via `apps/desktop/electron/notarize.cjs`).
- Cloud sandbox backends (terminal tool): Modal (`tools/environments/modal.py`), Daytona (`tools/environments/daytona.py`), Docker (`tools/environments/docker.py`), Singularity/Apptainer (`tools/environments/singularity.py`), SSH (`tools/environments/ssh.py`), Local (`tools/environments/local.py`).
- Cloud browser backends: Browserbase, Browser Use, Firecrawl (`plugins/browser/*/`).
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- `snake_case.py` for all modules. Examples: `error_classifier.py`, `hermes_logging.py`, `trajectory_compressor.py`, `run_agent.py`.
- Top-level modules live at the repo root (`cli.py`, `utils.py`, `hermes_state.py`, `model_tools.py`, `toolsets.py`). Subpackage modules live under their package (`agent/insights.py`, `gateway/session.py`, `hermes_cli/config.py`).
- Test files: `tests/test_<module>.py` or `tests/<package>/test_<topic>.py`. Examples: `tests/test_hermes_logging.py`, `tests/agent/test_i18n.py`, `tests/test_trajectory_compressor.py`.
- Test class files: `tests/test_<thing>.py` containing one or more `class Test<Thing>:` groups.
- `snake_case` for all functions and methods. Examples: `setup_logging()`, `classify_api_error()`, `get_default_hermes_root()`, `_extract_status_code()`.
- Private helpers are prefixed with a single underscore: `_classify_402()`, `_load_catalog()`, `_normalize_lang()`.
- Async functions follow the same naming; no `async_` prefix or `_async` suffix convention. Callers know they are async from `await`.
- `snake_case` for locals and module globals. Module-level constants are `UPPER_SNAKE_CASE`: `SUPPORTED_LANGUAGES`, `DEFAULT_LANGUAGE`, `_NOISY_LOGGERS`, `_CREDENTIAL_SUFFIXES`, `TRUTHY_STRINGS`.
- Module-private singletons are prefixed `_`: `_logging_initialized`, `_session_context`, `_catalog_cache`.
- `PascalCase` for classes: `ClassifiedError`, `FailoverReason`, `CompressionConfig`, `TrajectoryMetrics`, `InsightsEngine`.
- Enums subclass `enum.Enum` with lowercase values: `FailoverReason.auth = "auth"`, `FailoverReason.context_overflow = "context_overflow"`.
- Dataclasses for structured records — see `@dataclass class ClassifiedError` in `agent/error_classifier.py:69`.
- Test classes: `class TestXxx:` with methods `test_<scenario>`. See `tests/test_hermes_constants.py:18` (`class TestGetDefaultHermesRoot:`).
- Public API functions and class attributes are type-hinted. Internal helpers may omit annotations when obvious.
- Mixing legacy and PEP 604 syntax is acceptable: `agent/i18n.py` uses `str | None` (modern); `agent/error_classifier.py` uses `from __future__ import annotations` + `Optional[int]`. Prefer `from __future__ import annotations` at the top of new modules to enable PEP 604 / PEP 585 generics on Python 3.11.
- Return-type annotations are encouraged on public functions: `def get_language() -> str:`, `def t(key: str, ...) -> str:`.
## Code Style
- **No Black / autopep8 / yapf.** Formatting is enforced manually; the only automated linter is **Ruff** with a very narrow ruleset.
- Indent: 4 spaces. Line length: ~100 chars (soft; longer lines tolerated when comments explain non-obvious code).
- Quoting: double quotes for strings (`"foo"`, `"PascalCase"`). Single quotes appear occasionally in older code; do not introduce new ones.
- **Ruff** `0.15.10` (declared in `[project.optional-dependencies] dev`). Config in `pyproject.toml:270`:
- **PLW1514 (`unspecified-encoding`)** is the single load-bearing rule. It forces every `open()` / `read_text()` / `write_text()` to pass an explicit `encoding="utf-8"`. Rationale (from `pyproject.toml:274`): Windows defaults to cp1252 and silently corrupts non-ASCII content. Examples of compliant usage from `agent/i18n.py:141`:
- Per-file ignores (`pyproject.toml:283`):
- **Type checker:** `ty` `0.0.21` (Astral's experimental type checker). Runs in CI as an **advisory diff** (not blocking). Configuration:
- CI workflow: `.github/workflows/lint.yml` — `Lint (ruff + ty)`. The `ruff check .` step blocks merge; the `ty` step is advisory.
- Add `encoding="utf-8"` to every text-mode `open()`, even in tests where it would be optional under Ruff's ignore. Defensive against Windows.
- No `from x import *`. Always explicit imports.
- Use `from __future__ import annotations` at the top of new modules for forward-compat type syntax.
## Import Organization
## Error Handling
- Catch specific exception types, not bare `except:`. The classifier walks `__cause__` / `__context__` chains (`error_classifier.py:1219-1233`) — preserve chains with `raise X from cause`.
- Use `(ExcA, ExcB, ExcC)` tuples for related exceptions. Example from `utils.py:277-280`:
- **`except Exception:` is acceptable** for best-effort fallback paths where the goal is "don't crash". Always log the exception. Example from `agent/i18n.py:143-147`:
- `except BaseException:` is used **only** when cleanup must run even on `KeyboardInterrupt`/`SystemExit`. Example: temp-file cleanup in `utils.py:141-148` re-raises after unlinking the partial temp file. Do not adopt this pattern casually.
- On `except`, **always bind the exception to a name** (`except X as exc:`) and include it in the log message (`logger.warning("...: %s", exc)`). Do not swallow silently.
## Logging
- `agent.log` — INFO+, all activity (catch-all)
- `errors.log` — WARNING+, triage log
- `gateway.log` — gateway-component records only (`mode="gateway"`)
- `gui.log` — dashboard / TUI-gateway records only (`mode="gui"`)
- Use `logger.debug()` for routine diagnostic noise (HTTP retries, keychain probes, cache hits). See `agent/anthropic_adapter.py:826,830,840,892,957,980,990,993`.
- Use `logger.warning()` for recoverable misconfiguration (missing i18n catalog, failed chmod, refresh failure).
- Use `logger.error()` / `logger.exception()` only for genuine failures that need operator attention. Most API errors flow through `error_classifier.py` and surface as warnings with the classified reason.
- **Lazy %-formatting** — always pass args positionally: `logger.warning("Failed: %s", exc)`, never f-strings in log calls. Lets the logging framework skip formatting when the level is filtered out.
- Third-party noisy loggers (`openai`, `httpx`, `urllib3`, `asyncio`, `modal`, `websockets`, etc.) are pinned to `WARNING` — see `_NOISY_LOGGERS` at `hermes_logging.py:54-69`. Add new chatty libraries there rather than filtering per-call.
## i18n
## Type Hints Usage
- **Required** on public functions and class `__init__` signatures. Encouraged on private helpers.
- Use `from __future__ import annotations` for forward references and PEP 604 unions (`str | None`) on Python 3.11+.
- Use `typing.Any` sparingly — prefer narrower types or generics.
- Module-level typed constants: `_CREDENTIAL_SUFFIXES: tuple[str, ...] = (...)` (`tests/conftest.py:57`), `_NOISY_LOGGERS` (`hermes_logging.py:54`).
- Frozen sets for lookup tables: `_TRANSPORT_ERROR_TYPES = frozenset({...})` (`error_classifier.py:365`).
## Docstring Style
- The supply-chain pinning rationale at `pyproject.toml:14-33`.
- The live-system guard rationale at `tests/conftest.py:496-522`.
- The pattern-list ordering rationale at `error_classifier.py:533-547`.
## Function Design
- **Single responsibility.** The classifier pipeline in `error_classifier.py` is decomposed into `_classify_by_status`, `_classify_by_error_code`, `_classify_by_message`, `_classify_400`, `_classify_402` — each ~50 lines, testable in isolation.
- **Keyword-only args** for public functions with many optional knobs. Example: `setup_logging(*, hermes_home, log_level, max_size_mb, backup_count, mode, force)` at `hermes_logging.py:166`. Use `*` to force callers to name arguments.
- **Default to returning structured objects over tuples.** `ClassifiedError` dataclass (`error_classifier.py:69`) rather than `(reason, retryable, should_compress, ...)`.
- **Helpers return `None` to signal "no classification"**, which the caller treats as "try the next classifier". See `_classify_by_status` returning `Optional[ClassifiedError]` (`error_classifier.py:725-878`).
- **Size guideline:** Functions over ~80 lines are candidates for extraction. The codebase tolerates longer functions when they're a flat switch-dispatch (e.g. `_classify_by_status`), but pushes back on nested logic.
## Module Design
- `hermes_logging._logging_initialized` (`hermes_logging.py:42`)
- `agent/i18n._catalog_cache` + `_catalog_lock` (`i18n.py:83-84`)
- `tools/registry.registry` (the global `ToolRegistry`)
## Skill File Conventions (SKILL.md)
- **`tags`**: List of lowercase hyphen-separated tags for skill search and discovery. Examples from `skills/movie-experts/style_genome/SKILL.md:12`: `[movie, style, director, genre, visual-dna, style-blending, cross-module]`.
- **`related_skills`**: List of `name`s of skills that this expert collaborates with in a pipeline. Drives cross-skill recommendation and DAG ordering. Example from `style_genome/SKILL.md:13`: `[screenplay, drawer, colorist, editor, composer, scene_builder, performer, continuity]`.
- **`expert_id`**: Stable identifier used by the worker-agent `/decide` endpoint to match an incoming request to this expert. Usually equal to `name`. Example: `expert_id: style_genome`.
- **`metrics`**: Quality dimensions the expert is accountable for, used by evaluation pipelines. Example from `style_genome/SKILL.md:15`: `[style_consistency, gene_extraction_accuracy, blend_coherence, cross_module_alignment]`.
- `# <Name> Expert (<Chinese name>)` — H1 with bilingual title.
- `## When to use this skill` — trigger conditions.
- `## Role & Philosophy` — 3-5 bullets.
- `## Core Capabilities` — bullet list.
- `## Output Format` — bulleted list of JSON artifact filenames this expert produces (`style_genome.json`, `style_blend_protocol.json`, ...).
- `## Key Parameters` — nested subsections per parameter group, with H3 (`###`) headers and bullet lists of ranges/defaults.
## Anti-Patterns to Avoid
- **Bare `except:`** — always catch specific types or `except Exception:`.
- **`open()` without `encoding=`** — Ruff will block the merge.
- **`Path.home() / ".hermes"`** in production code — use `get_hermes_home()` from `hermes_constants` instead. The conftest fixture redirects `HERMES_HOME` per-test; `Path.home()` bypasses that and leaks into real `~/.hermes`.
- **`os.kill(pid, sig)` or `subprocess.run(["systemctl", "restart", ...])` in tests** without explicit mocking — the autouse `_live_system_guard` fixture (`tests/conftest.py:537-841`) raises `RuntimeError`. Mock both `find_gateway_pids` and `os.kill`, or mark the test with `@pytest.mark.live_system_guard_bypass`.
- **Inline string-matching for API errors** at call sites — route through `classify_api_error()`.
- **`f"..."` in `logger.x(...)` calls** — use `%s` positional args.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## System Overview
```text
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
- **Self-registration over central registries**: Tools call `registry.register(...)` at module import; providers call `register_provider(profile)`; platforms call `ctx.register_platform(...)`. Discovery is AST-scanning + import-side-effect.
- **Lazy plugin discovery**: First call triggers scan of `plugins/`, `~/.hermes/plugins/`, `.hermes/plugins/`, and `pip` entry points (`hermes_cli/plugins.py`).
- **Three-tier system prompt caching**: Stable / context / volatile to keep upstream provider prefix caches warm (`agent/system_prompt.py:61`).
- **Forwarder shim pattern**: `AIAgent.run_conversation` is a 3-line forwarder to `agent/conversation_loop.run_conversation`; this preserves the public API while letting the implementation live in a 4,000-line extracted module.
- **Patch contract preservation**: `_ra()` returns the `run_agent` module lazily so `mock.patch("run_agent.X")` keeps working in tests after extraction (`agent/conversation_loop.py:111`).
## Layers
- Purpose: Multiple user-facing surfaces share one runtime.
- Location: `cli.py`, `hermes_cli/main.py`, `gateway/run.py`, `tui_gateway/server.py`, `mcp_serve.py`, `apps/desktop/electron/`
- Contains: argparse/CLI dispatch, REPL loop, daemon main, MCP server, JSON-RPC handlers
- Depends on: `run_agent.AIAgent`, `agent.*`, `gateway/session.SessionStore`
- Used by: End users, MCP clients (Claude Code, Cursor), TUI frontend, desktop app
- Purpose: One user turn = build prompt → call model → dispatch tools → loop until done → compress if needed → persist.
- Location: `run_agent.py`, `agent/conversation_loop.py`, `agent/prompt_builder.py`, `agent/system_prompt.py`, `agent/agent_init.py`, `agent/agent_runtime_helpers.py`, `agent/tool_executor.py`, `agent/context_compressor.py`, `agent/curator.py`
- Contains: Orchestration, retry/failover logic, prompt assembly, context management
- Depends on: `providers/`, `agent/transports/`, `tools/`, `toolsets.py`, `hermes_state.SessionDB`
- Used by: All entry points
- Purpose: Decouple "what the model expects" (OpenAI chat-completions format internally) from "what the provider speaks" (Anthropic messages, Bedrock, Codex responses, Gemini, etc.).
- Location: `providers/__init__.py`, `providers/base.py`, `plugins/model-providers/*/`, `agent/transports/{anthropic,bedrock,codex,chat_completions}.py`
- Contains: `ProviderProfile` dataclass (auth/endpoints/quirks), `ProviderTransport` ABC (convert_messages / convert_tools / build_kwargs / normalize_response)
- Depends on: Provider SDKs (`anthropic`, `openai`, `boto3`, `google-genai`), `agent/transports/types.NormalizedResponse`
- Used by: `run_agent.AIAgent`, `agent/agent_runtime_helpers.create_openai_client`
- Purpose: Extend agent capabilities with file/web/browser/code tools, markdown skills, and plugin-defined commands.
- Location: `tools/` (Python tools), `skills/` (markdown skills), `plugins/` (Python plugins)
- Contains: Tool handlers + schemas, skill markdown with YAML frontmatter, plugin `register(ctx)` entrypoints
- Depends on: `tools/registry.py`, `agent/skill_utils.py`, `hermes_cli/plugins.PluginContext`
- Used by: `model_tools.handle_function_call`, `agent/tool_executor.execute_tool_calls_concurrent`
- Purpose: Sessions, conversations, credentials, profiles, plans persist across runs.
- Location: `hermes_state.py:364` (`SessionDB`), `gateway/session.py:668` (`SessionStore`), `~/.hermes/` (HERMES_HOME)
- Contains: SQLite schema, session routing, transcript storage, profile/config YAML
- Depends on: `sqlite3` stdlib, `hermes_constants.get_hermes_home`
- Used by: All entry points and runtime layer
## Data Flow
### Primary Request Path (CLI REPL)
### Gateway Flow (Multi-Platform Daemon)
### TUI Flow
### Skill Invocation Flow (Slashes)
- **Session state**: SQLite (`~/.hermes/sessions.db`) via `hermes_state.SessionDB`. One row per turn.
- **In-memory state**: `AIAgent.messages` list, `AIAgent._cached_system_prompt`, `IterationBudget` (`agent/iteration_budget.py`).
- **Process state**: Gateway is a long-running asyncio loop; CLI is a per-invocation process; TUI is parent (TS) + child (Python via JSON-RPC).
- **Thread state**: Tool execution uses `concurrent.futures.ThreadPoolExecutor`; plugin tool whitelists use `contextvars` (`hermes_cli/plugins.py:1654`).
## Key Abstractions
- Purpose: Declarative description of an inference provider (auth, endpoints, model catalog, quirks).
- Examples: `plugins/model-providers/alibaba/__init__.py`, `plugins/model-providers/anthropic/__init__.py`, `plugins/model-providers/openrouter/__init__.py`
- Pattern: Dataclass registered at import time via `register_provider(profile)`. Lazy discovery on first `get_provider_profile()` call.
- Purpose: Owns data conversion for one `api_mode` (chat_completions, anthropic_messages, bedrock, codex_responses).
- Examples: `agent/transports/anthropic.py`, `agent/transports/bedrock.py`, `agent/transports/codex.py`, `agent/transports/chat_completions.py`
- Pattern: ABC with `convert_messages`, `convert_tools`, `build_kwargs`, `normalize_response` → `NormalizedResponse`.
- Purpose: Single internal type for parsed provider responses (text, tool calls, usage, finish reason).
- Purpose: Tools self-register at import; `model_tools.get_tool_definitions` queries the registry.
- Examples: Every `tools/<name>_tool.py` (e.g. `tools/file_tools.py`, `tools/web_tools.py`, `tools/browser_tool.py`, `tools/terminal_tool.py`).
- Pattern: Module-level `registry.register(name=..., handler=..., schema=..., toolset=..., check_fn=...)`.
- Purpose: Markdown document with YAML frontmatter that shapes the model's behavior when invoked.
- Examples: `skills/movie-experts/screenplay/SKILL.md`, `skills/software-development/plan/SKILL.md`, `skills/creative/comfyui/SKILL.md`.
- Pattern: Frontmatter declares `name`, `description`, `prerequisites`, `metadata.hermes.{tags, related_skills, expert_id, metrics}`. Loader is `tools/skills_tool.py` + `agent/skill_utils.py`. Skill body is injected as a user message.
- Purpose: Declarative plugin descriptor (`plugin.yaml`) plus runtime `register(ctx)` function.
- Examples: `plugins/model-providers/alibaba/plugin.yaml`, `plugins/memory/mem0/`, `plugins/platforms/discord/`.
- Pattern: `PluginContext` (`hermes_cli/plugins.py:286`) exposes `register_tool`, `register_platform`, `register_command`, `register_hook`, `register_memory_provider`, etc. Discovery scans bundled + user + project + pip-entrypoint sources.
- Purpose: One class per messaging platform (Telegram, Slack, Discord, WhatsApp, Matrix, Signal, etc.).
- Examples: `gateway/platforms/telegram.py`, `gateway/platforms/slack.py`, `gateway/platforms/api_server.py:680` (`APIServerAdapter`).
- Pattern: ABC requiring `connect`, `disconnect`, `send`, `send_typing`, `send_image`, `get_chat_info`. Built-ins live in `gateway/platforms/`; community plugins in `plugins/platforms/<name>/adapter.py` register via `ctx.register_platform(...)`.
- Purpose: Routes inbound events to per-chat conversation state. One `SessionEntry` per (platform, chat_id).
## Entry Points
- Location: `cli.py` (standalone REPL), `hermes_cli/main.py:11738` (full CLI dispatcher with subcommands)
- Triggers: `hermes`, `hermes chat`, `python cli.py`
- Responsibilities: Arg parsing, REPL prompt loop, model setup wizard, status display, TUI launcher
- Location: `run_agent.py:4600` (`main()`)
- Triggers: `python run_agent.py "query"` — direct script invocation
- Responsibilities: Minimal CLI wrapper using `fire` library; instantiates `AIAgent`, runs one conversation, prints result.
- Location: `gateway/run.py`, launched by `hermes_cli/main.py:1918` `cmd_gateway`
- Triggers: `hermes gateway`, `hermes gateway start` (service)
- Responsibilities: Long-running async loop; instantiates platform adapters, routes inbound, runs agent per session, delivers replies.
- Location: `mcp_serve.py`
- Triggers: `hermes mcp serve`
- Responsibilities: stdio FastMCP server exposing 9+ tools (`conversations_list`, `messages_read`, `messages_send`, `events_poll`, `permissions_respond`, `channels_list`, etc.) for MCP-aware clients.
- Location: `tui_gateway/server.py:466` (`handle_request`), `tui_gateway/entry.py`
- Triggers: Spawned as subprocess by `ui-tui/` TUI frontend (TypeScript)
- Responsibilities: JSON-RPC over stdio; methods include `session.create`, `chat.send`, `interrupt`, `tool.call`.
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
### Eager plugin/provider imports
### Mutating agent._cached_system_prompt
### Calling registry.register inside a function
## Error Handling
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
- Tool arguments: `model_tools.coerce_tool_args` (`model_tools.py:606`) coerces strings to expected types per JSON schema.
- Provider responses: `agent/transports/base.py:67` `validate_response` is an opt-in transport hook.
- Skills: `agent/skill_utils.skill_matches_platform` (`agent/skill_utils.py:128`) filters by OS; `tools/skills_guard.py` AST-augments skill bodies for safety.
- Plugin manifests: `hermes_cli/plugins.py:233` `PluginManifest` validates `plugin.yaml` schema.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
