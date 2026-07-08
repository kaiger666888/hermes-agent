---
phase: 68
plan: validation
type: validation
created: 2026-07-08
status: ready
success_criteria:
  - SC1: "`hermes orchestrator status` CLI works with rich tables + `--json`"
  - SC2: "Dashboard Jinja2 panel surfaces 3 dimensions real-time"
  - SC3: "CLI + dashboard consume same metrics source (no drift)"
requirements: [OBSRV-04, OBSRV-05]
---

# Phase 68 Validation Strategy

## Test Pyramid

```
                  ┌─────────────────────┐
                  │  Parity test (1)    │  ← SC#3 no-drift invariant
                  └─────────────────────┘
                ┌───────────────────────────┐
                │  Integration tests (5+3)  │  ← CLI + dashboard endpoints
                └───────────────────────────┘
              ┌─────────────────────────────────┐
              │  Unit tests (handler logic)     │  ← _cmd_status shape
              └─────────────────────────────────┘
```

## Per-Task Test Map

### Plan 68-01 (CLI) — `tests/hermes_cli/test_orchestrator_cli.py`

| Test name | What it locks down | SC covered |
|-----------|---------------------|------------|
| `test_status_renders_3_tables` | Output contains "Agent Registry", "Round Table", "Memory Backend" headers | SC1 |
| `test_status_shows_key_metrics` | Output contains `agents_loaded`, `p50_latency_ms`, `search_p95_ms` (or similar) | SC1 |
| `test_json_flag_outputs_valid_json` | `--json` output parses as JSON; has 4 top-level keys (`agent_registry`, `round_table`, `memory_backend`, `snapshot_at`) | SC1, SC3 |
| `test_json_matches_endpoint_shape` | CLI `--json` top-level keys == endpoint `/orchestrator/agents/status` top-level keys | SC3 |
| `test_no_drift_between_cli_and_endpoint` | Both paths call same getters; sub-dict shapes match | SC3 |
| `test_help_lists_status_subcommand` | `hermes orchestrator --help` lists `status` | SC1 |
| `test_registry_failure_graceful` | When `load_agent_registry_with_warnings` raises, CLI exits 0 with `schema_ok=False` rendered (mirror endpoint behavior) | SC1 |

### Plan 68-02 (Dashboard) — `tests/hermes_cli/test_web_server_orchestrator_panel.py`

| Test name | What it locks down | SC covered |
|-----------|---------------------|------------|
| `test_orchestrator_panel_returns_html` | GET `/orchestrator` with auth returns 200 + `text/html` content-type | SC2 |
| `test_orchestrator_panel_requires_auth` | GET `/orchestrator` without auth returns 401 | SC2 (security) |
| `test_orchestrator_panel_contains_3_dimension_sections` | HTML body contains markers for all 3 dimensions (e.g., `id="agent-registry"`, `id="round-table"`, `id="memory-backend"`) | SC2 |
| `test_orchestrator_panel_not_in_public_paths` | `/orchestrator` not in `PUBLIC_API_PATHS` (defensive — it's not `/api/*` so already excluded, but the test locks the invariant) | SC2 (security) |

## Parity Verification (SC#3)

The single load-bearing test is `test_no_drift_between_cli_and_endpoint`:

```python
def test_no_drift_between_cli_and_endpoint():
    """CLI --json and /orchestrator/agents/status must emit identical shapes."""
    # 1. Call CLI handler directly, capture JSON
    cli_json = _run_cli_status_as_json()
    # 2. Call endpoint via TestClient
    endpoint_json = _call_endpoint()
    # 3. Assert top-level keys match
    assert set(cli_json.keys()) == set(endpoint_json.keys())
    # 4. Assert each sub-dict has same keys (values differ due to snapshot_at timestamps)
    for section in ("agent_registry", "round_table", "memory_backend"):
        assert set(cli_json[section].keys()) == set(endpoint_json[section].keys())
```

This works because BOTH paths call the same 3 getters from `agent.observability`. The test is a regression guard — if someone adds a key to the endpoint but not the CLI (or vice versa), this test fails.

## Nyquist Compliance

- **Implementation units:** 3 (CLI module, CLI wiring, dashboard route+template)
- **Test points:** 7 (CLI) + 4 (dashboard) = 11
- **Sampling rate:** 11/3 ≈ 3.7× — above Nyquist minimum of 2×

## Test Infrastructure

- **Framework:** `pytest==9.0.2` (existing)
- **HTTP client:** `fastapi.testclient.TestClient` (existing pattern from `test_web_server_orchestrator_status.py`)
- **CLI invocation:** Direct `_cmd_status(args)` call with a mock `argparse.Namespace` (avoid subprocess for speed + determinism)
- **Rich output capture:** `capsys` fixture (pytest builtin) — `_cmd_status` writes to stdout via `console.print()` which `capsys` captures
- **Auth fixture:** Reuse the `_auth_headers()` pattern from `test_web_server_orchestrator_status.py:25`

## Coverage Exclusions

- **Live GLM/mem0 calls:** Out of scope (Phase 64 handles live eval)
- **SPA integration:** Out of scope (SPA changes require `web/` rebuild — deferred to v14)
- **Browser-side JS rendering:** Out of scope (panel template's JS is verified by HTML structure tests, not by headless browser)

## Acceptance Gates

Before marking Phase 68 complete:

1. **All tests pass:** `python -m pytest tests/hermes_cli/test_orchestrator_cli.py tests/hermes_cli/test_web_server_orchestrator_panel.py -v`
2. **Existing tests unaffected:** `python -m pytest tests/hermes_cli/test_web_server_orchestrator_status.py -v` still passes (Phase 67 regression)
3. **Ruff clean:** `python -m ruff check hermes_cli/orchestrator.py hermes_cli/web_templates/ tests/hermes_cli/test_orchestrator_cli.py tests/hermes_cli/test_web_server_orchestrator_panel.py`
4. **Manual smoke (operator):** `hermes orchestrator status` renders 3 tables; `hermes orchestrator status --json | jq .` produces valid JSON (documented in VERIFICATION.md, not automated)
