---
name: drawer
description: "Drawer Expert: FLUX/LoRA parameter optimization for cinematic visual quality, character consistency, and film-like aesthetics."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm, hermes_llm_vision]
metadata:
  hermes:
    tags: [movie, image, flux, lora, visual, cinematic, character-consistency]
    related_skills: [screenplay, continuity, colorist, animator, style_genome, compliance_marketing, cinematographer]
    expert_id: drawer
    metrics: [aesthetic_score, character_consistency, film_realism, vram_efficiency]
---

# Drawer Expert (抽卡专家)

FLUX/LoRA parameter optimization specialist for cinematic visual quality, character consistency, and film-like aesthetics in AI-generated imagery.

## When to use this skill

The user needs to generate cinematic still frames, key frames for animation reference, character reference shots, or scene imagery for AI film production. Requires `hermes_llm_vision` for visual quality assessment.

## References

| Ref | When to Read | Contents |
|-----|--------------|----------|
| _(Phase 3 will populate with curated refs)_ | — | — |

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

### FLUX Generation
- **sampler**: `euler_a` (default), `dpmpp_2m` (detail)
- **steps**: 20-30 (preview), 30-50 (production)
- **cfg**: 3.5-5.0 (lower = more creative)
- **resolution**: 1024x1024 base, scale for aspect ratio

### LoRA Combinations
- **Character LoRA**: weight 0.6-0.8
- **Style LoRA**: weight 0.4-0.6
- **Total LoRA weight**: never exceed 1.5

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
