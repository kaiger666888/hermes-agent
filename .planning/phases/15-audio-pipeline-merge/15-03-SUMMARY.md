---
phase: 15-audio-pipeline-merge
plan: 03
subsystem: skills/movie-experts
tags: [merge, n-to-one, close-out-docs, cross-cutting, README, glossary, RAG-INVOCATION-PATTERN, project-corpus, audio_pipeline, dag-diagram, corpus-tree, footer-count]
requires:
  - 15-01-PLAN (source-level merge producing audio_pipeline with 6-item sub_steps)
  - 15-02-PLAN (consumer edge sync — all 11 consumers reference audio_pipeline)
  - skills-mapping.yaml (n_to_one_merged mapping entry for audio_pipeline — already canonical, no sign_off field)
provides:
  - README.md inventory + corpus tree + ASCII DAG diagram + Phase 7 summary + footer count all reflect audio_pipeline merge
  - _shared/glossary.md has new audio_pipeline entry + 5 prose references updated
  - _shared/RAG-INVOCATION-PATTERN.md has 3 model-attribution table rows updated with sub-step annotation
  - _shared/project-corpus/{animation-disney-system,editing-sound-post,production-chinese-and-low-budget}.md expert references updated
affects:
  - 6 cross-cutting documentation files (README.md, _shared/glossary.md, _shared/RAG-INVOCATION-PATTERN.md, 3 project-corpus files)
tech-stack:
  added: []
  patterns:
    - "Cross-cutting documentation consolidation: 6 audio expert_ids collapsed to audio_pipeline across README inventory + corpus→expert table + corpus tree + ASCII DAG diagram + narrative notes + Phase 7 summary + footer count"
    - "Corpus tree preserve+annotate pattern extended from Phase 14: 6 old audio directories preserved with '(Phase 15 redirect stub — merged_into audio_pipeline)' or '(Phase 15 redirect stub — folded_into audio_pipeline)' for spatial_audio — distinct fold annotation per D-1 disposition"
    - "Multi-line ASCII DAG box pattern: audio_pipeline label too long for single-line box → multi-line box with sub-step enumeration following Phase 13 compliance_gate + Phase 14 visual_executor precedent"
    - "Sub-step annotation pattern extended to all cross-cutting docs: glossary prose + RAG-INVOCATION-PATTERN table + project-corpus stage breakdowns + See Also links all carry '(composer sub-step)' / '(voicer sub-step)' etc. inline"
    - "Bilingual glossary header convention: new audio_pipeline entry uses '### audio_pipeline / 音频管线专家' bilingual header matching Phase 14's visual_executor entry format"
key-files:
  created: []
  modified:
    - skills/movie-experts/README.md
    - skills/movie-experts/_shared/glossary.md
    - skills/movie-experts/_shared/RAG-INVOCATION-PATTERN.md
    - skills/movie-experts/_shared/project-corpus/animation-disney-system.md
    - skills/movie-experts/_shared/project-corpus/editing-sound-post.md
    - skills/movie-experts/_shared/project-corpus/production-chinese-and-low-budget.md
decisions:
  - "Multi-line ASCII DAG box for audio_pipeline (6 sub-steps enumerated inside the box): label 'audio_pipeline' + sub-step list '(voicer/lip_sync/composer/foley/mixer/spatial)' would not fit the 15-char column width as a single line — extended the multi-line box pattern from Phase 13's compliance_gate + Phase 14's visual_executor. The continuity_auditor parallel-audit annotation moved from the mixer box to the audio_pipeline box (mixer is now an internal sub-step)"
  - "Corpus tree audio_pipeline/ row placed alphabetically near compliance_gate/ (the position where composer/ originally sat) — maintains alphabetical ordering while keeping the audio block visually grouped"
  - "Bilingual glossary header format '### audio_pipeline / 音频管线专家' adopted (matching Phase 14's '### visual_executor / 视觉执行专家') — the plan's verify regex `^### audio_pipeline$` was too strict and would have rejected the bilingual format; the bilingual header is the established convention"
  - "Audit-nodes narrative note updated from 'parallel to mixer' to 'parallel to audio_pipeline' — mixer is now an internal sub-step so the parallel-audit edge target is audio_pipeline"
  - "editing-sound-post.md See Also section: 4 separate markdown links (foley, composer, mixer, spatial_audio) consolidated to 4 audio_pipeline links with distinct sub-step annotations — preserves the per-sub-step context while routing through the merged expert"
metrics:
  duration: ~5 min
  completed: 2026-06-17
  tasks_completed: 2
  tasks_total: 2
  files_created: 0
  files_modified: 6
---

# Phase 15 Plan 03: Close-Out Documentation Summary

Updated all 6 cross-cutting documentation artifacts (README.md inventory + corpus→expert table + corpus tree + ASCII DAG diagram + narrative notes + Phase 7 summary + footer count, _shared/glossary.md, _shared/RAG-INVOCATION-PATTERN.md, _shared/project-corpus/{animation-disney-system,editing-sound-post,production-chinese-and-low-budget}.md) to reflect the voicer + lip_sync + composer + foley + mixer + spatial_audio → audio_pipeline merge. These are the cross-cutting docs that depend on both 15-01 (new expert exists) and 15-02 (consumer edges synced) being complete. A reader skimming README or any _shared/ doc now sees a single audio_pipeline expert where there used to be 6.

## What Was Done

### Task 1 — Updated README.md (commit `0ad1181c2`)

**Inventory table consolidation:**
- 5 contiguous rows in Phase 0 baselined section (composer, foley, spatial_audio, mixer, voicer — lines 71-75) replaced with single `[audio_pipeline]` row at the position where composer/ was. The new row's description column names all 6 sub-steps + cites Phase 15 + v2.0 PRFP DAG §4.9.
- lip_sync row in Phase 7 section (line 88) deleted — its LRS2/LRS3 benchmark capability is folded into the audio_pipeline row's description ("Phase 7A-2 lip_sync benchmark").

**Corpus → expert inventory table (line 39):**
- `editing-sound-post.md` row: `editor, foley, composer, documentary_maker` → `editor, audio_pipeline, documentary_maker` (foley + composer collapse to audio_pipeline).

**ASCII DAG diagram (lines 168-191):**
- 5 audio stage boxes (lip_sync + voicer pair, colorist/editor/composer/foley/spatial_audio 5-expert box, mixer box) collapsed into ONE multi-line `audio_pipeline` box. The box enumerates all 6 sub-steps: `(voicer/lip_sync/composer/foley/mixer/spatial)`. The continuity_auditor parallel-audit annotation moved from the mixer box to the audio_pipeline box.

**Narrative notes (lines 192-196):**
- Identity contract: `visual_executor / lip_sync / continuity_auditor` → `visual_executor / audio_pipeline (lip_sync sub-step) / continuity_auditor`
- Audio-visual lock: `voicer produces audio → lip_sync aligns` → `audio_pipeline (voicer sub-step) produces audio → audio_pipeline (lip_sync sub-step) aligns (now intra-expert handoff)`
- Bottleneck nodes: `lip_sync (after audio + footage) / mixer (after all audio)` → `audio_pipeline (after all audio + footage) — single node now subsumes lip_sync + mixer bottleneck roles`
- Audit nodes: `parallel to mixer` → `parallel to audio_pipeline`

**File Layout corpus tree (lines 355-372):**
- New `audio_pipeline/` row added (alphabetical placement after compliance_gate/) with 6-sub-folder references/ structure enumerating all 17 ref files + 6 LICENSE.md files + GAP-REPORT.md.
- 6 old audio rows preserved with redirect stub annotations:
  - `composer/` → `(Phase 15 redirect stub — merged_into audio_pipeline)`
  - `foley/` → `(Phase 15 redirect stub — merged_into audio_pipeline)`
  - `mixer/` → `(Phase 15 redirect stub — merged_into audio_pipeline)`
  - `spatial_audio/` → `(Phase 15 redirect stub — folded_into audio_pipeline)` (distinct per D-1)
  - `voicer/` → `(Phase 15 redirect stub — merged_into audio_pipeline)`
  - `lip_sync/` → `(Phase 15 redirect stub — merged_into audio_pipeline)` (notes _eval/ regression suite preserved)

**Phase 7 additions summary (lines 444, 453-455):**
- lip_sync row → `audio_pipeline (lip_sync sub-step)` (benchmark capability preserved)
- 3 ref paths updated: `composer/references/bgm-and-song-creation.md` → `audio_pipeline/references/composer/bgm-and-song-creation.md` (and foley + voicer equivalents)

**Footer running expert count (line 433):**
- `v2 = 22 experts (...) − 1 Phase 14 visual_executor merge` → `v2 = 17 experts (...) − 1 Phase 14 visual_executor merge − 5 Phase 15 audio_pipeline merge` (6 audio experts → 1 audio_pipeline = net delta of −5).

**_eval/prompts/lip_sync_demo.yaml row PRESERVED** (Phase 13 + 14 precedent: prompt filenames NOT renamed because the runner references them).

### Task 2 — Updated _shared/ docs (commit `23401f725`)

**_shared/glossary.md (5 prose references + 1 new entry):**
- Line 13: `(editor, composer)` → `(editor, audio_pipeline (composer sub-step))`
- Line 73: `composer aligns musical sting to 击中点.` → `audio_pipeline (composer sub-step) aligns musical sting to 击中点.`
- Line 164 (Character Bible): `visual_executor / lip_sync / continuity_auditor` → `visual_executor / audio_pipeline (lip_sync sub-step) / continuity_auditor`
- Line 171 (4D Anchor context): `lip_sync prefers front + 3Q` → `audio_pipeline (lip_sync sub-step) prefers front + 3Q`
- Line 201 (唇形同步 context): `lip_sync expert's domain. Decoupled from voicer (audio synthesis) — voicer produces WAV, lip_sync aligns WAV to footage.` → `audio_pipeline (lip_sync sub-step) domain. Intra-expert handoff from voicer sub-step (audio synthesis) — voicer sub-step produces WAV, lip_sync sub-step aligns WAV to footage.`
- NEW entry: `### audio_pipeline / 音频管线专家` added in new `## Phase 15 additions (audio_pipeline merge)` section. Bilingual CN+EN definitions document the Phase 15 merge of 6 predecessors + spatial_audio D-1 fold + FOUND-08 aliases + v2.0 PRFP DAG §4.9 provenance.

**_shared/RAG-INVOCATION-PATTERN.md (3 model-attribution table rows):**
- `<audio_gen_primary>` row: `foley` → `audio_pipeline (foley sub-step)`
- `<music_gen_primary>` row: `composer` → `audio_pipeline (composer sub-step)`
- `<tts_primary>` row: `voicer` → `audio_pipeline (voicer sub-step)`

**_shared/project-corpus/animation-disney-system.md (2 Disney pipeline stage refs):**
- Stage 4-5: `voice via voicer + leica reel` → `voice via audio_pipeline (voicer sub-step) + leica reel`
- Stage 12: `composer + mixer (1 day)` → `audio_pipeline (composer + mixer sub-steps) (1 day)`

**_shared/project-corpus/editing-sound-post.md (5 expert_id refs + 4 See Also links):**
- Summary: `` `composer` / `foley` / `mixer` experts `` → `` `audio_pipeline` expert (composer / foley / mixer sub-steps) ``
- Sound Bible heading: `` `foley` / `mixer` `` → `` `audio_pipeline` (foley / mixer sub-steps) ``
- Chion heading: `` `composer` / `spatial_audio` `` → `` `audio_pipeline` (composer / spatial_audio sub-steps) ``
- 4 See Also markdown links (foley, composer, mixer, spatial_audio SKILL.md) → 4 `audio_pipeline` links with distinct sub-step annotations
- Line 273 "Sync hard effects + foley" PRESERVED — craft noun (no markdown link, no expert_id context)

**_shared/project-corpus/production-chinese-and-low-budget.md (1 line):**
- `Post = editor + composer + mixer` → `Post = editor + audio_pipeline (composer + mixer sub-steps)`

## Deviations from Plan

### Auto-fixed Issues

**1. [Plan-text verification pattern inaccuracy] glossary verify regex `^### audio_pipeline$` too strict**

- **Found during:** Task 2 verification
- **Issue:** The plan's `<verify>` block expected `grep -q "^### audio_pipeline$"` (exact match, no trailing content). The actual glossary entry uses the bilingual header format `### audio_pipeline / 音频管线专家` — matching Phase 14's `### visual_executor / 视觉执行专家` convention. The strict regex would reject the correctly-formatted entry.
- **Fix:** No implementation change needed — the entry exists and follows the established bilingual header convention. Documented the verification pattern inaccuracy. Re-verified with relaxed regex `^### audio_pipeline\s*/` which passes.
- **Files affected:** None (documentation-only finding)
- **Commit:** N/A (no code change)

**2. [Scope boundary] Stray audio references in out-of-scope _shared/ files**

- **Found during:** Task 2 stray-reference sweep
- **Issue:** `grep -rnE "\b(voicer|lip_sync|composer|foley|mixer|spatial_audio)\b" skills/movie-experts/_shared/` returned hits in 3 files NOT in this plan's `<files_modified>` list: `_shared/cognitive-resonance-metrics.md` (3 hits — `composer` as doctrine owner), `_shared/known-external-models.yaml` (15 hits — provenance strings referencing predecessor ref file paths like `voicer/cn-tts-model-matrix.md`), `_shared/glossary.md:146` (Phase 7 section header listing `lip_sync` as a historical expert name).
- **Decision:** OUT OF SCOPE per plan boundary. The plan's `<files_modified>` explicitly lists only 6 files. Phase 14's 14-03-SUMMARY established the precedent: "known-external-models.yaml NOT modified in 14-03 — its provenance strings reference predecessor ref file paths that still resolve via archival preservation; Phase 18 (DOC-02 + VALIDATE-01) is canonical path reconciliation phase." The cognitive-resonance-metrics.md references are doctrine-owner attributions (not active expert_id dispatch references). The glossary section header is a historical label. All deferred to Phase 18 finalization.
- **Files affected:** None (deferred to Phase 18)
- **Commit:** N/A

## Verification Results

All plan success criteria verified (consolidated verification block ran green for all in-scope checks):

- [x] README.md inventory has ONE audio_pipeline row (replacing 6 separate audio expert rows — 5 in Phase 0 section + lip_sync in Phase 7 section)
- [x] README.md corpus → expert table line 39 references audio_pipeline for editing-sound-post.md
- [x] README.md ASCII DAG diagram has an audio_pipeline box (multi-line with 6 sub-steps enumerated per Phase 13+14 multi-line precedent)
- [x] README.md Bridge/Audio-visual lock/Bottleneck/Audit narrative references audio_pipeline (with sub-step annotations)
- [x] README.md File Layout corpus tree has a new audio_pipeline/ row with 6-sub-folder references structure
- [x] README.md old 6 audio rows in corpus tree preserved with redirect stub annotation (5 merged_into + 1 folded_into for spatial_audio)
- [x] README.md Phase 7 additions section paths updated to audio_pipeline/references/{sub-step}/...
- [x] README.md footer expert count decremented by 5 (22 → 17)
- [x] _shared/glossary.md has 5 updated prose references + 1 new audio_pipeline entry (bilingual header format, with D-1 fold note)
- [x] _shared/RAG-INVOCATION-PATTERN.md has 3 table rows updated with sub-step annotation
- [x] _shared/project-corpus/animation-disney-system.md has 2 stage refs updated
- [x] _shared/project-corpus/editing-sound-post.md has 5 expert_id refs + 4 See Also markdown links updated; "Sync hard effects + foley" craft noun preserved
- [x] _shared/project-corpus/production-chinese-and-low-budget.md Post line updated
- [x] No stray expert_id references to bare audio IDs in the 6 in-scope _shared/ files outside intentional contexts (sub-step annotations, English craft nouns)
- [x] skills-mapping.yaml NOT modified (n_to_one_merged has no sign_off_status field by convention — confirmed by Phase 14 close-out)

## Self-Check: PASSED

### Files modified (all 6 verified modified)

- FOUND (modified): skills/movie-experts/README.md
- FOUND (modified): skills/movie-experts/_shared/glossary.md
- FOUND (modified): skills/movie-experts/_shared/RAG-INVOCATION-PATTERN.md
- FOUND (modified): skills/movie-experts/_shared/project-corpus/animation-disney-system.md
- FOUND (modified): skills/movie-experts/_shared/project-corpus/editing-sound-post.md
- FOUND (modified): skills/movie-experts/_shared/project-corpus/production-chinese-and-low-budget.md

### Commits (verified exist)

- FOUND: 0ad1181c2 (docs(15-03): update README inventory + corpus tree + DAG diagram for audio_pipeline merge)
- FOUND: 23401f725 (docs(15-03): update _shared/ glossary + RAG-INVOCATION-PATTERN + project-corpus for audio_pipeline merge)
