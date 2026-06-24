# Phase 33: Observability + Integration Close-out - Research

**Researched:** 2026-06-25
**Domain:** Operator observability CLI + milestone canonical documentation close-out
**Confidence:** HIGH

## Summary

Phase 33 is a **close-out phase** that mirrors the v5.0 Phase 27 pattern: ship one new CLI subcommand family (`hermes curator stats`) + one canonical architecture doc (`_shared/v6-feedback-loop-architecture.md`) + one skills-mapping.yaml section (`v6_ref_signoffs:`) + README/glossary updates. The technical surface is small and **everything has a directly-mirrored precedent** in v4.0 (Phase 21) or v5.0 (Phase 27). Research value is in confirming the exact patterns to mirror, not in exploring new technology.

The stats CLI is a **pure read-only aggregation** over three existing data stores shipped in P29/P31/P32: `FeedbackStore.summary()` (verdict counts), `read_queue(status="applied")` (patch history), and `read_audit(action="apply")` (eval score trend). No new persistence, no new schema, no new dependencies. The only library addition is `rich.table.Table` which is already in the stack at `rich==14.3.3` and already used in 5 hermes_cli modules (`bundles.py:21`, `banner.py:570`, `plugins_cmd.py`, `secrets_cli.py`, `skills_hub.py`).

**Primary recommendation:** Implement as **single-plan** (one PLAN.md file). The work cleanly splits into (1) stats CLI module + tests, (2) architecture doc + sign-off YAML, (3) README/glossary + byte-intact verification — but these are tightly coupled by the SC criteria and a single plan can sequence them in 3 waves without coordination overhead. Mirror the curator CLI register_cli extension pattern from P32 exactly (lazy imports in handlers, sub-parser registered in `register_cli`, no module-level agent.evolution imports).

**Key finding on byte-intact checks:** The v5.0 git tag exists locally (`git tag --list 'v5*'` returns `v5.0`), and the SC-7/SC-8 commands in CONTEXT.md work as written. A spot-check of `git diff --name-only v5.0..HEAD -- skills/movie-experts/` returns 9 files — all under `_eval/` (correctly excluded by SC-7's `grep -v _eval`). The `_shared/` exclusion in SC-7 correctly permits the new `v6-feedback-loop-architecture.md` addition. SC-8's explicit file list for v4/v5 refs is the more precise check.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Per-skill stats aggregation | CLI layer (`hermes_cli/curator.py`) | Agent layer (read-only query) | CLI owns presentation; delegates reads to FeedbackStore (P29) + audit log (P32) + evolution queue (P31) |
| Verdict bucket counts | Agent layer (`agent/feedback_store.py`) | — | `FeedbackStore.summary()` already returns per-bucket counts — stats CLI consumes, does not recompute |
| Patch history | Agent layer (`agent/evolution/queue.py`) | — | `read_queue(status="applied")` already exists from P31 |
| Eval score trend | Agent layer (`agent/curator_audit.py`) | — | `read_audit(action="apply")` returns entries with `eval_score` field |
| Architecture doc | Skill knowledge layer (`_shared/`) | — | Operator-facing reference doc; no runtime import |
| Glossary entries | Skill knowledge layer (`_shared/glossary.md` + `README.md`) | — | Pure markdown; follows v4/v5 bilingual convention |
| Byte-intact verification | Git / shell | — | `git diff v5.0..HEAD` — no Python code |

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Stats output format:** Plain-text tables via `rich` library (`rich==14.3.3` already in stack). Use `rich.table.Table` for per-skill dashboard, cross-skill view, source breakdown. `--json` flag emits machine-readable JSON.
- **Eval score trend depth:** Default last N=10 runs, configurable via `--runs N`. History from `audit-log` entries (action=apply AND eval_score populated). If fewer than N runs: show existing + "need more data for trend" footer.
- **Trend visualization:** `rich.table.Table` with columns [Date | Verdict | Mean Δ | Per-prompt Max Drop | Commit SHA] + textual sparkline using unicode block chars (▁▂▃▄▅▆▇█) for mean_delta.
- **Architecture doc structure:** Mirror v5.0 `v86-pipeline-mapping.md` pattern. 7 sections (see §"v86-pipeline-mapping.md Structure Audit" below). Bilingual: English body + Chinese section headers per `### <EN> / <中文>` convention. Write to `skills/movie-experts/_shared/v6-feedback-loop-architecture.md`.
- **README + glossary:** Glossary 4 new terms (Feedback Ingestion / Knowledge Evolution / Eval Gate / Curator Proposal) — H3 bilingual header + 2-3 sentence explanation + cross-reference to architecture doc. README corpus tree updated to list new v6 ref alongside v4/v5 refs.
- **CLI surface:**
  ```
  hermes curator stats [skill_id] [--runs N] [--json]
  hermes curator stats --all [--top N] [--json]
  hermes curator stats --by-source [--skill <id>] [--json]
  ```
  `stats` extends existing `hermes_cli/curator.py:register_cli` (matches P32 `queue`/`approve`/`reject`/`audit-log` subparsers).

### Claude's Discretion

- **Sparkline rendering:** Recommend rich's `BarColumn` for consistency with Hermes CLI style (alternative: unicode block characters).
- **Glossary insertion location:** Append to existing glossary section (preserve order; insert alphabetical by English term).
- **Architecture doc diagram:** Recommend ASCII (renders in any viewer; mermaid requires GitHub rendering).
- **Stats output when FeedbackStore empty:** Show "no feedback yet" message + suggest operator actions (run `/feedback` or `hermes feedback import`).

### Deferred Ideas (OUT OF SCOPE)

- Web dashboard (P33 ships CLI stats only; web deferred to FUTURE-V6)
- Real-time stats / streaming (v6 stats are point-in-time queries)
- Multi-operator stats aggregation (v6 single-operator)
- Historical trend beyond audit log retention (current: unlimited; auto-prune deferred)
- Stats export to Prometheus/Grafana (`--json` flag covers external pipeline integration)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OBS-01 | Per-skill dashboard (`hermes curator stats [skill_id]`) — feedback counts by verdict + patch history + eval score trend over N runs | `FeedbackStore.summary(skill_id=...)` returns verdict buckets; `read_queue(status="applied")` returns patch history; `read_audit(action="apply", skill=...)` returns eval-score-populated entries for trend |
| OBS-02 | Cross-skill view (`hermes curator stats --all`) — top-N negative feedback / top-N patches by uplift / zero-feedback list | Iterate `FeedbackStore.summary()` across all bucket keys; aggregate from `store._index["buckets"]` (bucket key format `<skill>:<source>:<verdict>`) |
| OBS-03 | Source breakdown (CLI/kais-aigc/manual verdict distribution) | `FeedbackStore.summary(source=...)` per-source; OR single summary() call then group by parsing the bucket key middle segment |
| SC-4 | Canonical architecture doc `_shared/v6-feedback-loop-architecture.md` | Mirror v86-pipeline-mapping.md structure (7 sections confirmed, see audit below) |
| SC-5 | `skills-mapping.yaml` `v6_ref_signoffs:` section | Mirror v5_ref_signoffs schema (8 fields per entry — see schema audit below) |
| SC-6 | README corpus tree + glossary 4 new bilingual terms | README has `_shared/` listing at line 417; glossary has H3 bilingual convention confirmed (line 20 example: `### 运镜 / cinematography / camera movement`) |
| SC-7 | FOUND-08 milestone-wide preservation check | `git diff v5.0..HEAD -- skills/movie-experts/ \| grep -v _eval \| grep -v _shared \| wc -l` returns 0 — v5.0 tag confirmed present |
| SC-8 | v5/v4 refs byte-intact check | `git diff v5.0..HEAD -- skills/movie-experts/_shared/{snowflake-method,e-konte-format,scamper-variations,dreamina-cli-baseline,v86-pipeline-mapping}.md \| wc -l` returns 0 (none of these 5 files appear in the 9-file diff) |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `rich` | 14.3.3 | Table + sparkline rendering for stats output | Already in stack (`pyproject.toml`); already used in 5 `hermes_cli/*.py` modules `[VERIFIED: codebase grep]` |
| `argparse` | stdlib | Subparser wiring for `stats` command | Existing `register_cli` pattern in `hermes_cli/curator.py:811` `[VERIFIED: codebase]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `agent.feedback_store.FeedbackStore` | P29 shipped | `summary()` + `query()` for verdict counts / source breakdown | All stats reads — never re-implement |
| `agent.curator_audit.read_audit` | P32 shipped | Eval score trend (action=apply filter) | OBS-01 trend column |
| `agent.evolution.read_queue` | P31 shipped | Patch history (status=applied) | OBS-01 patch history table |
| `json` | stdlib | `--json` output flag | Machine-readable pipeline integration |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `rich.table.Table` | Plain text aligned columns | rich is already in stack + gives colored cells for verdict buckets (green=good, yellow=needs_work, red=bad) for free |
| Unicode sparkline (▁▂▃▄▅▆▇█) | rich's `BarColumn` | CONTEXT.md Claude's-discretion recommends BarColumn for consistency; sparkline is more compact for a trend row `[ASSUMED]` |
| stats as separate module | stats handlers in `hermes_cli/curator.py` | Single-module mirrors P32 pattern (queue/approve/reject handlers all in `curator.py`) — keeps register_cli + handlers co-located |

**Installation:** No new packages. `rich==14.3.3` is already pinned in `pyproject.toml`.

**Version verification:**
```bash
$ grep '^rich=' pyproject.toml       # → rich==14.3.3 [VERIFIED]
$ grep -rln "from rich.table import" hermes_cli/ | wc -l   # → 5 modules already use it [VERIFIED]
```

## Package Legitimacy Audit

> This phase installs **zero** new external packages. All dependencies are already pinned in `pyproject.toml` and shipped in prior phases (rich since v1; FeedbackStore since P29; curator_audit since P32; evolution queue since P31). Slopcheck step SKIPPED — no new packages to audit.

## Architecture Patterns

### System Architecture Diagram

```
Operator
   │
   │ hermes curator stats [skill_id] [--runs N] [--json]
   │ hermes curator stats --all [--top N] [--json]
   │ hermes curator stats --by-source [--skill X] [--json]
   ▼
┌─────────────────────────────────────────────────┐
│ hermes_cli/curator.py                            │
│  └─ _cmd_stats(args)  ← NEW handler             │
│      ├─ rich.table.Table rendering (or --json)   │
│      └─ LAZY imports (runtime isolation):        │
│         ├─ agent.feedback_store.FeedbackStore    │
│         ├─ agent.curator_audit.read_audit        │
│         └─ agent.evolution.read_queue            │
└─────────────────────────────────────────────────┘
   │              │                      │
   │  summary()   │  read_audit(         │  read_queue(
   │  query()     │    action="apply")   │    status="applied")
   ▼              ▼                      ▼
┌──────────┐  ┌──────────────────┐  ┌──────────────────┐
│ P29      │  │ P32              │  │ P31              │
│ store    │  │ ~/.hermes/       │  │ ~/.hermes/       │
│ index.   │  │ skills/.audit/   │  │ skills/.feedback │
│ json +   │  │ log.jsonl        │  │ /evolution/      │
│ buckets/ │  │ (sha256-chained) │  │ {pending,applied,│
│          │  │                  │  │  rejected}.jsonl │
└──────────┘  └──────────────────┘  └──────────────────┘
   ▲ READ-ONLY — stats MUST NOT mutate any of these stores
```

The diagram shows the read-only data flow: `stats` is a pure aggregation surface. The three data stores are owned by P29/P31/P32 respectively and `stats` only queries them.

### Recommended Project Structure
```
hermes_cli/curator.py                  # MODIFY — add _cmd_stats + stats subparser
tests/hermes_cli/test_curator_stats.py # NEW — CLI smoke tests (mirrors test_curator_cli.py)
tests/agent/test_curator_stats_engine.py  # NEW (optional) — aggregation helper tests
skills/movie-experts/_shared/
    v6-feedback-loop-architecture.md   # NEW — canonical architecture doc
    glossary.md                        # MODIFY — add 4 H3 bilingual entries
skills/movie-experts/README.md         # MODIFY — corpus tree + v6 section
.planning/research/v2-pipeline-design/
    skills-mapping.yaml                # MODIFY — add v6_ref_signoffs: section
```

### Pattern 1: curator CLI extension (mirror P32 exactly)
**What:** Add `stats` subparser to existing `register_cli`; handler does lazy imports.
**When to use:** Any new `hermes curator <verb>` command.
**Example:** `[VERIFIED: hermes_cli/curator.py:811-1005 — P32 register_cli extension]`
```python
# In hermes_cli/curator.py register_cli, AFTER p_auto block:

p_stats = subs.add_parser(
    "stats",
    help="Per-skill / cross-skill feedback stats (OBS-01/02/03)",
)
p_stats.add_argument(
    "skill_id", nargs="?", default=None,
    help="Skill to show (omit with --all/--by-source for cross-skill view)",
)
p_stats.add_argument(
    "--all", dest="all_skills", action="store_true",
    help="Cross-skill view (top-N negative feedback, zero-feedback list)",
)
p_stats.add_argument(
    "--by-source", dest="by_source", action="store_true",
    help="Source breakdown (CLI / kais_aigc / manual verdict distribution)",
)
p_stats.add_argument(
    "--top", type=int, default=10,
    help="Top-N for --all view (default: 10)",
)
p_stats.add_argument(
    "--runs", type=int, default=10,
    help="Eval-score trend depth (default: 10; OBS-01)",
)
p_stats.add_argument(
    "--skill", dest="skill_filter", default=None,
    help="Skill filter for --by-source",
)
p_stats.add_argument(
    "--json", dest="as_json", action="store_true",
    help="Emit machine-readable JSON",
)
p_stats.set_defaults(func=_cmd_stats)


def _cmd_stats(args) -> int:
    """``hermes curator stats`` — read-only observability (OBS-01/02/03).

    Pure aggregation over FeedbackStore (P29) + audit log (P32) + evolution
    queue (P31). NEVER mutates state.
    """
    # LAZY imports — zero module-level agent.evolution imports
    # (runtime-isolation invariant per agent/evolution/__init__.py).
    from agent.feedback_store import FeedbackStore
    from agent.curator_audit import read_audit
    from agent.evolution import read_queue
    # ... dispatch on args.all_skills / args.by_source / args.skill_id
    return 0
```

### Pattern 2: rich.table.Table verdict-bucket rendering
**What:** Colored cells for verdicts (good=green, needs_work=yellow, bad=red).
**When to use:** Per-skill dashboard + source breakdown.
**Example:** `[VERIFIED: hermes_cli/bundles.py:52-60 — existing Table pattern]`
```python
from rich.console import Console
from rich.table import Table

def _render_per_skill_dashboard(skill_id, summary, patch_history, eval_trend):
    console = Console()
    table = Table(title=f"Feedback stats: {skill_id}", show_lines=False)
    table.add_column("Verdict", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Weighted", justify="right")
    table.add_column("First ts")
    table.add_column("Last ts")

    # verdict styles: good=green, needs_work=yellow, bad=red
    style_map = {"good": "green", "needs_work": "yellow", "bad": "red"}
    for verdict in ("good", "needs_work", "bad"):
        # summary key format: "<skill_id>:<source>:<verdict>"
        count = weighted = 0
        first_ts = last_ts = "—"
        for key, bucket in summary.items():
            if key.endswith(f":{verdict}"):
                count += bucket.get("count", 0)
                weighted += bucket.get("weighted_count", 0)
                ...
        table.add_row(
            f"[{style_map[verdict]}]{verdict}[/{style_map[verdict]}]",
            str(count), f"{weighted:.1f}", first_ts, last_ts,
        )
    console.print(table)
```

### Pattern 3: Sparkline rendering
**What:** Compact trend visualization for mean_delta column.
**When to use:** Eval score trend (OBS-01).
**Example:** `[ASSUMED — recommend unicode block chars per CONTEXT.md]`
```python
_SPARK = "▁▂▃▄▅▆▇█"  # 8 buckets, index 0 (lowest) to 7 (highest)

def _sparkline(values: list[float]) -> str:
    """Compact unicode-block sparkline for a series of floats.

    Maps min(values)..max(values) onto 8 buckets. Empty list → empty string.
    """
    if not values:
        return ""
    lo, hi = min(values), max(values)
    if hi == lo:
        # All identical → all middle-tier block.
        return _SPARK[4] * len(values)
    span = hi - lo
    return "".join(
        _SPARK[min(7, max(0, int((v - lo) / span * 7.999)))]
        for v in values
    )
```
**Alternative (rich `BarColumn`):** Rich does not have a native sparkline column; `BarColumn` renders a single bar per row. For a multi-point trend on one row, the unicode sparkline is the cleaner choice. `[ASSUMED]`

### Anti-Patterns to Avoid
- **Mutating state in a stats command:** `stats` MUST be read-only. Never call `record_feedback`, `append_audit`, or any queue mutation. `[VERIFIED: CONTEXT.md specifics line 113]`
- **Module-level `agent.evolution` imports in `hermes_cli/curator.py`:** Breaks runtime-isolation invariant. All such imports MUST be inside handler bodies (P32 pattern at `hermes_cli/curator.py:691-699`). `[VERIFIED: P32 SC runtime-isolation-0]`
- **Re-implementing verdict aggregation from bucket files:** `FeedbackStore.summary()` already returns per-bucket counts/weighted_counts from `index.json`. Scanning `buckets/*.jsonl` directly bypasses the index and the supersession logic. `[VERIFIED: agent/feedback_store.py:990-1022]`
- **Mermaid diagrams in architecture doc:** CONTEXT.md Claude's-discretion recommends ASCII. Mermaid requires GitHub rendering and breaks in plain-text viewers. `[CITED: CONTEXT.md line 76]`
- **Glossary terms without cross-reference to architecture doc:** CONTEXT.md specifics require each entry cross-reference the architecture doc (e.g., "See `_shared/v6-feedback-loop-architecture.md` §3 for the JSON schema"). `[CITED: CONTEXT.md line 116]`

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Verdict counts | Walk `buckets/*.jsonl` + tally | `FeedbackStore.summary(skill_id=...)` | Already handles supersession filtering + weighted_count; index.json is the single source of truth `[VERIFIED: feedback_store.py:990]` |
| Eval score history | Parse `log.jsonl` manually | `read_audit(action="apply", skill=...)` | Already handles timestamp filtering + tz-aware comparison + malformed-line skip `[VERIFIED: curator_audit.py:345-423]` |
| Patch history | Read `applied.jsonl` directly | `read_queue(evolution_dir=..., status="applied")` | Already Pydantic-validated; returns PatchRecord objects with patch_id + skill_id + timestamps `[VERIFIED: hermes_cli/curator.py:715 — P32 usage]` |
| Source breakdown | Iterate sources manually | `FeedbackStore.summary(source=...)` per source | Same summary() API; just filter on the source segment of the bucket key |
| Stats table rendering | Manual column alignment | `rich.table.Table` | Already used in 5 hermes_cli modules; gives colored cells + monospace alignment for free |

**Key insight:** Every aggregation stats needs already has a shipped query API from P29/P31/P32. The stats CLI is a pure presentation layer — no new aggregation logic, no new persistence, no new indexing.

## v86-pipeline-mapping.md Structure Audit

Confirmed by reading `skills/movie-experts/_shared/v86-pipeline-mapping.md` end-to-end (185 lines). `[VERIFIED]`

**Actual structure observed (10 H2 sections, not 7):**

1. **Header block** (lines 1-7) — Title line + Source/Copyright/Last-verified/verified_date metadata block
2. `## Summary` — 2-paragraph English-body-with-Chinese-prose summary + V8.6-vs-V8.4 key differences bullet list
3. `## V-Version Provenance` — table of version/commit/date/key-changes
4. `## The 13-Step V8.6 Pipeline → expert_id Mapping` — the main mapping table + supplementary notes
5. `## V8.6 8-Gate Review Structure` — review-gate table + Hard vs Soft gates subsection
6. `## Atomic Operations (V8.6 §1-§6 6 组合并)` — atomic operation table
7. `## dreamina CLI as Canonical Image/Video Tool` — tool reference section
8. `## Per-Expert V8.6 Section Cross-Reference` — per-expert table of cross-links
9. `## Refresh Cadence` — drift triggers + refresh action list
10. `## See Also` — cross-ref links to other `_shared/` docs
11. `## Source Citation` — Primary/Secondary/Tertiary source list

**Context.md "7 sections" maps roughly to:** Summary + Data Flow + Schema Reference + Thresholds + Human-in-Loop + Module Ownership + Roadmap References. The CONTEXT.md list is a **logical 7-section outline**, not a literal section count. The planner should aim for the v86 doc's **structural conventions**, not its exact section titles:

- **Header metadata block** at top (Source / Copyright / Last-verified / verified_date)
- **Bilingual body:** English structure (tables, bullets) with Chinese descriptive prose embedded
- **Cross-reference table** at the end (like the Per-Expert cross-ref table)
- **Refresh Cadence** section (drift triggers — for v6: feedback schema bump, gate threshold change, etc.)
- **See Also + Source Citation** at the end
- **Footer ownership line** (`*Owned by Phase 33 plan 33-XX. ...*`)

**Recommendation:** Use the CONTEXT.md 7-section logical outline as the section sequence, but adopt the v86 doc's structural conventions (metadata header block + cross-reference table + refresh cadence + See Also + Source Citation footer).

## skills-mapping.yaml v5_ref_signoffs Schema Audit

Confirmed by reading `skills-mapping.yaml` lines 260-283 (v5_ref_signoffs section). `[VERIFIED]`

**Per-entry schema (8 fields):**

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `ref_path` | str | `skills/movie-experts/_shared/v86-pipeline-mapping.md` | Repo-relative path |
| `expert_owner` | str | `_shared` | `_shared` for cross-cutting refs; specific expert_id otherwise |
| `phase_added` | str | `v5.0-phase-27` | Format: `<milestone>-phase-<num>` |
| `requirement` | str | `INTEGRATION-01` | REQ-ID this ref satisfies |
| `verified_date` | date (YYYY-MM-DD) | `2026-06-19` | Sign-off date |
| `source` | str (long) | `"kais-movie-agent V8.6 SKILL.md (commit e41fa68, 2026-06-18 22:56:46 +0800) §..."` | Full citation including commit + section pointers |
| `license_status` | enum str | `fair_use_paraphrase` | Other values seen: `fair_use_paraphrase` is the only value used across v4+v5 |
| `line_count` | int | `220` | Total line count of the ref file |
| `signed_off_by` | str | `phase-27-doc-02` | Format: `phase-<num>-<plan-slug>` |
| `notes` | str (long) | `"V8.6 13-Step → expert_id mapping table..."` | Freeform provenance + original-work-delineation notes |

**Header convention:** Each section (`v4_ref_signoffs:`, `v5_ref_signoffs:`) is preceded by a comment block explaining what milestone added what. The v6 section should follow the same pattern:

```yaml
# ============================================
# v6.0 ref-level sign-off entries (Phase 33 close-out)
# ============================================
# These entries cover REFS (shared markdown under _shared/),
# NOT new expert_id mappings. They are distinct from the 19 expert-level
# `sign_off_status: signed_off` entries in the `mappings:` block above.
# v6.0 added 1 shared ref (v6-feedback-loop-architecture.md) documenting
# the v6.0 feedback-loop architecture per FOUND-08 backward-compat rule
# and v6.0 milestone scope.
v6_ref_signoffs:

  - ref_path: skills/movie-experts/_shared/v6-feedback-loop-architecture.md
    expert_owner: _shared
    phase_added: v6.0-phase-33
    requirement: OBS-01    # or INTEGRATION-equivalent; v6 has no INTEGRATION req — use OBS-01 as anchor
    verified_date: 2026-06-XX
    source: "Hermes Agent v6.0 Self-Evolution & Feedback Loop — internally authored architecture doc synthesizing P28-P32 implementations (agent/feedback_ingest.py + agent/feedback_store.py + skills/movie-experts/_eval/gate.py + agent/evolution/* + agent/curator.py + agent/curator_audit.py)"
    license_status: fair_use_paraphrase
    line_count: <TBD at write time>
    signed_off_by: phase-33-doc-01
    notes: "Canonical v6.0 feedback-loop architecture reference. Internally authored — no upstream source (unlike v4/v5 refs which paraphrased external methodologies). Documents ingest → store → gate → evolve → curate → observe pipeline with JSON schema, eval-gate thresholds, and human-in-loop boundaries."
```

**Schema-mirror sufficiency:** CONTEXT.md instruction "mirror schema" IS sufficient — every field has a clear precedent. The only novel aspect is `source` (internal vs external); the v4/v5 entries cite external books/commits, while v6 cites the Hermes Agent codebase itself. Use the `notes` field to make this internally-authored status explicit.

## README.md Corpus Tree + Glossary Structure

Confirmed by reading `skills/movie-experts/README.md` end-to-end. `[VERIFIED]`

**Corpus tree location:** Lines 357-425 (`## File Layout` section). The `_shared/` directory block at lines 417-424:

```
└── _shared/
    ├── glossary.md                               (EN↔CN term dictionary — Phase 7 expanded)
    ├── known-external-models.yaml                (model name allowlist — Phase 7 expanded)
    ├── platform-comparison.md
    ├── RAG-INVOCATION-PATTERN.md
    ├── SKILL-LAYOUT.md                           (reference anatomy spec)
    ├── cognitive-resonance-metrics.md            (Phase 7C-1 NEW — 4-scale evaluation rubric)
    └── quality-rubric.md                         (Phase 7C-2 NEW — 6-dim publish-gate rubric)
```

**Observation:** The corpus tree currently DOES NOT list `dreamina-cli-baseline.md` or `v86-pipeline-mapping.md` — they were added in v5.0 but the corpus tree was not updated. **SC-6 has a latent gap:** the v5.0 README close-out may have missed the corpus tree update. The planner should:
1. Add the new `v6-feedback-loop-architecture.md` line to the `_shared/` block (alphabetical or chronological — CONTEXT.md discretion recommends alphabetical by English term)
2. Optionally backfill the two missing v5.0 entries (`dreamina-cli-baseline.md`, `v86-pipeline-mapping.md`) — this is a documented gap, not in P33 scope but trivially fixable while we're editing the tree

**Glossary structure:** `_shared/glossary.md` uses H3 bilingual headers throughout:
- `### 运镜 / cinematography / camera movement` (line 20) — CN-first, EN-after-slash
- Each entry has 3 subsections: **CN:** / **EN:** / **Context:**
- Sections are organized: Core terms → Extended terms → Phase 7 additions → Phase 17 additions

**Glossary insertion plan:** Create a new `## v6.0 additions (4 new feedback-loop terms)` H2 section. Insert the 4 H3 entries in alphabetical order by English term:
- `### Curator Proposal / 策展提案`
- `### Eval Gate / 评估闸门`
- `### Feedback Ingestion / 知识反馈采集`
- `### Knowledge Evolution / 知识进化`

Each entry MUST cross-reference the architecture doc per CONTEXT.md specifics line 116.

**Format convention conflict note:** Existing glossary uses **CN-first** format (`### 运镜 / cinematography`), but CONTEXT.md examples use **EN-first** format (`### Feedback Ingestion / 知识反馈采集`). `[CITED: CONTEXT.md line 50-54]` Recommend following CONTEXT.md's EN-first format for the 4 new v6 entries — operators reading the architecture doc in English-order will find matching glossary entries. Document this format decision in a footer note. `[ASSUMED — needs operator confirmation in plan-phase]`

## Runtime State Inventory

> Phase 33 is a **close-out phase** with no rename/refactor/migration. SKIPPED per execution_flow Step 2.5 trigger condition. The only state touched is: (1) new file creation (`v6-feedback-loop-architecture.md`, two test files), (2) additive modification (`hermes_cli/curator.py` — new handlers + subparser, no existing code changed), (3) documentation edits (`README.md`, `glossary.md`, `skills-mapping.yaml` — append-only sections). No runtime state, no stored data, no OS-registered state, no secrets, no build artifacts touched.

## Common Pitfalls

### Pitfall 1: Architecture doc structure drift from v86 template
**What goes wrong:** The writer freeforms the architecture doc structure instead of mirroring v86-pipeline-mapping.md. Result: the v6 doc doesn't match the v5.0 close-out pattern, breaking the "mirrors v5.0 pattern" SC-4 criterion.
**Why it happens:** v86 has 10 H2 sections, not the 7 in CONTEXT.md's logical outline. The writer may either slavishly copy all 10 (some don't apply to v6 — e.g., "V-Version Provenance" is kais-specific) or improvise.
**How to avoid:** Use CONTEXT.md's 7-section logical outline as the section sequence. Adopt v86's structural conventions (metadata header block + cross-reference table + Refresh Cadence + See Also + Source Citation footer). Write a brief mapping note in the doc explaining which v86 sections were dropped (e.g., "V-Version Provenance — N/A for v6; v6 has no upstream V-number dependency").
**Warning signs:** Doc has < 5 or > 9 H2 sections; missing metadata header block; missing See Also / Source Citation footer.

### Pitfall 2: Byte-intact false positives from `_shared/` additions
**What goes wrong:** SC-7's `git diff v5.0..HEAD -- skills/movie-experts/ | grep -v _eval | grep -v _shared | wc -l` returns 0 — but the writer forgets to also exclude the new `_shared/v6-feedback-loop-architecture.md` from a stricter check. Conversely, SC-8's explicit file list for v4/v5 refs is correct but the writer may over-exclude.
**Why it happens:** SC-7 correctly excludes ALL of `_shared/` (which permits the v6 architecture doc addition). But a paranoid secondary check like `git diff v5.0..HEAD -- skills/movie-experts/_shared/ | wc -l` would return > 0 (because of the new v6 doc) and a naive reader might conclude SC-8 failed.
**How to avoid:** SC-7 and SC-8 are complementary: SC-7 verifies bundled SKILL.md + non-_shared references unchanged (excludes both `_eval/` and `_shared/`); SC-8 verifies the 5 specific v4/v5 _shared refs unchanged (explicit file list). They do NOT overlap. Run both as written; do not invent intermediate checks.
**Warning signs:** The verifier invents a third check that combines SC-7 and SC-8 logic; the new v6 doc is incorrectly included in SC-8's file list.

### Pitfall 3: Glossary format inconsistency (CN-first vs EN-first)
**What goes wrong:** Existing glossary uses CN-first (`### 运镜 / cinematography`); CONTEXT.md specifies EN-first for the 4 new entries (`### Feedback Ingestion / 知识反馈采集`). Result: the glossary has two conflicting header formats.
**Why it happens:** v1-v5 glossary grew organically CN-first; v6 CONTEXT.md author wrote examples EN-first.
**How to avoid:** Follow CONTEXT.md (EN-first for v6 entries). Add a footer note in the v6 section explaining the format shift: "v6.0 entries use EN-first format per Phase 33 CONTEXT.md; earlier entries retain CN-first for backward compatibility." This preserves existing entries byte-intact (SC-7) while making the new section internally consistent. `[ASSUMED — flag for operator confirmation]`
**Warning signs:** Writer "fixes" existing CN-first entries to EN-first — this would violate SC-7 byte-intact.

### Pitfall 4: Stats CLI mutating state accidentally
**What goes wrong:** `_cmd_stats` accidentally triggers FeedbackStore initialization side-effects (e.g., `_maybe_migrate_phase28_incoming` runs during `FeedbackStore()` construction and moves files).
**Why it happens:** `FeedbackStore.__init__` at `agent/feedback_store.py:214-269` runs lazy migration on construction. If a test fixture leaves files in `incoming/`, the stats command would migrate them — a write side-effect from a read command.
**How to avoid:** Stats tests should use `tmp_path` fixtures with empty `incoming/` directories. The `_maybe_migrate_phase28_incoming` is idempotent (sentinel file + `_migrated` flag) so production stats calls after P29 has run are safe. `[VERIFIED: feedback_store.py:1061-1063]`
**Warning signs:** Stats tests leave feedback files in `incoming/`; stats integration tests show migration log lines.

### Pitfall 5: `read_audit` tz-aware comparison edge case
**What goes wrong:** Stats trend query uses `since=` filter with a naive ISO date; `read_audit` returns 0 entries because of tz-naive-vs-aware TypeError historically (CR-02 in P32).
**Why it happens:** `read_audit` at `agent/curator_audit.py:372-388` already handles this (promotes naive `since` to aware UTC). But the stats CLI might construct `since` from `datetime.now() - timedelta(days=N)` without tzinfo.
**How to avoid:** Always use `datetime.now(timezone.utc)` for any timestamp construction in stats. The existing `read_audit` API is safe; the risk is only in CLI-level timestamp construction.
**Warning signs:** Trend shows 0 entries when audit log has entries; `--since` filter returns nothing.

## Code Examples

### read-only stats aggregation (VERIFIED API signatures)

```python
# Source: agent/feedback_store.py:990 (summary) + agent/curator_audit.py:345 (read_audit)
# Source: agent/evolution/__init__.py (read_queue — P31 shipped)

from agent.feedback_store import FeedbackStore
from agent.curator_audit import read_audit
from agent.evolution import read_queue

def gather_per_skill_stats(skill_id: str, runs: int = 10) -> dict:
    """Pure read-only aggregation for OBS-01 per-skill dashboard.

    Returns a dict suitable for either rich rendering or --json output.
    NEVER mutates any store.
    """
    store = FeedbackStore()  # Safe: idempotent init; migration runs only if incoming/ has files

    # 1. Verdict buckets from index.json (single source of truth)
    summary = store.summary(skill_id=skill_id)
    # summary keys: "<skill_id>:<source>:<verdict>" → {count, weighted_count, first_ts, last_ts}

    # 2. Patch history from P31 evolution queue
    patch_history = read_queue(status="applied")  # returns list[PatchRecord]
    patch_history = [p for p in patch_history if p.skill_id == skill_id]

    # 3. Eval score trend from P32 audit log (action=apply + eval_score populated)
    audit_entries = read_audit(action="apply", skill=skill_id)
    # Filter to entries with non-empty eval_score; take last `runs`
    trend_entries = [e for e in audit_entries if e.get("eval_score")] [-runs:]

    return {
        "skill_id": skill_id,
        "verdict_buckets": _collapse_sources(summary),
        "patch_count": len(patch_history),
        "recent_patches": [_patch_to_dict(p) for p in patch_history[-5:]],
        "eval_trend": trend_entries,
    }


def gather_cross_skill_stats(top_n: int = 10) -> dict:
    """Pure read-only aggregation for OBS-02 cross-skill view."""
    store = FeedbackStore()
    summary = store.summary()  # all buckets
    # Parse bucket keys "<skill>:<source>:<verdict>"
    per_skill = {}
    for key, bucket in summary.items():
        parts = key.split(":")
        if len(parts) != 3:
            continue
        skill, source, verdict = parts
        per_skill.setdefault(skill, {"good": 0, "needs_work": 0, "bad": 0})
        per_skill[skill][verdict] += bucket.get("count", 0)

    # Top-N by negative feedback (needs_work + bad)
    neg_counts = {
        s: counts["needs_work"] + counts["bad"]
        for s, counts in per_skill.items()
    }
    top_negative = sorted(neg_counts.items(), key=lambda x: -x[1])[:top_n]

    # Zero-feedback skills (need to know the bundled-skill list to detect gaps)
    # ... compare per_skill.keys() against the bundled expert_id list
    return {"per_skill": per_skill, "top_negative": top_negative}


def gather_source_breakdown(skill_id: str | None = None) -> dict:
    """Pure read-only aggregation for OBS-03 source breakdown."""
    store = FeedbackStore()
    # Either: summary(source=...) per source, OR summary(skill_id=...) then group
    sources = ("cli", "kais_aigc", "manual")
    out = {}
    for source in sources:
        summary = store.summary(source=source, skill_id=skill_id)
        # Tally verdicts across skills
        verdicts = {"good": 0, "needs_work": 0, "bad": 0}
        for key, bucket in summary.items():
            parts = key.split(":")
            if len(parts) != 3:
                continue
            verdict = parts[2]
            verdicts[verdict] = verdicts.get(verdict, 0) + bucket.get("count", 0)
        out[source] = verdicts
    return out
```

### argparse subparser wiring (mirror P32 register_cli)

See Pattern 1 above — the code block at `hermes_cli/curator.py:921-1005` (P32 extension) is the exact structural template. Append the `stats` subparser block after the `p_auto` block.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| v1-v5: Static knowledge layer (manual curate) | v6: Feedback-driven dynamic learning | v6.0 P28-P32 shipped 2026-06-24/25 | Stats CLI surfaces the new feedback signal for the first time — operators can see learning health |
| Per-phase byte-intact checks (P22-P32) | Milestone-wide SC-7 + SC-8 in P33 | v6.0 close-out | Consolidates preservation verification at milestone boundary, not per-phase |

**Deprecated/outdated:**
- None in this phase. All patterns mirror v5.0 P27 close-out.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Unicode sparkline chars (▁▂▃▄▅▆▇█) render correctly in operators' terminals | Pattern 3 | If wrong: fall back to ASCII (`_=-` chars); cosmetic only, no functional impact |
| A2 | EN-first glossary format for v6 entries is acceptable (CONTEXT.md examples vs existing CN-first convention) | Pitfall 3 | If wrong: operator prefers CN-first; trivial format swap, no content change. Flag for plan-phase confirmation |
| A3 | `requirement: OBS-01` is the correct anchor REQ-ID for the v6 architecture doc in skills-mapping.yaml (v6 has no INTEGRATION-* reqs) | skills-mapping.yaml schema audit | If wrong: any OBS-01..03 is defensible; the doc covers all three. Low impact |
| A4 | README corpus tree missing v5.0 entries (dreamina-cli-baseline.md, v86-pipeline-mapping.md) is a real latent gap, not a research oversight | README audit | If wrong (they were added somewhere else in README): minor — planner should grep README to confirm before deciding to backfill |
| A5 | Stats CLI should be a single plan, not split into multiple plans | Summary recommendation | If wrong: split into Plan 01 (CLI + tests) + Plan 02 (docs + sign-offs + byte-intact). Either works; single plan is simpler given the tight SC coupling |

## Open Questions

1. **Should the README corpus tree backfill the missing v5.0 entries?**
   - What we know: The `_shared/` corpus tree block at README.md:417-424 does not list `dreamina-cli-baseline.md` or `v86-pipeline-mapping.md`, even though both were added in v5.0.
   - What's unclear: Whether v5.0 Phase 27 added them elsewhere in README (e.g., the v5.0 summary section at line 483-513 lists them as "2 new `_shared/` refs" in a table — so they ARE documented, just not in the corpus tree block).
   - Recommendation: Add the v6 entry to the corpus tree; do NOT backfill v5.0 entries (they're documented in the v5.0 summary section already). Note this as a documented non-blocker.

2. **Does the empty-FeedbackStore case need a distinct exit code?**
   - What we know: CONTEXT.md Claude's-discretion says show "no feedback yet" message + suggest operator actions.
   - What's unclear: Exit 0 (normal "no data" report) vs exit 1 ("error: no data")? P32's `_cmd_audit_log` returns 0 when empty (`if not entries: print("(no audit entries match)"); return 0`).
   - Recommendation: Mirror P32 — exit 0 with informative message. `[VERIFIED: hermes_cli/curator.py:659-661]`

3. **Should stats verify the audit-log sha256 chain as a side check?**
   - What we know: `read_audit` reads but does not verify the chain. `verify_chain` exists.
   - What's unclear: Should `stats` warn if the chain is broken?
   - Recommendation: No — stats is read-only observability; chain verification is the job of `hermes curator audit-log --verify`. Adding it to stats would conflate concerns.

## Environment Availability

> Phase 33 has minimal external dependencies. The only runtime requirements are the already-shipped P29/P31/P32 modules + rich (already pinned). SKIPPED — no external tools/services beyond what P28-P32 already require.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `rich` | Stats table rendering | ✓ | 14.3.3 | Plain text (would lose color) |
| `git` | SC-7 + SC-8 byte-intact checks | ✓ | (any) | Manual sha256 comparison |
| `v5.0` git tag | SC-7 + SC-8 baseline | ✓ | (tag present) | Manual commit-sha specification |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 (already configured) `[VERIFIED: pyproject.toml:261]` |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (30s per-test timeout) |
| Quick run command | `python -m pytest tests/hermes_cli/test_curator_stats.py -x` |
| Full suite command | `python -m pytest tests/hermes_cli/test_curator_stats.py tests/agent/test_curator_stats_engine.py tests/agent/test_feedback_store.py tests/agent/test_audit_log.py -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| OBS-01 | Per-skill dashboard renders verdict buckets + patch history + eval trend | unit + smoke | `pytest tests/hermes_cli/test_curator_stats.py::TestPerSkillDashboard -x` | ❌ Wave 0 |
| OBS-01 | `--runs N` limits trend depth | unit | `pytest tests/hermes_cli/test_curator_stats.py::TestRunsFlag -x` | ❌ Wave 0 |
| OBS-01 | `--json` emits valid JSON | unit | `pytest tests/hermes_cli/test_curator_stats.py::TestJsonOutput -x` | ❌ Wave 0 |
| OBS-02 | `--all` renders top-N negative + zero-feedback list | unit + smoke | `pytest tests/hermes_cli/test_curator_stats.py::TestCrossSkillView -x` | ❌ Wave 0 |
| OBS-02 | `--top N` limits cross-skill depth | unit | `pytest tests/hermes_cli/test_curator_stats.py::TestTopFlag -x` | ❌ Wave 0 |
| OBS-03 | `--by-source` renders source × verdict matrix | unit + smoke | `pytest tests/hermes_cli/test_curator_stats.py::TestSourceBreakdown -x` | ❌ Wave 0 |
| OBS-* | Empty FeedbackStore → friendly message + exit 0 | unit | `pytest tests/hermes_cli/test_curator_stats.py::TestEmptyStore -x` | ❌ Wave 0 |
| OBS-* | `stats` is read-only (no store mutation) | unit | `pytest tests/hermes_cli/test_curator_stats.py::TestReadOnly -x` | ❌ Wave 0 |
| SC-4 | Architecture doc has 7 sections + bilingual headers + metadata block | smoke | `pytest tests/hermes_cli/test_curator_stats.py::TestArchitectureDoc -x` (or a dedicated doc-structure test) | ❌ Wave 0 |
| SC-5 | skills-mapping.yaml `v6_ref_signoffs:` present with 8 fields per entry | smoke | `pytest tests/hermes_cli/test_curator_stats.py::TestSkillsMappingV6 -x` | ❌ Wave 0 |
| SC-6 | README corpus tree lists v6 ref; glossary has 4 new H3 bilingual entries | smoke | `pytest tests/hermes_cli/test_curator_stats.py::TestReadmeAndGlossary -x` | ❌ Wave 0 |
| SC-7 | `git diff v5.0..HEAD -- skills/movie-experts/ \| grep -v _eval \| grep -v _shared \| wc -l` == 0 | shell | (run in VERIFICATION, not pytest) | n/a |
| SC-8 | `git diff v5.0..HEAD -- <5 v4/v5 refs>` == 0 | shell | (run in VERIFICATION, not pytest) | n/a |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/hermes_cli/test_curator_stats.py -x`
- **Per wave merge:** `python -m pytest tests/hermes_cli/test_curator_stats.py tests/agent/test_curator_stats_engine.py tests/agent/test_feedback_store.py tests/agent/test_audit_log.py -x`
- **Phase gate:** Full suite green + SC-7 + SC-8 byte-intact checks pass before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/hermes_cli/test_curator_stats.py` — CLI smoke tests for `stats` subcommand (mirrors `test_curator_cli.py` structure)
- [ ] (Optional) `tests/agent/test_curator_stats_engine.py` — pure-function tests for aggregation helpers if extracted to a helper module
- [ ] Architecture doc verification test — parse `_shared/v6-feedback-loop-architecture.md`, assert 7 H2 sections present + bilingual headers + metadata block
- [ ] Glossary verification test — parse `_shared/glossary.md`, assert 4 new H3 entries present with EN+CN+Context subsections

*(Framework install: not needed — pytest 9.0.2 already configured.)*

## Security Domain

> Phase 33 is a read-only observability + documentation phase. No new auth, no crypto, no input validation beyond argparse. Security considerations are limited to (1) stats CLI must not leak sensitive data in `--json` output, (2) byte-intact checks must not be bypassable.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — stats CLI inherits operator's existing auth (no new auth surface) |
| V3 Session Management | no | N/A |
| V4 Access Control | yes (weak) | Stats read-only by design; no mutation API exposed. Operator-level access only (single-operator v6 threat model per curator_audit.py docstring) |
| V5 Input Validation | yes | argparse validates `--runs N` (int), `--top N` (int); skill_id positional is free-string but only used as a dict lookup key (never executed, never used in path traversal — `FeedbackStore.summary` parses it into a bucket-key filter, not a path) |
| V6 Cryptography | no | N/A — stats reads but does not verify the sha256 chain (that's `audit-log --verify`'s job) |
| V7 Error Handling | yes | Stats must not crash on empty/partial data — friendly "no feedback yet" message per CONTEXT.md |
| V9 Communications | no | N/A — CLI-only, no network |

### Known Threat Patterns for stats CLI

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| `--json` output leaks operator feedback text | Information Disclosure | FeedbackRecord.correction field may contain operator-authored text. If stats includes recent corrections in output, ensure `--json` doesn't dump raw correction text (counts only). `[ASSUMED — planner should decide]` |
| Malformed bucket file crashes stats | Denial of Service | `FeedbackStore._read_bucket_records` already skips malformed lines with warning `[VERIFIED: feedback_store.py:664-678]` |
| Stats command triggers migration side-effect | Tampering | See Pitfall 4 — use empty `incoming/` in tests; production is safe after P29 has run |

## Sources

### Primary (HIGH confidence)
- `skills/movie-experts/_shared/v86-pipeline-mapping.md` — read end-to-end; confirmed 10-section structure + bilingual convention + metadata header pattern
- `.planning/research/v2-pipeline-design/skills-mapping.yaml` — read end-to-end; confirmed v4_ref_signoffs + v5_ref_signoffs schema (8 fields per entry)
- `agent/feedback_store.py` — read end-to-end; confirmed `summary()` API (line 990) + supersession filtering + bucket key format
- `agent/curator_audit.py` — read end-to-end; confirmed `read_audit(action=, skill=, since=)` API (line 345)
- `hermes_cli/curator.py` — read end-to-end; confirmed P32 `register_cli` extension pattern + lazy-import invariant
- `skills/movie-experts/README.md` — read end-to-end; confirmed corpus tree location + glossary reference + v5.0 section pattern
- `skills/movie-experts/_shared/glossary.md` — read 200 lines; confirmed H3 bilingual header convention (`### CN / EN / alt`)
- `.planning/REQUIREMENTS.md` — confirmed OBS-01/02/03 definitions
- `.planning/ROADMAP.md` Phase 33 section — confirmed SC-1..SC-8 success criteria verbatim
- `.planning/STATE.md` — confirmed Phase 32 fully complete (P31 invariant preserved, FOUND-08 byte-intact at P32 close)

### Secondary (MEDIUM confidence)
- `tests/hermes_cli/test_curator_cli.py` — read 80 lines; confirmed P32 CLI test pattern (class-per-subcommand, `register_cli` subparser assertion)
- `hermes_cli/bundles.py` — confirmed rich.table.Table usage pattern
- `git tag --list 'v5*'` returned `v5.0` — confirmed SC-7/SC-8 baseline tag exists
- `git diff --name-only v5.0..HEAD -- skills/movie-experts/` returned 9 files (all under `_eval/`) — confirmed SC-7 + SC-8 commands work as written

### Tertiary (LOW confidence)
- None. All findings are verified against primary sources.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — `rich==14.3.3` verified in pyproject.toml + 5 existing hermes_cli usages
- Architecture patterns: HIGH — all patterns have direct codebase precedent (P32 register_cli extension, v86 doc structure, skills-mapping schema)
- Stats data sources: HIGH — all three query APIs (`summary`, `read_audit`, `read_queue`) read end-to-end with confirmed signatures
- Pitfalls: HIGH — all 5 pitfalls derived from specific code paths or documented CONTEXT.md specifics
- Architecture doc structure: MEDIUM — CONTEXT.md's "7 sections" is a logical outline; the planner must map it to v86's 10-section actual structure. A4 assumption flagged.

**Research date:** 2026-06-25
**Valid until:** 2026-07-25 (30 days — stable close-out phase, no fast-moving dependencies)

## RESEARCH COMPLETE

**Phase:** 33 - Observability + Integration Close-out
**Confidence:** HIGH

### Key Findings
- **Everything has a direct precedent:** stats CLI mirrors P32 `register_cli` extension; architecture doc mirrors v86-pipeline-mapping.md (10 H2 sections, not 7 — CONTEXT.md's 7 is a logical outline); skills-mapping schema mirrors v5_ref_signoffs (8 fields per entry); glossary mirrors existing H3 bilingual convention.
- **Stats is pure read-only aggregation:** 3 shipped query APIs (`FeedbackStore.summary()`, `read_audit(action="apply")`, `read_queue(status="applied")`) cover all of OBS-01/02/03. Zero new persistence, zero new schema, zero new dependencies.
- **Byte-intact checks work as written in CONTEXT.md:** v5.0 git tag confirmed present; SC-7's `grep -v _eval | grep -v _shared` correctly excludes the 9 files changed under `skills/movie-experts/` (all under `_eval/`); SC-8's explicit 5-file list for v4/v5 refs is precise.
- **Latent gap discovered:** README corpus tree at line 417-424 does not list v5.0's `dreamina-cli-baseline.md` or `v86-pipeline-mapping.md` — they're documented in the v5.0 summary section but not in the corpus tree block. P33 should add the v6 entry; backfilling v5.0 entries is optional (documented non-blocker).
- **Format inconsistency flagged (A2):** Existing glossary uses CN-first headers (`### 运镜 / cinematography`); CONTEXT.md specifies EN-first for v6 entries (`### Feedback Ingestion / 知识反馈采集`). Recommend EN-first for v6 + footer note explaining the shift; flag for operator confirmation.

### File Created
`/data/workspace/hermes-agent/.planning/phases/33-observability-integration-close-out/33-RESEARCH.md`

### Confidence Assessment
| Area | Level | Reason |
|------|-------|--------|
| Standard Stack | HIGH | rich already pinned + used in 5 hermes_cli modules; no new packages |
| Architecture (CLI) | HIGH | P32 register_cli extension pattern read end-to-end at hermes_cli/curator.py:811-1005 |
| Architecture (Doc) | HIGH | v86-pipeline-mapping.md read end-to-end (185 lines, 10 H2 sections confirmed) |
| Pitfalls | HIGH | All 5 pitfalls derived from specific code paths (feedback_store migration, read_audit tz handling, etc.) |
| Stats Data Sources | HIGH | All 3 query APIs read end-to-end with confirmed signatures |

### Open Questions
1. README corpus tree backfill for missing v5.0 entries — recommendation: do NOT backfill (they're in the v5.0 summary section); document as non-blocker.
2. Empty-FeedbackStore exit code — recommendation: exit 0 with friendly message (mirrors P32 `_cmd_audit_log`).
3. Stats side-verification of audit-log sha256 chain — recommendation: no (concern separation; `audit-log --verify` owns this).
4. `--json` output scope — does it include operator-authored correction text? Recommend counts-only to avoid information disclosure (flagged in Security Domain).

### Ready for Planning
Research complete. Planner can now create PLAN.md files. Recommend single-plan structure (3 waves: Wave 1 = stats CLI + tests; Wave 2 = architecture doc + skills-mapping sign-off; Wave 3 = README + glossary + byte-intact verification).

---

**All Open Questions RESOLVED in PLAN.md (Phase 33 plan-phase, 2026-06-25):**

- OQ#1 (README backfill): RESOLVED — NOT backfilling v5.0 entries (they are documented in the v5.0 summary section; documented as non-blocker in Plan 33-03 D-no-backfill).
- OQ#2 (empty-store exit code): RESOLVED — exit 0 with friendly message, mirrors P32 _cmd_audit_log pattern (curator.py:659-661). Encoded in Plan 33-01 D-empty-store.
- OQ#3 (audit chain side check): RESOLVED — NO. Concern separation: `hermes curator audit-log --verify` owns chain verification; stats stays read-only observability.
- OQ#4 (--json output scope): RESOLVED — counts-only. No correction text / output_snapshot / feedback_ids leakage. Encoded in Plan 33-01 D-json-counts-only + TestJsonOutput assertion.
