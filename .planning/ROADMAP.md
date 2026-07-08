# Roadmap: Hermes Agent — Kai's Personal Agent Platform

## Overview

v13.0 (v10.0 Design Suite Full Rollout & Live Eval) shipped 2026-07-08 — closed the v10.0-v13.0 four-milestone architecture arc: 12 expert agent YAML transform (15/15 active coverage) + curator live-tick safety guards + observability dashboard (3 collectors + CLI + web panel). **8/8 reqs mapped (13 satisfied + 1 audit + 6 operator-handoff); audit verdict `tech_debt`; 6 operator-action handoffs deferred per VALIDATE-01 spec.**

**Awaiting next milestone.** v14+ decisions (物理分区 / 异步并发 / 15-expert production tuning) wait on v13 Phase 64 live-eval data (operator secrets needed).

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
- ✅ **v13.0 v10.0 Design Suite Full Rollout & Live Eval** - Phases 62-69 (shipped 2026-07-08, tag `v13.0`)

---

## v13.0: v10.0 Design Suite Full Rollout & Live Eval ✅ SHIPPED 2026-07-08

**Stats:** 8 phases (62-69) · 20/20 reqs (13 satisfied + 1 audit + 6 operator-handoff) · 17 plans in shipped phases · Tag `v13.0` · Audit `tech_debt`

**One sentence:** 把 v11.0 设计套件 + v12.0 hardening 留下的 4 项 scope deferrals 全部落地 —— 12 expert agent YAML 全量 transform(15/15 active coverage)+ curator live-tick 安全护栏 + 3 维 observability surface(agent registry + round table + memory backend)。

See `.planning/milestones/v13.0-ROADMAP.md` for full archive + `.planning/milestones/v13.0-MILESTONE-AUDIT.md` for audit.

---

## Shipped Milestone Details

<details>
<summary>✅ v13.0 v10.0 Design Suite Full Rollout & Live Eval (Phases 62-69) - SHIPPED 2026-07-08</summary>

**Stats:** 8 phases · 17 plans in shipped phases · 247 files · 34,341 insertions / 9,972 deletions · 20/20 reqs ✓ · Tag `v13.0` · Audit `tech_debt`

**One sentence:** 把 v11.0 设计套件 + v12.0 hardening 留下的 4 项 scope deferrals 全部落地 —— 12 expert agent YAML 全量 transform(15/15 active coverage)+ curator live-tick 安全护栏 + 3 维 observability surface(agent registry + round table + memory backend)。

| Phase | Name | Status |
|-------|------|--------|
| 62 | EXPERT-YAML-TRANSFORM — 12 expert agent YAML 全量 transform | SHIPPED (4 plans, 2026-07-08) |
| 63 | EXPERT-REGISTRY-INTEGRATION — 21-agent registry + missing-expert alarm + visual_executor smoke | SHIPPED (4 plans, 2026-07-08) |
| 64 | LIVE-EVAL-EXEC — 3 deferred operator smoke tests + report | DEFERRED (operator-handoff, needs GLM/mem0 secrets) |
| 65 | CURATOR-LIVE-GUARDS — `--live` opt-in flag + bias canary + audit log | SHIPPED (3 plans, 2026-07-08) |
| 66 | CURATOR-LIVE-TICK — 1st live tick + runbook | DEFERRED (operator-handoff, live memory mutation risk) |
| 67 | OBSERVABILITY-BACKEND — 3 metrics collectors + FastAPI endpoint | SHIPPED (4 plans, 2026-07-08) |
| 68 | OBSERVABILITY-PRESENTATION — CLI + dashboard panel | SHIPPED (2 plans, 2026-07-08) |
| 69 | VALIDATE — milestone audit + close-out | SHIPPED (audit doc, 2026-07-08) |

See `.planning/milestones/v13.0-ROADMAP.md` for full archive + `.planning/milestones/v13.0-MILESTONE-AUDIT.md` for audit (verdict: tech_debt, 13/20 satisfied + 1 audit + 6 operator-handoff).

</details>

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

*Last updated: 2026-07-08 — v13.0 milestone archived + tag `v13.0` placed. v10.0-v13.0 四 milestone 架构弧线收官。Next: operator review of 6 handoffs → `/gsd:new-milestone` for v14.0.*
