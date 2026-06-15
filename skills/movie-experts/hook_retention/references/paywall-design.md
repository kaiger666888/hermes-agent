# Paywall Design — 付费卡点 Density + 3-Tier Strength + 完播率 Rules + 转发 Triggers

**Source:** 公开 短剧 商业化创作指南 + 平台 付费机制 公开规则(微信小程序剧 / 抖音 / 快手 创作者中心)+ 创作者公开访谈与 MCN 公开运营报告
**Copyright:** Fair Use — aggregated observation only (no reproduction of copyrighted scripts, paywall copy, or proprietary creator-playbook material; see [LICENSE.md](./LICENSE.md))
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 `hook_retention` 专家商业化引擎的核心:**付费卡点 (paywall cliffhanger) 的放置策略**与**完播率 (completion rate) 优化规则**。回答四个核心问题:卡点 应以什么密度分布?卡点 强度如何分级?完播率 的 1.5x / ≤3s 规则如何执行?哪些 转发 (share) 触发器能放大算法分发?

本 ref 是 短剧 商业化数值的**唯一真相源 (canonical source of truth)** —— [`vertical-pacing.md`](./vertical-pacing.md) (02-02) 与 SKILL.md body (02-03) 必须跨链本 ref,而非重新定义数字。**[付费机制 (paywall mechanism) 的合规数字 —— 备案 / 付费门槛 / 分账比例 / 退款规则 —— 由 Phase 1 platform-spec refs 独占](../../compliance_marketing/references/platform-specs-miniprogram.md#付费机制)**;本 ref 只定义"卡点放在哪、强度如何",从不重复合规阈值(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) 教训:同数字在多文件漂移)。术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)([卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) / [付费卡点](../../_shared/glossary.md#付费卡点-paid-conversion-trigger) / [完播率](../../_shared/glossary.md#完播率-completion-rate) / [转发率](../../_shared/glossary.md#转发率-share-rate) / [爆款](../../_shared/glossary.md#爆款-viral-formula-explosive-hit))。

---

## 付费卡点 Density Rules

[付费卡点](../../_shared/glossary.md#付费卡点-paid-conversion-trigger) (paid-conversion trigger) 的密度是 [小程序剧](../../_shared/glossary.md#小程序剧-mini-program-drama) 与 抖音 / 快手 付费短剧变现的最关键变量。以下是 2026-Q2 公开观察的聚合规则(`*estimated*` —— 行业共识,非平台实测数据):

### 密度规则(观察值,`*estimated*`)

| 规则 | 数值 *estimated* | 说明 |
|------|------------------|------|
| **每 10 集 短剧 最少 卡点 数** | **3-5 个** | 10 集小程序剧行业最低标准。低于 3 个会让付费转化漏斗过窄;高于 5 个会让观众疲劳。 |
| **付费集 强制硬卡点** | **≥ 1 hard 卡点 at end of every paid episode** | 每个需要付费解锁的集末,必须有强悬念卡点 —— 这是付费解锁的物理触发器。 |
| **集中段 软卡点 (可选)** | **放置在 ~40-60% runtime** | 软卡点放在集中段,提升中段追看粘性。软卡点 是可选的,不强制。 |
| **卡点 间隔(集数)** | 每 2-3 集至少 1 个 卡点 | 避免连续 3+ 集无 卡点 —— 观众会"忘记"付费动机。 |

### 密度的底层逻辑

为什么是 3-5 / 每 10 集?基于以下公开观察的推理:

1. **观众容忍阈值:** 公开创作者访谈一致指出,小程序剧观众对付费频率的心理容忍度约在"每 2-3 集一次"。低于此频率会让观众感觉"总是在付费",高于此频率则会让付费漏斗过窄、变现效率低。3-5 / 10 集是这条曲线的甜区。
2. **算法偏好频繁 卡点:** 抖音 / 快手 / 微信小程序剧 的推荐算法权重中,[完播率](../../_shared/glossary.md#完播率-completion-rate) 与互动率(转发 / 评论 / 点赞)是核心指标。卡点 的本质是"未解的悬念",会驱动观众在评论区讨论("男主到底死没死"),从而提升互动率 —— 间接提升算法分发权重。
3. **硬卡点 vs 软卡点 的权衡:** 硬卡点 (episode end, 强制付费) 是直接变现触发器,但密度过高会让免费集观众流失(因为他们无法解锁);软卡点 (mid-episode, 提升粘性但不强制付费) 是免费观众的"留人器",但本身不产生收入。3-5 / 10 集 的组合通常是"硬卡点为主 + 软卡点为辅"。

### 卡点 位置规则(集中段 vs 集末)

| 卡点 类型 | 位置 | 强度要求 | 触发行为 |
|-----------|------|----------|----------|
| **硬 卡点 (hard cliffhanger)** | 集末 | 必须是 🟢 must-watch-next | 观众付费解锁下一集 |
| **软 卡点 (soft cliffhanger)** | ~40-60% runtime | 可为 🟡 curious-but-skippable | 观众继续观看本集,提升完播率 |

集中段(40-60%)放置软卡点的逻辑:观众在 30-40% 处会有第一次注意力低谷(见 [conflict-escalation.md](./conflict-escalation.md#击中点-placement-density) 软峰间隔规则)。此时放置一个软卡点(轻悬念),会重新拉起注意力,把观众带过中段疲劳区,提升单集完播率。

---

## 3-Tier 卡点 Strength Scoring

[卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) 本身有强度分级。一个"弱卡点"会让观众"觉得满足,可以不看了",反而降低付费转化率。以下是 3 级强度评分(借用但不重复 [`three-second-hooks.md`](./three-second-hooks.md) 的 5 级符号体系 —— 卡点 只需要 3 级,因为 cliffhanger 的语义空间比 hook 窄):

| Tier | 符号 | 名称 | Viewer Behavior | 典型设计特征 |
|------|------|------|-----------------|--------------|
| 1 | 🟢 | **must-watch-next** | 观众无法停止;立即付费解锁 | 未解的悬念 + 角色切身利益(unresolved mystery + character stakes) |
| 2 | 🟡 | **curious-but-skippable** | 观众好奇但可能容忍等待 | 软揭示 + 未来爽点的承诺(soft reveal + promise of future payoff) |
| 3 | 🔴 | **weak-resolve** | 观众"满足到可以停下" | 卡点前过度解决剧情,观众觉得"这集够了" |

### 强度评分的应用规则

强度评分不是"打完分就完了" —— 它直接驱动 卡点 设计的改写决策:

1. **硬 卡点 (集末) 必须是 🟢:** 任何集末付费卡点,若评分为 🟡 或 🔴,必须重写。这是商业变现的硬约束 —— 一个 🟡 集末卡点会让付费转化率下降 30-50%(*estimated*,基于公开创作者访谈聚合)。
2. **软 卡点 (集中段) 可以是 🟡:** 集中段软卡点的目的是"提升追看粘性",不直接驱动付费。🟡 软卡点是可接受的 —— 但 🟢 软卡点效果更好。
3. **🔴 weak-resolve 是反模式 (anti-pattern):** 无论硬卡点还是软卡点,🔴 都是必须避免的。它的本质是"在卡点前过度解决剧情",让观众感觉"本集已经够了"。常见原因:
   - 在集末把误会完全解开,只剩"明天会发生什么"的弱悬念。
   - 在卡点前让主角已经成功反击,反派已经失败,只剩"善后"的弱悬念。
   - 在卡点前揭穿所有关键真相,只剩"主角如何反应"的弱悬念。

### 🟢 must-watch-next 的设计要素

一个 🟢 硬卡点必须同时具备以下 3 个要素(公开观察的聚合,`*estimated*`):

- **未解的核心悬念 (unresolved core mystery):** 卡点必须留下一个让观众"必须知道答案"的核心问题。例如:"主角到底死没死" / "真相到底是什么" / "主角会选择谁"。
- **角色切身利益 (character stakes):** 悬念必须直接关系到主角的切身利益(生死 / 身份 / 爱情 / 复仇 / 财富)。若只是"配角的八卦",观众容忍度低。
- **下一集承诺的爽点 (promised payoff):** 卡点必须暗示"下一集会兑现一个爽点"(见 [conflict-escalation.md](./conflict-escalation.md#爽点-placement-strategy) 的 70-80% 爽点放置规则)。例如:卡点"反派得意洋洋"暗示下一集"主角反杀"。

---

## 完播率 Optimization Rules

[完播率](../../_shared/glossary.md#完播率-completion-rate) (completion rate) 是平台算法的最高权重指标([抖音 ~35% *estimated*](../../compliance_marketing/references/platform-specs-douyin.md#推荐机制for-you-页算法信号))。本节定义 完播率 优化的 3 条核心规则 —— 这些规则是本 ref 的**唯一真相源**,[`vertical-pacing.md`](./vertical-pacing.md) (02-02) 与 SKILL.md body (02-03) 必须跨链引用。

### 1.5x Pace Rule

**规则:** 竖屏短剧的平均镜头时长(average shot duration)应为 **1.5 秒**(横屏 16:9 通常为 2-3 秒,因此称为"1.5x pace rule" —— 竖屏比横屏快约 1.5 倍)。

**具体数值:**

| 维度 | 数值 *estimated* |
|------|------------------|
| 竖屏平均镜头时长 | **1.5s** |
| 横屏平均镜头时长(对比) | 2-3s |
| 90s 单集最少切数 | **~60 cuts minimum**(90 ÷ 1.5 = 60) |
| 1-3 分钟短剧的"高密度"门槛 | ≥ 60 cuts / 90s |

**底层逻辑:**

1. **算法偏好高密度内容:** 抖音 / 快手 / 微信小程序剧 的推荐算法明确偏好高 cut 密度(参见 [抖音 完播率 权重 ~35%](../../compliance_marketing/references/platform-specs-douyin.md#推荐机制for-you-页算法信号))。慢节奏内容会被算法判定为"低质量",分发权重下降。
2. **观众注意力衰减曲线:** 移动端观众的注意力衰减比 PC / 影院更快。一个镜头超过 2s,观众的上滑概率显著上升。1.5s 是平衡"信息密度"与"理解负担"的甜区。
3. **小程序剧长集数模式的例外:** [小程序剧](../../_shared/glossary.md#小程序剧-mini-program-drama) 长集(3-5 min)的 cut 密度可略低(2-2.5s),但仍需高于横屏 16:9。详见 [`vertical-pacing.md`](./vertical-pacing.md#multi-platform-pacing-variation) 的多平台分支。

**具体示例:** 一个 90s 抖音男频 战神归来 短剧,按 1.5x 规则应至少 60 cuts。若实际只有 40 cuts(平均 2.25s/cut),完播率会显著低于同类型爆款。

### ≤3s Dead Air Rule

**规则:** 竖屏短剧中,不允许出现超过 **3 秒** 的"死寂镜头"(silent / static stretch)—— 即无对白、无动作、无 BGM 推进的纯静态镜头。

**底层逻辑:** 死寂镜头让观众"出戏"。在移动端竖屏场景(通勤 / 排队 / 碎片时间),观众的退出成本极低,3s 死寂足以触发上滑。

**例外(EXCEPTIONS —— 明确文档化何时可以打破规则):**

以下场景**可以**延长镜头超过 3s,但必须同时满足触发条件:

| 场景 | 最长允许 | 触发条件(必须同时满足) |
|------|----------|--------------------------|
| **情感特写 (emotional close-up)** | **4-5s** | (1) 可见的强烈情绪(流泪 / 颤抖 / 凝视);(2) BGM 同步推起(BGM swell);(3) 该特写是 [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) 或 [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) 的兑现瞬间 |
| **BGM 推起 (BGM swell)** | **4-5s** | (1) BGM 进入音乐性高潮(鼓点 / 弦乐推起);(2) 镜头同步呈现视觉冲击(慢动作 / 关键画面);(3) 推起时长 ≤ 5s(超出会让观众感觉"拖") |
| **艺术停顿 (artistic pause)** | **3-4s** | (1) 戏剧效果停顿(例如:主角得知真相后的沉默);(2) BGM 必须有"呼吸感"的轻伴奏(不是死寂);(3) 停顿后立即接入下一个 cut / 对白 |

**反模式(必须避免):**

- **纯静态镜头 > 3s:** 无对白、无动作、无 BGM 推进的纯空镜 / 静物镜头。这是 100% 违规。
- **长台词单镜头 > 3s:** 一个角色在固定机位说超过 3s 的台词,无镜头切换。应拆分为多机位 / 反应镜头。
- **情感特写 + 无 BGM:** 即使有情绪,若无 BGM 推起,仍属违规(因为 BGM 是"情感放大器")。

**何时明确打破规则:** 本 ref 明确允许在"情感特写 + BGM swell"组合下延长到 4-5s。但纯静态镜头(无情绪、无 BGM)超过 3s **永远是违规**,无例外。

### BGM-Driven Sync

**规则:** 竖屏短剧的 cut(镜头切换)**应当**对齐 [composer.coupled_beat](../../composer/SKILL.md#coupled-beat-design) 时间戳。重大 cut(场景转换 / [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) 兑现) **必须**对齐 beat。

**契约关系:** composer 专家**独占** `coupled_beat` 概念的定义(包括 beat grid、energy_per_beat、emotion_tag 等参数)。本 ref 只声明 HOOK 的同步**需求**(cut 应当对齐 beat),从不重新定义 beat 概念。这是跨专家边界([D-7](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) composer 单向边)。

**同步工作流(典型 4 步):**

1. composer 专家输出 `coupled_beat.json`(beat timestamps + energy curve + emotional annotations),见 [composer/SKILL.md Output Format](../../composer/SKILL.md#output-format)。
2. editor 专家导入 `coupled_beat.json` 作为 cut-grid(镜头切换的对齐参考)。
3. hook_retention 专家(本专家)**验证** pacing alignment —— 检查 cut 是否落在 beat 上,以及 beat 之间的 dead air 是否 ≤ 3s。
4. editor 调整未对齐的 cut,或在必要时请求 composer 微调 beat grid。

**容忍度 (tolerance, `*estimated*`):**

| Cut 类型 | 对齐容忍度 *estimated* | 说明 |
|----------|------------------------|------|
| 重大 cut(场景转换 / 爽点兑现) | **MUST land on beat** | 必须严格对齐 beat,无容忍 |
| 普通 cut | ±100ms *estimated* | 允许 ±100ms 偏差(肉眼难辨) |

> **注意:** `±100ms` 是 HOOK 专家的最佳实践估算(`*estimated*`)。composer 专家可能有更严格的 spec。若两者冲突,以 composer 为准(composer 独占 beat 概念)。

---

## 5 转发 Trigger Categories

[转发率](../../_shared/glossary.md#转发率-share-rate) (share rate) 是平台算法权重仅次于 [完播率](../../_shared/glossary.md#完播率-completion-rate) 的核心指标([抖音 ~25% 互动率合并权重 *estimated*](../../compliance_marketing/references/platform-specs-douyin.md#推荐机制for-you-页算法信号))。观众转发 短剧 的动机可归纳为 5 类固定触发器:

| Trigger | 定义 | 典型设计 | 转发率预期影响 *estimated* |
|---------|------|----------|----------------------------|
| **情感共鸣** | 观众深深感受到情绪(共鸣 / 心痛 / 心动 / 心酸) | 强情感场景 + 可代入的角色处境 | *estimated* 高 for [女频](../../_shared/glossary.md#女频-female-oriented-channel)(豪门虐恋 / 亲情催泪) |
| **反转冲击** | 观众被意外转折震惊 | setup-payoff 结构 + 误导性线索 | *estimated* 高 for both [男频](../../_shared/glossary.md#男频-male-oriented-channel) / [女频](../../_shared/glossary.md#女频-female-oriented-channel) |
| **共识认同** | 观众认同内容表达的立场 / 价值观 | 价值宣告 + 角色倡导 | *estimated* 中(依赖话题热度) |
| **视觉震撼** | 视觉瞬间值得反复看 / 分享 | 震撼镜头 / VFX 时刻 / 慢动作 | *estimated* 高 for [抖音](../../compliance_marketing/references/platform-specs-douyin.md) 算法 |
| **实用价值** | 观众能用内容中的信息(how-to / 生活技巧 / 建议) | 可操作内容 + 短剧叙事框架 | *estimated* 高 for [快手](../../compliance_marketing/references/platform-specs-kuaishou.md) 草根观众 |

### 各 Trigger 的设计指南

**情感共鸣 (emotional resonance):**
设计让观众"代入主角处境"的场景。典型:[女频](../../_shared/glossary.md#女频-female-oriented-channel) 豪门虐恋中的"被婆婆当众羞辱"桥段 —— 观众代入"如果是我"。关键要素:(1) 角色处境必须可代入(普通人的困境);(2) 情绪必须真实(不浮夸);(3) 配合 BGM swell(放大情绪)。本 trigger 与 [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) 概念高度重叠。

**反转冲击 (twist shock):**
设计 setup-payoff 结构,通过误导性线索让观众"以为主角会 A,结果是 B"。典型:[男频](../../_shared/glossary.md#男频-male-oriented-channel) 战神归来中的"以为是主角被打败,结果是主角故意示弱以引出幕后黑手"。关键要素:(1) 误导线索必须合理(不能凭空反转);(2) 反转必须兑现一个爽点(不是为反转而反转)。本 trigger 与 Phase 1 [viral-element-catalog.md](../../compliance_marketing/references/viral-element-catalog.md) 中的 **反差钩** 元素重叠 —— 跨链查询。

**共识认同 (value consensus):**
设计让观众"点头同意"的价值宣告。典型:职场剧中的"打工人不该被 996 剥削" —— 观众认同并转发表达立场。关键要素:(1) 价值观必须是主流共识(非争议性);(2) 必须由角色之口表达(不是说教);(3) 话题热度越高,转发率越高。本 trigger 的风险:若价值观偏激,可能触发 [抖音 标题党与封面欺诈 🟡 红线](../../compliance_marketing/references/platform-specs-douyin.md#平台专属红线) —— 需 compliance_marketing 联检。

**视觉震撼 (visual spectacle):**
设计值得反复看的视觉瞬间。典型:慢动作打斗 / VFX 特效 / 震撼构图。关键要素:(1) 视觉必须超越日常(普通镜头不算);(2) 必须配合 BGM beat sync(增强冲击);(3) 时长建议 1-2s(够震撼但不拖)。本 trigger 在 [抖音](../../compliance_marketing/references/platform-specs-douyin.md) 算法中权重最高(抖音偏好"视觉冲击"内容)。

**实用价值 (practical utility):**
设计观众"能用上"的内容。典型:[快手](../../compliance_marketing/references/platform-specs-kuaishou.md) 草根短剧中的"如何用 10 元做出一桌菜"。关键要素:(1) 信息必须可操作(观众能立即用);(2) 必须包装在短剧叙事中(不是纯教程);(3) 适合快手草根观众([快手 实用价值 权重高于抖音](../../compliance_marketing/references/platform-specs-kuaishou.md#爆款公式))。本 trigger 是 [快手](../../compliance_marketing/references/platform-specs-kuaishou.md) 独有强项。

### Trigger 与 [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) / [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) 的关系

5 转发 trigger 不是孤立的 —— 它们通常与 [conflict-escalation.md](./conflict-escalation.md) 定义的 击中点 / 爽点 共生:

- **情感共鸣 trigger** 通常出现在 击中点 (emotional-impact point) 上。
- **反转冲击 trigger** 通常出现在 爽点 (satisfaction beat) 上。
- **视觉震撼 trigger** 通常出现在 爽点 或 击中点 上(取决于视觉类型)。
- **共识认同 / 实用价值 trigger** 通常独立于 击中点 / 爽点(它们是叙事层面的)。

---

## Hard vs Soft 卡点 Examples

以下是 3 个具体场景,展示 hard 卡点 + soft 卡点 的组合设计(每场景 ≥ 2 hard + 1 soft,符合 [CONTEXT specifics](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md)):

### Scenario 1: Romance 短剧 (女频 typical)

**题材:** [女频](../../_shared/glossary.md#女频-female-oriented-channel) 豪门虐恋(灰姑娘 + 霸总 + 误会 + 真相)

| 卡点 | 类型 | 位置 | 强度 | 内容 |
|------|------|------|------|------|
| Ep 3 末 | **Hard 1** | 集末 | 🟢 must-watch-next | 误会揭示:女主撞见男主与"前女友"亲密相拥,泪奔离开 —— 悬念:女主会原谅吗?(角色切身利益:爱情) |
| Ep 5 中段 (~50%) | **Soft** | 集中段 | 🟡 curious-but-skippable | 感情进展暗示:男主默默为女主准备生日惊喜,但女主不知情 —— 软悬念:女主会发现吗? |
| Ep 5 末 | **Hard 2** | 集末 | 🟢 must-watch-next | 真相临近:前女友当众揭穿"女主只是替身",男主沉默 —— 悬念:男主会选择谁?(角色切身利益:身份 + 爱情) |

**设计要点:** 2 个 hard 卡点都是 🟢,直接驱动付费解锁;1 个 soft 卡点放在 Ep 5 中段,连接 Ep 3 与 Ep 5 末的两个 hard 卡点,维持中段追看粘性。

### Scenario 2: Revenge 短剧 (男频 typical)

**题材:** [男频](../../_shared/glossary.md#男频-male-oriented-channel) 战神归来 / 重生复仇

| 卡点 | 类型 | 位置 | 强度 | 内容 |
|------|------|------|------|------|
| Ep 3 末 | **Hard 1** | 集末 | 🟢 must-watch-next | 反派出招:反派联手主角的"兄弟"设下陷阱,主角陷入绝境 —— 悬念:主角如何脱身?(角色切身利益:生死) |
| Ep 4 中段 (~45%) | **Soft** | 集中段 | 🟡 curious-but-skippable | 实力提升暗示:主角在绝境中触发隐藏能力,但尚未完全觉醒 —— 软悬念:主角会觉醒到什么程度? |
| Ep 5 末 | **Hard 2** | 集末 | 🟢 must-watch-next | 主角觉醒:主角完全觉醒隐藏实力,反杀陷阱,反派震惊跪地 —— 悬念:幕后黑手是谁?(角色切身利益:复仇 + 身份) |

**设计要点:** Hard 1(反派优势)+ Soft(主角觉醒暗示)+ Hard 2(主角反杀)构成完整的"危机-转折-胜利"弧线。Soft 卡点放在两 Hard 之间,让观众在 Ep 4 中段就预感到"主角要逆袭了",维持追看粘性。

### Scenario 3: Comedy 短剧 (快手 typical)

**题材:** [快手](../../compliance_marketing/references/platform-specs-kuaishou.md) 草根职场喜剧

| 卡点 | 类型 | 位置 | 强度 | 内容 |
|------|------|------|------|------|
| Ep 3 末 | **Hard 1** | 集末 | 🟢 must-watch-next | 下一笑点 setup:主角(外卖员)接到一个大单,客户开门竟是曾经的霸凌者 —— 悬念:主角会怎么做?(角色切身利益:尊严) |
| Ep 4 中段 (~50%) | **Soft** | 集中段 | 🟡 curious-but-skippable | 角色发展暗示:主角的"隐藏富豪身份"线索浮现(有人称呼他"少爷"),但主角迅速否认 —— 软悬念:主角真实身份是什么? |
| Ep 5 末 | **Hard 2** | 集末 | 🟢 must-watch-next | 笑点兑现 + 身份揭穿:主角富豪身份被霸凌者当众发现,霸凌者脸色精彩 + 主角淡定回应 —— 悬念:霸凌者会怎么求饶?(角色切身利益:尊严 + 逆袭) |

**设计要点:** 喜剧的 卡点 设计需平衡"笑点"与"悬念"。Hard 1 是"下一笑点 setup"(让观众想看兑现);Soft 是"角色发展暗示"(增加深度);Hard 2 是"笑点兑现 + 身份揭穿"(双重满足)。

---

## Cross-Reference

本 ref 与 hook_retention 专家的其他 ref、Phase 1 platform-spec refs、以及 composer 专家互链如下:

| 主题 | 跨链目标 | 关系 |
|------|----------|------|
| 付费机制 合规规则(备案 / 付费门槛 / 分账比例) | [`../../compliance_marketing/references/platform-specs-miniprogram.md`](../../compliance_marketing/references/platform-specs-miniprogram.md#付费机制) §付费机制 | **Phase 1 独占合规数字** —— 本 ref 只定义卡点放置策略,从不重复 备案 / 付费门槛 / 分账数字。 |
| 抖音 付费机制 | [`../../compliance_marketing/references/platform-specs-douyin.md`](../../compliance_marketing/references/platform-specs-douyin.md#付费机制) §付费机制 | **Phase 1 独占合规数字** —— 同上。 |
| 快手 付费机制 | [`../../compliance_marketing/references/platform-specs-kuaishou.md`](../../compliance_marketing/references/platform-specs-kuaishou.md#付费机制) §付费机制 | **Phase 1 独占合规数字** —— 同上。 |
| 阶梯式冲突升级(击中点 / 爽点 density) | [`conflict-escalation.md`](./conflict-escalation.md) (02-01) | [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) 是阶梯式升级的**第 5 级 Rung**(episode end cliffhanger)。本 ref 定义 卡点 放置,conflict-escalation.md 定义 卡点 在阶梯中的位置。 |
| 3 秒钩子设计 | [`three-second-hooks.md`](./three-second-hooks.md) (02-01) | Ep N 的 卡点 → Ep N+1 的 钩子锚定(见 conflict-escalation.md Multi-Episode Escalation)。 |
| 竖屏 cut density + BGM sync 细节 | [`vertical-pacing.md`](./vertical-pacing.md) (02-02) | 完播率 1.5x / ≤3s / 60 cuts 数值的**竖屏执行细节**(per-shot types / 字幕 design / multi-platform variation)详见此 ref。 |
| composer.coupled_beat(BGM 同步契约) | [`../../composer/SKILL.md`](../../composer/SKILL.md#coupled-beat-design) | composer 专家**独占** beat 概念。本 ref 只声明 HOOK 的同步需求(cut 对齐 beat),不重新定义 beat。 |
| 爆款 元素目录(反转冲击 ↔ 反差钩) | [`../../compliance_marketing/references/viral-element-catalog.md`](../../compliance_marketing/references/viral-element-catalog.md) | Phase 1 爆款 catalog。本 ref 的"反转冲击 trigger"与 viral-element-catalog 的"反差钩"重叠 —— 跨链查询。 |
| 术语定义 | [`../../_shared/glossary.md`](../../_shared/glossary.md) | [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) / [付费卡点](../../_shared/glossary.md#付费卡点-paid-conversion-trigger) / [完播率](../../_shared/glossary.md#完播率-completion-rate) / [转发率](../../_shared/glossary.md#转发率-share-rate) / [爆款](../../_shared/glossary.md#爆款-viral-formula-explosive-hit) / [男频](../../_shared/glossary.md#男频-male-oriented-channel) / [女频](../../_shared/glossary.md#女频-female-oriented-channel) / [小程序剧](../../_shared/glossary.md#小程序剧-mini-program-drama) 的标准定义。 |

---

## Refresh Cadence

- **常规复审周期:** 每 90 天(从 `verified_date` 起算;下次复审日期 = 2026-09-15)。
- **责任方:** `hook_retention` 专家(无人工 owner —— 这是 skill 而非团队职责)。
- **复审动作:**
  1. 复核 卡点 密度数字(3-5 / 10 集)是否仍准确 —— 平台算法与观众容忍度会随时间漂移。
  2. 复核 完播率 优化规则(1.5x / ≤3s / 60 cuts)是否仍为甜区 —— 若平台分发逻辑改变,这些数字可能需调整。
  3. 复核 5 转发 trigger 分类是否仍覆盖新兴转发模式(例如:新的"meme 化"转发模式)。
  4. 复核 hard vs soft 卡点 示例是否仍具代表性(题材趋势会变化 —— 例如 2026-Q3 若出现新的"AI 题材"爆款,需补充对应示例)。
  5. 复核 hard 卡点 强度 🟢 的 3 个设计要素(未解悬念 / 角色切身利益 / 下一集爽点承诺)是否仍准确描述观众付费动机。
  6. 复核 BGM sync 容忍度(±100ms *estimated*)是否仍合理 —— 若 composer 专家发布了更严格的 spec,需同步更新。
  7. 更新 `Last-verified` + `verified_date` 时间戳。
- **过期处理:** `scripts/verify_skill_references.py` 在 Last-verified > 90 天时标记本 ref 为 stale,stale ref 不得作为 RAG 检索源(见 [`../../_shared/SKILL-LAYOUT.md`](../../_shared/SKILL-LAYOUT.md#reference-file-anatomy) 的 Refresh cadence 规则)。

---

## Drift Signals

以下事件触发本 ref 的**非常规(提前)复审** —— 不必等到 90 天周期:

- **平台 付费机制 修订:** [微信小程序剧](../../compliance_marketing/references/platform-specs-miniprogram.md#付费机制) / [抖音](../../compliance_marketing/references/platform-specs-douyin.md#付费机制) 任意一方修订 付费门槛 / 分账比例 / 退款规则(会间接影响 卡点 放置策略的变现效率)。
- **完播率 算法权重漂移:** 创作者社区观察到 完播率 权重显著变化(例如:抖音从"密度优先"转向"质量优先"),会重写 1.5x / ≤3s 规则。
- **新 转发 模式出现:** 出现本 ref 未覆盖的第 6 类 trigger(例如:"meme 化"转发 / "二创"转发),需扩展 trigger 分类。
- **付费转化率 行业基准变化:** 公开创作者访谈显示 卡点 付费转化率基准显著变化(例如:从 3-8% 降到 1-3%),会重写 卡点 强度评分。
- **新平台出现:** 出现 抖音 / 快手 / 微信小程序剧 之外的新短剧平台(例如:小红书短剧 / B站竖屏短剧),需补充平台专属规则与 卡点 密度调整。
- **观众跳出模式变化:** 创作者社区观察到观众跳出点发生显著偏移(原本 7s 跳出率高,现在变成 5s),会缩短 dead air 容忍度 —— 届时需把 ≤3s 规则收紧为 ≤2s。
- **跨平台 卡点 策略融合:** 观察到多平台分发(抖音 + 小程序剧 同步上线)成为主流,需补充"跨平台 卡点 差异化"策略(例如:抖音版 卡点 更密集,小程序剧版 卡点 更深度)。

> 本 ref 所有数字阈值(3-5 卡点 / 1.5x pace / ≤3s dead air / 60 cuts / 4-5s 例外 / 5 triggers)均为基于公开观察的聚合估算(`*estimated*`)。这些数字是 hook_retention 专家的**唯一真相源** —— [`vertical-pacing.md`](./vertical-pacing.md) (02-02) 与 SKILL.md body (02-03) 必须跨链引用,不得重新定义。实际效果需通过平台 A/B 测试验证,超出本 ref 的纯文档范围。
