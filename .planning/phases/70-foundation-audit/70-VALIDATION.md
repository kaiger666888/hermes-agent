---
phase: 70
slug: foundation-audit
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-09
---

# Phase 70 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Phase 70 is documentation-only (zero code files written). Validation is smoke-test style: file-existence + content-shape assertions on the deliverables.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | N/A — bash + grep + test. No pytest/vitest needed; phase writes zero code. |
| **Config file** | none |
| **Quick run command** | `bash .planning/phases/70-foundation-audit/70-smoke.sh` (to be created by Wave 1) |
| **Full suite command** | Manual operator verification: `cat .planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md && hermes curator status && grep v14.0.freeze .planning/STATE.md` |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** Run the smoke assertions for that task's deliverable (file-existence + row-count grep)
- **After every plan wave:** Run `hermes curator status` (verify freeze active) + inventory completeness check
- **Before `/gsd:verify-work`:** All 6 XCUT-01 sub-rows green + freeze flag still set
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

> Task IDs are placeholders — final IDs assigned by gsd-planner. Requirements map to XCUT-01 sub-rows a–f (from RESEARCH.md `## Validation Architecture > Phase Requirements → Test Map`).

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 70-01-?? | 01 | 1 | XCUT-01a | — | N/A | smoke | `test -f .planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md && echo OK` | ❌ W0 (created by execution) | ⬜ pending |
| 70-01-?? | 01 | 1 | XCUT-01b | — | N/A | smoke | `[ $(grep -c 'skills/.*SKILL.md' .planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md) -ge 6 ]` | ❌ W0 | ⬜ pending |
| 70-01-?? | 01 | 1 | XCUT-01c | — | N/A | smoke | `[ $(grep -cE 'hermes-agent|kais-hermes-skills' .planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md) -ge 2 ]` | ❌ W0 | ⬜ pending |
| 70-02-?? | 02 | 1 | XCUT-01d | T-70-01 (curator freeze bypass) | `curator.enabled=false` blocks even `--live` | smoke | `hermes curator status \| grep -q DISABLED` (or grep config.yaml) | ❌ W0 | ⬜ pending |
| 70-02-?? | 02 | 1 | XCUT-01e | — | Freeze recorded in STATE.md so future sessions restore | smoke | `grep -q 'v14\.0\.freeze' .planning/STATE.md` | ❌ W0 | ⬜ pending |
| 70-03-?? | 03 | 1 | XCUT-01f | — | N/A | smoke | `[ $(grep -c '^|' .planning/phases/70-foundation-audit/70-VALIDATE-CHECKLIST.md) -ge 6 ]` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

This phase has **no Wave 0** in the traditional sense (no framework install, no test stubs). The "Wave 0 gaps" listed below are the deliverables themselves — they are created by execution, not pre-staged:

- [ ] `.planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md` — the primary deliverable (covers XCUT-01a/b/c). Created by Wave 1 task.
- [ ] `.planning/phases/70-foundation-audit/70-VALIDATE-CHECKLIST.md` — Phase 76 audit checklist (covers XCUT-01f). Created by Wave 1 task.
- [ ] `.planning/phases/70-foundation-audit/70-smoke.sh` — the smoke-test runner script. Created by Wave 1 task.
- [ ] `.planning/STATE.md` updated with `v14.0.freeze` block (covers XCUT-01e). Edited by Wave 1 task.
- [ ] `~/.hermes/config.yaml` `curator.enabled: false` (covers XCUT-01d). Edited by Wave 1 task.

*Existing infrastructure (bash + grep + hermes curator CLI) covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Operator confirms inventory rows look right (no pre-existing drift silently swallowed) | XCUT-01 | Researcher found pre-existing lineage drift in cinematographer + audio_pipeline; operator should eyeball the inventory and confirm the drift is captured as `MISMATCH` not `OK` | `cat .planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md` and visually verify the `lineage_match` column shows `MISMATCH` for cinematographer + audio_pipeline |
| Operator confirms `hermes curator status` reports disabled | XCUT-01d | Smoke test greps for DISABLED; operator should confirm the CLI shows expected state to a human | `hermes curator status` and read the output |
| Operator decides whether to address Open Question #2 (pre-existing drift) | XCUT-01 (downstream Phase 75) | Phase 70 captures the drift; Phase 75 closes it. Operator may want to decide now if Phase 75 should auto-fix or pause for review. | Read RESEARCH.md `## Open Questions` and record decision in CONTEXT.md-style note (or skip — Phase 75 will re-surface) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (smoke assertions on file existence + row count)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (every task has a smoke assertion)
- [x] Wave 0 covers all MISSING references (deliverables are listed; no external test framework to install)
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter (set at sign-off time, after planner assigns final task IDs)

**Approval:** pending
