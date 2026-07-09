# Milestones

## v14.0 kais-movie-pipeline 4-Track Upgrade (FORM / DUB / IMG / TRANSITION) (Shipped: 2026-07-10)

**Phases shipped:** 7 phases (70-76) · **Plans:** 17 (70:3 + 71:3 + 72:3 + 73:3 + 74:3 + 75:1 + 76:1) · **Requirements:** 26 / 26 mapped (24 satisfied + 2 operator-handoff)
**Tag:** `v14.0`
**Audit:** [`milestones/v14.0-MILESTONE-AUDIT.md`](./milestones/v14.0-MILESTONE-AUDIT.md) — verdict: `tech_debt` (24/26 fully satisfied at code level + 2/26 operator-handoff per XCUT-04 spec)

**One sentence:** 把 kais-movie-pipeline 从「竖屏短剧专用」升级为「横竖双 default 的通用短片创作管线」,同步升级 4 项核心生成环节到 production-grade —— 横竖并行双 default 形态参数化 (FORM) / CosyVoice 2.0-0.5B 配音 + LTX 2.3 native audio 分工 (DUB) / dreamina cli 深度编排 + GLM-4.6V vision-verify 强制门 (IMG) / 创作+数据+生成三层转场协作 (TRANSITION)。**v14.0 是 v9.0 后首个 kais-movie-pipeline-focused milestone,重启跨 repo 工作流** (plan → hermes-agent/.planning/,code → kais-hermes-skills/)。

**Key accomplishments:**

- **P70 FOUNDATION-AUDIT (lineage baseline + freeze):** Lineage Impact Inventory (6 SKILL.md hash + 3 agent.yaml + cross-repo commit pins hermes-agent `8f70fcf7` / kais-hermes-skills `d9620369`), curator `--live` frozen via `config.yaml curator.enabled: false` (code-enforced at `hermes_cli/curator.py:270-272`, blocks even `--live --skip-canary`), Phase 76 VALIDATE-CHECKLIST (34 rows) + 70-smoke.sh (6 XCUT-01 assertions, exits 0). Pre-existing drift on cinematographer + audio_pipeline captured as MISMATCH (Phase 75 closes as side-effect). 3 plans
- **P71 FORM (form_factor parameterization):** `PipelineState.form_factor` Literal["landscape","portrait"] field (default portrait, strict enum via `__post_init__`), `validate_form_factor_invariant`, new `references/horizontal-screen-framing.md` (226-line twin mirroring vertical), MSR_FC=17→41 swept across 5 doc locations + 1 runtime bug in `p11_video_render.py:74`, `--form-factor` LTX template helper, `_FORM_FACTOR_INSTRUCTION` injected into p09 GoalBuilder (XCUT-02 dual injection), 15 canonical active movie-expert SKILL.md `## Form Factor Adaptation` sections tiered Tier 1/2/3 (4/5/6), Step 14 4-cell reframe matrix + 8 sample-frame fixtures + 20 unit tests green. 3 plans
- **P72 DUB (CosyVoice + LTX 2.3 division):** CosyVoice promoted to P10 default via dual-path (gold-team CosyVoice-300M at :8002 + ComfyUI AIIA CosyVoice with Fun-CosyVoice3-0.5B-2512 — RESEARCH-corrected from original filliptm pick which was NOT installed). `validate_tts_engine_division()` standalone function (DUB-02 strict division rule), `validate_voice_clone_ref()` helper (DUB-03), fail-fast in `tts_batch.py`, auto-fallback to IndexTTS2 with DEPRECATED warning (DUB-04), `_TTS_ENGINE_INSTRUCTION` injected into `p10_voice.py` (FIRST p10 _INSTRUCTION — XCUT-02), top-level `VERSION.json` with `tts.cosyvoice_default_variant: null` (DUB-05 operator-action lock site), `cosyvoice-benchmark.md` template, `cosyvoice-deployment.md` dual-path deployment doc. 3 plans
- **P73 IMG (dreamina production-grade orchestration):** `dreamina_manager.py` orchestrator (asyncio.Semaphore(10) + tenacity AsyncRetrying + asyncio.gather block-on-all per IMG-01/IMG-02), `vision_verify.py` GLM-4.6V gate via `task="vision"` routing (CRITICAL CORRECTION — `prefer_vision=True` does NOT exist at `auxiliary_client.py:3015`; base64 data URL encoding; sha256-keyed cache 24h TTL; batched 4-8 images per call), `dreamina_stats.py` MetricsBuffer JSONL ring buffer at `~/.hermes/metrics/dreamina_stats.jsonl` (sync-only — INFRA-04 compliant), RHD/LHD 3-attempt budget + image2image fallback (IMG-04), `image2image-stratification.md` 1-ref/3-ref/5-ref strata (IMG-06), `hermes dreamina stats` CLI registered via `ctx.register_cli_command`, `_VISION_VERIFY_INSTRUCTION` XCUT-02 3-site injection in p07, SKILL.md body patches at kais-movie-pipeline + kais-jimeng-cli. 3 plans
- **P74 TRANSITION (3-layer creative+data+generation):** `transition_schema.py` at plugins/pipeline_state (Pydantic Literal TransitionMethod 12-enum + CameraContinuity 6-enum + `load_next_shot_link` backward-compat reader — TRANS-01/TRANS-02), `transition_design` slot added to ASSET_SCHEMA (slot 32, writer p09 / reader p13) + canvas_sync `_PHASE_OUTPUT_MAP` p09 tuple (TRANS-03), frontend zod reuses storyboard canvas_type (zero frontend change), field-level ownership split documented in cinematographer SKILL.md Step 9 + editor SKILL.md Workflow Step 7 + `p13_delivery.py` (TRANS-04, FOUND-08 preserved, NO new `transition_designer` expert), `transition-design.md` 12-type taxonomy with film examples under fair-use (TRANS-05), `transition-engine-routing.md` declarative routing rules (TRANS-06, INFRA-04 / PITFALL X-5 compliant — declarative constants only, NO runtime LLM), `ltx-flf-iclora-validation.md` research-scope TEMPLATE (TRANS-07), `_TRANSITION_DESIGN_INSTRUCTION` + `_EDITOR_TRANSITION_EXECUTION_INSTRUCTION` (p13 first _INJECTION), `e-konte-format.md` Layer 5 schema extension. 3 plans
- **P75 LINEAGE-BUMP (15 agent.yaml regeneration):** 15 agent.yaml lineage blocks regenerated (Track A 9 EXPERTS_9 via `transform_skill_to_agent.py` + Track B 6 v13.0 P62 via targeted lineage-field YAML edit, persona byte-preserved). `75-lineage-assert.sh` 15/15 PASSED (sha256 LF-norm UTF-8 equality). `75-LINEAGE-BUMP-REPORT.md` (136 lines). Pre-existing drift on cinematographer + audio_pipeline (P70 MISMATCH) closed as side-effect. Curator `--live` freeze lifted as final action (`config.yaml curator.enabled: false → true`, FROZEN comment replaced with release citation per ROADMAP SC#4). 1 plan
- **P76 VALIDATE (META-RULE audit + close-out):** `76-meta-rule-x2-audit.sh` (3-phase audit: 36 MUSTs / 13 _INSTRUCTION constants / 4/4 goal-tests PASSED, exits 0), `76-ANCESTRY-ASSERT.md` (both repos descendants of P70 baselines — hermes-agent `4e7c58cc9` descendant of `8f70fcf7`, kais-hermes-skills `ba58c254` descendant of `d9620369`, both exit 0), `v14.0-MILESTONE-AUDIT.md` (424 lines, 9 sections, verdict `tech_debt`), tag `v14.0` placed. All 26 reqs reconciled (24 satisfied + 2 operator-handoff DUB-05/TRANS-07). 1 plan

**Operator-action-handoffs (6, per XCUT-04 spec — NOT gaps):**

- Phase 72 DUB-05 A/B benchmark: CosyVoice 2.0-0.5B vs Fun-CosyVoice 3.0 on 3-5 reference dialogue lines; default variant + rationale locked in `VERSION.json`.
- Phase 72 DUB-03 voice_clone_reference_wav: operator-sourced per-character 3-10s reference audio samples.
- Phase 73 IMG-03 / XCUT-04c vision-verify API cost: GLM-4.6V batch calls at production scale (~213-shot × 5 refs ≈ 1065 images / 6 per batch ≈ 178 calls).
- Phase 74 XCUT-04b Hailuo/Vidu API keys: opt-in for cloud Chinese-content transition engines per TRANS-06.
- Phase 74 TRANS-07 LTX-FLF+ICLoRA validation report: operator runs 1-2 reference shots; gates TRANS-11 v15+ production rollout.
- Phase 71 / Phase 74 manual UAT: horizontal-screen-framing.md citation fair-use review + Tier 1 transition-design.md content substance review (carry-forward).

**v9.0-v14.0 milestone arc closure:** v9.0 kais-movie-pipeline 闭环深化 (P38-43) → v10.0 orchestrator design (P44-51) → v11.0 PoC (P52-56) → v12.0 hardening (P57-61) → v13.0 full rollout (P62-69) → **v14.0 4-track upgrade** (P70-76). v14.0 returns focus to kais-movie-pipeline with production-grade FORM/DUB/IMG/TRANSITION. SKILL.md L1-L6 read-only invariant exception破例 authorized for v14.0 only; v15+ reverts to read-only unless explicitly re-authorized.

**Cross-repo topology (reactivated from v9.0):** hermes-agent repo = GSD `.planning/` 工件; kais-hermes-skills repo = SKILL.md + refs + Python + ComfyUI workflow. Final cross-repo pins: hermes-agent `4e7c58cc9cac3c4925770beaf5a9433369094a24`, kais-hermes-skills `ba58c2548ab82f0cd9acd7cc7af14402137f8520`.

**Hard constraints preserved:**

- INFRA-04 serial execution NOT lifted (all IMG/TRANSITION code paths sync-only or declarative; zero `asyncio.gather` for GLM-coupled code)
- EVAL-06 dry-run-first NOT changed (curator `--live` frozen for v14.0 duration, released only post-Phase-75 bump)
- FOUND-08 15-expert set frozen (TRANS-04 field-level ownership split; zero new expert_id)
- SKILL.md L1-L6 read-only invariant exception破例 authorized for v14.0 only (lineage regeneration mandatory per XCUT-03; reverts read-only v15+ unless re-authorized)

See `.planning/milestones/v14.0-ROADMAP.md` for full archive + `.planning/milestones/v14.0-REQUIREMENTS.md` for archived requirements with traceability.

---

## v13.0 v10.0 Design Suite Full Rollout & Live Eval (Shipped: 2026-07-08)

**Phases shipped:** 8 phases (62-69) · **Plans:** 17 (in shipped phases — 62:4 + 63:4 + 65:3 + 67:4 + 68:2) · **Requirements:** 20 / 20 mapped (13 satisfied + 1 audit + 6 operator-handoff)
**Tag:** `v13.0`
**Audit:** [`milestones/v13.0-MILESTONE-AUDIT.md`](./milestones/v13.0-MILESTONE-AUDIT.md) — verdict: `tech_debt` (13/20 fully satisfied + 1 audit + 6 operator-handoff per VALIDATE-01 spec)

**One sentence:** 把 v11.0 设计套件 + v12.0 hardening 留下的 4 项 scope deferrals 全部落地 —— 12 expert agent YAML 全量 transform(达成 15/15 active expert 覆盖,21 total agents)+ curator self-evolution live-tick 安全护栏(opt-in `--live` flag + bias canary pre-check + audit log)+ 3 维 observability surface(agent registry + round table + memory backend)wired 到 FastAPI endpoint + CLI + dashboard panel。

**Key accomplishments:**

- **P62 EXPERT-YAML-TRANSFORM (12 → 21 agents):** 12 个 active expert SKILL.md → `~/.hermes/agents/{name}.agent.yaml` 全量 transform per v10.0 `04-MIGRATION-PATH.md §2` 75-cell table。15/15 active expert coverage achieved。全部 byte-pass `jsonschema.Draft202012Validator.validate()`。Lineage fields populated(source_sha + transform_rule_id + transform_timestamp)。4 plans
- **P63 EXPERT-REGISTRY-INTEGRATION (21-agent load + smoke):** Agent registry 启动时加载 21 agents 无 schema/lifecycle 错误。REQUIRED_DAG_EXPERTS frozenset + `_check_required_experts` sibling wired(preserves existing signature)。Missing-expert 告警 fires for known-absent expert_id。`visual_executor` round table smoke produces non-empty synthesis(mock-mode authoritative,live GLM operator-deferred)。4 plans
- **P65 CURATOR-LIVE-GUARDS (live-tick safety scaffolding):** `hermes curator evolve --live` opt-in flag(默认仍 dry-run per EVAL-06)。Pre-tick bias canary catches ≥ 4/5 known-bad records per v12.0 EVAL-03 baseline。Post-tick audit log emits sha256-tagged memory writes with timestamp(supports operator 24h review + manual rollback)。3 plans
- **P67 OBSERVABILITY-BACKEND (3 metrics collectors):** `agent/observability/` package(MetricsBuffer ring buffer + `agent_registry_metrics.py` + `round_table_metrics.py` + `memory_backend_metrics.py`)。All 4 grey areas resolved(G1 in-memory ring buffer · G2 pull model · G3 count-based window · G4 per-round-table summary)。INFRA-04 serial constraint preserved(sync `@contextmanager` only,zero `asyncio.gather`)。FastAPI `/orchestrator/agents/status` endpoint auth-gated。4 plans
- **P68 OBSERVABILITY-PRESENTATION (CLI + dashboard):** `hermes orchestrator status` CLI(3 rich tables + `--json` flag)。`/orchestrator` dashboard panel(auth-gated,client-side fetch + 30s auto-refresh)。Both surfaces consume same metrics source(no drift)。16/16 tests green。2 plans
- **P69 VALIDATE (audit + close-out):** `.planning/milestones/v13.0-MILESTONE-AUDIT.md` authored。Verdict `tech_debt`(13/20 satisfied + 1 audit + 6 operator-handoff)。5/5 cross-phase integration links verified WIRED end-to-end in live codebase

**Operator-action-handoffs (6, deferred per VALIDATE-01 spec):**

- Phase 64 LIVE-EVAL-EXEC (4 reqs EVAL-01..04): 3 operator smoke tests(GLM latency + mem0 p95 + fitness battery real-mode)+ report aggregation. Needs `GLM_API_KEY`, `MEM0_API_KEY`, `GLM_AUX_API_KEY_1..4`.
- Phase 66 CURATOR-LIVE-TICK (2 reqs CURATE-04/05): 1st actual live tick + runbook. Operator decision pending on live memory mutation risk.
- 3 manual UAT deferrals from Phases 62/63/67(non-blocking,mock/TestClient authoritative).

**v10.0-v13.0 milestone arc closure:** v10.0 design suite(8 phases,9 reqs,zero code)→ v11.0 PoC implementation(5 phases,15 reqs,vertical slice)→ v12.0 production hardening(5 phases,8 reqs,4 hardening gaps closed)→ v13.0 full rollout(8 phases,20 reqs,15/15 active expert coverage + observability surface + curator live guards). The four-milestone arc is now structurally complete. v14+ decisions wait on v13 Phase 64 live-eval data.

**Cross-repo invariant preserved:** kais-hermes-skills repo SKILL.md read-only(Lineage invariants L1-L6 from Phase 48-49 preserved)v13.0 transforms SKILL.md → agent YAML at `~/.hermes/agents/` without modifying source.

**Hard constraints preserved:**

- INFRA-04 serial execution NOT lifted(Phase 67 collectors sync only)
- EVAL-06 dry-run-first NOT changed(Phase 65 `--live` opt-in, default dry-run)
- SKILL.md read-only invariant L1-L6(Phase 48-49)

See `.planning/milestones/v13.0-ROADMAP.md` for full archive + `.planning/milestones/v13.0-REQUIREMENTS.md` for archived requirements with traceability.

---

## v9.0 kais-movie-pipeline 闭环深化 (Shipped: 2026-06-27)

**Phases completed:** 6 phases (38-43) · **Plans:** 13 · **Requirements:** 22 / 22 ✓
**Tag:** `v9.0` (anchored at `599ef61a8` — Phase 43 SUMMARY commit)
**Audit:** [`milestones/v9.0-MILESTONE-AUDIT.md`](./milestones/v9.0-MILESTONE-AUDIT.md) — status: passed (22/22 reqs, 6/6 phases, 3/3 integration flows, FOUND-08 preserved milestone-wide)

**One sentence:** 把 Notion "创作方向" Tier B+C 落地为 kais-movie-pipeline 的 4 个新能力 —— 平台母版切片 / 配方库 v0 / LTX2.3 预览闭环 / 数据收敛回流 —— 加 3 个跨平台红线审核门,完成「创意→生产→分发→反馈」全闭环。

**Key accomplishments:**

- **P38 SLICE (Step 14 平台母版切片):** 1 master.mp4 → 7 平台 variants(抖音竖屏/横屏、快手、B 站、小红书、视频号、红果);`platform-master-slicing.md` (346 行) + SKILL.md Step 14 body + `variants[]` schema in asset-bus-schema.md
- **P39 FORM (配方库 v0):** 新 plugin `plugins/formula_library/` + 10 seed formulas + Step 0 + theory_critic formula_reference。49 tests GREEN
- **P40 GATE (3 新审核门):** redline_emotion_desensitize / redline_no_cold_open / redline_unfinished_ending 注册到 gates.yaml (8→11 additive)。145 tests GREEN。V8.6 8-gate structure byte-for-byte preserved
- **P41 PREVIEW (Step 6.5 LTX2.3 预览闭环):** `ltx2-preview-loop.md` (321 行) + SKILL.md Step 6.5 + pipeline-dag.md annotation。4-state fallback policy rides existing BLOCKING-mode Gate。LTX2.3 selected as default ($0.10/clip)
- **P42 DATA (Step 15 数据收敛):** PlatformMetrics schema + 5 adapter stubs + formula_tuning_loop + JSONL queue + HIL-gated library_writer + CLI + `data-convergence.md`。107 tests GREEN
- **P43 VALIDATE (集成验证 + close-out):** 3 integration flows verified (SLICE→DATA / FORM→GATE / PREVIEW→Step 6)。30 SKILL.md frontmatter byte-diff all match `a2a20d2be`。`v9.0-MILESTONE-AUDIT.md` (10 sections) authored。301 tests GREEN final evidence

**Cross-repo migration (post-v9.0 ship, 2026-06-27):** Commit `f10495332` moved `skills/kais-movie-pipeline/` + `skills/movie-experts/` + 4 plugins (formula_library / kais_aigc / pipeline_state / platform_metrics / review_gates) to独立 repo `/data/workspace/kais-hermes-skills/`。hermes-agent repo 现仅保留 GSD `.planning/` 工件;v9.0 实际代码产物在 kais-hermes-skills repo。

**Operator-action-handoffs (NOT gaps, per scoped-boundary design):**

- (a) Phase 41 LTX2.3 live GPU generation testing (V9-FUTURE-02)
- (b) Phase 42 5 平台 API key configuration + live data ingestion (V9-FUTURE-01)

---

## v7.0 openclaw → hermes-agent Primary Agent Migration (Shipped: 2026-06-25)

**Phases completed:** 4 phases (34-37) · **Plans:** 7 · **Requirements:** 14 / 14 ✓
**Tag:** `v7.0`
**Audit:** [`v7.0-MILESTONE-AUDIT.md`](./v7.0-MILESTONE-AUDIT.md) — status: passed (14/14 reqs structurally satisfied, 8/8 integration points verified)
**Migration report:** [`milestones/v7.0-MIGRATION-REPORT.md`](./milestones/v7.0-MIGRATION-REPORT.md) — canonical close-out (207 lines, 6 sections)

**Paradigm shift:** v7.0 transitions hermes-agent from "movie-experts subsystem owner" to "Kai's primary agent". First milestone touching non-movie-experts scope — project category broadens from "movie-experts subsystem" to "personal hermes agent platform".

**Key accomplishments:**

- **Skills Migration (P34):** `coding-agent` (4 delegation targets: Codex/Claude Code/Pi/OpenCode) + `tmux-agents` (4 operations: spawn/list/attach/get-results) migrated to `skills/autonomous-ai-agents/`. SUPPLEMENT coexistence decision — bidirectional `related_skills` graph wired across all 6 autonomous-ai-agents skills. COEXISTENCE.md documents the partition.
- **SOUL.md Identity Enhancement (P35):** Non-destructive integration of openclaw AIGC routing rules into `~/.hermes/SOUL.md`. Original 513B Hermes Nous-Research identity preserved byte-for-byte at file head; openclaw rules added under tagged H2 header. 4 routing categories (immediate/cognitive/expert-management/default) adapted from regex+MCP notation to natural-language skill-discovery + mem0 + curator references. 9× source tags + 10× date tags.
- **Memory Ingestion (P36):** USER.md migrated to `~/.hermes/memories/` with openclaw-origin frontmatter. Idempotent batch_ingest.py (SHA-256 content-hash keyed) + spot_check.py (5 topic queries) built under `plugins/memory/mem0/scripts/`. Live ingestion deferred to operator (MEM0_API_KEY not configured at ship time) — commands documented in INGESTION-NOTE.md.
- **Validation & Report (P37):** Structural benchmark validates both skills + SOUL routing + canonical `.planning/milestones/v7.0-MIGRATION-REPORT.md` (207 lines, 6 H2 sections, 5 Explicitly Skipped categories with rationale, 14 reqs in traceability).

**Project scope broadening:** v1-v6 focused on `skills/movie-experts/`; v7.0 is the project's first milestone outside that scope. PROJECT.md `## What This Is` evolved to "Kai's personal Hermes Agent platform" (first non-movie-experts milestone).

**Operator-action-handoffs (NOT gaps):** 4 runtime smoke-tests deferred to operator per migration-milestone scoped-boundary design — MEM0_API_KEY config + live mem0 ingestion + SOUL routing observation + skill invocation smoke-test. All documented in v7.0-MIGRATION-REPORT.md §Operator Action Items with exact commands.

**File count correction:** ROADMAP/REQUIREMENTS stated 133 memory files / 1.3MB; verified reality is **124 files / 817KB**. Corrected in `36-01-INGESTION-NOTE.md` and v7.0-MIGRATION-REPORT.md.

**Known deferred items at close:** 4 operator-action smoke-tests + 1 pre-existing quick_task (unrelated to v7.0, carried from prior milestone). See STATE.md §Deferred Items.

---

## v6.0 Self-Evolution & Feedback Loop (Shipped: 2026-06-24)

**Phases completed:** 6 phases (28-33) · **Plans:** 13 · **Requirements:** 26 / 26 ✓
**Tag:** `v6.0`
**Audit:** [`v6.0-MILESTONE-AUDIT.md`](./milestones/v6.0-MILESTONE-AUDIT.md) — status: passed (26/26 reqs, 6/6 phases, 5/5 E2E flows, FOUND-08 preserved milestone-wide)

**Paradigm shift:** v6 transitions movie-experts from "static knowledge layer" (v1-v5) to "feedback-driven self-learning system." First milestone where skills can evolve based on operator feedback without manual curation.

**Key accomplishments:**

- **Multi-source feedback ingestion** (P28 INGEST): Operator CLI `/feedback`, kais-aigc-platform file exchange watcher, manual JSONL batch import — all emit unified `FeedbackRecord` Pydantic schema with sha256-tagged `output_snapshot`.
- **Durable feedback store** (P29 STORE): `FeedbackStore` class with bucketed JSONL persistence, atomic `index.json` single source of truth, linear time-decay `max(0.1, 1.0 - age/180)`, sha256 dedup + correction semantics (older superseded on verdict change).
- **Eval gate** (P30 GATE): Extended v1 `_eval/runner.py` with `parse_judge_scores()` numeric extraction (load-bearing — v1 discarded them), `gate.py` orchestrator with mean δ=0.3 + per-prompt 1.0 regression + stdlib paired-t significance (no scipy).
- **Knowledge evolution pipeline** (P31 EVOL): LLM aggregation with evidence chains, difflib-based additive diff generator, JSONL review queue, atomic `apply_patch_transaction` with FOUND-08 byte-intact + additive-only checks. **Non-bypassable human-in-loop enforced structurally** — `apply_patch_transaction` has exactly ONE caller (`_cmd_approve`); AST-walk test guards invariant.
- **Curator upgrade + audit** (P32 CURATE + EVOL-02): `agent/curator.py:run_curator_review` extended with feedback-scan phase (lazy imports preserve runtime isolation). EVOL-02 LLM-driven bilingual diff generator. Tamper-evident sha256-chained audit log at `~/.hermes/skills/.audit/log.jsonl`. Semi-automatic path for agent-created skills via `_cmd_approve` delegation (Option A preserves P31 invariant).
- **Observability + close-out** (P33 OBS): `hermes curator stats` with rich tables (per-skill dashboard, cross-skill view, source breakdown) + `--json` counts-only flag. Canonical `_shared/v6-feedback-loop-architecture.md` (305 lines, mirrors v86 pattern). skills-mapping.yaml `v6_ref_signoffs:`. 4 new bilingual glossary entries.

**Hermes-core scope expansion (v5→v6):** v6 touches Hermes runtime directly (`agent/curator.py` extension + new feedback/evolution/curator_audit modules). Pre-v6 curator behavior preserved per SC-6 regression coverage (additive extension only).

**Code review discipline:** 51 findings addressed across the milestone (16 CR + 35 WR) — every BLOCKER + WARNING fixed or documented.

**Known deferred items at close:** 3 (see STATE.md) — pre-existing v3.0 quick_task + P28 live-REPL UAT + P28 verification gap. All non-blocking; documented for future operator UAT.

---

---

## v5.0 kais-movie-agent V8.6 Adaptation (Shipped: 2026-06-19)

**Phases completed:** 6 phases (22-27) · **Requirements:** 30 / 30 ✓ · **Commits:** 17
**Tag:** `v5.0`
**Source artifact:** kais-movie-agent V8.4-V8.6 SKILL.md (commits `4fb57b4` + `c22867d` + `e41fa68`, all 2026-06-18)
**Audit:** [`v5.0-MILESTONE-AUDIT.md`](./milestones/v5.0-MILESTONE-AUDIT.md) — status: passed (30/30 reqs, 6/6 phases, FOUND-08 preserved milestone-wide)

**One sentence:** Sync hermes-agent's 16 active movie-experts to kais-movie-agent V8.4-V8.6 (13-step pipeline + dreamina CLI + V8.4 expert mapping) —— 纯知识层增量(2 新 `_shared/` refs + 18 expert SKILL.md body patches + 6 redirect-stub patches + 3 cross-cutting file updates),不引入新 expert_id、不动 DAG 节点、不重构核心架构,v4.0 方法论 refs 全部 PRESERVED 不替换。

**Key accomplishments:**

1. **Phase 22 — dreamina CLI 知识基线:** 新增 `_shared/dreamina-cli-baseline.md` (330 行) + `_shared/LICENSE.md`,文档化 V8.5 dreamina CLI 6 sub-commands + L1-L4 角色资产库策略 + async poll pattern + gold-team fallback + jimeng-client 废弃通知
2. **Phase 23 — 视觉系 V8.6 sync:** 6 expert SKILL.md body patches(visual_executor + prompt_injector + character_designer + cinematographer + colorist + style_genome)
3. **Phase 24 — 文学系 V8.6 sync:** 4 expert SKILL.md patches(hook_retention + creative_source + screenplay + script_auditor),覆盖 V8.6 atomic operations(Step 1 / 2 / 3 / 6)
4. **Phase 25 — 听觉系 V8.6 sync:** 1 主 patch(audio_pipeline)+ 6 redirect-stub patches,含 dreamina CLI `multimodal2video @Audio N` 绑定语法
5. **Phase 26 — 审核系 V8.6 sync:** 4 expert SKILL.md patches(continuity_auditor + compliance_gate + editor + theory_critic),文档化 V8.6 8-gate 审核门结构(down from 12)
6. **Phase 27 — 集成 close-out:** 新增 `_shared/v86-pipeline-mapping.md` (220 行) canonical 13-Step mapping + skills-mapping.yaml `v5_ref_signoffs:` section + README + glossary 3 new H3 entries

**Shipped artifacts:**

- **2 new `_shared/` refs** (~550 lines total): `dreamina-cli-baseline.md` (330) + `v86-pipeline-mapping.md` (220)
- **18 expert SKILL.md body patches** across 16 active experts(Phase 23-26)
- **6 redirect-stub SKILL.md patches**(Phase 25,所有 v3.0 merge/fold predecessors)
- **3 cross-cutting close-out updates**(Phase 27): README + skills-mapping.yaml + glossary
- **v5.0-MILESTONE-AUDIT.md** (status: passed, 30/30 reqs, FOUND-08 preserved)

**Cross-phase integration(verified by autonomous-orchestrator):**

- **V8.6 Pipeline Sync cross-reference network:** 15-row per-expert table in `v86-pipeline-mapping.md` bidirectionally links all active experts' V8.6 sections
- **FOUND-08 milestone-wide preservation:** zero new expert_id dirs, zero frontmatter changes across 24 patched files, v3.0/v4.0 byte-intact
- **License integrity:** both v5.0 refs `fair_use_paraphrase`, signed_off_by: phase-27-doc-02

**Known tech debt at close(non-blocking):**

- **FUTURE-10:** Live-run validation of dreamina CLI integration prompts against actual V8.6 pipeline run (deferred to operator — requires kais-movie-agent end-to-end execution)
- **FUTURE-11:** Cross-repo automated drift detection between kais-movie-agent V-number and hermes-agent internal knowledge (tooling not yet built)
- **FUTURE-12:** Vogler / Truby / 设计思维 / Story Grid / 起承转合 methodology expansion (defer to v6.0+ per v4.0 gap-analysis §6)
- **Quick task 260617-wgz:** status "missing" SUMMARY — pre-existing condition from v4.0 close(non-blocking,separate audit-open item)

See `.planning/milestones/v5.0-ROADMAP.md` for full phase details and `.planning/milestones/v5.0-REQUIREMENTS.md` for requirement outcomes.

---

## v4.0 — Methodology Backfill (Shipped: 2026-06-18)

**Phases completed:** 3 phases (19-21) · **Plans:** 3 · **Requirements:** 14 / 14 ✓
**Tag:** `v4.0`
**Source artifact:** [`.planning/research/methodology-gap-analysis-2026-06-17.md`](./research/methodology-gap-analysis-2026-06-17.md)(quick task 260617-wgz 产物)
**Audit:** [`v4.0-MILESTONE-AUDIT.md`](./milestones/v4.0-MILESTONE-AUDIT.md) — status: passed(14/14 reqs, 7/7 integration, 3/3 E2E flows, 4/4 FOUND-08)

**One sentence:** 把 2026-06-17 gap-analysis 识别的 3 个 ⭐⭐⭐⭐⭐ AI 化方法论缺口(Snowflake Method / E-Konte 絵コンテ / SCAMPER)增量挂载到 `creative_source+screenplay` / `cinematographer+visual_executor` / `style_genome+hook_retention` —— 不引入新 expert_id、不动 DAG 节点、不重构核心架构,纯知识层增量(1249 行新 refs + 8 SKILL.md patches + 16 glossary 词条)。

### Key accomplishments

- **Phase 19 — Snowflake Method Integration:** 新增 `creative_source/references/snowflake-method.md`(279 行)挂载 Ingermanson 10 步递进管线,填补 StoryKernel → Snyder 15-beat 之间的"展开塌陷"。Patched `creative_source/SKILL.md`(+45 行,新增 SnowflakeArtifacts output schema + Workflow steps 12-13)+ `screenplay/SKILL.md`(+20 行,Beat Planning 前新增 step 1.5 "Consume Snowflake-4 一页大纲" + 字段映射表)+ `_shared/glossary.md`(+52 行,4 词条)。StoryKernel→Snowflake→Snyder 全链路字段对齐。
- **Phase 20 — E-Konte Integration:** 新增 `cinematographer/references/e-konte-format.md`(371 行)挂载日本动画工业 5 层分镜格式(场景布局 / 镜头角度运动 / 角色位置表情动作 / 对白音效 / 时间帧数),与现有西方 Mascelli 8-level + 180°/30° 轴线**互补不替代**。Patched `cinematographer/SKILL.md`(+27 行,composition_lock 下新增 H2 "E-Konte as Intermediate Format")+ `visual_executor/SKILL.md`(+47 行,drawer 消费 Layer 1+3 / animator 消费 Layer 2+5)+ `_shared/glossary.md`(+41 行,4 词条)+ LICENSE.md attribution。兑现 Phase 17 storyboard_designer deprecated promise(E-Konte 折叠进 cinematographer,**不复活** storyboard_designer)。
- **Phase 21 — SCAMPER Variation Engine + DOC Close-out:** 新增 `style_genome/references/scamper-variations.md`(599 行)挂载 Bob Eberle SCAMPER 7 动词变体引擎,生成 35 个短剧变体配方(7 动词 × 5 genre×mood×pacing×cast×runtime 组合)。Patched `style_genome/SKILL.md`(+43 行,style_blend 上叠加 SCAMPER Variation Layer,显式声明**叠加不替代** auteur-theory)+ `hook_retention/SKILL.md`(+44 行,SCAMPER × 5 爆款公式 cross-table = 35 hook variant seeds)+ `_shared/glossary.md`(+67 行,8 词条)+ `README.md`(+35 行,corpus tree 列出 3 个新 refs)+ `.planning/research/v2-pipeline-design/skills-mapping.yaml`(+50 行,新增 v4_ref_signoffs section 3 entries)。

### Shipped artifacts

- **3 new methodology refs**(1249 lines total):`snowflake-method.md` (279) + `e-konte-format.md` (371) + `scamper-variations.md` (599)
- **8 SKILL.md body patches** across 6 experts(creative_source / screenplay / cinematographer / visual_executor / style_genome / hook_retention)
- **16 new glossary entries**(4 Snowflake + 4 E-Konte + 8 SCAMPER,中英对照 + 出处标注)
- **Updated corpus tree** in `skills/movie-experts/README.md`(Mermaid DAG 不变 —— 3 refs 都是已有 expert 内部 ref)
- **v4_ref_signoffs** section in `skills-mapping.yaml`(3 entries with verified_date / source / license_status: fair_use_paraphrase)
- **3 new refs LICENSE.md attribution rows**(creative_source / cinematographer / style_genome 各 +1)

### Cross-phase integration(verified by gsd-integration-checker)

- **Flow A — Snowflake narrative pipeline:** creative_source StoryKernel → Snowflake Step 1-4 → snowflake_artifacts.json → screenplay step 1.5 Consume → Snyder 15-beat validation(3 anchor points ±5%)→ Beat Planning。Fallback: 低质量 kernel 走 direct structural_formula → Beat Planning。
- **Flow B — E-Konte visual pipeline:** cinematographer composition_lock → 5-layer annotation → e_konte.json(dual-output with shot_intent.json)→ visual_executor drawer (L1+3) + animator (L2+5)→ editor 消费 shot_intent.json for axis compliance。Fallback: Western storyboard when e_konte absent。
- **Flow C — SCAMPER variation pipeline:** style_genome auteur + genre + cross-cultural → SCAMPER 7-verb expansion → scamper_variants.json(7 candidates with novelty/feasibility/alignment scores)→ hook_retention 7×5 cross-table(35 seeds)→ Hook Design Workflow。

### FOUND-08 backward-compat honored

- All 6 patched experts retain original `expert_id` + `related_skills`(byte-identical)
- No new expert directories created
- No deprecated experts revived(storyboard_designer / scene_builder / performer 仍 deprecated)
- E-Konte folded into existing cinematographer.composition_lock —— 兑现 Phase 17 promise

### Known tech debt at close(non-blocking)

- Snowflake trigger conditions expanded from 1 to 3 OR-conditions during execution(documented in 19-01-SUMMARY.md deviations)
- E-Konte trigger conditions expanded from 2 to 6-row table during execution(documented in 20-01-SUMMARY.md deviations)
- scamper-variations.md reached 599 lines vs 300-450 target —— 非阻塞 over-delivery,覆盖更彻底
- Live-run statistical validation of SCAMPER 7 候选 quality deferred to operator —— v4.0 close 不要求

See `.planning/milestones/v4.0-ROADMAP.md` for full phase details and `.planning/milestones/v4.0-REQUIREMENTS.md` for requirement outcomes.

---

## v1 — Movie-Experts Suite v2 (Shipped: 2026-06-15)

**Phases completed:** 7 phases (0-6) · **Plans:** 15 · **Tasks:** 25
**Tag:** `v1`
**Known deferred items at close:** 6 (see [STATE.md § Deferred Items](./STATE.md#deferred-items))

**One sentence:** RAG-augmented 18-expert movie-making skill suite (14 refactored + 4 new) covering 短剧 / 微电影 creation end-to-end, with MT-Bench position-swap eval harness and operator-deferred live statistical run.

### Key accomplishments

- **Phase 0 — Audit + Eval Skeleton:** Stripped 5 phantom refs (`wan22_video`, "168K controlled tokens", FLUX 1.x samplers, AudioLDM-2, CosyVoice) from existing 14 SKILL.md files. Built byte-exact snapshot tool (sha256 + git sha + ISO 8601) + MT-Bench position-swap eval harness (`runner.py` 616 lines, `judge_prompt.md` 4-dimension rubric, 3-condition ablation template). Captured 14 pre-refactor baselines as the eval anchor.
- **Phase 1 — EXPERT-COMPLI (Legal Gate):** Built `compliance_marketing` expert end-to-end — 5 refs (cn-content-rules covering 网信办 AI 标识办法 2025-09-01 + AI 漫剧 备案 regime 2026-04-01 + 3 platform specs 抖音/快手/小程序剧 + 8-category 红线 + 5-type 爆款 taxonomy) + bilingual SKILL.md + 5 eval prompts. Wired bidirectionally into 4 existing experts.
- **Phase 2 — EXPERT-HOOK (Commercial Engine):** Built `hook_retention` expert — 4 refs (`three-second-hooks`, `conflict-escalation`, `paywall-design` with 卡点 density + 3-tier 🟢🟡🔴 strength, `vertical-pacing` with multi-platform variation) + SKILL.md + 5 eval prompts.
- **Phase 3 — Top-4 RAG:** Deep-refactored screenplay / editor / colorist / style_genome with 5 curated refs each (20 total refs, ~400KB). Ran 36-verdict dry-run producing `_eval/reports/phase3-ablation-dryrun.md` + `_eval/reports/phase3-go-nogo.md` (CONDITIONAL GO — deferred to Phase 6 live run for statistical evidence).
- **Phase 4 — EXPERT-CINE (Camera Language):** Built `cinematographer` expert — boundary doc vs scene_builder / animator / editor authored BEFORE SKILL.md to prevent scope creep. 4 refs (shot-grammar, axis-rules, vertical-screen-framing, camera-motion-catalog) + SKILL.md + 3 prompts + 7 peer related_skills updates.
- **Phase 5 — Remaining 10 + EXPERT-PROD (v1.5):** Built `production` expert (AI-relevant subset only per PROD-07 — character LoRA spec, wardrobe, lighting intent, GPU budget, asset reuse; NOT live-action). 5 refs + SKILL.md + 3 prompts + 8 peer edges. Light-uplifted remaining 10 existing experts (2 refs each = 20 total). Carried forward all Phase 0 phantom strips.
- **Phase 6 — Full Eval + Bilingual + README:** Published top-level `skills/movie-experts/README.md` documenting 18-expert collaboration DAG + RAG usage guide (static refs / memory plugin / provider-agnostic) + Phase 6 live-run procedure (6-step operator runbook) + bilingual consistency section + file layout tree. Live run deferred to operator (requires `OPENROUTER_API_KEY` + budget).

### Shipped artifacts

- 18 expert directories under `skills/movie-experts/` (14 original refactored + 4 new)
- 58 markdown refs (~1.2MB cited fair-use content), all with LICENSE.md + `Last-verified: 2026-06-15` stamps
- `_eval/` harness: `runner.py`, `snapshot.py`, `judge_prompt.md`, `config.yaml.example`, 9 prompt files, `baseline/` × 14, `reports/` × 40+
- `_shared/`: `glossary.md` (EN↔CN), `known-external-models.yaml` (33-entry allowlist), `platform-comparison.md`, `RAG-INVOCATION-PATTERN.md`, `SKILL-LAYOUT.md`
- Top-level `README.md` (297 lines, 20KB)

### Known gaps at close

- Phase 6 UAT not executed (10 checkpoints paused at user redirect — see `06-UAT.md`)
- Phase 1 VERIFICATION `human_needed` — CN legal content + platform-spec thresholds + judge prompt quality + glossary completeness all require human/expert review
- Live-run statistical GO/NO-GO deferred to operator per CONTEXT D-11 (budget decision)

See `.planning/milestones/v1-ROADMAP.md` for full phase details and `.planning/milestones/v1-REQUIREMENTS.md` for requirement outcomes.

---

---

## v2.0 PRFP — Pipeline Redesign from First Principles (Shipped: 2026-06-16)

**Phases completed:** 6 phases (7-12) · **Plans:** N/A (design-only milestone)
**Tag:** `v2.0-prfp-design` (no code shipped — design suite only)
**Design artifacts:** `.planning/research/v2-pipeline-design/` (10 design docs + 4 YAML schemas + validation script)

**One sentence:** First-principles redesign of the movie-experts pipeline producing canonical DAG topology + per-node specs + corpus traceability + LLM-creative-distillation + cross-repo handoff plan + governance — design-only milestone, no skill code changes.

---

## v3.0 — Skills-to-DAG Alignment (Shipped: 2026-06-17)

**Phases completed:** 6 phases (13-18) · **Plans:** 16 · **Commits:** 67
**Tag:** `v3.0` (pending operator push)
**Stats:** 137 files changed · 19007 insertions · 2137 deletions · 1-day execution window
**Audit status:** tech_debt (12/12 requirements satisfied, 4 non-blocking WARNINGs) — see [v3.0-MILESTONE-AUDIT.md](./v3.0-MILESTONE-AUDIT.md)
**Known deferred items at close:** 6 (W-1, W-2, W-3, W-4, VALIDATE-D1, FUTURE-09) — see audit report

**One sentence:** Aligned v1 14-expert skill suite + v2 PRFP design to the canonical v2.0 PRFP DAG topology via 2 renames + 2 merges + 1 new + 3 deprecations — 13 legacy expert_id migrations preserved via FOUND-08 backward-compat aliases.

### Key accomplishments

- **Phase 13 — Expert Rename + Alias Scaffolding:** Renamed `continuity` → `continuity_auditor` and `compliance_marketing` → `compliance_gate` with `metadata.hermes.aliases` preservation (FOUND-08). 27 consumer related_skills rewired bidirectionally. skills-mapping.yaml sign_off_status flipped to signed_off for both renamed entries.
- **Phase 14 — Visual Executor Merge:** Merged `drawer` + `animator` into unified `visual_executor` with `sub_steps: [drawer, animator]` declaration. 15 consumer edges collapsed to single deduplicated entry. Refs organized under `references/{drawer,animator}/` sub-folders.
- **Phase 15 — Audio Pipeline Merge:** Merged 5 audio experts (`voicer` + `lip_sync` + `composer` + `foley` + `mixer` + `spatial_audio`) into unified `audio_pipeline` with `sub_steps: [voicer, lip_sync, composer, foley, mixer, spatial_audio]`. spatial_audio FOLDED as 6th sub-step (D-1 decision — preserves HRTF/Atmos content; uses `status: folded_into` distinct from `merged_into`). 11 consumer edges collapsed.
- **Phase 16 — New AI-Native Expert (prompt_injector):** Created brand-new `prompt_injector` expert (no v1 predecessor) per Phase 8 §2.7 + nodes.yaml. 4 refs (prompt-engineering-patterns, cross-call-consistency, token-budget-management, model-specific-prompt-templates). Bidirectional edges to creative_source + cinematographer + visual_executor + audio_pipeline.
- **Phase 17 — Deprecate 3 Experts:** Marked `performer` / `scene_builder` / `storyboard_designer` as `status: deprecated` with `inheritance_targets` and `deprecated_reason`. 9 consumer body annotations added. FOUND-08 preserved — original expert_id + body content intact for backward compatibility.
- **Phase 18 — Validation + Documentation:** Produced VALIDATION-REPORT.md reconciling 31 SKILL.md files into 4 buckets (15 active DAG + 3 active non-DAG + 3 deprecated + 10 redirect stubs). README.md ASCII DAG replaced with canonical Mermaid from 01-NODE-DAG.md §1.5. 5 glossary terms verified/added. known-external-models.yaml Phase 8 §2.17 dated annex (27 entries with verified_date: 2026-06-17). All 19 skills-mapping.yaml entries signed_off.

### Shipped artifacts

- 5 new expert directories: continuity_auditor, compliance_gate, visual_executor, audio_pipeline, prompt_injector
- 13 redirect/deprecated stubs preserving v1 expert_ids (10 redirect + 3 deprecated)
- 1 new prompt_injector expert with 4 refs + LICENSE + GAP-REPORT
- Updated README.md with Mermaid DAG + 4-bucket inventory classification
- Updated glossary.md (5 new H3 entries)
- Updated known-external-models.yaml (73 entries, 27 verified_date stamps, Phase 8 §2.17 annex)
- VALIDATION-REPORT.md (canonical milestone-close audit artifact)

### Known gaps at close

- **W-1:** creative_source → topic_curator dead reference (pre-existing v2.0, narrow phase scope)
- **W-2:** character_designer missing Phase 17 inheritance body annotation
- **W-3:** 32 pre-existing v2.0 bidirectional asymmetries (post-v3.0 normalization candidacy)
- **W-4:** Frontmatter `status:` field path inconsistency (documentation drift in per-phase verification reports)
- **VALIDATE-D1:** quality_gate gap — canonical 16th DAG node has no SKILL.md directory
- **FUTURE-09:** production expert (currently `disposition: deferred` in skills-mapping.yaml)

---

*Last updated: 2026-06-17 — v3.0 archived, awaiting next milestone decision*
