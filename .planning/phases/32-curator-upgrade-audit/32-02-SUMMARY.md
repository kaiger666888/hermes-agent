---
phase: 32-curator-upgrade-audit
plan: 02
subsystem: curator-cli-auto-apply
tags: [curator, cli, auto-apply, audit-log, delegation, p31-invariant, curate-04, curate-05]
requires:
  - P31-evolution (feedback CLI _cmd_approve / _cmd_review_queue / _cmd_reject + apply_patch_transaction)
  - P32-01 (agent/curator_audit.py append_audit + verify_chain + read_audit; agent/curator.py config getters; PatchRecord.auto_apply_eligible + confidence_score)
  - P31-TestNonBypassableHumanInLoop (structural invariant preserved UNCHANGED — Option A)
provides:
  - hermes_cli/curator.py:register_cli extension with 5 new subparsers (queue / approve / reject / audit-log / auto-apply-eligible)
  - _cmd_queue / _cmd_approve_curator / _cmd_reject_curator / _cmd_audit_log / _cmd_auto_apply_eligible handlers
  - _get_operator + _resolve_skill_from_patch helpers
  - CURATE-04 operator CLI surface (queue / approve / reject / audit-log + --verify)
  - CURATE-05 semi-automatic apply path (agent-created only, two-signal confidence, default OFF, bundled NEVER auto)
  - _cmd_approve in hermes_cli/feedback.py extended to call append_audit(action="apply") on success — single source of truth
  - TestStructuralInvariantPreserved ast-walk assertion in tests/hermes_cli/test_curator_cli.py
affects:
  - hermes_cli/curator.py (register_cli + 5 new handlers + 2 helpers + module docstring)
  - hermes_cli/feedback.py (_cmd_approve extended with audit-append call on successful apply)
  - tests/hermes_cli/test_curator_cli.py (NEW — 34 tests across 8 classes)
tech-stack:
  added: []  # no new deps — stdlib argparse + getpass + logging only
  patterns:
    - "Thin-wrapper delegation to P31 handlers (single source of truth for queue lifecycle)"
    - "Audit wiring inside _cmd_approve (RESEARCH A4 — every approve caller audited)"
    - "Architectural Constraint #1 Option A — CURATE-05 delegates to _cmd_approve (apply_patch_transaction never called directly)"
    - "Two-signal confidence gate (mean_delta + evidence_count — both required simultaneously)"
    - "Defense-in-depth for bundled-never-auto (is_agent_created recheck in CLI even if proposer errs)"
    - "Best-effort audit append (try/except WARNING — T-32-12 mitigation)"
    - "Lazy imports inside handler bodies (runtime isolation — 0 module-level agent.evolution imports)"
key-files:
  created:
    - tests/hermes_cli/test_curator_cli.py
  modified:
    - hermes_cli/curator.py
    - hermes_cli/feedback.py
decisions:
  - "CURATE-05 chose Option A (delegate to _cmd_approve) over Option B (direct apply_patch_transaction call) — P31 TestNonBypassableHumanInLoop passes UNCHANGED with zero test amendment"
  - "Audit-append for apply action wired INSIDE _cmd_approve in hermes_cli/feedback.py rather than in the curator wrapper — RESEARCH A4 rationale: single source of truth, every approve caller (direct / curator wrapper / auto-apply) audited"
  - "Audit-append for reject action wired in the curator wrapper (_cmd_reject_curator) rather than _cmd_reject — reject is lower-stakes than apply and the wrapper-level wiring avoids touching P31 _cmd_reject (minimal P31 blast radius)"
  - "Auto-apply command surface placed under `hermes curator auto-apply-eligible` (not `hermes feedback`) — CURATE-05 is curator-scope and operators think of auto-apply as curator behavior"
  - "Auto-apply audit action uses `auto_apply` (distinct from `apply`) so operators can filter automated vs manual applies in the audit log"
  - "Auto-apply passes yes=True programmatically to _cmd_approve via argparse.Namespace — the operator's explicit opt-in is running the command (config + command invocation = two-gate consent)"
metrics:
  duration: 5m
  completed: 2026-06-25
  tasks: 2
  tests_added: 34
  files_created: 1
  files_modified: 2
---

# Phase 32 Plan 02: Curator CLI + Auto-Apply Summary

CURATE-04 operator CLI surface (queue / approve / reject / audit-log + `--verify`) and CURATE-05 semi-automatic apply path (agent-created skills only, two-signal confidence, default OFF, bundled NEVER auto) shipped via Option A delegation — P31 structural invariant `TestNonBypassableHumanInLoop` passes UNCHANGED, `apply_patch_transaction` is still called only from `_cmd_approve`.

## What Shipped

### Task 1: Curator CLI subcommands (queue / approve / reject / audit-log)

**`hermes_cli/curator.py:register_cli`** extended AFTER the existing `p_rollback` block with 5 new subparsers (4 for Task 1, 1 for Task 2):

| Subcommand | Handler | Delegates To |
|------------|---------|--------------|
| `queue [--skill X] [--status pending\|applied\|rejected]` | `_cmd_queue` | P31 `_cmd_review_queue` |
| `approve <patch_id> [-y/--yes]` | `_cmd_approve_curator` | P31 `_cmd_approve` |
| `reject <patch_id> <reason>` | `_cmd_reject_curator` | P31 `_cmd_reject` + audit append on success |
| `audit-log [--action X] [--since D] [--skill Y] [--verify]` | `_cmd_audit_log` | `agent.curator_audit.{read_audit, verify_chain}` |
| `auto-apply-eligible [--dry-run]` (Task 2) | `_cmd_auto_apply_eligible` | `_cmd_approve` per patch (Option A) |

**`_cmd_approve` in `hermes_cli/feedback.py`** extended (lines 907-932) to call `append_audit(action="apply", ...)` AFTER `move_patch(...)` success — single source of truth per RESEARCH A4. Every approve caller (direct `hermes feedback approve`, curator wrapper, CURATE-05 auto-apply) now gets the audit entry automatically. Best-effort: try/except WARNING (T-32-12 — audit failure MUST NOT block the apply).

**Helpers:**
- `_get_operator()` — `getpass.getuser()` with `RuntimeError`/`ImportError` fallback to `"unknown"`
- `_resolve_skill_from_patch(patch_id)` — scans pending/applied/rejected queue files; returns `"unknown"` if not found

**`audit-log --verify`** behavior:
- Empty/missing log: `"audit chain: OK (all entries verify)"` exit 0
- Valid chain: same message, exit 0
- Tampered chain: `"audit chain: N break(s) detected:"` with per-line errors, exit 1

### Task 2: CURATE-05 auto-apply path (Option A)

**`_cmd_auto_apply_eligible`** in `hermes_cli/curator.py` implements the semi-automatic apply path for agent-created skills. Six-step flow:

1. **Config gate (T-32-09):** `if not get_auto_apply_enabled(): print disabled-message; return 0` — default OFF, first check before any queue scan
2. **Scan:** `read_queue(evolution_dir, status="pending")`
3. **Filter — two-signal confidence + agent-created + marked eligible:**
   - `auto_apply_eligible == True` (proposer marker)
   - `is_agent_created(skill_id) == True` (T-32-05 defense-in-depth — bundled NEVER auto even if proposer erred)
   - `confidence_score.mean_delta >= get_auto_apply_min_delta()` (default 0.1)
   - `confidence_score.evidence_count >= get_auto_apply_min_evidence()` (default 3)
   - Both signals must pass SIMULTANEOUSLY (either failing skips)
4. **`--dry-run`:** lists eligible patches without applying
5. **Apply via delegation (Option A):** for each eligible patch, construct `argparse.Namespace(patch_id=p.patch_id, yes=True)` and call `_cmd_approve(ns)` — NEVER calls `apply_patch_transaction` directly. On success, appends audit entry with `action="auto_apply"` (distinct from `"apply"`). Best-effort: one failure does not abort the batch.
6. **Summary:** `"auto-applied N patch(es), skipped M, failed F"`; exit 1 if any failure

**Architectural Constraint #1 — Option A chosen:**
- `_cmd_auto_apply_eligible` DELEGATES to `_cmd_approve` for each eligible patch
- `apply_patch_transaction` is STILL called only from `_cmd_approve` (1 Call node in `hermes_cli/feedback.py`, 0 in `hermes_cli/curator.py`)
- P31 `TestNonBypassableHumanInLoop` passes **UNCHANGED** — zero test amendment needed
- Alternative Option B (direct `apply_patch_transaction` call + P31 test allowlist amendment) was NOT chosen because Option A has strictly smaller blast radius and preserves the invariant's integrity

## Verification Results

All 8 plan verification commands pass:

| # | Verification | Result |
|---|--------------|--------|
| 1 | `pytest tests/hermes_cli/test_curator_cli.py -x --timeout=60` | **34 passed** (all 8 test classes: RegisterCli, QueueCmd, ApproveCmdCurator, RejectCmdCurator, AuditLogCmd, Delegation, AuditAppendBestEffort, GetOperator, AutoApplyCmd, StructuralInvariantPreserved) |
| 2 | `pytest tests/hermes_cli/test_evolution_cli.py -x --timeout=120` | **27 passed** (P31 CLI regression preserved) |
| 3 | `pytest tests/hermes_cli/test_evolution_cli.py::TestNonBypassableHumanInLoop -x` | **2 passed** UNCHANGED (Option A preserves the invariant) |
| 4 | `ruff check hermes_cli/curator.py hermes_cli/feedback.py` | **All checks passed** (PLW1514 — every open() has encoding="utf-8") |
| 5 | `apply_patch_transaction` Call nodes in `hermes_cli/curator.py` | **0** (curator CLI delegates, never calls apply directly) |
| 6 | `apply_patch_transaction` Call nodes in `hermes_cli/feedback.py` | **1** (P31 baseline preserved — Option A adds no new callers) |
| 7 | `pytest tests/agent/test_curator*.py tests/agent/evolution/ tests/agent/test_audit_log.py -x --timeout=120` | **267 passed** (Plan 01 engine tests unaffected by Plan 02) |
| 8 | FOUND-08 byte-intact: `git diff --name-only HEAD -- skills/movie-experts/ \| grep -v _eval \| grep -v _shared \| wc -l` | **0** |

**Combined regression:** 34 (new) + 27 (P31 CLI) + 267 (engine) = **328 tests green**, zero regressions.

## Option A Confirmation (CURATE-05 — Architectural Constraint #1)

**Option chosen:** Option A — `_cmd_auto_apply_eligible` delegates to `_cmd_approve` per eligible patch.

**Why Option A over Option B:**
- Option A has strictly smaller blast radius — no P31 test amendment needed
- `apply_patch_transaction` stays called only from `_cmd_approve` — the P31 structural invariant's safety guarantee (EVOL-04 non-bypassable human-in-loop) is preserved intact
- Option B would have weakened the invariant by allowlisting a second caller (`_cmd_auto_apply_eligible`) — reopening the EVOL-04 bypass risk the test was designed to prevent
- Option A is feasible because `_cmd_approve` accepts an `argparse.Namespace` with `yes=True` programmatically — the operator's explicit opt-in is the combination of (1) enabling `feedback.curator.auto_apply_enabled: true` in config AND (2) running `hermes curator auto-apply-eligible`

**Confirmation:**
- P31 `test_only_cmd_approve_calls_apply_patch_transaction` (ast-walks `hermes_cli/feedback.py`): **PASSED UNCHANGED**
- P31 `test_apply_patch_transaction_not_called_in_agent_or_runtime` (ast-walks `agent/`, `gateway/`, `run_agent.py`, `cli.py`): **PASSED UNCHANGED**
- Plan 02's own `TestStructuralInvariantPreserved::test_curator_cli_has_zero_apply_patch_transaction_calls` (ast-walks `hermes_cli/curator.py`): **PASSED** (0 Call nodes)
- `apply_patch_transaction` Call node count in `hermes_cli/feedback.py`: **1** (unchanged from P31 baseline — the single legitimate caller inside `_cmd_approve`)

## New CLI Subcommand Surface

```
hermes curator queue [--skill X] [--status pending|applied|rejected]
hermes curator approve <patch_id> [-y/--yes]
hermes curator reject <patch_id> <reason>
hermes curator audit-log [--action propose|approve|reject|apply|rollback|auto_apply]
                         [--since ISO_DATE] [--skill X] [--verify]
hermes curator auto-apply-eligible [--dry-run]
```

The first three are thin wrappers around P31 commands (single source of truth). `audit-log` is new (reads `~/.hermes/skills/.audit/log.jsonl`). `auto-apply-eligible` is the CURATE-05 semi-automatic apply path.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `_get_operator` test patched `builtins.__import__` instead of `getpass.getuser`**
- **Found during:** Task 1 GREEN phase
- **Issue:** The RED test `test_falls_back_to_unknown_on_failure` patched `builtins.__import__` to raise on `import getpass`. But `getpass` is imported at module top-level in `hermes_cli/curator.py`, so `builtins.__import__` patching no longer affects the already-bound `getpass.getuser`. The test returned the real username instead of `"unknown"`.
- **Fix:** Changed the test to monkeypatch `getpass.getuser` directly (the bound function) to raise `RuntimeError`. This correctly simulates the runtime failure path.
- **Files modified:** `tests/hermes_cli/test_curator_cli.py`
- **Commit:** cd59fc329

No authentication gates, no Rule 4 architectural changes (Option A was chosen as planned, no Option B pivot needed), no deferred issues.

## Known Stubs

None. All functions are fully implemented — no placeholder values, no TODO markers, no unwired data paths.

## Threat Flags

None. All threats in the plan's `<threat_model>` are mitigated as specified:

| Threat | Mitigation | Test |
|--------|------------|------|
| T-32-08 (bundled auto-apply) | `is_agent_created(p.skill_id)` recheck in `_cmd_auto_apply_eligible` — bundled NEVER auto even if proposer erred | `test_auto_apply_refuses_bundled` |
| T-32-09 (auto-apply when default OFF) | Step 1 config gate — first check before any queue scan | `test_auto_apply_default_off` |
| T-32-10 (apply_patch_transaction outside `_cmd_approve`) | Option A delegation — `_cmd_auto_apply_eligible` never calls `apply_patch_transaction` directly | P31 `TestNonBypassableHumanInLoop` UNCHANGED + `TestStructuralInvariantPreserved` |
| T-32-11 (malicious patch_id) | Delegation to P31 `_cmd_approve` (validates patch_id exists + `apply_patch_transaction` guards) — Plan 02 adds no new attack surface | (covered by P31 tests) |
| T-32-12 (audit append blocks approve) | try/except WARNING around every `append_audit` call — best-effort per RESEARCH A4 | `TestAuditAppendBestEffort` (2 tests) |
| T-32-13 (PII in feedback_ids) | `audit-log` prints only `ts / action / patch_id / skill_id` — never `feedback_ids` or `eval_score` content | (audit-log output format verified in `TestAuditLogCmd`) |
| T-32-SC (supply-chain) | Zero new packages — stdlib `argparse` + `getpass` + `logging` only | (n/a) |

## Self-Check: PASSED

**Files created (verified to exist):**
- FOUND: tests/hermes_cli/test_curator_cli.py

**Files modified (verified to exist):**
- FOUND: hermes_cli/curator.py
- FOUND: hermes_cli/feedback.py

**Commits (verified in git log):**
- FOUND: 54dff9a06 (test 32-02: RED phase — failing tests for curator CLI + auto-apply)
- FOUND: cd59fc329 (feat 32-02: GREEN phase — curator CLI subcommands + CURATE-05 auto-apply path)

**Test counts:**
- Task 1 (CLI subcommands): 25 tests across TestRegisterCliPreservesExistingSubcommands (7) + TestQueueCmd (1) + TestApproveCmdCurator (2) + TestRejectCmdCurator (2) + TestAuditLogCmd (6) + TestDelegation (3) + TestAuditAppendBestEffort (2) + TestGetOperator (2)
- Task 2 (CURATE-05 auto-apply): 9 tests across TestAutoApplyCmd (8) + TestStructuralInvariantPreserved (1)
- **Total new: 34 tests, all green**
- **Regression: 294 passed (27 P31 CLI + 267 engine), zero regressions**
