---
name: colorist
description: "Colorist Expert: CxSxZ color intent system with 28 core combinations, cinematic color grading for narrative emotion."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, color, grading, color-intent, lut, cinematic, color-science]
    related_skills: [screenplay, style_genome, visual_executor, continuity_auditor, production, theory_critic, cinematographer]
    expert_id: colorist
    metrics: [color_intent_match, color_cross_shot_consistency, style_fidelity]
---

# Colorist Expert (色彩专家)

Cinematic color grading specialist managing the CxSxZ three-dimensional color intent system (Chroma x Saturation x Brightness), with 28 core high-frequency color combinations ensuring color language serves narrative emotion across every shot.

## When to use this skill

The user needs to design color grading, apply color intent to scenes, create LUT curves, ensure cross-shot color consistency, or map emotions to color palettes for AI film production.

## References

本专家所有数值阈值由下列 5 个 refs 独占定义;SKILL.md body 仅作摘要 + 跨链,不重新给出数字原理(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) single-source-of-truth 教训)。

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/bellantoni-color-psychology.md`](./references/bellantoni-color-psychology.md) | 选 CxSxZ 组合的 C(色相)维度前 | Bellantoni 8-color 词汇表(Purple / Red / Yellow / Blue / Green / Orange / White / Black)+ 每色 ≥3 个 canonical director×film triplet(Kurosawa / Villeneuve / Spielberg / Almodóvar 等 n≈100 部 1960-2003 电影语料)+ "color as character" doctrine(单一主色必须驱动情绪节拍,非装饰) |
| [`references/hurkman-color-pipeline.md`](./references/hurkman-color-pipeline.md) | 设计 LUT 参数或 lift/gamma/gain 阈值前 | Hurkman *The Art and Technique of Digital Color Correction* (2012, 2nd ed) 数字调色管线 — primary/secondary grading 三层流程 + lift/gamma/gain 操作语义 + qualifier + power window + node-based 流水线 |
| [`references/color-cross-cultural.md`](./references/color-cross-cultural.md) | 设计跨文化或海外发行色盘前 | 学术 cross-cultural 研究 — Schirillo 1200-film sample 色温-情绪映射 + Adams & Osgood 23-culture color-emotion 跨文化 survey + Ekman basic-emotion 色彩关联(meta-analysis) |
| [`references/cn-audience-color.md`](./references/cn-audience-color.md) | 设计 短剧 / 微电影 CN 受众色盘前 | CN 受众色彩偏好(抖音 100K+ 视频色温统计 + 短剧 男频/女频 色温分野 + 国风 色盘 + 年节/双 11 节庆色卡)+ per-platform divergence(抖音高饱和 / 快手暖色偏低饱和 / 小程序剧重 deep teal+orange) |
| [`references/digital-color-science.md`](./references/digital-color-science.md) | 验证色精度或设计 ablation 实验前 | 数字色彩科学 — Rec.709 / Rec.2020 / DCI-P3 色域 + ΔE2000 色差公式(production ≤3 / preview ≤6)+ACES IDT/ODT 流水线 + LUT bit-depth 误差累积模型(8-bit banding 临界点 0.03 S delta)|
| [`../_shared/project-corpus/lighting-equipment-and-design.md`](../_shared/project-corpus/lighting-equipment-and-design.md) §Part 2 | 设计色彩叙事 / 研究第五代摄影师时 | 《镜头在说话》第五代摄影师色彩分析方法 + 色彩画中画 + 平面蒙太奇 + 理性写实主义 + 经典案例(英雄/花样年华/卧虎藏龙) |

## Knowledge Retrieval

在生成任何 `color_intent.json` / LUT 参数 / 28-combination 选择输出前,按以下顺序检索上下文(5 个检索主题):

- **Bellantoni 8-color 词汇表 + "color as character" doctrine**(8 主色 × 3+ canonical director×film triplet × 情绪负载)—— 详见 [`references/bellantoni-color-psychology.md`](./references/bellantoni-color-psychology.md)
- **Hurkman 数字调色管线**(primary/secondary/qualifier 三层 + lift/gamma/gain 语义 + node-based 流水线)—— 详见 [`references/hurkman-color-pipeline.md`](./references/hurkman-color-pipeline.md)
- **Cross-cultural 色彩-情绪学术研究**(Schirillo 1200-film + Adams & Osgood 23-culture + Ekman meta)—— 详见 [`references/color-cross-cultural.md`](./references/color-cross-cultural.md)
- **CN 受众色彩偏好与 per-platform divergence**(抖音 / 快手 / 小程序剧 色温饱和度分野 + 国风 / 节庆色盘)—— 详见 [`references/cn-audience-color.md`](./references/cn-audience-color.md)
- **数字色彩科学与色精度**(Rec.709/2020/DCI-P3 + ΔE2000 + ACES + LUT bit-depth 误差)—— 详见 [`references/digital-color-science.md`](./references/digital-color-science.md)

**若当前 runtime 中有 memory / RAG 工具**(例如 `<memory_plugin>` / `<rag_search>` 或类似检索工具,具体工具名由 runtime 决定),使用以下查询范围:

```
tags="expert:colorist,domain:bellantoni-color-psychology"
tags="expert:colorist,domain:hurkman-color-pipeline"
tags="expert:colorist,domain:color-cross-cultural"
tags="expert:colorist,domain:cn-audience-color"
tags="expert:colorist,domain:digital-color-science"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件(以 `## References` 表为准)。静态 refs 是权威源,memory 插件只是更大语料的优化。provider-agnostic 检索是 ablation eval 与多 provider 部署的硬约束。

> **NOTE:** 本 SKILL.md body 不引用任何具体外部模型名。涉及具体模型时使用 `<llm_primary>` / `<llm_fallback>` 占位符(见 [`../_shared/RAG-INVOCATION-PATTERN.md`](../_shared/RAG-INVOCATION-PATTERN.md) placeholder 表)。模型名只出现在 `references/*.md` 与 [`../_shared/known-external-models.yaml`](../_shared/known-external-models.yaml) allowlist 中。

## Role & Philosophy

- Color is the first emotion the audience feels before understanding anything
- Every color decision must have narrative motivation
- Cross-shot consistency is as important as beauty within a shot

## Core Capabilities

- CxSxZ 3D color intent matrix design (Chroma x Saturation x Brightness)
- 28 core high-frequency color combination parametric memory
- Color psychology to emotion mapping
- Cross-shot color consistency encoding and enforcement

## Output Format

- `color_intent.json`: per-shot CxSxZ 3D encoding
- `lut_reference`: recommended LUT curve parameters (lift/gamma/gain)
- `mood_color_map`: emotion-to-color mapping table

## Key Parameters

### Color Intent Encoding
- **color_space**: CIELAB (computation), HSL (output)
- **chroma_range**: 0-360° (±5° precision)
- **saturation_range**: 0.0-1.0 (0.05 steps)
- **brightness_range**: 0.0-1.0 (0.05 steps)
- **format**: `{C: [min, max], S: [min, max], Z: [min, max]}`

### LUT Parameters
- **lift**: shadows, RGB -0.05 to +0.05
- **gamma**: midtones, RGB 0.8 to 1.2
- **gain**: highlights, RGB 0.8 to 1.2
- **saturation_boost**: -0.3 to +0.3
- **temperature_shift**: -150K to +150K
- **tint_shift**: -0.02 to +0.02 (green-magenta axis)

### Color Transitions
- **transition_duration**: >= 2.0 seconds
- **transition_curve**: ease_in_out (default), linear (abrupt shifts)
- **cross_dissolve_blend**: 0.0-1.0

### GPU Budget
- Color analysis: ~2GB | LUT application: CPU | Total: <= 3GB

## 28 Core Color Combinations (Selection)

完整 28 组 CxSxZ 配方的创意侧权威源(每项情绪-色映射的 8-color 归属与 canonical deployment)详见 [`references/bellantoni-color-psychology.md`](./references/bellantani-color-psychology.md) §The 8-Color Vocabulary;CN 受众偏好覆盖详见 [`references/cn-audience-color.md`](./references/cn-audience-color.md);技术侧 LUT 实现参数详见 [`references/hurkman-color-pipeline.md`](./references/hurkman-color-pipeline.md) §Lift/Gamma/Gain Semantics。

| ID | Emotion/Scene | C (°) | S | Z | Bellantoni 8-color |
|----|--------------|-------|---|---|--------------------|
| C01 | Warm morning / Hope | 35-45 | 0.65 | 0.78 | Yellow (warm/safe) |
| C05 | Melancholy dusk / Loss | 220-240 | 0.45 | 0.52 | Blue (loss/grief) |
| C09 | Cold thriller / Fear | 195-210 | 0.30 | 0.38 | Blue (alienation) |
| C14 | Romantic soft light | 330-350 | 0.55 | 0.68 | Red (passion) |
| C21 | Action climax / Tension | 0-10 | 0.75 | 0.55 | Red (danger) |
| C28 | Post-apocalyptic despair | 30-50 | 0.20 | 0.30 | Yellow (decay/sickness) |

完整 28 组 CxSxZ 配方的创意侧权威源(每项情绪-色映射的 8-color 归属与 canonical deployment)详见 [`references/bellantoni-color-psychology.md`](./references/bellantoni-color-psychology.md) §The 8-Color Vocabulary;CN 受众偏好覆盖详见 [`references/cn-audience-color.md`](./references/cn-audience-color.md);技术侧 LUT 实现参数详见 [`references/hurkman-color-pipeline.md`](./references/hurkman-color-pipeline.md) §Lift/Gamma/Gain Semantics。

## Style Rules

### Color Narrative Rules
- Same-scene color temp change <= ±200K (unless narrative time shift)
- Emotional turns: gradual color temp/saturation transition (>= 2 seconds)
- Complementary colors for character confrontations (warm vs cold split)
- Low saturation for repression/introspection
- High saturation only for climaxes or dream/hallucination

### Color Psychology
- Warm (0-60°) -> intimacy, passion, danger — Bellantoni Red/Yellow/Orange triplet, see [`bellantoni-color-psychology.md`](./references/bellantoni-color-psychology.md) §Red/Yellow/Orange Triplets
- Cool (180-270°) -> alienation, melancholy, mystery — Bellantoni Blue/Green triplet, see [`bellantoni-color-psychology.md`](./references/bellantoni-color-psychology.md) §Blue/Green Triplets
- Low saturation (S < 0.25) -> repression, void, professional
- High brightness (Z > 0.75) -> hope, freedom, lightness — Bellantoni White, see [`bellantoni-color-psychology.md`](./references/bellantoni-color-psychology.md) §White Triplet
- Low brightness (Z < 0.35) -> fear, despair, oppression — Bellantoni Black, see [`bellantoni-color-psychology.md`](./references/bellantoni-color-psychology.md) §Black Triplet
- **CN divergence:** 抖音 男频 偏好高饱和暖色(Z ≥ 0.65, S ≥ 0.70);女频 偏好中等饱和暖色 + 高亮度;快手 偏好低饱和暖色(S 0.45-0.60);小程序剧 偏好 deep teal + orange duo-tone — see [`cn-audience-color.md`](./references/cn-audience-color.md) §Per-Platform Divergence

### Prohibited
- Random color changes without emotional motivation
- HDR over-saturation (S > 0.85 in realistic scenes)
- Color jumps without transition between shots
- Colors conflicting with style_genome

## Workflow

1. **Emotion-Color Mapping** — Map each `emotion_curve` sample to CxSxZ combination ID
2. **Combination Selection** — Select from 28 core combinations or interpolate new
3. **LUT Design** — Generate lift/gamma/gain parameters from selected combination
4. **Per-Frame Grading** — Apply LUT parameters to visual_executor output frames
5. **Cross-Shot Verification** — Compare adjacent shots for temp/saturation/brightness consistency
6. **Transition Processing** — Generate color gradient curves at emotional turning points
7. **Output Encoding** — Generate `color_intent.json` + LUT params + graded frames

## Quality Thresholds

色精度阈值(ΔE2000)与 LUT bit-depth 误差累积模型的权威源: [`references/digital-color-science.md`](./references/digital-color-science.md) §ΔE2000 Tolerance Bands + §LUT Bit-Depth Error Accumulation。

| Metric | Production Minimum | Source |
|--------|-------------------|--------|
| color_intent_match | >= 0.85 | (operational) |
| color_cross_shot_consistency | >= 0.80 | (operational) |
| style_fidelity | >= 0.82 | (operational) |
| color_temp_precision | ±150K (production), ±300K (preview) | [`digital-color-science.md`](./references/digital-color-science.md) §Color Temperature Precision |
| ΔE2000 (shot-to-shot) | ≤ 3.0 (production), ≤ 6.0 (preview) | [`digital-color-science.md`](./references/digital-color-science.md) §ΔE2000 Tolerance Bands |
| 8-bit banding threshold | S delta ≥ 0.03 triggers visible banding | [`digital-color-science.md`](./references/digital-color-science.md) §LUT Bit-Depth Error Accumulation |

## Collaboration

- **<- screenplay**: emotion_curve, lighting_mood, sound_mood
- **<- style_genome**: style gene vector, genre color preferences
- **<- visual_executor**: raw generated frames (pre-grading input)
- **<- continuity_auditor**: cross-shot deviation reports (feedback)
- **-> visual_executor**: color_intent.json (influences subsequent frame generation) + color params for temporal consistency
- **-> continuity_auditor**: graded frames for consistency audit
- **-> audio_pipeline (mixer sub-step)**: color emotion annotations for mixing judgment

## What NOT to do

- Don't apply S > 0.85 in realistic scenes (over-saturation)
- Don't skip cross-shot verification (color jumps break immersion)
- Don't allow color temp jumps > ±200K between adjacent shots
- Don't design LUTs without referencing style_genome vector
- Don't apply grading without narrative motivation
