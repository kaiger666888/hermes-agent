# 00 — 第一性原理推导：kais-movie-agent v2.0 Pipeline 节点集

> **Document status:** design-2026-06-16-prfp · supersedes: none · superseded_by: TBD
> **Phase:** 7 of v2.0 PRFP milestone · **Authors:** hermes-agent design team
> **Audience:** kais-movie-agent impl team + hermes-agent skills team + future design maintainers
> **Reading time:** ~30 minutes (full doc) / ~10 minutes (§0 + §4 candidate node set)
> **Stability:** §1+§2 stable; §3+§4 evolving; §7 experimental

---

## §0 — 阅读指南

本文档是 **kais-movie-agent v2.0 工作流节点集的第一性原理推导记录**，是 v2.0 PRFP (Pipeline Redesign from First Principles) 里程碑 Phase 7 的唯一交付件。它从四个不可还原的根本问题出发,逐步推导出一组候选节点,每节点都明确**为什么是它而不是别的**。

### 章节地图

| 章节 | 内容 | 阅读优先级 (按角色) |
|---|---|---|
| §0 | 阅读指南(本节) | 所有人先读 |
| §1 | 方法论框架(Musk / Aristotle / 认识论标签 / Steelman) | 维护者必读 |
| §2 | 四个第一性问题 + 每问题的语料子集预映射 | hermes skills 团队必读 |
| §3 | 推导链(从 Q1-Q4 走到中间结论) | 维护者必读;kais impl 团队可略读 |
| §4 | 候选节点集(每节点 8 字段) | kais impl 团队必读 |
| §5 | 节点数量审计 | 维护者必读 |
| §6 | Musk 方法审计清单(10 个 failure mode) | 审阅者必读 |
| §7 | 未解问题(喂给 Phase 12 OPEN-QUESTIONS.md) | 后续研究 phase 必读 |
| References | 全部引用源 | 任何被引文出处挑战时查 |

### 稳定性标记

| 章节 | 稳定性 | 修改门槛 |
|---|---|---|
| §1, §2 | `stable` | 修改需开新的设计-修订里程碑 |
| §3, §4 | `evolving` | 可在 v2.0 PRFP 内迭代;每次修改记录 CHANGELOG |
| §5, §6 | `stable` (与 §3+§4 同步) | 跟随 §3+§4 |
| §7 | `experimental` | 自由编辑(就是为后续研究准备的) |

### 受众指引

- **kais-movie-agent 实施团队**:先读 §0 + §4 + §6。如果对某个节点的存在有疑问,跳回 §3 看推导链。Phase 11 handoff 会给你 1-2 页的 impl-cheatsheet。
- **hermes-agent skills 团队**:先读 §0 + §2 + §4。你关心的是哪些现有 expert 映射到哪些新节点 — 看 §4 每节点的 `v1 expert_id mapping`。
- **未来设计维护者**:全读。本文档的设计-修订需通过 §6 审计清单的全部 10 个 failure mode。

---

## §1 — 方法论框架

> 本节声明本文档使用的全部方法论工具,以及它们的纪律性约束。任何后续章节(§2-§7)的论证必须在本节框架内进行 — 越界即视为第一性原理伪装(PITFALLS §1.1)。

### §1.1 — Musk 式第一性原理 (Musk first principles)

**定义:** 把问题还原到最基础的真理("什么是我们确知为真的?"),再向上推导 — 显式拒绝类比推理("一直以来都是这么做的")。

**主源:**

1. **Kevin Rose Foundation 采访 (2012)** — 最早、最规范的第一性原理表述。Musk 原话:
   > *"I tend to approach things from a physics framework. Physics teaches you to reason from first principles rather than by analogy."*
   > (我倾向于用物理学的框架来思考问题。物理学教你从第一性原理而非类比来推理。)
   >
   > — Musk to Kevin Rose, Foundation Series #3, 2012
   > 来源: <https://www.kevinrose.com/p/elon-musk-interview-kevin-reboots-the-old-foundation-series>

   著名的电池成本案例:Musk 没有接受"$600/kWh 市场价",而是把电池拆解到原材料(钴、镍、铝、碳),计算原材料成本(~$80/kWh),由此推出差距来自制造工艺而非物理极限 → 建 Gigafactory 把差距填上。

2. **Walter Isaacson 传记《Elon Musk》(2023)** — 把第一性原理描述为 Musk 的标志性"超能力"。SpaceX 案例:Musk 把火箭成本拆解到原材料(铝、钛、铜、碳纤维),发现原材料只占火箭售价的 ~2%,由此推出成本驱动是制造低效而非物理极限。Tesla 案例:"人类只用视觉输入就能驾驶,所以摄像头应该够用" → 第一性原理拒绝 LiDAR 依赖。

   **引用规范:** 因 Simon & Schuster 不同版次页码不同,本文档按章节上下文引用(不引用具体页码)。任何 Musk 转述均标记 `[转述; 主源: Kevin Rose 2012 / Isaacson 2023 ch. N]`。**不伪造引文** — 只引用 STACK §4.1 已引述的 Musk 原话。

3. **Musk YouTube 自述** — *"The First Principles Method Explained by Elon Musk"* 视频中 Musk 自己解释:第一性原理是为了实现 leap innovation(跨越式创新)而非 incremental improvement(渐进式改进)。

   来源: <https://www.youtube.com/watch?v=NV3sBlRgzTI>

### §1.2 — Aristotle 的根(哲学根源)

Musk 的"第一性原理 vs 类比"区分并非 2012 年原创 — 它的哲学根在 Aristotle *Physics* Book I, ch. 1 (Hardie & Gaye translation, Bekker 184a16-22):

> *"The natural way of doing this is to start from the things which are more knowable and obvious to us and proceed towards those which are clearer and more knowable by nature; for it is not the same thing to be knowable to us and knowable without qualification."*
> (自然的做法是从对我们来说更可知、更明显的事物出发,推进到那些就其本性而言更清晰、更可知的事物;因为"对我们可知"与"绝对可知"不是一回事。)
>
> — Aristotle, *Physics* I.1, 184a16-22 (Hardie & Gaye translation)
> 来源: <http://www.logoslibrary.org/aristotle/physics/11.html>

**关键区分:** Aristotle 区分两类可知性:
- **"对我们可知"(more knowable to us)** — 类比、经验、熟悉的事物。易得,但可能掩盖真相。
- **"按本性可知"(more knowable by nature)** — 基础真理,从它们出发可推出其他一切。

这正是 Musk "第一性原理 vs 类比"区分的 2400 年前的哲学源头。本文档在引用 Musk 方法时同时引用 Aristotle,以表明该方法的严肃性和传统厚度(不是某个 2012 podcast 的随口一说)。

**Aristotle 四因说(material/formal/efficient/final causes)的相关性:** 有限相关。本文档主要用 Aristotle 的"可知性区分";四因说更多用于分析单个节点的"为什么存在",而非整个推导链的方法论。在 §3 推导中遇到"这个节点的最终因(final cause)是什么"时,会借用四因说语言。

### §1.3 — 认识论状态标签(Epistemic-status taxonomy)

本文档对每个核心论断打 **4 类认识论状态标签** 之一,以区分稳定真理 vs 易变假设(防 PITFALLS §1.5 — "我推导自物理"谬误):

| 标签 | 波动性 | 示例 |
|---|---|---|
| `physical` | 跨世纪稳定 | 180° 轴线规则(观众空间定向是感知不变量)、光线方向、感知生理 |
| `psychological` | 跨十年稳定 | 注意力衰减、情感反应、叙事闭合感、人类对节奏的生理响应 |
| `platform-algorithmic` | 季度-年级波动 | 抖音完播率加权、快手 hot-tub 惩罚、视频号分发上限、平台审核阈值 |
| `tool-capability` | 月-季度波动 | 当前 LoRA 身份锁能力、当前 TTS 自然度上限、当前视频生成模型(月度迭代) |

**声明:** 本 4 类标签是 **本项目自定义**(per RESEARCH §5:没有任何标准认识论框架能干净映射到这 4 类)。该自定义是可辩护的,因为它直接对应 AIGC 设计需要追踪的波动性阶梯 — 这正是 Musk 方法区分 `validated-invariant` vs `contingent` 时需要的工具(见 §1.4)。

**最相关的替代框架(已评估并拒绝):**
- Bayesian 认识论(prior/posterior/likelihood)— 不面向波动性,而是面向概率更新
- 对话分析中的 epistemic status vs stance (Heritage & Raymond)— 用于对话回合而非设计文档
- 物理确定度(philosophy.institute "physical certitude")— 只覆盖一维,不是 4 类标签

未来里程碑(Phase 12 之后)可以把本 4 类标签与正式认识论框架对照研究 — 暂记入 §7 open questions。

### §1.4 — Contingent vs Validated-in-Invariant 分类

per PITFALLS §5.3:每个节点的核心假设必须分类为:

- **`contingent`(偶然)** — 某人某时做的选择,可以合理质疑。例如:"storyboard 作为独立产物持久化"(工作流选择)、"线性 DAG 拓扑"(继承假设)、"20 步粒度"(粒度选择)。
- **`validated-invariant`(经验验证的不变量)** — 跨大量实证观察成立的规律,质疑它需要 extraordinary evidence。例如:"180° 轴线规则"(感知不变量)、"Murch Rule of Six 的六维度"(剪辑经验规律)、"人类对前 3 秒低信任内容的快速脱离"(注意力实证)。

**关键纪律(per PITFALLS §5.3 + §1.2):** 第一性原理 ≠ "把所有假设都质疑一遍"。Musk 在 Twitter 收购时质疑的是 headcount(偶然选择),不是重力或铝的抗拉强度。本推导 **不会** 在第一性原理的名义下丢弃 `validated-invariant` — 这是 PITFALLS §1.2("把验证过的工艺当 bias 扔掉")和 §5.3("Twitter/X 故事的误用")的双重防御。

**与 §1.3 认识论标签的映射规则:**
- `physical` + `psychological` 标签 → **通常** 是 `validated-invariant`
- `platform-algorithmic` + `tool-capability` 标签 → **通常** 是 `contingent`

**但映射不 1:1:** 一个 `psychological` 论断如果只对特定受众群体成立(例如"Z 世代对竖屏内容的注意力窗口"),可以是 `contingent`。两个分类服务不同的审计目的:
- 认识论标签 = **波动性**(这条假设多久会过时?)
- 假设分类 = **可改性**(在第一性原理审查下,这条假设能被推翻吗?)

### §1.5 — Steelman-the-Elimination 纪律

per RESEARCH §3 + PITFALLS §1.6:对每个候选节点,推导必须包含一段 **steelman-the-elimination**(钢人反驳-消去):

1. **钢人反驳(strongest counter-argument):** 陈述最强的"这个节点不该存在"论点 — 必须是 **实质的反驳**,不是 strawman。一个 strawman 钢人比没有钢人更糟,因为它制造了严谨的假象。
2. **我方回应(response):** 解释为什么节点仍然存活 — 必须直接回应钢人,不是转移话题。
3. **判定(verdict):** SURVIVES / RECONSIDER / MERGE。

**根源:**
- **Principle of Charity(宽厚原则)** — Neil L. Wilson 1958-59 命名。要求以最合理的方式解读对方陈述。来源: <https://en.wikipedia.org/wiki/Principle_of_charity>
- **Paul Graham "How to Disagree"(2008)** — 提出分歧等级 7 级,最高级"Refuting the Central Point"要求先做 steelman。Graham:"Refutation is the rarest form of disagreement because it's the most work." 来源: <https://www.paulgraham.com/disagree.html>

**Phase 7 应用:** 在 §4 每个候选节点的条目里都包含 steelman 段落。这是防 PITFALLS §1.6(reverse-engineering desired answers into first principles)的结构机制 — 如果推导者心里已经有一个偏好的节点集,steelman 会把这种 bias 暴露出来(因为偏好集很难为每个节点都给出实质的钢人反驳)。

### §1.6 — Alternatives-Considered 日志格式(MADR-style)

per RESEARCH §4 + DERIV-05:每节点的 alternatives-considered 日志采用 **MADR(Markdown Architectural Decision Records)** 的 "Considered Options" 结构。

**为什么 MADR 而非 Nygard ADR:**
- **Nygard ADR(Michael Nygard 2011)** — 基础格式:Title, Context, Decision, Status, Consequences。alternatives 是隐式的(写在 narrative 里)。
- **MADR(Olaf Zimmermann et al.)** — Nygard 的超集;每个 Nygard ADR 都是有效的 MADR。MADR 增加了 **显式的 Considered Options 字段**(每个 option 有 pros/cons)。

来源:
- MADR 官方仓库: <https://adr.github.io/madr/>
- MADR 模板解读: <https://ozimmer.ch/practices/2022/11/22/MADRTemplatePrimer.html>
- 学术对比: <https://ceur-ws.org/Vol-2072/paper9.pdf>

**Phase 7 应用的 per-node 模板:**

```
Slot this node fills: [DAG 中的角色]
Considered options:
1. <chosen_node_id> (CHOSEN) — 描述
   Pros: ...
   Cons: ...
2. <rejected_alt_1> (REJECTED) — 描述
   Pros: ...
   Cons: [具体的失败模式 — 不是 "less preferred"]
Decision driver: [为什么 Option 1 赢 — 引用 §3 的推导步骤]
```

**DERIV-05 要求:** 每节点 ≥1 个 REJECTED 选项,且 REJECTED 的 Cons 必须是 **具体失败模式**(不是"较不优选")。

### §1.7 — 双语策略

per META-03 + CONTEXT.md Area 4/4:

| 元素 | 语言 |
|---|---|
| 章节标题(`## §0`, `## §1`, ...) | English |
| 字段标签(`derivation`, `alternatives-considered`, ...) | English kebab-case |
| 正文论述(理由、解释、推导) | 中文(CN 主)+ 关键英文术语保留 |
| 方法论 canon 术语 | 双语配对(第一性原理 / first principles) |
| 节点 ID | **English kebab-case 专属** — 例如 `creative_source`, `script_auditor` — 不允许中文 ID(否则破坏 Phase 8 YAML canonical layer,触发 PITFALLS §3.5) |
| Musk/Aristotle/TRIZ 引文 | 原文英文 + 括号内中文翻译 |
| 语料引用(书名) | 中文汉字 + (English gloss) 如果有 |
| 审计清单 | English 结构 + CN 论述 |

**v1 expert_id 兼容性(per HANDOFF-02 / FOUND-08 frozen rule):** 候选节点 ID 在与 v1 现有 26 个 expert 干净映射时,**保留** expert_id(如 `creative_source`, `script_auditor`, `cinematographer`, `hook_retention`, `compliance_marketing`)。新节点(AIGC-native 无 v1 对应)用描述性 English kebab-case 命名(如 `prompt_injector`, `continuity_auditor`, `camera_preview`)。**不允许** 静默重命名 v1 已冻结的 expert_id。

---

## §2 — 四个第一性问题 + 语料子集预映射

> 本节声明推导的四个不可还原起点。**问题顺序是 audience-first**(Q1 → Q2 → Q3 → Q4)— 先确立目的论锚("这是为了什么?"),再做能力分析("我们能做什么?")。

### §2.0 — 为什么是这四个问题(而不是五个或三个)

PROJECT.md 里程碑上下文明确指出推导要从根本问题出发。CONTEXT.md Area 2/4 锁定:**4 个问题**,audience-first 排序。第 5 个候选问题("什么是创意?")**显式推迟到 Phase 10**(LLM-Creative-Distillation deep-dive)。

理由:Phase 7 的任务是建立 **AI 能力边界**(Q3 "AI 能加速什么" + Q4 "AI 不能替代什么")。Phase 10 在这个边界内 deep-dive 创意本身。如果 Phase 7 把"什么是创意"也包进来,会导致:
1. Phase 7 范围爆炸(创意是 PITFALLS §4 整章的 topic,不能塞进一个 derivation 问题)
2. Phase 10 失去独立 deep-dive 的价值(被 Phase 7 抢先定义)

**§2.5** 会显式给出 Phase 10 的 forward reference。

### §2.1 — Q1:观众最终消费的是什么?

**问题框架:** 这个问题不可还原,因为它设定了整个推导的目的论锚点。下游的所有问题(哪些节点?哪些 AIGC 转化点?哪些 critic?)都靠"观众实际消费什么"来证成。

**子问题分解:**
- 观众消费的是 **故事**、**影像序列**、**情感弧**,还是三者的整合?
- 观众的体验发生在哪一层 — 叙事层、感知层、情感层?
- 答案在短剧和微电影之间有区别吗?(短剧更偏情感刺激 + 平台分发;微电影更偏叙事完整 + 艺术价值)

**语料子集引用(per DERIV-07):**
- **主语料(STACK §1.4 + 102 书目):**
  - `01-剧本/`(skills-影视创作 17 个 narrative-intent 文件)
  - `06-理论批评/{cinema-fundamentals, film-philosophy-bazin, film-philosophy-tarkovsky}`(回答"电影是什么")
  - 劳逊《戏剧与电影的剧作理论与技巧》(drama-vs-film 差异的根)
- **副语料:**
  - `case-studies/case-01-短片创作全流程.md`
- **Hermes 集成(可直接引用,无需重挖掘,per STACK §2.2):**
  - `theory-formalism-vs-realism.md`(形式主义 vs 现实主义)
  - `film-philosophy-bazin-tarkovsky.md`(Bazin 本体论 + Tarkovsky 雕刻时光)
  - `narrative-revolution-and-modernism.md`(现代主义叙事)

**第一性答案预览(完整推导见 §3):** 观众最终消费的是 **整合的情感-认知体验**,不是视频文件。一个没有情感弧的视频文件被消费为噪声并被遗忘。这种体验 **同时需要** 叙事意义 + 感知丰富 + 情感弧 — 三者不是可分离的阶段产出物,而是同一个体验的不可分割属性。

**认识论标签预览:** Q1 的答案主要是 `psychological`(观众接受层是人类本性偶然但稳定)+ 部分 `physical`(感知不变量如注意力衰减)。

### §2.2 — Q2:什么决定短剧/微电影的质量?

**问题框架:** 这个问题区分好输出和坏输出。质量是多维的(Murch 的 Rule of Six:emotion, story, rhythm, eye-trace, planarity, spatial continuity)— 哪些维度适用于短剧/微电影,权重如何?

**子问题分解:**
- 180° 轴线规则是 `validated-invariant`(感知)还是 `contingent`(惯例)?
- 节奏对短剧(完播率决定分发)和微电影(艺术价值决定电影节选择)的权重是否不同?
- Murch 的六维度里,哪些是 AIGC 最弱的(因此最需要 critic 节点)?
- 短剧 vs 微电影 vs 长片 — 质量驱动是否本质不同?(per PITFALLS §6.3 genre conflation 警告)

**语料子集引用(per DERIV-07):**
- **主语料(STACK §1.4):**
  - `04-后期/{editing-by-murch-rules, editing-rhythm-pacing, color-grading-strategy, final-mix, sound-layering-design}`
  - `03-拍摄/{cinematographer-masterclass, lighting-design, color-narrative-analysis}`
- **副语料:**
  - `02-分镜/{cinematic-language-grammar, mise-en-scene-blocking}`
- **Hermes 集成:**
  - `cinematography-masterclass-and-grammar.md`
  - `editing-sound-post.md`
  - `lighting-equipment-and-design.md`
- **🚨 GAP 标记(per STACK §1.4):** 102 书目以长片为主,**短剧特定质量驱动**(前 3 秒 hook、付费卡点 pacing、竖屏 framing)**不在语料中**。Phase 7 的 Q2 答案必须把语料与 v1 `hook_retention/references/three-second-hooks.md` + 外部短剧源配对。这个 gap 在 Phase 9(corpus-traceability)正式处理。

**第一性答案预览:** 质量由 **跨节点一致性(coherence)** 主导 — 影像是否匹配故事基调?声音是否匹配影像节奏?这是 PITFALLS §5.2 的"coherence budget"洞察:一个电影不是各部分成本之和(反驳 Musk 电池案例的误用),而是 emergent Gestalt,互动质量主导价值。每节点质量是必要但不充分的。

**认识论标签预览:** 主要是 `psychological`(观众质量感知稳定)+ 部分 `platform-algorithmic`(短剧完播率加权波动)。

### §2.3 — Q3:AI 实际能加速什么?

**问题框架:** 这个问题识别 AIGC 边际价值实际在哪 — **不是** 我们希望它在哪。per PITFALLS §1.3 + §2.7:避免过早模型承诺;答案必须在 **用户价值层**(composition lock, identity lock, pacing control),而非 **模型层**(Sora 2, Kling)。

**子问题分解:**
- 哪些人类工艺操作最 **程序化**(低创意外方差、高重复)?
- 哪些操作在人类时间上最 **昂贵**(因此 AIGC 化最有性价比)?
- 哪些操作在当前生成模型能力 **天花板最高**?

**语料子集引用(per DERIV-07):**
- **主语料(STACK §1.4 — 注意:102 书目是 pre-AIGC,Q3 答案需推断):**
  - 从 `04-后期/` 推断哪些后期任务最程序化(调色、foley 分层、ADR 替换)
  - `03-拍摄/animation-production.md`(动画是高程序化 + 高 AIGC 友好)
  - `05-制片/budget-allocation.md`(哪些人类任务最贵)
- **配对 kais-movie-agent V8 架构:** `/data/workspace/kais-movie-agent/docs/V8-ARCHITECTURE.md`(实际尝试过的 AIGC 集成点)
- **Hermes 集成:** `animation-disney-system.md` + `production-chinese-and-low-budget.md`
- **STACK §5 LLM-story-gen 8 篇论文**(Q3 的创意故事子集)

**第一性答案预览:** AI 加速:
- (a) **高程序化后期操作**(调色、foley、混音辅助)
- (b) **规范明确的文本→图/视频生成**(storyboard → 图、script → 视频)
- (c) **一致性验证**(LLM-as-critic 检测剧本 plot hole、跨镜头身份验证)

AI **不** 加速:
- (d) **创意意图起源**(从生活经验挖故事 kernel)
- (e) **最终剪辑判断**(人类的"这个好吗?"判断)
- (f) **平台分发策略**(平台算法是 `platform-algorithmic`,AI 模型训练数据滞后)

**认识论标签预览:** `tool-capability`(当前模型能力 — 最易变,月度迭代)+ `psychological`(哪些操作人类觉得枯燥 — 稳定)。

### §2.4 — Q4:AI 永远不能替代什么?

**问题框架:** 这个问题设定 Phase 10(LLM-Creative-Distillation)将在其中工作的边界。per PITFALLS §1.2 + §5.3:**不** 把验证不变量(Murch、Field 三幕、180° 轴线)当 "bias" 扔掉 — 它们是压缩的智慧,任何诚实推导都会重新发现它们。

**子问题分解:**
- 创意意图能否还原为 prompt?
- AI 能否生成训练分布之外的新组合?
- "一致性"对虚构内容(非事实内容)意味着什么?
- 平台 vs 艺术的张力住在哪里,设计如何避免教条?

**语料子集引用(per DERIV-07):**
- **主语料(STACK §1.4):**
  - `06-理论批评/{film-philosophy-bazin, film-philosophy-tarkovsky, formalism-vs-realism}`(不可还原的创意意图)
  - `01-剧本/{adaptation-writing, character-arc-design, dialogue-crafting}`(创作声音)
  - `03-拍摄/{acting-stanislavski-stella, actor-direction}`(表演真实)
- **配对:**
  - 麦基《故事》
  - 芦苇剧本笔记
- **Hermes 集成:** `theory-formalism-vs-realism.md` + `film-philosophy-bazin-tarkovsky.md` + `narrative-revolution-and-modernism.md` + `screenwriting-chinese-and-supplementary.md`

**第一性答案预览:** AI 不能替代:
- (a) **从生活经验起源的创意意图**(这正是 v1 `creative_source` expert 挖掘的 — 6 个社会阶层的生活经验)
- (b) **最终艺术判断**(theory_critic 咨询式 per META-06,创作者是手动拉的)
- (c) **观众对人类作者特定性的情感共鸣**(Bazin 的"objectivity"论证)

边界 **不是绝对的** — 它随模型能力漂移 — 但设计必须标记哪些节点是 `AI-native`(无传统对应)、`AI-augmented`(压缩传统工作流)、`AI-bounded`(AI 不能替代只能辅助)。

**认识论标签预览:** `psychological`(创意意图是人类本性偶然)+ `physical`(感知不变量如 180° 轴线)。

### §2.5 — Forward reference:Phase 10 (creativity deferred)

第 5 个候选问题"什么是创意?"**显式推迟到 Phase 10** 的 LLM-Creative-Distillation deep-dive。Phase 7 建立 AI 能力边界(Q3 + Q4 答案);Phase 10 在这个边界内 operationalize 创意本身 — **novelty within inviolable constraints**(在不可侵犯约束内的创新),per PITFALLS §4.5。

Phase 10 必须解决的具体问题(本文档 forward-reference,不在 Phase 7 范围):
- 创意的操作性定义(创新 ≠ 随机)
- 自洽性检验机制(consistency-context + logic-critic)
- LLM 凝练 prompt 策略(引用 STACK §5 ≥3 篇 LLM-story-gen 论文)
- 平台 vs 艺术张力的非教条处理
- 模板库(不是单一 Save-the-Cat 模板)
- novelty-pressure 机制,链接回 `creative_source` 节点

Phase 7 的 Q4 答案("AI 不能替代创意意图起源")**直接喂给** Phase 10 的边界定义。Phase 10 不能违背 Q4 — 否则就是 PITFALLS §4 全章的失败模式。

---

