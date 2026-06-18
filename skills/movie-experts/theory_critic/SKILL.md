---
name: theory_critic
description: "Theory & Criticism Expert: film theory frameworks (formalism/realism/psychoanalytic), auteur analysis, film history methods, and rigorous film criticism methodology."
version: 1.0.0
author: Hermes Agent (integrated from 100+本影视剪辑书 project)
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, theory, criticism, auteur, history, philosophy, formalism, realism, psychoanalysis, bazin, tarkovsky, zizek, mulvey, metz, dai-hua]
    related_skills:
      - style_genome        # Theory informs style encoding
      - screenplay          # Theory informs narrative choices
      - cinematographer     # Theory informs shot decisions
      - editor              # Theory informs cut decisions
      - colorist            # Theory informs color narrative
      - compliance_gate  # Theory informs cultural critique
    expert_id: theory_critic
    metrics: [theoretical_rigor, citation_accuracy, critical_depth, framework_fit]
---

# Theory & Criticism Expert (理论批评专家)

The only Movie-Experts Suite specialist for rigorous film theory, auteur analysis, film historiography, and academic-grade film criticism. Wraps the project corpus's 25+ theory / criticism books (Bazin, Tarkovsky, Andrew, Agel, Balázs, Mulvey, Žižek, Dai Hua, etc.) into a unified retrieval layer for higher-order analysis tasks.

## When to use this skill

Invoke this expert when the user needs:

- **Academic film analysis** — close reading, theoretical framework application
- **Auteur comparison** — "how does this 短剧 IP's virtual auteur compare to Bergman / Ozu / Tarkovsky?"
- **Genre / movement genealogy** — tracing visual / narrative lineage
- **Criticism writing** — structured review beyond impressionistic response
- **Theoretical diagnosis** — "is this 短剧 realist or formalist? Mulvey-test pass?"
- **Film history research** — 4-path historiography (aesthetic / economic / technological / social)
- **Cross-cultural adaptation** — Hollywood ↔ Chinese cinema theoretical translation
- **Style genome grounding** — when `style_genome`'s 5D encoding needs theoretical justification

## References

本专家所有理论框架由下列 8 个 refs 独占定义,SKILL.md body 仅作摘要 + 跨链。Project-corpus refs 来自 `/home/kai/Downloads/100+本影视剪辑书/` 项目(102 本 MinerU 转换的中文电影书)。

| Ref | When to Read | Contents |
|-----|--------------|----------|
| [`_shared/project-corpus/theory-formalism-vs-realism.md`](../_shared/project-corpus/theory-formalism-vs-realism.md) | 任何理论框架选择前 | Andrew《经典电影理论导论》形式主义 vs 写实主义两大流派 + 5 步流派判定 + 法国先锋派(上镜头性/完整电影) |
| [`_shared/project-corpus/film-philosophy-bazin-tarkovsky.md`](../_shared/project-corpus/film-philosophy-bazin-tarkovsky.md) | 涉及本体论/长镜头/雕刻时光时 | Bazin(影像本体论/完整电影/木乃伊情意综) + Tarkovsky(七部半/雕刻时光/电影影像) + 短剧应用 |
| [`_shared/project-corpus/psychoanalytic-film-theory.md`](../_shared/project-corpus/psychoanalytic-film-theory.md) | 涉及凝视/缝合/无意识时 | Mulvey(男性凝视)+ Baudry(镜像+双重认同)+ 麦茨(想象能指)+ Žižek(圣状/三界)+ 短剧 Mulvey-test |
| [`_shared/project-corpus/auteur-director-biographies.md`](../_shared/project-corpus/auteur-director-biographies.md) | 任何 auteur 分析 | 7 位大师独立方法论:Bergman/Kieślowski/Tarkovsky/Ozu/Fassbinder/Buñuel/Altman + 风格指纹 |
| [`_shared/project-corpus/film-criticism-methodology.md`](../_shared/project-corpus/film-criticism-methodology.md) | 写严肃影评 / 学术批评时 | 戴锦华《电影批评》视听+叙事+作者+文化 4 维度 + 《如何写影评》自问十题 + 5 层级批评 |
| [`_shared/project-corpus/film-history-methods.md`](../_shared/project-corpus/film-history-methods.md) | 做电影史研究 / 跨时代对比时 | Allen《电影史理论与实践》4 大史学路径(美学/经济/技术/社会) + 实在论方法论 + 短剧史研究 |
| [`_shared/project-corpus/narrative-revolution-and-modernism.md`](../_shared/project-corpus/narrative-revolution-and-modernism.md) | 研究反传统叙事 / 现代主义时 | 郭小橹《电影理论笔记》叙事革命词汇表 + 本雅明(机械复制/灵光)+ 阿多诺(文化工业) |
| [`_shared/project-corpus/README.md`](../_shared/project-corpus/README.md) | 查找具体原书时 | 102 本书索引,按 7 大类(剧本/分镜/拍摄/后期/制片/理论/史类)分类 |

## Role & Philosophy

- **理论不是装饰,是诊断工具。** 任何视觉/叙事选择都能追溯到某个理论谱系——本专家的工作是显化这个谱系。
- **跨文化翻译是核心价值。** 巴赞 / Mulvey / Žižek 诞生于欧美语境,但他们的概念能精确诊断中国 短剧 的美学问题(例如男频 短剧 = 显性 Mulvey-style 凝视结构)。
- **作者研究 ≠ 风格复制。** 研究 Bergman / Ozu / Tarkovsky 不是为了"像他们",而是为了"知道为什么不像他们也能成好作品"。
- **批评的5层级递进。** 从印象式 → 描述式 → 分析式 → 作者式 → 理论式,本专家默认输出层级 4-5。
- **历史是当下的镜子。** 电影史的 4 路径(美学/经济/技术/社会)同样适用于研究 短剧 平台时代。

## Knowledge Retrieval

在生成任何理论 / 批评输出前,按以下顺序检索上下文(8 个检索主题):

- **形式主义 vs 写实主义**(Andrew 经典两分 + 5 步流派判定 + 法国先锋派)—— 详见 [`_shared/project-corpus/theory-formalism-vs-realism.md`](../_shared/project-corpus/theory-formalism-vs-realism.md)
- **巴赞与塔可夫斯基**(影像本体论 + 完整电影 + 雕刻时光 + 七部半)—— 详见 [`_shared/project-corpus/film-philosophy-bazin-tarkovsky.md`](../_shared/project-corpus/film-philosophy-bazin-tarkovsky.md)
- **精神分析电影理论**(Mulvey 凝视 + Baudry 镜像 + 麦茨想象能指 + Žižek 圣状)—— 详见 [`_shared/project-corpus/psychoanalytic-film-theory.md`](../_shared/project-corpus/psychoanalytic-film-theory.md)
- **7 位导演传记研究法**(Bergman/Kieślowski/Tarkovsky/Ozu/Fassbinder/Buñuel/Altman 独立方法论)—— 详见 [`_shared/project-corpus/auteur-director-biographies.md`](../_shared/project-corpus/auteur-director-biographies.md)
- **戴锦华 4 维度批评**(视听 + 叙事 + 作者 + 文化)—— 详见 [`_shared/project-corpus/film-criticism-methodology.md`](../_shared/project-corpus/film-criticism-methodology.md)
- **电影史 4 大路径**(美学 / 经济 / 技术 / 社会)—— 详见 [`_shared/project-corpus/film-history-methods.md`](../_shared/project-corpus/film-history-methods.md)
- **叙事革命词汇表**(郭小橹) + **现代性美学**(本雅明 / 阿多诺)—— 详见 [`_shared/project-corpus/narrative-revolution-and-modernism.md`](../_shared/project-corpus/narrative-revolution-and-modernism.md)
- **102 本书索引**(按类目定位原书)—— 详见 [`_shared/project-corpus/README.md`](../_shared/project-corpus/README.md)

**若当前 runtime 中有 memory / RAG 工具**(例如 `<memory_plugin>` / `<rag_search>`),使用以下查询范围:

```
tags="expert:theory_critic,domain:formalism-vs-realism"
tags="expert:theory_critic,domain:bazin-tarkovsky"
tags="expert:theory_critic,domain:psychoanalytic-theory"
tags="expert:theory_critic,domain:auteur-research"
tags="expert:theory_critic,domain:criticism-methodology"
tags="expert:theory_critic,domain:film-history-methods"
tags="expert:theory_critic,domain:modernism-benjamin-adorno"
tags="domain:project-corpus,category:理论批评"
```

**若无此类工具**,回退到本目录 `_shared/project-corpus/*.md` 静态文件。

## Core Capabilities

- **5-step school determination** — for any film / 短剧, determine formalist vs realist + identify boundary cases
- **Auteur comparison matrix** — compare target work's virtual auteur to canonical directors (7 master library)
- **Mulvey gaze test** — diagnose male-gaze / female-gaze structure in 短剧 scenes
- **Žižek sinthome identification** — find the symptomatic core element recurring across episodes
- **Dai Hua 4-dimension close reading** — audiovisual + narrative + auteur + cultural
- **Self-Ask 10 protocol** — structured pre-critical questioning
- **5-level critical writing** — output at level 4-5 (auteurist / theoretical)
- **4-path historiographical research** — design research questions + select evidence per path
- **Cross-cultural theoretical translation** — adapt Western theory to Chinese 短剧 context

## Output Format

`critique.json` with optional sub-artifacts:

```yaml
analysis_type: close_reading | auteur_comparison | gaze_diagnosis | historical_research | theoretical_diagnosis
target: <film or 短剧 IP name>

theoretical_framework:
  primary_school: formalism | realism | psychoanalytic | cultural_studies
  secondary_schools: [...]
  cited_theorists: [Bazin, Mulvey, ...]

dimensions:
  audiovisual_analysis: <Dai Ch.1 style>
  narrative_analysis: <Metz syntagms>
  auteur_analysis: <cf. canonical director>
  cultural_context: <platform / era / demographics>

critical_level: 1-5
key_insights: [...]
actionable_recommendations: [...]

cross_references:
  related_experts: [style_genome, cinematographer, ...]
  source_books: [Project IDs]
```

## Key Parameters

### LLM Generation
- **model**: `<llm_primary>` (any high-quality chat model with ≥ 32K context for theory-heavy work; if `<llm_primary>` available, use it; otherwise `<llm_fallback>`)
- **temperature**: 0.4-0.6 (analytical writing — lower than creative)
- **max_tokens**: 8192 (full analysis), 2048 (single dimension)
- **top_p**: 0.85

### Critical Depth
- **level 1-2 (impressionistic/descriptive)**: NOT this expert's output
- **level 3 (analytical)**: minimum acceptable
- **level 4 (auteurist)**: default
- **level 5 (theoretical)**: when explicitly requested

## Workflow

### Standard theory_critic workflow

1. **Knowledge Retrieval** — query the 8 retrieval topics above (RAG or static refs)
2. **Framework selection** — choose primary school based on user task:
   - Visual style analysis → formalism/realism
   - Gender / power analysis → psychoanalytic
   - Director DNA → auteur theory
   - Era / platform analysis → film history
3. **Diagnostic application** — apply framework to target work
4. **Cross-validation** — sanity-check with second framework (avoid monocausal)
5. **Critical writing** — output at level 4-5 with explicit citations

### When paired with other experts
- **After `style_genome`**: validate 5D encoding against theoretical framework
- **Before `screenplay`**: provide theoretical anchor for IP's "virtual auteur"
- **During `compliance_gate`**: explain why a 爆款 element works theoretically (or fails)

## Integration with Project Corpus

This expert is the **primary consumer** of `_shared/project-corpus/*.md`. All theory / criticism / history tasks route through here, then dispatch to specific corpus refs.

The project corpus contains:
- 25 theory / criticism books (Bazin / Tarkovsky / Andrew / Agel / Mulvey / Žižek / Dai Hua)
- 7 director biographies (Bergman / Kieślowski / Tarkovsky / Ozu / Fassbinder / Buñuel / Altman)
- 5 history books (Sadoul / Oxford / Allen / 山田洋次 / 日本巨匠)
- 102 books total available as RAG corpus

## Sources & Attribution

All theoretical frameworks in this expert are attributed to their original theorists via `_shared/project-corpus/*.md` refs. Per-ref Fair Use policy: paraphrased concepts + page-references; no verbatim quotes > 200 chars.

## Cross-References

- [`../style_genome/SKILL.md`](../style_genome/SKILL.md) — Style encoding expert
- [`../screenplay/SKILL.md`](../screenplay/SKILL.md) — Screenplay expert
- [`../cinematographer/SKILL.md`](../cinematographer/SKILL.md) — Cinematography expert
- [`../editor/SKILL.md`](../editor/SKILL.md) — Editing expert
- [`../colorist/SKILL.md`](../colorist/SKILL.md) — Color expert
- [`../compliance_gate/SKILL.md`](../compliance_gate/SKILL.md) — Compliance expert
- [`../_shared/glossary.md`](../_shared/glossary.md) — Glossary
- [`../_shared/RAG-INVOCATION-PATTERN.md`](../_shared/RAG-INVOCATION-PATTERN.md) — RAG pattern

## V8.6 Pipeline Sync (Phase 26 v5.0)

> 来源:kais-movie-agent V8.6 SKILL.md §"hermes-agent 专家 → 管线 Step 速查" §"其他可用专家"(按需补充调用)。dreamina CLI 适配基线见 [`_shared/dreamina-cli-baseline.md`](../_shared/dreamina-cli-baseline.md)。

### V8.6 Step Position

theory_critic 在 V8.6 管线中是 **"按需补充调用" consultative role**(非主线 Step):

| V8.6 调用模式 | 触发条件 | 共同调用专家 |
|--------------|---------|------------|
| **按需补充**(非每项目都调用) | (1) 用户要求高水准批评分析 (2) 项目定位"艺术向"/获奖向 (3) style_genome 触发 auteur theory 需深化 | (任意 Step 都可调用,典型在 Step 2/6/9 后) |

**theory_critic 不是 V8.6 13 步主线的必需节点** —— 它属于 kais-movie-agent V8.6 SKILL.md §"其他可用专家"列表(per mapping table:`editor`, `production`, `compliance_marketing`, `compliance_gate`, `creative_source`, `theory_critic`, `documentary_maker`, `animation_studio`)。

### Consultative Role 触发场景

theory_critic 的 consultative 调用典型场景:

| 场景 | 何时调用 | 输出 |
|------|---------|------|
| **Auteur 选择深化** | Step 2.5 style_genome 确立 auteur 后 | auteur_analysis.md(导演 DNA 深度解读 + 风格一致性建议) |
| **Genre 选择验证** | Step 2.5 style_genome 确立 genre 后 | genre_critique.md(genre 经典范式对照 + 创新空间建议) |
| **剧本理论审计** | Step 3 后(可选) | theory_audit.md(formalism / realism / psychoanalytic 视角批评) |
| **成片艺术评价** | Step 11 后(可选) | artistic_assessment.md(成片艺术质量评价 + 改进建议) |

### V8.6 审核门关系

theory_critic **不绑定审核门** —— 它的输出作为 advisory(咨询性)材料供用户决策,不是 pass/fail 硬门。即使 theory_critic 给出"艺术性不足"评价,管线仍可推进(用户决定是否采纳)。

这区别于:
- compliance_gate(硬门,fail 阻止推进)
- script_auditor(硬门,predicted completion < 65% 阻止推进)
- continuity_auditor(硬门,4 维 fail 触发重生)

theory_critic 是**软咨询**,而非**硬审计**。

### V8.4 历史背景

theory_critic 在 V8.4 §1 "专家映射全面更新" 中**保持 1:1 映射**(无 merge / 无 rename / 无 deprecate)。它的 consultative 角色从 v1(Phase 3 v1.0)就确立 —— V8.4/V8.5/V8.6 都没有改变其 advisory 性质。

### dreamina CLI 关系

theory_critic **完全不涉及** dreamina CLI —— 它在内容生成后做理论批评,既不输入到 dreamina CLI,也不消费 dreamina CLI 输出。

但 theory_critic 应基于**实际生成内容**做批评(而非抽象理论),所以会消费 visual_executor + audio_pipeline 的成片产物作为批评素材。

### Cross-References

- [`_shared/dreamina-cli-baseline.md`](../_shared/dreamina-cli-baseline.md) — V8.6 工具链参考(本专家不直接使用,仅供批评素材溯源)(Phase 22 v5.0)
- [`style_genome/SKILL.md §V8.6 Pipeline Sync`](../style_genome/SKILL.md) — Step 2.5 auteur / genre 选择协同
- [`screenplay/SKILL.md §V8.6 Pipeline Sync`](../screenplay/SKILL.md) — Step 3 剧本理论审计
- [`editor/SKILL.md §V8.6 Pipeline Sync`](../editor/SKILL.md) — Step 8 剪辑理论批评
- [`compliance_gate/SKILL.md §V8.6 Pipeline Sync`](../compliance_gate/SKILL.md) — 区分:本专家是 soft advisory,compliance_gate 是 hard gate
