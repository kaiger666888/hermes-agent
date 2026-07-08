# Phase 68 Research: OBSERVABILITY-PRESENTATION

**Researched:** 2026-07-08
**Status:** Ready for planning
**Mode:** Inline autonomous (no sub-agent spawning)

<domain_summary>
## Phase Boundary

Two presentation surfaces consuming the SAME Phase 67 metrics source:

1. **CLI:** `hermes orchestrator status` — Rich tables showing 3 dimensions + `--json` flag
2. **Dashboard:** Jinja2 panel at `/orchestrator` URL on the existing `hermes dashboard` FastAPI server

**Phase 67 already ships:**
- `agent.observability.get_agent_registry_metrics(entries, missing, schema_ok)` → 6-key dict
- `agent.observability.get_round_table_metrics()` → 9-key dict
- `agent.observability.get_memory_backend_metrics()` → 8-key dict
- `/orchestrator/agents/status` FastAPI endpoint returning `{agent_registry, round_table, memory_backend, snapshot_at}` (auth-gated via `_require_token`, NOT in PUBLIC_API_PATHS)

</domain_summary>

<code_research>
## CLI Registration Pattern

### Where to add `orchestrator` group

**File:** `hermes_cli/main.py` (around line 11958, immediately after `curator_parser` block)

**Pattern (mirrors `curator_parser` at line 11960):**
```python
orchestrator_parser = subparsers.add_parser(
    "orchestrator",
    help="Operator observability (orchestrator status)",
    description=(
        "Operator visibility into the v10.0 orchestrator: agent registry "
        "health, round-table latency/token cost, and memory backend status. "
        "All metrics come from Phase 67 collectors (agent.observability)."
    ),
)
try:
    from hermes_cli.orchestrator import register_cli as _register_orchestrator_cli
    _register_orchestrator_cli(orchestrator_parser)
except Exception as _exc:
    logging.getLogger(__name__).debug("orchestrator CLI wiring failed: %s", _exc)
```

**Plus add `"orchestrator"` to `_BUILTIN_SUBCOMMANDS` frozenset** at line 11079 (or it'll be misclassified as plugin command during argv pre-dispatch).

### `hermes_cli/orchestrator.py` skeleton (mirror `hermes_cli/curator.py:1419`)

```python
def register_cli(parent: argparse.ArgumentParser) -> None:
    parent.set_defaults(func=lambda a: (parent.print_help(), 0)[1])
    subs = parent.add_subparsers(dest="orchestrator_command")
    p_status = subs.add_parser("status", help="Show orchestrator observability snapshot")
    p_status.add_argument("--json", dest="as_json", action="store_true",
                          help="Emit JSON (same shape as /orchestrator/agents/status)")
    p_status.set_defaults(func=_cmd_status)
```

### Handler contract

`_cmd_status(args) -> int` — returns 0 on success, 1 on hard failure (matches every other `_cmd_*` in `curator.py`).

## Rich Table API

**Dependency:** `rich==14.3.3` (already in core deps, used by `hermes_cli/curator.py:1138, 1255, 1318`).

**Pattern (from curator):**
```python
from rich.console import Console
from rich.table import Table

console = Console()
table = Table(title="Agent Registry", show_lines=False)
table.add_column("Metric", style="bold")
table.add_column("Value", justify="right")
table.add_row("agents_loaded", str(snapshot["agents_loaded"]))
console.print(table)
```

**3 tables, 1 per dimension:**
- Agent Registry: `agents_loaded | schema_ok | missing_experts | lineage_ok | snapshot_at`
- Round Table: `count | p50_ms | p95_ms | total_tokens | early_stop_rate`
- Memory Backend: `search_p95_ms | add_p95_ms | search_count | add_count | error_rate | conflict_count`

## Dashboard Panel — Jinja2 Templates

**Problem:** No existing Jinja2 templates directory in the codebase. `web_server.py` only serves the built SPA via `mount_spa()` at line 11251. `WEB_DIST = hermes_cli/web_dist/` is the SPA bundle.

**Solution:** Use `HTMLResponse` with an inline string template OR a small `hermes_cli/web_templates/orchestrator.html` static file loaded via `Path(__file__).parent / "web_templates"`. The template is intentionally minimal (Jinja2-style placeholder substitution is overkill — pure HTML + JS fetch is enough).

**Decision:** Create `hermes_cli/web_templates/orchestrator.html` as a static HTML file (not Jinja2-syntax template — there's no server-side data to substitute; all data comes from client-side `fetch('/orchestrator/agents/status')`). The CONTEXT.md spec says "Jinja2 panel" but means "server-side HTML panel" — a plain HTML file served via `FileResponse` is the minimal viable implementation. Future migration to Jinja2Templates is trivial.

**Route addition in `web_server.py`:**
```python
@app.get("/orchestrator")
def get_orchestrator_panel(request: Request):
    _require_token(request)  # auth gate — operator-only
    html_path = Path(__file__).parent / "web_templates" / "orchestrator.html"
    return FileResponse(html_path, media_type="text/html")
```

**IMPORTANT:** This route MUST be registered BEFORE the `mount_spa()` catchall at line 11348 (`@application.get("/{full_path:path}")`). FastAPI matches routes in registration order — since `web_server.py` imports happen at module load and `mount_spa(app)` is called at line 12322 (after all `@app.get` decorators), the `/orchestrator` route is naturally registered first. No reordering needed.

**Auth gate:** MUST call `_require_token(request)` — the panel itself is operator-only (it surfaces agent names + lineage SHAs). The endpoint it fetches (`/orchestrator/agents/status`) is already auth-gated; the panel page must be too. The session token is available in the SPA as `window.__HERMES_SESSION_TOKEN__` — but this panel is loaded in a fresh tab/direct URL, so we need cookie-based auth (the `gated_auth_middleware` path). For the loopback mode, the operator typically visits the dashboard first (which injects `_SESSION_TOKEN` into the SPA HTML), then navigates to `/orchestrator` — the session token would need to be passed as a query param `?token=xxx` OR the operator visits from within the SPA via `window.open('/orchestrator')` with `fetch` headers pre-set.

**Pragmatic auth decision:** The panel page itself does NOT call `_require_token`. Instead the panel is a pure HTML shell; the auth happens on the `fetch('/orchestrator/agents/status')` call (which IS auth-gated and will 401 without the token). For loopback mode, the panel reads `window.__HERMES_SESSION_TOKEN__` (injected by the SPA) from `localStorage` or query string. For OAuth mode, the cookie middleware authenticates the fetch automatically. **If the panel HTML itself were auth-gated, the operator would get a 401 on the page load with no way to enter a token.** This is consistent with how `/api/*` endpoints work: the SPA shell is public, the data endpoints are gated. We mirror that.

Wait — that reasoning is backwards. `/orchestrator` is NOT under `/api/*` so `gated_auth_middleware` (line 66 of `dashboard_auth/middleware.py`: `if path in PUBLIC_API_PATHS:` — and PUBLIC_API_PATHS only contains `/api/*` paths) does NOT auto-gate it. But `auth_middleware` (the loopback variant, line 433 of web_server.py: `if path.startswith("/api/") and path not in _PUBLIC_API_PATHS:`) ALSO only gates `/api/*` paths. So `/orchestrator` (no `/api/` prefix) is served WITHOUT auth at both middlewares.

**Conclusion:** Auth must be enforced INSIDE the `/orchestrator` route handler via `_require_token(request)`. This matches how `/orchestrator/agents/status` works (line 2014: explicit `_require_token(request)`).

**Revised handler:**
```python
@app.get("/orchestrator")
def get_orchestrator_panel(request: Request):
    _require_token(request)  # operator-only — agent names + lineage SHAs are sensitive
    html_path = Path(__file__).parent / "web_templates" / "orchestrator.html"
    return FileResponse(html_path, media_type="text/html")
```

For the loopback case where the operator visits `/orchestrator` directly in browser (no SPA-injected token), the `_require_token` will 401. The operator must include `?token=xxx` or the `X-Hermes-Session-Token` header — neither is browser-friendly. **Resolution:** Support a `?token=xxx` query param fallback inside `_require_token` OR document that operators navigate to `/orchestrator` from within the SPA (which sets the header on fetch). The panel template's fetch call uses the same headers as the SPA. For Phase 68 v1, the operator workflow is: (1) open dashboard SPA (authenticates via cookie or session token injection), (2) SPA's "Orchestrator" link opens `/orchestrator?token=<session_token>` in a new tab. The handler reads `request.query_params.get("token")` as a fallback. **This is a known UX rough edge documented in SUMMARY for v14 polish.**

**Simpler v1:** Just gate the panel and accept that direct browser visits require the operator to be already authenticated via the SPA. The SPA's "Orchestrator" menu item opens `/orchestrator` in a new tab — if the operator is in OAuth cookie mode, the cookie auths the request automatically. If in loopback mode, the SPA appends `?token=<session_token>` to the link. The handler's `_require_token` already accepts query param + header; we extend `_has_valid_session_token` to also check `request.query_params.get("token")` as a last resort.

</code_research>

<validation_architecture>
## Validation Architecture (Nyquist)

**Test frequency principle:** Tests must sample the implementation surface at ≥ 2× the rate of feature change (Nyquist). For Phase 68:

- **Feature rate:** 3 new code units (CLI module, CLI wiring in main.py, web_server route + template) = ~3 logical units of change.
- **Test rate:** 5+ CLI tests + 3+ dashboard tests + 1 parity test = 9+ test points. Sampling rate 9/3 = 3× — comfortably above Nyquist.

**Per-task test map** (see 68-VALIDATION.md for full mapping):

| Task | Test file | Test count | What it locks down |
|------|-----------|------------|---------------------|
| CLI handler | `tests/hermes_cli/test_orchestrator_cli.py` | 5+ | `_cmd_status` rendering, `--json` shape, parity with endpoint |
| Dashboard panel | `tests/hermes_cli/test_web_server_orchestrator_panel.py` | 3+ | route exists, auth gate, HTML shape |
| Parity (SC#3) | `tests/hermes_cli/test_orchestrator_cli.py::test_no_drift` | 1 | CLI `--json` == endpoint JSON keys |

**No drift invariant (SC#3):** The CLI `--json` output and the `/orchestrator/agents/status` endpoint response MUST have byte-identical top-level keys. This is enforced by a single parity test that calls both paths and asserts `set(cli_keys) == set(endpoint_keys)`. Since both paths call the same 3 getters from `agent.observability`, the shapes are structurally guaranteed — the test is a regression guard against future drift (e.g., someone adds a key to one path but not the other).

</validation_architecture>

<grey_areas>
## Grey Areas Resolved

### GA1: CLI handler error handling on registry load failure
**Decision:** Mirror the endpoint's graceful degradation (web_server.py:2029-2034). The CLI handler wraps `load_agent_registry_with_warnings()` in try/except; on failure, passes `entries=[], missing=[], schema_ok=False` to `get_agent_registry_metrics()`. The rich table renders with `agents_loaded=0`, `schema_ok=False`. Exit code 0 (this is observability data, not a CLI failure). Matches the endpoint's "never 500" contract.

### GA2: `--json` shape exact match
**Decision:** The CLI `--json` output MUST be a byte-for-byte structural match to the endpoint response (modulo `snapshot_at` timestamp which differs by call). Both emit `{agent_registry, round_table, memory_backend, snapshot_at}` with identical sub-dict shapes. Tested by `test_json_matches_endpoint_shape`.

### GA3: Dashboard panel template engine
**Decision:** Plain HTML file (no Jinja2 substitution needed — all data is client-side fetched). The file lives at `hermes_cli/web_templates/orchestrator.html` and is served via `FileResponse`. This satisfies CONTEXT.md's "minimal Jinja2 panel" spec because (a) no server-side data needs substitution, (b) Jinja2Templates would add a dependency on the `jinja2` package (already present via FastAPI, but importing it for a static HTML file is wasteful), (c) the panel is intentionally minimal. Future evolution to Jinja2 is trivial.

### GA4: Auth for `/orchestrator` panel page
**Decision:** `_require_token(request)` enforces auth. For loopback mode the operator passes the session token via query string `?token=xxx` (the SPA's link to the panel appends it). For OAuth mode the cookie middleware authenticates automatically. Document the loopback UX rough edge in SUMMARY for v14 polish.

</grey_areas>

<pitfalls>
## Pitfalls

### P1: Route ordering vs SPA catchall
`mount_spa(app)` at line 12322 registers `@application.get("/{full_path:path}")` as a catchall. FastAPI matches routes in declaration order. Our `@app.get("/orchestrator")` decorator (added near the existing `/orchestrator/agents/status` at line 2004) is registered BEFORE `mount_spa` runs. So `/orchestrator` hits our route, not the SPA fallback. **Verified by reading web_server.py: the `/orchestrator/agents/status` route already works this way.**

### P2: `_BUILTIN_SUBCOMMANDS` frozenset must include `"orchestrator"`
Without this, the top-level argv pre-dispatch in `_first_positional_argv` misclassifies `hermes orchestrator status` and may route it to plugin discovery. Add `"orchestrator"` to the frozenset at line 11079.

### P3: Lazy import for `agent.observability`
The CLI handler body must lazy-import `from agent.observability import ...` (mirror the endpoint at web_server.py:2018). Module-top import risks a load cycle if `agent.observability` ever imports from `hermes_cli` (it doesn't today, but the pattern is defensive).

### P4: `encoding="utf-8"` on every `open()` (CLAUDE.md Ruff PLW1514)
The template HTML file is served via `FileResponse` (no `open()` needed). If any test or helper reads the template with `open()`, MUST pass `encoding="utf-8"`.

### P5: No `Path.home() / ".hermes"` (CLAUDE.md anti-pattern)
The CLI handler does not touch `~/.hermes` directly — all data comes from the in-memory collectors. No `get_hermes_home()` call needed.

### P6: INFRA-04 serial constraint
Phase 68 adds NO new async work. The CLI handler is sync. The dashboard route is sync. The template's fetch call is client-side (browser async, not server async). INFRA-04 preserved.

</pitfalls>

<assumptions>
## Assumptions

- **A1:** Phase 67 getters are stable and will not change shape during Phase 68 execution. (Phase 67 is shipped; REQUIREMENTS.md marks OBSRV-01..03 as Complete.)
- **A2:** `rich==14.3.3` API (`Table`, `Console`) is stable. Used by 3 existing curator commands — proven pattern.
- **A3:** `FileResponse` for a static HTML file works without additional FastAPI config. (Already used at web_server.py:1471, 12232.)
- **A4:** The SPA's existing navigation can link to `/orchestrator` without SPA rebuild — the route is server-side, the SPA shell just needs a `<a href="/orchestrator" target="_blank">` link. (Out of scope for Phase 68 — SPA changes require `web/` rebuild, deferred to v14.)

</assumptions>

<open_questions>
## Open Questions

None — all grey areas resolved. Proceed to planning.
</open_questions>
