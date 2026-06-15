# Phase 3: Top-4 Existing Experts RAG - Context

**Gathered:** 2026-06-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 deep-refactors the four highest-leverage existing experts (screenplay, editor, colorist, style_genome) with curated RAG refs, revised quality thresholds, refined metrics, and statistically defensible ablation comparison vs Phase 0 baseline. This phase is the GO/NO-GO gate for Phase 5: if RAG uplift is statistically insignificant, Phase 5 (remaining 10 experts + EXPERT-PROD) is scrapped entirely.

In scope:
- For each of 4 experts (screenplay, editor, colorist, style_genome):
  - Author 5 curated refs (300-500 lines each, ≥3 concrete heuristics per ref)
  - Deep-refactor SKILL.md: thresholds + metrics + RAG invocation block + populated References table
  - Author 3 eval prompts
  - Run ablation eval: old-no-refs / new-no-refs / new-with-refs (3 conditions × N=12 verdicts)
- Preserve all 4 frozen `expert_id` values unchanged (FOUND-08 HARD RULE)
- Extend `screenplay.emotion_curve` schema with hooks/payoffs/cliffhangers arrays (closes Phase 2 HOOK-09 contract)
- Produce post-refactor eval comparison vs Phase 0 baseline for all 4 experts
- Make GO/NO-GO recommendation for Phase 5

Out of scope:
- Other 10 existing experts (Phase 5, conditional on Phase 3 GO)
- EXPERT-PROD (Phase 5)
- Full N≥20 eval run (Phase 6)
- Vector RAG via memory plugin (Phase 6 experiment)
- New SKILL.md structural conventions (use Phase 0 SKILL-LAYOUT.md spec)

</domain>

<decisions>
## Implementation Decisions

### Ref Curation Strategy
- **5 refs per expert** (within SC's 4-6 range) — 20 total refs across the phase
- **Source mix per expert:** 2 classic textbooks + 1 modern craft book + 1 academic paper + 1 CN-specific industry source
  - **screenplay:** Save the Cat (Snyder) + Story (McKee) + 短剧 pacing industry report + emotion-curve academic paper + CN 短剧 case studies
  - **editor:** In the Blink of an Eye (Murch) + The Technique of Film Editing (Reisz/Millar) + Rule of Six academic explication + montage theory paper + CN 短剧 cutting-rhythm source
  - **colorist:** If It's Purple (Bellantoni) + Color Correction Look Book (Hurkman) + color psychology cross-cultural paper + CN audience color preference study + digital color pipeline reference
  - **style_genome:** Director archive (expanded to 30-50 names) + genre DNA taxonomy + cross-cultural style paper + auteur theory academic + CN director style analysis
- **≥3 concrete heuristics per ref** (exceeds SC's ≥1 floor) — each heuristic must be a specific number/rule/threshold NOT in base model training
- **Ref length:** 300-500 lines per ref (substantive but not bloated)

### Refactor Depth & SKILL.md Changes
- **Revisions per SKILL.md:**
  1. **Quality thresholds** — numeric ranges updated based on curated ref heuristics (e.g., screenplay dialogue_density 0.4-0.6 → revised based on McKee dialogue-ratio findings)
  2. **Metrics array** — operational definitions refined (e.g., editor "rhythm_coherence" gets explicit cut-density window definition)
  3. **RAG invocation block** — provider-agnostic, placed after `## Role & Philosophy` before `## Core Capabilities`
  4. **References table** — populated with all 5 curated refs (Phase 0 FOUND-07 contract)
- **emotion_curve schema extension (screenplay only):** Add `hooks[]`, `payoffs[]`, `cliffhangers[]` arrays per Phase 2 HOOK-09 contract — closes the loop with HOOK's marker schema
- **Provider-agnostic phrasing:** STRONG form — every model/tool mention uses `<placeholder>` tokens + conditional fallback ("if `<video_gen_primary>` available, use it; otherwise inline heuristic")

### Ablation Eval & GO/NO-GO Decision
- **3 ablation conditions per PITFALLS #8:**
  1. **old-no-refs** — Phase 0 baseline SKILL.md (no RAG)
  2. **new-no-refs** — Refactored SKILL.md with RAG invocation block stripped
  3. **new-with-refs** — Refactored SKILL.md + RAG refs injected
- **3 prompts × 4 experts = 12 eval prompts total**
- **N per condition:** 3 prompts × 2 orderings (A/B + B/A) × 2 judges = 12 verdicts per condition per expert (48 per expert × 4 experts = 192 total eval calls)
- **GO/NO-GO gate criteria:**
  - GO if RAG uplift shows consistent direction (≥2/3 prompts improve with new-with-refs vs new-no-refs) across ≥3/4 experts
  - NO-GO if uplift is inconsistent or absent → recommend scrapping Phase 5
- **Judge panel:** Open-weight (per Phase 0 decision): Qwen3-235B + DeepSeek-V3 via OpenRouter; judge temp=0; CoT + `<decision>A|B|tie</decision>` tag

### Claude's Discretion
- Exact textbook/chapter selections within the source mix (e.g., which specific McKee chapters)
- Specific numeric threshold revisions (informed by refs but Claude's call)
- Concrete examples in each ref
- Order of refs in References table
- Final wording of eval prompts (shape is fixed by Phase 0 judge_prompt.md)
- Whether to use OpenRouter free tier or paid models for the 192 eval calls (operator's call based on budget)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets (from Phase 0/1/2)
- **Phase 0 baselines** at `_eval/baseline/{screenplay,editor,colorist,style_genome}/SKILL.md` — the "old-no-refs" condition source
- **`scripts/verify_skill_references.py`** — Validates refactored SKILL.md (must exit 0)
- **`_eval/runner.py`** — MT-Bench position-swap harness; supports ablation via `conditions` config
- **`_eval/judge_prompt.md`** — CoT template with 4 dimensions (industry_accuracy, professional_depth, actionability, language_quality)
- **`_eval/config.yaml.example`** — 2-judge open-weight panel config
- **`_shared/SKILL-LAYOUT.md`** — Reference anatomy spec (Source/Copyright/Last-verified/Summary/Heuristics columns)
- **`_shared/RAG-INVOCATION-PATTERN.md`** — Provider-agnostic pattern to embed in refactored SKILL.md
- **`_shared/glossary.md`** — 24+ EN↔CN entries; refs link rather than duplicate
- **`_shared/known-external-models.yaml`** — Allowlist (no changes needed unless new model refs introduced)
- **Phase 1 + 2 SKILL.md patterns** — compliance_marketing + hook_retention serve as templates for refactored structure (References table, per-platform branching pattern adapted to per-expert domain)
- **HOOK marker schema** (Phase 02-03) — `钩子/爽点/卡点` JSON shape to extend screenplay.emotion_curve with

### Established Patterns
- **Frontmatter schema** unchanged across all experts
- **References table** at top of SKILL.md (Phase 0 FOUND-07)
- **Provider-agnostic tokens** in body (Phase 1 CR-03 lesson reinforced)
- **Bilingual format:** EN YAML + EN H2 + CN prose
- **Per-expert eval prompt file:** `_eval/prompts/<expert>_demo.yaml`

### Integration Points
- **4 existing SKILL.md files to refactor:** `screenplay/`, `editor/`, `colorist/`, `style_genome/`
- **4 new `references/` directories** to create under each expert
- **20 new ref files** total (5 × 4)
- **4 new eval prompt files** (one per expert, 3 prompts each)
- **screenplay/SKILL.md emotion_curve schema extension** — adds hooks/payoffs/cliffhangers arrays
- **No changes to any expert_id** (frozen rule)
- **HOOK ↔ screenplay integration tested via emotion_curve extension**

</code_context>

<specifics>
## Specific Ideas

- **Ref authoring quality bar:** Each ref MUST contain ≥3 specific heuristics a base LLM would not produce from training:
  - **screenplay examples:** McKee's "gap between expectation and result" definition with concrete scene-parsing steps; Snyder's Beat Sheet with 15 specific beat types + page-count targets; 短剧-specific 3-act structure with minute-by-minute milestones for 90s/180s formats
  - **editor examples:** Murch's Rule of Six with weighted scoring (emotion 50% / story 25% / rhythm 10% / eye-trace 7% / 2D plane 5% / 3D space 3%); specific cut-density windows by genre; CN 短剧 faster-cut empirical data
  - **colorist examples:** Bellantoni's color-emotion studies with specific prevalence data (e.g., purple in 60% of villain scenes); Hurkman's specific scopes/transforms; CN audience cross-cultural color associations (red=festival+luck vs red=violence in West)
  - **style_genome examples:** 30-50 director DNA cards with specific signature shots; genre-specific cinematographic patterns; cross-cultural director influence maps
- **Threshold revisions should be empirically grounded:** cite the ref that justifies the new number
- **Eval prompts should include "trap" prompts** that test whether the model genuinely absorbed ref content (e.g., asking for a specific Murch Rule-of-Six weighting, where a base model would default to equal weighting)
- **GO/NO-GO report should be machine-readable JSON** + human-readable Markdown, stored in `_eval/reports/phase3-go-nogo.{json,md}`
- **Run ablation DRY-RUN first** to validate harness produces 3-condition output, then run live if OPENROUTER_API_KEY set, else ship dry-run + flag for Phase 6 live run

</specifics>

<deferred>
## Deferred Ideas

- **N≥20 eval run** — Phase 6 (Phase 3 ships N=3 per condition)
- **Other 10 experts RAG uplift** — Phase 5, conditional on Phase 3 GO
- **Vector RAG via memory plugin** — Phase 6 experiment
- **Automated ref refresh scraper** — Phase 6 polish
- **Cross-expert ablation** (e.g., does screenplay-with-colorist-refs beat screenplay-with-screenplay-refs?) — Phase 6 if interesting
- **Live OpenRouter run for 192 eval calls** — Phase 3 ships dry-run + harness validation; live run deferred to operator budget decision
- **Statistical significance testing with CIs** — Phase 6 with N≥20; Phase 3 uses simple direction-consistency rule

</deferred>
