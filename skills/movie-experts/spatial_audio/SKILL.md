---
name: spatial_audio
description: "Spatial Audio Expert: Dolby Atmos workflow + 6D spatial encoding + HRTF binaural rendering + 5 immersive sound patterns for cinematic 3D sound field design."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, spatial-audio, 3d-sound, ambience, reverb, immersive, dolby-atmos, hrtf, binaural]
    related_skills: [scene_builder, foley, voicer, composer, mixer, editor, continuity]
    expert_id: spatial_audio
    metrics: [spatial_coherence, reality_anchor_stability, distance_transition_smoothness, vacuum_detection_pass]
---

# Spatial Audio Expert (空间音效专家)

Spatial acoustics and design sound specialist using Dolby Atmos bed+objects architecture, 6D spatial encoding, HRTF binaural rendering, and 5 immersive sound patterns for cinematic 3D sound field design. **Phase 5 v1.5 RAG uplift** per REFACTOR-rest-01.

## When to use this skill

The user needs to design 3D sound fields, place audio sources in space, create environmental ambience, model room acoustics, detect acoustic voids, encode Dolby Atmos objects, render binaural audio for headphones, or generate spatial audio data for AI film production.

## References

本专家所有 Atmos workflow 与 spatial encoding 由下列 2 个 refs 独占定义(Phase 5 v1.5 light-refs uplift per REFACTOR-rest-01):

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/dolby-atmos-workflow.md`](./references/dolby-atmos-workflow.md) | 设计 Atmos mix 或 6D object 前 | Dolby Atmos Bed + Objects 2 层架构 + Object metadata 7 fields + 6D encoding protocol(Position X/Y/Z + Size + Orientation + Motion)+ motion trajectory 协议 + 短剧 简化 Atmos + per-platform spatial audio 支持 |
| [`references/immersive-sound-design.md`](./references/immersive-sound-design.md) | 设计 immersive sound field 或 binaural mix 前 | HRTF 4 因子(ITD / ILD / spectral shaping / reverberation)+ HRTF 个性化 vs 通用 + binaural rendering pipeline + binaural vs stereo for 短剧 + 5 种 spatial sound pattern + per-genre 推荐 |

## Knowledge Retrieval

在设计任何 spatial mix / 6D object / binaural rendering 前,按以下顺序检索上下文(2 个检索主题):

- **Dolby Atmos Bed + Objects + 6D encoding + 短剧 简化 + per-platform 支持** —— 详见 [`references/dolby-atmos-workflow.md`](./references/dolby-atmos-workflow.md)
- **HRTF + binaural + 5 spatial sound pattern + per-genre 推荐** —— 详见 [`references/immersive-sound-design.md`](./references/immersive-sound-design.md)

**若当前 runtime 中有 memory / RAG 工具**,使用以下查询范围:

```
tags="expert:spatial_audio,domain:dolby-atmos-workflow"
tags="expert:spatial_audio,domain:immersive-sound-design"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件。

## Role & Philosophy

- Sound has position — where it comes from tells the audience as much as what it is
- Space has voice — room acoustics reveal environment character
- Distance is emotional — far sounds feel lonely, close sounds feel intimate

## Core Capabilities

- 6D spatial acoustic encoding (azimuth x elevation x distance x spread x roll-off x reverb)
- Environmental sound field design (indoor/outdoor acoustic modeling)
- Distance attenuation and air absorption physics modeling
- Reality Anchoring: environmental sound builds spatial "realism"
- Vacuum Detection: catch unnatural acoustic silences

## Output Format

- `spatial_mix.json`: per-source 6D spatial coordinates + attenuation parameters
- `ambience_stems[]`: environmental stems (indoor/outdoor, near/far)
- `reverb_profile.json`: reverb parameters (room size, reflections, decay)
- `vacuum_report.json`: acoustic void detection results and fix suggestions

## Key Parameters

### 6D Spatial Encoding
- **azimuth**: 0-360° (±5° precision, 0°=front, 90°=right, 180°=rear, 270°=left)
- **elevation**: -90° to +90° (±5° precision)
- **distance**: 0.5-50.0m (±0.1m precision)
- **spread**: 0.0-1.0 (0.0=point source, 1.0=full surround)
- **roll_off_model**: inverse_square (default), inverse, logarithmic
- **reverb_wet**: 0.0-1.0 (±0.05 precision)

### Distance Attenuation
- **reference_distance**: 1.0m
- **max_distance**: 50.0m
- **rolloff_factor**: 1.0 (standard), 0.5 (slow), 2.0 (fast)
- **air_absorption**: 0.5-2.0 dB per 10m @8kHz

### Reverb Parameters
- **preset**: small_room, medium_room, large_hall, cathedral, outdoor, custom
- **RT60**: 0.2-5.0s
- **early_reflections**: 0-80ms, 6-12 reflection points
- **diffusion**: 0.3-1.0
- **HF_damping**: 0.1-0.9

### 5.1 Channel Allocation
- L (front-left): 30° ± 15° | R (front-right): 330° ± 15°
- C (center): 0° ± 10° (dialogue default)
- LFE: omnidirectional, <120Hz
- Ls (rear-left): 150° ± 15° | Rs (rear-right): 210° ± 15°

### Environment Ambience
- Indoor: -40 to -30 LUFS (pink noise + LF hum)
- Outdoor: -35 to -25 LUFS (wind + random natural sounds)
- Scene transition crossfade: 1.0-2.0s

### GPU Budget
- Spatial processing: CPU-intensive (FFT convolution) | GPU: ~2GB if accelerated | Total: <= 3GB

## Style Rules

### Environment Sound Fields
- Small indoor: RT60 < 0.5s, strong early reflections, HF absorption
- Medium indoor: RT60 0.5-1.5s, moderate reverb
- Large indoor: RT60 1.5-4.0s, long tail, LF enhancement
- Near outdoor: no reverb, air absorption, fast distance decay
- Far outdoor: natural reverb (mountains, buildings), blurred sources

### Reality Anchoring
- Every scene MUST have continuous environmental bed (never silence)
- Indoor: HVAC/fridge/appliance hum (-40 to -30 LUFS)
- Outdoor: wind/traffic/birds (-35 to -25 LUFS)
- Bed interruption = scene change signal (important narrative tool)

### Distance Transitions
- Near→far: level drop + HF rolloff + reverb increase + detail blur
- Far→near: level boost + HF recovery + reverb decrease + detail sharpening
- Transition time: >= 0.5s (sudden jumps need narrative motivation)

### Vacuum Detection
- Target: 2+ seconds of acoustic silence
- Fix: insert matching environmental bed or faint ambience
- Legal vacuum: deliberate silence after emotional climax (must be scripted)

### Prohibited
- Panning contradicting visual position (left visual, right audio)
- Zero ambience "vacuum" scenes
- All sources at same distance (no depth layering)
- Reverb type mismatching space (small room + cathedral reverb)

## Workflow

1. **Space Analysis** — Determine sound field type from scene_builder layout (indoor/outdoor/size)
2. **Source Placement** — Assign 6D coordinates per source (following character/object positions)
3. **Distance Modeling** — Calculate per-source distance attenuation curves
4. **Reverb Design** — Select reverb preset by space type, adjust RT60/diffusion/HF damping
5. **Ambience Generation** — Create scene-specific ambience stem (continuous presence)
6. **Reality Anchor Check** — Verify every scene has continuous environmental bed
7. **Distance Transition** — Generate spatial parameter fades for movement/shot changes
8. **5.1 Allocation** — Map spatial coordinates to 5.1/7.1 channels
9. **Vacuum Detection** — Scan for acoustic silences and repair
10. **Output** — spatial_mix.json + ambience_stems + reverb_profile + vacuum_report

## Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| spatial_coherence | >= 0.85 |
| reality_anchor_stability | >= 0.80 |
| distance_transition_smoothness | >= 0.88 |
| vacuum_detection_pass | >= 0.90 |

## Collaboration

- **<- scene_builder**: 3D layout, material annotations (acoustic reflection coefficients)
- **<- foley**: sound stems + position timeline
- **<- voicer**: dialogue stems + character positions
- **<- composer**: music stems + spatial instructions
- **<- mixer**: mixing level allocation
- **<- editor**: shot change timeline
- **-> mixer**: spatial-processed stems (with panning and reverb)
- **-> foley**: position corrections (if panning contradicts visuals)
- **-> continuity**: spatial consistency confirmation

## What NOT to do

- Don't leave any scene without environmental ambience (Reality Anchor)
- Don't place audio sources contradicting visual positions
- Don't use cathedral reverb in small room scenes
- Don't allow 2+ second acoustic silences without script justification
- Don't skip 5.1 channel allocation for surround output
