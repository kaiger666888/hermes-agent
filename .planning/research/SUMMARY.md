# Project Research Summary

**Project:** Movie-Experts Suite v2 — Milestone **v2.0 PRFP** (Pipeline Redesign from First Principles)
**Domain:** Design-doc derivation — first-principles reconstruction of the kais-movie-agent AIGC 短剧/微电影 pipeline node set (delivers DESIGN DOCS ONLY, zero implementation code, dual-repo handoff)
**Researched:** 2026-06-16
**Confidence:** HIGH overall (4 research files triangulate cleanly on corpus, methodology, and risk; primary disagreements are framing, not facts)

> **Note:** This SUMMARY supersedes the v1 research synthesis (2026-06-15). v1 research files (STACK/FEATURES/ARCHITECTURE/PITFALLS) have been overwritten in place with v2.0 PRFP-scoped research; v1 carryover audit is captured inside STACK.md.

---

## Executive Summary

This milestone is unusual: the deliverable is **design documents, not code**. It is a first-principles (Musk-style) derivation of a new AIGC film-pipeline node set that will eventually hand off to two downstream repos (`hermes-agent/skills/movie-experts/` for the knowledge/RAG layer; `kais-movie-agent/` for the execution/orchestration layer). The four research files converge on a clear shape for the work: a derivation-first design-document suite, anchored to a verified 102-book corpus, represented as YAML-canonical + Markdown-rendered, with strict non-binding handoff contracts.

The recommended approach is **derivation-first, integration-last**. Phase A (first-principles derivation producing a candidate node set) is the bottleneck — nothing else may start until it produces a defensible candidate node list. Once that exists, three streams run in parallel: node DAG + per-node specs (Phase B), 102-book corpus traceability (Phase C), and the LLM-creative-distillation deep-dive (Phase D). Cross-comparisons and the dual-repo handoff (Phase E) cannot begin until B+C+D are stable. Finalization (governance, open-questions, README) closes the milestone (Phase F). The critical path is **A → B → E → F**.

The headline risk — flagged unanimously across PITFALLS, STACK, and FEATURES — is **first-principles theater**: producing a doc that *sounds* like Musk-style derivation but is actually analogy and vibes dressed in reductionist language, which is worse than honest intuition because it feels unchallengeable. The single most load-bearing deliverable is therefore the structural rigor of the derivation log itself: per-node `derivation` fields, epistemic-status tagging (physical / psychological / platform-algorithmic / tool-capability), explicit steelman-the-elimination sections, an alternatives-considered log, and a contingent-vs-validated-invariant classification. The second-largest risk is **design-impl drift across the two repos** — the design will be stale by the time kais-movie-agent implements unless the handoff phase explicitly addresses baseline-ref, impl-cheatsheet, ownership matrix, and a date-stamped versioning scheme.

---

## Key Findings

### Recommended "Stack" (NOT code — source materials + methodologies)

This milestone ships ZERO code. The "stack" is the corpus + canon that node-design phases cite. STACK.md confirms physical locations by direct filesystem inspection.

**Source corpus (HIGH confidence — direct `ls` verified):**
- **102-book MinerU-converted film library** (`/home/kai/Downloads/100+本影视剪辑书/converted/` — 102 books, ~9.7M CN chars, 16 MinerU-classified categories) — answers "what is the irreducible human craft of cinema?"
- **Pre-synthesized 6-stage skill corpus** (`…/skills-影视创作/{00-orchestrator,01-剧本,02-分镜,03-拍摄,04-后期,05-制片,06-理论批评,case-studies}/` — 95+ files) — the "prior synthesis" first-principles must deliberately diverge from or build on
- **Already-integrated hermes corpus** (`skills/movie-experts/_shared/project-corpus/` — 14 files including README + INTEGRATION-REPORT + 12 content refs) — concentrated answers to theory + craft + producing questions; 9 of 12 ready to cite without re-mining
- **kais-movie-agent historical architecture** V1→V8 (`/data/workspace/kais-movie-agent/docs/{ARCHITECTURE_AND_WORKFLOW,WORKFLOW,V2-REFACTOR-PLAN,v6-architecture-notion,V8-ARCHITECTURE}.md` + 15 kais-* sub-skills) — the "what was tried" dataset; first-principles must explicitly question inherited assumptions (linearity, JSON asset bus, 20-step granularity, full-LLM-orchestration)

**Methodology canon (MEDIUM-HIGH confidence — web-verified June 2026):**
- **Musk first-principles** (Kevin Rose 2012 Foundation interview; Isaacson 2023 biography) — the headline method mandated by milestone brief
- **Aristotle φυσικαὶ ἀρχαί** (Physics I; Metaphysics Δ) — the philosophical root; distinguishes "more knowable to us" (analogy) from "more knowable by nature" (foundational truth)
- **TRIZ contradiction matrix** (Altshuller; 40 inventive principles, IEEE-verified "20 of 40 cover 75%") — contradiction-resolution lens when node-design surfaces trade-offs
- **Jobs-style subtractive reduction** (complementary to first-principles — derive then prune)

**LLM-creative-story research (MEDIUM-HIGH confidence — 8 peer-reviewed/arXiv refs):**
- Plot-hole detection benchmark (arXiv 2504.11900), ConStory-Bench (2603.05890), CONFACTCHECK (ACL 2025) — the "自洽性检验机制" evidence base
- Survey on LLMs for Story Generation (EMNLP 2025 Findings), Learning to Reason for Long-Form (OpenReview), Awesome-Story-Generation (GitHub) — the "创意凝练 prompt 策略" evidence base
- Creator-Centric Methods (ACM), Scaffolding the Story (IASDR) — supports "AI assists, doesn't replace creative intent"

### Expected Features (Node-Design Decisions to Scope)

FEATURES.md enumerated 41 candidate nodes grouped into 4 phases. The roadmapper should treat these as a working palette, not a final set.

**Table stakes — universal nodes every AIGC film pipeline must contain (~22 candidates):**
- **creative_source** (DAG root, story-kernel mining) — answers "what does the audience ultimately receive?"
- **style_genome, screenplay, character_designer** — define reusable identity/style assets
- **cinematographer, storyboard_designer, drawer, animator** — visual intent → execution chain
- **voicer + lip_sync** — audio-video lock (AIGC-native explicit alignment node)
- **editor, colorist, composer, foley, mixer** — post-production cluster (runs in parallel where possible)
- **quality_gate (multi-dim quantitative scorer), compliance_pre_check + compliance_final, distribution_cut_variants, poster + trailer** — delivery
- **prompt_injector (intent → model tokens)** — AIGC-native consistency mechanism (load-bearing)
- **continuity_auditor (cross-shot)** — AIGC-specific consistency verifier

**Differentiators — first-principles-derived nodes that distinguish the new pipeline from inherited traditional workflow (~14 candidates):**
- **script_auditor (5-dim quantitative, decoupled from screenplay)** — removes self-grading bias
- **hook_retention (commercial engine)** — for 竖屏短剧 this REPLACES part of screenplay's role
- **camera_preview (low-param cheap-fail loop)** — AIGC-native equivalent of "rough cut / final cut" split
- **theory_critic (consultative vertical, NOT in linear DAG)** — serious-film vertical only
- **topic_curatorial scan** — for high-volume production studios (defer)

**Anti-features — wrong-turns the design must reject (≥12 catalogued):**
- **AF-1 Over-decomposition** (100+ micro-nodes; "more nodes = more sophisticated" belief). Soft node-count budget: **8-15 per PITFALLS §2.6, with ≤25 as a hard ceiling**
- **AF-2 AI as drop-in replacement for human roles** ("AI Screenwriter" without compression/expansion justification)
- **AF-3 Missing critic/reviewer in creative loops** (every generation node needs a paired verifier with quantitative metric)
- **AF-5 Premature optimization for specific gen models** (hard-coding Sora/Kling/Veo — capability-spec must be canonical; model names only in dated annex)
- **AF-9 Auto-distribution / auto-upload nodes** (TOS risk, out of scope)
- **AF-12 Theory-critic as a blocking gate in linear pipeline** (kills 短剧 throughput; must be consultative)

**Selection criteria (the C1-C7 test from FEATURES §5 — all 7 must hold for a node set to qualify as "first-principles-derived"):**
1. User-value-anchored existence (rationale references user value, not "this is a traditional工序")
2. AIGC transformation measurability (measurable delta: cost / latency / quality / capability)
3. Compression-justified or expansion-justified (per node, explicitly)
4. Independent evaluability (≥1 quantitative success metric per node)
5. Single ownership (non-overlapping core_tasks)
6. Decoupled I/O contract (machine-readable schemas, statically type-checkable DAG)
7. Loop placement explicit (every feedback loop documented with trigger + exit condition)

### Architecture Approach

ARCHITECTURE.md prescribes a **derivation-first design-document suite** with three load-bearing constraints: (1) dual-repo non-binding handoff, (2) derivation record is the epistemic anchor (not the DAG), (3) machine-derivable AND human-reviewable — mandates YAML canonical schema + Markdown prose + Mermaid rendered views.

**Major components (design deliverable artifacts):**
1. **§00-FIRST-PRINCIPLES.md** — Musk-style derivation trace (the epistemic anchor)
2. **nodes.yaml + edges.yaml + corpus-trace.yaml** — canonical schema (single source of truth)
3. **§02-NODE-SPECS.md** — per-node spec sheets rendered from YAML, each with 3-line audit header (🅰 first-principles / 📚 traditional anchor / ⚡ AIGC justification)
4. **§03-CORPUS-TRACEABILITY.md** — bidirectional 102-book ↔ node coverage matrix
5. **§04-LLM-CREATIVE-DISTILLATION.md** — standalone horizontal deep-dive (user explicitly required as separate dimension)
6. **§05 + §06 COMPARISON-VS-{8-PHASES,26-SKILLS}.md** — non-binding delta analyses (MUST come after derivation to avoid contamination)
7. **§07-HANDOFF-PLAN.md** — dual-repo contract (skills-mapping.yaml + kais-migration-matrix.yaml)
8. **§08-GOVERNANCE.md + §09-OPEN-QUESTIONS.md + §10-CHANGELOG.md** — living-doc rules, known unknowns, audit trail

**Physical location recommended:** `.planning/research/v2-pipeline-design/` (subdirectory, not flat files, to group handoff artifacts and avoid polluting existing v1 milestone archive).

**The ONLY code allowed in this milestone:** a ~30-line governance-lint script (`scripts/validate_design.py`) — developer tool only, NOT shipped to downstream consumers.

### Critical Pitfalls (Top 5, consolidated from PITFALLS §"Top 5 Critical Risks")

1. **First-principles theater (PITFALLS 1.1, 1.5, 1.6, 5.4)** — Derivation that is ex-post justification dressed in reductionist language. The entire milestone is wasted effort if this happens. *Mitigation: derivation-record phase enforces structural rigor — per-node `derivation` field, epistemic-status tagging, steelman-the-elimination section, alternatives-considered log. Warning signs: derivation section shorter than node-description; nodes in same order as existing 8 phases; word "obviously" in justifications.*

2. **Design-impl drift across two repos (PITFALLS 3.1-3.5)** — Design doc stale by the time kais-movie-agent implements. v1 RETROSPECTIVE's "SUMMARY ↔ README drift" (Key Lesson 7) is the small-scale preview. *Mitigation: handoff doc includes `kais-movie-agent_baseline_ref` (git SHA), 1-2 page impl-cheatsheet annex, explicit ownership matrix (design-intent layer vs implementation layer), date-stamped versioning scheme.*

3. **Throwing out validated craft as "bias" (PITFALLS 1.2, 5.3)** — Discarding Murch / Field / 180° axis rule as "historical baggage." Musk's actual method discards *analogies with no physical basis*, not *validated invariants*. *Mitigation: corpus-anchor phase + assumption-classification (contingent vs validated-invariant) as required structural elements.*

4. **Premature model-commitment (PITFALLS 1.3, 2.7)** — Hard-coding Sora/Kling/Veo into node specs guarantees staleness within 6-12 months. v1 already burned by this (`animator/SKILL.md` shipped phantom `wan22_video`). *Mitigation: capability-spec is canonical layer; model names appear only in dated annex with `verified_date` stamps. Node DAG must be valid even if every named model is swapped.*

5. **Creative-story node under-specified (PITFALLS 4.1-4.7)** — The user's headline emphasis ("有创意且逻辑自洽") maps to huge surface area. Hand-waving novelty, self-consistency, and platform-vs-art tension produces either random or cliché output. *Mitigation: LLM-creative sub-doc must operationally define creativity (novelty within inviolable constraints), specify consistency-context input + novelty-pressure mechanism, support template library (not single Save-the-Cat template), and address platform-vs-art tension explicitly.*

---

## Cross-File Conflicts Surfaced (Synthesis Recommendations)

The 4 research files are largely convergent, but they disagree on framing in 5 places. Below: the conflict, then the synthesizer's recommended position.

### Conflict 1: Node-count target
- **STACK** (implicit): "minimum viable node set" — no number stated
- **FEATURES**: MVP "must-document nodes (P1)" = 22+ candidates; target overall ~25-30 ("aim for ~25 nodes, not 100")
- **ARCHITECTURE**: target 10-15 nodes ("per PROJECT.md: minimal necessary node set"); scaling table shows architecture holds without structural changes at 10-15
- **PITFALLS**: soft node-count budget **8-15 for short-drama pipeline**, ≤25 hard ceiling; node count grows during design = smell

**Synthesis position:** Roadmapper should scope the milestone for **8-15 nodes** as the derivation target, with explicit justification required for each node beyond that ceiling. FEATURES.md's 41 candidates are a *palette to select from*, not a target. The C1-C7 selection criteria (esp. C1 user-value-anchored existence + C5 single ownership) are the filter that compresses 41 → 10-15. The MVP "P1 must-document" list of 22 should be interpreted as "candidates that must be *considered*" not "candidates that must *appear in the final DAG*."

### Conflict 2: Phase structure for the design work itself
- **STACK** (§3.3 + §6.2): recommends building node-design from corpus clusters (剧本创作 + 电影理论 + 导演表演 + 电影教材 + 前期分镜 + 剪辑后期 + high-value "其他")
- **FEATURES** (§3): enumerates candidates by traditional-phase grouping (Pre-Production / Production / Post-Production / Delivery) — implies a phase-organized build
- **ARCHITECTURE** (§5): explicit 6-phase decomposition A→F with critical path A→B→E→F and parallelism (C, D alongside B)
- **PITFALLS** (Pitfall-to-Phase Mapping §): maps pitfalls to PROJECT.md's 5 target features (#1 derivation-record / #2 node-DAG / #3 corpus-anchor / #4 LLM-creative-subdoc / #5 handoff-doc) — implies a 5-phase structure

**Synthesis position (recommended for the roadmapper):** Adopt **ARCHITECTURE.md's 6-phase structure (A→F)** because (a) it is the only one with explicit critical-path + parallelism analysis, (b) it subsumes PITFALLS' 5-feature mapping (Phase A = feature #1 + part of #3; Phase B = feature #2 + #3; Phase D = feature #4; Phase E = feature #5 + the "comparison-vs-8-phases" deliverable PITFALLS calls out), (c) FEATURES' pre-prod/prod/post/delivery grouping is a *content taxonomy for the node-spec phase*, not a *work-decomposition*. STACK's corpus-cluster grouping is a *mining strategy for Phase C*, not a separate phase structure. See "Implications for Roadmap" below.

### Conflict 3: Should the corpus anchor come before or after node derivation?
- **STACK** (§1.4): implies corpus informs the first-principles questions ("Pair this ref with… consider re-mining books…")
- **FEATURES** (§1): "the raw material any first-principles derivation must either justify keeping, justify eliminating, or justify merging" — derivation is *upstream* of corpus citation
- **ARCHITECTURE** (§5): Phase A (derivation) produces candidate node set → Phase B (specs) names corpus anchors → Phase C (traceability) back-links
- **PITFALLS** (1.2): "the design throws out validated craft knowledge… treating them as bias to be cleansed" — implies corpus must be consulted during derivation

**Synthesis position:** Derivation (Phase A) is *primary* — the candidate node set must fall out of the reasoning trace, not be imported from the corpus. BUT derivation must be corpus-aware: the first-principles questions in Phase A ("what can AI not replace?", "what determines microfilm quality?") reference corpus subsets per STACK §1.4. The corpus-anchor *traceability matrix* (Phase C) is then a downstream *verification* artifact — does each derived node actually have ≥1 corpus citation? If a derived node has 0 strong citations, either (a) the node is AIGC-native with no traditional precedent (justify explicitly), or (b) the derivation missed something (revisit Phase A). This resolves both the "throw out craft as bias" pitfall AND the "contamination" risk.

### Conflict 4: Is theory_critic in the linear DAG?
- **FEATURES** (§3.1 row 9): "OPTIONAL — vertical, not in linear pipeline"
- **FEATURES** (§3 dependency notes): "theory_critic is consultative: Not in linear DAG; invoked when pipeline encounters its domain"
- **PITFALLS** (AF-12 / 4.7): theory-critic as blocking gate is an anti-feature
- **ARCHITECTURE**: edge type `consultative` is one of the 4 constrained edge types — explicitly supports this pattern

**Synthesis position:** Triangulated — theory_critic is a **consultative vertical**, NOT in the linear DAG. Edge type is `consultative`. This is settled; the roadmapper does not need to relitigate it.

### Conflict 5: How much should the design bind downstream repos?
- **PROJECT.md**: "范围严格收口: 本次里程碑交付仅设计文档"
- **ARCHITECTURE** (§3, §4, Anti-Pattern 3): "binding: non_binding_recommendation" hard rule; design NEVER modifies downstream files
- **PITFALLS** (3.3): ownership matrix must be explicit — design-intent layer (hermes-agent) vs implementation layer (kais-movie-agent) vs co-owned DAG (changes require sign-off from both)

**Synthesis position:** Non-binding is settled. The handoff phase (Phase E) must produce: (a) `skills-mapping.yaml` + `kais-migration-matrix.yaml` with `binding: non_binding_recommendation`, (b) explicit ownership matrix, (c) baseline-ref + versioning scheme, (d) impl-cheatsheet annex. The design's job is to be useful enough that downstream teams WANT to act on it — not to compel them.

---

## Implications for Roadmap

**Recommended phase structure (synthesizing ARCHITECTURE.md's A→F decomposition, validated against PITFALLS' pitfall-to-phase mapping and FEATURES' content taxonomy):**

### Phase A: First-Principles Derivation
**Rationale:** PROJECT.md is explicit ("节点设计从 0 推"). Every later section is a consequence of the derivation. Nothing else may start until Phase A produces a defensible candidate node set. This is the hardest intellectual work in the milestone.
**Delivers:** `00-FIRST-PRINCIPLES.md` — the Musk-style reasoning trace, concluding with a candidate node set. Required structural elements per PITFALLS 1.x: per-node `derivation` field, epistemic-status tagging (physical / psychological / platform-algorithmic / tool-capability), steelman-the-elimination, alternatives-considered log, contingent-vs-validated-invariant classification, analogy-validity field per node.
**Addresses:** Target feature #1 (first-principles derivation record). Avoids pitfalls 1.1, 1.5, 1.6, 5.1-5.4.
**Must use:** STACK §4 (Musk + Aristotle + TRIZ methodology canon), STACK §1.4 (per-question corpus subsets — derivation is corpus-aware but corpus does not dictate the node set).
**Critical-path position:** BOTTLENECK. No parallel work permitted.

### Phase B: Node DAG + Per-Node Specs (primary)
**Rationale:** Once Phase A produces candidate node IDs, the DAG can be drawn and specs drafted. Specs are the densest section. Phase B can begin in parallel with Phase C once node IDs exist.
**Delivers:** `01-NODE-DAG.md` + `02-NODE-SPECS.md` + canonical `nodes.yaml` + `edges.yaml`. Each node spec follows FEATURES §4 schema (core_task / I/O / AIGC transformation point / traditional anchor + STACK additions: success_criteria, fail_modes, fallback_strategy, dependencies, complexity_class, ai_capability_assumption, non_ai_alternative, rationale_for_existence, cost_budget, latency_budget, model_horizon). Apply C1-C7 selection criteria to filter 41 candidates → 8-15 final nodes.
**Addresses:** Target feature #2 (node DAG + I/O contracts + AIGC transformation points + traditional anchors). Avoids pitfalls 2.1-2.11.
**Must use:** STACK §1-2 (corpus + hermes-integrated refs for traditional anchors), FEATURES §2 (AIGC-native compression/expansion patterns), FEATURES §3 (41-candidate palette).
**Critical-path position:** On critical path. Partially parallelizable with C and D.

### Phase C: 102-Book Corpus Traceability (parallel)
**Rationale:** Corpus traceability can begin as soon as Phase A produces node IDs — does not need full specs. Runs in full parallel with B-spec-finalization and D. This is a verification artifact: does each derived node have ≥1 strong corpus citation?
**Delivers:** `03-CORPUS-TRACEABILITY.md` + `corpus-trace.yaml` — bidirectional 102-book ↔ node matrix. Per-anchor tags required (PITFALLS 6.x): `applicable_form` (长片/微电影/短剧/universal), challenge-source engagement (≥1 corpus source that *disagrees* with the node's design), principle-vs-workflow separation, original-term preservation (汉字 alongside gloss).
**Addresses:** Target feature #3 (传统经验锚点对照). Avoids pitfalls 1.2 (throwing out validated craft), 6.1-6.4 (cherry-picking, anachronism, genre conflation, translation loss).
**Must use:** STACK §1 (102-book corpus physical locations + category breakdown), STACK §2 (already-integrated hermes corpus — 9 of 12 refs ready to cite directly).
**Critical-path position:** Parallel with B and D. Must be stable before Phase E.

### Phase D: LLM-Creative-Distillation Deep-Dive (parallel)
**Rationale:** Horizontal concern — depends only on Phase A's definition of "what AI can/cannot do". Runs in full parallel with B and C.
**Delivers:** `04-LLM-CREATIVE-DISTILLATION.md` — standalone deep-dive covering: (a) definition of creativity (novelty within inviolable constraints — not randomness), (b) self-consistency check mechanism (consistency-context input + logic-critic), (c) LLM distillation prompt strategy, (d) fail modes. Required design elements per PITFALLS 4.x: consistency-context input, novelty-pressure mechanism (with creative_source wiring), template library (not single template), platform-vs-art tension address.
**Addresses:** Target feature #4 (LLM 创意凝练专题). Avoids pitfalls 4.1-4.7.
**Must use:** STACK §5 (8 LLM-story-gen references mapped to sub-topics).
**Critical-path position:** Parallel with B and C. Must be stable before Phase E.

### Phase E: Cross-Comparisons + Dual-Repo Handoff
**Rationale:** Cannot begin until B+C+D all stable (need final node set, corpus trace, and LLM-distillation patterns to compare against existing 8 phases / 26 skills). This is where design-impl-drift risk is highest — must produce explicit handoff artifacts.
**Delivers:** `05-COMPARISON-VS-8-PHASES.md` + `06-COMPARISON-VS-26-SKILLS.md` + `07-HANDOFF-PLAN.md` + `skills-mapping.yaml` + `kais-migration-matrix.yaml`. Required handoff elements per PITFALLS 3.x: `kais-movie-agent_baseline_ref` (git SHA), 1-2 page impl-cheatsheet annex, ownership matrix (design-intent / implementation / co-owned-DAG), date-stamped versioning scheme (`design-2026-06-16-prfp` with `supersedes`/`superseded_by`), skill-DAG mapping table (preserve expert_ids per v1 FOUND-08 frozen rule), convergence log (where new DAG agrees with existing pipeline — justify agreement, not just divergence).
**Addresses:** Target feature #5 (双 repo 交接说明) + PITFALLS' "comparison-and-gap-analysis" sub-deliverable. Avoids pitfalls 1.4 (divergence-for-divergence), 3.1-3.5.
**Must use:** STACK §3 (kais V1-V8 evolution history as the "what was tried" dataset).
**Critical-path position:** On critical path. Depends on B+C+D.

### Phase F: Finalization (Governance + Open Questions + README)
**Rationale:** Living-doc governance, known unknowns, audit trail, and entry-point README. Small in effort but load-bearing for downstream consumers.
**Delivers:** `08-GOVERNANCE.md` (rules G1-G7 per ARCHITECTURE §7), `09-OPEN-QUESTIONS.md` (mandatory honesty about gaps — feeds downstream research phases), `10-CHANGELOG.md` (append-only audit trail), `README.md` (final suite-level index with 3-page executive summary per PITFALLS 7.3), `scripts/validate_design.py` (governance lint — the only code in the milestone).
**Addresses:** PITFALLS 7.x (over-specifying, under-specifying, no exec summary, missing rationale, no versioning), ARCHITECTURE §7 (living-doc governance rules).
**Must use:** v1 PROJECT.md `Key Decisions` table pattern (Decision/Rationale/Outcome) — v1 RETROSPECTIVE validated this; v2.0 must not regress.
**Critical-path position:** On critical path. Final phase.

### Phase Ordering Rationale
- **A first** because PROJECT.md mandates derivation from first principles. Every other section is downstream of it. Starting elsewhere guarantees rework against a moving target.
- **B+C+D parallel** because they have minimal interdependencies once Phase A produces node IDs (B needs full specs, C needs only IDs, D needs only the AI-limits definition).
- **E after B+C+D** because comparisons and handoff require all design artifacts to be stable. Handing off a half-derived node set is worse than useless.
- **F last** because finalization requires everything else committed with CHANGELOG entries.
- This ordering avoids every Category 1 pitfall (derivation-first prevents first-principles theater) and every Category 3 pitfall (explicit handoff ceremony prevents design-impl drift).

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase A (First-Principles Derivation):** HIGH research load — Musk-method primary-source verification (PITFALLS 5.x Open Question #4), epistemic-status tagging framework, steelman-the-elimination methodology. Recommend `/gsd:plan-phase --research-phase A` to verify Musk quotes against Isaacson biography before citing them.
- **Phase B (Node DAG + Specs):** MEDIUM research load — current (2026-Q2) AI capability stability survey needed (FEATURES gap: "which `ai_capability_assumption` entries are stable_2026 vs evolving vs research_bet?"). Per-node cost/latency budgets need platform-economics validation (PITFALLS Open Question #1: actual cost ceiling for indie 短剧 episode).
- **Phase D (LLM-Creative-Distillation):** MEDIUM research load — STACK §5 provides 8 references but phase-specific deep-dives into prompt-strategy subtopics may need Awesome-Story-Generation follow-ups.

**Phases with standard / well-precedented patterns (skip research-phase):**
- **Phase C (Corpus Traceability):** Mechanical mapping against 102-book index — the corpus is already verified by direct `ls` (STACK §1) and 9 of 12 hermes-integrated refs are ready to cite. No new research needed.
- **Phase E (Handoff):** Non-binding handoff is a well-precedented pattern (RFC/ADR); ARCHITECTURE §3-4 prescribes the exact YAML schema. No new research needed.
- **Phase F (Finalization):** v1 PROJECT.md `Key Decisions` pattern is the template; no new research needed.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack (corpus + methodology canon) | HIGH | STACK.md verified by direct filesystem inspection (`ls` of all corpus paths, file reads of all kais-movie-agent architecture docs). LLM-story-gen references are MEDIUM-HIGH (peer-reviewed, web-verified June 2026). |
| Features (node-design decisions) | MEDIUM-HIGH | FEATURES.md synthesizes 41 candidates from corpus + existing 26-expert + 11-phase + AIGC ecosystem knowledge. AIGC-native compression/expansion patterns are MEDIUM (industry practice, not project-benchmarked). Selection criteria C1-C7 are MEDIUM (derived from project constraints + Musk reduction; not externally validated). |
| Architecture (design-doc structure + handoff) | HIGH | ARCHITECTURE.md grounded in direct reads of PROJECT.md, both repo READMEs, V8-ARCHITECTURE, V2-REFACTOR-PLAN, INTEGRATION.md, 26-skill inventory, v1 ARCHITECTURE.md, 102-book corpus index. YAML-canonical + Markdown-rendered pattern is industry-standard (OpenAPI/AsyncAPI). |
| Pitfalls (failure modes) | HIGH | PITFALLS.md grounded in v1 RETROSPECTIVE + actual PROJECT.md v2.0 scope + Musk/Isaacson method critique + AIGC pipeline literature. Each pitfall has concrete film/AIGC examples and warning signs. |

**Overall confidence:** HIGH. The 4 research files triangulate cleanly. The disagreements are framing-level (node-count target, phase-structure granularity), not fact-level. The synthesizer's recommendations above resolve all 5 cross-file conflicts.

### Gaps to Address

Gaps that cannot be resolved from research alone — flag for user input during requirements phase, or for phase-specific research during planning:

- **Node-count target validation (FEATURES gap):** Is 8-15 (PITFALLS), ~25 (FEATURES), or 10-15 (ARCHITECTURE) the right count? Synthesizer recommends 8-15 as the derivation target with ≤25 hard ceiling; user confirmation requested during requirements phase.
- **Actual cost ceiling for indie 短剧 episode in 2026 (PITFALLS Open Question #1):** Affects every node's `cost_budget` field. PITFALLS assumes ¥1000-10000; verify against current platform economics.
- **Which 2026-Q2 短剧 platform conventions are stable vs volatile (PITFALLS Open Question #2):** Affects epistemic-status tagging. If 抖音 conventions are psychological (stable) rather than platform-algorithmic (volatile), node justifications change.
- **Musk quote primary-source verification (PITFALLS Open Question #4):** Pitfalls 5.1-5.4 paraphrase Musk stories; exact wording must be verified against Isaacson biography before the design doc cites them. LOW confidence on exact wording; HIGH confidence on gist.
- **Skill-DAG mapping: which of the 26 existing experts map cleanly vs need deprecation (PITFALLS Open Question #5):** Required for Phase E handoff; may surface politically/technically loaded findings about which v1 experts the v2.0 design obsoletes.
- **Theory_critic trigger condition (FEATURES gap):** Confirmed consultative (Phase 8), but *when* does the pipeline invoke it? Needs design during Phase B or D.
- **Loop exit conditions for every `loop_with_critic` node (FEATURES gap):** Defer to per-node design during Phase B.
- **V8 审核门 (review gate) survival into v2.0 (PITFALLS Open Question #3):** V8 architecture has review gates; v2.0 may legitimately automate some. Handoff doc must address explicitly during Phase E.

---

## Open Questions for User (the roadmapper cannot resolve these from research alone)

1. **Node-count target.** Should the derivation target be **8-15** (PITFALLS / ARCHITECTURE recommendation, with ≤25 hard ceiling) or **~25** (FEATURES MVP P1 list)? This sets the rigor bar for Phase A — fewer nodes means each one must defend itself harder.
2. **Cost-ceiling assumption.** Should we adopt PITFALLS' assumption of **¥1000-10000/episode** as the budget envelope that constrains every node's `cost_budget`, or does the user have a different figure in mind (this drives whether loops, multi-model retries, etc. are affordable)?
3. **Single-author vs distributed authorship.** ARCHITECTURE Anti-Pattern 7 warns against mixing design authority with implementation authority. Does the user intend to be the sole design maintainer for this milestone, or should we plan for multiple authors (affecting Phase F governance rules)?
4. **Theory_critic invocation trigger.** Confirmed consultative, but when does the pipeline actually fire it? User-stated artistic-intent threshold, heuristic trigger, or always-available-but-optional?
5. **Bilingual doc policy.** v1 SKILL.md files follow EN structure + CN prose. Does the v2.0 design-doc suite follow the same pattern, or is it English-primary given the methodology canon (Musk/Isaacson/Aristotle/TRIZ) is English-sourced? Affects Phase F glossary work and PITFALLS 6.4 (translation/context loss).

---

### Ready for Requirements

4 source research files + this SUMMARY.md feed the requirements phase. Cross-file conflicts resolved above; open questions flagged for user input.

**Relevant file paths:**
- `/data/workspace/hermes-agent/.planning/research/STACK.md`
- `/data/workspace/hermes-agent/.planning/research/FEATURES.md`
- `/data/workspace/hermes-agent/.planning/research/ARCHITECTURE.md`
- `/data/workspace/hermes-agent/.planning/research/PITFALLS.md`
- `/data/workspace/hermes-agent/.planning/PROJECT.md` (Current Milestone v2.0 PRFP section)
