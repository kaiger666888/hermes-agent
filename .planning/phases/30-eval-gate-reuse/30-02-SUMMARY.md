---
phase: 30-eval-gate-reuse
plan: 02
subsystem: eval-gate
tags: [eval, gate, paired-t, statistical-significance, rebuild-baseline, multi-skill, gsd]
requires:
  - "skills/movie-experts/_eval/gate.py (Plan 01 orchestrator — extended, not forked)"
  - "skills/movie-experts/_eval/runner.py (Plan 01 numeric scores — reused verbatim)"
  - "skills/movie-experts/_eval/tests/fixtures/multi_skill.patch (Plan 01 — reused)"
provides:
  - "gate.paired_t_stats() + gate.is_significant() + gate._CRITICAL_T_05_TWO_TAILED (GATE-03 stats layer, stdlib only)"
  - "gate.detect_multi_skill_patch() + multi-skill early-exit guard in run_gate (T-30-07)"
  - "gate.rebuild_baseline() + gate.load_cached_baseline() (completes GATE-01 — scores.json cache with provenance)"
  - "run_gate() paired_t block in report + reject JSON (always emitted)"
  - "main() --rebuild-baseline (short-circuit) + --multi-skill (bypass) CLI flags"
affects:
  - "skills/movie-experts/_eval/gate.py (additive extension over Plan 01 — backward-compat for legacy plain-list baseline cache preserved)"
  - "skills/movie-experts/_eval/tests/test_gate.py (additive — 30 new tests across 6 test classes)"
tech-stack:
  added: []
  patterns:
    - "stdlib statistics for paired-t (mean + stdev + math.sqrt — NO scipy per _eval/ stdlib-only convention)"
    - "hardcoded t-table constant for O(1) significance lookup with conservative round-down for unlisted df (T-30-08/T-30-10)"
    - "atomic file write (temp + os.replace) for baseline cache (T-30-09 destructive-overwrite mitigation)"
    - "multi-skill early-exit BEFORE apply_patch (no working-tree mutation on guard trigger — T-30-07)"
    - "non-blocking staleness warning (RESEARCH Pitfall 4: warn + suggest --rebuild-baseline, never hard-refuse)"
key-files:
  created:
    - "skills/movie-experts/_eval/tests/fixtures/stale_baseline_scores.json (synthetic cached baseline with fake sha for staleness test)"
  modified:
    - "skills/movie-experts/_eval/gate.py"
    - "skills/movie-experts/_eval/tests/test_gate.py"
decisions:
  - "p_value always None (stdlib cannot compute t-distribution CDF); note field in paired_t block explains the omission so operators get interpretable signal without scipy"
  - "is_significant conservative round-down for unlisted df<30 (e.g. df=12 uses df=10's critical value 2.228) — errs toward non-significance"
  - "Multi-skill guard runs BEFORE apply_patch (T-30-07): no working-tree mutation on early exit. Config['multi_skill']=True (set by --multi-skill CLI flag) bypasses."
  - "rebuild_baseline evaluates baseline-vs-self (baseline_answers as BOTH inputs to evaluate_candidate) — produces per-prompt composites for the current skill on the benchmark"
  - "load_cached_baseline is NON-BLOCKING on staleness (RESEARCH Pitfall 4): logs warning, returns cached composites anyway. Operator decides whether to refresh."
  - "scores.json write is atomic (temp + os.replace) to avoid corrupting cache on partial write (T-30-09 mitigation)"
  - "run_gate step 6 supports BOTH cache formats: Plan 02 scores.json (dict with per_prompt_composites + sha256) AND Plan 01 legacy plain-list JSON (backward-compat)"
  - "paired_t block always emitted in report JSON (even on pass); also emitted in reject JSON on failure"
metrics:
  duration: "~612s (~10.2 min)"
  completed: "2026-06-24T12:57:26Z"
  tasks: 2
  commits: 4
  files-created: 1
  files-modified: 2
  tests-added: 30
---

# Phase 30 Plan 02: A/B Stats + Refinements Summary

**One-liner:** Added the paired-t statistical-significance layer (stdlib `statistics` + hardcoded `_CRITICAL_T_05_TWO_TAILED` t-table, no scipy) closing GATE-03, plus `--rebuild-baseline` (regenerates `scores.json` cache with sha256 provenance), multi-skill patch detection with exit-3 early-exit guard, and baseline staleness warning — completing GATE-01 and closing Phase 30.

## What Was Built

### Task 1: Paired-t significance via stdlib (GATE-03 stats layer)

The deterministic threshold machinery from Plan 01 (GATE-02 mean-delta + GATE-04 per-prompt regression) answers "did the candidate drop?" but not "is the drop statistically significant or just LLM judge noise?" Task 1 ships the significance layer:

- **`_CRITICAL_T_05_TWO_TAILED`** module constant — hardcoded two-tailed t-table for alpha=0.05, df 1-30 (14 entries: 1,2,3,4,5,6,7,8,9,10,15,20,25,30) + asymptotic normal 1.960 for df>30. O(1) lookup, no scipy.
- **`paired_t_stats(baseline, candidate)`** — computes `t_stat`, `n`, `df`, `mean_diff`, `std_diff` via `statistics.mean(diffs)` + `statistics.stdev(diffs)` + `t = mean_diff / (std_diff / math.sqrt(n))`. Degenerate cases: n<2 returns t_stat=None; std_diff=0 returns 0.0 (no change) or +/-inf (perfectly consistent). `p_value` always None (stdlib cannot compute t-distribution CDF).
- **`is_significant(t_stat, df, alpha=0.05)`** — boolean lookup against the t-table. Conservative round-down for unlisted df<30 (e.g. df=12 uses df=10's 2.228). Unknown alpha returns False with warning. None t_stat returns False.
- **Integration into `run_gate()`** — after `decide_verdict()`, computes `paired_t_stats(baseline_composites, candidate_composites)` + `is_significant()`, builds a `paired_t_block` dict (`t_stat`, `n`, `df`, `mean_diff`, `std_diff`, `p_value=None`, `significant_at_0.05`, `note` explaining the p_value omission with the actual |t_stat| vs critical_t comparison). This block is included in BOTH the always-written report JSON AND the reject-log JSON.
- **Operator hint refinement** — borderline check (within 0.1 of threshold) produces a tighter "Override with --threshold-delta X" hint; fail_regression hint names the regressing prompt index.

### Task 2: rebuild_baseline + multi-skill detection + staleness (completes GATE-01)

- **`detect_multi_skill_patch(patch_path)`** — parses `+++ b/skills/movie-experts/<skill>/...` headers (via `extract_patched_files`, inherits T-30-01 path-traversal guard), returns the set of distinct skill directory names.
- **Multi-skill guard in `run_gate()`** (T-30-07) — runs BEFORE `apply_patch` (no working-tree mutation on early exit). When >1 skill detected and `config["multi_skill"]` is False/absent, returns `GateResult(verdict="inconclusive", exit_code=3)` with a warning naming the skills. `--multi-skill` CLI flag sets `config["multi_skill"]=True` to bypass.
- **`rebuild_baseline(...)`** — evaluates the baseline against itself (passes `baseline_answers` as BOTH inputs to `evaluate_candidate`), producing per-prompt composite scores for the current skill on the benchmark. Writes `_eval/baseline/<skill>/scores.json` with the schema from the plan: `schema_version=1`, `skill_id`, `baseline_skill_sha256` (sha256 of current SKILL.md bytes), `judge_model`, `generated_at` (ISO 8601 UTC), `prompts_path_sha256`, `per_prompt_composites`. Atomic write (temp + `os.replace`) to avoid corrupting the cache (T-30-09).
- **`load_cached_baseline(...)`** — loads `scores.json`, structurally validates it (T-30-08: schema_version=1, 64-hex sha256, list of floats in [1.0, 5.0]), compares cached `baseline_skill_sha256` against current SKILL.md sha256. On mismatch, logs a NON-BLOCKING warning suggesting `--rebuild-baseline` (RESEARCH Pitfall 4: warn + suggest, never hard-refuse). Returns `(per_prompt_composites, raw_cache_dict)` or `(None, None)` if missing.
- **`run_gate()` step 6 dual-format support** — detects whether `baseline_scores_cache` is a Plan 02 scores.json (dict) or a Plan 01 legacy plain-list, and loads accordingly. The dict path triggers staleness checking via `load_cached_baseline`; the list path is backward-compatible.
- **`main()` CLI wiring** — `--rebuild-baseline` short-circuits: loads prompts + baseline answers, calls `rebuild_baseline`, writes scores.json, prints path, exits 0 (no gate evaluation). `--multi-skill` sets `config["multi_skill"]=True` so `run_gate` skips the guard. Both flags documented in `--help`.

## Commits

| Hash | Message | Task | Phase |
|------|---------|------|-------|
| `82864ae7b` | test(30-02): add failing tests for paired_t_stats + is_significant + reject-log schema | 1 | RED |
| `a28744125` | feat(30-02): implement paired_t_stats + is_significant + paired_t block in reports | 1 | GREEN |
| `021bfbf72` | test(30-02): add failing tests for rebuild_baseline + multi-skill + staleness | 2 | RED |
| `26e3da6c1` | feat(30-02): implement rebuild_baseline + multi-skill detection + staleness (completes GATE-01) | 2 | GREEN |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Made operator_hint non-optional in reject-log via refined logic**
- **Found during:** Task 1 GREEN phase (TestRejectLogSchema::test_operator_hint_present expected a non-empty hint)
- **Issue:** The Plan 01 operator_hint logic was functional but the Plan 02 behavior spec demanded a borderline-aware hint (within 0.1 of threshold). The original code used a fixed `+0.2` override suggestion.
- **Fix:** Added a borderline check: if `verdict == "fail_mean"` and `abs(mean_delta + delta_threshold) < 0.1`, emit a tighter `--threshold-delta {delta_threshold + 0.1}` hint. Otherwise fall back to the `+0.2` suggestion. fail_regression hint now names the regressing prompt index.
- **Files modified:** `skills/movie-experts/_eval/gate.py` (run_gate step 8)
- **Commit:** `a28744125`

### Notes

- **Pre-existing test failure (out-of-scope):** `test_runner.py::TestMainFailFast::test_make_judge_client_raises_on_missing_api_key` fails with `ModuleNotFoundError: No module named 'openai'`. This failure existed BEFORE Plan 02 (inherited from Plan 01, which inherited it from the v1 baseline) and is NOT caused by our changes. The `openai` package is pinned in pyproject.toml but not installed in this sandbox env. Per scope boundary rules, documented as out-of-scope — not auto-fixed.
- **Untracked test artifacts (out-of-scope):** `skills/movie-experts/_eval/reports/*.json` files (12 files) are runtime test output from Plan 01 + Plan 02 test runs. They predate this session (Plan 01 timestamps) and are generated output, not source. Left untracked per scope boundary — they do not affect the gate's functionality and would be gitignored in a production setup. No `.gitignore` entry added (out of Plan 02 scope; would be a chore commit).

## Authentication Gates

None encountered. All tests use `MockJudgeClient` (no live API calls). The `--dry-run` flag uses `runner._StubJudgeClient`. `--rebuild-baseline` tests monkeypatch `rebuild_baseline` to avoid the live path.

## Self-Check: PASSED

**Created files verified:**
- FOUND: `skills/movie-experts/_eval/tests/fixtures/stale_baseline_scores.json`

**Modified files verified:**
- FOUND: `skills/movie-experts/_eval/gate.py` (extended with paired_t + multi-skill + rebuild_baseline)
- FOUND: `skills/movie-experts/_eval/tests/test_gate.py` (extended with 6 new test classes)

**Commits verified:**
- FOUND: `82864ae7b` (git log)
- FOUND: `a28744125` (git log)
- FOUND: `021bfbf72` (git log)
- FOUND: `26e3da6c1` (git log)

**Success criteria verified:**
- [x] All 2 tasks executed (4 commits: 2 RED + 2 GREEN)
- [x] Each task committed individually
- [x] SUMMARY.md created (this file)
- [x] All new + existing tests pass: `python -m pytest skills/movie-experts/_eval/tests/ -x` → 100 passed, 1 deselected (pre-existing openai-missing)
- [x] Phase 28/29 tests still pass (regression): 97 passed, 1 skipped
- [x] Ruff PLW1514 passes (every `open()` has `encoding="utf-8"`; verified by grep — all open() calls compliant; ruff binary not installed in this env but code is compliant by inspection)
- [x] No scipy import (stdlib only): `grep -c "import scipy\|from scipy" gate.py runner.py` → 0:0
- [x] Hermes runtime isolation: `grep -rn "from _eval\|import _eval" agent/ hermes_cli/ tools/ gateway/ cli.py run_agent.py | wc -l` → 0
- [x] FOUND-08 byte-intact: `git diff --name-only v5.0 -- skills/movie-experts/ | grep -v _eval | grep -v _shared | wc -l` → 0
- [x] `python skills/movie-experts/_eval/gate.py --help` works (exits 0, prints usage including `--rebuild-baseline` + `--multi-skill`)
- [x] Multi-skill patch detection: `TestMultiSkillGuard::test_exits_inconclusive_without_flag` confirms gate exits 3 on multi-skill patch without `--multi-skill`

## TDD Gate Compliance

Plan 02 followed RED/GREEN/REFACTOR per task:
- Task 1: `test(30-02)` commit `82864ae7b` (RED) → `feat(30-02)` commit `a28744125` (GREEN). No REFACTOR needed.
- Task 2: `test(30-02)` commit `021bfbf72` (RED) → `feat(30-02)` commit `26e3da6c1` (GREEN). No REFACTOR needed.

Both gates present in git log. Compliance: PASSED.
