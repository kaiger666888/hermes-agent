# Genre DNA Taxonomy — 12-Genre 5D Vector Ranges + Signature Shot Patterns

**Source:** Aggregated from public film-studies genre theory — Altman *Film/Genre* (BFI, 1999), Grant *Film Genre Reader* (4th ed, Univ Texas Press, 2013) — plus 公开 短剧 创作指南 (MCN 公开运营报告 + 创作者公开访谈 aggregated). See [LICENSE.md](./LICENSE.md).
**Copyright:** Fair Use — 5D range encoding is original Hermes analytical work; genre signature shot patterns paraphrased from public scholarship. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 是 style_genome 专家的 **genre 档案唯一真相源** —— 12 个题材(横屏传统 + 短剧 平台特定)的 5D vector 区间、签名镜头模式、genre-locked metric thresholds、短剧 平台 genre divergence。SKILL.md body 仅引用本 ref,不重新定义数值(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) single-source-of-truth 规则)。术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)。

12 题材按"传统 film-studies classification"(Altman / Grant)+ "短剧 平台特定 classification"(MCN 公开观察)的双轴组织。前 10 个是传统题材;后 2 个(短剧-男频-revenge / 短剧-女频-romance)是 CN 短剧 平台特有的题材分化(详见 §短剧 Genre Divergence)。

---

## 12-Genre Taxonomy with 5D Ranges

### 关键 heuristic 1 (load-bearing): 12-genre 5D vector 区间表

每个题材的 5D vector 推荐区间(per [`director-dna-archive.md`](./director-dna-archive.md) §5D Encoding Protocol;区间是 *estimated* 聚合观察):

| # | Genre | Composition | Color | Rhythm | Light/Shadow | Sound | 典型导演参考 |
|---|-------|-------------|-------|--------|--------------|-------|--------------|
| 1 | **Action** | 0.4-0.7 | 0.5-0.8 | **0.7-1.0** | 0.3-0.6 | 0.7-0.9 | Bay / Snyder / Miller |
| 2 | **Romance** | 0.3-0.5 | **0.6-0.9** | 0.2-0.4 | 0.4-0.7 | 0.6-0.8 | Wong Kar-wai / Jenkins |
| 3 | **Horror** | 0.5-0.8 | 0.1-0.4 | 0.3-0.6 | **0.6-1.0** | 0.5-0.8 | Aster / Wan / Carpenter |
| 4 | **Sci-Fi** | 0.3-0.5 | 0.4-0.6 | 0.3-0.6 | 0.5-0.7 | 0.6-0.9 | Villeneuve / Kubrick |
| 5 | **Mystery / Thriller** | 0.4-0.6 | 0.3-0.5 | 0.4-0.7 | 0.5-0.8 | 0.5-0.7 | Fincher / Hitchcock |
| 6 | **Comedy** | 0.3-0.6 | 0.5-0.8 | 0.4-0.7 | 0.3-0.5 | 0.5-0.7 | Anderson / Wright |
| 7 | **Drama** | 0.3-0.5 | 0.4-0.7 | 0.3-0.5 | 0.4-0.7 | 0.5-0.7 | Bergman / PTA |
| 8 | **Animation** | 0.4-0.6 | 0.6-0.9 | 0.3-0.6 | 0.2-0.5 | 0.6-0.9 | Miyazaki / Pixar |
| 9 | **Documentary** | 0.4-0.6 | 0.4-0.6 | 0.3-0.5 | 0.4-0.6 | 0.3-0.5 | Wiseman / Morris |
| 10 | **Fantasy** | 0.4-0.6 | 0.6-0.8 | 0.4-0.6 | 0.4-0.7 | 0.6-0.9 | del Toro / Jackson |
| 11 | **短剧-男频-revenge** | 0.4-0.6 | 0.5-0.7 | **0.7-0.9** | 0.4-0.6 | 0.7-0.9 | 短剧 公开观察 |
| 12 | **短剧-女频-romance** | 0.3-0.5 | **0.7-0.9** | 0.4-0.6 | 0.5-0.7 | 0.6-0.8 | 短剧 公开观察 |

**关键 heuristic 2:** genre 5D 区间是**区间**,不是点值。style_genome 在 encoding 时,应根据具体 director + 具体作品 narrative 在区间内取点。例如 Action 的 rhythm 区间是 0.7-1.0;若选择 Bay 风格则取 0.9,若选择 George Miller 的 *Mad Max: Fury Road* 则取 0.8(略慢但仍 in-range)。

### Genre 5D 与 Director 5D 的关系

Genre 5D 区间与 [`director-dna-archive.md`](./director-dna-archive.md) 的 director 5D 向量通过以下规则组合:

- **Director within genre range** → "导演风格符合题材规范"(典型情况)
- **Director partially outside** → "导演带来个人特色"(aesthetic risk 但可能突围)
- **Director significantly outside** → "题材-导演冲突"(需 user explicit confirm)

**关键 heuristic 3:** 例如 Wes Anderson (color = 0.8) 应用到 Action genre (color = 0.5-0.8) → 处于区间边缘,带来 Wes Anderson 风格化 action (如 *The French Dispatch* chase scenes)。

---

## Genre Signature Shot Patterns

每个题材的 3+ 签名镜头模式(从 Altman / Grant 影评学 + 短剧 平台公开观察 aggregated):

### 1. Action — 3+ concrete examples

- **Fast cuts + handheld** —— 1.0-2.5s avg shot length (per [`director-dna-archive.md`](./director-dna-archive.md) Bay/Snyder/Greengrass 标志)
- **Wide + color contrast** —— 主体高饱和 + 背景去饱和(Bay orange-teal 经典)
- **Cut on action** —— 见 [`../editor/references/classical-editing-rhythm.md`](../editor/references/classical-editing-rhythm.md) §Cut on Action(-70% viewer 察觉率)
- **Concrete examples:** *Mad Max: Fury Road* (Miller) / *John Wick* (Stahelski) / *Mission: Impossible – Fallout* (McQuarrie)

### 2. Romance — 3+ concrete examples

- **Medium close-ups** —— 1.5-3.0s avg shot length,情感面部聚焦
- **Slow pacing + warm tones** —— color = 0.7-0.9,warm/amber palette 主导
- **Soft focus + shallow DoF** —— 主体清晰 + 背景模糊
- **Concrete examples:** *In the Mood for Love* (Wong Kar-wai) / *Moonlight* (Jenkins) / *Before Sunrise* (Linklater)

### 3. Horror — 3+ concrete examples

- **Low-key lighting** —— light_shadow = 0.6-1.0,chiaroscuro 主导
- **Jump scares + tight framing** —— sudden cut + CU on subject reaction
- **Slow build + sudden release** —— pacing 从 0.3 (build) 跳到 0.7 (release)
- **Concrete examples:** *Hereditary* (Aster) / *The Conjuring* (Wan) / *The Thing* (Carpenter)

### 4. Sci-Fi — 3+ concrete examples

- **Symmetric wide shots** —— composition = 0.3-0.5,环境尺度优先
- **Cool color palette + ambient sound** —— color = 0.4-0.6, sound = 0.6-0.9
- **Long takes** —— 0.3-0.6 ASL 略长于 action
- **Concrete examples:** *Blade Runner 2049* (Villeneuve) / *2001: A Space Odyssey* (Kubrick) / *Arrival* (Villeneuve)

### 5. Mystery / Thriller — 3+ concrete examples

- **Asymmetric composition** —— composition = 0.4-0.6
- **Desaturated palette + chiaroscuro** —— Fincher green-teal / Hitchcock B&W
- **Slow reveals** —— 关键信息通过 camera movement 逐步披露
- **Concrete examples:** *Se7en* (Fincher) / *Vertigo* (Hitchcock) / *Zodiac* (Fincher)

### 6. Comedy — 3+ concrete examples

- **Symmetric framing for punchlines** —— composition = 0.3-0.6
- **Bright palette + natural sound** —— light_shadow = 0.3-0.5
- **Whip pans / quick cuts** —— Edgar Wright-style timing(per [`director-dna-archive.md`](./director-dna-archive.md))
- **Concrete examples:** *Grand Budapest Hotel* (Anderson) / *Hot Fuzz* (Wright) / *Booksmart* (Oliveira)

### 7. Drama — 3+ concrete examples

- **Balanced 5D** —— 区间中部,无明显极端
- **Long takes + close-ups** —— 0.3-0.5 ASL,人物面部主导
- **Naturalistic palette** —— color = 0.4-0.7
- **Concrete examples:** *There Will Be Blood* (PTA) / *Scenes from a Marriage* (Bergman) / *Manchester by the Sea* (Lonergan)

### 8. Animation — 3+ concrete examples

- **Variable composition (hand-drawn freedom)** —— composition = 0.4-0.6
- **Vivid palette** —— color = 0.6-0.9 (Ghibli warmth / Pixar saturation)
- **Orchestral score** —— sound = 0.6-0.9 (Hisaishi / Giacchino / Newman)
- **Concrete examples:** *Spirited Away* (Miyazaki) / *Spider-Man: Into the Spider-Verse* (Persichetti) / *Coco* (Unkrich)

### 9. Documentary — 3+ concrete examples

- **Handheld naturalistic** —— composition = 0.4-0.6
- **Natural palette + ambient sound** —— color = 0.4-0.6, sound = 0.3-0.5
- **Interview + b-roll alternation** —— 标准 documentary grammar
- **Concrete examples:** *Hoop Dreams* (James) / *The Act of Killing* (Oppenheimer) / *O.J.: Made in America* (Edelman)

### 10. Fantasy — 3+ concrete examples

- **Painterly composition** —— composition = 0.4-0.6
- **Saturated palette + practical effects** —— color = 0.6-0.8
- **Sweeping score** —— sound = 0.6-0.9 (Shore / Williams / Beltrami)
- **Concrete examples:** *Pan's Labyrinth* (del Toro) / *LOTR* (Jackson) / *Shape of Water* (del Toro)

### 11. 短剧-男频-revenge —— 短剧 平台特定

- **Fast cuts (1.5-2.0s ASL)** —— rhythm = 0.7-0.9,爽感 driven pacing
- **High contrast + 主体强调** —— color = 0.5-0.7,主体高饱和 + 背景去饱和
- **慕强 POV (low-angle hero shots)** —— composition = 0.4-0.6,主角 dominance
- **Concrete examples:** 公开 *estimated* 短剧 平台观察 (见 §短剧 Genre Divergence)

### 12. 短剧-女频-romance —— 短剧 平台特定

- **Medium close-ups (2.0-3.0s ASL)** —— rhythm = 0.4-0.6,情感 breathing room
- **Warm saturated palette** —— color = 0.7-0.9,暖色调 + 柔光
- **女主 POV (over-the-shoulder + CU)** —— composition = 0.3-0.5
- **Concrete examples:** 公开 *estimated* 短剧 平台观察 (见 §短剧 Genre Divergence)

---

## Genre-Locked Metric Thresholds

### 关键 heuristic 4: 每题材的 locked metric thresholds

不同题材对 quality metric 的要求不同(per Altman *Film/Genre* genre theory + 短剧 公开 创作指南):

| Genre | rhythm_coherence (editor) | emotional_arc score (screenplay) | tension_duration (% scene runtime) | style_consistency (style_genome) |
|-------|---------------------------|----------------------------------|------------------------------------|----------------------------------|
| Action | **≥ 0.85** | ≥ 0.70 | ≥ 50% | ≥ 0.85 |
| Romance | ≥ 0.75 | **≥ 0.80** | ≥ 40% | ≥ 0.85 |
| Horror | ≥ 0.75 | ≥ 0.75 | **≥ 75%** | ≥ 0.88 |
| Sci-Fi | ≥ 0.80 | ≥ 0.70 | ≥ 50% | ≥ 0.90 |
| Mystery/Thriller | ≥ 0.85 | ≥ 0.75 | ≥ 70% | ≥ 0.88 |
| Comedy | ≥ 0.85 (timing-critical) | ≥ 0.70 | ≥ 40% | ≥ 0.85 |
| Drama | ≥ 0.75 | ≥ 0.80 | ≥ 50% | ≥ 0.85 |
| Animation | ≥ 0.80 | ≥ 0.75 | ≥ 50% | ≥ 0.88 |
| Documentary | ≥ 0.70 | ≥ 0.70 | ≥ 40% | ≥ 0.80 |
| Fantasy | ≥ 0.75 | ≥ 0.75 | ≥ 60% | ≥ 0.85 |
| **短剧-男频-revenge** | **≥ 0.85** | ≥ 0.75 (爽点 density) | ≥ 60% | ≥ 0.85 |
| **短剧-女频-romance** | ≥ 0.75 | **≥ 0.85** (情感 hit rate) | ≥ 50% | ≥ 0.85 |

**关键 heuristic 5:** style_genome 在 encoding 短剧 时,必须根据题材选择对应的 metric threshold 表;**不能**用通用的 style_consistency ≥ 0.88 覆盖所有题材 —— Romance 题材对 emotional_arc 要求更高(≥ 0.80),Action 题材对 rhythm_coherence 要求更高(≥ 0.85)。

---

## 短剧 Genre Divergence

### 关键 heuristic 6 (load-bearing): 短剧 平台 genre 分化

CN 短剧 平台(抖音 / 快手 / 小程序剧 / 视频号)的 genre 分化**远超**横屏传统电影。本节是 style_genome 在 短剧 部署时的**唯一 genre divergence 真相源**(per [LICENSE.md](./LICENSE.md)):

### 平台 × 题材 × 5D 区间分化

| 平台 | 题材子分类 | composition | color | rhythm | light | sound | 典型 ASL |
|------|-----------|-------------|-------|--------|-------|-------|----------|
| **抖音-男频 revenge** | 战神归来 / 重生复仇 / 赘婿逆袭 | 0.4-0.6 | 0.5-0.7 | **0.7-0.9** | 0.4-0.6 | 0.7-0.9 | **1.5-2.0s** |
| **抖音-女频 romance** | 豪门虐恋 / 替身白月光 / 闺蜜背叛 | 0.3-0.5 | **0.7-0.9** | 0.4-0.6 | 0.5-0.7 | 0.6-0.8 | **2.0-3.0s** |
| **快手-草根 slice-of-life** | 草根共鸣 / 生活片段 / 段子剧 | 0.4-0.6 | 0.4-0.6 | 0.3-0.5 | 0.4-0.6 | 0.3-0.5 | **2.5-4.5s** |
| **小程序剧 180s drama** | 长集数连续剧 / 宫斗 / 复仇 | 0.4-0.6 | 0.6-0.8 | 0.4-0.6 | 0.5-0.7 | 0.6-0.8 | **2.0-3.0s** |
| **视频号 hybrid** | 混合题材 | 0.4-0.6 | 0.5-0.7 | 0.5-0.7 | 0.4-0.6 | 0.6-0.8 | 1.5-2.5s |

### 短剧 Genre Divergence 的关键驱动因素

| 驱动 | 影响 | 解释 |
|------|------|------|
| **平台算法权重** | 高 | 抖音 推荐 算法权重 [完播率](../../_shared/glossary.md#完播率-completion-rate) ~35% *estimated*(见 [`../compliance_marketing/references/platform-specs-douyin.md`](../compliance_marketing/references/platform-specs-douyin.md) §推荐机制);高完播率需要快节奏(rhythm 高)→ 抖音-男频 revenge ASL 1.5-2.0s。 |
| **观众期待** | 高 | [男频](../../_shared/glossary.md#男频-male-oriented-channel) revenge 观众期待"快节奏爽感",[女频](../../_shared/glossary.md#女频-female-oriented-channel) romance 观众接受"慢节奏情感"。 |
| **竖屏 9:16 约束** | 中 | [竖屏](../../_shared/glossary.md#竖屏-vertical-screen-916) 约束压缩构图 → composition 区间窄(0.3-0.6);横屏能到 0.1-1.0。 |
| **付费转化 ([付费卡点](../../_shared/glossary.md#付费卡点-paid-conversion-trigger))** | 高 | [小程序剧](../../_shared/glossary.md#小程序剧-mini-program-drama) 180s drama 需要在 [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) 处放置悬念,emotion_curve 峰值必须 align 在 60-80% 单集 runtime。 |

### 短剧 Genre Divergence 的 5D 派生规则

style_genome 在 短剧 部署时,执行以下派生:

1. **若平台已知**(抖音 / 快手 / 小程序剧 / 视频号) → 直接查表 §平台 × 题材 × 5D 区间分化
2. **若题材已知但平台未知** → 用 genre 5D 区间(§12-Genre Taxonomy)+ §短剧 Genre Divergence 的派生 baseline
3. **若题材 + 平台都不明确** → 警告 USER: "短剧 部署需明确题材 + 平台,否则 5D encoding 风险高";用通用 短剧 baseline (rhythm 0.5-0.7 / color 0.5-0.7)

**关键 heuristic 7:** 短剧 Genre Divergence 是 cross-cultural localization caveat 的具体化(per [`cross-cultural-style.md`](./cross-cultural-style.md) §Localization Caveat for 短剧)。直接将 Western director(如 Tarantino rhythm 0.6)套到 抖音-男频 revenge(rhythm 0.7-0.9)需要 user confirm + ASL adjustment。

---

## Genre Blending Rules

### 关键 heuristic 8: Genre blending 与 Director blending 的区别

style_genome 在 SKILL.md §Style Blending Protocol 中定义了 director blending(`dominant × 0.7 + recessive × 0.3`)。Genre blending 是**另一种** blending,需要注意以下区别:

| Blending 类型 | 主导方 | 冲突解决 | Enhancement 规则 |
|---------------|--------|----------|------------------|
| **Director blending** | 具体导演 | dominant-overwrite (opposite direction) | weighted average (same direction) |
| **Genre blending** | genre 区间 | dominant-genre 区间内取点 + recessive-genre 提供调味 | 区间重叠部分 = enhancement zone |

**关键 heuristic 9:** 例如 blending Action (rhythm 0.7-1.0) 与 Sci-Fi (rhythm 0.3-0.6):
- 冲突维度:rhythm 区间不重叠 → dominant-genre (Action) 区间内取点, recessive-genre (Sci-Fi) 提供 composition / color 调味
- Enhancement 维度:Action 与 Sci-Fi 在 composition 上都偏 symmetric (0.3-0.5) → enhancement zone = 0.3-0.5

### Genre blending 的合规检查

style_genome 在执行 genre blending 时,必须验证:

1. **dominant-genre 区间完整性** —— dominant-genre 的 5D 区间不被 recessive-genre 突破超过 ±0.10
2. **recessive-genre signature elements** —— 至少 2 个 recessive-genre signature elements 被注入(如 Action 主导 + Romance 调味 → 注入 medium close-up + warm tones)
3. **metric threshold alignment** —— 使用 dominant-genre 的 metric threshold 表(§Genre-Locked Metric Thresholds),不混用
4. **user confirm 跨 Tier blending** —— 若 blending 涉及跨 Tier(Hollywood blockbuster × European art house),需 user explicit confirm

### Genre blending 的反模式

- **Genre 50/50 blending** —— 不指定 dominant genre,与 director blending 同理(per SKILL.md §What NOT to do)
- **Metric threshold 混用** —— 例如 Action 主导 + Romance 调味,但使用 Romance 的 emotional_arc ≥ 0.80 threshold(应该用 Action 的 ≥ 0.70)
- **跨平台 genre divergence 冲突** —— 例如将 抖音-男频 revenge(rhythm 0.7-0.9)与 快手-草根(rhythm 0.3-0.5)blending,平台冲突需 user resolve

---

## Genre Selection Workflow

style_genome 在 SKILL.md §Workflow Step 1 (Director Selection) 之前应有 **Genre Selection** 步骤(本 ref 补充,SKILL.md 后续细化):

```
Step 0a: Genre Selection (在 Director Selection 前)
├── 用户明确指定 genre? → 直接用,查 §12-Genre Taxonomy 表
├── 用户未指定但指定 director?
│   └── 查 director 5D 向量,匹配最接近的 genre 区间(可能多个)
│       └── 多个候选 genre 时,user confirm 优先级
├── 用户未指定 genre 也未指定 director?
│   └── 警告 USER: "需要 genre 或 director 锚定,否则 5D encoding 风险高"
└── 短剧 部署?
    └── 强制要求 platform + genre 子分类(抖音-男频 / 抖音-女频 / etc.)
        └── 查 §短剧 Genre Divergence 的平台 × 题材 × 5D 区间表

Step 0b: Genre-locked metric threshold 加载
├── 加载 §Genre-Locked Metric Thresholds 对应行
└── 后续 SKILL.md §Quality Thresholds 验证使用此 genre-specific threshold
```

**关键 heuristic 10:** Genre Selection 是 Director Selection 的前置步骤 —— 没有 genre 锚定,director 5D encoding 风险高(导演可能跨多个 genre)。短剧 部署时 genre + platform 双锚定是硬要求。

### Genre × Director compatibility matrix

style_genome 在 Director Selection (Step 1) 后,应验证 director 5D 与 genre 5D 的兼容性:

| 兼容等级 | 定义 | 处理 |
|----------|------|------|
| **Strong fit** | Director 5D 全部落在 genre 区间内 | 直接部署,无 warning |
| **Edge fit** | Director 5D 有 1-2 维度落在 genre 区间边缘(±0.05) | 部署 + 风格化提示("该导演带来 genre atypical 元素") |
| **Conflict** | Director 5D 有维度显著超出 genre 区间(> ±0.15) | user explicit confirm + 调整 director 5D(encoding 时取 director-genre 重叠区间的中点) |

**关键 heuristic 11:** 例如 Wes Anderson (color = 0.8) 应用到 Action genre (color = 0.5-0.8):
- Wes Anderson color = 0.8 落在 Action color 区间 0.5-0.8 的**边缘** → Edge fit
- 处理:部署 + 风格化提示;无需 user confirm

例如 Hou Hsiao-hsien (rhythm = 0.1) 应用到 Action genre (rhythm = 0.7-1.0):
- Hou rhythm = 0.1 显著超出 Action rhythm 区间 → Conflict
- 处理:user explicit confirm + 取 0.4-0.5 重叠区间(encoding 时不要照搬 Hou rhythm)

---

## Cross-References

- [`director-dna-archive.md`](./director-dna-archive.md) §5D Encoding Protocol —— 5D 编码协议(本 ref 的数值化标准与本 ref 一致)
- [`director-dna-archive.md`](./director-dna-archive.md) §Director Grouping by Dominant Trait —— 导演主导维度分组(genre 5D 区间与之协同)
- [`cross-cultural-style.md`](./cross-cultural-style.md) §Localization Caveat for 短剧 —— Western director DNA 套用 短剧 需 ASL 调整
- [`cn-director-analysis.md`](./cn-director-analysis.md) §短剧 Director DNA Candidates —— 短剧 平台特有的导演 DNA 候选
- [`auteur-theory.md`](./auteur-theory.md) §Sarris 3-Criteria Rubric —— genre 内的导演判定仍需 auteur criteria
- [`../editor/references/cn-cutting-rhythm.md`](../editor/references/cn-cutting-rhythm.md) §Cut-Density Windows by Platform/Genre —— 短剧 平台 cut-density 阈值与本 ref 的 rhythm 区间对齐
- [`../compliance_marketing/references/platform-specs-douyin.md`](../compliance_marketing/references/platform-specs-douyin.md) §推荐机制 —— 平台算法权重解释 短剧 genre divergence 驱动因素
- [`../../_shared/glossary.md`](../../_shared/glossary.md) —— [男频](../../_shared/glossary.md#男频-male-oriented-channel) / [女频](../../_shared/glossary.md#女频-female-oriented-channel) / [完播率](../../_shared/glossary.md#完播率-completion-rate) / [爆款](../../_shared/glossary.md#爆款-viral-formula-explosive-hit) / [竖屏](../../_shared/glossary.md#竖屏-vertical-screen-916) / [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) / [付费卡点](../../_shared/glossary.md#付费卡点-paid-conversion-trigger) / [小程序剧](../../_shared/glossary.md#小程序剧-mini-program-drama) 术语定义
- [`../style_genome/SKILL.md`](../SKILL.md) §Quality Thresholds —— genre-locked metric thresholds 是 SKILL.md 阈值的 genre-specific 细化

---

## Refresh Cadence

- **每季度复核一次**(下次:2026-09)。
- **复核内容:** 12-genre 5D 区间是否仍是 2026-Q2 甜区;短剧 平台 genre divergence(尤其是 抖音 / 快手 算法权重)是否有新数据;genre-locked metric thresholds 是否需要调整。
- **复核来源:** MCN 公开运营报告 + 平台创作者中心运营指南 + 创作者公开访谈 + 学术 genre theory 新出版物。
- **不需要更新:** 传统 genre 1-10 的 5D 区间(基于经典 film-studies,稳定)。

---

## Drift Signals

若以下信号出现,本 ref 需要更新:

- **新 genre 涌现:** 若出现新的 genre (如 AI 漫剧 [漫剧](../../_shared/glossary.md) 的新子分类)需要 style_genome 支持,需补充进 12-genre 表。
- **平台 genre 漂移:** 若行业统计显示 抖音-男频 revenge 的 rhythm 甜区从 0.7-0.9 漂移到 0.5-0.7(节奏放慢),需更新 §短剧 Genre Divergence。
- **新平台涌现:** 若新平台(如 B站 竖屏 / 小红书 视频)需要 genre divergence 数据,需补充进 §平台 × 题材 × 5D 区间分化表。
- **genre-locked metric thresholds 漂移:** 若 A/B 测试显示某 genre 的 threshold 需要调整(如 Action rhythm_coherence 需要从 0.85 调整到 0.90),需更新 §Genre-Locked Metric Thresholds。
- **AI 漫剧 备案 触发:** 若新的 [备案](../../_shared/glossary.md#备案-filing-regulatory-filing) 监管要求影响 genre divergence(如某些题材被限制),需补充 §短剧 Genre Divergence 的 compliance 注释。

---

> **Disclaimer:** 12-genre 5D 区间与 短剧 平台 genre divergence 阈值是 Hermes Agent 基于 public film-studies genre theory + MCN 公开运营报告 aggregated 的**分析性编码**(`*estimated*`)。所有数值是 style_genome 专家在 genre encoding 时的**唯一真相源** —— SKILL.md body 与其他 refs 必须跨链引用,不得重新定义数值。
