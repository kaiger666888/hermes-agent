# Phase 37: Validation & Migration Report - Context

**Gathered:** 2026-06-25
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart-discuss — infrastructure-phase classification)

<domain>
## Phase Boundary

Benchmark-verify Phase 34-36 deliverables are regression-free, then produce canonical `.planning/milestones/v7.0-MIGRATION-REPORT.md` documenting all transform decisions + explicitly skipped items with rationale. Ready for v8.0 planning reference.

**Inputs (read-only — Phase 34-36 outputs):**
- Phase 34 deliverables:
  - `skills/autonomous-ai-agents/coding-agent/SKILL.md`
  - `skills/autonomous-ai-agents/tmux-agents/SKILL.md`
  - `skills/autonomous-ai-agents/COEXISTENCE.md`
- Phase 35 deliverables:
  - `~/.hermes/SOUL.md` (integrated)
  - `~/.hermes/SOUL.md.openclaw-backup-2026-06-25`
  - `.planning/phases/35-soul-md-identity-enhancement/35-01-TRANSFORMATION-NOTE.md`
- Phase 36 deliverables:
  - `~/.hermes/memories/USER.md`
  - `plugins/memory/mem0/scripts/batch_ingest.py`
  - `plugins/memory/mem0/scripts/spot_check.py`
  - `.planning/phases/36-memory-ingestion-user-md-133-md-mem0/36-01-INGESTION-NOTE.md`
- Phase 34-36 VERIFICATION.md reports (human_needed items)

**Target outputs (repo-commit):**
- `.planning/milestones/v7.0-MIGRATION-REPORT.md` (canonical close-out artifact — REQUIRED by SC #3)

Out of scope: new migrations; touching Phase 34-36 deliverables; Hermes core code.

</domain>

<decisions>
## Implementation Decisions

### Smart Discuss Auto-Accept (Infrastructure Classification)

Phase 37 was classified as **infrastructure** (validation + report writing, no novel user-facing behavior). All implementation at Claude's discretion within ROADMAP SC constraints.

### Key Design Decisions

1. **VALIDATE-01 (skill benchmark):**
   - "Benchmark prompt" = a prompt that triggers the skill's delegation chain
   - coding-agent: a prompt like "use claude code to fix a typo in README.md" — verify the skill is discoverable + delegation command form is documented (cannot actually spawn tmux session in this validation — would need live tmux/agent binaries)
   - tmux-agents: a prompt like "spawn a coding agent named test-session to do X" — verify skill discoverability + spawn form is documented
   - **Limitation acknowledgment:** End-to-end live execution requires operator environment (tmux installed, claude/codex/opencode binaries available). Phase 37 validates structural preconditions + invocation forms + skill discoverability — actual tmux spawn is operator smoke-test.

2. **VALIDATE-02 (SOUL.md routing):**
   - Test prompts per category:
     - Immediate: "draw a cat" / "tts hello world" — verify routing rule fires (structural check: rule present + trigger pattern matches)
     - Cognitive: "帮我设计剧本" / "记住这个角色" — verify rule present
     - Default: "今天天气怎么样" — verify default route
   - **Limitation acknowledgment:** Live routing behavior requires hermes-agent runtime conversation. Phase 37 validates rule completeness + structural correctness — live runtime test is operator smoke-test (matches Phase 35's human_needed items).

3. **VALIDATE-03 (migration report):**
   - Canonical artifact at `.planning/milestones/v7.0-MIGRATION-REPORT.md`
   - Required sections:
     - Executive Summary (what v7.0 accomplished)
     - Transform Decisions (skill frontmatter mapping, prerequisite mapping, SOUL rule adaptation, memory ingestion strategy — each with rationale)
     - Explicitly Skipped Items (feishu-* / acp-router / models.json / sessions / multi-profile — each with one-line rationale)
     - Operator Action Items (MEM0_API_KEY config + live mem0 ingestion + SOUL.md routing smoke-test + skill invocation smoke-test)
     - Phase-by-Phase Summary (34/35/36 with verification status)
     - Forward-Looking Notes for v8.0

### Claude's Discretion

- Exact benchmark prompt phrasing (within the documented trigger patterns)
- Whether to include a "lessons learned" section
- Report length/depth (target: comprehensive but not bloated — 200-400 lines)
- Whether to suggest v8.0 priorities (likely yes, since deferred items exist)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- All Phase 34-36 deliverables (listed in domain section)
- `.planning/milestones/v6.0-MILESTONE-AUDIT.md` — reference for audit-style writing
- `.planning/milestones/v5.0-*` — prior migration report examples (if any)

### Established Patterns

- v3-v6 milestones wrote audit/report to `.planning/milestones/v{X}-MILESTONE-AUDIT.md`
- v7.0 file name is `v7.0-MIGRATION-REPORT.md` (per ROADMAP SC #3 — slightly different from prior milestone-audit naming, reflects the migration-not-build nature of v7.0)
- Reports use markdown with TOC, sectioned H2s, tables for transform decisions + skipped items

### Integration Points

- v7.0-MIGRATION-REPORT.md is referenced by Phase 37 SC #3 verbatim
- This artifact will be the primary input for v8.0 milestone planning (operator references it to decide what to tackle next)

</code_context>

<specifics>
## Specific Ideas

- VALIDATE-01 + VALIDATE-02 are partially blocking on operator runtime smoke-tests — the report should be honest about this and explicitly hand off smoke-testing to operator with documented test commands
- The "explicitly skipped items" section is load-bearing for preventing scope-creep reversal in v8.0 — each skipped item gets a one-line rationale (not just a name)

</specifics>

<deferred>
## Deferred Ideas

- Live end-to-end benchmark (tmux spawn, hermes conversation) — operator smoke-test
- Cross-AI peer review of the migration report (operator runs /gsd:review if desired)
- v8.0 milestone planning (separate workflow)

</deferred>
