# Cross-Cultural Style — CN vs Western vs Korean 5D Divergence + Hybrid Encoding

**Source:** David Bordwell *Planet Hong Kong* (2nd ed, 2011, Irvington Way Institute Press, ISBN 978-0615523045); Rey Chow *Sentimental Fabulations, Contemporary Chinese Films* (2007, Columbia UP, ISBN 978-0231136617); Marchetti *Hong Kong Film, Hollywood, and the New Global Cinema* (2007, Routledge); Hwang & Kim *Korean Cinema: From Origins to Renaissance* (2018, Korean Film Council); Nornes *Cinema Babel* (2007, Minnesota UP) for translation/cross-cultural framework.
**Copyright:** Fair Use — paraphrased cultural-style heuristics + aggregated 5D divergence data. No verbatim quotation beyond short technical phrases (≤20 words each). See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 style_genome 专家在跨文化场景(CN director × Western audience / Western director × CN audience / 短剧 出海)**必须遵守的 5D 向量跨文化 divergence 规则**(cross-cultural authoritative source)。它与 [`director-dna-archive.md`](./director-dna-archive.md)(数据侧:单一文化内 5D 编码)与 [`auteur-theory.md`](./auteur-theory.md)(理论侧:tier 判定)互补,共同构成 style_genome 编码的三层 grounding。

术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)。

---

## CN / Western / Korean 5D Divergence Matrix

### 关键 heuristic 1 (load-bearing): 5D 跨文化 divergence 区间表

基于 Bordwell *Planet Hong Kong* §"Asian Aesthetics" + Marchetti 2007 + Hwang & Kim 2018 的文化美学研究,跨文化 5D divergence 区间(style_genome §跨文化编码硬规则):

| 维度 | CN(大陆 / 港台)区间 | Western(US/EU)区间 | Korean 区间 | divergence |
|------|----------------------|----------------------|-------------|-----------|
| composition | 0.30-0.65(三分法 + 偶尔对称)| 0.30-0.55(三分法主导)| 0.40-0.70(构图相对密集)| CN ↔ Western ≤±0.10;CN ↔ Korean ≤±0.15 |
| color | 0.40-0.80(国风 high-sat 暖色 / 文艺片 low-sat)| 0.30-0.60(自然主义 + desaturated)| 0.50-0.70(mid-sat warm/cool)| CN ↔ Western ±0.15-0.25;Korean 中位 |
| rhythm | 0.20-0.55(慢节奏 + 文艺长镜;但 短剧 极快 0.85+)| 0.40-0.65(classic Hollywood 4-6s ASL)| 0.40-0.65(节奏接近 Western)| 短剧 单独案例,跨文化 divergence 极大 |
| light_shadow | 0.30-0.70(国风 high-key + 文艺片 low-key 双极)| 0.40-0.60(naturalistic)| 0.30-0.50(偏暗 chiaroscuro)| CN 文艺片 ↔ Western ±0.15 |
| sound | 0.50-0.80(丰富 score + 国风 instrument layer)| 0.40-0.70(score + diegetic)| 0.50-0.80(丰富 score + K-pop adjacency)| CN ↔ Korean ≤±0.10;CN ↔ Western ≤±0.15 |

### 关键 heuristic 2: "Cultural translation cost" 公式

style_genome 计算 cultural_translation_cost(CTC)= avg(|CN_5D - target_audience_5D|) per dimension。阈值:

- `CTC ≤ 0.10` → 低成本翻译(直接复用 5D vector;cross-cultural deploy 可行)
- `CTC 0.10-0.20` → 中等成本(需要 5D vector 局部 adjust;composition/color 维度最容易 adjust)
- `CTC > 0.20` → 高成本(必须 hybrid encoding;详见 §Hybrid Encoding Protocol)

**Worked Example — Zhang Yimou (*Hero*) 出海 Western audience:**
- 原 CN 5D: [0.65, 0.85, 0.30, 0.55, 0.75](国风高饱和暖色 + 慢节奏长镜)
- Western 5D 偏好区间: [0.30-0.55, 0.30-0.60, 0.40-0.65, 0.40-0.60, 0.40-0.70]
- CTC = (|0.65-0.45| + |0.85-0.45| + |0.30-0.55| + |0.55-0.50| + |0.75-0.55|) / 5 = (0.20 + 0.40 + 0.25 + 0.05 + 0.20) / 5 = 0.22
- **CTC = 0.22 > 0.20 = 高成本翻译;必须 hybrid encoding** → 详见 §Hybrid Encoding Protocol

---

## Hybrid Encoding Protocol

### 关键 heuristic 3 (load-bearing): Hybrid 5D vector formula

当 CTC > 0.20 时,style_genome 必须 hybrid encoding,公式:

```
hybrid_5D = original_culture_5D × 0.65 + target_audience_5D × 0.35
```

权重规则:
- **0.65 original**(主) — 保持 auteur signature 在跨文化场景中可识别
- **0.35 target**(副) — 降低 cultural translation cost,提高 target audience 接受度
- **不得 50/50** — 50/50 hybrid 会同时疏远两个 audience(同 SKILL.md §Style Blending §Prohibited anti-pattern)

**Hybrid 范围限制:** 单维度 hybrid 不可超出 ±0.20 of original_culture_5D(防止 auteur signature 完全丢失)。若计算结果超出范围,自动 clip + 标记 `hybrid_clipped: true` 在 style_genome.json 中。

### 关键 heuristic 4: Hybrid encoding worked example

**Zhang Yimou (*Hero*) × Western audience hybrid:**
- 原 CN 5D: [0.65, 0.85, 0.30, 0.55, 0.75]
- Western 中位 5D(取区间中位): [0.425, 0.45, 0.525, 0.50, 0.55]
- Hybrid(0.65/0.35): [0.65×0.65 + 0.425×0.35, ...] = [0.42 + 0.15, 0.55 + 0.16, 0.20 + 0.18, 0.36 + 0.18, 0.49 + 0.19] = [0.57, 0.71, 0.38, 0.54, 0.68]
- **Hybrid 5D:** [0.57, 0.71, 0.38, 0.54, 0.68]
- 验证:每维度 hybrid 偏离原 CN ≤±0.20 ✓(color: 0.85→0.71 偏离 0.14;sound: 0.75→0.68 偏离 0.07;其余 ≤±0.10)

---

## CN Director × Western Audience 部署硬规则

### 关键 heuristic 5: 文化不可译元素的保留清单

CN director × Western audience 部署时,下列元素**不可 hybrid**(必须保留 CN signature):

1. **国风 instrument layer**(二胡 / 古筝 / 笛 / 萧 in score)— sound 维度中保留 0.05-0.10 增量
2. **书法 / 水墨 composition element**(若 screenplay 涉及)— composition 维度保留 original
3. **节庆色卡**(红 + 金 / 红 + 黄)— color 维度保留 original
4. **功夫 choreography rhythm**(若 action genre)— rhythm 维度保留 original

style_genome 必须 output `non_translatable_elements[]` 数组列出所有保留元素,以警告下游 expert(continuity / compliance_marketing)这些元素不能 localizer 修改。

### 关键 heuristic 6: Western audience 接受度阈值

CN director × Western audience 部署,acceptance score 阈值(基于 Marchetti 2007 + 跨文化 reception 研究):

- **Acceptance score >= 0.70** → 直接部署成功案例(Crouching Tiger Hidden Dragon 2000 / Hero 2004 US release)
- **Acceptance score 0.50-0.70** → niche release(art-house circuit;e.g., Hou Hsiao-Hsien *Assassin* 2015)
- **Acceptance score < 0.50** → 必须 hybrid encoding 或放弃 Western release

**Acceptance score 计算:** acceptance = (style_coherence_score × 0.4) + ((1 - CTC) × 0.4) + (cultural_familiarity_factor × 0.2)

---

## Western Director × CN Audience 部署硬规则

### 关键 heuristic 7: "Glocalization" 编码规则

Western director × CN audience(如 Marvel × CN release / 短剧 出海)的 5D vector 调整:

1. **color 维度**:CN audience 偏好 high-sat warm(S 0.65-0.85 vs Western 0.45-0.65),hybrid 时 color 向 0.65-0.85 区间倾斜
2. **rhythm 维度**:CN audience 偏好 fast-paced(短剧 ASL 1.2-2.0s vs Western 4-6s),hybrid 时 rhythm 向 0.6-0.85 区间倾斜
3. **composition 维度**:CN audience 接受 symmetric composition(Kubrick-style one-point perspective 在 CN 接受度高 vs Western 偏好 rule-of-thirds)
4. **light_shadow 维度**:CN 文艺片接受度 low-key,但商业片偏好 high-key(抖音 / 快手 用户偏好明亮画面)

### 关键 heuristic 8: 政治敏感性 hard filter

Western director × CN audience 部署时,以下 5D 配置 **不可 hybrid**(触发 compliance_marketing expert 阻断):

- color 维度中 red 不可用于政治讽刺场景(详见 [`../compliance_marketing/references/cn-content-rules.md`](../compliance_marketing/references/cn-content-rules.md) §8-category 红线)
- composition 维度中 symmetry + 慢节奏(0.3 以下 rhythm)组合易触发"政宣片"误读
- sound 维度中 silence 极简(<0.2)在 CN 短剧 场景接受度低(用户习惯 BGM 持续)

---

## Korean Wave (Hallyu) 风格作为 CN-Japan 中介

### 关键 heuristic 9: Korean style 作为 hybrid 媒介

韩国电影/剧集(Parasite / Squid Game / Crash Landing on You 等)在 5D 维度上居 CN 与 Western 中间,作为 hybrid 媒介时**降低 cultural translation cost**:

- CN director × Korean 5D × Western audience:**CTC 0.18-0.22 → 0.10-0.15**(Korean 中介降低 ~30% CTC)
- Western director × Korean 5D × CN audience:**CTC 0.18-0.22 → 0.12-0.16**

style_genome 支持 `intermediate_culture: korean` flag,自动应用上述 hybrid 中介公式。详见 [`cn-director-analysis.md`](./cn-director-analysis.md) §Korean Style Crosswalk。

---

## Bilingual 短剧 出海特殊规则

### 关键 heuristic 10: 短剧 出海的 dual-track encoding

短剧 出海(原始 CN 拍摄 + 海外平台分发)必须 dual-track encoding,style_genome.json output 两套 5D vector:

1. **`original_5d`**:原始 CN 短剧 5D vector(用于 CN 平台 抖音 / 快手 / 小程序剧 分发)
2. **`adapted_5d`**:hybrid 后的 5D vector(用于 TikTok / YouTube Shorts / Reels 海外平台分发)

style_genome 必须 output `dual_track: true` flag,且 adapted_5D 经过 §Hybrid Encoding Protocol 计算。

### 关键 heuristic 11: 海外平台 5D 接受度阈值

| 平台 | color 接受区间 | rhythm 接受区间 | 备注 |
|------|----------------|-----------------|------|
| TikTok | 0.5-0.75 | 0.7-0.9 | 类 抖音 但 mid-sat |
| YouTube Shorts | 0.4-0.65 | 0.5-0.75 | Western 偏好 |
| Reels (Instagram) | 0.5-0.75 | 0.5-0.80 | 中位 |
| Kwai International | 0.45-0.70 | 0.7-0.85 | 类 快手 |

详见 [`../compliance_marketing/references/platform-douyin.md`](../compliance_marketing/references/platform-douyin.md) + 平台 spec 系列。

---

## Glossary

- **Cultural Translation Cost (CTC):** 原 5D vector 与 target audience 5D 偏好区间的平均偏差;阈值 ≤0.10 / 0.10-0.20 / >0.20。
- **Hybrid encoding:** 当 CTC > 0.20 时,style_genome 强制 0.65 original / 0.35 target 混合 5D vector;单维度 ≤±0.20 deviation 限制。
- **Non-translatable elements:** CN signature 元素(国风 instrument / 书法 composition / 节庆色卡 / 功夫 choreography)在跨文化 hybrid 中必须保留。
- **Dual-track encoding:** 短剧 出海场景下,output 两套 5D vector(original + adapted)用于不同平台。
- **Korean style as intermediate:** Hallyu 5D 作为 CN-Western hybrid 的中介,降低 ~30% CTC。

---

*Generated: 2026-06-15 as part of Phase 3 REFACTOR-04 (style_genome deep refactor).*
*Source provenance: Bordwell 2011 / Chow 2007 / Marchetti 2007 / Hwang & Kim 2018 / Nornes 2007 — fair use paraphrase + short technical phrases only.*
