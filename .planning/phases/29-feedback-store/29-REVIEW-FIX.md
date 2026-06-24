---
phase: 29-feedback-store
fixed_at: 2026-06-24T19:45:00Z
review_path: .planning/phases/29-feedback-store/29-REVIEW.md
iteration: 1
findings_in_scope: 9
fixed: 9
skipped: 0
status: all_fixed
---

# Phase 29: Code Review Fix Report

**Fixed at:** 2026-06-24
**Source review:** `.planning/phases/29-feedback-store/29-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 9 (3 Critical + 6 Warning; 3 Info intentionally out of scope)
- Fixed: 9
- Skipped: 0
- Full feedback suite: **150 passed, 1 skipped** (target was 150+ green)
- Ruff PLW1514: clean on all touched files
- FOUND-08: preserved (zero SKILL.md edits across all 9 commits)

## Fixed Issues

### CR-01: CORRECTION path recomputes the wrong bucket when older record has different skill_id/source

**Files modified:** `agent/feedback_store.py`
**Commit:** a580e99ff (combined with WR-04)
**Applied fix:**
- Added `skill_id` + `source` fields to the dedup registry entry written by `record_feedback` (step 2).
- Extended `_mark_superseded` to accept and persist `older_skill_id`, `older_source`, `newer_skill_id`, `newer_source` on the supersession event, so the post-restart replay has enough info to resolve either bucket.
- `_handle_dedup` CORRECTION branch now derives `older_bucket_key` from `existing["skill_id"]`/`existing["source"]` (with `or record.skill_id` fallback for legacy entries written before this fix — preserves old behavior for pre-existing data while fixing new writes).
- `_load_sha256_index` now reads `skill_id` + `source` from BOTH record entries and supersession events (using `.get()` so legacy lines without these fields degrade gracefully).

### CR-02: Migration can spuriously fire CORRECTION on the same record_id after a crash-retry

**Files modified:** `agent/feedback_store.py`
**Commit:** 6442f1303
**Applied fix:**
- Added a self-supersession guard at the top of `_mark_superseded`: if `older_record_id == newer_record_id`, log a warning and return without appending the supersession event or mutating state. This prevents a crash-retry migration from marking a record superseded by itself (which would have removed it from `query()`'s active set).
- Pre-migration dedup check: if the source `FeedbackRecord`'s sha256 is already in the registry with the same verdict, the file is routed to `archive/phase-28-migration/duplicate/` instead of re-calling `record_feedback`. Makes the crash-retry audit trail explicit.
- Archive filename disambiguation: when `archive_dir / src_path.name` already exists, append `.{N}` counter suffix until the name is free. Prevents silent overwrites when two Phase 28 runs produce `incoming/` files with the same second-precision basename.

### CR-03: `_scan_once` `seen` cache prevents re-ingestion of legitimately-updated files

**Files modified:** `agent/feedback_ingest.py`
**Commit:** bd753e398
**Applied fix:**
- Widened the `seen` cache value shape from `(mtime, size)` to `(mtime, size, sha256_content)`.
- Added a two-tier check: fast-path on `(mtime, size)` reject; if those match, compute `hashlib.sha256(raw_bytes).hexdigest()` and compare to the cached content hash. Cache hit only if all three match.
- Catches the sub-second-same-size-different-content rewrite attack (e.g. a kais-aigc exporter re-emitting the same filename with a revised verdict of the same byte length).
- Added `import hashlib` to the module.
- Updated `watch_inbox_kais`'s `seen` initializer to the new 3-tuple type.
- `content_sha_for_cache` falls back to a stat-derived signature on error paths (the file is moving to `errors/` anyway).

### WR-01: Malformed f-string with no placeholder

**Files modified:** `hermes_cli/feedback.py`
**Commit:** 9ace66b30
**Applied fix:** Converted `print(f"Validation failed:", ...)` to `print("Validation failed:", ...)` at line 223. The per-error loop below already prints exception details, so this branch only needs the heading.

### WR-02: `_move_to_errors` overwrites distinct files with the same basename

**Files modified:** `agent/feedback_ingest.py`
**Commit:** ce081eb87
**Applied fix:** Before `src.rename(target)`, check whether `target` exists. If so, walk `{stem}.{N}{suffix}` for N=1,2,… until a free name is found. Prevents silent overwrites when two malformed kais-aigc exports with the same filename land in `errors/` in succession.

### WR-03: Symlink check TOCTOU window between `is_symlink()` and `read_bytes()`

**Files modified:** `agent/feedback_ingest.py`
**Commit:** 3d40d054d
**Applied fix:**
- Replaced `Path(entry.path).read_bytes()` with `os.open(entry.path, os.O_RDONLY | os.O_NOFOLLOW)` + `os.fdopen(fd, "rb")`. O_NOFOLLOW atomically rejects symlinks at open time on POSIX, closing the TOCTOU window.
- On open failure (ELOOP / EMLINKAGE / permission / vanished), log + route to `_move_to_errors` and continue.
- Windows fallback: `getattr(os, "O_NOFOLLOW", 0)` returns 0 on Windows, so the flag is a no-op there and the existing `entry.is_symlink()` pre-check remains the only defense (documented gap).
- Kept the pre-check `entry.is_symlink()` to keep the common-case log noise low (symlinks are rejected before the open, not after).

### WR-04: `_recompute_single_bucket` silently drops the bucket from `index.json`

**Files modified:** `agent/feedback_store.py`
**Commit:** a580e99ff (combined with CR-01)
**Applied fix:** When the recomputed bucket has zero verdict-matching records, set the bucket entry to `{"count": 0, "weighted_count": 0.0, "first_ts": None, "last_ts": None}` rather than popping it from `self._index["buckets"]`. Honors the docstring's "count retains the raw line count (audit)" promise and prevents `summary()` from underreporting. Coordinated with CR-01 since both touch the same code path.

### WR-05: Config-load failures swallowed at debug level

**Files modified:** `agent/feedback_store.py`
**Commit:** aabe4b70b
**Applied fix:** Promoted the `_load_decay_window_days_from_config` config-load exception handler from `logger.debug` to `logger.warning`. New message: `"failed to load cli-config.yaml for feedback.decay_window_days; using default %d: %s"` — names the config section so the operator knows what to fix. The inner `int()` conversion handler remains at `debug` (benign type mismatch).

### WR-06: `summary()` parses bucket keys by splitting on `:` — future `skill_id` containing `:` would silently disappear

**Files modified:** `agent/feedback_schema.py`
**Commit:** 3b3253177
**Applied fix:** Added a path-safety check at the top of `FeedbackRecord._known_expert`: if `skill_id`/`expert_id` contains `:`, `/`, or `\`, raise a `ValueError` with a clear message ("must not contain ':', '/', or '\\'"). Belt-and-suspenders defense layered on top of the existing known-expert allowlist — the allowlist would reject these in practice, but this makes the bucket-path and bucket-key invariants explicit class-level guarantees independent of auto-discovery state.

## Skipped Issues

None — all 9 in-scope findings were applied successfully.

## Out of Scope (Info — not addressed per fix_scope)

- **IN-01:** `cli-config.yaml.example` feedback section directory description mismatch (doc-only).
- **IN-02:** `_cmd_watch` installs signal handlers globally (v6.0 foreground-only acceptable per review).
- **IN-03:** `compute_weight` docstring "0.0 floored at 0.1" phrasing cosmetic (math is correct).

## Verification

| Check | Result |
|-------|--------|
| Targeted tests after each fix (store/ingest/cli) | pass |
| Full feedback suite (store + integration + ingest + schema + snapshot + cli) | **150 passed, 1 skipped** |
| Ruff PLW1514 on `feedback_store.py` / `feedback_ingest.py` / `feedback_schema.py` / `feedback.py` | clean |
| `python3 -c "import ast; ast.parse(...)"` syntax checks | pass |
| FOUND-08 (no SKILL.md `expert_id`/`related_skills` edits) | preserved |

---

_Fixed: 2026-06-24_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
