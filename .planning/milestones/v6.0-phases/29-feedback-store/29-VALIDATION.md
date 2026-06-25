---
phase: 29
slug: feedback-store
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-24
---

# Phase 29 — Validation Strategy

> Per-phase validation contract. Feedback Store is the persistence/query/decay/dedup layer — every requirement must have automated test coverage.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 + pytest-timeout 2.4.0 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (testpaths=["tests"], 30s per-test timeout) |
| **Quick run command** | `python -m pytest tests/agent/test_feedback_store.py -x` |
| **Full suite command** | `python -m pytest tests/agent/test_feedback_store.py tests/agent/test_feedback_store_integration.py -x` |
| **Estimated runtime** | ~20 seconds (quick) / ~60 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/agent/test_feedback_store.py -x`
- **After every plan wave:** Run `python -m pytest tests/agent/test_feedback_store*.py tests/agent/test_feedback_ingest.py -x` (regression check — Phase 28 tests must still pass)
- **Before `/gsd:verify-work`:** Full feedback suite green + `ruff check .` green + FOUND-08 byte-intact
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task Pattern | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | Status |
|--------------|------|------|-------------|-----------------|-----------|-------------------|--------|
| FeedbackStore class | 01 | 1 | STORE-02 | Atomic index update; query filters correct | unit | `python -m pytest tests/agent/test_feedback_store.py::TestFeedbackStore -x` | ⬜ pending |
| record_feedback + bucket append | 01 | 1 | STORE-01 | Atomic bucket append (O(1)) + atomic index update | unit | `python -m pytest tests/agent/test_feedback_store.py::TestRecordFeedback -x` | ⬜ pending |
| query() with filters | 01 | 1 | STORE-02 | Returns FeedbackRecord list filtered by skill_id/source/verdict/since/until | unit | `python -m pytest tests/agent/test_feedback_store.py::TestQuery -x` | ⬜ pending |
| summary() per bucket | 01 | 1 | STORE-02 | Returns {count, weighted_count, first_ts, last_ts} per bucket | unit | `python -m pytest tests/agent/test_feedback_store.py::TestSummary -x` | ⬜ pending |
| Linear time-decay | 01 | 1 | STORE-03 | weight = max(0.1, 1.0 - age_days/180); computed at query time | unit | `python -m pytest tests/agent/test_feedback_store.py::TestDecay -x` | ⬜ pending |
| Lazy migration from Phase 28 incoming/ | 01 | 1 | (migration) | Idempotent; routes files to buckets/; archives originals | integration | `python -m pytest tests/agent/test_feedback_store.py::TestMigration -x` | ⬜ pending |
| Phase 28 write_feedback_record delegation | 02 | 2 | (integration) | Existing callers work unchanged; wrapper preserves signature | integration | `python -m pytest tests/agent/test_feedback_ingest.py -x` (regression) | ⬜ pending |
| Dedup: same sha256 + same verdict | 02 | 2 | STORE-04 | NOT double-counted in weighted_count; raw count still tracks | unit | `python -m pytest tests/agent/test_feedback_store.py::TestDedupSame -x` | ⬜ pending |
| Correction: same sha256 + different verdict | 02 | 2 | STORE-04 | Older weight=0, status=superseded; newer weight=active | unit | `python -m pytest tests/agent/test_feedback_store.py::TestCorrection -x` | ⬜ pending |
| `hermes feedback rebuild-index` CLI | 02 | 2 | STORE-02 | Repairs index from buckets/*.jsonl; idempotent | integration | `python -m pytest tests/hermes_cli/test_feedback_cli.py::TestRebuildIndex -x` | ⬜ pending |
| Index consistency invariant | 02 | 2 | STORE-02 | weighted_count <= count always; sum of bucket counts == total records | unit | `python -m pytest tests/agent/test_feedback_store.py::TestIndexConsistency -x` | ⬜ pending |
| Config: decay_window_days | 02 | 2 | STORE-03 | config.yaml override works; default 180 if missing | unit | `python -m pytest tests/agent/test_feedback_store.py::TestConfig -x` | ⬜ pending |
| Ruff PLW1514 | all | all | (convention) | Every `open()` passes `encoding="utf-8"` | lint | `ruff check agent/feedback_store.py hermes_cli/feedback.py` | ⬜ pending |
| FOUND-08 byte-intact | all | gate | (preservation) | No bundled SKILL.md or refs changed | smoke | `git diff --name-only v5.0 -- skills/movie-experts/ | grep -v _eval | grep -v _shared | wc -l` returns 0 | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `tests/agent/test_feedback_store.py` — Unit tests for FeedbackStore (record, query, summary, decay, migration, dedup, correction, index consistency, config)
- [ ] `tests/agent/test_feedback_store_integration.py` — Integration tests (Phase 28 delegation, end-to-end persistence)
- [ ] `tests/fixtures/feedback/store/` — Pre-populated `incoming/` and `buckets/` fixtures for migration testing

*No framework install needed — pytest already in `[dev]` extra.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `hermes feedback rebuild-index` runs cleanly on a live `~/.hermes/skills/.feedback/` with mixed Phase 28 + Phase 29 data | STORE-02 | Requires live operator data | 1) Populate `~/.hermes/skills/.feedback/` with mixed data. 2) Run `hermes feedback rebuild-index`. 3) Verify `index.json` reflects all records. |
| Time-decay shows correct weighted_count after 90+ days of operator inactivity | STORE-03 | Requires simulating months of aging | Unit tests cover the math; manual check is for operator UX (dashboard display in P33) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
