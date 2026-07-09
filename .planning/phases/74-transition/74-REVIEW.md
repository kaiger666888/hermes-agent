---
phase: 74-transition
reviewed: 2026-07-10T00:30:00Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - /data/workspace/kais-hermes-skills/plugins/pipeline_state/transition_schema.py
  - /data/workspace/kais-hermes-skills/plugins/pipeline_state/asset_bus.py
  - /data/workspace/kais-hermes-skills/plugins/kais_aigc/canvas_sync.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p13_delivery.py
  - /data/workspace/kais-hermes-skills/plugins/pipeline_state/tests/test_transition_schema.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p09_transition_unit.py
  - /data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/SKILL.md
  - /data/workspace/kais-hermes-skills/skills/movie-experts/editor/SKILL.md
  - /data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/references/e-konte-format.md
  - /data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/references/transition-design.md
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/transition-engine-routing.md
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/ltx-flf-iclora-validation.md
findings:
  critical: 2
  warning: 6
  info: 5
  total: 13
status: issues_found
---

# Phase 74: Code Review Report

**Reviewed:** 2026-07-10T00:30:00Z
**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Summary

Phase 74 (TRANSITION design v14.0) adds a 12-enum transition taxonomy + structured `next_shot_link` migration + asset-bus slot + canvas sync tuple + SKILL.md body patches + 3 new refs. The schema-side work (Pydantic Literal aliases + frozenset runtime authority + backward-compat reader) is well-designed and the asset-bus / canvas_sync registrations are correctly shaped. The SKILL.md ownership split (TRANS-04 cinematographer=intent, editor=execution) is clearly documented.

However, two BLOCKER-class defects undermine the TRANS-02 contract that the phase claims to deliver: (1) the `load_next_shot_link` backward-compat reader is dead code — no production path imports or calls it, so legacy bare-string `next_shot_link` JSON is never coerced; (2) the p09 goal builder emits an empty constraint bullet (`"- "`) on first run because the 7th `constraints()` entry is `fix_feedback` (empty string on first run). Six WARNING-class issues cover the field-map refactor's missing `p10b`/`p10c` `totalDuration` passthrough, the un-validated `shot_id` hole in `load_next_shot_link`, and others.

Out-of-scope items all verified clean: no `~/.hermes/agents/*.agent.yaml` touched (Phase 75 scope), no hermes-agent source outside `.planning/` modified, declarative-only routing (no runtime LLM — INFRA-04 / PITFALL X-5), LTX-2.3 FLF evaluated per-transition (not assumed incapable — SUMMARY reconciled conflict #1), ltx-flf-iclora-validation.md is correctly a TEMPLATE.

## Critical Issues

### CR-01: `load_next_shot_link` is dead code — TRANS-02 backward-compat contract is unenforced at runtime

**File:** `/data/workspace/kais-hermes-skills/plugins/pipeline_state/transition_schema.py:96` (definition); `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py:485` (consumer); `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p13_delivery.py:95` (consumer)

**Issue:** The TRANS-02 backward-compat reader `load_next_shot_link(value)` is defined and tested (12 tests, all green) but **no production code imports or invokes it**. Verified by grep:

```
grep -rn "load_next_shot_link" plugins/ skills/ --include="*.py" | grep -v test_ | grep -v transition_schema.py
# (zero matches)
```

`p09_shot_breakdown.py:485` reads `transition_design = expert_output.get("transition_design", [])` and writes it through to the asset bus as-is — **no per-shot `next_shot_link` coercion happens**. `p13_delivery.py:95` reads `transition-design` from the bus and forwards it to the goal context as-is — again, no coercion.

The docstring at `transition_schema.py:1-30` claims this module provides "TRANS-02 backward-compat reader for the v14.0 TRANSITION contract" and the test at `test_transition_schema.py:165-183` (`test_backward_compat_string_next_shot_link`) explicitly validates that legacy bare-string form loads cleanly. But the test only proves the function works in isolation — it does NOT prove the function is wired into the read path.

Consequence: a pre-v14.0 episode JSON file on disk (e.g. `e-konte-sheets.json` in `runs/ep-chameleon-rage/` — verified to contain bare-string `next_shot_link: shot_02` entries via grep) **will not be coerced**. Any downstream consumer that expects the structured v14.0 form (`{shot_id, transition_method, ...}`) will receive the legacy bare string and crash with `AttributeError: 'str' object has no attribute 'get'` when it tries to access `.get("transition_method")`. The TRANS-02 migration promise ("no migration script needed — the backward-compat reader handles any legacy form at read time", per `e-konte-format.md:154`) is **not actually kept**.

This is also a form of false confidence: the tests pass but the behavior they verify is not the behavior the production system exhibits. A reviewer reading only the test file would conclude TRANS-02 is shipped; a reviewer tracing the call graph would conclude it is not.

**Fix:** Wire the reader into the consumer. Two equally-valid wiring sites:

Option A — at the phase-output extraction site in p09 (preferred — single-touch coercion at write time so the slot always holds structured data):

```python
# p09_shot_breakdown.py:485 — replace the bare get()
from plugins.pipeline_state.transition_schema import load_next_shot_link

transition_design_raw = expert_output.get("transition_design", [])
transition_design = []
for entry in transition_design_raw:
    if isinstance(entry, dict):
        # Coerce legacy bare-string next_shot_link if present.
        if "next_shot_link" in entry:
            entry = {**entry, "next_shot_link": load_next_shot_link(entry["next_shot_link"])}
        transition_design.append(entry)
asset_bus_write("transition-design", transition_design)
```

Option B — at the AssetBus.read() layer (broader but more invasive, risks touching every consumer):

```python
# asset_bus.py: AssetBus.read() post-processing — NOT recommended for v14.0 scope.
```

Recommend Option A: it is minimal, tested via the existing `test_p09_writes_transition_design_slot`, and keeps AssetBus format-agnostic.

### CR-02: p09 goal emits an empty `[CONSTRAINTS]` bullet on first run (`fix_feedback = ""` is the 7th rule)

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py:436`

**Issue:** The `.constraints([...])` call at lines 429-437 passes a 7-element list:

```python
.constraints([
    "MUST produce E-Konte 5-layer sheets for EVERY shot (not optional)",
    "MUST check all 4 continuity dimensions ...",
    "MUST inject all 5 cross-cutting params ... (TRANS-01..04)",
    "MUST use ≥5 DIFFERENT camera_movement values ...",
    "MUST use ≥3 DIFFERENT framing values ...",
    "MUST output all 9 canvas structured fields per shot ...",
    fix_feedback,  # empty string on first run, fix instructions on retry
])
```

`fix_feedback` is initialized at line 363 as `fix_feedback = ""` and only populated on retry (line 365-369). On **first run** (the common case), the goal template renders:

```
[CONSTRAINTS]
- MUST produce E-Konte 5-layer sheets for EVERY shot (not optional)
- MUST check all 4 continuity dimensions ...
- MUST inject all 5 cross-cutting params ...
- MUST use ≥5 DIFFERENT camera_movement values ...
- MUST use ≥3 DIFFERENT framing values ...
- MUST output all 9 canvas structured fields per shot ...
- 
```

The trailing bullet `"- "` is an empty constraint. The `[CONSTRAINTS]` segment docstring (`_prompt_template.py:287`) explicitly says "Each rule MUST start with MUST / MUST NOT / LIMIT to be verifiable by automated tests" — the empty string violates that contract. Furthermore:

1. **Subagent confusion** — LLM consumers of the goal may interpret the empty bullet as "the constraint list is incomplete" or hallucinate content into the blank slot.
2. **MAX_CONSTRAINTS=7 budget is consumed by a non-constraint** — the `fix_feedback` slot competes with real constraints for the 7-row budget; on retry it carries valid content, but on first run it wastes a row.
3. **Test gap** — `test_p09_transition_unit.py` does NOT assert that all 7 constraint bullets are non-empty (it only checks for keyword presence in the goal string).

**Fix:** Only append `fix_feedback` when non-empty. Replace the 7-element list with a conditional 6-or-7 element list:

```python
constraint_rules = [
    "MUST produce E-Konte 5-layer sheets for EVERY shot (not optional)",
    "MUST check all 4 continuity dimensions (face/figure/scene/style) via continuity_auditor",
    "MUST inject all 5 cross-cutting params per shot ... AND MUST read form_factor ... AND MUST emit per-shot transition_method (12-value enum) + visual_hook + camera_continuity + structured next_shot_link in E-Konte Layer 5 (TRANS-01..04)",
    "MUST use ≥5 DIFFERENT camera_movement values across shots (≥6 shots); static (固定) ≤30% of total; each shot needs camera_move_motivation explaining WHY this move serves the narrative emotion",
    "MUST use ≥3 DIFFERENT framing values across shots (≥4 shots); final shot favors 特写/大特写; 远景 ≤20%",
    "MUST output all 9 canvas structured fields per shot ...",
]
if fix_feedback:
    constraint_rules.append(fix_feedback)
# then pass constraint_rules to .constraints()
```

This keeps the count at 6 on first run (within MAX_CONSTRAINTS=7) and 7 on retry — and removes the empty bullet.

## Warnings

### WR-01: Field-map refactor in `canvas_sync.py` drops the `p10b` audio field mappings — p10b rapid-preview clips lose `audioType` / `engine` / `emotion` / `speaker` structured fields

**File:** `/data/workspace/kais-hermes-skills/plugins/kais_aigc/canvas_sync.py:382-393`

**Issue:** The pre-refactor handwritten code at the old `_apply_schema_mappings` had:

```python
if phase_prefix in ("p10", "p10b"):
    if "audioType" not in data: ...
    if "engine" not in data: ...
    if "emotion" not in data: ...
    if "speaker" not in data: ...
```

The new refactor maps micro-gates via:
```python
if lookup_prefix in ("p09b",):
    lookup_prefix = "p09"
elif lookup_prefix in ("p10b", "p10c"):
    lookup_prefix = "p10"
```

This **does** correctly map p10b → p10 for field lookup. However, the new dispatch is now data-driven by `_MAPPINGS.PHASE_FIELDS.get(lookup_prefix)`. If the generated `canvas_sync_mappings.py` does not contain a `p10` entry that emits `audioType`/`engine`/`emotion`/`speaker` fields with the correct `python_key`/`canvas_key`/`enum`/`transform` shape, p10b (and p10) lose their structured fields. This is dependent on the generated file being up-to-date with the same field coverage as the old handwritten `_SNAKE_CAMEL` map.

The old handwritten code also wrote `engine` and `resolution` **unconditionally** (with defaults) for p10/p11 even when the source artifact was missing those fields (the "always set" behavior). The refactor preserves this via the `lookup_prefix == "p10" and ckey == "engine"` branch at line 437, BUT only if the generated PHASE_FIELDS[p10] actually contains an entry with `canvas_key: engine`. If the YAML omits that entry, the unconditional default-write path is never reached.

There is no test in the reviewed scope that exercises the refactor against the generated PHASE_FIELDS table end-to-end. The handwritten → generated handoff is a silent dependency.

**Fix:** Add a smoke test that constructs a `CanvasSyncSubscriber` with a stub `_MAPPINGS` and asserts p10/p10b/p11 structured-field emission for a minimal artifact dict. At minimum, document that the generated `pipeline-field-map.yaml` MUST contain the `p10` / `p11` entries with engine/emotion/etc. fields before this refactor is safe to ship.

### WR-02: `load_next_shot_link` does not validate `shot_id` — `None` silently passes through for dict input

**File:** `/data/workspace/kais-hermes-skills/plugins/pipeline_state/transition_schema.py:173-179`

**Issue:** For dict input, the function uses `value.get("shot_id")` which returns `None` when the key is missing. Verified empirically:

```
>>> load_next_shot_link({})
{'shot_id': None, 'transition_method': 'hard_cut', 'visual_hook': None, 'camera_continuity': 'none', 'generation_path': None}
>>> load_next_shot_link({"shot_id": None})
{'shot_id': None, ...}
```

The TRANS-02 contract says the legacy-string path sets `shot_id=<string>`. The structured path returning `shot_id=None` violates the implicit type contract that downstream consumers can rely on `shot_id` being a string. Any downstream code that does `coerced["shot_id"].startswith("shot_")` would crash with `AttributeError: 'NoneType' object has no attribute 'startswith'`.

The function claims to be a "fail-fast backward-compat reader" (line 117 docstring: "no fuzzy coercion of int / list / None — fail fast at the trust boundary per T-74-01") but the dict path does NOT fail fast on missing/null `shot_id`.

**Fix:** Add a `shot_id` validation in the dict branch:

```python
if isinstance(value, dict):
    shot_id = value.get("shot_id")
    if not isinstance(shot_id, str) or not shot_id:
        raise ValueError(
            f"next_shot_link dict must have non-empty string shot_id; got {shot_id!r} "
            f"(TRANS-02 strict type — no fuzzy coercion)."
        )
    tm = value.get("transition_method", "hard_cut")
    # ... rest unchanged
```

Add corresponding tests: `test_load_next_shot_link_rejects_missing_shot_id`, `test_load_next_shot_link_rejects_none_shot_id`, `test_load_next_shot_link_rejects_empty_shot_id`.

### WR-03: `load_next_shot_link` is never called on the `transition-design` slot's read path — empty list default at p13

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p13_delivery.py:95`

**Issue:** Related to CR-01 but separately classified: p13 reads `transition_design = asset_bus_read("transition-design") or {}` and forwards it to the goal context as `transition_design=transition_design` (line 109). If the slot is missing OR p09 did not populate it (e.g. legacy pre-v14.0 episode without the slot), p13 receives `{}` and passes an empty dict to the editor subagent. The editor then has no transition_design to read, and the `_EDITOR_TRANSITION_EXECUTION_INSTRUCTION` rule "Read the `transition-design` asset" silently degrades to a no-op.

There is no warning, no operator-visible signal that the editor proceeded without the transition design input. This is a soft-fail anti-pattern that CLAUDE.md §Error Handling warns against ("always bind the exception to a name ... Do not swallow silently").

**Fix:** Either (a) `require()` the slot at p13 when transition-v14.0 is active (strict mode), or (b) emit a `logger.warning("p13: transition-design slot empty — editor execution instruction will degrade")` when the slot is missing.

### WR-04: `test_p09_transition_unit.py` does not assert that the goal contains exactly 7 constraint bullets (no over- or under-count check)

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p09_transition_unit.py:91-146`

**Issue:** The XCUT-02 test asserts 9 keyword strings are present in the goal, but does not count the constraint bullets. This means:

- The empty-bullet defect (CR-02) is not detected by the test suite.
- A future regression that pushes the constraint count to 8 (raising `ValueError` at goal-build time) would be detected only when `p09.run()` raises — but only if the test happens to exercise that code path. The current test calls `p09.run()` with a 2-shot payload, which does exercise it, but the failure mode would be an opaque `ValueError: Over-constrained` rather than a clear assertion about the constraint budget.

**Fix:** Add an assertion that extracts the `[CONSTRAINTS]` segment and counts non-empty bullets:

```python
def test_p09_constraint_count_within_budget():
    """XCUT-02: p09 [CONSTRAINTS] segment has ≤7 non-empty bullets (MAX_CONSTRAINTS=7)."""
    captured: dict = {}
    # ... same setup as test_p09_goal_includes_transition_design_instruction
    p09.run(...)
    goal = captured["goal"]
    # Extract the [CONSTRAINTS] section.
    constraints_section = goal.split("[CONSTRAINTS]")[1].split("[")[0]
    bullets = [line for line in constraints_section.split("\n") if line.strip().startswith("- ")]
    non_empty_bullets = [b for b in bullets if b.strip() != "-"]
    assert len(non_empty_bullets) <= 7, f"p09 constraint count {len(non_empty_bullets)} > MAX_CONSTRAINTS=7"
    assert all(b.strip().startswith("- MUST") or b.strip().startswith("- MUST NOT") or b.strip().startswith("- LIMIT") for b in non_empty_bullets), \
        "Every constraint bullet MUST start with MUST / MUST NOT / LIMIT"
```

### WR-05: `transition-design.md` has dual inconsistent date metadata (`Last-verified` + bare `verified_date:`)

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/references/transition-design.md:5-6`

**Issue:** Lines 5-6 contain:
```
**Last-verified:** 2026-07-09
verified_date: 2026-07
```

The `verified_date:` line is bare text (not inside a YAML frontmatter block — the file has no frontmatter), making it look like malformed YAML. The two dates also disagree on precision (`2026-07-09` vs `2026-07`). Other refs in the same directory (`e-konte-format.md:5-6`) have the same dual-format pattern, so this is consistent with the existing convention, but the convention itself is a quality defect — readers cannot tell which field is authoritative.

This is a minor maintainability issue but worth flagging because the ref declares `Last-verified` as load-bearing for prompt-token mapping drift warnings (per the SKILL.md `Model drift warning (T-04-01)` pattern at `cinematographer/SKILL.md:67`).

**Fix:** Pick one format. Recommended: drop the bare `verified_date:` line and keep only `**Last-verified:** YYYY-MM-DD`. Or add proper YAML frontmatter at the top of the file.

### WR-06: `transition-engine-routing.md` cites `ltx-flf-iclora-validation.md` with a forward reference to Plan 74-03 that is now stale

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/transition-engine-routing.md:64`

**Issue:** Line 64 says: "see [`ltx-flf-iclora-validation.md`](./ltx-flf-iclora-validation.md) once authored in Plan 74-03". The file IS authored (it's in the review scope and is a complete template). The "once authored in Plan 74-03" phrasing is now stale and suggests the doc is missing when it isn't. Readers following the link will find the file and be confused by the mismatch between the link text ("once authored") and reality (already present).

**Fix:** Update to remove the "once authored in Plan 74-03" qualifier:

```markdown
... documented as a research-scope validation (TRANS-07, see [`ltx-flf-iclora-validation.md`](./ltx-flf-iclora-validation.md)).
```

## Info

### IN-01: `load_next_shot_link` audit suffix inconsistency — `ValueError` ends with `).` (period), `TypeError` ends with `.` (period), but the docstring example shows no trailing period

**File:** `/data/workspace/kais-hermes-skills/plugins/pipeline_state/transition_schema.py:159-183`

**Issue:** The error messages at lines 162-164, 169-171, and 181-183 all end with `).` (close-paren + period). The docstring at lines 131-135 describes the suffix without the trailing period. This is a cosmetic inconsistency — grep audits for `(TRANS-01 strict enum ...)` will still match because the suffix text matches up to the close-paren.

**Fix:** Strip the trailing period from the error messages, OR update the docstring to include it. Low priority.

### IN-02: `p13_delivery.py` constructs variables `mt_json` / `as_json` / `ci_json` (lines 99-101) that are never used — the goal builder uses `.context(...)` with the raw dicts instead

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p13_delivery.py:99-101`

**Issue:** Lines 99-101:
```python
mt_json = json.dumps(master_timeline, ensure_ascii=False)
as_json = json.dumps(audio_stems, ensure_ascii=False)
ci_json = json.dumps(color_intent, ensure_ascii=False)
```

These three variables are computed but never referenced — the goal builder at line 109 passes the raw dicts (`master_timeline=master_timeline, audio_stems=audio_stems, ...`) into `.context()`, which does its own JSON serialization. Dead code.

This is a pre-existing issue (the pattern is mirrored from p09 lines 378-383, where the same dead `*_json` variables are also computed but unused). Phase 74 introduced p13's `_EDITOR_TRANSITION_EXECUTION_INSTRUCTION` but did not introduce this dead-code pattern — it was already there.

**Fix:** Remove the three dead assignments.

### IN-03: `e-konte-format.md` Layer 5 schema extension uses `cut_transition_type: "dissolve_from_prev"` as a DEPRECATED alias example — value `"dissolve_from_prev"` is not in any documented enum

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/references/e-konte-format.md:130, 360`

**Issue:** Line 130 shows `cut_transition_type: "hard_cut"` as the legacy alias, but line 360 (in the Output Schema example) shows `cut_transition_type: "dissolve_from_prev"`. The 4-value legacy enum documented at line 145 is `hard_cut / dissolve / wipe / fade` — `"dissolve_from_prev"` is NOT in that enum. This is an example-only inconsistency (the field is documented as deprecated so the exact value is not load-bearing), but it could confuse readers about what values the legacy field accepted.

**Fix:** Change line 360 to `cut_transition_type: "dissolve"` to match the documented legacy enum.

### IN-04: `transition-design.md` has a stray `*Athina Rachel Tsangari*` film citation without bold/italic director-name consistency

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/references/transition-design.md:105`

**Issue:** Line 105 cites `*Athina Rachel Tsangari* uses them in *Attenberg* (2010)` — Athina Rachel Tsangari's name is italicized (treated as a film title by markdown convention) when it should be plain text (it's a person's name, not a film title). All other director names in the file are plain text (e.g., `*La La Land* (2016, Damien Chazelle)` — Damien Chazelle is plain). Minor citation-style inconsistency.

**Fix:** Change `*Athina Rachel Tsangari* uses them` → `Athina Rachel Tsangari uses them`.

### IN-05: `ltx-flf-iclora-validation.md` correctly uses `<operator fills>` placeholders — verified template discipline

**File:** `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/ltx-flf-iclora-validation.md`

**Issue:** None — this is a positive verification. The ref correctly uses `<operator fills>` / `<operator fills at validation close>` / `<YYYY-MM>` / `<operator fills YYYY-MM-DD>` placeholders throughout (lines 5-6, 59-91, 103, 114-116). No PII, no secrets, no hardcoded validation results. TRANS-07 research-scope lock (operator runs shots, phase produces template only) is correctly observed. No fix needed.

---

_Reviewed: 2026-07-10T00:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
