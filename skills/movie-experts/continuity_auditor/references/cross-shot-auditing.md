# Cross-Shot Auditing — Face/Color/Style/Object Matching Heuristics

**Source:** Reisz & Millar *The Technique of Film Editing* (2nd ed, 1968);Dmytryk *On Film Editing* (1984);Bordwell & Thompson *Film Art* (11th ed, 2020);Wang et al. *ArcFace* (2019 CVPR);Schroff et al. *FaceNet* (2015 CVPR)。
**Copyright:** Fair Use — paraphrased heuristics; no proprietary content. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 continuity 专家在 **cross-shot consistency audit** 时的**权威源**。它涵盖 4 维度(face / wardrobe / color / object)+ per-dimension metric 阈值 + audit protocol。

## 4-Dimension Audit Matrix

### 关键 heuristic 1 (load-bearing): 4 维度 audit 阈值

| 维度 | Metric | 阈值 | 失败处理 |
|------|--------|------|----------|
| **Face** | ArcFace/FaceNet cosine similarity | ≥ 0.80 | Re-generate shot |
| **Wardrobe** | CLIP image embedding cosine + color histogram Bhattacharyya | ≥ 0.95 / ≤ 0.10 | Re-generate shot |
| **Color** | ΔE2000 / CIELAB distance | ≤ 5.0 production / ≤ 8.0 preview | colorist re-grade |
| **Object** | Object detection IoU + CLIP object embedding | ≥ 0.70 / ≥ 0.90 | Re-generate or prop swap |

### 关键 heuristic 2: Within-scene vs Cross-scene audit

| 范围 | 严格度 | 备注 |
|------|--------|------|
| **Within-scene** | 极严格(zero tolerance for face/wardrobe/object) | 同场景同 character 必须 1:1 一致 |
| **Cross-scene(同一 episode)** | 严格(face ID + wardrobe baseline 一致) | 允许 lighting / angle 变化 |
| **Cross-episode** | 中等(face ID 一致,允许 wardrobe arc 变化) | per wardrobe-per-scene.md §Arc wardrobe |

### 关键 heuristic 3: Audit timing

- **Per-shot post-generation:** 4 维度 audit immediately after generation
- **Per-scene completion:** Within-scene consistency check
- **Per-episode completion:** Cross-scene + cross-episode check
- **Pre-distribution:** Final full audit + compliance_marketing review

---

## Audit Report Schema

### 关键 heuristic 4: audit_report.json 标准 schema

```json
{
  "scene_id": "S01E01_scene_003",
  "shots_audited": ["shot_001", "shot_002", "shot_003"],
  "audit_results": {
    "face": {
      "shot_001_vs_002": {"cosine_similarity": 0.92, "pass": true},
      "shot_002_vs_003": {"cosine_similarity": 0.88, "pass": true}
    },
    "wardrobe": {
      "shot_001_vs_002": {"clip_cosine": 0.97, "bhattacharyya": 0.05, "pass": true}
    },
    "color": {
      "shot_001_vs_002": {"delta_e2000": 3.2, "pass": true}
    },
    "object": {
      "shot_001_vs_002": {"iou": 0.85, "clip_cosine": 0.95, "pass": true}
    }
  },
  "overall_pass": true,
  "failures": [],
  "re_generate_required": []
}
```

---

## 与 production / colorist handoff

### 关键 heuristic 5: 失败时的 handoff 协议

| 失败维度 | Handoff to | Action |
|---------|------------|--------|
| Face consistency | drawer + production | Re-train LoRA 或 调整 IP-Adapter weight |
| Wardrobe | drawer + production | Re-generate with wardrobe baseline reference |
| Color | colorist | Re-grade shot |
| Object | drawer + scene_builder | Re-generate 或 prop swap |

---

## Anti-Patterns

### 关键 heuristic 6: Continuity 5 大 anti-pattern

1. **No automated audit anti-pattern:** 凭肉眼判断。**Mitigation:** 4-metric 自动化。
2. **Within-scene tolerance anti-pattern:** Within-scene 允许 face ID drift。**Mitigation:** zero tolerance。
3. **Cross-episode drift ignored anti-pattern:** 跨 episode face ID drift 未处理。**Mitigation:** cross-episode audit。
4. **No audit report anti-pattern:** 无 audit report 文件。**Mitigation:** audit_report.json per scene。
5. **Audit timing wrong anti-pattern:** 仅在 final distribution audit。**Mitigation:** per-shot + per-scene + per-episode。

---

## Glossary

- **Face embedding:** ArcFace/FaceNet 128/512-dim face vector。
- **CLIP image embedding:** CLIP 512-dim image vector。
- **ΔE2000:** CIELAB color difference metric。
- **IoU:** Intersection over Union,object detection metric。
- **Bhattacharyya distance:** Histogram similarity metric。

---

*Generated: 2026-06-15 as part of Phase 5 REFACTOR-rest-02 (continuity RAG uplift).*
*Source provenance: Reisz & Millar 1968 / Dmytryk 1984 / Bordwell 2020 / Wang et al. 2019 ArcFace / Schroff et al. 2015 FaceNet — fair use paraphrase + short technical phrases only.*
