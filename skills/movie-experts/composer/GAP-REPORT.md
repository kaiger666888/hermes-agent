# GAP-REPORT: composer

**Audited:** 2026-06-15
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

## <phantoms>

None detected.

## <knowledge_gaps>

<!-- Topics the expert should know but SKILL.md doesn't cover -->

1. **Current music gen model capabilities.** SKILL.md hardcodes MusicGen-large but doesn't acknowledge its stability ("not actively developed" per research SUMMARY). No fallback model documented (MusicGen is mature but frozen).
2. **短剧 BGM-driven hook sync.** Research SUMMARY calls out "BGM-driven hook sync with `composer.coupled_beat`" as a key EXPERT-HOOK requirement. composer has no hook-aware beat design pattern.
3. **CN-specific musical conventions.** No CN audience conventions for major/minor emotional mapping, instrument choices (古筝 / 二胡 / 笛子 for specific emotions), or 短剧 genre music signatures.
4. **Adaptive / layered scoring for interactive 短剧.** Future 小程序剧 may branch based on viewer choice. No layer-stem design pattern.
5. **Stem separation for downstream re-mixing.** No protocol for exporting separable stems (melody / bass / percussion / pads) vs a single combined music stem.

## <prompt_weak_points>

<!-- Vague instructions, missing thresholds, hand-wavy guidance -->

1. **"Silence is a powerful instrument — use it deliberately"** — vague principle. No operational threshold (min seconds of silence per scene? when is silence mandatory?).
2. **`coupling_strength: 0.3 (loose) to 0.8 (tight)`** — no guidance on scene-type to coupling-strength mapping (action = tight? emotional = loose?).
3. **`frequency_avoidance: 2000-5000 Hz zone (dialogue territory)`** — repeated across foley/mixer/voicer but no EQ curve template or sidechain ducking reference.
4. **`emotional_sync: >= 0.85`** — no measurement definition.
5. **Genre guidelines are shallow.** "Drama: strings + piano" is generic. No instrumentation specificity for subgenres (melodrama vs tragedy vs family drama).

## <stale_metrics>

<!-- metrics: [...] values that don't map to measurable behavior -->

- `emotional_sync` — production minimum >= 0.85. No measurement protocol (LLM-judged? correlation with screenplay.emotion_curve?).
- `spatial_coherence` — >= 0.80. What spatial coherence means for a mono/stereo music stem is unclear; this may belong to spatial_audio.
- `dynamic_range` — listed as 8-14 LU (EBU R128), which IS measurable. This one is OK.

## <missing_refs_topics>

<!-- Subjects that should become references/*.md in Phase 3/5 refactor -->

Research classification: **needs light-to-medium refs (2-4)**.

1. `references/musicgen-capabilities-and-limits.md` — what MusicGen-large can/cannot do as of 2026-06, recommended alternatives if quality regresses (Stable Audio Pro, Suno v4 as commercial fallbacks).
2. `references/cn-musical-conventions.md` — instrument-to-emotion mapping for CN audiences, 古筝/二胡/笛子 signatures, pentatonic vs diatonic emotional weight.
3. `references/shortdrama-hook-sync.md` — BGM-driven hook pattern (3-second intro hook, 爽点 drop alignment, 付费卡点 musical sting).
4. `references/frequency-allocation-atlas.md` — concrete EQ carve curves for music-foley-dialogue coexistence, sidechain templates.
