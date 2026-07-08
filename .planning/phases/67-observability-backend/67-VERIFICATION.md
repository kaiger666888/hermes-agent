---
phase: 67-observability-backend
verified: 2026-07-08T14:05:00Z
status: human_needed
score: 7/7 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: N/A
  gaps_closed: []
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Live curl against running `hermes dashboard` server"
    expected: "200 JSON with all 4 top-level keys (agent_registry, round_table, memory_backend, snapshot_at) and the 6 OBSRV-01 fields populated from the live 21-agent registry"
    why_human: "Requires starting the dashboard server (operator-visible process); CI uses fastapi.testclient.TestClient which does not exercise the real bind + middleware chain. Live auth in production bind (loopback or OAuth) and real concurrent round-table execution are out of automated reach."
---

# Phase 67: Observability Backend Verification Report

**Phase Goal:** 3 metrics collectors + wired into runtime + FastAPI `/orchestrator/agents/status` endpoint.
**Verified:** 2026-07-08T14:05:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

Must-haves merged from ROADMAP Success Criteria (3 SCs) + PLAN frontmatter (4 plans). The 3 ROADMAP SCs are the contract; PLAN truths add implementation-level detail. Deduplication kept the SC wording where it restated a plan truth.

| # | Truth | Source | Status | Evidence |
| --- | --- | --- | --- | --- |
| 1 | Agent registry health collector at `/orchestrator/agents/status` (SC#1) | ROADMAP SC#1 | VERIFIED | Endpoint registered on FastAPI app; live TestClient GET returns 200 with all 4 top-level keys + 6 OBSRV-01 fields (`agents_loaded=21`, `schema_validation_ok`, `missing_experts`, `lineage_integrity_ok`, `agent_names`, `snapshot_at_iso`); 5 integration tests green; auth gate test asserts 401 on no-token; not in `PUBLIC_API_PATHS` |
| 2 | Round table metrics collector wired into executor: latency p50/p95, token cost, state transitions, serial-lock wait, early-stop rate (SC#2) | ROADMAP SC#2 | VERIFIED | `mcp_serve.get_agent_opinion` source contains `_turn_capture`, `serial_lock_wait_ms`, `get_last_call_usage`; `submit_round_table_result` contains `_submit_capture`; `get_round_table_metrics()` returns all 5 SC-mandated dimensions (p50/p95/total_token_cost/status_distribution/serial_lock_wait_p95_ms/early_stop_rate); 13 unit tests green; live data-flow: 100 samples [1..100]ms → p50=50.50, p95=95.95 (real `statistics.quantiles` computation, not hardcoded) |
| 3 | Memory backend metrics collector wired into mem0 adapter: p95 read/write, conflict rate, compaction rate, error rate (SC#3) | ROADMAP SC#3 | VERIFIED | `plugins.memory.mem0._BackendAdapter.search` + `.add` source contain `_memory_op_capture` + `mark_failure` (WR-01 fix applied — 3 silent-degradation branches now correctly signal failure); `agent.memory_arbitration.append_conflict_record` calls `record_conflict()`; `get_memory_backend_metrics()` returns all 5 SC-mandated dimensions; 8 unit tests green; live data-flow: 100 search samples → search_p95=95.95, conflict_count=3 after 3 calls |
| 4 | `get_agent_registry_metrics` is importable and callable | 67-01-PLAN truth | VERIFIED | `from agent.observability import get_agent_registry_metrics` succeeds; pure function computing 6-key dict from `(entries, missing, schema_ok)`; tested with live 21-agent registry (`agents_loaded=21 == len(loader entries)`) |
| 5 | `MetricsBuffer` is thread-safe + bounded (auto-evict) | 67-01-PLAN truth | VERIFIED | `MetricsBuffer(maxlen=100)` with `threading.Lock` on both `append` + `snapshot`; 6 unit tests cover eviction, thread safety (10 threads × 1000 appends), snapshot-is-a-copy, `clear()` (added by WR-05 fix); `deque(maxlen=N)` bounded by construction |
| 6 | `get_round_table_metrics` importable; `_percentiles` empty-buffer-safe (no StatisticsError) | 67-02-PLAN truth | VERIFIED | Importable from `agent.observability`; `_percentiles([])` returns `{p50:0.0, p95:0.0, count:0}` (Pitfall 1 mitigated); `_percentiles([1.0])` returns single value; tested explicitly |
| 7 | `get_memory_backend_metrics` importable; empty-buffer returns zeros (no StatisticsError); exception path records `success=False` | 67-03-PLAN truth | VERIFIED | Importable; empty buffer returns zeros; exception path records failure via dual-path design (propagation OR `mark_failure`); WR-01 fix ensures mem0 backend error responses (not just exceptions) are counted as failures |

**Score:** 7/7 truths verified

### Required Artifacts

All artifacts pass Level 1 (exists), Level 2 (substantive), Level 3 (wired), and Level 4 (data flowing). No stubs, no orphans, no hollow wiring.

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `agent/observability/__init__.py` | Package marker + 3-getter re-export | VERIFIED (26 lines) | Re-exports `get_agent_registry_metrics`, `get_round_table_metrics`, `get_memory_backend_metrics` with `__all__`; single-import surface works (verified runtime) |
| `agent/observability/_ring_buffer.py` | `MetricsBuffer[T]` thread-safe primitive | VERIFIED (129 lines) | `deque(maxlen=N)` + `threading.Lock`; eviction, thread safety, `clear()` (WR-05), `snapshot()` returns copy |
| `agent/observability/agent_registry_metrics.py` | OBSRV-01 collector + `_check_lineage` | VERIFIED (121 lines) | Pure function, 6-key dict, defensive `entry.get("lineage") or {}`, vacuous-truth on empty entries |
| `agent/observability/round_table_metrics.py` | OBSRV-02 collector + 2 ctx mgrs + `_percentiles` | VERIFIED (368 lines) | `RoundTableMetricEntry` dataclass, `_CaptureState` mutable holder, sync `@contextmanager`, `_reset_for_test` via `_BUFFER.clear()` |
| `agent/observability/memory_backend_metrics.py` | OBSRV-03 collector + `_memory_op_capture` + `record_conflict` | VERIFIED (422 lines) | `MemoryOpMetricEntry`, dual-path failure detection, dedicated `_CONFLICT_LOCK`, `_percentile_p95`, honest-zero `compaction_triggers` per RESEARCH A1 |
| `hermes_cli/web_server.py` | GET `/orchestrator/agents/status` handler | VERIFIED (+50 lines) | Plain `def` (Pitfall 4), `_require_token` first line (Pitfall 5), lazy imports (Pitfall 6), try/except graceful degrade; verified via `inspect.getsource` + live TestClient |
| `mcp_serve.py` (instrumented) | `_turn_capture` + `_submit_capture` + `serial_lock_wait_ms` + `get_last_call_usage` | VERIFIED | Confirmed in source of both `get_agent_opinion` + `submit_round_table_result`; INFRA-04 preserved (sync `@contextmanager`) |
| `plugins/memory/mem0/__init__.py` (instrumented) | `_memory_op_capture` + `mark_failure` in search + add | VERIFIED | 3 silent-degradation branches now call `cap.mark_failure(RuntimeError(...))` per WR-01 fix; "never raise" adapter contract preserved |
| `agent/memory_arbitration.py` (instrumented) | `record_conflict()` in `append_conflict_record` | VERIFIED | Lazy import + single call near top of function body (before JSONL write) |
| `tests/agent/observability/test_*.py` | Wave 0 + OBSRV-02 + OBSRV-03 unit tests | VERIFIED (624 lines across 4 files) | 6 + 11 + 13 + 8 = 38 tests, all green |
| `tests/hermes_cli/test_web_server_orchestrator_status.py` | 5 integration tests via TestClient | VERIFIED (166 lines) | 5 tests green: 200 happy path, 6-field shape, 401 auth gate, NOT-in-PUBLIC_API_PATHS, registry-failure graceful |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `hermes_cli/web_server.py` | `agent/observability/__init__.py` | lazy import inside handler body | WIRED | `from agent.observability import get_agent_registry_metrics, get_round_table_metrics, get_memory_backend_metrics` — verified by successful live endpoint call returning real data from all 3 collectors |
| `hermes_cli/web_server.py` | `agent/registry_loader.py` | lazy import + live call | WIRED | `from agent.registry_loader import load_agent_registry_with_warnings` — live call returns 21 entries, propagated through collector; failure path (mock raising) returns 200 with `schema_validation_ok=False` |
| `hermes_cli/web_server.py` | `hermes_cli/dashboard_auth/public_paths.py` | frozenset inspection | WIRED (negative) | `assert '/orchestrator/agents/status' not in PUBLIC_API_PATHS` passes (security invariant holds; endpoint NOT leaked to unauthenticated callers) |
| `mcp_serve.get_agent_opinion` | `agent/observability/round_table_metrics.py` | `_turn_capture` wrap | WIRED | Source contains `with _turn_capture(round_id) as cap`, `cap.serial_lock_wait_ms = ...`, `cap.token_cost = int(get_last_call_usage()...)` |
| `mcp_serve.submit_round_table_result` | `agent/observability/round_table_metrics.py` | `_submit_capture` wrap | WIRED | Source contains `with _submit_capture(round_id) as cap`, populates token_cost/cost_usd/turn_count/early_stop_triggered from result dict |
| `plugins/memory.mem0._BackendAdapter.search` | `agent/observability/memory_backend_metrics.py` | `_memory_op_capture` wrap | WIRED | `with _memory_op_capture("search") as cap:`, `cap.hit_count = len(out)`, `cap.mark_failure(exc)` + 2 additional `mark_failure` calls per WR-01 |
| `plugins/memory.mem0._BackendAdapter.add` | `agent/observability/memory_backend_metrics.py` | `_memory_op_capture` wrap | WIRED | `with _memory_op_capture("add") as cap:`, `mark_failure(exc)` in except branch, `mark_failure(RuntimeError("mem0_error_response: ..."))` on parsed-error branch |
| `agent/memory_arbitration.append_conflict_record` | `agent/observability/memory_backend_metrics.py` | `record_conflict()` call | WIRED | `from agent.observability.memory_backend_metrics import record_conflict` + `record_conflict()` near top of function body |
| `agent/observability/__init__.py` | 3 collector submodules | re-export | WIRED | All 3 imports present in `__init__.py`; `__all__` lists all 3; single-import statement verified at runtime |

### Data-Flow Trace (Level 4)

Each collector traced end-to-end from real data source to endpoint output. No hardcoded values, no disconnected props, no hollow wiring.

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `get_agent_registry_metrics` | `agents_loaded` | `len(entries)` from `load_agent_registry_with_warnings()` | YES — live registry returns 21 agents; `agents_loaded == 21 == len(loader entries)` | FLOWING |
| `get_agent_registry_metrics` | `lineage_integrity_ok` | `_check_lineage(entries)` walks each entry's `lineage.source_sha256` + `transform_rule_id` | YES — defensive predicate over real parsed YAML dicts | FLOWING |
| `get_round_table_metrics` | `p50_latency_ms`, `p95_latency_ms` | `_percentiles(samples)` over `duration_ms` from buffer | YES — 100 samples [1..100]ms → p50=50.50, p95=95.95 (matches `statistics.quantiles(data, n=100)`) | FLOWING |
| `get_round_table_metrics` | `status_distribution` | `Counter(entry.status for entry in snapshot)` | YES — computed from buffer entries; empty buffer returns `{}` | FLOWING |
| `get_round_table_metrics` | `serial_lock_wait_p95_ms` | `_percentiles` over `serial_lock_wait_ms` samples | YES — populated from `perf_counter()` delta captured in `mcp_serve.get_agent_opinion` before/after `acquire_round_or_reject` | FLOWING |
| `get_memory_backend_metrics` | `search_p95_ms`, `add_p95_ms` | `_percentile_p95(samples)` per `op_type` | YES — 100 search samples [1..100]ms → search_p95=95.95 | FLOWING |
| `get_memory_backend_metrics` | `error_rate` | `failures / total` over buffer entries | YES — entries' `success` flag set via dual-path (exception propagation OR `mark_failure` for mem0 adapter's swallowing try/except, per WR-01 fix) | FLOWING |
| `get_memory_backend_metrics` | `conflict_count` | `_CONFLICT_COUNT` incremented by `record_conflict()` | YES — 3 calls to `append_conflict_record` → `conflict_count == 3` | FLOWING |
| `get_memory_backend_metrics` | `compaction_triggers` | Constant `0` | STATIC (intentional) | Documented honest-zero per RESEARCH A1 — Mem0 Platform server-side compaction is not client-observable; revisit v14 if self-hosted mem0. Not a stub — explicit design decision cited in module docstring + inline comment |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| SC#1 endpoint tests | `python3 -m pytest tests/hermes_cli/test_web_server_orchestrator_status.py -x -v` | 5 passed in 0.78s | PASS |
| SC#2 round table tests | `python3 -m pytest tests/agent/observability/test_round_table_metrics.py -x -v` | 13 passed in 0.34s | PASS |
| SC#3 memory backend tests | `python3 -m pytest tests/agent/observability/test_memory_backend_metrics.py -x -v` | 8 passed in 0.27s | PASS |
| Full Phase 67 suite | `python3 -m pytest tests/agent/observability/ tests/hermes_cli/test_web_server_orchestrator_status.py -x` | 43 passed in 1.46s | PASS |
| Endpoint registered | `python3 -c "from hermes_cli.web_server import app; assert '/orchestrator/agents/status' in [r.path for r in app.routes if hasattr(r, 'path')]"` | `OK: endpoint registered` | PASS |
| 3 getters importable | `python3 -c "from agent.observability import get_agent_registry_metrics, get_round_table_metrics, get_memory_backend_metrics"` | `OK: all 3 getters importable` | PASS |
| Auth gate (no token) | TestClient loopback mode, no `X-Hermes-Session-Token` | 401 Unauthorized | PASS |
| Auth gate (valid token) | TestClient loopback mode + valid header | 200 with full JSON | PASS |
| Registry-failure graceful | Mock loader to raise RuntimeError | 200 with `schema_validation_ok=False` (not 500) | PASS |
| Handler is sync `def` | `inspect.iscoroutinefunction(get_orchestrator_agents_status)` | False (Pitfall 4 OK) | PASS |
| NOT in PUBLIC_API_PATHS | `'/orchestrator/agents/status' not in PUBLIC_API_PATHS` | True (security invariant) | PASS |
| OBSRV-02 instrumentation | `inspect.getsource(mcp_serve.get_agent_opinion)` contains `_turn_capture`, `serial_lock_wait_ms`, `get_last_call_usage` | All 3 found | PASS |
| OBSRV-03 instrumentation | `inspect.getsource(_BackendAdapter.search)` + `.add` contain `_memory_op_capture` + `mark_failure`; `append_conflict_record` contains `record_conflict` | All found (WR-01 fix verified) | PASS |
| SC#2 live data-flow | 100 buffer entries [1..100]ms → `get_round_table_metrics()` | `count=100, p50=50.50, p95=95.95` | PASS |
| SC#3 live data-flow | 100 search entries + 3 conflict calls → `get_memory_backend_metrics()` | `search_count=100, search_p95=95.95, conflict_count=3` | PASS |

### Probe Execution

No conventional `scripts/*/tests/probe-*.sh` probes declared for this phase. Plan `<verification>` blocks specified pytest invocations (executed above under Behavioral Spot-Checks) + runtime `inspect.getsource` checks (executed above). All declared verification commands reproduced successfully.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- | 
| OBSRV-01 | 67-01, 67-04 | Agent registry health collector — 21 agents loaded, schema validation, missing-expert alarm, lineage integrity; wired into `hermes dashboard` FastAPI `/orchestrator/agents/status` | SATISFIED | Truth #1 + #4; collector returns 6-key dict with live 21-agent data; endpoint registered + returns 200 + 401 auth gate + graceful degrade |
| OBSRV-02 | 67-02 | Round table metrics collector — latency p50/p95, token cost, state transitions, serial-lock wait, early-stop rate; wired into round table executor | SATISFIED | Truth #2 + #6; `mcp_serve.get_agent_opinion` + `submit_round_table_result` instrumented; all 5 SC-mandated dimensions present in `get_round_table_metrics()` |
| OBSRV-03 | 67-03 | Memory backend metrics collector — mem0 p95 read/write, conflict rate, compaction rate, error rate; wired into mem0 backend adapter | SATISFIED | Truth #3 + #7; mem0 `_BackendAdapter.search/.add` instrumented with WR-01 fix; `append_conflict_record` wired; all 5 SC-mandated dimensions present |

**Orphaned requirements check:** `grep -E "Phase 67" .planning/REQUIREMENTS.md` returns only OBSRV-01/02/03 — no orphans.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `agent/observability/round_table_metrics.py` | 305, 338 | `except BaseException as exc:` binds `exc` but never uses it (re-raises only) | Info (IN-01) | No behavior impact; deferred per REVIEW default scope. CLAUDE.md convention says "always bind the exception to a name and include it in the log message" but these blocks deliberately don't log |
| `agent/observability/memory_backend_metrics.py` | 366 | Same unused `exc` binding | Info (IN-01) | Same as above |
| `hermes_cli/web_server.py` | 2024 | Imports private `_now_iso` from `agent.round_table_state` | Info (IN-03) | Couples endpoint to an internal helper; works correctly but brittle if upstream refactors. Deferred |
| `hermes_cli/web_server.py` | 2036-2041 | Top-level `snapshot_at` vs per-section `snapshot_at_iso` — naming drift; `memory_backend` section has no per-section timestamp | Info (IN-04) | Four timestamps disagree by microseconds. Not load-bearing for operator UX. Deferred |

**Debt-marker gate:** No `TBD`, `FIXME`, or `XXX` markers in any Phase 67 source file. No `TODO` / `HACK` / `PLACEHOLDER` markers either. The grep for "placeholder" / "coming soon" / "will be here" / "not yet implemented" returned zero hits.

**REVIEW findings disposition:**
- WR-01..05 (WARNING tier, 5 findings): ALL FIXED via dedicated commits (`5b44e6c7c`, `5d60149df`, `5f0b69c2e`, `bbf7178b3`, `c64ba9317`) — confirmed by source inspection (`mark_failure` present in 3 mem0 branches; `MetricsBuffer.clear()` exists; docstring updates present).
- IN-01..04 (INFO tier, 4 findings): Deferred per REVIEW default scope (not blockers).

### Known Limitations (documented, not blocking)

These were identified during code review (WR-02, WR-03) and accepted with documented rationale:

1. **WR-02 (lock-release time in `duration_ms`):** `release_round_lock` runs inside the `with _turn_capture` block, so per-turn `duration_ms` includes the lock-release await time. Uniform bias across all samples — p50/p95 *deltas* remain meaningful for trend analysis. Docstring updated to reflect actual nesting (commit `5d60149df`).
2. **WR-03 (`token_cost` race window):** `_LAST_CALL_USAGE` is a process-global dict; cross-roundId concurrent turns can interleave at the `await call_llm` resolution point and overwrite it. Within-roundId attribution is reliable (INFRA-04 serial). Inline comment labels the metric as "BEST-EFFORT; under cross-roundId concurrency it may be attributed to the wrong turn" (commit `5f0b69c2e`). Proper fix (have `call_llm` return usage inline) is out-of-Phase-67-scope.

Neither limitation prevents the goal ("3 metrics collectors + wired into runtime + endpoint") from being achieved. Both are measurement-accuracy caveats on metrics that ARE computed from real data (not stubs).

### Human Verification Required

### 1. Live Dashboard Curl Smoke

**Test:** Start `hermes dashboard` in the background, then `curl -H "Authorization: Bearer <token>" http://localhost:<port>/orchestrator/agents/status | jq .`
**Expected:** 200 JSON with all 4 top-level keys (`agent_registry`, `round_table`, `memory_backend`, `snapshot_at`) populated from the live 21-agent registry. `agent_registry.agents_loaded == 21`, `agent_registry.agent_names` lists real expert names. After running a real round table + memory operation, the `round_table` and `memory_backend` sections should show non-zero counts and computed percentiles.
**Why human:** Requires starting the dashboard server (operator-visible process) with a real bind. CI uses `fastapi.testclient.TestClient` which does not exercise the real production bind, the OAuth middleware chain (in `auth_required=True` mode), or live round-table / memory operations that would populate the buffers with real-world samples. The TestClient proves the handler logic, the auth gate, and the JSON shape; only a live curl can confirm the operator-visible end-to-end experience. (Per VALIDATION.md "Manual-Only Verifications" table.)

This is the single manual UAT item. All structural and quantitative behaviors have automated verification (43 tests green).

### Gaps Summary

**No gaps found.** All 3 ROADMAP Success Criteria are observably TRUE in the codebase:

- **SC#1:** Agent registry health collector is wired into the FastAPI `/orchestrator/agents/status` endpoint; emits all 6 OBSRV-01 fields from the live 21-agent registry; auth gate + graceful degrade verified.
- **SC#2:** Round table metrics collector is wired into `mcp_serve.get_agent_opinion` + `submit_round_table_result`; emits latency p50/p95 + token cost + status distribution + serial-lock wait p95 + early-stop rate; data-flow verified.
- **SC#3:** Memory backend metrics collector is wired into `plugins.memory.mem0._BackendAdapter.search/.add` + `agent.memory_arbitration.append_conflict_record`; emits search/add p95 + conflict count + compaction-triggers (honest zero) + error rate; WR-01 fix ensures accurate error_rate denominator.

The phase goal "3 metrics collectors + wired into runtime + FastAPI `/orchestrator/agents/status` endpoint" is achieved.

**Status:** `human_needed` — automated checks all PASS, but VALIDATION.md explicitly designates the live dashboard curl as a manual-only verification item. Per Step 9 decision tree, presence of any human verification item forces `human_needed` (even with 7/7 truths verified and no gaps).

---

_Verified: 2026-07-08T14:05:00Z_
_Verifier: Claude (gsd-verifier)_
