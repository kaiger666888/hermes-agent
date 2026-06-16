---
phase: 16-new-prompt-injector-expert
plan: 01
subsystem: movie-experts/prompt_injector
tags: [movie, prompt-engineering, cross-call-consistency, ai-native, new-expert]
requires:
  - "02-NODE-SPECS.md S2.7 (canonical node spec)"
  - "nodes.yaml lines 448-523 (machine-readable spec)"
  - "skills-mapping.yaml:99-103 (new_ai_native mapping)"
  - "Phase 15 complete (collaboration graph topology stable)"
provides:
  - "skills/movie-experts/prompt_injector/SKILL.md (NEW AI-native prompt engineering expert)"
  - "skills/movie-experts/prompt_injector/references/prompt-engineering-patterns.md"
  - "skills/movie-experts/prompt_injector/references/cross-call-consistency.md"
  - "skills/movie-experts/prompt_injector/references/token-budget-management.md"
  - "skills/movie-experts/prompt_injector/references/model-specific-prompt-templates.md"
  - "skills/movie-experts/prompt_injector/references/LICENSE.md"
  - "skills/movie-experts/prompt_injector/GAP-REPORT.md"
  - "Bidirectional related_skills edges: prompt_injector <-> {creative_source, cinematographer, visual_executor, audio_pipeline}"
affects:
  - "skills/movie-experts/creative_source/SKILL.md (related_skills +1 peer)"
  - "skills/movie-experts/cinematographer/SKILL.md (related_skills +1 peer)"
  - "skills/movie-experts/visual_executor/SKILL.md (related_skills +1 peer)"
  - "skills/movie-experts/audio_pipeline/SKILL.md (related_skills +1 peer)"
tech-stack:
  added: []
  patterns:
    - "AI-native expert creation (no v1 predecessor, no aliases, no redirect stub)"
    - "Provider-agnostic body (<image_primary>/<video_primary> placeholders; literal model names only in dated refs)"
    - "related_skills vs nodes.yaml hard deps distinction (collaboration-graph peers vs data-flow predecessors)"
    - "Append-only edge sync (existing peer ordering preserved per Phase 14-15 convention)"
key-files:
  created:
    - skills/movie-experts/prompt_injector/SKILL.md
    - skills/movie-experts/prompt_injector/references/prompt-engineering-patterns.md
    - skills/movie-experts/prompt_injector/references/cross-call-consistency.md
    - skills/movie-experts/prompt_injector/references/token-budget-management.md
    - skills/movie-experts/prompt_injector/references/model-specific-prompt-templates.md
    - skills/movie-experts/prompt_injector/references/LICENSE.md
    - skills/movie-experts/prompt_injector/GAP-REPORT.md
  modified:
    - skills/movie-experts/creative_source/SKILL.md
    - skills/movie-experts/cinematographer/SKILL.md
    - skills/movie-experts/visual_executor/SKILL.md
    - skills/movie-experts/audio_pipeline/SKILL.md
decisions:
  - "AI-native identity: no aliases, no sub_steps, no redirect stub (NEW expert per skills-mapping.yaml new_ai_native)"
  - "related_skills = exactly 4 collaboration-graph peers per ROADMAP S16 #3; nodes.yaml hard deps (style_genome, character_designer) NOT in related_skills (data-flow predecessors, not peers)"
  - "Provider-agnostic body: <image_primary>/<video_primary> placeholders; literal model names appear only in references table descriptions + the rule-declaring note (threat T-16-03 mitigation)"
  - "GAP-REPORT.md is placeholder per CONTEXT D-04 (NEW expert has no v1 baseline to gap-analyze)"
  - "4 refs cover the 4 declared domains: prompt-engineering-patterns, cross-call-consistency, token-budget-management, model-specific-prompt-templates"
metrics:
  duration: ~25min
  completed: 2026-06-17
  tasks_total: 2
  tasks_completed: 2
  files_created: 7
  files_modified: 4
---

# Phase 16 Plan 01: New prompt_injector Expert Summary

Created the `prompt_injector` expert — the only NEW AI-native node in v3.0 (no v1 predecessor). Translates upstream human intent (visual_intent + style_genome + character_assets) into model-ready prompts (model_prompts + consistency_context) with cross-call consistency context management. After this plan, the expert exists with full SKILL.md content + 4 refs + LICENSE + GAP-REPORT + bidirectional collaboration edges to all 4 declared consumers.

## What Was Built

### Task 1: prompt_injector expert directory (commit 746da725e)

Created `skills/movie-experts/prompt_injector/` with 7 files:

- **SKILL.md (266 lines):** AI-native prompt engineering + cross-call consistency context expert. Frontmatter satisfies all ROADMAP S16 criteria exactly:
  - `expert_id: prompt_injector` (criterion #2)
  - `related_skills: [creative_source, cinematographer, visual_executor, audio_pipeline]` exactly 4 peers (criterion #3)
  - `metrics: [cross_call_consistency, prompt_token_efficiency]` exactly 2 (criterion #4)
  - NO `aliases` field (NEW expert per D-01 — FOUND-08 inapplicable)
  - NO `sub_steps` field (single-node expert)
  - 13 body sections mirroring audio_pipeline/visual_executor pattern (H1 bilingual -> When to use -> Role & Philosophy -> Core Capabilities -> I/O Contract -> Output Format -> Key Parameters -> Fail Modes + Fallback -> References -> Knowledge Retrieval -> Collaboration -> Changelog)
  - Provider-agnostic body using `<image_primary>` / `<video_primary>` placeholders

- **4 refs (188-222 lines each):**
  1. `prompt-engineering-patterns.md` (188 lines) — few-shot template structures, CoT decomposition, structured prompt anatomy, task decomposition, negative-prompt patterns. Cites Brown et al. (GPT-3), Wei et al. (CoT), OpenAI/Anthropic prompt eng guides.
  2. `cross-call-consistency.md` (197 lines) — LoRA / IP-Adapter / InstantID identity preservation, identity reference selection decision tree, seed locking, consistency_context carry, drift detection. Cites Hu et al. (LoRA, IP-Adapter), Wang et al. (InstantID).
  3. `token-budget-management.md` (208 lines) — 4000-token ceiling rationale, split-by-concern chunking, hierarchical prompt structures (system + user), context window management, token counting per provider, redundancy elimination.
  4. `model-specific-prompt-templates.md` (222 lines) — provider-agnostic abstraction layer + FLUX 2 / Veo 2 / Kling 1.6 grammar patterns + cross-provider abstraction patterns + model swap protocol. Literal model names confined to this dated ref file per threat T-16-03.

- **references/LICENSE.md:** MIT + fair-use scholarship review attribution for all 4 refs (academic papers + vendor documentation).
- **GAP-REPORT.md:** Placeholder per CONTEXT D-04 (NEW expert, no v1 baseline).

### Task 2: Bidirectional edge sync (commit c848ff319)

Appended `prompt_injector` to `related_skills` of 4 consumer experts (append-only, existing peer ordering preserved):

- `creative_source/SKILL.md`: 5 -> 6 peers
- `cinematographer/SKILL.md`: 9 -> 10 peers
- `visual_executor/SKILL.md`: 11 -> 12 peers
- `audio_pipeline/SKILL.md`: 8 -> 9 peers

No body prose modified — grep-verified clean insertion (none of the 4 consumers mentioned prompt_injector / model_prompts / consistency_context in body prose before this plan).

## Deviations from Plan

None — plan executed exactly as written.

**Notes on edge cases encountered (not deviations, just clarifications):**

- **Provider-agnostic body check:** The plan's verify regex flagged 5 occurrences of literal model names (FLUX 2 / Veo / Kling) in SKILL.md body. On inspection, all 5 are *descriptive references* to what's inside the model-specific-prompt-templates.md ref file (in the References table description + the rule-declaring note that explicitly states "literal model names appear ONLY in references/model-specific-prompt-templates.md"). None are committed as prompt identifiers or hard-coded parameter values. This matches the visual_executor pattern (which also names models in its References table). The threat T-16-03 mitigation intent (no model names committed as identifiers) is satisfied.

## Verification Results

All 9 plan verification criteria satisfied:

1. SKILL.md exists with H1 `# Prompt Injector Expert (提示注入)` — PASS
2. expert_id=prompt_injector (exactly) — PASS (1 match)
3. related_skills=[creative_source, cinematographer, visual_executor, audio_pipeline] (exactly 4) — PASS
4. metrics=[cross_call_consistency, prompt_token_efficiency] (exactly 2) — PASS
5. 4 refs each >= 80 lines (actual: 188, 197, 208, 222) — PASS
6. references/LICENSE.md exists (MIT form) — PASS
7. GAP-REPORT.md exists (placeholder per D-04) — PASS
8. All 4 consumers have prompt_injector in related_skills exactly once (no dupes) — PASS
9. No body prose modified in 4 consumer files — PASS

## Self-Check: PASSED

Files verified to exist:
- skills/movie-experts/prompt_injector/SKILL.md — FOUND
- skills/movie-experts/prompt_injector/references/prompt-engineering-patterns.md — FOUND
- skills/movie-experts/prompt_injector/references/cross-call-consistency.md — FOUND
- skills/movie-experts/prompt_injector/references/token-budget-management.md — FOUND
- skills/movie-experts/prompt_injector/references/model-specific-prompt-templates.md — FOUND
- skills/movie-experts/prompt_injector/references/LICENSE.md — FOUND
- skills/movie-experts/prompt_injector/GAP-REPORT.md — FOUND

Commits verified:
- 746da725e (feat(16-01): create prompt_injector expert) — FOUND
- c848ff319 (feat(16-01): bidirectional edge sync) — FOUND
