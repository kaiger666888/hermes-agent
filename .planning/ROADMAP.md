# Roadmap: Hermes Agent — Kai's Personal Agent Platform

## Overview

v10.0 (design-only milestone) shipped 2026-07-07 — Hermes-Agent orchestrator + Hermes-native expert agents + Claude Code execution场 three-layer architecture derived from first principles. Next: v11.0 PoC will implement vertical slices per `05-POC-PLAN.md` §3.

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

Next milestone: **v11.0 PoC** — implement vertical slices per `.planning/research/v10-orchestrator-design/05-POC-PLAN.md` §3. Start with `/gsd:new-milestone v11.0`.

---

## Shipped Milestone Details

<details>
<summary>✅ v10.0 Hermes-Agent 编排架构第一性原理推导 (Phases 44-51) - SHIPPED 2026-07-07</summary>

**Stats:** 8 phases · 8 plans · 9/9 reqs ✓ · Tag `v10.0` · Design-only (zero code changes)

**One sentence:** 从第一性原理推导 Hermes 三层编排架构(总调度器 + native expert agents + CC 执行场),产 7 design docs + 3 schemas + 1 lint script,作为 v11.0 PoC 实施蓝本。

| Phase | Name | Status |
|-------|------|--------|
| 44 | FIRST-PRINCIPLES — 7 决策推导 + 显式拒绝总表 | SHIPPED (Plan 01, 2026-07-06) |
| 45 | AGENT-SCHEMA — 18-field YAML + memory-record-schema | SHIPPED (Plan 01, 2026-07-06) |
| 46 | ROUND-TABLE-PROTOCOL — Turn lifecycle + conflict arbitration | SHIPPED (Plan 01, 2026-07-06) |
| 47 | KIMI-COMPARISON — T6 vs Kimi 7-dim contrast | SHIPPED (Plan 01, 2026-07-06) |
| 48 | CROSS-REPO-IMPACT — 3-location sync + Option B vs partition | SHIPPED (Plan 01, 2026-07-06) |
| 49 | MIGRATION-PATH — 15 expert transform + memory migration | SHIPPED (Plan 01, 2026-07-06) |
| 50 | POC-PLAN — v11.0 PoC acceptance criteria + risk register | SHIPPED (Plan 01, 2026-07-06) |
| 51 | VALIDATE — Cross-doc lint + milestone audit | SHIPPED (Plan 01, 2026-07-07) |

See `.planning/milestones/v10.0-ROADMAP.md` for full archive + `.planning/v10.0-MILESTONE-AUDIT.md` for audit (status: passed, 9/9 reqs, 8/8 phases, design-only).

</details>

<details>
<summary>✅ v9.0 kais-movie-pipeline 闭环深化 (Phases 38-43) - SHIPPED 2026-06-27</summary>

**Stats:** 6 phases · 13 plans · 22/22 reqs ✓ · Tag `v9.0` (anchored at `599ef61a8`)

**One sentence:** 把 Notion "创作方向" Tier B+C 落地为 kais-movie-pipeline 的 4 个新能力(平台母版切片 / 配方库 v0 / LTX2.3 预览闭环 / 数据收敛回流)+ 3 个跨平台红线审核门,完成「创意→生产→分发→反馈」全闭环。

| Phase | Name | Status |
|-------|------|--------|
| 38 | SLICE — 平台母版切片 (Step 14) | SHIPPED (Plan 01, 2026-06-27) |
| 39 | FORM — 配方库 v0 (new plugin) | SHIPPED (Plans 01+02+03, 2026-06-27) |
| 40 | GATE — 3 新审核门 | SHIPPED (Plans 01+02+03, 2026-06-26) |
| 41 | PREVIEW — LTX2.3 Step 6.5 | SHIPPED (Plan 01, 2026-06-27) |
| 42 | DATA — 数据收敛 (Step 15) | SHIPPED (Plans 01+02+03+04, 2026-06-27) |
| 43 | VALIDATE — 集成验证 + close-out | SHIPPED (Plan 01, 2026-06-27) |

See `.planning/milestones/v9.0-MILESTONE-AUDIT.md` for full audit (status: passed, 22/22 reqs, 6/6 phases, FOUND-08 preserved milestone-wide).

</details>

<details>
<summary>✅ v7.0 openclaw → hermes Migration (Phases 34-37) - SHIPPED 2026-06-25</summary>

**Stats:** 4 phases · 7 plans · 14/14 reqs ✓ · Tag `v7.0`

| Phase | Name | Status |
|-------|------|--------|
| 34 | Skills Migration (coding-agent + tmux-agents) | SHIPPED |
| 35 | SOUL.md Identity Enhancement | SHIPPED |
| 36 | Memory Ingestion (USER.md + mem0 scripts) | SHIPPED |
| 37 | Validation + Migration Report | SHIPPED |

</details>

<details>
<summary>✅ v6.0 Self-Evolution Feedback Loop (Phases 28-33) - SHIPPED 2026-06-24</summary>

**Stats:** 6 phases · 13 plans · 26/26 reqs ✓ · Tag `v6.0`

| Phase | Name | Status |
|-------|------|--------|
| 28 | INGEST — Multi-source Feedback | SHIPPED |
| 29 | STORE — Durable FeedbackStore | SHIPPED |
| 30 | GATE — Eval gate | SHIPPED |
| 31 | EVOL — Knowledge evolution | SHIPPED |
| 32 | CURATE — Curator upgrade + EVOL-02 | SHIPPED |
| 33 | OBS — Observability + close-out | SHIPPED |

</details>

<details>
<summary>✅ Earlier milestones (v1-v5) - SHIPPED 2026-06-15 → 2026-06-19</summary>

- **v5.0 V8.6 Adaptation** (Phases 22-27, shipped 2026-06-19): 30/30 reqs ✓
- **v4.0 Methodology Backfill** (Phases 19-21, shipped 2026-06-18): 14/14 reqs ✓
- **v3.0 Skills-to-DAG Alignment** (Phases 13-18, shipped 2026-06-17): 12/12 reqs ✓
- **v2.0 PRFP Pipeline Design** (Phases 7-12, shipped 2026-06-16): 52/52 reqs ✓ (design-only)
- **v1.0 Movie-Experts Suite v2** (Phases 0-6, shipped 2026-06-15): all v1 reqs ✓

</details>

---

*Last updated: 2026-07-07 — v10.0 design milestone SHIPPED (9/9 reqs ✓, 8/8 phases ✓, tag `v10.0`). ROADMAP collapsed to milestone summary. Next: v11.0 PoC.*
