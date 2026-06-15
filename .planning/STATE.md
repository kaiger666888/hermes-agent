---
gsd_state_version: 1.0
milestone: v1
milestone_name: Movie-Experts Suite v2 (MESV2)
status: executing
last_updated: "2026-06-15T13:20:24.305Z"
progress:
  total_phases: 7
  completed_phases: 3
  total_plans: 15
  completed_plans: 15
  percent: 43
---

# State: Movie-Experts Suite v2 (MESV2)

## Project Reference

**Project code:** MESV2
**Name:** Movie-Experts Suite v2 — 短剧/微电影创作专家增强
**Core value:** 每个 movie-expert skill 都能用检索增强的方式调用行业知识库,让 AI 生成的短剧/微电影在专业度上接近人类创作者水平。
**Key docs:** `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/research/SUMMARY.md`
**Mode:** yolo (auto-advance, parallelization on)
**Granularity:** standard
**Model profile:** quality

## Current Position

Phase: 03 (top-4-existing-experts-rag) — COMPLETE
Plan: 5 of 5
**Phase:** 3
**Plan:** Complete (Gate artifact produced)
**Status:** Phase 3 complete — GO/NO-GO gate artifact produced; formal gate decision deferred to Phase 4
**Constraint:** Phase 0 is a blocker gate. Nothing else starts until it passes.

### Progress

```
Phase 0 [ .......... ] 0% Not started  (BLOCKER GATE)
Phase 1 [ .......... ] 0% Not started
Phase 2 [ .......... ] 0% Not started
Phase 3 [ .......... ] 0% Not started
Phase 4 [ .......... ] 0% Not started
Phase 5 [ .......... ] 0% Not started (v1.5)
Phase 6 [ .......... ] 0% Not started
```

### Phase Statuses

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 0 | AUDIT + Eval Skeleton | Complete | BLOCKER GATE passed 2026-06-15. ≤ 2 GLM-heavy ops in parallel. |
| 1 | EXPERT-COMPLI | Complete | Legal gate. Built compliance_marketing expert end-to-end. |
| 2 | EXPERT-HOOK | Complete | Commercial engine. Built hook_retention expert end-to-end. |
| 3 | Top-4 RAG | Gate artifact produced | Dry-run complete (36 verdicts); live deferred to Phase 6. GO/NO-GO report at `_eval/reports/phase3-go-nogo.{json,md}`. Formal gate decision deferred to Phase 4 per ROADMAP. |
| 4 | EXPERT-CINE | Complete | Built cinematographer expert end-to-end (4 refs + SKILL.md + 3 prompts + 7 peer related_skills updates). Boundary doc with scene_builder/animator/editor BEFORE SKILL.md. |
| 5 | Remaining 10 + EXPERT-PROD | Complete (v1.5) | Production expert built (5 refs + SKILL.md + 3 prompts + 8 peer edges). 10 existing experts RAG-uplifted (2 refs each). Phantom strips: foley AudioLDM-2 / voicer CosyVoice / drawer FLUX 1.x samplers / animator Wan family. |
| 6 | Full Eval + Bilingual + README | Documentation pass complete | Top-level README published (17-expert collaboration graph + RAG usage guide + Phase 6 live-run procedure). Bilingual consistency spot-check performed. Live run deferred to operator (requires OPENROUTER_API_KEY + budget). |

## Performance Metrics

- Phases completed: 0 / 7
- v1 requirements delivered: 0 / 46
- Plans completed: 0
- Phase 0 readiness: roadmap committed; ready for `/gsd:plan-phase 0`

## Accumulated Context

### Decisions (carried from PROJECT.md + research)

- **Hybrid RAG (static refs primary + memory plugin optional).** Static refs are git-trackable + reviewable; vector RAG reuses Hermes memory plugin — no new infra.
- **4 new experts (CINE / HOOK / PROD / COMPLI).** Cover 短剧 creation v1 gaps: camera language, retention, production mgmt, CN compliance.
- **Deep refactor of existing 14 (not light enhancement).** Deep prompt rewrite + metric revision + RAG injection required for measurable uplift.
- **Bilingual format: EN YAML structure + CN descriptive prose.** Hermes community compat preserved; CN prose carries 短剧 industry knowledge.
- **v1 includes LLM-as-judge eval harness.** Every "is RAG worth it" claim must be statistically defensible.
- **Pure skill + refs delivery (no Hermes core code changes).** PR risk control.
- **Frozen expert_id values for existing 14.** Backward-compat HARD RULE. Refactor edits prompt body, metrics, thresholds — NEVER identifiers.
- **≤ 2 GLM-heavy skills in flight per phase.** GLM overload already demonstrated (2/4 mapper failures).
- **Provider-agnostic RAG invocation.** Hard-coding `fact_store` / `mem0_search` breaks for the other provider. Defensive conditional phrasing is load-bearing.
- **Position-swap eval mandatory.** Both orderings, N ≥ 20, panel of ≥ 2 judges, ablation vs no-RAG baseline. Otherwise invalid.

### Todos (Phase 0 entry)

- [ ] Run `/gsd:plan-phase 0` to decompose Phase 0 into executable plans
- [ ] Confirm open-weight vs commercial judge panel composition (Phase 0 design decision per research Gaps)
- [ ] Verify Hermes ships FLUX 1.x or FLUX 2 (re-verify `plugins/image_gen/` inventory during AUDIT)
- [ ] Strip "168K controlled tokens" fabrication in `performer/SKILL.md` (verify it isn't a typo for a real concept first)

### Blockers / Risks (active)

- **P0:** Phantom refs (`wan22_video`, "168K tokens", FLUX 1.x samplers) already shipping in v1 — Phase 0 MUST strip before any downstream work.
- **P1:** 短剧 sample copyright risk in CN (active enforcement 2024-2026). Per-ref LICENSE.md mandatory.
- **P1:** LLM-as-judge invalidity if N<20, single ordering, or no ablation baseline.
- **P2:** Platform guideline drift — 抖音/快手/视频号 guidelines change quarterly; refs MUST carry `verified_date` stamp + refresh cadence.
- **P2:** EXPERT-CINE overlap with scene_builder/animator — boundary MUST be documented BEFORE writing SKILL.md.

### GO/NO-GO Gate (after Phase 4)

If Phase 3 RAG uplift is statistically insignificant (CI crosses 0), scrap Phase 5 entirely. Cheaper to discover after 5 experts than after 18.

### Research flags queued

- Phase 1: verify 2026-Q2 platform guideline versions + AI 漫剧 备案 threshold triggers
- Phase 2: validate 短剧 pacing data + current video gen model behavior
- Phase 5: AI budget modeling heuristics (character-LoRA cost, render-farm allocation)

## Session Continuity

**Last action:** Roadmap created from research SUMMARY.md prescriptive 7-phase build order.
**Next action:** `/gsd:plan-phase 0` (Phase 0 planning — blocker gate, no parallelization across phases).
**Hand-off note:** Phase 0 plans should produce (1) `scripts/verify_skill_references.py`, (2) GAP-REPORT.md × 14, (3) `_eval/{runner.py,snapshot.py,judge_prompt.md}` skeleton, (4) baseline snapshots × 14, (5) phantom-ref cleanup across 14 SKILL.md files, (6) `_shared/glossary.md` skeleton. Cap at ≤ 2 GLM-heavy operations in parallel.

---

*State initialized: 2026-06-15*
