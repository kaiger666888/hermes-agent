# Cross-Call Consistency (跨调用一致性)

> **Owner:** Phase 16 plan `16-01` (NEW prompt_injector RAG corpus).
> **Last updated:** 2026-06-17
> verified_date: 2026-06
> **Source mix:** Hu et al. *IP-Adapter* (2023) + Wang et al. *InstantID* (2024) + Hu et al. *LoRA* (2021) + community identity-preservation prompting practice (2023-2026).

## Scope

This ref covers **maintaining character / scene / style consistency across multiple LLM / gen-model calls** — the canonical challenge for AI 短剧 / 微电影 production where a single episode requires dozens of shots of the same character in the same style. Ties directly to the `cross_call_consistency ≥ 0.85` success criterion in `02-NODE-SPECS.md §2.7`.

This is a **fair-use scholarship review**: paraphrased method descriptions and weight-tuning heuristics drawn from published academic papers. No verbatim reproduction of paper text, no reproduction of proprietary model weights or training data.

---

## §1 — The Cross-Call Consistency Problem

Generative models are **stateless per-call** — each call samples fresh from the model's distribution. Without explicit consistency mechanisms, calling the same prompt twice produces two different outputs (different seed → different character face, different lighting, different composition drift).

For AI 短剧 / 微电影, this is fatal: the audience expects the same character across shots. Cross-call consistency mechanisms anchor the model's output to stable references across calls.

### Consistency dimensions

| Dimension | What must stay consistent | Mechanism |
|-----------|---------------------------|-----------|
| **Identity** | Character face, body, wardrobe | LoRA + IP-Adapter + InstantID |
| **Style** | Genre, mood, aesthetic, color palette | `style_genome_5d` vector + system prompt stable constraints |
| **Composition** | Axis locks, screen direction, framing conventions | `consistency_context.json` composition block + repeat-key-constraints |

### Consistency vs. variance trade-off

Too much consistency → output is a near-copy of reference (boring, no creative variance). Too little consistency → character drifts across shots (jarring, unprofessional).

The `cross_call_consistency ≥ 0.85` criterion targets the **high-consistency end** of this trade-off — 短剧 / 微电影 production prioritizes professional polish over creative variance.

---

## §2 — LoRA (Low-Rank Adaptation)

> **Source:** Hu, E. et al. *LoRA: Low-Rank Adaptation of Large Language Models.* ICLR 2022 (arXiv 2021). Established low-rank adapter fine-tuning for efficient character/style specialization.

LoRA fine-tunes a small set of low-rank matrices on top of a frozen base model. For character consistency, a per-character LoRA is trained on 10-30 reference images of that character, producing a `.safetensors` file (~50-200MB) that can be loaded at inference time.

### When to use LoRA

- **Main characters** appearing in many shots — the per-character LoRA is the primary identity anchor
- **Recurring wardrobe / props** — a wardrobe-specific LoRA can lock costume details across shots
- **Stable, file-based identity** — LoRA files are portable, version-controlled, and don't require re-embedding per call

### LoRA weight tuning

| Character role | Recommended LoRA scale | Rationale |
|----------------|------------------------|-----------|
| Lead (100+ shots/episode) | 0.75-0.90 | Strong anchor; identity must be unmistakable |
| Supporting (20-100 shots) | 0.65-0.80 | Moderate anchor; allows some IP-Adapter contribution |
| Background (5-20 shots) | 0.50-0.65 | Light anchor; rely more on IP-Adapter for variety |

**Stack strength rule:** Total stack strength (LoRA + IP-Adapter + InstantID weights summed) should be 1.0-2.0. Above 2.5 = over-constrained; output becomes rigid and artifact-prone.

### LoRA limitations

- Training requires 10-30 high-quality reference images per character (data prep overhead)
- LoRA is model-specific — a LoRA trained on FLUX 1.x won't work on `<image_primary>` without retraining
- Wardrobe changes require either a new LoRA or IP-Adapter supplementation

---

## §3 — IP-Adapter (Image Prompt Adapter)

> **Source:** Hu, Y. et al. *IP-Adapter: Text Compatible Image Prompt Adapter for Text-to-Image Diffusion Models.* arXiv 2023. Established image-prompt conditioning via decoupled cross-attention.

IP-Adapter conditions the model on an image embedding (rather than text only), allowing a reference image to drive identity / style / composition without fine-tuning. The reference image is encoded via a CLIP image encoder, then injected via a decoupled cross-attention layer.

### When to use IP-Adapter

- **Variable wardrobe / lighting** — same character in different outfits or lighting setups (LoRA can't easily handle this; IP-Adapter can, by swapping reference images)
- **Rapid identity lock without training** — when a per-character LoRA isn't available, IP-Adapter with a single reference image provides moderate identity lock
- **Style transfer** — IP-Adapter can lock style (genre / aesthetic) via a style reference image

### IP-Adapter weight tuning

| Use case | Recommended weight | Rationale |
|----------|-------------------|-----------|
| Identity lock (primary) | 0.50-0.65 | Strong but not dominant; allows LoRA to co-anchor |
| Wardrobe / lighting variation | 0.40-0.55 | Moderate; identity from LoRA, wardrobe from IP-Adapter ref |
| Style transfer | 0.30-0.45 | Light; style hint without dominating composition |

### IP-Adapter vs. LoRA

| Dimension | LoRA | IP-Adapter |
|-----------|------|------------|
| Setup cost | High (training required) | Low (single reference image) |
| Identity strength | Strong | Moderate |
| Flexibility | Low (locked to trained character) | High (swap reference images) |
| File portability | High (.safetensors file) | Medium (reference image + embedding) |

**Recommendation:** Use both. LoRA for stable main-character identity; IP-Adapter for variable wardrobe / lighting / supporting characters.

---

## §4 — InstantID (Zero-Shot Identity Preservation)

> **Source:** Wang, Q. et al. *InstantID: Zero-shot Identity-Preserving Generation in Seconds.* arXiv 2024. Established zero-shot identity preservation via face embedding + IdentityNet.

InstantID preserves face identity in a single forward pass, using only a reference face image (no fine-tuning, no per-character training). It extracts a face embedding from the reference image and injects it via a specialized IdentityNet.

### When to use InstantID

- **Close-up shots** where face identity is paramount — InstantID provides the strongest face identity lock
- **Zero-shot identity** — when no per-character LoRA is available and time is constrained
- **Face identity lock on top of LoRA + IP-Adapter** — stacking all three provides maximum identity preservation

### InstantID weight tuning

| Shot type | Recommended weight | Rationale |
|-----------|-------------------|-----------|
| Close-up (face dominant) | 0.55-0.70 | Strong face lock; close-up amplifies identity drift |
| Medium shot | 0.45-0.60 | Moderate; face visible but not dominant |
| Wide shot | 0.30-0.45 | Light; face is small in frame, less critical |

---

## §5 — Identity Reference Selection (Decision Tree)

```
Is this a main character (recurring across many shots)?
├── YES → Train per-character LoRA (scale 0.65-0.90)
│   ├── Variable wardrobe / lighting? → Add IP-Adapter (0.40-0.60)
│   └── Close-up shots? → Add InstantID (0.50-0.70)
└── NO (supporting / background character)
    ├── Reference image available? → IP-Adapter (0.45-0.60)
    │   └── Close-up? → Add InstantID (0.45-0.60)
    └── No reference image? → Text-only identity description (weakest; reserve for crowd shots)
```

**Total stack strength check:** After selecting methods, sum the weights. Target 1.0-2.0. Above 2.5 = over-constrained.

---

## §6 — Seed Locking + Multi-Shot Consistency Context

Beyond LoRA / IP-Adapter / InstantID, **seed locking** + **consistency_context carry** provide additional cross-call consistency:

### Seed locking

Fix the random seed across calls in a shot sequence. Same seed + same prompt + same references → near-identical output. Useful for:
- Generating variants of the same shot (vary only one parameter, lock the rest)
- Debugging consistency drift (compare outputs at same seed to isolate the drift cause)

**Limitation:** Seed locking doesn't help across *different* shots (different prompts) — it only stabilizes re-runs of the *same* shot.

### Consistency context carry

The `consistency_context.json` artifact (see SKILL.md `## Output Format`) is the canonical carry mechanism. Every call in a shot sequence receives the same `consistency_context`, ensuring:
- Same LoRA / IP-Adapter / InstantID refs loaded
- Same `style_genome_5d` vector in system prompt
- Same composition axis locks + screen direction

**`consistency_drift` fail mode trigger:** `consistency_context` lost or mutated between calls. Fallback: explicitly re-carry + repeat key constraints verbatim in every call's system prompt.

---

## §7 — Identity Drift Detection

To verify cross-call consistency in practice:

### Per-call identity embedding cosine similarity

After each call, compute the identity embedding of the output (via a face encoder for character identity, via CLIP for style). Compare to the reference embedding:

| Cosine similarity | Grade | Action |
|-------------------|-------|--------|
| ≥ 0.92 | A (excellent) | Ship |
| 0.85-0.92 | B (acceptable) | Ship; flag for review |
| 0.75-0.85 | C (marginal) | Retry with stronger InstantID weight |
| < 0.75 | D (failed) | `consistency_drift` triggered; re-carry context + repeat constraints |

The `cross_call_consistency ≥ 0.85` criterion maps to grade B or above.

### Cross-shot drift detection

For shot sequences, compute pairwise identity embedding cosine similarity between consecutive shots. Drift = consecutive-shot similarity < 0.85. Drift indicates `consistency_context` carry failure.

---

## Cross-references

- [`prompt-engineering-patterns.md`](./prompt-engineering-patterns.md) — few-shot / CoT / decomposition patterns
- [`token-budget-management.md`](./token-budget-management.md) — staying under 4000/call ceiling (identity refs count toward budget)
- [`../visual_executor/references/drawer/character-consistency-lora.md`](../visual_executor/references/drawer/character-consistency-lora.md) — visual_executor's LoRA / IP-Adapter / InstantID stack (cross-ref per CONTEXT D-04)

## Sources cited

1. Hu, E. et al. *LoRA: Low-Rank Adaptation of Large Language Models.* ICLR 2022. arXiv:2106.09685.
2. Hu, Y. et al. *IP-Adapter: Text Compatible Image Prompt Adapter for Text-to-Image Diffusion Models.* arXiv:2308.06721, 2023.
3. Wang, Q. et al. *InstantID: Zero-shot Identity-Preserving Generation in Seconds.* arXiv:2401.07519, 2024.
4. Community identity-preservation prompting practice (2023-2026) — fair-use paraphrase of public craft patterns.
