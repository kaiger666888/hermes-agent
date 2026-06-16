# Character Voice Consistency — Speaker Embedding + Voice Cloning Protocol

**Source:** Desplanques et al. *ECAPA-TDNN* (2020 Interspeech);Jia et al. *Transfer Learning from Speaker Verification to Multispeaker Text-to-Speech Synthesis* (Google, 2018 NeurIPS);Chen et al. *Speaker Verification* literature review (2022 IEEE TASLP);Hermes voice-cloning deployment notes (2024-2026)。
**Copyright:** Fair Use — paraphrased protocol + heuristics; no proprietary model weights verbatim. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 voicer 专家在 **跨 shot / 跨 episode voice consistency** 验证时的**权威源**。它涵盖 speaker embedding cosine similarity + voice cloning protocol + per-character voice ID 一致性 + 失败 fallback。

## Speaker Embedding Verification

### 关键 heuristic 1 (load-bearing): Voice ID 一致性 3 层验证

每个 character 的 voice 必须通过 3 层 verification(per [`../production/references/casting-lora-spec.md`](../production/references/casting-lora-spec.md) §Character ID Cross-Shot Consistency):

1. **Speaker embedding cosine similarity** ≥ 0.85(基于 ECAPA-TDNN 或 GE2EC)
2. **F0 (pitch) consistency:** 跨 shot pitch σ ≤ 30Hz(同一 character 不应有显著 pitch 漂移)
3. **Spectral envelope similarity** ≥ 0.80(MFCC + formant 一致性)

**失败处理:** 任一层失败 → 重新生成 + 调整 voice cloning sample 或 provider。

### 关键 heuristic 2: Per-character voice baseline 数据

每个 character 必须建立 voice baseline(per [`../production/references/asset-reuse-plan.md`](../production/references/asset-reuse-plan.md)):

```text
asset_library/voices/
├── protagonist_main/
│   ├── baseline_sample_5s.wav         (voice cloning sample)
│   ├── baseline_sample_extended.wav   (15-30s,for higher fidelity)
│   ├── baseline_speaker_embedding.npy  (ECAPA-TDNN 192-dim embedding)
│   ├── baseline_f0_stats.json         (mean pitch / range / contour)
│   └── provider_specific_models/
│       ├── minimax_voice_id.json
│       ├── elevenlabs_voice_id.json
│       └── ...
└── antagonist_main/
    └── ...
```

---

## Voice Cloning Protocol

### 关键 heuristic 3: 5-sample + 30-sample cloning 协议

| Cloning tier | Sample 时长 | 推荐场景 | Provider 支持 |
|--------------|------------|----------|---------------|
| **Quick clone** | 5-10s | 配角 / 群演 / 短 短剧 | MiniMax / ElevenLabs |
| **Standard clone** | 30s-1min | 主角 / 长篇 短剧 | MiniMax / ElevenLabs |
| **Premium clone** | 3-5min | 电影 / 高质量制作 | ElevenLabs Professional Voice Clone |
| **Preset voice** | 0s | 群演 / 一次性 character | Edge TTS / Gemini TTS |

### 关键 heuristic 4: Voice cloning sample 采集协议

per [`../production/references/casting-lora-spec.md`](../production/references/casting-lora-spec.md) §Reference image 采集协议,voice cloning sample 必须:

- 干净 background(无 music / noise / reverb)
- Sample rate 48kHz 24-bit
- 单人单话(避免多人对话干扰)
- Mid-range pitch + neutral emotion
- 包含 character trigger phrase
- Mid-paced delivery(180-220 wpm 中文 / 140-160 wpm 英文)

---

## Cross-Episode Voice Arc

### 关键 heuristic 5: Voice arc(情绪/状态变化)

跨 episode voice arc 必须 narrative-driven:

| Voice arc 触发 | Voice 参数变化 |
|---------------|---------------|
| 角色 aging / 时间跨度 | F0 ↓ + 速率 ↓ + breathiness ↑ |
| 角色 traumatized | F0 instability + pause 多 + whisper 倾向 |
| 角色 empowered | F0 ↑ + volume ↑ + rate ↑ |
| 角色 dying / sick | breathiness ↑ + volume ↓ + pause 多 |

### 关键 heuristic 6: Cross-episode voice consistency hard rule

同一 character 跨 episode 必须保持 voice baseline 一致(详见 §Speaker Embedding Verification)。Voice arc 是 emotion / state 调整,**不能改变 voice identity**(speaker embedding)。

---

## Handoff

### 关键 heuristic 7: 与 mixer / continuity handoff

- **→ mixer:** voicer 输出 raw TTS stem;mixer 负责 dialogue ducking / EQ / final levels
- **→ continuity:** voicer 输出 voice consistency report;continuity 跨 shot / 跨 episode 验证
- **→ production:** voice cloning sample 与 character LoRA training data 同步(per [`../production/references/casting-lora-spec.md`](../production/references/casting-lora-spec.md))

---

## Anti-Patterns

### 关键 heuristic 8: Voice consistency 5 大 anti-pattern(规避)

1. **No voice cloning for main character anti-pattern:** 主角用 preset voice。**Mitigation:** ≥30s sample cloning。
2. **Bad sample quality anti-pattern:** voice cloning sample 含 background noise / music。**Mitigation:** 干净 48kHz 24-bit sample。
3. **Voice identity drift anti-pattern:** 跨 episode voice identity 变化。**Mitigation:** speaker embedding verification ≥ 0.85。
4. **Single-provider lock-in anti-pattern:** 全用同一 provider。**Mitigation:** per-character 选择(per cn-tts-model-matrix.md heuristic 2)。
5. **No voice arc documentation anti-pattern:** voice arc 变化无 narrative motivation。**Mitigation:** per heuristic 5 协议。

---

## Glossary

- **Speaker embedding:** Voice identity 数学表示(ECAPA-TDNN 192-dim)。
- **Voice cloning:** 用短 sample 复制 voice identity。
- **F0:** 基频(pitch),决定 voice 高低。
- **Spectral envelope:** MFCC + formant,决定 voice 音色。
- **Voice arc:** 跨 episode voice 参数变化(emotion / state 反映)。

---

*Generated: 2026-06-15 as part of Phase 5 REFACTOR-rest-05 (voicer RAG uplift).*
*Source provenance: Desplanques et al. 2020 ECAPA-TDNN / Jia et al. 2018 NeurIPS GE2EC / Chen et al. 2022 IEEE TASLP / Hermes voice-cloning notes (2024-2026) — fair use paraphrase + short technical phrases only.*
