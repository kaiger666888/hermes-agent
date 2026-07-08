# Phase 68: OBSERVABILITY-PRESENTATION - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart-discuss — CLI + minimal Jinja2 panel, both consuming Phase 67 endpoint)

<domain>
## Phase Boundary

Two presentation surfaces consuming the SAME metrics source (Phase 67 `/orchestrator/agents/status` endpoint + `agent.observability` collectors):

1. **CLI:** `hermes orchestrator status` — Rich tables showing 3 dimensions; `--json` flag for script consumption
2. **Dashboard:** Minimal Jinja2 panel at `/orchestrator` URL on existing `hermes dashboard` FastAPI server — 3 panels with live data

**In scope:**
- CLI subcommand under `hermes orchestrator` (new top-level command group OR subcommand of `hermes status`)
- Rich tables via existing `rich==14.3.3` dependency (already used throughout CLI)
- Jinja2 template at `hermes_cli/web_templates/orchestrator.html` (or similar)
- Single source of truth: BOTH surfaces fetch from `/orchestrator/agents/status` (CLI via internal Python call to `agent.observability.get_*()`; dashboard via HTTP fetch from same endpoint OR direct collector call)

**Strictly out of scope:**
- New frontend framework (React/Vue/etc.) — Jinja2 + minimal JS only
- Real-time WebSocket push — initial page load fetches fresh data; refresh button or auto-poll every N seconds (operator UX detail)
- Authentication for dashboard panel — inherits existing `hermes dashboard` auth
- Historical metrics / trend graphs — Phase 67 emits current snapshot only; persistence/trends are v14+
- Alerts / SLO thresholds — v14+

</domain>

<decisions>
## Implementation Decisions

### Locked-from-prior-phases

- **Metrics source:** `agent.observability.get_agent_registry_metrics()` + `get_round_table_metrics()` + `get_memory_backend_metrics()` (Phase 67 — single source of truth)
- **HTTP endpoint:** `/orchestrator/agents/status` (Phase 67 — dashboard consumes via HTTP; CLI calls collectors in-process)
- **Rich tables:** `rich==14.3.3` (existing) — `rich.table.Table` for 3-dimension display
- **FastAPI app:** `hermes_cli/web_server.py:190` (existing)
- **Templates:** existing `hermes_cli/web_dist/` or `hermes_cli/web_templates/` directory (verify location during research)
- **CLI convention:** `hermes_cli/main.py:11958+` subparser pattern; new `orchestrator` group OR `hermes status` subcommand
- **No new framework:** PROJECT.md constraint (no React/Vue); Jinja2 + vanilla JS only

### Claude's Discretion

**G1: CLI command shape**
- **Option A (recommended):** NEW top-level group `hermes orchestrator status` — explicit namespace, future-proofs for `hermes orchestrator inspect <agent>`, `hermes orchestrator history`, etc.
- **Option B:** Subcommand of `hermes status` — overloaded with existing status
- Recommendation: A — matches SC#1 literal text "hermes orchestrator status"; creates clean namespace for future operators.

**G2: Dashboard panel routing**
- **Option A (recommended):** NEW route `/orchestrator` on FastAPI app — serves Jinja2 template; template fetches `/orchestrator/agents/status` via JavaScript fetch() on page load
- **Option B:** Inline HTML response at `/orchestrator/agents/status` (no separate template) — return HTML when `Accept: text/html`, JSON otherwise
- Recommendation: A — separation of data API from presentation; template is replaceable without touching endpoint.

**G3: Data parity mechanism (SC#3 — no drift)**
- **Option A (recommended):** CLI imports `agent.observability.get_*()` directly (in-process); dashboard HTTP fetches `/orchestrator/agents/status` which ALSO calls same getters. Both paths share the getter implementation.
- **Option B:** CLI HTTPs the endpoint too (`requests.get('/orchestrator/agents/status')`) — but requires dashboard running, bad UX
- Recommendation: A — CLI doesn't require server running; dashboard verifies HTTP path. Both consume same getter code → zero drift.

**G4: Refresh mechanism for dashboard**
- **Option A (recommended):** Manual refresh button + `<meta http-equiv="refresh" content="30">` (auto-refresh every 30s) — minimal JS
- **Option B:** WebSocket push (real-time) — too complex for v13.0
- Recommendation: A — matches "minimal Jinja2 panel" spec.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- **`agent.observability`** package (Phase 67) — 3 collectors + MetricsBuffer
- **`hermes_cli/web_server.py`** — FastAPI app + Jinja2 templates dir (verify path)
- **`hermes_cli/main.py`** — subparser registration pattern
- **`rich.table.Table`, `rich.console.Console`** — already used in `hermes curator stats` (v6.0 P33 OBS-01 pattern)

### Established Patterns

- **CLI subparser:** `subparsers.add_parser("name", ...); p.set_defaults(func=_cmd_xxx)` (mirror `hermes_cli/curator.py:1238+`)
- **Rich table render:** `console.print(Table(...))` pattern from existing CLI commands
- **Jinja2 template render:** `templates.TemplateResponse("name.html", {"request": request, ...})` (FastAPI standard)
- **Lazy import** for `agent.observability` inside CLI handler body (avoid module-load cycle)

### Integration Points

- **CLI handler `_cmd_orchestrator_status`:** calls `get_agent_registry_metrics()`, `get_round_table_metrics()`, `get_memory_backend_metrics()`, renders 3 rich tables OR returns JSON
- **Dashboard route `/orchestrator`:** serves Jinja2 template; template's JS calls `/orchestrator/agents/status` on load + every 30s
- **`--json` flag:** outputs the SAME shape as `/orchestrator/agents/status` endpoint response — byte-identical semantics

</code_context>

<specifics>
## Specific Ideas

- CLI rich tables: 1 table per dimension. Columns:
  - Agent Registry: `agents_loaded | schema_ok | missing_experts | lineage_ok | last_updated`
  - Round Table: `rounds_count | p50_ms | p95_ms | tokens_total | early_stop_rate`
  - Memory Backend: `ops_count | p95_read_ms | p95_write_ms | conflict_rate | error_rate`
- Dashboard template: simple HTML with 3 cards, each rendering a table. Use `<script>fetch('/orchestrator/agents/status').then(r => r.json()).then(data => { ... })</script>` to populate.
- Add a `Refresh` button + auto-refresh meta tag.

</specifics>

<deferred>
## Deferred Ideas

- Historical metrics / time-series graphs — v14+
- WebSocket real-time push — v14+
- Alert thresholds / SLO visualization — v14+
- Per-agent drill-down view — v14+
- Prometheus exporter — v14+
- Multi-instance aggregation — v14+

</deferred>
