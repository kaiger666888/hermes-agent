# LUFS Standards + Platform Specs — Detailed Compliance

**Source:** ITU-R BS.1770-4 (2015) + ITU-R BS.1771-1;EBU R128 (2011);AES TC-HFA Streaming Loudness recommendations (2020);platform-specific audio normalization specs (抖音 / 快手 / 小程序剧 / 视频号 / TikTok / YouTube / Spotify / Apple Music);ffmpeg loudnorm documentation。
**Copyright:** Fair Use — paraphrased standards. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 提供 LUFS standard 详细 reference + ffmpeg loudnorm 命令 + per-platform compliance 检查协议。与 mixing-secrets-small-studio.md 互补(前者概览,本文档详细规范)。

## ITU-R BS.1770-4 Measurement Spec

### 关键 heuristic 1 (load-bearing): Integrated / Short-term / Momentary LUFS

| Metric | Window | 用途 |
|--------|--------|------|
| **Integrated LUFS** | 整个 audio file | Final target compliance |
| **Short-term LUFS** | 3-second sliding window | Per-scene loudness |
| **Momentary LUFS** | 400-ms sliding window | Per-event loudness |

**规则:** Integrated 必须 = target(-14 LUFS 短剧);Short-term 最大 +1 LUFS tolerance;Momentary 无硬性上限但 True Peak 必须 ≤ -1 dBTP。

### 关键 heuristic 2: K-weighting filter

ITU-R BS.1770-4 用 K-weighting filter 模拟人耳 loudness perception:
- Stage 1:High-shelf filter (+4 dB at 1.5kHz)模拟 head-related transfer function
- Stage 2:High-pass filter (HP at 38Hz)模拟 low-frequency insensitivity

K-weighting 已 baked into all LUFS measurements(无需手动 apply)。

---

## ffmpeg loudnorm 命令

### 关键 heuristic 3: ffmpeg two-pass loudnorm

```bash
# Pass 1: measure
ffmpeg -i input.wav -af loudnorm=I=-14:TP=-1:LRA=11:print_format=json -f null -

# Pass 2: apply
ffmpeg -i input.wav -af loudnorm=I=-14:TP=-1:LRA=11:measured_I=<pass1_I>:measured_TP=<pass1_TP>:measured_LRA=<pass1_LRA> output.wav
```

参数说明:
- `I=-14`: Target Integrated LUFS
- `TP=-1`: Target True Peak (dBTP)
- `LRA=11`: Loudness Range target(typical 7-15)
- Two-pass:Pass 1 measure → Pass 2 apply measured values

---

## Per-Platform Compliance Check

### 关键 heuristic 4 (load-bearing): Compliance check protocol

每个 final mix 必须 verify:

1. **Integrated LUFS** matches target ±0.5 LUFS tolerance
2. **True Peak** ≤ -1 dBTP(no clipping)
3. **Loudness Range (LRA)** 7-15(comfortable dynamic range)
4. **No silence > 3s**(避免观众上滑,短剧 specific)
5. **Sample rate** 48kHz(production standard)

### 关键 heuristic 5: 自动化 compliance check

```bash
# 使用 ffmpeg + libebur128
ffmpeg -i output.wav -filter_complex ebur128=peak=true -f null - 2>&1 | grep -E "I:|LRA:|Threshold:|Peak:"
```

输出:
```
  I:         -14.0 LUFS   ← Integrated
  LRA:        11.0 LU     ← Loudness Range
  Threshold: -24.0 LUFS   ← gating threshold
  Peak:       -1.0 dBFS   ← True Peak
```

---

## Anti-Patterns

### 关键 heuristic 6: LUFS compliance 5 大 anti-pattern

1. **Single-pass loudnorm anti-pattern:** 用 single-pass,精度差。**Mitigation:** two-pass。
2. **Wrong target for platform anti-pattern:** Mix to -16 LUFS for 抖音。**Mitigation:** -14 LUFS for 短剧。
3. **True Peak > -1 dBTP anti-pattern:** Clipping。**Mitigation:** -1 dBTP limiter ceiling。
4. **LRA too compressed anti-pattern:** LRA < 5 (over-compressed)。**Mitigation:** LRA 7-15。
5. **Silence > 3s anti-pattern:** 短剧 用户上滑。**Mitigation:** ≤3s silence。

---

## Glossary

- **Integrated LUFS:** 整个 audio 的 average loudness。
- **Short-term LUFS:** 3-second sliding window loudness。
- **Momentary LUFS:** 400-ms sliding window loudness。
- **LRA (Loudness Range):** Loudness 动态范围。
- **K-weighting:** ITU-R BS.1770-4 人耳 loudness 模拟 filter。

---

*Generated: 2026-06-15 as part of Phase 5 REFACTOR-rest-04 (mixer RAG uplift).*
*Source provenance: ITU-R BS.1770-4 / EBU R128 / AES TC-HFA / platform specs / ffmpeg docs — fair use paraphrase + short technical phrases only.*
