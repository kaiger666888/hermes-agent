# Phase 29: Feedback Store - Context

**Gathered:** 2026-06-24
**Status:** Ready for planning

<domain>
## Phase Boundary

All ingested feedback (from Phase 28's three sources: CLI / kais-aigc / manual) persists durably under `~/.hermes/skills/.feedback/` in a structured `skill_id/source/` layout, is queryable via a single `index.json` consumed by both Curator (P32) and dashboard (P33), decays in weight over time (180-day linear ramp to 10% floor), and is deduplicated so the same `output_snapshot.sha256` cannot skew the learning signal.

Covers requirements STORE-01..04. Builds the persistence + query + decay + dedup layer on top of Phase 28's ingest contract. Hermes-core touch: Yes — new persistence layer under `~/.hermes/skills/.feedback/`. Pure data plumbing, no bundled-SKILL.md changes.

**Depends on Phase 28:** Reuses `FeedbackRecord` schema, `OutputSnapshot`, `build_output_snapshot`, and the existing `write_feedback_record` atomic write path. Phase 29 *extends* the write path to update the index incrementally + restructure storage from flat `incoming/` to `skill_id/source/` buckets.

</domain>

<decisions>
## Implementation Decisions

### Index Update Strategy (STORE-02)
- **Incremental update on every write** — `write_feedback_record` updates `index.json` atomically alongside the jsonl append (both via `utils.atomic_json_write`). Zero stale reads, no rebuild cron needed.
- Index stays small: one entry per `(skill_id, source, verdict)` bucket with `count`, `weighted_count`, `first_ts`, `last_ts`, plus a per-sha256 dedup registry.
- Periodic rebuild and lazy on-demand rejected — stale reads and slow first-read are unacceptable for the Curator's review queue.

### Time-Decay Function (STORE-03)
- **Linear decay** — `weight = max(0.1, 1.0 - (age_days / 180))` so:
  - 0 days old: weight = 1.0 (full signal)
  - 90 days old: weight = 0.5 (half signal — default operator-visible threshold)
  - 180 days old: weight = 0.0 mathematically but floored at 0.1 (10% residual)
  - >180 days: weight = 0.1 (never fully zero — old signal still counts weakly)
- Default `decay_window_days = 180`, configurable in `config.yaml` under `feedback.decay_window_days`.
- Operators can tune by editing config + restarting Hermes; no live retune needed for v6.

### Correction Weight Demotion (STORE-04)
- **Zero out older record, count only newer** — when same `output_snapshot.sha256` arrives with a different `verdict`:
  - Older record: `weight = 0.0`, `status = "superseded"`, `superseded_by = <newer_record_id>`
  - Newer record: normal weight based on its own age, `status = "active"`, `supersedes = <older_record_id>`
- Index reflects only the latest verdict per sha256 in `weighted_count`; raw `count` still includes superseded records for audit.
- Halve-older and keep-both rejected — both muddy the signal. Operator's most recent judgment is authoritative.

### Query API Surface (STORE-02)
- **`FeedbackStore` class** at `agent/feedback_store.py` with:
  - `query(skill_id=None, source=None, verdict=None, since=None, until=None, include_superseded=False) -> List[FeedbackRecord]`
  - `summary(skill_id=None, source=None) -> Dict[BucketKey, BucketSummary]` — returns `{count, weighted_count, first_ts, last_ts}` per bucket
  - `get_record(record_id) -> FeedbackRecord` — direct lookup
  - `record_feedback(record: FeedbackRecord) -> str` — persists + updates index + dedup check, returns record_id
- SQLite rejected (overkill for jsonl-scale ~thousands of records). HTTP endpoint rejected (P33 dashboard reads index.json directly — no server needed in P29).

### Storage Layout

```
~/.hermes/skills/.feedback/
├── index.json                          # Queryable index — single source of truth
├── buckets/
│   ├── screenplay/
│   │   ├── cli.jsonl                   # Append-only feedback records
│   │   ├── kais_aigc.jsonl
│   │   └── manual.jsonl
│   ├── drawer/
│   │   ├── cli.jsonl
│   │   └── ...
│   └── ... (one subdir per skill_id)
├── dedup/
│   └── sha256-registry.jsonl           # Append-only: {sha256, verdict, record_id, ts}
└── archive/                            # Optional operator-managed prune target
```

- `incoming/` (Phase 28's flat layout) becomes a transient staging dir — Phase 29 migrates files to `buckets/` on first access (lazy migration, no big-bang rewrite).
- `inbox-kais/` and `processed-kais/` (Phase 28 kais-aigc watcher) unchanged — watcher still drops files there; Phase 29 picks them up and routes to `buckets/<skill_id>/kais_aigc.jsonl`.

### Claude's Discretion
- `record_id` format — Claude's call (recommend `f"{ts_unix}_{sha256[:8]}"` for sortability + collision-resistance).
- Migration timing — Phase 28's `incoming/` can be migrated lazily (on first P29 access) or eagerly (on Phase 29 init). Lazy is safer for zero-downtime cutover.
- Thread safety — single-process access for MVP (no concurrent writers); add file-lock if needed in P32 when Curator reads concurrent with operator writes.
- Index file format — JSON (human-readable, matches existing `agent/curator.py:save_state` pattern). Not MessagePack or CBOR (no new deps).

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `agent/feedback_schema.py:1-200` (Phase 28) — `FeedbackRecord`, `OutputSnapshot` Pydantic models. Phase 29 reads/writes these directly.
- `agent/feedback_ingest.py:1-300` (Phase 28) — `write_feedback_record` atomic write path. Phase 29 extends this with index update + dedup check.
- `utils.py:111-153` — `atomic_json_write` (temp + fsync + os.replace). Use for both `buckets/*.jsonl` append (via atomic rewrite of the full file) and `index.json` update.
- `agent/curator.py:71-117` — `_state_file()`, `load_state`, `save_state` persistence pattern. Exact template for `FeedbackStore` load/save.
- `hermes_constants.py:53` — `get_hermes_home()` — root for `~/.hermes/skills/.feedback/`.
- `cli-config.yaml.example` — config file structure. Phase 29 adds `feedback.decay_window_days: 180` under existing `skills:` or new `feedback:` section (Claude's discretion — match existing style).

### Established Patterns
- Pydantic v2 (`field_validator`, `model_config`) — `FeedbackRecord` already uses this.
- `encoding="utf-8"` on every `open()` (Ruff PLW1514).
- `from __future__ import annotations` at top of new modules.
- `get_hermes_home()` not `Path.home() / ".hermes"`.
- Atomic write via `utils.atomic_json_write` for crash-safe persistence.
- Lazy %-formatting in logger calls.

### Integration Points
- **Phase 28 ingest path:** `agent/feedback_ingest.py:write_feedback_record` becomes a thin wrapper that calls `FeedbackStore.record_feedback(record)`. Existing callers (CLI / kais watcher / JSONL import) work unchanged.
- **Phase 32 Curator (consumer):** Will call `FeedbackStore.summary(skill_id=...)` and `FeedbackStore.query(verdict="bad")` to scan for patterns.
- **Phase 33 Dashboard (consumer):** Will read `index.json` directly for cross-skill view (no Python import needed — JSON-on-disk contract).
- **Lazy migration:** On first P29 access, scan `incoming/*.json` and route each to `buckets/<skill_id>/<source>.jsonl` based on the record's fields. Move originals to `archive/phase-28-migration/` for audit.

</code_context>

<specifics>
## Specific Ideas

- `index.json` MUST be the single source of truth for counts and weighted_counts — P32 Curator and P33 dashboard MUST NOT do parallel ad-hoc scans of `buckets/`. This is explicit in SC-2 and prevents divergence.
- The `dedup/sha256-registry.jsonl` is append-only — never rewritten. Each line: `{"sha256": "...", "verdict": "...", "record_id": "...", "ts": "..."}`. Lookup is O(N) but N stays small (one line per feedback record). For larger scale, P32+ can add an in-memory cache.
- Time-decay is computed on QUERY, not on write — stored records keep raw `ts`; the `weighted_count` in `index.json` is recomputed when index is updated. This makes decay-tuning cheap (just edit config + trigger an index rebuild via `hermes feedback rebuild-index` CLI command).
- Config key path: `feedback.decay_window_days` (top-level `feedback:` section). Default 180. Documented in `cli-config.yaml.example`.

</specifics>

<deferred>
## Deferred Ideas

- **Concurrent writer support** (file locking) — Phase 29 assumes single-process. Phase 32 Curator may run concurrently with operator CLI; add `fcntl.flock` or `filelock` lib then.
- **Auto-prune of old feedback** — Phase 29 keeps everything (time-decay reduces weight but doesn't delete). Operator manually prunes via `rm` or future `hermes feedback prune --older-than 365d` command (FUTURE-V6).
- **PII auto-redaction** — FUTURE-V6-06 per STATE.md risks. v6 assumes trusted operator.
- **Cross-operator aggregation** — v6 is single-operator. Multi-operator merge is FUTURE-V6.
- **Index compression** — For >100K records, `index.json` could grow large. Defer compression (gzip + content-type) to FUTURE-V6 if observed in practice.
- **Snapshot content storage** — Phase 29 stores `output_snapshot` inline in each feedback record. If snapshots grow large (full prompt + params), future work may externalize to `snapshots/<sha256>.json` with inline reference. Defer unless measured.

</deferred>
