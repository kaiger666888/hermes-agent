# Mixing Secrets for Small Studio — LUFS + Dialogue Ducking + EQ Carving

**Source:** Mike Senior *Mixing Secrets for the Small Studio* (2nd ed, 2019, Routledge, ISBN 978-1138318906);Katz *Mastering Audio* (4th ed, 2013);ITU-R BS.1770-4 spec(2015);AES Streaming Loudness recommendations(2020)。
**Copyright:** Fair Use — paraphrased mixing heuristics; no verbatim chapter content. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 mixer 专家在 **multi-track mixing** 决策时的**权威源**。它涵盖 LUFS standards + dialogue ducking + frequency management (EQ carving)+ mastering for streaming platforms。

## LUFS Standards

### 关键 heuristic 1 (load-bearing): Per-platform LUFS targets

per ITU-R BS.1770-4 + AES Streaming Loudness + platform specs(2026):

| Platform | Target LUFS (integrated)| True Peak (dBTP)| 备注 |
|----------|-------------------------|------------------|------|
| 抖音 | -14 LUFS | -1 dBTP | 短剧 标准 |
| 快手 | -14 LUFS | -1 dBTP | 同抖音 |
| 小程序剧 | -14 LUFS | -1 dBTP | 同抖音 |
| 视频号 | -16 LUFS | -1 dBTP | 较安静 |
| TikTok | -14 LUFS | -1 dBTP | 全球标准 |
| YouTube | -14 LUFS | -1 dBTP | 全球标准 |
| Spotify | -14 LUFS | -1 dBTP | 全球标准 |
| Apple Music | -16 LUFS | -1 dBTP | 较安静 |
| 影院 | -27 LUFS | -2 dBTP | theatrical mix |

### 关键 heuristic 2: Loudness penalty 规避

若 mix target = -10 LUFS(过响),platforms 自动 normalize 到 -14 LUFS,导致动态范围压缩 + audible pumping。

**规则:** Mix to -14 LUFS integrated;若需要更响,用 limiter 而非 compressor(避免 pumping)。

---

## Dialogue Ducking Protocol

### 关键 heuristic 3 (load-bearing): Dialogue ducking 4 参数

| 参数 | 推荐值 | 备注 |
|------|--------|------|
| **Threshold** | -25 dBFS(dialogue 触发 level)| Dialogue 进入时触发 ducking |
| **Reduction depth** | -6 to -12 dB(music duck)| Dialogue 时 music 下降 |
| **Attack** | 50-100 ms | Ducking 触发速度 |
| **Release** | 300-500 ms | Ducking 恢复速度 |

### 关键 heuristic 4: Per-frequency ducking

per Senior *Mixing Secrets* §Frequency Management:

- Music 主要 energy 在 low-mid(200-500Hz),与 dialogue 重叠 → 必须 ducking
- 高频(2kHz+)music 与 dialogue 高频冲突 → sidechain EQ carve
- Low-frequency(SFX < 200Hz)与 dialogue 不冲突 → 不需 ducking

---

## Frequency Management (EQ Carving)

### 关键 heuristic 5: 5 大频段职责分配

| 频段 | 主要 owner | 备注 |
|------|-----------|------|
| 20-80 Hz | Sub-bass SFX(explosion / impact)| Reserved for impact |
| 80-200 Hz | Music bass / Foley low | Music + SFX share |
| 200-500 Hz | Music low-mid + dialogue warmth | **Conflict zone — ducking required** |
| 500Hz-2kHz | Dialogue intelligibility | **Dialogue priority, music carve EQ** |
| 2-6 kHz | Dialogue presence + SFX | Shared but dialogue dominant |
| 6-20 kHz | Music high + SFX detail | Music + SFX share |

### 关键 heuristic 6: EQ carve protocol

```yaml
# Dialogue priority EQ carve on music
music_eq_carve:
  - freq: 1500 Hz
    q: 1.5
    gain_db: -4  # carve to make dialogue room
  - freq: 2500 Hz
    q: 1.2
    gain_db: -3
  - freq: 3500 Hz
    q: 1.0
    gain_db: -2
```

---

## Mastering for Streaming

### 关键 heuristic 7: Mastering chain 4 步

1. **EQ corrective:** Fix any frequency imbalances
2. **Compression (glue):** 2:1 ratio, slow attack, ~3dB gain reduction
3. **Limiter:** -1 dBTP ceiling, no audible pumping
4. **LUFS metering:** Verify target -14 LUFS integrated

---

## Anti-Patterns

### 关键 heuristic 8: Mixing 5 大 anti-pattern

1. **Wrong LUFS target anti-pattern:** Mix to -10 LUFS → loudness penalty。**Mitigation:** -14 LUFS。
2. **No dialogue ducking anti-pattern:** Music 与 dialogue 同 level。**Mitigation:** 4 参数 ducking。
3. **Frequency conflict unhandled anti-pattern:** Music 与 dialogue 在 1-3kHz 重叠。**Mitigation:** EQ carve。
4. **Pumping audible anti-pattern:** Compressor 释放过快。**Mitigation:** 用 limiter 替代。
5. **No true peak limiter anti-pattern:** 超过 -1 dBTP 导致 distortion。**Mitigation:** -1 dBTP ceiling。

---

## Glossary

- **LUFS:** Loudness Units relative to Full Scale,per ITU-R BS.1770-4。
- **True Peak (dBTP):** Inter-sample peak,digital-to-analog conversion 后的 peak。
- **Ducking:** 自动降低 music level 当 dialogue 进入。
- **EQ carve:** 用 EQ 在 music 上 "carve" 出 dialogue 频段空间。
- **Pumping:** Compressor 释放产生的 audible level fluctuation。

---

*Generated: 2026-06-15 as part of Phase 5 REFACTOR-rest-04 (mixer RAG uplift).*
*Source provenance: Senior 2019 Mixing Secrets / Katz 2013 Mastering Audio / ITU-R BS.1770-4 / AES Streaming Loudness — fair use paraphrase + short technical phrases only.*
