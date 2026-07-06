# Phase 48: CROSS-REPO-IMPACT - Context

**Gathered:** 2026-07-07
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart-discuss — design-only phase with over-determined success criteria)

<domain>
## Phase Boundary

Define the 3-location sync strategy (hermes-agent repo / kais-hermes-skills repo / `~/.hermes/`) + Option B (v11.0 PoC filter routing) vs physical partition (v12+ per-agent workspace) migration trigger conditions. Deliverable: single markdown file `06-CROSS-REPO-IMPACT.md` (~800-1200 lines).

Output location: `.planning/research/v10-orchestrator-design/` (sibling to prior design docs).

</domain>

<decisions>
## Implementation Decisions

### Sync Strategy (per SC#2)
- 3 locations: hermes-agent repo / kais-hermes-skills repo / `~/.hermes/`
- Per location document: stored content / write authority / sync direction / lineage relationships
- Example lineage: agent YAML in `~/.hermes/agents/` traces back to kais-hermes-skills SKILL.md frontmatter

### Option B vs Physical Partition (per SC#3)
- Option B (v11.0 PoC): single mem0 backend + `agent_id` filter routing
- Physical Partition (v12+): each agent gets own workspace
- Migration trigger conditions: scale threshold / latency threshold / when to switch
- Resolves OQ-12, prevents P3/P12

### Round Table State Path (per SC#4)
- Per-project state path: `.runtime/{slug}/round_tables/`
- Reference ARCHITECTURE §5.1

### Project Slug Stability (per SC#5)
- Short-term: accept breakage on rename/move
- Long-term: `.hermes/project.id` stable ID mechanism
- Resolves OQ-6

### Claude's Discretion
- All structural choices at Claude's discretion
- Cite Phase 44 locked decisions as validation targets
- Cite ARCHITECTURE §5.1, FEATURES §10/§11, PITFALLS (P3/P12), SUMMARY (OQ-6/OQ-12) by section number
- Mirror v2.0 PRFP design-doc rigor (bilingual EN structure + 中文 prose)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.planning/research/v10-orchestrator-design/00-FIRST-PRINCIPLES.md` — root argument
- `.planning/research/v10-orchestrator-design/01-AGENT-REGISTRY-SCHEMA.md` — agent schema
- `.planning/research/v10-orchestrator-design/02-ROUND-TABLE-PROTOCOL.md` — protocol
- `.planning/research/v10-orchestrator-design/03-COMPARISON-VS-KIMI-MCP-SHIM.md` — comparison (parallel-eligible sibling)
- `.planning/research/v10-orchestrator-design/ARCHITECTURE.md` — §5.1 round-table state storage, §8 anti-patterns
- `.planning/research/v10-orchestrator-design/PITFALLS.md` — P3/P12
- `.planning/research/v10-orchestrator-design/SUMMARY.md` — OQ-6/OQ-12

### Established Patterns
- Bilingual doc structure: EN headers + 中文 prose per CLAUDE.md
- Decision tables for migration triggers
- Citation cards at end for downstream docs (P49 migration + P50 POC-PLAN consume this)

### Integration Points
- Phase 49 MIGRATION-PATH consumes this for 3-location sync rules
- Phase 50 POC-PLAN consumes Option B definition + trigger conditions
- Phase 51 VALIDATE cross-doc lint checks §reference integrity

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond ROADMAP SC#1-5. The 3 locations, Option B vs physical partition framing, round-table state path, and project slug stability policy are all enumerated in the SCs.

Memory reference: `kais-movie-agent-v5-hermes-native-migration.md` documents that v5.0 migrated Node.js V8.6 to hermes-agent skill + 3 plugins, and `~/.hermes/` is the canonical state root per CLAUDE.md.

</specifics>

<deferred>
## Deferred Ideas

None — design-only phase, scope tightly bounded by ROADMAP SC#1-5.

</deferred>
