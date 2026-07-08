# Phase 67: OBSERVABILITY-BACKEND - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart-discuss — 3 collectors + 3 integration points, well-defined infra)

<domain>
## Phase Boundary

3 metrics collectors + wired into existing runtime modules + 1 new FastAPI endpoint on `hermes dashboard` server. Pure observability — read-only metrics emission, no new state mutation paths.

**In scope:**
1. **Agent registry health collector** (OBSRV-01) — wraps `load_agent_registry_with_warnings()` (Phase 63 sibling) and exposes JSON at `/orchestrator/agents/status` on `hermes_cli/web_server.py` FastAPI app
2. **Round table metrics collector** (OBSRV-02) — wired into `agent/round_table_executor.py`; emits p50/p95 latency, token cost, state transitions, serial-lock wait time, early-stop trigger rate per round table
3. **Memory backend metrics collector** (OBSRV-03) — wired into mem0 backend adapter (`plugins/memory/mem0/`); emits p95 read/write, conflict arbitration rate, compaction trigger rate, error rate

**Strictly out of scope:**
- CLI surface (`hermes orchestrator status` rich tables — Phase 68)
- Dashboard web view rendering (Phase 68 — Jinja2 panel consuming `/orchestrator/agents/status`)
- Prometheus/Grafana integration (v14+)
- Alerts / thresholds / SLO breaching (v14+ — Phase 67 emits raw metrics only)

</domain>

<decisions>
## Implementation Decisions

### Locked-from-prior-phases

- **FastAPI app:** `hermes_cli/web_server.py:190` — `app = FastAPI(title="Hermes Agent", ...)`. New endpoint registered here via `@app.get("/orchestrator/agents/status")`.
- **Registry source of truth:** `agent.registry_loader.load_agent_registry_with_warnings()` (Phase 63 sibling) returns `(entries, warnings)` — collector consumes this, does NOT re-implement.
- **Round table executor:** `agent/round_table_executor.py` (existing v11.0) — collector wraps turn execution, captures timing
- **mem0 backend:** `plugins/memory/mem0/` adapter (v12.0 Phase 60) — collector wraps read/write/conflict operations
- **Endpoint path:** `/orchestrator/agents/status` (SC#1 literal) — `hermes_cli/web_server.py` adds `@app.get` decorator
- **No new dependencies:** FastAPI already in pyproject.toml `[web]` extra; stdlib `statistics`, `time`, `dataclasses` sufficient for collectors
- **INFRA-04 serial constraint:** round table metrics emission MUST be sync inside the executor's serial lock — no async concurrency introduced

### Claude's Discretion

**G1: Metrics storage backend**
- **Option A (recommended):** In-memory ring buffer per collector (last 100 entries per metric); query endpoint reads current state. Zero persistence overhead, fast reads.
- **Option B:** SQLite at `~/.hermes/skills/.observability/metrics.db` — persistent, queryable, but adds I/O latency
- **Option C:** jsonl append-only log at `~/.hermes/logs/metrics.jsonl` — simple, grep-friendly, but no aggregation without parsing
- Recommendation: A — operators want fresh data; Phase 68 CLI reads on-demand. Persistence is Phase 68+ concern (or v14 Prometheus).

**G2: Metrics emission pattern**
- **Option A (recommended):** Pull — collectors store metrics in module-level ring buffer; endpoint computes aggregates (p50/p95) on demand
- **Option B:** Push — collectors `logger.info(structured=True)` metrics; endpoint scrapes log
- Recommendation: A — pull is simpler, deterministic, no log-parsing brittleness

**G3: p50/p95 computation window**
- **Option A (recommended):** Last 100 round table executions (or memory ops) in ring buffer
- **Option B:** Time-based window (last hour)
- Recommendation: A — count-based is deterministic; matches "recent workload" semantics better than wall-clock for low-frequency ops

**G4: Round table metrics granularity**
- **Option A (recommended):** Per-round-table summary (1 metrics entry per round_id) — turn-level latency aggregated into round p50/p95
- **Option B:** Per-turn granularity (1 metrics entry per turn) — more data, larger ring buffer needed
- Recommendation: A — keeps ring buffer small; turn-level data preserved in existing `~/.hermes/agents/.runtime/<project>/round_tables/<round_id>.json` state file

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- **`hermes_cli/web_server.py:190`** — FastAPI app instance (`app = FastAPI(...)`)
- **`hermes_cli/web_server.py:1699`** — `@app.get("/api/status")` existing endpoint pattern (reference for new endpoint)
- **`hermes_cli/web_server.py:1913`** — `@app.get("/api/system/stats")` existing stats endpoint (closest analog)
- **`agent/registry_loader.py`** — `load_agent_registry_with_warnings()` (Phase 63), `REQUIRED_DAG_EXPERTS` (Phase 63), `_check_required_experts` (Phase 63)
- **`agent/round_table_executor.py`** — `execute_turn` or equivalent function; serial lock `acquire_round_or_reject`
- **`agent/round_table_state.py`** — state file format for round table
- **`plugins/memory/mem0/`** — adapter directory (read for adapter entry points)

### Established Patterns

- **FastAPI route pattern:** `@app.get("/path") def handler(): return {...}` (sync or async)
- **Lazy %-logging** in collectors
- **`dataclasses.dataclass`** for structured metrics entries
- **`time.perf_counter()`** for sub-millisecond latency
- **`statistics.quantiles(data, n=100)`** for p50/p95 computation
- **Module-level singleton** for ring buffer (`_METRICS_BUFFER: deque[MetricsEntry]`)

### Integration Points

- **`/orchestrator/agents/status` endpoint:** JSON response with `{agents_loaded, schema_validation_status, missing_experts, lineage_integrity}`
- **Round table executor hook:** `with _round_table_metrics_capture(round_id): ...` context manager wrapping the existing turn execution
- **mem0 adapter hook:** `with _memory_op_metrics_capture(op_type): ...` wrapping existing read/write calls
- **Phase 68 consumer:** CLI `hermes orchestrator status` will fetch `/orchestrator/agents/status` + read in-process metrics buffers

</code_context>

<specifics>
## Specific Ideas

- Each collector lives in a new module: `agent/observability/agent_registry_metrics.py`, `agent/observability/round_table_metrics.py`, `agent/observability/memory_backend_metrics.py`
- Shared ring buffer primitive: `agent/observability/_ring_buffer.py` with `MetricsBuffer(max_entries=100)` class
- All 3 collectors register their buffers in a single registry: `agent/observability/__init__.py` exports `get_agent_registry_metrics()`, `get_round_table_metrics()`, `get_memory_backend_metrics()` returning the current buffer snapshot
- Endpoint `/orchestrator/agents/status` calls `get_agent_registry_metrics()` + does live `load_agent_registry_with_warnings()` call for fresh data
- All metrics timestamps in ISO-8601 UTC

</specifics>

<deferred>
## Deferred Ideas

- **CLI `hermes orchestrator status`** — Phase 68 (OBSRV-04)
- **Dashboard Jinja2 panel** — Phase 68 (OBSRV-05)
- **Prometheus exporter** — v14+
- **Alerts / SLO thresholds** — v14+
- **Time-windowed metrics (last hour)** — v14+ (Phase 67 uses count-based window per G3)
- **Persistence (SQLite metrics store)** — v14+ (Phase 67 uses in-memory per G1)
- **Multi-instance metrics aggregation** — v14+ (Phase 67 single-process only)

</deferred>
