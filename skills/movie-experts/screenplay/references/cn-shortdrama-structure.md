# CN 短剧 Structure — 90s / 180s Time Budgets + 10-Episode Season Arc + Per-Platform Divergence

**Source:** 公开 短剧 创作指南 + 创作者公开访谈 + 行业 whitepapers (MCN 公开运营报告) aggregated
**Copyright:** Fair Use — aggregated observation only (no reproduction of copyrighted scripts, paywall copy, or proprietary creator-playbook material; see [LICENSE.md](./LICENSE.md))
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 CN 短剧 (Chinese vertical short-drama) 的**多集连续剧结构** —— 区别于西方短片的单集独立形态,短剧 是 10-80 集的连续剧,每集 60-180s,以 [付费卡点](../../_shared/glossary.md#付费卡点-paid-conversion-trigger) 驱动变现。本 ref 回答三个核心问题:**单集内部的时间预算如何分配?跨集的 season arc 如何设计?不同平台(抖音 / 快手 / 微信小程序剧)的结构如何分化?**

本 ref 是 短剧 结构数值的**唯一真相源** —— SKILL.md body 仅引用数字 + 跨链,不重述原理(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) 教训)。术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)([钩子](../../_shared/glossary.md#钩子-hook) / [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) / [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) / [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) / [完播率](../../_shared/glossary.md#完播率-completion-rate) / [男频](../../_shared/glossary.md#男频-male-oriented-channel) / [女频](../../_shared/glossary.md#女频-female-oriented-channel) / [小程序剧](../../_shared/glossary.md#小程序剧-mini-program-drama))。本 ref 的 卡点 密度规则跨链 [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md)(单一真相源 —— 本 ref 不重复付费机制数字)。

---

## 90s 短剧 Time Budget

90s 是 抖音 单集短剧的标准形态([男频](../../_shared/glossary.md#男频-male-oriented-channel) 逆袭 / [女频](../../_shared/glossary.md#女频-female-oriented-channel) 闪婚 的主流集长)。以下是 2026-Q2 公开观察的聚合时间预算表(`*estimated*` —— 行业共识,非平台实测数据):

### 单集 90s 时间预算表(heuristic)

| 时间段 | 功能 | Runtime | 占比 | 对应 Snyder beat | 对应 HOOK marker |
|--------|------|---------|------|------------------|------------------|
| **0-3s** | **[钩子](../../_shared/glossary.md#钩子-hook)** | 3s | 3% | Opening Image + Save the Cat | 钩子 (5-type taxonomy 任一) |
| **3-15s** | **setup** | 12s | 13% | Set-Up + Catalyst | (无独立 marker) |
| **15-40s** | **escalation** | 25s | 28% | Debate + Fun & Games | 击中点 (软峰,~10-15s) |
| **40-70s** | **[爽点](../../_shared/glossary.md#爽点-satisfaction-beat) setup** | 30s | 33% | Midpoint + Bad Guys Close In | 击中点 (硬峰,~30-45s) + value-shift |
| **70-80s** | **[爽点](../../_shared/glossary.md#爽点-satisfaction-beat) payoff** | 10s | 11% | All Is Lost + Break into Three + Finale | 爽点 peak (9-10/10) |
| **80-88s** | **resolution** | 8s | 9% | Finale (收尾) | (情绪从峰值回落) |
| **88-90s** | **[卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) cliffhanger** | 2s | 2% | Final Image | 卡点 (硬卡点,🟢) |

**关键 heuristic 1:** 钩子 必须在 **0-3s**(不是 0-5s)。抖音 算法的 完播率 权重在 3s 处有一个陡降拐点 —— 观众如果在前 3s 没有被钩住,后续 87s 的内容质量再高也救不回 完播率。这与 [`emotion-curve-academic.md`](./emotion-curve-academic.md) §Attention Decay Curve 的数据吻合(8-12s 无 击中点 则 attention drops ≥ 15%)。

**关键 heuristic 2:** [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) payoff 必须在 **70-80s**(70-85% runtime)。这对应 Snyder 的 All Is Lost + Break into Three + Finale 压缩段。爽点 早于 70s(例如 60s 处)会让后续 30s 缺乏情绪峰值 —— 观众在 80-90s 的 卡点 前流失;爽点 晚于 85s(例如 85s 处)会让 卡点 cliffhanger 没有时间展开(卡点 需要 ≥ 2s 的悬念铺垫)。

**关键 heuristic 3:** [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) cliffhanger 必须在 **88-90s**(集末 2s)。卡点 不是"集末的最后一句话",而是"集末的最后 2s 的悬念锚点"。卡点 的功能是驱动观众点击"下一集" —— 它必须是一个**未解的、高强度的悬念**,而不是一个"温和的收尾"。硬卡点 强度目标 🟢 must-watch-next(见 [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §3-Tier Strength)。

### 击中点 密度(heuristic)

**关键 heuristic 4:** 90s 单集的 [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) 密度应为 **6-9 个**(平均每 10-15s 一个)。低于 6 个会让节奏"平";高于 9 个会让节奏"碎"(观众来不及消化每个 击中点)。这与 [`../hook_retention/references/conflict-escalation.md`](../hook_retention/references/conflict-escalation.md) §The 阶梯式 Escalation Ladder 的 5 级阶梯模型对应 —— 5 级阶梯 + 1-4 个过渡 击中点 = 6-9 个总数。

### 90s 短剧 各段的 击中点 分布(heuristic)

90s 单集的 6-9 个 击中点 不是均匀分布的 —— 不同段的密度不同:

| 时间段 | 击中点 密度 | 典型 击中点 类型 | 说明 |
|--------|-------------|-------------------|------|
| **0-3s(钩子段)** | 1 个(必须) | 钩子 pin | 开场 3 秒钩子本身就是一个 击中点 |
| **3-15s(setup 段)** | 1-2 个 | 第一次冲击(软峰) | setup 段不能全平淡,需要 1-2 个小 击中点 维持注意力 |
| **15-40s(escalation 段)** | 2-3 个 | 中段升级(硬峰) | escalation 段是 击中点 最密集的段 —— 主角与反派的初次交锋 |
| **40-70s(爽点 setup 段)** | 1-2 个 | value-shift 点 | 爽点 setup 段的 击中点 主要是 value-shift(局势恶化) |
| **70-80s(爽点 payoff 段)** | 1 个(必须) | 爽点 peak | 爽点 兑现是全集情绪峰值 —— 1 个极强 击中点 |
| **80-90s(resolution + 卡点 段)** | 0-1 个 | 卡点 cliffhanger | resolution 段通常无 击中点(情绪回落);卡点 是最后一个 击中点 |

**关键 heuristic 5(衍生):** escalation 段(15-40s)的 击中点 密度应最高(2-3 个 / 25s = 每 8-12s 一个),因为这是观众"被卷入"的关键段 —— 如果 escalation 段 击中点 不足,观众在 40s 后流失。这与 [`emotion-curve-academic.md`](./emotion-curve-academic.md) §Attention Decay Curve 的"8-12s 无 击中点 则 attention drops ≥ 15%"精确吻合。

### 90s 短剧 时间预算的验证清单

每个 90s 短剧 单集应通过以下时间预算验证:

1. [ ] 钩子 在 0-3s(不是 0-5s)
2. [ ] setup 在 3-15s(12s 窗口)
3. [ ] escalation 在 15-40s(25s 窗口,击中点 密度最高)
4. [ ] 爽点 setup 在 40-70s(30s 窗口)
5. [ ] 爽点 payoff 在 70-80s(10s 窗口,情绪峰值)
6. [ ] resolution 在 80-88s(8s 窗口)
7. [ ] 卡点 cliffhanger 在 88-90s(2s 窗口)
8. [ ] 总 击中点 数 6-9 个
9. [ ] escalation 段 击中点 ≥ 2 个

---

## 180s 短剧 Time Budget

180s 是 [小程序剧](../../_shared/glossary.md#小程序剧-mini-program-drama) 单集的典型形态(集长是 抖音 90s 的 2 倍,叙事容量更大)。180s 允许 2 个 [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) 和 1 个 mid-episode 软卡点。

### 单集 180s 时间预算表(heuristic)

| 时间段 | 功能 | Runtime | 占比 | 对应 Snyder beat | 对应 HOOK marker |
|--------|------|---------|------|------------------|------------------|
| **0-3s** | **钩子** | 3s | 2% | Opening Image + Save the Cat | 钩子 |
| **3-18s** | **setup** | 15s | 8% | Set-Up + Catalyst | (无独立 marker) |
| **18-45s** | **escalation (first half)** | 27s | 15% | Debate + Fun & Games (first) | 击中点 (软峰,~20-25s) |
| **45-80s** | **mid-escalation** | 35s | 19% | Midpoint + Fun & Games (second) | 击中点 (硬峰,~45-55s) + value-shift |
| **80-90s** | **mid-episode 软卡点 (可选)** | 10s | 6% | (Midpoint 之后的小低谷) | 软卡点 (🟡,见 [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §3-Tier Strength) |
| **90-140s** | **second escalation + 爽点 setup** | 50s | 28% | Bad Guys Close In + All Is Lost | 击中点 (硬峰,~120s) |
| **140-160s** | **爽点 payoff (second)** | 20s | 11% | Break into Three + Finale | 爽点 peak (9-10/10) |
| **160-175s** | **resolution** | 15s | 8% | Finale (收尾) | (情绪从峰值回落) |
| **175-180s** | **卡点 cliffhanger** | 5s | 3% | Final Image | 卡点 (硬卡点,🟢) |

**关键 heuristic 5:** 180s 短剧 的 [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) 兑现位置有两个 —— **mid-爽点 (~140s,对应 first escalation 的 payoff)** 和 **late-爽点 (~150s,对应 second escalation 的 payoff)**。mid-爽点 通常是"小胜"(主角解决了一个子问题),late-爽点 是"大胜"(主角解决了主线问题)。两个 爽点 之间必须有 All Is Lost 段(~120-140s)制造低谷,否则情绪曲线是"平顶"(缺乏起伏)。

**关键 heuristic 6:** mid-episode 软卡点(80-90s,~45-50% runtime)是 180s 短剧 的可选组件。它的功能是"提升中段追看粘性",但不强制付费。软卡点 强度 🟡 curious-but-skippable 即可(见 [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §3-Tier Strength)。不是所有 180s 短剧 都需要 mid-episode 软卡点 —— 如果主线紧张度足够,可以跳过。

### 180s 短剧 的双 爽点 设计(heuristic)

180s 短剧 允许 2 个 爽点,但两个 爽点 的关系需要精心设计:

| 爽点 类型 | 位置 | 功能 | 与 All Is Lost 的关系 |
|-----------|------|------|----------------------|
| **mid-爽点 (~140s)** | first escalation 的 payoff | 主角解决一个子问题 | mid-爽点 之后必须有 All Is Lost 段(120-140s)制造低谷 |
| **late-爽点 (~150s)** | second escalation 的 payoff | 主角解决主线问题 | late-爽点 是 Finale 的核心,无需后续低谷 |

**关键 heuristic 7(衍生):** mid-爽点 与 late-爽点 之间**必须有 All Is Lost 段**。如果两个 爽点 连续触发(中间没有低谷),情绪曲线是"平顶" —— 观众感受不到 late-爽点 的峰值,因为 mid-爽点 已经把情绪拉到高位。正确设计:mid-爽点(情绪 8)→ All Is Lost(情绪 3)→ late-爽点(情绪 10)。

### 180s 短剧 时间预算的验证清单

每个 180s 短剧 单集应通过以下时间预算验证:

1. [ ] 钩子 在 0-3s
2. [ ] setup 在 3-18s(15s 窗口)
3. [ ] first escalation 在 18-45s(27s 窗口)
4. [ ] mid-escalation 在 45-80s(35s 窗口)
5. [ ] mid-episode 软卡点(可选)在 80-90s
6. [ ] second escalation 在 90-140s(50s 窗口)
7. [ ] late-爽点 payoff 在 140-160s(20s 窗口)
8. [ ] resolution 在 160-175s(15s 窗口)
9. [ ] 卡点 cliffhanger 在 175-180s(5s 窗口)
10. [ ] mid-爽点 与 late-爽点 之间有 All Is Lost 段

---

## 10-Episode Season Arc

短剧 / 小程序剧 是连续剧形态,单集结构之上还有 **season arc**(跨集叙事弧)。10 集是最短的典型 season(抖音 短剧 常见);30 集 / 80 集是 小程序剧 的常见 season 长度。本节给出 10 集 season arc 的设计规则(更长 season 是 10 集 arc 的扩展)。

### 10 集 season arc 的 [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) 密度(heuristic)

**关键 heuristic 7:** 每集的 击中点 密度为 **6-9 个**(见 §90s 短剧 Time Budget)。10 集 season 的总 击中点 数为 **60-90 个**。这不是"越多越好" —— 击中点 过密会让观众疲劳(情绪阈值上升,后续 击中点 效果递减)。

### 10 集 season arc 的大 [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) 放置(heuristic)

**关键 heuristic 8:** 大 爽点(改变主线走向的 爽点,而非每集的小 爽点)应放置在以下 3 个位置:

| 位置 | 集数 | 爽点 类型 | 功能 | 对应 HOOK marker |
|------|------|-----------|------|------------------|
| **season 早段** | **ep 3** | 第一个大 爽点(主角首次小胜) | 给观众"这部剧值得追"的信号 | 爽点 (setup 跨集 callback) |
| **season 中段** | **ep 7** | 中段大 爽点(主角接近目标但有新障碍) | 维持中段追看动力 | 爽点 (payoff 跨集 callback) |
| **season 末段** | **ep 10 (finale)** | 终极 爽点(主线完全兑现) | 完结满足感 + 续季悬念(若有) | 爽点 (终极 payoff) |

**为什么是 ep 3 / ep 7 / ep 10?**
- ep 3:观众在 ep 1-2 建立 hook 后,ep 3 必须给第一个"兑现" —— 否则 ep 4+ 的 完播率 会崩(观众觉得"剧情拖")。
- ep 7:season 中段是"疲劳区" —— 观众在 ep 5-6 开始流失(新鲜感消退)。ep 7 的大 爽点 是"重新钩住"的关键。
- ep 10 (finale):完结满足感决定续季转化率 + 口碑传播(转发率)。

### 10 集 season arc 的 [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) 密度(heuristic)

**关键 heuristic 9:** 卡点 密度遵循 [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §付费卡点 Density Rules 的 **3-5 卡点 / 10 集** 规则(单一真相源 —— 本 ref 不重复数字原理)。典型放置:

| 集数 | 卡点 类型 | 强度 | 说明 |
|------|-----------|------|------|
| **ep 3** | 硬卡点 | 🟢 | 第一个付费门槛(观众已被 ep 1-2 的 hook 钩住,愿意付费) |
| **ep 5-6** | 硬卡点 | 🟢 | 中段付费门槛 |
| **ep 7-8** | 软卡点 (可选) | 🟡 | 中段粘性提升(不强制付费) |
| **ep 9-10** | 硬卡点 | 🟢 | season 末悬念(驱动续季或完结满足) |

这与 [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §付费卡点 Density Rules 的"每 2-3 集至少 1 个 卡点"规则一致。

### 10 集 Season Arc 的 跨集 callback 设计(heuristic)

[小程序剧](../../_shared/glossary.md#小程序剧-mini-program-drama) 的长 season(30-80 集)依赖跨集 callback 维持悬念。关键 heuristic:

**关键 heuristic 10(衍生):** 跨集 callback 应遵循"setup-遗忘-提醒-payoff" 4 步协议:

1. **setup (ep N):** 在 ep N 中植入一个悬念锚点(例如主角发现一封信)。此时观众可能不觉得重要。
2. **遗忘 (ep N+1 ~ N+2):** 在接下来 1-2 集中不提及这个锚点 —— 让观众"忘记"它。这制造了 payoff 时的惊喜。
3. **提醒 (ep N+3):** 在 ep N+3 中用一个 subtle 线索提醒观众(例如背景中出现同一封信)。
4. **payoff (ep N+4 ~ N+5):** 在 ep N+4 或 N+5 中兑现 payoff(信的内容揭露)。此时观众会回忆起 setup,产生"原来如此"的满足感。

这个 4 步协议与 HOOK marker schema 的 `setup_callback` / `payoff_callback` 字段对应(见 [`../hook_retention/SKILL.md`](../hook_retention/SKILL.md) §Marker Schema)。`setup_callback` 字段值 = "S1E0N MM:SS — 主角发现信";`payoff_callback` 字段值 = "S1E0N+4 — 信的内容揭露"。

### 10 集 Season Arc 的验证清单

每个 10 集 season arc 应通过以下验证:

1. [ ] ep 3 有第一个大 爽点(主角首次小胜)
2. [ ] ep 7 有中段大 爽点(主角接近目标但有新障碍)
3. [ ] ep 10 (finale) 有终极 爽点(主线完全兑现)
4. [ ] 卡点 密度 3-5 / 10 集(跨链 [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md))
5. [ ] 每 2-3 集至少 1 个 卡点
6. [ ] 付费集末必有 🟢 hard 卡点
7. [ ] 至少 1 个跨集 callback(setup-遗忘-提醒-payoff 4 步协议)

---

## Per-Platform Divergence

不同平台的受众偏好 + 算法权重 + 付费机制差异,导致 短剧 结构在不同平台上有显著分化。本节给出 3 个主要平台(抖音 / 快手 / 微信小程序剧)的结构差异点。

### 抖音(短剧 主流平台)

- **集长偏好:** **60-90s**(算法偏好高密度短格式;长集数会降低 完播率 权重)
- **题材偏好:** [男频](../../_shared/glossary.md#男频-male-oriented-channel) 逆袭 / 复仇 / 装穷打脸 / 战神;[女频](../../_shared/glossary.md#女频-female-oriented-channel) 闪婚 / 萌宝 / 替身 / 豪门虐恋
- **节奏密度:** 最快 cut 密度(1.5s 平均镜头 —— 抖音算法权重 完播率 ~35% `*estimated*`,快切是硬约束,见 [`../hook_retention/references/vertical-pacing.md`](../hook_retention/references/vertical-pacing.md) §Multi-Platform Pacing Variation)
- **付费门槛位置:** 第 5-7 集(见 [`../../compliance_marketing/references/platform-specs-douyin.md`](../../compliance_marketing/references/platform-specs-douyin.md) §付费机制,跨链不重复数字)
- **钩子 风格:** 高强度 冲突钩 / 反差钩 为主(抖音受众追求即时刺激)
- **典型 season 长度:** 20-30 集(短 season,快节奏)

### 快手(草根 短剧 平台)

- **集长偏好:** **60-120s**(略长于抖音;草根 题材需要更多 setup 时间建立共情)
- **题材偏好:** 草根 / 家庭 / 情感共鸣 / 普通人逆袭(避 炫富画面信号 —— 豪车 / 名表 是平台专属 红线,见 [`../../compliance_marketing/references/platform-specs-kuaishou.md`](../../compliance_marketing/references/platform-specs-kuaishou.md) §内容红线)
- **节奏密度:** 略慢于抖音(1.5-2.5s 平均镜头;草根美学 避免过度快切显得"刻意")
- **付费门槛位置:** 第 6-10 集(晚于抖音;快手付费意愿较低)
- **钩子 风格:** 情感钩 为主(快手受众重视"接地气"与"真实感")
- **典型 season 长度:** 20-40 集(快手受众对长 season 容忍度更高,因为情感共鸣驱动)

### 微信小程序剧(长集数 付费 短剧)

- **集长偏好:** **120-180s**(最长形态;集长允许更复杂的叙事容量)
- **题材偏好:** 长剧集悬念 / 多集反转 / 季末解谜 / 家族秘辛 / 重生复仇(深度叙事)
- **节奏密度:** 单集内部慢(2-3s 平均镜头,因集长更长);但 [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) 密度最高(每集末硬卡点 + 集中段软卡点)
- **付费门槛位置:** 第 3-5 集(最早;每集末必有 🟢 hard 卡点,见 [`../../compliance_marketing/references/platform-specs-miniprogram.md`](../../compliance_marketing/references/platform-specs-miniprogram.md) §付费机制)
- **钩子 风格:** 悬念钩 / 情感钩 复合(长 season 需要更深层的悬念锚定)
- **典型 season 长度:** 30-80 集(最长 season;serial cliffhanger 是核心商业模式)
- **特殊要求:** 双重 备案(广电 + 微信小程序),见 [`../../compliance_marketing/references/platform-specs-miniprogram.md`](../../compliance_marketing/references/platform-specs-miniprogram.md) §备案

### 平台分化总结表(heuristic)

| 维度 | 抖音 | 快手 | 微信小程序剧 |
|------|------|------|--------------|
| 集长 | 60-90s | 60-120s | 120-180s |
| cut 密度(平均镜头) | 1.5s | 1.5-2.5s | 2-3s |
| 付费门槛位置 | ep 5-7 | ep 6-10 | ep 3-5 |
| 卡点 密度(/10 集) | 3-5 | 3-5(较柔) | 5+(最高) |
| 钩子 主类型 | 冲突钩 / 反差钩 | 情感钩 | 悬念钩 / 情感钩 |
| season 长度 | 20-30 集 | 20-40 集 | 30-80 集 |
| 主导受众情绪 | 即时刺激 | 共鸣 / 真实感 | 悬念 / 深度叙事 |

### 平台分化的底层逻辑(heuristic)

为什么三个平台的结构差异如此显著?底层逻辑是**受众画像 + 算法权重 + 付费机制**三者的交叉:

**关键 heuristic(衍生):** 平台分化由三个因素共同决定:

1. **受众画像:** 抖音 受众偏年轻(18-35 岁)/ 城市化 / 追求即时刺激;快手 受众偏下沉市场 / 重视"接地气";小程序剧 受众偏中年女性 / 有付费能力 / 追求深度叙事。
2. **算法权重:** 抖音 算法权重 完播率 ~35% `*estimated*`(快切是硬约束);快手 算法权重 转发率 / 互动率(草根共鸣是核心);小程序剧 无公开算法(依赖 付费卡点 直接变现)。
3. **付费机制:** 抖音 付费门槛在 ep 5-7(较晚);快手 付费门槛在 ep 6-10(更晚,付费意愿低);小程序剧 付费门槛在 ep 3-5(最早,每集末硬卡点)。

这三个因素的交叉决定了每个平台的"最优结构" —— 创作者不能"一套剧本打所有平台",必须按平台分化调整结构。

---

## 使用说明

本 ref 是 screenplay 专家的 5 个 curated refs 之一(Phase 3 [CONTEXT D-1](../../../../../.planning/phases/03-top-4-existing-experts-rag/03-CONTEXT.md) source mix 第 3 项:CN 短剧 multi-episode structure)。screenplay SKILL.md 的 `## References` 表列出本 ref 的触发条件与核心内容摘要。

本 ref 的所有数值(time budget 各段位置 / 击中点 密度 / per-platform divergence 表 / season arc 大 爽点 位置)是**唯一真相源** —— screenplay SKILL.md body 的 scene_count threshold 依赖这些数字。screenplay SKILL.md body 不重复定义,只引用 + 跨链。

---

## Cross-References

- [`save-the-cat-beat-sheet.md`](./save-the-cat-beat-sheet.md) §短剧 Adaptation —— Snyder 15-beat 模型到 短剧 的 runtime 换算(本 ref 给 短剧 专属的时间段命名:钩子/setup/escalation/爽点/卡点,Snyder 给 beat 命名)
- [`mckee-scene-design.md`](./mckee-scene-design.md) §Value-Shift Rule —— 短剧 单场景的 value-shift rate(≥ 1 per scene)与本 ref 的 击中点 密度互补
- [`emotion-curve-academic.md`](./emotion-curve-academic.md) §Attention Decay Curve —— 8-12s 无 击中点 则 attention drops ≥ 15%;为本 ref 的 击中点 密度(6-9 per 90s)提供实证支撑
- [`dialogue-craft.md`](./dialogue-craft.md) §Per-Platform Register Divergence —— 不同平台的台词 register 差异(与本 ref 的节奏差异互补)
- [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §付费卡点 Density Rules —— 卡点 密度的单一真相源(3-5 / 10 集);本 ref 跨链不重复
- [`../hook_retention/references/conflict-escalation.md`](../hook_retention/references/conflict-escalation.md) §The 阶梯式 Escalation Ladder —— 击中点 的情绪强度升级阶梯
- [`../hook_retention/references/three-second-hooks.md`](../hook_retention/references/three-second-hooks.md) §Taxonomy —— 钩子 5-type taxonomy(本 ref 的 0-3s 钩子段消费)
- [`../../compliance_marketing/references/platform-specs-douyin.md`](../../compliance_marketing/references/platform-specs-douyin.md) / [`platform-specs-kuaishou.md`](../../compliance_marketing/references/platform-specs-kuaishou.md) / [`platform-specs-miniprogram.md`](../../compliance_marketing/references/platform-specs-miniprogram.md) —— 平台专属的 备案 / 付费机制 / 内容红线 数字(跨链不重复)
- [`../_shared/glossary.md`](../../_shared/glossary.md) —— 术语定义

---

## Refresh Cadence

- **季度复核(每 90 天):** 重新验证各平台集长偏好 / cut 密度 / 付费门槛位置是否仍为当前算法下的甜区
- **平台算法变更触发:** 抖音 / 快手 / 微信小程序剧 推荐算法权重调整时,重新验证 击中点 密度 / 钩子 位置 / 卡点 密度
- **新平台涌现触发:** 若出现新的主要 短剧 分发平台(例如 视频号 短剧 / B站 竖屏短剧),补充对应 per-platform divergence 条目
- **集长形态变化触发:** 若出现新的集长标准(例如 240s 超长集 / 45s 极短集),补充对应 time budget 表
- **跨集 callback 协议变化触发:** 若 短剧 行业出现新的跨集 callback 设计模式,修订 §10 集 Season Arc 的跨集 callback 设计
- **击中点 密度规则变化触发:** 若 A/B 测试显示 击中点 密度甜区漂移,更新 §90s 短剧 各段的 击中点 分布 表
- **负责模块:** screenplay SKILL.md body 的 scene_count / dialogue_density threshold 依赖本 ref

### 复核协议(heuristic)

每次复核应遵循以下 4 步协议:

1. **平台数据采集:** 从各平台创作者中心收集最近 90 天的 完播率 曲线 + 付费转化 数据(若公开)
2. **time budget 验证:** 对比当前 time budget 表的各段位置(钩子 0-3s / Catalyst ~9s / Midpoint ~45s 等)与实测 完播率 拐点
3. **per-platform divergence 验证:** 对比各平台的集长 / cut 密度 / 付费门槛位置与当前 divergence 表
4. **文档更新:** 更新 Last-verified 日期 + 修订记录;同步 screenplay SKILL.md 的 References 表

---

## 修订记录

| 日期 | 版本 | 修订内容 | 修订人 |
|------|------|----------|--------|
| 2026-06-15 | v1.0 | 初版 — 90s/180s time budget + 10-ep season arc + per-platform divergence | Phase 3 plan 03-01 |

---

## Drift Signals

以下信号提示本 ref 可能已过时,需要重新验证:

1. **集长偏好漂移:** 若 抖音 主流集长从 60-90s 漂移到 90-120s(更长的叙事容量),需更新 §90s 短剧 Time Budget 和 §Per-Platform Divergence
2. **付费门槛位置变化:** 若各平台的 付费门槛 位置系统性调整(例如 小程序剧 从 ep 3-5 提前到 ep 1-2),需更新 §10-Episode Season Arc 和 §Per-Platform Divergence
3. **新 钩子 类型涌现:** 若出现 5-type taxonomy 之外的新钩子类型(例如"互动钩"在互动短剧中),需评估是否纳入 §90s 短剧 Time Budget 的 0-3s 段
4. **击中点 密度规则失效:** 若 A/B 测试显示"低 击中点 密度(3-5 per 90s)"在某些题材下 完播率 更高,需修订 §90s 短剧 Time Budget 的密度规则
5. **跨平台趋同:** 若各平台的结构差异逐渐缩小(例如 抖音 和 快手 的 cut 密度趋同),需简化 §Per-Platform Divergence 表
