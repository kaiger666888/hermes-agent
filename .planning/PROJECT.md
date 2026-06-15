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
- [x] **AUDIT-01**: 对 14 个现有专家逐一审计,输出 GAP-REPORT.md(Phase 0 完成 2026-06-15)
- [x] **REFACTOR-A**: 对 14 个 SKILL.md 深度重构(Phase 3 完成 4 个深度重构 + Phase 5 完成 10 个 light uplift)
- [x] **REFS-A**: 为 14 个专家各建 `references/` 子目录(Phase 3 + Phase 5 完成,共 30 个 refs across 14 experts)

**B. 4 个新增专家**
- [x] **EXPERT-CINE**: Cinematographer(运镜/摄影指导)—— Phase 4 完成,4 refs + SKILL.md + 3 prompts + 7 peer edges
- [x] **EXPERT-HOOK**: Hook & Retention(钩子与留存)—— Phase 2 完成,4 refs + SKILL.md + 5 prompts
- [x] **EXPERT-PROD**: Production(制作管理)—— Phase 5 完成,AI-relevant subset only(per PROD-07 live-action exclusion),5 refs + SKILL.md + 3 prompts + 8 peer edges
- [x] **EXPERT-COMPLI**: 合规与宣发 —— Phase 1 完成,5 refs + SKILL.md + 5 prompts

**C. 跨专家工作**
- [x] **CORPUS-01**: 从 4 个语料来源策展 — Phase 0-5 完成,共 58 个 refs(~1.2MB),全部 fair-use 引用 + Last-verified 时间戳
- [x] **BILINGUAL-01**: SKILL.md 双语格式 — Phase 0-5 完成所有 18 个 SKILL.md
- [x] **EVAL-01**: 轻量级 LLM-as-judge 双盲评分 harness — Phase 0 完成 runner.py + judge_prompt.md,Phase 3 + Phase 5 完成 11 个 expert × 3-condition dry-run 共 135 verdicts
- [x] **DOC-01**: 顶层 README — Phase 6 完成,18 专家 collaboration DAG + RAG usage guide + Phase 6 live-run procedure

### v1.5 Release Status (2026-06-15)

**完整 18-expert collaboration graph v1.5 release ready:**

- **14 original experts:** all RAG-aware(Phase 3 deep × 4 + Phase 5 light × 10)
- **4 new experts:** compliance_marketing + hook_retention + cinematographer + production
- **总 ref corpus:** 58 个 markdown refs(~1.2MB)
- **Eval harness:** MT-Bench position-swap runner + 3-condition ablation + 135 dry-run verdicts
- **Phantom strip:** 5 phantom refs 清理(animator wan2 / performer 168K / drawer FLUX 1.x / foley AudioLDM-2 / voicer CosyVoice)
- **Model allowlist:** 33 entries in `_shared/known-external-models.yaml`

**Deferred items (operator / live-run):**
- Phase 6 live run execution(需 OPENROUTER_API_KEY + budget)
- N ≥ 20 prompt 扩展 per expert
- Multi-judge ensemble 调用
- Live-run statistical GO/NO-GO verdict(per CONTEXT D-9 criteria)

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
