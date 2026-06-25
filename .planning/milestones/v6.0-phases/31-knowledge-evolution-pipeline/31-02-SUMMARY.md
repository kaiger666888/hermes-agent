---
phase: 31-knowledge-evolution-pipeline
plan: 02
subsystem: knowledge-evolution-cli
tags: [evolution, cli, argparse, human-in-loop, lazy-import, found-08, ast-invariant]
requirements: [EVOL-01, EVOL-03, EVOL-04, EVOL-05]
requires:
  - "agent/evolution/* (P31 Plan 01 — public API: aggregate_feedback, PatchRecord, apply_patch_transaction, etc.)"
  - "hermes_cli/feedback.py:register_cli (P28/29 — existing 4 subcommands preserved)"
  - "agent/feedback_store.py:FeedbackStore (P29 — input source for evolve)"
  - "skills/movie-experts/_eval/gate.py (P30 — subprocess via --reports-dir; NO --report flag exists)"
  - "hermes_constants.get_hermes_home (canonical HERMES_HOME)"
provides:
  - "hermes_cli/feedback.py extended with 6 new subcommands + 6 _cmd_* handlers"
  - "_cmd_evolve (EVOL-01): --skill, --model, --dry-run, --insights-only"
  - "_cmd_review_queue / _cmd_show_patch / _cmd_reject (EVOL-03)"
  - "_cmd_approve (EVOL-04 non-bypassable + EVOL-05 atomic apply)"
  - "_cmd_rollback (EVOL-05 git revert)"
  - "_resolve_repo_root / _resolve_evolution_dir / _run_eval_gate helpers"
  - "tests/hermes_cli/test_evolution_cli.py (27 tests including TestNonBypassableHumanInLoop)"
affects:
  - "No runtime modules — all agent.evolution imports are LAZY (inside handler bodies)"
tech_stack:
  added: []
  patterns:
    - "Lazy import inside handler bodies (preserves runtime isolation — grep at module top returns 0)"
    - "argparse subparser extension (additive — 6 new subparsers after existing 4)"
    - "Plan-checker Warning 2/3 explicit-failure stub pattern (Task 1 stubs exit 2 with 'not yet implemented — see Task 2')"
    - "ast-walk structural invariant test (TestNonBypassableHumanInLoop)"
    - "subprocess argv-list only — never shell=True (T-31-17)"
    - "Gate subprocess via --reports-dir (Warning 4: --report flag does NOT exist in gate.py main())"
    - "Non-bypassable human-in-loop: --yes is REQUIRED for approve + rollback (no default-yes path)"
    - "SHA validation before git revert (T-31-14)"
    - "Temp patch file with try/finally unlink (no working-tree litter)"
key_files:
  created:
    - tests/hermes_cli/test_evolution_cli.py
  modified:
    - hermes_cli/feedback.py
    - .planning/phases/31-knowledge-evolution-pipeline/31-RESEARCH.md
    - .planning/phases/31-knowledge-evolution-pipeline/31-VALIDATION.md
decisions:
  - "Plan-checker Warning 4 adaptation: gate.py main() has --reports-dir, NOT --report. _run_eval_gate uses --reports-dir <dir> and reads <dir>/<patch_id>.json"
  - "Plan-checker Warning 2/3: Task 1 stubs for _cmd_approve/_cmd_rollback explicitly fail with exit 2 + 'not yet implemented — see Task 2' (NOT silent return 0). Prevents operator false-positive if execution interrupts."
  - "Lazy-import strategy: all `from agent.evolution import ...` live INSIDE handler function bodies. grep at module top returns 0 matches — preserves the runtime-isolation invariant."
  - "TestNonBypassableHumanInLoop uses ast.walk (not grep) for precise structural enforcement — tracks FunctionDef stack to verify every apply_patch_transaction Call is enclosed in _cmd_approve."
  - "--yes is REQUIRED (not just default-prompt): approve without --yes prints 'approval required (pass --yes to confirm)' + exit 1 WITHOUT calling apply_patch_transaction. Same for rollback ('rollback requires --yes')."
  - "ApplyError keeps patch pending: on apply failure, move_patch is NOT called — patch stays in queue.jsonl so operator can retry or reject."
  - "SHA validation before revert: `git rev-parse --verify <sha>` runs BEFORE `git revert` to fail fast on typos / injection (T-31-14)."
metrics:
  duration: "~30 min"
  completed: "2026-06-24"
  tasks_total: 3
  tasks_completed: 3
  commits: 3
  files_created: 1
  files_modified: 3
  tests_added: 27
---

# Phase 31 Plan 02: Knowledge Evolution CLI + Integration Summary

Wires the Plan 01 `agent/evolution/` engine into 6 operator-facing CLI subcommands appended to `hermes_cli/feedback.py:register_cli`. EVOL-04 non-bypassable human-in-loop is enforced structurally via `TestNonBypassableHumanInLoop` (ast-walk proves only `_cmd_approve` calls `apply_patch_transaction`). All `agent.evolution` imports are LAZY (inside handler bodies) so runtime isolation grep returns 0 matches at module top.

## What Was Built

### hermes_cli/feedback.py — 6 new subparsers + 6 handlers (additive)

**register_cli extension** — appends 6 subparsers AFTER the existing 4 (import/watch/submit/rebuild-index). `TestRegisterCliPreservesExistingSubcommands` verifies no regression.

| Subcommand | Handler | Flags | Requirement |
|------------|---------|-------|-------------|
| `evolve` | `_cmd_evolve` | `--skill` (req), `--model`, `--dry-run`, `--insights-only` | EVOL-01 |
| `review-queue` | `_cmd_review_queue` | `--skill`, `--status` (pending\|applied\|rejected) | EVOL-03 |
| `show-patch` | `_cmd_show_patch` | positional `patch_id` | EVOL-03 |
| `approve` | `_cmd_approve` | positional `patch_id`, `--yes` (REQUIRED) | EVOL-04 + EVOL-05 |
| `reject` | `_cmd_reject` | positional `patch_id`, positional `reason` | EVOL-03 |
| `rollback` | `_cmd_rollback` | positional `commit_sha`, `--yes` (REQUIRED) | EVOL-05 |

**Helpers:**
- `_resolve_repo_root()` — walks up from cwd looking for `.git`; SystemExit if not in a repo.
- `_resolve_evolution_dir()` — `get_hermes_home() / "skills" / ".feedback" / "evolution"`; mkdir parents=True.
- `_gate_script_path()` — resolves gate.py via `__file__` (hyphenated `movie-experts` path is not importable).
- `_run_eval_gate(*, patch_path, skill_id, repo_root, reports_dir, patch_id_for_report)` — subprocess `python gate.py --patch <p> --skill <s> --reports-dir <d>`; parses `<reports_dir>/<patch_id>.json` for the score.

**`_cmd_evolve` paths:**
- **No feedback:** `store.query()` returns empty → print `no feedback for skill <id>; nothing to evolve` → exit 0.
- **`--dry-run`:** writes a single stub InsightRecord (theme=`[dry-run] stub for <skill>`) to insights.jsonl WITHOUT calling the LLM. Offline testing path.
- **`--insights-only`** (RESEARCH Q3 RESOLVED): runs LLM aggregation, writes insights.jsonl, exits WITHOUT generating patches or running the gate.
- **Full pipeline:** aggregate_feedback → for each insight: generate_additive_diff → write temp .patch → `_run_eval_gate` subprocess → append_patch (pass) or append_failed_gate (fail) → finally unlink temp.

**`_cmd_approve` (EVOL-04 + EVOL-05) — the SOLE apply_patch_transaction caller:**
1. If not `args.yes`: print `approval required (pass --yes to confirm)` → exit 1 (NO apply call).
2. `read_queue(status="pending")` → find match by patch_id; if missing → exit 1.
3. Write `unified_diff` to temp `.patch` file.
4. `build_commit_message(insight_summary, feedback_ids, eval_verdict, eval_mean_delta)`.
5. `apply_patch_transaction(patch_path, repo_root, commit_message)` — Plan 01's 6-step atomic transaction.
6. On `ApplyError`: working tree auto-reverted; print `apply failed (working tree restored): <exc>` → exit 1 (patch STAYS pending).
7. On success: `move_patch(target_status="applied", commit_sha=result.commit_sha)` → print `applied <id> as commit <sha[:12]>` → exit 0.
8. `finally: patch_tmp.unlink(missing_ok=True)`.

**`_cmd_rollback` (EVOL-05):**
1. If not `args.yes`: print `rollback requires --yes` → exit 1.
2. `git rev-parse --verify <sha>` — fail fast on invalid SHA (T-31-14).
3. `git revert <sha> --no-edit` (argv-list, no shell=True).
4. On failure: print stderr tail (400 chars max) → exit 1.
5. On success: print `reverted <sha> as <revert_sha[:12]>`.

### tests/hermes_cli/test_evolution_cli.py — 27 tests across 11 classes

| Class | Tests | Scope |
|-------|-------|-------|
| `TestRegisterCliPreservesExistingSubcommands` | 7 | 4 existing + 6 new subcommands resolve; flag parsing |
| `TestEvolveCmdDryRun` | 1 | --dry-run writes stub insight without LLM call |
| `TestEvolveCmdInsightsOnly` | 1 | --insights-only writes insights.jsonl, skips queue.jsonl |
| `TestEvolveCmdNoFeedback` | 1 | empty FeedbackStore.query → friendly message + exit 0 |
| `TestEvolveCmdFullPipeline` | 1 | mock LLM + mock gate subprocess → queue.jsonl populated |
| `TestReviewQueueCmd` | 3 | empty, populated, skill-filtered |
| `TestShowPatchCmd` | 2 | happy path (full diff + rationale), not-found |
| `TestRejectCmd` | 2 | moves to rejected.jsonl, not-found exits non-zero |
| `TestApproveCmdRequiresYes` | 1 | no --yes → exit non-zero + apply_patch_transaction NOT called |
| `TestApproveCmdNotFound` | 1 | unknown patch_id → exit non-zero |
| `TestApproveCmdAppliesAndMoves` | 1 | --yes + valid patch → apply called + moved to applied.jsonl |
| `TestApproveCmdOnApplyError` | 1 | ApplyError → exit non-zero + move_patch NOT called (stays pending) |
| `TestRollbackCmdRequiresYes` | 1 | no --yes → exit non-zero + subprocess.run NOT called |
| `TestRollbackCmdInvalidSha` | 1 | invalid sha → exit non-zero |
| `TestRollbackCmdHappyPath` | 1 | real tmp git repo → revert commit appears in git log |
| `TestNonBypassableHumanInLoop` | 2 | ast-walk: only `_cmd_approve` calls apply_patch_transaction; runtime code (agent/, gateway/, run_agent.py, cli.py) has zero calls |

**Test count: 27** (matches plan estimate).

## EVOL-04 Non-Bypassable Human-In-Loop (CRITICAL)

The structural invariant is enforced by `TestNonBypassableHumanInLoop.test_only_cmd_approve_calls_apply_patch_transaction`:

```python
class _Walker(ast.NodeVisitor):
    def visit_Call(self, node: ast.Call) -> None:
        # Match apply_patch_transaction by name (Name or Attribute).
        if name == "apply_patch_transaction":
            enclosing = self.func_stack[-1] if self.func_stack else "<module>"
            if enclosing != "_cmd_approve":
                violators.append(f"line {node.lineno}: ...")
```

The test parses `hermes_cli/feedback.py` with `ast.parse`, walks every `Call` node, and asserts each `apply_patch_transaction` invocation is enclosed in a `FunctionDef` named `_cmd_approve`. If a future contributor adds it inside `_cmd_evolve` (or anywhere else), the test fails.

A second test (`test_apply_patch_transaction_not_called_in_agent_or_runtime`) walks `agent/`, `gateway/`, `run_agent.py`, `cli.py` and asserts zero calls (excluding the evolution subpackage itself, which owns the definition).

## Lazy-Import Strategy (Runtime Isolation)

Every `from agent.evolution import ...` lives INSIDE a handler function body — never at module top. This preserves the invariant:

```bash
$ grep -n "^from agent.evolution\|^import agent.evolution" hermes_cli/feedback.py
# (no output — exit 1)
```

This means importing `hermes_cli.feedback` (which happens at Hermes startup) does NOT trigger import of `agent.evolution` (which would pull in `openai`, `pydantic`, etc.). The evolution modules load ONLY when the operator invokes one of the 6 new subcommands.

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| `f1bbab060` | feat | Task 1: 4 evolution CLI handlers + 6 subparsers (approve/rollback as explicit-failure stubs per Warning 2/3) |
| `a976905b5` | feat | Task 2: _cmd_approve + _cmd_rollback real implementations + TestNonBypassableHumanInLoop |
| `8cb89237d` | docs | Task 3: RESEARCH.md Open Questions RESOLVED + VALIDATION.md sign-off |

## TDD Gate Compliance

Both Task 1 and Task 2 carried `tdd="true"` frontmatter and followed RED/GREEN cycles:

- **Task 1 RED:** 18 tests written first; first run failed (`AssertionError: new subcommand 'evolve' not registered`).
- **Task 1 GREEN:** 4 handlers implemented + 2 stubs; 18/18 tests pass.
- **Task 2 RED:** 9 Task-2-scope tests added; first run failed against stubs (`AssertionError: assert '--yes' in 'rollback: not yet implemented — see Task 2'`).
- **Task 2 GREEN:** Real approve/rollback implementations; 27/27 tests pass.

Task 3 was plain `type="auto"` (verification + docs).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking Issue] gate.py has `--reports-dir`, NOT `--report` (Plan-checker Warning 4)**
- **Found during:** Task 1 read_first (gate.py:1255-1390 inspection)
- **Issue:** The plan's Task 1 action step 12 specified `--report <path>` for the gate subprocess. Inspection of `skills/movie-experts/_eval/gate.py:main()` revealed NO `--report` flag exists — only `--reports-dir <dir>` (the gate writes `<dir>/<patch_id>.json`).
- **Fix:** `_run_eval_gate` uses `--reports-dir <reports_dir>` and reads `<reports_dir>/<patch_id>.json` for the score. Added a `patch_id_for_report` parameter to derive the report filename.
- **Files modified:** hermes_cli/feedback.py (`_run_eval_gate`)
- **Commit:** f1bbab060

**2. [Rule 2 - Missing Critical Functionality] Dry-run test needed seeded feedback**
- **Found during:** Task 1 GREEN phase (test_dry_run_writes_stub_insight failed with "no feedback for skill")
- **Issue:** The dry-run path references `feedback[0]` for the evidence chain, but the test didn't seed feedback in the isolated store. The empty-feedback branch fired first.
- **Fix:** Test now patches `agent.feedback_store.FeedbackStore` to return a non-empty `query()` result before exercising the dry-run path.
- **Files modified:** tests/hermes_cli/test_evolution_cli.py
- **Commit:** f1bbab060

**3. [Rule 3 - Blocking Issue] VALIDATION.md referenced `test_aggregate.py` but Plan 01 shipped `test_insights.py`**
- **Found during:** Task 3 VALIDATION.md update
- **Issue:** VALIDATION.md's Per-Task Verification Map cited `tests/agent/evolution/test_aggregate.py` as the test path, but Plan 01 actually shipped the EVOL-01 tests in `test_insights.py` (per 31-01-SUMMARY).
- **Fix:** Updated VALIDATION.md entries to reference `test_insights.py` (the correct filename).
- **Files modified:** .planning/phases/31-knowledge-evolution-pipeline/31-VALIDATION.md
- **Commit:** 8cb89237d

## Isolation Verification

**Hermes runtime isolation:** `grep -rn "from agent.evolution\|import agent.evolution" run_agent.py agent/conversation_loop.py agent/prompt_builder.py agent/system_prompt.py agent/tool_executor.py agent/curator.py cli.py gateway/ 2>/dev/null | wc -l` returns **0**.

**Module-top isolation in feedback.py:** `grep -n "^from agent.evolution\|^import agent.evolution" hermes_cli/feedback.py` returns **0 matches** (all imports inside handler bodies).

**EVOL-04 structural isolation:** `TestNonBypassableHumanInLoop.test_only_cmd_approve_calls_apply_patch_transaction` passes — the ast-walk confirms every `apply_patch_transaction` Call is enclosed in `_cmd_approve`. The broader `test_apply_patch_transaction_not_called_in_agent_or_runtime` confirms zero calls in `agent/`, `gateway/`, `run_agent.py`, `cli.py`.

## FOUND-08 + Additive-Only Verification

- **FOUND-08 byte-intact (SC-5):** No SKILL.md changes from Plan 02 commits. `git diff --name-only HEAD~3 -- skills/movie-experts/ | grep -v _eval | grep -v _shared` returns empty. The byte-level frontmatter check lives in Plan 01's `apply_patch_transaction` and runs at every approve.
- **Additive-only (SC-6):** Universal check in Plan 01's `verify_additive_only`; runs inside every `apply_patch_transaction` invocation. Protected refs flagged with explicit SC-6 error message.

## Plan 01 Regression

After Plan 02 modifications: `python -m pytest tests/agent/evolution/` → **60/60 tests pass** (unchanged from Plan 01 green state). The new CLI layer is purely additive — no Plan 01 module was modified.

## Open Dependencies

- Phase 32 (Curator automated path) will invoke the same `aggregate_feedback` + `apply_patch_transaction` machinery but MUST still route commits through `_cmd_approve` (EVOL-04 non-bypassable). The `TestNonBypassableHumanInLoop` test enforces this — any P32 code that calls `apply_patch_transaction` outside `_cmd_approve` will fail the test.
- Live operator verification (manual): run `hermes feedback evolve --skill screenplay` against a populated FeedbackStore with a live OPENROUTER_API_KEY to confirm the LLM aggregation produces meaningful insights end-to-end.

## Self-Check

**Files created (verified to exist):**
- tests/hermes_cli/test_evolution_cli.py ✓

**Files modified (verified to exist):**
- hermes_cli/feedback.py ✓
- .planning/phases/31-knowledge-evolution-pipeline/31-RESEARCH.md ✓
- .planning/phases/31-knowledge-evolution-pipeline/31-VALIDATION.md ✓

**Commits (verified in git log):**
- f1bbab060 ✓
- a976905b5 ✓
- 8cb89237d ✓

**Test suite:** 27/27 Plan 02 CLI tests green; 60/60 Plan 01 regression tests green; 87/87 combined green.

**Verification gates:**
- `grep -rn "from agent.evolution\|import agent.evolution" run_agent.py agent/ cli.py gateway/ 2>/dev/null | wc -l` → 0 ✓
- `grep -n "^from agent.evolution\|^import agent.evolution" hermes_cli/feedback.py` → 0 matches ✓
- `TestNonBypassableHumanInLoop` → passes ✓
- `ruff check agent/evolution/ hermes_cli/feedback.py` → All checks passed ✓
- `git diff --name-only HEAD~3 -- skills/movie-experts/ | grep -v _eval | grep -v _shared` → empty ✓
- `grep -c "RESOLVED" .planning/phases/31-knowledge-evolution-pipeline/31-RESEARCH.md` → 3 ✓

## Self-Check: PASSED
