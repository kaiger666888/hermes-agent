# Art Direction Methodology (美术指导方法论)

**Source:** Adapted from OpenClaw kais-art-direction methodology + production design industry standards (Bordwell production design literature).
**Copyright:** Fair Use — methodology distillation.
**Last-verified:** 2026-06-16

## Summary

Operational methodology for translating the 5D Style Genome (defined in [`./director-dna-archive.md`](./director-dna-archive.md)) into production-ready ArtDirection artifacts: mood board, color palette specification, lighting reference imagery, and texture/material direction. This file bridges the abstract style genome and the concrete drawer / scene_builder execution.

## Heuristics

### From Style Genome to ArtDirection

The Style Genome produces 5 dimensions: director DNA, genre DNA, auteur signature, cross-cultural blend, CN audience fit. ArtDirection translates these into 4 operational artifacts:

| Style Genome dimension | ArtDirection artifact |
|---|---|
| Director DNA | Mood board (3 reference frames per scene type) |
| Genre DNA | Color palette spec (5-7 hex codes with usage ratios) |
| Auteur signature | Texture / material direction |
| Cross-cultural blend | Lighting reference imagery |
| CN audience fit | Per-platform framing adjustments |

### Mood board 3-选-1 protocol

Per OpenClaw kais-art-direction methodology:

**For each scene type (dialogue / action / emotional peak), generate 3 mood board candidates.**

**Selection criteria:**
- Visual coherence with Style Genome
- Distinguishability from competitors (avoid derivative looks)
- Producibility (can drawer / animator actually achieve this look)

**Output:** 1 selected mood board per scene type + 2 rejected alternates with rejection reasons.

### Color palette specification

**Format:** 5-7 hex codes + per-color usage ratio.

**Example:**
```yaml
color_palette:
  - hex: "#0a0e27"
    usage_ratio: 0.45
    role: "background dominant"
    scene_types: ["night exterior", "industrial interior"]
  - hex: "#ff006e"
    usage_ratio: 0.15
    role: "accent"
    scene_types: ["neon signage", "character outfit highlight"]
  - hex: "#3a86ff"
    usage_ratio: 0.20
    role: "key light fill"
    scene_types: ["tech-lit interior"]
  - hex: "#ffbe0b"
    usage_ratio: 0.10
    role: "warm accent"
    scene_types: ["sunset", "incandescent light"]
  - hex: "#8338ec"
    usage_ratio: 0.10
    role: "secondary accent"
    scene_types: ["dramatic shadow"]
```

**Validation:** ratios sum to 1.0 ± 0.05.

### Lighting reference imagery

**For each scene, document:**
- Key light direction (cardinal / inter-cardinal)
- Key light intensity (0.0-1.0)
- Color temperature (Kelvin)
- Mood descriptor (e.g., "dramatic rim light", "soft window fill")
- Reference image URL (public-domain or fair-use)

**Cross-scene consistency:** all scenes in the same episode must share key light direction unless explicitly motivated by plot (e.g., day-to-night transition).

### Texture / material direction

**For each major surface type (skin / fabric / metal / concrete / glass), document:**
- Material name
- Surface treatment (matte / glossy / textured / weathered)
- Color (hex)
- Reflectivity (0.0-1.0)
- Reference image

**Example:**
```yaml
materials:
  protagonist_skin:
    material: "skin, East Asian male, late 20s"
    treatment: "matte, slight sweat"
    color: "#d4a373"
    reflectivity: 0.15
  trench_coat:
    material: "wool blend"
    treatment: "matte, weathered"
    color: "#1a1a1a"
    reflectivity: 0.10
```

### Per-platform framing adjustments

For 短剧 9:16 vertical vs 微电影 16:9 horizontal:

| Element | Horizontal (16:9) | Vertical (9:16) |
|---|---|---|
| Default shot size | Medium | Medium Close-up |
| Composition rule | Rule of thirds | Vertical thirds (top/middle/bottom) |
| Negative space | Lateral (left/right) | Vertical (top/bottom) |
| Caption strip | None | Bottom 10-15% reserved |
| Background detail | High | Reduced (focus on subject) |

### Mood board generation prompt template

```
{STYLE_CORE}, {scene_type}, mood board frame,
color palette: {palette_hex_list},
key light: {light_direction} {color_temp}K,
{mood_descriptor},
3 distinct compositions exploring {scene_emotional_intent},
high cinematic quality, professional production design
```

### Integration with downstream experts

- **-> [`drawer`](../../drawer/SKILL.md)**: consumes ArtDirection as STYLE_CORE layer per [`../../character_designer/references/layered-style-prefix.md`](../../character_designer/references/layered-style-prefix.md)
- **-> [`scene_builder`](../../scene_builder/SKILL.md)**: consumes materials spec for 3D scene construction
- **-> [`cinematographer`](../../cinematographer/SKILL.md)**: consumes lighting reference for shot planning
- **-> [`storyboard_designer`](../../storyboard_designer/SKILL.md)**: consumes per-platform framing for shot composition

### Common pitfalls

| Pitfall | Cause | Fix |
|---|---|---|
| Mood board looks derivative | Style Genome not specific enough | Revisit director DNA + auteur signature |
| Color palette too saturated | Default AI tendency | Reduce saturation by 20-30% in palette spec |
| Inconsistent lighting across scenes | Each scene designed in isolation | Enforce cross-scene key light consistency |
| Materials too "CG-clean" | Default drawer tendency | Add weathering + imperfection notes to materials |

---

## Cross-references

- [`./director-dna-archive.md`](./director-dna-archive.md) — feeds Director DNA dimension
- [`./genre-dna-taxonomy.md`](./genre-dna-taxonomy.md) — feeds Genre DNA dimension
- [`../../character_designer/references/layered-style-prefix.md`](../../character_designer/references/layered-style-prefix.md) — downstream STYLE_CORE consumer
- [`../../storyboard_designer/references/4d-anchoring-params.md`](../../storyboard_designer/references/4d-anchoring-params.md) — lighting dimension uses ArtDirection
