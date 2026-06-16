# BGM and Song Creation Methodology (背景音乐与歌曲创作方法论)

**Source:** Adapted from OpenClaw kais-bgm (dual-engine: local library + AI generation) + kais-song-agent (ACE-Step 1.5 workflow).
**Copyright:** Fair Use — methodology distillation.
**Last-verified:** 2026-06-16

## Summary

Operational methodology for BGM (background music) selection + AI generation, and full song creation pipeline. Decoupled from [`./musicgen-workflow.md`](./musicgen-workflow.md) (which covers MusicGen-Large inference) — this file covers the higher-level creative strategy.

## Heuristics

### Dual-engine BGM architecture

For any scene requiring BGM:

**Engine 1: Local library match (default, fast, cheap)**
- Maintain a curated local library tagged by (emotion, tempo, genre, instrumentation, duration)
- For each scene, query library by emotion_curve tags
- Match score: emotion similarity (0.6) + tempo fit (0.2) + duration fit (0.2)

**Engine 2: AI generation (when library match fails OR custom mood needed)**
- Use `<audio_gen_primary>` per [`../../_shared/known-external-models.yaml`](../../_shared/known-external-models.yaml)
- Generate based on emotion_curve + scene duration + instrumentation preferences
- Higher cost (~10-50× library match), but custom-fit

**Selection logic:**
```
if library_match_score >= 0.75:
    use library match
elif library_match_score >= 0.50 AND budget_limited:
    use library match (acceptable)
else:
    use AI generation
```

### BGM strategy from emotion_curve

Given a scene's emotion_curve (per [`../../screenplay/references/emotion-curve-academic.md`](../../screenplay/references/emotion-curve-academic.md)):

| Emotion curve shape | BGM strategy |
|---|---|
| Monotonic rising | Sustained crescendo, key instruments added progressively |
| Sawtooth (peaks + drops) | Stab pattern: short motifs at peaks, silence at drops |
| Plateau | Ambient drone with subtle texture variation |
| Free-fall (sudden drop) | Sudden instrument cut OR dissonant chord |
| Peak-valley | Two contrasting motifs alternating |

### Per-genre BGM conventions

| Genre | Default BPM | Key instruments | Avoid |
|---|---|---|---|
| 男频-revenge | 90-120 | Strings + percussion + brass | Woodwinds (too soft) |
| 女频-romance | 60-90 | Piano + strings + acoustic guitar | Heavy percussion |
| Cyberpunk | 120-140 | Synth + electronic drums + bass | Acoustic instruments |
| Wuxia | 70-100 | Erhu + dizi + guqin + percussion | Western instruments |
| Horror | 60-80 (variable) | Dissonant strings + sub-bass + atonal | Major key melodies |
| Comedy | 110-140 | Pizzicato strings + woodwinds + light percussion | Heavy dramatic strings |

### Song creation pipeline (ACE-Step-style)

For original songs (theme song, insert song, character song):

**Phase 1: Creative ideation**
- Identify song purpose (theme / character / mood / plot point)
- Define target emotion arc (matches some scene's emotion_curve)
- Specify language (CN / EN / bilingual)
- Define duration (full song 3-4min / short version 60-90s for 短剧 use)

**Phase 2: Lyrics creation**
- Verse-chorus structure (typical: V-C-V-C-Bridge-C-Outro)
- Rhyme scheme (CN: 押韵 in 4-tone system; EN: AABB or ABAB)
- Subtext ratio ≥ 60% (per [`../../screenplay/references/dialogue-craft.md`](../../screenplay/references/dialogue-craft.md))
- Avoid "as you know" anti-pattern (same as dialogue)

**Phase 3: Composition parameters**
- Key signature (matching emotional valence: major = positive, minor = negative)
- Time signature (4/4 default; 3/4 for waltz/dream; 6/8 for flowing)
- BPM (per genre conventions above)
- Instrumentation (per genre conventions)

**Phase 4: Engine invocation**
- Use `<song_gen_primary>` (e.g., ACE-Step 1.5) per [`../../_shared/known-external-models.yaml`](../../_shared/known-external-models.yaml)
- Input: lyrics + composition params + reference audio (optional)
- Output: audio file (WAV preferred for production, MP3 for review)

**Phase 5: Post-processing**
- EQ carving per [`../../mixer/references/lufs-standards.md`](../../mixer/references/lufs-standards.md) (LUFS target by platform)
- Dynamic range compression
- Stereo widening (avoid over-widening for vocal-forward songs)
- Final LUFS check per platform target

### Per-platform LUFS targets (for BGM + songs)

Per [`../../mixer/references/lufs-standards.md`](../../mixer/references/lufs-standards.md):

| Platform | LUFS target | True peak max |
|---|---|---|
| 抖音 / 快手 | -10 LUFS | -1 dBTP |
| Spotify | -14 LUFS | -1 dBTP |
| YouTube | -14 LUFS | -1 dBTP |
| Apple Music | -16 LUFS | -1 dBTP |
| 小程序 internal | -16 LUFS | -1 dBTP |

### Tempo synchronization with editor cuts

For BGM that must sync with editor's cuts:

**Sync protocol:**
1. Editor provides cut timestamps (per [`../../editor/SKILL.md`](../../editor/SKILL.md) shot list)
2. Composer generates BGM at exact scene duration
3. Beat markers placed at cut timestamps (within ±100ms)
4. Final mix verifies beat-cut alignment

**Per [`../../_shared/cognitive-resonance-metrics.md`](../../_shared/cognitive-resonance-metrics.md) §Scale 1:** audio-visual binding drift < 120ms; BGM beat vs cut drift should be ≤ 80ms (tighter than the perception threshold for production quality).

### Common pitfalls

| Pitfall | Cause | Fix |
|---|---|---|
| BGM overpowers dialogue | Mixing balance wrong | Apply dialogue ducking per [`../../mixer/references/mixing-secrets-small-studio.md`](../../mixer/references/mixing-secrets-small-studio.md) |
| Generic stock music feel | Default library pulls | Use AI generation OR curate library more aggressively |
| Tempo doesn't match scene | Composer didn't sync with editor | Re-generate at correct BPM OR ask editor to re-cut |
| Lyrics too "on-the-nose" | Subtext ratio < 60% | Rewrite with more metaphoric language |
| Song too long for 短剧 | Default 3-4min format | Generate 60-90s short version |

---

## Cross-references

- [`./musicgen-workflow.md`](./musicgen-workflow.md) — MusicGen-Large inference details
- [`./chion-audio-vision.md`](./chion-audio-vision.md) — audio-vision relationship theory
- [`../../screenplay/references/emotion-curve-academic.md`](../../screenplay/references/emotion-curve-academic.md) — emotion_curve source
- [`../../mixer/references/lufs-standards.md`](../../mixer/references/lufs-standards.md) — per-platform LUFS targets
- [`../../_shared/known-external-models.yaml`](../../_shared/known-external-models.yaml) — `<audio_gen_primary>` + `<song_gen_primary>` placeholders
