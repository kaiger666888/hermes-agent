# Phase 45: AGENT-SCHEMA - Context

**Gathered:** 2026-07-06
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart-discuss — design-only phase with over-determined success criteria)

<domain>
## Phase Boundary

Define the 18-field agent YAML schema + memory-record-schema as the physical carrier for all downstream design docs (02/04/05/06) field references, with 7 load-bearing pitfall mitigations (P1/P2/P4/P5/P8/P10/P14) encoded at the field level. Deliverables:
- `01-AGENT-REGISTRY-SCHEMA.md` (design narrative)
- `agents-schema.yaml` (18-field JSON Schema)
- `memory-record-schema.yaml` (independent schema with `expires_at`/`verified_at`/`supersedes_memory_id`/`confidence`/`half_life_days`/`evidence_chain`/`evidence_operator_ids`/`status`/`confidentiality`/`scope`)

Output location: `.planning/research/v10-orchestrator-design/` (sibling to `00-FIRST-PRINCIPLES.md`).

</domain>

<decisions>
## Implementation Decisions

### Schema Design Discipline
- 18 fields locked at the ROADMAP level — no addition/removal without milestone-level decision
- 7 load-bearing pitfalls (P1/P2/P4/P5/P8/P10/P14) MUST each map to ≥1 schema field-level mitigation
- Memory schema is 2-layer: agent-profile memory (per-agent scoped) + memory-record-schema (records about agents/users over time)
- Per-agent memory tier = core / working / archival, with `memory.max_records` cap + compaction trigger
- Curator field `_memory_evolution_phase` modeled on v6.0 `_feedback_scan_phase` (dry-run-by-default + try/except isolation + execution-order contract)

### Claude's Discretion
- All implementation choices (YAML structure, JSON Schema dialect, comment style, section ordering) are at Claude's discretion
- Use Phase 44's `00-FIRST-PRINCIPLES.md` as root argument — do NOT re-derive decisions
- Cite FEATURES §10/§11, ARCHITECTURE §2/§8, PITFALLS by section number per project convention
- Mirror v2.0 PRFP design doc rigor ( bilingual EN structure + 中文 prose per CLAUDE.md )
- 15-expert transform mapping table copied from ARCHITECTURE §2

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.planning/research/v10-orchestrator-design/00-FIRST-PRINCIPLES.md` — root argument, locked decisions
- `.planning/research/v10-orchestrator-design/SUMMARY.md` — 7 locked decisions + 16 Open Questions
- `.planning/research/v10-orchestrator-design/FEATURES.md` — §10 borrowable points (B1.3/B3.5/B4.1/B7.2/B5.1)
- `.planning/research/v10-orchestrator-design/ARCHITECTURE.md` — §2 15-expert transform source, §8 anti-patterns
- `.planning/research/v10-orchestrator-design/PITFALLS.md` — load-bearing pitfalls P1/P2/P4/P5/P8/P10/P14
- `.planning/research/v2-pipeline-design/00-FIRST-PRINCIPLES.md` — design-doc structure canon

### Established Patterns
- Bilingual doc structure: EN headers/schemas + 中文 prose (per CLAUDE.md skill-file convention)
- JSON Schema with `description`, `type`, `enum`, `required` per industry standard
- YAML frontmatter discipline carried from SKILL.md convention
- v6.0 `_feedback_scan_phase` field contract template (dry-run + try/except isolation + execution order)

### Integration Points
- Downstream design docs 02/04/05/06 will cite this schema's field names directly
- v11.0 PoC implementer will consume `agents-schema.yaml` as input to Python dataclass generation
- Migration phase 49 transforms existing SKILL.md frontmatter → agent YAML per this schema

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond ROADMAP success criteria — design space is over-determined by upstream research. The 6 OQs (OQ-1/OQ-4/OQ-7/OQ-13/OQ-14/OQ-16) and 7 pitfalls (P1/P2/P4/P5/P8/P10/P14) listed in SC#5 are the load-bearing decisions; each must be either resolved in the design narrative or explicitly deferred to v11.0 with rationale.

</specifics>

<deferred>
## Deferred Ideas

None — design-only phase, scope tightly bounded by ROADMAP SC#1-5.

</deferred>
