# Temporal Consistency — CLIP-T + LPIPS + Character ID Preservation

**Source:** Radford et al. *CLIP* (2021 ICML);Zhang et al. *LPIPS* (2018 CVPR);Esser et al. *CLIP-Temporal* extension literature (2022-2024);Tektas *Aesthetic Predictor* literature;Hermes animator deployment notes (2024-2026)。
**Copyright:** Fair Use — paraphrased metric definitions + heuristics; no proprietary model weights verbatim. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 animator 专家在 **temporal consistency(跨 frame 视觉一致性)** 验证时的**权威源**。它涵盖 CLIP-T + LPIPS + character ID embedding 三层 metric + 失败 fallback。

## 三层 Temporal Consistency Metric

### 关键 heuristic 1 (load-bearing): CLIP-T + LPIPS + Face embedding 阈值

| Metric | 阈值 | 用途 |
|--------|------|------|
| **CLIP-T** (cosine similarity between adjacent frames' CLIP embeddings) | ≥ 0.85 | 跨 frame 视觉风格一致性 |
| **LPIPS** (Learned Perceptual Image Patch Similarity) | ≤ 0.20 | 跨 frame perceptual 差异(lower = more similar) |
| **Face embedding cosine similarity** | ≥ 0.80 | 跨 frame character ID 一致性(per ArcFace / FaceNet)|
| **Object detection IoU** | ≥ 0.70 | 跨 frame object 位置一致性 |

**4 层 all pass:** temporal consistency strong(可用于 production)
**任一层 fail:** temporal consistency weak(需 re-generate 或 post-process)

### 关键 heuristic 2: Per-clip metric 抽样

每个 5s clip(典型 24fps × 5s = 120 frames)抽样 protocol:
- Sample 10 frames(均匀分布,~每 12 frames 一帧)
- 计算 9 个 adjacent-pair metrics(CLIP-T / LPIPS / Face embedding)
- 计算 10-frame average 与 baseline I-frame 的 deviation

**抽样帧数 trade-off:**
- 10 frames:快 + 误差大(典型 preview check)
- 30 frames:中 + 误差中(典型 production check)
- 120 frames(all):慢 + 完整(postmortem 分析)

---

## Character ID Preservation

### 关键 heuristic 3: Character ID drift detection

per [`../production/references/casting-lora-spec.md`](../production/references/casting-lora-spec.md) §Character ID Cross-Shot Consistency:

- **Cross-frame face embedding drift:** 跨 frame face embedding σ ≤ 0.05(同一 character 不应漂移)
- **Cross-clip face embedding drift:** 跨 clip face embedding σ ≤ 0.10(允许更大,因为 lighting / angle 变化)
- **Identity failure threshold:** face embedding cosine similarity < 0.70 → character ID 失败,必须 re-generate

### 关键 heuristic 4: Temporal flicker detection

**Flicker:** 跨 frame 的 unwanted visual variation(无 narrative motivation)。

**Flicker detection 协议:**
1. 计算 per-pixel frame-to-frame difference
2. 若 mean pixel difference > 0.15(无 narrative motivation)→ flicker detected
3. Flicker mitigation:
   - Frame interpolation(RIFE / FILM)平滑 transition
   - Add temporal smoothing filter
   - Re-generate clip with higher num_inference_steps

---

## Object Consistency

### 关键 heuristic 5: Object permanence 协议

跨 frame 的 object 必须保持:
- **位置:** Object detection IoU ≥ 0.70 跨 adjacent frames
- **Appearance:** Object CLIP embedding cosine similarity ≥ 0.90
- **Color:** Color histogram Bhattacharyya distance ≤ 0.10

**失败处理:** Object 在 frame N+1 突然消失 / morphing / color shift → temporal consistency 失败,re-generate。

---

## Anti-Patterns

### 关键 heuristic 6: Temporal consistency 5 大 anti-pattern(规避)

1. **No metric verification anti-pattern:** 凭肉眼判断 temporal consistency。**Mitigation:** 4 层 metric 自动化验证。
2. **Single-frame preview anti-pattern:** 仅看 1 frame 决定 clip quality。**Mitigation:** ≥10 frames 抽样。
3. **Character ID drift uncorrected anti-pattern:** 允许 face embedding drift > 0.05。**Mitigation:** σ ≤ 0.05 + re-generate if failed。
4. **Flicker ignored anti-pattern:** Visible flicker 但不处理。**Mitigation:** RIFE / FILM 平滑。
5. **Object morphing uncorrected anti-pattern:** Object 在 frame 间 morphing。**Mitigation:** Object detection IoU ≥ 0.70。

---

## Glossary

- **CLIP-T:** Temporal CLIP,跨 frame CLIP embedding cosine similarity。
- **LPIPS:** Learned Perceptual Image Patch Similarity,跨 frame perceptual 差异。
- **Face embedding:** ArcFace / FaceNet 等 face 识别模型的 embedding。
- **Flicker:** 跨 frame unwanted visual variation。
- **Frame interpolation:** RIFE / FILM 等算法生成中间 frame。

---

*Generated: 2026-06-15 as part of Phase 5 REFACTOR-rest-10 (animator RAG uplift).*
*Source provenance: Radford et al. 2021 CLIP / Zhang et al. 2018 LPIPS / Esser et al. CLIP-Temporal literature / Hermes deployment notes — fair use paraphrase + short technical phrases only.*
