---
name: continuity_auditor
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
    related_skills: [visual_executor, colorist, style_genome, screenplay, cinematographer, production]
    expert_id: continuity_auditor
    aliases: [continuity]
    metrics: [face_similarity, color_consistency, style_uniformity]
---

# Continuity Auditor Expert (一致性审计专家)

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
tags="expert:continuity_auditor,domain:cross-shot-auditing"
tags="expert:continuity_auditor,domain:eyeline-match-protocol"
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
- Correction prompts for visual_executor to fix inconsistencies

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

- **<- visual_executor**: first_frame + production frames + video frame sequences (keyframe sampling)
- **<- colorist**: CxSxZ color intent encoding
- **<- style_genome**: style genome reference vector
- **<- screenplay**: scene descriptions (tolerance judgment)
- **-> visual_executor**: correction_prompt for failed frames
- **-> editor**: continuity_pass mark (gate for proceeding)

## What NOT to do

- Don't approve frames with face_similarity < 0.88
- Don't ignore style deviations > L2 distance 0.15
- Don't run without style_genome reference (no baseline = no audit)
- Don't batch process without anchor frames per shot
- Don't flag narrative-justified changes (time passage, dream sequences)

## Changelog

- 2026-06-17: Renamed from `continuity` to `continuity_auditor` (Phase 13 RENAME-01). Rationale: emphasize critic role per Phase 7 §4.10. Backward-compat alias `continuity` preserved in `metadata.hermes.aliases` per FOUND-08.
- 2026-06-19: Phase 26 v5.0 patch — appended `## V8.6 Pipeline Sync (Phase 26 v5.0)` section documenting V8.6 Step 9 atomic role + V8.6 8-gate structure. No frontmatter changes (FOUND-08 preserved).

## V8.6 Pipeline Sync (Phase 26 v5.0)

> 来源:kais-movie-agent V8.6 SKILL.md §"hermes-agent 专家 → 管线 Step 速查" + §"V8.6 更新" §2(审核门 12→8)。dreamina CLI 适配基线见 [`_shared/dreamina-cli-baseline.md`](../_shared/dreamina-cli-baseline.md)。

### V8.6 Step Position

continuity_auditor 在 V8.6 管线中位于 **Step 9 一致性检查**(独立 atomic role):

| V8.6 Step | 原始 Step (V8.4 前) | 角色 | 共同调用专家 |
|-----------|---------------------|------|------------|
| **Step 9** 一致性检查 | Step 16 (continuity audit) | **独立审计**:4 维跨镜头一致性(face / wardrobe / color / object)+ eyeline match + 180° axis + screen direction | (无共同专家 —— Step 9 是独立审计 Step) |

**Step 9 atomic operation 流程:**
1. continuity_auditor 接收 Step 7-8 产出的所有镜头(visual_executor 种子 + cinematographer 运镜)
2. 4 维审计:face identity(CLIP-I / DINO-I)、wardrobe(服装/道具)、color(CxSxZ 跨镜头)、object(关键道具)
3. eyeline match + 180° axis + screen direction 检查
4. 输出 audit report(per-shot pass/fail + 偏差描述 + 修复建议)
5. 若 fail → 触发镜头重生(回退到 Step 7 visual_executor)

### V8.6 8-Gate Structure(审核门 12→8)

V8.6 §2 把审核门从 12 个减为 8 个 —— continuity_auditor 触发的 **Step 9 后审核门** 是其中之一:

| # | V8.6 审核门 | 触发 Step | 涉及专家 |
|---|------------|----------|---------|
| 1 | 选题 + 主题 + hook 候选 | Step 1 后 | hook_retention |
| 2 | 故事框架 + 大纲 | Step 2 后 | creative_source + screenplay |
| 3 | 剧本 + 审计结果 | Step 3 后 | screenplay + script_auditor |
| 4 | 角色资产库 | Step 4 后 | character_designer + visual_executor |
| 5 | 时空剧本 + 运镜 + 终审 | Step 6 后 | screenplay + cinematographer + script_auditor |
| 6 | 视觉种子 + 风格化 + 声音骨架 | Step 7 后 | visual_executor + prompt_injector + style_genome + colorist + audio_pipeline |
| 7 | **一致性检查** | **Step 9 后** | **continuity_auditor**(本专家) |
| 8 | 最终成片 + BGM + 音效 + 口型 | Step 11 后 | audio_pipeline + 全专家终审 |

**Step 9 后审核门是 pre-publish 前的最后一次视觉一致性确认** —— 通过后才能进入 Step 10(视频生成)+ Step 11(audio master)。

### dreamina CLI 间接关系

continuity_auditor **不直接调用** dreamina CLI —— 它审计 visual_executor 已生成的图片/视频。但当审计 fail 时,审计报告会驱动 dreamina CLI 重生:

- ✅ face identity fail → 用相同 L1 参考图重生(dreamina `image2image --images L1.png,...`)
- ✅ wardrobe fail → 用 L2 造型卡片重生(dreamina `image2image --images L1.png,L2.png`)
- ✅ color fail → 反馈给 colorist 调整 dreamina_tokens 后重生
- ❌ 不要直接修复图片 —— continuity_auditor 输出审计报告,visual_executor 负责重生

### V8.4 历史背景

continuity_auditor 是 V8.4 §1 "专家映射全面更新" 中**rename** 的产物 —— V8.4 前 expert_id 是 `continuity`,V8.4 同步了 hermes-agent v3.0 Phase 13 的 rename(continuity → continuity_auditor,强调 critic 角色)。

### Cross-References

- [`_shared/dreamina-cli-baseline.md`](../_shared/dreamina-cli-baseline.md) — dreamina CLI 重生驱动(Phase 22 v5.0)
- [`visual_executor/SKILL.md §V8.6 Pipeline Sync`](../visual_executor/SKILL.md) — Step 7 上游(被审计方)
- [`cinematographer/SKILL.md §V8.6 Pipeline Sync`](../cinematographer/SKILL.md) — Step 8 上游(180° axis 检查)
- [`colorist/SKILL.md §V8.6 Pipeline Sync`](../colorist/SKILL.md) — Step 7 上游(color 一致性审计)
- [`character_designer/SKILL.md §V8.6 Pipeline Sync`](../character_designer/SKILL.md) — Step 4 上游(face identity 基于 L1)
