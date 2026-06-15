# LICENSE — editor references

**Owner:** Phase 3 plan `03-02` (single owner — no parallel plan touches this file).
**Last updated:** 2026-06-15
verified_date: 2026-06

## Scope

This directory (`skills/movie-experts/editor/references/`) contains 5 curated reference files that form the editor expert's RAG corpus. Each ref paraphrases concrete heuristics (numbers, rules, thresholds) drawn from the source listed below. **No ref reproduces copyrighted scene description, dialogue, or continuous prose beyond the Fair Use quota (quoted heuristics only; ≤ 90 seconds of any scene description).**

The corpus is authored under **Fair Use** (17 U.S.C. § 107) and the corresponding Chinese 著作权法 第二十四条 合理使用 provision: the material is used for commentary, criticism, and scholarly analysis of craft technique, not for reproduction of protected expression.

## Per-ref attribution

| Ref | Source | Copyright status |
|-----|--------|------------------|
| `murch-rule-of-six.md` | *In the Blink of an Eye: A Perspective on Film Editing* (Walter Murch, 2nd ed 2001, Silman-James Press) | Fair Use — paraphrased Rule of Six weightings (Emotion 50% / Story 23% / Rhythm 10% / Eye-trace 7% / 2D plane 5% / 3D space 3%) + Emotion-First decision rule + blink-rhythm theory only; no reproduction of Murch's scene-walkthroughs or extended prose |
| `classical-editing-rhythm.md` | *The Technique of Film Editing* (Karel Reisz & Gavin Millar, 2nd ed 1968, Focal Press / original 1953) | Fair Use — paraphrased cut-density windows by genre + build-to-climax rule + cut-on-action principle + invisible-editing definition only; no reproduction of Reisz-Millar scene-analysis case studies |
| `montage-theory.md` | *Film Form: Essays in Film Theory* (Sergei Eisenstein, 1949, Harcourt; Jay Leyda ed./transl.) + academic explication literature | Fair Use — paraphrased 5 montage methods (Metric / Rhythmic / Tonal / Overtonal / Intellectual) + collision principle definitions only; no reproduction of extended Eisenstein prose or shot-list tables |
| `fxrxt-axis-compliance.md` | Classical film theory (180° / 30° rules) + Hermes-existing FxRxT convention (MIT-licensed Hermes Agent repo) | Mixed — classical rules are public domain (industry craft convention > 100 years old); FxRxT matrix terminology is Hermes-internal (MIT, see top-level LICENSE) |
| `cn-cutting-rhythm.md` | 公开 短剧 创作指南 + 创作者公开访谈 + 平台 公开运营报告(MCN 公开数据 aggregated) | Fair Use — aggregated observation only; no reproduction of copyrighted scripts, editing templates, or proprietary creator-playbook material |

## Fair Use four-factor analysis (applied to the textbook refs)

1. **Purpose and character of use:** Transformative — heuristics are extracted as craft rules (numbers / thresholds / structural definitions) and applied to AI 短剧 / 微电影 production, not reproduced for the original instructional market.
2. **Nature of the copyrighted work:** Published craft textbooks (factual / instructional leaning, with creative scene-walkthrough elements which are NOT reproduced here).
3. **Amount and substantiality:** Only paraphrased rules and numerical heuristics are used; no scene description > 90 seconds, no dialogue reproduced, no loglines reproduced.
4. **Effect upon the potential market:** None — this corpus targets the AI 短剧 production market, not the film-editing-instruction market served by the original textbooks.

## Refresh obligation

Every ref carries `## Refresh Cadence` and `## Drift Signals` sections per [`../_shared/SKILL-LAYOUT.md`](../_shared/SKILL-LAYOUT.md) reference anatomy. Stale refs (Last-verified > 90 days) are flagged by `scripts/verify_skill_references.py`. Quarterly re-verification is the owner's responsibility.

## Cross-references

- [`../_shared/SKILL-LAYOUT.md`](../_shared/SKILL-LAYOUT.md) — reference anatomy spec (Source / Copyright / Last-verified / Summary / Heuristics columns)
- [`../_shared/glossary.md`](../_shared/glossary.md) — EN↔CN term dictionary (refs hyperlink rather than duplicate)
- [`../../_eval/baseline/editor/SKILL.md`](../../_eval/baseline/editor/SKILL.md) — Phase 0 baseline snapshot (old-no-refs condition for ablation; do NOT modify)
- [`../hook_retention/references/vertical-pacing.md`](../hook_retention/references/vertical-pacing.md) — Phase 2 canonical source for 1.5x pace rule + ≤3s dead air rule (cn-cutting-rhythm.md cross-links rather than redefines)
