---
phase: 65-curator-live-guards
fixed_at: 2026-07-08T04:30:00Z
review_path: .planning/phases/65-curator-live-guards/65-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 65: Code Review Fix Report

**Fixed at:** 2026-07-08T04:30:00Z
**Source review:** `.planning/phases/65-curator-live-guards/65-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 7 (2 BLOCKER + 5 WARNING; INFO findings deferred per default scope)
- Fixed: 7
- Skipped: 0

**Verification:**
- Phase 65 deliverable tests: 54/54 pass (`tests/agent/test_curator_live_guards.py`, `tests/hermes_cli/test_curator_evolve_cli.py`, `tests/v11-bias-canary/`)
- Broader curator suite: 165/165 pass (excluding pre-existing `test_curator_stats.py` failures unrelated to Phase 65 — those failures reference `skills/movie-experts/_shared/v6-feedback-loop-architecture.md` which was removed in earlier commit `f10495332` "migrated kais skills + plugins to kais-skills repo")
- No regression introduced by fixes

## Fixed Issues

### CR-01: `run_bias_canary_pre_check` does not honor its "never raises" contract

**Files modified:** `agent/curator.py`
**Commit:** `9e14b1e31`
**Applied fix:** Wrapped per-record `check_record(record)` call in a broad `except Exception` (noqa BLE001) inside the existing for-loop. Any crash (AttributeError, TypeError, etc.) from a malformed fixture record is now logged at WARNING with the line number and record_id, the record_id is appended to `not_caught` as `<crashed>` (or the actual id when available), and iteration continues. The denominator is NOT reduced — the conservative interpretation per REVIEW.md (never let a buggy fixture line grant a false PASS). Added an inline comment justifying the broad except as fail-safe design (load-bearing "never raises" contract). The outer `except OSError` for file I/O remains unchanged.

### CR-02 + WR-02 + WR-05: Post-tick audit error handling (combined — same code block)

**Files modified:** `hermes_cli/curator.py`
**Commit:** `3f5396a3b`
**Applied fix (CR-02):** Added `AuditChainError` to the `except` tuple in `_cmd_evolve`'s post-tick audit block. Lazy-imported `AuditChainError` alongside `append_audit` from `agent.curator_audit`. With this fix, a corrupted audit log tail (the exact scenario documented at `agent/curator_audit.py:79-87` and `:255-260`) raises `AuditChainError` which is now caught — the CLI logs a WARNING and returns 0 instead of crashing after irreversible memory writes. Used the explicit form (preferred by REVIEW.md) over broad `except Exception` to avoid swallowing programming bugs like `KeyError`.

**Applied fix (WR-02):** Also added `ImportError` to the same `except` tuple for symmetry with the `_resolve_skill_from_patch` lazy-import defense at `hermes_cli/curator.py:675`. A partially-broken wheel install or circular-import regression should not crash the post-tick path either.

**Applied fix (WR-05):** Replaced misleading inner-comment "Wrap in try/except KeyError for forward-compat" (the caught types are `AttributeError, TypeError`, NOT `KeyError` — `dict.get()` cannot raise KeyError). New comment accurately describes the realistic crash mode (`result` being non-dict value, e.g. a future `run_curator_review` regression returning a string) and surfaces the malformed-result case as a WARNING rather than silently writing `mutation_summary={}`. Also removed redundant `from datetime import datetime as _dt` local import (module-level `datetime` already imported at line 27).

### WR-01: Hardcoded `/5` and `threshold: 4` literals in BIAS_CANARY_FAILED message

**Files modified:** `agent/curator.py`, `hermes_cli/curator.py`
**Commit:** `a90ea5caa`
**Applied fix:** Added two public aliases in `agent/curator.py`:
- `BIAS_CANARY_THRESHOLD` (alias for `_BIAS_CANARY_THRESHOLD`, v12.0 EVAL-03 baseline catch threshold)
- `BIAS_CANARY_FIXTURE_COUNT` (expected record count in bundled JSONL, synchronized with `tests/fixtures/curator_bias_canary/known_bad_records.jsonl`)

Updated `hermes_cli/curator.py` BIAS_CANARY_FAILED message to interpolate `curator.BIAS_CANARY_FIXTURE_COUNT` and `curator.BIAS_CANARY_THRESHOLD`. Updated `--live --help` text to reference the threshold constant instead of the hardcoded `<4/5 catch rate` string. The private `_BIAS_CANARY_THRESHOLD` name is preserved for backward-compat (default arg + docstring still reference it). Test `test_canary_failure_message_format` still passes — the rendered message is byte-identical when constants hold their current values (5 and 4).

### WR-03: Regression test for CR-02 (AuditChainError path)

**Files modified:** `tests/hermes_cli/test_curator_evolve_cli.py`
**Commit:** `862f38894`
**Applied fix:** Added new test `test_audit_chain_corruption_does_not_crash_tick` next to the existing `test_audit_failure_does_not_crash_tick`. The new test monkeypatches `append_audit` with `side_effect=AuditChainError("audit log tail is malformed — prev_sha256 chain broken")` (mimicking the exact failure mode documented in CR-02), then asserts:
1. `_cmd_evolve` returns `rc=0` (not crash) — the live tick already completed.
2. `run_curator_review` was called once with `dry_run=False` — proving the audit failure did not roll back or skip the live tick.

This is the test that would have caught CR-02. Evolve CLI suite now 18/18 passing (was 17/17).

### WR-04: Wheel-install blind spot in fixture path resolution

**Files modified:** `hermes_cli/curator.py`
**Commit:** `9c3d13e9a`
**Applied fix:** Added explicit detection in `_cmd_evolve`: when canary fails AND `_failed_ids == ["<fixtures-missing>"]` (the exact sentinel returned by `run_bias_canary_pre_check` when the fixture JSONL is absent), emit a distinct `BIAS_CANARY_FIXTURES_MISSING` stderr message naming the expected path and explaining the likely cause (pip/wheel install — `tests/` dir not bundled) plus remediation options (run from repo checkout, copy fixtures manually, or wait for Phase 66 fixture-bundling). Other canary-failure paths (ran but underperformed, fixture read error) continue to emit the existing `BIAS_CANARY_FAILED` message — only the distinct `<fixtures-missing>` sentinel triggers the new branch. Chose REVIEW.md option (b) (explicit warning) over option (a) (bundle fixtures as package data) because fixtures are test-only artifacts.

## Skipped Issues

None. All 7 in-scope findings were applied successfully.

## Deferred Issues (INFO — out of scope per default fix_scope=critical_warning)

- **IN-01:** Fixture file leading `#` comment lines — no fix needed (parser correctly skips).
- **IN-02:** Redundant `from datetime import datetime as _dt` local import in `_cmd_evolve` — **incidentally fixed** as part of WR-05/CR-02 refactor (local alias removed; module-level `datetime` used instead). Not a separate commit.
- **IN-03:** `_bias_canary_fixtures_path()` `parents[1]` indexing fragility — not fixed (low priority per REVIEW.md; fail-safe behavior is correct).

---

_Fixed: 2026-07-08T04:30:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
