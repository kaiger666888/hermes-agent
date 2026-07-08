# Phase 65 Deferred Items

Out-of-scope discoveries logged per executor SCOPE BOUNDARY rule. Not fixed by Phase 65 work.

## 1. Pre-existing `tests/hermes_cli/test_curator_stats.py` failures (18 tests)

**Discovered during:** Plan 65-03 Wave 2 full regression run.

**Symptom:** 18 tests in `test_curator_stats.py` fail because they assert v5/v6 milestone doc-tree structure (`skills/movie-experts/_shared/v6-feedback-loop-architecture.md`, glossary entries, SC7/SC8 byte-intact checks) that was removed from the main branch in commit `f10495332` ("remove: migrated kais skills + plugins to kais-skills repo", 2026-06-26).

**Root cause:** Test file was not updated when the v5/v6 milestone docs were migrated out of this repo to the `kais-skills` repo. The tests still assert the old in-repo structure.

**Scope relationship to Phase 65:** None. These failures are unrelated to curator live guards / bias canary / audit tick_mode. All Phase 65 SCs (CURATE-01/02/03) pass. The 18 failing tests are about documentation tree integrity for a different milestone (v5.0/v6.0).

**Recommended action:** Either (a) update `test_curator_stats.py` to point at the new `kais-skills` repo paths, or (b) delete the obsolete tests if the v5/v6 architecture docs now live elsewhere and these in-repo assertions are no longer load-bearing. This belongs to a v5.0/v6.0 cleanup task, NOT Phase 65.

**Files involved:**
- `tests/hermes_cli/test_curator_stats.py` (test file — assertions reference removed paths)
- `skills/movie-experts/_shared/` (directory removed in `f10495332`)

**Verification command:** `python3 -m pytest tests/hermes_cli/test_curator_stats.py -q` → 18 failed.
