---
phase: 13-expert-rename-alias-scaffolding
plan: 02
subsystem: skills/movie-experts
tags: [rename, alias, backward-compat, expert-id, compliance_gate]
requires:
  - skills-mapping.yaml (canonical mapping source, line 73)
  - FOUND-08 (zero-silent-rename rule)
provides:
  - skills/movie-experts/compliance_gate/ (renamed expert with alias metadata)
  - skills/movie-experts/compliance_marketing/SKILL.md (redirect-only stub)
affects:
  - 11 consumer SKILL.md related_skills arrays + body prose + cross-chain ref links
tech-stack:
  added: []
  patterns:
    - "Backward-compat rename pattern: new dir + redirect stub + metadata.hermes.aliases (reused from 13-01)"
    - "Bidirectional edge sync across collaboration graph"
key-files:
  created:
    - skills/movie-experts/compliance_gate/SKILL.md
    - skills/movie-experts/compliance_gate/references/cn-content-rules.md
    - skills/movie-experts/compliance_gate/references/viral-element-catalog.md
    - skills/movie-experts/compliance_gate/references/platform-specs-douyin.md
    - skills/movie-experts/compliance_gate/references/platform-specs-kuaishou.md
    - skills/movie-experts/compliance_gate/references/platform-specs-miniprogram.md
    - skills/movie-experts/compliance_gate/references/LICENSE.md
  modified:
    - skills/movie-experts/compliance_marketing/SKILL.md
    - skills/movie-experts/animation_studio/SKILL.md
    - skills/movie-experts/creative_source/SKILL.md
    - skills/movie-experts/documentary_maker/SKILL.md
    - skills/movie-experts/screenplay/SKILL.md
    - skills/movie-experts/script_auditor/SKILL.md
    - skills/movie-experts/theory_critic/SKILL.md
    - skills/movie-experts/hook_retention/SKILL.md
    - skills/movie-experts/editor/SKILL.md
    - skills/movie-experts/drawer/SKILL.md
    - skills/movie-experts/production/SKILL.md
    - skills/movie-experts/style_genome/SKILL.md
decisions:
  - "Apply FOUND-08: declare metadata.hermes.aliases: [compliance_marketing] on new SKILL.md for backward-compat dispatch"
  - "Preserve old compliance_marketing/references/ untouched (archival); only SKILL.md becomes redirect stub"
  - "Preserve LICENSE.md verbatim (including 'compliance_marketing Reference Corpus' header) — same pattern as 13-01 preserving continuity_auditor LICENSE verbatim"
  - "Apply uniform sed-based replacement across all 11 consumers — safe because the token compliance_marketing never collides with continuity_auditor or any English noun usage"
metrics:
  duration: ~15 min
  completed: 2026-06-17
  tasks_completed: 2
  tasks_total: 2
  files_created: 7
  files_modified: 12
---

# Phase 13 Plan 02: compliance_marketing → compliance_gate Rename Summary

Renamed v1 `compliance_marketing` movie-expert to `compliance_gate` per RENAME-02 (Phase 7 §4.15 — separate pure compliance from marketing) with full bidirectional edge sync, redirect-stub backward compat, and cross-chain ref link propagation. Pattern reused verbatim from 13-01 (continuity_auditor).

## What Was Done

### Task 1 — Created `compliance_gate/` expert directory (commit `ccad47b87`)

- New `skills/movie-experts/compliance_gate/` directory with full content
- **SKILL.md** frontmatter: `name: compliance_gate`, `expert_id: compliance_gate`, `metadata.hermes.aliases: [compliance_marketing]` (new field, FOUND-08 compliance)
- Body prose copied verbatim from old SKILL.md (When to use / References / Role & Philosophy / Core Capabilities / Output Format / Key Parameters / Per-Platform Branching / AIGC Labeling Workflow / Risk Review Workflow / RAG Invocation / Quality Thresholds / Collaboration / What NOT to do)
- RAG query tags inside body updated: `tags="expert:compliance_marketing,..."` → `tags="expert:compliance_gate,..."` (3 occurrences)
- `## Changelog` section appended documenting rename rationale (Phase 7 §4.15 + FOUND-08 alias preservation)
- 5 references (cn-content-rules.md + viral-element-catalog.md + 3 platform-specs-*.md + LICENSE.md) migrated verbatim — byte-for-byte identical to source (verified via diff)

### Task 2 — Redirect stub + 11-consumer rename propagation (commit `25f1b3d7e`)

- Old `skills/movie-experts/compliance_marketing/SKILL.md` replaced with **frontmatter-only redirect stub**: `name: compliance_marketing`, `metadata.hermes.{aliases: [compliance_gate], status: renamed, renamed_to: compliance_gate}` + 1 paragraph pointing to new location
- Old `compliance_marketing/references/` preserved untouched (archival; only SKILL.md became a stub)
- **11 consumer SKILL.md files updated** via uniform sed-based replacement:
  - `related_skills` array: `compliance_marketing` → `compliance_gate`
  - Body prose markdown links: `../compliance_marketing/SKILL.md` → `../compliance_gate/SKILL.md`
  - Cross-chain ref links (notably heavy in `hook_retention/SKILL.md`): `../../compliance_marketing/references/...` → `../../compliance_gate/references/...`
  - Collaboration-section bullets (`<- compliance_marketing` / `-> compliance_marketing`) renamed
  - Inline prose mentions of expert as citation (hook_retention "跨链 compliance_marketing catalog" etc.) renamed
  - JSON literal in `creative_source/SKILL.md` line 159: `"compliance_marketing"` → `"compliance_gate"`

## Deviations from Plan

None — plan executed exactly as written. The uniform sed-based replacement was safe because the token `compliance_marketing` never collides with `continuity_auditor` (the token handled by 13-01) or any English-noun usage that must be preserved. All shared consumer files (editor, drawer, production, style_genome) had their `continuity_auditor` tokens left intact — verified by regression check.

## Verification Results

All plan success criteria verified (full grep block in commit `25f1b3d7e`'s verify stage):

- [x] `skills/movie-experts/compliance_gate/SKILL.md` exists with `name: compliance_gate`, `expert_id: compliance_gate`, `metadata.hermes.aliases: [compliance_marketing]`
- [x] All other frontmatter fields (description, version 1.0.0, tags, related_skills, metrics, prerequisites) preserved verbatim
- [x] `skills/movie-experts/compliance_gate/references/` contains the 5 migrated ref files + LICENSE
- [x] `skills/movie-experts/compliance_marketing/SKILL.md` is a redirect stub (frontmatter + 1 paragraph)
- [x] Old `compliance_marketing/references/` preserved untouched (6 ref files unchanged on disk)
- [x] All 11 consumer SKILL.md files reference `compliance_gate` (not `compliance_marketing`) in related_skills + body prose + markdown links + cross-chain ref links + JSON literals
- [x] Changelog entry appended to new SKILL.md
- [x] Grep returns 0 stray `compliance_marketing` references outside redirect stub + new compliance_gate intentional mentions (aliases metadata, related_skills comment about HOOK listing, changelog entry)
- [x] **Regression check passes**: 13-01's `continuity_auditor` tokens in editor/drawer/production/style_genome are intact (no re-touching occurred)

## Self-Check: PASSED

### Files created (verified exist)
- FOUND: skills/movie-experts/compliance_gate/SKILL.md
- FOUND: skills/movie-experts/compliance_gate/references/cn-content-rules.md
- FOUND: skills/movie-experts/compliance_gate/references/viral-element-catalog.md
- FOUND: skills/movie-experts/compliance_gate/references/platform-specs-douyin.md
- FOUND: skills/movie-experts/compliance_gate/references/platform-specs-kuaishou.md
- FOUND: skills/movie-experts/compliance_gate/references/platform-specs-miniprogram.md
- FOUND: skills/movie-experts/compliance_gate/references/LICENSE.md

### Commits (verified exist)
- FOUND: ccad47b87 (feat(13-02): create compliance_gate expert)
- FOUND: 25f1b3d7e (refactor(13-02): rename compliance_marketing -> compliance_gate across consumers + redirect stub)
