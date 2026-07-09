---
phase: 74-transition
plan: 01
subsystem: pipeline_state
tags: [transition, schema, pydantic, literal-enum, backward-compat, asset-bus, canvas-sync, trans-01, trans-02, trans-03]
requires:
  - "Phase 73 IMG complete (kais-hermes-skills HEAD 7904bd0)"
  - "FORM-01 form_factor strict-enum precedent (store.py:79)"
  - "DUB-02 TTS_ENGINE_VALUES frozenset precedent (store.py:150)"
  - "Phase 36-02 asset-bus slot-addition pattern (asset_bus.py:223-236)"
provides:
  - "transition_schema.py module (TRANSITION_METHOD_VALUES 12-enum + CAMERA_CONTINUITY_VALUES 6-enum + load_next_shot_link backward-compat reader)"
  - "transition-design ASSET_SCHEMA slot (writer=p09, reader=p13, TRANS-04 ownership encoded)"
  - "transition_design canvas_sync _PHASE_OUTPUT_MAP p09 tuple (storyboard canvas_type, zero frontend change)"
  - "12 unit tests covering TRANS-01/02/03 (5 behavior + 2 enum-count + 4 slot-registered + 1 backward-compat)"
affects:
  - "Plan 74-02 SKILL.md ownership split (cinematographer Step 9 / editor Step 7) — depends on this plan's schema module + asset slot"
  - "Plan 74-03 LTX-FLF validation + smoke runner — depends on this plan's transition_schema.py import"
tech-stack:
  added: []
  patterns:
    - "Pydantic Literal strict-enum + frozenset runtime lookup (3-phase precedent: FORM-01 → DUB-02 → TRANS-01)"
    - "Backward-compat reader load_next_shot_link(value) — string → structured default coercion (DUB-02 .get(key, default) pattern extended)"
    - "3-system canvas registration (asset_bus ASSET_SCHEMA + canvas_sync _PHASE_OUTPUT_MAP + frontend zod reuse) — PITFALL T-4 mitigation"
    - "TDD red-green (RED: tests fail with ModuleNotFoundError / slot-not-registered; GREEN: implement + verify all pass)"
key-files:
  created:
    - "kais-hermes-skills/plugins/pipeline_state/transition_schema.py (180 lines)"
    - "kais-hermes-skills/plugins/pipeline_state/tests/test_transition_schema.py (205 lines, 12 tests)"
  modified:
    - "kais-hermes-skills/plugins/pipeline_state/asset_bus.py (+15 lines: transition-design slot after e-konte-sheets)"
    - "kais-hermes-skills/plugins/kais_aigc/canvas_sync.py (+16 lines: 1 p09 tuple + 14-line D-06 comment block)"
decisions:
  - "TRANS-01 12-enum + 6-enum: Pydantic Literal for type-checker hints + frozenset for runtime O(1) membership (mirrors FORM-01/DUB-02)"
  - "TRANS-02 backward-compat: load_next_shot_link() standalone helper, NOT @model_validator (Shot is plain dict per RESEARCH Critical Correction #3)"
  - "TRANS-03 system 3: reuse storyboard canvas_type (zero frontend change); distinct transition React Flow nodeType deferred to v15+"
  - "TRANS-04 ownership encoded in slot registry: writer_phase=p09_shot_breakdown, reader_phases=[p13_delivery]"
metrics:
  duration: "~5min (305s)"
  completed: "2026-07-09"
  tasks: 3
  files: 4
  tests: 12
  commits: 3 (kais-hermes-skills)
---

# Phase 74 Plan 01: TRANSITION Foundation Summary

TRANS-01/02/03 data-layer foundation: Pydantic Literal 12-enum transition_method + 6-enum camera_continuity with frozenset runtime enforcement, backward-compat `load_next_shot_link()` reader coercing legacy bare-string to structured default, and 3-system `transition-design` asset registration (asset-bus slot + canvas_sync `_PHASE_OUTPUT_MAP` tuple + frontend zod storyboard reuse).

## What Was Built

### Task 1 — `transition_schema.py` + 7 unit tests (TRANS-01/02) [commit df78a6f]

**`kais-hermes-skills/plugins/pipeline_state/transition_schema.py`** (180 lines, NEW):
- `TRANSITION_METHOD_VALUES` — Pydantic `Literal[...]` 12-value enum: `hard_cut / dissolve / wipe / fade / match_cut_shared_object / match_cut_shared_landscape / motion_vector_match / color_match / j_cut / l_cut / whip_pan / none`
- `CAMERA_CONTINUITY_VALUES` — Pydantic `Literal[...]` 6-value enum: `pan_to / zoom_to / dolly_through / whip_pan / match_cut_on_motion / none`
- `_TRANSITION_METHOD_SET` / `_CAMERA_CONTINUITY_SET` — module-level `frozenset` runtime lookup sets (the runtime authority; Literal is type-checker hint only)
- `load_next_shot_link(value: Any) -> dict` — backward-compat reader:
  - `isinstance(value, str)` → coerce to `{shot_id: value, transition_method: "hard_cut", visual_hook: None, camera_continuity: "none", generation_path: None}`
  - `isinstance(value, dict)` → validate `transition_method` against `_TRANSITION_METHOD_SET`, `camera_continuity` against `_CAMERA_CONTINUITY_SET`; defaults for unfilled fields
  - Neither → raise `TypeError` with `(TRANS-02 strict type — no fuzzy coercion)` audit suffix
  - Invalid enum → raise `ValueError` with `(TRANS-01 strict enum — no fuzzy matching, no warnings-and-continue)` audit suffix

Module layout mirrors `dub_validators.py` (Phase 72 sibling): module docstring (purpose → fail-fast contract → design decisions) → `from __future__ import annotations` → `from typing import Any, Literal` → enum type aliases → frozenset runtime sets → standalone validator function. Sibling module to `store.py`, NOT `@model_validator` (Shot is a plain dict per RESEARCH Critical Correction #3).

**`kais-hermes-skills/plugins/pipeline_state/tests/test_transition_schema.py`** (123 lines at Task 1 close, 205 lines at Task 2 close, NEW):
- 5 TRANS-02 behavior tests: `test_load_string_next_shot_link`, `test_load_structured_next_shot_link`, `test_load_next_shot_link_rejects_invalid_transition_method`, `test_load_next_shot_link_rejects_invalid_camera_continuity`, `test_load_next_shot_link_rejects_non_str_non_dict`
- 2 TRANS-01 enum-count sanity tests: `test_transition_method_enum_has_12_values`, `test_camera_continuity_enum_has_6_values`

TDD flow: RED verified (ModuleNotFoundError on missing module), then GREEN (all 7 pass).

### Task 2 — ASSET_SCHEMA slot + canvas_sync tuple + 5 tests (TRANS-03) [commit 2e446be]

**`kais-hermes-skills/plugins/pipeline_state/asset_bus.py`** (+15 lines, MODIFY):
- Appended `"transition-design"` slot AFTER `"e-konte-sheets"` (keeps p09 outputs grouped per 74-PATTERNS.md line 199)
- Slot dict: `file="transition-design.json"`, `format="json"`, `description="Transition design (creative intent from cinematographer Step 9; consumed by editor Step 13 for post-production execution). Per-shot transition_method (12-enum) + visual_hook + camera_continuity."`, `writer_phase="p09_shot_breakdown"`, `reader_phases=["p13_delivery"]`
- TRANS-04 ownership split encoded in registry (writer=p09 cinematographer, reader=p13 editor)
- Kebab-case name matching `"shot-list"` + `"e-konte-sheets"` convention
- Existing 43 slots remain byte-equivalent (append-only per D-36-05; verified: grep `"shot-list"` == 1, `"e-konte-sheets"` == 1)

**`kais-hermes-skills/plugins/kais_aigc/canvas_sync.py`** (+2 lines for Phase 74, MODIFY):
- Appended `("transition_design", "转场设计", "storyboard", False)` tuple to `_PHASE_OUTPUT_MAP["p09"]` AFTER the existing `e_konte_sheets` tuple
- `canvas_type="storyboard"` per RESEARCH A1 (zero frontend change — frontend zod already accepts storyboard nodes)
- `expand_subkeys=False` (per-shot list, matches shot_list pattern)
- Inline comment `# Phase 74 TRANS-03 — transition design (cinematographer creative intent → editor post-production)` above tuple

**5 new TRANS-03 tests** appended to `test_transition_schema.py`:
- `test_asset_bus_slot_registered` — `"transition-design" in ASSET_SCHEMA` (VALIDATION 74-01-05)
- `test_transition_design_slot_format_json` — `format == "json"`
- `test_transition_design_slot_writer_phase_p09` — `writer_phase == "p09_shot_breakdown"` (TRANS-04)
- `test_transition_design_slot_reader_phase_p13` — `"p13_delivery" in reader_phases` (TRANS-04)
- `test_backward_compat_string_next_shot_link` — legacy `layer_5` dict with bare-string `next_shot_link="shot_02"` loads cleanly via `load_next_shot_link` coercion (VALIDATION 74-03-02)

TDD flow: RED verified (AssertionError "transition-design slot not registered"), then GREEN (all 5 pass; full 12 pass).

### Task 3 — D-06 storyboard canvas_type reuse documentation [commit d079103]

**`kais-hermes-skills/plugins/kais_aigc/canvas_sync.py`** (+14 lines, MODIFY):
- 14-line documentation comment block above `_PHASE_OUTPUT_MAP` definition explaining D-06 storyboard canvas_type reuse decision:
  1. Frontend zod (`canvasAssetSchema.ts`) has 5 React Flow nodeTypes: audio / video / asset / storyboard / script — NO distinct "transition" type
  2. `transition_design` reuses storyboard canvas_type because it shares p09's pre-production design semantic (no media artifact, structured design data)
  3. Zero frontend change required in v14.0
  4. Distinct "transition" React Flow nodeType can be added in v15+ if operator requests visual separation
- Verified: `grep -c "storyboard" /data/workspace/kais-aigc-platform/src/lib/canvasAssetSchema.ts` returns 6 (VALIDATION 74-01-07 satisfied)
- No kais-aigc-platform repo edits (read-only verification per RESEARCH)

## Test Results

**All 12 TRANS tests green** (`python3 -m pytest plugins/pipeline_state/tests/test_transition_schema.py -xvs`):

| Test | VALIDATION | Status |
|------|-----------|--------|
| `test_load_string_next_shot_link` | 74-01-03 | PASSED |
| `test_load_structured_next_shot_link` | 74-01-04 | PASSED |
| `test_load_next_shot_link_rejects_invalid_transition_method` | 74-01-01 (reject path) | PASSED |
| `test_load_next_shot_link_rejects_invalid_camera_continuity` | 74-01-01 (reject path) | PASSED |
| `test_load_next_shot_link_rejects_non_str_non_dict` | TRANS-02 strict type | PASSED |
| `test_transition_method_enum_has_12_values` | 74-01-01 (count) | PASSED |
| `test_camera_continuity_enum_has_6_values` | 74-01-02 | PASSED |
| `test_asset_bus_slot_registered` | 74-01-05 | PASSED |
| `test_transition_design_slot_format_json` | 74-01-05 (format) | PASSED |
| `test_transition_design_slot_writer_phase_p09` | 74-01-05 (writer) | PASSED |
| `test_transition_design_slot_reader_phase_p13` | 74-01-05 (reader) | PASSED |
| `test_backward_compat_string_next_shot_link` | 74-03-02 | PASSED |

**Regression:** 346 existing pipeline_state tests still green (excluding 1 pre-existing `test_v50_regression_phase41` failure documented as out-of-scope in Phase 71-03 decisions — root cause: tests resolve paths assuming cwd is skill dir, not kais-hermes-skills root; NOT caused by Phase 74 changes).

## Plan-Level Verification (5 commands)

| # | Command | Expected | Actual |
|---|---------|----------|--------|
| 1 | `python -m pytest plugins/pipeline_state/tests/test_transition_schema.py -xvs` | 12 passed | 12 passed in 0.03s |
| 2 | `grep -c "transition-design" plugins/pipeline_state/asset_bus.py` | >= 1 | 2 (slot dict + comment) |
| 3 | `grep -A 6 '"p09"' plugins/kais_aigc/canvas_sync.py \| grep -c "transition_design"` | >= 1 | 1 |
| 4 | `grep -c "storyboard" /data/workspace/kais-aigc-platform/src/lib/canvasAssetSchema.ts` | >= 1 | 6 |
| 5 | `python -c "...from transition_schema import load_next_shot_link; r = load_next_shot_link('shot_02'); assert r['transition_method'] == 'hard_cut'"` | succeeds | OK |

## Deviations from Plan

### Auto-fixed Issues

**[Rule 3 - Blocking] canvas_sync.py pre-existing modifications swept into Task 2 commit**

- **Found during:** Task 2 staging (`git add plugins/kais_aigc/canvas_sync.py`)
- **Issue:** The canvas_sync.py working tree had substantial pre-existing uncommitted modifications (a generated field-map loader extraction refactor + removal of inline `_CAMERA_MOVEMENT_MAP` / `_FRAMING_MAP` / `_COMPOSITION_MAP` / `_PACING_MAP` constants — appears to be an in-progress operator refactor extracting these to a generated `canvas_sync_mappings.py` module). These were in the working tree before my session started. `git add` swept them into my Task 2 commit alongside my 2-line Phase 74 addition.
- **Fix applied:** Did NOT revert (would destroy prior operator work — forbidden per deviation rules). The Phase 74-specific change (the p09 `transition_design` tuple + inline comment) is correct and isolated. The pre-existing changes are a legitimate degrade-tolerant refactor (imports `canvas_sync_mappings.py` via importlib with fallback to no-op on missing file). Commit `2e446be` documents this in the body.
- **Files modified:** `plugins/kais_aigc/canvas_sync.py` (pre-existing refactor + my 2-line Phase 74 addition)
- **Commit:** `2e446be` (Task 2)
- **Recommendation:** Operator should verify the generated field-map refactor is intentional before Phase 74 close. If it should be a separate commit, `git reset 2e446be~ -- plugins/kais_aigc/canvas_sync.py` + re-stage only the p09 hunk. However, this is operator decision — Phase 74 work is complete either way.

### Plan executed as written otherwise

All 3 tasks executed exactly as planned. TDD red-green flow followed for Tasks 1+2. No Rule 1/2/4 deviations encountered.

## Commits

| Task | Commit | Type | Message |
|------|--------|------|---------|
| 1 | `df78a6f` | feat | `feat(74-01): TRANS-01/02 transition_schema.py + 7 unit tests` |
| 2 | `2e446be` | feat | `feat(74-01): TRANS-03 3-system transition-design registration` |
| 3 | `d079103` | docs | `docs(74-01): D-06 storyboard canvas_type reuse decision comment` |

**Cross-repo topology:** All 3 commits in `kais-hermes-skills` repo (master branch, HEAD now `d079103`). SUMMARY.md + STATE.md + ROADMAP.md commits follow in hermes-agent repo.

## Operator-Action Handoffs

**None for Plan 74-01.** This plan is pure data-layer foundation (schema + asset registration). Operator-action handoffs (Wan2.2 FLF2V install, Hailuo/Vidu API keys, LTX-FLF+ICLoRA validation shots) are Plan 74-02/74-03 scope per VALIDATION.md Manual-Only Verifications table.

## Known Stubs

None. All code in this plan is production-grade (no placeholder data, no TODO markers, no unimplemented paths).

## Threat Flags

None. All files created/modified stay within the documented trust boundary (episode JSON → pipeline_state). The T-74-01 (Tampering) and T-74-02 (Tampering) threats in the plan's `<threat_model>` are mitigated as specified:
- T-74-01: `load_next_shot_link()` enforces TRANS-01 strict enum via frozenset membership + ValueError with audit suffix
- T-74-02: ASSET_SCHEMA slot is source-code-level dict; no untrusted input reaches it at runtime

No new security-relevant surface introduced beyond what the threat model anticipated.

## Self-Check: PASSED

All 5 created/modified files exist on disk. All 3 kais-hermes-skills commits (`df78a6f`, `2e446be`, `d079103`) found in git log. All 12 TRANS tests green. All 5 plan-level verification commands pass.
