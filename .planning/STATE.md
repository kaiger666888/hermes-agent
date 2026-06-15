---
gsd_state_version: 1.0
milestone: v1.5
milestone_name: milestone
status: executing
last_updated: "2026-06-15T05:14:55.647Z"
progress:
  total_phases: 7
  completed_phases: 0
  total_plans: 4
  completed_plans: 5
  percent: 0
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

Phase: 1 (EXPERT-COMPLI (Legal Gate)) — EXECUTING
Plan: 1 of 3
**Phase:** 1
**Plan:** Not started
**Status:** Executing Phase 1
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
| 0 | AUDIT + Eval Skeleton | Not started | BLOCKER GATE. ≤ 2 GLM-heavy ops in parallel. |
| 1 | EXPERT-COMPLI | Not started | Legal gate. Research flag: verify 2026-Q2 platform guidelines + AI 漫剧 备案 thresholds. |
| 2 | EXPERT-HOOK | Not started | Commercial engine. Research flag: validate 短剧 pacing data + video gen model behavior. |
| 3 | Top-4 RAG | Not started | GO/NO-GO gate follows in Phase 4. Sequential screenplay → editor → colorist → style_genome. |
| 4 | EXPERT-CINE | Not started | Boundary vs scene_builder/animator/editor MUST be documented before SKILL.md written. |
| 5 | Remaining 10 + EXPERT-PROD | Not started (v1.5) | Deferred beyond v1 release. Scrap entirely if Phase 3 RAG uplift is statistically insignificant. |
| 6 | Full Eval + Bilingual + README | Not started | N ≥ 20 prompts/expert. Panel of ≥ 2 judges. Both orderings. |

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
