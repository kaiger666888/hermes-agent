# Roadmap: Hermes Agent — Kai's Personal Agent Platform

## Overview

v12.0 (Production Hardening) shipped 2026-07-08 — fixed 4 hardening gaps exposed by v11.0 real-GLM smoke tests + ran deferred live-backend benchmark infra. **8/8 reqs verified; audit verdict `passed`; 3 operator-action handoffs deferred.**

**v13.0 milestone in planning** — v10.0-v13.0 收官 milestone。4 tracks: EXPERT-COMPLETION (12 active expert YAMLs to reach 15/15 active coverage) + LIVE-EVAL-EXEC (3 deferred operator smoke tests with prod secrets) + CURATOR-LIVE (curator dry-run → live tick with safety guards) + OBSERVABILITY (operator dashboard: round table metrics + agent registry health + memory backend status).

## Milestones

- ✅ **v1.0 Movie-Experts Suite v2** - Phases 0-6 (shipped 2026-06-15)
- ✅ **v2.0 PRFP Pipeline Design** - Phases 7-12 (shipped 2026-06-16)
- ✅ **v3.0 Skills-to-DAG Alignment** - Phases 13-18 (shipped 2026-06-17)
- ✅ **v4.0 Methodology Backfill** - Phases 19-21 (shipped 2026-06-18)
- ✅ **v5.0 V8.6 Adaptation** - Phases 22-27 (shipped 2026-06-19)
- ✅ **v6.0 Self-Evolution Feedback Loop** - Phases 28-33 (shipped 2026-06-24)
- ✅ **v7.0 openclaw → hermes Migration** - Phases 34-37 (shipped 2026-06-25)
- ✅ **v9.0 kais-movie-pipeline 闭环深化** - Phases 38-43 (shipped 2026-06-27)
- ✅ **v10.0 Hermes-Agent 编排架构第一性原理推导(设计型)** - Phases 44-51 (shipped 2026-07-07, tag `v10.0`)
- ✅ **v11.0 Hermes-Native Expert Agents PoC Implementation** - Phases 52-56 (shipped 2026-07-07, tag `v11.0`)
- ✅ **v12.0 Production Hardening** - Phases 57-61 (shipped 2026-07-08, tag `v12.0`)
- 🚧 **v13.0 v10.0 Design Suite Full Rollout & Live Eval** - Phases 62-69 (in planning)

---

## v13.0: v10.0 Design Suite Full Rollout & Live Eval

**Milestone Goal:** 把 v11.0 设计套件 + v12.0 hardening 留下的 4 项 scope deferrals 全部落地 —— 12 expert agent YAML 全量 transform(达成 15/15 active expert 覆盖)+ 跑 v12.0 deferred 的 3 个 operator smoke tests 收集真实 prod baseline + curator self-evolution 从 dry-run 切 live + 新增 operator dashboard 把 round table / agent registry / memory backend 可观测化。**完成后 v10.0-v13.0 四 milestone 弧线收官。**

**Stats:** 8 phases (62-69) · 20/20 reqs ✓ · Standard granularity

### Phase Numbering

- Integer phases (62-69): Planned milestone work
- Decimal phases: Reserved for urgent insertions only (none currently)

### Critical Path

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                                                                          │
  │  Phase 62 (EXPERT-TRANSFORM) ──┐                                         │
  │                                ▼                                          │
  │                          Phase 63 (EXPERT-REGISTRY) ─────────────┐        │
  │                                                                   │        │
  │                                                                   │        │
  │  Phase 64 (LIVE-EVAL-EXEC) — operator-secrets-bound, parallel    │        │
  │                                                                   │        │
  │                                                                   │        │
  │  Phase 65 (CURATOR-LIVE-GUARDS) ──┐                               │        │
  │                                   ▼                               │        │
  │                             Phase 66 (CURATOR-LIVE-TICK) ─────┐   │        │
  │                                                                │   │        │
  │                                                                │   │        │
  │  Phase 67 (OBSRV-BACKEND) ──┐                                  │   │        │
  │                             ▼                                  │   │        │
  │                       Phase 68 (OBSRV-PRESENTATION) ───────────┼───┼────────┐
  │                                                                │   │        │
  │                                       ALL OTHER PHASES ────────┴───┴────────┼
  │                                                                          ▼
  │                                                            Phase 69 (VALIDATE)
  │                                                            strictly LAST
  └────────────────────────────────────────────────────────────────────────────┘
```

**Hard dependencies (must-hold):**
- Phase 63 → needs Phase 62 (12 new YAMLs must exist before registry 21-agent smoke)
- Phase 66 → needs Phase 65 (curator `--live` flag + bias canary must ship before 1st live tick)
- Phase 68 → needs Phase 67 (collectors must emit data before CLI/dashboard consume)
- Phase 69 → strictly LAST; cross-20-req audit + smoke + close-out (mirror v11.0 P56 / v12.0 P61 pattern)

**Parallel tracks (operator-secrets vs code-work):**
- Phase 64 (LIVE-EVAL-EXEC) needs operator secrets (GLM API key, `MEM0_API_KEY`, `GLM_AUX_API_KEY_1..4`) — can run in parallel with Phases 62, 63, 65-68; does not block code-work tracks
- Phases 62-63 (EXPERT-COMPLETION), 65-66 (CURATOR-LIVE), 67-68 (OBSERVABILITY) are pure code-work — can interleave with operator-secrets track

## Phases

- [ ] **Phase 62: EXPERT-YAML-TRANSFORM** - 12 expert agent YAML 全量 transform(15/15 active coverage)
- [ ] **Phase 63: EXPERT-REGISTRY-INTEGRATION** - 21-agent registry load + visual_executor round table smoke
- [ ] **Phase 64: LIVE-EVAL-EXEC** - 3 deferred operator smoke tests + live-eval-report.md(v14 decision feed)
- [ ] **Phase 65: CURATOR-LIVE-GUARDS** - `--live` opt-in flag + pre-tick bias canary + post-tick audit log
- [ ] **Phase 66: CURATOR-LIVE-TICK** - 1st live tick end-to-end + operator runbook + safety policy
- [ ] **Phase 67: OBSERVABILITY-BACKEND** - 3 metrics collectors(agent registry / round table / mem0 backend)
- [ ] **Phase 68: OBSERVABILITY-PRESENTATION** - CLI `hermes orchestrator status` + dashboard web view
- [ ] **Phase 69: VALIDATE** - v13.0 milestone audit + close-out report(strictly LAST)

## Phase Details

### Phase 62: EXPERT-YAML-TRANSFORM
**Goal**: 12 个 active expert SKILL.md → `~/.hermes/agents/{name}.agent.yaml` 全量 transform,达成 15/15 active expert 覆盖(9 已 ship + 12 新增)。Source SKILL.md 在 kais-hermes-skills repo 只读。
**Depends on**: Nothing (first v13.0 phase; v12.0 P57-61 shipped provides runtime baseline)
**Requirements**: EXPERT-01, EXPERT-02, EXPERT-03
**Success Criteria** (what must be TRUE):
  1. 12 个新 YAML 文件存在于 `~/.hermes/agents/{animation_studio,colorist,compliance_gate,creative_source,documentary_maker,performer,production,prompt_injector,scene_builder,script_auditor,storyboard_designer,visual_executor}.agent.yaml`(operator can `ls ~/.hermes/agents/` and count 21 total)
  2. 全部 12 个新 YAML byte-pass `jsonschema.Draft202012Validator.validate()` against `.planning/research/v10-orchestrator-design/agents-schema.yaml`(scripted check exits 0)
  3. 全部 12 个新 YAML lineage 字段 populated —— `source_sha` + `transform_rule_id` + `transform_timestamp`(grep finds non-empty values in all 12 files; spot-check 1 traces back to source SKILL.md commit SHA)
  4. Transform rules applied match v10.0 `04-MIGRATION-PATH.md §2` 75-cell table(per-agent transform log emitted with rule IDs cited)
**Plans**: TBD

### Phase 63: EXPERT-REGISTRY-INTEGRATION
**Goal**: Agent registry 启动时加载全部 21 agents 无错误,且至少 1 个新 agent(`visual_executor` — 最复杂,带 sub_steps)能通过 round table 实际调用产生非空响应。
**Depends on**: Phase 62 (12 new YAMLs must exist before 21-agent registry load)
**Requirements**: EXPERT-04, EXPERT-05
**Success Criteria** (what must be TRUE):
  1. Agent registry startup emits 21 agents loaded count with zero schema/lifecycle errors; missing-expert 告警逻辑 wired(`hermes orchestrator status` 或同等命令 surfaces the count)
  2. Missing-expert 告警 fires correctly when a known-required expert_id is absent from `~/.hermes/agents/`(canary test: temporarily rename one YAML, observe warning emitted)
  3. `visual_executor.agent.yaml` 通过 7 MCP tools 中的 `open_round_table` 实际调用并产生非空响应 —— operator 可以 run 一个 minimal round table with `visual_executor` as panelist,observe non-empty synthesis output in round table state file
**Plans**: TBD

### Phase 64: LIVE-EVAL-EXEC
**Goal**: 跑 v12.0 deferred 的 3 个 operator smoke tests 收集真实 prod baseline,produce decision feed for v14(物理分区 / 异步并发触发条件)。需要 operator secrets(GLM/mem0 keys)。**可与 code-work tracks 并行。**
**Depends on**: Nothing code-side; operator must provide secrets(`GLM_API_KEY`, `MEM0_API_KEY`, `GLM_AUX_API_KEY_1..4`)
**Requirements**: EVAL-01, EVAL-02, EVAL-03, EVAL-04
**Success Criteria** (what must be TRUE):
  1. Live GLM synthesis endpoint latency smoke 跑完 —— `python scripts/run_screenplay_step3_roundtable.py --smoke` 或同等命令 produces p50/p95 latency numbers,验证 long-prompt → anthropic-compat routing(ENDPOINT-01)在 live load 下工作(numbers captured in report)
  2. Live mem0 p95 benchmark 跑完 —— `MEM0_API_KEY` configured,read/write p95 numbers captured,显式 trigger 或不 trigger v14 物理分区 threshold(p95 < 500ms → 单 backend 保留;p95 ≥ 500ms → v14 物理分区评估开启)
  3. Real-mode fitness battery 跑完 —— `GLM_AUX_API_KEY_1..4` configured,8 scenarios × real GLM calls produce production-grade accuracy + latency numbers(captured in report)
  4. 3 smoke 结果聚合到 `.planning/research/v13-live-eval/live-eval-report.md` —— 显式 verdict per dimension(physical-partition yes/no;async-concurrency yes/no;fitness-battery accuracy baseline)作为 v14 决策输入
**Plans**: TBD
**Operator secrets needed**: `GLM_API_KEY`, `MEM0_API_KEY`, `GLM_AUX_API_KEY_1..4` (provided by operator before this phase runs)

### Phase 65: CURATOR-LIVE-GUARDS
**Goal**: 给 curator self-evolution CLI 加 `--live` opt-in flag(默认仍 dry-run per v11.0 EVAL-06 invariant)+ pre-tick bias canary check + post-tick 审计日志,为 1st live tick 铺好安全护栏。
**Depends on**: Nothing (precondition for Phase 66; v12.0 bias canary baseline already shipped)
**Requirements**: CURATE-01, CURATE-02, CURATE-03
**Success Criteria** (what must be TRUE):
  1. `hermes curator evolve --live` flag 工作 —— invoke without `--live` defaults to dry-run(zero state mutation,observable via test);invoke with `--live` proceeds to live mode(opt-in confirmed by CLI output)
  2. Pre-tick bias canary check wired —— must catch ≥ 4/5 known-bad records per v12.0 EVAL-03 baseline;canary fail 时 abort live tick with explicit error reason logged(operator can run the canary against 5 seeded bad records and verify ≥4 are flagged + live tick aborts)
  3. Post-tick 审计日志 emits sha256-tagged memory writes for every live tick —— operator can inspect `~/.hermes/skills/.audit/log.jsonl` (or equivalent) and see per-write sha256 + timestamp;supports manual rollback search within 24h window
**Plans**: TBD

### Phase 66: CURATOR-LIVE-TICK
**Goal**: 1st live curator tick 端到端跑通,capture before/after memory diff + bias canary 结果 + token cost,作为 v14+ live-tick baseline;同时落地 operator runbook + safety policy 文档。
**Depends on**: Phase 65 (`--live` flag + bias canary + audit log must be in place)
**Requirements**: CURATE-04, CURATE-05
**Success Criteria** (what must be TRUE):
  1. 1st live tick 端到端跑通 —— operator invokes `hermes curator evolve --live` against current `~/.hermes/agents/` state,capture before/after memory diff(sha256-tagged writes in audit log)+ bias canary pass/fail result + token cost summary in a report file
  2. `.planning/research/v13-live-eval/curator-live-runbook.md` exists —— documents when to use live vs dry-run, operator monitoring checklist(what to look for in 24h post-tick), manual rollback procedure, escalation policy
  3. Live tick report 自含 baseline metrics(memory writes count, token cost, bias canary verdict)作为 v14+ live-tick cadence decision input
**Plans**: TBD

### Phase 67: OBSERVABILITY-BACKEND
**Goal**: 3 个 metrics collectors 实现 + wired 进对应 runtime modules,emitting structured metrics agent registry health + round table metrics + memory backend metrics。
**Depends on**: Phase 63 (agent registry must load 21 agents before health check meaningful) — soft dependency; collectors can be built in parallel but SC#1 verification needs Phase 63 done
**Requirements**: OBSRV-01, OBSRV-02, OBSRV-03
**Success Criteria** (what must be TRUE):
  1. Agent registry health collector wired —— emits 21 agents loaded · schema validation status · missing-expert 告警 state · lineage integrity check result;accessible at `/orchestrator/agents/status` FastAPI endpoint on `hermes dashboard` server(operator can `curl localhost:<port>/orchestrator/agents/status` and get JSON)
  2. Round table metrics collector wired into round table executor —— emits latency p50/p95 · token cost · state transitions · serial-lock wait time · early-stop trigger rate per round table execution(metrics observable in metrics log or state file after a round table run)
  3. Memory backend metrics collector wired into mem0 backend adapter —— emits mem0 p95 read/write · conflict arbitration rate · compaction trigger rate · error rate(metrics observable after running a memory operation)
**Plans**: TBD

### Phase 68: OBSERVABILITY-PRESENTATION
**Goal**: CLI 命令 `hermes orchestrator status` rich tables 展示 3 个维度 + dashboard web view surface 实时状态,让 operator 一眼可见系统健康。
**Depends on**: Phase 67 (collectors must emit data before CLI/dashboard can surface)
**Requirements**: OBSRV-04, OBSRV-05
**Success Criteria** (what must be TRUE):
  1. `hermes orchestrator status` CLI 命令工作 —— rich tables 展示 3 个维度(agent registry / round table / memory backend);支持 `--json` flag 给脚本消费(operator can run command, observe 3 rich tables; `--json` produces valid JSON consumable by `jq`)
  2. Dashboard web view exists —— minimal Jinja2 panel surface 3 个维度的实时状态,基于现有 `hermes dashboard` FastAPI server 扩展(不引入新框架);operator can open dashboard URL and see 3 panels with live data
  3. CLI + dashboard 两个 surface 都消费同一个 metrics source(no data drift between them — operator can compare CLI `--json` output with dashboard panel data and verify parity)
**Plans**: TBD
**UI hint**: yes

### Phase 69: VALIDATE
**Goal**: v13.0 milestone audit + close-out report at `.planning/milestones/v13.0-MILESTONE-AUDIT.md`,包含 4-track traceability + operator-action handoffs 状态 + verdict(pass / tech_debt / fail)。**Strictly LAST phase**(mirror v11.0 P56 / v12.0 P61 single-phase close-out pattern)。
**Depends on**: All other v13.0 phases (62, 63, 64, 65, 66, 67, 68 must be complete)
**Requirements**: VALIDATE-01
**Success Criteria** (what must be TRUE):
  1. `.planning/milestones/v13.0-MILESTONE-AUDIT.md` exists —— covers 4-track traceability(EXPERT-COMPLETION 5 reqs / LIVE-EVAL-EXEC 4 reqs / CURATOR-LIVE 5 reqs / OBSERVABILITY 5 reqs / VALIDATE 1 req = 20/20)with status per requirement
  2. Audit doc 显式 verdict(pass / tech_debt / fail)+ operator-action handoffs 状态(3+ live validations from EVAL track + 1 live curator tick may be handoffs if secrets unavailable or run deferred)
  3. REQUIREMENTS.md Traceability table flipped to all phase numbers(62-69)and v10.0-v13.0 milestone arc 收官声明(v14+ decision feed from v13 live data)
**Plans**: TBD

## Progress

**Execution Order:**
Phases 62 → 63 (sequential, code-work); 65 → 66 (sequential, code-work); 67 → 68 (sequential, code-work); 64 (parallel, operator-secrets-bound); 69 (strictly LAST, all others complete)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 62. EXPERT-YAML-TRANSFORM | 0/TBD | Not started | - |
| 63. EXPERT-REGISTRY-INTEGRATION | 0/TBD | Not started | - |
| 64. LIVE-EVAL-EXEC | 0/TBD | Not started | - |
| 65. CURATOR-LIVE-GUARDS | 0/TBD | Not started | - |
| 66. CURATOR-LIVE-TICK | 0/TBD | Not started | - |
| 67. OBSERVABILITY-BACKEND | 0/TBD | Not started | - |
| 68. OBSERVABILITY-PRESENTATION | 0/TBD | Not started | - |
| 69. VALIDATE | 0/TBD | Not started | - |

---

## Shipped Milestone Details

<details>
<summary>✅ v12.0 Production Hardening (Phases 57-61) - SHIPPED 2026-07-08</summary>

**Stats:** 5 phases · 9 plans · 53 commits on v12.0-dev · 8/8 reqs ✓ · Tag `v12.0` · Audit `passed`

**One sentence:** Fixed 4 hardening gaps exposed by v11.0 real-GLM smoke tests — endpoint routing (long prompts → anthropic-compat), RPM throttling (token bucket + per-round-table TPM budget), auxiliary credential pool isolation (separate keys from main agent + per-key TPM tracking), live-eval infrastructure (mem0 backend adapter + fitness battery real-mode baseline).

| Phase | Name | Status |
|-------|------|--------|
| 57 | ENDPOINT-ROUTING — long-prompt endpoint routing (z.ai/anthropic-compat split) | SHIPPED (1 plan, 2026-07-08) |
| 58 | RPM-THROTTLING — per-task RPM token bucket + per-round-table TPM budget | SHIPPED (2 plans, 2026-07-08) |
| 59 | AUX-POOL-ISOLATION — separate auxiliary credential pool + per-key TPM tracking | SHIPPED (2 plans, 2026-07-08) |
| 60 | LIVE-EVAL — mem0 backend adapter + fitness battery real-mode infra | SHIPPED (2 plans, 2026-07-08) |
| 61 | VALIDATE — milestone audit + production smoke report | SHIPPED (1 plan, 2026-07-08) |

See `.planning/milestones/v12.0-ROADMAP.md` for full archive + `.planning/milestones/v12.0-MILESTONE-AUDIT.md` for audit (status: passed, 8/8 reqs, 3 operator-action handoffs deferred).

</details>

<details>
<summary>✅ v11.0 Hermes-Native Expert Agents PoC Implementation (Phases 52-56) - SHIPPED 2026-07-07</summary>

**Stats:** 5 phases · 12 plans · 128 commits · 149 files · 39,256 insertions · 15/15 reqs ✓ · Tag `v11.0` · Audit `passed`

**One sentence:** Implemented the v10.0 design suite as runtime code — agent registry + 7 MCP tools + round table state machine + serial executor + 9 sample agent YAMLs + screenplay Step 3 driver + memory conflict arbitration + 7 acceptance criteria (fitness battery, latency SLO, bias canary, compaction, threshold tuning, dry-run-first, schema migration dry-run).

See `.planning/milestones/v11.0-ROADMAP.md` for full archive + `.planning/milestones/v11.0-MILESTONE-AUDIT.md` for audit.

</details>

<details>
<summary>✅ v10.0 Hermes-Agent 编排架构第一性原理推导 (Phases 44-51) - SHIPPED 2026-07-07</summary>

**Stats:** 8 phases · 8 plans · 9/9 reqs ✓ · Tag `v10.0` · Design-only (zero code changes)

**One sentence:** 从第一性原理推导 Hermes 三层编排架构(总调度器 + native expert agents + CC 执行场),产 7 design docs + 3 schemas + 1 lint script,作为 v11.0 PoC 实施蓝本。

See `.planning/milestones/v10.0-ROADMAP.md` for full archive.

</details>

<details>
<summary>✅ v9.0 kais-movie-pipeline 闭环深化 (Phases 38-43) - SHIPPED 2026-06-27</summary>

**Stats:** 6 phases · 13 plans · 22/22 reqs ✓ · Tag `v9.0` (anchored at `599ef61a8`)

See `.planning/milestones/v9.0-MILESTONE-AUDIT.md` for full audit.

</details>

<details>
<summary>✅ v7.0 openclaw → hermes Migration (Phases 34-37) - SHIPPED 2026-06-25</summary>

</details>

---

*Last updated: 2026-07-08 — v13.0 ROADMAP created: 8 phases (62-69), 20/20 reqs mapped, VALIDATE-01 strictly LAST. Next: `/gsd:plan-phase 62` to start with EXPERT-YAML-TRANSFORM.*
