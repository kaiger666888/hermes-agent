# SCAMPER — Bob Eberle 7-Verb Variation Engine Stacked on style_blend for 短剧 / 微电影

**Source:** Bob Eberle *SCAMPER: Creative Thinking & Brainstorming* (1971, Prufrock Press Inc.; based on Alex F. Osborn's creative-thinking checklist from *Applied Imagination* 1953, Charles Scribner's Sons). The 7 verbs (Substitute / Combine / Adapt / Modify / Put-to-other-use / Eliminate / Reverse) are widely-referenced creativity-pedagogy terminology; this ref paraphrases the verb definitions only — no verbatim reproduction of Eberle's prose, examples, or chapter-level scaffolding. The 35 short-drama variation recipes are original Hermes Agent analytical work building on the paraphrased 7 verbs.
**Copyright:** Fair Use — paraphrased 7-verb methodology skeleton + original 35-recipe table + original LLM prompt templates + original JSON schema. No reproduction of Eberle's example cases, classroom exercises, or chapter walkthroughs. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-18
verified_date: 2026-06

---

## Summary

SCAMPER 是 Bob Eberle 在 1971 年系统化的 **7 动词变体引擎**(variation engine),基于 Alex Osborn 1953 年的创意思考清单(creative-thinking checklist)改编。7 动词分别对应 7 种「对已有方案做单点变体」的认知操作:**Substitute** / **Combine** / **Adapt** / **Modify** / **Put-to-other-use** / **Eliminate** / **Reverse**。

本 ref 把 SCAMPER **叠加**(stacked,不替代)到 [`style_genome`](../SKILL.md) 的 `style_blend` 子任务上 —— 当 style_genome 已用 [`auteur-theory.md`](./auteur-theory.md) 判定 director tier、用 [`genre-dna-taxonomy.md`](./genre-dna-taxonomy.md) 圈定 genre 5D 区间、用 [`cross-cultural-style.md`](./cross-cultural-style.md) 算完 hybrid encoding 后,SCAMPER 在这个已锁定的 style_genome 基础上展开 **7 个变体候选**,让下游(用户 / `hook_retention` / `prompt_injector`)有选择空间,而不是只能消费单一输出。

**SCAMPER 的角色边界(load-bearing):** SCAMPER 是**变体引擎**(variation engine),不是**分类系统**(classification system)。`auteur-theory` 决定 director tier(Pantheon / Modern Auteur / Operator),`genre-dna-taxonomy` 决定 genre 5D 区间 —— 这两个是分类系统。SCAMPER 在分类结果确定后才介入,系统化生成 7 个 style_blend 变体。SCAMPER 不重写 tier 判定、不动 genre 5D 区间、不替代 auteur-theory 的 Sarris 3-criteria。

术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)(Phase 21 SCAMPER-04 新增 8 条)。

---

## SCAMPER Method — Origin & Definition

**Osborn 1953 溯源:** Alex F. Osborn 在 *Applied Imagination: Principles and Procedures of Creative Thinking* (1953, Scribner) 系统化了 brainstorming 方法论,并提出 83-item "creative-thinking checklist"作为克服创作僵局的辅助工具。这份 checklist 在 1950s-1960s 广为流传,但 83 项对实操过载。

**Eberle 1971 系统化:** Bob Eberle 在 *SCAMPER: Creative Thinking & Brainstorming* (1971) 把 Osborn 的 83 项压缩成 7 个首字母助记的 verb 类别 —— **S**ubstitute / **C**ombine / **A**dapt / **M**odify / **P**ut-to-other-use / **E**liminate / **R**everse。每个 verb 类别涵盖若干 Osborn 原 checklist 条目(如 Modify 含 Magnify / Minify 两个子动作;Reverse 含 Rearrange / Reverse 两个子动作)。SCAMPER 的助记设计让创意思考能在 60 秒内被回忆与套用。

**与 style_genome 的契合点:** style_genome 的 5D 向量(composition / color / rhythm / light_shadow / sound)天然适配 SCAMPER 的「单点变体」操作 —— 7 动词各对应一种对 5D 向量的扰动方式,变体候选可量化为 5D diff。这与 Ingermanson 雪花法的过程性展开(Phase 19)、E-Konte 的格式性标注(Phase 20)在方法论层级**互补不重叠** —— 雪花法管「叙事怎么展开」、E-Konte 管「分镜怎么标注」、SCAMPER 管「风格怎么变体」。

---

## The 7 SCAMPER Verbs

### S — Substitute (替代)

**CN:** 替代 —— 把 style_genome 的某个元素(director / genre / 5D 维度值 / signature element)替换为另一个同类元素。
**EN:** Replace one component of the style genome (director reference / genre label / 5D value / signature element) with another of the same kind.
**操作目标:** 5D 向量任一维度 / director 引用 / signature element。
**变体动作:** `original_value → substitute_value`(标量替换)。
**短剧 / 微电影 适用场景:** 同 genre 下换导演(如 男频复仇 Wong Kar-wai color → Nolan color)、换色彩冷暖、换节奏快慢。

### C — Combine (组合)

**CN:** 组合 —— 把 style_genome 的两个不同元素(或两个不同 director / genre 的 5D 向量)合并成单一混合方案。
**EN:** Merge two distinct elements of the style genome (or 5D vectors from two directors / genres) into a single hybrid scheme.
**操作目标:** 两个 director 5D 向量 / 两个 genre 5D 区间 / 两个 signature elements。
**变体动作:** `vector_a × weight + vector_b × (1 - weight)`(向量加权融合,需遵守 style_genome §Style Blending 的 dominant/recessive 规则,不允许 50/50)。
**短剧 / 微电影 适用场景:** 男频复仇 × 女频甜宠 → 双主角复仇爽剧;快手草根 × 抖音男频 → 双平台分发公式。

### A — Adapt (适配)

**CN:** 适配 —— 把一个不同领域的元素(如游戏 / 文学 / 音乐 / 古典艺术)的风格特征借入 style_genome,转化为可编码的 5D 变动。
**EN:** Borrow a stylistic feature from another domain (game / literature / music / classical art) and translate it into encodable 5D variation.
**操作目标:** 跨领域元素的 5D 翻译。
**变体动作:** `domain_signal → 5D_translation`(如 "FPS 游戏第一人称视角" → composition +0.3 + rhythm +0.2)。
**短剧 / 微电影 适用场景:** 文学名著改编短剧(《红楼梦》改编 → composition +0.2 + light_shadow -0.1)、游戏 IP 改编(《黑神话》改编 → rhythm +0.3 + sound +0.2)。

### M — Modify / Magnify / Minify (修改 / 放大 / 缩小)

**CN:** 修改 —— 对 5D 向量的某个维度做幅度调整(Magnify 放大 / Minify 缩小)。
**EN:** Adjust the magnitude of a single 5D dimension(Magnify increases / Minify decreases).
**操作目标:** 5D 单一维度的 ±delta。
**变体动作:** `value → value ± delta`(标量调整,典型 delta ∈ [0.15, 0.35] 以触发 style_genome §Deviation Detection 的 warning_threshold)。
**短剧 / 微电影 适用场景:** color Magnify +0.3 → 高饱和度复仇爽剧;rhythm Minify -0.3 → 慢节奏治愈向微电影。

### P — Put to other use (另作他用)

**CN:** 另作他用 —— 把现有 style_genome 应用到完全不同的 runtime / 形态 / 受众(原 style_genome 设计为 男频 90s 单集 → 改用为 女频 60s 单集)。
**EN:** Apply the existing style_genome to a completely different runtime / form / audience than it was designed for.
**操作目标:** runtime × 受众 × 平台 元组。
**变体动作:** `(runtime, audience, platform) → (new_runtime, new_audience, new_platform)`。
**短剧 / 微电影 适用场景:** 抖音 90s 单集风格 → 微信小程序剧 180s 单集(扩展集长);男频复仇风格 → 女频甜宠(翻转受众);竖屏 9:16 → 横屏 16:9 微电影(改形态)。

### E — Eliminate (消除)

**CN:** 消除 —— 从 style_genome 中移除一个元素(signature element / 5D 维度的极端值 / 某个 genre feature),产生极简变体。
**EN:** Remove one element from the style_genome(signature element / extreme 5D value / genre feature)to produce a minimalist variant.
**操作目标:** signature element / 5D 极端值 / genre feature。
**变体动作:** `remove_element` 或 `value → neutral(0.5)`。
**短剧 / 微电影 适用场景:** 消除 signature close-up → 沉浸式第一人称视角;消除高饱和度 → 黑白微电影;消除 BGM → 纯环境音 ASMR 短剧。

### R — Reverse / Rearrange (反转 / 重排)

**CN:** 反转 —— 把 style_genome 的某个维度值取反(如 cool → warm / fast → slow);或重排 narrative 结构的 5D 表达顺序。
**EN:** Invert a 5D value(cool → warm / fast → slow);or rearrange the narrative-order 5D expression.
**操作目标:** 5D 向量取反 / signature element 顺序重排。
**变体动作:** `value → (1 - value)`(对称取反)或 `signature_order → reversed_order`。
**短剧 / 微电影 适用场景:** Wong Kar-wai 暖色调 → 冷色调悬疑改编;rhythm fast-cut → slow-cinema 艺术微电影;反转 Snyder beat 顺序(从结局开场倒叙)。

---

## SCAMPER × Style Genome Integration (Stacked on style_blend)

### 叠加不替代声明 (load-bearing)

SCAMPER 是**叠加层**(stacked layer),不是**替代层**(replacement layer)。本 ref 与 style_genome 现有逻辑的关系:

| 层级 | 子任务 | 输出 | SCAMPER 是否介入 |
|------|--------|------|-----------------|
| 分类系统 1 | auteur-theory director tier 判定 | `tier: Pantheon / Modern Auteur / Operator` | ❌ 不介入(tier 判定在 SCAMPER 之前) |
| 分类系统 2 | genre-dna-taxonomy 5D 区间 | `5D range per genre` | ❌ 不介入(区间在 SCAMPER 之前) |
| 分类系统 3 | cross-cultural-style hybrid encoding | `hybrid 5D vector` | ❌ 不介入(hybrid 在 SCAMPER 之前) |
| **变体引擎** | **SCAMPER 7 动词展开** | **`scamper_variants.json` (7 候选)** | **✅ 本 ref 介入** |
| 单一输出 | style_blend 单一 dominant/recessive 协议 | `style_blend_protocol.json` (1 输出) | ❌ 不替代(SCAMPER 是 style_blend 的扩展,不是替代) |

### 输入 / 处理 / 输出 三段式

**输入:** `style_genome.json`(已经过 auteur-theory + genre-dna + cross-cultural 三层分类确定的 5D 向量 + director reference + genre label)。

**处理:**
1. SCAMPER 引擎读取已锁定的 `style_genome.json` 作为 `original_genome`
2. 对 7 个 verb 各生成 1 个候选变体(每个 verb 应用其变体动作到 5D 向量)
3. 对每个变体计算 3 个推荐分数(详见 §Output Schema):
   - `novelty_score`:与 `original_genome` 的 5D 距离(越大越新)
   - `feasibility_score`:变体是否仍满足 genre 5D 区间约束 + director tier 兼容性
   - `alignment_score`:变体与用户原始意图(prompt 中声明的 runtime / 受众 / 平台)的匹配度

**输出:** `scamper_variants.json`(7 候选数组,详见 §Output Schema)。

### 触发条件

SCAMPER 变体引擎在以下任一条件下触发(由 style_genome SKILL.md `## SCAMPER Variation Layer` 子段落调用):

- **用户显式请求:** 用户输入「给 3-5 个候选风格」「我想看不同走向」等
- **hook_retention 消费:** `hook_retention` 在 `## SCAMPER × 5 爆款公式 Cross-Table` 中请求候选 hook 变体种子
- **用户不确定 dominant:** style_blend 在选 dominant director / genre 时,用户提供 2+ 候选,SCAMPER 自动展开 7 个组合
- **跨平台分发:** 用户要求一个 IP 在 抖音 / 快手 / 小程序剧 多平台分发,SCAMPER 展开 7 个平台适配变体

### 不触发条件

- auteur-theory tier 判定阶段(那是分类,不是变体)
- genre-dna 5D 区间圈定阶段(那是分类,不是变体)
- 用户只给 1 个 director + 1 个 genre + 明确不需要候选(style_blend 单一输出已足够)

---

## 35 Variation Recipes — 7 Verbs × 5 Gene Combinations

### 5 基因组合 (Gene Combinations)

以下 5 个 gene combinations 覆盖短剧 / 微电影最常见的形态组合,作为 SCAMPER 7 动词的展开目标。每个组合给出 `genre × mood × pacing × cast × runtime` 五元组:

| Combo ID | Genre | Mood | Pacing | Cast | Runtime | 典型平台 |
|----------|-------|------|--------|------|---------|----------|
| **C1** | 男频复仇 (male-revenge) | 压抑 → 释放 (suppress → release) | 1.5s avg shot | 单主角 | 90s 单集 | 抖音-男频 |
| **C2** | 女频甜宠 (female-romance) | 误解 → 揭露 → 圆满 (misunderstanding → reveal → resolution) | 2.0s avg shot | 男女双主角 | 60s 单集 | 抖音-女频 |
| **C3** | 悬疑烧脑 (suspense-mystery) | 多峰反转 (multi-peak reversal) | 2.5s avg shot | 多角色 (3-5) | 180s 单集 | 小程序剧-长集数 |
| **C4** | 微电影文艺 (arthouse-short) | 内省 → 顿悟 (introspection → epiphany) | 3-4s avg shot | 单主角 | 5-15min | YouTube Shorts / B站 |
| **C5** | 漫剧拟人化 (anthropomorphic-anime) | 情谊 → 冒险 (camaraderie → adventure) | 1.5-2.0s avg shot | 拟人主角 | 120s 单集 | 小程序剧-漫剧 |

### 7 × 5 = 35 Recipes

每个 recipe 用 `Verb-Combo` 编码(如 `S-C1` = Substitute 动词 × C1 基因组合)。每个 recipe 给出:输入摘要 / 变体动作 / 输出候选 5D 摘要 / 适用场景 / 反指示。

---

#### Substitute (S) 配方 S-C1 ... S-C5

**S-C1** (男频复仇 / Substitute color palette):
- **输入:** `composition=0.5, color=0.3(cool/desat), rhythm=0.7(fast), light_shadow=0.7(contrast), sound=0.7(LF rumble)`
- **变体动作:** Substitute `color=0.3 cool` → `color=0.8 warm/high-sat`(从冷色调压抑 → 暖色调爆发)
- **输出候选 5D:** `color=0.8, 其他保持`;novelty 0.50 / feasibility 0.85(C1 genre 允许 warm 变体)/ alignment 0.80(压抑 → 释放曲线契合)
- **适用场景:** 90s 单集「反转爆发型」男频短剧 —— 主角隐忍 60s 冷色调 → 反转瞬间切暖色调
- **反指示:** 60s 单集(信息密度过高,color shift 不易被感知)

**S-C2** (女频甜宠 / Substitute lighting style):
- **输入:** `light_shadow=0.7(contrast, dramatic)`(从男频沿用)
- **变体动作:** Substitute `light_shadow=0.7` → `light_shadow=0.2(soft/natural)`(软光女主甜宠)
- **输出候选 5D:** `light_shadow=0.2, 其他保持`;novelty 0.45 / feasibility 0.90(C2 genre 硬约束 soft light)/ alignment 0.85
- **适用场景:** 60s 单集「软光甜宠」女频短剧 —— 全程柔光 + 暖色调
- **反指示:** 多峰反转 C3(软光削弱反转冲击)

**S-C3** (悬疑烧脑 / Substitute narrative POV):
- **输入:** POV = protagonist single
- **变体动作:** Substitute `POV=protagonist` → `POV=antagonist hidden`(反派视角隐藏叙事)
- **输出候选:** narrative structure 翻转,5D 不变;novelty 0.85 / feasibility 0.65(POV 翻转风险高)/ alignment 0.75
- **适用场景:** 180s 长集数悬疑「真凶视角」短剧
- **反指示:** 60s 单集(无空间铺垫反派动机)

**S-C4** (微电影文艺 / Substitute focal length):
- **输入:** `common_focal_length=35mm`
- **变体动作:** Substitute `35mm` → `85mm`(长焦压缩空间 → 内省感)
- **输出候选 5D:** `composition +0.2`(长焦改变 depth perception);novelty 0.60 / feasibility 0.90 / alignment 0.85
- **适用场景:** 5-15min 文艺微电影「主角内心独白」段落
- **反指示:** 动作 / 战斗场景(长焦丢失空间感)

**S-C5** (漫剧拟人化 / Substitute character archetype):
- **输入:** archetype = hero-journey
- **变体动作:** Substitute `hero-journey` → `trickster-antihero`(恶作剧反英雄)
- **输出候选 5D:** `rhythm +0.1`(更快节奏);novelty 0.70 / feasibility 0.80 / alignment 0.70
- **适用场景:** 120s 漫剧「调皮主角」情谊冒险
- **反指示:** 悬疑烧脑 C3(trickster 削弱严肃感)

---

#### Combine (C) 配方 C-C1 ... C-C5

**C-C1** (男频复仇 × 女频甜宠 → 双主角复仇):
- **输入:** `male_revenge_5D × 0.7 + female_romance_5D × 0.3`
- **变体动作:** Combine 两个 genre 5D 向量(70/30 dominant ratio)
- **输出候选:** `color=0.5(mixed), rhythm=0.65(slower than pure male-revenge)`;novelty 0.65 / feasibility 0.75(70/30 不破 genre 约束)/ alignment 0.80
- **适用场景:** 90s 单集双主角复仇爽剧(男女主复仇线交织)
- **反指示:** 单主角 60s(无空间铺双线)

**C-C2** (女频甜宠 × 微电影文艺 → 文艺甜宠):
- **输入:** `female_romance_5D × 0.6 + arthouse_5D × 0.4`
- **变体动作:** Combine 60/40
- **输出候选:** `rhythm=0.4(slower), composition=0.6` ;novelty 0.70 / feasibility 0.70(40% 文艺会破甜宠节奏)/ alignment 0.65
- **适用场景:** 5-15min 文艺甜宠微电影
- **反指示:** 60s 抖音单集(文艺节奏过慢)

**C-C3** (悬疑烧脑 × 漫剧拟人化 → 拟人悬疑):
- **输入:** `suspense_5D × 0.65 + anthropomorphic_5D × 0.35`
- **变体动作:** Combine 65/35
- **输出候选:** `rhythm=0.6(中等节奏), sound=0.7(LF rumble 保留悬疑感)`;novelty 0.85 / feasibility 0.55(拟人化削弱悬疑严肃感)/ alignment 0.60
- **适用场景:** 120s 漫剧「动物侦探」悬疑短剧
- **反指示:** 真人短剧 C3(漫剧 ≠ 真人)

**C-C4** (微电影文艺 × 男频复仇 → 复仇艺术片):
- **输入:** `arthouse_5D × 0.55 + male_revenge_5D × 0.45`
- **变体动作:** Combine 55/45(罕见 dominant 翻转)
- **输出候选:** `rhythm=0.45(slow burn), composition=0.4(sym)`;novelty 0.90 / feasibility 0.50(罕见组合风险)/ alignment 0.55
- **适用场景:** 10-15min 艺术片电影节参赛(慢节奏复仇)
- **反指示:** 60-90s 抖音(节奏过慢)

**C-C5** (漫剧拟人化 × 女频甜宠 → 萌宠甜宠):
- **输入:** `anthropomorphic_5D × 0.6 + female_romance_5D × 0.4`
- **变体动作:** Combine 60/40
- **输出候选:** `color=0.75(warm/high-sat), sound=0.75`;novelty 0.65 / feasibility 0.85 / alignment 0.85
- **适用场景:** 120s 萌宠甜宠漫剧(拟人化宠物助攻女主)
- **反指示:** 男频复仇 C1(萌宠削弱复仇严肃感)

---

#### Adapt (A) 配方 A-C1 ... A-C5

**A-C1** (男频复仇 / Adapt FPS game first-person):
- **输入:** `composition=0.5(standard)`
- **变体动作:** Adapt `FPS game POV` → `composition +0.3, rhythm +0.2`(第一人称视角)
- **输出候选 5D:** `composition=0.8, rhythm=0.9`;novelty 0.75 / feasibility 0.70(POV 风险)/ alignment 0.80
- **适用场景:** 90s 男频「沉浸式战斗」短剧
- **反指示:** 60s 单集(无空间建立 POV)

**A-C2** (女频甜宠 / Adapt classical Chinese painting):
- **输入:** `composition=0.5, color=0.6`
- **变体动作:** Adapt `古典国画 留白` → `composition -0.2(留白构图), color +0.1`
- **输出候选 5D:** `composition=0.3, color=0.7`;novelty 0.65 / feasibility 0.85 / alignment 0.75
- **适用场景:** 60s 女频「古风甜宠」(古画审美)
- **反指示:** 现代题材 C2(留白不契合)

**A-C3** (悬疑烧脑 / Adapt noir film sound design):
- **输入:** `sound=0.6`
- **变体动作:** Adapt `1940s film noir sound` → `sound +0.2(jazz + voice-over)`
- **输出候选 5D:** `sound=0.8`;novelty 0.70 / feasibility 0.80 / alignment 0.80
- **适用场景:** 180s 悬疑「黑色电影风」短剧
- **反指示:** 漫剧 C5(noir 与拟人化冲突)

**A-C4** (微电影文艺 / Adapt Tarkovsky long-take):
- **输入:** `rhythm=0.3(slow)`
- **变体动作:** Adapt `Tarkovsky 7-9min long-take` → `rhythm -0.2(极致慢)`
- **输出候选 5D:** `rhythm=0.1`;novelty 0.85 / feasibility 0.60(极致慢节奏风险)/ alignment 0.75
- **适用场景:** 10-15min 文艺微电影「冥想式」段落
- **反指示:** 短剧 60-90s(节奏过慢)

**A-C5** (漫剧拟人化 / Adapt manga speed-line):
- **输入:** `rhythm=0.7(fast)`
- **变体动作:** Adapt `manga 速度线` → `rhythm +0.1, composition +0.1`
- **输出候选 5D:** `rhythm=0.8, composition=0.6`;novelty 0.75 / feasibility 0.85 / alignment 0.85
- **适用场景:** 120s 漫剧「战斗场面」速度线风格
- **反指示:** 微电影文艺 C4(速度线破坏文艺感)

---

#### Modify / Magnify / Minify (M) 配方 M-C1 ... M-C5

**M-C1** (男频复仇 / Magnify color saturation):
- **输入:** `color=0.6`
- **变体动作:** Magnify `color +0.3` → `color=0.9`(极致高饱和)
- **输出候选 5D:** `color=0.9`;novelty 0.55 / feasibility 0.90 / alignment 0.85
- **适用场景:** 90s 男频「视觉冲击型」复仇爽剧
- **反指示:** 微电影文艺 C4(高饱和破坏文艺)

**M-C2** (女频甜宠 / Minify cut density):
- **输入:** `rhythm=0.6(medium)`
- **变体动作:** Minify `rhythm -0.3` → `rhythm=0.3`(慢节奏甜宠)
- **输出候选 5D:** `rhythm=0.3`;novelty 0.60 / feasibility 0.75(破抖音 1.5x 硬约束)/ alignment 0.65
- **适用场景:** 60s 女频「慢节奏治愈」甜宠(破抖音规则,需 YouTube Shorts / B站)
- **反指示:** 抖音(破 1.5x 规则)

**M-C3** (悬疑烧脑 / Magnify light_shadow contrast):
- **输入:** `light_shadow=0.6`
- **变体动作:** Magnify `light_shadow +0.3` → `light_shadow=0.9`(极致高对比)
- **输出候选 5D:** `light_shadow=0.9`;novelty 0.55 / feasibility 0.85 / alignment 0.85
- **适用场景:** 180s 悬疑「黑色电影式」高对比
- **反指示:** 萌宠甜宠 C-C5(高对比破坏萌宠)

**M-C4** (微电影文艺 / Minify color saturation):
- **输入:** `color=0.5`
- **变体动作:** Minify `color -0.3` → `color=0.2`(低饱和 / 接近黑白)
- **输出候选 5D:** `color=0.2`;novelty 0.70 / feasibility 0.90 / alignment 0.85
- **适用场景:** 10-15min 文艺微电影「黑白质感」
- **反指示:** 女频甜宠 C2(低饱和破坏甜宠暖意)

**M-C5** (漫剧拟人化 / Magnify sound richness):
- **输入:** `sound=0.6`
- **变体动作:** Magnify `sound +0.3` → `sound=0.9`(丰富拟人化音效)
- **输出候选 5D:** `sound=0.9`;novelty 0.60 / feasibility 0.85 / alignment 0.85
- **适用场景:** 120s 漫剧「拟人化音效丰富」(动物叫声 / 拟人语音)
- **反指示:** 悬疑烧脑 C3(过丰富 sound 削弱悬疑留白)

---

#### Put to other use (P) 配方 P-C1 ... P-C5

**P-C1** (男频 90s 风格 → 改为女频 60s):
- **输入:** runtime=90s, audience=male → new_runtime=60s, new_audience=female
- **变体动作:** Put `(90s, male)` → `(60s, female)`
- **输出候选 5D:** 调整 `color +0.2, rhythm -0.2, light_shadow -0.3`;novelty 0.75 / feasibility 0.65(跨受众风险)/ alignment 0.70
- **适用场景:** IP 跨受众分发(原男频剧本改女频版)
- **反指示:** 剧本结构性男频元素(复仇兑现 vs 情感圆满不兼容)

**P-C2** (抖音 60s 风格 → 改为小程序剧 180s):
- **输入:** runtime=60s, platform=douyin → new_runtime=180s, new_platform=miniprogram
- **变体动作:** Put `(60s, douyin)` → `(180s, miniprogram)`
- **输出候选 5D:** 调整 `rhythm -0.3, sound +0.2`(更长节奏 + 更丰富 BGM);novelty 0.70 / feasibility 0.70 / alignment 0.75
- **适用场景:** IP 跨平台分发(抖音短剧改小程序剧长集)
- **反指示:** 剧本单集自洽(短剧自洽 ≠ 长集连续)

**P-C3** (真人短剧风格 → 改为漫剧):
- **输入:** form=live-action → new_form=animated
- **变体动作:** Put `live-action` → `animated`
- **输出候选 5D:** 调整 `composition +0.1(更平面化), sound +0.1(拟人音效)`;novelty 0.85 / feasibility 0.50(动画成本)/ alignment 0.55
- **适用场景:** 真人 IP 改编漫剧(二次元化)
- **反指示:** 真人演员 IP(演员脸 ≠ 动画角色)

**P-C4** (微电影文艺 5-15min → 改为长片 60-90min):
- **输入:** runtime=15min → new_runtime=60-90min
- **变体动作:** Put `(15min)` → `(60-90min)`
- **输出候选 5D:** 调整 `rhythm -0.1(更慢), sound +0.1(更丰富 BGM 层次)`;novelty 0.85 / feasibility 0.40(长片预算风险)/ alignment 0.50
- **适用场景:** 微电影扩展为长片(电影节 / 院线)
- **反指示:** 短剧剧本(无长片容量)

**P-C5** (漫剧 120s → 改为竖屏 9:16 → 横屏 16:9 微电影):
- **输入:** aspect=9:16 → new_aspect=16:9
- **变体动作:** Put `(9:16 vertical)` → `(16:9 horizontal)`
- **输出候选 5D:** 调整 `composition -0.1(横屏对称感), rhythm -0.1`;novelty 0.75 / feasibility 0.75 / alignment 0.70
- **适用场景:** 漫剧改横屏微电影(B站 / YouTube)
- **反指示:** 抖音竖屏硬约束(9:16 是平台硬规则)

---

#### Eliminate (E) 配方 E-C1 ... E-C5

**E-C1** (男频复仇 / Eliminate BGM):
- **输入:** `sound=0.7(LF rumble)`
- **变体动作:** Eliminate `BGM` → `sound=0.3`(纯环境音 + 对白)
- **输出候选 5D:** `sound=0.3`;novelty 0.85 / feasibility 0.55(破抖音 BGM coupled_beat 规则)/ alignment 0.65
- **适用场景:** 90s 男频「沉浸式战斗」无 BGM(突出环境音)
- **反指示:** 抖音(破 BGM sync)

**E-C2** (女频甜宠 / Eliminate dialogue):
- **输入:** dialogue-heavy
- **变体动作:** Eliminate `对白` → `无声剧 / 纯视觉叙事`
- **输出候选 5D:** `sound=0.2(纯环境音), rhythm=0.5`;novelty 0.90 / feasibility 0.45(高风险)/ alignment 0.55
- **适用场景:** 60s 女频「无声剧」实验短剧
- **反指示:** 180s 长集数(无对白撑不住)

**E-C3** (悬疑烧脑 / Eliminate signature close-up):
- **输入:** signature=close-up
- **变体动作:** Eliminate `close-up signature` → `远景 + 全景为主`
- **输出候选 5D:** `composition=0.2(extreme wide)`;novelty 0.70 / feasibility 0.75 / alignment 0.70
- **适用场景:** 180s 悬疑「旁观者视角」(无 close-up 冷距离感)
- **反指示:** 女频甜宠 C2(close-up 是甜宠核心)

**E-C4** (微电影文艺 / Eliminate narrative arc):
- **输入:** narrative=Snyder 15-beat
- **变体动作:** Eliminate `narrative arc` → `散文式 / 无明显结构`
- **输出候选 5D:** 无 5D 变化,只动 narrative;novelty 0.95 / feasibility 0.30(高风险)/ alignment 0.40
- **适用场景:** 10-15min 文艺微电影「实验无结构」
- **反指示:** 短剧 / 漫剧(商业内容需 narrative)

**E-C5** (漫剧拟人化 / Eliminate color):
- **输入:** `color=0.7(warm)`
- **变体动作:** Eliminate `color` → `黑白漫剧`
- **输出候选 5D:** `color=0.0`;novelty 0.80 / feasibility 0.70 / alignment 0.75
- **适用场景:** 120s 黑白漫剧(黑白漫画风)
- **反指示:** 女频甜宠 C2(无色破坏暖意)

---

#### Reverse / Rearrange (R) 配方 R-C1 ... R-C5

**R-C1** (男频复仇 / Reverse color temperature):
- **输入:** `color=0.3(cool)`
- **变体动作:** Reverse `color=0.3 cool` → `color=0.7 warm`
- **输出候选 5D:** `color=0.7`;novelty 0.55 / feasibility 0.85 / alignment 0.80
- **适用场景:** 90s 男频「暖色调复仇」(从冷压抑 → 暖爆发)
- **反指示:** 60s 单集(反转空间不足)

**R-C2** (女频甜宠 / Reverse rhythm):
- **输入:** `rhythm=0.5(medium)`
- **变体动作:** Reverse `rhythm=0.5` → `rhythm=0.9(fast-cut)`
- **输出候选 5D:** `rhythm=0.9`;novelty 0.75 / feasibility 0.70(快切破甜宠节奏)/ alignment 0.60
- **适用场景:** 60s 女频「快节奏甜宠」(实验性)
- **反指示:** 慢节奏治愈向 C2(快切破坏治愈感)

**R-C3** (悬疑烧脑 / Reverse narrative order):
- **输入:** narrative=chronological
- **变体动作:** Reverse `chronological` → `reverse chronological`(从结局倒叙)
- **输出候选 5D:** 无 5D 变化,只动 narrative;novelty 0.85 / feasibility 0.65(倒叙风险)/ alignment 0.75
- **适用场景:** 180s 悬疑「倒叙解谜」(从凶手揭晓倒推)
- **反指示:** 60s 单集(无空间倒叙铺垫)

**R-C4** (微电影文艺 / Reverse light_shadow):
- **输入:** `light_shadow=0.7(contrast)`
- **变体动作:** Reverse `light_shadow=0.7` → `light_shadow=0.3(soft)`
- **输出候选 5D:** `light_shadow=0.3`;novelty 0.60 / feasibility 0.85 / alignment 0.80
- **适用场景:** 10-15min 文艺微电影「柔光质感」
- **反指示:** 男频复仇 C1(柔光削弱复仇冲击)

**R-C5** (漫剧拟人化 / Reverse signature order):
- **输入:** signature_order=[intro, conflict, resolution]
- **变体动作:** Rearrange `[intro, conflict, resolution]` → `[resolution, intro, conflict]`(先揭晓结局再回顾)
- **输出候选 5D:** 无 5D 变化,只动 signature 顺序;novelty 0.85 / feasibility 0.60(重排风险)/ alignment 0.70
- **适用场景:** 120s 漫剧「先果后因」叙事实验
- **反指示:** 60s 单集(无空间重排)

---

## LLM Prompt Template

### 1. 通用 SCAMPER 变体生成 prompt

```
你是 style_genome 专家的 SCAMPER 变体引擎。给定一个已锁定的 style_genome,请用 SCAMPER 7 动词各生成 1 个候选变体。

输入 style_genome:
{style_genome_json}

要求:
1. 对每个 verb(Substitute / Combine / Adapt / Modify / Put-to-other-use / Eliminate / Reverse)各生成 1 个候选,共 7 个
2. 每个候选必须包含:recipe_id(verb-combo 格式如 S-C1)、modified_5D_vector、modification_summary、novelty_score(0-1)、feasibility_score(0-1)、alignment_score(0-1)
3. feasibility_score 必须基于 genre 5D 区间约束(参考 genre-dna-taxonomy.md)+ director tier 兼容性(参考 auteur-theory.md)
4. 输出 JSON 数组,7 个对象

参考配方表:[scamper-variations.md §35 Variation Recipes]

输出 schema:见 §Output Schema
```

### 2. 7 动词专用 prompt(每动词 1 个)

每个 prompt 都从「输入 style_genome + 该动词的变体规则」出发,聚焦该动词:

- **Substitute prompt:** 「找 style_genome 中最适合被替换的 1 个元素(director / genre / 5D value / signature),给出替换前后 + 理由」
- **Combine prompt:** 「找与当前 style_genome 最互补的第 2 个 style(从 35 配方表中选),用 dominant/recessive 协议合并」
- **Adapt prompt:** 「找 1 个跨领域元素(游戏 / 文学 / 音乐 / 古典艺术)的 5D 翻译,说明翻译规则」
- **Modify prompt:** 「选 1 个 5D 维度,做 Magnify(+0.15 到 +0.35)或 Minify(-0.15 到 -0.35),说明触发场景」
- **Put-to-other-use prompt:** 「把当前 style_genome 应用到完全不同的 runtime × 受众 × 平台 元组」
- **Eliminate prompt:** 「选 1 个 signature element / 5D 极端值 / genre feature,移除后产出极简变体」
- **Reverse prompt:** 「选 1 个 5D 维度做对称取反(value → 1-value),或重排 narrative 顺序」

---

## Output Schema (`scamper_variants.json`)

```json
{
  "schema_version": "1.0.0",
  "generated_at": "2026-06-18T00:00:00Z",
  "source_genome": {
    "director": "Wong Kar-wai",
    "genre": "男频复仇",
    "tier": "Pantheon",
    "5d_vector": {
      "composition": 0.7,
      "color": 0.8,
      "rhythm": 0.4,
      "light_shadow": 0.3,
      "sound": 0.7
    }
  },
  "variants": [
    {
      "recipe_id": "S-C1",
      "verb": "Substitute",
      "modification_summary": "color=0.8 warm → color=0.3 cool(压抑冷色复仇)",
      "modified_5d_vector": {
        "composition": 0.7,
        "color": 0.3,
        "rhythm": 0.4,
        "light_shadow": 0.3,
        "sound": 0.7
      },
      "novelty_score": 0.50,
      "feasibility_score": 0.85,
      "alignment_score": 0.80,
      "recommended_use_cases": [
        "90s 男频复仇冷色调压抑型",
        "抖音-男频分发"
      ],
      "anti_indicators": [
        "60s 单集(color shift 不易被感知)"
      ]
    },
    {
      "recipe_id": "C-C1",
      "verb": "Combine",
      "modification_summary": "Wong Kar-wai × Nolan 70/30 dominant blend",
      "modified_5d_vector": {
        "composition": 0.49,
        "color": 0.71,
        "rhythm": 0.49,
        "light_shadow": 0.51,
        "sound": 0.73
      },
      "novelty_score": 0.65,
      "feasibility_score": 0.75,
      "alignment_score": 0.80,
      "recommended_use_cases": [
        "90s 单集双线复仇爽剧"
      ],
      "anti_indicators": [
        "60s 单集(无空间铺双线)"
      ]
    }
    // ... 5 more variants (A-C1, M-C1, P-C1, E-C1, R-C1) ...
  ]
}
```

**字段语义:**
- `recipe_id`:动词-组合编号(如 S-C1 / C-C1 / A-C1 / M-C1 / P-C1 / E-C1 / R-C1)
- `verb`:SCAMPER 7 动词之一
- `modification_summary`:人类可读的变体动作描述(中文)
- `modified_5d_vector`:变体后的 5D 向量(5 个浮点数 0.0-1.0)
- `novelty_score`:与 source_genome 的 5D 欧氏距离归一化(越大越新)
- `feasibility_score`:变体是否仍满足 genre 5D 区间约束 + director tier 兼容性
- `alignment_score`:变体与用户原始意图(runtime / 受众 / 平台)的匹配度
- `recommended_use_cases`:该变体适合的场景数组(2-3 个)
- `anti_indicators`:何时不用此变体的反指示数组(1-2 个)

---

## Integration with auteur-theory + genre-dna-taxonomy

### SCAMPER 不替代 auteur-theory 的 tier 判定

auteur-theory.md §Sarris 3-Criteria Rubric 判定 director tier(Pantheon / Modern Auteur / Operator)是 style_genome 的**分类前置步骤**。SCAMPER 在 tier 判定后才介入,展开变体候选 —— 但**不修改 tier 字段**。如果 SCAMPER 的 Substitute 把 director 从 Wong Kar-wai 换成 Nolan,tier 字段(Pantheon vs Modern Auteur)由 auteur-theory 重新判定,SCAMPER 只标记「director 替换发生」。

### SCAMPER 不替代 genre-dna 的 5D 区间

genre-dna-taxonomy.md §12-Genre 5D Vector Ranges 给出每个 genre 的 5D 允许区间。SCAMPER 的 Modify(Magnify/Minify)操作必须在 genre 5D 区间内做 ±delta —— 如果用户给的 delta 超出区间,SCAMPER 引擎应拒绝并返回 `feasibility_score=0` + 警告「超出 genre 约束」。

### SCAMPER 与 cross-cultural-style 的 hybrid encoding 区别

cross-cultural-style.md §Hybrid Encoding Protocol 是**跨文化 hybrid**(CN × Western / 短剧 出海),用 `original × 0.65 + target × 0.35` 协议。SCAMPER 的 Combine 动词是**任意两 style 的混合**,可以是同文化内两个 director(如 Wong Kar-wai × Nolan)或同 director 不同 genre(Wong Kar-wai 男频 × 女频),用 70/30 dominant ratio。两者**不冲突** —— cross-cultural 是 hybrid 的特例(跨文化场景),SCAMPER Combine 是 hybrid 的通用化(任意两 style 场景)。

---

## Anti-Patterns / What NOT to do

- ❌ **不要把 SCAMPER 当作分类系统。** SCAMPER 是变体引擎(variation engine),不是分类系统(classification system)。auteur-theory(genre tier)+ genre-dna(genre 5D 区间)+ cross-cultural-style(hybrid encoding)才是分类系统。SCAMPER 在分类结果确定后才介入。
- ❌ **不要让 SCAMPER 替代 director tier 判定。** tier 判定是 auteur-theory 的责任。SCAMPER 不重写 tier 字段。
- ❌ **不要让 SCAMPER 改写 genre 5D 区间。** genre-dna-taxonomy 的区间表是硬约束。SCAMPER 的 Modify 操作若超出区间,必须拒绝(feasibility_score=0)。
- ❌ **不要把 7 候选全部应用。** 用户 / 下游应基于 novelty × feasibility × alignment 推荐分数挑选 1-3 个候选。把 7 个全部应用会引入风格混乱。
- ❌ **不要在 auteur-theory tier 判定阶段调用 SCAMPER。** SCAMPER 的触发条件是「tier + genre + hybrid 已锁定」之后,不是之前。
- ❌ **不要把 SCAMPER 与 cross-cultural hybrid 混淆。** cross-cultural 是 hybrid 的特例(跨文化);SCAMPER Combine 是 hybrid 的通用化(任意两 style)。
- ❌ **不要复制 Eberle 1971 原书内容。** 本 ref 只 paraphrase 7 动词定义 + 自创 35 配方与短剧适配。复制原书案例违反 Fair Use。

---

## Refresh Cadence

每季度复审:检查 35 配方表中是否有不再适用的基因组合(如新平台崛起 / 新 genre 出现),并在适当时机扩展 5 基因组合 → 6-7 个,使配方总数从 35 扩展到 42-49。

## Drift Signals

触发本 ref 更新的事件:
- 新短剧平台崛起(如新海外平台 / 新国内平台),5 基因组合需扩展
- 现有 5 基因组合中某 genre 失效(如 男频复仇 genre 衰落)
- SCAMPER 7 动词在教学领域被修订(罕见,Eberle 1971 已稳定 50+ 年)
- `_shared/glossary.md` SCAMPER 词条被修改(需同步)

---

## License

本 ref 是 **Fair Use paraphrase** + **original Hermes analytical work**:
- 7 SCAMPER 动词定义:Eberle 1971 + Osborn 1953 溯源,paraphrase only,无原书案例复制
- 35 变体配方:Hermes Agent 原创工作(基于 7 动词 × 5 基因组合的短剧适配,无单一版权源)
- LLM prompt 模板:Hermes Agent 原创工作
- JSON schema:Hermes Agent 原创工作

See [LICENSE.md](./LICENSE.md) §6 (attribution table row to be added by Phase 21 Plan F7).

---

*Owned by Phase 21 plan 21-01 (SCAMPER Variation Engine). No parallel plan touches this scamper-variations.md file. Other refs under style_genome/references/ are owned by their respective Phase 3 / Phase 7C plans.*
