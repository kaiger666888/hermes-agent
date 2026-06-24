---
phase: 30
slug: eval-gate-reuse
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-24
---

# Phase 30 — Validation Strategy

> Per-phase validation contract. Eval Gate is offline developer tooling — every requirement must have automated test coverage so operators can trust the gate's verdict.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 (note: `_eval/tests/` is NOT in pyproject.toml `testpaths=["tests"]` — invoke explicitly) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (30s per-test timeout) |
| **Quick run command** | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py -x` |
| **Full suite command** | `python -m pytest skills/movie-experts/_eval/tests/ -x` |
| **Estimated runtime** | ~15 seconds (quick) / ~30 seconds (full) |

---

## Sampling Rate

- **After every task commit:** `python -m pytest skills/movie-experts/_eval/tests/test_gate.py -x`
- **After every plan wave:** `python -m pytest skills/movie-experts/_eval/tests/ -x`
- **Before `/gsd:verify-work`:** Full eval-suite green + `ruff check .` green + FOUND-08 byte-intact
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task Pattern | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | Status |
|--------------|------|------|-------------|-----------------|-----------|-------------------|--------|
| parse_judge_scores() extension to runner.py | 01 | 1 | GATE-02/04 | Numeric scores extracted from judge response; rejects malformed | unit | `python -m pytest skills/movie-experts/_eval/tests/test_runner.py -x` (regression) + `test_gate.py::TestParseJudgeScores -x` | ⬜ pending |
| gate.py main entrypoint | 01 | 1 | GATE-01 | Patch input parsed; baseline loaded; gate runs end-to-end | unit + integration | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestGateEntry -x` | ⬜ pending |
| Patch apply + revert mechanics | 01 | 1 | GATE-01 | `git apply --check` validates; revert restores bytes exactly | integration | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestPatchMechanics -x` | ⬜ pending |
| Mean δ threshold check (GATE-02) | 01 | 1 | GATE-02 | Reject if mean drop > 0.3; pass if within threshold | unit | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestMeanThreshold -x` | ⬜ pending |
| Per-prompt regression (GATE-04) | 01 | 1 | GATE-04 | Reject if ANY single prompt drops > 1.0 | unit | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestRegression -x` | ⬜ pending |
| gate_config.yaml loading | 01 | 1 | GATE-02/04 | Config loaded; CLI flags override; defaults documented | unit | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestConfig -x` | ⬜ pending |
| A/B position swap | 02 | 2 | GATE-03 | 2 rounds (baseline-first, candidate-first); judge blind to order | integration | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestPositionSwap -x` | ⬜ pending |
| Paired-t significance | 02 | 2 | GATE-03 | Paired t-test on per-prompt scores; t-table boolean significance (stdlib only) | unit | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestPairedT -x` | ⬜ pending |
| Reject log emit | 02 | 2 | GATE-02/04 | Reject log at `_eval/reports/<patch_id>.reject.json` with full delta breakdown | integration | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestRejectLog -x` | ⬜ pending |
| Exit code convention | 02 | 2 | GATE-02/04 | 0=pass, 1=fail_mean, 2=fail_regression, 3=inconclusive | unit | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestExitCodes -x` | ⬜ pending |
| --rebuild-baseline flag | 02 | 2 | GATE-01 | Forces baseline refresh; idempotent | integration | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestRebuildBaseline -x` | ⬜ pending |
| Multi-skill patch detection | 02 | 2 | (safety) | Detect patch touching multiple skills; warn + exit 3 without --multi-skill | unit | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestMultiSkill -x` | ⬜ pending |
| Hermes runtime isolation | all | gate | (preservation) | `_eval/` not imported by Hermes runtime | smoke | `grep -rn "from _eval\|import _eval" agent/ hermes_cli/ tools/ gateway/ cli.py 2>/dev/null \| wc -l` returns 0 | ⬜ pending |
| Ruff PLW1514 | all | all | (convention) | Every `open()` passes `encoding="utf-8"` | lint | `ruff check skills/movie-experts/_eval/gate.py skills/movie-experts/_eval/runner.py` | ⬜ pending |
| FOUND-08 byte-intact | all | gate | (preservation) | No bundled SKILL.md or refs changed | smoke | `git diff --name-only v5.0 -- skills/movie-experts/ | grep -v _eval | grep -v _shared | wc -l` returns 0 | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `skills/movie-experts/_eval/tests/test_gate.py` (NEW) — Gate unit + integration tests
- [ ] `skills/movie-experts/_eval/tests/fixtures/` — Synthetic patches (passing, failing-mean, failing-regression, multi-skill)
- [ ] `skills/movie-experts/_eval/gate_config.yaml.example` (NEW) — Config template

*No framework install needed — pytest already in `[dev]` extra.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live LLM judge call produces stable verdict on same patch | GATE-03 | Requires real LLM API calls (cost, latency) | 1) Set OPENAI_API_KEY. 2) Run gate on a synthetic patch. 3) Rerun. 4) Verify verdict stable. |
| `--rebuild-baseline` on live system completes in reasonable time | GATE-01 | Requires live LLM judge for full benchmark | 1) Run `python skills/movie-experts/_eval/gate.py --rebuild-baseline --skill screenplay`. 2) Verify completion + cache populated. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify
- [ ] Sampling continuity
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
