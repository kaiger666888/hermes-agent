---
phase: 67-observability-backend
plan: 04
subsystem: observability
tags: [observability, fastapi, http-endpoint, integration-tests, tdd, wave-2]
requires:
  - "agent.observability.get_agent_registry_metrics (Plan 67-01 Wave 0)"
  - "agent.observability.round_table_metrics.get_round_table_metrics (Plan 67-02 Wave 1)"
  - "agent.observability.memory_backend_metrics.get_memory_backend_metrics (Plan 67-03 Wave 1)"
  - "agent.registry_loader.load_agent_registry_with_warnings (Phase 63)"
  - "hermes_cli.web_server FastAPI app (existing)"
provides:
  - "GET /orchestrator/agents/status FastAPI route (unified 3-section JSON snapshot)"
  - "agent.observability.__init__ consolidated 3-getter re-export surface"
affects:
  - "Phase 68 CLI hermes orchestrator status (reads the endpoint)"
  - "Phase 68 dashboard SPA Jinja2 observability panel (consumes the JSON)"
  - "v14 Prometheus exporter (the dict is scrape-able without rework)"
tech-stack:
  added: []
  patterns:
    - "sync FastAPI handler (plain `def`, not `async def`) — threadpool dispatch (Pitfall 4)"
    - "_require_token(request) as the auth gate inside the handler body (Pitfall 5)"
    - "lazy imports inside handler body (Pitfall 6 — module-load cycle avoidance)"
    - "try/except degrade-to-schema_validation_ok=False on loader failure (V7 error handling)"
    - "single-import re-export surface via __init__.py consolidation"
    - "TDD RED/GREEN per task (test commit precedes feat commit)"
key-files:
  created:
    - path: "tests/hermes_cli/test_web_server_orchestrator_status.py"
      lines: 166
      purpose: "5 integration tests: 200 happy path (4 top-level keys + 6 OBSRV-01 fields), 401 auth gate, NOT-in-PUBLIC_API_PATHS invariant, registry-failure graceful degrade"
  modified:
    - path: "hermes_cli/web_server.py"
      lines_added: 50
      lines_removed: 0
      purpose: "GET /orchestrator/agents/status handler inserted after /api/system/stats (line ~1992), before curator section"
    - path: "agent/observability/__init__.py"
      lines_added: 17
      lines_removed: 13
      purpose: "Re-export consolidation — now ships get_round_table_metrics + get_memory_backend_metrics alongside Plan 01's get_agent_registry_metrics"
decisions:
  - id: "D-67-04-1"
    decision: "Insert the endpoint between /api/system/stats and the curator section (line ~1992), NOT at line 1913"
    rationale: "Plan said 'near line 1913' (where /api/system/stats STARTS). Inserting after its return keeps observability endpoints grouped (system stats, then orchestrator status, then curator) and avoids disturbing the existing decorator-position numbering cited in CONTEXT/RESEARCH. The diff is a clean append-after-return."
  - id: "D-67-04-2"
    decision: "Use `agent.round_table_state._now_iso` for snapshot_at (mirrors Plan 67-02 instrumentation choice)"
    rationale: "Existing codebase utility for ISO-8601 UTC timestamps. Plan action specified this — same helper used by round_table_state.py for lastUpdatedAt fields, so timestamps are uniform across the orchestrator stack."
  - id: "D-67-04-3"
    decision: "Consolidate __init__.py re-exports in the SAME commit as the endpoint, not as a separate Task 3 commit"
    rationale: "Plan listed 3 tasks but Task 2 (endpoint) cannot function without Task 3 (re-exports) — the handler does `from agent.observability import get_round_table_metrics, get_memory_backend_metrics` which would ImportError without the consolidation. Splitting them would leave a RED intermediate state between commits. Combined into one GREEN commit that ships working software."
  - id: "D-67-04-4"
    decision: "Test auth pattern: set app.state.auth_required = False in try/finally + inject X-Hermes-Session-Token header"
    rationale: "Mirrors test_web_server_host_header.py convention. The finally block clears app.state.auth_required so subsequent tests inherit the default (gate not engaged). The X-Hermes-Session-Token header is the loopback-mode auth surface (auth_middleware short-circuits when auth_required=True; our path is /orchestrator/* not /api/* so the middleware never even sees it — _require_token inside the handler is the sole gate)."
metrics:
  duration: "5m"
  completed: "2026-07-08"
  tasks_total: 3
  tasks_completed: 3
  tests_added: 5
  tests_passing: 5
  files_created: 1
  files_modified: 2
  lines_added: 233
---

# Phase 67 Plan 04: FastAPI /orchestrator/agents/status Endpoint Summary

Ships the OBSRV-01 HTTP surface — a single `GET /orchestrator/agents/status` endpoint on the existing `hermes dashboard` FastAPI app that returns a unified JSON snapshot of agent registry health (OBSRV-01), round table metrics (OBSRV-02), and memory backend metrics (OBSRV-03). Plans 67-01/02/03 collectors now flow to operators through one URL. Plus 5 integration tests via `fastapi.testclient.TestClient` enforcing the contract, the auth gate, the PUBLIC_API_PATHS security invariant, and graceful registry-failure degrade.

## What Was Built

### `hermes_cli/web_server.py` — GET /orchestrator/agents/status handler (+50 lines)

Inserted between `/api/system/stats` and the curator section. Plain `def` handler (RESEARCH Pitfall 4 — sync handler runs in FastAPI threadpool, never blocks event loop).

```python
@app.get("/orchestrator/agents/status")
def get_orchestrator_agents_status(request: Request):
    _require_token(request)  # Pitfall 5
    # Lazy imports (Pitfall 6)
    from agent.observability import (
        get_agent_registry_metrics, get_round_table_metrics, get_memory_backend_metrics,
    )
    from agent.registry_loader import load_agent_registry_with_warnings
    from agent.round_table_state import _now_iso as _state_now_iso

    try:
        entries, missing = load_agent_registry_with_warnings()
        schema_ok = True
    except Exception as exc:  # V7 — never 500
        _log.warning("orchestrator status: registry load failed: %s", exc)
        entries, missing, schema_ok = [], [], False

    return {
        "agent_registry": get_agent_registry_metrics(entries, missing, schema_ok),
        "round_table": get_round_table_metrics(),
        "memory_backend": get_memory_backend_metrics(),
        "snapshot_at": _state_now_iso(),
    }
```

**Threat mitigations:**
- T-67-01 (info disclosure) — `_require_token(request)` first line; NOT in PUBLIC_API_PATHS (test enforces)
- T-67-01-exception (500 on registry failure) — try/except degrades to `schema_validation_ok=False`
- T-67-01-loop (sync handler blocks loop) — plain `def`, threadpool dispatch

### `agent/observability/__init__.py` — re-export consolidation (+17/-13 lines)

Wave 2 unifies the package's public surface. Plans 01/02/03 deliberately left this file to Plan 04 to avoid Wave 1 sibling overlap; this plan appends the two missing re-exports:

```python
from agent.observability.agent_registry_metrics import get_agent_registry_metrics
from agent.observability.memory_backend_metrics import get_memory_backend_metrics
from agent.observability.round_table_metrics import get_round_table_metrics

__all__ = [
    "get_agent_registry_metrics",
    "get_memory_backend_metrics",
    "get_round_table_metrics",
]
```

Now `from agent.observability import get_agent_registry_metrics, get_round_table_metrics, get_memory_backend_metrics` works in one statement (verified by runtime check + the endpoint's own import).

### `tests/hermes_cli/test_web_server_orchestrator_status.py` — 5 integration tests (NEW, 166 lines)

`class TestOrchestratorAgentsStatus:` exercises the contract via `fastapi.testclient.TestClient`:

| Test | What it asserts |
|------|-----------------|
| `test_status_returns_all_sections` | 200 + 4 top-level keys (`agent_registry`, `round_table`, `memory_backend`, `snapshot_at`) with correct value types |
| `test_agent_registry_section_shape` | `agent_registry` sub-dict has all 6 OBSRV-01 fields with correct types |
| `test_status_requires_auth` | 401 when called without `X-Hermes-Session-Token` (Pitfall 5 enforcement) |
| `test_status_not_in_public_paths` | `assert "/orchestrator/agents/status" not in PUBLIC_API_PATHS` (security invariant) |
| `test_registry_failure_graceful` | Mocked loader raising → 200 with `schema_validation_ok=False`, NOT 500 |

Auth pattern: each test sets `app.state.auth_required = False` in a `try/finally` block (loopback mode) and injects the `X-Hermes-Session-Token: <_SESSION_TOKEN>` header for authenticated cases. Mirrors the convention in `test_web_server_host_header.py`.

## How to Use

```bash
# Operator curl (loopback mode — token in Authorization header)
$ hermes dashboard &
$ TOKEN=$(python -c "from hermes_cli.web_server import _SESSION_TOKEN; print(_SESSION_TOKEN)")
$ curl -H "X-Hermes-Session-Token: $TOKEN" http://localhost:9119/orchestrator/agents/status | jq .
{
  "agent_registry": {
    "agents_loaded": 21,
    "schema_validation_ok": true,
    "missing_experts": [],
    "lineage_integrity_ok": true,
    "agent_names": ["screenplay", "drawer", "colorist", ...],
    "snapshot_at_iso": "2026-07-08T..."
  },
  "round_table": {
    "count": 42, "p50_latency_ms": 1234.5, "p95_latency_ms": 2890.1,
    "status_distribution": {"ok": 38, "serial_violation": 3, ...}, ...
  },
  "memory_backend": {
    "search_p95_ms": 95.05, "add_count": 12, "error_rate": 0.0,
    "conflict_count": 3, "status": "ok", ...
  },
  "snapshot_at": "2026-07-08T..."
}

# Unauthenticated — rejected at the auth gate
$ curl -i http://localhost:9119/orchestrator/agents/status
HTTP/1.1 401 Unauthorized
{"detail":"Unauthorized"}
```

Phase 68 CLI `hermes orchestrator status` will wrap this with rich tables; the dashboard SPA will consume the JSON in an observability panel.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Absolute-path Write tool wrote to main repo, not the worktree (#3099)**
- **Found during:** Task 1 (initial Write call)
- **Issue:** `Write(file_path="/data/workspace/hermes-agent/tests/...")` resolves to the **main repo** path, not the worktree at `/data/workspace/hermes-agent/.claude/worktrees/agent-ad3869d492e332807/tests/...`. The file silently landed in the main repo and was invisible to `pytest` running in the worktree.
- **Fix:** Deleted the leaked main-repo file; re-wrote using the worktree-prefixed absolute path `/data/workspace/hermes-agent/.claude/worktrees/agent-ad3869d492e332807/tests/...`. All subsequent Write/Edit calls in this plan used the worktree-prefixed form.
- **Files modified:** None in the main repo (verified via `git -C /data/workspace/hermes-agent status --short tests/hermes_cli/test_web_server_orchestrator_status.py`).
- **Verification:** `ls tests/hermes_cli/test_web_server_orchestrator_status.py` from inside the worktree succeeds.

**2. [Plan-order adjustment] Tasks 2 + 3 collapsed into one GREEN commit**
- **Found during:** Task 2 implementation
- **Issue:** Plan listed 3 sequential tasks, but Task 2 (endpoint) imports `get_round_table_metrics` and `get_memory_backend_metrics` from `agent.observability` — which would ImportError without Task 3's `__init__.py` consolidation. Splitting into two commits would leave a non-functional intermediate state (RED-with-extra-context, not GREEN).
- **Fix:** Combined the endpoint + re-export consolidation into a single GREEN commit (`396e19eab`). The TDD intent (test-first, then implementation) is preserved: RED commit `fbc56795b` precedes the combined GREEN commit. All 5 integration tests pass post-commit.
- **Files modified:** `hermes_cli/web_server.py` + `agent/observability/__init__.py` in the same commit.

### Deferred Issues

None.

## TDD Gate Compliance

Per-task TDD cycle followed strictly. Gate sequence verified in git log:

| Task | Phase | Commit | Hash |
|------|-------|--------|------|
| 1 | RED (test) | `test(67-04): add failing integration tests for /orchestrator/agents/status` | `fbc56795b` |
| 2+3 | GREEN (feat) | `feat(67-04): implement /orchestrator/agents/status endpoint (GREEN)` | `396e19eab` |

Task 1 RED confirmed at execution time: 4 of 5 tests failed with 404 (endpoint missing); the `test_status_not_in_public_paths` test passed pre-endpoint (validates the security invariant holds independent of endpoint existence — defensive depth).

No REFACTOR phase needed — implementation is already minimal (50 lines of handler logic, single-responsibility, no duplication).

## Verification Results

**Integration tests:** `python -m pytest tests/hermes_cli/test_web_server_orchestrator_status.py -x`
- 5 tests collected, 5 passed in 0.83s

**Full Phase 67 suite:** `python -m pytest tests/agent/observability/ tests/hermes_cli/test_web_server_orchestrator_status.py -x`
- 43 tests collected (Wave 0: 17 + Plan 02: 13 + Plan 03: 8 + Plan 04: 5 = 43), 43 passed in 1.41s
- Well under the 5s feedback-latency budget (VALIDATION.md)

**Re-export consolidation runtime check:**
```
$ python -c "from agent.observability import get_agent_registry_metrics, get_round_table_metrics, get_memory_backend_metrics; print('all 3 getters importable in one statement')"
all 3 getters importable in one statement
```

**Auth gate invariant:**
```
$ python -c "from hermes_cli.dashboard_auth.public_paths import PUBLIC_API_PATHS; assert '/orchestrator/agents/status' not in PUBLIC_API_PATHS; print('auth gate invariant OK')"
auth gate invariant OK
```

**CLAUDE.md compliance verified:**
- `from __future__ import annotations` not added to web_server.py (existing 12k-line module does not use it; handler uses only stdlib types + already-imported FastAPI types — no PEP 604 / forward-ref need). The `__init__.py` does have it (consistent with Wave 0).
- Lazy imports inside the handler body per Pitfall 6 (matches existing `from hermes_state import SessionDB` pattern at line 1797).
- `%s` positional log formatting: `_log.warning("orchestrator status: registry load failed: %s", exc)` — no f-strings in log calls.
- `except Exception as exc:` binds the exception name; no bare `except:`.
- 4-space indent, double-quoted strings throughout the new code.
- No `open()` calls in the new handler (PLW1514 trivially satisfied).
- `get_hermes_home()` used everywhere applicable (no `Path.home() / ".hermes"`).

## Scope Boundary Adherence

Strict scope guard honored. `git diff --name-only HEAD~2 HEAD` shows exactly the 3 files in the plan's `files_modified` frontmatter — 1:1 match:

- `tests/hermes_cli/test_web_server_orchestrator_status.py` (NEW)
- `hermes_cli/web_server.py` (endpoint added)
- `agent/observability/__init__.py` (re-export consolidation)

**Not touched (verified):**
- `STATE.md` / `ROADMAP.md` / `REQUIREMENTS.md` — per orchestrator instruction
- `hermes_cli/dashboard_auth/public_paths.py` — explicitly left unchanged (test enforces this)
- `mcp_serve.py`, `agent/registry_loader.py`, `agent/round_table_state.py` — read-only consumers, no modification
- Any file under `tests/agent/observability/` — owned by Plans 01/02/03
- No tracked-file deletions across both commits

## Known Stubs

None. The endpoint is fully wired:
- All 3 collector getters are imported from real modules (no placeholders).
- `load_agent_registry_with_warnings` is the live Phase 63 loader (not mocked in production path; only mocked in the registry-failure test).
- `snapshot_at` uses `agent.round_table_state._now_iso` (real ISO-8601 UTC timestamp).
- No TODOs, FIXMEs, or hardcoded "coming soon" placeholders.

## Threat Flags

None new. The threat surface introduced by this plan (the HTTP endpoint) is fully covered by the plan's `<threat_model>` mitigations:

- T-67-01 (info disclosure) → mitigated by `_require_token(request)` + NOT in `PUBLIC_API_PATHS` (verified by `test_status_requires_auth` + `test_status_not_in_public_paths`).
- T-67-01-recon (spoofing via leaked agent names) → same auth gate.
- T-67-01-exception (registry 500 → dashboard crash) → mitigated by try/except degrade (verified by `test_registry_failure_graceful`).
- T-67-01-loop (sync handler blocks event loop) → mitigated by plain `def` (visual inspection).

No new network endpoints beyond the one specified; no new auth paths (delegates to existing `_require_token`); no schema changes at trust boundaries.

## Unblocks

- **Phase 68 CLI** (`hermes orchestrator status`) — fetches `/orchestrator/agents/status` and renders rich tables.
- **Phase 68 dashboard SPA** — Jinja2 panel consuming the JSON.
- **v14 Prometheus exporter** — the dict shape is scrape-able without rework.
- **Phase 67 milestone close** — Plan 04 was the last of 4 plans; full Phase 67 suite is green and ready for `/gsd:verify-work`.

## Self-Check: PASSED

- [x] `tests/hermes_cli/test_web_server_orchestrator_status.py` exists (FOUND, 166 lines)
- [x] `hermes_cli/web_server.py` references `@app.get("/orchestrator/agents/status")` (FOUND)
- [x] `agent/observability/__init__.py` references `get_round_table_metrics` + `get_memory_backend_metrics` (FOUND)
- [x] Commit `fbc56795b` exists (RED Task 1)
- [x] Commit `396e19eab` exists (GREEN Tasks 2+3)
- [x] `python -m pytest tests/hermes_cli/test_web_server_orchestrator_status.py -x` exits 0 (5 passed in 0.83s)
- [x] `python -m pytest tests/agent/observability/ tests/hermes_cli/test_web_server_orchestrator_status.py -x` exits 0 (43 passed in 1.41s)
- [x] `python -c "from agent.observability import get_agent_registry_metrics, get_round_table_metrics, get_memory_backend_metrics"` succeeds (single-import surface works)
- [x] `python -c "from hermes_cli.dashboard_auth.public_paths import PUBLIC_API_PATHS; assert '/orchestrator/agents/status' not in PUBLIC_API_PATHS"` exits 0 (security invariant holds)
- [x] `git diff --name-only HEAD~2 HEAD` matches strict scope (3 files, 1:1 with plan frontmatter)
- [x] No modifications to forbidden files (`public_paths.py`, `STATE.md`, `ROADMAP.md`, `tests/agent/observability/*`)
