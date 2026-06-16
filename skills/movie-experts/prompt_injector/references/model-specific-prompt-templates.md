# Model-Specific Prompt Templates (模型专属提示模板)

> **Owner:** Phase 16 plan `16-01` (NEW prompt_injector RAG corpus).
> **Last updated:** 2026-06-17
> verified_date: 2026-06
> **Source mix:** FLUX 2 official documentation (2026) + Google DeepMind Veo 2 prompt guide (2026) + Kling AI 1.6 prompt engineering guide (2026) + community cross-provider abstraction practice (2025-2026).
>
> **CRITICAL:** This is the ONLY file in the `prompt_injector` directory where literal model names appear. SKILL.md body uses `<image_primary>` / `<video_primary>` placeholders per threat T-16-03. Every literal model name in this file carries a `verified_date:` stamp — stale templates must be re-verified quarterly.

## Scope

This ref covers **concrete template examples for current 2026 model horizons** — how to instantiate the abstract prompt structure (identity / composition / motion / lighting / mood sections) against specific model grammars. Cross-references `visual_executor/references/drawer/flux-2-prompt-engineering.md` for FLUX 2-specific deep-dive (per CONTEXT D-04 — cross-reference acceptable).

This is a **fair-use scholarship review**: paraphrased prompt-grammar patterns and ≤5 example prompt-token mappings per model, drawn from public vendor documentation. No verbatim reproduction of proprietary API documentation, model weights, or vendor-internal prompt templates.

---

## §1 — The Provider-Agnostic Abstraction Layer

The `prompt_injector` expert operates at two layers:

### Layer 1: Abstract prompt structure (provider-agnostic)

```
[identity] char_wuji, male, 30s, gaunt cheekbones, rain-soaked coat
[composition] medium close-up, eye-line left-of-frame, shallow DoF
[motion] static held beat, micro-tremor in jaw
[lighting] key: amber sodium-vapor practical from frame-left
[mood] oppressive humidity, moral rot barely concealed
```

This abstract structure is **stable across model swaps** — it captures the *intent* of the prompt without committing to any model's grammar.

### Layer 2: Model-specific template instantiation (provider-specific)

A thin adapter maps the abstract structure → model grammar. Swapping `<image_primary>` from FLUX 2 to a successor model should require only a template-adapter change, not an abstract-prompt rewrite.

```
# FLUX 2 adapter
[character: char_wuji, male, 30s, gaunt cheekbones, rain-soaked coat]
[composition: medium close-up, eye-line left-of-frame, shallow DoF]
[motion: static held beat, micro-tremor in jaw]
[lighting: key: amber sodium-vapor practical from frame-left]
[mood: oppressive humidity, moral rot barely concealed]

# Veo adapter
Camera: static held beat, micro-tremor in jaw. Subject: char_wuji, male, 30s, gaunt cheekbones, rain-soaked coat, eye-line left-of-frame. Lighting: amber sodium-vapor practical from frame-left. Mood: oppressive humidity, moral rot barely concealed.
```

---

## §2 — `<image_primary>` (FLUX 2) Prompt Grammar

> **verified_date:** 2026-06
> **Source:** FLUX 2 official documentation (blackforestlabs.ai, accessed 2026-06) + community FLUX 2 prompt engineering guides.

FLUX 2 (Klein 9B) uses a **structured-tags + natural-language blend** grammar. Structured tags (`[key: value]`) anchor specific concerns; natural-language sentences carry mood and atmosphere.

### Grammar pattern

```
[character: <identity description>]
[composition: <framing description>]
[lighting: <lighting setup>]
<mood sentence in natural language>
```

### Example (neo-noir close-up, char_wuji)

```
[character: char_wuji, male, 30s, gaunt cheekbones, rain-soaked dark wool coat, five-o-clock shadow]
[composition: medium close-up, eye-line left-of-frame, shallow depth of field, 9:16 vertical]
[lighting: key: amber sodium-vapor practical from frame-left, fill: cool blue bounce from frame-right, low-key ratio 4:1]
The air is thick with humidity and moral rot; char_wuji's jaw trembles almost imperceptibly as he holds the beat.
```

### FLUX 2-specific notes

- **Negative prompt supported** — `negative_prompt: cartoon, anime, oversaturated, HDR, plastic skin`
- **`max_sequence_length`:** 256-512 tokens (FLUX 2 supports longer prompts than FLUX 1.x)
- **`guidance_scale`:** 3.5 default (lower than SDXL's 7.0 — FLUX 2 needs less guidance pressure)
- **9:16 vertical:** supported natively for 短剧 vertical format (1080×1920)

### FLUX 2 cross-reference

For FLUX 2 inference parameters (num_inference_steps / guidance_scale / max_sequence_length) + character consistency stack (LoRA + IP-Adapter + InstantID weight tuning), see [`../visual_executor/references/drawer/flux2-parameter-surface.md`](../visual_executor/references/drawer/flux2-parameter-surface.md). This ref covers prompt grammar only; parameter surface is visual_executor's domain.

---

## §3 — `<video_primary>` (Veo 2) Prompt Grammar

> **verified_date:** 2026-06
> **Source:** Google DeepMind Veo 2 technical report + prompt guide (2026-06).

Veo 2 uses a **cinematographic descriptor prefixes** grammar. Each sentence begins with a category prefix (`Camera:` / `Subject:` / `Lighting:` / `Mood:`), followed by natural-language description.

### Grammar pattern

```
Camera: <camera move + speed + ease>. Subject: <identity + action>. Lighting: <lighting setup>. Mood: <emotional tone>.
```

### Example (neo-noir dolly-in, char_wuji)

```
Camera: slow dolly-in, ease-in-out, held for 4 seconds. Subject: char_wuji, male, 30s, gaunt cheekbones, rain-soaked dark wool coat, standing still with micro-tremor in jaw, eye-line locked left-of-frame. Lighting: amber sodium-vapor practical key from frame-left, cool blue bounce fill from frame-right, low-key 4:1 ratio. Mood: oppressive humidity, moral rot barely concealed beneath the surface.
```

### Veo 2-specific notes

- **Camera descriptors:** `pan`, `tilt`, `dolly`, `tracking`, `crane`, `static`, `orbit` — each with speed (0.0-1.0) and ease (linear / ease_in / ease_out / ease_in_out)
- **Duration:** 4-8 seconds per clip (concatenate for longer)
- **9:16 vertical:** supported for 短剧 format
- **Audio:** Veo 2 does not generate audio; pair with `audio_pipeline` for sound

---

## §4 — `<video_primary>` (Kling 1.6) Prompt Grammar

> **verified_date:** 2026-06
> **Source:** Kling AI 1.6 prompt engineering guide (klingai.com, 2026-06).

Kling 1.6 uses a **Chinese-friendly natural language with action verbs** grammar. Prompts can be in Chinese or English; Chinese prompts get slightly better performance for CN-native content.

### Grammar pattern (English)

```
<camera move> <subject identity> <subject action> <lighting> <mood>
```

### Grammar pattern (Chinese)

```
<镜头运动> <角色身份> <角色动作> <灯光> <情绪氛围>
```

### Example (English — neo-noir dolly-in, char_wuji)

```
Slow dolly-in. Char_wuji, a gaunt man in his 30s wearing a rain-soaked dark wool coat, stands still with a micro-tremor in his jaw. Amber sodium-vapor key light from frame-left, cool blue bounce fill from frame-right. Oppressive humidity, moral rot beneath the surface.
```

### Example (Chinese — same shot)

```
缓慢推镜头。吴季,三十多岁瘦削男子,身穿淋湿的深色羊毛大衣,静止站立,下巴微微颤抖。左侧钠蒸汽实用主光,右侧冷蓝反射补光。压抑的潮湿感,表面下隐藏的道德腐败。
```

### Kling 1.6-specific notes

- **Chinese prompts:** slightly better semantic fidelity for CN-native content (idioms, cultural references)
- **Action verbs:** Kling responds well to strong action verbs (`推` / `拉` / `摇` / `移` for camera; `站` / `坐` / `走` / `跑` for subject)
- **Duration:** 5-10 seconds per clip
- **9:16 vertical:** supported for 短剧 format

---

## §5 — Cross-Provider Abstraction Patterns

### Pattern 1: Abstract section → model grammar adapter

Define the abstract prompt once (provider-agnostic), then write a thin adapter per model that maps abstract sections → model grammar. Swapping models = swapping adapters, not rewriting prompts.

```python
def flux2_adapter(abstract_prompt):
    return f"[character: {abstract_prompt.identity}]\n[composition: {abstract_prompt.composition}]\n[lighting: {abstract_prompt.lighting}]\n{abstract_prompt.mood}"

def veo2_adapter(abstract_prompt):
    return f"Camera: {abstract_prompt.motion}. Subject: {abstract_prompt.identity}. Lighting: {abstract_prompt.lighting}. Mood: {abstract_prompt.mood}."
```

### Pattern 2: Shared `consistency_context`, per-model prompts

All models in a pipeline share the same `consistency_context.json` (identity / style / composition carry). Only the per-call prompt grammar differs by model.

### Pattern 3: Fallback chain

If `<image_primary>` (FLUX 2) fails (OOM, timeout, quality < threshold), fall back to `<image_fallback>`. The abstract prompt stays the same; only the adapter swaps. Same for `<video_primary>` → `<video_fallback>`.

---

## §6 — Template Instantiation Workflow

1. **Assemble abstract prompt** — from `visual_intent` + `style_genome_5d` + `character_assets`, build the provider-agnostic abstract structure (identity / composition / motion / lighting / mood sections)
2. **Select model target** — based on shot type (still → `<image_primary>`; motion → `<video_primary>`) + available VRAM + latency budget
3. **Apply model adapter** — map abstract structure → model grammar (FLUX 2 / Veo / Kling template)
4. **Load `consistency_context`** — inject identity refs (LoRA / IP-Adapter / InstantID) + style vector + composition locks
5. **Token budget check** — count tokens; if > 4000, trigger `prompt_overload` fallback (see `token-budget-management.md`)
6. **Emit `model_prompts.json`** — final model-ready prompt + metadata

---

## §7 — Model Swap Protocol

When swapping `<image_primary>` or `<video_primary>` to a new model:

1. **Re-verify prompt grammar** — new model may use a different grammar (structured tags vs. natural language vs. descriptor prefixes)
2. **Re-verify token counting** — new tokenizer may count differently
3. **Re-verify consistency refs** — LoRA / IP-Adapter / InstantID may need re-training for the new model
4. **Update `verified_date:` stamp** — stale templates must be re-verified quarterly
5. **Update this ref** — add new model's grammar pattern + example

**Quarterly re-verification is mandatory.** Model versions change quarterly; prompt-token mappings drift. The `verified_date: 2026-06` stamp is load-bearing.

---

## Cross-references

- [`prompt-engineering-patterns.md`](./prompt-engineering-patterns.md) — few-shot / CoT / decomposition patterns (provider-agnostic)
- [`cross-call-consistency.md`](./cross-call-consistency.md) — LoRA / IP-Adapter / InstantID identity preservation
- [`token-budget-management.md`](./token-budget-management.md) — staying under 4000/call ceiling
- [`../visual_executor/references/drawer/flux2-parameter-surface.md`](../visual_executor/references/drawer/flux2-parameter-surface.md) — FLUX 2 inference parameters + character consistency stack (cross-ref per CONTEXT D-04)
- [`../visual_executor/references/animator/video-gen-model-matrix.md`](../visual_executor/references/animator/video-gen-model-matrix.md) — Hermes 6-model video gen catalog (cross-ref per CONTEXT D-04)
- [`../_shared/known-external-models.yaml`](../_shared/known-external-models.yaml) — model name placeholder convention source

## Sources cited

1. Black Forest Labs. *FLUX 2 documentation.* 2026-06. https://blackforestlabs.ai (accessed 2026-06)
2. Google DeepMind. *Veo 2 technical report + prompt guide.* 2026-06.
3. Kuaishou. *Kling AI 1.6 prompt engineering guide.* 2026-06. https://klingai.com (accessed 2026-06)
4. Community cross-provider abstraction practice (2025-2026) — fair-use paraphrase of public craft patterns.
5. `02-NODE-SPECS.md §2.7` — canonical model_horizon `stable_2026` + `current_instantiation` block.
