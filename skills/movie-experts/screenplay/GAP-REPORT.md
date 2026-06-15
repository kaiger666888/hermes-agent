# GAP-REPORT: screenplay

**Audited:** 2026-06-15
**Audit tool:** scripts/verify_skill_references.py (sha256: see scripts/verify_skill_references.py)
**Baseline tag:** eval-baseline-v1

## <phantoms>

None detected.

## <knowledge_gaps>

<!-- Topics the expert should know but SKILL.md doesn't cover -->

1. **Save the Cat / McKee / Field structural references.** Research SUMMARY names *Save the Cat!* (Snyder), *Story* (McKee), *The Foundations of Screenwriting* (Field) as canonical screenplay sources. None cited. SKILL.md mentions "Hauge compression: 1 page = 30 seconds" without source.
2. **短剧-specific structure (not micro-film).** SKILL.md targets "60-180 seconds" which is micro-film territory. 短剧 episodes are 60-180s each but span 10-80 episodes with serialized cliffhangers. No multi-episode structure pattern.
3. **Hook design (3-second hook taxonomy).** Research SUMMARY EXPERT-HOOK requirements: 情感钩 / 悬念钩 / 冲突钩 / 反差钩 / 情绪爆点钩. No integration with future hook_retention expert.
4. **付费卡点 (paywall cliffhanger) design.** Research SUMMARY: 小程序剧 with 付费卡点 at min 3-5 of 10 episodes. No paywall structure pattern.
5. **CN dialogue conventions.** 短剧 dialogue density / subtext ratio differs from Western film. Ban on "as you know" expository constructions noted but no CN-specific equivalent (e.g., 旁白过度).
6. **Platform branching (抖音 vs 快手 vs 小程序剧).** Research SUMMARY: 爆款公式 diverges per platform. No per-platform dialogue/pacing variant.

## <prompt_weak_points>

<!-- Vague instructions, missing thresholds, hand-wavy guidance -->

1. **"Opening hook within first 3 seconds"** — good threshold, but no hook taxonomy (what KIND of hook?).
2. **"Subtext ratio: minimum 60% implicit meaning per line"** — strong threshold but no measurement protocol (LLM-judged? rule-based?).
3. **"Each scene has a clear dramatic question"** — "clear" is subjective.
4. **`narrative_tension: >= 0.80`** — no measurement protocol.
5. **`dialogue_naturalness: >= 0.85`** — no measurement protocol.
6. **"Hauge compression: 1 page = 30 seconds screen time"** — cited without source. Is this Hauge or a paraphrase?

## <stale_metrics>

<!-- metrics: [...] values that don't map to measurable behavior -->

- `narrative_tension` — >= 0.80. No measurement protocol.
- `dialogue_naturalness` — >= 0.85. No measurement protocol.
- `emotional_arc` — listed as "Complete (setup→tension→climax→resolution)". Categorical, OK but no rule for detecting "incomplete".

## <missing_refs_topics>

<!-- Subjects that should become references/*.md in Phase 3/5 refactor -->

Research classification: **needs deep refs (4-6)** — top-4 priority expert per FEATURES.

1. `references/save-the-cat-beat-sheet.md` — Snyder 15-beat structure adapted to 60-180s 短剧 format.
2. `references/mckee-story-scene-design.md` — McKee's scene-value-shift / beat / turning-point theory.
3. `references/shortdrama-multi-episode-structure.md` — 10-80 episode serialized structure with 付费卡点 placement (min 3-5 of 10).
4. `references/hook-taxonomy.md` — 3-second hook taxonomy (情感钩 / 悬念钩 / 冲突钩 / 反差钩 / 情绪爆点钩) with examples per platform.
5. `references/platform-explosion-formulas.md` — 抖音 男频 / 女频 / 快手 草根 / 小程序剧 branching formulas.
6. `references/cn-dialogue-conventions.md` — CN-specific dialogue density, subtext, vernacular register guidance.
