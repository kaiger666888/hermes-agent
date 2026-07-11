---
phase: 82-xcut-04c-cost-tracking-xcut-05-lineage-auto
plan: 01
subsystem: infra
tags: [pydantic, vision-verify, glm-4.6v, cost-tracking, metrics, dreamina]

# Dependency graph
requires:
  - phase: 79-02
    provides: "vision_verify.py get_threshold + stratum param + dreamina_manager stratum wiring (preserved)"
provides:
  - "DreaminaTaskMetrics with input_tokens/output_tokens/estimated_cost_usd fields"
  - "vision_verify._extract_usage() helper + usage key in verify_image_content/verify_batch returns"
  - "dreamina_manager._compute_cost_usd() with config.yaml glm_46v.pricing read + $3/$8 defaults"
  - "dreamina_manager._generate_one_with_verify captures usage + writes to MetricsBuffer via record_metric"
affects: [82-02, 83]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Process-lifetime _pricing_cache for config.yaml pricing (mirrors Phase 79 _threshold_cache pattern)"
    - "Dual-form attribute extraction (prompt_tokens/input_tokens + dict access) for OpenAI SDK response.usage"

key-files:
  created: []
  modified:
    - "plugins/kais_aigc/dreamina_stats.py — DreaminaTaskMetrics + 3 new token/cost fields"
    - "plugins/kais_aigc/vision_verify.py — _extract_usage() + usage key in verify_image_content/verify_batch"
    - "plugins/kais_aigc/dreamina_manager.py — _compute_cost_usd() + usage capture in _generate_one_with_verify + record_metric token fields"

key-decisions:
  - "Token fields default to 0 (backward-compatible with v14.0 entries lacking token data)"
  - "Pricing in config.yaml glm_46v.pricing block with $3/$8 per 1M token defaults (operator-configurable)"
  - "Cache hits report usage 0/0 (no new API call consumed)"
  - "Batch-level usage attributed to each image in batch (approximate — shared API call)"
  - "_extract_usage handles prompt_tokens, input_tokens, dict form, and None (dual-form pattern from auxiliary_client.py)"

patterns-established:
  - "Process-lifetime cache pattern for config reads (pricing follows Phase 79 threshold cache model)"
  - "Dual-form attribute extraction for provider response normalization"

requirements-completed: [XCUT-04c-INSTRUMENT]

# Metrics
duration: 18min
completed: 2026-07-10
---

# Phase 82 Plan 01: XCUT-04c MetricsBuffer Instrumentation Summary

**3 new fields on DreaminaTaskMetrics (input_tokens + output_tokens + estimated_cost_usd) with GLM-4.6V usage extraction in vision_verify + cost computation + MetricsBuffer capture in dreamina_manager, all backward-compatible with Phase 79 changes**

## Performance

- **Duration:** 18 min
- **Started:** 2026-07-10T13:00:00Z
- **Completed:** 2026-07-10T13:18:00Z
- **Tasks:** 2 (TDD: RED + GREEN for each)
- **Files modified:** 6 (3 source + 3 test)

## Accomplishments

- DreaminaTaskMetrics extended with input_tokens (int, default 0), output_tokens (int, default 0), estimated_cost_usd (float, default 0.0) — backward-compatible with v14.0 entries
- vision_verify._extract_usage() normalizes OpenAI SDK response.usage across all provider forms (prompt_tokens/input_tokens/dict/None)
- verify_image_content + verify_batch return dicts include "usage" key with token counts (0/0 on cache hits)
- dreamina_manager._compute_cost_usd() reads config.yaml glm_46v.pricing block with $3/$8 defaults + process-lifetime cache
- dreamina_manager._generate_one_with_verify captures usage from vision_verify return + computes cost + includes in all return paths
- batch_submit record_metric writes input_tokens + output_tokens + estimated_cost_usd to MetricsBuffer JSONL
- 16 new tests added (4 dreamina_stats + 6 vision_verify + 6 dreamina_manager), all 40 tests across 3 files passing

## Task Commits

Each task was committed atomically (TDD RED → GREEN):

1. **Task 1 RED: Token field tests + usage extraction tests** — `3f5acb5` (test)
2. **Task 1 GREEN: DreaminaTaskMetrics fields + vision_verify usage** — `74b139c` (feat)
3. **Task 2 RED: Usage capture + cost computation tests** — `dc22f2a` (test)
4. **Task 2 GREEN: dreamina_manager usage capture + _compute_cost_usd** — `0ab8f34` (feat)

## Files Created/Modified

- `plugins/kais_aigc/dreamina_stats.py` — Added input_tokens/output_tokens/estimated_cost_usd fields to DreaminaTaskMetrics (default 0, ge=0); extra="forbid" preserved
- `plugins/kais_aigc/vision_verify.py` — Added _extract_usage() helper + "usage" key in verify_image_content/verify_batch return dicts (0/0 on cache hit); Phase 79 get_threshold + stratum param preserved
- `plugins/kais_aigc/dreamina_manager.py` — Added _compute_cost_usd() with config.yaml pricing read + $3/$8 defaults; _generate_one_with_verify captures usage + computes cost in all return paths; record_metric includes token/cost fields; Phase 79 stratum wiring + asyncio.gather + tenacity retry preserved
- `plugins/kais_aigc/tests/test_dreamina_stats.py` — Added TestTokenFields class (4 tests)
- `plugins/kais_aigc/tests/test_vision_verify.py` — Added TestUsageExtraction (4 tests) + TestVerifyImageContentUsage (2 tests)
- `plugins/kais_aigc/tests/test_dreamina_manager.py` — Added TestUsageCapture class (6 tests)

## Decisions Made

- **Pricing defaults $3/$8 per 1M tokens** — approximate GLM-4.6V pricing per CONTEXT.md D-01. Operator verifies + updates via config.yaml glm_46v.pricing block. Config-based pricing lets operator update without code change.
- **Cache hits report usage 0/0** — cached entries don't consume new API tokens, so usage is zero. This prevents double-counting in cost aggregates.
- **Batch-level usage attributed per image** — verify_batch shares one API call across 4-8 images. Per-image attribution uses the batch total (documented as approximate in docstring). Finer attribution would require provider-side per-image token reporting (v16+ scope).
- **_extract_usage dual-form extraction** — OpenAI native uses prompt_tokens/completion_tokens; some providers use input_tokens/output_tokens; some return dict. Helper normalizes all forms with getattr + dict.get fallback. Mirrors auxiliary_client.py:951-959 pattern.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- **Pre-existing test failure (out of scope):** `test_canvas_sync_integration.py::TestFullPipelineEpisodeSubscriber::test_save_v2_bodies_carry_phase_node_ids` fails. Verified pre-existing via `git stash` (reproduces without Phase 82 changes). Unrelated to Phase 82 — canvas sync pipeline subsystem. Logged to `deferred-items.md` per scope-boundary rule. All 40 tests in the 3 plan test files pass.
- **Ruff not installed in venv:** The plan's verification step `python -m ruff check` cannot run — ruff is not installed in `/data/workspace/hermes-agent/.venv/`. Manual verification of all `open()` calls confirms `encoding="utf-8"` present on every text-mode open (the single `"rb"` binary mode open doesn't need it). PLW1514 compliance confirmed by grep.

## User Setup Required

None — no external service configuration required. Pricing config block is optional (defaults work without it).

## Next Phase Readiness

- Plan 82-02 (XCUT-04c-CLI) can build on the DreaminaTaskMetrics token fields to add `hermes glm stats` CLI aggregation
- Plan 82-03 (XCUT-05-AUTO) is independent of this plan (lineage bump script in hermes-agent repo)
- Phase 83 (VALIDATE) will verify all token fields are backward-compatible at milestone audit

## TDD Gate Compliance

- [x] RED gate: `test(82-01)` commits exist (3f5acb5, dc22f2a)
- [x] GREEN gate: `feat(82-01)` commits exist after RED (74b139c, 0ab8f34)
- [x] All tests pass after GREEN phase (40/40 across 3 files)

## Self-Check: PASSED

- [x] `plugins/kais_aigc/dreamina_stats.py` — FOUND (DreaminaTaskMetrics has 3 new fields)
- [x] `plugins/kais_aigc/vision_verify.py` — FOUND (_extract_usage + usage key in returns)
- [x] `plugins/kais_aigc/dreamina_manager.py` — FOUND (_compute_cost_usd + usage capture + record_metric)
- [x] `plugins/kais_aigc/tests/test_dreamina_stats.py` — FOUND (TestTokenFields)
- [x] `plugins/kais_aigc/tests/test_vision_verify.py` — FOUND (TestUsageExtraction + TestVerifyImageContentUsage)
- [x] `plugins/kais_aigc/tests/test_dreamina_manager.py` — FOUND (TestUsageCapture)
- [x] Commit `3f5acb5` — FOUND
- [x] Commit `74b139c` — FOUND
- [x] Commit `dc22f2a` — FOUND
- [x] Commit `0ab8f34` — FOUND
- [x] Backward compat: `DreaminaTaskMetrics(submit_id='x', stratum='1-ref', ...)` prints "0 0 0.0"
- [x] All open() calls have encoding="utf-8"
- [x] Phase 79 changes preserved (get_threshold + stratum param in vision_verify + dreamina_manager)

---
*Phase: 82-xcut-04c-cost-tracking-xcut-05-lineage-auto*
*Completed: 2026-07-10*
