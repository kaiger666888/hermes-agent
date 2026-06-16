# Prompt Engineering Patterns (提示工程模式)

> **Owner:** Phase 16 plan `16-01` (NEW prompt_injector RAG corpus).
> **Last updated:** 2026-06-17
> verified_date: 2026-06
> **Source mix:** Wei et al. *Chain-of-Thought Prompting* (2022) + Brown et al. *Language Models are Few-Shot Learners* (GPT-3 paper, 2020) + OpenAI Prompt Engineering Guide (2023-2026) + Anthropic Prompt Engineering Guide (2023-2026) + community prompt-pattern catalogs.

## Scope

This ref covers **general prompt engineering patterns** applicable to AI 短剧 / 微电影 generation across `<image_primary>` and `<video_primary>` model horizons. It is the discipline foundation — the *what* and *how* of assembling prompts. Sibling refs cover *cross-call consistency* (identity preservation across calls), *token budget management* (staying under 4000/call), and *model-specific templates* (FLUX 2 / Veo / Kling grammars).

This is a **fair-use scholarship review**: paraphrased craft rules and pattern names drawn from published academic papers and vendor prompt-engineering guides. No verbatim reproduction of proprietary API documentation, model weights, or vendor-internal prompt templates.

---

## §1 — Few-Shot Template Structures

> **Source:** Brown et al. *Language Models are Few-Shot Learners* (NeurIPS 2020) — established that large language models perform few-shot inference via in-context examples. Extended to multimodal gen-models by community practice (2023-2026).

The few-shot template provides `N` exemplar (input, output) pairs in the prompt, then asks the model to complete the `(N+1)`-th. For visual gen-models, "exemplar" = (text prompt, reference image/video frame).

### N-shot selection heuristic

| N | When to use | Trade-off |
|---|-------------|-----------|
| **0-shot** | Atomic single-concern shots (one character, static composition, no cross-call identity constraint beyond LoRA) | Lowest token cost; weakest consistency anchoring |
| **1-shot** | Single-character shots where a reference frame clarifies composition / lighting intent | Moderate token cost; one reference frame anchors visual style |
| **3-shot** | Multi-character compositions or scene transitions where 3 reference frames establish the visual grammar | Higher token cost; stronger style anchoring; risk of reference-frame overfitting |
| **5-shot** | Complex multi-shot sequences where 5 reference frames establish the full visual grammar across the sequence | Highest token cost; ceiling-approaching for 4000-token budget; reserve for high-stakes scenes |

**Empirical stability for `stable_2026` model horizons:** 0-shot and 1-shot are production-default. 3-shot is reserved for compositionally complex shots. 5-shot is reserved for scene transitions or sequence openers. Above 5-shot risks `prompt_overload` fail mode (see `token-budget-management.md`).

### Template structure (text-only prompts)

```
[system]
You are a cinematic image generation assistant. Adhere strictly to the stable constraints.

[user]
Examples:
1. [composition: medium close-up] [lighting: amber key, left-of-frame] [mood: oppressive heat] → (reference_frame_01.png)
2. [composition: wide shot] [lighting: cool blue key, overhead] [mood: cold isolation] → (reference_frame_02.png)

Now: [composition: extreme close-up] [lighting: sodium-vapor practical, frame-left] [mood: moral rot] →
```

### Template structure (multimodal prompts)

For `<image_primary>` and `<video_primary>` models that accept image references, the few-shot examples are embedded as image refs in the multimodal prompt payload. The text portion of the prompt carries only the *delta* (what's new in this shot) — the reference frames carry the *style* and *identity* anchors.

---

## §2 — Chain-of-Thought (CoT) Decomposition

> **Source:** Wei et al. *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models* (NeurIPS 2022) — established that interleaving reasoning steps improves performance on multi-step tasks. Applied to visual gen-models by community practice (2024-2026) as "describe-then-compose" prompt chains.

CoT for visual prompts means: decompose the final prompt into a reasoning chain (describe character → describe lighting → describe composition → compose final prompt) rather than emitting the final prompt in one shot.

### Chain depth heuristic

| Depth | When to use | Trade-off |
|-------|-------------|-----------|
| **Depth 1** | Atomic shots (one concern dominates) | Lowest token cost; no reasoning overhead |
| **Depth 2-3** | Standard shots (identity + composition + lighting) | Moderate token cost; reasoning improves coherence |
| **Depth 4** | Complex shots (identity + composition + lighting + motion) | Higher token cost; max stable depth for `stable_2026` |
| **Depth 5+** | Reserved for research / debugging | Risk of `prompt_overload`; generally avoided in production |

**Empirical stability for `stable_2026` model horizons:** Depth 2-4 is the production range. Above depth 5, token budget approaches 4000/call ceiling and reasoning chain becomes hard to follow.

### Example CoT prompt structure

```
[system]
You are a cinematic image prompt engineer. Reason step-by-step.

[user]
Step 1 (character): Describe char_wuji's identity, wardrobe, posture.
Step 2 (lighting): Describe the lighting setup consistent with the neo-noir mood.
Step 3 (composition): Describe the framing consistent with the medium close-up intent.
Step 4 (compose): Emit the final model-ready prompt combining steps 1-3.
```

---

## §3 — Structured Prompt Anatomy (System / Context / User Segments)

Most production gen-model APIs segment the prompt into three layers:

### System prompt (stable, cached, doesn't count against per-call variance)

- **Stable constraints** that don't change across calls: identity (LoRA refs / IP-Adapter embeddings), style (5-d genome vector), composition conventions (axis locks, screen direction)
- Cached by the model provider for prefix-cache hit rate
- Per `token-budget-management.md`: stable constraints live here, NOT in the user prompt — this is the `prompt_overload` fallback strategy

### Context prompt (semi-stable, scene-scoped)

- **Scene-scoped context** that holds across all shots in a scene but not across scenes: scene-level style overrides, scene-level character state (e.g., "char_wuji is now rain-soaked"), scene-level mood
- Smaller than the system prompt; rebuilt per scene

### User prompt (per-call variance)

- **Per-call variance** that changes shot-by-shot: motion deltas (camera dolly-in vs static), lighting deltas (amber key vs blue key), mood deltas (oppressive heat vs cold isolation)
- This is where token budget discipline matters most — the user prompt is what risks `prompt_overload`

---

## §4 — Task Decomposition Patterns

For complex visual_intent that resists single-prompt expression, decompose into atomic prompt units:

### Split-by-concern

Decompose by semantic concern:
- Identity section (character refs, wardrobe, posture)
- Composition section (framing, eye-line, DoF)
- Motion section (camera move, subject motion)
- Lighting section (key, fill, practicals)
- Mood section (emotional tone, atmosphere)

**Rule:** Never split a concern across two sections — breaks semantic coherence.

### Split-by-shot

For multi-shot sequences, decompose by shot:
- Shot 1 prompt
- Shot 2 prompt
- ...

Each shot's prompt references the shared `consistency_context.json` for identity / style / composition carry. The per-shot prompt carries only the *delta* from the previous shot.

### Split-by-model-target

For mixed `<image_primary>` / `<video_primary>` pipelines:
- `<image_primary>` prompt (for first-frame I-frames, key frames, character reference shots)
- `<video_primary>` prompt (for animated shot segments)

The two prompts share the same `consistency_context` but have different grammars (see `model-specific-prompt-templates.md`).

---

## §5 — Negative-Prompt Patterns

Negative prompts specify what the model should *avoid*. For cinematic 短剧 / 微电影, the standard negative set is:

```
negative_prompt: cartoon, anime, oversaturated, HDR, plastic skin, watermark, signature, low quality, blurry, deformed hands, extra fingers
```

### Negative-prompt selection by genre

| Genre | Add to negative prompt |
|-------|------------------------|
| Photorealistic drama | `cartoon, anime, illustration, painting` |
| Period piece | `modern clothing, modern props, digital devices` |
| Neo-noir | `bright cheerful colors, flat lighting, oversaturated` |
| Period Chinese 短剧 | `western clothing, modern hairstyles, anachronistic props` |

### Anti-over-constraining

Negative prompts > 50 tokens risk degrading output quality (the model spends attention budget on what to avoid rather than what to compose). Keep negative prompts tight (10-30 tokens production-default).

---

## §6 — Failure Modes in Prompt Engineering

| Mode | Cause | Symptom | Fix |
|------|-------|---------|-----|
| Over-constraining | Too many constraints in one prompt; model attention disperses | Output ignores critical constraints | Split into structured sections; move stable constraints to system prompt |
| Under-specifying | Too few constraints; model fills gaps with training-data defaults | Output drifts from intent | Add explicit constraints for identity / composition / lighting |
| Contradictory constraints | Two constraints conflict (e.g., "bright sunny" + "noir shadows") | Output is incoherent | Resolve contradiction at intent layer; pick one |
| Reference-frame overfitting | Few-shot reference frames dominate output; no creative variance | Output is a near-copy of reference | Reduce N-shot; use reference frames only for style anchor |

---

## Cross-references

- [`cross-call-consistency.md`](./cross-call-consistency.md) — identity preservation across calls (LoRA / IP-Adapter / InstantID)
- [`token-budget-management.md`](./token-budget-management.md) — staying under 4000/call ceiling
- [`model-specific-prompt-templates.md`](./model-specific-prompt-templates.md) — FLUX 2 / Veo / Kling grammars
- [`../_shared/glossary.md`](../_shared/glossary.md) — EN↔CN term dictionary

## Sources cited

1. Brown, T. et al. *Language Models are Few-Shot Learners.* NeurIPS 2020. (GPT-3 paper — established few-shot in-context learning)
2. Wei, J. et al. *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models.* NeurIPS 2022.
3. OpenAI. *Prompt Engineering Guide.* 2023-2026. https://platform.openai.com/docs/guides/prompt-engineering
4. Anthropic. *Prompt Engineering Guide.* 2023-2026. https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering
5. Community prompt-pattern catalogs (2023-2026) — fair-use paraphrase of public craft patterns.
