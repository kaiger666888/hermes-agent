---
plan: 04
phase: 04-expert-cine-camera-language
status: complete
requirements: [CINE-01, CINE-02, CINE-03, CINE-04, CINE-05, CINE-06, CINE-07, CINE-08, CINE-09]
expert: cinematographer
---

# Phase 4 EXPERT-CINE (Cinematographer) — Summary

## Objective

Build the cinematographer expert end-to-end so the suite has a unified 镜头语言 expression layer integrating with scene_builder (feasibility), animator (execution), and editor (180° axis compliance). Executed directly per `/goal` directive (skip strict GSD process).

## What Was Built

### Boundary documentation (BEFORE SKILL.md per ROADMAP SC #4)
- `.planning/phases/04-expert-cine-camera-language/04-CONTEXT.md` — Phase Boundary table documenting handoff between cinematographer (INTENT) vs scene_builder (FEASIBILITY) vs animator (EXECUTION) vs editor (COMPLIANCE)

### Refs authored (4 + LICENSE)
| Ref | Size | Source | Heuristic density |
|-----|------|--------|-------------------|
| `shot-grammar.md` | 12 KB | Bordwell & Thompson 2020 + Arijon 1976 + Mascelli 1965 + Cinemetrics + CN platform stats | 8-level shot scale + composition rules + 短剧 shot-scale distribution + OTS coverage |
| `axis-rules.md` | 11 KB | Arijon 1976 + Mascelli 1965 + Bordwell 2020 + Reisz & Millar 1968 + Dmytryk 1984 | 180° axis rule + 30° rule + screen direction + reverse cut + cross-cut protocol |
| `vertical-screen-framing.md` | 13 KB | CN platform framing stats + TikTok/YouTube Shorts/Reels Creator Academy + Bordwell 2020 | 9:16 power points + headroom + subtitle safe area + per-platform divergence (7 platforms) |
| `camera-motion-catalog.md` | 16 KB | Runway Gen-3 Alpha + Kling 1.6 + Veo 2 + Sora 2 official docs (2026-06) + Arijon + Mascelli + Hurbache 1987 | 12 camera moves + 2026-06 verified prompt-token mapping for 4 production-grade video gen models + dolly vs zoom distinction + Sora 2 multi-shot sequence |
| `LICENSE.md` | 5 KB | Fair Use attribution per Phase 0 convention | source + copyright + last-verified stamp per ref |

### SKILL.md authored
- Full bilingual SKILL.md with:
  - References table (5-ref corpus: 4 substantive + LICENSE)
  - Knowledge Retrieval block (provider-agnostic RAG invocation, 4 tag queries)
  - Handoff Boundaries table (INTENT / FEASIBILITY / EXECUTION / COMPLIANCE)
  - Style Rules (vertical framing rules / axis rules / camera move rules)
  - Quality Thresholds (6 metrics with source citations)
  - What NOT to do (10 anti-patterns)
  - Pipeline Position in production DAG

### Eval prompts authored (3)
| ID | Scenario | Tests |
|----|----------|-------|
| `cn-001` | basic | 90s 抖音-男频-revenge S1E01 shot list (6 anchor points × shot scale + composition + axis + camera move + 4-model prompt tokens) |
| `cn-002` | trap | Refuse horizontal rule-of-thirds in vertical 9:16 (vertical-screen-framing §Power Points 修正 + mobile viewing distance research) |
| `cn-003` | multi-model handoff | Design 3-shot sequence for 4 video gen models (Runway Gen-3 / Kling 1.6 / Veo 2 / Sora 2) — multi-shot sequence capability for Sora 2 |

### related_skills graph updates (7 peer experts)
Added `cinematographer` to the related_skills array of:
- screenplay, scene_builder, animator, editor, continuity, drawer, hook_retention

### Dry-run verification
- `cinematographer_phase3.{json,md}` — 9 verdicts (3 pairs × 3 prompts), all-tie stub signature confirms harness compatibility with new expert

## Key Decisions

**D-1: Camera-move prompt-token mapping scope** — Documented 4 production-grade 2026-06 models (Runway Gen-3 Alpha / Kling 1.6 / Veo 2 / Sora 2). Excluded Pika / MiniMax Hailuo / LTX Video / Haiper per adoption criteria.

**D-2: Bilingual format** — Same as Phase 3 (EN YAML structure + CN descriptive prose).

**D-3: expert_id and metrics** — `expert_id: cinematographer` (new expert, no backward-compat constraint); `metrics: [shot_intent_clarity, axis_compliance, vertical_framing_quality, motion_narrative_fit]`.

**D-4: Provider-agnostic RAG invocation** — Same Knowledge Retrieval block pattern as Phase 3 experts.

## Verification (ROADMAP Phase 4 SC #1-5)

- ✓ SC #1: `skills/movie-experts/cinematographer/SKILL.md` exists with bilingual content (EN YAML + CN prose)
- ✓ SC #2: 4 reference files exist (shot-grammar / axis-rules / vertical-screen-framing / camera-motion-catalog)
- ✓ SC #3: Camera-move → prompt-token mapping documented for 4 current video gen models (Runway Gen-3 Alpha / Kling 1.6 / Veo 2 / Sora 2) with `verified_date: 2026-06` stamp
- ✓ SC #4: Handoff boundary vs scene_builder/animator/editor documented in 04-CONTEXT.md BEFORE writing SKILL.md
- ✓ SC #5: Edges in related_skills graph to 7 relevant experts (screenplay, scene_builder, animator, editor, continuity, drawer, hook_retention) — bidirectional edges verified by grep across all 7 peer SKILL.md files

## Self-Check: PASSED

## Files Committed

- `.planning/phases/04-expert-cine-camera-language/04-CONTEXT.md` (boundary documentation)
- `.planning/phases/04-expert-cine-camera-language/04-SUMMARY.md` (this file)
- `skills/movie-experts/cinematographer/SKILL.md` (new)
- `skills/movie-experts/cinematographer/references/shot-grammar.md` (new)
- `skills/movie-experts/cinematographer/references/axis-rules.md` (new)
- `skills/movie-experts/cinematographer/references/vertical-screen-framing.md` (new)
- `skills/movie-experts/cinematographer/references/camera-motion-catalog.md` (new)
- `skills/movie-experts/cinematographer/references/LICENSE.md` (new)
- `skills/movie-experts/_eval/prompts/cinematographer_demo.yaml` (new)
- `skills/movie-experts/_eval/reports/cinematographer_phase3.{json,md}` (new, dry-run verification)
- `skills/movie-experts/screenplay/SKILL.md` (related_skills +cinematographer)
- `skills/movie-experts/scene_builder/SKILL.md` (related_skills +cinematographer)
- `skills/movie-experts/animator/SKILL.md` (related_skills +cinematographer)
- `skills/movie-experts/editor/SKILL.md` (related_skills +cinematographer)
- `skills/movie-experts/continuity/SKILL.md` (related_skills +cinematographer)
- `skills/movie-experts/drawer/SKILL.md` (related_skills +cinematographer)
- `skills/movie-experts/hook_retention/SKILL.md` (related_skills +cinematographer)
