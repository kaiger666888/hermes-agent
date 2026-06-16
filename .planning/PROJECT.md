# Movie-Experts Suite v2 — 短剧/微电影创作专家增强

## What This Is

Hermes Agent 的 `skills/movie-experts/` 专家体系的增强项目:在现有 14 个电影制作专家(编剧、绘图、动画、剪辑、调色、配乐、表演、场景、拟音、空间音频、混音、配音、连续性、风格基因组)基础上,通过 RAG 增强其行业经验,并补全 AI 短剧(短剧/竖屏短剧)与微电影创作全链路的关键缺口 —— 新增运镜指导、Hook & Retention、制作管理、合规与宣发 4 个专家。目标是让每个专家不再是「懂语法的模板」,而是「懂行业的专家」。

## Core Value

每个 movie-expert skill 都能用检索增强的方式调用行业知识库(静态 refs 为主,可选向量 RAG),让 AI 生成的短剧/微电影在专业度上接近人类创作者水平 —— 这是决定短剧生死的核心。

## Requirements

### Validated

<!-- v1 shipped — see .planning/MILESTONES.md for full inventory -->

**Pre-v1 baseline (existing capabilities):**
- ✓ 14 个专家 skill 已运行(screenplay, drawer, animator, editor, colorist, composer, performer, scene_builder, foley, spatial_audio, mixer, voicer, continuity, style_genome) — existing
- ✓ 模块化 SKILL.md 发现机制(metadata.hermes schema + related_skills 协作图) — existing
- ✓ 每个专家独立的编码矩阵(5D style genome、CxSxZ color、FxRxT editing、ExBxSxP performance、7D foley) — existing
- ✓ SKILL.md 纯 markdown,无 Python 代码 — existing
- ✓ Hermes memory plugin 已部署(可选向量 RAG 复用基础) — existing

**v1 / v1.5 — shipped 2026-06-15 (milestone tag `v1`):**
- ✓ AUDIT-01: 14-expert gap audit + phantom-ref strip (Phase 0)
- ✓ REFACTOR-A: 14 SKILL.md refactored (Phase 3 deep × 4 + Phase 5 light × 10)
- ✓ REFS-A: 58 markdown refs across 18 experts (Phase 3 + Phase 5)
- ✓ EXPERT-CINE: cinematographer (Phase 4 — 4 refs + SKILL.md + 3 prompts + 7 peer edges)
- ✓ EXPERT-HOOK: hook_retention (Phase 2 — 4 refs + SKILL.md + 5 prompts)
- ✓ EXPERT-PROD: production (Phase 5 — 5 refs + SKILL.md + 3 prompts + 8 peer edges; AI-relevant subset per PROD-07)
- ✓ EXPERT-COMPLI: compliance_marketing (Phase 1 — 5 refs + SKILL.md + 5 prompts)
- ✓ CORPUS-01: 58 refs curated from 4 source types (~1.2MB, all fair-use + Last-verified stamps)
- ✓ BILINGUAL-01: 18 SKILL.md files in EN structure + CN prose format
- ✓ EVAL-01: MT-Bench position-swap harness + 3-condition ablation + 135 dry-run verdicts
- ✓ DOC-01: top-level README with 18-expert collaboration DAG + RAG usage guide + Phase 6 live-run procedure

### Active

<!-- v2.0 in planning — REQ-IDs assigned after step 9 of /gsd-new-milestone. See REQUIREMENTS.md. -->

Milestone **v2.0 — Pipeline Redesign from First Principles (PRFP)** is being scoped. Requirements TBD via this workflow; see `.planning/REQUIREMENTS.md` once written.

### Deferred to operator (acknowledged at v1 close)

- Phase 6 live-run execution (requires `OPENROUTER_API_KEY` + budget)
- N ≥ 20 prompt expansion per expert (currently 3)
- Multi-judge ensemble invocation (currently single-judge)
- Live-run statistical GO/NO-GO verdict per CONTEXT D-9
- CN legal review of compliance_marketing refs (statutes + platform thresholds)
- Phase 6 UAT (10 checkpoints — paused at user redirect)
- Full bilingual consistency lint (full v1.5 corpus now shipped; spot-check performed)

See `.planning/STATE.md` § Deferred Items for the canonical list.

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

**v1 shipped state (2026-06-15):**
- `skills/movie-experts/` 下 18 个专家目录,全部 RAG-aware(14 refactor + 4 new)
- 58 markdown refs(~1.2MB),全部 fair-use 引用 + `Last-verified: 2026-06-15` stamps + per-ref LICENSE.md
- 5 phantom refs 清理:animator wan2 → Hermes catalog / performer "168K controlled tokens" → stripped / drawer FLUX 1.x → FLUX 2 / foley AudioLDM-2 → Stable Audio Open / voicer CosyVoice → multi-provider TTS
- `_eval/` harness: `runner.py`(MT-Bench position-swap)+ `snapshot.py`(sha256+git-sha provenance)+ `judge_prompt.md`(4-dim rubric)+ `config.yaml.example` + 9 prompt files + 14 baseline snapshots + 40+ reports
- `_shared/`: `glossary.md`(EN↔CN)+ `known-external-models.yaml`(33 entries)+ `platform-comparison.md` + `RAG-INVOCATION-PATTERN.md` + `SKILL-LAYOUT.md`
- Top-level `README.md`(297 lines / 20KB)documenting 18-expert collaboration DAG + RAG usage guide + Phase 6 live-run procedure
- 4 个新专家全部接入 `related_skills` 协作图(bidirectional edges preserved for frozen 14 expert_ids)

**Brownfield 基础(沿用)**:
- Hermes 已有 memory plugin(向量记忆)、image/video/audio generation providers、3D(Blender via scene_builder)等基础设施
- 每个专家通过 `metadata.hermes.related_skills` 声明协作关系,通过 `expert_id` 和 `metrics` 定义身份与质量标准

**v1 deferred to operator**(详见 `.planning/STATE.md` § Deferred Items):
- Phase 6 live-run execution(需 OPENROUTER_API_KEY + budget)
- N ≥ 20 prompt expansion + multi-judge ensemble + statistical GO/NO-GO verdict
- CN legal review of compliance_marketing refs( statutes + platform thresholds )
- Phase 6 UAT(10 checkpoints paused)
- Full bilingual consistency lint(corpus complete;spot-check performed)

**已知风险**(进入 v2 仍需关注):
- ⚠ Platform guideline drift —— 抖音/快手/视频号 guidelines 季度更新;refs 已带 `verified_date` + 90-day refresh cadence
- ⚠ 短剧 sample copyright —— fair-use 边界需 per-ref LICENSE.md 持续维护
- ⚠ LLM-as-judge invalidity —— live run 未执行前 Phase 3 GO/NO-GO 仍为 CONDITIONAL

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
| 混合 RAG(静态 refs 主 + memory plugin 可选) | 静态 refs 即开即用、可 git 跟踪、可 code review;向量 RAG 复用 Hermes 现有 memory plugin 不加新基础设施 | ✓ Good — 58 refs git-tracked;memory plugin optional path documented in `_shared/RAG-INVOCATION-PATTERN.md` |
| 4 个新增专家(Cinematographer / Hook & Retention / Production / Compliance) | 覆盖短剧创作 v1 关键缺口:镜头语言、留存设计、制作管理、中国合规 | ✓ Good — all 4 shipped with RAG refs + peer edges into collaboration graph |
| 现有 14 个深度重构(非轻量加 refs) | 用户选择;深度改进 prompt + 修订 metric + 注入 RAG 指令才能显著提升专家质量 | ⚠ Revisit — Phase 3 deep × 4 measurable uplift pending live run;Phase 5 light × 10 unmeasured. Statistical evidence deferred to operator. |
| SKILL 双语 + refs 中文 | 兼顾 Hermes 英文社区与短剧中国主场;英文 YAML 结构保兼容,中文段落承载行业经验 | ✓ Good — 18 SKILL.md shipped in EN+CN format; spot-check passed |
| v1 含 eval 脚本 | LLM-as-judge 双盲评分可重复验证增强前后效果,避免「感觉变好」的无依据声明 | ✓ Good — runner.py + judge_prompt + 3-condition ablation + 135 dry-run verdicts;⚠ statistical GO/NO-GO deferred |
| 纯 skill + refs 交付(不改 Hermes 本体) | 减小 PR 风险、聚焦内容质量、与 Hermes 主线解耦 | ✓ Good — zero Hermes core changes; all deliverables under `skills/movie-experts/` |
| 项目位置:直接在 `hermes-agent` 仓库的 `skills/movie-experts/` 下 | 不另起仓库;作为 Hermes 主仓库子系统;`/gsd:new-project` 把整个 hermes-agent 仓库当项目初始化(已与用户确认) | ✓ Good — co-located; .planning/ tracks project state |
| 现有 14 的 expert_id 与 related_skills 协作图保持向后兼容 | 现有用户的工作流不应被破坏;新增专家接入而非重写协作图 | ✓ Good — FOUND-08 frozen rule honored across all phases; verified at Phase 1 VERIFICATION SC-4 |

## Previous Milestone: v2.0 — Pipeline Redesign from First Principles (PRFP) ✅ SHIPPED

**Status:** Design shipped 2026-06-16 (Phases 7-12 all passed). 52/52 requirements verified. Design suite at `.planning/research/v2-pipeline-design/`. Frozen-pending-impl.

**Goal:** 从第一性原理出发(忽略现有 kais-movie-agent 8 phases 和 hermes movie-experts 26 skills 的历史包袱),推导出 kais-movie-agent 的新工作流节点集 —— 每节点明确**核心任务 + I/O 契约 + AIGC 转化点 + 传统经验锚点**,作为后续双 repo 实施的理论蓝本。

**Target features(本次里程碑只产出设计文档,不实施任何代码重构):**

1. **第一性原理推导记录** —— 从"观众最终要拿到什么 / 短剧为什么生死在前 3 秒 / 微电影质量由什么决定 / AI 真正能提效的环节在哪 / AI 不能替代什么"这种根本问题出发,逐步推导到最简必要的节点集;Musk-style 还原→推导(非类比)。
2. **工作流节点流程设计** —— 节点 DAG + 每节点核心任务 + I/O 契约 + 节点间依赖与产物传递路径。
3. **传统经验锚点对照** —— 每节点溯源到 102 本书(`_shared/project-corpus/` 9 ref + `/home/kai/Downloads/100+本影视剪辑书/` 原始 repo)里的传统工序 / 技巧 / 范例。
4. **LLM 创意凝练专题** —— 单独子文档:大模型如何产出**有创意且逻辑自洽**的故事框架(用户特别强调的洞察层;记录:创意的本质、自洽性的检验机制、LLM 凝练的 prompt 策略、fail modes)。
5. **双 repo 交接说明** —— 设计如何分别指导 hermes-agent 的 skills 演化(后续里程碑对齐)+ kais-movie-agent 的 pipeline 重构(后续在 kais-movie-agent/.planning/ 那边再开 phase 执行实施)。

**Key context:**

- **节点设计从 0 推**:不预设现有 8 phases 和 26 skills,但产出后会跟它们做**对照分析**(用于识别覆盖缺口和 AIGC 转化机会,非实施)。
- **物理位置:双 repo 协作**。本里程碑的 .planning/ 写在 hermes-agent(因为 movie-experts 是 kais-movie-agent 的知识层,设计文档作为交接件自然放这里);后续 kais-movie-agent 那边自己开 phase 执行实施。
- **范围严格收口**:本次里程碑交付**仅设计文档**,不动 hermes-agent/skills/ 任何 SKILL.md / refs,不动 kais-movie-agent/lib/ 任何 .js / .py。
- **马斯克第一性原理**贯穿:每个节点都要能回答"为什么是它而不是别的";每个 AIGC 转化点都要能回答"这个转化对最终用户价值的边际贡献是什么"。
- **大模型创意凝练洞察**作为独立维度贯穿设计:不只是"用 AI 生成 X",而是"如何让 AI 凝练出 X 的最小可行结构"。

**Shipped artifacts (18 files, ~340KB):**
- `00-FIRST-PRINCIPLES.md` (1638 行 derivation)
- `01-NODE-DAG.md` + `02-NODE-SPECS.md` + `nodes.yaml` + `edges.yaml`
- `03-CORPUS-TRACEABILITY.md` + `corpus-trace.yaml`
- `04-LLM-CREATIVE-DISTILLATION.md`
- `05-COMPARISON-VS-8-PHASES.md` + `06-COMPARISON-VS-26-SKILLS.md` + `07-HANDOFF-PLAN.md`
- `skills-mapping.yaml` + `kais-migration-matrix.yaml`
- `08-GOVERNANCE.md` + `09-OPEN-QUESTIONS.md` + `10-CHANGELOG.md` + `README.md`
- `scripts/validate_design.py` (~30 行 governance lint)

---

## Previous Milestone: v3.0 — Skills-to-DAG Alignment ✅ SHIPPED 2026-06-17

**Goal (achieved):** Aligned hermes-agent `skills/movie-experts/` from v1 expert layout to v2.0 PRFP DAG topology via 2 renames + 2 merges + 1 new AI-native + 3 deprecations. All 13 legacy expert_id migrations preserved via FOUND-08 backward-compat aliases.

**Stats:** 6 phases (13-18) · 16 plans · 67 commits · 137 files changed · 19007 insertions · 2137 deletions · 1-day execution (2026-06-16 → 2026-06-17)

**Audit status:** tech_debt (12/12 requirements satisfied, 4 non-blocking WARNINGs) — see `.planning/v3.0-MILESTONE-AUDIT.md`

**Key outcomes:**

- **5 new expert directories:** `continuity_auditor`, `compliance_gate`, `visual_executor` (sub_steps: [drawer, animator]), `audio_pipeline` (sub_steps: [voicer, lip_sync, composer, foley, mixer, spatial_audio] — spatial_audio FOLDED as 6th sub-step per D-1), `prompt_injector` (NEW AI-native)
- **3 deprecated experts:** `performer` (→ character_designer + screenplay), `scene_builder` (→ cinematographer + style_genome), `storyboard_designer` (→ cinematographer composition_lock)
- **10 redirect stubs** preserving v1 expert_ids (continuity, compliance_marketing, drawer, animator, voicer, lip_sync, composer, foley, mixer, spatial_audio)
- **31 SKILL.md files reconciled** into 4 buckets: 15 active DAG + 3 active non-DAG + 3 deprecated + 10 redirect stubs
- **skills-mapping.yaml** all 19 entries signed_off (16 mappings + 3 deprecate_candidates); production deferred per FUTURE-09
- **README.md** Mermaid DAG replaces ASCII art with canonical 01-NODE-DAG.md §1.5 topology
- **Glossary** 5 new terms (visual_executor, audio_pipeline, prompt_injector, continuity_auditor, compliance_gate)
- **known-external-models.yaml** Phase 8 §2.17 dated annex (27 entries with verified_date: 2026-06-17)

**Known deferred items at close:**

- W-1: creative_source → topic_curator dead ref (pre-existing v2.0)
- W-2: character_designer missing Phase 17 inheritance body annotation
- W-3: 32 pre-existing v2.0 bidirectional asymmetries
- W-4: Frontmatter `status:` field path inconsistency (documentation drift)
- VALIDATE-D1: quality_gate gap — canonical 16th DAG node has no SKILL.md
- FUTURE-09: production expert (disposition: deferred)

See full archive: `.planning/milestones/v3.0-ROADMAP.md`

---

## Current Milestone: None (awaiting operator decision)

v3.0 milestone archived 2026-06-17. Operator may:

- Start v4 via `/gsd:new-milestone` (suggest: clean up v3.0 deferred items W-1 through W-4 + VALIDATE-D1)
- Run `/gsd:review-backlog` to triage
- Run `/gsd:progress` to view state

---

## Previous Milestone (legacy section): v3.0 — Skills-to-DAG Alignment [LEGACY TEXT — pre-shipping]

**Goal:** 把 hermes-agent `skills/movie-experts/` 从 26 experts 对齐到 v2.0 PRFP 设计的 16 pipeline-roles —— 执行 `skills-mapping.yaml` 锁定的 rename / merge / new / deprecate 决定,让 skills 知识层与新 DAG 干净映射。

**Target features(本次里程碑执行设计决策,实施 skills 重构):**

1. **Rename 2 experts(per `skills-mapping.yaml` pending sign-off):**
   - `continuity` → `continuity_auditor`(强调 critic 角色)
   - `compliance_marketing` → `compliance_gate`(分离 pure compliance 与 marketing)
2. **Merge 7 experts → 2(per `skills-mapping.yaml`):**
   - `drawer` + `animator` → `visual_executor`(consistency context 统一)
   - 5 audio experts(`voicer` + `composer` + `foley` + `mixer` + `spatial_audio`)→ `audio_pipeline`(PITFALLS §2.6 节点压缩)
3. **Add 1 new AI-native expert:**
   - `prompt_injector`(无 v1 precedent,AI-native 节点 per Phase 7 §4.7)
4. **Resolve 3-4 deprecate candidates(per `06-COMPARISON-VS-26-SKILLS.md`):**
   - `performer` → 折叠进 character_designer + screenplay
   - `scene_builder` → 折叠进 cinematographer + style_genome
   - `storyboard_designer` → 折叠进 cinematographer composition_lock
   - `production` → defer 到未来 milestone(超 v3.0 范围)
5. **FOUND-08 frozen rule compliance:** 所有保留的 expert_id 不变量维护;rename + merge 显式 mapping 记录;deprecate 不静默。

**Key context:**

- **Source-of-truth:** `skills-mapping.yaml` 是 canonical 映射;`.planning/research/v2-pipeline-design/` 全部 18 个设计文档作为决策依据
- **Per HANDOFF-05 ownership matrix:** 本里程碑是 **design-intent layer** owner(hermes-agent);co-owned DAG 修改需与 kais-movie-agent team sign-off
- **FOUND-08 frozen rule:** v1 expert_id 不能静默重命名;所有 rename 必须显式 mapping + sign-off
- **Backward compatibility:** 现有创作者 workflow 不破坏;rename experts 必须保留旧 expert_id 作为 alias(可选)
- **范围严格收口:** 仅 hermes-agent `skills/movie-experts/` 范围;kais-movie-agent impl 是 parallel milestone(在该 repo)
- **Physical location:** skills 改动在 `skills/movie-experts/`;planning 文档继续在 `.planning/`

---

## Previous Milestone: v2.0 — Pipeline Redesign from First Principles (PRFP) ✅ SHIPPED

**Goal:** 从第一性原理出发(忽略现有 kais-movie-agent 8 phases 和 hermes movie-experts 26 skills 的历史包袱),推导出 kais-movie-agent 的新工作流节点集 —— 每节点明确**核心任务 + I/O 契约 + AIGC 转化点 + 传统经验锚点**,作为后续双 repo 实施的理论蓝本。

**Target features(本次里程碑只产出设计文档,不实施任何代码重构):**

1. **第一性原理推导记录** —— 从"观众最终要拿到什么 / 短剧为什么生死在前 3 秒 / 微电影质量由什么决定 / AI 真正能提效的环节在哪 / AI 不能替代什么"这种根本问题出发,逐步推导到最简必要的节点集;Musk-style 还原→推导(非类比)。
2. **工作流节点流程设计** —— 节点 DAG + 每节点核心任务 + I/O 契约 + 节点间依赖与产物传递路径。
3. **传统经验锚点对照** —— 每节点溯源到 102 本书(`_shared/project-corpus/` 9 ref + `/home/kai/Downloads/100+本影视剪辑书/` 原始 repo)里的传统工序 / 技巧 / 范例。
4. **LLM 创意凝练专题** —— 单独子文档:大模型如何产出**有创意且逻辑自洽**的故事框架(用户特别强调的洞察层;记录:创意的本质、自洽性的检验机制、LLM 凝练的 prompt 策略、fail modes)。
5. **双 repo 交接说明** —— 设计如何分别指导 hermes-agent 的 skills 演化(后续里程碑对齐)+ kais-movie-agent 的 pipeline 重构(后续在 kais-movie-agent/.planning/ 那边再开对应 phase)。

**Key context:**

- **节点设计从 0 推**:不预设现有 8 phases 和 26 skills,但产出后会跟它们做**对照分析**(用于识别覆盖缺口和 AIGC 转化机会,非实施)。
- **物理位置:双 repo 协作**。本里程碑的 .planning/ 写在 hermes-agent(因为 movie-experts 是 kais-movie-agent 的知识层,设计文档作为交接件自然放这里);后续 kais-movie-agent 那边自己开 phase 执行实施。
- **范围严格收口**:本次里程碑交付**仅设计文档**,不动 hermes-agent/skills/ 任何 SKILL.md / refs,不动 kais-movie-agent/lib/ 任何 .js / .py。
- **马斯克第一性原理**贯穿:每个节点都要能回答"为什么是它而不是别的";每个 AIGC 转化点都要能回答"这个转化对最终用户价值的边际贡献是什么"。
- **大模型创意凝练洞察**作为独立维度贯穿设计:不只是"用 AI 生成 X",而是"如何让 AI 凝练出 X 的最小可行结构"。

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
*Last updated: 2026-06-17 — v3.0 milestone archived (tech_debt: 12/12 reqs satisfied, 4 warnings); awaiting next milestone decision*
