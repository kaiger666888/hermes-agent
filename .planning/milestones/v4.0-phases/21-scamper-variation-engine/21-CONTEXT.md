# Phase 21: SCAMPER Variation Engine + DOC Close-out - Context

**Gathered:** 2026-06-18
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous / full-automation mode)

<domain>
## Phase Boundary

把 Bob Eberle SCAMPER 7 动词变体引擎挂载到 `style_genome.style_blend` 子任务上(叠加,不替代),让 `hook_retention` 消费 SCAMPER × 5 爆款公式交叉表得到 35 个 hook 变体种子。**Phase 21 也是 v4.0 milestone 的 close-out phase** —— 把 Phase 19/20/21 三个新 ref 同步到 README.md corpus tree + skills-mapping.yaml sign-off,完成 v4.0 documentation 收口。

**关键边界:**
- SCAMPER 叠加在 style_blend 之上,**不替代** auteur-theory / genre-dna / style_blend 现有逻辑
- 不创建新 expert_id,不修改 style_genome / hook_retention 的 frontmatter
- DOC-01 + DOC-02 是 cross-cutting(覆盖 Phase 19+20+21 三个新 ref),所以放在 Phase 21 做 close-out
- 不引入新 eval 维度,_eval/baseline/ 不更新

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

Full automation mode —— 所有实现细节由 Claude 基于 ROADMAP success criteria + v3.0 milestone 关闭后的 conventions 自行决定:

1. **scamper-variations.md 长度** — 目标 300-450 行(SCAMPER 7 动词 × 5 基因组合 = 35 个变体配方,每个配方至少 8-12 行展开,加上 LLM prompt 模板 + output schema),不少于 200 行。
2. **SCAMPER 7 动词定义** —— 严格按 Bob Eberle 1971(基于 Osborn 创意清单)原文:
   - **S - Substitute** 替代
   - **C - Combine** 组合
   - **A - Adapt** 适配
   - **M - Modify/Magnify/Minify** 修改/放大/缩小
   - **P - Put to other use** 另作他用
   - **E - Eliminate** 消除
   - **R - Reverse/Rearrange** 反转/重排
3. **35 变体配方组织** —— 7 动词 × 5 基因组合(genre × mood × pacing × cast × runtime),每个配方至少给出:
   - 输入 style genome(参考 style_genome 现有 schema)
   - 变体动作(动词 × 操作目标)
   - 输出 style_blend 候选(JSON schema)
   - 适用场景(短剧 60s/90s/180s × 男频/女频 × 平台)
4. **LLM prompt 模板** —— 提供 1 个通用 SCAMPER 变体生成 prompt 模板 + 7 个动词专用 prompt(每个动词一个),所有模板可被 style_genome SKILL.md 直接引用。
5. **style_genome SKILL.md 集成** —— `style_blend` 子任务下新增 "SCAMPER Variation Layer":
   - 输入:style_genome JSON(用户或上游提供)
   - 处理:7 动词展开 → 7 个候选 style_blend
   - 输出:候选数组 + 推荐分数(LLM-judged novelty × feasibility × alignment)
   - 显式声明 SCAMPER 与 auteur-theory / genre-dna 的关系(SCAMPER 是变体引擎,不是分类系统)
6. **hook_retention SKILL.md 集成** —— 新增 "SCAMPER × 5 爆款公式" 交叉表:
   - 行:7 SCAMPER 动词
   - 列:5 短剧爆款公式(参考 hook_retention 现有 5 平台公式:抖音 / 快手 / 小程序剧 / B站 / YouTube Shorts)
   - 单元格:1-2 个 hook 变体种子(总共 35+ 个)
7. **glossary 8 词条** — SCAMPER + 7 动词(Substitute / Combine / Adapt / Modify / Put-to-other-use / Eliminate / Reverse),中英对照 + Eberle 1971 出处 + Osborn 创意清单溯源。
8. **DOC-01 README corpus tree** —— 在 `skills/movie-experts/README.md` 的 corpus tree / inventory 表中列出 3 个新 refs:
   - `creative_source/references/snowflake-method.md` (Phase 19)
   - `cinematographer/references/e-konte-format.md` (Phase 20)
   - `style_genome/references/scamper-variations.md` (Phase 21)
   - Mermaid DAG 不变(3 个 ref 都是已有 expert 的内部 ref,不新增 DAG 节点)
9. **DOC-02 skills-mapping.yaml sign-off** —— 在 `.planning/research/v2-pipeline-design/skills-mapping.yaml` 为 3 个新 ref 增加 sign-off 条目,每个条目含:
   - `verified_date: 2026-06-18`
   - `source: [出处]`
   - `license_status: fair_use_paraphrase`
   - `phase_added: v4.0-phase-{19|20|21}`
10. **License 状态** —— scamper-variations.md 含 Fair Use paraphrase + Eberle 1971 + Osborn 出处标注,沿用现有 refs 模式。

### 自动接受的所有 grey area 默认值

- 文档语言:中文为主 + 方法论术语保留英文(SCAMPER / Substitute / 等)
- 不引入新 eval 维度
- 不修改 _eval/baseline/

</decisions>

<code_context>
## Existing Code Insights

**style_genome 当前结构:**
- `SKILL.md` frontmatter: `name: style_genome`, `expert_id: style_genome`, `related_skills: [screenplay, drawer(deprecated→visual_executor), colorist, editor, composer(deprecated→audio_pipeline), scene_builder(deprecated), performer(deprecated), continuity(deprecated→continuity_auditor)]`
- `references/` 现有 6 个 ref:`art-direction-methodology.md` + `auteur-theory.md`(Sarris-Truffaut-Bordwell)+ `cn-director-analysis.md` + `cross-cultural-style.md` + `director-dna-archive.md` + `genre-dna-taxonomy.md` + `LICENSE.md`
- `style_blend` 是现有子任务(混合多个 style 基因);SCAMPER 叠加在 style_blend 之上作为变体引擎

**hook_retention 当前结构:**
- `references/` 现有 4 个 ref:`conflict-escalation.md` + `paywall-design.md` + `three-second-hooks.md` + `vertical-pacing.md`
- 现有"短剧爆款公式 5-branch"已存在(5 平台公式),SCAMPER × 5 公式 = 35 变体种子是新交叉表

**README.md corpus tree 现状:** v3.0 milestone 关闭时已含 31 个 SKILL.md 文件 inventory,本 phase 在 corpus tree 子节(各 expert 的 references/ 列表)中增加 3 行。

**skills-mapping.yaml 现状:** v3.0 milestone 关闭时 19 entries signed_off,本 phase 增加 3 个 ref-level sign-off 条目(注意:不是 expert-level,是 ref-level —— 用单独的 section 或 sub-table 区分)。

**_shared/glossary.md:** Phase 19+20 已加 8 个词条(Snowflake 4 + E-Konte 4),本 phase 再加 8 个 SCAMPER 词条(累计 16 个 v4.0 新词条)。

</code_context>

<specifics>
## Specific Ideas

**Source artifact 引用:** `.planning/research/methodology-gap-analysis-2026-06-17.md` §5.3 给出 SCAMPER 接入点:
> "`style_genome.style_blend` 当前是手动协议;SCAMPER 能系统化生成 7 种故事变体,直接增强 hook_retention 的爆款公式扩展能力。接入难度 LOW-MEDIUM。"

**报告 §6.1 给出 SCAMPER 详细描述** —— planner / executor 应在 scamper-variations.md 中按 7 动词 + 35 配方组织内容。

**关键风险(STATE.md 已记录):** SCAMPER vs style_blend boundary confusion(MEDIUM)。本 phase 锚定 SCAMPER 是**叠加层**(stacked on top of style_blend),不是 replacement。

</specifics>

<canonical_refs>
## Canonical References

- `.planning/research/methodology-gap-analysis-2026-06-17.md`(§5.3 + §6.1 + §7.2 阶段 5)
- `.planning/quick/260617-wgz-write-gap-analysis-doc-comparing-creativ/source-research-report.md`(§6.1 SCAMPER 详细描述)
- `skills/movie-experts/style_genome/references/auteur-theory.md`(现有方法论,SCAMPER 不替代)
- `skills/movie-experts/style_genome/references/genre-dna-taxonomy.md`(genre DNA,SCAMPER 变体目标)
- `skills/movie-experts/style_genome/SKILL.md`(style_blend 子任务,SCAMPER 叠加点)
- `skills/movie-experts/hook_retention/SKILL.md`(5 爆款公式,SCAMPER × 公式 交叉表目标)
- `skills/movie-experts/hook_retention/references/three-second-hooks.md`(hook 变体种子消费点)
- `skills/movie-experts/README.md`(corpus tree,DOC-01 目标)
- `.planning/research/v2-pipeline-design/skills-mapping.yaml`(sign-off 文件,DOC-02 目标)

</canonical_refs>
