# CN TTS Model Matrix — Hermes Catalog + Per-Character Voice Selection

**Source:** Hermes TTS provider catalog (`plugins/voicer/`, 2026-06);MiniMax TTS API docs (2026-06);ElevenLabs TTS docs (2026-06);Mistral Voxtral docs (2026-06);Google Gemini TTS docs (2026-06);Microsoft Edge TTS docs (2026-06);NeuTTS docs (2026-06)。
**Copyright:** Fair Use — paraphrased provider capability matrix; no proprietary TTS model internals verbatim. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

> **⚠ Phantom strip note:** This ref replaces phantom CosyVoice references (per Phase 0 audit + research SUMMARY: Hermes 不部署 CosyVoice). Hermes 实际 TTS catalog:MiniMax / ElevenLabs / Mistral Voxtral / Gemini / Edge / NeuTTS。

## Hermes TTS Provider Capability Matrix (2026-06)

### 关键 heuristic 1 (load-bearing): 6 TTS providers + 能力矩阵

| Provider | CN 普通话支持 | Emotional control | Voice cloning | Latency | Cost / 1K chars | 备注 |
|----------|---------------|-------------------|---------------|---------|-----------------|------|
| **MiniMax T2A-01** | ✅ 母语级 | ✅ 6 emotions + intensity | ✅ 5s sample | 中(~3s)| $0.10 | CN 短剧 首选 |
| **ElevenLabs Multilingual v2** | ✅ 流利但带 accent | ✅ voice tuning | ✅ 1min sample | 低(~1s)| $0.30 | 全球首选,情感细腻 |
| **Mistral Voxtral** | ✅ 流利 | 中(prosody)| ✅ | 低(~0.8s)| $0.15 | 开源 + 自部署 |
| **Google Gemini TTS** | ✅ 流利 | 中 | ❌ preset only | 低(~1s)| $0.20 | Google ecosystem |
| **Microsoft Edge TTS** | ✅ 流利 | ❌ preset only | ❌ | 极低(~0.3s)| 免费 | 适合 preview / 群演 |
| **NeuTTS** | ✅ 母语级 | ✅ | ✅ | 中(~2s)| $0.12 | CN 本土,小众模型 |

### 关键 heuristic 2: Per-character 推荐选择

| Character 类型 | 推荐 Provider | 理由 |
|---------------|---------------|------|
| 主角(featured)+ 多 emotion | MiniMax T2A-01 或 ElevenLabs | emotional control + voice cloning |
| 配角(supporting) | MiniMax T2A-01 | CN 母语级 + 性价比 |
| 群演(extra) | Edge TTS | 免费 + 速度快 |
| 旁白 / VO | ElevenLabs(全球发行)或 MiniMax(CN 发行)| 音色质感优先 |
| 反派 / 复杂 emotion | ElevenLabs Multilingual v2 | emotional prosody 细腻 |
| AI voice / 机械 / 特殊 | Gemini TTS 或 NeuTTS | 非自然 voice preset |

### 关键 heuristic 3: Voice cloning 5-second sample 协议

per [`../production/references/casting-lora-spec.md`](../production/references/casting-lora-spec.md) §character voice consistency:

**5-second voice cloning sample 要求:**
- 持续 5-10s 单人单话(避免多人对话)
- 干净 background(无 music / noise / reverb)
- Mid-range pitch + neutral emotion(便于 emotion delta modulation)
- Sample rate 48kHz 24-bit(production-grade)
- 包含 character trigger phrase(便于 prompt-based activation)

---

## Phantom Strip: CosyVoice 替换协议

### 关键 heuristic 4: CosyVoice phantom 替换

per research SUMMARY + Phase 0 GAP-REPORT: **CosyVoice 不在 Hermes catalog**。

**替换 mapping:**
- `CosyVoice-300M (preview)` → `MiniMax T2A-01 (primary)` 或 `<tts_primary>` placeholder
- `CosyVoice-300M-SFT (production)` → `MiniMax T2A-01-HD` 或 `<tts_production>` placeholder

**SKILL.md 修正:**
- 不再 hard-code CosyVoice model name
- 使用 provider-agnostic placeholder + provider matrix reference
- 保留 model-allowlist references in `_shared/known-external-models.yaml`

---

## Voice Generation 协议

### 关键 heuristic 5: TTS prompt 工程 5 大原则

1. **Explicit emotion tag:** "happy" / "sad" / "angry" / "neutral" / "fearful" / "surprised"(per Ekman 7 basic emotions)
2. **Prosody control:** rate (slow / normal / fast) + pitch (low / mid / high) + volume (quiet / normal / loud)
3. **Pause encoding:** 用逗号 / 句号 / 省略号控制 pause;"..." = 长犹豫 pause
4. **Emphasis markup:** 用大写或斜体强调关键词(e.g., "你给我 *等着*")
5. **CN 特殊处理:** 中文 TTS 注意多音字 + 儿化音 + 轻声;MiniMax 处理最好

### 关键 heuristic 6: Per-platform TTS divergence

| Platform | TTS 推荐 | 备注 |
|----------|----------|------|
| 抖音 短剧 | MiniMax T2A-01 | CN 母语级 + 情感细腻 |
| 快手 短剧 | MiniMax T2A-01 + 偶尔 Edge TTS(群演)| 草根感 |
| 小程序剧 | MiniMax T2A-01 + ElevenLabs(关键 emotion)| 戏剧化 |
| 视频号 | MiniMax T2A-01 | 标准 CN |
| TikTok | ElevenLabs Multilingual v2 | 全球受众 |
| YouTube Shorts | ElevenLabs 或 Gemini | YouTube ecosystem |

---

## Anti-Patterns

### 关键 heuristic 7: TTS 5 大 anti-pattern(规避)

1. **Phantom CosyVoice reference anti-pattern:** 引用 CosyVoice(不在 Hermes catalog)。**Mitigation:** 用 MiniMax / ElevenLabs / 等。
2. **Single-provider lock-in anti-pattern:** 全用 ElevenLabs(贵)。**Mitigation:** per-character 选择(per heuristic 2)。
3. **No voice cloning for main character anti-pattern:** 主角用 preset voice。**Mitigation:** 5s sample cloning。
4. **Wrong provider for emotion anti-pattern:** 用 Edge TTS(无 emotional control)演复杂 emotion。**Mitigation:** 复杂 emotion → MiniMax / ElevenLabs。
5. **Bad sample quality anti-pattern:** voice cloning sample 含 background noise / music。**Mitigation:** 干净 48kHz 24-bit sample。

---

## Glossary

- **TTS:** Text-to-Speech,语音合成。
- **Voice cloning:** 用短样本(5-10s)克隆 voice identity。
- **Emotional control:** TTS 输出 emotion 调整能力(happy / sad / 等)。
- **Prosody:** 韵律(rate / pitch / volume / pause)。
- **Provider matrix:** 6 个 TTS provider 能力对比表。

---

*Generated: 2026-06-15 as part of Phase 5 REFACTOR-rest-05 (voicer RAG uplift).*
*Source provenance: Hermes TTS provider catalog (2026-06) + MiniMax / ElevenLabs / Mistral Voxtral / Gemini / Edge / NeuTTS docs — fair use paraphrase + short technical phrases only.*
*⚠ Phantom strip: CosyVoice references replaced per Phase 0 GAP-REPORT + research SUMMARY.*
