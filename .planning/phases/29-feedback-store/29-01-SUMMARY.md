---
phase: 29-feedback-store
plan: 01
subsystem: feedback-store
tags: [feedback, persistence, jsonl, decay, index, migration, pydantic, atomic-write]

# Dependency graph
requires:
  - phase: 28-feedback-ingestion-mvp
    provides: "agent.feedback_schema.FeedbackRecord + OutputSnapshot (frozen schema); agent.feedback_ingest.write_feedback_record (Phase 28 write path, Plan 02 wraps this)"
  - phase: 28-feedback-ingestion-mvp
    provides: "utils.atomic_json_write (temp + fsync + os.replace); hermes_constants.get_hermes_home (CLAUDE.md mandate)"
provides:
  - "agent.feedback_store.FeedbackStore (record_feedback / query / summary / get_record / bucket_path_for)"
  - "agent.feedback_store.compute_weight (STORE-03 linear decay: max(0.1, 1.0 - age_days/180))"
  - "agent.feedback_store.recompute_bucket_weighted_count (query-time weight aggregation)"
  - "agent.feedback_store._load_decay_window_days_from_config (config.yaml feedback.decay_window_days reader)"
  - "agent.feedback_store.DEFAULT_DECAY_WINDOW_DAYS = 180 constant"
  - "index.json schema v1 (version, decay_window_days, updated_ts, buckets{}, by_sha256{})"
  - "cli-config.yaml.example feedback: section documentation"
affects:
  - "Phase 29 Plan 02 (consumes FeedbackStore.record_feedback for write_feedback_record wrapper + adds STORE-04 sha256 dedup / correction branch)"
  - "Phase 32 Curator (consumes FeedbackStore.summary + query for review queue)"
  - "Phase 33 Dashboard (reads index.json directly — JSON-on-disk contract)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Hybrid persistence: direct append (O(1) per write) for buckets/*.jsonl + atomic_json_write for index.json (RESEARCH Pattern 1)"
    - "Linear time-decay computed at query time, never stored on record (weight = max(0.1, 1.0 - age_days/180))"
    - "Index bucket key format '<skill_id>:<source>:<verdict>' — colon separator avoids skill_id underscore collision (Pitfall #6)"
    - "Lazy idempotent migration via _migrated flag + .migration-in-progress sentinel + append-first-then-archive order (RESEARCH Pitfall #4)"
    - "Config reader with full tolerance (missing file / section / non-int all fall back to default — never crash init)"

key-files:
  created:
    - "agent/feedback_store.py"
    - "tests/agent/test_feedback_store.py"
  modified:
    - "cli-config.yaml.example"

key-decisions:
  - "Plan 01 deliberately OMITS the sha256 dedup / correction branch (STORE-04). record_feedback always writes. Plan 02 inserts the dedup check between _make_record_id and bucket append. TODO comment in source marks the insertion point."
  - "Index bucket count must FILTER records by verdict within the shared source file (the file holds all verdicts for skill_id+source; the index bucket key includes verdict). Auto-fixed (Rule 1) — see Deviations."
  - "__init__ order: _load_or_init_index MUST run before _maybe_migrate_phase28_incoming so record_feedback calls during migration have self._index available."

patterns-established:
  - "Pattern: FeedbackStore class owns ALL feedback persistence under <HERMES_HOME>/skills/.feedback/ — single writer, multiple consumers (Curator + dashboard)"
  - "Pattern: index.json is the single source of truth (STORE-02). P32 Curator + P33 dashboard MUST NOT do parallel ad-hoc scans of buckets/."
  - "Pattern: encoding=utf-8 mandatory on every open() in this module (Ruff PLW1514 enforced). No exceptions."

requirements-completed: [STORE-01, STORE-02, STORE-03]

# Metrics
duration: "~18 min"
completed: 2026-06-24
---

# Phase 29 Plan 01: Feedback Store Foundation Summary

**FeedbackStore class with bucketed jsonl persistence, linear time-decay at query time (STORE-03), atomic index.json as single source of truth (STORE-02), and lazy idempotent migration from Phase 28 flat incoming/ — the storage layer Plan 02 will wire the Phase 28 write path into.**

## Performance

- **Duration:** ~18 min
- **Started:** 2026-06-24T08:45:00Z
- **Completed:** 2026-06-24T09:03:00Z
- **Tasks:** 3 (all atomic TDD: RED → GREEN → commit)
- **Files created:** 2 (`agent/feedback_store.py` 540 LOC, `tests/agent/test_feedback_store.py` 770 LOC)
- **Files modified:** 1 (`cli-config.yaml.example` +19 lines)
- **Tests added:** 49 (16 Task 1 + 33 Task 2)

## Accomplishments
- `FeedbackStore` class exposes `record_feedback` / `query` / `summary` / `get_record` / `bucket_path_for` — the full STORE-02 Query API surface, ready for Plan 02's `write_feedback_record` wrapper delegation.
- `compute_weight` implements STORE-03 linear decay `max(0.1, 1.0 - age_days/180)`. Weights are computed at query / index-update time, NEVER stored on the record (CONTEXT.md specifics line 111). Naive datetimes raise TypeError (Pitfall #7 mitigation).
- `index.json` schema matches RESEARCH Pattern 2 exactly: `version=1`, `decay_window_days`, `updated_ts`, `buckets{}`, `by_sha256{}`. Bucket key is `"<skill_id>:<source>:<verdict>"` (colon separator avoids skill_id underscore collision — Pitfall #6).
- Bucket layout is `buckets/<skill_id>/<source>.jsonl` with O(1) direct append per write (no full-file rewrite). `atomic_json_write` is reserved for `index.json` only (RESEARCH Pattern 1 — avoids O(N²) rewrite cost over bucket lifetime).
- Lazy idempotent migration from Phase 28 flat `incoming/*.json` to `buckets/<skill_id>/<source>.jsonl` + archives originals to `archive/phase-28-migration/`. Append-first-then-archive order (RESEARCH Pitfall #4) ensures crash recovery. Per-file try/except logs WARNING + continues on malformed files (T-29-04 mitigation).
- `decay_window_days` configurable via `feedback.decay_window_days` in `config.yaml` (default 180). Documented in `cli-config.yaml.example` with the exact weight formula inline. Config reader tolerates missing file / section / non-int values — never crashes init.

## Task Commits

Each task was committed atomically:

1. **Task 1: FeedbackStore skeleton + decay + index schema** — `7d3b740c4` (feat)
2. **Task 2: record_feedback + query + summary + get_record + lazy migration** — `6d42599c9` (feat)
3. **Task 3: cli-config.yaml.example feedback section + regression sweep** — `58efdb458` (docs)

## Files Created/Modified

- **`agent/feedback_store.py`** (NEW, 540 LOC) — `FeedbackStore` class with all STORE-01/02/03 surface. `compute_weight` + `recompute_bucket_weighted_count` module-level functions. `_load_decay_window_days_from_config` reader. Module docstring declares single-process MVP assumption (no file locking — deferred per CONTEXT.md).
- **`tests/agent/test_feedback_store.py`** (NEW, 770 LOC) — 9 test classes: TestFeedbackStoreInit (3), TestIndex (3), TestDecay (10), TestRecordFeedback (8), TestQuery (8), TestSummary (6), TestGetRecord (2), TestMigration (6), TestConfig (3). All use isolated HERMES_HOME via the `feedback_env` fixture (monkeypatch + importlib.reload pattern).
- **`cli-config.yaml.example`** (MODIFIED, +19 lines) — New top-level `feedback:` section between `memory:` and `Session Reset Policy`. Documents `decay_window_days: 180` with the weight formula inline.

## Decisions Made

- **Plan 01 ships record_feedback WITHOUT the dedup branch.** The plan's `<objective>` is explicit: "Plan 01 deliberately SHIPS record_feedback WITHOUT the dedup/correction branch — it always writes. Plan 02 adds the sha256 dedup branch (STORE-04)." A TODO comment in source marks the exact insertion point for Plan 02.
- **`_maybe_migrate_phase28_incoming` is idempotent via the `_migrated` instance flag + a `.migration-in-progress` sentinel file** (RESEARCH Example 3). Append-first-then-archive order means a crash mid-migration leaves harmless duplicates that Plan 02's dedup catches (Pitfall #4 mitigation).
- **Config override via `feedback.decay_window_days`** reads from `cli-config.yaml` using the same pattern as `agent/curator._load_config` (curator.py:124). Falls back to 180 on ANY exception (ImportError, OSError, ValueError, TypeError, KeyError) — never crashes init.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Index bucket count overcounted when verdicts mix in the same source file**
- **Found during:** Task 2 (TestSummary::test_summary_returns_per_bucket_counts RED)
- **Issue:** The plan said "count = lines in bucket_file" but the bucket FILE is keyed by `(skill_id, source)` while the index bucket KEY is keyed by `(skill_id, source, verdict)`. With multiple verdicts writing to `screenplay/cli.jsonl`, the index bucket `screenplay:cli:needs_work` got count=5 (all lines in the file) instead of count=2 (only the needs_work lines). Same bug affected `weighted_count` and `first_ts`/`last_ts`.
- **Fix:** Filter `all_records` to `verdict_records = [r for r in all_records if r.verdict == record.verdict]` before computing count/weighted_count/ts-range. Applied in `record_feedback` (agent/feedback_store.py).
- **Files modified:** `agent/feedback_store.py`
- **Verification:** TestSummary::test_summary_returns_per_bucket_counts passes (good=3, needs_work=2). All 49 tests green.
- **Committed in:** `6d42599c9` (Task 2 commit)

**2. [Rule 1 - Bug] Migration ran before _load_or_init_index, crashing on missing self._index**
- **Found during:** Task 2 (TestMigration::test_migration_idempotent RED)
- **Issue:** The original `__init__` order was: `load_sha256_index → migrate → load_or_init_index`. When migration called `record_feedback`, `self._index` didn't exist yet (`AttributeError: 'FeedbackStore' object has no attribute '_index'`). The migration logged a WARNING and left files in `incoming/` — appearing to "succeed" but actually skipping every file.
- **Fix:** Reordered `__init__` so `_load_or_init_index` runs BEFORE `_maybe_migrate_phase28_incoming`. Now migration's `record_feedback` calls update the index safely.
- **Files modified:** `agent/feedback_store.py`
- **Verification:** TestMigration (all 6 tests including idempotent + partial recovery) passes. All 49 tests green.
- **Committed in:** `6d42599c9` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs)
**Impact on plan:** Both fixes essential for correctness — without them, mixed-verdict buckets overcounted and migration silently no-op'd. No scope creep. Both fixes preserve the plan's design intent (the plan said "count = lines in bucket_file" without accounting for the file-vs-key granularity mismatch; the fix implements the design intent rather than the literal wording).

## Issues Encountered

- **System Python 3 vs venv Python for CLI tests.** Running `python3 -m pytest tests/hermes_cli/test_feedback_cli.py` under `/usr/bin/python3` (system) fails with `ModuleNotFoundError: No module named 'prompt_toolkit'`. The `prompt_toolkit` package is only installed in `.venv/lib/python*/site-packages/`. Running under `.venv/bin/python` succeeds (17/17 CLI tests green). This is a pre-existing environment quirk, NOT a regression from this plan — the same failure mode exists on `main` before my changes. Out of scope per deviation Rule scope boundary (not caused by this plan's changes). The plan's verification step #6 (`pytest tests/agent/test_feedback_ingest.py -x`) is unaffected since it does not import `cli.py`.

## User Setup Required

None — no external service configuration required. The feedback store uses local filesystem under `<HERMES_HOME>/skills/.feedback/`. Operators can optionally tune `feedback.decay_window_days` in `cli-config.yaml` (default 180 days), but this is opt-in.

## Next Phase Readiness

- **Plan 29-02 readiness:** `FeedbackStore.record_feedback` + `bucket_path_for` are the exact insertion points for Plan 02's `write_feedback_record` wrapper. The TODO comment in source marks where the STORE-04 dedup branch goes. `_sha256_index` cache is already populated on init from `dedup/sha256-registry.jsonl` (Plan 01 writes the registry but doesn't consult it; Plan 02 adds the check).
- **Phase 32 Curator readiness:** `FeedbackStore.summary(skill_id=...)` returns per-bucket counts + weighted_counts ready for the review queue. `FeedbackStore.query(verdict="bad")` returns ts-ascending records ready for pattern analysis.
- **Phase 33 Dashboard readiness:** `index.json` is a self-contained JSON file with the exact RESEARCH Pattern 2 schema — the dashboard can read it directly without importing Python.
- **Blockers:** None. All 49 Plan 01 tests green + 45 Phase 28 unit tests still green + 14 ingest tests still green + Ruff PLW1514 clean + FOUND-08 preserved (zero bundled SKILL.md changes vs v5.0).

## Self-Check: PASSED

**Files verified to exist:**
- FOUND: agent/feedback_store.py
- FOUND: tests/agent/test_feedback_store.py
- FOUND: cli-config.yaml.example (modified — feedback: section added)

**Commits verified to exist:**
- FOUND: 7d3b740c4 (Task 1)
- FOUND: 6d42599c9 (Task 2)
- FOUND: 58efdb458 (Task 3)
