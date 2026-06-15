# GAP-REPORT: colorist

**Audited:** 2026-06-15
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

## <phantoms>

None detected.

## <knowledge_gaps>

<!-- Topics the expert should know but SKILL.md doesn't cover -->

1. **Cross-cultural color meaning divergence (CN vs Western audiences).** SKILL.md color psychology is Western-leaning (red=danger, blue=cold). Chinese audience reads 红色=喜庆/吉利 for celebration, with danger being secondary meaning. No CN audience variant.
2. **Save the Cat / Bellantoni color-emotion references.** Research SUMMARY calls out *If It's Purple, Someone's Gonna Die* (Bellantoni) as a named source for color theory. Not cited anywhere.
3. **AI-grading pipeline reality.** Current pipeline assumes LUT params flow into drawer output frames, but FLUX 2 / gpt-image-2 image gen already bake color into generation. No guidance on pre-generation color prompting vs post-generation LUT grading.
4. **HDR / SDR dual-grade workflow.** No HDR handling despite current delivery targets (抖音 HDR-capable, Apple devices HDR-default).
5. **短剧 platform color drift.** Each platform (抖音 / 快手 / 视频号 / B站) re-encodes with different color space conversions. No per-platform grade compensation.
6. **CxSxZ system source citation.** "28 core combinations" claims a specific parametric system but no academic or industry source. Looks like an invented framework that needs either a citation or a renaming.

## <prompt_weak_points>

<!-- Vague instructions, missing thresholds, hand-wavy guidance -->

1. **"Emotional turns: gradual color temp/saturation transition (>= 2 seconds)"** — good threshold but no curve shape specified (linear? ease_in_out?).
2. **"Low saturation for repression/introspection"** — no numeric floor (S < 0.25? < 0.30?).
3. **`color_temp_precision: ±150K (production), ±300K (preview)`** — precision threshold given but no measurement tool named (waveform monitor? LLM-as-judge? CLIP-color?).
4. **`style_fidelity: >= 0.82`** — measured how? Against style_genome vector? No method defined.

## <stale_metrics>

<!-- metrics: [...] values that don't map to measurable behavior -->

- `color_intent_match` — production minimum >= 0.85. Match against what ground truth? The 28-combination table? Needs measurement protocol.
- `color_cross_shot_consistency` — >= 0.80. Histogram correlation is mentioned in parameters but not tied to this metric.
- `style_fidelity` — >= 0.82. No measurement method (CLIP-style embedding distance? LLM-judged? perceptual delta-E?).

## <missing_refs_topics>

<!-- Subjects that should become references/*.md in Phase 3/5 refactor -->

Research classification: **needs deep refs (4-6)** — top-4 priority expert per FEATURES.

1. `references/color-emotion-cn-vs-western.md` — cross-cultural color meaning table with CN audience variations (红色, 黄色, 紫色, 白色 divergence from Western reading).
2. `references/bellantoni-color-catalog.md` — distilled heuristics from *If It's Purple, Someone's Gonna Die* with citable rules.
3. `references/hurkman-look-book.md` — color correction patterns from *Color Correction Look Book* (Hurkman).
4. `references/cxsz-combination-atlas.md` — full 28-combination table with source citation (if academic) or rename to "v2 color intent system" if invented.
5. `references/platform-color-drift.md` — 抖音/快手/视频号/B站 re-encoding color space loss + compensation LUTs.
