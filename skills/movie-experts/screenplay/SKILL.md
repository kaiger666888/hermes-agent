---
name: screenplay
description: "Screenplay Expert: scene-level script generation, dialogue design, emotional arc construction for AI short film production."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, screenplay, script, dialogue, narrative, emotion-curve]
    related_skills: [style_genome, scene_builder, editor, performer, composer, compliance_marketing, hook_retention, cinematographer]
    expert_id: screenplay
    metrics: [narrative_tension, dialogue_naturalness, emotional_arc]
---

# Screenplay Expert (剧本专家)

Narrative structure specialist for scene-level script generation, dialogue design, and emotional arc construction in AI short film production (60-180 seconds per episode; 10-80 episode serialized format for 短剧 / 小程序剧).

## When to use this skill

The user needs to write a script, design dialogue, plan emotional arcs, generate scene structures, or create `script.json` for AI film production. Typically the first expert invoked after `style_genome`. Also invoked when designing multi-episode 短剧 arcs with [付费卡点](../../_shared/glossary.md#付费卡点-paid-conversion-trigger) placement, or when integrating [钩子](../../_shared/glossary.md#钩子-hook) / [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) / [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) markers for the `hook_retention` expert (Phase 2 HOOK-09 contract).

## References

本专家所有数值阈值由下列 5 个 refs 独占定义;SKILL.md body 仅作摘要 + 跨链,不重新给出数字原理(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) 教训)。

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/save-the-cat-beat-sheet.md`](./references/save-the-cat-beat-sheet.md) | 设计任何 短剧 单集结构前 | Snyder 15-beat 节拍表(Catalyst p.10±3 / Midpoint p.55±3 / All Is Lost p.75±3)+ Save the Cat 时刻定义 + 短剧 60s/90s/180s beat budget 换算表 + Double-Bump 连续触发规则 |
| [`references/mckee-scene-design.md`](./references/mckee-scene-design.md) | 设计任何场景的戏剧密度前 | McKee gap(期望-结果鸿沟)4 步解析 + value-shift rate ≥ 1 per scene + beat decomposition 3-5 per 90s scene + turning point vs plot point(~25% & ~75% runtime) |
| [`references/cn-shortdrama-structure.md`](./references/cn-shortdrama-structure.md) | 设计 短剧 多集 season arc 或 per-platform 结构前 | 90s/180s 短剧 时间预算(钩子 0-3s / escalation 15-40s / 爽点 70-80s / 卡点 88-90s)+ 10-ep season arc(ep 3/7/10 大 爽点)+ per-platform divergence(抖音/快手/小程序剧) |
| [`references/emotion-curve-academic.md`](./references/emotion-curve-academic.md) | 设计 emotion_curve 或采样协议前 | Tan interest 公式(concern × uncertainty × anticipation ≥ 0.6)+ McMahon 6 arc 形状(85% 覆盖率)+ anchor-based 采样协议(信噪比 +30% vs uniform)+ 注意力衰减曲线(8-12s 无 击中点 则 drops ≥15%) |
| [`references/dialogue-craft.md`](./references/dialogue-craft.md) | 写任何台词前 | 台词密度阈值(男频 0.4-0.6 / 女频 0.5-0.7 / ≥0.8 = 旁白过度 anti-pattern)+ 潜台词比例 ≥ 60% + "as you know" CN anti-pattern 3-strike 规则 + per-platform register(抖音/快手/小程序剧) |

## Role & Philosophy

- Cinematic storytelling within 60-180 second per-episode constraints (短剧 multi-episode format)
- Every line of dialogue serves dual purpose: character revelation + plot advancement (subtext ratio ≥ 60%, per [`references/dialogue-craft.md`](./references/dialogue-craft.md) §Subtext Ratio Rule)
- Emotion curves drive every visual and audio decision downstream — sampled at anchor points (beat transitions / value shifts / hook-pin / 爽点 payoff / 卡点 cliffhanger), NOT uniform 0.5s intervals (per [`references/emotion-curve-academic.md`](./references/emotion-curve-academic.md) §Anchor-Based Sampling Protocol)
- Every scene MUST shift at least one value (McKee rule, per [`references/mckee-scene-design.md`](./references/mckee-scene-design.md) §Value-Shift Rule) — no value-shift = filler scene
- Snyder beat structure adapted to 短剧 runtime (Catalyst ~9s for 90s / Midpoint ~45s / All Is Lost ~67s, per [`references/save-the-cat-beat-sheet.md`](./references/save-the-cat-beat-sheet.md) §短剧 Adaptation)

## Knowledge Retrieval

在生成任何 script / dialogue / emotion_curve 输出前,按以下顺序检索上下文(5 个检索主题):

- **Snyder 15-beat 节拍表适配 短剧 60-180s 形态**(Catalyst / Midpoint / All Is Lost 位置 + Save the Cat 时刻 + Double-Bump 规则)—— 详见 [`references/save-the-cat-beat-sheet.md`](./references/save-the-cat-beat-sheet.md)
- **McKee 场景设计理论**(gap 4 步解析 + value-shift rate ≥ 1 per scene + beat decomposition 3-5 per 90s + turning point vs plot point)—— 详见 [`references/mckee-scene-design.md`](./references/mckee-scene-design.md)
- **CN 短剧 多集结构 + per-platform divergence**(90s/180s 时间预算 + 10-ep season arc + 抖音/快手/小程序剧 分化)—— 详见 [`references/cn-shortdrama-structure.md`](./references/cn-shortdrama-structure.md)
- **emotion_curve anchor-based 采样协议**(Tan interest 三因素 + McMahon 6 arcs + 注意力衰减曲线)—— 详见 [`references/emotion-curve-academic.md`](./references/emotion-curve-academic.md)
- **CN 短剧 台词工艺**(密度阈值 + 潜台词比例 + "as you know" anti-pattern + per-platform register)—— 详见 [`references/dialogue-craft.md`](./references/dialogue-craft.md)

**若当前 runtime 中有 memory / RAG 工具**(例如 `<memory_plugin>` / `<rag_search>` 或类似检索工具,具体工具名由 runtime 决定),使用以下查询范围:

```
tags="expert:screenplay,domain:save-the-cat-beat-sheet"
tags="expert:screenplay,domain:mckee-scene-design"
tags="expert:screenplay,domain:cn-shortdrama-structure"
tags="expert:screenplay,domain:emotion-curve-academic"
tags="expert:screenplay,domain:dialogue-craft"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件(以 `## References` 表为准)。静态 refs 是权威源,memory 插件只是更大语料的优化。provider-agnostic 检索是 ablation eval 与多 provider 部署的硬约束。

> **NOTE:** 本 SKILL.md body 不引用任何具体外部模型名。涉及具体模型时使用 `<llm_primary>` / `<llm_fallback>` 占位符(见 [`../_shared/RAG-INVOCATION-PATTERN.md`](../_shared/RAG-INVOCATION-PATTERN.md) placeholder 表)。模型名只出现在 `references/*.md` 与 [`../_shared/known-external-models.yaml`](../_shared/known-external-models.yaml) allowlist 中。

## Core Capabilities

- Three-act micro-structure compression (setup/payoff in seconds) — Snyder beat model adapted to 短剧 runtime
- Subtext-heavy dialogue writing (show don't tell) — subtext ratio ≥ 60% per [`references/dialogue-craft.md`](./references/dialogue-craft.md) §Subtext Ratio Rule
- Scene-level pacing and tension modulation — value-shift rate ≥ 1 per scene per [`references/mckee-scene-design.md`](./references/mckee-scene-design.md) §Value-Shift Rule
- Sound mood and lighting mood annotation for downstream experts
- Emotion curve generation at anchor points (beat transitions / value shifts / hook-pin / 爽点 payoff / 卡点 cliffhanger) per [`references/emotion-curve-academic.md`](./references/emotion-curve-academic.md) §Anchor-Based Sampling Protocol
- Multi-episode 短剧 season arc design (ep 3/7/10 大 [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) placement) per [`references/cn-shortdrama-structure.md`](./references/cn-shortdrama-structure.md) §10-Episode Season Arc
- [钩子](../../_shared/glossary.md#钩子-hook) / [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) / [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) marker output (with multi-episode callback support) — Phase 2 HOOK-09 contract closure

## Output Format

`script.json` with `scenes[]` array. Each scene contains:
- `shot_count`, `emotion_curve` (anchor-based samples + hooks/payoffs/cliffhangers arrays — see §Emotion Curve Hooks / Payoffs / Cliffhangers below)
- `dialogue[]`, `sound_mood`, `lighting_mood`
- `beat_count` (3-5 per 90s scene per [`references/mckee-scene-design.md`](./references/mckee-scene-design.md) §Beat Decomposition)
- `value_shifts[]` (≥ 1 per scene per [`references/mckee-scene-design.md`](./references/mckee-scene-design.md) §Value-Shift Rule)

## Key Parameters

### LLM Generation
- **model**: `<llm_primary>` (any high-quality chat model with ≥ 8K context; if `<llm_primary>` available, use it; otherwise `<llm_fallback>` — see [`../_shared/known-external-models.yaml`](../_shared/known-external-models.yaml) for current catalog)
- **temperature**: 0.7-0.9 (creative writing)
- **max_tokens**: 4096 (full scene), 1024 (dialogue-only)
- **top_p**: 0.9

### Emotion Curve
- **sampling_mode**: anchor-based (primary) — sample at beat transitions / value shifts / hook-pin / [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) payoff / [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) cliffhanger per [`references/emotion-curve-academic.md`](./references/emotion-curve-academic.md) §Anchor-Based Sampling Protocol
- **uniform_fallback**: 0.5s intervals permitted for low-budget fallback but documented as ~30% higher noise than anchor-based (per [`references/emotion-curve-academic.md`](./references/emotion-curve-academic.md) §Anchor-Based vs Uniform Sampling)
- **value_range**: 0.0 (neutral) to 1.0 (peak)
- **anchor_count**: ~15-25 per 90s episode (3-5 beat transitions × avg scenes + 1 hook + 1-2 爽点 + 1 卡点)

### Scene Budgets
- **total_runtime**: 60-180 seconds per episode (per [`references/cn-shortdrama-structure.md`](./references/cn-shortdrama-structure.md) §Per-Platform Divergence)
- **scene_count**: 3-8 scenes for 90s format / 6-15 scenes for 180s format (per [`references/cn-shortdrama-structure.md`](./references/cn-shortdrama-structure.md) §90s/180s 短剧 Time Budget)
- **shots_per_scene**: 3-8
- **dialogue_density**: genre-specific — revenge 0.4-0.6 lines/sec / romance 0.5-0.7 lines/sec / ≥ 0.8 = [旁白过度](../../_shared/glossary.md) anti-pattern (per [`references/dialogue-craft.md`](./references/dialogue-craft.md) §Density Thresholds by Genre)

### Emotion Curve Hooks / Payoffs / Cliffhangers

本节是 Phase 2 HOOK-09 合同的 **load-bearing 扩展** —— `emotion_curve` schema 新增 `hooks[]` / `payoffs[]` / `cliffhangers[]` 三个数组,消费 [`../hook_retention/SKILL.md`](../hook_retention/SKILL.md) §Marker Schema 定义的 marker。字段名、字段顺序、字段语义固定,不允许修改(T-03-01 threat mitigation)。

```json
"emotion_curve": {
  "samples": [
    {"t": "MM:SS.s", "v": 0.0-1.0}
  ],
  "hooks": [
    {
      "type": "情感钩|悬念钩|冲突钩|反差钩|情绪爆点钩",
      "timestamp": "MM:SS",
      "intensity_1_5": 1-5
    }
  ],
  "payoffs": [
    {
      "timestamp": "MM:SS",
      "intensity_1_5": 1-5,
      "setup_callback": "S1E03 02:15 — 主角在病床前发誓复仇"
    }
  ],
  "cliffhangers": [
    {
      "tier": "🟢|🟡|🔴",
      "timestamp": "MM:SS",
      "payoff_callback": "S1E0N+1 opening"
    }
  ]
}
```

**字段语义:**

- **samples[]** — emotion_curve 的采样点(anchor-based 或 uniform_fallback)。每个元素 `{t: "MM:SS.s", v: 0.0-1.0}`。这是原始 Phase 0 schema,未修改。
- **hooks[]** — 开场 [钩子](../../_shared/glossary.md#钩子-hook) marker 数组。每个元素包含:
  - `type`: 5-type taxonomy 之一(情感钩 / 悬念钩 / 冲突钩 / 反差钩 / 情绪爆点钩,见 [`../hook_retention/references/three-second-hooks.md`](../hook_retention/references/three-second-hooks.md) §Taxonomy)
  - `timestamp`: `MM:SS` 格式(本集内时间)
  - `intensity_1_5`: 1-5 整数(对应 [`../hook_retention/references/conflict-escalation.md`](../hook_retention/references/conflict-escalation.md) 1-10 尺度折半;5 = 🎯 bullseye)
- **payoffs[]** — [爽点](../../_shared/glossary.md#爽点-satisfaction-beat) 兑现 marker 数组。每个元素包含:
  - `timestamp`: `MM:SS` 格式(本集内时间)
  - `intensity_1_5`: 1-5 整数(5 = 爽点 峰值)
  - `setup_callback`: 自由字符串,**可跨集回指**(例如 `"S1E03 02:15 — 主角在病床前发誓复仇"`)—— 这是 HOOK-09 合同的核心 multi-episode callback 机制
- **cliffhangers[]** — [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) cliffhanger marker 数组。每个元素包含:
  - `tier`: 🟢 must-watch-next / 🟡 curious-but-skippable / 🔴 weak-resolve(见 [`../hook_retention/references/paywall-design.md`](../hook_retention/references/paywall-design.md) §3-Tier Strength)
  - `timestamp`: `MM:SS` 格式(通常在集末 88-90s for 90s format)
  - `payoff_callback`: 自由字符串,**可跨集前瞻**(例如 `"S1E0N+1 opening"` 或 `"S1E07 — 反派真实身份揭露"`)

**与 hook_retention 的集成:** `hooks[]` / `payoffs[]` / `cliffhangers[]` 数组的元素与 [`../hook_retention/SKILL.md`](../hook_retention/SKILL.md) §Marker Schema 的 marker 格式对齐(但 `type` 字段简化:HOOK marker 的 `type` 是 "钩子|爽点|卡点",本 schema 按 array 分离所以不需要 `type`)。跨集 callback 通过 `setup_callback` / `payoff_callback` 字符串中的 `S1E0X MM:SS` 形式承载(与 HOOK marker schema 一致)。

## Style Rules

### Narrative Standards
- Opening [钩子](../../_shared/glossary.md#钩子-hook) within first 3 seconds (per [`references/cn-shortdrama-structure.md`](./references/cn-shortdrama-structure.md) §90s 短剧 Time Budget: 0-3s 钩子段)
- Each scene has a clear dramatic question AND at least 1 value-shift (McKee rule, per [`references/mckee-scene-design.md`](./references/mckee-scene-design.md) §Value-Shift Rule)
- Ending resolves or subverts the opening hook (Final Image ↔ Opening Image 对照, per [`references/save-the-cat-beat-sheet.md`](./references/save-the-cat-beat-sheet.md) §Beat Budget 验证清单)
- Catalyst at ~10% runtime (90s: ~9s / 180s: ~18s / 60s: ~6s, per [`references/save-the-cat-beat-sheet.md`](./references/save-the-cat-beat-sheet.md) §短剧 Adaptation)

### Dialogue Quality
- Subtext ratio: minimum 60% implicit meaning per line (per [`references/dialogue-craft.md`](./references/dialogue-craft.md) §Subtext Ratio Rule)
- Maximum 3 lines per 10-second scene (visual storytelling priority)
- Ban expository "as you know" CN anti-patterns (3-strike rule per [`references/dialogue-craft.md`](./references/dialogue-craft.md) §"As You Know" CN Anti-Pattern)
- Vernacular register matching character background AND platform (per [`references/dialogue-craft.md`](./references/dialogue-craft.md) §Per-Platform Register Divergence)

### Emotional Arc Rules
- Minimum 3 distinct emotional phases per scene
- Tension curve never flat for >2 seconds
- Emotional peak at 70-85% of scene duration (per [`references/cn-shortdrama-structure.md`](./references/cn-shortdrama-structure.md) §90s 短剧 Time Budget: 爽点 payoff 70-80s)
- Recovery/cool-down: final 15-30%
- Arc shape identified as 1 of 6 McMahon arcs (per [`references/emotion-curve-academic.md`](./references/emotion-curve-academic.md) §6 Core Emotional Arcs)

### Prohibited Patterns
- Voice-over narration as plot crutch ([旁白过度](../../_shared/glossary.md) anti-pattern, per [`references/dialogue-craft.md`](./references/dialogue-craft.md) §"As You Know" CN Anti-Pattern 变体 2)
- Characters explaining their own emotions explicitly (anti-pattern 变体 3)
- Static "talking heads" without visual activity
- Deux ex machina resolutions without setup
- Scenes with 0 value-shifts (filler, per [`references/mckee-scene-design.md`](./references/mckee-scene-design.md) §Value-Shift Rule)

## Workflow

1. **Knowledge Retrieval** — 若有 memory/RAG 工具,查询 5 个检索主题(tags="expert:screenplay");若无,回退 `references/*.md`(见 §Knowledge Retrieval)
2. **Beat Planning** — Generate scene-level beat sheet using Snyder 15-beat model adapted to 短剧 runtime (per [`references/save-the-cat-beat-sheet.md`](./references/save-the-cat-beat-sheet.md) §短剧 Adaptation)
3. **Structure Validation** — Check Catalyst / Midpoint / All Is Lost positions; verify value-shift rate ≥ 1 per scene (per [`references/mckee-scene-design.md`](./references/mckee-scene-design.md) §Value-Shift Rule)
4. **Dialogue Draft** — Write dialogue with subtext annotations; verify density within genre range + subtext ratio ≥ 60% (per [`references/dialogue-craft.md`](./references/dialogue-craft.md))
5. **Mood Annotation** — Assign `sound_mood` and `lighting_mood` per scene
6. **Emotion Curve** — Generate per-scene `emotion_curve` at anchor points; populate `hooks[]` / `payoffs[]` / `cliffhangers[]` arrays per HOOK-09 contract (see §Emotion Curve Hooks / Payoffs / Cliffhangers)
7. **Self-Review** — LLM check on `dialogue_naturalness` (subtext ratio + "as you know" 3-strike + density), remove exposition dumps
8. **Format Output** — Assemble `script.json`

## Quality Checkpoints

- [ ] Every scene has a clear dramatic question + ≥ 1 value-shift
- [ ] Dialogue subtext ratio >= 60% + "as you know" 3-strike count ≤ 2
- [ ] Emotion arc >= 3 phases per scene + arc shape identified (1 of 6 McMahon arcs)
- [ ] `sound_mood` and `lighting_mood` populated for every scene
- [ ] Total runtime within 60-180s budget per episode
- [ ] No forbidden patterns
- [ ] `emotion_curve.hooks[]` / `payoffs[]` / `cliffhangers[]` arrays populated (HOOK-09 contract)
- [ ] Catalyst at ~10% runtime / Midpoint at ~50% / All Is Lost at ~68% (per [`references/save-the-cat-beat-sheet.md`](./references/save-the-cat-beat-sheet.md))

## Quality Thresholds

| Metric | Production Minimum | Source |
|--------|-------------------|--------|
| `narrative_tension` | McKee value-shift rate ≥ 1 per scene + Snyder Midpoint polarity reversal present | [`references/mckee-scene-design.md`](./references/mckee-scene-design.md) §Value-Shift Rule + [`references/save-the-cat-beat-sheet.md`](./references/save-the-cat-beat-sheet.md) §The 15 Beats |
| `dialogue_naturalness` | Subtext ratio ≥ 60% per line + zero "as you know" CN anti-pattern (3-strike count ≤ 2) + density within genre range | [`references/dialogue-craft.md`](./references/dialogue-craft.md) §Subtext Ratio Rule + §"As You Know" CN Anti-Pattern + §Density Thresholds by Genre |
| `emotional_arc` | Tan interest score ≥ 0.6 per scene (concern × uncertainty × anticipation) + arc shape identified (1 of 6 McMahon arcs) + anchor points sampled | [`references/emotion-curve-academic.md`](./references/emotion-curve-academic.md) §Tan's Interest Structure + §6 Core Emotional Arcs + §Anchor-Based Sampling Protocol |
| `scene_duration` | 3-15s per shot | (unchanged from Phase 0) |

## Collaboration

- **<- style_genome**: `style_correction` to adapt tone/genre
- **<- hook_retention**: 接收 `钩子_爽点_卡点_markers.json` 给 `emotion_curve` 离散锚点集成(HOOK-09 合同闭环 —— `hooks[]` / `payoffs[]` / `cliffhangers[]` 数组消费 HOOK marker)
- **-> scene_builder**: scenes[] with camera-ready descriptions, `lighting_mood`
- **-> editor**: shot_count estimates, rhythm intent, cross-reference IDs
- **-> performer**: emotion per shot, character psychology annotations
- **-> composer**: `sound_mood` per scene, coupled_beat hints
- **-> hook_retention**: 输出 `emotion_curve.hooks[]` / `payoffs[]` / `cliffhangers[]` 供 HOOK marker 对齐验证(双向 edge —— HOOK 设计 marker,screenplay 消费 marker,形成闭环)

## What NOT to do

- Don't generate scripts without runtime constraints (always 60-180s per episode)
- Don't skip emotion_curve — it's the backbone for all downstream experts
- Don't write dialogue-only; every scene needs `sound_mood` and `lighting_mood`
- Don't use temperature > 0.9 for creative writing (loses coherence)
- Don't skip the self-review pass (catches exposition dumps)
- Don't use uniform 0.5s emotion_curve sampling as primary mode — anchor-based is primary; uniform is fallback only (per [`references/emotion-curve-academic.md`](./references/emotion-curve-academic.md) §Anchor-Based Sampling Protocol)
- Don't hardcode provider-specific tool names (`fact_store` / `mem0_search` / etc.) — use `<memory_plugin>` / `<rag_search>` placeholders (per [`../_shared/RAG-INVOCATION-PATTERN.md`](../_shared/RAG-INVOCATION-PATTERN.md))
- Don't redefine numeric thresholds in SKILL.md body — cite the ref §section instead (Phase 1 CR-01 single-source-of-truth rule)
- Don't modify `expert_id: screenplay` (FOUND-08 HARD RULE — frozen identifier)
