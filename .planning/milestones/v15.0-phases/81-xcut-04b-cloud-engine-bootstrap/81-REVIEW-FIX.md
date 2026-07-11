---
phase: 81-xcut-04b-cloud-engine-bootstrap
fixed_at: 2026-07-10T20:05:00Z
review_path: .planning/phases/81-xcut-04b-cloud-engine-bootstrap/81-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 81: Code Review Fix Report

**Fixed at:** 2026-07-10T20:05:00Z
**Source review:** `.planning/phases/81-xcut-04b-cloud-engine-bootstrap/81-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 7 (2 Critical + 5 Warning; 4 Info excluded per fix_scope)
- Fixed: 7
- Skipped: 0
- Test count: 23 → 29 (+6 new tests)
- All commits atomic, one finding per commit

## Fixed Issues

### CR-01: Crash on non-dict `cloud_engines` block violates "NEVER crashes" contract (D-06)

**Files modified:** `skills/kais-movie-pipeline/scripts/check_cloud_engine_optin.py`, `skills/kais-movie-pipeline/tests/test_check_cloud_engine_optin.py`
**Commit:** `e721b93`
**Applied fix:** Added `isinstance(cloud_block, dict)` guard inside the existing try/except block, plus `isinstance(config, dict)` guard on the parent config object. When `cloud_engines` is a non-dict (list, string, scalar), logs a warning and treats it as empty (all engines not opted in). Added 3 tests: list-typed, string-typed, and int-typed `cloud_engines` all return defaults without crash.

### CR-02: `motion_vector_match` routing omits Vidu fallback, contradicts routing doc

**Files modified:** `skills/kais-movie-pipeline/scripts/check_cloud_engine_optin.py`, `skills/kais-movie-pipeline/tests/test_check_cloud_engine_optin.py`
**Commit:** `268d405`
**Applied fix:** Changed `TRANSITION_ENGINE_MAP["motion_vector_match"]` from `("hailuo", "ffmpeg_motion_based_cut")` to `("hailuo", "vidu", "ffmpeg_motion_based_cut")`, matching the routing doc's declaration of Hailuo/Vidu as co-primary cloud engines. Added `test_motion_vector_match_vidu_fallback` verifying vidu appears in the fallback chain when hailuo is not opted in.

### WR-01: `primary_engine` column shows active engine, not primary, when fallback triggers

**Files modified:** `skills/kais-movie-pipeline/scripts/check_cloud_engine_optin.py`, `skills/kais-movie-pipeline/tests/test_check_cloud_engine_optin.py`
**Commit:** `1a3dcde`
**Applied fix:** Changed `primary_engine` assignment from `primary if available else active_engine` to always report the declared primary. The Rich table is now internally consistent: the "Primary Engine" column shows what the routing table declares as primary, while "Available" + "Fallback" columns carry the actual-availability information. Added `test_primary_engine_always_declared` covering all cloud-engine transitions; also augmented `test_hailuo_not_opted_vidu_fallback` with a `primary_engine == "hailuo"` assertion.

### WR-02: `transition-engine-routing.md` internally contradicts TRANS-10 deferral version (v15+ vs v16+)

**Files modified:** `skills/kais-movie-pipeline/references/transition-engine-routing.md`
**Commit:** `8a3ca13`
**Applied fix:** Standardized all TRANS-10 deferral references to v16+ across 3 lines (77, 93, 97) that previously said v15+. Line 143 already said v16+. Canonical version confirmed via 81-CONTEXT.md line 116 ("TRANS-10 — v16+ scope") and cloud-engine-bootstrap.md. The TRANS-08 reference on line 33 correctly stays v15+ (separate requirement).

### WR-03: Missing sys.path bootstrap — script relies on editable install of hermes-agent

**Files modified:** `skills/kais-movie-pipeline/scripts/check_cloud_engine_optin.py`
**Commit:** `d0252a2`
**Applied fix:** Added a 3-tier sys.path bootstrap: (1) try the editable install of hermes-agent, (2) try the sibling `../hermes-agent` repo relative to kais-hermes-skills root, (3) fall back to a minimal vendored `get_hermes_home()` that reads `HERMES_HOME` env var and falls back to the platform-native default (`~/.hermes` on POSIX, `%LOCALAPPDATA%/Hermes` on Windows). The script now works standalone in any environment — fresh CI container, another developer's machine, or deployment without the editable install. Verified via direct standalone execution (`python scripts/check_cloud_engine_optin.py --json`).

### WR-04: Stray `verified_date: 2026-07` line in bootstrap doc prose — invalid YAML

**Files modified:** `skills/kais-movie-pipeline/references/cloud-engine-bootstrap.md`
**Commit:** `540c01f`
**Applied fix:** Removed the stray `verified_date: 2026-07` line (line 6) from the markdown prose body. The `**Last-verified:** 2026-07-10` field on line 5 already carries the verification date. The stray line was a copy-paste artifact from frontmatter that ended up in the prose body without `---` delimiters.

### WR-05: `_ENV_VAR_ALIASES` is private but `ENV_VAR_MAP` is public — inconsistent API surface

**Files modified:** `skills/kais-movie-pipeline/scripts/check_cloud_engine_optin.py`, `skills/kais-movie-pipeline/tests/test_check_cloud_engine_optin.py`
**Commit:** `ccc60e6`
**Applied fix:** Renamed `_ENV_VAR_ALIASES` to `ENV_VAR_ALIASES` (public) and added it to `__all__`. Updated the single usage in `_check_env_vars` to reference the new name. Downstream consumers (e.g., a routing subagent) can now enumerate the `MINIMAX_API_KEY` alias alongside the primary `ENV_VAR_MAP`. Added `test_env_var_aliases_is_public` verifying the public attribute, `__all__` membership, and alias content.

## Skipped Issues

None — all 7 in-scope findings were fixed.

---

_Fixed: 2026-07-10T20:05:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
