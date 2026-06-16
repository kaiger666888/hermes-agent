---
gsd_state_version: 1.0
milestone: v3.0
milestone_name: Skills-to-DAG Alignment
status: ready_to_plan
last_updated: 2026-06-16T16:33:48.138Z
last_activity: 2026-06-17 — Phase 13 Plan 03 complete (close-out: skills-mapping.yaml sign_off + README + glossary) — Phase 13 COMPLETE
progress:
  total_phases: 6
  completed_phases: 1
  total_plans: 3
  completed_plans: 3
  percent: 17
stopped_at: Phase 13 complete (3/3) — ready to discuss Phase 14
---

# State: Movie-Experts Suite v2 (MESV2)

## Project Reference

**Project code:** MESV2
**Name:** Movie-Experts Suite v2 — 短剧/微电影创作专家增强
**Core value:** 每个 movie-expert skill 都能用检索增强的方式调用行业知识库,让 AI 生成的短剧/微电影在专业度上接近人类创作者水平。
**Key docs:** `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/MILESTONES.md`, `.planning/REQUIREMENTS.md`, `.planning/milestones/v1-*.md`
**Mode:** yolo (auto-advance, parallelization on)
**Granularity:** standard
**Model profile:** quality
**Current focus:** Phase 14 — visual executor merge (drawer + animator)

## Current Position

Phase: 14
Plan: Not started
Status: Ready to plan
Last activity: 2026-06-16

### Progress

```
v1 milestone: [██████████] 100% Complete (Phases 0-6, shipped 2026-06-15)

v2.0 PRFP milestone: [██████████] 100% Complete (Phases 7-12, shipped 2026-06-16)

v3.0 Skills-to-DAG Alignment milestone:
  Phase 13 [██████████] 100% Complete (13-01 done: continuity→continuity_auditor; 13-02 done: compliance_marketing→compliance_gate; 13-03 done: sign_off + README + glossary close-out)
  Phase 14 [          ] 0% Not started (depends on 13 — UNBLOCKED)
  Phase 15 [          ] 0% Not started (depends on 13 — UNBLOCKED)
  Phase 16 [          ] 0% Not started (depends on 13 — UNBLOCKED)
  Phase 17 [          ] 0% Not started (depends on 13 — UNBLOCKED)
  Phase 18 [          ] 0% Not started (depends on 13-17)
```

### Phase Statuses (v2.0 PRFP)

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 7 | First-Principles Derivation | Not started (planning) | Bottleneck. HIGH research load (Musk-method primary-source verification, PITFALLS §5 OQ#4). Covers DERIV-01..08. |
| 8 | Node DAG + Per-Node Specs | Not started | Blocked by Phase 7. Covers NODE-01..09 + META-05 + META-06. MEDIUM research load (2026-Q2 AI capability stability). |
| 9 | 102-Book Corpus Traceability | Not started | Parallel with Phase 8 once Phase 7 emits node IDs. Covers CORPUS-01..07. No new research needed. |
| 10 | LLM-Creative-Distillation Deep-Dive | Not started | Parallel with Phase 8 once Phase 7 emits AI-limits definition. Covers CREATIVE-01..07. MEDIUM research load. |
| 11 | Cross-Comparisons + Dual-Repo Handoff | Not started | Blocked by 8+9+10 stable. Covers HANDOFF-01..09. |
| 12 | Finalization (Governance + Open Questions + README) | Not started | Blocked by Phase 11. Covers GOV-01..06 + META-01/02/03/04 (exit-checks). |

### Critical Path

```
7 → 8 → 11 → 12
      ↘
        9 (parallel with 8)
        10 (parallel with 8)
```

## Performance Metrics (v2.0 PRFP)

- v2.0 phases total: 6 (Phases 7-12)
- v2.0 phases completed: 0
- v2.0 requirements total: 52
- v2.0 requirements mapped: 52 / 52 ✓
- v2.0 requirements orphaned: 0
- v2.0 plans completed: 0 / ? (TBD per phase)
- Deliverable form: DESIGN DOCS ONLY — zero code changes to `skills/movie-experts/` or `kais-movie-agent/lib/`

## Accumulated Context

### Decisions (carried into v2.0 from research synthesis)

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Adopt ARCHITECTURE.md's 6-phase A→F decomposition (renumbered 7-12) | Only synthesis with explicit critical-path + parallelism analysis; subsumes PITFALLS' 5-feature mapping and FEATURES' content taxonomy | Pending — roadmap written 2026-06-16 |
| Phase 7 (derivation) is the bottleneck | PROJECT.md mandates "节点设计从 0 推"; every other section is downstream | Pending — enforced via critical path |
| Cross-cutting META assignment: META-05/06 → Phase 8 (they constrain node cost_budgets and shape theory_critic edges); META-01/02/03/04 → Phase 12 (exit-checks verified at milestone close) | META-05 cost ceiling must exist before Phase 8 can populate cost_budgets; META-06 trigger mode shapes DAG edges (Phase 8). META-01/02/03/04 are no-touch/bilingual/location invariants that can only be verified at finalization. | Pending |
| Coverage count = 52 (not 51) | REQUIREMENTS.md flagged a -1 for "HANDOFF-09/HANDOFF-01 overlap" — on review, these are distinct REQs (handoff contract vs comparison analyses). All 52 mapped. | Pending — noted in ROADMAP.md coverage section |
| Critical path 7 → 8 → 11 → 12 (not 7 → 8 → 9 → 10 → 11 → 12) | Phases 9 and 10 run parallel with 8 once Phase 7 produces node IDs / AI-limits; they do NOT extend the critical path | Pending |

### Decisions (v3.0 — Phase 13)

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Backward-compat rename pattern: new dir + redirect stub + `metadata.hermes.aliases` | FOUND-08 zero-silent-rename rule requires explicit alias declaration; redirect stub preserves historical transcript references | Applied 2026-06-17 in plan 13-01 (continuity → continuity_auditor) + plan 13-02 (compliance_marketing → compliance_gate) |
| Composer excluded from continuity_auditor consumer set | `composer/SKILL.md` never had `continuity` in `related_skills`; plan over-listed based on "invisible continuity" English noun | Documented in 13-01-SUMMARY §Deviations; rename correctly applied to all 16 actual consumers |
| `_eval/baseline/` snapshots NOT renamed | Frozen regression baselines must preserve point-in-time expert_id for eval harness integrity | Documented in 13-01-SUMMARY §Deviations; only active SKILL.md consumers renamed |
| lip_sync JSON output field names (`continuity_handoff`, `needs_continuity_audit`) preserved | These are data field names in the output schema, not expert_id references; renaming would be an API-shape change | Documented in 13-01-SUMMARY §Deviations; plan action 5 scope respected |
| Added `signed_off_at: 2026-06-17` + `signed_off_by: phase-13` traceability fields under each signed_off entry in skills-mapping.yaml | CONTEXT.md explicitly granted Claude's discretion; explicit sign-off timestamp + signer make audit trail unambiguous for Phase 18 verification | Applied 2026-06-17 in plan 13-03 (Task 1) |
| Phase 13 ASCII DAG diagram multi-line compliance box preserved (`compliance_` / `gate 合规`) | Same two-line form + column alignment as character_designer multi-line box — visual consistency | Applied 2026-06-17 in plan 13-03 (Task 2) |

### Blockers / Risks (carried from v1 + new v2.0 risks)

**Inherited from v1 (still ongoing):**

- ⚠ Platform guideline drift — refs use `verified_date` + 90-day refresh cadence
- ⚠ 短剧 sample copyright — fair-use + LICENSE.md per ref
- ⚠ LLM-as-judge invalidity — Phase 6 live run deferred to operator

**New in v2.0 PRFP (per PITFALLS §"Top 5 Critical Risks"):**

- 🔴 **First-principles theater** (PITFALLS 1.1, 1.5, 1.6, 5.4) — derivation that is ex-post justification dressed in reductionist language. Mitigation: Phase 7 enforces structural rigor (per-node `derivation`, epistemic-status tagging, steelman-elimination, alternatives log).
- 🔴 **Design-impl drift across two repos** (PITFALLS 3.1-3.5) — design stale by the time kais-movie-agent implements. Mitigation: Phase 11 handoff includes `baseline_ref` git SHA, impl-cheatsheet, ownership matrix, versioning scheme.
- ⚠ **Throwing out validated craft as "bias"** (PITFALLS 1.2, 5.3) — discarding Murch/Field/180°-axis as "historical baggage". Mitigation: Phase 9 corpus-anchor + Phase 7 contingent-vs-validated-invariant classification.
- ⚠ **Premature model-commitment** (PITFALLS 1.3, 2.7) — hard-coding Sora/Kling/Veo. Mitigation: Phase 8 capability-spec canonical layer; model names only in dated annex.
- ⚠ **Creative-story node under-specified** (PITFALLS 4.1-4.7). Mitigation: Phase 10 operational creativity definition, consistency-context + logic-critic, template library, platform-vs-art tension.

### Open Questions (carried from research SUMMARY.md §"Open Questions for User")

These remain unresolved at roadmap creation; they surface during phase planning:

1. Node-count target: 8-15 (PITFALLS/ARCHITECTURE) vs ~25 (FEATURES MVP P1)? Synthesizer recommends 8-15 with ≤25 hard ceiling.
2. Cost-ceiling assumption: ¥1000-10000/episode? (PITFALLS Open Question #1)
3. Single-author vs distributed authorship (ARCHITECTURE Anti-Pattern 7)?
4. Theory_critic invocation trigger (FEATURES gap)?
5. Bilingual doc policy for v2.0 design docs (META-03 says EN+CN — confirm applies to all design artifacts)?

## Session Continuity

**Last action:** Phase 13 Plan 03 executed (2026-06-17) — Close-out: skills-mapping.yaml `sign_off_status: pending` → `signed_off` for BOTH renamed entries (continuity_auditor + compliance_gate) + traceability fields `signed_off_at: 2026-06-17` + `signed_off_by: phase-13` + README.md inventory / corpus tree / ASCII DAG / shell-loop updates + _shared/glossary.md expert_id reference updates. Commits 8985f450a + 71da7c0f7.
**Next action:** Phase 14 (visual_executor merge — drawer + animator → visual_executor) can now begin. Phase 13's backward-compat rename pattern is established + authoritative per skills-mapping.yaml sign-off. Same pattern (new dir + redirect stub + metadata.hermes.aliases) is reusable for the N:1 merge cases in Phase 14 + 15.
**Hand-off note:** Phase 13 is COMPLETE — both renames signed off in canonical mapping. Phase 14 (visual_executor merge), Phase 15 (audio_pipeline merge), Phase 16 (prompt_injector new), Phase 17 (deprecations) are all UNBLOCKED. Phase 18 (finalization + inventory + verification) is gated on 13-17 all being complete.

---

## Deferred Items (carried from v1 close — unchanged)

| Category | Item | Status |
|----------|------|--------|
| uat | 06-UAT.md (Phase 6) | partial — 10 pending scenarios; UAT paused by user redirect |
| verification | 01-VERIFICATION.md (Phase 1) | human_needed — CN legal review + platform-spec spot-check + judge prompt quality + glossary completeness |
| live-run | Phase 6 live run execution | Requires OPENROUTER_API_KEY + budget |
| prompt-expansion | N ≥ 20 prompt expansion per expert | Phase 6 statistical threshold (currently 3 per expert) |
| multi-judge | Multi-judge ensemble invocation | runner currently uses judges[0] only |
| statistical-verdict | Live-run statistical GO/NO-GO verdict | Pending live run results per CONTEXT D-9 |
| legal-review | CN legal review of compliance_marketing refs | Statute citations + platform thresholds |
| bilingual-lint | Full bilingual consistency lint | Corpus complete; spot-check performed |

---

*State initialized: 2026-06-15 · Milestone v1 closed: 2026-06-15 · Milestone v2.0 PRFP started: 2026-06-16 · Roadmap written: 2026-06-16*

## Operator Next Steps

- `/gsd:plan-phase 7` to plan the First-Principles Derivation phase (HIGH research load — consider `--research-phase` flag)
- Review `.planning/ROADMAP.md` (v2.0 section) and `.planning/REQUIREMENTS.md` (Traceability section) to confirm phase assignments
- After Phase 7 produces candidate node IDs: `/gsd:plan-phase 8`, `/gsd:plan-phase 9`, `/gsd:plan-phase 10` can be planned in parallel
