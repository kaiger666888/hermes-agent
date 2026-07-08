# Phase 67: OBSERVABILITY-BACKEND - Research

**Researched:** 2026-07-08
**Domain:** Python observability (in-process metrics collection) + FastAPI endpoint wiring
**Confidence:** HIGH — all integration points verified by reading actual source; stdlib-only stack (no new deps)

## Summary

Phase 67 ships 3 read-only metrics collectors + 1 FastAPI endpoint on the existing `hermes dashboard` server. The scope is narrow and the integration points are all already-shipped Phase 52/53/58/60/63 code: `load_agent_registry_with_warnings()` for OBSRV-01, `get_agent_opinion` + `submit_round_table_result` MCP functions for OBSRV-02, and `plugins.memory.mem0.backend` adapter for OBSRV-03. No new external dependencies are required — the entire implementation uses `collections.deque(maxlen=...)`, `time.perf_counter()`, `statistics`, and `dataclasses` from the stdlib, plus FastAPI which is already in `pyproject.toml [web]`.

The recommended architecture is one new package `agent/observability/` with 5 files: a shared ring-buffer primitive, 3 collector modules, and an `__init__.py` registry. All three collectors use module-level singletons (the same pattern `agent/i18n._catalog_cache`, `agent/round_table_executor._ROUND_LOCKS`, and `providers/__init__._REGISTRY` already use) so the FastAPI endpoint can call `get_agent_registry_metrics()` and read the current snapshot synchronously. The metrics are pulled (per CONTEXT.md G2 lock) — collectors populate the buffer on each operation, the endpoint computes p50/p95 on demand via `statistics.quantiles`.

**Primary recommendation:** Build the `_ring_buffer.py` primitive first (Wave 0), then the 3 collectors in parallel, then wire the FastAPI endpoint last. The endpoint depends on all 3 collector snapshots being available; the collectors depend only on the shared primitive.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **FastAPI app:** `hermes_cli/web_server.py:190` — `app = FastAPI(title="Hermes Agent", ...)`. New endpoint registered here via `@app.get("/orchestrator/agents/status")`.
- **Registry source of truth:** `agent.registry_loader.load_agent_registry_with_warnings()` (Phase 63 sibling) returns `(entries, warnings)` — collector consumes this, does NOT re-implement.
- **Round table executor:** `agent/round_table_executor.py` (existing v11.0) — collector wraps turn execution, captures timing
- **mem0 backend:** `plugins/memory/mem0/` adapter (v12.0 Phase 60) — collector wraps read/write/conflict operations
- **Endpoint path:** `/orchestrator/agents/status` (SC#1 literal)
- **No new dependencies:** stdlib + FastAPI (already present)
- **INFRA-04 serial constraint:** round table metrics emission MUST be sync inside the executor's serial lock — no async concurrency introduced
- **G1: In-memory ring buffer** (Option A) — last 100 entries per metric; zero persistence
- **G2: Pull model** (Option A) — collectors store; endpoint computes aggregates on demand
- **G3: Count-based window** (Option A) — last 100 ops (NOT time-based)
- **G4: Per-round-table summary granularity** (Option A) — 1 metrics entry per round_id

### Claude's Discretion

(All 4 grey areas resolved by the Locked Decisions above — G1/G2/G3/G4 are all locked Option A.)

### Deferred Ideas (OUT OF SCOPE)

- CLI `hermes orchestrator status` — Phase 68 (OBSRV-04)
- Dashboard Jinja2 panel — Phase 68 (OBSRV-05)
- Prometheus exporter — v14+
- Alerts / SLO thresholds — v14+
- Time-windowed metrics (last hour) — v14+ (Phase 67 uses count-based window per G3)
- Persistence (SQLite metrics store) — v14+
- Multi-instance metrics aggregation — v14+
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OBSRV-01 | Agent registry health collector — 21 agents loaded · schema validation status · missing-expert 告警 · lineage integrity check; wire into `/orchestrator/agents/status` | `agent/registry_loader.load_agent_registry_with_warnings()` returns `(entries, missing_expert_warnings)` directly (`registry_loader.py:415-439`). Endpoint calls it live on each request (no caching — caller already caches internally via `_REGISTRY_CACHE`). Lineage integrity = verify each entry has `lineage` field populated (source SHA + transform rule ID). |
| OBSRV-02 | Round table metrics collector — latency p50/p95 · token cost · state transitions · serial-lock wait time · early-stop trigger rate | Instrument the 2 MCP functions in `mcp_serve.py`: `get_agent_opinion` (`mcp_serve.py:688-932`) and `submit_round_table_result` (`mcp_serve.py:936-1010`). See "Instrumentation Points" below for exact line anchors. |
| OBSRV-03 | Memory backend metrics collector — mem0 p95 read/write · conflict arbitration rate · compaction trigger rate · error rate | Instrument `_BackendAdapter.search` / `_BackendAdapter.add` (`plugins/memory/mem0/__init__.py:416-496`) and `agent.memory_arbitration.append_conflict_record` (`memory_arbitration.py:359-381`). |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Agent registry health snapshot | API / Backend | — | FastAPI endpoint calls `registry_loader` in-process; reads filesystem under `~/.hermes/agents/`. Pure backend, no client involvement. |
| Round table turn latency capture | API / Backend | Database / Storage | Timing wrap lives inside `mcp_serve.get_agent_opinion` (FastMCP server, same process as agent runtime). State file under `~/.hermes/agents/.runtime/` is secondary — metrics are NOT persisted there, only operational state. |
| Memory backend op latency capture | API / Backend | — | Wrap `_BackendAdapter.search/add` (sync HTTP calls to Mem0 Platform via SDK). Process-local. |
| Metrics aggregation + JSON response | API / Backend | — | FastAPI handler in `web_server.py` calls 3 collector getters + computes p50/p95 via stdlib `statistics`. |
| Endpoint HTTP transport | Frontend Server (SSR) | — | FastAPI/uvicorn — existing `hermes dashboard` server. |

No capability touches the Browser/Client or CDN tier. Phase 67 is pure backend.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `collections.deque` | stdlib (3.11+) | Bounded ring buffer (`maxlen=100`) — auto-evicts oldest on append | Idiomatic Python for fixed-size buffers; `deque(maxlen=N)` is thread-safe for append/popleft [CITED: docs.python.org/3/library/collections.html#deque] |
| `time.perf_counter` | stdlib (3.11+) | Sub-millisecond monotonic latency timing | Official recommendation over `time.time()` for durations — not subject to NTP jumps [CITED: docs.python.org/3/library/time.html#time.perf_counter] |
| `statistics.quantiles` | stdlib (3.11+) | p50/p95 computation from samples | Built-in, no numpy dependency. **Pitfall:** raises `StatisticsError` on `<2` data points — see Pitfalls. [VERIFIED: local runtime `python3 -c "import statistics; statistics.quantiles([], n=100)"` → `StatisticsError: must have at least two data points`] |
| `dataclasses` | stdlib (3.11+) | Structured metrics entries (`@dataclass(slots=True)`) | Codebase convention — see `agent/error_classifier.ClassifiedError` |
| `fastapi` | `==0.133.1` (`[web]` extra) | HTTP endpoint `/orchestrator/agents/status` | Already in `pyproject.toml`; same app instance as existing `/api/status` |
| `datetime` (UTC ISO-8601) | stdlib | Timestamps on every metrics entry | Mirrors `agent/round_table_state._now_iso()` pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `threading.Lock` | stdlib | Serialize ring-buffer mutations from concurrent asyncio tasks | One lock per buffer; held only for `append`/`snapshot` (~microseconds) |
| `contextlib.contextmanager` | stdlib | `with _round_table_capture(round_id): ...` instrumentation ergonomics | Wraps the existing turn-execution code path without restructuring it |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `collections.deque(maxlen=100)` | `numpy.array` ring | numpy not in core deps; pulling it in for a 100-element buffer is overkill |
| `statistics.quantiles` | Manual `sorted()[int(len*0.5)]` | Manual index is faster but loses the well-tested interpolation edge cases; `quantiles` is correct and the buffer is tiny (100 elems) |
| Module-level singleton buffer | Dependency injection (pass buffer object through every function) | Codebase pattern is module-level singletons (see `_REGISTRY` / `_ROUND_LOCKS`); DI would force a refactor of the entire call chain for no benefit |

**Installation:** No install step. All dependencies are stdlib or already pinned in `pyproject.toml`.

**Version verification:**
```bash
python3 -c "import fastapi; print(fastapi.__version__)"  # 0.133.1 confirmed in pyproject.toml [web] extra
python3 -c "import statistics, collections, dataclasses, time; print('stdlib OK')"
```

## Package Legitimacy Audit

> No external packages are installed in this phase. The entire stack is stdlib + `fastapi` (already pinned in `pyproject.toml`). Slopecheck gate N/A — no `pip install` / `npm install` commands introduced.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| (none — stdlib + existing fastapi only) | — | — | — | — | — | N/A |

## Architecture Patterns

### System Architecture Diagram

```text
                        ┌─────────────────────────────────────────┐
                        │   hermes dashboard FastAPI server        │
                        │   (hermes_cli/web_server.py:190 app)     │
                        │                                          │
   HTTP GET ───────────►│   @app.get("/orchestrator/agents/status")│
   /orchestrator/       │            │                             │
   agents/status        │            ▼                             │
                        │   get_agent_registry_metrics()           │
                        │   get_round_table_metrics()              │
                        │   get_memory_backend_metrics()           │
                        │            │                             │
                        │            ▼                             │
                        │   compute p50/p95 on demand              │
                        │   (statistics.quantiles)                 │
                        │            │                             │
                        │            ▼                             │
                        │   JSONResponse → operator                │
                        └─────────────────────────────────────────┘
                                    ▲   ▲   ▲
                                    │   │   │  (snapshot reads — pull model)
              ┌─────────────────────┘   │   └──────────────────────┐
              │                         │                          │
   ┌──────────┴──────────┐  ┌───────────┴──────────┐  ┌────────────┴───────────┐
   │  agent/observability │  │  agent/observability  │  │  agent/observability   │
   │  /agent_registry_    │  │  /round_table_        │  │  /memory_backend_      │
   │  metrics.py          │  │  metrics.py           │  │  metrics.py            │
   │                      │  │                       │  │                        │
   │  _BUFFER: deque      │  │  _BUFFER: deque       │  │  _BUFFER: deque        │
   │  (last 100 snapshots)│  │  (last 100 rounds)    │  │  (last 100 ops)        │
   └──────────┬───────────┘  └───────────┬───────────┘  └────────────┬───────────┘
              │                          │                           │
              │ live call on             │ context-manager wrap      │ context-manager wrap
              │ each HTTP request        │ inside MCP functions      │ inside _BackendAdapter
              ▼                          ▼                           ▼
   ┌─────────────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐
   │  registry_loader    │  │  mcp_serve.py            │  │  plugins/memory/mem0/    │
   │  .load_agent_       │  │  - get_agent_opinion()   │  │  - _BackendAdapter       │
   │  registry_with_     │  │    (line 688-932)        │  │    .search() .add()      │  │  warnings()         │  │  - submit_round_table_  │  │  agent/memory_arbitration│
   │                     │  │    result() (936-1010)   │  │  .append_conflict_record│
   └─────────────────────┘  └──────────────────────────┘  └──────────────────────────┘
```

Data flows UP from the runtime modules (where metrics are captured on each op) to the buffer (module-level singleton) to the endpoint (pulls on each HTTP GET). The buffer is the only mutable shared state; everything below it is read-only from the metrics system's perspective.

### Recommended Project Structure
```
agent/
├── observability/                  # NEW package (Phase 67)
│   ├── __init__.py                 # Registry: exports 3 getter functions
│   ├── _ring_buffer.py             # Shared MetricsBuffer(max_entries=100) primitive
│   ├── agent_registry_metrics.py   # OBSRV-01: snapshot_agent_registry()
│   ├── round_table_metrics.py      # OBSRV-02: _round_table_capture() ctx mgr + getter
│   └── memory_backend_metrics.py   # OBSRV-03: _memory_op_capture() ctx mgr + getter
├── registry_loader.py              # UNCHANGED (consumer)
├── round_table_executor.py         # UNCHANGED (consumer via mcp_serve wrap)
└── ...
hermes_cli/
└── web_server.py                   # MODIFIED: +1 endpoint near line 1913
mcp_serve.py                        # MODIFIED: +instrumentation in 2 functions
agent/memory_arbitration.py         # MODIFIED: +instrumentation in append_conflict_record
plugins/memory/mem0/__init__.py     # MODIFIED: +instrumentation in _BackendAdapter
tests/agent/observability/          # NEW test directory
├── __init__.py
├── test_ring_buffer.py
├── test_agent_registry_metrics.py
├── test_round_table_metrics.py
└── test_memory_backend_metrics.py
tests/hermes_cli/
└── test_web_server_orchestrator_status.py  # NEW integration test
```

### Pattern 1: Module-Level Singleton Ring Buffer
**What:** One `deque(maxlen=100)` per collector, guarded by a `threading.Lock`, exposed via module-level getter.
**When to use:** Always — this is the only storage pattern for Phase 67.
**Example:**
```python
# Source: codebase convention — mirrors agent/i18n._catalog_cache, agent/round_table_executor._ROUND_LOCKS
from __future__ import annotations
import threading
from collections import deque
from dataclasses import dataclass
from typing import Any

_LOCK = threading.Lock()
_BUFFER: deque["RoundTableMetricEntry"] = deque(maxlen=100)


@dataclass(slots=True)
class RoundTableMetricEntry:
    round_id: str
    started_at_iso: str
    completed_at_iso: str
    duration_ms: float
    token_cost: int
    serial_lock_wait_ms: float
    turn_count: int
    status: str  # "completed" | "aborted" | "error"


def record(entry: RoundTableMetricEntry) -> None:
    """Append one entry. Thread-safe (asyncio tasks from the FastMCP loop
    share the GIL but deque.append is atomic anyway — the lock protects
    against torn reads during snapshot)."""
    with _LOCK:
        _BUFFER.append(entry)


def snapshot() -> list[RoundTableMetricEntry]:
    """Return a point-in-time copy of the current buffer."""
    with _LOCK:
        return list(_BUFFER)
```

### Pattern 2: Context-Manager Instrumentation
**What:** `with _capture(round_id): ...` wraps existing code without restructuring it.
**When to use:** OBSRV-02 and OBSRV-03 — the instrumented functions are long and must keep their control flow.
**Example:**
```python
# Source: contextlib.contextmanager stdlib pattern
from contextlib import contextmanager
import time

@contextmanager
def _round_table_capture(round_id: str, *, phase: str = "turn"):
    """Wrap a round-table op (turn dispatch or submit). Records duration."""
    t0 = time.perf_counter()
    error: str | None = None
    try:
        yield
    except Exception as exc:
        error = type(exc).__name__
        raise
    finally:
        duration_ms = (time.perf_counter() - t0) * 1000.0
        # ... assemble entry, call round_table_metrics.record(entry)
```

### Pattern 3: On-Demand p50/p95 Computation
**What:** Endpoint computes percentiles fresh on each GET from the current buffer snapshot.
**When to use:** Always — G2 pull model.
**Example:**
```python
import statistics

def _percentiles(samples: list[float]) -> dict[str, float]:
    """Return {'p50': ..., 'p95': ...}. Empty/1-elem buffers return zeros."""
    if len(samples) < 2:
        # statistics.quantiles raises StatisticsError on < 2 data points
        # (verified: python3 -c "import statistics; statistics.quantiles([1.0], n=100)")
        if not samples:
            return {"p50": 0.0, "p95": 0.0, "count": 0}
        return {"p50": samples[0], "p95": samples[0], "count": 1}
    qs = statistics.quantiles(samples, n=100)
    return {"p50": qs[49], "p95": qs[94], "count": len(samples)}
```

### Anti-Patterns to Avoid
- **Asynchronous metrics push (background task flushing buffer to disk):** Violates G2 (pull model) and adds an asyncio task that could interfere with the INFRA-04 serial lock. Stay pull-only.
- **Wrapping the registry loader to cache its metrics result:** The loader already caches internally (`_REGISTRY_CACHE`); wrapping it again is redundant and risks staleness divergence. Call it live on each endpoint hit (cheap — cache hit path is microseconds).
- **Importing `agent.observability` from `web_server.py` at module top:** `web_server.py` already lazy-imports `agent.*` inside handlers (see line 1797 `from hermes_state import SessionDB` inside the handler body). Follow the same pattern to avoid import-cycle risk if observability ever needs to import from `hermes_cli`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Bounded buffer with auto-eviction | Custom list + index math + `if len > N: pop(0)` | `collections.deque(maxlen=N)` | `deque(maxlen=N)` evicts oldest automatically, is O(1) for append/popleft, thread-safe at the C level |
| Percentile computation | Manual `sorted_samples[int(len * 0.95)]` | `statistics.quantiles(data, n=100)` | Stdlib handles edge cases (interpolation, even/odd counts); manual index math is wrong on even-length lists |
| Atomic JSON file write for any persistence (NOT NEEDED in Phase 67) | (n/a — G1 is in-memory) | `utils.atomic_json_write` (already shipped) | Listed here only to prevent re-derivation; Phase 67 does NOT persist |
| Latency timing | `time.time()` deltas | `time.perf_counter()` | `time.time()` is wall-clock — subject to NTP adjustments that can produce negative durations; `perf_counter` is monotonic [CITED: docs.python.org/3/library/time.html#time.perf_counter] |
| HTTP response serialization | Manual `json.dumps` + `Response(content=..., media_type="application/json")` | Return a `dict` from the FastAPI handler | FastAPI auto-serializes dicts to JSON via its JSONResponse; matches existing `/api/status` pattern |

**Key insight:** Every piece of this phase is either stdlib or already-shipped code. The temptation to build a "metrics framework" should be resisted — 3 collectors + 1 endpoint is ~400 lines of Python total.

## Instrumentation Points (per collector)

### OBSRV-01: Agent Registry Metrics

**Consumer function:** `agent.registry_loader.load_agent_registry_with_warnings(*, force_reload=False) -> tuple[list[dict], list[str]]` (`registry_loader.py:415-439`)

**Capture strategy:** NO instrumentation of the loader itself. The endpoint calls `load_agent_registry_with_warnings(force_reload=False)` live on each HTTP request and assembles the metric entry from the returned tuple. Rationale: the loader is already cached (microseconds on cache hit); wrapping it would just duplicate the cache. The "metrics entry" here is a snapshot, not a time-series sample.

**Entry shape:**
```python
@dataclass(slots=True)
class AgentRegistryMetricEntry:
    snapshot_at_iso: str
    agents_loaded: int
    schema_validation_ok: bool   # True unless RegistryValidationError raised
    missing_experts: list[str]   # from the tuple's warnings list
    lineage_integrity_ok: bool   # True if every entry has non-empty lineage.source_sha + lineage.transform_rule_id
    agent_names: list[str]       # sorted, for operator scan
```

**Lineage integrity check (implementation hint):**
```python
def _check_lineage(entries: list[dict]) -> bool:
    """True iff every entry has lineage.source_sha256 and lineage.transform_rule_id."""
    for e in entries:
        lineage = e.get("lineage") or {}
        if not lineage.get("source_sha256") or not lineage.get("transform_rule_id"):
            return False
    return True
```

### OBSRV-02: Round Table Metrics

**Instrumentation targets (2 functions in `mcp_serve.py`):**

| Function | Lines | What to capture | Hook point |
|----------|-------|-----------------|------------|
| `get_agent_opinion` | `mcp_serve.py:688-932` | per-turn latency, token cost, serial-lock wait, status | Wrap the body from line 753 (`lock = await acquire_round_or_reject(round_id)`) through line 928 (outer `finally: release_round_lock`). Use `time.perf_counter()` at the boundary. |
| `submit_round_table_result` | `mcp_serve.py:936-1010` | per-round-table total cost, status transition, turn count, early-stop trigger | Wrap from line 996 (`_submit(...)`) through the result return. Read `result["tokensConsumed"]`, `result["costUsdEstimate"]`, `result["status"]`, `len(result.get("turns", []))`. |

**Per-turn capture (inside `get_agent_opinion`):**
- `t_lock_acquire = perf_counter()` BEFORE `await acquire_round_or_reject(round_id)` (line 753)
- `t_lock_acquired = perf_counter()` AFTER the await — `serial_lock_wait_ms = (t_lock_acquired - t_lock_acquire) * 1000`
- `t_dispatch_start = perf_counter()` BEFORE `call_llm(...)` (line 857)
- `t_dispatch_end = perf_counter()` AFTER the response — `dispatch_ms = (t_dispatch_end - t_dispatch_start) * 1000`
- Token cost: after the `call_llm` returns, read `agent.auxiliary_client.get_last_call_usage()["total_tokens"]` (confirmed at `auxiliary_client.py:5073`). **Pitfall:** this is a module-level mutable dict — read it immediately after `call_llm` returns, before any other coroutine runs.
- Status: `"ok"` from the happy-path return (line 912), or `"serial_violation"` if `lock is None` (line 754), or `"round_not_found"` / `"round_not_open"` / `"llm_malformed_response"` / `"append_turn_failed"` from the various error returns.

**Per-round-table capture (inside `submit_round_table_result`):**
- After `_submit(...)` succeeds, read from the returned `result` dict:
  - `tokensConsumed` (total round cost — already summed by `record_token_usage` across all turns)
  - `costUsdEstimate` (USD — already computed by `submit_round_table_result` via the GLM-5.2 formula)
  - `status` (`"completed"` on happy path, or the 409 conflict dict on re-submit)
  - `len(result.get("turns", []))` for turn count
- **G4 granularity:** emit ONE entry per `submit_round_table_result` call. Do NOT emit per-turn entries — turn-level data is already in the state file at `~/.hermes/agents/.runtime/{slug}/round_tables/{round_id}.json` (per CONTEXT.md G4 rationale).

**Entry shape:**
```python
@dataclass(slots=True)
class RoundTableMetricEntry:
    round_id: str
    snapshot_at_iso: str
    duration_ms: float              # submit_round_table_result total wall time
    token_cost: int                 # from result["tokensConsumed"]
    cost_usd: float                 # from result["costUsdEstimate"]
    turn_count: int                 # len(result["turns"])
    serial_lock_wait_ms_avg: float  # avg across turns in this round (best-effort)
    early_stop_triggered: bool      # any budget_exceeded event in result["events"]?
    status: str                     # "completed" | "aborted" | "conflict_409" | "error"
```

**INFRA-04 compliance:** All capture points are synchronous `perf_counter()` reads inside the already-serial async lock region. NO new `asyncio.create_task` or background dispatch. The `with _round_table_capture(...)` context manager is sync-only.

### OBSRV-03: Memory Backend Metrics

**Instrumentation targets (2 methods + 1 function):**

| Target | File:Line | What to capture |
|--------|-----------|-----------------|
| `_BackendAdapter.search` | `plugins/memory/mem0/__init__.py:416-458` | latency, hit_count, success/error |
| `_BackendAdapter.add` | `plugins/memory/mem0/__init__.py:460-496` | latency, success/error |
| `append_conflict_record` | `agent/memory_arbitration.py:359-381` | conflict arbitration rate (count of calls) |

**Compaction trigger rate:** No explicit "compaction" event exists in the current mem0 adapter (the Mem0 Platform handles compaction server-side). For Phase 67, report `compaction_triggers: 0` with a code comment noting "Mem0 Platform server-side compaction is not observable from the client; revisit in v14 if we move to self-hosted mem0." This is an honest empty-value rather than a fabricated metric.

**Entry shape:**
```python
@dataclass(slots=True)
class MemoryOpMetricEntry:
    op_type: str            # "search" | "add" | "conflict"
    started_at_iso: str
    duration_ms: float
    success: bool
    hit_count: int          # for search; 0 for add/conflict
    error_type: str | None  # exception class name if failed
```

**Wire pattern:** Add a `_memory_op_capture(op_type)` context manager inside `memory_backend_metrics.py`. Wrap `_BackendAdapter.search` and `_BackendAdapter.add` method bodies. For `append_conflict_record`, the wrap is at the call site in `memory_arbitration.py` (NOT inside the function itself — that function is a pure JSONL append and instrumenting it directly would double-count when called from test code).

## Runtime State Inventory

> Phase 67 introduces NO rename/refactor/migration. This section is included per protocol but is trivially empty.

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | None — collectors use in-memory deques only (per G1) | None |
| Live service config | None — no external service touched | None |
| OS-registered state | None | None |
| Secrets/env vars | None — `MEM0_API_KEY` is read by the existing adapter, not by the metrics layer | None |
| Build artifacts | None — pure Python, no compiled artifacts | None |

## Common Pitfalls

### Pitfall 1: `statistics.quantiles` on empty/small buffers
**What goes wrong:** Calling `statistics.quantiles([], n=100)` raises `statistics.StatisticsError: must have at least two data points`. Same for single-element lists.
**Why it happens:** The function needs at least 2 data points to interpolate between percentiles. A freshly-started dashboard with no round tables yet will have an empty buffer.
**How to avoid:** Wrap the quantile call in a length check; return `{p50: 0.0, p95: 0.0, count: 0}` for empty, `{p50: x, p95: x, count: 1}` for single-element. See Pattern 3 code example above.
**Warning signs:** `StatisticsError` traceback in `gateway.log` the first time an operator hits `/orchestrator/agents/status` before any round table has run.
**Verification status:** [VERIFIED: local runtime — `python3 -c "import statistics; statistics.quantiles([], n=100)"` → `StatisticsError`]

### Pitfall 2: Thread-safety of the ring buffer under asyncio
**What goes wrong:** Multiple asyncio tasks (from the FastMCP server) call `_BUFFER.append(entry)` concurrently. While `deque.append` is CPython-atomic, the pattern `snapshot = list(_BUFFER)` during a concurrent append can produce a torn read.
**Why it happens:** CPython's GIL makes `deque.append` atomic, but `list(deque)` iterates — if the GIL switches threads mid-iteration, the snapshot may be inconsistent.
**How to avoid:** Guard every buffer mutation AND every snapshot read with a `threading.Lock`. The lock is held for microseconds (deque ops are O(1)), so contention is negligible. **Important:** the lock must be a `threading.Lock`, NOT an `asyncio.Lock` — the buffer is accessed from both sync (`_BackendAdapter.search`) and async (`get_agent_opinion`) contexts, and `asyncio.Lock` cannot be used across the two.
**Warning signs:** Rare, irreproducible p95 spikes that don't match any real operation.

### Pitfall 3: `get_last_call_usage()` is a shared mutable global
**What goes wrong:** `agent.auxiliary_client.get_last_call_usage()` reads `_LAST_CALL_USAGE` (`auxiliary_client.py:5060-5125`), a module-level dict updated on every LLM call. If two coroutines dispatch LLM calls back-to-back, the second's `total_tokens` overwrites the first's before the first reads it.
**Why it happens:** The dict is not per-task — it's process-global.
**How to avoid:** In `get_agent_opinion`, read `get_last_call_usage()["total_tokens"]` IMMEDIATELY after `call_llm(...)` returns, before any `await` point. Since the round table is serialized by the per-roundId lock (INFRA-04), there is no concurrent LLM call within the same round — but defensive immediate-read is still correct.
**Warning signs:** Token costs that don't match the actual response length.

### Pitfall 4: FastAPI sync vs async route handler choice
**What goes wrong:** If the `/orchestrator/agents/status` handler is declared `async def`, calling `load_agent_registry_with_warnings()` (a sync function that does file I/O) inside it blocks the event loop.
**Why it happens:** FastAPI runs `async def` handlers directly on the event loop; sync I/O inside them blocks all other requests.
**How to avoid:** Either (a) declare the handler `def` (not `async def`) — FastAPI runs sync handlers in a threadpool — or (b) declare it `async def` and offload the loader call to `await loop.run_in_executor(None, load_agent_registry_with_warnings)`. **Recommendation:** Use plain `def` — it matches the existing `/api/curator` handler pattern (`web_server.py:2003` uses `async def` but its body is `await loop.run_in_executor` for the heavy work; simpler to just go sync). The handler does ~3 file reads + 3 buffer snapshots + percentile math — all sub-millisecond.
**Warning signs:** Dashboard UI latency when another operator hits `/orchestrator/agents/status` during heavy gateway traffic.

### Pitfall 5: Public-path auth gate
**What goes wrong:** Adding `/orchestrator/agents/status` to `PUBLIC_API_PATHS` (in `hermes_cli/dashboard_auth/public_paths.py`) would expose agent registry internals (names, lineage SHAs, missing-expert list) to unauthenticated callers — a recon risk.
**Why it happens:** Copy-pasting from `/api/status` which IS public.
**How to avoid:** Do NOT add `/orchestrator/agents/status` to `PUBLIC_API_PATHS`. The endpoint MUST go through the existing `_require_token(request)` gate (the auth middleware at `web_server.py:379` will enforce it automatically for any path not in the allowlist). This is the security-correct default.
**Warning signs:** The endpoint returns 200 without a session token — that means the auth gate is bypassed and there's a bug.
**Verification status:** [CITED: `hermes_cli/dashboard_auth/public_paths.py` docstring lines 22-29 — "every entry should be safe to expose to external uptime probes, the dashboard SPA before login, anyone who happens to curl the hostname"]

### Pitfall 6: Circular import via `web_server.py` → `agent.observability`
**What goes wrong:** `web_server.py` imports `agent.observability` at module top; `agent.observability` imports something that eventually imports `hermes_cli.*` → `ImportError: cannot import name`.
**Why it happens:** `hermes_cli/web_server.py` is a large module with many transitive dependencies.
**How to avoid:** Import `agent.observability` LAZILY inside the endpoint handler body (the same pattern `web_server.py` already uses for `hermes_state.SessionDB` at line 1797, `agent.curator` at line 2006, `gateway.config` at line 1743). The handler is the only consumer.
**Warning signs:** `ImportError` on `hermes dashboard` startup.

## Code Examples

### Existing FastAPI endpoint pattern (closest analog: `/api/system/stats`)
```python
# Source: hermes_cli/web_server.py:1913-1991 (VERIFIED — read directly)
@app.get("/api/system/stats")
async def get_system_stats():
    """Host + process system stats for the System page."""
    import platform as _platform
    info: Dict[str, Any] = { ... }
    try:
        import psutil
        # ... enrich
    except Exception:
        info["psutil"] = False
    return info  # FastAPI auto-serializes dict → JSONResponse
```

**Phase 67 endpoint follows this pattern:**
```python
# NEW — to be added near web_server.py:1913
@app.get("/orchestrator/agents/status")
def get_orchestrator_agents_status(request: Request):
    """Phase 67 OBSRV-01/02/03: operator observability endpoint.

    Read-only snapshot of agent registry health + round table metrics +
    memory backend metrics. Computed on-demand from in-memory ring buffers.
    """
    _require_token(request)  # Pitfall 5 — do NOT add to PUBLIC_API_PATHS

    # Lazy import to avoid any circular-import risk (Pitfall 6)
    from agent.observability import (
        get_agent_registry_metrics,
        get_round_table_metrics,
        get_memory_backend_metrics,
    )
    from agent.registry_loader import load_agent_registry_with_warnings

    # OBSRV-01: live registry snapshot (loader caches internally)
    try:
        entries, missing = load_agent_registry_with_warnings()
        schema_ok = True
    except Exception as exc:
        _log.warning("orchestrator status: registry load failed: %s", exc)
        entries, missing, schema_ok = [], [], False

    return {
        "agent_registry": get_agent_registry_metrics(entries, missing, schema_ok),
        "round_table": get_round_table_metrics(),
        "memory_backend": get_memory_backend_metrics(),
        "snapshot_at": _now_iso_utc(),
    }
```

### Registry loader test pattern (for Validation Architecture)
```python
# Source: tests/agent/test_registry_loader.py:500-535 (TestMissingExpertAlarm) — VERIFIED
class TestMissingExpertAlarm:
    def test_alarm_fires_when_screenplay_missing(self, caplog: pytest.LogCaptureFixture):
        _reset_registry_cache()
        _stage_required_experts(exclude={"screenplay"})
        from agent.registry_loader import load_agent_registry_with_warnings
        with caplog.at_level(logging.WARNING, logger="agent.registry_loader"):
            _entries, warnings = load_agent_registry_with_warnings(force_reload=True)
        assert "screenplay" in warnings
```

**Phase 67 OBSRV-01 test follows the same staging pattern** but asserts on the metrics entry shape returned by `get_agent_registry_metrics(entries, missing, schema_ok)`.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No observability (Phase 52-66) | In-memory ring buffer + FastAPI endpoint (Phase 67) | 2026-07-08 | Operators get first real-time view of agent registry + round table + memory health |
| Prometheus/Grafana (industry standard for web services) | Deferred to v14+ | — | Phase 67 deliberately ships a minimal stdlib-only stack; the API surface (`/orchestrator/agents/status` JSON) is Prometheus-exportable later without rework |

**Deprecated/outdated:**
- None — this is the first observability layer for the v10.0 orchestrator design.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Mem0 Platform server-side compaction is not observable from the client (so `compaction_triggers: 0` is honest) | OBSRV-03 instrumentation | LOW — if mem0 ever exposes a client-side compaction event, we add a capture point; no architectural rework |
| A2 | `get_last_call_usage()` is safe to read immediately after `call_llm` because the per-roundId serial lock prevents concurrent LLM calls within one round | Pitfall 3 | LOW — verified by reading `round_table_executor.py:110-154` (the lock is held across the entire turn) |
| A3 | `submit_round_table_result`'s returned dict always contains `tokensConsumed` and `costUsdEstimate` on the happy path | OBSRV-02 per-round-table capture | LOW — verified at `round_table_state.py:597-601` (the function sets these unconditionally on the completed transition) |

All three assumptions are LOW risk and verified by direct source reading. No user confirmation needed.

## Open Questions

1. **Should `/orchestrator/agents/status` also expose the raw agent names list, or just the count?**
   - What we know: OBSRV-01 spec says "21 agents loaded · schema validation status · missing-expert 告警 · lineage integrity check"
   - What's unclear: whether operator UI (Phase 68) wants the full name list for display, or just `agents_loaded: 21`
   - Recommendation: Include both — `agents_loaded: int` AND `agent_names: list[str]` (sorted). Cheap to serialize, useful for operator triage. Phase 68 CLI can truncate if needed.

2. **Should the round table metrics buffer survive a gateway restart?**
   - What we know: G1 locks in-memory (no persistence)
   - What's unclear: whether operators expect historical p95 across restarts
   - Recommendation: NO — G1 is locked. If operators need history, Phase 68 CLI can read the existing `~/.hermes/agents/.runtime/*/round_tables/*.json` state files (which DO persist per-round tokensConsumed + costUsdEstimate). The in-memory buffer is for "recent workload" semantics only.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | All collectors | ✓ | 3.13 (per `pyproject.toml [tool.ty]`) | — |
| `fastapi==0.133.1` | `/orchestrator/agents/status` endpoint | ✓ | 0.133.1 (`[web]` extra) | — |
| `uvicorn[standard]==0.41.0` | `hermes dashboard` server | ✓ | 0.41.0 | — |
| `mem0ai` (optional) | OBSRV-03 memory metrics | Conditional | — | If `MEM0_API_KEY` unset, `_BackendAdapter.is_available()` returns False; metrics buffer records zero ops. Endpoint reports `memory_backend: {status: "unavailable", ...}`. |
| Live GLM API key | OBSRV-02 real round table metrics | Conditional | — | If no round tables have run, buffer is empty; endpoint returns `count: 0` percentiles. |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** `mem0ai` and GLM API key are optional — the endpoint degrades gracefully to zero-count metrics when the underlying services aren't exercised.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 + pytest-timeout 2.4.0 (existing `[dev]` extra) |
| Config file | `pyproject.toml [tool.pytest.ini_options]` (existing — `addopts`, 30s timeout) |
| Quick run command | `python -m pytest tests/agent/observability/ tests/hermes_cli/test_web_server_orchestrator_status.py -x` |
| Full suite command | `python scripts/run_tests_parallel.py` (existing project-wide runner) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| OBSRV-01 | `get_agent_registry_metrics()` returns correct shape with `agents_loaded`, `missing_experts`, `schema_validation_ok`, `lineage_integrity_ok` | unit | `python -m pytest tests/agent/observability/test_agent_registry_metrics.py -x` | ❌ Wave 0 |
| OBSRV-01 | `/orchestrator/agents/status` returns 200 with all 3 sections | integration | `python -m pytest tests/hermes_cli/test_web_server_orchestrator_status.py::test_status_returns_all_sections -x` | ❌ Wave 0 |
| OBSRV-01 | `/orchestrator/agents/status` rejects unauthenticated request (401) | integration | `python -m pytest tests/hermes_cli/test_web_server_orchestrator_status.py::test_status_requires_auth -x` | ❌ Wave 0 |
| OBSRV-01 | Lineage integrity check flags entry missing `source_sha256` | unit | `python -m pytest tests/agent/observability/test_agent_registry_metrics.py::test_lineage_check_flags_missing_sha -x` | ❌ Wave 0 |
| OBSRV-02 | `_round_table_capture` records latency on happy path | unit | `python -m pytest tests/agent/observability/test_round_table_metrics.py::test_capture_records_latency -x` | ❌ Wave 0 |
| OBSRV-02 | `_round_table_capture` records entry even on exception | unit | `python -m pytest tests/agent/observability/test_round_table_metrics.py::test_capture_on_exception -x` | ❌ Wave 0 |
| OBSRV-02 | `get_round_table_metrics()` returns p50/p95 = 0.0 on empty buffer (Pitfall 1) | unit | `python -m pytest tests/agent/observability/test_round_table_metrics.py::test_empty_buffer_returns_zero_percentiles -x` | ❌ Wave 0 |
| OBSRV-02 | `get_round_table_metrics()` returns correct p95 on 100-element buffer | unit | `python -m pytest tests/agent/observability/test_round_table_metrics.py::test_p95_on_full_buffer -x` | ❌ Wave 0 |
| OBSRV-03 | `_memory_op_capture("search")` records latency + hit_count | unit | `python -m pytest tests/agent/observability/test_memory_backend_metrics.py::test_search_capture -x` | ❌ Wave 0 |
| OBSRV-03 | `_memory_op_capture("add")` records success/error | unit | `python -m pytest tests/agent/observability/test_memory_backend_metrics.py::test_add_capture -x` | ❌ Wave 0 |
| OBSRV-03 | Conflict counter increments on `append_conflict_record` call | unit | `python -m pytest tests/agent/observability/test_memory_backend_metrics.py::test_conflict_counter -x` | ❌ Wave 0 |
| SHARED | `MetricsBuffer(maxlen=100)` evicts oldest on append | unit | `python -m pytest tests/agent/observability/test_ring_buffer.py::test_eviction -x` | ❌ Wave 0 |
| SHARED | `MetricsBuffer` is thread-safe under concurrent append + snapshot | unit | `python -m pytest tests/agent/observability/test_ring_buffer.py::test_thread_safety -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/agent/observability/ -x` (unit tests only, < 5s)
- **Per wave merge:** `python -m pytest tests/agent/observability/ tests/hermes_cli/test_web_server_orchestrator_status.py -x` (full Phase 67 suite)
- **Phase gate:** Full suite green before `/gsd:verify-work` — includes the integration test hitting the FastAPI `TestClient`

### Wave 0 Gaps
- [ ] `tests/agent/observability/__init__.py` — package marker
- [ ] `tests/agent/observability/test_ring_buffer.py` — covers SHARED requirements (MetricsBuffer eviction + thread safety)
- [ ] `tests/agent/observability/test_agent_registry_metrics.py` — covers OBSRV-01 unit tests
- [ ] `tests/agent/observability/test_round_table_metrics.py` — covers OBSRV-02 unit tests (empty buffer, full buffer, capture-on-exception)
- [ ] `tests/agent/observability/test_memory_backend_metrics.py` — covers OBSRV-03 unit tests
- [ ] `tests/hermes_cli/test_web_server_orchestrator_status.py` — covers OBSRV-01 integration (TestClient hits `/orchestrator/agents/status`, asserts 200 + 3 sections + auth gate)

*(Framework install: none — pytest already in `[dev]` extra, already configured)*

## Security Domain

> `security_enforcement` is implicitly enabled (no `workflow.nyquist_validation: false` in config.json — verified).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | (delegated to existing dashboard auth gate — no new auth path) |
| V3 Session Management | yes (inherit) | Endpoint MUST go through existing `_require_token(request)` / OAuth cookie gate — see Pitfall 5. No new session handling. |
| V4 Access Control | yes | Endpoint path `/orchestrator/agents/status` MUST NOT be added to `PUBLIC_API_PATHS` — agent names + lineage SHAs are operator-sensitive recon |
| V5 Input Validation | no | GET endpoint with no query params; no user input to validate |
| V6 Cryptography | no | No crypto operations |
| V7 Error Handling | yes | Loader failures caught + logged + surfaced as `schema_validation_ok: false`; never crash the endpoint |
| V9 Communications | yes (inherit) | FastAPI HTTPS via existing `hermes dashboard` server — no new transport |

### Known Threat Patterns for observability endpoint

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Information disclosure via unauthenticated metrics scrape | Information Disclosure | Endpoint behind auth gate (Pitfall 5); NOT in `PUBLIC_API_PATHS` |
| Agent name / lineage SHA recon → targeted agent spoofing | Information Disclosure → Spoofing | Same auth gate; agent names are operator-only |
| Metrics buffer memory exhaustion (DoS via thousands of ops/sec) | Denial of Service | `deque(maxlen=100)` — bounded by construction; no attacker-controllable growth |
| Timing side-channel on `load_agent_registry_with_warnings` (filesystem read latency leaks agent count) | Information Disclosure | Acceptable — attacker already authenticated as operator; the same info is available via `ls ~/.hermes/agents/` |

## Recommended Plan Structure

3 plans across 2 waves. The shared primitive (Wave 0) unblocks parallel collector work; the FastAPI endpoint (Wave 1) depends on all 3 collectors being callable.

### Wave 0: Foundation (sequential)
- **Plan 67-01: Shared ring buffer + OBSRV-01 collector + unit tests**
  - Task 1: Create `agent/observability/__init__.py` (registry exports)
  - Task 2: Create `agent/observability/_ring_buffer.py` (`MetricsBuffer` class with thread-safe append + snapshot)
  - Task 3: Create `agent/observability/agent_registry_metrics.py` (`get_agent_registry_metrics()` + lineage integrity check)
  - Task 4: Create `tests/agent/observability/test_ring_buffer.py` (eviction + thread safety)
  - Task 5: Create `tests/agent/observability/test_agent_registry_metrics.py` (shape + lineage flagging)

### Wave 1: Collectors (parallel — independent modules)
- **Plan 67-02: OBSRV-02 round table metrics collector + instrumentation + unit tests**
  - Task 1: Create `agent/observability/round_table_metrics.py` (`_round_table_capture` ctx mgr + `get_round_table_metrics()` getter + `_percentiles()` helper)
  - Task 2: Instrument `mcp_serve.get_agent_opinion` (wrap lines 753-928)
  - Task 3: Instrument `mcp_serve.submit_round_table_result` (wrap lines 996-1010 result read)
  - Task 4: Create `tests/agent/observability/test_round_table_metrics.py` (empty buffer Pitfall 1 + full buffer p95 + capture-on-exception)

- **Plan 67-03: OBSRV-03 memory backend metrics collector + instrumentation + unit tests**
  - Task 1: Create `agent/observability/memory_backend_metrics.py` (`_memory_op_capture` ctx mgr + `get_memory_backend_metrics()` getter)
  - Task 2: Instrument `plugins/memory/mem0/_BackendAdapter.search` + `.add`
  - Task 3: Instrument `agent/memory_arbitration.append_conflict_record` call sites
  - Task 4: Create `tests/agent/observability/test_memory_backend_metrics.py` (search/add capture + conflict counter)

### Wave 2: Endpoint (sequential — depends on all 3 collectors)
- **Plan 67-04: FastAPI `/orchestrator/agents/status` endpoint + integration tests**
  - Task 1: Add `@app.get("/orchestrator/agents/status")` handler to `hermes_cli/web_server.py` (near line 1913, after `/api/system/stats`)
  - Task 2: Confirm handler uses `_require_token(request)` (NOT in `PUBLIC_API_PATHS`)
  - Task 3: Create `tests/hermes_cli/test_web_server_orchestrator_status.py` (TestClient asserts 200 + 3 sections + auth gate 401)
  - Task 4: Run full Phase 67 suite + verify all percentiles degrade gracefully on empty buffers

**Dependency graph:**
```
Plan 67-01 (Wave 0) ──► Plan 67-02 (Wave 1) ──┐
                ──────► Plan 67-03 (Wave 1) ──┼──► Plan 67-04 (Wave 2)
                                           ───┘
```

## Sources

### Primary (HIGH confidence)
- `agent/registry_loader.py` — read in full (lines 1-536); confirmed `load_agent_registry_with_warnings` signature + return shape + `REQUIRED_DAG_EXPERTS` + lineage expectations
- `agent/round_table_executor.py` — read in full (lines 1-295); confirmed `acquire_round_or_reject` + serial lock semantics + INFRA-04 constraint
- `agent/round_table_state.py` — read in full (lines 1-811); confirmed `submit_round_table_result` returns dict with `tokensConsumed` + `costUsdEstimate` + `status` + `turns`
- `mcp_serve.py:688-1010` — read `get_agent_opinion` + `submit_round_table_result` bodies; confirmed instrumentation line anchors
- `plugins/memory/mem0/__init__.py` — read in full (lines 1-501); confirmed `_BackendAdapter.search/add` + `backend` singleton
- `agent/memory_arbitration.py:355-509` — read `append_conflict_record` + `memory_retrieve_scoped` + `memory_submit_record`
- `hermes_cli/web_server.py:1-300, 1699-2000` — read FastAPI app + `/api/status` + `/api/system/stats` endpoint patterns
- `hermes_cli/dashboard_auth/public_paths.py` — read in full; confirmed auth gate semantics
- `tests/agent/test_registry_loader.py:440-540` — read `TestMissingExpertAlarm` canary pattern
- `agent/auxiliary_client.py:5060-5125` — confirmed `get_last_call_usage()` reads module-level `_LAST_CALL_USAGE` dict
- Local runtime verification: `python3 -c "import statistics; statistics.quantiles([], n=100)"` → `StatisticsError` confirmed

### Secondary (MEDIUM confidence)
- `python.org` stdlib docs for `collections.deque`, `time.perf_counter`, `statistics.quantiles` — cited inline

### Tertiary (LOW confidence)
- None — all findings verified by direct source reading or runtime verification

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — stdlib only, all APIs verified against actual source files
- Architecture: HIGH — module-level singleton pattern is the codebase's established convention; 5-file package layout is minimal and follows existing `agent/` structure
- Instrumentation points: HIGH — exact line numbers verified by reading `mcp_serve.py`, `plugins/memory/mem0/__init__.py`, `agent/memory_arbitration.py`
- Pitfalls: HIGH — Pitfall 1 (`StatisticsError`) verified at runtime; Pitfalls 2-6 grounded in codebase patterns (threading.Lock usage, lazy imports, auth gate)

**Research date:** 2026-07-08
**Valid until:** 2026-08-07 (30 days — stable; no external API dependencies that could drift)
