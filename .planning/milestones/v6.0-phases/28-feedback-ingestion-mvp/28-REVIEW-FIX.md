---
phase: 28-feedback-ingestion-mvp
fixed_at: 2026-06-24T15:30:00Z
review_path: .planning/phases/28-feedback-ingestion-mvp/28-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 28: Code Review Fix Report

**Fixed at:** 2026-06-24T15:30:00Z
**Source review:** `.planning/phases/28-feedback-ingestion-mvp/28-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 7 (1 Critical + 6 Warning; 5 Info findings excluded per default scope)
- Fixed: 7
- Skipped: 0

**Verification:**
- All 76 feedback tests pass after each atomic fix (snapshot=13, ingest=33, schema=13, cli=17).
- Ruff PLW1514 passes on all 5 modified files.
- FOUND-08 preserved: zero `skills/*/SKILL.md` or `references/*.md` bytes touched. Diff is confined to `agent/feedback_*.py` and `hermes_cli/{feedback,cli_commands_mixin}.py`.

## Fixed Issues

### CR-01: Non-serializable agent params crash write_feedback_record, breaking atomicity

**Files modified:** `agent/feedback_snapshot.py`
**Commit:** `29d2f155b`
**Applied fix:** Added a new `_safe_param(val)` helper that probes `json.dumps(val)` and drops the value (returns None) on TypeError/ValueError, logging at debug level. Applied this shallow JSON-safety probe uniformly to all four agent params (`max_tokens`, `reasoning_config`, `service_tier`, `request_overrides`) — the three non-dict params now go through `_safe_param`, while `request_overrides` retains its existing deep `_filter_serializable` filter for the dict branch (and uses `_safe_param` for the non-dict fallback). This extends RESEARCH Pitfall #8's protection to all four params, eliminating the `TypeError` mid-write crash path that defeated the atomic-write guarantee. Added `import json as _json` at module top.
**Test result:** 13/13 snapshot tests pass.

### WR-01: Source file orphaned in inbox when post-ingest unlink fails

**Files modified:** `agent/feedback_ingest.py`
**Commit:** `6d05c00f4`
**Applied fix:** When the post-ingest `Path(entry.path).unlink()` fails (after `write_feedback_record` succeeded and `target.write_bytes` succeeded), the orphaned source file is now relocated to `errors_dir` (i.e. `errors-kais/`) with a `.unlink-failed` suffix so the operator can see it. This breaks the silent-skip loop where the next scan would hit the seen cache and ignore the orphan. A nested `try/except OSError` handles the case where even the relocate-rename fails, logging loudly that manual cleanup is required. The record itself is safe in `incoming/` and the bytes are safe in `processed/`.
**Test result:** 33/33 ingest tests pass.

### WR-02: `--revised` flag in /feedback collides with literal correction text

**Files modified:** `hermes_cli/cli_commands_mixin.py`
**Commit:** `0b436ee5c`
**Applied fix:** Replaced `tail.partition("--revised")` with `shlex.split(tail)` tokenization. `--revised` is now detected only when it appears as a standalone token (via `"--revised" in shell_tokens` + `index()`), so the flag no longer matches inside a quoted correction string like `"The --revised flag is wrong"`. shlex also respects quoting, so `--revised "fixed text"` correctly produces `revised_output="fixed text"`. A `ValueError` fallback to `tail.split()` handles mismatched quotes gracefully. Local `import shlex` mirrors the existing `import re as _re` local-import pattern in the same method.
**Test result:** 17/17 CLI tests pass. Manually verified shlex behavior for both the standalone-token case (flag detected) and the inside-quoted-string case (flag NOT detected — the bug case).

### WR-03: Symlinks in inbox-kais/ are followed, not rejected

**Files modified:** `agent/feedback_ingest.py`
**Commit:** `32a03694b`
**Applied fix:** Added a `entry.is_symlink()` guard at the top of the file loop in `_scan_once`, before any `is_dir()` / `is_file()` / stat / read / rename call. Symlinks are rejected with a warning log and `continue`. This closes the low-severity info-leak vector where an adversary with write access to `inbox-kais/` could link a sensitive file (named `*.json`) and have its contents ingested as `output_text`. It also prevents the rename-the-symlink-not-the-target surprise that would orphan the link target.
**Test result:** 33/33 ingest tests pass.

### WR-04: `OutputSnapshot.sha256` validator's non-str branch is unreachable / masks Pydantic errors

**Files modified:** `agent/feedback_schema.py`
**Commit:** `d5274894a`
**Applied fix:** Removed the dead `not isinstance(v, str)` branch from the `_sha256_is_64_hex` field_validator. Pydantic v2 enforces `sha256: str` at the schema level before this validator runs, so non-str inputs surface as a Pydantic ValidationError with a clear "Input should be a valid string" message — no isinstance check needed. Updated the remaining error message to "sha256 must be 64 hex characters (0-9, a-f, A-F)" (was "64 lowercase hex characters", which was misleading since the regex accepts mixed case and we `.lower()` on success). Added an explanatory comment.
**Test result:** 13/13 schema tests pass. No tests reference the old error message text (verified via grep).

### WR-05: `_cmd_watch` `stop_event` wiring causes double-handler install attempts

**Files modified:** `hermes_cli/feedback.py`
**Commit:** `e9e60d01e`
**Applied fix:** Removed the `stop_event = threading.Event()` creation and the `stop_event=stop_event` kwarg from the `watch_inbox_kais(...)` call inside `_cmd_watch`. The watcher now receives `stop_event=None` (the default) and installs its own SIGINT/SIGTERM handlers per its docstring promise. The `except KeyboardInterrupt: return 0` path still works because Python's default SIGINT handler raises KeyboardInterrupt from `time.sleep` inside the watcher, which propagates up through `_scan_once` (no KeyboardInterrupt catch there) and the watcher's outer `except Exception` (KeyboardInterrupt is BaseException, not Exception). Expanded the docstring to document the distinction between CLI foreground invocation (no stop_event passed) and external test invocation (stop_event passed directly). Removed the now-unused `import threading` at module top.
**Test result:** 17/17 CLI tests pass. The existing `test_cmd_feedback_watch_invokes_watch_inbox_kais` test only asserts that `watch_inbox_kais` is called with the correct interval — it does not assert `stop_event` is passed, so the fix is backward-compatible.

### WR-06: `_scan_once` broad `Exception` catch shadows `UnicodeDecodeError` detail in logs

**Files modified:** `agent/feedback_ingest.py`
**Commit:** `d22724e33`
**Applied fix:** Added an explicit `except UnicodeDecodeError as exc:` branch in the `_scan_once` exception cascade, placed AFTER the `(json.JSONDecodeError, ValidationError)` branch and BEFORE the `OSError` branch. The new branch logs at WARNING with explicit encoding context ("file is not valid UTF-8 — re-export as UTF-8") so operators debugging a file rejected by the watcher see the actual decode-failure cause instead of the generic "unexpected failure" message. `UnicodeDecodeError` is a subclass of `ValueError` (not OSError), so without this branch it was falling through to the generic `except Exception:` clause. The file is still moved to `errors/` (same as all other failure branches).
**Test result:** 33/33 ingest tests pass.

## Skipped Issues

None. All 7 in-scope findings were fixed successfully.

---

_Fixed: 2026-06-24T15:30:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
