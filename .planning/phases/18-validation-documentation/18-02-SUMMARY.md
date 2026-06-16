---
phase: 18-validation-documentation
plan: 02
subsystem: planning-documentation
tags: [documentation, mermaid-dag, inventory, glossary, model-annex, milestone-gate]
requires:
  - Phase 18 Plan 01 (VALIDATION-REPORT.md — canonical 4-bucket classification source-of-truth)
  - 01-NODE-DAG.md §1.5 (canonical Mermaid topology source)
  - 02-NODE-SPECS.md §2.17 (canonical Global Model Annex source)
provides:
  - "skills/movie-experts/README.md — Mermaid DAG + reconciled inventory tables + accurate footer count"
  - "skills/movie-experts/_shared/glossary.md — DOC-02 5-term verification (3 present + 2 added) + Phase 18 verification matrix"
  - "skills/movie-experts/_shared/known-external-models.yaml — Phase 8 §2.17 dated annex (18 new + 9 extended entries, all verified_date: 2026-06-17)"
affects:
  - ".planning/ROADMAP.md — Phase 18 criteria #3/#4/#5 + DOC-01 + DOC-02 satisfied"
  - ".planning/REQUIREMENTS.md — DOC-01 + DOC-02 to be marked complete in plan 18-03"
tech-stack:
  added: []
  patterns:
    - "ASCII-art → Mermaid DAG wholesale replacement (single canonical source-of-truth: 01-NODE-DAG.md §1.5)"
    - "4-bucket inventory table consolidation (Active DAG / Active non-DAG / Deprecated / Redirect stubs)"
    - "Glossary DOC-02 verification matrix pattern (term × line-of-entry × phase-18-status)"
    - "Existing-entry inline extension (single source of truth) vs duplicate overlay block (corrected mid-task)"
key-files:
  created:
    - ".planning/phases/18-validation-documentation/18-02-SUMMARY.md"
  modified:
    - "skills/movie-experts/README.md"
    - "skills/movie-experts/_shared/glossary.md"
    - "skills/movie-experts/_shared/known-external-models.yaml"
decisions:
  - "Mermaid block replaces ASCII art wholesale (no comment fallback retained) — the prior ASCII DAG had accreted across Phases 14-15-16-17 and no longer matched v2.0 PRFP canonical topology"
  - "Phase 8 Cross-Cutting ASCII diagram converted to 3-row table distinguishing in-DAG (theory_critic) vs not-in-DAG (documentary_maker + animation_studio) verticals"
  - "7 inventory sub-sections consolidated into 3 canonical tables (Active / Deprecated / Redirect stubs) with per-phase provenance preserved in dedicated notes subsection"
  - "Footer count + Status line explicitly cite 21-target → actual reconciliation per CONTEXT D-06 (no silent sign-off)"
  - "quality_gate gap (DEFECT VALIDATE-D1 from 18-01) documented as Topology notes bullet — flagged as post-v3.0 candidate, not silently hidden"
  - "Glossary DOC-02 verification: 3 of 5 terms already PRESENT (Phase 14/15/16 additions), 2 ADDED in Phase 18 §canonical term reconciliation (continuity_auditor + compliance_gate)"
  - "known-external-models.yaml: initial overlay-block approach created 9 duplicate-name entries; corrected mid-task to inline-extend existing base entries instead (single source of truth per plan directive)"
metrics:
  duration: "~5 min"
  completed: "2026-06-17"
  tasks: 3
  files_touched: 3
---

# Phase 18 Plan 02: Documentation Finalization Summary

Finalized v3.0 user-facing documentation surfaces: replaced the accreted ASCII-art DAG in README.md with the canonical Mermaid block from `01-NODE-DAG.md §1.5`, consolidated 7 inventory sub-sections into 3 canonical tables matching VALIDATION-REPORT.md's 4-bucket classification, added DOC-02-required H3 entries for the 2 missing glossary terms (continuity_auditor + compliance_gate), and added the Phase 8 §2.17 dated annex (18 new model entries + 9 inline-extended existing entries) to known-external-models.yaml. DOC-01 + DOC-02 are satisfied.

## Completed Tasks

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | README.md Mermaid DAG conversion + reconciled inventory table | `9ee702f5a` | `skills/movie-experts/README.md` |
| 2 | Glossary verification + add missing 5 new-expert terms | `f57c0cda3` | `skills/movie-experts/_shared/glossary.md` |
| 3 | known-external-models.yaml Phase 8 §2.17 dated annex additions | `70a478a18` | `skills/movie-experts/_shared/known-external-models.yaml` |

## Verification Results

| Criterion | Verdict |
|-----------|---------|
| README.md has fenced ```mermaid block (no ASCII art DAG) | PASS (canonical 16-node topology, attributed to 01-NODE-DAG.md §1.5) |
| README.md Mermaid block contains `graph TD` + all 16 nodes + 7 topology properties | PASS |
| README.md inventory consolidated into Active / Deprecated / Redirect stubs tables matching VALIDATION-REPORT.md | PASS (15 active DAG + 3 active non-DAG + 3 deprecated + 10 redirect stubs) |
| README.md footer count + Status line reflect reconciled 31-count | PASS (with explicit 21-target → actual reconciliation note per CONTEXT D-06) |
| No ASCII-art DAG fragment remains in README.md | PASS (USER INTENT header gone; only legitimate File Layout tree-style `├──` remains) |
| glossary.md has H3 entries for all 5 DOC-02 terms | PASS (3 PRESENT from Phase 14/15/16, 2 ADDED in Phase 18) |
| glossary.md has Phase 18 DOC-02 verification section | PASS (verification matrix with per-term status) |
| glossary.md Last-updated header reflects Phase 18 | PASS |
| known-external-models.yaml parses as valid YAML | PASS (73 entries, 73 unique names, no duplicates) |
| known-external-models.yaml has Phase 8 §2.17 dated annex section | PASS (header comment + 18 new entries + 9 inline-extended entries) |
| known-external-models.yaml entries carry verified_date: 2026-06-17 | PASS (27 entries with verified_date stamps) |
| DOC-01 (README inventory + DAG topology) satisfied | PASS |
| DOC-02 (glossary 5 terms + §2.17 model annex) satisfied | PASS |

## Key Findings

### Mermaid DAG conversion

The prior ASCII-art DAG in README.md had accreted patches across Phases 14 (visual_executor merge), 15 (audio_pipeline merge), 16 (prompt_injector NEW), and 17 (3 deprecations). The result was a 76-line ASCII block whose topology no longer matched the v2.0 PRFP canonical DAG (it omitted quality_gate, had production in the linear pipeline, and was missing the screenplay↔script_auditor loop annotation). The Mermaid block from `01-NODE-DAG.md §1.5` replaces it wholesale with the canonical 16-node topology including:
- 7 subgraphs (L0 Root / L1 Intent parallel / L2 Visual intent / L3 Visual exec / L4 Audio+Post parallel / L5 Form-specific / L6 Final gates / Vertical Consultative)
- All 16 nodes with bilingual labels
- Linear edges + form-specific feedback + 2 loops + 2 human gates + consultative dotted edges + 2 cross-cutting invariants
- classDef styling (linear / loop / gate / consultative / invariant)

The 7 topology properties from §1.3 are documented in a Topology notes bullet list below the fence.

### Inventory consolidation

7 prior inventory sub-sections (14 Original / 4 New Phase 1-5 / 5 New Phase 7 / 3 New Phase 8 / 1 New Phase 16 / 3 Deprecated Phase 17) consolidated into 3 canonical tables:
- **Bucket 1 — Active DAG pipeline-roles (15)** with mapping-type column
- **Bucket 2 — Active non-DAG verticals (3)**
- **Deprecated (3)**
- **Redirect stubs (10)** with status + redirect-target + phase-migrated columns

Per-phase provenance preserved in a dedicated "Provenance notes" subsection so no historical information was lost.

### Glossary DOC-02 verification

Of the 5 required DOC-02 terms:
- **3 PRESENT** (no action needed): visual_executor (Phase 14, line 227), audio_pipeline (Phase 15, line 239), prompt_injector (Phase 16, line 251)
- **2 ADDED** in Phase 18 §canonical term reconciliation: continuity_auditor (Phase 13 rename from continuity, L3 critic_paired with visual_executor) + compliance_gate (Phase 13 rename from compliance_marketing, L6 final_gate paired with quality_gate)

The verification matrix documents this explicitly per DOC-02 audit requirement.

### §2.17 dated annex coverage

All 19 model entries from `02-NODE-SPECS.md §2.17` Global Model Annex now have allowlist coverage with `verified_date: 2026-06-17` provenance:
- **18 NEW entries**: claude-sonnet-4.5, claude-haiku-4.5, claude-opus-4.7, glm-4.6, gpt-5, gpt-5-mini, gemini-3-pro, suno-v5, udio-2, audioldm-3, ideogram, runway-gen-5, azure-tts, openai-tts-2, sd4, davinci-resolve, ffmpeg-dsp, template-few-shot
- **9 inline-extended existing entries**: flux2, cosyvoice, elevenlabs, stable_audio, musicgen, kling, sora, veo, ip-adapter (single source of truth preserved — original Phase 5/7 audit-trail context intact)

## Deviations from Plan

### [Rule 1 — Bug] Corrected duplicate-name entries in known-external-models.yaml

- **Found during:** Task 3 verification (YAML parse + entry count check)
- **Issue:** Initial implementation added a separate "Existing-entry extensions" overlay block with 9 duplicate-name entries (flux2, cosyvoice, elevenlabs, stable_audio, musicgen, kling, sora, veo, ip-adapter) that re-declared canonical tokens. This created 9 duplicate-name entries (82 total, 73 unique). The plan explicitly directed "verify + add dated-annex metadata, do NOT duplicate the base entry" — the overlay approach violated this.
- **Fix:** Removed the overlay block; instead inline-extended the 9 existing base entries by adding `verified_date` + `stability` + `node_role` fields and appending a "Phase 8 §2.17 dated annex (2026-06-17):" segment to each `provenance` string. Original audit-trail provenance preserved.
- **Files modified:** `skills/movie-experts/_shared/known-external-models.yaml`
- **Commit:** `70a478a18` (fix landed in the same commit before push — no separate fix-up commit needed)

No other deviations — plan executed as written.

## Self-Check: PASSED

- FOUND: `skills/movie-experts/README.md` (Mermaid block + 3 consolidated inventory tables + reconciled footer)
- FOUND: `skills/movie-experts/_shared/glossary.md` (5/5 DOC-02 terms with H3 entries + verification matrix)
- FOUND: `skills/movie-experts/_shared/known-external-models.yaml` (valid YAML, 73 entries, 27 with verified_date: 2026-06-17)
- FOUND: commit `9ee702f5a` (Task 1 — README Mermaid + inventory + footer)
- FOUND: commit `f57c0cda3` (Task 2 — glossary DOC-02 verification)
- FOUND: commit `70a478a18` (Task 3 — known-external-models.yaml §2.17 annex)

---

*Plan 18-02 complete. README.md + glossary.md + known-external-models.yaml are the canonical v3.0 user-facing documentation surfaces. DOC-01 + DOC-02 satisfied. Plan 18-03 (sign-off + close) is the remaining v3.0 milestone plan.*
