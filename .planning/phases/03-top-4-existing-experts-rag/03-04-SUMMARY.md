---
plan: 03-04
phase: 03-top-4-existing-experts-rag
status: complete
requirements: [REFACTOR-04, REFACTOR-08]
expert: style_genome
---

# 03-04 Style Genome RAG — Summary

## Objective

Deep-refactor the style_genome expert — the fourth of four top-priority existing experts — with 5 curated RAG refs (director DNA archive expanded to 35 entries / genre DNA taxonomy / academic cross-cultural / auteur theory / CN director analysis), a provider-agnostic RAG block, revised 5D thresholds, operationalized blending protocol (single-culture 0.7/0.3 vs cross-culture 0.65/0.35), refined metrics, and 3 eval prompts.

## What Was Built

### Refs authored (5 + LICENSE)
| Ref | Size | Source | Heuristic density |
|-----|------|--------|-------------------|
| `director-dna-archive.md` | 25 KB | Bordwell 2020 + Sarris 1968 + Wood 1965 + Cinemetrics | 35 director 5D vectors + signature elements + focal length + ASL + 3-tier classification |
| `genre-dna-taxonomy.md` | 22 KB | 12-genre taxonomy incl. 短剧-男频-revenge + 短剧-女频-romance | 5D ranges per genre + signature shot patterns + genre-locked metric thresholds |
| `auteur-theory.md` | 13 KB | Sarris 1968 *American Cinema* + Wood 1965 + Truffaut 1954 + Bordwell 2020 | Sarris 3-criteria rubric + tier decision tree + Style Coherence Doctrine |
| `cross-cultural-style.md` | 17 KB | Bordwell 2011 *Planet Hong Kong* + Chow 2007 + Marchetti 2007 + Hwang & Kim 2018 | CN/Western/Korean 5D divergence + CTC formula + Hybrid Encoding Protocol + Non-translatable elements + Hallyu 中介 |
| `cn-director-analysis.md` | 18 KB | Chow 2007 + Zhang 2004 + Bordwell 2011 + Cinemetrics + CN 平台 公开访谈 (2024-2026) | CN generation tiering + 5 canonical CN director 5D profile + signature elements + 短剧 director tiering |
| `LICENSE.md` | 6 KB | Fair Use attribution per Phase 0 convention | source + copyright + last-verified stamp per ref |

### SKILL.md refactor
- Replaced `## References` placeholder with full 5-ref table (When to Read + Contents columns)
- Added `## Knowledge Retrieval` block (provider-agnostic RAG invocation pattern, 5 tag queries)
- Added `Tier` column to showcase Director Archive table (Pantheon / Modern Auteur + interior_meaning tag)
- Extended `## Style Blending Protocol` to distinguish single-culture (0.7/0.3) vs cross-culture hybrid (0.65/0.35) — sourced from `cross-cultural-style.md` §Hybrid Encoding Protocol

### Eval prompts authored (3)
| ID | Scenario | Tests |
|----|----------|-------|
| `sg-001` | basic | Wong Kar-wai × action-thriller 0.7/0.3 blend + downstream signal distribution (drawer/colorist/editor/composer/etc.) + deviation report |
| `sg-002` | trap | Refuse 50/50 Nolan × Wes Anderson blend (style incoherence + Wood Style Coherence Doctrine) |
| `sg-003` | tier | Encode 李明 (short_drama director, 1/3 Sarris criteria) → Operator Convention tier + dual-track encoding for 出海 distribution |

## Key Deviations

**Salvage from interrupted executor:** 2 of 5 refs (director-dna-archive, genre-dna-taxonomy) were authored by an interrupted executor agent (03-04 style_genome RAG) that stalled on a min_lines-padding loop. These 2 refs were preserved (47 KB total). The remaining 3 refs (auteur-theory, cross-cultural-style, cn-director-analysis) + the SKILL.md refactor + eval prompts + this SUMMARY were authored directly by the orchestrator per the `/goal` directive (skip strict GSD process).

**Cross-culture hybrid protocol extension:** The original SKILL.md only specified 0.7/0.3 single-culture blend. Refactor extends this to dual-track: single-culture (0.7/0.3 per director-dna-archive.md §Style Blending Heuristics) + cross-culture hybrid (0.65/0.35 per cross-cultural-style.md §Hybrid Encoding Protocol). The dual formula addresses a previously-unhandled 短剧 出海 use case.

**Showcase 5D backward compatibility:** The 5 showcase director vectors (Wong Kar-wai / Nolan / Villeneuve / Fincher / Miyazaki) in SKILL.md match `director-dna-archive.md` §Showcase row-for-row. T-03-18 mitigation (向后兼容硬约束) verified.

## Verification

- ✓ `skills/movie-experts/style_genome/references/` contains 5 refs + LICENSE
- ✓ `skills/movie-experts/style_genome/SKILL.md` has `## References` table + `## Knowledge Retrieval` block + Tier column in showcase table + dual blend protocol
- ✓ `skills/movie-experts/_eval/prompts/style_genome_demo.yaml` exists with 3 prompts (sg-001/002/003)
- ✓ Frozen `expert_id: style_genome` preserved (backward-compat HARD RULE)
- ✓ Frozen metrics: `style_consistency` / `gene_extraction_accuracy` / `blend_coherence` / `cross_module_alignment` (IDs unchanged; operational definitions refined)
- ✓ Frozen showcase 5D vectors: Wong Kar-wai [0.7,0.8,0.4,0.3,0.7] / Nolan [0.4,0.5,0.6,0.7,0.8] / Villeneuve [0.3,0.6,0.3,0.6,0.6] / Fincher [0.4,0.3,0.5,0.5,0.7] / Miyazaki [0.5,0.7,0.3,0.2,0.8] — all match across SKILL.md and director-dna-archive.md
- ✓ All refs have `Last-verified: 2026-06-15` stamp + fair-use LICENSE attribution

## Self-Check: PASSED

## Files Committed

- `skills/movie-experts/style_genome/references/director-dna-archive.md` (new, salvaged)
- `skills/movie-experts/style_genome/references/genre-dna-taxonomy.md` (new, salvaged)
- `skills/movie-experts/style_genome/references/auteur-theory.md` (new)
- `skills/movie-experts/style_genome/references/cross-cultural-style.md` (new)
- `skills/movie-experts/style_genome/references/cn-director-analysis.md` (new)
- `skills/movie-experts/style_genome/references/LICENSE.md` (new, salvaged)
- `skills/movie-experts/style_genome/SKILL.md` (refactored)
- `skills/movie-experts/_eval/prompts/style_genome_demo.yaml` (new)
