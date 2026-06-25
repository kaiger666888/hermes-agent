---
phase: 30-eval-gate-reuse
plan: 01
subsystem: eval-gate
tags: [eval, gate, llm-as-judge, numeric-scoring, patch-mechanics, gsd]
requires:
  - "skills/movie-experts/_eval/runner.py (v1 MT-Bench harness — extended, not forked)"
  - "skills/movie-experts/_eval/snapshot.py (stdlib-only convention reference)"
  - "skills/movie-experts/_eval/judge_prompt.md (4-dimension rubric definition)"
provides:
  - "runner.parse_judge_scores() + runner.composite_score() + runner.run_position_swap() extended return (numeric scores)"
  - "gate.py orchestrator: run_gate + main + decide_verdict + apply_patch + revert_patch + extract_patched_files + load_gate_config + evaluate_candidate + generate_patch_id + GateResult + VERDICT_TO_EXIT"
  - "gate_config.yaml.example committed default thresholds"
  - "tests/test_gate.py (29 tests covering GATE-01/02/04 + T-30-01/02/03/04 mitigations)"
  - "tests/test_runner.py extended with TestParseJudgeScores + TestCompositeScore + TestRunPositionSwapNumeric (14 new tests)"
  - "tests/fixtures/{pass,multi_skill,path_traversal}.patch synthetic patches"
affects:
  - "skills/movie-experts/_eval/runner.py (additive extension — backward-compat verified)"
  - "skills/movie-experts/_eval/tests/test_runner.py (additive — 14 new tests)"
tech-stack:
  added: []
  patterns:
    - "thin-wrapper-over-library (gate.py imports runner, does NOT fork — 30-RESEARCH.md Pattern 1)"
    - "git subprocess patch mechanics (apply --check + apply + checkout --; 30-RESEARCH.md Pattern 2)"
    - "deterministic numeric decision function (decide_verdict; 30-RESEARCH.md Pattern 3)"
    - "try/finally revert guarantee (T-30-04 mitigation)"
    - "position-bias mitigation on numeric axis (scores_ab + scores_ba per-dimension average — 30-RESEARCH.md Pitfall 5)"
key-files:
  created:
    - "skills/movie-experts/_eval/gate.py"
    - "skills/movie-experts/_eval/gate_config.yaml.example"
    - "skills/movie-experts/_eval/tests/test_gate.py"
    - "skills/movie-experts/_eval/tests/fixtures/pass.patch"
    - "skills/movie-experts/_eval/tests/fixtures/multi_skill.patch"
    - "skills/movie-experts/_eval/tests/fixtures/path_traversal.patch"
  modified:
    - "skills/movie-experts/_eval/runner.py"
    - "skills/movie-experts/_eval/tests/test_runner.py"
decisions:
  - "parse_judge_scores silently drops out-of-range/non-numeric/missing dims (fail-safe empty dict) rather than imputing — caller decides how to treat absence"
  - "run_position_swap extended additively (raw_ab, raw_ba, scores_ab, scores_ba keys added) — existing keys unchanged for backward-compat"
  - "decide_verdict checks inconclusive -> fail_mean -> fail_regression -> pass in that order; per_prompt_threshold boundary is strict-less-than (exact -1.0 passes)"
  - "baseline cache lazy-populates on first run (candidate scores become the baseline for next run) when baseline_scores_cache is missing"
  - "revert_patch handles patch-added files via git clean -f <path> (scoped, NOT blanket) detected via git cat-file -e HEAD:<path>"
metrics:
  duration: "398s (~6.6 min)"
  completed: "2026-06-24T12:47:08Z"
  tasks: 2
  commits: 4
  files-created: 6
  files-modified: 2
  tests-added: 43
---

# Phase 30 Plan 01: Eval Gate Foundation Summary

**One-liner:** Added `parse_judge_scores()` to runner.py (the GATE-02/04 numeric enabler that v1 discarded) + built `gate.py` orchestrator with git apply/revert mechanics, pure `decide_verdict()` implementing mean-delta + per-prompt-regression thresholds, config loader with defaults<YAML<CLI precedence, and CLI surface with 0/1/2/3 exit codes.

## What Was Built

### Task 1: runner.py numeric-score extension (load-bearing per RESEARCH Pitfall 1)

The v1 `runner.py:53 _DECISION_RE` parsed ONLY `<decision>A|B|tie</decision>` and DISCARDED the 4 per-dimension numeric scores that `judge_prompt.md` explicitly asks the judge to emit. GATE-02 ("mean drops > δ=0.3") and GATE-04 ("any prompt drops > 1.0") are numeric by definition and cannot be evaluated without this extension.

Added (additive — no fork):
- `_SCORE_DIMENSIONS` constant (4 dims matching judge_prompt.md: `industry_accuracy`, `professional_depth`, `actionability`, `language_quality`)
- `_SCORE_DIMENSION_RES` compiled-regex-per-dimension dict (case-insensitive, bounded `[1-5]` pattern — no ReDoS surface)
- `parse_judge_scores(raw_text) -> dict[str, float]`: lifts per-dimension numeric scores; silently drops out-of-range/non-numeric/missing; returns `{}` when none found (fail-safe); never logs raw judge text (T-00-09)
- `composite_score(scores) -> float | None`: mean of available dims or None
- `run_position_swap()` return dict extended with `raw_ab`, `raw_ba`, `scores_ab`, `scores_ba` (backward-compat: existing `prompt_id`/`ordering_ab`/`ordering_ba`/`final` keys unchanged)

### Task 2: gate.py orchestrator + gate_config.yaml.example

Built the Phase 30 gate foundation as a thin wrapper over runner.py (extends, does NOT fork per CONTEXT.md):

**Patch mechanics (T-30-01/02/04 mitigations):**
- `extract_patched_files`: parses `+++ b/<path>` headers; rejects paths outside `skills/movie-experts/` or containing `..` (T-30-01 path traversal)
- `apply_patch`: `git apply --check` (validate, no mutation) then `git apply`; argv list, never `shell=True` (T-30-02)
- `revert_patch`: `git checkout --` for modified files, `git clean -f <path>` (scoped) for patch-added files; runs in `finally` block (T-30-04)

**Decision logic (GATE-02 + GATE-04 — pure function):**
- `decide_verdict`: deterministic for fixed inputs; checks inconclusive (n < min_prompts) -> fail_mean (mean_delta < -delta_threshold) -> fail_regression (any per-prompt delta < -per_prompt_threshold) -> pass; per-prompt boundary is strict-less-than (exact -1.0 passes)

**Config loader (T-30-04 validation):**
- `load_gate_config`: defaults < YAML < CLI precedence; validates ranges fail-fast

**Orchestrator:**
- `run_gate`: extract -> apply (try/finally) -> load pre-gen answers -> load prompts -> evaluate_candidate (calls runner.run_position_swap) -> load/lazy-populate baseline cache -> decide_verdict -> write report (always) + reject log (on failure with operator_hint) -> FINALLY revert
- `GateResult` dataclass + `VERDICT_TO_EXIT` mapping (0/1/2/3)
- `main()` CLI with `--patch --skill --baseline-answers --candidate-answers --config --threshold-delta --per-prompt-threshold --min-prompts --ab-positions --judge-model --prompts-dir --rebuild-baseline (stub for Plan 02) --dry-run`

**Scope fence:** pre-generated answers input only (no live answer generation — P31 scope per RESEARCH Open Q2 resolution).

## Commits

| Hash | Message | Task | Phase |
|------|---------|------|-------|
| `64f079add` | test(30-01): add failing tests for parse_judge_scores + numeric run_position_swap | 1 | RED |
| `43b34fe8b` | feat(30-01): implement parse_judge_scores + composite_score + numeric run_position_swap | 1 | GREEN |
| `d10894207` | test(30-01): add failing tests for gate.py orchestrator + 3 synthetic fixtures | 2 | RED |
| `d829a83f0` | feat(30-01): build gate.py orchestrator + gate_config.yaml.example | 2 | GREEN |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed IndexError in run_gate when candidate_composite is None**
- **Found during:** Task 2 GREEN phase (first test run of test_gate.py)
- **Issue:** When the stub judge returns no numeric scores (candidate_composite=None), the baseline_composite alignment used `idx = len(candidate_composites) - 1` which could be -1 (empty list) or refer to the wrong position, causing `IndexError: list index out of range`.
- **Fix:** Switched from `candidate_composites`-length-based index to the loop index `i` for baseline_composite alignment. Records with None candidate_composite now correctly skip the delta computation without misaligning the baseline.
- **Files modified:** `skills/movie-experts/_eval/gate.py` (run_gate step 6)
- **Commit:** `d829a83f0`

### Notes

- **Pre-existing test failure (out-of-scope):** `test_runner.py::TestMainFailFast::test_make_judge_client_raises_on_missing_api_key` fails with `ModuleNotFoundError: No module named 'openai'` in this environment. This failure existed BEFORE Plan 01 (27 passed, 1 failed baseline) and is NOT caused by our changes (the test imports `openai` at `runner.py:519` inside `make_judge_client`, which fails before the key-check logic runs). The `openai` package is pinned in pyproject.toml but not installed in this sandbox env. Per scope boundary rules, this is documented as out-of-scope — not auto-fixed.

## Authentication Gates

None encountered. All tests use `MockJudgeClient` (no live API calls). The `--dry-run` flag uses `runner._StubJudgeClient`.

## Self-Check: PASSED

**Created files verified:**
- FOUND: `skills/movie-experts/_eval/gate.py`
- FOUND: `skills/movie-experts/_eval/gate_config.yaml.example`
- FOUND: `skills/movie-experts/_eval/tests/test_gate.py`
- FOUND: `skills/movie-experts/_eval/tests/fixtures/pass.patch`
- FOUND: `skills/movie-experts/_eval/tests/fixtures/multi_skill.patch`
- FOUND: `skills/movie-experts/_eval/tests/fixtures/path_traversal.patch`

**Commits verified:**
- FOUND: `64f079add` (git log)
- FOUND: `43b34fe8b` (git log)
- FOUND: `d10894207` (git log)
- FOUND: `d829a83f0` (git log)

**Success criteria verified:**
- [x] All 2 tasks executed
- [x] Each task committed individually (4 commits: 2 RED + 2 GREEN)
- [x] SUMMARY.md created (this file)
- [x] All new tests pass: 43 new tests (14 runner + 29 gate) green
- [x] Phase 28/29 tests still pass (regression): 110 passed, 1 skipped
- [x] Ruff PLW1514 compliant on gate.py + runner.py (every `open()` passes `encoding="utf-8"`; ruff binary not installed in this env but code is compliant by inspection)
- [x] Hermes runtime isolation: `grep -rn "from _eval\|import _eval" agent/ hermes_cli/ tools/ gateway/ cli.py run_agent.py | wc -l` returns 0
- [x] FOUND-08 byte-intact: `git diff --name-only HEAD~2 -- skills/movie-experts/ | grep -v _eval | wc -l` returns 0 (only `_eval/` files changed)
- [x] `python skills/movie-experts/_eval/gate.py --help` works (exits 0, prints usage)
- [x] Public API exports verified: extract_patched_files, apply_patch, revert_patch, load_gate_config, decide_verdict, evaluate_candidate, generate_patch_id, run_gate, main, VERDICT_TO_EXIT, GATE_DIMENSIONS, GateResult
