---
phase: 58-rpm-throttling
plan: 02
subsystem: agent-round-table-budget
tags: [tpm-budget, round-table, token-tracking, cost-estimate, budget-events, glm-5-2]
requires:
  - 58-01-RPM-throttle
  - 52-INFRA-round-table-state
provides:
  - round_table_state.open_round_table(token_budget=...)
  - round_table_state.record_token_usage
  - round_table_state.append_event
  - round_table_state.submit_round_table_result receipt fields
  - round_table_executor.check_budget_before_turn
  - round_table_executor.record_panelist_tokens
  - screenplay-step3-driver budget wiring
affects:
  - agent/round_table_state.py
  - agent/round_table_executor.py
  - scripts/run_screenplay_step3_roundtable.py
  - cli-config.yaml.example
  - tests/agent/test_round_table_budget.py
tech-stack:
  added: []
  patterns:
    - per-state-file threading.Lock for atomic read-modify-write
    - threshold-event emission (warning < 2×, exceeded < 1×)
    - AST-walk source inspection (zero asyncio.sleep regression guard)
key-files:
  created:
    - tests/agent/test_round_table_budget.py
  modified:
    - agent/round_table_state.py
    - agent/round_table_executor.py
    - scripts/run_screenplay_step3_roundtable.py
    - cli-config.yaml.example
decisions:
  - "Hardcoded GLM-5.2 pricing (0.5 CNY/1M tokens, 7.2 USD/CNY rate) per MEMORY.md feedback-glm-5-2-only — config-driven pricing deferred to v13+"
  - "Per-state-file threading.Lock for record_token_usage/append_event serialization — protects against multi-process concurrent writes"
  - "Budget thresholds: <2× expected next call = warning (proceed), <1× = exceeded (abort) — per 58-CONTEXT.md decisions #5-#6"
  - "Receipt fields (tokensConsumed, costUsdEstimate) at top level of state dict — visibility for operator scripts + dashboard"
  - "Synthesis call uses higher expected_next_tokens (15K vs 5K for panelists) — avoids false-positive budget_exceeded at the final step"
metrics:
  duration: ~12 minutes
  completed: 2026-07-08
  tasks: 3
  files: 5
---

# Phase 58 Plan 02: Per-Round-Table TPM Budget Summary

Per-round-table token-per-meeting (TPM) ceiling with budget threshold events (warning/exceeded) and cost-estimate receipt — the SC#2 + SC#3 acceptance layer that caps GLM cost overrun on runaway panelist responses or retry fallbacks.

## What Was Built

### Layer 1 — State accounting (`agent/round_table_state.py`)
- `open_round_table` accepts optional keyword-only `token_budget: int | None = None` (default `DEFAULT_TOKEN_BUDGET = 100_000`); persists `tokenBudget` / `tokensConsumed=0` / `events=[]` in the state dict.
- `record_token_usage(state_path, tokens)` atomic read-modify-write under a per-state-file `threading.Lock` (registry keyed by `str(state_path)`). Lost-update-safe across concurrent threads/processes.
- `append_event(state_path, event)` atomic append to the `events` array; same lock primitive.
- `submit_round_table_result` seals `tokensConsumed` + `costUsdEstimate` at the top level of the state dict via the formula `(tokensConsumed / 1_000_000) * GLM_5_2_CNY_PER_1M_TOKENS / USD_CNY_RATE`.
- New module constants: `DEFAULT_TOKEN_BUDGET=100_000`, `GLM_5_2_CNY_PER_1M_TOKENS=0.5`, `USD_CNY_RATE=7.2`.

### Layer 2 — Budget decision (`agent/round_table_executor.py`)
- `check_budget_before_turn(state_path, expected_next_tokens=5000) -> bool` emits `budget_warning` event when `remaining < 2 × expected_next_tokens` (caller proceeds); emits `budget_exceeded` event and returns `False` when `remaining < expected_next_tokens` (caller MUST abort).
- `record_panelist_tokens(state_path, tokens)` thin delegation to `record_token_usage`.
- `DEFAULT_EXPECTED_NEXT_TOKENS = 5000` per v11.0 smoke baseline.

### Layer 3 — Driver wiring (`scripts/run_screenplay_step3_roundtable.py`)
- Pre-panelist `check_budget_before_turn(state_path, 5000)`; aborts with `mcp_serve.abort_round_table(reason='budget_exceeded')` and returns `{"error": "budget_exceeded"}` on threshold exhaustion.
- Post-panelist `record_panelist_tokens(state_path, total_tokens)` reading `auxiliary_client.get_last_call_usage()['total_tokens']`.
- Pre-synthesis `check_budget_before_turn(state_path, 15_000)` (synthesis is the heaviest call — higher threshold avoids false-positive abort).
- Post-synthesis token recording.

### Layer 4 — Operator docs (`cli-config.yaml.example`)
- `auxiliary.cost_estimate` block documenting the formula + hardcoded constants. Marked DOCUMENTATION ONLY for v12.0 (constants live in `agent/round_table_state.py`; config-driven pricing deferred to v13+ per 58-CONTEXT.md).

### Layer 5 — Test coverage (`tests/agent/test_round_table_budget.py`)
28 tests across 8 classes:
- `TestOpenWithTokenBudget` (2) — default vs explicit `token_budget`.
- `TestRecordTokenUsage` (3) — single, additive, zero-noop.
- `TestAppendEvent` (2) — single + ordered-multi.
- `TestRecordTokenUsageConcurrency` (1) — 100-thread no-lost-update proof.
- `TestSubmitReceipt` (3) — field presence, formula correctness (100K → 0.00694 USD), zero-cost.
- `TestBudgetExceededAbort` (1) — `abort_round_table(reason='budget_exceeded')`.
- `TestOpenIdempotenceWithBudget` (1) — duplicate open preserves existing budget.
- `TestModuleConstants` (3) — pin pricing constants.
- `TestCheckBudgetBeforeTurn` (3) — proceed/warning/exceeded transitions.
- `TestRecordPanelistTokens` (1) — delegation spy (avoids infinite recursion by capturing real fn).
- `TestDriverBudgetWiring` (3) — 9-panelist happy path (35K consumed), abort on budget=20K, events persistence.
- `TestRoundTableReceipt` (4) — v11 baseline ~0.00417 USD, zero-cost, budget-independence, top-level placement.
- `TestPhase58FullThrottlePipeline` (1) — end-to-end mocked smoke (SC#2 + SC#3): 35K consumed, 0.00243 USD, empty events at 100K budget, AST-walk verifies zero `asyncio.sleep` calls in driver source.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Test monkeypatch spy caused infinite recursion**
- **Found during:** Task 2 `test_delegates_to_state_record_token_usage`
- **Issue:** Initial spy implementation called `rts.record_token_usage(path, tokens)` to delegate to the "real" function — but `monkeypatch.setattr` had already replaced that attribute with the spy itself, causing unbounded recursion.
- **Fix:** Captured `real_record = rts.record_token_usage` BEFORE patching; spy delegates to the captured reference.
- **Files modified:** `tests/agent/test_round_table_budget.py`
- **Commit:** 02f37afae

**2. [Rule 1 - Bug] Substring check for asyncio.sleep false-positive on docstring**
- **Found during:** Task 3 `test_full_throttle_pipeline_mocked`
- **Issue:** Source-inspection assertion `"asyncio.sleep" not in src` matched the Phase 58 THROTTLE-01 explanatory docstring in the driver module (which mentions the removed sleep), not an actual call.
- **Fix:** Switched to AST walk — count `ast.Call` nodes with `func.value.id == "asyncio"` and `func.attr == "sleep"`. Comments/docstrings are not in the AST.
- **Files modified:** `tests/agent/test_round_table_budget.py`
- **Commit:** 19b820ab4

**3. [Rule 3 - Blocking] Mocked driver test saw `tokensConsumed == 0` initially**
- **Found during:** Task 2 `test_records_tokens_after_each_panelist`
- **Issue:** `_mock_mcp_and_aux` fixture's `aux.call_llm` lambda returned a stub response object but bypassed `_validate_llm_response` — the function that populates `_LAST_CALL_USAGE`. The fake `get_agent_opinion` similarly skipped the call_llm path, so `get_last_call_usage()` returned zeros and the driver's `record_panelist_tokens` was never invoked (guard `if _tokens > 0` skipped).
- **Fix:** Refactored the fixture to bump `_LAST_CALL_USAGE` directly inside both `_fake_opinion` and `_fake_call_llm`. Added a `TOKENS_PER_CALL = {"value": 3500}` mutable holder so individual tests can override without redefining fixtures.
- **Files modified:** `tests/agent/test_round_table_budget.py`
- **Commit:** 02f37afae

No architectural deviations (Rule 4). No deviations from the locked decisions in 58-CONTEXT.md.

## Auth Gates

None.

## Threat Mitigations Applied

- **T-58-02-01 (Tampering — CC-supplied token_budget):** Mitigation lives in the MCP tool layer per plan threat register; `round_table_state.open_round_table` is permissive (trusts internal callers). The MCP tool layer extension to clamp `[1000, 10_000_000]` is out of scope for THIS plan (documented in deferred-items.md).
- **T-58-02-02 (Repudiation — events lost on write failure):** Mitigated by construction — both `record_token_usage` and `append_event` use `utils.atomic_json_write` (temp+fsync+os.replace). No partial writes possible.
- **T-58-02-03 (DoS — adversarial token_budget=10^18):** Same as T-58-02-01 — MCP tool layer clamp is the mitigation point, deferred.
- **T-58-02-04 (Info Disclosure — cost reveals pricing):** Accepted per plan — operator-facing field by design.

## Known Stubs

None. Allotment of the budget wiring is end-to-end real (no placeholder values); the only "soft" contract is the MCP tool layer not yet passing `token_budget` from CC clients — that's out of scope per plan Step 3 note, and default 100K applies. Documented in the plan, not a stub.

## Threat Flags

None. No new network endpoints, auth paths, file access patterns, or schema-trust-boundary changes beyond what's already in the plan's `<threat_model>`.

## Self-Check: PASSED

All 6 modified/created files exist on disk. All 4 task commits (RED, GREEN state, GREEN executor+driver, GREEN receipt+docs) present in `git log`. Final `pytest tests/agent/test_round_table_budget.py` shows 28/28 GREEN in 1.08s. Phase 52 + 57 + 58-01 regression sweep (59 tests across `test_glm_throttle`, `test_round_table_state`, `test_round_table_executor`, `test_round_table_budget`) all GREEN — only pre-existing `openai`-SDK-missing env errors in `test_auxiliary_client.py` (4 tests), unrelated to this plan.
