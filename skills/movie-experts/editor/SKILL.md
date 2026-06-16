---
name: editor
description: "Editor Expert: FxRxT 3D editing matrix with Y/L/C/S cross-library orchestration, shot assembly for narrative rhythm."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, editing, rhythm, transition, montage, axis-rule, cut]
    related_skills: [screenplay, visual_executor, audio_pipeline, continuity_auditor, compliance_gate, hook_retention, cinematographer, theory_critic, documentary_maker]
    expert_id: editor
    metrics: [rhythm_accuracy, continuity_match, axis_violation_count, transition_smoothness]
---

# Editor Expert (剪辑专家)

Film editing grammar specialist managing the FxRxT three-dimensional editing matrix (Frame type x Rhythm pattern x Transition mode) with Y/L/C/S cross-library orchestration and shot assembly for narrative rhythm, applying Murch Rule of Six weighted scoring (Emotion 50% / Story 23% / Rhythm 10% / Eye-trace 7% / 2D plane 5% / 3D space 3%) as the top-level cut decision framework.

## When to use this skill

The user needs to plan shot sequences, design editing rhythm, create edit decision lists, manage transitions, verify 180° axis compliance, or assemble final cuts for AI film production. Typically invoked after `screenplay` (for shot_count estimates + emotion_curve) and `visual_executor` (for video clips). Also invoked when designing 短剧 cut-density windows per platform, applying Murch Emotion-First cut decision, or verifying FxRxT axis compliance.

## References

本专家所有数值阈值由下列 5 个 refs 独占定义;SKILL.md body 仅作摘要 + 跨链,不重新给出数字原理(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) 教训)。

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/murch-rule-of-six.md`](./references/murch-rule-of-six.md) | 做任何 cut 决策前 | Murch Rule of Six 加权评分模型(Emotion 50% / Story 23% / Rhythm 10% / Eye-trace 7% / 2D plane 5% / 3D space 3%,2nd ed canonical)+ Emotion-First 决策规则(emotion ≥ 8.0 豁免 / emotion ≤ 3.0 否决)+ Eye-trace 帧位移量化(横屏 ≤30%/40%,竖屏收紧 10%)+ Blink 节奏理论(~4s 眨眼间隔 + 30 cuts/min viewer-fatigue 阈值)+ 6-shot 完整评分工作流示例 |
| [`references/classical-editing-rhythm.md`](./references/classical-editing-rhythm.md) | 设计任何场景的节奏前 | Reisz-Millar 古典剪辑节奏学:cut-density windows by genre(横屏 drama 8-12 / action 20-40 / comedy 12-20 cuts/min)+ 竖屏 1.5x 换算 + build-to-climax 规则(最后 25% runtime = 1.5-2x baseline)+ cut on action 隐形效果(-70% viewer 察觉率)+ invisible editing 定义(eye-tracking < 10% 阈值)+ 喘息帧设计(2-3s 长度,15-20s 间隔) |
| [`references/montage-theory.md`](./references/montage-theory.md) | 设计任何蒙太奇 / 主题升华段前 | Eisenstein 5 种 montage 方法表(Metric / Rhythmic / Tonal / Overtonal / Intellectual)+ collision 原理(thesis + antithesis → synthesis)+ 经典示例(Strike / Potemkin / October)+ metric montage 帧数规则(24/48/96 frames at 24fps)+ tonal montage 在 短剧 爽点 段的三维协同(cut-density + color-tone + sound-tone)+ montage method 选择决策树 |
| [`references/fxrxt-axis-compliance.md`](./references/fxrxt-axis-compliance.md) | 做任何 cut 决策前(180°/30°/eyeline 验证) | 180° 轴线规则(angle delta > 180° = 零容忍违反)+ 30° 规则(angle delta < 30° = jump-cut 风险)+ eyeline match(方向差 > 45° = 违反)+ match cut 设计(graphic / motion / sound 三种类型)+ FxRxT 矩阵整合(editor=compliance, scene_builder=feasibility; Phase 17 v3.0 起 scene_builder feasibility 已折叠入 cinematographer composition_lock 子任务)+ 轴线合规自检工作流 JSON 输出 |
| [`references/cn-cutting-rhythm.md`](./references/cn-cutting-rhythm.md) | 设计 短剧 单集节奏前 | 平台 cut-density windows(抖音-男频 revenge 40-60/90s-ep / 抖音-女频 romance 30-45 / 快手-草根 20-35 / 小程序剧 60-90)+ 1.5x pace rule 跨链(数值由 [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) 独占)+ ≤3s dead air rule 跨链 + BGM-driven cut sync(rhythm_coherence +25%)+ 击中点 cut alignment + 3 个反模式 + 自检工作流 |
| [`../_shared/project-corpus/editing-sound-post.md`](../_shared/project-corpus/editing-sound-post.md) | 研究默奇剪辑哲学 / 学 7 位剪辑先驱 / 学音效圣经 5 分类时 | 《剪辑之道》5 城市 5 对话 + 默奇"谦卑的声音" + 6 原则权重 + 庖丁解牛比喻 + 7 位剪辑先驱(梅里爱/史密斯/波特/百代/格里菲斯/爱森斯坦/戈达尔)+ 《音效圣经》5 大分类(硬效果/拟音/背景/电子/声音设计)+ 录音十诫 |

## Role & Philosophy

- **Rule of Six 是顶层决策框架** —— 所有 cut 必须先过 Murch 加权评分(Emotion 50% / Story 23% / Rhythm 10% / Eye-trace 7% / 2D plane 5% / 3D space 3%,per [`references/murch-rule-of-six.md`](./references/murch-rule-of-six.md) §The Rule of Six Weightings);其他理论(Reisz-Millar / Eisenstein / FxRxT / CN 短剧)提供具体维度的执行规则
- **Emotion-Supreme(Emotion-First 在 短剧 加强版)** —— cut 必须先问"是否维护了 emotion_curve 的情绪弧线";emotion ≥ 8.0 的 cut 即使其他维度失败仍可保留;emotion ≤ 3.0 的 cut 必须否决(per [`references/murch-rule-of-six.md`](./references/murch-rule-of-six.md) §Emotion-First Decision Rule)
- **180° 轴线是零容忍硬约束** —— 即使 emotion = 10/10,180° 轴线违反也必须否决并重新设计;这是唯一不受 Emotion-First 豁免的硬约束(per [`references/fxrxt-axis-compliance.md`](./references/fxrxt-axis-compliance.md) §180° Axis Rule)
- **短剧 节奏平台差异化** —— 抖音-男频 revenge 需要 40-60 cuts/90s-ep 的高密度,但快手-草根 只需 20-35 cuts/90s-ep;cut 密度不是越高越好,而是要匹配平台 + 题质的甜区(per [`references/cn-cutting-rhythm.md`](./references/cn-cutting-rhythm.md) §Cut-Density Windows by Platform/Genre)
- **invisible editing 是默认美学,montage 是特殊场景** —— 短剧 以 invisible editing 为主(cut 不被察觉);montage 仅在回忆 / 主题升华 / 概念表达段使用(per [`references/montage-theory.md`](./references/montage-theory.md) §Montage Method 选择决策树)

## Knowledge Retrieval

在生成任何 edit_decision_list / cut list / axis_check_report 输出前,按以下顺序检索上下文(5 个检索主题):

- **Murch Rule of Six 加权评分模型**(Emotion 50% / Story 23% / Rhythm 10% / Eye-trace 7% / 2D plane 5% / 3D space 3% + Emotion-First 决策规则 + Eye-trace 帧位移量化 + Blink 节奏理论)—— 详见 [`references/murch-rule-of-six.md`](./references/murch-rule-of-six.md)
- **Reisz-Millar 古典剪辑节奏学**(cut-density windows by genre + build-to-climax 规则 + cut on action + invisible editing 定义 + 喘息帧设计)—— 详见 [`references/classical-editing-rhythm.md`](./references/classical-editing-rhythm.md)
- **Eisenstein 蒙太奇理论**(5 种 montage 方法 + collision 原理 + metric montage 帧数 + tonal montage 在 短剧 爽点 的应用)—— 详见 [`references/montage-theory.md`](./references/montage-theory.md)
- **FxRxT 轴线合规规则**(180° / 30° / eyeline / match cut + editor 与 scene_builder 的责任边界;Phase 17 v3.0 起 scene_builder feasibility 已折叠入 cinematographer composition_lock 子任务)—— 详见 [`references/fxrxt-axis-compliance.md`](./references/fxrxt-axis-compliance.md)
- **CN 短剧 剪辑节奏**(平台 cut-density windows + 1.5x pace rule + ≤3s dead air rule + BGM-driven cut sync + 击中点 cut alignment)—— 详见 [`references/cn-cutting-rhythm.md`](./references/cn-cutting-rhythm.md)

**若当前 runtime 中有 memory / RAG 工具**(例如 `<memory_plugin>` / `<rag_search>` 或类似检索工具,具体工具名由 runtime 决定),使用以下查询范围:

```
tags="expert:editor,domain:murch-rule-of-six"
tags="expert:editor,domain:classical-editing-rhythm"
tags="expert:editor,domain:montage-theory"
tags="expert:editor,domain:fxrxt-axis-compliance"
tags="expert:editor,domain:cn-cutting-rhythm"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件(以 `## References` 表为准)。静态 refs 是权威源,memory 插件只是更大语料的优化。provider-agnostic 检索是 ablation eval 与多 provider 部署的硬约束。

> **NOTE:** 本 SKILL.md body 不引用任何具体外部模型名。涉及具体模型时使用 `<llm_primary>` / `<llm_fallback>` 占位符(见 [`../_shared/RAG-INVOCATION-PATTERN.md`](../_shared/RAG-INVOCATION-PATTERN.md) placeholder 表)。模型名只出现在 `references/*.md` 与 [`../_shared/known-external-models.yaml`](../_shared/known-external-models.yaml) allowlist 中。

## Core Capabilities

- **FxRxT 三维剪辑矩阵**(F=Frame 景别 / R=Rhythm 节奏 / T=Transition 转场)—— editor 在每个维度执行 Rule of Six + 轴线合规检查
- **Murch Rule of Six 加权评分** —— 对每个 cut,按 6 维度评分并计算 murch_score,触发 Emotion-First 豁免 / 否决逻辑(per [`references/murch-rule-of-six.md`](./references/murch-rule-of-six.md) §Murch Score Calculation)
- **180° 轴线合规自检** —— 对每个 cut,验证 angle delta(> 180° 零容忍 / < 30° jump-cut 风险)与 eyeline match(方向差 > 45° 违反)(per [`references/fxrxt-axis-compliance.md`](./references/fxrxt-axis-compliance.md) §Axis Compliance 自检工作流)
- **平台特定 cut-density 规划** —— 根据平台(抖音 / 快手 / 小程序剧 / 视频号)与题材(男频 / 女频 / 草根)选择 cut-density 窗口(per [`references/cn-cutting-rhythm.md`](./references/cn-cutting-rhythm.md) §Cut-Density Windows by Platform/Genre)
- **Montage 段落设计** —— 根据场景美学意图选择 montage method(Metric / Rhythmic / Tonal / Overtonal / Intellectual)或 invisible editing(per [`references/montage-theory.md`](./references/montage-theory.md) §Montage Method 选择决策树)
- **击中点 cut alignment** —— 每个 [击中点](../../_shared/glossary.md#击中点-emotional-impact-point) 必须 align 在 cut 或 motion transition 上,不是 mid-static-shot(per [`references/cn-cutting-rhythm.md`](./references/cn-cutting-rhythm.md) §击中点 Cut Alignment)
- **BGM-driven cut sync** —— cut 时机对齐 audio_pipeline.composer.coupled_beat.json 的 BGM beat,bgm_alignment_rate ≥ 70%(per [`references/cn-cutting-rhythm.md`](./references/cn-cutting-rhythm.md) §BGM-Driven Cut Sync)
- **Y/L/C/S 跨库编排**(Y=Tempo / L=Transition / C=Composition / S=Narrative)—— 与 emotion_curve + coupled_beat 联动

## Output Format

- `edit_decision_list.json`: per-shot in/out/transition/duration + murch_score + murch_breakdown + segment_type + montage_method + bgm_aligned 字段
- `beat_timeline.json`: editing rhythm line + coupled_beat alignment marks + 击中点 cut alignment 验证
- `axis_check_report`: 180° + 30° + eyeline 合规检测报告(含 violations 列表 + 修复建议)

## Key Parameters

### LLM Generation
- **model**: `<llm_primary>` (any high-quality chat model with ≥ 8K context; if `<llm_primary>` available, use it; otherwise `<llm_fallback>` — see [`../_shared/known-external-models.yaml`](../_shared/known-external-models.yaml) for current catalog)
- **temperature**: 0.6-0.8 (less creative than screenplay; rhythm decisions need consistency)
- **max_tokens**: 4096 (full cut list), 1024 (single-segment)
- **top_p**: 0.85

### Murch Rule of Six Scoring
- **weightings**: Emotion 50% / Story 23% / Rhythm 10% / Eye-trace 7% / 2D plane 5% / 3D space 3% (per [`references/murch-rule-of-six.md`](./references/murch-rule-of-six.md) §The Rule of Six Weightings,2nd ed 2001 canonical)
- **murch_score 公式**: `(emotion × 0.50) + (story × 0.23) + (rhythm × 0.10) + (eye_trace × 0.07) + (plane_2d × 0.05) + (space_3d × 0.03)` (per [`references/murch-rule-of-six.md`](./references/murch-rule-of-six.md) §加权评分计算公式)
- **go/no-go 阈值**: ≥ 7.0 优秀 / 5.0-6.9 合格 / 3.0-4.9 弱 / < 3.0 不合格(per [`references/murch-rule-of-six.md`](./references/murch-rule-of-six.md) §加权评分计算公式)
- **Emotion-First 豁免**: emotion ≥ 8.0 即使 murch_score < 5.0 可保留;emotion ≤ 3.0 即使 murch_score ≥ 7.0 必须否决(per [`references/murch-rule-of-six.md`](./references/murch-rule-of-six.md) §Emotion-First Decision Rule)
- **Eye-trace 帧位移阈值**: 横屏 ≤ 30% 完美 / 30-40% 可接受 / > 40% 违反;竖屏收紧 10%(per [`references/murch-rule-of-six.md`](./references/murch-rule-of-six.md) §Eye-Trace Quantification)

### Rhythm Parameters — Cut-Density Windows(平台特定,per [`references/cn-cutting-rhythm.md`](./references/cn-cutting-rhythm.md) §Cut-Density Windows by Platform/Genre)
- **抖音-男频 revenge**: 40-60 cuts/90s-ep(~27-40 cuts/min,avg shot length ~1.5-2.0s)
- **抖音-女频 romance**: 30-45 cuts/90s-ep(~20-30 cuts/min,avg shot length ~2.0-3.0s)
- **快手-草根 slice-of-life**: 20-35 cuts/90-120s-ep(~13-23 cuts/min,avg shot length ~2.5-4.5s)
- **小程序剧 180s drama**: 60-90 cuts/180s-ep(~20-30 cuts/min,avg shot length ~2.0-3.0s)
- **视频号 60-90s hybrid**: 25-40 cuts/60-90s-ep(~25-45 cuts/min,avg shot length ~1.5-2.5s)

### Rhythm Parameters — Generic Thresholds(per [`references/classical-editing-rhythm.md`](./references/classical-editing-rhythm.md) §Cut-Density Windows by Genre,横屏换算)
- **cuts_per_second**: 0.3-0.5 (dialogue 横屏), 0.8-1.2 (action 横屏), 0.2-0.4 (emotional 横屏) —— 竖屏 × 1.5
- **shot_duration_min**: 0.5s (action), 2.0s (dialogue)
- **shot_duration_max**: 10.0s (establishing), 15.0s (extreme slow)
- **beat_alignment**: ±100ms (with audio_pipeline (composer sub-step)'s coupled_beat)

### Rhythm Parameters — 短剧 特定新增
- **cut_density**(平台特定,见上 Rhythm Parameters — Cut-Density Windows)
- **avg_shot_length**(平台特定,见上)
- **dead_air_max**: ≤ 3s per shot,例外条件(emotional climax / BGM swell / scene establishment / thematic long take)允许 ≤ 4-5s(per [`references/cn-cutting-rhythm.md`](./references/cn-cutting-rhythm.md) §≤3s Dead Air Rule)
- **build_to_climax_multiplier**: 最后 25% runtime 的 cut 密度 = 1.5-2.0x baseline(per [`references/classical-editing-rhythm.md`](./references/classical-editing-rhythm.md) §Build-to-Climax Rule)
- **bgm_alignment_rate**: ≥ 70% cuts 对齐 BGM beat(per [`references/cn-cutting-rhythm.md`](./references/cn-cutting-rhythm.md) §BGM-Driven Cut Sync)
- **击中点_alignment_rate**: 100% 击中点 align 在 cut 或 motion transition(per [`references/cn-cutting-rhythm.md`](./references/cn-cutting-rhythm.md) §击中点 Cut Alignment)
- **viewer_fatigue_threshold**: 持续 > 30 cuts/min 不超过 60s(per [`references/murch-rule-of-six.md`](./references/murch-rule-of-six.md) §Blink Rhythm Theory)

### Transition Parameters(unchanged from Phase 0)
- **hard_cut**: 0 frames
- **dissolve**: 12-24 frames (0.5-1.0s @24fps)
- **overlap**: 6-12 frames (match cut,per [`references/fxrxt-axis-compliance.md`](./references/fxrxt-axis-compliance.md) §Match Cut Design)
- **wipe**: 24-36 frames (stylized only)
- **fade_in/out**: 24-48 frames (scene boundaries)

### Axis Detection — 量化阈值(per [`references/fxrxt-axis-compliance.md`](./references/fxrxt-axis-compliance.md))
- **axis_threshold_180**: angle delta > 180° = 零容忍违反(violation)
- **axis_threshold_30**: angle delta < 30° = jump-cut 风险(除非 jump_cut_intentional=true)
- **eyeline_match_threshold**: 方向差 > 45° = eyeline 违反
- **neutral_shot_types**: frontal, profile, overhead (safe axis transition,per [`references/fxrxt-axis-compliance.md`](./references/fxrxt-axis-compliance.md) §轴线合规的修复策略)
- **axis_violation_count_target**: 0 per scene(零容忍)

### Composition Continuity
- **subject_position_tolerance**: ±15%
- **eye_line_match**: ±5°(横屏);竖屏收紧(详见 [`references/fxrxt-axis-compliance.md`](./references/fxrxt-axis-compliance.md) §Eyeline Match)
- **screen_direction**: consistent horizontal movement direction

### Audio-Visual Sync
- **L-cut**: dialogue leads 0.3-0.8s before visual cut
- **J-cut**: visual cuts 0.2-0.5s before dialogue
- **sync_tolerance**: ±2 frames (~83ms @24fps)

### GPU Budget
- Video decode/encode: ~3GB | Axis analysis: CPU | Total: <= 5GB

## Style Rules

### FxRxT Matrix
- **F (Frame)**: ECU/CU/MS/MLS/WS/EWS/POV/OTS(详见 [`../../_shared/glossary.md`](../../_shared/glossary.md#景别-shot-size-shot-scale))
- **R (Rhythm)**: static/gradual/accelerating/decelerating/jump_cut
- **T (Transition)**: cut/dissolve/overlap/wipe/match_cut

### Y/L/C/S Cross-Library
- **Y (Tempo)**: matched to emotion_curve + platform cut-density window(见 Key Parameters — Rhythm Parameters — Cut-Density Windows)
- **L (Transition)**: hard=0f, dissolve=12-24f, dissolve_long=24-48f
- **C (Composition)**: subject position deviation <= 15% between shots + eye-trace 帧位移 ≤ 30%(横屏)/ ≤ 27%(竖屏收紧 10%,per [`references/murch-rule-of-six.md`](./references/murch-rule-of-six.md) §Eye-Trace Quantification)
- **S (Narrative)**: key dialogue uses L-cut or J-cut (max 2 per scene)

### Rhythm by Scene Type — 短剧 平台特定(per [`references/cn-cutting-rhythm.md`](./references/cn-cutting-rhythm.md) §Cut-Density Windows by Platform/Genre)
- **抖音-男频 revenge**: 0.5-2.0s/shot(action 密集,cut on action 为主)
- **抖音-女频 romance**: 2.0-3.0s/shot(emotional breathing room 多)
- **快手-草根 slice-of-life**: 2.5-4.5s/shot(草根真实感,慢节奏)
- **小程序剧 180s drama**: 2.0-3.0s/shot(长集叙事,中等密度)

### Axis Rules — 量化(per [`references/fxrxt-axis-compliance.md`](./references/fxrxt-axis-compliance.md))
- Establish axis from first two-person shot camera-target line
- 180° angle delta > 180° = 零容忍违反(必须修复)
- 30° angle delta < 30° = jump-cut 风险(除非 intentional)
- Eyeline 方向差 > 45° = 违反
- Axis cross requires neutral shot transition (frontal/profile/overhead)
- Moving camera resets axis automatically

### Prohibited
- **180° 轴线违反**(零容忍,per [`references/fxrxt-axis-compliance.md`](./references/fxrxt-axis-compliance.md) §180° Axis Rule)
- Unmotivated jump cuts (unless stylized + jump_cut_intentional=true 标注)
- > 3s continuous hard cuts without rhythm variation 或 dead_air_exception(per [`references/cn-cutting-rhythm.md`](./references/cn-cutting-rhythm.md) §≤3s Dead Air Rule)
- L-cut/J-cut abuse (max 2 per scene)
- Cuts severely out of sync with coupled_beat (bgm_alignment_rate < 70%,per [`references/cn-cutting-rhythm.md`](./references/cn-cutting-rhythm.md) §BGM-Driven Cut Sync)
- 击中点 misaligned(在 mid-static-shot 中,per [`references/cn-cutting-rhythm.md`](./references/cn-cutting-rhythm.md) §击中点 Cut Alignment)
- emotion ≤ 3.0 的 cut(Emotion-First 否决,per [`references/murch-rule-of-six.md`](./references/murch-rule-of-six.md) §Emotion-First Decision Rule)

## Workflow

1. **Knowledge Retrieval** — 若有 memory/RAG 工具,查询 5 个检索主题(tags="expert:editor");若无,回退 `references/*.md`(见 §Knowledge Retrieval)
2. **Rhythm Planning** — Determine per-scene editing rhythm from emotion_curve + coupled_beat + 平台 cut-density window(见 Key Parameters — Rhythm Parameters — Cut-Density Windows)
3. **FxRxT Assignment** — Assign F (Frame) / R (Rhythm) / T (Transition) per shot;标注 segment_type + montage_method
4. **Murch Rule of Six Scoring** — 对每个候选 cut,按 6 维度评分并计算 murch_score;触发 Emotion-First 豁免 / 否决逻辑(per [`references/murch-rule-of-six.md`](./references/murch-rule-of-six.md) §Murch Score Calculation)
5. **Axis Establishment** — Set 180° axis from first two-person frame;消费 cinematographer (Phase 17 v3.0: was scene_builder composition_lock sub-task) axis_data(若存在)
6. **Shot Ordering** — Arrange shot sequence by narrative logic + rhythm + 击中点 alignment
7. **Transition Design** — Determine transition type and duration between shots;match cut 优先在场景转换处
8. **L/J-cut Marking** — Design audio lead/lag for key dialogue
9. **BGM Sync** — 对齐 cut 时机与 audio_pipeline.composer.coupled_beat.json 的 BGM beat;验证 bgm_alignment_rate ≥ 70%
10. **击中点 Alignment** — 验证每个 击中点 align 在 cut 或 motion transition(不是 mid-static-shot)
11. **Axis Audit** — Per-shot axis compliance check: 180° / 30° / eyeline 验证;输出 axis_check_report
12. **Rhythm Verification** — Validate edit rhythm alignment with coupled_beat (±100ms) + build-to-climax 倍数(1.5-2x)+ dead air 例外条件验证
13. **Output EDL** — Generate `edit_decision_list.json` (with murch_score + segment_type + montage_method + bgm_aligned) + `beat_timeline.json` + `axis_check_report`

## Quality Thresholds

| Metric | Production Minimum | Source |
|--------|-------------------|--------|
| `rhythm_accuracy` | cut alignment with BGM coupled_beat(bgm_alignment_rate ≥ 70%)+ 击中点 cut alignment(100%)+ 1.5x pace rule adherence + build-to-climax 1.5-2x + dead_air_max ≤ 3s 的综合评分,目标 ≥ 0.85 | [`references/cn-cutting-rhythm.md`](./references/cn-cutting-rhythm.md) §BGM-Driven Cut Sync + §击中点 Cut Alignment + §1.5x Pace Rule + §≤3s Dead Air Rule + [`references/classical-editing-rhythm.md`](./references/classical-editing-rhythm.md) §Build-to-Climax Rule |
| `continuity_match` | match cut 质量 + eyeline match(方向差 ≤ 45°)+ 180° axis compliance(angle delta ≤ 180°)+ 30° rule(angle delta ≥ 30°除非 intentional),目标 ≥ 0.80 | [`references/fxrxt-axis-compliance.md`](./references/fxrxt-axis-compliance.md) §Match Cut Design + §Eyeline Match + §180° Axis Rule + §30° Rule |
| `axis_violation_count` | 180° violations + 30° violations(非 intentional)+ eyeline mismatches 总和 = 0(零容忍)。违反量化:180° angle delta > 180°;30° angle delta < 30°;eyeline 方向差 > 45° | [`references/fxrxt-axis-compliance.md`](./references/fxrxt-axis-compliance.md) §Axis Compliance 自检工作流 |
| `transition_smoothness` | Murch Rule of Six compliance —— Emotion-First cut decision(emotion ≥ 8.0 豁免 / emotion ≤ 3.0 否决)+ eye-trace 帧位移 ≤ 30%(横屏)/ ≤ 27%(竖屏收紧 10%)+ cut on action 应用率,murch_score avg ≥ 7.0,目标 ≥ 0.88 | [`references/murch-rule-of-six.md`](./references/murch-rule-of-six.md) §Emotion-First Decision Rule + §Eye-Trace Quantification + §加权评分计算公式 + [`references/classical-editing-rhythm.md`](./references/classical-editing-rhythm.md) §Cut on Action |

## Collaboration

- **<- screenplay**: shot_count, rhythm intent, scene structure, emotion_curve(含 hooks[] / payoffs[] / cliffhangers[] 数组,Phase 2 HOOK-09 合同)
- **<- visual_executor**: video clips (per-shot MP4) + focal_point 字段(用于 eye-trace 计算)
- **<- audio_pipeline (composer sub-step)**: coupled_beat.json(用于 BGM-driven cut sync)+ light_beat.json
- **<- audio_pipeline (voicer sub-step)**: dialogue timeline (L/J-cut reference)
- **<- continuity_auditor**: consistency report (reject failed frames)
- **<- cinematographer (replaces deprecated Phase 17 scene_builder; composition_lock sub-task)**: axis_data(180° 轴线定义 + 摄影机位置;editor 负责 compliance,cinematographer composition_lock 子任务负责 feasibility)
- **<- hook_retention**: 击中点 / 爽点 / 卡点 markers(用于 cut alignment 验证)
- **-> audio_pipeline (composer sub-step)**: final cut points (adjust coupled_beat)
- **-> audio_pipeline (mixer sub-step)**: post-edit audio timeline
- **-> continuity_auditor**: edited shot sequence for final audit
- **-> hook_retention**: cut list 中的 击中点 / 爽点 / 卡点 cut alignment 验证结果

## What NOT to do

- Don't tolerate any axis violations (零容忍 policy —— 180° 轴线违反必须否决,即使 emotion = 10/10)
- Don't exceed 2 L-cut/J-cut per scene
- Don't cut faster than 0.5s per shot without action justification + cut on action
- Don't ignore audio_pipeline (composer sub-step)'s coupled_beat timestamps(bgm_alignment_rate 必须 ≥ 70%)
- Don't assemble without continuity pass approval
- Don't apply metric montage fast(every 24 frames)持续超过 10 秒(viewer-fatigue 阈值)
- Don't define numeric thresholds in SKILL.md body —— cite the ref §section instead(Phase 1 CR-01 single-source-of-truth rule)
- Don't hardcode provider-specific tool names(`fact_store` / `mem0_search` / etc.)—— use `<memory_plugin>` / `<rag_search>` placeholders(per [`../_shared/RAG-INVOCATION-PATTERN.md`](../_shared/RAG-INVOCATION-PATTERN.md))
- Don't modify `expert_id: editor` (FOUND-08 HARD RULE — frozen identifier)
- Don't use uniform cut density across entire episode —— build-to-climax 要求最后 25% runtime 加密 1.5-2x
- Don't mix Murch Story weighting 23% with 25% across files —— 2nd ed (2001) canonical is 23%(per [`references/murch-rule-of-six.md`](./references/murch-rule-of-six.md) §2nd ed vs 早期引用 差异说明,T-03-07 mitigation)
