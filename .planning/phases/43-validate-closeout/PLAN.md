---
phase: 43-validate-closeout
milestone: v9.0
granularity: standard
model_profile: quality
parallel: false
depends_on: [38-slice-platform-master, 39-form-formula-library, 40-gate-redlines, 41-preview-ltx2-step6_5, 42-data-convergence]
plans:
  - 43-01
plans_total: 1
status: planned
planned: 2026-06-27
---

# Phase 43: VALIDATE — 集成验证 + close-out

**Goal:** 全 milestone integration-checker (3 cross-phase flows) + FOUND-08 byte-diff audit milestone-wide + canonical `v9.0-MILESTONE-AUDIT.md` (10 sections) as the milestone's permanent close-out record.

This is the FINAL phase of v9.0 (and the FINAL phase of the formal milestone plan). It must run strictly LAST — all 5 prior phases (38 SLICE / 39 FORM / 40 GATE / 41 PREVIEW / 42 DATA) shipped before Phase 43 starts.

## Requirements (3)

- **VALIDATE-01**: Cross-5-phase integration-checker all-pass (SLICE `variants[]` → DATA adapter consumes; FORM `formula_lookup` → GATE `suggested_action` references formula_id; PREVIEW `preview_fail_exhausted` fallback to Step 6 preserves V8.6 13-step I/O contract)
- **VALIDATE-02**: FOUND-08 preserved milestone-wide — byte-diff of all movie-experts SKILL.md frontmatter + kais-movie-pipeline frontmatter against start commit `a2a20d2be` shows zero changes
- **VALIDATE-03**: Canonical `.planning/milestones/v9.0-MILESTONE-AUDIT.md` ships with 10 sections (header / phase outcomes / 22 req coverage / integration matrix / FOUND-08 evidence / test summary / operator-action-handoffs / V9-FUTURE candidates / v7.0 comparison / tag-prepared note)

## Plans

- [ ] **43-01-PLAN.md** — Integration-checker + FOUND-08 byte-diff + v9.0-MILESTONE-AUDIT.md (4 tasks: integration-checker + byte-diff audit + audit authoring + state/roadmap/requirements close-out) — covers all 3 VALIDATE reqs

## Success Criteria

1. SLICE→DATA integration verified: `variants[]` schema in `references/asset-bus-schema.md` matches what Phase 42 DATA PlatformMetrics consumes (variant_id FK target).
2. FORM→GATE integration verified: each Phase 40 redline gate's `suggested_action` matches `^formula:[a-z][a-z0-9-]*$` and references a Phase 39 read-side lookup key (already verified by Plan 40-01).
3. PREVIEW→Step 6 integration verified: Step 6.5 fallback policy references existing BLOCKING-mode Gate; V8.6 `step_count: 13` + `gate_count: 8` unchanged in SKILL.md frontmatter (verified by FOUND-08 byte-diff).
4. FOUND-08 byte-diff: all movie-experts + kais-movie-pipeline frontmatter sha256 matches pre-v9.0 `a2a20d2be`.
5. `v9.0-MILESTONE-AUDIT.md` ships with 10 sections; 301+ tests GREEN as final evidence; operator-action-handoffs documented (V9-FUTURE-01 + V9-FUTURE-02).

## Out of Scope

- **DO NOT touch Phase 38-42 source code** (read-only at this point)
- **DO NOT run `git tag v9.0`** — operator action after audit review
- **DO NOT run `/gsd:complete-milestone v9.0`** — operator action; this phase only prepares the audit
- **DO NOT modify `agent/*` / `hermes_cli/*`** (Hermes core)
- **DO NOT modify FOUND-08 protected files** (already enforced milestone-wide)

## Comparison Anchor

Mirrors v5.0 Phase 27 / v6.0 Phase 33 / v7.0 Phase 37 close-out pattern. v7.0 used a MIGRATION-REPORT (different scope type); v9.0 returns to the MILESTONE-AUDIT format (like v5.0 + v6.0).
