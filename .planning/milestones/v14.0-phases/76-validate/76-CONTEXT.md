# Phase 76: VALIDATE - Context

**Gathered:** 2026-07-10
**Status:** Ready for planning
**Mode:** Auto-generated (user prefers direct plan-phase dispatch)

<domain>
## Phase Boundary

Cross-cutting audit closes v14.0 with verified lineage coverage, META-RULE X-2 _INSTRUCTION injection test-count diff, cross-repo commit pin assertion, INFRA-04 / EVAL-06 / FOUND-08 preservation, documented operator-action handoffs, and the milestone audit doc + tag.

Requirements covered: XCUT-02 (META-RULE X-2 audit), XCUT-04 (operator-action handoff documentation).

**Strictly LAST phase** per ROADMAP — mirrors v10.0 P51 / v11.0 P56 / v12.0 P61 / v13.0 P69 pattern.

**Out of scope:** v15+ planning; deferred requirements (FORM-06/07, DUB-06/07/08, IMG-07/08/09, TRANS-08/09/10/11, XCUT-05); production rollout decisions (TRANS-07 verdict gates TRANS-11).

</domain>

<decisions>
## Implementation Decisions

### META-RULE X-2 Audit (XCUT-02)
- **Audit script:** New `.planning/phases/76-validate/76-meta-rule-x2-audit.sh` — bash script that:
  - Grep `MUST|MUST NOT` patterns in v14.0-touched SKILL.md files (17 files)
  - Count `MUST` occurrences
  - Grep corresponding `_INSTRUCTION` constants in p07/p09/p10/p13 phase modules
  - Count `_INSTRUCTION` constants
  - Run goal-content test count (test_p07_unit + test_p09_unit + test_p09_transition_unit + test_p10_unit)
  - Assert: every MUST has a corresponding _INSTRUCTION + test
- **Coverage gaps:** Document any MUST without _INSTRUCTION or test as gaps in milestone audit

### Cross-Repo Commit Pin Assertion (ROADMAP SC#2)
- **hermes-agent pin:** `6171e5202728770873dd91fe4e8f3b84610883e6` (final v14.0 commit after Phase 75)
- **kais-hermes-skills pin:** `ba58c2548ab82f0cd9acd7cc7af14402137f8520` (last code-review fix from Phase 74)
- **P70 baseline pins:** hermes-agent `8f70fcf7f0604db21158f86f8495f3d9ce3c9ab1`; kais-hermes-skills `d9620369e48eec51c31ee72ac8827c288eaccf71`
- **Assertion:** Both current pins are descendants of P70 baseline pins (per `git merge-base --is-ancestor`)
- **Recording:** STATE.md gets a `v14.0 Cross-Repo Pins (FINAL)` block documenting both pins

### Operator-Action Handoff Documentation (XCUT-04)
- **DUB-03:** CosyVoice voice_clone_reference_wav per character (3-10s samples) — Phase 72 operator-action handoff
- **TRANS-06 / XCUT-04b:** Hailuo/Vidu API keys (opt-in for cloud transition engines) + Wan2.2 ComfyUI node install
- **IMG-03 / XCUT-04c:** Vision-verify API cost budget (GLM-4.6V batch calls at production scale 213-shot × 5 refs ≈ 1065 images / 6 per batch ≈ 178 calls)
- **TRANS-07:** LTX-FLF+ICLoRA validation report disposition (operator runs 1-2 reference shots; gates TRANS-11 v15+ rollout)
- **Phase 71 FORM:** horizontal-screen-framing.md citation fair-use review (Phase 71 manual UAT item)
- **Phase 74 TRANSITION:** Tier 1 transition-design.md content substance review (Phase 71 manual UAT item deferred)

### Hard-Constraint Preservation Verification (ROADMAP SC#4)
- **INFRA-04 serial constraint:** Verify no `asyncio.gather` introduced in v14.0 code paths that violates `MAX_CONCURRENT_GL=1`. Spot-check dreamina_manager.py (uses asyncio.Semaphore(10) — IMG-01 contract, NOT GLM concurrency); p09/p10/p13 modules; kais_aigc transition routing (declarative only per TRANS-06).
- **EVAL-06 dry-run-first:** Verify curator `--live` was frozen during v14.0 (Phase 70 imposed), released only post-bump in Phase 75. Curator state check: `curator.enabled: true` (released).
- **FOUND-08 15-expert set:** Verify zero new `expert_id` added in v14.0 SKILL.md frontmatter. TRANS-04 field-level ownership split (cinematographer/editor) preserved the 15-expert set.
- **SKILL.md L1-L6 read-only exception破例:** Documented in PROJECT.md (v14.0 pre-authorized per ROADMAP). Lineage regeneration mandatory per XCUT-03 — verified by Phase 75 75-lineage-assert.sh exit 0.

### Milestone Audit Document
- **File:** `.planning/milestones/v14.0-MILESTONE-AUDIT.md` (NEW)
- **Structure:** Mirror v13.0-MILESTONE-AUDIT.md (existing at `.planning/milestones/v13.0-MILESTONE-AUDIT.md` per v13.0 archive)
- **Sections:**
  - Executive Summary (v14.0 scope, 7 phases, 26 reqs mapped)
  - Requirement Reconciliation Table (26/26 reqs: satisfied / audit / operator-handoff)
  - Phase-by-Phase Summary (Phases 70-76)
  - Lineage Coverage (XCUT-03 closure: 15 agent.yaml regenerated, 2 skill-only, drawer DEPRECATED)
  - META-RULE X-2 Audit Results (XCUT-02 closure: MUST count vs _INJECTION count vs test count)
  - Cross-Repo Commit Pins (final + baseline + ancestry assertion)
  - Hard-Constraint Preservation (INFRA-04 / EVAL-06 / FOUND-08)
  - Operator-Action Handoffs (4 items per XCUT-04)
  - Verdict (passed / gaps_found / tech_debt) — mirror v13.0 P69 verdict pattern
- **Tag placement:** `git tag v14.0` after audit doc committed

### Claude's Discretion
- Exact bash script structure for 76-meta-rule-x2-audit.sh (within "grep MUST, count _INSTRUCTION, run tests, compare" spec)
- Milestone audit doc section ordering (within required sections above)
- Verdict choice (passed / gaps_found / tech_debt) — default to `passed` if all checks pass; `tech_debt` if operator-action handoffs remain (mirror v13.0 P69 precedent)
- Operator-action handoff ordering in milestone audit

</decisions>

<canonical_refs>
## Canonical Refs (Phase 76 downstream agents MUST read)

**Hermes-agent repo:**
- `.planning/ROADMAP.md` — Phase 76 section (lines 119-135)
- `.planning/REQUIREMENTS.md` — XCUT-02 + XCUT-04 (cross-cutting)
- `.planning/STATE.md` — v14.0 progress; current hermes-agent pin
- `.planning/phases/70-foundation-audit/70-VALIDATE-CHECKLIST.md` (192 lines — Phase 76 audit input per Phase 70 Plan 03 deliverable)
- `.planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md` (P70 baseline pins for cross-repo ancestry assertion)
- `.planning/phases/75-lineage-bump/75-LINEAGE-BUMP-REPORT.md` (lineage coverage closure per XCUT-03)
- `.planning/phases/75-lineage-bump/75-lineage-assert.sh` (XCUT-03 CI assertion; Phase 76 re-runs as sanity check)
- `.planning/milestones/v13.0-MILESTONE-AUDIT.md` (v13.0 audit doc — structural template; if not present, mirror v9.0 / v10.0 / v11.0 / v12.0 pattern per SUMMARY)
- `.planning/phases/71-form/71-CONTEXT.md`, `72-dub/72-CONTEXT.md`, `73-img/73-CONTEXT.md`, `74-transition/74-CONTEXT.md` (per-phase operator-action handoff context)
- `.planning/phases/71-form/71-VERIFICATION.md`, `72-VERIFICATION.md`, `73-VERIFICATION.md`, `74-VERIFICATION.md`, `75-VERIFICATION.md` (manual UAT items to consolidate)

**Kais-hermes-skills repo (read-only):**
- All 17 v14.0-touched SKILL.md files (per `git diff d9620369..ba58c254 --name-only | grep SKILL.md`)
- p07_scene_generation.py + p09_shot_breakdown.py + p10_voice.py + p13_delivery.py + p04_character_design.py (META-RULE X-2 _INJECTION audit targets)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **70-VALIDATE-CHECKLIST.md (192 lines):** Phase 70 Plan 03 deliverable; 34-row audit checklist covering XCUT-01..04 + FORM-01..05 + DUB-01..05 + IMG-01..06 + TRANS-01..07. Phase 76 audit reuses this as input.
- **v13.0-MILESTONE-AUDIT.md (if exists):** Structural template for v14.0-MILESTONE-AUDIT.md
- **70-smoke.sh pattern:** Bash smoke script skeleton for 76-meta-rule-x2-audit.sh
- **75-lineage-assert.sh pattern:** 15-expert sha256 assertion; Phase 76 re-runs as XCUT-03 closure verification

### Established Patterns
- **Cross-repo ancestry assertion:** `git merge-base --is-ancestor <baseline> <current>` per repo
- **Operator-action handoff documentation:** Mirror v9.0 P43 + v13.0 P69 pattern (each handoff has trigger condition + operator action + cost/risk + production-readiness gate)
- **Verdict pattern:** `passed` (all reqs satisfied, no blockers) / `gaps_found` (some reqs incomplete) / `tech_debt` (operator-action handoffs remain but reqs structurally satisfied) — mirror v13.0 P69

### Integration Points
- Phase 76 audit consumes Phase 75 lineage bump closure
- Phase 76 audit consumes Phases 71-74 manual UAT items (consolidated into operator-action handoff section)
- Tag `v14.0` is the final action; release history for downstream packagers

</code_context>

<specifics>
## Specific Ideas

- **Cross-repo pin ancestry assertion:** Both final pins must be descendants of P70 baseline pins. Use `git -C <repo> merge-base --is-ancestor <baseline> <current>` and assert exit 0.
- **Operator-action handoff lifecycle:** Each handoff documented with: (1) Trigger — what causes it to be needed; (2) Action — operator manual step; (3) Cost/risk — what happens if not done; (4) Production-readiness gate — what's blocked until done.
- **v14.0 verdict:** Default `tech_debt` (mirror v13.0 P69) because: 4 operator-action handoffs remain (DUB-03 voice wavs / DUB-05 A/B benchmark / XCUT-04b Hailuo+Vidu keys / TRANS-07 LTX-FLF validation). All 26 reqs structurally satisfied but production readiness gated on operator actions.
- **Tag placement:** `git tag v14.0 -m "v14.0: kais-movie-pipeline 4-Track Upgrade (FORM / DUB / IMG / TRANSITION)"` as the final commit
- **Milestone archive:** Post-tag, `.planning/ROADMAP.md` + `.planning/REQUIREMENTS.md` get archived to `.planning/milestones/v14.0-ROADMAP.md` + `v14.0-REQUIREMENTS.md` (handled by `complete-milestone` lifecycle step in gsd-autonomous, NOT this phase)

</specifics>

<deferred>
## Deferred Ideas

- **v15.0 roadmap:** Post-v14.0 milestone planning; new milestone command after archive
- **Production rollout of TRANS-07 LTX-FLF+ICLoRA:** Gated by operator validation verdict; v15+ if turnkey
- **Automation of recurring Phase 76 audit patterns:** Future milestone template; not this phase
- **15-agent lineage bump automation (XCUT-05):** v15+
- **Auto-scaling dreamina concurrency (IMG-07):** v15+ if quota wall hit
- **Multi-model routing for IMG (IMG-08):** v15+ after v14.0 dreamina_manager pattern proven
- **Vision-verify false-positive threshold calibration (IMG-09):** v15+ with IMG-05 dashboard production data

</deferred>
