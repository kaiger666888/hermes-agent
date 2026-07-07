# Phase 62: EXPERT-YAML-TRANSFORM - Pattern Map

**Mapped:** 2026-07-08
**Files analyzed:** 14 (12 new agent YAMLs + 1 validation script + 1 transform log)
**Analogs found:** 12 / 12 new YAMLs have a shipped analog; 2 utility files have pattern references

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `~/.hermes/agents/animation_studio.agent.yaml` | agent YAML — animation pipeline expert | declarative-config | `~/.hermes/agents/audio_pipeline.agent.yaml` | role-match (multi-stage pipeline expert) |
| `~/.hermes/agents/colorist.agent.yaml` | agent YAML — visual/look expert (write_file) | declarative-config | `~/.hermes/agents/character_designer.agent.yaml` | role-match (analysis + write_file for JSON artifacts) |
| `~/.hermes/agents/compliance_gate.agent.yaml` | agent YAML — hard-gate authority | declarative-config | `~/.hermes/agents/continuity_auditor.agent.yaml` | exact (hard-gate pattern, "I am HARD gate") |
| `~/.hermes/agents/creative_source.agent.yaml` | agent YAML — upstream ideation expert (write_file) | declarative-config | `~/.hermes/agents/screenplay.agent.yaml` | role-match (upstream-of-pipeline + write_file for JSON artifacts) |
| `~/.hermes/agents/documentary_maker.agent.yaml` | agent YAML — narrative structure expert (analysis-only) | declarative-config | `~/.hermes/agents/theory_critic.agent.yaml` | role-match (analysis-only, theory/frameworks-heavy) |
| `~/.hermes/agents/performer.agent.yaml` | agent YAML — performance/character expert (analysis-only) | declarative-config | `~/.hermes/agents/character_designer.agent.yaml` | role-match (performance/character domain) |
| `~/.hermes/agents/production.agent.yaml` | agent YAML — production/advisory expert (analysis-only) | declarative-config | `~/.hermes/agents/editor.agent.yaml` | role-match (analysis-only advisory, consumes upstream, outputs specs) |
| `~/.hermes/agents/prompt_injector.agent.yaml` | agent YAML — AI-native prompt translator (write_file) | declarative-config | `~/.hermes/agents/character_designer.agent.yaml` | role-match (analysis + write_file for JSON artifacts) |
| `~/.hermes/agents/scene_builder.agent.yaml` | agent YAML — scene/3D expert (analysis-only, deprecated source) | declarative-config | `~/.hermes/agents/cinematographer.agent.yaml` | role-match (scene composition domain, Phase 17 absorption context) |
| `~/.hermes/agents/script_auditor.agent.yaml` | agent YAML — hard-gate critic (NOT creative writer) | declarative-config | `~/.hermes/agents/continuity_auditor.agent.yaml` | exact (hard-gate + critic-not-creator framing) |
| `~/.hermes/agents/storyboard_designer.agent.yaml` | agent YAML — visual design expert (analysis-only, deprecated source) | declarative-config | `~/.hermes/agents/cinematographer.agent.yaml` | role-match (visual shot design, Phase 17 absorption context) |
| `~/.hermes/agents/visual_executor.agent.yaml` | agent YAML — dreamina CLI executor (sub_steps, MOST COMPLEX) | declarative-config | `~/.hermes/agents/audio_pipeline.agent.yaml` | exact (multi-sub-step expressed in persona text) |
| `scripts/validate_phase62_yamls.py` | utility — batch validation script | batch | `agent/registry_loader.py` + `62-RESEARCH.md` §Code Examples | exact (validation pattern reference) |
| `.planning/phases/62-expert-yaml-transform/62-TRANSFORM-LOG.md` | audit log — transform provenance | transform | (none — derive from CONTEXT + RESEARCH) | no analog (free-form per-phase log) |

## Pattern Assignments

### `~/.hermes/agents/animation_studio.agent.yaml` (agent YAML — animation pipeline expert)

**Analog:** `~/.hermes/agents/audio_pipeline.agent.yaml` (both are pipeline experts with multi-stage chains expressed in persona text — audio_pipeline weaves 6 sub-steps into persona; animation_studio weaves the 12-stage production pipeline)

**Source SKILL.md:** `/data/workspace/kais-hermes-skills/skills/movie-experts/animation_studio/SKILL.md` (v1.0.0, NOT in §2.2-§2.16 — use §2.1 defaults)

**Frontmatter pattern** (copy from `audio_pipeline.agent.yaml:1-6`, sub `animation_studio`):
```yaml
name: animation_studio
description: 'Animation Studio Expert: Disney 4-stage system (early/feature/live-action/magic-kingdom)
  + 12-stage production pipeline + cross-cultural adaptation (花木兰 case) for 2D/3D/stop-motion
  animation.'
version: 1.0.0
```

**Persona rewrite pattern** (mirror `audio_pipeline.agent.yaml:7-16` — cite anchors + declare pipeline atomicity):
```yaml
# audio_pipeline example (lines 7-16) — replicate this style:
persona: 'I am the Animation Studio Expert (动画制片专家). I orchestrate the Disney 4-stage
  system (early / feature / live-action / magic-kingdom) and the 12-stage animation production
  pipeline [...]. My Story Structure Score metric catches structural regressions [...].
  Cites: Disney 4-stage taxonomy, 12-stage pipeline, cross-cultural adaptation (花木兰 hero-journey).'
```
**Required persona elements (per §2.1 + RESEARCH.md Per-Expert table row 1):**
- First-person voice
- Cite Disney 4-stage system + 12-stage pipeline + cross-cultural (花木兰) anchor
- Declare Story Structure Score metric
- Defer to peers (visual_executor on execution, colorist on color script, audio_pipeline on musical storytelling/voice casting)

**Tools whitelist** (§2.1 default — analysis-only):
```yaml
tools:
- hermes_llm
- read_file
- search_files
```

**related_agents** (verbatim from SKILL `metadata.hermes.related_skills` — all are becoming agents in this phase):
```yaml
related_agents:
- screenplay
- visual_executor
- colorist
- cinematographer
- audio_pipeline
- hook_retention
```

**Lineage block** (byte-compatible with shipped — see Shared Patterns §Lineage):
```yaml
lineage:
  derived_from_skill_id: animation_studio
  derived_from_repo: kais-hermes-skills
  transform_date: '2026-07-08'
  transform_notes: 'Rule IDs: §2.1 defaults (animation_studio not in §2.2-§2.16). Persona rewritten
    from SKILL body; Disney 4-stage + 12-stage pipeline + cross-cultural (花木兰) surfaced.
    Analysis-only tools — advisory/expert-knowledge output. Transform timestamp: 2026-07-08.'
  skill_sha256: <compute via hashlib.sha256(content.encode("utf-8")).hexdigest()>
```

**Uniform defaults** (copy verbatim from `audio_pipeline.agent.yaml:99-117`):
```yaml
memory_scope: per_agent
refs: []
evolution_log: []
fitness_score: null
platforms:
- linux
- macos
- windows
round_table_eligible: true
default_invocation: mcp_tool
```

**Tags / expert_id / metrics / prerequisites** (copy verbatim from SKILL `metadata.hermes`).

---

### `~/.hermes/agents/colorist.agent.yaml` (agent YAML — CxSxZ color narrative + LUT plan)

**Analog:** `~/.hermes/agents/character_designer.agent.yaml` (both produce JSON artifacts via `write_file`)

**Source SKILL.md:** `/data/workspace/kais-hermes-skills/skills/movie-experts/colorist/SKILL.md` (§2.14 — explicit per-expert rule)

**§2.14 rule mapping** (from `04-MIGRATION-PATH.md:551-559`):
- `tools`: `[hermes_llm, read_file, search_files, write_file]` — **+write_file** (LUT plan artifacts)
- `persona`: declare "integrate with visual_executor at Step 7" (V8.6 pipeline handoff)
- `related_agents` from SKILL: `[screenplay, style_genome, visual_executor, continuity_auditor, production, theory_critic, cinematographer]` (7 agents)

**Persona rewrite pattern** (mirror `character_designer.agent.yaml:7-15` — first-person + cite anchors + declare artifact format):
```yaml
# character_designer example (lines 7-15) — replicate this style with colorist-specific content:
persona: 'I am the Colorist Expert (色彩专家). I produce the CxSxZ 3D color intent (Chroma ×
  Saturation × Brightness) with 28 core combinations ensuring color language serves narrative
  emotion across every shot. My output is a color_intent.json + LUT plan (lift/gamma/gain)
  consumed by visual_executor at Step 7 of the V8.6 pipeline. I defer to style_genome on the
  5D vector (D1 color dimension) and integrate with visual_executor at Step 7 for the 视觉种子+风格化
  atomic operation. Cross-shot ΔE2000 ≤ 3.0 (production) is my quality gate.'
```

**Tools whitelist** (§2.14 — +write_file):
```yaml
tools:
- hermes_llm
- read_file
- search_files
- write_file
```

**Lineage block** (cite §2.14 explicitly in transform_notes):
```yaml
lineage:
  derived_from_skill_id: colorist
  derived_from_repo: kais-hermes-skills
  transform_date: '2026-07-08'
  transform_notes: 'Rule IDs: §2.14 colorist (CxSxZ color narrative + LUT plan, Step 7 integration
    with visual_executor). +write_file load-bearing for LUT plan artifacts. Bellantoni 8-color
    vocabulary + Hurkman digital pipeline + cross-cultural (CN audience divergence) surfaced in
    persona. Transform timestamp: 2026-07-08.'
  skill_sha256: <64-hex SHA-256 of source SKILL.md>
```

---

### `~/.hermes/agents/compliance_gate.agent.yaml` (agent YAML — hard-gate red-line authority)

**Analog:** `~/.hermes/agents/continuity_auditor.agent.yaml` (both are HARD gates with explicit "I am HARD gate, not advisory" persona framing)

**Source SKILL.md:** `/data/workspace/kais-hermes-skills/skills/movie-experts/compliance_gate/SKILL.md` (§2.15)

**§2.15 rule mapping + CONTEXT override** (from `04-MIGRATION-PATH.md:573-581` + `62-CONTEXT.md:46`):
- `tools`: `[hermes_llm, read_file, search_files]` (analysis-only)
- `persona`: declare hard-gate authority + 3 v9.0 red-lines (`redline_emotion_desensitize` / `redline_no_cold_open` / `redline_unfinished_ending`)
- **CONTEXT OVERRIDE on `default_invocation`:** §2.15 + §3.6 recommend `disabled` initially, but CONTEXT.md locks `mcp_tool` for all 12 active experts. **Follow CONTEXT (locked decision)** — `default_invocation: mcp_tool`.

**Persona hard-gate pattern** (mirror `continuity_auditor.agent.yaml:5-12` — declare HARD gate + block authority):
```yaml
# continuity_auditor hard-gate pattern (lines 5-12) — replicate with compliance_gate content:
persona: 'I am the Compliance Gate Expert (合规与宣发门专家). I am a HARD gate, not advisory —
  every production must pass my 3 v9.0 red-lines before distribution: (1) redline_emotion_desensitize
  (no emotion desensitization), (2) redline_no_cold_open (no cold open without context),
  (3) redline_unfinished_ending (no unfinished endings). I also enforce CN content-rules +
  AIGC labeling + per-platform distribution rules. My authority is red-line — I can block pipeline
  progression. Per CONTEXT locked decision, I am invoked via mcp_tool (not disabled).'
```

**Tools whitelist** (§2.15 — analysis-only):
```yaml
tools:
- hermes_llm
- read_file
- search_files
```

**Lineage block** (cite §2.15 + CONTEXT override in transform_notes):
```yaml
lineage:
  derived_from_skill_id: compliance_gate
  derived_from_repo: kais-hermes-skills
  transform_date: '2026-07-08'
  transform_notes: 'Rule IDs: §2.15 compliance_gate (hard-gate red-line authority, 3 v9.0 red-lines).
    CONTEXT.md locked decision overrides §2.15/§3.6 recommendation: default_invocation=mcp_tool
    (NOT disabled) per all-12-active-experts policy. Renamed from legacy compliance_marketing
    (aliases: [compliance_marketing]). Transform timestamp: 2026-07-08.'
  skill_sha256: <64-hex SHA-256 of source SKILL.md>
```

---

### `~/.hermes/agents/creative_source.agent.yaml` (agent YAML — Snowflake+SCAMPER ideation, +write_file)

**Analog:** `~/.hermes/agents/screenplay.agent.yaml` (both are upstream-of-pipeline generators producing JSON artifacts)

**Source SKILL.md:** `/data/workspace/kais-hermes-skills/skills/movie-experts/creative_source/SKILL.md` (§2.3)

**§2.3 rule mapping** (from `04-MIGRATION-PATH.md:301-309`):
- `tools`: `[hermes_llm, read_file, search_files, write_file]` — **+write_file** (StoryKernel JSON artifact)
- `persona`: declare StoryKernel JSON output format explicitly (load-bearing for write_file justification)
- **FILTER `topic_curator`** from related_agents (skill does NOT exist — `ls /data/workspace/kais-hermes-skills/skills/movie-experts/topic_curator` → not found, VERIFIED 2026-07-08)

**Persona rewrite pattern** (mirror `screenplay.agent.yaml:5-18` — first-person + cite method anchors + declare artifact format):
```yaml
# screenplay example pattern (lines 5-18) — replicate this style with creative_source content:
persona: 'I am the Creative Source Expert (创意源头专家). I mine structural social narratives from
  6 stratified layers (L1 institutional / L2 technological / L3 demographic / L4 spatial /
  L5 intergenerational-contract / L6 psychosocial) producing StoryKernel JSON seeds. My method
  backbone is the Snowflake Method 10-step + SCAMPER 7-verb variation framework. I am DECOUPLED
  from style_genome (style_genome defines HOW to tell; I define WHAT to tell). My output is a
  StoryKernel JSON scaffold written to ~/.hermes/projects/<slug>/story_kernel.json — write_file
  is load-bearing. Calling sequence: creative_source → style_genome → screenplay.'
```

**Tools whitelist** (§2.3 — +write_file):
```yaml
tools:
- hermes_llm
- read_file
- search_files
- write_file
```

**related_agents** (FILTERED — drop `topic_curator`):
```yaml
# Source: metadata.hermes.related_skills = [style_genome, screenplay, hook_retention, compliance_gate, topic_curator, prompt_injector]
# Filtered: topic_curator (skill does not exist as of 2026-07-08)
related_agents:
- style_genome
- screenplay
- hook_retention
- compliance_gate
- prompt_injector
```

**Lineage block** (cite §2.3 + filter rationale in transform_notes):
```yaml
lineage:
  derived_from_skill_id: creative_source
  derived_from_repo: kais-hermes-skills
  transform_date: '2026-07-08'
  transform_notes: 'Rule IDs: §2.3 creative_source (Snowflake Method 10-step + SCAMPER 7-verb,
    StoryKernel JSON output format). +write_file load-bearing for StoryKernel scaffold persistence.
    Filtered topic_curator from related_agents (skill does not exist as of 2026-07-08 — dangling
    edge avoided). Transform timestamp: 2026-07-08.'
  skill_sha256: <64-hex SHA-256 of source SKILL.md>
```

---

### `~/.hermes/agents/documentary_maker.agent.yaml` (agent YAML — documentary types + 4 schools)

**Analog:** `~/.hermes/agents/theory_critic.agent.yaml` (both are analysis-only theory/frameworks-heavy experts)

**Source SKILL.md:** `/data/workspace/kais-hermes-skills/skills/movie-experts/documentary_maker/SKILL.md` (NOT in §2.2-§2.16 — use §2.1 defaults)

**Persona rewrite pattern** (mirror `theory_critic.agent.yaml:5-12` — first-person + cite theoretical anchors + declare advisory-not-blocking):
```yaml
# theory_critic example (lines 5-12) — replicate with documentary_maker content:
persona: I am the Documentary Maker Expert (纪录片创作专家). I apply the 6 documentary types
  (poetic / expository / observational / participatory / reflexive / performative per Bill Nichols)
  and the 4 documentary schools (Flaherty / Vertov / Grierson / Direct-Vérité) as my theoretical
  backbone. My ethnographic methods (observation, fieldwork, interview ethics) ground documentary-style
  短剧 / 微电影 in observed reality rather than invented narrative. I am advisory (not a hard gate)
  — I surface documentary-craft concerns to screenplay, cinematographer, and editor.
```

**Tools whitelist** (§2.1 default — analysis-only):
```yaml
tools:
- hermes_llm
- read_file
- search_files
```

**related_agents** (verbatim from SKILL — all becoming agents):
```yaml
related_agents:
- screenplay
- cinematographer
- editor
- production
- compliance_gate
- theory_critic
```

**Lineage block** (cite §2.1 defaults — not in §2.2-§2.16):
```yaml
lineage:
  derived_from_skill_id: documentary_maker
  derived_from_repo: kais-hermes-skills
  transform_date: '2026-07-08'
  transform_notes: 'Rule IDs: §2.1 defaults (documentary_maker not in §2.2-§2.16 — post-v10.0
    addition). Persona rewritten from SKILL body; 6 documentary types (Nichols) + 4 schools
    (Flaherty/Vertov/Grierson/Direct-Vérité) + ethnographic methods surfaced. Analysis-only
    tools. Transform timestamp: 2026-07-08.'
  skill_sha256: <64-hex SHA-256 of source SKILL.md>
```

---

### `~/.hermes/agents/performer.agent.yaml` (agent YAML — Performance-4D matrix, deprecated source)

**Analog:** `~/.hermes/agents/character_designer.agent.yaml` (both performance/character domain — character_designer actually inherited performer's voice+behavioral-tics per Phase 17 deprecation)

**Source SKILL.md:** `/data/workspace/kais-hermes-skills/skills/movie-experts/performer/SKILL.md` (NOT in §2.2-§2.16; **SKILL is marked `status: deprecated`** with `inheritance_targets: [character_designer, screenplay]`)

**⚠️ DEPRECATION RESOLUTION** (CONTEXT.md locks decision — transform as active despite deprecated source):
- The source SKILL.md declares `deprecated: true` + `deprecated_reason` (function folded into character_designer + screenplay per Phase 17).
- CONTEXT.md's 12-active-experts list overrides this — performer is being reactivated as an independent agent in this phase.
- Document the deprecation-history in `transform_notes` so the lineage is auditable.

**Persona rewrite pattern** (mirror `character_designer.agent.yaml:7-15` — first-person + cite method anchors):
```yaml
persona: 'I am the Performer Expert (表演/动作专家). I define character action and emotion via
  the Performance-4D matrix (Emotion × Body × Space × Pace parametric dispatch) backed by
  Stanislavski ExB (Emotion×Body), Laban Effort (weight/space/time/flow), and Meisner
  truth-of-moment technique. My emotion_accuracy metric validates that character action matches
  the emotional intent from screenplay. I defer to character_designer on identity contracts and
  to screenplay on dialogue subtext.'
```

**Tools whitelist** (§2.1 default — analysis-only):
```yaml
tools:
- hermes_llm
- read_file
- search_files
```

**related_agents** (keep `scene_builder` — it's becoming an agent in this same phase):
```yaml
# Source: metadata.hermes.related_skills = [screenplay, continuity_auditor, scene_builder, editor, visual_executor, audio_pipeline, style_genome, production]
related_agents:
- screenplay
- continuity_auditor
- scene_builder
- editor
- visual_executor
- audio_pipeline
- style_genome
- production
```

**Lineage block** (cite §2.1 + deprecation history):
```yaml
lineage:
  derived_from_skill_id: performer
  derived_from_repo: kais-hermes-skills
  transform_date: '2026-07-08'
  transform_notes: 'Rule IDs: §2.1 defaults (performer not in §2.2-§2.16). CONTEXT.md locked
    decision reactivates performer as an active agent (overriding source SKILL deprecated:true
    status from Phase 17). Performance-4D matrix (ExBxSxP) + Stanislavski ExB + Laban Effort +
    Meisner surfaced in persona. Analysis-only tools. Transform timestamp: 2026-07-08.'
  skill_sha256: <64-hex SHA-256 of source SKILL.md>
```

---

### `~/.hermes/agents/production.agent.yaml` (agent YAML — AI-relevant production subset, analysis-only)

**Analog:** `~/.hermes/agents/editor.agent.yaml` (both are analysis-only advisory experts that consume upstream specs and output data — editor outputs EDL, production outputs budget/asset-reuse plan)

**Source SKILL.md:** `/data/workspace/kais-hermes-skills/skills/movie-experts/production/SKILL.md` (NOT in §2.2-§2.16 — use §2.1 defaults)

**Persona rewrite pattern** (mirror `editor.agent.yaml:5-12` — first-person + cite framework + declare output format):
```yaml
# editor example (lines 5-12) — replicate with production content:
persona: 'I am the Production Expert (制作管理专家). I own the AI-relevant production subset —
  character LoRA spec, per-scene wardrobe, lighting intent layer, GPU/render budget allocation,
  and cross-shot asset reuse plan. My budget_adherence metric governs resource discipline.
  I explicitly EXCLUDE live-action subset (crews / permits / insurance — deferred to v2 per
  PROD-07). I consume character_designer identity contracts + cinematographer shot intent +
  colorist LUT plan to produce a unified production spec. I am advisory (output is specs as
  data, not file writes).'
```

**Tools whitelist** (§2.1 default — analysis-only):
```yaml
tools:
- hermes_llm
- read_file
- search_files
```

**related_agents** (verbatim from SKILL — all becoming agents):
```yaml
related_agents:
- character_designer
- visual_executor
- continuity_auditor
- colorist
- compliance_gate
- cinematographer
- audio_pipeline
- theory_critic
- documentary_maker
```

**Lineage block** (cite §2.1 defaults):
```yaml
lineage:
  derived_from_skill_id: production
  derived_from_repo: kais-hermes-skills
  transform_date: '2026-07-08'
  transform_notes: 'Rule IDs: §2.1 defaults (production not in §2.2-§2.16). Persona rewritten
    from SKILL body; AI-relevant subset (LoRA / wardrobe / lighting / GPU budget / asset reuse)
    + live-action exclusion surfaced. Budget Adherence metric cited. Analysis-only tools
    (advisory role — outputs specs as data, not file writes). Transform timestamp: 2026-07-08.'
  skill_sha256: <64-hex SHA-256 of source SKILL.md>
```

---

### `~/.hermes/agents/prompt_injector.agent.yaml` (agent YAML — AI-native prompt translator, +write_file)

**Analog:** `~/.hermes/agents/character_designer.agent.yaml` (both produce JSON artifacts via `write_file` + have "decoupled" framing in persona)

**Source SKILL.md:** `/data/workspace/kais-hermes-skills/skills/movie-experts/prompt_injector/SKILL.md` (§2.9)

**§2.9 rule mapping** (from `04-MIGRATION-PATH.md:441-449`):
- `tools`: `[hermes_llm, read_file, search_files, write_file]` — **+write_file** (prompt JSON artifacts)
- `persona`: AI-native translator (intent → dreamina/Runway/Kling/Veo/Sora tokens)
- `derived_from_skill_id`: `prompt_injector` (SKILL.md EXISTS post-v3.0 — verified)

**Persona rewrite pattern** (mirror `character_designer.agent.yaml:7-15` — first-person + cite AI-native marker + decoupling):
```yaml
persona: 'I am the Prompt Injector Expert (提示注入专家). I am an AI-native node — no traditional
  counterpart exists. I translate upstream human intent (visual_intent + style_genome 5D vector
  + character_assets) into model-ready prompts (model_prompts + consistency_context) for dreamina
  CLI / Runway / Kling / Veo / Sora. My cross_call_consistency metric enforces that prompt tokens
  remain stable across multi-shot generation; my prompt_token_efficiency metric balances
  expressiveness vs token budget. My output is a prompt JSON artifact (write_file load-bearing).
  I integrate with visual_executor at Step 7 of the V8.6 pipeline.'
```

**Tools whitelist** (§2.9 — +write_file):
```yaml
tools:
- hermes_llm
- read_file
- search_files
- write_file
```

**Lineage block** (cite §2.9 + AI-native marker):
```yaml
lineage:
  derived_from_skill_id: prompt_injector
  derived_from_repo: kais-hermes-skills
  transform_date: '2026-07-08'
  transform_notes: 'Rule IDs: §2.9 prompt_injector (bilingual prompt translator, AI-native expert).
    +write_file load-bearing for prompt JSON artifacts. derived_from_skill_id=prompt_injector
    (SKILL.md exists post-v3.0 — verified). Cross-call consistency context + token budget
    surfaced in persona. Transform timestamp: 2026-07-08.'
  skill_sha256: <64-hex SHA-256 of source SKILL.md>
```

---

### `~/.hermes/agents/scene_builder.agent.yaml` (agent YAML — FxSxA scene matrix, deprecated source)

**Analog:** `~/.hermes/agents/cinematographer.agent.yaml` (both scene composition domain — cinematographer absorbed scene_builder per Phase 17, but CONTEXT lists scene_builder as transform target)

**Source SKILL.md:** `/data/workspace/kais-hermes-skills/skills/movie-experts/scene_builder/SKILL.md` (§2.7 absorption context; **SKILL is marked `status: deprecated`** with `inheritance_targets: [cinematographer, style_genome]`)

**⚠️ IDENTITY AMBIGUITY RESOLUTION** (RESEARCH.md §Common Pitfalls #3):
- §2.7 says scene_builder was "absorbed" into cinematographer (Phase 17).
- BUT scene_builder has its own SKILL.md with distinct content (FxSxA matrix, Blender 4.x previz, Pallasmaa space-as-character doctrine).
- CONTEXT.md lists scene_builder as 1 of 12 transform targets.
- **Resolution:** transform scene_builder as a standalone agent (its content is distinct from cinematographer's shot-intent layer). Cite §2.7 absorption context in transform_notes.

**Persona rewrite pattern** (mirror `cinematographer.agent.yaml:6-14` — first-person + cite anchors + declare domain distinctness):
```yaml
# cinematographer example (lines 6-14) — replicate with scene_builder content + distinctness claim:
persona: I am the Scene Builder Expert (三维场景建构专家). I produce the FxSxA scene matrix
  (Function × Scale × Atmosphere) + Blender 4.x previsualization + Pallasmaa space-as-character
  doctrine + 8 architectural patterns for cinematic scene design. My narrative_space_match
  metric validates that scene design serves story. I am DISTINCT from cinematographer —
  cinematographer owns shot-grammar rules (axis, framing, camera moves); I own the 3D scene
  container (spatial geometry, architectural storytelling, previz workflow). [§2.7 absorption
  context: although Phase 17 marked scene_builder deprecated into cinematographer + style_genome,
  CONTEXT.md reactivates scene_builder as an independent agent because its FxSxA matrix +
  Blender previz + Pallasmaa doctrine content is distinct from cinematographer's shot-intent layer.]
```

**Tools whitelist** (§2.1 default — analysis-only):
```yaml
tools:
- hermes_llm
- read_file
- search_files
```

**related_agents** (verbatim from SKILL — keep all, including deprecated-name peers):
```yaml
related_agents:
- screenplay
- style_genome
- colorist
- performer
- editor
- visual_executor
- audio_pipeline
- continuity_auditor
- cinematographer
- production
```

**Lineage block** (cite §2.7 absorption context + CONTEXT reactivation):
```yaml
lineage:
  derived_from_skill_id: scene_builder
  derived_from_repo: kais-hermes-skills
  transform_date: '2026-07-08'
  transform_notes: 'Rule IDs: §2.1 defaults + §2.7 absorption context. CONTEXT.md reactivates
    scene_builder as an independent agent (overriding source SKILL deprecated:true status from
    Phase 17). FxSxA matrix + Blender 4.x previz + Pallasmaa space-as-character doctrine
    surfaced — content distinct from cinematographer shot-intent layer. §2.7 absorption into
    cinematographer+style_genome documented; standalone transform chosen per CONTEXT. Transform
    timestamp: 2026-07-08.'
  skill_sha256: <64-hex SHA-256 of source SKILL.md>
```

---

### `~/.hermes/agents/script_auditor.agent.yaml` (agent YAML — 5-dimension hard-gate critic, NOT creative writer)

**Analog:** `~/.hermes/agents/continuity_auditor.agent.yaml` (both are HARD gates + critic-not-creator framing)

**Source SKILL.md:** `/data/workspace/kais-hermes-skills/skills/movie-experts/script_auditor/SKILL.md` (§2.5)

**§2.5 rule mapping** (from `04-MIGRATION-PATH.md:350-358`):
- `tools`: `[hermes_llm, read_file, search_files]` (analysis-only — reads screenplay outputs but never writes)
- `persona`: 5-dim critic (NOT creative writer) — predicts completion %, hard-gates on `< 65% predicted_completion`
- **Critical framing contract:** Persona MUST explicitly say "I am NOT a creative writer; I critique, I do not generate" to prevent model drift into rewriting screenplay's work

**Persona hard-gate + critic-not-writer pattern** (mirror `continuity_auditor.agent.yaml:5-12` — declare HARD gate + block authority + critic framing):
```yaml
# continuity_auditor hard-gate pattern (lines 5-12) — replicate with script_auditor content:
persona: 'I am the Script Auditor Expert (剧本审计专家). I am a HARD gate, not advisory —
  every script must pass my 5-dimension audit before production begins: (1) narrative_tension,
  (2) dialogue_naturalness, (3) pacing, (4) emotional_arc, (5) hook_strength. I predict expected
  完播率 (completion rate) band from script structure alone — no rendering, no A/B test required.
  I hard-gate on < 65% predicted_completion. CRITICAL FRAMING: I am NOT a creative writer; I
  critique, I do not generate. I never rewrite screenplay''s work — that would create circular
  feedback. My audit_score_correlation metric validates prediction accuracy against post-release
  completion data.'
```

**Tools whitelist** (§2.5 — analysis-only):
```yaml
tools:
- hermes_llm
- read_file
- search_files
```

**Lineage block** (cite §2.5 + critic-not-writer framing):
```yaml
lineage:
  derived_from_skill_id: script_auditor
  derived_from_repo: kais-hermes-skills
  transform_date: '2026-07-08'
  transform_notes: 'Rule IDs: §2.5 script_auditor (5-dimension critic, NOT creative writer).
    Hard-gate on < 65% predicted_completion explicit in persona. Critic-not-writer framing
    load-bearing — prevents model drift to creative rewriting. Analysis-only tools. Transform
    timestamp: 2026-07-08.'
  skill_sha256: <64-hex SHA-256 of source SKILL.md>
```

---

### `~/.hermes/agents/storyboard_designer.agent.yaml` (agent YAML — shot decomposition, deprecated source)

**Analog:** `~/.hermes/agents/cinematographer.agent.yaml` (both visual shot design domain — cinematographer defines rules, storyboard_designer applies them)

**Source SKILL.md:** `/data/workspace/kais-hermes-skills/skills/movie-experts/storyboard_designer/SKILL.md` (NOT in §2.2-§2.16; **SKILL is marked `status: deprecated`** with `inheritance_targets: [cinematographer]`)

**⚠️ DEPRECATION RESOLUTION** (same pattern as performer + scene_builder):
- Source SKILL is `status: deprecated` (folded into cinematographer's `composition_lock` subtask per Phase 17).
- CONTEXT.md reactivates storyboard_designer as an independent agent in this phase.
- Document deprecation history in transform_notes.

**Persona rewrite pattern** (mirror `cinematographer.agent.yaml:6-14` — first-person + declare decoupling):
```yaml
persona: I am the Storyboard Designer Expert (分镜设计师). I decompose screenplay scenes into
  per-shot Storyboard JSON with camera params, action, duration, reference image pointers, and
  4D anchoring (depth / identity / lighting / temporal). I am DECOUPLED from cinematographer —
  cinematographer defines the shot-grammar RULES (axis, framing, camera moves); I APPLY those
  rules to produce the executable shot list. My axis_compliance_rate metric validates that my
  storyboard obeys cinematographer's axis rules. [CONTEXT.md reactivates storyboard_designer
  as an independent agent — source SKILL deprecated:true status from Phase 17 overridden.]
```

**Tools whitelist** (§2.1 default — analysis-only):
```yaml
tools:
- hermes_llm
- read_file
- search_files
```

**related_agents** (keep `scene_builder` — becoming agent in this phase):
```yaml
related_agents:
- screenplay
- cinematographer
- scene_builder
- character_designer
- visual_executor
- editor
- continuity_auditor
```

**Lineage block** (cite §2.1 defaults + deprecation override):
```yaml
lineage:
  derived_from_skill_id: storyboard_designer
  derived_from_repo: kais-hermes-skills
  transform_date: '2026-07-08'
  transform_notes: 'Rule IDs: §2.1 defaults (storyboard_designer not in §2.2-§2.16). CONTEXT.md
    reactivates storyboard_designer as an independent agent (overriding source SKILL deprecated:true
    status from Phase 17). Shot decomposition + 4D anchoring (depth/identity/lighting/temporal)
    surfaced in persona. Decoupling from cinematographer (rules vs application) declared
    explicitly. Analysis-only tools. Transform timestamp: 2026-07-08.'
  skill_sha256: <64-hex SHA-256 of source SKILL.md>
```

---

### `~/.hermes/agents/visual_executor.agent.yaml` (agent YAML — MOST COMPLEX, sub_steps [drawer, animator])

**Analog:** `~/.hermes/agents/audio_pipeline.agent.yaml` (EXACT match — both have multi-sub-step pipelines that MUST be expressed in persona text, NOT as YAML fields, because schema `additionalProperties: false` rejects `sub_steps`)

**Source SKILL.md:** `/data/workspace/kais-hermes-skills/skills/movie-experts/visual_executor/SKILL.md` (§2.10) — MOST COMPLEX source (435 lines, 7 ref files, declares `sub_steps: [drawer, animator]`)

**§2.10 rule mapping** (from `04-MIGRATION-PATH.md:463-471`):
- `tools`: `[hermes_llm, dreamina_cli, read_file, write_file, patch]` — **+dreamina_cli + write_file + patch**
- `persona`: declare intent-vs-execution split load-bearing ("I do NOT decide intent")
- **sub_steps MUST go in persona + description text, NOT as YAML field** (schema top-level `additionalProperties: false` — see RESEARCH §Common Pitfalls #2)

**⚠️ sub_steps-in-persona pattern (HIGHEST-RISK PITFALL)** — extract from `audio_pipeline.agent.yaml:1-16`:

This is the canonical pattern for expressing multi-step pipelines in agent YAML. audio_pipeline has 6 sub_steps (voicer/lip_sync/composer/foley/mixer/spatial_audio) and expresses them in **two places**:

**Pattern 1 — sub_steps in `description` field** (from `audio_pipeline.agent.yaml:2-5`):
```yaml
description: 'Audio Pipeline Expert: unified 6-sub-step audio production (voicer TTS,
  lip_sync audio-driven sync, composer music, foley SFX, mixer mastering, spatial_audio
  3D encoding) for cinematic audio consistency. Sub-steps: [voicer, lip_sync, composer,
  foley, mixer, spatial_audio].'
```
**Apply to visual_executor** — description ends with `Sub-steps: [drawer, animator].` (this exact string is already present in source SKILL.md:3).

**Pattern 2 — sub_steps woven into `persona` text** (from `audio_pipeline.agent.yaml:7-16`):
```yaml
persona: 'I am the Audio Pipeline Expert (音频管线专家). I orchestrate the 6-sub-step audio
  production chain atomically: voicer (TTS — character voice from character_designer''s
  L3 specs), lip_sync (audio-driven video-gen sync for talking-head benchmarks), composer
  (music score — emotion_curve-driven MusicGen prompt tokens), foley (sound effects
  — physical-audio impact-sync), mixer (mastering — LUFS compliance, dialogue intelligibility,
  frequency masking score, ducking), spatial_audio (3D encoding — Dolby Atmos + binaural
  HRTF + ambience reverb for immersive reality anchor). My sub-steps are ATOMIC —
  partial output is rejected (CONTEXT D-7 one-directional contract with hook_retention:
  I receive BGM sync markers; I do not push back). My theoretical backbone is Michel
  Chion''s audio-vision (material credibility + forced sound + reality anchor stability).'
```
**Apply to visual_executor** — weave sub_steps `[drawer, animator]` into persona with per-step role:
```yaml
persona: 'I am the Visual Executor Expert (视觉执行专家). I orchestrate the 2-sub-step visual
  production chain atomically: drawer (FLUX 2 Klein 9B cinematic still image generation + LoRA +
  IP-Adapter + InstantID for character consistency + first-frame I-frames), animator (2026
  Hermes-catalog video gen models — veo3.1 / kling-v3-4k / pixverse-v6 / ltx-2.3 / seedance-2.0
  — for camera motion + temporal consistency, consuming drawer''s first_frame as I-frame input).
  My sub-steps are ATOMIC — the drawer→animator handoff is now an INTRA-expert handoff
  (same expert_id visual_executor), eliminating the consistency-context drift of v1''s
  inter-expert edge. I do NOT decide intent (cinematographer''s job) — I EXECUTE given intent
  via dreamina CLI (text2image / image2image / multimodal2video). My aesthetic_score +
  character_consistency + temporal_consistency metrics gate visual quality. Intent-vs-execution
  split is load-bearing — I refuse to second-guess cinematographer''s shot intent.'
```

**❌ ANTI-PATTERN — DO NOT add `sub_steps` as a YAML field** (would SC#2 byte-fail):
```yaml
# WRONG — schema top-level additionalProperties: false rejects this:
sub_steps: [drawer, animator]   # ← will fail jsonschema validation
```

**Tools whitelist** (§2.10 — +dreamina_cli + write_file + patch):
```yaml
tools:
- hermes_llm
- dreamina_cli
- read_file
- write_file
- patch
```

**related_agents** (11 agents — largest collaboration DAG, per SKILL `metadata.hermes.related_skills`):
```yaml
related_agents:
- screenplay
- continuity_auditor
- colorist
- style_genome
- compliance_gate
- cinematographer
- production
- editor
- character_designer
- audio_pipeline
- prompt_injector
```

**prerequisites** (source SKILL declares `hermes_llm_vision` prerequisite):
```yaml
prerequisites:
  tools:
  - hermes_llm
  - hermes_llm_vision
```

**Lineage block** (cite §2.10 + sub_steps handling + intent-vs-execution):
```yaml
lineage:
  derived_from_skill_id: visual_executor
  derived_from_repo: kais-hermes-skills
  transform_date: '2026-07-08'
  transform_notes: 'Rule IDs: §2.10 visual_executor (dreamina_cli + write_file + patch, sub_steps
    [drawer, animator], intent-vs-execution split). sub_steps expressed in description + persona
    text (NOT as YAML field per schema additionalProperties:false — mirrors audio_pipeline.agent.yaml
    pattern). +dreamina_cli + write_file + patch load-bearing for sub-step iteration. Intra-expert
    drawer→animator handoff (Phase 14 MERGE-01) explicit in persona. Phase 63 SC#3 round table
    smoke will use this agent — persona robustness verified. Transform timestamp: 2026-07-08.'
  skill_sha256: <64-hex SHA-256 of source SKILL.md>
```

---

### `scripts/validate_phase62_yamls.py` (utility — batch validation script)

**Analog pattern:** `agent/registry_loader.py` (existing v11.0 validation pattern) + `62-RESEARCH.md` §Code Examples (SHA + YAML dump + jsonschema snippets)

**Imports pattern** (from `agent/registry_loader.py:53-63`):
```python
from __future__ import annotations

import hashlib
import jsonschema
import yaml
from pathlib import Path
```

**Validation function pattern** (from `62-RESEARCH.md:519-543` — VERIFIED against 9 shipped YAMLs):
```python
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
```

**SHA-256 computation pattern** (from `62-RESEARCH.md:499-517` — VERIFIED, encoding explicit per CLAUDE.md PLW1514):
```python
def compute_skill_sha256(skill_path: Path) -> str:
    """Compute SHA-256 of source SKILL.md content (UTF-8 / LF)."""
    content = skill_path.read_text(encoding="utf-8")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
```

**Batch loop pattern** (from `agent/registry_loader.py:312-323` — flat glob + sorted):
```python
TARGET_DIR = Path.home() / ".hermes" / "agents"
SCHEMA_PATH = Path(".planning/research/v10-orchestrator-design/agents-schema.yaml")
NEW_YAMLS = [
    "animation_studio", "colorist", "compliance_gate", "creative_source",
    "documentary_maker", "performer", "production", "prompt_injector",
    "scene_builder", "script_auditor", "storyboard_designer", "visual_executor",
]

for name in NEW_YAMLS:
    yaml_path = TARGET_DIR / f"{name}.agent.yaml"
    errors = validate_agent_yaml(yaml_path, SCHEMA_PATH)
    if errors:
        print(f"FAIL {name}: {errors[0]}")
    else:
        print(f"PASS {name}")
```

**Error handling pattern** (from `agent/registry_loader.py:73-94` — structured error class optional but recommended):
```python
# Optional: raise RegistryValidationError with json_path + invalid_field for typed 400 responses
# (mirrors agent/registry_loader.py WR-02 fix). For Phase 62 inline validation, simple print
# of error message is sufficient.
```

---

### `.planning/phases/62-expert-yaml-transform/62-TRANSFORM-LOG.md` (audit log)

**Analog:** none (free-form per-phase audit log — derive structure from CONTEXT.md SC#3 + RESEARCH.md §"Transform Log Format")

**Recommended structure** (from `62-RESEARCH.md:566-581`):
```markdown
# Phase 62 Transform Log

**Transform execution:** 2026-07-08
**Operator:** Claude (GSD pattern mapper → planner → executor)
**Source repo:** /data/workspace/kais-hermes-skills @ commit <hash>
**Schema:** .planning/research/v10-orchestrator-design/agents-schema.yaml (Draft 2020-12, Phase 45 stable)
**Rules source:** 04-MIGRATION-PATH.md §2 (75-cell per-expert table)

## Per-Expert Transform Records

| # | Expert | §2 Rule ID | tools | source SHA-256 (first 12) | transform_notes summary | SC#2 pass |
|---|--------|-----------|-------|---------------------------|-------------------------|-----------|
| 1 | animation_studio | §2.1 defaults | analysis-only | `<12-hex>` | Disney 4-stage + 12-stage pipeline | PASS |
| 2 | colorist | §2.14 | +write_file | `<12-hex>` | CxSxZ + LUT plan + Step 7 integration | PASS |
| ... | ... | ... | ... | ... | ... | ... |
| 12 | visual_executor | §2.10 | +dreamina_cli +write_file +patch | `<12-hex>` | sub_steps in persona; intent-vs-execution | PASS |

## Edge Cases Resolved

- scene_builder deprecated source reactivated per CONTEXT (§2.7 absorption context documented)
- performer deprecated source reactivated per CONTEXT (Phase 17 inheritance_targets overridden)
- storyboard_designer deprecated source reactivated per CONTEXT (Phase 17 absorption overridden)
- creative_source `topic_curator` filtered from related_agents (skill does not exist)
- compliance_gate `default_invocation: mcp_tool` per CONTEXT override (NOT disabled per §2.15)

## SC Verification

- SC#1: 21 total YAMLs in ~/.hermes/agents/ (9 shipped + 12 new)
- SC#2: all 12 new YAMLs byte-pass Draft202012Validator.validate()
- SC#3: all 12 new YAMLs have non-empty lineage.skill_sha256 + transform_notes cite rule IDs
- SC#4: spot-check 1 YAML (visual_executor) — lineage.skill_sha256 traces to source SKILL.md SHA
```

---

## Shared Patterns

### Uniform Defaults Block (apply to all 12 new YAMLs)

**Source:** All 9 shipped YAMLs (`screenplay`, `style_genome`, `editor`, `cinematographer`, `character_designer`, `continuity_auditor`, `hook_retention`, `theory_critic`, `audio_pipeline`)

**Apply to:** All 12 new agent YAMLs (identical block)

```yaml
# From screenplay.agent.yaml:25,36,52-66 + audio_pipeline.agent.yaml:22,33,110-117
memory_scope: per_agent        # v11.0 default
refs: []                       # 9-shipped convention: refs surfaced in persona text, not paths
evolution_log: []              # curator-managed, append-only — DO NOT hand-edit
fitness_score: null            # curator-computed — NOT operator-set
platforms:                     # SKILL `platforms` copy
- linux
- macos
- windows
round_table_eligible: true     # all 12 are active experts
default_invocation: mcp_tool   # all 12 are active (NOT skill_fallback / disabled)
```

### Lineage Block Template (apply to all 12 new YAMLs)

**Source:** All 9 shipped YAMLs use this exact 5-field structure (no `source_sha` / `transform_rule_id` / `transform_timestamp` — see RESEARCH §Common Pitfalls #1)

**Apply to:** All 12 new agent YAMLs

```yaml
# Template — substitute {expert_name}, {transform_notes_text}, {skill_sha64}
lineage:
  derived_from_skill_id: {expert_name}        # = expert_name (found invariant)
  derived_from_repo: kais-hermes-skills       # constant for all 12
  transform_date: '2026-07-08'                # ISO date (schema format:date)
  transform_notes: 'Rule IDs: §2.X {expert} (...). {additional free-text including transform timestamp}.'
  skill_sha256: {64-hex SHA-256 of source SKILL.md content}
```

**⚠️ CRITICAL — DO NOT add SC#3 fields as lineage sub-fields** (RESEARCH §Common Pitfalls #1):
- SC#3 mentions `source_sha` / `transform_rule_id` / `transform_timestamp` as semantic concepts.
- Lineage $def has `additionalProperties: false` — adding these as sub-fields will SC#2 byte-fail.
- **Mapping:** `source_sha` → `skill_sha256` (semantic equivalent); `transform_rule_id` + `transform_timestamp` → cite in `transform_notes` free-text.

### Frontmatter Field Order (byte-compat with shipped)

**Source:** All 9 shipped YAMLs use this exact field order (verified via `diff <(head -7 ...)`)

**Apply to:** All 12 new agent YAMLs (use PyYAML `sort_keys=False`)

```yaml
# Order (from screenplay.agent.yaml + audio_pipeline.agent.yaml):
# 1. name
# 2. description
# 3. version
# 4. persona
# 5. tools
# 6. memory_scope
# 7. lineage
# 8. refs
# 9. tags
# 10. expert_id
# 11. metrics
# 12. prerequisites
# 13. related_agents
# 14. evolution_log
# 15. fitness_score
# 16. platforms
# 17. round_table_eligible
# 18. default_invocation
```

**PyYAML dump flags** (from `62-RESEARCH.md:547-563`):
```python
yaml.dump(agent, f, default_flow_style=False, sort_keys=False, allow_unicode=True, width=100)
```

### Persona Rewrite Rules (apply to all 12 new YAMLs)

**Source:** `screenplay.agent.yaml:5-18` (canonical example) + RESEARCH §Pattern 2

**Apply to:** All 12 new agent YAMLs

| Rule | Requirement |
|------|-------------|
| Voice | First-person ("I am", "I do", "My output is") |
| Anchor refs | Cite 1-2 method anchors by name (e.g., "Snyder 15-beat", "CxSxZ encoding") |
| Contracts | Declare load-bearing contracts in-line (e.g., "HOOK-09 marker arrays remain contract-load-bearing") |
| Peer deference | Defer to peers on their domains (e.g., "I defer to cinematographer on shot intent") |
| Output scope | Never generate full output unprompted (contribute slice when orchestrator asks) |
| Hard-gate | For hard-gate experts (compliance_gate, script_auditor): declare "I am HARD gate / I can block pipeline" |
| Execution-only | For visual_executor: declare "I do NOT decide intent" (intent-vs-execution split) |
| Sub-steps | For multi-sub-step experts (visual_executor): weave sub_steps into persona text, NOT as YAML field |

### SHA-256 Computation Pattern (apply to all 12 new YAMLs)

**Source:** `screenplay.agent.yaml:35` (skill_sha256 verified against source) + RESEARCH §Code Examples

```python
# VERIFIED 2026-07-08 — screenplay SKILL.md SHA matches shipped YAML lineage.skill_sha256
import hashlib
from pathlib import Path

def compute_skill_sha256(skill_path: Path) -> str:
    content = skill_path.read_text(encoding="utf-8")  # encoding explicit per CLAUDE.md PLW1514
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

# Usage:
SOURCE_REPO = Path("/data/workspace/kais-hermes-skills/skills/movie-experts")
for name in ["animation_studio", "colorist", ...]:
    skill_path = SOURCE_REPO / name / "SKILL.md"
    sha = compute_skill_sha256(skill_path)
    # → populate lineage.skill_sha256
```

### Validation Pattern (apply to all 12 new YAMLs)

**Source:** `agent/registry_loader.py:209-269` (existing v11.0 `load_one_agent_yaml`) + RESEARCH §Code Examples

```python
# VERIFIED — all 9 shipped YAMLs pass with 0 errors
import jsonschema
import yaml
from pathlib import Path

SCHEMA_PATH = Path(".planning/research/v10-orchestrator-design/agents-schema.yaml")
schema = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
validator = jsonschema.Draft202012Validator(schema)

for name in ["animation_studio", "colorist", ...]:
    yaml_path = Path.home() / ".hermes" / "agents" / f"{name}.agent.yaml"
    agent = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    errors = list(validator.iter_errors(agent))
    if errors:
        first = sorted(errors, key=lambda e: list(e.absolute_path))[0]
        raise ValueError(f"{name}: {first.message} at {first.json_path}")
```

### Tags / expert_id / metrics / prerequisites (copy verbatim from SKILL frontmatter)

**Source:** All 9 shipped YAMLs copy these fields verbatim from `metadata.hermes.*`

**Apply to:** All 12 new agent YAMLs — copy these 4 fields verbatim from source SKILL.md frontmatter:

| Field | SKILL source | YAML target | Transform |
|-------|--------------|-------------|-----------|
| `tags` | `metadata.hermes.tags` | `tags` | verbatim copy (lowercase hyphen pattern `^[a-z0-9-]+$`) |
| `expert_id` | `metadata.hermes.expert_id` | `expert_id` | verbatim copy (FOUND-08 preserved) |
| `metrics` | `metadata.hermes.metrics` | `metrics` | verbatim copy |
| `prerequisites` | `prerequisites` (top-level) | `prerequisites` | verbatim copy (sub-field: `tools: [...]`) |

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `.planning/phases/62-expert-yaml-transform/62-TRANSFORM-LOG.md` | audit log | transform | Per-phase free-form log — no existing pattern; derive structure from CONTEXT SC#3 + RESEARCH §"Transform Log Format" |

All 12 new agent YAMLs have at least a role-match analog among the 9 shipped YAMLs. The 2 utility files (`scripts/validate_phase62_yamls.py` + `62-TRANSFORM-LOG.md`) derive patterns from `agent/registry_loader.py` + RESEARCH §Code Examples + SC#3 requirements respectively.

---

## Edge Case Summary (cross-cutting)

| Edge Case | Affected File(s) | Resolution | Cite in transform_notes |
|-----------|------------------|------------|-------------------------|
| **sub_steps NOT in schema** | `visual_executor.agent.yaml` | Express `sub_steps: [drawer, animator]` in `description` + `persona` text, NOT as YAML field | "sub_steps expressed in persona + description text per schema additionalProperties:false (mirrors audio_pipeline pattern)" |
| **SC#3 fields NOT in schema** | All 12 YAMLs | Map `source_sha`→`skill_sha256`; cite `transform_rule_id` + `transform_timestamp` in `transform_notes` free-text | "Rule IDs: §2.X {expert} (...). Transform timestamp: 2026-07-08." |
| **scene_builder deprecated source** | `scene_builder.agent.yaml` | CONTEXT reactivates as standalone (distinct FxSxA + Blender + Pallasmaa content); document §2.7 absorption | "CONTEXT.md reactivates scene_builder... §2.7 absorption into cinematographer+style_genome documented" |
| **performer deprecated source** | `performer.agent.yaml` | CONTEXT reactivates as standalone (Performance-4D + Stanislavski + Laban + Meisner content); document Phase 17 inheritance_targets | "CONTEXT.md reactivates performer... overriding source SKILL deprecated:true from Phase 17" |
| **storyboard_designer deprecated source** | `storyboard_designer.agent.yaml` | CONTEXT reactivates as standalone (shot decomposition + 4D anchoring content); document Phase 17 absorption into cinematographer | "CONTEXT.md reactivates storyboard_designer... overriding source SKILL deprecated:true from Phase 17" |
| **creative_source dangling topic_curator** | `creative_source.agent.yaml` | Filter `topic_curator` from related_agents (skill does not exist — `ls` VERIFIED 2026-07-08) | "Filtered topic_curator from related_agents (skill does not exist as of 2026-07-08)" |
| **compliance_gate default_invocation override** | `compliance_gate.agent.yaml` | CONTEXT locks `mcp_tool` (all 12 active); override §2.15/§3.6 `disabled` recommendation | "CONTEXT.md locked decision overrides §2.15/§3.6 recommendation: default_invocation=mcp_tool" |
| **scene_builder / performer in peer related_skills** | `performer.agent.yaml`, `storyboard_designer.agent.yaml` | Keep `scene_builder` / `performer` in related_agents (both becoming agents in this same phase) | (no special note needed — graph stays connected) |

---

## Metadata

**Analog search scope:**
- `~/.hermes/agents/*.agent.yaml` (9 shipped YAMLs — all read end-to-end)
- `agent/registry_loader.py` (validation pattern reference)
- `.planning/research/v10-orchestrator-design/agents-schema.yaml` (schema field reference)
- `.planning/research/v10-orchestrator-design/04-MIGRATION-PATH.md` §2 (per-expert transform rules — 9 rule sections read)
- `/data/workspace/kais-hermes-skills/skills/movie-experts/{12 experts}/SKILL.md` (source frontmatter — 12 files read)
- `.planning/phases/62-expert-yaml-transform/62-CONTEXT.md` + `62-RESEARCH.md` (upstream inputs)

**Files scanned:** 9 shipped YAMLs + 12 source SKILL.mds + 1 schema + 1 registry_loader + 2 upstream inputs = **25 files**

**Pattern extraction date:** 2026-07-08
