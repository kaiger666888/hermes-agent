# LICENSE — screenplay references

**Owner:** Phase 3 plan `03-01` (single owner — no parallel plan touches this file).
**Last updated:** 2026-06-15
verified_date: 2026-06

## Scope

This directory (`skills/movie-experts/screenplay/references/`) contains 5 curated reference files that form the screenplay expert's RAG corpus. Each ref paraphrases concrete heuristics (numbers, rules, thresholds) drawn from the source listed below. **No ref reproduces copyrighted scene description, dialogue, or continuous prose beyond the Fair Use quota (quoted heuristics only, ≤ 90 seconds of any scene description).**

The corpus is authored under **Fair Use** (17 U.S.C. § 107) and the corresponding Chinese 著作权法 第二十四条 合理使用 provision: the material is used for commentary, criticism, and scholarly analysis of craft technique, not for reproduction of protected expression.

## Per-ref attribution

| Ref | Source | Copyright status |
|-----|--------|------------------|
| `save-the-cat-beat-sheet.md` | *Save the Cat!* (Blake Snyder, 2005, Studio City Productions) | Fair Use — paraphrased beat-sheet heuristics (page-count targets, "double bump" rule) only; no reproduction of Snyder's scene walkthroughs or example loglines |
| `mckee-scene-design.md` | *Story: Substance, Structure, Style, and the Principles of Screenwriting* (Robert McKee, 1997, Harper-Collins) | Fair Use — paraphrased scene-value-shift / gap / beat definitions only; no reproduction of McKee's scene-analysis case studies |
| `cn-shortdrama-structure.md` | 公开 短剧 创作指南 + 创作者公开访谈 + 行业 whitepapers (MCN 公开运营报告) aggregated | Fair Use — aggregated observation only; no reproduction of copyrighted scripts, paywall copy, or proprietary creator-playbook material |
| `emotion-curve-academic.md` | Selected academic film-emotion literature (Tan 1996 *Emotion and the Structure of Narrative Film* / Smith 1995 *Engaging Characters* / McMahon et al. 2016 emotional-arc clustering) | Fair Use — paraphrased model definitions + cited statistics only; no reproduction of extended prose, figures, or tables |
| `dialogue-craft.md` | 短剧 创作者 公开 创作经验 + modern CN screenplay craft books (公开) | Fair Use — aggregated observation only; no reproduction of copyrighted example dialogue beyond ≤ 90s fair-use fragments |

## Fair Use four-factor analysis (applied to the textbook refs)

1. **Purpose and character of use:** Transformative — heuristics are extracted as craft rules (numbers / thresholds / structural definitions) and applied to AI 短剧 / 微电影 production, not reproduced for the original instructional market.
2. **Nature of the copyrighted work:** Published craft textbooks (factual / instructional leaning, with creative scene-walkthrough elements which are NOT reproduced here).
3. **Amount and substantiality:** Only paraphrased rules and numerical heuristics are used; no scene description > 90 seconds, no dialogue reproduced beyond fair-use fragments, no loglines reproduced.
4. **Effect upon the potential market:** None — this corpus targets the AI 短剧 production market, not the screenwriting-instruction market served by the original textbooks.

## Refresh obligation

Every ref carries `## Refresh Cadence` and `## Drift Signals` sections per `_shared/SKILL-LAYOUT.md` reference anatomy. Stale refs (Last-verified > 90 days) are flagged by `scripts/verify_skill_references.py`. Quarterly re-verification is the owner's responsibility.

## Cross-references

- [`../_shared/SKILL-LAYOUT.md`](../_shared/SKILL-LAYOUT.md) — reference anatomy spec (Source / Copyright / Last-verified / Summary / Heuristics columns)
- [`../_shared/glossary.md`](../_shared/glossary.md) — EN↔CN term dictionary (refs hyperlink rather than duplicate)
- [`../../_eval/baseline/screenplay/SKILL.md`](../../_eval/baseline/screenplay/SKILL.md) — Phase 0 baseline snapshot (old-no-refs condition for ablation; do NOT modify)
