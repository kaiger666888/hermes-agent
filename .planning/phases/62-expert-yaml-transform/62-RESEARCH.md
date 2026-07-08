# Phase 62: EXPERT-YAML-TRANSFORM - Research

**Researched:** 2026-07-08
**Domain:** SKILL.md → agent YAML transform (v10.0 04-MIGRATION-PATH §2 rules execution)
**Confidence:** HIGH (all findings verified against schema + 9 shipped YAMLs + source SKILL.md files)

## Summary

Phase 62 是一个纯执行型 transform phase:把 12 个 active expert 的 SKILL.md(在 `kais-hermes-skills` repo 只读)transform 成 `~/.hermes/agents/{name}.agent.yaml`,达成 21 total(9 已 ship + 12 新增)。Transform 规则已经由 v10.0 `04-MIGRATION-PATH.md §2` 75-cell table 完全锁定,schema 由 `agents-schema.yaml`(Draft 2020-12,18 camelCase fields,`additionalProperties: false`)完全锁定,9 个已 ship YAML 提供了 canonical 结构模板。本 phase 的技术风险很低 —— 没有新代码、没有新 schema、没有新 pattern。

**但有 3 个关键 pitfall 必须在 plan 中显式处理:**

1. **SC#3 要求的 `source_sha` + `transform_rule_id` + `transform_timestamp` 字段 NOT IN SCHEMA。** Schema 的 `lineage` $def 有 `additionalProperties: false`,只允许 5 个 sub-fields(`derived_from_skill_id` / `derived_from_repo` / `transform_date` / `transform_notes` / `skill_sha256`)。如果把 SC#3 要求的 3 个新字段直接加到 lineage,会 **SC#2 byte-fail**。正确做法:`source_sha` → 用现有 `skill_sha256` 字段(语义等价);`transform_rule_id` + `transform_timestamp` → 写进 `transform_notes` 文本(free-text,cite rule IDs)。SC#3 的 grep check 必须调整为 grep `skill_sha256` + grep `transform_notes` 中的 rule ID 字符串。

2. **`sub_steps` NOT IN SCHEMA。** `visual_executor` SKILL.md frontmatter 有 `sub_steps: [drawer, animator]`,但 schema top-level `additionalProperties: false` 会拒绝 `sub_steps` 字段。已 ship 的 `audio_pipeline.agent.yaml`(同样有 6 sub_steps)的处理方式:把 sub_steps 信息写进 `persona` 文本 + `description` 文本,**不**作为独立 YAML 字段。visual_executor 必须照此 pattern。

3. **`scene_builder` is BOTH a transform target AND a deprecated name referenced by peers。** `04-MIGRATION-PATH §2.7` 说 scene_builder 被 cinematographer absorbed (Phase 17)。但 scene_builder 在本 phase 的 12-transform list 里(它有独立 SKILL.md + expert_id)。同时 performer + storyboard_designer 的 `related_skills` 列表里 cite 了 `scene_builder`。Planner 必须决定:在 related_agents 里保留 `scene_builder`(因为它即将成为 agent)还是 map 到 `cinematographer`(per §2.7 absorption rule)。推荐:保留 `scene_builder`(它是 21-agent DAG 的合法成员,Phase 63 会 load 它),在 transform_notes 里 cite §2.7 absorption context。

**Primary recommendation:** 按 9 个已 ship YAML 的 byte-compatible 结构,follow §2 per-expert rules,为 12 个 expert 各写一个 `.agent.yaml`。每个 YAML 走同一个 6-step pipeline:read SKILL.md → compute SHA-256 → apply §2 rules → draft persona → dump YAML (PyYAML, UTF-8, block style) → validate via `jsonschema.Draft202012Validator`。

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| SKILL.md source read (only) | External repo (kais-hermes-skills) | — | Lineage invariants L1-L6 (Phase 48-49): source is read-only |
| SHA-256 computation | Transform script (Python hashlib) | — | Computed at transform time, frozen in `lineage.skill_sha256` |
| Persona rewrite (SKILL body → first-person) | Transform author (manual + Claude) | — | Per §2.0 disposition class "REWRITE" — cannot be automated; requires per-expert domain judgment |
| YAML field population (17 copy/derive fields) | Transform author | — | Mechanical copy from frontmatter + §2 rules |
| Schema validation | `agent/registry_loader.py` (existing v11.0) | `jsonschema.Draft202012Validator` | Loader already validates at load time; Phase 62 pre-validates before write |
| Transform log emission | Transform script → `transform_notes` field | — | Per-agent rule IDs cited in free-text `transform_notes` (only schema-allowed location) |
| Write YAML to `~/.hermes/agents/` | Transform author (Write tool) | — | Target dir already has 9 YAMLs; flat glob (no subdirs) per registry_loader |

## User Constraints (from CONTEXT.md)

### Locked Decisions (from CONTEXT.md + carried from v10.0-v12.0)

- **Schema:** `agents-schema.yaml` Draft 2020-12,18 fields camelCase(Phase 45 stable)。`byte-pass jsonschema.Draft202012Validator.validate()` 是 SC#2 的硬约束
- **Lineage 字段必填:** schema-required `derived_from_skill_id` + `derived_from_repo` + `transform_date` + `skill_sha256`;SC#3 要求的 `source_sha` + `transform_rule_id` + `transform_timestamp` 语义通过 `skill_sha256` + `transform_notes` 表达(见 §Common Pitfalls #1)
- **default_invocation:** `mcp_tool`(12 个全部 active expert)— 与已 ship 的 9 个 active expert YAML 一致
- **round_table_eligible:** `true`(12 个全部 active expert)
- **memory_scope:** `per_agent`(v11.0 default)
- **Source SKILL.md 只读:** lineage invariants L1-L6(Phase 48-49)— 计算 SHA 但不修改源文件
- **Source repo path:** `/data/workspace/kais-hermes-skills/skills/movie-experts/{name}/SKILL.md`(post-v9.0 cross-repo migration,commit f10495332)

### Claude's Discretion

All implementation choices are at Claude's discretion — pure infrastructure phase. Use ROADMAP phase goal + success criteria + `04-MIGRATION-PATH.md §2` 75-cell transform table + existing 9 ship'd agent YAMLs as canonical patterns to guide decisions.

### Deferred Ideas (OUT OF SCOPE)

None — infrastructure phase, scope is fully captured by ROADMAP SCs + 04-MIGRATION-PATH.md §2 transform rules.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EXPERT-01 | 12 active expert SKILL.md → `~/.hermes/agents/{name}.agent.yaml` 全量 transform,严格按 v10.0 `04-MIGRATION-PATH.md` §2 75-cell table 规则。SKILL.md 只读 | §Architecture Patterns + §Per-Expert Transform Mapping 表(12 rows)提供 rule IDs + field overrides;§Code Examples 提供 SHA + YAML dump 骨架 |
| EXPERT-02 | 12 个新 YAML 全部 byte-pass `agents-schema.yaml` Draft 2020-12 验证(`jsonschema.Draft202012Validator.validate()`) | §Code Examples 提供 validation snippet;§Common Pitfalls #1/#2 警告 `source_sha`/`transform_rule_id`/`sub_steps` 不能作为独立字段(会 schema-fail) |
| EXPERT-03 | 12 个新 YAML lineage 字段必须 populated(source SHA + transform rule ID + timestamp),支持审计回溯到原 SKILL.md | §Schema Field Reference 解释 lineage 5-field 硬约束;§Common Pitfalls #1 给出 SC#3→schema 兼容的 mapping 方案(`skill_sha256` + `transform_notes` free-text) |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `PyYAML` | 6.0.3 [VERIFIED: pyproject.toml:52] | YAML dump (block style, UTF-8) | Hermes standard for all YAML; 9 shipped YAMLs dumped with PyYAML |
| `jsonschema` | 4.26.0 [VERIFIED: pip show jsonschema] | `Draft202012Validator.validate()` schema check | Used by `agent/registry_loader.py` (v11.0 INFRA-01); SC#2 hard constraint |
| `hashlib` (stdlib) | Python 3.11+ [VERIFIED: stdlib] | SHA-256 of source SKILL.md content | `hashlib.sha256(content.encode("utf-8")).hexdigest()` — encoding explicit per CLAUDE.md PLW1514 |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pathlib.Path` (stdlib) | Python 3.11+ | File path handling | Read source SKILL.md, write target YAML |
| `ruamel.yaml` | 0.18.17 [VERIFIED: pyproject.toml:53] | Optional: round-trip YAML preserving comments | NOT needed for Phase 62 (new files, no comment preservation); PyYAML sufficient |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyYAML dump | ruamel.yaml dump | ruamel preserves CJK better in block scalars but 9 shipped YAMLs use PyYAML — byte-compat argues for PyYAML |
| Manual persona rewrite | LLM-assisted rewrite | §2 mandates per-expert domain judgment; Claude can draft but operator must verify persona captures load-bearing contracts (HOOK-09, hard-gate framing, etc.) |

**Installation:** No new packages needed — all 3 core libraries already in `pyproject.toml` core deps.

**Version verification:**
```
PyYAML 6.0.3 — confirmed via python3 -c "import yaml; print(yaml.__version__)"
jsonschema 4.26.0 — confirmed via python3 -c "import jsonschema; print(jsonschema.__version__)"
hashlib — stdlib, no version check needed
Draft202012Validator — confirmed available via from jsonschema import Draft202012Validator
```

## Package Legitimacy Audit

> Phase 62 installs **zero** new packages. All libraries are pre-existing in `pyproject.toml` core deps.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| PyYAML | PyPI | ~14 yrs | 500M+/mo | github.com/yaml/pyyaml | n/a (pre-existing) | Approved (no install) |
| jsonschema | PyPI | ~12 yrs | 300M+/mo | github.com/python-jsonschema/jsonschema | n/a (pre-existing) | Approved (no install) |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*No slopcheck run needed — zero new package installs in this phase.*

## Architecture Patterns

### System Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────────────┐
│  kais-hermes-skills repo (READ-ONLY — lineage L1-L6)                │
│  skills/movie-experts/{name}/SKILL.md                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Frontmatter: name, description, version, platforms,        │   │
│  │  prerequisites.tools, metadata.hermes.{tags, related_skills,│   │
│  │  expert_id, metrics}, optional: sub_steps, aliases          │   │
│  │  Body: ## When to use / Role / Core Capabilities / Output / │   │
│  │  Key Parameters / References table                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           │ 1. Read SKILL.md (UTF-8)
                           │ 2. Compute SHA-256 of content
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Transform Pipeline (per expert, 12 iterations)                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Step 3: Apply 04-MIGRATION-PATH §2 rules (5 fields)        │   │
│  │    - tools: §2.X row "tools" (4 patterns: analysis-only /   │   │
│  │      dreamina_cli / write_file / write_file+patch)          │   │
│  │    - persona: §2.X row "persona" (REWRITE to first-person)  │   │
│  │    - refs: init [] (follow 9 shipped YAML convention —      │   │
│  │      refs surfaced in persona text, not as paths)           │   │
│  │    - related_agents: copy related_skills, apply FOUND-08    │   │
│  │      mapping (scene_builder → keep as-is since it becomes   │   │
│  │      an agent in this same phase)                           │   │
│  │    - lineage.skill_sha256: computed SHA-256                 │   │
│  │  Step 4: Apply uniform defaults (13 copy/derive fields)     │   │
│  │    - version: "1.0.0" (semver)                              │   │
│  │    - memory_scope: per_agent                                │   │
│  │    - evolution_log: []                                      │   │
│  │    - fitness_score: null                                    │   │
│  │    - round_table_eligible: true                             │   │
│  │    - default_invocation: mcp_tool                           │   │
│  │    - platforms: [linux, macos, windows]                     │   │
│  │    - prerequisites: copy from SKILL frontmatter             │   │
│  │    - tags/expert_id/metrics: copy verbatim                  │   │
│  │  Step 5: Dump YAML (PyYAML, UTF-8, block style, sort_keys=  │   │
│  │    False to match 9 shipped YAML field order)               │   │
│  └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           │ 6. Validate via Draft202012Validator
                           │    (must exit 0 — SC#2)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ~/.hermes/agents/{name}.agent.yaml (21 total after phase)          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  9 shipped (untouched): screenplay, style_genome, editor,   │   │
│  │    cinematographer, character_designer, continuity_auditor, │   │
│  │    hook_retention, theory_critic, audio_pipeline            │   │
│  │  12 new (this phase): animation_studio, colorist,           │   │
│  │    compliance_gate, creative_source, documentary_maker,     │   │
│  │    performer, production, prompt_injector, scene_builder,   │   │
│  │    script_auditor, storyboard_designer, visual_executor     │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure

Phase 62 不产生新 Python 模块(纯 YAML 产出)。文件布局:

```
~/.hermes/agents/                          # Target (21 total after phase)
├── screenplay.agent.yaml                  # shipped v11.0 (untouched)
├── style_genome.agent.yaml                # shipped v11.0 (untouched)
├── ... (7 more shipped)
├── animation_studio.agent.yaml            # NEW Phase 62
├── colorist.agent.yaml                    # NEW Phase 62
├── compliance_gate.agent.yaml             # NEW Phase 62
├── creative_source.agent.yaml             # NEW Phase 62
├── documentary_maker.agent.yaml           # NEW Phase 62
├── performer.agent.yaml                   # NEW Phase 62
├── production.agent.yaml                  # NEW Phase 62
├── prompt_injector.agent.yaml             # NEW Phase 62
├── scene_builder.agent.yaml               # NEW Phase 62
├── script_auditor.agent.yaml              # NEW Phase 62
├── storyboard_designer.agent.yaml         # NEW Phase 62
└── visual_executor.agent.yaml             # NEW Phase 62

# Validation script (optional, one-off — can be inline bash/python)
scripts/validate_phase62_yamls.py         # Optional: batch-validate 12 new YAMLs
```

### Pattern 1: Per-Expert Transform (6-Step Pipeline)

**What:** Every expert follows the same 6-step transform pipeline; §2 provides per-expert rule overrides for 5 fields.

**When to use:** Once per expert (12 times total).

**Example (skeleton):**
```python
# Source: 04-MIGRATION-PATH.md §2.1 (5-field mapping 通则) + §6.1 ARCHITECTURE
# Verified against 9 shipped YAMLs at ~/.hermes/agents/
import hashlib
import jsonschema
import yaml
from pathlib import Path

SOURCE_REPO = Path("/data/workspace/kais-hermes-skills/skills/movie-experts")
TARGET_DIR = Path.home() / ".hermes" / "agents"
SCHEMA_PATH = Path(".planning/research/v10-orchestrator-design/agents-schema.yaml")

def transform_one_expert(expert_name: str, persona_text: str, tools_list: list[str],
                         related_agents_list: list[str], transform_notes: str) -> None:
    # Step 1: Read source SKILL.md
    skill_path = SOURCE_REPO / expert_name / "SKILL.md"
    skill_content = skill_path.read_text(encoding="utf-8")

    # Step 2: Compute SHA-256 (encoding explicit per CLAUDE.md PLW1514)
    skill_sha256 = hashlib.sha256(skill_content.encode("utf-8")).hexdigest()

    # Step 3-4: Build agent dict (apply §2 rules via function params)
    agent = {
        "name": expert_name,
        "description": "...",  # copy from SKILL frontmatter
        "version": "1.0.0",
        "persona": persona_text,  # §2 per-expert rewrite
        "tools": tools_list,  # §2 per-expert tools whitelist
        "memory_scope": "per_agent",
        "lineage": {
            "derived_from_skill_id": expert_name,
            "derived_from_repo": "kais-hermes-skills",
            "transform_date": "2026-07-08",
            "transform_notes": transform_notes,  # §2 rule IDs cited here
            "skill_sha256": skill_sha256,  # SC#3 source_sha equivalent
        },
        "refs": [],  # follow 9-shipped convention: empty, refs in persona
        "tags": [...],  # copy from SKILL metadata.hermes.tags
        "expert_id": expert_name,  # FOUND-08 preserved
        "metrics": [...],  # copy from SKILL metadata.hermes.metrics
        "prerequisites": {"tools": ["hermes_llm"]},  # copy from SKILL
        "related_agents": related_agents_list,  # SKILL related_skills renamed
        "evolution_log": [],
        "fitness_score": None,
        "platforms": ["linux", "macos", "windows"],
        "round_table_eligible": True,
        "default_invocation": "mcp_tool",
    }

    # Step 5: Dump YAML (PyYAML, UTF-8, block style)
    target_path = TARGET_DIR / f"{expert_name}.agent.yaml"
    with open(target_path, "w", encoding="utf-8") as f:
        yaml.dump(agent, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True, width=100)

    # Step 6: Validate
    schema = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(agent))
    if errors:
        raise ValueError(f"{expert_name}: {len(errors)} schema errors: "
                         f"{errors[0].message}")
```

### Pattern 2: Persona Rewrite (First-Person Expert Voice)

**What:** SKILL.md body is imperative-second-person ("You are X. Do Y.") injected as USER message. Agent persona is first-person ("I am X. I do Y.") injected as SYSTEM-prompt fragment. This is THE load-bearing difference per agents-schema.yaml §2.4.

**When to use:** Every expert — but content is per-expert (cite anchor refs, declare contracts, defer to peers).

**Example (from shipped screenplay.agent.yaml lines 5-18):**
```yaml
# Source: ~/.hermes/agents/screenplay.agent.yaml (shipped v11.0, byte-verified)
persona: 'I am the Screenplay Expert (剧本专家). I write scene-level scripts with
  scene-by-scene emotion_curve marker arrays — hooks, payoffs, and cliffhangers are
  first-class JSON fields in my output, not afterthoughts. My structural backbone is
  Blake Snyder''s 15-beat Save-the-Cat beat sheet, Robert McKee''s scene-level
  value-shift framework, and Ed Tan''s interest-formula psychology.

  HOOK-09 emotion_curve marker arrays remain contract-load-bearing: every
  scene_breakdown entry MUST carry its own per-scene emotion_curve, and the
  top-level emotion_curve array MUST be non-empty — downstream storyboard Step
  6.5 + visual_executor Step 7 cross-reference these arrays for pacing decisions.'
```

**Rules:**
1. Always first-person ("I am", "I do", "My output is")
2. Cite 1-2 anchor refs by name (e.g., "Snyder 15-beat", "McKee value-shift")
3. Declare load-bearing contracts in-line (e.g., "HOOK-09 marker arrays remain contract-load-bearing")
4. Defer to peers on their domains (e.g., "I defer to cinematographer on shot intent")
5. Never generate full output unprompted (contribute slice when orchestrator asks)
6. For hard-gate experts (compliance_gate, script_auditor, continuity_auditor): declare "I am hard-gate / I can block pipeline"
7. For visual_executor: declare "I do NOT decide intent" (intent-vs-execution split)

### Anti-Patterns to Avoid

- **Copy SKILL.md body verbatim into persona:** SKILL body is second-person imperative; persona must be first-person. [CITED: agents-schema.yaml §2.4]
- **Add `sub_steps` as a top-level YAML field:** `additionalProperties: false` in schema rejects it. Put sub_steps info in persona + description text (audio_pipeline shipped YAML does this). [VERIFIED: schema line 42 + audio_pipeline.agent.yaml]
- **Add `source_sha` / `transform_rule_id` / `transform_timestamp` as lineage sub-fields:** Lineage $def has `additionalProperties: false` with only 5 allowed fields. Use `skill_sha256` + `transform_notes` free-text instead. [VERIFIED: schema $defs/Lineage]
- **Populate `refs` with path list:** All 9 shipped YAMLs have `refs: []`. Refs are surfaced in persona text by name, not as file paths. [VERIFIED: grep across 9 shipped YAMLs]
- **Hand-edit shipped YAMLs:** CONTEXT.md says "修改已 ship 的 9 个 agent YAML(它们 lineage 已 locked,不动)". [CITED: 62-CONTEXT.md]
- **Modify source SKILL.md:** Lineage invariants L1-L6 (Phase 48-49). Source is read-only. [CITED: 62-CONTEXT.md]

## Schema Field Reference (18 fields, agents-schema.yaml)

> **Source:** `.planning/research/v10-orchestrator-design/agents-schema.yaml` [VERIFIED: read + validated against 9 shipped YAMLs]

### Required Fields (7 — schema line 41)

| # | Field | Type | Constraint | Source / Notes |
|---|-------|------|------------|----------------|
| 1 | `name` | string | pattern `^[a-z0-9_-]+$`; MUST match filename stem | Copy from SKILL `name`; T-52-03 filename invariant enforced by registry_loader |
| 2 | `description` | string | minLength 10 | Copy from SKILL `description`; refine if needed |
| 3 | `version` | string | semver `^[0-9]+\.[0-9]+\.[0-9]+$` | Init `"1.0.0"` on first transform (distinct from SKILL version) |
| 4 | `persona` | string | (no constraint) | **REWRITE** from SKILL body — first-person expert voice (§Pattern 2) |
| 5 | `tools` | array[string] | minItems 1 | **DERIVE** per §2 rules — 4 patterns (analysis-only / dreamina_cli / write_file / write_file+patch) |
| 6 | `memory_scope` | string | enum `[shared, per_agent, project_scoped]` | Default `per_agent` for all 12 |
| 7 | `lineage` | object | see Lineage $def below | **NEW** — computed at transform time |

### Optional Fields (11 + 1 optional block)

| # | Field | Type | Default | Source / Notes |
|---|-------|------|---------|----------------|
| 8 | `memory` | object | `{}` | Optional thresholds block (max_records / confidence_threshold_for_promotion / evidence_chain_min_for_acceptance). **9 shipped YAMLs omit this** — Phase 62 should also omit (use schema defaults). [VERIFIED] |
| 9 | `refs` | array[string] | `[]` | **FLATTEN** from SKILL References table — but **9 shipped YAMLs all have `refs: []`** (refs surfaced in persona text instead). Follow shipped convention. |
| 10 | `tags` | array[string] | — | pattern `^[a-z0-9-]+$` per item. **COPY** verbatim from SKILL `metadata.hermes.tags` |
| 11 | `expert_id` | string | — | **COPY** verbatim from SKILL `metadata.hermes.expert_id` (FOUND-08 preserved) |
| 12 | `metrics` | array[string] | — | **COPY** verbatim from SKILL `metadata.hermes.metrics` |
| 13 | `prerequisites` | object | — | **COPY** from SKILL `prerequisites` (sub-fields: tools/skills/env arrays). Distinct from runtime `tools` |
| 14 | `related_agents` | array[string] | — | pattern `^[a-z0-9_-]+$` per item. **COPY-with-rename** from `metadata.hermes.related_skills` → `related_agents`. Apply FOUND-08 mapping if needed. |
| 15 | `evolution_log` | array | `[]` | Init `[]` (curator-managed, append-only). DO NOT hand-edit. |
| 16 | `fitness_score` | number\|null | `null` | Init `null` (curator-computed). NOT operator-set. |
| 17 | `platforms` | array[string] | `[linux, macos, windows]` | enum `[linux, macos, windows, termux]`. **COPY** from SKILL `platforms` |
| 18 | `round_table_eligible` | boolean | `true` | All 12 = `true` (active experts) |
| 19 | `default_invocation` | string | `mcp_tool` | enum `[mcp_tool, skill_fallback, disabled]`. All 12 = `mcp_tool` (active experts, not redirect stubs) |

### Lineage $def (sub-fields — schema lines 351-380)

| Field | Required | Type | Constraint | Phase 62 Usage |
|-------|----------|------|------------|----------------|
| `derived_from_skill_id` | YES | string | — | = expert_name (e.g., `"visual_executor"`) |
| `derived_from_repo` | YES | string | — | = `"kais-hermes-skills"` |
| `transform_date` | YES | string | format `date` (ISO) | = `"2026-07-08"` (transform execution date) |
| `transform_notes` | NO | string | free-text | **USE THIS for SC#3 rule ID + timestamp citation** (see Common Pitfalls #1) |
| `skill_sha256` | YES | string | pattern `^[a-f0-9]{64}$` | = SHA-256 hex of source SKILL.md content |

**Critical:** Lineage has `additionalProperties: false`. You CANNOT add `source_sha` / `transform_rule_id` / `transform_timestamp` as new sub-fields. [VERIFIED: schema line 354]

## Per-Expert Transform Mapping (12 rows)

> **Source:** `04-MIGRATION-PATH.md §2.2-§2.16` (75-cell table) + source SKILL.md frontmatter [VERIFIED: read all 12 source SKILL.md frontmatters + cross-referenced §2]

| # | Expert | §2 Rule ID | tools | persona key contracts | related_agents (from SKILL) | Edge Case Notes |
|---|--------|------------|-------|----------------------|-----------------------------|-----------------|
| 1 | `animation_studio` | §2 (not in §2.2-§2.16 — new expert) | `[hermes_llm, read_file, search_files]` | Disney 4-stage system, 12-stage pipeline, cross-cultural (花木兰); cite Story Structure Score metric | `[screenplay, visual_executor, colorist, cinematographer, audio_pipeline, hook_retention]` | animation_studio is NOT in §2.2-§2.16 (those cover v10.0's 15-expert list). Use §2.1 default rules + SKILL.md frontmatter as source of truth. |
| 2 | `colorist` | §2.14 | `[hermes_llm, read_file, search_files, write_file]` | CxSxZ color narrative + LUT plan; integrate with visual_executor at Step 7; defer to style_genome on 5D vector | `[screenplay, style_genome, visual_executor, continuity_auditor, production, theory_critic, cinematographer]` | **+write_file** for LUT plan artifacts. §2.14 edge case: Step 7 integration with visual_executor is load-bearing. |
| 3 | `compliance_gate` | §2.15 | `[hermes_llm, read_file, search_files]` | Hard-gate red-line authority; 3 v9.0 red-lines (redline_emotion_desensitize / redline_no_cold_open / redline_unfinished_ending); `default_invocation: mcp_tool` per CONTEXT locked decision (NOT `disabled` — CONTEXT overrides §2.15/§3.6 recommendation) | `[screenplay, editor, hook_retention, style_genome, visual_executor]` | **Context override:** §2.15 + §3.6 recommend `disabled` initially, but CONTEXT.md locks `default_invocation: mcp_tool` for all 12. Follow CONTEXT (locked decision). |
| 4 | `creative_source` | §2.3 | `[hermes_llm, read_file, search_files, write_file]` | Snowflake Method 10-step + SCAMPER 7-verb; outputs StoryKernel JSON; declare output format explicitly | `[style_genome, screenplay, hook_retention, compliance_gate, prompt_injector]` | **+write_file** for StoryKernel JSON. **FILTER `topic_curator`** from related_agents — topic_curator skill does NOT exist (future stub referenced in SKILL). [VERIFIED: ls kais-hermes-skills/skills/movie-experts/topic_curator → not found] |
| 5 | `documentary_maker` | §2 (not in §2.2-§2.16 — new expert) | `[hermes_llm, read_file, search_files]` | Documentary types (6) + 4 schools (Flaherty/Vertov/Grierson/Direct-Vérité); ethnographic methods | `[screenplay, cinematographer, editor, production, compliance_gate, theory_critic]` | Use §2.1 default rules + SKILL.md frontmatter. Analysis-only tools (no write). |
| 6 | `performer` | §2 (not in §2.2-§2.16 — new expert) | `[hermes_llm, read_file, search_files]` | Performance-4D matrix (ExBxSxP) + Stanislavski ExB + Laban Effort + Meisner; cite Emotion Accuracy metric | `[screenplay, continuity_auditor, scene_builder, editor, visual_executor, audio_pipeline, style_genome, production]` | Use §2.1 default rules. **related_skills lists `scene_builder`** — keep as-is (scene_builder becomes agent in this same phase). |
| 7 | `production` | §2 (not in §2.2-§2.16 — new expert) | `[hermes_llm, read_file, search_files]` | AI-relevant subset: LoRA / wardrobe / lighting / GPU budget / asset reuse; cite Budget Adherence metric | `[character_designer, visual_executor, continuity_auditor, colorist, compliance_gate, cinematographer, audio_pipeline, theory_critic, documentary_maker]` | Use §2.1 default rules. Analysis-only (advisory role — outputs specs as data, not file writes). |
| 8 | `prompt_injector` | §2.9 | `[hermes_llm, read_file, search_files, write_file]` | Bilingual prompt translator (camera-move intent → dreamina/Runway/Kling/Veo/Sora tokens); AI-native expert | `[creative_source, cinematographer, visual_executor, audio_pipeline]` | **+write_file** for prompt JSON artifacts. §2.9 AI-native marker: derived_from_skill_id should be `prompt_injector` (SKILL.md exists post-v3.0). NOT null. [VERIFIED: ls prompt_injector/SKILL.md → exists] |
| 9 | `scene_builder` | §2.7 (absorption context — but scene_builder is a transform target here) | `[hermes_llm, read_file, search_files]` | FxSxA scene matrix + Blender 4.x previz + Pallasmaa space-as-character; cite Narrative Space Match metric | `[screenplay, style_genome, colorist, performer, editor, visual_executor, audio_pipeline, continuity_auditor, cinematographer, production]` | **Ambiguity:** §2.7 says scene_builder was absorbed into cinematographer (Phase 17). BUT scene_builder has its own SKILL.md + expert_id + is in our 12-transform list. Resolution: transform it as a standalone agent (it has distinct content — FxSxA matrix, Blender previz, Pallasmaa doctrine — that cinematographer does NOT cover). Cite absorption context in transform_notes. |
| 10 | `script_auditor` | §2.5 | `[hermes_llm, read_file, search_files]` | 5-dim critic (NOT creative writer); predicts completion %; hard-gates on `< 65% predicted_completion`; critic-not-writer framing is load-bearing | `[screenplay, hook_retention, editor, style_genome, compliance_gate]` | Analysis-only (no write). §2.5 edge case: persona MUST say "I am NOT a creative writer" to prevent model drift. |
| 11 | `storyboard_designer` | §2 (not in §2.2-§2.16 — new expert) | `[hermes_llm, read_file, search_files]` | Shot decomposition + 4D anchoring (depth/identity/lighting/temporal); decoupled from cinematographer (cinematographer = rules, storyboard_designer = executable shot list) | `[screenplay, cinematographer, scene_builder, character_designer, visual_executor, editor, continuity_auditor]` | Use §2.1 default rules. Analysis-only. **related_skills lists `scene_builder`** — keep as-is. |
| 12 | `visual_executor` | §2.10 | `[hermes_llm, dreamina_cli, read_file, write_file, patch]` | Dreamina CLI executor (text2image / image2image / multimodal2video); sub_steps [drawer, animator] go in persona + description text (NOT as YAML field); intent-vs-execution split load-bearing | `[screenplay, continuity_auditor, colorist, style_genome, compliance_gate, cinematographer, production, editor, character_designer, audio_pipeline, prompt_injector]` | **+dreamina_cli + write_file + patch.** §2.10 edge case: sub_steps MUST be in persona text, NOT a YAML field (schema rejects `sub_steps`). **Phase 63 SC#3 will use this agent for round table smoke** — persona must be robust. |

### Experts NOT in §2.2-§2.16 (use §2.1 defaults)

The following 6 experts are in our 12-transform list but NOT in the v10.0 §2.2-§2.16 table (which covers the original v10.0 15-expert list): `animation_studio`, `documentary_maker`, `performer`, `production`, `scene_builder` (as standalone, not absorption), `storyboard_designer`.

For these, apply §2.1 5-field mapping defaults:
- `tools`: `[hermes_llm, read_file, search_files]` + expert-specific write/exec per SKILL body analysis
- `persona`: first-person rewrite citing SKILL body anchors
- `refs`: `[]` (follow 9-shipped convention)
- `related_agents`: copy `metadata.hermes.related_skills` verbatim
- `lineage.skill_sha256`: SHA-256 of source SKILL.md

### Cross-15-Expert 5-Field Edge Case Summary (from §2.19)

| Field | Default pattern | Edge case experts in our 12 |
|-------|----------------|------------------------------|
| `tools` | analysis-only (11/15 in §2) | colorist (+write_file), prompt_injector (+write_file), visual_executor (+dreamina_cli +write_file +patch) |
| `persona` | standard advisory | compliance_gate (hard-gate + 3 red-lines), script_auditor (critic-not-writer), visual_executor (intent-vs-execution split) |
| `related_agents` | copy verbatim | creative_source (filter out `topic_curator` — nonexistent), performer/storyboard_designer (keep `scene_builder` — it becomes agent) |
| `lineage.skill_sha256` | standard hash | none special (all 12 have SKILL.md) |

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML serialization | Manual `f"..."` string building | `yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)` | CJK quoting + block scalar handling is deceptively hard; PyYAML 6.0.3 handles it per 9 shipped YAMLs |
| Schema validation | Manual field-by-field if-checks | `jsonschema.Draft202012Validator(schema).validate(agent)` or `.iter_errors(agent)` | Schema has nested $defs + pattern constraints + enum checks — manual checks will miss edge cases |
| SHA-256 computation | `subprocess.run(["sha256sum", ...])` | `hashlib.sha256(content.encode("utf-8")).hexdigest()` | Stdlib, no subprocess overhead, encoding explicit per CLAUDE.md PLW1514 |
| Transform log | Separate `.log` file per expert | `transform_notes` free-text field in lineage | Schema's only free-text field for provenance notes; separate log files are NOT in schema and would need separate management |

**Key insight:** Every piece of complexity in this phase (schema validation, SHA computation, YAML serialization) has a battle-tested library already in the Hermes stack. The only "creative" work is the persona rewrite (§Pattern 2) — and even that follows §2 per-expert rules.

## Common Pitfalls

### Pitfall 1: SC#3 Fields Not In Schema (HIGHEST RISK)

**What goes wrong:** SC#3 requires `source_sha` + `transform_rule_id` + `transform_timestamp` populated. Planner naively adds these as lineage sub-fields. Result: schema `additionalProperties: false` on Lineage $def rejects them → SC#2 byte-fails → ALL 12 YAMLs invalid.

**Why it happens:** SC#3 language ("lineage 字段 populated —— `source_sha` + `transform_rule_id` + `transform_timestamp`") reads like field names, but they're semantic concepts, not schema field names.

**How to avoid:** Map SC#3 semantics to schema-allowed fields:
- `source_sha` → `lineage.skill_sha256` (semantic equivalent — SHA-256 of source SKILL.md)
- `transform_rule_id` → cite in `lineage.transform_notes` free-text (e.g., `"Rule IDs: §2.14 colorist (CxSxZ color narrative + LUT plan, Step 7 integration)"`)
- `transform_timestamp` → `lineage.transform_date` (ISO date) + optionally cite time in `transform_notes`

**SC#3 grep check adjustment:** The SC#3 grep verification should be:
1. `grep -c "skill_sha256:" ~/.hermes/agents/{12 new YAMLs}` → all 12 non-empty (64-hex pattern)
2. `grep -c "Rule IDs:" ~/.hermes/agents/{12 new YAMLs} transform_notes` → all 12 cite §2 rule IDs
3. `grep -c "transform_date:" ~/.hermes/agents/{12 new YAMLs}` → all 12 have ISO date

**Warning signs:** If `jsonschema.Draft202012Validator.validate()` raises `Additional properties are not allowed ('source_sha' was unexpected)` — you hit this pitfall. [VERIFIED: tested by checking schema $defs/Lineage additionalProperties: false]

### Pitfall 2: sub_steps As YAML Field (HIGH RISK for visual_executor)

**What goes wrong:** visual_executor SKILL.md frontmatter has `sub_steps: [drawer, animator]`. Planner copies it as a top-level YAML field. Result: schema top-level `additionalProperties: false` rejects `sub_steps` → SC#2 byte-fails for visual_executor.

**Why it happens:** SKILL.md frontmatter has `sub_steps`, so copy reflex kicks in.

**How to avoid:** `sub_steps` is NOT a schema field. Put sub_steps info in:
- `description` text: `"...Sub-steps: [drawer, animator]."`
- `persona` text: `"My sub_steps are [drawer, animator] — drawer produces... animator refines..."`

**Warning signs:** audio_pipeline shipped YAML (6 sub_steps) does exactly this — no `sub_steps` field, info in persona + description. [VERIFIED: checked audio_pipeline.agent.yaml keys — no sub_steps]

### Pitfall 3: scene_builder Identity Ambiguity

**What goes wrong:** §2.7 says scene_builder was "absorbed" into cinematographer (Phase 17). Planner either (a) skips scene_builder transform entirely, or (b) maps all `related_skills: scene_builder` → `cinematographer`.

**Why it happens:** §2.7 absorption language is authoritative but predates this phase's scope (which explicitly lists scene_builder as 1 of 12 transform targets).

**How to avoid:** scene_builder is a legitimate transform target (it has its own SKILL.md with distinct content: FxSxA matrix, Blender previz, Pallasmaa doctrine). Transform it as a standalone agent. For `related_agents` in OTHER experts that cite `scene_builder`:
- **Keep `scene_builder` in related_agents** (it's becoming a real agent in this phase)
- Cite the §2.7 absorption context in scene_builder's own `transform_notes`

**Warning signs:** If Phase 63 registry loads 20 agents instead of 21 — scene_builder was skipped or mapped away.

### Pitfall 4: creative_source References Nonexistent topic_curator

**What goes wrong:** creative_source SKILL.md `related_skills: [..., topic_curator, ...]`. Planner copies verbatim. Result: related_agents references a nonexistent agent → Phase 63 registry won't fail (related_agents is just a string list), but the collaboration DAG has a dangling edge.

**Why it happens:** SKILL.md references future/stub skills that don't exist yet.

**How to avoid:** Filter `topic_curator` from creative_source's related_agents. Document the filter in transform_notes: `"Filtered topic_curator from related_agents (skill does not exist as of 2026-07-08)"`.

**Warning signs:** `grep topic_curator ~/.hermes/agents/creative_source.agent.yaml` returns nothing (filtered) OR returns a reference (not filtered — Phase 63 will have a dangling edge). [VERIFIED: ls kais-hermes-skills/skills/movie-experts/topic_curator → not found]

### Pitfall 5: YAML Field Ordering (Byte-Compat with Shipped)

**What goes wrong:** PyYAML default `sort_keys=True` alphabetizes fields. 9 shipped YAMLs use a specific field order (name, description, version, persona, tools, memory_scope, lineage, ...). New YAMLs with alphabetical order look different → visual inconsistency, harder operator triage.

**Why it happens:** PyYAML default behavior.

**How to avoid:** Use `yaml.dump(data, f, sort_keys=False)` to preserve dict insertion order. Build the dict in the same field order as shipped YAMLs.

**Warning signs:** `diff <(head -5 screenplay.agent.yaml) <(head -5 new_expert.agent.yaml)` shows field order mismatch. [VERIFIED: 9 shipped YAMLs all use same field order — name first]

### Pitfall 6: CJK Content Quoting in persona

**What goes wrong:** persona text contains CJK + single quotes (e.g., `"Snyder's"`). PyYAML may use wrong quoting style, breaking round-trip parse.

**Why it happens:** YAML quoting rules are subtle with mixed CJK + ASCII quotes.

**How to avoid:** PyYAML 6.0.3 handles this correctly with `default_flow_style=False` + `allow_unicode=True`. Verify round-trip: `yaml.safe_load(yaml.dump(data)) == data`. The 9 shipped YAMLs demonstrate correct quoting (e.g., screenplay persona has `Snyder''s` — double-single-quote escape in YAML single-quoted scalar).

**Warning signs:** `yaml.safe_load` on dumped YAML raises YAMLError or produces different dict.

### Pitfall 7: Empty related_skills (YAML list parse)

**What goes wrong:** Some SKILL.md frontmatters use multi-line list format:
```yaml
related_skills:
  - screenplay
  - editor
```
A naive grep for `related_skills:` + same-line value misses the list items. Early research grep showed `related_skills:` with nothing after it, looking empty.

**Why it happens:** YAML multi-line list vs flow list `[a, b]` parse differently in grep.

**How to avoid:** Use `yaml.safe_load` to parse frontmatter, not grep. All 12 source SKILLs have non-empty related_skills when parsed as YAML. [VERIFIED: parsed all 12 with yaml.safe_load]

## Code Examples

### SHA-256 Computation (VERIFIED against shipped screenplay YAML)

```python
# Source: hashlib stdlib + 04-MIGRATION-PATH §2.1 + verified against shipped YAML
import hashlib
from pathlib import Path

def compute_skill_sha256(skill_path: Path) -> str:
    """Compute SHA-256 of source SKILL.md content (UTF-8 / LF).

    Encoding explicit per CLAUDE.md PLW1514 (Ruff will block merge without it).
    Pattern: hashlib.sha256(content.encode("utf-8")).hexdigest()
    Verified: screenplay SHA matches shipped YAML lineage.skill_sha256.
    """
    content = skill_path.read_text(encoding="utf-8")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

# Verification (PASSED 2026-07-08):
# screenplay SKILL.md → 2045286cbde10288a3949abf67e893fca1938d3904dfbb19a70e2abbca70e8c1
# screenplay.agent.yaml lineage.skill_sha256 → same value ✓
```

### jsonschema Draft202012Validator Validation (VERIFIED — all 9 shipped pass)

```python
# Source: agent/registry_loader.py (v11.0 INFRA-01) + verified against 9 shipped YAMLs
import jsonschema
import yaml
from pathlib import Path

def validate_agent_yaml(yaml_path: Path, schema_path: Path) -> list[str]:
    """Validate a single agent YAML against agents-schema.yaml.

    Returns list of error messages (empty = valid).
    Uses Draft202012Validator per SC#2 hard constraint.
    """
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    agent = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(agent), key=lambda e: list(e.absolute_path))
    return [f"{'.'.join(str(p) for p in e.absolute_path) or '$'}: {e.message}" for e in errors]

# Batch validation (VERIFIED 2026-07-08):
# All 9 shipped YAMLs → 0 errors each ✓
# Schema path: .planning/research/v10-orchestrator-design/agents-schema.yaml
```

### YAML Dump (byte-compat with shipped)

```python
# Source: inferred from 9 shipped YAML structure (PyYAML block style, UTF-8)
import yaml
from pathlib import Path

def write_agent_yaml(agent: dict, target_path: Path) -> None:
    """Write agent YAML in byte-compat style with 9 shipped YAMLs.

    Key flags:
    - default_flow_style=False: block style (not flow [a,b])
    - sort_keys=False: preserve dict insertion order (match shipped field order)
    - allow_unicode=True: CJK chars unescaped
    - width=100: wrap long lines (match shipped)
    """
    with open(target_path, "w", encoding="utf-8") as f:
        yaml.dump(agent, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True, width=100)
```

### Transform Log Format (in transform_notes free-text)

```yaml
# Source: SC#3 requirement + schema lineage $def (transform_notes is only free-text field)
# This is the RECOMMENDED format for citing §2 rule IDs in transform_notes:
lineage:
  derived_from_skill_id: visual_executor
  derived_from_repo: kais-hermes-skills
  transform_date: '2026-07-08'
  transform_notes: 'Rule IDs: §2.10 visual_executor (dreamina_cli + write_file + patch;
    sub_steps [drawer, animator] in persona + description text, NOT as YAML field per
    schema additionalProperties:false; intent-vs-execution split load-bearing). Source
    SKILL.md SHA-256 verified at transform time. Git commit 469ae4e (2026-07-04). Transform
    timestamp: 2026-07-08T14:30:00Z.'
  skill_sha256: <64-hex SHA-256 of source SKILL.md>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SKILL.md as only expert form (v1-v9) | Agent YAML + SKILL fallback (v10.0+) | v10.0 (Phase 44 决策 5, 2026-07-07) | Agent YAML is primary; SKILL is fallback via `default_invocation` |
| Manual transform (v11.0 PoC, 9 YAMLs) | Same manual transform (Phase 62, 12 YAMLs) | v11.0 → v13.0 | No change — `hermes agent transform` CLI deferred to v14+ per §1.2(c) |
| 9 active agents (v11.0 PoC baseline) | 21 active agents (Phase 62 target) | Phase 62 | Full 15-expert DAG coverage + 6 new experts (animation/documentary/performer/production/scene_builder/storyboard) |

**Deprecated/outdated:**
- `compliance_marketing` as expert_id: renamed to `compliance_gate` (compliance_marketing is now an alias). [VERIFIED: compliance_gate SKILL.md aliases: [compliance_marketing]]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `refs: []` (empty) is the correct pattern for all 12 new YAMLs | Schema Field Reference #9 | LOW — if wrong, Phase 63 round table might fail to retrieve RAG docs. But 9 shipped YAMLs all have `refs: []` and work. Mitigation: follow shipped convention. |
| A2 | `memory` block should be omitted (use schema defaults) | Schema Field Reference #8 | LOW — if tuning needed later, operator can add the block. 9 shipped YAMLs omit it. |
| A3 | scene_builder should be transformed as standalone (not mapped to cinematographer) | Per-Expert Transform #9 | MEDIUM — if wrong, Phase 63 loads 20 agents not 21. But CONTEXT.md explicitly lists scene_builder in the 12-transform set, overriding §2.7 absorption. |
| A4 | animation_studio / documentary_maker / performer / production / storyboard_designer use §2.1 defaults (not in §2.2-§2.16) | Per-Expert Transform table | LOW — these experts postdate v10.0's 15-expert list. §2.1 defaults + SKILL.md frontmatter provide sufficient transform guidance. |
| A5 | All 12 experts should have `default_invocation: mcp_tool` (including compliance_gate) | Per-Expert Transform #3 | LOW — CONTEXT.md locked decision overrides §2.15/§3.6 recommendation for `disabled`. If compliance_gate premature activation causes pipeline blocks, Phase 63 smoke will surface it. |

**If this table is empty:** N/A — 5 assumptions documented above, all LOW/MEDIUM risk with clear mitigations.

## Open Questions (RESOLVED)

1. **Should `refs` field be populated with actual ref paths or stay `[]`?**
   - What we know: All 9 shipped YAMLs have `refs: []`. Refs are surfaced in persona text by name. Schema allows array of strings.
   - What's unclear: Is this a deliberate v11.0 design choice (refs in persona suffice) or an oversight?
   - Recommendation: Follow shipped convention (`refs: []`). If Phase 63 round table needs path-based ref retrieval, operator can backfill. Low risk.
   - RESOLVED: Follow shipped convention (`refs: []`) — confirmed across all 12 transform_notes drafts in plans 02/03.

2. **Should creative_source's `topic_curator` reference be filtered or kept?**
   - What we know: topic_curator skill does NOT exist in kais-hermes-skills repo. [VERIFIED: ls → not found]
   - What's unclear: Is topic_curator a planned future skill that related_agents should pre-reference?
   - Recommendation: Filter it out (dangling edge in collaboration DAG is worse than missing a future peer). Document in transform_notes.
   - RESOLVED: Filter topic_curator (Plan 02 Task 2 acceptance criterion enforces grep returns 0).

3. **Transform timestamp precision — date only or ISO datetime?**
   - What we know: Schema `transform_date` has `format: date` (ISO date, no time). SC#3 says "transform_timestamp".
   - What's unclear: Does SC#3 require sub-day precision for audit?
   - Recommendation: Use ISO date in `transform_date` field (schema-compliant). Optionally add ISO datetime in `transform_notes` free-text for audit precision.
   - RESOLVED: ISO date in `transform_date` + ISO datetime in `transform_notes` free-text (Plan 02/03 transform_notes cite "2026-07-08T00:00:00Z").

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | hashlib, yaml, jsonschema | ✓ | 3.13 (ty) / 3.11+ runtime | — |
| PyYAML | YAML dump/parse | ✓ | 6.0.3 | — |
| jsonschema | SC#2 validation | ✓ | 4.26.0 | — |
| `/data/workspace/kais-hermes-skills/` repo | Source SKILL.md read | ✓ | git HEAD c15018611 | — |
| `~/.hermes/agents/` dir | Target YAML write | ✓ | 9 existing YAMLs | — |
| `.planning/research/v10-orchestrator-design/agents-schema.yaml` | SC#2 schema | ✓ | Phase 45 stable | — |
| `.planning/research/v10-orchestrator-design/04-MIGRATION-PATH.md` | §2 transform rules | ✓ | Phase 49 stable | — |

**Missing dependencies with no fallback:** None — all dependencies available.

**Missing dependencies with fallback:** N/A.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Python stdlib + jsonschema 4.26.0 + PyYAML 6.0.3 (no pytest needed for transform phase) |
| Config file | `pyproject.toml` (existing, no changes) |
| Quick run command | `python3 -c "import jsonschema, yaml; ..."` (inline validation script) |
| Full suite command | `python3 scripts/validate_phase62_yamls.py` (12-YAML batch validation, to be created) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EXPERT-01 | 12 new YAML files exist at `~/.hermes/agents/{name}.agent.yaml` | smoke | `ls ~/.hermes/agents/*.agent.yaml \| wc -l` → expect 21 | ❌ Wave 0 (inline bash) |
| EXPERT-02 | All 12 new YAMLs byte-pass `Draft202012Validator.validate()` | unit | `python3 -c "import jsonschema, yaml; schema=yaml.safe_load(open('...')); [jsonschema.Draft202012Validator(schema).validate(yaml.safe_load(open(p))) for p in glob('~/.hermes/agents/*.agent.yaml')]"` | ❌ Wave 0 (inline python) |
| EXPERT-03a | All 12 new YAMLs have non-empty `lineage.skill_sha256` (64-hex) | unit | `grep -c "skill_sha256: [a-f0-9]\{64\}" ~/.hermes/agents/{12 new YAMLs}` | ❌ Wave 0 (inline bash) |
| EXPERT-03b | All 12 new YAMLs cite §2 rule IDs in `transform_notes` | unit | `grep -c "Rule IDs:" ~/.hermes/agents/{12 new YAMLs}` | ❌ Wave 0 (inline bash) |
| EXPERT-03c | Spot-check 1 YAML: lineage.skill_sha256 traces back to source SKILL.md SHA | integration | `python3 -c "import hashlib; print(hashlib.sha256(open('/data/.../visual_executor/SKILL.md').read().encode()).hexdigest())"` → compare to YAML | ❌ Wave 0 (inline python) |
| EXPERT-01 (cross) | All 12 new YAMLs field-order byte-compatible with 9 shipped (sort_keys=False) | smoke | `diff <(head -7 ~/.hermes/agents/screenplay.agent.yaml) <(head -7 ~/.hermes/agents/{new}.agent.yaml)` → field names match | ❌ Wave 0 (inline bash) |

### Sampling Rate

- **Per task commit (per-YAML write):** Inline validation: `jsonschema.Draft202012Validator.validate()` on that single YAML
- **Per wave merge (batch of 6 or 12):** Full batch validation script across all new YAMLs
- **Phase gate (SC#1-4):** Full suite:
  1. `ls ~/.hermes/agents/*.agent.yaml | wc -l` → 21
  2. Batch jsonschema validation → 0 errors
  3. `grep "skill_sha256: [a-f0-9]\{64\}"` in all 12 → non-empty
  4. `grep "Rule IDs:"` in all 12 transform_notes → non-empty
  5. Spot-check: visual_executor SHA traces to source

### Wave 0 Gaps

- [ ] `scripts/validate_phase62_yamls.py` — optional batch validation script (can be inline python instead)
- [ ] No pytest test file needed — transform phase validates via inline jsonschema checks, not pytest fixtures

*(If no gaps: None — existing jsonschema + PyYAML infrastructure covers all phase validation needs)*

## Security Domain

> Phase 62 is a transform phase with no new user input surface, no auth, no network. Security considerations are minimal.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — no auth in transform phase |
| V3 Session Management | no | N/A |
| V4 Access Control | no | N/A |
| V5 Input Validation | yes | `yaml.safe_load` (refuses arbitrary tags — T-52-01 mitigation in registry_loader.py) + `jsonschema.Draft202012Validator` (rejects undeclared fields — T-52-04 mitigation) |
| V6 Cryptography | yes (light) | SHA-256 for lineage integrity (hashlib stdlib — never hand-roll). Used for drift detection, not security. |
| V7 Error Handling | yes | `RegistryValidationError` with structured json_path + invalid_field (existing v11.0 pattern in registry_loader.py) |
| V8 Data Protection | no | N/A — no sensitive data in YAMLs |
| V9 Communications | no | N/A — no network |
| V10 Business Logic | yes | Lineage invariants L1-L6 (source SKILL.md read-only) + FOUND-08 (expert_id preserved verbatim) |

### Known Threat Patterns for YAML Transform

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| YAML tag injection (arbitrary Python object instantiation) | Tampering | `yaml.safe_load` (not `yaml.load`) — refuses arbitrary tags [VERIFIED: registry_loader.py line 227] |
| Undeclared field injection (schema bypass) | Tampering | `additionalProperties: false` in agents-schema.yaml top-level + Lineage $def [VERIFIED: schema lines 42, 354] |
| Filename-name mismatch (spoofing) | Spoofing | registry_loader enforces `data["name"] == filename.stem` [VERIFIED: registry_loader.py lines 261-267] |
| Source SKILL.md tampering (lineage L1-L6) | Tampering | Read-only source repo; SHA-256 frozen at transform time enables drift detection |

## Sources

### Primary (HIGH confidence)

- `.planning/research/v10-orchestrator-design/agents-schema.yaml` — Draft 2020-12 schema, 18 fields, read + validated against 9 shipped YAMLs [VERIFIED: jsonschema validation, 0 errors]
- `.planning/research/v10-orchestrator-design/04-MIGRATION-PATH.md §2` — 75-cell per-expert transform rule table [CITED: §2.0-§2.19 read end-to-end]
- `~/.hermes/agents/*.agent.yaml` (9 shipped) — canonical structural templates [VERIFIED: read all 9, field structure confirmed]
- `/data/workspace/kais-hermes-skills/skills/movie-experts/{12 experts}/SKILL.md` — source frontmatter [VERIFIED: read all 12 frontmatters via yaml.safe_load]
- `agent/registry_loader.py` — existing v11.0 loader + validation pattern [VERIFIED: read full file]

### Secondary (MEDIUM confidence)

- `04-MIGRATION-PATH.md §2` persona excerpts — first-person rewrite examples for 15 experts [CITED: §2.2-§2.16 persona excerpt blocks]

### Tertiary (LOW confidence)

- None — all findings verified against primary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — PyYAML/jsonschema/hashlib all pre-existing and verified
- Architecture: HIGH — 9 shipped YAMLs provide exact structural template; registry_loader.py shows validation pattern
- Per-expert transform rules: HIGH for 6 experts in §2.2-§2.16 (colorist, compliance_gate, creative_source, prompt_injector, script_auditor, visual_executor); MEDIUM for 6 experts NOT in §2.2-§2.16 (animation_studio, documentary_maker, performer, production, scene_builder, storyboard_designer) — using §2.1 defaults + SKILL.md frontmatter
- Pitfalls: HIGH — all pitfalls verified by reading schema constraints + testing against shipped YAMLs
- Schema field reference: HIGH — read schema directly + validated field presence across 9 shipped YAMLs

**Research date:** 2026-07-08
**Valid until:** 2026-08-08 (30 days — schema + §2 rules are design-locked, stable indefinitely, but source SKILL.md content may drift if kais-hermes-skills repo is updated)
