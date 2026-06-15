# Shot Decomposition Rules (镜头分解规则)

**Source:** Bordwell & Thompson *Film Art* (11th ed.) + McKee scene-decomposition doctrine + 短剧 platform editing-density reports 2024-2026.
**Copyright:** Fair Use — methodology distillation.
**Last-verified:** 2026-06-16

## Summary

The authoritative rule set for decomposing screenplay scenes into per-shot Storyboard entries. Defines when each scene type (dialogue / action / emotion / transition) maps to which shot pattern, and the shot-count ranges per runtime.

## Heuristics

### Scene type → shot pattern mapping

| Scene type | Default shot pattern | Shot count (90s 短剧) |
|---|---|---|
| **对话场景 / Dialogue** | 正反打 / Over-the-shoulder alternating | 4-8 shots |
| **动作场景 / Action** | 全景 → 中景 → 特写 sequence | 6-12 shots |
| **情绪高潮 / Emotional peak** | 特写 + 缓慢推进 / Slow push-in close-up | 2-4 shots |
| **场景建立 / Establishing** | 全景 + 横摇或俯拍 / Wide + pan or high-angle | 1-2 shots |
| **过渡 / Transition** | 跟拍 / Tracking shot OR match-cut | 1-2 shots |
| **蒙太奇 / Montage** | 多个短 shot 快速切换 | 5-10 shots |
| **闪回 / Flashback** | 鸟瞰或荷兰角 + 慢动作 | 1-3 shots |

### Shot count calibration by runtime

| Episode length | Total shot count range | Avg shot duration |
|---|---|---|
| 15s (抖音 ad) | 3-5 | 3-5s |
| 30s (short short) | 4-7 | 4-6s |
| 60s (短剧 standard) | 6-12 | 5-8s |
| 90s (短剧 extended) | 10-18 | 5-9s |
| 180s (小程序剧) | 18-30 | 6-10s |
| 5min (微电影) | 30-50 | 6-10s |

**Why these ranges:**
- **Too few shots** = pacing feels slow, viewers lose attention (per [`../../_shared/cognitive-resonance-metrics.md`](../../_shared/cognitive-resonance-metrics.md) §Scale 1, attention-capture spacing ≤ 8s)
- **Too many shots** = chaotic, viewers can't track narrative (per cognitive-resonance §Scale 1, active-suspension concurrency ≤ 3)

### The 180° rule (zero-tolerance)

**Rule:** within a single scene, all camera positions must stay on one side of the "axis line" between two characters (or character + focal object).

**Violation consequence:** viewer disorientation; perceived as amateur.

**Auto-audit:**
1. For each scene, identify axis line(s).
2. For each shot, compute camera position relative to axis line.
3. Flag any shot that crosses the axis without an explicit neutralizing shot (e.g., a head-on shot).

**Exception:** intentional axis-crossing for confusion / dream-sequence effect. Must be marked with `"intentional_axis_cross": true` in shot metadata.

### The 30° rule (similar-shot cut)

**Rule:** when cutting between two shots of the same subject, the camera angle must differ by ≥ 30° (otherwise the cut looks like a jump-cut / glitch).

**Violation consequence:** perceived as editing error.

**Auto-audit:**
1. For consecutive shots featuring same character at same distance (e.g., medium → medium).
2. Compute angle difference (using camera position relative to character).
3. Flag any pair with angle difference < 30°.

**Exception:** intentional jump-cut for energy / disorientation. Must be marked with `"intentional_jump_cut": true`.

### Eyeline match rule

**Rule:** when character A looks off-screen at character B, character B's eyeline (in the next shot) must reciprocate — they're looking at each other.

**Violation consequence:** viewer feels something is off; "they're not actually looking at each other."

**Auto-audit:**
1. For each shot pair where character A looks off-screen.
2. Next shot of character B must have eyeline direction matching A's look direction (mirrored).

### Match-action rule

**Rule:** when an action continues across a cut, the on-screen motion must align (e.g., character raising hand in shot 1 must continue raising in shot 2, not restart).

**Violation consequence:** jarring discontinuity.

**Auto-audit:**
1. For each shot pair where action is described as "continuous."
2. Verify action verb in shot 1's `action` field matches shot 2's `action` field continuation.

### Rhythm curve templates

| Curve type | Description | Use case |
|---|---|---|
| **Escalating** | shot durations decrease over time | 情绪累积 / 高潮推进 |
| **Wave** | alternating long/short durations | 对话场景 / 情绪起伏 |
| **Constant** | similar durations throughout | 蒙太奇 / 平淡叙事 (rare) |
| **Reverse-escalating** | durations increase over time | 揭示 / 渐入佳境 (rare) |
| **Peak-valley** | one extreme peak + one extreme valley | 情绪反转 / 戏剧化 |

**Default for 短剧:** Escalating or Wave (depending on scene).

### Per-scene shot count decision tree

```
Is this a dialogue scene?
├── Yes → 4-8 shots, alternating over-the-shoulder
│   ├── 2 characters → 4-6 shots
│   ├── 3 characters → 6-8 shots (add coverage)
│   └── ≥ 4 characters → 8-12 shots (group shots + singles)
└── No → Is this an action scene?
    ├── Yes → 6-12 shots, wide→medium→close-up sequence
    │   ├── Single action → 4-6 shots
    │   ├── Multi-action (chase/fight) → 8-12 shots
    │   └── Climactic action → 10-15 shots (rapid cuts)
    └── No → Is this an emotional peak?
        ├── Yes → 2-4 shots, close-up + slow push-in
        └── No → Is this establishing / transition / montage?
            ├── Establishing → 1-2 shots, wide
            ├── Transition → 1-2 shots, tracking or match-cut
            └── Montage → 5-10 shots, rapid cuts
```

### Vertical (9:16) 短剧 adaptations

**Vertical screen changes shot composition rules:**
- **Close-ups dominate**: vertical frame limits wide compositions; close-ups and medium shots are preferred
- **Caption strip consideration**: bottom 10-15% of frame reserved for captions; avoid placing critical action there
- **Cut density 1.5-2× horizontal**: vertical short-form requires faster pacing than horizontal
- **Vertical headroom**: allow extra headroom above subjects (vertical frame aspect makes tight headroom feel cramped)

**Adjusted shot count for vertical 短剧:** multiply horizontal shot count by 1.5-2.0×.

### Common pitfalls

| Pitfall | Cause | Fix |
|---|---|---|
| All shots same duration | Lazy rhythm design | Use rhythm curve template; vary durations |
| Too many wide shots in vertical 短剧 | Treating vertical like horizontal | Default to medium / close-up for vertical |
| Axis violation in dialogue | Forgot 180° rule during shot assignment | Auto-audit; redesign over-the-shoulder pairs |
| Jump-cut between similar angles | 30° rule violation | Insert neutralizing shot OR widen angle difference |
| Mismatched eyeline in dialogue | Both characters looking same direction | Mirror eyeline direction across shot pair |
| Missing end_frame in multi-shot scene | Forgot extension-chain | Always emit end_frame for shots 1..N-1 in scene |

---

## Cross-references

- [`./camera-params-dictionary.md`](./camera-params-dictionary.md) — feeds camera angle/movement selection
- [`./4d-anchoring-params.md`](./4d-anchoring-params.md) — anchoring decided per shot
- [`./storyboard-schema.md`](./storyboard-schema.md) — schema for shot fields
- [`../../cinematographer/SKILL.md`](../../cinematographer/SKILL.md) — upstream shot-grammar rule definitions
- [`../../editor/references/murch.md`](../../editor/references/murch.md) — editor's rule-of-six consumes shot rhythm
- [`../../_shared/cognitive-resonance-metrics.md`](../../_shared/cognitive-resonance-metrics.md) §Scale 1 — attention-capture spacing drives shot count upper bound
