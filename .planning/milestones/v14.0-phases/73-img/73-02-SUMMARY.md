---
phase: 73-img
plan: 02
subsystem: img
tags: [dreamina, rhd-lhd, image2image, vision-verify, cli, xcut-02, glm-4.6v]
requires:
  - "Phase 73 Plan 01 (IMG foundation): dreamina_manager + vision_verify + dreamina_stats modules"
provides:
  - "RHD/LHD 3-attempt budget with image2image fallback in dreamina_manager._generate_one_with_verify (IMG-04)"
  - "_dreamina_image2image() subprocess wrapper for dreamina CLI image2image subcommand"
  - "image2image-stratification.md reference with 1/3/5-ref strength + retry budget table (IMG-06)"
  - "hermes dreamina stats CLI registered via ctx.register_cli_command in kais_aigc __init__.py (IMG-05 CLI half)"
  - "_VISION_VERIFY_INSTRUCTION XCUT-02 3-site injection in p07_scene_generation.py (constant + .task + .constraints)"
  - "SKILL.md body patches: vision-verify MUST gate + Volvo V2 3-attempt budget + Production Orchestrator H2"
affects:
  - "Plan 73-03: integration tests + smoke runner (validates XCUT-02 goal-content + e2e orchestrator)"
  - "Phase 75: lineage bump (commits kais-hermes-skills changes to hermes-agent PROJECT.md)"
tech-stack:
  added: []
  patterns:
    - "XCUT-02 _INSTRUCTION 3-site injection (constant + .task(steps=) + .constraints([]) — META-RULE X-2)"
    - "RHD/LHD 3-attempt budget state machine (LHD emphasis → stronger + negative → image2image fallback)"
    - "ctx.register_cli_command plugin hook (mirror platform_metrics pattern)"
    - "FOUND-08 frontmatter freeze (body-only SKILL.md edits)"
key-files:
  created:
    - "kais-hermes-skills/skills/kais-creative/kais-jimeng-cli/references/image2image-stratification.md"
  modified:
    - "kais-hermes-skills/plugins/kais_aigc/dreamina_manager.py"
    - "kais-hermes-skills/plugins/kais_aigc/tests/test_dreamina_manager.py"
    - "kais-hermes-skills/plugins/kais_aigc/__init__.py"
    - "kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p07_scene_generation.py"
    - "kais-hermes-skills/skills/kais-movie-pipeline/SKILL.md"
    - "kais-hermes-skills/skills/kais-creative/kais-jimeng-cli/SKILL.md"
decisions:
  - "[Rule 1] Test 1 (test_rhd_lhd_3_attempt_budget) initially passed with existing scaffolding — the 3-attempt loop was already functional from Plan 73-01. Updated test to mock both _dreamina_submit AND _dreamina_image2image since attempt 2 now routes to image2image fallback."
  - "plugin.yaml NOT modified — platform_metrics precedent confirms CLI is registered via register(ctx) hook, NOT plugin.yaml manifest"
  - "_escalate_prompt returns None on attempt 2 (not a prompt string) — signals caller to switch to _dreamina_image2image"
patterns-established:
  - "XCUT-02 _INJECTION pattern (3-site): module-top constant → .task(steps=[f\"{_INSTRUCTION}\"]) → .constraints([\"MUST ...\"])"
  - "RHD/LHD 3-attempt budget: attempt 0 = LHD emphasis, attempt 1 = stronger + negative RHD, attempt 2 = None → image2image fallback"
requirements-completed: [IMG-04, IMG-05, IMG-06, XCUT-02]
metrics:
  duration: "~9min"
  completed: "2026-07-09T14:33:45Z"
  tasks: 4
  files: 7
---

# Phase 73 Plan 02: IMG Integration Layer Summary

Wired the RHD/LHD 3-attempt budget with image2image fallback into dreamina_manager, authored the image2image-stratification.md reference (1/3/5-ref strata), registered the `hermes dreamina stats` CLI command, and injected the `_VISION_VERIFY_INSTRUCTION` XCUT-02 constant into p07_scene_generation.py with SKILL.md pitfall escalations.

## Performance

- **Duration:** ~9 min
- **Started:** 2026-07-09T14:24:07Z
- **Completed:** 2026-07-09T14:33:45Z
- **Tasks:** 4/4
- **Files modified:** 7 (1 created + 6 modified)

## Accomplishments

- **IMG-04 (RHD/LHD 3-attempt budget):** `_escalate_prompt` now returns None on attempt 2 to signal image2image fallback; `_dreamina_image2image()` added for dreamina CLI image2image subprocess path; `_generate_one_with_verify` handles the None → image2image switch using `item["lhd_reference_path"]`
- **IMG-06 (image2image stratification):** Authored Chinese-primary reference with 3-stratum parameter table (1-ref strength=0.75 retry=3, 3-ref strength=0.65 retry=4, 5-ref strength=0.55 retry=5), per-stratum prompt templates, PITFALL I-6 N-ref tolerance table, and MetricsBuffer cross-reference
- **IMG-05 CLI half:** `hermes dreamina stats` registered via `ctx.register_cli_command(name="dreamina", ...)` in kais_aigc `__init__.py` — mirrors platform_metrics formula CLI pattern exactly; auto-discovered at hermes_cli/main.py:11942
- **XCUT-02 + IMG-03/04 SKILL.md:** `_VISION_VERIFY_INSTRUCTION` constant defined + injected into `.task(steps=[])` AND `.constraints([])` (5/7 within MAX_CONSTRAINTS budget); kais-movie-pipeline/SKILL.md vision-verify escalated from advisory SHOULD to MUST gate; Volvo V2 RHD/LHD references 3-attempt budget; kais-jimeng-cli/SKILL.md Production Orchestrator H2 section appended

## Task Commits

Each task was committed atomically in kais-hermes-skills repo:

1. **Task 1 (TDD RED):** `e62ccce` — test(73-02): add RHD/LHD 3-attempt budget + image2image fallback tests
2. **Task 1 (TDD GREEN):** `402ad33` — feat(73-02): implement RHD/LHD 3-attempt budget with image2image fallback (IMG-04)
3. **Task 2:** `fb304de` — feat(73-02): author image2image-stratification.md reference (IMG-06)
4. **Task 3:** `989a9ed` — feat(73-02): register hermes dreamina stats CLI command (IMG-05 CLI half)
5. **Task 4:** `96adafe` — feat(73-02): inject _VISION_VERIFY_INSTRUCTION XCUT-02 + patch SKILL.md (IMG-03/04)

## Files Created/Modified

- `kais-hermes-skills/plugins/kais_aigc/dreamina_manager.py` — _escalate_prompt returns None at attempt 2; _dreamina_image2image() added; _generate_one_with_verify handles image2image fallback
- `kais-hermes-skills/plugins/kais_aigc/tests/test_dreamina_manager.py` — 2 new tests (test_rhd_lhd_3_attempt_budget + test_image2image_fallback_on_attempt_3)
- `kais-hermes-skills/plugins/kais_aigc/__init__.py` — ctx.register_cli_command(name="dreamina", ...) added after existing tool registrations
- `kais-hermes-skills/skills/kais-creative/kais-jimeng-cli/references/image2image-stratification.md` — NEW: 3-stratum parameter table + prompt templates + retry strategies + MetricsBuffer cross-ref
- `kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p07_scene_generation.py` — _VISION_VERIFY_INSTRUCTION constant + .task(steps=) injection + .constraints([]) MUST vision-verify
- `kais-hermes-skills/skills/kais-movie-pipeline/SKILL.md` — line 564 vision-verify escalated to MUST gate; line 573 Volvo V2 references 3-attempt budget (body only, frontmatter byte-identical)
- `kais-hermes-skills/skills/kais-creative/kais-jimeng-cli/SKILL.md` — Production Orchestrator H2 section appended (body only, frontmatter byte-identical)

## Test Results

All 5 dreamina_manager unit tests pass (3 from Plan 73-01 + 2 new from Plan 73-02):

| VALIDATION ID | Test/Check | Status |
|---------------|-----------|--------|
| 73-02-01 | test_rhd_lhd_3_attempt_budget (fail-fail-succeed) | PASSED |
| 73-02-02 | grep directional question in vision_verify.py (>= 1) | PASSED (2) |
| 73-02-03 | image2image-stratification.md exists + 3 strata (>= 3) | PASSED (19) |
| 73-02-04 | register_cli_command in __init__.py (>= 1) | PASSED (3) |
| 73-02-05 | _VISION_VERIFY_INSTRUCTION in p07 (>= 2) | PASSED (2) |
| 73-02-06 | MUST vision-verify in SKILL.md files (>= 1) | PASSED (1+1) |
| 73-02-07 | RHD/LHD 3-attempt in SKILL.md (>= 1) | PASSED (1) |

## TDD Gate Compliance

Task 1 followed RED/GREEN cycle:
- RED: `test(73-02)` commit `e62ccce` — test_image2image_fallback_on_attempt_3 failed (AttributeError: no _dreamina_image2image)
- GREEN: `feat(73-02)` commit `402ad33` — both new tests pass

Note: test_rhd_lhd_3_attempt_budget passed during RED phase because the existing 3-attempt scaffolding from Plan 73-01 already handled fail-fail-succeed via text2image. The test was updated to also mock `_dreamina_image2image` since the implementation now routes attempt 2 to image2image fallback. This is acceptable — the test validates the complete 3-attempt behavior including the image2image path.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test_rhd_lhd_3_attempt_budget to mock _dreamina_image2image**
- **Found during:** Task 1 GREEN phase
- **Issue:** The original test only mocked `_dreamina_submit` (text2image), but the implementation now routes attempt 2 to `_dreamina_image2image` (image2image fallback). The test's fail-fail-succeed scenario needs the 3rd attempt to go through image2image, not text2image.
- **Fix:** Added `_fake_image2image` mock and `lhd_reference_path` to the test item dict.
- **Files modified:** test_dreamina_manager.py
- **Commit:** 402ad33

**2. [Decision] plugin.yaml NOT modified**
- **Found during:** Task 3
- **Issue:** Plan mentioned modifying plugin.yaml "ONLY IF a provides_cli field is needed".
- **Resolution:** Checked platform_metrics/plugin.yaml — it does NOT declare CLI commands in the manifest. CLI is registered purely via register(ctx) hook. Followed the same convention — no plugin.yaml edit needed.
- **Commit:** 989a9ed

## Self-Check: PASSED

- All 7 created/modified files exist in kais-hermes-skills repo
- All 5 kais-hermes-skills commit hashes exist in git log (e62ccce, 402ad33, fb304de, 989a9ed, 96adafe)
- All 5 dreamina_manager unit tests green
- All 7 VALIDATION task IDs (73-02-01 through 73-02-07) pass
- Both SKILL.md frontmatters byte-identical (FOUND-08 freeze preserved)
- p07_scene_generation.py parses cleanly via ast.parse
- __init__.py parses cleanly via ast.parse
- No stubs found (TODO/FIXME/placeholder scan clean)
