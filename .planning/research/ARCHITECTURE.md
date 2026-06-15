# Architecture Patterns: RAG-Augmented Movie-Experts Suite v2

**Domain:** Skill-based RAG architecture inside a markdown-only skill system
**Researched:** 2026-06-15
**Overall confidence:** HIGH (based on direct reading of existing skills, memory plugin source, and codebase conventions)

## Executive Summary

The Hermes skill system has a deliberately narrow contract: **a skill is a markdown file injected as a user message**. The LLM in the conversation loop then autonomously decides which tools to call (file read, memory search, etc.) based on the instructions in that markdown. This shapes every architectural decision for RAG-augmented skills:

- Static `references/*.md` files are surfaced by **listing them in a References table inside SKILL.md** and pointing the agent to them with inline pointers like "see `references/foo.md` for X". The agent uses its existing `read_file`-style tool to read them on demand. No new code is needed; the skill prompt is the API.
- Optional memory-plugin RAG is invoked by **referencing tool names** (`mem0_search`, `memory`) in conditional language inside SKILL.md. The memory plugin already injects a system-prompt block announcing its presence, so the LLM knows when the tool is available. SKILL.md prompts should use defensive phrasing: "If memory search is available, query for X; otherwise rely on refs."
- Cross-expert collaboration is **declarative YAML** (`metadata.hermes.related_skills`). Adding an expert = new directory + new edges in upstream/downstream `related_skills` lists. There is no runtime orchestration; the graph is documentation plus (future) a worker `/decide` router.
- The eval harness is a **standalone Python script** under `scripts/` per skill. It is NOT registered with Hermes' tool registry; it is a developer-side benchmark, not a user-facing tool.

This means the architecture for RAG-augmented skills is almost entirely **content architecture** — the layout of directories, the phrasing of prompts, the structure of reference files — rather than runtime architecture. The load-bearing work happens at authoring time.

## Recommended Architecture

### High-Level Skill Layout (18-expert suite)

```
skills/movie-experts/
├── README.md                          # Top-level suite overview (NEW in DOC-01)
├── _shared/                           # (optional v2) cross-expert refs
│   ├── glossary.md                    # EN<->CN term dictionary
│   └── encoding-matrices.md           # 5D, CxSxZ, FxRxT, ... reference
├── screenplay/
│   ├── SKILL.md
│   ├── references/                    # NEW in REFS-A
│   │   ├── narrative-structure.md     # 3-act micro-structure, beat sheets
│   │   ├── dialogue-craft.md          # subtext, vernacular, "show don't tell"
│   │   ├── emotion-curve-design.md
│   │   ├── short-drama-hooks.md       # 短剧-specific: 3-second hooks
│   │   └── PAYWALL.md                 # cliffhanger / 卡点 patterns (CN-primary)
│   ├── prompts/                       # NEW in EVAL-01
│   │   ├── 01-three-act-structure.yaml
│   │   ├── 02-subtext-dialogue.yaml
│   │   └── 03-emotion-curve.yaml
│   └── reports/                       # NEW in EVAL-01 (gitignored output)
│       └── .gitkeep
├── cinematographer/                   # NEW expert (EXPERT-CINE)
│   ├── SKILL.md
│   ├── references/
│   │   ├── shot-grammar.md            # 景别/视角/构图
│   │   ├── axis-rules.md              # 180° rule, 30° rule, match cut
│   │   ├── vertical-screen-framing.md # 竖屏 specific framing
│   │   └── camera-motion-catalog.md
│   ├── prompts/
│   └── reports/
├── hook_retention/                    # NEW expert (EXPERT-HOOK)
│   ├── SKILL.md
│   ├── references/
│   │   ├── three-second-hooks.md
│   │   ├── conflict-escalation.md
│   │   ├── paywall-design.md          # 付费卡点 patterns
│   │   └── vertical-pacing.md
│   ├── prompts/
│   └── reports/
├── production/                        # NEW expert (EXPERT-PROD)
│   ├── SKILL.md
│   ├── references/
│   │   ├── casting-notes.md           # 选角
│   │   ├── costume-makeup-props.md    # 服化道
│   │   ├── lighting-setup.md
│   │   └── scheduling-call-sheet.md   # 统筹/拍摄计划
│   ├── prompts/
│   └── reports/
├── compliance_marketing/              # NEW expert (EXPERT-COMPLI)
│   ├── SKILL.md
│   ├── references/
│   │   ├── cn-content-rules.md        # 中国短剧合规清单
│   │   ├── platform-specs-douyin.md
│   │   ├── platform-specs-kuaishou.md
│   │   ├── platform-specs-miniprogram.md
│   │   └── viral-element-catalog.md   # 爆款元素
│   ├── prompts/
│   └── reports/
├── [12 other existing experts, each gaining references/ + prompts/ + reports/ subdirs]
└── _eval/                             # Top-level shared eval harness (alternative layout)
    ├── runner.py
    ├── judge_prompt.md
    ├── snapshot.py                    # captures "before" SKILL.md state
    └── README.md
```

### Two Layout Choices for Eval Harness

**Option A (recommended): central `_eval/` at suite root.** The eval runner knows how to walk all 18 experts. Each expert keeps only `prompts/` (input fixtures) locally; reports go to `_eval/reports/<expert>/`. This avoids duplicating runner.py 18 times.

**Option B: per-expert `scripts/runner.py`.** Each expert has its own copy. More boilerplate, but each expert becomes self-contained and portable (could be moved to `optional-skills/` without dragging a shared harness).

**Recommendation: Option A** because (1) the judge prompt and snapshot logic are shared, (2) the 14 existing experts share an identical evaluation pattern (LLM-as-judge double-blind), and (3) Hermes' own `scripts/` directory already centralizes developer tooling.

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `SKILL.md` | Declarative expert identity + workflow + quality thresholds + RAG invocation instructions | Parsed by `agent/skill_utils.parse_frontmatter`; body injected as user message |
| `references/*.md` | Static curated knowledge corpus (Chinese-primary, EN glossary) | Read by the LLM via `read_file` tool on demand; surfaced via References table in SKILL.md |
| `prompts/*.yaml` | Eval benchmark fixtures (input + expected dimensions) | Consumed by `_eval/runner.py`; never read by the runtime LLM |
| `_eval/runner.py` | Double-blind LLM-as-judge: invoke skill with "before" prompt, invoke with "after" prompt, judge | Calls Hermes via subprocess or HTTP; writes to `_eval/reports/` |
| `_eval/snapshot.py` | Captures pre-refactor SKILL.md state into `_eval/baseline/<expert>/SKILL.md` | Run once before REFACTOR-A begins; idempotent |
| `_shared/glossary.md` | Cross-expert EN<->CN term dictionary to keep translations consistent | Read by any expert; linked from each SKILL.md |
| Memory plugin (existing, untouched) | Optional vector RAG via `mem0_search` / `memory` tools | Activated by user config; LLM sees its tool schemas at runtime |

### Data Flow: A RAG-Augmented Skill Invocation

```
1. User invokes /screenplay (or worker /decide routes to it)
2. agent/skill_commands._load_skill_payload reads screenplay/SKILL.md,
   parses YAML frontmatter, injects body as user message
3. agent/conversation_loop.run_conversation sends to LLM
4. LLM, following instructions in SKILL.md body:
   a. Reads references/short-drama-hooks.md via read_file tool  ← static RAG
   b. (Conditional) Calls mem0_search("screenplay style preferences")
      IF memory plugin is configured                            ← optional RAG
   c. Falls back gracefully if mem0_search is absent
      (system prompt block from memory plugin is missing,
       so LLM knows the tool doesn't exist)
   d. Generates script.json per Output Format spec
5. Downstream /scene_builder invocation sees screenplay's output
   in conversation history (if same session) or via explicit
   file passing
```

**Critical insight:** The skill author does NOT need to write Python to make RAG work. The author writes prompt language that (a) tells the LLM which references to consult and when, and (b) defensively mentions memory-plugin tools by name so the LLM uses them when available. This is a **prompt-engineering architecture**, not a runtime architecture.

## Patterns to Follow

### Pattern 1: References Table at Top of SKILL.md

**What:** A markdown table immediately after the "## When to use" section listing every file in `references/` with a one-line description and trigger.

**Why:** The LLM scans the SKILL.md body linearly. A table at the top is the highest-signal way to say "these files exist, read them when X".

**Example** (adapted from `skills/creative/manim-video/SKILL.md:229`):

```markdown
## References

| File | When to Read | Contents |
|------|--------------|----------|
| `references/narrative-structure.md` | Before drafting any scene | 3-act micro-structure compression, beat sheet templates for 60-180s runtime |
| `references/dialogue-craft.md` | Before writing dialogue | Subtext ratio rules, vernacular register, banned expository patterns |
| `references/short-drama-hooks.md` | Before writing the opening scene | 短剧-specific 3-second hook patterns, cold-open templates |
| `references/PAYWALL.md` | When user requests 短剧 / 付费剧 | Cliffhanger (卡点) placement, paywall frequency by platform |

**Read the relevant reference BEFORE drafting.** Do not generate from training data alone — the references encode industry conventions that differ from generic screenplay advice.
```

### Pattern 2: Defensive Memory-Plugin Invocation

**What:** Phrasing in SKILL.md that uses memory-plugin tools **if and only if** they are available, with explicit fallback to static refs.

**Why:** The memory plugin's `system_prompt_block()` (`plugins/memory/mem0/__init__.py:230`) only injects its "Use mem0_search..." line when configured. If the plugin isn't configured, the LLM has no `mem0_search` tool in its schema and the SKILL.md prompt should not hard-require it. Defensive phrasing lets the same SKILL.md work in both configurations.

**Example** (concrete block to embed in SKILL.md):

```markdown
## Knowledge Retrieval

This expert draws on two knowledge sources. Always use (1); use (2) if available.

### 1. Static references (always available)

Before generating any output, read the relevant files from `references/`
listed in the References table above. These are curated industry knowledge
and override generic assumptions from training data.

### 2. Memory plugin (optional, if `mem0_search` or `memory` tool is in your tool list)

If the `mem0_search` tool is available in your current tool set, query it
for relevant context BEFORE drafting:

- `mem0_search("screenplay style preferences for this user")`
- `mem0_search("prior screenplay decisions in this project")`

If only the built-in `memory` tool is available, use:

- `memory(action="read", target="memory")` to retrieve stored notes.

If neither tool is present, skip this step silently — the static references
are sufficient. Do NOT mention to the user that memory tools are unavailable.
```

**Why this works:** The LLM sees its tool schema at runtime. If `mem0_search` isn't there, the conditional ("if available in your current tool set") evaluates false in the LLM's reasoning, and it proceeds with static refs only. No crash, no confused user-facing message.

### Pattern 3: Bilingual Sections with EN Structure, CN Body

**What:** SKILL.md keeps YAML frontmatter and H2 section headings in English (for parser compatibility and Hermes community convention). Body paragraphs under each heading are bilingual: EN summary sentence first, then CN explanatory paragraph with examples.

**Why:** The Hermes skill loader (`agent/skill_utils.parse_frontmatter`) expects English YAML keys. The CONVENTIONS.md note (line 54) explicitly says "双语策略是 EN 结构 + CN 描述与示例". Mixing CN into YAML keys would break discovery.

**Example** (concrete SKILL.md section):

```markdown
## Style Rules / 风格规则

### Narrative Standards / 叙事标准

English: Every scene must establish a clear dramatic question within the first 2 seconds. The opening hook must resolve or subvert by the closing scene.

中文:每个场景必须在最初 2 秒内确立明确的戏剧问题。开场钩子必须在结尾场景中得到回应或反转。短剧(60-180 秒)的节奏比电影更紧凑——观众滑动屏幕的速度决定了一切。

**Example / 示例:**
- EN: A character says "I'll come back for you" in scene 1 → returns (or doesn't) in scene 8.
- CN: 角色在场景 1 说出「我会回来找你」→ 在场景 8 中回归(或未回归),形成呼应。
```

### Pattern 4: Reference File Anatomy

**What:** Each `references/*.md` file follows a fixed anatomy so the LLM can extract value predictably.

**Why:** Consistent structure → LLM learns the pattern after reading one file → faster retrieval on subsequent reads.

**Template** (every reference file):

```markdown
# [Topic Title] / [中文标题]

**Source:** [Book / paper / platform guide / practitioner interview]
**Copyright:** [Public domain / fair-use excerpt / licensed / original]
**Last verified:** YYYY-MM-DD against [source version/edition]

## When to Read This

[One paragraph: trigger conditions. "Read this when the user asks for X, or when Y appears in the upstream screenplay output."]

## Core Principles

[Bullet list of 3-7 principles. Each principle is a one-line rule followed by a 2-3 sentence explanation.]

## Concrete Patterns

[3-5 named patterns with examples. Each pattern: name, when to use, example (EN+CN where relevant).]

## Anti-Patterns

[What NOT to do, with reasoning. LLMs respond well to "don't do X because Y".]

## Cross-References

[Links to other reference files in the same skill, or to other experts' refs. "For platform-specific paywall placement, see `../hook_retention/references/paywall-design.md`."]
```

### Pattern 5: Eval Prompt Fixture Format

**What:** Each eval prompt is a YAML file with structured fields so the runner can iterate them uniformly.

**Why:** The double-blind judge needs (a) the user-facing input, (b) the dimensions to score on, (c) the expected reference answer or rubric. YAML keeps this auditable.

**Template** (`prompts/01-three-act-structure.yaml`):

```yaml
---
id: screenplay-01-three-act-structure
expert: screenplay
skill_invocation: /screenplay
difficulty: medium
bilingual: true          # runner will run both EN and CN variants
input:
  en: |
    Write a 90-second short drama script about a mother discovering
    her daughter's secret social media account. Output script.json.
  cn: |
    写一段 90 秒的短剧剧本:母亲发现女儿的秘密社交账号。
    输出 script.json。
dimensions:
  - name: narrative_tension
    weight: 0.30
    rubric: |
      Score 0.0-1.0. Does the script maintain rising tension across
      all scenes? Penultimate scene should be near 1.0.
  - name: dialogue_naturalness
    weight: 0.30
    rubric: |
      Score 0.0-1.0. Is the dialogue plausible for the character's
      age and background? No expository "as you know" lines.
  - name: emotional_arc
    weight: 0.25
    rubric: |
      Score 0.0-1.0. Are there >=3 distinct emotional phases per scene?
      Does the peak land in the 70-85% runtime window?
  - name: short_drama_hook
    weight: 0.15
    rubric: |
      Score 0.0-1.0. Does the opening scene hook within 3 seconds?
      (短剧-specific; does not apply to generic screenplay rubrics.)
thresholds:
  production_minimum:
    narrative_tension: 0.80
    dialogue_naturalness: 0.85
    emotional_arc: 1.0    # "Complete" per SKILL.md
    short_drama_hook: 0.75
---
```

### Pattern 6: Eval Runner Architecture

**What:** A standalone Python script that lives at `skills/movie-experts/_eval/runner.py`. It is NOT registered with `tools/registry.py` — it is a developer tool, not an agent tool.

**Why:** Eval runs are offline benchmarks, not in-conversation tool calls. Registering it would expose benchmark scaffolding to the production agent, which is wrong.

**Runner pseudocode:**

```python
# skills/movie-experts/_eval/runner.py
"""
Double-blind LLM-as-judge eval harness for movie-experts suite.

Usage:
    python runner.py --expert screenplay --prompt-id 01
    python runner.py --all                  # run every prompt for every expert
    python runner.py --compare baseline/after   # diff two snapshots

Outputs:
    _eval/reports/<expert>/<prompt-id>_<timestamp>.json
    _eval/reports/summary.md                 # aggregated table
"""

def run_one(expert: str, prompt_file: Path, variant: str) -> dict:
    """
    variant: "baseline" or "refactored"
      - baseline: invoke the snapshot SKILL.md from _eval/baseline/<expert>/
      - refactored: invoke the current SKILL.md from skills/movie-experts/<expert>/

    Returns: {output: str, judge_scores: dict, elapsed_s: float}
    """
    # 1. Spawn hermes CLI (or HTTP API) in a clean session
    # 2. Inject the skill variant + the user input from prompt_file
    # 3. Capture the model's output
    # 4. Send output to a separate judge model with the rubric
    # 5. Return structured scores
    ...

def main():
    experts = ["screenplay", "scene_builder", ..., "cinematographer", ...]
    for expert in experts:
        for prompt_file in (Path(expert) / "prompts").glob("*.yaml"):
            baseline = run_one(expert, prompt_file, variant="baseline")
            refactored = run_one(expert, prompt_file, variant="refactored")
            # Double-blind: judge sees "Response A" and "Response B", not which is which
            verdict = judge_double_blind(
                rubric=prompt_file["dimensions"],
                response_a=baseline["output"],
                response_b=refactored["output"],
            )
            write_report(expert, prompt_file.stem, baseline, refactored, verdict)
```

**Critical detail — the "before" snapshot:** Before any REFACTOR-A work begins, run `snapshot.py` once. It copies every current `SKILL.md` into `_eval/baseline/<expert>/SKILL.md`. The runner then has a stable "before" to compare against, regardless of how many times the refactored version changes during development.

### Pattern 7: Cross-Expert Reference Linking

**What:** Reference files in one expert can link to reference files in another expert using relative paths.

**Why:** Some knowledge is shared (e.g., the 5D style genome belongs to `style_genome`, but `colorist` needs to reference its color dimensions). Duplicating breaks single-source-of-truth.

**Example** (from `skills/movie-experts/colorist/references/color-theory.md`):

```markdown
## Cross-References

- For how color dimensions map to the 5D style genome, see
  `../style_genome/references/genome-decomposition.md`.
- For how color intent flows into scene_builder's lighting setup, see
  `../scene_builder/references/lighting-setup.md`.
```

## Updated related_skills Graph (18 Experts)

### Existing 14-Expert Graph (from current SKILL.md files)

```
style_genome ──┬── screenplay ──┬── scene_builder ──┬── drawer
               │                 │                   ├── animator
               ├── colorist      ├── editor ─────────┼── voicer
               ├── editor        ├── performer       ├── composer
               ├── composer      ├── continuity      ├── foley
               ├── scene_builder ├── voicer          ├── spatial_audio
               ├── performer     ├── mixer           └── mixer
               └── continuity    └── composer

performer ──── (most-connected: 8 edges)
scene_builder  (9 edges)
foley ──────── (7 edges)
editor ─────── (6 edges)
```

### New 4-Expert Integration

#### Cinematographer (`cinematographer`)

**Contract:** Sits between `scene_builder` (which outputs 3D camera constraints) and `animator` (which executes 2D camera motion). Cinematographer translates spatial blocking into shot language (景别/视角/构图).

**Edges to add:**
- `cinematographer.related_skills: [scene_builder, animator, editor, screenplay, continuity, drawer, hook_retention]`
- Update `scene_builder.related_skills` to add `cinematographer`
- Update `animator.related_skills` to add `cinematographer`
- Update `editor.related_skills` to add `cinematographer` (axis rules)

**Collaboration block in cinematographer/SKILL.md:**
```markdown
## Collaboration

- **<- scene_builder**: camera_constraints.json (3D camera paths), scene blocking
- **<- screenplay**: per-scene dramatic intent (which moment needs close-up vs wide)
- **-> animator**: shot_list.json with framing + camera motion intent per shot
- **-> editor**: axis data + match-cut opportunities (180° rule compliance)
- **-> drawer**: framing references per shot (which subject occupies which third)
- **-> hook_retention**: shot pacing hints (which shots are "hook shots" for 3-second openings)
```

**Why this contract:** `scene_builder` currently produces `camera_constraints.json` (raw 3D math). `animator` consumes it as motion directives. The gap is **shot language** — the cinematographer's job is to decide "this moment is a medium close-up, eye-level, rule-of-thirds left" and hand that to animator as a framing intent. This is a layer of abstraction that currently doesn't exist.

#### Hook & Retention (`hook_retention`)

**Contract:** Bidirectional feedback loop with screenplay (rewrite hooks) and editor (pacing for retention). Also receives shot pacing hints from cinematographer.

**Edges to add:**
- `hook_retention.related_skills: [screenplay, editor, cinematographer, compliance_marketing, composer]`
- Update `screenplay.related_skills` to add `hook_retention`
- Update `editor.related_skills` to add `hook_retention`
- Update `compliance_marketing.related_skills` to add `hook_retention`

**Collaboration block in hook_retention/SKILL.md:**
```markdown
## Collaboration

- **<- screenplay**: full script.json (to evaluate hook strength, identify paywall points)
- **<- cinematographer**: shot pacing hints (which shots are hook-capable)
- **<- editor**: rough cut (to measure actual pacing vs intended retention curve)
- **-> screenplay**: hook_retention_notes.json — rewrite suggestions for opening 3 seconds,
  cliffhanger placement markers (卡点 positions), conflict escalation beats
- **-> editor**: pacing_adjustments.json — where to tighten cuts, where to let breath
- **-> compliance_marketing**: paywall timestamps (where 短剧 platform will insert paywall)
- **-> composer**: retention-curve sync points (where music should swell for re-engagement)
```

**Why this contract:** Retention is a feedback loop, not a forward pass. The hook expert reviews the screenplay's draft, suggests rewrites, and also reviews the editor's rough cut to suggest pacing changes. This is the first bidirectional expert in the suite.

#### Production (`production`)

**Contract:** Coordinates pre-production: casting (with performer), location (with scene_builder), scheduling (with continuity).

**Edges to add:**
- `production.related_skills: [performer, scene_builder, continuity, screenplay, style_genome]`
- Update `performer.related_skills` to add `production` (casting notes flow into performer)
- Update `continuity.related_skills` to add `production` (scheduling constraints)

**Collaboration block in production/SKILL.md:**
```markdown
## Collaboration

- **<- screenplay**: scene list, character list, location requirements
- **<- style_genome**: visual style constraints (which wardrobe palette fits the genre)
- **-> performer**: casting_notes.json — character physical/emotional requirements,
  age range, vocal register, chemistry requirements
- **-> scene_builder**: location_brief.json — which locations need building vs location-scouting
- **-> continuity**: shooting_schedule.json — shot order optimized for location/actor availability
```

#### Compliance & Marketing (`compliance_marketing`)

**Contract:** Reviews screenplay (for forbidden topics) and editor (for platform-specific cuts).

**Edges to add:**
- `compliance_marketing.related_skills: [screenplay, editor, hook_retention, style_genome]`
- Update `screenplay.related_skills` to add `compliance_marketing`
- Update `editor.related_skills` to add `compliance_marketing`

**Collaboration block in compliance_marketing/SKILL.md:**
```markdown
## Collaboration

- **<- screenplay**: full script (for forbidden-topic review per CN content rules)
- **<- editor**: final cut (for platform-specific duration limits, aspect ratio)
- **<- hook_retention**: paywall timestamps (to align with platform 短剧 payment cadence)
- **-> screenplay**: compliance_notes.json — flagged lines/scenes to revise, with suggested alternatives
- **-> editor**: platform_cuts.json — per-platform duration targets (抖音 60s, 快手 90s, 小程序剧 3min/ep)
- **-> hook_retention**: viral_elements.json — which viral tropes the platform currently rewards
```

### Full 18-Expert Graph (Adjacency List)

| Expert | related_skills (post-v2) |
|--------|--------------------------|
| style_genome | screenplay, drawer, colorist, editor, composer, scene_builder, performer, continuity, production, compliance_marketing |
| screenplay | style_genome, scene_builder, editor, performer, composer, hook_retention, compliance_marketing |
| scene_builder | screenplay, style_genome, colorist, performer, editor, drawer, animator, foley, continuity, cinematographer, production |
| drawer | screenplay, continuity, colorist, animator, style_genome, cinematographer |
| animator | drawer, scene_builder, editor, performer, colorist, continuity, cinematographer |
| colorist | screenplay, style_genome, drawer, continuity, animator |
| editor | screenplay, animator, composer, voicer, continuity, mixer, cinematographer, hook_retention, compliance_marketing |
| composer | screenplay, editor, style_genome, mixer, foley, spatial_audio, hook_retention |
| performer | screenplay, continuity, scene_builder, editor, drawer, animator, voicer, style_genome, production |
| foley | animator, performer, scene_builder, composer, mixer, spatial_audio, continuity |
| spatial_audio | scene_builder, foley, voicer, composer, mixer, editor, continuity |
| mixer | voicer, composer, foley, spatial_audio, editor, continuity |
| voicer | screenplay, performer, editor, mixer, spatial_audio |
| continuity | drawer, animator, colorist, style_genome, screenplay, production |
| **cinematographer** (NEW) | scene_builder, animator, editor, screenplay, continuity, drawer, hook_retention |
| **hook_retention** (NEW) | screenplay, editor, cinematographer, compliance_marketing, composer |
| **production** (NEW) | performer, scene_builder, continuity, screenplay, style_genome |
| **compliance_marketing** (NEW) | screenplay, editor, hook_retention, style_genome |

### Graph Invariants (must hold after v2)

1. **Symmetry is NOT required.** `screenplay` listing `hook_retention` does not require `hook_retention` to list `screenplay` back. The graph is directed (`A depends on B` ≠ `B depends on A`). However, where collaboration is genuinely bidirectional (hook_retention ↔ screenplay), both edges should exist.
2. **No new `expert_id` collisions.** The four new IDs (`cinematographer`, `hook_retention`, `production`, `compliance_marketing`) must not match any existing `expert_id` in the 14-expert set. Verified: none collide.
3. **Backward compatibility.** Existing 14 experts' `expert_id` values are unchanged. The 14 experts gain new entries in their `related_skills` arrays but no removals. A workflow that previously invoked `screenplay → scene_builder` still works.
4. **Snake_case naming.** New expert directory names use snake_case to match `scene_builder`, `style_genome` convention. Multi-word names: `hook_retention`, `compliance_marketing` (not `hook-retention` or `hookRetention`).

## Bilingual Content Architecture

### Decision Matrix

| Artifact | Primary Language | Secondary | Rationale |
|----------|------------------|-----------|-----------|
| YAML frontmatter (keys, values) | English | — | Parser expects English keys; `expert_id`, `metrics` are identifiers |
| `description` field in YAML | English (one line) | — | Used by `skills_list` for discovery; English for Hermes community compatibility |
| H1, H2 section headings | English | CN in parens | `# Screenplay Expert (剧本专家)` — matches existing 14-expert convention |
| Body paragraphs | English summary + CN explanation | — | EN structure for parser/community; CN carries the actual industry knowledge for 短剧主场 |
| Reference files (`references/*.md`) | Chinese primary | EN glossary at top | Short-drama industry knowledge is overwhelmingly Chinese-source; forcing EN would lose nuance |
| Eval prompts (`prompts/*.yaml`) | Bilingual (`input.en`, `input.cn`) | — | Runner tests both language paths; some short-drama patterns only surface in CN prompts |
| Eval reports (`reports/*.json`) | English (machine-generated) | — | For developer consumption; structured data, not prose |

### Bilingual Reference File Pattern

```markdown
# 短剧钩子设计 / Short-Drama Hook Design

**Source:** 短剧编剧实战手册 (2024 ed.) + 抖音/快手 creator interviews
**Copyright:** Fair-use excerpt + original synthesis
**Last verified:** 2026-06-15

## EN Glossary / 术语对照

| EN | 中文 | Notes |
|----|------|-------|
| Hook | 钩子 | First 3 seconds of a short drama |
| Paywall cliffhanger | 付费卡点 | The moment a paywall appears mid-episode |
| Retention curve | 留存曲线 | % of viewers still watching at second N |
| Cold open | 冷开场 | Pre-title-sequence hook |

## When to Read This / 何时阅读

Read when the user requests a 短剧 (short drama), 竖屏短剧 (vertical short drama),
or any video under 180 seconds targeting 抖音/快手/小程序剧 platforms.

阅读时机:当用户请求创作短剧、竖屏短剧,或任何 180 秒以内、面向抖音/快手/小程序剧平台的视频时。

## Core Principles / 核心原则

**1. 三秒生死 (3-Second Life-or-Death)**
The first 3 seconds determine whether 80% of viewers scroll past. The hook
must present conflict, mystery, or visceral emotion immediately — no establishing
shots, no slow fades.

前三秒决定 80% 观众是否划走。钩子必须立即呈现冲突、悬念或强烈情绪——
不能用建立镜头,不能慢淡入。

**Example / 示例:**
- ❌ Bad: 开场是城市夜景空镜,慢慢推近到主角窗户。
- ✅ Good: 开场第一帧就是主角在哭,手里攥着一张离婚证。

...
```

## Eval Harness Structure

### File Layout (Option A: centralized)

```
skills/movie-experts/
├── _eval/
│   ├── README.md                    # How to run evals
│   ├── runner.py                    # Main entry point
│   ├── judge_prompt.md              # System prompt for the judge model
│   ├── snapshot.py                  # One-shot: capture baseline SKILL.md state
│   ├── baseline/                    # gitignored after first capture
│   │   └── <expert>/SKILL.md
│   ├── reports/                     # gitignored output
│   │   ├── <expert>/
│   │   │   └── <prompt-id>_<timestamp>.json
│   │   └── summary.md               # Aggregated comparison table
│   └── requirements.txt             # httpx, pyyaml (judge calls via HTTP)
├── screenplay/
│   └── prompts/                     # Input fixtures live WITH the expert
│       ├── 01-three-act-structure.yaml
│       ├── 02-subtext-dialogue.yaml
│       └── 03-emotion-curve.yaml
├── [other experts with their own prompts/]
└── .gitignore                       # ignores _eval/baseline/, _eval/reports/
```

**Why prompts/ live with each expert but runner.py is centralized:** Prompts are domain knowledge (the screenplay expert knows what makes a good screenplay test case). The runner is infrastructure (knows how to invoke Hermes and call a judge). Mixing them would couple domain changes to infra changes.

### Judge Prompt Skeleton (`_eval/judge_prompt.md`)

```markdown
You are a double-blind judge evaluating two AI-generated movie production outputs.

You will see:
- A user request (the task)
- A scoring rubric with dimensions and weights
- Response A (you do not know which model/system produced this)
- Response B (you do not know which model/system produced this)

Score EACH dimension for EACH response independently on the scale described
in the rubric. Do not let your score on one dimension influence another.

Then declare which response is stronger overall, or "TIE" if they are within
0.05 of each other on the weighted total.

Output JSON:
{
  "response_a": { "<dimension>": <score>, ... },
  "response_b": { "<dimension>": <score>, ... },
  "weighted_total_a": <float>,
  "weighted_total_b": <float>,
  "winner": "A" | "B" | "TIE",
  "rationale": "<2-3 sentences explaining the key differentiator>"
}

Do NOT mention which response you prefer in your rationale until after
the JSON block. Stay neutral.
```

### Snapshot Protocol

**Before REFACTOR-A begins (one-time):**

```bash
cd skills/movie-experts
python _eval/snapshot.py --capture
# Creates _eval/baseline/<expert>/SKILL.md for all 14 existing experts
# Commits the baseline to git as a tagged commit: "eval-baseline-v1"
git add _eval/baseline/
git commit -m "chore(eval): capture pre-refactor baseline for double-blind eval"
git tag eval-baseline-v1
```

**After REFACTOR-A + REFS-A (per-expert, incremental):**

```bash
python _eval/runner.py --expert screenplay --all-prompts
# Outputs to _eval/reports/screenplay/<timestamp>.json
# Compares current screenplay/SKILL.md against _eval/baseline/screenplay/SKILL.md
```

**Why snapshot before refactor, not after:** The baseline is the "before" state. If we snapshot after refactor, we lose the comparison point. The PROJECT.md requirements (`EVAL-01`) explicitly call for before/after double-blind scoring.

## Suggested Build Order with Rationale

The PROJECT.md lists 9 active work items. Their dependencies dictate a phase order:

```
Phase 0: Foundation
├── DOC-01 (partial: top-level README skeleton, collaboration graph draft)
│   Rationale: Need a written graph before updating related_skills in code.
│   Partial because the full README needs eval results to be credible.
└── EVAL-01 (skeleton: snapshot.py + runner.py + judge_prompt.md)
    Rationale: The eval harness MUST exist before REFACTOR-A so we can
    measure improvement. Building it first also forces concrete prompt
    fixtures, which surface ambiguities in expert contracts early.

Phase 1: Audit
└── AUDIT-01 (GAP-REPORT.md for each of 14 experts)
    Depends on: nothing.
    Produces: per-expert gap report identifying (a) prompt improvement points,
    (b) metric revisions, (c) reference topics needed.
    Rationale: REFACTOR-A without an audit is guesswork. The audit tells us
    WHAT to change in each SKILL.md.

Phase 2: Refactor + Refs (parallel tracks per expert)
├── REFACTOR-A (per-expert, after its AUDIT-01 entry)
├── REFS-A (per-expert, after its AUDIT-01 entry)
└── CORPUS-01 (feeds REFS-A: curates the actual reference content)
    Ordering: CORPUS-01 must produce source material before REFS-A can
    format it into references/*.md. But CORPUS-01 can run in parallel
    with REFACTOR-A since they touch different files.

Phase 3: New Experts (after Phase 2 stabilizes contracts)
├── EXPERT-CINE (cinematographer)
├── EXPERT-HOOK (hook_retention)
├── EXPERT-PROD (production)
└── EXPERT-COMPLI (compliance_marketing)
    Depends on: Phase 2 must complete for the experts they integrate with.
    Cinematographer needs scene_builder and animator refactored first
    (to know their new contract). Hook & Retention needs screenplay's
    rewrite hooks in place. Compliance needs screenplay and editor stable.
    Production is least dependent (mostly additive) and can start earlier.

Phase 4: Verification + Docs
├── EVAL-01 (full run: every expert, every prompt, before/after comparison)
├── BILINGUAL-01 (final pass: verify CN/EN consistency across all 18 experts)
└── DOC-01 (complete: top-level README with collaboration graph, RAG usage,
    eval results summary)
    Depends on: all prior phases. The README cites eval numbers and the
    final 18-expert graph.
```

### Dependency Reasoning

| Work Item | Depends On | Blocks | Notes |
|-----------|------------|--------|-------|
| DOC-01 (partial) | — | Phase 0 graph draft | Skeleton only; full version in Phase 4 |
| EVAL-01 (skeleton) | — | REFACTOR-A measurement | Must exist before refactor to capture baseline |
| AUDIT-01 | EVAL-01 skeleton (for prompt fixtures) | REFACTOR-A, REFS-A | Audit informs what to change |
| CORPUS-01 | AUDIT-01 (knows what topics to curate) | REFS-A | Curation takes longest; start early |
| REFACTOR-A | AUDIT-01, EVAL-01 baseline snapshot | New expert integration | Per-expert; can be parallelized |
| REFS-A | AUDIT-01, CORPUS-01 | — | Per-expert; parallel with REFACTOR-A |
| EXPERT-CINE | REFACTOR-A for scene_builder, animator | DOC-01 final | Needs new contracts in place |
| EXPERT-HOOK | REFACTOR-A for screenplay, editor | DOC-01 final | Bidirectional integration |
| EXPERT-PROD | REFACTOR-A for performer, continuity (light dep) | DOC-01 final | Can start earlier if needed |
| EXPERT-COMPLI | REFACTOR-A for screenplay, editor | DOC-01 final | Reviews downstream output |
| EVAL-01 (full) | All REFACTOR-A + all new experts | DOC-01 final | The credibility anchor |
| BILINGUAL-01 | All content written | DOC-01 final | Consistency pass |
| DOC-01 (full) | Everything | — | Final deliverable |

### Critical Path

The longest dependency chain is:
```
EVAL-01 skeleton → AUDIT-01 → CORPUS-01 → REFS-A (screenplay)
                                       ↘
                                        REFACTOR-A (screenplay) → EXPERT-HOOK → EVAL-01 (full) → DOC-01
```

CORPUS-01 is the bottleneck. Curation of 4 source types × 18 experts is the largest single work item. Recommend splitting CORPUS-01 by source type (not by expert) so that the screenplay-relevant slice of all 4 sources can land first, unblocking EXPERT-HOOK.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Python Code in SKILL.md

**What:** Embedding Python in the SKILL.md body to "automate" RAG queries.
**Why bad:** Hermes skills are pure markdown. The loader (`agent/skill_utils.parse_frontmatter`) extracts the body as a string and injects it as a user message. Any Python would be inert text, not executable. Worse, it would confuse the LLM into thinking it should call interpreter tools.
**Instead:** Use prompt language. "Read `references/foo.md`" is the API. The LLM has a `read_file` tool already.

### Anti-Pattern 2: Hard-Requiring Memory Plugin Tools

**What:** Writing "You MUST call `mem0_search` before drafting" in SKILL.md.
**Why bad:** If the memory plugin isn't configured, `mem0_search` isn't in the tool schema. The LLM will either hallucinate the call or refuse to proceed. Either way, the skill breaks for users without the plugin.
**Instead:** Use conditional phrasing: "If `mem0_search` is available in your tools, query for X. Otherwise rely on the static references." The LLM's tool schema is the source of truth.

### Anti-Pattern 3: Duplicating Reference Content Across Experts

**What:** Copying `style_genome`'s 5D matrix explanation into `colorist`'s refs.
**Why bad:** Drift. When the 5D matrix evolves, the copy becomes stale. Two sources of truth.
**Instead:** Use relative-path cross-references: `../style_genome/references/genome-decomposition.md`. The LLM can follow these links.

### Anti-Pattern 4: Registering Eval Runner as a Hermes Tool

**What:** Calling `registry.register(name="eval_runner", ...)` in `_eval/runner.py`.
**Why bad:** Exposes developer-only benchmark scaffolding to the production agent. Users would see an `eval_runner` tool they didn't ask for. The eval harness is offline tooling, not an in-conversation capability.
**Instead:** Keep `_eval/runner.py` as a standalone script invoked from the shell. The leading underscore in `_eval/` signals "internal" per Python convention; Hermes' skill loader won't discover it as a skill directory anyway (it scans for `SKILL.md`, not `_eval/`).

### Anti-Pattern 5: Breaking Backward Compatibility on Existing expert_id Values

**What:** Renaming `scene_builder` to `scene_builder_v2` during refactor.
**Why bad:** Existing user workflows that invoke `/scene_builder` break. The `related_skills` arrays in other experts point to the old name.
**Instead:** Keep all 14 `expert_id` values unchanged. Refactor happens in-place. The version field in YAML frontmatter (`version: 1.0.0` → `version: 2.0.0`) is the versioning signal, not the ID.

### Anti-Pattern 6: Single-Pass Bilingual Translation

**What:** Writing all SKILL.md content in English first, then translating to Chinese in a separate pass at the end.
**Why bad:** Short-drama industry knowledge is Chinese-primary. Translating EN→CN at the end produces stilted, unnatural Chinese that loses domain nuance (e.g., 卡点, 爆款, 投流 are untranslatable without context).
**Instead:** Write CN-primary content for short-drama-specific sections (hooks, paywalls, compliance). Write EN-primary for universal craft sections (camera grammar, color theory). Use the bilingual section pattern (Pattern 3 above) to interleave.

## Scalability Considerations

| Concern | At 14 experts | At 18 experts (v1 target) | At 30+ experts (hypothetical v2) |
|--------|---------------|---------------------------|----------------------------------|
| related_skills graph density | Average ~5 edges per node | Average ~6 edges per node | Becomes unwieldy; consider grouping experts into clusters |
| Reference corpus size | ~14 × 5 files = 70 files | ~18 × 5 files = 90 files | Needs index file (`_shared/index.md`) for navigation |
| Eval runtime | ~14 × 3 prompts × 2 variants = 84 runs | ~18 × 3 × 2 = 108 runs | Parallelize runner; consider sampling prompts |
| SKILL.md size per expert | ~130 lines (current) | ~180 lines (post-refactor) | Risk of prompt bloat; extract more into refs |
| Cross-expert ref maintenance | Manual link checking | Manual + CI lint recommended | Automated link checker in `_eval/` |

For v1 (18 experts), the architecture holds without structural changes. For v2 (30+), consider:
- Clustering experts into sub-suites (`pre-production/`, `production/`, `post-production/`, `distribution/`) with intra-cluster and inter-cluster `related_skills`
- A top-level `_shared/` directory for cross-cutting refs (glossary, encoding matrices, style genome)
- Automated dead-link detection in CI

## Sources

- **Direct file reads (HIGH confidence):**
  - `skills/movie-experts/screenplay/SKILL.md` — existing expert structure
  - `skills/movie-experts/scene_builder/SKILL.md` — camera/spatial concerns, multi-edge related_skills
  - `skills/creative/comfyui/SKILL.md` — references table + scripts invocation pattern
  - `skills/creative/manim-video/SKILL.md` — references table + bilingual-friendly structure
  - `skills/research/research-paper-writing/SKILL.md` — references linking pattern
  - `agent/memory_provider.py` — MemoryProvider ABC interface, system_prompt_block contract
  - `plugins/memory/__init__.py` — memory plugin discovery, one-active-provider limit
  - `plugins/memory/mem0/__init__.py` — tool schemas (mem0_search, mem0_profile, mem0_conclude), system_prompt_block content
  - `tools/memory_tool.py:707` — built-in `memory` tool registration
  - `.planning/codebase/ARCHITECTURE.md` — skill invocation flow, system prompt tiers
  - `.planning/codebase/CONVENTIONS.md` — SKILL.md schema, bilingual strategy, naming
  - `.planning/PROJECT.md` — requirements, constraints, key decisions

- **Codebase observations (HIGH confidence):**
  - `git show 4290ab2` — confirmed the 14 experts are pure markdown, no Python
  - `grep related_skills` across all 14 experts — produced the adjacency list in this doc
  - `ls skills/creative/comfyui/{references,scripts}` — confirmed references/ + scripts/ coexistence pattern
  - `find skills -name references -type d` — found 20 skills with references folders, validating the pattern is established
