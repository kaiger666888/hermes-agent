---
phase: 03-top-4-existing-experts-rag
plan: 01
subsystem: screenplay-expert
tags: [rag, screenplay, snyder, mckee, shortdrama, emotion-curve, dialogue, hook-09]
requires:
  - "Phase 0 screenplay baseline (eval/baseline/screenplay/SKILL.md)"
  - "Phase 2 hook_retention SKILL.md (HOOK-09 marker schema contract)"
  - "Phase 1 compliance_marketing refs (platform-specs cross-links)"
provides:
  - "5 curated screenplay refs (Snyder/McKee/CN shortdrama/academic/dialogue)"
  - "Deep-refactored screenplay SKILL.md with RAG block + emotion_curve schema extension"
  - "3 eval prompts for screenplay ablation (basic/trap/multi-episode)"
  - "HOOK-09 contract closure (emotion_curve.hooks/payoffs/cliffhangers arrays)"
affects:
  - "screenplay/SKILL.md (v1.0.0 → v1.1.0)"
  - "hook_retention collaboration edge (bidirectional marker consumption)"
  - "Phase 3 ablation eval (03-05): new-with-refs condition input ready"
tech-stack:
  added: []
  patterns:
    - "anchor-based emotion_curve sampling (supersedes uniform 0.5s)"
    - "genre-specific dialogue_density thresholds (revenge 0.4-0.6 / romance 0.5-0.7)"
    - "emotion_curve hooks/payoffs/cliffhangers arrays (HOOK-09 multi-episode callback)"
key-files:
  created:
    - "skills/movie-experts/screenplay/references/save-the-cat-beat-sheet.md (303 lines)"
    - "skills/movie-experts/screenplay/references/mckee-scene-design.md (301 lines)"
    - "skills/movie-experts/screenplay/references/cn-shortdrama-structure.md (303 lines)"
    - "skills/movie-experts/screenplay/references/emotion-curve-academic.md (302 lines)"
    - "skills/movie-experts/screenplay/references/dialogue-craft.md (300 lines)"
    - "skills/movie-experts/screenplay/references/LICENSE.md (38 lines)"
    - "skills/movie-experts/_eval/prompts/screenplay_demo.yaml (3 prompts)"
  modified:
    - "skills/movie-experts/screenplay/SKILL.md (v1.0.0 → v1.1.0)"
decisions:
  - "D1: 5 refs per source mix (Snyder/McKee/CN shortdrama/academic/CN dialogue) — matches CONTEXT D-1"
  - "D2: Knowledge Retrieval block placed between Role & Philosophy and Core Capabilities — matches CONTEXT D-2"
  - "D3: emotion_curve schema extended with hooks/payoffs/cliffhangers arrays — closes Phase 2 HOOK-09"
  - "D4: anchor-based sampling is primary; uniform 0.5s is documented fallback — supersedes Phase 0 uniform sampling"
  - "D5: dialogue_density changed from uniform 0.3-0.7 to genre-specific ranges (revenge 0.4-0.6 / romance 0.5-0.7)"
metrics:
  duration: "24min"
  completed: "2026-06-15T11:27:15Z"
  tasks: 2
  files: 8
---

# Phase 3 Plan 01: Screenplay Expert Deep-Refactor Summary

Deep-refactored the screenplay expert (highest-leverage existing expert) with 5 curated RAG refs spanning Snyder/McKee/CN shortdrama/academic-emotion/dialogue-craft, a provider-agnostic Knowledge Retrieval block, genre-specific threshold revisions, anchor-based emotion_curve sampling, and the Phase 2 HOOK-09 emotion_curve schema extension (hooks/payoffs/cliffhangers arrays with multi-episode callback support).

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Author 5 screenplay refs + LICENSE | `32c733b93` | references/{save-the-cat,mckee,cn-shortdrama,emotion-curve,dialogue-craft}.md + LICENSE.md |
| 2 | Deep-refactor SKILL.md + 3 eval prompts | `55abadf51` | screenplay/SKILL.md (v1.1.0) + _eval/prompts/screenplay_demo.yaml |

## Key Changes

### 5 Curated Refs (300-303 lines each)

1. **save-the-cat-beat-sheet.md** — Snyder 15-beat model adapted to 60s/90s/180s 短剧 formats with exact runtime targets (Catalyst ~9s for 90s, Midpoint ~45s, All Is Lost ~67s). Includes Save the Cat moment variants for 男频 (reverse Save the Cat) and 女频 (emotional anchor), plus the Double-Bump rule (All Is Lost + Dark Night must be consecutive).

2. **mckee-scene-design.md** — McKee's gap theory (4-step expectation-result parsing protocol), value-shift rule (≥ 1 per scene, zero-tolerance for filler), beat decomposition (3-5 beats per 90s scene with escalation pattern), and turning point vs plot point distinction (~25% and ~75% runtime).

3. **cn-shortdrama-structure.md** — CN 短剧 multi-episode structure: 90s/180s time budgets (钩子 0-3s / escalation 15-40s / 爽点 70-80s / 卡点 88-90s), 10-episode season arc (big 爽点 at ep 3/7/10), and per-platform divergence table (抖音 60-90s / 快手 60-120s / 小程序剧 120-180s with distinct cut density, paywall position, hook style).

4. **emotion-curve-academic.md** — Tan's interest formula (concern × uncertainty × anticipation ≥ 0.6), McMahon 6 emotional arc shapes (85% coverage; Man in a Hole preferred for 男频 revenge, Cinderella for 女频 romance), anchor-based sampling protocol (~30% SNR improvement vs uniform), and attention decay curve (drops ≥ 15% at 8-12s without 击中点).

5. **dialogue-craft.md** — Genre-specific dialogue density thresholds (revenge 0.4-0.6 / romance 0.5-0.7 / ≥ 0.8 = 旁白过度 anti-pattern), subtext ratio ≥ 60% rule, "as you know" CN anti-pattern 3-strike rule with 3 variants, per-platform register divergence (抖音 punchy / 快手 colloquial / 小程序剧 elevated), and dialogue economy by format.

### SKILL.md Deep-Refactor (v1.0.0 → v1.1.0)

- **Knowledge Retrieval block** — Provider-agnostic RAG invocation with 5 retrieval topics, placed between `## Role & Philosophy` and `## Core Capabilities` (CONTEXT D-2 load-bearing placement). Uses `<memory_plugin>` / `<rag_search>` placeholders, not hardcoded tool names.
- **References table populated** — All 5 ref filenames with "When to Read" triggers and "Contents" summaries (replaced Phase 0 placeholder).
- **emotion_curve schema extension (HOOK-09 closure)** — Added `hooks[]` / `payoffs[]` / `cliffhangers[]` arrays with full JSON schema. `payoffs[]` elements carry `setup_callback` for cross-episode callback (e.g., "S1E03 02:15 — ..."). `cliffhangers[]` elements carry `payoff_callback` for cross-episode forward-reference. Bidirectional collaboration edge with `hook_retention` documented.
- **Threshold revisions** — `dialogue_density` from uniform 0.3-0.7 to genre-specific (revenge 0.4-0.6 / romance 0.5-0.7). `scene_count` from 5-12 to format-specific (3-8 for 90s / 6-15 for 180s). `sampling_rate` from uniform 0.5s to anchor-based primary with uniform fallback.
- **Metrics operational definitions refined** — `narrative_tension`: McKee value-shift rate + Snyder Midpoint polarity. `dialogue_naturalness`: subtext ratio + "as you know" 3-strike + density. `emotional_arc`: Tan interest score + McMahon arc shape + anchor sampling. Metric IDs NOT renamed (FOUND-08 rule).
- **Provider-agnostic phrasing** — All model mentions converted to `<llm_primary>` / `<llm_fallback>` placeholders. No Claude/GPT-4o literals remain.

### 3 Eval Prompts (screenplay_demo.yaml)

- **sc-001 (basic):** 90s 抖音-男频 revenge S1E01 — full beat budget + scene decomposition + dialogue + emotion_curve with hooks/payoffs/cliffhangers. Tests Snyder + McKee + HOOK-09 integration.
- **sc-002 (trap):** Requests a 0-value-shift "filler" scene. Refactored expert should REFUSE citing McKee's rule + attention decay + beat budget. Tests ref absorption vs training default.
- **sc-003 (multi-episode):** S1E03 → S1E05 arc with cross-episode `setup_callback` / `payoff_callback` strings. Tests HOOK-09 multi-episode callback capability.

## Deviations from Plan

None — plan executed exactly as written. All must_haves truths satisfied, all artifacts created with required minimum line counts, all key_links established.

## Known Stubs

None — all thresholds cite specific ref §sections; no hardcoded empty values or placeholder data.

## Threat Flags

None — all threats from the plan's `<threat_model>` are mitigated as specified (T-03-01 through T-03-06). No new security-relevant surface introduced beyond what the threat model anticipated.

## TDD Gate Compliance

N/A — this plan is `type: execute` (not `type: tdd`). No RED/GREEN/REFACTOR gate sequence required.

## Self-Check: PASSED

### Files verified to exist:
- FOUND: skills/movie-experts/screenplay/references/save-the-cat-beat-sheet.md
- FOUND: skills/movie-experts/screenplay/references/mckee-scene-design.md
- FOUND: skills/movie-experts/screenplay/references/cn-shortdrama-structure.md
- FOUND: skills/movie-experts/screenplay/references/emotion-curve-academic.md
- FOUND: skills/movie-experts/screenplay/references/dialogue-craft.md
- FOUND: skills/movie-experts/screenplay/references/LICENSE.md
- FOUND: skills/movie-experts/screenplay/SKILL.md
- FOUND: skills/movie-experts/_eval/prompts/screenplay_demo.yaml

### Commits verified to exist:
- FOUND: 32c733b93 (feat(03-01): author 5 screenplay refs + LICENSE)
- FOUND: 55abadf51 (feat(03-01): deep-refactor screenplay SKILL.md + 3 eval prompts)

### Verification results:
- Task 1 automated verify: PASS (5 refs 300-303 lines each, all anatomy sections present, glossary cross-linked, LICENSE.md Fair Use)
- Task 2 automated verify: PASS (expert_id preserved, Knowledge Retrieval positioned correctly, emotion_curve schema extension present, all 5 refs cross-linked, provider-agnostic tokens, version 1.1.0, 3 eval prompts)
- runner.py --dry-run: PASS (3 prompts loaded, 3 verdicts produced in 2 conditions)
- verify_skill_references.py scanner: PASS (0 phantom references, exit 0)
