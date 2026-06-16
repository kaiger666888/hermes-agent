# Research — Phase 7: First-Principles Derivation

**Phase:** 7 — First-Principles Derivation (v2.0 PRFP bottleneck)
**Researched:** 2026-06-16 (in main agent, per /goal directive)
**Confidence:** HIGH (synthesizes existing v2.0 research files + 3 targeted WebSearches)
**Scope:** What the planner needs to know to PLAN Phase 7 well — methodology canon verification, Musk-method failure-mode audit prompts, structural deliverable shape, validation strategy.

> **Key finding:** STACK.md (§4) and PITFALLS.md (§1+§5) already contain ~80% of what Phase 7 needs. The remaining 20% — steelman methodology, ADR alternatives-considered format, epistemic-taxonomy precedents — is filled in below via targeted WebSearch. The planner can plan confidently without further research.

---

## Executive Frame

Phase 7 produces **one deliverable**: `.planning/research/v2-pipeline-design/00-FIRST-PRINCIPLES.md` — a Musk-style derivation log that walks from 4 irreducible questions to a candidate node set, with explicit structural rigor (per-node derivation, epistemic tags, steelman-elimination, alternatives log, contingent-vs-validated-invariant classification, 6-pitfall audit).

The planner needs to know:
1. **Methodology canon verification** — are the Musk/Aristotle/TRIZ citations in STACK §4 sufficiently verified for the derivation doc to cite them?
2. **6-pitfall audit prompts** — what specific audit questions does DERIV-08's checklist need to walk?
3. **Steelman-the-elimination methodology** — what is it, where does it come from, how is it applied per-node?
4. **Alternatives-considered log format** — which ADR template (Nygard vs MADR) fits per-node logs?
5. **Epistemic-status taxonomy validation** — is {physical, psychological, platform-algorithmic, tool-capability} a recognized standard, or project-defined?
6. **Corpus subset pre-mapping** — which corpus clusters answer each of the 4 first-principles questions?
7. **Validation strategy** — what does "verification" mean for a derivation doc (no code)?

Each section below answers one of these questions with concrete guidance for the planner.

---

## 1. Methodology Canon Verification (HIGH confidence — primary sources cited)

STACK §4.1 + §4.2 already cites the methodology canon with primary-source URLs. The verification work for Phase 7 is **citation hygiene**, not fresh research:

### Musk first-principles (PRIMARY)
| Source | Status | Citation form recommended for `00-FIRST-PRINCIPLES.md` |
|---|---|---|
| **Kevin Rose Foundation interview (2012)** | cited in STACK §4.1 with primary URL `kevinrose.com` + James Clear synthesis URL | *"I tend to approach things from a physics framework. Physics teaches you to reason from first principles rather than by analogy."* — Musk to Kevin Rose, Foundation Series #3, 2012 |
| **Isaacson biography *Elon Musk* (2023)** | cited in STACK §4.1 with Wikipedia + Graham Mann + Lex Fridman transcript URLs | Reference by chapter (battery-cost reduction, SpaceX reusability) rather than page — Simon & Schuster pagination varies by edition |
| **Musk YouTube explainer** | cited in STACK §4.1 | *"The First Principles Method Explained by Elon Musk"* — leap innovation framing |

**Verification finding:** Primary sources are accessible via the URLs already in STACK §4.1. The CONTEXT.md decision (Area 3/4) recommended running `--research-phase` to verify exact wording before citing. Since STACK already gives us the primary URLs and the project's bibliographic convention is "cite source + date, not exact page", **Phase 7 can proceed using STACK §4.1 citations directly** with this discipline:
- Mark any Musk paraphrase as `[paraphrased; primary: Kevin Rose 2012 / Isaacson 2023 ch. N]` in-line
- Reserve direct quotation marks for the canonical Musk quotes already in STACK §4.1
- Do NOT invent new Musk quotes — only quote what STACK §4.1 already quotes

This satisfies DERIV-08 (avoid first-principles theater) without a separate research sub-phase.

### Aristotle φυσικαὶ ἀρχαί (PRIMARY)
| Source | Status | Citation form recommended |
|---|---|---|
| *Physics* Book I, ch. 1 (Hardie & Gaye translation) | cited in STACK §4.2 with Logos Virtual Library URL | *"The natural way of doing this is to start from the things which are more knowable and obvious to us and proceed towards those which are clearer and more knowable by nature; for it is not the same thing to be knowable to us and knowable without qualification."* — Aristotle, *Physics* I.1, 184a16-22 |
| *Metaphysics* Book Δ (Delta) | cited in STACK §4.2 with MIT classics URL | Reference Stanford Encyclopedia for the synthesis |
| Stanford Encyclopedia entry | cited in STACK §4.2 | Use as secondary synthesis |

**Key Aristotle insight for the derivation:** The distinction between "more knowable to us" (analogy, the familiar) and "more knowable by nature" (foundational truth) IS the philosophical root of Musk's "first principles vs analogy". Phase 7 should cite this distinction explicitly — it grounds the methodology canon in 2,400 years of philosophical tradition rather than a 2012 podcast.

### TRIZ (SECONDARY; spot-check only)
| Source | Status |
|---|---|
| Altshuller 40 inventive principles | cited in STACK §4.2 with TRIZ40.com URL |
| IEEE "20 of 40 cover 75%" claim | cited in STACK §4.2 with IEEE document URL |

**TRIZ applicability to Phase 7:** LOW. TRIZ is a contradiction-resolution tool for node-design (Phase 8) when trade-offs surface. Phase 7 produces candidate node IDs — TRIZ doesn't shape the derivation. **The planner should not include TRIZ tasks in Phase 7 plans.**

---

## 2. The 10 Musk-Method Failure Modes (DERIV-08 Audit Checklist)

DERIV-08 success criterion says "walk the 6 PITFALLS §1 + §5 Musk-method failure modes". Reading PITFALLS.md carefully, **§1 has 6 failure modes and §5 has 4 failure modes = 10 total**. The "6" in the success criterion is loose — the safer interpretation is "all failure modes in §1 + §5 relevant to derivation-record phase". The Pitfall-to-Phase Mapping in PITFALLS §"Top 5 Critical Risks" assigns all §1 and §5 pitfalls to the derivation-record phase, so the audit checklist should walk all 10.

### Category 1 — First-Principles Misapplication (6 failure modes)

| # | Failure mode | Audit prompt for `00-FIRST-PRINCIPLES.md` |
|---|---|---|
| **1.1** | "First principles" as decorative language (no actual decomposition) | Does any node's `derivation` field read "every pipeline has this"? Does the derivation section length exceed or match the node-description section? Does the word "obviously" appear anywhere in justifications? |
| **1.2** | Ignoring existing knowledge as "bias" when it is validated practice | Does the derivation explicitly preserve validated invariants (Murch Rule of Six, 180° axis, three-act structure) as `validated-invariant` rather than `contingent`? Are at least one corpus-anchor reference cited per node? |
| **1.3** | Premature optimization for current-gen models (Sora/Kling/Veo) | Do any candidate node IDs contain model-specific terms (e.g., `sora_video_gen`)? Are node IDs expressed at the user-value layer (e.g., `composition_lock`) or the model layer? (Node IDs should be model-agnostic in Phase 7; capability-spec layer comes in Phase 8.) |
| **1.4** | "Different from existing" mistaken for "better than existing" | Does the derivation log include a convergence-log? For each node where the new DAG agrees with kais-movie-agent V8, is the agreement justified? (Convergence log is Phase 11 deliverable, but Phase 7 derivation must NOT celebrate divergence as proof of correctness — flag this in audit.) |
| **1.5** | "I derived this from physics" fallacy — reasoning by analogy in disguise | Does every derivation claim tag its epistemic status as one of {physical, psychological, platform-algorithmic, tool-capability}? Are platform-dependent or tool-dependent claims flagged as `volatile`? |
| **1.6** | Reverse-engineering the desired answer into "first principles" | Does every node carry a steelman-the-elimination paragraph (the strongest "this node should NOT exist" argument + response)? Are alternatives-considered logs present and substantive (not "no alternatives considered")? |

### Category 5 — Musk-Method-Specific (4 failure modes)

| # | Failure mode | Audit prompt for `00-FIRST-PRINCIPLES.md` |
|---|---|---|
| **5.1** | Booster-reuse story misapplied — "reuse is always cheaper" | Does any node derive its existence from "reusability" as a universal principle? Cost-driver identification per node (compute? human time? latency?) — is this field populated? (Phase 8 fills cost_budget; Phase 7 emits node IDs that hint at cost-driver class.) |
| **5.2** | Battery-cost story misapplied — "decompose to materials" doesn't work for craft | Does the derivation try to sum constituent costs per node? Are cross-node coherence invariants (style, identity, continuity) treated as first-class value drivers in the derivation, not side-effects? |
| **5.3** | Twitter/X pricing story misapplied — "challenge the assumption" is not "ignore the data" | Are core assumptions classified as `contingent` vs `validated-invariant`? Are validated-invariants (180° axis, perceptual invariants) preserved without extraordinary evidence? |
| **5.4** | Musk himself warns about "first principles theater" | Does the derivation explicitly mark which nodes are `analogy-valid` (existing film pipeline applies directly) vs `analogy-breaks-here` (deep first-principles derivation required)? Is deep derivation applied only to the latter? |

### Audit checklist presentation format (recommendation)

The audit checklist should be a section at the END of `00-FIRST-PRINCIPLES.md`, structured as:

```markdown
## §6 — Musk-Method Audit Checklist

> Per DERIV-08, this section walks the 10 Musk-method failure modes from PITFALLS §1 + §5 and shows how this derivation avoids each.

### 1.1 "First principles" as decorative language
- **Audit prompt:** Does any node's derivation read "every pipeline has this"?
- **This derivation's answer:** [paragraph showing the structural rigor — per-node derivation, no "obviously", etc.]
- **Verdict:** PASS / FAIL / CONDITIONAL

### 1.2 Ignoring existing knowledge as "bias"
...

[Continue for all 10]
```

Inline (within `00-FIRST-PRINCIPLES.md`) is recommended over a separate audit file, because (a) SC-1 mandates end-to-end readability, (b) the audit IS part of the reasoning chain (verifying the derivation rigor), and (c) Phase 12 GOV-02 lint can still grep for the audit section by header.

---

## 3. Steelman-the-Elimination Methodology (NEW — synthesized from WebSearch)

### Definition and origin

**Steelmanning** = the deliberate practice of constructing the strongest possible version of an opposing argument before engaging with or refuting it. The opposite of strawmanning. Roots in:

1. **Principle of Charity** (philosophy) — named by **Neil L. Wilson in 1958-59**. Requires interpreting a speaker's statements in their most rational form.
2. **Paul Graham's Disagreement Hierarchy** (2008, "How to Disagree" essay) — 7 levels, top = "Refuting the Central Point" requires steelmanning first. Graham: refutation is "the rarest [form of disagreement] because it's the most work".

### Application to Phase 7 (per-node steelman-the-elimination)

For EACH candidate node in `00-FIRST-PRINCIPLES.md`, the derivation must include a steelman-the-elimination paragraph structured as:

```markdown
### Node X — Steelman-the-elimination

**The strongest case for removing this node:** [state the strongest argument
that this node should NOT exist — e.g., "in an AIGC pipeline, the storyboard
node could be absorbed into the shot-generation prompt as a transient internal
artifact; persisting it as a separate node adds pipeline complexity without
user-visible value"]

**Response:** [explain why the node survives this challenge — e.g., "the
storyboard persists because (a) current gen models need explicit visual
references that the prompt alone cannot internalize (tool-capability
constraint), (b) human review seam for art-direction approval exists at this
layer, (c) reusability across shots via consistent framing is a value driver"]

**Verdict:** SURVIVES / RECONSIDER / MERGE
```

If the response is weak, the node should be flagged `RECONSIDER` or `MERGE` — this is the structural mechanism that prevents Pitfall 1.6 (reverse-engineering desired answers).

### Format recommendation

Inline per-node is preferred over a separate steelman-log file, for the same reason as the audit checklist (SC-1 end-to-end readability). The `## §6` audit checklist section can include a summary table of all node verdicts; the per-node paragraphs live in the per-node derivation sections.

### Sources

- [Paul Graham — "How to Disagree"](https://www.paulgraham.com/disagree.html) — disagreement hierarchy
- [Wikipedia — Principle of Charity](https://en.wikipedia.org/wiki/Principle_of_charity) — Neil L. Wilson 1958-59 origin
- [LessWrong — "Better Disagreement"](https://www.lesswrong.com/posts/FhH8m5n8qGSSHsAgG/better-disagreement) — steelmanning × Graham hierarchy integration
- [Discourse Magazine — "Now More Than Ever, We Need Steel-Manning"](https://www.discoursemagazine.com/p/now-more-than-ever-we-need-steel-manning)

---

## 4. Alternatives-Considered Log Format (NEW — ADR format comparison)

### The choice: Nygard ADR vs MADR

Phase 7 must produce a per-node alternatives-considered log (DERIV-05). Two established templates:

| Aspect | **Nygard ADR** (2011) | **MADR** (Markdown ADR, Zimmermann et al.) |
|---|---|---|
| Origin | Michael Nygard, Cognitect blog post | Olaf Zimmermann et al., evolved from Nygard + Y-Statements |
| Fields | Title, Context, Decision, Status, Consequences | Title, Status, Context, Decision, **Considered Options (with pros & cons)**, Consequences, Compliance, Quality Goals |
| Alternatives-considered | Implicit (mentioned in narrative) | **Explicit dedicated field with pros/cons per option** |
| Relationship | Base format | **Superset** of Nygard — every Nygard ADR is a valid MADR |

### Recommendation: MADR-style per-node alternatives log

Per-node alternatives-considered log should use **MADR's "Considered Options" structure** because:
1. DERIV-05 requires "at least one node considered and rejected for this slot" — MADR's explicit options field enforces this structurally
2. PITFALLS 1.6 (reverse-engineering desired answers) is mitigated by the explicit pros/cons per option
3. PITFALLS 7.4 (missing rationale) is mitigated by MADR's "Decision Drivers" + "Compliance" fields

### Per-node alternatives log format (recommendation)

```markdown
### Node X — Alternatives considered

**Slot this node fills:** [what role in the DAG this node occupies]

**Considered options:**
1. **`<chosen_node_id>`** (CHOSEN) — [one-line description]
   - Pros: [what this option does well]
   - Cons: [what this option costs]
2. **`<rejected_alt_1>`** (REJECTED) — [one-line description]
   - Pros: [what this option does well]
   - Cons: [why rejected — concrete failure mode]
3. **`<rejected_alt_2>`** (REJECTED — optional) — [one-line description]
   - Pros: ...
   - Cons: ...

**Decision driver:** [why option 1 won — references first-principles answer that motivates this slot]
```

### Sources

- [The Markdown ADR (MADR) Template Explained and Distilled — Olaf Zimmermann](https://ozimmer.ch/practices/2022/11/22/MADRTemplatePrimer.html)
- [About MADR — official repository](https://adr.github.io/madr/)
- [Architecture Decision Records: Templates and Operational Patterns](https://hidekazu-konishi.com/entry/architecture_decision_records_templates_and_operations.html) — confirms "MADR is a superset of Nygard"
- [CEUR Workshop Proceedings — Markdown ADR Format and Tool Support](https://ceur-ws.org/Vol-2072/paper9.pdf) — academic comparison

---

## 5. Epistemic-Status Taxonomy Validation (NEW — project-defined, no clean standard)

### The 4-tag taxonomy in scope

`{physical, psychological, platform-algorithmic, tool-capability}` per DERIV-03.

### WebSearch finding

**No established epistemological framework maps cleanly to this 4-tag taxonomy.** Closest precedents:
- Heritage & Raymond (conversation analysis): epistemic status vs epistemic stance — but applied to conversational turn-taking, not design-doc claims
- Bayesian epistemology: distinguishes prior/posterior/likelihood — not volatility-oriented
- General "physical certitude" (Philosophy Institute): one dimension among many, not a 4-tag taxonomy

### Conclusion: project-defined taxonomy (defensible)

The 4-tag taxonomy is **project-defined** for this milestone. It is defensible because:
1. **It maps cleanly to the volatility ladder** that AIGC design needs to track:
   - `physical` — perceptual invariants (180° axis, light direction). Stable across centuries.
   - `psychological` — human-nature contingent but stable (attention decay, emotional response). Stable across decades.
   - `platform-algorithmic` — platform-specific (抖音 completion-rate weighting). Volatile, quarters-to-years.
   - `tool-capability` — current gen-model limits (LoRA identity lock). Volatile, months-to-quarters.
2. **It aligns with Musk's "validated-invariant vs contingent" distinction** (PITFALLS 5.3): `physical` and `psychological` map roughly to `validated-invariant`; `platform-algorithmic` and `tool-capability` map to `contingent`.
3. **No framework is a better fit** — applying Bayesian or conversation-analysis frameworks would require translation overhead that obscures the design intent.

### Phase 7 recommendation

The derivation doc should:
1. **State explicitly in the intro** that this is a project-defined taxonomy, not a standard one. Cite the volatility ladder.
2. **Map each tag to the contingent-vs-validated-invariant classification** in the per-node fields.
3. **Note in OPEN-QUESTIONS.md (Phase 12)** that future work could compare this taxonomy against formal epistemological frameworks — but for this milestone, project-defined is sufficient.

### Sources

- [Heritage & Raymond — Questions and Epistemic Stance (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/S2215039018300444) — closest prior art (epistemic status vs stance)
- [Stanford Encyclopedia — Reliabilist Epistemology](https://plato.stanford.edu/entries/reliabilism/) — alternative framework (rejected)
- [Nova Spivack — Epistemology and Metacognition in AI](https://www.novaspivack.com/technology/ai-technology/epistemology-and-metacognition-in-artificial-intelligence-defining-classifying-and-governing-the-limits-of-ai-knowledge) — adjacent AI-epistemology work

---

## 6. Per-Question Corpus Subset Pre-Mapping (HIGH confidence — STACK §1.4)

STACK §1.4 already provides the per-question corpus subset mapping. Phase 7 should USE this directly, not re-derive. Summary:

| First-principles question | Primary corpus subset (STACK §1.4) | Secondary corpus subset |
|---|---|---|
| **Q1: What does the audience ultimately consume?** | `01-剧本/` (narrative intent) + `06-理论批评/{cinema-fundamentals, film-philosophy-bazin, film-philosophy-tarkovsky}` (what cinema IS) + book 劳逊《戏剧与电影的剧作理论与技巧》 | `case-studies/case-01-短片创作全流程.md` |
| **Q2: What determines 短剧/微电影 quality?** | `04-后期/{editing-by-murch-rules, editing-rhythm-pacing, color-grading-strategy, final-mix, sound-layering-design}` + `03-拍摄/{cinematographer-masterclass, lighting-design, color-narrative-analysis}` | `02-分镜/{cinematic-language-grammar, mise-en-scene-blocking}` |
| **Q3: What can AI actually accelerate?** | NOT directly in 102-book corpus. Infer from `04-后期/` (which post tasks are most procedural?) + `03-拍摄/animation-production.md` + `05-制片/budget-allocation.md` (which human tasks are most expensive?). Pair with kais-movie-agent V8 architecture docs. | Hermes `_shared/project-corpus/` + STACK §5 LLM-story-gen refs |
| **Q4: What can AI never replace?** | `06-理论批评/{film-philosophy-bazin, film-philosophy-tarkovsky, formalism-vs-realism}` (irreducible creative intent) + `01-剧本/{adaptation-writing, character-arc-design, dialogue-crafting}` (creative voice) + `03-拍摄/{acting-stanislavski-stella, actor-direction}` (performance truth) | Book 麦基《故事》, 芦苇剧本笔记 |

**Important caveat from STACK §1.4:** Question "Why do short dramas live or die in the first 3 seconds?" is **NOT in the 102-book corpus** (corpus is feature-film oriented). Phase 7's Q2 ("what determines 短剧/微电影 quality?") must therefore pair the corpus with v1's `hook_retention/references/three-second-hooks.md` and external 短剧-specific sources. This is a Phase 9 (corpus-traceability) deliverable, but Phase 7 should flag the gap.

### Hermes-integrated corpus (ready to cite without re-mining)

Per STACK §2.2, **9 of 12 `skills/movie-experts/_shared/project-corpus/` ref files are concentrated enough to support Phase 7 derivation directly**:
- Theory root: `theory-formalism-vs-realism.md` + `film-philosophy-bazin-tarkovsky.md` + `narrative-revolution-and-modernism.md` — answers Q1 + Q4
- Craft execution: `cinematography-masterclass-and-grammar.md` + `lighting-equipment-and-design.md` + `editing-sound-post.md` + `animation-disney-system.md` — answers Q2 + Q4
- Producing: `production-chinese-and-low-budget.md` — answers Q3 (resource constraints)

3 refs need supplementation for v2.0 (flagged in STACK §2.2):
- `screenwriting-chinese-and-supplementary.md` — underweights 短剧-specific screenwriting (pair with v1 `screenplay/references/cn-shortdrama.md`)
- `psychoanalytic-film-theory.md` — does not cover 短剧-specific retention craft (pair with v1 `hook_retention/` 4 refs)
- AIGC marginal-value analysis — NO ref covers this; must infer from craft-execution refs + kais V8 architecture

---

## 7. Contingent vs Validated-Invariant Classification (HIGH confidence — from PITFALLS 5.3)

Per PITFALLS 5.3, every node's core assumptions must be classified as `contingent` (a choice someone made — fair to question) vs `validated-invariant` (an empirical regularity — questioning requires extraordinary evidence).

### Phase 7 application

For each candidate node, the derivation must include:

```markdown
### Node X — Assumption classification

**Core assumptions:**
- `validated-invariant`: [e.g., "180° axis rule applies because audience spatial orientation is a perceptual invariant"]
- `validated-invariant`: [e.g., "human attention decays within first 5-7 seconds for low-trust content"]
- `contingent`: [e.g., "storyboard persists as a separate artifact (could be transient if gen model accepts visual refs directly)"]
- `contingent`: [e.g., "human review happens at this seam (could be automated if critic rubric matures)"]
```

### Cross-reference to epistemic-status tags

`validated-invariant` typically maps to `physical` or `psychological` tags.
`contingent` typically maps to `platform-algorithmic` or `tool-capability` tags.
But the mapping is not 1:1 — a `psychological` claim can be `contingent` if it depends on a specific audience demographic. The two classifications serve different audit purposes (volatility vs. mutability).

---

## 8. Deliverable Structure — `00-FIRST-PRINCIPLES.md` Skeleton

Synthesizing DERIV-01..08 + the research above, the planner should expect this skeleton:

```markdown
# 00 — First-Principles Derivation: kais-movie-agent v2.0 Pipeline Node Set

> **Document status:** design-2026-06-16-prfp · supersedes: none · superseded_by: TBD
> **Phase:** 7 of v2.0 PRFP milestone · **Authors:** hermes-agent design team
> **Audience:** kais-movie-agent impl team + hermes-agent skills team + future design maintainers

## §0 — Reading guide (1 page)
[How to read this doc; what each section does; what's stable vs evolving]

## §1 — Methodology frame (1-2 pages)
- What is "Musk-style first principles" (cite Kevin Rose 2012, Isaacson 2023)
- Aristotle's "more knowable by nature" root (cite Physics I.1)
- The 4-tag epistemic-status taxonomy (project-defined, map to volatility)
- The contingent-vs-validated-invariant classification
- Steelman-the-elimination discipline (cite Wilson 1958, Graham 2008)

## §2 — The four first-principles questions + corpus pre-mapping (2-3 pages)
### Q1: What does the audience ultimately consume?
- Sub-question decomposition
- STACK §1.4 corpus subset citation (primary + secondary)
- Epistemic-status tags for the answer's core claims
- First-principles answer (CN prose, EN terms)

### Q2: What determines 短剧/微电影 quality?
[same structure]

### Q3: What can AI actually accelerate?
[same structure]

### Q4: What can AI never replace?
[same structure]

## §3 — Derivation trace (5-10 pages — the bulk)
- Walk from Q1+Q2+Q3+Q4 answers through intermediate conclusions to candidate node IDs
- Each derivation step tagged with epistemic-status
- No "obviously", no jumps from analogy to conclusion
- Diagrams (Mermaid reasoning-tree) where helpful

## §4 — Candidate node set (2-4 pages)
- The 8-15 candidate node IDs (English kebab-case) with:
  - one-line core task
  - derivation field (defends existence from first principles)
  - alternatives-considered log (MADR-style ≥1 rejected option)
  - assumption classification (contingent vs validated-invariant)
  - epistemic-status tags on core claims
  - steelman-the-elimination paragraph
  - corpus anchor (≥1 STACK §1.4 or Hermes-corpus reference)
  - analogy-validity field (analogy-valid / analogy-breaks-here)

## §5 — Node-count audit (0.5 page)
- Final count vs 8-15 target
- If >15, justification per node beyond target
- Hard-ceiling check (≤25)

## §6 — Musk-method audit checklist (2-3 pages)
- Walks all 10 failure modes from PITFALLS §1 + §5
- Each: audit prompt + this derivation's answer + verdict

## §7 — Open questions surfaced (0.5-1 page)
- Honest list of unresolved questions, feeding Phase 12 OPEN-QUESTIONS.md
- Not "what we couldn't derive" but "what this derivation revealed as research gaps"

## References
- Primary sources (Musk, Aristotle, TRIZ, Wilson, Graham)
- STACK §1-5 corpus + canon references
- Hermes project-corpus refs cited inline
```

### Length estimate

~15-25 pages total. The derivation trace (§3) + candidate node set (§4) should be ~60-70% of the doc; methodology + audit + open questions ~30-40%. If §3+§4 < §1+§2+§6 combined, that's a Pitfall 1.1 warning sign (first-principles theater).

---

## 9. Validation Architecture

### Nyquist validation: NOT applicable

Phase 7 produces design documents, not code. Nyquist validation (which requires real-environment test signals at twice the frequency of the phenomenon) doesn't apply — there is no observable runtime behavior to sample.

### What "verification" means for Phase 7

**Structural lint** — automated checks on `00-FIRST-PRINCIPLES.md` structure:
- Every candidate node has `derivation`, `alternatives-considered`, `assumption-classification`, `epistemic-status`, `steelman-elimination`, `corpus-anchor`, `analogy-validity` fields populated
- No node's `derivation` field contains forbidden phrases ("every pipeline has", "obviously", "traditionally")
- Every claim in §3 (derivation trace) has an epistemic-status tag
- §6 audit checklist covers all 10 failure modes
- Candidate node count is in [8, 25]

**Manual verification** (Phase 12 GOV-02 lint):
- The full `scripts/validate_design.py` (~30 lines) is a Phase 12 deliverable. Phase 7's job is to produce a doc that PASSES that lint, not to write the lint itself.

### Recommendation for Phase 7 plans

Phase 7 plans should:
1. NOT include `scripts/validate_design.py` (Phase 12 deliverable)
2. Include a manual "structural self-audit" task at the end of execution (run a checklist against the doc before declaring complete)
3. Treat verification as: a human reviewer can read `00-FIRST-PRINCIPLES.md` end-to-end and confirm the success criteria DERIV-01..08 hold

### VALIDATION.md artifact

Per the plan-phase workflow §5.5, a VALIDATION.md template exists. For Phase 7, the validation strategy is "structural lint + manual end-to-end readability check" — the VALIDATION.md should record this so the planner can encode it in plan acceptance criteria.

---

## 10. Bilingual Policy Implementation

CONTEXT.md decision (Area 4/4) locked: **EN structure + CN prose**, English kebab-case node IDs. Implementation guidance for `00-FIRST-PRINCIPLES.md`:

| Element | Language |
|---|---|
| Section headers (## §0, ## §1, ...) | English |
| Field labels (derivation, alternatives-considered, ...) | English kebab-case |
| Body prose (rationale, explanations, derivations) | Chinese (CN-primary), with English terms preserved where canonical |
| Methodology canon terms | Bilingual paired (e.g., "第一性原理 / first principles") |
| Node IDs | English kebab-case (e.g., `creative_source`, `script_auditor`) — NO Chinese IDs |
| Musk/Aristotle/TRIZ quotations | Original English with CN translation following in parentheses |
| Corpus citations (book titles) | Chinese 汉字 + English gloss in parentheses if available |
| Audit checklist | English structure, CN prose explanations |

This matches v1 SKILL.md policy (META-03) and avoids YAML canonical layer issues (PITFALLS §3.5 — node IDs are machine-processed; non-ASCII breaks tooling).

---

## Research Gaps Flagged (feed Phase 12 OPEN-QUESTIONS.md)

The research is HIGH confidence but flags 3 gaps that honest derivation should record:

1. **Musk quote primary-source pagination** — STACK §4.1 gives URLs but not exact page numbers from Isaacson 2023 (Simon & Schuster). If a downstream consumer challenges a specific quote, the design doc should be honest: "cited from chapter context, not page number; verify against edition". (Does NOT block Phase 7; record in OPEN-QUESTIONS.md for Phase 12.)

2. **Platform-specific volatility classification** — PITFALLS 5.3 says 抖音 algorithmic weighting is `platform-algorithmic` (volatile), but some platform conventions may be `psychological` (stable, e.g., attention decay in first 3 seconds). Phase 7's Q2 ("what determines 短剧/微电影 quality?") derivation must make case-by-case judgments; document the rationale per claim.

3. **Theory_critic trigger mode** — META-06 (Phase 8) declares "创作者手动拉". Phase 7 establishes that AI-limits exist (Q4 answer) but does NOT design the trigger mechanism. Don't accidentally specify trigger conditions in Phase 7.

---

## Summary for the Planner

**The planner can confidently write Phase 7 plans knowing:**
1. **One deliverable:** `.planning/research/v2-pipeline-design/00-FIRST-PRINCIPLES.md` (~15-25 pages, EN structure + CN prose, English kebab-case node IDs)
2. **8 requirements to cover:** DERIV-01..08 (see REQUIREMENTS.md)
3. **Methodology canon:** Use STACK §4 citations directly (no fresh research needed)
4. **Per-question corpus subsets:** Use STACK §1.4 mapping directly
5. **10-pitfall audit:** Walk all 10 in §6, with the audit prompts above
6. **Per-node fields:** derivation + alternatives-considered (MADR-style) + assumption-classification (contingent vs validated-invariant) + epistemic-status + steelman-elimination + corpus-anchor + analogy-validity
7. **Target node count:** 8-15 candidate (Phase 8 applies C1-C7 filter for final DAG)
8. **Verification:** structural self-audit + manual end-to-end readability check (NOT Nyquist; NOT automated tests)
9. **Language:** EN structure + CN prose, English kebab-case IDs (META-03 + CONTEXT.md Area 4/4)
10. **Location:** `.planning/research/v2-pipeline-design/00-FIRST-PRINCIPLES.md` (META-04)
11. **No code:** Phase 7 produces ZERO code; `scripts/validate_design.py` is Phase 12 deliverable
12. **No SKILL.md edits:** META-01 forbids touching hermes-agent/skills/movie-experts/
13. **No kais-movie-agent edits:** META-02 forbids touching kais-movie-agent/

**Plan count estimate:** 3-4 plans, all in Wave 1 (Phase 7 is bottleneck; no parallelism within the phase):
- Plan A: Methodology frame + corpus pre-mapping (§0-§2)
- Plan B: Derivation trace (§3) — the bulk
- Plan C: Candidate node set with full per-node rigor (§4-§5)
- Plan D: Musk-method audit + open questions + references (§6-§7)

(Or 3 plans if §4+§5 fold into §3's tail, or 5 plans if §1+§2 split.) The planner decides based on context-budget considerations.

