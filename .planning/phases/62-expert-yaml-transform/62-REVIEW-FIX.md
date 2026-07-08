---
phase: 62-expert-yaml-transform
fixed_at: 2026-07-08T00:43:48Z
review_path: .planning/phases/62-expert-yaml-transform/62-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 62: Code Review Fix Report

**Fixed at:** 2026-07-08T00:43:48Z
**Source review:** `.planning/phases/62-expert-yaml-transform/62-REVIEW.md`
**Iteration:** 1
**Scope:** WARNING only (Info deferred per default `/gsd:code-review --fix` scope)

**Summary:**
- Findings in scope: 4 (WR-01, WR-02, WR-03, WR-04)
- Fixed: 4
- Skipped: 0
- Deferred to tech_debt: 5 INFO findings (IN-01 .. IN-05)

## Important Note on Commit Boundary

Three of the four WARNING fixes (WR-01, WR-02, WR-04) target files under
`/home/kai/.hermes/agents/*.agent.yaml` — the runtime agent registry directory
which is **outside the git repository** (it is `$HERMES_HOME/agents/`, populated
at runtime and not version-controlled). Edits to those files are applied
directly to the filesystem; they cannot be captured in a `git commit`.

Only WR-03 (`scripts/validate_phase62_yamls.py`) touches a repo-tracked file
and is therefore the single atomic commit on `gsd-reviewfix/62-2450301`.
The YAML edits are documented here in full detail so the change is auditable
even without a per-fix commit.

## Fixed Issues

### WR-01: `documentary_maker` persona typo "Flaherty romantic-romantic"

**Files modified:** `/home/kai/.hermes/agents/documentary_maker.agent.yaml`
**Commit:** (no git commit — file is outside the repo; runtime dir)
**Applied fix:** Single targeted Edit replacing `romantic-romantic` with
`romantic-tradition` on the persona line (line 8). Chose "romantic-tradition"
per REVIEW.md recommendation — refers to the romanticized documentary tradition
exemplified by Flaherty's *Nanook of the North*. Surrounding text and YAML
structure untouched.
**Verification:**
- `grep "romantic-romantic"` → no match (typo removed)
- `yaml.safe_load()` → parses successfully
- `validate_one('documentary_maker', schema)` → PASS

### WR-02: `visual_executor` + `continuity_auditor` runtime `tools` whitelist missing `hermes_llm_vision`

**Files modified:**
- `/home/kai/.hermes/agents/visual_executor.agent.yaml`
- `/home/kai/.hermes/agents/continuity_auditor.agent.yaml`

**Commit:** (no git commit — files outside repo; runtime dir)
**Applied fix:** Plan A from REVIEW.md. Inserted `- hermes_llm_vision`
immediately after `- hermes_llm` in the runtime `tools:` whitelist of both
YAMLs. Aligns runtime grants with (a) persona text that explicitly references
`hermes_llm_vision` for image comparison / quality checks and (b) the existing
`prerequisites.tools` entry which previously was the only place listing it.

`continuity_auditor` is a SHIPPED v11.0 YAML (Phase 49). The fix is consistent
with shipped conventions: tool-family grouping (`hermes_llm*` adjacent) mirrors
the implicit grouping already present in `screenplay.agent.yaml`'s `tools`
field. The fix narrows a latent semantic drift between prerequisites and
runtime grants rather than changing expert capabilities.
**Verification:**
- Both YAMLs: runtime `tools` now contains `hermes_llm_vision`, matching
  `prerequisites.tools`
- `yaml.safe_load()` → parses successfully on both
- `validate_one()` → PASS for both

### WR-03: validator script `import hashlib` is a dead import

**Files modified:** `scripts/validate_phase62_yamls.py`
**Commit:** `c24cf3d06` on `gsd-reviewfix/62-2450301`
**Applied fix:**
1. Removed `import hashlib  # reserved: Plan 04 SHA spot-check import compat (do not remove)`
   at line 31. Plan 04's SHA spot-check (if/when it ships) should import
   `hashlib` in its own script — preserving the import here created a
   "reserved" anchor that reinforced the dead-import pattern.
2. Synced the module docstring (T-62-SC supply-chain note, lines 24-25):
   previously read "PyYAML + jsonschema + hashlib all pre-existing in
   pyproject.toml core deps" — `hashlib` is Python stdlib (not a pyproject
   dep) and the validator no longer uses it; rewrote to "PyYAML + jsonschema
   both pre-existing in pyproject.toml core deps".
**Verification:**
- Tier 1: re-read modified section — both edits present, surrounding code intact
- Tier 2: `python3 -c "import ast; ast.parse(open('scripts/validate_phase62_yamls.py').read())"` → OK
- `python3 scripts/validate_phase62_yamls.py` → `OK: 21/21`
- `python3 -m pytest tests/scripts/test_validate_phase62_yamls.py -q` → `14 passed`

### WR-04: `compliance_gate.transform_notes` references nonexistent `aliases` field

**Files modified:** `/home/kai/.hermes/agents/compliance_gate.agent.yaml`
**Commit:** (no git commit — file outside repo; runtime dir)
**Applied fix:** Rewrote `transform_notes` so it no longer cites
`aliases: [compliance_marketing]` (a field that exists in the SKILL.md
frontmatter but was dropped during SKILL→agent transform because the 18-field
agent YAML schema has no `aliases`). New text routes the backward-compat story
through the `expert_id` map (which is what FOUND-08 backward-compat actually
keys on) and explicitly notes "18-field schema has no aliases" so future
transform-CLI implementers will not be misled.
**Verification:**
- `grep "aliases:" /home/kai/.hermes/agents/compliance_gate.agent.yaml` → no match
- `yaml.safe_load()` → parses successfully
- `validate_one('compliance_gate', schema)` → PASS

## Skipped Issues

None.

## Deferred to tech_debt (INFO scope, not in this fix run)

Per `/gsd:code-review --fix` default scope, INFO findings are NOT applied.
They are listed here so a future `--all` run (or manual sweep) can pick them
up. None are blocking; all are test-quality / doc-precision / robustness
improvements.

| ID   | File                                                    | One-line summary                                                                              |
|------|---------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| IN-01 | `scripts/validate_phase62_yamls.py:160-172`             | `--batch` argparse choices `{A,B}` vs config docstring `A|B|all` drift                        |
| IN-02 | `scripts/validate_phase62_yamls.py:185`                 | `main()` raises bare `FileNotFoundError` traceback when schema missing (poor CLI UX)          |
| IN-03 | `tests/scripts/test_validate_phase62_yamls.py:300-310`  | `test_no_yaml_load_in_source` inline-comment strip not AST-aware (fragile vs `#` in strings)  |
| IN-04 | `/home/kai/.hermes/agents/production.agent.yaml:23-24`  | transform_notes cites schema pattern as inline string instead of `agents-schema.yaml §2.9`    |
| IN-05 | `/home/kai/.hermes/agents/scene_builder.agent.yaml:22-26`| transform_notes indirect-cites §2.7 (cinematographer row) instead of own §2.x section          |

## Final Verification State

| Check                                           | Result     |
|-------------------------------------------------|------------|
| `python3 scripts/validate_phase62_yamls.py`     | `OK: 21/21` |
| `python3 -m pytest tests/scripts/test_validate_phase62_yamls.py -q` | `14 passed` |
| YAML schema validity (all 21 agent YAMLs)       | PASS       |
| Tier 1 verification on every fix                | PASS       |
| Tier 2 syntax check (validator script)          | PASS       |

## REVIEW.md Status Update

`status: issues_found` → `status: fixed` (all WARNING-scope findings resolved;
INFO-scope findings deferred per default scope and documented as tech_debt).

---

_Fixed: 2026-07-08T00:43:48Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
