# Roadmap: Hermes Agent — Kai's Personal Agent Platform

## Overview

**Current milestone:** Awaiting next milestone decision (v7.0 shipped 2026-06-25).

v7.0 SHIPPED — openclaw → hermes-agent Primary Agent Migration. Migrated coding-agent + tmux-agents skills, integrated SOUL.md routing rules non-destructively, built mem0 ingestion tooling, wrote canonical migration report. First milestone outside `skills/movie-experts/` scope.

---

## Milestones

- ✅ **v1 Movie-Experts Suite v2** — Phases 0-6 (shipped 2026-06-15)
- ✅ **v2.0 PRFP** — Phases 7-12 (shipped 2026-06-16)
- ✅ **v3.0 Skills-to-DAG Alignment** — Phases 13-18 (shipped 2026-06-17)
- ✅ **v4.0 Methodology Backfill** — Phases 19-21 (shipped 2026-06-18)
- ✅ **v5.0 kais-movie-agent V8.6 Adaptation** — Phases 22-27 (shipped 2026-06-19)
- ✅ **v6.0 Self-Evolution & Feedback Loop** — Phases 28-33 (shipped 2026-06-24)
- ✅ **v7.0 openclaw → hermes-agent Primary Agent Migration** — Phases 34-37 (shipped 2026-06-25)

<details>
<summary>✅ v1 through v7.0 (Phases 0-37) — SHIPPED</summary>

For completed milestone phase details, see:
- `.planning/milestones/v1-ROADMAP.md`
- `.planning/milestones/v3.0-ROADMAP.md`
- `.planning/milestones/v4.0-ROADMAP.md`
- `.planning/milestones/v5.0-ROADMAP.md`
- `.planning/milestones/v6.0-ROADMAP.md`
- `.planning/milestones/v7.0-ROADMAP.md` (most recent)
- `.planning/milestones/v7.0-MIGRATION-REPORT.md` (v7.0 canonical close-out)

</details>

---

## Next Milestone

Not yet planned. Run `/gsd:new-milestone` to start v8.0 planning.

Suggested priorities from v7.0 migration report §Forward-Looking Notes (operator to decide):

- **Operator smoke-tests (immediate):** Complete the 4 deferred runtime validations from v7.0-MIGRATION-REPORT.md (MEM0_API_KEY config + live mem0 ingestion + SOUL routing observation + skill invocation smoke-test)
- **v8.0 candidate: feishu-* skills** — Largest deferred migration item; Feishu API surface substantial
- **v8.0 candidate: multi-profile mechanism** — v7.0 uses single SOUL.md; multi-profile was deferred
- **v8.0 candidate: doc-consistency patch** — ROADMAP/REQUIREMENTS "133 files / 1.3MB" vs actual "124 files / 817KB" discrepancy
- **Concurrent workstream integration:** `34-review-gate-framework/` (Gate state machine for review_gates plugin) was committed during v7.0; integration with mainline pending

---

*Last updated: 2026-06-25 — v7.0 SHIPPED (Phases 34-37, 14/14 reqs structurally satisfied). Awaiting next milestone decision.*
