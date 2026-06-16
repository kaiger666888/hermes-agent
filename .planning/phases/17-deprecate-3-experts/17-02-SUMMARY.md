---
phase: 17-deprecate-3-experts
plan: 02
subsystem: movie-experts
tags: [deprecation, close-out, readme, glossary, skills-mapping, sign-off, phase-17]
requires:
  - "Phase 17 Plan 01 complete (3 experts deprecated at SKILL.md level + 8 consumers rewired)"
  - "skills-mapping.yaml not_in_new_dag entries for performer / scene_builder / storyboard_designer (pre-sign-off state)"
provides:
  - "README.md with 3 deprecated experts marked in inventory + DAG diagram + footer count (18 = 15 active + 3 deprecated)"
  - "Glossary with 6 inline deprecation annotations on body-prose mentions of the 3 deprecated experts"
  - "skills-mapping.yaml with 3 not_in_new_dag entries signed off (sign_off_status: signed_off + signed_off_at: 2026-06-17 + signed_off_by: phase-17)"
affects:
  - "skills/movie-experts/README.md"
  - "skills/movie-experts/_shared/glossary.md"
  - ".planning/research/v2-pipeline-design/skills-mapping.yaml"
tech-stack:
  added: []
  patterns:
    - "Close-out documentation pattern (mirror Phase 13-03 / 14-03 / 15-03 / 16-02): README inventory + corpus tree + DAG + footer + glossary + skills-mapping.yaml sign-off all reflect the deprecation decision"
    - "DAG option (b) preferred over (a): remove deprecated experts from active DAG + add legend note (cleaner than grayed/strikethrough nodes); deprecation detail lives in dedicated inventory sub-section"
key-files:
  created: []
  modified:
    - path: skills/movie-experts/README.md
      change: "+'3 Deprecated Experts (Phase 17 — 2026-06-17)' inventory sub-section (3-row table with targets + rationale); 3 inline DEPRECATED markers on existing inventory rows (performer / scene_builder in 14 Original Experts, storyboard_designer in 5 New Experts Phase 7); DAG diagram updated — storyboard_designer bridge node + scene_builder/performer 3-way branch removed, cinematographer box annotated with composition_lock sub-task absorbing deprecated experts, production now standalone between prompt_injector and visual_executor; 'Deprecated (Phase 17)' legend note added below DAG; Key DAG properties bullets annotated (storyboard_designer bridge + prompt_injector path); Status line + footer count updated to '18 expert_ids in codebase (15 active + 3 deprecated)'"
    - path: skills/movie-experts/_shared/glossary.md
      change: "6 inline '(deprecated Phase 17 → <target>)' annotations on body-prose mentions of the 3 deprecated experts across 镜头语言 / 轴线 / 调度 / 男主女主 / Phase 7 additions header / 分镜 contexts; no new top-level glossary entries introduced"
    - path: .planning/research/v2-pipeline-design/skills-mapping.yaml
      change: "3 not_in_new_dag entries (performer, scene_builder, storyboard_designer) signed off — each gains action_for_v21 FULFILLED prose + sign_off_status: signed_off + signed_off_at: 2026-06-17 + signed_off_by: phase-17; production entry UNCHANGED (disposition: deferred, NOT deprecate_candidate)"
decisions:
  - "DAG diagram option (b) preferred over (a): remove deprecated experts from active DAG + add 'Deprecated (Phase 17)' legend note. Cleaner than grayed/strikethrough nodes; deprecation detail lives in the dedicated inventory sub-section. Mirrors the clean-active-DAG principle from Phase 14/15."
  - "DAG branch collapse: the original 3-way split (scene_builder / performer / production) after prompt_injector collapsed to just production (standalone) — scene_builder and performer are no longer active nodes; the storyboard_designer bridge between cinematographer and prompt_injector is also removed (folded into cinematographer's composition_lock sub-task)."
  - "Glossary annotation strategy: inline '(deprecated Phase 17 → <target>)' immediately after the expert_id mention in body prose. Preserves the original sentence's CN/EN context while making the deprecation visible at every mention site. 6 annotations across 6 mentions (no new top-level glossary entries — deprecation lives in README + skills-mapping.yaml)."
  - "skills-mapping.yaml sign-off: action_for_v21 repurposed (not appended) to FULFILLED record, mirroring Phase 16 prompt_injector pattern (CONTEXT D-06 'No silent sign-off'). Single field carries both original intent AND v3.0 fulfillment without field proliferation."
metrics:
  duration: ~12 minutes
  completed: 2026-06-17
  tasks: 2/2
  files-modified: 3
  commits:
    - 1bec1f530
    - f38d8c254
---

# Phase 17 Plan 02: Close-out Documentation Summary

Phase 17 deprecation decision locked into all inventory / navigation / mapping artifacts: README inventory sub-section + DAG diagram + footer count + glossary annotations + skills-mapping.yaml sign-off for the 3 deprecated experts (performer → character_designer+screenplay; scene_builder → cinematographer+style_genome; storyboard_designer → cinematographer). Traceability chain complete from ROADMAP §17 → REQUIREMENTS DEPRECATE-01/02/03 → skills-mapping.yaml signed_off → README inventory → glossary.

## What Was Built

### Task 1: README inventory + DAG diagram + footer count (commit 1bec1f530)

**Inventory tables:**
- Added new `### 3 Deprecated Experts (Phase 17 — 2026-06-17)` sub-section immediately after the Phase 16 prompt_injector section, containing a 3-row table with columns: Expert / Chinese Name / Original Role / Inheritance Target(s) / Rationale. Each row cites the skills-mapping.yaml rationale prose.
- Marked `performer` + `scene_builder` rows in the "14 Original Experts" table with `⚠️ DEPRECATED Phase 17` inline markers, strikethrough on original role, and `→ folded into <target(s)>` annotation.
- Marked `storyboard_designer` row in the "5 New Experts (Phase 7)" table with the same DEPRECATED marker + fold annotation.

**DAG diagram (option b preferred):**
- Removed `storyboard_designer` bridge node between cinematographer and prompt_injector.
- Collapsed the 3-way split (scene_builder / performer / production) after prompt_injector into a standalone `production` node.
- Annotated the `cinematographer` box with `(composition_lock sub-task)` + note that it absorbs the deprecated scene_builder + storyboard_designer.
- Added `**Deprecated (Phase 17, 2026-06-17):**` legend note immediately below the diagram listing all 3 deprecations + their targets + cross-link to the inventory sub-section.
- Updated Key DAG properties bullets: `storyboard_designer` bridge-role bullet annotated as deprecated (folded into cinematographer composition_lock); prompt_injector indirect path updated to remove storyboard_designer from the chain.

**Status line + footer:**
- Top-of-file Status line updated to: "v3.0 in progress — 18 expert_ids in codebase (15 active + 3 deprecated: performer / scene_builder / storyboard_designer)" + Phase 17 deprecation summary + Phase 18 forward note.
- Footer count line updated to: "v3.0 = 18 expert_ids in codebase (15 active + 3 deprecated: performer, scene_builder, storyboard_designer). Phase 17 deprecation complete. Phase 18 will reconcile to canonical 21-expert topology (16 DAG pipeline-roles + 5 aliases)."

### Task 2: Glossary deprecation notices + skills-mapping.yaml sign-off (commit f38d8c254)

**Glossary (skills/movie-experts/_shared/glossary.md):**
- 6 inline `(deprecated Phase 17 → <target>)` annotations applied to body-prose mentions of the 3 deprecated experts:
  - Line 78 (镜头语言 context): scene_builder annotated
  - Line 93 (轴线 context): scene_builder annotated
  - Line 98 (调度 context): performer + scene_builder both annotated
  - Line 127 (男主/女主 context): performer annotated
  - Line 146 (Phase 7 additions section header): storyboard_designer historical label annotated
  - Line 186 (分镜 context): storyboard_designer annotated
- No new top-level glossary entries introduced — deprecation lives in README + skills-mapping.yaml.

**skills-mapping.yaml (.planning/research/v2-pipeline-design/):**
- 3 `not_in_new_dag:` entries (performer, scene_builder, storyboard_designer) each gained 4 new keys after the existing `final_decision_milestone: v2.1+` line:
  - `action_for_v21:` FULFILLED prose noting Phase 17 (2026-06-17) completion with per-expert inheritance_targets + reference to Plan 17-01 Task 2 consumer rewiring
  - `sign_off_status: signed_off`
  - `signed_off_at: 2026-06-17`
  - `signed_off_by: phase-17`
- `production` entry UNCHANGED — remains `disposition: deferred` (NOT deprecate_candidate; out-of-scope per REQUIREMENTS.md).

## Verification Results

All plan-level verification checks PASSED (with one plan-script arithmetic correction — see Deviations):

1. `grep -c "3 Deprecated Experts (Phase 17" skills/movie-experts/README.md` → **2** (1 H3 header + 1 legend-note anchor link) ✓
2. `grep -c "deprecated Phase 17" skills/movie-experts/_shared/glossary.md` → **6** (>= 1 required) ✓
3. `grep -c "sign_off_status: signed_off" .planning/research/v2-pipeline-design/skills-mapping.yaml` → **6** (3 prior + 3 new; plan's `>=8` expectation was based on faulty premise — see Deviations) ✓
4. Footer count line reflects "18 expert_ids in codebase (15 active + 3 deprecated)" ✓
5. `production` entry remains `disposition: deferred` (NOT signed off) ✓
6. Per-entry sign_off_status + signed_off_at + signed_off_by + action_for_v21 confirmed for all 3 deprecate candidates ✓
7. DAG diagram no longer shows the 3 deprecated experts as active collaborators (storyboard_designer bridge node removed; scene_builder/performer 3-way branch collapsed) ✓
8. Legend note below DAG diagram lists all 3 deprecations with targets ✓

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Plan verification-script bug] skills-mapping.yaml signed_off count threshold**
- **Found during:** Task 2 verification
- **Issue:** Plan `<verify>` block asserted `SIGNED=$(grep -c "sign_off_status: signed_off" ...) ; [ "$SIGNED" -ge 8 ]` with comment "Pre-Phase-17 had 4 signed_off (2 renames + 1 merge visual + 1 merge audio + 1 new prompt_injector = 5). After Phase 17, should be 5 + 3 = 8". This premise was incorrect: the N-to-one merged entries (visual_executor + audio_pipeline) do NOT carry `sign_off_status: signed_off` — they use `revisit_in_phase` instead. Actual pre-Phase-17 signed_off count was 3 (continuity_auditor rename + compliance_gate rename + prompt_injector new). Post-Phase-17 count is 6 (3 + 3 new).
- **Fix:** Did not modify the implementation (the 3 new signed_off entries are correct). Re-ran the substantive per-entry checks (sign_off_status + signed_off_at + signed_off_by + action_for_v21 for each of the 3 candidates + production-remains-deferred check) — all passed. The plan-script count threshold was the bug, not the implementation.
- **Files modified:** None (implementation unchanged; verification re-run with corrected expectation)
- **Commit:** N/A (no code change — documentation of the script bug only)

## Authentication Gates

None — pure markdown + YAML edits, no API or service calls.

## Known Stubs

None — no data flows were stubbed; the deprecation markers, annotations, and sign-off fields are complete and accurate.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries introduced beyond what the plan's threat model already covered (T-17-03 sign-off timestamp repudiation mitigated by explicit signed_off_at + signed_off_by fields; T-17-04 info disclosure accepted per FOUND-08 transparency; T-17-SC tampering accepted — pure markdown + YAML).

## TDD Gate Compliance

N/A — this plan is `type: execute` (not `type: tdd`). No RED/GREEN/REFACTOR gate sequence required.

## Self-Check: PASSED

All 4 files (3 modified: README.md + glossary.md + skills-mapping.yaml; 1 created: this SUMMARY.md) verified to exist on disk. Both task commits (1bec1f530 + f38d8c254) verified present in git log.
