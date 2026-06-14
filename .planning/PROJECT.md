# Movie-Experts Suite v2 — 短剧/微电影创作专家增强

## What This Is

Hermes Agent 的 `skills/movie-experts/` 专家体系的增强项目:在现有 14 个电影制作专家(编剧、绘图、动画、剪辑、调色、配乐、表演、场景、拟音、空间音频、混音、配音、连续性、风格基因组)基础上,通过 RAG 增强其行业经验,并补全 AI 短剧(短剧/竖屏短剧)与微电影创作全链路的关键缺口 —— 新增运镜指导、Hook & Retention、制作管理、合规与宣发 4 个专家。目标是让每个专家不再是「懂语法的模板」,而是「懂行业的专家」。

## Core Value

每个 movie-expert skill 都能用检索增强的方式调用行业知识库(静态 refs 为主,可选向量 RAG),让 AI 生成的短剧/微电影在专业度上接近人类创作者水平 —— 这是决定短剧生死的核心。

## Requirements

### Validated

<!-- 现有能力,来自 codebase map 反推 -->

- ✓ 14 个专家 skill 已运行(screenplay, drawer, animator, editor, colorist, composer, performer, scene_builder, foley, spatial_audio, mixer, voicer, continuity, style_genome) — existing
- ✓ 模块化 SKILL.md 发现机制(metadata.hermes schema + related_skills 协作图) — existing
- ✓ 每个专家独立的编码矩阵(5D style genome、CxSxZ color、FxRxT editing、ExBxSxP performance、7D foley) — existing
- ✓ SKILL.md 纯 markdown,无 Python 代码 — existing
- ✓ Hermes memory plugin 已部署(可选向量 RAG 复用基础) — existing

### Active

<!-- 当前 scope,均为 hypothesis 直到交付验证 -->

**A. 现有 14 个专家的深度重构 + refs**
- [ ] **AUDIT-01**: 对 14 个现有专家逐一审计,输出 GAP-REPORT.md(每个专家的知识盲点、prompt 改进点、metric 修订建议、应增 refs 主题)
- [ ] **REFACTOR-A**: 对 14 个 SKILL.md 深度重构(注入 RAG 查询指令、修订 quality thresholds、补充 metric、按需精简/扩展 prompt)
- [ ] **REFS-A**: 为 14 个专家各建 `references/` 子目录,装人工整理的 markdown 专业资料

**B. 4 个新增专家**
- [ ] **EXPERT-CINE**: Cinematographer(运镜/摄影指导)—— 镜头语言体系、景别/视角/构图、轴线规则、match cut、与 scene_builder(机位规划)和 animator(动态执行)的协作边界
- [ ] **EXPERT-HOOK**: Hook & Retention(钩子与留存)—— 短剧特有:3 秒开场钩子、冲突升级节奏、击中点设计、付费卡点(cliffhanger)、付费频次优化、竖屏节奏
- [ ] **EXPERT-PROD**: Production(制作管理)—— 选角(performer 尚未覆盖)、服化道、灯光、拍摄计划、资源调度、统筹
- [ ] **EXPERT-COMPLI**: 合规与宣发 —— 中国短剧场景刚性需求:内容合规检、脚本护航、爆款元素识别、平台差异版(抖音/快手/小程序剧)裁剪、海报/trailer 生成

**C. 跨专家工作**
- [ ] **CORPUS-01**: 从 4 个语料来源策展(专业书籍/论文、现有短剧/微电影样本、平台指南与爆款公式、AI 生成工具实践经验);每条 ref 标注来源与版权状态
- [ ] **BILINGUAL-01**: SKILL.md 双语格式(英文结构保留 + 中文描述与示例),refs 以中文为主
- [ ] **EVAL-01**: 轻量级 LLM-as-judge 双盲评分 harness(prompts/ 装基准任务、scripts/ 跑双盲、输出对比报告)
- [ ] **DOC-01**: 更新 `skills/movie-experts/README.md`(或新增顶层 DOC)说明 18 专家协作图与 RAG 调用方式

### Out of Scope

<!-- 显式排除 + 理由,防止后续重新加回来 -->

- **Hermes 核心代码改动** —— 用户明确选择「纯 skill + refs」交付,避免 PR 风险,聚焦内容质量
- **新的 Python 包/外部服务** —— 范围控制;现有 Hermes 能力够用
- **独立 vector DB 部署(Chroma/Qdrant 等)** —— 复用现有 memory plugin 即可,新增基础设施超出 v1 范围
- **自动化语料 ingestion pipeline** —— v1 语料靠人工策展,质量优先于规模
- **新增 LLM provider 或 adapter** —— 与 movie-experts 增强无关
- **专门的 web/desktop UI** —— 通过现有 Hermes UI 使用即可,不重复造 UI
- **把现有 14 个 SKILL 完全重写为中文** —— 双语策略是「EN 结构 + CN 描述与示例」,保留与 Hermes 英文社区兼容
- **现有短剧样本的训练/微调** —— 这是 RAG 项目,不是 fine-tune 项目
- **其他创意 skill 类别(comfyui、manim 等)的增强** —— 仅限 `skills/movie-experts/` 范围

## Context

**Brownfield 项目**:这是 Hermes Agent 主仓库内的子系统增强,不另起仓库。

**当前状态(来自 `.planning/codebase/`)**:
- `skills/movie-experts/` 14 个专家是最近一次提交(`4290ab2`)新增的,纯 markdown,无代码
- 每个专家通过 `metadata.hermes.related_skills` 声明协作关系,通过 `expert_id` 和 `metrics` 定义身份与质量标准
- 新增一个专家 = 在 `skills/movie-experts/` 加一个 SKILL.md + 在上下游专家的 `related_skills` 中引用
- Hermes 已有 memory plugin(向量记忆)、image/video/audio generation providers、3D(Bender via scene_builder)等基础设施可直接复用
- 现有专家集中在「制作工艺层」,缺「制作管理层」和「分发合规层」

**已识别的能力缺口**(来自上一轮对话与 codebase map):
- 运镜/摄影能力目前分散在 `scene_builder`(机位规划)和 `animator`(动态执行),无统一的镜头语言表达层
- 短剧主场(中国)特有的「钩子设计」「付费卡点」「平台合规」完全缺失
- 选角、服化道、灯光、制片等制作管理环节无对应专家
- 现有 14 个专家的 prompt 偏「机制描述」,缺少「行业经验」注入

**用户偏好**:混合 RAG(静态主 + memory plugin 可选);深度重构而非轻量增强;双语 SKILL + 中文 refs;v1 含 eval harness;4 种语料来源全要。

**已知风险**:
- 4 种语料来源 × 18 个专家 = 较大策展工作量
- 现有短剧/微电影样本存在版权风险,需谨慎选择公开/授权素材
- 双语内容创作工作量翻倍
- LLM-as-judge eval 受 judge 模型偏差与 prompt 敏感性影响

## Constraints

- **Tech stack**: SKILL.md + references/*.md 纯 markdown;可选调用 Hermes memory plugin(通过 prompt 指令,不修改 plugin 本身)
- **Deliverable form**: 仅 skill 内容(refs + SKILL.md + eval scripts),不改 Hermes 核心 Python/JS 代码 —— *用户明确选择以控制范围*
- **Language**: SKILL.md 双语(英文 YAML 结构 + metadata 保留英文;description 与正文采用 EN structure + 中文段落/示例);refs 以中文为主,关键术语保留英文
- **Eval**: v1 含轻量 LLM-as-judge 双盲 harness(每个 skill 有 benchmark prompts + judge 脚本 + 报告输出)
- **Knowledge sources**: 4 种 —— 专业书籍/论文、现有短剧/微电影样本(仅公开/授权)、平台指南与爆款公式、AI 生成工具实践经验
- **Copyright**: 所有 refs 必须标注来源与版权状态;只使用公开授权或合理引用(fair use)范围内的素材
- **Compatibility**: 不破坏现有 14 专家的 expert_id 与 related_skills 协作图;新增专家必须接入现有协作图
- **Scope**: v1 = 14 重构 + 4 新增 + eval harness;后续扩展(v2)再考虑制作执行编排器、自动化 ingestion 等

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 混合 RAG(静态 refs 主 + memory plugin 可选) | 静态 refs 即开即用、可 git 跟踪、可 code review;向量 RAG 复用 Hermes 现有 memory plugin 不加新基础设施 | — Pending |
| 4 个新增专家(Cinematographer / Hook & Retention / Production / Compliance) | 覆盖短剧创作 v1 关键缺口:镜头语言、留存设计、制作管理、中国合规 | — Pending |
| 现有 14 个深度重构(非轻量加 refs) | 用户选择;深度改进 prompt + 修订 metric + 注入 RAG 指令才能显著提升专家质量 | — Pending |
| SKILL 双语 + refs 中文 | 兼顾 Hermes 英文社区与短剧中国主场;英文 YAML 结构保兼容,中文段落承载行业经验 | — Pending |
| v1 含 eval 脚本 | LLM-as-judge 双盲评分可重复验证增强前后效果,避免「感觉变好」的无依据声明 | — Pending |
| 纯 skill + refs 交付(不改 Hermes 本体) | 减小 PR 风险、聚焦内容质量、与 Hermes 主线解耦 | — Pending |
| 项目位置:直接在 `hermes-agent` 仓库的 `skills/movie-experts/` 下 | 不另起仓库;作为 Hermes 主仓库子系统;`/gsd:new-project` 把整个 hermes-agent 仓库当项目初始化(已与用户确认) | — Pending |
| 现有 14 的 expert_id 与 related_skills 协作图保持向后兼容 | 现有用户的工作流不应被破坏;新增专家接入而非重写协作图 | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-15 after initialization*
