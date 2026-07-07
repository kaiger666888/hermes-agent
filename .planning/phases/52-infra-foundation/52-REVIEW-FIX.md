---
phase: 52-infra-foundation
fixed_at: 2026-07-07T03:30:00Z
review_path: .planning/phases/52-infra-foundation/52-REVIEW.md
iteration: 1
findings_in_scope: 10
fixed: 10
skipped: 0
status: all_fixed
---

# Phase 52: Code Review Fix Report

**Fixed at:** 2026-07-07T03:30:00Z
**Source review:** `.planning/phases/52-infra-foundation/52-REVIEW.md`
**Iteration:** 1
**Fix scope:** critical_warning (4 BLOCKER + 6 WARNING in scope; 6 INFO deferred)

**Summary:**
- Findings in scope: 10
- Fixed: 10
- Skipped: 0
- Status: all_fixed

**Test verification:**
- Phase 52 targeted suite: 71 passed (was 39 baseline; +32 new tests across the 10 fixes)
- Ruff: `All checks passed!`
- Full agent suite: pre-existing `test_feedback_*` failures (78 failed / 65 errors) are unchanged from baseline — they predate this fix run and are unrelated to Phase 52.

## Fixed Issues

### CR-01: Path-traversal vulnerability — `round_id` is never validated

**Files modified:** `agent/round_table_state.py`, `mcp_serve.py`, `tests/agent/test_mcp_serve_round_table.py`
**Commit:** `eba8753cd`
**Applied fix:** Added `validate_round_id` (UUID v4 hex / canonical UUID, no `..` substring, no path separators) + `validate_project_slug` (1-64 chars of `[A-Za-z0-9_.:-]`, no `..`, no path separators) helpers in `agent/round_table_state.py`. Applied at the top of all 3 round-table MCP closures (`round_table_open`, `get_agent_opinion`, `submit_round_table_result`) so neither `round_id` nor `project_slug` reaches the filesystem concatenated into a path without passing the strict allow-list. Added 4 new tests (3 path-traversal rejection tests across the 3 closures + 1 non-UUID round_id guard).

### CR-02: TOCTOU race in `acquire_round_or_reject`

**Files modified:** `agent/round_table_executor.py`, `tests/agent/test_round_table_executor.py`
**Commit:** `27da085a5`
**Applied fix:** Holds `_ROUND_LOCKS_GUARD` across BOTH the registry lookup AND the `await lock.acquire()` so the check-and-acquire is atomic with respect to other dispatchers. Previously the await inside `lock.acquire()` was itself an await point that yielded to the event loop, allowing a racing coroutine to pass the `lock.locked()` check then block forever on its own `await lock.acquire()`. Added 2 async regression tests using `asyncio.gather` + `asyncio.wait_for(timeout=2.0)` (a regression hangs the test past the timeout): 2-way race + 3-way stress.

### CR-03: Non-durable rename in corrupt-file recovery

**Files modified:** `agent/round_table_state.py`, `tests/agent/test_round_table_state.py`
**Commit:** `ed6096dae`
**Applied fix:** Added `_fsync_parent_dir(dir_path)` helper that opens the parent directory, calls `os.fsync(dir_fd)`, and closes the fd (wrapped in `try/except OSError` because directory fsync is Linux-supported but not universally). Called immediately after `state_path.rename(archive)` in the corrupt-file recovery branch of `read_and_recover_state`. Without this, a power-loss crash between rename and the implicit dir-metadata flush could lose BOTH files on ext4/XFS default mount options. Added `test_corrupt_archive_fsyncs_parent_dir` that monkeypatches `os.fsync` and asserts ≥1 fsync call is made.

### CR-04: `abort_round_table` lifecycle transition missing

**Files modified:** `agent/round_table_state.py`, `tests/agent/test_round_table_state.py`, `.planning/research/v10-orchestrator-design/round-table-state-schema.yaml`
**Commit:** `d96650375`
**Applied fix:** Added `abort_round_table(state_path, *, reason, aborted_by) -> dict` mirroring `submit_round_table_result`'s shape but flipping status to `"aborted"`. Allowed transition: `open → aborted`. Rejects if already terminal (`completed` or `aborted`) with 409 Conflict — idempotent contract. NOT wired into MCP tools (per `02-ROUND-TABLE-PROTOCOL.md §5.0`, MCP wiring is v11.1+ scope); this is a programmatic API for operator scripts / curator hooks. Updated schema YAML with `abortRoundTable` property + `$defs.AbortRoundTable` so persisted state stays schema-valid (`additionalProperties:false` would otherwise reject the new field). 3 new tests: happy path, reject-on-completed, reject-on-already-aborted.

### WR-01: `submit_round_table_result` doesn't refresh `lastUpdatedAt` consistently

**Files modified:** `tests/agent/test_round_table_state.py`
**Commit:** `ee65cfc87`
**Applied fix:** The implementation already does the right thing (single `_now_iso()` call assigned to both `lastUpdatedAt` and `submitRoundTableResult.closedAt`). Pinned this contract in `test_submit_flips_status_to_completed` with an explicit assertion `result["lastUpdatedAt"] == result["submitRoundTableResult"]["closedAt"]` so a future refactor that computes them separately (and lets them drift) doesn't silently break `read_and_recover_state`'s stall detection during the narrow read-vs-write window.

### WR-02: Bare `except Exception` collapses `RegistryValidationError`

**Files modified:** `agent/registry_loader.py`, `mcp_serve.py`, `tests/agent/test_mcp_serve_round_table.py`
**Commit:** `742b4241f`
**Applied fix:** Added optional `json_path` + `invalid_field` attributes to `RegistryValidationError`, populated them at the schema-violation raise site in `load_one_agent_yaml`. Added typed `except RegistryValidationError as exc:` branch BEFORE the generic `except Exception` in `agents_list` / `agent_describe` / `round_table_open` closures, returning `{error: "registry_validation_failed", status: 400, detail: <msg>, json_path: <$.field>, invalid_field: <field>}`. Also added `status: 500` to the generic branches so callers can distinguish 400-class from 500-class. Added `test_agents_list_returns_typed_400_on_malformed_fixture` that drops the `malformed.agent.yaml` fixture into redirected HERMES_HOME and asserts the typed 400 + structured fields.

### WR-03: `panelist_agent_ids` items not validated (pattern / type / uniqueness)

**Files modified:** `mcp_serve.py`, `tests/agent/test_mcp_serve_round_table.py`
**Commit:** `8d4b764c0`
**Applied fix:** In `round_table_open` closure, after the `minItems=2` check, loop through `panelist_agent_ids` and verify each item is a non-empty string matching `^[a-z0-9_-]+$`; reject duplicates. Without this, None / empty-string / duplicate / uppercase IDs would silently land on disk via `open_round_table`'s `panelists[].agentId` + `turnOrder.seed` writes. 3 new tests: pattern rejection, non-string rejection, duplicate rejection.

### WR-04: `_load_schema` doesn't validate return value (empty file poisons cache)

**Files modified:** `agent/registry_loader.py`, `tests/agent/test_registry_loader.py`
**Commit:** `0ae3535fb`
**Applied fix:** After `yaml.safe_load`, assert the result is a `dict` and contains either `type` or `$schema` (the markers of a JSON Schema document). Raise `RegistryValidationError` with the path + type info on violation. Without this, an empty / YAML-null schema file would cache as `None` and silently poison every subsequent load — `Draft202012Validator(None)` raises a confusing SchemaError that doesn't mention the root cause. 3 new tests: empty file, non-dict (list), dict missing both `type` and `$schema`.

### WR-05: Future-dated `lastUpdatedAt` silently disables stall detection

**Files modified:** `agent/round_table_state.py`, `tests/agent/test_round_table_state.py`
**Commit:** `05c032a21`
**Applied fix:** In `read_and_recover_state`, added `future_skew_tolerance_minutes: int = 5` parameter. If `age_minutes < -future_skew_tolerance_minutes` (i.e. `lastUpdatedAt` is more than 5 minutes AHEAD of `now`), log warning AND flip status to stalled anyway. Without this guard, a corrupt future-dated file (hand-edit, clock skew, JSON munging) would compute a hugely negative `age_minutes`, the `> stall_threshold_minutes` check would always fail, and stall detection would be silently disabled for that file FOREVER. 2 new tests: 1-day-ahead flips to stalled, 1-minute-ahead does NOT (within tolerance — guards against false positive).

### WR-06: `_format_json_path` regex-parses the English jsonschema message

**Files modified:** `agent/registry_loader.py`, `tests/agent/test_registry_loader.py`
**Commit:** `b6a81344e`
**Applied fix:** Replaced the `_REQUIRED_MSG_RE` regex (which matched the literal English string `"'X' is a required property"`) with logic that derives the path from `err.validator_value` (the required-field list) + `err.instance` (the actual object) via set difference. For non-required errors, `err.json_path` (computed by jsonschema from `absolute_path`) is used directly. Removed the now-unused `_REQUIRED_MSG_RE` + `import re`. 3 new tests in `TestFormatJsonPath`: required-error-with-French-message (would never match old regex), required-error-multiple-missing-sorted, non-required-error-uses-json_path.

## Skipped Issues

None — all 10 in-scope findings were fixed cleanly.

The 6 INFO findings (IN-01 through IN-06) are deferred per `fix_scope=critical_warning` and remain in `issues_found` status. They should be addressed in a future polish pass or v11.1 milestone.

---

_Fixed: 2026-07-07T03:30:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
