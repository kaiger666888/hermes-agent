# TTS Emotion and Prosody Control (TTS 情感与韵律控制方法论)

**Source:** Adapted from OpenClaw kais-TTS-agent (Speech-AI-Forge / Qwen3-TTS methodology) + TTS industry emotion-control literature.
**Copyright:** Fair Use — methodology distillation.
**Last-verified:** 2026-06-16

## Summary

Methodology for controlling emotion and prosody in TTS-generated character voices. Complements [`./cn-tts-model-matrix.md`](./cn-tts-model-matrix.md) (engine selection) and [`./character-voice-consistency.md`](./character-voice-consistency.md) (cross-shot identity) by providing the per-utterance craft of emotional delivery.

## Heuristics

### Emotion taxonomy for TTS

Per Ekman 7 basic emotions + Plutchik 8-dim (per [`../../screenplay/references/emotion-curve-academic.md`](../../screenplay/references/emotion-curve-academic.md)):

| Emotion | Valence | Arousal | TTS parameter signature |
|---|---|---|---|
| Neutral | 0 | Low | speed=1.0, pitch_shift=0, no emphasis tags |
| Joy | +1 | High | speed=1.05-1.15, pitch_shift=+2 to +5, brighter timbre |
| Sadness | -1 | Low | speed=0.85-0.95, pitch_shift=-2 to -5, breathy timbre |
| Anger | -1 | High | speed=1.10-1.25, pitch_shift=-2 to +2 (variable), pressed timbre |
| Fear | -1 | High | speed=1.15-1.30, pitch_shift=+3 to +8, trembling timbre |
| Surprise | 0 | High | speed=1.20-1.35 (initial burst), pitch_shift=+5 to +10 |
| Contempt | -1 | Low | speed=0.95-1.05, pitch_shift=-3 to -1, nasal timbre |
| Disgust | -1 | Medium | speed=0.95-1.05, pitch_shift=-2 to 0, guttural timbre |

### Prosody control parameters

| Parameter | Range | Default | Effect |
|---|---|---|---|
| `speed_factor` | 0.7-1.4 | 1.0 | Speaking rate; 1.0 = natural |
| `pitch_shift` | -12 to +12 semitones | 0 | Pitch shift per character; preserves formants |
| `energy_factor` | 0.5-2.0 | 1.0 | Loudness contour; 1.0 = natural |
| `pause_factor` | 0.5-2.0 | 1.0 | Inter-sentence pause scaling |
| `breathiness` | 0.0-1.0 | 0.2 | Amount of breath in voice (higher = more intimate/weak) |
| `roughness` | 0.0-1.0 | 0.1 | Vocal cord roughness (higher = more angry/strained) |

### Emotion tag insertion (in-line control)

For per-word or per-phrase emotion modulation, use inline tags:

```
[neutral] 你来了。 [pause:300ms] [sadness:intensity=0.7] 我以为你不会回来了。
```

**Supported tags** (varies by engine, see [`../../_shared/known-external-models.yaml`](../../_shared/known-external-models.yaml)):
- `[<emotion>:intensity=<0-1>]` — emotion shift
- `[pause:<ms>]` — explicit pause
- `[emphasis]word[/emphasis]` — word emphasis
- `[whisper]word[/whisper]` — whispered delivery
- `[shout]word[/shout]` — shouted delivery
- `[laugh]word[/laugh]` — laughed-through delivery
- `[cry]word[/cry]` — cried-through delivery

### Per-character voice baseline

For each character (per CharacterBible 2.0 from [`../../character_designer/SKILL.md`](../../character_designer/SKILL.md)):

```yaml
voice_baseline:
  base_speed: 1.0
  base_pitch_shift: 0
  default_emotion: "calm_intensity=0.3"
  emotion_range:
    joy: "intensity_0.3_to_0.7"
    anger: "intensity_0.5_to_0.9"
    sadness: "intensity_0.4_to_0.8"
  signature_quirks:
    - "slight_pause_before_emotional_words"
    - "pitch_drops_at_end_of_statement"
```

**Hard rule:** voice_baseline is locked per character (per CharacterBible consistency_lock). Per-utterance emotion shifts modulate AROUND the baseline, not replace it.

### Cross-utterance coherence

For dialogue scenes with multiple utterances from same character:

1. **Voice identity:** same speaker_embedding across all utterances
2. **Emotion arc:** emotion per utterance follows scene emotion_curve
3. **Transition smoothness:** no abrupt emotion jumps unless motivated by plot

**Anti-pattern:** having character switch from "extreme joy" to "extreme sadness" in adjacent utterances without a beat of transition.

### Per-genre TTS conventions

| Genre | Default emotion style | Quirks |
|---|---|---|
| 男频-revenge | Flat/controlled → burst at climax | Calm intensity in early scenes, peak intensity at confrontation |
| 女频-romance | Warm/breathy | Higher breathiness default |
| Cyberpunk | Flat/affective | Lower pitch variance, more pauses |
| Wuxia | Stylized/classical | Slower speed, more emphasis tags |
| Horror | Whispers + sudden shouts | Extreme emotion range |

### Integration with screenplay emotion_curve

Per scene, the screenplay emits emotion_curve anchors (per [`../../screenplay/references/emotion-curve-academic.md`](../../screenplay/references/emotion-curve-academic.md)):

**Mapping protocol:**
1. For each dialogue utterance, find the nearest emotion_curve anchor
2. Map anchor (valence, arousal) to emotion category (per Ekman mapping)
3. Apply emotion tag with intensity proportional to arousal
4. Verify emotion shifts across utterances follow the curve shape

**Example mapping:**
- emotion_curve anchor: valence=-0.5, arousal=0.8
- → emotion category: "anger" (negative valence + high arousal)
- → TTS tag: `[anger:intensity=0.8]`

### Per-platform TTS divergence

Per [`./cn-tts-model-matrix.md`](./cn-tts-model-matrix.md):

| Platform | Typical use | Recommended engine |
|---|---|---|
| 抖音 (mass) | High-energy, clear pronunciation | MiniMax T2A-01 (CN-native) |
| 快手 (grassroots) | Natural, slightly unpolished | NeuTTS (CN本土) |
| 小红书 (lifestyle) | Warm, conversational | Gemini TTS (preset) |
| YouTube (global) | English / multilingual | ElevenLabs Multilingual v2 |

### Common TTS failures and fixes

| Failure | Cause | Fix |
|---|---|---|
| Robotic delivery | Default model params | Add `[breathiness:0.3]` + emotion tags |
| Wrong emotion | Engine doesn't support tag | Switch engine OR use SSML alternative |
| Emotion intensity too high | Default 1.0 intensity | Reduce to 0.5-0.7 for natural delivery |
| Cross-utterance inconsistency | Different voice seed per call | Lock speaker_embedding per character |
| Mismatched duration | TTS generates wrong length | Use `duration_target_ms` parameter OR adjust speed_factor |

### Per the cognitive-resonance-metrics alignment

Per [`../../_shared/cognitive-resonance-metrics.md`](../../_shared/cognitive-resonance-metrics.md):

- **Scale 1 (neural):** TTS onset must align with visual lip movement ±120ms (drives [`../../lip_sync/SKILL.md`](../../lip_sync/SKILL.md) requirements)
- **Scale 2 (emotional):** TTS emotion arc must match scene emotion_curve sawtooth
- **Scale 1:** TTS pacing must respect attention-capture spacing (≤ 8s gap)

---

## Cross-references

- [`./cn-tts-model-matrix.md`](./cn-tts-model-matrix.md) — engine selection
- [`./character-voice-consistency.md`](./character-voice-consistency.md) — cross-shot identity
- [`../../screenplay/references/emotion-curve-academic.md`](../../screenplay/references/emotion-curve-academic.md) — emotion_curve source
- [`../../character_designer/SKILL.md`](../../character_designer/SKILL.md) — CharacterBible voice_baseline consumer
- [`../../lip_sync/SKILL.md`](../../lip_sync/SKILL.md) — downstream audio consumer (lip-sync to TTS output)
- [`../../_shared/cognitive-resonance-metrics.md`](../../_shared/cognitive-resonance-metrics.md) §Scale 1+2 — neural + emotional alignment
