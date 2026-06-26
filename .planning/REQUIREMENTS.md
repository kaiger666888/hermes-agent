# Requirements: Hermes Agent — Kai's Personal Agent Platform

**Defined:** 2026-06-26 (v9.0 milestone start)
**Core Value:** 让 hermes-agent 成为 Kai 的主 agent — 既承载 movie-experts 这样的领域专家子系统,也具备通用 agent 必备的能力。v9.0 聚焦 kais-movie-pipeline 闭环深化(创意→生产→分发→反馈全闭环 Tier B+C)。

---

## v9.0 Requirements — kais-movie-pipeline 闭环深化

**Source artifact:** Notion page "心流♥ → aigc开发 → 创作方向" (page_id 32811082-af8e-8009-b097-d19a5027b46f); Tier A 已落地为 quick task 260626-vzl refs(platform-specs / creative-redlines / genre-anchor-urban-fantasy)。

**Scope约束:** 仅 `skills/kais-movie-pipeline/` + `skills/movie-experts/` + 新 plugin `plugins/formula_library/`,**不碰 Hermes 核心 Python/JS**;新 gate 注册到现有 `plugins/review_gates/`(Phase 34 已交付 state machine)。

### SLICE — Phase 38 平台母版切片 (Step 14)

- [ ] **SLICE-01**: Pipeline 能从 1 个 master.mp4 产出 7 平台 variants —— 抖音竖屏 9:16 / 抖音横屏 16:9 / 快手竖屏 / B 站横屏 5-10min / 小红书竖屏 3min / 视频号横屏 / 红果/快手极短 1-2min(对应 platform-specs.md 7-row 矩阵)
- [ ] **SLICE-02**: 每个 variant 自动调整 aspect ratio + length + hook position —— 开头 3s 钩子位置 / 中段卡点密度 / 结尾 3s 新钩子按 platform-specs.md 刚性约束
- [ ] **SLICE-03**: 切片元数据持久化到 `pipeline_state.episode_id.variants[]` —— schema 包含 platform / aspect_ratio / length / hook_timestamps / cut_points,供下游 DATA phase 平台 API 接入
- [ ] **SLICE-04**: 新 ref `skills/kais-movie-pipeline/references/platform-master-slicing.md` 文档化 7-variant 切片算法 + 4 关键决策点;SKILL.md body 新增 Step 14 section(不动 frontmatter)

### FORM — Phase 39 配方库 v0 (新 plugin)

- [ ] **FORM-01**: 新 plugin `plugins/formula_library/` scaffold —— `plugin.yaml` + `__init__.py` + `schema.py` (Pydantic) + `library/` 目录持 10 条种子公式 JSON;plugin discovery 通过现有 `hermes_cli/plugins.py` registry
- [ ] **FORM-02**: Schema 字段定义 —— `formula_id` / `genre` / `mood` / `pacing` / `hook_pattern` / `characters` / `runtime_sec` / `platform_fit[]` / `citation` (来源标注,fair-use) / `verified_date` / `eval_score`(可选,从 v6.0 eval gate 回填)
- [ ] **FORM-03**: 10 条种子公式覆盖 5 genre × 2 mood —— 都市奇幻/悬疑反转/家庭情感/校园青春/职场商战 × 轻喜剧/虐心;每条带 source citation(Notion 创作方向 / 公开爆款公式书 / kais-movie-agent 历史 benchmark)
- [ ] **FORM-04**: `kais-movie-pipeline/SKILL.md` 新增 `formula_lookup` 前置 step(Step 0) —— 接受 genre + mood + platform 输入,返回 top-3 匹配公式;`theory_critic/SKILL.md` 增 `formula_reference` 可选输入

### GATE — Phase 40 3 新审核门

- [ ] **GATE-01**: 在现有 `plugins/review_gates/gate.py` state machine 上注册 `redline_emotion_desensitize` gate —— 检测连续 ≥3 帧相同情绪效价(per `creative-redlines.md` R1:情绪脱敏 ≤2 次连续),违规时返回 reject + suggested_action(打散/插入反差)
- [ ] **GATE-02**: 注册 `redline_no_cold_open` gate —— 检测首 3s 是否含背景铺垫(per R3:零背景铺垫切入即冲突);违规时 reject + suggested_action(删铺垫 / 重排首帧)
- [ ] **GATE-03**: 注册 `redline_unfinished_ending` gate —— 检测结尾 3s 是否释放新钩子(per R4:结尾必释放新钩子);违规时 reject + suggested_action(加悬念 / 加新角色登场)
- [ ] **GATE-04**: 3 gates 接入 V8.6 8-gate review sequence(现有 `references/review-gates.md`) —— additive 加入为 gate 9 / 10 / 11,**不替换**现有 8;门序:gate 1-8 通过后,gate 9-11 在最终成片前再扫一次

### PREVIEW — Phase 41 LTX2.3 预览闭环 (Step 6.5)

- [ ] **PREVIEW-01**: 新 ref `skills/kais-movie-pipeline/references/ltx2-preview-loop.md` 文档化 LTX2.3 baseline —— 模型选型(LTX2.3 / CausVid / Kling 1.6 fast)、~5s 生成预算、composition / framing / pacing 3 维校验阈值、prompt 模板
- [ ] **PREVIEW-02**: `kais-movie-pipeline/SKILL.md` 新增 Step 6.5 wiring —— storyboard (Step 6) 通过后,自动调用 LTX2.3 fast-preview,preview 通过才进 Step 7 (dreamina CLI 最终渲染)
- [ ] **PREVIEW-03**: 失败回退策略 —— preview 不达标(pacing 偏差 > 15% / framing 偏差 > 10%)自动回退到 Step 6 重新分镜,max 2 retries;超过 2 次走 operator review gate(现有 `plugins/review_gates/` BLOCKING mode)

### DATA — Phase 42 数据收敛 (Step 15)

- [ ] **DATA-01**: 平台 API adapter 骨架 —— 抖音开放平台 / 快手开放平台 / 视频号 / 小红书薯条 / B 站创作者 5 个 adapter stub;operator 配 API key 后激活(`~/.hermes/.env` 新增 `DOUYIN_API_KEY` 等 5 个);adapter 输出统一 `PlatformMetrics` Pydantic schema
- [ ] **DATA-02**: Schema 扩展 v6.0 FeedbackStore —— `FeedbackRecord` 新增 `platform_metrics` 字段:`completion_rate` / `hook_dropoff_rate` / `engagement_rate` / `save_rate` / `comment_rate`,按 platform 分桶存储
- [ ] **DATA-03**: `formula_tuning_loop` —— 收敛的 metrics 触发自动建议:卡点跳出率高 → 建议加 hook 强度;完播率高但互动低 → 建议加 CTA;建议生成 JSONL review queue(沿用 v6.0 EVOL-02 queue 模式),operator approve 后回写 formula_library
- [ ] **DATA-04**: 新 ref `skills/kais-movie-pipeline/references/data-convergence.md` + dashboard —— `hermes formula stats` rich tables(per-formula / per-platform metrics);`--json` counts-only flag

### VALIDATE — Phase 43 集成验证 + close-out

- [ ] **VALIDATE-01**: 跨 5 phase integration-checker 全 pass —— Phase 38 SLICE 输出 variants[] → Phase 42 DATA adapter 消费;Phase 39 FORM formula_lookup → Phase 40 GATE suggested_action 引用;Phase 41 PREVIEW 回退到 Step 6 → 不破坏现有 13 step I/O 契约
- [ ] **VALIDATE-02**: FOUND-08 preserved milestone-wide —— zero expert_id changes / zero frontmatter changes across all 16 active movie-experts, byte-diff 验证(对照 v9.0 start commit `a2a20d2be`)
- [ ] **VALIDATE-03**: Canonical `.planning/milestones/v9.0-MILESTONE-AUDIT.md` —— 22/22 req coverage + 6/6 phase outcomes + integration matrix + FOUND-08 evidence chain + operator-action-handoffs 文档化

---

## Future Requirements (v10+ candidates)

Acknowledged but deferred — NOT in v9.0 roadmap.

### FEISHU (from v7.0 deferred)

- **FEISHU-01**: feishu-doc / feishu-drive / feishu-perm / feishu-wiki migration
- **FEISHU-02**: merge-vs-keep-4 设计决策

### AGENT (from v7.0 deferred)

- **AGT-01**: Multi hermes profile mechanism
- **AGT-02**: acp-router alternative form in hermes

### V9-FUTURE (acknowledged at v9.0 planning)

- **V9-FUTURE-01**: Live platform API data ingestion(live smoke-test,operator 配 key 后激活)
- **V9-FUTURE-02**: LTX2.3 真实模型生成验证(目前仅 baseline 文档 + adapter 骨架)
- **V9-FUTURE-03**: formula_library 扩展到 50+ 公式(目前 10 seed)
- **V9-FUTURE-04**: A/B 测试框架(per-variant metrics 对比 + 显著性检验)
- **V9-FUTURE-05**: 跨 milestone: kais-movie-pipeline v10 + 视觉系升级(TRELLIS 2 → Blender 3D 资产管线)

---

## Out of Scope

Explicit exclusions for v9.0 — to prevent scope creep.

| Feature | Reason |
|---------|--------|
| **Hermes 核心 Python/JS 代码改动** | 用户明确选择「纯 skill + refs + plugin」交付,避免 PR 风险,聚焦闭环逻辑;新 plugin `plugins/formula_library/` 是 hermes-agent 内 plugin 不是核心代码 |
| **kais-movie-agent repo 改动** | per v5.0 cross-repo migration decision,kais-movie-agent repo 保持 read-only;所有 v9.0 deliverable 在 hermes-agent 内 |
| **LTX2.3 真实生成测试** | Live GPU 测试 operator-side,v9.0 只产出 baseline 文档 + adapter 骨架;V9-FUTURE-02 deferred |
| **Live 平台 API 数据接入** | 5 平台 API key 由 operator 配置,v9.0 提供 adapter 骨架 + schema,operator 配 key 后激活;V9-FUTURE-01 deferred |
| **新增 movie-experts expert_id** | FOUND-08 frozen rule 继续生效;v9.0 不新增 expert_id,只在现有 16 active experts 上 patch SKILL.md body |
| **重构 V8.6 13-step 编号** | 新增 Step 6.5 / 14 / 15 是 additive,不重排现有 13 step;V8.6 编号稳定性优先 |
| **Multi-profile / agent 切换** | v7.0 deferred,v9.0 不触及 |
| **Feishu / ACP skills** | v7.0 deferred,v9.0 不触及 |
| **现有 14 active movie-experts 内容重写** | v9.0 只在 `theory_critic` + `compliance_gate` + `editor` 3 个 expert 上 patch SKILL.md body 加 formula/reference,其他 13 个不动 |

---

## Traceability

Updated during roadmap creation. v9.0 phases 38-43.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SLICE-01 | Phase 38 | Phase-assigned |
| SLICE-02 | Phase 38 | Phase-assigned |
| SLICE-03 | Phase 38 | Phase-assigned |
| SLICE-04 | Phase 38 | Phase-assigned |
| FORM-01 | Phase 39 | Phase-assigned |
| FORM-02 | Phase 39 | Phase-assigned |
| FORM-03 | Phase 39 | Phase-assigned |
| FORM-04 | Phase 39 | Phase-assigned |
| GATE-01 | Phase 40 | Phase-assigned |
| GATE-02 | Phase 40 | Phase-assigned |
| GATE-03 | Phase 40 | Phase-assigned |
| GATE-04 | Phase 40 | Phase-assigned |
| PREVIEW-01 | Phase 41 | Phase-assigned |
| PREVIEW-02 | Phase 41 | Phase-assigned |
| PREVIEW-03 | Phase 41 | Phase-assigned |
| DATA-01 | Phase 42 | Phase-assigned |
| DATA-02 | Phase 42 | Phase-assigned |
| DATA-03 | Phase 42 | Phase-assigned |
| DATA-04 | Phase 42 | Phase-assigned |
| VALIDATE-01 | Phase 43 | Phase-assigned |
| VALIDATE-02 | Phase 43 | Phase-assigned |
| VALIDATE-03 | Phase 43 | Phase-assigned |

**Coverage:**
- v9.0 requirements: 22 total (SLICE×4 + FORM×4 + GATE×4 + PREVIEW×3 + DATA×4 + VALIDATE×3)
- Mapped to phases: 22 / 22 ✓
- Unmapped: 0

---

*Requirements defined: 2026-06-26 — v9.0 milestone start (6 phases 38-43, 22 reqs).*
*Last updated: 2026-06-26 — ROADMAP created; traceability status flipped Pending → Phase-assigned (22/22 mapped to Phases 38-43).*
