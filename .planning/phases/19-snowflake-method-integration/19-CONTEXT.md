# Phase 19: Snowflake Method Integration - Context

**Gathered:** 2026-06-18
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous / full-automation mode)

<domain>
## Phase Boundary

把 Ingermanson 雪花法 10 步递进管线挂载到 `creative_source` + `screenplay` 两个已有 active expert,填补 StoryKernel → beat sheet 之间的"展开塌陷"。本 phase 不引入新 expert_id,只在 `creative_source/references/` 新增 1 个 ref + 增量更新 2 个 SKILL.md(creative_source + screenplay)+ 在 `_shared/glossary.md` 加 4 个词条。

**关键边界:**
- 不重构 creative_source 的 Bourdieu 路径(snowflake 只作为补充展开管线,不替代 StoryKernel)
- 不重构 screenplay 的 McKee+Snyder+Tan+McMahon 联用结构(snowflake-4 一页大纲作为输入 scaffold,不替换 Snyder beat sheet)
- 不创建新 expert_id,不触发 FOUND-08 alias 流程
- 仅修改 `skills/movie-experts/` 下的 markdown;不动 Hermes 核心 Python/JS 代码

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

Full automation mode — autonomous workflow with `skip_discuss`. 所有实现细节由 Claude 基于 ROADMAP success criteria + 项目 conventions 自行决定:

1. **snowflake-method.md 长度** — 目标 250-400 行(对齐 screenplay 现有 refs 如 mckee-scene-design.md / save-the-cat-beat-sheet.md 的密度),不少于 success criterion 要求的 200 行。
2. **Snowflake 10 步缩放规则** — 短剧 60-180s 单集形态映射:Step 1-2 (premise+paragraph) 必做;Step 3-4 (角色概要+一页大纲) 强制作为 screenplay 消费的最小输出;Step 5-6 可选;Step 7-10 移至 screenplay 内部 Beat Planning 之后做(避免与 Snyder beat sheet 重复)。
3. **StoryKernel → Snowflake 衔接协议** — Bourdieu 6 层 StoryKernel 提取 1-2 个最强冲突作为 Snowflake-1 (premise sentence) 的输入;`unspeakability_protocol` 阈值 ≥ 7 的 kernel 才走 Snowflake 展开路径(避免对低质量 kernel 做无意义展开)。
4. **Snowflake-4 字段映射到 Snyder 15-beat** — 显式给出表格:
   - Snowflake 段落第 1 段(开头) ↔ Snyder Set-Up + Catalyst
   - Snowflake 段落第 2-3 段(三幕灾难) ↔ Snyder Midpoint + All Is Lost
   - Snowflake 段落第 4 段(结尾) ↔ Snyder Finale + Final Image
5. **glossary 4 词条** — Snowflake Method / Story Spine / Premise Sentence / Scene List,中英对照,Ingermanson 2000s 出处,符合 _shared/glossary.md 现有 H3 格式。
6. **License 状态** — snowflake-method.md 必须含 LICENSE.md 引用(Fair Use paraphrase + 出处,与 screenplay 现有 refs 同模式)。

### 自动接受的所有 grey area 默认值

- 文档语言:中文为主,方法论术语保留英文(对齐 v3.0 milestone 关闭后的所有 refs 风格)
- 验收方式:静态文件存在性 + 字数 + 关键字段包含(success criteria 已显式给出)
- 不引入新 eval 维度(本 phase 是知识层增量,不触发 _eval/ 更新)

</decisions>

<code_context>
## Existing Code Insights

**creative_source 当前结构:**
- `SKILL.md` frontmatter: `name: creative_source`, `expert_id: creative_source`, `related_skills: [style_genome, screenplay, hook_retention, compliance_gate, topic_curator, prompt_injector]`
- `references/` 现有 5 个 ref:`multi-strata-resonance.md` / `story-kernel-schema.md` / `strata-guide.md` / `unspeakability-protocol.md` / `LICENSE.md`
- StoryKernel JSON 是核心输出 schema,目前直接交付给 style_genome + screenplay(无中间展开层)

**screenplay 当前结构:**
- `SKILL.md` 调用顺序:`style_genome → screenplay`(creative_source 间接通过 style_genome 链入)
- 现有 6 个 ref:`save-the-cat-beat-sheet.md`(Snyder 15-beat)+ `mckee-scene-design.md`(McKee gap/value-shift)+ `emotion-curve-academic.md`(Tan/McMahon)+ `dialogue-craft.md` + `cn-shortdrama-structure.md` + `LICENSE.md`
- Beat Planning 子步骤是 snowflake-4 输出的天然消费点(在 Beat Planning 前新增 "Consume Snowflake-4 一页大纲" 子步骤)

**_shared/glossary.md 现状:**
- H3 词条格式:`### Snowflake Method` + 中英对照段落 + 出处链接
- v3.0 milestone 关闭时已包含 ~80 个词条,本 phase 加 4 个新的(无重复)

**LICENSE 与版权:**
- snowflake-method.md 必须含 Fair Use paraphrase + Ingermanson 出处标注,沿用现有 refs 的 LICENSE.md 引用模式

</code_context>

<specifics>
## Specific Ideas

**Source artifact 引用:** `.planning/research/methodology-gap-analysis-2026-06-17.md` §5.1 给出 Snowflake 接入点:
> "填补 `creative_source → screenplay` 之间的'展开塌陷'(一句话→段落→角色→大纲→场景列表的递进管线)。接入难度 LOW。"

**报告 §2.1 给出 10 步原文** —— planner / executor 应在 snowflake-method.md 中按原文顺序列出 10 步,然后给出短剧适配的 step selection rule(见 decisions §2)。

**与 McMahon 六情感弧线的关系** —— snowflake-4 一页大纲应隐含呼应 McMahon 6 弧线之一(rags-to-riches / tragedy / man-in-a-hole / Icarus / Cinderella / Oedipus),但本 phase 不强制耦合(emotion-curve-academic.md 已有 McMahon 6 弧线,snowflake 只需在 step 2 [paragraph expansion] 时让作者选 1 个弧线作为 paragraph polarity 的隐含模板)。

</specifics>

<canonical_refs>
## Canonical References

- `.planning/research/methodology-gap-analysis-2026-06-17.md`(本 phase 事实底座,§5.1 + §2.1 + §7.2 阶段 2)
- `.planning/quick/260617-wgz-write-gap-analysis-doc-comparing-creativ/source-research-report.md`(原始调研报告,§2.1 雪花法)
- `skills/movie-experts/screenplay/references/save-the-cat-beat-sheet.md`(Snyder beat sheet,Snowflake-4 映射目标)
- `skills/movie-experts/screenplay/references/mckee-scene-design.md`(McKee scene,value-shift rule 与 snowflake step 9-10 [场景描述] 部分对齐)
- `skills/movie-experts/creative_source/references/story-kernel-schema.md`(StoryKernel JSON schema,snowflake-1 [premise] 的输入)
- `skills/movie-experts/creative_source/references/unspeakability-protocol.md`(阈值 ≥ 7 触发条件)

</canonical_refs>
