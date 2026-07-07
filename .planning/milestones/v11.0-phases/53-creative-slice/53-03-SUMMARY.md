---
phase: 53-creative-slice
plan: 03
subsystem: agent-round-table-driver
tags: [creative-01, round-table, glm-dispatch, driver, screenplay-step3, hook-09]
requires:
  - "Phase 52 contract surface (mcp_serve.py Phase 52 MCP tools + agent.round_table_executor + agent.round_table_state)"
  - "Plan 53-01: 9 agent YAMLs at ~/.hermes/agents/*.agent.yaml + tests/fixtures/screenplay-step3-schema.json"
  - "Plan 53-02: agent.memory_arbitration.memory_retrieve_scoped (real mem0 routing)"
  - "agent.auxiliary_client.call_llm (GLM dispatch via 4-key rotation + 3-strike early-abort)"
provides:
  - "mcp_serve.py::get_agent_opinion (real GLM dispatch — replaces Phase 52 placeholder)"
  - "mcp_serve.py::{round_table_open, submit_round_table_result, memory_retrieve_scoped, memory_submit_record} (lifted to module-level — directly importable for driver + tests)"
  - "scripts/run_screenplay_step3_roundtable.py (9-agent serial lifecycle driver + synthesis pass + HOOK-09 schema validation)"
  - "tests/agent/test_run_screenplay_step3.py (11 tests covering get_agent_opinion body + driver lifecycle + cli-config)"
  - "tests/fixtures/storykernel-sample.json (synthetic StoryKernel Step 1 input for driver)"
  - "cli-config.yaml.example auxiliary.round_table_opinion + auxiliary.memory_comparator entries"
affects:
  - "mcp_serve.py create_mcp_server() — Phase 52 nested-function tool registrations replaced with mcp.tool()(module_fn) pattern (Wave 0 OQ-1 contract now literally true)"
  - "tests/test_mcp_serve.py TestToolRegistration::test_all_tools_registered — Phase 52 had failed to update expected set when 7 new tools landed; this plan updated it (Rule 1)"
  - "Phase 54 EVAL-HARNESS-1: fitness battery consumes the running driver + HOOK-09-valid output"
tech-stack:
  added: []
  patterns:
    - "Nested-function → module-level tool lifting (Rule 3 blocking-issue auto-fix)"
    - "FastMCP mcp.tool()(module_fn) registration pattern for testable in-process MCP tools"
    - "Nested try/finally — outer preserves T-52-15 lock contract, inner clears _scoped_agent_id (RESEARCH Pitfall 5)"
    - "Dynamic agent.auxiliary_client.call_llm() lookup (NOT 'from ... import call_llm') so monkeypatch works in tests"
    - "Strict-serial for-loop with chained panel_context (T-53-12 accepted threat — round-table deliberation mechanism)"
    - "Synthesis pass as 10th GLM call with temperature=0.4 (vs per-panelist 0.7) — more deterministic consolidation"
key-files:
  created:
    - scripts/run_screenplay_step3_roundtable.py
    - tests/fixtures/storykernel-sample.json
    - .planning/phases/53-creative-slice/53-VERIFICATION.md
  modified:
    - mcp_serve.py
    - tests/agent/test_run_screenplay_step3.py
    - tests/test_mcp_serve.py
    - cli-config.yaml.example
decisions:
  - "Lift Phase 52's 5 round-table/memory MCP tools from nested functions inside create_mcp_server() to module-level async functions (Rule 3: nested structure prevented Wave 0 contract + plan's tests from running). create_mcp_server now re-registers them via mcp.tool()(fn). Phase 52 MCP surface unchanged."
  - "Use 'import agent.auxiliary_client' + dynamic 'agent.auxiliary_client.call_llm(...)' lookup in the driver (NOT 'from agent.auxiliary_client import call_llm'). The latter captures the reference at import time and breaks monkeypatch in tests."
  - "SC#2 real-GLM smoke test marked human_needed per CONTEXT.md deferred list — worktree executor cannot verify <30s latency contract (no openai package, no live GLM rate budget for 10 sequential calls). Operator runbook documented in 53-VERIFICATION.md."
  - "Synthesis pass: temperature=0.4 vs per-panelist 0.7. Rationale: the synthesis consolidates 9 opinions into a structured JSON — lower temperature improves schema-conformance without sacrificing the panelists' creative input."
metrics:
  duration: 612s
  completed: "2026-07-07"
  tasks: 2
  files-created: 3
  files-modified: 4
  tests-added: 11
  tests-passing: 53
---

# Phase 53 Plan 03: Real-GLM get_agent_opinion + 9-Agent Screenplay Step 3 Driver Summary

Wired real GLM dispatch into `mcp_serve.py::get_agent_opinion` (replacing Phase 52's `"[phase52_placeholder]"`) and shipped `scripts/run_screenplay_step3_roundtable.py` — the driver that orchestrates the 9-agent serial round table, runs a 10th synthesis GLM call, validates the output against the HOOK-09 emotion_curve marker schema, and exits cleanly when GLM is unavailable. Also lifted Phase 52's 5 nested round-table/memory MCP tools to module-level so Wave 0 OQ-1 contract is literally true (`from mcp_serve import round_table_open, get_agent_opinion, submit_round_table_result`).

## What Was Built

### mcp_serve.py — Phase 52 nested tools → module-level + real GLM dispatch

The 5 Phase 52 round-table/memory MCP tools were originally defined as nested functions inside `create_mcp_server()`, making them unimportable. Plan 53-03 Task 1 lifted them to module-level async functions (`round_table_open`, `get_agent_opinion`, `submit_round_table_result`, `memory_retrieve_scoped`, `memory_submit_record`); `create_mcp_server` now re-registers them via the FastMCP `mcp.tool()(module_fn)` pattern. Phase 52 MCP surface unchanged (same 5 tool names, same signatures, same error responses, same T-52-15 try/finally lock contract).

`get_agent_opinion` body now performs real GLM dispatch:

1. `set_scoped_agent_id(agent_id)` — sets ContextVar for memory routing (BEFORE memory_retrieve).
2. `await memory_retrieve_scoped(query=topic, agent_id=agent_id, top_k=5)` — real mem0 routing from Plan 53-02. Degrades to `{"status": "unavailable", "hits": []}` on backend error.
3. `_load_persona_for_agent(agent_id)` — reads `~/.hermes/agents/{agent_id}.agent.yaml` persona field; falls back to generic directive if YAML missing (best-effort, never crashes).
4. `call_llm(task="round_table_opinion", provider="glm", temperature=0.7, max_tokens=2048, messages=[...])` — explicit `provider="glm"` per MEMORY.md `feedback-glm-5-2-only.md` (RESEARCH Pitfall 6 mitigation).
5. `turn = {"turnIndex": ..., "panelistId": agent_id, "opinion": opinion_text, "citedMemoryIds": [...], "submittedAt": ...}` — real GLM text + extracted memory IDs.
6. Nested try/finally: inner `finally: set_scoped_agent_id(None)` clears the ContextVar on EVERY exit path (RESEARCH Pitfall 5 mitigation). Outer `finally: await release_round_lock(round_id)` preserves T-52-15 DoS mitigation verbatim.

The literal `"[phase52_placeholder]"` string is fully removed (0 matches via grep -F).

### scripts/run_screenplay_step3_roundtable.py — driver script

Orchestrates the 5-step 9-agent serial round table:

1. `await mcp_serve.round_table_open(round_id, project_slug="screenplay-step3-poc", question=..., panelist_agent_ids=PANEL_9, caller=...)` — creates state file.
2. **STRICT SERIAL** — `for agent_id in PANEL_9: resp = await mcp_serve.get_agent_opinion(round_id, project_slug, agent_id, topic, panel_context); panel_context = resp["opinion"]`. NO concurrent dispatch (INFRA-04 hard constraint). The chained `panel_context` IS the round-table deliberation mechanism (T-53-12 accepted threat).
3. `_synthesize_step3_output(storykernel, panel_opinions)` — 10th GLM call: screenplay expert consolidates the 9 opinions into final HOOK-09-valid Step 3 JSON. Uses `temperature=0.4` (more deterministic than per-panelist 0.7) + `max_tokens=4096` + a persona prompt that pins the 6-field output schema.
4. `await mcp_serve.submit_round_table_result(round_id, project_slug, conclusion=conclusion_json, cited_memories=[], closed_by=...)` — flips state to `"completed"`.
5. `_validate_step3_schema(output, output_path)` — `jsonschema.Draft202012Validator(schema).validate(output)` against `tests/fixtures/screenplay-step3-schema.json`, then atomic write to `output_path`.

Public API: `async def run_roundtable(storykernel_path, output_path, *, smoke=False) -> dict` returns `{"round_id", "panelist_count", "output_path", "latency_seconds"}` on success or `{"error": ...}` on failure.

CLI `main()` wraps `asyncio.run(run_roundtable(...))` with friendly error handling. On `RuntimeError` from `call_llm` (GLM unavailable), prints `"configure GLM_API_KEY in ~/.hermes/.env (see cli-config.yaml.example auxiliary.round_table_opinion)"` to stderr + exits 2 (no traceback — CONTEXT.md "Claude's Discretion" #6 graceful-skip).

### tests/fixtures/storykernel-sample.json — synthetic StoryKernel Step 1 input

Realistic Chinese-urban short-drama StoryKernel: 80-episode modern-life arc about a sous-chef returning to her coastal hometown. Fully synthetic, SFW, no PII. Includes 3 characters with voice traits + arc, setting with key locations, story_spine (inciting incident + midpoint reversal + climax + resolution), ip_provenance + content_safety metadata.

### cli-config.yaml.example — auxiliary task entries

Added two GLM-only auxiliary task entries under the existing `# auxiliary:` template section:

```yaml
round_table_opinion:
  provider: glm          # GLM-only — MEMORY.md feedback-glm-5-2-only.md
  model: glm-5.2         # Phase 53 CREATIVE-01 panelist opinion calls
  timeout: 30            # SC#2 latency budget (<30s per call)
memory_comparator:
  provider: glm          # GLM-only — same policy
  model: glm-5.2         # Phase 53 CREATIVE-02 conflict arbitration
  timeout: 30
```

### tests/agent/test_run_screenplay_step3.py — 11 tests

Task 1 (6 tests, all `@pytest.mark.asyncio` per RESEARCH Pitfall 3):

1. `test_get_agent_opinion_returns_real_glm_opinion` — mocked call_llm; returned opinion equals the mock content.
2. `test_get_agent_opinion_uses_round_table_opinion_task` — asserts `task="round_table_opinion"` + `provider="glm"`.
3. `test_get_agent_opinion_sets_scoped_agent_id_before_memory_call` — spies on set_scoped_agent_id + memory_retrieve_scoped; verifies ordering + finally cleanup.
4. `test_get_agent_opinion_preserves_try_finally_lock_contract` — call_llm raises; release_round_lock still called exactly once.
5. `test_get_agent_opinion_serial_violation_unchanged` — `asyncio.gather` of 2 concurrent calls for same round_id: one succeeds, one gets 429 serial_violation.
6. `test_get_agent_opinion_appends_turn_with_opinion` — state file `turns[-1].opinion` equals the mock response (not placeholder).

Task 2 (5 tests):

7. `test_driver_runs_full_lifecycle_with_mocked_glm` — mocked GLM returns distinct opinions per panelist + HOOK-09-valid final JSON; driver succeeds; state shows 9 turns + status=completed.
8. `test_driver_strict_serial_no_asyncio_gather` — grep driver source; `asyncio.gather` literal substring absent; `for agent_id in` + `await ... get_agent_opinion` present.
9. `test_driver_output_validates_against_hook09_schema` — `jsonschema.Draft202012Validator(schema).validate(output)` does NOT raise.
10. `test_driver_skips_gracefully_when_glm_unavailable` — subprocess invocation with empty GLM keys: exit code != 0, no traceback, stderr mentions GLM.
11. `test_cli_config_has_auxiliary_tasks` — `cli-config.yaml.example` contains both `round_table_opinion` + `memory_comparator` with `provider: glm` within a 200-char window.

## Success Criteria Verification

| SC | Description | Status | Evidence |
|----|-------------|--------|----------|
| SC#2 (CREATIVE-01) | driver produces HOOK-09-valid JSON, <30s real-GLM latency | PARTIAL — automated gates PASS; real-GLM latency deferred to operator | 11/11 mocked-GLM tests green + jsonschema validation green (Test 9). SC#2 real-GLM smoke test marked `human_needed` in 53-VERIFICATION.md per CONTEXT.md deferred list — operator runbook documented. |
| Phase 52 contract preservation | round_table_open / submit_round_table_result interfaces unchanged; T-52-15 lock preserved; INFRA-04 serial inherited | PASS | Tests 4 + 5 + 8 green. Same 5 MCP tool names registered. |
| GLM-only enforcement | All call_llm invocations pass `provider="glm"`; cli-config documents the contract | PASS | Test 2 + Test 11 green. `grep 'provider="glm"' mcp_serve.py scripts/run_screenplay_step3_roundtable.py` shows explicit provider in both files. |
| ContextVar hygiene | `_scoped_agent_id` set before memory_retrieve + cleared in finally on every exit path | PASS | Test 3 + Test 4 green. Nested try/finally pattern documented in source. |
| Operator deferral path | If GLM unavailable, SC#2 marked `human_needed` in VERIFICATION.md (does NOT block milestone) | PASS | 53-VERIFICATION.md created with full operator runbook. |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Lifted Phase 52 nested MCP tools to module level**

- **Found during:** Task 1 RED phase — first test attempted `await mcp_serve.round_table_open(...)` and got `AttributeError: module 'mcp_serve' has no attribute 'round_table_open'`.
- **Issue:** Phase 52 defined `round_table_open`, `get_agent_opinion`, `submit_round_table_result`, `memory_retrieve_scoped`, `memory_submit_record` as nested functions inside `create_mcp_server()`. They were not importable as `mcp_serve.X`. The Wave 0 contract test (Plan 53-01) was written assuming they would be module-level, but never actually probed importability — it only checked the underlying `agent.round_table_state` / `agent.memory_arbitration` symbols.
- **Fix:** Moved all 5 functions to module level in `mcp_serve.py`. `create_mcp_server` now re-registers each one via `mcp.tool()(module_fn)` (verified this FastMCP pattern works). Phase 52 MCP surface unchanged (same 5 tool names, same signatures, same docstrings).
- **Files modified:** `mcp_serve.py`
- **Commit:** 2825c8ee9

**2. [Rule 1 - Bug] Updated stale `test_all_tools_registered` expected set**

- **Found during:** Task 1 GREEN verification — broader suite run.
- **Issue:** `tests/test_mcp_serve.py::TestToolRegistration::test_all_tools_registered` was failing PRE-EXISTING (verified via `git stash` + retest). Phase 52 added 7 new MCP tools but never updated this test's expected set. The test was simply never run again after Phase 52 landed.
- **Fix:** Added the 5 round-table/memory tools + `agents_list` + `agent_describe` to the expected set with a comment pointing at Phase 52 + Phase 53 origins.
- **Files modified:** `tests/test_mcp_serve.py`
- **Commit:** 2825c8ee9

**3. [Rule 1 - Bug] Driver used top-level `from agent.auxiliary_client import call_llm`**

- **Found during:** Task 2 GREEN — Test 9 (validate against schema) failed with "synthesis output is not valid JSON: Expecting value: line 1 column 1 (char 0)" when run after Test 7.
- **Issue:** The top-level import captured `call_llm` at module-load time. Test 7's `monkeypatch.setattr(agent.auxiliary_client, "call_llm", mock)` patched the module attribute but NOT the driver's local reference. The synthesis call hit the real `call_llm` (which has no provider in tests), returning empty.
- **Fix:** Replaced top-level import with `import agent.auxiliary_client` + dynamic lookup `agent.auxiliary_client.call_llm(...)` at call time. Now monkeypatch works correctly.
- **Files modified:** `scripts/run_screenplay_step3_roundtable.py`
- **Commit:** 0827e5b69

### Deferred Issues

**1. SC#2 real-GLM smoke test — `human_needed`**

- **Reason:** Worktree executor cannot verify the <30s latency contract. The worktree Python environment lacks the `openai` package (system python3), and even with the main repo venv, 10 sequential real GLM calls exceed the executor's timeout budget under rate-limited conditions.
- **Action:** Documented operator runbook in `.planning/phases/53-creative-slice/53-VERIFICATION.md`. Does NOT block Phase 53 close per CONTEXT.md deferred list.
- **Verification:** All 11 mocked-GLM tests green prove the lifecycle wiring; only real-GLM latency is operator-verifiable.

**2. `tests/agent/test_auxiliary_client.py::TestAuxiliaryPoolAwareness::test_async_call_llm_retries_nous_after_401` pre-existing failure**

- **Reason:** Verified pre-existing via `git stash` + retest (failed before my changes).
- **Action:** Out of scope per Rule "scope boundary". Logged in 53-VERIFICATION.md.

## Phase 52 Contract Preservation

- **`round_table_open` MCP tool**: signature, docstring, error responses, status codes — unchanged (lifted to module level verbatim).
- **`submit_round_table_result` MCP tool**: same — unchanged.
- **`memory_retrieve_scoped` / `memory_submit_record` MCP tools**: same thin forwarders to `agent.memory_arbitration` functions (Plan 53-02 made those real).
- **`get_agent_opinion` body**: signature, docstring, validation, lock acquisition, state read, status check, append_turn call, success return shape — all preserved. ONLY the placeholder opinion swap + nested-try/finally addition are new.
- **T-52-15 (DoS mitigation)**: try/finally lock release preserved verbatim — verified by Test 4 (release_round_lock called exactly once on exception path).
- **INFRA-04 (serial enforcement)**: preserved — verified by Test 5 (concurrent gather → one 429 + one ok) + driver source has 0 `asyncio.gather` literals.
- **`_ROUND_LOCKS_GUARD` atomic check-then-acquire (CR-02 fix)**: untouched — `acquire_round_or_reject` called unchanged.

## Threat Model Mitigation Coverage

| Threat | Mitigation Status |
|--------|-------------------|
| T-53-10 (Spoofing — non-GLM provider answers round_table_opinion) | Implemented: explicit `provider="glm"` in `mcp_serve.py::get_agent_opinion` + driver's `_synthesize_step3_output` + `cli-config.yaml.example` documents both entries (Test 2 + Test 11 green). |
| T-53-11 (DoS — GLM timeout blocks get_agent_opinion indefinitely) | Accepted per plan: auxiliary_client.call_llm has its own `timeout` (configurable). On timeout, exception propagates → finally releases lock → operator sees error. Round can be retried or aborted. |
| T-53-12 (Tampering — panel_context influences next panelist prompt) | Accepted per plan: chained panel_context IS the deliberation mechanism. Content is LLM-generated (not user-injected); kept as opaque prior-discussion string, never as instructions. |
| T-53-13 (Info Disclosure — persona prompt leaks via opinion output) | Accepted per plan: persona is operator-curated in agent YAML; not sensitive. |
| T-53-14 (Repudiation — round result cannot trace which GLM call produced which opinion) | Mitigated: state file records `turns[i].panelistId` + `turns[i].submittedAt` + `turns[i].opinion` + `turns[i].citedMemoryIds`. Test 6 verifies the opinion is recorded. |
| T-53-15 (Elevation — driver bypasses serial lock) | Accepted per plan: driver imports from mcp_serve (which goes through the lock). Bypass requires deliberate source modification. |
| T-53-SC (supply chain) | N/A — no new packages installed. |

## Self-Check: PASSED

Created files verified to exist on disk:
- `scripts/run_screenplay_step3_roundtable.py` — FOUND
- `tests/fixtures/storykernel-sample.json` — FOUND
- `.planning/phases/53-creative-slice/53-VERIFICATION.md` — FOUND
- `.planning/phases/53-creative-slice/53-03-SUMMARY.md` — FOUND (this file)

Modified files verified:
- `mcp_serve.py` — FOUND, `[phase52_placeholder]` grep returns 0
- `tests/agent/test_run_screenplay_step3.py` — FOUND, 11 tests
- `tests/test_mcp_serve.py` — FOUND
- `cli-config.yaml.example` — FOUND, both task entries present

Commits verified in git log:
- `0dfbd30fd` — test(53-03): RED — 6 failing tests for get_agent_opinion real-GLM body — FOUND
- `2825c8ee9` — feat(53-03): real GLM dispatch in get_agent_opinion + module-level MCP tools — FOUND
- `a55d51b8a` — test(53-03): RED — 5 failing tests for driver script + cli-config entries — FOUND
- `0827e5b69` — feat(53-03): 9-agent screenplay Step 3 driver + auxiliary task config — FOUND

Phase-gate tests: 53/53 green (`tests/agent/test_phase52_contract.py tests/agent/test_transform_skill_to_agent.py tests/agent/test_memory_arbitration.py tests/agent/test_conflict_log_writer.py tests/agent/test_run_screenplay_step3.py`).

Static gates: 0 `[phase52_placeholder]` in mcp_serve.py; 0 `asyncio.gather` in driver; 9 agents load; HOOK-09 invariant present (2 matches in screenplay YAML); both auxiliary tasks documented with `provider: glm`.

## Known Stubs

None. Every component has a real implementation:
- `get_agent_opinion` performs real GLM dispatch (mocked in unit tests; real in operator smoke test).
- `_synthesize_step3_output` performs a real 10th GLM call.
- `_validate_step3_schema` performs real jsonschema validation.
- The mem0 routing in `memory_retrieve_scoped` degrades to `{"status": "unavailable", "hits": []}` when `MEM0_API_KEY` is unset — this is documented Phase 53 behavior (CONTEXT.md decision #3 — graceful degradation, NOT a stub).

## Notes for Downstream Plans

### Phase 54 (EVAL-HARNESS-1)

- The driver script is the **fitness battery entry point**: invoke `python scripts/run_screenplay_step3_roundtable.py --smoke` once per fitness eval cycle to produce a Step 3 JSON artifact.
- The HOOK-09 schema at `tests/fixtures/screenplay-step3-schema.json` is the **canonical contract** for downstream eval — every fitness dimension should validate its input against this schema first.
- `tests/fixtures/storykernel-sample.json` is the **benchmark StoryKernel** — use it across eval runs to control variables.
- The 11-test suite at `tests/agent/test_run_screenplay_step3.py` provides the **regression gate** — any change to mcp_serve, driver, or arbitration should keep all 11 green.

### Future v12+ work

- Real mem0 backend wiring (when MEM0_API_KEY is configured) — the routing layer is in place.
- Per-panelist temperature customization (currently uniform 0.7 per-panelist + 0.4 synthesis; cinematographer might want 0.5, theory_critic 0.3, etc.).
- Parallel round tables (v11.0 explicitly forbids this per INFRA-04; v12+ might revisit with sub-panel locking).
