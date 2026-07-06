# Phase 49: MIGRATION-PATH - Context

**Gathered:** 2026-07-07
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart-discuss — design-only phase with over-determined success criteria)

<domain>
## Phase Boundary

Define the Python runner incremental migration plan: 15 expert transform rules from SKILL frontmatter to agent YAML + memory schema migration from v6.0 FeedbackStore to new memory-record-schema + retained-phases allowlist. Deliverable: single markdown file `04-MIGRATION-PATH.md` (~800-1200 lines).

Output location: `.planning/research/v10-orchestrator-design/` (sibling to prior design docs).

</domain>

<decisions>
## Implementation Decisions

### Transform Rules (per SC#2)
- 15 experts × 5 fields each = 75 transform cells
- Each cell documents: SKILL frontmatter field → agent YAML field + default + edge cases
- Source experts: ARCHITECTURE §2 15-expert table (copied verbatim — FOUND-08 preserved)

### Skill Fallback Mechanism (per SC#3)
- `default_invocation: skill_fallback → mcp_tool`
- Agent prefers MCP tool; on failure falls back to SKILL form
- Document transition path + failure modes

### Memory Schema Migration (per SC#4)
- From: v6.0 FeedbackStore JSONL
- To: new memory-record-schema (defined in Phase 45)
- Include `schema_version` field for forward compatibility
- Include dry-run migration mode (prevents P14 silent drops)

### Retained-Phases Allowlist (per SC#5)
- `run_python_phase` only accepts Steps 0/6.5/7/10/11/12/15
- Allowlist location: `round-table-schema.yaml` (Phase 46 deliverable)
- Resolves OQ-10
- Plus: legacy v7.0 mem0 `agent_id=hermes` memory policy (resolves OQ-3)

### Claude's Discretion
- All structural choices at Claude's discretion
- Cite Phase 45 schema fields (no redefinition)
- Cite Phase 46 round-table schema (no redefinition)
- Cite ARCHITECTURE §2 for 15-expert table
- Mirror v2.0 PRFP design-doc rigor (bilingual)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.planning/research/v10-orchestrator-design/00-FIRST-PRINCIPLES.md` (Phase 44 root)
- `.planning/research/v10-orchestrator-design/01-AGENT-REGISTRY-SCHEMA.md` + `agents-schema.yaml` (Phase 45 — 18-field target schema)
- `.planning/research/v10-orchestrator-design/memory-record-schema.yaml` (Phase 45 — target memory schema)
- `.planning/research/v10-orchestrator-design/02-ROUND-TABLE-PROTOCOL.md` + `round-table-state-schema.yaml` (Phase 46 — allowlist location)
- `.planning/research/v10-orchestrator-design/ARCHITECTURE.md` (§2 15-expert table — copy verbatim)
- `.planning/research/v10-orchestrator-design/PITFALLS.md` (P14)
- `.planning/research/v10-orchestrator-design/SUMMARY.md` (OQ-3, OQ-10)

### Established Patterns
- Bilingual doc structure: EN headers + 中文 prose per CLAUDE.md
- Transform rule tables with explicit edge cases
- v6.0 `_feedback_scan_phase` migration precedent (per CLAUDE.md memory)

### Integration Points
- Phase 50 POC-PLAN consumes this for v11.0 PoC scope
- Phase 51 VALIDATE cross-doc lint checks transform rule completeness

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond ROADMAP SC#1-5. The 5 success criteria enumerate exact deliverable content (file existence, transform rule table dimensions, fallback mechanism, memory migration plan with dry-run + schema_version, retained-phases allowlist + legacy mem0 policy).

Memory reference: `v6-self-evolution-milestone.md` documents v6.0 FeedbackStore as the source memory schema being migrated.

</specifics>

<deferred>
## Deferred Ideas

None — design-only phase, scope tightly bounded by ROADMAP SC#1-5.

</deferred>
