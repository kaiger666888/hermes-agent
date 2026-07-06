# Phase 46: ROUND-TABLE-PROTOCOL - Context

**Gathered:** 2026-07-06
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart-discuss — design-only phase with over-determined success criteria)

<domain>
## Phase Boundary

Define the round table protocol (turn lifecycle / conflict arbitration / state schema) consuming Phase 45's agent schema, resolving memory conflicts, and enforcing serial execution to remain compatible with GLM 4-key rotation. Deliverables:
- `02-ROUND-TABLE-PROTOCOL.md` (design narrative)
- `round-table-state-schema.yaml` (JSON Schema for round-table session state)

Output location: `.planning/research/v10-orchestrator-design/` (sibling to `00-FIRST-PRINCIPLES.md`, `01-AGENT-REGISTRY-SCHEMA.md`).

</domain>

<decisions>
## Implementation Decisions

### Protocol Design Discipline
- Consume Phase 45 agent schema fields directly (no re-derivation)
- Turn lifecycle: `round_table_open` → turn N → `submit_round_table_result` (atomic)
- `turn_order`: default round-robin + pluggable strategy (resolves OQ-2)
- `round_id`: CC self-generates UUID (resolves OQ-11)
- Memory conflict arbitration: comparator LLM pass + scope precedence (session > project > global) + confidence-weighted voting + conflict log (resolves OQ-15, prevents P7)
- Serial execution mandatory: 1 panelist 1 turn sequential `await` — references `~/.claude/projects/-data-workspace-hermes-agent/memory/feedback-glm-overload-reduce-concurrency.md` (global concurrency==1 policy, resolves OQ-8)
- MCP tool naming: no prefix, aligns with existing 9 messaging tools (per STACK §3.2, resolves OQ-9)

### Borrowable Points Coverage (per SC#5)
- B1.4 / B2.1 / B2.3 / B4.2 / B6.1 / B7.3 / B8.2 — each must be explicitly addressed

### Claude's Discretion
- All implementation choices (YAML structure, narrative section ordering, JSON Schema dialect) at Claude's discretion
- Use Phase 44 `00-FIRST-PRINCIPLES.md` as root argument
- Use Phase 45 schemas (agents-schema.yaml, memory-record-schema.yaml) as field reference
- Cite FEATURES §10/§11, ARCHITECTURE §2/§8, PITFALLS, STACK §3.2 by section number
- Mirror v2.0 PRFP design doc rigor (bilingual EN structure + 中文 prose per CLAUDE.md)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.planning/research/v10-orchestrator-design/00-FIRST-PRINCIPLES.md` — root argument (Phase 44)
- `.planning/research/v10-orchestrator-design/01-AGENT-REGISTRY-SCHEMA.md` — agent schema narrative (Phase 45)
- `.planning/research/v10-orchestrator-design/agents-schema.yaml` — 18-field schema (Phase 45)
- `.planning/research/v10-orchestrator-design/memory-record-schema.yaml` — 10-field memory schema (Phase 45)
- `.planning/research/v10-orchestrator-design/STACK.md` — §3.2 MCP tool naming convention
- `.planning/research/v10-orchestrator-design/FEATURES.md` — §10 borrowable points (B1.4/B2.1/B2.3/B4.2/B6.1/B7.3/B8.2)
- `.planning/research/v10-orchestrator-design/PITFALLS.md` — P7 memory conflict, related pitfalls
- `~/.claude/projects/-data-workspace-hermes-agent/memory/feedback-glm-overload-reduce-concurrency.md` — global concurrency==1 policy

### Established Patterns
- Bilingual doc structure: EN headers/schemas + 中文 prose
- JSON Schema Draft 2020-12 with `$schema`, `$id`, `description`, `type`, `required`, `additionalProperties: false`, `properties`
- camelCase JSON Schema keywords (lesson from Phase 45 verification — never snake_case)
- v6.0 `_feedback_scan_phase` style for any curator/mediator phase contract

### Integration Points
- Phase 49 migration will reference this protocol's state schema for runtime data structures
- Phase 50 PoC plan consumes this protocol as the runtime contract
- Phase 47 (KIMI-COMPARISON) will compare this protocol vs Kimi's MCP shim approach (parallel-eligible)

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond ROADMAP success criteria. SC#1-5 enumerate exact deliverable filenames, lifecycle invariants, conflict arbitration components, serial constraint citation, and MCP tool naming convention. Each OQ (OQ-2/OQ-8/OQ-9/OQ-11/OQ-15) listed in SC#2-5 is load-bearing and must be either resolved in the design narrative or explicitly deferred to v11.0.

Critical reference: MEMORY.md `feedback-glm-overload-reduce-concurrency.md` documents that global concurrency==1 is by design (after 5→3→1 deprecation cycle) — DO NOT propose parallel panelist execution. The serial constraint is non-negotiable.

</specifics>

<deferred>
## Deferred Ideas

None — design-only phase, scope tightly bounded by ROADMAP SC#1-5.

</deferred>
