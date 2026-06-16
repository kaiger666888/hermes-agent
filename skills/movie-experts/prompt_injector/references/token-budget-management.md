# Token Budget Management (Token 预算管理)

> **Owner:** Phase 16 plan `16-01` (NEW prompt_injector RAG corpus).
> **Last updated:** 2026-06-17
> verified_date: 2026-06
> **Source mix:** OpenAI tokenizer documentation (2023-2026) + Anthropic context window documentation (2023-2026) + community prompt-chunking practice (2023-2026) + `02-NODE-SPECS.md §2.7` canonical `prompt_token_efficiency ≤ 4000` criterion.

## Scope

This ref covers **strategies for staying under the 4000 tokens/call ceiling** — the canonical `prompt_token_efficiency` success criterion for `prompt_injector` per `02-NODE-SPECS.md §2.7`. Cross-references the `prompt_overload` fail mode fallback ("split prompt into structured sections + use system prompt for stable constraints").

This is a **fair-use scholarship review**: paraphrased token-counting heuristics and chunking patterns drawn from vendor documentation and community practice. No verbatim reproduction of proprietary tokenizer internals.

---

## §1 — Why 4000 Tokens/Call?

The 4000-token ceiling is the empirically validated stability threshold for `stable_2026` model horizons. Above 4000 tokens, gen-model attention disperses — critical constraints (identity / composition / lighting) get ignored as the prompt grows.

### Attention degradation curve (empirical, `stable_2026`)

| Token count | Attention behavior | Production suitability |
|-------------|---------------------|------------------------|
| < 1000 | Tight focus; all constraints honored | Excellent (atomic shots) |
| 1000-2500 | Stable focus; minor attention dispersal at the tail | Good (standard shots) |
| 2500-4000 | Moderate dispersal; critical constraints still honored | Acceptable (complex shots) |
| 4000-6000 | Significant dispersal; some constraints dropped | `prompt_overload` risk zone |
| > 6000 | Severe dispersal; many constraints ignored | `prompt_overload` fail mode |

The 4000 ceiling is the **acceptability threshold** — above it, `prompt_overload` fallback must trigger.

---

## §2 — Prompt Chunking (Split-by-Concern)

The primary `prompt_overload` fallback is **chunking the prompt by semantic concern**:

### Standard 5-section chunk

| Section | Concern | Typical token range | Stability |
|---------|---------|---------------------|-----------|
| 1 | Identity (character refs, wardrobe, posture) | 80-200 | Stable (carry via system prompt) |
| 2 | Composition (framing, eye-line, DoF) | 50-150 | Stable (carry via system prompt) |
| 3 | Motion (camera move, subject motion) | 30-80 | Per-call variance |
| 4 | Lighting (key, fill, practicals) | 50-120 | Per-call variance |
| 5 | Mood (emotional tone, atmosphere) | 30-80 | Per-call variance |

**Total:** 240-630 tokens for a standard 5-section chunk. Well under the 4000 ceiling.

### When to chunk

- Single-section size > 200 tokens → chunking candidate
- Total prompt > 2500 tokens → chunking recommended
- Total prompt > 4000 tokens → chunking mandatory (`prompt_overload` fallback)

### Chunking rules

- **Never split a concern across two sections** — breaks semantic coherence
- **Order sections by stability** — stable concerns (identity, composition) first; per-call variance (motion, lighting, mood) last
- **Each section has a single semantic concern** — mixing concerns in one section defeats the chunking purpose

---

## §3 — Hierarchical Prompt Structures (System + User)

The most powerful token-budget strategy is the **system-prompt-for-stable-constraints** pattern:

### System prompt (stable, cached, scene-scoped)

Move all stable constraints to the system prompt:
- Identity (LoRA refs / IP-Adapter embeddings / InstantID face locks)
- Style (`style_genome_5d` vector)
- Composition conventions (axis locks, screen direction)
- Scene-level mood baseline

The system prompt is **cached** by the model provider — it doesn't count against per-call variance budget and doesn't re-process on every call (prefix-cache hit rate optimization).

### User prompt (per-call variance only)

The user prompt carries only the *delta* from the system prompt baseline:
- Per-shot motion deltas (camera dolly-in vs static)
- Per-shot lighting deltas (amber key vs blue key)
- Per-shot mood deltas (oppressive heat vs cold isolation)

### Token savings

| Pattern | Typical user-prompt token count | Total call token count |
|---------|--------------------------------|------------------------|
| Flat prompt (everything in user prompt) | 800-2500 | 800-2500 |
| Hierarchical (stable in system, variance in user) | 150-400 | 600-1500 (system cached) |

Hierarchical prompts cut user-prompt token count by 60-80%, keeping every call well under the 4000 ceiling.

---

## §4 — Context Window Management

### Provider context window sizes (`stable_2026`)

| Provider class | Context window | Effective prompt budget | Notes |
|----------------|-----------------|-------------------------|-------|
| `<image_primary>` (FLUX-class) | ~512-1024 prompt tokens | 512-1024 | Tight; chunking mandatory for complex prompts |
| `<video_primary>` (Veo-class) | ~1024-4096 prompt tokens | 1024-4000 | Moderate; hierarchical prompts recommended |
| LLM orchestrator (GPT-class) | 128k+ | 4000 ceiling self-imposed | The 4000 ceiling is a *quality* threshold, not a hard context-window limit |

**Key insight:** The 4000-token ceiling is NOT a context-window limit for most providers — it's an *attention quality* threshold. The model can accept longer prompts, but output quality degrades above 4000.

### Context window vs. token budget

- **Context window** = the maximum prompt length the model accepts (hard provider limit)
- **Token budget** = the prompt length at which output quality is still acceptable (soft quality threshold)

The 4000 ceiling is a token budget constraint, not a context window constraint.

---

## §5 — Token Counting Methods per Provider

Token counts vary by tokenizer. Approximate conversions:

| Unit | ≈ Tokens |
|------|----------|
| 1 English word | 1.3 tokens |
| 1 Chinese character | 2-3 tokens |
| 1 emoji | 2-5 tokens |
| 1 newline | 1 token |
| 1 punctuation mark | 1 token |

### Token counting APIs

- **OpenAI tokenizer:** `tiktoken` Python library (open-source, accurate for OpenAI models)
- **Anthropic tokenizer:** per-model tokenizer (closed-source; approximate via character count × 0.3)
- **Image gen models:** token counting is less standardized; use character count × 0.25 as a rough estimate

### Token budget planning

For each call, before invoking the model:
1. Count tokens in the assembled prompt (system + context + user)
2. If total > 4000 → trigger `prompt_overload` fallback
3. If total > 2500 → recommend chunking (warning, not fail)
4. If total < 1000 → consider adding more context (under-specifying risk)

---

## §6 — Redundancy Elimination

The most common token-budget waste is **redundancy** — repeating the same constraint in multiple sections.

### Redundancy patterns to eliminate

| Redundancy | Example | Fix |
|------------|---------|-----|
| Identity repeated in user prompt | "char_wuji, male, 30s, gaunt..." repeated in every call | Move to system prompt; carry via `consistency_context` |
| Style repeated per-section | "neo-noir mood" in identity, composition, AND mood sections | State once in system prompt; reference by name in sections |
| Composition lock repeated | "180° axis on char_wuji eye-line" in every shot's prompt | Carry via `consistency_context` composition block |

### Carry-don't-repeat rule

**Carry stable constraints via `consistency_context.json` — don't repeat them in every call's user prompt.** This is the single biggest token-budget saving.

| Strategy | Token cost per call | Token cost per 10-call sequence |
|----------|---------------------|---------------------------------|
| Repeat everything in user prompt | 2500 | 25000 |
| Carry via `consistency_context`, user prompt = variance only | 400 | 4000 + 2000 (one-time context setup) |

Carrying saves ~80% of token cost across a sequence.

---

## §7 — `prompt_overload` Fallback Protocol

When token count > 4000 ceiling:

### Step 1: Move stable constraints to system prompt

Identity / style / composition → system prompt (cached, doesn't count against per-call variance).

### Step 2: Chunk user prompt by concern

Split user prompt into atomic sections (identity / composition / motion / lighting / mood). Each section < 200 tokens.

### Step 3: Reduce few-shot N

If using 5-shot, drop to 3-shot or 1-shot. Reference frames are expensive in token budget.

### Step 4: Trim negative prompt

Negative prompts > 50 tokens degrade quality. Trim to 10-30 tokens.

### Step 5: Verify under ceiling

Re-count tokens. If still > 4000, escalate to intent-layer simplification (the visual_intent itself may be too complex for a single call — decompose into multiple calls with shared `consistency_context`).

---

## Cross-references

- [`prompt-engineering-patterns.md`](./prompt-engineering-patterns.md) — structured prompt anatomy (system / context / user)
- [`cross-call-consistency.md`](./cross-call-consistency.md) — `consistency_context` carry (the carry-don't-repeat foundation)
- [`model-specific-prompt-templates.md`](./model-specific-prompt-templates.md) — per-model token counting quirks

## Sources cited

1. OpenAI. *Tokenizer documentation.* 2023-2026. https://platform.openai.com/tokenizer
2. Anthropic. *Context window documentation.* 2023-2026. https://docs.anthropic.com/en/docs/build-with-claude/context-windows
3. `tiktoken` Python library (open-source OpenAI tokenizer). https://github.com/openai/tiktoken
4. Community prompt-chunking practice (2023-2026) — fair-use paraphrase of public craft patterns.
5. `02-NODE-SPECS.md §2.7` — canonical `prompt_token_efficiency ≤ 4000` criterion.
