---
phase: 52-infra-foundation
plan: 02
subsystem: round-table-state
tags: [round-table, state-machine, atomic-write, crash-recovery, infra-03]
requires:
  - "52-01 (INFRA-01 registry loader — sibling module; same wave, no code dependency)"
provides:
  - "agent/round_table_state.py — RoundTableStatus enum + open_round_table / append_turn / submit_round_table_result / read_and_recover_state lifecycle primitives"
  - "tests/agent/test_round_table_state.py — 10 tests covering lifecycle + 3 crash-recovery modes + schema-enum authority"
affects:
  - "Phase 52-03 (INFRA-02 MCP tools) composes these primitives into 7 MCP tools"
  - "Phase 52-04 (INFRA-04 serial executor) wraps append_turn in per-roundId asyncio.Lock"
  - "Phase 53 (creative slice) calls round_table_open / append_turn via MCP tools"
tech-stack:
  added: []
  patterns:
    - "atomic_json_write (utils.py:111) — temp + fsync + os.replace for all state mutations"
    - "dataclass-as-state idiom (agent/turn_retry_state.py) — here adapted to plain dict for schema-faithful camelCase emission"
    - "enum.Enum with str mixin (RoundTableStatus(str, Enum)) — value-level equality with schema YAML strings"
    - "defense-in-depth read-time recovery (archive corrupt file + re-raise)"
    - "stall detection via lastUpdatedAt age check (recovery modes b/c)"
key-files:
  created:
    - agent/round_table_state.py
    - tests/agent/test_round_table_state.py
  modified: []
decisions:
  - "Used dict[str, Any] (not dataclass) for state representation — RESEARCH.md canonical skeleton uses dict, avoids snake_case→camelCase serialization drift"
  - "Minimal PanelistSnapshot placeholders (personaSha256='0'*64, tools=[], fitnessScore=null) are schema-valid; 52-03 MCP tools enrich from registry at open time"
  - "Default stall_threshold_minutes=30 per schema YAML default + 05-POC-PLAN.md"
  - "read_and_recover_state logs + skips stall detection on malformed lastUpdatedAt rather than raising — fail-open for read paths"
metrics:
  duration: "3m56s"
  completed: "2026-07-07"
  tasks: 2
  files: 2
  tests_added: 10
---

# Phase 52 Plan 02: Round-Table State Machine Summary

One-liner: Atomic-persistence round-table state machine with 3 crash-recovery modes (partial-write archive, mid-turn stall flip, orphaned session recovery) wired to the schema-locked `open | completed | aborted | stalled` enum.

## What Was Built

### `agent/round_table_state.py`
Round-table lifecycle primitives + crash-recovery read for INFRA-03.

- **`RoundTableStatus(str, Enum)`** — 4 values verbatim from `round-table-state-schema.yaml:127-141`. Explicit docstring cites the schema YAML as authority and warns against the stale `in_progress / closed` shorthand from CONTEXT.md prose.
- **`open_round_table(state_dir, round_id, project_id, question, panelist_agent_ids, caller)`** — creates `{round_id}.json` with `status="open"`. Idempotent: duplicate open returns `{"error": "round_already_open", "status": 409}` instead of mutating. Writes via `atomic_json_write` (temp + fsync + os.replace). Constructs minimal schema-valid PanelistSnapshot list (52-03 enriches from registry).
- **`append_turn(state_path, turn)`** — atomic read-modify-write of a Turn entry; bumps `lastUpdatedAt`.
- **`submit_round_table_result(state_path, conclusion, cited_memories, closed_by)`** — terminal transition to `status="completed"`; adds `submitRoundTableResult` block. Idempotent: second submit returns 409.
- **`read_and_recover_state(state_path, *, stall_threshold_minutes=30)`** — handles 3 failure modes:
  - (a) Partial-write → archive to `.json.corrupt` + re-raise `json.JSONDecodeError` (defense-in-depth; `atomic_json_write` guarantees no partial body)
  - (b) Mid-turn crash → `status="open"` + `lastUpdatedAt > threshold` → flip to `"stalled"` via atomic write
  - (c) Orphaned session → same recovery path as (b)
- **`RoundTableStateError`** — exception class for invariant violations (exported but unused in v1 — reserved for future panelistId-mismatch checks).
- **`_state_file_path(project_slug, round_id)`** — helper returning canonical path `~/.hermes/agents/.runtime/{slug}/round_tables/{round_id}.json`. The `agents/` parent is load-bearing per schema YAML header + `06-CROSS-REPO-IMPACT.md §5.1` (some informal docs omit it).

### `tests/agent/test_round_table_state.py`
10 tests in 3 classes:

- **`TestRoundTableLifecycle`** (5 tests) — open creates file at correct path with `status="open"`; duplicate open returns 409; append_turn grows turns list + atomic write persists; submit flips to `completed`; second submit returns 409.
- **`TestCrashRecovery`** (4 tests) — SC#2 atomicity (interrupted submit archives corrupt file + raises), SC#3a partial-write (defense-in-depth), SC#3b mid-turn crash (2-hour-old `lastUpdatedAt` flipped to `stalled`), SC#3c orphaned session (90-min-old, default threshold).
- **`TestRoundTableStatusEnum`** (1 test) — explicit guard that `in_progress` and `closed` are NOT in the enum values.

Tests use the autouse `_hermetic_environment` fixture (`tests/conftest.py:328`) for HERMES_HOME redirection — no manual env var manipulation needed.

## Verification

```
$ pytest tests/agent/test_round_table_state.py -x -v
============================= 10 passed in 0.39s ==============================
```

All plan acceptance criteria verified:
- Module imports cleanly: `from agent.round_table_state import open_round_table, append_turn, submit_round_table_result, read_and_recover_state, RoundTableStatus, RoundTableStateError; print('ok')` → `ok`
- Status enum: `['open', 'completed', 'aborted', 'stalled']` (no `in_progress` / `closed`)
- All 10 tests pass
- Partial-write test archives to `.json.corrupt` before raising
- Mid-turn crash test returns `status=="stalled"`
- State files use camelCase keys (`roundId`, `projectId`, `lastUpdatedAt`, `submitRoundTableResult`)
- State file path nests under `agents/.runtime/{slug}/round_tables/` (verified via `assert "agents" in state_path.parts`)
- `ruff check agent/round_table_state.py` exits 0
- Combined regression: `pytest tests/agent/test_registry_loader.py tests/agent/test_round_table_state.py -x` → 20/20 pass

## Deviations from Plan

None — plan executed exactly as written. Two Write-tool operations initially landed in the main repo instead of the worktree (worktree-path-safety issue #3099); both were caught and moved to the worktree before commit. No code or test changes resulted.

## Known Stubs

| Stub | File | Line | Reason | Resolved By |
|------|------|------|--------|-------------|
| `personaSha256="0"*64` placeholder in PanelistSnapshot | agent/round_table_state.py | open_round_table | Schema-valid zero-hash; the registry layer (52-01 INFRA-01) provides real persona hashes | Phase 52-03 MCP tools enrich panelists from registry at open time |
| `tools=[]` empty list in PanelistSnapshot | agent/round_table_state.py | open_round_table | Schema-valid empty list; agent tools come from `~/.hermes/agents/*.agent.yaml` | Phase 52-03 MCP tools enrich panelists from registry at open time |

These are intentional schema-valid placeholders, not feature gaps. They satisfy the `round-table-state-schema.yaml $defs.PanelistSnapshot` required fields with safe defaults; 52-03's `round_table_open` MCP tool enriches them from the registry before calling this module's `open_round_table`.

## Threat Flags

None. The new filesystem path `~/.hermes/agents/.runtime/{slug}/round_tables/{round_id}.json` is documented in the plan's threat model (T-52-06 partial-write, T-52-07 orphaned session) and mitigated by `atomic_json_write` + `read_and_recover_state`. No new network endpoints, auth paths, or schema changes at trust boundaries beyond what the threat register covers.

## Self-Check: PASSED

- File `agent/round_table_state.py` exists at `/data/workspace/hermes-agent/.claude/worktrees/agent-a86e0d95bd4fb3be2/agent/round_table_state.py`
- File `tests/agent/test_round_table_state.py` exists at `/data/workspace/hermes-agent/.claude/worktrees/agent-a86e0d95bd4fb3be2/tests/agent/test_round_table_state.py`
- Commit `ae4799bfa` (test RED) found in `git log`
- Commit `050bd5ef6` (feat GREEN) found in `git log`
- All 10 tests pass: verified via `pytest tests/agent/test_round_table_state.py -x` → `10 passed in 0.39s`
- No state file ever serializes `in_progress` or `closed` (verified by `TestRoundTableStatusEnum::test_enum_values_match_schema_yaml_exactly`)
