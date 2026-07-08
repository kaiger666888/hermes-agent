---
phase: 65-curator-live-guards
plan: 02
subsystem: curator-self-evolution
tags: [curator, cli, evolve, live-tick, bias-canary, audit-chain, operator-surface]
requires:
  - "Phase 65 Plan 01 (run_bias_canary_pre_check + append_audit tick_mode extension)"
  - "Phase 32 (CURATE-04 audit chain — agent/curator_audit.py)"
  - "Phase 33 (hermes_cli/curator.py register_cli pattern)"
  - "v12.0 EVAL-03 baseline (>=4/5 catch rate threshold)"
provides:
  - "hermes_cli.curator._cmd_evolve — operator-facing handler for curator self-evolution (CURATE-01)"
  - "hermes curator evolve subparser with --live/--skip-canary/--sync flags (CURATE-01)"
  - "G4 canary failure UX: exit code 2 + structured BIAS_CANARY_FAILED stderr message"
  - "tests/hermes_cli/test_curator_evolve_cli.py — 17 unit tests covering parsing, exit codes, audit logging, canary failure UX"
affects:
  - "Plan 65-03 (smoke): end-to-end verification uses the registered evolve subcommand"
  - "Phase 66 (CURATE-LIVE-TICK): 1st actual live tick uses this CLI surface"
tech-stack:
  added: []
  patterns:
    - "lazy import for agent.curator + agent.curator_audit (preserves runtime isolation invariant)"
    - "explicit boolean dry_run=True/False at every run_curator_review call site (Pitfall 2 mitigation)"
    - "best-effort audit append wrapped in try/except (OSError, ValueError) — failure logs WARNING, never masks tick"
    - "TDD RED/GREEN: 17 failing tests first (AttributeError on _cmd_evolve), then implementation makes them pass"
key-files:
  created:
    - tests/hermes_cli/test_curator_evolve_cli.py
  modified:
    - hermes_cli/curator.py
    - tests/hermes_cli/test_curator_cli.py
decisions:
  - "evolve is a NEW subcommand distinct from run (G1 Option A) — operators grep audit logs for the evolve verb to find self-evolution events"
  - "exit code 2 for canary failure (G4 Option A) — distinguishes from generic error (exit 1); structured BIAS_CANARY_FAILED message is grep-friendly for runbook automation"
  - "audit canary_pass=None (not False) when --skip-canary used (Pitfall 5) — distinct from True/False so Phase 66 24h review can grep for escape-hatch use"
  - "mutation_summary extracted from auto_transitions dict (checked/archived/marked_stale/reactivated) — wrapped in try/except for forward-compat"
  - "canary failure path does NOT append audit — recording the abort would conflate 'tried and failed pre-check' with 'tick ran' in the audit trail"
metrics:
  duration: PT14M
  completed: 2026-07-08
---

# Phase 65 Plan 02: Curator Live Guards — Wave 1 CLI Wiring Summary

Wave 1 of Phase 65 wires the Plan 01 primitives (`run_bias_canary_pre_check` + extended `append_audit`) into the operator-facing CLI surface: the new `hermes curator evolve` subcommand. Default path is a dry-run preview; `--live` is the explicit opt-in for actual memory writes, gated by the deterministic bias canary pre-check; `--skip-canary` is the operator-only escape hatch (audit-logged with `canary_pass=None`).

---

## What Was Built

### 1. `hermes_cli/curator._cmd_evolve(args) -> int` (NEW)

The handler implements four operator paths:

| Path | Flags | Behavior | Exit |
|------|-------|----------|------|
| Curator disabled | (any) | Mirrors `_cmd_run`: prints "disabled via config" and returns | 1 |
| Dry-run preview (default) | (none) | Prints DRY-RUN marker; calls `run_curator_review(dry_run=True)` — explicit True (Pitfall 2); prints "Re-run with --live" hint | 0 |
| Live tick + canary pass | `--live` | Runs `run_bias_canary_pre_check()`; on pass (>=4/5) calls `run_curator_review(dry_run=False)` — explicit False; appends audit entry with `tick_mode="live"`, `canary_pass=True`, `caught_count=N` | 0 |
| Live tick + canary fail | `--live` | Runs canary; on fail (<4/5) prints `BIAS_CANARY_FAILED: caught N/5 (threshold: 4); live tick aborted; run 'hermes curator evolve' (no --live) for dry-run preview` to stderr (G4 exact format); does NOT call `run_curator_review` with `dry_run=False` | 2 |
| Skip-canary escape hatch | `--live --skip-canary` | Bypasses canary; calls `run_curator_review(dry_run=False)`; audit entry has `canary_pass=None` (Pitfall 5 — distinct from True/False) | 0 |

**Design choices:**

- **Lazy imports** of `agent.curator` and `agent.curator_audit` inside the handler body — preserves the runtime-isolation invariant documented at the top of `hermes_cli/curator.py` (zero module-level agent.evolution imports).
- **Explicit boolean `dry_run`** at every call site — never None. EVAL-06 treats None as True (silent dry-run); explicit True/False keeps the invariant readable (Pitfall 2 mitigation).
- **Best-effort audit append** (RESEARCH A4 / T-65-09): wraps `append_audit` in `try/except (OSError, ValueError)` so a failed audit write (disk full, schema drift) logs a WARNING but never masks a successful tick. The operator can investigate; the live writes already happened and cannot be rolled back from here.
- **mutation_summary extraction**: pulls `auto_transitions` counts (`checked`/`archived`/`marked_stale`/`reactivated`) from the `run_curator_review` result dict; wraps in `try/except (AttributeError, TypeError)` for forward-compat (RESEARCH: mutation_summary is free-form so Phase 66 runbook can evolve keys without audit-module edit).
- **Canary failure does NOT append audit**: recording the abort would conflate "tried and failed pre-check" with "tick ran" in the audit trail. The exit code 2 + stderr message is the operator signal; audit is for successful ticks only.
- **`--skip-canary` audit entry has `canary_pass=None`** (NOT False) — Pitfall 5: distinct from True/False so Phase 66's 24h operator review can `grep canary_pass=null` (or equivalent) to find escape-hatch use.

### 2. `evolve` subparser registration (in `register_cli`)

Added AFTER `p_run.set_defaults(func=_cmd_run)` and BEFORE `p_pause`:

```python
p_evolve = subs.add_parser(
    "evolve",
    help="Run curator self-evolution (default: dry-run preview; "
         "--live performs actual memory writes with bias canary pre-check)",
)
p_evolve.add_argument("--live", dest="live", action="store_true", ...)
p_evolve.add_argument("--skip-canary", dest="skip_canary", action="store_true", ...)
p_evolve.add_argument("--sync", "--synchronous", dest="synchronous", action="store_true", ...)
p_evolve.set_defaults(func=_cmd_evolve)
```

The `--live` help text mentions "LIVE memory writes" + "aborts on <4/5 catch rate"; `--skip-canary` help text says "DANGEROUS" + "audit-logged" (V4 access control per RESEARCH).

### 3. `tests/hermes_cli/test_curator_evolve_cli.py` (NEW — 17 tests)

Full unit suite for the evolve subcommand:

**Parsing tests (5):**
- `test_evolve_subcommand_registered` — evolve is in the subparser choices
- `test_default_is_dry_run` — `["evolve"]` yields `live=False`, `skip_canary=False`
- `test_live_flag_parsed` — `["evolve", "--live"]` yields `live=True`
- `test_skip_canary_parsed` — `["evolve", "--live", "--skip-canary"]` yields `skip_canary=True`
- `test_sync_alias` — both `--sync` and `--synchronous` yield `synchronous=True`

**Exit-code + path tests (4):**
- `test_curator_disabled_returns_1` — mirrors `_cmd_run` disabled path
- `test_default_path_calls_dry_run` — `run_curator_review` called with `dry_run is True` (explicit boolean)
- `test_default_path_prints_dry_run_marker` — stdout contains "DRY-RUN" or "dry-run"
- `test_live_flag_triggers_live_path` — canary pass → `run_curator_review` called once with `dry_run is False`

**Canary failure UX tests (3):**
- `test_live_aborts_on_canary_failure` — canary returns (False, 3, [...]) → exit 2, `run_curator_review` NOT called with `dry_run=False`
- `test_canary_failure_message_format` — stderr matches regex `^BIAS_CANARY_FAILED: caught 3/5 \(threshold: 4\); live tick aborted; run 'hermes curator evolve' \(no --live\) for dry-run preview$`
- `test_canary_failure_does_not_append_audit` — on abort path, `append_audit` is NOT called

**Audit logging tests (4):**
- `test_skip_canary_bypasses_pre_check` — `run_bias_canary_pre_check` NOT called; audit has `canary_pass=None`, `tick_mode="live"`
- `test_audit_logged_on_live_tick` — after successful `--live`, audit called with `tick_mode="live"`, `canary_pass=True`, `caught_count=4`
- `test_audit_failure_does_not_crash_tick` — `append_audit` raising OSError → tick still returns 0
- `test_audit_failure_on_skip_canary_does_not_crash` — same guarantee for `--skip-canary` path
- `test_mutation_summary_extracted_from_result` — `mutation_summary` is a dict reflecting `auto_transitions` counts

### 4. `tests/hermes_cli/test_curator_cli.py` — Extended

Appended `"evolve"` as the 6th element of `NEW_V6_SUBCOMMANDS`:

```python
NEW_V6_SUBCOMMANDS = (
    "queue", "approve", "reject", "audit-log", "auto-apply-eligible",
    "evolve",
)
```

This makes `test_new_five_subcommands_resolve` automatically cover `evolve` — catches a regression where someone removes the `p_evolve` block from `register_cli`.

---

## Test Results

```
$ python -m pytest tests/hermes_cli/test_curator_evolve_cli.py -x -q
.................                                                             [100%]
17 passed in 0.45s
```

**Regression suite:**
```
$ python -m pytest tests/hermes_cli/test_curator_cli.py tests/agent/test_curator.py tests/agent/test_curator_live_guards.py tests/hermes_cli/test_curator_evolve_cli.py tests/v11-bias-canary/ -x -q
........................................................................ [ 48%]
........................................................................ [ 96%]
......                                                                   [100%]
150 passed in 3.36s
```

All 150 curator + bias canary + CLI tests pass — no regressions. The existing 13 curator subcommands (status/run/pause/resume/pin/unpin/restore/list-archived/archive/prune/backup/rollback + stats) are unchanged.

**Smoke check (plan verification §4):**
```
$ python -c "import argparse; from hermes_cli.curator import register_cli; p=argparse.ArgumentParser(); register_cli(p); ns=p.parse_args(['evolve','--live']); print(ns.live, ns.skip_canary, callable(ns.func))"
True False True
```

---

## TDD Gate Compliance

RED/GREEN cycle followed per plan:

1. **RED commit (`be8ebeed1`):** 17 failing tests written first — all fail because `_cmd_evolve` does not exist (`AttributeError`) and the `evolve` subparser is not registered (`AssertionError: evolve subcommand not registered`).
2. **GREEN commit (`367d2a149`):** Implementation lands; all 17 tests pass.

Tasks 1 and 2 both modify `_cmd_evolve` in the same file and the function is only useful when complete (parsing without behavior is inert; behavior without parsing is unreachable). Both tasks' behaviors are covered by the same test suite, so the GREEN commit covers both Task 1 + Task 2 behaviors in a single atomic implementation.

No REFACTOR commit needed — the GREEN implementation is already minimal and clean (handler is ~100 lines with clear section comments; subparser registration follows the existing pattern exactly).

Task 3 (regression guard extension) is a separate commit (`7465db798`) because it modifies a different file (`test_curator_cli.py`) and is independently verifiable.

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking Issue] Worktree branch base was stale**
- **Found during:** Agent startup (worktree_branch_check)
- **Issue:** Worktree HEAD was at `605727e3b` (a feature branch), but the planning files for Phase 65 live on `main` at `5dfb3529c`. The merge-base was `d2c53ff5` (pre-Phase 32), so `.planning/phases/65-curator-live-guards/` did not exist in the worktree.
- **Fix:** Per the `<worktree_branch_check>` sanctioned `git reset --hard`, reset the worktree to `5dfb3529c7a7a75ef36798ddcf61731a4fe2a9a4`. This brought in Plan 01's primitives (`run_bias_canary_pre_check`, extended `append_audit`) that Plan 02 depends on. Working tree was clean before reset (no WIP to lose).
- **Files modified:** None functionally — git history recovery only.
- **Commits:** Unchanged from plan.

No other deviations. Plan executed as written.

---

## Known Stubs

None. All paths (`_cmd_evolve`, subparser registration) are fully implemented and exercised by tests.

---

## Threat Flags

None. The implementation matches the plan's `<threat_model>` mitigations exactly:

- **T-65-06** (EoP — `--live` mutation gate): mitigated via default dry-run (EVAL-06 preserved) + explicit opt-in flag + bias canary pre-check gate + help text warning "LIVE memory writes".
- **T-65-07** (EoP — `--skip-canary` escape hatch): mitigated via audit-logged `canary_pass=None` (distinct from True/False per Pitfall 5) + help text "DANGEROUS" + "audit-logged" warning.
- **T-65-08** (Repudiation — canary failure message): mitigated via structured `BIAS_CANARY_FAILED: caught N/5 (threshold: 4)` format to stderr (grep-friendly) + exit code 2 (distinct from generic error).
- **T-65-09** (Tampering — audit append after live tick): mitigated via `tick_mode="live"` + `canary_pass` + `caught_count` + `mutation_summary` fields; wrap in try/except so audit failure does not mask tick but logs WARNING.
- **T-65-10** (DoS — concurrent `evolve --live`): accepted per plan (Phase 65 ships no soft lock; Phase 66 runbook will document serial execution).

No new security-relevant surface introduced beyond the plan's threat model.

---

## Self-Check: PASSED

Files verified to exist:
- FOUND: tests/hermes_cli/test_curator_evolve_cli.py
- FOUND: hermes_cli/curator.py (modified — _cmd_evolve + evolve subparser added)
- FOUND: tests/hermes_cli/test_curator_cli.py (modified — NEW_V6_SUBCOMMANDS extended)

Commits verified to exist:
- FOUND: be8ebeed1 (test(65-02): add failing tests for _cmd_evolve + evolve subparser)
- FOUND: 367d2a149 (feat(65-02): implement _cmd_evolve + evolve subparser with canary gate)
- FOUND: 7465db798 (test(65-02): extend NEW_V6_SUBCOMMANDS regression guard with evolve)
