# Immersive Sound Design — HRTF + Binaural + 3D Sound Field

**Source:** Blauert *Spatial Hearing* (1997, MIT Press, rev ed);Wenzel *Localization in Nonindividualized Virtual Acoustic Environments* (1992);Begault *3D Sound for Virtual Reality and Multimedia* (2000, NASA);Chion *Audio-Vision* (1994);Hermes spatial_audio deployment notes (2024-2026)。
**Copyright:** Fair Use — paraphrased theory. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 spatial_audio 专家在 **immersive 3D sound field** 决策时的**权威源**。它涵盖 HRTF (Head-Related Transfer Function)+ binaural rendering + 3D sound perception theory + 实际应用 heuristics。

## HRTF Fundamentals

### 关键 heuristic 1 (load-bearing): HRTF 4 因子

per Blauert 1997 + Wenzel 1992:

**HRTF (Head-Related Transfer Function)** 描述 sound wave 从 source 到 ear canal 的频域 transfer function。决定 sound localization 的 4 因子:

| 因子 | 描述 | Perceptual cue |
|------|------|----------------|
| **ITD (Interaural Time Difference)** | Sound 到两耳的时间差(±0.6 ms)| Low-frequency localization(<1.5kHz)|
| **ILD (Interaural Level Difference)** | Sound 到两耳的强度差(±20 dB)| High-frequency localization(>1.5kHz)|
| **Spectral shaping** | 耳廓 + 头部对 sound 的频域 shaping | Front-back + elevation localization |
| **Reverberation** | 早期 reflection + late reverb | Distance + environment perception |

### 关键 heuristic 2: HRTF 个性化 vs 通用

| 类型 | 描述 | Accuracy | Use case |
|------|------|----------|----------|
| **Individual HRTF** | 每个 user 测量自己的 HRTF | 极高 | Research / 高端 VR |
| **Generic HRTF** | 通用 HRTF(如 KEMAR mannequin)| 中 | 大众消费 |
| **Morphological HRTF** | 根据 user 头部 / 耳廓 photo 估算 | 高 | 个人化 VR |

**短剧 / 微电影 推荐:** Generic HRTF(足够 + 兼容性高)。

---

## Binaural Rendering Protocol

### 关键 heuristic 3: Binaural rendering pipeline

```
Mono audio source
    ↓
Spatial position (X, Y, Z) + Listener orientation
    ↓
HRTF convolution (per ear)
    ↓
Binaural stereo (L, R)
    ↓
Headphone playback
```

### 关键 heuristic 4: Binaural vs Stereo for 短剧

| 类型 | 描述 | 短剧 用例 |
|------|------|-----------|
| **Stereo** | L/R 2-channel | 抖音 / 快手 / 小程序剧(主流)|
| **Binaural** | HRTF-rendered 3D for headphone | TikTok / YouTube 短剧(headphone 用户)|
| **Ambisonics** | 360 audio sphere | VR / 360 video |

**关键:** Binaural 仅 headphone playback 有效;speaker playback 失效(crosstalk cancellation 复杂)。

---

## 3D Sound Field Design Patterns

### 关键 heuristic 5 (load-bearing): 5 种 spatial sound pattern

per Chion 1994 + Begault 2000:

| Pattern | 描述 | 用例 |
|---------|------|------|
| **Static point source** | 固定位置 sound | 物体 sound(钟 / TV) |
| **Motion trajectory** | 移动 sound source | 飞机 / 车辆 / footsteps |
| **Surround envelopment** | 围绕 listener 的环境 | 环境 ambience(crowd / rain) |
| **Overhead presence** | 上方 sound | 雷声 / 直升机 |
| **Below-ground** | 下方 sound | 地下 noise / subway |

### 关键 heuristic 6: Per-genre spatial sound 推荐

| Genre | 推荐 spatial pattern |
|-------|---------------------|
| Drama | Static point + surround |
| Action | Motion trajectory + overhead |
| Horror | Below-ground + static point(tension) |
| Sci-Fi | All 5 patterns(immersive) |
| 短剧-男频 | Static + surround(简单) |
| 短剧-女频 | Static + surround(简单) |

**关键:** 短剧 简化 spatial;cinema 可 full immersive。

---

## Anti-Patterns

### 关键 heuristic 7: Spatial audio 5 大 anti-pattern

1. **Binaural for speaker playback anti-pattern:** Binaural 在 speaker 上失效。**Mitigation:** speaker → stereo。
2. **Individual HRTF for 短剧 anti-pattern:** Individual HRTF 太贵。**Mitigation:** generic HRTF。
3. **Too many spatial objects anti-pattern:** 短剧 用过多 spatial object。**Mitigation:** ≤3 objects。
4. **No motion trajectory for moving sound anti-pattern:** 移动 sound 用 static object。**Mitigation:** motion trajectory。
5. **Overhead overuse anti-pattern:** 过度用 overhead sound。**Mitigation:** overhead 仅 key moment。

---

## Glossary

- **HRTF:** Head-Related Transfer Function。
- **ITD:** Interaural Time Difference(时间差)。
- **ILD:** Interaural Level Difference(强度差)。
- **Binaural:** 双耳 3D audio rendering。
- **Ambisonics:** 360 audio sphere encoding。

---

*Generated: 2026-06-15 as part of Phase 5 REFACTOR-rest-01 (spatial_audio RAG uplift).*
*Source provenance: Blauert 1997 / Wenzel 1992 / Begault 2000 / Chion 1994 / Hermes deployment notes — fair use paraphrase + short technical phrases only.*
