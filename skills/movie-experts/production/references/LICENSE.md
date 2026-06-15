# LICENSE — production references

**Owner:** Phase 5 plan `05` (single owner — EXPERT-PROD / production expert).
**Last updated:** 2026-06-15
verified_date: 2026-06

## Scope

This directory (`skills/movie-experts/production/references/`) contains 5 curated reference files that form the production expert's RAG corpus (AI-relevant subset only — NO live-action crews/permits/insurance per PROD-07). Each ref paraphrases concrete heuristics (numbers, rules, thresholds, costs) drawn from the source listed below. **No ref reproduces proprietary training datasets, LoRA weights, or studio asset manifests beyond the Fair Use quota.**

The corpus is authored under **Fair Use** (17 U.S.C. § 107) and the corresponding Chinese 著作权法 第二十四条 合理使用 provision.

## Per-ref attribution

| Ref | Source | Copyright status |
|-----|--------|------------------|
| `casting-lora-spec.md` | Hugging Face PEFT docs (2026-06) + Kohya_ss SDXL/FLUX LoRA training guides + Civitai community best-practice guides (2024-2026) + fal-ai FLUX LoRA API docs + Hu et al. 2021 (arXiv:2106.09685) | Fair Use — paraphrased training hyperparameters + reference image spec protocol + character ID consistency 4-layer verification only; no proprietary LoRA weights / datasets |
| `wardrobe-per-scene.md` | Cole *The Complete Book of Costume Design* (2020) + Landon *The Guide to Filmmaking: Costumes & Wardrobe* (2018) + Bordwell & Thompson *Film Art* (11th ed, 2020) §Costume + CN 平台 公开 短剧 wardrobe 案例研究 (2024-2026) | Fair Use — paraphrased wardrobe baseline 3-layer architecture + per-scene delta protocol + cross-shot continuity hard rule only |
| `lighting-intent-layer.md` | Alton *Painting with Light* (1949, reprint 2013) + Malkiewicz *Film Lighting* (2nd ed, 2012) + Bordwell & Thompson *Film Art* (11th ed, 2020) §Lighting + Hermes fal-ai FLUX 2 docs (2026-06) + Stable Diffusion lighting prompt engineering community guides | Fair Use — paraphrased 3-point lighting setup + per-genre ratio + AI native lighting prompt token推荐 only |
| `gpu-render-budget.md` | AWS / RunPod / Modal / Replicate GPU pricing pages (2026-06) + Hugging Face PEFT training cost guides + fal-ai / Replicate FLUX inference pricing + Civitai community cost analyses + Runway / Kling / Veo / Sora pricing (2026-06) | Fair Use — paraphrased cost heuristics + budget allocation formulas; no proprietary pricing API verbatim |
| `asset-reuse-plan.md` | Hermes fal-ai / Replicate asset management guides (2026-06) + 公开 短剧 studio production pipeline case studies (2024-2026) + Bordwell & Thompson *Film Art* (11th ed, 2020) §Production Management + Avid / DaVinci asset library patterns | Fair Use — paraphrased asset batching heuristics + cross-episode reuse patterns |

## Fair Use four-factor analysis

1. **Purpose and character of use:** Transformative — production pipeline heuristics extracted as operational rules applied to AI 短剧 / 微电影 production.
2. **Nature of the copyrighted work:** Published craft textbooks (factual / instructional) + public technical documentation (factual). Pricing pages are public commercial offers.
3. **Amount and substantiality:** Only paraphrased rules + cost formulas + asset protocols are used; no LoRA weights verbatim, no proprietary training datasets.
4. **Effect upon the potential market:** None — targets AI 短剧 production market, not cinematography-instruction or LoRA-training-platform market.

## Refresh obligation

Every ref carries `Last-verified: 2026-06-15` stamp. Stale refs (>90 days) are flagged.

**HIGH-DRIFT-RISK refs:**
- `gpu-render-budget.md` — pricing changes MONTHLY; re-verify before any production budget commit
- `casting-lora-spec.md` — LoRA training hyperparameters evolve with new model releases
- `lighting-intent-layer.md` — AI lighting prompt tokens evolve with model updates

## Live-action exclusion (PROD-07)

Per Phase 5 PROD-07, this corpus **explicitly excludes** live-action production topics:
- Crew hiring / guild requirements (DGA / WGA)
- Location permits + insurance
- On-set equipment rental (camera bodies / lenses / grip / lighting)
- Post-production facility rental
- Stunt coordination + safety protocols
- Catering / craft services
- Union compliance

These topics are deferred to v2.

## Cross-references

- [`../_shared/SKILL-LAYOUT.md`](../_shared/SKILL-LAYOUT.md) — reference anatomy spec
- [`../_shared/glossary.md`](../_shared/glossary.md) — EN↔CN term dictionary
- [`../performer/references/stanislavski-prepares.md`](../performer/references/stanislavski-prepares.md) — character behavior consistency
- [`../continuity/references/cross-shot-auditing.md`](../continuity/references/cross-shot-auditing.md) — wardrobe + face consistency audit
- [`../colorist/references/bellantoni-color-psychology.md`](../colorist/references/bellantoni-color-psychology.md) — wardrobe color × emotion doctrine
