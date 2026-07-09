---
phase: 75-lineage-bump
verified: 2026-07-10T02:30:00Z
status: human_needed
score: 6/6 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: N/A
  gaps_closed: []
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Track B persona byte-identity on 6 manual experts (visual_executor, colorist, compliance_gate, creative_source, prompt_injector, script_auditor)"
    expected: "Only lineage.skill_sha256 / lineage.transform_date / lineage.transform_notes changed; persona body byte-identical to pre-bump v13.0 P62 state"
    why_human: "agent.yaml files at ~/.hermes/agents/ are NOT in hermes-agent git repo — no git diff baseline available. Pre-bump snapshot was not captured programmatically (P70 inventory covered only 3 of 15). VALIDATION.md Manual-Only table explicitly flagged this as manual byte-level diff verification. Structural proxies (Rule IDs prose present, persona field substantive) pass but cannot prove byte-identity."
---

# Phase 75: LINEAGE-BUMP Verification Report

**Phase Goal:** After all v14.0 SKILL.md edits are final, the 15 affected agent YAMLs at `~/.hermes/agents/` have their lineage fields regenerated (source_sha + transform_rule_id + transform_timestamp) by re-running the v13.0 P62 transform flow, with CI assertion `agent.yaml.source_sha == sha256(SKILL.md)` passing.
**Verified:** 2026-07-10T02:30:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | All 15 active movie-expert agent.yaml files have lineage.skill_sha256 matching sha256(LF-normalized UTF-8 SKILL.md) of the final v14.0 SKILL.md source | ✓ VERIFIED | `bash .planning/phases/75-lineage-bump/75-lineage-assert.sh` → "15/15 PASSED, 0 FAILED", exit 0. Each expert prints MATCH with skill and agent hash prefixes agreeing (e.g. cinematographer skill=523f260e0315 / agent=523f260e0315). |
| 2 | All 15 active movie-expert agent.yaml files have lineage.transform_date = 2026-07-10 (post-v14.0 bump, not stale 2026-07-07/08) | ✓ VERIFIED | Per-file grep of `transform_date:` field across all 15 agent.yaml files; every file shows `transform_date: '2026-07-10'`. |
| 3 | All 15 active movie-expert agent.yaml files have lineage.transform_notes citing 'v14.0 P75 lineage bump' | ✓ VERIFIED | Per-file grep for "P75" inside the lineage block (awk-scoped between `^lineage:` and next top-level key): 15/15 show `P75_in_lineage=YES`. The citation appears in multi-line folded YAML scalar bodies (e.g. cinematographer: "...anchors. Analysis-only tools... | v14.0 P75 lineage bump (post Phases 71-74 SKILL.md edits)"; visual_executor: "...Transform timestamp: 2026-07-08T00:00:00Z. \| v14.0 P75 lineage bump (post Phases 71-74 SKILL.md edits)"). Initial single-line `^transform_notes:` grep returned NO because the citation lives in the scalar continuation, not the header line — robust block-scoped grep confirms. |
| 4 | CI assertion 75-lineage-assert.sh exits 0 (all 15 lineage.skill_sha256 == sha256(SKILL.md)) | ✓ VERIFIED | Direct execution: `bash /data/workspace/hermes-agent/.planning/phases/75-lineage-bump/75-lineage-assert.sh` printed "Phase 75 lineage assertion: 15/15 PASSED, 0 FAILED" and exited 0. Script is 101 lines, executable, uses `set -euo pipefail`, file-existence-FIRST checks, and per-expert sha256 comparison via Python `_compute_skill_sha256` algorithm (LF-normalized UTF-8 per transform_skill_to_agent.py:232-240). |
| 5 | Curator freeze is lifted (curator.enabled: true in config.yaml) — final action of phase, AFTER all 15 bumps + assertion passes | ✓ VERIFIED | `grep -A2 "^curator:" ~/.hermes/config.yaml` returns: `curator:` / `  enabled: true        # Released post-Phase-75 lineage bump (XCUT-03 complete)` / `  interval_hours: 168`. PLAN's check pattern `grep -A1 "^curator:" ~/.hermes/config.yaml \| grep -q "enabled: true"` returns FREEZE RELEASED. NOTE: VALIDATION.md task 75-01-04's literal command `grep -c "curator.enabled: true"` returns 0 because YAML uses nested-key format not flat dotted-key — but the underlying truth (curator.enabled flag = true) is satisfied; this is a VALIDATION.md test-spec imprecision, not a phase-goal gap. |
| 6 | 75-LINEAGE-BUMP-REPORT.md exists with pre-bump baseline + post-bump final hashes + delta decomposition for Phase 76 VALIDATE audit | ✓ VERIFIED | File exists: 136 lines (>= 50 required). Contains: cross-repo pins at bump time (hermes-agent `ebd4c0e45cfc` + kais-hermes-skills `ba58c2548ab8`), pre-bump baseline table (3 P70-scope agents), post-bump final hashes table (15 rows), delta decomposition for cinematographer + audio_pipeline + editor with pre-v14.0 vs v14.0-introduced portions split per P70 Pitfall 3, Phase 76 lineage coverage row, skipped agents documentation. |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `~/.hermes/agents/cinematographer.agent.yaml` | Regenerated lineage (skill_sha256 + transform_date + transform_notes); persona body UNCHANGED | ✓ VERIFIED (lineage) / ⚠ HUMAN-NEEDED (persona body byte-identity) | Lineage block contains: derived_from_skill_id, derived_from_repo, transform_date '2026-07-10', transform_notes (multi-line folded scalar citing P75), skill_sha256 523f260e0315... matching assertion. Track A — persona regenerated via script. |
| `.planning/phases/75-lineage-bump/75-lineage-assert.sh` | CI assertion script: 15 active experts sha256 equality check | ✓ VERIFIED | 101 lines (>= 40 required), executable (-rwxrwxr-x), exits 0 with 15/15 PASSED. Uses set -euo pipefail, file-existence-FIRST, per-expert MATCH/FAIL output with truncated hash prefixes for debuggability. |
| `.planning/phases/75-lineage-bump/75-LINEAGE-BUMP-REPORT.md` | Phase 76 VALIDATE audit input: lineage coverage table + delta decomposition | ✓ VERIFIED | 136 lines (>= 50 required). Contains cross-repo pins, pre-bump baseline (3 rows), post-bump final hashes (15 rows), delta decomposition (3 agents with v14.0-vs-pre-v14.0 split), Phase 76 lineage coverage row, skipped agents documentation. |
| `~/.hermes/config.yaml` | Curator freeze released (curator.enabled: true) | ✓ VERIFIED | `curator:` block has `enabled: true` with citation "Released post-Phase-75 lineage bump (XCUT-03 complete)". |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `.planning/phases/75-lineage-bump/75-lineage-assert.sh` | `~/.hermes/agents/*.agent.yaml + /data/workspace/kais-hermes-skills/skills/movie-experts/*/SKILL.md` | bash sha256sum + grep lineage.skill_sha256 | ✓ WIRED | Script iterates 15-expert EXPERTS array; for each: (1) asserts SKILL.md exists at `$KIAS_SKILLS_ROOT/$expert/SKILL.md`, (2) asserts agent.yaml exists at `$AGENTS_DIR/$expert.agent.yaml`, (3) computes skill_sha via Python sha256 of LF-normalized UTF-8 bytes, (4) reads agent_sha via grep+sed on `skill_sha256:` field, (5) asserts equality. All 15 MATCH. |
| `~/.hermes/agents/cinematographer.agent.yaml` | `scripts/transform_skill_to_agent.py:232-240 algorithm` | lineage.skill_sha256 field regenerated by transform script (EXPERTS_9 subset) | ✓ WIRED | Track A — cinematographer is in EXPERTS_9; agent.yaml lineage.skill_sha256 = 523f260e0315... matches sha256 of current SKILL.md working-tree bytes. Assertion confirms algorithm fidelity. |

### Data-Flow Trace (Level 4)

Not applicable — Phase 75 is a mechanical transform phase (YAML field regeneration + bash assertion). No dynamic data rendering, no DB queries, no UI components. The "data flow" is SKILL.md bytes → sha256 algorithm → lineage.skill_sha256 YAML field → assertion script comparison, which the 15/15 PASSED result validates end-to-end.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Lineage assertion passes for all 15 experts | `bash .planning/phases/75-lineage-bump/75-lineage-assert.sh` | exit 0; "15/15 PASSED, 0 FAILED" with per-expert MATCH lines | ✓ PASS |
| All 15 transform_date values are 2026-07-10 | per-file grep `transform_date:` across 15 agent.yaml | 15/15 show `transform_date: '2026-07-10'` | ✓ PASS |
| All 15 lineage blocks cite P75 | awk-scoped grep for `P75\|v14.0 P75` in lineage block | 15/15 show `P75_in_lineage=YES` | ✓ PASS |
| Curator freeze released | `grep -A1 "^curator:" ~/.hermes/config.yaml \| grep -q "enabled: true"` | FREEZE RELEASED | ✓ PASS |
| No agent.yaml created for skipped experts | `ls ~/.hermes/agents/ \| grep -iE "drawer\|kais-movie-pipeline\|kais-jimeng-cli"` | (empty output) | ✓ PASS |
| Bump report documents 2 skill-only + drawer DEPRECATED | grep skipped-expert names in 75-LINEAGE-BUMP-REPORT.md | 5 matches across scope summary + skipped agents table | ✓ PASS |
| Track B Rule IDs prose preserved (structural proxy for persona preservation) | per-file grep `Rule IDs:` on 6 Track B agent.yaml | 6/6 show Rule IDs prose PRESENT | ✓ PASS (structural only — byte-identity needs human) |

### Probe Execution

| Probe | Command | Result | Status |
|-------|---------|--------|--------|
| `scripts/.../probe-*.sh` | N/A — no probe scripts in this phase | N/A | SKIP |
| Phase-specific assertion | `bash .planning/phases/75-lineage-bump/75-lineage-assert.sh` | exit 0, 15/15 PASSED | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| XCUT-03 | 75-01-PLAN.md | Lineage bump via v13.0 P62 transform flow — 15/15 agent.yaml regenerated, assertion passes, 2 skill-only + drawer DEPRECATED documented | ✓ SATISFIED | (1) 75-lineage-assert.sh exits 0 with 15/15 PASSED; (2) All 15 lineage.transform_date = 2026-07-10; (3) All 15 transform_notes cite P75; (4) 75-LINEAGE-BUMP-REPORT.md documents 2 skill-only (kais-movie-pipeline + kais-jimeng-cli) + drawer DEPRECATED; (5) Curator freeze released as final action. REQUIREMENTS.md `[x] XCUT-03` checkbox is checked and marks the requirement SHIPPED 2026-07-10. |

**Orphaned requirements:** NONE. REQUIREMENTS.md Phase 75 → XCUT-03 only; PLAN declares `requirements: [XCUT-03]`; XCUT-02 + XCUT-04 are explicitly assigned to Phase 76.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `.planning/phases/75-lineage-bump/75-lineage-assert.sh` | — | (none) | — | No TBD/FIXME/XXX/PLACEHOLDER/stub patterns found. |
| `.planning/phases/75-lineage-bump/75-LINEAGE-BUMP-REPORT.md` | — | (none) | — | No blocker markers. |
| `~/.hermes/config.yaml` | — | (none) | — | Curator flag cleanly flipped; no surrounding debt. |
| `.planning/phases/75-lineage-bump/75-VALIDATION.md` | 46 | `grep -c "curator.enabled: true"` test command pattern | ℹ️ Info | VALIDATION.md task 75-01-04's literal grep pattern would return 0 because YAML uses nested-key format (`curator:` then indented `enabled: true`), not flat dotted-key. The underlying truth is satisfied (PLAN's check pattern passes). This is a test-spec imprecision in VALIDATION.md, not a phase-goal gap — no remediation needed since the PLAN's check correctly verifies the truth. |

### Human Verification Required

#### 1. Track B persona body byte-identity on 6 v13.0 P62 experts

**Test:** Operator reviews `~/.hermes/agents/{visual_executor,colorist,compliance_gate,creative_source,prompt_injector,script_auditor}.agent.yaml` and confirms only the 3 lineage fields (`skill_sha256`, `transform_date`, `transform_notes`) changed; persona body byte-identical to pre-bump v13.0 P62 state.

**Expected:** Outside the `lineage:` block, no bytes changed. Specifically: `name`, `description`, `version`, `persona`, `tools`, `memory_scope`, `refs`, `tags`, `expert_id`, `metrics`, `prerequisites`, `related_agents`, `evolution_log`, `fitness_score`, `platforms`, `round_table_eligible`, `default_invocation` all unchanged from the 2026-07-08 v13.0 P62 state.

**Why human:** `agent.yaml` files at `~/.hermes/agents/` are NOT inside the hermes-agent git repo — no `git diff` baseline is available. The P70 inventory captured only 3 of 15 agents, so no pre-bump snapshot exists for the 6 Track B experts. VALIDATION.md Manual-Only table explicitly flagged this as manual byte-level diff verification (line 64). Structural proxies pass (Track B Rule IDs prose present in all 6, persona field has substantive content 582-1227 bytes), but cannot prove byte-identity of the full persona body. Only human review against operator's memory of v13.0 P62 output (or a backup if one exists outside the repo) can close this.

### Gaps Summary

**No blocker gaps.** All 6 must-have truths VERIFIED programmatically. XCUT-03 structurally satisfied. Assertion 15/15 PASSED. Curator freeze released. Bump report complete.

**One human-needed item:** Track B persona byte-identity (6 manual experts) — flagged by VALIDATION.md as manual-only from the start; not a regression or missed task. The agent.yaml files live outside the git repo so no automated baseline comparison is possible. Status is `human_needed` per Step 9 decision tree (Step 8 produced a non-empty human verification list — human items take priority over `passed`).

**Note on ROADMAP scope drift:** ROADMAP Phase 75 SC#1-2 originally framed the scope as "6 affected agents". The PLAN + CONTEXT.md explicitly SUPERSEDE this with "15 agent.yaml files" based on `git diff --name-only d9620369..HEAD | grep SKILL.md$` showing 17 SKILL.md files touched in v14.0 (15 active agents + 2 skill-only). The PLAN's `<success_criteria>` section documents this supersession per-SC. This is a legitimate scope correction documented in the user-decisions CONTEXT.md, not a gap. REQUIREMENTS.md reflects the actual 15/15 scope in the XCUT-03 checkbox text.

**Note on VALIDATION.md curator grep:** VALIDATION.md task 75-01-04 uses `grep -c "curator.enabled: true"` which returns 0 against nested YAML format. The PLAN's check (`grep -A1 "^curator:" ... | grep -q "enabled: true"`) correctly verifies the truth. Minor test-spec imprecision; no remediation needed.

---

_Verified: 2026-07-10T02:30:00Z_
_Verifier: Claude (gsd-verifier)_
