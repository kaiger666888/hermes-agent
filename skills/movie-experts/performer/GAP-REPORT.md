# GAP-REPORT: performer

**Audited:** 2026-06-15
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

## <phantoms>

<!-- Model/tool/sampler/concept names not in plugins/ inventory or known-external-models.yaml -->

- `168k controlled tokens` at `skills/movie-experts/performer/SKILL.md:3` — description references "Performance-4D matrix (ExBxSxP) with 168K controlled tokens". **Disposition: STRIP** (fabricated concept — no real industry term matches; the ExBxSxP matrix is real, the "168K controlled tokens" count is invented). Research SUMMARY Gaps confirms: "Likely pure fabrication — strip in AUDIT-01. But verify it's not a typo for some real concept before deleting." Verified: not a typo. The matrix dimensions (E: 7×5=35, B: continuous, S: 6 zones, P: 4 precision levels) do not multiply to 168K by any plausible combinatorial interpretation. Strip entirely; replace with concrete ExBxSxP description.

**Cleanup target:** remove every "168K controlled tokens" / "168K controlled performance token" occurrence in description frontmatter, H1 subtitle, Role bullets, and any Key Parameters section. Replace with: "Performance-4D matrix (ExBxSxP) — parametric dispatch across Emotion, Body mechanics, Spatial staging, and Prompt engineering dimensions."

## <knowledge_gaps>

<!-- Topics the expert should know but SKILL.md doesn't cover -->

1. **Stanislavski / Method acting reference.** Research SUMMARY lists *An Actor Prepares* (Stanislavski) as named source. Not cited.
2. **短剧 acting intensity conventions.** 短剧 acting tends toward heightened emotion / 爽点 emphasis compared to arthouse micro-film. No 短剧-specific intensity calibration.
3. **Micro-expression generation in current image/video models.** Which current models (FLUX 2, veo3.1, kling-v3-4k) reliably render micro-expressions vs macro body language. SKILL.md assumes drawer/animator can execute any P4 prompt; reality differs.
4. **CN body-language conventions.** Gestures differ across cultures (CN head-bob for "no" vs Western shake; pointing with full hand vs finger). No CN body-language variant.
5. **Gender / age performance calibration.** E dimension has 7 emotion types × 5 intensities = 35 states, but no gender or age adjustment (a child's "angry 0.8" looks different from an adult's).

## <prompt_weak_points>

<!-- Vague instructions, missing thresholds, hand-wavy guidance -->

1. **"Performance is body language"** — principle, not checkable.
2. **"Every gesture needs intention"** — intention judged how? No schema for annotating intention per gesture.
3. **`emotion_accuracy: >= 0.85`** — accuracy vs what ground truth? screenplay.emotion_curve? Human-judged? Undefined.
4. **`movement_naturalness: >= 0.88`** — naturalness measured how? No protocol.
5. **`prompt_effectiveness: >= 0.80`** — effectiveness = downstream generation quality? Undefined measurement.

## <stale_metrics>

<!-- metrics: [...] values that don't map to measurable behavior -->

- `emotion_accuracy` — >= 0.85. No measurement protocol.
- `movement_naturalness` — >= 0.88. No measurement protocol.
- `body_consistency` — >= 0.90. Overlaps with continuity.face_similarity; no delegation.
- `prompt_effectiveness` — >= 0.80. No measurement.

## <missing_refs_topics>

<!-- Subjects that should become references/*.md in Phase 3/5 refactor -->

Research classification: **needs light-to-medium refs (2-4)**.

1. `references/stanislavski-an-actor-prepares.md` — distilled emotion-memory / given-circumstances techniques.
2. `references/disney-12-principles.md` — applied to live-action-adjacent AI character motion (exaggeration, staging, appeal).
3. `references/micro-expression-catalog.md` — Ekman / FACS-derived micro-expression catalog with timing (0.3-0.5s) and emotion mappings.
4. `references/cn-body-language-conventions.md` — CN-specific gesture / posture / head-movement conventions vs Western baseline.
