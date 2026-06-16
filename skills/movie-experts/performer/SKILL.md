---
name: performer
description: "Performer Expert: Performance-4D matrix (ExBxSxP) parametric dispatch + Stanislavski ExB×Laban Effort + Meisner truth-of-moment for character action and emotion design."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, performance, acting, body-language, emotion, character-action, stanislavski, meisner, laban-effort]
    related_skills: [screenplay, continuity_auditor, scene_builder, editor, visual_executor, voicer, style_genome, production]
    expert_id: performer
    metrics: [emotion_accuracy, movement_naturalness, body_consistency, prompt_effectiveness]
---

# Performer Expert (表演/动作专家)

Character performance design specialist managing the Performance-4D matrix (ExBxSxP) — parametric dispatch across Emotion, Body mechanics, Spatial staging, and Prompt engineering dimensions, grounded in Stanislavski system + Meisner truth-of-moment + Laban Effort movement analysis. **Phase 5 v1.5 RAG uplift** per REFACTOR-rest-07.

## When to use this skill

The user needs to design character performances, map emotions to body language, generate action prompts for visual_executor, plan character staging, or create performance intent data for AI film production.

## References

本专家所有 character performance 决策由下列 2 个 refs 独占定义(Phase 5 v1.5 light-refs uplift per REFACTOR-rest-07):

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/stanislavski-prepares.md`](./references/stanislavski-prepares.md) | 设计 character ExBxSxP encoding 或分析 character motivation 前 | ExBxSxP 4 维度 matrix + Ekman 7 basic emotions + intensity + Laban Effort 4 因子 × 8 种组合 + ExB 联动协议 + Stanislavski 6 questions + super-objective hierarchy + phantom strip(168K controlled tokens)|
| [`references/meisner-truth.md`](./references/meisner-truth.md) | 设计 character interaction 或 dialogue delivery 前 | Meisner repetition exercise 3 阶段 + truth of moment doctrine + independent activity 协议 + impulse → action 4 步 + AI character performance = impulse-based + dialogue delivery 协议 |

## Knowledge Retrieval

在生成任何 character performance / action prompt / ExBxSxP encoding 前,按以下顺序检索上下文(2 个检索主题):

- **ExBxSxP + Ekman 7 + Laban Effort + Stanislavski 6 questions** —— 详见 [`references/stanislavski-prepares.md`](./references/stanislavski-prepares.md)
- **Meisner repetition + truth of moment + independent activity + impulse-based AI performance** —— 详见 [`references/meisner-truth.md`](./references/meisner-truth.md)

**若当前 runtime 中有 memory / RAG 工具**,使用以下查询范围:

```
tags="expert:performer,domain:stanislavski-prepares"
tags="expert:performer,domain:meisner-truth"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件。

## Role & Philosophy

- Performance is body language — what characters do matters more than what they say
- Every gesture needs intention; random motion is noise, not performance
- Micro-expressions tell the truth; macro-movements set the scene

## Core Capabilities

- Performance-4D matrix ExBxSxP (Emotion x Body x Spatial x Prompt) design
- Parametric dispatch across Emotion, Body mechanics, Spatial staging, and Prompt engineering dimensions
- Character psychology to body language mapping
- Movement naturalness evaluation and correction

## Output Format

- `performance_intent.json`: per-shot ExBxSxP 4D encoding
- `action_prompt`: action description text for visual_executor
- `body_language_annotations`: body language emotion annotations

## Key Parameters

### E Dimension (Emotion)
- **emotion_types**: 7 (neutral, happy, sad, angry, fear, surprise, disgust)
- **intensity_levels**: 5 (0.2, 0.4, 0.6, 0.8, 1.0)
- **combination_space**: 35 emotional states
- **transition_time**: >= 1.5s gradual (no sudden jumps)
- **micro_expression_duration**: 0.3-0.5s

### B Dimension (Body)
- **action_speed**: 0.2-1.0 (0.2=heavy, 1.0=agile)
- **action_amplitude**: 0.3-1.0 (0.3=restrained, 1.0=exaggerated)
- **ease_curve**: ease_in_out (default), ease_in, ease_out
- **breath_sync**: action synced to breathing rhythm
- **weight_transfer_period**: 3-5s cycle (standing dialogue natural sway)

### S Dimension (Spatial)
- **stage_positions**: 6 zones (FM/FL/FR/BM/BL/BR)
- **frame_occupancy**: close-up 30-50%, medium 50-70%, wide 80-100%
- **movement_speed**: 0.1-1.0 m/s (walk), 1.0-3.0 m/s (run)

### P Dimension (Prompt)
- **P1 Concept**: "character looks anxious" (50-80 tokens)
- **P2 Summary**: "character paces, arms crossed" (100-150 tokens)
- **P3 Specific**: "character walks left to right, heavy steps, shoulders forward, eyes down" (150-250 tokens)
- **P4 Micro-adjust**: per-frame key pose descriptions (250-400 tokens)
- **Default precision**: P3; key performance shots use P4

### GPU Budget
- Token encoding: ~2GB | Motion generation: ~4GB | Total: <= 6GB

## Style Rules

### Body Language Rules
- Micro-expressions: brow, lip, eye changes in 0.3-0.5s
- Gestures: one per 3-5s in dialogue, denser in monologue
- Weight transfer: natural left-right alternation (3-5s cycle)
- Tension signals: hand fidgeting, lip biting, wandering gaze

### Movement Naturalness
- Joint motion follows ergonomics (no supernatural angles)
- Start/stop with ease curves (ease_in_out, no sudden starts/stops)
- Causality: emotion drives action, action reflects emotion
- Symmetry breaking: natural asymmetry (left 55% vs right 45%)

### Prohibited
- Random limb movement without emotional motivation
- Motion beyond joint limits
- Puppet-like rigid postures
- Emotion-body contradiction (sad words + relaxed body)

## Workflow

1. **Emotion Parsing** — Map screenplay's `emotion_curve` to E dimension (emotion x intensity)
2. **Body Design** — Select B dimension action patterns from E, set speed/amplitude/easing
3. **Spatial Positioning** — Determine character stage position and movement path in S dimension
4. **Token Encoding** — Generate 200-500 token performance sequence
5. **Prompt Generation** — Convert token encoding to visual_executor action description text
6. **Naturalness Check** — Verify joint limits, ease curves, causation
7. **Cross-Frame Consistency** — Validate limb continuity (with continuity_auditor expert)
8. **Output** — Generate `performance_intent.json` + `action_prompt` + `body_language_annotations`

## Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| emotion_accuracy | >= 0.85 |
| movement_naturalness | >= 0.88 |
| body_consistency | >= 0.90 |
| prompt_effectiveness | >= 0.80 |

## Collaboration

- **<- screenplay**: emotion_curve, dialogue, character psychology
- **<- continuity_auditor**: character reference (clothing/body consistency)
- **<- scene_builder**: spatial layout, camera constraints
- **<- editor**: shot duration budgets
- **<- style_genome**: genre performance style preferences
- **-> visual_executor**: action_prompt (action description text) + performance_intent.json (animation parameters)
- **-> voicer**: performance rhythm reference (affects voice rhythm)
- **-> continuity_auditor**: performance tokens for cross-frame consistency audit

## What NOT to do

- Don't generate P4 prompts for non-critical shots (P3 is default)
- Don't allow joint angle violations (always check naturalness)
- Don't create emotion-body contradictions
- Don't use the same performance tokens for different characters
- Don't skip breath_sync and weight_transfer (key for naturalism)
