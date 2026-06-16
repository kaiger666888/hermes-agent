# Phase 16: New AI-Native Expert (prompt_injector) - Context

**Gathered:** 2026-06-17
**Status:** Ready for planning
**Mode:** Auto-generated (new expert creation — pattern from Phase 13-15 + node spec from v2.0 PRFP)

<domain>
## Phase Boundary

Create a brand-new movie-expert: `prompt_injector` (提示注入). This is the only NEW expert in v3.0 — no v1 precedent exists. Per `.planning/research/v2-pipeline-design/02-NODE-SPECS.md §2.7`:

- **Layer:** 2
- **Role:** visual_intent
- **v1 expert_id:** NEW (no v1 precedent — `skills-mapping.yaml:95-99` `mapping_type: new_ai_native`)
- **Core task:** 把 intent 翻译为 model-ready prompt + cross-call consistency context
- **I/O:** in: visual_intent + style_genome + character_assets; out: model_prompts + consistency_context
- **Success criteria:** cross_call_consistency ≥ 0.85; prompt_token_efficiency ≤ 4000 tokens/call
- **Fail modes:** consistency_drift / prompt_overload
- **Fallback:** carry context + split prompt
- **Budget:** ¥50/episode (compute) · 30s · stable_2026
- **AIGC transformation:** ai_native (无传统对应)
- **First principles:** per `00-FIRST-PRINCIPLES.md §4.7` (D3.5+D2.4)
- **Rationale:** AI-native 必要 + invariant ownership

Per ROADMAP §16 success criteria:
1. `skills/movie-experts/prompt_injector/SKILL.md` exists with full content (EN structure + CN prose per META-03)
2. `metadata.hermes.expert_id: prompt_injector`
3. `metadata.hermes.related_skills: [creative_source, cinematographer, visual_executor, audio_pipeline]` (per Phase 8 §2.7)
4. `metadata.hermes.metrics: [cross_call_consistency, prompt_token_efficiency]` (per nodes.yaml)
5. 4 refs in `prompt_injector/references/` (prompt engineering patterns + cross-call consistency literature)
6. README 21-expert inventory lists prompt_injector as NEW (Phase 16 entry)

Operations:
1. Create `skills/movie-experts/prompt_injector/` directory with SKILL.md + references/ (4 refs) + GAP-REPORT.md
2. Update `creative_source`, `cinematographer`, `visual_executor`, `audio_pipeline` to add `prompt_injector` to their related_skills (bidirectional edge sync)
3. Update README inventory + corpus tree + DAG diagram + glossary entry
4. **No redirect stub needed** — prompt_injector has no predecessor to redirect from

Out-of-scope: deprecations (Phase 17), validation/docs (Phase 18).

</domain>

<decisions>
## Implementation Decisions

### Expert Identity (Established by node spec + skills-mapping.yaml)
- **Source-of-truth:** `.planning/research/v2-pipeline-design/02-NODE-SPECS.md §2.7` (canonical node spec) + `nodes.yaml` + `skills-mapping.yaml:95-99` (`new_ai_native` mapping type)
- **No aliases:** Since prompt_injector has no v1 predecessor, NO `metadata.hermes.aliases` array (FOUND-08 doesn't apply to new nodes)
- **Directory:** `skills/movie-experts/prompt_injector/` with SKILL.md + references/ (4 refs) + GAP-REPORT.md

### Frontmatter Schema (per CLAUDE.md Skill File Conventions)
```yaml
---
name: prompt_injector
description: "Prompt Injector Expert: ..."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  tools: [hermes_llm]
metadata:
  hermes:
    tags: [movie, prompt-engineering, cross-call-consistency, model-prompts, ai-native, ...]
    related_skills: [creative_source, cinematographer, visual_executor, audio_pipeline]
    expert_id: prompt_injector
    metrics: [cross_call_consistency, prompt_token_efficiency]
---
```

### 4 Refs (recommend — Claude's discretion on exact titles)
1. **Prompt engineering patterns** — general patterns: few-shot, chain-of-thought, template structures, decomposition
2. **Cross-call consistency literature** — how to maintain character/scene/style consistency across multiple LLM/gen-model calls (LoRA references, IP-Adapter, identity-preserving prompting)
3. **Token budget management** — strategies for staying under 4000 tokens/call (chunking, hierarchical prompts, context windows)
4. **Model-specific prompt templates** — actual template examples for FLUX 2, Veo/Kling, etc. (cross-reference visual_executor refs)

### Claude's Discretion
- Exact ref titles, ordering, and content depth
- SKILL.md body structure (follow other experts' pattern: `## When to use this skill` → `## Role & Philosophy` → `## Core Capabilities` → `## Output Format` → `## Key Parameters`)
- GAP-REPORT.md content (placeholder OK for new expert)
- Bilingual depth (EN structure + CN prose per META-03)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.planning/research/v2-pipeline-design/02-NODE-SPECS.md §2.7` — full node spec
- `.planning/research/v2-pipeline-design/nodes.yaml` — machine-readable node metadata
- `.planning/research/v2-pipeline-design/skills-mapping.yaml:95-99` — new_ai_native mapping
- Phase 13-15 SKILL.md patterns: `continuity_auditor`, `compliance_gate`, `visual_executor`, `audio_pipeline` (all recently created/modified)
- `skills/movie-experts/creative_source/SKILL.md` — likely the upstream producer of visual_intent that prompt_injector consumes
- Existing references/ structures (LICENSE.md required per pattern)

### Established Patterns (cumulative from Phases 13-15)
- SKILL.md frontmatter schema: name + description + version + author + license + platforms + prerequisites + metadata.hermes.{tags, related_skills, expert_id, metrics}
- Bilingual: EN YAML structure + CN prose in body
- `related_skills` is bidirectional: prompt_injector lists creative_source/cinematographer/visual_executor/audio_pipeline; those experts should add prompt_injector back
- README.md inventory + corpus tree + DAG diagram updated
- `_shared/glossary.md` updated with new expert terms

### Integration Points
- `creative_source` likely produces the `visual_intent` that prompt_injector consumes
- `cinematographer` produces `composition_lock` and visual intent — prompt_injector consumes
- `visual_executor` consumes `model_prompts` from prompt_injector
- `audio_pipeline` may consume prompts for TTS/music gen
- All 4 consumers need `prompt_injector` added to their `related_skills` arrays (bidirectional edge sync)
- `skills/movie-experts/README.md` inventory needs new prompt_injector row (22 → 23 active experts if we count post-Phase-15, or final 21-expert topology post-Phase-17)
- `skills-mapping.yaml:99` `action_for_v21: "Add prompt_injector expert in v2.1+ skills milestone"` — this milestone v3.0 fulfills that forward-looking note

</code_context>

<specifics>
## Specific Ideas

- ROADMAP §16 success criterion #3: `metadata.hermes.related_skills: [creative_source, cinematographer, visual_executor, audio_pipeline]` — exactly these 4 per Phase 8 §2.7
- ROADMAP §16 success criterion #4: `metadata.hermes.metrics: [cross_call_consistency, prompt_token_efficiency]` — exactly these 2 per nodes.yaml
- ROADMAP §16 success criterion #5: 4 refs in `prompt_injector/references/` (prompt engineering patterns + cross-call consistency literature)
- ROADMAP §16 success criterion #6: README 21-expert inventory lists prompt_injector as NEW (Phase 16 entry)
- Node spec budget: ¥50/episode, 30s latency, stable_2026 maturity
- **No silent sign-off** — prompt_injector entry in skills-mapping.yaml already exists with `mapping_type: new_ai_native`; this phase just creates the actual skill directory

</specifics>

<deferred>
## Deferred Ideas

None — pure creation phase, scope tightly bounded by ROADMAP §16.

</deferred>
