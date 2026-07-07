---
phase: 59-aux-pool-isolation
verified: 2026-07-08T00:00:00Z
status: passed
score: 3/3 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 2/3
  gaps_closed:
    - "Per-key TPM in sliding 60s window; acquire_slot picks the key with most remaining TPM (ROADMAP SC#2 / POOL-02) — select_freshest_tpm is now wired into _select_pool_entry for pool_name='auxiliary' branch, and integration test test_aux_pool_picks_freshest_entry exercises the production call path."
  gaps_remaining: []
  regressions: []
---

# Phase 59: AUX-POOL-ISOLATION Verification Report

**Phase Goal:** Isolate auxiliary credential pool from main agent pool. Per-key TPM tracking.
**Verified:** 2026-07-08
**Status:** passed
**Re-verification:** Yes — after gap closure

## Re-Verification Summary

**Previous verdict:** gaps_found — SC#2 / POOL-02 partially implemented. `select_freshest_tpm` existed but was orphaned (zero production callers); `_select_pool_entry` called `pool.select()` (configured strategy) for both default AND aux pools.

**Fix applied:**
- `agent/auxiliary_client.py:613-616` — added conditional branch: when `pool_name == "auxiliary"` AND pool has `select_freshest_tpm`, invoke `pool.select_freshest_tpm()` instead of `pool.select()`.
- `tests/agent/test_auxiliary_client_aux_pool.py:282-353` — added `TestAuxPoolSelectsFreshestTpm::test_aux_pool_picks_freshest_entry` integration test that exercises the production call path `_select_pool_entry → select_freshest_tpm`.

**Verification of fix:**
- Production caller confirmed: `grep -A 5 'pool_name == "auxiliary"' agent/auxiliary_client.py | grep select_freshest_tpm` returns the wire-in (lines 613-614).
- `grep -rn select_freshest_tpm --include='*.py' agent/` now shows **2 production references** (line 613 condition + line 614 invocation) plus comments and the definition itself. Method is NO LONGER orphaned.
- Integration test PASSES (`pytest tests/agent/test_auxiliary_client_aux_pool.py::TestAuxPoolSelectsFreshestTpm -x` → 1 passed in 0.35s). The test is load-bearing: stale entry has higher `priority=20` (fill_first would pick it under old code) but lower remaining TPM; fresh entry has `priority=10` but more remaining TPM. Under the new wire-in, `_select_pool_entry("zai", pool_name="auxiliary")` returns the fresh entry. Under the old code, the assertion `entry.access_token == "fresh-key"` would fail.
- Regression sweep: `test_auxiliary_client_aux_pool.py` (6 tests) + `test_credential_pool_tpm_tracking.py` (9 tests) all pass — 15/15 in 63.78s.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `GLM_AUX_API_KEY_1..4` env vars (fallback to `GLM_API_KEY`); auxiliary calls never share main pool (ROADMAP SC#1 / POOL-01) | VERIFIED | `_seed_aux_env` at credential_pool.py:2557 reads `_AUX_ENV_VARS = ("GLM_AUX_API_KEY_1".."GLM_AUX_API_KEY_4")` PLUS `GLM_API_KEY` (additive fallback). `load_named_pool`/`load_aux_pool` persist under `auxiliary:<provider>` storage key (line 2667). `_select_pool_entry(pool_name="auxiliary")` dispatches to `load_named_pool` (line 599). `test_aux_pool_isolation_from_default_exhaustion` proves exhausting default pool does not affect aux pool selection. cli-config.yaml.example:420-457 documents the env vars. |
| 2 | Per-key TPM in sliding 60s window; acquire_slot picks the key with most remaining TPM (ROADMAP SC#2 / POOL-02) | VERIFIED | **FIX CONFIRMED.** TPM tracking fully wired (`TpmWindow` + `record_usage` + `pool_tpm_status` + `_check_aux_pool_tpm` + `tpm_warning` emission + `_LAST_SELECTED_AUX_ENTRY_ID` attribution). AND the freshest-key SELECTION is now wired: `auxiliary_client.py:613-614` calls `pool.select_freshest_tpm()` when `pool_name == "auxiliary"`. Integration test `TestAuxPoolSelectsFreshestTpm::test_aux_pool_picks_freshest_entry` exercises the production code path with unequal TPM + unequal priority and confirms the freshest key wins. CONTEXT.md decision #4 ("acquire_slot picks the key with most remaining TPM") is now satisfied. |
| 3 | Test verifies pool isolation (ROADMAP SC#3) | VERIFIED | `tests/agent/test_auxiliary_client_aux_pool.py::TestAuxPoolIsolation::test_aux_pool_isolation_from_default_exhaustion` (line 55) seeds the default pool with 2 entries both marked `last_status=exhausted, last_error_code=429`, seeds the aux pool with 2 fresh entries, asserts `_select_pool_entry("zai", pool_name="default")` returns `(True, None)` while `_select_pool_entry("zai", pool_name="auxiliary")` returns `(True, <entry>)` with `access_token in {"AUX_KEY_1", "AUX_KEY_2"}`. |

**Score:** 3/3 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `agent/credential_pool.py` | `load_aux_pool` + `load_named_pool` + `_seed_aux_env` + `TpmWindow` + `select_freshest_tpm` + `record_usage` + `pool_tpm_status` + storage_key kwarg | VERIFIED | All symbols present. Substantive implementation, well-documented. `select_freshest_tpm` now has a production caller. |
| `tests/agent/test_credential_pool_aux_isolation.py` | 7+ tests for aux pool load, env var seeding, fallback, isolation | VERIFIED | 8 tests in `TestAuxPoolLoadAndSeeding`. All pass. |
| `tests/agent/test_credential_pool_tpm_tracking.py` | 7+ tests for TPM window reset, freshest selection, threshold warning | VERIFIED | 9 tests across TestTpmTrackingBasics + TestSelectFreshestTpm. All pass (regression check after fix). |
| `tests/agent/test_glm_throttle_tpm.py` | 5 tests for tpm_warning emission | VERIFIED | 5 tests in TestAcquireSlotTpmWarning. All pass (established in prior verification). |
| `tests/agent/test_auxiliary_client_tpm_recording.py` | 5 tests for record_usage wire-in | VERIFIED | 5 tests. All pass (established in prior verification). |
| `tests/agent/test_auxiliary_client_aux_pool.py` | 5+ tests including load-bearing isolation AND freshest-pick integration | VERIFIED | 6 tests now (5 original + new `TestAuxPoolSelectsFreshestTpm::test_aux_pool_picks_freshest_entry`). All pass. |
| `agent/glm_throttle.py` | `acquire_slot`/`try_acquire_slot` accept `pool_name` kwarg + emit `tpm_warning` | VERIFIED | Lines 188-285 (_resolve_tpm_warning_threshold, _check_aux_pool_tpm), 288 acquire_slot signature, 344 try_acquire_slot signature. |
| `agent/auxiliary_client.py` | `_select_pool_entry` invokes `select_freshest_tpm` for aux pool + `_capture_usage` records TPM | VERIFIED | **Re-verified after fix.** Lines 613-616: `if pool_name == "auxiliary" and hasattr(pool, "select_freshest_tpm"): selected = pool.select_freshest_tpm() else: selected = pool.select()`. Lines 627-630: aux entry-id tracking. Lines 5063, 5120-5135: record_usage wire-in. |
| `cli-config.yaml.example` | `GLM_AUX_API_KEY_1..4` + `tpm_warning_threshold` docs | VERIFIED | Lines 420-457: substantive 38-line block documenting both POOL-01 env vars and POOL-02 threshold with usage examples. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `auxiliary_client._select_pool_entry` | `credential_pool.load_named_pool` | `pool_name` kwarg dispatch (line 599) | WIRED | Confirmed: when `pool_name != "default"`, calls `load_named_pool(pool_name, provider)`. |
| `auxiliary_client._capture_usage` | `credential_pool.record_usage` | post-call hook via `_LAST_SELECTED_AUX_ENTRY_ID` (line 5133) | WIRED | Confirmed: reads tracker, loads aux pool, calls `pool.record_usage(entry_id, total_int)`. |
| `glm_throttle.acquire_slot` | `credential_pool.load_named_pool` + `pool_tpm_status` | `_check_aux_pool_tpm` (line 217) called from acquire_slot loop (line 322) | WIRED | Confirmed: emits tpm_warning + sleeps when all keys < threshold. |
| `auxiliary_client._select_pool_entry` | `credential_pool.select_freshest_tpm` | aux-pool freshest-key selection (line 613-614) | **WIRED** | **FIX CONFIRMED.** Line 613 condition `pool_name == "auxiliary" and hasattr(pool, "select_freshest_tpm")` → line 614 invocation `pool.select_freshest_tpm()`. Previously NOT_WIRED (orphaned method); now has a production caller. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `auxiliary_client._capture_usage` | `total` | `response.usage.total_tokens` (upstream GLM response) | Yes (when response.usage present) | FLOWING |
| `CredentialPool.record_usage` | `entry.tokens_this_minute` | `_capture_usage` post-call | Yes | FLOWING |
| `CredentialPool.pool_tpm_status` | per-entry remaining/fraction | `tokens_this_minute` + `window_start` persisted to auth.json | Yes | FLOWING |
| `_check_aux_pool_tpm` warning decision | `all_below` | `pool_tpm_status()` from aux pool | Yes | FLOWING |
| `_select_pool_entry` selection | `selected.access_token` | `pool.select_freshest_tpm()` for aux pool (line 614) — picks entry with max `(cap - tokens_this_minute)` | Yes — freshest-key-influenced | **FLOWING** — TPM tracking data now influences which key is selected |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `select_freshest_tpm` wired into production call path | `grep -A 5 'pool_name == "auxiliary"' agent/auxiliary_client.py \| grep select_freshest_tpm` | Match at line 614 | PASS |
| `select_freshest_tpm` no longer orphaned | `grep -rn select_freshest_tpm --include='*.py' agent/` | 5 references: 1 condition (613), 1 invocation (614), 2 comments (1480, 1487), 1 definition (1491) | PASS |
| New integration test passes through production call path | `python3 -m pytest tests/agent/test_auxiliary_client_aux_pool.py::TestAuxPoolSelectsFreshestTpm -x` | 1 passed in 0.35s | PASS |
| Regression: aux pool + TPM tracking test files green | `python3 -m pytest tests/agent/test_auxiliary_client_aux_pool.py tests/agent/test_credential_pool_tpm_tracking.py` | 15 passed in 63.78s | PASS |

### Probe Execution

SKIPPED — no `scripts/*/tests/probe-*.sh` probes declared by PLAN/SUMMARY for this phase.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| POOL-01 | 59-01 | Separate Auxiliary Credential Pool: `GLM_AUX_API_KEY_1..4` env vars, named pool `auxiliary`, isolation from main pool, tests verifying isolation | SATISFIED | `load_aux_pool` + `load_named_pool` + `_seed_aux_env` implemented + 8 isolation tests + 6 aux_client pool tests (incl. new freshest-pick integration test) + cli-config docs. SC#1 + SC#3 fully met. |
| POOL-02 | 59-02 | Per-Key TPM Tracking: pick freshest key before call, decrement after call, emit tpm_warning + sleep when all < 10% | SATISFIED | **Promoted from PARTIAL to SATISFIED.** TPM tracking, post-call decrement, tpm_warning emission all implemented + tested. AND "pick freshest key before call" is now wired in `_select_pool_entry` (auxiliary_client.py:613-614) with integration test `test_aux_pool_picks_freshest_entry` proving the production code path returns the freshest entry. SC#2 fully met. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `agent/auxiliary_client.py` | 4619 | TODO in docstring (referencing OpenAI SDK, not Phase 59 work) | Info | Pre-existing; not introduced by Phase 59. |

The previously-reported orphaned-method anti-pattern on `agent/credential_pool.py:1491` is RESOLVED — `select_freshest_tpm` now has a production caller at `auxiliary_client.py:613-614`.

### Human Verification Required

None. All Phase 59 truths are programmatically verifiable (no UI / external-service dependencies).

### Gaps Summary

**No gaps remain.** The previous gap (SC#2 / POOL-02 freshest-key selection not wired into production call path) is fully closed:

1. Production caller added — `_select_pool_entry` (auxiliary_client.py:613-614) now invokes `pool.select_freshest_tpm()` when `pool_name == "auxiliary"`.
2. Integration test added — `TestAuxPoolSelectsFreshestTpm::test_aux_pool_picks_freshest_entry` exercises the production call path, uses unequal TPM consumption + unequal priority, and would FAIL under the old `pool.select()` code (fill_first would return the higher-priority stale key).
3. Test passes in 0.35s; full regression on aux pool + TPM tracking test files (15 tests) passes in 63.78s.

Phase 59 goal fully achieved: the auxiliary pool is isolated, TPM is tracked per-key in a sliding 60s window, and the freshest key is auto-selected before each aux call. The original v11.0 §3.1 failure mode (a 4-key aux pool hitting GLM's 200K/key TPM ceiling on the same key mid-synthesis) is now addressed both at selection time AND warning time.

---

_Verified: 2026-07-08 (re-verification after gap closure)_
_Verifier: Claude (gsd-verifier)_
