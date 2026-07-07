---
phase: 57-endpoint-routing
verified: 2026-07-07T15:40:51Z
status: human_needed
score: 2/3 must-have SCs fully verified (SC#2 deferred to Phase 61 per PLAN)
overrides_applied: 0
re_verification:
  previous_status: none
  note: "Initial verification (no prior VERIFICATION.md existed)"
human_verification:
  - test: "Live v11.0 SC#2 round-table smoke against real GLM backend"
    expected: "Total wall-clock latency drops from v11.0's measured 490s to <240s after Phase 57 routing + Phases 58-59 hardening. Synthesis call goes directly to open.bigmodel.cn/api/anthropic (no z.ai 30s cap, no 5x openai-SDK retry storm)."
    why_human: "Requires real GLM_API_KEY, gateway paused, and live network. Phase 57 Test 13 verifies the deterministic proxy signal (routed path: 1 dispatch + success; unrouted path: raises after fallback exhaustion). The live 490s to <240s wall-clock measurement is explicitly deferred to Phase 61 VALIDATE per ROADMAP Phase 57 SC#2 and PLAN <success_criteria> SC#2-preflight note."
---

# Phase 57: ENDPOINT-ROUTING Verification Report

**Phase Goal:** Route long-prompt LLM calls (synthesis, memory_compaction, memory_comparator) to `open.bigmodel.cn/api/anthropic` (anthropic-compat, no 30s cap); keep short-prompt calls (round_table_opinion panelists) on `z.ai/api/coding/paas/v4` (lower cost).
**Verified:** 2026-07-07T15:40:51Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth (ROADMAP SC) | Status | Evidence |
| --- | ------------------ | -------| -------- |
| 1   | `auxiliary_client.call_llm` auto-selects endpoint based on prompt token count; threshold configurable, default 4096 (SC#1) | VERIFIED | `agent/auxiliary_client.py:4896` defines `_select_endpoint_by_prompt_length`; wire-in at line 5324 (BEFORE `_resolve_task_provider_model` at line 5334); threshold read from `auxiliary.endpoint_routing.token_threshold` config (default 4096, lines 4939-4947); behavioral spot-check returns `None` for short prompts and `{"provider":"zhipu-anthropic","base_url":"https://open.bigmodel.cn/api/anthropic","api_mode":"chat_completions"}` for long prompts. Tests 1-9 PASS. |
| 2   | v11.0 SC#2 smoke latency drops from 490s to <240s (SC#2) | DEFERRED (human) | Live measurement requires real GLM_API_KEY + paused gateway; explicitly deferred to Phase 61 VALIDATE per ROADMAP Phase 57 SC#2 and PLAN `<success_criteria>` "SC#2-preflight" note. Proxy signal VERIFIED via Test 13: routed path completes in 1 dispatch with success status; unrouted path raises after fallback chain exhausts (z.ai 30s cap simulated). This eliminates the ~250s retry-storm component of the 490s wall-clock but the end-to-end production measurement needs Phase 61. |
| 3   | All v11.0 + v12.0 unit tests pass (SC#3) | VERIFIED | 259/259 PASS in 87.29s via the Phase 57 test gate: `tests/agent/test_auxiliary_endpoint_routing.py` (13) + 6 v11-* dirs (87) + 9 cross-cutting test files (159). Zero regressions. |

**Score:** 2/3 SCs fully verified; SC#2 live measurement deferred to Phase 61 (matches PLAN success_criteria design).

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `agent/auxiliary_client.py` | Helper + wire-in to call_llm | VERIFIED | `_select_endpoint_by_prompt_length` at line 4896 (substantive: 88 lines, handles 6 decision branches D-01..D-05); wire-in at line 5324 before resolver. Module-level import of `estimate_messages_tokens_rough` at line 103 (no circular dep — `model_metadata` imports only stdlib/utils/hermes_constants/requests/yaml). |
| `tests/agent/test_auxiliary_endpoint_routing.py` | Unit + integration tests, min 120 lines | VERIFIED | 416 lines, 13 tests in 2 classes (`TestSelectEndpointByPromptLength`, `TestCallLlmEndpointRouting`). All PASS. |
| `cli-config.yaml.example` | Documented `auxiliary.endpoint_routing` block | VERIFIED | 19-line block at lines 542-559 inside `# auxiliary:` section, between `memory_compaction` (line 537) and the `# ====` separator (line 561). All lines commented (`grep -v '^#'` returns 0 matches for endpoint_routing). Documents `enabled`, `token_threshold`, `short_prompt`, `long_prompt` per D-01..D-05. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `call_llm` | `_select_endpoint_by_prompt_length` | `if messages and not base_url and (provider in _ROUTABLE_PROVIDERS): _route_override = _select_endpoint_by_prompt_length(messages, provider, base_url)` (line 5324-5325) | WIRED | Helper invoked BEFORE `_resolve_task_provider_model` (line 5334). Override `provider` and `base_url` flow into resolver which returns `("custom", model, base_url, api_key, api_mode)` via the existing `if base_url:` branch at line 4851. Test 10 captures the actual `base_url` arg passed to `_get_cached_client` and asserts it contains `open.bigmodel.cn/api/anthropic`. |
| `_select_endpoint_by_prompt_length` | `auxiliary.endpoint_routing` config block | `_get_auxiliary_task_config("endpoint_routing")` (line 4932) | WIRED | Test 6 (custom threshold 8000), Test 7 (custom endpoints), Test 8 (`enabled: false`) all patch `_get_auxiliary_task_config` and confirm the helper reads the config correctly. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `call_llm` (integration Tests 10-12) | `captured["base_url"]` | `_get_cached_client(...)` patched to capture args; downstream of routing decision | Yes — patch captures the actual arg value flowing into the production client-construction path | FLOWING |
| `_select_endpoint_by_prompt_length` | `estimated_tokens` | `estimate_messages_tokens_rough(messages)` (line 4951) | Yes — Test 9 mocks the estimator and asserts it receives the actual messages list (not a stub) | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Import smoke (no circular imports) | `python3 -c "from agent.auxiliary_client import call_llm, _select_endpoint_by_prompt_length"` | `OK: _select_endpoint_by_prompt_length` | PASS |
| Routing decision matrix (4 branches) | Inline `python3` script invoking helper with stubbed config: short/long/non-glm/already-routed | `[None, {override}, None, None]` matches spec | PASS |
| Phase 57 test gate (SC#3) | `pytest tests/agent/test_auxiliary_endpoint_routing.py tests/v11-*/ tests/agent/test_phase52_contract.py ... 9 more files` | `259 passed in 87.29s` | PASS |
| Helper unit tests (Tests 1-9) | `pytest tests/agent/test_auxiliary_endpoint_routing.py::TestSelectEndpointByPromptLength` | 9/9 PASS | PASS |
| Integration tests (Tests 10-12) | `pytest tests/agent/test_auxiliary_endpoint_routing.py::TestCallLlmEndpointRouting -k "not sc2"` | 3/3 PASS | PASS |
| SC#2 latency regression (Test 13) | `pytest ...::test_sc2_latency_regression_routed_faster_than_unrouted` | 1/1 PASS — routed succeeds with 1 dispatch, unrouted raises after fallback chain | PASS |

### Probe Execution

Not applicable — Phase 57 declares no probe scripts. SC#2 wall-clock measurement is operator-action work for Phase 61 VALIDATE.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| ENDPOINT-01 | 57-01-PLAN.md | Long-prompt-aware endpoint routing (synthesis + compaction → anthropic-compat, panelists stay on coding plan, configurable threshold default 4096) | SATISFIED | All 3 deliverables present and verified: (1) `agent/auxiliary_client.py` modification (helper + wire-in); (2) unit tests covering both routing branches (Tests 3, 4, 10, 11, 12); (3) `cli-config.yaml.example` documentation block. SC#2 smoke target live measurement deferred to Phase 61 by PLAN design (SC#2-preflight only required for Phase 57). |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | - | - | - | No `TBD`/`FIXME`/`XXX` markers in any phase-57-modified file. No phase-57-related `TODO`/`HACK`/`PLACEHOLDER`. No empty handlers, no hardcoded empty data in routing code path. |

### Human Verification Required

### 1. Live v11.0 SC#2 round-table smoke (SC#2 production measurement)

**Test:** Run the v11.0 SC#2 round-table smoke script (`scripts/run_screenplay_step3_roundtable.py` synthesis path) against the real GLM backend after Phases 58-59 hardening is in place. Compare total wall-clock latency to v11.0's measured 490s baseline.
**Expected:** Total latency <240s. Synthesis call routes directly to `open.bigmodel.cn/api/anthropic` (no z.ai 30s cap, no 5x openai-SDK retry storm).
**Why human:** Requires real GLM_API_KEY, the gateway paused, and live network access. Phase 57's Test 13 verifies the deterministic proxy signal (routing eliminates the retry storm at the mocked boundary), but the end-to-end production measurement is operator-action work that ROADMAP Phase 57 SC#2 and the PLAN `<success_criteria>` both explicitly defer to Phase 61 VALIDATE.

### Gaps Summary

No automated gaps found. All 13 Phase 57 tests PASS, all 259 tests in the Phase 57 gate PASS, all 3 artifacts exist + are substantive + are wired, no anti-patterns detected. The single human-verification item (SC#2 live latency measurement) is by-design deferred to Phase 61 VALIDATE per the PLAN's `SC#2-preflight` designation and ROADMAP Phase 61 SC#2 ("production-smoke-report.md shows <240s round table").

Phase 57 ships the infrastructure (helper + wire-in + config + tests) that makes SC#2 possible in Phase 61. The routing logic itself is fully verified at the unit + integration level.

---

_Verified: 2026-07-07T15:40:51Z_
_Verifier: Claude (gsd-verifier)_
