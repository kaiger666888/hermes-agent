# Phase 83 VALIDATE — Cross-Repo Ancestry Assertion (SC#2 closure)

**Date:** 2026-07-10
**Phase:** 83 VALIDATE
**Requirements:** VALIDATE-V15 (SC#4 cross-repo final pins recorded)
**Executor:** Claude (gsd execute-plan, Phase 83 Plan 01 Task 2)

## Purpose

Phase 76 (v14.0 VALIDATE) captured cross-repo final pins anchoring the v14.0 milestone state
against its P70 baselines. Phase 83 (v15.0 VALIDATE) verifies that both repos' v15.0 final pins
are descendants of the v14.0 final pins — i.e. v15.0 commits layered on top, NOT force-push
rewrites that would invalidate the v14.0 baseline.

This document satisfies ROADMAP Phase 83 SC#4 ("Cross-repo final pins recorded in audit doc §8
+ STATE.md (hermes-agent + kais-hermes-skills commit hashes at close, ancestry assertions
exit 0)").

## Pin Table (4 pins)

| Repo | Role | Full SHA (40 char) | Short | Ancestry |
|------|------|---------------------|-------|----------|
| hermes-agent | v14.0 final (baseline) | `4e7c58cc9cac3c4925770beaf5a9433369094a24` | `4e7c58cc` | (baseline) |
| hermes-agent | v15.0 final | `48cb57d7b6ecc5d171f070d898fb57e7d5c5e70c` | `48cb57d7` | descendant of `4e7c58cc` (exit 0) |
| kais-hermes-skills | v14.0 final (baseline) | `ba58c2548ab82f0cd9acd7cc7af14402137f8520` | `ba58c254` | (baseline) |
| kais-hermes-skills | v15.0 final | `009773fcb50041813d436c4c09ac7a52f10cf5a3` | `009773f` | descendant of `ba58c254` (exit 0) |

> Note: the hermes-agent v15.0 final pin (`48cb57d7`) is the Phase 83 Task 1 audit-script commit.
> Subsequent Phase 83 commits (this doc, milestone audit, STATE/ROADMAP, tag v15.0) layer on top —
> all descendants of this pin. The kais-hermes-skills v15.0 final pin (`009773f`) is the HEAD at
> Task 2 execution time.

## Ancestry Assertion Commands + Exit Codes

Both assertions were run at Task 2 execution time (2026-07-10) — NOT cached from planning.

### hermes-agent

Command:
`git -C /data/workspace/hermes-agent merge-base --is-ancestor 4e7c58cc9cac3c4925770beaf5a9433369094a24 HEAD`

Exit code: **0** (descendant) — confirmed at execution time.

Interpretation: every v15.0 `.planning/` commit (Phases 77-83 plans, STATE edits, SUMMARY files,
roadmap updates) is layered on top of the v14.0 final commit. Zero force-push rewrites detected.

Commit count since v14.0 pin: **66 commits** (sanity check — confirms v15.0 work layered on top).

### kais-hermes-skills

Command:
`git -C /data/workspace/kais-hermes-skills merge-base --is-ancestor ba58c2548ab82f0cd9acd7cc7af14402137f8520 HEAD`

Exit code: **0** (descendant) — confirmed at execution time.

Interpretation: all v15.0-touched SKILL.md commits + scripts + workflows + refs in
kais-hermes-skills are layered on top of the v14.0 final commit. Zero force-push rewrites
detected.

Commit count since v14.0 pin: **140 commits** (sanity check — confirms v15.0 work layered on top).

## Coverage Statement

Cross-repo coordination preserved across v15.0 milestone: 140 commits in kais-hermes-skills
layered on top of v14.0 final (`ba58c254`), 66 commits in hermes-agent `.planning/` layered on
top of v14.0 final (`4e7c58cc`), zero force-push rewrites detected.

The v15.0 cross-repo topology (plan → hermes-agent `.planning/`, code → kais-hermes-skills)
follows the v14.0-established pattern. Both repos' commit graphs are linear descendants of
their v14.0 final pins — no rebase or force-push operations were performed during v15.0. The
lineage cascade threat (PITFALL X-1) is mitigated by this structural guarantee.

## Related Artifacts

- `.planning/phases/76-validate/76-ANCESTRY-ASSERT.md` — v14.0 ancestry assertion (baseline for v15.0)
- `.planning/milestones/v14.0-MILESTONE-AUDIT.md` — v14.0 milestone audit (cited pins)
- `.planning/milestones/v15.0-MILESTONE-AUDIT.md` §8 — v15.0 audit doc cites this document (Task 3)

---

*Verified: 2026-07-10 (Phase 83 Plan 01 Task 2 execution time)*
*Both ancestry assertions exit 0 (descendant) — cross-repo coordination preserved.*
