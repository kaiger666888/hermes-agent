# LICENSE — colorist references

**Owner:** Phase 3 plan `03-03` (single owner — no parallel plan touches this file).
**Last updated:** 2026-06-15
verified_date: 2026-06

## Scope

This directory (`skills/movie-experts/colorist/references/`) contains 5 curated reference files that form the colorist expert's RAG corpus. Each ref paraphrases concrete heuristics (numbers, rules, thresholds) drawn from the source listed below. **No ref reproduces copyrighted scene description, dialogue, or continuous prose beyond the Fair Use quota (quoted heuristics only; ≤ 5 specific LUT values per textbook; no scene image reproduction).**

The corpus is authored under **Fair Use** (17 U.S.C. § 107) and the corresponding Chinese 著作权法 第二十四条 合理使用 provision: the material is used for commentary, criticism, and scholarly analysis of craft technique, not for reproduction of protected expression.

## Per-ref attribution

| Ref | Source | Copyright status |
|-----|--------|------------------|
| `bellantoni-color-psychology.md` | *If It's Purple, Who's to Blame: The Symbolism and Meaning of Color in Film* (Patti Bellantoni, 2005, Michael Wiese Productions) | Fair Use — paraphrased 8-color vocabulary + prevalence percentages (purple ~60% of villain scenes / red ~78% of passion scenes) + "color as character" doctrine + 6 director-film triplets only; no reproduction of Bellantoni's scene analyses or film-still descriptions |
| `hurkman-color-pipeline.md` | *Color Correction Look Book: Creative Grading Techniques for Film and Video* (Alexis Van Hurkman, 2011, Peachpit Press) | Fair Use — paraphrased lift/gamma/gain ranges (lift ±0.05 / gamma 0.8-1.2 / gain 0.8-1.2) + ACES pipeline transforms + LUT format comparison (33³/17³/65³ grids) + 4-step shot-matching protocol only; no reproduction of Hurkman's before/after frame walkthroughs or chapter-length tutorials |
| `color-cross-cultural.md` | Selected academic cross-cultural color-emotion literature: Madden, Hewett & Roth (2000); Mehta & Zhu (2009, *Science* 326:1226-1229); Hupka et al. (1997, *Cross-Cultural Research* 31:3) | Fair Use — paraphrased country × emotion percentages + Cohen's d effect sizes + 6-emotion × 4-culture matrix + experimental protocol descriptions only; no reproduction of paper abstracts or full statistical tables |
| `cn-audience-color.md` | 公开 短剧 创作指南 + 创作者公开访谈 + CN audience preference industry whitepapers + 平台公开运营报告(aggregated observation) | Fair Use — aggregated observation only; no reproduction of copyrighted 短剧 scripts, creator playbook templates, or proprietary MCN color-grading presets |
| `digital-color-science.md` | ITU-R BT.709 / BT.2020 / BT.2100 (HDR) standards + SMPTE ST 2084 (PQ EOTF) + CIE 1976 LAB specification (public standards, freely accessible from ITU + SMPTE + CIE) | Public standards — these are public international standards documents, not copyrighted creative content. Quoted values (Rec.709 red x=0.640 y=0.330; Rec.2020 red x=0.708 y=0.292; ΔE formulas; PQ EOTF constants) are factual technical specifications, freely re-distributable with attribution to the issuing body. |

## Fair Use four-factor analysis (applied to the textbook + academic refs)

1. **Purpose and character of use:** Transformative — heuristics are extracted as craft rules (numbers / thresholds / structural definitions) and applied to AI 短剧 / 微电影 production, not reproduced for the original instructional or academic market.
2. **Nature of the copyrighted work:** Published craft textbooks and peer-reviewed academic papers (factual / instructional leaning, with creative scene-walkthrough elements which are NOT reproduced here). Academic papers' statistical findings are factual data, not protected expression.
3. **Amount and substantiality:** Only paraphrased rules and numerical heuristics are used; for textbook refs ≤ 5 specific LUT values per book; for academic refs only summary effect sizes and percentages, not full statistical tables; no scene image reproduction, no dialogue reproduced, no loglines reproduced.
4. **Effect upon the potential market:** None — this corpus targets the AI 短剧 production market, not the color-grading-instruction or color-psychology-research market served by the original textbooks and academic journals.

## Refresh obligation

Every ref carries `## Refresh Cadence` and `## Drift Signals` sections per [`../_shared/SKILL-LAYOUT.md`](../_shared/SKILL-LAYOUT.md) reference anatomy. Stale refs (Last-verified > 90 days) are flagged by `scripts/verify_skill_references.py`. Quarterly re-verification is the owner's responsibility.

Platform-specific refs (especially `cn-audience-color.md` §Douyin Saturation Ceiling) are higher-drift-risk: platform algorithms change quarterly; re-verify the saturation ceiling + warmth-preference percentages against current platform 公开运营报告 each quarter.

## Cross-references

- [`../_shared/SKILL-LAYOUT.md`](../_shared/SKILL-LAYOUT.md) — reference anatomy spec (Source / Copyright / Last-verified / Summary / Heuristics columns)
- [`../_shared/glossary.md`](../_shared/glossary.md) — EN↔CN term dictionary (refs hyperlink rather than duplicate); [完播率](../_shared/glossary.md) / [男频](../_shared/glossary.md) / [女频](../_shared/glossary.md) / [钩子](../_shared/glossary.md) / [卡点](../_shared/glossary.md) / [爆款](../_shared/glossary.md) are hyperlinked at first occurrence
- [`../../_eval/baseline/colorist/SKILL.md`](../../_eval/baseline/colorist/SKILL.md) — Phase 0 baseline snapshot (old-no-refs condition for ablation; do NOT modify)
- [`../compliance_marketing/references/cn-content-rules.md`](../compliance_marketing/references/cn-content-rules.md) — Phase 1 canonical source for CN 内容红线 + red=festival-vs-violence regulatory context (cn-audience-color.md §Red Duality in CN cross-links rather than redefines the regulatory threshold)
- [`../style_genome/SKILL.md`](../style_genome/SKILL.md) — Phase 3 style_genome 5D style index §Color Tendency dimension (consumes colorist palette decisions; style_genome ↔ colorist coupling is intentional — T-03-17 accept)
