# Wardrobe per Scene — 服化道 Spec + Continuity Handoff + Cross-Shot Audit

**Source:** Cole *The Complete Book of Costume Design* (2020);Landon *The Guide to Filmmaking: Costumes & Wardrobe* (2018);Bordwell & Thompson *Film Art* (11th ed, 2020) §Costume chapter;CN 平台 公开 短剧 wardrobe 案例研究(2024-2026)。
**Copyright:** Fair Use — paraphrased wardrobe protocol + continuity handoff schema;no reproduction of copyrighted wardrobe designs or branded fashion photography. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 production 专家在 **per-scene wardrobe(服化道)spec** 决策时的**权威源**。它涵盖 character wardrobe baseline + per-scene wardrobe delta + cross-shot wardrobe continuity handoff + 短剧 wardrobe cost optimization。

它与 [`casting-lora-spec.md`](./casting-lora-spec.md)(character LoRA)、[`lighting-intent-layer.md`](./lighting-intent-layer.md)(灯光)、[`gpu-render-budget.md`](./gpu-render-budget.md)(成本)和 [`asset-reuse-plan.md`](./asset-reuse-plan.md)(资产复用)互补。

术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)。

---

## Wardrobe Baseline Protocol

### 关键 heuristic 1 (load-bearing): Per-character wardrobe baseline 3 层架构

每个 character 必须定义 3 层 wardrobe baseline:

| 层级 | 名称 | 用途 | 典型变化频率 |
|------|------|------|--------------|
| **Layer 1** | Baseline wardrobe | character 默认 / 常用服装 | 每 season 1-2 套 |
| **Layer 2** | Scene-specific wardrobe | 特定场景服装(e.g., 正式场合 / 运动场景 / 睡眠)| 每 episode 0-2 次变化 |
| **Layer 3** | Mood / arc wardrobe | 情绪 / 故事 arc 反映(e.g., 复仇前 vs 复仇后)| 每 season 1-3 次大变化 |

**关键规则:** Layer 1 是 character LoRA 训练的一部分(详见 [`casting-lora-spec.md`](./casting-lora-spec.md) §Reference image 采集协议 §Wardrobe baseline);Layer 2/3 是 production 在 LoRA 基础上的 prompt delta。

### 关键 heuristic 2: Wardrobe color 与 emotion_curve 联动

wardrobe 颜色必须与 screenplay emotion_curve 联动(per Bellantoni "color as character" doctrine,详见 [`../colorist/references/bellantoni-color-psychology.md`](../colorist/references/bellantoni-color-psychology.md)):

| Emotion | Wardrobe color 推荐 | 备注 |
|---------|---------------------|------|
| Hope / 升起 | Yellow / warm orange | Bellantoni Yellow triplet |
| Power / 复仇 | Red / black | Bellantoni Red / Black triplet |
| Loss / 悲伤 | Blue / desaturated | Bellantoni Blue triplet |
| Mystery / 暧昧 | Purple / dark green | Bellantoni Purple / Green triplet |
| Purity / 新开始 | White / soft pastel | Bellantoni White triplet |

**Cross-expert handoff:** wardrobe color → colorist 进一步细化为 CxSxZ combination。

---

## Cross-Shot Wardrobe Continuity

### 关键 heuristic 3 (load-bearing): 同场景内 wardrobe continuity hard rule

**核心规则:** 同一场景内同一 character 的 wardrobe 必须 **完全一致**(zero tolerance)。任何 wardrobe 不一致 → shot 必须重新生成。

**verification 协议(per `continuity` expert):**
1. CLIP image embedding cosine similarity ≥ 0.95(wardrobe 视觉一致性)
2. Color histogram Bhattacharyya distance ≤ 0.10(wardrobe 颜色一致性)
3. Garment feature matching(领口 / 袖口 / 纽扣 / pattern 等 keypoint ≥ 80% 匹配)

**failure 处理:** 任一 check 失败 → wardrobe_inconsistency: true 警告 + shot 重新生成。

### 关键 heuristic 4: 跨场景 wardrobe arc(变化必须有 narrative motivation)

跨场景 wardrobe 变化允许,但必须有 narrative motivation(per screenplay emotion_curve beat):

| Wardrobe 变化触发 | Narrative beat 示例 |
|-------------------|---------------------|
| Color shift | 复仇前(blue / gray)→ 复仇后(red / black)|
| Formality shift | 工作场景(suit)→ 居家场景(casual)|
| Damage / wear | 战斗后(破损衣物)→ 治愈后(整洁衣物)|
| Symbolic accessory | 关键 prop(项链 / 戒指 / 手表)在 arc 中的揭示 / 隐藏 |

**Cross-expert handoff:** wardrobe 变化 → continuity expert 标注 `wardrobe_arc: true` + 触发 screenplay emotion_curve 验证。

---

## Wardrobe Spec JSON Schema

production 输出 `wardrobe_spec.json` 标准 schema:

```json
{
  "character_id": "protagonist_main",
  "baseline_wardrobe": {
    "top": "dark gray tailored blazer",
    "bottom": "black slim-fit trousers",
    "shoes": "black leather oxfords",
    "accessories": ["silver watch", "minimalist silver ring"],
    "color_palette": ["#2C2E3A", "#1A1B1F", "#0A0A0A"],
    "reference_image_id": "wardrobe_baseline_001"
  },
  "scene_deltas": [
    {
      "scene_id": "S01E01_scene_003",
      "delta_type": "formality_down",
      "wardrobe_override": {
        "top": "white linen shirt, sleeves rolled",
        "bottom": "navy chinos",
        "shoes": "brown leather loafers"
      },
      "narrative_motivation": "下班后私人时间",
      "continuity_check_required": true
    }
  ],
  "arc_wardrobe": [
    {
      "arc_id": "post_betrayal",
      "start_episode": "S01E15",
      "color_shift": "blue/gray → red/black",
      "narrative_motivation": "protagonist 决定复仇"
    }
  ]
}
```

下游 `continuity` expert 消费此 schema 验证 cross-shot wardrobe consistency。

---

## 短剧 Wardrobe Cost Optimization

### 关键 heuristic 5: Wardrobe cost 5 大优化策略

短剧 budget 受限,wardrobe 成本必须优化:

1. **Baseline wardrobe reuse:** Layer 1 wardrobe 在 60-80% shots 中复用;只有 20-40% shots 需要 Layer 2/3 wardrobe delta
2. **Color palette constraint:** 每个 character 限制在 3-5 色 palette 内,降低 reference image 训练量
3. **Accessory over garment:** 关键 prop 用 accessory(手表 / 项链 / 戒指)而非整套 garment 变化
4. **Off-screen wardrobe change:** wardrobe 变化尽量发生在 off-screen(切镜之间),不需要生成过渡 shot
5. **Stock wardrobe library:** 建立可复用 wardrobe library(基础款 suit / shirt / dress),不同 character 共享 stock pieces

### 关键 heuristic 6: Per-scene wardrobe delta budget

| Episode 类型 | Wardrobe delta 数量 | 典型 cost(USD)|
|-------------|---------------------|----------------|
| 90s 抖音 短剧 | 0-1 delta | $0-5(reference image 生成)|
| 180s 小程序剧 | 1-2 delta | $5-15|
| 30min 微电影 | 3-5 delta | $20-50|
| 60min TV-movie | 8-15 delta | $80-200|

---

## Continuity Expert Handoff

production → continuity handoff schema:

```json
{
  "continuity_handoff": {
    "wardrobe_baselines": ["protagonist_main_baseline", "antagonist_baseline", ...],
    "scene_deltas_count": 12,
    "arc_wardrobe_changes": [
      {"arc_id": "post_betrayal", "verification_required": true}
    ],
    "compliance_required": [
      "verify wardrobe consistency within each scene (zero tolerance)",
      "verify wardrobe changes have narrative motivation",
      "verify wardrobe color aligns with emotion_curve"
    ]
  }
}
```

详见 [`../continuity/references/cross-shot-auditing.md`](../continuity/references/cross-shot-auditing.md) §Wardrobe Continuity Audit。

---

## Anti-Patterns

### 关键 heuristic 7: Wardrobe 5 大 anti-pattern(规避)

1. **Wardrobe inconsistency within scene anti-pattern:** 同场景 character wardrobe 变化。**Mitigation:** zero-tolerance hard rule + continuity expert verification。
2. **Unmotivated wardrobe change anti-pattern:** 跨场景 wardrobe 变化无 narrative motivation。**Mitigation:** wardrobe arc 必须链接 screenplay emotion_curve beat。
3. **Wardrobe color vs emotion_curve mismatch anti-pattern:** wardrobe 颜色与 emotion 不符(e.g., 复仇场景穿 white)。**Mitigation:** Bellantoni "color as character" doctrine 联动验证。
4. **Excessive wardrobe delta anti-pattern:** 每 episode >3 wardrobe delta 增加 cost + 训练时间。**Mitigation:** baseline reuse + accessory over garment。
5. **Wardrobe reference image low quality anti-pattern:** reference image 模糊 / 光照差,导致 LoRA 训练失败。**Mitigation:** 参考 [`casting-lora-spec.md`](./casting-lora-spec.md) §Reference image 采集协议。

---

## Glossary

- **Wardrobe baseline:** Character 默认服装(Layer 1)。
- **Scene-specific wardrobe:** 特定场景服装 delta(Layer 2)。
- **Arc wardrobe:** 情绪 / 故事 arc 反映的 wardrobe 变化(Layer 3)。
- **Wardrobe delta:** 单场景内 wardrobe 与 baseline 的差异。
- **Wardrobe arc:** 跨 episode 的 wardrobe 变化轨迹。

---

*Generated: 2026-06-15 as part of Phase 5 EXPERT-PROD (production expert).*
*Source provenance: Cole 2020 / Landon 2018 / Bordwell & Thompson 2020 / CN 平台 公开 短剧 wardrobe 案例研究 (2024-2026) — fair use paraphrase + short technical phrases only.*
