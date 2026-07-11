# Phase 81: XCUT-04b Cloud Engine Bootstrap - Context

**Gathered:** 2026-07-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Operator-action handoff closure for XCUT-04b: deliver a cloud engine bootstrap doc + config schema + routing rules update + opt-in check script that turns cloud transition engine setup (Hailuo 02 i2v Pro + Vidu keyframe-to-video + ComfyUI Wan2.2 FLF2V) into a documented operator task with config-driven opt-in.

**In scope:**
- `references/cloud-engine-bootstrap.md` — Hailuo + Vidu API key acquisition steps + ComfyUI Wan2.2 FLF2V custom node install procedure + cost-estimation worksheet (per-shot + monthly projections).
- `~/.hermes/config.yaml` `cloud_engines` block — `hailuo_api_key` + `vidu_api_key` + `wan22_comfyui_node_enabled`. Config template (`cli-config.yaml.example`) updated with commented-out block.
- `transition-engine-routing.md` update — add `## Cloud Engine Opt-in State` section documenting config keys + fallback behavior. Update existing `MINIMAX_API_KEY`/`VIDU_API_KEY` env var references to point to config keys (config primary, env var fallback).
- `scripts/check_cloud_engine_optin.py` — simple CLI that reads `~/.hermes/config.yaml` cloud_engines block + prints Rich table showing opt-in status per engine + which transition methods are available.
- `kais-jimeng-cli/SKILL.md` minimal touch — add `## Cloud Engine Bootstrap` section with one-line link to `cloud-engine-bootstrap.md` (single authorized SKILL.md exception per v15.0 hard constraints).
- Unit tests for check_cloud_engine_optin.py.

**Out of scope (per REQUIREMENTS.md):**
- The actual API keys + ComfyUI node install (operator-action handoff — v15.0 delivers doc + config + opt-in mechanism, NOT the keys/installs themselves).
- TRANS-08 AI-generated whip pan transitions (v16+ scope).
- TRANS-09 custom transition types beyond 12-value taxonomy (v16+ scope).
- TRANS-10 per-transition runtime LLM routing (INFRA-04 risk — v15.0 stays declarative).
- TRANS-11 LTX-FLF+ICLoRA production rollout (gated by Phase 78 TRANS-07 verdict — v16+ scope).
- Any SKILL.md body changes beyond kais-jimeng-cli (L1-L6 read-only invariant — all other SKILL.md files untouched).
- Cloud engine API client libraries (Hailuo/Vidu SDK wrappers) — operator calls APIs directly per bootstrap doc. v16+ scope if pipeline integration needed.

**Cross-repo topology:** bootstrap doc + routing update + check script + tests + kais-jimeng-cli SKILL.md touch in kais-hermes-skills repo; cli-config.yaml.example update + planning artifacts in hermes-agent repo. Cross-repo pin recorded at milestone close.

</domain>

<decisions>
## Implementation Decisions

### Bootstrap Doc & SKILL.md Cross-reference
- `cloud-engine-bootstrap.md` location: `skills/kais-movie-pipeline/references/cloud-engine-bootstrap.md` — alongside `transition-engine-routing.md` (its companion). Co-located for cross-reference.
- Doc structure: per-engine sections (Hailuo + Vidu + Wan2.2) + unified cost worksheet. Each engine: acquisition steps (API key signup / node install) + prerequisites + troubleshooting. Cost worksheet: per-shot estimate + monthly projection table.
- Cost-estimation worksheet format: markdown table with per-engine columns — engine | cost-per-shot | shots-per-episode | episodes-per-month | monthly-cost. Operator fills in shot count; formulas documented inline.
- `kais-jimeng-cli/SKILL.md` cross-reference: add `## Cloud Engine Bootstrap` section with one-line link to `cloud-engine-bootstrap.md` + note that jimeng CLI is separate from cloud transition engines. Minimal touch — single authorized SKILL.md exception per v15.0 hard constraints.

### Config Schema & Opt-in Mechanism
- `cloud_engines` config block location: top-level `cloud_engines:` block in `~/.hermes/config.yaml` — alongside existing `vision_verify:` block (Phase 79). Top-level for visibility + operator discoverability.
- Config schema:
  ```yaml
  cloud_engines:
    hailuo_api_key: null  # null = not opted in; paste API key string to opt in
    vidu_api_key: null    # null = not opted in; paste API key string to opt in
    wan22_comfyui_node_enabled: false  # false = not installed; true = installed + opted in
  ```
- Env var compatibility: config is primary; env vars `HAILUO_API_KEY` / `VIDU_API_KEY` as fallback for CI/containers. Documented in bootstrap doc. Aligns with existing `MINIMAX_API_KEY` reference in routing doc (Hailuo = MiniMax rebrand — operator may know either name).
- Config template update: update `cli-config.yaml.example` in hermes-agent repo with `cloud_engines:` block commented out + documentation comment explaining each field.

### Routing Rules Update & Runtime Check
- `transition-engine-routing.md` update: add `## Cloud Engine Opt-in State` section after the routing table. Documents: (a) config keys that control opt-in (`cloud_engines.hailuo_api_key` etc.), (b) how to check opt-in state (read config.yaml or run `check_cloud_engine_optin.py`), (c) fallback behavior when not opted in. Update existing `MINIMAX_API_KEY`/`VIDU_API_KEY` references to point to config keys (config primary, env var fallback).
- Fallback behavior: when primary engine not opted in, routing falls back to next engine in the chain. E.g. `match_cut_shared_landscape`: Hailuo not opted in → Vidu; Vidu not opted in → ffmpeg manual cut. Operator sees which engine was used in pipeline logs.
- Runtime check mechanism: purely declarative — no code routing logic. Routing rules doc references config keys; operator/pipeline reads both docs + makes decision. INFRA-04 compliant (no runtime LLM routing). A simple `scripts/check_cloud_engine_optin.py` script provides CLI opt-in status check.
- Opt-in check script: `scripts/check_cloud_engine_optin.py` — reads `~/.hermes/config.yaml` cloud_engines block (via ruamel.yaml for round-trip safety) + env var fallback + prints Rich table showing opt-in status per engine + which transition methods are available. Sync-only, stdlib + ruamel.yaml + rich.

### Claude's Discretion
- **Bootstrap doc content depth:** Per-engine sections should cover: (a) what the engine does (1-2 sentences), (b) prerequisites (account, hardware, network), (c) acquisition steps (signup URL, API key generation, pricing page), (d) configuration (paste key into config.yaml cloud_engines block), (e) verification (run check_cloud_engine_optin.py to confirm opt-in), (f) troubleshooting (common issues — invalid key, rate limits, network). For Wan2.2: node install procedure (ComfyUI Manager → search "Wan2.2 FLF2V" → install → verify in /object_info).
- **Cost worksheet formulas:** Per-shot cost = engine pricing (e.g. Hailuo ~$0.10/shot, Vidu ~$0.15/shot — operator verifies current pricing at acquisition). Monthly cost = per-shot × shots-per-episode × episodes-per-month. Document as markdown table with example row + operator-fills rows.
- **check_cloud_engine_optin.py structure:** (a) `load_cloud_engines_config()` reads ~/.hermes/config.yaml cloud_engines block (returns dict, falls back to env vars); (b) `check_optin_status(config)` returns per-engine status (opted_in: bool, source: "config"|"env"|"not_set"); (c) `get_available_transitions(status)` maps engine availability to transition methods (reads routing table); (d) `emit_rich_table(status, transitions)` prints summary; (e) `main()` argparse with `--json` flag for machine-readable output. Exit 0 always (informational, not pass/fail).
- **kais-jimeng-cli SKILL.md touch:** Add section after existing content (don't modify existing sections). Section content: `## Cloud Engine Bootstrap\n\nFor cloud transition engines (Hailuo 02 i2v Pro, Vidu keyframe-to-video, ComfyUI Wan2.2 FLF2V), see [\`cloud-engine-bootstrap.md\`](../../kais-movie-pipeline/references/cloud-engine-bootstrap.md). The jimeng CLI is separate from these cloud engines — jimeng handles image generation (P07), cloud engines handle transition generation (P11/P12).`
- **Tests for check_cloud_engine_optin.py:** Mock config file (temp file with cloud_engines block). Test: (a) all engines opted in (config has keys); (b) no engines opted in (empty config); (c) partial opt-in (Hailuo yes, Vidu no); (d) env var fallback (config missing, env var set); (e) --json output format; (f) available transitions mapping correct.
- **cli-config.yaml.example update:** Add commented-out cloud_engines block with documentation. Don't touch existing content. Place after vision_verify block (Phase 79 addition) if it exists, otherwise at end of file.
- **Error handling:** If config.yaml missing, check script reports "no config file found" + all engines not opted in (exit 0). If cloud_engines block missing, same behavior. If config parse fails, report error + exit 0 (informational, not crash).

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`skills/kais-movie-pipeline/references/transition-engine-routing.md`** — existing routing rules doc. Line 30-41 has routing table with `match_cut_shared_landscape` → Hailuo primary + Vidu fallback. Line 36-37 references `MINIMAX_API_KEY` + `VIDU_API_KEY` (env var names — Phase 81 aligns to config keys). Phase 81 adds `## Cloud Engine Opt-in State` section + updates env var references.
- **`skills/kais-creative/kais-jimeng-cli/SKILL.md`** — existing SKILL.md for jimeng CLI. Phase 81 adds `## Cloud Engine Bootstrap` section (single authorized SKILL.md touch per v15.0 hard constraints).
- **`cli-config.yaml.example`** (hermes-agent repo) — existing config template. Phase 81 adds commented-out `cloud_engines:` block.
- **`skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py`** (Phase 77) — Rich table + argparse pattern reference for check_cloud_engine_optin.py.
- **`plugins/kais_aigc/dreamina_stats.py`** — `get_hermes_home()` usage + config read pattern.
- **`plugins/kais_aigc/vision_verify.py`** (Phase 79 modified) — `get_threshold()` reads `~/.hermes/config.yaml` via ruamel.yaml. Same pattern for check_cloud_engine_optin.py.

### Established Patterns
- **ruamel.yaml** for config round-trip (comments preserved) — Phase 79 apply_vision_verify_thresholds.py pattern.
- **`hermes_constants.get_hermes_home()`** for `~/.hermes/` paths.
- **Rich table for CLI output** — Phase 77/78/79/80 pattern.
- **`encoding="utf-8"`** on every `open()` call (Ruff PLW1514).
- **`from __future__ import annotations`** at module top.
- **Sync-only execution** — no GLM calls, no async. Pure stdlib + ruamel.yaml + rich.
- **Pydantic v2** for report schema (if check script produces JSON output).

### Integration Points
- **`~/.hermes/config.yaml`** — Hermes config file. Phase 81 adds `cloud_engines:` block. Read by check_cloud_engine_optin.py + referenced by transition-engine-routing.md.
- **`transition-engine-routing.md`** — existing routing rules doc. Phase 81 extends with opt-in state section. Operator/pipeline reads this doc + config to make routing decisions.
- **`kais-jimeng-cli/SKILL.md`** — existing SKILL.md. Phase 81 adds cross-reference section (single authorized touch).
- **`cli-config.yaml.example`** (hermes-agent) — config template. Phase 81 adds commented-out cloud_engines block.

</code_context>

<specifics>
## Specific Ideas

- **Bootstrap doc is the primary deliverable:** The doc is what operator reads to set up cloud engines. Config schema + routing update + check script support the doc. Doc-first approach ensures operator has a single entry point.
- **Config primary, env var fallback:** Config is the canonical opt-in mechanism (operator edits config.yaml). Env vars (`HAILUO_API_KEY`/`VIDU_API_KEY`) are fallback for CI/containers where config file isn't practical. Check script reports which source was used.
- **Hailuo = MiniMax rebrand clarification:** Existing routing doc references `MINIMAX_API_KEY`. Hailuo is the consumer-facing brand; MiniMax is the company/API. Document both names in bootstrap doc to avoid operator confusion. Config key uses `hailuo_api_key` (consumer brand) per success criterion.
- **Wan2.2 uses boolean, not API key:** Wan2.2 FLF2V is a ComfyUI custom node (local install), not a cloud API. Config field `wan22_comfyui_node_enabled: false` is a boolean self-declaration — operator sets to `true` after installing the node. No verification (honesty-based). Check script reports the config value.
- **No routing code (declarative only):** Phase 81 does NOT implement routing logic in code. The routing rules are declarative (in the markdown doc). Operator/pipeline reads the doc + config + makes decision. This preserves INFRA-04 (no runtime LLM routing per TRANS-10 deferral). Check script is informational only — it reports status, doesn't route.
- **kais-jimeng-cli SKILL.md minimal touch:** Only add a new section. Don't modify existing content. The section clarifies that jimeng CLI (image generation) is separate from cloud transition engines. Prevents operator confusion.

</specifics>

<deferred>
## Deferred Ideas

- **TRANS-11 LTX-FLF+ICLoRA production rollout** — gated by Phase 78 TRANS-07 verdict. v16+ scope if validation passes.
- **TRANS-08 AI-generated whip pan transitions** — v16+ scope (current engines unreliable for cross-shot motion-vector continuity).
- **TRANS-09 custom transition types beyond 12-value taxonomy** — v16+ scope (industry-standard taxonomy sufficient).
- **TRANS-10 per-transition runtime LLM routing** — v16+ scope (INFRA-04 serial constraint violation risk; v15.0 stays declarative).
- **Cloud engine API client libraries** — Hailuo/Vidu SDK wrappers for pipeline integration. v16+ scope if pipeline needs programmatic API calls (current v15.0 delivers doc + config + opt-in check; operator calls APIs manually per bootstrap doc).
- **Automated Wan2.2 node install verification** — config field is honesty-based (operator sets `wan22_comfyui_node_enabled: true` after install). Automated verification (check ComfyUI /object_info for Wan2.2 nodes) is v16+ scope.
- **Cost tracking integration** — bootstrap doc has cost worksheet, but actual cost tracking (API call counters + billing alerts) is v16+ scope (XCUT-04c Phase 82 covers GLM-4.6V cost tracking; cloud engine cost tracking is parallel).
- **Per-engine rate limiting** — bootstrap doc mentions rate limits in troubleshooting, but automated rate limiting is v16+ scope.
- **Multi-key rotation** — single API key per engine. Multi-key rotation (like GLM 4-key rotation) is v16+ scope if quota limits hit.

</deferred>
