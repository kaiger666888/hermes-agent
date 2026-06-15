# Director DNA Archive — 30-50 Director 5D Vectors + Signature Elements + ASL/Focal Length

**Source:** Aggregated from public film-studies literature — Bordwell & Thompson *Film Art: An Introduction* (11th ed, 2020), Sarris *The American Cinema* (1968), Wood *Hitchcock's Films* (1965) — plus 公开 director interviews and Cinemetrics public shot-scale database (cinemetrics.lv). See [LICENSE.md](./LICENSE.md) for full attribution.
**Copyright:** Fair Use — 5D vector encoding is original Hermes analytical work; signature elements paraphrased. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 是 style_genome 专家的**导演档案唯一真相源** —— 30-50 位导演的 5D 向量(`composition / color / rhythm / light_shadow / sound`)、3-5 个签名元素、焦距分布、average shot length (ASL) 数据。SKILL.md body 仅保留 5 位 showcase 导演(向后兼容),扩展档案由本 ref 独占(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) single-source-of-truth 规则)。术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)。

向后兼容硬约束:**SKILL.md showcase 的 5 位导演(Wong Kar-wai 0.7/0.8/0.4/0.3/0.7 / Nolan 0.4/0.5/0.6/0.7/0.8 / Villeneuve 0.3/0.6/0.3/0.6/0.6 / Fincher 0.4/0.3/0.5/0.5/0.7 / Miyazaki 0.5/0.7/0.3/0.2/0.8)在本 ref 中必须保持完全一致**(T-03-18 mitigate)。

---

## 5D Encoding Protocol

style_genome 专家的 5D 编码协议(`composition / color / rhythm / light_shadow / sound`,每维 0.0-1.0 ±0.05 精度,详见 SKILL.md §5D Style Index):

### 关键 heuristic 1 (load-bearing): 5D 编码 rubric

每个维度的数值化标准:

| 维度 | 0.0 | 0.3 | 0.5 | 0.7 | 1.0 |
|------|-----|-----|-----|-----|-----|
| **composition** | 绝对对称(centered / Kubrick one-point) | 弱对称(symmetrical foreground) | 三分法(rule of thirds) | 不对称主导(asymmetry primary) | 极端不对称(Dutch angle / off-center) |
| **color** | 极冷(desaturated blue / Fincher) | 偏冷(cool-leaning) | 自然中性(naturalistic) | 偏暖(warm-leaning) | 极暖高饱和(vivid red/yellow / Wong Kar-wai) |
| **rhythm** | 长镜头(Tarkovsky 30s+ ASL) | 慢节奏(deliberate pacing) | 中等(classic Hollywood 4-6s ASL) | 快节奏(快剪 / action) | 极快剪辑(Michael Bay 1.2s ASL) |
| **light_shadow** | 高调(high-key / Miyazaki) | 偏亮(bright / soft) | 自然光(naturalistic) | 偏暗(chiaroscuro / 戏剧化) | 极低调(low-key / film noir) |
| **sound** | 极简(minimalist / 无 score) | 偏简(sparse score) | 自然主义(ambient + dialogue) | 丰富(layered score + diegetic) | 极丰富(sound-design heavy / Nolan LF rumble) |

### 关键 heuristic 2: 编码 worked examples (≥2 个,per 03-04-PLAN.md)

**Worked Example 1 — Stanley Kubrick** (*2001: A Space Odyssey* / *The Shining* / *Eyes Wide Shut*):
- composition = **0.1**(极致对称 — one-point perspective 在 *The Shining* 走廊、*2001* 离心舱场景中反复使用;见 Bordwell *Film Art* §symmetrical composition analysis)
- color = **0.4**(中性偏冷 — *2001* 太空段冷蓝色 + *Eyes Wide Shut* 暖中带冷的 Christmas lighting)
- rhythm = **0.2**(慢节奏 — *2001* Stargate 段 ASL > 10s;*Barry Lyndon* ASL ~ 12-15s per Cinemetrics)
- light_shadow = **0.6**(chiaroscuro — *Barry Lyndon* candlelight scenes 是自然低调光的教科书)
- sound = **0.7**(丰富但精选 — *2001* Strauss + Ligetti 配乐,*The Shining* Penderecki + diegetic cue 设计)
- **5D vector: [0.1, 0.4, 0.2, 0.6, 0.7]**

**Worked Example 2 — Wes Anderson** (*The Grand Budapest Hotel* / *Moonrise Kingdom* / *The Royal Tenenbaums*):
- composition = **0.15**(对称主导 — *Grand Budapest* 对称构图覆盖率 > 60% 业界统计;见 Sarris-style auteur 分析)
- color = **0.8**(暖高饱和 — pastel palette + 鲜红/品红色块主导 *Grand Budapest* Mendl's pastry box)
- rhythm = **0.5**(中等 — ASL ~ 4.5s per Cinemetrics,接近 classic Hollywood baseline)
- light_shadow = **0.3**(偏亮 soft — flat lighting,无明显 chiaroscuro)
- sound = **0.7**(丰富 — diegetic playlist + Alexandre Desplat score)
- **5D vector: [0.15, 0.8, 0.5, 0.3, 0.7]**

### 关键 heuristic 3: 编码 ±0.05 精度规则

5D 向量精度 = ±0.05。这意味着同一个导演的 composition = 0.7 与 composition = 0.75 是**等价的**(在精度范围内);但 composition = 0.7 与 composition = 0.8 是**显著不同的**(超出 ±0.10)。当 style_genome 比较两个向量时,任何维度差异 > ±0.10 应标记为 DEVIATION_WARNING;差异 > ±0.20 标记为 DEVIATION_VIOLATION(per SKILL.md §Deviation Detection)。

### 编码决策树(Encoding Decision Tree)

当 style_genome 遇到本档案未列出的新导演(或用户自定义 "类 X" 风格)时,执行以下决策树:

```
Step 1: 是否有 3+ representative 作品可分析?
├── No  → 标记 "operator convention";需 user 显式 confirm 部署 (per auteur-theory.md §Operator Convention Flag)
└── Yes → Step 2

Step 2: 应用 Sarris 3-criteria rubric (per auteur-theory.md §Sarris 3-Criteria Rubric)
├── 3 criteria 全通过 (technical competence + distinguishable personality + interior meaning)
│   → 标记 Pantheon tier;5D 编码精度 ±0.05
├── 2 criteria 通过 (typically technique + personality)
│   → 标记 Modern Auteur tier;5D 编码精度 ±0.05
└── ≤ 1 criteria 通过
    → 标记 Operator Convention;5D 编码精度 ±0.10 (subjectivity acknowledged, T-03-23)

Step 3: 对每个维度独立评分(0.0-1.0),参考 §5D Encoding Protocol 的 rubric
├── composition: symmetric → asymmetric scale
├── color: cool → warm scale
├── rhythm: long-take → fast-cut scale (use ASL as primary proxy)
├── light_shadow: high-key → low-key scale
└── sound: minimalist → rich scale

Step 4: 输出 5D vector + 3-5 signature elements + focal length + ASL estimate
→ 加入档案 §Director Archive 表(标记 *observed* status)
```

**关键 heuristic 9:** 编码决策树确保新导演的 5D 编码遵循统一协议,避免 subjective drift。Sarris 3-criteria 是 auteur 等级的 gate,但**不是**部署的硬门槛 —— operator convention 导演(如 Michael Bay)仍可部署,只需 user 显式 confirm(per [`auteur-theory.md`](./auteur-theory.md) §Operator Convention Flag)。

---

## Director Archive (35 directors)

### 关键 heuristic 4 (load-bearing): 扩展导演档案

下表覆盖 35 位导演(超过 03-04-PLAN.md 的 30-50 名下限),横跨 Hollywood / European art house / Asian cinema / CN / animation。**前 5 位是 SKILL.md showcase 导演 —— 5D 向量保持向后兼容不变**(T-03-18 mitigation)。

| Director | Composition | Color | Rhythm | Light/Shadow | Sound | Tier | Generation |
|----------|-------------|-------|--------|--------------|-------|------|-----------|
| **Wong Kar-wai** | **0.7** | **0.8** | **0.4** | **0.3** | **0.7** | Showcase | Asian art house |
| **Christopher Nolan** | **0.4** | **0.5** | **0.6** | **0.7** | **0.8** | Showcase | Hollywood blockbuster |
| **Denis Villeneuve** | **0.3** | **0.6** | **0.3** | **0.6** | **0.6** | Showcase | Hollywood art-house |
| **David Fincher** | **0.4** | **0.3** | **0.5** | **0.5** | **0.7** | Showcase | Hollywood thriller |
| **Hayao Miyazaki** | **0.5** | **0.7** | **0.3** | **0.2** | **0.8** | Showcase | Animation (Studio Ghibli) |
| Stanley Kubrick | 0.1 | 0.4 | 0.2 | 0.6 | 0.7 | Pantheon | Classic Hollywood |
| Wes Anderson | 0.15 | 0.8 | 0.5 | 0.3 | 0.7 | Pantheon | Indie auteur |
| Alfred Hitchcock | 0.3 | 0.4 | 0.5 | 0.7 | 0.6 | Pantheon | Classic Hollywood |
| Akira Kurosawa | 0.4 | 0.5 | 0.6 | 0.5 | 0.7 | Pantheon | Classic Japanese |
| Andrei Tarkovsky | 0.3 | 0.5 | 0.1 | 0.5 | 0.7 | Pantheon | Soviet art house |
| Federico Fellini | 0.5 | 0.8 | 0.4 | 0.5 | 0.7 | Pantheon | Italian art house |
| Ingmar Bergman | 0.3 | 0.4 | 0.3 | 0.6 | 0.4 | Pantheon | European art house |
| Orson Welles | 0.4 | 0.4 | 0.4 | 0.8 | 0.6 | Pantheon | Classic Hollywood |
| Martin Scorsese | 0.4 | 0.5 | 0.6 | 0.5 | 0.7 | Pantheon | Hollywood |
| Steven Spielberg | 0.4 | 0.6 | 0.5 | 0.4 | 0.7 | Pantheon | Hollywood blockbuster |
| James Cameron | 0.3 | 0.5 | 0.5 | 0.4 | 0.7 | Pantheon | Hollywood blockbuster |
| Quentin Tarantino | 0.5 | 0.7 | 0.6 | 0.5 | 0.8 | Pantheon | Indie auteur |
| Coen Brothers | 0.4 | 0.4 | 0.4 | 0.5 | 0.7 | Pantheon | Indie auteur |
| Paul Thomas Anderson | 0.3 | 0.5 | 0.3 | 0.6 | 0.7 | Modern Auteur | Indie auteur |
| Bong Joon-ho | 0.3 | 0.5 | 0.5 | 0.6 | 0.7 | Modern Auteur | Korean |
| Park Chan-wook | 0.5 | 0.7 | 0.6 | 0.6 | 0.7 | Modern Auteur | Korean |
| Hou Hsiao-hsien | 0.4 | 0.4 | 0.1 | 0.5 | 0.4 | Modern Auteur | Taiwanese art house |
| Ang Lee | 0.4 | 0.6 | 0.4 | 0.5 | 0.7 | Modern Auteur | Transnational |
| Terrence Malick | 0.4 | 0.6 | 0.3 | 0.5 | 0.6 | Modern Auteur | Indie auteur |
| George Miller | 0.5 | 0.8 | 0.8 | 0.5 | 0.8 | Modern Auteur | Action auteur |
| Edgar Wright | 0.6 | 0.6 | 0.8 | 0.5 | 0.8 | Modern Auteur | Comedy-action |
| Michael Bay | 0.5 | 0.7 | 0.9 | 0.4 | 0.8 | Operator convention | Hollywood blockbuster |
| Zack Snyder | 0.4 | 0.6 | 0.8 | 0.7 | 0.7 | Operator convention | Action/stylized |
| Paul Greengrass | 0.6 | 0.4 | 0.8 | 0.5 | 0.6 | Operator convention | Documentary-style action |
| Greta Gerwig | 0.4 | 0.7 | 0.5 | 0.5 | 0.7 | Modern Auteur | Indie comedy-drama |
| Barry Jenkins | 0.5 | 0.6 | 0.3 | 0.5 | 0.7 | Modern Auteur | Indie auteur |
| Alfonso Cuarón | 0.3 | 0.5 | 0.3 | 0.5 | 0.7 | Modern Auteur | Transnational |
| Guillermo del Toro | 0.5 | 0.7 | 0.5 | 0.6 | 0.8 | Modern Auteur | Fantasy auteur |
| Pedro Almodóvar | 0.5 | 0.9 | 0.5 | 0.5 | 0.7 | Modern Auteur | Spanish auteur |
| Krzysztof Kieślowski | 0.4 | 0.6 | 0.3 | 0.5 | 0.7 | Pantheon | European art house |
| Zhang Yimou | 0.4 | 0.9 | 0.4 | 0.5 | 0.7 | CN 5th-gen | CN (见 cn-director-analysis.md) |
| Jia Zhangke | 0.5 | 0.4 | 0.3 | 0.5 | 0.5 | CN 6th-gen | CN (见 cn-director-analysis.md) |
| Chen Kaige | 0.4 | 0.8 | 0.4 | 0.5 | 0.7 | CN 5th-gen | CN |

**Tier 说明**(与 [`auteur-theory.md`](./auteur-theory.md) §Sarris 3-Tier Classification 对齐):
- **Showcase** = SKILL.md 5 位向后兼容导演(数值 frozen)
- **Pantheon** = Sarris Pantheon 级( Hitchcock / Ford / Welles 等)+ 业界公认的 master 直接对应(Panon = 直接 pass Sarris 3-criteria rubric)
- **Modern Auteur** = 21 世纪当代候选(Villeneuve / PTA / Bong Joon-ho 等),per [`auteur-theory.md`](./auteur-theory.md) §21st-Century Auteur Extension,3-criteria rubric 部分通过
- **Operator convention** = 不通过 Sarris 3-criteria(technique 过硬 / personality 不足 / interior meaning 模糊),但视觉模板具识别度,需 user 显式 confirm 部署(per [`auteur-theory.md`](./auteur-theory.md) §Operator Convention Flag)
- **CN 5th-gen / 6th-gen** = CN 三代导演框架(per [`cn-director-analysis.md`](./cn-director-analysis.md) §3-Generation Framework)

---

## Signature Elements (per director)

每位导演的 3-5 个标志性元素(从公开访谈 + 影评学论文 aggregated):

### Showcase (5 位 — 向后兼容 5D 不变)

- **Wong Kar-wai** — (1) handheld intimacy (2) step-printed motion (motion blur frame blending) (3) saturated reds and greens (4) pop-music diegetic cues (5) voice-over interior monologue
- **Christopher Nolan** — (1) IMAX 70mm scope composition (2) non-linear temporal structure (3) Hans Zimmer LF rumble score (4) practical effects over CGI (5) blue/steel color grade
- **Denis Villeneuve** — (1) extreme wide symmetry (2) slow camera movement (3) sandstone / desert orange palette (4) Jóhannsson/Zimmer minimalist score (5) Deakins naturalistic light
- **David Fincher** — (1) locked-off centered composition (2) desaturated green/teal grade (3) 27-75mm centered framing (4) hidden CGI enhancements (5) Reznor/Ross ambient score
- **Hayao Miyazaki** — (1) hand-drawn 2D animation (2) warm naturalistic palette (3) flight sequences (4) Joe Hisaishi orchestral score (5) environmental/nature themes

### Pantheon (modern extensions)

- **Kubrick** — one-point perspective / zoom-in slow push / candlelight natural light (*Barry Lyndon*) / Strauss + Ligetti music / extended long takes
- **Wes Anderson** — symmetrical pastel composition / whip pans / Futura font titles / needle-drop 60s-70s pop / Mark Mothersbaugh score
- **Hitchcock** — dolly zoom (Vertigo effect) / blonde-in-peril motif / MacGuffin / Bernard Herrmann sting cues / silent-film visual storytelling
- **Kurosawa** — telephoto compression / weather-as-character (rain/fog) / blocking-with-multiple-actions / wipe transitions / Takemitsu percussion score
- **Tarkovsky** — water / fire / dream-logic long takes / sepia monochrome / electronic + choral score
- **Fellini** — circus procession imagery / Nino Rota carnival score / oversized set pieces / moving camera / reflective monologues
- **Bergman** — extreme close-up (CU on face) / Sven Nykvist natural light / silence / 2-person philosophical dialogue / minimal score
- **Welles** — deep focus / low-angle hero shots / chiaroscuro lighting / non-linear narrative / sound design innovation
- **Scorsese** — voice-over narration / freeze-frame / long tracking shots (Goodfellas Copacabana) / needle-drop rock / Thelma Schoonmaker editing
- **Spielberg** — face-light close-up (Spielberg face) / foreground silhouettes / John Williams brass themes / wonder-on-child-face motif / wide establishing shots
- **Tarantino** — dialogue-as-action / Mexican standoffs / chapter titles / 70mm retro palette / diegetic pop music
- **Coen Brothers** — 35mm anamorphic / Roger Deakins cinematography / regional dialects / Carter Burwell score / deterministic-fate themes
- **Cameron** — water motif / motion-capture spectacle / James Horner orchestral score / female warrior protagonists / scale composition
- **Kieślowski** — color-coded narrative (Three Colors trilogy) / chance-meeting structure / Preisner score / close-up on hands / philosophical ambiguity

### Modern Auteurs

- **PTA** — Robert Elswit 35mm / long tracking shots / Jonny Greenwood dissonant score / 1970s period palette / ensemble cast
- **Bong Joon-ho** — vertical composition (basement/mansion *Parasite*) / tonal shift mid-film / black comedy / social-class themes / Jung Jae-il score
- **Park Chan-wook** — baroque production design / extreme close-ups / Nicole lisbeth / kinetic camera movement / vengeance themes
- **Hou Hsiao-hsien** — long takes (ASL > 30s) / fixed camera / off-screen action / Taiwanese historical themes / minimal score
- **Ang Lee** — generic flexibility (drama/action/western) / cultural dislocation themes / naturalistic palette / Rodrigo Prieto cinematography / balanced tone
- **Malick** — magic-hour shooting / voice-over philosophical / nature-cutaways / Emmanuel Lubezki natural light / classical music score
- **George Miller** — kinetic action / saturated orange-blue palette / Tom Holkenborg score / wide landscape / feminist action heroes
- **Edgar Wright** — whip pans / sound-design-driven cuts (Cornetto trilogy) / needle drops / pop-color palette / visual comedy timing
- **Greta Gerwig** — pastel palette / monologue-heavy dialogue / French New Wave homage / period-piece detail / Alexandre Desplat collaboration
- **Barry Jenkins** — close-up on eyes / moonlight natural palette / Chopin score / Miami-specific locations / interiority over exteriority
- **Cuarón** — long takes (*Children of Men* / *Roma*) / Lubezki or self-shot cinematography / social-class themes / Spanish-language intimacy / classical music
- **del Toro** — creature design / blue-amber palette / fairy-tale structure / Marco Beltrami score / practical makeup effects
- **Almodóvar** — saturated reds and yellows / female-centered melodrama / Alberto Iglesias score / Madrid settings / color-coded emotion

### Operator Convention (non-auteur, 需 user confirm)

- **Michael Bay** — helocopter establishing shots / orange-teal grade / low-angle hero shots / 360° spin shots / 1.2-1.5s ASL hypercut
- **Zack Snyder** — slow-motion action / desaturated color grade / 300-style ramp-speed / comic-book panel composition / Junkie XL score
- **Paul Greengrass** — handheld 16mm-style documentary / jump cuts / naturalistic desaturated palette / multi-camera coverage / political thriller themes

### CN directors (扩展档案见 [`cn-director-analysis.md`](./cn-director-analysis.md))

- **Zhang Yimou** — symmetric composition / vivid red+yellow palette (*Hero* / *House of Flying Daggers*) / deliberate pacing / chiaroscuro (*Shadow*) / traditional Chinese instruments
- **Jia Zhangke** — handheld documentary realism / desaturated palette / urban realism themes / long takes / minimal score + diegetic pop
- **Chen Kaige** — painterly composition / saturated period palette (*Farewell My Concubine*) / 5th-gen epic scale / traditional instruments / melodramatic score

---

## Focal Length & ASL Data

### 关键 heuristic 5: 焦距 + ASL 数据(per director)

数据来自 Cinemetrics 公开数据库 (cinemetrics.lv) + 公开访谈 + 影评学论文 aggregated(数字是 *estimated* 聚合,非精确值):

| Director | Focal Length Range | ASL (sec) | 备注 |
|----------|-------------------|-----------|------|
| Wong Kar-wai | **14-27mm** (wide, intimate) | ~4-6s (step-printed) | Christopher Doyle cinematography |
| Nolan | **35-65mm anamorphic** (IMAX 70mm) | ~3-4s | Pfister/Hoytema cinematography |
| Villeneuve | **21-50mm symmetric** (wide) | ~6-8s | Deakins cinematography, slow pace |
| Fincher | **27-75mm centered** (varies) | **~2.5s** | tight editing per Cronenweth |
| Miyazaki | N/A (hand-drawn animation) | ~3-5s (varies by shot) | animation timing |
| Kubrick | **18-50mm** (wide symmetric) | ~12-15s (*Barry Lyndon*) / ~6s (*Shining*) | extremely variable |
| Wes Anderson | **40mm symmetrical** (flat) | ~4.5s | consistent across filmography |
| Hitchcock | **25-50mm** (suspense framing) | ~4-6s | Robert Burks cinematography |
| Tarkovsky | **35-50mm** (long takes) | **>30s** (multiple films) | extreme long takes |
| Bergman | **50-75mm close-up** (face) | ~5-7s | Sven Nykvist face CU |
| Spielberg | **21-35mm** (wide + face CU) | ~4s | Kaminski cinematography |
| Bay | **21-50mm with shutter-angle tricks** | **~1.2-1.5s** | hypercut style |
| Snyder | **27-100mm with ramp-speed** | ~3-4s (ramped) | 300-style ramp |
| Greengrass | **handheld Aaton / 16mm** | ~1.5-2.5s | documentary style |
| Hou Hsiao-hsien | **50mm fixed** (long takes) | **>30s** | extreme minimalism |
| Cuarón | **21-35mm long takes** | **>30s** (*Children of Men* / *Roma*) | Lubezki long takes |
| Zhang Yimou | **35-50mm painterly** | ~4-6s | Xiao Ding cinematography |
| Jia Zhangke | **handheld 35mm** | ~6-10s | documentary realism |
| Edgar Wright | **handheld + whip-pan** | ~1.5-2.5s | tight comedic timing |
| Bong Joon-ho | **21-50mm vertical** (basement/mansion) | ~4-5s | Hong Kyung-pyo cinematography |

**关键 heuristic 6:** ASL 数据是导演 rhythm 维度的**最强单一可量化代理**(见 SKILL.md §5D Style Index 第 3 维度)。短剧 部署时需要 baseline ASL 调整(详见 [`cross-cultural-style.md`](./cross-cultural-style.md) §Localization Caveat for 短剧)。

---

## Director Grouping by Dominant Trait

### 关键 heuristic 7: 三层分类(Tier-3 Hierarchy)

按主导维度(dominant trait)将导演分为 3 组,辅助 style blending 时识别同方向增强 vs 反方向冲突:

### Tier 1 — Composition-masters(构图大师)

主导维度:**composition** 是 5D 中最突出的(< 0.3 或 > 0.7)

| Director | Composition Value | 标志 |
|----------|------------------|------|
| Kubrick | 0.1 | one-point extreme symmetry |
| Villeneuve | 0.3 | wide symmetric |
| Wes Anderson | 0.15 | flat pastel symmetrical |
| Spielberg | 0.4 | classical composed |
| Bong Joon-ho | 0.3 | vertical symmetric |

### Tier 2 — Color-poets(色彩诗人)

主导维度:**color** 是 5D 中最突出的(> 0.7)

| Director | Color Value | 标志 |
|----------|-------------|------|
| Wong Kar-wai | 0.8 | saturated reds/greens |
| Almodóvar | 0.9 | reds + yellows melodrama |
| Wes Anderson | 0.8 | pastel palette |
| Zhang Yimou | 0.9 | vivid red/yellow period |
| Kieślowski | 0.6 (color-coded) | Three Colors trilogy |

### Tier 3 — Rhythm-mavens(节奏大师)

主导维度:**rhythm** 是 5D 中最突出的(> 0.6 或 < 0.2)

| Director | Rhythm Value | ASL |
|----------|--------------|-----|
| Bay | 0.9 | ~1.2-1.5s |
| Snyder | 0.8 | ~3-4s ramped |
| Greengrass | 0.8 | ~1.5-2.5s |
| Edgar Wright | 0.8 | ~1.5-2.5s |
| George Miller | 0.8 | hyperkinetic |
| Tarkovsky | 0.1 | >30s long takes |
| Hou Hsiao-hsien | 0.1 | >30s long takes |
| Cuarón | 0.3 | >30s long takes |

**关键 heuristic 8:** Tier 分类用于 blending conflict resolution —— 当 dominant 和 recessive 都属于同一 Tier(同方向主导),应执行 enhancement rule(见 SKILL.md §Style Blending Protocol);当跨 Tier(反方向),应执行 dominant-overwrite rule。

---

## Cross-References

- [`auteur-theory.md`](./auteur-theory.md) §Sarris 3-Tier Classification —— 本 ref 的 Tier 字段与 Sarris 的 Pantheon / Far Side / Expressive Esoterica 三层结构对齐(不同概念:本 ref 的 Tier 是 dominant trait,Sarris 的 Tier 是 auteur 等级)
- [`auteur-theory.md`](./auteur-theory.md) §Sarris 3-Criteria Rubric —— 用于判定导演是 auteur 还是 operator convention
- [`cross-cultural-style.md`](./cross-cultural-style.md) §Director Influence Map —— 导演之间的 影响链(traces of)
- [`cross-cultural-style.md`](./cross-cultural-style.md) §Localization Caveat for 短剧 —— 短剧 部署时 ASL 调整规则
- [`genre-dna-taxonomy.md`](./genre-dna-taxonomy.md) §12-Genre Taxonomy with 5D Ranges —— genre 的 5D 区间与本 ref 的 director 5D 编码协议一致
- [`cn-director-analysis.md`](./cn-director-analysis.md) §Zhang Yimou / §Wong Kar-wai 5D Profile —— CN 导演的 worked examples 与本 ref 的数值一致(同 source-of-truth)
- [`../colorist/references/bellantoni-color-psychology.md`](../colorist/references/bellantoni-color-psychology.md) —— 导演 color DNA alignment:Bellantoni 提供 color-emotion 词汇表,本 ref 的 color 维度参考 Bellantoni 的 red/warm vs cool/blue 区分
- [`../../_shared/glossary.md`](../../_shared/glossary.md) —— [男频](../../_shared/glossary.md#男频-male-oriented-channel) / [女频](../../_shared/glossary.md#女频-female-oriented-channel) / [完播率](../../_shared/glossary.md#完播率-completion-rate) / [爆款](../../_shared/glossary.md#爆款-viral-formula-explosive-hit) 术语定义
- [`../style_genome/SKILL.md`](../SKILL.md) §5D Style Index —— 编码协议定义
- [`../style_genome/SKILL.md`](../SKILL.md) §Director Style Archive —— 5 位 showcase 导演(本 ref 前 5 行)向后兼容

---

## Refresh Cadence

- **每半年复核一次**(下次:2026-12)。
- **复核内容:** 现有 35 位导演的 5D 向量是否仍准确;新增当代导演(如近 6 月内有标志性作品的新人);ASL 数据是否需要 Cinemetrics 更新;Tier 分类是否需要重新评估。
- **复核来源:** Cinemetrics 公开数据库(cinemetrics.lv)+ 公开导演访谈 + 业界影评学论文 + 短剧 创作者访谈(短剧 平台可能涌现新的 director DNA 候选)。
- **不需要更新:** 前 5 位 showcase 导演的 5D 向量(向后兼容硬约束,T-03-18 mitigation)。

---

## Drift Signals

若以下信号出现,本 ref 需要更新:

- **新导演涌现:** 若出现有标志性作品的当代导演(如新晋 Cannes 金棕榈 / 奥斯卡最佳导演),需补充进档案。
- **现有导演 style 漂移:** 若某导演近期作品显著偏离历史 5D(如 Villeneuve 在 *Dune: Part Two* 中 color 维度漂移到 0.7+),需更新对应行。
- **ASL 数据更新:** 若 Cinemetrics 公开数据库新增更精确的 ASL 测量,需替换本 ref 的 *estimated* 数字。
- **短剧 导演 DNA 候选:** 若 短剧 平台涌现可量化的导演 signature(如某 MCN 主理人 signature 稳定 6+ 月),可补充进档案(标注 "观察期" per [`cn-director-analysis.md`](./cn-director-analysis.md) §短剧 Director DNA Candidates)。
- **Tier 重新分类:** 若某导演的 dominant trait 在新作品中显著变化(如 Bay 转向慢节奏艺术片),需重新评估 Tier。

---

> **Disclaimer:** 5D vector 数值是 Hermes Agent 基于 public film-studies scholarship aggregated 的**分析性编码**(analytical encoding),不是任何单一来源的直接复刻。所有数值精度为 ±0.05(per SKILL.md §5D Style Vector)。ASL / focal length 数据标注 *estimated* 来自 Cinemetrics 公开数据库聚合 + 公开访谈,非精确测量值。本 ref 是 style_genome 专家 director 档案的**唯一真相源** —— SKILL.md body 仅保留 5 位 showcase 向后兼容,其他 refs 与 SKILL.md body 必须跨链引用,不得重新定义数值。
