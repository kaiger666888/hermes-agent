# Architecture Research: Pipeline Redesign from First Principles (v2.0 PRFP)

**Domain:** Design-document architecture for a cross-repo pipeline handoff (hermes-agent skills layer + kais-movie-agent execution layer)
**Researched:** 2026-06-16
**Overall confidence:** HIGH (grounded in direct reads of `.planning/PROJECT.md`, both repo READMEs, V8-ARCHITECTURE.md, V2-REFACTOR-PLAN.md, INTEGRATION.md, the 26-skill inventory, the v1 ARCHITECTURE.md, and the 102-book corpus index)

---

## Executive Summary

This milestone is unusual: the deliverable is **only design documents, no code**. The "architecture" question is therefore not "what code do we write" but "what is the canonical structure of the design deliverable, how is it represented, how does it hand off to two downstream repos, and in what order should the design work itself be done." Every recommendation below answers one of those four questions.

Three load-bearing constraints shape every decision:

1. **Dual-repo handoff** — The design lives in `hermes-agent/.planning/` (because movie-experts is the knowledge layer), but must produce non-binding contracts readable by both `hermes-agent/skills/movie-experts/` (26 skills, knowledge/RAG layer) and `kais-movie-agent/` (separate repo with its own `.planning/`, execution/orchestration layer). The design must NOT mutate either repo. Both downstream consumers will open their own future milestones to act on it.

2. **First-principles derivation is the load-bearing section, not the DAG** — PROJECT.md is explicit: nodes are derived "from 0" (ignoring existing 8 phases + 26 skills), with Musk-style reasoning traces. This means the derivation record is the **epistemic anchor**; the DAG, the per-node specs, the corpus traceability, and the comparisons are all *consequences* of that derivation. Section ordering and review cadence must reflect this — a node that cannot be defended from first principles cannot survive, regardless of how neatly it slots into a DAG.

3. **The design must be machine-derivable AND human-reviewable** — Downstream consumers will (a) auto-generate skill-gap reports, (b) auto-generate phase-migration matrices, (c) run governance checks ("does this node have a first-principles defense? a corpus citation? an AIGC-justification?"). This mandates a structured canonical format (YAML/JSON) for the machine-derivable parts, layered under human-readable prose. Pure markdown alone is insufficient; pure schema alone is hostile to derivation review.

The rest of this document is organized around the 7 sub-questions in the milestone brief.

---

## 1. Design Document Structure (Canonical Layout)

### Recommended Section Order

The order is **derivation-first, integration-last**. Every downstream section must be defensible by walking backward to the derivation record. Skipping ahead (e.g., drafting the DAG before the first-principles pass) is the single largest risk to this milestone's integrity.

| # | Section | Purpose | Depends On |
|---|---------|---------|------------|
| 0 | **README.md** (suite-level index) | Single entry point. Lists every artifact, its current review status, who the downstream consumer is, and how to navigate. | — (skeleton only at Phase 0; full version in Phase E) |
| 1 | **00-FIRST-PRINCIPLES.md** | The Musk-style reasoning trace. Starts from irreducible questions ("What does the viewer ultimately receive?", "Why do 短剧 live or die in 3 seconds?", "What can AI actually accelerate?", "What can AI never replace?"). Derives a candidate minimal node set as the **conclusion** of the trace — never the starting point. | — |
| 2 | **01-NODE-DAG.md** | The DAG as a deliverable artifact. Includes the canonical diagram AND a pointer to the machine-readable `nodes.yaml`. Documents node adjacency, edge semantics (forward artifact / feedback / consultative), and bottlenecks. | §1 (derivation must produce the candidate node set first) |
| 3 | **02-NODE-SPECS.md** | Per-node spec sheet. Each node: core task / I/O contract / AIGC transformation point / traditional anchor / first-principles defense link / corpus citation link. This is the densest, longest section. | §1 + §2 (specs apply to derived nodes only) |
| 4 | **03-CORPUS-TRACEABILITY.md** | The 102-book → node coverage matrix. For each node: which books inform it, which chapter/concept, with a "coverage strength" rating. For each book: which nodes it informs, with a "source relevance" rating. Bidirectional. | §3 (specs name the corpus anchors; this section back-links them) |
| 5 | **04-LLM-CREATIVE-DISTILLATION.md** | Standalone deep-dive (user explicitly required as separate dimension). Covers: definition of creativity in narrative, the self-consistency check mechanism, LLM distillation prompt strategy, fail modes, evaluation hooks. Not node-specific — it is a horizontal concern that cuts across nodes. | §1 (must align with the first-principles definition of what AI can/can't do) |
| 6 | **05-COMPARISON-VS-8-PHASES.md** | Non-binding delta analysis vs kais-movie-agent's existing 8 phases. Output: coverage map (which new nodes are covered, partially covered, missing), with **recommendation framework** (parallel-run / cutover / per-node refactor) — not an implementation plan. | §2 + §3 (must compare derived nodes against existing phases) |
| 7 | **06-COMPARISON-VS-26-SKILLS.md** | Non-binding mapping vs hermes-agent's 26 movie-experts. Output: node → skill(s) coverage map, skill gap identification (nodes with no skill), skill redundancy identification (multiple skills per node), recommendation framework (merge / split / rename / relocate) — non-binding. | §2 + §3 (must compare derived nodes against existing skills) |
| 8 | **07-HANDOFF-PLAN.md** | Dual-repo handoff contract. For each downstream repo: (a) what they receive, (b) what they're expected to produce in their own future milestone, (c) what's strictly out of scope, (d) versioning & living-doc governance pointer. | All prior sections (handoff depends on all artifacts being stable) |
| 9 | **nodes.yaml** + **edges.yaml** + **corpus-trace.yaml** | Machine-readable canonical schema (see §2 below). Single source of truth that the markdown sections render from. | §1-§4 |

### Additional Sections the Brief Did Not Mention (Recommended)

| Additional Section | Why Needed |
|--------------------|-----------|
| **08-GOVERNANCE.md** | Living-doc rules. Required because the design will evolve. Documents: when a node addition requires explicit re-derivation; when an AIGC transformation update requires showing marginal value delta; review cadence; who has authority to merge changes; changelog format. |
| **09-OPEN-QUESTIONS.md** | Known unknowns that the design cannot resolve within this milestone. Forces honest gap-reporting rather than papering over ambiguity. Feeds forward into the downstream repos' research phases. |
| **10-CHANGELOG.md** | Append-only change log for the design itself (NOT the downstream repos). Every node addition / spec revision / corpus-link update gets a dated entry. This is the audit trail the milestone brief asks for in §6. |

### Physical Location in Repo

**Recommended:** `.planning/research/v2-pipeline-design/`

Rationale:
- The milestone's `.planning/research/` is the natural research output location. The v1 research files already live there.
- A subdirectory (rather than flat files) keeps the v2 design artifacts grouped and makes the handoff contract easier to reference ("see `.planning/research/v2-pipeline-design/`") without polluting the existing 5 research files.
- Alternative considered: `.planning/milestones/v2-design/` — rejected because the v2 milestone is not yet archived (per STATE.md, status is `planning`) and the design IS the research output of the milestone, not a post-hoc archive.

### Structure Rationale Summary

- **00-FIRST-PRINCIPLES first** because every later section is downstream of it. Reading the design top-to-bottom must mirror the reasoning path.
- **Node specs (02) and corpus trace (03) interleaved by reference, not by duplication** — the spec sheet cites corpus anchors by ID; the traceability matrix back-links to nodes. This avoids the v1 mistake of duplicating the related_skills adjacency list in multiple places.
- **LLM creative distillation (04) as a peer section, not embedded in node specs** — it is a horizontal concern (cuts across multiple nodes) and the user explicitly called it out as an independent insight layer.
- **Comparisons (05, 06) come AFTER derivation** because the design is supposed to ignore the existing 8 phases and 26 skills when deriving. Comparing too early contaminates the first-principles pass.
- **Handoff plan (07) last among markdown sections** because it requires every prior artifact to be stable. Handing off a half-derived node set is worse than useless.
- **YAML/JSON schema files (09) underlie markdown** — the markdown renders FROM the schema, never the reverse. Single source of truth.

---

## 2. Node DAG Representation (Format Decision)

### Alternatives Considered

| Option | Pro | Con | Verdict |
|--------|-----|-----|---------|
| **A. Markdown table only** | Maximum human readability; no tooling | Not machine-parseable; handoff requires manual transcription; graph operations (reachability, cycle detection) impossible | Insufficient |
| **B. Mermaid diagram only** | Renders as a visual graph in GitHub/most MD viewers; widely understood syntax | Not all consumers render Mermaid; hard to encode per-node metadata (I/O contracts, AIGC points); weak for diffing | Insufficient alone |
| **C. YAML schema only** | Full structure; machine-parseable; diff-friendly; can encode arbitrary metadata | Hostile to derivation review (a YAML file doesn't tell the story of WHY a node exists) | Insufficient alone |
| **D. Custom JSON schema** | Same as YAML plus stricter validation | Verbose; comments require out-of-band mechanism; less readable in PR diffs than YAML | Rejected — YAML with `#` comments wins |
| **E. **RECOMMENDED: Hybrid — YAML canonical + Mermaid render + Markdown spec** | **Single source of truth (YAML) → machine-derivable → renders to Mermaid (visual) + Markdown (prose). Three audiences, one source.** | Requires a small generator (10-50 lines Python or Node) to render Mermaid + Markdown from YAML. **This generator is the only "code" allowed in this design-only milestone** — it is a developer tool, NOT shipped to downstream consumers. | **CHOSEN** |

### Chosen Format: Hybrid (YAML canonical + Mermaid render + Markdown spec)

**Why hybrid wins:**

1. **The downstream consumers need both.** kais-movie-agent needs to programmatically diff "new nodes vs existing 8 phases" — that requires structured data, not prose. hermes-agent skills team needs to discuss "should this node map to `cinematographer` or split into two skills?" — that requires prose, not JSON. Hybrid serves both.

2. **The first-principles derivation is fundamentally prose.** A YAML file cannot capture the reasoning trace that defends a node's existence. The prose spec is where the defense lives; the YAML is the indexable, machine-checkable summary.

3. **Reviewability.** A PR that adds a node touches one YAML entry (canonical), regenerates the Mermaid + Markdown (mechanical), and the human reviewer reads the Markdown spec section to evaluate the derivation. The YAML diff makes "what changed" obvious; the Markdown diff is the human-readable consequence.

4. **Versionability.** YAML diffs cleanly in git. Mermaid + Markdown are generated artifacts — their diffs are noisy but they are derived, not authored.

### Canonical YAML Schema (`nodes.yaml`)

```yaml
# Canonical node schema. Single source of truth.
# Markdown sections (01-NODE-DAG.md, 02-NODE-SPECS.md) render FROM this file.
schema_version: 1
milestone: v2.0-PRFP
last_updated: 2026-06-16

nodes:
  - id: story_kernel_mining           # snake_case, stable identifier
    name: Story Kernel Mining          # human-readable
    name_cn: 故事内核挖掘               # bilingual
    phase_category: pre_production     # one of: pre_production / production / post_production / distribution / cross_cutting
    derivation_anchor:                 # link back to first-principles section
      section: "00-FIRST-PRINCIPLES.md#why-mine-a-kernel-before-style"
      one_line_defense: >
        The viewer ultimately receives a story, not a style. Mining a resonant
        kernel before locking style prevents aesthetic-first work that lacks
        emotional payload.
    core_task: >
      Extract the smallest narrative unit (Story Kernel) that carries the
      emotional/thematic payload the audience will ultimately receive.
    io_contract:
      consumes:
        - artifact: user_intent_brief
          schema_ref: schemas/user-intent-brief.json   # optional
          from: user_or_upstream_node
      produces:
        - artifact: story_kernel.json
          schema_ref: schemas/story-kernel.json
          consumed_by: [style_definition, screenplay_draft, hook_design]
    aigc_transformation:
      point: extraction-and-compression
      mechanism: >
        LLM compresses multi-source inputs (audience signal, social strata
        analysis, theme) into a 1-paragraph Story Kernel.
      marginal_value: >
        Reduces 2-4 hours of human thematic brainstorming to ~10 minutes of
        LLM-assisted extraction + human review.
      fail_modes:
        - "Hallucinated resonance: LLM invents social-strata connection not supported by input"
        - "Compression loss: 1-paragraph kernel drops the irreducible tension"
    traditional_anchor:
      source_type: book                # book / paper / interview / platform_guide
      corpus_ids: ["Andrew-formalism", "Bazin-realism", "Field-screenplay"]
      chapter_or_concept: "主题陈述 / Premise"
      human_practice: >
        Traditional screenwriting doctrine requires a one-sentence premise
        before any scene is written (Field, McKee).
    corpus_trace:                       # see §4 below — back-links the traceability matrix
      strong: ["-017-Field", "-019-McKee", "-021-Bourdieu"]
      supporting: ["-031-Bazin", "-032-Tarkovsky"]
    first_principles_pass: true         # governance flag — has this node been derived, not copied?
    status: derived                     # derived / proposed / under_review / accepted
    review_gates: [derivation, corpus_citation, aigc_justification]
```

**Schema design principles:**

- `id` is stable and snake_case. Downstream consumers MUST treat it as opaque identifier.
- `derivation_anchor.section` makes the first-principles defense **machine-checkable** (governance lint can verify every node has a non-empty anchor).
- `corpus_trace` uses corpus IDs (book IDs from `_shared/project-corpus/README.md` index), not free text — so the traceability matrix can be cross-validated.
- `review_gates` enumerates which validations have passed. Governance rule: a node cannot move from `proposed` to `accepted` without all three gates passing.
- `io_contract.consumes.artifact` and `produces.artifact` use kebab-case artifact names. These become the vocabulary of `edges.yaml`.

### Canonical Edge Schema (`edges.yaml`)

```yaml
schema_version: 1
edges:
  - from: story_kernel_mining
    to: style_definition
    type: forward_artifact              # forward_artifact / feedback_loop / consultative / audit
    artifact: story_kernel.json
    rationale: >
      Style must serve the kernel; defining style first risks aesthetic without
      emotional anchor.
  - from: hook_design
    to: screenplay_draft
    type: feedback_loop                 # bidirectional
    artifact: hook_rewrite_notes.json
    rationale: >
      Hook design and screenplay iterate — hooks require rewrite opportunities
      and screenplay drafts surface new hook placement points.
```

**Edge types are deliberately constrained to 4 values** so downstream consumers can reason about them:
- `forward_artifact` — linear pipeline step
- `feedback_loop` — bidirectional iteration
- `consultative` — optional cross-cutting consultation (Phase 8 theory_critic pattern)
- `audit` — parallel verification (continuity / script_auditor pattern)

### Mermaid Rendering

Generated from `nodes.yaml` + `edges.yaml` by a 30-line script. Three views:

1. **Pipeline view** (topological, phase_category-grouped) — answers "what runs when"
2. **Feedback view** (only `feedback_loop` + `audit` edges) — answers "where does iteration happen"
3. **Corpus coverage view** (nodes colored by corpus_trace.strong count) — answers "which nodes have weak literary backing"

Mermaid is the *rendered* layer; the canonical graph is in YAML.

### Markdown Spec Section (02-NODE-SPECS.md)

Each node gets a ~150-300 word block, generated from the YAML entry but **augmented with prose** the YAML cannot carry:

```markdown
## Node: Story Kernel Mining (故事内核挖掘)

**Status:** derived · **Phase:** pre-production · **First-principles defense:** [see §00#why-mine-a-kernel]

### Core Task

[Prose expansion of `core_task`. 2-3 sentences. This is where the design argues
WHY this task exists as a discrete node, not a sub-step of another node.]

### I/O Contract

**Consumes:** user_intent_brief (from user or upstream)
**Produces:** story_kernel.json — consumed by [style_definition, screenplay_draft, hook_design]

[Artifact schema reference: `schemas/story-kernel.json`]

### AIGC Transformation

[Prose expansion. Includes the fail modes inline with mitigation notes.
Crucially: this section must answer "what does the AI do that the human
couldn't do faster manually?" If the answer is "nothing," the node shouldn't
exist as an AIGC node.]

### Traditional Anchor

[Prose explanation of which traditional craft step this node corresponds to.
Cites corpus IDs. Argues that the AIGC transformation is a *compression* of
the traditional step, not a *substitution*. Substitution nodes require extra
justification — the design should be skeptical of any node that claims to
fully replace human craft.]

### Coverage Strength

**Corpus:** 3 strong citations, 2 supporting. Coverage: STRONG.
If coverage is WEAK (0-1 strong citations), flag for follow-up.
```

### Why not just Mermaid in markdown

Mermaid is good for **visualization** but bad for **diff, machine-query, and metadata**. The handoff contract requires downstream consumers to ask questions like "list all nodes with corpus coverage < 2 strong citations" — that is a 5-line query against YAML, and a multi-minute grep against rendered Mermaid.

### Why not a real graph DB / D2 / Graphviz

Overkill. The node count is in the 10-25 range (per PROJECT.md: "minimal necessary node set"). YAML + Mermaid handles this trivially. Graphviz would be a defensible alternative for the rendered layer if Mermaid's layout becomes cramped, but Mermaid is rendered natively by GitHub and most MD viewers — Graphviz requires an external rendering step.

---

## 3. Integration Strategy with movie-experts Skills (Non-Binding Handoff)

This is a **handoff contract, not a refactor plan**. The design produces recommendations; the skills team's future milestone decides whether to act on them.

### Mapping Format (`skills-mapping.yaml`)

The design emits a structured mapping file in `.planning/research/v2-pipeline-design/skills-mapping.yaml`:

```yaml
schema_version: 1
binding: non_binding_recommendation      # HARD constraint — never auto-applied
last_updated: 2026-06-16

mappings:
  - node_id: story_kernel_mining
    candidate_skills:
      - skill_id: creative_source
        coverage: primary               # primary / partial / adjacent / none
        rationale: >
          creative_source already mines Story Kernel from 6 social strata.
          This node is essentially a re-statement of creative_source's core task.
        recommendation: align           # align / merge / split / rename / relocate / new
        confidence: high
      - skill_id: style_genome
        coverage: adjacent
        rationale: >
          style_genome defines 5D style vectors, not kernels. Adjacency only.
        recommendation: none
        confidence: high

  - node_id: scene_assembly             # hypothetical example
    candidate_skills:
      - skill_id: scene_builder
        coverage: partial
        rationale: >
          scene_builder covers spatial/3D scene construction but NOT the
          storyboard-to-render handoff this node requires.
        recommendation: split_or_extend
        confidence: medium
        gap_note: >
          Gap: no current skill owns the "storyboard JSON → rendered still"
          transition cleanly. character_designer + drawer overlap but neither
          owns it.
```

### Skill Gap Identification

For each node where all `candidate_skills` have `coverage: none` or `partial`, the mapping emits a `gap_note`. Aggregated gap report (generated section in 06-COMPARISON-VS-26-SKILLS.md):

```markdown
## Skill Gaps (Nodes Without Clean Skill Coverage)

| Node | Closest Skill | Gap | Recommendation |
|------|---------------|-----|----------------|
| scene_assembly | scene_builder, character_designer, drawer (3 partial) | No skill owns the storyboard→render transition | Either extend scene_builder OR create new skill `scene_assembler` |
```

### Skill Redundancy Identification

For each node where 2+ skills have `coverage: primary`, the mapping flags redundancy. The v1 26-skill suite has known overlaps (per the v1 README DAG: `cinematographer` ↔ `scene_builder` ↔ `storyboard_designer` all touch spatial framing). The design surfaces these but **does not force consolidation** — that's the skills team's call.

### Recommendation Framework

| Recommendation | When to Emit | What It Means |
|----------------|--------------|---------------|
| `align` | Skill already matches node cleanly | No action needed; just confirm alignment |
| `extend` | Skill covers most of node but missing 1-2 facets | Add references / metrics to existing skill |
| `merge` | 2+ skills redundantly cover one node | Consider consolidating (skills team decides) |
| `split` | One skill covers parts of 2+ nodes | Consider decomposing (skills team decides) |
| `rename` | Skill name misleads about its role | Cosmetic |
| `relocate` | Skill is in wrong category | Cosmetic |
| `new` | No skill covers node at all | New skill needed (skills team decides priority) |
| `none` | Skill is unrelated to node | No recommendation |

**Hard rule:** All entries carry `binding: non_binding_recommendation`. The design document NEVER claims "skill X must be renamed" — it says "the mapping suggests rename; skills team to decide in their own milestone."

### Handoff Ceremony

When the design is finalized:

1. `skills-mapping.yaml` is committed to `.planning/research/v2-pipeline-design/`.
2. The 06-COMPARISON-VS-26-SKILLS.md section is generated from it.
3. A pointer is added to `skills/movie-experts/README.md` (Phase 9 of the design milestone): "Future skills reorganization should consult `.planning/research/v2-pipeline-design/skills-mapping.yaml`".
4. **No skill files are touched.** The skills team opens their own milestone when ready.

---

## 4. Integration Strategy with kais-movie-agent (Non-Binding Handoff)

Same pattern as §3 — non-binding contract, but the downstream consumer is a different repo with its own `.planning/`.

### Mapping Format (`kais-migration-matrix.yaml`)

The design emits:

```yaml
schema_version: 1
binding: non_binding_recommendation
last_updated: 2026-06-16

phase_mappings:
  - design_node_id: story_kernel_mining
    existing_phase:                    # kais-movie-agent's existing 8 phases
      - phase_id: 1_requirement
        coverage: partial
        rationale: >
          Existing Phase 1 (需求确认) captures surface requirements but does
          NOT do Story Kernel mining. Kernel mining is a deeper upstream step.
      - phase_id: 2_art_direction
        coverage: none
    lib_module_mapping:                # kais-movie-agent/lib/*.js
      - module: lib/1st-director.js
        coverage: partial
        rationale: >
          1st-director.js produces 四维蓝图 — adjacent to kernel but not the
          same artifact.
      - module: lib/ai-scorer.js
        coverage: none
    migration_recommendation: extend_phase_1
    migration_rationale: >
      Cheapest path: extend existing Phase 1 to include kernel mining, rather
      than adding a new phase that breaks the 8-phase rhythm. New helper
      module `lib/kernel-miner.js` would slot under Phase 1.
    migration_cost_estimate: medium    # small / medium / large
    confidence: medium
```

### Phase Mapping (Existing 8 Phases vs New Nodes)

The existing 8 phases (per V2-REFACTOR-PLAN.md and INTEGRATION.md) are:

```
1. requirement → 2. art-direction → 3. character → 4. scenario
  → 5. voice → 6. storyboard → 7. scene → 8. camera
  → (post-production implied)
```

(V8-ARCHITECTURE.md says there's also a 20-step pipeline variant. The design treats both as "existing" — non-binding either way.)

For each new design node, the migration matrix answers:
- **Coverage:** which existing phase(s) already do this work?
- **Gap:** what's missing?
- **Migration path:** `extend_phase_N` / `add_new_phase` / `split_phase_N` / `parallel_run` / `cutover`
- **Cost:** small (config change) / medium (new lib module) / large (new phase + pipeline restructure)

### Migration Strategy Framework

| Strategy | When to Recommend | Risk |
|----------|-------------------|------|
| `parallel_run` | New node is orthogonal to existing flow (e.g., theory_critic consultation) | Low — no existing flow disrupted |
| `per_node_refactor` | New node maps to extending one existing phase | Low — isolated change |
| `cutover` | New node fully replaces an existing phase (e.g., if first-principles derivation eliminates a phase) | High — must run both during transition |
| `phase_reorder` | New node requires moving an existing phase (e.g., audio-before-storyboard per V2-REFACTOR-PLAN change #2) | Medium — affects downstream contracts |
| `add_new_phase` | New node has no existing counterpart | Low if additive; medium if it changes total count |

**Hard rule:** The design does NOT prescribe which strategy to use. It enumerates the trade-offs. The kais-movie-agent team's future milestone decides.

### Handoff Ceremony (kais-movie-agent side)

1. `kais-migration-matrix.yaml` is committed in **hermes-agent** (design lives here).
2. A short pointer README is added at the top of the matrix: "This file is a non-binding handoff to kais-movie-agent. kais-movie-agent's team should copy or reference this file into their own `.planning/` when they open the migration milestone."
3. The handoff plan section (07-HANDOFF-PLAN.md) explicitly states: "kais-movie-agent is a separate repo. This design does NOT modify kais-movie-agent/lib/* or kais-movie-agent/skills/*. Migration is a future milestone owned by that repo."
4. **No kais-movie-agent files are touched from this milestone.**

---

## 5. Build Order for Design Deliverables (Phase Decomposition)

This is the **internal** build order for THIS milestone (the design work itself), not the downstream implementation order.

### Dependency DAG (Critical Path Analysis)

```
Phase A: First-Principles Derivation
   │
   │ (produces: candidate node set as output)
   ▼
Phase B: Node DAG + Per-Node Spec      ───┐
   │                                       │
   │ (depends on: Phase A's node set)      │
   ▼                                       │
   ├─── Phase C: 102-Book Corpus Trace ────┤  (Phase C can start in parallel
   │    (depends on: Phase B's node ids)   │   once Phase B has node IDs,
   │                                       │   even before B's specs finalize)
   │                                       │
   ▼                                       │
Phase D: LLM Creative Distillation Deep-Dive  (depends on Phase A's definition
   │                                       │     of "what AI can/can't do";
   │                                       │     otherwise independent)
   │                                       │
   ▼                                       │
Phase E: Cross-Comparisons + Handoff Plan ◄┘  (depends on B + C + D all stable)
   │
   ▼
Phase F: Governance + Open Questions + Changelog  (finalization)
```

### Phase-by-Phase Breakdown

| Phase | Deliverable | Depends On | Blocks | Parallelizable? | Est. Effort |
|-------|-------------|------------|--------|-----------------|-------------|
| **A** | `00-FIRST-PRINCIPLES.md` | — | B, D | No (everything waits on this) | Large (this is the hardest intellectual work) |
| **B** | `01-NODE-DAG.md` + `02-NODE-SPECS.md` + `nodes.yaml` + `edges.yaml` | A | C, E | Partially — once A produces candidate node IDs, B can begin; B's specs can be refined in parallel with C | Large |
| **C** | `03-CORPUS-TRACEABILITY.md` + `corpus-trace.yaml` | B (node IDs only — does not need full specs) | E | YES — full parallel with B-spec-finalization and D | Medium (mechanical mapping against 102-book index) |
| **D** | `04-LLM-CREATIVE-DISTILLATION.md` | A (definition of AI limits) | E | YES — full parallel with B and C | Medium |
| **E** | `05-COMPARISON-VS-8-PHASES.md` + `06-COMPARISON-VS-26-SKILLS.md` + `skills-mapping.yaml` + `kais-migration-matrix.yaml` + `07-HANDOFF-PLAN.md` | B + C + D all stable | F | No — depends on all prior | Medium |
| **F** | `08-GOVERNANCE.md` + `09-OPEN-QUESTIONS.md` + `10-CHANGELOG.md` + `README.md` (final) | E | — | No | Small |

### Critical Path

```
A → B → E → F
```

Phases C and D run alongside B. Phase A is the bottleneck — nothing else starts until the first-principles pass produces a candidate node set.

### Why Phase A Cannot Be Parallelized

PROJECT.md is explicit: "节点设计从 0 推". Every other section is a consequence of the derivation. If B, C, D start before A's candidate node set exists, they will be reworking against a moving target — guaranteed rework cost.

### Why Phase C (Corpus Trace) CAN Start Before B Finishes

C only needs the **node IDs and one-line descriptions**, not the full specs. As soon as Phase A produces a candidate node list, C can begin mapping each node ID to corpus books. If B later refines a node's spec, C's mapping for that node may need minor adjustment — but the bulk of the work is already done.

### Why Phase D (LLM Distillation) Is Independent

D is a horizontal concern. It depends on Phase A's definition of what AI can/cannot do (which is part of the first-principles pass), but it does not depend on any specific node. Once A's "AI limits" section is drafted, D can run in full parallel with B and C.

### Recommended Build Order

```
Week 1: Phase A (full focus — no parallel work)
Week 2: Phase B (primary) + Phase C (parallel, kicks off once node IDs exist) + Phase D (parallel)
Week 3: Phase B finalization + Phase C finalization + Phase D finalization
Week 4: Phase E (cross-comparisons + handoff) — requires B+C+D stable
Week 5: Phase F (governance + open questions + README) — finalization
```

**Hard rule:** No phase begins before its dependencies are stable. "Stable" means: committed to `.planning/research/v2-pipeline-design/` with a CHANGELOG entry, not "drafted in someone's head."

---

## 6. Traceability + Audit Trail

Each node must be defensible from three angles:
1. **First-principles defense** — Why does this node exist? (answered in §00)
2. **Traditional anchor** — Which traditional craft step does it compress or replace? (answered in §02 spec, with corpus citation)
3. **AIGC justification** — What does AI do here that the human couldn't do faster? (answered in §02 spec)

### Encoding (Machine-Readable)

Every node entry in `nodes.yaml` MUST have non-empty:

```yaml
derivation_anchor:
  section: "00-FIRST-PRINCIPLES.md#<anchor>"
  one_line_defense: "..."
corpus_trace:
  strong: [...]                        # MUST have ≥1 entry for accepted status
  supporting: [...]
aigc_transformation:
  marginal_value: "..."                # MUST be non-empty
  fail_modes: [...]                    # MUST have ≥1 entry
review_gates: [derivation, corpus_citation, aigc_justification]
status: derived | proposed | under_review | accepted
```

### Encoding (Human-Readable)

Each node's spec section in `02-NODE-SPECS.md` opens with three tagged lines:

```markdown
## Node: <Name> (<CN Name>)

**🅰 First-principles:** [link to §00 anchor] — [one-line defense]
**📚 Traditional anchor:** [corpus IDs] — [one-line human-practice summary]
**⚡ AIGC justification:** [one-line marginal value statement]
```

These three lines are the audit trail at-a-glance. A reviewer can scan the entire 02-NODE-SPECS.md in 60 seconds and identify any node missing one of the three defenses.

### Governance Lint (Developer Tool)

A 30-line Python script (the only "code" in this milestone) validates:

```python
# .planning/research/v2-pipeline-design/scripts/validate_design.py
def validate(nodes_yaml_path: str):
    nodes = yaml.safe_load(open(nodes_yaml_path))
    failures = []
    for node in nodes["nodes"]:
        if node["status"] == "accepted":
            if not node.get("derivation_anchor", {}).get("section"):
                failures.append(f"{node['id']}: missing derivation_anchor")
            if not node.get("corpus_trace", {}).get("strong"):
                failures.append(f"{node['id']}: missing corpus strong citation")
            if not node.get("aigc_transformation", {}).get("marginal_value"):
                failures.append(f"{node['id']}: missing AIGC marginal value")
            if "derivation" not in node.get("review_gates", []):
                failures.append(f"{node['id']}: derivation gate not passed")
            # ... etc
    return failures
```

This script runs as a pre-commit hook in `.planning/research/v2-pipeline-design/`. It does NOT run in either downstream repo.

### Audit Trail for Reviewers

When a reviewer questions "why does node X exist?", the audit path is:

1. Open `02-NODE-SPECS.md`, find node X
2. Click the `🅰 First-principles` link → jumps to the derivation section in §00
3. Read the prose defense
4. If unsatisfied, check `📚 Traditional anchor` corpus IDs → opens `_shared/project-corpus/README.md` for source-book metadata
5. If still unsatisfied, check `⚡ AIGC justification` — is the marginal value real or hand-wavy?
6. If still unsatisfied, the node should be `status: under_review`, not `accepted`

This is the "future implementers (and reviewers) can sanity-check any node" requirement from the brief.

---

## 7. Living-Doc Governance Rules

The design will evolve after this milestone closes. Downstream repos will surface gaps. New corpus books may be added. The 102-book corpus itself will get corrections.

### Hard Governance Rules

| Rule | Trigger | Required Action |
|------|---------|-----------------|
| **G1: Node addition requires re-derivation** | A new node is proposed | The proposing PR MUST add an entry to §00-FIRST-PRINCIPLES.md defending the node from first principles. A node without a derivation section cannot be merged. |
| **G2: Node deletion requires impact analysis** | An existing `accepted` node is proposed for removal | The PR MUST enumerate (a) which downstream nodes consume its output artifact, (b) what the migration path is for each consumer. |
| **G3: AIGC transformation update requires marginal-value delta** | The `aigc_transformation.marginal_value` of a node is changed | The PR MUST show the old vs new marginal value statement and explain what changed (new model capability? new fail mode discovered?). Cosmetic edits to wording don't trigger this; substantive edits do. |
| **G4: Corpus citation change requires source verification** | A `corpus_trace.strong` entry is added/removed | The PR MUST cite the specific book ID + chapter from `_shared/project-corpus/README.md`. Fabricated citations block the PR. |
| **G5: Status transitions require all gates** | A node moves between `proposed` → `under_review` → `accepted` | Each transition requires the corresponding `review_gates` to be checked. `accepted` requires all three gates (`derivation`, `corpus_citation`, `aigc_justification`) to pass. |
| **G6: Edge type changes require contract update** | An edge's `type` changes (e.g., `forward_artifact` → `feedback_loop`) | The PR MUST update the I/O contracts of both endpoints — feedback loops require both endpoints to declare bidirectional artifact exchange. |
| **G7: All changes logged in CHANGELOG.md** | Any PR touching the design | Append-only entry in `10-CHANGELOG.md` with date, node/edge/corpus ID affected, and one-line description. |

### Review Cadence

| Cadence | Activity |
|---------|----------|
| **Per PR** | Governance lint runs (G1-G7) |
| **Per downstream consumer milestone close** | The downstream repo (hermes-agent skills OR kais-movie-agent) opens an issue in this design doc's repo when their milestone reveals a design gap. Design maintainers triage — is it a node missing? a spec ambiguity? a corpus gap? |
| **Quarterly** | Full design review: re-walk §00 to confirm the first-principles assumptions still hold (especially the "what AI can/can't do" section — model capabilities drift fast). |
| **Per new corpus book** | When a new book is added to `_shared/project-corpus/`, design maintainers check whether any node's `corpus_trace` should be updated. |

### Authority Model

| Role | Authority |
|------|-----------|
| Design maintainer (this milestone's owner) | Approves PRs to the design doc. Sole authority over §00 (first-principles). |
| Hermes skills team | Consults on §06 (skills mapping). Can object to a recommendation; cannot unilaterally change it. |
| kais-movie-agent team | Consults on §05 (phase mapping). Same constraint. |
| Anyone | Can open issues proposing changes. PRs require design maintainer approval. |

### Versioning

The design doc uses semantic-ish versioning:

- **Major** (`v2 → v3`): First-principles derivation substantially revised; node set changed by >30%.
- **Minor** (`v2.0 → v2.1`): New node added or existing node spec substantially revised.
- **Patch** (`v2.0.0 → v2.0.1`): Corpus citation update, edge type clarification, typo fix.

Version lives in `nodes.yaml` `schema_version` + a top-level `design_version` field. CHANGELOG entry per change.

---

## Component Boundaries (This Milestone's Deliverable Artifacts)

| Component | Responsibility | Format | Consumed By |
|-----------|----------------|--------|-------------|
| `00-FIRST-PRINCIPLES.md` | Epistemic anchor; Musk-style derivation | Markdown prose | All other sections; reviewers; downstream consumers doing traceability audits |
| `nodes.yaml` | Canonical node schema (single source of truth) | YAML | Renderers (Mermaid, Markdown); governance lint; downstream consumers |
| `edges.yaml` | Canonical edge schema | YAML | Renderers; downstream consumers |
| `corpus-trace.yaml` | Bidirectional book↔node mapping | YAML | Renderer for `03-CORPUS-TRACEABILITY.md`; governance lint |
| `01-NODE-DAG.md` | Human-readable DAG overview + Mermaid renders | Markdown (generated) | Reviewers; downstream teams |
| `02-NODE-SPECS.md` | Per-node spec with 3-line audit header per node | Markdown (mostly generated, prose-augmented) | Reviewers; downstream teams |
| `03-CORPUS-TRACEABILITY.md` | Coverage matrix in prose form | Markdown (generated from YAML) | Reviewers; corpus maintainers |
| `04-LLM-CREATIVE-DISTILLATION.md` | Horizontal deep-dive on LLM creativity | Markdown prose (hand-authored) | All node spec authors; reviewers |
| `05-COMPARISON-VS-8-PHASES.md` | Non-binding delta vs kais-movie-agent phases | Markdown (generated from `kais-migration-matrix.yaml`) | kais-movie-agent team's future milestone |
| `06-COMPARISON-VS-26-SKILLS.md` | Non-binding mapping vs hermes skills | Markdown (generated from `skills-mapping.yaml`) | hermes skills team's future milestone |
| `07-HANDOFF-PLAN.md` | Dual-repo handoff contract | Markdown prose | Both downstream teams |
| `08-GOVERNANCE.md` | Living-doc rules (G1-G7) | Markdown prose | All future contributors |
| `09-OPEN-QUESTIONS.md` | Known unknowns | Markdown | Downstream teams' research phases |
| `10-CHANGELOG.md` | Append-only audit log | Markdown | All contributors |
| `README.md` | Entry point | Markdown | Everyone |
| `scripts/validate_design.py` | Governance lint | Python | Pre-commit hook; CI |

---

## Data Flow: How a Design Change Propagates

```
[Author proposes node addition]
    │
    ▼
[1] Author adds node entry to nodes.yaml
    │
    ├─ derivation_anchor.section MUST point to a new anchor in 00-FIRST-PRINCIPLES.md
    │   └─ Author adds that anchor to 00-FIRST-PRINCIPLES.md (G1)
    │
    ├─ corpus_trace.strong MUST have ≥1 entry from corpus-trace.yaml
    │   └─ Author updates corpus-trace.yaml with new book→node mapping (G4)
    │
    ├─ aigc_transformation.marginal_value MUST be non-empty
    │
    └─ status: proposed (cannot be accepted until all 3 review_gates pass)
    │
    ▼
[2] Author runs scripts/validate_design.py
    │
    ├─ PASS → continue
    └─ FAIL → fix issues
    │
    ▼
[3] Author regenerates derived artifacts:
    │   ├─ 01-NODE-DAG.md (Mermaid render)
    │   ├─ 02-NODE-SPECS.md (spec section for new node)
    │   └─ 03-CORPUS-TRACEABILITY.md (matrix row)
    │
    ▼
[4] Author appends to 10-CHANGELOG.md (G7)
    │
    ▼
[5] PR opened. Reviewers check:
    │   ├─ Does the first-principles derivation in §00 actually defend the node?
    │   ├─ Is the corpus citation real (not fabricated)?
    │   ├─ Is the AIGC marginal value non-trivial?
    │   └─ Does the new node break any existing edges/contracts?
    │
    ▼
[6] Design maintainer merges (or rejects with rationale)
    │
    ▼
[7] Downstream consumers (skills team / kais team) see the CHANGELOG entry
    │
    └─ They decide whether to act on it in their own future milestone.
       This design doc does NOT auto-trigger downstream changes.
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Designing the DAG Before the First-Principles Pass

**What people do:** Start by sketching the pipeline graph ("obviously we need a screenplay node, a scene node, ...").
**Why it's wrong:** PROJECT.md is explicit: nodes are derived from first principles, not by analogy to existing pipelines. Skipping the derivation produces a node set that looks reasonable but cannot be defended under scrutiny. When a downstream consumer asks "why does this node exist?", the answer will be "because the existing 8-phase pipeline has one like it" — which is exactly the contamination the milestone is supposed to avoid.
**Do this instead:** Write §00-FIRST-PRINCIPLES.md to completion FIRST. The candidate node set falls out as the conclusion of the reasoning trace, never the starting point.

### Anti-Pattern 2: Authoring Markdown Specs Without Underlying YAML

**What people do:** Write `02-NODE-SPECS.md` directly in markdown, deferring the YAML schema "until later".
**Why it's wrong:** Markdown specs without an underlying canonical schema drift. Two sections start describing the same node differently. Governance lint cannot run ("is every node covered?"). Downstream consumers cannot programmatically query the design. The handoff contract becomes "read 200 pages of markdown" instead of "consume this YAML."
**Do this instead:** YAML first, always. Markdown renders FROM YAML. Prose augmentation happens in the rendered markdown but the canonical fields stay in YAML.

### Anti-Pattern 3: Binding Recommendations to Downstream Repos

**What people do:** The design says "skill X MUST be renamed to Y" or "kais-movie-agent MUST add a new phase."
**Why it's wrong:** This design is non-binding by explicit milestone scope (PROJECT.md: "范围严格收口:本次里程碑交付仅设计文档"). Binding recommendations exceed scope and will be rejected by the downstream teams as overreach. Worse, they short-circuit the downstream teams' own first-principles processes.
**Do this instead:** All recommendations carry `binding: non_binding_recommendation`. Use language like "the mapping suggests," "the design recommends," "downstream team to decide in their own milestone."

### Anti-Pattern 4: One-Shot Derivation Without Iteration

**What people do:** Write §00 in one pass, declare it done, move to §01.
**Why it's wrong:** First-principles derivation is iterative. The candidate node set produced in round 1 will look different after corpus traceability (§3) reveals which nodes have weak literary backing, and after LLM-distillation deep-dive (§4) reveals which AIGC transformations are overstated.
**Do this instead:** Treat §00 as living. Allow it to be revised during Phases B-E. The CHANGELOG captures each revision.

### Anti-Pattern 5: Treating LLM Distillation as a Section Per Node

**What people do:** Embed "how does LLM help this node" inside each node's spec section.
**Why it's wrong:** The user explicitly required this as a separate dimension. The patterns (prompt strategy, self-consistency check, fail modes) are horizontal — they recur across nodes. Duplicating them per-node produces drift and prevents the deep-dive the user asked for.
**Do this instead:** §04-LLM-CREATIVE-DISTILLATION.md is a standalone section. Each node spec has an `aigc_transformation` block that cites §04 patterns by name, not by re-explaining them.

### Anti-Pattern 6: Skipping the Open Questions Section

**What people do:** Paper over ambiguities to make the design look complete.
**Why it's wrong:** Downstream consumers WILL hit those ambiguities in their own milestones. If the design pretended they were resolved, the downstream team wastes time rediscovering them and may distrust the entire design doc.
**Do this instead:** §09-OPEN-QUESTIONS.md is mandatory. Every "we don't know yet" gets an entry. This is honesty, not weakness.

### Anti-Pattern 7: Mixing Design Authority with Implementation Authority

**What people do:** Design maintainer also owns the skills refactor or the kais-movie-agent migration.
**Why it's wrong:** Conflicts of interest. The design maintainer might inflate recommendations to make their own downstream work easier. Or the downstream teams might resent "the design told us what to do."
**Do this instead:** Different people where possible. The design maintainer owns the design doc ONLY. The skills team owns skills. The kais team owns kais-movie-agent. Each party can raise issues on the others' repos, but no one unilaterally changes another's artifacts.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| hermes-agent `skills/movie-experts/` | One-way pointer from design doc to skills README. Design emits `skills-mapping.yaml`; skills team's future milestone reads it. | Design NEVER modifies skill files in this milestone. |
| kais-movie-agent `.planning/` | One-way pointer from hermes-agent design to kais-movie-agent's future milestone. Design emits `kais-migration-matrix.yaml`; kais team copies/refs it. | Design NEVER modifies kais-movie-agent files in this milestone. |
| `_shared/project-corpus/` (102-book index) | Read-only. Design cites corpus IDs from the existing index; does not modify the index. | If design reveals corpus gaps, those become entries in §09-OPEN-QUESTIONS.md, not changes to the corpus. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| §00 (first principles) ↔ §02 (node specs) | Derivation anchor links | §02 cites §00 by anchor; §00 does not know about §02 |
| §02 (specs) ↔ §03 (corpus trace) | Mutual citation via corpus IDs and node IDs | Both reference the same canonical `nodes.yaml` + `corpus-trace.yaml` |
| §02 (specs) ↔ §04 (LLM distillation) | §02's `aigc_transformation` block cites §04 patterns by name | §04 is horizontal; §02 is vertical |
| §02 (specs) ↔ §05 (kais comparison) | §05 maps design nodes to existing phases | One-way derivation: §05 reads §02, never the reverse |
| §02 (specs) ↔ §06 (skills comparison) | §06 maps design nodes to existing skills | One-way derivation: §06 reads §02 |
| All sections ↔ §10 (changelog) | Append-only audit trail | Every substantive change logs to §10 |

---

## Scaling Considerations

| Concern | At 10-15 nodes (expected v2 output) | At 25-30 nodes (hypothetical expansion) | At 50+ nodes (unlikely) |
|---------|--------------------------------------|------------------------------------------|--------------------------|
| YAML reviewability | Single-file review; clear diffs | Consider splitting `nodes.yaml` by phase_category | Mandatory split; index file required |
| Mermaid rendering | Native in GitHub | Mermaid handles up to ~30 nodes; layout becomes dense | Switch to Graphviz or sub-graphs |
| Corpus trace matrix | 10×102 = 1020 cells, fits in one markdown table | 25×102 = 2550 cells, needs grouping | Interactive matrix; static markdown insufficient |
| First-principles defense length | ~3000-5000 words for §00 | ~8000-12000 words; needs sectioning | Likely needs to split into multiple derivation docs |
| Downstream handoff ceremony | Single PR to add pointer in skills README + kais planning | Multiple PRs (per category) | Per-phase ceremonies |

For v2.0 (target: 10-15 nodes per first-principles derivation), the architecture holds without structural changes. The single-YAML-canonical approach is sufficient.

---

## Sources

### Primary (HIGH confidence — direct source reads)

- `/data/workspace/hermes-agent/.planning/PROJECT.md` — milestone v2.0 brief, scope constraints, first-principles directive, dual-repo handoff requirement
- `/data/workspace/hermes-agent/.planning/MILESTONES.md` — v1 close-out context (18 experts shipped, what's deferred)
- `/data/workspace/hermes-agent/.planning/STATE.md` — current v2.0 planning state
- `/data/workspace/hermes-agent/skills/movie-experts/README.md` — 26-skill inventory, production DAG, RAG usage guide (baseline for §6 skills mapping)
- `/data/workspace/kais-movie-agent/README.md` — 8-phase pipeline + lib/ structure + sketch-control sub-pipeline (baseline for §5 kais mapping)
- `/data/workspace/kais-movie-agent/INTEGRATION.md` — V1.0 GPU integration state, 13 functions, LLM migration to hermes-agent
- `/data/workspace/kais-movie-agent/docs/V8-ARCHITECTURE.md` — OpenClaw Agent pure-driver architecture, 20-step pipeline, gold-team direct connection
- `/data/workspace/kais-movie-agent/docs/V2-REFACTOR-PLAN.md` — 7 core changes (AI 熔断 / audio-driven storyboard / character assetization / art-bible lock / preview cutover / on-demand scene / structured 运镜), V2 phase ordering
- `/data/workspace/kais-movie-agent/lib/phases/index.js` — phase handlers + Hermes defaults (shows existing phase IDs and parameter surfaces)
- `/data/workspace/hermes-agent/skills/movie-experts/_shared/project-corpus/README.md` — 102-book corpus index, MinerU conversion path, per-category book counts
- `/data/workspace/hermes-agent/.planning/research/ARCHITECTURE.md` (v1) — 18-expert collaboration DAG, related_skills graph invariants, eval harness structure (informs §6 skills mapping approach)
- `/data/workspace/hermes-agent/.planning/research/SUMMARY.md` (v1) — 15 key findings, recommended build order, phase ordering rationale (informs this milestone's phase decomposition)

### Secondary (MEDIUM-HIGH confidence — codebase observations)

- `ls /data/workspace/kais-movie-agent/lib/` — confirmed 30+ lib modules (1st-director, ai-scorer, asset-bus, prompt-injector, shot-list-parser, etc.) informing the lib-module mapping in §4
- `ls /data/workspace/hermes-agent/skills/movie-experts/_shared/project-corpus/` — confirmed 14 ref files + README + INTEGRATION-REPORT informing corpus traceability approach in §4

### Methodological (HIGH confidence — established practice)

- YAML-as-canonical + Markdown-as-rendered pattern: standard in API spec ecosystems (OpenAPI, AsyncAPI). Verified by direct knowledge — this is the dominant pattern for design docs that need both machine-deriability and human review.
- Mermaid for rendered graph diagrams: native render support in GitHub since 2022. Standard for design docs in markdown-first repos.
- First-principles derivation as design epistemic anchor: aligns with milestone brief's "Musk-style" directive.
- Non-binding handoff contracts: standard pattern for cross-team / cross-repo design handoffs (RFC process in IETF, ADR pattern in software architecture).

---

*Architecture research for: Pipeline Redesign from First Principles (v2.0 PRFP) — design document structure, integration, and build order*
*Researched: 2026-06-16*
