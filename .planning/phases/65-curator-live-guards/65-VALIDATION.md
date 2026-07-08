---
phase: 65
slug: curator-live-guards
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-08
---

# Phase 65 — Validation Strategy

> Per-phase validation contract for curator `--live` flag + bias canary pre-check + audit log tick_mode extension.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest==9.0.2` + `pytest-asyncio==1.3.0` + `pytest-timeout==2.4.0` (existing) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (line 261) |
| **Quick run command** | `python -m pytest tests/hermes_cli/test_curator_evolve_cli.py tests/agent/test_curator_live_guards.py -x -q` |
| **Full suite command** | `python -m pytest tests/agent/test_curator*.py tests/hermes_cli/test_curator*.py tests/v11-bias-canary/ -x -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **Per task commit:** Quick suite (<10s)
- **Per wave merge:** Full Phase 65 + regression suite (<30s)
- **Before `/gsd:verify-work`:** Full suite green + live CLI smoke (`hermes curator evolve` shows dry-run preview; `hermes curator evolve --live` aborts on canary if test fixtures missing)
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 65-01-01 | 01 (fixtures + pre-check + audit extension) | 0 | CURATE-02 | — | `run_bias_canary_pre_check()` catches ≥4/5 known-bad | unit | `python -m pytest tests/agent/test_curator_live_guards.py::test_pre_check_catches_four_of_five -x` | ❌ W0 | ⬜ pending |
| 65-01-02 | 01 | 0 | CURATE-03 | — | `append_audit(tick_mode="live", ...)` writes entry with new field | unit | `python -m pytest tests/agent/test_curator_live_guards.py::test_append_audit_with_tick_mode -x` | ❌ W0 | ⬜ pending |
| 65-01-03 | 01 | 0 | CURATE-03 (backward compat) | — | `append_audit(...)` without `tick_mode` still works (legacy callers) | unit | `python -m pytest tests/agent/test_curator_live_guards.py::test_append_audit_backward_compat -x` | ❌ W0 | ⬜ pending |
| 65-01-04 | 01 | 0 | CURATE-03 (mixed schema) | — | `verify_chain()` passes on mixed-schema log | unit | `python -m pytest tests/agent/test_curator_live_guards.py::test_verify_chain_mixed_schema -x` | ❌ W0 | ⬜ pending |
| 65-02-01 | 02 (CLI wiring) | 1 | CURATE-01 | — | `hermes curator evolve` (no flag) → dry-run preview, exit 0 | unit | `python -m pytest tests/hermes_cli/test_curator_evolve_cli.py::TestEvolveCommand::test_default_is_dry_run -x` | ❌ W0 | ⬜ pending |
| 65-02-02 | 02 | 1 | CURATE-01 | — | `hermes curator evolve --live` calls `run_curator_review(dry_run=False)` | unit | `python -m pytest tests/hermes_cli/test_curator_evolve_cli.py::TestEvolveCommand::test_live_flag_triggers_live_path -x` | ❌ W0 | ⬜ pending |
| 65-02-03 | 02 | 1 | CURATE-02 | — | `evolve --live` aborts with exit 2 when canary catches <4 | unit | `python -m pytest tests/hermes_cli/test_curator_evolve_cli.py::TestEvolveCommand::test_live_aborts_on_canary_failure -x` | ❌ W0 | ⬜ pending |
| 65-02-04 | 02 | 1 | CURATE-02 | — | Canary failure msg format `BIAS_CANARY_FAILED: caught N/5 (threshold: 4)` | unit | `python -m pytest tests/hermes_cli/test_curator_evolve_cli.py::TestEvolveCommand::test_canary_failure_message_format -x` | ❌ W0 | ⬜ pending |
| 65-02-05 | 02 | 1 | CURATE-01 (skip-canary) | V4 Access Control (`--skip-canary` escape hatch logged) | `--skip-canary` bypasses pre-check; audit logs `canary_pass=None` | unit | `python -m pytest tests/hermes_cli/test_curator_evolve_cli.py::TestEvolveCommand::test_skip_canary_bypasses_pre_check -x` | ❌ W0 | ⬜ pending |
| 65-02-06 | 02 | 1 | EXPERT-04 regression | — | Existing curator subcommands (status/run/pin/etc) still work | regression | `python -m pytest tests/hermes_cli/test_curator_cli.py tests/agent/test_curator.py -x` | ✅ (existing) | ⬜ pending |
| 65-03-01 | 03 (smoke) | 2 | CURATE-01 (operator-visible) | — | `hermes curator evolve` (no --live) prints "DRY RUN" marker | integration | `python -c "import subprocess, sys; r = subprocess.run([sys.executable, '-m', 'hermes_cli.curator', 'evolve'], capture_output=True, text=True, env={'HERMES_HOME': '/tmp/q'}); assert 'DRY RUN' in r.stdout or 'dry-run' in r.stdout.lower()"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/fixtures/curator_bias_canary/known_bad_records.jsonl` — 5 records covering 4 deterministic failure modes + 1 LLM-only
- [ ] `tests/agent/test_curator_live_guards.py` — covers `run_bias_canary_pre_check` + `append_audit` tick_mode extension + backward compat + mixed schema + timestamp
- [ ] `tests/hermes_cli/test_curator_evolve_cli.py` — covers `_cmd_evolve` parsing + exit codes + canary failure UX
- [ ] Extend `tests/hermes_cli/test_curator_cli.py::NEW_V6_SUBCOMMANDS` to include `"evolve"` (regression guard)
- [ ] `agent/curator.py` — add `run_bias_canary_pre_check(seed_records_path: Path) -> tuple[bool, int, list[str]]` near `run_curator_review`
- [ ] `agent/curator_audit.py` — extend `append_audit` to accept optional `tick_mode: str` + `canary_pass: bool | None` fields
- [ ] `hermes_cli/curator.py` — add `evolve` subcommand in `register_cli` + `_cmd_evolve` function

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Audit log inspection on live system | CURATE-03 (operator UX) | Real `~/.hermes/skills/.audit/log.jsonl` inspection requires running on Kai's machine with existing audit history | Operator reads last N entries after Phase 66 1st live tick; verifies `tick_mode: "live"` field populated + sha256 chain still verifies via `python -m agent.curator_audit verify ~/.hermes/skills/.audit/log.jsonl` |

*All other behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (3 new test files + fixture + 3 module extensions)
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending planner/checker confirmation
