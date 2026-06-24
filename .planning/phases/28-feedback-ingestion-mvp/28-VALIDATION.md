---
phase: 28
slug: feedback-ingestion-mvp
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-24
---

# Phase 28 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Feedback ingestion is the must-have MVP for v6.0 — every requirement must have automated test coverage to ship green.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 + pytest-timeout 2.4.0 (`[dev]` extra, `pyproject.toml`) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (testpaths=["tests"], 30s per-test timeout, parallel via `scripts/run_tests_parallel.py`) |
| **Quick run command** | `python -m pytest tests/agent/test_feedback_schema.py -x` |
| **Full suite command** | `python -m pytest tests/agent/test_feedback_*.py tests/hermes_cli/test_feedback_cli.py -x` |
| **Estimated runtime** | ~15 seconds (quick) / ~45 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/agent/test_feedback_schema.py -x`
- **After every plan wave:** Run `python -m pytest tests/agent/test_feedback_*.py tests/hermes_cli/test_feedback_cli.py -x`
- **Before `/gsd:verify-work`:** Full feedback suite green + `ruff check .` green + FOUND-08 byte-intact check passes
- **Max feedback latency:** 60 seconds (quick run + ruff)

---

## Per-Task Verification Map

> Tasks IDs are placeholders — the planner will assign final IDs (e.g. `28-01-01`). Test commands are stable.

| Task Pattern | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | Status |
|--------------|------|------|-------------|-----------------|-----------|-------------------|--------|
| FeedbackRecord schema | 01 | 1 | INGEST-04 | Rejects bad verdict / skill_id / ts / sha256 with field-level errors | unit | `python -m pytest tests/agent/test_feedback_schema.py -x` | ⬜ pending |
| OutputSnapshot capture | 01 | 1 | INGEST-05 | sha256 deterministic; captures model+params; handles all content shapes | unit | `python -m pytest tests/agent/test_feedback_snapshot.py -x` | ⬜ pending |
| `/feedback` slash command | 02 | 1 | INGEST-01 | Persists valid record; clear error when no prior skill output | unit + integration | `python -m pytest tests/hermes_cli/test_feedback_cli.py::test_slash_feedback_persists -x` | ⬜ pending |
| File watcher (kais inbox) | 03 | 2 | INGEST-02 | Ingests stable files; skips partial writes; path-traversal safe | integration | `python -m pytest tests/agent/test_feedback_ingest.py::test_watch_inbox_* -x` | ⬜ pending |
| JSONL batch import | 04 | 2 | INGEST-03 | Atomic — all-or-nothing; lists all errors; cold-start 10 records works | integration | `python -m pytest tests/agent/test_feedback_ingest.py::test_import_jsonl_* -x` | ⬜ pending |
| Cross-source schema parity | 04 | 2 | INGEST-04 | cli / kais_aigc / manual produce identical JSON | unit | `python -m pytest tests/agent/test_feedback_schema.py::test_source_enum_same_schema -x` | ⬜ pending |
| Ruff PLW1514 (encoding) | all | all | (convention) | Every `open()` in new modules passes `encoding="utf-8"` | lint | `ruff check agent/feedback_*.py hermes_cli/feedback.py` | ⬜ pending |
| FOUND-08 byte-intact | all | gate | (preservation) | No bundled SKILL.md or refs changed | smoke | `git diff --name-only v5.0 -- skills/movie-experts/ \| grep -v _eval \| grep -v _shared` (must be empty) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/agent/test_feedback_schema.py` — Pydantic validator tests (accept/reject cases for each field)
- [ ] `tests/agent/test_feedback_snapshot.py` — output_snapshot capture tests (sha256 determinism, param extraction, content-shape handling)
- [ ] `tests/agent/test_feedback_ingest.py` — write path + watcher polling (2-poll stability) + JSONL atomic import
- [ ] `tests/hermes_cli/test_feedback_cli.py` — CLI subcommand smoke tests + `/feedback` slash command integration
- [ ] `tests/fixtures/feedback/` — sample JSONL files (valid_10.jsonl, invalid_verdict.jsonl, invalid_skill.jsonl, cold_start.jsonl)

*No framework install needed — pytest already in `[dev]` extra. Existing infrastructure covers all phase requirements once Wave 0 test files are created.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Operator types `/feedback good "nice work"` in live REPL and sees confirmation message | INGEST-01 | Requires interactive REPL with prior skill output — cannot reproduce in pytest | 1) Launch `hermes chat`. 2) Invoke any movie-expert skill. 3) Type `/feedback good "test"`. 4) Verify confirmation + file exists at `~/.hermes/skills/.feedback/incoming/`. |
| `hermes feedback watch` foreground process picks up JSON dropped in `inbox-kais/` within 2 seconds | INGEST-02 | Requires live filesystem polling + external file drop | 1) Start `hermes feedback watch` in terminal A. 2) Drop valid JSON into `~/.hermes/skills/.feedback/inbox-kais/test.json` from terminal B. 3) Verify file moves to `processed-kais/` within 2s. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (5 new test files + fixtures dir)
- [ ] No watch-mode flags (pytest runs are one-shot `-x`)
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
