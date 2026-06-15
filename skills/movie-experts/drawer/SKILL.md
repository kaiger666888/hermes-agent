---
name: drawer
description: "Drawer Expert: FLUX 2 Klein 9B + LoRA + IP-Adapter + InstantID for cinematic visual quality, character consistency, and film-like aesthetics."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm, hermes_llm_vision]
metadata:
  hermes:
    tags: [movie, image, flux-2, lora, ip-adapter, instantid, visual, cinematic, character-consistency]
    related_skills: [screenplay, continuity, colorist, animator, style_genome, compliance_marketing, cinematographer, production]
    expert_id: drawer
    metrics: [aesthetic_score, character_consistency, film_realism, vram_efficiency]
---

# Drawer Expert (抽卡专家)

FLUX 2 Klein 9B + LoRA + IP-Adapter + InstantID specialist for cinematic visual quality, character consistency, and film-like aesthetics in AI-generated imagery. **Phase 5 v1.5 RAG uplift:** FLUX 1.x Karras samplers (euler_a / dpmpp_2m) phantom stripped per Phase 0 GAP-REPORT;FLUX 2 推理参数 + character consistency stack documented in refs.

## When to use this skill

The user needs to generate cinematic still frames, key frames for animation reference, character reference shots, or scene imagery for AI film production. Requires `hermes_llm_vision` for visual quality assessment.

## References

本专家所有 FLUX 2 推理参数与 character consistency 协议由下列 2 个 refs 独占定义(Phase 5 v1.5 light-refs uplift per REFACTOR-rest-09):

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/flux2-parameter-surface.md`](./references/flux2-parameter-surface.md) | 生成任何 image 或替换 FLUX 1.x phantom 前 | FLUX 2 Klein 9B 推理参数(num_inference_steps / guidance_scale / max_sequence_length)+ 与 SDXL / FLUX 1.x 对比 + 5 大 prompt 工程原则 + 短剧 9:16 vertical generation 协议 + FLUX 1.x Karras samplers phantom strip |
| [`references/character-consistency-lora.md`](./references/character-consistency-lora.md) | 设计 character consistency 或训练 LoRA 前 | LoRA vs IP-Adapter vs InstantID 三方法对比 + 组合协议(consistency stack 强度和 1.0-2.0)+ LoRA training hyperparameters + IP-Adapter weight 调整 + InstantID face identity lock + character ID 4 层验证 |

## Knowledge Retrieval

在生成任何 image / character reference / I-frame 输出前,按以下顺序检索上下文(2 个检索主题):

- **FLUX 2 推理参数 + prompt 工程 + 短剧 vertical generation + phantom strip** —— 详见 [`references/flux2-parameter-surface.md`](./references/flux2-parameter-surface.md)
- **LoRA + IP-Adapter + InstantID 三方法组合 + training + verification** —— 详见 [`references/character-consistency-lora.md`](./references/character-consistency-lora.md)

**若当前 runtime 中有 memory / RAG 工具**,使用以下查询范围:

```
tags="expert:drawer,domain:flux2-parameter-surface"
tags="expert:drawer,domain:character-consistency-lora"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件。

## Role & Philosophy

- Real cinema aesthetic over stylized/2D looks
- Parameter precision over trial-and-error
- VRAM efficiency without quality sacrifice

## Core Capabilities

- FLUX model parameter optimization for photorealistic output
- LoRA combination management (character + style)
- Cinematic composition and lighting design
- Character consistency enforcement across frames
- Film grain and natural lighting integration

## Output Format

- High-resolution images (1024x1024 base, scaled for aspect ratio)
- First-frame images for animator I-frame reference
- Metadata JSON: prompt, LoRA weights, generation parameters

## Key Parameters

### FLUX 2 Generation (Phase 5 v1.5 updated)
- **model**: `fal-ai/flux-2/klein/9b` (Hermes default per `tools/image_generation_tool.py:372`)
- **num_inference_steps**: 12 (preview), 28 (production) — per [`references/flux2-parameter-surface.md`](./references/flux2-parameter-surface.md) §FLUX 2 推理参数
- **guidance_scale**: 3.5 (FLUX 2 default, lower than SDXL's 7.0)
- **max_sequence_length**: 256-512 (FLUX 2 supports longer prompts)
- **resolution**: 1024×1024 base (横屏), 1080×1920 (短剧 vertical 9:16)
- **negative_prompt**: supported (FLUX 2 修正)

> **NOTE:** 旧 SKILL.md 的 `euler_a` / `dpmpp_2m` / `cfg_scale: 3.5-5.0` 是 phantom — FLUX 2 不使用 Karras samplers,使用 distilled flow matching。已 strip per Phase 0 GAP-REPORT。详见 [`references/flux2-parameter-surface.md`](./references/flux2-parameter-surface.md) §Phantom Strip: FLUX 1.x samplers。

### Character Consistency Stack (Phase 5 v1.5 new)
per [`references/character-consistency-lora.md`](./references/character-consistency-lora.md):
- **Character LoRA**: scale 0.65-0.90 (per character type, see ref §LoRA scale 推荐)
- **IP-Adapter**: weight 0.40-0.60 (variable wardrobe / lighting)
- **InstantID**: weight 0.50-0.70 (face identity lock for close-up)
- **Total stack strength**: 1.0-2.0 (sum of all weights; > 2.5 = over-constrained)

### VRAM Budget
- Max 22GB total on RTX 3090
- Reserve 4GB for system overhead
- Batch size: 1

## Style Rules

### Visual Style
- Photorealistic rendering with film grain
- Natural lighting with cinematic color grading
- Shallow depth of field for subject focus

### Composition Rules
- Rule of thirds with intentional breaking
- Leading lines and negative space
- Dynamic angles for emotional impact

### Prohibited
- No 2D cartoon/anime style
- No oversaturated HDR look
- No artificial bokeh patterns

## Workflow

1. **Parse Input** — Extract scene description from screenplay
2. **Prompt Construction** — Generate FLUX prompt from scene + style genome
3. **LoRA Selection** — Select combination based on character/scene requirements
4. **Preview Render** — Low steps (20 steps) for quick validation
5. **Character Consistency Check** — Validate against reference (uses `hermes_llm_vision`)
6. **Production Render** — Full steps (30-50) at target resolution
7. **Quality Check** — Verify against thresholds (uses `hermes_llm_vision`)

## Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| aesthetic_score | >= 8.0 |
| character_consistency | >= 0.85 |
| film_realism | >= 8.0 |
| vram_efficiency | >= 0.7 |

## Collaboration

- **<- screenplay**: scene descriptions, lighting_mood
- **<- style_genome**: composition + color + light_shadow signals
- **<- performer**: action_prompt (character pose/action descriptions)
- **<- colorist**: color_intent.json (influences generation parameters)
- **-> animator**: first_frame image as I-frame reference
- **-> continuity**: production frames for cross-shot consistency audit
- **-> colorist**: raw frames for color grading

## What NOT to do

- Don't exceed 22GB VRAM (single RTX 3090 constraint)
- Don't use total LoRA weight > 1.5 (causes artifacting)
- Don't generate anime/2D style for film production
- Don't skip the preview step (saves VRAM and iteration time)
- Don't ignore character LoRA for multi-shot sequences (consistency breaks)
