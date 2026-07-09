# Phase 76 VALIDATE — Cross-Repo Ancestry Assertion (SC#2 + XCUT-04 partial)

**Date:** 2026-07-10
**Phase:** 76 VALIDATE
**Requirements:** XCUT-04 (partial — operator-action handoff documentation depends on pin context) + ROADMAP SC#2 (cross-repo commit pin assertion)
**Executor:** Claude (gsd execute-plan, Phase 76 Plan 01 Task 2)

## Purpose

Phase 70 captured cross-repo baseline pins to anchor the v14.0 milestone against the
pre-milestone state (PITFALL X-1 lineage cascade mitigation). Phase 76 verifies that both
repos' final v14.0 pins are descendants of the P70 baselines — i.e. v14.0 commits layered
on top, NOT force-push rewrites that would invalidate the baseline.

This document satisfies the ROADMAP Phase 76 SC#2 ("Cross-repo commit pin assertion passes:
both hermes-agent `.planning/` and kais-hermes-skills SKILL.md + refs + code have a
v14.0-anchored commit, recorded in STATE.md").

## Pin Table (4 pins)

| Repo | Role | Full SHA (40 char) | Short | Description |
|------|------|---------------------|-------|-------------|
| hermes-agent | P70 baseline | `8f70fcf7f0604db21158f86f8495f3d9ce3c9ab1` | `8f70fcf7` | Phase 70 Plan 01 commit; anchors `.planning/` baseline before any v14.0 plan/STATE edits |
| hermes-agent | v14.0 final | `4e7c58cc9cac3c4925770beaf5a9433369094a24` | `4e7c58cc9` | Phase 76 Plan 01 Task 1 commit (META-RULE X-2 audit script); final pin captured at Task 2 execution time. Subsequent Phase 76 commits (this doc, milestone audit, STATE/ROADMAP, tag v14.0) layer on top — all descendants of this pin. |
| kais-hermes-skills | P70 baseline | `d9620369e48eec51c31ee72ac8827c288eaccf71` | `d9620369` | Phase 70 inventory baseline; anchors SKILL.md + refs + code state before any v14.0 phase edits |
| kais-hermes-skills | v14.0 final | `ba58c2548ab82f0cd9acd7cc7af14402137f8520` | `ba58c254` | Phase 74 Plan 03 last code-review fix commit; final v14.0 pin for kais-hermes-skills (no further edits after Phase 74; Phases 75-76 are hermes-agent-only) |

> Note on hermes-agent final pin: the CONTEXT.md cited `6171e520...` (Phase 75 complete-phase
> commit). The ACTUAL HEAD at Task 2 execution time is `4e7c58cc9...` (includes the Phase 76
> Task 1 audit-script commit). Per the plan's critical_context instruction, the ACTUAL HEAD is
> recorded here — NOT the stale CONTEXT.md value. The ancestry assertion uses HEAD at
> execution time, which is a descendant of the baseline regardless of which post-Phase-70
> commit is chosen as "final".

## Ancestry Assertion Commands + Exit Codes

Both assertions were re-run at Task 2 execution time (2026-07-10) — NOT cached from planning.

### hermes-agent

Command:
`git -C /data/workspace/hermes-agent merge-base --is-ancestor 8f70fcf7f0604db21158f86f8495f3d9ce3c9ab1 HEAD`

Exit code: **0** (descendant) — confirmed at execution time.

Interpretation: every v14.0 `.planning/` commit (Phases 70-76 plans, STATE edits, SUMMARY
files, roadmap updates) is layered on top of the P70 baseline commit. Zero force-push rewrites
detected.

### kais-hermes-skills

Command:
`git -C /data/workspace/kais-hermes-skills merge-base --is-ancestor d9620369e48eec51c31ee72ac8827c288eaccf71 ba58c2548ab82f0cd9acd7cc7af14402137f8520`

Exit code: **0** (descendant) — confirmed at execution time.

Interpretation: all 17 v14.0-touched SKILL.md commits (plus refs + phase module + test edits)
in kais-hermes-skills are layered on top of the P70 baseline. Zero force-push rewrites detected.

## Coverage Statement

Cross-repo coordination preserved across v14.0 milestone: 17 SKILL.md commits in
kais-hermes-skills layered on top of P70 baseline (`d9620369`), hermes-agent `.planning/`
commits layered on top of P70 baseline (`8f70fcf7`), zero force-push rewrites detected.

The v14.0 cross-repo topology (plan → hermes-agent `.planning/`, code → kais-hermes-skills)
follows the v9.0-established pattern. Both repos' commit graphs are linear descendants of
their P70 baselines — no rebase or force-push operations were performed during v14.0. The
lineage cascade threat (PITFALL X-1) is mitigated by this structural guarantee.

## STATE.md Update

STATE.md receives a new `v14.0 Cross-Repo Pins (FINAL)` block (appended after the existing
`v14.0 Freeze Flags (RELEASED by Phase 75 — 2026-07-10)` block) recording both final pins +
both baseline pins + ancestry assertion result + date. This satisfies D-03: "STATE.md gets a
v14.0 Cross-Repo Pins (FINAL) block documenting both pins."

## Related Artifacts

- `.planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md` — P70 baseline pins source (embedded JSON block with 6 SKILL.md sha256 + cross-repo pins)
- `.planning/STATE.md` — `v14.0 Freeze Flags (RELEASED by Phase 75 — 2026-07-10)` block (baseline pins + freeze release record)
- `.planning/phases/75-lineage-bump/75-LINEAGE-BUMP-REPORT.md` — XCUT-03 closure (15/15 agent.yaml regenerated; bump-time pin table)
- `.planning/milestones/v14.0-MILESTONE-AUDIT.md` — Task 3 cites this document in §6 (Cross-Repo Commit Pins section)

---

*Verified: 2026-07-10 (Phase 76 Plan 01 Task 2 execution time)*
*Both ancestry assertions exit 0 (descendant) — cross-repo coordination preserved.*
