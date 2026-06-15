# Hook Strength Audit (Hook 强度审计)

**Source:** 短剧 platform behavioral data 2024-2026 (抖音 3-second drop-off curves) + hook taxonomy from [`../../hook_retention/references/three-second-hooks.md`](../../hook_retention/references/three-second-hooks.md).
**Copyright:** Fair Use — methodology distillation from public platform reports.
**Last-verified:** 2026-06-16

## Summary

Quantitative rubric for scoring Dimension 3 (Hook Strength, 20 points) of the script audit. Evaluates whether the script's opening 3s hook, chapter-end hooks, and first information impact are strong enough to retain audience past critical drop-off points.

## Heuristics

### Sub-metric 1: Opening 3-second hook (10 points)

**Industry basis:** 72% of 短剧 viewers decide stay-or-leave within 3 seconds.

**Scoring scale (per opening scene):**

| Score | Criteria |
|---|---|
| 10 | 开场即冲突(动作 / 悬念 / 反转),明确钩子类型,与内容类型匹配 |
| 8-9 | 开场有强烈情绪张力,冲突明显,符合"然后呢?"反应 |
| 6-7 | 开场有钩子但张力一般,需要 2-3s 才能确认 |
| 4-5 | 开场平铺直叙但有悬念暗示 |
| 1-3 | 开场缓慢,无任何钩子;或开场为片头 logo / 自我介绍 |

### Hook taxonomy and content-type match matrix

Per [`../../_shared/quality-rubric.md`](../../_shared/quality-rubric.md) §Dimension 1:

| Hook type | Best fit | Effectiveness |
|---|---|---|
| 悬念钩子 / Suspense | Knowledge, story | ⭐⭐⭐⭐⭐ |
| 痛点钩子 / Pain-point | Tutorial, review | ⭐⭐⭐⭐⭐ |
| 反差钩子 / Contrast | Opinion, comparison | ⭐⭐⭐⭐ |
| 情绪钩子 / Emotional | Story, 短剧 | ⭐⭐⭐⭐⭐ |
| 价值钩子 / Value | Tutorial, dry goods | ⭐⭐⭐⭐ |

**Mismatch penalty:**
- 情绪钩子 for knowledge content → -1 to -2 (effective but wasteful)
- 价值钩子 for story 短剧 → -2 to -3 (wrong audience心理 frame)
- 悬念钩子 for ad/带货 → -3 to -4 (triggers clickbait perception)

### Sub-metric 2: Chapter hook (5 points)

**Definition:** Suspense or tension hook placed at end of each act / chapter to maintain engagement into next act.

**Scoring criteria:**
- Each act ending has明确 suspense / tension → +1 per act (max 5)
- Act ending has no hook (just transitions) → 0
- Act ending is "thanks for watching" style → -1

### Sub-metric 3: First information impact (5 points)

**Definition:** Whether the first 10 seconds contain a core conflict, reversal, or key信息抛出.

**Scoring:**
- First 10s explicitly raises central conflict or reverses expectation → 5
- First 10s hints at central conflict but not explicit → 3
- First 10s only establishes background → 2
- First 10s is generic exposition with no central-conflict signal → 1

### The "然后呢?" golden rule

**Hard requirement:** The opening 3s MUST trigger "然后呢?" (what happens next?) reaction.

**Test:** Read the opening 3s in isolation. If a viewer would NOT spontaneously ask "然后呢?", the hook fails. Common failure modes:
- ❌ Opening establishes scene but no stakes ("The sun rises over the city...")
- ❌ Opening introduces character but no conflict ("Meet John, an ordinary guy...")
- ❌ Opening shows action but no uncertainty ("John drives to work...")

### Zero-delay principle

Per [`../../_shared/quality-rubric.md`](../../_shared/quality-rubric.md) §Dimension 1:

- ❌ No opening logo animation (any logo = -2)
- ❌ No self-introduction by narrator (any self-intro = -3)
- ❌ No background exposition > 3s (any exposition > 3s before hook = -3)

### Deduction rules

| Violation | Penalty |
|---|---|
| 开场 3s 无明确钩子 | -3 to -8 |
| 钩子类型与内容类型不匹配 | -1 to -4 |
| 片头 logo / 自我介绍 / 背景铺垫 > 3s | -2 to -5 |
| 章节结尾无悬念过渡 | -1 per occurrence |
| 前 10s 无核心矛盾信号 | -2 to -4 |
| 标题党(钩子承诺 > 30% 未兑现) | -5 to -8 (aligns with quality-rubric §Dimension 4) |

### Hit-pattern reference (Top 10%)

| Metric | Mean | Std |
|---|---|---|
| 3s Hook score | 8.7 | 0.8 |
| Chapter hook (5 acts) | 4.5 | 0.5 |
| First info impact | 4.3 | 0.6 |
| 钩子类型匹配率 | 92% | 8% |

### Miss-pattern reference (Bottom 30%)

| Metric | Mean | Std |
|---|---|---|
| 3s Hook score | 3.2 | 1.1 |
| Chapter hook (5 acts) | 1.8 | 0.7 |
| First info impact | 1.9 | 0.5 |
| 钩子类型匹配率 | 38% | 15% |

---

## Cross-references

- [`../../hook_retention/references/three-second-hooks.md`](../../hook_retention/references/three-second-hooks.md) — Authoritative hook taxonomy (hook_retention expert's ref)
- [`../../_shared/quality-rubric.md`](../../_shared/quality-rubric.md) §Dimension 1 — Source of the 25-point publish-gate hook rubric
- [`../../_shared/cognitive-resonance-metrics.md`](../../_shared/cognitive-resonance-metrics.md) §Scale 1 — Neural-layer attention-capture doctrine
