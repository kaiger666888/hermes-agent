# GAP-REPORT: scene_builder

**Audited:** 2026-06-15
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

## <phantoms>

None detected.

## <knowledge_gaps>

<!-- Topics the expert should know but SKILL.md doesn't cover -->

1. **EXPERT-CINE boundary.** Research SUMMARY: EXPERT-CINE owns 镜头语言 (semantics); scene_builder owns 空间布局 (geometry); animator owns 动态执行 (motion); editor owns 180° axis compliance. SKILL.md currently mixes camera blocking (CINE boundary) with scene layout. Boundary must be documented BEFORE EXPERT-CINE is written in Phase 4.
2. **Blender version / addon compatibility.** No version pin for Blender or required addons. Asset library compatibility drifts across Blender major versions.
3. **Asset library sourcing.** "20-30 base material presets" and asset library assumed but no sourcing strategy (free Blender assets vs paid vs custom-built).
4. **短剧 vertical environment constraints.** 9:16 vertical framing crops wide environments heavily. No vertical-specific scene sizing or safe-zone guidance.
5. **GPU/render farm budgeting.** "Cycles GPU: ~8GB (1080p @256s)" — single-machine assumption. No render-farm allocation pattern for multi-shot 短剧 batches.
6. **CN-specific environmental elements.** 短剧 often features specific CN environments (ktv包间, 出租屋, 办公室, 街头小吃摊) with characteristic props. No CN scene preset library.

## <prompt_weak_points>

<!-- Vague instructions, missing thresholds, hand-wavy guidance -->

1. **"Space tells story"** — principle, not checkable.
2. **"3D previsualization saves 10x the cost"** — unsourced claim.
3. **`narrative_space_match: >= 0.85`** — match judged how? LLM-judged against screenplay? Undefined.
4. **`camera_constraint_validity: >= 0.90`** — validity checked against what? Editor's shot plan? Undefined.
5. **"Physically impossible scenes (can't render in Blender)"** — implicit rule but no explicit impossibility checklist.

## <stale_metrics>

<!-- metrics: [...] values that don't map to measurable behavior -->

- `narrative_space_match` — >= 0.85. No measurement protocol.
- `camera_constraint_validity` — >= 0.90. No measurement protocol.
- `asset_completeness` — >= 0.80. Completeness vs what asset manifest? No schema.
- `pipeline_integration_score` — >= 0.85. Subjective.

## <missing_refs_topics>

<!-- Subjects that should become references/*.md in Phase 3/5 refactor -->

Research classification: **needs light-to-medium refs (2-4)**.

1. `references/blender-version-and-addons.md` — pinned Blender version, required addons (Camera Bird, Shot Generator, etc.), asset library compatibility.
2. `references/cn-scene-presets.md` — CN 短剧 common environment presets (ktv包间, 出租屋, 办公室, 街头) with prop manifests.
3. `references/expert-cine-boundary.md` — documented handoff boundary between scene_builder (geometry) and EXPERT-CINE (camera semantics).
4. `references/render-farm-allocation.md` — multi-shot batch render scheduling, GPU allocation, cost estimation.
