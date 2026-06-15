# Emotion Arc Audit (情感弧线审计)

**Source:** Plutchik *A General Psychoevolutionary Theory of Emotion* (1980) + emotion-curve academic refs in [`../../screenplay/references/emotion-curve-academic.md`](../../screenplay/references/emotion-curve-academic.md) + 短剧 emotion-labeling corpus 2024-2026.
**Copyright:** Fair Use — methodology distillation.
**Last-verified:** 2026-06-16

## Summary

Quantitative rubric for scoring Dimension 2 (Emotion Arc, 20 points) of the script audit. Evaluates whether the script's emotional trajectory follows the sawtooth pattern that sustains audience engagement, has sufficient valence range, and avoids dead zones (emotional plateaus).

## Heuristics

### Plutchik 8-dimensional emotion model

All emotion annotations use Plutchik's 8 primary emotions:

| Emotion (CN) | Emotion (EN) | Valence | Arousal |
|---|---|---|---|
| 愤怒 | Anger | -1 | High |
| 恐惧 | Fear | -1 | High |
| 悲伤 | Sadness | -1 | Low |
| 厌恶 | Disgust | -1 | Low |
| 惊讶 | Surprise | 0 | High |
| 期待 | Anticipation | +1 | Low |
| 信任 | Trust | +1 | Low |
| 喜悦 | Joy | +1 | High |

**Compound emotions** (e.g., 爱慕 = Joy + Trust, 绝望 = Sadness + Fear) computed by averaging primary components.

### Sub-metric 1: Emotion polarity range (7 points)

**Metric:** `range = max(valence_t) - min(valence_t)` over all scenes t.

Valence is computed as the average Plutchik valence across all emotion annotations in the scene, normalized to [-1, +1].

**Hit/miss thresholds:**

| Range | Hit (Top 10%) | Miss (Bottom 30%) |
|---|---|---|
| 极性跨度 | ≥ 1.4 | < 0.6 |

**Scoring:**
- Range ≥ 1.6 → 7 points
- 1.4-1.59 → 6 points
- 1.0-1.39 → 4 points
- 0.6-0.99 → 2 points
- < 0.6 → 1 point

### Sub-metric 2: Transition frequency (7 points)

**Metric:** Count of significant emotion transitions per minute.

**Transition definition:** A scene-to-scene valence change with `|Δvalence| ≥ 0.3` AND/OR primary-emotion class change.

**Hit/miss thresholds (短剧-specific):**

| Frequency | Hit (Top 10%) | Miss (Bottom 30%) |
|---|---|---|
| 情绪转场频率 | ≥ 5.0 次/分钟 | < 2.0 次/分钟 |

> **NOTE:** 短剧 has 1.5-2× higher transition frequency requirement than 微电影 due to shorter runtime and higher audience-scroll-away risk.

**Scoring:**
- ≥ 6.0 次/min → 7 points
- 5.0-5.9 → 6 points
- 3.5-4.9 → 4 points
- 2.0-3.4 → 2 points
- < 2.0 → 1 point

### Sub-metric 3: Ending valence (6 points)

**Scoring rules:**
- Ending returns to positive valence (+0.3 or higher) → 4 points base
- Ending leaves powerful suspense for next episode → +2 points (cliffhanger)
- Ending stays negative (-0.3 or lower) without suspense → -2 points (烂尾感)
- Ending emotionally ungrounded (no clear emotion) → -3 points

**Adjustment for serialized 短剧:**
- S01E01-E05: ending should establish悬念 (> -0.5 valence + cliffhanger flag)
- S01E06-E10: ending should escalate (> -0.3 valence + cliffhanger flag)
- S01 finale: ending should close major value gap (+0.3 or higher valence)

### Sawtooth amplitude doctrine

Per [`../../_shared/cognitive-resonance-metrics.md`](../../_shared/cognitive-resonance-metrics.md) §Scale 2:

- **Hard requirement:** peak-to-trough delta ≥ 0.4 (on [-1,+1] valence scale) per sawtooth cycle
- **Hard requirement:** no plateau > 15s (consecutive same-valence scenes)
- **Hard requirement:** each sawtooth peak must exceed prior peak (锯齿递增 — regression to baseline = repetitive)

### Deduction rules

| Violation | Penalty |
|---|---|
| 连续场景情绪无变化(情绪平坦) | -3 per occurrence |
| 开场情绪为负面且全剧无回升(压抑开头) | -4 |
| 结局情绪无着落(烂尾感) | -3 |
| 情绪平台期 > 15s | -2 per occurrence (aligns with cognitive-resonance §Scale 2) |
| Sawtooth 峰值递减(regression) | -3 |
| 单调情绪线(只升或只降) | -3 |

### Hit-pattern reference (Top 10%)

| Metric | Mean | Std |
|---|---|---|
| 极性跨度 | 1.65 | 0.18 |
| 转场频率 (per min) | 6.2 | 0.8 |
| 平台期最长 (s) | 8 | 3 |
| 结局 valence | +0.45 | 0.15 |

### Miss-pattern reference (Bottom 30%)

| Metric | Mean | Std |
|---|---|---|
| 极性跨度 | 0.45 | 0.15 |
| 转场频率 (per min) | 1.3 | 0.5 |
| 平台期最长 (s) | 32 | 8 |
| 结局 valence | -0.10 | 0.25 |

---

## Cross-references

- [`../../screenplay/references/emotion-curve-academic.md`](../../screenplay/references/emotion-curve-academic.md) — Authoritative emotion-curve doctrine; this audit ref consumes screenplay's emotion_curve schema as input
- [`../../_shared/cognitive-resonance-metrics.md`](../../_shared/cognitive-resonance-metrics.md) §Scale 2 — Source of sawtooth + plateau thresholds
- [`./narrative-structure-audit.md`](./narrative-structure-audit.md) — Dimension 1 rhythm variation correlates with emotion transition frequency
