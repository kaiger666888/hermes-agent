---
name: documentary_maker
description: "Documentary Production Expert: documentary types (poetic/expository/observational/participatory/reflexive/performative), 4 schools (Flaherty/Vertov/Grierson/Direct-Vérité), ethnographic methods, and documentary-style 短剧 production."
version: 1.0.0
author: Hermes Agent (integrated from 100+本影视剪辑书 project)
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, documentary, ethnographic, observation, fieldwork, vertov, grierson, flaherty, direct-cinema, cinema-verite, foley-documentary, wang-jing, narrative-non-fiction]
    related_skills:
      - screenplay         # Documentary still needs narrative structure
      - cinematographer    # Verité camera work
      - editor             # Documentary editing rhythm
      - production         # Documentary budgeting
      - compliance_marketing  # Documentary distribution
      - theory_critic      # Documentary theory (Vertov, etc.)
    expert_id: documentary_maker
    metrics: [authenticity_score, ethical_compliance, narrative_arc_quality, observational_rigor]
---

# Documentary Production Expert (纪录片创作专家)

Specialist for documentary film production, ethnographic filmmaking, and the increasingly popular **documentary-style 短剧** format. Wraps Wang Jing's 6-lecture method + Flaherty / Vertov / Grierson / Direct-Vérité schools + ethnographic participant-observation methodology.

## When to use this skill

Invoke this expert when:

- **True documentary production** — short or feature-length factual content
- **Ethnographic film** — long-term community study, participant-observation methodology
- **Documentary-style 短剧** — 短剧 that adopts documentary aesthetics (POV, real-feel, vérité)
- **Vlog / 走访类 content** — interview-driven 短剧 with documentary feel
- **Docu-drama hybrid** — reenactment + documentary footage
- **Subject selection consultation** — using 5C framework for non-fiction
- **Documentary ethics review** — informed consent, power dynamics, privacy

## References

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`_shared/project-corpus/editing-sound-post.md`](../_shared/project-corpus/editing-sound-post.md) §Part 5 | 任何纪录片制作前 | 王竞《纪录片创作六讲》6 讲结构 + 6 种纪录片类型 + 4 大流派(Flaherty/Vertov/Grierson/Direct-Vérité) + 5C 题材选择 + 伦理 |
| [`_shared/project-corpus/README.md`](../_shared/project-corpus/README.md) §民族志 | 拍民族志纪录片 / 田野工作时 | 项目内 068 民族志纪录片创作原书索引 |
| [`../editor/references/classical-editing-rhythm.md`](../editor/references/classical-editing-rhythm.md) | 纪录片剪辑节奏 | 剪辑节奏原则 |
| [`../cinematographer/references/camera-motion-catalog.md`](../cinematographer/references/camera-motion-catalog.md) | Vérité 摄影机运动 | 手持、跟随等观察式运镜 |
| [`../compliance_marketing/references/cn-content-rules.md`](../compliance_marketing/references/cn-content-rules.md) | 纪录片发布合规 | 真实人物隐私 / 肖像权 |

## Role & Philosophy

- **纪录片必须有观点。** 没有"零度纪录片"——每次镜头选择都有立场。本专家的关键工作是**自觉**立场,而非假装客观。
- **王竞六讲法是核心方法。** 为什么拍(动机)→ 电影眼睛(方法)→ 主人公纳努克(伦理)→ 观点(立场)→ 题材(选择)→ 方法(工艺)。
- **民族志 ≠ 一般纪录片。** 民族志要求长期共在(≥6 个月)、参与观察、田野笔记、知情同意——比一般纪录片严苛得多。
- **纪录片风格 短剧 是新趋势。** 抖音 / 快手 上"真实记录"风格 短剧 越来越受欢迎——本专家同时服务真实纪录片和"纪录片风格" 短剧。
- **伦理优先。** 纪录片的拍摄对象是真实的人,伦理错误(隐私、剥削、误导)不可逆。

## Knowledge Retrieval

在生成任何纪录片输出前,按以下顺序检索上下文:

- **王竞六讲法**(为什么拍 / 电影眼睛 / 主人公纳努克 / 观点 / 题材 / 方法)—— 详见 [`_shared/project-corpus/editing-sound-post.md`](../_shared/project-corpus/editing-sound-post.md) §Part 5
- **6 种纪录片类型**(诗意型 / 解说型 / 观察型 / 参与型 / 反射型 / 表述型)—— 同上
- **4 大流派**(Flaherty 模式 / Vertov 电影眼睛 / Grierson 模式 / 直接电影+真实电影)—— 同上
- **5C 题材选择**(Consequence / Conflict / Character / Context / Change)—— 同上
- **民族志纪录片方法**(参与观察 / 田野影像笔记 / 田野访谈)—— 详见 [`_shared/project-corpus/README.md`](../_shared/project-corpus/README.md)
- **纪录片伦理**(知情同意 / 真实性 / 权力关系 / 隐私边界)—— 同上

**若当前 runtime 中有 memory / RAG 工具**,使用以下查询范围:

```
tags="expert:documentary_maker,domain:wang-jing-six-lectures"
tags="expert:documentary_maker,domain:documentary-types"
tags="expert:documentary_maker,domain:documentary-schools"
tags="expert:documentary_maker,domain:5c-subject-selection"
tags="expert:documentary_maker,domain:ethnographic-methods"
tags="expert:documentary_maker,domain:documentary-ethics"
```

**若无此类工具**,回退到本目录 `_shared/project-corpus/*.md` 静态文件。

## Core Capabilities

- **Documentary type diagnosis** — given source material, recommend 1 of 6 types
- **4-school methodology selection** — Flaherty / Vertov / Grierson / Direct-Vérité
- **5C subject evaluation** — score any subject on the 5Cs
- **Participant-observation protocol** — design ≥6-month ethnographic engagement
- **Field interview design** — formal / informal / group / life-history
- **Documentary-style 短剧 adaptation** — convert documentary method to 短剧 runtime
- **Ethics review checklist** — informed consent, power, privacy, post-production feedback
- **Voice / POV articulation** — explicit documentary point of view

## Output Format

`documentary.json`:

```yaml
project_type: true_documentary | documentary_style_短剧 | docu_drama | ethnographic
target_runtime: <seconds>

documentary_type: poetic | expository | observational | participatory | reflexive | performative
school: flaherty | vertov | grierson | direct_cinema | cinema_verite | hybrid

subject_5c:
  consequence: 1-10
  conflict: 1-10
  character: 1-10
  context: 1-10
  change: 1-10

production_protocol:
  fieldwork_duration: <months>
  participant_observation: yes/no
  interview_types: [formal, informal, group, life_history]
  ethics_checklist_completed: yes/no

voice_and_pov:
  explicit_position: <one-sentence position statement>
  narrative_voice: <first/third person, narrator type>

short_drama_adaptation:
  applies: yes/no
  documentary_aesthetics: [verite_camera, real_locations, natural_light, ...]
  runtime_compression_strategy: <how to fit documentary style into 60-180s>
```

## Key Parameters

### LLM Generation
- **model**: `<llm_primary>` (high-quality chat model with ≥ 8K context)
- **temperature**: 0.5-0.7 (between analytical and creative)
- **max_tokens**: 4096 (full documentary plan)
- **top_p**: 0.9

### Fieldwork scale
- **True documentary**: 1-12 months
- **Ethnographic film**: 6-24 months minimum
- **Documentary-style 短剧**: 1-7 days (compressed)

## Workflow

### Standard documentary_maker workflow

1. **Knowledge Retrieval** — query the 6 retrieval topics above
2. **Subject evaluation** — 5C scoring
3. **Type selection** — choose 1 of 6 documentary types
4. **School selection** — Flaherty / Vertov / Grierson / Direct-Vérité
5. **Ethics protocol** — informed consent + privacy + power review
6. **Field plan** — duration, interview design, equipment
7. **Voice articulation** — explicit POV
8. **Distribution planning** — festival / streaming / educational

### For documentary-style 短剧
1. Standard workflow steps 1-3
2. Identify which documentary aesthetics to borrow (vérité camera, natural light, real locations, etc.)
3. Compress to 短剧 runtime
4. Maintain ethics (use real people? actors? hybrid?)

## Integration with Other Experts

- **`screenplay`**: Documentary still benefits from narrative arc ( Snyder 15-beat applies )
- **`cinematographer`**: Vérité = handheld, available light, observation
- **`editor`**: Documentary cutting = thematic-driven, not action-driven
- **`production`**: Documentary budget often 1/10 of fiction
- **`compliance_marketing`**: Real people = real consent forms, real privacy risk
- **`theory_critic`**: Documentary theory (Vertov, Flaherty ethics, observational tradition)

## Sources & Attribution

Documentary methodology primarily from:
- 王竞《纪录片创作六讲》(Project 049) — 6-lecture structure
- 《民族志纪录片创作》(Project 068) — ethnographic methods

Both books are in `_shared/project-corpus/`. Fair Use paraphrasing per project corpus LICENSE.

## Cross-References

- [`../screenplay/SKILL.md`](../screenplay/SKILL.md) — Documentary narrative
- [`../cinematographer/SKILL.md`](../cinematographer/SKILL.md) — Vérité camera
- [`../editor/SKILL.md`](../editor/SKILL.md) — Documentary cutting
- [`../production/SKILL.md`](../production/SKILL.md) — Documentary budget
- [`../compliance_marketing/SKILL.md`](../compliance_marketing/SKILL.md) — Real-person consent
- [`../theory_critic/SKILL.md`](../theory_critic/SKILL.md) — Documentary theory
- [`../_shared/project-corpus/editing-sound-post.md`](../_shared/project-corpus/editing-sound-post.md) §Part 5
- [`../_shared/glossary.md`](../_shared/glossary.md)
