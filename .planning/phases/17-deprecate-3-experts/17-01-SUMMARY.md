---
phase: 17-deprecate-3-experts
plan: 01
subsystem: movie-experts
tags: [deprecation, found-08, related_skills, edge-rewiring, phase-17]
requires:
  - "Phase 16 prompt_injector integrated (character_designer, screenplay, cinematographer, style_genome as inheritance targets all exist and stable)"
  - "skills-mapping.yaml not_in_new_dag entries for performer / scene_builder / storyboard_designer (rationale source-of-truth)"
provides:
  - "3 deprecated SKILL.md files (performer, scene_builder, storyboard_designer) with status: deprecated + metadata.hermes.{deprecated, deprecated_reason, inheritance_targets} + body deprecation notice"
  - "FOUND-08 backward compatibility: original expert_id + full body content preserved in each deprecated file"
  - "8 consumer SKILL.md related_skills edges rewired from deprecated IDs to inheritance targets"
  - "Body prose annotations across 8 consumers documenting the Phase 17 redirects"
affects:
  - "skills/movie-experts/performer/SKILL.md"
  - "skills/movie-experts/scene_builder/SKILL.md"
  - "skills/movie-experts/storyboard_designer/SKILL.md"
  - "skills/movie-experts/character_designer/SKILL.md"
  - "skills/movie-experts/screenplay/SKILL.md"
  - "skills/movie-experts/cinematographer/SKILL.md"
  - "skills/movie-experts/style_genome/SKILL.md"
  - "skills/movie-experts/visual_executor/SKILL.md"
  - "skills/movie-experts/audio_pipeline/SKILL.md"
  - "skills/movie-experts/editor/SKILL.md"
  - "skills/movie-experts/production/SKILL.md"
  - "skills/movie-experts/animation_studio/SKILL.md"
tech-stack:
  added: []
  patterns:
    - "Deprecation pattern: keep dir + extend frontmatter + insert body notice (distinct from Phase 13-15 rename/merge redirect-stub pattern)"
    - "Self-reference collapse rule: when inheritance target lists deprecated ID in its own related_skills, remove only (no self-reference add)"
    - "Body-prose annotation: (Phase 17 v3.0: was X) suffix or (replaces deprecated Phase 17 X) prefix"
key-files:
  created: []
  modified:
    - path: skills/movie-experts/performer/SKILL.md
      change: "+status: deprecated, +metadata.hermes.deprecated: true, +deprecated_reason (CN prose), +inheritance_targets: [character_designer, screenplay], +body deprecation blockquote; FOUND-08 expert_id + body preserved"
    - path: skills/movie-experts/scene_builder/SKILL.md
      change: "+status: deprecated, +metadata.hermes.deprecated: true, +deprecated_reason (CN prose), +inheritance_targets: [cinematographer, style_genome], +body deprecation blockquote; FOUND-08 preserved"
    - path: skills/movie-experts/storyboard_designer/SKILL.md
      change: "+status: deprecated, +metadata.hermes.deprecated: true, +deprecated_reason (CN prose), +inheritance_targets: [cinematographer], +body deprecation blockquote; FOUND-08 preserved"
    - path: skills/movie-experts/character_designer/SKILL.md
      change: "related_skills: removed performer (self-ref nonsensical — character_designer IS performer's inheritance target)"
    - path: skills/movie-experts/screenplay/SKILL.md
      change: "related_skills: removed performer (screenplay IS target) + scene_builder; body prose: 2 Collaboration bullets rewired to cinematographer + character_designer"
    - path: skills/movie-experts/cinematographer/SKILL.md
      change: "related_skills: removed scene_builder (self-ref); 10+ body prose mentions annotated with composition_lock sub-task notes"
    - path: skills/movie-experts/style_genome/SKILL.md
      change: "related_skills: removed scene_builder (self-ref) + performer, added character_designer; 8 body mentions annotated"
    - path: skills/movie-experts/visual_executor/SKILL.md
      change: "related_skills: removed performer + scene_builder, added character_designer; 4 body mentions annotated"
    - path: skills/movie-experts/audio_pipeline/SKILL.md
      change: "related_skills: removed performer + scene_builder, added character_designer + cinematographer; 10+ body mentions annotated across 6 sub-step sections"
    - path: skills/movie-experts/editor/SKILL.md
      change: "related_skills: NO change (no deprecated IDs); 4 body prose mentions annotated (Phase 17 v3.0: was scene_builder)"
    - path: skills/movie-experts/production/SKILL.md
      change: "related_skills: removed performer + scene_builder, added character_designer (cinematographer already present); 5 body mentions annotated"
    - path: skills/movie-experts/animation_studio/SKILL.md
      change: "related_skills (multi-line form): removed scene_builder bullet, added cinematographer; 3 body mentions annotated"
decisions:
  - "Deprecation pattern: keep dir + extend frontmatter + insert body notice (distinct from Phase 13-15 redirect-stub). Body content stays fully readable per FOUND-08."
  - "Self-reference collapse rule: inheritance target listing the deprecated ID just removes it (character_designer + performer; cinematographer + scene_builder; style_genome + scene_builder; screenplay + performer)."
  - "Body-prose annotation strategy: (Phase 17 v3.0: was X) suffix for Collaboration bullets (preserves handoff contract); replace-with-target for DAG strings (forward-looking)."
  - "scene_builder_handoff.json artifact filename PRESERVED in cinematographer body — stable contract name; annotation documents it now feeds internal composition_lock sub-task."
  - "animation_studio deviation (Rule 2): plan files_modified listed it but action narrative claimed no consumer work needed; actual audit found multi-line `scene_builder` bullet needing rewire to cinematographer."
  - "Zero storyboard_designer external consumers CONFIRMED — deeply nested in v1.5 DAG via body prose only, never via related_skills edge. SKIPPED per plan."
metrics:
  duration: ~25 minutes
  completed: 2026-06-17
  tasks: 2/2
  files-modified: 11
  commits:
    - d8cda9140
    - 2d8169e31
---

# Phase 17 Plan 01: Deprecate 3 Experts Summary

3 v1 movie-experts (performer, scene_builder, storyboard_designer) marked `status: deprecated` with FOUND-08 preservation + 8-consumer related_skills rewired to inheritance targets (character_designer + screenplay / cinematographer + style_genome / cinematographer) per ROADMAP §17 + skills-mapping.yaml not_in_new_dag rationale.

## What Was Built

### Task 1: 3 SKILL.md deprecated (commit d8cda9140)

Each of performer, scene_builder, storyboard_designer received additive frontmatter + a body deprecation notice. No body content was deleted, summarized, or commented out — FOUND-08 backward compatibility is preserved (legacy callers invoking these expert_ids still receive the full v1 expertise body for rendering).

**Frontmatter additions per file:**
- `status: deprecated` (top-level, sibling to `name`/`version`/`author`)
- Inside existing `metadata.hermes:` block: `deprecated: true`, `deprecated_reason: <CN prose citing skills-mapping.yaml rationale>`, `inheritance_targets: [<per-expert>]`
- Existing `expert_id`, `tags`, `related_skills`, `metrics` PRESERVED unchanged

**Per-expert inheritance_targets:**
- performer: `[character_designer, screenplay]` — voice + behavioral tics → character_designer; dialogue subtext → screenplay
- scene_builder: `[cinematographer, style_genome]` — mise-en-scène composition_lock → cinematographer; spatial aesthetics + style genes → style_genome
- storyboard_designer: `[cinematographer]` — composition_lock sub-task per Phase 7 §3.4 D3.4

**Body deprecation notice (immediately after H1):** Each file received a `> ⚠️ DEPRECATED (Phase 17 v3.0, 2026-06-17)` blockquote per CONTEXT.md template listing the targets + their absorbed functions + the FOUND-08 preservation note.

### Task 2: Consumer related_skills rewired (commit 2d8169e31)

8 consumer SKILL.md files had their `related_skills:` YAML lists edited to remove deprecated IDs and (where the inheritance target wasn't already present) add the appropriate target. Multi-line YAML form (animation_studio) and inline-array form (7 others) both handled.

**Self-reference collapse rule applied to 4 cases:**
- character_designer (listed performer; IS the performer target) → remove only
- cinematographer (listed scene_builder; IS the scene_builder target) → remove only
- style_genome (listed scene_builder; IS the scene_builder target) → remove only
- screenplay (listed performer; IS the performer target) → remove only

**Standard rewire applied to 4 cases:**
- visual_executor (had performer + scene_builder) → added character_designer; cinematographer already present
- audio_pipeline (had performer + scene_builder) → added character_designer + cinematographer
- production (had performer + scene_builder) → added character_designer; cinematographer already present
- animation_studio (had scene_builder in multi-line form) → replaced scene_builder bullet with cinematographer

**Body prose annotations** applied across all 8 consumers + editor (which had no related_skills change but had 4 body mentions). Strategy: preserve Collaboration-bullet handoff semantics with `(replaces deprecated Phase 17 X)` prefix or `(Phase 17 v3.0: was X)` suffix; replace-with-target for DAG strings (forward-looking). Total annotations: ~40+ across the 9 files.

**cinematographer special case:** As the scene_builder inheritance target with 10+ scene_builder body mentions (Handoff Boundaries table row + Hard boundary rule + Output Format + Workflow + Collaboration + What-NOT-to-do + Pipeline Position), each mention was annotated to note that scene_builder's feasibility role is now folded into cinematographer's internal composition_lock sub-task. The `scene_builder_handoff.json` artifact filename was PRESERVED (stable contract name) with an inline annotation noting it now feeds the internal sub-task.

## Verification Results

All plan-level verification checks PASSED:

1. `grep -l "^status: deprecated$" skills/movie-experts/{performer,scene_builder,storyboard_designer}/SKILL.md | wc -l` → **3** ✓
2. `grep -c "expert_id: performer" skills/movie-experts/performer/SKILL.md` → **1** (FOUND-08) ✓
3. `grep -c "expert_id: scene_builder" skills/movie-experts/scene_builder/SKILL.md` → **1** ✓
4. `grep -c "expert_id: storyboard_designer" skills/movie-experts/storyboard_designer/SKILL.md` → **1** ✓
5. Zero consumer related_skills YAML lists contain `performer` / `scene_builder` / `storyboard_designer` (strict multi-line + inline check) ✓
6. All 3 deprecated files have `> ⚠️ DEPRECATED` blockquote immediately after the H1 ✓
7. No duplicate IDs introduced in any related_skills list ✓
8. Zero storyboard_designer consumers confirmed (final grep returned empty) ✓

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] animation_studio consumer audit miss**
- **Found during:** Task 2 audit grep
- **Issue:** Plan action section claimed "storyboard_designer consumers: zero external consumers (grep returned empty). SKIP — no rewiring needed" and listed animation_studio in the `files_modified` block but the action narrative for scene_builder consumers enumerated 10 files NOT including animation_studio. Actual audit found animation_studio uses **multi-line** YAML form for related_skills and DID list `- scene_builder` as a bullet, plus 2 body prose mentions.
- **Fix:** Applied the same collapse rule: `scene_builder` bullet → `cinematographer` bullet in the multi-line YAML form; body prose mentions annotated. Total consumers rewired = 8 (plan narrative range was 7-10; 8 is within range).
- **Files modified:** `skills/movie-experts/animation_studio/SKILL.md`
- **Commit:** 2d8169e31

**2. [Rule 3 - Blocking issue] editor NOT in Task 2 related_changes but DID need body prose annotation**
- **Found during:** Task 2 body-prose scan
- **Issue:** editor has NO `performer` / `scene_builder` / `storyboard_designer` in its related_skills YAML list, so it correctly does NOT appear in the related_skills rewire set. However, editor body prose has 4 scene_builder mentions (fxrxt-axis-compliance ref description + Knowledge Retrieval bullet + Workflow step 5 + Collaboration inbound bullet) describing scene_builder as the feasibility counterpart. Per plan acceptance criterion ("body prose mentions of the 3 deprecated experts in consumer files are either replaced with inheritance targets OR annotated"), these needed annotation.
- **Fix:** Applied (Phase 17 v3.0: was scene_builder) annotations to the 4 editor body mentions; no related_skills YAML change (correctly absent). Plan files_modified listed editor — the action section's edge-rewiring rules didn't apply but the body-prose rule did.
- **Files modified:** `skills/movie-experts/editor/SKILL.md`
- **Commit:** 2d8169e31

### Decisions Made

1. **Deprecation ≠ redirect stub:** Plan CONTEXT explicitly distinguished this from Phase 13-15 rename/merge patterns — deprecated body content stays fully readable for FOUND-08 backward compatibility. No directory rename, no aliases field needed, no redirect stub.
2. **Self-reference collapse rule:** When the inheritance target itself lists the deprecated ID in its own related_skills, removing the deprecated ID and adding the target would create a nonsensical self-reference. Applied across 4 cases (character_designer, cinematographer, style_genome, screenplay).
3. **Artifact filename stability:** `scene_builder_handoff.json` filename preserved in cinematographer body to avoid breaking artifact schema; annotated inline to document it now feeds the internal composition_lock sub-task.
4. **Cinematographer body-prose density:** 10+ scene_builder mentions in cinematographer required careful annotation rather than wholesale rewrite — preserved v1 Handoff Boundaries table row (annotated as deprecated historical), updated Hard boundary rule, Workflow, Collaboration, Pipeline Position sections.

## Authentication Gates

None — pure markdown edits, no API or service calls.

## Known Stubs

None — no data flows were stubbed; the deprecation markers and annotations are complete and accurate.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries introduced beyond what the plan's threat model already covered.

## TDD Gate Compliance

N/A — this plan is `type: execute` (not `type: tdd`). No RED/GREEN/REFACTOR gate sequence required.

## Self-Check: PASSED

All 13 files (12 modified SKILL.md + SUMMARY.md) verified to exist on disk. Both task commits (d8cda9140, 2d8169e31) verified present in git log.
