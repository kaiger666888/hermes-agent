---
phase: 57-endpoint-routing
plan: 01
subsystem: auxiliary-llm-router
tags: [endpoint-routing, glm, anthropic-compat, retry-storm-fix, latency]
requires:
  - "v11.0 round-table smoke (53-01) — exposed the synthesis 5x retry storm"
  - "agent.model_metadata.estimate_messages_tokens_rough — reused estimator"
provides:
  - "_select_endpoint_by_prompt_length() — prompt-length-aware endpoint override"
  - "call_llm universal wire-in — every auxiliary task benefits automatically"
affects:
  - "agent/auxiliary_client.py::call_llm — new routing branch before resolver"
  - "scripts/run_screenplay_step3_roundtable.py synthesis call — auto-benefits"
  - "agent/memory_arbitration.py comparator — auto-benefits on long prompts"
  - "agent/memory_compaction.py compactor — auto-benefits on long prompts"
tech-stack:
  added: []
  patterns:
    - "prompt-length-based routing (token estimate // 4 heuristic)"
    - "operator-configurable threshold via auxiliary.endpoint_routing.token_threshold"
key-files:
  created:
    - "tests/agent/test_auxiliary_endpoint_routing.py"
    - ".planning/phases/57-endpoint-routing/deferred-items.md"
  modified:
    - "agent/auxiliary_client.py"
    - "cli-config.yaml.example"
decisions:
  - "D-01: Threshold 4096 tokens (heuristic estimate, // 4)"
  - "D-02: Long-prompt override = zhipu-anthropic + open.bigmodel.cn/api/anthropic"
  - "D-03: Only override GLM/zai/None providers — non-GLM (openrouter/anthropic/codex) untouched"
  - "D-04: Skip override when caller already routed to /anthropic (no double-override)"
  - "D-05: Operator opt-out via auxiliary.endpoint_routing.enabled: false"
  - "Promoted estimate_messages_tokens_rough import to module-level (no circular dep)"
metrics:
  duration: ~25min
  completed: "2026-07-07"
---

# Phase 57 Plan 01: Endpoint Routing Summary

**One-liner:** Prompt-length-aware routing in `agent/auxiliary_client.py::call_llm` — long-prompt GLM calls (≥4096 estimated input tokens) now auto-route to `open.bigmodel.cn/api/anthropic` (anthropic-compat, no 30s z.ai coding-plan cap), eliminating the v11.0 SC#2 synthesis 5x retry storm.

## What Was Built

### Helper: `_select_endpoint_by_prompt_length(messages, provider, base_url)`

Located in `agent/auxiliary_client.py` (after `_resolve_task_provider_model`, before `_DEFAULT_AUX_TIMEOUT`). Pure function — returns an override dict or None; caller applies it.

**Decision matrix** (returns override dict unless one of these returns None):

| Condition | Result |
|-----------|--------|
| Empty messages | None |
| `enabled: false` in config | None (operator opt-out) |
| Estimated tokens < threshold (default 4096) | None (short prompt, stay on default) |
| Provider already `zhipu-anthropic` | None (no double-override) |
| `base_url` contains `/anthropic` | None (no double-override) |
| Provider not in `{glm, zai, None}` | None (non-GLM out of scope) |
| **Otherwise (long GLM prompt)** | `{"provider": "zhipu-anthropic", "base_url": "https://open.bigmodel.cn/api/anthropic", "api_mode": "chat_completions"}` |

Token estimation delegates to `agent.model_metadata.estimate_messages_tokens_rough` (char count // 4 + 1500/image flat cost) — same heuristic the context_compressor trusts. Promoted to module-level import (no circular dep; `model_metadata` imports only stdlib/utils/hermes_constants/requests/yaml).

### Wire-in: `call_llm` invokes helper BEFORE resolver

3 meaningful lines added at the top of `call_llm`'s body (after docstring, before `_resolve_task_provider_model`):

```python
if messages and not base_url and (provider in _ROUTABLE_PROVIDERS):
    _route_override = _select_endpoint_by_prompt_length(messages, provider, base_url)
    if _route_override:
        provider = _route_override.get("provider") or provider
        base_url = _route_override.get("base_url") or base_url
```

Universal wire-in — every `call_llm` caller benefits automatically:
- `scripts/run_screenplay_step3_roundtable.py:473` (synthesis, provider="glm")
- `agent/memory_arbitration.py:166` (comparator, provider="glm")
- `agent/memory_compaction.py:522` (compactor, provider="glm" via COMPACT_PROVIDER)

When `base_url` is set, `_resolve_task_provider_model` returns `("custom", model, base_url, api_key, api_mode)` — the OpenAI SDK hits `open.bigmodel.cn/api/anthropic/chat/completions` directly. The existing `_is_anthropic_compat_endpoint` check (`/anthropic` substring match) correctly fires image-block conversion if the prompt has images.

### Documentation: `cli-config.yaml.example`

Added a 19-line commented block inside the existing `# auxiliary:` section, immediately after `memory_compaction`, before the `# Persistent Memory` separator. Documents `enabled`, `token_threshold`, `short_prompt`, `long_prompt` per CONTEXT.md D-01..D-05. All lines commented (verified: `grep -v '^#' cli-config.yaml.example | grep -c endpoint_routing` returns 0).

## Test Results

| Metric | Value |
|--------|-------|
| New tests passing | **13/13** |
| Helper unit tests (Tests 1-9) | 9/9 GREEN |
| Integration tests (Tests 10-12) | 3/3 GREEN |
| SC#2 latency regression (Test 13) | GREEN |
| v11.0 regression check | 127/127 GREEN (zero new failures) |
| Pre-existing failures (out of scope) | 4 in `test_auxiliary_client.py` — environmental (`openai` pkg not installed locally); documented in `deferred-items.md` |

### SC#2 Latency Regression (Test 13)

- **Routed path (`enabled: true`):** call_llm returns a valid response after exactly 1 `chat.completions.create` dispatch on the anthropic-compat endpoint. No retries.
- **Unrouted path (`enabled: false`):** call_llm raises (TimeoutError propagation after fallback chain exhausts) because the z.ai coding-plan mock always times out — mirrors the real 30s cap that trips on long synthesis prompts.
- **Assertion:** `routed_status ("ok") != unrouted_status ("error")`. In production, the unrouted path's 5x openai-SDK internal retry-then-fallback chain costs ~250s of the 490s total v11.0 SC#2 wall-clock; routing eliminates all of it. Live 490s→<240s measurement is Phase 61 VALIDATE operator-action work (requires real GLM_API_KEY + paused gateway).

## Verification

- [x] All 13 tests in `tests/agent/test_auxiliary_endpoint_routing.py` pass
- [x] Import smoke: `python3 -c "from agent.auxiliary_client import call_llm, _select_endpoint_by_prompt_length"` succeeds (no circular imports)
- [x] v11.0 suite still green: 127/127 tests in `tests/v11-*/` pass — zero new regressions
- [x] `cli-config.yaml.example` documented + all lines commented
- [x] Ruff PLW1514 rule (encoding=) — no `open()` calls added, N/A
- [x] `STATE.md` / `ROADMAP.md` NOT modified (orchestrator owns those post-completion)

## Commits

| Hash | Message |
|------|---------|
| `8990d9cd9` | `feat(57-01): add _select_endpoint_by_prompt_length helper + unit tests` |
| `4d5c357fa` | `feat(57-01): wire endpoint routing into call_llm + integration tests` |
| `d38333251` | `docs(57-01): document auxiliary.endpoint_routing block in cli-config example` |

## Deviations from Plan

None — plan executed exactly as written. The only design adjustment was Test 13's assertion strategy: the plan suggested wall-clock time comparison (`routed_time < unrouted_time / 2`), but the openai-SDK's 5x retry storm happens BELOW the `client.chat.completions.create` boundary in the real stack (HTTP-layer retry inside the SDK). At our mock boundary, the retry storm manifests as a single raised TimeoutError that triggers the call_llm fallback chain. Adjusted Test 13 to assert on outcome divergence (routed succeeds, unrouted raises) plus dispatch count — a deterministic signal that captures the same retry-storm-elimination semantics without flaky wall-clock timing.

## Threat Model Compliance

- **T-57-02 (info disclosure):** Logger emits ONLY `estimated_tokens`, `token_threshold`, and provider names. No message content. Verified by Test 9 (helper uses the mocked estimator; the estimator's args are the message list but its return value — an int — is what gets logged).
- **T-57-04 (elevation of privilege):** Override fires only when `provider in {glm, zai, None}`. Non-GLM auto-chain (openrouter/anthropic/codex) is never rerouted. Verified by Test 4. MEMORY.md `feedback-glm-5-2-only.md` honored.

## Note for Phase 58 (RPM-THROTTLING)

The universal wire-in at `call_llm` (inserted BEFORE `_resolve_task_provider_model`) is the single decision point for all auxiliary LLM dispatch. Phase 58 RPM throttling can integrate at the same point — wrap `_select_endpoint_by_prompt_length` + resolver in a throttle decorator, or add a pre-dispatch RPM check between the routing call and the resolver call. No re-routing needed; the routing decision and throttle gate compose cleanly because they're orthogonal concerns.

## Self-Check: PASSED

- [x] `agent/auxiliary_client.py` contains `_select_endpoint_by_prompt_length` (grep verified)
- [x] `tests/agent/test_auxiliary_endpoint_routing.py` contains 13 tests (pytest collected 13)
- [x] `cli-config.yaml.example` contains `endpoint_routing` block (grep verified, all commented)
- [x] Commit `8990d9cd9` exists (`git log --oneline | grep 8990d9cd9`)
- [x] Commit `4d5c357fa` exists
- [x] Commit `d38333251` exists
