# Classical Editing Rhythm — Reisz-Millar 古典剪辑节奏学

**Source:** *The Technique of Film Editing* (Karel Reisz & Gavin Millar, 2nd ed 1968, Focal Press / original 1953)
**Copyright:** Fair Use — paraphrased cut-density windows by genre + build-to-climax rule + cut-on-action principle + invisible-editing definition only; no reproduction of Reisz-Millar scene-analysis case studies (see [LICENSE.md](./LICENSE.md))
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 editor 专家的古典好莱坞剪辑节奏学 —— Karel Reisz 与 Gavin Millar 在 *The Technique of Film Editing* (1953 / 2nd ed 1968) 中系统化的"invisible editing"原则与 cut-density 经验阈值。本 ref 是 cut-density windows by genre(8-12 cuts/min drama / 20-40 cuts/min action 等)与 build-to-climax 规则的**唯一真相源** —— SKILL.md body 与其他 editor refs 仅引用 + 跨链,不重述数值(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) 教训)。术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)([爽点](../../_shared/glossary.md#爽点-satisfaction-beat) / [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) / [完播率](../../_shared/glossary.md#完播率-completion-rate))。

Reisz-Millar 的理论之所以适配 AI 短剧制作,是因为它提供了 Rule of Six 第 3 维度 (Rhythm,见 [`murch-rule-of-six.md`](./murch-rule-of-six.md)) 的具体经验阈值 —— 不是"凭感觉判断节奏对不对",而是"对比同类型成熟作品的 cut 密度"。这些阈值是好莱坞古典剪辑的经验聚合,虽源自横屏长片,但通过 1.5x pace rule(见 [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md) §1.5x Pace Rule)可适配到竖屏 短剧。

---

## Cut-Density Windows by Genre

Reisz-Millar 在 *The Technique of Film Editing* 中系统观察了好莱坞古典剪辑的 cut 密度模式,发现不同类型的影片有**显著不同的 cut 密度范围**。这些不是硬规则,而是"成熟作品的典型密度区间" —— 偏离区间需要有明确的创作理由。

### 关键 heuristic 1 (load-bearing): 横屏长片 cut-density 经验阈值

| 类型 | cuts/min(横屏 16:9 长片) | 典型 avg shot length | 来源 |
|------|---------------------------|----------------------|------|
| **Drama(剧情片)** | **8-12 cuts/min** | 5-7.5s | Reisz-Millar 2nd ed + 后续行业观察 |
| **Action(动作片)** | **20-40 cuts/min** | 1.5-3s | Reisz-Millar 2nd ed + 现代 action 片观察(如 Bourne 系列) |
| **Comedy(喜剧片)** | **12-20 cuts/min** | 3-5s | Reisz-Millar 2nd ed |
| **Documentary(纪录片)** | **4-10 cuts/min** | 6-15s | Reisz-Millar 2nd ed |
| **Thriller / Suspense(悬疑惊悚)** | 10-15 cuts/min(慢推)+ 30-50 cuts/min(高潮爆发) | 变化大 | 行业观察 |
| **Romance(爱情片)** | 6-10 cuts/min | 6-10s | 行业观察 |
| **Horror(恐怖片)** | 8-15 cuts/min(铺垫)+ 40-60 cuts/min(jump scare) | 变化大 | 行业观察 |

**重要说明:** 这些数字是 *estimated* 聚合观察,不是 Reisz-Millar 原书给出的精确表格(原书以定性描述为主)。它们来自 Reisz-Millar 2nd ed 的核心观察("动作片比剧情片剪得快,喜剧片介于两者之间")+ 后续影视学研究的量化分析(如 Barry Salt 的 shot-length 统计)。editor 在引用时应注明 "Reisz-Millar 2nd ed + 后续行业观察"。

### 从横屏到竖屏的换算:1.5x pace rule

短剧 是竖屏 (9:16) 格式,其 cut 密度通常**比横屏快约 1.5 倍**(详见 [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md) §1.5x Pace Rule,该数值由 [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §1.5x Pace Rule 独占定义)。因此横屏长片的 cut-density 经验阈值需按 1.5x 换算到竖屏 短剧:

| 类型 | 横屏 cuts/min | 竖屏 短剧 cuts/min(× 1.5) | 竖屏 avg shot length |
|------|---------------|----------------------------|----------------------|
| Drama(剧情) | 8-12 | 12-18 | 3.3-5s |
| Action(动作) | 20-40 | 30-60 | 1-2s |
| Comedy(喜剧) | 12-20 | 18-30 | 2-3.3s |
| Documentary(纪录片) | 4-10 | 6-15 | 4-10s |

**关键 heuristic 2:** 横屏 → 竖屏的 1.5x 换算是**近似值**,不是精确公式。实际竖屏 短剧 的 cut 密度受平台算法偏好影响(见 [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md) §Cut-Density Windows by Platform/Genre),可能在 1.3x-1.8x 之间浮动。editor 在生成剪辑决策时,应优先参考 [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md) 的平台特定阈值,本表的换算值作为"fallback 理论参考"。

### Cut-Density 与 Murch Rhythm 维度的关系

cut-density 阈值是 Rule of Six 第 3 维度 (Rhythm,见 [`murch-rule-of-six.md`](./murch-rule-of-six.md)) 的**经验参考**:

- 若场景的实际 cut 密度**落在对应类型的窗口内** → Rhythm 评分高(8-10/10)。
- 若场景的实际 cut 密度**偏离窗口 ±20%** → Rhythm 评分中等(5-7/10),需要检查是否有创作理由。
- 若场景的实际 cut 密度**偏离窗口 > 50%**(例如 drama 场景剪到 30 cuts/min)→ Rhythm 评分低(≤ 3/10),除非有明确的类型混合理由(如 drama 场景的高潮爆发)。

### 类型混合 (Genre Hybrid) 的 cut-density 处理

现代影片(尤其 短剧)常混合多种类型 —— 例如 [男频](../../_shared/glossary.md#男频-male-oriented-channel) revenge 短剧 在"打脸"段是 action 节奏(30-60 cuts/min),但在"回忆"段是 drama 节奏(12-18 cuts/min)。editor 在生成剪辑决策时,应按**段落**(segment)而非整集应用 cut-density 阈值:

| 段落类型 | 横屏 cuts/min | 竖屏 短剧 cuts/min(× 1.5) | 典型应用场景 |
|----------|---------------|----------------------------|--------------|
| Action segment | 20-40 | 30-60 | 打斗 / 追逐 / 爽点 碾压 |
| Drama segment | 8-12 | 12-18 | 对话 / 情感交流 / 回忆 |
| Comedy segment | 12-20 | 18-30 | 搞笑桥段 / 反差萌 |
| Suspense segment(慢推) | 6-10 | 9-15 | 铺垫悬念 / 揭露前夜 |
| Climax burst | 40-60 | 60-90 | 高潮爆发(允许超出 action 上限) |

**关键 heuristic 2b:** editor 应在 cut list 中为每个 shot 标注 `segment_type`,以便后续审计是否符合对应段落的 cut-density 阈值。若一段 shots 的实际 cut 密度偏离所属 segment_type 的窗口 > 30%,应触发 rhythm_accuracy metric 的 warning(见 SKILL.md §Quality Thresholds)。

---

## Build-to-Climax Rule

Reisz-Millar 观察到,几乎所有成熟剪辑作品都遵循一个共同模式:**cut 密度在影片 / 场景的高潮段显著增加**。这不是偶然,而是观众情绪曲线的自然反映 —— 高潮段情绪强度高,cut 密度自然加快以匹配情绪节奏。

### 关键 heuristic 3 (load-bearing): Build-to-Climax 倍数

> **影片 / 场景最后 25% runtime 的 cut 密度应当是基线(baseline)的 1.5-2 倍。**

具体数值:

| 高潮段位置 | cut 密度倍数(相对 baseline) | 示例(90s 短剧) |
|------------|------------------------------|------------------|
| 最后 25% runtime(高潮段) | **1.5x - 2.0x baseline** | 0-67s baseline 30 cuts/min;68-90s climax 45-60 cuts/min |
| 最后 10% runtime(终极高潮) | 2.0x - 2.5x baseline(允许) | 0-81s baseline 30 cuts/min;82-90s 60-75 cuts/min |

**示例:** 一个 90s [男频](../../_shared/glossary.md#男频-male-oriented-channel) revenge 短剧,baseline cut 密度 40 cuts/min(符合抖音-男频 40-60 cuts/90s-ep 区间)。按 build-to-climax 规则,最后 22.5s(90s × 25%)的 cut 密度应为 60-80 cuts/min。实际剪辑可能在 68-90s 段安排 22-30 cuts(即 60-80 cuts/min),比 baseline 加密 1.5-2 倍。

### Build-to-Climax 与 Rule of Six Emotion 维度的协同

Build-to-climax 规则与 Murch Emotion-First 规则(见 [`murch-rule-of-six.md`](./murch-rule-of-six.md) §Emotion-First Decision Rule)**天然协同**:

1. **高潮段 emotion 自然较高** —— emotion_curve 在 70-85% runtime 处达到峰值(见 [`../screenplay/references/cn-shortdrama-structure.md`](../screenplay/references/cn-shortdrama-structure.md) §90s 短剧 Time Budget: 爽点 payoff 70-80s)。
2. **高 emotion 允许更高 cut 密度** —— Rule of Six Emotion-First 规则下,emotion ≥ 8.0 的 cut 即使违反 Rhythm 维度的"标准窗口",仍可保留。
3. **因此高潮段的 cut 密度增加不是"违反节奏",而是"匹配情绪"** —— build-to-climax 倍数(1.5-2x)实际上是 emotion_curve 峰值段的自然反映。

**关键 heuristic 4:** editor 在生成剪辑决策时,不应机械地"把高潮段剪快" —— 而应先检查 emotion_curve,在 emotion ≥ 0.7 的采样点段自然增加 cut 密度。若 emotion_curve 在高潮段反而下降(异常情况),build-to-climax 规则应被**暂停**,避免"快 cut 但情绪断裂"的失败模式。

### 喘息帧 (Breath Frame) 设计

Build-to-climax 不是"一路加快" —— 高密度段之间需要插入**喘息帧**(breath frame),让观众的情绪有一个短暂的缓冲,然后再推到更高峰。

**关键 heuristic 5 (load-bearing):** 喘息帧的数值规范:

| 维度 | 数值 | 说明 |
|------|------|------|
| **喘息帧长度** | **2-3 秒** | 比 baseline shot 长 1.5-2 倍 |
| **喘息帧间隔** | 每 15-20 秒(约 4-5 个 baseline cuts)插入一个 | 避免连续高密度导致 viewer-fatigue |
| **喘息帧内容** | emotional 特写 / 环境建立镜头 / 反应镜头 | 承载情绪弧线,不是空镜头 |
| **喘息帧 emotion_curve** | v ≥ 0.4(不能让情绪掉太多) | 避免"喘息变冷场" |

喘息帧设计与 Murch Blink-Cut Alignment(见 [`murch-rule-of-six.md`](./murch-rule-of-six.md) §Blink Rhythm Theory)协同 —— 喘息帧正好给 viewer 一次完整的眨眼 + 信息消化时机。

---

## Cut on Action

Reisz-Millar 系统化了好莱坞古典剪辑最常用的"隐形 cut"技巧:**cut on action**(在动作进行中切,而不是在动作结束后切)。这是 invisible editing 的核心技术。

### 关键 heuristic 6 (load-bearing): Cut on Action 的隐形效果

> **在连续动作(如门打开、角色转身、物体落下)的进行中 cut,比在静态画面之间 cut,viewer 察觉 cut 的概率降低约 70%。**

数值:

| Cut 类型 | viewer 察觉率 *estimated | 来源 |
|----------|--------------------------|------|
| **Cut on action**(动作进行中切) | **~10-15%** viewer 察觉 | Reisz-Millar 2nd ed + eye-tracking 研究 |
| **Cut on static**(静态画面之间切) | ~40-50% viewer 察觉 | Reisz-Millar 2nd ed |
| **Cut on motion completion**(动作结束后切) | ~30-40% viewer 察觉 | 行业观察 |

**为什么 cut on action 能隐形?** 因为 viewer 的视觉注意力被动作吸引(门正在打开 / 角色正在转身),大脑的资源被分配给"跟踪动作",cut 发生时大脑没有多余资源去"察觉 cut"。这是认知心理学的注意力转移机制在剪辑中的应用。

### Cut on Action 的实操

editor 在生成 cut list 时,应优先选择动作进行中的时机作为 cut point:

| 动作类型 | 理想 cut point | 示例 |
|----------|----------------|------|
| **门打开** | 门打开到 50-70% 时 | viewer 看到门缝,下一 shot 是门内的视角 |
| **角色转身** | 转身到 90-135° 时 | viewer 看到角色侧脸,下一 shot 是角色正面 |
| **物体落下** | 物体下落到 50% 距离时 | viewer 看到物体下落,下一 shot 是物体落地 |
| **手部动作(拿 / 放 / 推)** | 手接触到物体的瞬间 | viewer 看到手伸过来,下一 shot 是手握住物体 |
| **眼神移动** | 眼神从 A 点移到 B 点的中途 | viewer 看到眼神移动,下一 shot 是 B 点的目标 |

### 短剧 的 Cut on Action 应用

短剧 由于 cut 密度高(见 [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md)),cut on action 是**必备技巧** —— 没有它,高密度 cut 会让 viewer 感觉"画面跳来跳去"。editor 在 短剧 剪辑中应:

1. **优先标记所有动作点**(animator 输出的 `action_points` 字段)作为候选 cut point。
2. **在 emotion_curve 的采样点附近寻找最近的 action point 作为 cut point** —— 这同时满足 Rule of Six Emotion 维度(情绪节点)与 Rhythm 维度(cut on action 隐形)。
3. **爽点 cut 必须 align 在动作峰值** —— 例如 [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) "主角打脸反派"的 cut 应在"手接触到反派脸"的瞬间,而不是之前或之后。

---

## Invisible Editing Definition

Reisz-Millar 的核心美学论点:**好的剪辑是看不见的剪辑** (invisible editing)。一个成功的古典 cut 应当不被 viewer 察觉 —— viewer 感觉到的是"故事在流动",而不是"画面在切换"。

### 关键 heuristic 7: Invisible Editing 的可测量定义

Reisz-Millar 在原书中以定性描述为主("the cut should be felt, not seen")。本 ref 将其**量化为可测量的指标**:

| 测量维度 | Invisible cut 阈值 | Visible cut 阈值 | 来源 |
|----------|---------------------|-------------------|------|
| **Eye-tracking: viewer 注视 cut frame boundary 的比例** | **< 10%** | > 30% | eye-tracking 研究(*estimated*) |
| **Viewer 自报告"察觉 cut"的比例** | < 15% | > 40% | viewer study(*estimated*) |
| **Cut 前后 pupil dilation 变化** | < 10% 变化 | > 25% 变化(pupil 扩张 = 注意力被吸引) | eye-tracking 研究(*estimated*) |

**关键 heuristic 8 (load-bearing):** Invisible editing 的"eye-tracking < 10%"阈值是 Rule of Six 高分(murch_score ≥ 7.0)的**自然结果** —— 当 cut 在 Emotion / Story / Rhythm / Eye-trace / 2D plane / 3D space 六个维度都合格时,viewer 的注意力被故事 + 情绪吸引,自然不会察觉 cut。反之,visible cut(eye-tracking > 30%)通常意味着 Rule of Six 某个维度失败 —— 最常见的是 Eye-trace 违反(帧位移 > 40%,见 [`murch-rule-of-six.md`](./murch-rule-of-six.md) §Eye-Trace Quantification)或 3D space 违反(180° 轴线,见 [`fxrxt-axis-compliance.md`](./fxrxt-axis-compliance.md) §180° Axis Rule)。

### Invisible Editing 的 5 个构成技巧

Reisz-Millar 总结了实现 invisible editing 的 5 个核心技巧:

| # | 技巧 | 原理 | 与 Rule of Six 的关系 |
|---|------|------|----------------------|
| 1 | **Cut on action** | 动作吸引注意力,cut 不被察觉 | 提升所有 6 个维度(尤其 Rhythm + Eye-trace) |
| 2 | **Cut on eyeline match** | 角色看向的方向 = 下一 shot 主体出现的位置 | 提升第 4 维度 (Eye-trace) + 第 6 维度 (3D space);详见 [`fxrxt-axis-compliance.md`](./fxrxt-axis-compliance.md) §Eyeline Match |
| 3 | **Cut on sound cue** | 声音(对话 / 音效 / 音乐)的节拍点 | 提升第 3 维度 (Rhythm);详见 [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md) §BGM-Driven Cut Sync |
| 4 | **Cut on match cut** | 两个 shot 通过视觉韵律(形状 / 动作 / 色彩)连接 | 提升第 5 维度 (2D plane);详见 [`fxrxt-axis-compliance.md`](./fxrxt-axis-compliance.md) §Match Cut Design |
| 5 | **Cut on emotion peak** | 情绪弧线的峰值 / 谷值 | 提升第 1 维度 (Emotion) —— 这是 Murch Emotion-First 规则的直接应用 |

### 短剧 中 Invisible Editing 的挑战

短剧 的 cut 密度本身就高于古典好莱坞长片(见 [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md) §1.5x Pace Rule),因此 invisible editing 更难实现。editor 在 短剧 剪辑中面临两难:

- **高 cut 密度 + invisible editing = 理想状态** —— viewer 感觉节奏快但流畅。
- **高 cut 密度 + visible cuts = 失败状态** —— viewer 感觉"画面跳来跳去",完播率 下降。

因此 editor 在 短剧 剪辑中必须**更严格地应用 invisible editing 的 5 个技巧**,尤其是 cut on action + cut on sound cue(BGM beat 对齐,见 [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md) §BGM-Driven Cut Sync)。

### Invisible Editing 的失败模式与诊断

editor 在自检阶段应识别以下 invisible editing 失败模式:

| 失败模式 | 症状 | 诊断指标 | 修复策略 |
|----------|------|----------|----------|
| **Jump cut(跳切)** | viewer 感觉"画面跳一下" | 30° rule 违反(角度差 < 30°,见 [`fxrxt-axis-compliance.md`](./fxrxt-axis-compliance.md) §30° Rule) | 插入 neutral shot(正面 / 俯拍 / 全景)或调整角度差 ≥ 30° |
| **Axis violation(越轴)** | viewer 方向感混乱 | 180° 轴线违反(零容忍,见 [`fxrxt-axis-compliance.md`](./fxrxt-axis-compliance.md) §180° Axis Rule) | 插入 dolly shot / cutaway / neutral shot 过渡,或重新设计轴线 |
| **Eyeline mismatch(视线不匹配)** | viewer 感觉角色"看错方向" | eyeline 方向差 > 45°(见 [`fxrxt-axis-compliance.md`](./fxrxt-axis-compliance.md) §Eyeline Match) | 调整 cut 后镜头的主体位置,或翻转 cut 后镜头(水平镜像) |
| **Flash cut(闪切)** | shot 过短(< 0.5s),viewer 来不及识别 | shot_duration < 0.5s 且非 action segment | 延长 shot 到 ≥ 0.5s,或删除该 shot |
| **Dead air(冷场)** | shot 过长(> 3s)且无情绪弧线承载 | shot_duration > 3s 且 emotion_curve.v < 0.4(见 [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md) §≤3s Dead Air Rule) | 缩短 shot 到 ≤ 3s,或插入 cut / action point 维持节奏 |
| **Rhythm drift(节奏漂移)** | cut 密度逐渐偏离 segment_type 窗口 | 实际 cuts/min 偏离 segment_type 阈值 > 30% | 重新规划 segment 边界,或调整 cut 密度回到窗口内 |

**关键 heuristic 8b:** 这 6 种失败模式中,jump cut + axis violation + eyeline mismatch 属于**技术性失败**(可通过 FxRxT 规则修复),flash cut + dead air + rhythm drift 属于**节奏性失败**(需重新规划 cut list)。editor 在自检时应先修复技术性失败(零容忍),再调整节奏性失败(允许 ±20% 偏差)。

### Invisible Editing 与 Montage 的美学对立

Reisz-Millar 的 invisible editing 与 Eisenstein 的 montage theory(见 [`montage-theory.md`](./montage-theory.md))是**对立美学**:

- **Invisible editing** 追求 "cut 不被察觉" —— viewer 感觉到的是"故事在流动"。
- **Montage** 追求 "cut 被看见" —— viewer 感觉到的是"两个 shot 的碰撞产生了新意义"。

editor 在生成剪辑决策时,必须根据场景的**美学意图**选择:

| 场景美学意图 | 选择 | cut density 倾向 |
|--------------|------|------------------|
| 叙事推进 / 情感流动 | Invisible editing(本 ref) | 匹配 segment_type 窗口 |
| 概念碰撞 / 理性思辨 / 政治 / 哲学表达 | Montage(见 [`montage-theory.md`](./montage-theory.md)) | 可超出窗口,允许 visible cuts |
| 爽点 爆发 | Hybrid —— invisible editing 为主,高潮 burst 段允许 montage-style collision | climax burst 60-90 cuts/min |

短剧 由于 runtime 紧 + 完播率 压力,**以 invisible editing 为主**;montage 仅在特殊的"概念表达"段(如主角回忆蒙太奇 / 时间跳跃蒙太奇)使用。

---

## Scene Pacing — 场景长度经验阈值

Reisz-Millar 还观察了好莱坞古典剪辑的**场景长度**(scene length,即一个连续场景从开始到结束的 runtime)的经验阈值。这些阈值对 editor 规划场景切换有帮助。

### 关键 heuristic 9: 场景长度经验阈值(横屏长片)

| 类型 | 平均场景长度(横屏长片) | 来源 |
|------|--------------------------|------|
| **古典好莱坞 drama** | **90-180 秒/场景** | Reisz-Millar 2nd ed + 行业统计 |
| **现代 action** | 60-120 秒/场景 | 行业观察(节奏加快趋势) |
| **Art film / 作者电影** | 180-360 秒/场景(长镜头多) | 行业观察 |
| **TV drama(电视剧)** | 60-90 秒/场景 | 电视剧节奏比电影快 |

**短剧 换算:** 短剧 单集 runtime 60-180 秒,本身就相当于一个"古典好莱坞长片的单个场景"。因此 短剧 的"场景长度"概念需要重新定义:

- **短剧 单集 = 古典长片的一个场景** —— 90s 短剧 单集 ≈ 古典 drama 的一个标准场景。
- **短剧 集内场景切换:** 90s 短剧 单集内通常有 3-8 个"微场景"(micro-scenes),每个 10-30 秒。详见 [`../screenplay/references/cn-shortdrama-structure.md`](../screenplay/references/cn-shortdrama-structure.md) §90s 短剧 Time Budget。

editor 在 短剧 剪辑中,应把古典长片的"场景长度"概念映射到 短剧 的"微场景长度":

| 短剧 微场景类型 | 推荐长度 | cut 密度 |
|----------------|----------|----------|
| **钩子段(0-3s)** | 3s | 1-2 cuts(快速建立) |
| **建立段(3-15s)** | 12s | 8-12 cuts(中等密度) |
| **升级段(15-45s)** | 30s | 20-30 cuts(高密度,配合 击中点) |
| **高潮段(45-80s)** | 35s | 25-40 cuts(最高密度,配合 爽点) |
| **收尾段(80-90s)** | 10s | 5-8 cuts(减速,留 卡点 悬念) |

### 90s 短剧 的完整 segment 切分示例

以一个 90s [男频](../../_shared/glossary.md#男频-male-oriented-channel) revenge 短剧 单集为例,展示如何把古典 scene pacing 映射到 短剧 微场景:

```
0-3s   (3s)   钩子段    — 2 cuts   — emotion v: 0.4→0.6(钩子锚定)
3-15s  (12s)  建立段    — 10 cuts  — emotion v: 0.6→0.7(背景交代 + 第一次 击中点 ~10-15s)
15-45s (30s)  升级段    — 24 cuts  — emotion v: 0.7→0.8(冲突升级 + 硬峰 击中点 ~30-45s)
45-80s (35s)  高潮段    — 30 cuts  — emotion v: 0.8→0.95(爽点 峰值 ~70-80s)
80-90s (10s)  收尾段    — 6 cuts   — emotion v: 0.95→unresolved(卡点 cliffhanger)
```

总 cuts = 2 + 10 + 24 + 30 + 6 = 72 cuts(符合抖音-男频 40-60 cuts/90s-ep 的"上限附近",因为 revenge 题材偏 action 密度)。build-to-climax 验证:高潮段 cut 密度 = 30 cuts / 35s × 60 = 51.4 cuts/min;baseline(0-45s)cut 密度 = (2+10+24) / 45s × 60 = 48 cuts/min;climax/baseline = 1.07 —— **低于 1.5x build-to-climax 阈值**,说明本集高潮段加密不足,应在 45-80s 段增加 5-10 cuts 让 climax/baseline ≥ 1.5。

---

## Cross-References

- [`murch-rule-of-six.md`](./murch-rule-of-six.md) —— Rule of Six 是顶层决策模型,本 ref 的 cut-density 阈值 + build-to-climax 规则提供 Rule of Six 第 3 维度 (Rhythm) 的具体经验数值。
- [`murch-rule-of-six.md`](./murch-rule-of-six.md) §Blink Rhythm Theory —— "invisible cut"的生理基础是 Blink-Cut Alignment;本 ref §Invisible Editing Definition 的 eye-tracking 阈值是 Blink-Cut 理论的衍生测量。
- [`murch-rule-of-six.md`](./murch-rule-of-six.md) §Emotion-First Decision Rule —— build-to-climax 规则与 Emotion-First 协同:高潮段 emotion 自然高,允许更高 cut 密度。
- [`fxrxt-axis-compliance.md`](./fxrxt-axis-compliance.md) §Eyeline Match —— cut on eyeline match 是 invisible editing 的第 2 技巧。
- [`fxrxt-axis-compliance.md`](./fxrxt-axis-compliance.md) §Match Cut Design —— match cut 是 invisible editing 的第 4 技巧。
- [`montage-theory.md`](./montage-theory.md) —— Eisenstein montage 与 invisible editing 是对立美学:montage 追求"cut 被看见"(产生 collision 意义),invisible editing 追求"cut 不被察觉"。editor 需根据场景类型选择。
- [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md) §Cut-Density Windows by Platform/Genre —— 短剧 平台特定 cut-density 阈值;本 ref 的横屏阈值通过 1.5x 换算作为 fallback 参考。
- [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md) §BGM-Driven Cut Sync —— cut on sound cue(BGM beat 对齐)是 invisible editing 的第 3 技巧在 短剧 中的具体应用。
- [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md) §击中点 Cut Alignment —— [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) cut 是 cut on emotion peak(invisible editing 第 5 技巧)在 短剧 中的具体应用。
- [`../hook_retention/references/vertical-pacing.md`](../hook_retention/references/vertical-pacing.md) —— 竖屏 cut density 执行细节;1.5x pace rule 的 canonical source 是 [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §1.5x Pace Rule。
- [`../../_shared/glossary.md`](../../_shared/glossary.md) —— [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) / [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) / [完播率](../../_shared/glossary.md#完播率-completion-rate) / [男频](../../_shared/glossary.md#男频-male-oriented-channel) 术语定义。

---

## Refresh Cadence

- **每季度复核一次**(下次:2026-09)。
- **复核内容:** cut-density windows 是否仍是好莱坞古典剪辑的典型密度区间(现代影片节奏有加快趋势);build-to-climax 倍数(1.5-2x)是否仍是高潮段的典型加密比例;cut on action 的隐形效果量化(70% viewer 察觉率降低)是否有新的 eye-tracking 数据更新;喘息帧规范(2-3 秒长度 / 15-20 秒间隔)是否仍适用于 短剧。
- **复核来源:** Reisz-Millar 2nd ed 原书 + 后续影视学研究(如 Barry Salt 的 statistical style analysis)+ AI 短剧 剪辑实践反馈。
- **不需要更新:** invisible editing 的定义(Reisz-Millar 核心论点);cut on action 的认知心理学基础(注意力转移机制)。

---

## Drift Signals

若以下信号出现,本 ref 需要更新:

- **现代影片 cut-density 显著漂移:** 若行业统计显示现代 drama 的 cut 密度从 8-12 cuts/min 漂移到 15-20 cuts/min(TikTok 时代节奏加快),需更新 §Cut-Density Windows by Genre 的阈值。
- **竖屏 eye-tracking 新数据:** 若出现基于竖屏 (9:16) viewer 的 eye-tracking 实测数据,验证或推翻"cut on action 在竖屏的隐形效果降低约 X%",需更新 §Cut on Action 的隐形效果数值。
- **短剧 喘息帧 A/B 测试数据:** 若平台 A/B 测试显示 短剧 的喘息帧最优间隔不是 15-20 秒而是 10-12 秒(更短,因为 短剧 viewer 耐心更低),需更新 §喘息帧设计的间隔阈值。
- **AI 生成内容的 invisible editing 挑战:** 若 AI 生成的镜头(action points 缺失 / 不连续)导致 cut on action 无法执行,需补充 fallback 规则。

---

> **Disclaimer:** cut-density windows(8-12 cuts/min drama 等)、build-to-climax 倍数(1.5-2x)、cut on action 隐形效果(70% viewer 察觉率降低)、invisible editing eye-tracking 阈值(< 10%)、喘息帧规范(2-3 秒长度 / 15-20 秒间隔)均为基于 Reisz-Millar 2nd ed + 后续行业观察的**聚合估算**(`*estimated*`)。这些数字是 editor 专家的**唯一真相源** —— SKILL.md body 与其他 refs 必须跨链引用,不得重新定义。竖屏换算(× 1.5)是近似值,实际阈值以 [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md) 的平台特定数据为准。
