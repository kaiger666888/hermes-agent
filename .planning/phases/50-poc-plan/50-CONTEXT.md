# Phase 50: POC-PLAN - Context

**Gathered:** 2026-07-07
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart-discuss — design-only phase with over-determined success criteria)

<domain>
## Phase Boundary

Capstone v10.0 design — aggregate the previous 6 docs' pitfall mitigations, produce the v11.0 PoC acceptance criteria checklist + workload estimate + risk register, serving as the v11.0 implementer's blueprint. Deliverable: single markdown file `05-POC-PLAN.md` (~800-1200 lines).

Output location: `.planning/research/v10-orchestrator-design/` (sibling to all prior design docs).

</domain>

<decisions>
## Implementation Decisions

### PoC Scope (per SC#2)
- Vertical slice: 1 creative phase + 1 infra phase
- Both selections must have explicit rationale (not arbitrary picks)
- Suggested: creative = storyboard/screenplay draft (Decision 3 D2 storyboard); infra = agent registry + 1 round table invocation

### Acceptance Criteria (per SC#3)
- 7 categories, each 1-3 day estimate:
  1. Fitness battery design (cite PITFALLS §P8)
  2. Latency SLO (p95 < 500ms for mem0 scoped retrieval)
  3. Bias canary (curator `_memory_evolution_phase` hallucination detection)
  4. Compaction pass (`memory.max_records` trigger)
  5. Threshold tuning (initial defaults + tuning path)
  6. Dry-run-first invariant (curator defaults to dry-run)
  7. Schema migration dry-run (per Phase 49 §4)

### Risk Register (per SC#4)
- 7 load-bearing pitfalls (P1/P2/P4/P5/P6/P7/P8) × PoC deferral evaluation
- Each pitfall: `must-fix-in-PoC` vs `defer-with-monitoring` verdict + rationale

### PoC Implementation Path (per SC#5)
- Sequence: fitness battery → schema migration dry-run → bias canary
- Reference STACK §7 token cost estimate (~550K per pipeline run)

### Claude's Discretion
- All structural choices at Claude's discretion
- Aggregate content from prior 6 docs (00-FIRST-PRINCIPLES, 01-AGENT-REGISTRY-SCHEMA, 02-ROUND-TABLE-PROTOCOL, 03-COMPARISON-VS-KIMI-MCP-SHIM, 04-MIGRATION-PATH, 06-CROSS-REPO-IMPACT)
- Mirror v2.0 PRFP design-doc rigor (bilingual)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets (all prior v10.0 design docs)
- `.planning/research/v10-orchestrator-design/00-FIRST-PRINCIPLES.md` (Phase 44 — root)
- `.planning/research/v10-orchestrator-design/01-AGENT-REGISTRY-SCHEMA.md` + schema yamls (Phase 45 — schemas)
- `.planning/research/v10-orchestrator-design/02-ROUND-TABLE-PROTOCOL.md` + state schema (Phase 46 — protocol)
- `.planning/research/v10-orchestrator-design/03-COMPARISON-VS-KIMI-MCP-SHIM.md` (Phase 47 — defense brief)
- `.planning/research/v10-orchestrator-design/04-MIGRATION-PATH.md` (Phase 49 — migration rules)
- `.planning/research/v10-orchestrator-design/06-CROSS-REPO-IMPACT.md` (Phase 48 — sync strategy)
- `.planning/research/v10-orchestrator-design/PITFALLS.md` (P1/P2/P4/P5/P6/P7/P8 — load-bearing)
- `.planning/research/v10-orchestrator-design/STACK.md` (§7 token cost)
- `.planning/research/v10-orchestrator-design/SUMMARY.md`

### Established Patterns
- Bilingual doc structure: EN headers + 中文 prose
- Acceptance criteria with workload estimates (1-3 days each)
- Risk register tables with verdict columns
- Implementation path diagrams with sequence rationale

### Integration Points
- Phase 51 VALIDATE consumes this for milestone audit (cross-doc lint + completeness)
- v11.0 implementer (future) consumes this as direct blueprint

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond ROADMAP SC#1-5. The PoC vertical slice composition, 7 acceptance categories, 7 risk register rows, and implementation path are all enumerated. Each acceptance item has a 1-3 day estimate cap.

Memory reference: `v6-self-evolution-milestone.md` documents v6.0 fitness battery precedents; the PoC fitness battery design should leverage v6.0 patterns.

</specifics>

<deferred>
## Deferred Ideas

None — design-only phase, scope tightly bounded by ROADMAP SC#1-5.

</deferred>
