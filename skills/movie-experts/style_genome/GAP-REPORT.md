# GAP-REPORT: style_genome

**Audited:** 2026-06-15
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

## <phantoms>

None detected.

## <knowledge_gaps>

<!-- Topics the expert should know but SKILL.md doesn't cover -->

1. **Director archive depth.** Only 5 directors profiled (Wong Kar-wai, Nolan, Villeneuve, Fincher, Miyazaki). Research SUMMARY calls for "expanded director archive 30-50 names" including CN directors (Zhang Yimou, Ang Lee, Jia Zhangke, Feng Xiaogang, Guo Jingming — key for 短剧 aesthetic).
2. **CN genre conventions.** 短剧 genres (赘婿逆袭, 战神归来, 重生复仇, 豪门虐恋) have distinct style DNA not captured by Western director archetypes.
3. **Cross-cultural style divergence.** Style DNA encoded from Western directors may not transfer to CN audience expectations (e.g., Wong Kar-wai's 0.8 saturation reads differently to CN vs Western audiences).
4. **短剧 vertical-screen style genome.** 5D vector assumes horizontal composition. Vertical 短剧 may need a 6th dimension or re-calibrated composition scale.
5. **Style evolution over time.** Directors' style drifts across their filmography. No temporal versioning for director profiles (early Nolan vs late Nolan).
6. **User-defined style extraction.** Workflow assumes CLIP-based extraction from reference imagery, but no protocol for user-described abstract style ("make it feel like a Wong Kar-wai film but warmer").

## <prompt_weak_points>

<!-- Vague instructions, missing thresholds, hand-wavy guidance -->

1. **"Style is not vague — it can be measured"** — principle, but the 5D encoding is itself a subjective mapping (who decides Nolan's composition = 0.4?).
2. **`gene_extraction_accuracy: >= 0.85`** — accuracy vs what ground truth? Expert-labeled director profiles? Undefined.
3. **`blend_coherence: >= 0.80`** — coherence measured how? LLM-judged? Perceptual study? Undefined.
4. **`cross_module_alignment: >= 0.82`** — alignment of what signals? L2 distance aggregation? Undefined.
5. **`dominant_weight: 0.70 (default), 0.60-0.80 (adjustable)`** — no guidance on when to push toward 0.60 (more blending) vs 0.80 (stronger dominant).

## <stale_metrics>

<!-- metrics: [...] values that don't map to measurable behavior -->

- `style_consistency` — >= 0.88. No measurement protocol.
- `gene_extraction_accuracy` — >= 0.85. No ground truth defined.
- `blend_coherence` — >= 0.80. No measurement protocol.
- `cross_module_alignment` — >= 0.82. No measurement protocol.

## <missing_refs_topics>

<!-- Subjects that should become references/*.md in Phase 3/5 refactor -->

Research classification: **needs deep refs (4-6)** — top-4 priority expert per FEATURES.

1. `references/director-archive-expanded.md` — 30-50 director profiles with sourced 5D vectors, including CN directors (Zhang Yimou, Ang Lee, Jia Zhangke, Feng Xiaogang, Guo Jingming, Derek Tsang).
2. `references/cn-genre-style-dna.md` — 短剧 genre archetypes (赘婿逆袭, 战神归来, 重生复仇, 豪门虐恋) encoded as style genome variants.
3. `references/cross-cultural-perceptual-divergence.md` — how Western-encoded style DNA reads differently to CN audiences; compensation factors.
4. `references/vertical-style-genome.md` — 9:16 vertical-screen composition dimension re-calibration; proposed 6th dimension.
5. `references/user-style-extraction.md` — protocol for abstract user-described style ("warmer Wong Kar-wai") → 5D vector mapping.
6. `references/director-temporal-versioning.md` — early/mid/late career style drift profiles for prolific directors.
