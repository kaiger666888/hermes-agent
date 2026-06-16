---
phase: 15-audio-pipeline-merge
plan: 01
subsystem: skills/movie-experts
tags: [merge, n-to-one, sub-steps, backward-compat, expert-id, audio_pipeline, voicer, lip_sync, composer, foley, mixer, spatial_audio, fold-disposition]
requires:
  - skills-mapping.yaml (n_to_one_merged mapping entry for audio_pipeline)
  - FOUND-08 (zero-silent-rename rule)
provides:
  - skills/movie-experts/audio_pipeline/ (merged expert with sub_steps metadata — 6 sub-steps)
  - skills/movie-experts/voicer/SKILL.md (redirect-only stub, status: merged_into)
  - skills/movie-experts/lip_sync/SKILL.md (redirect-only stub, status: merged_into)
  - skills/movie-experts/composer/SKILL.md (redirect-only stub, status: merged_into)
  - skills/movie-experts/foley/SKILL.md (redirect-only stub, status: merged_into)
  - skills/movie-experts/mixer/SKILL.md (redirect-only stub, status: merged_into)
  - skills/movie-experts/spatial_audio/SKILL.md (redirect-only stub, status: folded_into — distinct from merged_into)
affects:
  - 9+ consumer SKILL.md related_skills arrays (edge sync deferred to plan 15-02)
tech-stack:
  added: []
  patterns:
    - "N-to-one merge pattern extended from Phase 14 (2-item) to 6-item sub_steps array per v2.0 PRFP DAG"
    - "Fold disposition pattern: spatial_audio uses status: folded_into (distinct from merged_into) to record that it was folded into a related sub-step rather than merged as a peer — semantically meaningful for Phase 18 audit traceability"
    - "Explicit sub-step promotion pattern: lip_sync was implicit in v1 (only a voicer→lip_sync collaboration edge); v2.0 PRFP DAG promotes it to an explicit sub_step entry per Phase 8 §2.9 NODE-09 critic pairing"
    - "Sub-folder refs strategy: references/{voicer,lip_sync,composer,foley,mixer,spatial_audio}/ for predecessor-specific knowledge"
    - "Intra-audio handoff rewriting: all 6 predecessors' Collaboration bullets pointing to another audio expert rewritten as internal-handoff notes pointing to sibling Sub-step sections within the same SKILL.md"
key-files:
  created:
    - skills/movie-experts/audio_pipeline/SKILL.md
    - skills/movie-experts/audio_pipeline/GAP-REPORT.md
    - skills/movie-experts/audio_pipeline/references/voicer/LICENSE.md
    - skills/movie-experts/audio_pipeline/references/voicer/cn-tts-model-matrix.md
    - skills/movie-experts/audio_pipeline/references/voicer/tts-emotion-prosody-control.md
    - skills/movie-experts/audio_pipeline/references/voicer/character-voice-consistency.md
    - skills/movie-experts/audio_pipeline/references/lip_sync/LICENSE.md
    - skills/movie-experts/audio_pipeline/references/lip_sync/audio-video-input-spec.md
    - skills/movie-experts/audio_pipeline/references/lip_sync/identity-preservation.md
    - skills/movie-experts/audio_pipeline/references/lip_sync/latentsync-deployment.md
    - skills/movie-experts/audio_pipeline/references/lip_sync/sync-quality-metrics.md
    - skills/movie-experts/audio_pipeline/references/composer/LICENSE.md
    - skills/movie-experts/audio_pipeline/references/composer/bgm-and-song-creation.md
    - skills/movie-experts/audio_pipeline/references/composer/chion-audio-vision.md
    - skills/movie-experts/audio_pipeline/references/composer/musicgen-workflow.md
    - skills/movie-experts/audio_pipeline/references/foley/LICENSE.md
    - skills/movie-experts/audio_pipeline/references/foley/sound-effects-prompt-engineering.md
    - skills/movie-experts/audio_pipeline/references/foley/sound-effect-taxonomy.md
    - skills/movie-experts/audio_pipeline/references/foley/stable-audio-open.md
    - skills/movie-experts/audio_pipeline/references/mixer/LICENSE.md
    - skills/movie-experts/audio_pipeline/references/mixer/lufs-standards.md
    - skills/movie-experts/audio_pipeline/references/mixer/mixing-secrets-small-studio.md
    - skills/movie-experts/audio_pipeline/references/spatial_audio/LICENSE.md
    - skills/movie-experts/audio_pipeline/references/spatial_audio/dolby-atmos-workflow.md
    - skills/movie-experts/audio_pipeline/references/spatial_audio/immersive-sound-design.md
  modified:
    - skills/movie-experts/voicer/SKILL.md
    - skills/movie-experts/lip_sync/SKILL.md
    - skills/movie-experts/composer/SKILL.md
    - skills/movie-experts/foley/SKILL.md
    - skills/movie-experts/mixer/SKILL.md
    - skills/movie-experts/spatial_audio/SKILL.md
decisions:
  - "Applied FOUND-08: declare metadata.hermes.aliases: [voicer, lip_sync, composer, foley, mixer, spatial_audio] on new audio_pipeline/SKILL.md for backward-compat dispatch"
  - "Introduced NEW top-level `sub_steps: [voicer, lip_sync, composer, foley, mixer, spatial_audio]` field (extends Phase 14's 2-item sub_steps to 6-item array per v2.0 PRFP DAG convention, declared at same level as `metadata`, NOT nested inside it)"
  - "spatial_audio disposition D-1: fold (not deprecate). Rationale: spatial audio rendering is fundamentally a mixer/mastering concern (Atmos bed+objects, 6D encoding, HRTF binaural operate on the same stems mixer operates on). Fold preserves the unique HRTF/Atmos technical content. Rejected alternative = deprecation (loses irreplaceable tables). Documented in `## Spatial Audio Disposition` H2 section per ROADMAP §15 criterion #2"
  - "spatial_audio redirect stub uses status: folded_into + folded_into: audio_pipeline (distinct from the 5 merged_into stubs) — records the fold disposition explicitly for Phase 18 audit traceability"
  - "lip_sync promoted to explicit sub-step per Phase 8 §2.9 NODE-09 critic pairing (was implicit in v1, expressed only as voicer→lip_sync collaboration edge). Sub-step: Lip Sync section opens with 1-sentence note citing NODE-09 as rationale per ROADMAP §15 criterion #5"
  - "Preserved old {voicer,lip_sync,composer,foley,mixer,spatial_audio}/ directories' references/ + GAP-REPORT.md (where present) + lip_sync/_eval/ untouched (archival); only SKILL.md became redirect stubs — same pattern as Phase 13's + Phase 14's archival preservation"
  - "Refs organized into sub-folders (references/{voicer,lip_sync,composer,foley,mixer,spatial_audio}/) per CONTEXT.md Claude's-discretion recommendation — cleaner than filename-prefix strategy (matches Phase 14 visual_executor pattern)"
  - "All 6 predecessors' intra-audio Collaboration bullets rewritten as internal-handoff notes pointing to sibling Sub-step sections (preserves operational contract while making intra-expert nature explicit post-merge)"
  - "RAG query tag prefix migrated from expert:{voicer|lip_sync|composer|foley|mixer|spatial_audio},domain:X to expert:audio_pipeline,sub:{voicer|lip_sync|composer|foley|mixer|spatial_audio},domain:X — preserves domain axis while introducing sub-step scoping (matches Phase 14 migration pattern)"
  - "Version bumps on all 6 redirect stubs per plan: voicer 1.1.0→1.2.0, lip_sync 1.0.0→1.1.0, composer 1.1.0→1.2.0, foley 1.0.0→1.1.0, mixer 1.1.0→1.2.0, spatial_audio 1.1.0→1.2.0 (records the merge event in version history; distinct from Phase 14 which kept drawer/animator versions unchanged in their stubs)"
  - "lip_sync GAP-REPORT absence handled with explicit 1-line placeholder note inside the consolidated GAP-REPORT.md (lip_sync predecessor has only _eval/prompts/ regression suite, no GAP-REPORT.md) per T-15-08 threat mitigation"
metrics:
  duration: ~5 min
  completed: 2026-06-17
  tasks_completed: 2
  tasks_total: 2
  files_created: 25
  files_modified: 6
---

# Phase 15 Plan 01: voicer + lip_sync + composer + foley + mixer + spatial_audio → audio_pipeline Merge Summary

Merged 5 canonical audio movie-experts (voicer + lip_sync + composer + foley + mixer) plus the spatial_audio expert (folded per disposition D-1) into a unified `audio_pipeline` expert per MERGE-02 (Phase 7 §4.9 + PITFALLS §2.6: "5-task compression; consistency context unified"). The merged expert declares the new top-level `sub_steps: [voicer, lip_sync, composer, foley, mixer, spatial_audio]` field per v2.0 PRFP DAG convention (extending Phase 14's 2-item sub_steps to a 6-item array) and declares FOUND-08 backward-compat aliases. ROADMAP §15 success criteria #2 (spatial_audio disposition) and #5 (lip_sync explicit sub-step) are explicitly satisfied via dedicated H2 sections.

## What Was Done

### Task 1 — Created `audio_pipeline/` merged expert (commit `b4d9646c0`)

- New `skills/movie-experts/audio_pipeline/` directory with 6 sub-folder references/ tree
- **SKILL.md** frontmatter:
  - `name: audio_pipeline`, `expert_id: audio_pipeline`, `version: 1.0.0` (new baseline — not inherited from predecessors)
  - **NEW top-level field:** `sub_steps: [voicer, lip_sync, composer, foley, mixer, spatial_audio]` (extends Phase 14's 2-item field to 6-item array, declared at same level as `metadata`, per v2.0 PRFP DAG)
  - `metadata.hermes.aliases: [voicer, lip_sync, composer, foley, mixer, spatial_audio]` (FOUND-08 backward-compat)
  - `metadata.hermes.related_skills` = exact 8-item external union: `[screenplay, performer, editor, production, visual_executor, continuity_auditor, style_genome, scene_builder]` (union of all 6 predecessors' edges, deduped, audio-pipeline self-refs + internal audio edges dropped)
  - `metadata.hermes.tags` = union of all 6 predecessors' tags (deduped)
  - `metadata.hermes.metrics` = union of all 6 predecessors' metrics (deduped, preserving unique identifiers like `spatial_coherence` which appears in both composer and spatial_audio)
  - `prerequisites.tools` = [hermes_llm] (all 6 predecessors had only hermes_llm)
- **Body structure** (per plan `<behavior>`):
  1. H1 `# Audio Pipeline Expert (音频管线专家)` + intro paragraph stating unified role
  2. `## When to use this skill` (merged — all 6 audio use cases)
  3. `## Sub-steps` (NEW — table naming all 6 sub-steps in pipeline order voicer→lip_sync→composer→foley→mixer→spatial_audio with role/trigger/output + handoff contract paragraph)
  4. **`## Spatial Audio Disposition`** (NEW — MANDATORY per ROADMAP §15 criterion #2. Documents the D-1 fold decision: choice, rationale [spatial audio is fundamentally a mixer/mastering concern], rejected alternative [deprecation would lose HRTF/Atmos tables], distinct `folded_into` stub status)
  5. `## References` table listing all 17 refs (3 voicer + 4 lip_sync + 3 composer + 3 foley + 2 mixer + 2 spatial_audio) with paths to `./references/{sub-step}/*`
  6. `## Knowledge Retrieval` (merged — 15 query topics from all 6 predecessors; tag prefixes migrated to `expert:audio_pipeline,sub:{voicer|lip_sync|composer|foley|mixer|spatial_audio},*`)
  7. `## Sub-step: Voicer (TTS)` — full voicer body from `## Role & Philosophy` through `## What NOT to do`; internal ref links updated to `./references/voicer/*.md`; old References + Knowledge Retrieval sections removed (live at top of merged file)
  8. `## Sub-step: Lip Sync (Audio-Driven Video Sync)` — full lip_sync body (same scope). Opens with 1-sentence NODE-09 explicit-sub-step note (was implicit in v1; now explicit per Phase 8 §2.9 NODE-09 critic pairing — ROADMAP §15 criterion #5)
  9. `## Sub-step: Composer (Music + Score)` — full composer body (same scope)
  10. `## Sub-step: Foley (SFX)` — full foley body (same scope)
  11. `## Sub-step: Mixer (Mixing + Mastering)` — full mixer body (same scope)
  12. `## Sub-step: Spatial Audio (3D Encoding)` — full spatial_audio body (same scope), opened with 1-sentence note "Folded into audio_pipeline per disposition D-1 (see §Spatial Audio Disposition above)"
  13. `## Collaboration` (merged) — all 6 predecessors' Collaboration bullet lists; intra-audio bullets rewritten as internal-handoff notes pointing to sibling Sub-step sections; all NON-audio Collaboration bullets preserved as inter-expert edges
  14. `## Changelog` section at bottom documenting the merge: date 2026-06-17, 6 predecessors (5 merged + 1 folded), rationale citing Phase 7 §4.9 + PITFALLS §2.6, spatial_audio fold rationale (disposition D-1), lip_sync-explicit rationale (Phase 8 §2.9 NODE-09), aliases declared per FOUND-08
- **23 ref files** migrated verbatim (no content edits) to sub-folders:
  - `references/voicer/`: LICENSE.md, cn-tts-model-matrix.md, tts-emotion-prosody-control.md, character-voice-consistency.md
  - `references/lip_sync/`: LICENSE.md, audio-video-input-spec.md, identity-preservation.md, latentsync-deployment.md, sync-quality-metrics.md
  - `references/composer/`: LICENSE.md, bgm-and-song-creation.md, chion-audio-vision.md, musicgen-workflow.md
  - `references/foley/`: LICENSE.md, sound-effects-prompt-engineering.md, sound-effect-taxonomy.md, stable-audio-open.md
  - `references/mixer/`: LICENSE.md, lufs-standards.md, mixing-secrets-small-studio.md
  - `references/spatial_audio/`: LICENSE.md, dolby-atmos-workflow.md, immersive-sound-design.md
- **GAP-REPORT.md** consolidates all 6 predecessors: 5 verbatim migrated sections (voicer, composer, foley, mixer, spatial_audio) + 1 placeholder note for lip_sync (lip_sync predecessor has no GAP-REPORT.md — only `_eval/prompts/` regression suite — per T-15-08 threat mitigation)

### Task 2 — Replaced 6 audio SKILL.md files with redirect stubs (commit `36941fe06`)

- `skills/movie-experts/{voicer,lip_sync,composer,foley,mixer}/SKILL.md` (5 stubs) replaced with frontmatter-only redirect stubs (≤ 20 lines each):
  - `name:` + `expert_id:` of OLD ID retained (backward-compat dispatch)
  - `metadata.hermes.status: merged_into`, `merged_into: audio_pipeline`, `aliases: [audio_pipeline]` (forward alias)
  - Description prefixed "DEPRECATED — merged into audio_pipeline (Phase 15 MERGE-02)"
  - 1 paragraph after frontmatter with working markdown link `../audio_pipeline/SKILL.md`
  - Version bumps per plan: voicer 1.2.0, lip_sync 1.1.0, composer 1.2.0, foley 1.1.0, mixer 1.2.0
- `skills/movie-experts/spatial_audio/SKILL.md` replaced with analogous stub but uses **`status: folded_into` + `folded_into: audio_pipeline`** (distinct from merged_into — records the D-1 fold disposition per ROADMAP §15 criterion #2; semantically meaningful for Phase 18 audit traceability). Version 1.2.0.
- Old `references/` subdirs + GAP-REPORT.md files (voicer, composer, foley, mixer, spatial_audio) + `lip_sync/_eval/` preserved untouched (archival — same pattern as Phase 13's + Phase 14's)

## Deviations from Plan

None — plan executed exactly as written. All success criteria verified.

Note (not a deviation — plan-internal arithmetic slip, source-of-truth was the file list): the plan narrative mentions "21 ref files (3+4+3+3+2+2 + 6 LICENSEs)" but the actual file list in `<files>` and `<verify>` enumerates 23 files (4 voicer + 5 lip_sync + 4 composer + 4 foley + 3 mixer + 3 spatial_audio = 23). All 23 files were migrated as enumerated in the file list. The "21" figure was a miscount in the prose; the file list was the source of truth and was followed exactly.

## Verification Results

All plan success criteria verified (Task 1 + Task 2 automated verification blocks both ran green — `TASK-1 OK` + `TASK-2 OK`):

- [x] `skills/movie-experts/audio_pipeline/SKILL.md` exists with `sub_steps: [voicer, lip_sync, composer, foley, mixer, spatial_audio]` declared at top level (ROADMAP §15 criterion #1)
- [x] `metadata.hermes.related_skills` is the exact 8-item external union (no audio self-refs, no dupes) (ROADMAP §15 criterion #3)
- [x] `metadata.hermes.aliases: [voicer, lip_sync, composer, foley, mixer, spatial_audio]` declared
- [x] `metadata.hermes.expert_id: audio_pipeline` declared
- [x] `version: 1.0.0` (new expert baseline)
- [x] `## Spatial Audio Disposition` H2 section present documenting D-1 fold (ROADMAP §15 criterion #2)
- [x] Sub-step: Lip Sync section opens with NODE-09 explicit-sub-step note (ROADMAP §15 criterion #5)
- [x] Body has 6 clearly-marked `## Sub-step:` H2 sections in pipeline order voicer→lip_sync→composer→foley→mixer→spatial_audio
- [x] All 23 ref files migrated under `references/{voicer,lip_sync,composer,foley,mixer,spatial_audio}/` sub-folders (verbatim)
- [x] `GAP-REPORT.md` consolidates 5 predecessors with GAP-REPORTs + 1 placeholder for lip_sync
- [x] All internal ref markdown links updated to sub-folder paths
- [x] All RAG query tags use `expert:audio_pipeline,sub:{voicer|lip_sync|composer|foley|mixer|spatial_audio}` prefix
- [x] Intra-audio Collaboration bullets rewritten as internal-handoff notes
- [x] Changelog section appended
- [x] 5 old SKILL.md files (voicer, lip_sync, composer, foley, mixer) are redirect stubs (`status: merged_into` + `merged_into: audio_pipeline`)
- [x] spatial_audio/SKILL.md is a redirect stub with `status: folded_into` + `folded_into: audio_pipeline` (distinct per D-1)
- [x] Old `references/`, `GAP-REPORT.md` (where present), `lip_sync/_eval/` preserved untouched

## Self-Check: PASSED

### Files created (verified exist)
- FOUND: skills/movie-experts/audio_pipeline/SKILL.md
- FOUND: skills/movie-experts/audio_pipeline/GAP-REPORT.md
- FOUND: skills/movie-experts/audio_pipeline/references/voicer/LICENSE.md
- FOUND: skills/movie-experts/audio_pipeline/references/voicer/cn-tts-model-matrix.md
- FOUND: skills/movie-experts/audio_pipeline/references/voicer/tts-emotion-prosody-control.md
- FOUND: skills/movie-experts/audio_pipeline/references/voicer/character-voice-consistency.md
- FOUND: skills/movie-experts/audio_pipeline/references/lip_sync/LICENSE.md
- FOUND: skills/movie-experts/audio_pipeline/references/lip_sync/audio-video-input-spec.md
- FOUND: skills/movie-experts/audio_pipeline/references/lip_sync/identity-preservation.md
- FOUND: skills/movie-experts/audio_pipeline/references/lip_sync/latentsync-deployment.md
- FOUND: skills/movie-experts/audio_pipeline/references/lip_sync/sync-quality-metrics.md
- FOUND: skills/movie-experts/audio_pipeline/references/composer/LICENSE.md
- FOUND: skills/movie-experts/audio_pipeline/references/composer/bgm-and-song-creation.md
- FOUND: skills/movie-experts/audio_pipeline/references/composer/chion-audio-vision.md
- FOUND: skills/movie-experts/audio_pipeline/references/composer/musicgen-workflow.md
- FOUND: skills/movie-experts/audio_pipeline/references/foley/LICENSE.md
- FOUND: skills/movie-experts/audio_pipeline/references/foley/sound-effects-prompt-engineering.md
- FOUND: skills/movie-experts/audio_pipeline/references/foley/sound-effect-taxonomy.md
- FOUND: skills/movie-experts/audio_pipeline/references/foley/stable-audio-open.md
- FOUND: skills/movie-experts/audio_pipeline/references/mixer/LICENSE.md
- FOUND: skills/movie-experts/audio_pipeline/references/mixer/lufs-standards.md
- FOUND: skills/movie-experts/audio_pipeline/references/mixer/mixing-secrets-small-studio.md
- FOUND: skills/movie-experts/audio_pipeline/references/spatial_audio/LICENSE.md
- FOUND: skills/movie-experts/audio_pipeline/references/spatial_audio/dolby-atmos-workflow.md
- FOUND: skills/movie-experts/audio_pipeline/references/spatial_audio/immersive-sound-design.md

### Files modified (verified)
- FOUND: skills/movie-experts/voicer/SKILL.md (now redirect stub, status: merged_into)
- FOUND: skills/movie-experts/lip_sync/SKILL.md (now redirect stub, status: merged_into)
- FOUND: skills/movie-experts/composer/SKILL.md (now redirect stub, status: merged_into)
- FOUND: skills/movie-experts/foley/SKILL.md (now redirect stub, status: merged_into)
- FOUND: skills/movie-experts/mixer/SKILL.md (now redirect stub, status: merged_into)
- FOUND: skills/movie-experts/spatial_audio/SKILL.md (now redirect stub, status: folded_into — distinct)

### Commits (verified exist)
- FOUND: b4d9646c0 (feat(15-01): create audio_pipeline merged expert)
- FOUND: 36941fe06 (refactor(15-01): replace 6 audio SKILL.md files with redirect stubs)
