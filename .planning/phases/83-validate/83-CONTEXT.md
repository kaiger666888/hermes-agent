# Phase 83: VALIDATE - Context

**Gathered:** 2026-07-10
**Status:** Ready for planning

<domain>
## Phase Boundary

v15.0 milestone close — mirrors v14.0 P76 / v13.0 P69 / v10.0 P51 VALIDATE pattern. Re-runs META-RULE X-2 audit extended to v15.0 constants, documents v14.0 tech_debt closure status (operator-action items preserved, not closed), authors milestone audit doc with verdict, records cross-repo final pins, places tag `v15.0`.

**In scope:**
- `83-meta-rule-x2-audit.sh` — copy of v14.0's `76-meta-rule-x2-audit.sh` adapted for v15.0 (updated pins, phase count, confirms 0 new `_INSTRUCTION` constants + 0 movie-experts SKILL.md touches + existing goal-content tests pass).
- `v15.0-MILESTONE-AUDIT.md` — milestone audit doc with verdict (`tech_debt` — 15/15 automated reqs met, operator-action items deferred to v16+ operator runtime), v14.0 tech_debt closure status, v15.0 stats, cross-repo final pins.
- Tag `v15.0` placed after audit doc authored + committed.
- STATE.md + ROADMAP.md + REQUIREMENTS.md final updates (milestone complete).

**Out of scope:**
- v16+ milestone planning (separate `/gsd:new-milestone` invocation after v15.0 close).
- Operator actually running the 6 operator-action handoff tools (DUB-05 benchmark + DUB-03 voice sample sourcing + IMG-09 calibration on production data + TRANS-07 LTX-FLF validation + XCUT-04b cloud engine API key acquisition + XCUT-04c production data collection for cost tracking). These are operator-action handoffs preserved at v15.0 close — operator runs them at v16+ runtime.
- v14.0 carry-forward items NOT closed by v15.0 (FORM-06/07, DUB-06/07/08, IMG-07/08, TRANS-08/09/10/11) — these remain deferred to v16+ per REQUIREMENTS.md "Future Requirements" section.
- Code changes to close tech_debt (v15.0 is audit + documentation only — no code modifications in VALIDATE phase).

</domain>

<decisions>
## Implementation Decisions

### Audit Script & Coverage
- Audit script location: copy v14.0's `76-meta-rule-x2-audit.sh` from `.planning/milestones/v14.0-phases/76-validate/` to `.planning/phases/83-validate/83-meta-rule-x2-audit.sh`. Update v15.0 references (pins, phase count from 7 phases (77-83), milestone version v14.0 → v15.0).
- v15.0 `_INSTRUCTION` coverage: audit confirms "v15.0 added 0 new `_INSTRUCTION` constants" — all 6 code phases (77-82) created scripts/plugins, not phase modules with `_INSTRUCTION` constants. The 5 existing phase modules (p07/p09/p10/p12/p13 from v14.0) untouched. Document as INFO in audit output, not WARNING.
- SKILL.md MUST count: audit confirms "v15.0 did not touch movie-experts SKILL.md files" — only `kais-jimeng-cli/SKILL.md` was touched (Phase 81, minimal, no MUST markers). The 17 v14.0 MUST-bearing SKILL.md files unchanged. Document as INFO.
- Goal-content tests: re-run existing goal-content tests (from kais-movie-pipeline tests). v15.0 added no new tests. All should pass since phase modules untouched. Document as INFO.

### tech_debt Closure + Milestone Audit
- v14.0 tech_debt closure status: document as "operator-action handoff preserved — tooling delivered, operator runs at v16+ runtime" (NOT "closed"). All 3 items (DUB-05 lock / IMG-09 thresholds / TRANS-07 verdict) are operator-action handoffs — v15.0 delivered the tooling, operator hasn't run them yet. Audit doc §"v14.0 tech_debt Closure" lists each item + status:
  - DUB-05 A/B benchmark: Phase 77 delivered `run_cosyvoice_benchmark.py` + `lock_cosyvoice_default.py`. Operator runs benchmark + locks VERSION.json when ready. **Status: tooling delivered, operator-action pending.**
  - IMG-09 false-positive calibration: Phase 79 delivered `calibrate_vision_verify.py` + `apply_vision_verify_thresholds.py` + `vision_verify.py` per-stratum threshold override. Operator runs calibration on production MetricsBuffer data + applies thresholds when ready. **Status: tooling delivered, operator-action pending.**
  - TRANS-07 LTX-FLF validation: Phase 78 delivered `run_ltx_flf_validation.py` + `update_ltx_flf_verdict.py` + ComfyUI workflow JSON. Operator runs 1-2 reference shots + records verdict when ready. **Status: tooling delivered, operator-action pending.**
- Milestone audit verdict: `tech_debt` — all automated criteria met (15/15 requirements structurally satisfied), but operator-action items deferred to v16+ operator runtime. Mirrors v13.0 P69 (tech_debt) + v14.0 P76 (tech_debt) pattern. Still tagged `v15.0`.
- Cross-repo pins: record hermes-agent + kais-hermes-skills commit hashes at close (in audit doc + STATE.md). Pins capture exact state of both repos at v15.0 close. Computed via `git rev-parse HEAD` for each repo at close time.
- Tag `v15.0`: placed via `git tag v15.0` after audit doc authored + committed. Mirrors v10.0/v13.0/v14.0 pattern. Tag message references audit doc. Withhold tag if audit finds blocking issue (shouldn't happen per tech_debt verdict).

### Claude's Discretion
- **Audit script adaptation:** The v14.0 audit script has 3 phases (MUST count / _INSTRUCTION count / goal-content tests). For v15.0, the script confirms coverage is unchanged (0 new items). The script output should clearly state "v15.0 added 0 new audit targets — coverage matches v14.0 baseline". If the script fails on any phase, that's a WARNING (not hard-fail per v14.0 exit semantics).
- **Milestone audit doc structure:** Follow v14.0-MILESTONE-AUDIT.md structure (available at `.planning/milestones/v14.0-MILESTONE-AUDIT.md`). Sections: §1 Summary + verdict, §2 Phase-by-phase outcomes (77-83), §3 Requirement traceability (15/15), §4 Cross-cutting constraints preserved, §5 v14.0 tech_debt closure status, §6 v15.0 tech_debt deferred to v16+, §7 Operator-action handoffs (6 items), §8 Cross-repo final pins, §9 Hard constraints verification, §10 Stats + timeline.
- **Cross-repo pin computation:** At audit doc authoring time, run `git -C /data/workspace/hermes-agent rev-parse HEAD` + `git -C /data/workspace/kais-hermes-skills rev-parse HEAD`. Record both full + short hashes in audit doc §8 + STATE.md "Cross-Repo Pins" section.
- **Tag placement:** `git -C /data/workspace/hermes-agent tag -a v15.0 -m "v15.0 Operator-Action Closure Tooling SHIPPED"` after audit doc committed. Annotated tag (not lightweight) for message.
- **STATE.md final updates:** Update milestone status to `complete`, progress to 100%, add "v15.0 SHIPPED 2026-07-10" line. Add v15.0 to milestone history arc.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`.planning/milestones/v14.0-phases/76-validate/76-meta-rule-x2-audit.sh`** — v14.0 audit script template. Copy + adapt for v15.0.
- **`.planning/milestones/v14.0-MILESTONE-AUDIT.md`** — v14.0 milestone audit doc template. Follow structure for v15.0.
- **`.planning/milestones/v14.0-ROADMAP.md`** + **`v14.0-REQUIREMENTS.md`** — v14.0 archive. Reference for v15.0 milestone arc.
- **`.planning/STATE.md`** — current state. Updated at v15.0 close (milestone complete, 100% progress).
- **`.planning/ROADMAP.md`** — current roadmap. Phase 83 marked complete at close.
- **`.planning/REQUIREMENTS.md`** — 15 v15.0 reqs. All marked satisfied at close.

### Established Patterns
- **VALIDATE phase pattern:** v10.0 P51 / v13.0 P69 / v14.0 P76 all follow same structure: audit script run + milestone audit doc + tag placement.
- **Cross-repo pin pattern:** v14.0 recorded `hermes-agent 4e7c58cc` + `kais-hermes-skills ba58c254`. v15.0 records new pins at close.
- **tech_debt verdict pattern:** v13.0 + v14.0 both shipped with `tech_debt` verdict (acknowledged deferrals, not blocking). v15.0 follows same pattern.
- **Tag placement:** annotated tag (`git tag -a`) with message referencing milestone + audit doc.

### Integration Points
- **v15.0 phases 77-82:** all code + planning artifacts. VALIDATE audits their outcomes.
- **v14.0 archive (`.planning/milestones/v14.0-*`):** reference for v15.0 milestone arc + tech_debt items.
- **Both git repos:** hermes-agent + kais-hermes-skills. Cross-repo pins recorded at close.
- **Tag `v15.0`:** annotated tag on hermes-agent repo. kais-hermes-skills may also get tagged (v14.0 tagged both).

</code_context>

<specifics>
## Specific Ideas

- **VALIDATE is audit + documentation only:** No code changes in Phase 83. The audit script runs existing tests + counts. The audit doc summarizes phase outcomes. The tag marks the milestone.
- **tech_debt verdict is honest:** v15.0 delivered all automated tooling (15/15 requirements structurally satisfied). Operator-action items are preserved handoffs, not failures. The `tech_debt` verdict acknowledges this without overstating (not `passed`) or understating (not `gaps_found`).
- **Cross-repo pins are load-bearing:** Future v16+ work needs to know the exact v15.0 close state of both repos. Pins enable ancestry assertions (v16+ commits are descendants of v15.0 pins).
- **Tag is the milestone marker:** `v15.0` tag is the single source of truth for "v15.0 was shipped here". Annotated tag with message for git history clarity.
- **All 6 operator-action handoffs documented:** DUB-05 (Phase 77) + TRANS-07 (Phase 78) + IMG-09 (Phase 79) + DUB-03 (Phase 80) + XCUT-04b (Phase 81) + XCUT-04c (Phase 82 production data). Each documented in audit doc §7 with status + tooling delivered + operator next step.

</specifics>

<deferred>
## Deferred Ideas

- **v16+ milestone planning** — separate `/gsd:new-milestone` invocation after v15.0 close.
- **Operator running the 6 operator-action tools** — operator-action, not automatable. Operator runs when live infrastructure + production data available.
- **v14.0 carry-forward items NOT closed by v15.0** — FORM-06/07, DUB-06/07/08, IMG-07/08, TRANS-08/09/10/11. Remain deferred to v16+ per REQUIREMENTS.md.
- **Code changes to close tech_debt** — v15.0 is audit + documentation only. If tech_debt closure needs code changes, that's v16+ scope.
- **Live operator UAT for Phase 78 TRANS-07** — Phase 78 verification deferred 3 human items (live ComfyUI run + verdict recording + identity drift assessment). These remain pending until operator runs them. Documented in audit doc §7.
- **Cross-repo ancestry assertion** — v14.0 P76 ran `git merge-base --is-ancestor` to verify v14.0 commits are descendants of P70 baselines. v15.0 can do the same for v15.0 commits vs v14.0 pins. Optional (v16+ scope if needed).

</deferred>
