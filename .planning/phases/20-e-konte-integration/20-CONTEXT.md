# Phase 20: E-Konte Integration - Context

**Gathered:** 2026-06-18
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous / full-automation mode)

<domain>
## Phase Boundary

把日本动画工业 E-Konte(絵コンテ)分镜格式作为**中间格式选项**挂载到 `cinematographer` 的 `composition_lock` 子任务下,并让 `visual_executor` 显式消费 E-Konte 5 标注层。E-Konte 与现有西方 Mascelli 8-level + 180°/30° 轴线规则**互补不替代** —— 东方分镜语法 vs 西方轴线传统。

**关键边界:**
- 不重构 cinematographer 的 Mascelli / Arijon / 180°/30° 现有路径(E-Konte 只作为新增中间格式选项)
- 不创建新 expert_id(不复活已 deprecated 的 `storyboard_designer`)
- 不修改 cinematographer / visual_executor 的 frontmatter(name / expert_id / related_skills 全部不变 — FOUND-08)
- E-Konte 今敏级 hyper-detailed storyboard **不在 scope**(本 phase 只覆盖普通 E-Konte 5 层标注格式);今敏案例仅作为参考引述
- 仅修改 `skills/movie-experts/` 下的 markdown

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

Full automation mode —— 所有实现细节由 Claude 基于 ROADMAP success criteria + v3.0 milestone 关闭后的 conventions 自行决定:

1. **e-konte-format.md 长度** — 目标 250-400 行(对齐 cinematographer 现有 refs 如 shot-grammar.md / axis-rules.md 的密度),不少于 200 行。
2. **E-Konte 5 标注层** —— 严格按 success criterion 给出的 5 层:
   - **Layer 1 场景布局(Stage Layout)** — 场所 / 道具 / 角色位置
   - **Layer 2 镜头角度与运动(Camera Angle & Movement)** — 景别 / 角度 / 推拉摇移
   - **Layer 3 角色位置表情动作(Character Pose/Expression/Action)** — 体态 / 表情 / 关键动作
   - **Layer 4 对白音效(Dialogue & SFX)** — 台词 / BGM 起止 / 音效提示
   - **Layer 5 时间帧数(Duration & Frame Count)** — 秒数 / 帧数 / cut transition 类型
3. **与西方传统的对比表** —— 必须包含一张 "E-Konte vs Western storyboard" 对照表,显式说明:
   - E-Konte 5 层 vs Mascelli 8-level shot scale(映射 + 不映射部分)
   - E-Konte Layer 2 镜头运动 vs cinematographer 现有 12 camera moves
   - E-Konte Layer 5 时间帧数 vs Western "每页 ≈ 1 分钟"启发式
4. **今敏 / 宫崎骏案例** —— 仅作为参考文献引述(各 1-2 段),不展开 imitate 级别细节。今敏《红辣椒》一年半分镜案例用于说明"E-Konte 可达到的精度上限",但本 ref **不要求** AI 输出达到今敏级精度。
5. **composition_lock 集成** —— cinematographer SKILL.md 的 `composition_lock` 子任务下新增 "E-Konte as intermediate format" 步骤,显式声明:
   - 输入:scene JSON(screenplay 输出)+ 现有 axis-rules 校验
   - 处理:5 层标注(可选,触发条件:scene.visual_density ≥ threshold 或导演风格 = 东方)
   - 输出:E-Konte JSON + 与西方 storyboard 的双输出选项
6. **visual_executor 消费协议** —— visual_executor SKILL.md 在消费 cinematographer 输出时,新增 E-Konte 字段抽取说明:
   - Layer 2 → drawer/animator sub_steps 的 camera params
   - Layer 3 → drawer 的 character pose reference
   - Layer 5 → animator 的 duration / keyframe timing
7. **glossary 4 词条** —— E-Konte / 絵コンテ / Layout / ト書き(stage direction)/ 絵切り(cut transition),中英对照 + 日本动画工业体系出处。
8. **License 状态** —— e-konte-format.md 含 Fair Use paraphrase + 出处标注(日本动画工业通用知识 + 今敏/宫崎骏公开访谈纪录片);不复制具体分镜页或受版权保护的 cut.

### 自动接受的所有 grey area 默认值

- 文档语言:中文为主 + 日文术语保留(絵コンテ / ト書き / 絵切り)+ 英文对照
- 不引入新 eval 维度
- 不修改 _eval/baseline/(E-Konte 是 cinematographer 内部 ref,不触发 benchmark 更新)

</decisions>

<code_context>
## Existing Code Insights

**cinematographer 当前结构:**
- `SKILL.md` frontmatter: `name: cinematographer`, `expert_id: cinematographer`, `related_skills: [screenplay, scene_builder(deprecated), visual_executor, editor, continuity_auditor, prompt_injector, colorist]`
- `references/` 现有 5 个 ref:`axis-rules.md`(180°/30° 轴线)+ `camera-motion-catalog.md`(12 camera moves)+ `shot-grammar.md`(Mascelli 8-level + Arijon)+ `vertical-screen-framing.md`(竖屏特有构图)+ `LICENSE.md`
- 现有 `composition_lock` 子任务负责"scene → shot 分解 + 轴线审计"
- E-Konte 是东方传统,完全缺失

**visual_executor 当前结构:**
- v3.0 milestone 中由 drawer + animator 合并而来,`sub_steps: [drawer, animator]`
- 消费 cinematographer 的 shot 分解 + camera params
- E-Konte 5 层应作为可选输入格式被显式声明消费

**storyboard_designer(deprecated)状态:**
- v3.0 Phase 17 已 deprecate,`inheritance_targets: [cinematographer]`
- 本 phase **不复活** storyboard_designer,E-Konte 折叠进 cinematographer.composition_lock
- `deprecated_reason` 已经说明"分镜设计职能已折叠至 cinematographer 的 composition_lock 子任务",本 phase 是对该承诺的兑现

**_shared/glossary.md:** Phase 19 已加 4 个 Snowflake 词条,本 phase 再加 4 个 E-Konte 词条(累计 8 个 v4.0 新词条)。

</code_context>

<specifics>
## Specific Ideas

**Source artifact 引用:** `.planning/research/methodology-gap-analysis-2026-06-17.md` §5.2 给出 E-Konte 接入点:
> "`storyboard_designer` deprecated 后留下的真空,东方分镜传统完全缺席。接入难度 MEDIUM。"

**报告 §4.1 给出 E-Konte 详细描述** —— planner / executor 应在 e-konte-format.md 中按 5 层 + 今敏/宫崎骏案例组织内容。

**关键风险(STATE.md 已记录):** E-Konte 今敏级 vs 普通 scope confusion(MEDIUM/HIGH)。本 phase 锚定普通 E-Konte format(5 层标注),今敏级 hyper-detailed storyboard 不在 scope。

</specifics>

<canonical_refs>
## Canonical References

- `.planning/research/methodology-gap-analysis-2026-06-17.md`(§5.2 + §4.1 + §7.2 阶段 4)
- `.planning/quick/260617-wgz-write-gap-analysis-doc-comparing-creativ/source-research-report.md`(§4.1 E-Konte 详细描述)
- `skills/movie-experts/cinematographer/references/shot-grammar.md`(Mascelli 8-level + Arijon,对照目标)
- `skills/movie-experts/cinematographer/references/axis-rules.md`(180°/30° 轴线,E-Konte Layer 2 与之互补)
- `skills/movie-experts/cinematographer/references/camera-motion-catalog.md`(12 camera moves,E-Konte Layer 2 映射目标)
- `skills/movie-experts/storyboard_designer/SKILL.md`(deprecated 状态参考,但不复活)
- `skills/movie-experts/visual_executor/SKILL.md`(消费 E-Konte 字段的下游 expert)

</canonical_refs>
