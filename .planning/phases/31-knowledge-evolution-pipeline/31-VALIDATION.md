---
phase: 31
slug: knowledge-evolution-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-24
---

# Phase 31 — Validation Strategy

> Per-phase validation contract. Knowledge Evolution closes the self-learning loop. Every requirement must have automated test coverage; FOUND-08 + additive-only are non-negotiable.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| **Config file** | `pyproject.toml` (testpaths=["tests"], 30s per-test timeout) |
| **Quick run command** | `python -m pytest tests/agent/evolution/ -x` |
| **Full suite command** | `python -m pytest tests/agent/evolution/ tests/hermes_cli/test_evolution_cli.py tests/agent/test_feedback*.py tests/hermes_cli/test_feedback_cli.py skills/movie-experts/_eval/tests/ -x` |
| **Estimated runtime** | ~25 seconds (quick) / ~90 seconds (full regression) |

---

## Sampling Rate

- **After every task commit:** `python -m pytest tests/agent/evolution/ -x`
- **After every plan wave:** Full regression (above)
- **Before `/gsd:verify-work`:** Full regression green + `ruff check .` green + FOUND-08 + runtime isolation
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task Pattern | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | Status |
|--------------|------|------|-------------|-----------------|-----------|-------------------|--------|
| LLM aggregation pass | 01 | 1 | EVOL-01 | Structured JSON output; evidence chain; rejects malformed LLM response | unit (mock LLM) | `python -m pytest tests/agent/evolution/test_aggregate.py -x` | ⬜ pending |
| Insight record schema | 01 | 1 | EVOL-01 | Pydantic validators; insight_id format; evidence_chain non-empty | unit | `python -m pytest tests/agent/evolution/test_aggregate.py::TestInsightSchema -x` | ⬜ pending |
| Diff generator (difflib-based, additive-only) | 01 | 1 | (EVOL-02 placeholder) | difflib.unified_diff; rejects deletion hunks | unit | `python -m pytest tests/agent/evolution/test_diff_generator.py -x` | ⬜ pending |
| Queue append/move/read | 01 | 1 | EVOL-03 | Atomic append via atomic_json_write; status transitions (pending→applied/rejected) | unit | `python -m pytest tests/agent/evolution/test_queue.py -x` | ⬜ pending |
| Atomic apply transaction | 01 | 1 | EVOL-04 | git apply --check → git apply → FOUND-08 → additive check → git add → git commit; revert on any failure | integration | `python -m pytest tests/agent/evolution/test_apply.py -x` | ⬜ pending |
| FOUND-08 per-patch check | 01 | 1 | SC-5 | expert_id + related_skills frontmatter byte-for-byte preserved; abort on violation | unit | `python -m pytest tests/agent/evolution/test_apply.py::TestFound08 -x` | ⬜ pending |
| Additive-only v4/v5 refs check | 01 | 1 | SC-6 | Reject any `-` line in snowflake-method.md / e-konte-format.md / scamper-variations.md / dreamina-cli-baseline.md / v86-pipeline-mapping.md patches | unit | `python -m pytest tests/agent/evolution/test_apply.py::TestAdditiveOnly -x` | ⬜ pending |
| Revert on failure | 01 | 1 | EVOL-04 | Working tree restored on FOUND-08/additive/git failure; exit non-zero | integration | `python -m pytest tests/agent/evolution/test_apply.py::TestRevertOnFailure -x` | ⬜ pending |
| Eval gate integration (EVOL-05) | 01 | 1 | EVOL-05 | Patch runs through gate.py; failed-gate patches logged to failed_gate.jsonl, never enter queue | integration | `python -m pytest tests/agent/evolution/test_queue.py::TestGateIntegration -x` | ⬜ pending |
| `hermes feedback evolve` CLI | 02 | 2 | EVOL-01 | Smoke: --help works; --skill flag required; --model override | integration | `python -m pytest tests/hermes_cli/test_evolution_cli.py::TestEvolveCmd -x` | ⬜ pending |
| `hermes feedback review-queue` CLI | 02 | 2 | EVOL-03 | Lists pending patches; filter by skill/status | integration | `python -m pytest tests/hermes_cli/test_evolution_cli.py::TestReviewQueueCmd -x` | ⬜ pending |
| `hermes feedback show-patch` CLI | 02 | 2 | EVOL-03 | Prints full diff + rationale + chain | integration | `python -m pytest tests/hermes_cli/test_evolution_cli.py::TestShowPatchCmd -x` | ⬜ pending |
| `hermes feedback approve` CLI | 02 | 2 | EVOL-04 | Non-bypassable prompt; --yes flag; atomic apply; commit message format | integration | `python -m pytest tests/hermes_cli/test_evolution_cli.py::TestApproveCmd -x` | ⬜ pending |
| `hermes feedback reject` CLI | 02 | 2 | EVOL-03 | Moves to rejected.jsonl with reason | integration | `python -m pytest tests/hermes_cli/test_evolution_cli.py::TestRejectCmd -x` | ⬜ pending |
| Hermes runtime isolation | all | gate | (preservation) | `agent/evolution/` not imported by runtime | smoke | `grep -rn "from agent.evolution\|import agent.evolution" agent/ hermes_cli/ tools/ gateway/ cli.py run_agent.py 2>/dev/null \| grep -v "tests/" \| wc -l` returns 0 | ⬜ pending |
| Ruff PLW1514 | all | all | (convention) | Every `open()` passes `encoding="utf-8"` | lint | `ruff check agent/evolution/ hermes_cli/feedback.py` | ⬜ pending |
| FOUND-08 byte-intact | all | gate | (preservation) | No bundled SKILL.md changes outside evolution apply | smoke | `git diff --name-only v5.0 -- skills/movie-experts/ \| grep -v _eval \| grep -v _shared \| wc -l` returns 0 (until first patch applied; then per-patch FOUND-08 check is in test_apply.py) | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `tests/agent/evolution/__init__.py` (NEW)
- [ ] `tests/agent/evolution/conftest.py` (NEW) — Fixtures: `evolution_env` (HERMES_HOME + git repo), `mock_llm_client`, `sample_feedback_records`, `sample_skill_content`
- [ ] `tests/agent/evolution/test_aggregate.py` (NEW)
- [ ] `tests/agent/evolution/test_diff_generator.py` (NEW)
- [ ] `tests/agent/evolution/test_queue.py` (NEW)
- [ ] `tests/agent/evolution/test_apply.py` (NEW)
- [ ] `tests/hermes_cli/test_evolution_cli.py` (NEW)
- [ ] `tests/fixtures/evolution/` — Sample insights, sample SKILL.md content, sample unified diffs (additive + violating)

*No framework install needed — pytest already in `[dev]` extra.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live `hermes feedback evolve --skill screenplay` produces meaningful insights on real feedback | EVOL-01 | Requires live LLM API + populated FeedbackStore | 1) Populate feedback via P28. 2) Run evolve command. 3) Inspect stdout + insights.jsonl. |
| `hermes feedback approve <id>` on real patch produces correct git commit | EVOL-04 | Requires live git working tree + LLM-generated patch | 1) Run evolve. 2) review-queue. 3) approve. 4) Verify git log shows commit with feedback IDs. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify
- [ ] Sampling continuity
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
