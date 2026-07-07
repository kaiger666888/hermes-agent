---
phase: 55
slug: eval-harness-2
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-07
approved: 2026-07-07
---

# Phase 55 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 (strict mode) |
| **Quick run** | `.venv/bin/python -m pytest tests/v11-compaction/ tests/v11-schema-migration/ tests/agent/test_curator.py -x` |
| **Full suite** | `.venv/bin/python -m pytest tests/v11-compaction/ tests/v11-schema-migration/ tests/v11-fitness-battery/ tests/v11-latency-bench/ tests/v11-bias-canary/ tests/agent/ -x --timeout=30` |

---

## Sampling Rate

- **Per task commit:** Quick command
- **Per wave merge:** Full suite
- **Phase gate:** All EVAL-* tests pass + manual smoke (or `human_needed`)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Command | Status |
|---------|------|------|-------------|-----------|---------|--------|
| 55-01-01 | 01 | 1 | EVAL-04 | unit | `pytest tests/v11-compaction/ -x` | ⬜ |
| 55-01-02 | 01 | 1 | EVAL-04 | unit | `pytest tests/v11-compaction/ -x` | ⬜ |
| 55-02-01 | 02 | 1 | EVAL-05 | doc | `test -f .planning/research/v11-poc-eval/threshold-tuning.md` | ⬜ |
| 55-02-02 | 02 | 1 | EVAL-05 | schema | `grep "memory.thresholds" .planning/research/v10-orchestrator-design/agents-schema.yaml` | ⬜ |
| 55-03-01 | 03 | 1 | EVAL-06 | unit | `pytest tests/agent/test_curator.py -x` | ⬜ |
| 55-03-02 | 03 | 1 | EVAL-06 | AST-walk | `pytest tests/agent/test_curator_dry_run_invariant.py -x` | ⬜ |
| 55-04-01 | 04 | 2 | EVAL-07 | unit | `pytest tests/v11-schema-migration/ -x` | ⬜ |
| 55-04-02 | 04 | 2 | EVAL-07 | integration | `pytest tests/v11-schema-migration/ -x` | ⬜ |
| 55-04-03 | 04 | 2 | EVAL-07 + EVAL-06 | P14 | `pytest tests/v11-schema-migration/test_zero_silent_drops.py -x` | ⬜ |

---

## Wave 0 Requirements

- [ ] `tests/v11-compaction/` (NEW dir + 600-record fixture)
- [ ] `tests/v11-schema-migration/` (NEW dir + 30-record fixture across 3 buckets)
- [ ] `tests/agent/test_curator_dry_run_invariant.py` (NEW AST-walk test)
- [ ] `.planning/research/v11-poc-eval/threshold-tuning.md` (NEW doc)
- [ ] `.planning/research/v11-poc-eval/migration-dry-run-format.md` (NEW doc)
- [ ] `scripts/migrate_v6_feedback_to_memory_schema.py` (NEW script)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real GLM compaction summary | EVAL-04 | LLM summarization needs GLM_API_KEY | Operator runs compaction with real GLM. Mark `human_needed` if unavailable. |

---

**Approval:** approved 2026-07-07
