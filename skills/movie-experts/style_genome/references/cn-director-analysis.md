# CN Director Analysis — 张艺谋 / 贾樟柯 / 王家卫 / 周星驰 + 短剧 导演 5D 编码

**Source:** Rey Chow *Sentimental Fabulations, Contemporary Chinese Films* (2007, Columbia UP); Zhang Yingjin *Chinese National Cinema* (2004, Columbia UP); Bordwell *Planet Hong Kong* (2nd ed, 2011) for Hong Kong directors; CN 平台 公开导演访谈 + 短剧 制作公司公开 case studies(2024-2026);Cinemetrics public ASL 数据库 for 短剧 average shot length 统计。
**Copyright:** Fair Use — 5D 编码是 Hermes 原创分析工作;signature elements 改写自公开访谈和影评。无任何剧作 / 剧本 / 影片片段 verbatim 引用。See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 style_genome 专家在编码 **CN 大陆 / 港台 / 短剧 导演** 时的**CN 语境侧权威源**(CN-context authoritative source)。它与 [`director-dna-archive.md`](./director-dna-archive.md)(通用数据侧)、[`auteur-theory.md`](./auteur-theory.md)(理论侧 Sarris 判定)、[`cross-cultural-style.md`](./cross-cultural-style.md)(跨文化侧)互补,共同构成 style_genome 编码的四层 grounding。

CN 导演的 Sarris 3-criteria 评估存在特殊性:CN 第五代 / 第六代 / 香港新浪潮 / 短剧 第一代 director 各有独特 tiering 规则,详见本 ref §CN Director Tiering Crosswalk。

术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)。

---

## CN Director Tiering Crosswalk

### 关键 heuristic 1 (load-bearing): Sarris tier × CN generation 交叉表

CN 导演因文化产业历史发展差异,Sarris tier 判定必须考虑 generation 因素:

| Generation | Sarris tier 多数分布 | 5D 编码精度 | 备注 |
|-----------|----------------------|-------------|------|
| **第五代(1980s-)** | Pantheon / Modern Auteur | ±0.05 | Zhang Yimou / Chen Kaige / Tian Zhuangzhuang — international festival success + 跨 30+ 作品 personality signature |
| **第六代(1990s-)** | Modern Auteur | ±0.05 | Jia Zhangke / Wang Xiaoshuai / Zhang Yuan — urban realist 风格 + festival circuit |
| **香港新浪潮(1970s-)** | Pantheon(选)/ Modern Auteur | ±0.05 | Wong Kar-wai / Johnnie To / Ann Hui — 跨 30+ 作品 + international festival |
| **台湾新电影(1980s-)** | Pantheon(选)/ Modern Auteur | ±0.05 | Hou Hsiao-Hsien / Edward Yang / Tsai Ming-liang |
| **commercial 大片导演(2000s-)** | Operator Convention(多数)| ±0.10 | 部分商业片导演缺乏 personality signature |
| **短剧 第一代(2020s-)** | Operator Convention(多数) | ±0.10 | 短剧 导演多为 tradecraft,缺乏 auteur personality |

### 关键 heuristic 2: CN director 5D 编码必须标注 "primary contributor"

CN 导演 5D vector 在 §Auteur vs Operator Convention 中存在特殊情况:CN 大片常由 cinematographer / production designer 主导视觉,而非 director(如 Zhang Yimou × Zhao Xiaoding 摄影师组合)。style_genome 编码必须标注:

| Director | primary_contributor | secondary_contributor | 编码可信度 |
|----------|---------------------|----------------------|------------|
| Zhang Yimou(2002+,大片)| director (60%) | cinematographer Zhao Xiaoding (40%) | medium |
| Jia Zhangke | director (90%) | cinematographer Yu Lik-wai (10%) | high |
| Wong Kar-wai | director (70%) | cinematographer Christopher Doyle (30%) | high |
| 周星驰 | director (50%) | action choreographer (50%) | medium |

style_genome 部署:`style_genome.json` 必须 output `primary_contributor` 字段,标注 5D vector 信任度。

---

## 5 位 Canonical CN Director 5D Profile

### 关键 heuristic 3 (load-bearing): 5 位 CN showcase director 5D 向量

style_genome §Director Archive 必须包含下列 5 位 CN director(profile 与 [`auteur-theory.md`](./auteur-theory.md) §Sarris 3-criteria Rubric 兼容):

| Director | composition | color | rhythm | light_shadow | sound | tier | interior_meaning |
|----------|-------------|-------|--------|--------------|-------|------|------------------|
| **Zhang Yimou**(张艺谋)| 0.65 (frequent symmetry + 国风 composition) | 0.85 (high-sat 国风 warm) | 0.30 (long-take + tableau) | 0.55 (mixed) | 0.75 (rich score + 国风 instrument) | Pantheon | TM-03 (identity/culture) |
| **Jia Zhangke**(贾樟柯)| 0.40 (rule-of-thirds + 偶尔 handheld) | 0.30 (low-sat documentary) | 0.25 (slow + long-take) | 0.45 (naturalistic) | 0.45 (diegetic-heavy + minimal score) | Modern Auteur | TM-05 (alienation/modernity) |
| **Wong Kar-wai**(王家卫)| 0.70 (asymmetry + step-printing)| 0.80 (warm + high-sat teal/orange) | 0.40 (slow + step-printed) | 0.30 (low-key + chiaroscuro) | 0.70 (rich score + diegetic pop) | Pantheon | TM-01 (love/loss) |
| **Johnnie To**(杜琪峰)| 0.50 (deliberate composition)| 0.45 (desaturated cool)| 0.50 (mid-tempo)| 0.65 (chiaroscuro)| 0.60 (minimal + diegetic)| Modern Auteur | TM-07 (violence/order) |
| **Hou Hsiao-Hsien**(侯孝贤)| 0.45 (static + thoughtful framing)| 0.40 (naturalistic)| 0.20 (very long takes 30s+)| 0.50 (naturalistic)| 0.40 (diegetic + minimal)| Pantheon | TM-04 (memory/history) |

### 关键 heuristic 4: signature elements per CN director

style_genome §Director Archive 必须列出每位 CN director 的 3-5 个 signature elements:

**Zhang Yimou signatures:**
1. 国风 color palette(red + gold + black 主导;*Hero* / *House of Flying Daggers* 全片色彩叙事)
2. Symmetric tableau composition(*Curse of the Golden Flower* 宫廷场景)
3. Long-take + tableau blocking(*Hero* 棋馆场景)
4. National-style instrument layer(erhu + guzheng + percussion in score)
5. Cultural ritual choreography(武术 / 舞蹈 / 仪式)

**Jia Zhangke signatures:**
1. Realistic / documentary-style color(low-sat + desaturated;*Platform* / *Still Life*)
2. Long-take + static camera(30s+ ASL;*Still Life* 三峡工程场景)
3. Diegetic sound priority over score(pop music ambient + diegetic layer)
4. Real locations over sets(*Unknown Pleasures* 汾阳街道 / *Ash Is Purest White* 大同)
5. Non-professional actor + dialogue improvisation 部分

**Wong Kar-wai signatures:**
1. Step-printing(慢快门 + 跳印;*Chungking Express* / *In the Mood for Love*)
2. Teal + orange duo-tone color grading(暖色高饱和)
3. Asymmetric composition + claustrophobic framing
4. Diegetic pop music as score(California Dreamin' / Yumeji's Theme)
5. Voice-over interior monologue(*Chungking Express* / *Fallen Angels*)

**Johnnie To signatures:**
1. Geometric composition(对称 / 三角形;*The Mission* 枪战)
2. Cool desaturated palette(blue / gray 主导)
3. Static wide shots + sudden action bursts
4. Minimal score + diegetic-heavy sound
5. Extended stand-off + ritualized gun choreography

**Hou Hsiao-Hsien signatures:**
1. Very long takes(30s+ ASL;*Café Lumière* / *The Assassin*)
2. Static camera with subtle reframing
3. Naturalistic light(window / door light primary)
4. Diegetic sound + minimal score
5. Off-screen action + ambiguity

### 关键 heuristic 5: 焦距 + ASL 数据

style_genome §Director Archive `focal_length` + `asl_seconds` 字段(基于 Cinemetrics 公开数据):

| Director | common_focal_length | asl_seconds | source |
|----------|---------------------|-------------|--------|
| Zhang Yimou | 35-50mm(中焦 + 偶尔 85mm 人像) | 4.2s(*Hero*)/ 3.8s(*House of Flying Daggers*) | Cinemetrics |
| Jia Zhangke | 35-50mm(中焦 + 偶尔 24mm 广角)| 12.5s(*Platform*)/ 9.8s(*Still Life*) | Cinemetrics |
| Wong Kar-wai | 35-75mm(中长焦 + step-printing)| 3.6s(*Chungking Express*)/ 5.8s(*In the Mood for Love*) | Cinemetrics |
| Johnnie To | 35-50mm(中焦)| 4.5s(*The Mission*)/ 3.9s(*Election*) | Cinemetrics |
| Hou Hsiao-Hsien | 35-50mm(中焦)| 32.5s(*Café Lumière*)/ 28.7s(*The Assassin*) | Cinemetrics |

---

## CN 短剧 Director Tiering 特殊规则

### 关键 heuristic 6: 短剧 导演 Operator Convention tier 判定

短剧 导演(2020s 兴起的 短剧 / 小程序剧 第一代导演)多数为 Operator Convention tier,理由:

1. ** Personality signature 跨作品不稳定:** 短剧 导演常按平台 / 投资人要求调整风格,5D vector 跨作品 σ > 0.15
2. ** Interior meaning 缺乏:** 短剧 多为 类型化爽剧(revenge / romance / dominance),缺乏 Sarris 第 3 criteria 要求的 interior meaning
3. ** Tradecraft > authorship:** 短剧 工业化流水线作业(单集成片 1-3 天),导演更像 executor 而非 author

**部署硬规则:** 短剧 导演 5D 编码精度 ±0.10,且 style_genome.json 必须 output:
- `tier: Operator Convention`
- `short_drama_genre: <revenge | romance | dominance | comedy | other>`
- `interior_meaning: TM-XX: uncategorized`

### 关键 heuristic 7: 短剧 导演签名元素(signature elements)

短剧 导演虽多为 Operator Convention tier,但仍有可识别的 5D vector 偏好(基于 2024-2026 公开 case study):

**短剧-男频-revenge(剧本杀 / 重生 / 装逼)5D vector 偏好区间:**
- composition: 0.55-0.70(subjective POV + Dutch angle)
- color: 0.65-0.80(high-sat warm + red/blue contrast)
- rhythm: 0.80-0.95(极快剪辑 ASL 1.2-1.8s)
- light_shadow: 0.55-0.70(mid-key + dramatic chiaroscuro)
- sound: 0.65-0.80(rich score + drops + BGM 持续)

**短剧-女频-romance(甜宠 / 虐恋 / 双洁)5D vector 偏好区间:**
- composition: 0.45-0.65(三分法 + 中近景为主)
- color: 0.55-0.70(mid-sat warm + 暖光 + 柔焦)
- rhythm: 0.55-0.75(mid-tempo ASL 2.5-4s)
- light_shadow: 0.30-0.50(high-key + soft)
- sound: 0.55-0.70(pop ballad + diegetic)

---

## Korean Style Crosswalk

### 关键 heuristic 8: Korean director × CN 短剧 hybrid 编码

Korean cinema / K-drama 作为 CN 短剧 hybrid 媒介的 5D vector 参考(详见 [`cross-cultural-style.md`](./cross-cultural-style.md) §Korean Wave):

| Korean director | composition | color | rhythm | light_shadow | sound | 备注 |
|----------------|-------------|-------|--------|--------------|-------|------|
| **Bong Joon-ho** | 0.50 | 0.45 | 0.50 | 0.65 | 0.65 | cross-cultural hybrid-friendly |
| **Park Chan-wook** | 0.65 | 0.55 | 0.45 | 0.65 | 0.65 | TM-07 violence/order |
| **Lee Chang-dong** | 0.45 | 0.30 | 0.30 | 0.55 | 0.50 | TM-04 / TM-05 |
| **K-drama(romance)** | 0.50 | 0.65 | 0.55 | 0.40 | 0.65 | 短剧-女频 hybrid reference |
| **K-drama(thriller)** | 0.55 | 0.40 | 0.65 | 0.65 | 0.70 | 短剧-男频 hybrid reference |

style_genome 支持 `hybrid_reference: korean` flag,自动应用 Korean 5D vector 作为 hybrid 媒介。

---

## CN Director Archive 集成

style_genome §Director Archive 表新增 3 列(CN director 专属):

| 列名 | 取值范围 | 来源 |
|------|---------|------|
| `cn_generation` | 第五代 / 第六代 / 香港新浪潮 / 台湾新电影 / commercial / short_drama | 本 ref §CN Director Tiering Crosswalk |
| `primary_contributor` | director / cinematographer / production_designer(混合比例)| 本 ref §CN director 5D 编码必须标注 |
| `non_translatable_elements[]` | 国风 instrument / 书法 / 节庆色卡 / 功夫 choreography 等 | 详见 [`cross-cultural-style.md`](./cross-cultural-style.md) §Cultural translation cost |

---

## Anti-Pattern: CN Director 5D 编码常见误用

### 关键 heuristic 9: 5D 编码 3 大 anti-pattern(规避)

1. **过简 anti-pattern:** 把 Zhang Yimou 整体编码为 "red + slow",忽略其 5D vector 在 *Hero* / *Shadow* / *Cliff Walkers* 间的差异(详见 [`director-dna-archive.md`](./director-dna-archive.md) §5D Encoding Protocol §precision ±0.05)。**Mitigation:** 每位 director 提供 ≥3 部作品 5D vector,取均值。
2. **文化符号 = 5D 编码 anti-pattern:** 把"国风 instrument"自动 +0.10 sound 维度。**Mitigation:** 国风 instrument 仅在 SKILL.md §Sound 维度 §0.7-0.8 区间中体现,不可自动 +0.10。
3. **跨文化翻译 = 替换 anti-pattern:** 把 Zhang Yimou × Western audience 直接替换为 "Western 5D"(cultural erasure)。**Mitigation:** 必须 hybrid encoding,保留 0.65 original(详见 [`cross-cultural-style.md`](./cross-cultural-style.md) §Hybrid Encoding Protocol)。

---

## Glossary

- **CN Generation:** 第五代(1980s-) / 第六代(1990s-) / 香港新浪潮(1970s-) / 台湾新电影(1980s-) / commercial(2000s-) / short_drama(2020s-)。
- **Primary contributor:** CN 大片导演 5D vector 中 director 与 cinematographer 的信任度分配。
- **Non-translatable elements:** 跨文化 hybrid 中必须保留的 CN signature 元素。
- **Short drama genre:** 男频-revenge / 女频-romance / dominance / comedy / other。

---

*Generated: 2026-06-15 as part of Phase 3 REFACTOR-04 (style_genome deep refactor).*
*Source provenance: Chow 2007 / Zhang 2004 / Bordwell 2011 / Cinemetrics public database / CN 平台 公开访谈 (2024-2026) — fair use paraphrase + short technical phrases only.*
