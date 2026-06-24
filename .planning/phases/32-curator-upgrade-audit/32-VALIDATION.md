---
phase: 32
slug: curator-upgrade-audit
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-24
---

# Phase 32 — Validation Strategy

> Per-phase validation contract. Curator extension touches Hermes runtime — regression coverage is critical. Audit chain + EVOL-02 + auto-apply path each need robust tests.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| **Config file** | `pyproject.toml` (testpaths=["tests"], 30s per-test timeout) |
| **Quick run command** | `python -m pytest tests/agent/test_curator_feedback_scan.py tests/agent/test_audit_log.py tests/agent/evolution/test_evol02_generator.py -x` |
| **Full suite command** | `python -m pytest tests/agent/test_curator*.py tests/agent/test_audit_log.py tests/agent/evolution/ tests/hermes_cli/test_curator_cli.py tests/hermes_cli/test_evolution_cli.py tests/agent/test_feedback*.py tests/hermes_cli/test_feedback_cli.py -x` |
| **Estimated runtime** | ~30 seconds (quick) / ~120 seconds (full regression) |

---

## Sampling Rate

- **After every task commit:** `python -m pytest tests/agent/test_curator*.py tests/agent/test_audit_log.py tests/agent/evolution/test_evol02_generator.py -x`
- **After every plan wave:** Full regression suite
- **Before `/gsd:verify-work`:** Full regression + P31 TestNonBypassableHumanInLoop still green + FOUND-08 + runtime isolation
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task Pattern | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | Status |
|--------------|------|------|-------------|-----------------|-----------|-------------------|--------|
| SC-6 regression test (write FIRST) | 01 | 1 | SC-6 | Pre-v6 curator behavior preserved (inactivity transitions + consolidation) | regression | `python -m pytest tests/agent/test_curator_regression.py -x` | ⬜ pending |
| EVOL-02 generator | 01 | 1 | EVOL-02 | LLM structured instructions → difflib unified diff; bilingual EN+CN content | unit (mock LLM) | `python -m pytest tests/agent/evolution/test_evol02_generator.py -x` | ⬜ pending |
| Audit log + sha256 chain | 01 | 1 | CURATE-04 | Append-only; chain tamper-evident; verify catches breaks | unit | `python -m pytest tests/agent/test_audit_log.py -x` | ⬜ pending |
| Audit log verification | 01 | 1 | CURATE-04 | `audit-log --verify` walks chain, recomputes sha256, reports breaks | unit | `python -m pytest tests/agent/test_audit_log.py::TestVerifyChain -x` | ⬜ pending |
| Feedback threshold scan | 01 | 1 | CURATE-01 | Detects skills crossing threshold (≥3 neg across ≥2 sessions); skips below-threshold | unit (mock FeedbackStore) | `python -m pytest tests/agent/test_curator_feedback_scan.py -x` | ⬜ pending |
| Curator extension hook | 01 | 1 | CURATE-01 | run_curator_review feedback-scan phase appends after consolidation; pre-v6 unchanged | integration | `python -m pytest tests/agent/test_curator_regression.py tests/agent/test_curator_feedback_scan.py -x` | ⬜ pending |
| Curator invokes EVOL pipeline | 01 | 1 | CURATE-01, CURATE-02 | Proposes patches land in P31 queue; propose action logged | integration | `python -m pytest tests/agent/test_curator_feedback_scan.py::TestEvolInvocation -x` | ⬜ pending |
| `hermes curator queue` CLI | 02 | 2 | CURATE-03 | Lists pending (delegates to P31 review-queue) | integration | `python -m pytest tests/hermes_cli/test_curator_cli.py::TestQueueCmd -x` | ⬜ pending |
| `hermes curator approve/reject` CLI | 02 | 2 | CURATE-03 | Delegates to P31 approve/reject; logs to audit | integration | `python -m pytest tests/hermes_cli/test_curator_cli.py::TestApproveCmd tests/hermes_cli/test_curator_cli.py::TestRejectCmd -x` | ⬜ pending |
| `hermes curator audit-log` CLI | 02 | 2 | CURATE-04 | Filter by action/since/skill; --verify walks chain | integration | `python -m pytest tests/hermes_cli/test_curator_cli.py::TestAuditLogCmd -x` | ⬜ pending |
| CURATE-05 auto-apply path | 02 | 2 | CURATE-05 | Two-signal confidence; agent-created only; bundled NEVER auto; default OFF | integration | `python -m pytest tests/hermes_cli/test_curator_cli.py::TestAutoApply -x` | ⬜ pending |
| P31 TestNonBypassableHumanInLoop regression | all | gate | (preservation) | Auto-apply routes through _cmd_approve (or AST test amended) | structural | `python -m pytest tests/hermes_cli/test_evolution_cli.py::TestNonBypassableHumanInLoop -x` | ⬜ pending |
| Runtime isolation preserved | all | gate | (preservation) | agent/evolution/ not imported by runtime (curator_audit.py lives at agent/, not agent/evolution/) | smoke | `grep -rn "from agent.evolution\|import agent.evolution" agent/curator.py agent/curator_audit.py 2>/dev/null \| wc -l` returns 0 (curator imports curator_audit, not evolution) | ⬜ pending |
| Ruff PLW1514 | all | all | (convention) | Every `open()` passes `encoding="utf-8"` | lint | `ruff check agent/curator.py agent/curator_audit.py agent/evolution/evol02_generator.py hermes_cli/curator.py` | ⬜ pending |
| FOUND-08 byte-intact | all | gate | (preservation) | No bundled SKILL.md changes outside P31 approved evolution patches | smoke | `git diff --name-only v5.0 -- skills/movie-experts/ \| grep -v _eval \| grep -v _shared \| wc -l` returns 0 (until first curator-proposed patch applied via approve) | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `tests/agent/test_curator_regression.py` (NEW) — Pre-v6 curator behavior regression tests (SC-6). Write FIRST.
- [ ] `tests/agent/test_curator_feedback_scan.py` (NEW)
- [ ] `tests/agent/test_audit_log.py` (NEW)
- [ ] `tests/agent/evolution/test_evol02_generator.py` (NEW)
- [ ] `tests/hermes_cli/test_curator_cli.py` (NEW)
- [ ] `tests/fixtures/curator/` — Sample feedback scenarios, sample audit chains (valid + tampered)

*No framework install needed — pytest already in `[dev]` extra.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live `hermes curator queue` on populated FeedbackStore + EVOL pipeline | CURATE-01 | Requires live LLM + populated feedback | 1) Populate feedback via P28. 2) Wait for curator review cycle. 3) `hermes curator queue`. 4) Verify proposed patches listed. |
| Live `hermes curator audit-log --verify` on operator-modified log | CURATE-04 | Requires manual log editing | 1) Populate audit log via approve flow. 2) Manually edit one entry. 3) `hermes curator audit-log --verify`. 4) Verify break reported. |
| Auto-apply path on agent-created skill with high-confidence patch | CURATE-05 | Requires live LLM + agent-created skill + opt-in config | 1) Enable `feedback.curator.auto_apply_enabled: true`. 2) Trigger EVOL on agent-created skill. 3) Verify auto_apply audit entry + git commit. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify
- [ ] Sampling continuity
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
