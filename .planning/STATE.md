---
gsd_state_version: 1.0
milestone: v14.0
milestone_name: kais-movie-pipeline 4-Track Upgrade (FORM / DUB / IMG / TRANSITION)
status: ready_to_plan
last_updated: 2026-07-09T07:22:10.383Z
last_activity: 2026-07-09
progress:
  total_phases: 7
  completed_phases: 1
  total_plans: 3
  completed_plans: 3
  percent: 14
stopped_at: Phase 70 complete (3/3) — ready to discuss Phase 71
---

# State: Hermes Agent — Kai's Personal Agent Platform

## Project Reference

**Project code:** MESV2 (historical; v7.0+ broadens scope beyond movie-experts; v14.0 returns focus to kais-movie-pipeline)
**Name:** Hermes Agent — Kai's Personal Agent Platform
**Core value:** 让 hermes-agent 成为 Kai 的主 agent:既承载 movie-experts 这样的领域专家子系统(v1-v6 已 shipped),也具备通用 agent 必备能力(v7.0+ 迁移)。v10.0-v13.0 四 milestone 架构弧线(编排器 + native expert agents + CC 执行场)已收官。**v14.0 回到 kais-movie-pipeline 把 4 项核心生成环节升级到 production-grade**(横竖双 default 形态 / CosyVoice 配音 / dreamina 深度集成 / 三层转场协作)。
**Key docs:** `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/research/v14-4track-upgrade/SUMMARY.md` (HIGH-confidence research), `.planning/MILESTONES.md` (v1-v13 history)
**Mode:** yolo (auto-advance, parallelization on)
**Granularity:** standard
**Model profile:** quality
**Current focus:** Phase 71 — form

## Current Position

Phase: 71
Plan: Not started
Status: Ready to plan
Last activity: 2026-07-09

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
v14.0 4-Track Upgrade:             [░░░░░░░░░░]   0% (Phases 70-76, started 2026-07-09, IN PROGRESS)
```

**v14.0 milestone status:** IN PROGRESS — roadmap created 2026-07-09. 7 phases (70-76), 26/26 reqs mapped. Phase 70 (FOUNDATION-AUDIT) ready to plan.

### Phase Statuses (v14.0)

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 70 | FOUNDATION-AUDIT | Complete (3/3 plans shipped, ready for verification) | Lineage Impact Assessment (XCUT-01). Curator `--live` freeze. Cross-repo baseline commit pin. **All 3 plans shipped 2026-07-09:** Plan 01 = 70-LINEAGE-INVENTORY.md (6 SKILL.md hashes + 3 agent.yaml lineage + cross-repo pins); Plan 02 = curator.enabled:false freeze + STATE.md v14.0 Freeze Flags block; Plan 03 = 70-VALIDATE-CHECKLIST.md (Phase 76 audit input, 34 rows) + 70-smoke.sh (6 XCUT-01 assertions, exits 0). Pre-existing drift flagged for cinematographer + audio_pipeline (Phase 75 closes). |
| 71 | FORM | Not started | form_factor parameterization (FORM-01..05). Foundational — every other track consumes `form_factor`. |
| 72 | DUB | Not started | CosyVoice + LTX 2.3 native audio (DUB-01..05). Parallel with Phase 73. Needs plan-phase research (CosyVoice variant A/B). |
| 73 | IMG | Not started | dreamina production-grade orchestration (IMG-01..06). Parallel with Phase 72. Needs plan-phase research (GLM-4.6V LHD/RHD accuracy). |
| 74 | TRANSITION | Not started | 创作+数据+生成三层 (TRANS-01..07). Most invasive. Needs plan-phase research (LTX FLF+ICLoRA combined workflow). |
| 75 | LINEAGE-BUMP | Not started | Re-run v13.0 P62 transform on 6 agents (XCUT-03). After all SKILL.md edits final. |
| 76 | VALIDATE | Not started | META-RULE audit (XCUT-02) + operator-action handoffs (XCUT-04) + milestone audit. Strictly LAST. |

### Critical Path

```
Phase 70 (FOUNDATION-AUDIT) ──▶ Phase 71 (FORM) ──┬──▶ Phase 72 (DUB)    ──┐
                                                   │                        │
                                                   └──▶ Phase 73 (IMG)    ──┤
                                                                            │
                                          Phase 72 + Phase 73 complete ──▶ Phase 74 (TRANSITION)
                                                                            │
                                                                            ▼
                                                                   Phase 75 (LINEAGE-BUMP)
                                                                            │
                                                                            ▼
                                                                   Phase 76 (VALIDATE)
                                                                            │
                                                                       strictly LAST
```

Phase 72 (DUB) and Phase 73 (IMG) execute in parallel. Phase 76 (VALIDATE) is strictly LAST (mirror v10.0 P51 / v11.0 P56 / v12.0 P61 / v13.0 P69 pattern).

### Hard Constraints Preserved (v14.0)

- **INFRA-04 serial constraint NOT lifted** — MEMORY.md `feedback-glm-overload-reduce-concurrency.md`. All transition engine routing decisions stay under `MAX_CONCURRENT_GL=1`. No `asyncio.gather` for GLM-coupled code paths.
- **EVAL-06 dry-run-first NOT changed** — curator `--live` mode is FROZEN for v14.0 duration per XCUT-01 (released only post-Phase 75 bump).
- **FOUND-08 15-expert set frozen** — TRANS-04 field-level ownership split (cinematographer creative intent / editor post-production execution). NO new `transition_designer` expert_id.
- **SKILL.md L1-L6 read-only invariant 例外破例** — PROJECT.md authorized for v14.0. Lineage regeneration mandatory per XCUT-03 (Phase 75 re-runs v13.0 P62 transform on 6 affected agents).

## Performance Metrics (v14.0)

- v14.0 phases total: 7 (Phases 70-76, continuing from v13.0 phase 69)
- v14.0 phases shipped: 0 (Phase 70 complete pending verification; 71-76 not started)
- v14.0 requirements total: 26 (FORM-01..05 + DUB-01..05 + IMG-01..06 + TRANS-01..07 + XCUT-01..04)
- v14.0 requirements mapped: 26/26 (100% coverage)
- v14.0 plans in shipped phases: 0
- v14.0 audit verdict: pending (Phase 76)

### Per-plan execution metrics

| Phase | Plan | Duration | Tasks | Files |
|-------|------|----------|-------|-------|
| 70 | P01 | ~15min | 1 | 1 (70-LINEAGE-INVENTORY.md) |
| 70 | P02 | ~8min | 1 | 3 (STATE.md + 2 operator-owned) |
| 70 | P03 | 5min | 2 | 2 (70-VALIDATE-CHECKLIST.md + 70-smoke.sh) |

## Decisions (v14.0 — in progress)

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 7 phases continuing from v13.0 phase 69 (70-76) | Sequential phase numbering; v13.0 ended at P69. | Applied 2026-07-09 |
| Phase 0 / FOUNDATION-AUDIT as explicit Phase 70 | PITFALLS X-1 (lineage cascade) + X-4 (curator drift) require enumerating every SKILL.md to be touched BEFORE any edits land. SUMMARY §Implications for Roadmap endorses explicit Phase 0. | Applied 2026-07-09 |
| Phase 72 (DUB) ∥ Phase 73 (IMG) parallel execution | Independent surfaces; both depend only on Phase 71 (FORM). SUMMARY §Implications for Roadmap endorses. Cuts wall time. | Applied 2026-07-09 |
| Phase 74 (TRANSITION) after Phase 73 (IMG), not before | FLF2V match-cut needs IMG's vision-verify precedent to confirm first/last frame content. Most invasive phase lands last to avoid cascading schema changes mid-milestone. | Applied 2026-07-09 |
| XCUT-02 (META-RULE X-2 _INSTRUCTION injection) as per-phase work, audited in Phase 76 | Per-phase work distributes the load; Phase 76 audit CI gate `grep MUST SKILL.md | wc -l == count_constraints(goal)` is the close-out verification. Not a standalone phase (research recommendation). | Applied 2026-07-09 |
| XCUT-04 (operator-action handoffs) in Phase 76 VALIDATE | Mirror v9.0 P43 / v11.0 P56 / v12.0 P61 / v13.0 P69 pattern — operator-action handoffs documented in milestone audit. | Applied 2026-07-09 |
| Lineage bump scope = 6 agents (not 15) | Only SKILL.md that actually change get bumped: cinematographer, editor, audio_pipeline, drawer, kais-movie-pipeline, kais-jimeng-cli. SUMMARY reconciled conflict #6 confirms ARCHITECTURE narrowed correctly from PITFALLS' worst-case 15. | Applied 2026-07-09 |
| LTX-2.3 FLF path evaluated per-transition, NOT assumed incapable | SUMMARY reconciled conflict #1: LTX-2.3 has ICLoRA (identity) AND FLF (first-last-frame) as separate workflows; STACK was wrong to say "LTX cannot do FLF." TRANS-06 + TRANS-07 reflect this. | Applied 2026-07-09 |
| MSR_FC canonical = 41 (not 17) | SUMMARY reconciled conflict #5: SKILL.md line 446 is STALE (pre-2026-07-01 A/B test). FORM-05 incidental tech-debt fix. | Applied 2026-07-09 |
| CosyVoice default variant gated on A/B benchmark | SUMMARY reconciled conflict #3: CosyVoice 2.0-0.5B default via `filliptm/ComfyUI_FL-CosyVoice3` (same node path supports v3 fallback). DUB-05 A/B test on 3-5 reference lines before locking default in `VERSION.json`. | Applied 2026-07-09 |
| Field-level ownership split (TRANS-04), NOT new expert | SUMMARY reconciled conflict #4: creative intent → cinematographer Step 9; post-production execution → editor Step 13. `transition_design.json` emitted by cinematographer, additively annotated by editor. FOUND-08 preserved. | Applied 2026-07-09 |
| **[Phase 70-01]** Lineage inventory uses canonical field names `lineage.skill_sha256` / `lineage.transform_date` / `lineage.transform_notes`, NOT roadmap shorthand `source_sha` / `transform_rule_id` / `transform_timestamp` | Roadmap shorthand was authored from research SUMMARY; actual agent YAML schema (verified against 5 live `~/.hermes/agents/*.agent.yaml` files + `scripts/transform_skill_to_agent.py:191-197`) uses canonical names. Phase 75/76 grep for `source_sha` would silently pass on empty set. Mapping documented explicitly in 70-LINEAGE-INVENTORY.md. | Applied 2026-07-09 (commit a0a15e2ce) |
| **[Phase 70-01]** Pre-existing drift captured as MISMATCH, NOT fixed mid-Phase-70 | `cinematographer` + `audio_pipeline` agent.yaml `lineage.skill_sha256` mismatch their current SKILL.md hashes (drift introduced between v13.0 P62 transform 2026-07-07 and 2026-07-09). Phase 75 closes it as side-effect of re-transform; fixing mid-Phase-70 would violate read-only enumeration scope. | Applied 2026-07-09 (commit a0a15e2ce) |
| **[Phase 70-01]** Lineage bump scope = 3 existing agent.yaml files (NOT 6) | Only `cinematographer` / `editor` / `audio_pipeline` have agent YAMLs today. `drawer` merged into `visual_executor` (Phase 14 DEPRECATED stub); `kais-movie-pipeline` + `kais-jimeng-cli` are skill-only orchestration/tool skills (not native expert agents per FOUND-08 frozen 15-expert set). Phase 75 bumps 3 only. | Applied 2026-07-09 (commit a0a15e2ce) |
| **[Phase 70-03]** VALIDATE-CHECKLIST authored hand-rolled (no prior template in repo) | PATTERNS.md No Analog Found section confirms no `.planning/**/CHECKLIST*.md` exists. Hand-rolled from RESEARCH.md Validation Architecture spec. 34 table rows covering 6 XCUT-01 sub-claims + INFRA-04/EVAL-06/FOUND-08/L1-L6 hard-constraint preservation + cross-repo pin re-hash procedure + META-RULE X-2 audit rows. | Applied 2026-07-09 (commit 6e4cba4e4) |
| **[Phase 70-03]** smoke.sh XCUT-01d uses config.yaml grep (not `hermes curator status` CLI) | Config flag is the canonical freeze mechanism per RESEARCH Pattern 2; works without hermes CLI in execution environment; CLI depends on prompt_toolkit which may not be in scope for Phase 76 CI runner. | Applied 2026-07-09 (commit f665e98df) |
| **[Phase 70-03]** Canonical field-name discipline encoded in checklist callout | `lineage.skill_sha256` (NOT `source_sha`) — Phase 76 grep for `source_sha` silently passes on empty set (false-green). Checklist prevents the exact bug Phase 76 exists to catch. Mapping documented in both 70-LINEAGE-INVENTORY.md + 70-VALIDATE-CHECKLIST.md. | Applied 2026-07-09 (commit 6e4cba4e4) |

### Decisions carried forward (still relevant)

| Decision | Rationale | Why relevant to v14.0 |
|----------|-----------|------------------------|
| v10.0 design suite as canonical implementation blueprint | 7 design docs + 3 schemas + 1 lint script shipped 2026-07-07. v11.0-v13.0 implemented + rolled out. | v14.0 lineage bump (Phase 75) re-runs v13.0 P62 transform flow per `04-MIGRATION-PATH.md §2`. |
| v9.0 cross-repo topology (plan → hermes-agent, code → kais-hermes-skills) | Commit `f10495332` post-v9.0 established the split. | v14.0 reactivates this topology (first kais-movie-pipeline-focused milestone since v9.0). |
| v13.0 Phase 64 EVAL-01..04 deferred as operator-handoff | Live GLM/mem0 secrets needed. | v14.0 does NOT depend on Phase 64 data (different scope — kais-movie-pipeline content, not orchestrator runtime). |

## Accumulated Context

### v14.0 Goal Restatement

把 kais-movie-pipeline 从「竖屏短剧专用」升级为「横竖双 default 的通用短片创作管线」,同步升级 4 个核心生成环节:

1. **FORM (Phase 71)** — Pipeline `form_factor` parameterization (横竖并行双 default) — foundational, every other track consumes `form_factor`
2. **DUB (Phase 72)** — CosyVoice 2.0-0.5B TTS default (replacing IndexTTS2) + LTX 2.3 native audio division rule
3. **IMG (Phase 73)** — dreamina cli production-grade orchestration (retry / vision-verify mandatory gate / RHD-LHD mitigation / SLA tracking)
4. **TRANSITION (Phase 74)** — 创作+数据+生成三层协作 (E-Konte Layer 5 schema extension + `transition_design.json` first-class asset + per-transition engine routing)

Plus 3 cross-cutting phases: Phase 70 (FOUNDATION-AUDIT lineage baseline) + Phase 75 (LINEAGE-BUMP regeneration) + Phase 76 (VALIDATE audit + operator handoffs).

**关键范式声明 (v14.0-specific):**

- **SKILL.md L1-L6 read-only invariant 例外破例** — PROJECT.md authorized; lineage regeneration mandatory per XCUT-03
- **跨 repo 模式 (沿用 v9.0)** — plan → hermes-agent/.planning/;code → kais-hermes-skills/
- **Phase 72 ∥ Phase 73 parallel** — DUB and IMG are independent surfaces, both depend only on FORM
- **TRANS-07 research-scope only** — LTX FLF+ICLoRA combined workflow validated on 1-2 shots, NOT pipeline-integrated; v15+ rollout gated by validation result

### Blockers / Risks (v14.0 — active)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **CosyVoice ComfyUI node maturity (7 months old, install docs missing)** | MEDIUM | MEDIUM (DUB-01 default could be blocked if node install fails) | Phase 72 plan-phase research runs install healthcheck before locking default; DUB-04 keeps IndexTTS2 as DEPRECATED fallback. |
| **GLM-4.6V LHD/RHD detection accuracy on dreamina interiors unverified** | MEDIUM | MEDIUM (IMG-03 vision-verify gate false-positive rate unknown) | Phase 73 plan-phase research validates empirically; IMG-09 false-positive threshold calibration deferred to v15+. |
| **LTX FLF+ICLoRA combined workflow has no public turnkey option** | HIGH | LOW (TRANS-07 is research-scope only, NOT pipeline-integrated) | Phase 74 validation on 1-2 shots; v15+ production rollout gated by report. Zero pipeline integration risk in v14.0. |
| **Lineage cascade silently corrupts agent YAMLs mid-milestone** | MEDIUM | HIGH (PITFALL X-1) | Phase 70 FOUNDATION-AUDIT captures baseline; curator `--live` frozen; Phase 75 LINEAGE-BUMP regenerates deterministically; Phase 76 CI assertion `agent.yaml.source_sha == sha256(SKILL.md)`. |
| **"文档有规则,代码没执行" META-RULE X-2 regression** | HIGH | HIGH (most-recurring bug pattern per SUMMARY §Pitfalls) | XCUT-02 enforced per-phase: every MUST/MUST NOT in SKILL.md has corresponding `_INSTRUCTION` constant in `goal` f-string + test. Phase 76 CI gate `grep MUST SKILL.md | wc -l == count_constraints(goal)`. |
| **CosyVoice + LTX 2.3 native audio both enabled (PITFALL D-1)** | MEDIUM | HIGH (doubled audio / phase cancellation / lip-sync mismatch) | DUB-02 schema validator rejects; unit test asserts no shot has both `ltx_native_dialogue AND cosyvoice_overlay`. |
| **Operator wavs missing for CosyVoice clone mode (PITFALL D-2)** | MEDIUM | LOW (fail-fast with explicit error) | DUB-03 schema field + fail-fast error. Documented as operator-action handoff in Phase 76. |

### v14.0 Freeze Flags (active — set by Phase 70, released by Phase 75)

| flag | value | set_by | released_by | enforcement |
|------|-------|--------|-------------|-------------|
| `curator.enabled` | `false` | Phase 70 (2026-07-09) | Phase 75 (post-bump) | `~/.hermes/config.yaml` line 458 (code-enforced via `agent/curator.py:is_enabled()` lines 141-144; `--live` flag blocked at `hermes_cli/curator.py:270-272`) |
| `curator.consolidate` | `false` (already default) | Phase 70 (defense-in-depth) | Phase 75 (post-bump) | `~/.hermes/config.yaml` line 463 (already false; documented for traceability) |
| `cross_repo_pin.hermes-agent` | `8f70fcf7f0604db21158f86f8495f3d9ce3c9ab1` | Phase 70 | Phase 76 (assertion) | STATE.md record (documentation-only; Phase 76 re-hashes from this pin) |
| `cross_repo_pin.kais-hermes-skills` | `d9620369e48eec51c31ee72ac8827c288eaccf71` | Phase 70 | Phase 76 (assertion) | STATE.md record (documentation-only) |

**Freeze rationale:** PITFALL X-1 (lineage cascade) + X-4 (curator drift) — no curator tick can silently mutate `~/.hermes/agents/*.agent.yaml` during v14.0. The freeze blocks even `hermes curator evolve --live --skip-canary` (VERIFIED at `hermes_cli/curator.py:270-272` via `is_enabled()` check, not assumed). `hermes curator status` CLI reports `curator: DISABLED` as operator-visible confirmation.

**Verified 2026-07-09:**

- `agent/curator.py:is_enabled()` returns `False` (Python-level check)
- `hermes curator status` CLI prints `curator: DISABLED`
- Backup of pre-freeze config at `~/.hermes/config.yaml.pre-v14.0-freeze.bak`
- Config flag read fresh on every curator call (`_load_config()` line 125-138) — no gateway restart needed (survives systemd `Restart=always` cycle per MEMORY.md `hermes-gateway-systemd.md`)

**Release procedure (Phase 75 final action):**

1. Confirm Phase 75 lineage bump complete (all 3 existing `agent.yaml` files regenerated: `cinematographer`, `editor`, `audio_pipeline`)
2. Edit `~/.hermes/config.yaml` line 458: `enabled: false` -> `enabled: true` (remove the `# FROZEN for v14.0 ...` comment)
3. Run `hermes curator status` to verify output reports `ENABLED`
4. Run `agent/curator.py:is_enabled()` to verify returns `True`
5. (Optional) Remove backup `~/.hermes/config.yaml.pre-v14.0-freeze.bak`

**Threat model T-70-01 (HIGH, Tampering) mitigation:** Operator running `hermes curator evolve --live --skip-canary` during v14.0 window is blocked at `hermes_cli/curator.py:270-272` BEFORE the `--live` flag is even read (line 274). Residual: `--skip-canary` is audit-logged at `hermes_cli/curator.py:344-349` (`canary_pass=None`); Phase 76 VALIDATE checks the audit log for any live-tick during v14.0.

### Pending Todos

None yet (milestone just started).

## Deferred Items

Items acknowledged and carried forward (NOT in v14.0 scope):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| **v13.0 Phase 64 LIVE-EVAL-EXEC (4 reqs)** | 3 operator smoke tests + report (GLM/mem0 secrets) | Deferred to v15+ planning (operator-handoff per v13 VALIDATE-01 spec) | v13.0 close (2026-07-08) |
| **v13.0 Phase 66 CURATOR-LIVE-TICK (2 reqs)** | 1st live tick + runbook | Deferred to v15+ planning (operator-handoff) | v13.0 close (2026-07-08) |
| **v13.0 物理分区 (mem0 split)** | v13 EVAL-02 data drives v15+ decision | Deferred to v15+ | v13.0 planning |
| **v13.0 INFRA-04 async concurrency lift** | GLM capacity expansion gate | Deferred to v15+ (NOT lifted in v14.0 per MEMORY.md) | v13.0 planning |
| **v14.0 FORM-06 per-shot form_factor override** | Anti-pattern (cross-shot consistency collapse) | Deferred to v15+ (acknowledged as anti-feature) | v14.0 planning (2026-07-09) |
| **v14.0 FORM-07 auto-form_factor inference** | Unreliable (~40% wrong per FEATURES research) | Deferred to v15+ | v14.0 planning |
| **v14.0 DUB-06 real-time TTS streaming** | Race-condition architecture needed | Deferred to v15+ | v14.0 planning |
| **v14.0 DUB-07 CosyVoice 2 instruct2 fine-grained control** | P2 differentiator; defer until CosyVoice 2 baseline proven | Deferred to v15+ | v14.0 planning |
| **v14.0 IMG-07 auto-scaling concurrency** | Current 10-parallel validated; auto-tune adds complexity | Deferred to v15+ | v14.0 planning |
| **v14.0 IMG-08 multi-model routing** | Defer until v14.0 dreamina_manager pattern proven | Deferred to v15+ | v14.0 planning |
| **v14.0 IMG-09 vision-verify false-positive threshold calibration** | Research gap; needs production data | Deferred to v15+ | v14.0 planning |
| **v14.0 TRANS-08 AI-generated whip pan transitions** | Current engines unreliable | Deferred to v15+ | v14.0 planning |
| **v14.0 TRANS-11 LTX FLF+ICLoRA production rollout** | Research-scope validation in TRANS-07; production gated by report | Deferred to v15+ if not turnkey | v14.0 planning |
| **v14.0 XCUT-05 full 15-agent lineage bump automation** | v14.0 bumps 6; automation for full 15 deferred | Deferred to v15+ | v14.0 planning |

## Session Continuity

**If session is lost, restore context by reading:**

1. `.planning/PROJECT.md` §"Current Milestone: v14.0" — 4-track scope + cross-repo topology + hard constraints
2. `.planning/ROADMAP.md` — 7 phases (70-76), 26/26 reqs mapped, critical path, phase details
3. `.planning/REQUIREMENTS.md` — 26 v14.0 reqs + Traceability table + Out of Scope
4. `.planning/research/v14-4track-upgrade/SUMMARY.md` — HIGH-confidence research (4 parallel researcher + synthesizer, 6 reconciled conflicts)
5. `.planning/MILESTONES.md` — v1-v13 history (FOUND-08 / INFRA-04 / EVAL-06 invariants)
6. `.planning/milestones/v13.0-ROADMAP.md` — v13.0 archive (Phase 62 transform flow reused in Phase 75)
7. `.planning/research/v10-orchestrator-design/04-MIGRATION-PATH.md` — §2 lineage transform 5-step procedure (canonical for Phase 75)
8. MEMORY.md `feedback-glm-overload-reduce-concurrency.md` (INFRA-04 serial constraint — NOT lifted in v14.0)
9. `~/.hermes/agents/` — 21 agent YAMLs (6 to be bumped in Phase 75: cinematographer, editor, audio_pipeline, drawer, kais-movie-pipeline, kais-jimeng-cli)

**Next action:** `/gsd:plan-phase 70` to plan Plans 02 (curator freeze + STATE.md freeze block) and 03 (smoke.sh + VALIDATE-CHECKLIST). Plan 01 (70-LINEAGE-INVENTORY.md) shipped 2026-07-09 — pre-v14.0 lineage baseline captured.

---

*Last updated: 2026-07-09 — v14.0 Phase 70 COMPLETE (3/3 plans shipped, ready for verification). Plan 01 (commit a0a15e2ce): lineage baseline (6 SKILL.md hashes + 3 agent.yaml lineage.skill_sha256 + cross-repo pins hermes-agent=8f70fcf7 / kais-hermes-skills=d9620369). Plan 02 (commit ebcf22fbf): curator freeze (config.yaml curator.enabled:false + STATE.md v14.0 Freeze Flags block). Plan 03 (commits 6e4cba4e4 + f665e98df): Phase 76 VALIDATE-CHECKLIST.md (34 rows) + 70-smoke.sh (6 XCUT-01 assertions, exits 0). Pre-existing drift flagged for cinematographer + audio_pipeline (Phase 75 closes). 7 phases (70-76), 26/26 reqs mapped. Phase 72 ∥ Phase 73 parallel. Phase 76 strictly LAST. Cross-repo: hermes-agent/.planning/ + kais-hermes-skills/. SKILL.md L1-L6 read-only exception破例 authorized per PROJECT.md; lineage regeneration mandatory per XCUT-03 in Phase 75.*
