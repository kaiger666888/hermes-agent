# Pitfalls Research — v2.0 PRFP (Pipeline Redesign from First Principles)

**Domain:** First-principles derivation of a new AIGC film-pipeline node set, delivered as DESIGN DOCS (no implementation). Dual-repo: design in hermes-agent, impl later in kais-movie-agent.
**Researched:** 2026-06-16
**Confidence:** HIGH (grounded in v1 RETROSPECTIVE + actual PROJECT.md v2.0 scope + Musk/Isaacson method critique + AIGC pipeline literature)
**Scope note:** This milestone ships ONLY design docs. Every pitfall below is a way the *design work itself* can fail — producing a doc that, when later implemented, will waste effort or break. Phases must prevent these *during design*, not during a future implementation.

---

## Summary

This milestone has **seven compounding failure dimensions** that the v1 retrospective did not have to face, because v1 was content work inside one repo. v2.0 PRFP is *derivation work across two repos with no executable validation* — so the dominant risks are epistemic (bad reasoning), not technical (broken code). The single largest delivery risk is **first-principles theater**: producing a doc that *sounds* like Musk-style derivation but is actually analogy + vibes dressed in reductionist language, which is worse than honest intuition because it feels unchallengeable. The second-largest risk is **design-impl drift**: a beautiful doc that the kais-movie-agent team silently re-derives from scratch because the handoff is unreadable or out of date by the time they pick it up.

---

## Category 1 — First-Principles Misapplication (the headline risk for this milestone)

The user explicitly invoked "Musk first-principles". This category is where the milestone earns or loses its name. Each failure mode below is concrete and specific to film/AIGC pipeline design — not generic engineering philosophy.

### Pitfall 1.1: "First principles" as decorative language (no actual decomposition)

**What goes wrong:** The design doc uses the phrase "from first principles" in the intro and then proceeds by listing nodes that *feel right* with post-hoc justifications ("this is essential because every film needs a script"). The actual derivation step — "what is irreducible about a short-drama pipeline, what is convention, what can AIGC compress" — never happens. The doc reads as authoritative because of the framing, not the rigor.

**Why it happens:** Genuine first-principles decomposition is slow, uncomfortable, and frequently concludes "the existing thing was mostly right" — which feels like failure. Analogy dressed as derivation is faster and feels creative.

**Concrete film/AIGC example:** "From first principles, a film pipeline needs: Ideation → Script → Storyboard → Shots → Edit → Sound → Mix." This is the *traditional* pipeline restated — not derived. A real first-principles pass would ask: "Why is storyboard a separate node from shot-generation in an AIGC world where the gen model accepts text + character refs directly? Does the storyboard node survive only because humans needed an intermediate spec, or does it carry marginal value the gen model cannot internalize?" If the design doesn't *answer that question explicitly per node*, it's not first principles.

**How to avoid:** Each node in the final DAG must carry a `derivation` field answering: (a) what is the irreducible user value this node produces, (b) what would be lost if this node were merged into an adjacent one, (c) what traditional-workflow artifact this node replaces or compresses. Nodes whose `derivation` reads "every pipeline has this" fail the test and must be re-derived or merged.

**Warning signs:** The derivation section is shorter than the node-description section. Nodes appear in the same order as kais-movie-agent's existing 8 phases. The word "obviously" appears in justifications.

**Phase to address:** The **derivation-record** phase (target feature #1) — this IS the milestone's core deliverable; if derivation is theater, the whole milestone fails.

---

### Pitfall 1.2: Ignoring existing knowledge as "bias" when it is validated practice

**What goes wrong:** In the name of "ignoring historical baggage" (the user's words: "忽略现有 kais-movie-agent 8 phases 和 hermes movie-experts 26 skills 的历史包袱"), the design throws out *validated* craft knowledge — 180° axis rule, Murch's Rule of Six, three-act structure, 付费卡点 placement heuristics — treating them as bias to be cleansed rather than compressed wisdom to be re-derived and likely re-confirmed.

**Why it happens:** "First principles" is emotionally conflated with "clean slate". Musk's actual method does not discard validated physics — it discards *analogies* that have no physical basis. The 180° axis rule is not analogy; it is a perceptual invariant (audience spatial orientation) that will re-emerge from any honest derivation.

**Concrete film/AIGC example:** The design concludes "there is no 'editor' node — the gen model emits final cuts directly". This discards Murch's Rule of Six (rhythm, spatial continuity, temporal continuity, etc.) as if AIGC makes it obsolete. But those six dimensions are *exactly* the failure modes gen video exhibits (temporal flicker, identity drift, axis breaks). A first-principles derivation would re-derive the *need* for a consistency-critique node — possibly concluding the human editor role compresses into an AI critic node, but NOT concluding it disappears.

**How to avoid:** Target feature #3 (102-book corpus anchoring) is the antidote IF used correctly. Each derived node must cite which traditional工序 it succeeds, and the design doc must include a "re-derivation log" showing the node was *tested against* the corpus rather than *derived in ignorance of it*. If a node has no traditional anchor AND no explicit justification for why traditional wisdom is obsolete in AIGC, it is suspect.

**Warning signs:** The 102-book corpus is cited only in an appendix. Refs to Murch / Field / Bazin appear in the bibliography but never in node derivations. The design uses "AIGC changes everything" as a blanket license to skip re-derivation.

**Phase to address:** The **corpus-anchor** phase (target feature #3) — and a cross-cutting review gate that verifies each node's derivation references at least one corpus anchor.

---

### Pitfall 1.3: Premature optimization for current-gen models (Sora/Kling/Veo)

**What goes wrong:** The derived node set is shaped by *today's* gen-model capabilities and limits — e.g., "we need a separate character-consistency node because LoRA + IP-Adapter is the only way to get identity lock today". Six months from now, when a model ships native cross-shot identity, that node is dead weight and the design looks foolish.

**Why it happens:** Current-gen constraints are concrete and easy to reason about; future-gen capabilities are speculative. It is tempting to derive "what is necessary given Sora 2" rather than "what is necessary given the *trajectory* of AIGC".

**Concrete film/AIGC example:** Deriving a "sketch-then-render" two-stage node (kais-movie-agent's actual V8 architecture Phase 5.3/5.5) as a *first-principles* necessity. It is not — it is a workaround for current image-gen's weak composition control. A first-principles node would be "composition-lock" (the user value), with sketch-then-render documented as *one current instantiation*, not as the node itself.

**How to avoid:** Separate two layers in every node spec: (a) the **irreducible user value** (composition lock, identity lock, pacing control) — stable across model generations; (b) the **current AIGC instantiation** (sketch-then-render, LoRA, ControlNet) — explicitly flagged as model-dependent, with a `model_horizon` field noting when this instantiation is likely to be superseded. The node DAG must be valid even if every named model in layer (b) is swapped.

**Warning signs:** Node names contain model-specific terms ("LoRA-bake node", "Seedance node"). The I/O contract references a specific provider's API shape. There is no "model-agnostic invariant" statement per node.

**Phase to address:** The **node-design** phase (target feature #2) — I/O contracts must be specified at the user-value layer, with current-model instantiation as a separate annex.

---

### Pitfall 1.4: "Different from existing" mistaken for "better than existing"

**What goes wrong:** Because the user said "ignore the historical 8 phases / 26 skills", the design treats divergence from existing as proof of correctness. If the new node set has 5 nodes where kais-movie-agent has 8, the design celebrates "compression!" without verifying the 3 removed stages were actually redundant rather than load-bearing.

**Why it happens:** The brief rewards novelty. There is no explicit pressure to *justify* convergence with the existing pipeline when convergence is the right answer.

**Concrete film/AIGC example:** The new DAG omits a separate audio-mix node, arguing "the gen model emits mixed audio". This is divergence-for-divergence's-sake: mixing is a perceptual craft (LUFS targeting, dialogue ducking, platform loudness specs) that gen models are actively bad at. The design should converge with existing here (keep a mix node) — but the "first principles = different" frame makes convergence feel like failure.

**How to avoid:** Add an explicit "convergence log" to the design doc: for each node where the new DAG agrees with the existing kais-movie-agent 8 phases, state why agreement is correct (not just "we kept it"). For each divergence, state what specific failure mode of the existing pipeline the divergence fixes. Divergence without a named failure mode is a smell.

**Warning signs:** The design doc never agrees with the existing pipeline. Every existing node is "replaced" or "merged". The comparison section (target feature implies comparing to existing 8 phases) is missing or only lists gaps in the existing pipeline, never gaps in the new one.

**Phase to address:** The **comparison-and-gap-analysis** sub-deliverable (implied by "产出后会跟它们做对照分析") — must be a real section, not an afterthought.

---

### Pitfall 1.5: "I derived this from physics" fallacy — reasoning by analogy in disguise

**What goes wrong:** The design presents nodes as if derived from fundamental constraints ("a story must have a hook because attention is finite") when the actual reasoning was "every successful 短剧 has a hook in the first 3 seconds" — which is empirical pattern-matching, not first-principles derivation. The vocabulary of derivation masks the epistemic status.

**Why it happens:** True first-principles derivation is rare and hard. "Attention is finite → therefore hook" *sounds* reductionist but is actually: (a) an empirical observation (humans disengage), (b) mediated by a platform algorithm (抖音's completion-rate weighting). Both are contingent, not physical.

**Concrete film/AIGC example:** Deriving a "3-second hook node" as physically necessary. The honest derivation: "Platform algorithms weight 完播率 heavily; human attention drops sharply in the first 5-7 seconds for low-trust content (short-form); therefore a node that maximizes early-frame engagement has high expected ROI on platform distribution." That is a *contingent, platform-dependent* derivation — and it should be labeled as such, so that when the platform algorithm changes, the node's justification is revisable.

**How to avoid:** Every derivation step must tag its epistemic status: `physical` (perceptual invariant — 180° axis, light direction), `psychological` (attention, emotion — contingent on human nature but stable), `platform-algorithmic` (抖音 weighting — contingent and volatile), `tool-capability` (current gen model limits — contingent and fast-moving). Nodes whose only justification is `platform-algorithmic` or `tool-capability` must be flagged as high-volatility and given a re-derivation trigger.

**Warning signs:** All derivations read as equally fundamental. No node is flagged as platform-dependent. The design never asks "what happens to this node if 抖音 changes its algorithm tomorrow?"

**Phase to address:** The **derivation-record** phase — epistemic tagging is a structural requirement of the derivation log, not an optional annotation.

---

### Pitfall 1.6: Reverse-engineering the desired answer into "first principles"

**What goes wrong:** The author has a preferred node set in mind (often: a lightly-relabeled version of what already exists, or a personal aesthetic preference) and works backward to construct a derivation that lands on it. The derivation is ex post justification, not inquiry.

**Why it happens:** Designers are human; we all have priors. Without an adversarial check, derivation drifts toward confirming the author's prior.

**Concrete film/AIGC example:** The author believes "the screenplay is the soul of a film, so the screenplay node must be central and upstream of everything". The derivation then constructs reasons why this must be so, ignoring evidence that in AIGC pipelines the visual style genome (which constrains what the gen model can produce) may be the actual upstream constraint, with screenplay downstream of visual feasibility.

**How to avoid:** Include a **steelman-the-elimination** section: for each node in the final DAG, state the strongest case for *removing* it, and explain why that case loses. If the design cannot articulate the strongest case against its own nodes, the derivation was not honest.

**Warning signs:** The final DAG closely matches the author's prior published work (or the existing pipeline with cosmetic renames). The "alternatives considered" section is weak or absent. No node was seriously considered for elimination and survived.

**Phase to address:** The **derivation-record** phase — must include an explicit "nodes considered and rejected" log with reasons.

---

## Category 2 — AIGC Pipeline Node-Design Pitfalls

These are failure modes specific to designing gen-AI pipelines (not traditional film pipelines). The v1 RETROSPECTIVE did not surface these because v1 was about *content* (refs + skills), not *pipeline architecture*.

### Pitfall 2.1: Over-decomposition — every traditional stage becomes a node, missing AIGC compression

**What goes wrong:** The new DAG has 20+ nodes mirroring the traditional film pipeline one-to-one, because that's the safe-feeling decomposition. AIGC's actual win is *compression*: stages that required separate human specialists can collapse into one prompt with the right context.

**Why it happens:** Decomposing along traditional lines is intellectually easy and defensible ("every stage is real"). Compression requires arguing that two stages are actually one capability, which is harder and riskier.

**Concrete example:** Separate nodes for "shot list" → "storyboard" → "shot generation". In AIGC, the storyboard may be a *transient internal artifact* of the shot-generation prompt, not a separate persisted node — especially as multi-shot gen models (Sora 2, Kling multi-shot) mature.

**How to avoid:** For every adjacent pair of nodes, ask the "merge test": "Could a single sufficiently-capable model with the right context do both in one pass?" If yes, the two nodes must justify their separation by a *current* model-capability gap (flagged `tool-capability`, per Pitfall 1.5) or a *human-review* seam (see Pitfall 2.9) — not by tradition.

**Warning signs:** Node count > 12 for a short-drama pipeline. Every traditional film stage has a 1:1 node. No two nodes are candidates for merging.

**Phase to address:** Node-design phase — merge-test is a required step per node pair.

---

### Pitfall 2.2: Under-decomposition — one giant "generate film" prompt, no consistency guarantees

**What goes wrong:** The opposite extreme — over-confident in AIGC, the design collapses everything into 3-4 mega-nodes ("generate script", "generate video", "generate audio"). Identity, style, and plot continuity drift because no node is responsible for *enforcing* them; each gen call is locally coherent but globally inconsistent.

**Why it happens:** Excitement about model capability + desire for elegance. Especially tempting after reading Sora 2 demos that look end-to-end.

**Concrete example:** A single "video generation" node that takes the full script and emits all shots. No node owns character-identity consistency across shots; no node owns plot-continuity verification; the output is a string of pretty but incoherent clips.

**How to avoid:** Every *global invariant* (character identity, style genome, plot continuity, spatial consistency, emotional arc) must have an **explicit owner node** in the DAG — either a generation node that consumes the invariant as input, or a critique node that verifies it post-hoc. Invariants with no owner are the #1 source of AIGC film incoherence.

**Warning signs:** The DAG has generation nodes but no critic/audit nodes. No node consumes a "character bible" or "style genome" as input. No node emits a "continuity verdict".

**Phase to address:** Node-design phase — produce an "invariant ownership matrix" (invariant × owning node) as a required deliverable.

---

### Pitfall 2.3: "AI director" without explaining marginal value over a prompt template

**What goes wrong:** The design includes nodes labeled "AI Director", "AI Showrunner", "AI Creative Producer" — high-status human roles slapped onto an LLM call without specifying what the AI does that a static prompt template or a deterministic ruleset could not do.

**Why it happens:** Role-naming feels sophisticated. Specifying marginal value is hard.

**Concrete example:** An "AI Director" node whose job is "review the dailies and give notes". If the notes are deterministic ("check 180° axis, check eyeline match"), it's a linter, not a director — call it that. If the notes require genuine creative judgment ("this performance reads flat, try a different emotional subtext"), the design must specify *what context the LLM needs* to make that judgment (the script's subtext, the actor's previous takes, the directorial intent) — otherwise it's theater.

**How to avoid:** For every "AI <human-role>" node, the spec must answer: (a) what does this node decide that a static template cannot, (b) what context does it need to make that decision well, (c) what is the fallback if the LLM's judgment is wrong (human review? regeneration? rules-based veto?). Nodes that cannot answer (a) should be renamed to their actual function ("axis-lint", "style-consistency-checker").

**Warning signs:** Node names map 1:1 to Hollywood job titles. Node specs describe "creativity" without specifying inputs. No node has a "fallback when LLM is wrong" clause.

**Phase to address:** Node-design phase — role-name audit pass is required.

---

### Pitfall 2.4: Ignoring consistency loops — regenerating without continuity verification

**What goes wrong:** The DAG is a straight line: generate → generate → generate. No node verifies that shot N is consistent with shots 1..N-1. Drift accumulates silently until the final cut is unwatchable, and the only recovery is "regenerate everything".

**Why it happens:** Linear DAGs are easy to draw. Loops require specifying exit conditions, max-iteration budgets, and escalation paths.

**Concrete example:** Character wardrobe drifts across shots because each shot-gen call samples wardrobe independently. The DAG has no "wardrobe-continuity-check" node between shot gen and the next stage.

**How to avoid:** Every multi-shot invariant must have a **verification node** downstream of generation, with a defined loop back to regeneration (max N iterations) and an escalation path (human review) when the loop budget is exhausted. v1's continuity expert exists for exactly this — the v2.0 design must decide whether to keep it as a node, fold it into a broader "consistency-critic" node, or eliminate it (with justification).

**Warning signs:** No node has "loop back to <upstream>" in its spec. No max-iteration field on any node. No human-escalation path.

**Phase to address:** Node-design phase — loop topology is a required diagram, not optional.

---

### Pitfall 2.5: Missing critic/reviewer nodes — trusting the first output

**What goes wrong:** Every node is a generator. No node is a critic. Quality is whatever the generator emits. This is the single most common AIGC pipeline failure mode in the wild.

**Why it happens:** Generators feel like progress; critics feel like overhead. Demo videos look great when you cherry-pick.

**Concrete example:** A "script generation" node with no downstream "script audit" node. The script that goes to production is whatever the LLM emitted first. v1 actually built `script_auditor` (Phase 7A-1) for exactly this reason — the v2.0 design must not regress.

**How to avoid:** Adopt v1's own pattern: every generation node must have a paired critique node (or a critique step inside the node spec) that scores the output against an explicit rubric and decides accept/regenerate/escalate. v1 already proved this pattern works (script_auditor's Pearson ≥ 0.65 validation protocol).

**Warning signs:** No node name contains "audit", "critic", "verify", "check", "review". No node emits a quality score. No node has a "reject and regenerate" output.

**Phase to address:** Node-design phase — pair every generator with a critic; this is non-negotiable.

---

### Pitfall 2.6: "More nodes = more sophisticated" — conflating count with rigor

**What goes wrong:** The design celebrates a 25-node DAG as "more sophisticated" than kais-movie-agent's 8 phases. Sophistication comes from per-node rigor (clear I/O, validated invariants, real critique), not from count. A 6-node DAG where each node is rigorous beats a 25-node DAG where most are hand-wavy.

**Why it happens:** Node count is a visible metric; per-node rigor is not. More nodes feels like more work done.

**Concrete example:** Splitting "audio" into "dialogue", "music", "foley", "ambient", "mix", "master" as 6 separate nodes when a single "audio-pipeline" node with sub-steps would be clearer and equally capable.

**How to avoid:** Set a soft node-count budget up front (suggest: 8-15 for a short-drama pipeline). Every node beyond the budget requires explicit justification of why it cannot be a sub-step of an adjacent node. Track "node count" as a design smell, not an achievement.

**Warning signs:** Node count grows during design (starts at 8, ends at 22). No node is ever merged or removed during design iterations. The design doc brags about node count.

**Phase to address:** Node-design phase — node-count budget set in the derivation-record phase, enforced in node-design.

---

### Pitfall 2.7: Premature commitment to specific gen models (Sora today, gone tomorrow)

**What goes wrong:** The node specs hard-code model names ("the video node calls Sora 2"). By the time kais-movie-agent implements, Sora 3 has shipped with a different API, or Sora is deprecated, and the design is stale.

**Why it happens:** Concrete model names make specs feel actionable. Abstract capability descriptions feel vague.

**Concrete example:** v1 RETROSPECTIVE already burned by this — `animator/SKILL.md` shipped `wan22_video` which did not exist. The same mistake at the design-doc level propagates further.

**How to avoid:** Node specs describe **capability requirements** ("generates ≥1080p video, ≥5s, with character identity lock given a reference image"), not model names. Model names appear only in a separate "current instantiation" annex with `verified_date` stamps, exactly as v1's `_shared/known-external-models.yaml` allowlist requires. The design must be implementable against ANY model meeting the capability spec.

**Warning signs:** Model names appear in node I/O contracts. Node names reference models. No capability-spec layer exists separate from instantiation.

**Phase to address:** Node-design phase — capability-spec is the canonical layer; model annex is secondary.

---

### Pitfall 2.8: Ignoring cost/latency tradeoffs — a technically-correct but unrunnable pipeline

**What goes wrong:** The DAG is internally consistent and would produce good output, but the total cost per short-drama episode is $50 and the latency is 4 hours. No operator can afford to run it. The design is technically correct and practically dead.

**Why it happens:** Design docs don't bear the cost; implementation does. It's easy to add "and another critique pass" when you're not paying for it.

**Concrete example:** A loop that regenerates shots up to 5 times until the critic passes, with no cost ceiling. Each shot gen is $0.50; 5 retries × 30 shots = $75 just for shot-gen retries.

**How to avoid:** Each node spec must include a `cost_budget` (currency or compute units) and `latency_budget`. The DAG must include a `total_run_cost` estimate with a sanity check against realistic operator budgets (短剧 production budgets are typically ¥1000-10000/episode for indie). Nodes without cost budgets are not spec-complete.

**Warning signs:** No node has a cost field. The DAG has loops with no cost ceiling. Total cost is never estimated. The design never asks "can a real operator afford to run this?"

**Phase to address:** Node-design phase — cost/latency budget is a required field per node.

---

### Pitfall 2.9: Neglecting human-in-the-loop seams — where AI fails, nothing catches it

**What goes wrong:** The DAG is fully automated. When the LLM makes a subtle creative mistake (a hook that's technically present but emotionally flat; a plot twist that's logical but cliché), nothing in the pipeline catches it because no node is designed for human review at the right seams.

**Why it happens:** Automation feels like progress. Human-in-the-loop feels like a regression.

**Concrete example:** A pipeline that goes from topic → final video with zero human checkpoints. The hook is weak, but no node flags it; the entire episode ships and flops.

**How to avoid:** Identify the **high-leverage review seams** — the points where a 30-second human check saves hours of downstream waste. For short-drama: (a) after story-kernel / hook design, (b) after first-shot-per-scene (does the visual style work?), (c) after rough-cut (does pacing work?). The DAG must mark these as `human_gate: true` nodes with defined review criteria and time budgets. kais-movie-agent's V8 architecture already has 审核门 (review gates) — the v2.0 design must explicitly decide where to keep them.

**Warning signs:** No node has `human_gate: true`. The DAG claims "fully autonomous". No review criteria are specified for any seam.

**Phase to address:** Node-design phase — human-gate placement is a required diagram annotation.

---

### Pitfall 2.10: No fallback strategy per node — when the gen model is down/bad/expensive

**What goes wrong:** Each node assumes its gen model is available and good. When the model is rate-limited, deprecated, or producing degraded output, the pipeline has no fallback and either crashes or ships garbage.

**Why it happens:** Fallback is unglamorous cross-cutting concerns work.

**Concrete example:** The TTS node assumes a specific provider. That provider has an outage. The pipeline stalls for 6 hours with no fallback to an alternative TTS or even a graceful "audio pending" state.

**How to avoid:** Each node spec includes a `fallback_strategy` field: (a) alternative model (named by capability, not brand), (b) degraded-mode output (e.g., static image if video gen fails), (c) deferred-completion (mark output as pending, continue pipeline, fill later). Nodes with no fallback must be flagged as single-point-of-failure.

**Warning signs:** No node has a `fallback_strategy` field. The design assumes 100% model availability. No degraded-mode behavior is specified.

**Phase to address:** Node-design phase — fallback is a required field per node.

---

### Pitfall 2.11: Conflating "AIGC transformation point" with "where an LLM is called"

**What goes wrong:** The user's milestone brief asks each node to specify its "AIGC 转化点" (AIGC transformation point). The design reduces this to "does this node call an LLM?" — missing that an AIGC transformation point is about *where traditional human craft is replaced or augmented by generative AI*, which is a deeper question than API-call placement.

**Why it happens:** "AIGC 转化点" is a fuzzy term; reducing it to "LLM call here" is the path of least resistance.

**Concrete example:** Marking the "mix" node as an AIGC transformation point because it calls an AI mastering service, while marking the "screenplay" node as also an AIGC transformation point because it calls an LLM. These are very different transformations: the former is a narrow AI assist on a deterministic task; the latter is full creative generation. The design should distinguish them.

**How to avoid:** Classify each AIGC transformation point by type: `full-generation` (AI creates from spec, e.g., screenplay from story kernel), `augmentation` (AI assists but human or rules dominate, e.g., mixing assist), `verification` (AI critiques human or AI output, e.g., script audit), `transformation` (AI converts between modalities, e.g., text-to-image). The node's value proposition differs by type — full-generation nodes need strong critique downstream; verification nodes need validated rubrics.

**Warning signs:** Every node's AIGC transformation point is described identically. No distinction between generation and verification. The transformation point section reads as a checklist of "where we call the API".

**Phase to address:** Node-design phase — AIGC transformation taxonomy is a required structural element.

---

## Category 3 — Dual-Repo Coordination Pitfalls

Design lives in hermes-agent/.planning/; implementation lives (later) in kais-movie-agent/. The v1 RETROSPECTIVE's "SUMMARY ↔ README drift" lesson (Key Lesson 7) is the small-scale version of this category. At the cross-repo scale, the drift risk is far worse.

### Pitfall 3.1: Design/impl drift — design evolves without impl tracking, or vice versa

**What goes wrong:** The v2.0 design ships. kais-movie-agent starts implementation 2 months later. Meanwhile, kais-movie-agent has shipped V8, V9, V10 changes that diverge from the design's assumptions. The design doc references a V8 architecture that no longer exists.

**Why it happens:** Two repos, two timelines, no synchronization mechanism.

**Prevention strategy:** The v2.0 design doc must include a `kais-movie-agent_baseline_ref` field at the top — a git commit SHA or version tag of kais-movie-agent at design time. When implementation starts, the impl team must verify the baseline is still valid; if not, design must be re-validated against current kais-movie-agent before implementation begins. The handoff doc (target feature #5) must specify this reconciliation step explicitly.

**Phase to address:** The **handoff-doc** phase (target feature #5) — baseline ref + reconciliation procedure is a required deliverable.

---

### Pitfall 3.2: Handoff doc rot — design sits unread, impl team re-derives from scratch

**What goes wrong:** The design doc is 80 pages, beautifully reasoned, and the kais-movie-agent impl team reads the executive summary, skips the rest, and re-derives the pipeline from their own intuition because "the design doc is too long to read during implementation".

**Why it happens:** Design docs are written for design-time reasoning, not impl-time lookup. The v1 RETROSPECTIVE already hit this pattern (SUMMARY drifted from README because nobody refreshed it).

**Prevention strategy:** The design doc must have a **impl-cheatsheet annex** — a 1-2 page extract containing: (a) the final node DAG as a diagram, (b) per-node I/O contract table (inputs, outputs, capabilities required), (c) per-node AIGC transformation type, (d) the human-gate locations. The impl team reads this annex; the derivation log is reference material, not required reading. The cheatsheet must be the canonical source for implementation decisions; any divergence from it requires a written ADR (architecture decision record) in kais-movie-agent explaining why.

**Phase to address:** The **handoff-doc** phase — impl-cheatsheet is a required sub-deliverable.

---

### Pitfall 3.3: Ambiguous ownership — who owns the node DAG over time?

**What goes wrong:** v2.0 ships the design. Three months later, both hermes-agent (movie-experts skills evolve) and kais-movie-agent (pipeline evolves) have reasons to modify the DAG. Neither side knows who owns the canonical version. The DAG forks silently.

**Why it happens:** The brief says "design lives in hermes-agent", but doesn't specify post-handoff ownership.

**Prevention strategy:** The handoff doc must declare explicit ownership: (a) **hermes-agent owns the design-intent layer** (node value propositions, AIGC transformation rationale, derivation log) — changes here require a design-revision milestone; (b) **kais-movie-agent owns the implementation layer** (concrete model choices, API integration, actual code) — changes here are free within the capability-spec; (c) **the node DAG itself is co-owned** — structural changes (add/remove/reorder nodes) require sign-off from both repos, documented as a DAG-revision ADR cross-linked in both repos. Without this, the DAG will fork within 6 months.

**Phase to address:** The **handoff-doc** phase — ownership matrix is a required deliverable.

---

### Pitfall 3.4: Versioning — design v1 vs impl v1 vs design v2

**What goes wrong:** Design v1 ships. Impl v1 starts. Design v2 is started (to fix design v1 gaps discovered during impl) while impl v1 is still in progress. Impl v1 finishes implementing design v1, which is now obsolete. Nobody knows which version of the design is authoritative.

**Why it happens:** Sequential numbering hides concurrent evolution.

**Prevention strategy:** Use **date-stamped design versions** (not just `v1`, `v2`): `design-2026-06-16-prfp`. Each design version declares its `supersedes` and `superseded_by` fields. Each impl milestone in kais-movie-agent declares which design version it targets (`targets_design: design-2026-06-16-prfp`). A design version is `frozen` once an impl targets it; revisions require a new dated version. This is the only way to keep concurrent evolution tractable across two repos.

**Phase to address:** The **handoff-doc** phase — versioning scheme is a required deliverable.

---

### Pitfall 3.5: Implicit assumption that hermes-agent skills will follow the new DAG

**What goes wrong:** The v2.0 design derives a new node set, but hermes-agent's existing 26 movie-experts skills don't actually map onto it. The design doc claims "this informs hermes-agent skill evolution" (target feature #5) but provides no concrete mapping. When a later hermes-agent milestone tries to align skills to the DAG, it discovers the mapping is ambiguous or contradictory.

**Why it happens:** The design team knows hermes-agent but doesn't do the mapping work because "that's a future milestone".

**Prevention strategy:** The handoff doc must include a **skill-DAG mapping table**: for each of the 26 existing experts, state which new DAG node(s) it informs, and flag experts that don't map cleanly (these are candidates for deprecation or major refactor in the future hermes-agent milestone). The v1 RETROSPECTIVE's "frozen expert_id HARD RULE" (FOUND-08) means this mapping must preserve expert_ids — the design must not silently rename experts.

**Phase to address:** The **handoff-doc** phase — skill-DAG mapping is a required deliverable.

---

## Category 4 — LLM Creative-Story-Framework Pitfalls

The user emphasized "大模型如何凝练出有创意且逻辑自洽的故事框架". This is target feature #4 (a dedicated sub-doc). The failure modes here are about how the design *specifies* the creative-story node(s), not about the LLM's behavior in the abstract.

### Pitfall 4.1: Hallucinated logic — LLM generates plot points that contradict the setup

**What goes wrong:** The story-kernel / screenplay node emits a plot that is locally coherent per scene but globally contradictory (character knows something they shouldn't; timeline doesn't add up; stakes established in scene 1 vanish by scene 5).

**Why it happens:** LLMs generate token-by-token without a global consistency model. Each scene looks fine; the cross-scene invariants are not enforced.

**Design-level mitigation:** The creative-story node's I/O contract must include a **consistency-context input** — a structured representation of established facts (character knowledge state, timeline, stakes, spatial layout) that the generation must respect. Downstream, a **logic-critic node** (or sub-step) verifies the generated story against this context and rejects/regenerates on contradiction. v1's `script_auditor` (5-dim audit including character-network) is a precedent; the v2.0 design must not drop this pattern. The design must specify what the consistency-context schema looks like — without it, the critic has nothing to check against.

**Phase to address:** The **LLM-creative-subdoc** phase (target feature #4) + the node-design phase (the story node's I/O contract).

---

### Pitfall 4.2: Shallow narrative — cliché tropes from training data, no genuine creativity

**What goes wrong:** Every generated story is a slight remix of Save the Cat! beats or 短剧 爆款公式. The output is "creative" only in the sense that the LLM picked different surface details; the structure is identical across runs.

**Why it happens:** LLMs are trained on the most common patterns; without explicit pressure toward novelty, they regress to the mean.

**Design-level mitigation:** The creative-story node spec must include a **novelty-pressure mechanism**: (a) a `novelty_constraint` input (e.g., "avoid these 5 tropes", "must include an unconventional POV"), (b) a `novelty_critic` that scores output against a trope-catalog and rejects outputs above a similarity threshold, (c) a `creative_source` input (v1 already built `creative_source` expert mining 6 social strata — this is the antidote; the design must wire it in). Without explicit novelty pressure, the node produces competently-executed clichés.

**Phase to address:** The **LLM-creative-subdoc** phase — novelty mechanism is a required design element.

---

### Pitfall 4.3: Lack of self-consistency verification — trusting the LLM's first draft

**What goes wrong:** The story node emits a draft; no node checks whether the draft is self-consistent before passing it downstream. By the time the inconsistency is noticed (in storyboard, or worse, in final video), the cost of fixing it is 10-100x higher.

**Why it happens:** Self-consistency verification requires a separate LLM call (or a structured validator), which feels like overhead.

**Design-level mitigation:** Same pattern as Pitfall 2.5 but applied specifically to story: every story-generation node must be paired with a story-verification node (or sub-step) that checks: (a) character arc consistency, (b) timeline consistency, (c) stake escalation consistency, (d) setup-payoff closure. v1's `script_auditor` 5-dim rubric is the template — the v2.0 design must explicitly decide whether to keep script_auditor as-is, fold it into a broader story-critic, or replace it.

**Phase to address:** The **LLM-creative-subdoc** phase + node-design phase.

---

### Pitfall 4.4: "More details" mistaken for "richer story"

**What goes wrong:** The story node spec asks for exhaustive detail (full character bios, complete scene descriptions, every prop listed), on the theory that more detail = richer story. In practice, the detail bloats the prompt, dilutes the LLM's attention on what matters, and produces stories that are dense but emotionally flat.

**Why it happens:** "Comprehensive spec" feels rigorous. "Minimal viable story structure" feels negligent.

**Design-level mitigation:** The story node's I/O contract must specify a **minimal viable story structure** — the smallest set of fields that captures the creative essence (logline, protagonist-want, central conflict, turning points, resolution stance). Additional detail (full bios, prop lists) is generated *on demand* by downstream nodes that actually need it, not pre-emptively by the story node. The design must distinguish "story structure" (irreducible, upstream) from "story elaboration" (extensible, downstream). v1's `creative_source` Story Kernel schema is the right level of abstraction — the design should build on it, not inflate it.

**Phase to address:** The **LLM-creative-subdoc** phase + node-design phase.

---

### Pitfall 4.5: "Creative" confused with "random" — genuine creativity is constraint-respecting novelty

**What goes wrong:** The design encourages "creative" story generation by removing constraints ("let the LLM surprise us"). The output is random, not creative. Genuine creativity (per the cognitive-science literature the user's emphasis implies) is novelty *within* constraints — a creative choice is creative *because* it satisfies the constraints in an unexpected way, not because it ignores them.

**Why it happens:** "Creative" is operationally undefined in the design; the LLM fills the vacuum with high-variance sampling.

**Design-level mitigation:** The creative-story node must define creativity **operationally**: (a) what constraints are inviolable (genre, length, platform format, character count, 完播率 target), (b) what dimensions are open for novelty (POV, structural inversion, trope-subversion, thematic angle), (c) how novelty is measured (against a trope-catalog embedding, against a corpus of prior outputs). Creativity = high novelty on open dimensions + full compliance on inviolable constraints. The design must make this distinction explicit, or the node produces randomness labeled as creativity.

**Phase to address:** The **LLM-creative-subdoc** phase — operational definition of creativity is the core deliverable of that sub-doc.

---

### Pitfall 4.6: Story-arc template over-reliance — Save the Cat! / Hero's Journey applied dogmatically

**What goes wrong:** The story node hard-codes a single story-arc template (Save the Cat!'s 15 beats, or the Hero's Journey 12 stages) and forces every story through it. Output variety collapses; every short-drama feels structurally identical.

**Why it happens:** Templates are concrete and easy to spec. Choosing among templates requires a meta-decision the design doesn't make.

**Design-level mitigation:** The story node must support a **template library** (not a single template): classical 3-act, Save the Cat!, Hero's Journey, Kishōtenketsu (起承转合, the East Asian 4-act structure suited to short-form), 短剧 爆款公式 (the platform-specific pacing template), and anti-structure (no template, for experimental work). The node takes a `template_choice` input; downstream, a critic verifies the output conforms to the chosen template. The design must not bake in a single template as "the" structure — v1's `screenplay` ref already includes multiple structural theories (Field, McKee, O'Bannon); the v2.0 design must preserve that plurality.

**Phase to address:** The **LLM-creative-subdoc** phase + node-design phase.

---

### Pitfall 4.7: Ignoring Chinese 短剧 conventions — OR over-fitting to them at the expense of artistic merit

**What goes wrong:** Two opposite failure modes: (a) the design treats 短剧 as just "short film" and ignores the platform-specific conventions (前3秒 hook, 付费卡点 density, 竖屏 framing, 男频/女频 genre split) — output flops on platform; (b) the design over-fits to 爆款公式 and produces algorithmically-optimized but artistically-empty content that wins short-term distribution but builds no durable audience.

**Why it happens:** (a) happens when the designer's frame is Western/general; (b) happens when the designer chases platform metrics without an artistic counter-weight.

**Design-level mitigation:** The story node must take a `platform_context` input that activates the relevant conventions (抖音 短剧, 快手 短剧, 小程序剧, 微电影, general short film), AND a `artistic_intent` input that can override pure-metric-optimization. The design must explicitly address the tension between platform-optimization and artistic-merit, not pick one side silently. v1's `compliance_marketing` and `hook_retention` experts encode the platform side; the design must preserve a counter-weight (v1's `theory_critic` and `creative_source` are candidates for the artistic side).

**Phase to address:** The **LLM-creative-subdoc** phase + node-design phase — the platform-vs-art tension is a required design topic.

---

## Category 5 — Musk-Method-Specific Pitfalls (with citations)

The user explicitly invoked Musk first-principles. This category covers what Musk himself warns about, and common misapplications of his stories.

### Pitfall 5.1: The booster-reuse story misapplied — "reuse is always cheaper" is not the lesson

**The story:** SpaceX derived, from physics, that the propellant is ~0.3% of launch cost; the rocket hardware is the rest; therefore reuse of the booster (the expensive hardware) could cut cost by ~100x. This is THE canonical Musk first-principles story (Isaacson biography, ch. on Falcon 9 landing; Musk has repeated it in many interviews).

**The common misapplication:** Generalizing to "reuse is always the first-principles answer". People apply this to software pipelines and conclude "every node must produce reusable artifacts". But the actual derivation is conditional: reuse wins *when the reusable thing is the cost driver and reuse overhead is low*. In an AIGC pipeline, the cost driver is often *inference compute* (not reusable — you pay each generation) or *human review time* (partially reusable via templates). Reusing artifacts (story bibles, character designs) helps, but is not the same kind of 100x lever.

**How it applies to v2.0 design:** Do not derive nodes around "reusability" as a universal principle. Derive around *cost-driver identification*: for each node, what is the actual cost driver (compute? human time? latency?), and does the node's design minimize *that* driver? The booster-reuse lesson, applied correctly, is "find the cost driver and attack it" — not "make everything reusable".

**Phase to address:** Derivation-record phase — cost-driver identification is a required field per node (ties to Pitfall 2.8).

---

### Pitfall 5.2: The battery-cost story misapplied — "decompose to materials" doesn't work for craft

**The story:** Musk looked at a battery pack's cost (~$600/kWh at the time), decomposed it to constituent materials (cobalt, nickel, aluminum, carbon), found the materials cost ~$80/kWh, concluded the gap is manufacturing/process, not physics, and built Gigafactory to close the gap. (Cited in Isaacson biography and many Musk interviews.)

**The common misapplication:** Decomposing a *craft* (filmmaking) to "constituents" and concluding the gap is process. Filmmaking is not a battery; its "constituents" (story, image, sound, performance) are not materials whose costs sum. A film is not the sum of its parts; it's an emergent Gestalt where the interaction quality dominates. Decomposing film to "story cost + image cost + sound cost" and optimizing each misses that the value is in the *integration*, which is exactly the part Musk's method is silent on.

**How it applies to v2.0 design:** Do not derive node costs by summing constituent costs. The pipeline's output value is dominated by *cross-node coherence* (does the image match the story's tone? does the sound match the image's rhythm?), which is a property of the DAG topology, not of any single node. The design must include a "coherence budget" — explicit cross-node invariants and the nodes that enforce them — and treat coherence as a first-class value driver, not a side-effect of good per-node specs.

**Phase to address:** Node-design phase — coherence-budget / invariant-ownership matrix (cross-references Pitfall 2.2).

---

### Pitfall 5.3: The Twitter/X pricing story misapplied — "challenge the assumption" is not "ignore the data"

**The story:** When acquiring Twitter, Musk questioned the assumption that the service needed its existing headcount and feature set, derived from "what is a town square minimally" and cut aggressively. (Isaacson biography, Twitter chapter.) The lesson people take: "question every assumption".

**The common misapplication:** Questioning assumptions that are actually *validated empirical regularities*. Musk questioned headcount (a contingent choice) — he did not question gravity, or the tensile strength of aluminum, or the fact that lithium ions intercalate. The method distinguishes *contingent assumptions* (fair game) from *validated invariants* (not fair game). People misapply the method by treating validated invariants (like the 180° axis rule, or the fact that humans disengage from boring content within seconds) as contingent assumptions to be questioned.

**How it applies to v2.0 design:** For each "assumption" the design questions, classify it: `contingent` (a choice someone made — fair to question) vs `validated-invariant` (an empirical regularity — questioning it requires extraordinary evidence). The 180° axis rule is a validated-invariant (perceptual); "we need a separate storyboard node" is contingent (workflow choice). The design must not casually discard validated-invariants in the name of first principles. (This is the same root as Pitfall 1.2; stated differently here with Musk-method framing.)

**Phase to address:** Derivation-record phase — assumption-classification is a required structural element.

---

### Pitfall 5.4: Musk himself warns about "first principles theater"

**The citation:** In interviews (e.g., the Lex Fridman podcast, the Third Row Tesla club AMA), Musk has repeatedly distinguished genuine first-principles thinking (which he says is exhausting and rarely necessary — "most of the time, reasoning by analogy is fine and faster") from the performative version. He has said, paraphrased: "First principles is for when the analogy is wrong or absent. If the analogy works, use it. Don't reinvent wheels."

**The misapplication:** Treating first-principles as a *mandatory method for every decision*. Musk uses it sparingly, for high-stakes decisions where existing analogies are demonstrably wrong (rocket reuse when the industry said "rockets are expendable"). For most pipeline-design decisions, the existing film pipeline IS a working analogy, and the right move is to *identify where the analogy breaks in the AIGC context* and apply first-principles only there.

**How it applies to v2.0 design:** Do not force every node to be derived from scratch. The design should explicitly mark which nodes are `analogy-valid` (existing film pipeline applies directly — e.g., color grading still needs a colorist node), which are `analogy-breaks-here` (existing pipeline assumes something false in AIGC — e.g., "each shot requires a separate shoot day" is false when gen models exist), and apply deep derivation only to the latter. Forcing first-principles on analogy-valid nodes wastes effort and risks Pitfall 1.4 (divergence-for-divergence).

**Phase to address:** Derivation-record phase — analogy-validity classification is a required field per node.

---

## Category 6 — 102-Book Corpus Mining Pitfalls

Target feature #3 requires anchoring each node to traditional工序 from the 102-book corpus. The v1 RETROSPECTIVE already shipped this corpus integration (Phase 8); the v2.0 design must mine it for *anchor references* without falling into these traps.

### Pitfall 6.1: Cherry-picking — citing only books that support the desired conclusion

**What goes wrong:** The designer has a preferred node set, and searches the corpus only for books that support it. Books that would challenge the design (e.g., Tarkovsky's anti-structure *Sculpting in Time* cited in corpus as -022, which argues against tight story-arc templates) are silently ignored.

**Why it happens:** Confirmation bias. The corpus is large enough to find support for almost any position.

**Prevention strategy:** For each node's corpus anchor, the design must also cite (and engage with) at least one corpus source that *challenges* the node's design. If no challenging source exists in the corpus, the design must state so explicitly. The "steelman-the-elimination" requirement (Pitfall 1.6) applies here at the corpus level: the strongest corpus-based case against each node must be stated and refuted.

**Phase to address:** Corpus-anchor phase (target feature #3).

---

### Pitfall 6.2: Anachronism — applying pre-AIGC workflow wisdom literally to AIGC context

**What goes wrong:** The corpus is overwhelmingly pre-AIGC (Bazin, Tarkovsky, Murch, Field — all writing before gen video existed). Anchoring a node to "Murch says cut on emotion" is fine as a *principle*, but anchoring the *execution* of that node to Murch's physical-film workflow (e.g., "the editor sits at a Steenbeck and reviews daily prints") is anachronistic nonsense.

**Why it happens:** The corpus's workflow details are vivid and easy to cite; separating principle from workflow requires judgment.

**Prevention strategy:** Each corpus anchor citation must distinguish: (a) the **principle** (likely still valid — "cut on emotion, not action"), (b) the **workflow** (likely obsolete — "review dailies on film"). The node's design adopts the principle, not the workflow. The anchor citation must explicitly note where AIGC changes the workflow execution while preserving the principle.

**Phase to address:** Corpus-anchor phase.

---

### Pitfall 6.3: Genre conflation — 微电影 wisdom ≠ 短剧 wisdom ≠ 长片 wisdom

**What goes wrong:** The corpus spans all three forms (the index shows 长片 theory dominates: Bazin, Tarkovsky, Field, McKee; 短剧 is barely represented; 微电影 has a few entries like 051 微电影剧作教程). The design treats corpus wisdom as uniform across forms, but pacing, hook density, 付费卡点 logic, and platform distribution differ radically between them.

**Why it happens:** The corpus is organized by craft discipline (剧本/导演/后期), not by content form. Genre/Form tagging is implicit.

**Prevention strategy:** Each corpus anchor citation must tag the source's `applicable_form` (长片 / 微电影 / 短剧 / universal-principle). Anchors tagged `长片` cannot be used to justify 短剧-specific node designs without an explicit translation argument ("this 长片 principle applies to 短剧 because..."). The design must be especially careful about 短剧-specific nodes (hook, 付费卡点) — the corpus has weak coverage here, and the design must not fake coverage by citing 长片 sources.

**Phase to address:** Corpus-anchor phase.

---

### Pitfall 6.4: Translation/context loss — Chinese film literature has specific traditions

**What goes wrong:** The corpus is largely Chinese (芦苇, 刘天赐, 戴锦华, 第五代摄影师) with specific Chinese cinematic and cultural traditions. Citing these sources via paraphrased English summaries loses the cultural specificity that makes them valuable. Worse, the design may misread a Chinese-theory concept through a Western-theory lens (e.g., reading 意境 as "mood" misses the Buddhist-aesthetic lineage).

**Why it happens:** The design is written bilingually (EN structure + CN prose per project convention), but the conceptual framing may default to Western.

**Prevention strategy:** For Chinese-theory corpus anchors, the citation must include the original term (in 汉字) alongside any gloss, and must flag where the concept has no clean English equivalent. v1 already built `_shared/glossary.md` (EN↔CN term dictionary) — the v2.0 design must extend it for any new terms introduced. The design must not silently translate untranslatable concepts.

**Phase to address:** Corpus-anchor phase + glossary maintenance (cross-references v1's bilingual pitfall pattern).

---

## Category 7 — Design-Documentation Pitfalls

These are failure modes of the *design doc itself* as an artifact. The v1 RETROSPECTIVE's "SUMMARY ↔ README drift" (Key Lesson 7) and "MILESTONES.md auto-accomplishments" patterns are precursors.

### Pitfall 7.1: Over-specifying — so rigid that future revisions are blocked

**What goes wrong:** The design doc specifies node I/O contracts down to the JSON field name and enum value. When implementation discovers a needed change, the doc's rigidity makes any change feel like a violation, so changes happen off-doc and the doc rots.

**Why it happens:** Precision feels rigorous. The line between "spec enough to implement" and "spec so tight it can't evolve" is hard to find.

**Prevention strategy:** Distinguish **stable contracts** (the user-value I/O — what the node produces for the next node, at the semantic level) from **implementation details** (JSON schema, field names, transport). Stable contracts are specified precisely and require design-revision milestones to change. Implementation details are sketched as suggestions with explicit "impl may vary" latitude. The doc must mark which layer each spec element belongs to.

**Phase to address:** All design phases — but enforced at the doc-review gate.

---

### Pitfall 7.2: Under-specifying — so vague that impl team has to re-design

**What goes wrong:** The design doc says "the story node generates a story given a topic" and stops there. The impl team has no idea what inputs the node actually needs, what outputs it produces, what its quality criteria are — so they re-design the node from scratch and the design doc adds no value.

**Why it happens:** Vague specs feel safely unchallengeable. Precise specs invite argument.

**Prevention strategy:** Every node spec must include, at minimum: (a) **inputs** (named, with types and sources), (b) **outputs** (named, with types and consumers), (c) **core task** (one sentence), (d) **AIGC transformation type** (per Pitfall 2.11), (e) **success criterion** (how do we know the node did its job — even if qualitative), (f) **corpus anchor** (per target feature #3). Nodes missing any of these are not spec-complete; the design milestone is not done.

**Phase to address:** Node-design phase — these six fields are the required node-spec template.

---

### Pitfall 7.3: No executive summary — design is inaccessible to non-authors

**What goes wrong:** The design doc is 60 pages of derivation log. The kais-movie-agent impl lead opens it, sees no summary, closes it, asks the author for a Slack summary. The Slack summary becomes the de facto design doc; the 60-page doc rots.

**Why it happens:** Derivation is the fun part; summarizing is not.

**Prevention strategy:** The design doc's first section must be a **3-page executive summary** containing: (a) the derived node DAG as a single diagram, (b) one-paragraph rationale for the overall shape, (c) the top 5 ways this DAG differs from the existing kais-movie-agent 8 phases and why, (d) the top 3 risks the design does NOT solve (deferred to implementation). The exec summary must be readable in 10 minutes by someone who will never read the rest. (Cross-references Pitfall 3.2's impl-cheatsheet.)

**Phase to address:** Doc-finalization phase — exec summary is the last thing written but the first thing reviewed.

---

### Pitfall 7.4: Missing rationale — decisions stated without "why"

**What goes wrong:** The design doc says "the DAG has 9 nodes, not 8" but doesn't say why 9, not 8 or 10. Every design decision reads as a fiat. When the decision is later questioned, nobody can reconstruct the reasoning, so it's either blindly defended or blindly overturned.

**Why it happens:** Rationale is implicit at design time (the author knows why) and feels redundant to write down.

**Prevention strategy:** Every design decision in the doc must carry a `rationale` field answering "why this and not the obvious alternative". v1's PROJECT.md `Key Decisions` table (Decision / Rationale / Outcome) is the exact pattern to follow — the v2.0 design doc must use the same shape. The v1 RETROSPECTIVE validated this pattern; the v2.0 design must not regress.

**Phase to address:** All design phases — `rationale` is a required field per decision.

---

### Pitfall 7.5: No versioning strategy — doc becomes impossible to evolve

**What goes wrong:** The design doc is committed as a single file with no version marker. Three months later, half of it has been edited in-place and nobody knows which parts are "v1 original" vs "v1.1 patches". When v2 is attempted, the team can't tell what's load-bearing vs negotiable.

**Why it happens:** Versioning feels like overhead until it's too late.

**Prevention strategy:** The design doc must use the versioning scheme from Pitfall 3.4 (date-stamped, with `supersedes` / `superseded_by`). Within the doc, each major section must carry a `stability` marker: `stable` (unlikely to change — the node DAG shape), `evolving` (expected to refine — per-node I/O details), `experimental` (a hypothesis — novel creative-story mechanisms). Future edits respect stability markers: `stable` sections require design-revision milestones to change; `experimental` sections are freely editable.

**Phase to address:** Doc-finalization phase — versioning scheme is set up front, stability markers applied during writing.

---

## Top 5 Critical Risks (priority order)

1. **First-principles theater (Pitfall 1.1, 1.5, 1.6, 5.4)** — If the derivation is ex-post justification dressed in reductionist language, the entire milestone is wasted effort and worse than honest intuition, because it feels unchallengeable. **The derivation-record phase must enforce structural rigor (per-node `derivation`, epistemic-status tagging, steelman-the-elimination, alternatives-considered log) — not just produce prose that sounds derived.**

2. **Design-impl drift across two repos (Pitfall 3.1, 3.2, 3.3, 3.4, 3.5)** — The design doc will be stale by the time kais-movie-agent implements, with no synchronization mechanism, unless the handoff-doc phase explicitly addresses baseline-ref, impl-cheatsheet, ownership-matrix, versioning-scheme, and skill-DAG mapping. v1's "SUMMARY ↔ README drift" (RETROSPECTIVE Key Lesson 7) is the small-scale preview of this failure.

3. **Throwing out validated craft as "bias" (Pitfall 1.2, 5.3)** — Discarding Murch / Field / the 180° axis rule as "historical baggage" in the name of first principles will produce a pipeline that regresses on solved problems. The corpus-anchor phase + assumption-classification (contingent vs validated-invariant) are the antidotes.

4. **Premature model-commitment (Pitfall 1.3, 2.7)** — Hard-coding Sora/Kling/Veo into node specs guarantees the design is stale within 6-12 months. Capability-spec layer must be canonical; model names appear only in a dated annex. v1 already burned by this (phantom `wan22_video`); v2.0 must not repeat at design-doc scale.

5. **Creative-story node under-specified (Pitfall 4.1-4.7)** — The user's headline emphasis ("有创意且逻辑自洽") maps to a node design with huge surface area. If the LLM-creative sub-doc (target feature #4) hand-waves novelty, self-consistency, and the platform-vs-art tension, the resulting pipeline produces either random or cliché output — neither of which is "creative". The sub-doc must operationally define creativity, specify consistency-context and novelty-pressure mechanisms, and address platform conventions without over-fitting.

---

## Pitfall-to-Phase Mapping

Since v2.0 PRFP roadmap phases are not yet defined, this mapping uses target features from PROJECT.md as the phase units. The roadmapper should translate these into concrete phases.

| Pitfall Category | Target Feature to Address | Verification |
|---|---|---|
| 1.x First-principles misapplication | #1 derivation-record + #3 corpus-anchor | Each node carries `derivation`, epistemic-status, steelman-elimination fields; review gate checks structural rigor |
| 2.x AIGC pipeline node-design | #2 node DAG design | Node-spec template enforces inputs/outputs/cost/fallback/critic/invariant-ownership; node-count budget enforced |
| 3.x Dual-repo coordination | #5 handoff doc | Handoff doc includes baseline-ref, impl-cheatsheet, ownership-matrix, versioning-scheme, skill-DAG mapping |
| 4.x LLM creative-story | #4 LLM-creative sub-doc | Sub-doc operationally defines creativity; specifies consistency-context, novelty-pressure, template-library, platform-vs-art tension |
| 5.x Musk-method misapplication | #1 derivation-record | Per-node assumption-classification (contingent vs validated-invariant); analogy-validity field; cost-driver-identification field |
| 6.x Corpus mining | #3 corpus-anchor | Per-anchor `applicable_form` tag; challenge-source engagement; principle-vs-workflow separation; original-term preservation |
| 7.x Design documentation | All phases, enforced at doc-review gate | Exec summary exists; `rationale` per decision; versioning + stability markers; spec layer separation (stable-contract vs impl-detail) |

---

## Confidence Assessment

| Area | Confidence | Reason |
|---|---|---|
| First-principles misapplications | HIGH | Failure modes are well-documented in philosophy-of-science and Musk-biography critique literature; examples grounded in actual v1/v2 scope |
| AIGC pipeline pitfalls | HIGH | Failure modes (no critic, no consistency loop, no fallback) are standard AIGC engineering patterns; v1 RETROSPECTIVE confirms the project already hit related issues |
| Dual-repo coordination | HIGH | v1 RETROSPECTIVE's "SUMMARY ↔ README drift" is direct precedent at smaller scale |
| LLM creative-story pitfalls | MEDIUM-HIGH | Failure modes (hallucinated logic, cliché output) are well-known LLM behaviors; design-level mitigations are reasonable but unvalidated for this specific domain |
| Musk-method specific | MEDIUM | Citations are from Isaacson biography + well-known interviews; exact quote wording should be verified against primary sources before the design doc cites them |
| 102-book corpus mining | HIGH | Direct inspection of corpus README confirms genre/form imbalance (长片-dominant, 短剧-weak); v1 Phase 8 already integrated this corpus so pitfalls are concrete |
| Design documentation | HIGH | v1 RETROSPECTIVE Key Lessons (esp. #4 frozen-identifier-rules, #7 refresh-when-scope-changes) directly inform these patterns |

---

## Open Questions (flag for phase-specific research)

1. **What is the actual cost ceiling for an indie 短剧 episode in 2026?** Pitfall 2.8 assumes ¥1000-10000; verify against current platform economics. Affects every node's cost_budget field.
2. **Which current (2026-Q2) 短剧 platform conventions are stable vs volatile?** Pitfall 4.7 assumes 抖音/快手 conventions are platform-algorithmic (volatile). If some are actually psychological (stable), the design's epistemic tagging changes. Needs platform-guideline verification.
3. **Does kais-movie-agent's V8 审核门 (review gate) pattern survive into the v2.0 design?** Pitfall 2.9 assumes human-gates belong in the DAG; V8 architecture (per `kais-movie-agent/docs/V8-ARCHITECTURE.md`) has them, but the v2.0 design may legitimately automate some. The handoff doc must address this explicitly.
4. **Musk quote primary-source verification.** Pitfalls 5.1-5.4 paraphrase Musk stories; before the design doc cites them, the exact quotes should be verified against the Isaacson biography and interview transcripts. LOW confidence on exact wording; HIGH confidence on the gist.
5. **Which of the 26 existing hermes-agent experts map cleanly to v2.0 DAG nodes, and which are candidates for deprecation?** Pitfall 3.5 requires this mapping; producing it may surface experts whose role the v2.0 design obsoletes (a politically and technically loaded finding).

---

*Pitfalls research for: v2.0 PRFP (Pipeline Redesign from First Principles) design-doc milestone*
*Researched: 2026-06-16*
*Sources: direct reading of `.planning/PROJECT.md` (v2.0 section), `skills/movie-experts/README.md`, `kais-movie-agent/README.md`, `kais-movie-agent/docs/V8-ARCHITECTURE.md`, `.planning/RETROSPECTIVE.md`, `skills/movie-experts/_shared/project-corpus/README.md`, prior v1 `.planning/research/PITFALLS.md`. Musk-method citations from Isaacson biography + public interviews (paraphrased; primary-source verification flagged in Open Questions).*
