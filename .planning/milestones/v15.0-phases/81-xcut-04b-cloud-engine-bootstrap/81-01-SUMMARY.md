---
phase: 81-xcut-04b-cloud-engine-bootstrap
plan: 01
subsystem: infra
tags: [cloud-engine, hailuo, vidu, wan22, comfyui, config-schema, transition-routing, xcut-04b]

# Dependency graph
requires:
  - phase: 74-transition
    provides: transition-engine-routing.md declarative routing table with per-transition engine assignments (Hailuo/Vidu/Wan2.2 referenced)
provides:
  - cloud-engine-bootstrap.md — Hailuo + Vidu + Wan2.2 per-engine bootstrap doc with acquisition steps + cost worksheet
  - cloud_engines config schema (3 fields: hailuo_api_key + vidu_api_key + wan22_comfyui_node_enabled) documented in cli-config.yaml.example
  - Cloud Engine Opt-in State section in transition-engine-routing.md (config keys table + fallback behavior + declarative routing note)
  - kais-jimeng-cli SKILL.md Cloud Engine Bootstrap cross-reference section (single authorized SKILL.md touch)
affects: [81-02, 82-xcut-04c-cost-tracking, 83-validate]

# Tech tracking
tech-stack:
  added: []  # No new libraries — doc-only + config-only plan
  patterns: [config-primary-env-var-fallback, declarative-routing-opt-in, honesty-based-boolean-config]

key-files:
  created:
    - skills/kais-movie-pipeline/references/cloud-engine-bootstrap.md (kais-hermes-skills repo, 320 lines)
  modified:
    - skills/kais-movie-pipeline/references/transition-engine-routing.md (kais-hermes-skills repo — XCUT-04b section replaced with Cloud Engine Opt-in State)
    - skills/kais-creative/kais-jimeng-cli/SKILL.md (kais-hermes-skills repo — appended Cloud Engine Bootstrap section, 4 lines)
    - cli-config.yaml.example (hermes-agent repo — appended commented-out cloud_engines block, 22 lines)

key-decisions:
  - "Config-primary, env-var-fallback pattern: cloud_engines config block is canonical opt-in mechanism; HAILUO_API_KEY/VIDU_API_KEY env vars are fallback for CI/containers"
  - "Hailuo = MiniMax rebrand: both HAILUO_API_KEY and MINIMAX_API_KEY env vars accepted (same key); config key uses hailuo_api_key (consumer brand)"
  - "Wan2.2 uses boolean config (wan22_comfyui_node_enabled), not API key — honesty-based self-declaration, no automated verification (deferred to v16+)"
  - "Declarative routing only — no runtime LLM routing (INFRA-04 compliant per TRANS-10 deferral); check script is informational, not routing code"
  - "kais-jimeng-cli SKILL.md is the SINGLE authorized SKILL.md touch per v15.0 hard constraints; touch is minimal (4 lines appended at end, lines 1-483 unchanged)"

patterns-established:
  - "Config-primary-env-var-fallback: config.yaml is canonical; env vars are fallback for CI/containers. Check script (Plan 02) will report which source was used."
  - "Per-engine bootstrap doc structure: what it does + prerequisites + acquisition steps + configuration + verification + troubleshooting + pricing (6 subsections per engine)"
  - "Cost-estimation worksheet format: markdown table with engine | cost-per-shot | shots-per-episode | episodes-per-month | monthly-cost columns"

requirements-completed: [XCUT-04b-DOCS]

# Metrics
duration: 4min
completed: 2026-07-10
---

# Phase 81 Plan 01: Cloud Engine Bootstrap Doc Summary

**Hailuo + Vidu + Wan2.2 cloud engine bootstrap doc (320 lines) with per-engine acquisition steps + cost-estimation worksheet, config schema documented in cli-config.yaml.example, routing doc updated with Cloud Engine Opt-in State section, kais-jimeng-cli SKILL.md minimal cross-reference touch (single authorized exception)**

## Performance

- **Duration:** 4 min
- **Started:** 2026-07-10T07:18:42Z
- **Completed:** 2026-07-10T07:22:32Z
- **Tasks:** 2
- **Files modified:** 4 (1 new + 3 modified across 2 repos)

## Accomplishments
- Created cloud-engine-bootstrap.md (320 lines) with 3 per-engine sections (Hailuo + Vidu + Wan2.2), each covering: what it does, prerequisites, acquisition/install steps, configuration, verification, troubleshooting, pricing
- Created cost-estimation worksheet with markdown table + example calculation (Hailuo $10.08/month for 4 episodes × 15 cloud transitions) + operator-fill rows
- Updated transition-engine-routing.md: replaced XCUT-04b Operator-Action Handoff section with Cloud Engine Opt-in State section (config keys table + fallback behavior + declarative routing note + bootstrap doc link); updated routing table rows to reference config keys (config primary, env var fallback)
- Added commented-out cloud_engines config block to cli-config.yaml.example (22 lines, all commented out, documents 3 fields + env var fallback + bootstrap doc reference)
- Added Cloud Engine Bootstrap section to kais-jimeng-cli/SKILL.md (4 lines appended at end — single authorized SKILL.md touch per v15.0 hard constraints)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create cloud-engine-bootstrap.md + update transition-engine-routing.md** - `4c78e69` (docs, kais-hermes-skills repo)
2. **Task 2a: kais-jimeng-cli SKILL.md touch** - `c36382e` (docs, kais-hermes-skills repo)
3. **Task 2b: cli-config.yaml.example update** - `3a3a6d3a8` (docs, hermes-agent repo)

_Note: Task 2 was split into 2 commits because the files live in different repos (kais-hermes-skills vs hermes-agent)._

## Files Created/Modified
- `skills/kais-movie-pipeline/references/cloud-engine-bootstrap.md` (kais-hermes-skills) - NEW, 320 lines — Hailuo + Vidu + Wan2.2 per-engine bootstrap doc with acquisition steps + cost worksheet + config schema reference
- `skills/kais-movie-pipeline/references/transition-engine-routing.md` (kais-hermes-skills) - MODIFIED — XCUT-04b Operator-Action Handoff section replaced with Cloud Engine Opt-in State section; routing table rows updated to reference config keys
- `skills/kais-creative/kais-jimeng-cli/SKILL.md` (kais-hermes-skills) - MODIFIED — appended 4-line Cloud Engine Bootstrap section at end (line 484+); lines 1-483 unchanged
- `cli-config.yaml.example` (hermes-agent) - MODIFIED — appended 22-line commented-out cloud_engines config block at end

## Decisions Made
- Config-primary, env-var-fallback pattern for cloud engine opt-in (config.yaml is canonical; env vars HAILUO_API_KEY/VIDU_API_KEY are fallback for CI/containers)
- Hailuo = MiniMax rebrand documented explicitly in bootstrap doc + routing doc (both env var names accepted; config key uses hailuo_api_key per consumer brand)
- Wan2.2 uses boolean config (wan22_comfyui_node_enabled), not API key — honesty-based, no automated verification (v16+ scope)
- Declarative routing preserved (INFRA-04 compliant — no runtime LLM routing; TRANS-10 deferred to v16+)
- kais-jimeng-cli SKILL.md touch is minimal (4 lines, purely additive, no existing content modified) — single authorized exception per v15.0 hard constraints

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. The cloud_engines config block is commented out in cli-config.yaml.example. Operator opts in by uncommenting + pasting API keys when ready (per bootstrap doc).

## Next Phase Readiness
- Plan 02 (XCUT-04b-OPTIN) can proceed: config schema is documented, routing doc references config keys, bootstrap doc exists for operator reference
- The check_cloud_engine_optin.py script (Plan 02 deliverable) will read the cloud_engines config block documented in this plan
- Cross-repo topology: 3 files committed in kais-hermes-skills repo, 1 file committed in hermes-agent repo — both repos have clean commits for this plan

## Self-Check: PASSED

All 5 files verified to exist. All 3 commit hashes verified in git logs:
- `4c78e69` (kais-hermes-skills: cloud-engine-bootstrap.md + transition-engine-routing.md)
- `c36382e` (kais-hermes-skills: kais-jimeng-cli/SKILL.md)
- `3a3a6d3a8` (hermes-agent: cli-config.yaml.example)

---
*Phase: 81-xcut-04b-cloud-engine-bootstrap*
*Completed: 2026-07-10*
