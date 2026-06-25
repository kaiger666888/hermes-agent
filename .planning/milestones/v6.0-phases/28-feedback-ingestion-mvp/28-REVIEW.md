---
phase: 28-feedback-ingestion-mvp
reviewed: 2026-06-24T14:05:00Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - agent/feedback_ingest.py
  - agent/feedback_schema.py
  - agent/feedback_snapshot.py
  - hermes_cli/cli_commands_mixin.py
  - hermes_cli/commands.py
  - hermes_cli/feedback.py
  - hermes_cli/main.py
  - tests/agent/test_feedback_ingest.py
  - tests/agent/test_feedback_schema.py
  - tests/agent/test_feedback_snapshot.py
  - tests/hermes_cli/test_feedback_cli.py
findings:
  critical: 1
  warning: 6
  info: 5
  total: 12
status: issues_found
---

# Phase 28: Code Review Report

**Reviewed:** 2026-06-24T14:05:00Z
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Reviewed the v6.0 P28 Feedback Ingestion MVP at standard depth across 11 files (3 source modules, 4 CLI/integration touchpoints, 4 test files). The implementation is well-structured and largely faithful to the RESEARCH.md pitfalls (atomic write via `utils.atomic_json_write`, 2-poll stability check, source-override anti-spoofing, sanitized `.name` for path-traversal defense). Hermes conventions are mostly honored: `encoding="utf-8"` everywhere, `get_hermes_home()` for path resolution, lazy %-logging, specific exception types with `as exc`.

One BLOCKER was found: non-serializable values in `agent.reasoning_config` / `agent.service_tier` / `agent.max_tokens` are not filtered the way `request_overrides` is, so a single bad value crashes `write_feedback_record` mid-write — defeating the atomic-write guarantee for the CLI path. Several WARNING-level issues around partial-write cleanup races, `--revised` flag parsing ambiguity, and symlinks in the inbox are documented below. FOUND-08 (no bundled SKILL.md touches) is preserved — only Hermes-core / agent / hermes_cli files were modified.

## Critical Issues

### CR-01: Non-serializable agent params crash write_feedback_record, breaking atomicity

**File:** `agent/feedback_snapshot.py:156-167`
**Issue:** `build_output_snapshot` filters non-serializable values ONLY from `request_overrides` (via `_filter_serializable`). The other three params — `max_tokens`, `reasoning_config`, `service_tier` — are read with `getattr(agent, attr, None)` and stored into `params` unfiltered. Pydantic accepts them (the field is `params: dict[str, Any]`), so the snapshot builds fine. But `write_feedback_record` → `atomic_json_write` → `json.dump` will raise `TypeError: Object of type X is not JSON serializable` mid-write when the record contains e.g. a custom dataclass or enum instance for `reasoning_config`.

This defeats the atomic-write guarantee: the atomic_json_write helper uses `tempfile.mkstemp + json.dump + os.replace`. A `TypeError` raised inside `json.dump` is caught by the `except BaseException` clause in `atomic_json_write` (which unlinks the temp file and re-raises), so no partial file appears — but the `/feedback` command then prints `Feedback failed: ...` instead of persisting the record. RESEARCH Pitfall #8 calls this out for `request_overrides`; the same risk applies to the other three params, but only `request_overrides` is filtered.

In practice, `agent.reasoning_config` is typically `dict | None`, `service_tier` is `str | None`, and `max_tokens` is `int | None` — all JSON-safe in the current codebase. But the runtime contract for these attrs is not enforced anywhere, and `request_overrides`'s filtering exists precisely because the team does not trust these shapes. The inconsistency is the bug.

**Fix:** Apply `_filter_serializable` (or an equivalent per-value check) uniformly to all four params, or wrap each non-`request_overrides` value in a try/except json.dumps probe:

```python
# agent/feedback_snapshot.py — replace the for-loop at lines 156-167
import json as _json

def _safe_param(val: Any) -> Any:
    """Coerce a param value to a JSON-safe shape; drop if not serializable."""
    try:
        _json.dumps(val)
        return val
    except (TypeError, ValueError):
        logger.debug("dropped non-serializable agent param value: %r", val)
        return None

params: dict[str, Any] = {}
for attr in ("max_tokens", "reasoning_config", "service_tier", "request_overrides"):
    val = getattr(agent, attr, None)
    if val is None:
        continue
    if attr == "request_overrides":
        if isinstance(val, dict):
            params[attr] = _filter_serializable(val)
        else:
            params[attr] = _safe_param(val)
    else:
        safe = _safe_param(val)
        if safe is not None:
            params[attr] = safe
```

This keeps the existing `request_overrides` deep-filter behavior and adds shallow safety to the other three.

## Warnings

### WR-01: Source file orphaned in inbox when post-ingest unlink fails

**File:** `agent/feedback_ingest.py:260-281`
**Issue:** After `write_feedback_record(record)` succeeds and `Path(entry.path).rename(target)` fails, the fallback path does `target.write_bytes(raw_bytes)` then `Path(entry.path).unlink()`. If `unlink()` fails (e.g. file locked on Windows, permission revoked mid-run, NFS hiccup), the source file remains in `inbox/` with the same `(mtime, size)`. The next `_scan_once` iteration hits `seen.get(key) == current` (set at line 302 after the try/except) and silently skips it — so the loop doesn't spin — but the operator sees a "stale" file in inbox that was already ingested.

The data is not lost (the snapshot is in `incoming/`), but the operator's mental model ("files in inbox/ are pending") breaks. Worse, if the operator manually deletes `incoming/` to "retry", the inbox file is NOT re-ingested (because `seen` still has the key), producing silent confusion.

**Fix:** Distinguish "ingested but not moved" from "moved" in the seen record, or attempt the unlink in a separate scan pass with a `pending_unlink` set:

```python
# After successful write_feedback_record, before setting seen[key]:
moved_ok = False
try:
    Path(entry.path).rename(target)
    moved_ok = True
except OSError as exc:
    logger.warning("kais inbox rename failed for %s: %s; falling back to copy+unlink", entry.name, exc)
    try:
        target.write_bytes(raw_bytes)
        Path(entry.path).unlink(missing_ok=True)
        moved_ok = True
    except OSError as unlink_exc:
        logger.warning(
            "kais inbox post-ingest cleanup failed for %s: %s "
            "(record was written to incoming/ — manual cleanup needed)",
            entry.name, unlink_exc,
        )
# Only mark seen if the file is gone from inbox; otherwise the next scan
# should retry the move (not the ingest — write_feedback_record is idempotent
# only if ts differs, which it won't on retry).
if moved_ok or not Path(entry.path).exists():
    seen[key] = current
    pending.pop(key, None)
```

Even simpler: log the orphan loudly (already done) and document the operator-runbook step. The current code's main flaw is the silent skip on the next scan.

### WR-02: `--revised` flag in /feedback collides with literal correction text

**File:** `hermes_cli/cli_commands_mixin.py:2324-2327`
**Issue:** `_handle_feedback_command` parses the `--revised` flag via `tail.partition("--revised")`. The partition matches the flag ANYWHERE in the tail, including inside the correction text. Examples that break:

- `/feedback bad The --revised flag is wrong` → correction becomes `"The"`, revised_output becomes `"flag is wrong"`
- `/feedback needs_work User wrote --revised in their note` → same shape

`shlex.split` is not used here (unlike `/cron`, `/background`), so quoting doesn't help — `partition` is a pure string split. The operator's intent is ambiguous in these cases, but the silent misparse is worse than an error.

**Fix:** Use `shlex.split` + explicit `--revised` argument, or require the flag to be preceded by whitespace and start the token:

```python
import shlex
try:
    tokens = shlex.split(tail)
except ValueError:
    tokens = tail.split()
revised_output = None
if "--revised" in tokens:
    idx = tokens.index("--revised")
    revised_output = " ".join(tokens[idx + 1:]).strip().strip('"').strip("'")
    tokens = tokens[:idx]
verdict = tokens[0].lower() if tokens else ""
correction = " ".join(tokens[1:]).strip()
```

This requires `--revised` to be a standalone token, matching the documented usage. Backward-compat: operators who typed `/feedback good note --revised "text"` still work because `--revised` is its own token.

### WR-03: Symlinked inbox entries are followed, not rejected

**File:** `agent/feedback_ingest.py:231-235`
**Issue:** `os.scandir` returns `DirEntry` objects whose `is_dir()` / `is_file()` follow symlinks by default. A symlink placed in `inbox-kais/` pointing to e.g. `/etc/` or a file outside the watcher tree would be:

1. `entry.is_dir()` returns True if the symlink points to a dir → `continue` (safe).
2. `entry.is_dir()` returns False (symlink to a file) → `entry.name.endswith(".json")` check passes if the link name ends in `.json` → file is read via `Path(entry.path).read_bytes()`, which follows the link.

The data is then ingested as a kais_aigc record. This is mostly safe (the data goes through JSON validation), but:

- The `rename` to `processed/` renames the symlink itself, not the target — leaving the target file orphaned at its original location and breaking any external process that created the link.
- An adversary with write access to `inbox-kais/` could link to a sensitive file (e.g. `~/.hermes/config.yaml` renamed to `secret.json`) and have the watcher ingest its contents as `output_text` in a FeedbackRecord, which then persists under `~/.hermes/skills/.feedback/incoming/`. This is a low-severity info-leak vector given the threat model assumes the operator controls the inbox, but the symlink case is undocumented.

**Fix:** Reject symlinks (or use `os.scandir(path).is_symlink()` check):

```python
for entry in os.scandir(inbox_dir):
    if entry.is_symlink():
        logger.warning(
            "kais inbox ignoring symlink %s (symlinks are not followed for safety)",
            entry.name,
        )
        continue
    if entry.is_dir():
        continue
    # ... rest unchanged
```

### WR-04: `OutputSnapshot.sha256` validator's non-str branch is unreachable / masks Pydantic errors

**File:** `agent/feedback_schema.py:168-173`
**Issue:** The validator does `if not isinstance(v, str) or not _SHA256_HEX_RE.match(v): raise ValueError(...)`. Pydantic v2 already enforces `sha256: str` at the schema level — non-str inputs raise a Pydantic `ValidationError` with a clear "Input should be a valid string" message BEFORE this validator runs. The `isinstance` check is therefore dead code, and the error message "sha256 must be 64 lowercase hex characters" misleads operators whose actual problem was a non-string input.

This is a minor correctness issue — it can't crash — but it degrades debuggability for callers like `_cmd_submit` that build the snapshot from CLI args (where a `None` could sneak through if an arg is missed).

**Fix:** Drop the isinstance check and rely on the regex (Pydantic handles the type contract):

```python
@field_validator("sha256")
@classmethod
def _sha256_is_64_hex(cls, v: str) -> str:
    if not _SHA256_HEX_RE.match(v):
        raise ValueError("sha256 must be 64 hex characters (0-9, a-f, A-F)")
    return v.lower()
```

### WR-05: `_cmd_watch` `stop_event` wiring causes double-handler install attempts

**File:** `hermes_cli/feedback.py:152-166`
**Issue:** `_cmd_watch` creates a fresh `threading.Event()` and passes it to `watch_inbox_kais(stop_event=stop_event)`. Looking at `watch_inbox_kais` (line 360): when `stop_event is None`, it creates one and installs SIGINT/SIGTERM handlers; when `stop_event is not None` (as here), it does NOT install the signal handlers. So `_cmd_watch`'s `try/except KeyboardInterrupt` is the only thing catching Ctrl+C.

That `KeyboardInterrupt` is raised by Python's default SIGINT handler during the `time.sleep(slice_sleep)` inside the watcher. The exception propagates up through `_scan_once` (no `KeyboardInterrupt` catch there — good) and the watcher's outer try/except `Exception` (KeyboardInterrupt is `BaseException`, not `Exception`, so it's NOT caught — good). So the except in `_cmd_watch` DOES fire, sets `stop_event` (which is then discarded), and returns 0.

The flow is correct, but the indirection is brittle: any future change that adds a `try/except Exception` wider net inside `watch_inbox_kais` (e.g. wrapping `_scan_once` differently) could swallow the KeyboardInterrupt path. The cleaner pattern is to NOT pass a stop_event and let the watcher install its own handlers (matching the docstring's "fresh threading.Event is created and SIGINT/SIGTERM are wired to set it" promise).

**Fix:** Either don't pass `stop_event` from `_cmd_watch` (let the watcher self-manage), or add a test asserting the KeyboardInterrupt path is reachable. Minimal fix is documentation:

```python
def _cmd_watch(args) -> int:
    """``hermes feedback watch [--interval N]``.

    Ctrl+C is caught by Python's default SIGINT handler (raised as
    KeyboardInterrupt from time.sleep inside the watcher) and propagated
    here; we swallow it and return 0. We deliberately do NOT pass a
    stop_event so the watcher's own SIGINT/SIGTERM handlers also fire
    when invoked from other contexts.
    """
    from agent.feedback_ingest import watch_inbox_kais
    try:
        watch_inbox_kais(interval=args.interval)
    except KeyboardInterrupt:
        return 0
    return 0
```

### WR-06: `_scan_once` broad `Exception` catch shadows `ValidationError` detail in logs

**File:** `agent/feedback_ingest.py:282-298`
**Issue:** The exception cascade is `(json.JSONDecodeError, ValidationError)` → log + move to errors; then `OSError` → log + move to errors; then `Exception` → log + move to errors. The first branch catches `ValidationError` and logs at WARNING. But the generic `Exception` branch at line 292 also catches things like `UnicodeDecodeError` (from `raw_bytes.decode("utf-8")` at line 254) — these never reach the ValidationError branch but produce a generic "unexpected failure" log message that hides the actual decode failure.

This is a logging quality issue, not a correctness bug — the file still moves to errors/. But operators debugging a file rejected by the watcher see "unexpected failure: 'utf-8' codec can't decode byte 0xff" instead of "unicode decode failed". The distinction matters when the inbox receives files from a kais-aigc exporter that emits UTF-16 or GBK.

**Fix:** Add `UnicodeDecodeError` as an explicit branch with a clearer message, or collapse JSONDecodeError + UnicodeDecodeError under a single "encoding/parse" branch:

```python
except (json.JSONDecodeError, UnicodeDecodeError) as exc:
    logger.warning(
        "kais inbox ingest failed (encoding/parse) for %s: %s",
        entry.name, exc,
    )
    _move_to_errors(entry.path, errors_dir)
except ValidationError as exc:
    logger.warning(
        "kais inbox ingest failed (validation) for %s: %s",
        entry.name, exc,
    )
    _move_to_errors(entry.path, errors_dir)
except OSError as exc:
    # ... unchanged
```

## Info

### IN-01: `_FALLBACK_EXPERT_IDS` hardcoded list will drift silently

**File:** `agent/feedback_schema.py:45-79`
**Issue:** The 30-entry fallback frozenset is a snapshot as of 2026-06-24. When a new movie-expert ships (v7+) and the repo layout is somehow unavailable (frozen wheel, zipapp, running outside repo), the fallback will reject the new expert's ID at validation time. The auto-discovery path handles the common case, but the fallback is a silent rejection vector.

The test `test_known_expert_ids_meets_minimum_count` asserts `>= 28`, which catches gross shrinkage but not additions.

**Fix:** Add a CI check that compares `_FALLBACK_EXPERT_IDS` against the live `skills/movie-experts/*/SKILL.md` discovery output and fails the build on drift. Or document the sync requirement in a maintainers checklist. Low priority — auto-discovery handles the common case.

### IN-02: `_scan_once` mixes `entry.path` (str) and `Path(entry.path)` styles

**File:** `agent/feedback_ingest.py:253-281`
**Issue:** The function bounces between `Path(entry.path).read_bytes()`, `Path(entry.path).rename(target)`, and `_move_to_errors(entry.path, errors_dir)` (which takes `str`). Style inconsistency, not a bug. Binding `entry_path = Path(entry.path)` once at the top of the loop body would clean this up.

**Fix:**
```python
entry_path = Path(entry.path)
raw_bytes = entry_path.read_bytes()
# ...
try:
    entry_path.rename(target)
# ...
_move_to_errors(entry_path, errors_dir)  # change signature to accept Path
```

### IN-03: `print()` in `watch_inbox_kais` banner bypasses logger

**File:** `agent/feedback_ingest.py:382-386`
**Issue:** The startup banner uses `print()` directly rather than `logger.info()`. This is intentional (the banner is operator-facing on the foreground CLI, and loggers may not be configured when invoked standalone), but it bypasses `_cprint` / skin-engine styling when run inside the TUI. In practice `_cmd_watch` is invoked as a standalone CLI subcommand (not inside the TUI REPL), so the unstyled print is fine.

**Fix:** Optional — add a `logger.info(...)` call alongside the print so log scrapers can find the PID. Low priority.

### IN-04: `_cmd_submit` doesn't list valid skill_ids on validation failure

**File:** `hermes_cli/feedback.py:206-211`
**Issue:** When the user runs `hermes feedback submit bad_skill good`, the Pydantic error message includes "Known: [...]" (because of the validator's `f"Known: {sorted(known)}"` at `feedback_schema.py:214`), but the CLI prints only `loc: msg` lines. The user sees `skill_id: skill_id 'bad_skill' is not a known movie-expert. Known: [...]` which is workable but noisy. UX nit.

**Fix:** Optional — pretty-print the known list in a follow-up line, e.g. `Valid skill_ids: screenplay, editor, ...`. Low priority.

### IN-05: Test `test_watch_inbox_uses_env_var_override` assertion is fragile

**File:** `tests/agent/test_feedback_ingest.py:616-631`
**Issue:** The final assertion uses `or` chaining to accept three different locations for `processed-kais/`:

```python
assert (custom_inbox.parent / "processed-kais").is_dir() or (
    custom_inbox / ".." / "processed-kais"
).exists() or (tmp_path / "processed-kais").exists()
```

This is testing implementation detail rather than behavior. The watcher's actual contract is "processed-kais is a sibling of inbox-kais" (per `_resolve_kais_inbox` + `inbox_dir.parent / "processed-kais"`), so only the first clause can ever be true. The `or` chain papers over uncertainty about the path resolution.

**Fix:** Tighten to the single correct assertion:

```python
assert (custom_inbox.parent / "processed-kais").is_dir()
```

If that fails, the bug is in `_resolve_kais_inbox`, not the test.

---

## Structural Notes (manual)

No structural pre-pass (`<structural_findings>`) was provided, so this section is the reviewer's own cross-cutting observations:

- **FOUND-08 preserved**: No `skills/*/SKILL.md` files were touched in this phase. The only files modified are `agent/feedback_*`, `hermes_cli/{feedback,commands,cli_commands_mixin,main}.py`, and the four test files. Verified by reading each source file's imports and content — no SKILL.md reads or writes anywhere.
- **Convention adherence**: `encoding="utf-8"` is present on every text `open()` / `read_text()` / `write_text()` in both source and tests (checked: `feedback_ingest.py:143, 254`, `feedback_schema.py:112`, `feedback_snapshot.py` (no I/O), `hermes_cli/feedback.py` (no I/O), `cli_commands_mixin.py:2412-2427` (no file I/O in the /feedback path)). `get_hermes_home()` is used consistently; no `Path.home()` in the production feedback modules (verified by test `test_no_path_home_usage` and direct grep).
- **Lazy %-logging**: All `logger.x` calls in `feedback_ingest.py` and `feedback_snapshot.py` use `%s` positional args. No f-string log calls found.
- **Specific exceptions**: Every `except` binds the exception with `as exc` and includes it in the log message. The broad `except Exception:` clauses carry explicit `# noqa: BLE001` rationales.
- **Circular imports**: `agent/feedback_*` modules do not import `run_agent` at module top (verified) — they use `getattr` lazily for agent attrs, consistent with the architectural constraint.
- **Test isolation**: The `feedback_env` fixture reloads `hermes_constants` and `feedback_ingest` per-test to pick up the monkeypatched `HERMES_HOME`. Pattern matches the cited `test_curator_reports.py` reference.

---

_Reviewed: 2026-06-24T14:05:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
