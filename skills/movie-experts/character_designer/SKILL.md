---
name: character_designer
description: "Character Designer Expert: defines character identity (4D-Anchor multi-view + layered STYLE_PREFIX + consistency stress test) producing CharacterBible 2.0 JSON. Decoupled from visual_executor — visual_executor generates images, character_designer defines the identity contract that visual_executor must satisfy."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, character, design, identity, 4d-anchor, consistency, character-bible]
    related_skills: [style_genome, screenplay, visual_executor, continuity_auditor, audio_pipeline, production]
    expert_id: character_designer
    metrics: [cross_angle_consistency, identity_preservation_rate, stress_test_pass_rate, negative_trait_compliance]
---

# Character Designer Expert (角色设计专家)

Character identity contract author for AI 短剧 / 微电影. Produces `CharacterBible 2.0` JSON that defines a character's appearance, personality, style layers, 4D multi-view anchor references, negative traits (anti-drift), and consistency stress-test results. **Decoupled from [`visual_executor`](../visual_executor/SKILL.md)**: visual_executor generates images (drawer sub-step, FLUX 2 / LoRA / IP-Adapter) and video (animator sub-step); character_designer defines WHAT the character is before any image is generated. Calling sequence: character_designer → visual_executor → audio_pipeline (lip_sync sub-step).

## When to use this skill

The user needs one of:
- **New character creation** — define a character before any image generation
- **Character identity contract** — produce a `CharacterBible 2.0` that downstream experts (visual_executor, audio_pipeline (lip_sync sub-step), continuity_auditor) can consume as ground truth
- **Consistency stress test** — verify an existing character's identity survives 3 different scene contexts before locking it
- **Cross-angle validation** — check whether 4 anchor views (front / 3-quarter / side / back) are mutually consistent
- **Negative trait enforcement** — define what the character is NOT (e.g., "no blonde hair, no beard") to prevent downstream drift
- **Identity drift diagnosis** — diagnose why a character looks different across shots/episodes

**Do NOT confuse with [`visual_executor`](../visual_executor/SKILL.md)**: visual_executor *generates images*. character_designer *defines the identity contract*. Calling visual_executor without a CharacterBible first = unreliable, drifting character. Calling character_designer after visual_executor = post-hoc rationalization.

## References

本专家所有数值阈值与协议由下列 4 个 refs 独占定义;SKILL.md body 仅作摘要 + 跨链。

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/4d-anchor-system.md`](./references/4d-anchor-system.md) | 设计任何角色的多视角锚点 前 | 4D 锚点协议(front / 3-quarter / side / back 四视角)+ 各视角的 prompt 关键词 + 视角优先级(3Q > Front > Side > Back)+ 向后兼容(无 references 字段时回退 reference_images[0])|
| [`references/layered-style-prefix.md`](./references/layered-style-prefix.md) | 构建 STYLE_PREFIX 前 | 三层架构(CORE 全局不变 / IDENTITY 严格锁定 / VARIANCE 随镜头变化)+ 组合公式 `{CORE}, {IDENTITY}, {VARIANCE}` + 锁定后不可变规则 + 风格变更时重生成转面图触发条件 |
| [`references/consistency-stress-test.md`](./references/consistency-stress-test.md) | 锁定角色前验证一致性 前 | 3 测试场景协议(街头夜景 0.40 / 室内特写 0.55 / 动作侧拍 0.35)+ 人工检查标准("3张图是否还是同一个人?")+ 失败回退到 Step 2 + CLIP-I / DINO-I 跨角度相似度量化阈值 |
| [`references/character-bible-schema.md`](./references/character-bible-schema.md) | 输出 CharacterBible 2.0 前 | 完整 JSON schema 字段定义(anchors / style_layers / negative_traits / consistency_lock / seedance_profile / video_samples)+ 每字段的下游消费专家 + 字段冻结规则(frozen_fields 不可改)|

## Role & Philosophy

- **身份优先于像素** — drawer 关心怎么画,character_designer 关心画的是谁。没有 CharacterBible 的角色 = 没有身份证的人。
- **4D 锚点而非单图** — 单张正面图无法支撑镜头的多角度需求。front / 3-quarter / side / back 四视角构成角色的"4D 身份护照",缺一不可。
- **负面特征是反漂移的核心** — "character 是金发" 不够,"character 不能是金发 + 不能有胡须 + 不能戴眼镜" 才能锁定。
- **压力测试先于锁定** — 在 3 个完全不同场景验证一致性,通过才 lock;不通过回退到变体重生成。
- **下游可消费的契约** — CharacterBible 2.0 是 visual_executor / audio_pipeline (lip_sync sub-step) / continuity_auditor 的 ground truth,字段冻结后不能随意改。

## Knowledge Retrieval

在生成任何 CharacterBible 输出前,按以下顺序检索上下文(4 个检索主题):

- **4D 锚点协议 + 视角优先级 + 向后兼容** —— 详见 [`references/4d-anchor-system.md`](./references/4d-anchor-system.md)
- **三层 STYLE_PREFIX + 锁定规则 + 重生成触发** —— 详见 [`references/layered-style-prefix.md`](./references/layered-style-prefix.md)
- **3 测试场景协议 + CLIP/DINO 阈值 + 失败回退** —— 详见 [`references/consistency-stress-test.md`](./references/consistency-stress-test.md)
- **CharacterBible 2.0 schema + 字段冻结规则 + 下游消费** —— 详见 [`references/character-bible-schema.md`](./references/character-bible-schema.md)

**若当前 runtime 中有 memory / RAG 工具**,使用以下查询范围:

```
tags="expert:character_designer,domain:4d-anchor-system"
tags="expert:character_designer,domain:layered-style-prefix"
tags="expert:character_designer,domain:consistency-stress-test"
tags="expert:character_designer,domain:character-bible-schema"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件。

> **NOTE:** 本 SKILL.md body 不引用任何具体外部模型名。涉及具体模型时使用 `<image_gen_primary>` / `<clip_eval>` / `<dino_eval>` 占位符。模型名只出现在 `references/*.md` 与 [`../_shared/known-external-models.yaml`](../_shared/known-external-models.yaml) allowlist 中。

## Core Capabilities

- **4D 锚点生成** — 从 character spec + ArtDirection 生成 front / 3-quarter / side / back 四视角源图(每视角有专属 prompt 模板)
- **分层 STYLE_PREFIX 构建** — CORE + IDENTITY + VARIANCE 三层,锁定后 IDENTITY + CORE 不可改,VARIANCE 可随镜头变化
- **8-image reference library** — 基于源图生成 8 张动态 strength 的参考图(portrait / 3quarter-body / side-profile / back-view / 3 expressions / 1 action),每张 strength 根据用途调整(0.30-0.55 区间)
- **负面特征排除** — 显式 negative_traits 数组(如 `["blonde hair", "beard", "glasses"]`),注入到所有下游 image-gen prompt
- **一致性压力测试** — 3 场景验证(街头夜景 / 室内特写 / 动作侧拍),用 CLIP-I / DINO-I 客观量化跨场景相似度
- **CharacterBible 2.0 输出** — 完整 JSON schema,字段冻结 + 版本控制 + 下游消费专家标注
- **Identity drift 诊断** — 给定 N 张图,识别哪些图偏离了 character identity,给出具体偏离维度(hair / face / outfit / accessories)

## Output Format

```json
{
  "type": "CharacterBible",
  "version": "2.0.0",
  "character_id": "char_wuji",
  "name": "无极",
  "appearance": "25岁男性,黑色长发(及肩,微卷),红色瞳孔,左脸颊有刀疤,黑色风衣,内搭灰色高领毛衣,黑色靴子",
  "personality": "冷静、隐忍、为复仇而生;对敌人冷酷,对无辜者保留底线",
  "anchors": {
    "front": "assets/characters/char_wuji/front-source.png",
    "three_quarter": "assets/characters/char_wuji/3q-source.png",
    "side": "assets/characters/char_wuji/side-source.png",
    "back": "assets/characters/char_wuji/back-source.png"
  },
  "reference_images": [
    "front-portrait.png",
    "3quarter-body.png",
    "side-profile.png",
    "back-view.png",
    "expression-shock.png",
    "expression-shy.png",
    "expression-calm.png",
    "action-typing.png"
  ],
  "reference_library": {
    "front-portrait":   { "url": "...", "strength": 0.55, "angle": "portrait", "purpose": "facial close-up" },
    "3quarter-body":    { "url": "...", "strength": 0.45, "angle": "full_body", "purpose": "default half-body" },
    "side-profile":     { "url": "...", "strength": 0.45, "angle": "full_body", "purpose": "side silhouette" },
    "back-view":        { "url": "...", "strength": 0.45, "angle": "full_body", "purpose": "back composition" },
    "expression-shock": { "url": "...", "strength": 0.50, "angle": "expression", "purpose": "shock emotion" },
    "expression-shy":   { "url": "...", "strength": 0.50, "angle": "expression", "purpose": "shyness emotion" },
    "expression-calm":  { "url": "...", "strength": 0.50, "angle": "expression", "purpose": "calm emotion" },
    "action-typing":    { "url": "...", "strength": 0.30, "angle": "action", "purpose": "low-lock action" }
  },
  "style_layers": {
    "core": "anime, cyberpunk era, cinematic lighting",
    "identity": "black long hair (shoulder-length, slight wave), red eyes, scar on left cheek, black trench coat, gray turtleneck, black boots",
    "variance_template": "{lighting}, {weather}, {mood}"
  },
  "style_prefix_locked": "anime, cyberpunk era, cinematic lighting, black long hair (shoulder-length, slight wave), red eyes, scar on left cheek, black trench coat, gray turtleneck, black boots, {VARIANCE}",
  "negative_traits": ["blonde hair", "beard", "glasses", "short hair", "blue eyes", "smile (default)"],
  "layers": {
    "face":        { "locked": true,  "features": "red eyes, scar, jawline, hair color/length" },
    "outfit":      { "locked": true,  "features": "black trench coat, gray turtleneck, black boots" },
    "accessories": { "locked": false, "features": "may add watch / earrings per scene" }
  },
  "seedance_profile": {
    "consistency_mode": "strict",
    "default_strength": 0.45,
    "character_ref_priority": ["three_quarter", "front"]
  },
  "video_samples": [],
  "sample_strength_default": 0.35,
  "consistency_lock": {
    "locked": true,
    "lock_version": 1,
    "anchor_mode": "reference_image",
    "frozen_fields": ["appearance", "style_layers.core", "style_layers.identity", "negative_traits"],
    "stress_test_results": {
      "passed": true,
      "tests": [
        {
          "scene": "street night neon",
          "strength": 0.40,
          "clip_i_score": 0.87,
          "dino_i_score": 0.84,
          "verdict": "pass"
        },
        {
          "scene": "indoor close-up crying",
          "strength": 0.55,
          "clip_i_score": 0.91,
          "dino_i_score": 0.89,
          "verdict": "pass"
        },
        {
          "scene": "running side view",
          "strength": 0.35,
          "clip_i_score": 0.83,
          "dino_i_score": 0.80,
          "verdict": "pass"
        }
      ],
      "aggregate_clip_i_mean": 0.87,
      "aggregate_dino_i_mean": 0.84,
      "warnings": []
    }
  },
  "downstream_consumers": [
    "visual_executor",
    "audio_pipeline",
    "continuity_auditor",
    "production"
  ]
}
```

### Consistency lock status

| Status | Meaning | Action allowed |
|---|---|---|
| **unlocked** | Initial state, no anchors generated | Full edit; no consumers may reference |
| **stress_testing** | Anchors generated, stress test running | Read-only; awaiting test verdict |
| **locked (passed)** | Stress test passed, frozen_fields locked | Only `variance_template` editable; downstream may consume |
| **locked (failed)** | Stress test failed | Reject; regenerate variants + re-test |
| **revision_pending** | User requests post-lock change | Requires explicit unfreeze + re-test; bumps lock_version |

## Key Parameters

### Anchor generation

- **`<image_gen_primary>`**: any high-quality image model with multi-view consistency (see [`../_shared/known-external-models.yaml`](../_shared/known-external-models.yaml))
- **anchor_views**: `["front", "three_quarter", "side", "back"]` (full 4D) OR subset for minor characters
- **anchor_resolution**: 2K (production) / 1K (preview)
- **anchor_style_consistency**: must reuse same STYLE_PREFIX across all views

### Style layer construction

- **`STYLE_CORE`**: derived from upstream [`style_genome`](../style_genome/SKILL.md) output (genre + era + mood)
- **`STYLE_IDENTITY`**: per-character appearance spec (frozen on lock)
- **`STYLE_VARIANCE`**: per-scene variable (lighting / weather / mood), template-substituted

### Stress test

- **`<clip_eval>`**: CLIP-I (image-image similarity) for cross-scene consistency
- **`<dino_eval>`**: DINO-I (self-supervised features, more shape-aware than CLIP)
- **pass_threshold_clip**: 0.80 (per [`references/consistency-stress-test.md`](./references/consistency-stress-test.md))
- **pass_threshold_dino**: 0.78
- **test_scenes**: 3 canonical (street night neon / indoor close-up crying / running side view)

### Reference library

- **image_count**: 8 (recommended) — covers 4 angles + 3 expressions + 1 action
- **strength_range**: 0.30 (action, low lock for pose freedom) - 0.55 (portrait, high lock for face)
- **default_strength**: 0.35 for downstream `sample_strength` parameter

## Workflow

1. **Receive upstream inputs** — [`style_genome`](../style_genome/SKILL.md) (genre/era/mood) + [`screenplay`](../screenplay/SKILL.md) (character list + role).
2. **Build layered STYLE_PREFIX** — assemble CORE (from style_genome) + IDENTITY (from character spec) + VARIANCE (template).
3. **Generate 3 visual variants** (tournament mode) — A/B/C candidates per character, covering front + 3-quarter + side preview.
4. **REVIEW GATE** — present 3 variants to user; await selection.
5. **Generate 4D anchors** — front / 3-quarter / side / back source images using selected variant.
6. **Build 8-image reference library** — generate per dynamic-strength table.
7. **Run consistency stress test** — 3 scenes, compute CLIP-I + DINO-I per scene.
8. **Lock or fail** — if all 3 scenes pass thresholds, lock + freeze `frozen_fields`; if any fail, regenerate variants + re-test.
9. **Emit CharacterBible 2.0** — full JSON with all downstream consumer pointers.
10. **Hand off to downstream** — visual_executor / audio_pipeline (lip_sync sub-step) / continuity_auditor / production.

## Quality Thresholds

| Threshold | Value | Source |
|---|---|---|
| CLIP-I 跨场景 pass 阈值 | ≥ 0.80 | [`references/consistency-stress-test.md`](./references/consistency-stress-test.md) |
| DINO-I 跨场景 pass 阈值 | ≥ 0.78 | [`references/consistency-stress-test.md`](./references/consistency-stress-test.md) |
| CLIP-I 优秀(distinct identity) | ≥ 0.85 | [`references/consistency-stress-test.md`](./references/consistency-stress-test.md) |
| Reference library 最小张数 | 6 (推荐 8) | [`references/character-bible-schema.md`](./references/character-bible-schema.md) |
| Negative traits 最少条数 | 3 | [`references/character-bible-schema.md`](./references/character-bible-schema.md) |
| Stress test 场景数 | 3 (street / indoor / action) | [`references/consistency-stress-test.md`](./references/consistency-stress-test.md) |
| sample_strength 范围 | 0.30-0.55 | [`references/character-bible-schema.md`](./references/character-bible-schema.md) |

## Collaboration

### Upstream

- **<- [`style_genome`](../style_genome/SKILL.md)** — provides STYLE_CORE (genre / era / mood)
- **<- [`screenplay`](../screenplay/SKILL.md)** — provides character list + narrative role + dialogue style
- **<- [`production`](../production/SKILL.md)** — provides per-character casting spec + wardrobe budget

### Downstream

- **-> [`visual_executor`](../visual_executor/SKILL.md)** — consumes CharacterBible as ground-truth identity for every image generation (drawer sub-step) + consumes anchors for video-gen identity preservation (animator sub-step)
- **-> [`audio_pipeline`](../audio_pipeline/SKILL.md) (lip_sync sub-step)** — consumes front/three_quarter anchors for identity reference embedding
- **-> [`continuity_auditor`](../continuity_auditor/SKILL.md)** — consumes ArcFace baseline computed from front anchor
- **-> [`production`](../production/SKILL.md)** — consumes character wardrobe + accessories spec

## What NOT to do

- ❌ **不要在没有 style_genome 上游的情况下设计 character** — CORE 风格层必须有来源,自由发挥 = drift 风险。
- ❌ **不要跳过 4D 锚点** — 单张正面图无法支撑侧拍 / 背拍 / 动作镜头。
- ❌ **不要在 stress test 失败后强行 lock** — 失败 = 回到 Step 2 重生成变体。强行 lock = 下游所有专家都会受影响。
- ❌ **不要忽略 negative_traits** — 没有 negative 锁定的角色 = drawer 容易漂移到训练分布默认值(金发、微笑等)。
- ❌ **不要 lock 后修改 frozen_fields** — appearance / style_layers.core / style_layers.identity / negative_traits 一旦锁定,只能通过显式 revision_pending 流程 + 版本 bump 修改。
- ❌ **不要把 CharacterBible 字段写得抽象** — "黑发红眼有疤"不够;"黑色长发及肩微卷,红色瞳孔,左脸颊刀疤约 3cm" 才合格。
- ❌ **不要在 SKILL.md body 引用具体模型名** — `<image_gen_primary>` / `<clip_eval>` 占位符,具体名只在 references + known-external-models.yaml。

## Validation protocol (how to know if this expert improved)

本专家的核心 KPI 是**跨场景一致性 + 跨角度一致性**,用 CLIP-I + DINO-I 客观量化,不依赖 LLM-judge:

1. **Build test corpus**: 收集 ≥ 30 characters,每个 character 在 3 stress-test scenes + 4 anchor views = 7 张图。
2. **Run character_designer** on each character spec, output CharacterBible 2.0。
3. **Compute CLIP-I**: 对每个 character 的 7 张图两两计算 CLIP-I cosine similarity,取平均。
4. **Compute DINO-I**: 同上,但用 DINO 自监督特征(更关注 shape / structure)。
5. **Compute negative_trait compliance**: 检查生成的所有图是否符合 negative_traits(如 "no blonde hair" 的 character 不能有金发图)。
6. **Compute cross-character distinctness**: 不同 character 的 anchor 图之间 CLIP-I 应 < 0.65(否则角色辨识度不足)。

**Targets:**

| Metric | Target | Stretch |
|---|---|---|
| Within-character CLIP-I (across 7 imgs) | ≥ 0.85 | ≥ 0.90 |
| Within-character DINO-I | ≥ 0.82 | ≥ 0.88 |
| Negative-trait compliance | ≥ 95% | ≥ 99% |
| Cross-character distinctness (CLIP-I) | ≤ 0.65 | ≤ 0.55 |
| Stress-test pass rate (1st attempt) | ≥ 70% | ≥ 85% |

**Iteration signal**: 当 references/*.md 更新或 prompt 模板调整后,所有 5 个指标必须不下降。

校准数据集和脚本位于 [`_eval/character_benchmark/`](./_eval/character_benchmark/)(若不存在,operator 需创建并标注 ≥ 30 个 character)。

## V8.6 Pipeline Sync (Phase 23 v5.0)

> 来源:kais-movie-agent V8.5 SKILL.md §"L1/L2 双参考角色一致性系统" + §"Step 7 角色资产库完整化" + V8.6 SKILL.md §"hermes-agent 专家 → 管线 Step 速查"。dreamina CLI L1-L4 策略详见 [`_shared/dreamina-cli-baseline.md`](../_shared/dreamina-cli-baseline.md)。

### V8.6 Step Position

character_designer 在 V8.6 管线中位于 **Step 4 主角设计+资产库**(原 V8.4 之前的 Step 4 + Step 6 合并):

| V8.6 Step | 角色 | 共同调用专家 | character_designer 输出 |
|-----------|------|------------|----------------------|
| **Step 4** 主角设计+资产库 | **身份契约定义**(definitions) + 资产库生成协调 | visual_executor(执行图片生成) | CharacterBible 2.0 + L1/L2/L3/L4 asset manifest |

**Step 4 atomic operation 流程:**
1. character_designer 定义 4D-Anchor 多视图身份契约 + STYLE_PREFIX + stress test 规则
2. character_designer 协调 visual_executor 调用 dreamina CLI 生成 L1 候选(`dreamina text2image` × 6 张)
3. 黄金标准检测(per `_shared/dreamina-cli-baseline.md` §"参考图黄金标准")→ 不合格重生 ≤ 3 轮
4. L1 审核通过 → 注册到 CharacterAssetManager 作为永久身份锚点
5. 同流程生成 L2(每套服装正面+侧面各 3 变体)+ L3 姿势包 + L4 表情标定(按需)

### L1/L2/L3/L4 Asset Output Format

character_designer 输出的 CharacterBible 2.0 JSON 必须包含 L1-L4 资产清单,供下游 visual_executor + dreamina CLI 使用:

```yaml
character_assets:
  L1:  # 身份锚点 — 角色参考 (Character Ref),永不更换
    - view: "front_bust"
      path: "assets/L1/front_bust.png"
      dreamina_ref: "Character Ref"  # 角色参考 API 入口
      verified: true
  L2:  # 造型卡片 — 智能参考 (Smart Ref),每套服装一张
    - costume: "default_outfit"
      views: ["front", "side"]
      paths: ["assets/L2/default_front.png", "assets/L2/default_side.png"]
      dreamina_ref: "Smart Ref"
  L3:  # 姿势包 — 智能参考,按需生成
    - pose: "sitting"
      path: "assets/L3/sitting.png"
  L4:  # 表情标定 — 智能参考,表情戏前生成
    - emotion: "smile"
      path: "assets/L4/smile.png"
```

**核心原则**(per baseline §"核心原则"):角色参考只传脸,智能参考传衣服/姿势. 不要混放!

### dreamina CLI 集成角色

character_designer **不直接调用** dreamina CLI —— 它定义身份契约 + 资产清单,由 visual_executor 执行实际图片生成。但 character_designer 必须:

- ✅ 输出 dreamina CLI 兼容的 asset manifest 格式(L1/L2/L3/L4 path + dreamina_ref 标注)
- ✅ 在 CharacterBible 2.0 中明确标注每个 asset 的层级(L1/L2/L3/L4)+ API 入口(Character Ref / Smart Ref)
- ✅ 定义 L1 黄金标准检测规则(供 visual_executor 在 Step 4A 自动重生时使用)

### V8.4 历史背景

V8.4 §1 "专家映射全面更新" 把 hermes-agent v3.0 Phase 17 deprecated 的 `performer` 折叠进 character_designer(voice + behavioral tics)+ screenplay(dialogue subtext)。character_designer 因此承担了**身份契约 + 行为契约**双重职责。

V8.5 §2 "Step 7 角色资产库完整化" 进一步把 L1-L4 资产库管理纳入 character_designer 职责范围。

### Cross-References

- [`_shared/dreamina-cli-baseline.md`](../_shared/dreamina-cli-baseline.md) — L1/L2/L3/L4 完整策略 + 黄金标准(Phase 22 v5.0)
- [`visual_executor/SKILL.md §V8.6 Pipeline Sync`](../visual_executor/SKILL.md) — Step 4 下游执行者
- [`continuity_auditor/SKILL.md §V8.6 Pipeline Sync`](../continuity_auditor/SKILL.md) — Step 9 一致性审计消费 L1-L4
- [`audio_pipeline/SKILL.md §V8.6 Pipeline Sync`](../audio_pipeline/SKILL.md) — voice sub-step 消费 character voice traits
