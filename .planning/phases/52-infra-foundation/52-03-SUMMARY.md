---
phase: 52-infra-foundation
plan: 03
subsystem: mcp-tools
tags: [mcp-tools, round-table, wire-up, fastmcp, contextvars, phase53-stub]
requires:
  - 52-01 (agent.registry_loader — load_agent_registry / load_one_agent_yaml)
  - 52-02 (agent.round_table_state — open_round_table / append_turn / submit_round_table_result / read_and_recover_state)
provides:
  - "7 v11.0 MCP tool closures registered inside mcp_serve.create_mcp_server() (round_table_open / submit_round_table_result / get_agent_opinion / agents_list / agent_describe / memory_retrieve_scoped / memory_submit_record)"
  - "agent.memory_arbitration module with phase53_not_implemented stubs + _scoped_agent_id contextvars primitive"
affects:
  - "mcp_serve.py — tool count 10 → 17 (Phase 53 adds real LLM call inside get_agent_opinion)"
  - "Phase 53 (CREATIVE-SLICE) consumes agents_list / agent_describe / round_table_open / submit_round_table_result as-is; replaces memory stubs with mem0 routing"
tech-stack:
  added: []
  patterns:
    - "FastMCP @mcp.tool() decorator form (extended existing create_mcp_server factory)"
    - "Lazy-import agent.* inside closures (mirrors mcp_serve.py:765 channels_list pattern)"
    - "contextvars.ContextVar with _UNSET sentinel (mirrors gateway/session_context.py:39-62)"
    - "Path-traversal regex validation (T-52-09 mitigation)"
key-files:
  created:
    - agent/memory_arbitration.py
    - tests/agent/test_memory_arbitration_stub.py
    - tests/agent/test_mcp_serve_round_table.py
  modified:
    - mcp_serve.py
decisions:
  - "Tool names LOCKED to 52-CONTEXT.md point 1 list (NOT 02-ROUND-TABLE-PROTOCOL.md §5 — that list is the v10.0 broader vision, not v11.0 PoC scope)"
  - "Memory tools ship as phase53_not_implemented stubs returning fixed payloads (CONTEXT.md point 3)"
  - "_scoped_agent_id contextvars primitive lives in agent.memory_arbitration (not in round_table_executor) because memory routing is cross-cutting"
  - "Direct _tool_manager._tools[name].fn access in tests (simpler than FastMCP call_tool which returns TextContent wrappers)"
metrics:
  duration: "~25 min"
  completed: "2026-07-07T01:48Z"
  tasks: 3
  files_created: 3
  files_modified: 1
  tests_added: 23
  tests_passing: 43 (incl. 20 Phase 52-01/52-02 regression)
---

# Phase 52 Plan 03: MCP Tool Wire-up Summary

Wire-up of 7 v11.0 round-table MCP tools into `mcp_serve.py`'s `create_mcp_server()` factory, composing the registry loader (INFRA-01) + state machine (INFRA-03) + a Phase-52 memory-arbitration stub module — the wire-up layer that lets Claude Code (or any MCP client) drive the round-table lifecycle.

## Outcome

| Outcome | Detail |
|---------|--------|
| Tool count | 10 → 17 registered tools (7 new + 10 existing) |
| Tool names | All 7 LOCKED to CONTEXT.md point 1 list (census test guards against v10 drift) |
| Memory stubs | `phase53_not_implemented` payloads per CONTEXT.md point 3 |
| Lifecycle SC#2 | round_table_open → get_agent_opinion → submit_round_table_result verified end-to-end against synthetic 2-panelist round table; final state file has `status="completed"` |
| T-52-09 path traversal | project_slug regex `^[A-Za-z0-9_.:-]+$` + reject `..` substring |
| Schema minItems=2 | Enforced at open-time (returns 400 panelists_min_2_required) |
| Idempotency | 409 round_already_open on duplicate open; 409 round_not_open on duplicate submit |

## Commits

| Hash | Message |
|------|---------|
| `a008054b2` | test(52-03): add failing tests for memory_arbitration stub + contextvars (RED Task 1) |
| `4ba6444bd` | feat(52-03): implement memory_arbitration Phase 52 stub + contextvars (GREEN Task 1) |
| `62c7b8b2b` | test(52-03): add failing integration tests for 7 v11.0 MCP tools (RED Task 2) |
| `58b98cdd5` | feat(52-03): wire 7 v11.0 round-table MCP tools into create_mcp_server (GREEN Task 3) |

TDD gate sequence per task: RED `test(...)` commit → GREEN `feat(...)` commit. Both gates satisfied; no REFACTOR commit needed (code was clean after GREEN).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `get_scoped_agent_id` returned `'None'` string instead of `None`**
- **Found during:** Task 1 GREEN phase — `test_set_none_returns_none` failed
- **Issue:** `set_scoped_agent_id(None)` made the ContextVar return `None`; my getter then did `str(None)` → `'None'`
- **Fix:** Added explicit `None` check (`if val is _UNSET or val is None: return None`)
- **Files modified:** agent/memory_arbitration.py
- **Commit:** `4ba6444bd`

**2. [Rule 1 - Bug] `test_no_eager_mem0_import` substring-matched docstring text**
- **Found during:** Task 1 GREEN phase — test false-positived on the module docstring which mentions `plugins.memory.mem0` in warning text
- **Issue:** Original test did `assert "import plugins.memory.mem0" not in src` against the entire module source — caught the docstring
- **Fix:** Switched to AST-walking (`ast.Import` / `ast.ImportFrom` nodes only); docstring/comment mentions no longer trigger
- **Files modified:** tests/agent/test_memory_arbitration_stub.py
- **Commit:** `4ba6444bd`

**3. [Rule 1 - Bug] Plan's "9 existing tools" count was wrong; actual is 10**
- **Found during:** Task 3 GREEN phase — `test_total_tool_count_is_nine_plus_seven` failed asserting 17 got 16
- **Issue:** Plan / CONTEXT.md / RESEARCH.md all informally said "9 existing messaging tools" but the actual pre-Phase-52 count is 10 — the plan omitted `attachments_fetch` from its census
- **Fix:** Renamed test to `test_total_tool_count_is_seventeen` and updated assertion to 17 (10 + 7)
- **Files modified:** tests/agent/test_mcp_serve_round_table.py
- **Commit:** `58b98cdd5`

### Operator-Action Blockers

**0. [BLOCKER — orchestrator attention needed] Test file `tests/agent/test_memory_arbitration_stub.py` was inadvertently committed to `main` branch in the main repo**

- **Found during:** Task 1 RED commit step
- **Issue:** The `<worktree_branch_check>` rule's `git reset --hard` ran inside the worktree and reported OK (worktree branch was already at the base commit, so reset was a no-op). My subsequent bash commands used absolute paths to `/data/workspace/hermes-agent` (the MAIN repo), so `git add` + `git commit` landed on `main` instead of my worktree branch. Detected immediately when `[main f325c52e0]` appeared in commit output. The `<pre_commit_head_assertion>` in `<task_commit_protocol>` would have caught this, but I had not yet adopted the pattern at that point in execution.
- **Recovery applied:** Per `<worktree_branch_check>` rule, did NOT `git update-ref` or `git reset --hard` on `main` (protected ref). Instead cherry-picked the bad commit (`f325c52e0`) into my worktree branch (`a008054b2`) and continued all subsequent work using absolute paths under the worktree root (`/data/workspace/hermes-agent/.claude/worktrees/agent-ac2d682942218e17c`). All later commits landed correctly on the worktree branch.
- **State on main:** `main` in the MAIN repo has one extra commit (`f325c52e0` — test file only, content-identical to worktree commit `a008054b2`). When the orchestrator merges the worktree branch, this commit on main will either (a) fast-forward cleanly if main hasn't moved, or (b) trigger a no-op merge if the file content matches. **Recommendation:** orchestrator should `git reset --hard 5c3d0a355` on main in the main repo before merge to drop the stray commit. This is the SAFE recovery — main in main repo is NOT a per-agent branch and the bad commit is a duplicate that will land on main anyway via the worktree merge.

## Auth Gates

None — pure infrastructure phase, no auth-bound surfaces touched.

## Known Stubs

Phase 52 ships the following stubs intentionally; Phase 53 (CREATIVE-SLICE) replaces them with real implementations:

| Stub | File | Line | Phase 53 Replaces With |
|------|------|------|------------------------|
| `memory_retrieve_scoped` returns `{"status": "phase53_not_implemented", "hits": []}` | agent/memory_arbitration.py | `async def memory_retrieve_scoped` | Real mem0 backend routing per agents-schema.yaml §2.6 `memory_scope` (shared / per_agent / project_scoped) |
| `memory_submit_record` returns `{"status": "phase53_not_implemented", "record_id": None}` | agent/memory_arbitration.py | `async def memory_submit_record` | Real mem0 backend routing |
| `get_agent_opinion` returns `opinion: "[phase52_placeholder]"` | mcp_serve.py | `async def get_agent_opinion` closure | Real GLM API call (Phase 53 wires the LLM dispatch via `agent/round_table_executor.py`) |

These stubs are intentional per CONTEXT.md "Resolved by Kai" point 3 (memory tools) and PLAN.md `<objective>` (get_agent_opinion placeholder). Phase 52's goal is wire-up + primitives; Phase 53's goal is real routing. Census + contract tests guard against payload drift.

## Threat Flags

No new threat surface beyond the plan's `<threat_model>`. T-52-09 (path traversal) mitigation landed as specified (regex + reject `..`). T-52-10/11/12 (DoS / spoofing / info disclosure) accepted per plan, no new surface. T-52-13 (concurrent flood) is Phase 52-04 scope (per-`roundId` `asyncio.Lock`), not Phase 52-03.

## Test Plan Verification

- [x] **SC#1 (MCP half):** `test_agents_list_returns_json` — drops test-coordinator fixture YAML into redirected `~/.hermes/agents/`, invokes `agents_list` closure, asserts `count: 1` with `name="test-coordinator"`. PASS.
- [x] **SC#2 (lifecycle):** `test_lifecycle_round_trip` — open → opinion → submit against synthetic 2-panelist round table; final state file has `status="completed"` and `status != "in_progress"` (atomicity). PASS.
- [x] **SC#4 (serial — half-scoped to 52-04):** Not in 52-03 scope, but `test_submit_round_table_result_idempotent` verifies the related idempotency invariant. SC#4 proper (concurrent `get_agent_opinion` rejection) lands in Phase 52-04.
- [x] **Tool census:** `test_all_seven_v11_tools_registered` + `test_no_v10_stale_names_substituted` + `test_total_tool_count_is_seventeen` guard the locked tool list.
- [x] **Memory stubs:** `test_memory_retrieve_scoped_stub_via_tool` + `test_memory_submit_record_stub_via_tool` verify the exact `phase53_not_implemented` payloads.
- [x] **Defenses:** `test_round_table_open_rejects_too_few_panelists` (minItems=2) + `test_round_table_open_rejects_bad_project_slug` (T-52-09 path traversal).

## Self-Check

Files created (absolute paths under worktree root):
- `/data/workspace/hermes-agent/.claude/worktrees/agent-ac2d682942218e17c/agent/memory_arbitration.py` — FOUND
- `/data/workspace/hermes-agent/.claude/worktrees/agent-ac2d682942218e17c/tests/agent/test_memory_arbitration_stub.py` — FOUND
- `/data/workspace/hermes-agent/.claude/worktrees/agent-ac2d682942218e17c/tests/agent/test_mcp_serve_round_table.py` — FOUND

Files modified:
- `/data/workspace/hermes-agent/.claude/worktrees/agent-ac2d682942218e17c/mcp_serve.py` — FOUND (now 17 tools registered)

Commits verified in git log:
- `a008054b2` test(52-03): RED Task 1 — FOUND
- `4ba6444bd` feat(52-03): GREEN Task 1 — FOUND
- `62c7b8b2b` test(52-03): RED Task 2 — FOUND
- `58b98cdd5` feat(52-03): GREEN Task 3 — FOUND

## Self-Check: PASSED
