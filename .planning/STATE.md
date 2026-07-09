---
gsd_state_version: 1.0
milestone: v14.0
milestone_name: kais-movie-pipeline 形态/音频/图像/转场 4 项升级
status: planning
last_updated: "2026-07-09T04:03:28.574Z"
last_activity: 2026-07-09
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# State: Hermes Agent — Kai's Personal Agent Platform

## Project Reference

**Project code:** MESV2 (historical; v7.0+ broadens scope beyond movie-experts)
**Name:** Hermes Agent — Kai's Personal Agent Platform
**Core value:** 让 hermes-agent 成为 Kai 的主 agent:既承载 movie-experts 这样的领域专家子系统(v1-v6 已 shipped),也具备通用 agent 必备的代码委派、自动化集成、文档协作、个人身份与记忆能力(v7.0 迁移目标)。v10.0 推导 Hermes 总调度器 + Hermes-native expert agents + CC 执行场的三层编排架构。v11.0 实施垂直切片,v12.0 硬化生产缺口。**v13.0 SHIPPED — v10.0-v13.0 四 milestone 架构弧线收官。**
**Key docs:** `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/MILESTONES.md`, `.planning/milestones/v13.0-ROADMAP.md`(THE archived milestone), `.planning/milestones/v13.0-REQUIREMENTS.md`, `.planning/milestones/v13.0-MILESTONE-AUDIT.md`, `.planning/research/v10-orchestrator-design/04-MIGRATION-PATH.md`(THE 12-expert transform rules §2)
**Mode:** yolo (auto-advance, parallelization on)
**Granularity:** standard
**Model profile:** quality
**Current focus:** Milestone archived — awaiting `/gsd:new-milestone` for v14.0

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-07-09 — Milestone v14.0 started

### Progress

```
v1 movie-experts:                  [██████████] 100% (Phases 0-6, shipped 2026-06-15)
v2.0 PRFP design:                  [██████████] 100% (Phases 7-12, shipped 2026-06-16)
v3.0 Skills-to-DAG:                [██████████] 100% (Phases 13-18, shipped 2026-06-17)
v4.0 Methodology Backfill:         [██████████] 100% (Phases 19-21, shipped 2026-06-18)
v5.0 V8.6 Adaptation:              [██████████] 100% (Phases 22-27, shipped 2026-06-19)
v6.0 Self-Evolution Feedback:      [██████████] 100% (Phases 28-33, shipped 2026-06-24)
v7.0 openclaw → hermes Migration:  [██████████] 100% (Phases 34-37, shipped 2026-06-25)
v9.0 kais-movie-pipeline 闭环深化:  [██████████] 100% (Phases 38-43, shipped 2026-06-27)
v10.0 编排架构设计(设计型):         [██████████] 100% (Phases 44-51, shipped 2026-07-07, tag v10.0)
v11.0 Expert Agents PoC:           [██████████] 100% (Phases 52-56, shipped 2026-07-07, tag v11.0)
v12.0 Production Hardening:        [██████████] 100% (Phases 57-61, shipped 2026-07-08, tag v12.0)
v13.0 Design Suite Full Rollout:   [██████████] 100% (Phases 62-69, shipped 2026-07-08, tag v13.0, verdict: tech_debt)
```

**v13.0 milestone status:** ARCHIVED — 5/8 phases fully shipped + verified (62, 63, 65, 67, 68); 2/8 deferred as operator-handoff (64 LIVE-EVAL-EXEC needs secrets; 66 CURATOR-LIVE-TICK needs operator decision); 1/8 audit (69 VALIDATE). Verdict `tech_debt` (13/20 satisfied + 1 audit + 6 operator-handoff). 17/17 plans in shipped phases complete. Tag `v13.0` placed. Phases archived to `.planning/milestones/v13.0-ROADMAP.md` + `.planning/milestones/v13.0-REQUIREMENTS.md`. REQUIREMENTS.md deleted (next milestone starts fresh).

### Phase Statuses (v13.0)

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 62 | EXPERT-YAML-TRANSFORM | SHIPPED ✓ 2026-07-08 | 12 new agent YAMLs at `~/.hermes/agents/` (21 total). 15/15 active expert coverage. 4 plans. |
| 63 | EXPERT-REGISTRY-INTEGRATION | SHIPPED ✓ 2026-07-08 | 21-agent registry load + missing-expert alarm + visual_executor round table smoke (mock-mode). 4 plans. |
| 64 | LIVE-EVAL-EXEC | DEFERRED (operator-handoff) | EVAL-01..04 needs GLM/mem0 secrets (`GLM_API_KEY`, `MEM0_API_KEY`, `GLM_AUX_API_KEY_1..4`). |
| 65 | CURATOR-LIVE-GUARDS | SHIPPED ✓ 2026-07-08 | `hermes curator evolve --live` opt-in flag + bias canary (4/5 catch) + audit tick_mode. 3 plans. |
| 66 | CURATOR-LIVE-TICK | DEFERRED (operator-handoff) | CURATE-04/05 deferred per operator decision on live memory mutation risk. |
| 67 | OBSERVABILITY-BACKEND | SHIPPED ✓ 2026-07-08 | 3 metrics collectors + FastAPI `/orchestrator/agents/status` endpoint (auth-gated). 4 plans. |
| 68 | OBSERVABILITY-PRESENTATION | SHIPPED ✓ 2026-07-08 | `hermes orchestrator status` CLI + `/orchestrator` dashboard panel. 2 plans. |
| 69 | VALIDATE | SHIPPED ✓ 2026-07-08 | Audit verdict `tech_debt`. 13/20 satisfied + 1 audit + 6 operator-handoff. |

### Critical Path

```
Phase 62 (EXPERT-TRANSFORM) ──▶ Phase 63 (EXPERT-REGISTRY) ──────────────┐
                                                                          │
Phase 64 (LIVE-EVAL-EXEC)  ─── parallel, operator-secrets-bound ──────────┤
                                                                          │
Phase 65 (CURATOR-GUARDS)  ──▶ Phase 66 (CURATOR-LIVE-TICK) ──────────────┤
                                                                          │
Phase 67 (OBSRV-BACKEND)   ──▶ Phase 68 (OBSRV-PRESENTATION) ─────────────┤
                                                                          │
                                          ALL OTHER PHASES COMPLETE ──▶ Phase 69 (VALIDATE)
                                                                            strictly LAST
```

**Hard constraints preserved (carry-forward to v14+):**

- INFRA-04 serial execution NOT lifted (GLM capacity gate — v14+ decision, deferred pending v13 Phase 64 live data)
- EVAL-06 dry-run-first NOT changed (CURATE-01 only adds opt-in `--live` flag)
- SKILL.md in kais-hermes-skills repo stays read-only (EXPERT-01..03 transform without modifying source; lineage invariants L1-L6 preserved)
- Operator secrets needed for EVAL-01..03 — Phase 64 deferred as operator-handoff per VALIDATE-01 spec

## Performance Metrics (v13.0)

- v13.0 phases total: 8 (Phases 62-69, continuing from v12.0 phase 61)
- v13.0 phases shipped: 6 (62, 63, 65, 67, 68, 69 — 5 code-work + 1 audit)
- v13.0 phases deferred (operator-handoff): 2 (64, 66)
- v13.0 requirements total: 20 (EXPERT-01..05 + EVAL-01..04 + CURATE-01..05 + OBSRV-01..05 + VALIDATE-01)
- v13.0 requirements fully satisfied: 13/20
- v13.0 requirements satisfied by audit doc: 1/20 (VALIDATE-01)
- v13.0 requirements operator-handoff: 6/20 (EVAL-01..04 + CURATE-04/05)
- v13.0 plans in shipped phases: 17/17 complete (62:4 + 63:4 + 65:3 + 67:4 + 68:2 = 17)
- v13.0 audit verdict: `tech_debt`
- v13.0 tag: `v13.0` placed 2026-07-08

## Decisions (v13.0 — milestone archived)

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 8 phases continuing from v12.0 phase 61 (62-69) | Sequential phase numbering; v12.0 ended at P61. | Applied 2026-07-08 |
| Phase clustering by track + SC-count splits | Each phase delivers one coherent capability. EXPERT split 62+63; CURATE split 65+66; OBSRV split 67+68. | Applied 2026-07-08 |
| Phase 69 (VALIDATE) strictly LAST | Cross-20-req audit + close-out (mirror v10.0 P51 / v11.0 P56 / v12.0 P61 pattern). | Applied 2026-07-08 |
| Phase 64 (LIVE-EVAL-EXEC) operator-secrets parallel track | 3 smoke tests need `GLM_API_KEY`, `MEM0_API_KEY`, `GLM_AUX_API_KEY_1..4`. Phase deferred as operator-handoff per VALIDATE-01 spec. | Applied 2026-07-08 |
| **Hard constraint: INFRA-04 serial execution NOT lifted** | Cites MEMORY.md `feedback-glm-overload-reduce-concurrency.md`. Phase 67 collectors use sync `@contextmanager` only. | Preserved 2026-07-08 |
| **Hard constraint: EVAL-06 dry-run-first NOT changed** | Curator default `dry_run: true` preserved. CURATE-01 only adds opt-in `--live` flag. | Preserved 2026-07-08 |
| **Hard constraint: SKILL.md in kais-hermes-skills repo read-only** | Lineage invariants L1-L6 (Phase 48-49). EXPERT-01..03 transform without modifying source. | Preserved 2026-07-08 |
| Phase 64 + Phase 66 deferred as operator-handoff per VALIDATE-01 spec | Operator secrets / live memory mutation risk — VALIDATE-01 spec allows operator-handoff close-out (mirror v11.0 P56 + v12.0 P61 pattern). | Applied 2026-07-08 |

### Decisions (carried forward to v14+ — relevant to next milestone)

| Decision | Rationale | Why relevant to v14+ |
|----------|-----------|----------------------|
| v10.0 design suite as canonical implementation blueprint | 7 design docs + 3 schemas + 1 lint script shipped 2026-07-07. v11.0 implemented, v12.0 hardened, v13.0 rolled out full scope. | All v14+ decisions cite v10.0 docs (e.g., OQ-12 mem0 p95 threshold → physical-partition decision; 02-ROUND-TABLE-PROTOCOL.md §5 → async concurrency decision). |
| v11.0 PoC implementation + v12.0 hardening + v13.0 rollout as production baseline | Agent registry + 7 MCP tools + state machine + serial executor + 21 agents + endpoint routing + RPM throttling + aux pool + observability all shipped. | v14+ builds on top of this baseline (async lift, physical partition, 15-expert production tuning). |
| v13 Phase 64 EVAL-01..04 produces v14 decision feed | Live GLM latency + mem0 p95 + fitness battery data drive v14 decisions (physical partition trigger / async concurrency trigger / 15-expert tuning targets). | Phase 64 operator-handoff MUST complete before v14 milestone planning is informed. |

## Accumulated Context

### v13.0 Goal Restatement (achievement: YES with operator-handoff deferrals)

把 v11.0 设计套件 + v12.0 hardening 留下的 4 项 scope deferrals 全部落地:

1. **EXPERT-COMPLETION** — DONE — 12 active expert agent YAML 全量 transform(达成 15/15 active expert 覆盖,9 已 ship + 12 新增 = 21 total)
2. **LIVE-EVAL-EXEC** — INFRA READY, OPERATOR-HANDOFF — 3 operator smoke tests need GLM/mem0 secrets; Phase 64 deferred per VALIDATE-01 spec
3. **CURATOR-LIVE** — GUARDS DONE, LIVE-TICK HANDOFF — `--live` flag + bias canary + audit log shipped (Phase 65); 1st actual live tick deferred (Phase 66)
4. **OBSERVABILITY** — DONE — 3 collectors + FastAPI endpoint + CLI + dashboard panel shipped (Phase 67 + 68)

**完成后 v10.0-v13.0 四 milestone 弧线收官。** v14+ 决策(物理分区 / 异步并发 / 15-expert production tuning)由 v13 Phase 64 live-eval 数据驱动。

**关键范式声明(沿用 v10.0-v12.0):**

- **Hermes 是 agent 容器**(新形态 YAML),有 per-agent memory + 自进化能力;CC 仅是场地 + 协调员 + 结构化助手
- Agent vs Skill 分层:agent 是 Hermes-side 独立 YAML 实体;SKILL 作 fallback 保留(`default_invocation: skill_fallback`)
- v13.0 在 v11.0/v12.0 runtime 之上做 rollout + observability,不重新推导 v10.0 设计决策

### Blockers / Risks (v13.0 — residual at close)

| Risk | Likelihood | Impact | Mitigation Status |
|------|-----------|--------|-------------------|
| **Operator secrets unavailable for Phase 64 (LIVE-EVAL-EXEC)** | MEDIUM | LOW (Phase 64 deferred as operator-handoff per VALIDATE-01 spec; does not block v14 milestone planning) | Phase 64 SCs explicitly allow operator-action handoff per VALIDATE-01 spec (mirror v12.0 pattern). Code-work tracks (62-63, 65-68) proceeded independently and shipped. |
| **Curator 1st live tick deferred pending operator decision on live memory mutation risk** | LOW | LOW (Phase 65 guards shipped — bias canary + opt-in `--live` + audit log all in place; Phase 66 will run once operator approves) | Phase 65 SC#2 bias canary catches ≥ 4/5 known-bad records pre-tick. Phase 66 SC#1 captures before/after diff for operator 24h review + manual rollback (CURATE-03 audit log supports this). |
| **mem0 p95 ≥ 500ms triggers v14 物理分区 evaluation prematurely** | LOW | LOW (this is the intended v14 decision feed, not a v13 blocker) | Phase 64 EVAL-02 produces decision feed; v14 physical-partition evaluation is a separate milestone. v13 scope explicitly excludes physical partition. |

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260626-rq4 | flood-aware `_send_with_retry` (parse retry_after, clamp [3,60]s, default 5s) | 2026-06-26 | dda0e6c1a | [260626-rq4-flood-aware-send-retry](./quick/260626-rq4-flood-aware-send-retry/) |
| 260626-t0q | CJK error classification (port openclaw failover-matches + Zhipu 1305/1311/1113 codes) | 2026-06-26 | c9e1ca8d4 | [260626-t0q-cjk-error-classification](./quick/260626-t0q-cjk-error-classification/) |
| 260626-vzl | Encode Notion "创作方向" into kais-movie-pipeline refs | 2026-06-26 | bd53bc387 | [260626-vzl-kmp-creative-direction-refs](./quick/260626-vzl-kmp-creative-direction-refs/) |
| 260702-ezx | GLM concurrency + retry hardening | 2026-07-02 | 4b821c29b | [260702-ezx-glm-concurrency-hardening](./quick/260702-ezx-glm-concurrency-hardening/) |
| 260702-o1a | Credential-pool overloaded fix | 2026-07-02 | 5839b5f78 | [260702-o1a-credential-pool-overloaded-fix](./quick/260702-o1a-credential-pool-overloaded-fix/) |

## Deferred Items

Items acknowledged and carried forward (NOT in v13.0 scope, explicitly deferred — operator-handoffs are non-blocking close-out per VALIDATE-01 spec):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| **Phase 64 LIVE-EVAL-EXEC (4 reqs EVAL-01..04)** | 3 operator smoke tests + report | Deferred to v14 planning (operator-handoff per VALIDATE-01 spec) | v13.0 close (2026-07-08) |
| **Phase 66 CURATOR-LIVE-TICK (2 reqs CURATE-04/05)** | 1st live tick + runbook | Deferred to v14 planning (operator-handoff per VALIDATE-01 spec) | v13.0 close (2026-07-08) |
| **Option B → 物理分区 migration** | v13.0 EVAL-02 mem0 p95 数据决定是否触发 v14 | Deferred to v14+ (decision feed from v13 EVAL-02) | v13.0 planning (2026-07-08) |
| **Round table 异步并发(INFRA-04 解除)** | GLM upstream capacity 扩容前保留串行约束 | Deferred to v14+ (decision feed from v13 EVAL-03) | v13.0 planning (2026-07-08) |
| **15-expert 全量 production hardening tuning** | v13.0 完成 12-expert transform + smoke;threshold tuning 用 prod 数据留 v14+ | Deferred to v14+ | v13.0 planning (2026-07-08) |
| **kais-hermes-skills repo SKILL.md 改动** | Lineage invariants L1-L6(Phase 48-49)v13.0 仍只读 SKILL.md | Deferred (read-only invariant preserved) | v13.0 planning (2026-07-08) |
| **新 repo 创建(如 kais-orchestrator)** | 单 repo 收敛决策保留;v13.0 全在 hermes-agent | Deferred (decision preserved) | v13.0 planning (2026-07-08) |
| **Automated rollback for curator live tick** | 太复杂;v13.0 用 operator 24h review + 手工 rollback(CURATE-03) | Deferred to v14+ | v13.0 planning (2026-07-08) |
| **OBSRV Prometheus/Grafana integration** | 范围控制;v13.0 用 rich tables + minimal Jinja2 panel | Deferred to v14+ | v13.0 planning (2026-07-08) |
| **15 expert 之外的新 agent(例如 coding-agent-as-agent)** | v13.0 收口于 movie-experts 全量覆盖;非-movie-expert 的 agent 化是 v14+ 候选 | Deferred to v14+ | v13.0 planning (2026-07-08) |

Items acknowledged at v12.0 close (2026-07-08) — 3 operator-action handoffs (runtime validations on real GLM/mem0 APIs):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Operator smoke-test | Phase 57 SC#2: live GLM synthesis endpoint latency smoke | v13.0 Phase 64 EVAL-01 executes this (Phase 64 itself deferred as operator-handoff) | v12.0 close (2026-07-08) |
| Operator smoke-test | Phase 60 EVAL-01: live mem0 p95 benchmark | v13.0 Phase 64 EVAL-02 executes this (Phase 64 itself deferred as operator-handoff) | v12.0 close (2026-07-08) |
| Operator smoke-test | Phase 60 EVAL-02: real-mode fitness battery | v13.0 Phase 64 EVAL-03 executes this (Phase 64 itself deferred as operator-handoff) | v12.0 close (2026-07-08) |

## Session Continuity

**If session is lost, restore context by reading:**

1. `.planning/PROJECT.md` §"Current Milestone: Awaiting next milestone" — v13.0 SHIPPED status + 6 operator-handoff summary + next milestone candidates
2. `.planning/milestones/v13.0-ROADMAP.md` — full v13.0 archive (8 phases, 20/20 reqs, critical path, deferred items)
3. `.planning/milestones/v13.0-MILESTONE-AUDIT.md` — audit doc (verdict: tech_debt, 13/20 satisfied + 1 audit + 6 operator-handoff)
4. `.planning/milestones/v13.0-REQUIREMENTS.md` — archived requirements with traceability table
5. `.planning/ROADMAP.md` — milestones list (v1-v13 all shipped)
6. `.planning/research/v10-orchestrator-design/` — design suite (7 docs + 3 schemas + 1 lint script) as canonical implementation blueprint for v14+
7. `~/.hermes/agents/` — 21 agent YAMLs (9 shipped v11.0 + 12 new v13.0); 15/15 active expert coverage achieved
8. MEMORY.md `feedback-glm-overload-reduce-concurrency.md` (serial constraint policy — INFRA-04 still NOT lifted in v14+ until GLM capacity expands)

**Next action:** Run `/gsd:new-milestone` to start v14.0. **Before v14 milestone planning:** Operator MUST review 6 operator-handoffs from v13.0 close (Phase 64 EVAL-01..04 + Phase 66 CURATE-04/05) to inform v14 scope decisions.

---

*Last updated: 2026-07-08 — v13.0 milestone ARCHIVED. Tag `v13.0` placed. v10.0-v13.0 四 milestone 架构弧线收官. Verdict `tech_debt` (13/20 satisfied + 1 audit + 6 operator-handoff per VALIDATE-01 spec). 17/17 plans in shipped phases complete. REQUIREMENTS.md deleted (next milestone starts fresh via `/gsd:new-milestone`).*

## Operator Next Steps

**v13.0 milestone is ARCHIVED.** Operator actions before v14:

1. Review 6 operator-action handoffs:
   - (a) Phase 64 EVAL-01: live GLM synthesis endpoint latency smoke (needs `GLM_API_KEY`)
   - (b) Phase 64 EVAL-02: live mem0 p95 benchmark (needs `MEM0_API_KEY`) — drives v14 physical-partition decision
   - (c) Phase 64 EVAL-03: real-mode fitness battery (needs `GLM_AUX_API_KEY_1..4`) — drives v14 async-concurrency decision
   - (d) Phase 64 EVAL-04: aggregate report
   - (e) Phase 66 CURATE-04: 1st live curator tick (needs operator approval of live memory mutation risk)
   - (f) Phase 66 CURATE-05: live-tick operator runbook + safety policy
2. Run `/gsd:new-milestone` for v14.0 (informed by Phase 64 live-eval data if executed, or by Phase 67/68 observability dashboard data from steady-state operations)
3. v14+ scope candidates:
   - 物理分区 migration (if Phase 64 EVAL-02 mem0 p95 ≥ 500ms)
   - INFRA-04 async concurrency lift (if Phase 64 EVAL-03 fitness battery passes)
   - 15-expert production tuning (threshold calibration with prod data)
   - 15-expert 之外的新 agent (e.g., coding-agent-as-agent) — v14+ candidate per v13.0 scope discipline
