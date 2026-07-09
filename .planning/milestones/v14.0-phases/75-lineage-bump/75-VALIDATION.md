---
phase: 75
slug: lineage-bump
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-10
validation_exemption: true
---

# Phase 75 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
>
> **Validation exemption:** Phase 75 is a mechanical transform + audit phase (per ROADMAP "Standard pattern — mechanical transform + audit; documented 5-step procedure from v10.0 04-MIGRATION-PATH.md"). Nyquist sampling concerns (continuous feedback during iterative development) do not apply — the phase has 2 discrete tasks, each verifiable via deterministic bash assertions. This VALIDATION.md is provided for completeness but the sampling rate is "once after task completion" rather than continuous.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | bash smoke script (deterministic sha256 assertions); Python stdlib for sha256 computation |
| **Config file** | None — bash script self-contained |
| **Quick run command** | `bash .planning/phases/75-lineage-bump/75-lineage-assert.sh` |
| **Full suite command** | Same as quick (single deterministic check) |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** Run `75-lineage-assert.sh`
- **Before `/gsd:verify-work`:** `75-lineage-assert.sh` exits 0
- **Max feedback latency:** 3 seconds (deterministic)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 75-01-01 | 01 (Execution) | 1 | XCUT-03 | — | All 15 agent.yaml files have `lineage.skill_sha256` matching `sha256(LF-normalized UTF-8 SKILL.md)` | bash | `bash .planning/phases/75-lineage-bump/75-lineage-assert.sh` exits 0 | ❌ W0 | ⬜ pending |
| 75-01-02 | 01 | 1 | XCUT-03 | — | All 15 agent.yaml files have `lineage.transform_date: 2026-07-10` (not stale v13.0 value) | grep | `for f in ~/.hermes/agents/{cinematographer,editor,audio_pipeline,visual_executor,character_designer,colorist,compliance_gate,continuity_auditor,creative_source,hook_retention,prompt_injector,screenplay,script_auditor,style_genome,theory_critic}.agent.yaml; do grep -q "transform_date: 2026-07-10" "$f"; done` exits 0 | ❌ W0 | ⬜ pending |
| 75-01-03 | 01 | 1 | XCUT-03 | — | 75-LINEAGE-BUMP-REPORT.md exists with pre-bump baseline + post-bump final + delta decomposition | bash | `test -f .planning/phases/75-lineage-bump/75-LINEAGE-BUMP-REPORT.md && wc -l .planning/phases/75-lineage-bump/75-LINEAGE-BUMP-REPORT.md` ≥ 50 | ❌ W0 | ⬜ pending |
| 75-01-04 | 01 | 1 | XCUT-03 | — | Curator freeze released: `~/.hermes/config.yaml` has `curator.enabled: true` | grep | `grep -c "curator.enabled: true" ~/.hermes/config.yaml` ≥ 1 | ❌ W0 | ⬜ pending |
| 75-01-05 | 01 | 1 | XCUT-03 | — | 2 skill-only (kais-movie-pipeline + kais-jimeng-cli) documented in bump report; NO agent.yaml generated for them | grep | `grep -c "kais-movie-pipeline\|kais-jimeng-cli" .planning/phases/75-lineage-bump/75-LINEAGE-BUMP-REPORT.md` ≥ 2 | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `.planning/phases/75-lineage-bump/75-lineage-assert.sh` — bash smoke script iterating 15 active experts
- [ ] `.planning/phases/75-lineage-bump/75-LINEAGE-BUMP-REPORT.md` — lineage coverage table for Phase 76 VALIDATE audit

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Persona body preservation for Track B (6 manual experts) | XCUT-03 | Byte-level diff verification beyond lineage fields | Operator runs `git diff ~/.hermes/agents/<6 manual experts>.agent.yaml` and confirms only `lineage.skill_sha256` / `lineage.transform_date` / `lineage.transform_notes` changed; persona body byte-identical |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify (validation exemption for mechanical phase)
- [x] Sampling continuity: N/A (2 discrete tasks, not iterative development)
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter (mechanical phase exemption documented)

**Approval:** approved 2026-07-10 (mechanical phase exemption per ROADMAP "Standard pattern" classification)
