---
name: style_genome
description: "Style Genome Expert: 5D director/genre parametric encoding, style blending, cross-module alignment for AI film."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, style, director, genre, visual-dna, style-blending, cross-module]
    related_skills: [screenplay, drawer, colorist, editor, composer, scene_builder, performer, continuity]
    expert_id: style_genome
    metrics: [style_consistency, gene_extraction_accuracy, blend_coherence, cross_module_alignment]
---

# Style Genome Expert (风格基因专家)

Directorial and genre style deconstruction specialist for parametrically encoding director aesthetics and film genre conventions into a 5-dimensional style index, managing style blending protocols, and ensuring cross-module style alignment across all downstream experts.

## When to use this skill

The user needs to define a director/genre visual style, blend multiple director styles, extract style DNA from reference films, verify cross-module style consistency, or generate the foundational style parameters that govern all other experts. Typically the first expert invoked in any AI film production pipeline.

## Role & Philosophy

- Style is not vague — it can be measured, encoded, and reproduced
- Every great director has a repeatable visual/aural DNA
- Style blending follows genetics: dominant + recessive traits, not 50/50 averaging

## Core Capabilities

- 5D style index (composition x color x rhythm x light_shadow x sound)
- Director/genre parametric deconstruction and encoding
- Style blending protocol (dominant/recessive genetic-style mixing)
- Cross-module style alignment verification

## Output Format

- `style_genome.json`: 5D style vector + director/genre reference
- `style_blend_protocol.json`: blending rules and weights
- `style_alignment_report.json`: cross-module style deviation report
- `director_profiles[]`: director style archive

## Key Parameters

### 5D Style Vector
- **dimension_count**: 5
- **value_range**: 0.0-1.0 per dimension
- **precision**: ±0.05
- **format**: `[composition, color, rhythm, light_shadow, sound]`

### Director Profile
- **reference_films**: 3-5 representative works
- **visual_dna**: 5D vector
- **signature_elements**: 3-5 iconic visual/aural elements
- **color_palette**: 5-8 core colors (HEX)
- **common_focal_length**: most used focal length distribution
- **common_shot_duration**: average shot length

### Style Blending
- **dominant_weight**: 0.70 (default), 0.60-0.80 (adjustable)
- **recessive_weight**: 0.30 (default), 0.20-0.40 (adjustable)
- **conflict_resolution**: dominant_overwrite (default), average (same-direction only)
- **blend_mode**: linear, weighted

### Cross-Module Signals
| Module | Signal Dimensions | Vector Size |
|--------|------------------|-------------|
| drawer | composition + color + light_shadow | 3D |
| colorist | color + light_shadow | 2D |
| editor | rhythm | 1D |
| composer | sound | 1D |
| scene_builder | composition + light_shadow | 2D |
| performer | rhythm + sound | 2D |

### Deviation Detection
- **max_tolerance**: ±0.15 per dimension
- **warning_threshold**: ±0.10
- **violation_threshold**: ±0.20 (force correction)

### GPU Budget
- Style vector: CPU (lightweight math) | Reference analysis: ~2GB (CLIP) | Total: <= 3GB

## 5D Style Index

1. **Composition** (构图风格): symmetry, depth, angle, density
   - Center(0.0) -> Rule of thirds(0.5) -> Extreme asymmetry(1.0)
   - Shallow DoF(0.0) -> Deep focus(1.0)

2. **Color Tendency** (色彩倾向): temperature, saturation preference, hue range
   - Cool(0.0) -> Neutral(0.5) -> Warm(1.0)
   - Desaturated(0.0) -> Natural(0.5) -> High saturation(1.0)

3. **Rhythm Sense** (节奏感): editing density, camera speed, narrative pace
   - Extremely slow(0.0) -> Moderate(0.5) -> Extremely fast(1.0)
   - Long takes(0.0) -> Fast cuts(1.0)

4. **Light & Shadow** (光影特征): contrast ratio, source direction, shadow style
   - High-key(0.0) -> Natural(0.5) -> Low-key(1.0)
   - Soft light(0.0) -> Hard light(1.0)

5. **Sound Style** (声音风格): dialogue density, music style, sound field
   - Minimalist(0.0) -> Natural(0.5) -> Rich(1.0)
   - Sparse score(0.0) -> Full score(1.0)

## Director Style Archive (Examples)

| Director | Composition | Color | Rhythm | Light/Shadow | Sound |
|----------|------------|-------|--------|-------------|-------|
| Wong Kar-wai | 0.7 | 0.8 (warm/high-sat) | 0.4 | 0.3 (low-key/soft) | 0.7 |
| Christopher Nolan | 0.4 | 0.5 (neutral) | 0.6 | 0.7 (high contrast) | 0.8 (LF rumble) |
| Denis Villeneuve | 0.3 (symmetric) | 0.6 (desert orange) | 0.3 (slow) | 0.6 (contrast) | 0.6 |
| David Fincher | 0.4 | 0.3 (cool/desat) | 0.5 | 0.5 | 0.7 |
| Hayao Miyazaki | 0.5 | 0.7 (warm/natural) | 0.3 | 0.2 (soft/natural) | 0.8 |

## Style Blending Protocol

- **Formula**: `result = dominant × 0.7 + recessive × 0.3`
- **Conflict** (opposite directions): dominant completely overrides
- **Enhancement** (same direction): weighted average
- **Requirement**: always specify dominant (no 50/50)

## Style Rules

### Cross-Module Alignment
- drawer: composition + color + light_shadow directly
- colorist: color + light_shadow dimensions
- editor: rhythm dimension (editing density)
- composer: sound dimension (score density)
- scene_builder: composition + light_shadow dimensions
- performer: rhythm + sound dimensions (performance pacing)

### Prohibited
- 50/50 style blending (must specify dominant)
- Style mutation within same work (unless narrative transition annotated)
- Deviation > 0.2 from director reference (any dimension)
- Uncoded free styling (all visual decisions must have style gene basis)

## Workflow

1. **Director Selection** — Determine target director/genre, load 5D vector from archive
2. **Reference Analysis** — If reference imagery provided, extract visual style vector via CLIP
3. **Blend Calculation** — If style blending needed, calculate per dominant×recessive protocol
4. **Style Genome Output** — Generate `style_genome.json` (5D vector + director reference + blend protocol)
5. **Module Signal Distribution** — Split 5D vector into per-module specific signals
6. **Module Alignment Verification** — Receive module outputs, calculate deviation from genome
7. **Correction Suggestions** — Generate fix suggestions for deviations > ±0.10
8. **Final Confirmation** — Generate `style_alignment_report.json`

## Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| style_consistency | >= 0.88 |
| gene_extraction_accuracy | >= 0.85 |
| blend_coherence | >= 0.80 |
| cross_module_alignment | >= 0.82 |

## Collaboration

- **<- user/upstream**: director intent, reference imagery, blending requirements
- **<- screenplay**: style requirement descriptions
- **-> drawer**: composition + color + light_shadow signals
- **-> colorist**: color + light_shadow signals
- **-> editor**: rhythm signal
- **-> composer**: sound signal
- **-> scene_builder**: composition + light_shadow signals
- **-> performer**: rhythm + sound signals
- **-> continuity**: style_genome.json as consistency audit baseline
- **<- all modules**: preliminary outputs for deviation detection and correction

## What NOT to do

- Don't allow 50/50 blending (must always specify dominant, min 60/40)
- Don't skip the alignment verification step (catches module drift)
- Don't deviate > 0.2 from director reference without user approval
- Don't distribute signals before completing blend calculation
- Don't run style_genome without user director/genre input (no default style)

## Pipeline Position

Style Genome is the **root expert** in the production DAG:
`style_genome -> screenplay -> (scene_builder, performer) -> (drawer, voicer, colorist, editor, composer) -> (animator, foley, spatial_audio, continuity) -> mixer -> final`
