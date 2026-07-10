---
gsd_state_version: 1.0
milestone: v15.0
milestone_name: Operator-Action Closure Tooling
status: executing
last_updated: "2026-07-10T04:08:00.000Z"
last_activity: 2026-07-10 -- Phase 78 Plan 01 complete
progress:
  total_phases: 7
  completed_phases: 1
  total_plans: 4
  completed_plans: 3
  percent: 21
---

# State: Hermes Agent — Kai's Personal Agent Platform

## Project Reference

**Project code:** MESV2 (historical; v7.0+ broadens scope beyond movie-experts; v14.0 returns focus to kais-movie-pipeline)
**Name:** Hermes Agent — Kai's Personal Agent Platform
**Core value:** 让 hermes-agent 成为 Kai 的主 agent:v14.0 shipped kais-movie-pipeline 4-track upgrade (FORM/DUB/IMG/TRANSITION);**v15.0 聚焦把 v14.0 留的 6 项 operator-action handoffs 工具化,让每个 handoff 变成 5-minute operator task 而非 research project**。Captured data flows back to code (VERSION.json locks / calibration thresholds / validation verdicts)。
**Key docs:** `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/MILESTONES.md` (v1-v14 history), `.planning/milestones/v14.0-MILESTONE-AUDIT.md` §5 (6 operator-action handoffs source)
**Mode:** yolo (auto-advance, parallelization on)
**Granularity:** standard
**Model profile:** quality
**Current focus:** Phase 78 — TRANS-07 LTX-FLF Validation Runner

## Current Position

Phase: 78 (TRANS-07 LTX-FLF Validation Runner) — EXECUTING
Plan: 1 of 2 complete (Plan 02 pending: verdict doc update script + Runner Usage docs)
Status: Phase 78 Plan 01 complete
Last activity: 2026-07-10 -- Phase 78 Plan 01 (workflow JSON + runner + tests) shipped

### Progress

```
v1 movie-experts:                  [██████████] 100% (Phases 0-6, shipped 2026-06-15)
v2.0 PRFP design:                  [██████████] 100% (Phases 7-12, shipped 2026-06-16)
v3.0 Skills-to-DAG:                [██████████] 100% (Phases 13-18, shipped 2026-06-17)
v4.0 Methodology Backfill:         [██████████] 100% (Phases 19-21, shipped 2026-06-18)
v5.0 V8.6 Adaptation:              [██████████] 100% (Phases 22-27, shipped 2026-06-19)
v6.0 Self-Evolution Feedback:      [██████████] 100% (Phases 28-33, shipped 2026-06-24)
v7.0 openclaw → hermes Migration:  [██████████] 100% (Phases 34-37, shipped 2026-06-25)
v9.0 kais-movie-pipeline 闭环深化:  [██████████] 100% (Phases 38-43, shipped 2026-06-27)
v10.0 编排架构设计(设计型):         [██████████] 100% (Phases 44-51, shipped 2026-07-07, tag v10.0)
v11.0 Expert Agents PoC:           [██████████] 100% (Phases 52-56, shipped 2026-07-07, tag v11.0)
v12.0 Production Hardening:        [██████████] 100% (Phases 57-61, shipped 2026-07-08, tag v12.0)
v13.0 Design Suite Full Rollout:   [██████████] 100% (Phases 62-69, shipped 2026-07-08, tag v13.0, verdict: tech_debt)
v14.0 4-Track Upgrade:             [██████████] 100% (Phases 70-76, shipped 2026-07-10, tag v14.0, verdict: tech_debt)
v15.0 Operator-Action Closure:     [██░░░░░░░░] 21% (Phases 77-83, Phase 77 complete 2/2 + Phase 78 Plan 01 complete, 3/14 plans done)
```

### Phase Statuses (v15.0)

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 77 | DUB-05 Benchmark Runner | COMPLETE (2/2 plans) | CosyVoice A/B benchmark runner script + VERSION.json lock mechanism + cosyvoice-benchmark.md Runner Usage docs. DUB-05-RUNNER + DUB-05-LOCK complete. Ready for verification. |
| 78 | TRANS-07 LTX-FLF Validation Runner | Plan 01 complete (1/2) | ComfyUI workflow JSON + async validation runner + 12 tests shipped. Plan 02 pending: verdict update script + Runner Usage docs. |
| 79 | IMG-09 Vision-Verify Calibration | Not started | False-positive calibration analyzer + per-stratum threshold override. IMG-09-CALIBRATE/APPLY. Parallel with Phase 78. |
| 80 | DUB-03 Voice Sample Protocol | Not started | Collection protocol ref + batch validator. DUB-03-PROTOCOL/BATCH-VALIDATE. |
| 81 | XCUT-04b Cloud Engine Bootstrap | Not started | Hailuo/Vidu/Wan2.2 bootstrap doc + opt-in config. XCUT-04b-DOCS/OPTIN. |
| 82 | XCUT-04c Cost Tracking + XCUT-05 Lineage Auto | Not started | GLM-4.6V cost instrumentation + CLI + auto lineage bump. XCUT-04c-INSTRUMENT/CLI + XCUT-05-AUTO. |
| 83 | VALIDATE | Not started | Milestone audit + meta-rule audit extension + tag v15.0. VALIDATE-V15. Strictly LAST. |

### Critical Path (v15.0)

```
Phase 77 (DUB-05 Runner) ──┬──▶ Phase 78 (TRANS-07 Runner)  ──┐
                           │                                   │
                           └──▶ Phase 79 (IMG-09 Calibrate)  ──┤
                                                               │
                                     Phase 78 + 79 complete ───▶ Phase 80 (DUB-03 Protocol)
                                                                               │
                                                                               ▼
                                                                     Phase 81 (XCUT-04b Cloud Engine)
                                                                               │
                                                                               ▼
                                                                     Phase 82 (XCUT-04c + XCUT-05)
                                                                               │
                                                                               ▼
                                                                     Phase 83 (VALIDATE — strictly LAST)
```

Phase 78 and Phase 79 execute in parallel (both depend only on Phase 77). Phase 83 (VALIDATE) is strictly LAST (mirror v14.0 P76 / v13.0 P69 / v10.0 P51 pattern).

### Hard Constraints Preserved (v15.0)

- **INFRA-04 serial constraint NOT lifted** — MEMORY.md `feedback-glm-overload-reduce-concurrency.md`. All code paths stay serial for GLM-coupled operations.
- **EVAL-06 dry-run-first NOT changed** — curator `--live` opt-in (default dry-run preserved). v15.0 does NOT unfreeze.
- **FOUND-08 15-expert set frozen** — zero new expert_id. v15.0 tooling is operator-action closure, not expert expansion.
- **SKILL.md L1-L6 read-only invariant REVERTS** post-v14.0 — v15.0 only `kais-jimeng-cli` SKILL.md may be touched for cloud-engine-bootstrap doc references. No Form/DUB/IMG/TRANSITION SKILL.md body changes.

## Performance Metrics (v15.0)

- v15.0 phases total: 7 (Phases 77-83, continuing from v14.0 phase 76)
- v15.0 phases shipped: 0 (roadmap just created)
- v15.0 requirements total: 15 (DUB-05-RUNNER/LOCK + TRANS-07-WORKFLOW/RUNNER/VERDICT + IMG-09-CALIBRATE/APPLY + DUB-03-PROTOCOL/BATCH-VALIDATE + XCUT-04b-DOCS/OPTIN + XCUT-04c-INSTRUMENT/CLI + XCUT-05-AUTO + VALIDATE-V15)
- v15.0 requirements mapped: 15/15 (100% coverage)
- v15.0 plans in shipped phases: 0
- v15.0 audit verdict: pending (Phase 83)

### Per-plan execution metrics

| Phase | Plan | Duration | Tasks | Files |
|-------|------|----------|-------|-------|
| 77 | 01 | 373s | 2 | 2 |
| 77 | 02 | 195s | 3 | 3 |
| 78 | 01 | 366s | 2 | 3 |

## Accumulated Context

### v15.0 Goal Restatement

把 v14.0 留的 6 项 operator-action handoffs 工具化,让每个 handoff 变成 5-minute operator task:

1. **DUB-05 (Phase 77)** — CosyVoice A/B benchmark runner script + lock mechanism → operator runs benchmark once + locks VERSION.json
2. **TRANS-07 (Phase 78)** — LTX-FLF+ICLoRA validation ComfyUI workflow + runner script → operator submits 1-2 reference shots + gets verdict
3. **IMG-09 (Phase 79)** — Vision-verify false-positive calibration analyzer + threshold override → operator runs calibration on production data + applies thresholds
4. **DUB-03 (Phase 80)** — Voice sample collection protocol ref + batch validator → operator sources wavs per protocol + validates before pipeline
5. **XCUT-04b (Phase 81)** — Cloud engine bootstrap doc (Hailuo/Vidu/Wan2.2) + opt-in config → operator follows steps + opts in
6. **XCUT-04c (Phase 82)** — GLM-4.6V cost tracking instrumentation + CLI + auto lineage bump script

Plus Phase 83 (VALIDATE — audit + tag v15.0).

**Cross-repo topology (沿用 v14.0):** scripts + workflows + Python in kais-hermes-skills; planning in hermes-agent.

### Decisions

Decisions are logged in PROJECT.md Key Decisions table. Recent decisions affecting v15.0 work:

- **[Roadmap]** 7 phases continuing from v14.0 phase 76 (77-83) — sequential phase numbering; v14.0 ended at P76.
- **[Roadmap]** Phase 78 ∥ Phase 79 parallel execution — TRANS-07 and IMG-09 are independent surfaces; both depend only on Phase 77 (establishes operator-runner pattern). Cuts wall time.
- **[Roadmap]** Phase 82 combines XCUT-04c (2 reqs) + XCUT-05-AUTO (1 req) — both are cost/tooling closures on dreamina_stats/transform infrastructure; natural grouping.
- **[Roadmap]** Phase 83 strictly LAST — mirrors v14.0 P76 / v13.0 P69 / v10.0 P51 pattern; must run after all code-bearing phases.
- [Phase ?]: test
- [Phase ?]: DUB-05 runner CLI variant IDs use underscores (cosyvoice_2_0_0_5b) for shell-safety, mapped to VERSION.json dotted IDs (cosyvoice_2.0_0.5B) via _VARIANT_TO_VERSION_JSON dict
- [Phase ?]: DUB-05 runner uses sync-only execution (INFRA-04 compliant) with per-cell error handling — partial results preserved on single-variant failure
- [Phase 77]: DUB-05-LOCK: lock script reads operator_decision.variant from benchmark report (not --variant flag); 3-check validation + lock_ready guard + overwrite guard; writes only 3 fields to VERSION.json; does NOT auto-pick-lower-WER (DUB-05-AUTO-LOCK deferred)
- [Phase 77]: DUB-05-LOCK: VARIANT_ID_MAP maps CLI underscore IDs to VERSION.json dotted IDs; rationale guard added as 4th validation check (T-77-09 repudiation mitigation)
- [Phase 78]: TRANS-07-RUNNER: async runner with serial awaits (httpx.AsyncClient, no concurrent dispatch — INFRA-04); vision_verify_fn injected as parameter for testability; 3-frame identity check (first/middle/last) per shot
- [Phase 78]: TRANS-07-WORKFLOW: 25-node combined ICLoRA+FLF JSON template based on validated LiconMSR (3/3 success 2026-06-28) + FLF additions (LTXVImgToVideoInplace + LTXVAddGuide); placeholder strings for runner parameterization

### Blockers / Risks (v15.0)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Operator hasn't run v14.0 IMG stack in production yet (IMG-09 calibration needs data)** | MEDIUM | MEDIUM (IMG-09-CALIBRATE can't produce real thresholds without production MetricsBuffer data) | Phase 79 delivers the analyzer script; operator runs calibration when production data exists. Script works on empty buffer (outputs "insufficient data" recommendation). |
| **ComfyUI Wan2.2 FLF2V node install complexity (XCUT-04b)** | MEDIUM | LOW (v15.0 delivers install doc only, NOT the install) | Phase 81 delivers procedure doc; operator runs install. Doc covers troubleshooting per community reports. |
| **LTX-FLF+ICLoRA workflow may not be production-ready (TRANS-07)** | HIGH | LOW (TRANS-07 validation runner gates TRANS-11 v16+ rollout) | Phase 78 runner captures results; verdict doc records ready/deferred decision. Deferred verdict is acceptable outcome (gates v16+ scope). |
| **SKILL.md L1-L6 read-only invariant REVERTS post-v14.0** | LOW | MEDIUM (unauthorized SKILL.md edits would violate hard constraint) | v15.0 hard constraint documented explicitly: only kais-jimeng-cli SKILL.md may be touched for cloud-engine-bootstrap doc references. Phase 83 audit verifies. |

### Pending Todos

None yet (milestone just started).

## Deferred Items

Items acknowledged and carried forward (NOT in v15.0 scope):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| **v14.0 DUB-05 A/B benchmark result** | Operator runs benchmark + locks VERSION.json | v15.0 Phase 77 delivers runner (operator-action handoff closure) | v14.0 close (2026-07-10) |
| **v14.0 TRANS-07 LTX-FLF validation** | Operator runs 1-2 reference shots | v15.0 Phase 78 delivers runner (operator-action handoff closure) | v14.0 close (2026-07-10) |
| **v14.0 IMG-09 calibration** | Operator runs calibration on production data | v15.0 Phase 79 delivers analyzer (operator-action handoff closure) | v14.0 close (2026-07-10) |
| **v14.0 DUB-03 voice_clone_reference_wav** | Operator sources per-character wavs | v15.0 Phase 80 delivers protocol + validator (operator-action handoff closure) | v14.0 close (2026-07-10) |
| **v14.0 XCUT-04b Hailuo/Vidu API keys** | Operator opts in per cloud engine | v15.0 Phase 81 delivers bootstrap doc + opt-in (operator-action handoff closure) | v14.0 close (2026-07-10) |
| **v14.0 XCUT-04c GLM-4.6V cost tracking** | MetricsBuffer token spend instrumentation | v15.0 Phase 82 delivers instrumentation + CLI | v14.0 close (2026-07-10) |
| **v13.0 Phase 64 LIVE-EVAL-EXEC** | 3 operator smoke tests (GLM/mem0 secrets) | Deferred to v16+ (operator-secret-dependent) | v13.0 close |
| **v13.0 Phase 66 CURATOR-LIVE-TICK** | 1st live tick + runbook | Deferred to v16+ (operator-handoff) | v13.0 close |
| **v15.0 DUB-05-AUTO-LOCK** | Full automation of VERSION.json lock | Deferred to v16+ (operator-in-loop required for audio quality) | v15.0 planning |
| **v15.0 IMG-09-AUTO-TUNE** | Closed-loop auto-threshold adjustment | Deferred to v16+ (operator review still required) | v15.0 planning |
| **v14.0 FORM-06..TRANS-11 carry-forward** | 11 future reqs (FORM-06/07, DUB-06/07/08, IMG-07/08, TRANS-08/09/10/11) | Deferred to v16+ | v14.0 planning |

## Session Continuity

**If session is lost, restore context by reading:**

1. `.planning/PROJECT.md` §"Current Milestone: v15.0" — 6 operator-action closure tracks + hard constraints
2. `.planning/ROADMAP.md` — 7 phases (77-83), 15/15 reqs mapped, critical path, phase details
3. `.planning/REQUIREMENTS.md` — 15 v15.0 reqs + Traceability table + Out of Scope
4. `.planning/MILESTONES.md` — v1-v14 history (FOUND-08 / INFRA-04 / EVAL-06 invariants)
5. `.planning/milestones/v14.0-MILESTONE-AUDIT.md` §5 — 6 operator-action handoffs (v15.0 source)
6. MEMORY.md `feedback-glm-overload-reduce-concurrency.md` (INFRA-04 serial constraint — NOT lifted in v15.0)

**Next action:** Phase 77 complete (2/2 plans). Next: `/gsd:plan-phase 78` and `/gsd:plan-phase 79` (parallel — TRANS-07 LTX-FLF Validation Runner + IMG-09 Vision-Verify Calibration).

---

## Operator Next Steps

- Plan the first phase with `/gsd:plan-phase 77`

---

<details>
<summary>v14.0 Historical Context (archived — read-only reference)</summary>

The sections below preserve the v14.0 execution context for reference. v14.0 SHIPPED 2026-07-10 (tag v14.0, verdict tech_debt). v15.0 builds on v14.0's foundation.

### v14.0 Phase Statuses (all COMPLETE)

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 70 | FOUNDATION-AUDIT | COMPLETE (3/3 plans) | Lineage Impact Assessment (XCUT-01). Curator `--live` freeze. Cross-repo baseline commit pin. |
| 71 | FORM | COMPLETE (3/3 plans) | form_factor parameterization (FORM-01..05). |
| 72 | DUB | COMPLETE (3/3 plans) | CosyVoice + LTX 2.3 native audio (DUB-01..05). |
| 73 | IMG | COMPLETE (3/3 plans) | dreamina production-grade orchestration (IMG-01..06). |
| 74 | TRANSITION | COMPLETE (3/3 plans) | 创作+数据+生成三层 (TRANS-01..07). |
| 75 | LINEAGE-BUMP | COMPLETE (1/1 plan) | 15 agent.yaml regenerated. Curator freeze released. |
| 76 | VALIDATE | COMPLETE (1/1 plan) | META-RULE X-2 audit + ancestry assertion + milestone audit + tag v14.0. |

### v14.0 Cross-Repo Pins (FINAL)

| Repo | Role | Full SHA | Short | Ancestry |
|------|------|----------|-------|----------|
| hermes-agent | P70 baseline | `8f70fcf7f0604db21158f86f8495f3d9ce3c9ab1` | `8f70fcf7` | (baseline) |
| hermes-agent | v14.0 final | `4e7c58cc9cac3c4925770beaf5a9433369094a24` | `4e7c58cc` | descendant of `8f70fcf7` (exit 0) |
| kais-hermes-skills | P70 baseline | `d9620369e48eec51c31ee72ac8827c288eaccf71` | `d9620369` | (baseline) |
| kais-hermes-skills | v14.0 final | `ba58c2548ab82f0cd9acd7cc7af14402137f8520` | `ba58c254` | descendant of `d9620369` (exit 0) |

### v14.0 Operator-Action Handoffs (6 items — source for v15.0)

Per XCUT-04 spec, these are NOT gaps — v14.0 delivered the framework, operator runs the action:

1. **DUB-05 A/B benchmark** — CosyVoice 2.0-0.5B vs Fun-CosyVoice 3.0 on 3-5 reference dialogue lines → locks `VERSION.json.tts.cosyvoice_default_variant`
2. **DUB-03 voice_clone_reference_wav** — operator-sourced per-character 3-10s reference audio samples
3. **IMG-03 / XCUT-04c vision-verify API cost** — GLM-4.6V batch calls at production scale (~178 calls per 213-shot episode)
4. **XCUT-04b Hailuo/Vidu API keys** — opt-in for cloud Chinese-content transition engines per TRANS-06
5. **TRANS-07 LTX-FLF+ICLoRA validation report** — operator runs 1-2 reference shots; gates TRANS-11 v15+ production rollout
6. **Manual UAT** — horizontal-screen-framing.md citation fair-use review + Tier 1 transition-design.md content substance review (carry-forward)

### v14.0 Hard Constraints (all preserved)

- INFRA-04 serial execution NOT lifted (zero asyncio.gather for GLM-coupled code paths)
- EVAL-06 dry-run-first NOT changed (curator `--live` frozen for v14.0 duration, released post-Phase-75)
- FOUND-08 15-expert set frozen (TRANS-04 field-level ownership split, zero new expert_id)
- SKILL.md L1-L6 read-only invariant exception破例 authorized for v14.0 only (lineage regeneration mandatory per XCUT-03) — **REVERTS v15+ unless re-authorized**

</details>

---

*Last updated: 2026-07-10 — v15.0 roadmap created (Operator-Action Closure Tooling; 7 phases 77-83, 15/15 reqs mapped, standard granularity). v14.0 SHIPPED 2026-07-10 (tag v14.0, verdict tech_debt). Critical path: 77 → (78 ∥ 79) → 80 → 81 → 82 → 83. Phase 83 strictly LAST. Next: `/gsd:plan-phase 77`.*
