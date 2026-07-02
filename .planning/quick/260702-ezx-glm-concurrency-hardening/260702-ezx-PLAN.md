---
phase: quick-260702-ezx
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - agent/glm_concurrency_guard.py
  - agent/conversation_loop.py
  - agent/retry_utils.py
  - tests/test_glm_concurrency_guard.py
  - tests/agent/test_retry_utils_overloaded.py
  - cli-config.yaml.example
autonomous: true
requirements: [GLM-HARDEN-A, GLM-HARDEN-B, GLM-HARDEN-C]
user_setup: []

must_haves:
  truths:
    - "When N>=4 in-flight requests are already hitting *.bigmodel.cn, the N+1th caller BLOCKS instead of firing another HTTP request that would collide with GLM's capacity"
    - "A 1305/overloaded_error response triggers a 30s-base / 600s-cap jittered backoff instead of the default 0.5s/32s path, so the retry budget is not exhausted by 3 sub-minute retries"
    - "Three consecutive 1305 overloaded failures abort the turn cleanly with a human-readable 'GLM model overloaded, please retry in N minutes' message instead of burning 10 retries"
    - "Non-overloaded failures (rate_limit, timeout, server_error) keep the full 10-retry budget and the existing 0.5s/32s backoff"
    - "No credential-pool, model-switch, fallback-provider, or OpenRouter changes ship with this commit"
  artifacts:
    - path: "agent/glm_concurrency_guard.py"
      provides: "Process-wide host-keyed semaphore for *.bigmodel.cn concurrency throttling; context manager API + host matcher"
      exports: ["acquire_glm_slot", "glm_concurrency_slot", "get_glm_semaphore", "is_glm_endpoint"]
      min_lines: 80
    - path: "agent/retry_utils.py"
      provides: "Extended jittered_backoff with overloaded-specific preset; new jittered_backoff_overloaded() thin wrapper"
      exports: ["jittered_backoff", "jittered_backoff_overloaded"]
    - path: "tests/test_glm_concurrency_guard.py"
      provides: "Unit tests for semaphore acquire/release, host matching, configurable N"
      min_lines: 60
    - path: "tests/agent/test_retry_utils_overloaded.py"
      provides: "Unit tests for overloaded backoff preset (base=30, cap=600) vs default"
      min_lines: 30
  key_links:
    - from: "agent/conversation_loop.py (line ~1119, run_llm_execution_middleware call)"
      to: "agent/glm_concurrency_guard.acquire_glm_slot"
      via: "context manager wrapping _perform_api_call"
      pattern: "with acquire_glm_slot\\(agent\\.base_url\\):"
    - from: "agent/conversation_loop.py (line ~3488, jittered_backoff call site)"
      to: "agent/retry_utils.jittered_backoff_overloaded"
      via: "branch on classified.reason == FailoverReason.overloaded"
      pattern: "jittered_backoff_overloaded|jittered_backoff\\(.*base_delay=0\\.5"
    - from: "agent/conversation_loop.py (retry loop top, near _retry state init)"
      to: "consecutive overloaded counter on _retry namespace"
      via: "increment on FailoverReason.overloaded; reset on any other outcome; break at >=3"
      pattern: "consecutive_overloaded"
---

<objective>
Mitigate recurring open.bigmodel.cn 1305 overloaded_error / 1302 rate_limit failures (today's incident 2026-07-02 10:05-10:25 CST, ~400 retries) by shipping three atomic, complementary hardening changes in ONE commit:

A. Process-wide concurrency guard keyed by host (caps in-flight *.bigmodel.cn requests at N=4, configurable).
B. 1305-specific long-jitter backoff (30s base / 600s cap) so retries actually span the typical 1305 recovery window instead of exhausting the budget in <2 minutes.
C. Early abort after 3 consecutive 1305 failures, surfacing a clear "GLM overloaded, retry in N minutes" message instead of churning through all 10 retries.

Constraint (user-confirmed, NON-NEGOTIABLE): single endpoint (open.bigmodel.cn), single model (glm-5.2), no extra cost. NO OpenRouter, NO model fallback, NO credential pool changes, NO title_generator/curator disabling.

Purpose: Stop the recurring "model provider failed after retries" outages during peak hours while staying inside the locked constraints.
Output: New module agent/glm_concurrency_guard.py, modified conversation_loop.py + retry_utils.py, two new test files, one example-config addition — single atomic commit.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.planning/STATE.md

# Exact integration points in current code (READ BEFORE EDITING):

<interfaces>
<!-- Extracted from current codebase — executor does NOT need to grep again. -->

From agent/retry_utils.py (current jittered_backoff signature — line 19):
```python
def jittered_backoff(
    attempt: int,
    *,
    base_delay: float = 5.0,
    max_delay: float = 120.0,
    jitter_ratio: float = 0.5,
) -> float: ...
```
NOTE: Two existing call sites use different defaults:
- agent/conversation_loop.py:1399  →  base=5.0, max=120.0  (invalid-response path — leave alone)
- agent/conversation_loop.py:3491  →  base=0.5, max=32.0, jitter=0.25  (API-error path — THIS is the one to branch)

From agent/conversation_loop.py (the API-call site, line 1110):
```python
def _perform_api_call(next_api_kwargs):
    if _use_streaming:
        return agent._interruptible_api_call(
            next_api_kwargs, on_first_delta=_stop_spinner
        )
    return agent._interruptible_api_call(next_api_kwargs)

response = run_llm_execution_middleware(
    api_kwargs, _perform_api_call, ...
)
```
This is the SINGLE chokepoint for the main conversation loop's API calls.
delegate_task subagents spawn their own AIAgent which runs through this same
loop, so they are covered by wrapping _perform_api_call.

From agent/conversation_loop.py (the API-error retry branch, line 3488):
```python
if _retry_after:
    wait_time = _retry_after
else:
    wait_time = jittered_backoff(retry_count, base_delay=0.5, max_delay=32.0, jitter_ratio=0.25)
if is_rate_limited:
    ...
elif classified.reason == FailoverReason.overloaded:
    agent._buffer_status(f"🔥 Upstream overloaded. Waiting {wait_time:.1f}s ...")
```
The `classified` variable is in scope here (ClassifiedError) — use classified.reason
to pick the backoff preset BEFORE computing wait_time.

From agent/error_classifier.py (FailoverReason enum — line 37):
```python
overloaded = "overloaded"  # 503/529 — provider overloaded, backoff
```
1305 detection lives at error_classifier.py:626 (regex) and :1426 (code match).

From agent/agent_runtime_helpers.py:675-690: existing overloaded→rotate branch in
recover_with_credential_pool. Returns (False, has_retried_429) when pool is empty
(single-key user) — no change needed here, the guard + backoff + early-abort compensate.

Config getter: hermes_cli/config.py:5359  `cfg_get(cfg, *keys, default=None)`.
Config loader: hermes_cli/config.py:5444  `load_config() -> Dict[str, Any]`.

NO existing config key `glm.global_concurrency` — this commit introduces it.
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Implement A+B+C combo (guard module + retry preset + loop hooks)</name>
  <files>
    agent/glm_concurrency_guard.py,
    agent/retry_utils.py,
    agent/conversation_loop.py,
    tests/test_glm_concurrency_guard.py,
    tests/agent/test_retry_utils_overloaded.py,
    cli-config.yaml.example
  </files>
  <behavior>
    <!-- What each test must assert BEFORE implementation -->
    - Test A1 (host matching): `is_glm_endpoint("https://open.bigmodel.cn/api/anthropic")` returns True; `is_glm_endpoint("https://api.anthropic.com")` returns False; `is_glm_endpoint(None)` returns False; `is_glm_endpoint("")` returns False.
    - Test A2 (semaphore singleton per host): calling `get_glm_semaphore("https://open.bigmodel.cn")` twice returns the SAME object; calling for two distinct bigmodel hosts returns distinct semaphores.
    - Test A3 (config N wins): set env override OR monkeypatch load_config to return `{"glm": {"global_concurrency": 7}}`; assert `get_glm_semaphore(...)._value == 7`. With no config, assert default `_value == 4`.
    - Test A4 (concurrency cap): spawn 10 threads that each enter `acquire_glm_slot(url)` and sleep 0.2s; with N=3 injected, assert at most 3 are simultaneously inside the context manager (high-water mark via shared counter).
    - Test A5 (release-on-exception): inside `with acquire_glm_slot(url): raise RuntimeError("boom")`; assert the semaphore value returns to its initial state afterwards.
    - Test A6 (non-glm endpoint passthrough): for `is_glm_endpoint("https://api.openai.com") is False`, `acquire_glm_slot(...)` MUST be a no-op context manager (does not block) — verify by entering it with N=0 semaphore and confirming no block.
    - Test B1 (overloaded preset): `jittered_backoff_overloaded(1)` >= 30.0 and < 60.0; `jittered_backoff_overloaded(5)` >= 600.0 (capped + jitter, exact upper bound loose); return type is float.
    - Test B2 (default unchanged): `jittered_backoff(1, base_delay=0.5, max_delay=32.0, jitter_ratio=0.25)` still returns a value in [0.5, 0.625] — confirms the existing default path is untouched.
    - Test C1 (early-abort counter): invoke a fake retry loop that classifies 3 consecutive `FailoverReason.overloaded` errors; assert the loop exits with `failed=True` and `error` field contains the substring "GLM model overloaded".
    - Test C2 (other-reason no-abort): same fake loop with 3 consecutive `FailoverReason.timeout` errors; assert it does NOT early-abort (continues to max_retries).
    - Test C3 (counter resets): 2 overloaded → 1 timeout → 2 more overloaded; loop should NOT abort (counter reset on the timeout), proving the consecutive-only semantics.
  </behavior>
  <action>
    Write tests FIRST (RED), then implement (GREEN). Order: tests/test_glm_concurrency_guard.py + tests/agent/test_retry_utils_overloaded.py first, run to confirm they fail, then implement.

    **A. Create agent/glm_concurrency_guard.py** (new module, ~90 lines):
    - `from __future__ import annotations` at top (per CLAUDE.md module convention).
    - Module-level `_SEMAPHORES: dict[str, threading.Semaphore]` keyed by normalized host, `_LOCK = threading.Lock()`.
    - `is_glm_endpoint(base_url: str | None) -> bool`: return False on empty/None; parse with `urllib.parse.urlparse`; return True iff hostname endswith `"bigmodel.cn"`. This matches open.bigmodel.cn AND any future *.bigmodel.cn subdomain. Do NOT hard-code "open." — Zhipu may route via other subdomains.
    - `_resolve_glm_n() -> int`: read `os.environ.get("HERMES_GLM_CONCURRENCY")` first (operator escape hatch during incidents), else `cfg_get(load_config(), "glm", "global_concurrency", default=4)`. Clamp to [1, 32]. Cache the resolved value module-level after first call (config hot-reload NOT required — operator can restart the gateway to pick up new value, matching existing config semantics).
    - `get_glm_semaphore(base_url: str | None) -> threading.Semaphore | None`: return None if not `is_glm_endpoint(base_url)`; else lazily create-or-get from the dict under `_LOCK`. Use the parsed hostname as key (so open.bigmodel.cn is one semaphore even if paths differ).
    - `acquire_glm_slot(base_url: str | None)`: return a `contextlib.contextmanager` that (a) if `is_glm_endpoint(base_url)` is False → yields immediately (no-op, zero overhead for non-GLM providers — CRITICAL: must not slow down Anthropic/OpenAI/etc paths); (b) else acquires `get_glm_semaphore(base_url)` before yield, releases in finally. Use `try/finally` so exceptions release the slot.
    - Log INFO once when the semaphore is first created for a host: `"GLM concurrency guard enabled for %s: N=%d"`. Log DEBUG on each acquire if `logger.isEnabledFor(logging.DEBUG)`.
    - Concurrency note: use `threading.Semaphore` (NOT asyncio) because the agent's API calls run synchronously inside `_perform_api_call` even under the gateway's asyncio loop — the OpenAI SDK call blocks the thread. ThreadPoolExecutor workers (delegate_task) and asyncio threads will all share this process-wide semaphore. Cross-process is OUT OF SCOPE (single gateway process assumption — matches the existing hermes-gateway.service deployment).

    **B. Extend agent/retry_utils.py**:
    - Do NOT change the signature of existing `jittered_backoff`.
    - Add `def jittered_backoff_overloaded(attempt: int) -> float:` thin wrapper returning `jittered_backoff(attempt, base_delay=30.0, max_delay=600.0, jitter_ratio=0.5)`. The 30s floor ensures the third retry happens at >= 30s + jitter (well past the typical 1305 micro-burst), the 600s cap leaves headroom under the gateway's max-iteration wall-clock.
    - Add a module docstring note that the overloaded preset is tuned for Zhipu GLM 1305 ("该模型当前访问量过大") recovery windows observed 2026-07-02.

    **C. Modify agent/conversation_loop.py** — three surgical edits:

    **C1. Guard hook at the API-call chokepoint** (around line 1119):
    - Import at top: `from agent.glm_concurrency_guard import acquire_glm_slot`.
    - Wrap the `run_llm_execution_middleware(...)` call like so:
      ```
      with acquire_glm_slot(getattr(agent, "base_url", None)):
          response = run_llm_execution_middleware(
              api_kwargs, _perform_api_call, ...
          )
      ```
    - The context manager is a no-op for non-GLM providers, so this is safe to wrap unconditionally. Do NOT add a branch like `if is_glm_endpoint(...)`. The guard module already short-circuits internally.
    - The semaphore is released the moment `_perform_api_call` returns (success or exception) — this is the correct scope: we are throttling IN-FLIGHT HTTP requests, not retry-loop iterations.

    **C2. 1305-specific backoff in the API-error retry branch** (line ~3488):
    - Replace the unconditional `jittered_backoff(retry_count, base_delay=0.5, max_delay=32.0, jitter_ratio=0.25)` with a branch:
      ```
      if _retry_after:
          wait_time = _retry_after
      elif classified.reason == FailoverReason.overloaded:
          wait_time = jittered_backoff_overloaded(retry_count)
      else:
          wait_time = jittered_backoff(retry_count, base_delay=0.5, max_delay=32.0, jitter_ratio=0.25)
      ```
    - Import: extend the existing `from agent.retry_utils import jittered_backoff` line to also import `jittered_backoff_overloaded`.
    - Do NOT touch line 1399 (invalid-response path) — that path uses 5s/120s defaults and is unrelated.

    **C3. Consecutive-overloaded early-abort counter**:
    - The retry-loop state lives in a `_retry` namespace (SimpleNamespace). Add a new field next to the existing ones (search for `image_shrink_retry_attempted` or `multimodal_tool_content_retry_attempted` to find the init block): `_retry.consecutive_overloaded = 0`.
    - At the very TOP of the API-error branch, AFTER `classified = classify_api_error(...)` but BEFORE the `if retry_count >= max_retries:` terminal check, add:
      ```
      if classified.reason == FailoverReason.overloaded:
          _retry.consecutive_overloaded += 1
      else:
          _retry.consecutive_overloaded = 0
      ```
    - Then add an early-abort guard IMMEDIATELY AFTER the counter update and BEFORE the max_retries check:
      ```
      if _retry.consecutive_overloaded >= 3:
          agent._flush_status_buffer()
          _abort_msg = (
              "GLM model overloaded — 3 consecutive 1305/overloaded responses. "
              "Pause new requests for ~10-15 minutes and retry."
          )
          agent._emit_status(f"🔥 {_abort_msg}")
          logger.error(
              "%sGLM early-abort: 3 consecutive overloaded (1305) failures. "
              "Backing off rather than exhausting %s retries. %s",
              agent.log_prefix, max_retries, agent._client_log_context(),
          )
          agent._persist_session(messages, conversation_history)
          return {
              "messages": messages,
              "completed": False,
              "api_calls": api_call_count,
              "failed": True,
              "error": _abort_msg,
              "failure_reason": "glm_overloaded_abort",
          }
      ```
    - Reset semantics: the counter resets on ANY non-overloaded classified reason, AND on the next successful API call (place `_retry.consecutive_overloaded = 0` together with where the existing retry counters reset on success — search for the success path). This ensures that a single 1305 followed by recovery does not poison the next burst.
    - Verify by re-reading tests C1/C2/C3 in the behavior block — they must all pass against this logic.

    **D. cli-config.yaml.example** — append to the existing commented `glm:` block (around line 1174):
    ```
    #   glm:
    #     model: glm-4.7
    #     provider: custom
    #     base_url: "https://open.bigmodel.cn/api/anthropic"
    #     # Process-wide cap on concurrent in-flight requests to *.bigmodel.cn.
    #     # Mitigates 1305 overloaded_error during peak hours. Default 4.
    #     # Operator override: HERMES_GLM_CONCURRENCY env var (takes precedence).
    #     global_concurrency: 4
    ```

    **Code-style checklist (per CLAUDE.md — Ruff will block merge otherwise):**
    - Every `open(...)` in tests uses `encoding="utf-8"` (even though tests rarely open files — any fixture files must comply).
    - All `logger.x(...)` calls use `%s` positional args, NOT f-strings. The abort message above uses an f-string for `_abort_msg` (a user-facing string, fine) but `logger.error(...)` uses `%s`.
    - snake_case for all new identifiers.
    - `from __future__ import annotations` at the top of `agent/glm_concurrency_guard.py`.
    - Use `from agent.retry_utils import jittered_backoff, jittered_backoff_overloaded` (explicit imports, no `*`).
    - Use `except X as exc:` with bound name in any except block; never bare `except:`.

    **Do NOT:**
    - Touch agent/agent_runtime_helpers.py (the existing overloaded-rotate branch is correct for multi-key users; with the new guard in place, single-key users no longer hit it 10 times in a row).
    - Add credential pool logic, model fallback, or OpenRouter routing.
    - Disable curator or title_generator (out of scope — the guard covers the main loop which is where the incident originated).
    - Add the guard to auxiliary_client.py paths in this commit — those are lower-volume and can be a follow-up if observed.
  </action>
  <verify>
    <automated>cd /data/workspace/hermes-agent && python -m pytest tests/test_glm_concurrency_guard.py tests/agent/test_retry_utils_overloaded.py -x -v 2>&1 | tail -40 && echo "---REGRESSION---" && python -m pytest tests/agent/test_error_classifier.py tests/test_retry_utils.py 2>/dev/null -x 2>&1 | tail -10 && echo "---RUFF---" && ruff check agent/glm_concurrency_guard.py agent/retry_utils.py agent/conversation_loop.py 2>&1 | tail -10</automated>
  </verify>
  <done>
    - All tests in tests/test_glm_concurrency_guard.py and tests/agent/test_retry_utils_overloaded.py pass.
    - Existing tests/agent/test_error_classifier.py and tests/test_retry_utils.py still pass (no regression in error classification or default backoff math).
    - `ruff check` is clean on all three modified/created Python files (PLW1514 enforced — every open() has encoding=).
    - Manual code-read confirms: (1) `acquire_glm_slot` is the ONLY new call inside the run_llm_execution_middleware site; (2) `jittered_backoff_overloaded` is branched ONLY in the API-error retry path at line ~3488; (3) `_retry.consecutive_overloaded` is incremented, reset on non-overloaded, reset on success, and checked `>= 3` before the max_retries terminal branch.
    - The three changes are atomic — none depends on another being shipped first, but together they eliminate the failure mode observed 2026-07-02.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| operator config → runtime | `glm.global_concurrency` integer is read from `~/.hermes/config.yaml` and the `HERMES_GLM_CONCURRENCY` env var; a malformed value could either under- or over-permit concurrency |
| multi-thread → shared semaphore | The process-wide semaphore is mutated from the main loop thread, delegate_task ThreadPoolExecutor workers, and any auxiliary caller — concurrent lazy-init must be lock-guarded |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-GLM-01 | Tampering | `glm.global_concurrency` config value | mitigate | Clamp to [1, 32] in `_resolve_glm_n()`; reject absurd values; fall back to default 4 on any TypeError/ValueError during parsing. |
| T-GLM-02 | DoS (self-inflicted) | Operator sets N=1 | accept | N=1 is a valid choice (fully serialize GLM calls); log a warning so operator sees the throughput impact. Rationale: not a security threat, operator's own foot. |
| T-GLM-03 | Tampering | `HERMES_GLM_CONCURRENCY` env var injection | accept | Env var already requires process-level access; an attacker who can set env vars on hermes-gateway.service already owns the box. No additional mitigation beyond the [1, 32] clamp. |
| T-GLM-04 | DoS | Semaphore deadlock on exception | mitigate | `acquire_glm_slot` uses try/finally to release on exception; Test A5 explicitly covers this. |
| T-GLM-05 | Repudiation | Missing log trail for guard activation | mitigate | INFO log on first semaphore creation ("GLM concurrency guard enabled for %s: N=%d"); DEBUG on each acquire so operator can correlate with agent.log. |
</threat_model>

<verification>
After Task 1 lands:

1. **Unit tests green** — `python -m pytest tests/test_glm_concurrency_guard.py tests/agent/test_retry_utils_overloaded.py -v` (12 tests, all pass).
2. **No regression** — `python -m pytest tests/agent/test_error_classifier.py tests/test_retry_utils.py tests/agent/test_auxiliary_client.py -x` passes (existing behavior unchanged for non-overloaded paths).
3. **Ruff clean** — `ruff check agent/glm_concurrency_guard.py agent/retry_utils.py agent/conversation_loop.py` exits 0 (PLW1514 encoding rule specifically).
4. **Manual incident-time check (operator)** — during the next peak hour, `tail -F ~/.hermes/logs/agent.log | grep -E "GLM concurrency|consecutive 1305|early-abort"` should show (a) the one-time guard-enabled INFO line at startup, (b) the early-abort ERROR line if/when 3× 1305 strikes again instead of 10 useless retries.
5. **Single commit** — `git log -1 --stat` shows exactly one commit containing all 6 files (3 source + 2 test + 1 config example). Commit message references "2026-07-02 10:05-10:25 CST incident" and the constraint (single endpoint / single model / no extra cost).
</verification>

<success_criteria>
- The "model provider failed after retries" failure mode observed 2026-07-02 10:05-10:25 CST is structurally eliminated for single-key GLM users: the concurrency guard prevents the request flood that caused the 1305 burst, the long backoff gives retries a real chance to span the provider's recovery window, and the 3-strike early-abort surfaces a clear operator-actionable message instead of churning through 10 retries that the user perceives as a generic crash.
- Zero changes to credential pool, fallback provider, model switch, OpenRouter, curator, title_generator, or any non-GLM code path.
- All automated checks in <verify> green.
</success_criteria>

<output>
Create `.planning/quick/260702-ezx-glm-concurrency-hardening/260702-ezx-SUMMARY.md` when done. Single atomic commit, message format:

```
fix(glm): concurrency guard + 1305 backoff + 3-strike abort (A+B+C)

Mitigates recurring open.bigmodel.cn 1305 overloaded_error storm
(2026-07-02 10:05-10:25 CST, ~400 retry failures surfacing as
"model provider failed after retries").

A. agent/glm_concurrency_guard.py: process-wide threading.Semaphore
   keyed by host, default N=4, configurable via glm.global_concurrency
   (config.yaml) or HERMES_GLM_CONCURRENCY (env). No-op for non-GLM
   providers. Wraps _perform_api_call at the single chokepoint.

B. jittered_backoff_overloaded(): 30s base / 600s cap for
   FailoverReason.overloaded — gives retries a real chance to span
   the 1305 recovery window. Default path unchanged.

C. consecutive-overloaded counter on _retry namespace; 3 in a row
   aborts with "GLM model overloaded — pause ~10-15 min" instead of
   exhausting all 10 retries. Counter resets on any non-overloaded
   reason and on success.

Constraint honored: single endpoint (open.bigmodel.cn), single model
(glm-5.2), no OpenRouter, no model fallback, no credential pool changes.

Tests: tests/test_glm_concurrency_guard.py,
       tests/agent/test_retry_utils_overloaded.py
```
</output>
