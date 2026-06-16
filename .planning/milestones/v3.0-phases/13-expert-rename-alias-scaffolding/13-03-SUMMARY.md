---
phase: 13-expert-rename-alias-scaffolding
plan: 03
subsystem: skills/movie-experts
tags: [close-out, sign-off, documentation, skills-mapping, readme, glossary]
requires:
  - 13-01 (continuity_auditor rename complete)
  - 13-02 (compliance_gate rename complete)
  - skills-mapping.yaml (canonical mapping source, lines 66-78)
provides:
  - skills-mapping.yaml with both renamed entries signed_off
  - README.md inventory + corpus tree + ASCII DAG updated for both renames
  - _shared/glossary.md expert_id references updated
affects:
  - downstream phases 14-18 reading skills-mapping.yaml as authoritative source
  - new developers reading README.md to navigate expert corpus
tech-stack:
  added: []
  patterns:
    - "Documentation close-out wave: update cross-cutting docs AFTER per-expert renames land"
    - "English-noun preservation rule: 'visual continuity reference' is a noun phrase, NOT an expert_id reference"
key-files:
  created:
    - .planning/phases/13-expert-rename-alias-scaffolding/13-03-SUMMARY.md
  modified:
    - .planning/research/v2-pipeline-design/skills-mapping.yaml
    - skills/movie-experts/README.md
    - skills/movie-experts/_shared/glossary.md
decisions:
  - "Added `signed_off_at: 2026-06-17` + `signed_off_by: phase-13` traceability fields under each signed_off entry (CONTEXT.md explicitly granted Claude's discretion on this)"
  - "ASCII DAG diagram compliance box kept multi-line form (`compliance_` / `gate 合规`) for box-width alignment consistency with character_designer multi-line pattern"
  - "English-noun phrase 'visual continuity reference' in glossary line 195 left untouched per plan action 6 (NOT an expert_id reference)"
metrics:
  duration: ~10 min
  completed: 2026-06-17
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 3
---

# Phase 13 Plan 03: Close-Out (skills-mapping sign_off + README + glossary) Summary

Closed out Phase 13 by (1) flipping `sign_off_status: pending` → `signed_off` for both renamed entries in the canonical skills-mapping.yaml, (2) propagating the new expert IDs and directory paths across the README.md inventory / corpus tree / ASCII pipeline diagram / shell-loop example, and (3) updating _shared/glossary.md expert_id references. This is Wave 3 of Phase 13 — pure documentation closure that depends on both Wave 1 (13-01) and Wave 2 (13-02) having completed.

## What Was Done

### Task 1 — skills-mapping.yaml sign-off (commit `8985f450a`)

- `.planning/research/v2-pipeline-design/skills-mapping.yaml` lines 66-78 (the two `one_to_one_renamed` entries under the "=== 1:1 renamed (2) — requires skills team sign-off ===" comment block):
  - `new_node: continuity_auditor`: `sign_off_status: pending` → `sign_off_status: signed_off` + added `signed_off_at: 2026-06-17` + `signed_off_by: phase-13`
  - `new_node: compliance_gate`: `sign_off_status: pending` → `sign_off_status: signed_off` + added `signed_off_at: 2026-06-17` + `signed_off_by: phase-13`
- All other YAML content preserved verbatim (`mapping_type`, `rename_rationale`, `sign_off_required`, `v1_expert_id`, `new_node`)
- Traceability fields added per CONTEXT.md "Claude's Discretion" grant — explicit sign-off timestamp + signer make the audit trail unambiguous for Phase 18 verification
- **Fulfills ROADMAP §13 success criterion #5 (hard requirement):** "`skills-mapping.yaml` `sign_off_status` updated: `pending` → `signed_off` for both renamed entries"
- Downstream impact: Phase 14 (visual_executor merge) + Phase 15 (audio_pipeline merge) + Phase 16 (prompt_injector new) + Phase 17 (deprecations) can all now read this file and treat the two renames as authoritative rather than provisional

### Task 2 — README.md + _shared/glossary.md documentation propagation (commit `71da7c0f7`)

**README.md (11 sites updated):**

- Line 31 — corpus traceability table row: `theory_critic, compliance_marketing` → `theory_critic, compliance_gate`
- Line 77 — inventory row: `[`continuity`](./continuity/SKILL.md)` → `[`continuity_auditor`](./continuity_auditor/SKILL.md)` (Chinese name 连续性专家 preserved)
- Line 83 — inventory row: `[`compliance_marketing`](./compliance_marketing/SKILL.md)` → `[`compliance_gate`](./compliance_gate/SKILL.md)` (Chinese name 合规与宣发专家 preserved)
- Lines 135-136 — ASCII DAG diagram compliance box: `compliance_` / `marketing 合规` → `compliance_` / `gate 合规` (multi-line form preserved for box-width alignment consistency with character_designer box)
- Line 201 — ASCII DAG diagram audit marker: `◄──── continuity (parallel audit)` → `◄──── continuity_auditor (parallel audit)`
- Line 215 — Identity contract bullet: `consumed by drawer / animator / lip_sync / continuity` → `... / continuity_auditor`
- Line 219 — Audit nodes bullet: `**Audit nodes:** \`continuity\` (parallel to mixer) + ...` → `**Audit nodes:** \`continuity_auditor\` (parallel to mixer) + ...`
- Line 291 — Ref corpus summary row: `| compliance_marketing | 5 | ~80 KB | 2026-06-15 |` → `| compliance_gate | 5 | ~80 KB | 2026-06-15 |`
- Line 335 — Phase 6 shell loop: `... compliance_marketing hook_retention production` → `... compliance_gate hook_retention production`
- Lines 377 + 379 — File-layout corpus tree: `├── compliance_marketing/ ...` → `├── compliance_gate/ ...`; `├── continuity/ ...` → `├── continuity_auditor/ ...`
- Line 405 — Eval demo yaml listing: `compliance_marketing_demo.yaml` → `compliance_gate_demo.yaml`

**_shared/glossary.md (2 expert_id references updated):**

- Line 164 — Character Bible CN definition (Phase 7 addition): `... drawer / animator / lip_sync / continuity)的 ground truth` → `... drawer / animator / lip_sync / continuity_auditor)的 ground truth`
- Line 186 — Storyboard Context line: `downstream consumers are drawer / animator / editor / continuity.` → `downstream consumers are drawer / animator / editor / continuity_auditor.`
- Line 195 — **English-noun "visual continuity reference" PRESERVED untouched** (NOT an expert_id reference; per plan action 6)

## Deviations from Plan

None — plan executed exactly as written. The plan's grep-enumerated line numbers all matched the file state on disk (lines had not drifted because 13-01 and 13-02 correctly excluded README.md + glossary.md from their files_modified lists).

Two Claude-discretion decisions exercised per CONTEXT.md "Claude's Discretion" grant:

1. **Traceability fields added** (`signed_off_at`, `signed_off_by`) — CONTEXT.md explicitly offered this as optional but recommended for audit trail. Added under both entries with identical timestamp + signer.
2. **ASCII diagram multi-line form preserved** — original `compliance_` / `marketing 合规` two-line pattern replaced with `compliance_` / `gate 合规` (same two-line form, same column alignment) rather than collapsing to a single-line form. This keeps visual consistency with the other multi-line box in the same diagram (`character_` / `designer`).

## Verification Results

All 9 plan success criteria verified:

- [x] skills-mapping.yaml: both renamed entries show `sign_off_status: signed_off` (count = 2)
- [x] Exactly 2 `sign_off_status: signed_off` occurrences; zero `pending` for renamed entries (count = 0)
- [x] README.md inventory rows link to new directory paths (`./continuity_auditor/SKILL.md` count=1, `./compliance_gate/SKILL.md` count=1)
- [x] README.md corpus tree shows new directory names (`continuity_auditor/` count=2, `compliance_gate/` count=2)
- [x] README.md ASCII pipeline diagram uses new IDs (continuity_auditor marker + compliance box)
- [x] README.md has zero stranded `compliance_marketing` references (count = 0)
- [x] README.md has zero stranded `continuity` expert_id references (count = 0; English-noun uses preserved)
- [x] _shared/glossary.md references `continuity_auditor` where it referred to the expert (count = 2)
- [x] _shared/glossary.md preserves English-noun "visual continuity reference" (count = 1)

## Self-Check: PASSED

### Files created (verified exist)
- FOUND: .planning/phases/13-expert-rename-alias-scaffolding/13-03-SUMMARY.md (this file)

### Files modified (verified via git)
- FOUND: .planning/research/v2-pipeline-design/skills-mapping.yaml (commit 8985f450a)
- FOUND: skills/movie-experts/README.md (commit 71da7c0f7)
- FOUND: skills/movie-experts/_shared/glossary.md (commit 71da7c0f7)

### Commits (verified exist)
- FOUND: 8985f450a (chore(13-03): sign off both renamed entries in skills-mapping.yaml)
- FOUND: 71da7c0f7 (docs(13-03): rename expert references in README + glossary (Phase 13 close-out))
