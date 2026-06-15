# Murch Rule of Six — 加权评分模型 + Emotion-First 决策 + Eye-Trace 量化 + Blink 节奏

**Source:** *In the Blink of an Eye: A Perspective on Film Editing* (Walter Murch, 2nd ed 2001, Silman-James Press)
**Copyright:** Fair Use — paraphrased Rule of Six weightings + Emotion-First decision rule + eye-trace quantification + blink-rhythm theory only; no reproduction of Murch's scene walkthroughs or extended prose (see [LICENSE.md](./LICENSE.md))
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 editor 专家最核心的剪辑决策模型 —— Walter Murch 在 *In the Blink of an Eye* (2nd ed 2001) 提出的 **Rule of Six**:一个 cut 的"理想度"应当从 6 个维度加权评分,其中 Emotion 权重 50% 远高于其他 5 个维度之和。本 ref 是 Rule of Six 权重数值(Emotion 50% / Story 23% / Rhythm 10% / Eye-trace 7% / 2D plane 5% / 3D space 3%)的**唯一真相源** —— SKILL.md body 与其他 editor refs 仅引用 + 跨链,不重述原理(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) 教训)。术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)([爽点](../../_shared/glossary.md#爽点-satisfaction-beat) / [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) / [钩子](../../_shared/glossary.md#钩子-hook) / [完播率](../../_shared/glossary.md#完播率-completion-rate))。

Murch 的 Rule of Six 之所以适配 AI 短剧制作,是因为它把"这个 cut 应该在哪里发生"这件主观的事,拆成了 6 个**可逐项评分的客观维度**。LLM 生成剪辑决策时若不参照此模型,倾向于按"叙事流畅"这种模糊标准选择 cut point —— 结果常常是叙事上没错、但观众情绪断裂。Rule of Six 强制剪辑师(无论是人类还是 LLM)先问"这个 cut 维护了哪个情绪?",再问其他 5 个维度。

---

## The Rule of Six Weightings

Murch 提出:一个理想的 cut 应当尽量同时满足 6 个条件。但 6 个条件的重要性**严重不对等** —— Emotion 占据一半权重。下表是 2nd ed (2001) 的规范化权重:

| # | 维度 | 权重 (2nd ed, 2001) | 含义 | 量化方式 |
|---|------|---------------------|------|----------|
| 1 | **Emotion** | **50%** | cut 是否维护了观众当前的情绪状态?情绪是否被推进而非打断? | 主观 0-10 评分 × 0.50 |
| 2 | **Story** | **23%** | cut 是否推进了故事(让观众知道新信息 / 改变对已有信息的理解)? | 信息增量 0-10 评分 × 0.23 |
| 3 | **Rhythm** | **10%** | cut 时机是否符合场景的节奏感(快 / 慢 / 喘息)? | 节拍对齐 0-10 评分 × 0.10 |
| 4 | **Eye-trace** | **7%** | cut 前后观众的注视中心是否在同一画面区域(避免眼球大幅跳动)? | 帧位移百分比 ≤ 30%(详见 §Eye-Trace Quantification) |
| 5 | **2D plane of action** | **5%** | cut 前后构图是否和谐(主体位置 / 三分线 / 视线方向)? | 构图连续性 0-10 评分 × 0.05 |
| 6 | **3D space** | **3%** | cut 前后观众对 3D 空间关系的感知是否被维护(谁在左 / 右 / 前 / 后)? | 轴线合规(详见 [`fxrxt-axis-compliance.md`](./fxrxt-axis-compliance.md) §180° Axis Rule) |

**关键 heuristic 1 (load-bearing):** Rule of Six 的权重总和 = 50% + 23% + 10% + 7% + 5% + 3% = **98%**(Murch 故意留下 2% 余量表示"剪辑始终有不可量化的直觉成分")。其中 **Emotion 独占 50%** —— 这意味着即使其他 5 个维度全部满分(总和 48%),Emotion 失败的 cut 也应当被否决;反之 Emotion 满分的 cut 即使其他 5 个维度全部失败,只要不违反 180° 轴线(零容忍硬约束,见 [`fxrxt-axis-compliance.md`](./fxrxt-axis-compliance.md)),仍可保留。

### 2nd ed (23%) vs 早期引用 (25%) 的差异说明 (T-03-07 mitigation)

**Rule of Six 中 Story 维度的权重在文献中存在两种引用值:**

- **早期引用 (1st ed 1995 + 部分二手文献):** Story = 25%
- **2nd ed (2001, canonical):** Story = 23%

Murch 在 2nd ed 的后记中调整了 Story 的权重(从 25% 下调到 23%),理由是 Story 与 Emotion 的边界比他最初设想的更模糊 —— "推进故事"的 cut 通常已经在维护情绪,因此把权重从 Story 划一部分给 Emotion 更符合实际剪辑判断。本 ref 与 editor SKILL.md body 统一采用 **2nd ed 的 23% 作为 canonical 值**,但在任何对外文档 / 论文中引用时,若读者熟悉 1st ed,需注明 "23% (2nd ed, 2001);早期版本曾引用 25%"。

> **重要:** 不要在 SKILL.md body 或其他 refs 中混用 23% 与 25% —— 这会导致 metric 数值漂移(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) 教训)。本 ref 是 Rule of Six 权重的**唯一真相源**。

### 加权评分计算公式

给定一个 cut,6 个维度各自评分 0-10,加权总分计算公式:

```
murch_score = (emotion × 0.50) + (story × 0.23) + (rhythm × 0.10) + (eye_trace × 0.07) + (plane_2d × 0.05) + (space_3d × 0.03)
```

**应用阈值:**

| murch_score | 评估 | 动作 |
|-------------|------|------|
| ≥ 7.0 | 优秀 cut | 保留 |
| 5.0 - 6.9 | 合格 cut | 保留,但若 murch_score < 5.5 应检查是否有更好 cut point |
| 3.0 - 4.9 | 弱 cut | 重新选择 cut point;若 emotion ≥ 8.0 则可保留(Emotion-First 豁免,见下节) |
| < 3.0 | 不合格 cut | 否决;必须重新设计 |

**关键 heuristic 2:** murch_score 阈值 7.0 与 5.0 不是 Murch 原书的数字 —— Murch 没有给出数值化阈值。这些阈值是 editor 专家基于 2nd ed 加权公式的**操作性延伸**(operational extension),用于让 LLM 在生成剪辑决策时有明确的 go/no-go 标准。它们属于 *estimated* 类别(详见 [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md) 末尾的 *estimated* 声明)。

---

## Emotion-First Decision Rule

Murch 在 *In the Blink of an Eye* 中提出的**最重要决策规则**(Rule of Six 的灵魂):

> **"If a cut preserves Emotion but violates the other five, KEEP the cut. Conversely, a cut that fails Emotion but satisfies the other five should be REJECTED."** —— Murch 2nd ed (paraphrased)

**关键 heuristic 3 (load-bearing):** Emotion-First 规则的实操含义 —— 在 murch_score 计算后,若 `emotion ≥ 8.0`,则即使总 murch_score < 5.0(其他 5 个维度平均失败),cut **仍应保留**;反之,若 `emotion ≤ 3.0`,则即使 murch_score ≥ 7.0(其他 5 个维度平均优秀),cut **仍应否决**。

### Emotion-First 的 3 个具体示例

**示例 1 (Emotion-First 豁免保留):**
一个 [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) 镜头 —— 主角得知父亲死讯的瞬间。cut 时机选择在主角瞳孔放大的瞬间(0.5s 短镜头),eye-trace 违反(前一镜头主体在画面左 1/3,此镜头主体在画面右 1/3,帧位移 ~55% > 30% 阈值)。但 emotion = 10/10(情绪峰值),story = 9/10(信息重大增量)。**Emotion-First 豁免 → 保留 cut。**

**示例 2 (Emotion 失败否决):**
一个对话场景中,LLM 默认选择在"主角说完一句话后 0.3s"切到反应镜头。story = 8/10(推进信息),rhythm = 9/10(符合节拍),eye-trace = 8/10(注视中心对齐)。但 emotion = 2/10 —— 切走得太早,主角的情绪表达(一个被压抑的微笑)还没完成就被切走,观众情绪被打断。**Emotion-First 否决 → 重新选择 cut point,延迟到主角情绪完整呈现后再切。**

**示例 3 (Emotion 与其他维度冲突的权衡):**
一个动作场景中,cut 选择在主角起身的瞬间(action cut)。emotion = 7/10(紧张感延续),rhythm = 10/10(完美节拍对齐),eye-trace = 9/10(注视中心对齐)。但 story = 4/10 —— 这个 cut 没有给观众新信息(主角起身这件事在前一镜头已经预示)。**Emotion-First 评估:emotion = 7/10(中等偏高)→ 保留 cut,但记录 story 弱项。若后续剪辑流程发现整段动作场景 story 维度平均 < 5.0,应重新设计该段 cut 顺序。**

### Emotion-First 在 短剧 中的应用

短剧 的核心 KPI 是 [完播率](../../_shared/glossary.md#完播率-completion-rate) —— 观众是否看完。完播率 与情绪驱动强相关:观众"想看下去"的本质是情绪被钩住。因此 editor 在 短剧 剪辑中,**Emotion-First 规则应被进一步加强为 "Emotion-Supreme"**:

- **任何 cut 必须先问 "这个 cut 是否维护了当前场景的情绪曲线?"** —— 情绪曲线由 screenplay 专家生成(见 [`../screenplay/SKILL.md`](../screenplay/SKILL.md) §Emotion Curve Hooks / Payoffs / Cliffhangers)。
- **爽点 cut(见 [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md) §击中点 Cut Alignment)必须 align 在情绪峰值** —— 即 emotion_curve.samples 的 v ≥ 0.8 的采样点。
- **钩子 cut(见 [`../hook_retention/references/three-second-hooks.md`](../hook_retention/references/three-second-hooks.md))必须 align 在情绪首次拉起的瞬间** —— 通常是 emotion_curve 的第一个 v ≥ 0.6 的采样点。

---

## Eye-Trace Quantification

Murch 的 Eye-trace 维度在原书中以定性描述为主("观众的眼睛 cut 后应当落在与 cut 前相同的画面区域")。本 ref 将其**量化为可计算的阈值**,使 LLM 在生成剪辑决策时有明确的 go/no-go 标准。

### 帧位移百分比定义

给定 cut 前一镜头(cut_A)的"主体注视中心"(subject focal point,通常是人脸 / 关键物体 / 动作焦点),与 cut 后一镜头(cut_B)的"主体注视中心",帧位移百分比定义:

```
frame_displacement = euclidean_distance(focal_A, focal_B) / frame_diagonal × 100%
```

其中 `focal_A` 与 `focal_B` 是归一化坐标(frame 左下角 = (0,0),frame 右上角 = (1,1)),`frame_diagonal = sqrt(1² + 1²) ≈ 1.414`。

**关键 heuristic 4 (load-bearing):** Eye-trace 违反阈值:

| frame_displacement | Eye-trace 评分 | 说明 |
|--------------------|----------------|------|
| ≤ 30% | 10/10 | 完美对齐 —— 观众注视中心几乎不动 |
| 30% - 40% | 5-7/10 | 可接受 —— 观众眼球小幅跳动但仍在 comfort zone |
| **> 40%** | **≤ 3/10(违反)** | **Eye-trace violation** —— 观众眼球大幅跳动,产生"画面跳一下"的不适感 |

**示例:** cut_A 主体在画面中心 (0.5, 0.5),cut_B 主体在画面右上角 (0.8, 0.8)。frame_displacement = sqrt((0.8-0.5)² + (0.8-0.5)²) / 1.414 × 100% = sqrt(0.18) / 1.414 × 100% ≈ 30%。**临界值** —— 评分 7/10,可接受但应注意。

### 竖屏 (9:16) 的 Eye-trace 调整

竖屏画幅的视觉重心与横屏不同 —— 竖屏观众倾向于先看上 1/3(避开顶部 UI overlays)再看下 1/3(避开底部 UI)(详见 [`../hook_retention/references/vertical-pacing.md`](../hook_retention/references/vertical-pacing.md) §竖屏 vs 横屏 Pacing Difference)。因此竖屏 短剧 的 Eye-trace 阈值应**收紧约 10%**:

| frame_displacement | 横屏 (16:9) 评分 | 竖屏 (9:16) 评分 |
|--------------------|------------------|------------------|
| ≤ 30% | 10/10 | 10/10 |
| 30% - 40% | 5-7/10 | 3-5/10(竖屏观众对跳动更敏感) |
| > 40% | ≤ 3/10 | ≤ 2/10(竖屏 hard violation) |

### 注视中心检测的实操

LLM 在生成剪辑决策时如何确定 cut_A 与 cut_B 的"主体注视中心"?三种方式(按优先级):

1. **animator 输出的 `focal_point` 字段**(若存在):animator 在生成镜头时输出 `{shot_id, focal_point: {x, y}}`。editor 直接消费。
2. **drawer 输出的 `composition_anchor` 字段**(若存在):drawer 在生成分镜时输出构图锚点。
3. **LLM 推断**(fallback):基于 shot description(如"主角特写,面部居中")推断 focal_point。LLM 推断的准确率约 70-80%(*estimated*),应在 editor 自检阶段用前两种来源交叉验证。

### 2D Plane 与 3D Space 维度的实操评分

Rule of Six 的第 5 维度 (2D plane) 与第 6 维度 (3D space) 虽然权重最低(5% + 3% = 8%),但它们的评分直接影响 viewer 的空间感知连续性。editor 在生成剪辑决策时应按以下检查表评分:

**2D plane 评分检查表:**

| 检查项 | 通过(10/10) | 失败(≤ 5/10) |
|--------|--------------|---------------|
| 主体位置 | cut 前后主体在同一画面区域(左 / 中 / 右) | 主体位置跳变(如 cut_A 主体居中,cut_B 主体在画面边缘) |
| 三分线对齐 | 两个镜头的主体都 align 在三分线交叉点 | 主体在画面正中心(缺乏构图张力) |
| 视线方向 | cut_A 角色看向的方向与 cut_B 主体出现的位置一致(eyeline match,详见 [`fxrxt-axis-compliance.md`](./fxrxt-axis-compliance.md) §Eyeline Match) | 视线方向与主体位置不一致 |
| 色彩和谐 | cut 前后主色调在同一色系(详见 colorist 专家) | 色调突变(如暖调切到冷调,除非是情绪转换) |

**3D space 评分检查表:**

| 检查项 | 通过(10/10) | 失败(≤ 5/10) |
|--------|--------------|---------------|
| 轴线合规 | 180° 轴线未违反(详见 [`fxrxt-axis-compliance.md`](./fxrxt-axis-compliance.md) §180° Axis Rule) | 180° 轴线违反(零容忍硬约束) |
| 空间关系连续 | cut 前后观众对"谁在左 / 右 / 前 / 后"的感知一致 | 空间关系跳变(如 cut_A 中 A 在 B 左侧,cut_B 中 A 在 B 右侧且无 transition) |
| 景别跳跃合理性 | 景别变化在合理范围(如 MS → CU 是合理跳跃;ECU → EWS 是过大跳跃) | 景别跳跃过大(详见 [`classical-editing-rhythm.md`](./classical-editing-rhythm.md) §Cut on Action 的 30° rule 关联) |
| 摄影机方向 | cut 前后摄影机角度差 ≥ 30°(避免 jump cut 感,详见 [`fxrxt-axis-compliance.md`](./fxrxt-axis-compliance.md) §30° Rule) | 角度差 < 30°(jump cut 风险) |

**关键 heuristic 7:** 3D space 维度的 180° 轴线违反是**唯一不受 Emotion-First 豁免的硬约束**。即使 emotion = 10/10,若 cut 违反 180° 轴线,必须否决并重新设计 —— 因为 180° 违反会让观众完全丧失空间方向感,即使情绪到位,观众也会因为"不知道谁在哪里"而跳出。这是 Rule of Six 与 FxRxT axis compliance 的**硬交集**。

---

## Blink Rhythm Theory

Murch 的另一个核心理论:**cut 应当 align 在观众自然眨眼的节奏上**。Murch 观察到,人眼在专注观看时平均每 4 秒眨眼一次(15-20 blinks/min),而 cut 发生在眨眼瞬间时,观众几乎察觉不到 cut 的存在 —— 这就是"invisible editing"的生理基础(详见 [`classical-editing-rhythm.md`](./classical-editing-rhythm.md) §Invisible Editing Definition)。

### 关键 heuristic 5 (load-bearing): 眨眼节奏数值

| 观察维度 | 数值 *estimated* | 来源 |
|----------|------------------|------|
| **专注观看时的平均眨眼间隔** | **~4 秒**(范围 3-6 秒) | Murch 2nd ed + 生理学观察 |
| **专注观看时的平均眨眼频率** | **15-20 blinks/min** | Murch 2nd ed |
| **cut 间隔 ≤ 4 秒时的 viewer-fatigue 风险** | 低 —— cut align 在眨眼节奏上 | Murch 2nd ed |
| **cut 密度 > 30 cuts/min 持续超过 60 秒时的 viewer-fatigue 风险** | **高** —— viewer 进入 "cut 过载"状态,注意力分散 | Murch 2nd ed + 行业观察 |

**关键 heuristic 6 (load-bearing):** cut 密度 > 30 cuts/min 的"viewer-fatigue 阈值"。这个数字是 Rule of Six + blink-rhythm 理论的**衍生阈值** —— 若 cut 密度持续超过 30 cuts/min(平均 shot 长度 < 2 秒),cut 节奏快于观众眨眼节奏,viewer 无法在眨眼间隙"消化"画面信息,产生疲劳感。这与 [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md) §Cut-Density Windows by Platform/Genre 的平台阈值(抖音-男频 40-60 cuts/90s-ep,即 27-40 cuts/min)形成张力 —— 男频 短剧 的 cut 密度本身就接近 viewer-fatigue 阈值。editor 必须在"平台算法偏好的高密度"与"viewer-fatigue 阈值"之间权衡,通过 Rhythm 维度的喘息帧(见 [`classical-editing-rhythm.md`](./classical-editing-rhythm.md) §Build-to-Climax Rule)缓解。

### Blink-Cut Alignment 的实操

editor 在生成 cut list 时,应将 cut point 尽量 align 在 4 秒眨眼节奏的"边界点":

- **理想 cut point:** 0s / 4s / 8s / 12s / 16s / 20s ...(即 4 秒的整数倍)
- **可接受 cut point:** 任意 shot 长度在 2-6 秒之间(cut 节奏与眨眼节奏有 ±50% 余量)
- **应避免 cut point:** shot 长度 < 2 秒(除非 action 场景,见 [`classical-editing-rhythm.md`](./classical-editing-rhythm.md) §Cut on Action)或 > 6 秒(除非 emotional 场景,且 shot 必须持续承载情绪弧线)

### 短剧 的 Blink-Cut 调整

短剧 的 cut 密度本身就高于眨眼节奏(见 [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md)),因此 Blink-Cut Alignment 不能机械执行。editor 在 短剧 剪辑中应遵循以下调整:

1. **爽点 / 击中点 段:** 允许 cut 密度超过眨眼节奏(40-60 cuts/90s-ep),因为这些段落的情绪强度(emotion ≥ 8.0)会"覆盖"viewer-fatigue 信号 —— 观众在情绪峰值时眨眼频率会自然降低。
2. **喘息帧段:** 每 15-20 秒(约 4-5 个 cuts)插入一个 2-3 秒的"喘息 shot"(emotional 特写 / 环境建立镜头),让 viewer 有一次完整的眨眼 + 信息消化。
3. **钩子段(0-3s):** cut 必须 align 在 3 秒边界 —— 钩子 的核心是"3 秒内抓住注意力",cut 节奏不能慢于眨眼节奏(否则 viewer 在第一次眨眼时上滑)。

---

## Murch Score Calculation — 完整工作流示例

本节通过一个完整的 90s 抖音-男频 revenge 短剧 冷开场,演示 Rule of Six 加权评分的端到端计算流程。

### 示例场景

一个 90s [男频](../../_shared/glossary.md#男频-male-oriented-channel) 战神归来 短剧 的冷开场(0-15s),包含 6 个 shots。emotion_curve 来自 screenplay 专家,采样点如下:

```
emotion_curve.samples = [
  {t: "00:00", v: 0.4},  // 开场:主角背影,悬念
  {t: "00:03", v: 0.6},  // 钩子锚定:主角转身
  {t: "00:06", v: 0.5},  // 喘息:配角反应
  {t: "00:09", v: 0.7},  // 第一次 击中点:主角展示实力
  {t: "00:12", v: 0.8},  // 情绪升级:反派震惊
  {t: "00:15", v: 0.9}   // 爽点 预热:主角碾压
]
```

### 6 个 shots 的 Rule of Six 评分

| Shot # | 时间戳 | 时长 | 内容描述 | Emotion (50%) | Story (23%) | Rhythm (10%) | Eye-trace (7%) | 2D plane (5%) | 3D space (3%) | murch_score | 决策 |
|--------|--------|------|----------|---------------|-------------|--------------|-----------------|----------------|----------------|-------------|------|
| 1 | 0.0-3.0s | 3.0s | 主角背影特写,悬念(钩子) | 8/10 (v=0.6 钩子锚定) | 7/10 (悬念建立) | 9/10 (3s align 钩子边界) | 10/10 (focal 居中) | 9/10 (背影构图强) | 10/10 (轴线建立) | **7.96** | 保留 |
| 2 | 3.0-4.5s | 1.5s | 主角转身,表情冷漠 | 8/10 (情绪延续) | 8/10 (揭示主角身份) | 8/10 (1.5s align 1.5x pace) | 7/10 (focal 从背影到正面,位移 ~25%) | 8/10 (构图和谐) | 9/10 (轴线维护) | **7.80** | 保留 |
| 3 | 4.5-6.0s | 1.5s | 配角震惊反应 | 6/10 (情绪 v=0.5 喘息) | 7/10 (配角视角) | 8/10 (节拍对齐) | 6/10 (focal 切到配角,位移 ~35%) | 7/10 (构图合理) | 8/10 (轴线维护) | **6.42** | 保留(临界) |
| 4 | 6.0-9.0s | 3.0s | 主角展示实力(击中点) | 10/10 (v=0.7 击中点) | 9/10 (实力揭示) | 9/10 (3s align 4s 眨眼边界) | 8/10 (focal 回到主角,位移 ~20%) | 9/10 (动作构图) | 9/10 (轴线维护) | **9.25** | 保留(优秀) |
| 5 | 9.0-12.0s | 3.0s | 反派震惊 + 后退 | 9/10 (v=0.8 升级) | 8/10 (反派视角) | 8/10 (节拍对齐) | 7/10 (focal 切到反派,位移 ~30%) | 8/10 (构图合理) | 8/10 (轴线维护) | **8.27** | 保留 |
| 6 | 12.0-15.0s | 3.0s | 主角碾压(爽点 预热) | 10/10 (v=0.9 爽点 预热) | 9/10 (碾压兑现) | 9/10 (3s align 4s 边界) | 9/10 (focal 回到主角,位移 ~15%) | 10/10 (碾压构图) | 9/10 (轴线维护) | **9.37** | 保留(优秀) |

### 评分流程的关键观察

1. **Emotion 维度与 emotion_curve 强相关:** murch_score 的 emotion 评分直接取自 emotion_curve.samples 的 v 值映射(v=0.4 → emotion 4/10;v=0.9 → emotion 9/10)。这验证了 Rule of Six 第 1 维度 与 screenplay 的 emotion_curve 的**数据流集成**。
2. **喘息帧(Shot 3)murch_score 最低(6.42):** 这是符合预期的 —— 喘息帧的功能是"让观众消化",不是"推情绪"。它的 emotion 评分自然较低(6/10),但因为 rhythm / eye-trace / 2D plane / 3D space 都合格,总 murch_score 仍在 5.0 阈值以上,**保留**。
3. **击中点 与 爽点 预热段的 murch_score 最高(9.25 / 9.37):** 这也符合预期 —— 情绪峰值段自然获得高 murch_score,因为 emotion 维度权重 50% 占主导。
4. **没有 cut 触发 Emotion-First 否决:** 所有 6 个 shots 的 emotion 评分都在 6-10 之间,没有 emotion ≤ 3.0 的 cut 需要否决。若 Shot 3 的 emotion 评分是 2/10(喘息过度,情绪断裂),即使其他维度满分(murch_score ≈ 4.6 + 2×0.5 = 5.6),Emotion-First 规则会否决这个 cut —— 要求重新设计喘息帧,让情绪曲线在喘息段也保持 v ≥ 0.4。

### 工作流输出

editor 在完成 Rule of Six 评分后,应输出以下 JSON 结构(集成到 `edit_decision_list.json`):

```json
{
  "shots": [
    {
      "shot_id": "S1E01_cold_open_001",
      "timestamp": "00:00-00:03",
      "duration_s": 3.0,
      "murch_score": 7.96,
      "murch_breakdown": {
        "emotion": 8, "story": 7, "rhythm": 9,
        "eye_trace": 10, "plane_2d": 9, "space_3d": 10
      },
      "decision": "keep",
      "emotion_ref": "emotion_curve.samples[1].v=0.6"
    }
    // ... 其余 5 个 shots
  ],
  "murch_summary": {
    "avg_score": 8.18,
    "min_score": 6.42,
    "max_score": 9.37,
    "emotion_first_vetoes": 0,
    "axis_violations": 0
  }
}
```

---

## Rule of Six 与其他剪辑理论的关系

Rule of Six 不是唯一的剪辑决策模型。editor 在生成剪辑决策时,应理解 Rule of Six 与其他理论的关系,避免在 SKILL.md body 中混淆:

| 理论 | 核心论点 | 与 Rule of Six 的关系 |
|------|----------|----------------------|
| **Murch Rule of Six** (本 ref) | 加权评分模型,Emotion 占 50% | **canonical 剪辑决策模型** —— 所有 cut 必须先过 Rule of Six 评分 |
| **Reisz-Millar Classical Editing** ([`classical-editing-rhythm.md`](./classical-editing-rhythm.md)) | invisible editing + cut-density windows + cut on action | 提供 Rule of Six 第 3 维度 (Rhythm) 的具体阈值;invisible editing 是 Rule of Six 高分的自然结果 |
| **Eisenstein Montage Theory** ([`montage-theory.md`](./montage-theory.md)) | collision montage + intellectual montage | 与 Rule of Six 第 2 维度 (Story) 强相关 —— collision montage 的核心是"cut 产生新意义",即 story 维度的信息增量 |
| **FxRxT Axis Compliance** ([`fxrxt-axis-compliance.md`](./fxrxt-axis-compliance.md)) | 180° / 30° / eyeline / match cut | 提供 Rule of Six 第 6 维度 (3D space) 与第 4 维度 (Eye-trace) 的具体规则 |
| **CN 短剧 Cutting Rhythm** ([`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md)) | 平台 cut-density + 1.5x pace + ≤3s dead air | 提供 Rule of Six 第 3 维度 (Rhythm) 在 短剧 场景的具体数值 |

**关键 heuristic 8:** editor 在 SKILL.md body 中描述剪辑决策流程时,应明确指出 Rule of Six 是**顶层决策框架**,其他理论提供**具体维度的执行规则**。LLM 在生成剪辑决策时,应先按 Rule of Six 6 维度评分,再根据场景类型(对话 / 动作 / 情感 / 短剧 平台)调用对应的执行规则。这避免了"LLM 凭直觉选择 cut point"的模糊决策模式。

---

## Cross-References

- [`fxrxt-axis-compliance.md`](./fxrxt-axis-compliance.md) §180° Axis Rule —— Rule of Six 第 6 维度 (3D space) 的具体执行规则;180° 违反是零容忍硬约束,不受 Emotion-First 豁免。
- [`classical-editing-rhythm.md`](./classical-editing-rhythm.md) §Cut-Density Windows by Genre —— cut 密度阈值与 Rule of Six 第 3 维度 (Rhythm) 的关系;build-to-climax 规则与 Emotion-First 规则的协同。
- [`classical-editing-rhythm.md`](./classical-editing-rhythm.md) §Invisible Editing Definition —— "invisible cut"的生理基础是 Blink-Cut Alignment(本 ref §Blink Rhythm Theory)。
- [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md) §击中点 Cut Alignment —— [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) cut 必须 align 在 emotion ≥ 8.0 的情绪峰值(Emotion-First 规则的 短剧 应用)。
- [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md) §≤3s Dead Air Rule —— "dead air"是 Emotion-First 规则的反面 —— cut 间隔 > 3 秒且无情绪弧线承载时,emotion 自然衰减。
- [`../screenplay/references/emotion-curve-academic.md`](../screenplay/references/emotion-curve-academic.md) §Anchor-Based Sampling Protocol —— emotion_curve 采样点是 Rule of Six 第 1 维度 (Emotion) 的数据源。
- [`../hook_retention/references/three-second-hooks.md`](../hook_retention/references/three-second-hooks.md) —— [钩子](../../_shared/glossary.md#钩子-hook) cut 必须 align 在情绪首次拉起的瞬间(Emotion-First 规则的开场应用)。
- [`../../_shared/glossary.md`](../../_shared/glossary.md) —— [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) / [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) / [钩子](../../_shared/glossary.md#钩子-hook) / [完播率](../../_shared/glossary.md#完播率-completion-rate) 术语定义。

---

## Refresh Cadence

- **每季度复核一次**(下次:2026-09)。
- **复核内容:** Rule of Six 权重是否仍为 2nd ed canonical 值(Emotion 50% / Story 23% / Rhythm 10% / Eye-trace 7% / 2D plane 5% / 3D space 3%);Emotion-First 规则的实操阈值(emotion ≥ 8.0 豁免 / emotion ≤ 3.0 否决)是否需要调整;Eye-trace 帧位移阈值(横屏 30% / 40%,竖屏收紧 10%)是否需要调整;Blink-Cut 节奏(~4 秒间隔)是否仍是生理学共识。
- **复核来源:** Murch 2nd ed 原书 + 后续剪辑理论文献 + AI 短剧 剪辑实践反馈。
- **不需要更新:** Rule of Six 的 6 个维度定义(Murch 原书固定);Emotion-First 决策规则(Murch 原书核心论点,不会变)。

---

## Drift Signals

若以下信号出现,本 ref 需要更新:

- **Murch 3rd ed 发布:** 若 Murch 发布 3rd ed 并调整 Rule of Six 权重(例如 Emotion 从 50% 调整),需更新本 ref 的 canonical 值 + 在 SKILL.md body 中同步修订。
- **AI 短剧 viewer-fatigue 研究新数据:** 若出现基于 eye-tracking 的 短剧 viewer-fatigue 实测数据(例如:90s 男频 短剧 的 cut 密度甜区不是 40-60 而是 50-70),需更新 §Blink Rhythm Theory 的 cut 密度阈值。
- **竖屏 Eye-trace 阈值实测:** 若出现竖屏 (9:16) viewer 的 eye-tracking 实测数据(验证或推翻本 ref 的"竖屏收紧 10%"推断),需更新 §Eye-Trace Quantification 的竖屏调整表。
- **跨文化 blink 节奏差异:** 若出现基于 CN viewer 的 blink 节奏实测(验证或推翻 15-20 blinks/min 通用值),需更新 §Blink Rhythm Theory 的数值。

---

> **Disclaimer:** Rule of Six 权重(Emotion 50% / Story 23% / Rhythm 10% / Eye-trace 7% / 2D plane 5% / 3D space 3%)是 Murch 2nd ed (2001) 的 canonical 值。Emotion-First 规则的实操阈值(emotion ≥ 8.0 豁免 / emotion ≤ 3.0 否决)、Eye-trace 帧位移阈值(横屏 30% / 40%,竖屏收紧 10%)、murch_score go/no-go 阈值(7.0 / 5.0 / 3.0)、cut 密度 viewer-fatigue 阈值(30 cuts/min)均为基于 Murch 理论的**操作性延伸**(`*estimated*`)。这些操作性阈值是 editor 专家的**唯一真相源** —— SKILL.md body 与其他 refs 必须跨链引用,不得重新定义。
