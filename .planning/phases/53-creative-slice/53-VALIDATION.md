---
phase: 53
slug: creative-slice
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-07
approved: 2026-07-07
---

# Phase 53 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 (strict mode — NOT auto; `@pytest.mark.asyncio` explicit) |
| **Config file** | `pyproject.toml:261` (`addopts` includes `-ra --strict-markers --timeout=30`) |
| **Quick run command** | `/data/workspace/hermes-agent/.venv/bin/python -m pytest tests/agent/test_transform_skill_to_agent.py tests/agent/test_memory_arbitration.py tests/agent/test_conflict_log_writer.py -x` |
| **Full suite command** | `/data/workspace/hermes-agent/.venv/bin/python -m pytest tests/agent/ -x --timeout=30` |
| **Estimated runtime** | ~20 seconds for quick; ~90 seconds for full agent suite |

---

## Sampling Rate

- **After every task commit:** Run quick command (transform + arbitration + conflict log tests)
- **After every plan wave:** Run full agent test suite
- **Before `/gsd:verify-work`:** Full suite green + manual `python scripts/run_screenplay_step3_roundtable.py --smoke` on real GLM (or `human_needed` flag if GLM unavailable)
- **Max feedback latency:** 30 seconds (per-test timeout in pyproject.toml)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 53-01-01 | 01 | 1 | MIGR-01 (Wave 0) | — | Phase 52 contract imports resolve + stub returns | unit | `pytest tests/agent/test_phase52_contract.py -x` | ❌ W0 | ⬜ pending |
| 53-01-02 | 01 | 1 | MIGR-01 | — | 9 YAMLs validate against agents-schema.yaml | unit | `pytest tests/agent/test_transform_skill_to_agent.py::test_9_yamls_validate -x` | ❌ W0 | ⬜ pending |
| 53-01-03 | 01 | 1 | MIGR-01 | — | screenplay lineage.transform_notes contains HOOK-09 invariant | unit | `pytest tests/agent/test_transform_skill_to_agent.py::test_screenplay_transform_preserves_HOOK_09 -x` | ❌ W0 | ⬜ pending |
| 53-01-04 | 01 | 1 | MIGR-01 | — | SHA-256 LF-normalized | unit | `pytest tests/agent/test_transform_skill_to_agent.py::test_skill_sha256_lf_normalized -x` | ❌ W0 | ⬜ pending |
| 53-02-01 | 02 | 1 | CREATIVE-02 | — | COMPARATOR_PROMPT_TEMPLATE verbatim from §3.2 | unit | `pytest tests/agent/test_memory_arbitration.py::test_comparator_prompt_verbatim -x` | ❌ W0 | ⬜ pending |
| 53-02-02 | 02 | 1 | CREATIVE-02 | — | 2-conflict scenario produces correct arbitration | unit | `pytest tests/agent/test_memory_arbitration.py::test_2conflict_arbitration -x` | ❌ W0 | ⬜ pending |
| 53-02-03 | 02 | 1 | CREATIVE-02 | — | scope precedence session > project > global | unit | `pytest tests/agent/test_memory_arbitration.py::test_scope_precedence -x` | ❌ W0 | ⬜ pending |
| 53-02-04 | 02 | 1 | CREATIVE-02 | — | confidence tie-break (<0.05 Δ → deferred-to-operator) | unit | `pytest tests/agent/test_memory_arbitration.py::test_confidence_tiebreak -x` | ❌ W0 | ⬜ pending |
| 53-02-05 | 02 | 1 | CREATIVE-02 | — | conflicts.jsonl append + atomic semantics | unit | `pytest tests/agent/test_conflict_log_writer.py -x` | ❌ W0 | ⬜ pending |
| 53-02-06 | 02 | 1 | CREATIVE-02 | — | Phase 52 _scoped_agent_id primitive preserved verbatim | unit | `pytest tests/agent/test_memory_arbitration.py::test_phase52_scoped_agent_id_unchanged -x` | ❌ W0 | ⬜ pending |
| 53-03-01 | 03 | 2 | CREATIVE-01 | — | get_agent_opinion swaps placeholder → real call_llm with provider="glm" | unit | `pytest tests/agent/test_run_screenplay_step3.py::test_get_agent_opinion_uses_real_llm -x` | ❌ W1 | ⬜ pending |
| 53-03-02 | 03 | 2 | CREATIVE-01 | — | round_table_open → 9 get_agent_opinion → submit (mocked GLM) | integration | `pytest tests/agent/test_run_screenplay_step3.py::test_lifecycle_9_agents -x` | ❌ W1 | ⬜ pending |
| 53-03-03 | 03 | 2 | CREATIVE-01 | — | HOOK-09 schema validation on output | integration | `pytest tests/agent/test_run_screenplay_step3.py::test_step3_output_validates -x` | ❌ W1 | ⬜ pending |
| 53-03-04 | 03 | 2 | CREATIVE-01 | — | T-52-15 try/finally lock contract preserved | unit | `pytest tests/agent/test_run_screenplay_step3.py::test_t52_15_lock_contract_preserved -x` | ❌ W1 | ⬜ pending |
| 53-03-05 | 03 | 2 | CREATIVE-01 | — | strict serial (no asyncio.gather) | unit | `pytest tests/agent/test_run_screenplay_step3.py::test_no_asyncio_gather -x` | ❌ W1 | ⬜ pending |
| 53-03-06 | 03 | 2 | CREATIVE-01 (SC#2 smoke) | — | real GLM smoke test, <30s latency | manual-only | `python scripts/run_screenplay_step3_roundtable.py --smoke` | ❌ W1 (script) / VERIFICATION.md (result) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Test files + fixtures to create before main implementation tasks:

- [ ] `tests/agent/test_phase52_contract.py` — proves Phase 52 imports resolve (Wave 0 smoke)
- [ ] `tests/agent/test_transform_skill_to_agent.py` — 9 sub-tests for MIGR-01
- [ ] `tests/agent/test_memory_arbitration.py` — 7+ tests for CREATIVE-02 (5-mechanism + tie-break + Phase 52 preservation)
- [ ] `tests/agent/test_conflict_log_writer.py` — JSONL append + atomic semantics
- [ ] `tests/agent/test_run_screenplay_step3.py` — 5+ tests for CREATIVE-01 (mocked GLM)
- [ ] `tests/fixtures/screenplay-step3-schema.json` — JSON Schema for HOOK-09 emotion_curve marker contract
- [ ] `tests/fixtures/storykernel-sample.json` — synthetic Step 1 output (input to driver)
- [ ] `tests/fixtures/memory-conflict-2conflict.json` — 2-conflict scenario fixture
- [ ] `tests/fixtures/transform-audit-log.json` — expected transform log structure
- [ ] Verify pytest-asyncio markers explicit (`@pytest.mark.asyncio`) — mode is strict NOT auto

*Existing infrastructure (pytest, pytest-asyncio, HERMES_HOME redirection via conftest `_hermetic_environment`) covers framework + isolation requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real GLM API smoke test (SC#2 latency < 30s) | CREATIVE-01 | Requires GLM_API_KEY; provider may be unavailable in CI | Run `python scripts/run_screenplay_step3_roundtable.py --smoke` against real GLM. If GLM unavailable, mark `human_needed` in VERIFICATION.md per autonomous workflow (#3309 end-of-phase mode). |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-07 (plan-checker initially flagged missing VALIDATION.md as blocker; created inline from RESEARCH § Validation Architecture content; all task-level content compliant)
