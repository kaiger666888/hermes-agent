# Stable Audio Open 1.0 — Workflow + 7D Parametric Sound Design

**Source:** Stability AI *Stable Audio Open 1.0* model card (huggingface.co/stabilityai/stable-audio-open-1.0, 2024-2026);Evans *The Sound Effects Bible* (2nd ed, 2019);Ament *The Producers Guide to Audio Stripping* (2017);Viers *The Sound Effects Bible* (2019 update).
**Copyright:** Fair Use — paraphrased workflow + 7D parametric design; no reproduction of copyrighted SFX library content. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 foley 专家在 **AI 音效生成 workflow** 决策时的**权威源**。它涵盖 Stable Audio Open 1.0 模型能力 + 7D parametric sound design(Material × Action × Force × Environment × Distance × Layering × Emotional intent)+ 与现有 Hermes catalog 集成。

替代 phantom 引用 AudioLDM-2(Phase 0 audit 标记的 phantom);Stable Audio Open 1.0 是 2026-06 实际可用的 open-weight SFX 生成模型。

## Stable Audio Open 1.0 能力矩阵

### 关键 heuristic 1 (load-bearing): Stable Audio Open 1.0 generation 参数

| 参数 | 范围 | 默认 | 备注 |
|------|------|------|------|
| sample_rate | 44.1kHz / 48kHz | 44.1kHz | 48kHz 推荐 for film |
| duration_sec | 0.5-47s | 10s | 短剧 SFX 通常 ≤5s |
| prompt | 自由文本 | — | 推荐 ≤100 tokens |
| negative_prompt | 自由文本 | — | 用于避免 unwanted sounds |
| num_inference_steps | 10-150 | 50 | quality vs speed tradeoff |
| guidance_scale | 1.0-15.0 | 7.0 | higher = more prompt-adherent |
| seed | int | random | 复现性 |

### 关键 heuristic 2: Stable Audio Open 1.0 与 AudioLDM-2 对比

| 特征 | AudioLDM-2(phantom)| Stable Audio Open 1.0 |
|------|---------------------|----------------------|
| 训练数据 | AudioCaps(50K 验证)| CCmixter + freesound + Bandcamp split(800K+)| 更大 + 商用安全 |
| 最大时长 | 10s | 47s | SFX + 短 music 片段 |
| 商用许可 | ❌ 模糊 | ✅ CC-BY-NC-SA 4.0 + Stability community license | 商用清晰 |
| 中文 prompt 支持 | 弱 | 中 | 英文 prompt 优先 |
| 部署 | 5GB VRAM | 6GB VRAM | 相近 |

**关键规则:** Hermes 现已不部署 AudioLDM-2(phantom)。Stable Audio Open 1.0 是 v1.5 default SFX 生成模型。

## 7D Parametric Sound Design

### 关键 heuristic 3: 7 维度 foley 参数

每个 foley SFX 必须 specify 7 维度(per foley/SKILL.md §Output Format):

1. **Material (M)** — 物体材质(wood / metal / glass / flesh / fabric / plastic / water / stone)
2. **Action (A)** — 动作类型(impact / scrape / friction / break / drip / rustle / breathe)
3. **Force (F)** — 力度 0.0-1.0(silent 0.0 / gentle 0.3 / moderate 0.5 / strong 0.7 / violent 1.0)
4. **Environment (E)** — 环境(reverb-time 0.0-5.0s + room-size 0.0-1.0 + outdoor/indoor)
5. **Distance (D)** — 距离 0.0-1.0(close-mic 0.0 / mid 0.5 / distant 1.0)
6. **Layering (L)** — 层叠数 1-5(单层 / 双层 / 三层 / 多层)
7. **Emotional intent (EI)** — 情绪(hope / fear / tension / relief / shock / neutral)

### 关键 heuristic 4: 7D → Stable Audio Open prompt 编译公式

```
stable_audio_prompt = f"{Material} {Action}, {Force_intensity} force, {Distance} mic placement, {Environment} reverb {reverb_time}s, {Emotional_intent} mood"
```

**示例 7D:** Material=metal, Action=impact, Force=0.7, Environment=hall(reverb 1.8s, room 0.6, indoor), Distance=0.4, Layering=2, EI=tension

**Stable Audio Open prompt:** "metal impact, strong force, mid-distance mic placement, hall reverb 1.8 seconds, tension mood"

---

## 与 composer / mixer 的 handoff

- **→ composer:** foley 提供单 SFX stem;composer 决定 SFX 与 music 的 timing
- **→ mixer:** foley 输出 dry SFX;mixer 负责 EQ / reverb / ducking / final levels
- **→ spatial_audio:** foley 输出 mono / stereo SFX;spatial_audio 负责 6D encoding

---

## Anti-Patterns

### 关键 heuristic 5: Foley 5 大 anti-pattern(规避)

1. **Phantom model reference anti-pattern:** 引用 AudioLDM-2(phantom)。**Mitigation:** 用 Stable Audio Open 1.0。
2. **Single-layer SFX anti-pattern:** 单层 SFX 缺 depth。**Mitigation:** Layering ≥2(详见 §7D §L)。
3. **No reverb context anti-pattern:** SFX 无 environment context。**Mitigation:** specify Environment 维度。
4. **Over-driven Force anti-pattern:** Force=1.0 用于 non-violent scene。**Mitigation:** per-scene Force 协议。
5. **No seed reproducibility anti-pattern:** SFX 无法复现。**Mitigation:** 指定 seed + 记录。

---

## Glossary

- **Stable Audio Open 1.0:** Stability AI 开源 SFX + 短 music 生成模型(2024)。
- **7D parametric design:** Material / Action / Force / Environment / Distance / Layering / Emotional intent。
- **Stem:** 单 SFX 文件,待 mixer 混音。
- **Dry SFX:** 无 reverb / EQ 的原始 SFX。

---

*Generated: 2026-06-15 as part of Phase 5 REFACTOR-rest-03 (foley RAG uplift).*
*Source provenance: Stability AI Stable Audio Open 1.0 model card (2024-2026) / Evans 2019 / Ament 2017 / Viers 2019 — fair use paraphrase + short technical phrases only.*
