# CN 短剧 Cutting Rhythm — 平台 cut-density + 1.5x Pace + ≤3s Dead Air

**Source:** 公开 短剧 创作指南 + 创作者公开访谈 + 平台 公开运营报告(MCN 公开数据 aggregated)
**Copyright:** Fair Use — aggregated observation only (no reproduction of copyrighted scripts, editing templates, or proprietary creator-playbook material; see [LICENSE.md](./LICENSE.md))
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 editor 专家在 CN 短剧 场景的剪辑节奏规则 —— 平台特定的 cut-density windows、1.5x pace rule、≤3s dead air rule、BGM-driven cut sync、击中点 cut alignment。本 ref 是 短剧 平台 cut-density 阈值的**唯一真相源** —— SKILL.md body 仅引用 + 跨链,不重述数值(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) 教训)。术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)([爽点](../../_shared/glossary.md#爽点-satisfaction-beat) / [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) / [完播率](../../_shared/glossary.md#完播率-completion-rate) / [竖屏](../../_shared/glossary.md#竖屏-vertical-screen-916) / [男频](../../_shared/glossary.md#男频-male-oriented-channel) / [女频](../../_shared/glossary.md#女频-female-oriented-channel) / [小程序剧](../../_shared/glossary.md#小程序剧-mini-program-drama))。

**重要:** 1.5x pace rule 与 ≤3s dead air rule 的数值由 [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) 独占定义 —— 本 ref 只展开这些数值在 editor 剪辑流程中的执行细节,不重新定义数值本身(Phase 2 [T-03-11](../../../../../.planning/phases/03-top-4-existing-experts-rag/03-02-PLAN.md) threat:cross-link coupling is intentional — single source of truth)。

---

## Cut-Density Windows by Platform/Genre

不同平台 + 不同题材的 短剧 有**显著不同的 cut-density 甜区**。这些数字基于 2026-Q2 公开观察的聚合估算(`*estimated*`),来自 MCN 公开运营报告 + 创作者公开访谈 + 平台推荐算法公开信息。

### 关键 heuristic 1 (load-bearing): 短剧 平台 cut-density 阈值表

| 平台 + 题材 | 单集时长 | cuts/ep | cuts/min | avg shot length | 来源 |
|-------------|----------|---------|----------|-----------------|------|
| **抖音 90s [男频](../../_shared/glossary.md#男频-male-oriented-channel) revenge(战神归来 / 重生复仇)** | 90s | **40-60 cuts** | **27-40 cuts/min** | **~1.5-2.0s** | MCN 公开观察 *estimated* |
| **抖音 90s [女频](../../_shared/glossary.md#女频-female-oriented-channel) romance(豪门虐恋 / 替身白月光)** | 90s | **30-45 cuts** | **20-30 cuts/min** | **~2.0-3.0s** | MCN 公开观察 *estimated* |
| **快手 草根 slice-of-life(草根共鸣 / 生活片段)** | 90-120s | **20-35 cuts** | **13-23 cuts/min** | **~2.5-4.5s** | MCN 公开观察 *estimated* |
| **微信小程序剧 180s [小程序剧](../../_shared/glossary.md#小程序剧-mini-program-drama) drama(长集数连续剧)** | 180s | **60-90 cuts** | **20-30 cuts/min** | **~2.0-3.0s** | MCN 公开观察 *estimated* |
| **视频号 60-90s hybrid(混合题材)** | 60-90s | **25-40 cuts** | **25-45 cuts/min** | **~1.5-2.5s** | 行业观察 *estimated* |

**重要说明:** 这些数字是 *estimated* 聚合观察,不是平台官方数据。它们来自 MCN 公开创作者访谈 + 平台创作者中心运营指南的聚合估算。实际效果需通过平台 A/B 测试验证,超出本 ref 的纯文档范围。

### 为什么不同平台 / 题材的 cut-density 不同?

| 维度 | 影响 | 解释 |
|------|------|------|
| **平台算法偏好** | 高 | 抖音 推荐 算法权重 完播率 ~35% *estimated*(见 [`../compliance_marketing/references/platform-specs-douyin.md`](../compliance_marketing/references/platform-specs-douyin.md) §推荐机制),高 cut 密度 → 高完播率 → 高分发权重。快手 算法权重更均衡(完播率 / 互动率 / 转发率),允许稍慢节奏。 |
| **观众期待** | 高 | 男频 revenge 观众期待"快节奏爽感",女频 romance 观众接受"慢节奏情感"。快手草根观众更重视"真实感",不接受过度快切。 |
| **单集时长** | 中 | 90s 单集需要更快节奏(信息密度高);180s 小程序剧 长集允许稍慢(有更多叙事空间)。 |
| **题材类型** | 高 | action / revenge / 慕强 题材天然需要高 cut 密度;romance / 宫斗 题材接受中等密度;slice-of-life 题材允许低密度。 |

### Cut-Density 与 Murch Rule of Six Rhythm 维度的映射

短剧 平台 cut-density 阈值是 Rule of Six 第 3 维度 (Rhythm,见 [`murch-rule-of-six.md`](./murch-rule-of-six.md)) 的**平台特定经验值**:

- 若 短剧 单集的实际 cut 密度**落在对应平台 / 题材的窗口内** → Rhythm 评分高(8-10/10)。
- 若偏离窗口 ±20% → Rhythm 评分中等(5-7/10),需检查是否有创作理由。
- 若偏离窗口 > 50%(例如 抖音-男频 revenge 短剧 只剪 20 cuts/90s-ep)→ Rhythm 评分低(≤ 3/10),完播率 会受直接冲击。

---

## 1.5x Pace Rule

> **重要:** 本节只展开 1.5x pace rule 的数值在 editor 剪辑流程中的执行细节。**数值本身(竖屏平均 shot length ≈ 1.5s,横屏通常 2-3s)由 [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §1.5x Pace Rule 独占定义** —— 本 ref 跨链引用,不重新定义。

### 1.5x Pace Rule 的执行

1.5x pace rule 在 editor 剪辑流程中的执行:

| 执行点 | 规则 | 来源 |
|--------|------|------|
| **avg shot length** | 竖屏 短剧 ≈ **1.5s**(横屏 16:9 通常 2-3s) | [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §1.5x Pace Rule(canonical source) |
| **90s 单集最少 cuts** | **~60 cuts minimum**(90 ÷ 1.5 = 60) | 派生自 1.5s avg shot length |
| **180s 小程序剧最少 cuts** | **~120 cuts minimum**(180 ÷ 1.5 = 120) | 派生自 1.5s avg shot length |
| **cut-density 范围** | 各平台 / 题材的具体窗口见 §Cut-Density Windows by Platform/Genre | 本 ref(平台特定细化) |

**关键 heuristic 2:** 1.5x pace rule 是**竖屏通用基线**,但各平台 / 题材可在此基础上调整:

- 抖音-男频 revenge 通常**略快于** 1.5s avg shot length(可达 1.2-1.5s),因为 action 段需要更高密度。
- 抖音-女频 romance 通常**略慢于** 1.5s avg shot length(可达 2.0-3.0s),因为情感段需要更多 breathing room。
- 快手-草根 通常**显著慢于** 1.5s avg shot length(可达 2.5-4.5s),因为草根观众不接受过度快切。

### 1.5x Pace Rule 与 Classical Editing 横屏阈值的换算

本 ref 的 cut-density 阈值与 [`classical-editing-rhythm.md`](./classical-editing-rhythm.md) §Cut-Density Windows by Genre 的横屏阈值通过 1.5x 换算关联:

| 类型 | 横屏 cuts/min | 竖屏 短剧 cuts/min(× 1.5) | 本 ref 的实际阈值 | 一致性 |
|------|---------------|----------------------------|-------------------|--------|
| Drama | 8-12 | 12-18 | 抖音-女频 romance 20-30 | 略高(女频 romance 偏 action 化) |
| Action | 20-40 | 30-60 | 抖音-男频 revenge 27-40 | 一致(在窗口内) |
| Slice-of-life | 4-10 | 6-15 | 快手-草根 13-23 | 略高(快手草根节奏稍快于经典 slice-of-life) |

**关键 heuristic 3:** 横屏 → 竖屏的 1.5x 换算是**近似值**,不是精确公式。本 ref 的平台特定阈值是 editor 的**首选参考**;[`classical-editing-rhythm.md`](./classical-editing-rhythm.md) 的换算值作为"fallback 理论参考"(若没有平台特定数据时使用)。

---

## ≤3s Dead Air Rule

> **重要:** 本节只展开 ≤3s dead air rule 的数值在 editor 剪辑流程中的执行细节。**数值本身(连续 shot 无 cut / dialogue / audio change > 3s = viewer 跳出风险)由 [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §3-Second Dead Air Rule 独占定义** —— 本 ref 跨链引用,不重新定义。

### ≤3s Dead Air Rule 的执行

| 执行点 | 规则 | 来源 |
|--------|------|------|
| **max shot duration** | 单个 shot ≤ **3s**(除非满足例外条件) | [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §3-Second Dead Air Rule(canonical source) |
| **dead air 定义** | 连续 shot 无 cut / 无 dialogue / 无 audio change | 本 ref(执行细化) |
| **viewer 跳出率** | 每超出 3s 一秒,跳出率上升 ~15% *estimated*(抖音) | [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §3-Second Dead Air Rule |

### ≤3s Dead Air Rule 的例外条件

并非所有 > 3s 的 shot 都是 dead air —— 以下例外条件允许 shot > 3s:

| 例外条件 | 允许 shot 时长 | 原因 | 验证 |
|----------|----------------|------|------|
| **emotional 特写(情绪弧线峰值)** | ≤ 4-5s | 情绪特写承载 emotion_curve 峰值,viewer 沉浸其中 | emotion_curve.v ≥ 0.8 |
| **BGM swell(BGM 渐强段)** | ≤ 4-5s | BGM swell 提供音频变化,不构成 dead air | composer.coupled_beat.json 标注 swell |
| **环境建立镜头(scene establishment)** | ≤ 4s | 场景开头需要空间交代 | 仅限 segment 开头 1 个 shot |
| **主题升华长镜头** | ≤ 5-6s | 罕见;用于主题表达(配合 intellectual montage) | 需 screenplay + style_genome 确认 |

**关键 heuristic 4:** editor 在生成 cut list 时,所有 > 3s 的 shot 必须标注 `"dead_air_exception": "emotional_climax" / "bgm_swell" / "scene_establishment" / "thematic_long_take"` + 对应验证字段(如 `"emotion_ref": "emotion_curve.samples[5].v=0.85"`)。未标注例外的 > 3s shot 应在自检阶段标记为 DEAD_AIR_VIOLATION。

---

## BGM-Driven Cut Sync

短剧 的 cut 时机高度依赖 BGM beat 对齐 —— 这是 rhythmic montage(见 [`montage-theory.md`](./montage-theory.md) §Rhythmic Montage)在 短剧 的核心应用。

### 关键 heuristic 5 (load-bearing): BGM-Driven Cut Sync 效果

> **cut 时机对齐 BGM beat(鼓点 / 重音 / 节拍变化)时,viewer 感知的 rhythm_coherence 提升 ~25% *estimated*(subjective viewer study proxy)。**

数值:

| cut 时机 | rhythm_coherence 评分 *estimated | viewer 感知 |
|----------|----------------------------------|-------------|
| **BGM beat 对齐**(cut on beat) | **~0.85-0.95** | "节奏感强 / 爽" |
| **BGM beat 近似对齐**(±100ms) | ~0.70-0.80 | "节奏感还行" |
| **BGM beat 未对齐**(> 200ms 偏差) | ~0.40-0.60 | "节奏乱 / 跳" |

### BGM-Driven Cut Sync 的执行流程

editor 在生成 cut list 时,应消费 composer 专家的 `coupled_beat.json`(详见 [`../hook_retention/references/vertical-pacing.md`](../hook_retention/references/vertical-pacing.md) §BGM 节奏):

1. **加载 composer.coupled_beat.json** —— 包含 BGM 的 beat timestamps(如 `[0.5s, 1.0s, 1.5s, 2.0s, ...]`)。
2. **对每个 candidate cut point,寻找最近的 BGM beat** —— 若 candidate cut point 距最近 beat ≤ 100ms,标记为 `bgm_aligned`;否则标记为 `bgm_unaligned`。
3. **优先选择 bgm_aligned 的 cut point** —— 若多个 candidate cut point 都满足 Rule of Six,优先选 bgm_aligned 的那个。
4. **验证整体 bgm_alignment_rate** —— 整集 cut list 中,`bgm_aligned` cuts 占比应 ≥ 70% *estimated*(低于此阈值说明 cut 与 BGM 节奏脱节,rhythm_accuracy 会下降)。

### BGM-Driven Cut Sync 与 Murch Rhythm 维度的映射

BGM-driven cut sync 直接影响 Rule of Six 第 3 维度 (Rhythm) 的评分:

- 若 cut 的 `bgm_aligned` = true → Rhythm 评分 +2(加成)。
- 若 cut 的 `bgm_aligned` = false 但 emotion ≥ 8.0 → Rhythm 评分不扣(Emotion-First 豁免)。
- 若 cut 的 `bgm_aligned` = false 且 emotion < 5.0 → Rhythm 评分 -2(扣分)。

---

## 击中点 Cut Alignment

[击中点](../../_shared/glossary.md#击中点-emotional-impact-point) (emotional-impact point) 是 短剧 节奏设计的中间台阶(详见 [`../hook_retention/references/conflict-escalation.md`](../hook_retention/references/conflict-escalation.md) §击中点 Placement Density)。editor 的责任是确保每个 击中点 align 在 cut 或 motion transition 上,而不是 mid-static-shot。

### 关键 heuristic 6 (load-bearing): 击中点 Cut Alignment 规则

> **每个 [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) 必须align 在一个 cut 或 motion transition 上,而不是 mid-static-shot。**

击中点 的密度来自 [`../hook_retention/references/conflict-escalation.md`](../hook_retention/references/conflict-escalation.md) §击中点 Placement Density(canonical source):

| 击中点 类型 | 间隔 | 单集 90s 短剧典型数量 | 来源 |
|-------------|------|-----------------------|------|
| 软峰(情绪微冲击) | **每 10-15 秒** 至少 1 个 | 5-7 个 | conflict-escalation.md(canonical) |
| 硬峰(情绪大冲击) | **每 30-45 秒** 至少 1 个 | 1-2 个 | conflict-escalation.md(canonical) |
| 总计 | — | **6-9 个** 击中点 | conflict-escalation.md(canonical) |

### 击中点 Cut Alignment 的执行

editor 在生成 cut list 时,应消费 screenplay 专家的 emotion_curve.samples(标注 击中点 位置)与 hook_retention 专家的 markers:

1. **识别所有 击中点 timestamps** —— 来自 emotion_curve.samples 中 v ≥ 0.7 的采样点(软峰)或 v ≥ 0.8 的采样点(硬峰)。
2. **对每个 击中点,验证是否有 cut 或 motion transition align** —— 若 击中点 timestamp 距最近 cut ≤ 200ms,标记为 `击中点_aligned`;否则标记为 `击中点_misaligned`。
3. **所有 击中点 必须 aligned** —— `击中点_misaligned` 是自检失败项(除非 emotion ≥ 0.9 且 shot 是 intentional emotional climax)。
4. **优先在 击中点 处使用 cut on action**(见 [`classical-editing-rhythm.md`](./classical-editing-rhythm.md) §Cut on Action) —— 击中点 + cut on action 的组合是 短剧 "爽感"的核心来源。

### 击中点 Cut Alignment 与 Rule of Six Emotion 维度的协同

击中点 cut alignment 直接影响 Rule of Six 第 1 维度 (Emotion) 的评分:

- 若 击中点 aligned 在 cut 上 → Emotion 评分取 emotion_curve.v × 10(如 v=0.8 → Emotion 8/10)。
- 若 击中点 misaligned(在 mid-static-shot 中) → Emotion 评分 -2(扣分),因为 viewer 在 static shot 中感受不到"击中"的冲击。

### 击中点 Cut Alignment 的 90s 短剧 示例

以一个 90s [男频](../../_shared/glossary.md#男频-male-oriented-channel) revenge 短剧 为例,展示 击中点 与 cut list 的 alignment:

| 时间戳 | 击中点 类型 | emotion_curve.v | cut 对齐情况 | 状态 |
|--------|-------------|-----------------|--------------|------|
| 0-3s | 钩子锚定 | 0.6 | cut on action(主角转身) | aligned ✓ |
| ~10-15s | 第一次 击中点(软峰) | 0.7 | cut on action(主角展示实力) | aligned ✓ |
| ~30-45s | 硬峰 击中点 | 0.8 | cut on BGM beat(反派震惊) | aligned ✓ |
| ~70-80s | [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) 峰值 | 0.95 | cut on action(主角碾压) | aligned ✓ |
| ~85-90s | [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) cliffhanger | unresolved | cut on BGM swell(悬念收尾) | aligned ✓ |

总 击中点 数 = 5(符合 conflict-escalation.md 的 6-9 个区间下限附近;revenge 题材 击中点 偏少因为情绪集中爆发)。所有 击中点 aligned 在 cut 或 motion transition 上。

---

## 短剧 剪辑节奏的 3 个反模式 (Anti-Patterns)

editor 在 短剧 剪辑中应避免以下 3 个常见反模式:

### 反模式 1:节奏均匀(无 build-to-climax)

**症状:** 整集 90s 短剧 的 cut 密度均匀(如全程 40 cuts/min),没有高潮段加密。

**诊断:** build-to-climax 倍数 < 1.3(高潮段 cut 密度与 baseline 相差不大)。

**后果:** viewer 感觉"节奏平",爽点 不够爽,完播率 下降。

**修复:** 按 [`classical-editing-rhythm.md`](./classical-editing-rhythm.md) §Build-to-Climax Rule,在最后 25% runtime 增加cut 密度到 baseline 的 1.5-2x。

### 反模式 2:过度快切(无喘息帧)

**症状:** 整集全程高 cut 密度(60+ cuts/min),没有喘息帧。

**诊断:** 爆发段(cut 密度 > 40 cuts/min)持续时间 > 30s 无中断。

**后果:** viewer 进入 viewer-fatigue 状态(见 [`murch-rule-of-six.md`](./murch-rule-of-six.md) §Blink Rhythm Theory 的 30 cuts/min 阈值),注意力分散,完播率 反而下降。

**修复:** 每 15-20s 插入一个 2-3s 喘息帧(见 [`classical-editing-rhythm.md`](./classical-editing-rhythm.md) §喘息帧设计)。

### 反模式 3:BGM 与 cut 脱节

**症状:** cut 时机与 BGM beat 不对齐(bgm_alignment_rate < 50%)。

**诊断:** 大量 cut 的 timestamp 距最近 BGM beat > 200ms。

**后果:** viewer 感觉"节奏乱 / 跳",rhythm_coherence 下降 ~25%(见 §BGM-Driven Cut Sync)。

**修复:** 重新生成 cut list,优先选择 bgm_aligned 的 cut point;若 candidate cut 都不 align,调整 BGM(composer 协作)或调整 cut 时机。

---

## 短剧 剪辑节奏自检工作流

editor 在完成 cut list 生成后,应执行以下 短剧 专用的节奏自检流程:

```
对整集 cut list 执行:
  1. cut-density 验证
     ├── 计算总 cuts 与 单集时长 → cuts/min
     ├── 对照 §Cut-Density Windows by Platform/Genre 验证
     └── 若偏离窗口 > 20% → 报告 CUT_DENSITY_DRIFT warning

  2. 1.5x pace rule 验证
     ├── 计算 avg shot length = 单集时长 / 总 cuts
     └── 若 avg shot length > 2.0s(显著慢于 1.5s baseline)→ 报告 PACE_TOO_SLOW warning

  3. ≤3s dead air 验证
     ├── 对每个 shot,检查 duration > 3s
     ├── 若 duration > 3s 且无 dead_air_exception 标注 → 标记 DEAD_AIR_VIOLATION
     └── 若有 exception 标注,验证 exception 条件(如 emotion_curve.v ≥ 0.8)

  4. BGM-driven cut sync 验证
     ├── 对每个 cut,检查 bgm_aligned 字段
     ├── 计算 bgm_alignment_rate = bgm_aligned cuts / 总 cuts
     └── 若 bgm_alignment_rate < 70% → 报告 BGM_SYNC_LOW warning

  5. 击中点 cut alignment 验证
     ├── 加载 emotion_curve.samples,识别 v ≥ 0.7 的 击中点
     ├── 对每个 击中点,验证距最近 cut ≤ 200ms
     └── 若 misaligned → 标记 击中点_MISALIGNED(除非 emotion ≥ 0.9 exception)

  6. build-to-climax 验证
     ├── 计算 baseline(0-67.5s for 90s ep)的 cuts/min
     ├── 计算 climax(67.5-90s)的 cuts/min
     └── 若 climax/baseline < 1.5 → 报告 BUILD_TO_CLIMAX_INSUFFICIENT warning

  7. 综合自检结果
     ├── 统计 violations + warnings
     ├── 若有任何 violation → 自检 FAIL,返回修复
     └── 若全部 PASS → 自检 PASS,输出 cut list
```

**自检输出 JSON 示例:**

```json
{
  "rhythm_check_report": {
    "cut_density_cuts_per_min": 38,
    "cut_density_window": "27-40 (抖音-男频 revenge)",
    "cut_density_status": "PASS",
    "avg_shot_length_s": 1.58,
    "pace_rule_status": "PASS",
    "dead_air_violations": 0,
    "dead_air_exceptions": 2,
    "bgm_alignment_rate": 0.78,
    "bgm_sync_status": "PASS",
    "击中点_aligned_count": 5,
    "击中点_misaligned_count": 0,
    "击中点_alignment_status": "PASS",
    "build_to_climax_ratio": 1.65,
    "build_to_climax_status": "PASS",
    "overall_status": "PASS"
  }
}
```

**关键 heuristic 7:** 短剧 剪辑节奏自检是 SKILL.md §Quality Thresholds 的 `rhythm_accuracy` metric 的具体执行 —— rhythm_accuracy = (PASS 的检查项数 / 总检查项数)。例如,上述示例 6 项全部 PASS,所以 rhythm_accuracy = 6/6 = 1.0(production minimum ≥ 0.85,见 SKILL.md)。

---

## Cross-References

- [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §1.5x Pace Rule —— **1.5x pace rule 的 canonical source**(本 ref 跨链引用,不重新定义)。
- [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §3-Second Dead Air Rule —— **≤3s dead air rule 的 canonical source**(本 ref 跨链引用,不重新定义)。
- [`../hook_retention/references/vertical-pacing.md`](../hook_retention/references/vertical-pacing.md) —— 竖屏 cut density + BGM sync + 字幕 设计的执行细节(Phase 2);本 ref 与之协同,但平台 cut-density 阈值由本 ref 独占。
- [`../hook_retention/references/conflict-escalation.md`](../hook_retention/references/conflict-escalation.md) §击中点 Placement Density —— **击中点 density 的 canonical source**(本 ref 跨链引用,不重新定义)。
- [`murch-rule-of-six.md`](./murch-rule-of-six.md) §Blink Rhythm Theory —— cut 密度 > 30 cuts/min 的 viewer-fatigue 阈值;短剧 高密度剪辑的疲劳管理。
- [`murch-rule-of-six.md`](./murch-rule-of-six.md) §Emotion-First Decision Rule —— 击中点 cut 必须 align 在 emotion ≥ 0.7 的情绪节点。
- [`classical-editing-rhythm.md`](./classical-editing-rhythm.md) §Cut-Density Windows by Genre —— 横屏长片 cut-density 阈值;本 ref 通过 1.5x 换算作为 fallback 参考。
- [`classical-editing-rhythm.md`](./classical-editing-rhythm.md) §Build-to-Climax Rule —— 短剧 高潮段的 cut 密度加密(1.5-2x baseline)。
- [`classical-editing-rhythm.md`](./classical-editing-rhythm.md) §Cut on Action —— 击中点 cut 应优先使用 cut on action。
- [`montage-theory.md`](./montage-theory.md) §Rhythmic Montage —— BGM-driven cut sync 是 rhythmic montage 的 短剧 应用。
- [`montage-theory.md`](./montage-theory.md) §Tonal Montage Application to 短剧 爽点 —— 爽点 段的三维协同(cut-density + color-tone + sound-tone)。
- [`../../_shared/glossary.md`](../../_shared/glossary.md) —— [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) / [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) / [完播率](../../_shared/glossary.md#完播率-completion-rate) / [竖屏](../../_shared/glossary.md#竖屏-vertical-screen-916) / [男频](../../_shared/glossary.md#男频-male-oriented-channel) / [女频](../../_shared/glossary.md#女频-female-oriented-channel) / [小程序剧](../../_shared/glossary.md#小程序剧-mini-program-drama) 术语定义。

---

## Refresh Cadence

- **每季度复核一次**(下次:2026-09)。
- **复核内容:** 平台 cut-density 阈值是否仍是 2026-Q2 的甜区(平台算法可能漂移);1.5x pace rule 的执行细节是否需要调整(若平台分发逻辑变化);BGM-driven cut sync 的 rhythm_coherence 提升幅度(~25%)是否有新数据;击中点 cut alignment 的 density 是否仍 align conflict-escalation.md。
- **复核来源:** MCN 公开运营报告 + 平台创作者中心运营指南 + 创作者公开访谈 + 平台推荐算法公开信息。
- **不需要更新:** 1.5x pace rule 与 ≤3s dead air rule 的**数值**(由 [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) 独占定义,本 ref 不重新定义)。

---

## Drift Signals

若以下信号出现,本 ref 需要更新:

- **平台 cut-density 漂移:** 若行业统计显示 抖音-男频 revenge 的甜区从 40-60 cuts/90s-ep 漂移到 50-70(节奏进一步加快),需更新 §Cut-Density Windows by Platform/Genre 的阈值。
- **新平台涌现:** 若新的 短剧 平台(如 B站 竖屏 / 小红书 视频)需要 editor 支持,需补充对应平台的 cut-density 阈值。
- **跨平台 viewer 节奏敏感度差异:** 若 A/B 测试显示不同平台 viewer 对 cut 密度的敏感度有显著差异(例如 抖音 viewer 比 快手 viewer 更能接受高 cut 密度),需更新 §Cut-Density Windows by Platform/Genre 的解释。
- **1.5x pace rule 调整:** 若 [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §1.5x Pace Rule 的数值发生变化(例如从 1.5s 调整到 1.3s),需同步更新本 ref 的派生阈值(~60 cuts / 90s minimum 等)。
- **AI 生成内容的 BGM 同步挑战:** 若 AI 生成的 BGM 缺乏明确 beat(coupled_beat.json 质量低),需补充 fallback 规则(如何用 LLM 推断 beat 时机)。

---

> **Disclaimer:** 平台 cut-density 阈值(抖音-男频 40-60 / 抖音-女频 30-45 / 快手 20-35 / 小程序剧 60-90)、BGM-driven cut sync 的 rhythm_coherence 提升(~25%)、击中点 cut alignment 的间隔(10-15s 软峰 / 30-45s 硬峰)均为基于公开观察的**聚合估算**(`*estimated*`)。这些数字是 editor 专家在 短剧 场景的**唯一真相源** —— SKILL.md body 与其他 refs 必须跨链引用,不得重新定义。1.5x pace rule 与 ≤3s dead air rule 的**数值**由 [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) 独占定义 —— 本 ref 只展开执行细节,不重新定义数值本身。
