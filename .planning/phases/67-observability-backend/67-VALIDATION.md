---
phase: 67
slug: observability-backend
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-08
---

# Phase 67 — Validation Strategy

> Per-phase validation contract for 3 observability collectors + FastAPI endpoint.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest==9.0.2` + `pytest-asyncio==1.3.0` + `pytest-timeout==2.4.0` (existing `[dev]`) |
| **Config file** | `pyproject.toml [tool.pytest.ini_options]` |
| **Quick run command** | `python -m pytest tests/agent/observability/ -x` |
| **Full suite command** | `python -m pytest tests/agent/observability/ tests/hermes_cli/test_web_server_orchestrator_status.py -x` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **Per task commit:** `python -m pytest tests/agent/observability/ -x` (<5s)
- **Per wave merge:** Full Phase 67 suite (<10s)
- **Before `/gsd:verify-work`:** Full suite green + integration test (TestClient hits `/orchestrator/agents/status`)
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 67-01-01 | 01 (foundation) | 0 | SHARED | — | `MetricsBuffer(maxlen=100)` evicts oldest on append | unit | `python -m pytest tests/agent/observability/test_ring_buffer.py::test_eviction -x` | ❌ W0 | ⬜ pending |
| 67-01-02 | 01 | 0 | SHARED | T-thread-safety | `MetricsBuffer` thread-safe under concurrent append + snapshot | unit | `python -m pytest tests/agent/observability/test_ring_buffer.py::test_thread_safety -x` | ❌ W0 | ⬜ pending |
| 67-01-03 | 01 | 0 | OBSRV-01 | — | `get_agent_registry_metrics()` returns shape with 4 fields | unit | `python -m pytest tests/agent/observability/test_agent_registry_metrics.py -x` | ❌ W0 | ⬜ pending |
| 67-01-04 | 01 | 0 | OBSRV-01 (lineage) | — | Lineage integrity check flags entry missing `source_sha256` | unit | `python -m pytest tests/agent/observability/test_agent_registry_metrics.py::test_lineage_check_flags_missing_sha -x` | ❌ W0 | ⬜ pending |
| 67-02-01 | 02 (round table) | 1 | OBSRV-02 | — | `_round_table_capture` records latency on happy path | unit | `python -m pytest tests/agent/observability/test_round_table_metrics.py::test_capture_records_latency -x` | ❌ W0 | ⬜ pending |
| 67-02-02 | 02 | 1 | OBSRV-02 (exception path) | — | `_round_table_capture` records entry even on exception | unit | `python -m pytest tests/agent/observability/test_round_table_metrics.py::test_capture_on_exception -x` | ❌ W0 | ⬜ pending |
| 67-02-03 | 02 | 1 | OBSRV-02 (Pitfall #1) | — | `get_round_table_metrics()` returns p50/p95=0.0 on empty buffer | unit | `python -m pytest tests/agent/observability/test_round_table_metrics.py::test_empty_buffer_returns_zero_percentiles -x` | ❌ W0 | ⬜ pending |
| 67-02-04 | 02 | 1 | OBSRV-02 (full buffer) | — | p95 correct on 100-element buffer | unit | `python -m pytest tests/agent/observability/test_round_table_metrics.py::test_p95_on_full_buffer -x` | ❌ W0 | ⬜ pending |
| 67-03-01 | 03 (memory) | 1 | OBSRV-03 | — | `_memory_op_capture("search")` records latency + hit_count | unit | `python -m pytest tests/agent/observability/test_memory_backend_metrics.py::test_search_capture -x` | ❌ W0 | ⬜ pending |
| 67-03-02 | 03 | 1 | OBSRV-03 (add) | — | `_memory_op_capture("add")` records success/error | unit | `python -m pytest tests/agent/observability/test_memory_backend_metrics.py::test_add_capture -x` | ❌ W0 | ⬜ pending |
| 67-03-03 | 03 | 1 | OBSRV-03 (conflict) | — | Conflict counter increments on `append_conflict_record` | unit | `python -m pytest tests/agent/observability/test_memory_backend_metrics.py::test_conflict_counter -x` | ❌ W0 | ⬜ pending |
| 67-04-01 | 04 (FastAPI endpoint) | 2 | OBSRV-01 (HTTP) | T-67-01 (info disclosure via unauth) | `/orchestrator/agents/status` returns 200 with 3 sections | integration | `python -m pytest tests/hermes_cli/test_web_server_orchestrator_status.py::test_status_returns_all_sections -x` | ❌ W0 | ⬜ pending |
| 67-04-02 | 04 | 2 | OBSRV-01 (auth gate) | T-67-01 | Rejects unauthenticated request (401) | integration | `python -m pytest tests/hermes_cli/test_web_server_orchestrator_status.py::test_status_requires_auth -x` | ❌ W0 | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `tests/agent/observability/__init__.py` — package marker
- [ ] `tests/agent/observability/test_ring_buffer.py` — SHARED tests (eviction + thread safety)
- [ ] `tests/agent/observability/test_agent_registry_metrics.py` — OBSRV-01 unit tests
- [ ] `tests/agent/observability/test_round_table_metrics.py` — OBSRV-02 unit tests
- [ ] `tests/agent/observability/test_memory_backend_metrics.py` — OBSRV-03 unit tests
- [ ] `tests/hermes_cli/test_web_server_orchestrator_status.py` — OBSRV-01 integration via TestClient
- [ ] `agent/observability/__init__.py` — registry exports
- [ ] `agent/observability/_ring_buffer.py` — MetricsBuffer class
- [ ] `agent/observability/agent_registry_metrics.py` — OBSRV-01 collector
- [ ] `agent/observability/round_table_metrics.py` — OBSRV-02 collector
- [ ] `agent/observability/memory_backend_metrics.py` — OBSRV-03 collector

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live `/orchestrator/agents/status` against running `hermes dashboard` | OBSRV-01 (operator UX) | Requires starting the dashboard server (operator-visible process); CI uses TestClient | Operator: `hermes dashboard &` then `curl -H "Authorization: Bearer <token>" http://localhost:<port>/orchestrator/agents/status \| jq .` |

*All structural / quantitative behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (6 new test files + 5 new module files)
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending planner/checker confirmation
