# Character Consistency LoRA — Training + IP-Adapter + InstantID

**Source:** Hu et al. *LoRA: Low-Rank Adaptation* (2021 arXiv:2106.09685);Ye et al. *IP-Adapter* (2023 arXiv:2308.06721);Wang et al. *InstantID* (2024 arXiv:2401.07519);Kohya_ss SDXL/FLUX LoRA training guides (github.com/bmaltais/kohya_ss);Civitai community character consistency best-practice guides (2024-2026)。
**Copyright:** Fair Use — paraphrased training + inference protocols; no proprietary LoRA weights verbatim. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 drawer 专家在 **character consistency(跨 shot character ID 一致)** 决策时的**权威源**。它涵盖 LoRA + IP-Adapter + InstantID 三种方法的对比 + 选择 + 组合协议。

## 三种 Character Consistency 方法对比

### 关键 heuristic 1 (load-bearing): LoRA vs IP-Adapter vs InstantID

| 方法 | 训练需求 | Per-shot 调整 | 速度 | 一致性强度 | 适合场景 |
|------|---------|---------------|------|------------|----------|
| **LoRA** | 必需(30-60min)| 不灵活(scale 调整)| 快 | 强 | 固定 character × 多 shot |
| **IP-Adapter** | 不需要(per-image)| 灵活(weight 调整)| 中 | 中 | Variable wardrobe / lighting |
| **InstantID** | 不需要(per-image)| 中(face ID focus)| 中 | 强(face)| 重点 face consistency |

### 关键 heuristic 2: 三方法组合协议

短剧 production 通常组合使用:

```yaml
# 典型 character consistency 配置
character: protagonist_main
consistency_stack:
  lora:
    path: asset_library/characters/protagonist_main/lora_weights.safetensors
    scale: 0.85  # 强 identity
  ip_adapter:
    image: asset_library/characters/protagonist_main/baseline_iframes/scene_001.png
    weight: 0.40  # 中等(避免 over-constraint)
  instantid:
    face_image: asset_library/characters/protagonist_main/face_baseline.png
    weight: 0.60  # 强 face ID
```

**组合强度和:**
- LoRA 0.85 + IP-Adapter 0.40 + InstantID 0.60 = 1.85(总和 1.0-2.0 区间为佳)
- 总和 > 2.5:over-constrained(画面僵硬,无 creative freedom)
- 总和 < 1.0:under-constrained(character ID 不稳定)

---

## LoRA Training for Character Consistency

### 关键 heuristic 3: 训练数据 quality > quantity

per [`../production/references/casting-lora-spec.md`](../production/references/casting-lora-spec.md) §LoRA Training Protocol:

| Quality 维度 | 推荐 | 避免 |
|--------------|------|------|
| Resolution | 1024×1024 minimum | <768px |
| Diversity | 多角度 / 多表情 / 多 lighting | 全 same angle |
| Background | 40% plain + 60% environment | 全 plain backdrop |
| Caption | 含 trigger word + 描述 | 仅 trigger word |

### 关键 heuristic 4: 训练 hyperparameters

| Character 类型 | rank | alpha | learning rate | scheduler | steps |
|---------------|------|-------|---------------|-----------|-------|
| 主角 | 32-64 | 16-32 | 1e-4 | cosine | 2000-3000 |
| 配角 | 16-32 | 8-16 | 1e-4 | cosine | 1500-2000 |
| 群演 | 8-16 | 4-8 | 1e-4 | cosine | 800-1200 |

---

## IP-Adapter for Variable Scenes

### 关键 heuristic 5: IP-Adapter 使用场景

IP-Adapter 适合以下场景(无需训练 LoRA):

1. **Variable wardrobe:** 同 character 不同 wardrobe(per scene delta)
2. **Variable lighting:** 同 character 不同 lighting 氛围
3. **Variable age / state:** character 跨时间(年轻 vs 老年)或 状态(健康 vs 生病)
4. **Quick character test:** LoRA 训练前先用 IP-Adapter 验证 character 设计

### 关键 heuristic 6: IP-Adapter weight 调整

| Weight | 效果 |
|--------|------|
| 0.20-0.40 | 弱 — reference 影响 minimal |
| 0.40-0.60 | 中 — reference 提供 character 框架,允许 creative freedom |
| 0.60-0.80 | 强 — reference dominant,生成接近 reference |
| 0.80-1.00 | 极强 — 接近 1:1 复制 reference(可能 over-constrained)|

---

## InstantID for Face Consistency

### 关键 heuristic 7: InstantID 用于 face identity lock

InstantID 专门用于 face identity 一致性(基于 face embedding),适合:

- Close-up / BCU shots 需要 face 一致
- 跨 lighting / wardrobe 变化的 face identity lock
- LoRA 训练失败的 fallback

**InstantID 训练数据:** 仅需 1-3 张 face close-up(1024×1024 minimum,正面 + 中性表情)

---

## Cross-Shot Verification

### 关键 heuristic 8: Character ID 4 层验证

per [`../production/references/casting-lora-spec.md`](../production/references/casting-lora-spec.md) §Character ID Cross-Shot Consistency:

1. CLIP-T (temporal CLIP) ≥ 0.85
2. Face embedding cosine similarity ≥ 0.80
3. IP-Adapter identity drift ≤ 0.10
4. Human review sanity check

任一层失败 → 重新生成 + 调整 consistency stack。

---

## Anti-Patterns

### 关键 heuristic 9: Character consistency 5 大 anti-pattern(规避)

1. **No consistency stack anti-pattern:** 纯 prompt 生成,character ID 不稳定。**Mitigation:** LoRA + IP-Adapter 组合。
2. **LoRA scale too high anti-pattern:** scale > 0.95 导致 over-constrained 画面僵硬。**Mitigation:** 0.65-0.90 区间。
3. **IP-Adapter wrong reference anti-pattern:** 用 close-up reference 生成 wide shot。**Mitigation:** reference 与目标 shot scale 一致。
4. **InstantID for non-face shots anti-pattern:** InstantID 用于 EWS / WS。**Mitigation:** 仅 close-up + BCU。
5. **Inconsistent trigger word anti-pattern:** 跨 prompt 用不同 trigger word。**Mitigation:** 唯一 trigger word per character。

---

## Glossary

- **LoRA (Low-Rank Adaptation):** Hu et al. 2021,低秩矩阵适配。
- **IP-Adapter:** Ye et al. 2023,Image Prompt Adapter。
- **InstantID:** Wang et al. 2024,face identity preservation。
- **Trigger word:** LoRA 激活 token。
- **Consistency stack:** LoRA + IP-Adapter + InstantID 三方法组合。

---

*Generated: 2026-06-15 as part of Phase 5 REFACTOR-rest-09 (drawer RAG uplift).*
*Source provenance: Hu et al. 2021 / Ye et al. 2023 / Wang et al. 2024 / Kohya_ss / Civitai (2024-2026) — fair use paraphrase + short technical phrases only.*
