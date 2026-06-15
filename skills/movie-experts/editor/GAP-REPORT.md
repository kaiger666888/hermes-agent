# GAP-REPORT: editor

**Audited:** 2026-06-15
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

## <phantoms>

None detected.

## <knowledge_gaps>

<!-- Topics the expert should know but SKILL.md doesn't cover -->

1. **短剧 cut density scaling.** Research SUMMARY: vertical 短剧 typically 1.5-2x horizontal cinema cut density. No scaling factor in `cuts_per_second` parameters (action: 0.8-1.2 — but is that for horizontal or vertical?).
2. **Murch Rule of Six.** Research SUMMARY calls out *In the Blink of an Eye* (Murch) as named source. Not cited. Rule of Six (emotion > story > rhythm > eye-trace > 2D plane > 3D space) absent.
3. **No >3s dead air rule for 短剧.** Research HOOK requirements mandate no >3s dead air (完播率 optimization). No such rule here.
4. **Vertical-screen eye-line matching.** `eye_line_match: ±5°` — but vertical framing changes the perceptual tolerance. No 9:16 variant.
5. **Platform-specific aspect-ratio delivery.** 抖音 9:16, B站 16:9, 视频号 6:7 hybrid. No multi-aspect delivery protocol.
6. **Match-cut design catalog.** Research SUMMARY lists "match-cut design" as EXPERT-CINE table-stakes. Editor should consume but doesn't define match-cut recognition patterns.

## <prompt_weak_points>

<!-- Vague instructions, missing thresholds, hand-wavy guidance -->

1. **"Editing is invisible when done right"** — principle, not a checkable rule.
2. **`axis_violation_count: = 0`** — good (zero tolerance) but no definition of how axis is computed from shot metadata.
3. **`beat_alignment: ±100ms (with composer's coupled_beat)`** — good threshold. But "severely out of sync" in Prohibited has no numeric bound.
4. **"Unmotivated jump cuts (unless stylized)"** — "unmotivated" and "stylized" are subjective.
5. **`transition_smoothness: >= 0.88`** — no measurement protocol.

## <stale_metrics>

<!-- metrics: [...] values that don't map to measurable behavior -->

- `rhythm_accuracy` — >= 0.85. Accuracy of what vs what? Beat alignment variance? Not defined.
- `continuity_match` — >= 0.80. Overlaps with continuity expert's metrics. Delegation unclear.
- `transition_smoothness` — >= 0.88. No measurement (perceptual? optical-flow-based?).
- `axis_violation_count` — measurable (count), this one is OK.

## <missing_refs_topics>

<!-- Subjects that should become references/*.md in Phase 3/5 refactor -->

Research classification: **needs deep refs (4-6)** — top-4 priority expert per FEATURES.

1. `references/murch-rule-of-six.md` — distilled from *In the Blink of an Eye*, with citable priority hierarchy.
2. `references/fxrxt-axis-compliance.md` — FxRxT matrix axis compliance rules with neutral-shot transition patterns.
3. `references/shortdrama-cut-density.md` — empirical 1.5-2x scaling rule, shot duration floors by scene type for vertical 短剧.
4. `references/reisz-millar-technique.md` — distilled from *The Technique of Film Editing*.
5. `references/match-cut-recognition.md` — visual / audio / motion match-cut detection patterns for editor consumption.
6. `references/no-dead-air-rule.md` — 3-second dead air ceiling for 短剧, recovery patterns.
