---
phase: 82-xcut-04c-cost-tracking-xcut-05-lineage-auto
plan: 03
subsystem: infra
tags: [automation, lineage, agent-registry, yaml, transform, xcut-05]

requires:
  - phase: 52-infra-foundation
    provides: agent/registry_loader.py load_one_agent_yaml validation
  - phase: 53-poc-migr-01
    provides: scripts/transform_skill_to_agent.py (Track A transform_one)
provides:
  - "scripts/bump_all_agent_lineage.py — single-command 15-agent lineage bump (Track A + Track B)"
  - "ACTIVE_EXPERTS_15 hardcoded list (9 Track A + 6 Track B) for operator traceability"
  - "transform_track_b_one pure function for the 6 Track B manual-case experts"
  - "validate_all post-write validation gate for all 15 YAMLs"
affects: [lineage-bump, agent-registry, v15.0-milestone, operator-workflow]

tech-stack:
  added: []
  patterns:
    - "Wrapper pattern: bump_all_agent_lineage wraps transform_skill_to_agent (Track A delegation)"
    - "Mirror pattern: transform_track_b_one mirrors transform_one with Track-B-specific overrides"
    - "Broader-panel filter: TRACK_B_PANEL preserves non-expert agent peers in collaboration graph"

key-files:
  created:
    - scripts/bump_all_agent_lineage.py
    - tests/agent/test_bump_all_agent_lineage.py
  modified: []

key-decisions:
  - "ACTIVE_EXPERTS_15 = Track A (EXPERTS_9) + Track B (6 manual cases), hardcoded per D-03"
  - "Track B tools mapping sourced from existing agent.yaml ground truth (plan interfaces block was stale)"
  - "TRACK_B_PANEL includes non-expert agent peers (compliance_gate, production, prompt_injector, scene_builder) to preserve v13.0 P62 collaboration graph"
  - "transform_track_b_one does NOT apply LEGACY_NAME_MAP canonicalization (preserves scene_builder verbatim — matches existing YAMLs)"

patterns-established:
  - "Wrapper+mirror: new bump script wraps proven base script for Track A and mirrors its structure for Track B"
  - "Ground-truth-driven tools: when plan interfaces conflict with existing YAMLs, existing YAMLs win (Rule 1)"

requirements-completed: [XCUT-05-AUTO]

duration: 6min
completed: 2026-07-10
---

# Phase 82 Plan 03: XCUT-05-AUTO 15-Agent Lineage Bump Script Summary

**Single-command automation of the full 15-expert lineage bump, wrapping transform_skill_to_agent.py for Track A (9) + handling Track B (6) with per-expert persona/tools/notes + validating all 15 YAMLs.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-07-10T13:05:18Z
- **Completed:** 2026-07-10T13:11:23Z
- **Tasks:** 1/1
- **Files modified:** 2 (both new)

## Accomplishments
- Created `scripts/bump_all_agent_lineage.py` — automates the full 15-agent lineage bump in one invocation (`python scripts/bump_all_agent_lineage.py`)
- Track A (9 EXPERTS_9) delegates to the proven `transform_one` from the base script; Track B (6 manual-case experts) uses `transform_track_b_one` with per-expert persona / tools / transform-notes
- All 15 output YAMLs pass `load_one_agent_yaml` schema validation via `validate_all()`
- `main()` exits 0 on full success, 1 on partial (documented operator-review behavior)
- 46 tests (parametrized + end-to-end + structural) — all passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Create bump_all_agent_lineage.py with ACTIVE_EXPERTS_15 + Track A/B handling + validation** — `fc11ae840` (feat)

## Files Created/Modified
- `scripts/bump_all_agent_lineage.py` — The bump automation script. Contains ACTIVE_EXPERTS_15 (9 Track A + 6 Track B), TRACK_B_TOOLS, TRACK_B_TRANSFORM_NOTES, 6 Track B persona builders, transform_track_b_one, bump_track_a, bump_track_b, validate_all, main.
- `tests/agent/test_bump_all_agent_lineage.py` — 46 tests covering structure counts, Track A/B disjointness, per-expert SKILL.md existence, 18-field shape, tools whitelist, lineage block, transform notes completeness, panel peer preservation, end-to-end bump+validate, main() exit code, individual YAML validation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Track B tools mapping corrected to match existing agent.yaml ground truth**
- **Found during:** Task 1 implementation (reading existing agent.yaml files for persona content)
- **Issue:** The plan's `<interfaces>` block specified stale tools lists for 3 of the 6 Track B experts:
  - `colorist`: plan said `["hermes_llm", "read_file", "search_files"]` but existing YAML has `["hermes_llm", "read_file", "search_files", "write_file"]` (LUT plan artifact writing)
  - `storyboard_designer`: plan said `["hermes_llm", "read_file", "write_file"]` but existing YAML has `["hermes_llm", "read_file", "search_files"]` (analysis-only)
  - `visual_executor`: plan said `["hermes_llm", "dreamina_cli", "read_file", "write_file"]` but existing YAML has `["hermes_llm", "hermes_llm_vision", "dreamina_cli", "read_file", "write_file", "patch"]` (vision + patch for sub-step iteration)
- **Fix:** TRACK_B_TOOLS in the script matches the existing `~/.hermes/agents/<name>.agent.yaml` files (the ground truth). The existing YAMLs are the proven production state from v13.0 P62 / v14.0 P75.
- **Files modified:** scripts/bump_all_agent_lineage.py (TRACK_B_TOOLS dict)
- **Commit:** fc11ae840

**2. [Rule 1 - Bug] TRACK_B_PANEL broadened to preserve collaboration graph**
- **Found during:** Task 1 implementation (comparing existing agent.yaml related_agents vs source SKILL.md related_skills)
- **Issue:** The plan specified `TRACK_B_PANEL: frozenset[str] = frozenset(ACTIVE_EXPERTS_15)`. But the existing v13.0 P62 Track B YAMLs' related_agents arrays include 3 non-expert agent peers (compliance_gate, production, prompt_injector) and the legacy name `scene_builder`. Filtering to ACTIVE_EXPERTS_15 alone would strip these peers, regressing the collaboration graph.
- **Fix:** TRACK_B_PANEL includes ACTIVE_EXPERTS_15 + the 3 non-expert peers + scene_builder. Additionally, `transform_track_b_one` does NOT apply LEGACY_NAME_MAP canonicalization (so scene_builder survives verbatim), matching the existing YAMLs.
- **Files modified:** scripts/bump_all_agent_lineage.py (TRACK_B_PANEL constant, _filter_related_agents_track_b function)
- **Commit:** fc11ae840

### Notes
- Ruff is not installed in the current Python environment (system python3 / .venv both lack the `ruff` module). CLAUDE.md compliance was verified manually: all `open()` calls use `encoding="utf-8"`, no `Path.home()` usage, lazy %-formatting in all logger calls, `except X as exc:` with bound names throughout. Ruff's only load-bearing rule (PLW1514) is satisfied.

## Threat Flags

None. No new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries were introduced beyond what the plan's `<threat_model>` already covers (T-82-07 through T-82-10, all accept/mitigate dispositions honored).

## Self-Check: PASSED

- [x] `scripts/bump_all_agent_lineage.py` exists — FOUND
- [x] `tests/agent/test_bump_all_agent_lineage.py` exists — FOUND
- [x] Commit `fc11ae840` exists in git log — FOUND
- [x] `python3 -m pytest tests/agent/test_bump_all_agent_lineage.py -x -q` — 46 passed
- [x] `python3 -c "import sys; sys.path.insert(0, 'scripts'); from bump_all_agent_lineage import ACTIVE_EXPERTS_15; print(len(ACTIVE_EXPERTS_15))"` — prints 15
