# Vertical Pacing — 竖屏 Cut Density + BGM Sync + 字幕 Design

**Source:** 竖屏 短剧 节奏学公开观察 + 创作者经验访谈 + 平台 推荐 算法 公开信息(抖音 / 快手 / 微信小程序剧 创作者中心运营指南)
**Copyright:** Fair Use — aggregated observation only (no reproduction of copyrighted scripts, editing templates, or proprietary creator-playbook material; see [LICENSE.md](./LICENSE.md))
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 `hook_retention` 专家的**竖屏 (9:16) 格式节奏需求**,回答三个核心问题:竖屏为什么比横屏更快?cut 密度的具体数字是多少?字幕 设计语言如何适配竖屏 UI?

本 ref 是竖屏执行细节的专题 ref。**[完播率](../../_shared/glossary.md#完播率-completion-rate) 优化规则的数值(1.5x pace / ≤3s dead air / 60 cuts)由 [`paywall-design.md`](./paywall-design.md) 独占定义** —— 本 ref 只展开这些数值的竖屏执行细节(per-shot types / BGM sync 工作流 / 字幕 safe zones),不重新定义数值本身。术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)([完播率](../../_shared/glossary.md#完播率-completion-rate) / [竖屏](../../_shared/glossary.md#竖屏-vertical-screen-916) / [钩子](../../_shared/glossary.md#钩子-hook) / [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment))。

---

## 竖屏 vs 横屏 Pacing Difference

竖屏 (9:16) 与横屏 (16:9) 的节奏需求有本质差异。以下是 2026-Q2 公开观察的对比(`*estimated*`):

| 维度 | 横屏 (16:9) | 竖屏 (9:16) |
|------|-------------|-------------|
| **平均镜头时长** | 2-3s | **1.5s**(1.5x pace rule,详见 [`paywall-design.md`](./paywall-design.md#15x-pace-rule) §1.5x Pace Rule) |
| **字幕占比** | ~5% frame | **~15-20% frame**(竖屏字幕必须更大,因移动端外放场景多) |
| **视觉重心** | 中心 / 三分法(传统构图) | **上 1/3**(避开顶部 UI overlays:摄像头 / 状态栏)+ **下 1/3**(避开底部 UI:评论 / 互动区) |
| **BGM 节奏** | 较慢,atmospheric(氛围性) | **更快,beat-driven**(节拍驱动,与 cut 同步) |
| **单集时长** | 3-5 min(横屏 IP 改编长剧) | 1-3 min(主流竖屏短剧);3-5 min([小程序剧](../../_shared/glossary.md#小程序剧-mini-program-drama) 长集) |
| **观看场景** | PC / 影院 / 客厅 TV(沉浸式) | 移动端通勤 / 排队 / 碎片时间(易中断) |

### 为什么竖屏更快?

竖屏 1.5x pace rule 的底层逻辑(详见 [`paywall-design.md`](./paywall-design.md#15x-pace-rule) §底层逻辑,本 ref 不重复):

1. **移动端观看场景的退出成本低:** 横屏在影院 / 客厅,观众的退出成本高(买票了 / 坐下了);竖屏在通勤 / 排队,观众的上滑成本几乎为零。因此竖屏必须用更高密度维持注意力。
2. **平台算法偏好快切内容:** [抖音 完播率 权重 ~35% *estimated*](../../compliance_marketing/references/platform-specs-douyin.md#推荐机制for-you-页算法信号),而 完播率 与 cut 密度强相关。慢节奏内容会被算法判定为"低质量",分发权重下降。
3. **竖屏画幅的信息容量更小:** 9:16 比 16:9 的水平视野窄,单镜头能承载的信息更少。因此需要更快切换来维持信息密度。

---

## Cut Density Rules

本节展开 [`paywall-design.md`](./paywall-design.md#15x-pace-rule) §1.5x Pace Rule 的竖屏执行细节。

### 总体规则

竖屏短剧的 cut 应当**平均 every 1.5 seconds** 切换一次(即 1.5x pace rule,横屏 16:9 通常每 2-3 秒切换,因此竖屏比横屏快约 1.5 倍)。

| 规则 | 数值 *estimated* | 来源 |
|------|------------------|------|
| **平均镜头时长** | **1.5s**(平均 every 1.5 seconds 切换) | [`paywall-design.md`](./paywall-design.md#15x-pace-rule) §1.5x Pace Rule(canonical source) |
| **90s 单集最少切数** | **~60 cuts minimum** | 90 ÷ 1.5 = 60(与 paywall-design.md 示例一致) |
| **3 min 小程序剧长集最少切数** | ~120 cuts minimum | 180 ÷ 1.5 = 120 |

### Per-Shot 类型推荐(非硬限制)

不同景别(shot size)的镜头时长有差异。以下是推荐值(`*estimated*` —— 非硬限制,可按场景调整):

| 景别 | 推荐时长 *estimated* | 适用场景 |
|------|----------------------|----------|
| **特写 (close-up)** | 1-2s | 情绪表达 / 关键细节 / 反应镜头 |
| **中景 (medium shot)** | 1.5-2.5s | 对话 / 日常动作 / 角色互动 |
| **全景 (wide shot)** | 2-3s | 场景建立 / 空间关系 / 环境交代 |

> **注意:** 这些是**推荐值**而非硬限制。特写 可短至 0.5s(快速反应镜头),全景 可长至 4s(场景建立)。但任何镜头超过 3s 必须满足 [`paywall-design.md`](./paywall-design.md#≤3s-dead-air-rule) §≤3s Dead Air Rule 的例外条件(情感特写 + BGM swell)。

### 具体示例:90s Romance 短剧 Cold-Open 帧级 Cut List

以下是一个 90s [女频](../../_shared/glossary.md#女频-female-oriented-channel) romance 短剧 cold-open 的帧级 cut list 示例,展示 1.5x pace rule 的实际应用(共 ~18 cuts for first 27s,符合 1.5s/cut):

| Cut # | 时间戳 | 时长 | 景别 | 内容 |
|-------|--------|------|------|------|
| 1 | 0.0-1.0s | 1.0s | 特写 | 女主泪眼特写(0-3s [钩子](../../_shared/glossary.md#钩子-hook) 锚定) |
| 2 | 1.0-2.0s | 1.0s | 特写 | 男主背影(悬念:他是谁?) |
| 3 | 2.0-3.5s | 1.5s | 中景 | 女主追上去,拉住男主袖子 |
| 4 | 3.5-4.5s | 1.0s | 特写 | 男主转身,表情冷漠 |
| 5 | 4.5-6.0s | 1.5s | 中景 | 男主甩开女主的手 |
| 6 | 6.0-7.5s | 1.5s | 特写 | 女主错愕表情 |
| 7 | 7.5-9.0s | 1.5s | 全景 | 场景建立:雨夜街道 |
| 8 | 9.0-10.5s | 1.5s | 中景 | 女主跪坐在地 |
| 9 | 10.5-12.0s | 1.5s | 特写 | 女主抬头,眼神坚定(第一次 [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) ~10-15s) |
| 10 | 12.0-13.5s | 1.5s | 中景 | 女主站起 |
| 11 | 13.5-15.0s | 1.5s | 特写 | 女主擦干眼泪 |
| 12 | 15.0-16.5s | 1.5s | 全景 | 女主转身离开 |
| 13 | 16.5-18.0s | 1.5s | 中景 | 男主在远处注视 |
| 14 | 18.0-19.5s | 1.5s | 特写 | 男主复杂表情 |
| 15 | 19.5-21.0s | 1.5s | 中景 | 男主掏出手机 |
| 16 | 21.0-22.5s | 1.5s | 特写 | 手机屏幕:"监视她的一切" |
| 17 | 22.5-24.0s | 1.5s | 全景 | 场景切换:第二天,女主公司 |
| 18 | 24.0-27.0s | 3.0s | 中景 | 女主走进公司,众人窃窃私语(中段升级 setup) |

> **说明:** 这 18 cuts 覆盖前 27s,平均 1.5s/cut。其中 Cut 18 是 3.0s 中景(场景建立),满足 ≤3s dead air rule 边界(有对白 / 动作,非纯静态)。完整 90s 应有 ~60 cuts,本示例只展开 cold-open 部分。

---

## BGM Sync Requirements

本节定义 竖屏 短剧 cut 与 [composer.coupled_beat](../../composer/SKILL.md#coupled-beat-design) 的同步需求。

### composer.coupled_beat Integration

**契约关系:** composer 专家**独占** `coupled_beat` 概念(包括 `coupled_beat.json` 的 beat grid、energy_per_beat、emotion_tag、coupling_strength 等参数,见 [composer/SKILL.md §Coupled Beat Design](../../composer/SKILL.md#coupled-beat-design))。本 ref 只声明 HOOK 的同步**需求**,从不重新定义 beat 概念。这是跨专家边界([D-7](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) composer 单向边)。

**HOOK 的同步需求:**

| Cut 类型 | 对齐要求 | 容忍度 *estimated* |
|----------|----------|---------------------|
| **重大 cut**(场景转换 / [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) 兑现 / [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) cliffhanger) | **MUST land on beat** | 无容忍(严格对齐) |
| **普通 cut**(日常切换 / 反应镜头) | SHOULD land on beat | **±100ms** *estimated* |

> **注意:** `±100ms` 是 HOOK 专家的最佳实践估算(`*estimated*`)。composer 专家可能有更严格的 spec(例如基于音频采样精度的 ±50ms)。若两者冲突,以 composer 为准(composer 独占 beat 概念)。

### Sync Workflow

典型 BGM 同步工作流(4 步,跨 composer / editor / hook_retention 三专家):

1. **composer 输出 `coupled_beat.json`:** composer 专家根据 [screenplay](../../composer/SKILL.md#collaboration) 的 `emotion_curve` 与 `sound_mood`,生成 BGM stem + `coupled_beat.json`(beat timestamps + energy curve + emotional annotations)。输出格式见 [composer/SKILL.md §Output Format](../../composer/SKILL.md#output-format)。
2. **editor 导入为 cut-grid:** editor 专家将 `coupled_beat.json` 导入剪辑软件,作为镜头切换的对齐参考(cut-grid)。editor 的 cut 决策应优先落在 beat 上。
3. **hook_retention 验证 pacing alignment:** 本专家(hook_retention)**验证** cut 是否落在 beat 上,以及 beat 之间的 dead air 是否 ≤ 3s(见 [`paywall-design.md`](./paywall-design.md#≤3s-dead-air-rule) §≤3s Dead Air Rule)。验证方式:比对 editor 的 cut list 与 composer 的 beat grid,标记偏差 > ±100ms 的普通 cut 或未对齐的重大 cut。
4. **editor 调整未对齐的 cut:** editor 根据验证结果调整 cut,或在必要时请求 composer 微调 beat grid(例如:若 cut 必须落在某个特定帧,但 beat 不在那,composer 可调整 BGM 节奏)。

### BGM Swell Exceptions

BGM 推起(swells)可延长镜头超过 1.5s 基线(跨链 [`paywall-design.md`](./paywall-design.md#≤3s-dead-air-rule) §≤3s Dead Air Rule 例外):

| 场景 | 最长允许 | 触发条件 | 来源 |
|------|----------|----------|------|
| **BGM swell** | **4-5s** | (1) BGM 进入音乐性高潮;(2) 镜头同步呈现视觉冲击;(3) swell 时长 ≤ 5s | [`paywall-design.md`](./paywall-design.md#≤3s-dead-air-rule) §例外 |

**Swell 时长建议(`*estimated*`):**

- **典型 swell 时长:** 2-4s。短于 2s 推起不明显;长于 4s 会让观众感觉"拖"。
- **swell 必须在观众注意力衰减前结束:** 基于 [conflict-escalation.md](./conflict-escalation.md#击中点-placement-density) 的 10-15s 软峰间隔规则,swell 后必须立即接入下一个 cut / [击中点](../../_shared/glossary.md#击中点-emotional-impact-point),重新拉起注意力。
- **swell 与 [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) / [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) 共生:** swell 通常出现在 击中点 或 爽点 的兑现瞬间(放大情绪)。纯氛围性 swell(无情绪兑现)应避免。

---

## 字幕 Design Language

竖屏 (9:16) 的字幕设计与横屏有本质差异 —— 竖屏 UI overlays 占用大量屏幕空间,字幕必须避开这些区域。

### Placement & Safe Zones

**竖屏 UI overlays 占用区域(`*estimated*`,基于 2026-Q2 抖音 / 快手 / 微信小程序剧 平台 UI):**

| 区域 | 占比 *estimated* | 内容 |
|------|------------------|------|
| **顶部** | ~10-15% frame | 摄像头 notch(手机硬件)/ 状态栏 / 平台顶部 UI(返回按钮 / 标题) |
| **底部** | ~15-20% frame | 平台底部 UI(评论按钮 / 点赞 / 转发 / 互动区)/ 手机 home indicator |

**安全区 (safe zone):**

- **安全区 = 中间 ~60% of frame**(避开顶部 + 底部 UI overlays)。
- **字幕放置:** 典型在安全区的**下 1/3**(lower-third of safe zone)。**不是**屏幕底边 —— 底边会被评论 / 互动 UI 遮挡。
- **字幕与底部 UI 的距离:** 至少留 20-30px 间隙(避免视觉拥挤)。

> **注意:** 不同平台的 UI 布局略有差异。[抖音](../../compliance_marketing/references/platform-specs-douyin.md#内容时长与画幅) 字幕安全区"距底边 220-280px";[微信小程序剧](../../compliance_marketing/references/platform-specs-miniprogram.md#长剧集模式与画幅) "需避开微信小程序底部导航栏(高度 ~98px)"。跨平台分发需校准字幕位置。

### Font & Size

**字体推荐(`*estimated*`,基于移动端可读性):**

| 推荐项 | 数值 *estimated* | 说明 |
|--------|------------------|------|
| **字体** | 黑体 / 思源黑体(Source Han Sans) | 无衬线,移动端可读性最佳。避免宋体 / 楷体(小字号下难辨) |
| **字号** | **≥ 4% frame height** | 例如 1920px 高的竖屏,字号 ≥ 77px。低于此值在移动端难辨 |
| **字重** | Medium / Bold | 增加可读性,尤其在复杂背景下 |
| **描边 / 阴影** | 必须(stroke / shadow) | 提供对比度,确保在任何背景下可读 |

**[女频](../../_shared/glossary.md#女频-female-oriented-channel) vs [男频](../../_shared/glossary.md#男频-male-oriented-channel) 字体差异:**

- **女频:** 细黑体 / 宋体(优雅感,情感向)。字号可略小(~3.5-4%),配合精致排版。
- **男频:** 加粗黑体(力量感,爽点向)。字号偏大(~4-5%),配合对比色(黄底黑字 / 红底白字)。

### Duration

字幕在屏时长(on-screen time)规则(`*estimated*`):

| 字幕类型 | 最短 | 最长 | 说明 |
|----------|------|------|------|
| **短句**(≤ 8 字) | **1.5s** | 3s | 最短 1.5s(跨链 [`paywall-design.md`](./paywall-design.md#15x-pace-rule) §1.5x pace rule —— 字幕最短时长 = 最短镜头时长) |
| **长句**(> 8 字) | 2.5s | **4s** | 最长 4s(情感长台词例外,超过 4s 应拆分) |

> **拆分规则:** 超过 4s 的长台词必须拆分为多句字幕,每句 ≤ 4s。拆分点应在自然停顿(逗号 / 句号 / 换气)。

### Emphasis Styling

字幕的强调样式(emphasis styling)用于标记 [钩子](../../_shared/glossary.md#钩子-hook) / [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) / [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) marker 类型。**Marker schema 的完整定义在 SKILL.md body (02-03) 中** —— 本 ref 只定义字幕层面的视觉表现:

| Marker 类型 | 字幕样式 *estimated* | 说明 |
|-------------|----------------------|------|
| **[钩子](../../_shared/glossary.md#钩子-hook)** | **黄色高亮** (yellow highlight) | 标记钩子锚定句(0-3s),吸引注意力 |
| **[爽点](../../_shared/glossary.md#爽点-satisfaction-beat)** | **红色加粗** (red bold) | 标记爽点兑现句,强化冲击 |
| **[卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment)** | **蓝色闪烁** (blue flash) | 标记卡点 cliffhanger 句,制造悬念感 |

> **注意:** 这些样式是**视觉强调**,不是必需的。普通字幕可保持默认样式(白色 + 描边)。强调样式只在 marker 出现时使用,避免过度装饰。

---

## Multi-Platform Pacing Variation

不同平台的 [爆款](../../_shared/glossary.md#爆款-viral-formula-explosive-hit) 公式对节奏密度有不同要求(详见 [CONTEXT D-6](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) 爆款公式分支)。以下是 4 个主流分支的节奏差异(`*estimated*`):

| Platform | 节奏密度 | 典型 cut rate *estimated* | BGM 风格 | 单集时长 |
|----------|----------|---------------------------|----------|----------|
| **抖音-男频** | 极快 | **1.2-1.5s/cut** | 强节奏 electronic(鼓点密集) | 1-3 min |
| **抖音-女频** | 快 | **1.5-2s/cut** | 情感 lyrical(钢琴 / 弦乐) | 1-3 min |
| **快手-草根** | 中等 | **2-2.5s/cut** | 民谣 / 流行(接地气) | 1-3 min |
| **小程序剧-长集数** | 较慢 | **2-3s/cut** | 叙事 instrumental(氛围性) | 3-5 min |

### 各分支的节奏逻辑

**抖音-男频(极快 1.2-1.5s/cut):**
[男频](../../_shared/glossary.md#男频-male-oriented-channel) 战神归来 / 重生复仇题材的核心是 [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) 密度(每 30s 至少 1 个打脸 / 装逼 / 逆袭桥段,见 [抖音 platform-spec](../../compliance_marketing/references/platform-specs-douyin.md#男频爆款公式))。极快 cut 节奏强化"爽感" —— 快速切换让爽点兑现更"炸"。BGM 必须强节奏 electronic(鼓点与 cut 同步)。

**抖音-女频(快 1.5-2s/cut):**
[女频](../../_shared/glossary.md#女频-female-oriented-channel) 豪门虐恋 / 闺蜜背叛题材的核心是 [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) 密度(每集至少 1 个让观众"心痛 / 心动 / 心酸"的瞬间,见 [抖音 platform-spec](../../compliance_marketing/references/platform-specs-douyin.md#女频爆款公式))。快 cut 节奏(略慢于男频)让情绪有"呼吸空间"。BGM 必须情感 lyrical(钢琴 / 弦乐,与情绪转折同步)。

**快手-草根(中等 2-2.5s/cut):**
[快手](../../compliance_marketing/references/platform-specs-kuaishou.md#草根共鸣公式快手主流) 草根共鸣 / 家庭伦理题材的核心是"代入感"(让观众觉得"这就是我 / 我的家人")。中等 cut 节奏让观众有时间"消化"角色处境(太快会让草根观众感觉"看不清")。BGM 民谣 / 流行(接地气)。

**小程序剧-长集数(较慢 2-3s/cut):**
[小程序剧](../../_shared/glossary.md#小程序剧-mini-program-drama) 长集(3-5 min)的节奏可略慢于抖音 / 快手(因为单集时长长,观众投入度高,容忍慢节奏)。但 2-3s/cut 仍快于横屏 16:9。BGM 叙事 instrumental(氛围性,长篇叙事需要)。详见 [小程序剧 platform-spec](../../compliance_marketing/references/platform-specs-miniprogram.md#长剧集模式与画幅)。

> **注意:** 这些 cut rate 是**典型值**而非硬限制。具体题材 / 具体场景可调整。但任何分支都不得低于 [`paywall-design.md`](./paywall-design.md#15x-pace-rule) §1.5x pace rule 的下限(1.5s average)—— 除非是小程序剧长集(2-3s/cut 是其分支特性,但整体仍快于横屏)。

---

## Cross-Reference

本 ref 与 hook_retention 专家的其他 ref、Phase 1 platform-spec refs、以及 composer 专家互链如下:

| 主题 | 跨链目标 | 关系 |
|------|----------|------|
| 完播率 优化规则(1.5x / ≤3s / 60 cuts) | [`paywall-design.md`](./paywall-design.md) (02-02) | **canonical source** —— 本 ref 只展开竖屏执行细节,数值本身由 paywall-design.md 定义。 |
| 卡点 放置 + 付费转化 | [`paywall-design.md`](./paywall-design.md) (02-02) | 卡点 density + 3-tier strength + 5 转发 triggers 详见此 ref。 |
| 阶梯式冲突升级(击中点 / 爽点 density) | [`conflict-escalation.md`](./conflict-escalation.md) (02-01) | 节奏时序(10-15s 软峰 / 30-45s 硬峰 / 6-9 击中点 / 70-80% 爽点 / 30s setup)由此 ref 独占。本 ref 的 cut density 与之配合。 |
| 3 秒钩子设计 | [`three-second-hooks.md`](./three-second-hooks.md) (02-01) | 钩子锚定 (0-3s) 是 cold-open 的第一 cut。本 ref 的帧级 cut list 示例包含钩子锚定。 |
| composer.coupled_beat(BGM 同步契约) | [`../../composer/SKILL.md`](../../composer/SKILL.md#coupled-beat-design) §Coupled Beat Design | composer 专家**独占** beat 概念。本 ref 只声明 HOOK 的同步需求。 |
| 平台 字幕安全区 / UI 布局 | [`../../compliance_marketing/references/platform-specs-douyin.md`](../../compliance_marketing/references/platform-specs-douyin.md#内容时长与画幅) / [`platform-specs-kuaishou.md`](../../compliance_marketing/references/platform-specs-kuaishou.md#内容时长与画幅) / [`platform-specs-miniprogram.md`](../../compliance_marketing/references/platform-specs-miniprogram.md#长剧集模式与画幅) | Phase 1 platform-spec refs 定义各平台 UI 布局与字幕安全区。本 ref 跨链引用。 |
| 术语定义 | [`../../_shared/glossary.md`](../../_shared/glossary.md) | [完播率](../../_shared/glossary.md#完播率-completion-rate) / [竖屏](../../_shared/glossary.md#竖屏-vertical-screen-916) / [钩子](../../_shared/glossary.md#钩子-hook) / [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) / [男频](../../_shared/glossary.md#男频-male-oriented-channel) / [女频](../../_shared/glossary.md#女频-female-oriented-channel) / [小程序剧](../../_shared/glossary.md#小程序剧-mini-program-drama) 的标准定义。 |

---

## Refresh Cadence

- **常规复审周期:** 每 90 天(从 `verified_date` 起算;下次复审日期 = 2026-09-15)。
- **责任方:** `hook_retention` 专家(无人工 owner —— 这是 skill 而非团队职责)。
- **复审动作:**
  1. 复核竖屏 vs 横屏对比表的数值(平均镜头时长 / 字幕占比 / 安全区)是否仍准确 —— 平台 UI 修订会影响这些数字。
  2. 复核 per-shot 类型推荐(特写 / 中景 / 全景时长)是否仍合理。
  3. 复核 BGM sync 容忍度(±100ms *estimated*)是否仍合理 —— 若 composer 专家发布更严格 spec,需同步。
  4. 复核字幕字体 / 字号 / 样式推荐是否仍为最佳实践(移动端显示技术会进化)。
  5. 复核多平台 pacing variation 表的 cut rate 是否仍准确 —— 平台算法权重变化会影响甜区。
  6. 更新 `Last-verified` + `verified_date` 时间戳。
- **过期处理:** `scripts/verify_skill_references.py` 在 Last-verified > 90 天时标记本 ref 为 stale,stale ref 不得作为 RAG 检索源。

---

## Drift Signals

以下事件触发本 ref 的**非常规(提前)复审** —— 不必等到 90 天周期:

- **平台 UI overlay 修订:** 抖音 / 快手 / 微信小程序剧 任意一方修订顶部 / 底部 UI 布局(影响字幕安全区)。
- **算法权重漂移:** 创作者社区观察到高密度内容的推荐权重显著变化(例如:算法从"密度优先"转向"质量优先"),会重写 cut rate 推荐。
- **新 BGM 驱动 爆款 模式出现:** 出现新的"BGM-driven 爆款"模式(例如:某种新型 beat sync 结构),需补充 sync workflow。
- **竖屏显示技术进化:** 手机硬件进化(例如:折叠屏 / 更高刷新率)影响字幕可读性与 cut 节奏容忍度。
- **新平台出现:** 出现 抖音 / 快手 / 微信小程序剧 之外的新竖屏短剧平台,需补充平台专属 pacing。
- **composer 专家 beat spec 修订:** composer 专家修订 `coupled_beat.json` schema 或 coupling_strength 参数,会影响 HOOK 的 sync workflow。
- **字幕 styling 趋势变化:** 创作者社区出现新的字幕 styling 趋势(例如:动态字幕 / 交互字幕),需评估是否扩展 emphasis styling 表。

> 本 ref 所有数值(1.5s / 60 cuts / 4-5s 例外 / ±100ms 容忍度 / 安全区百分比 / per-shot 时长 / 多平台 cut rate)均为基于公开观察的聚合估算(`*estimated*`)。其中 完播率 核心数值(1.5x / ≤3s / 60 cuts)的**canonical source** 是 [`paywall-design.md`](./paywall-design.md);节奏时序数值(10-15s / 30-45s / 6-9 / 70-80% / 30s)的 canonical source 是 [`conflict-escalation.md`](./conflict-escalation.md)。本 ref 只展开竖屏执行细节,不重新定义这些数值。实际效果需通过平台 A/B 测试验证,超出本 ref 的纯文档范围。
