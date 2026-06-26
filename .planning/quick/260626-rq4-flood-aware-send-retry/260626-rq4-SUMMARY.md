---
phase: quick
quick_id: 260626-rq4
slug: flood-aware-send-retry
plan: 01
subsystem: gateway
tags: [gateway, telegram, flood-control, retry, base-adapter, stream-consumer-parity]
requires:
  - gateway/platforms/base.py::_send_with_retry (existing)
  - gateway/stream_consumer.py::_FLOOD_RETRY_AFTER_RE (vocabulary reference)
provides:
  - gateway/platforms/base.py::_FLOOD_RETRY_AFTER_RE (flood regex, byte-identical to stream_consumer)
  - gateway/platforms/base.py::_FLOOD_WAIT_MAX_SECONDS / _MIN_SECONDS / _DEFAULT_SECONDS
  - gateway/platforms/base.py::BasePlatformAdapter._is_flood_error(str)
  - gateway/platforms/base.py::BasePlatformAdapter._extract_retry_after_seconds(SendResult)
  - gateway/platforms/base.py::_send_with_retry flood-aware wait branch
affects:
  - gateway/platforms/telegram.py (benefits from base fix; out-of-scope WIP handled separately)
  - gateway/stream_consumer.py (vocabulary parity maintained; out-of-scope WIP handled separately)
tech-stack:
  added: []
  patterns:
    - "Flood-aware retry (clamped retry_after wait) mirroring stream_consumer._apply_flood_suspend"
    - "Three-source retry_after fallback (dict -> attribute -> regex)"
    - "Distinct log line for flood events (operator-grep friendly)"
key-files:
  created: []
  modified:
    - gateway/platforms/base.py
    - tests/gateway/test_send_retry.py
decisions:
  - "Broadened _send_with_retry entry condition to OR-in _is_flood_error (plan's <action> said modify only the if-is_network branch, but flood errors never entered that branch because _RETRYABLE_ERROR_PATTERNS excludes flood markers)"
  - "Kept _FLOOD_RETRY_AFTER_RE byte-identical to stream_consumer.py (requires trailing 'seconds?' suffix); bare 'retry after 30' without suffix falls through to _FLOOD_WAIT_DEFAULT_SECONDS"
  - "Updated mid-loop break check to also consider flood errors so persistent flood windows retry through instead of breaking early"
metrics:
  duration: 379s
  completed: 2026-06-26T12:09:25Z
  tasks: 3
  files: 2
  tests-added: 35
  tests-total: 70
---

# Quick Task 260626-rq4: Flood-Aware Send Retry Summary

Made `BasePlatformAdapter._send_with_retry()` Telegram-flood-aware so the gateway stops losing complete agent responses to Telegram's 18-27s sliding flood window. Flood errors now wait the parsed `retry_after` seconds (clamped to [3, 60], default 5) instead of the ~2s/~4s exponential backoff that was exhausting retries while the window was still active. Mirrors the proven pattern already shipped in `gateway/stream_consumer.py` so both layers speak the same flood vocabulary.

## What Changed

### `gateway/platforms/base.py`

1. **New module constants** (next to `_RETRYABLE_ERROR_PATTERNS`):
   - `_FLOOD_WAIT_MAX_SECONDS = 60.0` — cap so a malicious/malformed hint can't park the gateway forever (T-rq4-01 mitigation).
   - `_FLOOD_WAIT_MIN_SECONDS = 3.0` — Telegram's typical minimum flood backoff floor.
   - `_FLOOD_WAIT_DEFAULT_SECONDS = 5.0` — used when the error matches flood markers but no parseable retry_after is present.
   - `_FLOOD_RETRY_AFTER_RE` — byte-identical regex to `stream_consumer._FLOOD_RETRY_AFTER_RE` (vocabulary parity).

2. **New static helpers** on `BasePlatformAdapter` (next to `_is_retryable_error` / `_is_timeout_error`):
   - `_is_flood_error(error: Optional[str]) -> bool` — substring detection of `"flood"`, `"retry after"`, `"rate limit"`, `"429"` (case-insensitive). String-based variant of stream_consumer's result-object helper.
   - `_extract_retry_after_seconds(result: SendResult) -> Optional[float]` — three-source fallback chain (raw_response dict -> raw_response attribute -> regex on error string). Returns None when nothing parses; caller applies clamp + default.

3. **`_send_with_retry` modifications:**
   - Broadened retry-loop entry condition: `is_network = result.retryable or self._is_retryable_error(error_str) or self._is_flood_error(error_str)` (flood errors now reach the retry loop instead of falling through to plain-text fallback).
   - Inside the retry loop, added a flood branch that waits `max(MIN, min(secs, MAX))` seconds (or `DEFAULT` when retry_after is unparseable) before retrying, instead of exponential backoff.
   - Recompute `is_flood` after each retry to handle flood -> non-flood transitions.
   - Updated mid-loop break check to also consider flood errors so persistent flood windows retry through.
   - Emit distinct `"Flood control: waiting X.Xs before retry"` warning (lazy %-format) — operators can grep flood events in gateway.log, distinct from the normal `"Send failed (attempt"` retry line.

### `tests/gateway/test_send_retry.py`

- New imports: `_FLOOD_RETRY_AFTER_RE`, `_FLOOD_WAIT_MAX_SECONDS`, `_FLOOD_WAIT_MIN_SECONDS`, `_FLOOD_WAIT_DEFAULT_SECONDS`, `SimpleNamespace`.
- **`TestFloodModuleConstants`** (4 tests): constant values + regex shape.
- **`TestFloodAwareRetryHelpers`** (19 tests, parametrized): `_is_flood_error` true/false/case-insensitive; `_extract_retry_after_seconds` from dict / attribute / regex / garbage / preferred-source / int-coercion / None-fallback.
- **`TestFloodAwareRetry`** (12 async tests): flood-path waits parsed retry_after from all three sources; cap-at-60s; floor-at-3s; default-5s fallback; non-flood exponential-backoff regression guard; end-to-end flood-twice-then-succeed; distinct-log-line verification.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Flood errors never entered the retry loop**
- **Found during:** Task 2 RED phase (async tests all fell through to plain-text fallback)
- **Issue:** The plan's `<action>` said to modify only the `if is_network:` branch. But `_RETRYABLE_ERROR_PATTERNS` intentionally excludes flood markers (it's connection-error-only), and `SendResult.retryable` defaults to False, so `is_network` evaluated False for flood errors. They never reached the new flood branch — they fell through to plain-text fallback. The flood feature was unreachable as specified.
- **Fix:** Broadened the entry condition to `result.retryable or self._is_retryable_error(error_str) or self._is_flood_error(error_str)`. Also updated the mid-loop break check (line 3584) to OR-in `is_flood` so persistent flood windows don't break out of the retry loop early.
- **Files modified:** `gateway/platforms/base.py`
- **Commit:** `dda0e6c1a`

**2. [Rule 1 - Bug] Test error strings lacked flood markers**
- **Found during:** Task 2 GREEN phase (3 tests failed with strings like "Retry in 18 seconds")
- **Issue:** `_is_flood_error` requires substring markers ("flood", "retry after", "rate limit", "429") — mirroring `stream_consumer._is_flood_error`. Error strings like `"Retry in 18 seconds"` match the `_FLOOD_RETRY_AFTER_RE` regex but not the flood-marker check, so they never entered the flood branch. The plan's behavior spec (lines 203-209) used these bare strings, but they're inconsistent with the documented detection contract.
- **Fix:** Updated the three affected tests to prefix the error with `"flood: "` so the detection contract is exercised. The regex-only parse path is still tested via `test_flood_retry_after_from_regex_only`.
- **Files modified:** `tests/gateway/test_send_retry.py`
- **Commit:** `dda0e6c1a`

**3. [Rule 1 - Bug] "retry after 30" without "seconds" suffix not parseable**
- **Found during:** Task 1 GREEN phase (2 helper tests failed)
- **Issue:** The plan's `<interfaces>` block and `<action>` both specify `_FLOOD_RETRY_AFTER_RE = re.compile(r"retry\s*(?:in|after)\s+(\d+)\s*seconds?", re.IGNORECASE)` — byte-identical to `stream_consumer.py`. The trailing `seconds?` is required. But the plan's `<behavior>` (lines 145, 150) listed `"retry after 30"` (no suffix) as a parseable case — internally inconsistent.
- **Fix:** Aligned the two affected tests with the regex contract (added `" seconds"` suffix). The bare `"retry after 30"` form is still detected as a flood error via `_is_flood_error` substring match and falls through to `_FLOOD_WAIT_DEFAULT_SECONDS` (5s) in the retry path.
- **Files modified:** `tests/gateway/test_send_retry.py`
- **Commit:** `041303a37`

## Verification Results

- **Unit tests:** 70/70 pass in `tests/gateway/test_send_retry.py` (35 pre-existing + 23 helper + 12 async flood). Zero regressions.
- **Lint:** `ruff` is not installed in the project's environment (tooling gap, out of scope). Manual CLAUDE.md compliance checks pass:
  - No new `open()` calls introduced (PLW1514 N/A).
  - Both new `logger.warning` calls use lazy %-formatting with positional args — no f-strings in logger calls.
- **Scope hygiene:** Only `gateway/platforms/base.py` + `tests/gateway/test_send_retry.py` modified by this task. The pre-existing WIP files (`gateway/platforms/telegram.py`, `gateway/stream_consumer.py`, `tests/gateway/test_stream_consumer_flood_suspend.py`, `.planning/debug/`) remain in their uncommitted state — the user handles those separately.

## Pattern Parity Spot-Check

- `_FLOOD_RETRY_AFTER_RE` in base.py is byte-identical to `stream_consumer._FLOOD_RETRY_AFTER_RE` (regex string `r"retry\s*(?:in|after)\s+(\d+)\s*seconds?"` with `re.IGNORECASE`).
- The clamp formula `max(_FLOOD_WAIT_MIN_SECONDS, min(secs, _FLOOD_WAIT_MAX_SECONDS))` matches `stream_consumer._apply_flood_suspend` (lines 1067-1068) — identical structure, renamed constants.
- The three-source fallback order (dict -> attribute -> regex) matches `stream_consumer._extract_retry_after_seconds` (lines 1035-1053) — same try/except wrap, same None-return contract.

## Commits

| Hash | Message |
|------|---------|
| `041303a37` | `test(260626-rq4): add flood-aware retry helpers (RED+GREEN)` |
| `dda0e6c1a` | `feat(260626-rq4): wire flood-aware wait path into _send_with_retry` |

## Self-Check: PASSED

- `gateway/platforms/base.py` — FOUND (constants at lines ~1696-1708; helpers at lines ~3402-3463; flood branch in `_send_with_retry` at lines ~3565-3605)
- `tests/gateway/test_send_retry.py` — FOUND (TestFloodModuleConstants, TestFloodAwareRetryHelpers, TestFloodAwareRetry classes added)
- Commit `041303a37` — FOUND in `git log`
- Commit `dda0e6c1a` — FOUND in `git log`
