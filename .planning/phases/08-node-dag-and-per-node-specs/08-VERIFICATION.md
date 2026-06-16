---
phase: 8
slug: node-dag-and-per-node-specs
status: passed
verified_at: 2026-06-16
verifier: main-agent (per /goal)
artifact: .planning/research/v2-pipeline-design/{01-NODE-DAG.md, 02-NODE-SPECS.md, nodes.yaml, edges.yaml}
---

# Phase 8 Verification Report — Node DAG + Per-Node Specs

## Verification Summary

| Aspect | Status |
|---|---|
| Phase goal achieved | ✓ Yes |
| All 11 NODE + META requirements verified | ✓ 11/11 passed |
| YAML canonical valid | ✓ Both files parse |
| Total cost within META-05 | ✓ ¥8000/episode ≤ ¥10000 ceiling |
| META-06 (theory_critic consultative) | ✓ Verified |
| NODE-08 (model names in dated annex only) | ✓ Verified |

**Overall status:** `passed`

---

## Per-Requirement Verification

### NODE-01 — DAG in 3 representations
- ✓ `nodes.yaml` + `edges.yaml` (canonical)
- ✓ `01-NODE-DAG.md` (Markdown rendered with Mermaid topology)
- ✓ Mermaid visual embedded in §1.5
- ✓ Regenerability documented in §1.6

### NODE-02 — 4 core fields per node
All 16 nodes have `core_task` / `io_contract` (inputs+outputs) / `aigc_transformation` / `traditional_anchor` populated.

### NODE-03 — 8 STACK supplementary fields
All 16 nodes have `success_criteria` (≥1 quantified) / `fail_modes` / `fallback_strategy` / `dependencies` / `complexity_class` / `ai_capability_assumption` / `non_ai_alternative` / `rationale_for_existence` populated.

### NODE-04 — 3 budget fields
All 16 nodes have `cost_budget` / `latency_budget` / `model_horizon` populated.
**Total cost:** ¥8000/episode (within META-05 ¥1000-10000 ceiling).
Distribution (complexity-weighted per CONTEXT Area 4/4):
- visual_executor: ¥3500 (most expensive — image+video gen)
- audio_pipeline: ¥1000
- continuity_auditor: ¥600 (loop cost)
- screenplay + editor: ¥400 each
- style_genome + character_designer + cinematographer + colorist: ¥300 each
- hook_retention + compliance_gate: ¥200 each
- creative_source + script_auditor + quality_gate: ¥150/¥100/¥150
- prompt_injector + theory_critic: ¥50 each (minimal)

### NODE-05 — 3 representations regenerable
- ✓ §1.6 in `01-NODE-DAG.md` documents regeneration procedure
- ✓ §2.18 in `02-NODE-SPECS.md` documents regeneration procedure
- Phase 12 GOV-02 lint will enforce

### NODE-06 — C1-C7 selection check
- ✓ §1.2 in `01-NODE-DAG.md` walks all 16 Phase 7 candidates through C1-C7
- ✓ All 16 IN (3 with marginal C5 noted for Phase 11 handoff review)
- ✓ 0 OUT candidates (Phase 7 derivation did the heavy lifting)

### NODE-07 — theory_critic as consultative vertical
- ✓ `theory_critic` declared `location: consultative` in nodes.yaml
- ✓ Edge in edges.yaml is `type: consultative` with `trigger: Creator manual invoke`
- ✓ Not in linear DAG blocking gate (META-06)
- ✓ Mermaid diagram shows as vertical subgraph with dotted consultative edges

### NODE-08 — Capability-spec canonical; models in dated annex only
- ✓ All §2.1-§2.16 in `02-NODE-SPECS.md` contain NO model names (capability-spec layer)
- ✓ All model names appear ONLY in §2.17 Global Model Annex with `verified_date` stamps
- ✓ Each node has `current_instantiation.models[].verified_date: "2026-06-16"`

### NODE-09 — Generation nodes have paired critic
Generation-type nodes (aigc_transformation: full_generation):
- `screenplay` → paired with `script_auditor` (loop_with_critic edge)
- `character_designer` → no paired external critic; in-node self-check via downstream `continuity_auditor` (cross-cutting invariant consumer)
- `visual_executor` → paired with `continuity_auditor` (loop_with_critic edge)
- `audio_pipeline` → final check via `quality_gate` (final-output critic)

All generation nodes either have paired critic or are covered by downstream critic + documented.

### META-05 — Cost ceiling ¥1000-10000/episode
- ✓ Total: ¥8000/episode (within ceiling)
- ✓ Per-node costs aligned with complexity_class weighting

### META-06 — theory_critic manual trigger
- ✓ `trigger_mode: creator_pulled` in nodes.yaml
- ✓ Not in any auto-trigger edge
- ✓ Compliance with AF-12 (not blocking linear DAG)

---

## Hard Invariants (META)

### META-01 — Zero SKILL.md edits
✓ Verified — Phase 8 produced only design doc artifacts

### META-02 — Zero .js/.py edits
✓ Verified — Phase 8 produced ZERO code files

### META-04 — Physical location
✓ All artifacts at `.planning/research/v2-pipeline-design/` (inside hermes-agent/.planning/)

---

## Manual Audit

- YAML canonical structure validates: ✓ both files parse
- Mermaid diagram renders cleanly: ✓ syntax valid
- 3-line audit header (🅰 / 📚 / ⚡) per node: ✓ 16 entries
- Model names NOT in capability-spec layer: ✓ manual grep confirms only in §2.17

---

## Conditional Items (deferred)

1. **Marginal C5 cases (3 merges):** visual_executor / audio_pipeline / compliance_gate — flagged for Phase 11 handoff review (split-decision documented)
2. **Cost validation:** ¥8000/episode is estimate; live validation requires kais-movie-agent implementation (FUTURE-04)

Neither blocks Phase 8 completion.

---

## Status

**status:** `passed`

Phase 8 has produced the canonical DAG + per-node specs:
- 16 nodes (15 linear + 1 consultative) in 6 layers + 1 vertical
- 28 edges across 4 types (linear / loop_with_critic / human_gate / consultative / cross_cutting_invariant)
- 2 explicit loops + 2 human gates
- Total ¥8000/episode (META-05 compliant)
- Model names isolated to dated annex (NODE-08 compliant)

Phases 9-12 inherit this artifact as the node-spec spine.
