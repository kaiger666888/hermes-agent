# GAP-REPORT: foley

**Audited:** 2026-06-15
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

## <phantoms>

<!-- Model/tool/sampler/concept names not in plugins/ inventory or known-external-models.yaml -->

- `synthesis_model` at `skills/movie-experts/foley/SKILL.md:48` — `synthesis_model: AudioLDM-2 (primary), AudioGen (fallback)`. The token `synthesis_model` matches the scanner's suffix regex (`_model`). **Disposition: ALLOWLIST** the suffix token AND the specific model names. `AudioLDM-2` is real (research-era, superseded) and `AudioGen` is real (Meta AudioCraft). However per research SUMMARY §"What NOT to use": `AudioLDM-2` is "research-era, superseded by Stable Audio Open". So the token is a real model name but the recommendation is STALE — should be rewritten to `stable_audio_open` (already in allowlist). Rewrite in Phase 5.

**Cleanup target:** Add `synthesis_model`, `audioldm-2`, `audiogen` to allowlist as legitimate legacy model names. Rewrite SKILL.md body to recommend `stable_audio_open` (current default per research) with `AudioLDM-2` / `AudioGen` as legacy fallbacks.

## <knowledge_gaps>

<!-- Topics the expert should know but SKILL.md doesn't cover -->

1. **Current SOTA foley/SFX model.** Research SUMMARY: Stable Audio Open 1.0 is the current open-source default (47s @ 44.1kHz). Stable-Foley (arXiv:2412.15023) for video-synced foley. SKILL.md hardcodes AudioLDM-2 which is research-era.
2. **Video-synced foley pipeline.** Stable-Foley and similar models take video frames as input for sync. SKILL.md assumes text-to-audio only.
3. **CN-specific material sounds.** Some materials have culturally specific sounds (古筝 strings, 瓷器 porcelain, 丝绸 silk friction). No CN material acoustic signature additions.
4. **Layered foley for complex interactions.** SKILL.md treats each "physical interaction" as one stem, but real foley often layers (footstep on wood + fabric rustle + breath). No layering protocol.
5. **Foley library vs synthesized hybrid workflow.** No guidance on when to use library samples (high realism) vs synthesized (full control).

## <prompt_weak_points>

<!-- Vague instructions, missing thresholds, hand-wavy guidance -->

1. **"Sound makes the image real"** — principle, not checkable.
2. **"Every physical interaction in frame deserves its acoustic fingerprint"** — strong principle but no priority ranking (which interactions are critical vs which can be backgrounded?).
3. **`material_credibility: >= 0.85`** — credibility measured how? Human-judged? CLAP-audio? Perceptual model? Undefined.
4. **`force_consistency: >= 0.80`** — consistency across what? Same material-action across shots? No protocol.
5. **`spectral_clarity: >= 0.82`** — undefined measurement.

## <stale_metrics>

<!-- metrics: [...] values that don't map to measurable behavior -->

- `material_credibility` — >= 0.85. No measurement protocol.
- `impact_sync_accuracy` — >= 0.90. Measurable (frame-alignment variance) but method not stated.
- `force_consistency` — >= 0.80. No measurement.
- `spectral_clarity` — >= 0.82. No measurement.

## <missing_refs_topics>

<!-- Subjects that should become references/*.md in Phase 3/5 refactor -->

Research classification: **needs light-to-medium refs (2-4)**.

1. `references/stable-audio-open-guide.md` — Stable Audio Open 1.0 capabilities, prompt patterns, 47s duration limit, extension via concatenation.
2. `references/viers-sound-effects-bible.md` — distilled from *The Sound Effects Bible* (Viers) — material-action-force heuristics.
3. `references/chion-audio-vision.md` — distilled from *Audio-Vision* (Chion) — audio-visual synchronization theory.
4. `references/cn-material-acoustic-signatures.md` — CN-specific materials (瓷器, 丝绸, 古筝 strings, 竹木) acoustic signatures.
