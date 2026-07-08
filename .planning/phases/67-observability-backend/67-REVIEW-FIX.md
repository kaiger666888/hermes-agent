---
phase: 67-observability-backend
fixed_at: 2026-07-08T00:00:00Z
review_path: .planning/phases/67-observability-backend/67-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 67: Code Review Fix Report

**Fixed at:** 2026-07-08
**Source review:** `.planning/phases/67-observability-backend/67-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 5 (WR-01..05 — WARNING tier)
- Fixed: 5
- Skipped: 0
- INFO findings (IN-01..04): deferred per default scope

## Fixed Issues

### WR-01: OBSRV-03 underreports mem0 add() error responses

**Files modified:** `plugins/memory/mem0/__init__.py`
**Commit:** `5b44e6c7c`
**Applied fix:** Added `cap.mark_failure(RuntimeError(...))` calls on all three silent-degradation error branches in the mem0 adapter — (1) `add()` `parsed.get("error")` branch (the original cited branch), (2) `search()` `if not isinstance(parsed, dict)` branch, (3) `search()` `if not isinstance(items, list)` branch. Without these calls, the `_memory_op_capture` context manager recorded `success=True` on error-shaped responses, inflating the operator-visible `error_rate` denominator. The synthesized `RuntimeError` carries a descriptive message (`mem0_error_response:`, `mem0_malformed_response:`, `mem0_malformed_results:`) for forensic visibility. Mirrors the existing `except Exception as exc: cap.mark_failure(exc)` contract.

### WR-02: Docstring/implementation drift in get_agent_opinion

**Files modified:** `mcp_serve.py`
**Commit:** `5d60149df`
**Applied fix:** Chose REVIEW Option (b) — updated the docstring to accurately describe the actual nesting. The `release_round_lock` call IS inside the `with _turn_capture` block, so `duration_ms` includes lock-release await time. Option (a) (hoist the release outside the `with` block) was rejected because it requires removing the redundant inner `try:` at the original L779 and re-indenting ~190 lines of body — too high blast-radius for a documentation-drift fix. The new comment explicitly documents the bias (uniform across samples, so p50/p95 *deltas* remain meaningful for trend analysis) and includes a sketch of the proper restructure for a future fix.

### WR-03: get_last_call_usage() race in get_agent_opinion

**Files modified:** `mcp_serve.py`
**Commit:** `5f0b69c2e`
**Applied fix:** Chose REVIEW Option (a) — accept the race with an updated comment. Expanded the inline comment from "prevents race" (incorrect) to "narrows the race window" (accurate) and documented the residual window: cross-roundId concurrent turns can interleave at the `await call_llm` resolution point and overwrite the global `_LAST_CALL_USAGE`. The `token_cost` metric is now explicitly labeled "BEST-EFFORT; under cross-roundId concurrency it may be attributed to the wrong turn. Within-roundId attribution is reliable (INFRA-04 serial)." A proper fix (have `call_llm` return the usage dict inline) is noted as out-of-Phase-67-scope.

### WR-04: submit_capture happy-path documentation drift

**Files modified:** `mcp_serve.py`
**Commit:** `bbf7178b3`
**Applied fix:** Updated the comment to match reality. The state module unconditionally sets ONLY `tokensConsumed`, `costUsdEstimate`, and `lastUpdatedAt` on the completed transition. `turns` and `events` are pre-existing lists in the state dict — they are NOT created or reset by `submit_round_table_result`. The comment now discloses that for pre-Phase-58 state files lacking `turns`/`events`, the metric reports `turn_count=0` and `early_stop_triggered=False` (defensive, no crash, but misleading for legacy state). Noted the proper fix (push a guarantee into `round_table_state.submit_round_table_result`) as out-of-scope.

### WR-05: Round-table _reset_for_test rebinds module global

**Files modified:** `agent/observability/_ring_buffer.py`, `agent/observability/round_table_metrics.py`, `agent/observability/memory_backend_metrics.py`
**Commit:** `c64ba9317`
**Applied fix:** Added a public `clear()` method to the `MetricsBuffer` class (`_ring_buffer.py`) that empties the deque in place under the existing `_lock` (preserves `maxlen`). Updated `round_table_metrics._reset_for_test()` to call `_BUFFER.clear()` instead of rebinding the module global. Updated `memory_backend_metrics._reset_for_test()` to call `_BUFFER.clear()` instead of reaching into the private `_BUFFER._buf` attribute. Both helpers now use the same public API, eliminating both the rebinding hazard (silent breakage of `from ... import _BUFFER` callers) and the private-attribute reach. Smoke-tested `clear()` manually: `maxlen` is preserved across clear+append cycles.

## Skipped Issues

None — all 5 in-scope findings successfully fixed.

---

_Fixed: 2026-07-08_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
