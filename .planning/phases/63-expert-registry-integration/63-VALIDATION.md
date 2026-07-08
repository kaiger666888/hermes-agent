---
phase: 63
slug: expert-registry-integration
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-08
---

# Phase 63 — Validation Strategy

> Per-phase validation contract for 21-agent registry load + missing-expert alarm + visual_executor round table smoke.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest==9.0.2` + `pytest-asyncio==1.3.0` + `pytest-timeout==2.4.0` (`[dev]` extra, existing) |
| **Config file** | `pyproject.toml` (existing — 30s per-test timeout per `addopts`) |
| **Quick run command** | `python -m pytest tests/agent/test_registry_loader.py -x` |
| **Full suite command** | `python -m pytest tests/agent/test_registry_loader.py tests/agent/test_phase63_round_table_smoke.py -x` |
| **Estimated runtime** | ~5 seconds (mock mode); +10s if `HERMES_PHASE63_LIVE_SMOKE=1` |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/agent/test_registry_loader.py -x` (<2s)
- **After every plan wave:** Run full Phase 63 suite (both test files)
- **Before `/gsd:verify-work`:** Full suite green + inline SC#1 verification (21-agent count against real `~/.hermes/agents/`)
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 63-01-01 | 01 (missing-expert alarm) | 0 | EXPERT-04 | T-52-04 (undeclared field — alarm reads only loaded data, no new YAML field injection surface) | `load_agent_registry_with_warnings()` returns tuple; missing-expert alarm emitted via `logger.warning` + structured return | unit | `python -m pytest tests/agent/test_registry_loader.py::TestMissingExpertAlarm -x` | ❌ W0 | ⬜ pending |
| 63-01-02 | 01 | 0 | EXPERT-04 | — | 15 required DAG experts hard-coded as `REQUIRED_DAG_EXPERTS` frozenset (v10.0 §6.2 verbatim) | unit | `python3 -c "from agent.registry_loader import REQUIRED_DAG_EXPERTS; assert isinstance(REQUIRED_DAG_EXPERTS, frozenset); assert len(REQUIRED_DAG_EXPERTS) == 15; assert 'screenplay' in REQUIRED_DAG_EXPERTS"` | ❌ W0 | ⬜ pending |
| 63-02-01 | 02 (canary test) | 1 | EXPERT-04 (SC#2) | — | Alarm fires when `screenplay` YAML absent from fixture HERMES_HOME | unit | `python -m pytest tests/agent/test_registry_loader.py::TestMissingExpertAlarm::test_alarm_fires_when_screenplay_missing -x` | ❌ W0 | ⬜ pending |
| 63-02-02 | 02 | 1 | EXPERT-04 (SC#2 silent path) | — | Alarm silent when all 15 required experts present | unit | `python -m pytest tests/agent/test_registry_loader.py::TestMissingExpertAlarm::test_alarm_silent_when_all_15_present -x` | ❌ W0 | ⬜ pending |
| 63-03-01 | 03 (round table smoke — mock) | 2 | EXPERT-05 (SC#3) | — | `visual_executor` round table produces non-empty synthesis (mock LLM) | integration | `python -m pytest tests/agent/test_phase63_round_table_smoke.py::TestVisualExecutorSmoke::test_round_table_produces_nonempty_opinion -x` | ❌ W0 | ⬜ pending |
| 63-03-02 | 03 | 2 | EXPERT-05 (SC#3 live, OPTIONAL) | — | visual_executor live GLM synthesis non-empty | manual-only | `HERMES_PHASE63_LIVE_SMOKE=1 GLM_API_KEY=... python -m pytest tests/agent/test_phase63_round_table_smoke.py::TestVisualExecutorSmoke::test_live_round_table -x` (operator handoff) | ❌ W0 | ⬜ pending |
| 63-04-01 | 04 (integration verification) | 2 | EXPERT-04 (SC#1) | — | 21 agents load via `load_agent_registry()` with zero errors | integration | `python3 -c "from agent.registry_loader import load_agent_registry; r=load_agent_registry(); assert len(r)==21, f'expected 21, got {len(r)}'"` | ✅ (inline) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/agent/test_registry_loader.py` — add `TestMissingExpertAlarm` class with 2 tests (fires + silent) + `_stage_required_experts` pytest helper
- [ ] `tests/agent/test_phase63_round_table_smoke.py` — new file, `TestVisualExecutorSmoke` class with 1 mock test + 1 opt-in live test
- [ ] `agent/registry_loader.py` — add `REQUIRED_DAG_EXPERTS` frozenset + `_check_required_experts` function + `load_agent_registry_with_warnings` sibling + integrate into existing `load_agent_registry`
- [ ] No framework install needed — pytest + pytest-asyncio already in `[dev]` extra

*Existing v11.0 infrastructure (`agent/registry_loader.py`, `agent/round_table_state.py`, `agent/round_table_executor.py`) is the integration target — Phase 63 extends, does not replace.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| visual_executor live GLM synthesis | EXPERT-05 (optional SC#3 live) | Live GLM call requires `GLM_API_KEY` env (stripped by conftest); also flaky under rate limits | Operator runs: `HERMES_PHASE63_LIVE_SMOKE=1 GLM_API_KEY=... python -m pytest tests/agent/test_phase63_round_table_smoke.py::TestVisualExecutorSmoke::test_live_round_table -x`. Verify non-empty `synthesis` field in round-table state file. Mock-mode test (63-03-01) is the SC#3 authoritative check; live is operator-confidence-only. |
| Missing-expert alarm surfacing in operator workflow | EXPERT-04 (qualitative) | `hermes orchestrator status` CLI not yet implemented (Phase 68); cannot verify operator visibility end-to-end | Operator reads `~/.hermes/logs/agent.log` after triggering registry load with missing YAML; confirms warning is human-readable |

*All structural / quantitative behaviors have automated verification. The live-GLM smoke is optional and does not block SC#3 (mock-mode is authoritative).*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (test files + registry_loader extension)
- [x] No watch-mode flags (pytest is single-shot)
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending planner/checker confirmation
