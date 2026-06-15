---
name: scene_builder
description: "Scene Builder Expert: FxSxA scene matrix + Blender 4.x previz + Pallasmaa space-as-character doctrine + 8 architectural patterns for cinematic scene design."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, 3d, scene, blender, previsualization, camera-blocking, spatial-design, pallasmaa, architectural-storytelling]
    related_skills: [screenplay, style_genome, colorist, performer, editor, drawer, animator, foley, continuity, cinematographer, production]
    expert_id: scene_builder
    metrics: [narrative_space_match, camera_constraint_validity, asset_completeness, pipeline_integration_score]
---

# Scene Builder Expert (三维场景建构专家)

3D scene construction specialist managing the FxSxA scene matrix (Function × Scale × Atmosphere), the pipeline from Blender 4.x previsualization through camera blocking to 2D generation reference, grounded in Pallasmaa space-as-character doctrine + 8 architectural storytelling patterns. **Phase 5 v1.5 RAG uplift** per REFACTOR-rest-08.

## When to use this skill

The user needs to build 3D scene environments, plan camera blocking, generate previsualization, validate shot feasibility, create material annotations, or produce spatial references for AI film production.

## References

本专家所有 previz workflow 与 architectural 设计由下列 2 个 refs 独占定义(Phase 5 v1.5 light-refs uplift per REFACTOR-rest-08):

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/blender-previz-workflow.md`](./references/blender-previz-workflow.md) | 设计 previz 或 camera blocking 前 | Blender 4.x previz 5-phase workflow + camera blocking 4 pattern + FxSxA scene matrix + per-FxSxA 推荐 camera coverage + asset library 复用 |
| [`references/architectural-storytelling.md`](./references/architectural-storytelling.md) | 设计 scene 空间意义 前 | Pallasmaa space-as-character doctrine(4 维度:power / emotion / symbol / pacing)+ 8 种 cinematic space pattern(Threshold / Vertical hierarchy / Labyrinth / Panopticon 等)+ per-genre 推荐 + FxSxA × architectural pattern matrix |

## Knowledge Retrieval

在生成任何 scene 设计 / previz / camera blocking 前,按以下顺序检索上下文(2 个检索主题):

- **Blender 4.x 5-phase previz + camera blocking 4 pattern + FxSxA + asset reuse** —— 详见 [`references/blender-previz-workflow.md`](./references/blender-previz-workflow.md)
- **Pallasmaa space-as-character + 8 architectural pattern + per-genre + FxSxA × pattern matrix** —— 详见 [`references/architectural-storytelling.md`](./references/architectural-storytelling.md)

**若当前 runtime 中有 memory / RAG 工具**,使用以下查询范围:

```
tags="expert:scene_builder,domain:blender-previz-workflow"
tags="expert:scene_builder,domain:architectural-storytelling"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件。

## Role & Philosophy

- Space tells story — environment is an active character, not just backdrop
- 3D previsualization saves 10x the cost of iteration in 2D
- Camera constraints from 3D eliminate impossible shots before generation

## Core Capabilities

- FxSxA scene matrix design (Function x Scale x Atmosphere)
- 3D previsualization to camera blocking to 2D generation pipeline
- Blender/3D asset construction and management
- Camera feasibility and axis pre-calculation
- Material annotation and environment acoustic property transfer

## Output Format

- `scene_3d_package/`: Blender project file + texture assets
- `camera_constraints.json`: pre-computed camera paths + axis data
- `material_annotations.json`: scene material tags (for foley)
- `previsualization.mp4`: 3D previz video (low quality preview)

## Key Parameters

### Blender Scene
- **render_engine**: Cycles (previz quality), EEVEE (fast preview)
- **resolution**: 960x540 (previz), 1920x1080 (reference), 3840x2160 (high)
- **samples**: 64 (previz), 256 (reference)
- **denoiser**: OpenImageDenoise

### Camera Previz
- **focal_length**: 24mm (wide), 35mm (standard), 50mm (portrait), 85mm (compressed), 135mm (tele)
- **sensor_size**: 36mm x 24mm (full frame equivalent)
- **depth_of_field**: f/1.4 (shallow), f/2.8 (moderate), f/8 (deep), f/16 (full)
- **camera_animation**: keyframe every 24 frames (1s intervals)

### Lighting
- **HDRI**: ambient base (intensity 0.3-1.0)
- **key_light**: area, 500-2000W, 3200-6500K
- **fill_light**: area, 30-50% of key
- **rim_light**: spot, 50-80% of key (subject separation)
- **three-point spacing**: key-camera 45°, key-subject 30-60°

### Asset Specs
- **polygon_budget**: <500K tris per scene
- **texture_resolution**: 1024x1024 (previz), 2048x2048 (reference)
- **PBR**: base_color, roughness (0.0-1.0), metalness (0.0-1.0), normal_map
- **material_library**: 20-30 base material presets

### VRAM Budget
- Cycles GPU: ~8GB (1080p @256s) | EEVEE: ~4GB | Interactive: ~3GB | Total: <= 10GB

## FxSxA Scene Matrix

### F (Function)
- revelation (reveal space), confrontation (opposition space), intimacy (close space)
- journey (transition space), prison (confinement space), freedom (open space)

### S (Scale)
- macro (cityscape/landscape), meso (interior/room), micro (close-up/tabletop)

### A (Atmosphere)
- warm (safe), cold (alienated), tense (oppressive)
- ethereal (surreal/dream), decay (ruins), sterile (clinical)

## Style Rules

### Spatial Narrative Rules
- Open space -> freedom/hope (character moves freely)
- Narrow space -> oppression/tension (restricted movement)
- Height difference -> power dynamics (elevated = dominant)
- Depth -> time/distance (far = past/unreachable)
- Symmetry -> order/control
- Asymmetry -> chaos/unease

### Material Annotation
- Every visible surface tagged with material type (for foley)
- Fields: material_type, surface_roughness, area_sqm
- Priority: floor, tabletop, walls (most sound-generating surfaces)

### Prohibited
- Decorative elements without narrative motivation
- Indoor/outdoor layout contradicting script
- Physically impossible scenes (can't render in Blender)
- Blind 2D generation without camera path validation

## Workflow

1. **FxSxA Analysis** — Map script description to Function/Scale/Atmosphere
2. **Asset Collection/Build** — Select or build required 3D assets from library
3. **Spatial Layout** — Place scene geometry and props per narrative intent
4. **Lighting Setup** — Configure three-point + HDRI based on colorist intent
5. **Camera Previz** — Set camera paths per editor shot plan, verify feasibility
6. **Axis Calculation** — Output per-frame camera position + axis data (for editor)
7. **Material Annotation** — Tag all visible surface materials (for foley)
8. **Previz Render** — Low quality preview (960x540, EEVEE, 64 samples)
9. **Reference Frame Render** — High quality key frames (1920x1080, Cycles, 256 samples)
10. **Pipeline Package** — Output scene_3d_package + camera_constraints + material_annotations

## Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| narrative_space_match | >= 0.85 |
| camera_constraint_validity | >= 0.90 |
| asset_completeness | >= 0.80 |
| pipeline_integration_score | >= 0.85 |

## Collaboration

- **<- screenplay**: scene descriptions, lighting_mood, spatial requirements
- **<- style_genome**: genre spatial preferences, reference imagery
- **<- colorist**: lighting intent (color temp/direction/intensity)
- **<- performer**: character movement paths
- **<- editor**: shot planning, camera type requirements
- **-> drawer**: reference frame images (composition/lighting reference)
- **-> animator**: camera_constraints.json (camera path constraints)
- **-> editor**: axis data + previz video
- **-> foley**: material_annotations.json (surface material tags)
- **-> continuity**: scene layout reference (environment consistency audit)

## What NOT to do

- Don't exceed 500K tris per scene (Blender interactivity breaks)
- Don't skip camera path validation (impossible shots waste generation time)
- Don't forget material annotations (foley depends on them)
- Don't render final quality before previz approval (saves GPU time)
- Don't run scene_builder alongside drawer/animator on single GPU (combined >24GB)
