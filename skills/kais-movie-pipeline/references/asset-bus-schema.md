# Asset Bus Schema — Slot Types + Lifecycle

**Source:** `plugins/pipeline_state/asset_bus.py` (`ASSET_SCHEMA` constant, Phase 33); Phase 35 slot additions per CONTEXT D-35-05; Phase 36 Wave 1 additions per CONTEXT D-36-04.
**Copyright:** Fair Use — slot schema is factual integration architecture.
**Last-verified:** 2026-06-26 (Phase 36-05 Wave 2 refinement — full slot table replacing placeholder)

---

## Summary

This document is the **AssetBus V3 slot schema reference** for the `kais-movie-pipeline` orchestration skill. It answers "what slots exist, what format, what reads/writes each" for port engineers wiring phase modules to the asset bus.

**Phase 36-05 Wave 2 refinement:** The "Phase 36 Future Slots TBD" placeholder has been replaced with the actual slot table written by Wave 1 (36-01..36-04). All slot names + writer/reader phases below are sourced from the `ASSET_SCHEMA` dict in `plugins/pipeline_state/asset_bus.py`.

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

## Phase 36 Slots (Complete — 36-01..36-04 Wave 1)

> Refined in Phase 36-05 from actual Wave 1 ASSET_SCHEMA additions. All 17 slots below are JSON format, envelope-wrapped, atomic write (per Phase 33 / Phase 35 convention). Slot names are kebab-case semantic (no phase prefix).

| Slot | Format | Writer Phase | Reader Phase(s) | Purpose / V8.6 Equivalent |
|------|--------|--------------|------------------|----------------------------|
| `character-bible` | json | p04 `p04_character_design` | p05, p06, p09 | Character Bible 2.0 (4D-Anchor identity + style_prefix per character) — V8.6 Step 4 character_designer output |
| `character-assets` | json | p04 `p04_character_design` | p07, p11 | L1-L4 asset manifest (identity anchors + expression sheets + costume cards + prop cards) — V8.6 Step 4 visual_executor (drawer) output |
| `pain-points` | json | p05 `p05_pain_discovery` | (Gate 4 review) | L1-L6 pain strata mined from 6 social strata — V8.6 Step 5 creative_source output |
| `escalation-ladder` | json | p05 `p05_pain_discovery` | (Gate 4 review) | Escalation ladder (theory_critic stress-tested) — V8.6 Step 5 theory_critic output |
| `spatio-temporal-script` | json | p06 `p06_spatio_temporal_script` | p07, p08, p09 | Spatio-temporal script (screenplay + cinematographer axis lock) — V8.6 §5 atomic |
| `final-audit` | json | p06 `p06_spatio_temporal_script` | (Gate 6 review) | 5-dim final audit (script_auditor) — V8.6 §5 atomic |
| `scene-images` | json | p07 `p07_scene_generation` | p08, p11 | 5-view per-scene keyframes (visual_executor + prompt_injector) — V8.6 §4 atomic |
| `style-vector` | json | p07 `p07_scene_generation` | p08, p12 | 5D style genome (genre/mood/aesthetic/pace/color) — V8.6 §4 atomic |
| `color-intent` | json | p07 `p07_scene_generation` | p13 | CxSxZ 28-combination color intent + LUT plan — V8.6 §4 atomic |
| `scene-selection` | json | p08 `p08_scene_selection` | p09 | Operator-approved scene subset — V8.6 Step 8 |
| `geometry-bed` | json | p08 `p08_scene_selection` | p09, p11 | Cross-shot 3D anchor frame (composition_lock) — V8.6 Step 8 |
| `shot-list` | json | p09 `p09_shot_breakdown` | p10, p11 | Per-shot intent + duration decomposition — V8.6 Step 9 |
| `e-konte-sheets` | json | p09 `p09_shot_breakdown` | (analytics) | 5-layer E-Konte (composition/camera/lighting/action/dialogue) — V8.6 Step 9 |
| `voice-clips` | json | p10 `p10_voice` | p12 | Per-shot narration/dialogue audio paths — V8.6 Step 7B voicer sub-step |
| `voice-timeline` | json | p10 `p10_voice` | p11, p12 | Per-shot voice start_ms/end_ms alignment — V8.6 Step 7B |
| `video-clips` | json | p11 `p11_video_render` | p12 | Per-shot raw video clips (aggregated single write, NOT per-shot appends) — V8.6 Step 10 |
| `lip-sync-reports` | json | p11 `p11_video_render` | p12 | Per-shot lip-sync alignment reports (audio_pipeline lip_sync sub-step) — V8.6 Step 10 |
| `master-timeline` | json | p12 `p12_composition` | p13 | FxRxT timeline (editor) + audio master (audio_pipeline §6 6 sub-steps) — V8.6 §6 atomic |
| `audio-stems` | json | p12 `p12_composition` | p13 | BGM + SFX + lip-sync stems (audio_pipeline §6) — V8.6 §6 atomic |
| `master-mp4` | json | p13 `p13_delivery` | (operator — release artifact) | Final composed master.mp4 (preserves v4.0 PIPE-COMPOSE-01 contract) — V8.6 Step 12-13 |
| `delivery-package` | json | p13 `p13_delivery` | (operator — release artifact) | Distribution manifest (per-platform variants + AIGC labels) — V8.6 Step 12-13 |

**Total Phase 36 slots added: 21** (6 from 36-01, 7 from 36-02, 4 from 36-03, 4 from 36-04). Plus Phase 33's 4 + Phase 35's 6 = **31 slots total** in `ASSET_SCHEMA`.

**Naming clarifications (resolved during Wave 1):**
- `character-bible` (not `character-bible-2.0`) — kebab-case, semantic, no version suffix.
- `spatio-temporal-script` (not `spatio-script` or `spatio_script`) — full semantic name, hyphen-separated.
- `master-mp4` (not `master.mp4`) — slot name is the semantic identifier; the on-disk file is `master-mp4.json` (envelope-wrapped). The actual mp4 bytes live at the path stored inside the slot's `value.path` field.
- `video-clips` is JSON (single aggregated write), NOT JSONL — even though p11 fans out per-shot delegate calls, the slot write happens once after all shots complete (D-36-08 aggregation contract).

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
