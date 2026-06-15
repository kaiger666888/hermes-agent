---
phase: 00-audit-eval-skeleton-blocker-gate
plan: 04
subsystem: movie-experts
tags: [audit, gap-report, phantom-cleanup, references-table, foundation-docs]
requires:
  - 00-01-PLAN (phantom detector + audit JSON)
  - 00-02-PLAN (baseline snapshots)
provides:
  - 14 GAP-REPORT.md files (audit findings per expert)
  - _shared/glossary.md (EN<->CN term dictionary, 24 entries)
  - _shared/SKILL-LAYOUT.md (standard skill directory layout spec)
  - _shared/RAG-INVOCATION-PATTERN.md (provider-agnostic RAG contract)
  - 14 SKILL.md files with ## References table skeleton
  - Phantom-free SKILL.md inventory (verify_skill_references.py --strict exits 0)
affects:
  - animator/SKILL.md (wan22_video stripped -> <video_gen_primary>)
  - performer/SKILL.md (168K controlled tokens stripped -> ExBxSxP description)
  - drawer/SKILL.md (References table inserted; flux allowlisted)
  - foley/SKILL.md (References table inserted; synthesis_model/audioldm-2/audiogen allowlisted)
  - _shared/known-external-models.yaml (4 new allowlist entries)
tech-stack:
  added: []
  patterns:
    - "Provider-agnostic placeholder tokens (<video_gen_primary>, <image_gen_primary>, <audio_gen_primary>)"
    - "GAP-REPORT.md 5-section structure (<phantoms>, <knowledge_gaps>, <prompt_weak_points>, <stale_metrics>, <missing_refs_topics>)"
    - "## References table as stable contract anchor for Phase 3 ref authoring"
key-files:
  created:
    - skills/movie-experts/animator/GAP-REPORT.md
    - skills/movie-experts/colorist/GAP-REPORT.md
    - skills/movie-experts/composer/GAP-REPORT.md
    - skills/movie-experts/continuity/GAP-REPORT.md
    - skills/movie-experts/drawer/GAP-REPORT.md
    - skills/movie-experts/editor/GAP-REPORT.md
    - skills/movie-experts/foley/GAP-REPORT.md
    - skills/movie-experts/mixer/GAP-REPORT.md
    - skills/movie-experts/performer/GAP-REPORT.md
    - skills/movie-experts/scene_builder/GAP-REPORT.md
    - skills/movie-experts/screenplay/GAP-REPORT.md
    - skills/movie-experts/spatial_audio/GAP-REPORT.md
    - skills/movie-experts/style_genome/GAP-REPORT.md
    - skills/movie-experts/voicer/GAP-REPORT.md
    - skills/movie-experts/_shared/glossary.md
    - skills/movie-experts/_shared/SKILL-LAYOUT.md
    - skills/movie-experts/_shared/RAG-INVOCATION-PATTERN.md
  modified:
    - skills/movie-experts/animator/SKILL.md
    - skills/movie-experts/colorist/SKILL.md
    - skills/movie-experts/composer/SKILL.md
    - skills/movie-experts/continuity/SKILL.md
    - skills/movie-experts/drawer/SKILL.md
    - skills/movie-experts/editor/SKILL.md
    - skills/movie-experts/foley/SKILL.md
    - skills/movie-experts/mixer/SKILL.md
    - skills/movie-experts/performer/SKILL.md
    - skills/movie-experts/scene_builder/SKILL.md
    - skills/movie-experts/screenplay/SKILL.md
    - skills/movie-experts/spatial_audio/SKILL.md
    - skills/movie-experts/style_genome/SKILL.md
    - skills/movie-experts/voicer/SKILL.md
    - skills/movie-experts/_shared/known-external-models.yaml
decisions:
  - "flux (bare family name) allowlisted — real model family covering FLUX 1.x and 2; specific version goes in references/*.md"
  - "synthesis_model, audioldm-2, audiogen allowlisted as legitimate legacy tokens; foley/SKILL.md body recommendation flagged as stale (AudioLDM-2 -> stable_audio rewrite deferred to Phase 5)"
  - "168K controlled tokens confirmed fabricated (not a typo) — stripped entirely, replaced with concrete ExBxSxP description"
  - "References table inserted before '## Role & Philosophy' in all 14 for consistent placement (Phase 3 relies on this anchor)"
metrics:
  duration: "8m 42s"
  completed: "2026-06-15"
  tasks: 4
  files_created: 17
  files_modified: 15
  commits: 17
---

# Phase 0 Plan 04: Audit Reports + Phantom Cleanup + Foundation Docs Summary

14 GAP-REPORTs published, 2 confirmed phantom references stripped (wan22_video / 168K controlled tokens), 4 real-but-flagged tokens allowlisted (flux / synthesis_model / audioldm-2 / audiogen), 3 _shared foundation docs created, References table skeleton inserted into all 14 SKILL.md, strict audit gate exits 0.

## What Was Built

### Task 1: 14 GAP-REPORT.md files

Each expert got a structured audit report with 5 sections: `<phantoms>` (from verify_skill_references.py JSON), `<knowledge_gaps>` (craft topics the expert should know but doesn't cover), `<prompt_weak_points>` (vague phrasing / undefined thresholds), `<stale_metrics>` (metric names without measurement protocols), `<missing_refs_topics>` (proposed reference file topics for Phase 3/5).

Phantom findings logged per expert:
- **animator**: 5 (wan2 ×4, wan22_video ×1) — all stripped in Task 2
- **drawer**: 6 (flux ×6) — all allowlisted in Task 2 (real family name)
- **foley**: 1 (synthesis_model) — allowlisted + AudioLDM-2/AudioGen context noted as stale
- **performer**: 1 (168K controlled tokens) — stripped in Task 2 (fabricated)
- **other 10 experts**: 0 phantoms

Each GAP-REPORT references `eval-baseline-v1` tag for FOUND-04 traceability. Per-expert research classification honored: screenplay/editor/colorist/style_genome = "needs deep refs (4-6)"; continuity/scene_builder/animator/drawer/composer/mixer/foley/voicer/spatial_audio/performer = "needs light-to-medium refs (2-4)".

### Task 2: Phantom strip from animator + performer SKILL.md

**animator/SKILL.md** (5 edits):
- description: "Wan2.2 video generation" → "current video generation models"
- tags: `wan22` → `video-gen`
- H1 subtitle: "Wan2.2 video generation specialist" → "Current video generation model specialist"
- H3: "### Wan2.2 Generation" → "### Video Generation"
- model field: `wan22_video (primary), wan22_video_turbo (preview only)` → `<video_gen_primary> (primary), <video_gen_preview> (preview only)`

**performer/SKILL.md** (3 edits):
- description: stripped "with 168K controlled tokens" → "parametric dispatch across Emotion, Body mechanics, Spatial staging, and Prompt engineering dimensions"
- H1 subtitle: stripped "with 168K controlled performance tokens" → "a parametric dispatch system across Emotion, Body mechanics, Spatial staging, and Prompt engineering dimensions"
- Role bullet: "168K controlled performance token parametric dispatch" → "Parametric dispatch across Emotion, Body mechanics, Spatial staging, and Prompt engineering dimensions"

**_shared/known-external-models.yaml** (4 new allowlist entries):
- `flux` — Black Forest Labs FLUX family shorthand (covers 1.x and 2)
- `synthesis_model` — generic suffix token for audio synthesis model field name
- `audioldm-2` — real research-era text-to-audio model (flagged as stale in foley GAP-REPORT)
- `audiogen` — real Meta AudioCraft text-to-audio model

**expert_id preservation (FOUND-08):** both `animator` and `performer` expert_id values verified UNCHANGED post-edit.

### Task 3: _shared foundation docs

**glossary.md** (142 lines, 24 H3 entries):
- All 15 SC #5 required terms present (运镜, 钩子, 卡点, 爆款, 男频, 女频, 完播率, 付费卡点, 爽点, 击中点, 镜头语言, 景别, 视角, 轴线, 调度)
- 9 extended terms added beyond SC #5 minimum (转发率, 竖屏, 备案, 标识, 男主/女主, 小程序剧, 慕强, alt-form 钩子)
- Each entry has CN / EN / Context structure

**SKILL-LAYOUT.md** (113 lines, FOUND-05):
- Required files (SKILL.md, references/*.md, _eval/prompts/<expert>.yaml)
- Optional files (baseline, LICENSE.md, GAP-REPORT.md)
- Forbidden (Python/JS code, lowercase skill.md, symlinks, binary assets)
- Naming conventions (expert_id == directory name, snake_case, frozen for existing 14)
- Frontmatter schema (mandatory + optional fields)
- Canonical body section order (12 sections, References table at position 3)
- Example directory tree

**RAG-INVOCATION-PATTERN.md** (102 lines, FOUND-06):
- Hard rule: NEVER hardcode fact_store / mem0_search / vendor API names in SKILL.md body
- Canonical conditional-phrasing template (graceful degradation to bundled refs)
- Before/after anti-pattern example
- Placeholder token convention table (7 placeholders: video_gen_primary/preview, image_gen_primary/fast, audio_gen_primary, music_gen_primary, tts_primary)
- Memory plugin tag convention (`tags="expert:<id>,domain:<topic>"`)

### Task 4: References table skeleton in 14 SKILL.md (FOUND-07)

Inserted identical markdown block into all 14 SKILL.md files, immediately after `## When to use this skill`, before `## Role & Philosophy`:

```markdown
## References

| Ref | When to Read | Contents |
|-----|--------------|----------|
| _(Phase 3 will populate with curated refs)_ | — | — |
```

Consistent placement across all 14 — Phase 3 ref authoring will rely on this stable anchor. Idempotent (grep for `^## References$` before insert; skip if present). Non-destructive (surgical Edit, no file rewrite). All 14 expert_id values verified UNCHANGED.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Critical functionality] Added allowlist entries for legitimately-flagged tokens**
- **Found during:** Task 2 (scanner triage)
- **Issue:** The plan listed drawer `flux` and foley `synthesis_model` as candidates needing triage. The scanner flagged 6 `flux` occurrences in drawer and 1 `synthesis_model` in foley. Triage: all are real model names / field names, not phantoms.
- **Fix:** Added `flux`, `synthesis_model`, `audioldm-2`, `audiogen` to `_shared/known-external-models.yaml` with provenance notes. Flagged AudioLDM-2 recommendation as stale in foley GAP-REPORT (Phase 5 will rewrite to stable_audio).
- **Files modified:** `skills/movie-experts/_shared/known-external-models.yaml`
- **Commit:** ae5b4449c

**2. [Rule 1 - Bug] References table inserted before `## Role & Philosophy` instead of immediately after `## When to use this skill`**
- **Found during:** Task 4
- **Issue:** Plan specified insertion "immediately after `## When to use this skill` section". However, the When-to-use section content varies in length per expert, making the content-end a non-unique anchor for Edit tool. The next stable header (`## Role & Philosophy`) is present in all 14 and uniquely identifies the insertion point.
- **Fix:** Inserted `## References` block immediately BEFORE `## Role & Philosophy`. Net effect is identical: References table appears between When-to-use content and Role-Philosophy, which IS "immediately after the When-to-use section". The placement is consistent across all 14.
- **Files modified:** 14 SKILL.md files
- **Commit:** 4efea0d82

## Snapshot Drift Report (Expected)

`python3 skills/movie-experts/_eval/snapshot.py verify` reports DRIFT on all 14 baselines. This is EXPECTED and CORRECT:

- Baselines were captured by Plan 00-02 (pre-cleanup state, tag `eval-baseline-v1`)
- This plan (00-04) modified all 14 SKILL.md files:
  - animator + performer: phantom strip (Task 2) + References table (Task 4)
  - other 12: References table only (Task 4)
- The drift IS the proof that cleanup happened AFTER baseline was captured. This satisfies the verification note in the plan: "baseline = pre-cleanup state; current = post-cleanup state".

Phase 3 (RAG uplift) will re-run eval comparisons against this same `eval-baseline-v1` tag — the baseline represents the pre-refactor starting point, not a re-snapshot target.

## BLOCKER GATE Status

**PASSED.** The Phase 0 BLOCKER GATE is now closed:

- `python3 scripts/verify_skill_references.py --strict` exits 0 (zero phantoms)
- 14 GAP-REPORT.md files exist with all 5 required sections each
- `_shared/glossary.md` (24 entries), `_shared/SKILL-LAYOUT.md`, `_shared/RAG-INVOCATION-PATTERN.md` published
- 14 SKILL.md files carry `## References` table skeleton (FOUND-07)
- All 14 `expert_id` values verified UNCHANGED (FOUND-08)
- Phantom tokens (`wan22_video`, `168K controlled tokens`) absent from all 14 SKILL.md

Phase 1 (EXPERT-COMPLI legal gate) is now unblocked.

## Self-Check: PASSED

- 17 created files verified present (14 GAP-REPORT.md + 3 _shared docs)
- 17 commits verified in git log (14 GAP-REPORT commits + 1 phantom strip + 1 foundation docs + 1 References table)
- `verify_skill_references.py --strict` exits 0 (verified after every task)
- All 14 expert_id values unchanged (verified via grep loop)
- All 14 SKILL.md files contain `## References` header + 3-column table (verified via grep loop)
