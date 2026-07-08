---
phase: 65-curator-live-guards
plan: 03
subsystem: curator-self-evolution
tags: [curator, smoke, integration, bias-canary, audit-chain, operator-runbook]
requires:
  - "Phase 65 Plan 01 (run_bias_canary_pre_check + append_audit tick_mode extension)"
  - "Phase 65 Plan 02 (_cmd_evolve CLI handler + evolve subparser + canary failure UX)"
provides:
  - "65-SMOKE.md — end-to-end smoke evidence for all 3 Phase 65 SCs (CURATE-01/02/03)"
  - "Operator runbook snippet for Phase 66 first live tick + 24h rollback window"
affects:
  - "Phase 66 (CURATE-LIVE-TICK): 1st actual live tick uses the documented runbook"
tech-stack:
  added: []
  patterns:
    - "Smoke evidence uses isolated HERMES_HOME (mktemp -d) — never touches operator's real ~/.hermes state (T-65-11 mitigation)"
    - "Canary abort path covered authoritatively by unit tests when CLI override is not exposed (per Plan 65-03 Task 1 action)"
key-files:
  created:
    - .planning/phases/65-curator-live-guards/65-SMOKE.md
    - .planning/phases/65-curator-live-guards/deferred-items.md
  modified: []
decisions:
  - "SC#2 abort path covered by 3 authoritative unit tests instead of smoke reproduction — CLI does not expose a fixtures_path override, so reproducing a canary-fail scenario requires monkeypatch (which is what the unit tests already do)"
  - "Pre-existing test_curator_stats.py failures (18 tests) logged to deferred-items.md rather than fixed — root cause is v5/v6 doc-tree removal in commit f10495332, unrelated to Phase 65 scope"
  - "Smoke uses isolated HERMES_HOME per T-65-11 mitigation; no operator state touched"
requirements-completed: [CURATE-01]
metrics:
  duration: PT4M
  completed: 2026-07-08
---

# Phase 65 Plan 03: Curator Live Guards — Wave 2 Integration Smoke Summary

Wave 2 of Phase 65 closes the last Nyquist verification cell (task 65-03-01) by running the CLI as an operator would (subprocess) and capturing end-to-end evidence that the 3 Phase 65 success criteria hold: dry-run default works, canary gates the live path, and audit chain records live ticks with the new `tick_mode` field.

---

## Performance

- **Duration:** ~4 min
- **Started:** 2026-07-08T03:52:55Z
- **Completed:** 2026-07-08T03:57:40Z
- **Tasks:** 1
- **Files modified:** 2 (both new)

## Accomplishments

- **SC#1 verified end-to-end:** `hermes curator evolve` (no flag) prints `DRY-RUN` marker to stdout, exits 0, writes no audit entry. Operator-visible signal unambiguous.
- **SC#2 verified end-to-end:** `hermes curator evolve --live` runs the canary pre-check (caught 4/5, passed threshold), proceeds to live tick, exits 0. Abort path (exit 2 + structured `BIAS_CANARY_FAILED` stderr) covered by 3 authoritative unit tests.
- **SC#3 verified end-to-end:** Live tick appended well-formed audit entry with `tick_mode: "live"`, `canary_pass: true`, `caught_count: 4`, `mutation_summary` populated; `verify_chain` exits 0. Backward-compat + mixed-schema chain integrity proven by 3 unit tests.
- **Operator runbook documented:** 65-SMOKE.md includes a Phase 66 runbook (dry-run preview → live tick → audit verify → 24h rollback window → escape hatch).

## Task Commits

Each task was committed atomically:

1. **Task 1: Run end-to-end smoke for SC#1/SC#2/SC#3** - `51323b312` (docs)

**Plan metadata:** (no separate metadata commit — SUMMARY committed alongside per parallel execution pattern)

## Files Created/Modified

- `.planning/phases/65-curator-live-guards/65-SMOKE.md` — End-to-end smoke evidence for all 3 Phase 65 SCs with command + output + verdict, plus operator runbook for Phase 66 first live tick.
- `.planning/phases/65-curator-live-guards/deferred-items.md` — Logs 18 pre-existing `test_curator_stats.py` failures (v5/v6 doc-tree removal in `f10495332`, unrelated to Phase 65).

## Decisions Made

- **SC#2 abort path coverage strategy:** The CLI does not expose a `--fixtures-path` override flag, so reproducing a canary-fail scenario from the shell requires either monkeypatching (which the unit tests already do) or pointing at an alternative fixtures file (not CLI-accessible). Per Plan 65-03 Task 1 `<action>` guidance, the smoke proves the happy canary-pass path and the 3 authoritative unit tests (`test_live_aborts_on_canary_failure`, `test_canary_failure_message_format`, `test_canary_failure_does_not_append_audit`) cover the abort path. This avoids duplicating unit-test infrastructure in the smoke artifact.
- **Pre-existing stats test failures:** 18 tests in `test_curator_stats.py` fail because they assert v5/v6 milestone doc-tree structure (`skills/movie-experts/_shared/v6-feedback-loop-architecture.md`) that was removed in commit `f10495332` ("migrate kais skills + plugins to kais-skills repo"). Root cause is unrelated to Phase 65. Logged to `deferred-items.md` per executor SCOPE BOUNDARY rule rather than fixed in-line.
- **Smoke isolation:** Smoke runs in `mktemp -d` HERMES_HOME per T-65-11 mitigation. No operator state touched. The live tick against the isolated empty state correctly shows zero mutations (`mutation_summary: {checked: 0, archived: 0, ...}`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking Issue] Worktree branch base was stale (pre-Wave 0/1)**
- **Found during:** Agent startup (worktree_branch_check)
- **Issue:** Worktree HEAD was at `605727e3b` (a feature branch), but Phase 65 Wave 0/1 work lives at `3452ee914` on main. Test files `tests/agent/test_curator_live_guards.py`, `tests/hermes_cli/test_curator_evolve_cli.py`, and the fixtures were absent; `_cmd_evolve` and `run_bias_canary_pre_check` were not in their modules.
- **Fix:** Per the `<worktree_branch_check>` sanctioned `git reset --hard`, reset the worktree to `3452ee914c3e6cdc3de6eb99ed2b588dd0279174`. Working tree was clean before reset (no WIP to lose). All Wave 0 + Wave 1 primitives and tests now present.
- **Files modified:** None functionally — git history recovery only.
- **Verification:** `python3 -m pytest tests/agent/test_curator_live_guards.py tests/hermes_cli/test_curator_evolve_cli.py tests/hermes_cli/test_curator_cli.py tests/v11-bias-canary/ -x -q` → 89 passed.
- **Committed in:** (recovery, pre-Task 1)

**2. [Rule 3 — Blocking Issue] Write tool resolved absolute path against main repo instead of worktree (#3099)**
- **Found during:** Task 1 (writing 65-SMOKE.md)
- **Issue:** First Write call for `65-SMOKE.md` and `deferred-items.md` used paths beginning with `/data/workspace/hermes-agent/.planning/...`. The Write tool resolved these against the main repo at `/data/workspace/hermes-agent/`, not the worktree at `/data/workspace/hermes-agent/.claude/worktrees/agent-ad12c5a40d859b1a5/`. Files landed in the main repo, missing from the worktree.
- **Fix:** Used `git rev-parse --show-toplevel` to derive the worktree root, then `mv` the misplaced files from `/data/workspace/hermes-agent/.planning/...` to `$WT_ROOT/.planning/...`. Verified gate passes from worktree cwd.
- **Files modified:** None functionally — file relocation only.
- **Verification:** `test -f "$WT_ROOT/.planning/phases/65-curator-live-guards/65-SMOKE.md"` → found; `grep -c "SC#1\|SC#2\|SC#3" ...` → 3+ matches.
- **Committed in:** (recovery, pre-Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both auto-fixes were git/path recovery operations with no functional changes. No scope creep. Plan executed as written once primitives were accessible.

## Issues Encountered

- **18 pre-existing `test_curator_stats.py` failures:** Discovered during the full Phase 65 regression run. These are NOT caused by Phase 65 work — they assert v5/v6 doc-tree structure removed in `f10495332`. Logged to `deferred-items.md` and excluded from the canonical Phase 65 verification surface. The 150 curator + bias canary + evolve CLI tests all pass.

## Known Stubs

None. The smoke artifact is documentation only — no executable code, no stubs.

## Threat Flags

None. Smoke output captured in 65-SMOKE.md contains only aggregate counts + DRY RUN markers + exit codes + audit entry JSON (no PII, no secrets, no operator-identifying data — T-65-12 accept disposition honored).

## Next Phase Readiness

- **Phase 66 (CURATE-LIVE-TICK)** can use the operator runbook in `65-SMOKE.md` to run the first actual live tick against the operator's real `~/.hermes` state.
- All Phase 65 primitives (Wave 0) + CLI surface (Wave 1) + smoke evidence (Wave 2) are in place.
- The 18 deferred `test_curator_stats.py` failures should be addressed by a v5.0/v6.0 cleanup task (NOT a Phase 65 blocker).

---

## Self-Check: PASSED

Files verified to exist:
- FOUND: .planning/phases/65-curator-live-guards/65-SMOKE.md
- FOUND: .planning/phases/65-curator-live-guards/deferred-items.md

Commits verified to exist:
- FOUND: 51323b312 (docs(65-03): end-to-end smoke evidence for curator live guards)

---

*Phase: 65-curator-live-guards*
*Completed: 2026-07-08*
