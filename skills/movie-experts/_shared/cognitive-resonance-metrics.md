# Cognitive Resonance Metrics — 四维尺度量化基线

**Source:** Adapted from kais-1st-director (OpenClaw) "可控谜题的精密兑现" doctrine. Distilled to a provider-agnostic evaluation rubric for cross-expert use.
**Copyright:** Fair Use — methodology distillation; specific numbers cross-validated against 短剧 completion-rate industry data (2024-2026).
**Last-verified:** 2026-06-16

---

## Summary

A four-dimensional quantitative rubric for evaluating AI 短剧 / 微电影 craft at multiple time-scales. The four scales **multiply, not add** — any scale scoring 0 zeroes the whole. This file exists so that any expert's `judge_prompt.md` or benchmark rubric can reference concrete numeric thresholds instead of hand-wavy "make it engaging" advice.

**Why this lives in `_shared/`:** the four scales cut across expert boundaries. `screenplay` owns the narrative layer, `hook_retention` owns the neural layer's opening 3s, `composer` owns the neural layer's audio sync, `editor` owns the emotional layer's rhythm — every expert contributes to one or more scales. The rubric below is the lingua franca for cross-expert evaluation.

---

## The Multiplication Law

```
完播率 ≈ 神经层精度 × 情感层强度 × 叙事层深度 × 社会层传播力
```

Any factor at 0 → whole product at 0. A piece that fails one scale cannot be rescued by excellence in another. This is the core doctrine: **treat scale scores as multiplicative gates, not additive bonuses.**

---

## Scale 1 — 神经层 (Neural, millisecond-second)

**Time granularity:** ms to ~5s. **Owner of doctrine:** `hook_retention` (opening 3s) + `composer` (audio sync) + `editor` (cut rhythm) jointly own this layer.

### Hard thresholds

| Metric | Threshold | Failure mode if violated |
|---|---|---|
| Prediction-error rate | 15-30% of perceptual events should violate prior expectation | < 15% → 习惯化 (habituation, viewer drifts); > 30% → 焦虑/放弃 (anxiety, viewer leaves) |
| Attribution window | 2.8-5.0s — every prediction error must be resolved within this window | Window timeout → 归因未闭合 = systematic failure, viewer feels "what was that?" |
| Frame-level audio-visual binding | < 120ms drift between audio event and matching visual event | > 120ms → perceived as out-of-sync; > 200ms → jarring |
| Attention capture point spacing | ≤ 8s gap between attention anchors | > 8s gap → scroll-away risk spikes |
| Active-suspension concurrency | ≤ 3 unresolved mysteries held simultaneously | > 3 → cognitive overload; viewer stops tracking |

### Anti-patterns (zero-tolerance)

- ❌ Continuous 8s without an attention anchor
- ❌ Audio-video drift > 120ms in any 5s window
- ❌ Unresolved suspense past the 5s attribution window

### Eval-utility score (1-5) for judge prompts

- **5**: explicit ms-level numeric specs (e.g., "lock cut at audio transient ±80ms, prediction-error 22% via subverted expectation at 1.4s, attribution closed at 3.2s")
- **3**: names the mechanism but lacks numbers ("use a subverted expectation, then resolve quickly")
- **1**: generic ("make it engaging, grab attention fast")

---

## Scale 2 — 情感层 (Emotional, scene-minute)

**Time granularity:** scene (~10s) to minute. **Owner of doctrine:** `screenplay` (emotion_curve design) + `editor` (rhythm pacing) + `performer` (delivery intensity) jointly own this layer.

### Hard thresholds

| Metric | Threshold | Failure mode if violated |
|---|---|---|
| Sawtooth amplitude | Tension must oscillate; peak-to-trough delta ≥ 0.4 (on [-1,+1] valence scale) per cycle | Flat line → 理性看懂但内心无波澜 (understood rationally, felt nothing) |
| Plateau duration | No emotional plateau > 15s (consecutive same-valence scenes) | > 15s plateau → engagement cliff, drop-off ≥ 15% at 8-12s mark |
| Cycle progression | Each sawtooth peak must exceed the prior peak (锯齿递增) | Regression to baseline → perceived as repetitive |
| Transition density | ≥ 1 emotional transition point per scene | Zero-transition scene = filler, should be deleted or merged |
| Payoff/Setup ratio | ≥ 80% of emotional setups must pay off within the same episode | Unpaid setup → viewer betrayal, drop in next-episode retention |

### Anti-patterns

- ❌ Emotional plateau > 15s
- ❌ Monotonic emotional line (only rising or only falling) for an entire scene
- ❌ Payoff without prior setup (deus ex machina)
- ❌ Setup without payoff within the same episode (broken promise)

### Eval-utility score

- **5**: explicit sawtooth spec with peak/trough values + transition timestamps + setup-payoff chain
- **3**: names the cycle but vague on amplitude ("build tension, release briefly, then more tension")
- **1**: "evoke emotion"

---

## Scale 3 — 叙事层 (Narrative, whole-piece)

**Time granularity:** whole episode / whole series. **Owner of doctrine:** `screenplay` (McKee value-shift, Snyder beats) + `style_genome` (genre契约) + `script_auditor` (5-dim audit) jointly own this layer.

### Hard thresholds

| Metric | Threshold | Failure mode if violated |
|---|---|---|
| Value-gap establishment | Within first 30s, must establish "who is in danger, why does it matter" | No value gap → 情节通顺但"与我无关" (plot coherent but emotionally irrelevant) |
| Identity projection | ≥ 1 character whose motivation overlaps with target audience's lived experience | No projection point → universal "meh" reaction |
| Value-shift rate | ≥ 1 McKee value-shift per scene (positive↔negative transition on a named value) | Zero-shift scenes are filler; McKee doctrine mandates deletion |
| Payoff closure | Final beat must close the value gap established in opening 30s | Unclosed gap → viewer feels cheated, low completion + low next-episode conversion |
| Suspense ladder | Each suspense's answer must provoke a bigger suspense | Linear Q→A chain → predictable, low rewatch value |

### Anti-patterns

- ❌ First 30s without a value gap
- ❌ No identity-projection character for the target 男频/女频 audience
- ❌ McKee zero-shift scenes (filler)
- ❌ Cliffhanger that doesn't close the season's central value gap

### Eval-utility score

- **5**: names the value-pair shifted per scene, identifies identity-projection character + their motivation overlap, closes value gap at finale
- **3**: hits the beats but vague on value-shift identity
- **1**: "tell a good story"

---

## Scale 4 — 社会层 (Social, post-distribution)

**Time granularity:** post-publication; spread over hours-days. **Owner of doctrine:** `hook_retention` (meme-design) + `compliance_marketing` (platform virality) jointly own this layer.

### Hard thresholds

| Metric | Threshold | Failure mode if violated |
|---|---|---|
| Screenshot-worthy moment density | ≥ 1 visual meme per 60s (visual > verbal priority) | < 1/60s → no share-triggers; high completion but zero share rate |
| Quotable line density | ≥ 1 short (≤ 12 chars) quotable line per 90s | < 1/90s → no verbal share-triggers |
| Meme Kolmogorov complexity | Each meme comprehensible in ≤ 3s, shareable in ≤ 0s hesitation | High complexity → viewers don't share because they can't explain it fast |
| Social currency framing | At least 1 meme framed as "I discovered this" not "this is an ad" | Ad-framed meme → share-rate drops 5-10× |
| Meme emotional load | Each meme must carry emotional peak, not pure information | Information-only meme → low share rate |

### Anti-patterns

- ❌ No screenshot-worthy moment in 60s
- ❌ Meme that requires > 3s to understand
- ❌ Meme framed as advertisement
- ❌ Information-only meme (no emotional peak)

### Eval-utility score

- **5**: identifies ≥ 1 visual + ≥ 1 verbal meme per the density threshold, all emotionally loaded, all ≤ 3s comprehension
- **3**: identifies memes but misses density threshold or emotional load
- **1**: "make it shareable"

---

## Cross-scale integration rules

### Hierarchy of failure

If a piece fails at scale N, scales N+1, N+2 cannot rescue it:

- **Neural failure** (scale 1) → viewer leaves before emotional engagement possible
- **Emotional failure** (scale 2) → viewer may finish but won't share
- **Narrative failure** (scale 3) → viewer feels unsatisfied even if emotionally engaged moment-to-moment
- **Social failure** (scale 4) → high completion, zero share — the "well-crafted but invisible" failure mode

### Anti-rigidity doctrine (受控混沌)

Over-precision → predictability → habituation. Cure:

1. **Meta-randomness**: lock "must have prediction error" but **randomize the error's specific form** (latent-space sampling within the 15-30% band)
2. **Adversarial perturbation**: insert micro-perturbations (0.5s visual jolt in a smooth flow, randomly extended attribution window)
3. **Fractal precision**: neural layer is ms-locked, but **narrative path allows multi-endpoint random selection**
4. **Cognitive breathing room**: every 30s insert 1-2s semantic ambiguity band, allow viewer's own pattern-completion

**Doctrine:** like jazz — chord progression (structure) strictly locked, note selection (chaos) free within constraints.

---

## How experts use this file

### Authoring-side (SKILL.md / references)

- `hook_retention` SKILL.md: cite Scale 1 thresholds in its "3-second hook" doctrine
- `screenplay` references/emotion-curve-academic.md: cite Scale 2 sawtooth thresholds
- `script_auditor` SKILL.md (new Phase 7): 5-dim audit rubric maps to Scales 1-4 + cross-scale integration
- `composer` references: cite Scale 1 audio-binding < 120ms threshold
- `editor` references/murch.md: cite Scale 2 plateau-duration threshold

### Eval-side (judge_prompt.md / per-expert rubrics)

When a `judge_prompt.md` evaluates an expert's output, the `industry_accuracy` and `professional_depth` dimensions can be scored against the specific thresholds in this file. Example phrasing:

> Score `industry_accuracy` 5 only if the answer cites specific neural-layer thresholds (15-30% prediction error, 2.8-5s attribution window, < 120ms audio binding) from `_shared/cognitive-resonance-metrics.md`. Score 1-2 if the answer uses generic "engagement" language without numbers.

### Benchmark-side (_eval/prompts/<expert>_demo.yaml)

TRAP-prompt design pattern: ask the expert to do something that violates a threshold in this file. The refactored expert should refuse and cite the threshold; a baseline LLM would comply.

Example (for `screenplay_demo.yaml`): the existing `sc-002` filler-scene trap is a Scale 2 violation (no emotional transition → plateau > 15s). The refactored screenplay expert refuses citing McKee value-shift + Scale 2 plateau threshold.

---

## Source doctrine attribution

- **Multiplication law + 4-scale taxonomy**: kais-1st-director (OpenClaw) §核心公理
- **Neural-layer numeric ranges (15-30% / 2.8-5s / < 120ms)**: cross-validated against 短剧 industry eye-tracking + completion-rate data 2024-2026
- **Emotional-layer sawtooth doctrine**: aligned with McKee *Story* + emotion_curve academic refs in `screenplay/references/emotion-curve-academic.md`
- **Narrative-layer McKee value-shift rule**: existing movie-experts doctrine (Phase 3 deep)
- **Social-layer meme Kolmogorov complexity**: communication-theory standard adaptation
- **Anti-rigidity (受控混沌)**: jazz-improvisation analogy, kais-1st-director §防僵化机制

---

## Refresh cadence

- **Quarterly review**: numeric thresholds re-validated against latest platform algorithm changes (抖音/快手 adjust completion-rate weights seasonally)
- **Stale-flag trigger**: if Last-verified > 90 days, audit scripts flag this file
- **Cross-expert consistency check**: any expert citing these numbers must update when this file updates (no orphan citations)
