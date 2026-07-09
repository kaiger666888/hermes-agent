---
phase: 73-img
plan: 03
subsystem: img
tags: [integration-tests, e2e, smoke, xcut-02, goal-content, rhd-lhd, img-validation]
requires:
  - "Phase 73 Plan 01 (IMG foundation): dreamina_manager + vision_verify + dreamina_stats modules"
  - "Phase 73 Plan 02 (IMG integration): RHD/LHD 3-attempt budget + image2image + CLI + XCUT-02 injection"
provides:
  - "test_batch_e2e — 3-shot batch e2e with mocked CLI + GLM-4.6V (IMG-01 integration)"
  - "test_rhd_lhd_e2e — RHD/LHD failure injection e2e with image2image fallback (IMG-04 integration)"
  - "test_goal_includes_vision_verify_instruction — XCUT-02 goal-content assertion for _VISION_VERIFY_INSTRUCTION"
  - "73-smoke.sh — 15-assertion XCUT-01 style smoke runner (IMG-01..06 + XCUT-02 file/code presence)"
affects:
  - "Phase 76 VALIDATE: smoke runner serves as milestone audit input"
tech-stack:
  added: []
  patterns:
    - "async-boundary mock chain (_dreamina_submit + _dreamina_poll + _download + _dreamina_image2image + verify_image_content) — extends Plan 73-01 mock pattern with reusable _patch_chain helper"
    - "delegate-spy goal-content assertion (mirror test_p09_unit.py:56-63) — 3 keyword checks in captured['goal']"
    - "XCUT-01 smoke runner skeleton (mirror 70-smoke.sh / 72-smoke.sh) — set -euo pipefail + KHS_ROOT cross-repo resolution + per-assertion block + ALL PASS echo"
key-files:
  created:
    - "kais-hermes-skills/plugins/kais_aigc/tests/test_integration.py"
    - ".planning/phases/73-img/73-smoke.sh"
  modified:
    - "kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p07_unit.py"
decisions:
  - "[Rule 1 - Bug] XCUT-02b smoke assertion adjusted from plan literal 'MUST vision-verify' to actual SKILL.md body text 'MUST be vision-verified' — Plan 73-02 T4 patch used the latter phrasing. Intent (vision-verify MUST gate presence in SKILL.md body) preserved."
  - "Task 1 + Task 2 are tdd-marked but the implementation code already exists (Plans 73-01 + 73-02); these are NEW tests verifying existing behavior, so single test() commit per task (no separate feat() commit needed)."
  - "_patch_chain helper introduced in test_integration.py — 1 entry point patches the full dreamina_manager → vision_verify chain at async boundary (extends Plan 73-01 single-boundary mock to full-chain e2e scope)."
  - "Pre-existing test_canvas_sync_integration.py failure logged as deferred (out of scope per Rule SCOPE BOUNDARY — canvas sync subsystem, unrelated to IMG)."
requirements-completed: [IMG-01, IMG-04, XCUT-02]
metrics:
  duration: "~12min"
  completed: "2026-07-09T14:45:42Z"
  tasks: 3
  files: 3
---

# Phase 73 Plan 03: IMG Validation Layer Summary

Built the IMG validation layer: end-to-end integration tests (mocked CLI + GLM-4.6V), XCUT-02 goal-content assertion test, and the top-level 15-assertion smoke runner script. Together these prove the foundation (Plan 73-01) and integration (Plan 73-02) modules work as a chain, and provide the Phase 76 VALIDATE smoke input.

## Performance

- **Duration:** ~12 min
- **Started:** 2026-07-09T14:34:00Z
- **Completed:** 2026-07-09T14:45:42Z
- **Tasks:** 3/3
- **Files:** 3 (2 created + 1 modified)

## Accomplishments

- **IMG-01 integration (test_batch_e2e):** 3-shot batch via `batch_submit` with mocked CLI + GLM-4.6V. Asserts sync queue (3 results returned block-on-all), status=ok on all 3, vision_verified=True, confidence >= 0.7, 3 submit calls, 3 verify calls with propagated directional_check="lhd".
- **IMG-04 integration (test_rhd_lhd_e2e):** Failure injection e2e. Vision-verify fails attempts 0+1 (low-confidence RHD detection), 3rd attempt routes to image2image fallback. Asserts 2 text2image + 1 image2image calls, status in (ok | degraded), degraded path carries explicit non-empty error.
- **XCUT-02 (test_goal_includes_vision_verify_instruction):** Delegate-spy captures the goal string from `p07.run()`. Asserts 3 keywords visible to subagents at runtime: "VISION-VERIFY MANDATORY GATE" (H1 label via .task), "MUST vision-verify" (.constraints rule), "vision_verify.verify_image_content" (API symbol).
- **73-smoke.sh (XCUT-01 style):** 15 bash assertions covering IMG-01..06 + XCUT-02 file/code presence across both repos. Strict mode (`set -euo pipefail`), KHS_ROOT cross-repo resolution, per-assertion block pattern mirroring 70-smoke.sh / 72-smoke.sh. Serves as Phase 76 VALIDATE smoke input.

## Task Commits

Each task committed atomically per repo (cross-repo topology per v9.0 precedent):

1. **Task 1 (kais-hermes-skills):** `3ab1d0f` — test(73-03): add IMG e2e integration tests (IMG-01 batch + IMG-04 RHD/LHD)
2. **Task 2 (kais-hermes-skills):** `4fdd8ab` — test(73-03): add XCUT-02 goal-content assertion for _VISION_VERIFY_INSTRUCTION
3. **Task 3 (hermes-agent):** `b6f889a68` — feat(73-03): bash smoke runner executing 15 IMG + XCUT-02 assertions

## Files Created/Modified

- `kais-hermes-skills/plugins/kais_aigc/tests/test_integration.py` — NEW (301 lines): 2 e2e integration tests + `_patch_chain` reusable mock helper
- `kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p07_unit.py` — MODIFIED (+48 lines): added `test_goal_includes_vision_verify_instruction` (8 existing tests unchanged)
- `.planning/phases/73-img/73-smoke.sh` — NEW (164 lines, executable): 15-assertion XCUT-01 style smoke runner

## Test Results

All 23 IMG + p07 tests pass:

| VALIDATION ID | Test/Check | Status |
|---------------|-----------|--------|
| 73-03-01 | test_batch_e2e (3-shot batch e2e) | PASSED |
| 73-03-02 | test_rhd_lhd_e2e (RHD/LHD failure injection e2e) | PASSED |
| 73-03-03 | test_goal_includes_vision_verify_instruction (XCUT-02 goal-content) | PASSED |
| 73-03-04 | 73-smoke.sh exits 0 (all 15 assertions) | PASSED |

Existing IMG + p07 tests still green (no regressions):
- 5 dreamina_manager unit tests (3 from Plan 73-01 + 2 from Plan 73-02)
- 6 vision_verify unit tests (Plan 73-01)
- 4 dreamina_stats unit tests (Plan 73-01)
- 8 existing p07 unit tests (pre-Plan-73)

## TDD Gate Compliance

Tasks 1 and 2 are `tdd="true"` in the plan. Both target **already-implemented** code (Plans 73-01 + 73-02 shipped the dreamina_manager / vision_verify / p07 _VISION_VERIFY_INSTRUCTION modules). Per TDD discipline these are NEW test commits verifying existing behavior — no separate feat() commit is needed because there is no implementation step. Single `test(73-03)` commit per task.

Task 3 is `type="auto"` (not TDD) — bash smoke script with no test-first dimension.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] XCUT-02b smoke assertion text adjusted**
- **Found during:** Task 3 (73-smoke.sh authoring)
- **Issue:** Plan 73-03 Task 3 action specified `grep -c "MUST vision-verify" SKILL.md` >= 1. The actual SKILL.md body patch (shipped in Plan 73-02 T4 commit `96adafe`) escalated line 564 to "MUST be vision-verified before upload to ComfyUI" — the literal "MUST vision-verify" phrase appears 0 times. Plan and artifact disagreed.
- **Fix:** Smoke assertion matches the actual artifact text: `grep -c 'MUST be vision-verified' SKILL.md` >= 1. Documented inline in the smoke script with a comment explaining the Rule 1 adjustment. Intent (vision-verify MUST gate presence in SKILL.md body) fully preserved — the assertion still proves the body was patched from advisory SHOULD to MUST gate.
- **Files modified:** .planning/phases/73-img/73-smoke.sh
- **Commit:** b6f889a68

## Out-of-Scope Pre-existing Failure (Deferred)

- `plugins/kais_aigc/tests/test_canvas_sync_integration.py::TestFullPipelineEpisodeSubscriber::test_save_v2_bodies_carry_phase_node_ids` FAILS (pre-existing, unrelated to IMG). Root cause: canvas sync integration — different subsystem. Per Rule SCOPE BOUNDARY, pre-existing failures in unrelated files are NOT auto-fixed mid-task. Phase 76 VALIDATE may sweep if relevant.

## Operator-Action Handoff (XCUT-04c — vision-verify API cost budget)

Per CONTEXT.md specifics + VALIDATION.md Manual-Only Verifications table, the following data is **NOT collected by this phase** — operator runs full project at production scale to capture it for Phase 76 VALIDATE audit:

| Metric | Why Manual | Operator Action |
|--------|-----------|-----------------|
| GLM-4.6V batch calls cost at production scale | Requires production-scale image volume (213-shot × 5 refs) | Run full project; document GLM-4.6V API spend; record in milestone audit (Phase 76) |
| GLM-4.6V vision-verify accuracy on dreamina interiors | Requires actual dreamina-generated images + subjective content-match review | Run `verify_image_content()` on 5-10 production images; record false-positive rate |
| RHD/LHD 3-attempt budget success rate ≥95% | Requires actual dreamina RHD failure injection + 3-attempt budget execution at production scale | Run 20-shot batch with RHD-prone prompts; count attempts-to-success |
| `hermes dreamina stats` dashboard correctness on long history | Requires accumulated MetricsBuffer data over multiple sessions | Run 3+ pipeline sessions; verify dashboard aggregates correctly |

**Cost estimate framework (operator to validate):**
- Per-image GLM-4.6V call: ~$0.001-0.01 (varies by provider pricing)
- Batched calls (6 images/call per IMG-03 PITFALL I-1 mitigation): ~6x cost reduction
- 213-shot × 5 refs = ~1065 images / 6 per batch = ~178 GLM-4.6V calls per full project
- Operator records actual spend + accuracy in Phase 76 VALIDATE milestone audit

## Self-Check: PASSED

- All 3 created/modified files exist (verified):
  - `/data/workspace/kais-hermes-skills/plugins/kais_aigc/tests/test_integration.py` FOUND
  - `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p07_unit.py` FOUND
  - `/data/workspace/hermes-agent/.planning/phases/73-img/73-smoke.sh` FOUND (executable)
- All 3 commit hashes exist in git log:
  - kais-hermes-skills: `3ab1d0f`, `4fdd8ab` FOUND
  - hermes-agent: `b6f889a68` FOUND
- All 4 VALIDATION task IDs (73-03-01..04) pass
- 23 IMG + p07 tests green (no regressions)
- 73-smoke.sh exits 0 (all 15 assertions pass)
- All 3 test/script files parse cleanly via ast.parse / bash -n
- XCUT-04c operator-action handoff documented above
