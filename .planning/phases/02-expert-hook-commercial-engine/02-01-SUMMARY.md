---
phase: 02-expert-hook-commercial-engine
plan: 01
subsystem: hook_retention
tags: [hook-design, short-drama, pacing, commercial-engine, reference-foundation]
requires:
  - "Phase 0 _shared/{glossary.md, SKILL-LAYOUT.md}"
  - "Phase 1 compliance_marketing/references/viral-element-catalog.md"
provides:
  - "three-second-hooks.md — 5-type hook taxonomy × 3 examples × frame-by-frame + 5-tier scoring"
  - "conflict-escalation.md — 阶梯式升级 ladder + 击中点/爽点 density (canonical source of truth)"
  - "LICENSE.md — Fair Use attribution for hook_retention reference corpus"
affects:
  - "02-02 (paywall-design.md, vertical-pacing.md) — must cross-link conflict-escalation.md numbers, not redefine"
  - "02-03 (SKILL.md body) — cites §情感钩, §悬念钩 etc. from three-second-hooks.md; ladder rungs map to marker schema"
  - "screenplay.emotion_curve — downstream consumer of 钩子/击中点/爽点/卡点 markers defined via ladder"
tech-stack:
  added: []
  patterns:
    - "5-type hook taxonomy with cross-reference table to Phase 1 viral-element-catalog.md (3 overlap + 2 HOOK-only)"
    - "3-second frame-by-frame structure (0-1s attention-grab / 1-2s context-establish / 2-3s hook-pin)"
    - "5-tier strength scoring rubric (🎯/✅/⚠️/❌/💀) as subjective proxy metric"
    - "5-rung escalation ladder with canonical numeric thresholds (10-15s/30-45s/6-9/70-80%/30s)"
    - "Single source of truth rule: conflict-escalation.md owns rhythm numbers; 02-02/02-03 cross-link"
key-files:
  created:
    - skills/movie-experts/hook_retention/references/three-second-hooks.md
    - skills/movie-experts/hook_retention/references/conflict-escalation.md
    - skills/movie-experts/hook_retention/references/LICENSE.md
  modified: []
decisions:
  - "Marked all 完播率 hold ranges as *estimated* per T-02-01 mitigation (Refresh Cadence + Drift Signals document quarterly re-verification)"
  - "LICENSE.md owned exclusively by 02-01 for parallel safety; 02-02 references but does NOT modify"
  - "Declared conflict-escalation.md as canonical source of truth for rhythm thresholds (10-15s/30-45s/6-9/70-80%/30s) per T-02-03 mitigation"
  - "Cross-referenced HOOK taxonomy to Phase 1 viral-element-catalog.md (3 identical + 2 HOOK-only: 悬念钩/情绪爆点钩) per T-02-04 mitigation"
metrics:
  duration: "~7 min"
  completed: 2026-06-15
  tasks_completed: 2
  tasks_total: 2
  files_created: 3
  files_modified: 0
  total_lines: 579
---

# Phase 02 Plan 01: Hook Retention Reference Foundation Summary

5-type 3-second hook taxonomy with frame-by-frame breakdown (15 examples across romance/revenge/family/mystery/comedy) + 阶梯式 escalation ladder defining 击中点/爽点 placement density as the canonical source of truth for downstream 02-02/02-03.

## What Was Built

### Task 1: three-second-hooks.md (296 lines) + LICENSE.md (51 lines)

Authored the 3-second hook design vocabulary for the hook_retention expert:

- **5-type taxonomy:** 情感钩 / 悬念钩 / 冲突钩 / 反差钩 / 情绪爆点钩 with male/female channel typical applications and explicit mapping to Phase 1 COMPLI catalog (3 overlap + 2 HOOK-only).
- **3-second frame structure:** Three H3 subsections (0-1s Attention-Grab / 1-2s Context-Establish / 2-3s Hook-Pin) with concrete pattern options and explicit anti-patterns.
- **15 frame-by-frame examples** distributed across romance/revenge/family/mystery/comedy (each genre ≥ 2 occurrences; within each type, no genre repeats across all 3 examples). Every example has 0-1s/1-2s/2-3s concrete scene details + estimated 完播率 impact.
- **5-tier strength scoring rubric:** 🎯 bullseye (≥85% hold) / ✅ strong (60-85%) / ⚠️ weak (30-60%) / ❌ broken (<30%) / 💀 anti-hook. Documented as subjective proxy metric per Phase 1 precedent, with structured self-check checklist for upgrading ⚠️ → ✅.
- **Cross-reference table** mapping HOOK 5-type ↔ COMPLI 5-type, explicitly noting HOOK does NOT replicate 🟢/🟡/🔴 risk badges (risk assessment must cross-link to viral-element-catalog.md).
- **LICENSE.md** declaring Fair Use — aggregated industry observation; no copyrighted script/scene/dialogue reproduced. Covers all 4 HOOK reference files (3 authored here + 2 in 02-02 parallel).

### Task 2: conflict-escalation.md (232 lines)

Authored the 阶梯式 escalation model and 击中点/爽点 density rules:

- **5-rung escalation ladder:** 钩子锚定 (0-3s, 6/10) → first 击中点 (10-15s, 7/10) → mid-escalation (30-45s, 8/10) → 爽点峰值 (70-80%, 9-10/10) → 卡点 cliffhanger (episode end, unresolved). Each rung maps to a marker type in the eventual SKILL.md schema.
- **击中点 density rules (canonical):** soft peak every 10-15s, hard peak every 30-45s, total 6-9 击中点 per 90s episode. Includes attention decay curve rationale and density boundaries (over/under).
- **爽点 placement strategy (canonical):** 70-80% of runtime, ≥30s setup callback, 9-10/10 intensity. Includes 3 concrete genre examples (romance/revenge/comedy) with full ladder walkthroughs.
- **爽点 strength tiers:** Reuses 5-tier symbols from three-second-hooks.md but with payoff semantics (🎯 cathartic / ✅ satisfying / ⚠️ muted / ❌ absent).
- **5 conflict archetypes:** 内心/人际/阶级/道德/命运 conflicts mapped to payoff types.
- **Multi-episode escalation:** Episode N's 卡点 → Episode N+1's 钩子锚定 continuation patterns; season-long arc curve (low → mid → high → finale peak); serialized hard+soft 卡点 combination strategy.
- **Declared canonical source of truth** for all rhythm numeric thresholds (T-02-03 mitigation) — 02-02 and 02-03 must cross-link rather than redefine.

## Deviations from Plan

None — plan executed exactly as written. Both task scanners passed on the first run; no Rule 1-3 auto-fixes triggered.

## Authentication Gates

None — pure markdown authoring task with no API/credential dependencies.

## Compliance Notes

- **Copyright compliance:** All 15 examples describe genre-trope patterns (e.g., "替身的爱", "霸总装穷"), not reproductions of any specific copyrighted work's actual frames or dialogue. LICENSE.md explicitly marks the corpus as Fair Use aggregated observation.
- **Risk badge non-duplication:** Per plan requirement, three-second-hooks.md does NOT replicate 🟢/🟡/🔴 risk badges from Phase 1 viral-element-catalog.md. Downstream agents must cross-link for risk assessment.
- **Estimated numbers:** All 完播率 ranges, density thresholds, and intensity scores marked `*estimated*` per T-02-01 mitigation.

## Known Stubs

None — no stubs in this plan. All sections contain concrete content; no `TODO`/`FIXME`/placeholder values flowing to UI rendering.

## Threat Flags

None — no new security-relevant surface introduced beyond what the plan's `<threat_model>` already covers. All 5 threats (T-02-01 through T-02-05 + T-02-SC) mitigated as specified.

## Cross-Plan Contracts Established

This plan establishes these contracts that 02-02 and 02-03 MUST honor:

| Contract | Owner | Consumers | Rule |
|----------|-------|-----------|------|
| Rhythm numeric thresholds (10-15s / 30-45s / 6-9 / 70-80% / 30s) | `conflict-escalation.md` | 02-02 paywall-design.md, 02-03 SKILL.md | Cross-link, never redefine (T-02-03 mitigation) |
| LICENSE.md ownership | 02-01 (this plan) | 02-02 | Reference only; do NOT modify |
| 5-type hook taxonomy | `three-second-hooks.md` | 02-03 SKILL.md body, downstream screenplay expert | Cite §情感钩 etc. by section anchor |
| HOOK ↔ COMPLI taxonomy mapping | `three-second-hooks.md` §Cross-Reference | 02-03 SKILL.md, compliance_marketing | 3 overlap (情感/冲突/反差) + 2 HOOK-only (悬念/情绪爆点) |

## Self-Check: PASSED

**Files verified:**
- FOUND: skills/movie-experts/hook_retention/references/three-second-hooks.md (296 lines)
- FOUND: skills/movie-experts/hook_retention/references/conflict-escalation.md (232 lines)
- FOUND: skills/movie-experts/hook_retention/references/LICENSE.md (51 lines)

**Commits verified:**
- FOUND: 9c4900ee9 — docs(02-01): author three-second-hooks.md + LICENSE.md
- FOUND: 8fda657eb — docs(02-01): author conflict-escalation.md

**Scanner verification:**
- Task 1 scanner: PASS (296 lines ≥ 280; all 5 H3 type sections; exactly 15 frame-by-frame blocks; all 5 tier symbols; cross-links to viral-element-catalog.md + glossary.md)
- Task 2 scanner: PASS (232 lines ≥ 220; all required H2 sections; density numbers 10-15s and 70-80% present; cross-links to three-second-hooks.md + paywall-design.md + vertical-pacing.md)
