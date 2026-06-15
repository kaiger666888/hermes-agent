# Dolby Atmos Workflow — Renderer + Bed + Objects + 6D Encoding

**Source:** Dolby *Atmos Production Suite Guide* (2024);Dolby Atmos Cinema + Home specs;AES 10-channel spec;Hermes spatial_audio tool catalog(2026-06);Apple Spatial Audio + Sony 360 Reality Audio 对比 specs。
**Copyright:** Fair Use — paraphrased workflow; no proprietary Atmos renderer internals. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 spatial_audio 专家在 **Dolby Atmos / 6D spatial encoding** 决策时的**权威源**。它涵盖 Atmos renderer workflow + bed channels + objects + 6D encoding(3D position + size + orientation + motion + divergence + reverb)。

## Dolby Atmos Bed + Objects Architecture

### 关键 heuristic 1 (load-bearing): Bed + Objects 2 层架构

Dolby Atmos 用 2 层 audio 架构:

| 层 | 描述 | 典型 use |
|----|------|----------|
| **Bed channels** | 7.1.2 或 9.1.6 fixed channel(包含 LFE + L/R + C + Ls/Rs + Lrs/Rrs + Ltf/Rtf + Ltr/Rtr) | Ambient + music + 整体 mix |
| **Objects** | 最多 118 个 dynamic audio objects(每个含 position + size + orientation) | Specific SFX + dialogue + character voice |

**Atmos 总 channel count:** 7.1.2 bed + 118 objects = typical cinema config;Consumer(home / 短剧):7.1.2 bed + 12-20 objects。

### 关键 heuristic 2: Object metadata 7 fields

每个 Atmos object 必须 specify:

| Field | 范围 | 用途 |
|-------|------|------|
| **Position X** | -1 to 1(left to right)| 水平位置 |
| **Position Y** | -1 to 1(front to back)| 前后位置 |
| **Position Z** | 0 to 1(bottom to top)| 高度 |
| **Size** | 0 to 1(point to large)| 声音 size(point source vs diffuse)|
| **Divergence** | 0 to 1| 距离越远 divergence ↑ |
| **Snap** | 0 / 1| 是否 snap to bed channel |
| **ZoneMask** | bitmask | 限制 zone(如 "仅头顶")|

---

## 6D Encoding Protocol

### 关键 heuristic 3 (load-bearing): 6D spatial encoding 6 维度

per spatial_audio SKILL.md §6D Spatial Encoding:

| 维度 | 描述 | 范围 |
|------|------|------|
| **1. Position X (azimuth)** | 水平方位 | -180° to +180° |
| **2. Position Y (elevation)** | 高度方位 | -90° to +90° |
| **3. Position Z (distance)** | 距离 | 0.1m to 100m |
| **4. Size** | 声音 size | 0 (point) to 1 (diffuse) |
| **5. Orientation** | 朝向(directional sound) | azimuth × elevation |
| **6. Motion** | 动态 trajectory | spline curve through (X, Y, Z) over time |

### 关键 heuristic 4: Motion trajectory 协议

Object 在 time-series 上的 motion trajectory:

```json
{
  "object_id": "SFX_helicopter_001",
  "trajectory": [
    {"t_sec": 0.0, "x": -1.0, "y": 0.5, "z": 0.7, "size": 0.3},
    {"t_sec": 1.0, "x": -0.5, "y": 0.6, "z": 0.8, "size": 0.3},
    {"t_sec": 2.0, "x":  0.0, "y": 0.7, "z": 0.9, "size": 0.3},
    {"t_sec": 3.0, "x":  0.5, "y": 0.6, "z": 0.8, "size": 0.3},
    {"t_sec": 4.0, "x":  1.0, "y": 0.5, "z": 0.7, "size": 0.3}
  ],
  "interpolation": "catmull_rom"
}
```

---

## 短剧 / 微电影 Atmos Adaptation

### 关键 heuristic 5: 短剧 简化 Atmos

短剧 不需要 cinema-grade Atmos。简化 protocol:

| 层 | 短剧 推荐 | Cinema 标准 |
|----|-----------|-------------|
| **Bed** | 2.0 stereo 或 5.1 | 7.1.2 |
| **Objects** | 0-3(headphone playback 不需 objects)| 12-118 |
| **Vertical(Z)** | 仅 key moment 用 | 持续用 |
| **Motion** | 仅 SFX(doorbell / phone)| 持续 trajectory |

### 关键 heuristic 6: Per-platform spatial audio 支持

| Platform | Spatial audio 支持 | 短剧 推荐 |
|----------|-------------------|-----------|
| 抖音 | ❌(stereo only)| Stereo mix |
| 快手 | ❌ | Stereo mix |
| 小程序剧 | ❌ | Stereo mix |
| 视频号 | ❌ | Stereo mix |
| TikTok | ✅ Apple Spatial Audio 头戴耳机 | 可选 binaural mix |
| YouTube | ✅ 360 audio + Ambisonics | 可选 spatial |
| Cinema | ✅ Dolby Atmos / DTS:X | Full Atmos |

**关键规则:** CN 平台 stereo only;海外 platform 可选 spatial。

---

## Anti-Patterns

### 关键 heuristic 7: Spatial audio 5 大 anti-pattern

1. **Full Atmos for 短剧 anti-pattern:** 短剧 用 7.1.2 + 118 objects 浪费资源。**Mitigation:** Stereo + 0-3 objects。
2. **No motion trajectory anti-pattern:** Static object。**Mitigation:** trajectory for moving sound。
3. **Wrong Z-dimension usage anti-pattern:** 短剧 over-use vertical Z。**Mitigation:** Z 仅 key moment。
4. **Stereo-only for cinema anti-pattern:** Cinema 用 stereo。**Mitigation:** Full Atmos for cinema。
5. **No platform-specific mix anti-pattern:** 同一 mix 全平台。**Mitigation:** per-platform 短剧 stereo / cinema Atmos。

---

## Glossary

- **Bed channel:** Atmos 固定 channel(7.1.2 / 9.1.6)。
- **Object:** Atmos dynamic audio element(含 position + size + orientation)。
- **6D encoding:** X (azimuth) + Y (elevation) + Z (distance) + Size + Orientation + Motion。
- **Divergence:** 距离衰减。
- **Binaural:** 双耳 3D audio 模拟(headphone playback)。

---

*Generated: 2026-06-15 as part of Phase 5 REFACTOR-rest-01 (spatial_audio RAG uplift).*
*Source provenance: Dolby Atmos Production Suite Guide (2024) / Dolby Atmos Cinema+Home specs / AES / Hermes spatial_audio catalog / Apple Spatial Audio + Sony 360 RA specs — fair use paraphrase + short technical phrases only.*
