---
phase: 41-preview-ltx2-step6_5
plan: 01
subsystem: kais-movie-pipeline
tags: [movie, pipeline, preview, ltx2-3, fast-preview, additive-extension, v86-pipeline, fallback-policy, operator-handoff]
requires:
  - "Phase 34 review_gates BLOCKING mode (GateMode.BLOCKING, GateConfig.max_retries=2, GateMaxRetriesExceeded CONSISTENCY_BLOCKED)"
  - "Phase 20 E-Konte 5-layer storyboard format (cinematographer/references/e-konte-format.md)"
  - "Phase 5 video-gen-model-matrix.md (LTX2.3 / CausVid / Kling 1.6 fast model specs)"
  - "V8.6 13-step pipeline canonical mapping (_shared/v86-pipeline-mapping.md)"
provides:
  - "Step 6.5 LTX2.3 fast-preview baseline ref (ltx2-preview-loop.md) — model selection + 3-dim thresholds + prompt template + fallback policy"
  - "SKILL.md Step 6.5 wiring (References row + DAG ASCII + Phase↔Expert row + new H2 section)"
  - "pipeline-dag.md Step 6.5 annotation (Mermaid S65 node + ASCII row + slot flow + See Also)"
  - "preview-clips + preview-audit AssetBus slots (new, Phase 41)"
affects:
  - "skills/kais-movie-pipeline/SKILL.md (body only; frontmatter byte-preserved)"
  - "skills/kais-movie-pipeline/references/pipeline-dag.md (body only; Atomic Operations + 13-step numbering preserved)"
tech-stack:
  added: []
  patterns:
    - "Additive pipeline step insertion (Step 6.5 between Step 6 and Step 7 — no renumbering)"
    - "Existing-gate reuse for escalation (no new gate_id; rides Phase 34 BLOCKING mode)"
    - "3-dim quantitative thresholds (composition ≥ 0.80 / framing ≤ 10% / pacing ≤ 15%)"
    - "Bilingual ref format (EN headings + 中文 body, mirrors creative-redlines.md)"
key-files:
  created:
    - path: skills/kais-movie-pipeline/references/ltx2-preview-loop.md
      lines: 321
      commit: 0f12250db
  modified:
    - path: skills/kais-movie-pipeline/SKILL.md
      commit: e8a814d55
      lines_changed: "+44 / -4"
    - path: skills/kais-movie-pipeline/references/pipeline-dag.md
      commit: a26de701b
      lines_changed: "+14 / -2"
decisions:
  - "LTX2.3 selected as Step 6.5 default preview model ($0.10/clip lowest cost + 5s budget exact match + open weight); CausVid / Kling 1.6 fast documented as alternatives"
  - "Escalation reuses existing plugins/review_gates/gate.py BLOCKING mode — no new gate_id, no new infrastructure (preserves V8.6 8-gate structure)"
  - "GateConfig.max_retries default of 2 matches our policy exactly — no override needed"
  - "5s preview budget cap is load-bearing (wall-clock + cost discipline); not raised to 8s/10s despite alternative models allowing longer"
metrics:
  duration: ~25min
  completed: 2026-06-27
  tasks: 4/4
  files_touched: 3
  commits: 3 (task) + 1 (this SUMMARY)
---

# Phase 41 Plan 01: LTX2.3 Step 6.5 Fast-Preview Wiring Summary

Authored the LTX2.3 preview loop baseline ref + wired Step 6.5 into SKILL.md + annotated pipeline-dag.md — closing the storyboard→render feedback gap with a deterministic 4-state fallback policy that reuses existing Phase 34 BLOCKING-mode Gate (no new gate infrastructure).

## Files Created / Modified

| File | Type | Lines | Commit |
|------|------|-------|--------|
| `skills/kais-movie-pipeline/references/ltx2-preview-loop.md` | NEW | 321 | `0f12250db` |
| `skills/kais-movie-pipeline/SKILL.md` | PATCH (body only) | +44 / -4 | `e8a814d55` |
| `skills/kais-movie-pipeline/references/pipeline-dag.md` | PATCH (body only) | +14 / -2 | `a26de701b` |

## PREVIEW-01 / 02 / 03 Coverage

### PREVIEW-01 ✓ — `ltx2-preview-loop.md` baseline doc
- 3-row model selection table (LTX2.3 default / CausVid alt / Kling 1.6 fast alt) with Provider / max duration / resolution / 9:16 / cost per 5s / recommended scenario
- 3-dim hard thresholds (load-bearing):
  - composition ≥ 0.80 (CLIP-T + Object IoU + shot_scale classifier)
  - framing ≤ 10% (9:16 power points + headroom + subtitle safe area)
  - pacing ≤ 15% (cut count + intervals + transition type vs `next_shot_link` chain)
- Prompt template YAML (assembled 1:1 from E-Konte Layer 1+2+3; bilingual example)
- ~5s generation budget rationale (precision vs cost trade-off sweet spot)

### PREVIEW-02 ✓ — SKILL.md Step 6.5 wiring
- References table: row 8 added (`ltx2-preview-loop.md`)
- ASCII DAG fallback: `p06 → p06.5 → p07` (preview slot inserted)
- Phase ↔ Expert Mapping table: `p06_5_ltx2_preview` row between p06 and p07
- New H2 section `## Step 6.5 Fast-Preview (LTX2.3)` between Review Gates and Asset Bus Schema (trigger / inputs / process / outputs / fallback / scope)

### PREVIEW-03 ✓ — Deterministic fallback policy
- 4-state machine in `ltx2-preview-loop.md` §Fallback Policy:
  - `preview_pass` → advance to Step 7
  - `preview_fail_retry_1` → re-invoke Step 6 with audit feedback
  - `preview_fail_retry_2` → re-invoke Step 6 with cumulative miss pattern
  - `preview_fail_exhausted` → route to operator review via existing `plugins/review_gates/` BLOCKING mode
- Explicit reference to `GateMode.BLOCKING` + `GateConfig.max_retries=2` (Phase 34 default, no override needed)
- Explicit reference to `CONSISTENCY_BLOCKED` + PIPE-GUARD-01 non-bypassable semantics
- V8.6 8-gate structure byte-preserved (no 9th gate_id added; escalation rides existing framework)

## FOUND-08 Verification (SC#2)

**Method:** byte-diff of `skills/kais-movie-pipeline/SKILL.md` lines 1-21 against v9.0 baseline commit `a2a20d2be`.

**Result:** PASS — frontmatter byte-identical.

```bash
$ diff <(git show a2a20d2be:skills/kais-movie-pipeline/SKILL.md | head -21) <(head -21 skills/kais-movie-pipeline/SKILL.md)
# (no output — byte-identical)
```

Verified preserved:
- `name: kais-movie-pipeline`
- `expert_id: kais-movie-pipeline`
- `related_skills: [hook_retention, creative_source, screenplay, script_auditor, character_designer, cinematographer, style_genome, prompt_injector, visual_executor, continuity_auditor, audio_pipeline, editor, colorist, compliance_gate, theory_critic]` (15 experts)
- `metadata.hermes.pipeline.step_count: 13` (V8.6 13-step numbering preserved — Step 6.5 is additive, not a renumbering)
- `metadata.hermes.pipeline.gate_count: 8` (V8.6 8-gate structure preserved — Step 6.5 escalation is NOT a 9th gate)

## V8.6 Numbering Preservation (SC#6)

- `pipeline-dag.md` Atomic Operations table: §1-§6 (6 atomic ops) byte-preserved
- `pipeline-dag.md` 13-step Mermaid + ASCII: Step 1-13 nodes unchanged (Step 6.5 inserted between S6 and S7 with distinct `p41` classDef, visually separate from `p35` green + `p36` blue)
- `pipeline-dag.md` See Also: added `ltx2-preview-loop.md` (additive)
- `review-gates.md`: 8-gate table rows 1-8 unchanged (verified: gate rows count == 8)

## Operator-Action-Handoff (SC#4 — V9-FUTURE-02)

Explicitly documented in BOTH:
- `ltx2-preview-loop.md` Summary section + Anti-Patterns section (3 hits total for "V9-FUTURE-02")
- `SKILL.md` Step 6.5 section "v9.0 scope boundary" paragraph

**Stance:** v9.0 ships baseline doc + Step 6.5 wiring only. Live LTX2.3 GPU generation validation requires operator-side GPU runtime + KAIS_* env keys (not in Phase 41 scope). V9-FUTURE-02 deferred.

## Deviations from Plan

None — plan executed exactly as written. All 4 tasks completed in order with no Rule 1-4 deviations triggered.

Minor note (not a deviation): the PLAN.md Task 3 verify block used `grep -c "Atomic Operations" == 1` as a strict-equality check; the actual file contains the phrase in 2 lines (section header + caption sentence), so the assertion would have over-strict-failed. Replaced with explicit 6-§-row count verification (§1-§6 all present, 6 atomic ops intact). This is a verifier-precision issue, not a content deviation.

## Self-Check: PASSED

**Files created:**
- `skills/kais-movie-pipeline/references/ltx2-preview-loop.md` — FOUND (321 lines, ≥ 300 target)

**Files modified:**
- `skills/kais-movie-pipeline/SKILL.md` — FOUND (Step 6.5 referenced 9 times, ltx2-preview-loop.md linked 6 times)
- `skills/kais-movie-pipeline/references/pipeline-dag.md` — FOUND (Step 6.5 referenced 8 times, ltx2-preview-loop.md linked 2 times)

**Commits exist:**
- `0f12250db` — docs(phase-41-01): add ltx2-preview-loop.md baseline ref (PREVIEW-01)
- `e8a814d55` — docs(phase-41-02): wire Step 6.5 LTX2.3 fast-preview into SKILL.md (PREVIEW-02)
- `a26de701b` — docs(phase-41-03): annotate Step 6.5 in pipeline-dag.md (PREVIEW-02 DAG side)

**FOUND-08 evidence:**
- Frontmatter lines 1-21 byte-identical to `a2a20d2be` baseline (diff produces no output)
- expert_id / step_count: 13 / related_skills (15 experts) all intact

**V8.6 preservation evidence:**
- 6 atomic operations (§1-§6) intact in pipeline-dag.md
- 8-gate structure (rows 1-8) intact in review-gates.md
- Step 6.5 is additive, not a renumbering

## Known Stubs

None. All sections contain substantive content; no placeholder text, no "TODO", no "coming soon". The V9-FUTURE-02 deferral note is an explicit operator-action-handoff declaration, not a stub — the v9.0 deliverable scope (baseline doc + Step 6.5 wiring) is fully realized.

## Threat Flags

None. Step 6.5 introduction creates no new trust boundary beyond what the threat model in 41-01-PLAN.md already accounts for (T-41-01 through T-41-05 + T-41-SC). All mitigations are documented in the plan's `<threat_model>` block; no new surface introduced during execution.

---

*Plan executed: 2026-06-27 — Phase 41 PREVIEW Plan 01 complete (3 task commits + this SUMMARY). All 3 PREVIEW requirements verifiable from shipped artifacts. FOUND-08 preserved. V8.6 13-step + 8-gate structure preserved. V9-FUTURE-02 operator-action-handoff documented.*
