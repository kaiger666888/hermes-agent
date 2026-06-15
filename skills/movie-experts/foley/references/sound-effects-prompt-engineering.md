# Sound Effects Prompt Engineering (音效 prompt 工程方法论)

**Source:** Adapted from OpenClaw kais-sound-effects-agent (Sony Woosh prompt engineering methodology) + sound design industry standards.
**Copyright:** Fair Use — methodology distillation.
**Last-verified:** 2026-06-16

## Summary

Methodology for crafting effective prompts for AI-generated sound effects. Complements [`./stable-audio-open.md`](./stable-audio-open.md) (engine specs) and [`./sound-effect-taxonomy.md`](./sound-effect-taxonomy.md) (BBC 21-category taxonomy) by providing the prompt-level craft.

## Heuristics

### The 5-component SFX prompt structure

Effective SFX prompts include 5 components:

```
{source} + {action} + {environment} + {proximity} + {temporal_dynamics}
```

**Example:**
- ✅ `glass bottle breaking on concrete floor, sharp shattering, distant room echo, close-up perspective, instantaneous impact with 200ms decay tail`
- ❌ `breaking glass` (too vague)

### Component specifications

#### Component 1: Source

The physical object producing the sound.

| Source category | Examples | Prompt keywords |
|---|---|---|
| Solid impacts | glass, ceramic, metal, wood | "glass bottle", "ceramic plate", "steel pipe" |
| Liquid | water, oil, blood | "water drop", "oil sizzle", "wet impact" |
| Gas/Air | wind, breath, explosion | "wind howl", "sharp exhale", "distant explosion" |
| Organic | footstep, body impact, voice | "leather shoe on tile", "fist on flesh", "grunt" |
| Mechanical | engine, gear, motor | "diesel engine idle", "metallic gear grind" |
| Electronic | beep, hum, glitch | "high-pitched beep", "60Hz electrical hum" |

**Specificity rule:** always name the specific material (e.g., "ceramic plate" not just "plate").

#### Component 2: Action

The force or motion producing the sound.

| Action category | Examples |
|---|---|
| Impact (instant) | break, shatter, slam, crack |
| Sustained | hum, buzz, drone, ring |
| Friction | scrape, slide, drag, rub |
| Movement | roll, spin, fall, swing |
| Explosion | burst, pop, boom, detonate |

**Intensity modifier:** add "sharp", "dull", "heavy", "light" to qualify.

#### Component 3: Environment

The acoustic space.

| Environment | Acoustic signature | Prompt keywords |
|---|---|---|
| Open outdoor | no reflections, distant echoes | "open field", "distant mountain echo" |
| Small room | short reverb (~200ms) | "small bedroom", "tight reverb" |
| Large hall | long reverb (1-3s) | "cathedral", "concert hall" |
| Industrial | metallic ringing | "factory floor", "metallic resonance" |
| Vehicle interior | confined, low-frequency rumble | "car interior", "low rumble floor" |

#### Component 4: Proximity

Distance from microphone perspective.

| Perspective | Prompt keyword | Mix level |
|---|---|---|
| Close-up (intimate) | "close-up", "intimate", "in-ear" | -3 to 0 dB |
| Near (present) | "near", "present" | -6 to -3 dB |
| Mid (normal) | (default, no qualifier) | -12 to -6 dB |
| Far (distant) | "distant", "far away" | -18 to -12 dB |
| Background (ambient) | "background", "ambient" | -24 to -18 dB |

#### Component 5: Temporal dynamics

How the sound evolves over time.

| Dynamic | Description | Prompt keyword |
|---|---|---|
| Instantaneous | < 100ms attack + immediate decay | "sharp", "instantaneous", "staccato" |
| Sustained | Long hold with gradual decay | "sustained", "drone" |
| Crescendo | Builds in intensity | "crescendo", "building" |
| Decrescendo | Fades from intensity | "fading", "decrescendo" |
| Pulse | Rhythmic repetition | "pulsing", "rhythmic" |

### Engine-specific prompt conventions

Different SFX engines respond to different prompt conventions. Per [`../../_shared/known-external-models.yaml`](../../_shared/known-external-models.yaml), the primary SFX engine family responds well to:

- **Detailed material + action**: critical
- **Environment descriptors**: moderate impact
- **Temporal dynamics**: high impact (distinguishes "shatter" from "sustained ring")
- **Style/music keywords**: low impact (SFX engines are not music engines)

### Negative prompt for SFX

Always include negative prompt to avoid common AI-SFX artifacts:

```
negative: "music, melody, song, vocals, speech, looping, repetitive,
          low quality, distorted, artifacted"
```

### Per-scene SFX density

Per [`../../_shared/cognitive-resonance-metrics.md`](../../_shared/cognitive-resonance-metrics.md) §Scale 1 (neural layer):

| Scene type | Recommended SFX count per 30s |
|---|---|
| Dialogue-focused | 1-3 (subtle ambient + occasional accent) |
| Action-focused | 5-10 (constant impacts + motion) |
| Emotional-quiet | 0-2 (silence is often more powerful) |
| Montage | 8-15 (layered with music) |

**Anti-pattern:** too many SFX = cognitive overload (per cognitive-resonance §Scale 1, active-suspension concurrency ≤ 3).

### Common SFX generation failures and fixes

| Failure | Cause | Fix |
|---|---|---|
| Sounds like music | Engine misinterprets prompt as music request | Add "non-musical" / "sound effect only" |
| Too short / abrupt | Default AI tendency | Add "sustained" + "with 500ms decay tail" |
| Looping artifact | Engine generates loopable sample | Add "one-shot" + "non-looping" |
| Wrong material | Vague source description | Specify exact material ("ceramic" not "hard") |
| Distorted / artifacted | Engine pushed past quality range | Reduce prompt specificity OR use higher-quality engine |

### Integration with screenplay emotion_curve

For each scene, the screenplay emits emotion_curve anchors (per [`../../screenplay/references/emotion-curve-academic.md`](../../screenplay/references/emotion-curve-academic.md)). Foley should map emotion transitions to SFX moments:

| Emotion transition | Foley cue |
|---|---|
| Calm → tense | Subtle low rumble building |
| Tense → release | Sudden silence OR gentle ambient restoration |
| Joy → grief | Major-key ambient removed, dissonant drone enters |
| Fear → shock | Sting (sudden loud SFX) at the shock moment |

### Per the cognitive-resonance-metrics alignment

Per [`../../_shared/cognitive-resonance-metrics.md`](../../_shared/cognitive-resonance-metrics.md):

- **Scale 1 (neural):** SFX must respect the 2.8-5s attribution window — major SFX moments should land within 5s of their visual trigger
- **Scale 2 (emotional):** SFX density should match sawtooth amplitude — fewer SFX during plateaus, more during peaks
- **Scale 1:** audio-visual binding < 120ms drift — SFX onset must align with visual event ±120ms

---

## Cross-references

- [`./stable-audio-open.md`](./stable-audio-open.md) — primary SFX engine specs
- [`./sound-effect-taxonomy.md`](./sound-effect-taxonomy.md) — BBC 21-category taxonomy
- [`../../screenplay/references/emotion-curve-academic.md`](../../screenplay/references/emotion-curve-academic.md) — emotion_curve source
- [`../../_shared/cognitive-resonance-metrics.md`](../../_shared/cognitive-resonance-metrics.md) §Scale 1 — neural-layer audio binding
- [`../../_shared/known-external-models.yaml`](../../_shared/known-external-models.yaml) — SFX engine placeholders
