# Standard Skill Directory Layout — Movie-Experts Suite v2

**Purpose:** Define the canonical filesystem layout for every expert under `skills/movie-experts/`. All 14 existing experts and all 4 new experts MUST conform to this layout. Drift breaks the skill loader (`tools/skills_tool.py`), cross-expert references, and the eval harness.

**Related:** CLAUDE.md "Skill File Conventions" section; `agent/skill_utils.py` (frontmatter parser); `tools/skills_tool.py` (loader).

**Last updated:** 2026-06-15 (Phase 0 skeleton)

---

## Required files

Every expert directory MUST contain:

| File | Purpose | Discovered by loader? |
|------|---------|----------------------|
| `SKILL.md` | The skill itself — YAML frontmatter + markdown body. Uppercase filename is MANDATORY (loader skips lowercase `skill.md`). | Yes — primary discovery target. |
| `references/*.md` | Curated RAG corpus. One file per atomic domain. Populated in Phase 3 (top-4) and Phase 5 (remaining 10 + PROD). | No — surfaced via `## References` table in SKILL.md body. |
| `_eval/prompts/<expert>.yaml` | Benchmark prompts for the LLM-as-judge harness. Populated per-phase. | No — consumed only by `_eval/runner.py` at suite level. |

## Optional files

| File | Purpose | When to include |
|------|---------|----------------|
| `_eval/baseline/SKILL.md` | Snapshot of SKILL.md captured at baseline tag (e.g., `eval-baseline-v1`). | Always — captured by `_eval/snapshot.py` once before refactor begins. |
| `references/LICENSE.md` | Per-ref copyright / license attribution. | MANDATORY if ref cites creator-licensed samples or fair-use excerpts > 30s. |
| `GAP-REPORT.md` | Audit findings from Phase 0. | Produced once; not refreshed unless a re-audit is requested. |

## Forbidden

- **Python / JS code in skill directories.** Eval scripts live at `skills/movie-experts/_eval/` (suite level), NOT per-expert. Skills are pure markdown per PROJECT.md constraint.
- **Lowercase `skill.md`.** Loader only discovers uppercase `SKILL.md` (see CLAUDE.md "Skill File Conventions").
- **Symlinks** out of the expert directory (breaks Windows compatibility).
- **Binary assets** (images, audio, video) committed directly. Use external URLs in refs or document as user-deployed assets.

## Naming conventions

- **expert_id** MUST match directory name. Example: `skills/movie-experts/style_genome/` → `expert_id: style_genome`.
- **Directory name** MUST be `snake_case`, lowercase. Example: `style_genome`, not `StyleGenome` or `style-genome`.
- **expert_id values for existing 14 are FROZEN** (FOUND-08 hard rule). Refactor edits prompt body, metrics, thresholds — NEVER the identifier.
- **Reference files** use `kebab-case.md`. Example: `references/save-the-cat-beat-sheet.md`, not `SaveTheCat.md`.
- **Eval prompt files** use `<expert>.yaml` matching expert_id. Example: `_eval/prompts/screenplay.yaml`.

## Frontmatter schema

Every `SKILL.md` frontmatter MUST include these fields (see CLAUDE.md "Skill File Conventions" for full reference):

```yaml
---
name: <expert_id>                    # MUST match directory name
description: "<one-line EN+CN summary>"
version: <semver>                    # Bump on prompt-body changes; NEVER bump for identifier changes
author: <author>
license: <license>
platforms: [<platforms>]
prerequisites:
  tools: [<hermes tool names>]
metadata:
  hermes:
    tags: [<lowercase hyphenated tags>]
    related_skills: [<expert_id list>]   # Drives DAG ordering + cross-skill recommendation
    expert_id: <expert_id>               # FROZEN for existing 14 (FOUND-08)
    metrics: [<quality-dimension list>]  # Consumed by eval pipelines
---
```

**Mandatory frontmatter fields:** `name`, `description`, `version`, `metadata.hermes.{tags, related_skills, expert_id, metrics}`.

**Optional frontmatter fields:** `author`, `license`, `platforms`, `prerequisites.tools`.

## Body section structure (canonical order)

Every SKILL.md body SHOULD follow this section order (established by existing 14; new experts inherit):

1. `# <Name> Expert (<Chinese name>)` — H1 with bilingual title.
2. `## When to use this skill` — trigger conditions.
3. `## References` — References table (FOUND-07; columns: Ref / When to Read / Contents). Populated by Phase 3.
4. `## Role & Philosophy` — 3-5 bullets.
5. `## Core Capabilities` — bullet list.
6. `## Output Format` — bulleted list of JSON artifact filenames.
7. `## Key Parameters` — nested H3 subsections per parameter group.
8. `## Style Rules` — craft constraints.
9. `## Workflow` — numbered steps.
10. `## Quality Thresholds` — markdown table.
11. `## Collaboration` — `<- upstream` / `-> downstream` arrows.
12. `## What NOT to do` — anti-patterns.

**`## References` table placement** is load-bearing: it MUST appear immediately after `## When to use this skill` so that downstream ref-authoring tooling (Phase 3) can locate it deterministically across all experts.

## Example tree (hypothetical expert)

```
skills/movie-experts/<expert_id>/
├── SKILL.md                              # The skill (uppercase, mandatory)
├── GAP-REPORT.md                         # Phase 0 audit findings
├── references/
│   ├── <topic-a>.md                      # Curated ref (kebab-case)
│   ├── <topic-b>.md
│   ├── <topic-c>.md
│   └── LICENSE.md                        # If any ref cites licensed material
└── _eval/
    ├── baseline/
    │   └── SKILL.md                      # Baseline snapshot (captured by snapshot.py)
    └── prompts/
        └── <expert_id>.yaml              # Benchmark prompts
```

## Cross-cutting rules

- **Provider-agnostic RAG:** SKILL.md body MUST use the provider-agnostic invocation pattern documented in `_shared/RAG-INVOCATION-PATTERN.md`. Never hardcode `fact_store` / `mem0_search` / `cosyvoice_api` tool names in prompt body.
- **Bilingual format:** EN YAML structure (keys, metadata) + CN prose where 短剧 cultural context warrants. See `_shared/glossary.md` for canonical EN↔CN term mapping.
- **Copyright:** Every ref MUST carry a `Source:` + `Copyright:` + `Last-verified:` header. Reference anatomy (Source / Copyright / Last-verified / Summary / Heuristics columns) is defined in this document's "Reference file anatomy" section below.

## Reference file anatomy

Each `references/<topic>.md` file MUST start with this header block:

```markdown
# <Topic Title>

**Source:** <book title / paper / URL / interview>
**Copyright:** <© Year Holder | Public Domain | Fair Use | Licensed>
**Last-verified:** YYYY-MM-DD

## Summary

<2-3 sentence overview of what this ref covers>

## Heuristics

<Concrete numbers / rules / thresholds — NOT Wikipedia summaries. Each heuristic must contain at least one specific value a base LLM would not produce from training data alone.>
```

Refresh cadence: every `references/*.md` is re-verified quarterly. Stale refs (Last-verified > 90 days) are flagged in audit reports via `scripts/verify_skill_references.py`.
- **No phantom model names:** Use `<video_gen_primary>` / `<image_gen_primary>` / `<audio_gen_primary>` placeholders in SKILL.md body; specific model names appear only in `references/*.md` (which are versioned and can be refreshed). See `_shared/known-external-models.yaml` for the allowlist.
