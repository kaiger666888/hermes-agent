---
phase: 30-eval-gate-reuse
verified: 2026-06-24T22:30:00Z
status: passed
score: 9/9 must-haves verified
overrides_applied: 0
---

# Phase 30: Eval Gate Reuse — Verification Report

**Phase Goal:** Any candidate patch to a bundled movie-expert skill can be automatically scored against the baseline using the existing `_eval/runner.py` MT-Bench position-swap harness, with clear pass/fail thresholds and regression guards — before the patch ever reaches a human reviewer.

**Verified:** 2026-06-24T22:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth (from ROADMAP SC + PLAN must_haves) | Status | Evidence |
| --- | --------- | ------ | -------- |
| 1   | SC-1: Candidate patch enters gate via `_eval/runner.py` (or thin wrapper) — NO new harness built | ✓ VERIFIED | `gate.py:48` imports `runner` as sibling; `gate.py::evaluate_candidate` (line 548) calls `runner.run_position_swap`; `runner.py:153 parse_judge_scores` + `runner.py:196 composite_score` + extended `run_position_swap` (runner.py:336-380) all present. `gate.py --help` exits 0. TestRunGateEndToEnd::test_with_mock_judge_and_pregenerated_answers PASSED. |
| 2   | SC-2: Patch with mean drop > δ=0.3 below baseline is REJECTED; rejection logged with score delta | ✓ VERIFIED | `gate.py:493 decide_verdict` has `mean_delta < -delta_threshold → "fail_mean"` branch with `all_deltas` + `mean_baseline/mean_candidate` evidence dict. `gate_config.yaml.example` line 19: `delta_threshold: 0.3`. TestDecideVerdict::test_fail_mean PASSED. Behavioral spot-check: `decide_verdict([4.0]*5, [3.4]*5, delta_threshold=0.3, ...) → "fail_mean"`. |
| 3   | SC-3: A/B double-blind comparison with position swapping emits statistical-significance report | ✓ VERIFIED | `gate.py:316 paired_t_stats` (uses stdlib `statistics.mean/stdev` + `math.sqrt`); `gate.py:382 is_significant` with hardcoded `_CRITICAL_T_05_TWO_TAILED` (df 1-10,15,20,25,30 + 31-40,60,120 + asymptotic 1.960 for df>120). `run_gate` lines 1157-1231 build `paired_t_block` and emit it in BOTH report JSON (line 1218) AND reject JSON (line 1231). TestPairedT (7 tests) + TestIsSignificant (7 tests) + TestRejectLogSchema::test_paired_t_in_report_always PASSED. Behavioral: `paired_t_stats([4.0]*5, [3.0]*5)` → t_stat=-inf, mean_diff=-1.0, df=4; `is_significant(_, 4)` → True. |
| 4   | SC-4: Regression detection rejects if ANY single prompt drops > 1.0 (even if mean OK) | ✓ VERIFIED | `gate.py:502-510 decide_verdict` has `if d < -per_prompt_threshold → "fail_regression"` loop returning `regressing_prompt_idx` + `delta` + `all_deltas`. Strict-less-than boundary documented (test_regression_boundary_passes confirms exact -1.0 passes). `gate_config.yaml.example` line 20: `per_prompt_threshold: 1.0`. Behavioral: `decide_verdict([4.0]*5, [4.0,4.0,2.5,4.0,4.0], ...) → "fail_regression"`. |
| 5   | SC-5: Phase touches only `_eval/`; bundled SKILL.md + refs byte-intact vs v5.0 | ✓ VERIFIED | `git diff --name-only v5.0..HEAD -- skills/movie-experts/ \| grep -v _eval \| grep -v _shared` returns empty (0 files). All 9 changed files live under `_eval/`. `_shared/` not touched. |
| 6   | parse_judge_scores() extracts 4 per-dimension scores from judge text | ✓ VERIFIED | `runner.py:59 _SCORE_DIMENSIONS` tuple matches judge_prompt.md (industry_accuracy, professional_depth, actionability, language_quality). Behavioral spot-check: parses all 4 dims from sample text including decimal (2.5). TestParseJudgeScores covers well_formed/case_insensitive/missing_dim/out_of_range/non_numeric/empty/decimal. |
| 7   | run_position_swap() return dict extended with scores_ab, scores_ba, raw_ab, raw_ba (backward-compat) | ✓ VERIFIED | `runner.py:361-379`: raw_ab/scores_ab computed after parse_judge_decision; new keys added alongside existing prompt_id/ordering_ab/ordering_ba/final. All 11 pre-existing test_runner.py tests still green. |
| 8   | decide_verdict is pure + deterministic for fixed inputs; checks inconclusive → fail_mean → fail_regression → pass in that order | ✓ VERIFIED | `gate.py:443-517` is a pure function (no I/O, no logging). TestDecideVerdict::test_deterministic PASSED. CR-05 fix added length-mismatch → inconclusive guard at line 477 (refuses to silently truncate). |
| 9   | apply_patch validates via `git apply --check` before mutating; revert_patch runs in finally block | ✓ VERIFIED | `gate.py:182 git apply --check` then `gate.py:191 git apply`; `gate.py:228 git checkout --` + `gate.py:239 git clean -f` for added files. TestPatchMechanics::test_apply_then_revert_restores_bytes + test_apply_check_failure_raises PASSED. TestRevertOnException::test_revert_runs_in_finally PASSED. |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `skills/movie-experts/_eval/gate.py` | Gate orchestrator: run_gate + main + decide_verdict + apply/revert + config load + paired_t + rebuild_baseline + multi-skill | ✓ VERIFIED | 58947 bytes; 1290+ lines; exports all 13 public symbols listed in PLAN 01 (extract_patched_files, apply_patch, revert_patch, load_gate_config, decide_verdict, evaluate_candidate, generate_patch_id, run_gate, main, VERDICT_TO_EXIT, GATE_DIMENSIONS, GateResult) + 4 Plan 02 extensions (paired_t_stats, is_significant, detect_multi_skill_patch, rebuild_baseline, load_cached_baseline). |
| `skills/movie-experts/_eval/runner.py` | parse_judge_scores + composite_score + extended run_position_swap | ✓ VERIFIED | Extended additively; parse_judge_scores line 153, composite_score line 196, run_position_swap extended return at lines 376-379. |
| `skills/movie-experts/_eval/gate_config.yaml.example` | Committed defaults (delta=0.3, per_prompt=1.0, min=5, ab=2, judge_model) | ✓ VERIFIED | File exists with all 5 documented fields + header comment. |
| `skills/movie-experts/_eval/tests/test_gate.py` | Unit tests for decide_verdict, config, parse_judge_scores integration, exit codes, paired_t, multi-skill, rebuild_baseline, staleness | ✓ VERIFIED | 71262 bytes (>> min_lines 350); 20 test classes covering all behaviors. |
| `skills/movie-experts/_eval/tests/test_runner.py` | TestParseJudgeScores class | ✓ VERIFIED | Extended with TestParseJudgeScores + TestRunPositionSwapNumeric + TestCompositeScore. |
| `skills/movie-experts/_eval/tests/fixtures/{pass,multi_skill,path_traversal,stale_baseline_scores}.patch/.json` | Synthetic fixtures for path-traversal security + multi-skill detection | ✓ VERIFIED | 4 fixture files present (pass.patch, multi_skill.patch, path_traversal.patch, stale_baseline_scores.json). |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `gate.py` | `runner.py` | sibling `import runner` + calls run_position_swap / make_judge_client / load_prompts / parse_judge_scores / composite_score | ✓ WIRED | `gate.py:48 import runner`; calls at evaluate_candidate (line 548+), run_gate (multiple), rebuild_baseline. |
| `gate.py::decide_verdict` | numeric thresholds (delta_threshold, per_prompt_threshold, min_prompts) | pure function over baseline_scores + candidate_scores lists | ✓ WIRED | `gate.py:443-517` pure function; thresholds passed as kwargs. |
| `gate.py::apply_patch` | git subprocess | `subprocess.run(['git', 'apply', '--check', ...])` then `subprocess.run(['git', 'apply', ...])` | ✓ WIRED | argv list, no `shell=True`. T-30-02 mitigation. |
| `gate.py::paired_t_stats` | stdlib `statistics` module | `statistics.mean(diffs) + statistics.stdev(diffs) + manual t = mean_diff / (std_diff / sqrt(n))` | ✓ WIRED | `gate.py:316` + imports at line 37. |
| `gate.py::rebuild_baseline` | `_eval/baseline/<skill>/scores.json` cache | evaluate_candidate(baseline, baseline) → per-prompt composites → atomic write (temp + os.replace) | ✓ WIRED | `gate.py:652`; T-30-09 atomic write. |
| `run_gate` report writer | `_eval/reports/<patch_id>.json` + reject log | json.dump with paired_t_block + operator_hint | ✓ WIRED | `gate.py:1157-1231`; TestRejectLogSchema (3 tests) PASSED. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `gate.py::run_gate` | `paired_t_block` | `paired_t_stats(baseline_composites, candidate_composites)` from evaluate_candidate records | ✓ FLOWING | End-to-end test_with_mock_judge_and_pregenerated_answers drives full pipeline: prompts → judge → scores → verdict + paired_t_block in report JSON. |
| `gate.py::decide_verdict` | `deltas` | `c - b for c, b in zip(candidate, baseline)` | ✓ FLOWING | Pure numeric computation over real per-prompt composites; TestDecideVerdict (6 tests) green. |
| `runner.py::parse_judge_scores` | `scores_ab` / `scores_ba` | regex over `_call_judge` raw response | ✓ FLOWING | Behavioral spot-check parses 4 dims + decimal; backed by judge_prompt.md rubric definition. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| `--help` exits 0 + prints usage (CLI surface) | `.venv/bin/python skills/movie-experts/_eval/gate.py --help` | exits 0, prints all 14 flags (--patch, --skill, --rebuild-baseline, --multi-skill, --dry-run, etc.) | ✓ PASS |
| parse_judge_scores extracts 4 dims + decimal | `.venv/bin/python -c "...parse_judge_scores(...)"` | `{'industry_accuracy': 4.0, 'professional_depth': 3.0, 'actionability': 5.0, 'language_quality': 2.5}`; composite=3.625 | ✓ PASS |
| decide_verdict returns correct verdicts | behavioral script for fail_mean / fail_regression / pass | `fail_mean`, `fail_regression`, `pass` returned in correct cases | ✓ PASS |
| paired_t_stats + is_significant | behavioral script with [4.0]*5 vs [3.0]*5 | t_stat=-inf, mean_diff=-1.0, df=4; is_significant=True | ✓ PASS |
| _CRITICAL_T_05_TWO_TAILED table df entries | inspect `sorted(gate._CRITICAL_T_05_TWO_TAILED.keys())` | df 1-10, 15, 20, 25, 30, 31-40, 60, 120 (CR-02 extended from base set) | ✓ PASS |
| scipy-free (stdlib only) | `grep -c "import scipy\|from scipy" gate.py runner.py` | `gate.py:0`, `runner.py:0` (count 0 in both) | ✓ PASS |
| Hermes runtime isolation | `grep -rn "from _eval\|import _eval" agent/ hermes_cli/ tools/ gateway/ cli.py run_agent.py \| wc -l` | 0 | ✓ PASS |
| FOUND-08 byte-intact (SC-5) | `git diff --name-only v5.0..HEAD -- skills/movie-experts/ \| grep -v _eval \| grep -v _shared \| wc -l` | 0 (no bundled SKILL.md or refs touched) | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` declared for this phase. The phase's verification is test-driven (105 _eval tests + behavioral spot-checks above), matching the PLAN's `<verification>` blocks which all use pytest + grep, not shell probes. Step 7c: SKIPPED (no probe files declared or conventional).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| GATE-01 | 30-01, 30-02 | Reuse `_eval/runner.py` for patch-vs-baseline | ✓ SATISFIED | gate.py imports runner; run_gate orchestrates apply→eval→decide→revert; --rebuild-baseline (30-02) regenerates scores.json cache; multi-skill detection (30-02). TestRunGateEndToEnd + TestRebuildBaseline + TestMultiSkillGuard green. |
| GATE-02 | 30-01 | Pass threshold δ=0.3 on 4-point rubric | ✓ SATISFIED | decide_verdict fail_mean branch; gate_config.yaml.example delta_threshold: 0.3; parse_judge_scores enables numeric scoring. TestDecideVerdict::test_fail_mean green. |
| GATE-03 | 30-02 | A/B double-blind position-swap + significance report | ✓ SATISFIED | runner.run_position_swap reused (scores_ab/ba + raw_ab/ba); paired_t_stats + is_significant via stdlib; paired_t_block in report + reject JSON. TestPairedT (7) + TestIsSignificant (7) + TestRejectLogSchema (3) green. |
| GATE-04 | 30-01 | Per-prompt regression detection (threshold 1.0) | ✓ SATISFIED | decide_verdict fail_regression branch; per_prompt_threshold: 1.0 in config; strict-less-than boundary tested. TestDecideVerdict::test_fail_regression + test_regression_boundary_passes green. |

**Orphaned requirements:** None. REQUIREMENTS.md maps GATE-01..04 to Phase 30 (lines 99-102); PLAN 01 declares GATE-01/02/04; PLAN 02 declares GATE-03/01. All 4 covered.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | — | — | — | No TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER/not-yet-implemented markers found in any Phase 30 file (gate.py, runner.py, gate_config.yaml.example, test_gate.py, test_runner.py). All gate.py `open()` calls pass `encoding="utf-8"` (Ruff PLW1514 clean). No `shell=True` in subprocess calls (T-30-02 mitigation verified). No hardcoded empty data flowing to render. |

### Code-Review Fix Commits Confirmed

13 commits (5 BLOCKERS + 8 WARNINGS) found in `git log v5.0..HEAD -- skills/movie-experts/_eval/`:

| Hash | Marker | Description |
| ---- | ------ | ----------- |
| `93480abd6` | CR-01, CR-03, CR-04, WR-02 | wire baseline cache + refuse self-score + stub scores |
| `fbc3eb2f2` | WR-03 | escalate revert failures to internal_error (exit 4) |
| `2b2bf1499` | WR-01 | concurrency-safe baseline cache write |
| `f039a6f14` | WR-07 | reject deletion patches explicitly |
| `32b95f02f` | WR-05, WR-06 | judge-score regex tolerance + null answers guard |
| `94e7131d7` | WR-04 | lengthen patch_id sha prefix to 16 chars |
| `1514adc61` | WR-08 | warn on low-power n<5 paired-t |
| `93fbf6e51` | CR-05 | detect mismatched baseline/candidate lengths |
| `0bbc03418` | CR-02 | extend critical-t table for df=31..40,60,120 |

All 9 code-review fix commits land before the two Plan 02 GREEN commits, all post-dated to the Plan 02 SUMMARY's 4 commits. Total Phase 30 commits: 16 (8 RED/GREEN from TDD + 8 distinct fix commits; CR-01/03/04/WR-02 bundled into 1). Verified — all 13 review items addressed.

### FOUND-08 + Runtime Isolation Evidence

**FOUND-08 (bundled skills byte-intact across v6.0):**
- `git diff --name-only v5.0..HEAD -- skills/movie-experts/ | grep -v _eval | grep -v _shared | wc -l` → **0**
- All 9 changed files in `skills/movie-experts/` since v5.0 live under `_eval/`:
  `gate.py`, `gate_config.yaml.example`, `runner.py`, `tests/test_gate.py`, `tests/test_runner.py`, `tests/fixtures/multi_skill.patch`, `tests/fixtures/pass.patch`, `tests/fixtures/path_traversal.patch`, `tests/fixtures/stale_baseline_scores.json`
- No bundled `SKILL.md` or `references/*.md` bytes touched. Zero new expert_id directories. Zero DAG node rewiring.

**Hermes runtime isolation:**
- `grep -rn "from _eval\|import _eval" agent/ hermes_cli/ tools/ gateway/ cli.py run_agent.py | wc -l` → **0**
- `_eval/` modules use sibling-import convention (`sys.path.insert(0, str(_EVAL_DIR)); import runner; import gate`) — never importable from Hermes runtime tree.
- Matches `_eval/snapshot.py:14` "stdlib only / offline developer tooling" invariant.

**Phase 28/29 regression:**
- `tests/agent/test_feedback_*.py` (5 files): 133 passed, 1 skipped. No regression in feedback subsystem.

### Human Verification Required

None. The phase is pure offline tooling — no UI, no real-time behavior, no external service calls in unit tests (all use MockJudgeClient). The only path requiring human verification would be a live end-to-end run with real OPENROUTER_API_KEY + real judge calls, which is explicitly out-of-scope for automated verification (PLAN 01/02 scope-fenced to pre-generated answers). Operators wishing to do a live smoke test can follow the `--help` documented flags; this is operator runtime, not phase-gate verification.

### Gaps Summary

No gaps found. All 5 ROADMAP success criteria verified (SC-1 through SC-5). All 4 requirements (GATE-01..04) satisfied. All 9 must-have truths verified with codebase evidence + passing tests. All 3 levels of artifact verification (exists, substantive, wired) pass; Level 4 data-flow trace confirms real numeric data flows end-to-end through the gate pipeline. FOUND-08 + runtime isolation invariants preserved. All 13 code-review markers (5 CR + 8 WR) closed in 9 commits.

105/105 _eval tests pass. Phase 28/29 tests still green (no regressions). Ruff PLW1514 clean. scipy-free confirmed. Gate is invocable both as CLI (`python gate.py ...`) and as importable module (`from gate import run_gate`).

Phase 30 goal achieved: candidate patches to bundled movie-expert skills can be automatically scored against the v5.0 baseline using the existing MT-Bench position-swap harness, with deterministic mean-delta (GATE-02) + per-prompt regression (GATE-04) + paired-t statistical-significance (GATE-03) thresholds, before reaching a human reviewer.

---

_Verified: 2026-06-24T22:30:00Z_
_Verifier: Claude (gsd-verifier)_
