# Phase 51: VALIDATE - Context

**Gathered:** 2026-07-07
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart-discuss — design-only close-out phase with over-determined success criteria)

<domain>
## Phase Boundary

v10.0 milestone close-out — produce cross-doc consistency lint script (VALIDATE-02) + milestone audit report (VALIDATE-01). Verify 9/9 reqs satisfied + 7 design docs cross-reference consistent + 16 Open Questions resolved or explicitly deferred. Deliverables:
- `scripts/v10-consistency-check.py` (Python lint script)
- `.planning/milestones/v10.0-MILESTONE-AUDIT.md` (milestone audit report)

Strictly LAST — analog to v9.0 Phase 43 / v5.0 Phase 27 close-out pattern.

</domain>

<decisions>
## Implementation Decisions

### Lint Script Scope (per SC#1, SC#2 — VALIDATE-02)
- Path: `scripts/v10-consistency-check.py`
- Checks (4 dimensions):
  1. **Terminology consistency**: agent / skill / round table / panel / turn across 7 design docs
  2. **Schema reference consistency**: `agents-schema.yaml` field names match design docs
  3. **Decision number reference consistency**: 决策 1-7 described consistently across docs
  4. **MCP tool naming consistency**: STACK form (no prefix) everywhere
- Run script on all 7 design docs, expect zero ERRORs (WARNINGs acceptable, list in audit)

### Milestone Audit Report (per SC#3, SC#4, SC#5 — VALIDATE-01)
- Path: `.planning/milestones/v10.0-MILESTONE-AUDIT.md`
- 9/9 reqs cross-check (each req → its phase SUMMARY)
- 7 design docs cross-reference consistency check
- 16 OQs (OQ-1..OQ-16) resolution/defer status
- 7 load-bearing pitfalls field-level mitigation check (in Phases 45/46/50)
- 4 research citation chain completeness
- Final milestone-level verdict: PASS / tech_debt / FAIL with evidence pointers

### Claude's Discretion
- All structural choices at Claude's discretion
- The lint script must be Python 3.11+ compatible (per project runtime)
- Use stdlib only (no external deps) for the lint script for portability
- Audit report follows v9.0 / v5.0 close-out template structure

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets — All 7 v10.0 Design Docs
- `.planning/research/v10-orchestrator-design/00-FIRST-PRINCIPLES.md` (Phase 44)
- `.planning/research/v10-orchestrator-design/01-AGENT-REGISTRY-SCHEMA.md` + `agents-schema.yaml` + `memory-record-schema.yaml` (Phase 45)
- `.planning/research/v10-orchestrator-design/02-ROUND-TABLE-PROTOCOL.md` + `round-table-state-schema.yaml` (Phase 46)
- `.planning/research/v10-orchestrator-design/03-COMPARISON-VS-KIMI-MCP-SHIM.md` (Phase 47)
- `.planning/research/v10-orchestrator-design/04-MIGRATION-PATH.md` (Phase 49)
- `.planning/research/v10-orchestrator-design/05-POC-PLAN.md` (Phase 50)
- `.planning/research/v10-orchestrator-design/06-CROSS-REPO-IMPACT.md` (Phase 48)

### Research Source Docs (citation chain to verify)
- `.planning/research/v10-orchestrator-design/STACK.md`
- `.planning/research/v10-orchestrator-design/FEATURES.md`
- `.planning/research/v10-orchestrator-design/ARCHITECTURE.md`
- `.planning/research/v10-orchestrator-design/PITFALLS.md`
- `.planning/research/v10-orchestrator-design/SUMMARY.md`

### Project Conventions
- Python 3.11+ (per CLAUDE.md)
- snake_case for modules/functions
- Type hints required on public functions
- `encoding="utf-8"` on every `open()` (Ruff PLW1514)
- Bilingual audit report (EN structure + 中文 prose)
- v9.0 Phase 43 audit template at `.planning/milestones/v9.0-MILESTONE-AUDIT.md` (precedent)

### Integration Points
- v11.0 PoC implementer consumes the lint script for CI integration
- `gsd-audit-milestone` skill may consume the audit report
- Project memory entry will be added upon milestone completion

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond ROADMAP SC#1-5. The 4 lint dimensions, 5 audit checks, and PASS/tech_debt/FAIL verdict format are all enumerated.

Memory precedent: `v9.0-MIGRATION-REPORT.md` and earlier milestone close-outs in `.planning/milestones/` provide structural templates. Phase 51 audit should mirror v9.0 close-out rigor.

</specifics>

<deferred>
## Deferred Ideas

None — close-out phase, scope tightly bounded by ROADMAP SC#1-5.

</deferred>
