# LICENSE — prompt_injector references

**Owner:** Phase 16 plan `16-01` (single owner — NEW prompt_injector RAG corpus creation).
**Last updated:** 2026-06-17
verified_date: 2026-06

## Scope

This directory (`skills/movie-experts/prompt_injector/references/`) contains 4 curated reference files that form the prompt_injector expert's RAG corpus. Each ref paraphrases concrete heuristics (patterns, weight-tuning ranges, token-count thresholds, prompt-grammar examples) drawn from the sources listed below. **No ref reproduces copyrighted paper text, proprietary model weights, vendor-internal prompt templates, or continuous prose beyond the Fair Use quota (≤5 prompt-token examples per model; no model weight reproduction; no proprietary API verbatim).**

The corpus is authored under **Fair Use** (17 U.S.C. § 107) and the corresponding Chinese 著作权法 第二十四条 合理使用 provision: the material is used for commentary, criticism, and scholarly analysis of prompt-engineering craft technique, not for reproduction of protected expression.

## Per-ref attribution

| Ref | Source | Copyright status |
|-----|--------|------------------|
| `prompt-engineering-patterns.md` | Brown et al. *Language Models are Few-Shot Learners* (GPT-3 paper, NeurIPS 2020) + Wei et al. *Chain-of-Thought Prompting* (NeurIPS 2022) + OpenAI Prompt Engineering Guide (2023-2026) + Anthropic Prompt Engineering Guide (2023-2026) + community prompt-pattern catalogs | Fair Use — paraphrased few-shot template structures + CoT decomposition patterns + structured prompt anatomy + negative-prompt patterns only; no verbatim reproduction of paper text or vendor-internal templates |
| `cross-call-consistency.md` | Hu et al. *LoRA* (ICLR 2022, arXiv:2106.09685) + Hu et al. *IP-Adapter* (arXiv:2308.06721, 2023) + Wang et al. *InstantID* (arXiv:2401.07519, 2024) + community identity-preservation practice (2023-2026) | Fair Use — paraphrased method descriptions + weight-tuning heuristics only; no verbatim paper text; no model weight reproduction; no proprietary training data |
| `token-budget-management.md` | OpenAI tokenizer documentation (2023-2026) + Anthropic context window documentation (2023-2026) + `tiktoken` open-source library + community prompt-chunking practice + `02-NODE-SPECS.md §2.7` canonical 4000-token criterion | Fair Use — paraphrased token-counting heuristics + chunking patterns + redundancy elimination strategies; no verbatim reproduction of proprietary tokenizer internals |
| `model-specific-prompt-templates.md` | FLUX 2 official documentation (blackforestlabs.ai, 2026-06) + Google DeepMind Veo 2 prompt guide (2026-06) + Kling AI 1.6 prompt engineering guide (klingai.com, 2026-06) + community cross-provider abstraction practice (2025-2026) | Fair Use — ≤5 prompt-token examples per model drawn from public vendor documentation; no proprietary model weights / internals / API verbatim; no vendor-internal prompt templates |

## Fair Use four-factor analysis (applied to the academic paper + vendor documentation refs)

1. **Purpose and character of use:** Transformative — prompt-engineering patterns and identity-preservation methods are extracted as craft rules (patterns / weight ranges / token thresholds / grammar examples) and applied to AI 短剧 / 微电影 production, not reproduced for the original academic or vendor-instructional market.
2. **Nature of the copyrighted work:** Published academic papers (factual / scholarly leaning) + public vendor documentation (factual). Papers are peer-reviewed scholarly work; vendor docs are public-facing API documentation.
3. **Amount and substantiality:** Only paraphrased rules and prompt-token examples are used; for academic paper refs ≤ 5 specific heuristics per paper; for vendor model refs ≤ 5 prompt-token examples per model; no model weight reproduction, no proprietary API verbatim, no vendor-internal template reproduction.
4. **Effect upon the potential market:** None — this corpus targets the AI 短剧 production market, not the academic-publishing or video-gen-model-API market served by the original papers and model providers.

## Refresh obligation

Every ref carries `Last-verified` / `verified_date` stamp per [`../_shared/SKILL-LAYOUT.md`](../_shared/SKILL-LAYOUT.md) reference anatomy. Stale refs (Last-verified > 90 days) are flagged by `scripts/verify_skill_references.py`. Quarterly re-verification is the owner's responsibility.

**Model-specific ref (`model-specific-prompt-templates.md`) is HIGH-DRIFT-RISK:** FLUX 2 / Veo / Kling versions change quarterly; prompt-grammar patterns must be re-verified against current model documentation each quarter. The `verified_date: 2026-06` stamp is load-bearing.

**Academic-paper refs (`prompt-engineering-patterns.md` + `cross-call-consistency.md`) are LOW-DRIFT-RISK:** few-shot / CoT patterns and LoRA / IP-Adapter / InstantID methods are stable scholarly contributions; re-verify only when new landmark papers publish.

## Cross-references

- [`../_shared/SKILL-LAYOUT.md`](../_shared/SKILL-LAYOUT.md) — reference anatomy spec
- [`../_shared/glossary.md`](../_shared/glossary.md) — EN↔CN term dictionary (refs hyperlink rather than duplicate)
- [`../visual_executor/SKILL.md`](../visual_executor/SKILL.md) — downstream consumer of `model_prompts` + `consistency_context`
- [`../visual_executor/references/drawer/flux2-parameter-surface.md`](../visual_executor/references/drawer/flux2-parameter-surface.md) — FLUX 2 inference parameters (cross-ref per CONTEXT D-04)
- [`../visual_executor/references/drawer/character-consistency-lora.md`](../visual_executor/references/drawer/character-consistency-lora.md) — visual_executor's LoRA / IP-Adapter / InstantID stack (cross-ref per CONTEXT D-04)
- [`../audio_pipeline/SKILL.md`](../audio_pipeline/SKILL.md) — secondary consumer (audio-side prompt assembly support)
