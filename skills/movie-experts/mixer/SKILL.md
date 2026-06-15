---
name: mixer
description: "Mixer Expert: multi-track mixing per Senior *Mixing Secrets*, dialogue ducking, EQ carving, LUFS-compliant mastering for cinematic soundscape."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, mixing, mastering, ducking, lufs, frequency, audio-balance, stems, senior-mixing-secrets]
    related_skills: [voicer, composer, foley, spatial_audio, editor, continuity]
    expert_id: mixer
    metrics: [level_compliance, frequency_masking_score, dialogue_intelligibility, dynamic_range_appropriateness]
---

# Mixer Expert (混音专家)

Multi-track audio mixing and mastering specialist using Senior *Mixing Secrets* heuristics for level balancing, frequency management, dialogue ducking, and LUFS-compliant final master processing per ITU-R BS.1770-4. **Phase 5 v1.5 RAG uplift** per REFACTOR-rest-04.

## When to use this skill

The user needs to mix multiple audio stems, balance dialogue/music/effects levels, apply ducking, manage frequency conflicts, master the final audio to platform-compliant LUFS, or produce the finished soundtrack for AI film production.

## References

本专家所有 mixing 与 LUFS compliance 阈值由下列 2 个 refs 独占定义(Phase 5 v1.5 light-refs uplift per REFACTOR-rest-04):

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/mixing-secrets-small-studio.md`](./references/mixing-secrets-small-studio.md) | 设计 mix 或 dialogue ducking 前 | Per-platform LUFS targets(抖音/快手/小程序剧/视频号/TikTok/YouTube/Spotify/Apple/cinema)+ dialogue ducking 4 参数 + 5 大频段职责分配 + EQ carve protocol + mastering chain 4 步 |
| [`references/lufs-standards.md`](./references/lufs-standards.md) | 验证 LUFS compliance 或 ffmpeg loudnorm 前 | ITU-R BS.1770-4 measurement spec(Integrated/Short-term/Momentary)+ K-weighting filter + ffmpeg two-pass loudnorm 命令 + per-platform compliance check protocol + 自动化 ebur128 verification |

## Knowledge Retrieval

在执行任何 mix / master / LUFS compliance check 前,按以下顺序检索上下文(2 个检索主题):

- **Per-platform LUFS + dialogue ducking + EQ carve + mastering chain** —— 详见 [`references/mixing-secrets-small-studio.md`](./references/mixing-secrets-small-studio.md)
- **ITU-R BS.1770-4 spec + ffmpeg loudnorm + ebur128 verification** —— 详见 [`references/lufs-standards.md`](./references/lufs-standards.md)

**若当前 runtime 中有 memory / RAG 工具**,使用以下查询范围:

```
tags="expert:mixer,domain:mixing-secrets-small-studio"
tags="expert:mixer,domain:lufs-standards"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件。

## Role & Philosophy

- Mixing is about hierarchy — dialogue is king, music serves, effects support
- The audience should never strain to hear dialogue
- Frequency real estate is finite; every stem earns its space

## Core Capabilities

- Multi-track mixing and level balancing (5-12 tracks simultaneously)
- Dialogue ducking automation (dialogue priority protection)
- Frequency avoidance and EQ carving
- Dynamic range control and mastering
- LUFS/LRA precision metering

## Output Format

- `mix_stereo.wav`: final stereo mix (48kHz, 24-bit)
- `mix_5.1.wav`: 5.1 surround mix (if spatial_audio requires)
- `mix_report.json`: per-track levels, frequency distribution, LUFS/LRA stats
- `stem_balance.json`: per-track gain/spectrum/ducking parameter records

## Key Parameters

### Multi-Track Mixing
- **max_tracks**: 12 (dialogue×N + music×2 + foley×N + ambience×2)
- **sample_rate**: 48000 Hz
- **bit_depth**: 24-bit
- **buffer_size**: 512-1024 samples
- **pan_range**: -1.0 (left) to +1.0 (right), 0.0 = center

### EQ Parameters
- **Dialogue**: HPF 80Hz, LF shelf -3dB @200Hz, presence +2dB @3kHz
- **Music**: LPF 16kHz, presence dip -4dB @2.5kHz (dialogue avoidance)
- **Foley**: custom per material, usually HPF 60Hz
- **Ambience**: LPF 8kHz, HPF 40Hz

### Compression
- **Dialogue bus**: threshold -18dB, ratio 3:1, attack 5ms, release 100ms
- **Music bus**: threshold -12dB, ratio 2:1, attack 20ms, release 300ms
- **Foley bus**: no compression (preserve transients), limiter -3dBFS only

### Ducking
- **duck_detector**: dialogue stem VAD
- **duck_depth_music**: -6 to -12 dB (when dialogue present)
- **duck_depth_ambience**: -3 to -6 dB
- **duck_attack**: 50-100ms
- **duck_release**: 200-500ms
- **hold_time**: 100-200ms after dialogue ends

### Mastering
- **LUFS_target**: -16.0 ± 1.0 (stereo), -24.0 ± 2.0 (5.1)
- **LRA_target**: 8-14 LU
- **True_peak**: -1.0 dBTP (stereo), -3.0 dBTP (5.1)
- **Dither**: triangular, for 24-to-16 bit downconversion

### GPU/CPU Budget
- Mixing: CPU-intensive | Monitoring latency: <20ms | VRAM: <= 1GB (visualization)

## Style Rules

### 4-Layer Hierarchy
1. **Dialogue** (highest) — always clear and intelligible
2. **Foley/SFX** (high) — synced to visual action
3. **Ambience** (medium) — spatial atmosphere
4. **Music** (lowest) — emotional space filler

### Level Balance
- Dialogue: -16 LUFS ± 1.5
- Music (with dialogue): -22 to -18 LUFS
- Music (solo): -20 to -14 LUFS
- Foley peaks: -12 to -8 dBFS
- Ambience bed: -35 to -30 LUFS

### Frequency Allocation
- Dialogue: 2000-5000Hz (sacred, never mask)
- Music LF: 20-200Hz (bass, kick)
- Music MF: 500-2000Hz (sidechain for dialogue avoidance)
- Music HF: 8000-20000Hz (air, shimmer)
- Foley: 100-12000Hz (distributed by material)

### Dynamic Range
- Target DR: 8-14 LU (EBU R128)
- Dialogue compression: 2:1-4:1
- Master limiter: -1.0 dBTP
- Stereo balance: no > ±1.5 dB offset

### Prohibited
- Dialogue masked by music or effects (zero tolerance)
- Over-compression causing pumping/breathing
- All tracks at same volume (no layering)
- Hard clipping (any track peak > 0 dBFS)
- Stereo imbalance > ±1.5 dB

## Workflow

1. **Track Loading** — Import all stems, sort by layer priority (dialogue > foley > ambience > music)
2. **Level Pre-balance** — Set baseline levels per track (dialogue -16 LUFS, etc.)
3. **EQ Carving** — Preserve dialogue clarity, music avoids 2000-5000Hz
4. **Ducking Setup** — Configure dialogue detection + auto gain reduction
5. **Frequency Masking Check** — Analyze full spectrum, flag conflict points
6. **Spatial Allocation** — Stereo/5.1 panning (coordinate with spatial_audio)
7. **Dynamic Range Control** — Compression + limiting, target DR 8-14 LU
8. **Mastering** — LUFS normalization + True Peak limiting + Dither
9. **Quality Audit** — Perceptual check + data validation
10. **Output** — mix_stereo.wav + mix_report.json + stem_balance.json

## Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| level_compliance | >= 0.88 |
| frequency_masking_score | >= 0.85 |
| dialogue_intelligibility | >= 0.92 |
| dynamic_range_appropriateness | >= 0.85 |

## Collaboration

- **<- voicer**: dialogue stems + metadata
- **<- composer**: music stems + coupled_beat.json
- **<- foley**: sound stems + foley_metadata.json
- **<- spatial_audio**: spatial field data + 5.1 panning instructions
- **<- editor**: edit timeline (audio sync)
- **-> spatial_audio**: post-mix stereo/5.1 output
- **-> continuity**: final audio consistency confirmation

## What NOT to do

- Don't let anything mask dialogue (zero tolerance policy)
- Don't compress beyond 4:1 on dialogue bus (causes pumping)
- Don't skip the frequency masking check (catches hidden conflicts)
- Don't exceed -1.0 dBTP True Peak (broadcast standard)
- Don't master without checking LUFS against target
