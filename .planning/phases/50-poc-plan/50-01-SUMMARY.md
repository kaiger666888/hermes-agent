---
phase: 50-poc-plan
plan: 01
subsystem: design-doc
tags: [v10.0, poc-plan, capstone, risk-register, acceptance-criteria, vertical-slice, fitness-battery, bias-canary, schema-migration]
requires:
  - 00-FIRST-PRINCIPLES.md (Phase 44 — 7 决策 root)
  - 01-AGENT-REGISTRY-SCHEMA.md (Phase 45 — agents-schema.yaml + memory-record-schema.yaml)
  - 02-ROUND-TABLE-PROTOCOL.md (Phase 46 — round-table-state-schema.yaml + conflict arbitration)
  - 04-MIGRATION-PATH.md (Phase 49 — §4 memory migration + §5 retained-phases)
  - PITFALLS.md (§Risk Register Summary line 470-488 + §P1/§P2/§P4/§P5/§P6/§P7/§P8 + §P14)
  - STACK.md (§3.2 7 MCP tool + §7 ~550K tokens/pipeline run)
  - SUMMARY.md (§Risk Register line 145-160 + §Gaps to Address line 172-178)
provides:
  - "v10.0 design doc #05 — capstone PoC plan: vertical slice selection + 7-item acceptance criteria + 7-row risk register + PoC implementation path"
  - "v11.0 PoC implementer blueprint (single deliverable, ~1420 lines bilingual)"
affects:
  - Phase 51 VALIDATE (lint risk register alignment + 7 决策 audit + acceptance criteria coverage)
  - v11.0 PoC milestone (next milestone consumes this as direct blueprint)
tech-stack:
  added: []
  patterns:
    - "capstone aggregation (cite-only Phase 44/45/46/49 + PITFALLS + STACK + SUMMARY, no re-derivation)"
    - "5-dimension vertical slice selection scorecard (round-table density / schema coverage / decision coverage / synthetic-input / isolation)"
    - "first-principles task decomposition for 1-3 day estimates per acceptance criterion"
    - "hard-precondition sequencing rationale (fitness battery before schema migration before bias canary)"
    - "PoC verdict aligned with 2 canonical sources (PITFALLS §Risk Register Summary + SUMMARY §Risk Register)"
key-files:
  created:
    - .planning/research/v10-orchestrator-design/05-POC-PLAN.md (1420 lines)
  modified: []
decisions:
  - "PoC scope = vertical slice (1 creative = screenplay Step 3 + 1 infra = agent registry + 1 round table), NOT full pipeline run (budget + isolation rationale)"
  - "7 acceptance criteria = 12 person-days total (fitness battery 3d / latency SLO 2d / bias canary 2d / compaction 1d / threshold tuning 1d / dry-run-first 1d / schema migration dry-run 2d)"
  - "7-row risk register verdicts: 6 must-fix (P1/P2/P4/P5/P7/P8) + 1 PARTIAL (P6 signed feedback must, outlier defer with monitoring)"
  - "PoC implementation path sequence: fitness battery FIRST → schema migration dry-run SECOND → bias canary THIRD (硬 precondition chain)"
  - "PoC budget: ~15-17 person-days + 30-day shadow-run = ~6 calendar weeks"
  - "Per-vertical-slice token cost: ~148K creative screenplay Step 3 (9-agent dense) / ~10K infra (1 round table) — within GLM 4-key 800K TPM ceiling for serial"
metrics:
  duration: ~22 minutes (5 tasks × ~4 min/task)
  completed: 2026-07-07
  tasks: 5
  files: 1
  lines: 1420
---

# Phase 50 Plan 01: PoC Plan Capstone Summary

**One-liner**: v10.0 设计套件收口 capstone — aggregate 前 6 份 design docs 的 pitfall 缓解成 v11.0 PoC 实施蓝本: vertical slice (screenplay Step 3 + agent registry + 1 round table) + 7-item acceptance criteria (12 person-days) + 7-row risk register (6 must-fix + P6 PARTIAL) + fitness battery → schema migration → bias canary 实施路径 (~550K/pipeline-run token cost scoping).

## What Was Built

Single deliverable: `.planning/research/v10-orchestrator-design/05-POC-PLAN.md` (1420 lines, bilingual EN structure + 中文 prose per CLAUDE.md).

### Document Structure

| § | Topic | Lines | SC# |
|---|-------|-------|-----|
| §0 | 阅读指南 (chapter map + 3-audience + stability markers + cite-only consumption table) | 73 | — |
| §1 | Framing + 4 deliverables declared upfront + capstone-at-a-glance + out-of-scope | 175 | SC#1 |
| §2 | PoC scope boundary (done 定义 + 5 exclusions + ~/.hermes-poc workspace + budget) | 110 | SC#1 |
| §3 | Vertical slice selection (creative screenplay Step 3 + infra agent registry + 1 round table, 5-dim scorecard) | 235 | SC#2 |
| §4 | 7-item acceptance criteria (12 person-days, per-criterion task decomposition) | 265 | SC#3 |
| §5 | 7-row risk register (P1/P2/P4/P5/P6/P7/P8 × verdict, aligned with PITFALLS + SUMMARY) | 220 | SC#4 |
| §6 | PoC implementation path (fitness battery → schema migration → bias canary + 6-week calendar) | 165 | SC#5 |
| §7 | Phase 44 7 决策 cross-validation audit + OQ/Pitfall resolution | 110 | — |
| §8 | Downstream citation guide + coherence + References | 70 | — |

### 4 Lockable Artifacts

1. **Vertical slice selection** (§3): creative = screenplay Step 3 round table (9 related_agents densest, HOOK-09 emotion_curve edge case); infra = agent registry + 1 round table invocation (7 MCP tool wire-up). Both with 决策号 citation + 5-dim scorecard + edge case.
2. **7-item acceptance criteria** (§4, 12 person-days total): fitness battery 3d (P1+P8) / latency SLO p95<500ms 2d (P3) / bias canary 2d (P5) / compaction 1d (P9) / threshold tuning 1d (P13) / dry-run-first 1d (P5) / schema migration dry-run 2d (P14).
3. **7-row risk register** (§5): 6 must-fix (P1/P2/P4/P5/P7/P8) + 1 PARTIAL (P6 signed feedback must, outlier defer). Verdicts aligned with PITFALLS §Risk Register Summary line 470-488 + SUMMARY §Risk Register line 145-160 (no divergent verdicts).
4. **PoC implementation path** (§6): fitness battery FIRST (regression-detection foundation) → schema migration dry-run SECOND (memory layer integrity) → bias canary THIRD (curator `_memory_evolution_phase` live-mode gate). 6-week calendar timeline. Per-vertical-slice token cost ~148K creative / ~10K infra.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Critical functionality] Added SC cross-validation subsections (§2.5, §3.7, §3.8, §4.10)**
- **Found during**: Tasks 2-3
- **Issue**: Plan's `done` criteria required SC#1-5 mapping but verification scripts only checked term presence. Without explicit SC cross-validation tables, the doc would be hard for Phase 51 VALIDATE to audit.
- **Fix**: Added §2.5 (SC#1 PASS), §3.7+§3.8 (SC#2 PASS), §4.10 (run order aligned with SC#5 impl path), with explicit PASS declarations.
- **Files modified**: `.planning/research/v10-orchestrator-design/05-POC-PLAN.md`
- **Commit**: ee6256b2c, c0d942033

**2. [Rule 1 - Bug] Mitigation cost alignment table added (§4.8)**
- **Found during**: Task 3
- **Issue**: PITFALLS §Risk Register Summary line 470-488 has explicit mitigation cost column (H/M/L) but initial §4.8 summary didn't cross-check PoC implementation cost vs PITFALLS mitigation cost.
- **Fix**: Added mitigation cost alignment table to §4.8 showing PoC implementation cost matches PITFALLS mitigation cost estimate (e.g. P1: PITFALLS=M, PoC=3d → aligned).
- **Files modified**: `.planning/research/v10-orchestrator-design/05-POC-PLAN.md`
- **Commit**: c0d942033

None of the deviations changed the plan's intent — all are elaborations that strengthen Phase 51 VALIDATE auditability.

## Self-Check: PASSED

### Created files exist

- ✅ `.planning/research/v10-orchestrator-design/05-POC-PLAN.md` (1420 lines, target ~1300+)

### Commits exist

- ✅ `58bf37bc7` (Task 1 — §0 + §1)
- ✅ `ee6256b2c` (Task 2 — §2 + §3)
- ✅ `c0d942033` (Task 3 — §4)
- ✅ `7d346e5a4` (Task 4 — §5)
- ✅ `1bcfab404` (Task 5 — §6 + §7 + §8)

### Verification scripts (from plan `<verify>` blocks)

- Task 1: ≥250 lines + all 38 required terms + ≥8 PITFALLS §PX citations → PASS
- Task 2: ≥600 cumulative lines + 4 §2 subsections + 6 §3 subsections + all 32 required terms → PASS
- Task 3: ≥950 cumulative lines + 8 §4 subsections + all 38 required terms + ≥7 day estimates → PASS
- Task 4: ≥1100 cumulative lines + 10 §5 subsections + all 30 required terms + ≥7 P# in §5.8 + ≥7 must-fix|PARTIAL in §5.8 → PASS
- Task 5: ≥1300 cumulative lines + 6 §6 subsections + 3 §7 subsections + 2 §8 subsections + all 47 required terms + 7 决策 in §7.1 + 7 ✅ in §7.1 → PASS

## Risk Register Verdict Alignment (no divergent verdicts)

| P# | 本 doc (§5) | PITFALLS §Risk Register Summary line 470-488 | SUMMARY §Risk Register line 145-160 | Aligned? |
|----|-------------|-----------------------------------------------|--------------------------------------|----------|
| P1 | must-fix | NO (load-bearing) | NO (load-bearing) | ✅ |
| P2 | must-fix | NO (load-bearing) | NO (load-bearing) | ✅ |
| P4 | must-fix | NO (load-bearing) | NO (load-bearing) | ✅ |
| P5 | must-fix | NO (load-bearing) | NO (load-bearing) | ✅ |
| P6 | PARTIAL (signed must, outlier defer) | PARTIAL (signed feedback is PoC must; outlier detection can defer) | PARTIAL | ✅ |
| P7 | must-fix | NO (round-table is v10.0 core) | NO (round-table is v10.0 core) | ✅ |
| P8 | must-fix | NO (load-bearing) | NO (load-bearing) | ✅ |

Phase 51 VALIDATE lint 脚本可 cross-check §5.9 对齐 declaration.

## TDD Gate Compliance

N/A — this is a `type: execute` plan (design doc deliverable, no code/tests). RED/GREEN/REFACTOR gate not applicable.

## Known Stubs

None. The deliverable is a complete design doc; no placeholders, no TODOs, no "coming soon" stubs.

## Threat Flags

None. The deliverable is design-only markdown; no new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries. (T-50-01 through T-50-06 threat register items are documentation-level concerns, all mitigated in the doc itself per the plan's `<threat_model>` dispositions.)

## Next Consumers

1. **v11.0 PoC implementer** — direct blueprint consumer (cite §3 vertical slice + §4 acceptance + §5 risk register + §6 impl path, no re-derivation)
2. **Phase 51 VALIDATE** — cross-doc lint (§5.8 risk register summary + §7.1 7 决策 audit + §4.8 acceptance summary + §7.3 OQ/pitfall resolution)
3. **Operator (Kai)** — review PoC scope feasibility (~15-17 person-days + 6 weeks) + defer-with-monitoring verdicts acceptability

## Commit History (this plan)

```
1bcfab404 docs(50-01): task 5 — write §6 impl path + §7 决策 audit + §8 downstream
7d346e5a4 docs(50-01): task 4 — write §5 7-row risk register (SC#4 deep-dive)
c0d942033 docs(50-01): task 3 — write §4 7-item acceptance criteria (12 person-days)
ee6256b2c docs(50-01): task 2 — write §2 PoC scope + §3 vertical slice selection
58bf37bc7 docs(50-01): task 1 — write §0 reading guide + §1 framing for 05-POC-PLAN
```
