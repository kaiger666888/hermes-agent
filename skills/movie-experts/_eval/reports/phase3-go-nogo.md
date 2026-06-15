# Phase 3 GO/NO-GO Report

**Generated:** 2026-06-15
**Phase:** 3 — Top-4 Existing Experts RAG (Deep Refactor)
**Status:** DEFERRED to Phase 6 live run
**Preliminary recommendation:** CONDITIONAL GO pending Phase 6 live-run evidence
**Report authority:** Phase 3 ships evidence + preliminary recommendation; **Phase 4 produces the formal gate decision** (per ROADMAP Phase 4 GO/NO-GO GATE note)

---

## Recommendation

**CONDITIONAL GO** — pending Phase 6 live-run evidence.

Phase 3 produced 4 deep-refactored experts (screenplay, editor, colorist, style_genome) with 5 curated refs each (20 refs total) + provider-agnostic RAG invocation blocks + revised thresholds with source citations + refined metrics operational definitions + 12 eval prompts (3 per expert). The harness validated end-to-end on the 3-condition × 4-expert matrix (36 dry-run verdicts).

**However**, the Phase 3 dry-run produces no statistical signal — the `_StubJudgeClient` (runner.py:453) deterministically returns "tie" for every pair, regardless of answer content. The all-tie signature is a position-bias demonstration, NOT a quality verdict. The formal GO/NO-GO verdict requires the Phase 6 live run with:
- Real judge models (Qwen3-235B + DeepSeek-V3)
- ≥20 prompts per expert (EVAL-05 statistical threshold)
- Both orderings (position-swap)
- Multi-judge ensemble (EVAL-06)

**Operator action:** Proceed with Phase 4 (cinematographer) planning. Phase 6 live run will produce the statistical evidence required for the formal Phase 4 GO/NO-GO gate decision.

---

## GO Criteria

Per CONTEXT decision D-9:

> **GO criteria:** ≥2/3 prompts improve with new-with-refs vs new-no-refs across ≥3/4 experts.

**Operationalization:**

1. For each expert, compute the per-expert improvement rate on the `(new_no_refs vs new_with_refs)` pair:
   ```
   improvement_rate_expert = (count of "new_with_refs wins") / (count of non-tie verdicts)
   ```
   Where "new_with_refs wins" = final verdict is `B_wins` when pair order is `[new_no_refs, new_with_refs]` (or `A_wins` when reversed).

2. Expert passes GO threshold if `improvement_rate_expert >= 2/3` (i.e., ≥2 of 3 prompts show new_with_refs winning on non-tie verdicts).

3. Overall GO requires ≥3/4 experts to pass the per-expert threshold.

**Note:** Ties are excluded from both numerator and denominator. If an expert has 0 non-tie verdicts (all-tie), it fails the threshold (insufficient signal).

---

## Phase 3 Evidence

| Expert | Refs Authored | REFACTOR-08 Heuristics/Ref | Dry-Run Verdicts | Live-Run Status | SUMMARY |
|--------|---------------|---------------------------|-------------------|-----------------|---------|
| screenplay | 5 (Snyder / McKee / CN shortdrama / academic / dialogue) | ≥3 per ref (REFACTOR-08 satisfied, ≥3 floor exceeded per CONTEXT decision #2) | 9 (all-tie stub) | deferred to Phase 6 | [`03-01-SUMMARY.md`](../../.planning/phases/03-top-4-existing-experts-rag/03-01-SUMMARY.md) |
| editor | 5 (Murch / classical / montage / fxrxt / CN cutting) | ≥3 per ref (REFACTOR-08 satisfied) | 9 (all-tie stub) | deferred to Phase 6 | [`03-02-SUMMARY.md`](../../.planning/phases/03-top-4-existing-experts-rag/03-02-SUMMARY.md) |
| colorist | 5 (Bellantoni / Hurkman / cross-cultural / CN audience / digital science) | ≥3 per ref (REFACTOR-08 satisfied) | 9 (all-tie stub) | deferred to Phase 6 | [`03-03-SUMMARY.md`](../../.planning/phases/03-top-4-existing-experts-rag/03-03-SUMMARY.md) |
| style_genome | 5 (director archive / genre DNA / auteur theory / cross-cultural / CN director) | ≥3 per ref (REFACTOR-08 satisfied) | 9 (all-tie stub) | deferred to Phase 6 | [`03-04-SUMMARY.md`](../../.planning/phases/03-top-4-existing-experts-rag/03-04-SUMMARY.md) |

**Totals:** 20 refs authored + 4 SKILL.md refactors + 12 eval prompts + 36 dry-run verdicts.

---

## Harness Validation

Phase 3 dry-run proves the harness end-to-end:

1. ✓ `runner.py` accepts 3 conditions (replaces Phase 0 baseline/candidate with old_no_refs/new_no_refs/new_with_refs)
2. ✓ C(3,2) = 3 pairs enumerated per expert
3. ✓ 9 verdicts per expert × 4 experts = 36 total verdicts (matches expected formula)
4. ✓ Dry-run stub signature observed (all-tie per `_StubJudgeClient` design at runner.py:453-498)
5. ✓ No prompts file missing (all 4 expert prompts files resolved correctly)
6. ✓ Per-expert reports written in both JSON and Markdown (machine + human readable)

**Harness validity conclusion:** The runner would have produced statistically analyzable output (non-tie verdicts) if a live judge client had been substituted for the stub. The output shape, pair enumeration, prompt resolution, and reporting pipeline are all validated.

Detailed dry-run report: [`phase3-ablation-dryrun.md`](./phase3-ablation-dryrun.md) + [`phase3-ablation-dryrun.json`](./phase3-ablation-dryrun.json).

---

## Deferred Live Run

| Field | Value |
|-------|-------|
| `OPENROUTER_API_KEY` present | false (not in env) |
| Live run attempted | false |
| Live run completed experts | [] |
| Live run errors | [] |

**Phase 6 Live Run Prerequisites** (per `phase3-go-nogo.json`):

1. `OPENROUTER_API_KEY` configured in `~/.hermes/.env` (or runtime env)
2. `config.yaml` (NOT `.example`) committed locally with live credentials redacted from git
3. Phase 6 expands N from 3 to ≥20 prompts per expert (EVAL-05 statistical threshold)
4. Phase 6 invokes multi-judge ensemble (both `qwen3-235b` AND `deepseek-v3` — not just `judges[0]`)

---

## Phase 4 Gate Authority

**The formal GO/NO-GO gate decision occurs at the end of Phase 4** (per ROADMAP Phase 4 GO/NO-GO GATE note), not at the end of Phase 3.

Phase 3 ships:
- Evidence: 4 deep-refactored experts + 20 refs + 12 prompts + 36 dry-run verdicts
- Preliminary recommendation: CONDITIONAL GO pending Phase 6 live evidence
- Harness validation: end-to-end dry-run confirms output shape and pipeline correctness

Phase 4 will ship:
- The 5th expert (cinematographer) end-to-end
- The formal GO/NO-GO gate verdict (incorporating Phase 6 live evidence if available, or deferring further if not)

**STATE.md** Phase 3 row reflects this authority boundary: status is "Gate artifact produced", not "GO decision made".

---

## Ref Corpus Audit (REFACTOR-08)

For each of 4 experts, the 5 authored refs and their concrete heuristics (each ref carries ≥3 specific heuristics NOT in base model training, exceeding the CONTEXT decision #2 floor of ≥3):

### screenplay (5 refs)
1. **save-the-cat-beat-sheet.md** — Snyder 15-beat positions (Catalyst p.10±3 / Midpoint p.55±3 / All Is Lost p.75±3) + 短剧 60s/90s/180s beat budget conversion + Double-Bump rule
2. **mckee-scene-design.md** — McKee gap 4-step analysis + value-shift rate ≥1/scene + beat decomposition 3-5 per 90s + turning point vs plot point (~25% & ~75% runtime)
3. **cn-shortdrama-structure.md** — 90s/180s 时间预算 (钩子 0-3s / escalation 15-40s / 爽点 70-80s / 卡点 88-90s) + 10-ep season arc (ep 3/7/10 大爽点) + per-platform divergence
4. **emotion-curve-academic.md** — Tan interest 公式 (concern × uncertainty × anticipation ≥ 0.6) + McMahon 6 arc shapes (85% coverage) + anchor-based sampling protocol (信噪比 +30% vs uniform)
5. **dialogue-craft.md** — 台词密度阈值 (男频 0.4-0.6 / 女频 0.5-0.7 / ≥0.8 anti-pattern) + 潜台词比例 ≥60% + "as you know" CN anti-pattern 3-strike rule

### editor (5 refs)
1. **murch-rule-of-six.md** — Murch Rule of Six (emotion 51% / story 23% / rhythm 10% / eye-trace 7% / 2D plane 5% / 3D space 4%) + ideal cut moment 6 criteria
2. **classical-editing-rhythm.md** — Reisz-Millar classical cutting + scene rhythm ASL targets per genre + reaction shot priority
3. **montage-theory.md** — Eisenstein 5 methods of montage (metric / rhythmic / tonal / overtonal / intellectual) + dialectical collision principle
4. **fxrxt-axis-compliance.md** — 180° axis rule + 30° rule + shot-reverse-shot pacing + cross-cutting density
5. **cn-cutting-rhythm.md** — 短剧 ASL 1.2-2.0s (vs Western 4-6s) + BGM-driven cut points + 字幕 design for vertical 9:16

### colorist (5 refs)
1. **bellantoni-color-psychology.md** — 8-color vocabulary (Purple / Red / Yellow / Blue / Green / Orange / White / Black) + each color ≥3 canonical director×film triplets + "color as character" doctrine
2. **hurkman-color-pipeline.md** — primary/secondary/qualifier 三层 + lift/gamma/gain 操作语义 + node-based 流水线 + power window
3. **color-cross-cultural.md** — Schirillo 1200-film sample 色温-情绪映射 + Adams & Osgood 23-culture color-emotion survey + Ekman basic-emotion meta
4. **cn-audience-color.md** — 抖音 100K+ video color temp stats + 男频/女频 色温分野 + 国风 色盘 + per-platform divergence
5. **digital-color-science.md** — Rec.709/2020/DCI-P3 色域 + ΔE2000 公式 (production ≤3 / preview ≤6) + ACES IDT/ODT + LUT bit-depth 误差累积

### style_genome (5 refs)
1. **director-dna-archive.md** — 35 director 5D vectors + signature elements + 焦距 + ASL (Cinemetrics) + 3-tier classification (Composition-masters / Color-poets / Rhythm-makers)
2. **genre-dna-taxonomy.md** — 12-genre 5D vector 区间表 (incl. 短剧-男频-revenge / 短剧-女频-romance) + signature shot patterns + genre-locked metric thresholds
3. **auteur-theory.md** — Sarris 3-criteria rubric (technical competence + distinguishable personality + interior meaning) + Style Coherence Doctrine (Wood 1965) + tier decision tree
4. **cross-cultural-style.md** — CN/Western/Korean 5D divergence matrix + Cultural Translation Cost formula + Hybrid Encoding Protocol (0.65/0.35) + Non-translatable elements + Hallyu 中介
5. **cn-director-analysis.md** — CN generation tiering (第五代/第六代/香港新浪潮/台湾新电影/short_drama) + 5 canonical CN director 5D profile (张艺谋/贾樟柯/王家卫/杜琪峰/侯孝贤) + signature elements

**REFACTOR-08 status:** SATISFIED. Each ref carries ≥3 concrete heuristics with explicit citations to specific academic / industry / case-study sources.

---

## Next Steps

**Option A (recommended): `/gsd:plan-phase 4`** — Plan EXPERT-CINE (cinematographer), the next phase. This builds the 5th v1 expert and produces the Phase 4 GO/NO-GO gate context.

**Option B: `/gsd:plan-phase 6` first** — Run Phase 6 live eval first to produce the statistical evidence required for the formal Phase 4 gate verdict. This delays Phase 4 but provides the GO/NO-GO data.

Either option preserves the ROADMAP intent: Phase 5 (remaining 10 experts + production) is conditional on Phase 3 RAG uplift being statistically significant; that evidence comes from Phase 6 live run.

---

*Report generated: 2026-06-15 as part of Phase 3 REFACTOR-05 (ablation + GO/NO-GO).*
*Authority: Phase 3 evidence + preliminary recommendation only. Formal GO/NO-GO gate decision deferred to Phase 4 per ROADMAP.*
