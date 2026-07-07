---
phase: 52
slug: infra-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-07
---

# Phase 52 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 (already pinned in `pyproject.toml`) |
| **Config file** | `pyproject.toml:261` (`addopts` includes `-ra --strict-markers --timeout=30`) |
| **Quick run command** | `/data/workspace/hermes-agent/.venv/bin/python -m pytest tests/agent/test_registry_loader.py tests/agent/test_round_table_state.py tests/agent/test_round_table_executor.py -x` |
| **Full suite command** | `/data/workspace/hermes-agent/.venv/bin/python -m pytest tests/agent/ -x` |
| **Estimated runtime** | ~15 seconds for quick; ~60 seconds for full agent suite |

---

## Sampling Rate

- **After every task commit:** Run quick command (registry_loader + round_table_state + round_table_executor tests)
- **After every plan wave:** Run full agent test suite
- **Before `/gsd:verify-work`:** Full suite must be green + 4 INFRA-* SC tests passing
- **Max feedback latency:** 30 seconds (per-test timeout in pyproject.toml)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 52-01-01 | 01 | 1 | INFRA-01 | — | Valid YAML loads + appears in `agents_list` | unit | `pytest tests/agent/test_registry_loader.py::test_valid_yaml_loads -x` | ❌ W0 | ⬜ pending |
| 52-01-02 | 01 | 1 | INFRA-01 | — | Malformed YAML rejected with field-specific error | unit | `pytest tests/agent/test_registry_loader.py::test_malformed_yaml_rejected -x` | ❌ W0 | ⬜ pending |
| 52-01-03 | 01 | 1 | INFRA-01 | — | `name` mismatch with filename stem rejected | unit | `pytest tests/agent/test_registry_loader.py::test_name_filename_mismatch -x` | ❌ W0 | ⬜ pending |
| 52-02-01 | 02 | 2 | INFRA-02 | — | `agents_list` MCP tool returns JSON list | integration | `pytest tests/agent/test_mcp_serve_round_table.py::test_agents_list_returns_json -x` | ❌ W0 | ⬜ pending |
| 52-02-02 | 02 | 2 | INFRA-02 | — | `agent_describe` returns full agent YAML | integration | `pytest tests/agent/test_mcp_serve_round_table.py::test_agent_describe_returns_yaml -x` | ❌ W0 | ⬜ pending |
| 52-02-03 | 02 | 2 | INFRA-02 | — | `memory_retrieve_scoped` returns phase53_not_implemented stub | integration | `pytest tests/agent/test_mcp_serve_round_table.py::test_memory_retrieve_scoped_stub -x` | ❌ W0 | ⬜ pending |
| 52-03-01 | 03 | 2 | INFRA-03 SC#2 | — | `open → opinion → submit` round trip on synthetic agent | integration | `pytest tests/agent/test_mcp_serve_round_table.py::test_lifecycle_round_trip -x` | ❌ W0 | ⬜ pending |
| 52-03-02 | 03 | 2 | INFRA-03 SC#2 | — | Interrupted submit doesn't leave `status` outside schema enum | unit | `pytest tests/agent/test_round_table_state.py::test_interrupted_submit_atomic -x` | ❌ W0 | ⬜ pending |
| 52-03-03 | 03 | 2 | INFRA-03 SC#3a | — | Partial-write corruption recovered (defense-in-depth) | unit | `pytest tests/agent/test_round_table_state.py::test_partial_write_recovery -x` | ❌ W0 | ⬜ pending |
| 52-03-04 | 03 | 2 | INFRA-03 SC#3b | — | Mid-turn crash recovered via stall detection | unit | `pytest tests/agent/test_round_table_state.py::test_mid_turn_crash_recovery -x` | ❌ W0 | ⬜ pending |
| 52-03-05 | 03 | 2 | INFRA-03 SC#3c | — | Orphaned session recovered on next read | unit | `pytest tests/agent/test_round_table_state.py::test_orphaned_session_recovery -x` | ❌ W0 | ⬜ pending |
| 52-04-01 | 04 | 3 | INFRA-04 SC#4 | — | Concurrent second `get_agent_opinion` rejected with 429 | async unit | `pytest tests/agent/test_round_table_executor.py::test_concurrent_submission_rejected -x` | ❌ W0 | ⬜ pending |
| 52-04-02 | 04 | 3 | INFRA-04 SC#4 | — | Single sequential submission proceeds + returns opinion | async unit | `pytest tests/agent/test_round_table_executor.py::test_sequential_submission_succeeds -x` | ❌ W0 | ⬜ pending |
| 52-04-03 | 04 | 3 | INFRA-04 SC#4 | — | 429 message contains `feedback-glm-overload-reduce-concurrency.md` substring | async unit | `pytest tests/agent/test_round_table_executor.py::test_429_message_cites_memory_md -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Test files to create before main implementation tasks:

- [ ] `tests/agent/test_registry_loader.py` — covers INFRA-01 (3 tests min: valid/malformed/name-mismatch)
- [ ] `tests/agent/test_round_table_state.py` — covers INFRA-03 (5 tests min: lifecycle + 3 crash recovery + atomic)
- [ ] `tests/agent/test_round_table_executor.py` — covers INFRA-04 (3 tests min: concurrent reject + sequential success + MEMORY.md citation substring)
- [ ] `tests/agent/test_mcp_serve_round_table.py` — covers INFRA-02 integration (4+ tests: agents_list / agent_describe / lifecycle round trip / memory stub)
- [ ] `tests/agent/fixtures/agents/test-coordinator.agent.yaml` — minimal valid synthetic agent fixture
- [ ] `tests/agent/fixtures/agents/malformed.agent.yaml` — invalid YAML fixture for SC#1 negative test
- [ ] `tests/agent/fixtures/agents/name-mismatch.agent.yaml` — YAML where `name:` field doesn't match filename stem
- [ ] Verify pytest-asyncio mode is `auto` in pyproject.toml (or mark async tests with `@pytest.mark.asyncio` explicitly)

*Existing infrastructure (pytest, pytest-asyncio, HERMES_HOME redirection via conftest `_hermetic_environment`) covers framework + isolation requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real GLM API call produces opinion (SC#2 full lifecycle) | INFRA-02 / SC#2 | Phase 52 uses mocked LLM; real GLM smoke test is Phase 56 VALIDATE scope | Run `scripts/run_screenplay_step3_roundtable.py` (Phase 53) end-to-end on real GLM in Phase 56 |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
