---
phase: quick-260702-o1a
plan: 01
subsystem: agent-runtime
tags: [credential-pool, failover, glm, overloaded, rotation, incident-fix]
requires:
  - "agent/credential_pool.py (mark_exhausted_and_rotate, _select_unlocked, _available_entries)"
  - "agent/agent_runtime_helpers.py (recover_with_credential_pool)"
  - "agent/error_classifier.py (FailoverReason.overloaded)"
  - "quick-260702-ezx (3-strike abort + 30s/600s backoff + concurrency guard)"
provides:
  - "CredentialPool.rotate_to_next() — non-mutating rotation for FailoverReason.overloaded"
  - "overloaded branch in recover_with_credential_pool that preserves key health"
affects:
  - "Multi-key GLM setups (Kai's 4-key rotation) during provider-side capacity storms"
  - "Any pooled-credential provider where FailoverReason.overloaded (503/529/1305) fires"
tech-stack:
  added: []
  patterns:
    - "non-mutating rotation via exclusion set (filter previous_id from candidates instead of marking exhausted)"
    - "compose cleanly with conversation-loop-level termination (ezx 3-strike abort)"
key-files:
  created:
    - tests/agent/test_credential_pool_overloaded_rotation.py
  modified:
    - agent/credential_pool.py
    - agent/agent_runtime_helpers.py
decisions:
  - "Exclusion-set rotation over cycle-back detection — plan's original next.id == previous_id check doesn't work because _select_unlocked re-picks the same lowest-priority entry; filtering previous_id from candidates achieves real rotation"
  - "Pool loops on healthy multi-key setups by design — ezx 3-strike abort at conversation-loop level handles termination; pool only yields when genuinely no alternative exists"
  - "Added overloaded branch directly (no pre-existing branch to replace) — base commit 39da07ac had no overloaded handling in recover_with_credential_pool; ezx's note 'do not touch agent_runtime_helpers.py' meant ezx didn't add it, this fix adds the correct version directly"
metrics:
  duration: ~25m
  completed: 2026-07-02
  tasks: 1
  files: 3
  tests-added: 11
---

# Phase quick-260702-o1a Plan 01: Credential-Pool Overloaded Rotation Fix Summary

Non-mutating `CredentialPool.rotate_to_next()` for `FailoverReason.overloaded` (1305/503/529) — stops the silent rotation-death that killed Kai's 4-key GLM setup three times on 2026-07-02.

## What Shipped

**Bug fixed:** The `FailoverReason.overloaded` branch in `recover_with_credential_pool` called `pool.mark_exhausted_and_rotate()`, which permanently marked the current key `STATUS_EXHAUSTED` — identical to billing exhaustion. But 1305 ("model capacity exceeded") means the MODEL is overloaded, not that the KEY's quota is gone. After N× 1305 across an N-key pool, all keys were marked exhausted → recovery became a no-op → user saw "model provider failed after retries". Manual cleanup of `~/.hermes/auth.json` was required after each storm.

**Fix:** New `CredentialPool.rotate_to_next()` advances `_current_id` to the next available entry WITHOUT calling `_mark_exhausted`. Uses an exclusion-set approach (filters `previous_id` out of candidates) so the same key is never immediately re-selected. The overloaded branch in `recover_with_credential_pool` now calls `rotate_to_next()`; billing (402) and rate_limit (429) branches unchanged.

**Composition with ezx (quick-260702-ezx):** On a healthy multi-key pool, `rotate_to_next` keeps offering alternatives so the pool survives transient capacity storms. The conversation-loop-level ezx 3-strike abort (`consecutive_overloaded >= 3`) surfaces "GLM model overloaded" after 3 consecutive 1305s. When the pool genuinely has no alternative (single-key setup or all-but-one exhausted), `rotate_to_next` returns None and recovery yields cleanly.

## Files

| File | Change | Lines |
|------|--------|-------|
| `agent/credential_pool.py` | New `rotate_to_next()` method after `mark_exhausted_and_rotate` | +108 |
| `agent/agent_runtime_helpers.py` | New overloaded branch in `recover_with_credential_pool` | +27 |
| `tests/agent/test_credential_pool_overloaded_rotation.py` | 11 tests (pool-level + integration + regression + E2E) | +411 |

## Test Results

- **New tests:** 11/11 passed (`tests/agent/test_credential_pool_overloaded_rotation.py`)
- **Pool regression:** 90/90 passed (`test_credential_pool.py` + `test_custom_pool_mismatch_guard.py` + `test_credential_pool_routing.py` minus 2 CLI-import-blocked tests)
- **ezx regression:** 35/35 passed (`test_glm_concurrency_guard.py` + `test_retry_utils_overloaded.py`)
- **Ruff:** Not runnable in this env (ruff not installed) — manually verified PLW1514 compliance (no new `open()` calls; all `logger.info` use `%s` positional args)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Plan assumed pre-existing overloaded branch; base commit had none**

- **Found during:** Task 1 implementation
- **Issue:** The plan's `<interfaces>` section quoted "current overloaded branch (lines 675-690)" in `agent/agent_runtime_helpers.py` and the `<action>` said "replace the body of the `if effective_reason == FailoverReason.overloaded:` block". But base commit `39da07ac` had NO overloaded branch in `recover_with_credential_pool` — only `billing`, `rate_limit`, and `auth` branches existed. The ezx quick task (commit `4b821c29b`) explicitly noted "Do NOT touch agent_runtime_helpers.py" and never added one.
- **Fix:** Added the overloaded branch directly with the correct behavior (calling `pool.rotate_to_next()`), rather than first adding a buggy version then fixing it. End state identical to what the plan specifies. Documented in commit message.
- **Files modified:** `agent/agent_runtime_helpers.py`
- **Commit:** 5839b5f78

**2. [Rule 1 - Bug] Plan's rotate_to_next implementation didn't actually rotate**

- **Found during:** Task 1 GREEN phase (Test 1 + Test 2 failed)
- **Issue:** The plan's specified implementation (set `_current_id = None`, call `_select_unlocked`) doesn't achieve rotation in any strategy. In `fill_first`, `_select_unlocked` always picks the lowest-priority available entry — after clearing `_current_id`, it re-picks the same entry. The plan's `next_entry.id == previous_id` cycle check then fires immediately, returning None on the first call. In `round_robin`, `_select_unlocked` pops from the front of `available` (which is sorted by priority) — same effect.
- **Fix:** Replaced the "clear and re-select" approach with an exclusion-set approach: filter `previous_id` out of `_available_entries()` candidates, then pick from the filtered set using the configured strategy. This achieves real rotation across all 4 strategies (fill_first, round_robin, least_used, random).
- **Files modified:** `agent/credential_pool.py`
- **Commit:** 5839b5f78

**3. [Rule 1 - Bug] Test expectations for cycle behavior were wrong**

- **Found during:** Task 1 GREEN phase (Test 2 + Test 11 failed)
- **Issue:** Tests assumed `rotate_to_next` would give up after `pool_size - 1` rotations (cycle-back detection). But the plan's own `<implementation_note>` point 2 clarifies: "the pool doesn't need to give up — the conversation loop does (via ezx 3-strike abort)". On a healthy multi-key pool, rotation SHOULD cycle indefinitely through distinct entries.
- **Fix:** Rewrote Test 2 to verify each rotation yields a DIFFERENT entry (no tight A→A loop). Rewrote Test 11 to verify (a) no key marked exhausted across 4× 1305, (b) rotation distributes across ≥3 keys, (c) all calls return `(True, False)`. Added Test 12 (`test_overloaded_yields_when_pool_has_no_alternative`) covering the actual must-have truth #2 scenario: single-entry pool returns `(False, has_retried_429)` because there's genuinely no alternative.
- **Files modified:** `tests/agent/test_credential_pool_overloaded_rotation.py`
- **Commit:** 5839b5f78

### Out-of-scope discoveries (logged, NOT fixed)

- **Pre-existing env issue:** `prompt_toolkit` not installed in this worktree's Python env, blocking 2 tests in `test_credential_pool_routing.py` (`TestCliTurnRoutePool`, `TestGatewayTurnRoutePool`) that import `cli.py`. Confirmed pre-existing (fails on clean base too). NOT a regression from this change.

## Authentication Gates

None — no auth required for this fix.

## Known Stubs

None — all code paths are fully implemented and tested.

## Threat Flags

None — the threat model in the plan (T-O1A-01 through T-O1A-05) is fully mitigated:
- T-O1A-01 (infinite loop): mitigated by exclusion-set + conversation-loop ezx 3-strike
- T-O1A-02 (concurrent corruption): mitigated by `with self._lock:` (unchanged from `mark_exhausted_and_rotate`)
- T-O1A-03 (key material leak): no change — only labels/ids logged
- T-O1A-04 (rotation distinguishability): log messages include "overloaded rotation" + "(key retained)"
- T-O1A-05 (privilege escalation): N/A (accept)

## Self-Check: PASSED

- [x] `agent/credential_pool.py` exists with `rotate_to_next` method (line 1428)
- [x] `agent/agent_runtime_helpers.py` has overloaded branch calling `pool.rotate_to_next()` (line 658-684)
- [x] `tests/agent/test_credential_pool_overloaded_rotation.py` exists with 11 tests
- [x] Commit `5839b5f78` exists in git log
- [x] Single atomic commit with exactly 3 files (2 source + 1 test)
