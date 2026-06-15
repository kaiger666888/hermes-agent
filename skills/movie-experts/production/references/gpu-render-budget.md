# GPU / Render Budget Allocation — Character-LoRA Cost + Render-Farm Heuristics

**Source:** AWS / RunPod / Modal / Replicate GPU pricing pages (accessed 2026-06);Hugging Face PEFT training cost guides (2024-2026);fal-ai / Replicate FLUX inference pricing (2026-06);Civitai community LoRA training cost analyses (2024-2026);Runway Gen-3 / Kling / Veo / Sora token pricing (2026-06)。
**Copyright:** Fair Use — paraphrased cost heuristics + budget allocation formulas;no proprietary pricing API verbatim. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

> **⚠ Pricing drift warning:** Cloud GPU + model API pricing changes monthly. This ref carries `verified_date: 2026-06`. Re-verify pricing before any production budget commit.

## Summary

本 ref 定义 production 专家在 **GPU/render budget allocation** 决策时的**权威源**。它涵盖 character LoRA 训练成本 + image generation 成本 + video generation 成本 + 跨 shot / episode 资产复用 heuristics + 总 budget allocation 公式。

它与 [`casting-lora-spec.md`](./casting-lora-spec.md)、[`wardrobe-per-scene.md`](./wardrobe-per-scene.md)、[`lighting-intent-layer.md`](./lighting-intent-layer.md)和 [`asset-reuse-plan.md`](./asset-reuse-plan.md)互补。

术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)。

---

## GPU Pricing Reference (2026-06)

### 关键 heuristic 1 (load-bearing): 主流 GPU 速率参考(2026-06)

| GPU | 显存 | 用途 | AWS rate | RunPod rate | Modal rate |
|-----|------|------|----------|-------------|------------|
| H100 80GB | 80GB | Heavy training(MusicGen-large / video LoRA)| $4.50-6.00/hr | $2.50-3.50/hr | $3.20-4.50/hr |
| A100 80GB | 80GB | Standard training(FLUX LoRA, character LoRA)| $3.00-4.00/hr | $2.00-3.00/hr | $2.50-3.50/hr |
| A100 40GB | 40GB | Mid training | $2.50-3.00/hr | $1.50-2.00/hr | $2.00-2.50/hr |
| A10G 24GB | 24GB | Inference(image gen, audio gen)| $1.00-1.50/hr | $0.50-0.80/hr | $0.80-1.10/hr |
| L4 24GB | 24GB | Light inference | $0.80-1.00/hr | $0.40-0.60/hr | $0.60-0.80/hr |
| T4 16GB | 16GB | Audio inference / TTS | $0.50-0.80/hr | $0.30-0.40/hr | $0.40-0.50/hr |

**Cloud-agnostic 经验:** RunPod 通常比 AWS 便宜 30-50%;Modal 介于两者之间,但 spot pricing 更激进。

---

## Character LoRA Training Cost

### 关键 heuristic 2: LoRA 训练成本公式

per [`casting-lora-spec.md`](./casting-lora-spec.md) §LoRA Training Protocol,character LoRA 训练成本:

```
lora_training_cost = (training_steps / steps_per_minute) / 60 × GPU_rate × re_take_buffer
```

**经验值(A100 80GB @ $2.50/hr):**
- 主角 LoRA(3000 steps, rank 32):0.75 hour × $2.50 × 1.3 (re-take buffer) = **$2.44**
- 配角 LoRA(2000 steps, rank 16):0.5 hour × $2.50 × 1.3 = **$1.63**
- 群演 LoRA(1000 steps, rank 8):0.25 hour × $2.50 × 1.3 = **$0.81**

### 关键 heuristic 3: Per-character cost decision matrix

| Character type | LoRA rank | Training cost | 推理 cost / shot | 推理 cost / 30-ep 短剧 | Total |
|----------------|-----------|---------------|-------------------|------------------------|-------|
| 主角(featured) | 32 | $2.44 | $0.0005 | $0.25 | **$2.69** |
| 反派(antagonist) | 32 | $2.44 | $0.0005 | $0.25 | **$2.69** |
| 配角(supporting) | 16 | $1.63 | $0.0003 | $0.15 | **$1.78** |
| 群演(extra) | 8 | $0.81 | $0.0002 | $0.10 | **$0.91** |

**典型 男频-revenge 短剧 30 集 cast cost:**
- 1 主角 + 1 反派 + 3 配角 + 5 群演 = $2.69 × 2 + $1.78 × 3 + $0.91 × 5 = $5.38 + $5.34 + $4.55 = **$15.27**

---

## Image Generation Cost

### 关键 heuristic 4: FLUX 2 / Stable Diffusion 推理成本

主流 image generation API pricing(2026-06):

| Model | Provider | Cost / image(1024×1024)| Notes |
|-------|----------|----------------------------|-------|
| FLUX 2 Klein 9B | fal-ai | $0.025-0.040 | Hermes 默认 image gen |
| FLUX 1.1 Pro | fal-ai | $0.040 | 老 model,便宜但 quality 略低 |
| Stable Diffusion 3.5 | self-hosted | $0.005-0.010 (GPU amortized) | 适合批量 |
| DALL-E 3 | OpenAI | $0.040 | 不推荐(无 LoRA 支持)|

**典型 短剧 image cost(30 集,每集 15 shots,每 shot 1 I-frame + 2 alt):**
- 30 × 15 × 3 = 1350 images
- 1350 × $0.030 = **$40.50** for FLUX 2 全 image generation

---

## Video Generation Cost

### 关键 heuristic 5 (load-bearing): Video gen model API pricing(2026-06)

主流 video generation API pricing:

| Model | Provider | Cost / 5s clip(720p) | Cost / 10s clip(720p) | 备注 |
|-------|----------|------------------------|-------------------------|------|
| Runway Gen-3 Alpha Turbo | runwayml.com | $0.50 | $1.00 | 速度快,quality 好 |
| Runway Gen-3 Alpha Lite | runwayml.com | $0.30 | $0.60 | 便宜 30%,速度慢 |
| Kling 1.6 Pro | klingai.com | $0.70 | $1.40 | CN 内容偏好 |
| Kling 1.6 Standard | klingai.com | $0.35 | $0.70 | 便宜,quality 略低 |
| Veo 2 | Google AI Studio | $0.40 | $0.80 | cinematic 理解强 |
| Sora 2 | OpenAI | $0.80-1.20 | $1.60-2.40 | 60s 长 clip,multi-shot 支持 |

**典型 短剧 video cost(30 集,每集 8 clips × 5s = 40s 总视频):**
- 30 × 8 = 240 clips
- Runway Gen-3 Alpha Turbo: 240 × $0.50 = **$120**
- Kling 1.6 Pro: 240 × $0.70 = **$168**
- Veo 2: 240 × $0.40 = **$96**

---

## Total Budget Allocation Formula

### 关键 heuristic 6 (load-bearing): 短剧 总 budget 公式

```
total_budget = (
    character_lora_cost +      # Per-character LoRA training
    image_generation_cost +    # I-frames + alt frames
    video_generation_cost +    # 5-10s clips × shot count
    audio_generation_cost +    # foley + composer + voicer
    re_take_buffer +           # 30% re-take overhead
    ops_overhead               # Storage + transfer + monitoring
)
```

**典型 30 集 抖音-男频-revenge 短剧 budget allocation:**

| 项目 | 成本(USD) | 占比 |
|------|-----------|------|
| Character LoRA training(10 characters)| $15.27 | 6% |
| Image generation(1350 FLUX 2 images)| $40.50 | 17% |
| Video generation(Runway Gen-3 Alpha Turbo,240 × 5s)| $120.00 | 49% |
| Audio generation(foley + composer + voicer)| $25.00 | 10% |
| Re-take buffer(30%)| $60.23 | 25% |
| Ops overhead(storage / transfer)| $5.00 | 2% |
| **TOTAL** | **$265.00** | 100% |

**关键洞察:** video generation 占 49% budget。Video model selection 是 budget 优化的最大杠杆。Switch Runway Turbo → Kling Standard 节省 50% video cost。

---

## Asset Reuse Strategy

### 关键 heuristic 7: Cross-shot asset reuse 5 大策略

per [`asset-reuse-plan.md`](./asset-reuse-plan.md):

1. **I-frame reuse:** 同 character 在不同 shot 中的 I-frame 复用(LoRA 保证 character ID 一致)
2. **Background reuse:** 同场景 multiple shots 共享 background(diffusion model + mask)
3. **Wardrobe reuse:** wardrobe baseline 复用(per [`wardrobe-per-scene.md`](./wardrobe-per-scene.md))
4. **Lighting reuse:** 同场景 lighting setup 复用(per [`lighting-intent-layer.md`](./lighting-intent-layer.md))
5. **Music / SFX reuse:** episode-level music theme 复用(composer expert)

详见 [`asset-reuse-plan.md`](./asset-reuse-plan.md) §Cross-Shot Asset Batching。

---

## Budget Tracking Schema

production 输出 `budget_tracking.json`:

```json
{
  "project_id": "S01_短剧_30ep",
  "budget_allocation": {
    "character_lora": {"allocated": 20, "spent": 15.27, "remaining": 4.73},
    "image_generation": {"allocated": 50, "spent": 40.50, "remaining": 9.50},
    "video_generation": {"allocated": 130, "spent": 120.00, "remaining": 10.00},
    "audio_generation": {"allocated": 30, "spent": 25.00, "remaining": 5.00},
    "ops_overhead": {"allocated": 10, "spent": 5.00, "remaining": 5.00}
  },
  "re_take_buffer_pct": 30,
  "total_allocated": 240,
  "total_spent": 205.77,
  "remaining": 34.23,
  "burn_rate_pct": 86
}
```

---

## Anti-Patterns

### 关键 heuristic 8: Budget 5 大 anti-pattern(规避)

1. **No re-take buffer anti-pattern:** budget 不留 re-take buffer,导致 over-budget。**Mitigation:** 30% re-take buffer。
2. **Single video model lock-in anti-pattern:** 全用 Runway Turbo 不考虑 cheaper alternatives。**Mitigation:** per-scene 复杂度选择 model。
3. **Over-trained LoRA anti-pattern:** character LoRA 训练过多图片 + 过高 rank 浪费 cost。**Mitigation:** per [`casting-lora-spec.md`](./casting-lora-spec.md) §LoRA Training Protocol。
4. **No asset reuse anti-pattern:** 每个 shot 从零生成,无 I-frame / background / lighting 复用。**Mitigation:** per [`asset-reuse-plan.md`](./asset-reuse-plan.md)。
5. **Manual cost tracking anti-pattern:** 无自动化 budget tracking。**Mitigation:** budget_tracking.json + 每 episode 更新。

---

## Glossary

- **GPU rate:** 每 GPU 小时成本(因 GPU 类型和 cloud 而异)。
- **Re-take buffer:** 预算中预留给 re-take 的 30% buffer。
- **Burn rate:** 实际花费 / 总预算(%);接近 100% 触发警告。
- **Asset reuse:** 跨 shot / episode 复用 image / background / lighting / music。

---

*Generated: 2026-06-15 as part of Phase 5 EXPERT-PROD (production expert).*
*Source provenance: AWS / RunPod / Modal / Replicate pricing pages (2026-06) / Hugging Face PEFT guides / fal-ai pricing / Civitai cost analyses — fair use paraphrase + short technical phrases only.*
*⚠ Pricing drift: monthly refresh required. `verified_date: 2026-06` is load-bearing.*
