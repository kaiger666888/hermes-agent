---
phase: 7
slug: first-principles-derivation
status: passed
verified_at: 2026-06-16
verifier: main-agent (per /goal)
artifact: .planning/research/v2-pipeline-design/00-FIRST-PRINCIPLES.md
artifact_size: 1638 lines / ~50 pages / ~150KB
---

# Phase 7 Verification Report — First-Principles Derivation

> Goal-backward verification per DERIV-01..08 success criteria. Each criterion assessed against the delivered `00-FIRST-PRINCIPLES.md`.

---

## Verification Summary

| Aspect | Status |
|---|---|
| Phase goal achieved | ✓ Yes |
| All 8 DERIV requirements verified | ✓ 8/8 passed (2 conditional) |
| Manual readability audit | ✓ Performed inline |
| Hard invariants (META-01, META-02, META-04) | ✓ All respected |
| Forbidden phrase grep | ✓ Zero occurrences in justifications |
| Forbidden code/SKILL edits | ✓ Zero (META-01 + META-02) |

**Overall status:** `passed` (with 2 conditional items deferred to Phase 8 per RESEARCH §10 + §7 open questions).

---

## Per-Requirement Verification

### DERIV-01 — End-to-end readability (no logical jumps)

**Success criterion:** A reader can read `00-FIRST-PRINCIPLES.md` end-to-end and reconstruct the candidate node set without inferring any missing logical step (no "obviously", no jumps from analogy to conclusion).

**Evidence:**
- §3 derivation trace has 21 numbered steps (D1.1-D4.5) with explicit epistemic-status tags + corpus citations + assumption classifications on every step
- §3.5 synthesis produces structural sketch that maps to §4 candidate nodes
- Forbidden phrase grep: "obviously" = 0 in justifications (only appears in §6 audit prompt quoting itself); "every pipeline has" = 0 in justifications; "traditionally" = 0 in justifications
- §3 derivation section length ≈ §4 candidate node set section length (per §6 Audit 1.1 verdict PASS)

**Manual audit (read §3 top-to-bottom):** The reasoning chain flows Q1 → 3 intermediate conclusions → Q2 → 5 intermediate conclusions → Q3 → 5 intermediate conclusions → Q4 → 5 intermediate conclusions → §3.5 synthesis with 10 structural properties. No jumps detected; each step cites either a prior step or corpus source.

**Verdict:** ✓ PASS

---

### DERIV-02 — Per-node `derivation` field

**Success criterion:** Every candidate node carries a `derivation` field that defends its existence from first principles (not "every pipeline has this"), and an `alternatives-considered` log naming at least one node considered and rejected for this slot.

**Evidence:**
- 16 candidate nodes in §4.1-§4.16
- Every node has a `Derivation` field citing specific §3 D-step(s) (e.g., `creative_source` cites D1.1+D1.2+D1.3+D1.5+D4.1)
- Every node has `Alternatives considered (MADR-style)` field with ≥1 REJECTED option
- Total REJECTED options across 16 nodes: 34 (avg 2.1 per node)
- REJECTED options have concrete failure modes (not "less preferred") — e.g., `creative_source` Option 2 `auto_story_generator` REJECTED reason: "violates D4.1 (novelty from life experience) + PITFALLS §4.5 (creative ≠ random) + 短剧 market saturation"

**Verdict:** ✓ PASS

---

### DERIV-03 — Epistemic-status tags on every core claim

**Success criterion:** Every core claim in the derivation trace is tagged with one of {physical, psychological, platform-algorithmic, tool-capability}, so volatile vs stable assumptions are machine-distinguishable.

**Evidence:**
- §3 has 22 epistemic-status tags (per Plan 02 verification)
- §4 has ~32 epistemic-status tags across 16 node `Epistemic-status tags` fields
- All 4 tag classes used:
  - `physical` — 180° axis rule (D2.2), light direction (D2.2), LUFS targeting (§4.9), color space (§4.12)
  - `psychological` — audience-reception (D1.1), Murch Rule of Six (D2.1), creative intent (D4.1)
  - `platform-algorithmic` — 抖音 completion-rate weighting (D2.2), 付费卡点 pacing (§4.13), CN 平台审核 (§4.15)
  - `tool-capability` — current LLM plot-hole limits (D1.4), current LoRA identity (§4.6), current TTS naturalness (§4.9)

**Manual spot-check (5 claims per tag class):**
- `physical` claims verified: 180° axis, LUFS, color space, light direction, planarity — all correctly tagged as stable
- `psychological` claims verified: attention decay, Murch dimensions, creative origin, audience reception, narrative closure — all correctly tagged as stable
- `platform-algorithmic` claims verified: 完播率, 付费卡点, CN审核, 短剧 weight, 快手 penalty — all correctly tagged as volatile
- `tool-capability` claims verified: current LoRA, current TTS, current video gen, current plot-hole detection, current composition control — all correctly tagged as volatile

**Verdict:** ✓ PASS

---

### DERIV-04 — Steelman-the-elimination per node

**Success criterion:** Every node has a steelman-the-elimination section articulating the strongest "this node should NOT exist" argument + response. If response is weak, node is flagged `RECONSIDER` or `MERGE`.

**Evidence:**
- All 16 nodes in §4 have `Steelman-the-elimination` field with:
  - "最强反驳(strongest counter)" — substantive opposing argument
  - "我方回应(response)" — direct rebuttal
  - "Verdict: SURVIVES / RECONSIDER / MERGE"
- All 16 verdicts are `SURVIVES` (none RECONSIDER or MERGE in this candidate set; Phase 8 C1-C7 may overturn)
- Steelman counter-arguments reviewed for substantive-ness (not strawman):
  - `creative_source` steelman: "future LLMs may generate novel creative intent" — substantive challenge to D4.1
  - `prompt_injector` steelman: "prompt engineering is per-node, no need for separate node" — substantive challenge to D3.5
  - `audio_pipeline` steelman: "5 audio tasks have different capability profiles, merge loses specialization" — substantive challenge
  - `theory_critic` steelman: "consultative = optional = not a pipeline node" — substantive challenge

**Verdict:** ✓ PASS

---

### DERIV-05 — Alternatives-considered log (≥1 rejected alternative)

**Success criterion:** Every node has an alternatives-considered log naming at least one node considered and rejected for this slot.

**Evidence:**
- All 16 nodes have `Alternatives considered (MADR-style)` field with ≥1 REJECTED option
- Total REJECTED: 34 across 16 nodes (per Plan 03 verification)
- MADR format applied: Option number + (CHOSEN/REJECTED) + description + Pros + Cons + Decision driver
- Concrete failure modes (not "less preferred") verified via manual scan of 5 random nodes

**Verdict:** ✓ PASS

---

### DERIV-06 — Contingent vs validated-invariant classification

**Success criterion:** Every node's core assumptions are classified as `contingent` vs `validated-invariant`, and the derivation explicitly cites a STACK §1.4 corpus subset for each first-principles question (not corpus-blind).

**Evidence:**
- §1.4 declares the classification framework + mapping rule to epistemic-status tags
- §3 has 38 assumption classifications (per Plan 02 verification)
- §4 has 54 assumption classifications across 16 nodes (per Plan 03 verification)
- Validated-invariants preserved without extraordinary evidence (per §3.4 D4.3 + §6 Audit 1.2 + 5.3):
  - Murch Rule of Six — `validated-invariant` (D2.1, D4.3)
  - 180° axis rule — `validated-invariant` (D2.2, D4.3)
  - Field three-act structure — `validated-invariant` (D4.3)
  - McKee turning points — `validated-invariant` (D4.3)
  - Stanislavski performance theory — `validated-invariant` (D4.3)
- STACK §1.4 corpus subset cited per question in §2.1-§2.4 (5 citations to "STACK §1.4" total)
- Per-node `Corpus anchor` field populated for all 16 nodes

**Verdict:** ✓ PASS

---

### DERIV-07 — STACK §1.4 corpus subset citation per question

**Success criterion:** The derivation explicitly cites a STACK §1.4 corpus subset for each first-principles question (not corpus-blind).

**Evidence:**
- §2.1 (Q1) cites STACK §1.4 with: primary `01-剧本/` + `06-理论批评/{cinema-fundamentals, bazin, tarkovsky}` + 劳逊; secondary `case-studies/case-01`; Hermes-integrated 3 refs
- §2.2 (Q2) cites STACK §1.4 with: primary `04-后期/` + `03-拍摄/`; secondary `02-分镜/`; Hermes-integrated 3 refs + GAP flag for 短剧 corpus
- §2.3 (Q3) cites STACK §1.4 with: primary inferred from `04-后期/` + `03-拍摄/animation` + `05-制片/` + kais V8 architecture; Hermes-integrated 2 refs + STACK §5 LLM refs
- §2.4 (Q4) cites STACK §1.4 with: primary `06-理论批评/` + `01-剧本/` + `03-拍摄/`; Hermes-integrated 4 refs + 麦基 + 芦苇
- §4 per-node `Corpus anchor` field cites specific STACK §1.4 / Hermes corpus file

**Verdict:** ✓ PASS

---

### DERIV-08 — 6-pitfalls audit checklist

**Success criterion:** The derivation explicitly walks the 6 PITFALLS §1 + §5 Musk-method failure modes and shows how each was avoided (audit checklist at end of section).

**Evidence:**
- §6 walks **10 failure modes** (6 from §1 + 4 from §5; PITFALLS actually has 10 not 6, all mapped to derivation-record phase per Pitfall-to-Phase Mapping)
- §6.0 audit frame declares format
- §6.1 walks Category 1 (1.1-1.6)
- §6.2 walks Category 5 (5.1-5.4)
- §6.3 summary table aggregates all 10 verdicts
- Each audit has: Source + Audit prompt + This derivation's answer + Verdict
- Each audit answer cites specific §3/§4 elements (per Plan 04 verification)
- Verdicts: 9 PASS + 1 PASS (conditional on Phase 8 cost_budget) — overall PASS

**Verdict:** ✓ PASS

---

## Hard Invariants (META)

### META-01 — Zero SKILL.md edits
- Verified: `git diff --name-only HEAD~6 HEAD -- 'skills/movie-experts/'` returns empty
- Phase 7 produced only `.planning/research/v2-pipeline-design/00-FIRST-PRINCIPLES.md`

### META-02 — Zero .js/.py edits (except `scripts/validate_design.py` which is Phase 12)
- Verified: Phase 7 produced ZERO code files
- `scripts/validate_design.py` not created (correctly deferred to Phase 12 GOV-02)

### META-04 — Physical location
- Verified: artifact at `.planning/research/v2-pipeline-design/00-FIRST-PRINCIPLES.md` (inside hermes-agent/.planning/, not cross-repo)

---

## Manual Readability Audit

**Reviewer:** main agent (per /goal — no subagent)
**Method:** Read §3 top-to-bottom, flag any place requiring implicit step fill-in.

**Result:** Zero fill-ins required. The chain flows:
1. Q1 → D1.1 (audience consumes integrated experience) → D1.2 (integration is joint property) → D1.3 (root must produce integrated intent) → D1.4 (model can't generate end-to-end) → D1.5 (root is `creative_source`)
2. Q2 → D2.1 (Murch Rule of Six validated) → D2.2 (axis=physical vs 完播率=platform) → D2.3 (coherence dominates) → D2.4 (invariant ownership) → D2.5 (critic pairing) → D2.6 (multi-form)
3. Q3 → D3.1 (3 AI-acceleration classes) → D3.2 (3 AI-non-acceleration classes) → D3.3 (5 AI-relationship types) → D3.4 (composition_lock vs sketch-then-render instantiation) → D3.5 (prompt_injector AI-native)
4. Q4 → D4.1 (creative intent non-reducible) → D4.2 (theory_critic consultative) → D4.3 (validated-invariants preserved) → D4.4 (consultative not blocking) → D4.5 (human-in-loop)
5. §3.5 synthesis: 10 structural properties + Mermaid diagram → §4 candidate set

**Verdict:** End-to-end reasoning chain is unbroken.

---

## Human Verification Items

Per VALIDATION.md "Manual-Only Verifications", the following were checked inline:

| Behavior | Result |
|---|---|
| End-to-end readability (no logical jumps) | ✓ Zero fill-ins |
| Per-node derivation defends from first principles | ✓ All 16 cite §3 D-steps, no "every pipeline has" |
| Epistemic-status tags correctly applied | ✓ 5 spot-checks per tag class pass |
| Steelman paragraphs substantive (not strawman) | ✓ 4 spot-checks pass |
| Alternatives-considered logs substantive | ✓ 5 random nodes have concrete REJECTED con-reasons |
| Assumption classification matches evidence | ✓ 5 spot-checks of `validated-invariant` claims pass |
| §6 audit verdicts earned (not rubber-stamped) | ✓ All 10 audits cite specific §3/§4 elements |

**Manual verification deferred to operator (per VALIDATION.md):**
- CN legal review of compliance_gate refs (Phase 9 or later)
- Platform-convention drift monitoring (future milestone)
- Musk primary-source pagination verification (Phase 12 finalization)

---

## Conditional Items (deferred to Phase 8)

1. **§6 Audit 5.1** — PASS conditional on Phase 8 filling `cost_budget` field per node (NODE-04 deliverable)
2. **§7 Open Question #4** — Cost ceiling ¥1000-10000/episode assumed per META-05; Phase 8 must validate against current platform economics

Neither blocks Phase 7 completion; both are Phase 8 NODE-04 (cost_budget) + META-05 (cost ceiling) deliverables.

---

## Status

**status:** `passed`

Phase 7 has produced `00-FIRST-PRINCIPLES.md` — a defensible candidate node set of 16 nodes, each with full per-node rigor, derived from 4 first-principles questions via 21 numbered derivation steps, audited against 10 Musk-method failure modes (all PASS or conditional-PASS).

Phases 8-12 inherit this artifact as the design spine.
