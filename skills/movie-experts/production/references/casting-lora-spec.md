# Casting LoRA Spec — Character LoRA Training + Reference Image Protocol

**Source:** Hugging Face PEFT docs (huggingface.co/docs/peft, accessed 2026-06);Kohya_ss SDXL/FLUX LoRA training guides (github.com/bmaltais/kohya_ss);Civitai community LoRA training best-practice guides (2024-2026);fal-ai FLUX LoRA API documentation (fal.ai, 2026-06);Original LoRA paper (Hu et al. 2021 arXiv:2106.09685).
**Copyright:** Fair Use — paraphrased training hyperparameters + reference image spec protocol; no proprietary LoRA weights / datasets / community model verbatim. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 production 专家在 **AI 选角(character LoRA training + reference image spec)** 决策时的**权威源**。它涵盖 LoRA 训练数据采集协议 + reference image 规范 + character ID 跨镜头一致性策略 + per-character cost estimation。

它与 [`wardrobe-per-scene.md`](./wardrobe-per-scene.md)(服化道)、[`lighting-intent-layer.md`](./lighting-intent-layer.md)(灯光)、[`gpu-render-budget.md`](./gpu-render-budget.md)(成本估算)和 [`asset-reuse-plan.md`](./asset-reuse-plan.md)(资产复用)互补,共同构成 production 决策的五层 grounding。

术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)。

---

## LoRA Training Protocol

### 关键 heuristic 1 (load-bearing): Per-character LoRA 训练数据量阈值

基于 Hugging Face PEFT docs + Kohya_ss 社区最佳实践(2024-2026):

| 用途 | 训练图片数 | 训练步数 | LoRA rank | LoRA alpha | 学习率 | 训练时长(A100 80GB)|
|------|-----------|----------|-----------|------------|--------|---------------------|
| 主角(featured character)| 30-50 张 | 2000-3000 步 | 32-64 | 16-32 | 1e-4 | 30-60 分钟 |
| 配角(supporting character)| 15-25 张 | 1500-2000 步 | 16-32 | 8-16 | 1e-4 | 15-30 分钟 |
| 群演(extra / one-shot)| 5-10 张 | 800-1200 步 | 8-16 | 4-8 | 1e-4 | 5-15 分钟 |
| 物件 / 道具 prop | 10-20 张 | 1000-1500 步 | 16 | 8 | 1e-4 | 10-20 分钟 |

**关键规则:**
- **图片多样性 > 图片数量**:30 张多角度 / 多表情 / 多光照 > 100 张同角度
- **背景多样性**:训练图片必须包含 plain backdrop(40%)+ 环境 backdrop(60%)
- **caption 必须包含 trigger word**:e.g., "skw1 man, mid-30s, sharp jawline, dark suit" — trigger word "skw1" 是 LoRA identifier

### 关键 heuristic 2: Reference image 采集协议(5 类必需 + 3 类可选)

production 必须为每个 character 采集以下 reference images(per character LoRA training):

**5 类必需:**
1. **Front face neutral** (正面中性表情) — 5-8 张,plain backdrop,soft front lighting
2. **3/4 angle** (四分之三角度) — 5-8 张,left + right 两侧
3. **Profile** (侧面) — 3-5 张,left + right 两侧
4. **Expression range** (表情范围) — 5-8 张,covering happy / sad / angry / surprised / disgusted / fearful / contemptuous (7 basic emotions per Ekman 1971)
5. **Wardrobe baseline** (基准服装) — 3-5 张,character 穿 baseline 服装,plain backdrop

**3 类可选(narrative-driven):**
6. **Action poses** (动作姿态) — 若 character 有 choreography 需求,5-10 张关键 action poses
7. **Environmental integration** (环境融合) — 5-10 张,character 在 narrative 环境(in office / in park / at night street 等)
8. **Interaction shots** (互动镜头) — 若 character 与他人有 intimate 互动,3-5 张

### 关键 heuristic 3: LoRA rank 与 character 复杂度的关系

LoRA rank 决定 character 的"可识别特征"数量:

| LoRA rank | 适用 character 类型 | 训练时间 | 推理 latency | 跨镜头稳定性 |
|-----------|-------------------|----------|---------------|--------------|
| 8 | extra / prop / one-shot | 5-10 分钟 | 最低 | 弱(简单 character)|
| 16 | supporting character | 15-20 分钟 | 低 | 中 |
| 32 | featured 主角 / 关键配角 | 30-45 分钟 | 中 | 强 |
| 64 | 主角 / 多套服装 / 多场景 | 60-90 分钟 | 高 | 极强 |
| 128+ | 不推荐 | >2 小时 | 显著 | 过拟合风险 |

**经验规则:** `rank ≈ 2 × √(训练图片数)`。e.g., 25 张 → rank ≈ 10 → 用 16;49 张 → rank ≈ 14 → 用 16 或 32。

---

## Character ID Cross-Shot Consistency

### 关键 heuristic 4 (load-bearing): Character ID 一致性 4 层验证

每个生成的 shot 必须通过 4 层 character ID 验证(per CLIP-T + face embedding + IP-Adapter + human review):

1. **CLIP-T (temporal CLIP) score** ≥ 0.85 (跨 shot 视觉一致性)
2. **Face embedding cosine similarity** ≥ 0.80 (跨 shot 面部特征一致性,基于 ArcFace / FaceNet)
3. **IP-Adapter identity drift** ≤ 0.10 (IP-Adapter 输入 reference image,输出与 reference 的 embedding 距离)
4. **Human review sanity check** — 每集 5-shot spot check

**失败处理:** 任一层失败 → 重新生成 shot(或回退到更高 rank LoRA + 更严格 reference image 约束)。

### 关键 heuristic 5: Voice / 行为 / 服装 一致性 — 跨 expert 协作

character 跨 shot 一致性不仅限于视觉,还包括:

- **voicer 一致性:** 同一 character 跨 shot 必须 voice 一致(speaker embedding cosine similarity ≥ 0.85 per [`../voicer/references/character-voice-consistency.md`](../voicer/references/character-voice-consistency.md))
- **performer 一致性:** 同一 character 跨 shot 必须 emotion / 行为模式一致(ExBxSxP matrix σ ≤ 0.10 per [`../performer/references/stanislavski-prepares.md`](../performer/references/stanislavski-prepares.md))
- **wardrobe 一致性:** 同一场景内同一 character 必须 wardrobe 一致(per [`wardrobe-per-scene.md`](./wardrobe-per-scene.md))

production 专家必须协调上述 3 个 expert 的 character 一致性输出。

---

## Per-Character Cost Estimation

### 关键 heuristic 6: LoRA 训练 + 推理 GPU cost 公式

production 必须为每个 character 计算 LoRA 成本(per GPU-hour pricing):

```
character_cost = (training_hours × training_gpu_rate) + (inference_hours × inference_gpu_rate)
```

**典型 GPU 速率(2026-06 AWS / RunPod / Modal):**
- A100 80GB: $2.50-4.00 / GPU-hour (training)
- A10G 24GB: $1.00-1.50 / GPU-hour (inference)
- L4 24GB: $0.80-1.20 / GPU-hour (inference)

**典型 character 成本(主角,rank 32,30 集 短剧):**
- Training: 0.75 小时 × $3.00 = $2.25
- Inference (per shot generation,10s/shot × 500 shots × 0.5s/shot GPU time):0.07 小时 × $1.00 = $0.07
- **Per-character total: ~$2.32**

**全 短剧 cast 成本估算(典型 男频-revenge 短剧 30 集):**
- 1 主角 + 1 反派 + 3 配角 + 5 群演 = 10 characters
- 主角 + 反派:rank 32 × 2 = $4.64
- 配角:rank 16 × 3 × $1.16 = $3.48
- 群演:rank 8 × 5 × $0.58 = $2.90
- **Cast LoRA total: ~$11.02**(excluding re-takes + GPU contention overhead)

### 关键 heuristic 7: Re-take budget rule

每个 character LoRA 训练预期 **1.3 次 re-take**(因 reference image 质量 / caption 错误 / overfitting)。budget 估算必须包含 30% re-take buffer:

```
final_character_cost = base_character_cost × 1.3
```

详见 [`gpu-render-budget.md`](./gpu-render-budget.md) §LoRA 训练 + 推理 budget 公式。

---

## Anti-Patterns

### 关键 heuristic 8: LoRA training 5 大 anti-pattern(规避)

1. **Too few reference images anti-pattern:** <10 张图片训练 LoRA,导致 character ID 弱。**Mitigation:** ≥15 张(spotted)or ≥30 张(featured)。
2. **Same angle / same backdrop anti-pattern:** 所有训练图片同一角度 + 同一 backdrop,导致 LoRA 在其他角度失效。**Mitigation:** 多角度 + 多 backdrop(详见 §Reference image 采集协议)。
3. **No trigger word in caption anti-pattern:** caption 不包含 trigger word,导致 LoRA 无法激活。**Mitigation:** 必须包含 trigger word(e.g., "skw1 man")。
4. **Too-high rank anti-pattern:** rank > 64 导致 overfitting(LoRA 在训练集外数据上失效)。**Mitigation:** rank ≤ 64,典型 16-32。
5. **Cross-character trigger word collision anti-pattern:** 多个 character 共享 trigger word,导致 LoRA 互相干扰。**Mitigation:** 每个 character 独立 trigger word(e.g., skw1 / skw2 / skw3)。

---

## Glossary

- **LoRA (Low-Rank Adaptation):** Hu et al. 2021 — 低秩矩阵适配,用于 fine-tune 扩散模型。
- **LoRA rank:** 低秩矩阵的秩;决定 LoRA 容量。
- **Trigger word:** caption 中激活 LoRA 的 identifier。
- **CLIP-T:** Temporal CLIP score,跨 shot 视觉一致性度量。
- **IP-Adapter:** Image Prompt Adapter,将 reference image 作为 prompt 输入。

---

*Generated: 2026-06-15 as part of Phase 5 EXPERT-PROD (production expert).*
*Source provenance: Hugging Face PEFT / Kohya_ss / Civitai / fal-ai FLUX LoRA docs (2026-06) / Hu et al. 2021 — fair use paraphrase + short technical phrases only.*
