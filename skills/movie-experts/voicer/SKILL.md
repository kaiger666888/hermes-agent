---
name: voicer
description: "Voicer Expert: Multi-provider TTS (MiniMax / ElevenLabs / Voxtral / Gemini / Edge / NeuTTS) for character voice generation, emotion-adaptive delivery, and dialogue timing sync."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, voice, speech, tts, dialogue, character-voice, multi-provider]
    related_skills: [screenplay, performer, editor, mixer, spatial_audio, production]
    expert_id: voicer
    metrics: [voice_naturalness, emotion_match, character_distinctiveness]
---

# Voicer Expert (配音专家)

Multi-provider TTS synthesis specialist for character voice generation, emotion-adaptive delivery, and dialogue timing synchronization. **Phase 5 v1.5 RAG uplift:** CosyVoice phantom references replaced with Hermes-catalog providers (MiniMax / ElevenLabs / Mistral Voxtral / Gemini / Edge / NeuTTS) per [`references/cn-tts-model-matrix.md`](./references/cn-tts-model-matrix.md).

## When to use this skill

The user needs to generate character dialogue audio, create voice profiles, synthesize speech with emotional delivery, or produce dialogue stems for film production mixing.

## References

本专家所有 TTS provider 选择与 voice consistency 阈值由下列 2 个 refs 独占定义(Phase 5 v1.5 light-refs uplift per REFACTOR-rest-05):

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/cn-tts-model-matrix.md`](./references/cn-tts-model-matrix.md) | 选择 TTS provider 或 替换 phantom CosyVoice 前 | Hermes 6-provider 能力矩阵(MiniMax / ElevenLabs / Voxtral / Gemini / Edge / NeuTTS)+ per-character 推荐 + 5s voice cloning sample 协议 + CosyVoice phantom 替换 mapping + TTS prompt 工程 5 大原则 + per-platform TTS divergence |
| [`references/character-voice-consistency.md`](./references/character-voice-consistency.md) | 验证 voice identity 跨 shot/episode 一致性 前 | Speaker embedding cosine similarity 3 层验证 + voice cloning 4-tier 协议 + per-character voice baseline 数据结构 + cross-episode voice arc 协议 + 与 mixer / continuity handoff |

## Knowledge Retrieval

在生成任何 dialogue stem / voice profile / character voice baseline 输出前,按以下顺序检索上下文(2 个检索主题):

- **Hermes TTS provider matrix + per-character 推荐 + CosyVoice phantom 替换 + prompt 工程** —— 详见 [`references/cn-tts-model-matrix.md`](./references/cn-tts-model-matrix.md)
- **Speaker embedding 3 层验证 + voice cloning 协议 + cross-episode voice arc** —— 详见 [`references/character-voice-consistency.md`](./references/character-voice-consistency.md)

**若当前 runtime 中有 memory / RAG 工具**,使用以下查询范围:

```
tags="expert:voicer,domain:cn-tts-model-matrix"
tags="expert:voicer,domain:character-voice-consistency"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件。

## Role & Philosophy

- Voice is character — each role needs a distinct vocal identity
- Emotion in delivery trumps emotion in words
- Natural prosody over robotic precision

## Core Capabilities

- Voice timbre analysis and character-voice matching
- Prosodic rhythm design (intonation, stress, timing)
- Emotion-adaptive parameter modulation
- Lip-sync coordination with performer's facial animation

## Output Format

- WAV audio stem per dialogue line (48kHz, 16-bit, mono)
- Metadata JSON: `duration_ms`, `emotion_label`, `character_id`, `prosody_markers[]`
- Lip-sync alignment data for performer integration

## Key Parameters

### TTS Provider API (Phase 5 v1.5 multi-provider)
- **primary provider**: MiniMax T2A-01 (CN 母语级 + emotional control) per [`references/cn-tts-model-matrix.md`](./references/cn-tts-model-matrix.md) §Hermes TTS Provider Capability Matrix
- **fallback providers**: ElevenLabs Multilingual v2 (全球发行) / Mistral Voxtral (自部署) / Gemini TTS (preset) / Edge TTS (免费群演) / NeuTTS (CN 本土)
- **speaker_embedding**: character-specific vector via voice cloning (5-30s sample per [`references/character-voice-consistency.md`](./references/character-voice-consistency.md) §Voice Cloning Protocol)
- **emotion_control**: neutral, happy, sad, angry, fearful, surprised, contempt (per Ekman 7 basic emotions)
- **emotion_strength**: 0.0-1.0 (0=subtle, 0.7=moderate, 1.0=extreme)
- **speed_factor**: 0.8-1.3 (1.0 = natural)
- **pitch_shift**: -12 to +12 semitones (character adjustment)
- **sample_rate**: 48000 Hz

> **NOTE:** 旧 SKILL.md 的 CosyVoice-300M / CosyVoice-300M-SFT references 是 phantom(per Phase 0 GAP-REPORT + research SUMMARY:Hermes 不部署 CosyVoice)。已替换为 `<tts_primary>` placeholder + provider matrix reference。详见 [`references/cn-tts-model-matrix.md`](./references/cn-tts-model-matrix.md) §Phantom Strip: CosyVoice 替换协议。

### Voice Cloning
- **Reference audio**: 5-15 seconds minimum for stable clone
- **Reference samples**: 3-5 at different emotional states
- **Clone similarity**: >= 0.90 for production

### Prosody Control
- **sdp_ratio**: 0.0-1.0 (0.5 = balanced)
- **noise_scale**: 0.1-0.5 (lower = more stable)
- **max_phoneme_duration**: 300ms
- **pause_between_sentences**: 300-600ms (adjust by emotion)
- **pause_between_clauses**: 150-300ms

### GPU Budget
- ~3GB VRAM per stream | 2-3 concurrent on RTX 3090
- Real-time factor: ~0.3x | Latency: <2 seconds

## Style Rules

### Voice Characterization
- Unique vocal fingerprint per character: pitch, timbre, rate, breath
- Age-appropriate pitch: children (300-500Hz), adult female (180-280Hz), adult male (100-160Hz)
- Speech rate: 3.5-5.0 syll/s (normal), 2.0-3.0 (emotional), 5.5-7.0 (rapid)
- Natural breath pauses every 5-8 syllables

### Emotional Delivery
- Sad: slower + lower + breathier + longer pauses
- Angry: faster + higher + harder consonants + shorter pauses
- Fear: higher pitch + tremolo + irregular rhythm + breath catches
- Joy: wider range + faster + brighter + rising contours

### Prohibited
- Monotone delivery (flat pitch across entire line)
- Over-acting (exaggerated emotion beyond scene context)
- Misaligned emotion (happy delivery during sad scene)
- Identical voice across different characters

## Workflow

1. **Voice Profile Load** — Retrieve character `speaker_embedding` from registry
2. **Emotion Mapping** — Map screenplay's `emotion_curve` to `emotion_control` + `emotion_strength`
3. **Prosody Design** — Set `speed_factor`, pauses based on scene context
4. **Preview Synthesis** — Quick preview (lower quality) for timing check
5. **Lip-sync Alignment** — Validate duration matches performer's facial timeline
6. **Production Synthesis** — Full quality render per dialogue line
7. **Post-Processing** — Noise gate (-40dB), normalization (-16 LUFS), fade (10ms), de-essing
8. **Metadata Export** — Generate alignment data and prosody markers JSON

## Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| voice_naturalness | >= 0.90 |
| emotion_match | >= 0.85 |
| character_distinctiveness | >= 0.80 |
| prosody_naturalness | >= 0.85 |

## Collaboration

- **<- screenplay**: dialogue text + emotion_curve + scene context
- **<- performer**: character psychology, action-to-voice sync points
- **<- editor**: timing marks, cut boundaries, dialogue pacing intent
- **-> mixer**: dialogue stem (WAV) + metadata for level balancing
- **-> performer**: lip-sync alignment data for facial animation
- **-> spatial_audio**: dialogue position data for spatial placement

## What NOT to do

- Don't use Edge TTS / preset voices for main characters (no emotional control; use MiniMax / ElevenLabs voice cloning per [`references/cn-tts-model-matrix.md`](./references/cn-tts-model-matrix.md) §Per-character 推荐选择)
- Don't skip post-processing (noise gate + normalization + de-essing)
- Don't exceed 3 concurrent streams on single RTX 3090
- Don't clone voices with <5 seconds reference audio
- Don't normalize outside -16 LUFS ± 1
