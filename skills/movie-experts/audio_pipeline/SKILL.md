---
name: audio_pipeline
description: "Audio Pipeline Expert: unified 6-sub-step audio production (voicer TTS, lip_sync audio-driven sync, composer music, foley SFX, mixer mastering, spatial_audio 3D encoding) for cinematic audio consistency. Sub-steps: [voicer, lip_sync, composer, foley, mixer, spatial_audio]."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
sub_steps: [voicer, lip_sync, composer, foley, mixer, spatial_audio]
metadata:
  hermes:
    tags: [movie, audio, voice, speech, tts, dialogue, character-voice, multi-provider, lip-sync, audio-driven, video-generation, benchmark, talking-head, digital-human, music, score, sound, beat-sync, film-scoring, musicgen, chion-audio-vision, foley, sound-effects, physical-audio, impact-sync, sound-design, mixing, mastering, ducking, lufs, frequency, audio-balance, stems, senior-mixing-secrets, spatial-audio, 3d-sound, ambience, reverb, immersive, dolby-atmos, hrtf, binaural]
    related_skills: [screenplay, performer, editor, production, visual_executor, continuity_auditor, style_genome, scene_builder, prompt_injector]
    expert_id: audio_pipeline
    aliases: [voicer, lip_sync, composer, foley, mixer, spatial_audio]
    metrics: [voice_naturalness, emotion_match, character_distinctiveness, lip_sync_error, lip_sync_confidence, temporal_consistency, identity_preservation, emotional_sync, spatial_coherence, dynamic_range, material_credibility, impact_sync_accuracy, force_consistency, spectral_clarity, level_compliance, frequency_masking_score, dialogue_intelligibility, dynamic_range_appropriateness, reality_anchor_stability, distance_transition_smoothness, vacuum_detection_pass]
---

# Audio Pipeline Expert (音频管线专家)

Unified cinematic audio consistency expert for AI 短剧 / 微电影 production. Merges the **voicer sub-step** (multi-provider TTS — MiniMax / ElevenLabs / Voxtral / Gemini / Edge / NeuTTS — for character voice generation, emotion-adaptive delivery, dialogue timing), **lip_sync sub-step** (audio-driven mouth-motion alignment via latent diffusion — now an explicit sub-step per Phase 8 §2.9 NODE-09 critic pairing), **composer sub-step** (MusicGen-Large BGM + Chion audio-vision modes + coupled beat design), **foley sub-step** (7-dimensional parametric sound effects via Stable Audio Open 1.0), **mixer sub-step** (multi-track mixing per Senior *Mixing Secrets* + LUFS mastering per ITU-R BS.1770-4), and **spatial_audio sub-step** (Dolby Atmos bed+objects + 6D spatial encoding + HRTF binaural rendering + 5 immersive sound patterns).

Per Phase 7 §4.9 + PITFALLS §2.6: **5-task compression; consistency context unified**. The 6 sub-steps share a unified audio-consistency context (dialogue/music/foley/ambience stems, frequency allocation, LUFS targets), eliminating the cross-expert handoff drift that the v1 voicer→lip_sync→composer→foley→mixer↔spatial_audio collaboration bullets had to paper over.

**Sub-steps (declared in frontmatter):** `[voicer, lip_sync, composer, foley, mixer, spatial_audio]`

## When to use this skill

The user needs to produce any audio asset for AI film production:

- **Character dialogue audio / voice profiles / TTS stems** → invoke the **voicer sub-step** (multi-provider TTS synthesis).
- **Audio-driven lip alignment for character footage / digital human / 多语言重配音** → invoke the **lip_sync sub-step** (latent-diffusion mouth-motion alignment, LRS2/LRS3 benchmark-graded).
- **Film scores / background music / coupled beats for music-edit sync** → invoke the **composer sub-step** (MusicGen-Large + Chion audio-vision modes).
- **Physical sound effects / 7D parametric foley / impact-friction-footstep SFX** → invoke the **foley sub-step** (Stable Audio Open 1.0 synthesis).
- **Multi-track mixing / dialogue ducking / EQ carve / LUFS-compliant final master** → invoke the **mixer sub-step** (Senior *Mixing Secrets* heuristics + ITU-R BS.1770-4 mastering).
- **3D sound fields / 6D spatial encoding / Dolby Atmos objects / binaural rendering for headphones / ambience beds / vacuum detection** → invoke the **spatial_audio sub-step** (Atmos bed+objects + HRTF binaural + 5 immersive sound patterns).

## Sub-steps

This expert has six declared sub-steps (pipeline order):

| Sub-step | Role | When invoked | Output |
|----------|------|--------------|--------|
| **voicer** | Multi-provider TTS (MiniMax / ElevenLabs / Voxtral / Gemini / Edge / NeuTTS) for character voice generation + emotion-adaptive delivery + dialogue timing sync | Any scene with character dialogue | WAV dialogue stem (48kHz 16-bit mono) + metadata JSON |
| **lip_sync** | Audio-driven lip-sync via latent diffusion (LatentSync v1.5/v1.6); aligns target audio to character footage while preserving identity, expression, head pose. Benchmark-graded via LRS2/LRS3 (LSE/LSE-C) — no LLM-judge required | Any scene where character footage must speak the dialogue audio produced by the voicer sub-step | Synced MP4 + LSE/LSE-C/SyncNet quality report JSON |
| **composer** | MusicGen-Large film scoring + Chion audio-vision mode analysis + coupled beat design for music-edit synchronization | Any scene needing BGM, underscore, source music, or music-edit sync | Music stem WAV (48kHz 24-bit) + coupled_beat.json + light_beat.json |
| **foley** | Stable Audio Open 1.0 + 7D parametric sound effects (Material × Action × Force × Duration × Resonance × Pitch × Texture) for physical audio grounding | Any scene with visible physical interactions (impacts, footsteps, friction, breaks) | foley_stems[] (WAV 48kHz 24-bit mono) + foley_metadata.json + sync_map.json |
| **mixer** | Senior *Mixing Secrets* multi-track mixing + dialogue ducking + EQ carve + LUFS-compliant final mastering per ITU-R BS.1770-4 | When all upstream stems (dialogue + music + foley + ambience) must be balanced into a final master | mix_stereo.wav (or mix_5.1.wav) + mix_report.json + stem_balance.json |
| **spatial_audio** | Dolby Atmos bed+objects + 6D spatial encoding (azimuth × elevation × distance × spread × roll-off × reverb) + HRTF binaural rendering + 5 immersive sound patterns + vacuum detection | Any scene needing 3D sound placement, environmental ambience beds, surround/binaural delivery | spatial_mix.json + ambience_stems[] + reverb_profile.json + vacuum_report.json |

**Handoff contract (pipeline order):** voicer generates `dialogue.wav` → lip_sync consumes (footage.mp4 + dialogue.wav) → produces synced footage; composer generates music stem + coupled_beat.json; foley generates foley_stems[] + sync_map.json; mixer consumes all stems (dialogue + music + foley + ambience from spatial_audio) → produces final master; spatial_audio runs in parallel with mixer to attach 6D spatial coordinates + ambience beds + reverb profiles. All intra-audio handoffs are now intra-expert (same expert_id `audio_pipeline`), not inter-expert edges.

## Spatial Audio Disposition

> **MANDATORY per ROADMAP §15 criterion #2.** This section documents the **disposition D-1: fold** decision for the v1 `spatial_audio` expert.

**Decision (D-1, 2026-06-17):** The v1 standalone `spatial_audio` expert is **folded into** `audio_pipeline` **as the 6th sub-step** (sub_steps array position 6). It is NOT deprecated.

**Rationale:** Spatial audio rendering is fundamentally a mixer/mastering concern. Dolby Atmos bed+objects, 6D spatial encoding, HRTF binaural rendering, and the 5 immersive sound patterns all operate on the same stems the mixer sub-step operates on — they just add spatial encoding (azimuth/elevation/distance/spread/reverb) on top of the level/frequency work mixer does. Keeping spatial_audio as a distinct sub-step inside audio_pipeline:

1. **Unifies the consistency context** — LUFS targets, frequency allocation (the 2000-5000Hz dialogue band sacred zone), dialogue ducking, and 5.1/7.1 channel allocation are now decided in one expert rather than negotiated between two.
2. **Preserves the unique technical surface** — HRTF 4-factor tables (ITD/ILD/spectral shaping/reverberation), Atmos object metadata (7 fields), 6D encoding protocol, and the 5 immersive sound pattern catalog all migrate verbatim into the `audio_pipeline/references/spatial_audio/` sub-folder and the `## Sub-step: Spatial Audio` body section.
3. **Eliminates the spatial_audio↔mixer ping-pong** — the v1 Collaboration graph had spatial_audio→mixer ("spatial-processed stems with panning and reverb") and mixer→spatial_audio ("post-mix stereo/5.1 output") as a circular pair. Both are now intra-expert sub-step handoffs.

**Rejected alternative — deprecation:** Deprecating spatial_audio outright would lose the HRTF/Atmos technical content (irreplaceable domain knowledge distilled from immersive-sound-design literature). Rejected.

**Stub status distinction:** The old `skills/movie-experts/spatial_audio/SKILL.md` becomes a redirect stub declaring `status: folded_into` + `folded_into: audio_pipeline` (per Task 2 of plan 15-01). This is **distinct from `merged_into`** used by the other 5 predecessor stubs (voicer, lip_sync, composer, foley, mixer). The `folded_into` status records that spatial_audio was not a peer-equivalent merge but a fold-into-a-related-sub-step disposition — the difference is semantically meaningful for Phase 18 (validate + docs) audit traceability.

**ROADMAP §15 criterion #2 satisfaction:** This section + the `folded_into` stub status together satisfy the criterion that the spatial_audio disposition be explicitly documented with rationale.

## References

本专家所有 TTS provider / lip-sync 部署 / MusicGen workflow / Stable Audio / mixing / Atmos / HRTF 阈值由下列 17 个 refs 独占定义(Phase 5 v1.5 light-refs uplift per REFACTOR-rest-{01,03,04,06} + REFACTOR-rest-05):

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/voicer/cn-tts-model-matrix.md`](./references/voicer/cn-tts-model-matrix.md) | 选择 TTS provider 或 替换 phantom CosyVoice 前 | Hermes 6-provider 能力矩阵(MiniMax / ElevenLabs / Voxtral / Gemini / Edge / NeuTTS)+ per-character 推荐 + 5s voice cloning sample 协议 + CosyVoice phantom 替换 mapping + TTS prompt 工程 5 大原则 + per-platform TTS divergence |
| [`references/voicer/tts-emotion-prosody-control.md`](./references/voicer/tts-emotion-prosody-control.md) | 设计 emotion-adaptive delivery 或 prosody 前 | Ekman 7 emotion × pitch/speed/pause mapping + prosody 控制 + breath 协议 + per-emotion acoustic signature |
| [`references/voicer/character-voice-consistency.md`](./references/voicer/character-voice-consistency.md) | 验证 voice identity 跨 shot/episode 一致性 前 | Speaker embedding cosine similarity 3 层验证 + voice cloning 4-tier 协议 + per-character voice baseline 数据结构 + cross-episode voice arc 协议 + 与 mixer / continuity_auditor handoff |
| [`references/lip_sync/sync-quality-metrics.md`](./references/lip_sync/sync-quality-metrics.md) | 评估输出视频质量或构造 benchmark 前 | LSE (Lip Sync Error) 公式 + LSE-C (Lip Sync Confidence) + SyncNet confidence score + LRS2/LRS3 国际标准 benchmark 协议 + 行业 SOTA 阈值(LSE ≤ 6.5 / LSE-C ≥ 7.0) |
| [`references/lip_sync/latentsync-deployment.md`](./references/lip_sync/latentsync-deployment.md) | 部署 LatentSync 推理服务前 | v1.5 (8GB / 256×256) vs v1.6 (18GB / 512×512) 显存要求 + 推理参数(inference_steps 20-50 / guidance_scale 1.0-3.0)+ DeepCache 加速 + Linux/Windows/ComfyUI/Replicate 5 部署路径 + 中文优化建议 |
| [`references/lip_sync/audio-video-input-spec.md`](./references/lip_sync/audio-video-input-spec.md) | 准备输入素材前 | 视频输入要求(MP4 / 25fps / 正面人脸 / 无遮挡)+ 音频输入要求(WAV / 16000Hz / 长度匹配)+ 失败模式(侧脸 / 多人 / 遮挡 / 光线不足)+ 4-tier 输入质量评级 |
| [`references/lip_sync/identity-preservation.md`](./references/lip_sync/identity-preservation.md) | 验证输出视频角色一致性 前 | Identity preservation 3 层验证(面部结构 / 表情 / 头部姿态)+ 跨帧抖动检测 + 与 continuity_auditor expert 的 handoff 协议 |
| [`references/composer/musicgen-workflow.md`](./references/composer/musicgen-workflow.md) | 生成任何 music / score 前 | MusicGen-Large 4 mode(text-to-music / melody conditioning / continuation / stereo)+ generation 参数 + melody conditioning 协议 + emotion_curve × tempo sync + editor cut-point sync |
| [`references/composer/chion-audio-vision.md`](./references/composer/chion-audio-vision.md) | 设计 scene-level audio-vision 关系 前 | Chion 5 audio-vision modes(empirical / adding value / rendered / psycho-analytic / acousmatic)+ acousmatic 详解 + per-scene audio-vision analysis 协议 + silence as design choice |
| [`references/composer/bgm-and-song-creation.md`](./references/composer/bgm-and-song-creation.md) | 生成 BGM 或 theme song 前 | BGM 结构(主歌/副歌/bridge)+ theme song 旋律设计 + 乐器编排 + 与 screenplay.scene_emotion 同步 |
| [`references/foley/stable-audio-open.md`](./references/foley/stable-audio-open.md) | 生成任何 SFX 前(替换 phantom AudioLDM-2)| Stable Audio Open 1.0 generation 参数 + 与 AudioLDM-2 对比(phantom 替换)+ 7D parametric sound design(Material / Action / Force / Environment / Distance / Layering / Emotional intent)+ 7D → Stable Audio prompt 编译公式 |
| [`references/foley/sound-effect-taxonomy.md`](./references/foley/sound-effect-taxonomy.md) | 选择 SFX 类别或设计 scene-level SFX 协议前 | BBC 21-category SFX taxonomy + 短剧 高频使用统计 + per-platform SFX divergence + 3 类必备 SFX per scene 协议 + 卡点 SFX 设计 + 3-5 层 Layering 协议 + SFX library 累积策略 |
| [`references/foley/sound-effects-prompt-engineering.md`](./references/foley/sound-effects-prompt-engineering.md) | 编译 Stable Audio prompt 前 | SFX prompt 5 大原则 + material-action-force 三元组描述公式 + negative prompt + seed 控制 + batch variation |
| [`references/mixer/mixing-secrets-small-studio.md`](./references/mixer/mixing-secrets-small-studio.md) | 设计 mix 或 dialogue ducking 前 | Per-platform LUFS targets(抖音/快手/小程序剧/视频号/TikTok/YouTube/Spotify/Apple/cinema)+ dialogue ducking 4 参数 + 5 大频段职责分配 + EQ carve protocol + mastering chain 4 步 |
| [`references/mixer/lufs-standards.md`](./references/mixer/lufs-standards.md) | 验证 LUFS compliance 或 ffmpeg loudnorm 前 | ITU-R BS.1770-4 measurement spec(Integrated/Short-term/Momentary)+ K-weighting filter + ffmpeg two-pass loudnorm 命令 + per-platform compliance check protocol + 自动化 ebur128 verification |
| [`references/spatial_audio/dolby-atmos-workflow.md`](./references/spatial_audio/dolby-atmos-workflow.md) | 设计 Atmos mix 或 6D object 前 | Dolby Atmos Bed + Objects 2 层架构 + Object metadata 7 fields + 6D encoding protocol(Position X/Y/Z + Size + Orientation + Motion)+ motion trajectory 协议 + 短剧 简化 Atmos + per-platform spatial audio 支持 |
| [`references/spatial_audio/immersive-sound-design.md`](./references/spatial_audio/immersive-sound-design.md) | 设计 immersive sound field 或 binaural mix 前 | HRTF 4 因子(ITD / ILD / spectral shaping / reverberation)+ HRTF 个性化 vs 通用 + binaural rendering pipeline + binaural vs stereo for 短剧 + 5 种 spatial sound pattern + per-genre 推荐 |

## Knowledge Retrieval

在生成任何 dialogue stem / voice profile / character voice baseline / synced video / music / score / audio-vision analysis / foley_stems / SFX / sync_map / mix / master / LUFS compliance check / spatial mix / 6D object / binaural rendering 输出前,按以下顺序检索上下文(13 个检索主题):

- **Hermes TTS provider matrix + per-character 推荐 + CosyVoice phantom 替换 + prompt 工程** —— 详见 [`references/voicer/cn-tts-model-matrix.md`](./references/voicer/cn-tts-model-matrix.md)
- **Ekman 7 emotion × pitch/speed/pause + prosody + breath 协议** —— 详见 [`references/voicer/tts-emotion-prosody-control.md`](./references/voicer/tts-emotion-prosody-control.md)
- **Speaker embedding 3 层验证 + voice cloning 协议 + cross-episode voice arc** —— 详见 [`references/voicer/character-voice-consistency.md`](./references/voicer/character-voice-consistency.md)
- **LSE / LSE-C 计算公式 + LRS2/LRS3 benchmark 协议 + SOTA 阈值** —— 详见 [`references/lip_sync/sync-quality-metrics.md`](./references/lip_sync/sync-quality-metrics.md)
- **LatentSync 部署路径 + 显存要求 + 推理参数** —— 详见 [`references/lip_sync/latentsync-deployment.md`](./references/lip_sync/latentsync-deployment.md)
- **输入素材规格 + 失败模式 + 质量评级** —— 详见 [`references/lip_sync/audio-video-input-spec.md`](./references/lip_sync/audio-video-input-spec.md)
- **Identity preservation 验证 + 抖动检测 + continuity_auditor handoff** —— 详见 [`references/lip_sync/identity-preservation.md`](./references/lip_sync/identity-preservation.md)
- **MusicGen-Large 4 mode + melody conditioning + tempo × emotion sync + editor cut-point sync** —— 详见 [`references/composer/musicgen-workflow.md`](./references/composer/musicgen-workflow.md)
- **Chion 5 audio-vision modes + acousmatic + silence as design + emotion × mode mapping** —— 详见 [`references/composer/chion-audio-vision.md`](./references/composer/chion-audio-vision.md)
- **Stable Audio Open 1.0 workflow + 7D parametric design + prompt 编译** —— 详见 [`references/foley/stable-audio-open.md`](./references/foley/stable-audio-open.md)
- **BBC 21-category SFX taxonomy + 短剧 SFX 高频用法 + per-platform divergence + Layering 协议** —— 详见 [`references/foley/sound-effect-taxonomy.md`](./references/foley/sound-effect-taxonomy.md)
- **Per-platform LUFS + dialogue ducking + EQ carve + mastering chain** —— 详见 [`references/mixer/mixing-secrets-small-studio.md`](./references/mixer/mixing-secrets-small-studio.md)
- **ITU-R BS.1770-4 spec + ffmpeg loudnorm + ebur128 verification** —— 详见 [`references/mixer/lufs-standards.md`](./references/mixer/lufs-standards.md)
- **Dolby Atmos Bed + Objects + 6D encoding + 短剧 简化 + per-platform 支持** —— 详见 [`references/spatial_audio/dolby-atmos-workflow.md`](./references/spatial_audio/dolby-atmos-workflow.md)
- **HRTF + binaural + 5 spatial sound pattern + per-genre 推荐** —— 详见 [`references/spatial_audio/immersive-sound-design.md`](./references/spatial_audio/immersive-sound-design.md)

**若当前 runtime 中有 memory / RAG 工具**,使用以下查询范围:

```
tags="expert:audio_pipeline,sub:voicer,domain:cn-tts-model-matrix"
tags="expert:audio_pipeline,sub:voicer,domain:tts-emotion-prosody-control"
tags="expert:audio_pipeline,sub:voicer,domain:character-voice-consistency"
tags="expert:audio_pipeline,sub:lip_sync,domain:sync-quality-metrics"
tags="expert:audio_pipeline,sub:lip_sync,domain:latentsync-deployment"
tags="expert:audio_pipeline,sub:lip_sync,domain:audio-video-input-spec"
tags="expert:audio_pipeline,sub:lip_sync,domain:identity-preservation"
tags="expert:audio_pipeline,sub:composer,domain:musicgen-workflow"
tags="expert:audio_pipeline,sub:composer,domain:chion-audio-vision"
tags="expert:audio_pipeline,sub:foley,domain:stable-audio-open"
tags="expert:audio_pipeline,sub:foley,domain:sound-effect-taxonomy"
tags="expert:audio_pipeline,sub:mixer,domain:mixing-secrets-small-studio"
tags="expert:audio_pipeline,sub:mixer,domain:lufs-standards"
tags="expert:audio_pipeline,sub:spatial_audio,domain:dolby-atmos-workflow"
tags="expert:audio_pipeline,sub:spatial_audio,domain:immersive-sound-design"
```

**若无此类工具**,回退到本目录 `references/{voicer,lip_sync,composer,foley,mixer,spatial_audio}/*.md` 静态文件。

## Sub-step: Voicer (TTS)

Multi-provider TTS synthesis specialist for character voice generation, emotion-adaptive delivery, and dialogue timing synchronization. **Phase 5 v1.5 RAG uplift:** CosyVoice phantom references replaced with Hermes-catalog providers (MiniMax / ElevenLabs / Mistral Voxtral / Gemini / Edge / NeuTTS) per [`references/voicer/cn-tts-model-matrix.md`](./references/voicer/cn-tts-model-matrix.md).

### Role & Philosophy

- Voice is character — each role needs a distinct vocal identity
- Emotion in delivery trumps emotion in words
- Natural prosody over robotic precision

### Core Capabilities

- Voice timbre analysis and character-voice matching
- Prosodic rhythm design (intonation, stress, timing)
- Emotion-adaptive parameter modulation
- Lip-sync coordination with performer's facial animation

### Output Format

- WAV audio stem per dialogue line (48kHz, 16-bit, mono)
- Metadata JSON: `duration_ms`, `emotion_label`, `character_id`, `prosody_markers[]`
- Lip-sync alignment data for performer integration

### Key Parameters

#### TTS Provider API (Phase 5 v1.5 multi-provider)
- **primary provider**: MiniMax T2A-01 (CN 母语级 + emotional control) per [`references/voicer/cn-tts-model-matrix.md`](./references/voicer/cn-tts-model-matrix.md) §Hermes TTS Provider Capability Matrix
- **fallback providers**: ElevenLabs Multilingual v2 (全球发行) / Mistral Voxtral (自部署) / Gemini TTS (preset) / Edge TTS (免费群演) / NeuTTS (CN 本土)
- **speaker_embedding**: character-specific vector via voice cloning (5-30s sample per [`references/voicer/character-voice-consistency.md`](./references/voicer/character-voice-consistency.md) §Voice Cloning Protocol)
- **emotion_control**: neutral, happy, sad, angry, fearful, surprised, contempt (per Ekman 7 basic emotions)
- **emotion_strength**: 0.0-1.0 (0=subtle, 0.7=moderate, 1.0=extreme)
- **speed_factor**: 0.8-1.3 (1.0 = natural)
- **pitch_shift**: -12 to +12 semitones (character adjustment)
- **sample_rate**: 48000 Hz

> **NOTE:** 旧 SKILL.md 的 CosyVoice-300M / CosyVoice-300M-SFT references 是 phantom(per Phase 0 GAP-REPORT + research SUMMARY:Hermes 不部署 CosyVoice)。已替换为 `<tts_primary>` placeholder + provider matrix reference。详见 [`references/voicer/cn-tts-model-matrix.md`](./references/voicer/cn-tts-model-matrix.md) §Phantom Strip: CosyVoice 替换协议。

#### Voice Cloning
- **Reference audio**: 5-15 seconds minimum for stable clone
- **Reference samples**: 3-5 at different emotional states
- **Clone similarity**: >= 0.90 for production

#### Prosody Control
- **sdp_ratio**: 0.0-1.0 (0.5 = balanced)
- **noise_scale**: 0.1-0.5 (lower = more stable)
- **max_phoneme_duration**: 300ms
- **pause_between_sentences**: 300-600ms (adjust by emotion)
- **pause_between_clauses**: 150-300ms

#### GPU Budget
- ~3GB VRAM per stream | 2-3 concurrent on RTX 3090
- Real-time factor: ~0.3x | Latency: <2 seconds

### Style Rules

#### Voice Characterization
- Unique vocal fingerprint per character: pitch, timbre, rate, breath
- Age-appropriate pitch: children (300-500Hz), adult female (180-280Hz), adult male (100-160Hz)
- Speech rate: 3.5-5.0 syll/s (normal), 2.0-3.0 (emotional), 5.5-7.0 (rapid)
- Natural breath pauses every 5-8 syllables

#### Emotional Delivery
- Sad: slower + lower + breathier + longer pauses
- Angry: faster + higher + harder consonants + shorter pauses
- Fear: higher pitch + tremolo + irregular rhythm + breath catches
- Joy: wider range + faster + brighter + rising contours

#### Prohibited
- Monotone delivery (flat pitch across entire line)
- Over-acting (exaggerated emotion beyond scene context)
- Misaligned emotion (happy delivery during sad scene)
- Identical voice across different characters

### Workflow

1. **Voice Profile Load** — Retrieve character `speaker_embedding` from registry
2. **Emotion Mapping** — Map screenplay's `emotion_curve` to `emotion_control` + `emotion_strength`
3. **Prosody Design** — Set `speed_factor`, pauses based on scene context
4. **Preview Synthesis** — Quick preview (lower quality) for timing check
5. **Lip-sync Alignment** — Validate duration matches performer's facial timeline
6. **Production Synthesis** — Full quality render per dialogue line
7. **Post-Processing** — Noise gate (-40dB), normalization (-16 LUFS), fade (10ms), de-essing
8. **Metadata Export** — Generate alignment data and prosody markers JSON

### Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| voice_naturalness | >= 0.90 |
| emotion_match | >= 0.85 |
| character_distinctiveness | >= 0.80 |
| prosody_naturalness | >= 0.85 |

### What NOT to do

- Don't use Edge TTS / preset voices for main characters (no emotional control; use MiniMax / ElevenLabs voice cloning per [`references/voicer/cn-tts-model-matrix.md`](./references/voicer/cn-tts-model-matrix.md) §Per-character 推荐选择)
- Don't skip post-processing (noise gate + normalization + de-essing)
- Don't exceed 3 concurrent streams on single RTX 3090
- Don't clone voices with <5 seconds reference audio
- Don't normalize outside -16 LUFS ± 1

## Sub-step: Lip Sync (Audio-Driven Video Sync)

> **Now an explicit sub-step** (was implicit in v1, expressed only as a voicer→lip_sync collaboration edge). Per **Phase 8 §2.9 NODE-09 critic pairing**, the v2.0 PRFP DAG promotes lip_sync to an explicit sub-step of `audio_pipeline` because it carries unique objective validation (LRS2/LRS3 benchmark + LSE/LSE-C via SyncNet — no LLM-judge) and must pair with a theory_critic on output identity preservation. **ROADMAP §15 criterion #5 satisfaction:** this explicit declaration is the criterion.

Audio-driven lip-sync specialist for AI 短剧 / 微电影 character footage. Takes (person-speaking video + target audio) and produces a new video where the mouth motion matches the target audio, while preserving identity, expression, and head pose. **Decoupled from the voicer sub-step**: voicer synthesizes the audio; lip_sync aligns the audio to existing or generated visual footage. The two compose in series: voicer → lip_sync (both now intra-expert sub-steps of `audio_pipeline`).

### Role & Philosophy

- **唯一国际标准 benchmark 专家** — LRS2 / LRS3 是全球公认的 lip-sync 评估数据集,LSE / LSE-C 是业界标准指标。本 sub-step 的产出质量**不依赖 LLM-as-judge**,可直接用 SyncNet 客观验证。
- **音频驱动而非视频重生成** — 只修改嘴部区域,保留面部其他部分、表情、头部姿态、身份。这是与 [`visual_executor`](../visual_executor/SKILL.md) 的核心区别:visual_executor 从零生成视频,lip_sync 在已有视频上做局部修改。
- **口型精度优先于画质** — 数字人/口播场景下,口型与音频的对齐误差 > 120ms 会被观众感知为不同步,即使其他画质指标优秀。
- **与 [`continuity_auditor`](../continuity_auditor/SKILL.md) 协作** — 输出的视频必须通过 continuity_auditor expert 的"identity preservation"审计,确保角色身份在 shot 内不漂移。

### Core Capabilities

- **Audio-driven lip motion generation** — Whisper 音频嵌入 → U-Net 交叉注意力 → TREPA 时间对齐 → SyncNet 三重损失优化
- **Identity preservation** — 只修改嘴部 ROI,保留面部其他结构;每帧的 identity embedding cosine similarity ≥ 0.92 (per [`references/lip_sync/identity-preservation.md`](./references/lip_sync/identity-preservation.md) §3-layer verification)
- **Multi-resolution support** — 256×256 (v1.5, 8GB VRAM) 与 512×512 (v1.6, 18GB VRAM) 双档,根据 GPU 自适应
- **Batch processing** — 输入 (video, audio) pair list,顺序处理 + checkpoint resume
- **Quality self-check** — 推理完成后自动计算 SyncNet confidence;若 < 阈值,触发 retry 或 downgrade
- **Multi-provider execution** — LatentSync 本地推理 (primary) / Replicate API (cloud fallback) / ComfyUI node (workflow integration)

### Output Format

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

#### Quality grade scale

| Grade | LSE | LSE-C | SyncNet conf | Action |
|---|---|---|---|---|
| **A** (Excellent) | ≤ 6.0 | ≥ 7.5 | ≥ 0.85 | Ship as-is |
| **B** (Acceptable) | 6.0-7.0 | 6.5-7.5 | 0.75-0.85 | Ship; flag for review |
| **C** (Marginal) | 7.0-8.5 | 5.5-6.5 | 0.65-0.75 | Retry with higher inference_steps |
| **D** (Failed) | > 8.5 | < 5.5 | < 0.65 | Re-examine input quality or switch model |

### Key Parameters

#### Engine selection (provider-agnostic)

- **primary engine**: `<lip_sync_primary>` (per [`../_shared/known-external-models.yaml`](../_shared/known-external-models.yaml) — currently a latent-diffusion method, model name in references only)
- **fallback engine**: `<lip_sync_fallback>` (GAN-based, faster but lower quality; used when VRAM < 8GB or processing-time budget < 30s)

#### Resolution vs VRAM trade-off

| Resolution | Min VRAM | Recommended VRAM | Use case |
|---|---|---|---|
| 256×256 (v1.5) | 8 GB | 10 GB | Fast preview, low-end GPU |
| 512×512 (v1.6) | 18 GB | 24 GB | Final delivery, hides blur |

#### Inference parameters

- **`inference_steps`**: 20 (fast) - 50 (high-quality); default 25
- **`guidance_scale`**: 1.0-3.0; default 1.5; higher = sharper lip but more jitter
- **`deepcache`**: enabled (default) — 30-40% speed-up with negligible quality loss
- **`mask_dilation`**: 0-10 pixels; default 4 — controls how far beyond mouth ROI the diffusion can edit

#### Input specifications

- **Video**: MP4, recommended 25fps, H.264; face must be frontal, well-lit, single-person
- **Audio**: WAV, 16000Hz sample rate, mono; duration ≤ video duration
- **Aspect**: any; face ROI auto-detected; output preserves input aspect

### Workflow

1. **Pre-check input** — validate video + audio per [`references/lip_sync/audio-video-input-spec.md`](./references/lip_sync/audio-video-input-spec.md) §4-tier input quality rating. If input is D-tier (multi-person / occlusion / extreme angle), reject with guidance.
2. **Select resolution** — based on available VRAM (auto-detect or user-specified), pick v1.5 or v1.6.
3. **Configure parameters** — based on quality target (preview / final) + time budget.
4. **Execute inference** — call primary engine; on OOM or timeout, downgrade to fallback engine.
5. **Quality self-check** — compute LSE, LSE-C, SyncNet confidence, identity cosine sim. If grade < B, retry with adjusted parameters or downgrade resolution.
6. **Continuity handoff** — emit `continuity_handoff` block for downstream continuity_auditor audit if `identity_cosine_sim < 0.95` or scene involves cross-shot character continuity.

### Quality Thresholds

| Threshold | Value | Source |
|---|---|---|
| LSE SOTA (industry) | ≤ 6.5 | [`references/lip_sync/sync-quality-metrics.md`](./references/lip_sync/sync-quality-metrics.md) |
| LSE-C SOTA (industry) | ≥ 7.0 | [`references/lip_sync/sync-quality-metrics.md`](./references/lip_sync/sync-quality-metrics.md) |
| SyncNet confidence (A grade) | ≥ 0.85 | [`references/lip_sync/sync-quality-metrics.md`](./references/lip_sync/sync-quality-metrics.md) |
| Identity cosine sim (must-pass) | ≥ 0.92 | [`references/lip_sync/identity-preservation.md`](./references/lip_sync/identity-preservation.md) |
| Temporal jitter p95 | ≤ 60ms | [`references/lip_sync/identity-preservation.md`](./references/lip_sync/identity-preservation.md) |
| Audio-video drift (per [`../_shared/cognitive-resonance-metrics.md`](../_shared/cognitive-resonance-metrics.md) §Scale 1) | < 120ms | shared neural-layer threshold |

### What NOT to do

- ❌ **不要重新生成整段视频** — 这是 [`visual_executor`](../visual_executor/SKILL.md) 的职责。lip_sync 只修改嘴部 ROI。
- ❌ **不要接受 D-tier 输入** — 侧脸 / 多人 / 遮挡 / 光线不足的视频会输出垃圾。必须 reject 并引导用户重拍或切换到 visual_executor。
- ❌ **不要忽略 SyncNet 客观指标** — LLM-judge 不可靠,必须用 SyncNet 数学指标判定 grade。任何"看起来还行"的主观判断都不合格。
- ❌ **不要在没有 LSE benchmark 的情况下声称"SOTA"** — 必须在 LRS2/LRS3 测试集上跑出 LSE ≤ 6.5 才能声称 SOTA;否则只能说"达到 X 等级"。
- ❌ **不要忽略 identity 漂移** — 输出视频与输入视频的 identity cosine similarity < 0.92 时,即使 LSE 优秀也必须 VETO 并触发 continuity_auditor handoff。
- ❌ **不要把 LatentSync 写死在 SKILL.md body** — 模型名只在 references/*.md 中,SKILL.md 使用 `<lip_sync_primary>` 占位符。provider-agnostic 是硬约束。

### Validation protocol (how to know if this expert improved)

本 sub-step 的核心 KPI 是**LSE / LSE-C 在 LRS2/LRS3 上的实测分数**——全球公认的客观指标,不需要 LLM-judge,不需要 A/B 测试:

1. **Download LRS2 / LRS3 test set**:公开数据集,从 https://github.com/JoonSon/LipSync 或官方来源下载。
2. **Run lip_sync on each test sample**:输入 (video, audio) pair,输出 synced video。
3. **Compute LSE / LSE-C / SyncNet confidence**:用 SyncNet model(预训练)计算每个输出视频的 LSE / LSE-C。
4. **Compare against SOTA baselines**: LatentSync v1.6 paper claims LSE = 5.13 / LSE-C = 8.25 on LRS2. 本 sub-step 的目标 = match or exceed。
5. **Iteration signal**: 当 references/*.md 更新或参数调整后,LSE 必须不下降。下降 = 配置回归。

校准脚本和 LRS2/LRS3 evaluation harness 位于 [`_eval/lip_sync_benchmark/`](../../lip_sync/_eval/lip_sync_benchmark/)(若不存在,operator 需创建并下载 LRS2/LRS3;legacy path preserved under old lip_sync/ dir for archival).

## Sub-step: Composer (Music + Score)

Film scoring and sound design specialist using MusicGen-Large for background music generation, Chion audio-vision mode analysis for sound-image relationship, and coupled beat design for music-edit synchronization in AI film production. **Phase 5 v1.5 RAG uplift** per REFACTOR-rest-06.

### Role & Philosophy

- Music amplifies emotion without dictating it
- Silence is a powerful instrument — use it deliberately
- Rhythmic sync between music and editing creates invisible continuity

### Core Capabilities

- Film scoring grammar (leitmotif, underscore, stinger, source music)
- Coupled beat design for music-edit synchronization
- Genre-specific arrangement and orchestration
- Emotional mapping: scene mood to musical parameters

### Output Format

- Music stem: WAV 48kHz 24-bit stereo (or 5.1/7.1)
- `coupled_beat.json`: beat timestamps + energy curve + emotional annotations
- `light_beat.json`: downbeat-level markers for editor sync

### Key Parameters

#### Music Generation
- **model**: MusicGen-large (primary, 32kHz stereo)
- **guidance_scale**: 3.0-7.0 (higher = closer to prompt)
- **temperature**: 0.8-1.2
- **generation_length**: 30s per segment (loop/extend for longer)
- **sample_rate**: 48000 Hz (production), 32000 Hz (preview)

#### Audio Specs
- **bit_depth**: 24-bit (production), 16-bit (preview)
- **channels**: stereo (default), 5.1/7.1 (coordinate with spatial_audio sub-step)
- **LUFS_target**: -20 to -14 (film underscore)

#### Coupled Beat Design
- **light_beat.json**: primary downbeats every 1-4 bars, timestamped
- **coupled_beat.json**: full beat grid + energy_per_beat (0.0-1.0) + emotion_tag
- **beat_resolution**: 16th note granularity
- **coupling_strength**: 0.3 (loose) to 0.8 (tight)

#### Dynamic Range
- **target_DR**: 8-14 LU (EBU R128)
- **compression_ratio**: 2:1-4:1 (gentle)
- **limiter_ceiling**: -1.0 dBTP
- **frequency_avoidance**: 2000-5000 Hz zone (dialogue territory)

#### GPU Budget
- MusicGen-large: ~6GB VRAM for 30s | ~15-30s generation time | 1 at a time

### Style Rules

#### Scoring Standards
- Underscore for emotional support, source for diegetic world-building
- Leitmotif: 2-4 bar recurring phrase per key character/theme
- Dynamic shaping: music swells/fades with scene emotion
- Sparse for intimate, full for dramatic climaxes

#### BPM Guide
- 60-80 (contemplative), 80-120 (neutral/narrative), 120-160 (tension/action)
- Max ±20 BPM per scene, gradual (2+ seconds)

#### Genre Guidelines
- Drama: strings + piano, minimal percussion
- Thriller: low strings + percussion + dissonance
- Romance: woodwinds + strings, legato
- Sci-fi: synthesizers + processed instruments
- Comedy: pizzicato + woodwinds, staccato

#### Prohibited
- Constant wall-to-wall music
- Music fighting dialogue in 2000-5000Hz
- Melodic hooks that distract from narrative
- Genre mismatch | Over-compressed dynamics

### Workflow

1. **Mood Analysis** — Map `emotion_curve` to musical parameters (BPM, key, instrumentation)
2. **Genre Selection** — Determine scoring approach from `style_genome` + `sound_mood`
3. **Prompt Construction** — Build text-to-music prompt with genre/mood/tempo
4. **Music Generation** — Generate 30s segments via MusicGen, extend/loop as needed
5. **Beat Extraction** — Analyze output for beat grid, create `coupled_beat.json`
6. **Dynamic Shaping** — Volume automation to match scene emotion curve
7. **Frequency Check** — Verify no clash with dialogue zone (2000-5000Hz)
8. **Export Stems** — Output music WAV + coupled_beat.json + light_beat.json

### Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| emotional_sync | >= 0.85 |
| spatial_coherence | >= 0.80 |
| dynamic_range | 8-14 LU |
| genre_fidelity | >= 0.80 |

### What NOT to do

- Don't generate wall-to-wall music (scenes need breathing room)
- Don't occupy the 2000-5000Hz zone (dialogue territory)
- Don't compress beyond 4:1 (kills film scoring dynamics)
- Don't run MusicGen alongside visual_executor on single GPU
- Don't ignore editor's cut points (coupled beats must align)

## Sub-step: Foley (SFX)

Sound effects design specialist managing the 7-dimensional parametric Foley & SFX matrix (Material x Action x Force x Duration x Resonance x Pitch x Texture) for realistic physical sound that grounds AI-generated visuals in acoustic reality.

### Role & Philosophy

- Sound makes the image real — what you hear convinces you what you see
- Every physical interaction in frame deserves its acoustic fingerprint
- Foley is not about loudness, it's about texture and timing

### Core Capabilities

- 7D parametric sound effect matrix design
- Physical acoustic modeling (impact, friction, fluid, metal, wood, etc.)
- Frame-accurate sound-to-action synchronization
- Material credibility assessment (does it sound like what it looks like)

### Output Format

- `foley_stems[]`: WAV 48kHz 24-bit mono (one stem per independent effect)
- `foley_metadata.json`: trigger timestamps, material tags, force values, spatial positions
- `sync_map.json`: precise audio-to-video-frame alignment mapping

### Key Parameters

#### Sound Generation
- **synthesis_model**: Stable Audio Open 1.0 (primary, 2026-06 Hermes default), AudioGen (fallback) — per [`references/foley/stable-audio-open.md`](./references/foley/stable-audio-open.md) §Stable Audio Open 1.0 能力矩阵(phantom AudioLDM-2 已替换)
- **guidance_scale**: 4.0-7.0 (higher = more precise)
- **duration_max**: 47s per generation (typical SFX ≤5s; per Stable Audio Open 1.0 spec)
- **sample_rate**: 48000 Hz (production), 32000 Hz (preview)
- **bit_depth**: 24-bit

#### Force-to-Loudness Mapping
| Force | Level | dBFS | Spectrum |
|-------|-------|------|----------|
| 0.1 (tap) | -35 dBFS | Narrow |
| 0.3 (light) | -25 dBFS | Medium |
| 0.5 (moderate) | -18 dBFS | Expanded |
| 0.7 (strong) | -12 dBFS | Full bandwidth |
| 1.0 (smash) | -6 dBFS | Peak + distortion edge |

#### Transient Parameters
- **attack_time**: 0.5-5.0ms (harder material = shorter)
- **decay_time**: 10-500ms (metal > concrete > wood > fabric)
- **tail_reverb**: 0-2.0s (spatial resonance)
- **pre_delay**: 5-30ms (simulated mic distance)

#### Frequency Allocation
- Foley range: 100-12000Hz
- Dialogue avoidance: 2000-5000Hz (coordinate with mixer sub-step)
- Low freq: <200Hz (footsteps, impact LF)
- High detail: >5000Hz (metal texture, shattering)

#### Sync Precision
- **sync_tolerance**: ±40ms (production), ±80ms (preview)
- **pre_trigger**: -20ms for footsteps (ground conduction)
- **impact_sync**: visual contact point ±40ms

#### GPU Budget
- Stable Audio Open 1.0: ~6GB | 5s audio in 5-10s GPU time | Total: <= 6GB

### 7D Parametric Matrix

1. **Material**: metal, wood, glass, concrete, fabric, liquid, rubber, flesh, dirt
2. **Action**: impact, scrape, slide, bounce, break, drip, tear
3. **Force**: 0.1 (tap) to 1.0 (smash)
4. **Duration**: transient (<50ms), short (50-500ms), sustain (0.5-2s)
5. **Resonance**: dry, medium, wet
6. **Pitch**: low (<200Hz), mid (200-2000Hz), high (>2000Hz)
7. **Texture**: smooth, rough, gritty, hollow

#### Material Acoustic Signatures
- Metal: bright HF, short transient, long tail (2000-8000Hz)
- Wood: warm MF, medium transient, short decay (500-3000Hz)
- Glass: extreme HF, very short transient, shatter spectrum (3000-12000Hz)
- Concrete: heavy LF, long transient, LF resonance (50-500Hz)
- Fabric: soft friction, MF-HF, no transient (1000-5000Hz)

### Style Rules

#### Sync Rules
- Impact: visual contact point ±40ms
- Footsteps: heel strike -20ms pre-trigger (ground conduction)
- Friction: fully synchronized with visual action
- Environmental: 100-200ms early (hear-before-see realism)

#### Prohibited
- Generic "canned" sound effects (each material-action combo must be unique)
- Force-visual mismatch (light touch with heavy impact sound)
- Over-reverb (destroys source localization)
- Sound covering dialogue (dialogue clarity priority)
- Silent physical contacts (visible impact with no sound)

### Workflow

1. **Action Audit** — Frame-by-frame scan of all physical interactions in video
2. **Material Identification** — Determine interaction materials from visual + scene_builder annotations
3. **7D Encoding** — Generate Material x Action x Force x Duration x Resonance x Pitch x Texture per effect
4. **Sound Synthesis** — Generate each independent stem via Stable Audio Open 1.0 (per [`references/foley/stable-audio-open.md`](./references/foley/stable-audio-open.md))
5. **Force Calibration** — Adjust loudness to match performer's force parameters
6. **Time Alignment** — Position effects precisely to video frames (±40ms)
7. **Frequency Check** — Confirm no dialogue band conflict, EQ if needed
8. **Output** — foley_stems[] + foley_metadata.json + sync_map.json

### Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| material_credibility | >= 0.85 |
| impact_sync_accuracy | >= 0.90 |
| force_consistency | >= 0.80 |
| spectral_clarity | >= 0.82 |

### What NOT to do

- Don't reuse identical sound effects for different material-action combos
- Don't exceed ±40ms sync tolerance (audible to viewers)
- Don't generate Foley in the 2000-5000Hz zone without EQ avoidance
- Don't skip any visible physical interaction (every contact needs sound)
- Don't apply heavy reverb (destroys spatial localization)

## Sub-step: Mixer (Mixing + Mastering)

Multi-track audio mixing and mastering specialist using Senior *Mixing Secrets* heuristics for level balancing, frequency management, dialogue ducking, and LUFS-compliant final master processing per ITU-R BS.1770-4. **Phase 5 v1.5 RAG uplift** per REFACTOR-rest-04.

### Role & Philosophy

- Mixing is about hierarchy — dialogue is king, music serves, effects support
- The audience should never strain to hear dialogue
- Frequency real estate is finite; every stem earns its space

### Core Capabilities

- Multi-track mixing and level balancing (5-12 tracks simultaneously)
- Dialogue ducking automation (dialogue priority protection)
- Frequency avoidance and EQ carving
- Dynamic range control and mastering
- LUFS/LRA precision metering

### Output Format

- `mix_stereo.wav`: final stereo mix (48kHz, 24-bit)
- `mix_5.1.wav`: 5.1 surround mix (if spatial_audio sub-step requires)
- `mix_report.json`: per-track levels, frequency distribution, LUFS/LRA stats
- `stem_balance.json`: per-track gain/spectrum/ducking parameter records

### Key Parameters

#### Multi-Track Mixing
- **max_tracks**: 12 (dialogue×N + music×2 + foley×N + ambience×2)
- **sample_rate**: 48000 Hz
- **bit_depth**: 24-bit
- **buffer_size**: 512-1024 samples
- **pan_range**: -1.0 (left) to +1.0 (right), 0.0 = center

#### EQ Parameters
- **Dialogue**: HPF 80Hz, LF shelf -3dB @200Hz, presence +2dB @3kHz
- **Music**: LPF 16kHz, presence dip -4dB @2.5kHz (dialogue avoidance)
- **Foley**: custom per material, usually HPF 60Hz
- **Ambience**: LPF 8kHz, HPF 40Hz

#### Compression
- **Dialogue bus**: threshold -18dB, ratio 3:1, attack 5ms, release 100ms
- **Music bus**: threshold -12dB, ratio 2:1, attack 20ms, release 300ms
- **Foley bus**: no compression (preserve transients), limiter -3dBFS only

#### Ducking
- **duck_detector**: dialogue stem VAD
- **duck_depth_music**: -6 to -12 dB (when dialogue present)
- **duck_depth_ambience**: -3 to -6 dB
- **duck_attack**: 50-100ms
- **duck_release**: 200-500ms
- **hold_time**: 100-200ms after dialogue ends

#### Mastering
- **LUFS_target**: -16.0 ± 1.0 (stereo), -24.0 ± 2.0 (5.1)
- **LRA_target**: 8-14 LU
- **True_peak**: -1.0 dBTP (stereo), -3.0 dBTP (5.1)
- **Dither**: triangular, for 24-to-16 bit downconversion

#### GPU/CPU Budget
- Mixing: CPU-intensive | Monitoring latency: <20ms | VRAM: <= 1GB (visualization)

### Style Rules

#### 4-Layer Hierarchy
1. **Dialogue** (highest) — always clear and intelligible
2. **Foley/SFX** (high) — synced to visual action
3. **Ambience** (medium) — spatial atmosphere
4. **Music** (lowest) — emotional space filler

#### Level Balance
- Dialogue: -16 LUFS ± 1.5
- Music (with dialogue): -22 to -18 LUFS
- Music (solo): -20 to -14 LUFS
- Foley peaks: -12 to -8 dBFS
- Ambience bed: -35 to -30 LUFS

#### Frequency Allocation
- Dialogue: 2000-5000Hz (sacred, never mask)
- Music LF: 20-200Hz (bass, kick)
- Music MF: 500-2000Hz (sidechain for dialogue avoidance)
- Music HF: 8000-20000Hz (air, shimmer)
- Foley: 100-12000Hz (distributed by material)

#### Dynamic Range
- Target DR: 8-14 LU (EBU R128)
- Dialogue compression: 2:1-4:1
- Master limiter: -1.0 dBTP
- Stereo balance: no > ±1.5 dB offset

#### Prohibited
- Dialogue masked by music or effects (zero tolerance)
- Over-compression causing pumping/breathing
- All tracks at same volume (no layering)
- Hard clipping (any track peak > 0 dBFS)
- Stereo imbalance > ±1.5 dB

### Workflow

1. **Track Loading** — Import all stems, sort by layer priority (dialogue > foley > ambience > music)
2. **Level Pre-balance** — Set baseline levels per track (dialogue -16 LUFS, etc.)
3. **EQ Carving** — Preserve dialogue clarity, music avoids 2000-5000Hz
4. **Ducking Setup** — Configure dialogue detection + auto gain reduction
5. **Frequency Masking Check** — Analyze full spectrum, flag conflict points
6. **Spatial Allocation** — Stereo/5.1 panning (coordinate with spatial_audio sub-step)
7. **Dynamic Range Control** — Compression + limiting, target DR 8-14 LU
8. **Mastering** — LUFS normalization + True Peak limiting + Dither
9. **Quality Audit** — Perceptual check + data validation
10. **Output** — mix_stereo.wav + mix_report.json + stem_balance.json

### Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| level_compliance | >= 0.88 |
| frequency_masking_score | >= 0.85 |
| dialogue_intelligibility | >= 0.92 |
| dynamic_range_appropriateness | >= 0.85 |

### What NOT to do

- Don't let anything mask dialogue (zero tolerance policy)
- Don't compress beyond 4:1 on dialogue bus (causes pumping)
- Don't skip the frequency masking check (catches hidden conflicts)
- Don't exceed -1.0 dBTP True Peak (broadcast standard)
- Don't master without checking LUFS against target

## Sub-step: Spatial Audio (3D Encoding)

> **Folded into audio_pipeline per disposition D-1** (see §Spatial Audio Disposition above). The v1 standalone `spatial_audio` expert becomes this sub-step; its redirect stub uses `status: folded_into` (distinct from `merged_into` for the other 5 predecessors).

Spatial acoustics and design sound specialist using Dolby Atmos bed+objects architecture, 6D spatial encoding, HRTF binaural rendering, and 5 immersive sound patterns for cinematic 3D sound field design. **Phase 5 v1.5 RAG uplift** per REFACTOR-rest-01.

### Role & Philosophy

- Sound has position — where it comes from tells the audience as much as what it is
- Space has voice — room acoustics reveal environment character
- Distance is emotional — far sounds feel lonely, close sounds feel intimate

### Core Capabilities

- 6D spatial acoustic encoding (azimuth x elevation x distance x spread x roll-off x reverb)
- Environmental sound field design (indoor/outdoor acoustic modeling)
- Distance attenuation and air absorption physics modeling
- Reality Anchoring: environmental sound builds spatial "realism"
- Vacuum Detection: catch unnatural acoustic silences

### Output Format

- `spatial_mix.json`: per-source 6D spatial coordinates + attenuation parameters
- `ambience_stems[]`: environmental stems (indoor/outdoor, near/far)
- `reverb_profile.json`: reverb parameters (room size, reflections, decay)
- `vacuum_report.json`: acoustic void detection results and fix suggestions

### Key Parameters

#### 6D Spatial Encoding
- **azimuth**: 0-360° (±5° precision, 0°=front, 90°=right, 180°=rear, 270°=left)
- **elevation**: -90° to +90° (±5° precision)
- **distance**: 0.5-50.0m (±0.1m precision)
- **spread**: 0.0-1.0 (0.0=point source, 1.0=full surround)
- **roll_off_model**: inverse_square (default), inverse, logarithmic
- **reverb_wet**: 0.0-1.0 (±0.05 precision)

#### Distance Attenuation
- **reference_distance**: 1.0m
- **max_distance**: 50.0m
- **rolloff_factor**: 1.0 (standard), 0.5 (slow), 2.0 (fast)
- **air_absorption**: 0.5-2.0 dB per 10m @8kHz

#### Reverb Parameters
- **preset**: small_room, medium_room, large_hall, cathedral, outdoor, custom
- **RT60**: 0.2-5.0s
- **early_reflections**: 0-80ms, 6-12 reflection points
- **diffusion**: 0.3-1.0
- **HF_damping**: 0.1-0.9

#### 5.1 Channel Allocation
- L (front-left): 30° ± 15° | R (front-right): 330° ± 15°
- C (center): 0° ± 10° (dialogue default)
- LFE: omnidirectional, <120Hz
- Ls (rear-left): 150° ± 15° | Rs (rear-right): 210° ± 15°

#### Environment Ambience
- Indoor: -40 to -30 LUFS (pink noise + LF hum)
- Outdoor: -35 to -25 LUFS (wind + random natural sounds)
- Scene transition crossfade: 1.0-2.0s

#### GPU Budget
- Spatial processing: CPU-intensive (FFT convolution) | GPU: ~2GB if accelerated | Total: <= 3GB

### Style Rules

#### Environment Sound Fields
- Small indoor: RT60 < 0.5s, strong early reflections, HF absorption
- Medium indoor: RT60 0.5-1.5s, moderate reverb
- Large indoor: RT60 1.5-4.0s, long tail, LF enhancement
- Near outdoor: no reverb, air absorption, fast distance decay
- Far outdoor: natural reverb (mountains, buildings), blurred sources

#### Reality Anchoring
- Every scene MUST have continuous environmental bed (never silence)
- Indoor: HVAC/fridge/appliance hum (-40 to -30 LUFS)
- Outdoor: wind/traffic/birds (-35 to -25 LUFS)
- Bed interruption = scene change signal (important narrative tool)

#### Distance Transitions
- Near→far: level drop + HF rolloff + reverb increase + detail blur
- Far→near: level boost + HF recovery + reverb decrease + detail sharpening
- Transition time: >= 0.5s (sudden jumps need narrative motivation)

#### Vacuum Detection
- Target: 2+ seconds of acoustic silence
- Fix: insert matching environmental bed or faint ambience
- Legal vacuum: deliberate silence after emotional climax (must be scripted)

#### Prohibited
- Panning contradicting visual position (left visual, right audio)
- Zero ambience "vacuum" scenes
- All sources at same distance (no depth layering)
- Reverb type mismatching space (small room + cathedral reverb)

### Workflow

1. **Space Analysis** — Determine sound field type from scene_builder layout (indoor/outdoor/size)
2. **Source Placement** — Assign 6D coordinates per source (following character/object positions)
3. **Distance Modeling** — Calculate per-source distance attenuation curves
4. **Reverb Design** — Select reverb preset by space type, adjust RT60/diffusion/HF damping
5. **Ambience Generation** — Create scene-specific ambience stem (continuous presence)
6. **Reality Anchor Check** — Verify every scene has continuous environmental bed
7. **Distance Transition** — Generate spatial parameter fades for movement/shot changes
8. **5.1 Allocation** — Map spatial coordinates to 5.1/7.1 channels
9. **Vacuum Detection** — Scan for acoustic silences and repair
10. **Output** — spatial_mix.json + ambience_stems + reverb_profile + vacuum_report

### Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| spatial_coherence | >= 0.85 |
| reality_anchor_stability | >= 0.80 |
| distance_transition_smoothness | >= 0.88 |
| vacuum_detection_pass | >= 0.90 |

### What NOT to do

- Don't leave any scene without environmental ambience (Reality Anchor)
- Don't place audio sources contradicting visual positions
- Don't use cathedral reverb in small room scenes
- Don't allow 2+ second acoustic silences without script justification
- Don't skip 5.1 channel allocation for surround output

## Collaboration

> **Merged collaboration graph.** Cross-references to OTHER experts (screenplay, performer, editor, production, visual_executor, continuity_auditor, style_genome, scene_builder) remain inter-expert edges. References between the 6 audio sub-steps (voicer↔lip_sync↔composer↔foley↔mixer↔spatial_audio) are now intra-expert handoffs (internal to `audio_pipeline`) — see the `## Sub-steps` section above.

### Voicer sub-step inbound / outbound (external + internal handoffs)

- **<- screenplay**: dialogue text + emotion_curve + scene context
- **<- performer**: character psychology, action-to-voice sync points
- **<- editor**: timing marks, cut boundaries, dialogue pacing intent
- **→ [internal handoff to Lip Sync sub-step — see §Sub-step: Lip Sync above]**: `dialogue.wav` audio input (voicer synthesizes audio; lip_sync aligns it to footage)
- **→ [internal handoff to Mixer sub-step — see §Sub-step: Mixer below]**: dialogue stem (WAV) + metadata for level balancing
- **-> performer**: lip-sync alignment data for facial animation
- **→ [internal handoff to Spatial Audio sub-step — see §Sub-step: Spatial Audio below]**: dialogue position data for spatial placement

### Lip Sync sub-step inbound / outbound (external + internal handoffs)

- **← [internal handoff from Voicer sub-step — see §Sub-step: Voicer above]**: `dialogue.wav` audio input
- **<- [`visual_executor`](../visual_executor/SKILL.md)**: silent character video footage(角色对话镜头无音频版)
- **<- [`performer`](../performer/SKILL.md)**: performance baseline(表情、头部姿态基线)
- **-> [`editor`](../editor/SKILL.md)**: synced footage 进入剪辑
- **-> [`continuity_auditor`](../continuity_auditor/SKILL.md)**: identity preservation 审计
- **→ [internal handoff to Mixer sub-step — see §Sub-step: Mixer below]**: 最终音频与视频对齐

### Composer sub-step inbound / outbound (external + internal handoffs)

- **<- screenplay**: emotion_curve, sound_mood, scene structure
- **<- editor**: cut points, shot durations for beat alignment
- **<- style_genome**: genre, director style references
- **→ [internal handoff to Mixer sub-step — see §Sub-step: Mixer below]**: music stem + coupled_beat.json for ducking and balancing
- **→ [internal handoff to Foley sub-step — see §Sub-step: Foley above]**: beat grid for rhythmic Foley sync
- **→ [internal handoff to Spatial Audio sub-step — see §Sub-step: Spatial Audio below]**: spatial placement instructions for surround mix

### Foley sub-step inbound / outbound (external + internal handoffs)

- **<- [`visual_executor`](../visual_executor/SKILL.md)**: video clips (action audit input)
- **<- [`performer`](../performer/SKILL.md)**: force, speed, contact point parameters
- **<- [`scene_builder`](../scene_builder/SKILL.md)**: material annotations (floor, object materials)
- **← [internal handoff from Composer sub-step — see §Sub-step: Composer above]**: beat timeline (rhythm alignment)
- **→ [internal handoff to Mixer sub-step — see §Sub-step: Mixer below]**: foley_stems[] + foley_metadata.json (mixing input)
- **→ [internal handoff to Spatial Audio sub-step — see §Sub-step: Spatial Audio below]**: spatial position data (3D sound field placement)
- **-> [`continuity_auditor`](../continuity_auditor/SKILL.md)**: sound effect consistency check (same material + force = similar)

### Mixer sub-step inbound / outbound (external + internal handoffs)

- **← [internal handoff from Voicer sub-step — see §Sub-step: Voicer above]**: dialogue stems + metadata
- **← [internal handoff from Composer sub-step — see §Sub-step: Composer above]**: music stems + coupled_beat.json
- **← [internal handoff from Foley sub-step — see §Sub-step: Foley above]**: sound stems + foley_metadata.json
- **← [internal handoff from Spatial Audio sub-step — see §Sub-step: Spatial Audio above]**: spatial field data + 5.1 panning instructions
- **<- editor**: edit timeline (audio sync)
- **→ [internal handoff to Spatial Audio sub-step — see §Sub-step: Spatial Audio above]**: post-mix stereo/5.1 output
- **-> [`continuity_auditor`](../continuity_auditor/SKILL.md)**: final audio consistency confirmation

### Spatial Audio sub-step inbound / outbound (external + internal handoffs)

- **<- [`scene_builder`](../scene_builder/SKILL.md)**: 3D layout, material annotations (acoustic reflection coefficients)
- **← [internal handoff from Foley sub-step — see §Sub-step: Foley above]**: sound stems + position timeline
- **← [internal handoff from Voicer sub-step — see §Sub-step: Voicer above]**: dialogue stems + character positions
- **← [internal handoff from Composer sub-step — see §Sub-step: Composer above]**: music stems + spatial instructions
- **← [internal handoff from Mixer sub-step — see §Sub-step: Mixer above]**: mixing level allocation
- **<- editor**: shot change timeline
- **→ [internal handoff to Mixer sub-step — see §Sub-step: Mixer above]**: spatial-processed stems (with panning and reverb)
- **→ [internal handoff to Foley sub-step — see §Sub-step: Foley above]**: position corrections (if panning contradicts visuals)
- **-> [`continuity_auditor`](../continuity_auditor/SKILL.md)**: spatial consistency confirmation

## Changelog

- **2026-06-17** — Merged 5 audio predecessors (`voicer` v1.1.0, `lip_sync` v1.0.0, `composer` v1.1.0, `foley` v1.0.0, `mixer` v1.1.0) + folded 1 (`spatial_audio` v1.1.0) into `audio_pipeline` (v1.0.0) per Phase 15 MERGE-02. **Predecessors:** `skills/movie-experts/{voicer,lip_sync,composer,foley,mixer}/SKILL.md` (5 now redirect-only stubs with `status: merged_into` + `merged_into: audio_pipeline`), `skills/movie-experts/spatial_audio/SKILL.md` (1 redirect-only stub with `status: folded_into` + `folded_into: audio_pipeline` — distinct from `merged_into` per disposition D-1). **Rationale:** Phase 7 §4.9 + PITFALLS §2.6 — "5-task compression; consistency context unified". The v1 voicer↔lip_sync↔composer↔foley↔mixer↔spatial_audio inter-expert collaboration edges are now intra-expert sub-step handoffs of one expert_id (`audio_pipeline`), eliminating the consistency context drift across the 6 audio disciplines (dialogue/music/foley/ambience LUFS targets, frequency allocation, ducking, 5.1 channel allocation now decided in one expert). **spatial_audio fold rationale (disposition D-1):** Spatial audio rendering is fundamentally a mixer/mastering concern (Dolby Atmos bed+objects, 6D encoding, HRTF binaural, immersive sound patterns operate on the same stems mixer operates on). Fold preserves the unique HRTF/Atmos technical content (irreplaceable domain knowledge). Rejected alternative = deprecation (loses irreplaceable HRTF/Atmos tables). Documented in `## Spatial Audio Disposition` H2 section per ROADMAP §15 criterion #2. **lip_sync explicit sub-step rationale (Phase 8 §2.9 NODE-09):** lip_sync was implicit in v1 (only a voicer→lip_sync collaboration edge); v2.0 PRFP DAG promotes it to an explicit sub-step because it carries unique objective validation (LRS2/LRS3 benchmark + LSE/LSE-C via SyncNet — no LLM-judge required) and must pair with a theory_critic on output identity preservation. Documented in `## Sub-step: Lip Sync` opening note per ROADMAP §15 criterion #5. **Backward-compat aliases:** `metadata.hermes.aliases: [voicer, lip_sync, composer, foley, mixer, spatial_audio]` declared per FOUND-08 (zero silent merges — aliases declared explicitly). **New top-level frontmatter field:** `sub_steps: [voicer, lip_sync, composer, foley, mixer, spatial_audio]` per v2.0 PRFP DAG convention (extends Phase 14's 2-item `sub_steps` to a 6-item array). **Refs:** 23 ref files (4 voicer + 5 lip_sync + 4 composer + 4 foley + 3 mixer + 3 spatial_audio — including 6 LICENSEs) migrated verbatim to `references/{voicer,lip_sync,composer,foley,mixer,spatial_audio}/` sub-folders. **GAP-REPORT:** consolidated from 5 predecessors with GAP-REPORTs (voicer, composer, foley, mixer, spatial_audio) + 1 placeholder note for lip_sync (which has no GAP-REPORT — only `_eval/prompts/` regression suite).
