---
phase: 16-new-prompt-injector-expert
plan: 02
subsystem: movie-experts/prompt_injector (close-out docs)
tags: [movie, prompt-engineering, close-out, documentation, dag-diagram, glossary]
requires:
  - "16-01-SUMMARY.md (prompt_injector expert created with SKILL.md + 4 refs + bidirectional edges)"
  - "Phase 15 close-out pattern (README + corpus tree + DAG + _shared/ + skills-mapping.yaml sign-off)"
provides:
  - "skills/movie-experts/README.md updated: Phase 16 inventory section + prompt_injector node in DAG + corpus tree row + footer count 17 → 18"
  - "skills/movie-experts/_shared/glossary.md updated: prompt_injector H3 bilingual entry"
  - ".planning/research/v2-pipeline-design/skills-mapping.yaml updated: prompt_injector entry signed_off + action_for_v21 FULFILLED record"
affects:
  - "ROADMAP §16 criterion #6 (README 21-expert inventory lists prompt_injector as NEW Phase 16 entry) — SATISFIED"
  - "Phase 18 VALIDATE-01 will find sign_off_status: signed_off on prompt_injector entry when it audits all mappings"
tech-stack:
  added: []
  patterns:
    - "Phase 13/14/15 close-out pattern applied to Phase 16 NEW expert (no merge predecessor — single-row inventory section, no redirect stub annotations in corpus tree)"
    - "Multi-line ASCII DAG box form (prompt_injector / 提示注入) per Phase 13-15 multi-line box precedent"
    - "Self-documenting footer arithmetic: 17 + 1 NEW (no merge offset) = 18, with forward note that Phase 17 deprecations + Phase 18 canonical reconciliation will arrive at 21"
    - "action_for_v21 repurposed from forward-looking note to FULFILLED-in-v3.0 completion record (preserves audit trail in single field)"
key-files:
  created:
    - .planning/phases/16-new-prompt-injector-expert/16-02-SUMMARY.md
  modified:
    - skills/movie-experts/README.md
    - skills/movie-experts/_shared/glossary.md
    - .planning/research/v2-pipeline-design/skills-mapping.yaml
decisions:
  - "Phase 16 inventory section uses single-row table (1 NEW expert) — distinct from Phase 14/15 multi-row tables (which enumerated merge predecessors + new merged entry)"
  - "ASCII DAG prompt_injector box placed between storyboard_designer and visual_executor per nodes.yaml io_contract (consumes visual_intent, outputs model_prompts + consistency_context)"
  - "Parallel inbound edges from style_genome_5d + character_assets annotated as comments on the prompt_injector box (per plan's 'do NOT draw direct creative_source → prompt_injector arrow' instruction — indirect path documented in Key DAG properties bullet)"
  - "Footer count text explicitly documents Phase 17 deprecation plan (3 candidates) + Phase 18 canonical 21 target (16 DAG + 5 aliases) so the intermediate 18-count is unambiguous"
  - "action_for_v21 field repurposed (not appended) — single field carries both the original forward-looking intent and the v3.0 fulfillment per CONTEXT D-06 'No silent sign-off'"
  - "Glossary entry placed under new 'Phase 16 additions' H2 section (matching Phase 14 / Phase 15 H2 section pattern)"
metrics:
  duration: ~10min
  completed: 2026-06-17
  tasks_total: 2
  tasks_completed: 2
  files_created: 1
  files_modified: 3
---

# Phase 16 Plan 02: prompt_injector Close-Out Documentation Summary

Closed out Phase 16 with full documentation integration: README inventory + corpus tree + ASCII DAG diagram + footer arithmetic + bilingual glossary entry + skills-mapping.yaml sign-off. After this plan, all 6 ROADMAP §16 success criteria are satisfied (criterion #6 specifically required README 21-expert inventory listing). A reader skimming the docs now sees prompt_injector integrated as the new AI-native expert in every canonical surface.

## What Was Built

### Task 1: README inventory + corpus tree + DAG diagram + footer update (commit 179030a4e)

Updated `skills/movie-experts/README.md` with four discrete edits:

- **Inventory table:** Added new `### 1 New Expert (Phase 16 — AI-Native prompt_injector, 2026-06-17)` section after the Phase 8 section. Single-row table with Chinese name 提示注入专家 + role summary + source citation (02-NODE-SPECS.md §2.7 + Phase 7 §4.7 D3.5+D2.4) + ref count (4). Satisfies ROADMAP §16 criterion #6.
- **ASCII DAG diagram:** Inserted `prompt_injector` node between `storyboard_designer` and `visual_executor` per nodes.yaml io_contract. Two-line multi-line box form (`prompt_injector` / `提示注入`) per Phase 13-15 multi-line box precedent (label exceeds 13-char single-line width). Parallel inbound edges from `style_genome_5d` and `character_assets` annotated as comments on the box (per plan instruction — indirect path from DAG root `creative_source` documented in Key DAG properties bullet rather than drawn as direct arrow, which would misrepresent data flow).
- **Key DAG properties section:** Added new bullet documenting AI-native prompt assembly role — distinct from cinematographer (which owns shot intent / composition_lock), prompt_injector owns the prompt-assembly layer that did not exist in traditional pre-AI cinematography.
- **Corpus tree:** Added `prompt_injector/` directory row with 4 refs (prompt-engineering-patterns / cross-call-consistency / token-budget-management / model-specific-prompt-templates) + LICENSE.md + GAP-REPORT.md placeholder.
- **Footer count:** Updated 17 → 18 with self-documenting arithmetic annotation. The text explicitly notes Phase 17 will deprecate 3 candidates (performer / scene_builder / storyboard_designer) and Phase 18 will reconcile to canonical 21-expert topology (16 DAG pipeline-roles + 5 aliases), so the intermediate 18-count is unambiguous for Phase 18 audit.
- **Top-of-file Status line:** Updated from v2 "26 experts" claim to v3.0 "18 active expert_ids (17 post-Phase-15 + 1 Phase 16 prompt_injector NEW)" with Phase 13-16 transition history. (Pre-existing v2 Status line was stale after Phases 13-15 — this update brings it current through Phase 16.)

### Task 2: Glossary entry + skills-mapping.yaml sign-off (commit 11454d246)

Two discrete edits across two files:

- **_shared/glossary.md:** Added new `### prompt_injector / 提示注入 / Prompt Injector` H3 entry under a new `## Phase 16 additions` H2 section (matching Phase 14 / Phase 15 H2 section pattern). Bilingual header follows Phase 14/15 convention. Body covers: AI-native node status, I/O contract (visual_intent + style_genome_5d + character_assets → model_prompts + consistency_context), success criteria (cross_call_consistency ≥ 0.85 + prompt_token_efficiency ≤ 4000 tokens/call), fail modes + fallbacks (consistency_drift + prompt_overload), related_skills peer set, mapping_type `new_ai_native`. Placed at the end of the glossary after the Phase 15 audio_pipeline entry.
- **skills-mapping.yaml:** Signed off the prompt_injector entry (lines 99-103). Added three traceability fields per Phase 13 close-out convention: `sign_off_status: signed_off` + `signed_off_at: 2026-06-17` + `signed_off_by: phase-16`. Repurposed `action_for_v21` field from forward-looking note ("Add prompt_injector expert in v2.1+ skills milestone") to FULFILLED-in-v3.0 completion record — single field now carries both the original forward-looking intent AND the v3.0 fulfillment, preserving audit trail per CONTEXT D-06 "No silent sign-off". Phase 18 VALIDATE-01 will find `sign_off_status: signed_off` on the prompt_injector entry when it audits all mappings.

## Deviations from Plan

None — plan executed exactly as written.

**Notes on minor judgment calls (not deviations, just clarifications):**

- **Top-of-file Status line update:** The plan's `<interfaces>` block described the README structure starting at line 10 (`## 🆕 Phase 8 Update`) and listed inventory tables + DAG + corpus tree + footer as the four edit targets, but did not explicitly mention the top-of-file `**Status:**` line (line 5). That Status line was stale ("v2 complete — 26 experts") after Phases 13-15. Updated it to "v3.0 in progress — 18 active expert_ids" to keep the document internally consistent with the new footer count. This is within the spirit of Task 1's "Four discrete edits" (the plan's verify block greps for `18 active expert_ids` and finds it in both the Status line and the footer — both must reflect the same count).
- **Glossary placement:** Plan action said "append a new H3 entry at the end of the glossary (or in alphabetical/logical position consistent with surrounding entries)". Chose end-of-file placement under a new `## Phase 16 additions` H2 section, matching the Phase 14 (`## Phase 14 additions`) and Phase 15 (`## Phase 15 additions`) H2 section pattern. This is consistent with surrounding entries.

## Verification Results

All 9 plan verification criteria satisfied:

1. README.md inventory section lists prompt_injector with Chinese name 提示注入 + role + ref count — PASS (Phase 16 section header + table row verified)
2. ASCII DAG diagram includes prompt_injector node between storyboard_designer and visual_executor with two-line multi-line box form — PASS (`prompt_injector` + `提示注入` two-line box)
3. Key DAG properties section has a new bullet documenting AI-native prompt assembly role — PASS (`AI-native prompt assembly` bullet found)
4. Corpus tree lists prompt_injector/ directory with 4 refs + LICENSE + GAP-REPORT — PASS (5-line corpus tree block verified)
5. Footer count updated 17 → 18 with self-documenting arithmetic annotation — PASS (`18 active expert_ids` appears in both Status line and footer)
6. _shared/glossary.md has prompt_injector H3 entry with bilingual header + body covering I/O contract + metrics + fail modes + related_skills — PASS (`### prompt_injector / 提示注入 / Prompt Injector` header + body verified)
7. skills-mapping.yaml prompt_injector entry has sign_off_status: signed_off + signed_off_at: 2026-06-17 + signed_off_by: phase-16 — PASS (all three fields verified)
8. action_for_v21 field updated to FULFILLED-in-v3.0 completion record — PASS (`FULFILLED in v3.0 milestone Phase 16` string found)
9. ROADMAP §16 criterion #6 satisfied (README 21-expert inventory lists prompt_injector as NEW Phase 16 entry) — PASS (Phase 16 inventory section + table row verified)

## Self-Check: PASSED

Files verified to exist / contain expected content:
- skills/movie-experts/README.md — FOUND (7 prompt_injector mentions across inventory + DAG + corpus tree + footer + Status line)
- skills/movie-experts/_shared/glossary.md — FOUND (prompt_injector H3 entry under Phase 16 additions section)
- .planning/research/v2-pipeline-design/skills-mapping.yaml — FOUND (sign_off_status + signed_off_at + signed_off_by + FULFILLED action_for_v21)

Commits verified:
- 179030a4e (docs(16-02): README inventory + corpus tree + DAG diagram + footer for prompt_injector) — FOUND
- 11454d246 (docs(16-02): glossary entry + skills-mapping.yaml sign-off for prompt_injector) — FOUND
