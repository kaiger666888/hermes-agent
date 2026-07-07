---
phase: 53-creative-slice
plan: 01
subsystem: agent-registry-transform
tags: [migr-01, agent-yaml, transform, hook-09, registry, screenplay-step3]
requires:
  - "Phase 52 contract surface (registry_loader, round_table_state, round_table_executor, memory_arbitration)"
  - "kais-hermes-skills repo (9 source SKILL.md files, read-only)"
  - "agents-schema.yaml (v10.0 18-field Draft 2020-12 schema)"
provides:
  - "9 agent YAMLs at ~/.hermes/agents/*.agent.yaml (screenplay, cinematographer, hook_retention, theory_critic, editor, character_designer, continuity_auditor, audio_pipeline, style_genome)"
  - "scripts/transform_skill_to_agent.py (one-shot CLI, public transform_one() API)"
  - "tests/fixtures/screenplay-step3-schema.json (HOOK-09 emotion_curve marker contract schema, consumed by plan 53-03)"
  - "tests/fixtures/transform-audit-log.json (9-entry field-mapping audit trail per SC#1)"
  - "tests/agent/test_phase52_contract.py (Wave 0 import + stub-contract gate for plans 53-02 / 53-03)"
affects:
  - "Plan 53-02 (CREATIVE-01 driver) consumes the 9 YAMLs via load_agent_registry"
  - "Plan 53-03 (CREATIVE-02 arbitration) inherits Wave 0 contract gate"
tech-stack:
  added: []
  patterns:
    - "SKILL→agent YAML transform per Phase 49 §2 75-cell rules"
    - "LF-normalized SHA-256 for source lineage (RESEARCH Pitfall 7 mitigation)"
    - "LEGACY_NAME_MAP canonicalization (FOUND-08 + Pattern 1b)"
    - "Per-expert first-person SYSTEM-prompt persona (ARCHITECTURE §2.4 + §8.1)"
key-files:
  created:
    - scripts/transform_skill_to_agent.py
    - tests/agent/test_phase52_contract.py
    - tests/agent/test_transform_skill_to_agent.py
    - tests/fixtures/screenplay-step3-schema.json
    - tests/fixtures/transform-audit-log.json
    - ~/.hermes/agents/screenplay.agent.yaml
    - ~/.hermes/agents/cinematographer.agent.yaml
    - ~/.hermes/agents/hook_retention.agent.yaml
    - ~/.hermes/agents/theory_critic.agent.yaml
    - ~/.hermes/agents/editor.agent.yaml
    - ~/.hermes/agents/character_designer.agent.yaml
    - ~/.hermes/agents/continuity_auditor.agent.yaml
    - ~/.hermes/agents/audio_pipeline.agent.yaml
    - ~/.hermes/agents/style_genome.agent.yaml
  modified: []
decisions:
  - "Filter source tags via agents-schema.yaml §2.9 regex `^[a-z0-9-]+$` (drop non-ASCII tags like `镜头语言` rather than fail validation)"
  - "Leave RAG refs array empty in v11.0 PoC; refs wiring deferred to a later phase (CONTEXT.md deferred list)"
  - "Operator-invoked CLI script (not background-triggered) per RESEARCH anti-pattern 'Auto-re-transform on SHA-256 drift'"
  - "9 production YAMLs live at ~/.hermes/agents/ (NOT under tests/fixtures/); test isolation via HERMES_HOME redirection"
metrics:
  duration: "~22 min"
  completed: "2026-07-07"
  tasks_completed: 2
  tests_passed: 28
  files_created: 14
  files_modified: 0
---

# Phase 53 Plan 01: 9-Agent YAML Transform (MIGR-01) Summary

Transformed 9 sample movie-expert SKILL.md files into agent YAMLs at `~/.hermes/agents/*.agent.yaml`, validating each against the locked Phase 45 `agents-schema.yaml` (18-field Draft 2020-12 schema) and preserving the HOOK-09 emotion_curve marker invariant in `screenplay.agent.yaml`. Wave 0 contract smoke test proves the Phase 52 surface (registry_loader / round_table_state / round_table_executor / memory_arbitration) imports cleanly and stub return payloads are intact.

## What Was Built

### scripts/transform_skill_to_agent.py

One-shot operator-invoked CLI (`python scripts/transform_skill_to_agent.py`) that:

1. Walks the 9-expert subset (`screenplay, cinematographer, hook_retention, theory_critic, editor, character_designer, continuity_auditor, audio_pipeline, style_genome`) per CONTEXT.md decision #1.
2. Reads each source `SKILL.md` from `/data/workspace/kais-hermes-skills/skills/movie-experts/<name>/SKILL.md` (read-only per Phase 48 + 49 lineage invariants).
3. Calls `transform_one(expert_name, skill_md_path)` — pure function returning the 18-field agent YAML dict.
4. Writes the YAML to `~/.hermes/agents/<name>.agent.yaml` (production path).
5. Post-write validates each YAML via `load_one_agent_yaml()` — exits non-zero on any `RegistryValidationError` (never silently emits invalid YAMLs).
6. Writes a 9-entry audit log to `tests/fixtures/transform-audit-log.json` documenting every frontmatter→YAML field mapping.

Public API: `transform_one(expert_name, skill_md_path) -> dict[str, Any]`. Internal helpers:
- `_compute_skill_sha256(content)`: LF-normalize (`\r\n` → `\n`) then SHA-256 hex.
- `_filter_related_agents(related_skills)`: apply `LEGACY_NAME_MAP` (`scene_builder`→`cinematographer`, `continuity`→`continuity_auditor`, `performer`→`character_designer`, `composer`→`audio_pipeline`), then filter to `PANEL_9`.
- `_build_persona(expert_name, body)`: dispatches to 9 per-expert persona builders (`_persona_screenplay`, `_persona_cinematographer`, ...). First-person SYSTEM-prompt fragment citing load-bearing frameworks (Snyder / McKee / Tan / cn-shortdrama-structure for screenplay, etc.).
- `_transform_notes(expert_name)`: per-expert verbatim from Phase 49 §2.x. Screenplay entry contains the literal HOOK-09 invariant substring.
- `_tools_for(expert_name)`: returns Phase 49 §2.x per-expert default whitelist.

### tests/fixtures/screenplay-step3-schema.json

JSON Schema Draft 2020-12 document defining the HOOK-09 emotion_curve marker contract. Declares 6 top-level fields: `logline`, `scene_breakdown` (each entry with its own per-scene `emotion_curve`), `hooks` (5-type enum: cold_open / curiosity / shock / cliffhanger / paywall), `payoffs`, `cliffhangers`, top-level `emotion_curve`. `additionalProperties: false`, all 6 in `required`. Consumed by plan 53-03 driver output validation.

### tests/agent/test_phase52_contract.py

5-test Wave 0 gate covering all 11 Phase 52 public symbols + 2 locked stub return contracts + HOOK-09 schema fixture structural validation. Async tests carry explicit `@pytest.mark.asyncio` (strict mode per RESEARCH Pitfall 3).

### tests/agent/test_transform_skill_to_agent.py

7-test behavior coverage:
- Test 1 (parametrized 9): per-expert tools whitelist matches Phase 49 §2.x.
- Test 2: HOOK-09 verbatim substring in screenplay `lineage.transform_notes`.
- Test 3: SHA-256 LF-normalization (CRLF checkout mitigation per Pitfall 7).
- Test 4 (parametrized 9): filename-stem invariant + `load_one_agent_yaml` round-trip.
- Test 5: all 9 YAMLs load via `load_agent_registry` (end-to-end SC#1).
- Test 6: `LEGACY_NAME_MAP` canonicalization + FOUND-08 deprecated-name preservation.
- Test 7: 9-entry audit log structure with non-empty `frontmatter_mappings`.

### ~/.hermes/agents/*.agent.yaml (9 production YAMLs)

All 9 emitted by the CLI invocation. Each carries:
- 7 required fields (`name, description, version, persona, tools, memory_scope, lineage`) ✓
- 11 optional fields (`refs, tags, expert_id, metrics, prerequisites, related_agents, evolution_log, fitness_score, platforms, round_table_eligible, default_invocation`) ✓
- `lineage.skill_sha256` matches LF-normalized SHA-256 of source SKILL.md ✓
- `name` field matches filename stem (T-52-03 spoofing mitigation) ✓
- `tags` filtered to schema pattern (no non-ASCII tags leaked) ✓

## Success Criteria Verification

| SC | Description | Status | Evidence |
|----|-------------|--------|----------|
| SC#1 | 9 agent YAMLs validate against agents-schema.yaml; lineage has derived_from_skill_id + skill_sha256 | PASS | `load_agent_registry(force_reload=True)` returns 9 agents; each YAML passes `load_one_agent_yaml` |
| HOOK-09 | `screenplay.agent.yaml` lineage.transform_notes contains literal substring `HOOK-09 emotion_curve marker arrays remain contract-load-bearing` | PASS | `grep -c` returns 2 matches (persona fragment + transform_notes) |
| Audit trail | `tests/fixtures/transform-audit-log.json` documents field mappings per Phase 49 §2 75-cell rules for all 9 experts | PASS | Test 7 verifies 9 entries with non-empty frontmatter_mappings |
| Wave 0 | Phase 52 imports resolve; stub return contracts (`phase53_not_implemented`) intact | PASS | 5/5 `test_phase52_contract.py` tests green |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed non-ASCII tag schema violation**

- **Found during:** Task 2 GREEN run
- **Issue:** `cinematographer` source SKILL.md `metadata.hermes.tags` array contained `镜头语言` (Chinese tag). `agents-schema.yaml` §2.9 declares tag pattern `^[a-z0-9-]+$` which rejects non-ASCII. `load_one_agent_yaml` raised `RegistryValidationError: schema violation at $.tags[6]`.
- **Fix:** Added `_TAG_PATTERN = re.compile(r"^[a-z0-9-]+$")` and filtered tags in `transform_one()`: `filtered_tags = [t for t in raw_tags if isinstance(t, str) and _TAG_PATTERN.fullmatch(t)]`. Documented in audit log entry under `tags` mapping.
- **Files modified:** `scripts/transform_skill_to_agent.py`
- **Commit:** f42911277

No other deviations — plan executed as written.

## Open Issues

None.

## Notes for Downstream Plans

### Plan 53-02 (CREATIVE-01 driver)

- The 9 YAMLs at `~/.hermes/agents/` are live and discoverable via `load_agent_registry()`. No further transform needed before invoking `round_table_open`.
- The HOOK-09 schema at `tests/fixtures/screenplay-step3-schema.json` is ready for output validation in the driver.
- Operator-config gap (OQ-4 resolution): `cli-config.yaml.example` still needs `auxiliary.round_table_opinion` + `auxiliary.memory_comparator` entries — deferred to plan 53-03 Task 2 per RESEARCH OQ-4 resolution.

### Plan 53-03 (CREATIVE-02 arbitration)

- Wave 0 contract test (`tests/agent/test_phase52_contract.py`) confirms Phase 52 stubs return `phase53_not_implemented` payloads — these are the gates Phase 53-03 will swap for real routing.
- `_scoped_agent_id` ContextVar + `set_scoped_agent_id` / `get_scoped_agent_id` are importable from `agent.memory_arbitration` — ready for routing integration.

## Self-Check: PASSED

Created files verified to exist on disk:
- scripts/transform_skill_to_agent.py — FOUND
- tests/agent/test_phase52_contract.py — FOUND
- tests/agent/test_transform_skill_to_agent.py — FOUND
- tests/fixtures/screenplay-step3-schema.json — FOUND
- tests/fixtures/transform-audit-log.json — FOUND
- ~/.hermes/agents/screenplay.agent.yaml — FOUND
- ~/.hermes/agents/cinematographer.agent.yaml — FOUND
- ~/.hermes/agents/hook_retention.agent.yaml — FOUND
- ~/.hermes/agents/theory_critic.agent.yaml — FOUND
- ~/.hermes/agents/editor.agent.yaml — FOUND
- ~/.hermes/agents/character_designer.agent.yaml — FOUND
- ~/.hermes/agents/continuity_auditor.agent.yaml — FOUND
- ~/.hermes/agents/audio_pipeline.agent.yaml — FOUND
- ~/.hermes/agents/style_genome.agent.yaml — FOUND

Commits verified in git log:
- 2d1fac8c0 — test(53-01): Wave 0 contract smoke test + HOOK-09 schema fixture — FOUND
- f42911277 — feat(53-01): SKILL→agent YAML transform for 9 movie-expert PoC agents — FOUND

Test suite: 28/28 green (5 contract + 23 transform).
