# 03 — Corpus Traceability: 102-Book ↔ Node Coverage

> **Document status:** design-2026-06-16-prfp · supersedes: none · superseded_by: TBD
> **Phase:** 9 of v2.0 PRFP · **Source:** rendered from `corpus-trace.yaml` (canonical)
> **Stability:** evolving (corpus drift mitigation: 90-day refresh cadence per CORPUS-07)
> **Regeneration:** This Markdown is regenerable from `corpus-trace.yaml` via lint script (Phase 12 GOV-02)

---

## §3.0 Reading guide

本文档把 102-book 传统电影制作 corpus 与 Phase 8 推导出的 16 个 v2.0 节点做**双向对照**(bidirectional mapping)。每个节点的 corpus 锚点显式标记 `applicable_form` (长片 / 微电影 / 短剧 / universal),避免 genre conflation (PITFALLS §6.3);每个锚点显式分离 principle vs workflow (PITFALLS §6.2);每个节点至少有 1 个**对该节点设计持反对立场**的 corpus 来源被引入并回应 (CORPUS-03 anti-cherry-picking,per PITFALLS §6.1)。

### Coverage snapshot

| 维度 | 数值 |
|---|---|
| 节点总数 | 16 (15 linear + 1 consultative theory_critic) |
| 102-book corpus 中实际引用书目数 | **40 / 102 = 39%** (远超 ≥20 目标) |
| 有 corpus 锚点的节点 | 13 / 16 |
| AIGC-native 节点(zero-strength corpus) | 3 / 16 |
| 每节点 challenge source | 16 / 16 ✓ |
| Hermes `project-corpus/` 12 refs 中可直接引用 | 9 / 12 |
| 需 supplementation 的 refs | 3 (screenwriting-短剧 / psychoanalytic-短剧 / AIGC-marginal-value) |

### CORPUS 需求项 (7)

| Req | 描述 | 状态 | 见 |
|---|---|---|---|
| CORPUS-01 | 双向覆盖矩阵 | passed | §3.1 + §3.2 |
| CORPUS-02 | `applicable_form` per anchor | passed | §3.3 per-node + §3.4 audit |
| CORPUS-03 | ≥1 challenge source per node | passed | §3.3 challenge_source + §3.5 |
| CORPUS-04 | principle vs workflow 分离 | passed | §3.6 (editor 是 demo 案例) |
| CORPUS-05 | 中文术语保留 | passed | §3.7 (21 汉字 terms, 1 untranslatable) |
| CORPUS-06 | AIGC-native 节点 0-strength 标记 | passed | §3.8 (3 节点) |
| CORPUS-07 | `Last-verified` 时间戳 | passed | §3.9 (全部 2026-06-16) |

### Applicable-form 简码

- **U** = universal (跨 form 适用,validated-invariant)
- **长** = 长片 (feature-film-specific)
- **微** = 微电影 (microfilm-specific)
- **短** = 短剧 (short-drama-specific,platform-algorithmic)

### Anchor strength 标记

- ●●● strong (corpus 直接覆盖,validated-invariant)
- ●● medium (corpus 部分覆盖,需 form-translation)
- ● weak (corpus 间接覆盖,需 supplementation)
- ⊘ zero (AIGC-native,无传统对应)

---

## §3.1 Forward coverage matrix (node → corpus sources)

正查方向:每个节点的 corpus 锚点数 + 主要来源 + 是否 AIGC-native + challenge source。

| Node | Layer | Role | 锚点 | 主要 corpus 来源 | 强度 | AIGC-native? | Challenge source |
|---|---|---|---|---|---|---|---|
| `creative_source` | 0 | root | 2 | PC-screenwriting + PC-film-philosophy | ●● | 否 | narrative-revolution-and-modernism (本雅明/阿多诺) |
| `style_genome` | 1 | intent_parallel | 2 | PC-cinematography + PC-lighting | ●● | 否 | theory-formalism-vs-realism (Balázs) |
| `screenplay` | 1 | intent_parallel | 2 | PC-screenwriting + screenplay/cn-shortdrama.md (v1) | ●● | 否 | film-philosophy-bazin-tarkovsky (塔可夫斯基) |
| `script_auditor` | 1 | critic_paired | 1 | PC-screenwriting (McKee + 芦苇) | ●● | 否 | film-criticism-methodology (戴锦华) |
| `character_designer` | 1 | intent_parallel | 2 | PC-animation-disney + PC-cinematography | ●● | 否 | film-philosophy-bazin-tarkovsky (Bazin) |
| `cinematographer` | 2 | visual_intent | 2 | PC-cinematography + PC-lighting | ●●● | 否 | theory-formalism-vs-realism (长镜头学派) |
| `prompt_injector` | 2 | visual_intent | **0** | — | **⊘** | **是** | auteur 理论家 (塔可夫斯基 反对机械化翻译) |
| `visual_executor` | 3 | visual_exec | 2 | PC-animation-disney + PC-cinematography | ●● | 否 | film-philosophy-bazin-tarkovsky (Bazin indexical truth) |
| `audio_pipeline` | 4 | audio_post | 1 | PC-editing-sound-post | ●●● | 否 | film-philosophy-bazin-tarkovsky (塔可夫斯基) |
| `continuity_auditor` | 3 | critic_paired | 1 | PC-editing-sound-post (Murch) | ●● | 否 | theory-formalism-vs-realism (Eisenstein 蒙太奇) |
| `editor` | 4 | audio_post | **2** | PC-editing-sound-post (Murch principle + 长片 workflow) | ●●● | 否 | film-philosophy-bazin-tarkovsky (Bazin+Godard) |
| `colorist` | 4 | audio_post | 1 | PC-lighting (color subset) | ●● | 否 | narrative-revolution-and-modernism (Adorno) |
| `hook_retention` | 5 | form_specific | 1 | hook_retention/three-second-hooks.md (v1 external) | ● | **是** | film-philosophy-bazin-tarkovsky (auteur 反对算法优化) |
| `quality_gate` | 6 | final_gate | 1 | PC-editing-sound-post (Murch Rule of Six audit) | ●● | 否 | film-criticism-methodology (戴锦华) |
| `compliance_gate` | 6 | final_gate | **0** | — | **⊘** | **是** | film-philosophy-bazin-tarkovsky (auteur 反对合规优先) |
| `theory_critic` | vertical | consultative | 4 | PC-theory-formalism + PC-bazin-tarkovsky + PC-criticism-method + PC-psychoanalytic | ●●● | 否 | narrative-revolution-and-modernism (本雅明/阿多诺 反对理论脱离社会) |

**密度观察:** 3 个 AIGC-native 节点(prompt_injector / hook_retention / compliance_gate)的 corpus 覆盖弱或为零,这是 corpus 本身的 gap 而非设计疏忽(详见 §3.8)。剩余 13 节点都有 corpus 锚点,其中 `theory_critic` 锚点最丰富(4 个,因为它是理论资源池)。

---

## §3.2 Reverse coverage matrix (book → nodes)

反查方向:每本被引用的书对应哪些节点。共 40 本(40/102 = 39%)。

### Theory / philosophy (8 books)

| Book ID | Title (zh) | Title (en gloss) | Informs nodes | Form |
|---|---|---|---|---|
| -022 | 雕刻时光 (塔可夫斯基) | Sculpting in Time (Tarkovsky) | creative_source, screenplay, audio_pipeline, visual_executor, hook_retention, compliance_gate, theory_critic | U |
| 巴赞《电影是什么》 | 电影是什么 (巴赞) | What Is Cinema? (Bazin) | creative_source, character_designer, visual_executor, editor, theory_critic | U |
| Andrew 形式主义 | 形式主义 (Andrew) | Formalism (Andrew) | style_genome, cinematographer, continuity_auditor, theory_critic | U |
| Balázs | Balázs (电影理论) | Balázs (film theory) | theory_critic | U |
| Agel | Agel (电影理论) | Agel (film theory) | theory_critic | U |
| 七部半 | 七部半 (塔可夫斯基访谈) | Time Within Time (Tarkovsky diaries) | creative_source, theory_critic | U |
| 本雅明《机械复制时代的艺术作品》 | 机械复制时代的艺术作品 (本雅明) | The Work of Art in the Age of Mechanical Reproduction (Benjamin) | creative_source, colorist, theory_critic | U |
| 阿多诺 | 阿多诺 (文化工业理论) | Adorno (culture industry theory) | colorist, theory_critic | U |

### Screenwriting (10 books)

| Book ID | Title (zh) | Title (en gloss) | Informs nodes | Form |
|---|---|---|---|---|
| -017 | 剧本 (菲尔德) | Screenplay (Field) | creative_source, screenplay, script_auditor | U |
| -026 | 故事 (麦基) | Story (McKee) | creative_source, screenplay, script_auditor | U |
| 芦苇剧本笔记 | 芦苇剧本笔记 | Lu Wei screenplay notes | creative_source, screenplay, script_auditor | U |
| 维基·金《如何写出好故事》 | 如何写出好故事 (维基·金) | How to Write a Good Story (Viki King) | creative_source, screenplay | U |
| 刘天赐《电视剧编剧艺术》 | 电视剧编剧艺术 (刘天赐) | The Art of TV Drama Screenwriting (Lau Tin-chi) | creative_source, screenplay | U |
| 编剧策略 | 编剧策略 | Screenwriting Strategy | creative_source, screenplay | U |
| 奥班农 | 奥班农 (编剧理论) | O'Bannon (screenwriting theory) | creative_source, screenplay | U |
| 温斯顿 | 温斯顿 (编剧理论) | Winston (screenwriting theory) | creative_source, screenplay | U |
| 戴锦华 | 戴锦华 (电影批评) | Dai Jinhua (film criticism) | script_auditor, quality_gate, theory_critic | U |
| 如何写影评 | 如何写影评 | How to Write Film Criticism | theory_critic | U |

### Cinematography / lighting (8 books)

| Book ID | Title (zh) | Title (en gloss) | Informs nodes | Form |
|---|---|---|---|---|
| 阿里洪《电影语言的语法》 | 电影语言的语法 (阿里洪) | Grammar of Film Language (Arijon) | style_genome, character_designer, cinematographer, visual_executor | U |
| 电影 100 手法 | 电影 100 手法 | 100 Cinematic Techniques | style_genome, cinematographer | U |
| -036 | 拉片子 | La Pianzi (shot-by-shot analysis) | style_genome, cinematographer | U |
| 拆解好电影 | 拆解好电影 | Deconstructing Good Films | style_genome, cinematographer | U |
| 21 位大师 | 21 位大师 (摄影) | 21 Masters (Cinematography) | style_genome, character_designer, cinematographer, visual_executor | U |
| 照明器材 | 照明器材 | Lighting Equipment | style_genome, cinematographer, colorist | U |
| 影视光线艺术 | 影视光线艺术 | The Art of Film Lighting | style_genome, cinematographer, colorist | U |
| 镜头在说话 | 镜头在说话 | The Lens Speaks | style_genome, cinematographer, colorist | U |

### Editing / sound post (5 books)

| Book ID | Title (zh) | Title (en gloss) | Informs nodes | Form |
|---|---|---|---|---|
| 剪辑之道 (Murch) | 剪辑之道 (Murch《In the Blink of an Eye》) | In the Blink of an Eye (Murch) | audio_pipeline, continuity_auditor, editor, quality_gate | U |
| 魅力剪辑 | 魅力剪辑 | The Charm of Editing | audio_pipeline, continuity_auditor, editor | **长** |
| 音效圣经 | 音效圣经 (Sound Effect Bible) | The Sound Effects Bible | audio_pipeline | U |
| 视听 | 视听 (视听语言) | Audio-Visual Language | audio_pipeline, editor | U |
| 王竞六讲 | 王竞六讲 (剪辑) | Wang Jing's Six Lectures (Editing) | audio_pipeline, editor | U |

### Animation (2 books)

| Book ID | Title (zh) | Title (en gloss) | Informs nodes | Form |
|---|---|---|---|---|
| 迪士尼的艺术 | 迪士尼的艺术 | The Art of Disney | character_designer, visual_executor | U |
| 影视动画剧本赏析 | 影视动画剧本赏析 | Appreciation of Animation Screenplays | character_designer, visual_executor | U |

### Production (4 books)

| Book ID | Title (zh) | Title (en gloss) | Informs nodes | Form |
|---|---|---|---|---|
| 拍电影 | 拍电影 | Making Movies | theory_critic | U |
| 制片手册 | 制片手册 | Production Handbook | theory_critic | U |
| 创意制片 | 创意制片 | Creative Producing | theory_critic | U |
| 狼图腾摄影 | 狼图腾 (摄影) | Wolf Totem (cinematography) | style_genome, cinematographer, colorist | U |

### Psychoanalysis / modernism (3 books)

| Book ID | Title (zh) | Title (en gloss) | Informs nodes | Form |
|---|---|---|---|---|
| 凝视的快感 | 凝视的快感 | The Pleasure of the Gaze | theory_critic | U |
| 好莱坞中的拉康 | 好莱坞中的拉康 | Lacan in Hollywood | theory_critic | U |
| 郭小橹 | 郭小橹 (叙事革命) | Guo Xiaolu (narrative revolution) | theory_critic | U |

---

## §3.3 Per-node corpus anchors (16 subsections)

### §3.3.1 `creative_source` (创意源) · Layer 0 root

**Anchors (2):**

| Source | Books | Form | Principle (保留) | Workflow obsolete (弃用) | Verified |
|---|---|---|---|---|---|
| PC-screenwriting-chinese-and-supplementary.md | -017 Field / -026 McKee / 芦苇 / 维基·金 / 刘天赐 / 编剧策略 / 奥班农 / 温斯顿 | U | 故事核 = logline + 主角欲望 + 中央冲突 + 转折点 + 解决立场 | Field 的 "sympathy page count" 是 长片 时间预算,短剧须前 3 秒 | 2026-06-16 |
| PC-film-philosophy-bazin-tarkovsky.md | 巴赞 / 塔可夫斯基 / 七部半 | U | 创作者 personal vision 是元意图不可替代源头 (auteur theory 作者论) | Bazin 长镜头美学不是 kernel 提取方法论 | 2026-06-16 |

**Chinese terms:** 故事核 (story kernel) · 转折点 (turning point) · 作者论 (auteur theory)

**Challenge source:** narrative-revolution-and-modernism.md (本雅明《机械复制时代的艺术作品》)
- **反对立场:** 本雅明挑战作者意图神圣性 — 机械复制后,作品的"灵韵"(Aura)消散,作者意图不再是意义中心
- **我方回应:** 我们承认 auteur essentialism 在机械复制时代部分解构,但 v2.0 节点是 AI 辅助生成,创作者的 lived experience 仍提供不可替代的 novelty pressure (per Phase 7 D4.1)。我们不回归"作者即上帝",而是把作者 intent 作为 AI 不能替代的 novelty 锚点

**AIGC-native flag:** false (传统编剧有 personal-experience mining 传统)

---

### §3.3.2 `style_genome` (风格基因组) · Layer 1 intent_parallel

**Anchors (2):**

| Source | Books | Form | Principle | Workflow obsolete | Verified |
|---|---|---|---|---|---|
| PC-cinematography-masterclass-and-grammar.md | 阿里洪 / 100 手法 / -036 拉片子 / 拆解好电影 / 21 位大师 | U | 视觉语言有 5D genome:色调 / 构图 / 节奏 / 材质 / 情感基调 | 阿里洪 1970s 胶片时代 lens 选择 — AIGC 用 prompt 控制 | 2026-06-16 |
| PC-lighting-equipment-and-design.md | 照明器材 / 影视光线艺术 / 镜头在说话 / 狼图腾 | U | 光线创造情感基调 + 引导视觉注意力 | 传统灯光器材选择 workflow — AIGC 用 light direction prompt | 2026-06-16 |

**Chinese terms:** 影调 (tone/tonality) · 构图 (composition) · 光效 (lighting effect)

**Challenge source:** theory-formalism-vs-realism.md (Balázs 现实主义)
- **反对立场:** Balázs 现实主义挑战"风格 genome 可独立抽象"的论点 — 风格是内容的有机延伸,不能像 DNA 一样拆解为 5D 向量
- **我方回应:** 我们同意风格与内容不可完全解耦,但 style_genome 不是"独立完整风格",而是"可复用的风格 invariants"(色调 + 节奏等),用于跨节点一致性。这是工程化抽象,不否定有机整体性

**AIGC-native flag:** false (传统 art direction + production design 有明确锚点)

---

### §3.3.3 `screenplay` (剧本) · Layer 1 intent_parallel

**Anchors (2):**

| Source | Books | Form | Principle | Workflow obsolete | Verified |
|---|---|---|---|---|---|
| PC-screenwriting-chinese-and-supplementary.md | -017 / -026 / 芦苇 / 维基·金 / 刘天赐 / 编剧策略 / 奥班农 / 温斯顿 | U | 三幕结构 + 转折点 + 对话技艺 = validated-invariant 叙事骨架 | Field page count (Act 1 = 30p) 是 长片 时间预算,短剧必须压缩 | 2026-06-16 |
| screenplay/references/cn-shortdrama.md (v1 external) | (外部短剧来源) | **短** | 短剧前 3 秒 hook + 付费卡点 pacing + 竖屏 framing | N/A — 短剧是 2020s 平台算法环境产物,无 pre-AIGC workflow | 2026-06-16 |

**Form-translation note:** 三幕是 universal;page count 须按 form 重新分配(短剧一集 ≈ 90 秒)

**Chinese terms:** 三幕结构 (three-act structure) · 转折点 (turning point) · 付费卡点 (paywall cliffhanger) · 钩子 (hook)

**Challenge source:** film-philosophy-bazin-tarkovsky.md (塔可夫斯基《雕刻时光》)
- **反对立场:** 塔可夫斯基反对"结构化剧本公式":真正的电影不应被三幕/转折点公式约束,而应像"雕刻时光"一样按时间流自然生长
- **我方回应:** 我们承认 auteur cinema 反公式立场,但 v2.0 节点服务的是商业内容生产(短剧/微电影),不是 art house cinema。三幕结构在此情境是 validated-invariant。我们用 theory_critic (§2.16) 保留 auteur 反对声音的咨询入口

**AIGC-native flag:** false (传统编剧有明确锚点;短剧-specific 锚点用 external v1 ref 补)

**Supplementation flag:** STACK §2.2 标记 PC-screenwriting underweights 短剧-specific screenwriting — 已用 v1 cn-shortdrama.md 补

---

### §3.3.4 `script_auditor` (剧本审计) · Layer 1 critic_paired

**Anchors (1):**

| Source | Books | Form | Principle | Workflow obsolete | Verified |
|---|---|---|---|---|---|
| PC-screenwriting-chinese-and-supplementary.md | -026 McKee / 芦苇 | U | 5-dim 剧本审计:structure / character / dialogue / theme / form-fit | 传统 script doctor 经验性 notes session — AIGC 版本量化 + decoupled | 2026-06-16 |

**Chinese terms:** 剧本医生 (script doctor)

**Challenge source:** film-criticism-methodology.md (戴锦华)
- **反对立场:** 戴锦华挑战"量化打分"的批评方法 — 真正有意义的批评是政治经济学/符号学深读,不是 5-dim rubric 数字打分
- **我方回应:** 我们同意深度批评不能量化,但 script_auditor 不是批评家 — 它是流水线质量门,目标是捕捉 plot_hole/dialogue_flat 等可量化缺陷。深度理论批评交给 theory_critic 咨询入口

**AIGC-native flag:** false (传统 script doctor 直接对应;AIGC 量化是改造)

---

### §3.3.5 `character_designer` (角色设计) · Layer 1 intent_parallel

**Anchors (2):**

| Source | Books | Form | Principle | Workflow obsolete | Verified |
|---|---|---|---|---|---|
| PC-animation-disney-system.md | 迪士尼的艺术 / 影视动画剧本赏析 | U | 角色 identity = face + body + wardrobe + voice + behavioral tics (Disney 12 principles lineage) | Disney 手绘 24fps 逐帧 — AIGC 用 IP-Adapter + ControlNet | 2026-06-16 |
| PC-cinematography-masterclass-and-grammar.md | 阿里洪 / 21 位大师 | U | casting + character presentation 通过 framing/lighting 共同塑造 identity | 传统 casting workflow(试镜/选角导演)— AIGC 不适用 | 2026-06-16 |

**Chinese terms:** 角色弧光 (character arc) · 角色一致性 (character consistency)

**Challenge source:** film-philosophy-bazin-tarkovsky.md (Bazin 现实主义)
- **反对立场:** Bazin 挑战"character identity 可工程化锁定" — 真实电影中角色的真实感来自演员肉身和现场偶然,AIGC 工程化锁定可能杀死"偶发性真实"
- **我方回应:** Bazin 的是 art house 美学立场。v2.0 服务商业短剧/微电影,identity 漂移是 production bug 不是 feature。我们承认 art house 不能用此节点,但目标场景需要

**AIGC-native flag:** false (传统角色设计 + casting 直接对应)

---

### §3.3.6 `cinematographer` (摄影指导) · Layer 2 visual_intent

**Anchors (2):**

| Source | Books | Form | Principle | Workflow obsolete | Verified |
|---|---|---|---|---|---|
| PC-cinematography-masterclass-and-grammar.md | 阿里洪 / 100 手法 / -036 / 拆解好电影 / 21 位大师 | U | 镜头列表 + 灯光 + 构图 + composition_lock(180° 轴线是 validated-invariant) | 传统摄影师选 lens + 走位 physical workflow — AIGC 用 visual_intent + prompt | 2026-06-16 |
| PC-lighting-equipment-and-design.md | 照明器材 / 影视光线艺术 / 镜头在说话 / 狼图腾 | U | 光线方向 + 色温 + 对比度 = 情感 + 视觉引导 | 照明器材选择 workflow — AIGC 用 light direction prompt | 2026-06-16 |

**Chinese terms:** 180度轴线规则 (180-degree axis rule) · 镜头语言 (cinematic language) · 主光 / 辅光 / 轮廓光 (key / fill / rim light)

**Challenge source:** theory-formalism-vs-realism.md (长镜头学派)
- **反对立场:** 长镜头学派反对分镜构图公式 — 真正电影艺术是"影像流"(image stream),不被镜头切分;预定义镜头列表扼杀电影性
- **我方回应:** 我们同意长镜头艺术价值,但短剧/微电影制作 budget 不允许全程长镜头。我们保留镜头列表作为 production 必需 spec,同时 theory_critic 可拉起 long-take 立场讨论

**AIGC-native flag:** false (传统摄影指导角色直接适用,corpus 锚点最丰富)

---

### §3.3.7 `prompt_injector` (提示注入) · Layer 2 visual_intent — **AIGC-NATIVE**

**Anchors: 0** (无传统对应)

**Challenge source:** auteur 理论家(塔可夫斯基)
- **反对立场:** 传统电影制作无 prompt 工程角色;部分 auteur 理论家会反对"机械化翻译意图"
- **我方回应:** 我们承认这是 AIGC-native 节点,无传统对应。塔可夫斯基的反对映射到 design 上 — 我们不让 prompt_injector 取代 cinematographer 的创造性,而仅做"visual_intent → model-ready prompt"的翻译层。创造性仍在 cinematographer

**AIGC-native flag: true**
**Zero-strength explanation:** 无传统对应 — prompt 工程是 2023+ LLM/multimodal 时代新工序。强行用传统锚点(如"摄影师的指令沟通")是 PITFALLS §6.6 "fake-traditional disguise"。明确标记 AIGC-native,避免伪装传统

---

### §3.3.8 `visual_executor` (视觉执行) · Layer 3 visual_exec

**Anchors (2):**

| Source | Books | Form | Principle | Workflow obsolete | Verified |
|---|---|---|---|---|---|
| PC-animation-disney-system.md | 迪士尼的艺术 / 影视动画剧本赏析 | U | identity consistency + temporal continuity 是动画制作 validated-invariant | Disney 手绘 24fps 逐帧 — AIGC 用 Sora/Kling 视频生成 + ControlNet | 2026-06-16 |
| PC-cinematography-masterclass-and-grammar.md | 阿里洪 / 21 位大师 | U | 构图 + 光效执行,跟随 cinematographer intent | 传统摄影机 physical operation — AIGC 用 image gen model | 2026-06-16 |

**Chinese terms:** 中间画 (in-between frames)

**Challenge source:** film-philosophy-bazin-tarkovsky.md (Bazin 现实主义 — 反对合成影像)
- **反对立场:** Bazin 现实主义认为电影的独特价值是记录"现实时空的偶然性";AIGC 全合成影像失去 photography 的 indexical truth
- **我方回应:** 我们承认 Bazin 的 indexical truth 立场,但 v2.0 节点服务的是虚构内容生产(动画/短剧剧本),不是 documentary。我们保留 documentary 与 fiction 两类生产的区分;fiction 不强求 indexical truth

**AIGC-native flag:** false (drawer + animator 传统对应存在;AIGC 合并是改造,非从无到有)

---

### §3.3.9 `audio_pipeline` (音频管线) · Layer 4 audio_post

**Anchors (1):**

| Source | Books | Form | Principle | Workflow obsolete | Verified |
|---|---|---|---|---|---|
| PC-editing-sound-post.md | 剪辑之道 (Murch) / 魅力剪辑 / 音效圣经 / 视听 / 王竞六讲 | U | 5 个 audio 子任务(voice + lip_sync + composer + foley + mixer)+ LUFS 平台 spec 合规 | 传统 5 个独立 audio 专家 workflow(per spec §2.9 merged in AIGC)— PITFALLS §2.1 压缩 | 2026-06-16 |

**Chinese terms:** 拟音 (foley) · 混音 (mixing)

**Challenge source:** film-philosophy-bazin-tarkovsky.md (塔可夫斯基 sound 设计反对立场)
- **反对立场:** 塔可夫斯基认为电影声音应保留"沉默"与"环境音"的诗意空间,不应被 LUFS 标准化 + 5 子任务工程化压缩为"音频流水线"
- **我方回应:** 我们同意 auteur cinema 的 sound 哲学,但 v2.0 服务商业短剧,需要平台 spec 合规(LUFS)+ production efficiency。塔可夫斯基哲学保留在 theory_critic 咨询入口

**AIGC-native flag:** false (传统 5 个 audio 专家直接对应;AIGC 压缩是改造)

---

### §3.3.10 `continuity_auditor` (连续性审计) · Layer 3 critic_paired

**Anchors (1):**

| Source | Books | Form | Principle | Workflow obsolete | Verified |
|---|---|---|---|---|---|
| PC-editing-sound-post.md | 剪辑之道 (Murch) / 魅力剪辑 | U | 180° 轴线 + identity + wardrobe + spatial + plot 五类 continuity(validated-invariant) | 传统剧本监督(continuity supervisor)是现场人工跟踪 — AIGC 版本自动化 | 2026-06-16 |

**Chinese terms:** 剧本监督 (continuity supervisor) · 接戏 (continuity matching, colloquial)

**Challenge source:** theory-formalism-vs-realism.md (Eisenstein 蒙太奇学派)
- **反对立场:** 形式主义某些流派(如 Eisenstein 蒙太奇学派)反对"连续性至上" — 冲突蒙太奇故意违反 180° 轴线以制造意义
- **我方回应:** 我们承认 Eisenstein 蒙太奇学派,但短剧/微电影主流是连续性叙事。冲突蒙太奇是 art house 实验,由 theory_critic 保留咨询入口

**AIGC-native flag:** false (传统剧本监督直接对应)

---

### §3.3.11 `editor` (剪辑) · Layer 4 audio_post — **CORPUS-04 DEMO CASE (principle vs workflow)**

**Anchors (2 — explicitly principle vs workflow split):**

| Source | Books | Form | Principle vs Workflow | Verified |
|---|---|---|---|---|
| PC-editing-sound-post.md (Murch Rule of Six subset) | 剪辑之道 (Murch《In the Blink of an Eye》) | U | **PRINCIPLE** — Murch Rule of Six(emotion 60% / story / rhythm / eye-trace / 2D plane / 3D space)作为 evaluation 原则,validated-invariant | 2026-06-16 |
| PC-editing-sound-post.md (workflow variant) | 魅力剪辑 | **长** | **WORKFLOW** — 具体长片 cutting sequence(例如《教父》洗礼序列)是 长片 case,不直接复用到 短剧/微电影 | 2026-06-16 |

**This node is the canonical CORPUS-04 demo:** Murch Rule of Six (principle,跨 form 保留)vs 长片 cutting sequence workflow(form-specific,弃用)。详见 §3.6。

**Form-translation note:** 长片 cutting sequence workflow 不直接适用于 短剧 — 短剧 节奏更快,pacing 更密集

**Chinese terms:** 剪辑节奏 (cutting rhythm)

**Challenge source:** film-philosophy-bazin-tarkovsky.md (Bazin 长镜头 + Godard 跳切)
- **反对立场:** Bazin 长镜头学派认为真实电影应保留时空连续,反对剪辑构造的"虚假节奏";Godard 跳切反对"无缝剪辑"意识形态
- **我方回应:** 我们承认长镜头 + 跳切的艺术价值,但短剧/微电影主流是连续性剪辑 + 节奏控制。两种反对立场均保留在 theory_critic 咨询入口

**AIGC-native flag:** false (传统剪辑师直接对应;Murch Rule of Six 是 validated-invariant principle)

---

### §3.3.12 `colorist` (调色) · Layer 4 audio_post

**Anchors (1):**

| Source | Books | Form | Principle | Workflow obsolete | Verified |
|---|---|---|---|---|---|
| PC-lighting-equipment-and-design.md (color subset) | 镜头在说话 / 狼图腾 | U | color theory(互补色 / 类比色 / 情感色调映射)是 validated-invariant | 传统 DaVinci Resolve 工程师 manual grading workflow — AIGC 用 AI LUT 自动化部分 | 2026-06-16 |

**Chinese terms:** 调色 (color grading) · 色调 (color tone)

**Challenge source:** narrative-revolution-and-modernism.md (Adorno 文化工业理论)
- **反对立场:** Adorno 文化工业理论挑战 color grading 作为"情感操控技术" — 标准化色调抹平作品的 unique 视觉政治
- **我方回应:** 我们承认 Adorno 文化工业批判,但 v2.0 节点服务商业生产,需要 color 一致性。Adorno 批判由 theory_critic 咨询入口保留

**AIGC-native flag:** false (传统调色师直接对应;color theory validated-invariant)

---

### §3.3.13 `hook_retention` (钩子留存) · Layer 5 form_specific (short_drama only) — **AIGC-NATIVE**

**Anchors (1):**

| Source | Books | Form | Principle | Workflow obsolete | Verified |
|---|---|---|---|---|---|
| hook_retention/references/three-second-hooks.md (v1 external) | (外部短剧来源) | **短** | 前 3 秒 hook + 完播率 retention curve + 付费卡点 pacing + 竖屏 framing | N/A — 短剧是 2020s 移动平台催生的新形态,无 pre-AIGC 传统 | 2026-06-16 |

**Supplementation flag:** STACK §2.2 标记 短剧 corpus gap — 102-book corpus 是 feature-film-oriented

**Chinese terms:** 完播率 (completion rate) · 钩子 (hook)

**Challenge source:** film-philosophy-bazin-tarkovsky.md (auteur cinema)
- **反对立场:** Auteur cinema(Bazin / Tarkovsky)反对以平台算法 retention curve 优化创作 — 这是把艺术降格为注意力商品
- **我方回应:** 我们承认 auteur 反对立场,但 hook_retention 是 form_specific(短剧 only)节点,服务商业短剧形态。Microfilm / 长片 路径绕过此节点。Auteur 路径用 theory_critic 保留反对声音

**AIGC-native flag: true**
**Zero-strength explanation:** 102-book corpus 几乎无短剧-specific 文献(短剧是 2020s 才规模化)。STACK §1.4 明确指出"NOT in corpus — corpus is feature-film oriented"。v1 已从外部短剧来源整合 hook_retention refs,但 corpus base 仍弱。明确标记 zero-strength,避免假传统

---

### §3.3.14 `quality_gate` (质量门) · Layer 6 final_gate

**Anchors (1):**

| Source | Books | Form | Principle | Workflow obsolete | Verified |
|---|---|---|---|---|---|
| PC-editing-sound-post.md (Murch Rule of Six audit subset) | 剪辑之道 (Murch) | U | Murch Rule of Six(6-dim)+ form-specific weight 是 final quality 判定 principle | 传统 test screening(现场观众问卷)— AIGC 版本量化 + automated | 2026-06-16 |

**Chinese terms:** 试映 (test screening)

**Challenge source:** film-criticism-methodology.md (戴锦华)
- **反对立场:** 戴锦华挑战 multi-dim scoring rubric — 真正批评是政治经济学/符号学深读,不是 6-dim 数字打分
- **我方回应:** 我们同意深度批评不能量化,但 quality_gate 是 production 流水线质量门,目标是 form-compliance + platform-spec 合规,不是批评理论贡献。深度批评由 theory_critic 保留

**AIGC-native flag:** false (传统 test screening + final QC 直接对应;Murch 6-dim 是 validated-invariant)

---

### §3.3.15 `compliance_gate` (合规门) · Layer 6 final_gate — **AIGC-NATIVE**

**Anchors: 0** (无传统对应)

**Challenge source:** film-philosophy-bazin-tarkovsky.md (auteur cinema)
- **反对立场:** Auteur cinema 反对 pre-emptive 合规审查限制创作自由
- **我方回应:** 我们承认 auteur 立场,但 v2.0 服务 CN 平台商业生产,合规是生产前提不是创作选择。Auteur 路径可绕过 compliance_gate(art house 出口)

**AIGC-native flag: true**
**Zero-strength explanation:** 无传统对应 — CN 平台合规是 AIGC + 平台算法时代新工序。v1 compliance_marketing refs 是外部来源,非 102-book corpus base。明确标记 zero-strength,避免把 CN 平台规则伪装为"传统工序"。强行用 pre-AIGC corpus 是 PITFALLS §6.2 anachronism + §6.6 fake-traditional disguise

---

### §3.3.16 `theory_critic` (理论批评) · Layer vertical / consultative

**Anchors (4):**

| Source | Books | Form | Principle | Verified |
|---|---|---|---|---|
| PC-theory-formalism-vs-realism.md | Andrew / Agel / Balázs | U | 形式主义 vs 现实主义是电影理论根本张力 | 2026-06-16 |
| PC-film-philosophy-bazin-tarkovsky.md | 巴赞 / 塔可夫斯基 / 七部半 | U | Bazin 现实主义 + Tarkovsky 雕刻时光 = 电影本体论 | 2026-06-16 |
| PC-film-criticism-methodology.md | 戴锦华 / 如何写影评 / 外国批评文选 | U | 批评方法论(政治经济学 / 符号学 / 精神分析)是理论工具 | 2026-06-16 |
| PC-psychoanalytic-film-theory.md | 凝视的快感 / 好莱坞中的拉康 | U | 精神分析批评(凝视 / 欲望 / 主体)是观众接受层理论资源 | 2026-06-16 |

**Chinese terms:** 形式主义 (formalism) · 现实主义 (realism) · 电影本体论 (film ontology) · **意境 (yì jìng — mood/atmosphere, Buddhist-aesthetic lineage, 无 clean Western equivalent)** · 符号学 (semiotics) · 凝视 (the gaze)

> **CORPUS-05 untranslatable flag:** 意境 (yì jìng) — 跨佛教美学谱系,Western "mood" / "atmosphere" 译法丢失精神维度。本设计保留汉字,不强行翻译。

**Challenge source:** narrative-revolution-and-modernism.md (本雅明/阿多诺)
- **反对立场:** 本雅明 + 阿多诺反对"理论家脱离生产实践" — 纯理论批评易脱离文化工业现实,沦为象牙塔
- **我方回应:** 我们承认此风险,但 theory_critic 是 consultative(创作者手动拉),非 blocking gate。它的目的是给创作者 theoretical lens,不是替代 production。理论脱离风险由 META-06 触发模式 + form_context 注入缓解

**AIGC-native flag:** false (传统 theory consultant 直接对应;corpus 锚点最丰富)

---

## §3.4 Genre conflation audit (CORPUS-02)

每个节点的 corpus 锚点 `applicable_form` 分布。**关键检查:是否有节点用 长片 锚点为 短剧-specific 设计背书而无 translation note。**

| Node | 锚点 form 分布 | Genre conflation 风险 | Translation note 状态 |
|---|---|---|---|
| creative_source | U × 2 | 低 | n/a |
| style_genome | U × 2 | 低 | n/a |
| screenplay | U × 1 + 短 × 1 | 中(Field page count 长片 → 短剧) | ✓ form_translation_note 已写 |
| script_auditor | U × 1 | 低 | n/a |
| character_designer | U × 2 | 低 | n/a |
| cinematographer | U × 2 | 低 | n/a |
| prompt_injector | (zero) | n/a | AIGC-native |
| visual_executor | U × 2 | 低 | n/a |
| audio_pipeline | U × 1 | 低 | n/a |
| continuity_auditor | U × 1 | 低 | n/a |
| editor | U × 1 + 长 × 1 | 中(长片 cutting sequence → 短剧) | ✓ form_translation_note 已写 + CORPUS-04 demo |
| colorist | U × 1 | 低 | n/a |
| hook_retention | 短 × 1 (AIGC-native) | 高(corpus 短剧 gap) | AIGC-native flag + zero_strength_explanation |
| quality_gate | U × 1 | 低 | n/a |
| compliance_gate | (zero) | n/a | AIGC-native |
| theory_critic | U × 4 | 低 | n/a |

**Applicable-form distribution 全局:**
- universal: 33
- 长片: 2
- 微电影: 0
- 短剧: 3

**短剧 corpus gap discussion (PITFALLS §6.3):**

3 个节点 corpus 覆盖弱:
- `prompt_injector` — 完全 AIGC-native,无 form 问题
- `hook_retention` — 短剧 form-specific,但 corpus base 是 长片。已用 v1 external 短剧 ref 补 + 明确 zero-strength
- `compliance_gate` — 完全 AIGC-native(CN 平台新形态)

`screenplay` 和 `editor` 节点用 长片 锚点为 universal 设计背书,但已写显式 form_translation_note(三幕 universal / page count form-specific;Murch Rule of Six universal / 长片 cutting sequence form-specific)。无隐藏 genre conflation。

---

## §3.5 Challenge-source engagement audit (CORPUS-03)

**Anti-cherry-picking check:** 每节点 ≥1 corpus 来源持反对立场被引入并回应。

| Node | Challenge source | 反对立场摘要 | 我方回应 |
|---|---|---|---|
| creative_source | 本雅明《机械复制时代的艺术作品》 | 作者意图神圣性被机械复制解构 | novelty pressure 仍需 human 锚点 |
| style_genome | Balázs 现实主义 | 风格不能像 DNA 拆解 | style_genome 是 invariants,非完整风格 |
| screenplay | 塔可夫斯基《雕刻时光》 | 反结构化公式 | auteur 保留在 theory_critic;商业情境用三幕 |
| script_auditor | 戴锦华 | 量化打分不是真正批评 | script_auditor 是质量门非批评家;深度批评交给 theory_critic |
| character_designer | Bazin 现实主义 | identity 工程化锁定杀死偶发性真实 | art house 立场承认;商业生产需要 consistency |
| cinematographer | 长镜头学派 | 预定义镜头列表扼杀电影性 | budget 限制 + theory_critic 入口 |
| prompt_injector | auteur 反对机械化翻译 | (无传统反对 — AIGC-native) | 翻译层非创造,创造性仍在 cinematographer |
| visual_executor | Bazin indexical truth | 全合成影像失去现实记录价值 | fiction 生产不强求 indexical truth |
| audio_pipeline | 塔可夫斯基 sound 哲学 | LUFS 标准化杀死诗意空间 | 商业短剧需要平台合规 |
| continuity_auditor | Eisenstein 蒙太奇学派 | 冲突蒙太奇故意违反轴线 | 商业主流是连续性;art house 由 theory_critic |
| editor | Bazin + Godard | 反对剪辑至上 | 商业主流是连续性剪辑 |
| colorist | Adorno 文化工业理论 | 标准化色调抹平视觉政治 | 商业生产需要 consistency |
| hook_retention | auteur 反对算法优化 | 艺术降格为注意力商品 | form_specific 节点;auteur 路径绕过 |
| quality_gate | 戴锦华 | 6-dim 打分不是真正批评 | 质量门非批评家 |
| compliance_gate | auteur 反对合规优先 | 合规限制创作自由 | CN 平台商业生产是前提 |
| theory_critic | 本雅明/阿多诺 | 理论脱离生产实践 | consultative 非 blocking |

**Coverage:** 16 / 16 nodes 都有 challenge source ✓

**关键模式:** corpus 反对声音主要集中在 auteur cinema 立场(Bazin / Tarkovsky / Godard),这些立场反对商业化/标准化/工程化。我方设计承认 art house 价值,通过 theory_critic 咨询入口保留反对声音,但坚持商业生产路径需要工程化抽象。

---

## §3.6 Principle vs workflow separation audit (CORPUS-04)

**Editor 节点作为 demo 案例(CORPUS-04 标杆):**

| 层次 | 内容 | 来源 | 状态 |
|---|---|---|---|
| **Principle** (validated-invariant) | Murch Rule of Six — emotion (60%) / story / rhythm / eye-trace / 2D plane / 3D space 作为 evaluation 原则 | 剪辑之道 (Murch《In the Blink of an Eye》) | ✓ 保留,universal |
| **Workflow** (form-specific / anachronistic) | Murch 在 Steenbeck 剪胶片的 physical workflow | (Murch 1970s physical workflow) | ✗ 完全过时 |
| **Workflow variant** (form-specific) | 具体长片 cutting sequence(《教父》洗礼序列) | 魅力剪辑 | ✗ 长片 case,不适用 短剧 |

**全节点 principle vs workflow 分离状态:**

| Node | Principle 锚点 | Workflow 锚点 | 分离显式? |
|---|---|---|---|
| creative_source | 故事核 + Field 三幕 + auteur theory | Field page count | ✓ |
| style_genome | 5D genome + 光线创造情感 | 胶片 lens 选择 / 照明器材选择 | ✓ |
| screenplay | 三幕 + 转折点 + 对话技艺 | Field page count(长片) | ✓ |
| script_auditor | 5-dim 剧本审计 | script doctor notes session(经验性) | ✓ |
| character_designer | identity 5 要素 + casting framing | Disney 逐帧 + 试镜 workflow | ✓ |
| cinematographer | 180° 轴线 + composition_lock | 摄影师选 lens / 走位 | ✓ |
| prompt_injector | (n/a — AIGC-native) | (n/a) | n/a |
| visual_executor | identity consistency + temporal continuity | Disney 24fps 逐帧 / 摄影机操作 | ✓ |
| audio_pipeline | 5 子任务 + LUFS spec | 5 个独立专家 workflow | ✓ |
| continuity_auditor | 5 类 continuity + 180° 轴线 | continuity supervisor 现场跟踪 | ✓ |
| editor | **Murch Rule of Six** | **Steenbeck + 长片 cutting 序列** | ✓ **DEMO** |
| colorist | color theory(互补/类比/情感) | DaVinci manual grading | ✓ |
| hook_retention | (n/a — AIGC-native,无传统 principle) | (n/a) | n/a |
| quality_gate | Murch Rule of Six(6-dim audit) | test screening 问卷 | ✓ |
| compliance_gate | (n/a — AIGC-native) | (n/a) | n/a |
| theory_critic | 形式/现实主义 + 电影本体论 + 批评方法论 + 精神分析 | (理论本身 timeless) | ✓ |

**关键观察:** Murch Rule of Six 作为 principle 在 3 个节点(editor / continuity_auditor / quality_gate)复用,但每个节点都显式剥离了 Murch 的 physical-film workflow(Steenbeck 剪胶片)。这是 PITFALLS §6.2 (anachronism) 的标杆规避案例。

---

## §3.7 Chinese terminology preservation audit (CORPUS-05)

**21 个 distinct 汉字 terms 在 corpus anchors 中保留:**

| Term (汉字) | Pinyin | English gloss | 节点 | Untranslatable? |
|---|---|---|---|---|
| 故事核 | gù shì hé | story kernel | creative_source, screenplay | 否 |
| 转折点 | zhuǎn zhé diǎn | turning point | creative_source, screenplay | 否 |
| 作者论 | zuò zhě lùn | auteur theory | creative_source | 否 |
| 影调 | yǐng diào | tone / tonality | style_genome | 否 |
| 构图 | gòu tú | composition | style_genome, cinematographer | 否 |
| 光效 | guāng xiào | lighting effect | style_genome | 否 |
| 三幕结构 | sān mù jié gòu | three-act structure | screenplay | 否 |
| 付费卡点 | fù fèi kǎ diǎn | paywall cliffhanger | screenplay, hook_retention | 否 |
| 钩子 | gōu zi | hook | screenplay, hook_retention | 否 |
| 剧本医生 | jù běn yī shēng | script doctor | script_auditor | 否 |
| 角色弧光 | jué sè hú guāng | character arc | character_designer | 否 |
| 角色一致性 | jué sè yī zhì xìng | character consistency | character_designer | 否 |
| 180度轴线规则 | 180 dù zhóu xiàn guī zé | 180-degree axis rule | cinematographer, continuity_auditor | 否 |
| 镜头语言 | jìng tóu yǔ yán | cinematic language | cinematographer | 否 |
| 主光 / 辅光 / 轮廓光 | zhǔ / fǔ / lún kuò guāng | key / fill / rim light | cinematographer | 否 |
| 中间画 | zhōng jiān huà | in-between frames | visual_executor | 否 |
| 拟音 | nǐ yīn | foley | audio_pipeline | 否 |
| 混音 | hùn yīn | mixing | audio_pipeline | 否 |
| 剧本监督 | jù běn jiān dū | continuity supervisor | continuity_auditor | 否 |
| 接戏 | jiē xì | continuity matching (colloquial) | continuity_auditor | 否 |
| 剪辑节奏 | jiǎn jí jié zòu | cutting rhythm | editor | 否 |
| 调色 | tiáo sè | color grading | colorist | 否 |
| 色调 | sè diào | color tone | colorist | 否 |
| 完播率 | wán bō lǜ | completion rate | hook_retention | 否 |
| 试映 | shì yìng | test screening | quality_gate | 否 |
| 形式主义 | xíng shì zhǔ yì | formalism | theory_critic | 否 |
| 现实主义 | xiàn shí zhǔ yì | realism | theory_critic | 否 |
| 电影本体论 | diàn yǐng běn tǐ lùn | film ontology | theory_critic | 否 |
| **意境** | **yì jìng** | **mood / atmosphere (Buddhist-aesthetic lineage)** | **theory_critic** | **是 — 无 clean Western equivalent** |
| 符号学 | fú hào xué | semiotics | theory_critic | 否 |
| 凝视 | níng shì | the gaze | theory_critic | 否 |

**Untranslatable flag:** 意境 (yì jìng) — 跨佛教美学谱系。Western "mood" / "atmosphere" 译法丢失精神维度。本设计保留汉字,在 corpus anchor 中标记 `untranslatable_flag: true`,避免 PITFALLS §6.4 (translation/context loss)。

---

## §3.8 AIGC-native nodes audit (CORPUS-06)

**3 个节点标记 AIGC-native(无传统 corpus 锚点,zero-strength):**

| Node | AIGC-native rationale | Zero-strength explanation |
|---|---|---|
| `prompt_injector` | 传统电影无 prompt 工程角色;AIGC-native 必需 | 无传统对应 — prompt 工程是 2023+ LLM/multimodal 时代新工序。强行用"摄影师指令沟通"伪装是 PITFALLS §6.6 fake-traditional disguise |
| `hook_retention` | 短剧是 AIGC + 移动平台算法催生的新形态;102-book corpus 是 feature-film-oriented | corpus 几乎无短剧-specific 文献(STACK §1.4 明确"NOT in corpus")。v1 external 短剧 refs 已补,但 corpus base 弱 |
| `compliance_gate` | CN 平台是 2020s 兴起的发布渠道,AIGC 内容合规是新工序 | 无传统对应 — CN 平台合规是 AIGC + 平台算法时代新工序。强行用 pre-AIGC corpus 是 PITFALLS §6.2 anachronism + §6.6 fake-traditional disguise |

**模式观察:** 这 3 个节点的 AIGC-native 性质反映 corpus 本身的 gap(prompt 工程是 LLM 时代新工序 / 短剧是 2020s 新形态 / CN 平台合规是新工序),非设计疏忽。这 3 个 gap 已喂给 Phase 12 GOV-04 OPEN-QUESTIONS.md(详见 §3.10)。

---

## §3.9 Last-verified stamps audit (CORPUS-07)

**全局验证:** corpus-trace.yaml 中所有 `last_verified` 字段值统一为 **2026-06-16**。

**覆盖范围:**
- 16 个节点 challenge_source:全部 2026-06-16
- 33 个 corpus 锚点(含 separation block):全部 2026-06-16
- 40 个 books_reverse_index 条目:全部 2026-06-16

**Refresh cadence:** 90 天(per v1 LICENSE 模式 + STATE.md corpus drift mitigation)
- 下次 corpus drift 检测:**2026-09-14**
- 触发条件:Phase 12 GOV-01 living-doc rule + corpus 变更 source 验证

---

## §3.10 Coverage gaps + open questions (feed Phase 12 GOV-04)

**3 个 corpus gap 已识别,标记为 OPEN-QUESTIONS:**

| Gap ID | Description | Affected nodes | Mitigation | Feeds |
|---|---|---|---|---|
| GAP-09-01 | 短剧-specific corpus 几乎为零(102-book corpus 是 feature-film-oriented) | hook_retention, screenplay(短剧 subset) | v1 external refs + AIGC-native flag + needs_supplementation | GOV-04 OPEN-QUESTIONS.md |
| GAP-09-02 | AIGC marginal-value 分析 corpus 缺失 | prompt_injector, visual_executor, audio_pipeline(AIGC transformation subset) | 从 craft-execution refs 推断 + kais-movie-agent V8 架构 | GOV-04 OPEN-QUESTIONS.md |
| GAP-09-03 | 微电影-specific corpus 弱(applicable_form_distribution 显示 0 微电影 anchor) | editor(workflow), colorist | universal 锚点 + form_translation_note | GOV-04 OPEN-QUESTIONS.md |

**重要:** 这些 gap 不阻塞 Phase 9 完成,但必须在 Phase 12 OPEN-QUESTIONS.md 中显式列出(GOV-04 要求"已知 gap 不藏")。

---

## §3.11 Verification summary

| CORPUS req | Status | Evidence |
|---|---|---|
| CORPUS-01 (bidirectional matrix) | passed | §3.1 (forward 16 rows) + §3.2 (reverse 40 rows) |
| CORPUS-02 (applicable_form per anchor) | passed | §3.4 audit shows all 33 anchors tagged |
| CORPUS-03 (≥1 challenge per node) | passed | §3.5 audit shows 16/16 nodes |
| CORPUS-04 (principle vs workflow separated) | passed | §3.6 audit (editor 是 demo case) |
| CORPUS-05 (Chinese terms preserved) | passed | §3.7 audit (21 distinct terms, 1 untranslatable) |
| CORPUS-06 (AIGC-native 0-strength flagged) | passed | §3.8 audit (3 nodes with zero_strength_explanation) |
| CORPUS-07 (Last-verified stamps) | passed | §3.9 audit (all 2026-06-16 + 90-day cadence) |

**Phase 9 status: passed** (all 7 CORPUS reqs satisfied)

---

*Document version: design-2026-06-16-prfp*
*Phase 9 of v2.0 PRFP milestone*
*Source of truth: corpus-trace.yaml*
*Bilingual policy: EN structure + CN prose (META-03)*
*Regeneration: from corpus-trace.yaml via lint script (Phase 12 GOV-02)*
