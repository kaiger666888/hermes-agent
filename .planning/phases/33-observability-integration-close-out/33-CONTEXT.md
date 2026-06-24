# Phase 33: Observability + Integration Close-out - Context

**Gathered:** 2026-06-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Operators can observe feedback-driven learning health via `hermes curator stats [skill_id]` (per-skill) and `hermes curator stats --all` (cross-skill + source breakdown). The v6.0 milestone ships:
1. Canonical architecture doc `_shared/v6-feedback-loop-architecture.md` (mirrors v5.0 `v86-pipeline-mapping.md` pattern)
2. `skills-mapping.yaml` new `v6_ref_signoffs:` section
3. `skills/movie-experts/README.md` corpus tree update + glossary 4 new bilingual entries
4. Milestone-wide FOUND-08 preservation check + v5/v4 refs byte-intact check

Covers requirements OBS-01, OBS-02, OBS-03 (+ integration close-out deliverables, no separate REQ-IDs). **Hermes-core touch: Mixed** — extends `hermes_cli/curator.py` with `stats` subcommand; writes new `_shared/` ref; modifies `skills-mapping.yaml` + README + glossary. No bundled SKILL.md or v4/v5 ref bytes changed.

**Depends on:** Phase 28-32 all complete (needs full feedback loop running to surface meaningful stats). MUST run last per ROADMAP critical path.

</domain>

<decisions>
## Implementation Decisions

### Stats Output Format (OBS-01..03)
- **Plain-text tables via `rich` library** (already in stack at `rich==14.3.3` per `pyproject.toml`). Use `rich.table.Table` for:
  - Per-skill dashboard (OBS-01): feedback counts bucketed by verdict (good/needs_work/bad), patch history table, eval score trend sparkline
  - Cross-skill view (OBS-02): top-N skills by negative feedback volume, top-N patches by score uplift, zero-feedback skills list
  - Source breakdown (OBS-03): per-source verdict distribution table
- `--json` flag emits machine-readable JSON for scripted pipelines.
- Raw plain text rejected (too dense for human reading). HTML dashboard out of scope (P33 is CLI-only observability).

### Eval Score Trend Depth (OBS-01)
- **Default last N=10 runs** (configurable via `--runs N`). History derived from `audit-log` entries (where action=apply AND eval_score field populated).
- If fewer than N runs exist: show existing entries + "need more data for trend" footer.
- Trend visualization: `rich.table.Table` with columns [Date | Verdict | Mean Δ | Per-prompt Max Drop | Commit SHA], plus a textual sparkline using unicode block characters (▁▂▃▄▅▆▇█) for mean_delta.

### Architecture Doc Structure (SC-4)
- **Mirror v5.0 `v86-pipeline-mapping.md` pattern** with 7 sections:
  1. **Overview & Goal** — what the feedback loop achieves
  2. **Data Flow Diagram** — ASCII diagram of ingest → store → gate → evolve → curate → observe
  3. **JSON Schema Reference** — FeedbackRecord, PatchRecord, audit entry
  4. **Eval-Gate Thresholds** — δ=0.3, per_prompt=1.0, min_prompts=5, configurable
  5. **Human-in-Loop Boundaries** — bundled NEVER auto-apply (CURATE-05); agent-created conditional
  6. **Module Ownership Map** — file:purpose table for P28-32 components
  7. **Roadmap References** — cross-refs to ROADMAP.md, REQUIREMENTS.md, MILESTONES.md
- Bilingual: English body + Chinese section headers (per CLAUDE.md convention `### <EN> / <中文>`).
- Write to `skills/movie-experts/_shared/v6-feedback-loop-architecture.md`.

### README + Glossary Close-out (SC-6)
- **Claude's discretion based on P28-32 deliverables.** Glossary 4 new terms:
  1. `### Feedback Ingestion / 知识反馈采集` — multi-source feedback intake into normalized schema (P28)
  2. `### Knowledge Evolution / 知识进化` — LLM aggregation + EVOL-02 diff generation pipeline (P31/32)
  3. `### Eval Gate / 评估闸门` — patch-vs-baseline MT-Bench position-swap harness (P30)
  4. `### Curator Proposal / 策展提案` — Curator's auto-trigger of EVOL pipeline + audit trail (P32)
- Each entry: H3 bilingual header + 2-3 sentence explanation + cross-reference to architecture doc.
- README corpus tree (`skills/movie-experts/README.md`) updated to list `_shared/v6-feedback-loop-architecture.md` alongside existing v4/v5 refs.

### Curator CLI Extension Surface

```bash
# Per-skill dashboard
hermes curator stats [skill_id] [--runs N] [--json]

# Cross-skill view (top-N by negative feedback, zero-feedback list)
hermes curator stats --all [--top N] [--json]

# Source breakdown (verdict distribution by source)
hermes curator stats --by-source [--skill <id>] [--json]
```

- `stats` extends existing `hermes_cli/curator.py:register_cli` pattern (matches P32 `queue`/`approve`/`reject`/`audit-log` subparsers).

### Claude's Discretion
- Sparkline rendering — use unicode block characters (`▁▂▃▄▅▆▇█`) or rich's built-in `BarColumn`. Recommend rich's BarColumn for consistency with Hermes CLI style.
- Glossary insertion location within `README.md` — append to existing glossary section (preserve order; insert alphabetical by English term).
- Architecture doc diagram — ASCII vs mermaid. Recommend ASCII (renders in any viewer; mermaid requires GitHub rendering).
- Stats output when FeedbackStore empty — show "no feedback yet" message + suggest operator actions (run `/feedback` or `hermes feedback import`).

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `agent/curator_audit.py` (P32) — `read_audit()` for eval score history (apply events with eval_score field)
- `agent/feedback_store.py:FeedbackStore` (P29) — `summary()` for verdict counts; `query()` for source breakdown
- `agent/evolution/queue.py:read_queue()` (P31) — patch history
- `hermes_cli/curator.py:register_cli` (P32) — extend with `stats` subparser
- `skills/movie-experts/_shared/v86-pipeline-mapping.md` (v5.0 close-out) — structural template for v6 architecture doc
- `skills/movie-experts/_shared/snowflake-method.md` + 4 other v4/v5 refs — byte-intact reference baseline (SC-8)
- `.planning/research/v2-pipeline-design/skills-mapping.yaml` — canonical sign-off registry (add v6_ref_signoffs)
- `skills/movie-experts/README.md` — corpus tree + glossary (extend)
- `rich` library (`rich==14.3.3`) — table + sparkline rendering

### Established Patterns
- `encoding="utf-8"` on every `open()` (Ruff PLW1514)
- `from __future__ import annotations`
- `get_hermes_home()`
- Pydantic v2 for record schemas
- snake_case modules, PascalCase classes
- Bilingual EN+CN glossary convention `### Term / 中文术语`

### Integration Points
- **Input:** `~/.hermes/skills/.feedback/` (P29 store) + `~/.hermes/skills/.audit/log.jsonl` (P32) + `~/.hermes/skills/.feedback/evolution/queue.jsonl` (P31)
- **Output:** `skills/movie-experts/_shared/v6-feedback-loop-architecture.md` (NEW)
- **Output:** `skills/movie-experts/README.md` (MODIFY — add corpus tree entry + 4 glossary entries)
- **Output:** `.planning/research/v2-pipeline-design/skills-mapping.yaml` (MODIFY — add v6_ref_signoffs section)

</code_context>

<specifics>
## Specific Ideas

- The stats subcommand MUST be read-only — never mutate state. Operator-facing observability surface only.
- The architecture doc MUST include a data flow diagram showing the feedback loop. ASCII recommended (renders everywhere; mermaid requires GitHub rendering).
- The glossary entries MUST cross-reference the architecture doc (e.g., "See `_shared/v6-feedback-loop-architecture.md` §3 for the JSON schema") so operators can navigate from term to detail.
- The `v6_ref_signoffs:` section MUST mirror the schema of `v4_ref_signoffs:` and `v5_ref_signoffs:` (existing in skills-mapping.yaml). Verify the schema by reading existing sections first.
- The milestone-wide byte-intact checks (SC-7 + SC-8) MUST run as part of phase verification — not just per-phase checks. `git diff v5.0..HEAD -- skills/movie-experts/ | grep -v _eval | grep -v _shared | wc -l` should return 0 for bundled SKILL.md changes (allowing only _shared/ additions and _eval/ extensions).

</specifics>

<deferred>
## Deferred Ideas

- **Web dashboard** — P33 ships CLI stats only. Web dashboard deferred to FUTURE-V6.
- **Real-time stats** — v6 stats are point-in-time queries. Live updates / streaming deferred.
- **Multi-operator stats aggregation** — v6 single-operator. FUTURE-V6.
- **Historical trend beyond audit log retention** — bounded by audit log retention (current: unlimited; auto-prune deferred).
- **Stats export to Prometheus/Grafana** — out of scope. `--json` flag enables external pipeline integration.

</deferred>
