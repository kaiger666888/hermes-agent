# Consistency Stress Test (一致性压力测试)

**Source:** CLIP-I / DINO-I image-similarity literature + OpenClaw kais-character-designer stress-test doctrine + Hermes Agent benchmark calibration.
**Copyright:** Fair Use — methodology distillation.
**Last-verified:** 2026-06-16

## Summary

The 3-scene consistency stress test is the GATE between character variant generation and final character lock. **A character that has not passed stress test is NOT locked** — downstream experts must not consume an unlocked CharacterBible. This file defines the canonical 3 test scenes, the CLIP-I / DINO-I thresholds, and the failure-handling protocol.

## Heuristics

### Why stress test (and not just check the 4 anchors)

4D anchor verification (per [`./4d-anchor-system.md`](./4d-anchor-system.md)) confirms that 4 views of the same character are mutually consistent. But anchors are generated from the same prompt template — they're trivially similar.

The stress test verifies something stronger: **does the character survive 3 radically different scene contexts?** A character that drifts in different scenes will drift in actual production shots.

### The 3 canonical test scenes

| Scene | Full prompt | Strength | Verification target |
|---|---|---|---|
| **街头夜景** / Street night neon | `walking in busy street at night, neon lights, cyberpunk atmosphere, full body shot` | 0.40 | 远景一致性 (long-shot consistency: silhouette, outfit, hair outline) |
| **室内特写** / Indoor close-up crying | `close-up crying indoor, soft window light, emotional intensity, face only` | 0.55 | 面部一致性 (face consistency: eye color, scar, jawline) |
| **动作侧拍** / Running side view | `running dynamically, side view, motion blur, athletic action` | 0.35 | 动态一致性 (dynamic consistency: hair flow, outfit movement, body shape) |

**Why these 3 scenes specifically:**
- **街头夜景** tests low-strength long-shot — if character drifts here, drawer's full-body shots will drift.
- **室内特写** tests high-strength close-up — if character drifts here, drawer's portrait shots will drift.
- **动作侧拍** tests very-low-strength action — if character drifts here, animator's action shots will drift.

Together they cover the strength range (0.35-0.55) and shot-type range (long / close / action) that downstream experts will use.

### CLIP-I threshold

**CLIP-I** = cosine similarity between CLIP image embeddings of two images.

**Per-scene verification:**
- For each test scene, generate the image.
- Compute CLIP-I between generated image and the 3Q anchor (primary reference).
- **Pass threshold:** CLIP-I ≥ 0.80.

**Cross-scene aggregate:**
- Compute mean CLIP-I across the 3 scenes.
- **Pass threshold:** mean ≥ 0.82.
- **Distinct identity threshold:** mean ≥ 0.85 (character is robustly consistent).

### DINO-I threshold

**DINO-I** = cosine similarity between DINO self-supervised image embeddings.

DINO features focus more on shape and structure (vs CLIP which focuses on semantics + style). Use both for cross-validation.

**Per-scene:**
- DINO-I between generated image and 3Q anchor.
- **Pass threshold:** DINO-I ≥ 0.78.

**Cross-scene aggregate:**
- Mean ≥ 0.80.

### Why CLIP-I 0.80 and not higher

Empirical calibration:
- Same character, same scene, regen: CLIP-I = 0.90-0.95
- Same character, different reasonable scenes: CLIP-I = 0.75-0.88
- Different character, same style: CLIP-I = 0.55-0.70
- Different character, different style: CLIP-I = 0.30-0.50

0.80 sits in the "same character, different scene" upper range. Setting it higher (e.g., 0.85) would reject legitimate scene-induced variance; lower (e.g., 0.70) would accept drift.

### Why both CLIP-I and DINO-I

- CLIP-I catches **style/semantic drift** (e.g., character's outfit changing color, hair becoming different texture).
- DINO-I catches **shape/structural drift** (e.g., face shape changing, body proportions shifting).
- Both must pass — one passing and the other failing indicates a specific drift mode.

**Common failure patterns:**

| CLIP-I | DINO-I | Interpretation |
|---|---|---|
| Low | Low | Wholesale identity drift — regenerate variants |
| Low | Pass | Style drift only — refine STYLE_CORE or negative_traits |
| Pass | Low | Shape drift — refine STYLE_IDENTITY physical tokens |
| Pass | Pass | Consistent — lock |

### Strength parameter per scene

The strength parameter controls how strongly the reference image influences the generated image:

| Strength | Effect | Use case |
|---|---|---|
| 0.30-0.40 | Low lock, high pose freedom | Action shots, dynamic scenes |
| 0.40-0.50 | Medium lock, balanced | Default for most scenes |
| 0.50-0.60 | High lock, low pose freedom | Face close-ups, portraits |

**Test scenes use the extremes of this range** to ensure the character holds at both low and high strength.

### Pass / fail decision matrix

| All 3 scenes pass (CLIP-I ≥ 0.80 AND DINO-I ≥ 0.78) | Action |
|---|---|
| Yes | **Lock** the character; downstream experts may consume |
| No (1 scene fails) | **Investigate** the failing scene; try 1 regeneration; if still fails, return to variant selection |
| No (2 scenes fail) | **Reject** the variant; return to Step 2 (variant tournament) |
| No (3 scenes fail) | **Catastrophic** — likely STYLE_PREFIX broken; return to step 1 (STYLE_PREFIX construction) |

### Stress test CLI invocation pattern

The stress test is run via the character_designer's processing pipeline:

```
Input: candidate CharacterBible (variant-selected, anchors generated)
  ↓
For each of 3 test scenes:
  - Generate image with anchor reference + scene-specific prompt + strength
  - Compute CLIP-I vs 3Q anchor
  - Compute DINO-I vs 3Q anchor
  - Record pass/fail
  ↓
Aggregate:
  - mean CLIP-I across 3 scenes
  - mean DINO-I across 3 scenes
  - per-scene verdict
  ↓
Output: StressTestResults JSON block (consumed by character_designer lock decision)
```

**Manual check recommendation:** in addition to CLIP-I / DINO-I, ask a human reviewer: "Are these 3 images the same person?" Human inspection catches subtle drifts (e.g., character looks "tired" in one scene, "alert" in another) that similarity scores miss.

### Common failure modes and fixes

| Failure mode | Likely cause | Fix |
|---|---|---|
| Indoor close-up fails (CLIP-I < 0.80) | Face identity insufficient in STYLE_IDENTITY | Add more face-specific tokens (eye shape, nose type, jawline) |
| Running side view fails | Body shape drifts at low strength | Add body-specific tokens (height, build, posture) |
| Street night neon fails | Outfit color/shape changes under colored lighting | Add explicit outfit tokens to STYLE_IDENTITY |
| All 3 fail at low CLIP-I | STYLE_PREFIX incoherent | Restart at STYLE_PREFIX construction |
| All 3 pass but cross-character CLIP-I too high (> 0.70) | Characters not distinct enough | Add differentiating traits to STYLE_IDENTITY |

### Why stress test, not just visual inspection

**LLM-judge cannot reliably perform this test.** A GPT-class model:
- Tokenizes images, losing fine-grained spatial detail
- Has been shown to be biased toward "looks similar" judgments
- Cannot compute CLIP-I / DINO-I directly

**Therefore:** the stress test MUST be backed by CLIP-I / DINO-I objective scores. Human visual inspection is a complement (catches subtle expression drift), not a substitute.

---

## Cross-references

- [`./4d-anchor-system.md`](./4d-anchor-system.md) — anchor verification is a prerequisite to stress test
- [`./layered-style-prefix.md`](./layered-style-prefix.md) — STYLE_PREFIX issues often surface as stress-test failures
- [`./character-bible-schema.md`](./character-bible-schema.md) — `consistency_lock.stress_test_results` schema
- [`../../_shared/known-external-models.yaml`](../../_shared/known-external-models.yaml) — `<clip_eval>` and `<dino_eval>` placeholders resolve here
