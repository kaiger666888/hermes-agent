# FLUX 2 Parameter Surface — Klein 9B Defaults + Prompt Engineering

**Source:** Black Forest Labs *FLUX 2 Klein 9B* model card (blackforestlabs.ai, 2026);fal-ai FLUX 2 API docs (fal.ai/models/fal-ai/flux-2/klein/9b, 2026-06);Hermes image_generation_tool.py (line 372: `fal-ai/flux-2/klein/9b` is default);FLUX 2 community prompt engineering guides (Civitai / Reddit r/StableDiffusion, 2024-2026)。
**Copyright:** Fair Use — paraphrased parameter ranges + prompt engineering patterns; no proprietary model weights verbatim. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

> **⚠ Phantom strip note:** 旧 drawer SKILL.md 的 FLUX 1.x sampler 参数(euler_a / dpmpp_2m)是 phantom。FLUX 2 Klein 9B 不使用 Karras samplers;使用 distilled flow matching + 推理 step + guidance 双参数。

## FLUX 2 Klein 9B 能力矩阵

### 关键 heuristic 1 (load-bearing): FLUX 2 推理参数

| 参数 | 范围 | 默认 | 备注 |
|------|------|------|------|
| width × height | 512-2048 | 1024 × 1024(横屏) / 1080 × 1920(竖屏)| 短剧 用 1080×1920 |
| num_inference_steps | 4-50 | 28(production) / 12(preview) | quality vs speed |
| guidance_scale | 0.0-20.0 | 3.5(FLUX 2 推荐)| lower than SDXL's 7.0 |
| max_sequence_length | 256-512 | 256 | prompt token 限制 |
| seed | int | random | 复现性 |
| output_format | png / jpeg / webp | png | png 推荐(无损)|
| negative_prompt | 自由文本 | — | FLUX 2 支持,SDXL 时代的反义词 |

**关键差异 vs SDXL:**
- guidance_scale 默认 3.5(SDXL 7.0)— FLUX 2 prompt 理解更强,不需要 high guidance
- num_inference_steps 默认 28(SDXL 30-40)— FLUX 2 更快收敛
- prompt token 限制 512(SDXL 75-225)— FLUX 2 支持更长 prompt

### 关键 heuristic 2: FLUX 2 prompt 工程 5 大原则

1. **Natural language > tags:** FLUX 2 理解自然语言完整句子;"a woman in red dress standing by window, golden hour sunlight" > "1girl, red dress, window, golden_heter"
2. **Detail over brevity:** FLUX 2 鼓励详细 prompt(300-500 字符);越具体越准确
3. **Lighting / mood 显式:** "soft window light, warm golden hour" 显式写出;FLUX 2 准确响应
4. **Composition keywords:** "rule of thirds" / "centered" / "wide shot" / "close-up" 等
5. **LoRA / IP-Adapter activation:** LoRA trigger word 必须在 prompt 前 50 tokens;IP-Adapter 通过 image prompt 输入

### 关键 heuristic 3: 短剧 9:16 vertical generation 协议

```yaml
# 短剧 9:16 production config
width: 1080
height: 1920
num_inference_steps: 28  # production
guidance_scale: 3.5
seed: <per-scene baseline seed>  # 见 asset-reuse-plan.md
output_format: png
prompt: |
  [character trigger word] [shot scale] [wardrobe baseline] [lighting] 
  [environment] [camera angle] [composition rule]
  # Example:
  # skw1 man, MCU close-up, dark gray tailored blazer, soft window light 
  # golden hour, modern office interior, eye-level, rule of thirds vertical
```

---

## 与 character LoRA / IP-Adapter 集成

### 关键 heuristic 4: LoRA + FLUX 2 加载协议

per [`../production/references/casting-lora-spec.md`](../production/references/casting-lora-spec.md):

```yaml
# LoRA loading via fal-ai API
model: fal-ai/flux-2/klein/9b
lora:
  - path: asset_library/characters/protagonist_main/lora_weights.safetensors
    scale: 0.85  # LoRA strength (0.0-1.0)
```

**LoRA scale 推荐:**
- 主角 LoRA: 0.80-0.90(强 identity)
- 配角 LoRA: 0.65-0.75
- 群演 LoRA: 0.50-0.60
- prop LoRA: 0.70-0.80

### 关键 heuristic 5: IP-Adapter character consistency

IP-Adapter 输入 reference image(典型 character baseline I-frame):

```yaml
# IP-Adapter configuration
ip_adapter:
  image: asset_library/characters/protagonist_main/baseline_iframes/scene_001_office.png
  weight: 0.60  # IP-Adapter weight (0.0-1.0)
  noise: 0.15   # IP-Adapter noise
```

**LoRA vs IP-Adapter 选择:**
- LoRA:训练后复用,适合固定 character;cost-effective
- IP-Adapter:per-image 调整,适合 variable wardrobe / lighting;无需训练

---

## Phantom Strip: FLUX 1.x samplers

### 关键 heuristic 6: 老 SKILL.md FLUX 1.x 参数 phantom

旧 drawer SKILL.md 的 sampler 参数:

| 旧 phantom 参数 | FLUX 2 替换 |
|----------------|-------------|
| `euler_a` | (无 — FLUX 2 不用 Karras samplers) |
| `dpmpp_2m` | (无 — 同上) |
| `ddim_steps: 30-50` | `num_inference_steps: 28`(默认) |
| `cfg_scale: 7.0-12.0` | `guidance_scale: 3.5`(FLUX 2 默认) |

**SKILL.md 修正:** 上述 phantom 参数全部 strip + 替换为 FLUX 2 推理参数。

---

## Anti-Patterns

### 关键 heuristic 7: FLUX 2 5 大 anti-pattern(规避)

1. **Phantom Karras samplers anti-pattern:** 引用 euler_a / dpmpp_2m。**Mitigation:** strip + FLUX 2 推理参数。
2. **Too-high guidance anti-pattern:** guidance_scale >7.0 导致 over-saturated。**Mitigation:** 默认 3.5。
3. **Tag-based prompt anti-pattern:** 用 SDXL 时代的 tag prompt。**Mitigation:** 自然语言 prompt。
4. **No LoRA / IP-Adapter anti-pattern:** 纯 prompt 生成,character ID 不稳定。**Mitigation:** LoRA + IP-Adapter 组合。
5. **Wrong aspect ratio anti-pattern:** 横屏 16:9 prompt 用于 9:16。**Mitigation:** 显式 width / height。

---

## Glossary

- **FLUX 2 Klein 9B:** Black Forest Labs 9B 参数 open-weight 扩散模型。
- **Distilled flow matching:** FLUX 2 的训练方法,替代 Karras diffusion。
- **Guidance scale:** prompt 引导强度;FLUX 2 默认 3.5。
- **LoRA scale:** LoRA 强度;0.0-1.0。
- **IP-Adapter:** Image Prompt Adapter,reference image 作为 prompt 输入。

---

*Generated: 2026-06-15 as part of Phase 5 REFACTOR-rest-09 (drawer RAG uplift).*
*Source provenance: Black Forest Labs FLUX 2 model card (2026) / fal-ai FLUX 2 API docs (2026-06) / Hermes image_generation_tool.py / FLUX 2 community guides (2024-2026) — fair use paraphrase + short technical phrases only.*
*⚠ Phantom strip: FLUX 1.x Karras samplers (euler_a / dpmpp_2m) stripped per Phase 0 GAP-REPORT.*
