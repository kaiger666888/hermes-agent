---
phase: 54
slug: eval-harness-1
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-07
approved: 2026-07-07
---

# Phase 54 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 (strict mode) |
| **Config file** | `pyproject.toml:261` |
| **Quick run command** | `/data/workspace/hermes-agent/.venv/bin/python -m pytest tests/v11-fitness-battery/ tests/v11-latency-bench/ tests/v11-bias-canary/ -x` |
| **Full suite command** | `/data/workspace/hermes-agent/.venv/bin/python -m pytest tests/v11-fitness-battery/ tests/v11-latency-bench/ tests/v11-bias-canary/ tests/agent/ -x --timeout=30` |

---

## Sampling Rate

- **Per task commit:** Quick command
- **Per wave merge:** Full suite
- **Phase gate:** All EVAL-* tests pass + manual `scripts/run_fitness_battery.py` / `run_bias_canary.py` smoke (or `human_needed` if GLM unavailable)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 54-01-01 | 01 | 1 | EVAL-01 | unit | `pytest tests/v11-fitness-battery/ -x` | ⬜ pending |
| 54-01-02 | 01 | 1 | EVAL-01 | integration | `pytest tests/v11-fitness-battery/ -x` | ⬜ pending |
| 54-02-01 | 02 | 1 | EVAL-02 | unit | `pytest tests/v11-latency-bench/ -x` | ⬜ pending |
| 54-02-02 | 02 | 1 | EVAL-02 | integration | `pytest tests/v11-latency-bench/ -x` | ⬜ pending |
| 54-03-01 | 03 | 2 | EVAL-03 | unit | `pytest tests/v11-bias-canary/ -x` | ⬜ pending |
| 54-03-02 | 03 | 2 | EVAL-03 | integration | `pytest tests/v11-bias-canary/ -x` | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `tests/v11-fitness-battery/` (NEW directory + 8 scenario YAMLs + tests)
- [ ] `tests/v11-latency-bench/` (NEW directory + 3 seed fixtures + benchmark script)
- [ ] `tests/v11-bias-canary/` (NEW directory + 5 bad-record + 1 good-record fixtures + tests)
- [ ] `.planning/research/v11-poc-eval/` (NEW directory for spec docs + baseline reports)
- [ ] `scripts/run_fitness_battery.py` + `scripts/run_latency_benchmark.py` + `scripts/run_bias_canary.py`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real-GLM fitness battery judge + bias canary LLM | EVAL-01 + EVAL-03 | LLM-as-judge + claim-check need real GLM_API_KEY | Run scripts with real GLM. If unavailable, mark `human_needed` in VERIFICATION.md. |
| Live mem0 latency benchmark | EVAL-02 | Production mem0 backend latency depends on MEM0_API_KEY + network | Operator runs against configured mem0; PoC documents baseline using fixture-only store. |

---

## Validation Sign-Off

- [x] All tasks have automated verify
- [x] Sampling continuity
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true`

**Approval:** approved 2026-07-07
