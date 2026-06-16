---
phase: 15-audio-pipeline-merge
plan: 02
subsystem: skills/movie-experts
tags: [merge, n-to-one, consumer-edge-sync, bidirectional-edges, expert-id, audio_pipeline, voicer, lip_sync, composer, foley, mixer, spatial_audio, dedup, backward-compat, directional-edge, d-7]
requires:
  - 15-01-PLAN (source-level merge producing audio_pipeline with 6-item sub_steps)
  - skills-mapping.yaml (n_to_one_merged mapping entry for audio_pipeline)
  - FOUND-08 (zero-silent-rename rule — aliases propagate)
provides:
  - Bidirectional related_skills edges between audio_pipeline and 10 consumers (8 from plan + production + colorist body-only)
  - Zero stranded audio expert_id references (voicer, lip_sync, composer, foley, mixer, spatial_audio) outside the 6 redirect stubs
  - Directional edge D-7 preserved (hook_retention → audio_pipeline one-way)
affects:
  - 11 consumer SKILL.md files (character_designer, editor, hook_retention, performer, scene_builder, screenplay, style_genome, visual_executor, animation_studio, production, colorist)
tech-stack:
  added: []
  patterns:
    - "Bidirectional edge sync post-merge: audio_pipeline lists consumers (15-01) + consumers list audio_pipeline back (15-02)"
    - "Multi-entry collapse rule (editor): when a consumer lists MULTIPLE audio experts in related_skills (editor: voicer + composer + mixer), replace ALL with exactly ONE audio_pipeline entry"
    - "Add-edge rule (visual_executor, production): when a consumer lists ZERO audio experts but audio_pipeline lists this consumer, ADD audio_pipeline for bidirectional consistency"
    - "Body-only rule (colorist): when a consumer has body audio references but is NOT in audio_pipeline.related_skills, update body prose only — preserves the directional edge semantics"
    - "Sub-step annotation strategy: Collaboration bullets + artifact paths + DAG nodes carry `(composer sub-step)` / `(voicer sub-step)` / `(foley sub-step)` / `(mixer sub-step)` / `(lip_sync sub-step)` inline annotations to preserve operational routing context lost in the N→1 collapse"
    - "DAG pipeline string consolidation (style_genome + production): `(visual_executor, voicer, colorist, editor, composer, foley, spatial_audio, continuity_auditor) -> mixer -> final` → `(visual_executor, audio_pipeline, colorist, editor, continuity_auditor) -> final` (6 audio nodes collapse to 1; the `-> mixer -> final` suffix folds into audio_pipeline which IS the audio mastering node)"
    - "Artifact path prefix migration: `composer.coupled_beat.json` → `audio_pipeline.composer.coupled_beat.json` (dotted sub-step form preferred for path-like references; preserves the artifact filename contract)"
key-files:
  created: []
  modified:
    - skills/movie-experts/character_designer/SKILL.md
    - skills/movie-experts/editor/SKILL.md
    - skills/movie-experts/hook_retention/SKILL.md
    - skills/movie-experts/performer/SKILL.md
    - skills/movie-experts/scene_builder/SKILL.md
    - skills/movie-experts/screenplay/SKILL.md
    - skills/movie-experts/style_genome/SKILL.md
    - skills/movie-experts/visual_executor/SKILL.md
    - skills/movie-experts/animation_studio/SKILL.md
    - skills/movie-experts/production/SKILL.md
    - skills/movie-experts/colorist/SKILL.md
decisions:
  - "Deviation (Rule 2 — Plan audit incompleteness): plan <files_modified> + <interfaces> audit table enumerated 9 consumers but the actual corpus contained 11. Two additional consumers (production, colorist) had stranded audio expert_id references (production: `**-> voicer**` Collaboration bullet + voicer/composer/foley/mixer in DAG pipeline string + voicer in cross-expert coordination bullets; colorist: `**-> mixer**` Collaboration bullet). The plan's own success criterion 'Zero stranded **-> {audio_id}** Collaboration bullets outside redirect stubs' was load-bearing — applied the edge sync to both. production gets bidirectional audio_pipeline edge (audio_pipeline lists production); colorist gets body-only update (directional edge preserved — audio_pipeline does NOT list colorist, so no related_skills add)."
  - "animation_studio deviation (Rule 1 — Plan audit inaccuracy): plan <interfaces> table claimed 'animation_studio: NONE in related_skills per audit — body prose only'. Actual file state (lines 18-19 of pre-edit file) had `- composer` + `- voicer` as explicit multi-line related_skills entries. Applied the collapse rule: replaced both with single `- audio_pipeline` line (annotated with both sub-step roles in inline comment). Same deviation pattern as Phase 14's animation_studio drawer/animator audit miss."
  - "Sub-step annotation strategy for merged Collaboration bullets + artifact paths: inline-annotated each sub-step's specific contract — e.g., editor `**<- audio_pipeline (composer sub-step)**: coupled_beat.json + light_beat.json` preserves the composer-specific BGM-driven cut sync contract; `audio_pipeline.composer.coupled_beat.json` artifact path preserves the filename contract while routing through the merged expert. Matches Phase 14 sub-step annotation pattern."
  - "DAG pipeline string consolidation in style_genome + production: original strings had 5-6 audio IDs scattered across stages + a `-> mixer -> final` suffix. Post-merge all audio nodes collapse to ONE `audio_pipeline` node. The `-> mixer` final stage folds INTO audio_pipeline (mixer is now an internal sub-step, not a downstream peer) — so the suffix becomes `-> final` directly. Avoids ambiguous duplicate `audio_pipeline` entries in a non-array DAG-string context."
  - "Bare-noun 'foley-documentary' tag in documentary_maker/SKILL.md line 12 PRESERVED — this is a hyphenated descriptor for documentary-style foley work (a TAG, not an expert_id reference). Out of scope per English-noun preservation rule."
  - "Directional edge CONTEXT D-7 preservation: hook_retention → audio_pipeline edge remains one-way (hook_retention.related_skills includes audio_pipeline; audio_pipeline.related_skills does NOT include hook_retention). Plan 15-01 already enforced the exclusion; this plan did NOT modify audio_pipeline/SKILL.md so the exclusion holds. Verified post-edit: `grep 'related_skills' audio_pipeline/SKILL.md` shows no `hook_retention` token."
metrics:
  duration: ~6 min
  completed: 2026-06-17
  tasks_completed: 1
  tasks_total: 1
  files_created: 0
  files_modified: 11
---

# Phase 15 Plan 02: Consumer Edge Sync Summary

Propagated the voicer + lip_sync + composer + foley + mixer + spatial_audio → audio_pipeline merge across all 11 non-audio consumer SKILL.md files (9 enumerated in plan + 2 deviation discoveries: production + colorist), closing the bidirectional edge sync required by ROADMAP §15 success criterion #4. Every consumer's `metadata.hermes.related_skills` array that previously listed any of the 6 audio expert_ids now lists `audio_pipeline` (deduplicated — never multiple entries), and every body prose reference to any audio expert_id (markdown links, Collaboration bullets, JSON literals, JSON artifact paths, DAG pipeline strings, narrative pair references) is updated to `audio_pipeline` with sub-step annotations where the specific sub-step matters for edge semantics.

## What Was Done

### Task 1 — Updated 11 consumer SKILL.md files (commit `35dd7c705`)

**related_skills array changes (9 consumers with array edits):**

| Consumer | Before | After | Rule applied |
|----------|--------|-------|--------------|
| character_designer | `[..., lip_sync, production]` | `[..., audio_pipeline, production]` | Single-edge (lip_sync → audio_pipeline) |
| editor | `[..., composer, voicer, continuity_auditor, mixer, ...]` | `[..., audio_pipeline, continuity_auditor, ...]` | Multi-entry collapse (3 → 1) |
| hook_retention | `[..., composer, cinematographer]` | `[..., audio_pipeline, cinematographer]` | Single-edge + D-7 directional preserved |
| performer | `[..., voicer, ...]` | `[..., audio_pipeline, ...]` | Single-edge |
| scene_builder | `[..., foley, ...]` | `[..., audio_pipeline, ...]` | Single-edge |
| screenplay | `[..., composer, ...]` | `[..., audio_pipeline, ...]` | Single-edge |
| style_genome | `[..., composer, ...]` | `[..., audio_pipeline, ...]` | Single-edge |
| visual_executor | (no audio entry) | appended `audio_pipeline` | Add-edge (audio_pipeline lists visual_executor — bidirectional) |
| animation_studio | multi-line `- composer` + `- voicer` (deviation) | single `- audio_pipeline` line | Multi-entry collapse (2 → 1) |
| production | (no audio entry, but audio_pipeline lists production) | inserted `audio_pipeline` | Add-edge (deviation discovery — bidirectional) |
| colorist | (no audio entry, audio_pipeline does NOT list colorist) | UNCHANGED | Body-only rule (directional edge preserved) |

**Body prose changes (per consumer):**

- **character_designer**: description (calling sequence `→ lip_sync` → `→ audio_pipeline (lip_sync sub-step)`), When-to-use narrative (downstream experts list), Philosophy bullet (下游可消费的契约), JSON literal `"lip_sync"` → `"audio_pipeline"` in downstream_consumers array, Workflow step 10 (Hand off), Collaboration bullet (`-> lip_sync` markdown link → `-> audio_pipeline (lip_sync sub-step)`). Preserved: line 47 "drawer 关心怎么画" + line 268 "drawer 容易漂移" (English-noun usages from Phase 14, no link).
- **editor**: heavy edits — 3 related_skills audio entries collapsed to ONE audio_pipeline; Core Capabilities bullet (`composer.coupled_beat.json` → `audio_pipeline.composer.coupled_beat.json`), beat_alignment parameter (with composer's coupled_beat → with audio_pipeline (composer sub-step)'s coupled_beat), Workflow step 9 (BGM Sync artifact path), Collaboration bullets (`<- composer` + `<- voicer` → `<- audio_pipeline (composer sub-step)` + `<- audio_pipeline (voicer sub-step)`; `-> composer` + `-> mixer` → `-> audio_pipeline (composer sub-step)` + `-> audio_pipeline (mixer sub-step)`), What-NOT-to-do bullet (Don't ignore composer's coupled_beat → Don't ignore audio_pipeline (composer sub-step)'s coupled_beat).
- **hook_retention**: related_skills comment rewritten (composer one-directional → audio_pipeline (composer sub-step) one-directional, CONTEXT D-7); Output Format narrative (供下游 screenplay / editor / composer → screenplay / editor / audio_pipeline (composer sub-step)); Rhythm parameter (cut 必须落在 composer.coupled_beat → audio_pipeline.composer.coupled_beat); Collaboration bullet (`-> composer` → `-> audio_pipeline (composer sub-step)` with directional edge annotation preserved).
- **performer**: Collaboration bullet (`-> voicer` → `-> audio_pipeline (voicer sub-step)`).
- **scene_builder**: 5 foley references — Output Format field (`for foley` → `for audio_pipeline (foley sub-step)`), Material Annotation parameter (`for foley`), Workflow step 7 (`for foley`), Collaboration bullet (`-> foley` → `-> audio_pipeline (foley sub-step)`), What-NOT-to-do bullet (foley depends on them → audio_pipeline (foley sub-step) depends on them).
- **screenplay**: Collaboration bullet (`-> composer` → `-> audio_pipeline (composer sub-step)`).
- **style_genome**: Cross-Module Alignment table row (`| composer |` → `| audio_pipeline (composer sub-step) |`), Cross-Module Alignment bullet (composer: sound dimension → audio_pipeline (composer sub-step): sound dimension), Collaboration bullet (`-> composer` → `-> audio_pipeline (composer sub-step)`), Pipeline Position DAG string consolidated (6 audio nodes in one stage + `-> mixer -> final` suffix → ONE audio_pipeline node + `-> final`; the mixer stage folds INTO audio_pipeline since mixer is now an internal sub-step).
- **visual_executor**: related_skills ADD audio_pipeline (appended at end of array — bidirectional edge with audio_pipeline from plan 15-01). Body had zero audio references (Phase 14 migration cleaned them).
- **animation_studio** (DEVIATION): related_skills multi-line block (`- composer` + `- voicer` → single `- audio_pipeline` line with combined sub-step comment); description (Complements `visual_executor`, `composer` → Complements `visual_executor`, `audio_pipeline`); AI 短剧 workflow step 4 (TTS via voicer → TTS via audio_pipeline (voicer sub-step)); Integration-with-Other-Experts bullets (`composer` + `voicer` rows → `audio_pipeline (composer sub-step)` + `audio_pipeline (voicer sub-step)` rows); Cross-References markdown links (`../composer/SKILL.md` + `../voicer/SKILL.md` → single `../audio_pipeline/SKILL.md` row with both sub-step annotations).
- **production** (DEVIATION): related_skills ADD audio_pipeline (audio_pipeline lists production → bidirectional); Core Capabilities cross-expert coordination list (voicer → audio_pipeline (voicer sub-step)); Workflow step 7 (Hand off to voicer → Hand off to audio_pipeline (voicer sub-step)); Collaboration bullet (`-> voicer` → `-> audio_pipeline (voicer sub-step)`); Pipeline Position DAG string consolidated (4 audio nodes + `-> mixer -> final` suffix → ONE audio_pipeline node + `-> final`).
- **colorist** (DEVIATION): body-only — Collaboration bullet (`-> mixer` → `-> audio_pipeline (mixer sub-step)`). related_skills UNCHANGED (directional edge preserved — audio_pipeline does NOT list colorist).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — Plan audit incompleteness] production + colorist had stranded audio expert_id references**

- **Found during:** Task 1 consolidated verification sweep (comprehensive grep beyond plan's 9-file list)
- **Issue:** Plan `<files_modified>` enumerated 9 consumer SKILL.md files. Plan `<interfaces>` audit table did not list `production` or `colorist`. However:
  - `skills/movie-experts/production/SKILL.md` had 4 stranded audio references: `**-> voicer**` Collaboration bullet (line 175), `voicer / composer / foley` in Pipeline Position DAG string (line 197), `voicer` in Cross-Expert Coordination bullets (lines 76, 154). Additionally, `audio_pipeline.related_skills` (set in plan 15-01) INCLUDES `production` — bidirectional edge sync requires production to list audio_pipeline back.
  - `skills/movie-experts/colorist/SKILL.md` had 1 stranded audio reference: `**-> mixer**` Collaboration bullet (line 176). `audio_pipeline.related_skills` does NOT include colorist — directional edge preserved, so body-only update.
- **Plan's own success criterion made this load-bearing:** `<success_criteria>` explicitly required "Zero stray `**-> {audio_id}**` or `**<- {audio_id}**` Collaboration bullets outside redirect stubs". Leaving production's `**-> voicer**` and colorist's `**-> mixer**` would have violated this criterion.
- **Fix:** Applied the same edge sync rules to both files. production: add audio_pipeline to related_skills (bidirectional) + collapse all body references with sub-step annotations + consolidate DAG pipeline string. colorist: body-only update (mixer → audio_pipeline (mixer sub-step)), related_skills unchanged.
- **Files modified:** skills/movie-experts/production/SKILL.md, skills/movie-experts/colorist/SKILL.md
- **Commit:** 35dd7c705

**2. [Rule 1 — Plan audit inaccuracy] animation_studio DID list composer + voicer in related_skills**

- **Found during:** Task 1 initial grep (before any edits)
- **Issue:** Plan `<interfaces>` audit table claimed "animation_studio: NONE in related_skills per audit — body prose references only". Plan `<behavior>` said "animation_studio: NO related_skills change (audit confirms it doesn't list audio experts there)". Plan `<acceptance_criteria>` explicitly excluded animation_studio from consumers expected to have audio_pipeline in related_skills.
- **Reality:** `skills/movie-experts/animation_studio/SKILL.md` lines 18-19 (pre-edit) had a multi-line related_skills block explicitly listing `- composer` (line 18) and `- voicer` (line 19).
- **Fix:** Applied the collapse rule — replaced both lines with a single `- audio_pipeline` line (preserving the comment style, combined sub-step annotation inline). The 10 consumers with audio_pipeline in related_skills (instead of the originally-claimed 8) is the correct outcome.
- **Files modified:** skills/movie-experts/animation_studio/SKILL.md
- **Commit:** 35dd7c705

**3. [Sub-step context preservation] Body prose merge strategy**

- **Found during:** Task 1 edits to editor, hook_retention, scene_builder, screenplay, style_genome, animation_studio, production, colorist
- **Issue:** Pure collapse of multiple audio references into a single `audio_pipeline` token would lose operational routing context (e.g., editor's coupled_beat.json specifically comes from the composer sub-step; scene_builder's material_annotations.json specifically feeds the foley sub-step).
- **Fix:** Adopted sub-step annotation pattern — every body reference that previously named a specific audio expert now carries `(composer sub-step)` / `(voicer sub-step)` / `(lip_sync sub-step)` / `(foley sub-step)` / `(mixer sub-step)` inline. Artifact path references use the dotted form (`audio_pipeline.composer.coupled_beat.json`) for path-like references. Matches Phase 14's sub-step annotation pattern for visual_executor's drawer/animator sub-steps.
- **Files modified:** Multiple consumer SKILL.md Collaboration sections + body prose
- **Commit:** 35dd7c705

## Verification Results

All consolidated verification checks passed:

- [x] **Check 1 (strict, value-only):** No consumer related_skills array VALUE (before `#` comment) contains any of {voicer, lip_sync, composer, foley, mixer, spatial_audio} as standalone token. (hook_retention's apparent "composer" hit was in the inline comment, not the array value — verified by stripping `#.*$` before grep.)
- [x] **Check 2:** All 9 consumers expected to have audio_pipeline in related_skills now do (character_designer, editor, hook_retention, performer, scene_builder, screenplay, style_genome, visual_executor, animation_studio) — plus the 2 deviation additions (production). colorist correctly excluded (directional edge).
- [x] **Check 3:** No consumer has DUPLICATE audio_pipeline entries in related_skills (collapse rule held — apparent hook_retention duplicate was comment artifact, not array value).
- [x] **Check 4:** Zero stray `(../{audio_id}/SKILL.md)` markdown links outside the 6 audio redirect stubs.
- [x] **Check 5:** Zero stray `**-> {audio_id}**` or `**<- {audio_id}**` Collaboration bullets outside redirect stubs (after production + colorist deviation fixes).
- [x] **Check 6:** Zero stray `"{audio_id}",` JSON literals outside redirect stubs (character_designer's `"lip_sync"` → `"audio_pipeline"` applied).
- [x] **Check 7:** `_eval/baseline/{voicer,composer,foley,mixer,spatial_audio}/SKILL.md` retain their original expert_id values (frozen regression baselines untouched). lip_sync has no _eval/baseline snapshot (only _eval/prompts/).
- [x] **Check 8:** Redirect stubs in 6 audio directories preserve their old `expert_id` fields (backward-compat).
- [x] **Check 9:** Phase 13 tokens preserved — `continuity_auditor` + `compliance_gate` directories + expert_id fields intact.
- [x] **Check 10:** Phase 14 tokens preserved — `visual_executor` directory + expert_id field + drawer/animator sub_steps intact; visual_executor now has bidirectional edge with audio_pipeline.
- [x] **Check 11:** DAG pipeline strings in style_genome + production collapse 6 audio nodes to ONE audio_pipeline node, with `-> mixer -> final` suffix folding INTO audio_pipeline (mixer is internal sub-step).
- [x] **Check 12:** JSON artifact path references (`composer.coupled_beat.json`) updated to `audio_pipeline.composer.coupled_beat.json` in editor + hook_retention.
- [x] **Check 13:** Sub-step annotations (`(composer sub-step)`, `(voicer sub-step)`, etc.) preserved where specific edge matters.
- [x] **Check 14:** Directional edge D-7 preserved — `audio_pipeline.related_skills` does NOT include `hook_retention` (verified: `grep 'related_skills' audio_pipeline/SKILL.md | grep -q hook_retention` returns no match).
- [x] **Check 15:** English-noun usages preserved — documentary_maker tag `foley-documentary` (hyphenated descriptor, not expert_id) untouched; character_designer bare-noun `drawer` usages from Phase 14 preserved.

## Self-Check: PASSED

### Files modified (all 11 verified modified)

- FOUND (modified): skills/movie-experts/character_designer/SKILL.md
- FOUND (modified): skills/movie-experts/editor/SKILL.md
- FOUND (modified): skills/movie-experts/hook_retention/SKILL.md
- FOUND (modified): skills/movie-experts/performer/SKILL.md
- FOUND (modified): skills/movie-experts/scene_builder/SKILL.md
- FOUND (modified): skills/movie-experts/screenplay/SKILL.md
- FOUND (modified): skills/movie-experts/style_genome/SKILL.md
- FOUND (modified): skills/movie-experts/visual_executor/SKILL.md
- FOUND (modified): skills/movie-experts/animation_studio/SKILL.md
- FOUND (modified): skills/movie-experts/production/SKILL.md
- FOUND (modified): skills/movie-experts/colorist/SKILL.md

### Commits (verified exist)

- FOUND: 35dd7c705 (refactor(15-02): sync audio_pipeline edges across 11 consumer SKILL.md files)
