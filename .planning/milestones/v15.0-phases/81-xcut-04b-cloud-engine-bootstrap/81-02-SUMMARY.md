---
phase: 81-xcut-04b-cloud-engine-bootstrap
plan: 02
subsystem: infra
tags: [cloud-engine, opt-in-check, hailuo, vidu, wan22, rich-table, xcut-04b]

# Dependency graph
requires:
  - phase: 81-xcut-04b
    plan: 01
    provides: cloud_engines config schema (hailuo_api_key + vidu_api_key + wan22_comfyui_node_enabled) documented in cli-config.yaml.example + cloud-engine-bootstrap.md
provides:
  - check_cloud_engine_optin.py — CLI opt-in status checker for cloud engines (reads config.yaml + env var fallback, Rich table + --json output, exits 0 always)
  - test_check_cloud_engine_optin.py — 23 unit tests covering all opt-in scenarios
affects: [83-validate]

# Tech tracking
tech-stack:
  added: []  # No new libraries — uses existing ruamel.yaml + rich
  patterns: [config-primary-env-var-fallback-sync-check, rich-table-dual-output, key-masking-information-disclosure-protection]

key-files:
  created:
    - skills/kais-movie-pipeline/scripts/check_cloud_engine_optin.py (kais-hermes-skills repo, 449 lines)
    - skills/kais-movie-pipeline/tests/test_check_cloud_engine_optin.py (kais-hermes-skills repo, 516 lines)

key-decisions:
  - "Config-primary-env-var-fallback: load_cloud_engines_config() reads config.yaml first; HAILUO_API_KEY/VIDU_API_KEY (and MINIMAX_API_KEY alias) env vars are fallback when config keys are null/missing"
  - "Key masking: API keys masked in output showing only last 4 chars ('****5678'); keys < 4 chars fully masked ('****') — T-81-04 information disclosure mitigation"
  - "Exit 0 always: check script is informational NOT pass/fail — not opting in is a valid state (ffmpeg fallback applies per D-05)"
  - "MINIMAX_API_KEY alias: Hailuo = MiniMax rebrand, so both HAILUO_API_KEY and MINIMAX_API_KEY env vars are accepted for the hailuo engine"
  - "wan22 has NO env var fallback: it's a local install boolean (wan22_comfyui_node_enabled), not an API key — must be set in config.yaml"

patterns-established:
  - "Dual-output pattern: --json for machine-readable, Rich table for human-readable (mirror run_cosyvoice_benchmark.py)"
  - "Source provenance tracking: _source sub-dict tracks whether each engine value came from config/env/not_set"

requirements-completed: [XCUT-04b-OPTIN]

# Metrics
duration: 3min
completed: 2026-07-10
---

# Phase 81 Plan 02: Cloud Engine Opt-in Check Script Summary

**CLI opt-in status checker (449 lines) + 23 unit tests (516 lines) — reads config.yaml cloud_engines block with env var fallback, prints Rich table + supports --json, exits 0 always (informational per D-05), INFRA-04 compliant (sync-only, zero GLM calls)**

## Performance

- **Duration:** 3 min
- **Started:** 2026-07-10T10:47:21Z
- **Completed:** 2026-07-10T10:50:19Z
- **Tasks:** 2
- **Files created:** 2 (1 script + 1 test file in kais-hermes-skills repo)

## Accomplishments
- Created check_cloud_engine_optin.py (449 lines) with 5 exported functions: load_cloud_engines_config, check_optin_status, get_available_transitions, emit_rich_table, main
- Script reads ~/.hermes/config.yaml cloud_engines block via ruamel.yaml + get_hermes_home() pattern (mirrors vision_verify.py get_threshold)
- Env var fallback: HAILUO_API_KEY + MINIMAX_API_KEY (alias) for hailuo; VIDU_API_KEY for vidu; wan22 has NO env var (local install boolean)
- Key masking in output: API keys show only last 4 chars ("****5678"); short keys fully masked ("****") — T-81-04 mitigation
- Rich table dual output: Table 1 = engine opt-in status (engine/opted_in/source/key_masked), Table 2 = transition method availability (12 transitions: 3 cloud-dependent + 9 ffmpeg-only)
- --json flag produces machine-readable JSON with "engines" + "transitions" arrays
- Exit 0 always (informational, not pass/fail per D-05)
- INFRA-04 compliant: sync-only, no async, no GLM calls, stdlib + ruamel.yaml + rich
- Created 23 unit tests (516 lines) covering: all opted in, none opted in, partial opt-in, env var fallback (hailuo/vidu/minimax-alias), missing config, invalid YAML, key masking (long + short), transition availability (all/hailuo-absent/none/ffmpeg-only), --json output, exit code, --help, Rich table rendering

## Task Commits

Each task was committed atomically:

1. **Task 1: Create check_cloud_engine_optin.py script** - `87b4b1d` (feat, kais-hermes-skills repo)
2. **Task 2: Create test_check_cloud_engine_optin.py unit tests** - `92af134` (test, kais-hermes-skills repo)

## Files Created/Modified
- `skills/kais-movie-pipeline/scripts/check_cloud_engine_optin.py` (kais-hermes-skills) - NEW, 449 lines — CLI opt-in status checker with 5 exported functions, Rich table + --json output
- `skills/kais-movie-pipeline/tests/test_check_cloud_engine_optin.py` (kais-hermes-skills) - NEW, 516 lines — 23 unit tests in 5 test classes covering all opt-in scenarios

## Decisions Made
- Config-primary-env-var-fallback pattern: load_cloud_engines_config() checks config.yaml first, then env vars as fallback (CI/containers)
- MINIMAX_API_KEY alias: Hailuo = MiniMax rebrand, so both env var names accepted (same key, different brand names)
- Key masking implementation: `_mask_key()` helper shows last 4 chars for keys > 4 chars; fully masks short keys — prevents accidental API key exposure in terminal output
- Transition availability: get_available_transitions() builds ordered engine chain lookup; first opted-in engine in chain becomes active; ffmpeg entries always available
- Source provenance: _source sub-dict tracks "config"/"env"/"not_set" per engine for operator visibility

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. The check script is informational and reads existing config (which may be empty/all-not-opted-in — a valid state).

## Next Phase Readiness
- Phase 81 is fully complete (Plan 01 docs + Plan 02 code)
- XCUT-04b-OPTIN requirement satisfied: operator can run `python scripts/check_cloud_engine_optin.py` and see Rich table showing opt-in status + available transitions
- Cross-repo topology: both files committed in kais-hermes-skills repo

## Self-Check: PASSED

All files verified to exist. All commit hashes verified in git logs:
- `87b4b1d` (kais-hermes-skills: check_cloud_engine_optin.py)
- `92af134` (kais-hermes-skills: test_check_cloud_engine_optin.py)

All 23 tests pass (0.48s execution time).

---
*Phase: 81-xcut-04b-cloud-engine-bootstrap*
*Completed: 2026-07-10*
