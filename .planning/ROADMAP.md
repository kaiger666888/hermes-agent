# Roadmap: Hermes Agent — Kai's Personal Agent Platform

## Milestones

| Version | Name | Phases | Shipped | Tag | Audit |
|---------|------|--------|---------|-----|-------|
| v1 | Movie-Experts Suite v2 | 0-6 | 2026-06-15 | `v1` | passed (deferred live run) |
| v2.0 | PRFP Pipeline Design (design-only) | 7-12 | 2026-06-16 | `v2.0-prfp-design` | design-only |
| v3.0 | Skills-to-DAG Alignment | 13-18 | 2026-06-17 | `v3.0` | tech_debt |
| v4.0 | Methodology Backfill | 19-21 | 2026-06-18 | `v4.0` | passed |
| v5.0 | kais-movie-agent V8.6 Adaptation | 22-27 | 2026-06-19 | `v5.0` | passed |
| v6.0 | Self-Evolution Feedback Loop | 28-33 | 2026-06-24 | `v6.0` | passed |
| v7.0 | openclaw → hermes Migration | 34-37 | 2026-06-25 | `v7.0` | passed |
| v9.0 | kais-movie-pipeline 闭环深化 | 38-43 | 2026-06-27 | `v9.0` | passed |
| v10.0 | 编排架构第一性原理推导(设计型) | 44-51 | 2026-07-07 | `v10.0` | passed (zero code) |
| v11.0 | Hermes-Native Expert Agents PoC | 52-56 | 2026-07-07 | `v11.0` | passed |
| v12.0 | Production Hardening | 57-61 | 2026-07-08 | `v12.0` | passed |
| v13.0 | v10.0 Design Suite Full Rollout & Live Eval | 62-69 | 2026-07-08 | `v13.0` | tech_debt |
| **v14.0** | **kais-movie-pipeline 4-Track Upgrade (FORM / DUB / IMG / TRANSITION)** | **70-76** | **2026-07-10** | **`v14.0`** | **tech_debt (24 satisfied + 2 operator-handoff)** |

See [MILESTONES.md](./MILESTONES.md) for full milestone history with key accomplishments per milestone, and `milestones/v{N}.0-ROADMAP.md` for archived phase artifacts.

---

## Most Recent Milestone: v14.0 ✅ SHIPPED 2026-07-10

**Stats:** 7 phases (70-76) · 17 plans · 36 tasks · 26/26 reqs mapped (24 satisfied + 2 operator-handoff) · Tag `v14.0` · Audit `tech_debt`

**One sentence:** 把 kais-movie-pipeline 从「竖屏短剧专用」升级为「横竖双 default 的通用短片创作管线」,同步升级 4 项核心生成环节到 production-grade (横竖并行双 default 形态参数化 / CosyVoice 2.0-0.5B 配音 + LTX 2.3 native audio 分工 / dreamina cli 深度编排 + GLM-4.6V vision-verify 强制门 / 创作+数据+生成三层转场协作)。v14.0 是 v9.0 后首个 kais-movie-pipeline-focused milestone,重启跨 repo 工作流 (plan → hermes-agent/.planning/,code → kais-hermes-skills/)。

**Phase summary:**

| Phase | Name | Status | Completed |
|-------|------|--------|-----------|
| 70 | FOUNDATION-AUDIT | SHIPPED (3 plans) | 2026-07-09 |
| 71 | FORM | SHIPPED (3 plans) | 2026-07-09 |
| 72 | DUB | SHIPPED (3 plans) | 2026-07-09 |
| 73 | IMG | SHIPPED (3 plans) | 2026-07-09 |
| 74 | TRANSITION | SHIPPED (3 plans) | 2026-07-09 |
| 75 | LINEAGE-BUMP | SHIPPED (1 plan) | 2026-07-10 |
| 76 | VALIDATE | SHIPPED (1 plan + audit + tag) | 2026-07-10 |

**Cross-repo topology:** hermes-agent = GSD planning; kais-hermes-skills = SKILL.md + refs + code. Final pins: hermes-agent `4e7c58cc9`, kais-hermes-skills `ba58c254` (both descendants of P70 baselines, exit 0 on `git merge-base --is-ancestor`).

**Hard constraints preserved:**

- INFRA-04 serial execution NOT lifted (zero asyncio.gather for GLM-coupled code paths)
- EVAL-06 dry-run-first NOT changed (curator `--live` frozen for v14.0 duration, released post-Phase-75)
- FOUND-08 15-expert set frozen (TRANS-04 field-level ownership split, zero new expert_id)
- SKILL.md L1-L6 read-only invariant exception破例 authorized for v14.0 only (lineage regeneration mandatory per XCUT-03)

<details>
<summary>v14.0 Phase Details (click to expand)</summary>

### Phase 70: FOUNDATION-AUDIT

**Goal**: Enumerate every SKILL.md to be touched with current lineage baseline BEFORE any edits land, freeze curator `--live` for milestone duration, capture cross-repo commit pins so Phase 76 VALIDATE can assert ancestry post-bump.
**Depends on**: Nothing (first v14.0 phase)
**Requirements**: XCUT-01
**Plans** (3):
- [x] 70-01-PLAN.md — Lineage Impact Inventory (6 SKILL.md + 3 agent.yaml + cross-repo pins)
- [x] 70-02-PLAN.md — Curator freeze (config.yaml) + STATE.md v14.0.freeze block
- [x] 70-03-PLAN.md — Phase 76 VALIDATE-CHECKLIST (34 rows) + 70-smoke.sh (6 XCUT-01 assertions)

### Phase 71: FORM

**Goal**: Pipeline `form_factor` parameterization enabling横竖并行双 default — every expert emits form-aware creative rules instead of hardcoded 9:16 assumptions.
**Depends on**: Phase 70 (lineage impact inventory must be the authoritative edit-list)
**Requirements**: FORM-01, FORM-02, FORM-03, FORM-04, FORM-05
**Plans** (3):
- [x] 71-01-PLAN.md — FORM Foundation (PipelineState.form_factor schema + horizontal-screen-framing.md ref + MSR_FC=17→41 sweep + LTX template helper + _FORM_FACTOR_INSTRUCTION injection)
- [x] 71-02-PLAN.md — 15 SKILL.md Form Factor Adaptation patches tiered Tier 1/2/3 (4/5/6)
- [x] 71-03-PLAN.md — Step 14 4-cell reframe matrix + 20 unit tests + 8 sample-frame fixtures

### Phase 72: DUB

**Goal**: CosyVoice 2.0-0.5B as P10 default (replacing IndexTTS2) with strict schema-enforced division rule preventing CosyVoice overlay + LTX 2.3 native audio on the same shot, benchmark-locked default variant recorded in `VERSION.json`.
**Depends on**: Phase 70 + Phase 71; parallel with Phase 73
**Requirements**: DUB-01, DUB-02, DUB-03, DUB-04, DUB-05
**Plans** (3):
- [x] 72-01-PLAN.md — DUB Foundation (validate_tts_engine_division + voice_clone_reference_wav schema + validate_voice_clone_ref + tts_batch routing + DEPRECATED fallback)
- [x] 72-02-PLAN.md — ComfyUI AIIA CosyVoice workflow JSON + probe-tts-routing.sh healthcheck + auto-fallback + SKILL.md IndexTTS2 DEPRECATED demotion + _TTS_ENGINE_INJECTION into p10 (FIRST p10 _INSTRUCTION)
- [x] 72-03-PLAN.md — cosyvoice-deployment.md dual-path + VERSION.json + cosyvoice-benchmark.md template + 72-smoke.sh (11 assertions)

### Phase 73: IMG

**Goal**: dreamina batch image generation through production-grade orchestrator with retry + concurrency cap + sync queue semantics, GLM-4.6V vision-verify mandatory gate, RHD/LHD systematic mitigation, SLA dashboard.
**Depends on**: Phase 70 + Phase 71; parallel with Phase 72
**Requirements**: IMG-01, IMG-02, IMG-03, IMG-04, IMG-05, IMG-06
**Plans** (3):
- [x] 73-01-PLAN.md — IMG Foundation (dreamina_manager.py + vision_verify.py GLM-4.6V gate + dreamina_stats.py MetricsBuffer + 10 unit tests)
- [x] 73-02-PLAN.md — RHD/LHD 3-attempt budget + image2image-stratification.md + `hermes dreamina stats` CLI + _VISION_VERIFY_INSTRUCTION XCUT-02 injection in p07 + SKILL.md patches
- [x] 73-03-PLAN.md — IMG validation layer (e2e integration tests + XCUT-02 goal-content test + 73-smoke.sh 15 assertions)

### Phase 74: TRANSITION

**Goal**: Structured transition designs as first-class pipeline assets with creative intent (cinematographer Step 9) cleanly separated from post-production execution (editor Step 13), per-transition engine routing evaluated across multiple engines.
**Depends on**: Phase 70 + Phase 71 + Phase 73 (FLF2V match-cut reuses IMG vision-verify precedent)
**Requirements**: TRANS-01, TRANS-02, TRANS-03, TRANS-04, TRANS-05, TRANS-06, TRANS-07
**Plans** (3):
- [x] 74-01-PLAN.md — TRANSITION Foundation (transition_schema.py TRANS-01/02 + asset_bus slot + canvas_sync TRANS-03 + 12 tests)
- [x] 74-02-PLAN.md — SKILL.md Ownership + Routing Refs + XCUT-02 Injection (TRANS-04/05/06 + _TRANSITION_DESIGN_INSTRUCTION + _EDITOR_TRANSITION_EXECUTION_INSTRUCTION + e-konte Layer 5)
- [x] 74-03-PLAN.md — LTX-FLF Validation + Smoke (TRANS-07 research-scope template + XCUT-02 goal-content test + 74-smoke.sh 17 assertions)

### Phase 75: LINEAGE-BUMP

**Goal**: 15 affected agent YAMLs at `~/.hermes/agents/` regenerated via v13.0 P62 transform flow with refreshed `source_sha` matching `sha256(SKILL.md)` of final v14.0 source. Curator `--live` freeze lifted as final action.
**Depends on**: Phase 74 (TRANSITION final — must be the last SKILL.md-touching phase)
**Requirements**: XCUT-03
**Plans** (1):
- [x] 75-01-PLAN.md — LINEAGE-BUMP Execution (Track A 9 EXPERTS_9 via transform_skill_to_agent.py + Track B 6 v13.0 P62 manual lineage update + 75-lineage-assert.sh 15/15 PASSED + 75-LINEAGE-BUMP-REPORT.md + curator freeze release as final action)

### Phase 76: VALIDATE

**Goal**: Cross-cutting audit closes v14.0 with verified lineage coverage, META-RULE X-2 _INSTRUCTION injection audit, cross-repo commit pin ancestry assertion, hard-constraint preservation, documented operator-action handoffs, and the milestone audit doc + tag.
**Depends on**: Phase 75 (strictly LAST — mirror v10.0 P51 / v11.0 P56 / v12.0 P61 / v13.0 P69 pattern)
**Requirements**: XCUT-02, XCUT-04
**Plans** (1):
- [x] 76-01-PLAN.md — VALIDATE Execution (76-meta-rule-x2-audit.sh XCUT-02 + ancestry assertion SC#2 + v14.0-MILESTONE-AUDIT.md + tag v14.0)

**Critical path:** 70 → 71 → (72 ∥ 73) → 74 → 75 → 76. Phase 76 strictly LAST.

</details>

---

## Backlog

Candidate directions for v15+ (not yet committed — pending milestone planning):

- **DUB-05 A/B benchmark result** (v14.0 operator-handoff): CosyVoice 2.0-0.5B vs Fun-CosyVoice 3.0 — locks default variant in `VERSION.json`. Gates v15 voice work direction.
- **TRANS-07 LTX-FLF validation report** (v14.0 operator-handoff): LTX-2.3 FLF + ICLoRA combined workflow — gates TRANS-11 v15+ production rollout.
- **v13.0 Phase 64 live-eval data** (v13.0 carryforward): 3 operator smoke tests (GLM latency + mem0 p95 + fitness battery real-mode) — drives v15+ physical partition / async concurrency / 15-expert production tuning decisions.
- **v13.0 Phase 66 CURATOR-LIVE-TICK** (v13.0 carryforward): 1st actual live tick + runbook — operator decision pending on live memory mutation risk.
- **FORM-06 / FORM-07 / DUB-06 / DUB-07 / IMG-07 / IMG-08 / IMG-09 / TRANS-08 / TRANS-09 / TRANS-10 / TRANS-11 / XCUT-05** (v14.0 Future Requirements, all explicitly acknowledged as deferred).
- **feishu-* skills migration** (v7.0 carryforward): largest v7.0 deferred item, not yet planned.

---

*Last updated: 2026-07-10 — v14.0 SHIPPED (4-Track Upgrade; 7 phases, 17 plans, 26/26 reqs mapped, verdict `tech_debt`, tag `v14.0`). v9.0-v14.0 milestone arc closure complete. Next milestone not yet planned.*
