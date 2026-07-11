# Phase 82: XCUT-04c Cost Tracking + XCUT-05 Lineage Auto - Context

**Gathered:** 2026-07-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Two parallel tracks closing v14.0 deferrals: (1) XCUT-04c GLM-4.6V cost tracking instrumentation + CLI surface; (2) XCUT-05-AUTO 15-agent lineage bump automation script.

**In scope:**

**Track 1 — XCUT-04c (GLM-4.6V Cost Tracking):**
- `plugins/kais_aigc/dreamina_stats.py` modification — add 3 fields to `DreaminaTaskMetrics` (input_tokens, output_tokens, estimated_cost_usd). Add `register_glm_cli()` function for `hermes glm stats` subcommand.
- `plugins/kais_aigc/vision_verify.py` modification — extend `verify_image_content()` + `verify_batch()` to return usage info (input_tokens, output_tokens) from `async_call_llm` response.
- `plugins/kais_aigc/dreamina_manager.py` modification — capture vision_verify usage + write to DreaminaTaskMetrics.
- `~/.hermes/config.yaml` `glm_46v.pricing` block — input_usd_per_1m_tokens + output_usd_per_1m_tokens (operator-configurable).
- Tests for all modifications.

**Track 2 — XCUT-05-AUTO (15-Agent Lineage Bump):**
- `scripts/bump_all_agent_lineage.py` (hermes-agent repo) — wraps `transform_skill_to_agent.py` for Track A 9 EXPERTS_9 + handles Track B 6 v13.0 P62 manual cases. Validates all 15 agent.yaml outputs via `agent.registry_loader.load_one_agent_yaml`.
- Tests for bump script.

**Out of scope (per REQUIREMENTS.md):**
- IMG-07 auto-scaling concurrency (v16+ scope).
- IMG-08 multi-model routing (v16+ scope).
- TRANS-08/09/10/11 (v16+ scope).
- Live GLM API pricing queries (config-based pricing only — v16+ scope if real-time pricing needed).
- Per-character cost tracking (current granularity is per-task; finer is v16+).
- Track B automated template generation (current Track B uses per-expert manual template mapping — full automation is v16+ scope).
- SKILL.md body changes (L1-L6 read-only invariant — not touched).
- Historical MetricsBuffer backfill (existing entries stay zero-token — no migration).

**Cross-repo topology:** Track 1 code in kais-hermes-skills repo (dreamina_stats.py + vision_verify.py + dreamina_manager.py); Track 2 script in hermes-agent repo (scripts/bump_all_agent_lineage.py). Planning artifacts in hermes-agent. Cross-repo pin recorded at milestone close.

</domain>

<decisions>
## Implementation Decisions

### XCUT-04c MetricsBuffer Extension
- Token spend fields: add 3 fields to `DreaminaTaskMetrics` directly — `input_tokens: int = 0`, `output_tokens: int = 0`, `estimated_cost_usd: float = 0.0`. Default to 0 for backward compatibility with v14.0 entries (which don't have these fields). One vision_verify GLM-4.6V call per task.
- Token capture mechanism: extend `vision_verify.verify_image_content()` + `verify_batch()` to return usage info (input_tokens, output_tokens) extracted from `async_call_llm` response. Add `usage` field to the returned dict. `dreamina_manager.py` captures usage + writes to DreaminaTaskMetrics on task completion.
- `estimated_cost_usd` calculation: pricing in `~/.hermes/config.yaml` `glm_46v.pricing` block — `input_usd_per_1m_tokens: 3.0` + `output_usd_per_1m_tokens: 8.0` (GLM-4.6V approximate pricing — operator verifies + updates). Computed per call: `(input_tokens / 1_000_000 * input_rate) + (output_tokens / 1_000_000 * output_rate)`.
- Backward compatibility: existing `dreamina_stats.jsonl` entries without token fields → default to 0. `hermes glm stats` CLI reports "N entries have no token data (pre-v15.0)" warning. Entries without token data are excluded from cost totals but counted in task counts.

### XCUT-04c CLI (`hermes glm stats`)
- CLI registration: new `register_glm_cli()` function in `dreamina_stats.py` (alongside existing `register_dreamina_cli()`). Registers `hermes glm stats` subcommand. Reuses the same `dreamina_stats.jsonl` MetricsBuffer (single source of truth).
- Aggregation dimensions: monthly + per-stratum (1-ref/3-ref/5-ref/text2image). Monthly totals (token count + estimated USD cost) + per-stratum breakdown. Aligns with `hermes dreamina stats` per-stratum split.
- Rich table format: mirror `hermes dreamina stats` — monthly table (month | task_count | input_tokens | output_tokens | estimated_cost_usd) + per-stratum table (stratum | task_count | total_tokens | estimated_cost_usd). Reuse `_emit_rich` helper from dreamina_stats.py.
- `--json` flag: yes — mirrors `hermes dreamina stats --json`. JSON output with same aggregation data. Optional `--month YYYY-MM` flag to filter to single month.

### XCUT-05-AUTO Lineage Bump Script
- Script location: `/data/workspace/hermes-agent/scripts/bump_all_agent_lineage.py` — alongside `transform_skill_to_agent.py` (in hermes-agent repo). Wrapper pattern: calls base script for Track A + handles Track B directly.
- 15 experts list: hardcoded `ACTIVE_EXPERTS_15` list in `bump_all_agent_lineage.py` (Track A 9 + Track B 6). Clear + explicit for operator review. Two sub-lists separated for traceability:
  - Track A (EXPERTS_9, handled by transform_skill_to_agent.py): screenplay, storyboard_designer, character_designer, scene_builder, cinematographer, editor, colorist, audio_pipeline, animation_studio
  - Track B (6 v13.0 P62 manual cases): style_genome, continuity_auditor, performer, hook_retention, documentary_maker, theory_critic
- Track B handling: script calls `transform_skill_to_agent.py` for Track A 9 experts, then handles Track B 6 experts as "manual cases" with per-expert template mapping (documented in script docstring). Track B experts may need special field handling not in the base script. If a Track B expert fails, script logs error + continues (partial success acceptable).
- Validation: validate all 15 generated YAMLs via `agent.registry_loader.load_one_agent_yaml` (same validation as base script). Verify lineage fields (skill_sha256, transform_notes, source_version). Script exits 0 only if all 15 pass; exit 1 on partial success.

### Claude's Discretion
- **vision_verify usage extraction:** The `async_call_llm` response likely has a `usage` field with `prompt_tokens` + `completion_tokens`. Extract these + map to `input_tokens` + `output_tokens` in the vision_verify return dict. If `async_call_llm` doesn't return usage, fall back to estimating from response length (rough estimate — document the estimation formula).
- **dreamina_stats.py register_glm_cli structure:** (a) `register_glm_cli(subparser)` adds `glm stats` subcommand with `--json` + `--month` flags; (b) `_glm_command(args)` reads MetricsBuffer + aggregates by month/stratum; (c) `_emit_glm_rich(monthly_data, stratum_data)` renders tables. Reuse `_emit_rich` pattern from dreamina stats.
- **Pricing config block:** Add `glm_46v:` block to `~/.hermes/config.yaml` with `pricing:` sub-block. If config missing, use hardcoded defaults ($3/$8 per 1M tokens — document as approximate). If config has invalid pricing (negative, non-numeric), warn + use defaults.
- **bump_all_agent_lineage.py structure:** (a) `ACTIVE_EXPERTS_15` list with Track A + Track B sub-lists; (b) `bump_track_a()` calls transform_skill_to_agent.py via subprocess; (c) `bump_track_b()` handles each Track B expert with per-expert logic (some may call transform_skill_to_agent.py with --expert flag, others need direct YAML construction); (d) `validate_all()` runs load_one_agent_yaml on all 15; (e) `main()` orchestrates + reports.
- **Track B per-expert mapping:** For Track B experts that transform_skill_to_agent.py doesn't know about, the bump script can either (a) extend the base script to handle them, or (b) construct YAMLs directly using the same field-mapping rules. Recommend (b) for minimal base script changes — Track B logic lives entirely in bump_all_agent_lineage.py.
- **Tests:** (a) MetricsBuffer schema with new fields (backward compat); (b) vision_verify usage extraction (mocked async_call_llm response with usage); (c) dreamina_manager captures usage; (d) register_glm_cli + --json + --month; (e) pricing config read + default fallback; (f) bump script ACTIVE_EXPERTS_15 list correct; (g) bump script validates all 15; (h) Track B per-expert handling.
- **Error handling:** If MetricsBuffer file missing, `hermes glm stats` reports zero. If pricing config invalid, warn + use defaults. If bump script's transform_skill_to_agent.py call fails (Track A), log error + continue to Track B. If Track B expert fails, log error + continue to next expert. Partial success is acceptable (operator reviews failures).

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`plugins/kais_aigc/dreamina_stats.py`** — existing MetricsBuffer + CLI. `DreaminaTaskMetrics` Pydantic v2 schema (line 57). `register_dreamina_cli()` at line 165. `_emit_rich()` helper. Phase 82 adds 3 fields to schema + new `register_glm_cli()`.
- **`plugins/kais_aigc/vision_verify.py`** — existing vision-verify module (Phase 79 modified). `verify_image_content()` at line 73 + `verify_batch()` at line 136 (both async). `_extract_confidence()` parses confidence from response. Phase 82 extends to return usage info.
- **`plugins/kais_aigc/dreamina_manager.py`** — existing dreamina orchestrator (Phase 79 modified — passes stratum param). Calls verify_image_content/verify_batch. Phase 82 captures usage from return + writes to DreaminaTaskMetrics.
- **`scripts/transform_skill_to_agent.py`** (hermes-agent) — existing lineage bump tool. `EXPERTS_9` list at line 72. Handles Track A 9 experts. Phase 82's bump_all_agent_lineage.py wraps this.
- **`~/.hermes/agents/*.agent.yaml`** — 20 existing agent.yaml files. 15 are active experts (Track A 9 + Track B 6). 5 are non-expert agents (script_auditor, prompt_injector, creative_source, production, compliance_gate).
- **`agent/registry_loader.py`** (hermes-agent) — `load_one_agent_yaml()` validates agent.yaml schema. Used by transform_skill_to_agent.py + Phase 82 bump script.

### Established Patterns
- **Pydantic v2 BaseModel** with `ConfigDict(extra="forbid")` for MetricsBuffer schema.
- **ruamel.yaml** for config.yaml round-trip (Phase 79 apply_vision_verify_thresholds.py pattern).
- **Rich table for CLI output** — dreamina_stats `_emit_rich` pattern.
- **`hermes_constants.get_hermes_home()`** for `~/.hermes/` paths.
- **`encoding="utf-8"`** on every `open()` call (Ruff PLW1514).
- **`from __future__ import annotations`** at module top.
- **Sync-only CLI scripts** (INFRA-04 — no asyncio.gather for GLM calls).
- **Async vision_verify functions** with serial awaits (Phase 78 pattern).

### Integration Points
- **`~/.hermes/metrics/dreamina_stats.jsonl`** — MetricsBuffer JSONL. Extended with 3 new fields per entry. Read by `hermes dreamina stats` + new `hermes glm stats`.
- **`~/.hermes/config.yaml`** — new `glm_46v.pricing` block (Phase 79 added `vision_verify.thresholds` block; Phase 81 added `cloud_engines` block).
- **`agent/auxiliary_client.py` `async_call_llm`** — vision_verify calls this. Response has `usage` field with token counts. Phase 82 extracts usage.
- **`scripts/transform_skill_to_agent.py`** — Phase 82 bump script wraps this for Track A + extends for Track B.
- **`~/.hermes/agents/*.agent.yaml`** — output of bump script. Validated by `agent.registry_loader.load_one_agent_yaml`.

</code_context>

<specifics>
## Specific Ideas

- **Two-track parallel design:** Track 1 (XCUT-04c) + Track 2 (XCUT-05-AUTO) are independent. Track 1 modifies kais-hermes-skills plugins; Track 2 creates a new hermes-agent script. They can be in separate plans + waves.
- **vision_verify usage return is backward-compatible:** Adding `usage` field to the return dict doesn't break existing callers (they ignore unknown fields). Dreamina_manager captures it; other callers (if any) don't.
- **DreaminaTaskMetrics backward compat via default=0:** Existing entries without token fields load cleanly (Pydantic v2 uses defaults). No migration needed. `hermes glm stats` warns about pre-v15.0 entries.
- **Pricing in config.yaml (not hardcoded):** GLM-4.6V pricing changes over time. Config-based pricing lets operator update without code change. Default values documented as approximate.
- **bump_all_agent_lineage.py wraps (not replaces) transform_skill_to_agent.py:** The base script is proven (v10.0/v13.0/v14.0 used it). The bump script wraps it for Track A + extends for Track B. If the base script fails, Track A errors are logged but Track B still attempts.
- **Track B per-expert template mapping documented:** Track B 6 experts have field-mapping rules that differ from Track A (v13.0 P62 manual cases). The bump script documents each Track B expert's mapping in the docstring + handles them explicitly.

</specifics>

<deferred>
## Deferred Ideas

- **IMG-07 auto-scaling concurrency** — v16+ scope (current 10-parallel is validated stable).
- **IMG-08 multi-model routing** — v16+ scope (defer until dreamina_manager pattern proven).
- **Live GLM API pricing queries** — config-based pricing only. Real-time pricing API integration is v16+ scope.
- **Per-character cost tracking** — current granularity is per-task. Finer (per-character, per-shot) is v16+ scope.
- **Historical MetricsBuffer backfill** — existing v14.0 entries stay zero-token. No migration. If operator needs historical costs, they estimate from task counts.
- **Track B full automation** — Track B uses per-expert manual template mapping. Full automation (auto-derive mapping from SKILL.md structure) is v16+ scope.
- **bump_all_agent_lineage.py auto-detect experts** — current design hardcodes ACTIVE_EXPERTS_15. Auto-detect from SKILL.md directory is v16+ scope (requires stable detection logic).
- **Cross-repo lineage consistency check** — bump script validates agent.yaml schema but doesn't cross-check against kais-hermes-skills SKILL.md source. SHA-256 drift detection is v16+ scope.
- **Agent lineage diff viewer** — script bumps lineage but doesn't show what changed. Diff viewer is v16+ scope.

</deferred>
