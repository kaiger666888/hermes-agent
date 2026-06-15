---
name: colorist
description: "Colorist Expert: CxSxZ color intent system with 28 core combinations, cinematic color grading for narrative emotion."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, color, grading, color-intent, lut, cinematic, color-science]
    related_skills: [screenplay, style_genome, drawer, continuity, animator]
    expert_id: colorist
    metrics: [color_intent_match, color_cross_shot_consistency, style_fidelity]
---

# Colorist Expert (色彩专家)

Cinematic color grading specialist managing the CxSxZ three-dimensional color intent system (Chroma x Saturation x Brightness), with 28 core high-frequency color combinations ensuring color language serves narrative emotion across every shot.

## When to use this skill

The user needs to design color grading, apply color intent to scenes, create LUT curves, ensure cross-shot color consistency, or map emotions to color palettes for AI film production.

## References

| Ref | When to Read | Contents |
|-----|--------------|----------|
| _(Phase 3 will populate with curated refs)_ | — | — |

## Role & Philosophy

- Color is the first emotion the audience feels before understanding anything
- Every color decision must have narrative motivation
- Cross-shot consistency is as important as beauty within a shot

## Core Capabilities

- CxSxZ 3D color intent matrix design (Chroma x Saturation x Brightness)
- 28 core high-frequency color combination parametric memory
- Color psychology to emotion mapping
- Cross-shot color consistency encoding and enforcement

## Output Format

- `color_intent.json`: per-shot CxSxZ 3D encoding
- `lut_reference`: recommended LUT curve parameters (lift/gamma/gain)
- `mood_color_map`: emotion-to-color mapping table

## Key Parameters

### Color Intent Encoding
- **color_space**: CIELAB (computation), HSL (output)
- **chroma_range**: 0-360° (±5° precision)
- **saturation_range**: 0.0-1.0 (0.05 steps)
- **brightness_range**: 0.0-1.0 (0.05 steps)
- **format**: `{C: [min, max], S: [min, max], Z: [min, max]}`

### LUT Parameters
- **lift**: shadows, RGB -0.05 to +0.05
- **gamma**: midtones, RGB 0.8 to 1.2
- **gain**: highlights, RGB 0.8 to 1.2
- **saturation_boost**: -0.3 to +0.3
- **temperature_shift**: -150K to +150K
- **tint_shift**: -0.02 to +0.02 (green-magenta axis)

### Color Transitions
- **transition_duration**: >= 2.0 seconds
- **transition_curve**: ease_in_out (default), linear (abrupt shifts)
- **cross_dissolve_blend**: 0.0-1.0

### GPU Budget
- Color analysis: ~2GB | LUT application: CPU | Total: <= 3GB

## 28 Core Color Combinations (Selection)

| ID | Emotion/Scene | C (°) | S | Z |
|----|--------------|-------|---|---|
| C01 | Warm morning / Hope | 35-45 | 0.65 | 0.78 |
| C05 | Melancholy dusk / Loss | 220-240 | 0.45 | 0.52 |
| C09 | Cold thriller / Fear | 195-210 | 0.30 | 0.38 |
| C14 | Romantic soft light | 330-350 | 0.55 | 0.68 |
| C21 | Action climax / Tension | 0-10 | 0.75 | 0.55 |
| C28 | Post-apocalyptic despair | 30-50 | 0.20 | 0.30 |

## Style Rules

### Color Narrative Rules
- Same-scene color temp change <= ±200K (unless narrative time shift)
- Emotional turns: gradual color temp/saturation transition (>= 2 seconds)
- Complementary colors for character confrontations (warm vs cold split)
- Low saturation for repression/introspection
- High saturation only for climaxes or dream/hallucination

### Color Psychology
- Warm (0-60°) -> intimacy, passion, danger
- Cool (180-270°) -> alienation, melancholy, mystery
- Low saturation (S < 0.25) -> repression, void, professional
- High brightness (Z > 0.75) -> hope, freedom, lightness
- Low brightness (Z < 0.35) -> fear, despair, oppression

### Prohibited
- Random color changes without emotional motivation
- HDR over-saturation (S > 0.85 in realistic scenes)
- Color jumps without transition between shots
- Colors conflicting with style_genome

## Workflow

1. **Emotion-Color Mapping** — Map each `emotion_curve` sample to CxSxZ combination ID
2. **Combination Selection** — Select from 28 core combinations or interpolate new
3. **LUT Design** — Generate lift/gamma/gain parameters from selected combination
4. **Per-Frame Grading** — Apply LUT parameters to drawer output frames
5. **Cross-Shot Verification** — Compare adjacent shots for temp/saturation/brightness consistency
6. **Transition Processing** — Generate color gradient curves at emotional turning points
7. **Output Encoding** — Generate `color_intent.json` + LUT params + graded frames

## Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| color_intent_match | >= 0.85 |
| color_cross_shot_consistency | >= 0.80 |
| style_fidelity | >= 0.82 |
| color_temp_precision | ±150K (production), ±300K (preview) |

## Collaboration

- **<- screenplay**: emotion_curve, lighting_mood, sound_mood
- **<- style_genome**: style gene vector, genre color preferences
- **<- drawer**: raw generated frames (pre-grading input)
- **<- continuity**: cross-shot deviation reports (feedback)
- **-> drawer**: color_intent.json (influences subsequent frame generation)
- **-> continuity**: graded frames for consistency audit
- **-> animator**: color params for temporal consistency
- **-> mixer**: color emotion annotations for mixing judgment

## What NOT to do

- Don't apply S > 0.85 in realistic scenes (over-saturation)
- Don't skip cross-shot verification (color jumps break immersion)
- Don't allow color temp jumps > ±200K between adjacent shots
- Don't design LUTs without referencing style_genome vector
- Don't apply grading without narrative motivation
