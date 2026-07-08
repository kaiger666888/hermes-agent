---
phase: 68
plan: 02
name: orchestrator-dashboard-panel
subsystem: observability
tags: [dashboard, observability, orchestrator, jinja2, fastapi, obsrv-05]
requires:
  - "Phase 67 /orchestrator/agents/status endpoint (data source)"
  - "Phase 68-01 _build_snapshot() shared shape (parity reference)"
provides:
  - "GET /orchestrator auth-gated HTML panel"
  - "hermes_cli/web_templates/orchestrator.html static template"
affects:
  - "hermes_cli/web_server.py (new route + WEB_TEMPLATE_DIR constant)"
tech-stack:
  added: []
  patterns:
    - "FileResponse for static HTML panel (no Jinja2 substitution needed)"
    - "Client-side fetch + textContent-only inserts (XSS mitigation)"
    - "Route declared before mount_spa() catchall (FastAPI ordering)"
    - "?token=xxx query param fallback for loopback auth"
key-files:
  created:
    - "hermes_cli/web_templates/orchestrator.html"
    - "tests/hermes_cli/test_web_server_orchestrator_panel.py"
  modified:
    - "hermes_cli/web_server.py (1 route + WEB_TEMPLATE_DIR constant)"
decisions:
  - "Static HTML file (not Jinja2 template) — no server-side data to substitute; all data client-side fetched"
  - "Auth gate inside handler via _require_token — /orchestrator is NOT under /api/* so middleware auto-gate does not apply"
  - "textContent-only dynamic inserts — threat T-68-02-xss mitigation"
  - "?token=xxx query param fallback for loopback mode (operator navigates from SPA)"
metrics:
  duration: "~10 minutes"
  completed: 2026-07-08
  tasks: 3
  files_created: 2
  files_modified: 1
  tests_added: 4
---

# Phase 68 Plan 02: Dashboard Panel Summary

Implemented the dashboard observability panel at `/orchestrator` URL on the existing `hermes dashboard` FastAPI server. The panel surfaces all 3 Phase 67 observability dimensions via client-side fetch, with auth gate matching the data endpoint.

## Deliverables

### Created
- **`hermes_cli/web_templates/orchestrator.html`** (290 lines) — static HTML with dark theme, 3 dimension sections (`id="agent-registry"`, `id="round-table"`, `id="memory-backend"`), each with a metrics table. Client-side JS fetches `/orchestrator/agents/status` on load + every 30s, populates via `textContent` only (XSS mitigation). Refresh button + last-refresh timestamp.
- **`tests/hermes_cli/test_web_server_orchestrator_panel.py`** (121 lines) — 4 tests: returns_html (200 + text/html), requires_auth (401 without token), contains_3_dimension_sections (id markers), not_in_public_paths (security invariant).

### Modified
- **`hermes_cli/web_server.py`** (2 surgical edits):
  1. Added `WEB_TEMPLATE_DIR = Path(__file__).parent / "web_templates"` constant near `WEB_DIST` (line 107).
  2. Added `@app.get("/orchestrator")` route (30 lines) before the existing `/orchestrator/agents/status` endpoint. Calls `_require_token(request)` + returns `FileResponse(panel_path, media_type="text/html")`.

## SC Coverage

| Success Criterion | Status | Evidence |
|-------------------|--------|----------|
| SC#2: Dashboard panel surfaces 3 dimensions real-time | ✅ | `test_orchestrator_panel_contains_3_dimension_sections` + `test_orchestrator_panel_returns_html`; template's JS fetches live data on load + 30s interval |
| SC#3: CLI + dashboard same metrics source | ✅ | Both consume `agent.observability` getters — CLI via `_build_snapshot()`, dashboard via HTTP fetch of endpoint that calls same getters |

## Threat Mitigations

| Threat | Mitigation | Test |
|--------|------------|------|
| T-68-02-public (added to PUBLIC_API_PATHS) | `test_orchestrator_panel_not_in_public_paths` | ✅ |
| T-68-02-noauth (handler forgets _require_token) | `test_orchestrator_panel_requires_auth` + mirror endpoint pattern | ✅ |
| T-68-02-xss (innerHTML on agent names) | `textContent`-only setters throughout template JS | (code review — no `innerHTML` in template) |
| T-68-02-cycle (module-top import) | `FileResponse` + `Path(__file__).parent` — no extra imports | (structural) |

## Deviations from Plan

**[Rule 2 - Critical functionality] Auth mode documentation gap:**
- **Found during:** Task 2 implementation
- **Issue:** Plan didn't specify how the panel authenticates in loopback mode (direct browser visit has no SPA-injected token).
- **Fix:** Template's JS reads `?token=xxx` query param as fallback. Handler docstring documents both loopback (`?token=`) and OAuth (cookie) modes. UX rough edge documented for v14 polish (operator navigates from SPA which appends token).
- **Files modified:** `orchestrator.html` (JS token resolver), `web_server.py` (handler docstring).
- **Commit:** 6d8f5ee4d

## Known Stubs

None — all data flows from the live `/orchestrator/agents/status` endpoint via client-side fetch.

## Test Results

```
tests/hermes_cli/test_web_server_orchestrator_panel.py: 4/4 PASSED
tests/hermes_cli/test_web_server_orchestrator_status.py:  5/5 PASSED (Phase 67 regression)
tests/hermes_cli/test_orchestrator_cli.py:                7/7 PASSED (Phase 68-01 regression)
Total: 16/16 PASSED in 1.05s
```

## Self-Check: PASSED

- `hermes_cli/web_templates/orchestrator.html` exists (committed 6d8f5ee4d)
- `tests/hermes_cli/test_web_server_orchestrator_panel.py` exists (committed c60e25093)
- `hermes_cli/web_server.py` route `@app.get("/orchestrator")` exists (grep-verified)
- 4/4 new tests pass
- 12/12 Phase 67 + Phase 68-01 tests still pass
- No `innerHTML` in template (XSS mitigation verified)
- `/orchestrator` NOT in PUBLIC_API_PATHS (test asserts)
