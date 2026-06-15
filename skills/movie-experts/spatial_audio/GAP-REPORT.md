# GAP-REPORT: spatial_audio

**Audited:** 2026-06-15
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

## <phantoms>

None detected.

## <knowledge_gaps>

<!-- Topics the expert should know but SKILL.md doesn't cover -->

1. **Mobile-device spatial rendering.** 短剧 consumed on phones; 5.1 / 7.1 surround is irrelevant for phone playback. No binaural / HRTF rendering protocol for mobile delivery.
2. **Dolby Atmos for 短剧.** tags include `dolby-atmos` but no Atmos-specific object-based audio workflow documented.
3. **CN-specific environmental ambience signatures.** CN environments (ktv, 出租屋, 地铁, 街头小吃摊) have characteristic ambient signatures not covered by generic "indoor / outdoor" presets.
4. **Adaptive spatial audio for interactive 短剧.** No protocol for listener-position-dependent spatial audio (viewer-rotates-phone for 360° 短剧).
5. **Acoustic modeling integration with scene_builder.** scene_builder emits `material_annotations.json` with surface roughness; spatial_audio needs acoustic reflection coefficients. No conversion protocol.

## <prompt_weak_points>

<!-- Vague instructions, missing thresholds, hand-wavy guidance -->

1. **"Sound has position"** — principle, not checkable.
2. **`spatial_coherence: >= 0.85`** — no measurement protocol.
3. **`reality_anchor_stability: >= 0.80`** — stability over time? Across shots? Undefined.
4. **`distance_transition_smoothness: >= 0.88`** — measured how?
5. **`vacuum_detection_pass: >= 0.90`** — "pass" is binary; what does 0.90 mean?

## <stale_metrics>

<!-- metrics: [...] values that don't map to measurable behavior -->

- `spatial_coherence` — >= 0.85. No measurement protocol.
- `reality_anchor_stability` — >= 0.80. No measurement protocol.
- `distance_transition_smoothness` — >= 0.88. No measurement protocol.
- `vacuum_detection_pass` — >= 0.90. Binary concept with continuous threshold — contradictory.

## <missing_refs_topics>

<!-- Subjects that should become references/*.md in Phase 3/5 refactor -->

Research classification: **needs light-to-medium refs (2-4)**.

1. `references/mobile-binaural-rendering.md` — HRTF / binaural rendering for phone playback, earbuds compensation.
2. `references/cn-environmental-ambience.md` — CN-specific environment ambience presets (ktv, 出租屋, 地铁, 街头).
3. `references/material-to-acoustic-conversion.md` — scene_builder material_annotations → acoustic reflection coefficients protocol.
4. `references/dolby-atmos-object-workflow.md` — Atmos object-based audio authoring for 短剧 delivery.
