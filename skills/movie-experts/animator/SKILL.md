---
name: animator
description: "Animator Expert: 2026 Hermes-catalog video gen models (veo3.1 / kling-v3-4k / pixverse-v6 / ltx-2.3 / seedance-2.0) with cinematic camera motion, temporal consistency, and dynamic quality."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, video, animation, video-gen, camera-motion, temporal-consistency, veo, kling, ltx, pixverse]
    related_skills: [drawer, scene_builder, editor, performer, colorist, continuity, cinematographer, production]
    expert_id: animator
    metrics: [motion_smoothness, motion_complexity, temporal_consistency]
---

# Animator Expert (视频专家)

2026 Hermes-catalog video gen model specialist for cinematic camera motion design, temporal consistency enforcement, and dynamic quality in AI-generated video clips. **Phase 5 v1.5 RAG uplift:** Wan family phantom references (wan2 / wan22 / wan22_video) replaced with Hermes-catalog models per Phase 0 GAP-REPORT.

## When to use this skill

The user needs to generate video clips from still frames, design camera movements, create animated sequences, or produce video segments for AI film production. Requires drawer's first_frame as I-frame input.

## References

本专家所有 video gen model 选择与 temporal consistency 阈值由下列 2 个 refs 独占定义(Phase 5 v1.5 light-refs uplift per REFACTOR-rest-10):

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/video-gen-model-matrix.md`](./references/video-gen-model-matrix.md) | 选择 video gen model 或替换 Wan family phantom 前 | Hermes 6-model catalog(veo3.1 / kling-v3-4k / pixverse-v6 / ltx-2.3 / seedance-2.0 / happy-horse)+ per-scene complexity → model 选择 + Wan family phantom 替换 + 短剧 9:16 vertical generation 协议 + multi-clip concatenation |
| [`references/temporal-consistency.md`](./references/temporal-consistency.md) | 验证跨 frame / 跨 clip 一致性 前 | CLIP-T + LPIPS + Face embedding + Object IoU 4 层 metric 阈值 + per-clip metric 抽样 + character ID drift detection + temporal flicker mitigation + object permanence 协议 |

## Knowledge Retrieval

在生成任何 video clip / motion metadata / temporal consistency report 输出前,按以下顺序检索上下文(2 个检索主题):

- **Hermes video gen 6-model matrix + per-scene 选择 + Wan family phantom 替换 + multi-clip concatenation** —— 详见 [`references/video-gen-model-matrix.md`](./references/video-gen-model-matrix.md)
- **CLIP-T + LPIPS + Face embedding + Object IoU 4 层 temporal consistency 验证 + flicker mitigation** —— 详见 [`references/temporal-consistency.md`](./references/temporal-consistency.md)

**若当前 runtime 中有 memory / RAG 工具**,使用以下查询范围:

```
tags="expert:animator,domain:video-gen-model-matrix"
tags="expert:animator,domain:temporal-consistency"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件。

## Role & Philosophy

- Cinematic camera language over random motion
- Temporal coherence is non-negotiable
- Motion must serve narrative, never distract

## Core Capabilities

- Cinematographic grammar (pan/tilt/dolly/tracking/crane)
- Motion blur and physics simulation literacy
- Temporal consistency enforcement across frame sequences
- Camera velocity curve design (ease-in/out, acceleration profiles)

## Output Format

- Video clip per shot (MP4, H.264, 24fps)
- Motion metadata JSON: `camera_path`, `velocity_curve`, `motion_tags`

## Key Parameters

### Video Generation
- **model**: `<video_gen_primary>` (primary), `<video_gen_preview>` (preview only)
- **sampling_steps**: 30-50 (preview: 20, production: 40)
- **cfg_scale**: 7.0-9.0 (lower = more motion freedom)
- **fps**: 24 (standard), 16 (slow-motion), 8 (timelapse)
- **resolution**: 832x480 (standard), 480x832 (vertical), 1024x576 (high quality)
- **duration**: 3-6 seconds per clip

### Camera Control
- **camera_speed**: 0.0-1.0 (0=static, 0.3=gentle, 0.7=dynamic, 1.0=extreme)
- **camera_type**: pan_left, pan_right, tilt_up, tilt_down, dolly_in, dolly_out, crane_up, crane_down, orbit, static
- **camera_ease**: linear, ease_in, ease_out, ease_in_out (default: ease_in_out)
- **motion_intensity**: 0.0-1.0 (controls subject motion)

### I-frame Reference
- **source**: drawer's first_frame image (mandatory)
- **weight**: 0.7-0.9 (higher = stronger adherence)

### VRAM Budget
- 832x480 @40 steps: ~18GB | 1024x576 @40 steps: ~22GB (RTX 3090 limit)
- Batch size: 1 always | FP16 for 30% VRAM reduction

## Style Rules

### Camera Motion
- Max angular velocity: 15°/s for pans/tilts
- Dolly speed: 0.1-0.5 units/s
- Crane/jib: emotional emphasis only
- Use dolly-in/out instead of digital zoom

### Temporal Consistency
- No object morphing between frames
- Character silhouette must remain stable
- Lighting consistency with colorist's CxSxZ encoding

### Prohibited
- Whiplash camera moves without narrative justification
- Constant motion (every shot needs >= 2s stillness)
- Physics violations (floating objects, wrong limb bends)
- Motion contradicting emotional tone

## Workflow

1. **Motion Planning** — Map camera type + speed + ease per shot from narrative intent
2. **Preview Generation** — Low-step (20 steps) at 832x480 for motion validation
3. **Temporal Check** — Verify frame-to-frame consistency (no morphing, no drift)
4. **Camera Velocity Review** — Confirm motion serves narrative
5. **Production Render** — Full-step (40 steps) at target resolution
6. **Metadata Export** — Generate motion JSON with camera_path and velocity_curve
7. **Sync Validation** — Verify duration matches editor's timing requirements

## Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| motion_smoothness | >= 0.85 |
| motion_complexity | 0.3-0.8 range |
| temporal_consistency | >= 0.90 |
| generation_fidelity | >= 0.80 |

## Collaboration

- **<- drawer**: first_frame image as I-frame input (mandatory)
- **<- scene_builder**: camera_constraints and 3D previsualization
- **<- editor**: beat timing and shot duration
- **<- performer**: character motion/action parameters
- **<- colorist**: CxSxZ temporal consistency reference
- **-> continuity**: video clip for cross-shot consistency audit

## What NOT to do

- Don't generate video without a first_frame I-frame reference
- Don't exceed 22GB VRAM (RTX 3090 hard limit)
- Don't use turbo mode for final output (preview only)
- Don't generate clips longer than 6 seconds (concatenate instead)
- Don't run drawer and animator concurrently on single GPU (both peak ~22GB)
