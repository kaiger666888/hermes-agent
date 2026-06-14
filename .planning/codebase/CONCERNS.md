# Codebase Concerns

**Analysis Date:** 2026-06-14

This document captures actionable warnings about Hermes Agent (`main` branch @ `4290ab2`, v0.15.1 release tag). It is focused on what to watch out for when making changes — file paths are load-bearing for planning.

---

## Tech Debt

### Oversized single-file dispatch hubs (refactor candidates)

**`gateway/run.py` (~19,348 lines / ~913 KB):**
- Issue: One file owns the entire gateway daemon — 35 top-level imports, 268 `def`/`class`/`async def` definitions. Mixes runner lifecycle, platform dispatch, session store, agent cache (`_agent_cache_lock` referenced in 10+ sites), stream consumer glue, slash-command routing, SQLite session persistence, status / pairing / memory monitor wiring.
- Why it grew: Ad-hoc extraction of helper modules (`gateway/session.py`, `gateway/stream_consumer.py`, `gateway/status.py`, `gateway/platform_registry.py`) left the runner body intact. Comments throughout the file reference "out of scope to move here" — refactor was deferred.
- Impact: Test patches target `gateway.run.<symbol>` as module attributes (see top-of-file comment about preserving test surface), so any extraction must preserve re-exports. Conflict surface for parallel work is enormous — every gateway touch edits this file.
- Fix approach: Continue the established extraction pattern. Logical next slices: (1) agent-cache management (`_enforce_agent_cache_cap`, `_session_expiry_watcher`, all `_agent_cache_lock` sites) into `gateway/agent_cache.py`; (2) slash-command routing into `gateway/slash_commands.py`; (3) platform dispatch fall-through into `platform_registry.create_adapter` only. Each extraction must re-export the moved symbols via `from gateway.<new> import *` shim so existing `mock.patch("gateway.run.<X>")` keeps working.

**`agent/conversation_loop.py` (~4,707 lines / ~262 KB):**
- Issue: Single `run_conversation()` body covering model call, tool dispatch, retries, fallbacks, compression triggers, post-turn hooks, background memory/skill review nudges. Only 11 top-level `def`/`class` declarations — most logic is inside the one giant function. Comments throughout (`agent/conversation_loop.py:796`, `:812`, `:1502`, `:2587`, `:2820`, `:3258`, `:4165`, `:4282`) describe retry-trace buffering and terminal-flush logic interleaved across thousands of lines.
- Why it grew: Extracted from `run_agent.py` as the "biggest single chunk" per the module header. The function takes the parent `AIAgent` instance and accesses its state via attribute lookup, so further factoring requires breaking up state.
- Impact: Any change to retry policy, fallback chains, or trace buffering requires understanding the full control flow. Hard to unit test — `tests/run_agent/test_run_agent.py` (84 skip markers — top of test-skip leaderboard) and `tests/run_agent/test_streaming.py` (68 skips) cover this surface.
- Fix approach: Extract the retry/fallback state machine into a `RetryController` class with discrete methods (`should_retry`, `flush_trace`, `surface_terminal_error`). Keep `run_conversation()` as the orchestrator. Tests can then patch the controller.

**`agent/auxiliary_client.py` (~5,662 lines / ~249 KB, 145 top-level definitions):**
- Issue: Houses every "call a cheap/fast model for side work" path — compression, title generation, hindsight, background review, classification. Mixes client construction, request shaping, error classification, retries, and feature-specific call sites.
- Why it grew: Each auxiliary-model use case (compression, title, hindsight, ...) was bolted on without an abstraction boundary.
- Impact: Any change to retry policy or auth for one auxiliary path affects every other. `tests/agent/test_auxiliary_client.py` carries 32 skip markers indicating fragile coverage.
- Fix approach: Split into `agent/auxiliary/<feature>.py` modules sharing a common `AuxiliaryClient` base. Preserve `auxiliary_client.<symbol>` re-exports.

**`hermes_cli/main.py` (~14,910 lines / ~579 KB, 218 top-level definitions):**
- Issue: The `hermes` CLI entry point. Module docstring lists 30+ subcommands spanning chat, gateway lifecycle, setup, doctor, cron, honcho, sessions, acp, update, uninstall, claw migrate. Mixes subcommand dispatch, interactive REPL, TUI/PTY wiring, dashboard launch, plugin manager startup.
- Why it grew: New CLI subcommands accumulate as top-level functions. `hermes_cli/commands.py` exists as a partial extraction but most subcommand bodies still live in `main.py`.
- Fix approach: Continue migrating subcommands to dedicated modules under `hermes_cli/` (e.g. `hermes_cli/kanban.py`, `hermes_cli/backup.py` already exist as 111 KB / 36 KB modules — apply same pattern to remaining inline subcommands).

**`run_agent.py` (~4,816 lines / ~213 KB, top-level `AIAgent` class):**
- Issue: The original monolith. `agent/conversation_loop.py`, `agent/message_sanitization.py`, `agent/conversation_compression.py`, `agent/auxiliary_client.py`, etc. were extracted from this file but it remains the coordinator. Header notes that `OpenAI` is re-exported as a thin lazy proxy specifically so `patch("run_agent.OpenAI", ...)` in ~28 test files keeps working.
- Why it grew: Historical — the agent was originally one file. Extraction is in progress.
- Impact: New contributors land changes here by default rather than the more focused modules.
- Fix approach: Continue extracting cohesive responsibilities to `agent/` modules; `run_agent.py` should shrink to class wiring and re-export shims.

**Other oversized files (refactor tier-2):**
- `hermes_cli/config.py` (~5,984 lines / ~264 KB)
- `cli.py` (~15,609 lines / ~711 KB) — separate Fire-based CLI entry, not `hermes` CLI
- `hermes_cli/auth.py` (~7,666 lines / ~303 KB) — owns `PROVIDER_REGISTRY`, OAuth flows for nous/codex/xai/qwen/minimax
- `hermes_cli/web_server.py` (~6,232 lines / ~242 KB) — dashboard backend
- `hermes_cli/gateway.py` (~6,468 lines / ~250 KB) — gateway service controller (separate from `gateway/run.py`)
- `hermes_cli/kanban_db.py` (~7,441 lines / ~301 KB) — SQLite-backed kanban store
- `hermes_state.py` (~3,697 lines / ~158 KB) — SQLite session/trajectory store
- `gateway/config.py` (~2,290 lines / ~95 KB)
- `hermes_cli/setup.py` (~3,298 lines / ~134 KB)

### Lazy import proxy preserves test patch surface

**`run_agent.OpenAI` lazy proxy pattern:**
- Issue: `run_agent.py` exposes `OpenAI` as a thin proxy imported from `agent.process_bootstrap` purely so `mock.patch("run_agent.OpenAI", ...)` in ~28 test files keeps working. Comment at `run_agent.py:64-76` documents the constraint explicitly.
- Why: Avoid rewriting test surface during extraction.
- Impact: Couples module layout to test patches; refactoring `run_agent.py` requires auditing every `# noqa: F401` re-export.
- Fix approach: Migrate the ~28 test files to patch the actual import sites (e.g. `patch("agent.process_bootstrap.OpenAI")`), then drop the re-exports.

### `cli.py` parallel CLI surface

**Duplicate entry point `cli.py` (~15,609 lines / ~711 KB):**
- Issue: The repo ships two top-level CLIs: `hermes` (from `hermes_cli/main.py`) and a Fire-based CLI in `cli.py`. Many functions are duplicated or re-exported.
- Why: Historical migration from Fire to Rich/Click-style CLI in `hermes_cli/`; `cli.py` retained for back-compat.
- Impact: Bug fixes must land in both surfaces. Confusing for contributors.
- Fix approach: Document which CLI is canonical (likely `hermes`) and mark `cli.py` as deprecated in its module docstring with a migration table.

---

## Known Bugs / Recently Fixed Issues

### v0.15.1 hotfixes (still relevant context)

These landed in the v0.15.1 patch release (`RELEASE_v0.15.1.md`) and indicate areas that were fragile in v0.15.0. If you touch these subsystems, read the original PRs first.

**Dashboard 401 reload loop (fixed `#30698`):**
- Symptoms: In loopback mode, `/api/auth/me` returns 401 by design; v0.15.0's stale-token reload guard treated every 401 as a rotated session token and full-page-reloaded forever. Firefox "Navigated to /sessions" storm; Chrome React re-render storm.
- Trigger: Docker, hosted Hermes, fresh installs running v0.15.0 in loopback mode.
- Fix: `fetchJSON` gained an `allowUnauthorized` opt-out. 401 still throws (so `AuthWidget` swallows it) but the one-shot reload guard is skipped in loopback mode.
- Implication for future work: Any code that adds new fetch callers in the dashboard must decide whether to pass `allowUnauthorized`. The pattern is now load-bearing.

**Docker `--insecure` was inferred from bind host (fixed `#34188`, `#34204`):**
- Symptoms: Docker entrypoint conflated "I want LAN access" with "I want to disable the same-origin guard."
- Trigger: Binding the dashboard to a non-loopback host under v0.15.0.
- Fix: `HERMES_DASHBOARD_INSECURE=1` is now an explicit env opt-in. Existing setups that wanted insecure binding must now set the env var.
- Implication: Document this in any deployment guide; if you add new "insecure" code paths, model them on this opt-in pattern.

**MCP bare-command resolution under Docker (fixed `#34186`):**
- Symptoms: MCP servers configured with bare commands (`npx`, `npm`, `node`) failed silently in Docker containers because the agent's effective PATH didn't include `/usr/local/bin`.
- Fix: Bare commands now resolve against `/usr/local/bin` when running inside the Docker image.
- Implication: Container-local MCP server paths are now a documented surface; if you add a new MCP launch path, mirror the resolution logic.

**`.md` files delivery was blocked by gateway allowlist (fixed `#34022`):**
- Symptoms: Gateway media delivery rejected `.md` attachments.
- Fix: Validation defaults to denylist-only instead of an overly-narrow allowlist.
- Implication: When extending the media-delivery surface, prefer denylists over allowlists.

**Probe stepdown to smaller model on context overflow without explicit provider limit (fixed `#33826`):**
- Symptoms: On context-overflow without an explicit provider context limit, the agent stepped down to a smaller model based on an unknown ceiling.
- Fix: No stepdown without an explicit limit.
- Implication: Anywhere you wire a "stepdown on overflow" path, require an explicit limit check first.

**Redactor ate web URL query parameters that looked credential-shaped (fixed `#34029`):**
- Symptoms: Redactor in `agent/redact.py` was stripping URL query parameters that matched sensitive-key heuristics even on plain web URLs.
- Fix: Web URLs pass through unchanged.
- Implication: `agent/redact.py` is an active bug surface. New patterns must distinguish URL query params from in-body credentials. See "Security Considerations" below.

**Kanban worker SIGTERM absorbed by intermediate process (fixed `#34045`):**
- Symptoms: `SIGTERM` on a kanban worker was absorbed by an intermediate process and the worker stayed running.
- Implication: Any code that spawns worker subprocesses must propagate signals correctly. See `hermes_cli/kanban.py` / `hermes_cli/kanban_db.py` (kanban_db.py is ~7,441 lines).

### Reverted fix

**`cd8aa38` — Revert "fix(tui): clamp bogus terminal dimensions (WSL 131072x1) (#35657)":**
- The clamp logic in `ui-tui/src/lib/terminalDimensions.ts` was reverted in commit `cd8aa38` (2026-05-31). If you see terminal-dimension handling in the TUI surface, do NOT re-introduce clamp logic without understanding why the original fix was reverted. Affected files were `ui-tui/src/lib/terminalDimensions.ts`, `ui-tui/src/entry.tsx`, and `ui-tui/src/__tests__/terminalDimensions.test.ts` (all deleted by the revert).

### Recent fix commits on `main` (post-v0.15.1)

These are the latest fixes already on `main`. Read the linked commits before touching the same surface:

- `eb3cf97 fix(gateway): resolve _get_dm_topic_info on adapter class, not instance`
- `4259bab fix(gateway): preserve Telegram DM topic routing metadata in synthetic notifications`
- `6f8975d fix(tools): don't compound-rewrite spawn_via_env background wrappers`
- `7a315bd fix(tools): preserve live session cwd in terminal_tool, and keep ACP update_cwd authoritative`
- `1044d9f fix(gateway): /stop can interrupt a sibling participant's run in a per-user thread (#35959)`
- `a726e8a fix(tui): auto-recover session on unexpected gateway death (+ persist lifecycle breadcrumbs) (#35893)`
- `fa4ebaa fix(install): build desktop in 'desktop' stage on macOS/Linux instead of silently skipping (#36134)`
- `77bb648 fix(desktop): report desktop_contract in lazy session.create info (#36112)`
- `3ef97a6 fix(desktop): track main for self-update now that GUI merged (#36104)`

The recent commit cadence on gateway/Telegram DM routing and `spawn_via_env` background wrappers suggests the gateway subprocess-spawn surface is currently fragile.

### `test-results.md` (untracked, repo root)

`test-results.md` (untracked, dated 2026-06-01 GMT+8) is a manual E2E integration report from a downstream integration with a "Worker Agent" and 14 movie-expert skills + GLM-5.1. It is NOT a Hermes Agent core test artifact — it documents a separate downstream integration. One notable observation: `--no-stream` is no longer a valid flag in v0.15.1 (the test marks this as a non-blocking API change). Anyone documenting CLI flags should update accordingly.

---

## Security Considerations

Hermes Agent's security posture is documented authoritatively in `SECURITY.md`. The single load-bearing security boundary is **OS-level isolation** (terminal-backend sandbox or whole-process wrapping). Everything inside the agent process — approval gates, redaction, allowlists — is an in-process heuristic, NOT a boundary. This drives every recommendation below.

### Secret handling — credential pool

**Files:** `agent/credential_pool.py` (~2,400 lines), `agent/credential_sources.py`, `agent/credential_persistence.py`, `agent/secret_sources/bitwarden.py`, `hermes_cli/auth.py` (owns `PROVIDER_REGISTRY`).

- Risk: The credential pool reads from many heterogeneous sources (`env:`, `claude_code`, `hermes_pkce`, `device_code`, `qwen-cli`, `gh_cli`, `config:`, `model_config`, `manual`). Each source has a removal contract registered in `agent/credential_sources.py` to ensure `hermes auth remove` actually persists across `load_pool()` calls. A new source that forgets to register a `RemovalStep` will silently reappear on next pool load — historically this happened for qwen-cli, nous device_code (partial), hermes_pkce, copilot gh_cli, and custom-config sources.
- Current mitigation: `agent/credential_sources.py` unifies the removal contract; new sources must register a `RemovalStep`. `agent/credential_persistence.py` defines `_PERSISTABLE_PROVIDER_SOURCES` — a closed allowlist of `(provider, source_id)` pairs that may persist raw values in `auth.json`. Everything else is treated as borrowed/reference-only and stripped at the disk boundary (fail-closed for future external secret providers).
- Recommendations:
  - When adding a new credential source, register both a `_seed_from_*` reader in `credential_pool.py` AND a `RemovalStep` in `credential_sources.py`. Add the `(provider, source_id)` tuple to `_PERSISTABLE_PROVIDER_SOURCES` only if Hermes owns the source.
  - `_TERMINAL_AUTH_REASONS` in `credential_pool.py` (token_invalidated, token_revoked, invalid_token, invalid_grant, unauthorized_client, refresh_token_reused) defines unrecoverable failure modes — extend this set when a new OAuth provider adds new terminal error reasons, otherwise DEAD credentials will be retried pointlessly.
  - Multi-process refresh race comments are scattered throughout (`credential_pool.py:981`, `:1049`) — two Hermes processes can race on xai-oauth / openai-codex / nous token refresh. The mitigation is `refresh_token_reused` detection but the race itself is acknowledged as known.

### Bitwarden secret source

**Files:** `agent/secret_sources/bitwarden.py`, `agent/secret_sources/__init__.py`.

- Risk: Auto-installs the `bws` binary into `<hermes_home>/bin/bws` from GitHub Releases. The download is verified against the release's published SHA-256 checksum file. Failures never block Hermes startup (warning + continue with `.env`).
- Current mitigation: Pinned version (`_BWS_VERSION`), SHA-256 verification, subprocess-driven (not a Rust-extension wheel), access token stored in `.env` as the one bootstrap secret.
- Recommendations:
  - Treat the pinned `_BWS_VERSION` as load-bearing — bumping it requires re-verifying checksums.
  - The fail-open-on-startup behavior is intentional but means a misconfigured Bitwarden integration silently falls back to whatever `.env` had. Surface this loudly in onboarding.

### Regex-based secret redaction

**Files:** `agent/redact.py` (~480 lines), `agent/message_sanitization.py`.

- Risk: Per `SECURITY.md` §2.4, redaction is a heuristic over attacker-influenced strings, NOT a boundary. A motivated output producer will defeat it. v0.15.1 fixed a regression where the redactor was eating URL query parameters that looked credential-shaped (`#34029`).
- Current mitigation: `_SENSITIVE_QUERY_PARAMS` and `_SENSITIVE_BODY_KEYS` are exact-match frozensets (case-insensitive), ported from `nearai/ironclaw#2529`. Body keys use exact match specifically so `token_count` and `session_id` do NOT match. Short tokens (<18 chars) fully masked; longer tokens preserve first 6 / last 4 for debuggability.
- Recommendations:
  - Do NOT weaken exact-match semantics on body keys — substring matching would over-redact.
  - When adding a new sensitive parameter name, append to BOTH `_SENSITIVE_QUERY_PARAMS` and `_SENSITIVE_BODY_KEYS` if the parameter can appear in either location.
  - Any new redaction pattern must have a regression test — see `tests/test_evidence_store.py`, `tests/test_sql_injection.py` for the established pattern.

### File-write safety

**Files:** `agent/file_safety.py` (~440 lines).

- Risk: The agent must not write to sensitive host paths (`~/.ssh/authorized_keys`, `~/.ssh/id_rsa`, `.env`, `.anthropic_oauth.json`, shell rc files, `.netrc`, `.pgpass`, `.npmrc`, `.pypirc`, `.git-credentials`, `/etc/sudoers`, `/etc/passwd`, `/etc/shadow`) or sensitive directory prefixes (`~/.ssh`, `~/.aws`, `~/.gnupg`, `~/.kube`, `~/.docker`, `~/.azure`, `~/.config/gh`, `~/.config/gcloud`). v0.15.1 hardened profile-aware path resolution (`#15981`): top-level `.env` and `.anthropic_oauth.json` remain protected even when a profile is active.
- Current mitigation: `build_write_denied_paths(home)` and `build_write_denied_prefixes(home)` produce exact-match and prefix sets using `os.path.realpath` to defend against symlinks.
- Recommendations:
  - When adding a new file-write tool or ACP shim, route through `agent/file_safety.py` helpers — do NOT inline your own path check.
  - When extending the denied paths/prefixes, prefer exact-match over substring; resolve through `os.path.realpath`.

### Gateway allowlist enforcement

**Files:** `gateway/platforms/base.py`, `gateway/platforms/msgraph_webhook.py`, `gateway/platforms/wecom.py`, `gateway/platforms/weixin.py`, etc.

- Risk: Per `SECURITY.md` §2.6, every network-exposed adapter MUST refuse to dispatch agent work until an allowlist is configured. Code paths that fail open when no allowlist is set are security bugs in scope under §3.1.
- Current mitigation: `msgraph_webhook.py:136` implements `_source_allowlist_required_but_missing()` and refuses dispatch. `wecom.py`, `weixin.py`, `dingtalk.py` enforce `dm_policy == "allowlist"`. `telegram.py:1655` documents the "fail loudly at start rather than silently run in fail-open mode" stance.
- Recommendations:
  - When adding a new gateway platform adapter, mirror `msgraph_webhook.py`'s `_source_allowlist_required_but_missing()` pattern. Default policy must be "refuse" not "open".
  - `gateway/run.py:1817` has an explicit `pass  # Non-fatal — fail-open at scan time if unavailable` comment. This is intentional (scan-time vs dispatch-time) but is a fragile distinction. Any new fail-open MUST justify why it is scan-time only.

### `tirith_fail_open` config toggle

**Files:** `hermes_cli/config.py:1744`, `hermes_cli/config.py:4878`, `hermes_cli/tips.py:466-467`.

- Risk: Tirith scanner has a `tirith_fail_open` config (default `True`) and a `TIRITH_FAIL_OPEN` env override. When True, Hermes allows commands when the tirith scanner itself errors out. When False, Hermes blocks.
- Current mitigation: Documented in tips. Operator can flip the toggle.
- Recommendations: Treat the default as a UX tradeoff, not a security boundary (per SECURITY.md §2.4 — in-process pattern scanners are not boundaries). When in doubt, leave the default and surface the toggle prominently in `hermes doctor`.

### Skills Guard and plugin trust

**Files:** `SECURITY.md` §2.4 / §2.5, `hermes_cli/plugins.py` (~1,846 lines), `agent/skill_*` modules.

- Risk: Skills execute arbitrary Python at import time. Plugins load into the agent process with full agent privileges. The boundary is operator review before install, NOT a runtime sandbox.
- Current mitigation: Skills Guard scans installable skill content for injection patterns (a review aid, not a boundary). Plugin manifests in `plugins/<name>/plugin.yaml` declare `kind`, `version`, `author` — but these are not trusted without operator review.
- Recommendations:
  - Document for plugin/skill authors that their code runs with full agent privileges.
  - Any change to plugin-install or skill-install paths that prevents the operator from seeing what they're installing IS in scope under SECURITY.md §3.1 — file as security bug.

---

## Performance Bottlenecks

### Gateway dispatch hub startup

**File:** `gateway/run.py`.
- Problem: Module-level imports pull the OpenAI SDK chain (~230 ms) eagerly per the comment at `gateway/run.py:18-25` (justified by test patches that target `gateway.run.fetch_account_usage` as a module-level attribute).
- Cause: Test-patch surface compatibility forces eager imports in a long-running daemon.
- Improvement path: Once tests are migrated to patch the actual source module, drop the eager import. The gateway is a daemon so boot cost is amortized, but cold-restart speed matters for `--no-supervise` failure-restart loops.

### Per-session AIAgent cache eviction

**File:** `gateway/run.py` (constants at lines 27-29: `_AGENT_CACHE_MAX_SIZE = 128`, `_AGENT_CACHE_IDLE_TTL_SECS = 3600.0`).
- Problem: Each `AIAgent` holds LLM clients, tool schemas, and memory providers — non-trivial memory. The LRU + idle TTL eviction (`_enforce_agent_cache_cap()`, `_session_expiry_watcher()`) bounds the cache at 128 entries / 1h idle.
- Cause: Long-lived gateways accumulate sessions.
- Improvement path: The 128 / 1h values are constants — operators with very high session churn may need to tune. Consider exposing via config.

### Context compression pipeline

**Files:** `agent/context_compressor.py` (~2,078 lines / ~97 KB), `agent/conversation_compression.py` (~755 lines), `trajectory_compressor.py` (~1,508 lines / ~65 KB), `agent/auxiliary_client.py`.

- Problem: Context compaction requires a full auxiliary-LLM round-trip to summarize middle turns. The summarizer input includes tool output pruning, scaled summary budget proportional to compressed content, and iterative summary updates that preserve info across multiple compactions.
- Cause: Compression is on the critical path of every long conversation. `agent/conversation_compression.py:359` notes that one failure mode is NOT a `sqlite3.Error` so the method's own fail-open guard never triggers.
- Improvement path: Pre-pass tool-output pruning (cheap) before LLM summarization (expensive) is already in place — extend pruning before invoking the summarizer. Profile `compress_context` end-to-end; the summary template and Resolved/Pending question tracking add prompt tokens.

### Token estimation

**Files:** `agent/model_metadata.py` (~77 KB / 1,900+ lines).

- Problem: `estimate_messages_tokens_rough` and `estimate_request_tokens_rough` are called throughout the loop to decide when to compress. They are heuristics ("rough").
- Cause: Real tokenization would require the model's tokenizer; rough estimates avoid per-provider tokenizer dependencies.
- Improvement path: Document the error band of the rough estimator; compression thresholds should account for it. If a provider exposes a cheap token-count endpoint, prefer it for the threshold check.

### Provider failover fan-out

**Files:** `agent/credential_pool.py`, `hermes_cli/runtime_provider.py`.

- Problem: The credential pool supports strategies `fill_first`, `round_robin`, `random`, `least_used` (see constants at top of `credential_pool.py`). Failover across multiple credentials for the same provider is built in but each failover is a network call to a freshly-selected credential.
- Cause: Multi-credential pools exist precisely for failover.
- Improvement path: Pre-warm health checks; track per-credential `last_status` / `last_error_code` (already in `_SAFE_SECRETISH_METADATA_KEYS`) and skip known-DEAD credentials proactively (already done via `STATUS_DEAD`).

---

## Fragile Areas

### Multi-provider adapter drift

**Files:** `agent/anthropic_adapter.py` (2,303 lines), `agent/codex_responses_adapter.py` (1,260 lines), `agent/bedrock_adapter.py` (1,277 lines), `agent/gemini_native_adapter.py` (971 lines), `agent/gemini_cloudcode_adapter.py` (909 lines), plus 29 entries in `plugins/model-providers/`.

- Why fragile: Each provider has its own adapter with its own request shaping, response parsing, error classification, and tool-call format. The adapters are not subclasses of a common base — they share patterns by convention, not by inheritance. Drift is structural.
- Common failures: A new provider capability (e.g. a new tool-call ID format) lands in one adapter and not the others. Provider-specific error codes that should map to `_TERMINAL_AUTH_REASONS` are missed.
- Safe modification: Before changing one adapter, grep the others for the same pattern. `agent/error_classifier.py` (`FailoverReason`, `classify_api_error`) is the shared error surface — extend there when adding a new error mapping.
- Test coverage: Provider-specific tests live under `tests/agent/`, `tests/providers/`, and `tests/plugins/`. Coverage is uneven across the 29 providers.

### Multi-runtime support (chat_completions / codex_app_server / claude_code / opencode / gemini CLI)

**Files:** `hermes_cli/runtime_provider.py`, `agent/codex_runtime.py`, `agent/codex_responses_adapter.py`, `agent/copilot_acp_client.py`, `hermes_cli/codex_runtime_switch.py`, `hermes_cli/codex_runtime_plugin_migration.py`, `agent/agent_runtime_helpers.py`.

- Why fragile: The `model.openai_runtime` config toggles between `auto` (= chat_completions, Hermes' default) and `codex_app_server` (= hand turns to a codex subprocess). `runtime_provider.py:_maybe_apply_codex_app_server_runtime()` reads the persisted config value and resolves credentials per-runtime. Each runtime has its own auth surface (`resolve_codex_runtime_credentials`, `resolve_xai_oauth_runtime_credentials`, `resolve_qwen_runtime_credentials`, `resolve_gemini_oauth_runtime_credentials`, `resolve_external_process_provider_credentials` in `hermes_cli/auth.py`).
- Common failures: A change to one runtime's auth path breaks callers that haven't been migrated. The `codex_runtime_plugin_migration.py` module (31 KB) exists specifically to migrate users between runtime modes — implying the migration surface is non-trivial.
- Safe modification: When touching any runtime's auth resolution, check whether `runtime_provider.py` calls into it and whether the codex-runtime switch surfaces it via `CodexRuntimeStatus.requires_new_session`.
- Test coverage: `tests/hermes_cli/test_codex_runtime_plugin_migration.py` has 30 skip markers — fragile.

### ACP integration

**Files:** `acp_adapter/server.py` (1,952 lines, 59 definitions), `acp_adapter/tools.py` (1,291 lines), `acp_adapter/session.py` (628 lines), `acp_adapter/entry.py`, `acp_adapter/edit_approval.py`, `acp_adapter/permissions.py`, `agent/copilot_acp_client.py` (686 lines).

- Why fragile: The ACP server exposes Hermes via the Agent Client Protocol — pinned to `agent-client-protocol==0.9.0` in `pyproject.toml:132`. The schema is imported from `acp.schema` (InitializeResponse, NewSessionResponse, LoadSessionResponse, ForkSessionResponse, etc.). A schema bump in the `acp` package can break the adapter silently.
- Common failures: `7a315bd fix(tools): preserve live session cwd in terminal_tool, and keep ACP update_cwd authoritative` is a recent fix where ACP and non-ACP surfaces disagreed on cwd authority. Any new tool or state mutation that doesn't go through ACP's session model can desync the editor view.
- Safe modification: When adding a tool, register it in `acp_adapter/tools.py` AND the agent's tool registry. When changing session state, ensure `acp_adapter/session.py` observes the change.
- Test coverage: `tests/acp_adapter/` and `tests/acp/` exist. Pinned `acp` version is load-bearing — do not bump without integration testing.

### Conversation loop retry/fallback state machine

**File:** `agent/conversation_loop.py` (~4,707 lines).
- Why fragile: The retry trace is buffered throughout the loop and flushed only on terminal states (lines `:1502`, `:2587`, `:2820`, `:3258`, `:4165`, `:4282`). Grace-call logic (`:812-816`) consumes a one-shot flag. Iteration budget interacts with `max_iterations` and `iteration_budget.remaining` (`:796`).
- Common failures: A change to one flush point that misses another leaves the user without retry context. Adding a new retry reason without updating the trace buffer leaves it invisible.
- Safe modification: Audit every place that surfaces "Terminal" in comments before changing retry policy. Read `agent/error_classifier.py` to understand which reasons are terminal vs. retriable.
- Test coverage: `tests/run_agent/test_run_agent.py` has 84 skip markers and `tests/run_agent/test_streaming.py` has 68 — the most fragile test surface in the repo.

### Context compression SQLite split

**Files:** `agent/conversation_compression.py`, `hermes_state.py` (~3,697 lines).

- Why fragile: `compress_context` splits the SQLite session, rotates the session_id, notifies plugin context engines / memory providers, and rebuilds the system prompt. `agent/conversation_compression.py:359` notes that one failure mode is NOT a `sqlite3.Error` so the method's own fail-open guard never triggers. `tests/test_hermes_state_compression_locks.py` and `tests/test_hermes_state_wal_fallback.py` exist specifically for this surface — implying known lock and WAL-fallback fragility.
- Common failures: Concurrent compression and tool execution on the same session. WAL fallback edge cases.
- Safe modification: Read the WAL fallback test before changing session store internals.

### `spawn_via_env` background wrappers

**Files:** Recent commits `6f8975d`, `59cc7c3` ("fix(tools): don't compound-rewrite spawn_via_env background wrappers") suggest the terminal tool's subprocess-spawn-via-env wrapper is currently fragile.

- Why fragile: Background-wrapper shell escaping compounds across rewrites; a fix landed recently.
- Safe modification: Read commit `6f8975d` before touching `tools/terminal_tool` or any code that rewrites shell commands for subprocess invocation.

---

## Scaling Limits

### Per-session AIAgent cache

**File:** `gateway/run.py:27-29`.
- Current capacity: 128 concurrent sessions per gateway process, 1h idle TTL.
- Limit: High-churn deployments (many short sessions) will thrash the LRU.
- Symptoms at limit: Re-creating an AIAgent is expensive (LLM clients, tool schemas, memory providers per `gateway/run.py:18-25`).
- Scaling path: Tune `_AGENT_CACHE_MAX_SIZE` / `_AGENT_CACHE_IDLE_TTL_SECS` via config; consider sharding across gateway processes.

### SQLite session store

**Files:** `hermes_state.py`, `hermes_cli/kanban_db.py`.
- Current capacity: Single SQLite file per profile. WAL mode enabled.
- Limit: SQLite is single-writer. Concurrent writes serialize.
- Symptoms at limit: `database is locked` errors. WAL fallback exists (`tests/test_hermes_state_wal_fallback.py`).
- Scaling path: For kanban specifically, `hermes_cli/kanban_db.py:3336` documents its own failure-counter clearing semantics — kanban has tighter write patterns than the session store. For high-throughput, consider per-session SQLite files or Postgres backend.

### Gateway platform fan-out

**Files:** `gateway/platforms/` (16 built-in adapters), `plugins/platforms/` (8 plugin adapters).
- Current capacity: All configured adapters run concurrently in one gateway process.
- Limit: Long-running platform connections (Telegram long-poll, Slack RTM, Matrix sync) each hold an event-loop task. Asyncio event-loop contention under high message volume.
- Symptoms at limit: Message latency spikes during bursts.
- Scaling path: Run multiple gateway processes with platform partitioning.

---

## Dependencies at Risk

### `agent-client-protocol==0.9.0` (ACP)

**File:** `pyproject.toml:132`.
- Risk: Pinned hard. The `acp_adapter/server.py` imports many schema types directly from `acp.schema` — any breaking change in `acp` will break the ACP server.
- Impact: ACP-based editor integrations (Zed, VSCode via Copilot ACP) stop working.
- Migration plan: Bump pin deliberately; integration test against the consuming editors before release.

### OpenAI SDK

**Files:** `run_agent.py:64-76`, `agent/process_bootstrap.py`.
- Risk: `OpenAI` is exposed as a lazy proxy specifically to defer the ~240ms SDK import. The proxy preserves `patch("run_agent.OpenAI", ...)` in ~28 test files.
- Impact: An SDK upgrade that changes constructor signature, error types, or streaming semantics will break the lazy proxy AND the conversation loop's error classifier.
- Migration plan: When upgrading the OpenAI SDK, audit `agent/error_classifier.py` and `agent/chat_completion_helpers.py` for new error types.

### `acp` SDK schema surface

**File:** `acp_adapter/server.py` (top imports list ~30 schema types).
- Risk: Any schema type renamed or removed upstream breaks the import.
- Migration plan: Mirror upstream schema in tests.

### Multi-provider OAuth SDKs

**Files:** `agent/google_oauth.py` (38 KB), `agent/azure_identity_adapter.py` (23 KB), `hermes_cli/auth.py` (~7,666 lines owning OAuth flows for nous/codex/xai/qwen/minimax).
- Risk: Each OAuth provider has its own token-refresh and credential format. Drift in provider OAuth spec breaks one provider at a time.
- Impact: One provider's auth silently fails; rotation may degrade.
- Migration plan: Keep `_TERMINAL_AUTH_REASONS` in `credential_pool.py` synchronized with each provider's documented error vocabulary.

---

## Missing Critical Features

No feature gaps identified that block core workflows. The codebase has comprehensive coverage of CLI, gateway, plugins, MCP, ACP, kanban, web dashboard, TUI gateway, and cron. Feature gaps that exist (e.g. `--no-stream` removal flagged in `test-results.md`) are intentional API changes, not missing features.

---

## Test Coverage Gaps

### Conversation loop retry/fallback surface

- What's not tested: End-to-end retry/fallback chains with realistic provider errors. Buffered-trace flushing at each terminal point.
- Files: `agent/conversation_loop.py:1502`, `:2587`, `:2820`, `:3258`, `:4165`, `:4282`.
- Risk: Retry policy changes silently break user-visible retry trace.
- Priority: High — but blocked by the file's complexity. Test refactoring must come first.
- Difficulty to test: Requires faking the OpenAI SDK streaming surface and the error classifier simultaneously. The 84 / 68 skip markers in `tests/run_agent/test_run_agent.py` and `tests/run_agent/test_streaming.py` indicate the existing tests are themselves fragile.

### Auxiliary client paths

- What's not tested: Every auxiliary-model feature path (compression, title, hindsight, background review) end-to-end. `tests/agent/test_auxiliary_client.py` has 32 skip markers.
- Files: `agent/auxiliary_client.py`.
- Risk: A retry-policy change for one auxiliary feature breaks others.
- Priority: Medium.
- Difficulty to test: Each path constructs its own auxiliary client; mocking the full client surface is verbose.

### Per-provider adapter coverage

- What's not tested: Adapters in `plugins/model-providers/` (29 providers) have uneven test coverage. Adapters in `agent/` (anthropic, codex_responses, bedrock, gemini_native, gemini_cloudcode) have dedicated tests; plugin providers vary.
- Files: `plugins/model-providers/*/__init__.py`.
- Risk: A provider-specific quirk lands untested and breaks users of that provider.
- Priority: Medium — depends on provider popularity.
- Difficulty to test: Each provider requires its own fixtures and credentials.

### Multi-process credential refresh race

- What's not tested: Two Hermes processes refreshing the same OAuth token simultaneously. Comments at `agent/credential_pool.py:981`, `:1049` acknowledge this race.
- Files: `agent/credential_pool.py`.
- Risk: `refresh_token_reused` detection exists but the race itself is not regression-tested.
- Priority: Medium.
- Difficulty to test: Requires spawning two Hermes processes with shared credential state.

### Gateway allowlist enforcement

- What's not tested: Negative tests ("refuses to dispatch when allowlist missing") for every adapter. Some adapters have it (`msgraph_webhook.py`, `wecom.py`); others may not.
- Files: `gateway/platforms/*`.
- Risk: A new adapter silently fail-opens — security bug per `SECURITY.md` §3.1.
- Priority: High for any new adapter being added.
- Difficulty to test: Each adapter has its own config surface.

---

*Concerns audit: 2026-06-14*
*Update as issues are fixed or new ones discovered*
