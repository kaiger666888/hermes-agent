---
phase: 54-eval-harness-1
plan: 03
subsystem: eval/bias-canary
tags: [eval, bias, canary, curator, hallucination, p5-mitigation, glm]
requires:
  - agent/auxiliary_client.call_llm (GLM dispatch — claim-check LLM)
  - agent/glm_concurrency_guard.acquire_glm_slot (serial lock)
  - agent/curator_audit.append_audit (sha256-chained audit log)
provides:
  - agent/curator_bias_canary (3 deterministic checks + LLM claim-support pass)
  - scripts/run_bias_canary.py (CLI with default mock + --smoke real-GLM modes)
  - tests/v11-bias-canary/fixtures/{5 bad + 1 good} synthetic memory records
affects:
  - cli-config.yaml.example (bias_canary_claim_check task registered)
tech-stack:
  added: []
  patterns:
    - lazy-import LLM proxy (mirrors agent/fitness_battery.py _call_llm)
    - async batch runner with stub-LLM injection for unit tests
    - fail-safe default on malformed LLM response (T-54-08)
    - deterministic bag-of-words embed_fn fallback (no LLM in unit tests)
key-files:
  created:
    - agent/curator_bias_canary.py
    - scripts/run_bias_canary.py
    - tests/v11-bias-canary/__init__.py
    - tests/v11-bias-canary/conftest.py
    - tests/v11-bias-canary/test_evidence_coverage.py
    - tests/v11-bias-canary/test_operator_diversity.py
    - tests/v11-bias-canary/test_bias_canary_integration.py
    - tests/v11-bias-canary/fixtures/bad_record_single_operator.json
    - tests/v11-bias-canary/fixtures/bad_record_low_evidence.json
    - tests/v11-bias-canary/fixtures/bad_record_unsupported_claim.json
    - tests/v11-bias-canary/fixtures/bad_record_low_confidence.json
    - tests/v11-bias-canary/fixtures/bad_record_no_operator_id.json
    - tests/v11-bias-canary/fixtures/good_record_multi_operator.json
  modified:
    - cli-config.yaml.example
decisions:
  - "#3 (CONTEXT.md) — separate module agent/curator_bias_canary.py, not curator.py edit"
  - "Deterministic bag-of-words embed_fn fallback (no LLM in unit tests, no external dep)"
  - "LLM claim-check is async; serial lock via acquire_glm_slot (sync context manager, safe in async because underlying call_llm is sync)"
  - "Smoke mode marked human_needed per CLAUDE.md operator-action-handoff; default uses mock"
metrics:
  duration: ~25min
  completed: 2026-07-07
  tasks: 2
  files_created: 13
  files_modified: 1
  tests_added: 24
---

# Phase 54 Plan 03: EVAL-03 Bias Canary Summary

Bias canary module gates P5 (curator failure modes) — flags hallucinated, single-operator-biased, low-confidence, or unsupported memory records before they reach the mem0 store. 3 deterministic checks + 1 GLM claim-support pass; 5 bad-record fixtures + 1 good-record fixture; acceptance threshold 4/5 caught (actual: 5/5).

## What Was Built

### Module: `agent/curator_bias_canary.py`

Three deterministic checks per PITFALLS §P5 + §4.5 safe-defaults:

1. **`_check_evidence_coverage`** (P5 mitigation 2) — cosine similarity ≥ 0.7 between new memory text and each cited evidence record's text. Below threshold → flag record index. Default embed_fn is a deterministic 16-dim bag-of-words hash vector (no LLM, no network) so unit tests stay reproducible without monkey-patching globals; production callers can swap in a real embedding model.

2. **`_check_operator_diversity`** (P5 mitigation 3) — requires ≥2 distinct operator IDs in `evidence_operator_ids`. Filters `None`/empty-string entries. Single-operator insights cannot drive automated memory writes.

3. **`_check_confidence_threshold`** (§4.5 safe-defaults) — curator confidence must be ≥ 0.3. Low certainty on a promotion candidate is suspicious.

Plus async **`run_bias_canary`** batch runner that adds a 4th check:

4. **`claim_support` LLM pass** — asks GLM (via `auxiliary_client.call_llm(task="bias_canary_claim_check", provider="glm")`) whether `record["text"]` is supported by `record["evidence_chain"]`. Wrapped in `glm_concurrency_guard.acquire_glm_slot` serial lock. Fail-safe: any dispatch error or malformed response defaults to `supported=False` (T-54-08 mitigation).

Aggregation: `CanaryReport` dataclass with `checks_passed` / `checks_failed` / `details` / `flagged`. Audit chain entry appended via `curator_audit.append_audit(action="auto_apply", eval_score={"bias_canary": {...}})` — sha256-chained, verified by `verify_chain()`.

### CLI: `scripts/run_bias_canary.py`

- `--fixtures <dir>` — load every `*.json` (sorted) as a memory record
- `--out <path>` — write JSON report
- `--smoke` — invoke REAL GLM (operator-action; never in CI)
- `--no-audit` — skip curator_audit chain append
- Default mode: deterministic checks + mocked LLM (returns supported=True); the unsupported_claim fixture is still caught by the deterministic evidence_coverage check
- Acceptance verdict: `pass` if 4 ≤ flagged_count ≤ 5 (for the canonical 6-fixture set)

### Fixtures: `tests/v11-bias-canary/fixtures/`

| Fixture | Triggered Check |
|---------|-----------------|
| `bad_record_single_operator.json` | operator_diversity (both IDs are op1) |
| `bad_record_low_evidence.json` | evidence_coverage (deep-sea text vs FLUX claim) |
| `bad_record_unsupported_claim.json` | claim_support (anamorphic-lens rule absent from evidence) |
| `bad_record_low_confidence.json` | confidence_threshold (confidence=0.15) |
| `bad_record_no_operator_id.json` | operator_diversity (empty list) |
| `good_record_multi_operator.json` | (passes all 4 checks — false-positive guard) |

### Tests: 24 total

- `test_evidence_coverage.py` — 8 tests (PASS/FAIL/empty/multi-record/threshold bounds)
- `test_operator_diversity.py` — 8 tests (distinct count/None filtering/min threshold bounds)
- `test_bias_canary_integration.py` — 8 tests (acceptance 4/5, per-record expectations, false positive, CLI subprocess, audit chain, --smoke help)

All 24 tests pass; `pytest tests/v11-bias-canary/ -x` is green.

## Acceptance Verification

```
$ python scripts/run_bias_canary.py --fixtures tests/v11-bias-canary/fixtures/ --out /tmp/canary_report.json
bias canary: 5/6 flagged → verdict=pass
```

- `flagged_count=5/6` (acceptance band: 4–5) → verdict=pass
- Good record (multi-operator) correctly NOT flagged (no false positive)
- All 5 bad records caught (1 above threshold — extra coverage, not a regression)

Plan grep verifications:
- `grep -c 'provider="glm"\|CANARY_PROVIDER' agent/curator_bias_canary.py` → 5 (≥1 required)
- `grep -c "acquire_glm_slot" agent/curator_bias_canary.py` → 5 (≥1 required)
- `grep -c "from agent.curator_bias_canary" agent/curator.py` → 0 (module is separate from curator main path, per CONTEXT.md decision #3)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Fixed stub-LLM factory pattern in CLI + tests**
- **Found during:** Task 2 integration test run
- **Issue:** Initial `_stub_claim_check(record)` returned an async function instead of being one; `await dispatch(record)` raised `object function can't be used in 'await' expression`. Same bug in `_mock_claim_check_factory(records)`.
- **Fix:** Made both stubs top-level async functions (`async def _stub_claim_check(record) -> tuple[bool, str]`) matching the `run_bias_canary` `claim_check_llm` contract: `Callable[[dict], Awaitable[tuple[bool, str]]]`.
- **Files modified:** `tests/v11-bias-canary/test_bias_canary_integration.py`, `scripts/run_bias_canary.py`
- **Commit:** 64bc6952f

**2. [Rule 1 — Bug] Fixed audit log path in integration test**
- **Found during:** Task 2 audit-chain test
- **Issue:** Test asserted audit log at `<HERMES_HOME>/curator_audit.jsonl`, but `curator_audit._audit_log_path()` resolves to `<HERMES_HOME>/skills/.audit/log.jsonl`.
- **Fix:** Updated test path expectation to match the v6.0 audit module's actual layout.
- **Files modified:** `tests/v11-bias-canary/test_bias_canary_integration.py`
- **Commit:** 64bc6952f

### Architectural Decisions

None — implementation followed CONTEXT.md decisions #3 (separate module) and #4 (use `auxiliary_client.call_llm` with `task="bias_canary_claim_check"`, `provider="glm"`) exactly.

## Threat Surface

No new threat surface introduced. The LLM network/auth path delegates entirely to `auxiliary_client.call_llm` (audited in v6.0). The serial lock + fail-safe defaults (T-54-08) are the only new mitigations and they reduce existing surface rather than adding new.

## Known Stubs

None. The default `_default_embed` is a real deterministic implementation (not a stub) — chosen per CONTEXT.md decision rationale "no external embedding lib (deterministic fallback)". Production swap-in via `embed_fn=` parameter is the intended extension point for Phase 56 VALIDATE.

## Operator Action Handoff

`scripts/run_bias_canary.py --smoke` invokes real GLM via `auxiliary_client.call_llm`. Operators run this manually with valid GLM credentials configured in `cli-config.yaml`. CI never invokes `--smoke`. Documented in CLI `--help` text and in `cli-config.yaml.example` comment block.

## TDD Gate Compliance

- **RED commit:** `7d1cf876d test(54-03): add failing bias canary unit tests (RED)` — 16 failing tests (module not yet created)
- **GREEN commit:** `a8ddecc1a feat(54-03): implement bias canary module — 3 deterministic checks + LLM pass` — all 16 unit tests pass
- **Integration commit:** `64bc6952f feat(54-03): add 6 fixtures + integration tests + CLI for bias canary` — 8 integration tests pass; full suite 24/24 green

## Self-Check: PASSED

Files verified present:
- `agent/curator_bias_canary.py` — FOUND
- `scripts/run_bias_canary.py` — FOUND (executable)
- `tests/v11-bias-canary/__init__.py` — FOUND
- `tests/v11-bias-canary/conftest.py` — FOUND
- `tests/v11-bias-canary/test_evidence_coverage.py` — FOUND
- `tests/v11-bias-canary/test_operator_diversity.py` — FOUND
- `tests/v11-bias-canary/test_bias_canary_integration.py` — FOUND
- 6 fixture JSON files — FOUND
- `cli-config.yaml.example` modified — FOUND (`bias_canary_claim_check` task registered)

Commits verified:
- `7d1cf876d` — FOUND
- `a8ddecc1a` — FOUND
- `64bc6952f` — FOUND

Test suite: 24/24 pass. CLI acceptance verdict: pass (5/6 flagged, in band [4,5]).
