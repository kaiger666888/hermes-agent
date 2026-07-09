---
phase: 74-transition
plan: 03
subsystem: kais-movie-pipeline
tags: [transition, validation, smoke, ltx-flf, iclora, xc-02, goal-content-test, trans-07, xcut-01, operator-handoff]
requires:
  - "Phase 74 Plan 01 (kais-hermes-skills HEAD d079103 — transition_schema.py + ASSET_SCHEMA slot + canvas_sync)"
  - "Phase 74 Plan 02 (kais-hermes-skills HEAD 7d113da — _TRANSITION_DESIGN_INSTRUCTION + _EDITOR_TRANSITION_EXECUTION_INSTRUCTION + transition-design.md + transition-engine-routing.md)"
  - "Phase 70 70-smoke.sh skeleton (XCUT-01 style precedent)"
provides:
  - "TRANS-07 LTX-2.3 FLF + ICLoRA combined workflow validation report template (research-scope — operator fills)"
  - "XCUT-02 goal-content assertion test (test_p09_transition_unit.py) verifying _TRANSITION_DESIGN_INSTRUCTION reaches p09 goal"
  - "Phase 74 XCUT-01 smoke runner (74-smoke.sh) with 17 TRANS-01..07 + XCUT-02 assertions"
affects:
  - "Phase 76 VALIDATE — 74-smoke.sh is the Phase 74 audit input (XCUT-01 style)"
  - "TRANS-11 v15+ production rollout gate — ltx-flf-iclora-validation.md verdict box gates rollout"
tech-stack:
  added: []
  patterns:
    - "Research-scope validation template: ComfyUI node graph setup (LiconMSR + FLF Loader + LTXVConditioning + SamplerCustomAdvanced) + <operator fills> placeholders for actual results (per CONTEXT.md TRANS-07 lock)"
    - "Goal-content assertion delegate-spy: captured[\"goal\"] = goal from delegate_task callback; assert MUST keywords present in f-string (mirror test_p09_unit.py:56-63, 159-184 — META-RULE X-2 enforcement)"
    - "XCUT-01 bash smoke runner: set -euo pipefail + SCRIPT_DIR/REPO_ROOT/KHS_ROOT resolution + per-assertion OK/FAIL block (file-existence FIRST then grep -c with -lt N threshold per T-74-07 threat mitigation)"
key-files:
  created:
    - "kais-hermes-skills/skills/kais-movie-pipeline/references/ltx-flf-iclora-validation.md (126 lines, TRANS-07 research-scope template)"
    - "kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p09_transition_unit.py (175 lines, 2 tests — goal-content + slot-write)"
    - ".planning/phases/74-transition/74-smoke.sh (227 lines, 17 XCUT-01 assertions)"
  modified: []
decisions:
  - "TRANS-07 research-scope only: detailed ComfyUI node graph setup + <operator fills> placeholders; operator runs actual shots per CONTEXT.md D-11 lock. Production-readiness verdict (ready / deferred) gates TRANS-11 v15+ rollout."
  - "Goal-content test asserts 9 keywords (TRANSITION DESIGN + transition_method + visual_hook + camera_continuity + next_shot_link MUST structured + DO NOT emit execution fields + Wan2.2 + ffmpeg xfade) — covers TRANS-01/02/04/06 injection in one assertion function"
  - "Goal-content test uses separate file test_p09_transition_unit.py (NOT extending test_p09_unit.py) per CONTEXT.md Claude's Discretion — cleaner per-requirement test isolation"
  - "Smoke script 17 assertions (>= 16 per plan acceptance criterion) — adds TRANS-07a line-count check (>= 80) beyond the 16-pattern list as defense-in-depth"
  - "TDD RED phase pre-satisfied: Plan 74-02 Task 3 (_TRANSITION_DESIGN_INSTRUCTION injection) shipped before Plan 74-03 in wave 2 parallel. Cross-plan dependency resolved as documented in critical_context."
metrics:
  duration: "~5min (274s)"
  completed: "2026-07-09"
  tasks: 3
  files: 3
  tests: 2 new (4 assertions) + 17 smoke assertions
  commits: 3 (2 kais-hermes-skills + 1 hermes-agent)
---

# Phase 74 Plan 03: LTX-FLF Validation + Smoke Summary

TRANS-07 LTX-2.3 FLF + ICLoRA combined workflow validation report template authored (research-scope — operator fills actual results); XCUT-02 goal-content test asserts 9 keywords present in p09 goal f-string (META-RULE X-2 enforcement via delegate-spy); 74-smoke.sh aggregates 17 XCUT-01 assertions (TRANS-01..07 + XCUT-02) and exits 0 — serves as Phase 76 VALIDATE audit input.

## What Was Built

### Task 1 — ltx-flf-iclora-validation.md TRANS-07 research-scope template [commit 0182ba8]

**`kais-hermes-skills/skills/kais-movie-pipeline/references/ltx-flf-iclora-validation.md`** (126 lines, NEW):
- Header block: Source (LTX-2.3 IC-LoRA docs + Reddit community thread + PITFALLS T-1 + SUMMARY conflict #1) + Copyright (Fair Use — workflow setup paraphrased, results operator-private) + Last-verified `<operator fills>` + verified_date `<YYYY-MM>` per 71/72/73-PATTERNS convention
- Scope note (locked decision): Research-scope validation on 1-2 reference shots ONLY; NOT pipeline-integrated; operator runs actual shots; phase produces report TEMPLATE + setup instructions per CONTEXT.md TRANS-07 lock
- **Background — PITFALL T-1 Orthogonality** section: documents LTX-2.3 has TWO ORTHOGONAL capabilities (ICLoRA `ltx/msr` LiconMSR for identity preservation ref1-ref5 + FLF `ltx/fflf` / `ltx/singularityFFLF` for first/last frame conditioning) that are SEPARATE workflows with no merged turnkey option today; explains why this validation tests whether a combined workflow is production-ready
- **ComfyUI Node Graph Setup** section: 5 numbered steps (load LiconMSR via LiconMSR Loader / load FLF via Loader / add LTXVConditioning node / add SamplerCustomAdvanced node / connect chain Loader → LTXVConditioning → SamplerCustomAdvanced → VAEDecode → SaveVideo) with note citing the community source (Reddit r/StableDiffusion LTX-2.3 ID-LoRA with FLF thread)
- **Reference Shots (operator fills)** section: 2 sub-section templates (Shot 1 / Shot 2), each with `<operator fills>` placeholders for Setup (first/last frame path + ref1-ref5 + FLF model + sampler settings) / Identity continuity assessment / Drift risk observation / Transition smoothness / Verdict (pass | drift_unacceptable | partial)
- **Production-Readiness Verdict** section: 2 checkboxes (Ready for v15+ production rollout TRANS-11 / Deferred to v15+ with rationale + alternative paths: Wan2.2 FLF2V / LTX-MSR + post-production match-cut / Hailuo/Vidu cloud)
- Operator signature + Date + ComfyUI commit / LTX-2.3 model version line
- Cross-References section linking to transition-engine-routing.md + video-engine-comparison.md + PITFALLS.md T-1 + SUMMARY conflict #1 + CONTEXT.md TRANS-07
- 126 lines (>= 80 per VALIDATION 74-03-01 wc -l threshold); 13 ICLoRA + 24 FLF + 9 ComfyUI-node-name + 19 `<operator fills>` references

### Task 2 — test_p09_transition_unit.py XCUT-02 goal-content assertion [commit 3f79695]

**`kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p09_transition_unit.py`** (175 lines, NEW — 2 tests):
- **`test_p09_goal_includes_transition_design_instruction`**: delegate-spy captures goal f-string from `p09.run()` call; asserts 9 keywords present in `captured["goal"]`:
  - `"TRANSITION DESIGN"` (the _INSTRUCTION constant title per Plan 74-02)
  - `"transition_method"` (TRANS-01 12-enum field name)
  - `"visual_hook"` (TRANS-01 free-text field)
  - `"camera_continuity"` (TRANS-01 6-enum field)
  - `"next_shot_link MUST be a structured object"` (TRANS-02 migration mandate)
  - `"DO NOT emit execution fields"` (TRANS-04 ownership boundary — cinematographer creative only)
  - `"Wan2.2"` (TRANS-06 routing for match_cut_shared_object)
  - `"ffmpeg xfade"` (TRANS-06 routing for dissolve/wipe/fade)
- **`test_p09_writes_transition_design_slot`**: write_spy captures asset_bus_write calls; asserts `"transition-design"` in written dict (TRANS-03 system 1 writer verification — p09 writes creative intent for p13 reader)
- Helper functions mirror test_p09_unit.py:39-63 exactly: `_ok_summary()` returns a valid fenced JSON block (now including `transition_design` key) + `_make_delegate_spy(captured)` returns a mock function that stores goal/context/toolsets and returns `{"summary": _ok_summary()}`
- sys.path bootstrap inserts skill_dir parent for p09 import (mirror test_p09_unit.py:27-29)
- Both tests PASS (GREEN) — Plan 74-02 Task 3 pre-satisfied the RED phase (cross-plan intra-wave dependency resolved: 74-02 shipped before 74-03 in wave 2 parallel per critical_context)

### Task 3 — 74-smoke.sh XCUT-01 style smoke runner [commit 29b4194f0]

**`.planning/phases/74-transition/74-smoke.sh`** (227 lines, NEW — 17 assertions):
- Header: `#!/usr/bin/env bash` + `set -euo pipefail` + comment documenting 17 assertions + operator-action handoff note (does NOT invoke live Docker/ComfyUI/Wan2.2/Hailuo/Vidu)
- Path resolution: `SCRIPT_DIR` + `REPO_ROOT` via `BASH_SOURCE` (hermes-agent repo) + `KHS_ROOT="/data/workspace/kais-hermes-skills"` (hardcoded cross-repo path per Phase 74 topology)
- 17 per-assertion blocks organized by requirement:
  - **TRANS-01a/b** (2): e-konte-format.md `transition_method` + `12-value`/`12-type` grep
  - **TRANS-02a/b** (2): python-import `load_next_shot_link('shot_02')['transition_method'] == 'hard_cut'` + `_TRANSITION_METHOD_SET` len == 12
  - **TRANS-03a/b** (2): python-import `'transition-design' in ASSET_SCHEMA` + canvas_sync.py `transition_design` grep
  - **TRANS-04a/b** (2): cinematographer SKILL.md creative-intent grep + editor SKILL.md execution-field grep
  - **TRANS-05a/b** (2): transition-design.md file-exists + `match_cut_shared_object|whip_pan|j_cut` >= 3 grep
  - **TRANS-06a/b/c** (3): transition-engine-routing.md file-exists + `Wan2.2` grep + `ffmpeg xfade` grep
  - **TRANS-07a/b** (2): ltx-flf-iclora-validation.md file-exists + `wc -l >= 80` + `ICLoRA` grep
  - **XCUT-02a/b** (2): p09_shot_breakdown.py `_TRANSITION_DESIGN_INSTRUCTION` >= 2 + p13_delivery.py `_EDITOR_TRANSITION_EXECUTION_INSTRUCTION|_TRANSITION_DESIGN_INSTRUCTION` >= 2
- Each assertion block follows the 70-smoke.sh pattern: file-existence check FIRST (T-74-07 threat mitigation — prevents false-green on missing files), then grep-count with explicit `-lt N` threshold (NOT bare `== 0` gate per planner grep-gate hygiene rule); FAIL prints reason + `exit 1`; OK prints count + success
- Final line: `echo "Phase 74 smoke status: ALL 17 ASSERTIONS PASSED"`
- Exits 0 when all 17 assertions pass (VALIDATION 74-03-04 satisfied — serves as Phase 76 VALIDATE audit input)

## Test Results

| Test Suite | Count | Status |
|-----------|-------|--------|
| test_p09_transition_unit.py (new) | 2 | PASSED (0.22s) |
| test_backward_compat_string_next_shot_link (VALIDATION 74-03-02) | 1 | PASSED (0.02s) |
| Full pipeline_state + p09_unit + p09_transition_unit suite | 356 | PASSED (1.73s) |
| 74-smoke.sh (17 assertions) | 17 | ALL PASSED (exit 0) |
| **Total** | **376** | **ALL GREEN** |

**Pre-existing out-of-scope failure:** `test_v50_regression_phase41.py::test_phase40_full_dag_tests_pass` (1 test) — documented in Plan 74-01 SUMMARY as out-of-scope (root cause: tests resolve paths assuming cwd is skill dir, not kais-hermes-skills root; NOT caused by Phase 74 changes). Excluded from the 356-pass count above; full suite with this test = 356 passed + 1 pre-existing failed.

**Regression:** None. All 3 task deliverables are additive (new files only — zero modifications to existing code). The test_p09_transition_unit.py tests verify pre-existing Plan 74-02 behavior; the smoke script is read-only grep/file/python-import checks.

## Plan-Level Verification (5 commands)

| # | Command | Expected | Actual |
|---|---------|----------|--------|
| 1 | `test -f ltx-flf-iclora-validation.md && wc -l >= 80` | file exists, >= 80 lines | 126 lines (VALIDATION 74-03-01 PASS) |
| 2 | `pytest test_p09_transition_unit.py::test_p09_goal_includes_transition_design_instruction -xvs` | passes | PASSED in 0.22s (VALIDATION 74-03-03 PASS) |
| 3 | `bash 74-smoke.sh` exits 0 | exits 0 | exit 0 with 17/17 OK (VALIDATION 74-03-04 PASS) |
| 4 | `pytest test_transition_schema.py::test_backward_compat_string_next_shot_link -xvs` | passes | PASSED in 0.02s (VALIDATION 74-03-02 PASS) |
| 5 | Full suite green (excluding pre-existing failure) | all pass | 356 passed in 1.73s |

## Deviations from Plan

None - plan executed exactly as written. All 3 tasks executed exactly as planned. TRANS-07 research-scope template structure (PITFALL T-1 background + ComfyUI node graph + 2 reference shot placeholders + production-readiness verdict checkboxes) + delegate-spy test pattern (mirror test_p09_unit.py:56-63) + 17-assertion XCUT-01 smoke script (mirror 70-smoke.sh skeleton) + file-existence-FIRST threat mitigation (T-74-07) + set -euo pipefail + operator-action handoff (no live API calls) were all locked decisions in the plan. No Rule 1/2/3/4 deviations encountered.

**TDD RED phase pre-satisfied (documented, not a deviation):** Plan 74-03 Task 2 has `tdd="true"` but the implementation it tests (`_TRANSITION_DESIGN_INSTRUCTION` injection in p09_shot_breakdown.py) was already shipped by Plan 74-02 Task 3 (commit `7d113da`) earlier in wave 2 parallel. Per TDD error handling "RED doesn't fail → investigate": investigation confirms Plan 74-02 pre-satisfied the implementation; the test correctly passes GREEN on first run. The cross-plan dependency was documented in the plan's critical_context ("Intra-wave 2 cross-plan dependency: Plan 74-03 Task 2 depends on Plan 74-02 Task 3 — Plan 74-02 has already shipped — so this dependency is resolved").

## Commits

| Task | Commit | Repo | Type | Message |
|------|--------|------|------|---------|
| 1 | `0182ba8` | kais-hermes-skills | docs | `docs(74-03): TRANS-07 LTX-FLF+ICLoRA validation report template` |
| 2 | `3f79695` | kais-hermes-skills | test | `test(74-03): XCUT-02 p09 goal-content assertion for _TRANSITION_DESIGN_INSTRUCTION` |
| 3 | `29b4194f0` | hermes-agent | feat | `feat(74-03): bash smoke runner executing 17 XCUT-01 assertions` |

**Cross-repo topology:** Tasks 1+2 (TRANS-07 template + XCUT-02 test) live in kais-hermes-skills repo (master branch, HEAD now `3f79695`). Task 3 (smoke runner) lives in hermes-agent repo (main branch). SUMMARY.md + STATE.md + ROADMAP.md commits follow in hermes-agent repo.

## Operator-Action Handoffs

**Two operator-action handoffs documented (NOT gaps — research-scope per locked decisions):**

1. **TRANS-07 LTX-FLF+ICLoRA validation shots** — Operator runs 1-2 reference shots using the ComfyUI node graph setup in `ltx-flf-iclora-validation.md`, fills in the `<operator fills>` placeholders with actual results (identity continuity assessment + drift risk observation + transition smoothness + verdict), and checks ONE box in the Production-Readiness Verdict section. This verdict gates TRANS-11 v15+ production rollout. The phase produced the TEMPLATE + setup instructions only (per CONTEXT.md TRANS-07 lock); the validation shots are research-scope and explicitly NOT pipeline-integrated in v14.0.

2. **XCUT-04b Hailuo/Vidu API keys** — Already documented in `transition-engine-routing.md` §XCUT-04b Operator-Action Handoff section (shipped in Plan 74-02). Operator sources Hailuo MINIMAX_API_KEY + Vidu VIDU_API_KEY + installs Wan2.2 ComfyUI node in comfyui-primary container. All three cloud/local engines degrade gracefully to ffmpeg post-production fallback when keys/node are missing. NOT required for v14.0 mandatory scope — all transition routing has ffmpeg fallback per TRANS-06 declarative rules.

## Known Stubs

None. All 3 deliverables in this plan are production-grade:
- `ltx-flf-iclora-validation.md` is intentionally a TEMPLATE with `<operator fills>` placeholders per TRANS-07 research-scope lock — this is NOT a stub, it's the locked deliverable form (operator runs the actual shots, phase produces the template + setup only)
- `test_p09_transition_unit.py` tests verify real `_TRANSITION_DESIGN_INSTRUCTION` injection (no mocks of the instruction itself; only the delegate_task + asset_bus are mocked per delegate-spy pattern)
- `74-smoke.sh` assertions check real file existence + real grep counts + real python imports (no stubbed assertions)

## Threat Flags

None. All files created stay within the documented trust boundaries. The T-74-06 (Information Disclosure — operator-filled validation results) and T-74-07 (Tampering — smoke script false-green risk) threats in the plan's `<threat_model>` are mitigated as specified:
- **T-74-06**: `ltx-flf-iclora-validation.md` template uses explicit `<operator fills>` placeholders; validation results are operator-private; no PII or secrets in template structure; header Copyright block documents Fair Use + operator-private status
- **T-74-07**: Each smoke assertion uses file-existence check FIRST (`if [ ! -f "$FILE" ]; then echo FAIL; exit 1; fi`), then grep-count with explicit `-lt N` threshold (NOT bare `== 0` gate); `set -euo pipefail` ensures undefined vars + pipe failures abort; TRANS-07a includes `wc -l >= 80` line-count check as defense-in-depth beyond keyword grep

No new security-relevant surface introduced beyond what the threat model anticipated.

## Self-Check: PASSED

All 3 created files exist on disk:
- `kais-hermes-skills/skills/kais-movie-pipeline/references/ltx-flf-iclora-validation.md` — FOUND (126 lines)
- `kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p09_transition_unit.py` — FOUND (175 lines, 2 tests)
- `.planning/phases/74-transition/74-smoke.sh` — FOUND (227 lines, 17 assertions)

All 3 task commits found in git log:
- kais-hermes-skills `0182ba8` — FOUND
- kais-hermes-skills `3f79695` — FOUND
- hermes-agent `29b4194f0` — FOUND

All 376 tests/assertions green (2 new unit tests + 1 VALIDATION 74-03-02 test + 356 full-suite tests + 17 smoke assertions). All 5 plan-level verification commands pass. VALIDATION 74-03-01 through 74-03-04 all satisfied.

---

## Phase 74 Close-Out (this is the FINAL plan of Phase 74)

Plan 74-03 is the final plan of Phase 74 (TRANSITION). This SUMMARY also serves as the phase-level close-out. Phase 74 deliverables across all 3 plans:

### All 7 TRANS requirements satisfied

| Req | Plan | Deliverable | Status |
|-----|------|-------------|--------|
| TRANS-01 | 74-01 | transition_schema.py 12-enum transition_method + 6-enum camera_continuity + frozenset runtime + Pydantic Literal type hints | SATISFIED |
| TRANS-02 | 74-01 | load_next_shot_link() backward-compat reader (string → structured default coercion); legacy episode JSON loads cleanly | SATISFIED |
| TRANS-03 | 74-01 | transition-design ASSET_SCHEMA slot (system 1) + canvas_sync _PHASE_OUTPUT_MAP p09 tuple (system 2) + storyboard canvas_type reuse (system 3, zero frontend change) | SATISFIED |
| TRANS-04 | 74-02 | Field-level ownership split: cinematographer Step 9 creative intent (transition_method / visual_hook / camera_continuity) + editor Step 7/p13 execution (cut_duration_frames / dissolve_curve / match_cut_alignment_point); FOUND-08 preserved (no new expert_id) | SATISFIED |
| TRANS-05 | 74-02 | transition-design.md 12-type taxonomy ref (hard_cut → none; film examples under fair-use) | SATISFIED |
| TRANS-06 | 74-02 | transition-engine-routing.md declarative per-transition routing table (INFRA-04 compliant, PITFALL T-1 LTX-FLF drift documented, XCUT-04b operator-action handoff) | SATISFIED |
| TRANS-07 | 74-03 | ltx-flf-iclora-validation.md research-scope template (ComfyUI node graph setup + 2 reference shot placeholders + production-readiness verdict); operator runs actual shots | SATISFIED (template delivered; operator-action validation pending) |

### Operator-action handoffs (XCUT-04 scope)

1. **TRANS-07 LTX-FLF+ICLoRA validation shots** — operator runs 1-2 reference shots, fills `<operator fills>` placeholders, checks Production-Readiness Verdict box (gates TRANS-11 v15+ rollout)
2. **XCUT-04b Hailuo/Vidu API keys + Wan2.2 ComfyUI node install** — documented in transition-engine-routing.md §XCUT-04b (shipped Plan 74-02); all cloud/local engines degrade gracefully to ffmpeg fallback when keys missing

### FOUND-08 preservation

No new `transition_designer` expert_id added. TRANS-04 field-level ownership split resolved the architectural gap via field boundaries (cinematographer creative / editor execution). Verified: `grep -c "transition_designer" cinematographer/SKILL.md editor/SKILL.md` returns 0 in frontmatter (1 in cinematographer body — the explicit "No new transition_designer expert_id" note). 15-expert frozen set preserved milestone-wide.

### INFRA-04 compliance

All transition engine routing rules are **declarative** (markdown table in transition-engine-routing.md), NOT runtime LLM decisions (TRANS-10 deferred). All calls under existing `glm_concurrent` semaphore (`MAX_CONCURRENT_GL=1`); NO separate transition semaphore. Verified: `grep -c "INFRA-04\|declarative" transition-engine-routing.md` returns 10.

### MAX_CONSTRAINTS=7 consolidation result

p09 GoalBuilder constraint budget: consolidated transition_method MUST with existing form_factor + cross-cutting constraint #3 (both Layer 5 E-Konte fields, semantically cohesive). p09 stays at 6 constraints (5 MUST + fix_feedback placeholder) — NO 8th constraint added. p13 has 5 constraints (within MAX_CONSTRAINTS=7, no consolidation needed).

### 74-smoke.sh exit code

`bash .planning/phases/74-transition/74-smoke.sh` exits 0 with 17/17 assertions PASSED. Serves as Phase 76 VALIDATE audit input.

### Cross-repo commit hashes

- **kais-hermes-skills** (master branch): HEAD `3f79695` (Plan 74-03 advanced from `7d113da` → `0182ba8` → `3f79695`)
- **hermes-agent** (main branch): HEAD `29b4194f0` (Plan 74-03 Task 3 + this SUMMARY + state updates)

Phase 74 COMPLETE — ready for Phase 75 (LINEAGE-BUMP).
