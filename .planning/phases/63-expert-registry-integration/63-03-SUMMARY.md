---
phase: 63-expert-registry-integration
plan: "03"
subsystem: round-table
tags:
  - round-table
  - visual-executor
  - smoke-test
  - mock-llm
  - tdd
dependency_graph:
  requires:
    - "63-01 (alarm scaffolding — same phase context; no code dep)"
  provides:
    - "tests/agent/test_phase63_round_table_smoke.py (SC#3 authoritative smoke)"
  affects:
    - "Phase 64+ integration tests can reuse the _seed / _mock_call_llm helpers"
tech_stack:
  added: []
  patterns:
    - "mock LLM unconditional in authoritative test (Pitfall #3)"
    - "opt-in live GLM via HERMES_PHASE63_LIVE_SMOKE=1 env var"
    - "stage 2 panelists for minItems=2 schema (Pitfall #4)"
    - "registry cache invalidation per-test (Pitfall #6)"
key_files:
  created:
    - "tests/agent/test_phase63_round_table_smoke.py"
  modified: []
decisions:
  - "G3 Option A: mock LLM is SC#3 authoritative; live mode is operator opt-in only"
  - "Pitfall #4 mitigation: cinematographer staged as 2nd panelist to satisfy minItems=2 — only visual_executor asked for opinion (SC#3 scope)"
  - "Acceptance grep criteria (asyncio.gather==0, Path.home()==0) required docstring rewording to avoid false-positive matches"
metrics:
  duration: "~5min"
  completed: "2026-07-08"
  tasks: 1
  files: 1
---

# Phase 63 Plan 03: visual_executor Round-Table Smoke Summary

Mock-LLM SC#3 authoritative smoke proving the most complex agent (visual_executor with sub_steps [drawer, animator] in persona text) traverses the full 3-step round-table lifecycle (open -> opinion -> submit) producing a non-empty opinion.

## What was built

`tests/agent/test_phase63_round_table_smoke.py` — a NEW 439-line test file with:

- **`TestVisualExecutorSmoke` class** (3 test methods):
  1. `test_round_table_produces_nonempty_opinion` — SC#3 authoritative mock test. Full lifecycle: seed 2 YAMLs -> mock LLM -> `open_round_table` -> `await get_agent_opinion(agent_id="visual_executor")` -> `submit_round_table_result`. Asserts final state file has `status="completed"` with at least 1 turn whose `opinion` field is non-empty + `panelistId="visual_executor"`.
  2. `test_live_round_table` — operator opt-in live GLM smoke. Skipif-gated on `HERMES_PHASE63_LIVE_SMOKE=1` env var AND requires `GLM_API_KEY`. Additional keyword assertion (opinion mentions "drawer" OR "animator") proves persona robustness under real GLM dispatch.
  3. `test_open_round_table_idempotent_on_duplicate` — sanity check that second `open_round_table` with the same `round_id` returns 409 `round_already_open`.

- **`_seed_visual_executor_yamls(tmp_path)` helper** — stages real `visual_executor.agent.yaml` + `cinematographer.agent.yaml` from `~/.hermes/agents/` into the redirected HERMES_HOME's `agents/` dir. Invalidates `registry_loader._REGISTRY_CACHE` (Pitfall #6).

- **`_mock_call_llm(monkeypatch)` helper** — mirrors `tests/agent/test_mcp_serve_round_table.py:88-117` pattern. Patches `auxiliary_client.call_llm` with a `FakeResponse` whose `choices[0].message.content` is a deterministic string containing persona keywords ("drawer", "animator").

- **`_compute_state_dir()` helper** — returns `get_hermes_home() / "agents" / ".runtime" / SMOKE_PROJECT_SLUG / "round_tables"`. MUST match the path `mcp_serve.get_agent_opinion` computes internally (mcp_serve.py:758-765).

## Verification results

```
$ python -m pytest tests/agent/test_phase63_round_table_smoke.py -v
collected 3 items

tests/agent/test_phase63_round_table_smoke.py::TestVisualExecutorSmoke::test_round_table_produces_nonempty_opinion PASSED [ 33%]
tests/agent/test_phase63_round_table_smoke.py::TestVisualExecutorSmoke::test_live_round_table SKIPPED [ 66%]
tests/agent/test_phase63_round_table_smoke.py::TestVisualExecutorSmoke::test_open_round_table_idempotent_on_duplicate PASSED [100%]

========================= 2 passed, 1 skipped in 0.53s =========================
```

Acceptance criteria verified:
- `asyncio.gather` count: 0 (INFRA-04 serial constraint respected)
- `Path.home()` count: 0 (uses `get_hermes_home()` throughout)
- Mock-mode test exits 0 (SC#3 authoritative)
- Idempotency test exits 0
- Live test reports 1 skipped by default (does not fail CI)

## TDD compliance

Single-task TDD plan (`tdd="true"`). RED was implicit (the file did not exist before this commit; running it would have produced collection error). GREEN produces the passing test. No separate RED commit because the test and its assertions are co-located (the lifecycle under test already exists in v11.0/v12.0 runtime — the test proves it works with the Phase 62 visual_executor YAML, which is itself the "feature"). No refactor step needed (file is already clean).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Worktree absolute-path safety (#3099)**
- **Found during:** Task 1 file write
- **Issue:** First Write call used absolute path `/data/workspace/hermes-agent/tests/agent/...` which resolved to the MAIN REPO (not the worktree at `/data/workspace/hermes-agent/.claude/worktrees/agent-a458c795fbc04ad9a/`). The file landed outside the worktree's git scope.
- **Fix:** Deleted the misplaced file from the main repo, rewrote with the worktree-rooted absolute path `/data/workspace/hermes-agent/.claude/worktrees/agent-a458c795fbc04ad9a/tests/agent/test_phase63_round_table_smoke.py`.
- **Files modified:** `tests/agent/test_phase63_round_table_smoke.py` (correct location only)
- **Commit:** 69d2e1e75

**2. [Rule 1 - Bug] Acceptance grep false-positives in docstring**
- **Found during:** Task 1 verification
- **Issue:** Initial docstring literally mentioned ``asyncio.gather`` and ``Path.home() / ".hermes"`` as descriptive prose, causing `grep -c` to return 2 (not 0 as required by the plan's acceptance criteria).
- **Fix:** Reworded the module docstring + constant comment to avoid the literal grep-triggering substrings ("parallel-dispatch primitives" instead of `asyncio.gather`; "home-directory concatenation pattern" instead of `Path.home()`).
- **Files modified:** `tests/agent/test_phase63_round_table_smoke.py`
- **Commit:** 69d2e1e75 (same commit — fix applied before commit)

## Auth gates

None — no live GLM calls in the default test path (mock is unconditional per Pitfall #3).

## Known Stubs

None — the test exercises the real v11.0/v12.0 round-table runtime (`agent.round_table_state`, `mcp_serve.get_agent_opinion`); the only mock is `auxiliary_client.call_llm` which is the documented hermetic pattern.

## Threat Flags

None — all threats in the plan's `<threat_model>` are either mitigated (T-63-10 opt-in live mode; T-63-11 per-test UUID + lock release; T-63-12 no parallel dispatch; T-63-SC zero new packages) or accepted (T-63-09 mock determinism; T-63-13 existing validators). No new threat surface introduced.

## Self-Check: PASSED

- `tests/agent/test_phase63_round_table_smoke.py` — FOUND (439 lines, 3 test methods)
- Commit `69d2e1e75` — FOUND in `git log --oneline`
