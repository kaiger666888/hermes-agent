---
phase: 30-eval-gate-reuse
fixed_at: 2026-06-24T00:00:00Z
review_path: .planning/phases/30-eval-gate-reuse/30-REVIEW.md
iteration: 1
findings_in_scope: 13
fixed: 13
skipped: 0
status: all_fixed
---

# Phase 30: Code Review Fix Report

**Fixed at:** 2026-06-24
**Source review:** `.planning/phases/30-eval-gate-reuse/30-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 13 (5 Critical + 8 Warning)
- Fixed: 13
- Skipped: 0
- Status: all_fixed

**Test results (full eval suite):** 104 passed, 1 deselected
- The 1 deselected test (`test_runner.py::TestMainFailFast::test_make_judge_client_raises_on_missing_api_key`) is a PRE-EXISTING failure caused by `openai` not being installed in the sandbox env. Confirmed by running the same test against the pre-fix code (via `git stash`) — it failed identically with `ModuleNotFoundError: No module named 'openai'`. Not caused by any fix.

**Commit coverage:** 9 atomic commits cover all 13 fixes (4 commits handle paired fixes that touch overlapping code).

## Fixed Issues

### CR-01: Baseline cache is never loaded in CLI runs (dead cache infrastructure)

**Files modified:** `skills/movie-experts/_eval/gate.py`
**Commit:** `93480abd6`
**Applied fix:** Added `--baseline-cache` CLI flag (default: `_eval/baseline/<skill>/scores.json`) plus `--no-baseline-cache` escape hatch for smoke tests. Wired `baseline_scores_cache` through `main()` → `run_gate()`. Verified with new `test_baseline_cache_flag_wires_through` test that the flag is honored end-to-end (gate reaches a real verdict, not missing-baseline inconclusive).

### CR-02: `is_significant` fallback for unknown df is ANTI-conservative

**Files modified:** `skills/movie-experts/_eval/gate.py`
**Commit:** `0bbc03418`
**Applied fix:** Extended `_CRITICAL_T_05_TWO_TAILED` table with df=31..40, 60, 120 entries (e.g. df=31→2.040, df=40→2.021, df=60→2.000, df=120→1.980). Asymptotic z=1.960 fallback now fires only for df>120. Updated docstring to clarify "conservative" = larger critical-t = harder to declare significance. Also updated the parallel fallback at the `paired_t_block` note builder.

### CR-03: "First-run populates baseline from candidate" path is dead code (always-empty candidate_composites)

**Files modified:** `skills/movie-experts/_eval/gate.py`, `skills/movie-experts/_eval/tests/test_gate.py`
**Commit:** `93480abd6`
**Applied fix:** Removed the `baseline_composites = list(candidate_composites)` lazy-population path. If no baseline cache is available, `run_gate` now returns `verdict="inconclusive"` with `evidence.reason="missing_baseline_cache"` and logs an ERROR directing the operator to run `--rebuild-baseline` first. Added regression test `TestMissingBaselineRefusal`. Updated `test_with_mock_judge_and_pregenerated_answers` to provide an explicit baseline cache.

### CR-04: `--dry-run` produces uniformly None composites

**Files modified:** `skills/movie-experts/_eval/runner.py`
**Commit:** `93480abd6`
**Applied fix:** Extended `_StubJudgeClient._Completions.create` to synthesize per-dimension scores deterministically from the prompt text (sha256 byte → [1.0, 5.0] range, each dimension uses a different byte offset for independence). Documented as "synthetic for dry-run only — not for production verdicts." Combined with CR-01, `--dry-run` now exercises the full composite pipeline end-to-end.

### CR-05: `decide_verdict` and `paired_t_stats` silently disagree with per_prompt report when list lengths differ

**Files modified:** `skills/movie-experts/_eval/gate.py`
**Commit:** `93fbf6e51`
**Applied fix:** Added length-mismatch check at the top of `decide_verdict`: if `len(baseline_scores) != len(candidate_scores)`, returns `"inconclusive"` with `evidence.reason="mismatched_prompt_counts"` plus `n_baseline` / `n_candidate` so the operator sees the corruption. No silent truncation.

### WR-01: Baseline cache write is not concurrency-safe

**Files modified:** `skills/movie-experts/_eval/gate.py`
**Commit:** `2b2bf1499`
**Applied fix:** `rebuild_baseline` now uses `tempfile.mkstemp(dir=out_dir, prefix="scores.", suffix=".tmp")` for a unique tmp name per run, then `os.replace(tmp_path, out_path)` for atomic publication. Best-effort tmp cleanup on failure. Eliminates the cross-run .tmp collision window.

### WR-02: First-run baseline cache write happens BEFORE verdict

**Files modified:** `skills/movie-experts/_eval/gate.py`
**Commit:** `93480abd6` (folded into CR-03/CR-01/CR-04 commit because removing the lazy-population path also removed the cache-write-on-failure surface)
**Applied fix:** The cache-write-from-`run_gate` path was removed entirely (it lived inside the CR-03 lazy-population branch). Cache is now written ONLY via `rebuild_baseline`, which is invoked by `--rebuild-baseline` — never during a gate evaluation. State mutation can no longer precede (or be triggered by) a verdict decision.

### WR-03: `revert_patch` swallows errors silently

**Files modified:** `skills/movie-experts/_eval/gate.py`, `skills/movie-experts/_eval/tests/test_gate.py`
**Commit:** `fbc3eb2f2`
**Applied fix:** Added `"internal_error": 4` to `VERDICT_TO_EXIT`. The try/finally in `run_gate` now captures the revert exception, logs at ERROR level with the file list, and escalates `verdict="internal_error"` (exit code 4) with `evidence.reason="revert_failed"`. Operators MUST see the dirty working tree. Added regression test `TestRevertFailureEscalation`.

### WR-04: `generate_patch_id` is not collision-resistant for rapid re-runs

**Files modified:** `skills/movie-experts/_eval/gate.py`, `skills/movie-experts/_eval/tests/test_gate.py`
**Commit:** `94e7131d7`
**Applied fix:** Bumped sha prefix from `sha256[:8]` (32 bits) to `sha256[:16]` (64 bits) — collision-resistant for any realistic CI matrix. Updated docstring + `TestGeneratePatchId` expectations.

### WR-05: `parse_judge_scores` regex is fragile against markdown emphasis

**Files modified:** `skills/movie-experts/_eval/runner.py`
**Commit:** `32b95f02f`
**Applied fix:** Each dimension regex now tolerates optional markdown bold/italic markers (`*`, `_`) and list markers (`-`, `+`) before/after the dimension name, plus arbitrary whitespace around the colon. Also added `logger.debug("dimension %s not found in judge response", dim)` when a dimension is missing — operators get an audit trail for "judge emitted scores in a slightly different format" without exposing the raw judge text (T-00-09 preserved).

### WR-06: Silent `null`→`"None"` coercion in answers loader

**Files modified:** `skills/movie-experts/_eval/gate.py`
**Commit:** `32b95f02f`
**Applied fix:** `_load_answers_json` now validates element types. JSON `null` is treated as a missing answer (warn + skip); any other non-string non-null type raises `ValueError` at load time with the index + type name. No more silent `"None"` / `"True"` / `"42"` coercion.

### WR-07: Deletion-patch handling

**Files modified:** `skills/movie-experts/_eval/gate.py`, `skills/movie-experts/_eval/tests/test_gate.py`
**Commit:** `f039a6f14`
**Applied fix:** `extract_patched_files` now explicitly detects `+++ /dev/null` headers and raises `ValueError("patch contains file deletion ...")`. The error message names the scope boundary (gate is for additive patches per EVOL-02) so operators know it's intentional rather than a bug. Added regression test `test_rejects_deletion_patch`.

### WR-08: Low-power n=2 paired-t

**Files modified:** `skills/movie-experts/_eval/gate.py`
**Commit:** `1514adc61`
**Applied fix:** `paired_t_stats` emits a `logger.warning` when `n < 5` showing the actual critical-t at `df=n-1` so operators understand how unattainable significance is. The report's `paired_t.note` also appends `"(WARNING: n<5 — paired-t has low power; treat significant_at_0.05 with caution.)"` so the audit trail carries the warning.

## Commit Log (chronological)

```
0bbc03418  fix(30): CR-02 extend critical-t table for df=31..40,60,120
93fbf6e51  fix(30): CR-05 detect mismatched baseline/candidate lengths
1514adc61  fix(30): WR-08 warn on low-power n<5 paired-t
94e7131d7  fix(30): WR-04 lengthen patch_id sha prefix to 16 chars
32b95f02f  fix(30): WR-05 WR-06 judge-score regex tolerance + null answers guard
f039a6f14  fix(30): WR-07 reject deletion patches explicitly
2b2bf1499  fix(30): WR-01 concurrency-safe baseline cache write
fbc3eb2f2  fix(30): WR-03 escalate revert failures to internal_error (exit 4)
93480abd6  fix(30): CR-01 CR-03 CR-04 WR-02 wire baseline cache + refuse self-score + stub scores
```

## Verification Status

- [x] All 13 in-scope findings fixed (5 CR + 8 WR; 4 commits fold paired fixes)
- [x] Each fix committed atomically with `fix(30): <ID> <desc>` format
- [x] All targeted tests pass after each fix (verified incrementally)
- [x] Full eval suite green at end: **104 passed, 1 deselected** (pre-existing openai-not-installed failure, unrelated to fixes)
- [x] FOUND-08 byte-intact preserved (`git diff main --name-only -- skills/movie-experts/ | grep -v _eval | grep -v _shared` → empty)
- [x] PLW1514 (encoding="utf-8") passes on every modified `open()` call (manually verified — no `open()` without encoding remains)
- [x] No scipy import (only docstring/comment mentions, no actual `import scipy`)
- [x] Source files match REVIEW.md line citations (verified by reading source before each edit)
- [x] Hermes conventions respected (lazy %s logging, specific exceptions, stdlib-only _eval/, `from __future__ import annotations`)

## Skipped Issues

None.

---

_Fixed: 2026-06-24_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
