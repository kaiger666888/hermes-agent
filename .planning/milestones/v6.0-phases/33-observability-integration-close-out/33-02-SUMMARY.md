---
phase: 33
plan: 02
subsystem: documentation
tags: [architecture-doc, skills-mapping, sign-off, v6-feedback-loop, sc-4, sc-5, close-out, documentation]
requires:
  - "Phase 28-32 shipped implementations (feedback_ingest + feedback_schema + feedback_store + _eval/runner + _eval/gate + evolution/* + curator + curator_audit + hermes_cli/feedback + hermes_cli/curator)"
  - "skills/movie-experts/_shared/v86-pipeline-mapping.md (v5.0 structural template)"
  - ".planning/research/v2-pipeline-design/skills-mapping.yaml v5_ref_signoffs schema (8+ field template)"
  - "Phase 33 Plan 01 test file (tests/hermes_cli/test_curator_stats.py — appended to)"
provides:
  - "Canonical v6.0 feedback-loop architecture reference (skills/movie-experts/_shared/v6-feedback-loop-architecture.md)"
  - "skills-mapping.yaml v6_ref_signoffs section with 1 entry mirroring v5 schema"
  - "TestArchitectureDoc + TestSkillsMappingV6 verification tests (14 tests)"
affects:
  - "skills/movie-experts/_shared/v6-feedback-loop-architecture.md (NEW — 305 lines)"
  - ".planning/research/v2-pipeline-design/skills-mapping.yaml (MODIFIED — additive v6_ref_signoffs section)"
  - "tests/hermes_cli/test_curator_stats.py (EXTENDED — TestArchitectureDoc + TestSkillsMappingV6 classes appended)"
tech-stack:
  added: []
  patterns:
    - "v86-pipeline-mapping.md structural conventions (metadata header block + See Also + Source Citation + Refresh Cadence + footer ownership line)"
    - "TDD RED → GREEN cycle (RED commit first, then GREEN commit)"
    - "ASCII data-flow diagram (no mermaid — renders everywhere)"
    - "Bilingual EN body + CN section headers (CLAUDE.md convention)"
    - "Internally-authored sign-off entry (v6 has no upstream external source unlike v4/v5 refs)"
key-files:
  created:
    - skills/movie-experts/_shared/v6-feedback-loop-architecture.md
  modified:
    - .planning/research/v2-pipeline-design/skills-mapping.yaml
    - tests/hermes_cli/test_curator_stats.py
decisions:
  - "D-doc-structure: mirror v86-pipeline-mapping.md conventions (10 H2 sections: 7 CONTEXT.md content + 3 v86 footer) — honored"
  - "D-bilingual: English body + Chinese section headers per `### <EN> / <中文>` convention — honored"
  - "D-diagram-format: ASCII data flow (no mermaid — renders everywhere) — honored + test_no_mermaid_block asserts"
  - "D-v6-signoff-anchor-req: OBS-01 (v6 has no INTEGRATION-* reqs; OBS-01 defensible anchor) — honored"
  - "D-yaml-internal-source: notes field makes internally-authored status explicit (unlike v4/v5 which cite external books) — honored"
  - "D-h2-bound-fix: upper bound 9 → 11 (Rule 1: plan's own <action> requires 3 footer sections on top of 7 content = 10 minimum; original 9 bound contradicted plan requirements)"
  - "D-header-parse-fix: split on `\\n---` instead of `\\n\\n` (Rule 1: original split returned only H1 title, missing metadata block that lives between title and first `---` separator)"
metrics:
  duration: "~4.5 minutes (268s)"
  completed: "2026-06-25"
  tasks_complete: 2
  files_created: 1
  files_modified: 2
  tests_added: 14
  tests_passing: 14
  regression_tests_passing: 209
---

# Phase 33 Plan 02: v6 Architecture Doc + Skills-Mapping Sign-off Summary

Canonical v6.0 feedback-loop architecture reference documenting ingest → store → gate → evolve → curate → observe pipeline, plus the skills-mapping.yaml `v6_ref_signoffs:` section mirroring v5 schema. Mirrors v5.0 Phase 27 `v86-pipeline-mapping.md` close-out pattern: the documentation half of the milestone close-out that gives operators and future maintainers a single canonical reference for the paradigm shift from static knowledge to feedback-driven learning.

## What Shipped

### Architecture doc (SC-4) — `skills/movie-experts/_shared/v6-feedback-loop-architecture.md` (305 lines, NEW)

**Structure** (mirrors v86-pipeline-mapping.md conventions):
- **4-line metadata header**: Source / Copyright / Last-verified (2026-06-25) / verified_date (2026-06). Copyright explicitly notes "Original Hermes Agent analytical work — no upstream external source (unlike v4/v5 `_shared/` refs)".
- **10 H2 sections** (7 CONTEXT.md content outline + 3 v86-convention footer):
  1. `## Overview & Goal / 概览与目标` — 2-paragraph bilingual prose synthesizing STATE.md v6.0 goal restatement; 4-bullet core design principles (feedback as first-class data / eval gate as only merge path / human-in-loop non-bypassable / observability as first-class surface)
  2. `## Data Flow / 反馈闭环数据流` — ASCII fenced code block showing the complete pipeline: Operator feedback (3 sources) → P28 ingest → P29 store → P30 gate → P31 evolution → P32 curator + audit → P33 stats. Each stage is a labeled box with module path + key API.
  3. `## JSON Schema Reference / JSON 结构定义` — 3 tables documenting FeedbackRecord (8 fields), OutputSnapshot (7 fields), Audit Log Entry (8 fields) with one-sentence purpose per field
  4. `## Eval-Gate Thresholds / 评估闸门阈值` — table of 4 thresholds (mean_delta=0.3, per_prompt=1.0, min_prompts=5, paired-t α=0.05) with "configurable?" and "where configured" columns; documents gate verdict decision logic + baseline cache behavior
  5. `## Human-in-Loop Boundaries / 人工审核边界` — 4 subsections: Bundled Skills (NEVER auto-apply, structural via ast-walk) / Agent-Created Skills (conditional on confidence ≥ 0.8) / Operator CLI Surface (15-command table covering P28-P33) / Audit Log Tamper-Evidence (sha256-chained)
  6. `## Module Ownership Map / 模块归属表` — 17-row table of file → purpose → shipped phase, covering every P28-P33 component
  7. `## Roadmap References / 路线图引用` — bullets cross-referencing ROADMAP.md (critical path) + REQUIREMENTS.md (26 reqs traceability) + MILESTONES.md (v6.0 archive pattern) + STATE.md (decisions table) + 33-01-SUMMARY.md (stats CLI)
  8. `## Refresh Cadence / 复核节奏` — 5 drift triggers (schema bump / threshold change / new ingest source / curator scope expansion / new observability surface) + refresh actions
  9. `## See Also` — 5 cross-ref links (v86-pipeline-mapping / dreamina-cli-baseline / glossary / RAG-INVOCATION-PATTERN / SKILL-LAYOUT)
  10. `## Source Citation` — Primary (Hermes Agent v6.0 codebase, internally authored, lists all 11 source modules) / Secondary (REQUIREMENTS.md) / Tertiary (ROADMAP.md + STATE.md)
- **Footer ownership line**: `*Owned by Phase 33 plan 33-02. Canonical v6.0 feedback-loop architecture reference. Cross-references Phase 28-32 implementations + Phase 33 plan 33-01 stats CLI. No parallel plan touches this file.*`

### skills-mapping.yaml sign-off (SC-5) — `.planning/research/v2-pipeline-design/skills-mapping.yaml` (MODIFIED, additive)

New `v6_ref_signoffs:` section appended after `v5_ref_signoffs:`. Preceded by a 9-line comment block (mirrors v5 comment block pattern) explaining:
- Covers REFS (shared markdown), NOT expert_id mappings
- v6.0 added 1 shared ref documenting feedback-loop architecture per FOUND-08
- Unlike v4/v5 refs, this v6 ref is internally authored (no upstream external source)

Single entry for `v6-feedback-loop-architecture.md` mirroring the 10-field v5 schema:
- `ref_path`: skills/movie-experts/_shared/v6-feedback-loop-architecture.md
- `expert_owner`: _shared
- `phase_added`: v6.0-phase-33
- `requirement`: OBS-01 (anchor — v6 has no INTEGRATION-* reqs per research A3)
- `verified_date`: 2026-06-25
- `source`: Hermes Agent v6.0 codebase citation (lists all 11 synthesized modules)
- `license_status`: fair_use_paraphrase (only value used across v4+v5+v6)
- `line_count`: 305
- `signed_off_by`: phase-33-doc-01
- `notes`: Explicit internally-authored status + pipeline coverage statement

### Verification tests — `tests/hermes_cli/test_curator_stats.py` (EXTENDED)

Two new test classes appended after Plan 01's classes (14 new tests):

| Class | Tests | Behavior |
|-------|-------|----------|
| `TestArchitectureDoc` | 8 | SC-4: metadata header block / H2 section count (7-11) / required section titles / footer ownership line / ASCII diagram present / no mermaid / bilingual CJK / See Also + Source Citation |
| `TestSkillsMappingV6` | 6 | SC-5: v6_ref_signoffs section present / 10 mandatory fields per entry / ref_path canonical / phase_added format / verified_date format / v5_ref_signoffs byte-intact (still 2 entries) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed `test_metadata_header_block_present` head-split logic**
- **Found during:** Task 2 GREEN state — test failed because `doc.split("\n\n", 1)[0]` returned only the H1 title line (line 1), missing the metadata block that lives between the title and the first `---` separator (lines 3-6).
- **Issue:** Original split on `\n\n` assumed the metadata block was in the first paragraph; in v86 and the v6 doc, the title is line 1, a blank line follows, then 4 metadata lines, then `---`. The first `\n\n` split point is between title and metadata.
- **Fix:** Changed split to `doc.split("\n---", 1)[0]` — captures everything before the first horizontal rule, which is the standard v86 metadata block region.
- **Files modified:** `tests/hermes_cli/test_curator_stats.py`
- **Commit:** `403c9a607`

**2. [Rule 1 - Bug] Fixed `test_minimal_h2_section_count` upper bound (9 → 11)**
- **Found during:** Task 2 GREEN state — test failed because the doc has 10 H2 sections, exceeding the `<= 9` bound.
- **Issue:** The plan's `<action>` explicitly requires 3 v86-convention footer sections (`## Refresh Cadence` + `## See Also` + `## Source Citation`) ON TOP OF the 7 CONTEXT.md content sections = 10 minimum. The original `<= 9` bound in the test contradicted the plan's own requirements.
- **Fix:** Relaxed upper bound from 9 to 11 (10 expected + 1 tolerance for a v86-style Summary section if added later). Lower bound (7) unchanged. Documented rationale in the test docstring.
- **Files modified:** `tests/hermes_cli/test_curator_stats.py`
- **Commit:** `403c9a607`

## Authentication Gates

None — pure documentation + YAML + test edits with no auth surface.

## Known Stubs

None — the architecture doc is a complete reference with no placeholder content. Every section has substantive content; the Module Ownership Map covers all 17 P28-P33 components with real file paths.

## Threat Flags

None — the plan's `<threat_model>` covered all introduced surface (T-33-07 through T-33-10). T-33-07 (v5 byte-intact) mitigated by `test_v5_byte_intact`. T-33-08 (Source Citation footer) mitigated by `test_see_also_and_source_citation_footer` + explicit internally-authored notes field. T-33-10 (mermaid drift) mitigated by `test_no_mermaid_block`. No new security-relevant surface introduced beyond what the threat model anticipated.

## TDD Gate Compliance

- [x] RED gate commit exists: `0320f3d4f test(33-02): add RED tests for architecture doc + skills-mapping sign-off` — all 14 new tests failed. TestArchitectureDoc failed with `FileNotFoundError` (doc didn't exist yet); TestSkillsMappingV6 failed with `KeyError: 'v6_ref_signoffs'` (YAML section absent).
- [x] GREEN gate commit exists: `403c9a607 feat(33-02): write v6 architecture doc + skills-mapping sign-off (SC-4/SC-5, GREEN)` — 14/14 new tests pass after writing doc + adding YAML section + fixing 2 test-bound bugs (Rule 1 deviations documented above).
- [x] REFACTOR gate: skipped (no refactor needed; GREEN implementation is clean).

## Self-Check: PASSED

**Files verified to exist:**
- [FOUND] `skills/movie-experts/_shared/v6-feedback-loop-architecture.md` (created, 305 lines)
- [FOUND] `.planning/research/v2-pipeline-design/skills-mapping.yaml` (modified — additive v6_ref_signoffs section)
- [FOUND] `tests/hermes_cli/test_curator_stats.py` (extended — TestArchitectureDoc + TestSkillsMappingV6 appended)

**Commits verified to exist:**
- [FOUND] `0320f3d4f` — `test(33-02): add RED tests for architecture doc + skills-mapping sign-off`
- [FOUND] `403c9a607` — `feat(33-02): write v6 architecture doc + skills-mapping sign-off (SC-4/SC-5, GREEN)`

**Verification commands re-run:**
- `python3 -m pytest tests/hermes_cli/test_curator_stats.py::TestArchitectureDoc tests/hermes_cli/test_curator_stats.py::TestSkillsMappingV6 -x`: 14 passed in 0.46s
- `python3 -m pytest tests/hermes_cli/test_curator_stats.py -x`: 32 passed in 0.97s (18 Plan 01 + 14 Plan 02)
- `python3 -m pytest tests/hermes_cli/test_curator_cli.py tests/agent/test_feedback_store.py tests/agent/test_audit_log.py tests/agent/evolution/ -x`: 209 passed (regression)
- `ruff check tests/hermes_cli/test_curator_stats.py`: All checks passed (PLW1514)
- FOUND-08 bundled SKILL.md changes: empty (0 files)
- v4/v5 refs byte-intact: empty (0 files — snowflake/e-konte/scamper/dreamina-cli-baseline/v86-pipeline-mapping all unchanged)
