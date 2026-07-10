# Hermes Agent — Kai's Personal Agent Platform

## What This Is

Kai 的个人 Hermes Agent 平台。v1-v6 聚焦 `skills/movie-experts/` 短剧/微电影创作专家体系(14 重构 + 4 新增 + RAG 增强 + 反馈闭环自学习);**v7.0 起** 项目范畴拓宽为「openclaw → hermes-agent 主 agent 迁移」,把 coding-agent / tmux-agents / feishu / agent 定义 / 身份记忆等通用 agent 能力从 openclaw 接管到 hermes-agent,让 hermes-agent 成为 Kai 的主 agent。movie-experts 后续深化在另一 repo(kais-movie-agent)处理。

## Core Value

让 hermes-agent 成为 Kai 的主 agent:既承载 movie-experts 这样的领域专家子系统(v1-v6 已 shipped),也具备通用 agent 必备的代码委派、自动化集成、文档协作、个人身份与记忆能力(v7.0 迁移目标)—— 任何 openclaw 能做的事,hermes-agent 都能做,且做得更好。

## Current Milestone: v15.0 — Operator-Action Closure Tooling (STARTED 2026-07-10)

**Goal:** Author production-grade tooling + workflows that close v14.0's 6 operator-action handoffs by making them executable; captured data flows back to code (VERSION.json locks, calibration thresholds, validation verdicts).

**Target features (6 tracks mirroring v14.0 operator-action handoffs):**

1. **DUB-05 Benchmark Runner** — `scripts/run_cosyvoice_benchmark.py` takes 3-5 dialogue lines + runs both CosyVoice 2.0-0.5B + Fun-CosyVoice 3.0 + outputs side-by-side comparison report; operator runs once + locks `VERSION.json.tts.cosyvoice_default_variant`.
2. **TRANS-07 LTX-FLF Validation Runner** — ComfyUI workflow JSON + `scripts/run_ltx_flf_validation.py` submits 1-2 reference shots + captures results + writes production-readiness verdict to `ltx-flf-iclora-validation.md`; gates TRANS-11 v16+ rollout.
3. **IMG-09 False-Positive Calibration** — `scripts/calibrate_vision_verify.py` analyzes `~/.hermes/metrics/dreamina_stats.jsonl` production data + recommends confidence threshold per stratum (1-ref/3-ref/5-ref); operator reviews + commits calibrated thresholds.
4. **DUB-03 Voice Sample Collection Protocol** — `references/voice-sample-collection-protocol.md` + `scripts/validate_voice_clone_batch.py` (batch-validates operator-provided wavs against 3-10s + wav + ≥16kHz + mono rules); operator sources wavs per protocol.
5. **XCUT-04b Cloud Engine Bootstrap** — `references/cloud-engine-bootstrap.md` (Hailuo + Vidu API key acquisition + ComfyUI Wan2.2 FLF2V node install + cost-estimation worksheet); operator opts in per engine.
6. **XCUT-04c GLM-4.6V Cost Tracking** — Extend `dreamina_stats.py` MetricsBuffer to track per-batch GLM-4.6V token spend + monthly aggregate; `hermes glm stats` CLI subcommand.

**Cross-cutting phases:**

- **VALIDATE** — closes v14.0 tech_debt items in the audit; re-runs `76-meta-rule-x2-audit.sh` + extends to v15.0 `_INSTRUCTION` constants.
- **LINEAGE-BUMP** (if any SKILL.md touched in v15.0) — regenerate agent.yaml per XCUT-03 pattern.

**Hard constraints preserved (沿用 v14.0):**

- INFRA-04 serial execution NOT lifted
- EVAL-06 dry-run-first NOT changed (curator `--live` opt-in; v15.0 doesn't unfreeze)
- FOUND-08 15-expert set frozen
- SKILL.md L1-L6 read-only invariant **REVERTS** unless v15.0 re-authorizes the破例 (default: only kais-jimeng-cli SKILL.md may be touched for cloud-engine-bootstrap doc references; no Form/DUB/IMG/TRANSITION SKILL.md body changes)

**Cross-repo topology (沿用):** hermes-agent repo = GSD `.planning/` 工件; kais-hermes-skills repo = scripts + refs + Python. Final cross-repo pins recorded at v15.0 close.

## Previous Milestone: v14.0 ✅ SHIPPED 2026-07-10 — kais-movie-pipeline 形态/音频/图像/转场 4 项升级

**Stats:** 7 phases (70-76) · 17 plans · 36 tasks · 26/26 reqs mapped (24 satisfied + 2 operator-handoff) · Tag `v14.0` · Audit `tech_debt`

**Goal (achieved):** 把 kais-movie-pipeline 从「竖屏短剧专用」升级为「横竖双 default 的通用短片创作管线」，同步升级配音 (CosyVoice)、图像 (dreamina cli 深度集成)、转场(创作+数据+生成三层)三个核心生成环节。**v14.0 是 v9.0 后首个 kais-movie-pipeline-focused milestone，重启跨 repo 工作流**（plan → hermes-agent/.planning/，code → kais-hermes-skills/）。

**4 tracks shipped:**

1. **FORM (Phase 71)** — `PipelineState.form_factor` Literal["landscape","portrait"] field + 15 SKILL.md `## Form Factor Adaptation` sections tiered Tier 1/2/3 + Step 14 4-cell reframe matrix + MSR_FC=17→41 sweep + `_FORM_FACTOR_INSTRUCTION` injection into p09 GoalBuilder.
2. **DUB (Phase 72)** — CosyVoice 2.0-0.5B promoted to P10 default (dual-path gold-team + ComfyUI AIIA) + `validate_tts_engine_division` strict division rule (DUB-02) + `validate_voice_clone_ref` (DUB-03) + IndexTTS2 DEPRECATED fallback (DUB-04) + `_TTS_ENGINE_INSTRUCTION` first p10 _INSTRUCTION + top-level `VERSION.json` lock site for DUB-05.
3. **IMG (Phase 73)** — `dreamina_manager.py` orchestrator (asyncio.Semaphore(10) + tenacity AsyncRetrying + block-on-all) + `vision_verify.py` GLM-4.6V gate via `task="vision"` routing (CRITICAL CORRECTION — `prefer_vision=True` does NOT exist) + `dreamina_stats.py` MetricsBuffer + RHD/LHD 3-attempt budget + image2image-stratification ref + `hermes dreamina stats` CLI + `_VISION_VERIFY_INSTRUCTION` 3-site injection in p07.
4. **TRANSITION (Phase 74)** — `transition_schema.py` (12-enum + 6-enum + `load_next_shot_link` backward-compat) + `transition_design.json` first-class asset (3 systems wired) + field-level ownership split cinematographer/editor (TRANS-04, FOUND-08 preserved) + 12-type taxonomy ref + declarative routing rules ref (INFRA-04 compliant) + LTX-FLF validation template (TRANS-07) + `_TRANSITION_DESIGN_INSTRUCTION` + `_EDITOR_TRANSITION_EXECUTION_INSTRUCTION` (p13 first _INJECTION).

**Cross-cutting phases shipped:**

- **Phase 70 FOUNDATION-AUDIT** — Lineage Impact Inventory + curator freeze + cross-repo baseline pins + Phase 76 VALIDATE-CHECKLIST (34 rows) + 70-smoke.sh.
- **Phase 75 LINEAGE-BUMP** — 15 agent.yaml regeneration (Track A 9 EXPERTS_9 + Track B 6 v13.0 P62); `75-lineage-assert.sh` 15/15 PASSED; curator freeze released as final action.
- **Phase 76 VALIDATE** — `76-meta-rule-x2-audit.sh` (36 MUSTs / 13 _INSTRUCTION / 4/4 goal-tests PASSED) + ancestry assertion (both repos descendants of P70 baselines) + `v14.0-MILESTONE-AUDIT.md` (424 lines, verdict `tech_debt`) + tag `v14.0` placed.

**Operator-action-handoffs (6, per XCUT-04 spec — NOT gaps):**

- DUB-05 A/B benchmark: CosyVoice 2.0-0.5B vs Fun-CosyVoice 3.0 on 3-5 reference dialogue lines (locks default variant in `VERSION.json`).
- DUB-03 voice_clone_reference_wav: operator-sourced per-character 3-10s reference audio samples.
- IMG-03 / XCUT-04c vision-verify API cost: GLM-4.6V batch calls at production scale (~178 calls per 213-shot episode).
- XCUT-04b Hailuo/Vidu API keys: opt-in for cloud Chinese-content transition engines per TRANS-06.
- TRANS-07 LTX-FLF+ICLoRA validation report: operator runs 1-2 reference shots; gates TRANS-11 v15+ production rollout.
- Manual UAT: horizontal-screen-framing.md citation fair-use review + Tier 1 transition-design.md content substance review (carry-forward).

**Cross-repo topology (reactivated from v9.0):** hermes-agent repo = GSD `.planning/` 工件; kais-hermes-skills repo = SKILL.md + refs + Python + ComfyUI workflow. Final cross-repo pins: hermes-agent `4e7c58cc9cac3c4925770beaf5a9433369094a24`, kais-hermes-skills `ba58c2548ab82f0cd9acd7cc7af14402137f8520`. Both verified descendants of P70 baselines via `git merge-base --is-ancestor` (exit 0).

**Hard constraints preserved:**

- INFRA-04 serial execution NOT lifted (all IMG/TRANSITION code paths sync-only or declarative; zero `asyncio.gather` for GLM-coupled code)
- EVAL-06 dry-run-first NOT changed (curator `--live` frozen for v14.0 duration, released only post-Phase-75 bump)
- FOUND-08 15-expert set frozen (TRANS-04 field-level ownership split; zero new expert_id)
- SKILL.md L1-L6 read-only invariant exception破例 authorized for v14.0 only (lineage regeneration mandatory per XCUT-03; reverts read-only v15+ unless re-authorized)

See `.planning/milestones/v14.0-ROADMAP.md` for the full archive + `.planning/milestones/v14.0-REQUIREMENTS.md` for requirement outcomes + `.planning/milestones/v14.0-MILESTONE-AUDIT.md` for the audit report.

## Current State (v14.0 SHIPPED 2026-07-10)

v14.0 milestone SHIPPED + closed 2026-07-10 (tag `v14.0` placed, phases archived to `.planning/milestones/v14.0-ROADMAP.md` + `.planning/milestones/v14.0-REQUIREMENTS.md` + `.planning/milestones/v14.0-MILESTONE-AUDIT.md`).

**v9.0-v14.0 milestone arc closure:** v9.0 kais-movie-pipeline 闭环深化 (P38-43) → v10.0 orchestrator design (P44-51) → v11.0 PoC (P52-56) → v12.0 hardening (P57-61) → v13.0 full rollout (P62-69) → **v14.0 4-track upgrade** (P70-76). v14.0 returns focus to kais-movie-pipeline with production-grade FORM/DUB/IMG/TRANSITION.

**Next milestone:** Not yet planned. v15+ candidate directions wait on (a) DUB-05 A/B benchmark result (CosyVoice variant lock); (b) TRANS-07 LTX-FLF validation report (production rollout gate); (c) v13.0 Phase 64 live-eval data (operator secrets). Run `/gsd:new-milestone` to start.

## Previous Milestone: v13.0 — v10.0 Design Suite Full Rollout & Live Eval ✅ SHIPPED 2026-07-08

**Stats:** 8 phases (62-69) · 17 plans in shipped phases · 20/20 reqs mapped (13 satisfied + 1 audit + 6 operator-handoff) · Tag `v13.0` · Audit `tech_debt`

**Goal:** 把 v11.0 设计套件 + v12.0 hardening 留下的 4 项 scope deferrals 全部落地 —— 12 expert agent YAML 全量 transform(达成 15/15 active expert 覆盖)+ 跑 v12.0 deferred 的 3 个 operator smoke tests + curator self-evolution 从 dry-run 切 live + 新增 operator dashboard 把 round table / agent registry / memory backend 可观测化。**完成后 v10.0-v13.0 四 milestone 弧线收官。**

See `.planning/milestones/v13.0-MILESTONE-AUDIT.md` for the full audit (verdict: tech_debt, 13/20 satisfied + 1 audit + 6 operator-handoff).

## Previous Milestone: v12.0 — Production Hardening ✅ SHIPPED 2026-07-08

**Stats:** 5 phases (57-61) · 9 plans · 53 commits on v12.0-dev · 8/8 reqs ✓ · Tag `v12.0` · Audit `passed`

**Goal:** Fixed 4 hardening gaps exposed by v11.0 real-GLM smoke tests — endpoint routing (long prompts → anthropic-compat), RPM throttling (token bucket + per-round-table TPM budget), auxiliary credential pool isolation (separate keys from main agent + per-key TPM tracking), live-eval infrastructure (mem0 backend adapter + fitness battery real-mode baseline).

See `.planning/milestones/v12.0-MILESTONE-AUDIT.md` for the full audit (status: passed, 8/8 reqs).

## Previous Milestone: v11.0 — Hermes-Native Expert Agents PoC Implementation ✅ SHIPPED 2026-07-07

**Stats:** 5 phases (52-56) · 12 plans · 128 commits · 149 files · 39,256 insertions · 15/15 reqs ✓ · Tag `v11.0` · Audit `passed`

**Goal:** Implemented the v10.0 design suite as runtime code — agent registry + 7 MCP tools + round table state machine + serial executor + 9 sample agent YAMLs + screenplay Step 3 driver + memory conflict arbitration + 7 acceptance criteria.

**Phases:**
- Phase 52: INFRA-FOUNDATION — agent registry + 7 MCP tools + state machine + serial enforcement (4 plans)
- Phase 53: CREATIVE-SLICE — 9 agent YAMLs + Step 3 round table + conflict arbitration (3 plans)
- Phase 54: EVAL-HARNESS-1 — fitness battery + latency SLO + bias canary (3 plans)
- Phase 55: EVAL-HARNESS-2 — compaction + threshold tuning + dry-run-first + schema migration (4 plans)
- Phase 56: VALIDATE — milestone audit + smoke test report (1 plan)

**Code review:** 4 BLOCKER + 6 WARNING fixed in Phase 52 iter 1; 4 BLOCKER + 7 WARNING fixed in Phase 53 iter 1.

**Operator-action handoffs (5):** documented in `.planning/research/v11-poc-eval/smoke-test-report.md §3` — runtime validations of code already verified by 339+ automated tests.

See `.planning/milestones/v11.0-MILESTONE-AUDIT.md` for the full audit (status: passed, 15/15 reqs).

## Previous Milestone: v10.0 — Hermes-Agent 编排架构第一性原理推导(设计型)✅ SHIPPED 2026-07-07

v10.0 SHIPPED + closed 2026-07-07 (tag `v10.0`). v10.0 是**设计型** milestone,零代码改动,产出 7 design docs + 3 schemas + 1 lint script + 1 audit report,作为 v11.0 PoC 的实施蓝本。9/9 reqs satisfied, 8/8 phases verified `passed`,audit status `passed`。

See `.planning/milestones/v10.0-ROADMAP.md` for full archive.

**v9.0 scope (6 phases 38-43):**
- 平台母版切片 (Step 14)
- 配方库 v0 (new plugin plugins/formula_library/)
- 3 新审核门 (redline_emotion_desensitize / redline_no_cold_open / redline_unfinished_ending)
- LTX2.3 预览闭环 (Step 6.5 fast-preview)
- 数据收敛 (Step 15 平台 API → FeedbackStore → formula tuning)
- 集成验证 + close-out

## Previous Milestone: v9.0 — kais-movie-pipeline 闭环深化 ✅ SHIPPED 2026-06-27

(See archived `.planning/milestones/v9.0-ROADMAP.md` for full details.)
6. Dry-run-first invariant (1d)
7. Schema migration dry-run (2d)

**Key constraints:**
- 复用 v10.0 设计,不重新推导 7 决策(cite `00-FIRST-PRINCIPLES.md` §2)
- 强制串行(1 panelist 1 turn `await`)兼容 GLM 4-key rotation
- dry-run-first invariant(curator 默认 dry-run,所有 schema 迁移默认 dry-run)

**Start:** Phase 52(继续 v10.0 Phase 51 后的编号)

---

## Previous Milestone: v10.0 — Hermes-Agent 编排架构第一性原理推导(设计型)✅ SHIPPED 2026-07-07

**Goal:** 借鉴 Kimi 2026-07-06 Notion 架构2.0,结合本 repo 已 ship 的 coding-agent / GSD / curator / mem0,从第一性原理推导 **Hermes-Agent 总调度器 + Hermes-native expert agents + Claude Code 执行场**的三层架构 —— 产出可指导 v11.0 PoC 的设计套件,**不动任何代码**。范式类比 v2.0 PRFP(纯设计 milestone)。

**Stats:** 8 phases (44-51) · 8 plans · 9/9 reqs ✓ · Tag `v10.0` · Design-only (zero code changes) · Audit `passed`

**Target features(7 个设计文档,均放在 `.planning/research/v10-orchestrator-design/`):**

1. **00-FIRST-PRINCIPLES.md** —— 从「编排器需要什么 / agent 身份是什么 / CC 角色边界 / 状态层选型 / 故障恢复 / 多 agent 协作 / 创作内容如何流转」推到最简必要协议集
2. **01-AGENT-REGISTRY-SCHEMA.md + agents-schema.yaml** —— agent YAML schema(persona / tools / refs / memory_scope / lineage)+ 15 个 movie-expert → agent 转化对照表
3. **02-ROUND-TABLE-PROTOCOL.md + round-table-schema.yaml** —— round table 协议(panel / turn_order / max_rounds / early_stop_rule / output_schema)+ 7 个新 MCP tool 契约
4. **03-COMPARISON-VS-KIMI-MCP-SHIM.md** —— T6 vs Kimi 全 MCP 方案对比 + 7 个设计决策的推导记录
5. **04-MIGRATION-PATH.md** —— Python runner 增量迁移计划(B3a:9 个 delegate-only phase 迁 CC,4 个 ComfyUI-calling phase + Step 0/6.5/15 保留 Python)
6. **05-POC-PLAN.md** —— v11.0 PoC 验证计划(目标 / 垂直切片 / 成功标准 / 工作量估算)
7. **06-CROSS-REPO-IMPACT.md** —— hermes-agent repo / kais-hermes-skills repo / `~/.hermes/` 的物理位置分配

**Key context(7 个已锁的设计决策):**

| # | 决策 | 选型 | 理由 |
|---|------|------|------|
| 1 | **协议**(T6) | Hermes MCP server(扩展现有 `mcp_serve.py`)+ tmux dispatch(复用 coding-agent)+ CC native MCP client for callbacks | 复用 4 个已 ship 组件,零自定义 shim,稳定性最高 |
| 2 | **Python runner**(B3a 增量迁移) | delegate-only phase(9 个创意 step)迁 CC;ComfyUI-calling phase(4 个生成 step)+ Step 0/6.5/15 保留 Python runner | 保留 v3-v9 五 milestone 硬化的 ComfyUI 集成 + asset bus + GoalBuilder |
| 3 | **Storyboard-first-class**(D2) | V8.6 编号保留,在 orchestrator 调度层做 round-based parallel(跨场景,不跨 step) | 守住 FOUND-08,真实价值在跨场景并行 |
| 4 | **通用 vs 专属**(G2) | 抽象 pipeline orchestration pattern,kais-movie-pipeline 作为首个 sample | v12+ 扩展 music video / long-form 容易 |
| 5 | **Agent 形态**(α) | YAML + persona prompt + tools + refs + memory_scope + lineage,物理位置 `~/.hermes/agents/{name}.agent.yaml` | 干净的 agent / skill 分层;SKILL 形态作 fallback 保留 |
| 6 | **Agent 记忆** | per-agent scoped memory(扩展 mem0 backend),curator 驱动跨项目自进化 | 满足"agent 随项目越多越有经验"核心诉求 |
| 7 | **CC 角色**((vi) 分层) | Hermes 控 turn_order / max_rounds / schema / early_stop_rule;CC 控 question framing + synthesis | 审计性 + 可重现 + token 成本低 + 充分用 CC 推理能力 |

**关键范式声明(与 Kimi 方案的本质差异):**

- **Kimi 默认**:CC 是 agent 容器 + 执行器(`.claude/agents/*.md` Teammates)
- **v10.0 设计**:Hermes 是 agent 容器(新形态),CC 仅是**场地 + 协调员 + 结构化助手**
- **Agent vs Skill 分层**:不是把现有 SKILL 当 agent 用,也不是把 agent 塞进 CC;agent 是 Hermes-side 独立 YAML 实体,有 per-agent memory + 自进化能力
- **CC 的 Team Lead 配置极薄**:不定义 Expert,只描述 round table 协调员工作流

**Constraints(沿用 + 新增):**

- **范围严格收口:** 仅设计文档,**零代码改动**(不动 SKILL.md / Python / plugin manifest / `mcp_serve.py`)
- **物理位置:** 仅 hermes-agent repo(单 repo 收敛,与 Kai 2026-07-06 决策对齐)
- **类比 v2.0 PRFP:** 同设计型 milestone;v2.0 PRFP 产 18 个文档(340KB),v10.0 预计产 7 个文档(200-300KB)
- **目标读者:** Kai + Kimi(便于 Notion 续聊)+ 未来 v11.0 PoC 实施者
- **输入来源:**
  - Notion "架构2.0" page_id `39511082-af8e-80d7-83b6-e5df50d3f07c`(Kimi 设计)
  - `skills/autonomous-ai-agents/coding-agent/SKILL.md`(本 repo v7.0 ship)
  - `.planning/research/v2-pipeline-design/`(本 repo v2.0 PRFP 设计套件,作为方法论参考)
  - `skills/movie-experts/`(在 kais-hermes-skills repo,作为 agent 转化源)
- **阶段编号:** 继续从 v9.0 phase 43 起 → v10.0 phase 44 起

**Source artifact:** Notion page "架构2.0"(Kimi 2026-07-06 生成,page_id `39511082-af8e-80d7-83b6-e5df50d3f07c`)。

---

## Previous Milestone: v9.0 — kais-movie-pipeline 闭环深化 ✅ SHIPPED 2026-06-27

**Goal:** 把 Notion "创作方向" Tier B+C 落地为 kais-movie-pipeline 的 4 个新能力 —— 平台母版切片 / 配方库 v0 / LTX2.3 预览闭环 / 数据收敛回流 —— 加 3 个跨平台红线审核门,完成「创意→生产→分发→反馈」全闭环。

**Stats:** 6 phases (38-43) · 13 plans · 22/22 reqs satisfied · Tag `v9.0` (anchored at `599ef61a8`)

**Target features shipped:**

1. **平台母版切片 (Step 14, SLICE)** —— 1 master.mp4 → 7 平台 variants(抖音竖屏/横屏、快手、B 站、小红书、视频号、红果)
2. **配方库 v0 (FORM)** —— 新 plugin `plugins/formula_library/` + 10 seed formulas + Step 0 集成
3. **3 新审核门 (GATE)** —— gates.yaml 8→11 additive(redline_emotion_desensitize / redline_no_cold_open / redline_unfinished_ending)
4. **LTX2.3 预览闭环 (PREVIEW, Step 6.5)** —— LTX2.3 default model + 4-state fallback policy + BLOCKING gate escalation
5. **数据收敛 (DATA, Step 15)** —— PlatformMetrics schema + 5 adapter stubs + formula_tuning_loop + JSONL queue + HIL-gated library_writer
6. **集成验证 (VALIDATE)** —— 3 integration flows verified + 30 SKILL.md byte-diff all match `a2a20d2be` + v9.0-MILESTONE-AUDIT.md authored

**Audit:** `.planning/milestones/v9.0-MILESTONE-AUDIT.md` — status: passed (22/22 reqs, 6/6 phases, 3/3 integration flows, FOUND-08 preserved milestone-wide).

**Cross-repo migration (post-v9.0 ship, 2026-06-27):** Commit `f10495332` moved `skills/kais-movie-pipeline/` + `skills/movie-experts/` + 5 plugins (formula_library / kais_aigc / pipeline_state / platform_metrics / review_gates) to 独立 repo `/data/workspace/kais-hermes-skills/`。hermes-agent repo 现仅保留 GSD `.planning/` 工件。

**Operator-action-handoffs (NOT gaps):**
- (a) Phase 41 LTX2.3 live GPU generation testing (V9-FUTURE-02)
- (b) Phase 42 5 平台 API key configuration + live data ingestion (V9-FUTURE-01)

See `.planning/milestones/v9.0-phases/` for archived phase artifacts.

## Next Milestone Goals

v9.0 shipped 后,候选方向:
- feishu-* skills migration (largest v7.0 deferred item)
- Multi-profile mechanism (v7.0 used single SOUL.md)
- v9.0 operator-actionhandoffs 实测 (平台 API key 配置 + live data ingestion)
- 跨 milestone: 全 hermes-agent 周期 v10+ — 待 Kai 决定

## Core Value

每个 movie-expert skill 都能用检索增强的方式调用行业知识库(静态 refs 为主,可选向量 RAG),让 AI 生成的短剧/微电影在专业度上接近人类创作者水平 —— 这是决定短剧生死的核心。

## Requirements

### Validated

<!-- v1 shipped — see .planning/MILESTONES.md for full inventory -->

**v14.0 — shipped 2026-07-10 (milestone tag `v14.0`, verdict `tech_debt` — 24 satisfied + 2 operator-handoff):**

- ✓ **FORM-01** (v14.0): PipelineState.form_factor Literal["landscape","portrait"] field, default portrait (Phase 71)
- ✓ **FORM-02** (v14.0): 15 active movie-expert SKILL.md `## Form Factor Adaptation` sections tiered Tier 1/2/3 (Phase 71)
- ✓ **FORM-03** (v14.0): `references/horizontal-screen-framing.md` landscape twin mirroring vertical (Phase 71)
- ✓ **FORM-04** (v14.0): Step 14 4-cell reframe matrix (16:9↔9:16 both directions) + 20 unit tests green (Phase 71)
- ✓ **FORM-05** (v14.0): MSR_FC=17→41 swept across 5 doc locations + 1 runtime bug in p11_video_render.py:74 (Phase 71)
- ✓ **DUB-01** (v14.0): CosyVoice 2.0-0.5B P10 default via dual-path (gold-team :8002 + ComfyUI AIIA CosyVoice with Fun-CosyVoice3-0.5B) (Phase 72)
- ✓ **DUB-02** (v14.0): `validate_tts_engine_division` standalone function rejects shot with both ltx_native_dialogue AND tts_engine='cosyvoice' (Phase 72)
- ✓ **DUB-03** (v14.0): `validate_voice_clone_ref` helper (3-10s + wav + ≥16kHz + mono) + fail-fast in tts_batch.py (Phase 72)
- ✓ **DUB-04** (v14.0): IndexTTS2 ComfyUI node retained as DEPRECATED fallback with healthcheck-based auto-fallback (Phase 72)
- ✓ **DUB-05** (v14.0 - operator-handoff): `VERSION.json` tts.cosyvoice_default_variant lock site + `cosyvoice-benchmark.md` template (operator runs actual A/B benchmark)
- ✓ **IMG-01** (v14.0): `dreamina_manager.py` orchestrator with asyncio.Semaphore(10) + tenacity AsyncRetrying + sync queue (Phase 73)
- ✓ **IMG-02** (v14.0): asyncio.gather block-on-all in batch_submit (fixes line 619 pitfall — no missing reference images in P11) (Phase 73)
- ✓ **IMG-03** (v14.0): `vision_verify.py` GLM-4.6V gate via task="vision" routing + base64 data URL encoding + sha256 cache 24h TTL + SKILL.md MUST gate + p07 _VISION_VERIFY_INSTRUCTION (Phase 73)
- ✓ **IMG-04** (v14.0): RHD/LHD 3-attempt budget (LHD prompt → stronger + negative → image2image fallback) in dreamina_manager (Phase 73)
- ✓ **IMG-05** (v14.0): `hermes dreamina stats` CLI + `dreamina_stats.py` MetricsBuffer JSONL ring buffer (Phase 73)
- ✓ **IMG-06** (v14.0): `image2image-stratification.md` 1-ref/3-ref/5-ref strata (strength=0.75/0.65/0.55, retry=3/4/5) (Phase 73)
- ✓ **TRANS-01** (v14.0): `transition_schema.py` Pydantic Literal TransitionMethod 12-enum + CameraContinuity 6-enum + frozenset runtime (Phase 74)
- ✓ **TRANS-02** (v14.0): `load_next_shot_link` backward-compat reader coercing legacy string to structured default (no data migration needed — doc-only field) (Phase 74)
- ✓ **TRANS-03** (v14.0): `transition_design.json` first-class asset registered in 3 systems (ASSET_SCHEMA slot 32 + canvas_sync tuple + frontend zod storyboard reuse) (Phase 74)
- ✓ **TRANS-04** (v14.0): Field-level ownership split documented in cinematographer SKILL.md Step 9 + editor SKILL.md Workflow Step 7 + p13_delivery.py (FOUND-08 preserved, NO new transition_designer expert) (Phase 74)
- ✓ **TRANS-05** (v14.0): `references/transition-design.md` 12-type taxonomy with film examples under fair-use (Phase 74)
- ✓ **TRANS-06** (v14.0): `references/transition-engine-routing.md` declarative routing rules (Wan2.2 FLF2V / Hailuo / Vidu / ffmpeg xfade / LTX-2.3 FLF evaluated per-transition — INFRA-04 compliant) (Phase 74)
- ✓ **TRANS-07** (v14.0 - operator-handoff): `ltx-flf-iclora-validation.md` research-scope template (ComfyUI node graph + `<operator fills>` placeholders; operator runs 1-2 reference shots) (Phase 74)
- ✓ **XCUT-01** (v14.0): Phase 70 Lineage Impact Inventory + curator `--live` freeze + cross-repo baseline pins + Phase 76 VALIDATE-CHECKLIST (34 rows) (Phase 70)
- ✓ **XCUT-02** (v14.0): META-RULE X-2 _INJECTION audit pattern — every MUST in SKILL.md has corresponding _INSTRUCTION constant in goal f-string + test asserting keyword in captured["goal"] (Phase 71-74 + Phase 76 meta-rule-x2-audit.sh: 36 MUSTs / 13 _INSTRUCTION / 4/4 goal-tests PASSED)
- ✓ **XCUT-03** (v14.0): Phase 75 Lineage Bump — 15 agent.yaml regenerated (Track A 9 EXPERTS_9 + Track B 6 v13.0 P62) with 75-lineage-assert.sh 15/15 PASSED (Phase 75)
- ✓ **XCUT-04** (v14.0): Operator-action handoffs documented in milestone audit (6 items: DUB-03/05 + IMG-03/XCUT-04c + XCUT-04b + TRANS-07 + carry-forward UAT) (Phase 76)

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

<!-- v14.0 SHIPPED 2026-07-10 — see Validated section above + .planning/milestones/v14.0-* archives. -->
<!-- Next milestone not yet planned. Run /gsd:new-milestone to start. -->

No active requirements. v14.0 milestone closed 2026-07-10.

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

## Previous Milestone: v4.0 — Methodology Backfill ✅ SHIPPED 2026-06-18

**Goal:** 把 2026-06-17 gap-analysis 识别的 3 个 ⭐⭐⭐⭐⭐ AI 化方法论缺口补进 `skills/movie-experts/` —— Snowflake Method(过程)、E-Konte 絵コンテ(视觉中间格式)、SCAMPER(变体引擎),三者互补不重叠。

**Target features:**
- ✅ **Snowflake Method** — 接入 `creative_source` + `screenplay`,填补 Story Kernel → beat sheet 之间的"展开塌陷"(一句话→段落→角色→大纲→场景列表的递进管线)。
- ✅ **E-Konte 絵コンテ** — 接入 `cinematographer`,填补 `storyboard_designer` deprecated 后留下的东方分镜真空(分镜中间格式 + 轴线 + 景别 + 时长 + 表情/动作注记)。
- ✅ **SCAMPER** — 接入 `style_genome` + `hook_retention`,填补 `style_blend` 手动协议的变体引擎缺口(7 动词系统化生成故事/风格变体)。

**Shipped:** 3 phases, 3 plans, 14/14 requirements satisfied (audit PASSED). 1249 lines of new methodology refs + 8 SKILL.md patches across 6 experts + 16 new glossary entries. See `.planning/milestones/v4.0-ROADMAP.md` and `.planning/milestones/v4.0-MILESTONE-AUDIT.md`.

---

## Current State (post-v6.0)

**Last shipped:** v6.0 Self-Evolution & Feedback Loop (2026-06-24) — [Audit](./milestones/v6.0-MILESTONE-AUDIT.md)

## Current Milestone: v7.0 — openclaw → hermes-agent Primary Agent Migration

**Goal:** 把 openclaw 作为主 agent 时的关键能力(skills / agent 定义 / 身份记忆)迁移到 hermes-agent,让 hermes-agent 接管主 agent 角色时保持能力对等。聚焦 personal hermes agent(movie-experts 后续深化在另一 repo kais-movie-agent 处理)。

**Target features:**

1. **Skills 迁移** —— 把 openclaw 独有的 skill 搬到 hermes-agent:
   - `coding-agent`(统一 tmux 委派 Codex/Claude Code/Pi/OpenCode)
   - `tmux-agents`(后台 tmux agent 管理)
   - `feishu-{doc,drive,perm,wiki}`(飞书文档/网盘/权限/知识库)
   - `acp-router`(TBD — 看 ACP 是否还需要保留)
2. **Agent 定义转换** —— 7 份 `openclaw/agents/{main, claude, codex, hermes, hermes-agent, pi, default}.json` 从 openclaw schema 转为 hermes schema,放到 hermes-agent 对应位置
3. **身份与记忆迁移** —— `SOUL.md` + `USER.md` + `workspace/memory/*.md`(25+ 研究笔记)落到 `~/.hermes/`,保留下一步 agent 个性化所需的身份/历史/偏好

**Key context:**

- **范畴拓宽**:v1-v6 都聚焦 movie-experts;v7.0 是项目第一次触及非 movie-experts 范畴。PROJECT.md `## What This Is` 已对应演进
- **Config 显式 out of scope**:provider keys、acp config、feishu channel config 由 Kai 手动处理(不走 milestone 流程)
- **Workspace 项目文件不迁**:`workspace/` 下 GB 级 AIGC 产出与 agent 能力无关,留原处
- **前序 milestone 完整保留**:v1-v6 历史在 PROJECT.md 下文 + MILESTONES.md + milestones/ 完整保留,作为 movie-experts 子系统的归档
- **ACP 路由待定**:acp-router 是否迁移取决于 ACP 协议在 hermes-agent 下是否还需要(openclaw 是 ACP 调度器,hermes-agent 自己是 agent 不是调度器)

**Paradigm:** movie-experts is now a **feedback-driven self-learning system** (transition completed in v6). Skills can evolve based on operator feedback without manual curation. The Hermes runtime gained a feedback/evolution/audit sublayer alongside the existing curator module.

**v6.0 capabilities shipped:**
- Multi-source feedback ingestion: `/feedback` CLI + kais-aigc file watcher + JSONL import (P28)
- Durable FeedbackStore with time-decay + dedup (P29)
- Eval gate (`_eval/gate.py`) with δ=0.3 mean + 1.0 per-prompt regression (P30)
- Knowledge evolution pipeline with non-bypassable human-in-loop (P31)
- Curator extension + EVOL-02 diff generator + sha256-chained audit log (P32)
- Observability (`hermes curator stats`) + canonical architecture doc (P33)

**Hermes-core touch (v5→v6 expansion):** `agent/curator.py` extended with feedback-scan phase (lazy imports preserve runtime isolation). New modules: `agent/feedback_schema.py`, `agent/feedback_ingest.py`, `agent/feedback_store.py`, `agent/feedback_snapshot.py`, `agent/curator_audit.py`, `agent/evolution/{insights,diff_generator,queue,apply,evol02_generator}.py`.

**Next milestone:** Not yet planned. Run `/gsd:new-milestone` to start.

---

## Previous Milestone: v6.0 — Self-Evolution & Feedback Loop ✅ SHIPPED 2026-06-24

**Goal:** 让 movie-experts skill suite 从「静态知识层」进化为「带反馈闭环的自学习系统」—— 专家给出意见后,调用者(含 kais-aigc-platform 审核系统)能反馈结果,反馈驱动 eval-gated 的 SKILL.md / refs 改进。

**Delivered (26/26 requirements satisfied):**

1. ✅ **反馈采集通道 (Feedback Ingestion)** (P28 INGEST-01..05) — 多源接入:CLI `/feedback` + kais-aigc file watcher + 手工 JSONL import;统一 `FeedbackRecord` schema with sha256-tagged `output_snapshot`
2. ✅ **反馈存储 (Feedback Store)** (P29 STORE-01..04) — `FeedbackStore` class with bucketed JSONL, atomic `index.json`, linear time-decay `max(0.1, 1.0 - age/180)`, sha256 dedup + correction semantics
3. ✅ **eval gate** (P30 GATE-01..04) — Extended v1 `_eval/runner.py` with `parse_judge_scores()` numeric extraction + `gate.py` orchestrator (δ=0.3 mean + 1.0 per-prompt regression + stdlib paired-t significance, no scipy)
4. ✅ **反馈→知识库回流 (Knowledge Evolution Pipeline)** (P31 EVOL-01, EVOL-03..05) — LLM aggregation with evidence chains + difflib additive diff + JSONL review queue + atomic `apply_patch_transaction` with FOUND-08 byte-intact + additive-only checks. **Non-bypassable human-in-loop enforced structurally** (AST-walk test guards single-caller invariant)
5. ✅ **Curator 升级 + EVOL-02** (P32 CURATE-01..05, EVOL-02) — `agent/curator.py:run_curator_review` extended with feedback-scan phase (lazy imports preserve runtime isolation). EVOL-02 LLM-driven bilingual diff generator. Tamper-evident sha256-chained audit log. Semi-automatic path for agent-created skills via `_cmd_approve` delegation (Option A preserves P31 invariant)
6. ✅ **可观测性 + close-out** (P33 OBS-01..03) — `hermes curator stats` with rich tables (per-skill dashboard / cross-skill view / source breakdown) + `--json` counts-only flag. Canonical `_shared/v6-feedback-loop-architecture.md`. skills-mapping.yaml `v6_ref_signoffs:`. 4 new bilingual glossary entries

**Key outcomes:**

- **范式跃迁完成**:从 v1-v5 的「人工 curate 静态知识」转为「反馈驱动动态学习」。movie-experts 现在具备 self-improvement 能力
- **Hermes-core scope expansion accepted** (v5→v6):v6 touches Hermes runtime directly (`agent/curator.py` extension + new modules). Pre-v6 curator behavior preserved per SC-6 regression coverage
- **Code review discipline:** 51 findings addressed milestone-wide (16 CR + 35 WR) — every BLOCKER + WARNING fixed or documented
- **FOUND-08 milestone-wide preservation:** zero bundled SKILL.md changes across v6.0 (verified via SC-7 git diff); v4/v5 refs byte-intact (SC-8)

**See:** [Audit report](./milestones/v6.0-MILESTONE-AUDIT.md) · [MILESTONES.md entry](./MILESTONES.md) · Tag `v6.0`

---

## Previous Milestone: v5.0 — kais-movie-agent V8.6 Adaptation ✅ SHIPPED 2026-06-19

**Goal:** Sync hermes-agent's 16 active movie-experts to kais-movie-agent V8.4-V8.6 (13-step pipeline + dreamina CLI + V8.4 expert mapping) so experts stop emitting pre-V8.4 assumptions and align with the consumer-side calling sequence.

**Stats:** 6 phases (P22-P27) · 17 commits · 1-day execution (2026-06-19) · 30/30 requirements satisfied · Audit PASSED

**Trigger source (3 commits same day, 2026-06-18 in kais-movie-agent):**
- `4fb57b4` V8.4 — hermes-agent v2 expert mapping full update (drawer+animator→visual_executor, audio N:1 merge, continuity→continuity_auditor, scene_builder/storyboard_designer→cinematographer, NEW prompt_injector)
- `c22867d` V8.5 — dreamina CLI 取代 jimeng-client + Step 7 角色资产库完整化 (L1 面部锚点 + L2 造型卡片 + L3 姿势包 + L4 表情标定)
- `e41fa68` V8.6 — 管线精简 25→13 步, 审核门 12→8 个, Expert 调用 15→10 次

**Key accomplishments:**

1. **2 new `_shared/` refs** — `dreamina-cli-baseline.md` (330 lines, Phase 22) + `v86-pipeline-mapping.md` (220 lines, Phase 27), both with verified_date: 2026-06 + LICENSE attribution + fair_use_paraphrase status
2. **18 expert SKILL.md body patches** across 16 active experts (Phase 23-26) — each received `## V8.6 Pipeline Sync (Phase XX v5.0)` section documenting V8.6 Step positions + dreamina CLI integration + V8.4 historical context
3. **6 redirect-stub patches** (Phase 25) — voicer/lip_sync/composer/foley/mixer/spatial_audio stubs updated with V8.6 Step position annotations preserving `merged_into` / `folded_into` frontmatter
4. **3 cross-cutting close-out updates** (Phase 27) — README.md corpus tree + skills-mapping.yaml `v5_ref_signoffs:` section + glossary.md 3 new V8.6 term H3 entries (Atomic Step / Review Gate / L1 Identity Anchor)
5. **FOUND-08 preserved milestone-wide** — zero new expert_id directories, zero frontmatter changes across 24 patched files, zero DAG node modifications
6. **v4.0 methodology refs preserved byte-intact** — snowflake-method.md / e-konte-format.md / scamper-variations.md cross-referenced as PRESERVED (not replaced) from new V8.6 sections

**Scope discipline:** Pure knowledge-layer increment. No new expert_id, no DAG node change, no architecture refactor. Mirrors v4.0 scope discipline.

See `.planning/milestones/v5.0-ROADMAP.md` for full phase details, `.planning/milestones/v5.0-REQUIREMENTS.md` for requirement outcomes, and `.planning/milestones/v5.0-MILESTONE-AUDIT.md` for the audit report (status: passed, 30/30 reqs, FOUND-08 preserved).

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
*Last updated: 2026-07-10 — v14.0 milestone SHIPPED (kais-movie-pipeline 4-Track Upgrade FORM/DUB/IMG/TRANSITION; 7 phases 70-76, 17 plans, 26/26 reqs mapped, verdict `tech_debt`, tag `v14.0`). v9.0-v14.0 milestone arc closure complete. SKILL.md L1-L6 read-only invariant exception破例 authorized for v14.0 only; reverts read-only v15+ unless re-authorized. Next milestone not yet planned — v15+ candidate directions wait on DUB-05 A/B benchmark + TRANS-07 LTX-FLF validation + v13.0 Phase 64 live-eval data.*
