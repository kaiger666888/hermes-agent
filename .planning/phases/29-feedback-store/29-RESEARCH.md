# Phase 29: Feedback Store - Research

**Researched:** 2026-06-24
**Domain:** Local JSONL persistence + queryable index + time-decay weights + sha256 dedup (Python stdlib + Pydantic v2; no new deps)
**Confidence:** HIGH

## Summary

Phase 29 builds the durable storage + query + decay + dedup layer on top of Phase 28's `FeedbackRecord` contract. It is pure data plumbing — no new dependencies, no new external services, no bundled-SKILL.md bytes touched. The work decomposes cleanly into four sub-problems that map 1:1 onto the four STORE requirements: (1) restructure the on-disk layout from Phase 28's flat `incoming/` into `buckets/<skill_id>/<source>.jsonl`, (2) maintain a single `index.json` as the source of truth for counts and weighted_counts, (3) compute linear time-decay weights at query time so tuning is cheap, (4) detect duplicate `output_snapshot.sha256` and demote older records when a correction arrives.

The recommended architecture is one new module — `agent/feedback_store.py` — exposing a `FeedbackStore` class with `record_feedback()` / `query()` / `summary()` / `get_record()` methods. The Phase 28 write path (`agent/feedback_ingest.py:write_feedback_record`) becomes a thin 2-line wrapper that delegates to `FeedbackStore.record_feedback()`. All existing callers (the `/feedback` slash command, the kais-aigc watcher, the JSONL batch importer) keep working unchanged because the wrapper preserves the exact `FeedbackRecord -> Path` signature. The `index.json` file is the single source of truth — Phase 32's Curator and Phase 33's dashboard both read it directly and MUST NOT do parallel ad-hoc scans of `buckets/` (this is explicit in SC-2 and prevents divergence).

**Primary recommendation:** Build a hybrid persistence layer — direct append (`with open(path, "a", encoding="utf-8")`) for the append-only `buckets/*.jsonl` files (O(1) per write, no rewrite), atomic full rewrite via `utils.atomic_json_write` for `index.json` (small file, crash-safe). Compute decay weights at query/index-update time, not on write, so operators can retune `decay_window_days` via config without rewriting records.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Index Update Strategy (STORE-02):** Incremental update on every write — `write_feedback_record` updates `index.json` atomically alongside the jsonl append. Zero stale reads, no rebuild cron. Index stays small: one entry per `(skill_id, source, verdict)` bucket with `count`, `weighted_count`, `first_ts`, `last_ts`, plus a per-sha256 dedup registry. Periodic rebuild and lazy on-demand rejected.

**Time-Decay Function (STORE-03):** Linear decay — `weight = max(0.1, 1.0 - (age_days / 180))`. 0 days = 1.0; 90 days = 0.5; 180 days = 0.0 floored at 0.1; >180 days = 0.1 (never fully zero). Default `decay_window_days = 180`, configurable under `feedback.decay_window_days` in `config.yaml`. Operators tune by editing config + restarting Hermes (no live retune for v6).

**Correction Weight Demotion (STORE-04):** Zero out older record, count only newer. When same `output_snapshot.sha256` arrives with a different `verdict`: older record gets `weight = 0.0`, `status = "superseded"`, `superseded_by = <newer_record_id>`; newer record gets normal weight based on its own age, `status = "active"`, `supersedes = <older_record_id>`. Index reflects only the latest verdict per sha256 in `weighted_count`; raw `count` still includes superseded records for audit. Halve-older and keep-both rejected.

**Query API Surface (STORE-02):** `FeedbackStore` class at `agent/feedback_store.py` with `query(skill_id=None, source=None, verdict=None, since=None, until=None, include_superseded=False) -> List[FeedbackRecord]`, `summary(skill_id=None, source=None) -> Dict[BucketKey, BucketSummary]`, `get_record(record_id) -> FeedbackRecord`, `record_feedback(record: FeedbackRecord) -> str`. SQLite rejected (overkill). HTTP endpoint rejected (P33 dashboard reads `index.json` directly).

**Storage Layout:**
```
~/.hermes/skills/.feedback/
├── index.json                          # Queryable index — single source of truth
├── buckets/
│   ├── screenplay/
│   │   ├── cli.jsonl
│   │   ├── kais_aigc.jsonl
│   │   └── manual.jsonl
│   ├── drawer/...
│   └── ... (one subdir per skill_id)
├── dedup/
│   └── sha256-registry.jsonl           # Append-only: {sha256, verdict, record_id, ts}
└── archive/                            # Optional operator-managed prune target
```

`incoming/` (Phase 28 flat layout) becomes a transient staging dir — Phase 29 migrates files to `buckets/` on first access (lazy migration). `inbox-kais/` and `processed-kais/` unchanged.

### Claude's Discretion

- **`record_id` format** — recommend `f"{ts_unix}_{sha256[:8]}"` for sortability + collision-resistance.
- **Migration timing** — lazy on first P29 access (zero-downtime cutover preferred).
- **Thread safety** — single-process access for MVP; add file-lock in P32 if Curator concurrent with operator CLI.
- **Index file format** — JSON (human-readable, matches `agent/curator.py:save_state` pattern). Not MessagePack/CBOR.

### Deferred Ideas (OUT OF SCOPE)

- Concurrent writer support / file locking (P32 Curator may need this)
- Auto-prune of old feedback (operator manually prunes via `rm`)
- PII auto-redaction (FUTURE-V6-06)
- Cross-operator aggregation (v6 is single-operator)
- Index compression (defer unless >100K records measured)
- Snapshot content storage externalization (defer unless snapshots grow large)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| STORE-01 | `~/.hermes/skills/.feedback/` persistent dir structure, `skill_id/source/` sub-dirs, jsonl append | `## Pattern 1: Hybrid persistence (append + atomic)` + `## Recommended Project Structure` |
| STORE-02 | `index.json` queryable by skill_id/verdict/source/timestamp; Curator + dashboard consume single index | `## Pattern 2: FeedbackStore class + index.json schema` + `## Integration Points` |
| STORE-03 | Time-decay weight (default 180 days per CONTEXT.md, configurable) | `## Pattern 3: Linear decay computed at query time` + `## State of the Art` |
| STORE-04 | Dedup by sha256+verdict; same sha256 different verdict = correction (older demoted) | `## Pattern 4: sha256 registry + supersession` + `## Don't Hand-Roll` |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Feedback record persistence (append to jsonl) | Storage tier (local FS under HERMES_HOME) | — | Pure data plumbing; no network surface; JSONL chosen for append-friendliness + grep-ability |
| Index maintenance (counts + weighted_counts) | Storage tier (single `index.json`) | — | Single source of truth so P32 Curator + P33 dashboard don't diverge (SC-2 explicit) |
| Time-decay weight computation | Query/API tier (FeedbackStore methods) | — | Computed at query time so weights stay fresh and decay-window tuning doesn't require record rewrites |
| Dedup detection (sha256 registry) | Storage tier (append-only `dedup/sha256-registry.jsonl`) | In-memory cache on FeedbackStore | Lookup is O(N) on disk but N stays small; scan-on-load into `_sha256_index: dict[str, Record]` for O(1) checks |
| Migration from Phase 28 `incoming/` | Storage tier (lazy on first access) | — | One-shot migration; originals moved to `archive/phase-28-migration/` for audit |
| Query API (`query`/`summary`/`get_record`) | API tier (`FeedbackStore` Python class) | — | Python class — no HTTP server (P33 dashboard reads `index.json` directly per CONTEXT.md) |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (`json`, `pathlib`, `os`, `hashlib`, `datetime`, `logging`, `threading`) | 3.11+ | JSONL append, path resolution, atomic rename, time-decay math | Already in the runtime; no new deps. `[CITED: pyproject.toml:157 requires-python=">=3.11"]` |
| `pydantic` | 2.13.4 | `FeedbackRecord` / `OutputSnapshot` schema (Phase 28 contract) | Already pinned; Phase 29 reads but does not modify the schema. `[VERIFIED: npm registry equivalent — pyproject.toml:60]` |
| `utils.atomic_json_write` | local | Atomic JSON file rewrite (temp + fsync + os.replace) | Already used by Phase 28's `write_feedback_record` and `agent/curator.py:save_state`. `[CITED: utils.py:111-153]` |
| `hermes_constants.get_hermes_home` | local | Resolve `~/.hermes/` honoring `HERMES_HOME` env var | CLAUDE.md mandate; never use `Path.home() / ".hermes"`. `[CITED: hermes_constants.py:53]` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `agent.feedback_schema.FeedbackRecord` | local (Phase 28) | Read/write the canonical feedback record | Every `record_feedback()` call; schema is immutable in P29 |
| `agent.feedback_schema.OutputSnapshot` | local (Phase 28) | Access `sha256` field for dedup | Every dedup check |
| `agent.curator.load_state/save_state` | local | Template for FeedbackStore state load/save | Pattern reference only — copy the style, don't import |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| JSONL append + `index.json` | SQLite under HERMES_HOME | CONTEXT.md rejected SQLite as overkill for ~thousands of records. SQLite adds query power but complicates cross-tool reads (P33 dashboard would need Python, not just JSON). |
| Per-record JSONL files | Single rolling JSONL per bucket | One file per skill_id+source is already a bucket; further sharding adds no benefit at v6 scale. |
| Pre-computed weight on write | Compute weight at query time | Query-time keeps weights fresh; retuning `decay_window_days` doesn't require rewriting records. CHOSEN per CONTEXT.md specifics line 111. |

**Installation:** None — Phase 29 adds zero new dependencies. All required libraries are already pinned in `pyproject.toml`.

**Version verification:** Not applicable — no new packages installed. Existing pins verified via `pyproject.toml:157` (pytest 9.0.2 + pytest-asyncio 1.3.0 for tests) and `pyproject.toml:60` (pydantic 2.13.4).

## Package Legitimacy Audit

Phase 29 installs **zero** external packages. All code reuses the existing stack: Python stdlib, `pydantic==2.13.4`, and Hermes-local modules (`utils.atomic_json_write`, `hermes_constants.get_hermes_home`, `agent.feedback_schema.*`).

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| (none — no new packages) | — | — | — | — | — | N/A |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*No gate needed — the legitimacy protocol only triggers when a phase installs external packages, and this phase installs none.*

## Architecture Patterns

### System Architecture Diagram

```
                     ┌──────────────────────────────────────────────┐
                     │  Phase 28 ingestion sources (UNCHANGED)      │
                     │  ┌────────────┐  ┌──────────┐  ┌──────────┐  │
                     │  │ /feedback  │  │ kais     │  │ JSONL    │  │
                     │  │ slash cmd  │  │ watcher  │  │ importer │  │
                     │  └─────┬──────┘  └────┬─────┘  └────┬─────┘  │
                     │        │              │             │        │
                     │        ▼              ▼             ▼        │
                     │  ┌──────────────────────────────────────┐   │
                     │  │ write_feedback_record(record)        │   │
                     │  │ (agent/feedback_ingest.py:51)        │   │
                     │  └─────────────────┬────────────────────┘   │
                     └────────────────────┼────────────────────────┘
                                          │
                   Phase 29 extension: this becomes a thin wrapper
                                          │
                                          ▼
           ┌──────────────────────────────────────────────────────────┐
           │  FeedbackStore.record_feedback(record) -> record_id       │
           │  (agent/feedback_store.py — NEW)                          │
           │                                                          │
           │  1. Validate (Pydantic — already done by caller)          │
           │  2. Compute record_id = f"{ts_unix}_{sha256[:8]}"         │
           │  3. Append to buckets/<skill_id>/<source>.jsonl           │
           │     (direct append, O(1) per write)                       │
           │  4. Append to dedup/sha256-registry.jsonl                 │
           │  5. Check for existing sha256 in registry:                │
           │     - If same sha256 + same verdict → DUPLICATE, skip     │
           │     - If same sha256 + diff verdict → CORRECTION:         │
           │       mark older status=superseded, weight=0              │
           │  6. Recompute affected bucket's weighted_count (decay)    │
           │  7. atomic_json_write(index.json)                         │
           └─────────────────────────┬────────────────────────────────┘
                                     │
       ┌─────────────────────────────┼─────────────────────────────┐
       │                             │                             │
       ▼                             ▼                             ▼
┌─────────────┐              ┌──────────────┐              ┌──────────────┐
│ buckets/    │              │ index.json   │              │ dedup/       │
│ *.jsonl     │              │ (atomic)     │              │ sha256-      │
│ (append)    │              │              │              │ registry.jsonl│
└─────────────┘              └──────┬───────┘              └──────────────┘
                                    │
                                    │ Single source of truth
                                    │ for counts + weighted_counts
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                                            ▼
   ┌─────────────────────┐                    ┌─────────────────────┐
   │ Phase 32 Curator    │                    │ Phase 33 Dashboard  │
   │ FeedbackStore       │                    │ reads index.json    │
   │ .summary() / .query()│                    │ directly (no Python │
   │                     │                    │ import needed)      │
   └─────────────────────┘                    └─────────────────────┘
```

The diagram shows the primary write path (Phase 28 source → wrapper → `FeedbackStore.record_feedback` → 3 disk writes) and the two consumer paths (P32 Curator via Python API; P33 dashboard via JSON-on-disk contract). The decision point at step 5 (dedup vs correction) is the only branching logic in the write path.

### Recommended Project Structure

```
agent/
├── feedback_schema.py         # Phase 28 — UNCHANGED (schema is frozen)
├── feedback_snapshot.py       # Phase 28 — UNCHANGED
├── feedback_ingest.py         # Phase 28 — write_feedback_record becomes 2-line wrapper
└── feedback_store.py          # Phase 29 — NEW: FeedbackStore class + index maintenance

tests/agent/
├── test_feedback_schema.py    # Phase 28 — UNCHANGED
├── test_feedback_snapshot.py  # Phase 28 — UNCHANGED
├── test_feedback_ingest.py    # Phase 28 — UNCHANGED (wrapper delegation covered here)
├── test_feedback_store.py     # Phase 29 — NEW: unit tests for FeedbackStore
└── test_feedback_store_integration.py  # Phase 29 — NEW: end-to-end Phase 28→29 delegation

# Runtime layout (under HERMES_HOME — NOT in repo)
~/.hermes/skills/.feedback/
├── index.json
├── buckets/<skill_id>/<source>.jsonl
├── dedup/sha256-registry.jsonl
├── archive/phase-28-migration/   # lazy migration moves originals here
├── incoming/                      # Phase 28 staging — becomes transient
├── inbox-kais/                    # Phase 28 — UNCHANGED
├── processed-kais/                # Phase 28 — UNCHANGED
└── errors-kais/                   # Phase 28 — UNCHANGED
```

### Pattern 1: Hybrid persistence (append for buckets, atomic for index)

**What:** Use direct O(1) file append for `buckets/*.jsonl` (append-only data), and full atomic rewrite via `atomic_json_write` for `index.json` (small, crash-sensitive).

**When to use:** Always — this is the chosen strategy for Phase 29.

**Why not atomic for everything:** `atomic_json_write` rewrites the whole file via temp+fsync+os.replace (see `utils.py:111-153`). For a bucket with 5,000 records, every new feedback would rewrite 5,000 lines — O(N) per write, O(N²) over the lifetime of the bucket. At v6 scale (~thousands per bucket) this is tolerable but wasteful; direct append is O(1) and the jsonl format is designed for it. The `index.json` file is tiny (one entry per bucket — maybe ~300 buckets for 31 experts × 3 sources × 3 verdicts) so atomic rewrite is cheap and the crash-safety is worth it.

**Example:**
```python
# Source: utils.py:111-153 (atomic_json_write) + standard Python append idiom

# APPEND path (O(1) per write — for buckets/*.jsonl)
def _append_to_bucket(self, record: FeedbackRecord, bucket_path: Path) -> None:
    line = record.model_dump_json()  # Pydantic v2 — compact JSON, one line
    # encoding="utf-8" is MANDATORY — Ruff PLW1514 (CLAUDE.md)
    with open(bucket_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())  # durability on crash

# ATOMIC path (O(filesize) — for index.json)
def _write_index(self, index: dict) -> None:
    atomic_json_write(  # from utils.py:111
        self._index_path,
        index,
        indent=2,
        sort_keys=True,  # matches agent/curator.py:save_state style
    )
```

`[CITED: utils.py:111-153 for atomic_json_write contract; agent/curator.py:102-107 for save_state pattern]`

### Pattern 2: FeedbackStore class + index.json schema

**What:** One Python class owns the storage. Every write goes through `record_feedback()`. Every read goes through `query()` / `summary()` / `get_record()`. The class maintains an in-memory `_sha256_index: dict[str, _DedupEntry]` loaded once from `dedup/sha256-registry.jsonl` for O(1) dedup checks.

**When to use:** All Phase 29 code paths.

**Index schema (recommended):**
```json
{
  "version": 1,
  "decay_window_days": 180,
  "updated_ts": "2026-06-24T13:30:00+00:00",
  "buckets": {
    "screenplay:cli:good": {
      "count": 12,
      "weighted_count": 9.5,
      "first_ts": "2026-03-01T10:00:00+00:00",
      "last_ts": "2026-06-24T13:30:00+00:00"
    },
    "screenplay:cli:needs_work": {
      "count": 3,
      "weighted_count": 2.8,
      "first_ts": "...",
      "last_ts": "..."
    }
  },
  "by_sha256": {
    "abc123...": {
      "record_id": "1719243000_abc12345",
      "verdict": "good",
      "ts": "2026-06-24T13:30:00+00:00",
      "status": "active"
    },
    "def456...": {
      "record_id": "1719242900_def45678",
      "verdict": "needs_work",
      "ts": "2026-06-20T09:00:00+00:00",
      "status": "superseded",
      "superseded_by": "1719243000_abc12345"
    }
  }
}
```

**Key refinements over the CONTEXT.md sketch:**
1. **Bucket key format `"<skill_id>:<source>:<verdict>"`** — colon-separated (not `_`) so `skill_id` values containing underscores (`hook_retention`, `compliance_gate`) don't collide. Three-level key matches the SC-2 query dimensions exactly (skill_id / verdict / source / ts).
2. **`by_sha256` lives INSIDE `index.json`** (not a separate file) — this makes the index fully self-contained for P33 dashboard reads (single JSON, no second file to coordinate). Cost: `index.json` grows by ~100 bytes per unique sha256, negligible at v6 scale.
3. **The separate `dedup/sha256-registry.jsonl` is the audit log** (append-only, never rewritten). `by_sha256` in `index.json` is the queryable view; `sha256-registry.jsonl` is the durable history. If `index.json` is lost/corrupted, it can be rebuilt from `sha256-registry.jsonl` + `buckets/*.jsonl`.
4. **`status` field** on each sha256 entry distinguishes `active` (counts toward `weighted_count`) from `superseded` (weight=0, retained in raw `count` for audit).
5. **`version: 1`** at the top — forward-compat for schema evolution (decay function change, bucket key format change) without breaking older readers.
6. **`decay_window_days` echoed in index** — makes the index self-describing. P32 Curator reading a stale index knows what decay window was in effect when it was written.

**Example:**
```python
# Source: pattern derived from agent/curator.py:71-117 (state file load/save)

class FeedbackStore:
    """Durable feedback store with index, decay, and dedup."""

    def __init__(self, *, hermes_home: Path | None = None,
                 decay_window_days: int = 180) -> None:
        self._root = (hermes_home or get_hermes_home()) / "skills" / ".feedback"
        self._index_path = self._root / "index.json"
        self._buckets_root = self._root / "buckets"
        self._dedup_path = self._root / "dedup" / "sha256-registry.jsonl"
        self._archive_root = self._root / "archive"
        self._decay_window_days = decay_window_days
        # In-memory dedup cache — loaded once, updated incrementally.
        self._sha256_index: dict[str, dict] = {}
        self._load_sha256_index()
        # Lazy migration on first init if incoming/ has files.
        self._maybe_migrate_phase28_incoming()

    def record_feedback(self, record: FeedbackRecord) -> str:
        record_id = self._make_record_id(record)
        # ... dedup check, bucket append, index update (see Pattern 4)
        return record_id

    def query(self, *, skill_id=None, source=None, verdict=None,
              since=None, until=None, include_superseded=False) -> list[FeedbackRecord]:
        # Scan relevant bucket files, apply filters, return FeedbackRecord list.
        ...

    def summary(self, *, skill_id=None, source=None) -> dict[str, dict]:
        # Read index.json, return filtered bucket summaries.
        ...

    def get_record(self, record_id: str) -> FeedbackRecord | None:
        # Scan bucket files for matching record_id (linear; v6 scale OK).
        ...
```

`[CITED: agent/curator.py:71-117 (_state_file + load_state + save_state template); CONTEXT.md decisions: Query API Surface]`

### Pattern 3: Linear decay computed at query time

**What:** Do NOT store `weight` in the feedback record. Store only the raw `ts`. Compute `weight` from `age_days = (now - record.ts).days` whenever `weighted_count` needs to be (re)computed.

**When to use:** Always — this is the chosen strategy. CONTEXT.md specifics line 111 makes this explicit: "Time-decay is computed on QUERY, not on write."

**Why:** If weights were stored on write, they'd go stale — a record written 30 days ago with weight=1.0 actually "weighs" 0.83 today. Storing only `ts` keeps the source of truth immutable; weights are always fresh.

**Index update strategy:** `weighted_count` IS stored in `index.json` (so P33 dashboard doesn't have to recompute), but it's recomputed from raw `ts` values on every write. To recompute, `FeedbackStore` needs access to all `ts` values in the bucket — so it reads the bucket file when updating the index. At v6 scale (~thousands of records per bucket) this is fast; for >100K records a future phase can cache `ts_list` in memory.

**Example:**
```python
# Source: CONTEXT.md decisions: Time-Decay Function (STORE-03)
from datetime import datetime, timezone

def compute_weight(ts: datetime, *, now: datetime | None = None,
                   decay_window_days: int = 180) -> float:
    """Linear time-decay weight.

    - 0 days old: weight = 1.0 (full signal)
    - 90 days old: weight = 0.5
    - 180 days old: weight = 0.0 floored at 0.1
    - >180 days: weight = 0.1 (never fully zero — old signal still counts weakly)
    """
    now = now or datetime.now(timezone.utc)
    age_days = max(0.0, (now - ts).total_seconds() / 86400.0)
    raw_weight = 1.0 - (age_days / decay_window_days)
    return max(0.1, raw_weight)


def recompute_bucket_weighted_count(
    records: list[FeedbackRecord],
    *,
    now: datetime | None = None,
    decay_window_days: int = 180,
) -> float:
    """Sum of weights for non-superseded records in a bucket.

    Superseded records (weight=0 by definition) contribute nothing.
    Round to 2 decimal places for clean index.json reads.
    """
    now = now or datetime.now(timezone.utc)
    total = sum(
        compute_weight(r.ts, now=now, decay_window_days=decay_window_days)
        for r in records
        if getattr(r, "status", "active") == "active"
    )
    return round(total, 2)
```

`[CITED: CONTEXT.md decisions: Time-Decay Function]`

### Pattern 4: sha256 registry + supersession (correction handling)

**What:** Every `record_feedback()` call appends a line to `dedup/sha256-registry.jsonl` and updates `index.json["by_sha256"]`. The in-memory `_sha256_index` dict enables O(1) lookup.

**Decision matrix on write:**

| Condition | Action | Effect on index |
|-----------|--------|-----------------|
| New sha256 (not in registry) | Append to registry; add to `by_sha256` with `status="active"` | Bucket `count` +1; `weighted_count` += weight(new record) |
| Same sha256 + same verdict (DUPLICATE) | Reject — return existing `record_id`, do NOT write | No change |
| Same sha256 + different verdict (CORRECTION) | Append new entry to registry; mark OLD `by_sha256` entry `status="superseded"`, `weight=0`; add NEW entry `status="active"` | Bucket of OLD verdict: `weighted_count` -= weight(old); bucket of NEW verdict: `count` +1, `weighted_count` += weight(new). Raw `count` of OLD bucket UNCHANGED (audit). |

**Example:**
```python
# Source: CONTEXT.md decisions: Correction Weight Demotion (STORE-04)

def _handle_dedup(self, record: FeedbackRecord, record_id: str) -> str:
    """Returns the record_id that should be persisted (may be the existing one)."""
    sha = record.output_snapshot.sha256
    existing = self._sha256_index.get(sha)

    if existing is None:
        # New sha256 — no dedup action needed.
        return record_id

    if existing["verdict"] == record.verdict:
        # DUPLICATE: identical sha256 + identical verdict.
        # Do NOT double-count. Return the existing record_id; caller skips write.
        logger.info(
            "feedback duplicate detected: sha256=%s verdict=%s existing_record_id=%s",
            sha[:8], record.verdict, existing["record_id"],
        )
        return existing["record_id"]

    # CORRECTION: same sha256, different verdict.
    # Mark the older record superseded (weight=0 going forward).
    older_id = existing["record_id"]
    self._mark_superseded(sha=sha, older_record_id=older_id,
                          newer_record_id=record_id)
    logger.info(
        "feedback correction: sha256=%s older_verdict=%s -> newer_verdict=%s "
        "(older_record_id=%s weight zeroed)",
        sha[:8], existing["verdict"], record.verdict, older_id,
    )
    return record_id  # proceed with write


def _mark_superseded(self, *, sha: str, older_record_id: str,
                     newer_record_id: str) -> None:
    """Update by_sha256 entry: older -> status=superseded, newer -> active."""
    # The in-memory index + index.json["by_sha256"] both get updated.
    # The bucket file containing the older record is NOT rewritten —
    # instead, a "supersession marker" is appended to the registry:
    #   {"sha256": "...", "event": "superseded", "older": "...", "newer": "...", "ts": "..."}
    # Query() filters out records whose record_id appears as "older" in any
    # supersession event (unless include_superseded=True).
    ...
```

**Important nuance:** When a CORRECTION happens, the OLDER record's bytes are still in its bucket file (we don't rewrite bucket files — they're append-only). Instead, the `by_sha256[sha]` entry is updated to point at the NEWER record_id with `status="active"`, and the OLDER entry gets `status="superseded"`. When `query()` scans a bucket file, it cross-references each record against `by_sha256` to determine its effective status. This keeps bucket files immutable while still supporting correction semantics.

`[CITED: CONTEXT.md decisions: Correction Weight Demotion; SC-4 success criterion]`

### Anti-Patterns to Avoid

- **Storing `weight` on the FeedbackRecord** — goes stale; forces record rewrite when decay window changes. Store only `ts`; compute weight at query time.
- **Rewriting `buckets/*.jsonl` on every write via `atomic_json_write`** — O(N) per write, O(N²) over bucket lifetime. Use direct append for buckets; reserve atomic rewrite for `index.json`.
- **Multiple consumers scanning `buckets/` independently** — SC-2 explicitly forbids this; it causes count divergence between Curator and dashboard. `index.json` is the single source of truth.
- **Using `_` as the bucket key separator** — skill_ids like `hook_retention` contain underscores. Use `:` (colon) as the separator: `"screenplay:cli:good"`.
- **`Path.home() / ".hermes"` in production code** — CLAUDE.md anti-pattern; use `get_hermes_home()` from `hermes_constants`. Test fixture monkeypatches `Path.home` and the production path bypasses it.
- **`open()` without `encoding="utf-8"`** — Ruff PLW1514 will block the merge. Every text-mode `open()` must be explicit (CLAUDE.md).
- **Eager migration of `incoming/` on every init** — expensive on cold start if `incoming/` has many files. Migrate lazily (once-per-process flag, only if `incoming/` is non-empty AND `buckets/` is empty or missing).
- **In-memory mutation of `_sha256_index` without writing to disk** — crash loses the dedup state. Always append to `sha256-registry.jsonl` BEFORE returning from `record_feedback`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atomic JSON file writes | Temp file + fsync + os.replace from scratch | `utils.atomic_json_write` (`utils.py:111`) | Already handles symlinks (`atomic_replace`), file mode preservation, fsync. Battle-tested in `curator.save_state` and Phase 28. |
| Pydantic schema for FeedbackRecord | New `Record` dataclass | `agent.feedback_schema.FeedbackRecord` (Phase 28) | Schema is frozen in P29 — extending it would break Phase 28 callers. |
| HERMES_HOME resolution | `Path.home() / ".hermes"` | `hermes_constants.get_hermes_home()` | Honors `HERMES_HOME` env var + `active_profile` override; CLAUDE.md mandate. |
| Record persistence (write path) | New `store_feedback()` function | `agent.feedback_ingest.write_feedback_record` (Phase 28) | Existing callers (`/feedback` slash cmd, kais watcher, JSONL importer) all use it. Wrap it, don't replace it. |
| Expert ID validation | Hardcoded list | `agent.feedback_schema._KNOWN_EXPERT_IDS` (auto-discovered) | Already covers all 31 current experts + v3/v4/v5 additions automatically. |
| Decay function formula | Custom sigmoid / exponential | Linear `max(0.1, 1.0 - age/180)` per CONTEXT.md | Operator-tunable; predictable behavior; floor at 0.1 preserves weak signal from very old feedback. |

**Key insight:** Phase 29 is glue code — every primitive it needs already exists. The novel work is (a) the `FeedbackStore` class skeleton, (b) the `index.json` schema design, (c) the dedup/correction branching logic. All filesystem operations, schema validation, and atomicity primitives are reused.

## Runtime State Inventory

> Phase 29 restructures the on-disk layout under `~/.hermes/skills/.feedback/`. This is a rename/migration phase, so the runtime state inventory is mandatory.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| **Stored data** | Phase 28 writes records to `incoming/*.json` (one file per record, flat layout). After Phase 28 ships, this directory may contain any number of feedback records from `/feedback`, the kais watcher (no — those go to `incoming/` after watcher writes), or JSONL importer. | **Lazy migration on first FeedbackStore init:** scan `incoming/*.json`, parse each as `FeedbackRecord`, route to `buckets/<skill_id>/<source>.jsonl`, move original to `archive/phase-28-migration/<filename>`. Idempotent (re-running finds `incoming/` empty, no-op). |
| **Live service config** | None — no external services have configuration stored outside git. The kais-aigc watcher reads from `inbox-kais/` (unchanged by P29). | None |
| **OS-registered state** | None — no Task Scheduler / launchd / systemd / pm2 entries reference feedback paths. | None |
| **Secrets/env vars** | `HERMES_FEEDBACK_INBOX_KAIS` env var (Phase 28 watcher) — path override for kais inbox. Code references this by name; env var name UNCHANGED. | None — code reads env var by name, name is stable. |
| **Build artifacts** | `agent/feedback_schema.py`, `agent/feedback_snapshot.py`, `agent/feedback_ingest.py` exist as compiled `.pyc` in `__pycache__/`. After modifying `feedback_ingest.py` (to add the wrapper delegation), Python will recompile automatically on next import. No manual cleanup needed. | None (automatic) |

**Migration verification commands** (planner should add as a Wave 0 task):
```bash
# Pre-flight: confirm Phase 28 write path is the only writer to incoming/
grep -rn 'incoming' agent/ tests/ | grep -v test_ | grep -v '__pycache__'
# Expected: only agent/feedback_ingest.py references 'incoming'

# Post-migration: confirm incoming/ is empty after first FeedbackStore init
ls ~/.hermes/skills/.feedback/incoming/  # should be empty (or dir absent)
ls ~/.hermes/skills/.feedback/archive/phase-28-migration/  # originals preserved
ls ~/.hermes/skills/.feedback/buckets/  # records routed to skill_id/source.jsonl
```

## Common Pitfalls

### Pitfall 1: Encoding errors on Windows / Termux
**What goes wrong:** `open(path, "a")` without `encoding="utf-8"` defaults to cp1252 on Windows, corrupting any non-ASCII Chinese text in `output_snapshot.output_text` or `correction` fields.
**Why it happens:** Python's default text encoding follows the OS locale. CLAUDE.md enforces Ruff PLW1514 specifically to catch this.
**How to avoid:** Every text-mode `open()` — append AND read — must pass `encoding="utf-8"`. The append path in Pattern 1 shows the correct idiom.
**Warning signs:** Tests pass on Linux CI but fail on a Windows operator's machine; Chinese characters render as mojibake in `index.json`.

### Pitfall 2: Stale weights if computed on write
**What goes wrong:** If `weight` is computed and stored in the feedback record at write time, it goes stale — a record written 60 days ago shows `weight=0.67` but its true current weight is `0.33`. Downstream aggregation silently mis-weights old feedback.
**Why it happens:** It feels "simpler" to compute once at write time. But decay is a function of *current age*, not *age at write*.
**How to avoid:** Store only `ts` in the record. Compute weight in `recompute_bucket_weighted_count()` at every index update. CONTEXT.md specifics line 111 makes this the chosen strategy.
**Warning signs:** `weighted_count` in `index.json` doesn't change when records age (because it was frozen at write time).

### Pitfall 3: Bucket filename race in correction path
**What goes wrong:** Two near-simultaneous feedback writes for the same `sha256` (same operator double-clicking `/feedback`, or watcher batch importing a file with the same record twice) race through dedup check → both pass as "new" → both write → `by_sha256` ends up with two active entries for the same sha.
**Why it happens:** Phase 29 assumes single-process (CONTEXT.md Claude's-discretion + Deferred Ideas). But the CLI and the kais watcher COULD run concurrently if an operator starts both.
**How to avoid:** Document the single-process assumption in the `feedback_store.py` module docstring. If concurrent writers are observed in P32, add `fcntl.flock` (Unix) / `msvcrt.locking` (Windows) on a `.lock` file. For v6 MVP, the worst case is a duplicate record that a future `hermes feedback dedup-repair` command can clean up — no data loss.
**Warning signs:** `len(by_sha256)` != number of unique sha256 values in `dedup/sha256-registry.jsonl`.

### Pitfall 4: Migration not idempotent
**What goes wrong:** First `FeedbackStore.__init__` migrates `incoming/*.json` → `buckets/` → moves originals to `archive/phase-28-migration/`. If the process crashes mid-migration, some originals are in `archive/`, some are still in `incoming/`, and some buckets have the records. Second init re-migrates the remaining `incoming/` files — but what about the ones already migrated?
**Why it happens:** Migration state isn't checkpointed.
**How to avoid:** Migration is naturally idempotent IF (a) the bucket append is idempotent for the same record_id (record_id includes `ts_unix_microsecond + sha256[:8]`, so duplicates would be exact dupes and could be skipped), AND (b) the move-to-archive step happens AFTER the bucket append succeeds. Order matters: append first, then move. If append succeeds but move fails, next init re-appends (a duplicate line in the bucket — harmless, dedup catches it) and re-tries the move.
**Warning signs:** Bucket file has duplicate lines; `archive/phase-28-migration/` is missing files that are no longer in `incoming/`.

### Pitfall 5: index.json corruption on crash mid-write
**What goes wrong:** Process crashes between temp-file-write and `os.replace` → `index.json` is left as the OLD version (atomic write guarantees this). But if the process crashes AFTER the bucket append but BEFORE the index update, the bucket has a record the index doesn't know about.
**Why it happens:** The bucket append and index update are not in one transaction.
**How to avoid:** `atomic_json_write` already protects `index.json` itself (temp + fsync + os.replace — see `utils.py:111-153`). For bucket/index divergence, add a `rebuild_index()` method (or `hermes feedback rebuild-index` CLI command per CONTEXT.md specifics line 111) that scans all `buckets/*.jsonl` + `dedup/sha256-registry.jsonl` and regenerates `index.json` from scratch. Operator runs this if counts look wrong. SC-2 doesn't require zero-divergence under crash; it requires the index to be queryable and eventually-consistent.
**Warning signs:** `sum(bucket.count for bucket in index.buckets.values())` != number of lines across all `buckets/*.jsonl`.

### Pitfall 6: Bucket key separator collision
**What goes wrong:** Using `_` as separator: `hook_retention_cli_good` is ambiguous (is the skill_id `hook_retention` or `hook`?).
**Why it happens:** Skill_ids like `hook_retention`, `compliance_gate`, `scene_builder` contain underscores.
**How to avoid:** Use `:` as the separator: `"hook_retention:cli:good"`. Colons are illegal in Windows filenames BUT the bucket key is a JSON object key, NOT a filename — so this is safe. Filenames use `buckets/hook_retention/cli.jsonl` (directory-per-skill, file-per-source — no collision).
**Warning signs:** `query(skill_id="hook")` returns records that belong to `hook_retention`.

### Pitfall 7: Timezone-naive datetime in decay computation
**What goes wrong:** `datetime.now()` (no tz) minus `record.ts` (tz-aware UTC) raises `TypeError`. Or `record.ts` is tz-aware but `now` is naive, giving wrong age.
**Why it happens:** `FeedbackRecord.ts` validator (`agent/feedback_schema.py:223`) already rejects naive datetimes, but internal `now` computations must also use tz-aware UTC.
**How to avoid:** Always use `datetime.now(timezone.utc)` in decay computations. The Pattern 3 example shows this.
**Warning signs:** `TypeError: can't subtract offset-naive and offset-aware datetimes` in production.

## Code Examples

### Example 1: write_feedback_record becomes a thin wrapper (Phase 29 integration)

```python
# Source: derived from agent/feedback_ingest.py:51-102 (Phase 28) + CONTEXT.md Integration Points

# AFTER Phase 29, agent/feedback_ingest.py:write_feedback_record becomes:

def write_feedback_record(record: FeedbackRecord) -> Path:
    """Atomically persist a validated FeedbackRecord to disk.

    Phase 29: delegates to FeedbackStore.record_feedback(). Existing
    callers (CLI /feedback, kais watcher, JSONL importer) work unchanged.
    """
    from agent.feedback_store import FeedbackStore  # lazy import to avoid cycle
    store = FeedbackStore()  # reads hermes_home + config lazily
    record_id = store.record_feedback(record)
    # Return the bucket path for backward compat with Phase 28 callers
    # that print the written path (e.g., the /feedback slash command).
    return store.bucket_path_for(record)
```

`[CITED: agent/feedback_ingest.py:51-102; CONTEXT.md code_context: Integration Points]`

### Example 2: record_id generation (collision-resistant + sortable)

```python
# Source: CONTEXT.md Claude's Discretion (record_id format)

import time
from datetime import timezone

def _make_record_id(record: FeedbackRecord) -> str:
    """Generate a sortable, collision-resistant record_id.

    Format: f"{ts_unix_micro}_{sha256[:8]}"
      - ts_unix_micro: microseconds since epoch (sortable, sub-ms precision)
      - sha256[:8]: 8 hex chars from output_snapshot.sha256 (collision-resistant)

    Example: '1719243000123456_abc12345'
    """
    # record.ts is guaranteed tz-aware by FeedbackRecord._ts_has_tz validator.
    ts_unix_micro = int(record.ts.timestamp() * 1_000_000)
    sha_prefix = record.output_snapshot.sha256[:8]
    return f"{ts_unix_micro}_{sha_prefix}"
```

`[CITED: agent/feedback_schema.py:223 (_ts_has_tz validator); CONTEXT.md Claude's Discretion]`

### Example 3: Lazy migration from Phase 28 incoming/

```python
# Source: CONTEXT.md code_context: Integration Points (lazy migration)

def _maybe_migrate_phase28_incoming(self) -> None:
    """Migrate Phase 28's flat incoming/ layout to buckets/ (lazy, idempotent).

    Triggered once per process on FeedbackStore.__init__. If incoming/ is
    empty OR has already been migrated (we track via a sentinel file),
    this is a no-op.

    Migration algorithm:
      1. List incoming/*.json (if empty, return).
      2. Write a .migrating sentinel (crash recovery marker).
      3. For each file: parse as FeedbackRecord, append to buckets/
         via the normal record_feedback path (dedup-aware), then move
         the original to archive/phase-28-migration/.
      4. Remove the sentinel.
    """
    incoming_dir = self._root / "incoming"
    if not incoming_dir.is_dir():
        return
    pending = sorted(incoming_dir.glob("*.json"))
    if not pending:
        return  # nothing to migrate

    archive_dir = self._archive_root / "phase-28-migration"
    archive_dir.mkdir(parents=True, exist_ok=True)
    sentinel = self._root / ".migration-in-progress"
    sentinel.touch(exist_ok=True)  # idempotent across crashes

    migrated = 0
    for src_path in pending:
        try:
            raw = json.loads(src_path.read_text(encoding="utf-8"))
            record = FeedbackRecord(**raw)
            # Re-route through the normal store path. Dedup may reject
            # if the record was already migrated on a previous partial run.
            self.record_feedback(record)
            # Move original to archive for audit (do NOT delete).
            safe_name = src_path.name  # already sanitized by Phase 28
            target = archive_dir / safe_name
            src_path.rename(target)
            migrated += 1
        except Exception as exc:  # noqa: BLE001 — migration must not crash init
            logger.warning(
                "phase-28 migration skipped %s: %s (left in incoming/ for retry)",
                src_path.name, exc,
            )

    sentinel.unlink(missing_ok=True)
    if migrated:
        logger.info(
            "phase-28 feedback migration: moved %d records from incoming/ to buckets/",
            migrated,
        )
```

`[CITED: CONTEXT.md code_context: Integration Points; agent/feedback_ingest.py:_scan_once for the rename-with-fallback pattern]`

### Example 4: Config integration (feedback: section)

```yaml
# Source: derived from cli-config.yaml.example structure (memory: at line 496,
# curator: defaults in hermes_cli/config.py:1986). Top-level section style.

# =============================================================================
# Feedback Store (v6.0 Self-Evolution)
# =============================================================================
# Controls the durable feedback persistence layer. Feedback records land under
# ~/.hermes/skills/.feedback/ in skill_id/source/ buckets after Phase 29.
feedback:
  # Time-decay window in days. Feedback older than this decays linearly
  # toward a 0.1 floor (never fully zero — old signal still counts weakly).
  # weight = max(0.1, 1.0 - (age_days / decay_window_days))
  # Default: 180 days (6 months). Operators can tune + restart Hermes.
  decay_window_days: 180
```

```python
# Source: derived from agent/curator.py:_load_config (line 124-137)

def _load_feedback_config() -> dict:
    """Read feedback.* config from ~/.hermes/config.yaml. Tolerates missing file."""
    try:
        from hermes_cli.config import load_config
        cfg = load_config()
    except Exception as exc:
        logger.debug("Failed to load config for feedback: %s", exc)
        return {}
    if not isinstance(cfg, dict):
        return {}
    fb = cfg.get("feedback") or {}
    return fb if isinstance(fb, dict) else {}

DEFAULT_DECAY_WINDOW_DAYS = 180

def get_decay_window_days() -> int:
    cfg = _load_feedback_config()
    try:
        return int(cfg.get("decay_window_days", DEFAULT_DECAY_WINDOW_DAYS))
    except (TypeError, ValueError):
        return DEFAULT_DECAY_WINDOW_DAYS
```

`[CITED: agent/curator.py:124-137 (_load_config pattern); cli-config.yaml.example line 496 (memory: section style); CONTEXT.md decisions: Time-Decay Function]`

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Phase 28 flat `incoming/*.json` (one file per record) | Phase 29 `buckets/<skill_id>/<source>.jsonl` (append-only, one file per bucket) | Phase 29 (this phase) | O(1) append per write (was O(1) per write via `atomic_json_write` but with full-file rewrite). Enables bucket-level queries without scanning all files. |
| No queryable index (Phase 28 just dumps files) | `index.json` single source of truth for counts + weighted_counts | Phase 29 (this phase) | P32 Curator + P33 dashboard read one small JSON instead of scanning thousands of files. SC-2 requirement. |
| No decay (Phase 28 all records equal weight) | Linear decay `max(0.1, 1.0 - age/180)` at query time | Phase 29 (this phase) | Old feedback doesn't dominate learning signal. Operator-tunable via config. |
| No dedup (Phase 28 captures sha256 but doesn't act on it) | sha256 registry + correction demotion | Phase 29 (this phase) | Same output snapshot can't be double-counted; corrections zero out the older verdict. |

**Deprecated/outdated:**
- Phase 28's `incoming/` as the primary storage location — becomes a transient staging dir after Phase 29 ships. Watcher and CLI still write there only if `FeedbackStore` isn't initialized (e.g., direct test writes); the lazy migration picks them up.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Single-process access is sufficient for v6 MVP (no concurrent writers) | Pattern 4 / Pitfall 3 | If operator runs CLI + watcher simultaneously, dedup races could create duplicate active entries for one sha256. Mitigation: document the assumption + add a `dedup-repair` command in a future phase. |
| A2 | v6 scale is ~thousands of records per bucket (not millions) | Pattern 1 / Pattern 2 | If scale is 10x higher, `index.json` weighted_count recomputation (which scans bucket files) becomes slow. Mitigation: cache `ts_list` in memory inside `FeedbackStore`; the API doesn't change. |
| A3 | Bucket files are never rewritten (append-only) | Pattern 4 | If a future phase needs to edit records in place, the supersession-marker approach (status field in index, original bytes preserved) will need extension. Low risk — v6 scope explicitly defers in-place edits. |
| A4 | `record_id = f"{ts_unix_micro}_{sha256[:8]}"` is unique in practice | Code Example 2 | Two records with the same microsecond-precision timestamp AND same sha256[:8] collide. Microsecond precision makes this astronomically unlikely (~1 in 10^12 per second). If observed, add a counter suffix. |
| A5 | `archive/phase-28-migration/` is an acceptable audit location | Runtime State Inventory | If operators consider the archive "clutter," they may delete it. Migration is idempotent so deletion is safe — but audit trail is lost. Document in operator README (out of scope for P29). |
| A6 | `feedback:` is the right top-level config section name | Code Example 4 | If `skills.feedback` or `feedback_store` was intended, config won't load. CONTEXT.md specifics line 112 explicitly says "top-level `feedback:` section" — this is verified, not assumed. (Listed for traceability.) |

## Open Questions

1. **Migration trigger for tests** — Should the lazy migration run on `FeedbackStore.__init__`, or on first `record_feedback()` / `query()` call? Init is simpler but slower for tests that don't care about migration. Recommend: init, gated by a `_migrated: bool` instance flag. Tests that don't want migration can use the existing `feedback_env` fixture pattern (isolated HERMES_HOME with empty `incoming/`).

2. **Bucket file rotation** — When (if ever) should a bucket file be rotated? v6 doesn't need this (no auto-prune per Deferred Ideas). Flag for P33+ if a bucket file exceeds 100MB.

3. **Index rebuild CLI** — CONTEXT.md specifics line 111 mentions `hermes feedback rebuild-index` as the decay-tuning trigger. Is this in P29 scope or P30+? Recommend: P29 ships `FeedbackStore.rebuild_index()` as a public method; the CLI wrapper (`hermes feedback rebuild-index`) is a thin 5-line addition that fits naturally. Planner's call.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | All Phase 29 code | ✓ | 3.13 (per `[tool.ty.environment] python-version = "3.13"` in pyproject.toml:358) | — |
| pytest | Test suite | ✓ | 9.0.2 (pyproject.toml:157) | — |
| pytest-asyncio | Async test support (if needed) | ✓ | 1.3.0 (pyproject.toml:157) | — |
| Pydantic | FeedbackRecord schema | ✓ | 2.13.4 (pyproject.toml:60) | — |
| ruff | Lint (PLW1514 encoding check) | ✓ | 0.15.10 (pyproject.toml:157) | — |
| ty (type check, advisory) | CI lint | ✓ | 0.0.21 (pyproject.toml:157) | — |
| Filesystem (`~/.hermes/`) | Persistence | ✓ | Linux/macOS/Windows/Termux (all first-class per CLAUDE.md Platform Requirements) | — |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None — every required tool is already installed and pinned.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 (sync tests only — no async needed for FeedbackStore) |
| Config file | `pyproject.toml:348` (`[tool.pytest.ini_options]`, `testpaths=["tests"]`, `addopts="-m 'not integration'"`) |
| Quick run command | `pytest tests/agent/test_feedback_store.py -x` |
| Full suite command | `pytest tests/agent/test_feedback_store.py tests/agent/test_feedback_store_integration.py tests/agent/test_feedback_ingest.py -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STORE-01 | Bucket dir layout (`buckets/<skill_id>/<source>.jsonl`) created on first write | unit | `pytest tests/agent/test_feedback_store.py::TestRecordFeedback::test_bucket_layout -x` | ❌ Wave 0 |
| STORE-01 | Append-only semantics (existing bytes unchanged on new write) | unit | `pytest tests/agent/test_feedback_store.py::TestRecordFeedback::test_append_only -x` | ❌ Wave 0 |
| STORE-01 | Migration from Phase 28 `incoming/` routes records to correct buckets | unit | `pytest tests/agent/test_feedback_store.py::TestMigration::test_migrate_incoming -x` | ❌ Wave 0 |
| STORE-01 | Migration is idempotent (re-running finds `incoming/` empty) | unit | `pytest tests/agent/test_feedback_store.py::TestMigration::test_migration_idempotent -x` | ❌ Wave 0 |
| STORE-02 | `index.json` has expected schema (version, decay_window_days, buckets, by_sha256) | unit | `pytest tests/agent/test_feedback_store.py::TestIndex::test_index_schema -x` | ❌ Wave 0 |
| STORE-02 | `query(skill_id=...)` filters correctly | unit | `pytest tests/agent/test_feedback_store.py::TestQuery::test_query_by_skill_id -x` | ❌ Wave 0 |
| STORE-02 | `query(verdict=..., source=..., since=..., until=...)` composes | unit | `pytest tests/agent/test_feedback_store.py::TestQuery::test_query_composed_filters -x` | ❌ Wave 0 |
| STORE-02 | `summary()` returns per-bucket counts + weighted_counts | unit | `pytest tests/agent/test_feedback_store.py::TestSummary::test_summary_per_bucket -x` | ❌ Wave 0 |
| STORE-02 | `get_record(record_id)` returns the right FeedbackRecord | unit | `pytest tests/agent/test_feedback_store.py::TestGetRecord::test_get_record -x` | ❌ Wave 0 |
| STORE-02 | Phase 28 `write_feedback_record` delegates to FeedbackStore | integration | `pytest tests/agent/test_feedback_store_integration.py::TestDelegation::test_write_feedback_record_delegates -x` | ❌ Wave 0 |
| STORE-03 | `compute_weight(ts, now)` returns 1.0 at age=0 | unit | `pytest tests/agent/test_feedback_store.py::TestDecay::test_weight_at_birth -x` | ❌ Wave 0 |
| STORE-03 | `compute_weight` returns 0.5 at age=90 (half decay window) | unit | `pytest tests/agent/test_feedback_store.py::TestDecay::test_weight_at_half -x` | ❌ Wave 0 |
| STORE-03 | `compute_weight` floors at 0.1 for age > decay_window_days | unit | `pytest tests/agent/test_feedback_store.py::TestDecay::test_weight_floor -x` | ❌ Wave 0 |
| STORE-03 | `weighted_count` in index differs from raw `count` when bucket has old records | unit | `pytest tests/agent/test_feedback_store.py::TestDecay::test_weighted_count_differs -x` | ❌ Wave 0 |
| STORE-03 | `decay_window_days` configurable via config | unit | `pytest tests/agent/test_feedback_store.py::TestDecay::test_config_override -x` | ❌ Wave 0 |
| STORE-04 | Duplicate (same sha256 + same verdict) is NOT written | unit | `pytest tests/agent/test_feedback_store.py::TestDedup::test_duplicate_rejected -x` | ❌ Wave 0 |
| STORE-04 | Correction (same sha256 + diff verdict) demotes older record | unit | `pytest tests/agent/test_feedback_store.py::TestDedup::test_correction_demotes_older -x` | ❌ Wave 0 |
| STORE-04 | After correction, `weighted_count` reflects only the newer verdict's bucket | unit | `pytest tests/agent/test_feedback_store.py::TestDedup::test_correction_weighted_count -x` | ❌ Wave 0 |
| STORE-04 | `query(include_superseded=True)` returns both records | unit | `pytest tests/agent/test_feedback_store.py::TestDedup::test_query_includes_superseded -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/agent/test_feedback_store.py -x` (unit tests for the changed code path)
- **Per wave merge:** `pytest tests/agent/test_feedback_store.py tests/agent/test_feedback_store_integration.py tests/agent/test_feedback_ingest.py tests/agent/test_feedback_schema.py -x` (full feedback subsystem — catches delegation regressions)
- **Phase gate:** Full suite green + manual verification of SC-1..4 + FOUND-08 byte-intact check (`git diff v5.0 -- skills/movie-experts/` minus `_eval/_shared` returns empty)

### Wave 0 Gaps

- [ ] `tests/agent/test_feedback_store.py` — covers STORE-01/02/03/04 unit tests (TestRecordFeedback, TestQuery, TestSummary, TestGetRecord, TestDecay, TestDedup, TestIndex, TestMigration)
- [ ] `tests/agent/test_feedback_store_integration.py` — covers Phase 28→29 delegation (TestDelegation: write_feedback_record wrapper, /feedback slash command still works end-to-end, JSONL importer routes through store)
- [ ] `tests/agent/test_feedback_ingest.py` — may need a new test asserting the wrapper delegation (or this lives in the integration file)
- [ ] Test fixture: extend `feedback_env` (already exists at `tests/agent/test_feedback_ingest.py`) to also reload `agent.feedback_store` after HERMES_HOME monkeypatch — same importlib.reload pattern

*(No framework install needed — pytest 9.0.2 already pinned in `[dev]` extra.)*

## Security Domain

> Phase 29 introduces no new authentication, network surface, or secret handling. The security considerations are limited to filesystem safety (atomic writes, path traversal defense during migration, encoding correctness). ASVS V1/V13 (filesystem + API) are the only marginally-relevant categories, and they're covered by existing code (`atomic_json_write`, `get_hermes_home`).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V1 Architecture | yes (weakly) | `FeedbackStore` is the single owner of feedback persistence (SC-2 single-source-of-truth invariant) |
| V2 Authentication | no | No auth in Phase 29 — local file storage only |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | Local operator-only; HERMES_HOME assumed trusted |
| V5 Input Validation | yes | Pydantic `FeedbackRecord` validation already enforced by Phase 28 schema (skill_id against `_KNOWN_EXPERT_IDS`, verdict enum, sha256 64-hex, ts tz-aware) |
| V6 Cryptography | no | No crypto in Phase 29 — sha256 is for dedup, not security |
| V7 Error Handling | yes | Specific exception types (`OSError`, `ValidationError`), never bare `except:`; lazy %-logging per CLAUDE.md |
| V13 API & Web Service | no | No HTTP endpoint in Phase 29 (P33 dashboard reads `index.json` directly) |

### Known Threat Patterns for Python local-file storage

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal during migration (crafted `incoming/` filename escapes `buckets/`) | Tampering | Migration writes target paths ONLY from `record.skill_id` + `record.source` (validated fields), never from the source filename. Same defense as Phase 28 watcher (T-28-06). |
| Symlink injection in `incoming/` (adversary symlinks a sensitive file) | Information disclosure | Migration uses `Path.read_text(encoding="utf-8")` which follows symlinks — but migration is triggered by `FeedbackStore.__init__` in a trusted operator context. Document the assumption. Phase 28 watcher already rejects symlinks (T-28-06 mitigation in `_scan_once`). |
| File mode leak (other users on shared system read feedback) | Information disclosure | `atomic_json_write` creates temp files as 0o600 by default (`tempfile.mkstemp`); `index.json` inherits parent dir mode. For append-only bucket files, `open(path, "a")` creates with default mode (0o644 on most systems). If stricter mode is needed, `os.chmod(path, 0o600)` after first creation. Defer to operator policy — v6 assumes trusted environment. |
| Race condition on `index.json` (two writers) | Tampering | Phase 29 assumes single-process (CONTEXT.md Deferred Ideas + Pitfall 3). Document in module docstring. |

## Sources

### Primary (HIGH confidence)

- `agent/feedback_schema.py:1-229` — Phase 28 `FeedbackRecord` + `OutputSnapshot` schema. Read in full; this is the immutable contract Phase 29 consumes.
- `agent/feedback_ingest.py:1-463` — Phase 28 write path + watcher + JSONL importer. Read in full; `write_feedback_record:51` is the integration point.
- `agent/curator.py:1-150` — `_state_file()` / `load_state` / `save_state` / `_load_config` template for FeedbackStore. Read in full.
- `utils.py:111-170` — `atomic_json_write` contract (temp + fsync + os.replace, `ensure_ascii=False` hardcoded, symlink-safe via `atomic_replace`).
- `.planning/phases/29-feedback-store/29-CONTEXT.md` — user decisions (locked): index strategy, decay function, correction handling, Query API surface, storage layout.
- `.planning/phases/28-feedback-ingestion-mvp/28-CONTEXT.md` + `28-01-SUMMARY.md` + `28-02-SUMMARY.md` — Phase 28 contract and shipped deliverables.
- `.planning/REQUIREMENTS.md:22-27` — STORE-01..04 requirement text.
- `.planning/ROADMAP.md:57-68` — Phase 29 success criteria (SC-1..4).
- `/data/workspace/hermes-agent/CLAUDE.md` — Hermes conventions (encoding, get_hermes_home, naming, error handling).
- `pyproject.toml:157,348-356` — pytest config + version pins.

### Secondary (MEDIUM confidence)

- `hermes_cli/config.py:1975-2024` — `curator:` config section style (template for `feedback:` section). Verified via Read.
- `cli-config.yaml.example:496-514` — `memory:` section style (template for top-level section formatting). Verified via grep.
- `tests/agent/test_feedback_ingest.py:1-80` — `feedback_env` fixture pattern (monkeypatch HERMES_HOME + importlib.reload). Verified via Read.
- `tests/agent/test_curator_reports.py:1-50` — `curator_env` fixture pattern (origin of the `feedback_env` pattern). Verified via Read.

### Tertiary (LOW confidence)

- None — all claims are sourced from in-repo code or CONTEXT.md.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new packages; all dependencies verified in `pyproject.toml` and existing code.
- Architecture: HIGH — Pattern 1-4 derive directly from CONTEXT.md locked decisions + existing `curator.save_state` / `atomic_json_write` patterns.
- Pitfalls: HIGH — all 7 pitfalls derive from concrete code observations (encoding default, atomic rewrite cost, dedup race) or CONTEXT.md explicit notes.
- Migration: HIGH — Phase 28 `incoming/` layout confirmed via Read of `agent/feedback_ingest.py:82`; migration algorithm derived from the existing `_scan_once` rename-with-fallback pattern.

**Research date:** 2026-06-24
**Valid until:** 2026-07-24 (30 days — stable internal-codebase research, no external API surface to drift)

## RESEARCH COMPLETE
