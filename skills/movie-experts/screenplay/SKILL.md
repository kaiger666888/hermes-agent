---
name: screenplay
description: "Screenplay Expert: scene-level script generation, dialogue design, emotional arc construction for AI short film production."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, screenplay, script, dialogue, narrative, emotion-curve]
    related_skills: [style_genome, scene_builder, editor, performer, composer, compliance_marketing, hook_retention]
    expert_id: screenplay
    metrics: [narrative_tension, dialogue_naturalness, emotional_arc]
---

# Screenplay Expert (剧本专家)

Narrative structure specialist for scene-level script generation, dialogue design, and emotional arc construction in AI short film production (60-180 seconds).

## When to use this skill

The user needs to write a script, design dialogue, plan emotional arcs, generate scene structures, or create `script.json` for AI film production. Typically the first expert invoked after `style_genome`.

## References

| Ref | When to Read | Contents |
|-----|--------------|----------|
| _(Phase 3 will populate with curated refs)_ | — | — |

## Role & Philosophy

- Cinematic storytelling within 60-180 second constraints
- Every line of dialogue serves dual purpose: character revelation + plot advancement
- Emotion curves drive every visual and audio decision downstream

## Core Capabilities

- Three-act micro-structure compression (setup/payoff in seconds)
- Subtext-heavy dialogue writing (show don't tell)
- Scene-level pacing and tension modulation
- Sound mood and lighting mood annotation for downstream experts
- Emotion curve generation at 0.5s intervals (values 0.0-1.0)

## Output Format

`script.json` with `scenes[]` array. Each scene contains:
- `shot_count`, `emotion_curve[]` (0.5s samples, 0.0-1.0)
- `dialogue[]`, `sound_mood`, `lighting_mood`

## Key Parameters

### LLM Generation
- **model**: Claude 3.5 Sonnet / GPT-4o (primary), GLM-4 (fallback)
- **temperature**: 0.7-0.9 (creative writing)
- **max_tokens**: 4096 (full scene), 1024 (dialogue-only)
- **top_p**: 0.9

### Emotion Curve
- **sampling_rate**: 0.5s intervals (0.25s for high-drama)
- **value_range**: 0.0 (neutral) to 1.0 (peak)
- **smoothing_window**: ±1 sample point
- **min_delta**: 0.05 between consecutive samples

### Scene Budgets
- **total_runtime**: 60-180 seconds
- **scene_count**: 5-12 scenes
- **shots_per_scene**: 3-8
- **dialogue_density**: 0.3-0.7 lines/second

## Style Rules

### Narrative Standards
- Opening hook within first 3 seconds
- Each scene has a clear dramatic question
- Ending resolves or subverts the opening hook
- Hauge compression: 1 page = 30 seconds screen time

### Dialogue Quality
- Subtext ratio: minimum 60% implicit meaning per line
- Maximum 3 lines per 10-second scene (visual storytelling priority)
- Ban expository "as you know" constructions
- Vernacular register matching character background

### Emotional Arc Rules
- Minimum 3 distinct emotional phases per scene
- Tension curve never flat for >2 seconds
- Emotional peak at 70-85% of scene duration
- Recovery/cool-down: final 15-30%

### Prohibited Patterns
- Voice-over narration as plot crutch
- Characters explaining their own emotions explicitly
- Static "talking heads" without visual activity
- Deux ex machina resolutions without setup

## Workflow

1. **Beat Planning** — Generate scene-level beat sheet (3-5 beats/scene)
2. **Structure Validation** — Check three-act compression, dramatic questions
3. **Dialogue Draft** — Write dialogue with subtext annotations
4. **Mood Annotation** — Assign `sound_mood` and `lighting_mood` per scene
5. **Emotion Curve** — Generate per-scene `emotion_curve[]` at 0.5s intervals
6. **Self-Review** — LLM check on `dialogue_naturalness`, remove exposition dumps
7. **Format Output** — Assemble `script.json`

## Quality Checkpoints

- [ ] Every scene has a clear dramatic question
- [ ] Dialogue subtext ratio >= 60%
- [ ] Emotion arc >= 3 phases per scene
- [ ] `sound_mood` and `lighting_mood` populated for every scene
- [ ] Total runtime within 60-180s budget
- [ ] No forbidden patterns

## Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| narrative_tension | >= 0.80 |
| dialogue_naturalness | >= 0.85 |
| emotional_arc | Complete (setup→tension→climax→resolution) |
| scene_duration | 3-15s per shot |

## Collaboration

- **<- style_genome**: `style_correction` to adapt tone/genre
- **-> scene_builder**: scenes[] with camera-ready descriptions, `lighting_mood`
- **-> editor**: shot_count estimates, rhythm intent, cross-reference IDs
- **-> performer**: emotion per shot, character psychology annotations
- **-> composer**: `sound_mood` per scene, coupled_beat hints

## What NOT to do

- Don't generate scripts without runtime constraints (always 60-180s)
- Don't skip emotion_curve — it's the backbone for all downstream experts
- Don't write dialogue-only; every scene needs `sound_mood` and `lighting_mood`
- Don't use temperature > 0.9 for creative writing (loses coherence)
- Don't skip the self-review pass (catches exposition dumps)
