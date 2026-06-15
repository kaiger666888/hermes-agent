# FxRxT Axis Compliance — 180° / 30° / Eyeline / Match Cut 规则

**Source:** Classical film theory (180° / 30° rules — industry craft convention > 100 years old, public domain) + Hermes-existing FxRxT matrix convention (MIT-licensed Hermes Agent repo)
**Copyright:** Mixed — classical rules are public domain (industry craft convention); FxRxT matrix terminology is Hermes-internal (MIT, see top-level LICENSE; see [LICENSE.md](./LICENSE.md))
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 editor 专家的轴线合规规则 —— 180° 轴线规则、30° 规则、eyeline match、match cut 设计,以及这些规则如何集成到 editor 的 FxRxT 三维剪辑矩阵(F=Frame / R=Rhythm / T=Transition)。本 ref 是 180° / 30° / eyeline / match cut 的量化阈值(180° angle delta > 180° = 违反;30° angle delta < 30° = jump-cut 风险;eyeline direction mismatch > 45° = 违反)的**唯一真相源** —— SKILL.md body 与其他 editor refs 仅引用 + 跨链,不重述数值(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) 教训)。术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)([轴线](../../_shared/glossary.md#轴线-axis-line-180-rule-line) / [景别](../../_shared/glossary.md#景别-shot-size-shot-scale))。

这些规则之所以对 editor 专家至关重要,是因为它们是 Rule of Six 第 6 维度 (3D space) 与第 4 维度 (Eye-trace) 的**具体执行规则**(见 [`murch-rule-of-six.md`](./murch-rule-of-six.md) §2D Plane 与 3D Space 维度的实操评分)。180° 轴线违反是**唯一不受 Emotion-First 豁免的零容忍硬约束** —— 即使情绪完美,轴线违反也会让观众丧失方向感。

---

## 180° Axis Rule

180° 轴线规则(又称 "line of action" / "axis of action")是古典电影剪辑最基础的规则。它定义了场景中两个主体之间的"轴线",所有摄影机位置必须留在轴线的同一侧(180° 半圆内),以维护观众的方向感。

### 关键 heuristic 1 (load-bearing): 180° 轴线定义与违反阈值

> **场景中两个主体(通常是对话的两个人物)之间的连线定义了"轴线"。所有摄影机位置必须留在轴线的同一侧(180° 半圆内)。跨过轴线到另一侧 = 轴线违反(axis violation)。**

量化阈值:

| 维度 | 合规 | 违反 | 来源 |
|------|------|------|------|
| **摄影机角度差(相对轴线)** | ≤ 180°(留在同一侧) | **> 180°(跨过轴线)** | Classical film theory |
| **viewer 方向感** | 维持(角色 A 在左 / B 在右) | 混乱(A 与 B 左右对调) | 认知心理学 |

### 轴线违反的后果

轴线违反会让观众完全丧失方向感:

- cut_A 中角色 A 在画面左侧,B 在右侧。
- cut_B(轴线违反)中 A 突然在右侧,B 在左侧。
- viewer 大脑无法理解"为什么角色左右对调了" → 方向感崩溃 → 注意力分散 → 完播率 下降。

**关键 heuristic 2:** 180° 轴线违反是 editor 专家的**零容忍硬约束**(见 SKILL.md §Quality Thresholds: axis_violation_count = 0)。即使 Rule of Six 的 emotion = 10/10,轴线违反也必须否决并重新设计(见 [`murch-rule-of-six.md`](./murch-rule-of-six.md) §2D Plane 与 3D Space 维度的实操评分)。

### 轴线合规的修复策略

若 editor 在自检时发现轴线违反,有以下修复策略(按优先级):

| # | 修复策略 | 原理 | 适用场景 |
|---|----------|------|----------|
| 1 | **Neutral shot 过渡** | 插入一个正面 / 俯拍 / 全景 shot(不依赖轴线),作为"轴线重置点" | 最通用;几乎所有轴线违反都可用此修复 |
| 2 | **Dolly / tracking shot 过渡** | 用一个移动镜头从轴线一侧"移"到另一侧,viewer 跟随摄影机移动,方向感自然更新 | 适合有移动摄影机资源的场景 |
| 3 | **Cutaway(切出)** | 切到一个与环境 / 物体相关的 shot(无关轴线),再切回新角度 | 适合需要短暂离开主体的场景 |
| 4 | **重新设计轴线** | 修改 scene_builder 的轴线数据,让后续 shots 都 align 到新轴线 | 适合前期阶段(需要 scene_builder 协作) |

### 短剧 的轴线合规挑战

短剧 由于 cut 密度高(见 [`cn-cutting-rhythm.md`](./cn-cutting-rhythm.md)),轴线违反的风险更大 —— 高密度 cut 意味着更多摄影机角度切换,更容易不小心跨过轴线。editor 在 短剧 剪辑中应:

1. **优先消费 scene_builder 的 `axis_data` 字段**(若存在) —— scene_builder 预计算了场景的轴线定义。
2. **在 cut list 生成时自动检测轴线违反** —— 对每个 cut,计算 cut_A 与 cut_B 的摄影机角度差,若 > 180° 则标记为 axis violation。
3. **零容忍执行** —— axis_violation_count 必须 = 0(见 SKILL.md §Quality Thresholds);任何违反必须用上述修复策略解决。

---

## 30° Rule

30° 规则是 180° 规则的补充 —— 即使摄影机留在轴线同一侧,连续两个 cut 的摄影机角度差也不能太小(否则看起来像 jump cut)。

### 关键 heuristic 3 (load-bearing): 30° 规则定义与违反阈值

> **连续两个 cut 的摄影机角度(对同一主体)差必须 ≥ 30°。角度差 < 30° = jump-cut 风险。**

量化阈值:

| 维度 | 合规 | 违反 | 来源 |
|------|------|------|------|
| **摄影机角度差(连续 cuts,同一主体)** | **≥ 30°** | **< 30°** | Classical film theory |
| **viewer 感知** | 两个明显不同的视角 | "画面跳了一下"(jump cut 感) | 认知心理学 |

### 30° Rule 与 Jump Cut 的关系

Jump cut(跳切)是指两个角度差极小的 cut 连续出现,viewer 感觉"画面跳了一下"而不是"切换了视角"。这是 invisible editing 的失败模式之一(见 [`classical-editing-rhythm.md`](./classical-editing-rhythm.md) §Invisible Editing 的失败模式与诊断)。

**30° rule 的实操含义:**

- cut_A 是角色的正面特写(0°)。
- cut_B 必须是角度差 ≥ 30° 的镜头(如 30° 侧面特写 / 45° 侧面 / 90° 正侧面等)。
- cut_B 不能是角度差 < 30° 的镜头(如 10° 微侧面 —— viewer 感觉只是"画面晃了一下")。

### 30° Rule 的例外:Jump Cut 作为风格

Jump cut 在某些场景是**故意使用**的风格选择:

| 场景 | jump cut 的目的 | 是否允许 |
|------|----------------|----------|
| **时间跳跃(蒙太奇)** | 表示时间快速流逝 | 允许(配合 overtonal montage,见 [`montage-theory.md`](./montage-theory.md) §Overtonal Montage) |
| **角色心理混乱** | 表示角色精神状态不稳定 | 允许(需 emotion_curve 支撑) |
| **Godard 式作者风格** | 打破古典剪辑的"隐形"幻觉 | 允许(但 短剧 中少见) |
| **对话重复(同一主体同一角度)** | 表示角色在重复同一行为 | 允许(需明确叙事理由) |

editor 在应用 jump cut 时,必须在 cut list 中标注 `"jump_cut_intentional": true` + `"reason": "..."`,以便后续审计区分"故意 jump cut"与"30° rule 违反"。

---

## Eyeline Match

Eyeline match(视线匹配)是指 cut 前后角色的视线方向与新画面中主体出现的位置一致。

### 关键 heuristic 4 (load-bearing): Eyeline Match 定义与违反阈值

> **角色在 cut_A 中看向画外某方向(如左侧),cut_B 的主体应当出现在 cut_A 角色所看方向的位置(如画面右侧)。**

量化阈值:

| 维度 | 合规 | 违反 | 来源 |
|------|------|------|------|
| **eyeline 方向 vs 主体位置** | 方向一致(左看 → 右出) | **方向差 > 45°** | Classical film theory |
| **viewer 感知** | "角色在看 cut_B 的主体" | "角色在看错方向" | 认知心理学 |

### Eyeline Match 的三种典型场景

| 场景 | cut_A(看者) | cut_B(被看者) | eyeline 方向 |
|------|--------------|----------------|--------------|
| **对话(POV shot)** | 角色 A 看向画面左侧 | 角色 B 出现在画面右侧 | A 左看 → B 右出 |
| **物体关注** | 角色 A 看向画面下方 | 物体(如手机)出现在画面中央 | A 下看 → 物体出现 |
| **远景注视** | 角色 A 看向画面深处(远方) | 远景(如城市天际线) | A 深看 → 远景出现 |

### Eyeline Match 的违反修复

若 editor 发现 eyeline match 违反(方向差 > 45°),修复策略:

1. **调整 cut_B 的主体位置** —— 让主体出现在 cut_A 角色所看方向的位置(最直接修复)。
2. **水平镜像 cut_B**(flip horizontal) —— 让 cut_B 的构图左右翻转,匹配 cut_A 的 eyeline(需 animator / drawer 配合,不能在剪辑阶段单独翻转,因为会破坏文字 / 标志方向)。
3. **插入 POV shot** —— 在 cut_A 与 cut_B 之间插入一个"角色 A 视角"的 shot,明确 viewer 跟随 A 的视线(适合复杂场景)。

---

## Match Cut Design

Match cut(匹配剪辑)是指两个 shot 通过**视觉韵律**(visual rhyme)连接 —— 形状 / 动作 / 色彩的相似性让 cut 显得"自然",甚至产生隐喻效果。

### 关键 heuristic 5: Match Cut 的三种类型

| 类型 | 连接元素 | 经典示例 | 短剧 应用 |
|------|----------|----------|-----------|
| **Graphic match(图形匹配)** | 形状 / 构图相似 | *2001: A Space Odyssey* — 骨头 → 太空船(形状相似) | 场景转场:主角手中的酒杯 → 下一场景的圆形灯具 |
| **Motion match(动作匹配)** | 动作延续 / 相似 | 角色挥手 → 下一 shot 旗帜飘扬(动作延续) | 动作转场:主角推门 → 下一场景门打开 |
| **Sound match(声音匹配)** | 声音延续 / 相似 | cut_A 的火车汽笛 → cut_B 的茶壶哨声(声音相似) | 声音转场:cut_A 的雷声 → cut_B 的爆炸声 |

### Match Cut 在 短剧 的应用

短剧 由于 runtime 紧 + 场景切换多,match cut 是**高效的场景转场技巧** —— 它让 cut 显得自然,同时可能产生隐喻。editor 在 短剧 剪辑中应:

1. **标记 match cut 候选点** —— 在 cut list 生成时,检测 cut_A 与 cut_B 是否有形状 / 动作 / 色彩的相似性。
2. **优先在场景转换处使用 match cut** —— match cut 是 invisible editing 第 4 技巧(见 [`classical-editing-rhythm.md`](./classical-editing-rhythm.md) §Invisible Editing 的 5 个构成技巧),适合场景之间的平滑过渡。
3. **设计隐喻性 match cut** —— 在主题升华段(如 [男频](../../_shared/glossary.md#男频-male-oriented-channel) revenge 短剧 的反思结尾),用 graphic match 产生隐喻(如主角手中的剑 → 城市霓虹灯的剑形招牌)。

### Match Cut 的设计流程

editor 设计 match cut 的流程:

1. **识别 cut_A 的"视觉锚点"** —— 主体形状 / 动作终点 / 主色调(如"主角手中的红色酒杯,圆形")。
2. **在 cut_B 中寻找匹配元素** —— 相似形状 / 相似动作 / 相似色彩(如"下一场景的红色圆形灯具")。
3. **调整 cut 时机** —— 让 cut 发生在 cut_A 视觉锚点最清晰的瞬间 + cut_B 匹配元素出现的瞬间。
4. **验证 match 的"明显度"** —— match cut 的视觉效果依赖于匹配的明显度;若匹配太微妙,viewer 可能察觉不到(失去 invisible editing 效果);若匹配太刻意,viewer 会感觉"做作"。

### Match Cut 的 3 个 短剧 经典应用

| # | 场景 | cut_A | cut_B | match 类型 | 效果 |
|---|------|-------|-------|------------|------|
| 1 | **场景转场(回忆 → 现在)** | 主角手中的旧照片(矩形) | 现实中的窗户(矩形) | Graphic match | 时间跨越感;照片与窗户的形状相似暗示"回忆照进现实" |
| 2 | **动作延续(追逐段)** | 主角推开大门(手向前推) | 反派撞开另一扇门(身体向前冲) | Motion match | 动作延续感;两个"向前推/冲"的动作匹配,让 cut 隐形 |
| 3 | **主题升华(爽点 结尾)** | 主角手中的剑(竖直线条) | 城市天际线的剑形霓虹招牌(竖直线条) | Graphic match + 隐喻 | 隐喻效果;主角的"剑"扩大为城市的"剑",暗示主角已成为城市的主宰 |

**关键 heuristic 5b:** Match cut 在 短剧 中的应用频率应当**克制** —— 不是每个场景转换都需要 match cut。过度使用会让 viewer 感觉"每个 cut 都在炫技",反而破坏 invisible editing 的"故事流动感"。建议每集 90s 短剧 最多 1-2 个明显的 match cut(作为"亮点"),其余场景转换用常规 cut on action / cut on eyeline。

---

## FxRxT Integration — 轴线合规在 FxRxT 矩阵中的位置

FxRxT 是 editor 专家的核心剪辑矩阵:F=Frame(景别)/ R=Rhythm(节奏)/ T=Transition(转场)。本节明确轴线合规规则在 FxRxT 矩阵中的位置与边界。

### FxRxT 三维的定义

| 维度 | 含义 | 典型值 |
|------|------|--------|
| **F (Frame)** | 景别(详见 [`../../_shared/glossary.md`](../../_shared/glossary.md#景别-shot-size-shot-scale)) | ECU / CU / MS / MLS / WS / EWS / POV / OTS |
| **R (Rhythm)** | 节奏模式 | static / gradual / accelerating / decelerating / jump_cut |
| **T (Transition)** | 转场模式 | cut / dissolve / overlap / wipe / match_cut |

### 关键 heuristic 6 (load-bearing): editor 与 scene_builder 的轴线责任边界

轴线合规的责任在 editor 与 scene_builder 之间有明确分工:

| 专家 | 轴线责任 | 阶段 |
|------|----------|------|
| **scene_builder** | **feasibility(可行性)** —— 场景的轴线是否在物理 / 空间上可拍?摄影机位置是否合理? | 前期(场景设计) |
| **editor** | **compliance(合规)** —— 实际 cut 是否违反 180° / 30° / eyeline 规则?cut 顺序是否维护方向感? | 后期(剪辑) |

**边界说明:** scene_builder 提供 `axis_data`(场景的轴线定义 + 摄影机位置的可行性验证);editor 消费 `axis_data`,在 cut list 生成时验证每个 cut 的轴线合规。若 scene_builder 的 `axis_data` 缺失或错误,editor 应在自检阶段报告 `axis_data_missing` warning,但**不承担 scene_builder 的可行性责任**。

### FxRxT 矩阵中轴线合规的执行点

轴线合规在 FxRxT 矩阵的三个维度都有执行点:

| 维度 | 轴线合规执行点 | 违反示例 |
|------|----------------|----------|
| **F (Frame)** | 景别切换时,主体位置应 maintain 方向感 | cut_A MS(主角在左)→ cut_B CU(主角突然在右)= eyeline 风险 |
| **R (Rhythm)** | jump_cut 节奏(连续快速 cut)容易触发 30° 违反 | 连续 5 个 cuts 角度差 < 30° = 30° rule 违反 |
| **T (Transition)** | match_cut 转场需要验证 eyeline match | cut_A 角色看向左 → cut_B match_cut 主体在左 = eyeline 违反(应主体在右) |

editor 在 FxRxT 矩阵的每个维度都应执行轴线合规检查,输出 `axis_check_report`(见 SKILL.md §Output Format)。

### Axis Compliance 自检工作流

editor 在完成 cut list 生成后,应执行以下轴线合规自检流程:

```
对每个 cut (cut_A → cut_B):
  1. 加载 cut_A.camera_angle + cut_B.camera_angle(来自 scene_builder.axis_data)
     └── 若 axis_data 缺失 → 报告 axis_data_missing warning,跳过后续检查(LLM 推断)
  2. 计算 angle_delta = |cut_B.camera_angle - cut_A.camera_angle|
     ├── 若 angle_delta > 180° → 标记 AXIS_VIOLATION_180 (零容忍,必须修复)
     ├── 若 angle_delta < 30° → 标记 JUMP_CUT_RISK_30 (除非 jump_cut_intentional=true)
     └── 否则 → 轴线合规 PASS
  3. 加载 cut_A.eyeline_direction + cut_B.subject_position
     └── 若 eyeline vs subject 方向差 > 45° → 标记 EYELINE_MISMATCH
  4. 若 cut.transition == match_cut:
     └── 验证 match 元素(形状 / 动作 / 色彩)存在,否则标记 MATCH_CUT_WEAK
  5. 累计 axis_violation_count (180° + 30° + eyeline violations 总和)
     └── 若 axis_violation_count > 0 → 自检 FAIL,返回修复
```

**自检输出 JSON 示例:**

```json
{
  "axis_check_report": {
    "total_cuts_checked": 45,
    "axis_violations_180": 0,
    "jump_cut_risks_30": 1,
    "eyeline_mismatches": 0,
    "match_cut_weak": 0,
    "axis_violation_count": 1,
    "status": "FAIL",
    "violations": [
      {
        "cut_pair": ["shot_012", "shot_013"],
        "type": "JUMP_CUT_RISK_30",
        "angle_delta": 18.5,
        "fix_recommendation": "Insert neutral shot (frontal) between shot_012 and shot_013, or adjust shot_013 camera angle to >= 30° delta"
      }
    ]
  }
}
```

**关键 heuristic 7:** axis_violation_count 必须 = 0 才能通过 SKILL.md §Quality Thresholds 的 production gate。这意味着 180° violations + 30° violations + eyeline violations 三类都必须为 0。jump_cut_risks_30 若有 `jump_cut_intentional=true` 标注则不计入 violation_count(允许作为风格选择)。

---

## Cross-References

本 ref 与其他 editor refs 的关系:

- [`murch-rule-of-six.md`](./murch-rule-of-six.md) §2D Plane 与 3D Space 维度的实操评分 —— 180° 轴线违反是 Rule of Six 第 6 维度的零容忍硬约束;30° rule 与第 5 维度 (2D plane) 相关。
- [`murch-rule-of-six.md`](./murch-rule-of-six.md) §Eye-Trace Quantification —— eyeline match 与 eye-trace 帧位移相关;eyeline 违反通常伴随 eye-trace 违反。
- [`murch-rule-of-six.md`](./murch-rule-of-six.md) §Emotion-First Decision Rule —— 180° 轴线违反是唯一不受 Emotion-First 豁免的硬约束(emotion = 10/10 也必须否决)。
- [`classical-editing-rhythm.md`](./classical-editing-rhythm.md) §Invisible Editing 的失败模式与诊断 —— jump cut + axis violation + eyeline mismatch 是 invisible editing 的技术性失败模式。
- [`classical-editing-rhythm.md`](./classical-editing-rhythm.md) §Cut on Action —— cut on action 是避免 visible cut 的技巧,与 30° rule 协同。
- [`montage-theory.md`](./montage-theory.md) §Tonal Montage —— match cut 是 tonal montage 的一种特殊形式(视觉韵律连接)。
- [`../scene_builder/SKILL.md`](../scene_builder/SKILL.md) —— scene_builder 负责 axis feasibility;editor 负责 axis compliance。
- [`../../_shared/glossary.md`](../../_shared/glossary.md) —— [轴线](../../_shared/glossary.md#轴线-axis-line-180-rule-line) / [景别](../../_shared/glossary.md#景别-shot-size-shot-scale) / [视角](../../_shared/glossary.md#视角-angle-camera-angle) 术语定义。

---

## Refresh Cadence

- **每季度复核一次**(下次:2026-09)。
- **复核内容:** 180° / 30° / eyeline 的量化阈值(> 180° / < 30° / > 45°)是否仍是古典剪辑的 canonical 标准;match cut 的三种类型分类是否仍是主流;editor 与 scene_builder 的责任边界是否需要调整(若 scene_builder 输出的 `axis_data` 字段 schema 变化)。
- **复核来源:** Classical film theory 教材(如 Bordwell / Thompson *Film Art*)+ Hermes Agent scene_builder / editor 的实践反馈。
- **不需要更新:** 180° / 30° / eyeline 规则的定义(> 100 年的行业共识);match cut 的核心原理(视觉韵律连接)。

---

## Drift Signals

若以下信号出现,本 ref 需要更新:

- **竖屏轴线规则调整:** 若出现基于竖屏 (9:16) 的轴线规则研究(验证或推翻"竖屏 viewer 对 180° 违反更敏感 / 更不敏感"),需更新 §180° Axis Rule 的竖屏调整。
- **AI 生成内容的轴线挑战:** 若 AI 生成的镜头缺乏"轴线感知"(animator 不输出 `axis_data`),需补充 fallback 规则(如何用 LLM 推断轴线)。
- **match cut 自动检测:** 若出现基于 CV(computer vision)的 match cut 自动检测工具,可集成到 editor 的自检流程。
- **scene_builder schema 变化:** 若 scene_builder 输出的 `axis_data` 字段 schema 变化,需同步更新 §FxRxT Integration。
- **跨平台 viewer 轴线敏感度差异:** 若出现基于 CN viewer vs 西方 viewer 的轴线违反敏感度对比研究,需补充跨文化 viewer 的轴线规则调整。
- **VR / 360° 内容的轴线规则:** 若 Hermes 扩展到 VR / 360° 内容(超出当前 短剧 范围),需重新定义轴线规则(180° 在 VR 中不再适用)。

---

## 轴线合规在 Quality Thresholds 中的映射

本 ref 的量化阈值直接映射到 SKILL.md §Quality Thresholds 的 metric:

| Metric | 本 ref 的映射 | Production Minimum |
|--------|---------------|-------------------|
| `axis_violation_count` | 180° violations + 30° violations + eyeline mismatches 总和(见 §Axis Compliance 自检工作流) | **= 0**(零容忍) |
| `continuity_match` | match cut 质量 + eyeline match + 180° axis compliance 的综合评分 | ≥ 0.80(见 SKILL.md) |
| `transition_smoothness` | match cut 设计质量 + cut on action 应用率 | ≥ 0.88(见 SKILL.md) |

---

> **Disclaimer:** 180° / 30° / eyeline / match cut 的定义是古典电影理论(public domain 行业共识,> 100 年)。量化阈值(angle delta > 180° / < 30° / > 45°)是 classical film theory 的 canonical 标准。FxRxT 矩阵术语(F=Frame / R=Rhythm / T=Transition)是 Hermes Agent 的内部 convention(MIT license)。editor 与 scene_builder 的责任边界(feasibility vs compliance)是基于 Hermes 架构的**操作性定义**。这些阈值与定义是 editor 专家的**唯一真相源** —— SKILL.md body 与其他 refs 必须跨链引用,不得重新定义。
