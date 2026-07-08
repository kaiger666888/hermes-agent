---
phase: 68
plan: 01
name: orchestrator-cli
subsystem: observability
tags: [cli, observability, orchestrator, rich-tables, obsrv-04]
requires:
  - "Phase 67 OBSRV-01/02/03 collectors (agent.observability getters)"
  - "Phase 67 /orchestrator/agents/status endpoint (shape reference)"
provides:
  - "hermes orchestrator status CLI command (rich tables + --json)"
  - "_build_snapshot() shared shape builder (parity source of truth)"
affects:
  - "hermes_cli/main.py (orchestrator_parser wiring + _BUILTIN_SUBCOMMANDS)"
tech-stack:
  added: []
  patterns:
    - "argparse subparser registration (mirror hermes_cli/curator.py:1419)"
    - "Rich tables (rich.table.Table + rich.console.Console)"
    - "Lazy imports for agent.observability (mirror endpoint pattern)"
    - "Single-shape builder (_build_snapshot) for cross-surface parity"
key-files:
  created:
    - "hermes_cli/orchestrator.py"
    - "tests/hermes_cli/test_orchestrator_cli.py"
  modified:
    - "hermes_cli/main.py (2 edits: _BUILTIN_SUBCOMMANDS + orchestrator_parser block)"
decisions:
  - "G1: NEW top-level 'orchestrator' command group (not subcommand of 'status') — future-proofs for inspect/history verbs"
  - "GA1: registry load failure → exit 0 with schema_ok=False (mirror endpoint graceful degradation)"
  - "GA2: --json output is byte-identical in shape to /orchestrator/agents/status (modulo snapshot_at timestamp)"
metrics:
  duration: "~12 minutes"
  completed: 2026-07-08
  tasks: 3
  files_created: 2
  files_modified: 1
  tests_added: 7
---

# Phase 68 Plan 01: Orchestrator CLI Summary

Implemented `hermes orchestrator status` CLI command with 3 rich tables for the v10.0 orchestrator observability dimensions (agent registry / round table / memory backend) + `--json` flag for script consumption.

## Deliverables

### Created
- **`hermes_cli/orchestrator.py`** (294 lines) — `register_cli(parent)` builder + `_cmd_status(args)` handler + `_build_snapshot()` shared shape builder + `_render_tables(snapshot)` rich rendering helper. Three formatting helpers (`_bool_mark`, `_fmt_ms`, `_fmt_pct`) keep the table rendering DRY.
- **`tests/hermes_cli/test_orchestrator_cli.py`** (211 lines) — 7 tests covering: 3-table render, key metric visibility, `--json` valid JSON, endpoint shape parity (SC#3), no-drift regression guard, parser recognizes `status` subcommand, registry failure graceful exit.

### Modified
- **`hermes_cli/main.py`** (2 surgical edits):
  1. Added `"orchestrator"` to `_BUILTIN_SUBCOMMANDS` frozenset (line ~11084) — prevents argv pre-dispatch from misclassifying `hermes orchestrator status` as a plugin command.
  2. Added `orchestrator_parser` block (15 lines) after `curator_parser` (line ~11977) — mirrors the curator pattern: `subparsers.add_parser(...)` + lazy import of `register_cli`.

## SC Coverage

| Success Criterion | Status | Evidence |
|-------------------|--------|----------|
| SC#1: `hermes orchestrator status` rich tables + `--json` | ✅ | `test_status_renders_3_tables` + `test_json_flag_outputs_valid_json` |
| SC#3: CLI + dashboard same metrics source | ✅ | `test_json_matches_endpoint_shape` + `test_no_drift_between_cli_and_endpoint` (CLI calls same getters as endpoint) |

## Threat Mitigations

| Threat | Mitigation | Test |
|--------|------------|------|
| T-68-01-drift (shape drift between CLI + endpoint) | `_build_snapshot()` single source; parity test enforces key-set equality | `test_no_drift_between_cli_and_endpoint` |
| T-68-01-crash (registry load failure) | try/except → `schema_ok=False`, exit 0 | `test_registry_failure_graceful` |
| T-68-01-cycle (module-load cycle) | Lazy imports inside `_build_snapshot` body | (structural — mirror endpoint pattern) |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all data flows from Phase 67 getters (no placeholders, no TODOs).

## Test Results

```
tests/hermes_cli/test_orchestrator_cli.py: 7/7 PASSED
tests/hermes_cli/test_web_server_orchestrator_status.py: 5/5 PASSED (Phase 67 regression)
```

## Self-Check: PASSED

- `hermes_cli/orchestrator.py` exists (committed ae0aef87a)
- `tests/hermes_cli/test_orchestrator_cli.py` exists (committed d2028b3eb)
- 7/7 new tests pass
- 5/5 Phase 67 tests still pass
- No `open()` calls in new code (Ruff PLW1514 N/A)
