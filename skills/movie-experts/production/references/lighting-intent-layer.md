# Lighting Intent Layer — 3-Point Lighting + Mood Lighting + AI Native Constraints

**Source:** Alton *Painting with Light* (1949, reprint 2013, University of California Press);Malkiewicz *Film Lighting* (2nd ed, 2012);Bordwell & Thompson *Film Art* (11th ed, 2020) §Lighting chapter;Hermes fal-ai FLUX 2 docs (fal.ai/models/fal-ai/flux-2/klein/9b, 2026-06);Stable Diffusion lighting prompt engineering community guides (2024-2026)。
**Copyright:** Fair Use — paraphrased lighting setup + AI native constraint heuristics; no reproduction of copyrighted film stills or gaffer diagrams. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 production 专家在 **lighting intent(灯光意图)** 决策时的**权威源**。它涵盖 3-point lighting setup + per-genre lighting 协议 + AI native constraints(扩散模型对 lighting prompt 的响应特性)+ 与 colorist / drawer / cinematographer 的 handoff。

它与 [`casting-lora-spec.md`](./casting-lora-spec.md)、[`wardrobe-per-scene.md`](./wardrobe-per-scene.md)、[`gpu-render-budget.md`](./gpu-render-budget.md)和 [`asset-reuse-plan.md`](./asset-reuse-plan.md)互补。

术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)。

---

## 3-Point Lighting Standard

### 关键 heuristic 1 (load-bearing): 3-point lighting standard setup

经典 3-point lighting per Alton *Painting with Light* (1949):

| Light | 位置 | 强度 | 用途 |
|-------|------|------|------|
| **Key light** | camera 左 / 右 30-45°,高于主体 30-45° | 100%(reference)| 主要光源,塑造主体形态 |
| **Fill light** | camera 对侧,与 key 同高度 | 30-50% of key | 填充 key 产生的 shadow |
| **Back light / Rim light** | 主体后方,高于主体 45-60° | 50-100% of key | 分离主体与 backdrop,r highlight 主体轮廓 |

**Key-to-fill ratio** 决定 dramatic intensity:
- **Low ratio (2:1):** 高调 / 明亮 / 喜剧 / 女频 romance
- **Medium ratio (4:1):** 中等 / 标准剧情
- **High ratio (8:1+):** 低调 / 戏剧 / 黑色 / 悬疑 / 男频 revenge
- **Very high ratio (16:1+):** 极低调 / 黑色电影 / horror

### 关键 heuristic 2: Per-genre lighting 协议

| Genre | Key-to-fill ratio | 主光色温 | Back light | 短剧 修正 |
|-------|-------------------|----------|------------|-----------|
| Comedy / 女频 romance | 2:1 | warm 3200K | soft rim | 高调 + 柔光 |
| Drama / 文艺 | 4:1 | natural 5600K | standard rim | 中等 + 自然光 |
| Thriller / 男频 revenge | 8:1+ | cool 3200K + warm practical | hard rim | 低调 + 高对比 |
| Horror | 16:1+ | cool 4200K from below | minimal | 极低调 + 红色 wash |
| Documentary / 现实主义 | natural | natural 5600K | ambient | 自然光 + minimal setup |
| Music video / 实验 | variable | colored | colored | stylized |

---

## AI Native Constraints(扩散模型对 lighting 的响应)

### 关键 heuristic 3 (load-bearing): FLUX 2 / Stable Diffusion 对 lighting prompt 的 5 大约束

扩散模型对 lighting 的理解与传统 cinematography 不同,production 必须考虑:

1. **Light direction 强度:** FLUX 2 / SD 对 "light from camera left" 等方向词响应良好;"light at 35° azimuth, 60° elevation" 等精确角度响应差。
2. **Light quality:** "soft light" / "hard light" 区分准确;"diffused" / "directional" 区分准确。
3. **Multiple light sources:** FLUX 2 支持 2-3 light sources(如 "key + fill + back");4+ light sources 易混乱。
4. **Colored light:** "warm key with cool fill" 区分准确;"cyan rim with magenta key" 等饱和色 light 易 over-saturate。
5. **Time of day:** "golden hour" / "blue hour" / "magic hour" 响应准确;"3:47 PM" 不响应。

### 关键 heuristic 4: AI lighting prompt token 推荐

| Lighting 意图 | FLUX 2 / SD 推荐 prompt token | 备注 |
|---------------|-------------------------------|------|
| 高调 | "high-key lighting, soft, bright, even illumination" | — |
| 低调 | "low-key lighting, dramatic, deep shadows" | — |
| 3-point 标准 | "3-point lighting setup, key + fill + back" | FLUX 2 准确解析 |
| Natural window | "soft natural light from window, north-facing" | — |
| Golden hour | "warm golden hour sunlight, long shadows" | — |
| Blue hour | "cool blue hour twilight, ambient" | — |
| Tungsten practical | "warm tungsten practical light, lamp-lit interior" | — |
| Neon cyberpunk | "neon cyberpunk lighting, magenta + cyan" | 注意 over-saturation |
| Cinematic chiaroscuro | "chiaroscuro lighting, Caravaggio-style, single-source" | — |

### 关键 heuristic 5: Lighting 在 LoRA 训练中的处理

character LoRA 训练数据中的 lighting 多样性至关重要:

- **Avoid single-lighting overfit:** 若所有训练图片同一 lighting(e.g., 全 soft window light),LoRA 在其他 lighting 下生成效果差
- **Recommended lighting distribution per character LoRA:**
  - 40% soft front lighting
  - 25% side lighting(左 + 右)
  - 15% back lighting / rim
  - 15% low-key dramatic
  - 5% experimental / stylized

---

## Lighting Intent JSON Schema

production 输出 `lighting_intent.json`:

```json
{
  "scene_id": "S01E01_scene_003",
  "lighting_setup": {
    "key_light": {
      "position": "camera left 35°, height 45°",
      "intensity_pct": 100,
      "color_temp_K": 3200,
      "quality": "soft"
    },
    "fill_light": {
      "position": "camera right 30°, height 30°",
      "intensity_pct": 35,
      "color_temp_K": 3200,
      "quality": "soft"
    },
    "back_light": {
      "position": "subject rear 45°, height 60°",
      "intensity_pct": 75,
      "color_temp_K": 5600,
      "quality": "hard"
    }
  },
  "key_to_fill_ratio": "3:1",
  "ai_prompt_tokens": {
    "flux_2": "3-point lighting setup, soft warm key, low fill ratio, hard rim back light, dramatic mood",
    "stable_diffusion_xl": "cinematic 3-point lighting, key + fill + back, chiaroscuro"
  },
  "handoff": {
    "to_colorist": "lighting_mood=high_contrast_dramatic, color_temp=3200K",
    "to_drawer": "lighting_prompt_token='3-point lighting setup, soft warm key, low fill ratio, hard rim back light'",
    "to_cinematographer": "lighting_consistent_with_shot_intent=true"
  }
}
```

---

## Cross-Expert Handoff

production 的 lighting intent 流向:

- **→ colorist:** lighting 决定 color grading baseline(colorist 在 lighting 基础上调整 final CxSxZ)
- **→ drawer:** lighting prompt token 注入 image generation prompt
- **→ cinematographer:** lighting 与 shot intent 一致性 verification
- **→ continuity:** 跨场景 lighting continuity(同场景 lighting 必须 consistent)

---

## Anti-Patterns

### 关键 heuristic 6: Lighting 5 大 anti-pattern(规避)

1. **Flat lighting anti-pattern:** 无 fill + 无 back,主体扁平无 depth。**Mitigation:** 3-point standard。
2. **Wrong light direction for genre anti-pattern:** 喜剧用 high-ratio dramatic lighting。**Mitigation:** per-genre 协议表。
3. **Over-saturated colored light anti-pattern:** 饱和色 light 导致主体颜色失真。**Mitigation:** colored light desaturate 30%。
4. **AI lighting prompt too precise anti-pattern:** "35° azimuth, 60° elevation" AI 不响应。**Mitigation:** 使用 heuristic 4 的 natural language tokens。
5. **Lighting inconsistent within scene anti-pattern:** 同场景 lighting 变化无 motivation。**Mitigation:** continuity verification。

---

## Glossary

- **3-point lighting:** Key + Fill + Back standard setup。
- **Key-to-fill ratio:** Key 强度 / Fill 强度,决定 dramatic intensity。
- **High-key / Low-key:** 高调(明亮 evenly lit)/ 低调(dramatic shadows)。
- **Practical light:** 场景内可见光源(lamp / candle / neon)。
- **Chiaroscuro:** 强烈 light/dark 对比,意大利文艺复兴绘画风格。

---

*Generated: 2026-06-15 as part of Phase 5 EXPERT-PROD (production expert).*
*Source provenance: Alton 1949/2013 / Malkiewicz 2012 / Bordwell & Thompson 2020 / fal-ai FLUX 2 docs (2026-06) — fair use paraphrase + short technical phrases only.*
