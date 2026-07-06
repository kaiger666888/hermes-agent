# Phase 47: KIMI-COMPARISON - Context

**Gathered:** 2026-07-07
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart-discuss — design-only phase with over-determined success criteria)

<domain>
## Phase Boundary

Produce the T6 vs Kimi full-MCP-shim solution's per-dimension contrast, serving as horizontal validation of the 7 locked decisions + the argument library for the subagent form rejection. Deliverable: single markdown file `03-COMPARISON-VS-KIMI-MCP-SHIM.md` (~800-1200 lines).

Output location: `.planning/research/v10-orchestrator-design/` (sibling to Phase 44/45/46 deliverables).

</domain>

<decisions>
## Implementation Decisions

### Comparison Scope
- 7 dimensions: 协议 / dispatch / callback / state / 多 agent / 实现成本 / 稳定性
- Each dimension: T6 (Hermes MCP server + tmux dispatch + CC native MCP client) vs Kimi (full MCP shim with everything as MCP tools)
- Each dimension must produce: pros/cons for each side + selection rationale (rooted in Phase 44 decisions)

### Subagent Rejection (per SC#3)
- Cite FEATURES §11 B4.1 (subagent form rejection row)
- Document Claude Agent SDK default context-isolation limitation
- Explain why context-isolated agents are unsuitable as round-table panelists
- Cross-reference Phase 46 protocol's serial constraint + memory conflict arbitration requirements

### Microsoft Three-Layer Validation (per SC#4)
- Cite FEATURES §7.4 B7.1
- Map v10.0 T6 selection to Microsoft's layered model:
  - internal → platform-native (Hermes Python runtime)
  - tool → MCP (mcp_serve.py extension)
  - cross-platform → A2A (future-proof, deferred to v11+)
- Prove v10.0 aligns with industry consensus

### Claude's Discretion
- All structural choices at Claude's discretion
- Use Phase 44's locked decisions as validation targets
- Cite FEATURES §7.4, §10, §11 by section number
- Mirror v2.0 PRFP design-doc rigor (bilingual EN structure + 中文 prose)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.planning/research/v10-orchestrator-design/00-FIRST-PRINCIPLES.md` — root argument (Phase 44)
- `.planning/research/v10-orchestrator-design/SUMMARY.md` — locked decisions + OQ list
- `.planning/research/v10-orchestrator-design/FEATURES.md` — §7.4 Microsoft layered, §10 borrowable, §11 anti-features (B4.1 subagent rejection)
- `.planning/research/v10-orchestrator-design/ARCHITECTURE.md` — §8 anti-patterns
- `.planning/research/v10-orchestrator-design/PITFALLS.md` — context-isolation, subagent pitfalls
- `.planning/research/v10-orchestrator-design/STACK.md` — T6 协议 layer detail
- `.planning/research/v10-orchestrator-design/01-AGENT-REGISTRY-SCHEMA.md` — agent form reference
- `.planning/research/v10-orchestrator-design/02-ROUND-TABLE-PROTOCOL.md` — protocol reference (parallel-eligible sibling)

### Established Patterns
- Bilingual doc structure: EN headers + 中文 prose per CLAUDE.md
- Markdown tables for dimension comparison
- Citation cards at end for downstream docs (P50 POC-PLAN consumes this comparison)

### Integration Points
- Phase 50 POC-PLAN consumes this comparison as the "v11.0 PoC implementer's defense brief"
- Phase 51 VALIDATE cross-references this doc for SC#4 (Microsoft layered validation completeness)

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond ROADMAP SC#1-5. The 7 dimensions and the 3 mandatory citations (FEATURES §11 B4.1, FEATURES §7.4 B7.1, Claude Agent SDK context-isolation) are load-bearing.

Memory reference: `coding-agent-vs-mcp-shim.md` in user's project memory documents that v10.0 must compare existing coding-agent (tmux mode) vs Kimi Notion 架构2.0 MCP shim — this comparison should also reference that prior analysis if relevant.

</specifics>

<deferred>
## Deferred Ideas

None — design-only phase, scope tightly bounded by ROADMAP SC#1-5.

</deferred>
