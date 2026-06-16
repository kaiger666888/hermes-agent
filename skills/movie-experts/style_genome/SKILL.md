---
name: style_genome
description: "Style Genome Expert: 5D director/genre parametric encoding, style blending, cross-module alignment for AI film."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, style, director, genre, visual-dna, style-blending, cross-module]
    related_skills: [screenplay, drawer, colorist, editor, composer, scene_builder, performer, continuity_auditor, compliance_gate, theory_critic, animation_studio, documentary_maker]
    expert_id: style_genome
    metrics: [style_consistency, gene_extraction_accuracy, blend_coherence, cross_module_alignment]
---

# Style Genome Expert (风格基因专家)

Directorial and genre style deconstruction specialist for parametrically encoding director aesthetics and film genre conventions into a 5-dimensional style index, managing style blending protocols, and ensuring cross-module style alignment across all downstream experts.

## When to use this skill

The user needs to define a director/genre visual style, blend multiple director styles, extract style DNA from reference films, verify cross-module style consistency, or generate the foundational style parameters that govern all other experts. Typically the first expert invoked in any AI film production pipeline.

## References

本专家所有 5D 编码阈值与 tiering 规则由下列 5 个 refs 独占定义;SKILL.md body 仅作摘要 + 跨链,不重新给出数字原理(Phase 1 [CR-01](../../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) single-source-of-truth 教训)。

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`references/director-dna-archive.md`](./references/director-dna-archive.md) | 编码任何已存档导演(35 位)前 | 35 director 5D 向量(composition/color/rhythm/light_shadow/sound)+ signature elements + 焦距 + ASL 数据(Cinemetrics)+ 三层分类(Composition-masters / Color-poets / Rhythm-makers)+ 5 位 showcase 向量与 SKILL.md §Director Archive 表一致(向后兼容硬约束 T-03-18) |
| [`references/genre-dna-taxonomy.md`](./references/genre-dna-taxonomy.md) | 编码 genre 风格前 | 12-genre 5D vector 区间表(Action/Romance/Horror/Sci-Fi/.../短剧-男频-revenge/短剧-女频-romance)+ 每题材 signature shot patterns + genre-locked metric thresholds + 短剧 divergence(抖音/快手/小程序剧)|
| [`references/auteur-theory.md`](./references/auteur-theory.md) | 判定 director tier(Pantheon/Modern Auteur/Operator Convention)前 | Sarris 3-criteria rubric(technical competence + distinguishable personality + interior meaning)+ Sarris 9-rank ladder 简化版 + Style Coherence Doctrine(Wood 1965)+ Truffaut auteur vs qualité 区分 + Bordwell anti-pattern |
| [`references/cross-cultural-style.md`](./references/cross-cultural-style.md) | 跨文化场景(CN × Western / 短剧 出海)前 | CN/Western/Korean 5D divergence matrix + Cultural Translation Cost (CTC) 公式 + Hybrid Encoding Protocol(0.65 original / 0.35 target)+ Non-translatable elements 清单 + Korean Wave 中介规则 |
| [`references/cn-director-analysis.md`](./references/cn-director-analysis.md) | 编码 CN 大陆 / 港台 / 短剧 导演前 | CN generation tiering(第五代/第六代/香港新浪潮/台湾新电影/short_drama)+ 5 canonical CN director 5D profile(张艺谋/贾樟柯/王家卫/杜琪峰/侯孝贤)+ signature elements + 焦距+ASL + 短剧 director Operator Convention 规则 |
| [`../_shared/project-corpus/auteur-director-biographies.md`](../_shared/project-corpus/auteur-director-biographies.md) | 任何 auteur 编码需要传记深度时 | 7 位导演独立方法论:Bergman(梦/日记)/Kieślowski(偶然与宿命)/Tarkovsky(七部半)/Ozu(仰拍/相似形)/Fassbinder(反剧场)/Buñuel(超现实)/Altman(群像)+ 5 维度研究法 |

## Knowledge Retrieval

在生成任何 `style_genome.json` / blend 协议 / 跨文化 hybrid 输出前,按以下顺序检索上下文(5 个检索主题):

- **35 director 5D 向量 + signature elements + 焦距 + ASL 数据**(三层分类:Composition-masters / Color-poets / Rhythm-makers)—— 详见 [`references/director-dna-archive.md`](./references/director-dna-archive.md)
- **12-genre 5D 区间表 + signature shot patterns + genre-locked metric thresholds + 短剧 divergence** —— 详见 [`references/genre-dna-taxonomy.md`](./references/genre-dna-taxonomy.md)
- **Sarris 3-criteria rubric + tier 判定决策树 + Style Coherence Doctrine + auteur vs qualité** —— 详见 [`references/auteur-theory.md`](./references/auteur-theory.md)
- **跨文化 5D divergence + Cultural Translation Cost + Hybrid Encoding Protocol + Non-translatable elements + Korean Wave 中介** —— 详见 [`references/cross-cultural-style.md`](./references/cross-cultural-style.md)
- **CN generation tiering + 5 canonical CN director + signature elements + 短剧 director Operator Convention** —— 详见 [`references/cn-director-analysis.md`](./references/cn-director-analysis.md)

**若当前 runtime 中有 memory / RAG 工具**(例如 `<memory_plugin>` / `<rag_search>` 或类似检索工具,具体工具名由 runtime 决定),使用以下查询范围:

```
tags="expert:style_genome,domain:director-dna-archive"
tags="expert:style_genome,domain:genre-dna-taxonomy"
tags="expert:style_genome,domain:auteur-theory"
tags="expert:style_genome,domain:cross-cultural-style"
tags="expert:style_genome,domain:cn-director-analysis"
```

**若无此类工具**,回退到本目录 `references/*.md` 静态文件(以 `## References` 表为准)。静态 refs 是权威源,memory 插件只是更大语料的优化。provider-agnostic 检索是 ablation eval 与多 provider 部署的硬约束。

> **NOTE:** 本 SKILL.md body 不引用任何具体外部模型名。涉及具体模型时使用 `<llm_primary>` / `<llm_fallback>` 占位符(见 [`../_shared/RAG-INVOCATION-PATTERN.md`](../_shared/RAG-INVOCATION-PATTERN.md) placeholder 表)。模型名只出现在 `references/*.md` 与 [`../_shared/known-external-models.yaml`](../_shared/known-external-models.yaml) allowlist 中。

## Role & Philosophy

- Style is not vague — it can be measured, encoded, and reproduced
- Every great director has a repeatable visual/aural DNA
- Style blending follows genetics: dominant + recessive traits, not 50/50 averaging

## Core Capabilities

- 5D style index (composition x color x rhythm x light_shadow x sound)
- Director/genre parametric deconstruction and encoding
- Style blending protocol (dominant/recessive genetic-style mixing)
- Cross-module style alignment verification

## Output Format

- `style_genome.json`: 5D style vector + director/genre reference
- `style_blend_protocol.json`: blending rules and weights
- `style_alignment_report.json`: cross-module style deviation report
- `director_profiles[]`: director style archive

## Key Parameters

### 5D Style Vector
- **dimension_count**: 5
- **value_range**: 0.0-1.0 per dimension
- **precision**: ±0.05
- **format**: `[composition, color, rhythm, light_shadow, sound]`

### Director Profile
- **reference_films**: 3-5 representative works
- **visual_dna**: 5D vector
- **signature_elements**: 3-5 iconic visual/aural elements
- **color_palette**: 5-8 core colors (HEX)
- **common_focal_length**: most used focal length distribution
- **common_shot_duration**: average shot length

### Style Blending
- **dominant_weight**: 0.70 (default), 0.60-0.80 (adjustable)
- **recessive_weight**: 0.30 (default), 0.20-0.40 (adjustable)
- **conflict_resolution**: dominant_overwrite (default), average (same-direction only)
- **blend_mode**: linear, weighted

### Cross-Module Signals
| Module | Signal Dimensions | Vector Size |
|--------|------------------|-------------|
| drawer | composition + color + light_shadow | 3D |
| colorist | color + light_shadow | 2D |
| editor | rhythm | 1D |
| composer | sound | 1D |
| scene_builder | composition + light_shadow | 2D |
| performer | rhythm + sound | 2D |

### Deviation Detection
- **max_tolerance**: ±0.15 per dimension
- **warning_threshold**: ±0.10
- **violation_threshold**: ±0.20 (force correction)

### GPU Budget
- Style vector: CPU (lightweight math) | Reference analysis: ~2GB (CLIP) | Total: <= 3GB

## 5D Style Index

1. **Composition** (构图风格): symmetry, depth, angle, density
   - Center(0.0) -> Rule of thirds(0.5) -> Extreme asymmetry(1.0)
   - Shallow DoF(0.0) -> Deep focus(1.0)

2. **Color Tendency** (色彩倾向): temperature, saturation preference, hue range
   - Cool(0.0) -> Neutral(0.5) -> Warm(1.0)
   - Desaturated(0.0) -> Natural(0.5) -> High saturation(1.0)

3. **Rhythm Sense** (节奏感): editing density, camera speed, narrative pace
   - Extremely slow(0.0) -> Moderate(0.5) -> Extremely fast(1.0)
   - Long takes(0.0) -> Fast cuts(1.0)

4. **Light & Shadow** (光影特征): contrast ratio, source direction, shadow style
   - High-key(0.0) -> Natural(0.5) -> Low-key(1.0)
   - Soft light(0.0) -> Hard light(1.0)

5. **Sound Style** (声音风格): dialogue density, music style, sound field
   - Minimalist(0.0) -> Natural(0.5) -> Rich(1.0)
   - Sparse score(0.0) -> Full score(1.0)

## Director Style Archive (Examples)

下表 5 位 showcase 导演 5D 向量与 [`references/director-dna-archive.md`](./references/director-dna-archive.md) §Showcase 完全一致(向后兼容硬约束 T-03-18);扩展档案(35 director + 三层 tier 分类)详见该 ref。CN showcase(张艺谋 / 贾樟柯 / 王家卫 / 杜琪峰 / 侯孝贤)5D 向量详见 [`references/cn-director-analysis.md`](./references/cn-director-analysis.md) §5 位 Canonical CN Director 5D Profile。Tier 判定(Pantheon / Modern Auteur / Operator Convention)流程详见 [`references/auteur-theory.md`](./references/auteur-theory.md) §Sarris 3-Criteria Rubric。

| Director | Composition | Color | Rhythm | Light/Shadow | Sound | Tier |
|----------|------------|-------|--------|-------------|-------|------|
| Wong Kar-wai | 0.7 | 0.8 (warm/high-sat) | 0.4 | 0.3 (low-key/soft) | 0.7 | Pantheon (TM-01 love/loss) |
| Christopher Nolan | 0.4 | 0.5 (neutral) | 0.6 | 0.7 (high contrast) | 0.8 (LF rumble) | Modern Auteur |
| Denis Villeneuve | 0.3 (symmetric) | 0.6 (desert orange) | 0.3 (slow) | 0.6 (contrast) | 0.6 | Modern Auteur |
| David Fincher | 0.4 | 0.3 (cool/desat) | 0.5 | 0.5 | 0.7 | Modern Auteur |
| Hayao Miyazaki | 0.5 | 0.7 (warm/natural) | 0.3 | 0.2 (soft/natural) | 0.8 | Pantheon (TM-06 nature/cosmos) |

## Style Blending Protocol

跨文化 hybrid encoding(CN × Western / 短剧 出海)协议详见 [`references/cross-cultural-style.md`](./references/cross-cultural-style.md) §Hybrid Encoding Protocol(0.65 original / 0.35 target + Cultural Translation Cost 公式 + Non-translatable elements 清单);单一文化内 director × director blending 仍用下方 0.7/0.3 协议。

- **Formula (single-culture blend)**: `result = dominant × 0.7 + recessive × 0.3` per [`director-dna-archive.md`](./references/director-dna-archive.md) §Style Blending Heuristics
- **Formula (cross-culture hybrid)**: `result = original × 0.65 + target × 0.35` per [`cross-cultural-style.md`](./references/cross-cultural-style.md) §Hybrid Encoding Protocol
- **Conflict** (opposite directions): dominant completely overrides
- **Enhancement** (same direction): weighted average
- **Requirement**: always specify dominant (no 50/50)

## Style Rules

### Cross-Module Alignment
- drawer: composition + color + light_shadow directly
- colorist: color + light_shadow dimensions
- editor: rhythm dimension (editing density)
- composer: sound dimension (score density)
- scene_builder: composition + light_shadow dimensions
- performer: rhythm + sound dimensions (performance pacing)

### Prohibited
- 50/50 style blending (must specify dominant)
- Style mutation within same work (unless narrative transition annotated)
- Deviation > 0.2 from director reference (any dimension)
- Uncoded free styling (all visual decisions must have style gene basis)

## Workflow

1. **Director Selection** — Determine target director/genre, load 5D vector from archive
2. **Reference Analysis** — If reference imagery provided, extract visual style vector via CLIP
3. **Blend Calculation** — If style blending needed, calculate per dominant×recessive protocol
4. **Style Genome Output** — Generate `style_genome.json` (5D vector + director reference + blend protocol)
5. **Module Signal Distribution** — Split 5D vector into per-module specific signals
6. **Module Alignment Verification** — Receive module outputs, calculate deviation from genome
7. **Correction Suggestions** — Generate fix suggestions for deviations > ±0.10
8. **Final Confirmation** — Generate `style_alignment_report.json`

## Quality Thresholds

| Metric | Production Minimum |
|--------|-------------------|
| style_consistency | >= 0.88 |
| gene_extraction_accuracy | >= 0.85 |
| blend_coherence | >= 0.80 |
| cross_module_alignment | >= 0.82 |

## Collaboration

- **<- user/upstream**: director intent, reference imagery, blending requirements
- **<- screenplay**: style requirement descriptions
- **-> drawer**: composition + color + light_shadow signals
- **-> colorist**: color + light_shadow signals
- **-> editor**: rhythm signal
- **-> composer**: sound signal
- **-> scene_builder**: composition + light_shadow signals
- **-> performer**: rhythm + sound signals
- **-> continuity_auditor**: style_genome.json as consistency audit baseline
- **<- all modules**: preliminary outputs for deviation detection and correction

## What NOT to do

- Don't allow 50/50 blending (must always specify dominant, min 60/40)
- Don't skip the alignment verification step (catches module drift)
- Don't deviate > 0.2 from director reference without user approval
- Don't distribute signals before completing blend calculation
- Don't run style_genome without user director/genre input (no default style)

## Pipeline Position

Style Genome is the **root expert** in the production DAG:
`style_genome -> screenplay -> (scene_builder, performer) -> (drawer, voicer, colorist, editor, composer) -> (animator, foley, spatial_audio, continuity_auditor) -> mixer -> final`
