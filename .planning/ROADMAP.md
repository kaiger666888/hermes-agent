# Roadmap: Movie-Experts Suite v2 — Milestone **v2.0 PRFP** (Pipeline Redesign from First Principles)

**Milestone:** v2.0 PRFP — Pipeline Redesign from First Principles
**Defined:** 2026-06-16
**Granularity:** standard
**Phase numbering:** continues from v1 (v1 ended at Phase 6; v2.0 starts at **Phase 7**)
**Coverage:** 52/52 v2.0 requirements mapped ✓ (0 orphaned)
**Deliverable form:** DESIGN DOCS ONLY — zero code changes to `skills/movie-experts/` or `kais-movie-agent/lib/`. Only `scripts/validate_design.py` (governance lint, dev tool) is permitted.

---

## Milestones

- ✅ **v1 — Movie-Experts Suite v2** — Phases 0-6 (shipped 2026-06-15) — [Full archive](./milestones/v1-ROADMAP.md)
- 🚧 **v2.0 PRFP — Pipeline Redesign from First Principles** — Phases 7-12 (in planning)

<details>
<summary>✅ v1 — Movie-Experts Suite v2 (Phases 0-6) — SHIPPED 2026-06-15</summary>

- ✅ Phase 0: AUDIT + Eval Skeleton (BLOCKER GATE) — completed 2026-06-15
- ✅ Phase 1: EXPERT-COMPLI (Legal Gate) — completed 2026-06-15
- ✅ Phase 2: EXPERT-HOOK (Commercial Engine) — completed 2026-06-15
- ✅ Phase 3: Top-4 Existing Experts RAG — completed 2026-06-15 (dry-run; live deferred)
- ✅ Phase 4: EXPERT-CINE (Camera Language) — completed 2026-06-15
- ✅ Phase 5: Remaining 10 + EXPERT-PROD (v1.5) — completed 2026-06-15
- ✅ Phase 6: Full Eval + Bilingual + README — completed 2026-06-15 (doc pass; live run deferred to operator)

See [`.planning/milestones/v1-ROADMAP.md`](./milestones/v1-ROADMAP.md) for full v1 phase details.

</details>

---

## Critical Path

```
7 → 8 → 11 → 12
      ↘
        9 (parallel with 8, starts when 7 produces node IDs)
        10 (parallel with 8, starts when 7 produces "AI-limits" definition)
```

- **Phase 7 (A)** is the bottleneck — nothing else may start until the first-principles pass produces a defensible candidate node set.
- **Phase 9 (C)** and **Phase 10 (D)** run fully parallel with **Phase 8 (B)** once Phase 7 emits node IDs / AI-limits definition.
- **Phase 11 (E)** waits on 8 + 9 + 10 all stable.
- **Phase 12 (F)** is finalization — waits on 11.

---

## Phases

- [ ] **Phase 7: First-Principles Derivation** — Musk-style reasoning trace producing the candidate node set (the epistemic anchor)
- [ ] **Phase 8: Node DAG + Per-Node Specs** — YAML-canonical + Markdown-rendered DAG and per-node spec sheets
- [ ] **Phase 9: 102-Book Corpus Traceability** — bidirectional book ↔ node coverage matrix + per-anchor tags
- [ ] **Phase 10: LLM-Creative-Distillation Deep-Dive** — standalone horizontal sub-doc on creativity / self-consistency / prompts / fail modes
- [ ] **Phase 11: Cross-Comparisons + Dual-Repo Handoff** — non-binding delta analyses vs existing 8 phases + 26 skills + handoff contract
- [ ] **Phase 12: Finalization (Governance + Open Questions + README)** — living-doc rules, known unknowns, audit trail, executive summary

---

## Phase Details

### Phase 7: First-Principles Derivation
**Goal:** A reader can follow an unbroken Musk-style first-principles reasoning chain from irreducible questions ("what does the audience ultimately receive?", "what can AI actually accelerate?", "what can AI never replace?") to a candidate node set — and can challenge every step.
**Depends on:** Nothing (bottleneck; nothing else may start until 7 emits the candidate node set)
**Requirements:** DERIV-01, DERIV-02, DERIV-03, DERIV-04, DERIV-05, DERIV-06, DERIV-07, DERIV-08 (8)
**Success Criteria** (what must be TRUE):
  1. A reader can read `00-FIRST-PRINCIPLES.md` end-to-end and reconstruct the candidate node set without inferring any missing logical step (no "obviously", no jumps from analogy to conclusion).
  2. Every candidate node carries a `derivation` field that defends its existence from first principles (not "every pipeline has this"), and an `alternatives-considered` log naming at least one node considered and rejected for this slot.
  3. Every core claim in the derivation trace is tagged with one of {physical, psychological, platform-algorithmic, tool-capability}, so volatile vs stable assumptions are machine-distinguishable.
  4. Every node's core assumptions are classified as `contingent` vs `validated-invariant`, and the derivation explicitly cites a STACK §1.4 corpus subset for each first-principles question (not corpus-blind).
  5. The derivation explicitly walks the 6 PITFALLS §1 + §5 Musk-method failure modes and shows how each was avoided (audit checklist at end of section).
**Plans:** TBD

### Phase 8: Node DAG + Per-Node Specs
**Goal:** A reader (human reviewer or downstream tool) can read a machine-derivable, human-reviewable DAG of 8-15 nodes where each node declares its full spec (core task, I/O, AIGC transformation, traditional anchor, cost/latency/model-horizon, critic pairing, theory_critic placement) and can defend every node against the C1-C7 selection criteria.
**Depends on:** Phase 7 (needs candidate node IDs + AI-limits definition)
**Requirements:** NODE-01, NODE-02, NODE-03, NODE-04, NODE-05, NODE-06, NODE-07, NODE-08, NODE-09, META-05, META-06 (11 — includes META-05 because it constrains every node's `cost_budget`, and META-06 because it shapes theory_critic edges)
**Success Criteria** (what must be TRUE):
  1. The DAG exists in 3 representations — YAML canonical (`nodes.yaml` + `edges.yaml`), Markdown rendered (`01-NODE-DAG.md`), Mermaid visual — and regenerating Markdown+Mermaid from YAML is reproducible.
  2. Every node in the DAG has all 4 core fields (`core_task` / `I/O contract` / `AIGC transformation point` / `traditional experience anchor`) AND all 8 STACK supplementary fields (`success_criteria ≥1 quantified`, `fail_modes`, `fallback_strategy`, `dependencies`, `complexity_class`, `ai_capability_assumption`, `non_ai_alternative`, `rationale_for_existence`) AND all 3 budget fields (`cost_budget` within the META-05 ¥1000-10000/episode ceiling, `latency_budget`, `model_horizon`) populated and non-empty.
  3. Every node has passed an explicit C1-C7 selection check (FEATURES §5); nodes failing any of the 7 are NOT in the DAG, and the rejection is logged.
  4. Every generation-type node has a paired critic node OR a self-critic step with a quantified metric; any generation node lacking a critic has a written justification.
  5. `theory_critic` appears only as a `consultative` vertical edge (per META-06, creator-pulled — not auto-invoked, not a blocking linear gate), and model names appear ONLY in a dated annex — the canonical node spec is capability-spec, never brand-named (NODE-08).
**Plans:** TBD

### Phase 9: 102-Book Corpus Traceability
**Goal:** A reader can verify, for every derived node, which 102-book corpus sources inform it (and at what strength), AND for every cited source, which nodes it informs — with the corpus anchor's `applicable_form`, original Chinese terminology, principle-vs-workflow separation, challenge-source engagement, and verification date all machine-checkable.
**Depends on:** Phase 7 (node IDs only — does NOT need full Phase 8 specs to begin)
**Requirements:** CORPUS-01, CORPUS-02, CORPUS-03, CORPUS-04, CORPUS-05, CORPUS-06, CORPUS-07 (7)
**Success Criteria** (what must be TRUE):
  1. A bidirectional `corpus-trace.yaml` exists — readers can query both "node → supporting books" (forward) and "book → informed nodes" (reverse) without manual lookup.
  2. Every corpus anchor carries an `applicable_form` tag (长片 / 微电影 / 短剧 / universal) — no 长片 anchor silently justifies a 短剧-specific node without an explicit translation argument.
  3. For every node, at least 1 corpus source that DISAGREES with the node's design is cited and engaged (challenge-source engagement — prevents cherry-picking); 0-citation nodes are explicitly marked AIGC-native with a written rationale (no fake-tradition masquerade).
  4. Each anchor separates principle (likely still valid) from workflow (likely obsolete in AIGC) AND preserves the Chinese original term alongside any English gloss.
  5. Every anchor has a `Last-verified` stamp consistent with v1's LICENSE pattern, enabling downstream corpus-drift detection.
**Plans:** TBD

### Phase 10: LLM-Creative-Distillation Deep-Dive
**Goal:** A reader can read a standalone sub-doc that operationally defines LLM creativity (novelty within inviolable constraints, not randomness), specifies the self-consistency verification mechanism, references ≥3 LLM-story-gen papers for prompt strategy, handles the platform-vs-art tension without dogma, and wires creativity back to the DAG's `creative_source` node rather than floating in the abstract.
**Depends on:** Phase 7 (the "what AI can/cannot do" definition falls out of the derivation)
**Requirements:** CREATIVE-01, CREATIVE-02, CREATIVE-03, CREATIVE-04, CREATIVE-05, CREATIVE-06, CREATIVE-07 (7)
**Success Criteria** (what must be TRUE):
  1. A standalone `04-LLM-CREATIVE-DISTILLATION.md` exists covering all 4 dimensions: creativity definition, self-consistency mechanism, prompt strategy, fail modes.
  2. Creativity is operationally defined as "novelty within inviolable constraints" with explicit lists of (a) inviolable constraints and (b) open-for-novelty dimensions — a reader can distinguish "creative" from "random".
  3. The self-consistency check mechanism is concretely specified as `consistency-context input + logic-critic` (anti-hallucinated-logic), and the prompt strategy cites ≥3 STACK §5 LLM-story-gen papers (not invented from vibes).
  4. Platform-vs-art tension (短剧 convention vs artistic value) is explicitly addressed without picking a dogmatic side, AND a template library (≥2 narrative-arc templates, not a single Save-the-Cat / Hero's-Journey) is specified.
  5. The sub-doc links back to the DAG's `creative_source` node via an explicit novelty-pressure mechanism — creativity is wired to the DAG, not floating.
**Plans:** TBD

### Phase 11: Cross-Comparisons + Dual-Repo Handoff
**Goal:** A reader at either downstream repo (hermes-agent skills team OR kais-movie-agent impl team) can pick up a non-binding handoff contract that maps new DAG nodes ↔ existing artifacts (26 skills / 8 phases / lib modules), declares explicit ownership, baselines against a recorded git SHA, ships a 1-2 page impl cheatsheet, and explains convergence (where new DAG agrees with existing) — not just divergence.
**Depends on:** Phase 8 + Phase 9 + Phase 10 all stable (need final node set, corpus trace, and LLM-distillation patterns to compare against)
**Requirements:** HANDOFF-01, HANDOFF-02, HANDOFF-03, HANDOFF-04, HANDOFF-05, HANDOFF-06, HANDOFF-07, HANDOFF-08, HANDOFF-09 (9)
**Success Criteria** (what must be TRUE):
  1. The handoff plan is explicitly labeled `binding: non_binding_recommendation` and downstream consumers know they decide in their own future milestones (no compulsion).
  2. `skills-mapping.yaml` maps every new DAG node ↔ existing 26 movie-experts skills, preserving v1 FOUND-08 frozen `expert_id` rule; `kais-migration-matrix.yaml` maps every node ↔ existing kais-movie-agent phases + lib modules, with the kais-movie-agent `baseline_ref` git SHA recorded as the design-vs-impl drift baseline.
  3. The ownership matrix distinguishes design-intent layer (hermes-agent) / implementation layer (kais-movie-agent) / co-owned DAG (changes require sign-off from both) — a reader knows who owns what post-handoff.
  4. A date-stamped versioning scheme (e.g., `design-2026-06-16-prfp`) with `supersedes` / `superseded_by` is in place, AND a 1-2 page impl-cheatsheet annex exists for kais-movie-agent onboarding.
  5. The convergence log explains where the new DAG AGREES with the existing pipeline (and why agreement is correct, not just where it diverges); `COMPARISON-VS-8-PHASES.md` + `COMPARISON-VS-26-SKILLS.md` both exist as non-binding delta analyses authored AFTER Phases 7-10 (contamination-safe).
**Plans:** TBD

### Phase 12: Finalization (Governance + Open Questions + README)
**Goal:** The design-doc suite ships with living-doc governance rules (enforced by a lint script), an honest OPEN-QUESTIONS.md feeding downstream research, an append-only CHANGELOG audit trail, Decision/Rationale/Outcome entries for every key call, and a 3-page executive summary readable by a non-author in 10 minutes — plus verified META exit-checks that no SKILL.md / no kais-movie-agent code was touched and bilingual policy was followed.
**Depends on:** Phase 11
**Requirements:** GOV-01, GOV-02, GOV-03, GOV-04, GOV-05, GOV-06, META-01, META-02, META-03, META-04 (10 — META-01/02/03/04 land here as the final exit-check; this is the load-bearing phase for the no-touch / bilingual / location invariants)
**Success Criteria** (what must be TRUE):
  1. `08-GOVERNANCE.md` documents rules G1-G7 (node addition requires re-derivation; AIGC updates require marginal-value delta; corpus changes require source verification; status transitions require all review gates) AND `scripts/validate_design.py` (~30-line lint) enforces them as a runnable pre-commit hook.
  2. `09-OPEN-QUESTIONS.md` is mandatory and non-empty — every gap surfaced in SUMMARY.md §"Gaps to Address" is transferred here (no hidden ambiguities) to feed downstream research phases.
  3. `10-CHANGELOG.md` is append-only (date / what / why / who per entry) and every key design decision has a Decision / Rationale / Outcome record (v1 PROJECT.md pattern — v1 RETROSPECTIVE validated it).
  4. The README contains a 3-page executive summary (non-author-readable in 10 min: derived DAG diagram + one-paragraph shape rationale + top-5 diffs vs existing 8 phases + top-3 deferred risks).
  5. META exit-checks pass at milestone close: zero SKILL.md edits under `skills/movie-experts/` (META-01); zero `.js`/`.py` edits under `kais-movie-agent/` except `scripts/validate_design.py` (META-02); design docs follow EN-structure + CN-prose bilingual policy (META-03); all artifacts physically live under `.planning/research/v2-pipeline-design/` in hermes-agent (META-04).
**Plans:** TBD

---

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 0. AUDIT + Eval Skeleton | v1 | 4/4 | ✓ Complete | 2026-06-15 |
| 1. EXPERT-COMPLI | v1 | 3/3 | ✓ Complete | 2026-06-15 |
| 2. EXPERT-HOOK | v1 | 3/3 | ✓ Complete | 2026-06-15 |
| 3. Top-4 Existing Experts RAG | v1 | 5/5 | ✓ Complete | 2026-06-15 |
| 4. EXPERT-CINE | v1 | 1/1 | ✓ Complete | 2026-06-15 |
| 5. Remaining 10 + EXPERT-PROD (v1.5) | v1 | 1/1 | ✓ Complete | 2026-06-15 |
| 6. Full Eval + Bilingual + README | v1 | 1/1 | ✓ Complete | 2026-06-15 |
| 7. First-Principles Derivation | v2.0 | 0/? | Not started | - |
| 8. Node DAG + Per-Node Specs | v2.0 | 0/? | Not started | - |
| 9. 102-Book Corpus Traceability | v2.0 | 0/? | Not started | - |
| 10. LLM-Creative-Distillation Deep-Dive | v2.0 | 0/? | Not started | - |
| 11. Cross-Comparisons + Dual-Repo Handoff | v2.0 | 0/? | Not started | - |
| 12. Finalization (Governance + Open Questions + README) | v2.0 | 0/? | Not started | - |

---

## Coverage Map (all 52 v2.0 requirements mapped)

| Phase | Requirements | Count |
|-------|--------------|-------|
| 7 — First-Principles Derivation | DERIV-01..08 | 8 |
| 8 — Node DAG + Per-Node Specs | NODE-01..09, META-05, META-06 | 11 |
| 9 — 102-Book Corpus Traceability | CORPUS-01..07 | 7 |
| 10 — LLM-Creative-Distillation Deep-Dive | CREATIVE-01..07 | 7 |
| 11 — Cross-Comparisons + Dual-Repo Handoff | HANDOFF-01..09 | 9 |
| 12 — Finalization (Governance + Open Questions + README) | GOV-01..06, META-01, META-02, META-03, META-04 | 10 |
| **Total mapped** | | **52** |
| **Orphaned** | | **0** |

**Cross-cutting META assignment rationale:**
- **META-01/02/03/04 → Phase 12** — these are exit-checks (no-touch policy, bilingual policy, location invariant) that the finalization phase verifies at milestone close. Putting them earlier would be premature; Phase 12 is the load-bearing verification point.
- **META-05 → Phase 8** — the ¥1000-10000/episode cost ceiling directly constrains every node's `cost_budget` field, which is a Phase 8 deliverable. The ceiling must be set before cost budgets can be populated.
- **META-06 → Phase 8** — theory_critic's "creator-pulled, not auto-invoked" trigger mode shapes the DAG's `consultative` edge type, which is a Phase 8 deliverable.

> **Note on count:** REQUIREMENTS.md flagged "51 total - 1 for HANDOFF-09/HANDOFF-01 overlap - 待 roadmapper 验证". On review, HANDOFF-01 (non-binding handoff plan declared) and HANDOFF-09 (comparison-vs-existing artifacts exist) are distinct REQs addressing different artifacts (the handoff contract vs the comparison analyses). No overlap; actual count = **52** = 8+9+7+7+9+6+6. All mapped.

---

## Research Flags (phases likely needing deeper research during planning)

- **Phase 7 (First-Principles Derivation):** HIGH research load — Musk-method primary-source verification against Isaacson biography before citing (PITFALLS §5 Open Question #4); epistemic-status tagging framework; steelman-the-elimination methodology. Recommend `/gsd:plan-phase --research-phase 7`.
- **Phase 8 (Node DAG + Specs):** MEDIUM research load — 2026-Q2 AI capability stability survey (which `ai_capability_assumption` entries are `stable_2026` vs `evolving` vs `research_bet`); per-node cost/latency budget validation against current platform economics (PITFALLS Open Question #1).
- **Phase 10 (LLM-Creative-Distillation):** MEDIUM research load — STACK §5 provides 8 references but prompt-strategy subtopics may need Awesome-Story-Generation follow-ups.
- **Phases 9, 11, 12:** Standard / well-precedented patterns. No new research needed.

---

*Roadmap created: 2026-06-16 via /gsd:new-project (roadmapper agent) for milestone v2.0 PRFP*
*v1 archive: milestones/v1-ROADMAP.md · Source synthesis: research/SUMMARY.md + research/ARCHITECTURE.md*
