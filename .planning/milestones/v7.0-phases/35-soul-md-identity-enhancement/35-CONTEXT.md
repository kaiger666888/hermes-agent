# Phase 35: SOUL.md Identity Enhancement - Context

**Gathered:** 2026-06-25
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart-discuss — infrastructure-phase classification)

<domain>
## Phase Boundary

Integrate openclaw's AIGC routing intelligence from `~/.openclaw/SOUL.md` (24 lines, 4 routing categories) into `~/.hermes/SOUL.md` (currently 0 bytes — empty) non-destructively. The integration must:

1. Preserve original hermes-default SOUL.md content byte-for-byte (trivially satisfied since hermes default is empty — any addition is additive)
2. Tag openclaw-origin rules with source attribution ("openclaw 迁移" + date 2026-06-25)
3. Adapt openclaw trigger modes (regex-based, MCP routed) to hermes invocation patterns
4. Backup original openclaw SOUL.md verbatim at `~/.hermes/SOUL.md.openclaw-backup-2026-06-25`
5. Write a transformation note under `.planning/phases/35-soul-md-identity-enhancement/` recording each rule's fate (integrated / adapted / dropped)

**Source files (read-only input):**
- `~/.openclaw/SOUL.md` — 24 lines, contains:
  - Identity statement (Kais AIGC Director 主控 Agent, "手"/"脑"分工)
  - 4 routing categories:
    - 即时执行命令 (immediate-execution): draw/video/tts/run/status/queue → local_skill
    - 认知类命令 (cognitive): plan/规划/剧本/分镜 → mcp:hermes_plan etc. (5 MCP routes)
    - 专家管理命令: /expert → local_skill:expert_manager
    - 默认: simple chat → local LLM (GLM-4-flash)

**Target outputs:**
- `~/.hermes/SOUL.md` (operator-state, additive integration)
- `~/.hermes/SOUL.md.openclaw-backup-2026-06-25` (operator-state, verbatim backup)
- `.planning/phases/35-soul-md-identity-enhancement/35-01-TRANSFORMATION-NOTE.md` (repo-commit, audit trail)

Out of scope: Hermes core code; modifying any plugin; touching `~/.openclaw/` source files.

</domain>

<decisions>
## Implementation Decisions

### Smart Discuss Auto-Accept (Infrastructure Classification)

Phase 35 was classified as **infrastructure** per autonomous-smart-discuss criteria (migration keywords, technical SCs, no novel user-facing behavior). All implementation choices at Claude's discretion within ROADMAP SC constraints.

### Key Design Decisions (deferred to plan-phase research + planner judgment)

1. **Source attribution tagging:** Each integrated rule gets a `> **Source:** openclaw 迁移 (2026-06-25)` annotation or equivalent inline marker. The integrated section as a whole gets an H2 header like `## openclaw 迁移规则 (Source: openclaw SOUL.md, migrated 2026-06-25)`.

2. **Trigger mode adaptation:** openclaw used regex-based routing with `mcp:hermes_*` targets (assumes MCP server mode). Hermes-agent's invocation modes are slash-commands (`/skill`, `/expert`) or natural language with skill-discovery. Plan-phase must decide how to express each route:
   - **Option A:** Keep regex patterns verbatim, rewrite MCP targets to hermes equivalents (`mcp:hermes_plan` → `/skill screenplay` or similar)
   - **Option B:** Rewrite as natural-language trigger descriptions (more hermes-native but loses precision)
   - **Option C:** Hybrid — regex patterns as comments, natural-language descriptions as primary

3. **Backup file format:** Verbatim copy of `~/.openclaw/SOUL.md` to `~/.hermes/SOUL.md.openclaw-backup-2026-06-25`. Use `cp -p` to preserve mtime. No transformation.

4. **Transformation note structure:** Per SOUL-03, the note MUST record where each openclaw rule landed:
   - Identity statement → integrated / adapted / dropped (which?)
   - 6 immediate-execution regex patterns → integrated / adapted / dropped (each?)
   - 5 cognitive MCP routes → integrated / adapted / dropped (each?)
   - 1 expert management command → integrated / adapted / dropped
   - 1 default route → integrated / adapted / dropped

5. **GLM-4-flash reference in default route:** openclaw's default routes simple chat to local GLM-4-flash. Hermes doesn't have this concept natively (uses configured model). Decision needed: drop the reference, genericize to "local LLM", or keep as-is with adaptation note.

### Claude's Discretion

All remaining implementation choices (exact wording of integrated rules, header structure, whether to use a fenced block for the openclaw section, etc.) deferred to plan-phase.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- `~/.hermes/SOUL.md` (currently 0 bytes) — no hermes-default content to preserve; SC #3 trivially satisfied
- `~/.openclaw/SOUL.md` — 24-line source file with 4 routing categories

### Established Patterns

- Hermes SOUL.md is operator-state (not repo-tracked) — loaded by hermes-agent at conversation start
- SOUL.md is markdown — no YAML frontmatter expected (unlike SKILL.md)
- Transformation note (repo-commit) provides audit trail for operator-state changes — this pattern is unique to v7.0 Phase 35 (no prior milestone precedent)

### Integration Points

- `~/.hermes/SOUL.md` is auto-loaded by hermes-agent runtime — no code changes needed to make the integrated rules take effect (just file content)
- Hermes MCP server is exposed via `mcp_serve.py` — openclaw's `mcp:hermes_*` references may need translation to actual hermes MCP tool names (research at plan time)

</code_context>

<specifics>
## Specific Ideas

- SC #3 requires explicit source tagging per rule — this is the load-bearing audit constraint
- SC #4 requires a transformation note — this is the repo-commit deliverable
- The "手"/"脑" identity framing (openclaw=手, hermes=脑) doesn't translate cleanly to single-agent hermes model — likely needs adaptation or dropping

</specifics>

<deferred>
## Deferred Ideas

- Multi-profile mechanism (openclaw had separate SOULs per agent profile) — explicitly OUT of v7.0 scope per ROADMAP
- ACP / acp-router references in SOUL body — not in v7.0 scope
- openclaw's `mcp:hermes_*` MCP tool names — actual hermes MCP tools may differ; mapping at plan time

</deferred>
