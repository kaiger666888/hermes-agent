---
name: visual_executor
description: "Visual Executor Expert: unified FLUX 2 image gen (drawer sub-step) + 2026 Hermes-catalog video gen (animator sub-step) for cinematic visual + temporal consistency. Sub-steps: [drawer, animator]."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm, hermes_llm_vision]
sub_steps: [drawer, animator]
metadata:
  hermes:
    tags: [movie, image, video, flux-2, lora, ip-adapter, instantid, video-gen, camera-motion, temporal-consistency, veo, kling, ltx, pixverse, visual, cinematic, character-consistency]
    related_skills: [screenplay, continuity_auditor, colorist, style_genome, compliance_gate, cinematographer, production, scene_builder, editor, performer]
    expert_id: visual_executor
    aliases: [drawer, animator]
    metrics: [aesthetic_score, character_consistency, film_realism, vram_efficiency, motion_smoothness, motion_complexity, temporal_consistency, generation_fidelity]
---

# Visual Executor Expert (视觉执行专家)

Unified cinematic visual + temporal consistency expert for AI 短剧 / 微电影 production. Merges the **drawer sub-step** (FLUX 2 Klein 9B + LoRA + IP-Adapter + InstantID for cinematic still images + first-frame I-frames) and the **animator sub-step** (2026 Hermes-catalog video gen models — veo3.1 / kling-v3-4k / pixverse-v6 / ltx-2.3 / seedance-2.0 — for cinematic camera motion + temporal consistency).

Per Phase 7 §4.8 + PITFALLS §2.1: **consistency context unified; specialization loss acceptable**. The two sub-steps share a unified character-consistency + color + lighting reference frame, eliminating the cross-expert handoff drift that the v1 drawer→animator collaboration bullet had to paper over.

**Sub-steps (declared in frontmatter):** `[drawer, animator]`

## When to use this skill

The user needs to produce visual assets for AI film production:

- **Stills / key frames / character reference shots / first-frame I-frames** → invoke the **drawer sub-step** (FLUX 2 image generation).
- **Video clips from still frames, camera-movement sequences, animated shot segments** → invoke the **animator sub-step** (video gen models).
- **Cross-shot visual + temporal consistency audit** → both sub-steps share a unified consistency stack (LoRA + IP-Adapter + InstantID + CLIP-T + LPIPS + Face embedding + Object IoU).

Requires `hermes_llm_vision` for visual quality assessment and character consistency verification.

## Sub-steps

This expert has two declared sub-steps:

| Sub-step | Role | When invoked | Output |
|----------|------|--------------|--------|
| **drawer** | FLUX 2 Klein 9B cinematic still image generation + first-frame I-frames + character consistency stack | Any scene that needs a still image, key frame, character reference shot, or I-frame for video gen | High-resolution PNG + generation metadata JSON |
| **animator** | 2026 Hermes-catalog video gen models (veo3.1 / kling-v3-4k / pixverse-v6 / ltx-2.3 / seedance-2.0 / happy-horse) for camera motion + temporal consistency | Any scene that needs motion; requires drawer's first_frame as I-frame input | MP4 (H.264, 24fps) + motion metadata JSON |

**Handoff contract:** drawer generates the first_frame image → animator consumes it as I-frame input. Per Phase 7 §4.8 this is now an intra-expert handoff (same expert_id `visual_executor`), not an inter-expert edge.

## References

本专家所有 FLUX 2 推理参数 + character consistency stack + video gen model 选择 + temporal consistency 阈值由下列 5 个 refs 独占定义(Phase 5 v1.5 light-refs uplift per REFACTOR-rest-09 + REFACTOR-rest-10):

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/drawer/flux2-parameter-surface.md`](./references/drawer/flux2-parameter-surface.md) | 生成任何 image 或替换 FLUX 1.x phantom 前 | FLUX 2 Klein 9B 推理参数(num_inference_steps / guidance_scale / max_sequence_length)+ 与 SDXL / FLUX 1.x 对比 + 5 大 prompt 工程原则 + 短剧 9:16 vertical generation 协议 + FLUX 1.x Karras samplers phantom strip |
| [`references/drawer/character-consistency-lora.md`](./references/drawer/character-consistency-lora.md) | 设计 character consistency 或训练 LoRA 前 | LoRA vs IP-Adapter vs InstantID 三方法对比 + 组合协议(consistency stack 强度和 1.0-2.0)+ LoRA training hyperparameters + IP-Adapter weight 调整 + InstantID face identity lock + character ID 4 层验证 |
| [`references/animator/video-gen-model-matrix.md`](./references/animator/video-gen-model-matrix.md) | 选择 video gen model 或替换 Wan family phantom 前 | Hermes 6-model catalog(veo3.1 / kling-v3-4k / pixverse-v6 / ltx-2.3 / seedance-2.0 / happy-horse)+ per-scene complexity → model 选择 + Wan family phantom 替换 + 短剧 9:16 vertical generation 协议 + multi-clip concatenation |
| [`references/animator/temporal-consistency.md`](./references/animator/temporal-consistency.md) | 验证跨 frame / 跨 clip 一致性 前 | CLIP-T + LPIPS + Face embedding + Object IoU 4 层 metric 阈值 + per-clip metric 抽样 + character ID drift detection + temporal flicker mitigation + object permanence 协议 |
| [`references/animator/camera-execution-and-degradation.md`](./references/animator/camera-execution-and-degradation.md) | 执行 storyboard → video-gen 或降级处理失败 shot 时 | Storyboard shot → prompt assembly + 4-level degradation strategy + async batch processing + seedance-style async API + cross-shot extension chain + per-scene vs per-shot generation trade-off |

## Knowledge Retrieval

在生成任何 image / character reference / I-frame / video clip / motion metadata / temporal consistency report 输出前,按以下顺序检索上下文(4 个检索主题):

- **FLUX 2 推理参数 + prompt 工程 + 短剧 vertical generation + phantom strip** —— 详见 [`references/drawer/flux2-parameter-surface.md`](./references/drawer/flux2-parameter-surface.md)
- **LoRA + IP-Adapter + InstantID 三方法组合 + training + verification** —— 详见 [`references/drawer/character-consistency-lora.md`](./references/drawer/character-consistency-lora.md)
- **Hermes video gen 6-model matrix + per-scene 选择 + Wan family phantom 替换 + multi-clip concatenation** —— 详见 [`references/animator/video-gen-model-matrix.md`](./references/animator/video-gen-model-matrix.md)
- **CLIP-T + LPIPS + Face embedding + Object IoU 4 层 temporal consistency 验证 + flicker mitigation** —— 详见 [`references/animator/temporal-consistency.md`](./references/animator/temporal-consistency.md)

**若当前 runtime 中有 memory / RAG 工具**,使用以下查询范围:

```
tags="expert:visual_executor,sub:drawer,domain:flux2-parameter-surface"
tags="expert:visual_executor,sub:drawer,domain:character-consistency-lora"
tags="expert:visual_executor,sub:animator,domain:video-gen-model-matrix"
tags="expert:visual_executor,sub:animator,domain:temporal-consistency"
```

**若无此类工具**,回退到本目录 `references/{drawer,animator}/*.md` 静态文件。

## Sub-step: Drawer (Image Generation)

FLUX 2 Klein 9B + LoRA + IP-Adapter + InstantID specialist for cinematic visual quality, character consistency, and film-like aesthetics in AI-generated imagery. **Phase 5 v1.5 RAG uplift:** FLUX 1.x Karras samplers (euler_a / dpmpp_2m) phantom stripped per Phase 0 GAP-REPORT;FLUX 2 推理参数 + character consistency stack documented in refs.

### Role & Philosophy

- Real cinema aesthetic over stylized/2D looks
- Parameter precision over trial-and-error
- VRAM efficiency without quality sacrifice

### Core Capabilities

- FLUX model parameter optimization for photorealistic output
- LoRA combination management (character + style)
- Cinematic composition and lighting design
- Character consistency enforcement across frames
- Film grain and natural lighting integration

### Output Format

- High-resolution images (1024x1024 base, scaled for aspect ratio)
- First-frame images for animator I-frame reference
- Metadata JSON: prompt, LoRA weights, generation parameters

### Key Parameters

#### FLUX 2 Generation (Phase 5 v1.5 updated)
- **model**: `fal-ai/flux-2/klein/9b` (Hermes default per `tools/image_generation_tool.py:372`)
- **num_inference_steps**: 12 (preview), 28 (production) — per [`references/drawer/flux2-parameter-surface.md`](./references/drawer/flux2-parameter-surface.md) §FLUX 2 推理参数
- **guidance_scale**: 3.5 (FLUX 2 default, lower than SDXL's 7.0)
- **max_sequence_length**: 256-512 (FLUX 2 supports longer prompts)
- **resolution**: 1024×1024 base (横屏), 1080×1920 (短剧 vertical 9:16)
- **negative_prompt**: supported (FLUX 2 修正)

> **NOTE:** 旧 SKILL.md 的 `euler_a` / `dpmpp_2m` / `cfg_scale: 3.5-5.0` 是 phantom — FLUX 2 不使用 Karras samplers,使用 distilled flow matching。已 strip per Phase 0 GAP-REPORT。详见 [`references/drawer/flux2-parameter-surface.md`](./references/drawer/flux2-parameter-surface.md) §Phantom Strip: FLUX 1.x samplers。

#### Character Consistency Stack (Phase 5 v1.5 new)
per [`references/drawer/character-consistency-lora.md`](./references/drawer/character-consistency-lora.md):
- **Character LoRA**: scale 0.65-0.90 (per character type, see ref §LoRA scale 推荐)
- **IP-Adapter**: weight 0.40-0.60 (variable wardrobe / lighting)
- **InstantID**: weight 0.50-0.70 (face identity lock for close-up)
- **Total stack strength**: 1.0-2.0 (sum of all weights; > 2.5 = over-constrained)

#### VRAM Budget
- Max 22GB total on RTX 3090
- Reserve 4GB for system overhead
- Batch size: 1

### Style Rules

#### Visual Style
- Photorealistic rendering with film grain
- Natural lighting with cinematic color grading
- Shallow depth of field for subject focus

#### Composition Rules
- Rule of thirds with intentional breaking
- Leading lines and negative space
- Dynamic angles for emotional impact

#### Prohibited
- No 2D cartoon/anime style
- No oversaturated HDR look
- No artificial bokeh patterns

### Workflow

1. **Parse Input** — Extract scene description from screenplay
2. **Prompt Construction** — Generate FLUX prompt from scene + style genome
3. **LoRA Selection** — Select combination based on character/scene requirements
4. **Preview Render** — Low steps (20 steps) for quick validation
5. **Character Consistency Check** — Validate against reference (uses `hermes_llm_vision`)
6. **Production Render** — Full steps (30-50) at target resolution
7. **Quality Check** — Verify against thresholds (uses `hermes_llm_vision`)

### Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| aesthetic_score | >= 8.0 |
| character_consistency | >= 0.85 |
| film_realism | >= 8.0 |
| vram_efficiency | >= 0.7 |

### What NOT to do

- Don't exceed 22GB VRAM (single RTX 3090 constraint)
- Don't use total LoRA weight > 1.5 (causes artifacting)
- Don't generate anime/2D style for film production
- Don't skip the preview step (saves VRAM and iteration time)
- Don't ignore character LoRA for multi-shot sequences (consistency breaks)

## Sub-step: Animator (Video Generation)

2026 Hermes-catalog video gen model specialist for cinematic camera motion design, temporal consistency enforcement, and dynamic quality in AI-generated video clips. **Phase 5 v1.5 RAG uplift:** Wan family phantom references (wan2 / wan22 / wan22_video) replaced with Hermes-catalog models per Phase 0 GAP-REPORT.

### Role & Philosophy

- Cinematic camera language over random motion
- Temporal coherence is non-negotiable
- Motion must serve narrative, never distract

### Core Capabilities

- Cinematographic grammar (pan/tilt/dolly/tracking/crane)
- Motion blur and physics simulation literacy
- Temporal consistency enforcement across frame sequences
- Camera velocity curve design (ease-in/out, acceleration profiles)

### Output Format

- Video clip per shot (MP4, H.264, 24fps)
- Motion metadata JSON: `camera_path`, `velocity_curve`, `motion_tags`

### Key Parameters

#### Video Generation
- **model**: `<video_gen_primary>` (primary), `<video_gen_preview>` (preview only)
- **sampling_steps**: 30-50 (preview: 20, production: 40)
- **cfg_scale**: 7.0-9.0 (lower = more motion freedom)
- **fps**: 24 (standard), 16 (slow-motion), 8 (timelapse)
- **resolution**: 832x480 (standard), 480x832 (vertical), 1024x576 (high quality)
- **duration**: 3-6 seconds per clip

#### Camera Control
- **camera_speed**: 0.0-1.0 (0=static, 0.3=gentle, 0.7=dynamic, 1.0=extreme)
- **camera_type**: pan_left, pan_right, tilt_up, tilt_down, dolly_in, dolly_out, crane_up, crane_down, orbit, static
- **camera_ease**: linear, ease_in, ease_out, ease_in_out (default: ease_in_out)
- **motion_intensity**: 0.0-1.0 (controls subject motion)

#### I-frame Reference
- **source**: drawer's first_frame image (mandatory)
- **weight**: 0.7-0.9 (higher = stronger adherence)

#### VRAM Budget
- 832x480 @40 steps: ~18GB | 1024x576 @40 steps: ~22GB (RTX 3090 limit)
- Batch size: 1 always | FP16 for 30% VRAM reduction

### Style Rules

#### Camera Motion
- Max angular velocity: 15°/s for pans/tilts
- Dolly speed: 0.1-0.5 units/s
- Crane/jib: emotional emphasis only
- Use dolly-in/out instead of digital zoom

#### Temporal Consistency
- No object morphing between frames
- Character silhouette must remain stable
- Lighting consistency with colorist's CxSxZ encoding

#### Prohibited
- Whiplash camera moves without narrative justification
- Constant motion (every shot needs >= 2s stillness)
- Physics violations (floating objects, wrong limb bends)
- Motion contradicting emotional tone

### Workflow

1. **Motion Planning** — Map camera type + speed + ease per shot from narrative intent
2. **Preview Generation** — Low-step (20 steps) at 832x480 for motion validation
3. **Temporal Check** — Verify frame-to-frame consistency (no morphing, no drift)
4. **Camera Velocity Review** — Confirm motion serves narrative
5. **Production Render** — Full-step (40 steps) at target resolution
6. **Metadata Export** — Generate motion JSON with camera_path and velocity_curve
7. **Sync Validation** — Verify duration matches editor's timing requirements

### Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| motion_smoothness | >= 0.85 |
| motion_complexity | 0.3-0.8 range |
| temporal_consistency | >= 0.90 |
| generation_fidelity | >= 0.80 |

### What NOT to do

- Don't generate video without a first_frame I-frame reference
- Don't exceed 22GB VRAM (RTX 3090 hard limit)
- Don't use turbo mode for final output (preview only)
- Don't generate clips longer than 6 seconds (concatenate instead)
- Don't run drawer and animator concurrently on single GPU (both peak ~22GB)

## Collaboration

> **Merged collaboration graph.** Cross-references to OTHER experts (cinematographer, colorist, continuity_auditor, editor, scene_builder, performer, production, screenplay, style_genome, compliance_gate) remain inter-expert edges. References between the drawer and animator sub-steps are now intra-expert handoffs (internal to `visual_executor`) — see the `## Sub-steps` section above.

### Drawer sub-step inbound / outbound (external experts)

- **<- screenplay**: scene descriptions, lighting_mood
- **<- style_genome**: composition + color + light_shadow signals
- **<- performer**: action_prompt (character pose/action descriptions)
- **<- colorist**: color_intent.json (influences generation parameters)
- **→ [internal handoff to Animator sub-step — see §Sub-step: Animator above]**: first_frame image as I-frame reference
- **-> continuity_auditor**: production frames for cross-shot consistency audit
- **-> colorist**: raw frames for color grading

### Animator sub-step inbound / outbound (external experts)

- **← [internal handoff from Drawer sub-step — see §Sub-step: Drawer above]**: first_frame image as I-frame input (mandatory)
- **<- scene_builder**: camera_constraints and 3D previsualization
- **<- editor**: beat timing and shot duration
- **<- performer**: character motion/action parameters
- **<- colorist**: CxSxZ temporal consistency reference
- **-> continuity_auditor**: video clip for cross-shot consistency audit

## Changelog

- **2026-06-17** — Merged `drawer` (v1.1.0) + `animator` (v1.1.0) into `visual_executor` (v1.0.0) per Phase 14 MERGE-01. **Predecessors:** `skills/movie-experts/drawer/SKILL.md`, `skills/movie-experts/animator/SKILL.md` (both now redirect-only stubs with `status: merged_into` + `merged_into: visual_executor`). **Rationale:** Phase 7 §4.8 + PITFALLS §2.1 — "consistency context unified; specialization loss acceptable". The drawer→animator inter-expert edge is now an intra-expert handoff between two sub-steps of one expert_id (`visual_executor`), eliminating the consistency context drift between the two phases of the visual pipeline. **Backward-compat aliases:** `metadata.hermes.aliases: [drawer, animator]` declared per FOUND-08 (zero silent merges — aliases declared explicitly). **New top-level frontmatter field:** `sub_steps: [drawer, animator]` per v2.0 PRFP DAG convention. **Refs:** 7 ref files (3 drawer-side + 4 animator-side) migrated verbatim to `references/{drawer,animator}/` sub-folders. **GAP-REPORT:** consolidated from both predecessors.
