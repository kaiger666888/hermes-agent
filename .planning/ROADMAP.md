# Roadmap: Hermes Agent — Kai's Personal Agent Platform

## Overview

v11.0 (Hermes-Native Expert Agents PoC) shipped 2026-07-07 — implemented the v10.0 design suite as runtime code: agent registry + 7 MCP tools + round table state machine + serial executor + 9 sample agent YAMLs + screenplay Step 3 driver + memory conflict arbitration + 7 acceptance criteria. **317 automated tests green; audit verdict `passed` with 5 documented operator-action handoffs.**

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

---

## Next Milestone

Not yet planned. Run `/gsd:new-milestone` to start.

---

## Shipped Milestone Details

<details>
<summary>✅ v11.0 Hermes-Native Expert Agents PoC Implementation (Phases 52-56) - SHIPPED 2026-07-07</summary>

**Stats:** 5 phases · 12 plans · 128 commits · 149 files · 39,256 insertions · 15/15 reqs ✓ · Tag `v11.0` · Audit `passed`

**One sentence:** Implemented the v10.0 design suite as runtime code — agent registry + 7 MCP tools + round table state machine + serial executor + 9 sample agent YAMLs + screenplay Step 3 driver + memory conflict arbitration + 7 acceptance criteria (fitness battery, latency SLO, bias canary, compaction, threshold tuning, dry-run-first, schema migration dry-run).

| Phase | Name | Status |
|-------|------|--------|
| 52 | INFRA-FOUNDATION — agent registry + 7 MCP tools + state machine + serial enforcement | SHIPPED (4 plans, 2026-07-07) |
| 53 | CREATIVE-SLICE — 9 agent YAMLs + Step 3 round table + conflict arbitration | SHIPPED (3 plans, 2026-07-07) |
| 54 | EVAL-HARNESS-1 — fitness battery + latency SLO + bias canary | SHIPPED (3 plans, 2026-07-07) |
| 55 | EVAL-HARNESS-2 — compaction + threshold tuning + dry-run-first + schema migration | SHIPPED (4 plans, 2026-07-07) |
| 56 | VALIDATE — milestone audit + smoke test report | SHIPPED (1 plan, 2026-07-07) |

See `.planning/milestones/v11.0-ROADMAP.md` for full archive + `.planning/milestones/v11.0-MILESTONE-AUDIT.md` for audit (status: passed, 15/15 reqs, 5 operator-action handoffs deferred per VALIDATE-01 spec).

</details>

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

See `.planning/milestones/v10.0-ROADMAP.md` for full archive + `.planning/milestones/v10.0-MILESTONE-AUDIT.md` for audit.

</details>

<details>
<summary>✅ v9.0 kais-movie-pipeline 闭环深化 (Phases 38-43) - SHIPPED 2026-06-27</summary>

**Stats:** 6 phases · 13 plans · 22/22 reqs ✓ · Tag `v9.0` (anchored at `599ef61a8`)

**One sentence:** 把 Notion "创作方向" Tier B+C 落地为 kais-movie-pipeline 的 4 个新能力(平台母版切片 / 配方库 v0 / LTX2.3 预览闭环 / 数据收敛回流)+ 3 个跨平台红线审核门,完成「创意→生产→分发→反馈」全闭环。

See `.planning/milestones/v9.0-MILESTONE-AUDIT.md` for full audit.

</details>

<details>
<summary>✅ v7.0 openclaw → hermes Migration (Phases 34-37) - SHIPPED 2026-06-25</summary>

</details>

---

*Last updated: 2026-07-07 — v11.0 milestone archived (5 phases, 12 plans, 15/15 reqs, audit `passed`). Next: `/gsd:new-milestone` to start the next milestone.*
