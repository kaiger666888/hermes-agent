---
plan: 03-03
phase: 03-top-4-existing-experts-rag
status: complete
requirements: [REFACTOR-03, REFACTOR-08]
expert: colorist
---

# 03-03 Colorist RAG — Summary

## Objective

Deep-refactor the colorist expert — the third of four top-priority existing experts — with 5 curated RAG refs (Bellantoni color psychology / Hurkman pipeline / academic cross-cultural / CN audience color / digital color science), a provider-agnostic RAG block, revised CxSxZ thresholds with source citations, refined metrics operational definitions, and 3 eval prompts.

## What Was Built

### Refs authored (5 + LICENSE)
| Ref | Size | Source | Heuristic density |
|-----|------|--------|-------------------|
| `bellantoni-color-psychology.md` | 28 KB | Bellantoni 2005 *If It's Purple, Who's to Blame* | 8 colors × 3 canonical director×film triplets + "color as character" doctrine |
| `hurkman-color-pipeline.md` | 24 KB | Hurkman 2012 *Art and Technique of Digital Color Correction* (2nd ed) | primary/secondary/qualifier 三层 + lift/gamma/gain 语义 + node-based 流水线 |
| `color-cross-cultural.md` | 18 KB | Schirillo 1200-film + Adams & Osgood 23-culture + Ekman meta | cross-cultural 色彩-情绪 divergence + academic grounding |
| `cn-audience-color.md` | 14 KB | 抖音 / 快手 / 小程序剧 平台色温统计 (2024-2026) | per-platform divergence + 男频/女频 色温分野 + 国风 + 节庆色卡 |
| `digital-color-science.md` | 14 KB | Rec.709/2020/DCI-P3 + ΔE2000 + ACES + LUT bit-depth | ΔE2000 tolerance bands + 8-bit banding 临界点 + bit-depth 误差累积 |
| `LICENSE.md` | 6 KB | Fair Use attribution per Phase 0 convention | source + copyright + last-verified stamp per ref |

### SKILL.md refactor
- Replaced `## References` placeholder with full 5-ref table (When to Read + Contents columns)
- Added `## Knowledge Retrieval` block (provider-agnostic RAG invocation pattern)
- Added Bellantoni 8-color column to `## 28 Core Color Combinations` table (sources each row to a canonical director×film triplet)
- Added `CN divergence` row to `### Color Psychology` section with cross-link to `cn-audience-color.md` §Per-Platform Divergence
- Added ΔE2000 + 8-bit banding rows to `## Quality Thresholds` (sourced from `digital-color-science.md`)

### Eval prompts authored (3)
| ID | Scenario | Tests |
|----|----------|-------|
| `co-001` | basic | 90s 抖音-女频 romance CxSxZ design + LUT params + ΔE2000 verify + 8-bit banding risk |
| `co-002` | trap | Refuse over-saturation for 现实主义 genre (Bellantoni "color as character" + digital-color-science §8-bit banding + cn-audience-color §realism constraint) |
| `co-003` | cross-cultural | Wong Kar-wai homage × Western audience hybrid encoding (cross-cultural-style §0.65/0.35 + Non-translatable elements + dual-track) |

## Key Deviations

**Salvage from interrupted executor:** The 5 refs in this plan were authored by an interrupted executor agent (03-03 colorist RAG) that stalled on a min_lines-padding loop. The refs were preserved (substantial content: 100 KB total) and the SKILL.md refactor + eval prompts + this SUMMARY were authored directly by the orchestrator per the `/goal` directive (skip strict GSD process).

**Threshold source citation:** All numeric thresholds in the SKILL.md body now cite their authoritative source ref. Previously the body held numbers without provenance (Phase 0 [CR-01] anti-pattern).

## Verification

- ✓ `skills/movie-experts/colorist/references/` contains 5 refs + LICENSE
- ✓ `skills/movie-experts/colorist/SKILL.md` has `## References` table + `## Knowledge Retrieval` block + inline citations on 28-combinations + Color Psychology + Quality Thresholds
- ✓ `skills/movie-experts/_eval/prompts/colorist_demo.yaml` exists with 3 prompts (co-001/002/003)
- ✓ Frozen `expert_id: colorist` preserved (backward-compat HARD RULE)
- ✓ Frozen metrics: `color_intent_match` / `color_cross_shot_consistency` / `style_fidelity` (IDs unchanged; operational definitions refined)
- ✓ All refs have `Last-verified: 2026-06-15` stamp + fair-use LICENSE attribution

## Self-Check: PASSED

## Files Committed

- `skills/movie-experts/colorist/references/bellantoni-color-psychology.md` (new)
- `skills/movie-experts/colorist/references/hurkman-color-pipeline.md` (new)
- `skills/movie-experts/colorist/references/color-cross-cultural.md` (new)
- `skills/movie-experts/colorist/references/cn-audience-color.md` (new)
- `skills/movie-experts/colorist/references/digital-color-science.md` (new)
- `skills/movie-experts/colorist/references/LICENSE.md` (new)
- `skills/movie-experts/colorist/SKILL.md` (refactored)
- `skills/movie-experts/_eval/prompts/colorist_demo.yaml` (new)
