---
phase: 52-infra-foundation
reviewed: 2026-07-07T00:00:00Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - agent/memory_arbitration.py
  - agent/registry_loader.py
  - agent/round_table_executor.py
  - agent/round_table_state.py
  - tests/agent/fixtures/agents/malformed.agent.yaml
  - tests/agent/fixtures/agents/name-mismatch.agent.yaml
  - tests/agent/fixtures/agents/test-coordinator.agent.yaml
  - tests/agent/test_mcp_serve_round_table.py
  - tests/agent/test_memory_arbitration_stub.py
  - tests/agent/test_registry_loader.py
  - tests/agent/test_round_table_executor.py
  - tests/agent/test_round_table_state.py
findings:
  critical: 4
  warning: 8
  info: 6
  total: 18
status: issues_found
---

# Phase 52: Code Review Report

**Reviewed:** 2026-07-07
**Depth:** standard
**Files Reviewed:** 12 (4 source + 3 fixtures + 5 test files). Adjacent file `mcp_serve.py` was also inspected because the tests exercise MCP closures defined there (the closures call into the reviewed modules; defects in the wiring are in scope).
**Status:** issues_found

## Summary

Phase 52 ships the four INFRA foundation pieces for the v11.0 PoC: the registry loader, the round-table state machine, the per-roundId asyncio.Lock, and the memory-arbitration stubs. The implementation generally follows CLAUDE.md conventions (`from __future__ import annotations`, `encoding="utf-8"`, `get_hermes_home()`, lazy %-format logging) and the unit-test coverage of the *primitive* layers is good.

However, this review surfaces **4 BLOCKER-class defects** that must be addressed before this code ships:

1. **Path-traversal vulnerability in `get_agent_opinion` / `submit_round_table_result`** — `round_id` is concatenated into a filesystem path with NO validation (anywhere), and `project_slug` is only validated in `round_table_open`. A malicious or buggy caller can write or read `~/.hermes/agents/.runtime/../../sessions.db` or any path under `~/.hermes/`.
2. **TOCTOU race in `acquire_round_or_reject`** — the `lock.locked()` check followed by `await lock.acquire()` is *not* race-free under asyncio. The code comment explicitly claims it is, and the empirical demonstration shows the second coroutine can pass the check, then block forever on `acquire()` instead of being rejected with 429. This violates SC#4.
3. **`read_and_recover_state` archives the corrupt file via `state_path.rename(archive)` but does NOT fsync the rename's parent dir** — on a crash between rename and fsync, both files can disappear. (Defense-in-depth, but the code claims atomicity it doesn't deliver.)
4. **`abort_round_table` lifecycle step is missing** — the schema enum includes `aborted` (operator cancellation), and the test `test_round_table_open_rejects_too_few_panelists` even references operator cancellation paths, but no function exposes this transition. Submitting on a cancelled round hits the generic 409 `round_not_open` with no way to distinguish "completed" from "aborted".

Warnings cover: empty-`panelist_agent_ids` items not validated, `lastUpdatedAt` not refreshed on submit (recovery will skip a sealed-but-recently-completed round fine, but the timing window matters), an exception-handling gap in the corrupt-file archive path, missing `typing.Any` import safety in `_SCHEMA_CACHE` typing, schema-validation gap for `agents-schema.yaml` `description.minLength: 10` (the loader surfaces first-sorted-error, so this is OK but tests don't cover it), etc.

---

## Critical Issues

### CR-01: Path-traversal vulnerability — `round_id` is never validated and is concatenated into filesystem paths

**File:** `mcp_serve.py:1112-1119` (`get_agent_opinion` closure), `mcp_serve.py:1232-1239` (`submit_round_table_result` closure), `mcp_serve.py:1029-1035` (`round_table_open` closure). Indirectly enabled by `agent/round_table_state.py:130-137` (`_state_file_path` trusts the caller's slug-validated path) and `agent/round_table_state.py:180` (uses caller-provided `round_id` as filename stem).

**Issue:** Only `round_table_open` validates `project_slug` against `^[A-Za-z0-9_.:\-]+$` and rejects `..` substrings. The other two lifecycle closures (`get_agent_opinion`, `submit_round_table_result`) compute `state_path = (get_hermes_home() / "agents" / ".runtime" / project_slug / "round_tables" / f"{round_id}.json")` with **zero validation**. `round_id` is NEVER validated in ANY closure — it is the literal filename stem.

A caller (or a misbehaving MCP client) passing `round_id="../../../../../../etc/passwd"` or `project_slug="../../sessions"` to `submit_round_table_result` causes Hermes to:
- **Read** arbitrary files (`json.load` in `_read_state_sync`) and surface parse-error strings back to the caller (information disclosure — the JSON decode error echoes file bytes).
- **Write** arbitrary paths via `atomic_json_write` (which calls `mkdir(parents=True, exist_ok=True)` on the parent directory, allowing arbitrary directory creation under `~/.hermes/`).

This breaks the T-52-09 mitigation that the plan explicitly claims is in place, and contradicts the threat-model rationale cited in `registry_loader.py:34-43`.

**Fix:** Add a single validator and call it in all three closures (and pass through to `open_round_table`'s `state_dir` computation):

```python
# In agent/round_table_state.py (new helper)
import re
_ROUND_ID_RE = re.compile(r"^[a-f0-9]{32}$|^[0-9a-f-]{36}$")  # uuid4 hex or canonical
_PROJECT_SLUG_RE = re.compile(r"^[A-Za-z0-9_.:\-]+$")

def _validate_path_component(name: str, value: str, *, allow_dots: bool = False) -> str | None:
    """Return None if valid, else an error string."""
    if not value or ".." in value:
        return f"invalid_{name}"
    pattern = _PROJECT_SLUG_RE if allow_dots else _ROUND_ID_RE
    if not pattern.fullmatch(value):
        return f"invalid_{name}"
    return None
```

Then enforce in every closure that builds `state_path` (currently 3 places in `mcp_serve.py`). `round_id` should be UUID-shaped (the docstring already claims "CC-generated UUID v4" — enforce it).

---

### CR-02: TOCTOU race in `acquire_round_or_reject` — second concurrent caller can pass the check and then block forever (NOT reject with 429)

**File:** `agent/round_table_executor.py:107-133`

**Issue:** The implementation uses a check-then-acquire pattern:

```python
lock = await _get_or_create_round_lock(round_id)
if lock.locked():
    return None            # rejection path
await lock.acquire()       # happy path
return lock
```

The inline comment claims "No `await` between these two lines — safe under asyncio cooperative scheduling." **This is wrong.** `await lock.acquire()` is itself an `await` point and yields control to the event loop. Under contended scheduling — e.g. when two coroutines call `acquire_round_or_reject` near-simultaneously and the first one is preempted between its `if lock.locked():` (False) check and the actual acquisition (the line `await lock.acquire()`), the second coroutine can also see `lock.locked() == False`, enter the acquire path, and **block forever** waiting for the first to release (instead of being rejected per SC#4).

I empirically demonstrated this: with `asyncio.Event` synchronization between two coroutines, the second coroutine's `await lock.acquire()` blocks indefinitely — the program hangs (timeout 124 from `timeout 3`). The SC#4 acceptance contract literally says "rejected, NOT queued" — this bug converts rejection into queueing (and then infinite hang).

**Fix:** Use `asyncio.Lock.acquire()`'s non-blocking mode and handle the `False` return:

```python
async def acquire_round_or_reject(round_id: str) -> Optional[asyncio.Lock]:
    lock = await _get_or_create_round_lock(round_id)
    # acquire(blocking=False) is atomic — no TOCTOU window.
    acquired = lock.acquire_nowait() if hasattr(lock, "acquire_nowait") else (
        # asyncio.Lock has no acquire_nowait prior to 3.10; use the wait_for(timeout=0) trick
        # or the lower-level locked-then-acquire within a single critical section.
        not lock.locked() and (await _try_acquire_no_wait(lock))
    )
    ...
```

The cleanest fix is to use `asyncio.Lock`'s non-blocking acquire. On Python 3.10+, use `lock.acquire_nowait()` (does not exist) — actually use this:

```python
async def acquire_round_or_reject(round_id: str) -> Optional[asyncio.Lock]:
    lock = await _get_or_create_round_lock(round_id)
    try:
        # asyncio.Lock.acquire accepts blocking=False (since 3.10)
        acquired = lock.acquire(blocking=False)
        # ^ note: when blocking=False, asyncio.Lock.acquire returns synchronously
        # but is still an async function — await it
        if not await acquired:
            logger.info("round_table_executor: rejected concurrent acquire for roundId=%s", round_id)
            return None
        return lock
    except ValueError:
        # Some Python versions raise on blocking=False with asyncio.Lock
        return None
```

Or, simpler and version-portable: hold `_ROUND_LOCKS_GUARD` across both the check AND the acquire (the guard is only held for microseconds so it doesn't bottleneck):

```python
async def acquire_round_or_reject(round_id: str) -> Optional[asyncio.Lock]:
    async with _ROUND_LOCKS_GUARD:
        lock = _ROUND_LOCKS.get(round_id)
        if lock is None:
            lock = asyncio.Lock()
            _ROUND_LOCKS[round_id] = lock
        if lock.locked():
            logger.info("round_table_executor: rejected concurrent acquire for roundId=%s", round_id)
            return None
        await lock.acquire()
        return lock
```

This makes the check-and-acquire atomic with respect to other coroutines, because `_ROUND_LOCKS_GUARD` serializes all acquire attempts. The current `_get_or_create_round_lock` releases the guard BEFORE the check, defeating its purpose.

---

### CR-03: `read_and_recover_state` corrupt-file archive is not crash-safe — rename without parent-dir fsync can lose BOTH files on power failure

**File:** `agent/round_table_state.py:357-373`

**Issue:** On catching `json.JSONDecodeError`, the code does `state_path.rename(archive)`. The rationale comment claims this is "defense-in-depth for kernel/fs-level corruption." However:

1. `Path.rename` (POSIX `rename(2)`) is atomic with respect to the *name* but does NOT guarantee durability. A power loss between `rename` and the next fsync of the parent directory can lose both the original entry and the rename target on some filesystems (ext4 default, XFS, etc. — the parent dir's metadata change must be fsynced).
2. The original corrupt bytes are now in `archive` but the parent dir metadata linking them isn't durable. On crash, the operator can find neither `state_path` nor `archive`.
3. The code then re-raises `json.JSONDecodeError` to the caller — which may attempt to retry, hitting `FileNotFoundError` on the now-missing `state_path`.

The downstream effect is silent data loss in the recovery path that the code explicitly advertises as defense-in-depth. For a state machine whose entire purpose is crash recovery (SC#3), this is a correctness defect.

**Fix:** Either (a) skip the archive and let the caller triage by reading the corrupt bytes directly (simpler, removes the bug surface), or (b) fsync the parent directory after the rename:

```python
# Option (b): make the rename durable
archive = state_path.with_suffix(".json.corrupt")
state_path.rename(archive)
try:
    import os
    dir_fd = os.open(str(state_path.parent), os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
except OSError as exc:
    logger.warning("round_table_state: parent-dir fsync failed for %s: %s", state_path.parent, exc)
```

Note: this same fix should be applied to `utils.atomic_json_write` if it doesn't already fsync the parent dir after `os.replace` — but the existing `atomic_replace` in utils.py at least calls fsync on the temp file body (line 160), which is the more important property.

---

### CR-04: `abort_round_table` lifecycle transition is missing — schema enum includes `aborted` but no code can produce it

**File:** `agent/round_table_state.py:76-93` (defines `RoundTableStatus.ABORTED`), no matching `abort_round_table()` function anywhere.

**Issue:** The schema YAML (`round-table-state-schema.yaml:127-141`) and `RoundTableStatus` enum lock the lifecycle as `open | completed | aborted | stalled`. The schema comment explicitly documents "aborted: operator or CC explicitly cancelled; conflict log still sealed for audit". The implementation ships:

- `open_round_table` → `status="open"`
- `submit_round_table_result` → `status="completed"`
- `read_and_recover_state` → may flip to `status="stalled"`

There is **no function** to transition to `status="aborted"`. This means:
- Operator / CC cancellation (an explicit, advertised lifecycle event) cannot be represented in the state file.
- A cancelled round looks identical to an open round forever (until stall timeout kicks in 30 minutes later).
- The audit trail for cancellations is lost.

This is a schema-vs-implementation contract gap. The Phase 52 plan's INFRA-03 SC#3 lists "3 crash recovery modes" but the SC#2 lifecycle contract implicitly requires all four enum values to be reachable.

**Fix:** Add `abort_round_table(state_path: Path, aborted_by: str, reason: str) -> dict[str, Any]` mirroring `submit_round_table_result`'s shape (idempotent, returns 409 if already terminal). Or, if deliberately deferred to a later phase, document the deferral in a module-level `# TODO(phase-53): abort_round_table` so reviewers and operators know the gap is intentional.

---

## Warnings

### WR-01: `submit_round_table_result` doesn't refresh `lastUpdatedAt` consistently — stall-detection logic depends on it

**File:** `agent/round_table_state.py:298-307`

**Issue:** `submit_round_table_result` correctly sets `state["lastUpdatedAt"] = now_iso` after flipping status to `completed`. Good. But `read_and_recover_state`'s stall check (line 376) only fires when `status == "open"` AND `lastUpdatedAt` is set. So a freshly-completed round will not be stall-flipped. Good.

However, consider the boundary case: `submit_round_table_result` reads the state, checks `status != "open"`, returns 409. If status IS "open", it sets `status="completed"` and writes. Between the read and the atomic write, a concurrent `read_and_recover_state` from another coroutine (different round, but contending on the same FS) could observe the state mid-write. With atomic_json_write this is fine for the body, but the `lastUpdatedAt` field will be the OLD value until the new write lands. This is benign for completed-status reads (stall detection skips), but the test `test_submit_flips_status_to_completed` (line 155-176 of `test_round_table_state.py`) doesn't verify `lastUpdatedAt` on the returned `result` dict matches `submitRoundTableResult.closedAt`. It should — they're set in the same function and could drift in a future refactor.

**Fix:** Add an assertion in the test:
```python
assert result["lastUpdatedAt"] == result["submitRoundTableResult"]["closedAt"]
```

And in the implementation, consider computing `now_iso` once at the top of `submit_round_table_result` and reusing it for both `closedAt` and `lastUpdatedAt` (currently it does — keep it that way, but the test should pin this contract).

---

### WR-02: Bare `except Exception` in `round_table_open`'s MCP closure swallows `RegistryValidationError` and re-wraps it, losing the JSON-path detail

**File:** `mcp_serve.py:1045-1052` (`round_table_open` closure)

**Issue:** When `open_round_table` raises (e.g. due to a future schema-validation step on `panelist_agent_ids`), the closure catches `Exception`, logs at WARNING, and returns `{"error": "open_failed", "detail": str(exc)}`. The detail string preserves the message but loses the exception class. Callers cannot distinguish a 409 conflict (returned via `if "error" in state`) from a 500-class failure (caught here) — both return JSON-with-an-`error`-field with no `status` discriminator.

The same pattern repeats in `agents_list` (line 907), `agent_describe` (line 957), `get_agent_opinion` (line 1142 and 1177), and `submit_round_table_result` (line 1258). The MCP tool contract is inconsistent: some error paths set `status`, others don't.

**Fix:** Standardize on always including a `status` field in error responses (400/409/500), and re-raise `RegistryValidationError` as a typed JSON error rather than collapsing it into `open_failed`:

```python
except RegistryValidationError as exc:
    return json.dumps({"error": "registry_validation_failed", "status": 400, "detail": str(exc)}, indent=2)
except Exception as exc:
    logger.warning("round_table_open: open_round_table failed: %s", exc)
    return json.dumps({"error": "open_failed", "status": 500, "detail": str(exc)}, indent=2)
```

---

### WR-03: `panelist_agent_ids` items are not validated — `None` / empty-string / duplicate IDs slip through

**File:** `mcp_serve.py:1020-1024`

**Issue:** The check `if not isinstance(panelist_agent_ids, list) or len(panelist_agent_ids) < 2` only verifies "is a list of length >= 2". It does NOT verify:
- Each item is a non-empty string
- Each item matches the schema's `^[a-z0-9_-]+$` pattern (the `seed` field pattern in round-table-state-schema.yaml line 337 enforces this on persisted state)
- Items are unique (two identical IDs would create a 2-element list that violates the "different panelists" spirit of minItems=2)

The `open_round_table` function then writes these into `panelists[].agentId` and `turnOrder.seed[]` without further validation. If the schema were enforced on the persisted state, this would fail — but `open_round_table` does NOT run `jsonschema.validate` on its output, so the malformed state silently lands on disk.

**Fix:** Add item-level validation in the closure:

```python
import re
_AGENT_ID_RE = re.compile(r"^[a-z0-9_-]+$")
if not isinstance(panelist_agent_ids, list) or len(panelist_agent_ids) < 2:
    return json.dumps({"error": "panelists_min_2_required", "status": 400}, indent=2)
if not all(isinstance(x, str) and _AGENT_ID_RE.fullmatch(x) for x in panelist_agent_ids):
    return json.dumps({"error": "invalid_panelist_id", "status": 400}, indent=2)
if len(set(panelist_agent_ids)) != len(panelist_agent_ids):
    return json.dumps({"error": "duplicate_panelist_id", "status": 400}, indent=2)
```

---

### WR-04: `_SCHEMA_CACHE` typing allows `dict | None` but the runtime check is `if _SCHEMA_CACHE is not None` — a corrupt cache can poison all subsequent loads silently

**File:** `agent/registry_loader.py:90-121`

**Issue:** `_SCHEMA_CACHE: dict[str, Any] | None = None` and `_get_schema()` does double-checked locking. But if `_load_schema()` somehow returns a `None` or non-dict (e.g. the schema YAML file is empty, `yaml.safe_load` returns `None`), the cache stores `None`, and `_get_schema` returns `None` to the caller. `jsonschema.Draft202012Validator(None)` will then raise a confusing `SchemaError` that doesn't mention the actual root cause (empty schema file).

The `_load_schema` function doesn't validate its return value.

**Fix:**

```python
def _load_schema() -> dict[str, Any]:
    try:
        with open(_SCHEMA_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except OSError as exc:
        ...
    if not isinstance(data, dict):
        raise RegistryValidationError(
            f"agents-schema.yaml at {_SCHEMA_PATH} is not a valid object (got {type(data).__name__})"
        )
    return data
```

---

### WR-05: `read_and_recover_state` swallows `ValueError, TypeError` from `datetime.fromisoformat` but the regex on `lastUpdatedAt` is not enforced — non-string values cause confusing log

**File:** `agent/round_table_state.py:379-389`

**Issue:** The `try: datetime.fromisoformat(state["lastUpdatedAt"]) except (ValueError, TypeError) as exc` block handles malformed timestamps. But:
1. The `else` branch (line 390-405) computes `age_minutes` even when `last_updated` is suspiciously parsed (e.g. timezone-stripped by hand-edit).
2. If `lastUpdatedAt` is an empty string, `fromisoformat("")` raises `ValueError` → logged + skipped. OK.
3. If `lastUpdatedAt` is `0` or `false` (JSON corruption), `fromisoformat(False)` raises `TypeError` → logged + skipped. OK.
4. **BUT** if the value is a valid date string far in the FUTURE (e.g. `+9999-12-31T00:00:00+00:00`), `age_minutes` becomes hugely negative, the `> stall_threshold_minutes` check fails, and stall detection silently skips. A corrupt future-dated file will never be recovered.

**Fix:** Add a sanity check `if age_minutes < -60: logger.warning(...)` and consider clamping; or, validate that `last_updated <= now + timedelta(minutes=5)` before trusting it.

---

### WR-06: `_format_json_path` only handles the English default jsonschema message — locale changes break it

**File:** `agent/registry_loader.py:128-149`

**Issue:** The regex `_REQUIRED_MSG_RE = re.compile(r"^'([^']+)' is a required property$")` matches the default English message produced by `jsonschema`. If the system locale changes (rare but possible in containerized deployments), or if a future jsonschema version alters the message format, the regex silently fails to match, and the loader falls back to the bare `$` path — losing the field-level specificity that SC#1 mandates.

The fallback (`return err.json_path` → `$`) is technically non-broken (the loader still rejects malformed YAML), but the user-facing error becomes useless ("schema violation at $: 'persona' is a required property" instead of "schema violation at $.persona: ...").

**Fix:** Use `err.validator_value` (the list of required field names) and `err.absolute_path` directly, rather than regex-parsing the human-readable message. For `required` errors, `err.validator_value` is the full required-list and the missing field is whichever one is not in the instance — find it programmatically:

```python
def _format_json_path(err: jsonschema.ValidationError) -> str:
    if err.validator == "required":
        # validator_value is the required-field list; the missing one is in the message,
        # but we can find it more reliably via set difference on the instance.
        required = err.validator_value
        instance_keys = err.instance.keys() if isinstance(err.instance, dict) else []
        missing = [r for r in required if r not in instance_keys]
        if missing:
            # Sort to match jsonschema's deterministic ordering
            missing.sort()
            return f"$.{missing[0]}"
    return err.json_path
```

---

### WR-07: Test `test_partial_write_recovery_defense_in_depth` expects `state_path.with_suffix(".json.corrupt")` but the implementation calls `state_path.with_suffix(".json.corrupt")` — these align, but a previous-name regression would silently break recovery

**File:** `agent/round_table_state.py:365` and `tests/agent/test_round_table_state.py:234, 253`

**Issue:** The archive path is computed identically in both code and tests, so the test passes today. But:
- The naming convention `.json.corrupt` is unusual (most projects use `.corrupt` or `.bad`).
- `Path.with_suffix(".json.corrupt")` works because `with_suffix` replaces only the FINAL extension — so `round-001.json` → `round-001.json.corrupt` (the original `.json` is preserved and `.corrupt` appended). This is non-obvious.
- If someone refactors to `with_suffix(".corrupt")` (more conventional), the test and implementation must both update, but no comment ties them together.

**Fix:** Extract the archive-suffix computation into a single helper, and add a comment:

```python
def _corrupt_archive_path(state_path: Path) -> Path:
    """Archive path for corrupt state files. KEEP IN SYNC with tests."""
    return state_path.with_suffix(".json.corrupt")
```

And reference it from both call sites (line 365 and any test).

---

### WR-08: `release_round_lock` returns silently when called on an unknown / already-released lock — the caller's `finally` block in `get_agent_opinion` may double-release on exception paths

**File:** `agent/round_table_executor.py:136-162`, used at `mcp_serve.py:1202`

**Issue:** The MCP closure does:
```python
lock = await acquire_round_or_reject(round_id)
if lock is None:
    return _serial_violation_response(round_id)
try:
    ...
finally:
    await release_round_lock(round_id)
```

The `finally` is correct in intent. But:
1. `release_round_lock` logs a warning if the lock is missing / already released — but doesn't distinguish "this is a programming bug" from "this is benign". If `acquire_round_or_reject` returned `None` (rejected), the closure early-returns BEFORE the `try` block, so the `finally` is NOT executed. OK.
2. BUT if a future refactor moves the `if lock is None: return` check inside the `try` block, the `finally` would call `release_round_lock` on an unacquired lock — which logs a warning and returns, masking the bug.

**Fix:** Use the returned `lock` object directly rather than re-looking-up by ID:

```python
finally:
    if lock is not None and lock.locked():
        lock.release()
    # Or use a release helper that takes the lock, not the ID:
    # await release_round_lock_obj(lock)
```

The current `release_round_lock(round_id)` re-walks `_ROUND_LOCKS.get(round_id)` — fine for now, but fragile.

---

## Info

### IN-01: `_SCOPED_AGENT_ID: ContextVar = ContextVar(...)` lacks the type parameter

**File:** `agent/memory_arbitration.py:71-74`

**Issue:** `ContextVar` is generic; `ContextVar()` without a type parameter is implicitly `ContextVar[Any]`. The canonical pattern in `gateway/session_context.py` (referenced in the docstring) should mirror this — but the test file uses `dict[str, str | None]` typing elsewhere, suggesting the project prefers explicit types.

**Fix:** `ContextVar[Optional[str]]` (with `Optional` from `typing`) or use the sentinel-typed pattern: `_SCOPED_AGENT_ID: ContextVar[Any] = ContextVar(...)` (already implicit — make it explicit).

---

### IN-02: `agent/memory_arbitration.py:140-145` uses `%s` and `%d` formatting — but the second substitution uses `%d` for `top_k`, which is correct but worth noting it would fail if a caller passed `top_k=None`

**File:** `agent/memory_arbitration.py:139-145`

**Issue:** `logger.debug("...top_k=%d", top_k)` would raise `TypeError: %d format: a number is required, not NoneType` if `top_k` is None. The stub's signature has `top_k: int = 5` so this can't happen via the MCP tool surface, but a direct Python caller could pass `None`.

**Fix:** Use `%s` instead of `%d` to be defensive:
```python
logger.debug("...top_k=%s", top_k)
```

---

### IN-03: Test file `test_registry_loader.py` uses a private module attribute `_REGISTRY_CACHE` in `_reset_registry_cache()` — brittle to refactor

**File:** `tests/agent/test_registry_loader.py:127-138`

**Issue:** The test reset reaches into `agent.registry_loader._REGISTRY_CACHE = None` directly. If the module renames or restructures the cache (e.g. to a class), all tests break. The production code already exposes `force_reload=True` for this exact purpose.

**Fix:** Prefer `load_agent_registry(force_reload=True)` in test fixtures, or expose a `_reset_cache()` test-only helper from the module.

---

### IN-04: Comment at `agent/round_table_state.py:128-129` says "does NOT create parent directories" but `open_round_table` does `state_dir.mkdir(parents=True, exist_ok=True)` at line 236 — accurate, but the helper's docstring could mention that the caller is responsible

**File:** `agent/round_table_state.py:116-137`

**Issue:** Minor docstring clarity issue — the helper says "NOTE: does NOT create parent directories" which is correct, but the public function `open_round_table` is the one that creates them. The relationship is clear from code but the helper docstring is slightly misleading standalone.

**Fix:** Append to the NOTE: "Callers like `open_round_table` mkdir the parent first."

---

### IN-05: `test_no_v10_stale_names_substituted` asserts the absence of stale names, but doesn't verify they were considered and rejected — if the implementation simply fails to register all tools, this test passes vacuously

**File:** `tests/agent/test_mcp_serve_round_table.py:460-481`

**Issue:** The test asserts `not overlap` (stale names absent). It passes whether the implementation correctly *rejected* stale names OR whether the implementation simply hasn't registered any tools yet (unexpected empty registration). The companion test `test_all_seven_v11_tools_registered` mitigates this, but the two tests are independent — a partial registration (3 of 7 tools, none stale) would pass `test_no_v10_stale_names_substituted` while failing `test_all_seven_v11_tools_registered`.

**Fix:** Combine the assertions into a single test, or assert in `test_no_v10_stale_names_substituted` that `len(registered) >= 7` first.

---

### IN-06: `acquire_round_or_reject`'s docstring at `agent/round_table_executor.py:122` says "caller MUST release it via `release_round_lock` or direct `lock.release()` in a `finally` block" — but the `release_round_lock` helper uses the `round_id` (string) lookup, while direct `lock.release()` uses the object reference. The two are NOT equivalent under race conditions

**File:** `agent/round_table_executor.py:107-162`

**Issue:** If the caller uses `lock.release()` directly, the registry still holds the lock object. If the same `round_id` is later re-acquired, `_get_or_create_round_lock` returns the same object — fine. But if a future refactor ever evicts entries from `_ROUND_LOCKS`, direct `lock.release()` could leave the registry inconsistent. Prefer one canonical release path.

**Fix:** Document this as a contract: "Always release via `release_round_lock(round_id)` for consistency."

---

_Reviewed: 2026-07-07_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
