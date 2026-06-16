---
phase: 14-visual-executor-merge
plan: 01
subsystem: skills/movie-experts
tags: [merge, n-to-one, sub-steps, backward-compat, expert-id, visual_executor, drawer, animator]
requires:
  - skills-mapping.yaml (n_to_one_merged mapping entry for visual_executor)
  - FOUND-08 (zero-silent-rename rule)
provides:
  - skills/movie-experts/visual_executor/ (merged expert with sub_steps metadata)
  - skills/movie-experts/drawer/SKILL.md (redirect-only stub)
  - skills/movie-experts/animator/SKILL.md (redirect-only stub)
affects:
  - 17 consumer SKILL.md related_skills arrays (edge sync deferred to plan 14-02)
tech-stack:
  added: []
  patterns:
    - "N-to-one merge pattern: new dir + sub_steps frontmatter + redirect stubs + metadata.hermes.aliases"
    - "Sub-folder refs strategy: references/{drawer,animator}/ for predecessor-specific knowledge"
    - "Intra-expert handoff rewriting: drawer<->animator Collaboration bullets rewritten as internal-handoff notes pointing to Sub-step sections"
key-files:
  created:
    - skills/movie-experts/visual_executor/SKILL.md
    - skills/movie-experts/visual_executor/GAP-REPORT.md
    - skills/movie-experts/visual_executor/references/drawer/LICENSE.md
    - skills/movie-experts/visual_executor/references/drawer/flux2-parameter-surface.md
    - skills/movie-experts/visual_executor/references/drawer/character-consistency-lora.md
    - skills/movie-experts/visual_executor/references/animator/LICENSE.md
    - skills/movie-experts/visual_executor/references/animator/video-gen-model-matrix.md
    - skills/movie-experts/visual_executor/references/animator/temporal-consistency.md
    - skills/movie-experts/visual_executor/references/animator/camera-execution-and-degradation.md
  modified:
    - skills/movie-experts/drawer/SKILL.md
    - skills/movie-experts/animator/SKILL.md
decisions:
  - "Applied FOUND-08: declare metadata.hermes.aliases: [drawer, animator] on new SKILL.md for backward-compat dispatch"
  - "Introduced NEW top-level frontmatter field `sub_steps: [drawer, animator]` per v2.0 PRFP DAG convention (declared at same level as `metadata`, NOT nested inside it)"
  - "Preserved old drawer/ + animator/ directories' references/ and GAP-REPORT.md files untouched (archival); only SKILL.md became redirect stub — same pattern as Phase 13 continuity/ + compliance_marketing/"
  - "Refs organized into sub-folders (references/drawer/ + references/animator/) per CONTEXT.md Claude's-discretion recommendation — cleaner than filename-prefix strategy"
  - "Drawer<->animator Collaboration bullets rewritten as internal-handoff notes pointing to Sub-step sections (not deleted) — preserves the operational contract while making the intra-expert nature explicit"
  - "RAG query tag prefix migrated from expert:{drawer|animator},domain:X to expert:visual_executor,sub:{drawer|animator},domain:X — preserves the domain axis while introducing sub-step scoping"
  - "Provider-agnostic placeholders <video_gen_primary> / <video_gen_preview> / <video_gen_fallback> are intentional design (CONTEXT.md §Claude's Discretion + PITFALLS §1.3 anti-premature-model-commitment) — NOT stub patterns"
metrics:
  duration: ~3 min
  completed: 2026-06-17
  tasks_completed: 2
  tasks_total: 2
  files_created: 9
  files_modified: 2
---

# Phase 14 Plan 01: drawer + animator → visual_executor Merge Summary

Merged v1 `drawer` (FLUX 2 image gen) + `animator` (video gen) movie-experts into a unified `visual_executor` expert per MERGE-01 (Phase 7 §4.8 + PITFALLS §2.1: "consistency context unified; specialization loss acceptable"), introducing the new top-level `sub_steps: [drawer, animator]` frontmatter field per v2.0 PRFP DAG convention and declaring FOUND-08 backward-compat aliases.

## What Was Done

### Task 1 — Created `visual_executor/` merged expert (commit `240725bc6`)

- New `skills/movie-experts/visual_executor/` directory
- **SKILL.md** frontmatter:
  - `name: visual_executor`, `expert_id: visual_executor`, `version: 1.0.0` (new baseline — not inherited from predecessors)
  - **NEW top-level field:** `sub_steps: [drawer, animator]` (declared at same level as `metadata`, per v2.0 PRFP DAG)
  - `metadata.hermes.aliases: [drawer, animator]` (FOUND-08 backward-compat)
  - `metadata.hermes.related_skills` = exact 10-item union: `[screenplay, continuity_auditor, colorist, style_genome, compliance_gate, cinematographer, production, scene_builder, editor, performer]` (drawer + animator edges, deduped, no self-references)
  - `metadata.hermes.tags` = union of drawer + animator tags (deduped)
  - `metadata.hermes.metrics` = union of drawer + animator metrics (deduped)
  - `prerequisites.tools` = union [hermes_llm, hermes_llm_vision]
- **Body structure** (per plan `<behavior>`):
  1. H1 `# Visual Executor Expert (视觉执行专家)` + intro paragraph stating unified role
  2. `## When to use this skill` (merged — both stills and video use cases)
  3. `## Sub-steps` (NEW — table naming drawer + animator sub-steps with role / trigger / output, plus handoff contract paragraph)
  4. `## References` table listing all 5 refs with paths to `./references/drawer/*` and `./references/animator/*`
  5. `## Knowledge Retrieval` (4 query topics, 2 drawer + 2 animator; RAG tag prefixes migrated to `expert:visual_executor,sub:drawer|animator`)
  6. `## Sub-step: Drawer (Image Generation)` — full drawer body from `## Role & Philosophy` through `## What NOT to do`; internal ref links updated to `./references/drawer/*.md`; old References + Knowledge Retrieval sections removed (they live at top of merged file)
  7. `## Sub-step: Animator (Video Generation)` — full animator body, same treatment with `./references/animator/*.md`
  8. `## Collaboration` (merged) — drawer `-> animator` bullet rewritten as "→ [internal handoff to Animator sub-step — see §Sub-step: Animator above]"; animator `<- drawer` bullet rewritten as "← [internal handoff from Drawer sub-step — see §Sub-step: Drawer above]"; all other Collaboration edges (cinematographer, colorist, continuity_auditor, editor, scene_builder, performer, production, screenplay, style_genome, compliance_gate) preserved as inter-expert edges
  9. `## Changelog` section at bottom documenting the merge: date 2026-06-17, predecessors drawer v1.1.0 + animator v1.1.0 → visual_executor v1.0.0, rationale citing Phase 7 §4.8 + PITFALLS §2.1, aliases declared per FOUND-08
- **7 ref files** migrated verbatim (no content edits) to sub-folders:
  - `references/drawer/LICENSE.md`, `references/drawer/flux2-parameter-surface.md`, `references/drawer/character-consistency-lora.md`
  - `references/animator/LICENSE.md`, `references/animator/video-gen-model-matrix.md`, `references/animator/temporal-consistency.md`, `references/animator/camera-execution-and-degradation.md`
- **GAP-REPORT.md** consolidates both predecessors with two sections: `## Drawer GAP-REPORT (migrated)` and `## Animator GAP-REPORT (migrated)`, each containing the verbatim body of the corresponding old GAP-REPORT.md

### Task 2 — Replaced drawer + animator SKILL.md with redirect stubs (commit `811b56052`)

- `skills/movie-experts/drawer/SKILL.md` replaced with frontmatter-only redirect stub (15 lines):
  - `name: drawer`, `expert_id: drawer` (retained for backward-compat dispatch)
  - `metadata.hermes.status: merged_into`, `merged_into: visual_executor`, `aliases: [visual_executor]` (forward alias)
  - Description prefixed "DEPRECATED — merged into visual_executor (Phase 14 MERGE-01)"
  - 1 paragraph after frontmatter with working markdown link `../visual_executor/SKILL.md`
- `skills/movie-experts/animator/SKILL.md` replaced with analogous stub
- Old `drawer/references/`, `drawer/GAP-REPORT.md`, `animator/references/`, `animator/GAP-REPORT.md` preserved untouched (archival — same pattern as Phase 13's continuity/ + compliance_marketing/)

## Deviations from Plan

None — plan executed exactly as written. All success criteria verified.

## Verification Results

All plan success criteria verified:

- [x] `skills/movie-experts/visual_executor/SKILL.md` exists with `sub_steps: [drawer, animator]` declared at top level
- [x] `metadata.hermes.related_skills` is the exact 10-item union (no drawer/animator self-refs, no dupes)
- [x] `metadata.hermes.aliases: [drawer, animator]` declared
- [x] `metadata.hermes.expert_id: visual_executor` declared
- [x] `version: 1.0.0` (new expert baseline)
- [x] Body has two clearly-marked `## Sub-step: Drawer (Image Generation)` and `## Sub-step: Animator (Video Generation)` H2 sections
- [x] All 7 ref files migrated under `references/{drawer,animator}/` sub-folders (verbatim)
- [x] `GAP-REPORT.md` consolidates both predecessors
- [x] All internal ref markdown links updated to sub-folder paths
- [x] All RAG query tags use `expert:visual_executor,sub:{drawer|animator}` prefix
- [x] Drawer→animator + animator←drawer Collaboration bullets rewritten as internal-handoff notes
- [x] Changelog section appended
- [x] Old `drawer/SKILL.md` is a redirect stub (frontmatter-only + 1 paragraph, `status: merged_into` + `merged_into: visual_executor`)
- [x] Old `animator/SKILL.md` is a redirect stub (same shape)
- [x] Old `drawer/references/`, `drawer/GAP-REPORT.md`, `animator/references/`, `animator/GAP-REPORT.md` preserved untouched

## Self-Check: PASSED

### Files created (verified exist)
- FOUND: skills/movie-experts/visual_executor/SKILL.md
- FOUND: skills/movie-experts/visual_executor/GAP-REPORT.md
- FOUND: skills/movie-experts/visual_executor/references/drawer/LICENSE.md
- FOUND: skills/movie-experts/visual_executor/references/drawer/flux2-parameter-surface.md
- FOUND: skills/movie-experts/visual_executor/references/drawer/character-consistency-lora.md
- FOUND: skills/movie-experts/visual_executor/references/animator/LICENSE.md
- FOUND: skills/movie-experts/visual_executor/references/animator/video-gen-model-matrix.md
- FOUND: skills/movie-experts/visual_executor/references/animator/temporal-consistency.md
- FOUND: skills/movie-experts/visual_executor/references/animator/camera-execution-and-degradation.md

### Files modified (verified)
- FOUND: skills/movie-experts/drawer/SKILL.md (now redirect stub)
- FOUND: skills/movie-experts/animator/SKILL.md (now redirect stub)

### Commits (verified exist)
- FOUND: 240725bc6 (feat(14-01): create visual_executor merged expert (drawer + animator))
- FOUND: 811b56052 (refactor(14-01): replace drawer + animator SKILL.md with redirect stubs)
