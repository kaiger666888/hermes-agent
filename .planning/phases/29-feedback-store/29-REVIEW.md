---
phase: 29-feedback-store
reviewed: 2026-06-24T00:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - agent/feedback_ingest.py
  - agent/feedback_store.py
  - hermes_cli/feedback.py
  - cli-config.yaml.example
findings:
  critical: 3
  warning: 6
  info: 3
  total: 12
status: issues_found
---

# Phase 29: Code Review Report

**Reviewed:** 2026-06-24
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Phase 29 ships the durable feedback store (`FeedbackStore`) and a thin
`write_feedback_record` wrapper that preserves the Phase 28 signature.
The persistence layer is well-structured: atomic `index.json` writes,
append-only bucket files, sha256-keyed dedup, and a `rebuild-index`
repair tool. Convention adherence is strong overall (explicit
`encoding="utf-8"`, `get_hermes_home()`, lazy `%s` logging, specific
exception binding).

However, three **BLOCKERS** undermine the contract the code claims to
honor:

1. **CORRECTION path recomputes the WRONG bucket** when the older record
   had a different `skill_id` or `source` than the incoming one. The
   dedup registry does not store those fields, so `_recompute_single_bucket`
   is invoked with a key derived from the *new* record's fields and
   silently no-ops when the older file does not exist there.
2. **Migration can create duplicate registry entries** because
   `_maybe_migrate_phase28_incoming` calls `record_feedback` (which
   appends to the dedup registry) BEFORE moving the source file to
   `archive/`. A crash between append and rename leaves the record in
   BOTH the registry and `incoming/` — and on the next `__init__` the
   dedup logic rejects the re-migration as a DUPLICATE, which is the
   *safe* failure, but only when the verdict matches. When the verdict
   differs across re-migration attempts, the CORRECTION path fires
   spuriously and marks the very same record_id superseded by itself.
3. **`_load_sha256_index` and `rebuild_index` strip `skill_id`/`source`
   from the registry replay**, so after a process restart the
   `_sha256_index` no longer has enough information to recompute
   weighted counts correctly. Combined with finding #1, this means the
   index can drift silently from the bucket files after a restart that
   triggers a CORRECTION write.

Several **WARNINGS** also surface: a f-string in a `print` call (CLI
convention drift but harmless), a symlink-vs-file TOCTOU window in
`_scan_once`, a `_move_to_errors` that can silently overwrite distinct
files with the same basename, a `seen` cache that prevents re-ingestion
of legitimately-updated files, and the `rebuild-index` command's use of
`len(summary)` which counts ALL buckets not just the ones touched.

A defense-in-depth **path-traversal** gap exists: `skill_id` and
`source` from the JSON payload are interpolated directly into a
filesystem path (`buckets/<skill_id>/<source>.jsonl`) without path-
separator validation. Pydantic validates `skill_id` against a known set
populated by auto-discovery, but auto-discovery `name.strip()`s without
rejecting `..` or `/`, and `source` is a `Literal` that happens to be
safe today but is not validated for path characters as a class
invariant.

## Critical Issues

### CR-01: CORRECTION path recomputes the wrong bucket when older record has different skill_id/source

**File:** `agent/feedback_store.py:454-458`
**Issue:**
The dedup registry entry stored on disk (lines 339-345) and in
`self._sha256_index` (line 353, 559, 699, 709) contains ONLY
`{sha256, verdict, record_id, ts, status}`. It does NOT store
`skill_id` or `source`.

In `_handle_dedup`'s CORRECTION branch, the older bucket key is
constructed from the **incoming** record's fields:

```python
older_bucket_key = (
    f"{record.skill_id}:{record.source}:{older_verdict}"
)
self._recompute_single_bucket(older_bucket_key)
```

If the older record landed in a different (skill_id, source) bucket —
which is realistic: the same `output_snapshot.sha256` can legitimately
appear via `source="cli"` and later `source="manual"` for a different
operator reviewing the same output, or two skill_ids referencing the
same artifact — `_recompute_single_bucket` reads
`buckets/<record.skill_id>/<record.source>.jsonl` (line 478-479),
filters by `b_verdict == older_verdict`, finds ZERO records (the older
record is in a different file), hits the `else` branch (line 499-501),
and **pops the older bucket from the index entirely**.

The result: the older bucket's count + weighted_count are silently
destroyed in `index.json` even though its records remain on disk. The
older record's `record_id` is correctly added to
`_superseded_record_ids` (so `query()` will filter it), but the bucket
summary is now wrong. `rebuild-index` recovers it, but only if the
operator happens to run it.

The newer record is then written to `buckets/<record.skill_id>/<record.source>.jsonl`
(line 325), which may be a third, separate file. The CORRECTION
contract ("older record marked superseded, weight=0 going forward") is
honored for `query()`, but the per-bucket summaries are corrupted.

**Fix:**
Store `skill_id` and `source` in the dedup registry entry so the older
bucket can be located precisely. Two places need patching:

```python
# 1. In record_feedback step 2 (dedup_entry construction):
dedup_entry = {
    "sha256": record.output_snapshot.sha256,
    "verdict": record.verdict,
    "record_id": record_id,
    "skill_id": record.skill_id,   # NEW
    "source": record.source,        # NEW
    "ts": record.ts.isoformat(),
    "status": "active",
}

# 2. In _handle_dedup CORRECTION branch, derive older bucket key
#    from the stored entry, not from the incoming record:
older_bucket_key = (
    f"{existing['skill_id']}:{existing['source']}:{older_verdict}"
)

# 3. Update _load_sha256_index and rebuild_index to read these fields
#    so they survive a process restart.
```

For backward compatibility with registry entries written before this
fix, fall back to scanning all bucket files for the older `record_id`
when `skill_id`/`source` are missing from the entry.

---

### CR-02: Migration can spuriously fire CORRECTION on the same record_id after a crash-retry

**File:** `agent/feedback_store.py:989-1009`
**Issue:**
The migration loop is:

```python
for src_path in pending:
    try:
        raw = json.loads(src_path.read_text(encoding="utf-8"))
        record = FeedbackRecord(**raw)
        self.record_feedback(record)          # appends to registry
        target = archive_dir / src_path.name
        src_path.rename(target)                # moves source file
        migrated += 1
    except Exception as exc:
        ...
```

`record_feedback` returns successfully (line 390) AFTER appending to
the dedup registry (lines 347-350) and writing `index.json`. If the
process crashes BETWEEN `record_feedback` returning and `src_path.rename`
completing (the rename itself is not wrapped in a try/except here — an
`OSError` propagates only to the outer `except Exception`), then:

1. The record is persisted in `buckets/` + the dedup registry.
2. The source file is STILL in `incoming/`.
3. On the next `__init__`, `_maybe_migrate_phase28_incoming` runs again
   (the `_migrated` flag is per-instance, so a new process re-runs),
   picks up the same file, calls `record_feedback` again.
4. `_handle_dedup` finds the existing entry. If the verdict MATCHES
   (DUPLICATE path), no-op — safe. If the verdict DIFFERS — but a
   single file has a single verdict, so this should not happen for the
   same file.

The real danger: `archive_dir / src_path.name` (line 1000) can collide.
Two Phase 28 runs that wrote `incoming/screenplay_cli_20260624.json`
produce two files with the SAME basename if the naming convention
collides (which the Phase 28 layout does on `ts_compact` second-
precision across multiple writes within the same second).
`Path.rename` on POSIX silently OVERWRITES the target, destroying the
earlier archive copy. The migration "succeeds" (the source file is
gone from `incoming/`) but the audit trail is corrupted.

Worse: the second `record_feedback` call for the same logical record
(after a crash) appends a SECOND line to the bucket file with a
*new* `record_id` (because `ts` was re-computed at
`datetime.now(timezone.utc)` at write time if the original was not
preserved — but the migration reads the ORIGINAL record from the
file, so `ts` is preserved and the `_make_record_id` is identical,
making the dedup catch it as a DUPLICATE and return without writing).
So this specific failure mode is contained by dedup — but only
because dedup is active. If dedup were ever disabled or bypassed
(e.g. via `rebuild_index` then a re-migration), the bucket would
gain duplicate lines.

**Fix:**
The collision risk on `archive_dir / src_path.name` is the more
serious bug. Add a unique suffix or check existence:

```python
target = archive_dir / src_path.name
if target.exists():
    # Collision — disambiguate with a counter or hash.
    stem, suffix = src_path.stem, src_path.suffix
    i = 1
    while True:
        candidate = archive_dir / f"{stem}.{i}{suffix}"
        if not candidate.exists():
            target = candidate
            break
        i += 1
src_path.rename(target)
```

Also document that `record_feedback` is NOT idempotent across
restarts for files with differing verdicts — the CORRECTION path
would fire and the older record_id would equal the newer record_id
(`_make_record_id` is deterministic given `ts` + `sha256`), producing
a self-supersession. Add a guard at the top of `_mark_superseded`:

```python
if older_record_id == newer_record_id:
    logger.warning(
        "self-supersession prevented: sha256=%s record_id=%s",
        sha[:8], older_record_id,
    )
    return
```

---

### CR-03: `_scan_once` `seen` cache prevents re-ingestion of legitimately-updated files

**File:** `agent/feedback_ingest.py:264-272, 359-363`
**Issue:**
The 2-poll stability check (lines 268-271) updates `pending[key]` to
the latest size when the size changes between polls. Once a file is
stable for two consecutive polls, it is ingested and `seen[key] =
(mtime, size)` is recorded (line 362).

If a file is later MODIFIED in place (mtime + size both change), the
check at line 266 (`seen.get(key) == current`) will be False, so the
file is re-processed. So far so good. BUT: if a file is REPLACED with
different content but identical (mtime, size) — a real possibility
when a kais-aigc exporter truncates and rewrites the same filename
within the same second with content of identical length (e.g. a
re-export of the same template with a tweaked field that does not
change byte count) — the `seen` cache hit silently skips the
re-ingestion. The new feedback record is lost.

More concretely: the exporter could rewrite the file with the SAME
output but a DIFFERENT verdict (the operator revised their feedback).
The second write has identical mtime (same second) and identical size
(verdict field is the same length: "good" → "needs_work" is the same
byte count). The `seen` cache returns the cached tuple and the file
is never re-read.

**Fix:**
Use a stronger content fingerprint than (mtime, size) for the `seen`
cache. Either hash the file bytes after stability is detected, or
track an inode + first-N-bytes signature:

```python
# After 2-poll stability, compute a quick content hash and store it:
content_sig = hashlib.blake2b(raw_bytes, digest_size=16).hexdigest()
if seen.get(key) == ("content", content_sig):
    continue  # truly identical to last ingestion
```

Alternatively, document that the kais-aigc exporter MUST use unique
filenames per export (which the existing anti-spoofing + path-
traversal defenses already assume) and add an assertion in
`watch_inbox_kais` startup that warns if any file in `inbox-kais/`
matches an existing `seen` cache entry on the first scan.

---

## Warnings

### WR-01: `print(f"Validation failed:", ...)` — malformed f-string with no placeholder

**File:** `hermes_cli/feedback.py:223`
**Issue:**
```python
print(f"Validation failed:", file=sys.stderr)
```
This is an f-string with no interpolation — a lint nit, but it also
suggests the author intended `print(f"Validation failed: {exc}", ...)`
and forgot the placeholder. As written, the exception details are
NOT printed in this branch (they are printed per-error in the loop
below, so functionally OK), but the construct is confusing.

**Fix:**
```python
print("Validation failed:", file=sys.stderr)
```

---

### WR-02: `_move_to_errors` overwrites distinct files with the same basename

**File:** `agent/feedback_ingest.py:367-382`
**Issue:**
The fallback path `target.write_bytes(src.read_bytes())` overwrites
an existing `errors/<name>` file silently. Two malformed kais-aigc
exports with the same filename (e.g. both named `feedback.json`)
landing in `errors/` in succession destroy the first one's audit
trail.

**Fix:**
Apply the same disambiguation suggested in CR-02:
```python
target = errors_dir / safe_name
if target.exists():
    stem, suffix = Path(safe_name).stem, Path(safe_name).suffix
    i = 1
    while (errors_dir / f"{stem}.{i}{suffix}").exists():
        i += 1
    target = errors_dir / f"{stem}.{i}{suffix}"
```

---

### WR-03: Symlink check in `_scan_once` has a TOCTOU window between `is_symlink()` and `read_bytes()`

**File:** `agent/feedback_ingest.py:246-275`
**Issue:**
The symlink guard (line 246) calls `entry.is_symlink()`. If the
adversary swaps the entry for a symlink AFTER the check but BEFORE
`Path(entry.path).read_bytes()` (line 274), the read follows the
symlink and ingests an arbitrary file. The window is small (a few
microseconds within the same scan iteration) but the defense is
documented as closing the info-leak vector and it does not fully
close it under an active attacker.

**Fix:**
Use `os.open(entry.path, os.O_NOFOLLOW)` and read from the fd, which
fails atomically if the path is a symlink:

```python
try:
    fd = os.open(entry.path, os.O_RDONLY | os.O_NOFOLLOW)
except OSError as exc:
    logger.warning("kais inbox open(O_NOFOLLOW) failed for %s: %s",
                   entry.name, exc)
    _move_to_errors(entry.path, errors_dir)
    seen[key] = current
    continue
try:
    with os.fdopen(fd, "rb") as f:
        raw_bytes = f.read()
finally:
    # fd is closed by the context manager; nothing else to do.
    pass
```

On Windows `O_NOFOLLOW` is not available — fall back to the existing
`is_symlink()` check there.

---

### WR-04: `_recompute_single_bucket` silently drops the bucket from `index.json` when zero verdict-matching records remain

**File:** `agent/feedback_store.py:499-501`
**Issue:**
```python
else:
    # No records of this verdict remain in the bucket file.
    self._index["buckets"].pop(bucket_key, None)
```
This is reachable via two paths: (1) the CORRECTION path (CR-01),
where the bucket key was derived from the incoming record's fields
and points at the WRONG file — the pop destroys an unrelated bucket;
(2) legitimately when the last record of a verdict is superseded.
In case (2) the bucket FILE still contains the superseded record
bytes (audit), but `index.json` no longer lists the bucket at all,
so `summary()` reports zero for that (skill, source, verdict) even
though `query(include_superseded=True)` returns the record.

The asymmetry between `count` (kept in the active-records case) and
the silent drop (zero-verdict case) is inconsistent with the
docstring at line 470-471: "If the bucket has no active records
left, weighted_count drops to 0.0 while count retains the raw line
count (audit)." The drop path violates this promise.

**Fix:**
Keep the bucket in the index with `count=0` and `weighted_count=0.0`
rather than popping it, OR fix CR-01 so the bucket key is always
correct and this branch is only reached legitimately. If keeping the
audit invariant is the intent, change line 501 to:
```python
self._index["buckets"][bucket_key] = {
    "count": 0,
    "weighted_count": 0.0,
    "first_ts": None,
    "last_ts": None,
}
```

---

### WR-05: `_load_decay_window_days_from_config` swallows all exceptions at debug level

**File:** `agent/feedback_store.py:168-188`
**Issue:**
```python
try:
    from hermes_cli.config import load_config
    cfg = load_config()
except Exception as exc:  # noqa: BLE001 — config load must never crash
    logger.debug("failed to load config for feedback: %s", exc)
    return DEFAULT_DECAY_WINDOW_DAYS
```
A misconfigured `cli-config.yaml` that fails to parse is logged at
`debug` only. The operator will not notice unless they have debug
logging enabled, and feedback will silently use the default 180-day
window even though they configured a custom one. The same applies to
the `int(...)` conversion at line 181.

**Fix:**
Promote to `logger.warning` for the config-load failure (it indicates
a real problem the operator should fix) and keep `debug` for the
`int()` conversion (which is more likely a benign type mismatch):

```python
except Exception as exc:
    logger.warning(
        "failed to load feedback config; using default decay_window_days=%d: %s",
        DEFAULT_DECAY_WINDOW_DAYS, exc,
    )
    return DEFAULT_DECAY_WINDOW_DAYS
```

---

### WR-06: `rebuild-index` CLI reports bucket count from `summary()` which includes ALL buckets, not just rebuilt ones

**File:** `hermes_cli/feedback.py:266-267`
**Issue:**
```python
summary = store.summary()
print(f"Index rebuilt: {len(summary)} buckets.")
```
After `rebuild_index()`, `self._index["buckets"]` is the freshly
rebuilt dict, and `summary()` returns a copy of it. So `len(summary)`
IS the rebuilt bucket count — this is correct. However, `summary()`
parses bucket keys by splitting on `:` (line 926-928); if any
skill_id or source ever contains a literal `:` (which the schema
permits today for `skill_id` since it's just `str` validated against
a known set), the parse drops that bucket from the summary
silently, underreporting the count. This is a latent bug in
`summary()`, not in the CLI.

**Fix:**
Either (a) validate that `skill_id` and `source` cannot contain `:`
at schema time (add a `field_validator` to `FeedbackRecord`), or (b)
use a different bucket-key separator that cannot appear in skill
names (e.g. `"␟"` or a tuple stored as a list in JSON). Option
(a) is the lighter touch:

```python
# In FeedbackRecord:
@field_validator("skill_id", "expert_id")
@classmethod
def _known_expert(cls, v: str) -> str:
    if ":" in v or "/" in v or "\\" in v:
        raise ValueError("skill_id must not contain ':', '/', or '\\'")
    ...
```

---

## Info

### IN-01: `cli-config.yaml.example` feedback section uses `skill_id/source/` directory description that does not match the actual bucket layout

**File:** `cli-config.yaml.example:520`
**Issue:**
```
# Controls the durable feedback persistence layer. Feedback records land
# under ~/.hermes/skills/.feedback/ in skill_id/source/ buckets after
# Phase 29 (STORE-01).
```
The actual layout (per `feedback_store.py:11-14` and `bucket_path_for`
at line 285) is `buckets/<skill_id>/<source>.jsonl` — a single jsonl
file per source, NOT a `skill_id/source/` directory tree. The
documentation is misleading.

**Fix:**
```
# under ~/.hermes/skills/.feedback/buckets/<skill_id>/<source>.jsonl
# after Phase 29 (STORE-01).
```

---

### IN-02: `_cmd_watch` installs signal handlers globally when run from CLI but the docstring claims tests pass `stop_event` directly

**File:** `hermes_cli/feedback.py:160-182`, `agent/feedback_ingest.py:420-440`
**Issue:**
The CLI handler deliberately does NOT pass `stop_event`, which means
`watch_inbox_kais` installs `signal.signal(SIGINT, _handler)` in the
main thread. This OVERRIDES any prior SIGINT handler the CLI may
have installed (e.g. for graceful shutdown of other subsystems if
the CLI ever grows to run the watcher alongside other long-running
tasks). The override is not restored on exit.

For v6.0 foreground-only use this is acceptable, but it is a latent
footgun. Document it or save/restore the prior handler:

```python
prior_sigint = signal.getsignal(signal.SIGINT)
prior_sigterm = signal.getsignal(signal.SIGTERM)
try:
    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)
    # ... loop ...
finally:
    signal.signal(signal.SIGINT, prior_sigint)
    signal.signal(signal.SIGTERM, prior_sigterm)
```

---

### IN-03: `compute_weight` docstring says "older than decay_window_days: weight = 0.1" but the math gives weight > 0.1 for any finite age

**File:** `agent/feedback_store.py:84-85, 118-120`
**Issue:**
```python
- decay_window_days old: weight = 0.0 floored at 0.1
- older than decay_window_days: weight = 0.1 (never fully zero)
```
At exactly `age_days == decay_window_days`, `raw_weight = 0.0` and the
`max(0.1, 0.0)` returns `0.1`. At `age_days == decay_window_days / 2`,
`raw_weight = 0.5`. The math is correct; the docstring's "0.0 floored
at 0.1" phrasing is slightly confusing because 0.0 never escapes the
`max()`. Cosmetic only.

**Fix:**
Rephrase to "at decay_window_days old and beyond, the raw weight goes
negative or zero and the floor clamps it to 0.1".

---

_Reviewed: 2026-06-24_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
