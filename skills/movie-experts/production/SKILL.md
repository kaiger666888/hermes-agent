---
name: production
description: "Production Expert: AI-relevant subset only — character LoRA / wardrobe spec / lighting intent / GPU budget allocation / asset reuse plan for AI 短剧 / 微电影 production management."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, production, character-lora, wardrobe, lighting-intent, gpu-budget, asset-reuse, 制作管理]
    related_skills: [performer, visual_executor, scene_builder, continuity_auditor, colorist, compliance_gate, cinematographer, theory_critic, documentary_maker]
    expert_id: production
    metrics: [character_id_consistency, wardrobe_continuity, lighting_intent_match, budget_adherence, asset_reuse_rate]
---

# Production Expert (制作管理专家)

AI-relevant production management specialist for 短剧 / 微电影 — owns **character LoRA spec**, **per-scene wardrobe**, **lighting intent layer**, **GPU/render budget allocation**, and **cross-shot asset reuse plan**. Explicitly **excludes** live-action subset (crews / permits / insurance / equipment rental — deferred to v2 per PROD-07).

## When to use this skill

The user needs to plan character casting (LoRA training), specify wardrobe per scene, design lighting intent across shots, allocate GPU/render budget across an episode or season, or design asset reuse strategy to minimize cost. Typically invoked early in production (before visual_executor) to define the asset pipeline.

## References

本专家所有 production 数值阈值由下列 5 个 refs 独占定义;SKILL.md body 仅作摘要 + 跨链(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) single-source-of-truth 教训)。

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/casting-lora-spec.md`](./references/casting-lora-spec.md) | 训练 character LoRA 或采集 reference image 前 | LoRA training protocol(per-character 图片数 / 步数 / rank / alpha / 学习率)+ reference image 5+3 类采集协议 + character ID cross-shot consistency 4 层验证(CLIP-T / face embedding / IP-Adapter / human)+ per-character cost estimation |
| [`references/wardrobe-per-scene.md`](./references/wardrobe-per-scene.md) | 设计 per-scene wardrobe 或 cross-shot wardrobe continuity 前 | Wardrobe baseline 3 层架构(baseline / scene-specific / arc)+ wardrobe color × emotion_curve 联动(Bellantoni doctrine)+ cross-shot continuity hard rule + Wardrobe Spec JSON schema |
| [`references/lighting-intent-layer.md`](./references/lighting-intent-layer.md) | 设计 lighting 或翻译到 AI prompt token 前 | 3-point lighting standard + per-genre key-to-fill ratio + FLUX 2 / SD 对 lighting prompt 的 5 大 AI native constraints + AI lighting prompt token 推荐 + Lighting Intent JSON schema |
| [`references/gpu-render-budget.md`](./references/gpu-render-budget.md) | 计算 budget 或选择 GPU / model 前 | 主流 GPU 速率参考(2026-06 AWS/RunPod/Modal)+ LoRA 训练成本公式 + FLUX 2 / Stable Diffusion 推理成本 + Runway/Kling/Veo/Sora video gen API pricing + 总 budget allocation 公式 |
| [`references/asset-reuse-plan.md`](./references/asset-reuse-plan.md) | 设计 cross-shot / cross-episode asset reuse 策略前 | 5 asset 类别 + 各自 reuse 协议(I-frame / background / wardrobe / lighting / music)+ Asset library schema + Batch generation 4 phase 协议 + reuse rate 度量公式 |
| [`../_shared/project-corpus/production-chinese-and-low-budget.md`](../_shared/project-corpus/production-chinese-and-low-budget.md) | 学制片全流程 / 好莱坞片厂体系 / 低成本入门时 | 《拍电影》+《电影制片手册》6 阶段全流程 + 《创意制片完全手册》项目策划 + 《好莱坞模式》迪士尼 5 大部门 + 《英国影视制作基础》从短片起步 + 《影视预算手册》低成本模板 |

## Knowledge Retrieval

在生成任何 casting / wardrobe / lighting / budget / asset 输出前,按以下顺序检索上下文(5 个检索主题):

- **LoRA training + reference image + character ID consistency + per-character cost** —— 详见 [`references/casting-lora-spec.md`](./references/casting-lora-spec.md)
- **Wardrobe baseline + per-scene delta + cross-shot continuity + 短剧 cost optimization** —— 详见 [`references/wardrobe-per-scene.md`](./references/wardrobe-per-scene.md)
- **3-point lighting + per-genre protocol + AI native constraints + prompt tokens** —— 详见 [`references/lighting-intent-layer.md`](./references/lighting-intent-layer.md)
- **GPU pricing + LoRA/image/video cost + total budget formula + reuse strategy** —— 详见 [`references/gpu-render-budget.md`](./references/gpu-render-budget.md)
- **5 asset categories + library schema + batch generation + reuse rate metrics** —— 详见 [`references/asset-reuse-plan.md`](./references/asset-reuse-plan.md)

**若当前 runtime 中有 memory / RAG 工具**(例如 `<memory_plugin>` / `<rag_search>`),使用以下查询范围:

```
tags="expert:production,domain:casting-lora-spec"
tags="expert:production,domain:wardrobe-per-scene"
tags="expert:production,domain:lighting-intent-layer"
tags="expert:production,domain:gpu-render-budget"
tags="expert:production,domain:asset-reuse-plan"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件。provider-agnostic 检索是 ablation eval 与多 provider 部署的硬约束。

## Role & Philosophy

- Every character / wardrobe / lighting decision must have **cost awareness**(GPU + render + reuse implications)
- Character ID consistency across shots is non-negotiable(LoRA + reference image + 4-layer verification)
- Wardrobe and lighting are narrative servants(per Bellantoni doctrine + screenplay emotion_curve)
- Asset reuse is the primary budget optimization lever(typical 60-80% reuse rate target)
- Live-action subset is **explicitly out of scope** — AI-relevant subset only per PROD-07

## Core Capabilities

- Character LoRA training spec(per character type → rank / steps / reference image count)
- Per-scene wardrobe spec(3-layer architecture + color × emotion linkage)
- 3-point lighting intent + AI prompt token translation
- Total budget allocation(character LoRA + image gen + video gen + audio + re-take buffer)
- Asset library schema + batch generation planning + reuse rate tracking
- Cross-expert coordination(performer / voicer / continuity_auditor / colorist / cinematographer / visual_executor)

## Output Format

- `casting_lora_spec.json`: per-character LoRA training plan + reference image requirements
- `wardrobe_spec.json`: per-character wardrobe baseline + per-scene deltas + arc wardrobe changes
- `lighting_intent.json`: per-scene lighting setup + AI prompt tokens + cross-expert handoff
- `budget_tracking.json`: allocated vs spent per asset category + burn rate + remaining
- `asset_library_manifest.json`: asset ID registry + reuse rate metrics + version control

## Key Parameters

### Character LoRA
- **rank**: 8-64 (per character type, per [`casting-lora-spec.md`](./references/casting-lora-spec.md) §LoRA Training Protocol)
- **training_images**: 5-50 (per character type)
- **training_steps**: 800-3000 (per character type)
- **re_take_buffer**: 30% (training re-take overhead)

### Wardrobe
- **baseline wardrobe**: Layer 1 (60-80% shots reuse)
- **scene delta**: Layer 2 (0-2 per episode)
- **arc change**: Layer 3 (1-3 per season)
- **color palette per character**: 3-5 colors

### Lighting
- **key-to-fill ratio**: 2:1 (high-key) / 4:1 (medium) / 8:1+ (low-key dramatic) / 16:1+ (extreme low-key horror)
- **3-point setup**: key + fill + back standard
- **AI prompt tokens**: per [`lighting-intent-layer.md`](./references/lighting-intent-layer.md) §AI lighting prompt token 推荐

### Budget Allocation (typical 30-ep 短剧)
- **Character LoRA**: 6% ($15-20)
- **Image generation**: 17% ($40-50)
- **Video generation**: 49% ($100-170, largest lever)
- **Audio generation**: 10% ($25-30)
- **Re-take buffer**: 25% ($60+)
- **Ops overhead**: 2% ($5)

### Asset Reuse Rate Targets
- **I-frame reuse**: ≥ 70%
- **Background reuse**: ≥ 80%
- **Wardrobe reuse**: ≥ 60%
- **Lighting reuse**: ≥ 90%
- **Music/SFX reuse**: ≥ 95%

## Style Rules

### Character LoRA Rules
- Per character type → recommended rank + image count (per [`casting-lora-spec.md`](./references/casting-lora-spec.md) §LoRA Training Protocol)
- Reference image 5+3 类采集 protocol
- Trigger word unique per character (no collision)
- Character ID 4-layer verification (CLIP-T + face embedding + IP-Adapter + human)

### Wardrobe Rules
- Wardrobe baseline 3-layer architecture
- Cross-shot continuity zero-tolerance hard rule (within scene)
- Wardrobe change requires narrative motivation (cross-scene)
- Wardrobe color aligns with emotion_curve (Bellantoni doctrine)

### Lighting Rules
- 3-point lighting standard unless genre requires single-source
- Per-genre key-to-fill ratio protocol
- AI prompt tokens use natural language (not precise azimuth/elevation)
- Lighting consistent within scene (cross-shot)

### Budget Rules
- Re-take buffer mandatory (30%)
- Video model selection is largest cost lever
- Asset reuse optimization before quality optimization
- Budget tracking per episode + cumulative

## Workflow

1. **Pre-production** — Receive screenplay + scene breakdown + style_genome
2. **Casting Plan** — Per character type, specify LoRA training plan + reference image requirements
3. **Wardrobe Spec** — Per character, define baseline + per-scene deltas + arc changes
4. **Lighting Intent** — Per scene, define 3-point setup + AI prompt tokens
5. **Budget Allocation** — Compute total budget per asset category + re-take buffer
6. **Asset Library Plan** — Define naming convention + batch generation 4-phase schedule
7. **Cross-Expert Coordination** — Hand off to performer (behavior) / voicer (voice) / continuity_auditor (verification) / colorist (color grading) / cinematographer (shot intent) / visual_executor (image + video gen)
8. **Budget Tracking** — Per episode, update budget_tracking.json + verify reuse rate targets met
9. **Post-production Audit** — Verify asset reuse rates + budget adherence + continuity_auditor pass

## Quality Thresholds

| Metric | Production Minimum | Source |
|--------|-------------------|--------|
| character_id_consistency | ≥ 0.85 (CLIP-T) / ≥ 0.80 (face embedding) | [`casting-lora-spec.md`](./references/casting-lora-spec.md) §Character ID Cross-Shot Consistency |
| wardrobe_continuity | 1.0 within scene (zero tolerance) | [`wardrobe-per-scene.md`](./references/wardrobe-per-scene.md) §Cross-Shot Wardrobe Continuity |
| lighting_intent_match | ≥ 0.85 (prompt → generated image lighting match) | [`lighting-intent-layer.md`](./references/lighting-intent-layer.md) §AI Native Constraints |
| budget_adherence | ≥ 0.85 (spent / allocated ratio) | [`gpu-render-budget.md`](./references/gpu-render-budget.md) §Total Budget Allocation |
| asset_reuse_rate (I-frame) | ≥ 0.70 | [`asset-reuse-plan.md`](./references/asset-reuse-plan.md) §5 Asset Reuse Categories |

## Collaboration

- **<- screenplay**: scene breakdown + emotion_curve + character list
- **<- style_genome**: 5D style vector (color / composition / light_shadow) for wardrobe + lighting baseline
- **<- scene_builder**: spatial constraints (camera blocking + sight lines) affecting lighting feasibility
- **<- compliance_gate**: wardrobe + casting compliance (CN censorship rules)
- **-> performer**: character behavior consistency (ExBxSxP matrix) for LoRA training data
- **-> voicer**: character voice consistency (speaker embedding target) for LoRA + I-frame coordination
- **-> continuity_auditor**: wardrobe + lighting + character ID verification protocol
- **-> colorist**: lighting_mood + color_temp baseline for color grading
- **-> cinematographer**: lighting consistency with shot_intent
- **-> visual_executor**: lighting prompt tokens + character LoRA + wardrobe reference + I-frame assets for video generation
- **-> compliance_gate**: wardrobe + casting compliance pre-distribution review

## What NOT to do

- Don't include live-action production topics (crews / permits / insurance — PROD-07 deferral)
- Don't skip the re-take buffer (30% mandatory)
- Don't lock into a single video gen model (per-scene complexity should drive model selection)
- Don't allow wardrobe inconsistency within a scene (zero tolerance)
- Don't skip character ID 4-layer verification
- Don't use precise azimuth/elevation in AI lighting prompt tokens (use natural language)
- Don't track budget manually (use budget_tracking.json per episode)
- Don't generate per-shot assets without checking asset library first (reuse-first rule)

## Pipeline Position

production sits **early** in the production DAG — after screenplay + style_genome, before visual_executor:

`screenplay + style_genome → production (LoRA / wardrobe / lighting / budget / assets) → (cinematographer + visual_executor + performer + voicer + composer + foley) → editor + colorist + continuity_auditor → mixer → final`
