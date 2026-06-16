# Phase 8: Node DAG + Per-Node Specs - Context

**Gathered:** 2026-06-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 8 produces the **machine-derivable, human-reviewable DAG** of pipeline nodes — converting Phase 7's 16 candidate node IDs into a final spec'd DAG with full per-node rigor (4 core + 8 STACK supplementary + 3 budget fields per node). This is the densest section of the v2.0 PRFP design suite.

**In scope:**
- Apply C1-C7 selection filter (FEATURES §5) to Phase 7's 16 candidates → final DAG node set
- Per-node full specs (15 fields per node): core_task / I/O contract / AIGC transformation point / traditional anchor / success_criteria (≥1 quantified) / fail_modes / fallback_strategy / dependencies / complexity_class / ai_capability_assumption / non_ai_alternative / rationale_for_existence / cost_budget / latency_budget / model_horizon
- DAG topology: hybrid (root → intent layer parallel → visual chain + audio branch + post branch → final gates) with 2 loops + 2 human gates
- 3 representations: `nodes.yaml` + `edges.yaml` (canonical) / `01-NODE-DAG.md` (rendered) / Mermaid visual
- C1-C7 check log (inline rejection table + appendix)
- Cost budget distribution (complexity-weighted, total within META-05 ¥1000-10000/episode ceiling)
- Model dated annex (global + per-node `current_instantiation` with `verified_date` stamps)
- theory_critic as consultative vertical edge (per META-06, creator-pulled)

**Out of scope (deferred):**
- 102-book corpus ↔ node bidirectional traceability matrix — **Phase 9**
- LLM creativity definition + consistency mechanism + prompt strategy — **Phase 10**
- Cross-comparisons vs 8 phases / 26 skills / dual-repo handoff — **Phase 11**
- Governance rules, validate_design.py lint, README, OPEN-QUESTIONS, CHANGELOG — **Phase 12**

</domain>

<decisions>
## Implementation Decisions

### C1-C7 Filter Approach
- **Strictness:** Pragmatic — keep 15 linear nodes + 1 consultative vertical (theory_critic); document marginal cases in C check log
- **theory_critic counting:** Exclude from linear node count (it's a consultative vertical edge, not linear DAG); 15 linear + 1 consultative = pipeline topology
- **Phase 7 merge candidates (visual_executor / audio_pipeline / compliance_gate):** Keep merged in Phase 8; document split-decision in C5 (single-ownership) check log for Phase 11 handoff review
- **C check log location:** Inline rejection table in `02-NODE-SPECS.md` header + appendix for rejected candidates from Phase 7's 16

### YAML Canonical Schema
- **Enforcement:** Convention-based YAML + structural grep lint; formal `validate_design.py` is Phase 12 GOV-02 deliverable
- **Document structure:** Single `nodes:` top-level mapping in `nodes.yaml`; separate `edges.yaml` file
- **Edge types (4):** `linear` (main DAG sequence) / `consultative` (theory_critic vertical) / `loop_with_critic` (generation↔critic iteration with exit condition) / `cross_cutting_invariant` (style/identity ownership)

### DAG Topology Shape
- **Overall:** Hybrid — root → intent layer (parallel: style_genome / screenplay+script_auditor / character_designer) → visual execution chain → audio branch (parallel) + post branch (parallel) → final gates (quality_gate + compliance_gate)
- **Loops (2 explicit):** (a) `screenplay ↔ script_auditor` (low-cost text loop); (b) `visual_executor ↔ continuity_auditor` (high-cost visual loop with max-iter + cost ceiling)
- **Human gates (2):** (a) after `screenplay` (narrative intent review — high leverage, <5 min budget); (b) after `editor` (final cut review — final checkpoint, <5 min budget)
- **Mermaid orientation:** TD (top-down) for main flow + LR (left-right) subgraphs for parallel branches

### Budget Fields + Model Annex
- **Cost budget distribution:** Complexity-weighted — `tool-capability`-heavy nodes (visual_executor, audio_pipeline) get higher weight; creative_source is human-time-heavy (lower cost, longer latency); theory_critic minimal overhead; total within META-05 ¥1000-10000/episode
- **`model_horizon` enum:** 3 classes — `stable_2026` (stable across model changes for ≥2 years) / `evolving` (quarterly updates) / `research_bet` (may fail)
- **Model annex location:** Global appendix in `02-NODE-SPECS.md` + per-node `current_instantiation` field with `verified_date` stamps
- **Critic pairing:** Keep Phase 7's 3 critic roles (script_auditor, continuity_auditor, quality_gate) + in-node self-critic steps where needed (composition self-check in cinematographer; rhythm self-check in editor); avoid node-count bloat

### Claude's Discretion
- Exact YAML schema field order within each node entry
- Which specific nodes get in-node self-critic steps (beyond the 3 paired critics)
- Cost budget specific ¥-amounts per node (within META-05 ceiling + complexity-weighted principle)
- Mermaid diagram styling (colors, edge labels)
- Whether to include a quick-reference `NODE-SPECS-CHEATSHEET.md` for kais-movie-agent impl team (Phase 11 also produces an impl-cheatsheet; Phase 8 cheatsheet would be node-spec-focused, Phase 11 handoff-focused)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Phase 7 output (primary input):** `.planning/research/v2-pipeline-design/00-FIRST-PRINCIPLES.md` — 16 candidate nodes with full per-node rigor (derivation + alternatives + classifications + steelman + anchor + analogy-validity)
- **Phase 7 §3.5 synthesis:** 10 structural properties the DAG must satisfy
- **Phase 7 §4 per-node fields:** derivation + epistemic-status + assumption-classification + steelman-elimination + alternatives-considered + corpus-anchor + analogy-validity — Phase 8 inherits these as `rationale_for_existence` source material
- **FEATURES.md §5:** C1-C7 selection criteria definitions
- **ARCHITECTURE.md:** YAML canonical schema guidance + 4 edge type constraint
- **PITFALLS.md §2.1-§2.11:** AIGC pipeline node-design failure modes (cost budgets, critic pairing, fallback strategies, model-commitment avoidance, etc.)

### Established Patterns
- **v1 expert_id compatibility:** Phase 7 preserved 14 of 16 candidate IDs as v1 expert_ids (HANDOFF-02 / FOUND-08); Phase 8 must continue this — no silent renames
- **YAML canonical + Markdown rendered pattern:** Industry-standard (OpenAPI/AsyncAPI); ARCHITECTURE.md §5 prescribes this for the design suite
- **MADR-style per-node records:** Phase 7 §1.6 declared this format; Phase 8 per-node entries follow same pattern

### Integration Points
- **Phase 8 output → Phase 9 input:** Final node IDs enable corpus-traceability bidirectional matrix (corpus-trace.yaml: node ↔ corpus)
- **Phase 8 output → Phase 10 input:** `creative_source` + `screenplay` + `script_auditor` nodes seed Phase 10's LLM-creative-distillation deep-dive
- **Phase 8 output → Phase 11 input:** Final DAG + per-node specs enable skills-mapping.yaml + kais-migration-matrix.yaml
- **Phase 8 output → Phase 12 input:** validate_design.py lint will check Phase 8's structural conventions

</code_context>

<specifics>
## Specific Ideas

- **Each node's `rationale_for_existence` field** should reference Phase 7's derivation directly (e.g., "per Phase 7 §3.1 D1.5 + §4.1 derivation"). This is the audit trail that connects Phase 8 specs to Phase 7 first-principles.
- **Cost budgets must be defensible** — each node's `cost_budget` should explain the ¥-amount with reference to either (a) current API pricing for `tool-capability` operations, (b) human-time-equivalent for `human-time-heavy` operations, or (c) industry benchmark.
- **`fail_modes` must be AIGC-specific** — not generic software fail modes. Examples: "LoRA identity drift after N shots", "TTS pronunciation degradation on Chinese dialects", "color grading AI misclassifies scene mood".
- **`fallback_strategy` must address the named fail mode** — generic "retry" is not enough. Examples: "switch to backup TTS provider for dialect X", "fall back to human colorist review if AI confidence < threshold", "degrade to static image if video gen fails > N retries".
- **YAML canonical must be validatable by `validate_design.py`** (Phase 12) — Phase 8 should structure the YAML so the lint can be a 30-line script, not a 300-line script.

</specifics>

<deferred>
## Deferred Ideas

- **Live cost validation** — Phase 8 budgets are estimates; live validation requires kais-movie-agent implementation + actual runs (FUTURE-04 per REQUIREMENTS.md)
- **Per-node A/B testing methodology** — design-doc scope; A/B test design is implementation milestone
- **Specific model API contracts** (request/response schemas for Sora/Kling/etc.) — out of scope per PITFALLS §1.3 + §2.7; capability-spec canonical only, model names in dated annex
- **Theory_critic trigger heuristics** — META-06 locks "creator-pulled"; heuristic trigger design is future research
- **Multi-form pipeline parameterization** — Phase 7 §3.2 D2.6 declared multi-form support; Phase 8 emits single DAG form with form-specific notes per node (短剧/微电影/长片 differences called out where load-bearing); formal multi-form parameterization is Phase 11 handoff

</deferred>

