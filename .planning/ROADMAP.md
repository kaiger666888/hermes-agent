# Roadmap: Hermes Agent — Kai's Personal Agent Platform

## Milestones

| Version | Name | Phases | Shipped | Tag | Audit |
|---------|------|--------|---------|-----|-------|
| v1 | Movie-Experts Suite v2 | 0-6 | 2026-06-15 | `v1` | passed (deferred live run) |
| v2.0 | PRFP Pipeline Design (design-only) | 7-12 | 2026-06-16 | `v2.0-prfp-design` | design-only |
| v3.0 | Skills-to-DAG Alignment | 13-18 | 2026-06-17 | `v3.0` | tech_debt |
| v4.0 | Methodology Backfill | 19-21 | 2026-06-18 | `v4.0` | passed |
| v5.0 | kais-movie-agent V8.6 Adaptation | 22-27 | 2026-06-19 | `v5.0` | passed |
| v6.0 | Self-Evolution Feedback Loop | 28-33 | 2026-06-24 | `v6.0` | passed |
| v7.0 | openclaw → hermes Migration | 34-37 | 2026-06-25 | `v7.0` | passed |
| v9.0 | kais-movie-pipeline 闭环深化 | 38-43 | 2026-06-27 | `v9.0` | passed |
| v10.0 | 编排架构第一性原理推导(设计型) | 44-51 | 2026-07-07 | `v10.0` | passed (zero code) |
| v11.0 | Hermes-Native Expert Agents PoC | 52-56 | 2026-07-07 | `v11.0` | passed |
| v12.0 | Production Hardening | 57-61 | 2026-07-08 | `v12.0` | passed |
| v13.0 | v10.0 Design Suite Full Rollout & Live Eval | 62-69 | 2026-07-08 | `v13.0` | tech_debt |
| v14.0 | kais-movie-pipeline 4-Track Upgrade (FORM / DUB / IMG / TRANSITION) | 70-76 | 2026-07-10 | `v14.0` | tech_debt (24 satisfied + 2 operator-handoff) |
| **v15.0** | **Operator-Action Closure Tooling** | **77-83** | **In progress** | **TBD** | **TBD** |

See [MILESTONES.md](./MILESTONES.md) for full milestone history with key accomplishments per milestone, and `milestones/v{N}.0-ROADMAP.md` for archived phase artifacts.

---

## Most Recent Shipped Milestone: v14.0 ✅ SHIPPED 2026-07-10

**Stats:** 7 phases (70-76) · 17 plans · 36 tasks · 26/26 reqs mapped (24 satisfied + 2 operator-handoff) · Tag `v14.0` · Audit `tech_debt`

**One sentence:** 把 kais-movie-pipeline 从「竖屏短剧专用」升级为「横竖双 default 的通用短片创作管线」,同步升级 4 项核心生成环节到 production-grade (横竖并行双 default 形态参数化 / CosyVoice 2.0-0.5B 配音 + LTX 2.3 native audio 分工 / dreamina cli 深度编排 + GLM-4.6V vision-verify 强制门 / 创作+数据+生成三层转场协作)。v14.0 是 v9.0 后首个 kais-movie-pipeline-focused milestone,重启跨 repo 工作流 (plan → hermes-agent/.planning/,code → kais-hermes-skills/)。

See archived `milestones/v14.0-ROADMAP.md` for full phase details. v14.0 left 6 operator-action handoffs documented in `milestones/v14.0-MILESTONE-AUDIT.md §5` — v15.0 closes them.

<details>
<summary>v14.0 Phase Details (click to expand)</summary>

| Phase | Name | Status | Completed |
|-------|------|--------|-----------|
| 70 | FOUNDATION-AUDIT | SHIPPED (3 plans) | 2026-07-09 |
| 71 | FORM | SHIPPED (3 plans) | 2026-07-09 |
| 72 | DUB | SHIPPED (3 plans) | 2026-07-09 |
| 73 | IMG | SHIPPED (3 plans) | 2026-07-09 |
| 74 | TRANSITION | SHIPPED (3 plans) | 2026-07-09 |
| 75 | LINEAGE-BUMP | SHIPPED (1 plan) | 2026-07-10 |
| 76 | VALIDATE | SHIPPED (1 plan + audit + tag) | 2026-07-10 |

**Critical path:** 70 → 71 → (72 ∥ 73) → 74 → 75 → 76. Phase 76 strictly LAST.

**Cross-repo topology:** hermes-agent = GSD planning; kais-hermes-skills = SKILL.md + refs + code. Final pins: hermes-agent `4e7c58cc9`, kais-hermes-skills `ba58c254`.

**Hard constraints preserved:** INFRA-04 serial NOT lifted · EVAL-06 dry-run-first NOT changed · FOUND-08 15-expert set frozen · SKILL.md L1-L6 read-only invariant exception破例 authorized for v14.0 only (reverts v15+ unless re-authorized).

</details>

---

## Current Milestone: v15.0 — Operator-Action Closure Tooling (STARTED 2026-07-10)

**Milestone Goal:** Author production-grade tooling + workflows that close v14.0's 6 operator-action handoffs by making them executable; captured data flows back to code (VERSION.json locks, calibration thresholds, validation verdicts). Each handoff becomes a 5-minute operator task rather than a research project.

**Stats:** 7 phases (77-83) · 15 reqs · Coverage 15/15 ✓

**Cross-repo topology (沿用 v14.0):** hermes-agent repo = GSD `.planning/` 工件; kais-hermes-skills repo = scripts + workflows + Python + refs. Final cross-repo pins recorded at v15.0 close.

**Hard constraints preserved (沿用 v14.0):**

- INFRA-04 serial execution NOT lifted
- EVAL-06 dry-run-first NOT changed (curator `--live` opt-in; v15.0 doesn't unfreeze)
- FOUND-08 15-expert set frozen
- SKILL.md L1-L6 read-only invariant **REVERTS** post-v14.0 — v15.0 only `kais-jimeng-cli` SKILL.md may be touched for cloud-engine-bootstrap doc references; no Form/DUB/IMG/TRANSITION SKILL.md body changes

### Phase summary

| Phase | Name | Status | Completed |
|-------|------|--------|-----------|
| 77 | 2/2 | Complete    | 2026-07-10 |
| 78 | 2/2 | Complete    | 2026-07-10 |
| 79 | 2/2 | Complete    | 2026-07-10 |
| 80 | 1/1 | Complete    | 2026-07-10 |
| 81 | XCUT-04b Cloud Engine Bootstrap | 2/2 | Complete    | 2026-07-10 |
| 82 | XCUT-04c Cost Tracking + XCUT-05 Lineage Auto | 1/3 | In progress    |
| 83 | VALIDATE | Not started | - |

**Critical path:** 77 → (78 ∥ 79) → 80 → 81 → 82 → 83. Phase 83 strictly LAST.

---

## Phases

- [x] **Phase 77: DUB-05 Benchmark Runner** - CosyVoice A/B benchmark script + VERSION.json lock mechanism (completed 2026-07-10)
- [x] **Phase 78: TRANS-07 LTX-FLF Validation Runner** - ComfyUI workflow JSON + validation runner + verdict doc (completed 2026-07-10, parallel with Phase 79)
- [x] **Phase 79: IMG-09 Vision-Verify Calibration** - False-positive calibration analyzer + per-stratum threshold override (parallel with Phase 78, completed 2026-07-10)
- [x] **Phase 80: DUB-03 Voice Sample Protocol** - Collection protocol ref + batch validator script (completed 2026-07-10)
- [x] **Phase 81: XCUT-04b Cloud Engine Bootstrap** - Hailuo/Vidu/Wan2.2 bootstrap doc + opt-in config mechanism (completed 2026-07-10)
- [ ] **Phase 82: XCUT-04c Cost Tracking + XCUT-05 Lineage Auto** - GLM-4.6V cost instrumentation + CLI + automated lineage bump script (Plan 01 complete)
- [ ] **Phase 83: VALIDATE** - Milestone audit + meta-rule audit extension + tag v15.0 (strictly LAST)

---

## Phase Details

### Phase 77: DUB-05 Benchmark Runner

**Goal**: Operator can execute a side-by-side A/B benchmark of CosyVoice 2.0-0.5B vs Fun-CosyVoice 3.0 on representative dialogue lines, review structured output, and lock the chosen variant in VERSION.json with captured rationale.
**Depends on**: Nothing (first v15.0 phase; builds on v14.0 Phase 72 DUB foundation + VERSION.json lock site)
**Requirements**: DUB-05-RUNNER, DUB-05-LOCK
**Success Criteria** (what must be TRUE):

  1. User can run `python scripts/run_cosyvoice_benchmark.py --dialogue-lines <file> --variants cosyvoice_2_0_0_5b,fun_cosyvoice_3_0` and get a structured JSON report + audio files for human review
  2. User can run `python scripts/lock_cosyvoice_default.py --benchmark-report <path>` to lock the chosen variant in `VERSION.json.tts.cosyvoice_default_variant` with rationale field populated from the benchmark report
  3. The lock script does NOT auto-pick-lower-WER — it requires operator decision (audio quality judgment is human-in-loop per DUB-05-AUTO-LOCK deferral)

**Plans**: 2 plans
Plans:
**Wave 1**

- [x] 77-01-PLAN.md — Benchmark runner script + unit tests (DUB-05-RUNNER)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 77-02-PLAN.md — VERSION.json lock script + tests + cosyvoice-benchmark.md Runner Usage section (DUB-05-LOCK)

### Phase 78: TRANS-07 LTX-FLF Validation Runner

**Goal**: Operator can validate the LTX-2.3 FLF + ICLoRA combined workflow against 1-2 reference shots through a ComfyUI workflow JSON + runner script, and read the production-readiness verdict that gates TRANS-11 v16+ rollout.
**Depends on**: Phase 77 (DUB-05 benchmark infrastructure establishes the operator-runner pattern); parallel with Phase 79
**Requirements**: TRANS-07-WORKFLOW, TRANS-07-RUNNER, TRANS-07-VERDICT
**Success Criteria** (what must be TRUE):

  1. User can read `references/workflows/ltx-flf-iclora-validation.json` ComfyUI workflow (LiconMSR + LTXVConditioning + SamplerCustomAdvanced node graph) for 1-2 reference shot validation
  2. User can run `python scripts/run_ltx_flf_validation.py --reference-shots <dir>` to submit reference shots through the workflow + capture results (gen_status, latency, identity-continuity via vision_verify)
  3. User can read production-readiness verdict (ready / deferred-to-v16+) in `references/ltx-flf-iclora-validation.md` after operator runs validation — this verdict gates TRANS-11 v16+ production rollout

**Plans**: 2 plans
Plans:
**Wave 1**

- [x] 78-01-PLAN.md — ComfyUI workflow JSON template + async validation runner script + unit tests (TRANS-07-WORKFLOW + TRANS-07-RUNNER)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 78-02-PLAN.md — Verdict update script + tests + ltx-flf-iclora-validation.md Runner Usage section (TRANS-07-VERDICT)

### Phase 79: IMG-09 Vision-Verify Calibration

**Goal**: Operator can calibrate vision-verify confidence thresholds per stratum based on production MetricsBuffer data, reducing false positives without sacrificing detection of real identity drift.
**Depends on**: Phase 77 (DUB-05 establishes the operator-runner pattern); parallel with Phase 78
**Requirements**: IMG-09-CALIBRATE, IMG-09-APPLY
**Success Criteria** (what must be TRUE):

  1. User can run `python scripts/calibrate_vision_verify.py --metrics-buffer <path>` to analyze production MetricsBuffer data and get a recommended confidence threshold per stratum (1-ref / 3-ref / 5-ref) using false-positive rate analysis
  2. User can apply calibrated thresholds via `vision_verify.py` config (per-stratum threshold override) and the change is recorded in an audit log capturing when and why thresholds changed
  3. The calibration script reads from existing `~/.hermes/metrics/dreamina_stats.jsonl` production data (no new data collection needed — operator must have run v14.0 IMG stack in production first)

**Plans**: 2 plans
Plans:
**Wave 1**

- [x] 79-01-PLAN.md — Calibration script + unit tests (IMG-09-CALIBRATE)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 79-02-PLAN.md — Apply script + vision_verify.py modification + tests (IMG-09-APPLY)

### Phase 80: DUB-03 Voice Sample Protocol

**Goal**: Operator can source per-character voice samples following a documented protocol and batch-validate them against technical requirements before pipeline ingestion.
**Depends on**: Phase 78 + Phase 79 (both parallel tracks must complete before moving to the next sequential phase)
**Requirements**: DUB-03-PROTOCOL, DUB-03-BATCH-VALIDATE
**Success Criteria** (what must be TRUE):

  1. User can read `references/voice-sample-collection-protocol.md` for per-character voice sample collection guidelines (3-10s clean recording, environment requirements, file naming convention `assets/<episode>/voice_refs/<character>.wav`)
  2. User can run `python scripts/validate_voice_clone_batch.py --voice-refs-dir <dir>` to batch-validate all voice_clone_reference_wav files against 3-10s duration + wav format + >=16kHz sample rate + mono channel rules
  3. The validator outputs a pass/fail report per character identifying which rule(s) each sample violated (enabling targeted re-recording)

**Plans**: 1 plan
Plans:
**Wave 1**

- [x] 80-01-PLAN.md — Collection protocol doc + batch validator script + unit tests (DUB-03-PROTOCOL + DUB-03-BATCH-VALIDATE)

### Phase 81: XCUT-04b Cloud Engine Bootstrap

**Goal**: Operator can bootstrap cloud transition engines (Hailuo 02 i2v Pro, Vidu keyframe-to-video, ComfyUI Wan2.2 FLF2V) by following documented acquisition steps and opting in per engine via config.
**Depends on**: Phase 80
**Requirements**: XCUT-04b-DOCS, XCUT-04b-OPTIN
**Success Criteria** (what must be TRUE):

  1. User can read `references/cloud-engine-bootstrap.md` for Hailuo + Vidu API key acquisition steps + ComfyUI Wan2.2 FLF2V custom node install procedure + cost-estimation worksheet (per-shot + monthly projections)
  2. User can opt in per cloud engine via `~/.hermes/config.yaml` `cloud_engines` block (`hailuo_api_key` + `vidu_api_key` + `wan22_comfyui_node_enabled`)
  3. The existing `transition-engine-routing.md` declarative routing rules consume the opt-in state at runtime (engines not opted in are skipped during routing evaluation)
  4. The `kais-jimeng-cli` SKILL.md may be touched ONLY for cloud-engine-bootstrap doc cross-references (the single authorized SKILL.md exception per v15.0 hard constraints)

**Plans**: 2 plans
Plans:
**Wave 1**

- [x] 81-01-PLAN.md — Cloud engine bootstrap doc + routing update + cli-config + kais-jimeng-cli SKILL.md touch (XCUT-04b-DOCS)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 81-02-PLAN.md — check_cloud_engine_optin.py script + unit tests (XCUT-04b-OPTIN)
**UI hint**: yes

### Phase 82: XCUT-04c Cost Tracking + XCUT-05 Lineage Auto

**Goal**: GLM-4.6V token spend is tracked alongside latency/success metrics with a CLI surface, and the 15-agent lineage bump is automated into a single script closing the v14.0 XCUT-05 deferral.
**Depends on**: Phase 81
**Requirements**: XCUT-04c-INSTRUMENT, XCUT-04c-CLI, XCUT-05-AUTO
**Success Criteria** (what must be TRUE):

  1. `dreamina_stats.py` MetricsBuffer tracks per-batch GLM-4.6V token spend (`input_tokens` + `output_tokens` + `estimated_cost_usd`) alongside existing per-task latency / success rate
  2. User can run `hermes glm stats` CLI subcommand to see monthly GLM-4.6V aggregate spend (token count + estimated USD cost) + per-stratum breakdown, reusing Rich table formatting from `hermes dreamina stats`
  3. User can run `python scripts/bump_all_agent_lineage.py` to automate the full 15-agent lineage bump (wraps `transform_skill_to_agent.py` for all 15 active experts + handles Track B 6 v13.0 P62 manual cases)

**Plans**: 3 plans
Plans:
**Wave 1**

- [x] 82-01-PLAN.md — XCUT-04c MetricsBuffer instrumentation + vision_verify usage + dreamina_manager capture (XCUT-04c-INSTRUMENT)

- [ ] 82-03-PLAN.md — XCUT-05-AUTO bump_all_agent_lineage.py 15-agent lineage bump script (XCUT-05-AUTO)

**Wave 2** *(blocked on Wave 1 Plan 82-01 completion)*

- [ ] 82-02-PLAN.md — XCUT-04c-CLI register_glm_cli + monthly/per-stratum aggregation + Rich tables (XCUT-04c-CLI)
**UI hint**: yes

### Phase 83: VALIDATE

**Goal**: v15.0 milestone closes with a re-run of the META-RULE X-2 audit extended to v15.0 constants, closure of v14.0 tech_debt items where operator-action data has flowed back to code, and the milestone audit doc + tag.
**Depends on**: Phase 82 (strictly LAST — mirror v10.0 P51 / v14.0 P76 pattern; must run after all code-bearing phases complete)
**Requirements**: VALIDATE-V15
**Success Criteria** (what must be TRUE):

  1. `76-meta-rule-x2-audit.sh` re-runs successfully and its coverage extends to any new v15.0 `_INSTRUCTION` constants (if any were added)
  2. v14.0 tech_debt items are closed where operator-action data has flowed back to code: DUB-05 lock applied (if operator ran benchmark) / IMG-09 thresholds applied (if operator ran calibration) / TRANS-07 verdict recorded (if operator ran validation)
  3. `v15.0-MILESTONE-AUDIT.md` authored with verdict + tag `v15.0` placed
  4. Cross-repo final pins recorded (hermes-agent + kais-hermes-skills commit hashes at close)

**Plans**: TBD

---

## Backlog

Candidate directions for v16+ (not yet committed — pending milestone planning):

- **TRANS-11 production rollout** (gated by TRANS-07 v15.0 validation verdict): LTX-2.3 FLF + ICLoRA combined workflow — if validation passes, v16+ rolls it into production transition routing.
- **DUB-05-AUTO-LOCK**: full automation of VERSION.json lock based on benchmark scores (v15.0 deferred — operator-in-loop required for audio quality judgment).
- **IMG-09-AUTO-TUNE**: closed-loop auto-threshold adjustment based on rolling production data (v15.0 deferred — operator review still required for threshold changes).
- **v15-LIVE-EVAL**: v13.0 Phase 64 live-eval secrets integration (operator-secret-dependent).
- **feishu-* skills migration** (v7.0 carryforward): largest v7.0 deferred item, not yet planned.
- **FORM-06 / FORM-07 / DUB-06 / DUB-07 / IMG-07 / IMG-08 / TRANS-08 / TRANS-09 / TRANS-10** (v14.0 Future Requirements, all explicitly acknowledged as deferred).

---

*Last updated: 2026-07-10 — v15.0 roadmap created (Operator-Action Closure Tooling; 7 phases 77-83, 15/15 reqs mapped, standard granularity). v14.0 milestone SHIPPED 2026-07-10. Critical path: 77 → (78 ∥ 79) → 80 → 81 → 82 → 83.*
