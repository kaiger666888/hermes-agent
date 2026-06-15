# LICENSE — mixer references

**Owner:** Phase 5 plan `05` (single owner — EXPERT-mixer RAG uplift).
**Last updated:** 2026-06-15
verified_date: 2026-06

## Scope

This directory (`skills/movie-experts/cinematographer/references/`) contains 4 curated reference files that form the cinematographer expert's RAG corpus. Each ref paraphrases concrete heuristics (numbers, rules, thresholds) drawn from the source listed below. **No ref reproduces copyrighted scene description, dialogue, storyboards, or continuous prose beyond the Fair Use quota (quoted heuristics only; ≤ 5 specific prompt-token examples per video gen model; no film-still reproduction).**

The corpus is authored under **Fair Use** (17 U.S.C. § 107) and the corresponding Chinese 著作权法 第二十四条 合理使用 provision: the material is used for commentary, criticism, and scholarly analysis of craft technique, not for reproduction of protected expression.

## Per-ref attribution

| Ref | Source | Copyright status |
|-----|--------|------------------|
| `shot-grammar.md` | Bordwell & Thompson *Film Art: An Introduction* (11th ed, 2020, McGraw-Hill) + Arijon *Grammar of the Film Language* (1976, Silman-James Press) + Mascelli *The Five C's of Cinematography* (1965, Silman-James) + CN 平台 公开 shot-distribution 统计 (2024-2026) + Cinemetrics public ASL database | Fair Use — paraphrased 8-level shot scale taxonomy + composition rules + shot-scale × emotion mapping only; no reproduction of textbook shot diagrams or scene analyses |
| `axis-rules.md` | Arijon *Grammar of the Film Language* (1976) + Mascelli *The Five C's of Cinematography* (1965) + Bordwell & Thompson *Film Art* (11th ed, 2020) + Reisz & Millar *The Technique of Film Editing* (2nd ed, 1968) + Dmytryk *On Film Editing* (1984) | Fair Use — paraphrased 180° axis rule + 30° rule + screen direction continuity + reverse-cut protocol only; no reproduction of textbook diagrams or scene walkthroughs |
| `vertical-screen-framing.md` | CN 平台 公开 framing 统计 (抖音 / 快手 / 小程序剧 / 视频号 2024-2026 user behavior studies) + TikTok Creator Academy public guides + YouTube Shorts Creator Academy + Instagram Reels Creative Guidelines + Bordwell & Thompson *Film Art* (11th ed, 2020) for general framing principles | Fair Use — paraphrased 9:16 power point corrections + headroom standards + subtitle safe area zones + per-platform divergence only; no reproduction of platform-internal documentation or proprietary creator playbooks |
| `camera-motion-catalog.md` | Runway Gen-3 Alpha official documentation (runwayml.com, accessed 2026-06) + Kling AI 1.6 prompt engineering guide (klingai.com, 2026-06) + Google DeepMind Veo 2 technical report + prompt guide (2026-06) + OpenAI Sora 2 system card + community guides (2026-06) + Arijon (1976) + Mascelli (1965) + Hurbache *The Camera* (1987, 3rd ed) | Fair Use — paraphrased 12 camera move taxonomy + model-specific prompt-token mappings from public documentation only; no proprietary model weights / internals / API verbatim; ≤5 prompt-token examples per model |

## Fair Use four-factor analysis (applied to the textbook + model documentation refs)

1. **Purpose and character of use:** Transformative — camera move heuristics are extracted as craft rules (numbers / thresholds / prompt-token mappings) and applied to AI 短剧 / 微电影 production, not reproduced for the original instructional market.
2. **Nature of the copyrighted work:** Published craft textbooks (factual / instructional leaning) + public technical documentation (factual). Model documentation is public-facing API documentation (factual).
3. **Amount and substantiality:** Only paraphrased rules and prompt-token examples are used; for textbook refs ≤ 5 specific heuristics per book; for model refs ≤ 5 prompt-token examples per model; no scene image reproduction, no storyboard reproduction, no proprietary API verbatim.
4. **Effect upon the potential market:** None — this corpus targets the AI 短剧 production market, not the cinematography-instruction or video-gen-model-API market served by the original textbooks and model providers.

## Refresh obligation

Every ref carries `Last-verified` stamp per [`../_shared/SKILL-LAYOUT.md`](../_shared/SKILL-LAYOUT.md) reference anatomy. Stale refs (Last-verified > 90 days) are flagged by `scripts/verify_skill_references.py`. Quarterly re-verification is the owner's responsibility.

**Model-specific refs (`camera-motion-catalog.md`) are HIGH-DRIFT-RISK:** Runway / Kling / Veo / Sora versions change quarterly; prompt-token mappings must be re-verified against current model documentation each quarter. The `verified_date: 2026-06` stamp is load-bearing.

**Platform-specific refs (`vertical-screen-framing.md`):** platform algorithms change quarterly; re-verify the per-platform divergence (subtitle zone / framing preference / 字号) against current platform 公开运营报告 each quarter.

## Cross-references

- [`../_shared/SKILL-LAYOUT.md`](../_shared/SKILL-LAYOUT.md) — reference anatomy spec
- [`../_shared/glossary.md`](../_shared/glossary.md) — EN↔CN term dictionary (refs hyperlink rather than duplicate)
- [`../scene_builder/SKILL.md`](../scene_builder/SKILL.md) — feasibility handoff (cinematographer intent → scene_builder validates spatial constraints)
- [`../animator/SKILL.md`](../animator/SKILL.md) — execution handoff (cinematographer camera-move intent → animator translates to model-specific prompt tokens)
- [`../editor/SKILL.md`](../editor/SKILL.md) — compliance handoff (cinematographer axis + screen-direction markers → editor verifies cross-cut continuity)
