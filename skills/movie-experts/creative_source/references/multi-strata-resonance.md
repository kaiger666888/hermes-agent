# Multi-Strata Resonance (多层叠加共振)

**Source:** Adapted from OpenClaw kais-soul-radar multi-layer analysis + Hermes Agent project resonance calibration.
**Copyright:** Fair Use — methodology distillation.
**Last-verified:** 2026-06-16

## Summary

Authoritative rules for combining 2-3 strata layers into a single StoryKernel, and the resonance coefficient each combination produces. Multi-layer overlay is the difference between a "sharp" single-issue story and a "resonant" structural story.

## Heuristics

### Why multi-layer overlay amplifies resonance

**Single-layer stories** describe ONE structural force. Audience perceives them as "about X" — sharp, clear, but limited.

**Multi-layer stories** describe 2-3 structural forces acting on the same subjects. Audience perceives resonance — "this is bigger than X." The forces amplify each other because:
1. **Causal chains cross** (L1 institutional design causes L4 spatial exclusion)
2. **Symbolic density** increases (one image carries multiple meanings)
3. **Audience recognition** widens (more demographic groups see themselves in the story)

### The "1+1 > 2" principle

For two layers in compatible combination, resonance > sum of individual strengths. The amplification factor depends on:
- Causal linkage between layers
- Shared subject population
- Symbolic overlap potential

### Strata overlay coefficient matrix (2-layer combinations)

| Layer A ↓ / Layer B → | L1 | L2 | L3 | L4 | L5 | L6 |
|---|---|---|---|---|---|---|
| **L1** Institutional | - | 1.5 | 1.4 | **1.8** | 1.5 | 1.4 |
| **L2** Technological | 1.5 | - | 1.3 | 1.5 | **1.7** | 1.5 |
| **L3** Demographic | 1.4 | 1.3 | - | 1.6 | 1.4 | **1.6** |
| **L4** Spatial | **1.8** | 1.5 | 1.6 | - | 1.5 | 1.4 |
| **L5** Intergenerational | 1.5 | **1.7** | 1.4 | 1.5 | - | 1.5 |
| **L6** Psychosocial | 1.4 | 1.5 | **1.6** | 1.4 | 1.5 | - |

### The 3 canonical high-resonance overlays

#### L1 + L4 (resonance 1.8) — 制度-空间双重锁定

**Why it works:** Institutional design (L1) creates spatial分配 rules (L4) that compound disadvantage. Subjects are locked both legally and physically.

**Example:** 灵活就业政策(L1) + 人才房政策(L4) = 灵活就业者既无法获得社保(L1),也无法获得城市住房(L4),双重锁定。

#### L2 + L5 (resonance 1.7) — 技术-代际时代断层

**Why it works:** Technology (L2) renders父辈 skills obsolete; intergenerational contract (L5) breaks because父辈 can't advise子辈 on world they don't recognize.

**Example:** AI 替代文案岗位(L2) + 父母认为"读书改变命运"(L5) = 父辈无法理解子辈失业的真正原因,代际契约断裂。

#### L3 + L6 (resonance 1.6) — 人口-心灵沉默创伤

**Why it works:** Demographic shifts (L3) silently重组 social relationships; the psychological layer (L6) records the创伤 but cannot name the cause.

**Example:** 老龄化+少子化(L3) + 年轻人弥漫性孤独感(L6) = 心灵层的"沉默创伤"找不到具体原因,因为根源是人口结构的不可见变化。

### Strata overlay coefficient matrix (3-layer combinations)

**Rare but powerful.** 3-layer combinations produce resonance 2.5-3.0 when they form a "causal chain" (L1 → L2 → L4):

| Combination | Resonance | Causal chain |
|---|---|---|
| **L1 + L2 + L4** | 2.5 | 制度 → 技术 → 空间 (institutional policy enables tech replacement, which drives spatial exclusion) |
| **L2 + L3 + L6** | 2.3 | 技术 → 人口 → 心灵 (tech displacement accelerates demographic shift, deposits as psychological trauma) |
| **L1 + L4 + L5** | 2.4 | 制度 → 空间 → 代际 (institutional design spatially traps父辈, breaking intergenerational contract) |
| **L3 + L4 + L6** | 2.2 | 人口 → 空间 → 心灵 (demographic flow creates spatial displacement, deposits as psychological trauma) |

**3-layer with NO causal chain** (e.g., L1 + L3 + L5 unrelated) → resonance drops to 1.5 (worse than focused 2-layer).

### 4+ layer combinations: avoid

**Resonance drops below 1.5 for 4+ layers.** Why:
- Narrative overload — audience cannot track 4+ structural forces simultaneously
- Cognitive-resonance violation — per [`../../_shared/cognitive-resonance-metrics.md`](../../_shared/cognitive-resonance-metrics.md) §Scale 1, active-suspension concurrency ≤ 3
- Dramatic potential drops — too abstract to dramatize

**Hard rule:** maximum 3 layers per StoryKernel.

### Best-overlay selection algorithm

```
Given user input (topic + optional layer specification):

1. If user specifies single layer → coefficient = 1.0
2. If user specifies 2 layers → look up in 2-layer matrix
3. If user specifies 3 layers → check if causal chain exists; if yes, use 3-layer coefficient; if no, downweight
4. If user doesn't specify → recommend the highest-resonance 2-layer combo whose evidence_sources are available

Output: coefficient + amplification explanation
```

### Causal chain detection

A 3-layer combination forms a causal chain when:
- Layer X "causes" layer Y (X is upstream of Y in social process)
- Layer Y "causes" layer Z

**Causal directions:**
- L1 → L2 (institutional policy enables tech adoption)
- L2 → L4 (tech displacement drives spatial mobility)
- L1 → L4 (institutional policy allocates space)
- L4 → L5 (spatial trap breaks intergenerational contract)
- L3 → L6 (demographic shift deposits as psychological trauma)
- L2 → L3 (tech displacement changes demographic flow)
- L1 → L5 (institutional change breaks intergenerational contract)

**Non-causal (parallel) combinations:**
- L1 + L3 (institutional and demographic are parallel forces, not causal)
- L2 + L4 (tech and spatial are parallel)

For parallel combinations, use base 2-layer coefficient without amplification.

### Resonance computation example

User wants analysis of "灵活就业者困境":
- L1 (institutional): 灵活就业政策 → individual responsibility
- L4 (spatial): 人才房政策 → 高学历优先

**L1 + L4 combination:** coefficient = 1.8 (from matrix)

**Amplification explanation:**
"L1+L4 叠加使故事核从'制度悲剧'升级为'制度-空间双重锁定',共振强度 1+1=1.8(>2 的物理叠加)"

### Validation: is the amplification real?

**Empirical test:** Take 100 single-layer stories + 100 2-layer stories. Measure audience response (评论深度 + 转发率 + 完播率). 

**Expected result:** 2-layer stories outperform single-layer on:
- 评论深度 (comment depth): +35-50%
- 转发率 (share rate): +20-30%
- 完播率 (completion rate): +10-15%

**Per [`../../_shared/cognitive-resonance-metrics.md`](../../_shared/cognitive-resonance-metrics.md) §Scale 3 (narrative):** multi-layer stories have higher "identity projection" — more audience demographic groups see themselves in the structural conflict.

---

## Cross-references

- [`./strata-guide.md`](./strata-guide.md) — layer definitions
- [`./story-kernel-schema.md`](./story-kernel-schema.md) — `strata_overlay_coefficient` field
- [`../../_shared/cognitive-resonance-metrics.md`](../../_shared/cognitive-resonance-metrics.md) §Scale 3 — narrative-layer identity projection
