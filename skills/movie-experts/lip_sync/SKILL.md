---
name: lip_sync
description: "Lip Sync Expert: audio-driven lip synchronization for AI 短剧 / 微电影 character footage. Generates mouth-motion-aligned video from (video + audio) pairs using latent diffusion. The only movie-expert with international-standard benchmark (LRS2/LRS3) and objective metrics (LSE/LSE-C) — no LLM-as-judge required for validation."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, lip-sync, audio-driven, video-generation, benchmark, talking-head, digital-human]
    related_skills: [voicer, performer, editor, animator, mixer, continuity]
    expert_id: lip_sync
    metrics: [lip_sync_error, lip_sync_confidence, temporal_consistency, identity_preservation]
---

# Lip Sync Expert (唇形同步专家)

Audio-driven lip-sync specialist for AI 短剧 / 微电影 character footage. Takes (person-speaking video + target audio) and produces a new video where the mouth motion matches the target audio, while preserving identity, expression, and head pose. **Decoupled from [`voicer`](../voicer/SKILL.md)**: voicer synthesizes the audio; lip_sync aligns the audio to existing or generated visual footage. The two compose in series: voicer → lip_sync.

## When to use this skill

The user needs one of:
- **口播视频 / digital human** — a character (real-person footage OR AI-generated avatar) must speak the dialogue audio produced by [`voicer`](../voicer/SKILL.md)
- **多语言重配音** — same footage, re-dubbed in another language; lip motion must match the new audio
- **角色对话镜头** — generated character animation needs lip-sync to dialogue audio
- **batch 口播生成** — generate N variations of the same footage with different audio tracks

**Do NOT confuse with [`voicer`](../voicer/SKILL.md)**: voicer *produces audio*. lip_sync *aligns audio to video*. Calling sequence: voicer produces `dialogue.wav` → lip_sync consumes (footage.mp4 + dialogue.wav) → outputs synced footage.

## References

本专家所有数值阈值由下列 4 个 refs 独占定义;SKILL.md body 仅作摘要 + 跨链。

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/sync-quality-metrics.md`](./references/sync-quality-metrics.md) | 评估输出视频质量或构造 benchmark 前 | LSE (Lip Sync Error) 公式 + LSE-C (Lip Sync Confidence) + SyncNet confidence score + LRS2/LRS3 国际标准 benchmark 协议 + 行业 SOTA 阈值(LSE ≤ 6.5 / LSE-C ≥ 7.0)|
| [`references/latentsync-deployment.md`](./references/latentsync-deployment.md) | 部署 LatentSync 推理服务前 | v1.5 (8GB / 256×256) vs v1.6 (18GB / 512×512) 显存要求 + 推理参数(inference_steps 20-50 / guidance_scale 1.0-3.0)+ DeepCache 加速 + Linux/Windows/ComfyUI/Replicate 5 部署路径 + 中文优化建议 |
| [`references/audio-video-input-spec.md`](./references/audio-video-input-spec.md) | 准备输入素材前 | 视频输入要求(MP4 / 25fps / 正面人脸 / 无遮挡)+ 音频输入要求(WAV / 16000Hz / 长度匹配)+ 失败模式(侧脸 / 多人 / 遮挡 / 光线不足)+ 4-tier 输入质量评级 |
| [`references/identity-preservation.md`](./references/identity-preservation.md) | 验证输出视频角色一致性 前 | Identity preservation 3 层验证(面部结构 / 表情 / 头部姿态)+ 跨帧抖动检测 + 与 [`continuity`](../continuity/SKILL.md) expert 的 handoff 协议 |

## Role & Philosophy

- **唯一国际标准 benchmark 专家** — LRS2 / LRS3 是全球公认的 lip-sync 评估数据集,LSE / LSE-C 是业界标准指标。本专家的产出质量**不依赖 LLM-as-judge**,可直接用 SyncNet 客观验证。
- **音频驱动而非视频重生成** — 只修改嘴部区域,保留面部其他部分、表情、头部姿态、身份。这是与 [`animator`](../animator/SKILL.md) 的核心区别:animator 从零生成视频,lip_sync 在已有视频上做局部修改。
- **口型精度优先于画质** — 数字人/口播场景下,口型与音频的对齐误差 > 120ms 会被观众感知为不同步,即使其他画质指标优秀。
- **与 [`continuity`](../continuity/SKILL.md) 协作** — 输出的视频必须通过 continuity expert 的"identity preservation"审计,确保角色身份在 shot 内不漂移。

## Knowledge Retrieval

在生成任何 synced video 前,按以下顺序检索上下文(4 个检索主题):

- **LSE / LSE-C 计算公式 + LRS2/LRS3 benchmark 协议 + SOTA 阈值** —— 详见 [`references/sync-quality-metrics.md`](./references/sync-quality-metrics.md)
- **LatentSync 部署路径 + 显存要求 + 推理参数** —— 详见 [`references/latentsync-deployment.md`](./references/latentsync-deployment.md)
- **输入素材规格 + 失败模式 + 质量评级** —— 详见 [`references/audio-video-input-spec.md`](./references/audio-video-input-spec.md)
- **Identity preservation 验证 + 抖动检测 + continuity handoff** —— 详见 [`references/identity-preservation.md`](./references/identity-preservation.md)

**若当前 runtime 中有 memory / RAG 工具**,使用以下查询范围:

```
tags="expert:lip_sync,domain:sync-quality-metrics"
tags="expert:lip_sync,domain:latentsync-deployment"
tags="expert:lip_sync,domain:audio-video-input-spec"
tags="expert:lip_sync,domain:identity-preservation"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件。

> **NOTE:** 本 SKILL.md body 不引用任何具体外部模型名。涉及具体模型时使用 `<lip_sync_primary>` / `<lip_sync_fallback>` 占位符。模型名只出现在 `references/*.md` 与 [`../_shared/known-external-models.yaml`](../_shared/known-external-models.yaml) allowlist 中。

## Core Capabilities

- **Audio-driven lip motion generation** — Whisper 音频嵌入 → U-Net 交叉注意力 → TREPA 时间对齐 → SyncNet 三重损失优化
- **Identity preservation** — 只修改嘴部 ROI,保留面部其他结构;每帧的 identity embedding cosine similarity ≥ 0.92 (per [`references/identity-preservation.md`](./references/identity-preservation.md) §3-layer verification)
- **Multi-resolution support** — 256×256 (v1.5, 8GB VRAM) 与 512×512 (v1.6, 18GB VRAM) 双档,根据 GPU 自适应
- **Batch processing** — 输入 (video, audio) pair list,顺序处理 + checkpoint resume
- **Quality self-check** — 推理完成后自动计算 SyncNet confidence;若 < 阈值,触发 retry 或 downgrade
- **Multi-provider execution** — LatentSync 本地推理 (primary) / Replicate API (cloud fallback) / ComfyUI node (workflow integration)

## Output Format

```json
{
  "type": "LipSyncResult",
  "version": "1.0.0",
  "input": {
    "video_path": "/path/to/input.mp4",
    "audio_path": "/path/to/dialogue.wav",
    "video_duration_seconds": 12.5,
    "audio_duration_seconds": 12.3
  },
  "output": {
    "video_path": "/path/to/synced.mp4",
    "resolution": "512x512",
    "fps": 25
  },
  "quality": {
    "lip_sync_error_LSE": 5.8,
    "lip_sync_confidence_LSE_C": 7.4,
    "syncnet_confidence": 0.89,
    "identity_cosine_sim": 0.94,
    "temporal_jitter_p95_ms": 45
  },
  "quality_grade": "A",
  "deployment": {
    "engine": "<lip_sync_primary>",
    "version": "1.6",
    "inference_steps": 25,
    "guidance_scale": 1.5,
    "deepcache_enabled": true,
    "vram_used_gb": 19.2,
    "processing_time_seconds": 47.3
  },
  "warnings": [],
  "continuity_handoff": {
    "identity_preservation_passed": true,
    "scene_ref": "shot_04_take_02",
    "character_ref": "char_wuji",
    "needs_continuity_audit": true
  }
}
```

### Quality grade scale

| Grade | LSE | LSE-C | SyncNet conf | Action |
|---|---|---|---|---|
| **A** (Excellent) | ≤ 6.0 | ≥ 7.5 | ≥ 0.85 | Ship as-is |
| **B** (Acceptable) | 6.0-7.0 | 6.5-7.5 | 0.75-0.85 | Ship; flag for review |
| **C** (Marginal) | 7.0-8.5 | 5.5-6.5 | 0.65-0.75 | Retry with higher inference_steps |
| **D** (Failed) | > 8.5 | < 5.5 | < 0.65 | Re-examine input quality or switch model |

## Key Parameters

### Engine selection (provider-agnostic)

- **primary engine**: `<lip_sync_primary>` (per [`../_shared/known-external-models.yaml`](../_shared/known-external-models.yaml) — currently a latent-diffusion method, model name in references only)
- **fallback engine**: `<lip_sync_fallback>` (GAN-based, faster but lower quality; used when VRAM < 8GB or processing-time budget < 30s)

### Resolution vs VRAM trade-off

| Resolution | Min VRAM | Recommended VRAM | Use case |
|---|---|---|---|
| 256×256 (v1.5) | 8 GB | 10 GB | Fast preview, low-end GPU |
| 512×512 (v1.6) | 18 GB | 24 GB | Final delivery, hides blur |

### Inference parameters

- **`inference_steps`**: 20 (fast) - 50 (high-quality); default 25
- **`guidance_scale`**: 1.0-3.0; default 1.5; higher = sharper lip but more jitter
- **`deepcache`**: enabled (default) — 30-40% speed-up with negligible quality loss
- **`mask_dilation`**: 0-10 pixels; default 4 — controls how far beyond mouth ROI the diffusion can edit

### Input specifications

- **Video**: MP4, recommended 25fps, H.264; face must be frontal, well-lit, single-person
- **Audio**: WAV, 16000Hz sample rate, mono; duration ≤ video duration
- **Aspect**: any; face ROI auto-detected; output preserves input aspect

## Workflow

1. **Pre-check input** — validate video + audio per [`references/audio-video-input-spec.md`](./references/audio-video-input-spec.md) §4-tier input quality rating. If input is D-tier (multi-person / occlusion / extreme angle), reject with guidance.
2. **Select resolution** — based on available VRAM (auto-detect or user-specified), pick v1.5 or v1.6.
3. **Configure parameters** — based on quality target (preview / final) + time budget.
4. **Execute inference** — call primary engine; on OOM or timeout, downgrade to fallback engine.
5. **Quality self-check** — compute LSE, LSE-C, SyncNet confidence, identity cosine sim. If grade < B, retry with adjusted parameters or downgrade resolution.
6. **Continuity handoff** — emit `continuity_handoff` block for downstream audit if `identity_cosine_sim < 0.95` or scene involves cross-shot character continuity.

## Quality Thresholds

| Threshold | Value | Source |
|---|---|---|
| LSE SOTA (industry) | ≤ 6.5 | [`references/sync-quality-metrics.md`](./references/sync-quality-metrics.md) |
| LSE-C SOTA (industry) | ≥ 7.0 | [`references/sync-quality-metrics.md`](./references/sync-quality-metrics.md) |
| SyncNet confidence (A grade) | ≥ 0.85 | [`references/sync-quality-metrics.md`](./references/sync-quality-metrics.md) |
| Identity cosine sim (must-pass) | ≥ 0.92 | [`references/identity-preservation.md`](./references/identity-preservation.md) |
| Temporal jitter p95 | ≤ 60ms | [`references/identity-preservation.md`](./references/identity-preservation.md) |
| Audio-video drift (per [`../_shared/cognitive-resonance-metrics.md`](../_shared/cognitive-resonance-metrics.md) §Scale 1) | < 120ms | shared neural-layer threshold |

## Collaboration

### Upstream

- **<- [`voicer`](../voicer/SKILL.md)** — `dialogue.wav` 音频输入
- **<- [`animator`](../animator/SKILL.md)** — silent character video footage(角色对话镜头无音频版)
- **<- [`performer`](../performer/SKILL.md)** — performance baseline(表情、头部姿态基线)

### Downstream

- **-> [`editor`](../editor/SKILL.md)** — synced footage 进入剪辑
- **-> [`continuity`](../continuity/SKILL.md)** — identity preservation 审计
- **-> [`mixer`](../mixer/SKILL.md)** — 最终音频与视频对齐

## What NOT to do

- ❌ **不要重新生成整段视频** — 这是 [`animator`](../animator/SKILL.md) 的职责。lip_sync 只修改嘴部 ROI。
- ❌ **不要接受 D-tier 输入** — 侧脸 / 多人 / 遮挡 / 光线不足的视频会输出垃圾。必须 reject 并引导用户重拍或切换到 animator。
- ❌ **不要忽略 SyncNet 客观指标** — LLM-judge 不可靠,必须用 SyncNet 数学指标判定 grade。任何"看起来还行"的主观判断都不合格。
- ❌ **不要在没有 LSE benchmark 的情况下声称"SOTA"** — 必须在 LRS2/LRS3 测试集上跑出 LSE ≤ 6.5 才能声称 SOTA;否则只能说"达到 X 等级"。
- ❌ **不要忽略 identity 漂移** — 输出视频与输入视频的 identity cosine similarity < 0.92 时,即使 LSE 优秀也必须 VETO 并触发 continuity handoff。
- ❌ **不要把 LatentSync 写死在 SKILL.md body** — 模型名只在 references/*.md 中,SKILL.md 使用 `<lip_sync_primary>` 占位符。provider-agnostic 是硬约束。

## Validation protocol (how to know if this expert improved)

本专家的核心 KPI 是**LSE / LSE-C 在 LRS2/LRS3 上的实测分数**——全球公认的客观指标,不需要 LLM-judge,不需要 A/B 测试:

1. **Download LRS2 / LRS3 test set**:公开数据集,从 https://github.com/JoonSon/LipSync 或官方来源下载。
2. **Run lip_sync on each test sample**:输入 (video, audio) pair,输出 synced video。
3. **Compute LSE / LSE-C / SyncNet confidence**:用 SyncNet model(预训练)计算每个输出视频的 LSE / LSE-C。
4. **Compare against SOTA baselines**: LatentSync v1.6 paper claims LSE = 5.13 / LSE-C = 8.25 on LRS2. 本专家的目标 = match or exceed。
5. **Iteration signal**: 当 references/*.md 更新或参数调整后,LSE 必须不下降。下降 = 配置回归。

校准脚本和 LRS2/LRS3 evaluation harness 位于 [`_eval/lip_sync_benchmark/`](./_eval/lip_sync_benchmark/)(若不存在,operator 需创建并下载 LRS2/LRS3)。
