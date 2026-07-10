---
phase: 82-xcut-04c-cost-tracking-xcut-05-lineage-auto
fixed_at: 2026-07-10T13:50:00Z
review_path: .planning/phases/82-xcut-04c-cost-tracking-xcut-05-lineage-auto/82-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 82: Code Review Fix Report

**Fixed at:** 2026-07-10T13:50:00Z
**Source review:** `.planning/phases/82-xcut-04c-cost-tracking-xcut-05-lineage-auto/82-REVIEW.md`
**Iteration:** 1
**Repo:** kais-hermes-skills (all fixes target this repo, not hermes-agent)

**Summary:**
- Findings in scope: 5 (1 Critical + 4 Warnings)
- Fixed: 5
- Skipped: 0
- Tests: 58 passed (3 test files: test_dreamina_manager.py + test_vision_verify.py + test_dreamina_stats.py)

## Fixed Issues

### CR-01: Cost tracking undercounts tokens for multi-attempt vision-verify

**Files modified:** `plugins/kais_aigc/dreamina_manager.py`, `plugins/kais_aigc/tests/test_dreamina_manager.py`
**Commit:** 6a59757
**Applied fix:** Added `total_input_tokens` + `total_output_tokens` accumulators before the 3-attempt loop in `_generate_one_with_verify`. Each vision-verify call's usage is added to the running total. All return paths (ok, degraded) now use cumulative totals via `cumulative_usage` / `cumulative_cost`. The failed return path (before vision-verify) correctly reports zero usage/cost. Added two tests: `test_multi_attempt_accumulates_usage` (fail-fail-pass, 3 attempts, verifies sum of all 3 attempts' tokens) and `test_multi_attempt_degraded_accumulates_usage` (all 3 fail, verifies accumulated total).

### WR-01: DreaminaTaskResult TypedDict missing usage + estimated_cost_usd fields

**Files modified:** `plugins/kais_aigc/dreamina_manager.py`, `plugins/kais_aigc/tests/test_dreamina_manager.py`
**Commit:** 7f4c354
**Applied fix:** Added `usage: dict[str, int]` and `estimated_cost_usd: float` fields to the `DreaminaTaskResult` TypedDict annotation. Added annotation test `test_dreamina_task_result_has_usage_fields` verifying both fields are declared.

### WR-02: Exception-path vr fallback dict missing usage key

**Files modified:** `plugins/kais_aigc/dreamina_manager.py`, `plugins/kais_aigc/tests/test_dreamina_manager.py`
**Commit:** 8afa2f0
**Applied fix:** Added `"usage": {"input_tokens": 0, "output_tokens": 0}` to the exception-path `vr` fallback dict (previously only `{"pass": False, "confidence": 0.0}`). This ensures shape consistency with successful `verify_image_content` returns. Added test `test_vision_verify_exception_includes_usage` verifying the exception path result includes usage + zero cost.

### WR-03: verify_batch attributes full batch-level usage to each image (N x inflation)

**Files modified:** `plugins/kais_aigc/vision_verify.py`, `plugins/kais_aigc/tests/test_vision_verify.py`
**Commit:** 64ae564
**Applied fix:** Implemented option (a) from the review suggestion: divide the batch-level usage by `len(batch_idx)` to get each image's per-image share. This ensures that summing usage across images reconstructs the batch total (not N x inflation). Updated docstring to document the division + remainder-drop behavior (integer division). Added two tests: `test_batch_usage_divided_among_images` (6 images, 600/300 batch → 100/50 each) and `test_batch_usage_summation_approximates_total` (4 images, 400/200 batch → sum = 400/200).

### WR-04: _extract_usage uses `or` fallback which treats legitimate 0 as falsy

**Files modified:** `plugins/kais_aigc/vision_verify.py`, `plugins/kais_aigc/tests/test_vision_verify.py`
**Commit:** 89390cf
**Applied fix:** Replaced `or` fallback chains with explicit `<= 0` checks in `_extract_usage`. The `or` operator treats `prompt_tokens=0` (a valid value) as falsy and silently skips to the alternate key. The explicit `if input_tokens <= 0:` check documents the intent: use the primary key when it has a positive value, otherwise try the alternate key. Added two tests: `test_extract_usage_zero_prompt_tokens_no_fallback_key` (0 with no alternate → 0) and `test_extract_usage_zero_prompt_tokens_with_fallback_key` (0 with alternate=50 → falls back to 50).

---

_Fixed: 2026-07-10T13:50:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
