---
phase: 74-transition
plan: 02
subsystem: pipeline_state
tags: [transition, skill-md, ownership-split, routing, declarative, xc-02-injection, trans-04, trans-05, trans-06, found-08]
requires:
  - "Phase 74 Plan 01 (kais-hermes-skills HEAD d079103 — transition_schema.py + ASSET_SCHEMA slot + canvas_sync)"
  - "FORM-01 form_factor _INJECTION precedent (p09_shot_breakdown.py:80-89)"
  - "Phase 71/72/73 SKILL.md body-edit precedent (FOUND-08 frontmatter freeze)"
provides:
  - "TRANS-04 field-level ownership split documented in cinematographer Step 9 + editor Workflow Step 7 + p13_delivery.py"
  - "transition-design.md 12-type taxonomy ref (TRANS-05)"
  - "transition-engine-routing.md per-transition declarative routing table (TRANS-06)"
  - "_TRANSITION_DESIGN_INSTRUCTION + _EDITOR_TRANSITION_EXECUTION_INSTRUCTION XCUT-02 injection"
  - "e-konte-format.md Layer 5 schema extension (TRANS-01/02 backward-compat)"
affects:
  - "Plan 74-03 LTX-FLF validation + smoke runner — depends on this plan's _INJECTION constants for goal-content test"
tech-stack:
  added: []
  patterns:
    - "MAX_CONSTRAINTS=7 budget consolidation: append transition_method MUST to existing form_factor + cross-cutting constraint #3 (both Layer 5 E-Konte fields — semantically cohesive)"
    - "XCUT-02 3-site injection (constant + .task(steps=) + .constraints([])): p09 + p13 both wired per META-RULE X-2 / PITFALL X-2"
    - "SKILL.md body-only edit (FOUND-08 frontmatter byte-identical — verified via SHA256 hash)"
    - "PITFALL T-4 disambiguation: Step 13 = pipeline phase p13_delivery.py (line 89 editor final-cut), corresponds to editor SKILL.md Workflow Steps 7-13 collectively"
key-files:
  created:
    - "kais-hermes-skills/skills/movie-experts/cinematographer/references/transition-design.md (210 lines, 12-type taxonomy)"
    - "kais-hermes-skills/skills/kais-movie-pipeline/references/transition-engine-routing.md (165 lines, per-transition routing)"
  modified:
    - "kais-hermes-skills/skills/movie-experts/cinematographer/SKILL.md (+15 lines: Step 9 sub-step 5 extend + Field Ownership subsection)"
    - "kais-hermes-skills/skills/movie-experts/editor/SKILL.md (+15 lines: Workflow Step 7 rewrite + Execution Ownership subsection)"
    - "kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py (+34 lines: _TRANSITION_DESIGN_INSTRUCTION + .task + consolidated .constraints + asset_bus_write)"
    - "kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p13_delivery.py (+36 lines: _EDITOR_TRANSITION_EXECUTION_INSTRUCTION + INPUT_SLOTS + .task + .constraints + .context + asset_bus_read)"
    - "kais-hermes-skills/skills/movie-experts/cinematographer/references/e-konte-format.md (+22 lines: Layer 5 schema extension + backward-compat note + Output Schema extension)"
decisions:
  - "MAX_CONSTRAINTS=7 consolidation: appended transition_method MUST to existing constraint #3 (form_factor + cross-cutting). Both are Layer 5 E-Konte fields — semantically cohesive. p09 stays at 6 constraints (5 MUST + fix_feedback placeholder). Alternative rejected: split p09 _INSTRUCTION into 2 goal builders (breaks CF-36-03 single-delegate pattern)."
  - "PITFALL T-4 disambiguation: Step 13 in TRANS-04 = pipeline phase p13_delivery.py (line 89 editor performs final-cut + render), NOT editor SKILL.md Workflow Step 13. Both interpretations point to same code path; documented explicitly in editor SKILL.md ownership subsection."
  - "transition-design.md cross-reference path: editor SKILL.md uses ../cinematographer/references/transition-design.md (taxonomy is creative-intent-primary per CONTEXT Open Question #1 resolution). transition-engine-routing.md uses ../../kais-movie-pipeline/references/ relative path."
  - "Routing rules declarative only (INFRA-04 / PITFALL X-5 compliance): all routing is a markdown table, NO runtime LLM decisions (TRANS-10 deferred). All calls under existing glm_concurrent semaphore; NO separate transition semaphore."
  - "LTX-2.3 FLF evaluated per-transition (NOT assumed incapable per SUMMARY reconciled conflict #1): routing table states drift risk explicitly per row; PITFALL T-1 section documents ICLoRA + FLF orthogonality."
metrics:
  duration: "~7min (471s)"
  completed: "2026-07-09"
  tasks: 3
  files: 7
  tests: 20 (8 p09 unit + 12 transition_schema — all pass)
  commits: 3 (kais-hermes-skills)
---

# Phase 74 Plan 02: SKILL.md Ownership + Routing Refs + XCUT-02 Injection Summary

TRANS-04 field-level ownership split documented in BOTH cinematographer Step 9 (creative intent: transition_method / visual_hook / camera_continuity) AND editor Workflow Step 7 + p13_delivery.py (execution: cut_duration_frames / dissolve_curve / match_cut_alignment_point); TRANS-05 12-type taxonomy ref + TRANS-06 declarative per-transition routing table authored with INFRA-04 compliance; XCUT-02 `_TRANSITION_DESIGN_INSTRUCTION` injected into p09 (consolidated with form_factor per MAX_CONSTRAINTS=7) + `_EDITOR_TRANSITION_EXECUTION_INSTRUCTION` injected into p13; e-konte-format.md Layer 5 schema extended with backward-compat migration note.

## What Was Built

### Task 1 — cinematographer + editor SKILL.md ownership subsections (TRANS-04 / FOUND-08) [commit eec0b72]

**`kais-hermes-skills/skills/movie-experts/cinematographer/SKILL.md`** (+15 lines, MODIFY):
- Step 9 sub-step 5 (E-Konte 5-layer sheets timing description): replaced legacy "cut_transition + next_shot_link" with "transition_method (12-value enum) + visual_hook (free-text, str|None) + camera_continuity (6-value enum) + next_shot_link (structured object)" with cross-references to transition-design.md + e-konte-format.md
- Appended "### TRANSITION DESIGN Field Ownership (TRANS-04 — v14.0)" subsection after Step 9 Procedure (before §Key technique): 3-row table citing cinematographer owns transition_method / visual_hook / camera_continuity (creative intent), editor Step 13 owns execution fields, + explicit "No new `transition_designer` expert_id is added (FOUND-08 preserved — 15-expert frozen set)" note

**`kais-hermes-skills/skills/movie-experts/editor/SKILL.md`** (+15 lines, MODIFY):
- Workflow Step 7 (Transition Design): rewritten as "Transition Design (TRANS-04 — v14.0 ownership split)" — cites cinematographer Step 9 creative intent fields + editor emits cut_duration_frames / dissolve_curve / match_cut_alignment_point execution fields, with cross-references to transition-design.md + transition-engine-routing.md
- Appended "### TRANSITION DESIGN Execution Ownership (TRANS-04 — v14.0)" subsection after Workflow Step 13 (before §Quality Thresholds): 3-row table listing editor-owned execution fields + cinematographer owns creative intent + explicit PITFALL T-4 disambiguation note ("Step 13 in TRANS-04 refers to pipeline phase `p13_delivery.py` line 89, NOT editor SKILL.md Workflow Step 13; corresponds to editor Workflow Steps 7-13 collectively")

**Frontmatter freeze (FOUND-08):** YAML frontmatter (name/description/tags/related_skills/expert_id/metrics) byte-identical in both files — verified via SHA256 hash comparison (cinematographer `ed747970...` unchanged; editor `32931100...` unchanged). Body-only patches per Phase 71/72/73 precedent.

### Task 2 — transition-design.md (12-type taxonomy) + transition-engine-routing.md (routing) [commit 11e165e]

**`kais-hermes-skills/skills/movie-experts/cinematographer/references/transition-design.md`** (210 lines, NEW — TRANS-05):
- Header block (Source / Copyright / Last-verified / verified_date per 71-PATTERNS convention)
- 12 H2 sections, one per transition_method value (hard_cut through none), in REQUIREMENTS order
- Each section has 5 subsections: Definition / When to use / Execution path classification (generation-time / post-production / hybrid) / Concrete film examples (title + year + director under fair-use) / Engine routing cross-ref to transition-engine-routing.md
- Film examples: *2001: A Space Odyssey* (1968, Kubrick) bone-to-spaceship match cut; *La La Land* (2016, Chazelle) whip-pan opening; *The Conversation* (1974, Coppola) J-cut; *Citizen Kane* (1941, Welles) dissolve; *Star Wars* (1977, Lucas) wipe; *The Godfather* (1972, Coppola) fade — all under fair-use with title+year+director attribution per CLAUDE.md copyright discipline
- Citation Discipline section + Cross-References section at end

**`kais-hermes-skills/skills/kais-movie-pipeline/references/transition-engine-routing.md`** (165 lines, NEW — TRANS-06):
- Header block + Summary
- 12-row per-transition routing table with columns [transition_method | Primary Engine | Fallback | LTX-2.3 FLF Evaluation]: hard_cut/j_cut/l_cut → ffmpeg; dissolve/wipe/fade → ffmpeg xfade; match_cut_shared_object → Wan2.2 14B FLF2V; match_cut_shared_landscape/motion_vector_match → Hailuo/Vidu cloud; color_match → ffmpeg color; whip_pan → ffmpeg whippan (AI unreliable per TRANS-08); none → ffmpeg concat
- Routing Rule Application Order section (declarative lookup, no runtime LLM)
- "LTX-2.3 FLF + ICLoRA Combined Workflow Note (PITFALL T-1)" section: documents orthogonality (ICLoRA identity vs FLF frame-interp — separate workflows, no merged turnkey), drift risk, per-transition trade-off statement (identity-critical → Wan2.2 or MSR + post-production; landscape-only → LTX-2.3 FLF viable with drift caveat)
- "INFRA-04 Compliance (PITFALL X-5)" section: declarative routing only, NO runtime LLM decisions (TRANS-10 deferred), all calls under existing `glm_concurrent` semaphore (`MAX_CONCURRENT_GL=1`), NO separate transition semaphore, TRANS-10 v15+ rollout gate
- "XCUT-04b Operator-Action Handoff" section: Hailuo MINIMAX_API_KEY + Vidu VIDU_API_KEY env vars + Wan2.2 ComfyUI node install + graceful ffmpeg fallback when keys missing
- ffmpeg xfade Filter Availability verified 2026-07-09 (6.1.1-3ubuntu5 + xfade/wipeleft/wiperight/whippan supported)

### Task 3 — _TRANSITION_DESIGN_INSTRUCTION + _EDITOR_TRANSITION_EXECUTION_INSTRUCTION + e-konte Layer 5 [commit 7d113da]

**`kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py`** (+34 lines, MODIFY):
- Defined `_TRANSITION_DESIGN_INSTRUCTION` module constant (after `_FORM_FACTOR_INSTRUCTION`): 5-point instruction covering transition_method 12-enum + visual_hook + camera_continuity + structured next_shot_link + transition_design.json asset emission + TRANS-04 ownership split (DO NOT emit execution fields) + TRANS-06 declarative routing keywords (Wan2.2 FLF2V / ffmpeg xfade / Hailuo / Vidu)
- Injected `f"{_TRANSITION_DESIGN_INSTRUCTION}"` into `.task(steps=[...])` (between `_FORM_FACTOR_INSTRUCTION` and continuity_auditor check)
- **CRITICAL CONSOLIDATION (MAX_CONSTRAINTS=7 per D-09):** appended "AND MUST emit per-shot transition_method (12-value enum) + visual_hook + camera_continuity + structured next_shot_link in E-Konte Layer 5 (TRANS-01..04)" to existing constraint #3 (form_factor + cross-cutting params — both are Layer 5 E-Konte fields, semantically cohesive). p09 stays at 6 constraints (5 MUST + fix_feedback placeholder) — NO 8th constraint added.
- Added `asset_bus_write("transition-design", expert_output.get("transition_design", []))` after existing shot-list + e-konte-sheets writes

**`kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p13_delivery.py`** (+36 lines, MODIFY):
- Defined `_EDITOR_TRANSITION_EXECUTION_INSTRUCTION` module constant (first _INSTRUCTION constant in p13 — Phase 74 establishes the XCUT-02 pattern here): 4-point instruction covering read transition-design asset (DO NOT re-decide creative intent) + emit per-shot cut_duration_frames / dissolve_curve / match_cut_alignment_point + TRANS-06 declarative routing + FOUND-08 ownership
- Extended `INPUT_SLOTS` to add `"transition-design"` (TRANS-03 reader)
- Added `transition_design = asset_bus_read("transition-design") or {}` (Phase 74 TRANS-04)
- Injected `f"{_EDITOR_TRANSITION_EXECUTION_INSTRUCTION}"` into `.task(steps=[...])`
- Added 5th constraint: "MUST read transition-design asset and emit per-shot cut_duration_frames + dissolve_curve + match_cut_alignment_point (TRANS-04 editor execution ownership)" — p13 now 5 constraints (within MAX_CONSTRAINTS=7, no consolidation needed)
- Added `transition_design=transition_design` to `.context(...)` so subagent sees it

**`kais-hermes-skills/skills/movie-experts/cinematographer/references/e-konte-format.md`** (+22 lines, MODIFY):
- Extended Layer 5 schema (the field schema block): added transition_method (12-value enum, supersedes cut_transition_type 4-value) + visual_hook (str|None) + camera_continuity (6-value enum) + structured next_shot_link object. cut_transition_type preserved as DEPRECATED alias per T-74-05 threat mitigation.
- Added "### Layer 5 字段演变 (v14.0 TRANS-01..02)" backward-compat note section: documents v13.0 legacy fields (cut_transition_type 4-value + bare-string next_shot_link) + v14.0 fields (transition_method 12-value + structured next_shot_link) + load_next_shot_link reader
- Extended Output Schema Layer 5 example with the same v14.0 fields

## Test Results

| Test Suite | Count | Status |
|-----------|-------|--------|
| p09 unit tests (`test_p09_unit.py`) | 8 | PASSED (0.23s) |
| transition_schema tests (`test_transition_schema.py`) | 12 | PASSED (0.03s) |
| p09 + p13 Python syntax check | 2 | PASSED |
| Total | 22 | ALL GREEN |

**Regression:** No regressions. The `_TRANSITION_DESIGN_INSTRUCTION` injection into p09 .task(steps=[...]) is additive (no existing step removed); the constraint #3 consolidation is an in-place append (no existing constraint removed). The p13 changes are all additive (new INPUT_SLOT + new constant + new .task step + new constraint + new .context field).

## Plan-Level Verification (9 commands)

| # | Command | Expected | Actual |
|---|---------|----------|--------|
| 1 | `grep -c "TRANS-04" cinematographer/SKILL.md` | >= 1 | 1 |
| 2 | `grep -c "cut_duration_frames\|dissolve_curve\|match_cut_alignment_point" editor/SKILL.md` | >= 1 | 4 |
| 3 | `grep -c "^## " transition-design.md` | >= 12 | 15 (12 type sections + Summary + Citation + Cross-References) |
| 4 | `grep -c "Wan2.2\|ffmpeg xfade\|LTX-2.3 FLF" transition-engine-routing.md` | >= 4 | 18 |
| 5 | `grep -c "INFRA-04\|declarative" transition-engine-routing.md` | >= 1 | 10 |
| 6 | `grep -c "_TRANSITION_DESIGN_INSTRUCTION" p09_shot_breakdown.py` | >= 2 | 2 (definition + .task injection) |
| 7 | `grep -c "_EDITOR_TRANSITION_EXECUTION_INSTRUCTION\|_TRANSITION_DESIGN_INSTRUCTION" p13_delivery.py` | >= 2 | 2 (definition + .task injection) |
| 8 | p09 MAX_CONSTRAINTS not exceeded | no 8th constraint | 6 constraints (consolidation verified — constraint #3 now has form_factor + transition_method in one line) |
| 9 | grep -c "transition_designer" in both SKILL.md frontmatters | == 0 | cinematographer: 0 in frontmatter (1 in body — the explicit "No new transition_designer expert_id" note at line 217); editor: 0 |

## Deviations from Plan

None - plan executed exactly as written. The MAX_CONSTRAINTS=7 consolidation choice (constraint #3 merge with form_factor) + PITFALL T-4 disambiguation note + declarative routing rules + LTX-2.3 FLF per-transition evaluation + FOUND-08 compliance + SKILL.md frontmatter byte-identical were all locked decisions in the plan. No Rule 1/2/3/4 deviations encountered.

## Commits

| Task | Commit | Type | Message |
|------|--------|------|---------|
| 1 | `eec0b72` | docs | `docs(74-02): TRANS-04 cinematographer + editor SKILL.md ownership split` |
| 2 | `11e165e` | docs | `docs(74-02): TRANS-05/06 transition-design + routing refs` |
| 3 | `7d113da` | feat | `feat(74-02): XCUT-02 _INJECTION p09 + p13 + e-konte Layer 5 extension` |

**Cross-repo topology:** All 3 commits in `kais-hermes-skills` repo (master branch, HEAD now `7d113da`). SUMMARY.md + STATE.md + ROADMAP.md commits follow in hermes-agent repo.

## Operator-Action Handoffs

**None for Plan 74-02.** This plan is pure documentation + constant injection. Operator-action handoffs (Wan2.2 FLF2V ComfyUI node install, Hailuo/Vidu API keys) are documented in transition-engine-routing.md §XCUT-04b for Plan 74-03 / Phase 76 VALIDATE scope, NOT required for this plan's deliverables.

## Known Stubs

None. All code + refs in this plan are production-grade (no placeholder data, no TODO markers, no unimplemented paths). Film citations in transition-design.md are real (title + year + director under fair-use). Engine routing in transition-engine-routing.md reflects actual verified availability (ffmpeg 6.1.1 + xfade supported; Wan2.2 / Hailuo / Vidu cloud engines documented as opt-in with graceful ffmpeg fallback).

## Threat Flags

None. All files created/modified stay within the documented trust boundaries. The T-74-03 (Tampering — ownership documentation), T-74-04 (Denial of Service — declarative routing), T-74-05 (Tampering — backward-compat schema) threats in the plan's `<threat_model>` are mitigated as specified:
- T-74-03: TRANS-04 field ownership split documented in BOTH cinematographer SKILL.md (creative intent) + editor SKILL.md + p13_delivery.py (execution) with explicit field tables + PITFALL T-4 disambiguation note preventing wrong-step ownership assignment
- T-74-04: INFRA-04 Compliance section in transition-engine-routing.md explicitly states NO runtime LLM decisions (TRANS-10 deferred), all calls under existing glm_concurrent semaphore, NO separate transition semaphore
- T-74-05: cut_transition_type preserved as DEPRECATED alias in e-konte-format.md Layer 5 schema; "Layer 5 字段演变" backward-compat note documents the migration path + load_next_shot_link reader

No new security-relevant surface introduced beyond what the threat model anticipated.

## Self-Check: PASSED

All 7 created/modified files exist on disk. All 3 kais-hermes-skills commits (`eec0b72`, `11e165e`, `7d113da`) found in git log. All 22 tests green (8 p09 unit + 12 transition_schema + 2 syntax checks). All 9 plan-level verification commands pass.
