# 方法论 Gap Analysis:报告 §7.2 蓝图 vs 当前 movie-experts 实际覆盖

> **日期:** 2026-06-17
> **源报告路径:** `.planning/quick/260617-wgz-write-gap-analysis-doc-comparing-creativ/source-research-report.md`
> **审计范围:** `skills/movie-experts/`(v3.0 Skills-to-DAG Alignment milestone 关闭后的实际状态)
> **审计方法:** 对每个被点名的 skill 的 SKILL.md + references/ 实测读取(planner 已在 2026-06-17 验证,executor 信任 verified reconciliation matrix)

---

> **本文档定位:决策依据,非 phase 启动**
>
> 本文档只对照"源调研报告 §7.2 设想的 6 阶段 AI 视频管线蓝图"与"`skills/movie-experts/` 当前实际覆盖了哪些方法论"。
> 本文档**不启动新 phase**,**不创建 PLAN.md**,**不修改任何 skills/ 代码**。Kai 在读完本文档后,
> 可以从文末 §8 列出的三条候选路径中选一条推进,也可以选择不推进。

---

## 1. Executive Summary(一句话结论)

当前 `skills/movie-experts/` 14 个 active + 3 个 deprecated 专家实际已经接入了**比源调研报告设想更广的方法论谱系**:Western 主流的 Snyder 15-beat + McKee scene-design 之外,还补了 Tan 兴趣结构(1996)、McMahon 六情感弧线(2016)、Smith Engaging Characters(1995)、Bourdieu 场域理论、Sarris-Truffaut-Bordwell Auteur Theory、CN 短剧 5 平台爆款公式、Plutchik 八维情绪、attention decay 物理模型等 8 个报告完全未提及的独立方法论。对照报告 §7.2 的 6 阶段蓝图,**实际覆盖率只有 1/6(Snyder-only partial),路径不同 2/6(creative_source 走了 Bourdieu 路径;character_designer 走了视觉身份路径),完全真空 3/6(E-Konte / SCAMPER / meta-process)**。源调研报告反复使用"与麦基方法的异同"(共 9 处)作为对照基准,**这一框架已经过时** —— `screenplay/references/` 实际是 McKee + Snyder 联用,而且 McKee 之上还叠加了 Tan / McMahon / CN 短剧结构。最高 ROI 的三个补缺机会是 **Snowflake Method、E-Konte(絵コンテ)、SCAMPER**(报告全部标注 ⭐⭐⭐⭐⭐ AI 化适合度,且三者各自落点明确、接入难度可控)。本文档不启动新 phase,只提供决策依据。

---

## 2. 当前实际覆盖(实测 skills/movie-experts/ 各 skill 的方法论清单)

以下清单逐 skill 给出**实测引用的方法论 + 出处 ref 文件**(planner 已读取验证,executor 不再重复读 SKILL.md)。

### 2.1 screenplay(编剧专家)

- **Snyder 15-beat Sheet**(`references/save-the-cat-beat-sheet.md`)— 15 节拍按 0-100% 百分比位置给出,并已按短剧 60-180s 时长做了节拍时长缩放。
- **McKee Scene Design**(`references/mckee-scene-design.md`)— value-shift rate ≥ 1/scene,beat 分解 3-5 个 / 90s,turning point vs plot point(~25% / ~75% runtime)。
- **Tan 兴趣结构(1996)**(`references/emotion-curve-academic.md`)— interest = concern × uncertainty × anticipation ≥ 0.6 阈值公式。
- **McMahon 六情感弧线(2016)**(同上)— 85% 故事形态覆盖。
- **CN 短剧结构**(`references/cn-shortdrama-structure.md`)— 抖音/快手/小程序剧的本土化节奏模板。
- **对白工艺**(`references/dialogue-craft.md`)— 维基·金《如何写出好对话》、芦苇、奥班农等中文编剧教材的方法论整合。
- **补充语料**(`_shared/project-corpus/screenwriting-chinese-and-supplementary.md`)— 中文编剧经典 + 补充方法论。

### 2.2 creative_source(创意源专家)

- **Bourdieu 场域理论(L1-L6 六阶层)**(`references/strata-guide.md`)— 6 阶层场域 / habitus / capital 三维模型。
- **Foucault 话语权力 + Lefebvre 空间生产**(同上)— 多阶层共振、不可言说性 10 点协议。
- **Multi-strata Resonance** + **Unspeakability 10-point protocol** — 创意原点不可压缩性测度。

### 2.3 character_designer(角色设计专家)

- **4D-Anchor System** — 人物锚点四维度(身份 / 欲望 / 矛盾 / 创伤)。
- **3-layer STYLE_PREFIX** — 视觉身份三层叠加(prefix / suffix / body)。
- **CLIP-I / DINO-I Stress Test** — 角色跨镜头一致性的客观模型压测。
- **NOT covered:** Truby 四角对立 / Lisa Cron 第三条线索 / Vogler 8 原型 —— 当前路径完全偏向**视觉身份**,缺心理结构维度。

### 2.4 cinematographer(运镜专家)

- **Mascelli 8-level Shot Scale**(`references/`相关 ref)— 8 级景别轴(大远 → 大近)。
- **Arijon 构图规则** — 西方经典画面构图。
- **180°/30° Axis Rules** — 轴线 / 反拍 / 越轴规范。
- **12 Camera Moves** + **Runway/Kling/Veo/Sora Prompt-Token Mapping** — 12 种运镜动作与各主流 AI 视频模型的 prompt token 映射。
- **NOT covered:** E-Konte(絵コンテ)/ Bruce Block 视觉故事 —— 走的是**西方轴线传统**,东方分镜传统完全缺席。

### 2.5 style_genome(风格基因组专家)

- **Sarris 3-criteria Auteur Theory(1962/1968)**(`references/auteur-theory.md`)— 导演 authorship 的 3 标准评分。
- **Truffaut + Bordwell**(同上)— 法国新浪潮 + 认知电影学补全。
- **35 Director 5D DNA Archive** — 35 位导演的 5 维风格基因。
- **12-genre Taxonomy** + **Cross-cultural Hybrid Encoding(0.65/0.35)** — 风格混合的参数化协议(dominant 0.65 / recessive 0.35,固定权重)。

### 2.6 hook_retention(Hook 与留存专家)

- **5-type Hook Taxonomy** — 5 种 Hook 类型。
- **3-tier 卡点 Strength** — 强 / 中 / 弱卡点。
- **Per-platform 5-branch 爆款公式**(`SKILL.md`)— 抖音-男频 / 抖音-女频 / 快手-草根 / 小程序剧-长集数 / 通用 fallback 共 5 个分支。

### 2.7 script_auditor(剧本审计专家)

- **Dimension 1:** Snyder + McKee(结构与节拍审计)。
- **Dimension 2:** Plutchik 八维情绪(`references/emotion-arc-audit.md`)— 8 个情绪维度的弧线审计。
- **Dimension 3:** 3 秒 Hook 10 点(`references/completion-rate-forecast.md`)— 开篇 3 秒留人的 10 项硬指标。
- **Dimension 4:** 角色网络(关系图与冲突网审计)。
- **Dimension 5:** 疲劳曲线物理模型(同上)— `attention(t) = base × e^(-decay × t) × conflict_gain(t)`。
- **5 维总分 100** —— 评估**单剧本**,不生成变体。

### 2.8 storyboard_designer(分镜设计专家)— **DEPRECATED**

- **Phase 17 v3.0(2026-06-17)deprecate**:`status: deprecated`,folded into `cinematographer.composition_lock` sub-task。
- 原始版本使用 shot-decomposition rules + camera params + 4D anchoring,**不是 E-Konte**。
- Deprecation 后 E-Konte 缺口变得**更加突出** —— 唯一可能承载东方分镜传统的容器已经被合并到西方轴线专家的子任务里。

---

## 3. 报告蓝图 §7.2 六阶段对照矩阵

下表的 6 行均经过 planner 在 2026-06-17 实测读取对应 SKILL.md 验证。覆盖度符号:`✅` 已覆盖 / `⚠️` 部分覆盖 / `❌` 真空或路径不同。

| # | 报告 §7.2 阶段 | 报告点名的核心方法论 | 当前实现(实测) | 覆盖度 | 缺口描述 |
|---|---|---|---|---|---|
| 1 | **创意种子** | Story Spine + CPS | `creative_source` 用 **Bourdieu 6 strata(L1-L6)+ Foucault + Lefebvre** | ❌ | 路径不同 —— 当前路径比报告设想的"Story Spine 一句话种子"更深、更强,但**不是报告设想的那条路径**。Story Spine 完全未引入。 |
| 2 | **故事大纲** | Snowflake Method + Snyder 15-beat + Vogler 12 阶段 | `screenplay` 用 **Snyder 15-beat + McKee scene-design** | ⚠️ | 1/3 覆盖(Snyder only)。Snowflake 与 Vogler 均未引入;McKee 是当前路径的额外补强(报告未提)。 |
| 3 | **角色深度** | Truby 四角对立 + Lisa Cron 第三条线索 + Vogler 8 原型 | `character_designer` 用 **4D-Anchor + 3-layer STYLE_PREFIX + CLIP-I/DINO-I stress test** | ❌ | 路径完全不同 —— 当前是**视觉身份路径**,缺心理结构 / 道德论证 / 原型维度。 |
| 4 | **分镜设计** | E-Konte(絵コンテ)+ Bruce Block | `cinematographer` 用 **Mascelli 8-level + Arijon + 180°/30° axis + 12 camera moves + Runway/Kling/Veo/Sora prompt token**;`storyboard_designer` 已 deprecate | ❌ | **E-Konte 真空**。西方轴线传统完全替代了东方分镜传统;storyboard_designer deprecate 后更无容器。Bruce Block 视觉对比三要素也缺席。 |
| 5 | **创意变换** | SCAMPER + 六顶思考帽 + 横向思维 | `style_genome.style_blend_protocol` 是**手工 0.7/0.3 dominant-recessive 权重混合**;`script_auditor` 是 **5 维打分** | ❌ | **SCAMPER 真空**。当前混合协议只产出**一个**融合结果,不是 7 变体引擎;script_auditor 只评**一个**剧本,不是变体生成器。 |
| 6 | **迭代优化** | 设计思维五阶段 / 双钻模型 + Story Grid | 没有显式 meta-process;`script_auditor ↔ screenplay` 迭代环存在但**非正式** | ❌ | **Meta-process 真空**。Story Grid 五戒律也未引入(script_auditor 走的是 Snyder + McKee + Plutchik + 疲劳曲线,不是 Coyne 的 5-commandments)。 |

**汇总:** 6 阶段中,`⚠️` Partial 1/6(阶段 2 Snyder-only),`❌` Path-divergent 2/6(阶段 1 Bourdieu 路径 / 阶段 3 视觉身份路径),`❌` Vacuum 3/6(阶段 4 E-Konte / 阶段 5 SCAMPER / 阶段 6 meta-process)。**严格意义上的"已覆盖"= 0/6**(阶段 2 也只覆盖 1/3)。

---

## 4. 关键事实校正(McKee-as-baseline framing 已过时)

源调研报告 §7.2 + 全文 9 处出现的 **"与麦基方法的异同"** 字样,**反复把 McKee 当作隐含的方法论基准**(baseline)。这一框架在 2026-06-17 已经不再成立。当前 `skills/movie-experts/screenplay/references/` 实际上是:

```
screenplay/references/
├── mckee-scene-design.md          # McKee《Story》核心: value-shift + beat + turning point
├── save-the-cat-beat-sheet.md     # Snyder 15-beat with % positions (adapted to 短剧 60-180s)
├── emotion-curve-academic.md      # Tan (1996) + McMahon 6 arcs (2016)
├── cn-shortdrama-structure.md     # CN 短剧本土节奏
├── dialogue-craft.md              # 维基·金 / 芦苇 / 奥班农
└── _shared/project-corpus/        # 补充中文与西方编剧经典
```

**两个直接结论:**

1. **未来规划不得假设"还需要从零引入 McKee"** —— 这项工作已经在 v1 milestone 完成。任何 PLAN.md 若仍然把 McKee 列为"待引入缺口",就是基于过时的事实状态做出的规划。
2. **真正的缺口,是报告 LISTS 但当前 NOT YET IN 的那些方法论** —— Snowflake / E-Konte / SCAMPER / Vogler / Truby / Story Grid / 设计思维五阶段 / 起承转合(Kishōtenketsu)等等。这些才是 §5、§6 罗列的补缺候选。

**附带校正:** 报告反复对照的"麦基 vs X 异同"分析框架,对**未来规划已经失去指导意义** —— McKee 不是规划基线,它是已经沉淀进 screenplay 的既有资产。规划基线应该是 §3 的 6 阶段矩阵(覆盖度实测)。

---

## 5. 高 ROI 缺口排序(3 个最高优先级)

按"AI 化适合度星级 × 缺口真空程度 × 接入难度倒数"三因素排序,以下三个缺口是 ROI 最高的补缺候选。每个缺口给出 4 字段:**报告位置 / 当前真空原因 / 接入难度估算 / 对应现有 skill 接入点**。

### 5.1 Gap 1 — Snowflake Method(雪花法)

- **报告位置:** §2.1,AI 化适合度 ⭐⭐⭐⭐⭐(报告原文:"**天然的 AI 生成管线**!每一步都是上一步的扩展,完美匹配 LLM 的递进生成能力。可以直接设计为多步 prompt 链")。
- **当前为何真空(verified):** `creative_source` 当前输出的是 `StoryKernel`(one-line `structural_formula` + `strata_layers[]`)。`screenplay` 拿到 StoryKernel 之后**直接跳到** Snyder 15-beat sheet。**中间没有"kernel → 一段话 → 角色概要 → 一页大纲 → 四页大纲 → 场景列表"的递进扩展**。整条 pipeline 把 kernel → beat_sheet **坍缩成一跳**。
- **接入难度估算:LOW。** Snowflake 是一个**纯流程方法**(prompt chain),不需要新 skill、不需要新 schema、不需要新数据。可以两种方式落地:(a) 作为 `screenplay` 内部新增的 sub-step(在 StoryKernel → 15-beat 之间插入 Snowflake expansion);(b) 作为独立的新 skill `snowflake_expander/`,放在 DAG 中 `creative_source` 与 `screenplay` 之间。
- **对应接入点:** `screenplay/references/snowflake-expansion.md`(新文件)—— OR 新 skill `snowflake_expander/`(介于 creative_source 与 screenplay 之间)。

#### 5.1.1 Snowflake 10 步扩展细节(对接入设计有用)

Ingermanson 原始的 Snowflake Method 是 10 步递进,每一步都是上一步的"扇出"扩展:

1. **一句话总结**(≤25 words)— 当前 `creative_source.StoryKernel.structural_formula` 已经做了这一步。
2. **一段话扩展** — 将一句话扩展为包含开头、三幕灾难、结尾的段落(5 句话结构)。
3. **角色概要** — 每个主要角色一页:姓名、故事线、动机、目标、冲突、顿悟、一句话总结。
4. **一页大纲** — 将一段话扩展为每句一页(对应三幕灾难 + 转折)。
5. **角色大纲** — 每个角色一页人物传记。
6. **四页大纲** — 进一步扩展细节。
7. **完整角色表** — 详尽角色档案。
8. **场景列表** — 电子表格列出所有场景。
9. **场景描述** — 多段叙述每个场景。
10. **写初稿** — 开始正式写作。

**当前 pipeline 只做了 step 1(creative_source)和 step 10(screenplay 跳到 beat_sheet),step 2-9 全部缺失。** 如果引入 Snowflake,step 2-9 可以作为 creative_source → screenplay 之间的中间 artifacts(每一步都是上一步的可机器验证扩展,天然适合 LLM 链式生成)。

#### 5.1.2 与现有 Snyder 15-beat 的协同关系

Snowflake 不是替代 Snyder,而是**上游的递进展开器**。Snyder 15-beat 是**结构模板**(告诉你 beat_sheet 长什么样),Snowflake 是**流程方法论**(告诉你如何从一句话扩展到 beat_sheet)。引入 Snowflake 之后,DAG 应该是:

```
creative_source (Bourdieu) → StoryKernel (一句话)
   ↓
snowflake_expander (Snowflake step 2-7)
   ↓
scene_list (Snowflake step 8)
   ↓
screenplay (Snyder 15-beat + McKee scene-design,基于 scene_list 填充 beat_sheet)
```

### 5.2 Gap 2 — E-Konte(絵コンテ)

- **报告位置:** §4.1,AI 化适合度 ⭐⭐⭐⭐⭐(报告原文:"**这是 AI 视频管线的直接蓝图!** E-Konte 的结构天然可以转化为 AI 生成的中间格式")。
- **当前为何真空(verified):** `cinematographer` 用的是**西方轴线传统**(180° rule / 30° rule / Mascelli shot scale)。原本可以承载 E-Konte 的 `storyboard_designer` 在 **Phase 17 v3.0(2026-06-17)被 deprecate**,folded into `cinematographer.composition_lock` 子任务。**deprecate 之前的 storyboard_designer 也没有用 E-Konte** —— 它用的是 shot-decomposition rules + camera params + 4D anchoring。所以 E-Konte 在当前 skills 里**完全缺席**,没有现成容器。
- **接入难度估算:MEDIUM。** E-Konte 是一种**格式规范 / 中间表示**(每个镜头要标 time/frame、layout、composition、angle、movement、action、dialogue、sfx 等字段),需要:(a) 新增一份 ref 文件说明 E-Konte 格式;(b) 决策:扩展 `cinematographer.composition_lock` 子任务输出 E-Konte 风格的中间格式,还是引入"今敏风格的可出版分镜"作为独立 artifact 类型。
- **对应接入点:** `cinematographer/references/e-konte-format.md`(新文件)+ 扩展 `composition_lock` 子任务的 output schema,或者新增 `e_konte_storyboard.json` 作为 `cinematographer` 的附加 output artifact。

#### 5.2.1 E-Konte 字段集(对接入设计有用)

日本动画工业的 E-Konte(絵コンテ)每个镜头至少包含以下字段:

| 字段 | 含义 | 当前 cinematographer 是否覆盖 |
|---|---|---|
| `shot_id` | 镜头编号 | ✅ |
| `time_in` / `time_out` / `frames` | 时间码与帧数 | ❌ 当前只有粗粒度时长 |
| `panel_layout` | 分格画面布局(单格 / 双格 / 四格) | ❌ 完全真空 |
| `composition` | 构图(画面元素位置) | ⚠️ 部分覆盖(Arijon) |
| `camera_angle` | 镜头角度(平视 / 仰视 / 俯视) | ✅ Mascelli 8-level |
| `camera_movement` | 运镜(推拉摇移跟) | ✅ 12 camera moves |
| `character_pose` / `expression` / `action` | 角色姿态 / 表情 / 动作 | ❌ 当前无 character blocking |
| `dialogue` | 对白文本 | ❌ 当前无 dialogue 字段 |
| `sfx_annotation` | 音效标注 | ❌ 当前无音效字段 |
| `bg_layer` | 背景层 | ❌ |
| `camera_lens` / `focal_length` | 焦距与镜头规格 | ❌ 今敏风格的精细镜头规格完全缺席 |

**结论:** E-Konte 至少需要新增 6-8 个字段,扩展 cinematographer.composition_lock 的 output schema 是工作量主体。

#### 5.2.2 今敏(Satoshi Kon)风格的额外约束

报告 §4.1 特别提到今敏的极致方法 —— 分镜精确到可以当作漫画出版,每帧标注摄影机运动 / 焦距 / 特效,《红辣椒》分镜耗时一年半。这种"可出版级"分镜不是普通 E-Konte,而是**今敏风格的 hyper-detailed storyboard**。接入决策需要明确:目标是普通 E-Konte 还是今敏级?两者工作量差 5-10 倍。

### 5.3 Gap 3 — SCAMPER(7 动词创意变换)

- **报告位置:** §6.1,AI 化适合度 ⭐⭐⭐⭐⭐(报告原文:"每个动词都可以直接作为 AI prompt 的变换维度,用于故事变体生成")。
- **当前为何真空(verified):** `style_genome.style_blend_protocol` 是**参数化的 0.7/0.3 dominant-recessive 权重混合协议** —— 它**只产出一个融合结果**,不是 7 变体引擎。`script_auditor` 是**评分器**(评估单剧本),不是变体生成器。**当前没有任何 skill 做"如果 Substitute / Combine / Adapt / Modify / Put-to-other-use / Eliminate / Reverse 故事,会怎样"的变体生成。**
- **接入难度估算:LOW-MEDIUM。** SCAMPER 本质是 7 条 prompt 模板。可以两种方式落地:(a) 作为 `screenplay` 的**自迭代工具**(初稿生成后用 SCAMPER 7 动词生成 7 个变体,再选最优);(b) 作为 `creative_source` 的新 sub-step(在 StoryKernel 提交前先产出 7 个 kernel 变体,再 commit 最优)。需要先决策:**SCAMPER 跑在 screenplay 之前(kernel 变体)还是之后(剧本变体)?**
- **对应接入点:** `creative_source/references/scamper-variants.md`(kernel 阶段变体)—— OR `screenplay/references/scamper-iteration.md`(剧本阶段变体)—— OR 新 skill `variant_generator/`。

#### 5.3.1 SCAMPER 7 动词映射到短剧创作语境

| 动词 | 短剧场景下的变换问句 | 当前是否有近似实现 |
|---|---|---|
| **S**ubstitute(替代) | "如果主角从男频换成女频会怎样?" | ❌ 当前 hook_retention 只选分支,不变体 |
| **C**ombine(组合) | "把悬疑 + 治愈组合在一起?" | ⚠️ style_genome 0.7/0.3 部分覆盖(但只产出 1 个结果) |
| **A**dapt(适配) | "把电影叙事节奏适配到 60s 短剧?" | ✅ screenplay 已做(CN 短剧结构适配) |
| **M**odify(修改) | "把结局从悲剧改成喜剧?" | ❌ |
| **P**ut to other use(另作他用) | "这个 IP 可以改成小游戏吗?" | ❌ |
| **E**liminate(消除) | "去掉所有对白,纯视觉叙事?" | ❌ |
| **R**everse / Rearrange(反转 / 重排) | "从反派视角重讲?" | ❌ |

**7/7 中只有 1 个被近似覆盖**(Adapt)。SCAMPER 引入后能补 5-6 个变换维度。

#### 5.3.2 SCAMPER vs style_genome.style_blend_protocol 的边界

style_blend_protocol 是**风格混合**(genre A × genre B → 混合风格),SCAMPER 是**结构变体**(story X → 7 个变体故事)。两者维度不同 —— style_blend 在**风格基因组层**操作,SCAMPER 在**叙事结构层**操作。引入 SCAMPER 不会与 style_blend 冲突,反而构成**风格层 × 结构层**的二维变体空间。

---

## 6. 次优先级缺口(简表)

下表列出报告提及、但 ROI 低于 §5 三个缺口的剩余方法论。每行给出报告位置、AI 化适合度、当前状态、一句话说明。

| 方法论 | 报告位置 | AI 化适合度 | 当前状态 | 一句话说明 |
|---|---|---|---|---|
| **Vogler 12 阶段 + 8 原型** | §1.4 | ⭐⭐⭐⭐⭐ | **Vacuum** | 神话学英雄之旅 + 8 角色原型,天然分类系统,适合角色与情节生成;当前完全未引入。 |
| **Truby 22 步 + 四角对立** | §1.3 | ⭐⭐⭐⭐ | **Vacuum** | 反三幕的有机生长系统;前置深度角色弧线生成;当前 character_designer 路径完全不同。 |
| **设计思维五阶段(Stanford d.school)** | §5.1 | ⭐⭐⭐⭐⭐ | **Vacuum** | Empathize / Define / Ideate / Prototype / Test 元流程;当前无显式 meta-process。 |
| **Story Grid(Coyne 2015)** | §2.2 | ⭐⭐⭐⭐ | **Partial** | script_auditor 走的是 Snyder + McKee + Plutchik + 疲劳曲线,**不是** Coyne 的 5-commandments(Inciting Incident / Progressive Complications / Crisis / Climax / Resolution);相邻但不重合。 |
| **起承转合(Kishōtenketsu)** | §3.3 | ⭐⭐⭐⭐ | **Vacuum(CN 文化相关性)** | 非 conflict-driven 的 contrast-driven 四幕结构;适合**治愈向 / 氛围型** AI 短视频(吉卜力风格);CN/JP 文化语境下不可忽视。 |
| **六顶思考帽(de Bono)** | §6.3 | ⭐⭐⭐⭐ | **Vacuum** | 6 维度评审;适合作为故事评审环节(script_auditor 当前是 5 维打分,可扩展)。 |
| **横向思维(de Bono)** | §6.4 | ⭐⭐⭐⭐ | **Vacuum** | 随机输入触发新联想;可被 AI 以 embedding 语义相似性实现。 |
| **CPS(Osborn-Parnes)** | §6.5 | ⭐⭐⭐⭐ | **Vacuum** | Clarify / Ideate / Develop / Implement 四阶段;与设计思维同源;当前无显式接入。 |
| **Story Spine** | §1.5 | ⭐⭐⭐⭐⭐ | **Vacuum** | "Once upon a time… Every day… But one day…" 7 行极简模板;适合作为 AI 故事生成的种子/起始点。 |
| **模块化叙事(Telltale/Bioware)** | §3.2 | ⭐⭐⭐⭐⭐ | **Vacuum** | 模块自包含 + 弱耦合 + state flag;适合系列化 / 多分支 AI 内容生成。 |

**优先级备注:** Story Spine 虽然是 ⭐⭐⭐⭐⭐,但 `creative_source` 已经走了**更深**的 Bourdieu 路径,Story Spine 的 ROI 实际**低于** Snowflake(因为 Snowflake 能填补 kernel → 15-beat 之间的明确空白,而 Story Spine 与现有 Bourdieu 路径功能部分重叠)。起承转合由于 CN 文化相关性,**优先级应高于**六顶思考帽 / 横向思维等通用创意方法。

---

## 7. 独创方法论清单(当前 skills 引入但报告未覆盖)

当前 `skills/movie-experts/` 已经引入了 **8 个源调研报告完全没有提及的独立方法论**。这些是 v1-v3 milestone 期间沉淀的独创资产,在评估"还需要补什么"时**不应被当作待引入项** —— 它们已经是 in-place 的覆盖。每个方法论给出一句话说明它**额外覆盖了哪个维度**。

- **Tan 兴趣结构(1996)** — `screenplay/references/emotion-curve-academic.md` —— 给出了 interest = concern × uncertainty × anticipation ≥ 0.6 的**量化阈值公式**,报告的 Snyder / McKee / Vogler 都没有这种量化判据。
- **McMahon 六情感弧线(2016)** — 同上 —— 用 6 种基本弧线覆盖 85% 故事形态,提供了**比三幕更细粒度**的情感形态分类。
- **Smith Engaging Characters(1995)** — 经由 emotion-curve ref 间接引用 —— 引入"角色 engaging 维度"的概念,补全 character engagement 这一观众心理学维度。
- **Bourdieu 场域理论(L1-L6 六阶层)** — `creative_source/references/strata-guide.md` —— **取代了 Story Spine 的位置**,提供"创意源点 6 阶层 + 场域/habitus/capital"的三维框架,远比一句话种子更深。
- **Sarris-Truffaut-Bordwell Auteur Theory(1962/1968)** — `style_genome/references/auteur-theory.md` —— Sarris 3 标准评分 + Truffaut 作者论 + Bordwell 认知电影学,**为导演风格基因库提供了学术合法性**,报告完全没有这一支线。
- **短剧爆款公式 5 平台分支** — `hook_retention/SKILL.md` —— 抖音-男频 / 抖音-女频 / 快手-草根 / 小程序剧-长集数 / 通用 fallback 共 5 个分支,**CN 平台实战经验**的报告完全没有覆盖。
- **Plutchik 八维情绪** — `script_auditor/references/emotion-arc-audit.md` —— 8 维度情绪轮(joy / trust / fear / surprise / sadness / disgust / anger / anticipation)用于 Dimension 2 审计,比报告的"情感弧线"更细粒度。
- **疲劳曲线物理模型** — `script_auditor/references/completion-rate-forecast.md` —— `attention(t) = base × e^(-decay × t) × conflict_gain(t)`,**把观众注意力衰减建模成物理方程**,这是报告完全没有触及的量化维度。

---

## 8. 不动作决策(non-action decision)

**本文档不启动新 phase,不创建 PLAN.md,不修改任何 `skills/` 代码。** 本文档只是决策依据,把"报告设想的蓝图 vs 当前实际覆盖"的事实状态摆清楚,让 Kai 在事实基础上选择下一步路径,而不是在报告的"麦基基准"框架下决策。

后续路径(由 Kai 决定,不是由本文档预设):

- **选项 A — 写 spec 后走 `/gsd:plan-phase`:** 如果 Kai 已经决定要补 Snowflake / E-Konte / SCAMPER 中的一个或多个,可以先写一份 spec(目标 + 验收标准 + 影响范围),然后 `/gsd:plan-phase` 启动正式 phase 规划。
- **选项 B — 进入 `/gsd:explore` 做更深的选型调研:** 如果 Kai 还不确定三者中哪个先做,或者想再考察 Vogler / Truby / Story Grid 等次优先级方法论,可以进入 explore 阶段做更深的技术选型调研。
- **选项 C — 直接重构 `creative_source` 把 Snowflake 折叠进 StoryKernel → Screenplay 中间步骤:** Snowflake 接入难度是 LOW,如果 Kai 想快速验证价值,可以直接以重构方式做掉(走 `/gsd-quick`),不必启动完整 phase。

**后续路径的入口文档:** `.planning/research/v2-pipeline-design/` 已有的 pipeline design 文档(包括 nodes.yaml、io-contract 等)是后续任何选项的事实底座,任何规划都应该基于这份文档的 DAG 拓扑做增量。

**当前不动作的依据:** (1) v3.0 Skills-to-DAG Alignment milestone 在 2026-06-17 关闭,21 个 canonical expert_ids 全部签收、12/12 requirements Complete;(2) 本 gap analysis 揭示的缺口(E-Konte / SCAMPER / Snowflake)在 v3.0 milestone 范围内**不属于 deferred item** —— 它们是**新发现的候选方向**,不在 v3.0 任何 ROADMAP §13-18 success criteria 范围内;(3) 因此本文档不构成对 v3.0 milestone 完成度的任何否定,只是为 v4+ 候选方向提供事实依据。

---

*文档结束。本文档为 quick task `260617-wgz` 的产物,写入路径 `.planning/research/methodology-gap-analysis-2026-06-17.md`,不修改任何 `skills/movie-experts/` 代码。*
