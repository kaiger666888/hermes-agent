# Asset Bus Schema — Slot Types + Lifecycle

**Source:** `plugins/pipeline_state/asset_bus.py` (`ASSET_SCHEMA` constant, Phase 33); Phase 35 slot additions per CONTEXT D-35-05.
**Copyright:** Fair Use — slot schema is factual integration architecture.
**Last-verified:** 2026-06-25

---

## Summary

This document is the **AssetBus V3 slot schema reference** for the `kais-movie-pipeline` orchestration skill. It answers "what slots exist, what format, what reads/writes each" for port engineers wiring phase modules to the asset bus.

This is **skeleton form** (per ROADMAP SC#5). Phase 36 refines with actual port experience (per-slot JSON schemas for p04-p13 outputs, observed envelope derivation chains, CreativeHistoryTracker DAG edges).

---

## Slot Format Types

AssetBus V3 supports two slot formats. Reference: `ASSET_SCHEMA` in `plugins/pipeline_state/asset_bus.py`.

| Format | Write Semantics | Read Semantics | Envelope | Used By |
|--------|-----------------|----------------|----------|---------|
| **`json`** | Atomic write (tmp + `os.replace`) — value replaced on each write | Auto-unwrap envelope, return raw payload | Wrapped in `{value, derived_from, content_hash, schema_version}` envelope by default | Most slots — atomic state per phase output |
| **`jsonl`** | Append-only — `open(..., "a")` (O_APPEND, no fsync, mirrors Node.js) | Read all non-blank lines as parsed dicts | No envelope (each line is a standalone record) | Append-only logs (currently only `finetune-dataset`) |

**API surface:**
- JSON slots: `bus.write(slot, data, envelope=True, derived_from=[...])` / `bus.read(slot)` / `bus.require(slot)` (raises if missing)
- JSONL slots: `bus.append_line(slot, line_obj)` / `bus.read_lines(slot)` → list of dicts
- Introspection: `bus.list_asset_names()` → all registered slot names

---

## Phase 33 Slots (PRESERVED)

The original 4 slots shipped in Phase 33. Phase 35 does **NOT** modify these — they are preserved as-is per CONTEXT D-35-05 (Phase 35 only adds new phase-output slots).

| Slot | Format | File | Purpose |
|------|--------|------|---------|
| `creative-history` | json | `creative-history.json` | CreativeHistoryTracker DAG state (`shots: [{shot_id, source_hash, derived_from, content_hash, timestamp}]`) — tracks asset provenance for blast-radius BFS |
| `failed-shots` | json | `failed-shots.json` | Failed-shot ledger (`failures: [{shot_id, error, timestamp, run_id, prompt, fingerprints}]`) |
| `finetune-dataset` | jsonl | `finetune-dataset.jsonl` | Append-only training dataset (one record per finetune sample) |
| `review-outcomes` | json | `review-outcomes.json` | Gate decision ledger (Phase 34 tightens schema: approve / reject / contest + suggested_action + rollback target) |

---

## Phase 35 Slots (added per D-35-05)

Phase 35-02 extends `ASSET_SCHEMA` with 6 phase-output slots for the p01-p03 vertical slice. All are JSON format, envelope-wrapped, atomic write.

| Slot | Format | Phase | Written by | Read by |
|------|--------|-------|------------|---------|
| `requirement` | json | p01 input | operator (or upstream) | `p01_hook_topic` |
| `topic-kernel` | json | p01 output | `p01_hook_topic` | `p02_outline` |
| `hook-design` | json | p01 output | `p01_hook_topic` | (Gate 1 review; canvas sync Phase 37) |
| `story-framework` | json | p02 output | `p02_outline` | `p03_script_audit` |
| `script-draft` | json | p03 output | `p03_script_audit` | (p04-p06 downstream, Phase 36) |
| `audit-report` | json | p03 output | `p03_script_audit` | (Gate 3 review; future training data) |

**Naming note:** `topic-kernel` not `p01-topic-kernel` — kebab-case semantic names (matches existing Phase 33 slot convention and Node.js V8.6 asset-bus where applicable for port traceability).

---

## Phase 36 Future Slots

Phase 36 will add ~20 more slots as p04-p13 phase modules are ported. **Exact names + schemas are TBD** (defined when each phase module is implemented; Phase 36 SC#4 refines this doc with actual port experience). Expected slot names (placeholder):

- `character-bible` (p04 — character_designer output, L1-L4 asset library)
- `scene-design` (p05 — cinematographer + style_genome scene design)
- `spatio-script` (p06 — screenplay + cinematographer spatio-temporal script)
- `shot-list` (p06 / p08 — cinematographer shot decomposition)
- `visual-seeds` (p07 — visual_executor + prompt_injector seed images)
- `styled-frames` (p07 — colorist styled keyframes)
- `audio-skeleton` (p07b — audio_pipeline voicer + composer + foley skeleton)
- `video-clips` (p10 — dreamina CLI generated raw clips, possibly JSONL for parallel shots)
- `voice-timeline` (p11 — audio_pipeline lip_sync alignment)
- `audio-stems` (p11 — BGM + SFX + lip-sync stems)
- `master-mp4` (p12-p13 — final composed master)
- `continuity-report` (p09 — continuity_auditor 4-dim report)
- `gate-N-outcome` variants (if per-gate slotting chosen — TBD)

---

## Envelope Schema

Every JSON slot write wraps the payload in a v3.0 envelope via `bus.write(slot, value, envelope=True)` (default). Read auto-unwraps — callers receive the raw payload. Reference: `wrap_envelope` / `unwrap_envelope` in `plugins/pipeline_state/asset_bus.py`.

```python
{
  "value": <payload>,
  "derived_from": [<upstream content_hash>, ...],  # default []
  "content_hash": "<sha256 hex of canonical JSON of value>",
  "schema_version": "3.0"
}
```

**Key behaviors:**
- `derived_from` non-empty **forces** envelope even when `envelope=False` (so CreativeHistoryTracker DAG edges are always recorded)
- `content_hash` uses `sort_keys=True` for cross-run determinism (differs from Node.js insertion-order `JSON.stringify`, removes dict-ordering bugs — see Phase 33 PATTERNS.md)
- Backward compat: a v2.0 raw dict without `schema_version == "3.0"` + `value` key passes through `unwrap_envelope` untouched
- Arrays are never envelopes

---

## Slot Naming Convention

- **kebab-case** (matches Phase 33 slots: `creative-history`, `failed-shots`, `review-outcomes`)
- **Semantic names** matching V8.6 Node.js asset-bus where applicable — for port traceability (port engineer can grep Node.js `lib/asset-bus.js` for the same slot name)
- **No phase prefix** — `topic-kernel` not `p01-topic-kernel` (phase identity flows from the write contract, not the name)
- **JSON vs JSONL by intent** — atomic-state outputs are JSON; append-only logs are JSONL

---

## See Also

- [`pipeline-dag.md`](./pipeline-dag.md) — 13-step DAG (slot flow per edge)
- [`review-gates.md`](./review-gates.md) — `review-outcomes` slot is the gate decision sink
- [`expert-mapping.md`](./expert-mapping.md) — which expert writes which slot
- `plugins/pipeline_state/asset_bus.py` — Phase 33 canonical implementation (V3 envelope + atomic write)
- `plugins/pipeline_state/creative_history.py` — Phase 33 DAG + reverse BFS over `creative-history` slot
