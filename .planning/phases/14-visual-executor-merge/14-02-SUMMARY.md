---
phase: 14-visual-executor-merge
plan: 02
subsystem: skills/movie-experts
tags: [merge, n-to-one, consumer-edge-sync, bidirectional-edges, expert-id, visual_executor, drawer, animator, dedup, backward-compat]
requires:
  - 14-01-PLAN (source-level merge producing visual_executor)
  - skills-mapping.yaml (n_to_one_merged mapping entry for visual_executor)
provides:
  - Bidirectional related_skills edges between visual_executor and 14 consumers
  - Zero stranded drawer/animator expert_id references outside redirect stubs
affects:
  - 15 consumer SKILL.md files (character_designer, scene_builder, editor, colorist, cinematographer, composer, production, performer, storyboard_designer, continuity_auditor, compliance_gate, foley, lip_sync, animation_studio, style_genome)
tech-stack:
  added: []
  patterns:
    - "Bidirectional edge sync post-merge: visual_executor lists consumers (14-01) + consumers list visual_executor back (14-02)"
    - "Multi-line related_skills block edit pattern (compliance_gate, animation_studio): collapse sub-list items preserving inline comments"
    - "Sub-step-aware body prose: when merging two Collaboration bullets that previously targeted drawer + animator separately, combine into one visual_executor bullet with '(drawer sub-step)' / '(animator sub-step)' inline annotations to preserve operational handoff context"
key-files:
  created: []
  modified:
    - skills/movie-experts/character_designer/SKILL.md
    - skills/movie-experts/scene_builder/SKILL.md
    - skills/movie-experts/editor/SKILL.md
    - skills/movie-experts/colorist/SKILL.md
    - skills/movie-experts/cinematographer/SKILL.md
    - skills/movie-experts/composer/SKILL.md
    - skills/movie-experts/production/SKILL.md
    - skills/movie-experts/performer/SKILL.md
    - skills/movie-experts/storyboard_designer/SKILL.md
    - skills/movie-experts/continuity_auditor/SKILL.md
    - skills/movie-experts/compliance_gate/SKILL.md
    - skills/movie-experts/foley/SKILL.md
    - skills/movie-experts/lip_sync/SKILL.md
    - skills/movie-experts/animation_studio/SKILL.md
    - skills/movie-experts/style_genome/SKILL.md
decisions:
  - "Deviation (Rule 1 — Plan audit inaccuracy): plan interface table claimed animation_studio related_skills had NEITHER drawer NOR animator; actual audit found BOTH drawer + animator listed (lines 15-16). Applied the collapse rule: replaced both with one visual_executor entry. Documented as deviation since acceptance criteria (composer + animation_studio 'unchanged') was based on the incorrect audit."
  - "Sub-step annotation strategy: when merging two Collaboration bullets (drawer + animator → visual_executor), inline-annotated each sub-step's specific contract — e.g., cinematographer line 190: 'visual_executor: `animator_handoff.json` (...) + shot composition + framing intent for first_frame generation'. Preserves operational context lost in pure collapse."
  - "Artifact filename `animator_handoff.json` (cinematographer line 97, 190) PRESERVED — this is a stable artifact contract name, not an expert_id reference; renaming would change the artifact schema"
  - "Bare-noun 'drawer' usages in character_designer body (line 47 'drawer 关心怎么画', line 270 'drawer 容易漂移') PRESERVED per plan's English-noun rule — no markdown link, refers to the act/agent of drawing generically, not the expert_id"
  - "style_genome DAG pipeline string consolidated: original `... -> (drawer, voicer, colorist, editor, composer) -> (animator, foley, spatial_audio, continuity_auditor) -> ...` had drawer (stills) in stage 4 and animator (video) in stage 5; post-merge both are visual_executor sub-steps, so the pipeline was reflowed to a single stage: `(visual_executor, voicer, colorist, editor, composer, foley, spatial_audio, continuity_auditor)` — avoids awkward duplicate visual_executor entries in a DAG-string (which is not a related_skills array and would have read ambiguously)"
  - "storyboard_designer line 272 'drawer 自由发挥' + line 274 '下游 animator 需要 end_frame' CHANGED despite bare-noun status: context clearly describes the EXPERT's behavior/needs (free-form drift without anchoring / downstream expert's input requirement), paralleling line 50 which was also changed. Consistent treatment within the same file."
metrics:
  duration: ~13 min
  completed: 2026-06-17
  tasks_completed: 1
  tasks_total: 1
  files_created: 0
  files_modified: 15
---

# Phase 14 Plan 02: Consumer Edge Sync Summary

Propagated the drawer + animator → visual_executor merge across all 15 consumer SKILL.md files, closing the bidirectional edge sync required by ROADMAP §14 success criterion #4. Every consumer's `metadata.hermes.related_skills` array that previously listed `drawer` and/or `animator` now lists `visual_executor` (deduplicated — never two entries), and every body prose reference to the drawer/animator expert_id (markdown links, Collaboration bullets, JSON literals, narrative pair references, DAG pipeline strings) is updated to `visual_executor`.

## What Was Done

### Task 1 — Updated 15 consumer SKILL.md files (commit `f06e15c0d`)

**related_skills array changes (13 consumers with array edits):**

| Consumer | Before | After |
|----------|--------|-------|
| character_designer | `[style_genome, screenplay, drawer, animator, performer, ...]` | `[style_genome, screenplay, visual_executor, performer, ...]` |
| scene_builder | `[..., drawer, animator, foley, ...]` | `[..., visual_executor, foley, ...]` |
| editor | `[..., animator, composer, ...]` | `[..., visual_executor, composer, ...]` |
| colorist | `[..., drawer, continuity_auditor, animator, ...]` | `[..., visual_executor, continuity_auditor, ...]` |
| cinematographer | `[..., animator, editor, ..., drawer, ...]` | `[..., visual_executor, editor, ...]` |
| production | `[..., drawer, animator, scene_builder, ...]` | `[..., visual_executor, scene_builder, ...]` |
| performer | `[..., drawer, animator, voicer, ...]` | `[..., visual_executor, voicer, ...]` |
| storyboard_designer | `[..., drawer, animator, editor, ...]` | `[..., visual_executor, editor, ...]` |
| continuity_auditor | `[drawer, animator, colorist, ...]` | `[visual_executor, colorist, ...]` |
| compliance_gate | multi-line `- drawer` | multi-line `- visual_executor` |
| foley | `[animator, performer, ...]` | `[visual_executor, performer, ...]` |
| lip_sync | `[..., animator, mixer, ...]` | `[..., visual_executor, mixer, ...]` |
| animation_studio | multi-line `- drawer` + `- animator` (DEVIATION — plan audit was wrong) | multi-line `- visual_executor` (single entry) |
| style_genome | `[screenplay, drawer, colorist, ...]` | `[screenplay, visual_executor, colorist, ...]` |

**composer related_skills UNCHANGED** (correctly — audit confirmed `[screenplay, editor, style_genome, mixer, foley, spatial_audio]` contains neither drawer nor animator).

**Body prose changes (per consumer):**

- **character_designer**: description line (drawer → visual_executor), body intro (drawer/animator → visual_executor with sub-step annotation), Core Capabilities bullet (drawer, animator, lip_sync → visual_executor, lip_sync), Philosophy bullet (drawer / animator / lip_sync → visual_executor / lip_sync), JSON literal `"downstream_consumers": ["drawer", "animator", "lip_sync", ...]` → `["visual_executor", "lip_sync", ...]`, Hand off step (drawer / animator / lip_sync → visual_executor / lip_sync), Collaboration bullets (`-> drawer` + `-> animator` merged into single `-> visual_executor` with both sub-step contracts). Preserved: line 47 "drawer 关心怎么画" + line 270 "drawer 容易漂移" (English-noun usages, no link).
- **scene_builder**: Collaboration bullets (`-> drawer` + `-> animator` merged → `-> visual_executor`), What-NOT-to-do GPU-sharing warning (drawer/animator → visual_executor).
- **editor**: When-to-use narrative ("after `animator`" → "after `visual_executor`"), Collaboration bullet (`<- animator` → `<- visual_executor`).
- **colorist**: Per-Frame Grading step ("drawer output frames" → "visual_executor output frames"), Collaboration bullets (`<- drawer` + `-> drawer` + `-> animator` → single `<- visual_executor` + single `-> visual_executor` with merged contracts).
- **cinematographer**: heavy edits — narrative mentions (`animator` (execution) → `visual_executor` (execution)), expert-boundary table row (`| animator | EXECUTION |` → `| visual_executor | EXECUTION |`), Hard-boundary-rule paragraph, Core Capabilities handoff list, Output Encoding step (4 handoff files: scene_builder / animator / editor / continuity_auditor → ... / visual_executor / ...), Handoff-to-Downstream step, Collaboration bullets (`-> animator` + `-> drawer` merged → `-> visual_executor`), What-NOT-to-do bullet, Pipeline Position DAG string (animator execution + drawer first_frame → visual_executor execution + first_frame). Preserved: artifact filename `animator_handoff.json` (lines 97, 190 — contract name, not expert_id).
- **composer**: body-only edit — What-NOT-to-do GPU-sharing warning ("drawer/animator" → "visual_executor"). related_skills unchanged (correctly).
- **production**: When-to-use narrative ("before drawer / animator" → "before visual_executor"), Core Capabilities cross-expert list, Cross-Expert Coordination step (drawer + animator → visual_executor), Collaboration bullets (`-> drawer` + `-> animator` merged → `-> visual_executor`), Pipeline Position narrative + DAG string.
- **performer**: When-to-use narrative ("action prompts for drawer/animator" → "for visual_executor"), Output Format field description ("for drawer/animator" → "for visual_executor"), Process step (drawer/animator action description text → visual_executor), Collaboration bullets (`-> drawer` + `-> animator` merged → `-> visual_executor`).
- **storyboard_designer**: Core Capabilities bullet ("downstream drawer / animator / scene_builder" → "downstream visual_executor / scene_builder"), Philosophy bullets ("让 drawer 拿着... 让 animator 拿着..." → "让 visual_executor 拿着..." + "drawer 自由发挥" → "visual_executor 自由发挥"), JSON literal `"downstream_consumers": ["drawer", "animator", "scene_builder", ...]` → `["visual_executor", "scene_builder", ...]`, Collaboration bullets (`-> drawer` + `-> animator` merged → `-> visual_executor` with both sub-step contracts), What-NOT-to-do bullets (drawer 自由发挥 → visual_executor 自由发挥; 下游 animator 需要 end_frame → 下游 visual_executor 需要 end_frame).
- **continuity_auditor**: Knowledge Retrieval bullet ("Correction prompts for drawer/animator" → "for visual_executor"), Collaboration bullets (`<- drawer` + `<- animator` merged → `<- visual_executor`; `-> drawer/animator` → `-> visual_executor`). Phase 13 expert_id token `continuity_auditor` preserved intact.
- **compliance_gate**: multi-line related_skills block (`- drawer` → `- visual_executor`), Collaboration bullet (`<- drawer` → `<- visual_executor`). Phase 13 expert_id token `compliance_gate` preserved intact.
- **foley**: Collaboration bullet (`<- animator` → `<- visual_executor`).
- **lip_sync**: Philosophy bullet (`animator` markdown-link reference + bare-noun → `visual_executor`), Collaboration bullet (`<- animator` markdown link → `<- visual_executor`), What-NOT-to-do bullets (animator markdown-link + bare-noun → visual_executor).
- **animation_studio**: related_skills multi-line block (drawer + animator → single visual_executor with combined comment), intro narrative ("Complements drawer (stills), animator (motion), composer" → "Complements visual_executor (stills + motion), composer"), references table (drawer + animator rows → single visual_executor row with sub-step annotations), workflow step (drawer, animator → visual_executor), Integration-with-Other-Experts section (drawer + animator bullets → single visual_executor bullet with sub-step annotations), related-skills list at bottom (drawer + animator markdown-link rows → single visual_executor row). No "Senior animators draw key frames" / "Junior animators" content found in this SKILL.md (those are in project-corpus refs, out of scope for this consumer edit).
- **style_genome**: Cross-Module Alignment table row (`| drawer |` → `| visual_executor |`), Cross-Module Alignment bullet ("drawer: composition..." → "visual_executor: composition..."), Collaboration bullet (`-> drawer` → `-> visual_executor`), Pipeline Position DAG string consolidated (drawer + animator in separate stages → visual_executor in one combined stage to avoid ambiguous duplicate entry in non-array context).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Plan audit inaccuracy] animation_studio DID list drawer + animator in related_skills**
- **Found during:** Task 1 audit phase (initial grep)
- **Issue:** Plan `<interfaces>` table claimed "animation_studio: none in related_skills (body prose references only)". Plan `<behavior>` said "If it contains NEITHER (composer, animation_studio per the audit): no related_skills change required". Plan `<acceptance_criteria>` excluded animation_studio from the list of consumers expected to have visual_executor.
- **Reality:** `skills/movie-experts/animation_studio/SKILL.md` lines 13-21 had a multi-line related_skills block explicitly listing `- drawer` (line 15) and `- animator` (line 16).
- **Fix:** Applied the collapse rule — replaced both lines with a single `- visual_executor` line (preserving the comment style). The 14 consumers with visual_executor in related_skills (instead of the originally-claimed 13) is the correct outcome.
- **Files modified:** skills/movie-experts/animation_studio/SKILL.md
- **Commit:** f06e15c0d

**2. [Rule 1 — Sub-step context preservation] Body prose merge strategy**
- **Found during:** Task 1 edits to cinematographer, character_designer, storyboard_designer, production, performer, colorist, continuity_auditor
- **Issue:** Pure collapse of two Collaboration bullets (drawer + animator) into one visual_executor entry would lose operational context (e.g., drawer receives CharacterBible for image gen vs. animator consumes anchors for video-gen).
- **Fix:** Adopted sub-step annotation pattern in the merged bullets — e.g., cinematographer: `**-> visual_executor**: \`animator_handoff.json\` (model-agnostic camera move + 4-model prompt-token table) + shot composition + framing intent for first_frame generation`. Each sub-step's specific contract preserved as inline annotation. Not strictly mandated by plan but consistent with plan's intent ("preserves operational context").
- **Files modified:** Multiple consumer SKILL.md Collaboration sections
- **Commit:** f06e15c0d

## Verification Results

All 10 consolidated verification checks passed:

- [x] **Check 1**: No consumer has stray `\bdrawer\b` or `\banimator\b` token in related_skills block (single-line OR multi-line)
- [x] **Check 2**: 14 of 15 consumers have `visual_executor` in related_skills (composer correctly excluded — audit confirmed it never listed drawer/animator there)
- [x] **Check 3**: No consumer has DUPLICATE `visual_executor` entries in related_skills (collapse rule held)
- [x] **Check 4**: Zero stray `(../drawer/SKILL.md)` or `(../animator/SKILL.md)` markdown links outside drawer/ + animator/ redirect stubs
- [x] **Check 5**: Zero stray `**-> drawer**`, `**<- drawer**`, `**-> animator**`, `**<- animator**` Collaboration bullets outside redirect stubs
- [x] **Check 6**: `_eval/baseline/drawer/SKILL.md` + `_eval/baseline/animator/SKILL.md` retain their original expert_id values (frozen regression baselines untouched)
- [x] **Check 7**: Redirect stubs in `skills/movie-experts/drawer/SKILL.md` + `animator/SKILL.md` preserve their old `expert_id` fields (backward-compat)
- [x] **Check 8**: Zero stray `"drawer"` or `"animator"` JSON literals outside redirect stubs (character_designer + storyboard_designer JSON arrays updated)
- [x] **Check 9**: Phase 13 tokens preserved — `continuity_auditor/` + `compliance_gate/` directories + expert_id fields intact
- [x] **Check 10**: visual_executor's own related_skills (10-item union set in 14-01) unchanged — bidirectional edge sync is now complete

## Self-Check: PASSED

### Files modified (all 15 verified modified)

- FOUND (modified): skills/movie-experts/character_designer/SKILL.md
- FOUND (modified): skills/movie-experts/scene_builder/SKILL.md
- FOUND (modified): skills/movie-experts/editor/SKILL.md
- FOUND (modified): skills/movie-experts/colorist/SKILL.md
- FOUND (modified): skills/movie-experts/cinematographer/SKILL.md
- FOUND (modified): skills/movie-experts/composer/SKILL.md
- FOUND (modified): skills/movie-experts/production/SKILL.md
- FOUND (modified): skills/movie-experts/performer/SKILL.md
- FOUND (modified): skills/movie-experts/storyboard_designer/SKILL.md
- FOUND (modified): skills/movie-experts/continuity_auditor/SKILL.md
- FOUND (modified): skills/movie-experts/compliance_gate/SKILL.md
- FOUND (modified): skills/movie-experts/foley/SKILL.md
- FOUND (modified): skills/movie-experts/lip_sync/SKILL.md
- FOUND (modified): skills/movie-experts/animation_studio/SKILL.md
- FOUND (modified): skills/movie-experts/style_genome/SKILL.md

### Commits (verified exist)

- FOUND: f06e15c0d (refactor(14-02): sync visual_executor edges across 15 consumer SKILL.md files)
