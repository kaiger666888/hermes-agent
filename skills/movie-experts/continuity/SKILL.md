---
name: continuity
description: "Continuity Expert: 4-dimension cross-shot auditing (face/wardrobe/color/object) + eyeline match + 180° axis + screen direction continuity for AI film."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm, hermes_llm_vision]
metadata:
  hermes:
    tags: [movie, continuity, consistency, face-matching, color-check, cross-shot, eyeline-match, axis-continuity]
    related_skills: [drawer, animator, colorist, style_genome, screenplay, cinematographer, production]
    expert_id: continuity
    metrics: [face_similarity, color_consistency, style_uniformity]
---

# Continuity Expert (一致性专家)

4-dimension cross-shot consistency auditor for AI-generated films: face + wardrobe + color + object coherence, plus eyeline match + 180° axis + screen direction continuity verification. Uses `hermes_llm_vision` for image comparison. **Phase 5 v1.5 RAG uplift** per REFACTOR-rest-02.

## When to use this skill

The user needs to verify visual consistency across shots, detect character face mismatches, audit color grading continuity, validate style uniformity, or verify eyeline/axis/screen direction continuity. Uses `hermes_llm_vision` for image comparison.

## References

本专家所有 audit 协议与 eyeline/axis 阈值由下列 2 个 refs 独占定义(Phase 5 v1.5 light-refs uplift per REFACTOR-rest-02):

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/cross-shot-auditing.md`](./references/cross-shot-auditing.md) | 执行 cross-shot audit 或 写 audit report 前 | 4-dimension audit matrix(face / wardrobe / color / object)+ per-dimension metric 阈值 + within-scene vs cross-scene vs cross-episode 严格度 + audit timing + audit_report.json schema + 失败 handoff 协议 |
| [`references/eyeline-match-protocol.md`](./references/eyeline-match-protocol.md) | 验证 eyeline match 或 180° axis continuity 前 | Eyeline match 3 rule + mismatch 案例与修正 + cross-cut axis verification + cross-scene axis reset + screen direction 4 状态 audit + 与 cross-shot-auditing.md 集成 |

## Knowledge Retrieval

在执行任何 audit 或 continuity verification 前,按以下顺序检索上下文(2 个检索主题):

- **4-dimension audit(face/wardrobe/color/object)+ metric 阈值 + audit report schema** —— 详见 [`references/cross-shot-auditing.md`](./references/cross-shot-auditing.md)
- **Eyeline match 3 rule + 180° axis continuity + screen direction audit** —— 详见 [`references/eyeline-match-protocol.md`](./references/eyeline-match-protocol.md)

**若当前 runtime 中有 memory / RAG 工具**,使用以下查询范围:

```
tags="expert:continuity,domain:cross-shot-auditing"
tags="expert:continuity,domain:eyeline-match-protocol"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件。

## Role & Philosophy

- Consistency is the invisible backbone of cinematic immersion
- Audiences notice inconsistency before they notice beauty
- Every frame must belong to the same universe

## Core Capabilities

- Face/body similarity detection across varied poses and lighting
- Color temperature and grading consistency analysis
- Style uniformity verification against director vision
- Environmental continuity tracking (props, lighting, weather, time-of-day)

## Output Format

- `continuity_report.json` per scene: pass/fail per dimension, deviation scores
- Annotated diff images for failed checks (current vs reference)
- Correction prompts for drawer/animator to fix inconsistencies

## Key Parameters

### Face Similarity Detection
- **model**: ArcFace / InsightFace (512-dim embedding)
- **similarity_threshold**: 0.88 (production), 0.80 (preview)
- **reference_frame**: first frame of each shot sequence as anchor
- **detection_zones**: eye distance, nose bridge, jawline, face contour

### Color Consistency
- **color_space**: CIELAB (perceptually uniform)
- **color_temp_tolerance**: ±200K (adjacent shots)
- **contrast_deviation**: <= 5% (SSIM)
- **saturation_deviation**: ΔS <= 0.05 (HSL)
- **histogram_correlation**: >= 0.90 (adjacent shots)

### Style Consistency
- **style_encoding**: style_genome 5D vector, L2 distance <= 0.15
- **render_consistency**: CLIP score >= 0.92
- **grain_deviation**: noise_level Δ <= 0.03

### GPU Budget
- ArcFace: ~1GB per face pair | CLIP: ~2GB | Batch: 8-16 frames | Total: <= 4GB

## Style Rules

### Consistency Dimensions
1. Character (weight 0.40) — face, hair, clothing, body type
2. Clothing/Props (weight 0.25) — stable across shots
3. Color/Lighting (weight 0.20) — temperature, contrast, saturation
4. Environment (weight 0.15) — light sources, props, weather, time

### Tolerance Rules
- ±200K color temp (narrative time passage)
- ±5% exposure (natural light fluctuation)
- No face feature mutation (same character, same scene)
- No unexplained prop appearance/disappearance
- No style jumps without narrative transition

## Workflow

1. **Anchor Extraction** — First frame per shot sequence as reference baseline
2. **Face Detection** — Extract character face embeddings from all frames
3. **Color Analysis** — Compute CIELAB deviation between frames
4. **Environment Scan** — Compare foreground/background element consistency
5. **Style Verification** — Validate render style alignment with `style_genome`
6. **Violation Flagging** — Generate `continuity_report.json` (pass/fail + deviations)
7. **Correction Suggestions** — Generate `correction_prompt` for failed items

## Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| face_similarity | >= 0.88 |
| color_consistency | >= 0.85 |
| style_uniformity | >= 0.85 |
| environment_consistency | >= 0.80 |

## Collaboration

- **<- drawer**: first_frame + production frames
- **<- animator**: video frame sequences (keyframe sampling)
- **<- colorist**: CxSxZ color intent encoding
- **<- style_genome**: style genome reference vector
- **<- screenplay**: scene descriptions (tolerance judgment)
- **-> drawer/animator**: correction_prompt for failed frames
- **-> editor**: continuity_pass mark (gate for proceeding)

## What NOT to do

- Don't approve frames with face_similarity < 0.88
- Don't ignore style deviations > L2 distance 0.15
- Don't run without style_genome reference (no baseline = no audit)
- Don't batch process without anchor frames per shot
- Don't flag narrative-justified changes (time passage, dream sequences)
