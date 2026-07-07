---
phase: 59-aux-pool-isolation
plan: 02
subsystem: credential-pool
tags: [credential-pool, tpm-tracking, sliding-window, glm, key-selection, throttle]
requires:
  - 59-01 (named pools — load_aux_pool + load_named_pool)
  - 58-01 (RPM token bucket + _capture_usage chokepoint)
provides:
  - "Per-key TPM tracking with sliding 60s window (TpmWindow dataclass)"
  - "select_freshest_tpm() key selection (max remaining TPM)"
  - "record_usage() post-call hook with auth.json persistence"
  - "tpm_warning emission in acquire_slot when all keys < 10% remaining"
  - "_LAST_SELECTED_AUX_ENTRY_ID tracker for cross-call attribution"
affects:
  - "agent/credential_pool.py — PooledCredential TPM fields, CredentialPool.select_freshest_tpm / record_usage / pool_tpm_status, storage_key param"
  - "agent/glm_throttle.py — _check_aux_pool_tpm + _resolve_tpm_warning_threshold + acquire_slot integration"
  - "agent/auxiliary_client.py — _LAST_SELECTED_AUX_ENTRY_ID, _capture_usage record_usage wire-in, _select_pool_entry tracker set/clear"
  - "cli-config.yaml.example — auxiliary.tpm_warning_threshold documentation"
tech-stack:
  added: []
  patterns:
    - "Sliding-window rate tracker (60s monotonic, lazy-init, reset-on-slide)"
    - "Best-effort refinement gate (TPM check wraps in try/except; RPM token-bucket continues on any failure)"
    - "Storage-key override for named pools (preserves namespace isolation at the disk boundary)"
key-files:
  created:
    - tests/agent/test_credential_pool_tpm_tracking.py
    - tests/agent/test_glm_throttle_tpm.py
    - tests/agent/test_auxiliary_client_tpm_recording.py
  modified:
    - agent/credential_pool.py
    - agent/glm_throttle.py
    - agent/auxiliary_client.py
    - cli-config.yaml.example
decisions:
  - "TPM cap hardcoded at 200_000/key (GLM-5.2 ceiling) per CONTEXT.md deferred list — configurable in v13+"
  - "tpm_warning_threshold default 0.1 (10%), overridable via auxiliary.tpm_warning_threshold in cli-config.yaml"
  - "select_freshest_tpm bypasses the configured pool strategy (fill_first/round_robin) — TPM freshness always wins for the aux pool"
  - "record_usage persists to auth.json on every aux call (~30 RPM/task) so the gateway process and parallel CLI round-table drivers see consistent TPM state"
  - "TPM check failure is best-effort — any exception in _check_aux_pool_tpm is swallowed at debug; the RPM token-bucket pacer continues"
metrics:
  duration: "~3 hours"
  completed: 2026-07-08
  tasks: 3
  files_created: 3
  files_modified: 4
  tests_added: 19
---

# Phase 59 Plan 02: Per-Key TPM Tracking Summary

**One-liner:** Sliding-60s per-key TPM tracker on the auxiliary pool with freshest-key selection, post-call `record_usage` decrement, and `tpm_warning` emission when all keys drop below 10% remaining — eliminates the "round table fails halfway through" failure mode by proactively pacing the aux pool instead of reactively handling 429s.

## What Shipped

### Task 1 — TpmWindow dataclass + CredentialPool methods (TDD)

**RED→GREEN cycle:**
- `tests/agent/test_credential_pool_tpm_tracking.py` (9 tests): fresh entry has None TPM fields, record_usage initializes / accumulates / resets window, TPM_CAP_PER_KEY_GLM == 200_000, default-pool entries unaffected, unknown entry_id is a no-op + debug log, select_freshest_tpm picks highest-remaining entry, select_freshest_tpm returns None on empty pool.
- `agent/credential_pool.py`:
  - Module constant `TPM_CAP_PER_KEY_GLM: int = 200_000` (CONTEXT.md deferred list).
  - Module constant `TPM_WINDOW_SECONDS: float = 60.0`.
  - `PooledCredential.tokens_this_minute: Optional[int] = None` + `window_start: Optional[float] = None` — Optional + None default so default-pool entries load cleanly.
  - `TpmWindow` dataclass with `fresh()`, `remaining(cap)`, `remaining_fraction(cap)`, `window_remaining_seconds(now)`, `record(tokens, now)`. Defensive clamps for negative inputs (T-59-08-T mitigation).
  - `CredentialPool.select_freshest_tpm(cap=...)`: returns the entry with the most remaining TPM. Bypasses configured strategy (fill_first/round_robin). NO-OP on entries with `tokens_this_minute=None`.
  - `CredentialPool.record_usage(entry_id, tokens)`: lazy-init TpmWindow, slide-on-expire, persist to auth.json via `_persist()`.
  - `CredentialPool.pool_tpm_status(cap=...)`: returns `{entry_id: {remaining_tokens, window_remaining_s, remaining_fraction, tokens_consumed}}` — read-only snapshot for throttle layer decisions.
  - **BUG FIX:** `CredentialPool.__init__` now accepts `storage_key: Optional[str]` kwarg. `_persist` writes to `self._storage_key` instead of `self.provider`. Named pools (`auxiliary:zai`) pass the explicit pool_key so `_persist` writes to the correct namespace. Previously the Phase 59-01 implementation wrote to `self.provider` ("zai"), clobbering the default pool's namespace and losing TPM state on reload.

### Task 2 — tpm_warning emission in acquire_slot

- `agent/glm_throttle.py`:
  - `_TPM_WARNING_THRESHOLD_DEFAULT = 0.1` module constant.
  - `_resolve_tpm_warning_threshold()`: reads `auxiliary.tpm_warning_threshold` from cli-config.yaml with `[0.0, 1.0]` range validation, falls back to default on any error.
  - `_check_aux_pool_tpm(pool_name)`: best-effort TPM availability check. Loads aux pool via `load_named_pool("auxiliary", "zai")`, reads `pool_tpm_status()`, emits `tpm_warning` log + brief sleep (capped at 60s) when ALL keys below threshold. Returns early for non-aux pool names. Swallows all exceptions at debug level.
  - `acquire_slot`: short-circuits the TPM check when `pool_name != "auxiliary"` (load-bearing — Test 5 verifies the helper is NEVER called for default-pool callers). For aux pool, wraps `_check_aux_pool_tpm` in try/except so a buggy TPM path can never wedge the RPM pacer.
- `tests/agent/test_glm_throttle_tpm.py` (5 tests): all-keys-below-threshold emits warning, one-remaining no-warning, empty pool no-crash, TPM-check-failure no-crash, default-pool-name skips check entirely.

### Task 3 — record_usage wire-in + integration

- `agent/auxiliary_client.py`:
  - Module-level `_LAST_SELECTED_AUX_ENTRY_ID: Optional[str] = None` (T-59-11-E: cleared on default-pool select so default-pool usage never attributes TPM to the aux pool).
  - `_select_pool_entry`: when `pool_name == "auxiliary"` AND entry selected, records `entry.id` in the tracker. When `pool_name == "default"`, clears the tracker.
  - `_capture_usage`: after updating `_LAST_CALL_USAGE`, reads `_LAST_SELECTED_AUX_ENTRY_ID`, calls `credential_pool.load_named_pool("auxiliary", "zai").record_usage(entry_id, total_tokens)`. Best-effort — failures logged at debug and swallowed.
- `cli-config.yaml.example`: documents `auxiliary.tpm_warning_threshold` (default 0.1) with usage example, cross-referenced with the existing `GLM_AUX_API_KEY_1..4` block.
- `tests/agent/test_auxiliary_client_tpm_recording.py` (5 tests): successful call records total_tokens, error path no-mutation, default-pool no-attribution, sequential accumulation, persistence across reloads.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Storage namespace collision for named pools**
- **Found during:** Task 3 (Test 5 — persistence across reloads)
- **Issue:** `CredentialPool._persist()` wrote to `self.provider` ("zai"), NOT to the named pool's storage key ("auxiliary:zai"). This meant `record_usage` writes landed in the default pool's namespace, AND `_seed_aux_env` on the next `load_aux_pool` call re-seeded from env vars (losing the persisted TPM state). The Phase 59-01 `load_named_pool` constructor passed only `provider`, not the storage key.
- **Fix:** Added `storage_key: Optional[str] = None` kwarg to `CredentialPool.__init__`. `_persist` writes to `self._storage_key` (defaults to `self.provider` for backward compat). `load_named_pool` passes `storage_key=pool_key` so named pools persist to their own namespace.
- **Files modified:** `agent/credential_pool.py`
- **Commit:** 1af52b853 (Task 3)

**2. [Rule 1 - Bug] acquire_slot invoked TPM check for default pool_name**
- **Found during:** Task 2 (Test 5 — default pool_name skips TPM check)
- **Issue:** The first implementation called `_check_aux_pool_tpm(pool_name)` unconditionally and relied on the helper's internal `pool_name != "auxiliary"` early-return. The test contract was stricter: the helper must NEVER be invoked for default-pool callers (cheaper + auditable via monkeypatch).
- **Fix:** Wrapped the `_check_aux_pool_tpm` call in `if pool_name == "auxiliary":` in `acquire_slot`. The helper still has its own early-return as defense-in-depth.
- **Files modified:** `agent/glm_throttle.py`
- **Commit:** 3d46b1ec5 (Task 2)

## Test Results

All 19 new tests pass. All 22 pre-existing Phase 58 + 59-01 tests still pass (zero regression):

```
tests/agent/test_credential_pool_tpm_tracking.py .........      (9 tests)
tests/agent/test_glm_throttle_tpm.py .....                     (5 tests)
tests/agent/test_auxiliary_client_tpm_recording.py .....       (5 tests)
+ test_credential_pool_aux_isolation.py, test_glm_throttle.py,
  test_auxiliary_client_aux_pool.py — all green (22 tests)
```

Pre-existing failure: `tests/agent/test_credential_pool_routing.py::TestCliTurnRoutePool::test_resolve_turn_includes_pool` — environmental (missing `prompt_toolkit` module in this sandbox). Unrelated to Phase 59-02; verified by running the same test against a clean checkout (HEAD~4).

## Verification Checks

| Check | Result |
|---|---|
| `grep -c "TPM_CAP_PER_KEY_GLM\|select_freshest_tpm\|record_usage\|TpmWindow" agent/credential_pool.py` | 21 (≥4 required) ✅ |
| `grep -c "tpm_warning\|_check_aux_pool_tpm\|_TPM_WARNING_THRESHOLD" agent/glm_throttle.py` | 22 (≥3 required) ✅ |
| `grep -c "_LAST_SELECTED_AUX_ENTRY_ID\|record_usage" agent/auxiliary_client.py` | 11 (≥2 required) ✅ |
| `grep -c "tpm_warning_threshold" cli-config.yaml.example` | 2 (≥1 required) ✅ |
| Manual REPL spot-check: `load_aux_pool("zai")` + `select_freshest_tpm()` + `TPM_CAP_PER_KEY_GLM` | Returns `(None, 200000)` when no GLM keys configured — correct ✅ |

## TDD Gate Compliance

- RED commit `f2884124d` exists: `test(59-02): add failing tests for per-key TPM sliding window`
- GREEN commit `65c52eaca` exists: `feat(59-02): implement TpmWindow + select_freshest_tpm + record_usage on CredentialPool`
- Tasks 2 and 3 followed test-then-implement pattern within single commits (test scaffold + implementation together) — acceptable per plan note: "same commit acceptable for new test scaffold + new helper module when TDD RED+GREEN cycles are tight".

## Threat Model Coverage

| Threat | Mitigation Status |
|---|---|
| T-59-07-S (upstream usage spoofing) | ✅ accept — upstream under-reporting surfaces as 429 → existing mark_exhausted_and_rotate flow |
| T-59-08-T (auth.json tampering) | ✅ mitigate — `TpmWindow.record` clamps negative inputs to 0; lazy-init treats None as "start fresh" |
| T-59-09-R (cross-process repudiation) | ✅ mitigate — `record_usage` calls `_persist()` so gateway + CLI see consistent state. Verified by Test 5 (Task 3). |
| T-59-10-D (round-table TPM DoS) | ✅ mitigate — core threat POOL-02 addresses: `select_freshest_tpm` distributes, `tpm_warning` + sleep prevents simultaneous exhaustion |
| T-59-11-E (record_usage on default-pool entry) | ✅ mitigate — `_LAST_SELECTED_AUX_ENTRY_ID` set ONLY on aux-pool select, cleared on default-pool select. Verified by Test 3 (Task 3). |

## Self-Check: PASSED

- `tests/agent/test_credential_pool_tpm_tracking.py` — FOUND ✅
- `tests/agent/test_glm_throttle_tpm.py` — FOUND ✅
- `tests/agent/test_auxiliary_client_tpm_recording.py` — FOUND ✅
- `agent/credential_pool.py` modified — FOUND ✅ (TpmWindow, select_freshest_tpm, record_usage, pool_tpm_status, storage_key)
- `agent/glm_throttle.py` modified — FOUND ✅ (_check_aux_pool_tpm, _resolve_tpm_warning_threshold)
- `agent/auxiliary_client.py` modified — FOUND ✅ (_LAST_SELECTED_AUX_ENTRY_ID, _capture_usage wire-in, _select_pool_entry tracker)
- Commit f2884124d (RED) — FOUND ✅
- Commit 65c52eaca (GREEN Task 1) — FOUND ✅
- Commit 3d46b1ec5 (Task 2) — FOUND ✅
- Commit 1af52b853 (Task 3) — FOUND ✅
