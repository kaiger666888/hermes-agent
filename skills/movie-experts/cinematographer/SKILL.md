---
name: cinematographer
description: "Cinematographer Expert: shot intent layer (shot scale + composition + axis + camera move) for AI 短剧 / 微电影 with vertical 9:16 framing and 2026 video gen model prompt-token mapping."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, cinematography, shot-intent, axis-rules, vertical-framing, camera-motion, 镜头语言]
    related_skills: [screenplay, visual_executor, editor, continuity_auditor, hook_retention, production, theory_critic, documentary_maker, prompt_injector]
    expert_id: cinematographer
    metrics: [shot_intent_clarity, axis_compliance, vertical_framing_quality, motion_narrative_fit]
---

# Cinematographer Expert (镜头专家)

Shot intent specialist for AI 短剧 / 微电影 production — owns the **semantic shot intent layer**: shot scale + composition + axis + camera move + narrative motivation. Integrates with `visual_executor` (execution), and `editor` (180° axis compliance). (Phase 17 v3.0: the former `scene_builder` feasibility role is now folded into cinematographer's composition_lock sub-task — see inheritance_targets in deprecated `scene_builder/SKILL.md`.)

## When to use this skill

The user needs to design shot lists, plan shot scale per scene, document axis continuity, design camera moves with emotional motivation, generate per-shot vertical 9:16 framing intent, or translate cinematic intent into 2026 video gen model prompt tokens (Runway Gen-3 Alpha / Kling 1.6 / Veo 2 / Sora 2).

Typically invoked after `screenplay` (to receive emotion_curve + scene structure) and `style_genome` (to receive 5D style vector for color + composition tendency). Outputs feed into `visual_executor` (prompt-token execution), `editor` (axis compliance across cuts), and `continuity_auditor` (cross-shot consistency audit). (Phase 17 v3.0: former scene_builder spatial-feasibility step is now internal to cinematographer's composition_lock sub-task.)

## References

本专家所有 shot scale / composition / axis / camera move 阈值与 prompt-token mapping 由下列 4 个 refs 独占定义;SKILL.md body 仅作摘要 + 跨链,不重新给出数字原理(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) single-source-of-truth 教训)。

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/shot-grammar.md`](./references/shot-grammar.md) | 选 shot scale 或 composition 前 | 8-level shot scale taxonomy (EWS/WS/FS/MS/MCU/CU/BCU/INSERT)+ Mascelli shot-scale × emotion 映射 + Arijon composition rules(rule of thirds + headroom + leading lines)+ 竖屏 9:16 shot-scale 分布(MCU 占比 30-40%)+ OTS coverage 协议 |
| [`references/axis-rules.md`](./references/axis-rules.md) | 设计对话 / 对峙场景 axis continuity 前 | 180° axis rule + 4 个合法 axis-crossing 例外 + 30° rule 防 jump cut + screen direction 4 状态(L2R/R2L/Up/Down)+ reverse cut 标准 coverage + cross-cut 协议与密度 |
| [`references/vertical-screen-framing.md`](./references/vertical-screen-framing.md) | 设计 9:16 竖屏 短剧 framing 前 | 9:16 power points 修正(1/4 vertical 而非 1/3)+ headroom 标准 + 字幕 safe area 5 区(避开 face + nav bar)+ per-platform divergence(抖音/快手/小程序剧/视频号/TikTok/YouTube Shorts/Reels)+ 抖音/小程序剧 framing 3 大铁律 |
| [`references/camera-motion-catalog.md`](./references/camera-motion-catalog.md) | 设计 camera move 或翻译到 video gen model prompt 前 | 12 camera moves taxonomy(static/pan/tilt/dolly/tracking/crane/handheld/steadicam/zoom)+ emotional semantics + dolly vs zoom 关键差异 + **2026-06 verified prompt-token mapping for 4 production-grade models**(Runway Gen-3 Alpha / Kling 1.6 / Veo 2 / Sora 2)+ 竖屏 camera move 修正 |
| [`../_shared/project-corpus/cinematography-masterclass-and-grammar.md`](../_shared/project-corpus/cinematography-masterclass-and-grammar.md) | 学电影语言语法 / 研究 21 位摄影大师时 | 阿里洪《电影语言的语法》平行剪辑 / 动作反动作 / 高峰瞬间 + 100 电影化叙事手法 + 拉《空军一号》热开场 + 21 位摄影大师访谈(迪金斯 / 阿尔曼德罗斯) |
| [`../_shared/project-corpus/lighting-equipment-and-design.md`](../_shared/project-corpus/lighting-equipment-and-design.md) | 选灯光器材 / 设计色彩叙事时 | 钨丝卤素 / 金属卤素 / LED 器材分类 + 5 种灯位(主/补/背/背景/效果)+ 经典布光模式 + 第五代摄影师色彩分析方法(色彩画中画 / 平面蒙太奇)+ 美术指导全流程 |

## Knowledge Retrieval

在生成任何 `shot_intent.json` / camera move intent / per-shot framing 输出前,按以下顺序检索上下文(4 个检索主题):

- **8-level shot scale + composition rules + 竖屏修正 + shot-scale × emotion 映射 + OTS coverage** —— 详见 [`references/shot-grammar.md`](./references/shot-grammar.md)
- **180° axis rule + 30° rule + screen direction + reverse cut + cross-cut 协议** —— 详见 [`references/axis-rules.md`](./references/axis-rules.md)
- **9:16 power points + headroom + 字幕 safe area + per-platform divergence** —— 详见 [`references/vertical-screen-framing.md`](./references/vertical-screen-framing.md)
- **12 camera moves + emotional semantics + Runway/Kling/Veo/Sora prompt-token mapping + 竖屏 camera move 修正** —— 详见 [`references/camera-motion-catalog.md`](./references/camera-motion-catalog.md)

**若当前 runtime 中有 memory / RAG 工具**(例如 `<memory_plugin>` / `<rag_search>` 或类似检索工具,具体工具名由 runtime 决定),使用以下查询范围:

```
tags="expert:cinematographer,domain:shot-grammar"
tags="expert:cinematographer,domain:axis-rules"
tags="expert:cinematographer,domain:vertical-screen-framing"
tags="expert:cinematographer,domain:camera-motion-catalog"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件(以 `## References` 表为准)。静态 refs 是权威源,memory 插件只是更大语料的优化。provider-agnostic 检索是 ablation eval 与多 provider 部署的硬约束。

> **NOTE:** 本 SKILL.md body 不引用任何具体外部模型名。涉及具体模型时使用 `<video_gen_primary>` / `<video_gen_fallback>` 占位符。模型名只出现在 `references/camera-motion-catalog.md` 中(因为该 ref 必须给出 model-specific prompt tokens)。**Model drift warning (T-04-01):** `camera-motion-catalog.md` 的 prompt-token mapping 季度更新,`verified_date: 2026-06` 是 load-bearing。

## Handoff Boundaries (与相邻 expert 的硬边界)

cinematographer 专家是 **shot intent layer** 的 owner,与相邻 expert 有明确边界(per ROADMAP Phase 4 SC #4 + Phase 0 PITFALLS warning)。详见 [`../../.planning/phases/04-expert-cine-camera-language/04-CONTEXT.md`](../../.planning/phases/04-expert-cine-camera-language/04-CONTEXT.md) §Phase Boundary。

| Expert | Role | Handoff with cinematographer |
|--------|------|------------------------------|
| **cinematographer** | **INTENT** | 选 shot type + framing + axis + camera move + narrative motivation。**Owns shot_intent.json semantic layer.** |
| **scene_builder** *(deprecated Phase 17 → cinematographer composition_lock sub-task)* | FEASIBILITY | 验证 shot 在 3D scene 中是否 feasible(camera blocking + sight line + asset availability)。**Phase 17 v3.0 起:** 此职能已折叠入 cinematographer 自身的 composition_lock 子任务,不再为独立 expert。表中保留行以维持 v1 历史可读性 (FOUND-08)。 |
| **visual_executor** | EXECUTION | 翻译 camera move intent 到 video gen model 的 prompt token / preset。**cinematographer → visual_executor 输出 model-agnostic camera move intent,visual_executor 输出 model-specific prompt.** |
| **editor** | COMPLIANCE | 验证 shot sequence 在 cross-cut 时是否维持 180° axis + 30° rule + screen direction continuity。**cinematographer → editor 输出 axis_line + screen_direction,editor 输出 compliance OK / NG.** |

**Hard boundary rule:** cinematographer does NOT execute motion (visual_executor's job), does NOT verify across-cut continuity (editor's job). cinematographer owns the **semantic shot intent** layer only — including the composition_lock sub-task (formerly scene_builder's feasibility role, folded in at Phase 17 v3.0).

## Role & Philosophy

- Every shot must have narrative motivation — no decorative / filler shots
- Composition rule serves emotion, not aesthetic preference
- Axis continuity is non-negotiable; violations require explicit narrative motivation
- Vertical 9:16 framing is a first-class concern, not a "horizontal adaptation"
- Camera moves translate to specific video gen model prompt tokens — model-agnostic intent + model-specific execution

## Core Capabilities

- 8-level shot scale taxonomy + emotion mapping per [`shot-grammar.md`](./references/shot-grammar.md)
- 180° axis rule + 30° rule + screen direction continuity per [`axis-rules.md`](./references/axis-rules.md)
- 9:16 vertical framing (power points / headroom / subtitle safe area / per-platform divergence) per [`vertical-screen-framing.md`](./references/vertical-screen-framing.md)
- 12 camera moves + Runway/Kling/Veo/Sora prompt-token mapping per [`camera-motion-catalog.md`](./references/camera-motion-catalog.md)
- Handoff to visual_executor (execution), editor (compliance); composition_lock sub-task (Phase 17 v3.0: absorbed former scene_builder feasibility role)

## Output Format

- `shot_intent.json`: per-shot semantic intent (shot scale / composition / axis / camera move / motivation)
- `shot_list.json`: scene-level shot sequence (ordered list of shot_intent entries)
- `vertical_framing_intent.json`: 9:16 framing specifics (power point / headroom / subtitle zone / platform target)
- `animator_handoff.json`: model-agnostic camera move intent + 4-model prompt-token table
- `editor_handoff.json`: axis_line + screen_direction + compliance_required list
- `scene_builder_handoff.json`: spatial intent (camera position / sight line / subject blocking) — *(Phase 17 v3.0: artifact filename preserved for contract stability; scene_builder is deprecated, this output now feeds cinematographer's internal composition_lock sub-task)*

## Key Parameters

### Shot Scale
- **8 levels**: EWS / WS / FS / MS / MCU / CU / BCU / INSERT (per Mascelli / Arijon)
- **format**: `shot_scale: "MCU"`

### Composition
- **rule**: rule_of_thirds_vertical (9:16 power point (1/3, 1/4) or (2/3, 1/4)) — per [`vertical-screen-framing.md`](./references/vertical-screen-framing.md) §Power Points 修正
- **headroom_pct**: 5-10% (FS/MS) / 3-7% (MCU) / 2-5% (CU) / 0-2% (BCU)
- **leading_lines**: vertical preferred in 9:16 (stairs / buildings / trees)

### Axis Continuity
- **axis_line**: vector (e.g., "+X (L2R)" means axis along +X direction, camera on north side)
- **screen_direction**: L2R / R2L / Up / Down (must be consistent within scene unless narrative motivation)
- **30° rule**: same-subject consecutive shots must differ by ≥30° (or shot scale by ≥1 level)

### Camera Move
- **12 moves**: static / pan / tilt / dolly_in / dolly_out / tracking / crane_up / crane_down / handheld / steadicam / zoom_in / zoom_out
- **motion_intensity**: subtle / gentle / moderate / high / extreme
- **vertical_priority**: prefer tilt / crane / vertical_tracking; avoid horizontal pan in 9:16

### Video Gen Model Prompt Tokens (2026-06 verified)
- **Runway Gen-3 Alpha**: explicit prompt tokens (slow dolly in / quick zoom in)
- **Kling 1.6**: bilingual (缓慢推进,推镜头 / slow push-in)
- **Veo 2**: declarative cinematic language (a slow dolly-in on..., shallow depth of field, 35mm lens equivalent)
- **Sora 2**: 60s multi-shot sequence support

## Style Rules

### Shot Intent Rules
- Every shot must have narrative motivation (per screenplay emotion_curve beat)
- Shot scale choice follows shot-scale × emotion mapping per [`shot-grammar.md`](./references/shot-grammar.md) §Shot Scale × Narrative Function
- MCU is the default 短剧 shot scale (30-40% distribution per [`shot-grammar.md`](./references/shot-grammar.md) §短剧 shot-scale 分布)

### Axis Continuity Rules
- 180° axis maintained within scene (4 legal exceptions per [`axis-rules.md`](./references/axis-rules.md) §180° Axis Rule)
- 30° rule enforced between consecutive same-subject shots
- Screen direction consistent within scene (L2R / R2L / Up / Down)

### Vertical Framing Rules
- Power points (1/3, 1/4) or (2/3, 1/4), NOT horizontal rule-of-thirds (1/3, 1/3)
- Headroom 2-10% depending on shot scale
- Subtitle in lower-center zone (65-85%) or upper-center zone (15-35%), never face zone (35-65%)
- Per-platform divergence respected (抖音 / 快手 / 小程序剧 / 视频号 / TikTok / YouTube Shorts / Reels)

### Camera Move Rules
- Dolly vs zoom distinction preserved in prompt tokens (per [`camera-motion-catalog.md`](./references/camera-motion-catalog.md) §Dolly vs Zoom)
- Vertical camera move priority (tilt / crane / vertical_tracking) over horizontal pan in 9:16
- At least 1 camera move per 30s of footage (avoid static-only anti-pattern)

### Prohibited
- Horizontal rule-of-thirds in vertical 9:16 framing
- EWS overuse in 短剧 (>3% distribution)
- Crossing the 180° axis without legal exception
- Same-subject consecutive shots <30° apart
- Subtitle placement in face zone (35-65% vertical)
- Model-agnostic prompt (must use model-specific tokens from camera-motion-catalog.md)
- Camera move without narrative motivation

## Workflow

1. **Receive Upstream Inputs** — `screenplay.emotion_curve` (anchor points + beat structure) + `style_genome.5D_vector` (color + composition tendency)
2. **Shot List Design** — Per scene, enumerate required shots following shot-scale × emotion mapping
3. **Composition per Shot** — Apply vertical 9:16 power points + headroom per shot scale
4. **Axis Plan** — Define axis_line + screen_direction for entire scene; document crossings
5. **Camera Move Intent** — Per shot, select camera move based on emotion + narrative beat
6. **Vertical Framing Intent** — Per shot, define power_point + headroom + subtitle_zone + platform_target
7. **Model-Specific Handoff** — Translate camera_move to Runway/Kling/Veo/Sora prompt tokens
8. **Output Encoding** — Generate `shot_intent.json` + 4 handoff files (composition_lock sub-task internal / visual_executor / editor / continuity_auditor) — *Phase 17 v3.0: scene_builder handoff slot now feeds the internal composition_lock sub-task*
9. **Handoff to Downstream** — composition_lock sub-task (internal feasibility, formerly scene_builder) → visual_executor executes → editor verifies compliance

## Quality Thresholds

| Metric | Production Minimum | Source |
|--------|-------------------|--------|
| shot_intent_clarity | >= 0.88 | (operational: each shot_intent.json has all required fields populated) |
| axis_compliance | >= 0.95 | (operational: 180° axis + 30° rule + screen direction maintained across scene) |
| vertical_framing_quality | >= 0.85 | (operational: power points + headroom + subtitle zone follow 9:16 rules) |
| motion_narrative_fit | >= 0.82 | (operational: every camera move has narrative motivation) |
| first_frame_hook_rate (抖音) | >= 0.95 | [`vertical-screen-framing.md`](./references/vertical-screen-framing.md) §抖音 短剧 framing 3 大铁律 |
| per-platform divergence compliance | >= 0.80 | [`vertical-screen-framing.md`](./references/vertical-screen-framing.md) §Per-Platform Framing Divergence |

## Collaboration

- **<- screenplay**: emotion_curve (anchor points + beat structure) + scene breakdown + dialogue density
- **<- style_genome**: 5D vector (composition / color / rhythm / light_shadow / sound) + director reference
- **<- editor**: compliance OK / NG feedback (axis + 30° rule + screen direction across cuts)
- **-> composition_lock sub-task (internal, Phase 17 v3.0 absorbed deprecated scene_builder)**: `shot_intent.json` (spatial intent: camera position + sight line + subject blocking) — feasibility feedback now loops internally
- **-> visual_executor**: `animator_handoff.json` (model-agnostic camera move + 4-model prompt-token table) + shot composition + framing intent for first_frame generation
- **-> editor**: `editor_handoff.json` (axis_line + screen_direction + compliance_required list)
- **-> continuity_auditor**: `shot_intent.json` (full per-shot intent for cross-shot consistency audit)
- **-> hook_retention**: first-frame hook + close-up cliffhanger framing (per [`vertical-screen-framing.md`](./references/vertical-screen-framing.md) §抖音 / 小程序剧 framing 铁律)

## What NOT to do

- Don't apply horizontal rule-of-thirds to vertical 9:16 framing (use power points (1/3, 1/4))
- Don't decide feasibility (Phase 17 v3.0: now part of cinematographer's composition_lock sub-task — formerly scene_builder's job)
- Don't execute motion (visual_executor's job — cinematographer outputs model-agnostic intent + model-specific token table)
- Don't verify across-cut continuity (editor's job — cinematographer outputs axis + screen_direction; editor verifies)
- Don't cross 180° axis without legal exception (camera move / EWS re-anchor / insert / trisection)
- Don't use same-subject consecutive shots <30° apart (jump cut anti-pattern)
- Don't place subtitle in face zone (35-65% vertical)
- Don't use model-agnostic prompt tokens (4 models have divergent token mappings per camera-motion-catalog.md)
- Don't use horizontal pan in 9:16 without strong motivation (subject exits frame quickly)
- Don't design shots without narrative motivation (per screenplay emotion_curve)

## Pipeline Position

cinematographer sits in the production DAG between upstream semantic experts (screenplay + style_genome) and downstream execution / verification experts (visual_executor / editor / continuity_auditor). *Phase 17 v3.0: the former scene_builder feasibility step is now an internal composition_lock sub-task within cinematographer itself.*

`screenplay + style_genome → cinematographer (incl. composition_lock sub-task — formerly scene_builder) → (visual_executor execution + first_frame) → (editor compliance) → (continuity_auditor audit) → final`
