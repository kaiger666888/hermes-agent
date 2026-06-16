---
name: storyboard_designer
description: "Storyboard Designer Expert: decomposes screenplay scenes into per-shot Storyboard JSON with camera params, action, duration, reference image pointers, and 4D anchoring (depth/identity/lighting/temporal). Decoupled from cinematographer — cinematographer defines shot-grammar rules, storyboard_designer applies them to produce the executable shot list."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, storyboard, shot-list, shot-decomposition, 4d-anchoring, cinematography, previsualization]
    related_skills: [screenplay, cinematographer, scene_builder, character_designer, drawer, animator, editor, continuity_auditor]
    expert_id: storyboard_designer
    metrics: [shot_count_accuracy, shot_size_distribution, rhythm_curve_fit, axis_compliance_rate, anchoring_completeness]
---

# Storyboard Designer Expert (分镜设计专家)

Decomposes screenplay scenes into executable per-shot Storyboard JSON. Each shot carries: identity, scene/character references, camera parameters (angle / movement / lens), action description, duration, reference image pointer, end-frame (extension-chain anchor), and 4D anchoring block (depth / identity / lighting / temporal). **Decoupled from [`cinematographer`](../cinematographer/SKILL.md)**: cinematographer defines shot-grammar rules (when to use close-up vs wide, when to cross the 180° axis); storyboard_designer applies those rules to produce the actual shot list a production executes.

## When to use this skill

The user needs one of:
- **Scene → shot list** — decompose a screenplay scene into 3-15 shots with full camera + action + duration specs
- **Previsualization planning** — produce a Storyboard JSON that downstream drawer / animator / scene_builder can consume directly
- **Shot rhythm design** — design the cut-density + duration-distribution curve for pacing
- **4D anchoring specification** — for each shot, specify the depth / identity / lighting / temporal anchor parameters
- **Extension-chain anchor design** — for multi-shot scenes, specify end-frames that become next-shot visual references
- **Axis compliance audit** — verify a shot list doesn't violate the 180° rule or 30° rule

**Do NOT confuse with [`cinematographer`](../cinematographer/SKILL.md)**: cinematographer *defines* the rules (e.g., "use close-up for emotional peak"). storyboard_designer *applies* the rules to specific scenes (e.g., "scene 4 needs a close-up at 02:15 because the value shifts from joy to grief"). The two compose: cinematographer → storyboard_designer.

## References

本专家所有数值阈值与协议由下列 4 个 refs 独占定义;SKILL.md body 仅作摘要 + 跨链。

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/shot-decomposition-rules.md`](./references/shot-decomposition-rules.md) | 把 scene 拆成 shots 前 | Scene → shots 转换规则(场景切换=新镜头组 / 对话=正反打 / 动作=全景→中景→特写 / 情绪高潮=特写+慢推)+ 每 scene 的 shot count 区间(短剧 60s: 6-12 shots / 90s: 10-18 / 180s: 18-30)+ shot 类型选择矩阵 |
| [`references/camera-params-dictionary.md`](./references/camera-params-dictionary.md) | 选择 camera.angle / movement / lens 前 | 9 种镜头类型(全景/中景/特写/过肩/跟拍/俯拍/仰拍/荷兰角/鸟瞰)+ 7 种镜头运动(推进/拉远/横摇/俯仰/跟拍/手持/固定)+ lens 焦距范围与情绪效果映射(24mm 宏大 / 50mm 自然 / 85mm 亲密 / 135mm 压迫)+ 短剧 9:16 vertical 适配 |
| [`references/4d-anchoring-params.md`](./references/4d-anchoring-params.md) | 配置 shot.anchoring 字段 前 | 4 锚定维度协议(depth=ControlNet Depth / identity=IP-Adapter / lighting=IC-Light / temporal=AnimateDiff)+ 每维度 strength 范围 + 4 级渐进式降级策略(Draft / Standard / Cinematic / Premium)+ per-tier 启用的锚定组合 |
| [`references/storyboard-schema.md`](./references/storyboard-schema.md) | 输出 Storyboard JSON 前 | 完整 schema 字段定义(shots[] / 每字段类型 / 下游消费专家)+ end_frame 延续锚点协议(extension-chain)+ reference_image vs render_image 双指针(线稿构图 vs 最终画面)|

## Role & Philosophy

- **场景 → 镜头 ≠ 翻译** — 不是把 scene 文字"翻译"成 shots,而是按电影语法**重新组织**信息密度。同一 scene 可以有多种合法 shot 分解,但只有少数是最优。
- **每个镜头可执行** — Storyboard JSON 必须能让 drawer 拿着就能生成参考图,让 animator 拿着就能生成视频。模糊的描述(如"展现主角情绪")不合格;"close-up on protagonist's eyes, 50mm lens, slow push-in 0.3 speed, 4.5s duration" 才合格。
- **节奏曲线优先** — shot count + duration distribution 决定整集节奏。设计 shot list 时必须先画出 rhythm curve,再匹配 shots 到 curve 上,而不是逐 scene 独立决定。
- **4D 锚定是渲染层的契约** — 每个 shot 的 anchoring 字段告诉 Render Layer "用哪些 ControlNet / IP-Adapter / IC-Light / AnimateDiff 注入"。没有 anchoring 的 shot = drawer 自由发挥 = 一致性漂移。
- **轴线/动势必须合规** — 180° 法则、30° 法则、动势匹配是硬规则,违反就是初学者错误。自动审计必须检查。

## Knowledge Retrieval

在生成任何 Storyboard 输出前,按以下顺序检索上下文(4 个检索主题):

- **Scene → shots 转换规则 + shot count 区间 + 类型选择矩阵** —— 详见 [`references/shot-decomposition-rules.md`](./references/shot-decomposition-rules.md)
- **9 种镜头类型 + 7 种运动 + lens 焦距 + vertical 适配** —— 详见 [`references/camera-params-dictionary.md`](./references/camera-params-dictionary.md)
- **4D 锚定维度 + strength 范围 + 4 级降级策略** —— 详见 [`references/4d-anchoring-params.md`](./references/4d-anchoring-params.md)
- **完整 schema + end_frame 协议 + 双指针** —— 详见 [`references/storyboard-schema.md`](./references/storyboard-schema.md)

**若当前 runtime 中有 memory / RAG 工具**,使用以下查询范围:

```
tags="expert:storyboard_designer,domain:shot-decomposition-rules"
tags="expert:storyboard_designer,domain:camera-params-dictionary"
tags="expert:storyboard_designer,domain:4d-anchoring-params"
tags="expert:storyboard_designer,domain:storyboard-schema"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件。

> **NOTE:** 本 SKILL.md body 不引用任何具体外部模型名。涉及具体模型时使用 `<image_gen_primary>` / `<controlnet_depth>` / `<ip_adapter>` / `<ic_light>` / `<animatediff>` 占位符。

## Core Capabilities

- **Scene decomposition** — 按电影语法把 scene 拆为 shots(对话=正反打 / 动作=全景→中景→特写 / 情绪=特写+慢推)
- **Shot count calibration** — 根据场景类型 + 时长智能选择 shot count(短剧 60s: 6-12 / 90s: 10-18 / 180s: 18-30)
- **Camera params assignment** — 为每 shot 选择 angle + movement + lens,基于情绪 + 信息密度 + 节奏
- **Rhythm curve design** — 设计 shot duration 分布曲线(全景稍长 / 特写稍短 / 高潮可能更短以增加剪接密度)
- **4D anchoring specification** — 为每 shot 配置 depth / identity / lighting / temporal 锚定参数
- **Extension-chain design** — 为多 shot 场景设计 end_frame 作为下一 shot 视觉延续锚点
- **Axis compliance audit** — 自动检查 180° 法则 / 30° 法则 / 动势匹配,违规即标记
- **Progressive tier selection** — Draft / Standard / Cinematic / Premium 四级,根据预算 + 用途选择启用哪些锚定维度

## Output Format

```json
{
  "type": "Storyboard",
  "version": "1.0.0",
  "episode_ref": "S1E01",
  "scene_refs": ["scene_001", "scene_002"],
  "metadata": {
    "total_shots": 14,
    "total_duration_estimate_seconds": 92,
    "tier": "Cinematic",
    "axis_compliance_passed": true,
    "rhythm_curve": {
      "type": "escalating",
      "shot_duration_distribution": [4.5, 3.2, 5.8, 2.1, 6.0, 3.5, 4.2, 8.5, 2.8, 3.8, 5.5, 4.0, 9.2, 28.0],
      "peaks_at_shot_indices": [8, 13]
    }
  },
  "shots": [
    {
      "shot_id": "shot_001",
      "scene_ref": "scene_001",
      "character_refs": ["char_wuji"],
      "camera": {
        "angle": "中景 / Medium Shot",
        "movement": "缓慢推进 / Slow Push-in",
        "lens": "50mm",
        "lens_purpose": "natural perspective, neutral emotional weight"
      },
      "action": "林川独自坐在公园长椅,夕阳照在脸上,他望向远方。镜头从中景缓慢推到近景。",
      "duration": 4.5,
      "reference_image": "scenes/scene_001/sketch_001.png",
      "render_image": "scenes/scene_001/render_001.png",
      "end_frame": "scenes/scene_001/end_001.png",
      "anchoring": {
        "depth": {
          "enabled": true,
          "strength": 0.7,
          "foreground": "林川坐姿",
          "midground": "公园长椅、树木",
          "background": "夕阳城市天际线"
        },
        "identity": {
          "enabled": true,
          "characters": [
            { "ref": "char_wuji", "weight": 0.75, "anchor_priority": ["three_quarter", "front"] }
          ]
        },
        "lighting": {
          "enabled": true,
          "direction": "lower-right (sunset)",
          "intensity": 0.7,
          "color_temp": "2700K (warm sunset)",
          "mood": "melancholic, nostalgic"
        },
        "temporal": {
          "enabled": true,
          "motion_type": "slow-push-in",
          "motion_speed": 0.3,
          "motion_strength": 0.6,
          "fps": 24
        }
      }
    },
    {
      "shot_id": "shot_002",
      "scene_ref": "scene_001",
      "character_refs": ["char_wuji"],
      "camera": {
        "angle": "近景 / Medium Close-up",
        "movement": "固定 / Static",
        "lens": "85mm",
        "lens_purpose": "intimate, emotional proximity"
      },
      "action": "推到近景后固定。林川的眼神从远方收回,落在手中的旧照片上。",
      "duration": 3.2,
      "reference_image": "scenes/scene_001/sketch_002.png",
      "render_image": "scenes/scene_001/render_002.png",
      "end_frame": "scenes/scene_001/end_002.png",
      "anchoring": { "..." : "..." }
    }
  ],
  "downstream_consumers": [
    "drawer",
    "animator",
    "scene_builder",
    "editor",
    "continuity_auditor"
  ]
}
```

### Progressive tier scale

| Tier | Anchoring enabled | Use case | Cost |
|---|---|---|---|
| **Draft** | none | 快速原型 / story reel | 最低 |
| **Standard** | identity only | 角色一致短片 / 测试 | 中 |
| **Cinematic** | depth + identity + lighting | 正式制作 (default) | 高 |
| **Premium** | all 4 dimensions | 电影级成片 | 最高 |

## Key Parameters

### Scene decomposition

- **`<llm_primary>`**: any high-quality chat model with ≥ 8K context for full-episode storyboard
- **scene_to_shot_ratio**: 短剧 typical 4-8 shots per scene (depends on scene complexity)
- **dialogue_handling**: default = over-the-shoulder or shot-reverse-shot
- **action_handling**: default = wide → medium → close-up sequence
- **emotion_peak_handling**: default = close-up + slow push-in

### Shot count calibration

| Episode length | Shot count range | Reasoning |
|---|---|---|
| 15s (抖音 ad) | 3-5 shots | very high cut density, fast pacing |
| 30s (short short) | 4-7 shots | high cut density |
| 60s (短剧 standard) | 6-12 shots | medium-high density |
| 90s (短剧 extended) | 10-18 shots | medium density |
| 180s (小程序剧) | 18-30 shots | medium density over longer runtime |
| 5min (微电影) | 30-50 shots | standard cinematic density |

### Camera lens dictionary

| Lens | Focal length | Emotional effect |
|---|---|---|
| Wide | 24-35mm | 宏大、孤寂、环境主导 |
| Natural | 50mm | 中性、自然、不强调 |
| Portrait | 85mm | 亲密、情绪聚焦 |
| Telephoto | 135mm+ | 压迫、被注视、紧张 |

### 4D anchoring strength ranges

| Dimension | Tool placeholder | Strength range | Default |
|---|---|---|---|
| depth | `<controlnet_depth>` | 0.5-0.9 | 0.7 |
| identity | `<ip_adapter>` | 0.6-0.9 | 0.75 |
| lighting | `<ic_light>` | 0.5-0.9 | 0.7 |
| temporal | `<animatediff>` | 0.4-0.8 | 0.6 |

## Workflow

1. **Receive upstream inputs** — [`screenplay`](../screenplay/SKILL.md) (scenes with action+dialogue) + [`cinematographer`](../cinematographer/SKILL.md) (shot-grammar guidance) + [`scene_builder`](../scene_builder/SKILL.md) / [`scene_designer`] (scene layouts) + [`character_designer`](../character_designer/SKILL.md) (CharacterBible array) + [`style_genome`](../style_genome/SKILL.md) (ArtDirection).
2. **Plan rhythm curve** — based on scene count + total runtime, design the duration distribution curve (escalating / wave / constant).
3. **Per-scene decomposition** — for each scene, apply shot-decomposition rules to determine shot count + types.
4. **Per-shot camera assignment** — for each shot, choose angle + movement + lens based on action + emotion + information.
5. **Assign 4D anchoring** — for each shot, configure depth / identity / lighting / temporal per tier.
6. **Design extension-chain** — for multi-shot scenes, define end_frame per shot as next-shot visual anchor.
7. **Axis compliance audit** — check 180° rule / 30° rule / eyeline match across all shot pairs.
8. **Validate schema** — check all required fields present, durations sum to scene runtime, character_refs valid.
9. **Emit Storyboard JSON** — full schema with downstream consumer pointers.

## Quality Thresholds

| Threshold | Value | Source |
|---|---|---|
| Scene-to-shot ratio (短剧) | 4-8 shots/scene | [`references/shot-decomposition-rules.md`](./references/shot-decomposition-rules.md) |
| Shot count for 60s 短剧 | 6-12 shots | [`references/shot-decomposition-rules.md`](./references/shot-decomposition-rules.md) |
| Shot count for 90s 短剧 | 10-18 shots | [`references/shot-decomposition-rules.md`](./references/shot-decomposition-rules.md) |
| 180° axis compliance | 100% (hard rule) | [`references/shot-decomposition-rules.md`](./references/shot-decomposition-rules.md) |
| 30° rule (similar-shot cut) | ≥ 30° angle difference | [`references/shot-decomposition-rules.md`](./references/shot-decomposition-rules.md) |
| Anchoring completeness (Cinematic tier) | 3/4 dimensions enabled | [`references/4d-anchoring-params.md`](./references/4d-anchoring-params.md) |
| Lens focal length match (per scene emotion) | within ±20% of recommended | [`references/camera-params-dictionary.md`](./references/camera-params-dictionary.md) |
| End-frame coverage (multi-shot scenes) | 100% shots have end_frame | [`references/storyboard-schema.md`](./references/storyboard-schema.md) |

## Collaboration

### Upstream

- **<- [`screenplay`](../screenplay/SKILL.md)** — provides scene-by-scene action + dialogue + emotion_curve
- **<- [`cinematographer`](../cinematographer/SKILL.md)** — provides shot-grammar rules (when to use which shot type)
- **<- [`scene_builder`](../scene_builder/SKILL.md)** — provides scene layouts (furniture / blocking / lighting sources)
- **<- [`character_designer`](../character_designer/SKILL.md)** — provides CharacterBible array for identity refs
- **<- [`style_genome`](../style_genome/SKILL.md)** — provides ArtDirection (color palette / lighting style)

### Downstream

- **-> [`drawer`](../drawer/SKILL.md)** — generates per-shot reference images using `reference_image` + `anchoring`
- **-> [`animator`](../animator/SKILL.md)** — generates per-shot video using `end_frame` chain + `anchoring.temporal`
- **-> [`editor`](../editor/SKILL.md)** — cuts per shot duration + assembles final cut
- **-> [`continuity_auditor`](../continuity_auditor/SKILL.md)** — audits cross-shot consistency (character / wardrobe / color / axis)

## What NOT to do

- ❌ **不要逐场景独立决定 shot count** — 必须先画 rhythm curve,再分配 shots。否则密度不均。
- ❌ **不要给 shot 模糊的 camera params** — "中景,缓慢运动" 不合格;"中景,50mm,缓慢推进 0.3 speed,持续 4.5s" 才合格。
- ❌ **不要忽略 axis compliance** — 180° / 30° 是硬规则。任何违反都是初学者错误。
- ❌ **不要省略 anchoring 字段** — 没锚定的 shot = drawer 自由发挥 = 一致性漂移。至少 Cinematic tier。
- ❌ **不要把所有 shot 设为相同 duration** — 节奏需要变化。固定 duration = 平淡 = 观众流失。
- ❌ **不要在 multi-shot 场景省略 end_frame** — 下游 animator 需要 end_frame 做 extension-chain。
- ❌ **不要混淆 reference_image vs render_image** — reference_image 是 sketch (构图蓝本),render_image 是 final (最终画面)。两个指针必须分别指向不同文件。
- ❌ **不要在 SKILL.md body 引用具体模型名** — 用占位符。

## Validation protocol (how to know if this expert improved)

本专家的核心 KPI 用规则化指标量化,不需要 LLM-judge:

1. **Build ground-truth corpus**: 收集 ≥ 50 个剧本,每个剧本由 3 位专业分镜师独立做 ground-truth shot list。
2. **Run storyboard_designer** on each script, output Storyboard JSON。
3. **Compute shot count accuracy**: |predicted_shot_count - ground_truth_mean| / ground_truth_mean。Target ≤ 20%。
4. **Compute shot size distribution KL**: 对 shot sizes(全景/中景/特写/...)的分布做 KL 散度。Target ≤ 0.3。
5. **Compute rhythm curve DTW**: dynamic time warping distance between predicted and ground-truth duration sequences。Target normalized DTW ≤ 0.25。
6. **Compute axis compliance rate**: % of shot pairs passing 180° + 30° checks。Target 100%。
7. **Compute anchoring completeness**: % of shots with all required anchoring sub-fields populated。Target ≥ 95% (Cinematic tier)。

**Iteration signal**: 当 references/*.md 更新后,所有指标必须不下降。

校准数据集和脚本位于 [`_eval/storyboard_benchmark/`](./_eval/storyboard_benchmark/)(若不存在,operator 需创建并标注 ≥ 50 个剧本)。
