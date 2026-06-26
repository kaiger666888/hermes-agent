---
phase: 39-form-formula-library
plan: 02
subsystem: formula-library
tags: [seed-data, formulas, fair-use, bilingual, form-03]
requires:
  - "Plan 39-01 schema.py::Formula (validates JSON shape; not yet shipped at time of writing — wave 1 sibling)"
provides:
  - "10 seed formula JSON files covering 5-genre × 2-mood matrix (FORM-03)"
  - "LICENSE.md with per-formula fair-use attribution for all 10 formulas"
  - "Bilingual README.md (plugin manual, EN headings + 中文 body)"
affects:
  - "Plan 39-03 SKILL.md Step 0 wiring (consumes formula_lookup output)"
  - "Plan 39-03 theory_critic formula_reference input (consumes Formula objects)"
tech-stack:
  added: []
  patterns:
    - "Fair-use citation discipline: every JSON carries non-null citation.source from {notion, public-book, kais-benchmark}"
    - "Bilingual convention: EN headings + 中文 body (per CLAUDE.md)"
    - "5×2 seed matrix coverage — exactly 1 formula per (genre, mood) cell"
key-files:
  created:
    - plugins/formula_library/library/formula_urban_fantasy_light_01.json
    - plugins/formula_library/library/formula_mystery_twist_light_01.json
    - plugins/formula_library/library/formula_family_emotion_light_01.json
    - plugins/formula_library/library/formula_campus_youth_light_01.json
    - plugins/formula_library/library/formula_workplace_light_01.json
    - plugins/formula_library/library/formula_urban_fantasy_angst_01.json
    - plugins/formula_library/library/formula_mystery_twist_angst_01.json
    - plugins/formula_library/library/formula_family_emotion_angst_01.json
    - plugins/formula_library/library/formula_campus_youth_angst_01.json
    - plugins/formula_library/library/formula_workplace_angst_01.json
    - plugins/formula_library/LICENSE.md
    - plugins/formula_library/README.md
  modified: []
decisions:
  - "Filename convention follows PLAN.md: formula_{genre_slug_underscore}_{mood_slug}_01.json (not orchestrator brief's simpler form). PLAN.md is authoritative."
  - "Vary top platform across light formulas (抖音/B站/视频号/快手/抖音) so Plan 39-03 lookup ranking tests have signal."
  - "虐心 mood = emotional weight (lost/betrayal/sacrifice), explicitly NOT graphic content (per creative-redlines §题材禁忌 + cn-content-rules)."
  - "Multi-source citations allowed (e.g. Notion + 公开书); citation.source_type picks the *primary* source per formula. LICENSE §Source List documents the multi-source reality."
  - "All eval_score: null for seed formulas — v6.0 eval gate 回填 deferred (V9-FUTURE-03 expansion scope)."
metrics:
  duration: "225s (~4min)"
  completed: "2026-06-26"
  tasks: 3
  files-created: 12
  formulas: 10
---

# Phase 39 Plan 39-02: 10 Seed Formulas + LICENSE + Bilingual README Summary

10 seed formula JSON files covering the full 5-genre × 2-mood matrix (FORM-03), each carrying a fair-use citation from Notion / public-book / kais-benchmark, plus LICENSE.md with per-formula attribution and a bilingual plugin README.

---

## What Shipped

### 10 Seed Formulas (5×2 matrix, exactly 1 formula per cell)

| Genre \ Mood | 轻喜剧 (light) | 虐心 (angst) |
|--------------|----------------|--------------|
| 都市奇幻 | `urban-fantasy-light-01` (抖音-top 0.92, Notion verbatim-spec) | `urban-fantasy-angst-01` (视频号-top 0.88, Notion §题材禁忌 paraphrased) |
| 悬疑反转 | `mystery-twist-light-01` (B站-top 0.88, 公开书 paraphrased) | `mystery-twist-angst-01` (抖音-top 0.90, three-second-hooks 示例4 + kais-bench derived) |
| 家庭情感 | `family-emotion-light-01` (视频号-top 0.90, Notion+书 paraphrased) | `family-emotion-angst-01` (抖音-top 0.89, three-second-hooks 示例14 + 书 paraphrased) |
| 校园青春 | `campus-youth-light-01` (快手-top 0.88, kais-bench derived) | `campus-youth-angst-01` (快手-top 0.86, 书 + kais-bench derived) |
| 职场商战 | `workplace-light-01` (抖音-top 0.87, Notion+书 paraphrased) | `workplace-angst-01` (抖音-top 0.88, three-second-hooks 示例7 + Notion paraphrased) |

### Documentation

- **`LICENSE.md`** — Fair Use Declaration + Source List (notion/public-book/kais-benchmark) + Per-Formula Attribution for all 10 formula_ids (verbatim citation.source strings) + 90-day Refresh Cadence (next review 2026-09-26).
- **`README.md`** — Bilingual plugin manual: EN headings + 中文 body. Schema table (11 fields), Library (10 formulas grouped by genre), Usage example, Adding Formulas guide, Integration section (kais-movie-pipeline Step 0 + theory_critic formula_reference).

---

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | `599fa5ad9` | `feat(phase-39-02): 5 轻喜剧 seed formulas (FORM-03)` |
| 2 | `4105ab235` | `feat(phase-39-02): 5 虐心 seed formulas (FORM-03 — matrix complete)` |
| 3 | `d4a036964` | `docs(phase-39-02): LICENSE + bilingual README (FORM-03 fair-use attribution)` |

---

## Verification

Each task's `<verify><automated>` block from PLAN.md was run + passed:

- **Task 1 verify:** 5 light formulas parsed, all 5 genres represented, every required FORM-02 field present, every `citation.source` non-empty, all `eval_score: null`.
- **Task 2 verify:** 10 total formulas parsed, 5×2 matrix coverage confirmed exactly (10 unique (genre, mood) cells), every required field present.
- **Task 3 verify:** LICENSE.md contains "Fair Use" + every formula_id from JSON; README.md is bilingual (含 "配方库" + "formula_lookup").
- **End-to-end quality gate (final):** 10 files / 5×2 matrix / source_type valid / fair_use_status valid / fit_score ∈ [0,1] / runtime_sec ∈ [60,600] / LICENSE attribution complete / README bilingual — ALL PASSED.

**Note on schema validation:** Plan 39-01's `schema.py` (Pydantic `Formula` model) has NOT shipped at time of writing — it is a wave-1 sibling plan. This plan's `<verify>` blocks use pure-JSON validation (`json.loads` + field-presence checks), which works without the Pydantic schema. Once Plan 39-01 ships, the integration tests in Plan 39-03 (`test_schema.py`) will round-trip these 10 JSON files through `Formula.model_validate()` to enforce Pydantic-level constraints (Literal enum validation, fit_score range, etc.).

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Python interpreter is `python3`, not `python`**
- **Found during:** Task 1 verify step
- **Issue:** First verify run failed with `python: 未找到命令` (command not found).
- **Fix:** Switched all verify commands from `python -c` to `python3 -c`. No file content affected; only the verify invocation.
- **Files modified:** None (verify-only).

### Plan-Faithful Decisions (not deviations)

- **Filename convention:** Followed PLAN.md (`formula_{genre_slug_underscore}_{mood_slug}_01.json`) rather than orchestrator brief's simpler form. PLAN.md is authoritative per execution protocol.
- **Platform variation:** Followed plan's platform_fit guidance (urban_fantasy 抖音-top, mystery_twist B站-top, family_emotion 视频号-top, campus_youth 快手-top, workplace 抖音-top for light; varied for angst) to give Plan 39-03 lookup-ranking tests deterministic ordering signal.
- **Multi-source citations:** Several formulas cite 2 sources (e.g. Notion + 公开书). This is permitted by PLAN.md (`citation.source` is a free-form string). The `source_type` field picks the *primary* source. LICENSE §Source List documents the multi-source reality explicitly.

No other deviations. Plan executed as written.

---

## Cross-References

- **Plan 39-01** (sibling, wave 1): ships `schema.py::Formula` Pydantic model that will validate these JSON files. Once it ships, run `python -m pytest plugins/formula_library/tests/test_schema.py -v` from Plan 39-03 to confirm.
- **Plan 39-03** (wave 2, depends_on [39-01, 39-02]): wires `formula_lookup` as Step 0 in `kais-movie-pipeline/SKILL.md` + `formula_reference` in `theory_critic/SKILL.md` (body-only patches, frontmatter byte-frozen per FOUND-08).
- **`genre-anchor-urban-fantasy.md`** — V1 题材锚定 source for `urban-fantasy-light-01`.
- **`three-second-hooks.md`** — 5-type hook taxonomy source for `hook_pattern` field + 示例 4/14/7 references in angst formulas.
- **`cn-content-rules.md`** — CN compliance baseline; 虐心 formulas designed as emotional weight, NOT graphic content.

---

## Known Stubs

None. All 10 formulas are fully-authored (no placeholder text, no TODO markers, no hardcoded empty values flowing to UI). `eval_score: null` is intentional per FORM-02 spec ("可选, 从 v6.0 eval gate 回填") and per PLAN.md task action ("All `eval_score: null`"). V9-FUTURE-03 (50+ formula expansion) will回填 eval scores via v6.0 gate.

---

## Threat Flags

None. No new security-relevant surface introduced beyond what PLAN.md `<threat_model>` documents:
- T-39-05 (Repudiation / fair-use attribution) — mitigated by LICENSE.md per-formula attribution + 90-day refresh cadence.
- T-39-06 (Information disclosure / citation source strings) — accepted; all citations reference public Notion pages, published books, or internal benchmarks — no PII or credentials.
- T-39-07 (Tampering / seed JSON content) — accepted; files ship under git, review-bound.

No new network endpoints, auth paths, file access patterns, or trust-boundary schema changes introduced by this plan.

---

## Self-Check: PASSED

Files verified to exist on disk:
- FOUND: `plugins/formula_library/library/formula_urban_fantasy_light_01.json`
- FOUND: `plugins/formula_library/library/formula_mystery_twist_light_01.json`
- FOUND: `plugins/formula_library/library/formula_family_emotion_light_01.json`
- FOUND: `plugins/formula_library/library/formula_campus_youth_light_01.json`
- FOUND: `plugins/formula_library/library/formula_workplace_light_01.json`
- FOUND: `plugins/formula_library/library/formula_urban_fantasy_angst_01.json`
- FOUND: `plugins/formula_library/library/formula_mystery_twist_angst_01.json`
- FOUND: `plugins/formula_library/library/formula_family_emotion_angst_01.json`
- FOUND: `plugins/formula_library/library/formula_campus_youth_angst_01.json`
- FOUND: `plugins/formula_library/library/formula_workplace_angst_01.json`
- FOUND: `plugins/formula_library/LICENSE.md`
- FOUND: `plugins/formula_library/README.md`

Commits verified in git log:
- FOUND: `599fa5ad9` (Task 1)
- FOUND: `4105ab235` (Task 2)
- FOUND: `d4a036964` (Task 3)

---

*SUMMARY authored: 2026-06-26 — v9.0 Phase 39 Plan 39-02 complete.*
