---
phase: 81-xcut-04b-cloud-engine-bootstrap
reviewed: 2026-07-10T20:15:00Z
depth: quick
iteration: 2
files_reviewed: 2
files_reviewed_list:
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/check_cloud_engine_optin.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_check_cloud_engine_optin.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
previous_iteration:
  critical: 2
  warning: 5
  info: 4
  total: 11
---

# Phase 81: Code Review Report (Iteration 2 — Re-review)

**Reviewed:** 2026-07-10T20:15:00Z
**Depth:** quick
**Iteration:** 2 (re-review after fixes)
**Files Reviewed:** 2 (script + test; reference docs WR-02/WR-04 cross-checked)
**Status:** clean

## Summary

Re-reviewed the two source files after iteration-1 fixes. All 2 Critical and all 5 Warning findings from iteration 1 are verified resolved. No new Critical/Warning issues introduced. Test suite expanded from 23 to 29 tests, all passing.

The scope of this re-review is the 2 source files listed in `files_reviewed_list`. The two doc-level warnings (WR-02 transition-engine-routing.md, WR-04 cloud-engine-bootstrap.md) from iteration 1 were cross-checked against the reference docs and confirmed resolved, but the docs themselves are not counted as reviewed source files in this iteration.

## Fix Verification

### CR-01: Crash on non-dict `cloud_engines` block — RESOLVED

**File:** `scripts/check_cloud_engine_optin.py:194-207`
**Verification:** The value-extraction logic now sits INSIDE the try/except, AND adds an explicit `isinstance(cloud_block, dict)` guard (lines 197-201) that logs a warning and sets `cloud_block = None` on non-dict values. The "NEVER crashes" contract (D-06) now holds for list/string/int/scalar `cloud_engines` values.
**Tests added:** `test_cloud_engines_is_list`, `test_cloud_engines_is_string`, `test_cloud_engines_is_int` — all PASS.

### CR-02: `motion_vector_match` routing omits Vidu fallback — RESOLVED

**File:** `scripts/check_cloud_engine_optin.py:124`
**Verification:** `TRANSITION_ENGINE_MAP["motion_vector_match"]` is now `("hailuo", "vidu", "ffmpeg_motion_based_cut")` — Vidu inserted between Hailuo and the ffmpeg fallback. Matches the routing doc's "Hailuo / Vidu" co-primary declaration.
**Test added:** `test_motion_vector_match_vidu_fallback` — asserts `"vidu" in mvm["fallback"]` when hailuo absent + vidu present. PASS.

### WR-01: `primary_engine` shows fallback instead of declared primary — RESOLVED

**File:** `scripts/check_cloud_engine_optin.py:384`
**Verification:** Line 384 now unconditionally sets `"primary_engine": primary` (the declared primary, first in chain), no longer overwritten with `active_engine` on fallback. The Rich table "Primary Engine" column now reports the declared primary consistently; the `Available` and `Fallback` columns carry the fallback semantics.
**Test added:** `test_primary_engine_always_declared` — iterates `TRANSITION_ENGINE_MAP`, asserts `primary_engine == engine_chain[0]` for every cloud transition even when no engines are opted in. PASS. `test_hailuo_not_opted_vidu_fallback` also strengthened to assert `primary_engine == "hailuo"`.

### WR-02: TRANS-10 deferral version contradiction (v15+ vs v16+) — RESOLVED

**File:** `references/transition-engine-routing.md:77,93,97`
**Verification:** Cross-checked the doc — line 77 reads "TRANS-10 deferred to v16+", line 93 reads "v16+ may revisit", line 97 reads "deferred to v16+ per CONTEXT.md". Consistent. (Note: doc is not in this iteration's `files_reviewed_list` but was checked to confirm the warning is closed.)

### WR-03: Missing sys.path bootstrap — RESOLVED

**File:** `scripts/check_cloud_engine_optin.py:37-81`
**Verification:** Comprehensive sys.path bootstrap added (lines 37-81) with 4-tier resolution: (1) already-importable, (2) kais-hermes-skills repo root, (3) sibling `../hermes-agent` repo, (4) vendored minimal `get_hermes_home()` fallback (lines 66-81) reading `HERMES_HOME` env var with platform-native default. Script now runs standalone in any environment — verified by executing `python3 .../check_cloud_engine_optin.py --json` with `HERMES_HOME=/tmp/nonexistent` producing valid JSON + exit 0. The vendored fallback correctly mirrors `hermes_constants.get_hermes_home` core logic including the Windows `LOCALAPPDATA` path with a `Path.home()` final fallback.

### WR-04: Stray `verified_date:` line in bootstrap doc — RESOLVED

**File:** `references/cloud-engine-bootstrap.md:6`
**Verification:** Line 6 is now blank; the stray `verified_date: 2026-07` prose has been removed. The `**Last-verified:** 2026-07-10` field on line 5 carries the verification date. (Note: doc is not in this iteration's `files_reviewed_list` but was checked.)

### WR-05: `_ENV_VAR_ALIASES` private, inconsistent with public `ENV_VAR_MAP` — RESOLVED

**File:** `scripts/check_cloud_engine_optin.py:116-119`
**Verification:** Renamed to `ENV_VAR_ALIASES` (public, no underscore) at line 116. Added to `__all__` at line 92. `_check_env_vars` at line 250 uses the new name. No lingering `_ENV_VAR_ALIASES` references in production code (grep confirmed; only the test file references the old name in a docstring + an intentional `not hasattr` assertion).
**Test added:** `test_env_var_aliases_is_public` — asserts `hasattr(optin, "ENV_VAR_ALIASES")`, `not hasattr(optin, "_ENV_VAR_ALIASES")`, `"ENV_VAR_ALIASES" in optin.__all__`, and `"MINIMAX_API_KEY" in optin.ENV_VAR_ALIASES["hailuo"]`. PASS.

## Anti-Pattern Scan (New Issues Check)

Ran quick-mode pattern scans against both files for newly-introduced defects:

- **Hardcoded secrets:** None. (No literal API key assignments; only env var name string constants.)
- **Dangerous functions:** None. (No `eval`, `exec`, `system`, `innerHTML`.)
- **Debug artifacts:** None. (No `console.log`, `debugger`, `TODO`, `FIXME`, `HACK`, `XXX`.)
- **Empty catch / bare except:** None. (The one `except Exception as exc` at line 203 logs the exception per project convention — not silent.)
- **`open()` without `encoding=`:** None. (Single `open()` at line 190 passes `encoding="utf-8"` — Ruff PLW1514 compliant.)

## Test Suite Status

`python3 -m pytest` reports **29 passed in 0.45s** (up from 23 in iteration 1). The 6 new tests cover the CR-01/CR-02/WR-01/WR-05 regression cases. No failures, no skips, no warnings.

## Conclusion

All 7 Critical+Warning findings from iteration 1 are resolved. The 4 Info-level findings from iteration 1 (unused `main` import, missing whitespace-key test, missing wan22 string-bool test, cost-table ambiguity) remain unfixed but are out of scope for this re-review — they are non-blocking quality suggestions. No new Critical or Warning issues were introduced by the fixes.

**Status: clean.** Code is ready to ship.

---

_Reviewed: 2026-07-10T20:15:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: quick_
_Iteration: 2 (re-review after fixes)_
