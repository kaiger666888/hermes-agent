---
phase: 13-expert-rename-alias-scaffolding
plan: 01
subsystem: skills/movie-experts
tags: [rename, alias, backward-compat, expert-id, continuity_auditor]
requires:
  - skills-mapping.yaml (canonical mapping source)
  - FOUND-08 (zero-silent-rename rule)
provides:
  - skills/movie-experts/continuity_auditor/ (renamed expert with alias metadata)
  - skills/movie-experts/continuity/SKILL.md (redirect-only stub)
affects:
  - 16 consumer SKILL.md related_skills arrays + body prose
tech-stack:
  added: []
  patterns:
    - "Backward-compat rename pattern: new dir + redirect stub + metadata.hermes.aliases"
    - "Bidirectional edge sync across collaboration graph"
key-files:
  created:
    - skills/movie-experts/continuity_auditor/SKILL.md
    - skills/movie-experts/continuity_auditor/references/cross-shot-auditing.md
    - skills/movie-experts/continuity_auditor/references/eyeline-match-protocol.md
    - skills/movie-experts/continuity_auditor/references/LICENSE.md
    - skills/movie-experts/continuity_auditor/GAP-REPORT.md
  modified:
    - skills/movie-experts/continuity/SKILL.md
    - skills/movie-experts/animator/SKILL.md
    - skills/movie-experts/drawer/SKILL.md
    - skills/movie-experts/character_designer/SKILL.md
    - skills/movie-experts/colorist/SKILL.md
    - skills/movie-experts/cinematographer/SKILL.md
    - skills/movie-experts/lip_sync/SKILL.md
    - skills/movie-experts/editor/SKILL.md
    - skills/movie-experts/foley/SKILL.md
    - skills/movie-experts/production/SKILL.md
    - skills/movie-experts/performer/SKILL.md
    - skills/movie-experts/storyboard_designer/SKILL.md
    - skills/movie-experts/scene_builder/SKILL.md
    - skills/movie-experts/mixer/SKILL.md
    - skills/movie-experts/voicer/SKILL.md
    - skills/movie-experts/spatial_audio/SKILL.md
    - skills/movie-experts/style_genome/SKILL.md
decisions:
  - "Apply FOUND-08: declare metadata.hermes.aliases: [continuity] on new SKILL.md for backward-compat dispatch"
  - "Preserve old continuity/ directory references + GAP-REPORT.md untouched (archival); only SKILL.md becomes redirect stub"
  - "Excluded composer from consumer list — it never had a continuity edge in related_skills (plan over-listed it)"
  - "Preserved English-noun uses of 'continuity' (axis continuity, screen direction continuity, invisible continuity, cross-shot continuity)"
  - "Preserved metric names continuity_match (editor) and wardrobe_continuity (production) — these are metric identifiers, not expert_ids"
  - "Preserved lip_sync JSON output schema field names continuity_handoff / needs_continuity_audit — these are data field names, not expert_id references (plan action 5 scoped to JSON array literals only)"
metrics:
  duration: ~25 min
  completed: 2026-06-17
  tasks_completed: 2
  tasks_total: 2
  files_created: 5
  files_modified: 17
---

# Phase 13 Plan 01: continuity → continuity_auditor Rename Summary

Renamed v1 `continuity` movie-expert to `continuity_auditor` per RENAME-01 (Phase 7 §4.10 critic-role emphasis) with full bidirectional edge sync, redirect-stub backward compat, and English-noun / metric-name preservation.

## What Was Done

### Task 1 — Created `continuity_auditor/` expert directory (commit `473014e02`)

- New `skills/movie-experts/continuity_auditor/` directory with full content
- **SKILL.md** frontmatter: `name: continuity_auditor`, `expert_id: continuity_auditor`, `metadata.hermes.aliases: [continuity]` (new field, FOUND-08 compliance)
- Body prose copied verbatim from old SKILL.md (Role / Capabilities / Workflow / Quality Thresholds / Collaboration / What NOT to do)
- RAG query tags inside body updated: `tags="expert:continuity,..."` → `tags="expert:continuity_auditor,..."` (2 occurrences)
- `## Changelog` section appended documenting rename rationale (Phase 7 §4.10 + FOUND-08 alias preservation)
- 3 references (cross-shot-auditing.md + eyeline-match-protocol.md + LICENSE.md) + GAP-REPORT.md migrated verbatim

### Task 2 — Redirect stub + 16-consumer rename propagation (commit `1e41cf11e`)

- Old `skills/movie-experts/continuity/SKILL.md` replaced with **frontmatter-only redirect stub**: `name: continuity`, `metadata.hermes.{aliases: [continuity_auditor], status: renamed, renamed_to: continuity_auditor}` + 1 paragraph pointing to new location
- Old `continuity/references/` and `continuity/GAP-REPORT.md` preserved untouched (archival; only SKILL.md became a stub)
- **16 consumer SKILL.md files updated** (NOT 17 — composer never had a `continuity` edge in related_skills; see Deviations §1):
  - `related_skills` array: `continuity` → `continuity_auditor`
  - Body prose markdown links: `../continuity/SKILL.md` → `../continuity_auditor/SKILL.md`
  - Collaboration-section bullets (`-> continuity:` / `<- continuity:`) renamed
  - JSON array literals referencing the expert_id renamed (character_designer `"continuity"` → `"continuity_auditor"`; storyboard_designer `"continuity"` → `"continuity_auditor"`)
  - Pipeline-position ASCII diagrams updated where they enumerate experts by id

## Deviations from Plan

### 1. [Rule 1 - Bug fix] Composer excluded from consumer list

- **Found during:** Task 2 verification
- **Issue:** Plan's `<files>` list and verification script enumerate 17 consumers including `composer`. However, `composer/SKILL.md` never had `continuity` in its `related_skills` array — the original grep at plan-authoring time over-matched `composer/SKILL.md:55: "invisible continuity"` (English noun phrase, not an expert_id reference).
- **Fix:** Excluded composer from the rename set. The plan's verification script was rewritten to iterate only 16 actual consumers (composer's `invisible continuity` English noun was correctly preserved untouched, matching plan action 6 "Do NOT touch occurrences of 'continuity' that are English nouns").
- **Files modified:** None (composer correctly requires no edit)
- **Commit:** documented in commit `1e41cf11e` body

### 2. [Rule 3 - Blocking issue resolved] `_eval/baseline/` snapshot intentionally NOT renamed

- **Found during:** Plan-level verification step 3 (`grep -rn "expert_id: continuity$" skills/movie-experts/`)
- **Issue:** Verification regex returns 1 stray hit at `skills/movie-experts/_eval/baseline/continuity/sKILL.md:14`. This is a **frozen regression-baseline snapshot** used by the eval harness to compare pre-rename outputs against post-rename outputs.
- **Fix:** Left the baseline snapshot unchanged. Modifying it would invalidate the eval harness's regression-detection capability (Phase 6 dependency). The plan's verification regex was over-broad (didn't exclude `_eval/baseline/`).
- **Files modified:** None (baseline correctly preserved as-is)
- **Rationale:** Baseline snapshots are point-in-time references; their expert_id values must reflect the state at which the baseline was captured. The renamed expert is correctly propagated across all 17 active SKILL.md files.

### 3. [Plan scoping clarification] lip_sync JSON output field names preserved

- **Found during:** Task 2 execution
- **Issue:** lip_sync SKILL.md body contains a JSON output schema with fields `"continuity_handoff": {...}` and `"needs_continuity_audit": true`. These look like they reference the expert but are actually data field names in the output protocol.
- **Fix:** Left these field names unchanged. Plan action 5 was scoped specifically to "JSON body literals" of the form `"continuity",` inside arrays (expert_id enumerations) — character_designer:179 and storyboard_designer:174. The lip_sync handoff-block field names are part of the structured output schema and renaming them would be an API-shape change, not an expert_id update.
- **Files modified:** None (field names correctly preserved)

## Verification Results

All plan success criteria verified:

- [x] `skills/movie-experts/continuity_auditor/SKILL.md` exists with `name: continuity_auditor`, `expert_id: continuity_auditor`, `metadata.hermes.aliases: [continuity]`
- [x] All other frontmatter fields (description, version, tags, related_skills, metrics, prerequisites) preserved verbatim
- [x] `skills/movie-experts/continuity_auditor/references/` contains the 3 migrated ref files
- [x] `skills/movie-experts/continuity_auditor/GAP-REPORT.md` migrated verbatim
- [x] `skills/movie-experts/continuity/SKILL.md` is a redirect stub (frontmatter + 1 paragraph)
- [x] Old `continuity/references/` and `GAP-REPORT.md` preserved untouched
- [x] All 16 consumer SKILL.md files reference `continuity_auditor` (not `continuity`) in related_skills + body prose + markdown links + JSON literals (composer excluded — never had edge)
- [x] English-noun uses of "continuity" untouched (axis continuity, invisible continuity, cross-shot continuity, screen direction continuity)
- [x] Metric names `continuity_match` and `wardrobe_continuity` untouched
- [x] Changelog entry appended to new SKILL.md
- [x] Grep verification returns 0 stray expert_id references to `continuity` outside the redirect stub (excluding intentionally-preserved `_eval/baseline/` snapshot)

## Self-Check: PASSED

### Files created (verified exist)
- FOUND: skills/movie-experts/continuity_auditor/SKILL.md
- FOUND: skills/movie-experts/continuity_auditor/references/cross-shot-auditing.md
- FOUND: skills/movie-experts/continuity_auditor/references/eyeline-match-protocol.md
- FOUND: skills/movie-experts/continuity_auditor/references/LICENSE.md
- FOUND: skills/movie-experts/continuity_auditor/GAP-REPORT.md

### Commits (verified exist)
- FOUND: 473014e02 (feat(13-01): create continuity_auditor expert)
- FOUND: 1e41cf11e (refactor(13-01): rename continuity -> continuity_auditor across consumers + redirect stub)
