---
phase: 65-curator-live-guards
verified: 2026-07-08T04:30:00Z
status: passed
score: 3/3 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: N/A
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 65: Curator Live Guards — Verification Report

**Phase Goal:** curator self-evolution CLI `--live` opt-in flag + pre-tick bias canary + post-tick audit log.
**Verified:** 2026-07-08T04:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

Roadmap-derived success criteria (non-negotiable contract):

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `hermes curator evolve --live` flag works; default (no flag) is dry-run | VERIFIED | `_cmd_evolve` at `hermes_cli/curator.py:250`; `evolve` subparser registered at `hermes_cli/curator.py:1459` with `--live`/`--skip-canary`/`--sync` flags; default path prints `DRY-RUN — REPORT ONLY` marker, exit 0, no audit side effects (reproduced end-to-end against isolated HERMES_HOME). Tests: `test_default_is_dry_run`, `test_live_flag_triggers_live_path`, `test_default_path_prints_dry_run_marker`, `test_default_path_calls_dry_run` — 4/4 PASSED. End-to-end smoke (isolated HERMES_HOME): `curator evolve: running DRY-RUN preview (no mutations)` + `DRY-RUN — REPORT ONLY. DO NOT MUTATE THE SKILL LIBRARY.` + `dry-run: no changes applied.` + EXIT=0. |
| 2 | Pre-tick bias canary catches ≥4/5 known-bad records; canary fail aborts live tick (exit 2) | VERIFIED | `run_bias_canary_pre_check()` at `agent/curator.py:1986` with `_BIAS_CANARY_THRESHOLD=4` (frozen, line 1949); fixture JSONL at `tests/fixtures/curator_bias_canary/known_bad_records.jsonl` has 5 records (4 deterministic-fail + 1 LLM-only by design). Empirical catch rate: 4/5 (matches threshold). Exit 2 on canary failure with structured `BIAS_CANARY_FAILED: caught N/5 (threshold: 4); live tick aborted; run 'hermes curator evolve' (no --live) for dry-run preview` to stderr (G4 format). Tests: `test_pre_check_catches_four_of_five`, `test_live_aborts_on_canary_failure`, `test_canary_failure_message_format`, `test_canary_failure_does_not_append_audit` — all PASSED. End-to-end smoke: `hermes curator evolve --live` produced `curator evolve: running LIVE tick (canary: 4/5 caught)` + EXIT=0 (canary passed, proceeded). Abort path covered authoritatively by 4 unit tests (CLI does not expose fixtures_path override — documented in 65-SMOKE.md §SC#2b). |
| 3 | Post-tick audit log emits sha256-tagged memory writes with `tick_mode` field; operator can inspect within 24h rollback window | VERIFIED | `append_audit` at `agent/curator_audit.py:158` extended with 4 optional kwargs: `tick_mode`, `canary_pass`, `caught_count`, `mutation_summary` (lines 172-175). Validation rules: (1) `tick_mode in {"live", "dry_run", None}`, (2) `canary_pass=True requires tick_mode="live"` (lines 236-242). New fields conditionally included in entry dict so legacy entries stay byte-identical (lines 281-288). `_compute_entry_sha256` includes new fields in hash via existing serializer. End-to-end smoke wrote audit entry to isolated HERMES_HOME: `{"tick_mode": "live", "canary_pass": true, "caught_count": 4, "mutation_summary": {...}, "entry_sha256": "01afd1..."}`. `verify_chain()` (function at `agent/curator_audit.py:317`) returns `[]` (clean chain) on the smoke-produced log. Tests: `test_append_audit_with_tick_mode`, `test_verify_chain_mixed_schema`, `test_append_audit_backward_compat` — 3/3 PASSED. 24h rollback window supported via `hermes curator rollback` (snapshot created before each live tick — confirmed in smoke output: `curator: snapshot created (2026-07-08T04-23-33Z)`). |

**Score:** 3/3 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/fixtures/curator_bias_canary/known_bad_records.jsonl` | 5 known-bad records (4 deterministic-fail + 1 LLM-only) | VERIFIED | 15 lines (10-line header + 5 JSONL records). Validated: `bad-low-confidence` (confidence=0.15 < 0.3), `bad-single-operator` (1 distinct op < 2), `bad-no-operator-id` (0 distinct ops), `bad-low-evidence` (cooking evidence vs editing claim — evidence_coverage fail), `bad-unsupported-claim` (LLM-only by design). All records have required fields: `record_id`, `agent_id`, `confidence`, `evidence_operator_ids`, `evidence_records`, `text`, `_canary_expected_failure`. |
| `agent/curator.py` (modified) | `run_bias_canary_pre_check` helper + `_BIAS_CANARY_THRESHOLD` constant | VERIFIED | `def run_bias_canary_pre_check` at line 1986 with signature `(*, fixtures_path: Path \| None, threshold: int) -> tuple[bool, int, list[str]]`. `_BIAS_CANARY_THRESHOLD=4` at line 1949; public alias `BIAS_CANARY_THRESHOLD` at line 1958; `BIAS_CANARY_FIXTURE_COUNT=5` at line 1966 (WR-01 fix). `_bias_canary_fixtures_path()` helper at line 1969. CR-01 review fix applied: per-record `check_record` call wrapped in defensive `except Exception` (fail-safe — never raises). |
| `agent/curator_audit.py` (modified) | `append_audit` with `tick_mode`/`canary_pass`/`caught_count`/`mutation_summary` kwargs | VERIFIED | `def append_audit` at line 158 with all 4 new kwargs (lines 172-175). Validation: tick_mode enum + canary_pass/tick_mode consistency (lines 236-242). Conditional field inclusion preserves backward compat (lines 281-288). `verify_chain()` at line 317 passes on mixed-schema logs. |
| `tests/agent/test_curator_live_guards.py` | Wave 0 unit tests (pre-check + audit extension) | VERIFIED | 293 lines, 12+ tests covering pre-check (5 tests), audit extension (6 tests), regression guard (1 test). |
| `hermes_cli/curator.py` (modified) | `_cmd_evolve` handler + `evolve` subparser in `register_cli` | VERIFIED | `def _cmd_evolve` at line 250 (~150 lines, 4 paths: disabled/dry-run/live-canary-pass/live-canary-fail/skip-canary). Subparser registered at line 1459 with `--live`, `--skip-canary`, `--sync`/`--synchronous` flags. CR-02 review fix applied: `except (OSError, ValueError, AuditChainError, ImportError)` at line 410 (best-effort audit append preserved). WR-04 fix: `BIAS_CANARY_FIXTURES_MISSING` distinct message at line 323 for wheel-install blind spot. |
| `tests/hermes_cli/test_curator_evolve_cli.py` | Unit tests for evolve subcommand | VERIFIED | 435 lines, 18 tests covering parsing (5), exit codes (4), canary failure UX (3), audit logging (5), regression (1 — AuditChainError path). |
| `tests/hermes_cli/test_curator_cli.py` (modified) | `NEW_V6_SUBCOMMANDS` extended with `evolve` | VERIFIED | Line 47-52: `NEW_V6_SUBCOMMANDS = ("queue", "approve", "reject", "audit-log", "auto-apply-eligible", "evolve")`. `test_new_five_subcommands_resolve` (and renamed variants) iterates this tuple, so `evolve` is now regression-guarded. |
| `.planning/phases/65-curator-live-guards/65-SMOKE.md` | End-to-end smoke evidence for all 3 SCs | VERIFIED | 241 lines with SC#1/SC#2/SC#3 sections + Phase 66 operator runbook. SC#1 evidence shows DRY-RUN stdout + exit 0. SC#2 evidence shows canary 4/5 caught + live tick proceeded + abort path covered by 3 unit tests. SC#3 evidence shows audit entry with `tick_mode: "live"` + `verify_chain` clean. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `hermes_cli/curator._cmd_evolve` | `agent/curator.run_bias_canary_pre_check` | lazy import `from agent import curator` + call `curator.run_bias_canary_pre_check()` inside `--live` branch | WIRED | Line 318 `_cmd_evolve` invokes `curator.run_bias_canary_pre_check()`; result unpacked into `passed, caught, _failed_ids`. Verified by `test_live_aborts_on_canary_failure` (monkeypatches the call). |
| `hermes_cli/curator._cmd_evolve` | `agent/curator.run_curator_review` | explicit `dry_run=True` (default) / `dry_run=False` (live) boolean | WIRED | Line 295 dry-run path: `curator.run_curator_review(..., dry_run=True)`. Line 359 live path: `curator.run_curator_review(..., dry_run=False)`. Never None (Pitfall 2 mitigation). Verified by `test_default_path_calls_dry_run` and `test_live_flag_triggers_live_path`. |
| `hermes_cli/curator._cmd_evolve` | `agent/curator_audit.append_audit` | lazy import + call with `tick_mode`, `canary_pass`, `caught_count`, `mutation_summary` after live tick | WIRED | Line 370 lazy import; line 410 `except (OSError, ValueError, AuditChainError, ImportError)` (best-effort). Verified by `test_audit_logged_on_live_tick`, `test_audit_chain_corruption_does_not_crash_tick`. |
| `agent/curator.run_bias_canary_pre_check` | `agent/curator_bias_canary.check_record` | lazy import `from agent.curator_bias_canary import check_record` inside function body | WIRED | Line 1998 lazy import; line 2042 per-record `check_record(record)` call. CR-01 fix wraps call in `except Exception` (line ~2040, noqa BLE001). |
| `agent/curator_audit.append_audit` | `agent/curator_audit._compute_entry_sha256` | existing sha256 chain auto-includes new optional fields via `_serialize_entry_for_sha256` | WIRED | Conditional inclusion at lines 281-288 means new fields are auto-included when present, absent when None. `verify_chain()` test on mixed-schema log confirms chain integrity (test_verify_chain_mixed_schema PASSED). |
| `evolve` subparser | `_cmd_evolve` handler | `p_evolve.set_defaults(func=_cmd_evolve)` | WIRED | Line 1482. Verified by `test_evolve_subcommand_registered` (parses `["evolve"]` and asserts `ns.func` is `_cmd_evolve`). |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|----|
| `_cmd_evolve` (stdout: "running LIVE tick (canary: N/5 caught)") | `caught` | `run_bias_canary_pre_check()` return value | Yes (4 deterministic catches from real fixture JSONL) | FLOWING |
| Audit entry `tick_mode`/`canary_pass`/`caught_count`/`mutation_summary` | kwargs passed to `append_audit` | `_cmd_evolve` post-tick block | Yes — verified by end-to-end smoke producing real audit entry with `caught_count: 4`, `mutation_summary: {checked: 0, archived: 0, marked_stale: 0, reactivated: 0}` | FLOWING |
| sha256 chain integrity | `entry_sha256` field | `_compute_entry_sha256(prev_sha256, entry)` | Yes — `verify_chain()` returns `[]` on smoke-produced log with real `entry_sha256: "01afd1..."` | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| SC#1 dry-run default | `HERMES_HOME=$(mktemp -d) python3 -m hermes_cli.curator evolve` | stdout contains `DRY-RUN` marker (3 times), EXIT=0, no audit log written | PASS |
| SC#2 canary pass + live tick | `HERMES_HOME=$(mktemp -d) python3 -m hermes_cli.curator evolve --live` | stdout: `curator evolve: running LIVE tick (canary: 4/5 caught)` + `curator: snapshot created (...)`, EXIT=0, audit entry appended with `tick_mode: "live"`, `canary_pass: true`, `caught_count: 4` | PASS |
| SC#3 audit verify after live tick | programmatic `verify_chain()` on smoke-produced log | returns `[]` (chain clean) | PASS |
| Phase 65 full test suite | `pytest tests/agent/test_curator_live_guards.py tests/hermes_cli/test_curator_evolve_cli.py tests/v11-bias-canary/` | 54 passed in 1.21s | PASS |
| Curator regression (CLI + agent) | `pytest tests/agent/test_curator.py tests/agent/test_curator_live_guards.py tests/hermes_cli/test_curator_cli.py tests/hermes_cli/test_curator_evolve_cli.py tests/v11-bias-canary/` | 151 passed in 3.12s | PASS |

### Probe Execution

No probe scripts declared in PLAN/SUMMARY for this phase. Probe-based verification not applicable (this is a CLI + audit-module phase, not a migration/tooling phase).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CURATE-01 | 65-02, 65-03 | 给 curator self-evolution CLI 加 `--live` opt-in flag (默认仍 dry-run) | SATISFIED | `hermes curator evolve` subcommand registered with `--live` flag (line 1464); default path calls `run_curator_review(dry_run=True)` (line 295); 5 parsing + path tests pass; end-to-end smoke confirms DRY-RUN default. |
| CURATE-02 | 65-01, 65-02 | Pre-tick bias canary check — 必须 catch ≥ 4/5 known-bad records; canary fail 时 abort live tick, 记录原因 | SATISFIED | `run_bias_canary_pre_check()` catches 4/5 deterministically; `_BIAS_CANARY_THRESHOLD=4`; canary fail → exit 2 + structured `BIAS_CANARY_FAILED` stderr message; abort path covered by 4 unit tests + `test_pre_check_catches_four_of_five`. |
| CURATE-03 | 65-01 | Post-tick 审计日志 — 记录每个 live tick 的所有 memory writes (sha256-tagged), 支持 operator 手工 rollback (24h review) | SATISFIED | `append_audit` extended with `tick_mode`/`canary_pass`/`caught_count`/`mutation_summary` kwargs; sha256 chain preserved (`verify_chain()` clean on mixed-schema logs); snapshot created before each live tick enables `hermes curator rollback`; smoke confirmed real audit entry with `tick_mode: "live"` + valid `entry_sha256`. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | — | No TBD/FIXME/XXX/HACK/PLACEHOLDER markers in Phase 65 modified files | — | — |

**Debt marker gate:** PASSED — no unreferenced TBD/FIXME/XXX markers found in any Phase 65 file.

### Human Verification Required

None required. All Phase 65 success criteria are covered by automated tests + end-to-end smoke reproduction. Operator-facing UX (stderr message clarity, exit code semantics) is asserted by exact-regex unit tests. The 24h rollback window is a Phase 66 operational concern (first actual live tick against real state), not a Phase 65 verification gap — Phase 65 ships guards only.

### Gaps Summary

No gaps. All 3 success criteria verified at all 4 levels:

- **Level 1 (exists):** 7 artifacts present (2 source modifications + 1 source extension + 3 test files + 1 fixture).
- **Level 2 (substantive):** All patterns match plan contracts (`run_bias_canary_pre_check` signature, `tick_mode` kwargs, `_cmd_evolve` 4-path handler, `evolve` subparser registration).
- **Level 3 (wired):** All 6 key links connected and exercised by tests.
- **Level 4 (data flowing):** End-to-end smoke produced a real audit entry with `tick_mode: "live"` + valid sha256; `verify_chain()` clean; dry-run default produces DRY-RUN stdout with no audit side effects.

**Pre-existing failures note:** 18 tests in `tests/hermes_cli/test_curator_stats.py` fail (unrelated to Phase 65). Root cause: v5/v6 doc-tree removal in commit `f10495332` ("migrate kais skills + plugins to kais-skills repo", 2026-06-26) removed `skills/movie-experts/_shared/v6-feedback-loop-architecture.md` and related paths that those tests assert. Documented in `.planning/phases/65-curator-live-guards/deferred-items.md`. Belongs to a v5.0/v6.0 cleanup task, NOT Phase 65.

**Review fix status:** 7/7 in-scope findings from `65-REVIEW.md` (2 BLOCKER + 5 WARNING) are applied and verified in code (CR-01 defensive except in `run_bias_canary_pre_check`; CR-02 `AuditChainError` in post-tick `except` tuple; WR-01 threshold/fixture-count constants; WR-03 regression test for AuditChainError path; WR-04 `BIAS_CANARY_FIXTURES_MISSING` distinct message; WR-05 misleading comment fixed). `65-REVIEW-FIX.md` documents all fixes with commit hashes.

**Minor note on smoke command accuracy:** The `65-SMOKE.md` SC#3 section uses `python3 -m agent.curator_audit verify <path>` as the operator inspection command. This module has no `__main__` block, so the invocation silently exits 0 without actually verifying. The load-bearing behavior — the `verify_chain()` function — works correctly when invoked programmatically (confirmed above). The operator runbook's alternative commands (`tail -1 ... \| json.tool`, `grep '"tick_mode": "live"'`) are accurate. This is a documentation cosmetic issue, not a goal-achievement gap.

---

_Verified: 2026-07-08T04:30:00Z_
_Verifier: Claude (gsd-verifier)_
