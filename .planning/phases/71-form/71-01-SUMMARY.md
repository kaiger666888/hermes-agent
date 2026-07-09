---
phase: 71-form
plan: 01
subsystem: kais-movie-pipeline (form_factor foundation)
tags: [form-factor, schema-migration, horizontal-framing, msr-fc, xcut-02]
requires: []
provides:
  - "PipelineState.form_factor Literal['landscape','portrait'] field with 'portrait' default (FORM-01)"
  - "validate_form_factor_invariant() rejecting per-shot form_factor overrides (FORM-01 / ARCHITECTURE Anti-Pattern 1)"
  - "horizontal-screen-framing.md 16:9 landscape ref mirroring vertical twin 5-section structure (FORM-03)"
  - "MSR_FC=41 canonical across all docs + p11_video_render.py code (FORM-05)"
  - "--form-factor argparse helper in ltx_msr_batch_render.py (FORM-01 render)"
  - "_FORM_FACTOR_INSTRUCTION injected into p09 goal f-string (XCUT-02 / META-RULE X-2)"
affects:
  - "Plan 71-02 (15 SKILL.md patches) consumes form_factor field + dispatch contract"
  - "Plan 71-03 (Step 14 matrix) consumes form_factor for 4-cell reframe logic"
  - "Phase 75 lineage bump will re-run transform on cinematographer + kais-movie-pipeline (SKILL.md bodies changed)"
tech-stack:
  added: []
  patterns:
    - "Schema Migration with Defaults (PipelineState.form_factor auto-whitelisted via _STATE_FIELDS)"
    - "_INSTRUCTION constant injection (META-RULE X-2 dual .task() + .constraints() sites)"
    - "Ref Twin Authoring (horizontal-screen-framing.md mirrors vertical-screen-framing.md)"
key-files:
  created:
    - "kais-hermes-skills/skills/movie-experts/cinematographer/references/horizontal-screen-framing.md (226 lines, FORM-03)"
    - "kais-hermes-skills/skills/kais-movie-pipeline/tests/test_form_factor.py (199 lines, 5 tests)"
  modified:
    - "kais-hermes-skills/plugins/pipeline_state/store.py (+form_factor field +__post_init__ +validate_form_factor_invariant)"
    - "kais-hermes-skills/skills/kais-movie-pipeline/SKILL.md (line 40 form_factor dispatch, line 446 MSR_FC=41)"
    - "kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py (+_FORM_FACTOR_INJECTION +.task() +.constraints())"
    - "kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p11_video_render.py (MSR_FC=17→41 bugfix)"
    - "kais-hermes-skills/skills/kais-movie-pipeline/templates/ltx_msr_batch_render.py (+_FORM_FACTOR_RESOLUTION +--form-factor argparse)"
    - "kais-hermes-skills/skills/kais-movie-pipeline/references/p11-single-shot-orchestration.md (MSR_FC=41 + recomputed example)"
    - "kais-hermes-skills/skills/kais-movie-pipeline/references/post-production-audit.md (MSR_FC=41 + trim-sec comment)"
    - "kais-hermes-skills/skills/kais-movie-pipeline/references/ltx-msr-workflow-spec.md (MSR_FC=41)"
decisions:
  - "form_factor default 'portrait' (not 'landscape') — preserves all existing 短剧 9:16 projects backward compat"
  - "__post_init__ validator enforces Literal enum (stdlib Literal is type-checker-only, not runtime)"
  - "Consolidated form_factor constraint with cross-cutting constraint to stay within GoalBuilder MAX_CONSTRAINTS=7"
  - "p11_video_render.py MSR_FC=17→41 fixed as Rule 1 bug (RESEARCH audit missed it; grep found it)"
metrics:
  duration: "~10min"
  completed: "2026-07-09"
  tasks: 3
  commits: 6
---

# Phase 71 Plan 01: FORM Foundation Summary

Established the form_factor contract layer for v14.0: PipelineState schema field (Literal["landscape","portrait"] with "portrait" default + __post_init__ strict enum validator + per-shot invariant validator), horizontal-screen-framing.md landscape ref mirroring the vertical twin, MSR_FC=17→41 sweep across 4 doc locations + 1 code location, --form-factor helper in the LTX render template, and _FORM_FACTOR_INSTRUCTION injection into p09 goal f-string (XCUT-02 / META-RULE X-2).

## Tasks Completed

| Task | Name | Commit(s) | Result |
|------|------|-----------|--------|
| 1 | Add form_factor field to PipelineState + validate_form_factor_invariant + tests (FORM-01) | 5987e14 (RED) + 5e47245 (GREEN) | 4 FORM-01 tests green; TDD RED→GREEN cycle |
| 2 | Sweep MSR_FC=17→41 across docs + orchestrator SKILL.md:40 form_factor dispatch (FORM-05 + FORM-01 partial) | 777e31a | 5 doc + 1 code location swept; SKILL.md:40 reads form_factor |
| 3 | Add --form-factor helper + author horizontal-screen-framing.md + inject _FORM_FACTOR_INSTRUCTION into p09 (FORM-01 render, FORM-03, XCUT-02) | 3c04855 + 93b08e5 + fea9999 | 3 atomic commits; all 5 form_factor tests green |

## Requirements Delivered

| Req | Description | Verification |
|-----|-------------|--------------|
| FORM-01 | form_factor field on PipelineState with strict enum + backward compat | 4 pytest unit tests green (backward compat + round-trip + invalid-value + per-shot invariant) |
| FORM-03 | horizontal-screen-framing.md landscape ref mirroring vertical twin | 226 lines, 9 H2 sections (5 core mirroring vertical twin + 4 trailing); film citations with fair-use attribution |
| FORM-05 | MSR_FC=17→41 sweep | grep returns 0 actionable hits (only historical A/B test narrative preserved); 41 canonical across 6 locations |
| FORM-02 (partial) | Orchestrator SKILL.md:40 form_factor dispatch | "All 15 movie-experts assume this form" claim dropped; form_factor read from PipelineState |
| XCUT-02 | _FORM_FACTOR_INSTRUCTION injected into p09 goal | test_p09_goal_includes_form_factor_instruction green; dual injection (.task + .constraints) |

## Verification Results

```
=== FULL test_form_factor.py (5 tests) ===
test_old_json_defaults_to_portrait          PASSED
test_landscape_round_trip                   PASSED
test_invalid_form_factor_raises             PASSED
test_rejects_per_shot_form_factor           PASSED
test_p09_goal_includes_form_factor_instruction PASSED
5 passed in 0.23s

=== VALIDATION 71-01-04 (MSR_FC=17 sweep) ===
0 actionable hits (historical narrative excluded) — PASS

=== VALIDATION 71-01-05 (MSR_FC=41 canonical) ===
53 hits across skills/kais-movie-pipeline/ (≥5 required) — PASS

=== VALIDATION 71-01-06 (form-factor resolution mapping) ===
portrait: (704, 1280), landscape: (1280, 704) — PASS

=== VALIDATION 71-01-07 (horizontal ref ≥150 lines) ===
226 lines — PASS

=== VALIDATION 71-01-08 (horizontal ref ≥5 H2 sections) ===
9 H2 sections — PASS

=== VALIDATION 71-01-09 ("All 15 movie-experts assume" absent) ===
0 occurrences — PASS

=== p09 regression (existing 8 unit tests) ===
8 passed — no regression
```

## TDD Gate Compliance

Task 1 was `tdd="true"`. Gate sequence verified in git log:

1. **RED gate** — `test(71-01): add failing tests for form_factor + invariant validator (RED)` (commit 5987e14). Tests failed with ImportError on `validate_form_factor_invariant` (which did not exist yet). Confirmed RED before any implementation.
2. **GREEN gate** — `feat(71-01): add form_factor Literal field to PipelineState + invariant validator (FORM-01)` (commit 5e47245). All 4 FORM-01 tests passed.
3. **REFACTOR gate** — Not needed. Implementation is minimal (Literal field + __post_init__ + recursive scan function); no cleanup warranted.

Task 3's XCUT-02 test (`test_p09_goal_includes_form_factor_instruction`) was authored in the RED commit alongside the FORM-01 tests, then turned GREEN by commit fea9999 (Part C of Task 3). This preserves the TDD gate sequence across the plan boundary.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed stale MSR_FC=17 in p11_video_render.py:74**
- **Found during:** Task 2 MSR_FC grep
- **Issue:** The phase module `p11_video_render.py:74` had `MSR_FC = 17  # Conditioning frames — ALWAYS 17` at runtime. The template script `ltx_msr_batch_render.py` already had `MSR_FC_DEFAULT = 41` (canonical per A/B test), but the phase module that orchestrates the render was passing 17 to the template. RESEARCH audit table (lines 506-522) missed this file — it only listed the template script as already-correct.
- **Fix:** Changed `MSR_FC = 17` to `MSR_FC = 41` with updated comment. Without this fix, the docs would say 41 but the orchestrator code would silently pass 17 to the template, regressing output quality (fewer identity-conditioning frames than the A/B test validated).
- **Files modified:** `skills/kais-movie-pipeline/pipeline/phases/p11_video_render.py`
- **Commit:** 777e31a

**2. [Rule 3 - Blocking issue] Consolidated form_factor constraint to stay within MAX_CONSTRAINTS=7**
- **Found during:** Task 3 Part C (XCUT-02 injection)
- **Issue:** GoalBuilder enforces `MAX_CONSTRAINTS = 7` (`_prompt_template.py:62`). Initial separate-constraint approach raised `ValueError: Over-constrained: 8 rules > 7 max` during the test run.
- **Fix:** Consolidated the form_factor MUST constraint with the existing cross-cutting injection constraint (`MUST inject all 5 cross-cutting params ... AND MUST read form_factor ...`). Semantically correct — form_factor IS a cross-cutting parameter that every shot must carry. Stays within the 7-constraint budget.
- **Files modified:** `skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py`
- **Commit:** fea9999

**3. [Rule 1 - Bug] Recomputed p11-single-shot-orchestration.md num_frames example + post-production-audit.md trim-sec comment**
- **Found during:** Task 2 MSR_FC sweep
- **Issue:** (a) The old example `duration_sec=4, MSR_FC=17 → num_frames=105, effective=88 frames = 3.67s (within ±1s of 4s)` broke under MSR_FC=41: effective = 105-41 = 64 frames = 2.67s, which is NOT within ±1s of 4s. (b) `post-production-audit.md:157` comment said `# 0.7083s` (which was 17/24) but with MSR_FC=41 the correct value is 1.708s (41/24). Leaving these stale would make the docs internally contradictory.
- **Fix:** (a) Updated example to `duration_sec=5, MSR_FC=41 → num_frames=129, effective=88 frames = 3.67s (within ±1s of 5s ✓)` — recomputed arithmetic verified. (b) Updated comment to `# 1.7083s`.
- **Files modified:** `references/p11-single-shot-orchestration.md`, `references/post-production-audit.md`
- **Commit:** 777e31a

## Known Stubs

None. All functionality wired end-to-end:
- PipelineState.form_factor: real Literal field + __post_init__ validator + invariant function (no stub)
- horizontal-screen-framing.md: full 226-line ref with real film citations (no placeholder content)
- _FORM_FACTOR_INSTRUCTION: real constant with dual-form guidance + dual injection sites (no TODO)
- --form-factor helper: real argparse option + resolution derivation logic (no placeholder)

## Threat Flags

None. No new security-relevant surface beyond what the plan's `<threat_model>` already covers:
- T-71-01 (Tampering, PipelineState.form_factor): mitigated by __post_init__ strict enum (✓ implemented)
- T-71-02 (Tampering, per-shot form_factor override): mitigated by validate_form_factor_invariant (✓ implemented)
- T-71-03 (Information Disclosure, horizontal ref citations): accepted — fair-use analytical references with bibliographic attribution (✓ implemented)
- T-71-04 (Tampering, --form-factor argparse): mitigated by `choices=["landscape","portrait"]` (✓ implemented)

## Commits (kais-hermes-skills repo)

| Commit | Type | Message |
|--------|------|---------|
| 5987e14 | test | test(71-01): add failing tests for form_factor + invariant validator (RED) |
| 5e47245 | feat | feat(71-01): add form_factor Literal field to PipelineState + invariant validator (FORM-01) |
| 777e31a | fix | fix(71-01): sweep MSR_FC=17→41 across docs + code + form_factor dispatch at SKILL.md:40 (FORM-05, FORM-01 partial) |
| 3c04855 | feat | feat(71-01): add --form-factor helper to ltx_msr_batch_render.py (FORM-01) |
| 93b08e5 | feat | feat(71-01): author horizontal-screen-framing.md mirroring vertical twin (FORM-03) |
| fea9999 | feat | feat(71-01): inject _FORM_FACTOR_INSTRUCTION into p09 goal (XCUT-02 / META-RULE X-2) |

Baseline parent: d9620369e48eec51c31ee72ac8827c288eaccf71 (P70 baseline — preserved as parent, not reset).

## Self-Check: PASSED

**Created files exist:**
- FOUND: kais-hermes-skills/skills/movie-experts/cinematographer/references/horizontal-screen-framing.md
- FOUND: kais-hermes-skills/skills/kais-movie-pipeline/tests/test_form_factor.py

**Commits exist (kais-hermes-skills repo):**
- FOUND: 5987e14 (test RED)
- FOUND: 5e47245 (feat GREEN)
- FOUND: 777e31a (fix MSR_FC sweep)
- FOUND: 3c04855 (feat --form-factor)
- FOUND: 93b08e5 (feat horizontal ref)
- FOUND: fea9999 (feat XCUT-02 injection)

All claimed artifacts verified on disk + in git log.
