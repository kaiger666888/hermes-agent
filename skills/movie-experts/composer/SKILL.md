---
name: composer
description: "Composer Expert: background music generation, sound effect design, music-video synchronization via coupled beats for AI film."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, music, score, sound, beat-sync, film-scoring, musicgen]
    related_skills: [screenplay, editor, style_genome, mixer, foley, spatial_audio]
    expert_id: composer
    metrics: [emotional_sync, spatial_coherence, dynamic_range]
---

# Composer Expert (音乐/音效专家)

Film scoring and sound design specialist for background music generation, coupled beat design for music-edit synchronization, and genre-specific arrangement in AI film production.

## When to use this skill

The user needs to generate film scores, create background music, design audio beats synchronized with video editing, or produce music stems for AI film production.

## References

| Ref | When to Read | Contents |
|-----|--------------|----------|
| _(Phase 3 will populate with curated refs)_ | — | — |

## Role & Philosophy

- Music amplifies emotion without dictating it
- Silence is a powerful instrument — use it deliberately
- Rhythmic sync between music and editing creates invisible continuity

## Core Capabilities

- Film scoring grammar (leitmotif, underscore, stinger, source music)
- Coupled beat design for music-edit synchronization
- Genre-specific arrangement and orchestration
- Emotional mapping: scene mood to musical parameters

## Output Format

- Music stem: WAV 48kHz 24-bit stereo (or 5.1/7.1)
- `coupled_beat.json`: beat timestamps + energy curve + emotional annotations
- `light_beat.json`: downbeat-level markers for editor sync

## Key Parameters

### Music Generation
- **model**: MusicGen-large (primary, 32kHz stereo)
- **guidance_scale**: 3.0-7.0 (higher = closer to prompt)
- **temperature**: 0.8-1.2
- **generation_length**: 30s per segment (loop/extend for longer)
- **sample_rate**: 48000 Hz (production), 32000 Hz (preview)

### Audio Specs
- **bit_depth**: 24-bit (production), 16-bit (preview)
- **channels**: stereo (default), 5.1/7.1 (coordinate with spatial_audio)
- **LUFS_target**: -20 to -14 (film underscore)

### Coupled Beat Design
- **light_beat.json**: primary downbeats every 1-4 bars, timestamped
- **coupled_beat.json**: full beat grid + energy_per_beat (0.0-1.0) + emotion_tag
- **beat_resolution**: 16th note granularity
- **coupling_strength**: 0.3 (loose) to 0.8 (tight)

### Dynamic Range
- **target_DR**: 8-14 LU (EBU R128)
- **compression_ratio**: 2:1-4:1 (gentle)
- **limiter_ceiling**: -1.0 dBTP
- **frequency_avoidance**: 2000-5000 Hz zone (dialogue territory)

### GPU Budget
- MusicGen-large: ~6GB VRAM for 30s | ~15-30s generation time | 1 at a time

## Style Rules

### Scoring Standards
- Underscore for emotional support, source for diegetic world-building
- Leitmotif: 2-4 bar recurring phrase per key character/theme
- Dynamic shaping: music swells/fades with scene emotion
- Sparse for intimate, full for dramatic climaxes

### BPM Guide
- 60-80 (contemplative), 80-120 (neutral/narrative), 120-160 (tension/action)
- Max ±20 BPM per scene, gradual (2+ seconds)

### Genre Guidelines
- Drama: strings + piano, minimal percussion
- Thriller: low strings + percussion + dissonance
- Romance: woodwinds + strings, legato
- Sci-fi: synthesizers + processed instruments
- Comedy: pizzicato + woodwinds, staccato

### Prohibited
- Constant wall-to-wall music
- Music fighting dialogue in 2000-5000Hz
- Melodic hooks that distract from narrative
- Genre mismatch | Over-compressed dynamics

## Workflow

1. **Mood Analysis** — Map `emotion_curve` to musical parameters (BPM, key, instrumentation)
2. **Genre Selection** — Determine scoring approach from `style_genome` + `sound_mood`
3. **Prompt Construction** — Build text-to-music prompt with genre/mood/tempo
4. **Music Generation** — Generate 30s segments via MusicGen, extend/loop as needed
5. **Beat Extraction** — Analyze output for beat grid, create `coupled_beat.json`
6. **Dynamic Shaping** — Volume automation to match scene emotion curve
7. **Frequency Check** — Verify no clash with dialogue zone (2000-5000Hz)
8. **Export Stems** — Output music WAV + coupled_beat.json + light_beat.json

## Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| emotional_sync | >= 0.85 |
| spatial_coherence | >= 0.80 |
| dynamic_range | 8-14 LU |
| genre_fidelity | >= 0.80 |

## Collaboration

- **<- screenplay**: emotion_curve, sound_mood, scene structure
- **<- editor**: cut points, shot durations for beat alignment
- **<- style_genome**: genre, director style references
- **-> mixer**: music stem + coupled_beat.json for ducking and balancing
- **-> foley**: beat grid for rhythmic Foley sync
- **-> spatial_audio**: spatial placement instructions for surround mix

## What NOT to do

- Don't generate wall-to-wall music (scenes need breathing room)
- Don't occupy the 2000-5000Hz zone (dialogue territory)
- Don't compress beyond 4:1 (kills film scoring dynamics)
- Don't run MusicGen alongside drawer/animator on single GPU
- Don't ignore editor's cut points (coupled beats must align)
