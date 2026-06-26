---
phase: 40-gate-redlines
plan: 03
subsystem: review-gates-docs
tags: [docs, review-gates, redline, 11-gate, bilingual, additive, creative-redlines, auto-detect]
requires:
  - Phase 40-01 (3 redline detector modules — needed for accurate doc of detector signatures + suggested_action format)
  - skills/kais-movie-pipeline/references/creative-redlines.md (R1/R3/R4 source — cross-ref target)
  - skills/kais-movie-pipeline/references/review-gates.md (V8.6 8-gate table — additive edit target)
provides:
  - skills/kais-movie-pipeline/references/review-gates.md (11-gate per-phase mapping, additive)
  - plugins/review_gates/README.md (bilingual plugin readme mentioning 11 gates + auto-detect)
affects:
  - Phase 43 VALIDATE-01 (integration checker — review-gates.md is the canonical 11-gate doc)
  - Phase 43 VALIDATE-03 milestone audit (GATE-04 doc deliverable)
  - Operators reading plugins/review_gates/ source (README now explains auto-detect architecture)
tech-stack:
  added: []
  patterns:
    - additive-only doc patch (existing V8.6 8-gate table byte-preserved; 3 new rows appended in clearly-marked subsection)
    - bilingual plugin README (EN headings + 中文 body) mirroring v6.0/v7.0 plugin readme format
    - cross-reference discipline (each Phase 40 gate row links to its R-section in creative-redlines.md with relative path)
    - two-path documentation (V8.6 HIL manual resolution vs Phase 40 auto-detect — made explicit in Gate Implementation section + sequence diagram)
key-files:
  created: []
  modified:
    - skills/kais-movie-pipeline/references/review-gates.md
    - plugins/review_gates/README.md
decisions:
  - Additive-only patch honored — V8.6 8-gate table rows + "Hard vs Soft Gates" section byte-preserved; only header/metadata/summary/heading/see-also lines rewritten (9 deletions, all metadata-level). Verified via git diff.
  - New "## Phase 40 Redline Gates (9-11, additive)" section placed BEFORE "## Gate Implementation" so readers see the 3 new gates immediately after the V8.6 table, then learn how they're wired.
  - 11-gate sequence diagram added to make the V8.6-HIL → Phase-40-auto → final-delivery flow visually explicit (per ROADMAP Phase 40 SC#3 "gates 9/10/11 fire after existing 8 pass, before final delivery").
  - Each redline gate row cross-references its R-section in creative-redlines.md with a relative markdown link + 1-sentence operational definition lifted with attribution.
  - README bilingual format mirrors v6.0/v7.0 plugin readmes (EN headings + 中文 body where natural); Phase 31 / Phase 34 status history preserved verbatim.
metrics:
  duration: ~3min
  completed: 2026-06-26T16:07:39Z
  tasks: 2
  files_modified: 2
  review_gates_md_insertions: 119
  review_gates_md_deletions: 9
  readme_insertions: 34
  readme_deletions: 12
---

# Phase 40 Plan 03: Docs — review-gates.md 8→11 + plugin README bilingual Summary

Additive documentation patch: extended the V8.6 8-gate per-phase mapping to 11 gates (3 Phase 40 redline gates R1/R3/R4 appended as 9/10/11) and rewrote the `plugins/review_gates/README.md` as a bilingual (EN headings + 中文 body) readme documenting the auto-detect architecture. Zero code changes; V8.6 8-gate table byte-preserved.

## What Was Built

### `skills/kais-movie-pipeline/references/review-gates.md` (119 insertions, 9 deletions)

Additive-only update to the V8.6 8-gate per-phase mapping doc. The 9 deletions are exclusively header / metadata / summary / heading / See Also rewrites required to surface the 11-gate framing — **the existing V8.6 8-gate table rows and the "Hard vs Soft Gates" section are byte-preserved** (verified via `git diff | grep '^-'`).

Changes:

1. **Header** — `"V8.6 8-Gate Per-Phase Mapping"` → `"11-Gate Per-Phase Mapping (8 V8.6 + 3 Phase 40 Redline, additive)"`. Source line extended to cite `creative-redlines.md §R1/§R3/§R4`. Last-verified stamp updated to `2026-06-26 (Phase 40)`.

2. **Summary section** — Rewritten to mention the 11-gate count + Phase 40 additive extension. A new "Phase 40 additive extension" paragraph explains the 3 redline gates fire after Gate 8 passes, auto-resolve via detectors (no HIL), and reference `creative-redlines.md` for the source spec.

3. **New `## Phase 40 Redline Gates (9-11, additive)` section** — placed between "Hard vs Soft Gates" and "Gate Implementation". Contains:
   - A 3-row table (gates 9/10/11) mapping `gate_id` → trigger-after-gate-8 → `redline_scanner` reviewer → auto-reject mode → creative-redlines source.
   - Per-gate detail subsections (Gate 9 / Gate 10 / Gate 11) each with: the R-section operational definition lifted verbatim from `creative-redlines.md` with attribution + relative link, the detector module path + detection logic summary, the `suggested_action` formula_id + explanation that it's a Phase 39 `formula_library` read-side lookup key, and boundary notes.
   - An 11-gate ASCII sequence diagram showing `Step 1-11 (gates 1-8 HIL) → Gate 8 passes → Phase 40 redline scan (gates 9-11 auto-detect) → final master.mp4 release`.

4. **`## Gate Implementation` section extended** — added a "Two resolution paths (V8.6 HIL vs Phase 40 auto-detect)" subsection with a comparison table, the `auto_detect_and_resolve` / `is_redline_gate` Python contract snippet (Plan 40-02 interface), the rationale for the split (redlines are deterministic; V8.6 needs creative judgment), and the T-40-09 mitigation note (misconfigured `redline_*` gate_id raises KeyError, fails closed). The existing `pause_for_review` / `resolve_direct` / `resume_from_callback` / `mark_episode_failed` bullet list is preserved.

5. **`## All 8 Gates` → `## All 11 Gates (Phase 35+36 Complete, Phase 40 Redline Added)`** — heading renamed; 3 new rows appended to the implementation-wiring table (gates 9/10/11) mapping each to `runner_hooks.auto_detect_and_resolve` + its `GATE_ID` + Auto-detect mode + `redline_scanner (DETECTOR_REGISTRY)` reviewer + `Complete (Phase 40)` status. The 8 existing rows are byte-preserved.

6. **`## See Also` section** — added 3 new bullets: `creative-redlines.md` (with note "Phase 40 redline gates 9-11 implement R1 / R3 / R4 from this ref"), `plugins/review_gates/gates/` detector modules, `runner_hooks.auto_detect_and_resolve`. Existing `gates.yaml` bullet updated from "8 gates" → "Phase 40 expanded 8 → 11 gates".

### `plugins/review_gates/README.md` (34 insertions, 12 deletions)

Rewritten as a bilingual (EN headings + 中文 body) readme. Preserves the Phase 31 / Phase 34 status history verbatim.

Changes:

1. **Description paragraph** — `"8 V8.6 gate YAML config"` → `"11 个 gate 的 YAML 配置(8 V8.6 + 3 Phase 40 redline,additive)"`. Mentions Phase 40 added 3 cross-platform redline gates additively and wired an auto-detect path.

2. **`## Exposed tools`** — `gate_submit` bullet gained a note explaining the `redline_` prefix routing (auto-resolve via Plan-01 detectors, no manual `gate_resolve` needed; V8.6 HIL preserved). `gates_list` description: `"(8 V8.6 gates)"` → `"(11 gates: 8 V8.6 + 3 redline)"`.

3. **New `## Phase 40 Additions` section** — a 3-row table mapping each `gate_id` to its redline (R1/R3/R4), detector module path, and `suggested_action` formula_id. Followed by: explanation that each gate implements one creative-redline (cross-link), detector module purity note (D-34-01 extended, AST-verified, formula_library read-side lookup), auto-detect path explanation (`is_redline_gate` + `auto_detect_and_resolve` + routing logic + rationale), and cross-link to `review-gates.md` for the 11-gate per-phase mapping.

4. **`## Status` section** — Phase 31 and Phase 34 history lines preserved verbatim. New **Phase 40** line appended: "3 redline gates (R1/R3/R4) added additively. Detector modules in `gates/` subpackage + auto-detect path in `runner_hooks.auto_detect_and_resolve`. Plugin version bumped 0.1.0 → 0.2.0."

## Commits

| Hash | Type | Message |
|---|---|---|
| `c6e0232d0` | docs | `docs(phase-40-03): review-gates.md 8→11 gate table + Phase 40 redline section` — additive update; V8.6 8-gate rows byte-preserved |
| `6a09a30e1` | docs | `docs(phase-40-03): plugin README bilingual — Phase 40 redline + auto-detect` — bilingual readme; Phase 31/34 history preserved |

## Verification

All plan verification gates met:

| Gate | Required | Actual | Status |
|---|---|---|---|
| review-gates.md contains all 3 new gate names + Phase 40 terms | yes | 18 grep hits for `Gate 9\|Gate 10\|Gate 11\|redline_emotion_desensitize\|redline_no_cold_open\|redline_unfinished_ending\|auto_detect_and_resolve` | PASS |
| review-gates.md cross-references creative-redlines.md | yes | 9 grep hits for `creative-redlines` | PASS |
| Existing 8-gate table rows byte-preserved (additive only) | yes | `git diff \| grep '^-'` shows 9 deletions, all header/metadata/summary/heading/See Also rewrites — no V8.6 table row deletions | PASS |
| V8.6 8-gate table rows (gates 1-8) still present | yes | 207 grep hits for `\|^| [1-8] \|` patterns (table rows + body references preserved) | PASS |
| "Hard vs Soft Gates" section preserved | yes | 1 hit for `## Hard vs Soft Gates` heading | PASS |
| README mentions Phase 40 + auto-detect + redline gates | yes | 9 grep hits for `Phase 40\|redline_emotion_desensitize\|auto_detect_and_resolve` | PASS |
| README bilingual (中文 body present) | yes | 4 grep hits for `本 plugin\|审批回调\|新增\|零背景铺垫\|结尾未完成\|情绪脱敏` | PASS |
| Phase 31 / Phase 34 status history preserved in README | yes | 4 grep hits for `Phase 31\|Phase 34` (2 in body + 2 in Status section) | PASS |
| gates_list description updated to 11 gates | yes | 1 hit for `11 gates` | PASS |
| Documentation-only plan (zero code files touched) | yes | both commits (`c6e0232d0` + `6a09a30e1`) touched only `.md` files — verified via `git diff --name-only c6e0232d0~1 6a09a30e1` | PASS |
| No edits to other plans' owned files (gate.py / gates.yaml / runner_hooks.py / tests/* / SKILL.md) | yes | both commits' file lists contain only `review-gates.md` + `README.md` | PASS |

## Deviations from Plan

None — plan executed exactly as written. Both tasks completed on the first pass with no auto-fixes (Rules 1-3) or architectural questions (Rule 4) triggered.

## Known Stubs

None. Both files are fully written documentation. The `formula:emotion-break-up` / `formula:cold-open-conflict-hook` / `formula:open-question-cliffhanger` strings mentioned in the docs are Phase 39 `formula_library` read-side lookup keys — the library entries themselves are owned by Phase 39 (Plan 39-02, already shipped). The docs reference the keys; Phase 39 owns the entries.

## Threat Flags

None. Documentation-only plan with no code execution surface. The only externally-visible content is public pattern names ("emotion-break-up", "cold-open-conflict-hook", "open-question-cliffhanger") — no proprietary information, no PII (T-40-10 disposition: accept, per plan threat model).

## Self-Check: PASSED

- FOUND: skills/kais-movie-pipeline/references/review-gates.md
- FOUND: plugins/review_gates/README.md
- FOUND: c6e0232d0 (docs Task 1 — review-gates.md)
- FOUND: 6a09a30e1 (docs Task 2 — README.md)
