# Stack Research

**Domain:** RAG-augmented movie-expert skill suite inside Hermes Agent (hybrid static refs + optional memory plugin)
**Researched:** 2026-06-15
**Confidence:** HIGH for memory-plugin internals (verified from source code at `plugins/memory/`, `agent/memory_provider.py`, `agent/memory_manager.py`); HIGH for existing Hermes image/video backend IDs (verified from `plugins/image_gen/`, `plugins/video_gen/`, `tools/image_generation_tool.py`); MEDIUM for 2026 external AI tool versions (verified via WebSearch against vendor/fal.ai docs, June 2026); MEDIUM for eval framework recommendations (verified via WebSearch against arXiv + official framework docs).

---

## 1. Hermes Memory Plugin — Concrete API Surface

This is the most important section for skill authors. Verified by direct read of source code on 2026-06-15.

### 1.1 Architecture (single-external-provider limit)

Hermes enforces a **hard single-external-provider limit**. `MemoryManager.add_provider()` (in `agent/memory_manager.py:258-302`) rejects any second non-builtin provider with a logged warning. Built-in provider (name `"builtin"`) is always accepted; external plugins (holographic, mem0, honcho, hindsight, supermemory, retaindb, byterover, openviking) compete for the single external slot. Provider selection happens at agent init via `memory.provider` in `cli-config.yaml`.

**Implication for movie-expert skills:** A skill CANNOT choose its provider. The user has already picked one when they configured Hermes. Skills must emit prompt-level RAG instructions that work against ANY of the registered memory provider's tools — they cannot hard-code `mem0_search` if the user has `holographic` selected.

### 1.2 Default Provider: `holographic` (local SQLite + FTS5 + HRR)

This is the most likely provider our skills will encounter because:
- `is_available()` returns `True` unconditionally (SQLite is always available).
- Requires zero config and no API key.
- Activated simply by `hermes config set memory.provider holographic`.

**Tools exposed (verified in `plugins/memory/holographic/__init__.py:39-90`):**

| Tool | Description | Required For |
|------|-------------|--------------|
| `fact_store` | 9 actions: `add`, `search`, `probe`, `related`, `reason`, `contradict`, `update`, `remove`, `list` | All RAG-style skill queries |
| `fact_feedback` | `helpful` / `unhelpful` rating on a `fact_id` | Train trust scores after a fact is used |

**`fact_store` parameter schema (from `__init__.py:54-73`):**

```python
{
  "action": enum["add","search","probe","related","reason","contradict","update","remove","list"],  # required
  "content": str,        # required for "add"
  "query":   str,        # required for "search"
  "entity":  str,        # required for "probe" / "related"
  "entities": [str],     # required for "reason"
  "fact_id": int,        # required for "update" / "remove"
  "category": enum["user_pref","project","tool","general"],  # optional
  "tags":     str,       # comma-separated, optional
  "trust_delta": float,  # optional, for "update"
  "min_trust":  float,   # default 0.3
  "limit":     int,      # default 10
}
```

**Retrieval pipeline (verified in `plugins/memory/holographic/retrieval.py`):**
- Stage 1: FTS5 candidates (`limit * 3` from SQLite full-text search)
- Stage 2: Jaccard token overlap rerank
- Stage 3: HRR (Holographic Reduced Representations) similarity if NumPy available; otherwise weights shift to FTS=0.6 / Jaccard=0.4 / HRR=0.0
- Stage 4: Trust-weighted scoring: `final = relevance * trust_score`
- Stage 5 (optional): temporal decay if `temporal_decay_half_life > 0`

**Schema constraints (`plugins/memory/holographic/store.py:16-76`):**
- `facts.content` is `TEXT NOT NULL UNIQUE` — duplicate content silently returns the existing fact_id.
- `facts.category` is a free string with a soft enum hint `["user_pref","project","tool","general"]` in the tool schema. Custom categories like `movie:cinematographer` WILL be accepted (the SQLite column has no CHECK constraint), but the tool schema's enum will reject them at the agent tool-call layer. **Workaround:** use one of the four fixed categories + `tags` for expert-specific filtering.
- `tags` is a comma-separated string, indexed via FTS5.
- Entities are auto-extracted from content via regex (capitalized phrases, quoted phrases, AKA patterns). Skills cannot inject entities explicitly.

**Per-skill namespace support:** NO direct namespace. The closest mechanism is `category` (4-value enum) + `tags` (free string). Skills should encode their expert_id into tags (e.g. `tags="expert:cinematographer,domain:camera-language"`) and then `fact_store(action="search", query="180度规则", category="tool")` returns only facts whose tags contain the expert prefix. This is a soft filter at the skill prompt level, not enforced by the DB.

**Limitations for skill RAG use:**
1. No built-in skill-scoped namespace — skills compete for the same `facts` table.
2. FTS5 tokenization is language-agnostic at the SQLite level but Chinese/CJK tokenization is poor without a custom tokenizer. Skills writing Chinese refs should ALSO write an English index field.
3. No batch ingest API — refs must be `add`-ed one fact at a time (the auto-extract hook at session end runs only when `auto_extract=true`).
4. No embedding model — HRR is a fixed random-projection binding scheme (not learned). Semantic recall on paraphrases is weaker than true embeddings.
5. The `category` enum is fixed at 4 values in the tool schema — adding `"expert:screenplay"` is NOT possible without editing the plugin (which is out of scope per PROJECT.md).

### 1.3 Optional Provider: `mem0` (server-side semantic search)

Activated via `mem0.json` or `MEM0_API_KEY` env var. Uses the Mem0 Platform API (`pip install mem0ai`). Circuit breaker: 5 consecutive failures → 120s pause (`plugins/memory/mem0/__init__.py:_BREAKER_THRESHOLD`).

**Tools exposed:**

| Tool | Parameters | Notes |
|------|------------|-------|
| `mem0_profile` | none | All stored memories, no reranking |
| `mem0_search`  | `query` (required), `rerank` (bool, default false), `top_k` (int, default 10, max 50) | Semantic similarity search |
| `mem0_conclude`| `conclusion` (required) | Verbatim store (no LLM extraction) |

**Per-skill namespace:** Partial. Mem0 has `user_id` and `agent_id` scopes. The skill can prefix queries (e.g. `query="expert:cinematographer axis rule"`) but there is no true namespace isolation — all skills share one Mem0 user_id by default.

### 1.4 Other providers (less relevant for movie-experts)

- `honcho` — dialectic AI semantic memory, remote API, `HONCHO_API_KEY`.
- `supermemory` — remote, similar API surface to mem0.
- `retaindb` — remote, `RETAINDB_API_KEY`.
- `openviking` — remote, `OPENVIKING_ENDPOINT`.
- `byterover` / `hindsight` — local-experimental.

**Recommendation for skills:** Skills should emit provider-agnostic RAG instructions in their system prompt, listing the available tools dynamically. Do NOT hard-code `fact_store` or `mem0_search` — let the agent's tool catalog drive selection.

### 1.5 How a skill triggers RAG (concrete recipe)

Since skills are pure markdown, RAG is invoked through **prompt-level instructions**, not code. The recommended pattern (derived from how `skills/creative/pretext/`, `skills/creative/manim-video/`, `skills/creative/comfyui/` work today) is:

```markdown
## Knowledge Retrieval

Before answering, query memory for relevant industry knowledge:

1. **Probe your domain** — call `fact_store(action="search", query="<topic>")` with keywords from the user's task.
2. **Filter by your tags** — only use facts whose `tags` contain `expert:<your_expert_id>`.
3. **Cite sources** — when using a fact, note its `fact_id` and tags in your output.
4. **Add new facts** — if you discover durable industry knowledge (camera rules, hook formulas, compliance rules), call `fact_store(action="add", content="...", category="tool", tags="expert:<your_expert_id>,source:<origin>")`.
5. **Rate after use** — call `fact_feedback(action="helpful"|"unhelpful", fact_id=<id>)` after using a fact to train trust scores.

If no memory provider is configured, fall back to your bundled `references/*.md` corpus.
```

This is the v1 pattern. v2 could add a small Python helper that auto-tags facts on insert, but that's out of scope.

---

## 2. Static Reference Corpus — Best Practices (verified from existing skills)

### 2.1 Directory layout pattern

Verified against 12 existing `skills/creative/*/references/` directories. The dominant pattern:

```
skills/<category>/<skill>/
  SKILL.md                       # Main skill (formerly included all knowledge)
  references/                    # NEW: extracted knowledge corpus
    README.md                    # Index/TOC of all refs (optional but recommended)
    <topic-1>.md                 # Atomic, file-per-domain
    <topic-2>.md
    ...
```

**File naming convention (verified from `manim-video`, `p5js`, `comfyui`):**
- `kebab-case` filenames: `animation-design-thinking.md`, `color-systems.md`, `core-api.md`, `decorations.md`, `workflow-format.md`, `template-integrity.md`, `troubleshooting.md`, `visual-effects.md`.
- One file per atomic knowledge domain. No mega-files.
- Always include `troubleshooting.md` — this is where "what NOT to do" goes.

### 2.2 Section structure pattern

Verified from `manim-video/references/animations.md`, `p5js/references/color-systems.md`, `comfyui/references/workflow-format.md`. Standard structure:

```markdown
# <Topic Name>

## Core Concept
<2-4 sentence explanation — what this is and why it matters>

## <Subtopic 1>

### <Pattern>
```<lang>
<concrete code example>
```

**Critical:** <callout on what's easy to get wrong>

## <Subtopic 2>
...

## Anti-Patterns
<what NOT to do, with rationale>

## Source
- [Source Name](url) — license / fair-use status
```

**Key conventions:**
- Code blocks for any API call, JSON shape, or workflow. Skills should be able to copy-paste.
- **"Critical" callouts** for gotchas (`**Critical:** After Transform(A, B), variable A references the on-screen mobject. Variable B is NOT on screen.`).
- Tables for parameter catalogs (`| Node Class | Key Fields |`).
- Each ref is self-contained — no dependency on another ref being loaded.

### 2.3 Citation / provenance format

Existing skills are inconsistent on this. Best pattern seen (from `comfyui/references/template-integrity.md`):

```markdown
> **Authored by [@purzbeats](https://github.com/purzbeats)** — adapted from
> [purzbeats/hermes-agent-comfyui-helper](https://github.com/purzbeats/hermes-agent-comfyui-helper).
> Use this reference when ...
```

**Recommended citation format for movie-experts refs** (we own this since there's no existing precedent):

```markdown
---
source:
  type: book | paper | platform_guide | sample | practitioner_notes
  title: "<title>"
  author: "<author or org>"
  year: <year>
  url: "<url if online>"
  license: "public_domain | cc_by_4_0 | fair_use_excerpt | proprietary_quoted"
  excerpt_pages: "<e.g. pp. 47-52, fair use>"  # if applicable
---

# <Ref title>

<body>

## Provenance
- Source: [<title>](<url>)
- License: <license>
- Used: <quote/paraphrase/adapted>
```

This satisfies PROJECT.md's constraint: "All refs must be tagged with source and copyright status."

### 2.4 Cross-reference / indexing pattern

Recommended (not yet seen in existing skills — we're introducing this):
- A per-skill `references/README.md` with a TOC: topic → file → when to use.
- In-skill SKILL.md `## Knowledge Retrieval` block listing which refs to consult for which user intent.
- Optional: top-level `skills/movie-experts/CORPUS.md` mapping all 18 experts → ref topics → cross-cutting concepts (e.g. "axis line" appears in cinematographer, editor, continuity).

---

## 3. AI Generation Tool Stack (2026-06) — Verify Before Asserting in Skill Refs

**Critical finding from codebase audit:** The existing 14 movie-expert SKILL.md files reference stale model versions that DON'T MATCH the actual Hermes backend catalog. Specifically:
- `drawer/SKILL.md` says "FLUX model parameter optimization" with `sampler=euler_a`, `steps=20-30`, `cfg=3.5-5.0` — these are **FLUX 1.x** parameters. Hermes actually ships FLUX 2 (Klein 9B and Pro) via FAL.
- `animator/SKILL.md` references `wan22_video` and `wan22_video_turbo` — these IDs do **not** exist anywhere in `plugins/video_gen/` or `tools/`. Wan2.2 IS real (verified on fal.ai), but the Hermes backend does not currently route to it.
- `voicer/SKILL.md` references `CosyVoice-300M (preview)` and `CosyVoice-300M-SFT` — these are v1 model IDs from mid-2024. CosyVoice 2.0 (Dec 2024) and **CosyVoice 3.0** (verified via search 2026-06) are the current versions.
- `composer/SKILL.md` references `MusicGen-large (primary, 32kHz stereo)` — this is the original 2023 model. Stable Audio Open 1.0 is now the open-source default for foley/SFX; MusicGen remains the music default but is no longer actively developed.
- `foley/SKILL.md` references `AudioLDM-2` — research-era model. **Stable Audio Open 1.0** + **Stable-Foley** (built on top of it, arXiv:2412.15023) are now the state of the art for video-synced foley.

### 3.1 Image Generation — verified from `plugins/image_gen/` and `tools/image_generation_tool.py`

**Hermes backend: FAL.ai** (default, `image_gen.provider: fal`). 18-model catalog. Top picks verified against `tools/image_generation_tool.py:98-372`:

| Model ID | Display | Strengths | Use Case |
|----------|---------|-----------|----------|
| `fal-ai/flux-2/klein/9b` | FLUX 2 Klein 9B | DEFAULT (`DEFAULT_MODEL` at line 372). Fast, capable. | Primary for cinematic stills, character reference shots |
| `fal-ai/flux-2-pro` | FLUX 2 Pro | Slower, higher fidelity. Requires `image_format=png`. | Final production frames, hero shots |
| `fal-ai/z-image/turbo` | Z-Image Turbo | Fastest. | Quick iteration, preview |
| `fal-ai/nano-banana-pro` | Nano Banana Pro (Gemini) | High aesthetic quality. | Alternative cinematic look |
| `fal-ai/gpt-image-2` | GPT Image 2 | Strong text-in-image. | Poster / title card generation (relevant for EXPERT-COMPLI) |
| `fal-ai/recraft/v4/pro/text-to-image` | Recraft v4 Pro | Vector-friendly, strong UI/design aesthetic. | Less relevant for film |

**Also available (not FAL):**
- OpenAI `gpt-image-2` direct — `plugins/image_gen/openai/`, 3 tiers: `gpt-image-2-low` (~15s), `gpt-image-2-medium` (~40s default), `gpt-image-2-high` (~2min). Same model, different latency.
- xAI `grok-imagine` — `plugins/image_gen/xai/`, `XAI_API_KEY`.
- Krea 2 Large + Medium — `plugins/image_gen/krea/`, `KREA_API_KEY`.

**Recommendation for drawer skill:** Rewrite `drawer/SKILL.md` to default to **`fal-ai/flux-2/klein/9b`** (the actual Hermes default), with `flux-2-pro` as the production tier. Remove the `euler_a` / `dpmpp_2m` sampler language — these are FLUX 1 / SDXL concepts; FLUX 2 exposes a different parameter surface (verify against FAL's flux-2-klein schema before writing final SKILL.md).

**What NOT to reference in skills (anymore):**
- `FLUX 1 dev`, `FLUX 1 schnell` — superseded by FLUX 2.
- SDXL checkpoints, A1111 sampler names — Hermes has no ComfyUI/A1111 image backend.
- DALL-E 3 — superseded by gpt-image-2.

### 3.2 Video Generation — verified from `plugins/video_gen/fal/__init__.py`

**Hermes backend: FAL.ai** (only video backend, `video_gen.provider: fal`). Family catalog (`FAL_FAMILIES` at line 67):

| Family ID | Display | Tier | Endpoints | Strengths |
|-----------|---------|------|-----------|-----------|
| `ltx-2.3` | LTX 2.3 (22B) | cheap | `fal-ai/ltx-2.3-22b/{text,image}-to-video` | Native audio, affordable |
| `pixverse-v6` | Pixverse v6 | cheap | `fal-ai/pixverse/v6/{text,image}-to-video` | 1-15s, negative prompts |
| `veo3.1` | Veo 3.1 | premium | `fal-ai/veo3.1` + `/image-to-video` | Google DeepMind, native audio, 4-8s, 16:9/9:16, 720p-4K |
| `seedance-2.0` | Seedance 2.0 | premium | `bytedance/seedance-2.0/{text,image}-to-video` | ByteDance, lip-sync, 4-15s |
| `kling-v3-4k` | Kling v3 4K | premium | `fal-ai/kling-video/v3/4k/{text,image}-to-video` | 4K, 3-15s, CN+EN audio |
| `happy-horse` | Happy Horse 1.0 | premium | `alibaba/happy-horse/{text,image}-to-video` | Alibaba, 60-120s |

**Wan2.2 (referenced by current animator skill) IS NOT in the Hermes catalog.** Wan2.2 IS real on fal.ai (verified: `fal-ai/wan/v2.2-5b/text-to-video` and `fal-ai/wan/v2.2-a14b/text-to-video`), but Hermes' video plugin does not include it in `FAL_FAMILIES`. **Latest is Wan 2.7** (text-to-video, image-to-video with first-and-last-frame control, reference-to-video for character consistency, instruction-based editing).

**Recommendation for animator skill:** Either (a) rewrite to use `veo3.1` or `kling-v3-4k` as the primary family (both support 16:9 and 9:16 — critical for vertical 短剧), or (b) document Wan2.2 as "external model, user must add a custom fal model override" and have the skill instruct the agent to call `video_generate(model="fal-ai/wan/v2.2-a14b/text-to-video", ...)` directly. Option (a) is simpler and uses what Hermes already ships.

**Also available:**
- xAI `grok-imagine` text-to-video / image-to-video / edit / extend — `plugins/video_gen/xai/`, `XAI_API_KEY`.

### 3.3 TTS / Speech Synthesis — verified from INTEGRATIONS.md and `voicer/SKILL.md`

Hermes ships 10+ TTS backends. CosyVoice is NOT one of them — `voicer/SKILL.md` references a model that Hermes does not actually invoke. Verified against the TTS registry list in INTEGRATIONS.md.

**For Chinese 短剧 voice work, the actually-available best options are:**

| Backend | Plugin | Strengths for CN drama |
|---------|--------|------------------------|
| **MiniMax TTS** | built-in | `MINIMAX_API_KEY`, strong CN voice quality, emotion control |
| **ElevenLabs** | `tts.elevenlabs`, `elevenlabs==1.59.0` | Voice cloning (character consistency), `ELEVENLABS_API_KEY` |
| **Mistral Voxtral** | `tts.mistral`, `mistralai==2.4.8` | Multilingual |
| **Gemini TTS** | built-in | Google, decent CN |
| **OpenAI TTS** | built-in | Weak CN — skip for Chinese 短剧 |
| **Edge TTS** | `tts.edge`, `edge-tts==7.2.7` | Free, default, decent CN |
| **NeuTTS (local)** | `tools/neutts_synth.py` | Local CN TTS |
| **KittenTTS (local)** | built-in | 25MB, fast |

**CosyVoice recommendation:** If the project wants CosyVoice (which is genuinely SOTA for CN emotional TTS — verified CosyVoice 3.0 is the latest, supporting 9 languages), it would need either (a) local deployment outside Hermes + reference docs in `voicer/references/cosyvoice-deployment.md`, or (b) a wait for Hermes to add a CosyVoice plugin. Option (a) fits within the "pure skill + refs" deliverable constraint — the SKILL.md describes the CosyVoice API surface and the user deploys it themselves.

### 3.4 Music Generation

| Tool | Status (2026-06) | Use Case |
|------|------------------|----------|
| **MusicGen-large / MusicGen-small** (Meta AudioCraft) | Mature, stable, but **not actively developed**. Last significant update 2024. 32kHz mono/stereo, 30s chunks. | Composer skill default. Open weights, runs locally. |
| **Stable Audio 2.5** (commercial) | Active, integrated in ComfyUI, up to 3-min tracks in <2s. | Commercial alternative, subscription. |
| **Stable Audio Open 1.0** | Open-source, up to 47s stereo at 44.1kHz. **Better than MusicGen for SFX/foley/ambient.** | Foley/ambient stems. |
| **AudioGen** (Meta AudioCraft) | Co-developed with MusicGen, focused on SFX. | Sound effects generation. |

**Recommendation for composer skill:** Keep MusicGen-large as the open-source default (no API cost, fits "no new infrastructure" constraint), but add a note: "MusicGen development is mature/stable; for higher-fidelity commercial music consider Stable Audio 2.5 (requires subscription)."

### 3.5 Foley / SFX

| Tool | Status (2026-06) | Use Case |
|------|------------------|----------|
| **Stable Audio Open 1.0** | Open-source, 47s @ 44.1kHz. Foley, ambient, SFX, drum beats. | Default for foley skill |
| **Stable-Foley** (arXiv:2412.15023) | Built on Stable Audio Open, video-synchronized SFX. Research-grade. | Video-synced foley (research only — not production API) |
| **Foley Control** (Stability AI, V-JEPA2 + Stable Audio Open) | Video-conditioned foley via cross-attention. Research. | Same |
| **AudioLDM-2** | Research-era, referenced by current `foley/SKILL.md`. Superseded by Stable Audio Open. | **REMOVE from skill — outdated.** |
| **AudioGen** (Meta) | Mature, SFX-focused sibling of MusicGen. | Viable alternative to Stable Audio Open. |

**Recommendation for foley skill:** Replace AudioLDM-2 with Stable Audio Open 1.0 as primary; AudioGen as fallback. Document Stable-Foley as a research-grade option for video-synced output.

---

## 4. LLM-as-Judge Eval Framework — For Skill Before/After Comparison

Verified via WebSearch against arXiv, NeurIPS, official framework docs.

### 4.1 Standard approaches (the "right" pattern for our use case)

We need to evaluate: **"Is the skill output better after RAG enhancement than before?"** This is a **pairwise comparison** problem, not a single-answer grading problem. The relevant literature is:

**MT-Bench (Zheng et al., NeurIPS 2023)** — foundational paper on LLM-as-judge. Two mitigation techniques for judge bias:
1. **Chain-of-thought judge** — judge writes reasoning before score.
2. **Reference-guided judge** — provide a gold reference.
3. **Pairwise A/B with position swap** — present A and B in both orders; if the judge flips its preference, mark as a tie.

**Position bias is REAL and LARGE.** Verified finding: median LLM judge flips preference in **45% of decisive cases** when answer order is swapped (source: position_bias benchmark, lechmazur/position_bias on GitHub). This means a naive "always present enhanced-version-first" eval is statistically invalid.

### 4.2 Framework options

| Framework | Strengths | Weaknesses | Fit for our project |
|-----------|-----------|------------|---------------------|
| **Ragas** | Purpose-built for RAG. Core metrics: `faithfulness` (answer grounded in retrieved context), `answer_relevancy`, `context_precision`, `context_recall`. Official docs at docs.ragas.io. | Focused on retrieval pipeline metrics, NOT on "is skill output better" pairwise comparison. No built-in position-swap harness. | MEDIUM — useful for measuring RAG quality (do refs actually get retrieved + cited correctly), but NOT the right tool for double-blind skill comparison. |
| **DeepEval** | Pytest-native syntax (`@pytest.mark`). 50+ metrics including faithfulness, hallucination, answer relevance. CI/CD integration. Open-source. | Heavier than a hand-rolled harness. Some metrics overlap with Ragas. | HIGH — fits naturally if we want each skill's eval as a pytest test. But our constraint is "no new Python packages" (PROJECT.md Out of Scope). Verify whether DeepEval can be a dev-only dependency. |
| **Hand-rolled harness** | Total control. Implements MT-Bench position-swap pattern directly. ~200 lines of Python. | Must implement bias mitigations ourselves. | HIGHEST FIT — matches the "lightweight LLM-as-judge double-blind harness" requirement in PROJECT.md. Lives in `eval/` next to each skill. |
| **prompteams** | Arena-style comparison. | Niche, smaller community. | LOW |
| **Chatbot Arena methodology** | Large-scale pairwise. | Requires many human votes — overkill for our small eval. | LOW |

### 4.3 Recommended eval harness pattern (concrete)

For each skill, ship:
1. `eval/prompts/` — 5-10 benchmark tasks (e.g. for cinematographer: "design a 180-degree rule sequence for a 2-character dialogue", "compose an over-the-shoulder framing for emotional reveal").
2. `eval/run.py` — runs each prompt twice: (a) WITHOUT RAG (baseline = skill prompt alone), (b) WITH RAG (skill prompt + retrieved refs). Calls a judge LLM (default: GLM-4 or Claude 3.5 Sonnet) with **both orderings** (A/B and B/A).
3. `eval/judge_prompt.md` — MT-Bench-style rubric: "You are judging two outputs from a movie cinematographer expert. Score on: technical accuracy (0-10), industry specificity (0-10), actionability (0-10). Output JSON."
4. `eval/report.md` — auto-generated. Per-prompt scores for both runs, position-swap consistency check, aggregate win-rate.

**Critical implementation rules (verified from MT-Bench paper):**
- ALWAYS run both A/B and B/A orderings. If the judge disagrees on ordering, mark as tie.
- Use **chain-of-thought judge**: judge writes reasoning before final score. Prevents anchor-on-first-impression bias.
- Use **multiple judge models** if budget allows — agreement across GPT-4o + Claude 3.5 + GLM-4 increases confidence.
- Pin judge temperature to 0 (or 0.1 max) for reproducibility.
- Report inter-run variance, not just mean — a 0.5-point mean improvement is meaningless if run-to-run variance is 1.5.

**No new Python package required.** The harness uses only: `openai` SDK (already in Hermes), `pyyaml` (already in Hermes), `jinja2` (already in Hermes for prompt templating). This honors the PROJECT.md "no new Python packages" constraint.

---

## 5. Vector DB Choice (v2 only — NOT for v1)

**v1 does not add a standalone vector DB.** PROJECT.md explicitly excludes this from scope. The following is for v2 planning only.

Verified via WebSearch against 2026 comparison guides (Firecrawl, Encore, iternal.ai, aiml.qa).

| Option | Strengths | Weaknesses | v2 Verdict |
|--------|-----------|------------|------------|
| **sqlite-vec** | SQLite extension. Zero new infrastructure. Hermes already ships SQLite + FTS5. Same DB file pattern as `memory_store.db`. | Limited scalability (~100K vectors practical). No GPU acceleration. | **RECOMMENDED for v2.** Aligns with Hermes' SQLite-first architecture. Replaces the HRR layer in holographic with true learned embeddings, keeping the same file-based deployment story. |
| **LanceDB** | Embedded (file-based), multimodal (vectors + images + text), columnar. Scales to millions. Smaller community. | New dependency. Different file format from SQLite. | Strong alternative if we need multimodal (storing image embeddings alongside text). |
| **Chroma** | Best DX for local dev. Python-native, easy. | In-memory by default; persistence is a separate mode. Memory-hungry at scale. | Use only for prototyping. |
| **Qdrant** | Best self-hosted option, Rust-fast, good free tier. Built-in filtering. | Requires running a separate service (Docker). Adds operational burden. | Overkill for a skill suite. |
| **pgvector** | If Hermes ever moves session storage to Postgres, this is free. | Hermes uses SQLite for sessions. Adding Postgres just for vectors is a non-starter. | NO. |
| **Pinecone / Weaviate Cloud** | Managed, zero ops. | Vendor lock-in, cost, latency, privacy (sending refs to a third party). | NO. |

**v2 recommendation:** sqlite-vec as the primary, with LanceDB as the fallback if multimodal (image+text) retrieval becomes a requirement. This stays within the "no new infrastructure" philosophy — sqlite-vec is just a loadable SQLite extension.

---

## Recommended Stack Summary (One-Pager)

| Layer | v1 Choice | v2 (deferred) |
|-------|-----------|---------------|
| Static knowledge corpus | Markdown refs in `skills/movie-experts/<expert>/references/*.md` | Same |
| RAG query mechanism (default) | `fact_store(action="search")` via holographic plugin | Same |
| RAG query mechanism (optional) | `mem0_search` if user has Mem0 configured | Same |
| Per-skill namespace | Soft filter via `tags="expert:<expert_id>"` | Add real namespace to plugin |
| Image gen | `fal-ai/flux-2/klein/9b` (default) / `fal-ai/flux-2-pro` (production) | Same |
| Video gen | `veo3.1` or `kling-v3-4k` (both support 9:16 vertical for 短剧) | Add Wan2.7 if plugin extended |
| TTS (CN 短剧) | MiniMax or ElevenLabs (via Hermes backends) | Same + optional CosyVoice local |
| Music | MusicGen-large (open-source, no new dep) | Stable Audio 2.5 (commercial alt) |
| Foley / SFX | Stable Audio Open 1.0 (replaces AudioLDM-2) | Stable-Foley for video-sync |
| Eval harness | Hand-rolled MT-Bench-style position-swap harness, no new deps | + DeepEval for pytest-native CI |
| Vector DB | None (use holographic HRR / FTS5) | sqlite-vec |
| LLM providers | GLM-5.2 (project default) / Claude 3.5 Sonnet / GPT-4o | Same |

---

## What NOT to Use (with rationale)

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| FLUX 1.x (dev/schnell) sampler parameters (`euler_a`, `dpmpp_2m`, `cfg=3.5-5.0`) | Superseded by FLUX 2 in Hermes' actual backend; sampler names don't transfer | FLUX 2 API surface (verify against `fal-ai/flux-2/klein/9b` schema) |
| `wan22_video` / `wan22_video_turbo` model IDs | Do NOT exist in Hermes' `FAL_FAMILIES` catalog — calls would fail | `veo3.1` or `kling-v3-4k` (in-catalog) OR document Wan2.2 as user-supplied custom model |
| `CosyVoice-300M (preview)` / `CosyVoice-300M-SFT` | v1 model IDs, 2024. Latest is CosyVoice 3.0 | Either document CosyVoice 3.0 as user-deployed local service, OR use MiniMax / ElevenLabs from Hermes' built-in TTS registry |
| `AudioLDM-2` | Research-era, superseded by Stable Audio Open for foley | Stable Audio Open 1.0 |
| DALL-E 3 | Superseded by gpt-image-2 in OpenAI's catalog | `gpt-image-2` (low/medium/high tiers) |
| Chroma / Qdrant / Pinecone as v1 vector DB | Out of scope per PROJECT.md; Hermes memory plugin suffices | `holographic` (default) or `mem0` (optional) |
| Ragas as the primary eval harness | Built for retrieval-pipeline metrics, not pairwise skill comparison | Hand-rolled position-swap harness; Ragas optional for retrieval-quality sub-metric |
| Hard-coding `fact_store` tool name in skills | User might have `mem0` or other provider configured | Provider-agnostic prompt instructions ("query memory for ...") |
| Single-run LLM-as-judge (no position swap) | Position bias causes ~45% preference flips — statistically invalid | ALWAYS run A/B and B/A orderings, mark disagreement as tie |

---

## Sources

**Hermes codebase (HIGH confidence, direct source read):**
- `/data/workspace/hermes-agent/agent/memory_provider.py` — MemoryProvider ABC, lifecycle hooks
- `/data/workspace/hermes-agent/agent/memory_manager.py` — single-external-provider limit, prefetch/sync orchestration
- `/data/workspace/hermes-agent/plugins/memory/holographic/__init__.py` — fact_store / fact_feedback tool schemas
- `/data/workspace/hermes-agent/plugins/memory/holographic/store.py` — SQLite schema, FTS5 triggers, HRR vector storage
- `/data/workspace/hermes-agent/plugins/memory/holographic/retrieval.py` — hybrid FTS5 + Jaccard + HRR retrieval pipeline
- `/data/workspace/hermes-agent/plugins/memory/mem0/__init__.py` — Mem0 client, circuit breaker, profile/search/conclude tools
- `/data/workspace/hermes-agent/plugins/memory/holographic/README.md`, `/data/workspace/hermes-agent/plugins/memory/mem0/README.md` — config keys, setup
- `/data/workspace/hermes-agent/plugins/video_gen/fal/__init__.py` — FAL_FAMILIES catalog (ltx-2.3, pixverse-v6, veo3.1, seedance-2.0, kling-v3-4k, happy-horse)
- `/data/workspace/hermes-agent/plugins/image_gen/fal/plugin.yaml`, `/data/workspace/hermes-agent/tools/image_generation_tool.py` — FAL image model catalog (FLUX 2 Klein, FLUX 2 Pro, Z-Image, Nano Banana, gpt-image-2, Recraft v4)
- `/data/workspace/hermes-agent/plugins/image_gen/openai/__init__.py` — gpt-image-2 low/medium/high tiers
- `/data/workspace/hermes-agent/skills/movie-experts/{screenplay,drawer,animator,voicer,composer,foley}/SKILL.md` — stale model references to update
- `/data/workspace/hermes-agent/skills/creative/{manim-video,p5js,comfyui}/references/*.md` — reference corpus structure pattern
- `/data/workspace/hermes-agent/.planning/codebase/{STACK.md,INTEGRATIONS.md}` — Hermes stack baseline

**External docs (MEDIUM confidence, WebSearch-verified June 2026):**
- [CosyVoice GitHub (FunAudioLLM)](https://github.com/FunAudioLLM/CosyVoice) — CosyVoice 3.0 confirmed as latest, 9 languages
- [CosyVoice 2 arXiv paper](https://arxiv.org/html/2412.10117v2) — v2 details
- [Wan 2.2 on fal.ai](https://fal.ai/models/fal-ai/wan/v2.2-5b/text-to-video) + [Wan 2.7](https://fal.ai/wan-2.7) — Wan2.2 exists on FAL but is NOT in Hermes catalog; Wan 2.7 is current latest
- [Stable Audio Open (Stability AI)](https://stability.ai/news-updates/introducing-stable-audio-open) + [HF model](https://huggingface.co/stabilityai/stable-audio-open-1.0) — 47s @ 44.1kHz, foley/SFX/ambient
- [Stable-Foley (arXiv:2412.15023)](https://arxiv.org/html/2412.15023v1) — video-synced foley on Stable Audio Open base
- [Foley Control (Stability AI research)](https://stability-ai.github.io/foleycontrol.github.io/) — V-JEPA2 + Stable Audio Open
- [AudioCraft / MusicGen (Meta)](https://github.com/facebookresearch/audiocraft) — stable but not actively developed
- [MT-Bench paper (arXiv:2306.05685)](https://arxiv.org/abs/2306.05685) + [NeurIPS 2023](https://neurips.cc/virtual/2023/poster/73434) — LLM-as-judge + position-bias mitigation
- [Position bias benchmark (lechmazur)](https://github.com/lechmazur/position_bias) — 45% preference flip rate median
- [Systematic Study of Position Bias in LLM-as-a-Judge (arXiv:2406.07791)](https://arxiv.org/html/2406.07791v9)
- [Ragas docs](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/) — faithfulness / answer relevancy / context metrics
- [DeepEval official](https://deepeval.com/) + [GitHub](https://github.com/confident-ai/deepeval) — pytest-native, 50+ metrics
- [Best Vector Databases 2026 (Firecrawl)](https://www.firecrawl.dev/blog/best-vector-databases) + [Encore](https://encore.dev/articles/best-vector-databases) — Chroma/Qdrant/LanceDB/sqlite-vec comparison

---
*Stack research for: RAG-augmented movie-expert skill suite*
*Researched: 2026-06-15*
