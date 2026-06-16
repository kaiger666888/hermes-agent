---
gsd_state_version: 1.0
milestone: v3.0
milestone_name: Skills-to-DAG Alignment
status: ready_to_plan
last_updated: 2026-06-17T00:00:00.000Z
last_activity: 2026-06-17 — Phase 15 Plan 01 complete (audio_pipeline merged expert created: 6 sub_steps [voicer, lip_sync, composer, foley, mixer, spatial_audio]; 5 merged_into stubs + 1 folded_into stub for spatial_audio per disposition D-1; 23 ref files migrated to 6 sub-folders; GAP-REPORT consolidated)
progress:
  total_phases: 6
  completed_phases: 2
  total_plans: 6
  completed_plans: 6
  percent: 33
stopped_at: Phase 15 Plan 01 complete (1/3) — ready for 15-02 (consumer edge sync)
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
**Current focus:** Phase 15 — audio pipeline merge (5 audio experts → audio_pipeline with sub_steps)

## Current Position

Phase: 15
Plan: 15-01 complete (1/3); next is 15-02 (consumer edge sync)
Status: Executing
Last activity: 2026-06-17

### Progress

```
v1 milestone: [██████████] 100% Complete (Phases 0-6, shipped 2026-06-15)

v2.0 PRFP milestone: [██████████] 100% Complete (Phases 7-12, shipped 2026-06-16)

v3.0 Skills-to-DAG Alignment milestone:
  Phase 13 [██████████] 100% Complete (13-01 done: continuity→continuity_auditor; 13-02 done: compliance_marketing→compliance_gate; 13-03 done: sign_off + README + glossary close-out)
  Phase 14 [██████████] 100% Complete (14-01 done: drawer+animator → visual_executor with sub_steps metadata; 14-02 done: consumer edge sync across 15 SKILL.md; 14-03 done: README + corpus tree + DAG + _shared/ docs close-out)
  Phase 15 [███       ] 33% In progress (15-01 done: voicer+lip_sync+composer+foley+mixer+spatial_audio → audio_pipeline with 6-item sub_steps + Spatial Audio Disposition D-1 fold + lip_sync NODE-09 explicit-sub-step; 15-02 pending: consumer edge sync; 15-03 pending: close-out docs)
  Phase 16 [          ] 0% Not started (prompt_injector NEW — UNBLOCKED, depends on 15)
  Phase 17 [          ] 0% Not started (deprecate 3 — UNBLOCKED, depends on 16)
  Phase 18 [          ] 0% Not started (validate + docs — depends on 13-17)
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

### Decisions (v3.0 — Phase 14)

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| N-to-one merge pattern: new dir + sub_steps frontmatter + redirect stubs + aliases | Phase 13 backward-compat rename pattern extended to N:1 merges; `sub_steps` field declares predecessor experts as sub-steps per v2.0 PRFP DAG | Applied 2026-06-17 in plan 14-01 (drawer + animator → visual_executor) |
| New top-level `sub_steps: [drawer, animator]` frontmatter field | Declared at same level as `metadata`, NOT nested inside it — per v2.0 PRFP DAG convention | Applied 2026-06-17 in plan 14-01; grep-verified |
| Refs organized into sub-folders (`references/drawer/` + `references/animator/`) | Cleaner than filename-prefix strategy; CONTEXT.md granted Claude's discretion | Applied 2026-06-17 in plan 14-01 |
| Drawer<->animator Collaboration bullets rewritten as internal-handoff notes | Preserves operational contract while making intra-expert nature explicit (post-merge they are sub-steps of one expert_id) | Applied 2026-06-17 in plan 14-01 |
| RAG tag prefix migration: `expert:{drawer\|animator},domain:X` → `expert:visual_executor,sub:{drawer\|animator},domain:X` | Preserves domain axis while introducing sub-step scoping for query precision | Applied 2026-06-17 in plan 14-01 |
| Old `drawer/references/` + `animator/references/` + both `GAP-REPORT.md` preserved untouched | Same archival pattern as Phase 13 — point-in-time references must remain intact for transcript resolution | Applied 2026-06-17 in plan 14-01 |
| animation_studio plan-audit deviation (Rule 1) | Plan interface table claimed animation_studio had NEITHER drawer NOR animator in related_skills; actual file listed BOTH. Applied collapse rule anyway — correctness over plan-text literalism. 14 consumers (not 13) now have visual_executor edges. | Applied 2026-06-17 in plan 14-02 |
| Sub-step annotation strategy for merged Collaboration bullets | Pure collapse of drawer+animator → visual_executor bullets would lose operational context; inline-annotated each sub-step's specific contract to preserve handoff semantics | Applied 2026-06-17 in plan 14-02 across cinematographer, character_designer, storyboard_designer, production, performer, colorist, continuity_auditor |
| Artifact filename `animator_handoff.json` preserved (cinematographer lines 97, 190) | Stable artifact contract name, not an expert_id reference; renaming would change the artifact schema | Applied 2026-06-17 in plan 14-02 |
| style_genome DAG pipeline string consolidated to single stage | Original DAG had drawer (stills) + animator (video) in separate stages; post-merge both are visual_executor sub-steps, so a single combined stage avoids ambiguous duplicate entries in non-array context | Applied 2026-06-17 in plan 14-02 |
| Bare-noun "drawer" in character_designer body (lines 47, 270) PRESERVED | No markdown link, refers to the act/agent of drawing generically, not the expert_id — per plan's English-noun preservation rule | Applied 2026-06-17 in plan 14-02 |
| Multi-line ASCII DAG box form for visual_executor (`visual_` / `executor 视觉`) | Label exceeds 13-char width of surrounding single-line boxes; same two-line form + column alignment as Phase 13's compliance_gate box | Applied 2026-06-17 in plan 14-03 |
| Corpus tree: old drawer/ + animator/ rows preserved with `(Phase 14 redirect stub)` annotation | Plan explicitly recommended preserve+annotate over Phase 13's remove-entirely pattern for richer audit trail | Applied 2026-06-17 in plan 14-03 |
| Footer expert count 23 → 22 with explicit '− 1 Phase 14 visual_executor merge' annotation | Self-documenting arithmetic; Phase 18 will do canonical 26→21 reconciliation | Applied 2026-06-17 in plan 14-03 |
| known-external-models.yaml NOT modified in 14-03 | Its provenance strings reference predecessor ref file paths (e.g., `animator/video-gen-model-matrix.md`) that still resolve via 14-01's archival preservation; plan files_modified did not list it; Phase 18 (DOC-02 + VALIDATE-01) is canonical path reconciliation phase | Documented 2026-06-17 in plan 14-03 |

### Decisions (v3.0 — Phase 15)

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| N-to-one merge pattern extended from 2-item (Phase 14) to 6-item sub_steps array | v2.0 PRFP DAG canonicalized the audio_pipeline node with 6 sub-steps (voicer, lip_sync, composer, foley, mixer, spatial_audio); frontmatter `sub_steps` field extends naturally to N items | Applied 2026-06-17 in plan 15-01 |
| spatial_audio disposition D-1: fold (not deprecate) | Spatial audio rendering is fundamentally a mixer/mastering concern (Atmos bed+objects, 6D encoding, HRTF binaural operate on the same stems mixer operates on); folding preserves the unique HRTF/Atmos technical content; deprecation would lose irreplaceable tables | Applied 2026-06-17 in plan 15-01; documented in `## Spatial Audio Disposition` H2 section per ROADMAP §15 criterion #2 |
| spatial_audio redirect stub uses status: folded_into (distinct from merged_into) | Records the fold disposition explicitly — spatial_audio was not a peer-equivalent merge but a fold-into-a-related-sub-step; semantically meaningful for Phase 18 audit traceability | Applied 2026-06-17 in plan 15-01 |
| lip_sync promoted to explicit sub-step per Phase 8 §2.9 NODE-09 | lip_sync was implicit in v1 (only a voicer→lip_sync collaboration edge); v2.0 PRFP DAG promotes it because it carries unique objective validation (LRS2/LRS3 + LSE/LSE-C via SyncNet — no LLM-judge) and pairs with a theory_critic on output identity preservation | Applied 2026-06-17 in plan 15-01; documented in `## Sub-step: Lip Sync` opening note per ROADMAP §15 criterion #5 |
| lip_sync GAP-REPORT absence handled with placeholder note | lip_sync predecessor has no GAP-REPORT.md (only `_eval/prompts/` regression suite); silent omission would lose traceability record | Applied 2026-06-17 in plan 15-01; T-15-08 threat mitigation |
| Refs organized into sub-folders (references/{voicer,lip_sync,composer,foley,mixer,spatial_audio}/) | Cleaner than filename-prefix strategy; CONTEXT.md granted Claude's discretion; matches Phase 14 visual_executor pattern | Applied 2026-06-17 in plan 15-01 |
| All 6 predecessors' intra-audio Collaboration bullets rewritten as internal-handoff notes | Post-merge the audio experts are sub-steps of one expert_id (audio_pipeline); preserving the intra-audio Collaboration bullets as inter-expert edges would be incorrect — rewritten to point at sibling Sub-step sections | Applied 2026-06-17 in plan 15-01 |
| RAG tag prefix migration: `expert:{voicer\|lip_sync\|composer\|foley\|mixer\|spatial_audio},domain:X` → `expert:audio_pipeline,sub:{voicer\|lip_sync\|composer\|foley\|mixer\|spatial_audio},domain:X` | Preserves domain axis while introducing sub-step scoping for query precision; matches Phase 14 migration pattern | Applied 2026-06-17 in plan 15-01 |
| Version bumps on all 6 redirect stubs | Records the merge event in version history (voicer 1.2.0, lip_sync 1.1.0, composer 1.2.0, foley 1.1.0, mixer 1.2.0, spatial_audio 1.2.0); distinct from Phase 14 which kept drawer/animator versions unchanged in their stubs | Applied 2026-06-17 in plan 15-01 |
| Plan narrative "21 ref files" miscount NOT propagated | The plan narrative says "21 ref files (3+4+3+3+2+2 + 6 LICENSEs)" but the actual file list in `<files>` and `<verify>` enumerates 23 files; file list was the source of truth and was followed exactly; SUMMARY documents the discrepancy | Documented 2026-06-17 in plan 15-01 SUMMARY §Deviations |

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

**Last action:** Phase 15 Plan 01 executed (2026-06-17) — audio_pipeline merged expert created. New `skills/movie-experts/audio_pipeline/SKILL.md` declares top-level `sub_steps: [voicer, lip_sync, composer, foley, mixer, spatial_audio]` (6-item array — extends Phase 14's 2-item sub_steps field). `metadata.hermes.aliases: [voicer, lip_sync, composer, foley, mixer, spatial_audio]` declared per FOUND-08. `metadata.hermes.related_skills` = exact 8-item external union `[screenplay, performer, editor, production, visual_executor, continuity_auditor, style_genome, scene_builder]` (audio-pipeline self-refs + internal audio edges dropped). Body has 6 `## Sub-step:` H2 sections in pipeline order voicer→lip_sync→composer→foley→mixer→spatial_audio. `## Spatial Audio Disposition` H2 documents the D-1 fold decision + rationale + rejected alternative + `folded_into` stub status (ROADMAP §15 criterion #2). Sub-step: Lip Sync opens with NODE-09 explicit-sub-step note (ROADMAP §15 criterion #5). All 6 predecessors' intra-audio Collaboration bullets rewritten as internal-handoff notes. 23 ref files migrated verbatim to `references/{voicer,lip_sync,composer,foley,mixer,spatial_audio}/` sub-folders. GAP-REPORT.md consolidates 5 predecessor GAP-REPORTs + 1 placeholder for lip_sync. 6 old audio SKILL.md files replaced with redirect stubs (5 `status: merged_into` + 1 `status: folded_into` for spatial_audio). Commits b4d9646c0 + 36941fe06.
**Next action:** `/gsd:plan-phase 15` (continue with plan 15-02) or `/gsd:execute-phase 15` to plan + execute consumer edge sync across 9+ consumer SKILL.md files. ROADMAP §15 criteria 1, 2, 3, 5 satisfied; criterion 4 (old audio expert dirs preserved) partly satisfied at source-expert level. Bidirectional consumer edge sync (criterion 4 full satisfaction) is the job of plan 15-02.
**Hand-off note:** Phase 15 IN PROGRESS — 1/3 plans done. audio_pipeline merged expert created + predecessor stubs in place. Next: 15-02 (consumer edge sync across NON-audio consumers referencing old audio expert_ids) + 15-03 (close-out docs: README inventory + corpus tree + DAG + _shared/ glossary + RAG-INVOCATION-PATTERN + project-corpus). Phase 16 (prompt_injector new), Phase 17 (deprecations) remain UNBLOCKED. Phase 18 (finalization) gated on 13-17 complete.

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
