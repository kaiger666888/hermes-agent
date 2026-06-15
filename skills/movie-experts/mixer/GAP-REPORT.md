# GAP-REPORT: mixer

**Audited:** 2026-06-15
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

## <phantoms>

None detected.

## <knowledge_gaps>

<!-- Topics the expert should know but SKILL.md doesn't cover -->

1. **Platform-specific loudness targets.** 抖音 / 快手 / 视频号 / B站 each have different normalization curves (抖音 boosts to -14 LUFS on upload, others differ). SKILL.md gives generic `-16.0 ± 1.0` stereo target. No per-platform table.
2. **Mobile-device playback compensation.** 短剧 consumed primarily on phones with small speakers + earbuds. No frequency compensation for phone speaker LF roll-off or earbuds bass-boost.
3. **CN 短剧 BGM ducking conventions.** CN 短剧 tends to run louder BGM-to-dialogue ratio than Western film (emotional emphasis). No CN-specific duck depth guidance.
4. **Adaptive mixing for interactive 短剧.** No protocol for branching audio mix tied to interactive 小程序剧 choices.
5. **Subtitle / caption audio cue layer.** CN 短剧 relies heavily on subtitles; no audio cue pattern for subtitle appearance/emphasis.

## <prompt_weak_points>

<!-- Vague instructions, missing thresholds, hand-wavy guidance -->

1. **"Mixing is about hierarchy"** — principle stated, hierarchy quantified (4-layer), but no fail-check for hierarchy violations beyond "Dialogue masked" (zero tolerance). Intermediate violations (e.g., music 1dB louder than dialogue in MF band) not enumerated.
2. **`frequency_masking_score: >= 0.85`** — no measurement definition.
3. **`dialogue_intelligibility: >= 0.92`** — high threshold but no measurement (STOI? PESQ? human-judged?).
4. **`dynamic_range_appropriateness: >= 0.85`** — "appropriateness" is subjective even with the 8-14 LU target.
5. **Ducking `hold_time: 100-200ms after dialogue ends`** — good, but no rule for when music should ramp back up if next dialogue is < hold_time away (duck oscillation problem).

## <stale_metrics>

<!-- metrics: [...] values that don't map to measurable behavior -->

- `level_compliance` — >= 0.88. Compliance with what target? LUFS? True peak? Both? No protocol.
- `frequency_masking_score` — >= 0.85. No measurement.
- `dialogue_intelligibility` — >= 0.92. No measurement protocol.
- `dynamic_range_appropriateness` — >= 0.85. Subjective.

## <missing_refs_topics>

<!-- Subjects that should become references/*.md in Phase 3/5 refactor -->

Research classification: **needs light-to-medium refs (2-4)**.

1. `references/senior-mixing-secrets.md` — distilled from *Mixing Secrets for the Small Studio* (Senior) — EQ carve curves, compression recipes.
2. `references/platform-loudness-targets.md` — 抖音 / 快手 / 视频号 / B站 per-platform upload normalization, LUFS targets, re-encoding loss.
3. `references/mobile-playback-compensation.md` — phone speaker and earbud frequency compensation curves, LF roll-off handling.
4. `references/cn-shortdrama-ducking-conventions.md` — CN 短剧 BGM-to-dialogue ratio conventions, emotional-emphasis duck depth patterns.
