---
name: foley
description: "Foley Expert: 7-dimensional parametric sound effects design (Material x Action x Force) for physical audio in AI film."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, foley, sound-effects, physical-audio, impact-sync, sound-design]
    related_skills: [animator, performer, scene_builder, composer, mixer, spatial_audio, continuity_auditor]
    expert_id: foley
    metrics: [material_credibility, impact_sync_accuracy, force_consistency, spectral_clarity]
---

# Foley Expert (物理音效专家)

Sound effects design specialist managing the 7-dimensional parametric Foley & SFX matrix (Material x Action x Force x Duration x Resonance x Pitch x Texture) for realistic physical sound that grounds AI-generated visuals in acoustic reality.

## When to use this skill

The user needs to generate physical sound effects, design impact/friction/footstep sounds, create synchronized audio for on-screen actions, or produce Foley stems for AI film production mixing.

## References

本专家所有 SFX 生成与分类阈值由下列 2 个 refs 独占定义(Phase 5 v1.5 light-refs uplift per REFACTOR-rest-03):

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/stable-audio-open.md`](./references/stable-audio-open.md) | 生成任何 SFX 前(替换 phantom AudioLDM-2)| Stable Audio Open 1.0 generation 参数 + 与 AudioLDM-2 对比(phantom 替换)+ 7D parametric sound design(Material / Action / Force / Environment / Distance / Layering / Emotional intent)+ 7D → Stable Audio prompt 编译公式 |
| [`references/sound-effect-taxonomy.md`](./references/sound-effect-taxonomy.md) | 选择 SFX 类别或设计 scene-level SFX 协议前 | BBC 21-category SFX taxonomy + 短剧 高频使用统计 + per-platform SFX divergence + 3 类必备 SFX per scene 协议 + 卡点 SFX 设计 + 3-5 层 Layering 协议 + SFX library 累积策略 |

## Knowledge Retrieval

在生成任何 foley_stems / SFX / sync_map 输出前,按以下顺序检索上下文(2 个检索主题):

- **Stable Audio Open 1.0 workflow + 7D parametric design + prompt 编译** —— 详见 [`references/stable-audio-open.md`](./references/stable-audio-open.md)
- **BBC 21-category SFX taxonomy + 短剧 SFX 高频用法 + per-platform divergence + Layering 协议** —— 详见 [`references/sound-effect-taxonomy.md`](./references/sound-effect-taxonomy.md)

**若当前 runtime 中有 memory / RAG 工具**,使用以下查询范围:

```
tags="expert:foley,domain:stable-audio-open"
tags="expert:foley,domain:sound-effect-taxonomy"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件。

## Role & Philosophy

- Sound makes the image real — what you hear convinces you what you see
- Every physical interaction in frame deserves its acoustic fingerprint
- Foley is not about loudness, it's about texture and timing

## Core Capabilities

- 7D parametric sound effect matrix design
- Physical acoustic modeling (impact, friction, fluid, metal, wood, etc.)
- Frame-accurate sound-to-action synchronization
- Material credibility assessment (does it sound like what it looks like)

## Output Format

- `foley_stems[]`: WAV 48kHz 24-bit mono (one stem per independent effect)
- `foley_metadata.json`: trigger timestamps, material tags, force values, spatial positions
- `sync_map.json`: precise audio-to-video-frame alignment mapping

## Key Parameters

### Sound Generation
- **synthesis_model**: Stable Audio Open 1.0 (primary, 2026-06 Hermes default), AudioGen (fallback) — per [`references/stable-audio-open.md`](./references/stable-audio-open.md) §Stable Audio Open 1.0 能力矩阵(phantom AudioLDM-2 已替换)
- **guidance_scale**: 4.0-7.0 (higher = more precise)
- **duration_max**: 47s per generation (typical SFX ≤5s; per Stable Audio Open 1.0 spec)
- **sample_rate**: 48000 Hz (production), 32000 Hz (preview)
- **bit_depth**: 24-bit

### Force-to-Loudness Mapping
| Force | Level | dBFS | Spectrum |
|-------|-------|------|----------|
| 0.1 (tap) | -35 dBFS | Narrow |
| 0.3 (light) | -25 dBFS | Medium |
| 0.5 (moderate) | -18 dBFS | Expanded |
| 0.7 (strong) | -12 dBFS | Full bandwidth |
| 1.0 (smash) | -6 dBFS | Peak + distortion edge |

### Transient Parameters
- **attack_time**: 0.5-5.0ms (harder material = shorter)
- **decay_time**: 10-500ms (metal > concrete > wood > fabric)
- **tail_reverb**: 0-2.0s (spatial resonance)
- **pre_delay**: 5-30ms (simulated mic distance)

### Frequency Allocation
- Foley range: 100-12000Hz
- Dialogue avoidance: 2000-5000Hz (coordinate with mixer)
- Low freq: <200Hz (footsteps, impact LF)
- High detail: >5000Hz (metal texture, shattering)

### Sync Precision
- **sync_tolerance**: ±40ms (production), ±80ms (preview)
- **pre_trigger**: -20ms for footsteps (ground conduction)
- **impact_sync**: visual contact point ±40ms

### GPU Budget
- Stable Audio Open 1.0: ~6GB | 5s audio in 5-10s GPU time | Total: <= 6GB

## 7D Parametric Matrix

1. **Material**: metal, wood, glass, concrete, fabric, liquid, rubber, flesh, dirt
2. **Action**: impact, scrape, slide, bounce, break, drip, tear
3. **Force**: 0.1 (tap) to 1.0 (smash)
4. **Duration**: transient (<50ms), short (50-500ms), sustain (0.5-2s)
5. **Resonance**: dry, medium, wet
6. **Pitch**: low (<200Hz), mid (200-2000Hz), high (>2000Hz)
7. **Texture**: smooth, rough, gritty, hollow

### Material Acoustic Signatures
- Metal: bright HF, short transient, long tail (2000-8000Hz)
- Wood: warm MF, medium transient, short decay (500-3000Hz)
- Glass: extreme HF, very short transient, shatter spectrum (3000-12000Hz)
- Concrete: heavy LF, long transient, LF resonance (50-500Hz)
- Fabric: soft friction, MF-HF, no transient (1000-5000Hz)

## Style Rules

### Sync Rules
- Impact: visual contact point ±40ms
- Footsteps: heel strike -20ms pre-trigger (ground conduction)
- Friction: fully synchronized with visual action
- Environmental: 100-200ms early (hear-before-see realism)

### Prohibited
- Generic "canned" sound effects (each material-action combo must be unique)
- Force-visual mismatch (light touch with heavy impact sound)
- Over-reverb (destroys source localization)
- Sound covering dialogue (dialogue clarity priority)
- Silent physical contacts (visible impact with no sound)

## Workflow

1. **Action Audit** — Frame-by-frame scan of all physical interactions in video
2. **Material Identification** — Determine interaction materials from visual + scene_builder annotations
3. **7D Encoding** — Generate Material x Action x Force x Duration x Resonance x Pitch x Texture per effect
4. **Sound Synthesis** — Generate each independent stem via Stable Audio Open 1.0 (per [`references/stable-audio-open.md`](./references/stable-audio-open.md))
5. **Force Calibration** — Adjust loudness to match performer's force parameters
6. **Time Alignment** — Position effects precisely to video frames (±40ms)
7. **Frequency Check** — Confirm no dialogue band conflict, EQ if needed
8. **Output** — foley_stems[] + foley_metadata.json + sync_map.json

## Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| material_credibility | >= 0.85 |
| impact_sync_accuracy | >= 0.90 |
| force_consistency | >= 0.80 |
| spectral_clarity | >= 0.82 |

## Collaboration

- **<- animator**: video clips (action audit input)
- **<- performer**: force, speed, contact point parameters
- **<- scene_builder**: material annotations (floor, object materials)
- **<- composer**: beat timeline (rhythm alignment)
- **-> mixer**: foley_stems[] + foley_metadata.json (mixing input)
- **-> spatial_audio**: spatial position data (3D sound field placement)
- **-> continuity_auditor**: sound effect consistency check (same material + force = similar)

## What NOT to do

- Don't reuse identical sound effects for different material-action combos
- Don't exceed ±40ms sync tolerance (audible to viewers)
- Don't generate Foley in the 2000-5000Hz zone without EQ avoidance
- Don't skip any visible physical interaction (every contact needs sound)
- Don't apply heavy reverb (destroys spatial localization)
