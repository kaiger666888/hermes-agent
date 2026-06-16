# Phase 7: First-Principles Derivation - Context

**Gathered:** 2026-06-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 7 produces `00-FIRST-PRINCIPLES.md` — a Musk-style first-principles derivation trace that walks from irreducible questions to a candidate node set, ending with a 6-pitfall audit checklist. Phase 7 is the **intellectual bottleneck** of milestone v2.0 PRFP: nothing else (Phases 8-12) may begin until Phase 7 emits a defensible candidate node set.

**In scope:**
- The reasoning trace from "what does the audience ultimately receive?" → candidate node IDs
- Per-node `derivation` field, `alternatives-considered` log, `contingent` vs `validated-invariant` classification
- Epistemic-status tags {physical / psychological / platform-algorithmic / tool-capability} on every core claim
- Steelman-the-elimination section per node
- STACK §1.4 corpus subset citation per first-principles question
- 6-pitfall (§1 + §5) Musk-method audit checklist at end of doc
- Pre-mapping of STACK §1.4 corpus subsets per question (up-front, not lazy)
- Musk/Isaacson quote primary-source verification (research sub-phase)
- Candidate node IDs emitted as English kebab-case (e.g., `creative_source`)

**Out of scope (deferred to later phases):**
- Full per-node specs (cost_budget, latency_budget, model_horizon, fail_modes, dependencies) — **Phase 8**
- C1-C7 filter application that compresses candidate set to final DAG — **Phase 8**
- Theory_critic trigger mode / consultative edge declaration — **Phase 8 (META-06)**
- Cost ceiling (¥1000-10000/episode) — **Phase 8 (META-05)**
- 102-book corpus ↔ node bidirectional traceability matrix — **Phase 9**
- LLM creativity definition / consistency mechanism / prompt strategy deep-dive — **Phase 10**
- Cross-comparisons vs 8 phases / 26 skills / dual-repo handoff — **Phase 11**
- Governance rules, validate_design.py lint, README, OPEN-QUESTIONS, CHANGELOG — **Phase 12**

</domain>

<decisions>
## Implementation Decisions

### Node-Count Target
- Target: **8-15 nodes** (PITFALLS §2.6 + ARCHITECTURE scaling table + SUMMARY synthesis)
- Hard ceiling: **≤25 nodes** — any node beyond 15 must carry explicit justification in its `derivation` field
- Emission mode: **Candidate set** — Phase 7 emits a palette, Phase 8 applies C1-C7 filter to compress further to final DAG. Phase 7 does NOT end the derivation debate.
- Re-evaluation: Allowed mid-Phase-7 with audit log entry (if derivation surfaces 16-20 defensible nodes, document why — PITFALLS §2.6 smell-detection alignment)

### First-Principles Question Set
- Count: **4 questions** (the 3 listed in the goal + "what determines 短剧/微电影 quality?" — PROJECT.md mandates this, SUMMARY cites it, PITFALLS §4 leans on it)
- Ordering: **Audience-first** ("what does the audience ultimately receive?" → "what determines quality?" → "what can AI accelerate?" → "what can AI never replace?")
- Creativity question: **Deferred to Phase 10** — Phase 7 establishes AI-limits boundary (can/cannot replace), Phase 10 deep-dives on creativity within that boundary
- Corpus subsets: **Pre-mapped in Phase 7 plan** — each question gets its STACK §1.4 corpus subset declared up-front, preventing corpus-blind derivation

### Musk Quote Primary-Source Verification
- Verification depth: **Run research sub-phase in Phase 7** — `gsd-plan-phase --research-phase 7` per SUMMARY §"Research Flags". HIGH research load is flagged; prevents first-principles theater (citing a misremembered quote undermines the entire methodology canon)
- Authoritative sources: **Isaacson 2023 biography + Kevin Rose 2012 Foundation interview** — both flagged in SUMMARY as primary
- Contradiction handling: **Update the derivation trace to reflect verified wording** — derivation must survive quote correction
- Aristotle + TRIZ canon: **Spot-check only** — Aristotle φυσικαὶ ἀρχαί is well-attested in standard translations; TRIZ 40-principles coverage is IEEE-verified per SUMMARY

### Bilingual Policy for `00-FIRST-PRINCIPLES.md`
- Language strategy: **EN structure + CN prose** — consistent with v1 SKILL.md policy + META-03; CN terminology preserved (汉字 alongside gloss per PITFALLS 6.4); rationale and explanatory prose in CN
- Methodology canon terminology: **Bilingual** — key terms paired (e.g., "第一性原理 / first principles", "物理还原 / physical reduction"); CN-primary readers can still access the canon
- Node IDs: **English kebab-case** (e.g., `creative_source`, `script_auditor`) — matches Phase 8 YAML canonical schema; matches v1 expert_id convention; CN display name optional per-node
- Prose tone: **Technical but accessible** — must be readable end-to-end per SC-1; CN prose for clarity, formal where rigor demands

### Claude's Discretion
- Exact section ordering within the doc (intro → question set → corpus map → derivation trace → candidate node set → audit checklist → conclusion is one suggested skeleton, but Claude may reorganize for logical flow)
- How to present the alternatives-considered log (inline per node vs appendix table) — as long as it's machine-detectable for DERIV-05 verification
- Audit checklist presentation format (inline at end of `00-FIRST-PRINCIPLES.md` vs separate `00-AUDIT.md` appendix) — inline recommended to keep reasoning chain in one file, but appendices are acceptable if the audit is referenced from the main body
- Diagrams (Mermaid reasoning-tree) — optional but useful; place near top of derivation trace

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Research artifacts (read-only input):**
  - `.planning/research/STACK.md` — corpus physical locations verified by `ls`; §1.4 maps first-principles questions to corpus subsets; §4 documents Musk + Aristotle + TRIZ methodology canon; §5 lists 8 LLM-story-gen references
  - `.planning/research/PITFALLS.md` — §1 + §5 enumerate the 6 Musk-method failure modes Phase 7 must audit against; §"Top 5 Critical Risks" ranks first-principles theater as #1
  - `.planning/research/FEATURES.md` — 41-candidate palette (Phase 7 selects 8-15 from this); C1-C7 selection criteria (Phase 8 applies filter, Phase 7 just emits candidates)
  - `.planning/research/ARCHITECTURE.md` — Phase A decomposition (which Phase 7 implements); YAML-canonical schema definition (Phase 8 inherits, but Phase 7 should produce node IDs compatible with it)
  - `.planning/research/SUMMARY.md` — synthesizes all 4 research files; resolves 5 cross-file conflicts; flags HIGH research load for Phase 7
- **v1 PROJECT.md + REQUIREMENTS.md** — milestone context, 4-decision carryover (node count / cost ceiling / authorship / theory_critic trigger / bilingual — first 4 fall outside Phase 7 scope, last one is in scope as bilingual policy above)
- **v1 RETROSPECTIVE** — Key Lesson 7 (SUMMARY ↔ README drift) is the small-scale preview of design-impl drift Phase 11 must address; informs Phase 7's structural rigor

### Established Patterns
- **SKILL.md YAML frontmatter + bilingual body** — v1 18-expert corpus demonstrates EN structure + CN prose pattern; Phase 7 should follow the same convention for `00-FIRST-PRINCIPLES.md` body (META-03)
- **Per-node `derivation` field precedent** — STACK §4 documents the Musk-method derivation structure; FEATURES §4 node schema includes `rationale_for_existence`; Phase 7's `derivation` field extends this
- **Epistemic-status tagging** — NEW pattern for v2.0 (no v1 precedent); DERIV-03 mandates the 4-tag taxonomy
- **Steelman-the-elimination** — NEW pattern; DERIV-04 mandates one paragraph per node

### Integration Points
- **Phase 7 output → Phase 8 input**: Candidate node IDs (English kebab-case) flow into `nodes.yaml` canonical schema; per-node `derivation` + `alternatives-considered` + `contingent-vs-validated-invariant` fields carry forward into per-node specs
- **Phase 7 output → Phase 9 input**: Candidate node IDs enable corpus-traceability bidirectional matrix (node → corpus AND corpus → node)
- **Phase 7 output → Phase 10 input**: "What AI can/cannot do" definition (the 4th question's answer) seeds Phase 10's creativity boundary
- **Phase 7 audit checklist → Phase 12 governance**: The 6-pitfall audit becomes a re-derivation trigger rule (GOV-01 G1: "node addition requires re-derivation")

</code_context>

<specifics>
## Specific Ideas

- **Readers should be able to challenge every step** — Phase 7 success criterion #1 mandates no logical jumps. The doc should read like a proof: every step defends itself.
- **No "obviously" / no "every pipeline has this"** — PITFALLS §1 warning signs; explicit reject list for the derivation prose
- **Steelman-the-elimination is structural, not optional** — every node has a paragraph stating the strongest "this node shouldn't exist" argument AND a response. If the response is weak, the node should be reconsidered.
- **Alternatives-considered log per node** — at least one alternative node considered and rejected per slot (DERIV-02 + DERIV-05); rejected alternatives are evidence the derivation is not ex-post justification
- **Musk primary-source verification must happen before citations land in the doc** — if the verification sub-phase finds a paraphrase is wrong, the derivation trace gets updated; do not cite-then-verify
- **Output location** (META-04): `.planning/research/v2-pipeline-design/00-FIRST-PRINCIPLES.md` — inside hermes-agent/.planning/, not cross-repo

</specifics>

<deferred>
## Deferred Ideas

- **Phase 7 should also produce a separate executive summary** — no, README is Phase 12 GOV-03 deliverable; Phase 7 produces only the derivation doc (plus the audit checklist section within it)
- **Phase 7 should sketch the DAG** — no, Phase 8 NODE-05 declares DAG (YAML + Markdown + Mermaid); Phase 7 emits node IDs and per-node derivation, NOT the DAG itself
- **Phase 7 should pre-define theory_critic trigger** — no, META-06 is Phase 8; Phase 7 only establishes that AI-limits exist (the "cannot replace" answer sets the boundary, not the trigger)
- **Phase 7 should pick specific AI models** — no, that's premature model-commitment (PITFALLS §1.3); Phase 8 capability-spec canonical layer handles this with dated annex
- **Phase 7 should produce `01-NODE-DAG.md`** — no, that's Phase 8 deliverable per ARCHITECTURE §5

</deferred>

