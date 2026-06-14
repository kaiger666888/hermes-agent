# External Integrations

**Analysis Date:** 2026-06-14

Hermes is integration-first: nearly every capability (LLM, image, video, voice, search, browser, memory, messaging, MCP) is a pluggable backend selected via `config.yaml` or env vars. Two integration surfaces:

1. **Built-in adapters** — Python modules in `agent/`, `gateway/platforms/`, `tools/`.
2. **Plugin backends** — `plugin.yaml` manifests under `plugins/<category>/<name>/`, auto-discovered by `hermes_cli/plugins.py`, registered via `PluginContext.register_*` hooks.

Lazy dependency installation routes through `tools/lazy_deps.py` (`LAZY_DEPS` map) so a quarantined PyPI release cannot break fresh installs — see policy comment in `pyproject.toml:188-220`.

## APIs & External Services

### LLM Providers (model-providers)

Two-layer architecture: (a) **provider plugin** declares the endpoint + auth shape (`plugins/model-providers/<name>/plugin.yaml` + `__init__.py`); (b) **adapter module** in `agent/` implements the wire protocol when it deviates from OpenAI-compatible.

| Provider | Plugin | Adapter | Auth env var(s) | API wire |
|----------|--------|---------|-----------------|----------|
| OpenRouter (aggregator) | `plugins/model-providers/openrouter/` | OpenAI SDK | `OPENROUTER_API_KEY` | OpenAI |
| Nous Portal | `plugins/model-providers/nous/` | OpenAI SDK + `agent/credential_sources.py` | `hermes login` OAuth | OpenAI |
| Anthropic (native) | `plugins/model-providers/anthropic/` | `agent/anthropic_adapter.py` (anthropic SDK) | `ANTHROPIC_API_KEY` | anthropic-messages |
| AWS Bedrock | `plugins/model-providers/bedrock/` | `agent/bedrock_adapter.py` (boto3 `boto3==1.42.89`) | AWS creds (env / IAM) | bedrock-converse |
| Gemini (native API key) | `plugins/model-providers/gemini/` | `agent/gemini_native_adapter.py` (httpx, schema sanitize in `agent/gemini_schema.py`) | `GOOGLE_API_KEY` / `GEMINI_API_KEY` | Gemini OpenAI-compat |
| Gemini (Cloud Code OAuth) | `plugins/model-providers/gemini/` | `agent/gemini_cloudcode_adapter.py` + `agent/google_code_assist.py` | `agent/google_oauth.py` (OAuth 2.0 loopback) | Google Code Assist |
| OpenAI Codex (Responses API) | `plugins/model-providers/openai-codex/` | `agent/codex_responses_adapter.py` + `agent/codex_runtime.py` (subprocess runtime) | `hermes auth` OAuth token | OpenAI Responses |
| GitHub Copilot (ACP) | `plugins/model-providers/copilot-acp/` | `agent/copilot_acp_client.py` (ACP subprocess) | `GITHUB_TOKEN` | Agent Client Protocol |
| GitHub Copilot (direct) | `plugins/model-providers/copilot/` | OpenAI SDK | `GITHUB_TOKEN` | OpenAI-compat |
| Azure Foundry / Azure OpenAI | `plugins/model-providers/azure-foundry/` | `agent/azure_identity_adapter.py` (`azure-identity==1.25.3`) | API key OR `auth_mode: entra_id` (DefaultAzureCredential) | Azure OpenAI |
| Z.AI / GLM | `plugins/model-providers/zai/` | OpenAI SDK + `agent/moonshot_schema.py` | `GLM_API_KEY` | OpenAI-compat |
| Kimi / Moonshot | `plugins/model-providers/kimi-coding/` | OpenAI SDK | `KIMI_API_KEY` / `KIMI_CN_API_KEY` | OpenAI-compat |
| MiniMax (global/CN/OAuth) | `plugins/model-providers/minimax/` | OpenAI SDK | `MINIMAX_API_KEY` / `MINIMAX_CN_API_KEY` | OpenAI-compat |
| NovitaAI | `plugins/model-providers/novita/` | OpenAI SDK | `NOVITA_API_KEY` | OpenAI-compat |
| NVIDIA NIM | `plugins/model-providers/nvidia/` | OpenAI SDK | `NVIDIA_API_KEY` | OpenAI-compat |
| HuggingFace Inference | `plugins/model-providers/huggingface/` | OpenAI SDK | `HF_TOKEN` | OpenAI-compat (router) |
| Ollama Cloud | `plugins/model-providers/ollama-cloud/` | OpenAI SDK | `OLLAMA_API_KEY` | OpenAI-compat |
| LM Studio (local) | first-class via `provider: lmstudio` | OpenAI SDK | optional `LM_API_KEY` | OpenAI-compat |
| Custom / Ollama / vLLM / llama.cpp | `plugins/model-providers/custom/` | OpenAI SDK | `OPENAI_API_KEY` + `OPENAI_BASE_URL` | OpenAI-compat |
| Alibaba DashScope | `plugins/model-providers/alibaba/` | OpenAI SDK | `DASHSCOPE_API_KEY` | OpenAI-compat |
| Alibaba Cloud Coding Plan | `plugins/model-providers/alibaba-coding-plan/` | OpenAI SDK | — | OpenAI-compat |
| DeepSeek | `plugins/model-providers/deepseek/` | OpenAI SDK | `DEEPSEEK_API_KEY` | OpenAI-compat |
| xAI Grok | `plugins/model-providers/xai/` | OpenAI SDK (Responses API) | `XAI_API_KEY` or xAI Grok OAuth | OpenAI Responses |
| Arcee AI | `plugins/model-providers/arcee/` | OpenAI SDK | `ARCEEAI_API_KEY` | OpenAI-compat |
| KiloCode | `plugins/model-providers/kilocode/` | OpenAI SDK | `KILOCODE_API_KEY` | OpenAI-compat |
| OpenCode Zen / Go | `plugins/model-providers/opencode-zen/` | OpenAI SDK | `OPENCODE_ZEN_API_KEY` / `OPENCODE_GO_API_KEY` | OpenAI-compat |
| Qwen Portal (OAuth) | `plugins/model-providers/qwen-oauth/` | OpenAI SDK | `HERMES_QWEN_BASE_URL` + OAuth | OpenAI-compat |
| StepFun Step Plan | `plugins/model-providers/stepfun/` | OpenAI SDK | `STEPFUN_API_KEY` | OpenAI-compat |
| Xiaomi MiMo | `plugins/model-providers/xiaomi/` | OpenAI SDK | `XIAOMI_API_KEY` | OpenAI-compat |
| GMI Cloud | `plugins/model-providers/gmi/` | OpenAI SDK | `GMI_API_KEY` | OpenAI-compat |

Model routing / fallback chain lives in `hermes_cli/providers.py`, `hermes_cli/runtime_provider.py`, `hermes_cli/fallback_config.py`, and `hermes_cli/copilot_auth.py` / `hermes_cli/codex_models.py` / `hermes_cli/dingtalk_auth.py` (per-provider setup flows). Auxiliary tasks (vision, web_extract, compression, session_search) pick their own provider via the `auxiliary:` config block (see `cli-config.yaml.example:415-460`).

### OAuth / Identity Providers

| Provider | Module | Flow | Stored at |
|----------|--------|------|-----------|
| Google (Gemini Cloud Code, Workspace, Chat) | `agent/google_oauth.py` (loopback http.server, PKCE) + `agent/google_code_assist.py` (token refresh/exchange) | OAuth 2.0 authorization code + PKCE, redirect to `http://localhost:<port>` | `~/.hermes/auth.json` |
| GitHub (Copilot, App JWT for Skills Hub) | `hermes_cli/copilot_auth.py`; Skills Hub via `PyJWT[crypto]==2.12.1` (GitHub App JWT) | OAuth device flow + App JWT (Skills Hub publishing) | `~/.hermes/auth.json`, `GITHUB_TOKEN` |
| Azure AD (Foundry, Teams, Outlook) | `agent/azure_identity_adapter.py` (`azure-identity==1.25.3`) + `hermes_cli/azure_detect.py` | DefaultAzureCredential (az login, managed identity, workload identity, env vars) | env or Azure CLI cache |
| Spotify | `plugins/spotify/client.py` | OAuth 2.0 + PKCE via `hermes auth spotify` | `~/.hermes/auth.json` (`providers.spotify`) |
| Nous Portal (LLM + Dashboard) | `plugins/dashboard_auth/nous/` (OAuth 2.0 + PKCE); `hermes_cli/portal_cli.py` (CLI login) | Authorization code + PKCE | `~/.hermes/auth.json` |
| Linear (MCP) | `optional-mcps/linear/manifest.yaml` | Native MCP OAuth 2.1 + Dynamic Client Registration over Streamable HTTP (`https://mcp.linear.app/mcp`) | MCP token store via `mcp_oauth_manager` |
| Telegram / Slack / Discord / WhatsApp etc. | `gateway/platforms/<name>.py` | Per-platform bot tokens / OAuth | env vars in `~/.hermes/.env` |
| DingTalk | `gateway/platforms/dingtalk.py` + `hermes_cli/dingtalk_auth.py` | QR-code login (`qrcode==7.4.2`) | env / `dingtalk-stream` cache |
| WeCom | `gateway/platforms/wecom.py` + `wecom_callback.py` + `wecom_crypto.py` | Callback URL + AES XML crypto (`defusedxml==0.7.1`) | env |

### Image / Video / Audio / Search / Browser providers

Each category has a registry in `agent/` (`*_registry.py`) and an ABC in `agent/*_provider.py`. Backends register via `PluginContext.register_*` at plugin import time. Active backend is selected by `<category>.provider` in `cli-config.yaml` (e.g. `image_gen.provider: fal`).

**Image generation** (`agent/image_gen_registry.py`, `agent/image_gen_provider.py`):
| Backend | Plugin | SDK / wire | Env |
|---------|--------|-----------|-----|
| FAL.ai (flux, recraft, gpt-image) | `plugins/image_gen/fal/` | `fal-client==0.13.1` | `FAL_KEY` |
| OpenAI (gpt-image-2) | `plugins/image_gen/openai/` | OpenAI SDK | `OPENAI_API_KEY` |
| OpenAI Codex OAuth (gpt-image via Responses image_generation) | `plugins/image_gen/openai-codex/` | Codex OAuth SSE | `hermes auth` |
| xAI (grok-imagine) | `plugins/image_gen/xai/` | xAI HTTP API | `XAI_API_KEY` |
| Krea (2 Large + Medium) | `plugins/image_gen/krea/` | Krea HTTP API | `KREA_API_KEY` |

**Video generation** (`agent/video_gen_registry.py`, `agent/video_gen_provider.py`, tool at `tools/video_generation_tool.py`):
| Backend | Plugin | Models | Env |
|---------|--------|--------|-----|
| FAL.ai | `plugins/video_gen/fal/` | Veo 3.1, Kling, Pixscene (queue API) | `FAL_KEY` |
| xAI | `plugins/video_gen/xai/` | Grok-Imagine (text-to-video, image-to-video, edit, extend) | `XAI_API_KEY` |

**TTS** (`agent/tts_registry.py`, `agent/tts_provider.py`, tool at `tools/tts_tool.py`, lazy deps in `tools/lazy_deps.py`):
- Edge TTS (free, default) — `edge-tts==7.2.7` via `tts.edge`
- ElevenLabs — `elevenlabs==1.59.0` via `tts.elevenlabs`, `ELEVENLABS_API_KEY`
- OpenAI TTS — OpenAI SDK, `OPENAI_API_KEY`
- MiniMax TTS — `MINIMAX_API_KEY`
- Mistral (Voxtral TTS) — `mistralai==2.4.8` via `tts.mistral`, `MISTRAL_API_KEY`
- Google Gemini TTS — Gemini API
- xAI TTS — Grok OAuth or `XAI_API_KEY`
- NeuTTS (local) — `tools/neutts_synth.py`
- KittenTTS (local, 25MB model) — KittentTTS via `tools/tts_tool.py`
- Piper (local, HA-style) — optional
- Opus `.ogg` output for Telegram voice bubbles (`ffmpeg`)

**Speech-to-Text / Transcription** (`agent/transcription_registry.py`, `agent/transcription_provider.py`, tools at `tools/transcription_tools.py`):
- local (`faster-whisper==1.2.1`) — default, free; lazy via `stt.faster_whisper`
- Groq Whisper — `GROQ_API_KEY`, `STT_GROQ_MODEL` (e.g. `whisper-large-v3-turbo`)
- OpenAI Whisper — `STT_OPENAI_MODEL` (whisper-1 / gpt-4o-mini-transcribe / gpt-4o-transcribe)
- Mistral Voxtral — `mistralai==2.4.8` via `stt.mistral`
- ElevenLabs Scribe — `STT_ELEVENLABS_MODEL=scribe_v2`

**Web search + content extraction** (`agent/web_search_registry.py`, `agent/web_search_provider.py`, tool at `tools/web_tools.py`):
| Backend | Plugin | Env | Notes |
|---------|--------|-----|-------|
| Brave (free tier) | `plugins/web/brave_free/` | `BRAVE_SEARCH_API_KEY` | Data-for-Search API |
| DuckDuckGo (ddgs) | `plugins/web/ddgs/` | — (no key) | `pip install ddgs` |
| Exa | `plugins/web/exa/` | `EXA_API_KEY` | `exa-py==2.10.2` |
| Firecrawl | `plugins/web/firecrawl/` | `FIRECRAWL_API_KEY` (or `FIRECRAWL_API_URL` self-host) + Nous gateway routing | `firecrawl-py==4.17.0` |
| Parallel.ai | `plugins/web/parallel/` | `PARALLEL_API_KEY` | `parallel-web==0.4.2` |
| SearXNG | `plugins/web/searxng/` | `SEARXNG_URL` | Self-hosted metasearch |
| Tavily | `plugins/web/tavily/` | `TAVILY_API_KEY` | Search + extract + crawl |
| xAI Web Search | `plugins/web/xai/` | `XAI_API_KEY` / xAI OAuth | Grok agentic web_search via Responses API |

**Browser automation** (`agent/browser_provider.py`, `agent/browser_registry.py`, tool at `tools/browser_tool.py`, supervisor at `tools/browser_supervisor.py`):
| Backend | Plugin | Env | Notes |
|---------|--------|-----|-------|
| Browserbase | `plugins/browser/browserbase/` | `BROWSERBASE_API_KEY` + `BROWSERBASE_PROJECT_ID` | Stealth, proxies, keep-alive |
| Browser Use | `plugins/browser/browser-browser-use/` | `BROWSER_USE_API_KEY` or Nous tool gateway | "Nous Subscription" UX flow |
| Firecrawl | `plugins/browser/firecrawl/` | `FIRECRAWL_API_KEY` | Distinct from web plugin |
| CamoFox (local stealth browser) | `tools/browser_camofox.py` | `CAMOFOX_URL`, `CAMOFOX_USER_ID`, `CAMOFOX_SESSION_KEY` | Local stealth browser |
| Local Playwright | bundled (Dockerfile installs Chromium) | `AGENT_BROWSER_ENGINE=auto`, `AGENT_BROWSER_ARGS=--no-sandbox` | Default; supervisor at `tools/browser_supervisor.py` |

## Data Storage

**Databases:**
- **SQLite** (FTS5 enabled) — session transcripts (`hermes_state.py:SessionDB`), session search (`tools/session_search_tool.py`), Kanban (`hermes_cli/kanban_db.py`), Holographic memory plugin (`plugins/memory/holographic/`). DB file at `$HERMES_HOME/sessions/` and `$HERMES_HOME/kanban/`.
- **Postgres** (optional, Matrix-only) — `asyncpg==0.31.0` pulled by `[matrix]` extra for mautrix state storage.

**File Storage:**
- Local filesystem only by default. `$HERMES_HOME` (default `~/.hermes/`) holds: `config.yaml`, `.env`, `auth.json`, `sessions/`, `cron/`, `kanban/`, `skills/`, `skins/`, `cache/` (incl. `cache/images/` for image-gen outputs), `logs/`.
- Google Drive — via `google-workspace` skill (`skills/productivity/google-workspace/`) using `google-api-python-client==2.194.0`.

**Caching:**
- Anthropic prompt caching — `agent/prompt_caching.py`, TTL configurable via `prompt_caching.cache_ttl: 5m | 1h` in `cli-config.yaml`.
- OpenRouter response caching — `openrouter.response_cache` / `response_cache_ttl` config keys.
- Sticker / media cache — `gateway/sticker_cache.py`.
- Langfuse trace cache — `plugins/observability/langfuse/` (opt-in).

## Authentication & Identity

**Auth Provider:**
- Custom multi-provider token manager at `hermes_cli/auth.py` + `hermes_cli/auth_commands.py`; tokens persisted to `~/.hermes/auth.json`. Per-provider OAuth files in `hermes_cli/copilot_auth.py`, `hermes_cli/dingtalk_auth.py`, `agent/google_oauth.py`, `plugins/spotify/client.py`, `plugins/dashboard_auth/nous/`.
- Credential pool / sources: `agent/credential_pool.py`, `agent/credential_sources.py`, `agent/credential_persistence.py`, `agent/secret_sources/` (multi-key rotation for high-throughput cron / batch).
- Azure Managed Identity / Entra ID: `agent/azure_identity_adapter.py` + `hermes_cli/azure_detect.py`.

**Implementation:** OAuth 2.0 authorization-code + PKCE is the canonical flow for new providers. The Nous dashboard plugin (`plugins/dashboard_auth/nous/`) is the reference implementation.

## Monitoring & Observability

**Error Tracking:**
- Optional Langfuse — `plugins/observability/langfuse/` (`HERMES_LANGFUSE_PUBLIC_KEY`, `HERMES_LANGFUSE_SECRET_KEY`). Hooks `pre_api_request` and `post_api_request`.

**Logs:**
- Python `logging` module; logger setup in `hermes_logging.py`. Session trajectories auto-saved to `$HERMES_HOME/logs/session_<YYYYMMDD>_<HHMMSS>_<uuid>.json` via `agent/trajectory.py`.
- `hermes logs` subcommand at `hermes_cli/logs.py` for tailing.

**Crash / shutdown forensics:**
- `gateway/shutdown_forensics.py` captures exit state; `gateway/memory_monitor.py` tracks RSS growth.

## CI/CD & Deployment

**Hosting:**
- Docker (primary) — `Dockerfile` + `docker-compose.yml` (gateway + dashboard services, s6-overlay supervised). `docker-compose.windows.yml` for Windows hosts.
- Nix flakes — `flake.nix` builds reproducible Linux/macOS packages.
- Native installers — Electron apps via `apps/desktop/` (DMG/ZIP macOS with notarization, NSIS/MSI Windows, AppImage/deb/rpm Linux).
- Termux / Android — supported via `constraints-termux.txt` + `setup-hermes.sh` Termux branch.

**CI Pipeline:**
- GitHub Actions (`.github/workflows/` — referenced from `Dockerfile:204` for `HERMES_GIT_SHA` build-arg). Docker image published to GHCR.
- Test runner: `scripts/run_tests_parallel.py` runs each test file in its own pytest subprocess with a 30s per-test timeout.
- Secrets injected as build-args / env at deploy time (Fly.io platform-secrets for `HERMES_DASHBOARD_OAUTH_CLIENT_ID`).

## Environment Configuration

**Required env vars** (none strictly required — Hermes auto-detects from whatever credentials are present). The most common minimal set:
- One LLM credential: `OPENROUTER_API_KEY` (default aggregator) OR `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` / `GLM_API_KEY` / etc. OR `hermes login` (Nous Portal).
- `HERMES_HOME` (optional; defaults to `~/.hermes`).

**Critical env var groups** (full list at `.env.example` — ~110 vars):
- **LLM provider keys**: `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`/`GEMINI_API_KEY`, `GLM_API_KEY`, `KIMI_API_KEY`/`KIMI_CN_API_KEY`, `MINIMAX_API_KEY`/`MINIMAX_CN_API_KEY`, `NOVITA_API_KEY`, `NVIDIA_API_KEY`, `HF_TOKEN`, `OLLAMA_API_KEY`, `XIAOMI_API_KEY`, `ARCEEAI_API_KEY`, `KILOCODE_API_KEY`, `OPENCODE_ZEN_API_KEY`, `OPENCODE_GO_API_KEY`, `DEEPSEEK_API_KEY`, `STEPFUN_API_KEY`, `GMI_API_KEY`, `DASHSCOPE_API_KEY`, `XAI_API_KEY`, `GITHUB_TOKEN`, `KREA_API_KEY`, `FAL_KEY`.
- **Base URL overrides**: `<PROVIDER>_BASE_URL` for every cloud provider (e.g. `GLM_BASE_URL`, `KIMI_BASE_URL`, `OLLAMA_BASE_URL`, `GROQ_BASE_URL`, `STT_OPENAI_BASE_URL`, `ELEVENLABS_STT_BASE_URL`).
- **Web / search**: `EXA_API_KEY`, `PARALLEL_API_KEY`, `FIRECRAWL_API_KEY` (+ `FIRECRAWL_API_URL` / `FIRECRAWL_GATEWAY_URL`), `TAVILY_API_KEY`, `BRAVE_SEARCH_API_KEY`, `SEARXNG_URL`.
- **Browser**: `BROWSERBASE_API_KEY` + `BROWSERBASE_PROJECT_ID`, `BROWSER_USE_API_KEY`, `AGENT_BROWSER_ENGINE`, `AGENT_BROWSER_ARGS`, `CAMOFOX_URL`/`CAMOFOX_USER_ID`/`CAMOFOX_SESSION_KEY`/`CAMOFOX_ADOPT_EXISTING_TAB`.
- **Image / video**: `FAL_KEY`, `KREA_API_KEY`, `XAI_API_KEY`, `OPENAI_API_KEY`.
- **TTS / STT**: `ELEVENLABS_API_KEY`, `GROQ_API_KEY`, `MISTRAL_API_KEY`, `VOICE_TOOLS_OPENAI_KEY`.
- **Terminal sandbox**: `TERMINAL_ENV` (local | docker | ssh | singularity | modal | daytona), `TERMINAL_CWD`, `TERMINAL_DOCKER_IMAGE`, `TERMINAL_SINGULARITY_IMAGE`, `TERMINAL_SSH_HOST`/`USER`/`PORT`/`KEY`, `HERMES_DOCKER_BINARY` (podman alternative), `SUDO_PASSWORD`.
- **Gateway platforms**: `TELEGRAM_BOT_TOKEN` + `TELEGRAM_ALLOWED_USERS` (+ optional `TELEGRAM_HOME_CHANNEL`, `TELEGRAM_WEBHOOK_*`), `SLACK_BOT_TOKEN` + `SLACK_APP_TOKEN`, `DISCORD_TOKEN`/`DISCORD_ALLOWED_USERS`, `WHATSAPP_ENABLED` + `WHATSAPP_ALLOWED_USERS`, `EMAIL_ADDRESS` + `EMAIL_PASSWORD` + IMAP/SMTP hosts/ports + `EMAIL_ALLOWED_USERS`, `MATRIX_HOMESERVER` + `MATRIX_ACCESS_TOKEN` (or `MATRIX_USER_ID`+`MATRIX_PASSWORD`) + `MATRIX_ENCRYPTION`, `TEAMS_CLIENT_ID` + `TEAMS_CLIENT_SECRET` + `TEAMS_TENANT_ID` + `TEAMS_ALLOWED_USERS`, `GOOGLE_CHAT_PROJECT_ID` + `GOOGLE_CHAT_SUBSCRIPTION_NAME` + `GOOGLE_CHAT_SERVICE_ACCOUNT_JSON`, `GOOGLE_CHAT_ALLOWED_USERS`.
- **Memory**: `HONCHO_API_KEY`, `RETAINDB_API_KEY`, `OPENVIKING_ENDPOINT`, `HERMES_LANGFUSE_PUBLIC_KEY`/`SECRET_KEY`.
- **Cron / dashboard**: `HERMES_DASHBOARD_OAUTH_CLIENT_ID`, `HERMES_DASHBOARD_PORTAL_URL`, `HERMES_DASHBOARD_PUBLIC_URL`, `API_SERVER_KEY` + `API_SERVER_HOST` (gateway OpenAI-compat API).
- **Hyperliquid** (finance skill): `HYPERLIQUID_API_URL`, `HYPERLIQUID_USER_ADDRESS`.

**Secrets location:**
- `~/.hermes/.env` (from `.env.example`) — API keys, bot tokens.
- `~/.hermes/auth.json` — OAuth tokens (Google, Copilot, Spotify, Nous Portal, MiniMax OAuth, Qwen OAuth).
- `~/.hermes/.shell-hooks-allowlist.json` — first-use consent for shell-script hooks.
- Docker: build-args + `~/.hermes` volume mount.
- Never commit secrets: `pyproject.toml` policy bans `[all]` from including any provider SDK that could pull a quarantined release.

## Webhooks & Callbacks

**Incoming:**
- `gateway/platforms/api_server.py` — optional OpenAI-compatible HTTP API on the gateway (auth via `API_SERVER_KEY`, host via `API_SERVER_HOST`).
- `gateway/platforms/webhook.py` — generic webhook receiver for platforms that require a public URL.
- Telegram webhook: `TELEGRAM_WEBHOOK_URL` + `TELEGRAM_WEBHOOK_PORT` + `TELEGRAM_WEBHOOK_SECRET` (alternative to long-polling).
- LINE Messaging API: HMAC-SHA256 verified webhook server (in `plugins/platforms/line/`).
- Google Chat: Cloud Pub/Sub pull subscription (no public URL needed).
- MS Graph webhook: `gateway/platforms/msgraph_webhook.py`.
- WeCom callback: `gateway/platforms/wecom_callback.py` (XML POST + AES).
- Email: IMAP polling (`gateway/platforms/email.py`); Home Assistant: webhook poll (`gateway/platforms/homeassistant.py`).
- Dashboard OAuth callback: `<dashboard>/auth/callback`.

**Outgoing:**
- LLM API calls to whichever provider is configured.
- MCP client → MCP server (stdio subprocess or Streamable HTTP — see `optional-mcps/linear/manifest.yaml`).
- Browser, image, video, TTS, STT, search HTTP calls to the configured backend.
- Webhook POSTs to ntfy, Discord, Mattermost, etc. when cron / notifications fire.
- Skills Hub: GitHub App API (`PyJWT[crypto]` signed JWT) for skill publishing.

---

*Integration audit: 2026-06-14*
