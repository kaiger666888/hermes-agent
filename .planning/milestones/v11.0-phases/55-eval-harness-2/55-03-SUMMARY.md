---
phase: 55-eval-harness-2
plan: 03
subsystem: testing
tags: [eval, dry-run-first, p5-mitigation, p14-mitigation, invariant, curator, ast-walk, tdd]

# Dependency graph
requires:
  - phase: 54-fitness-battery-1
    provides: Phase 54 bias canary (sister safety module) — this plan completes the dry-run-first half of P5 mitigation
provides:
  - "run_curator_review() defaults to dry_run=True (live writes require explicit dry_run=False opt-in)"
  - "Defensive None-check: dry_run=None / missing → treated as True (defense-in-depth)"
  - "AST-walk non-bypassable invariant test (mirrors v6.0 TestNonBypassableHumanInLoop pattern)"
  - "tests/v11-dry-run-first/ test suite (12 tests: 5 behavior + 4 AST-walk + 3 sanity)"
affects:
  - 55-04-schema-migration (will reuse the same dry_run: bool = True default + AST-walk pattern)
  - v11.0 PoC §4.6 acceptance check (curator default mode zero writes)
  - future curator changes (AST-walk will fail the build if a bypass path is introduced)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dry-run-first invariant: default value True + defensive None-check + AST-walk non-bypass test (P5 mitigation pattern)"
    - "AST-walk guard detection recognizes BOTH `if not dry_run:` (direct) and `if dry_run: ... else: <write>` (indirect via else-branch) — semantically equivalent"
    - "AST-walk parent_map keyed by id(node) — Python dict membership on AST nodes falls back to id-based hashing, but explicit id() tracking is more readable"

key-files:
  created:
    - "tests/v11-dry-run-first/__init__.py"
    - "tests/v11-dry-run-first/conftest.py"
    - "tests/v11-dry-run-first/test_default_dry_run.py"
    - "tests/v11-dry-run-first/test_ast_walk_non_bypass.py"
  modified:
    - "agent/curator.py"
    - "tests/agent/test_curator.py"
    - "tests/agent/test_curator_backup.py"

key-decisions:
  - "Default flip from dry_run: bool = False → True is the primary mitigation; defensive None-check is defense-in-depth"
  - "maybe_run_curator (auto-loop) now defaults to dry-run — auto-curation gated behind explicit operator opt-in. This is intentional per P5 mitigation: silent hallucinated writes from the auto-loop were the failure mode."
  - "AST-walk recognizes BOTH `if not dry_run:` (direct) AND `if dry_run: ... else: <write>` (indirect). The latter is semantically identical but lacks a `not dry_run` ancestor in the AST."
  - "Existing tests that asserted live-mode behavior (state mutation, snapshot creation) updated to pass dry_run=False explicitly — these were intentionally broken by the flip per plan Task 1 <action> step 5."

patterns-established:
  - "Dry-run-first invariant pattern: signature default True + None-check + AST-walk test. Future write paths (e.g. 55-04 schema migration script) reuse this pattern."
  - "AST-walk guard patterns: direct (`ast.If(test=UnaryOp(Not, Name(dry_run)))`) + indirect (`ast.If(test=Name(dry_run))` with call in orelse). Both count as valid `not dry_run` guards."

requirements-completed: [EVAL-06]

# Metrics
duration: 8min
completed: 2026-07-07
---

# Phase 55 Plan 03: Dry-Run-First Invariant (EVAL-06) Summary

**Curator `run_curator_review()` default flipped from `dry_run=False` → `True` + defensive None-check + AST-walk non-bypassable test mirroring v6.0 `TestNonBypassableHumanInLoop` pattern**

## Performance

- **Duration:** 8 min
- **Started:** 2026-07-07T10:23:26Z
- **Completed:** 2026-07-07T10:31:36Z
- **Tasks:** 2 (both TDD: RED → GREEN → test bugfix refinement)
- **Files modified:** 5 (1 source + 2 existing tests + 2 new test scaffolding files)
- **Tests:** 12 new tests + 3 existing tests updated; full curator + dry-run-first suite = 162 tests green

## Accomplishments

- **Dry-run-first default enforced as a value, not a convention.** `run_curator_review()` now defaults to `dry_run=True`. Callers MUST pass `dry_run=False` explicitly for live writes. P5 mitigation (curator failure modes) is now structurally enforced.
- **Defense-in-depth via None-check.** If `dry_run=None` is passed (or the kwarg is omitted and somehow defaults to None), the function treats it as True. Caller cannot accidentally trigger live writes.
- **AST-walk non-bypassable invariant test.** Static analysis of `agent/curator.py` verifies every write-path call site (`append_audit`, `apply_automatic_transitions`, `apply_patch_transaction`) is structurally nested inside an `if not dry_run:` guard. Future contributors adding unguarded write paths trigger immediate build failure.
- **Banner visibility in dry-run mode.** Default-mode invocation logs the existing `CURATOR_DRY_RUN_BANNER` via `logger.info()` and surfaces it via `on_summary` callback. Operators see "DRY-RUN — REPORT ONLY" so they know how to enable live writes.
- **Live mode preserved.** Explicit `dry_run=False` invocation runs the full deterministic prune + LLM consolidation fork exactly as before — verified by the existing test suite (162 tests green).

## Task Commits

Each task was committed atomically:

1. **Task 1 RED phase** — `f8a6aafab` (test): Added failing EVAL-06 dry-run-first invariant tests. 12 tests asserting default=True + zero-mutation in default mode + AST-walk structure. All failed against the unmodified curator.
2. **Task 1 GREEN phase** — `f5a74b834` (feat): Flipped `dry_run: bool = False → True` + defensive None-check + CURATOR_DRY_RUN_BANNER logging. Updated 3 existing tests that asserted live-mode behavior to pass `dry_run=False` explicitly.
3. **Task 2 AST-walk bugfix** — `4995541a1` (test): Fixed parent-chain id tracking + added else-branch pattern recognition in the AST-walk. Recognized that `if dry_run: ... else: <write>` is semantically equivalent to `if not dry_run: <write>`.

**Plan metadata:** (pending — final docs commit below)

## Files Created/Modified

### Created
- `tests/v11-dry-run-first/__init__.py` — Package marker.
- `tests/v11-dry-run-first/conftest.py` — `hermes_home_tmp` (autouse), `mock_audit_chain`, `mock_apply_automatic_transitions` fixtures.
- `tests/v11-dry-run-first/test_default_dry_run.py` — 5 behavior tests mapping 1:1 to plan Task 1 `<behavior>`.
- `tests/v11-dry-run-first/test_ast_walk_non_bypass.py` — 4 AST-walk tests + 2 sanity tests (mirrors v6.0 `TestNonBypassableHumanInLoop`).

### Modified
- `agent/curator.py` — Signature default flip + None-check + banner log + docstring update (5 lines added, 1 changed).
- `tests/agent/test_curator.py` — `test_run_review_records_state` + `test_run_review_skips_llm_when_consolidate_off` updated to pass `dry_run=False` explicitly.
- `tests/agent/test_curator_backup.py` — `test_real_run_takes_pre_snapshot` updated to pass `dry_run=False` explicitly.

## Decisions Made

1. **Auto-loop default flip is intentional.** `agent/curator.py:maybe_run_curator` (the auto-curaton entry point) calls `run_curator_review(on_summary=on_summary)` with no `dry_run` arg → after the flip, this becomes dry-run. Operators must wire explicit `dry_run=False` to enable live auto-runs. This is the core P5 mitigation: silent hallucinated writes from the auto-loop were the failure mode the dry-run-first invariant gates.

2. **AST-walk recognizes else-branch as equivalent guard.** The initial AST-walk only matched `if not dry_run:` directly. The actual curator code uses `if dry_run: ... else: <write>` for the main prune path. The test was updated to recognize both patterns as semantically equivalent (the `else` branch of `if dry_run:` is structurally the same as `if not dry_run:`).

3. **AST-walk parent_map uses id() tracking.** Initial implementation did `while node in parent_map:` but parent_map is `dict[int, ast.AST]` (keyed by id). Switched to `while current_id in parent_map:` with explicit id() bookkeeping.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] AST-walk parent-chain id tracking was broken**
- **Found during:** Task 2 (AST-walk test verification)
- **Issue:** Initial `_is_inside_not_dry_run_guard` did `while node in parent_map:` but `parent_map` is `dict[int, ast.AST]` keyed by `id(node)`. The dict-membership check on an AST node never matched because the dict keys are ints. The walk silently terminated at depth 0, returning False for every call site.
- **Fix:** Track `current_id = id(call_node)` and check `current_id in parent_map`, advancing `current_id = id(parent)` each iteration.
- **Files modified:** `tests/v11-dry-run-first/test_ast_walk_non_bypass.py`
- **Verification:** `test_apply_automatic_transitions_calls_are_dry_run_guarded` now correctly recognizes the call site at line 1564 as nested inside `if dry_run:` (else-branch pattern).
- **Committed in:** `4995541a1` (Task 2 AST-walk bugfix commit)

**2. [Rule 1 - Bug] AST-walk missed else-branch guard pattern**
- **Found during:** Task 2 (AST-walk test verification)
- **Issue:** `apply_automatic_transitions` at line 1564 lives inside the `else:` branch of `if dry_run: ... else: <write>`. This is semantically identical to `if not dry_run: <write>` but has no `not dry_run` ancestor in the AST — only `if dry_run:` with the call inside `orelse[]`.
- **Fix:** Added Pattern 2 detection in `_is_inside_not_dry_run_guard`: if parent is `ast.If` with `_test_is_dry_run(parent.test)` AND `last_node in parent.orelse`, treat as guarded. The `last_node` is tracked explicitly during the walk so we know which direct child of `parent` we ascended from.
- **Files modified:** `tests/v11-dry-run-first/test_ast_walk_non_bypass.py`
- **Verification:** Test now passes for the `else:` branch call site.
- **Committed in:** `4995541a1` (Task 2 AST-walk bugfix commit)

**3. [Rule 3 - Blocking] Existing curator tests broke (intentional, per plan)**
- **Found during:** Task 1 (post-flip caller-impact verification)
- **Issue:** Three existing tests called `run_curator_review(synchronous=True)` without `dry_run=False`, expecting live-mode behavior (state mutation, snapshot creation). These broke because the default is now dry-run.
- **Fix:** Updated each to pass `dry_run=False` explicitly, per plan Task 1 `<action>` step 5: "Any tests that called `run_curator_review()` without args expecting live behavior — these BREAK (intentionally, per EVAL-06). Update them to pass `dry_run=False` explicitly."
- **Files modified:** `tests/agent/test_curator.py` (`test_run_review_records_state`, `test_run_review_skips_llm_when_consolidate_off`), `tests/agent/test_curator_backup.py` (`test_real_run_takes_pre_snapshot`)
- **Verification:** Full curator + dry-run-first suite (162 tests) green.
- **Committed in:** `f5a74b834` (Task 1 GREEN phase commit)

---

**Total deviations:** 3 auto-fixed (2 bug fixes in AST-walk test, 1 blocking existing-test update)
**Impact on plan:** All auto-fixes necessary for correctness. The AST-walk bugs were undiscovered until runtime verification — exactly the failure mode the AST-walk test exists to catch in production code, now also catching bugs in itself. No scope creep.

## Issues Encountered

- **Absolute-path safety (#3099).** Initial Edit call used `/data/workspace/hermes-agent/agent/curator.py` (main repo) instead of the worktree path. The edit landed in the main repo, was detected via test runtime (tests in the worktree couldn't see the change), and was reverted before any commit. Subsequent edits used the worktree-rooted absolute path explicitly.
- **Worktree base is older than main repo.** The worktree was branched from `d2c53ff558` which predates v6.0 self-evolution milestone. The worktree's `agent/curator.py` does NOT contain `_feedback_scan_phase` or v6.0 `append_audit` calls — only `apply_automatic_transitions`. The AST-walk test's sanity minimum was relaxed from 2 to 1 write-path call site accordingly. The structural pattern is identical to main repo; only line numbers differ.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **EVAL-06 acceptance is complete.** Invoking `run_curator_review()` without explicit `dry_run=False` produces zero state mutation. AST-walk fails loudly if a bypass path is introduced.
- **55-04 schema migration** can reuse the same pattern: `dry_run: bool = True` default + defensive None-check + AST-walk test for the migration script's write paths. The pattern is documented in `tests/v11-dry-run-first/test_ast_walk_non_bypass.py` (see `_is_inside_not_dry_run_guard` docstring).
- **v11.0 PoC §4.6 acceptance check** is satisfied: default mode zero writes + `--apply-memory` mode (analog of `dry_run=False`) writes proceed with audit log.

## Threat Surface Scan

No new security-relevant surface introduced. The change is a default-value flip — no new endpoints, no new auth paths, no new file access patterns, no schema changes at trust boundaries. The threat model in 55-03-PLAN.md covers the two relevant threats (T-55-08 elevation via default bypass, T-55-09 tampering via future unguarded path) — both mitigated.

## TDD Gate Compliance

- [x] RED commit exists: `f8a6aafab` (test: failing EVAL-06 dry-run-first invariant tests)
- [x] GREEN commit exists after RED: `f5a74b834` (feat: flip default + defensive check)
- [x] Additional test-bugfix commit after GREEN: `4995541a1` (test: AST-walk parent-chain id tracking fix)

RED phase genuinely failed before implementation (verified via `pytest` output showing `Constant(value=False)` mismatch). GREEN phase genuinely passed after implementation (12/12 tests green). No TDD gate violations.

---
*Phase: 55-eval-harness-2*
*Completed: 2026-07-07*

## Self-Check: PASSED

All claimed files exist on disk. All commit hashes verified present in git log. Signature default `dry_run: bool = True` confirmed at `agent/curator.py:1483`. Defensive None-check `if dry_run is None:` confirmed at `agent/curator.py:1527`.
