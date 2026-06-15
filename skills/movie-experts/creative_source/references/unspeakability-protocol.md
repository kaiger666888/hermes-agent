# Unspeakability Protocol (不可言说性评估协议)

**Source:** Adapted from OpenClaw kais-soul-radar unspeakability scoring + CN platform regulatory framework (网信办 / 广电总局 / 各平台 community guidelines).
**Copyright:** Fair Use — methodology distillation from publicly available platform guidelines.
**Last-verified:** 2026-06-16

## Summary

The authoritative 10-point scoring protocol for assessing how "off-limits" a StoryKernel is for production on CN platforms. The 4 sub-dimensions (political / platform / audience / regulatory) combine into an aggregate score that gates whether the kernel can be produced, and on which platform.

## Heuristics

### The 4 sub-dimensions

| Dimension | Range | What it measures |
|---|---|---|
| `political_sensitivity` | 1-10 | 政治敏感度:是否触及核心政治议题(领导人 / 主权 / 历史) |
| `platform_algorithm_risk` | 1-10 | 平台算法风险:是否会被推荐算法降权 / 标记 |
| `audience_discomfort` | 1-10 | 观众不适度:是否会引发大规模举报 / 差评 |
| `regulatory_redline` | 1-10 | 监管红线:是否触及明文禁止(广电总局 / 网信办) |

### Aggregate score formula

```
unspeakability_score = round(
  political_sensitivity * 0.20 +
  platform_algorithm_risk * 0.30 +
  audience_discomfort * 0.15 +
  regulatory_redline * 0.35
)
```

**Why these weights:**
- `regulatory_redline` (0.35): hard cutoff — regulatory rejection is non-negotiable
- `platform_algorithm_risk` (0.30): soft cutoff — algorithm降权 kills distribution
- `political_sensitivity` (0.20): high但 may be mitigated by reframing
- `audience_discomfort` (0.15): lowest weight — discomfort can be productive (challenging content finds niche audience)

### Scoring rubric per dimension

#### political_sensitivity

| Score | Description | Example |
|---|---|---|
| 1-2 | No political content | Pure romantic comedy |
| 3-4 | General social issues (employment, housing) | 灵活就业政策 |
| 5-6 | Policy critique with named institutions | "平台经济 needs regulation" |
| 7-8 | Sensitive historical / regional topics | Specific minority region issues |
| 9-10 | Direct political criticism | (avoid) |

#### platform_algorithm_risk

| Score | Description |
|---|---|
| 1-2 | Algorithm-friendly (positive, mainstream) |
| 3-4 | Neutral (no algorithm preference) |
| 5-6 | Mild risk (some keywords flagged) |
| 7-8 | Moderate risk (algorithm deprioritizes) |
| 9-10 | Hard risk (content hidden / removed) |

#### audience_discomfort

| Score | Description |
|---|---|
| 1-2 | Universally comfortable |
| 3-4 | Slight discomfort, easily digestible |
| 5-6 | Moderate discomfort, niche appeal |
| 7-8 | Strong discomfort, requires warning labels |
| 9-10 | Extreme discomfort, mass rejection |

#### regulatory_redline (硬性)

| Score | Description |
|---|---|
| 1-2 | No regulatory concern |
| 3-4 | General content, 备案 standard |
| 5-6 | Touches边缘 topics, careful handling needed |
| 7-8 | Approaches regulatory红线, requires pre-review |
| 9-10 | Clear红线 violation (e.g., 涉政 / 涉黄 / 涉暴 / 涉恐) |

### Aggregate score interpretation

| Score | Verdict | Action |
|---|---|---|
| 1-2 | 主流安全 | Produce as-is on any platform |
| 3-4 | 谨慎处理 | Minor reframing; standard release |
| 5-6 | 平台分化 | Per-platform strategy needed (see [`#platform-strategy-matrix`]) |
| 7-8 | 高风险 | Major reframing OR limited platform release |
| 9-10 | 禁忌 | **VETO** — cannot be made on any CN platform |

### Platform strategy matrix (per CN platform)

| Platform | Tolerance for unspeakability | Best-fit content | Risk content |
|---|---|---|---|
| **抖音** | 1-5 (cautious) | Mass entertainment, daily life | Structural critique, policy discussion |
| **快手** | 1-6 (moderate) | Town life, grassroots stories | Class conflict too explicit |
| **小红书** | 1-6 (moderate) | Female perspective, lifestyle | Political topics |
| **微信小程序** | 1-7 (tolerant) | Long-form serialized drama | Sensitive political |
| **B站** | 1-6 (moderate) | Youth culture, niche interests | Mainstream商业 forced |
| **视频号** | 1-5 (cautious) | Family-friendly, official media | Critique of official policy |

### Per-platform compliance path generation

For a StoryKernel with `unspeakability_score ≥ 5`, generate per-platform paths:

#### 抖音 compliance path (when score ≥ 5)

**Strategy:** individual-heroic narrative reframing (去除 structural critique)

**Pattern:**
- Structural critique: "灵活就业政策将社保责任转移给个人,每个选项都通向脆弱"
- 抖音 reframing: "灵活就业小伙通过个人努力突破困境,逆袭成为人生赢家"

**Trade-off:** loses structural power; gains algorithm distribution.

#### 快手 compliance path (when score ≥ 6)

**Strategy:** preserve partial structural critique via "小镇青年" perspective

**Pattern:**
- Story stays grounded in structural conflict
- But framed as "personal experience" rather than systemic analysis
- 小镇青年 audience is more tolerant of structural themes

#### 小红书 compliance path (when score ≥ 6)

**Strategy:** female perspective re-centering

**Pattern:**
- Re-center on female protagonist experiencing the structural conflict
- Platform's female-primary audience is more receptive to structural critique via personal narrative

#### 微信小程序 compliance path (when score ≥ 7)

**Strategy:** long-form serialization allows gradual topic introduction

**Pattern:**
- Use 10-30 episode format to introduce structural themes gradually
- Early episodes use safe framing; later episodes deepen critique
- Audience commitment enables higher tolerance

### Hard VETO conditions

StoryKernel is VETO regardless of dramatic_potential if:

- ❌ `regulatory_redline = 10` (clear regulatory violation)
- ❌ `political_sensitivity ≥ 9` AND `regulatory_redline ≥ 7`
- ❌ `unspeakability_score = 10` (aggregate)

When VETO triggered:
- Mark StoryKernel as `vetoed: true`
- Do not pass to downstream experts
- Output vetoed report to user

### Daily scan filtering

For automated daily kernel scanning:

```
filter:
  - exclude if unspeakability_score >= 9
  - downrank if unspeakability_score >= 7 (deprioritize in topic recommendations)
  - highlight if unspeakability_score in 4-6 range (sweet spot: meaningful + producible)
  - skip if unspeakability_score <= 2 (too safe, likely uninteresting)
```

### Calibration and refresh

**Platform guidelines change quarterly.** This protocol's thresholds must be re-validated every quarter against:
- 网信办 latest announcements
- 广电总局 latest备案 regulations
- Each platform's community guideline updates

**Stale-flag:** if Last-verified > 90 days, audit scripts flag this file.

### Why this matters (cost-of-failure analysis)

**Cost of producing a kernel with unspeakability_score = 8 without proper protocol:**
- 60% chance of regulatory rejection post-production
- 30% chance of platform algorithm deprioritization (kills distribution)
- 10% chance of mass audience rejection

**Expected loss:** 70-90% of production cost.

**Cost of running unspeakability protocol:** ~5 minutes per kernel.

**ROI:** protocol pays for itself after first prevented failure.

---

## Cross-references

- [`./story-kernel-schema.md`](./story-kernel-schema.md) — `unspeakability_*` schema
- [`./strata-guide.md`](./strata-guide.md) — each layer has typical unspeakability range (annotated inline)
- [`../../compliance_marketing/SKILL.md`](../../compliance_marketing/SKILL.md) — downstream consumer of `platform_compliance_paths`
- [`../../_shared/quality-rubric.md`](../../_shared/quality-rubric.md) — publishing gate uses unspeakability as input
