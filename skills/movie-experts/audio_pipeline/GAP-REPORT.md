# Audio Pipeline GAP-REPORT

**Consolidated:** 2026-06-17 (Phase 15 MERGE-02 — merged 5 predecessors + folded spatial_audio into `audio_pipeline`)
**Predecessors:** `voicer` (GAP-REPORT migrated), `lip_sync` (no GAP-REPORT — placeholder), `composer` (migrated), `foley` (migrated), `mixer` (migrated), `spatial_audio` (folded — migrated)
**Audit baseline:** eval-baseline-v1 (per-predecessor audit dated 2026-06-15)

This file consolidates the GAP-REPORT.md bodies of all 6 audio predecessors so Phase 18 (validate + docs) and any future gap-closure work has a single audit point for the unified `audio_pipeline` expert. Bodies are verbatim copies from the predecessor GAP-REPORT.md files (only the H1 of each predecessor was demoted to H2 to fit the consolidation structure).

## Voicer GAP-REPORT (migrated)

> Verbatim copy of `skills/movie-experts/voicer/GAP-REPORT.md` body (2026-06-15 audit).

**Audited:** 2026-06-15
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

### <phantoms>

None detected by scanner (CosyVoice model name is in `_shared/known-external-models.yaml` allowlist).

**Manual review note:** SKILL.md hardcodes `CosyVoice-300M (preview)` / `CosyVoice-300M-SFT` which are v1-era model IDs from 2024. Research SUMMARY §"What NOT to use": "CosyVoice-300M (preview) / CosyVoice-300M-SFT — v1 model IDs from 2024; latest is CosyVoice 3.0." These are not phantoms (CosyVoice is a real model family) but the version is STALE. Rewrite in Phase 5 to reference CosyVoice 3.0 (current SOTA) and MiniMax / ElevenLabs as Hermes-native alternatives.

### <knowledge_gaps>

<!-- Topics the expert should know but SKILL.md doesn't cover -->

1. **Hermes-native TTS alternatives.** Research SUMMARY: Hermes ships MiniMax, ElevenLabs, Mistral Voxtral, Gemini, Edge, NeuTTS. SKILL.md only covers CosyVoice (user-deployed external). No Hermes-native TTS selection guidance.
2. **CosyVoice deployment path.** CosyVoice 3.0 requires local deployment outside Hermes. No deployment doc reference (research SUMMARY: "document in voicer/references/cosyvoice-deployment.md").
3. **CN 短剧 voice acting conventions.** 短剧 voice acting is heightened / dramatized compared to naturalistic film. No 短剧-specific emotion_strength calibration.
4. **Multi-character voice consistency across episodes.** 短剧 spans 10-80 episodes; character voice must remain stable. No multi-episode voice profile persistence protocol.
5. **Dialect / regional accent support.** CN 短剧 often uses regional dialects (东北话, 四川话, 粤语). No dialect handling guidance.

### <prompt_weak_points>

<!-- Vague instructions, missing thresholds, hand-wavy guidance -->

1. **"Voice is character"** — principle, not checkable.
2. **`voice_naturalness: >= 0.90`** — high threshold, no measurement protocol (MOS? human-judged? neural MOS predictor?).
3. **`emotion_match: >= 0.85`** — match vs screenplay.emotion_curve? Undefined.
4. **`character_distinctiveness: >= 0.80`** — distinctiveness measured across how many characters? Undefined baseline.
5. **`speaker_embedding: character-specific vector (3-5 reference samples)`** — no guidance on optimal sample selection (emotion diversity, recording quality, duration distribution).

### <stale_metrics>

<!-- metrics: [...] values that don't map to measurable behavior -->

- `voice_naturalness` — >= 0.90. No measurement protocol.
- `emotion_match` — >= 0.85. No measurement protocol.
- `character_distinctiveness` — >= 0.80. No measurement protocol.
- `prosody_naturalness` — >= 0.85. No measurement protocol (note: this metric is in Quality Thresholds table but NOT in frontmatter `metrics:` list — inconsistency).

### <missing_refs_topics>

<!-- Subjects that should become references/*.md in Phase 3/5 refactor -->

Research classification: **needs light-to-medium refs (2-4)**.

1. `references/cosyvoice-deployment.md` — CosyVoice 3.0 local deployment guide, API surface, GPU requirements, Docker setup.
2. `references/hermes-tts-selection-matrix.md` — MiniMax vs ElevenLabs vs CosyVoice vs Voxtral vs Gemini vs Edge vs NeuTTS selection by use case (CN emotion, voice cloning, multilingual).
3. `references/cn-shortdrama-voice-conventions.md` — 短剧 voice acting intensity conventions, emotion_strength calibration by genre.
4. `references/dialect-and-accent-support.md` — CN regional dialect TTS capability matrix per provider.

## Lip Sync GAP-REPORT (migrated)

**Note:** The `lip_sync` predecessor has no `GAP-REPORT.md` (only `_eval/prompts/` regression suite under `skills/movie-experts/lip_sync/_eval/`). No gaps recorded at v1 baseline audit; the lip_sync SKILL.md is the only movie-expert with an international-standard benchmark (LRS2/LRS3) and objective metrics (LSE/LSE-C via SyncNet), so its validation surface is uniquely well-defined. Phase 18 validate work may consolidate a fresh GAP-REPORT for the `audio_pipeline` lip_sync sub-step from the benchmark regression output.

## Composer GAP-REPORT (migrated)

> Verbatim copy of `skills/movie-experts/composer/GAP-REPORT.md` body (2026-06-15 audit).

**Audited:** 2026-06-15
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

### <phantoms>

None detected.

### <knowledge_gaps>

<!-- Topics the expert should know but SKILL.md doesn't cover -->

1. **Current music gen model capabilities.** SKILL.md hardcodes MusicGen-large but doesn't acknowledge its stability ("not actively developed" per research SUMMARY). No fallback model documented (MusicGen is mature but frozen).
2. **短剧 BGM-driven hook sync.** Research SUMMARY calls out "BGM-driven hook sync with `composer.coupled_beat`" as a key EXPERT-HOOK requirement. composer has no hook-aware beat design pattern.
3. **CN-specific musical conventions.** No CN audience conventions for major/minor emotional mapping, instrument choices (古筝 / 二胡 / 笛子 for specific emotions), or 短剧 genre music signatures.
4. **Adaptive / layered scoring for interactive 短剧.** Future 小程序剧 may branch based on viewer choice. No layer-stem design pattern.
5. **Stem separation for downstream re-mixing.** No protocol for exporting separable stems (melody / bass / percussion / pads) vs a single combined music stem.

### <prompt_weak_points>

<!-- Vague instructions, missing thresholds, hand-wavy guidance -->

1. **"Silence is a powerful instrument — use it deliberately"** — vague principle. No operational threshold (min seconds of silence per scene? when is silence mandatory?).
2. **`coupling_strength: 0.3 (loose) to 0.8 (tight)`** — no guidance on scene-type to coupling-strength mapping (action = tight? emotional = loose?).
3. **`frequency_avoidance: 2000-5000 Hz zone (dialogue territory)`** — repeated across foley/mixer/voicer but no EQ curve template or sidechain ducking reference.
4. **`emotional_sync: >= 0.85`** — no measurement definition.
5. **Genre guidelines are shallow.** "Drama: strings + piano" is generic. No instrumentation specificity for subgenres (melodrama vs tragedy vs family drama).

### <stale_metrics>

<!-- metrics: [...] values that don't map to measurable behavior -->

- `emotional_sync` — production minimum >= 0.85. No measurement protocol (LLM-judged? correlation with screenplay.emotion_curve?).
- `spatial_coherence` — >= 0.80. What spatial coherence means for a mono/stereo music stem is unclear; this may belong to spatial_audio.
- `dynamic_range` — listed as 8-14 LU (EBU R128), which IS measurable. This one is OK.

### <missing_refs_topics>

<!-- Subjects that should become references/*.md in Phase 3/5 refactor -->

Research classification: **needs light-to-medium refs (2-4)**.

1. `references/musicgen-capabilities-and-limits.md` — what MusicGen-large can/cannot do as of 2026-06, recommended alternatives if quality regresses (Stable Audio Pro, Suno v4 as commercial fallbacks).
2. `references/cn-musical-conventions.md` — instrument-to-emotion mapping for CN audiences, 古筝/二胡/笛子 signatures, pentatonic vs diatonic emotional weight.
3. `references/shortdrama-hook-sync.md` — BGM-driven hook pattern (3-second intro hook, 爽点 drop alignment, 付费卡点 musical sting).
4. `references/frequency-allocation-atlas.md` — concrete EQ carve curves for music-foley-dialogue coexistence, sidechain templates.

## Foley GAP-REPORT (migrated)

> Verbatim copy of `skills/movie-experts/foley/GAP-REPORT.md` body (2026-06-15 audit).

**Audited:** 2026-06-15
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

### <phantoms>

<!-- Model/tool/sampler/concept names not in plugins/ inventory or known-external-models.yaml -->

- `synthesis_model` at `skills/movie-experts/foley/SKILL.md:48` — `synthesis_model: AudioLDM-2 (primary), AudioGen (fallback)`. The token `synthesis_model` matches the scanner's suffix regex (`_model`). **Disposition: ALLOWLIST** the suffix token AND the specific model names. `AudioLDM-2` is real (research-era, superseded) and `AudioGen` is real (Meta AudioCraft). However per research SUMMARY §"What NOT to use": `AudioLDM-2` is "research-era, superseded by Stable Audio Open". So the token is a real model name but the recommendation is STALE — should be rewritten to `stable_audio_open` (already in allowlist). Rewrite in Phase 5.

**Cleanup target:** Add `synthesis_model`, `audioldm-2`, `audiogen` to allowlist as legitimate legacy model names. Rewrite SKILL.md body to recommend `stable_audio_open` (current default per research) with `AudioLDM-2` / `AudioGen` as legacy fallbacks.

### <knowledge_gaps>

<!-- Topics the expert should know but SKILL.md doesn't cover -->

1. **Current SOTA foley/SFX model.** Research SUMMARY: Stable Audio Open 1.0 is the current open-source default (47s @ 44.1kHz). Stable-Foley (arXiv:2412.15023) for video-synced foley. SKILL.md hardcodes AudioLDM-2 which is research-era.
2. **Video-synced foley pipeline.** Stable-Foley and similar models take video frames as input for sync. SKILL.md assumes text-to-audio only.
3. **CN-specific material sounds.** Some materials have culturally specific sounds (古筝 strings, 瓷器 porcelain, 丝绸 silk friction). No CN material acoustic signature additions.
4. **Layered foley for complex interactions.** SKILL.md treats each "physical interaction" as one stem, but real foley often layers (footstep on wood + fabric rustle + breath). No layering protocol.
5. **Foley library vs synthesized hybrid workflow.** No guidance on when to use library samples (high realism) vs synthesized (full control).

### <prompt_weak_points>

<!-- Vague instructions, missing thresholds, hand-wavy guidance -->

1. **"Sound makes the image real"** — principle, not checkable.
2. **"Every physical interaction in frame deserves its acoustic fingerprint"** — strong principle but no priority ranking (which interactions are critical vs which can be backgrounded?).
3. **`material_credibility: >= 0.85`** — credibility measured how? Human-judged? CLAP-audio? Perceptual model? Undefined.
4. **`force_consistency: >= 0.80`** — consistency across what? Same material-action across shots? No protocol.
5. **`spectral_clarity: >= 0.82`** — undefined measurement.

### <stale_metrics>

<!-- metrics: [...] values that don't map to measurable behavior -->

- `material_credibility` — >= 0.85. No measurement protocol.
- `impact_sync_accuracy` — >= 0.90. Measurable (frame-alignment variance) but method not stated.
- `force_consistency` — >= 0.80. No measurement.
- `spectral_clarity` — >= 0.82. No measurement.

### <missing_refs_topics>

<!-- Subjects that should become references/*.md in Phase 3/5 refactor -->

Research classification: **needs light-to-medium refs (2-4)**.

1. `references/stable-audio-open-guide.md` — Stable Audio Open 1.0 capabilities, prompt patterns, 47s duration limit, extension via concatenation.
2. `references/viers-sound-effects-bible.md` — distilled from *The Sound Effects Bible* (Viers) — material-action-force heuristics.
3. `references/chion-audio-vision.md` — distilled from *Audio-Vision* (Chion) — audio-visual synchronization theory.
4. `references/cn-material-acoustic-signatures.md` — CN-specific materials (瓷器, 丝绸, 古筝 strings, 竹木) acoustic signatures.

## Mixer GAP-REPORT (migrated)

> Verbatim copy of `skills/movie-experts/mixer/GAP-REPORT.md` body (2026-06-15 audit).

**Audited:** 2026-06-15
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

### <phantoms>

None detected.

### <knowledge_gaps>

<!-- Topics the expert should know but SKILL.md doesn't cover -->

1. **Platform-specific loudness targets.** 抖音 / 快手 / 视频号 / B站 each have different normalization curves (抖音 boosts to -14 LUFS on upload, others differ). SKILL.md gives generic `-16.0 ± 1.0` stereo target. No per-platform table.
2. **Mobile-device playback compensation.** 短剧 consumed primarily on phones with small speakers + earbuds. No frequency compensation for phone speaker LF roll-off or earbuds bass-boost.
3. **CN 短剧 BGM ducking conventions.** CN 短剧 tends to run louder BGM-to-dialogue ratio than Western film (emotional emphasis). No CN-specific duck depth guidance.
4. **Adaptive mixing for interactive 短剧.** No protocol for branching audio mix tied to interactive 小程序剧 choices.
5. **Subtitle / caption audio cue layer.** CN 短剧 relies heavily on subtitles; no audio cue pattern for subtitle appearance/emphasis.

### <prompt_weak_points>

<!-- Vague instructions, missing thresholds, hand-wavy guidance -->

1. **"Mixing is about hierarchy"** — principle stated, hierarchy quantified (4-layer), but no fail-check for hierarchy violations beyond "Dialogue masked" (zero tolerance). Intermediate violations (e.g., music 1dB louder than dialogue in MF band) not enumerated.
2. **`frequency_masking_score: >= 0.85`** — no measurement definition.
3. **`dialogue_intelligibility: >= 0.92`** — high threshold but no measurement (STOI? PESQ? human-judged?).
4. **`dynamic_range_appropriateness: >= 0.85`** — "appropriateness" is subjective even with the 8-14 LU target.
5. **Ducking `hold_time: 100-200ms after dialogue ends`** — good, but no rule for when music should ramp back up if next dialogue is < hold_time away (duck oscillation problem).

### <stale_metrics>

<!-- metrics: [...] values that don't map to measurable behavior -->

- `level_compliance` — >= 0.88. Compliance with what target? LUFS? True peak? Both? No protocol.
- `frequency_masking_score` — >= 0.85. No measurement.
- `dialogue_intelligibility` — >= 0.92. No measurement protocol.
- `dynamic_range_appropriateness` — >= 0.85. Subjective.

### <missing_refs_topics>

<!-- Subjects that should become references/*.md in Phase 3/5 refactor -->

Research classification: **needs light-to-medium refs (2-4)**.

1. `references/senior-mixing-secrets.md` — distilled from *Mixing Secrets for the Small Studio* (Senior) — EQ carve curves, compression recipes.
2. `references/platform-loudness-targets.md` — 抖音 / 快手 / 视频号 / B站 per-platform upload normalization, LUFS targets, re-encoding loss.
3. `references/mobile-playback-compensation.md` — phone speaker and earbud frequency compensation curves, LF roll-off handling.
4. `references/cn-shortdrama-ducking-conventions.md` — CN 短剧 BGM-to-dialogue ratio conventions, emotional-emphasis duck depth patterns.

## Spatial Audio GAP-REPORT (migrated)

> Verbatim copy of `skills/movie-experts/spatial_audio/GAP-REPORT.md` body (2026-06-15 audit). **Folded into audio_pipeline per disposition D-1** — the spatial_audio sub-step retains its unique technical surface (HRTF tables, Atmos metadata, 5 immersive sound patterns) inside the merged expert.

**Audited:** 2026-06-15
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

### <phantoms>

None detected.

### <knowledge_gaps>

<!-- Topics the expert should know but SKILL.md doesn't cover -->

1. **Mobile-device spatial rendering.** 短剧 consumed on phones; 5.1 / 7.1 surround is irrelevant for phone playback. No binaural / HRTF rendering protocol for mobile delivery.
2. **Dolby Atmos for 短剧.** tags include `dolby-atmos` but no Atmos-specific object-based audio workflow documented.
3. **CN-specific environmental ambience signatures.** CN environments (ktv, 出租屋, 地铁, 街头小吃摊) have characteristic ambient signatures not covered by generic "indoor / outdoor" presets.
4. **Adaptive spatial audio for interactive 短剧.** No protocol for listener-position-dependent spatial audio (viewer-rotates-phone for 360° 短剧).
5. **Acoustic modeling integration with scene_builder.** scene_builder emits `material_annotations.json` with surface roughness; spatial_audio needs acoustic reflection coefficients. No conversion protocol.

### <prompt_weak_points>

<!-- Vague instructions, missing thresholds, hand-wavy guidance -->

1. **"Sound has position"** — principle, not checkable.
2. **`spatial_coherence: >= 0.85`** — no measurement protocol.
3. **`reality_anchor_stability: >= 0.80`** — stability over time? Across shots? Undefined.
4. **`distance_transition_smoothness: >= 0.88`** — measured how?
5. **`vacuum_detection_pass: >= 0.90`** — "pass" is binary; what does 0.90 mean?

### <stale_metrics>

<!-- metrics: [...] values that don't map to measurable behavior -->

- `spatial_coherence` — >= 0.85. No measurement protocol.
- `reality_anchor_stability` — >= 0.80. No measurement protocol.
- `distance_transition_smoothness` — >= 0.88. No measurement protocol.
- `vacuum_detection_pass` — >= 0.90. Binary concept with continuous threshold — contradictory.

### <missing_refs_topics>

<!-- Subjects that should become references/*.md in Phase 3/5 refactor -->

Research classification: **needs light-to-medium refs (2-4)**.

1. `references/mobile-binaural-rendering.md` — HRTF / binaural rendering for phone playback, earbuds compensation.
2. `references/cn-environmental-ambience.md` — CN-specific environment ambience presets (ktv, 出租屋, 地铁, 街头).
3. `references/material-to-acoustic-conversion.md` — scene_builder material_annotations → acoustic reflection coefficients protocol.
4. `references/dolby-atmos-object-workflow.md` — Atmos object-based audio authoring for 短剧 delivery.
