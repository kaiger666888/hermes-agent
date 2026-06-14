# Technology Stack

**Analysis Date:** 2026-06-14

## Languages

**Primary:**
- **Python 3.11+** (target: `requires-python = ">=3.11"` in `pyproject.toml`; tool.ty pinned to 3.13). Backend agent runtime, gateway, plugins, all tools, skills, MCP server, cron, tests. ~95% of the codebase.

**Secondary:**
- **TypeScript / JavaScript** — three bundled frontends under npm workspaces (`package.json`):
  - `apps/desktop/` — Electron 40 + Vite 8 + React 19 desktop shell (`apps/desktop/package.json`)
  - `ui-tui/` — Ink 6 (React 19) terminal UI (`ui-tui/package.json`)
  - `web/` — Vite + React 19 web dashboard (`web/package.json`)
- **Bash** — `setup-hermes.sh`, `Dockerfile` helper scripts, `docker/*.sh`, plugin install hooks.
- **Nix** — `flake.nix`, `nix/` overlays/modules for reproducible packaging.

## Runtime

**Environment:**
- Python 3.11 minimum (3.13 used by type-checker `ty`); the published Docker image ships Python 3.13 via the `uv:0.11.6-python3.13-trixie` source stage (`Dockerfile:1`).
- Node.js 22 LTS — copied from `node:22-bookworm-slim` into the Docker image; root `package.json` declares `"engines": { "node": ">=20.0.0" }`.
- Electron 40.9.3 ships in `apps/desktop/package.json` devDependencies for the desktop build.

**Package Manager:**
- **uv 0.11.6** for Python (lockfile `uv.lock` present, ~all dependencies exact-pinned per `pyproject.toml` comments). Installed via `COPY --from=uv_source /usr/local/bin/uv /usr/local/bin/uvx` in `Dockerfile`.
- **npm** (workspaces) for JS — root `package.json` declares `"workspaces": ["apps/*"]`, with separate `package-lock.json` files at `apps/desktop/`, `ui-tui/`, `web/`. `npm_config_install_links=false` is enforced in the Dockerfile.
- Lockfiles: `uv.lock` (Python, frozen); `package-lock.json` x4 (root + each workspace).

## Frameworks

**Core:**
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

**Testing:**
- **pytest** `==9.0.2` with `pytest-asyncio==1.3.0`, `pytest-timeout==2.4.0` (`[dev]` extra). Per-file subprocess parallelism via `scripts/run_tests_parallel.py`. 30s per-test timeout, `addopts` in `pyproject.toml:261`.
- **Vitest** 4.x — `ui-tui/` and `apps/desktop/` test runner.
- **ty** `==0.0.21` — type checker (Astral; `[dev]` extra, configured via `[tool.ty]` table).
- **Ruff** `==0.15.10` — linter/formatter with preview rules; only `PLW1514` (unspecified-encoding) is enabled (`[tool.ruff.lint]`).
- **debugpy** `==1.8.20` — `[dev]` extra for attach debugging.

**Build/Dev:**
- **setuptools** `==82.0.1` (`[dev]` extra) + `setup.py` shim — Python packaging backend (`[build-system] requires = ["setuptools>=61.0"]`).
- **Vite** 8.x (desktop), 7.x (web) — JS bundler.
- **electron-builder** `^26.8.1` — desktop distributable (dmg/zip/nsis/msi/AppImage/deb/rpm).
- **esbuild** `~0.27.0` — `ui-tui/packages/hermes-ink/` build.
- **Playwright** (Chromium, shell-only) — installed at Docker build time (`npx playwright install --with-deps chromium --only-shell`); powers browser tools.
- **uv2nix / pyproject.nix** — Nix packaging (`flake.nix`).

## Key Dependencies

**Critical:**
- `openai==2.24.0` — every LLM call routes through the OpenAI SDK (native OpenAI-compatible, OpenRouter, Nous Portal, Codex Responses, etc.).
- `httpx[socks]==0.28.1` — async HTTP for Gemini native, Bedrock OAuth, gateway webhook platforms (Telegram, Discord, Slack, Matrix, …), and most plugins.
- `mcp==1.26.0` + `starlette==1.0.1` (CVE-2026-48710 BadHost pin) — MCP server/client; `mcp_serve.py` exposes a stdio MCP server; agent also acts as MCP client for `mcp_servers` config.
- `pydantic==2.13.4` — schema validation, settings, tool signatures.
- `fastapi>=0.104.0,<1` — dashboard + gateway HTTP API surface.
- `tenacity==9.1.4` — `agent/retry_utils.py`, every provider adapter.

**Infrastructure:**
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

**Environment:**
- Python env: `python-dotenv` reads `~/.hermes/.env` (location configurable via `HERMES_HOME`). Template at `.env.example` — ~110 documented env vars covering LLM providers, gateways, browser backends, terminal backends, OAuth, cron delivery channels.
- Config file: `cli-config.yaml` (copied from `cli-config.yaml.example`). Loaded by `hermes_cli/config.py`. YAML schema documented inline in the example: `model`, `terminal`, `browser`, `toolsets`, `platform_toolsets`, `mcp_servers`, `auxiliary`, `memory`, `compression`, `agent`, `display`, `skills`, `cronjob`, plus per-platform blocks.
- Precedence: CLI flags > env vars > `cli-config.yaml` > defaults. `--model` and `--provider` flags override at every invocation.
- Tool selection per platform via `platform_toolsets:` map (defaults: `hermes-cli`, `hermes-telegram`, `hermes-discord`, etc.).
- Plugin manifests: `plugin.yaml` / `plugin.yml` under each `plugins/*/*/` directory; declared in `[tool.setuptools.package-data]` so wheels/sdists carry them (`pyproject.toml:233-245`, `MANIFEST.in`).
- Optional MCP catalog: `optional-mcps/<name>/manifest.yaml` (currently `linear` remote OAuth MCP, `n8n` stdio git-install MCP).

**Build:**
- Python: `pyproject.toml` (setuptools backend, exact-pinned deps, 22+ optional-dependencies groups). Lock: `uv.lock`.
- JS: per-workspace `package.json` + `package-lock.json`. Build commands: `apps/desktop`: `npm run build` (tsc -b && vite build) then `electron-builder`. `ui-tui`: `node scripts/build.mjs` (esbuild). `web`: `tsc -b && vite build`.
- Container: `Dockerfile` (Debian 13.4 base, s6-overlay 3.2.3.0 as PID 1, multi-arch amd64/arm64). Compose: `docker-compose.yml`, `docker-compose.windows.yml`.
- Native packaging: `flake.nix` (nixpkgs + uv2nix + pyproject.nix + flake-parts). Termux constraints: `constraints-termux.txt`. Homebrew/AUR downstream packagers consume the wheel.
- Build artifacts committed for distribution: `apps/desktop/electron/`, `hermes_cli/web_dist/`, `hermes_cli/tui_dist/` (declared in `[tool.setuptools.package-data]`).

## Platform Requirements

**Development:**
- Python 3.11+ (3.13 for `ty` type-check), Node 20+ (22 LTS recommended), npm, uv.
- Linux / macOS / Windows / Termux (Android) — all first-class. `psutil`, `ptyprocess`/`pywinpty`, `tzdata` (Windows) ensure cross-platform parity.
- Optional native deps for `[voice]` (faster-whisper → ctranslate2, onnxruntime wheels) — Linux/macOS only; deliberately kept out of `[all]` per the policy comment (`pyproject.toml:202-208`).

**Production:**
- Primary deployment target: Docker container via `docker-compose.yml` (gateway + dashboard services, s6-overlay supervised).
- Also: Nix (`nix build`), Homebrew formula, AUR, Windows installer (NSIS/MSI), macOS DMG/ZIP (notarized via `apps/desktop/electron/notarize.cjs`).
- Cloud sandbox backends (terminal tool): Modal (`tools/environments/modal.py`), Daytona (`tools/environments/daytona.py`), Docker (`tools/environments/docker.py`), Singularity/Apptainer (`tools/environments/singularity.py`), SSH (`tools/environments/ssh.py`), Local (`tools/environments/local.py`).
- Cloud browser backends: Browserbase, Browser Use, Firecrawl (`plugins/browser/*/`).

---

*Stack analysis: 2026-06-14*
