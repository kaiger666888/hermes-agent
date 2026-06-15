# Provider-Agnostic RAG Invocation Pattern — Movie-Experts Suite v2

**Purpose:** Define the canonical contract for how every expert's SKILL.md invokes retrieval-augmented generation (RAG) without breaking portability across Hermes providers.

**Related:** CLAUDE.md "Skill File Conventions"; PROJECT.md "Provider-agnostic RAG invocation" decision; `_shared/known-external-models.yaml` (vendor token conventions).

**Last updated:** 2026-06-15 (Phase 0 skeleton)

---

## The hard rule

**NEVER hardcode a specific memory-plugin tool name (`fact_store`, `mem0_search`, `cosyvoice_api`, or any vendor-specific API surface) in a SKILL.md prompt body.**

Hermes runs against multiple providers. The user picks one at agent init time (`holographic` default, or `mem0` if `MEM0_API_KEY` is configured). Hard-coding `mem0_search` breaks for `holographic` users and vice versa.

Research SUMMARY (Finding #3): "`MemoryManager.add_provider()` rejects any second non-builtin provider. Skills CANNOT choose their provider — the user already picked one at agent init. **All skills must emit provider-agnostic RAG instructions**."

## The canonical pattern

Every SKILL.md that needs RAG retrieval MUST include a `## Knowledge Retrieval` block (or equivalent conditional phrasing in `## Workflow` step 1) following this template:

```markdown
## Knowledge Retrieval

Before generating output, retrieve context from the following reference topics:

- <topic-a> (e.g., "Save the Cat 15-beat structure adapted to 60-180s 短剧")
- <topic-b> (e.g., "hook taxonomy: 情感钩 / 悬念钩 / 冲突钩")
- <topic-c>

**If a memory/RAG tool is available in your current runtime** (e.g., `fact_store`, `mem0_search`, or a similar retrieval tool), query for these topics with `tags="expert:<expert_id>"` to scope results to this expert's domain.

**If no such tool is available**, fall back to the bundled `references/*.md` files listed in the `## References` table above. The bundled refs are authoritative; the memory plugin is an optimization for larger corpora.
```

## Why this pattern is load-bearing

1. **Graceful degradation:** If the memory plugin is absent, misconfigured, or circuit-broken (mem0 has a 5-fail → 120s pause breaker), the skill still works by reading bundled refs.
2. **Provider portability:** The same SKILL.md runs identically whether the user has `holographic`, `mem0`, or no memory plugin at all.
3. **Silent failure prevention:** Without explicit conditional phrasing, a skill that assumes `fact_store` exists will silently produce no-RAG output when the plugin is absent — the user never knows. The conditional phrasing surfaces a warning ("running in static-refs-only mode") in the model's reasoning.
4. **Eval validity:** The Phase 3 / Phase 6 LLM-as-judge harness needs deterministic control over whether RAG is active (for ablation runs). Provider-agnostic phrasing lets the harness toggle RAG by injecting / withholding the memory tool, without rewriting SKILL.md.

## Before / after example

### ❌ Anti-pattern (hardcoded tool name)

```markdown
## Workflow

1. **Retrieve context** — Call `mem0_search(query="save the cat beat sheet", tags="expert:screenplay")` to load the structural reference.
2. **Beat planning** — Generate scene-level beat sheet using retrieved context.
```

This breaks for `holographic` users (no `mem0_search` tool exists in their runtime). It also makes ablation eval impossible without rewriting the skill.

### ✅ Correct pattern (provider-agnostic conditional)

```markdown
## Workflow

1. **Knowledge Retrieval** — If a memory/RAG tool is available (e.g., `fact_store`, `mem0_search`, or similar), query for "save the cat beat sheet" and "短剧 hook taxonomy" with `tags="expert:screenplay"`. If no such tool is available, fall back to `references/save-the-cat-beat-sheet.md` and `references/hook-taxonomy.md` (see `## References` table).
2. **Beat Planning** — Generate scene-level beat sheet using retrieved context.
```

This works for any provider configuration and supports ablation eval.

## Placeholder token conventions

For vendor-specific model / API names that MUST appear in SKILL.md body (e.g., when describing what kind of model the expert expects), use provider-agnostic placeholders:

| Placeholder | Resolves to (Phase 3+ refs) | Used by |
|-------------|----------------------------|---------|
| `<video_gen_primary>` | veo3.1, kling-v3-4k (vertical 短剧 capable) | animator |
| `<video_gen_preview>` | ltx-2.3, pixverse-v6 (cheap preview tier) | animator |
| `<image_gen_primary>` | FLUX 2 Klein 9B (Hermes default via fal) | drawer |
| `<image_gen_fast>` | Z-Image Turbo (fastest tier) | drawer |
| `<audio_gen_primary>` | Stable Audio Open 1.0 (foley/SFX default) | foley |
| `<music_gen_primary>` | MusicGen-large (open-source music default) | composer |
| `<tts_primary>` | MiniMax / ElevenLabs (Hermes-native) or CosyVoice 3.0 (user-deployed) | voicer |

**Resolution:** Phase 3 / Phase 5 `references/*.md` files document the current model matrix with specific names, costs, and capabilities. Placeholders in SKILL.md body ensure the prompt doesn't break when the underlying model catalog changes (quarterly refresh).

## Memory plugin tag convention

When querying the memory plugin, scope results by expert using the `tags` field:

```
tags="expert:<expert_id>,domain:<topic>"
```

Example: `tags="expert:screenplay,domain:beat-sheet"`.

This is a soft filter (research SUMMARY Finding #4: "Per-skill namespace is a soft filter, not a DB feature. The only mechanism is the free-string `tags` field."). There is no native namespace isolation; tags are the only scoping primitive.

## Cross-references

- `_shared/known-external-models.yaml` — manual allowlist for external model names that appear in refs (Sora, Veo, Kling, etc.).
- `_shared/SKILL-LAYOUT.md` — standard skill directory layout (where `references/*.md` lives).
- `_shared/glossary.md` — EN↔CN term dictionary.
- CLAUDE.md "Skill File Conventions" — frontmatter schema.
- `.planning/research/SUMMARY.md` — source for the provider-agnostic hard rule and memory plugin internals.
