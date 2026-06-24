---
phase: 33
slug: observability-integration-close-out
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-25
---

# Phase 33 — Validation Strategy

> Per-phase validation contract. Close-out phase: stats CLI + architecture doc + skills-mapping + README/glossary + milestone-wide byte-intact checks.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + rich 14.3.3 (already pinned) |
| **Quick run command** | `python -m pytest tests/hermes_cli/test_curator_stats.py -x` |
| **Full suite command** | `python -m pytest tests/hermes_cli/test_curator_*.py tests/agent/test_curator*.py tests/agent/test_audit_log.py tests/agent/evolution/ -x` |
| **Estimated runtime** | ~20 seconds (quick) / ~120 seconds (full regression) |

---

## Sampling Rate

- **After every task commit:** Quick run
- **After every plan wave:** Full regression
- **Before `/gsd:verify-work`:** Full regression + SC-7/SC-8 milestone-wide byte-intact checks + Ruff
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task Pattern | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | Status |
|--------------|------|------|-------------|-----------------|-----------|-------------------|--------|
| `hermes curator stats <skill>` CLI | 01 | 1 | OBS-01 | Renders verdict buckets + patch history + eval trend; --json emits counts only | integration | `python -m pytest tests/hermes_cli/test_curator_stats.py::TestStatsPerSkill -x` | ⬜ pending |
| `hermes curator stats --all` CLI | 01 | 1 | OBS-02 | Top-N negative-feedback skills + score-uplift patches + zero-feedback list | integration | `python -m pytest tests/hermes_cli/test_curator_stats.py::TestStatsAll -x` | ⬜ pending |
| `hermes curator stats --by-source` CLI | 01 | 1 | OBS-03 | Verdict distribution grouped by source (cli/kais_aigc/manual) | integration | `python -m pytest tests/hermes_cli/test_curator_stats.py::TestStatsBySource -x` | ⬜ pending |
| `--runs N` flag | 01 | 1 | OBS-01 | Default 10; override via --runs; "need more data" footer when <N | unit | `python -m pytest tests/hermes_cli/test_curator_stats.py::TestRunsFlag -x` | ⬜ pending |
| `--json` flag (counts only) | 01 | 1 | OBS-01..03 | No correction text leakage; counts + verdicts only | unit | `python -m pytest tests/hermes_cli/test_curator_stats.py::TestJsonOutput -x` | ⬜ pending |
| Architecture doc creation | 02 | 2 | SC-4 | 7+ sections; ASCII data flow diagram; bilingual headers | doc check | `python -m pytest tests/hermes_cli/test_curator_stats.py::TestArchitectureDoc -x` | ⬜ pending |
| skills-mapping.yaml v6_ref_signoffs | 02 | 2 | SC-5 | Schema mirrors v5_ref_signoffs; verified_date present; license_status declared | schema | `python -m pytest tests/hermes_cli/test_curator_stats.py::TestSkillsMappingV6 -x` | ⬜ pending |
| README corpus tree update | 03 | 3 | SC-6 | New v6 ref listed in _shared/ block; alphabetical or appended per existing convention | doc check | `python -m pytest tests/hermes_cli/test_curator_stats.py::TestReadmeCorpusTree -x` | ⬜ pending |
| Glossary 4 bilingual entries | 03 | 3 | SC-6 | 4 H3 entries (Feedback Ingestion/Knowledge Evolution/Eval Gate/Curator Proposal); EN-first bilingual format | doc check | `python -m pytest tests/hermes_cli/test_curator_stats.py::TestGlossaryEntries -x` | ⬜ pending |
| SC-7 FOUND-08 milestone-wide | 03 | 3 | SC-7 | 0 bundled SKILL.md / refs changes vs v5.0 (excluding _eval/ + _shared/) | smoke | `git diff v5.0..HEAD -- skills/movie-experts/ \| grep -v _eval \| grep -v _shared \| wc -l` returns 0 | ⬜ pending |
| SC-8 v5/v4 refs byte-intact | 03 | 3 | SC-8 | snowflake/e-konte/scamper/dreamina-cli-baseline/v86-pipeline-mapping byte-intact | smoke | `git diff v5.0..HEAD -- skills/movie-experts/_shared/{snowflake-method,e-konte-format,scamper-variations,dreamina-cli-baseline,v86-pipeline-mapping}.md \| wc -l` returns 0 | ⬜ pending |
| Stats is read-only | 01 | 1 | (safety) | stats subcommand never mutates state | unit | `python -m pytest tests/hermes_cli/test_curator_stats.py::TestReadOnly -x` | ⬜ pending |
| Empty store friendly message | 01 | 1 | (UX) | When FeedbackStore empty: "no feedback yet" + suggest /feedback or import | unit | `python -m pytest tests/hermes_cli/test_curator_stats.py::TestEmptyStore -x` | ⬜ pending |
| Ruff PLW1514 | all | all | (convention) | Every `open()` passes `encoding="utf-8"` | lint | `ruff check hermes_cli/curator.py` | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `tests/hermes_cli/test_curator_stats.py` (NEW) — CLI smoke tests + doc/schema verification tests

*No framework install needed — pytest + rich already in stack.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live `hermes curator stats` on populated FeedbackStore renders meaningfully | OBS-01 | Requires live data + visual review of rich table | 1) Populate feedback. 2) `hermes curator stats screenplay`. 3) Visual review of dashboard. |
| Architecture doc reads cleanly end-to-end | SC-4 | Subjective doc quality | 1) Read `_shared/v6-feedback-loop-architecture.md`. 2) Verify clarity for new operator onboarding. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify
- [ ] Sampling continuity
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
