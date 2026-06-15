# Asset Reuse Plan — Cross-Shot + Cross-Episode Asset Batching

**Source:** Hermes fal-ai / Replicate asset management guides (2026-06);production pipeline case studies from 公开 短剧 studios (2024-2026);Bordwell & Thompson *Film Art* (11th ed, 2020) §Production Management chapter;f tv/film industry asset management standards (Avid Media Composer / DaVinci Resolve asset library patterns)。
**Copyright:** Fair Use — paraphrased asset batching heuristics + cross-episode reuse patterns; no proprietary studio asset manifests. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 production 专家在 **cross-shot + cross-episode asset reuse** 决策时的**权威源**。它涵盖 5 类 asset 的复用协议 + asset library schema + batch generation 策略 + reuse rate 度量。

它与 [`casting-lora-spec.md`](./casting-lora-spec.md)、[`wardrobe-per-scene.md`](./wardrobe-per-scene.md)、[`lighting-intent-layer.md`](./lighting-intent-layer.md)和 [`gpu-render-budget.md`](./gpu-render-budget.md)互补。

术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)。

---

## 5 Asset Reuse Categories

### 关键 heuristic 1 (load-bearing): 5 类 asset + 各自复用协议

| Asset 类别 | 复用率目标 | 复用方法 | Cost 节省 |
|-----------|-----------|----------|-----------|
| **1. I-frame (character stills)** | 60-80% | LoRA 保证 character ID 一致 → 同 character 跨 shot 共享 I-frame 模板 | 50-70% |
| **2. Background / environment** | 70-90% | 同场景所有 shots 共享 background(diffusion model + subject mask)| 70-85% |
| **3. Wardrobe** | 80-90% per baseline | Layer 1 baseline wardrobe 在 60-80% shots 复用(per [`wardrobe-per-scene.md`](./wardrobe-per-scene.md))| 60-75% |
| **4. Lighting setup** | 90%+ within scene | 同场景 lighting_intent 复用(per [`lighting-intent-layer.md`](./lighting-intent-layer.md))| 80-90% |
| **5. Music / SFX theme** | 95%+ per episode | Episode-level theme + SFX library 复用(composer / foley expert)| 90%+ |

### 关键 heuristic 2: I-frame 复用协议

I-frame(character stills,作为 video gen 的 I-frame 输入)复用规则:

1. **Per character per scene baseline:** 每个 character 在每个场景生成 1 个 baseline I-frame
2. **Scene 内 shot 复用:** 同场景 5-10 个 shots 共享 1 个 baseline I-frame(通过 LoRA 保证 character ID 一致 + wardrobe consistency check)
3. **跨场景新 I-frame:** 跨场景的 wardrobe 变化或 lighting 变化时,生成新 I-frame
4. **跨 episode arc I-frame:** wardrobe arc 变化(per [`wardrobe-per-scene.md`](./wardrobe-per-scene.md) §Arc wardrobe)时,生成新 baseline I-frame

**典型 短剧 I-frame count:**
- 30 集 短剧,每集 5-8 shots,每 shot 1 I-frame
- 总 shot count: 30 × 6.5 = 195 shots
- I-frame reuse rate 70%: 实际 unique I-frame = 195 × 0.30 = ~58 unique I-frames
- 节省 70% image generation cost

---

## Asset Library Schema

### 关键 heuristic 3 (load-bearing): Asset library 5 类 + 命名 convention

production 必须维护 asset library,按下列 schema 组织:

```text
asset_library/
├── characters/
│   ├── protagonist_main/
│   │   ├── lora_weights.safetensors       (LoRA model)
│   │   ├── reference_images/              (训练用)
│   │   ├── baseline_iframes/              (per-scene baseline I-frames)
│   │   │   ├── scene_001_office.png
│   │   │   ├── scene_002_park.png
│   │   │   └── ...
│   │   └── wardrobe_baselines/            (per-wardrobe baseline)
│   │       ├── baseline_formal.json
│   │       └── baseline_casual.json
│   └── antagonist_main/
│       └── ...
├── backgrounds/
│   ├── scene_001_office_bg.png            (无 character 的 background)
│   ├── scene_002_park_bg.png
│   └── ...
├── lighting_setups/
│   ├── lighting_high_key_office.json      (lighting preset for office + high-key)
│   └── ...
├── music_themes/
│   ├── episode_theme_S01E01.mp3
│   └── ...
├── sfx_library/
│   ├── footstep_hard_floor.wav
│   ├── door_close_metal.wav
│   └── ...
└── wardrobe_library/
    ├── stock_suit_dark_gray.json          (复用 stock pieces)
    └── ...
```

### 关键 heuristic 4: Asset ID naming convention

每个 asset 必须有 unique ID,按以下 convention:

```
asset_id = <project_id>_<asset_type>_<scene_or_episode_id>_<variant>
```

示例:
- `S01_char_protagonist_main_baseline_formal_v3`
- `S01_bg_scene_001_office_v1`
- `S01_light_high_key_office_v2`
- `S01_music_ep01_theme_v1`
- `S01_sfx_footstep_hard_v1`

---

## Cross-Shot Asset Batching

### 关键 heuristic 5: Batch generation 协议

为最大化 asset reuse + 最小化 cost,production 应 batch 生成 asset:

**Pre-production phase(batch A — character LoRA + baseline I-frames):**
1. 训练所有 character LoRA(per [`casting-lora-spec.md`](./casting-lora-spec.md) §LoRA Training Protocol)
2. 为每个 character × 每个 baseline wardrobe 生成 baseline I-frame
3. 预计耗时:1-2 周(典型 10 character 短剧)

**Scene pre-production(batch B — backgrounds + lighting):**
1. 为每个 unique scene 生成 background(无 character)
2. 为每个 scene × lighting setup 生成 lighting preset
3. 预计耗时:3-5 天(典型 20 scene 短剧)

**Episode production(batch C — character × scene combinations):**
1. Per episode,组合 character LoRA + background + lighting preset → 生成 episode 的 shots
2. 每个 shot 的 image gen 调用包含 character LoRA + background reference + lighting prompt
3. 预计耗时:每个 episode 1-2 小时(典型 30 集 短剧 = 30-60 小时)

**Post-production(batch D — video + audio):**
1. Per episode,组合 I-frames → 生成 video clips(animator expert)
2. Per episode,生成 audio tracks(composer / foley / voicer expert)
3. 预计耗时:每个 episode 1-2 小时

### 关键 heuristic 6: Reuse rate 度量公式

production 必须计算 asset reuse rate(per asset type):

```
reuse_rate = (total_shots - unique_assets_generated) / total_shots
```

**Target reuse rates:**
- I-frame reuse rate: ≥ 70%
- Background reuse rate: ≥ 80%
- Wardrobe reuse rate: ≥ 60%
- Lighting reuse rate: ≥ 90%
- Music / SFX reuse rate: ≥ 95%

低于 target 触发 audit — 通常表明 LoRA 训练不足或 scene 设计过于碎片化。

---

## Cross-Episode Asset Batching

### 关键 heuristic 7: 跨 episode arc 复用

跨 episode 的 wardrobe arc / character arc 复用:

1. **Wardrobe arc reuse:** 主角的 "复仇前" wardrobe 在 ep 1-14 复用;"复仇后" wardrobe 在 ep 15-30 复用(per [`wardrobe-per-scene.md`](./wardrobe-per-scene.md) §Arc wardrobe)
2. **Character relationship arc:** 主角 + 反派的"对手感"在多 episode 中通过相同 lighting ratio(高对比)dramatize
3. **Music theme arc:** 主 theme 在所有 episode 出现;关键 emotion beat 的 motif 在多 episode 复用(composer expert)
4. **Lighting arc:** 整 season 的 lighting 从明亮(ep 1)逐渐变暗(ep 30 反派失败)的 arc

---

## Anti-Patterns

### 关键 heuristic 8: Asset reuse 5 大 anti-pattern(规避)

1. **No asset library anti-pattern:** 每个 shot 从零生成,无 library。**Mitigation:** 强制 asset_library/ 目录 + naming convention。
2. **Low reuse rate anti-pattern:** reuse rate 低于 target。**Mitigation:** audit LoRA 训练质量 + scene 设计。
3. **Asset ID collision anti-pattern:** 多个 asset 共享 ID,导致 retrieval 错误。**Mitigation:** unique naming convention。
4. **Over-reuse anti-pattern:** 复用过激进导致 episode 间无视觉差异。**Mitigation:** arc-level reuse 区分 baseline-level reuse。
5. **No version control anti-pattern:** asset 更新后旧版本丢失。**Mitigation:** version suffix `_v1`, `_v2`, etc.

---

## Glossary

- **I-frame:** Character still image 作为 video gen 输入。
- **Asset reuse rate:** (total - unique) / total,衡量 asset 复用程度。
- **Baseline asset:** Character / scene / lighting 的默认版本。
- **Arc asset:** 跨 episode 变化的资产(wardrobe arc / music arc / lighting arc)。
- **Batch generation:** 集中批量生成 asset 而非 per-shot 生成。

---

*Generated: 2026-06-15 as part of Phase 5 EXPERT-PROD (production expert).*
*Source provenance: Hermes fal-ai / Replicate asset management (2026-06) / 公开 短剧 studio case studies (2024-2026) / Bordwell & Thompson 2020 — fair use paraphrase + short technical phrases only.*
