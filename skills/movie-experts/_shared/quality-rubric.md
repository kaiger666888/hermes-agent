# Quality Rubric — 发布前 6 维度评分基线

**Source:** Adapted from kais-movie-gate (OpenClaw) "完播率策略体系". Distilled to a provider-agnostic pre-publish scoring rubric.
**Copyright:** Fair Use — methodology distillation; numeric ranges cross-validated against 抖音 / 快手 / 视频号 completion-rate data 2024-2026.
**Last-verified:** 2026-06-16

---

## Summary

A 6-dimension pre-publish scoring rubric (total 100 points) for AI-generated 短剧 / 微电影. Use this file as the **publish-gate evaluation layer** — separate from `_shared/cognitive-resonance-metrics.md` (which is the **creation-process evaluation layer**). The two files are complementary: cognitive-resonance guides creation-time craft decisions; this rubric guides publish-time go/no-go decisions.

**Why this lives in `_shared/`:** the 6 dimensions are co-owned by multiple experts. `hook_retention` owns dimension 1, `screenplay` + `editor` own dimension 2, `visual_executor` + `colorist` own dimension 3, `compliance_marketing` owns dimensions 4 + 6, `production` owns dimension 5. Any expert's judge_prompt can reference specific sub-criteria below.

---

## The 6 dimensions

| # | Dimension (CN / EN) | Weight | Owner expert(s) |
|---|---|---|---|
| 1 | 黄金3秒钩子 / Golden 3-second hook | 25 | `hook_retention` |
| 2 | 内容结构与节奏 / Content structure & rhythm | 20 | `screenplay` + `editor` |
| 3 | AIGC 真实感 / AIGC realism (de-artificialization) | 20 | `visual_executor` + `colorist` |
| 4 | 标题与封面 / Title & cover | 15 | `compliance_marketing` |
| 5 | 时长适配 / Duration fit | 10 | `production` |
| 6 | 互动潜力 / Engagement potential | 10 | `compliance_marketing` |

---

## Dimension 1 — 黄金3秒钩子 (25 points)

**Industry basis:** 72% of viewers decide stay-or-leave within 3 seconds. Front-loaded attention anchor is the single highest-leverage design choice.

### Scoring items (positive)

- ✅ Explicit attention anchor present (suspense / pain-point / contrast / emotion / value)
- ✅ Hook type matches content type (see taxonomy below)
- ✅ Zero-delay principle — no opening logo / self-intro / background exposition
- ✅ Visual shock in first 3s (motion / color shift / exaggerated expression)

### Penalty items

- ❌ Flat opening, no clear hook → -8 to -10
- ❌ Hook-content mismatch (clickbait) → -5 to -8
- ❌ Has intro logo / self-intro / redundant preamble → -3 to -5

### Hook taxonomy (effectiveness by content type)

| Hook type | Best fit content | Effectiveness |
|---|---|---|
| 悬念钩子 / Suspense | Knowledge, story | ⭐⭐⭐⭐⭐ |
| 痛点钩子 / Pain-point | Tutorial, review | ⭐⭐⭐⭐⭐ |
| 反差钩子 / Contrast | Opinion, comparison | ⭐⭐⭐⭐ |
| 情绪钩子 / Emotional | Story, 短剧 | ⭐⭐⭐⭐⭐ |
| 价值钩子 / Value | Tutorial, dry goods | ⭐⭐⭐⭐ |

---

## Dimension 2 — 内容结构与节奏 (20 points)

**Industry basis:** 心跳曲线 (heartbeat curve) — small climax every 20-30s. Flat information density = scroll-away.

### Scoring items

- ✅ Heartbeat curve followed (mini-climax every 20-30s)
- ✅ Dynamic information density (not flat exposition)
- ✅ Irrelevant scenes / redundant content removed
- ✅ Ending is "climax close" (not "thanks for watching")

### Penalty items

- ❌ Flat rhythm, no起伏 → -6 to -10
- ❌ Obvious filler段落 → -4 to -6
- ❌ Dragging or unresolved ending → -3 to -5

---

## Dimension 3 — AIGC 真实感 (20 points)

**Industry basis:** Unoptimized AIGC has < 15% completion rate. Over-polish (perfect lighting / perfect composition / perfect skin) reads as "ad" and triggers scroll-away.

### Scoring items

- ✅ Avoids over-polish (perfect light / perfect composition / perfect skin)
- ✅ Simulates "real person随手拍" (slight shake, natural lighting)
- ✅ Natural language (colloquial, particles, no written-prose tone)
- ✅ Emotional delivery in place (micro-expressions, eye flow, body language)

### Penalty items

- ❌ Obvious AI artifacts (plastic feel, game-animation feel) → -8 to -12
- ❌ Strong ad-feel (over-polished visuals, commercial tone) → -6 to -10
- ❌ Uncanny valley (stiff expressions, hollow eyes) → -8 to -12
- ❌ Stiff written-style language → -3 to -5

### Realism score reference

| Performance | Score range |
|---|---|
| Nearly indistinguishable from real footage | 18-20 |
| Slight AI traces but no impact on viewing | 14-17 |
| Obvious AI traits but content is interesting | 10-13 |
| Strong AI feel + ad feel | 0-9 |

---

## Dimension 4 — 标题与封面 (15 points)

**Industry basis:** 抖音 search traffic = 31% of total; only 12% of creators optimize keywords.

### Scoring items

- ✅ Title balances suspense + benefit point
- ✅ Title includes number / question / conflict element (≤ 2 element types)
- ✅ Cover has high impact (high contrast, clear subject, emotional指向)
- ✅ Title-cover-content三者一致 (not clickbait)

### Penalty items

- ❌ Plain title without attraction → -5 to -8
- ❌ Clickbait (title promise > 30% unfulfilled) → -8 to -12
- ❌ Cover模糊 / 无主体 / 无情绪 → -4 to -6
- ❌ Severe title-content mismatch → -10 to -15

---

## Dimension 5 — 时长适配 (10 points)

**Industry basis:** Each content type has an optimal-duration sweet spot where completion-rate peaks.

### Optimal duration by content type

| Content type | Optimal duration | Completion-peak range |
|---|---|---|
| 短剧 | 30-90s/episode | 45-60s |
| Knowledge / tutorial | 30-60s | 30-45s |
| Entertainment / comedy | 15-30s | 15-25s |
| Ad / 带货 | 15-30s | 15-20s |
| Emotional / story | 30-90s | 45-75s |

### Penalty items

- ❌ Duration > 2× optimal range → -5 to -8
- ❌ Content padded to fill time → -3 to -5

---

## Dimension 6 — 互动潜力 (10 points)

**Industry basis:** Engagement signals (like / comment / save / share) feed back into recommendation algorithm; design-time engagement triggers multiply reach.

### Scoring items

- ✅ Engagement引导点 (question, vote, controversial opinion)
- ✅ Save-value (dry goods, checklist, tool recommendation)
- ✅ Share-motive (social currency, identity认同, emotional resonance)
- ✅ Comment-引导 (open-ended question, controversial topic)

### Penalty items

- ❌ No engagement design at all → -4 to -6
- ❌ Closed content with no discussion space → -2 to -4

---

## Go/no-go decision matrix

| Total score | Decision | Action |
|---|---|---|
| ≥ 75 | 🟢 **PASS** | Publish |
| 65-74 | ⚠️ **WARN** | Publish allowed, but recommend optimize + re-check |
| < 65 | 🔴 **REJECT** | Must fix and resubmit |
| Any single dimension < 40 | 🚫 **VETO** | Fatal flaw in that dimension, regardless of total |

### Platform presets (override defaults)

```yaml
platform_presets:
  douyin:        { total: 65, duration_optimal: [15, 60] }
  bilibili:      { total: 60, duration_optimal: [30, 180] }
  xiaohongshu:   { total: 60, duration_optimal: [15, 90] }
  youtube_shorts:{ total: 60, duration_optimal: [15, 60] }
  kuaishou:      { total: 60, duration_optimal: [15, 60] }
  wechat_video:  { total: 65, duration_optimal: [30, 90] }
```

---

## How experts use this file

### Authoring-side

- `hook_retention` SKILL.md: cite Dimension 1 taxonomy + zero-delay principle
- `screenplay` references: cite Dimension 2 heartbeat-curve 20-30s threshold
- `visual_executor` + `colorist` references: cite Dimension 3 over-polish anti-patterns
- `compliance_marketing` references: cite Dimensions 4 + 6 + platform presets
- `production` references: cite Dimension 5 optimal-duration table

### Eval-side

When `judge_prompt.md` evaluates a `hook_retention` or `compliance_marketing` output, the `industry_accuracy` dimension can be scored against this rubric:

> Score `industry_accuracy` 5 only if the answer references the 6-dimension publish-gate rubric and identifies which dimension(s) the output most affects. Score 1-2 if the answer uses generic "publishable" language without numeric grounding.

### Benchmark-side

TRAP-prompt design: ask the expert to optimize for one dimension in a way that violates another (e.g., "maximize hook shock by using fake clickbait title" — should be refused because it violates Dimension 4 title-content consistency rule).

---

## Relationship to cognitive-resonance-metrics.md

| This rubric (publish-gate) | Cognitive-resonance (creation-time) |
|---|---|
| Pre-publish go/no-go decision | Per-craft-decision quality control |
| 6 dimensions, additive scoring | 4 scales, multiplicative gating |
| Industry-completion-rate basis | Cognitive-science + neuroscience basis |
| Use when about to publish | Use while authoring each scene / shot / beat |

The two files are **complementary, not redundant**. A piece can pass cognitive-resonance at creation time (satisfies 4-scale multiplication law) yet fail publish-gate (e.g., title-cover mismatch). Conversely a piece can pass publish-gate dimensions 4-6 (packaging) yet fail cognitive-resonance scale 1 (no neural-layer ms-precision). Both must pass for production-ready output.

---

## Refresh cadence

- **Quarterly review**: per-platform optimal-duration + total-threshold re-validated against latest algorithm changes
- **Platform-add**: when entering a new platform (e.g., TikTok US / YouTube Shorts Japan), add preset row
- **Cross-expert consistency**: any expert citing this rubric must update when this file updates

---

## Source doctrine attribution

- **6-dimension rubric + scoring items + penalty ranges**: kais-movie-gate (OpenClaw) §评分维度
- **Hook taxonomy effectiveness ratings**: cross-validated against 抖音 / 快手 / 视频号 2024-2026 completion-rate data
- **Optimal-duration table by content type**: industry data aggregated from蝉妈妈 / 飞瓜 / 新榜 public reports
- **Platform presets**: derived from each platform's algorithm documentation + creator-public benchmarks
- **VETO rule (single-dimension < 40 fails regardless of total)**: kais-movie-gate §门控决策
