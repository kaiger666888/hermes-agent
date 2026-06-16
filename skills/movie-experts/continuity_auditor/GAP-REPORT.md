# GAP-REPORT: continuity

**Audited:** 2026-06-15
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

## <phantoms>

None detected.

## <knowledge_gaps>

<!-- Topics the expert should know but SKILL.md doesn't cover -->

1. **Scene-graph / object-tracking protocol.** SKILL.md mentions "Environmental continuity tracking (props, lighting, weather, time-of-day)" but no structured object-graph schema. How is a "prop appearance/disappearance" detected algorithmically?
2. **Wardrobe continuity across 短剧 episode boundaries.** 短剧 often spans 10+ episodes with the same characters. No multi-episode wardrobe tracking pattern.
3. **ArcFace / InsightFace model version drift.** SKILL.md references "ArcFace / InsightFace (512-dim embedding)" without version pin. Face-recognition models drift; baseline embeddings captured with one model are incomparable to embeddings from a different version.
4. **Cross-expert correction feedback loop.** SKILL outputs `correction_prompt` but no structured schema that drawer/animator can consume programmatically. Currently free-text.
5. **短剧 vertical-screen continuity specifics.** Vertical framing crops differently than horizontal; eye-line match tolerances may differ. No 9:16-specific continuity rules.

## <prompt_weak_points>

<!-- Vague instructions, missing thresholds, hand-wavy guidance -->

1. **`face_similarity: >= 0.88`** — strong threshold but no guidance on edge cases (glasses on/off, profile vs frontal, lighting change of >500K).
2. **"No unexplained prop appearance/disappearance"** — "unexplained" is subjective. No rule for what counts as explained (narrative annotation? scene_builder tag?).
3. **`render_consistency: CLIP score >= 0.92`** — high threshold. CLIP score varies by CLIP model version. No model pin.
4. **"Don't flag narrative-justified changes"** — who decides "justified"? Needs screenplay.annotated_justifications schema.
5. **Weight allocation** (Character 0.40, Clothing 0.25, Color 0.20, Environment 0.15) — no sensitivity analysis. Are these weights empirically derived?

## <stale_metrics>

<!-- metrics: [...] values that don't map to measurable behavior -->

- `face_similarity` — >= 0.88. Measurable via cosine similarity on ArcFace embeddings, but model version not pinned.
- `color_consistency` — >= 0.85. Measurement protocol undefined (histogram correlation? delta-E? CLIP-color?).
- `style_uniformity` — >= 0.85. Measurement undefined (L2 distance from style_genome 5D vector? CLIP score?).

## <missing_refs_topics>

<!-- Subjects that should become references/*.md in Phase 3/5 refactor -->

Research classification: **needs light-to-medium refs (2-4)**.

1. `references/face-model-versioning.md` — ArcFace/InsightFace version pinning, embedding migration protocol when models upgrade.
2. `references/object-graph-schema.md` — structured per-scene object/prop/wardrobe tracking schema with timestamps.
3. `references/vertical-screen-continuity.md` — 9:16 framing crop rules, eye-line tolerances, safe-zone continuity.
4. `references/correction-prompt-schema.md` — machine-readable correction output schema for drawer/animator consumption.
