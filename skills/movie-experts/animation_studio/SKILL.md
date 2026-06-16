---
name: animation_studio
description: "Animation Production Expert: Disney 4-stage system (early/feature/live-action/magic-kingdom), 12-stage production pipeline, cross-cultural adaptation (花木兰 case), and animation script structure for 2D/3D/stop-motion animation."
version: 1.0.0
author: Hermes Agent (integrated from 100+本影视剪辑书 project)
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, animation, disney, 2d, 3d, stop-motion, pixar, cross-cultural-adaptation, mulan, hero-journey, musical-storytelling, character-design, color-script, voice-casting, leica-reel]
    related_skills:
      - screenplay          # Animation script structure
      - visual_executor    # Character design / concept art + animation execution
      - colorist            # Color script
      - cinematographer     # 3D scene composition_lock (Phase 17 v3.0: was scene_builder)
      - audio_pipeline      # Musical storytelling (composer sub-step) + voice casting for animation (voicer sub-step)
      - hook_retention      # Children's content hook design
    expert_id: animation_studio
    metrics: [story_structure_score, visual_consistency, character_appeal, musical_integration, cross_cultural_adaptation]
---

# Animation Production Expert (动画制作专家)

Specialist for animation production pipeline, Disney system methodology, and cross-cultural adaptation (East Asian / folk tale to global animation). Complements `visual_executor` (stills + motion), `audio_pipeline` (music, voice) by providing the structural / methodological framework.

## When to use this skill

Invoke this expert when:

- **True animation production** — 2D / 3D / stop-motion short or feature
- **Animation-style 短剧** — 短剧 adopting animation aesthetics (motion graphics, character animation, stop-motion)
- **Cross-cultural adaptation** — adapting Chinese folk tale / literature into animation
- **Disney-style production planning** — 12-stage pipeline
- **Animation script structure** — musical storytelling, sidekick comedy, hero's journey
- **Color script design** — per-scene color narrative for animation
- **Animation IP development** — multi-character ensemble for serialization

## References

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`_shared/project-corpus/animation-disney-system.md`](../_shared/project-corpus/animation-disney-system.md) | 任何动画制作前 | 迪士尼 4 阶段体系(早期事业 / 动画长片 / 实景拍摄 / 魔幻王国) + 12 阶段流程 + 跨文化改编(花木兰)+ 歌舞叙事 + 搭档喜剧 |
| [`_shared/project-corpus/README.md`](../_shared/project-corpus/README.md) §动画 | 查找动画原书时 | 项目内迪士尼艺术 + 影视动画经典剧本赏析索引 |
| [`../screenplay/references/save-the-cat-beat-sheet.md`](../screenplay/references/save-the-cat-beat-sheet.md) | 设计动画剧本结构 | Snyder 15-beat 适配动画长片 |
| [`../visual_executor/SKILL.md`](../visual_executor/SKILL.md) | 角色设计 + 动画执行 | FLUX + LoRA + IP-Adapter (drawer sub-step) / veo3.1 / kling-v3-4k / pixverse-v6 (animator sub-step) |
| [`../colorist/SKILL.md`](../colorist/SKILL.md) | 色彩脚本 | 色彩心理学 + LUT 设计 |

## Role & Philosophy

- **迪士尼 4 阶段是动画制作的"母语"。** 早期事业 → 动画长片 → 实景拍摄 → 魔幻王国——任何动画工作室的发展都遵循类似阶段。
- **跨文化改编 5 法则。** 选普世母题 + 加入美式价值观 + 创造滑稽配角 + 设计歌舞段落 + 保留文化元素装饰。
- **歌舞叙事是动画的灵魂。** 重要情感时刻用歌曲——歌曲推进剧情,不浪费。
- **搭档喜剧结构。** 主角 + 滑稽配角——配角是观众的"代入点",让沉重剧情可消化。
- **动画剧本 vs 真人剧本。** 动画需要更高密度、更明快的视觉节奏、更外放的情感表达。

## Knowledge Retrieval

在生成任何动画输出前,按以下顺序检索上下文:

- **迪士尼 4 阶段体系**(早期 / 长片 / 实景 / 魔幻王国)—— 详见 [`_shared/project-corpus/animation-disney-system.md`](../_shared/project-corpus/animation-disney-system.md)
- **12 阶段制作流程**(故事构思 → 剧本 → 故事板 → 配音 → Leica Reel → 角色设计 → 美术 → 原画 → 中间画 → 背景 → 上色/合成 → 后期)—— 同上
- **跨文化改编 5 法则**(《花木兰》案例)—— 同上
- **3 种主要动画类型**(二维 / 三维 / 定格)—— 同上
- **歌舞叙事原则**(情感时刻用歌曲)—— 同上
- **搭档喜剧结构**(主角 + 滑稽配角)—— 同上

**若当前 runtime 中有 memory / RAG 工具**,使用以下查询范围:

```
tags="expert:animation_studio,domain:disney-4-stage"
tags="expert:animation_studio,domain:12-stage-pipeline"
tags="expert:animation_studio,domain:cross-cultural-adaptation"
tags="expert:animation_studio,domain:musical-storytelling"
tags="expert:animation_studio,domain:sidekick-comedy"
tags="expert:animation_studio,domain:color-script"
```

**若无此类工具**,回退到本目录 `_shared/project-corpus/*.md` 静态文件。

## Core Capabilities

- **Disney 4-stage mapping** — for any animation studio / project, identify current stage
- **12-stage pipeline planning** — full animation production schedule
- **Cross-cultural adaptation assessment** — apply 5 rules to source material
- **Musical storytelling design** — identify which emotional moments need song
- **Sidekick comedy pairing** — design protagonist + sidekick chemistry
- **Color script construction** — per-scene color narrative
- **Voice casting strategy** — cast voice before animation (Disney principle)
- **Leica reel workflow** — storyboard + voice → test rhythm before animation

## Output Format

`animation_plan.json`:

```yaml
project_type: 2d_feature | 3d_feature | stop_motion | short | animation_style_短剧
target_runtime: <minutes>

disney_stage_mapping:
  current_stage: early | feature | live_action | magic_kingdom
  stage_progress: 0-100%

production_pipeline_12_stage:
  - stage: story_idea
    status: completed | in_progress | pending
    deliverable: <description>
  - stage: script
    ...
  (12 stages)

cross_cultural_adaptation:
  source_material: <folk tale / literature / original>
  universal_motif: <identified motif>
  american_values_added: [individualism, freedom, ...]
  sidekick_characters: [name1, name2]
  musical_numbers: [scene1, scene2]
  cultural_elements_preserved: [color, architecture, costume]

musical_storytelling:
  songs: [...]
  emotional_moments_as_songs: [...]

character_design:
  protagonist: <description>
  sidekick: <description>
  villain: <description>
  visual_signatures: [...]

color_script:
  per_scene: [...]
  overall_arc: <description>

voice_casting:
  protagonist_voice: <description>
  sidekick_voice: <description>
  record_before_animation: yes/no
```

## Key Parameters

### LLM Generation
- **model**: `<llm_primary>` (high-quality chat model with ≥ 16K context for animation bible)
- **temperature**: 0.7-0.9 (creative work)
- **max_tokens**: 6144 (full pipeline)
- **top_p**: 0.9

### Production scale
- **2D short (3-15 min)**: 3-6 months
- **3D short**: 6-12 months
- **2D feature**: 2-4 years
- **3D feature**: 3-5 years

## Workflow

### Standard animation_studio workflow

1. **Knowledge Retrieval** — query the 6 retrieval topics above
2. **Disney stage mapping** — identify current stage
3. **Source material analysis** — if adaptation, apply cross-cultural 5 rules
4. **Story structure** — Snyder 15-beat adapted to animation runtime
5. **Musical numbers placement** — which emotional moments need song
6. **Character design** — protagonist + sidekick + villain
7. **Color script** — per-scene color narrative
8. **Voice casting** — record voice before animation
9. **Leica reel** — storyboard + voice → test rhythm
10. **Pipeline planning** — 12-stage schedule

### For AI 短剧 adopting animation aesthetics
1. Standard workflow steps 1-3
2. Compress to 短剧 runtime (60-180s)
3. Use AI tools (visual_executor) for character / scene
4. Skip traditional animation stages 8-9 (no voice casting; TTS via audio_pipeline (voicer sub-step))
5. Focus on color script and shot composition

## Integration with Other Experts

- **`screenplay`**: Adapted screenplay with musical numbers + sidekick comedy
- **`visual_executor`**: Character design / concept art / model sheets (drawer sub-step) + Animation execution (veo3.1, kling-v3-4k, etc.) (animator sub-step)
- **`colorist`**: Color script + per-scene LUT
- **`cinematographer`** *(replaces deprecated Phase 17 `scene_builder`)*: 3D scene construction for 3D animation (now composition_lock sub-task)
- **`audio_pipeline (composer sub-step)`**: Musical numbers composition
- **`audio_pipeline (voicer sub-step)`**: Voice casting for animation characters
- **`hook_retention`**: Children's content hook design (3-second attention)
- **`compliance_gate`**: Animation-specific compliance (儿童内容, 广告限制)

## Sources & Attribution

Animation methodology primarily from:
- 《迪士尼的艺术：从米老鼠到魔幻王国》(Project 【迪士尼】) — 4-stage system
- 《影视动画经典剧本赏析》(Project -062) — 花木兰 cross-cultural case

Both books are in `_shared/project-corpus/`. Fair Use paraphrasing per project corpus LICENSE.

## Cross-References

- [`../screenplay/SKILL.md`](../screenplay/SKILL.md) — Screenplay expert
- [`../visual_executor/SKILL.md`](../visual_executor/SKILL.md) — Visual executor expert (drawing + animation sub-steps)
- [`../colorist/SKILL.md`](../colorist/SKILL.md) — Color expert
- [`../cinematographer/SKILL.md`](../cinematographer/SKILL.md) — 3D scene expert (Phase 17 v3.0: replaces deprecated [`../scene_builder/SKILL.md`](../scene_builder/SKILL.md); composition_lock sub-task)
- [`../audio_pipeline/SKILL.md`](../audio_pipeline/SKILL.md) — Music expert (composer sub-step) + Voice expert (voicer sub-step)
- [`../hook_retention/SKILL.md`](../hook_retention/SKILL.md) — Hook expert
- [`../_shared/glossary.md`](../_shared/glossary.md)
