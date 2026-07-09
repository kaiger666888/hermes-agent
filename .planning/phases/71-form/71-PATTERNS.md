# Phase 71: FORM - Pattern Map

**Mapped:** 2026-07-09
**Files analyzed:** 28 (3 Plan A code/doc + 5 MSR_FC doc fixes + 2 new tests + 15 Plan B SKILL.md + 1 Plan C ref + 1 Plan C test + 1 Plan C cinematographer edit + 1 _eval dir)
**Analogs found:** 26 / 28 (2 with no analog: `horizontal-screen-framing.md` is a mirror-by-spec, `_eval/form_factor_step14/` sample frames are greenfield fixtures)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `kais-hermes-skills/plugins/pipeline_state/store.py` (MODIFY +1 field) | model | CRUD | `store.py` itself (v9.0 P38 additive-field precedent; `phases` field default) | exact |
| `kais-hermes-skills/skills/kais-movie-pipeline/SKILL.md:40` (MODIFY) | config/skill-body | request-response | same file's Step 0 additive section (lines 71-120) | exact |
| `kais-hermes-skills/skills/movie-experts/cinematographer/references/horizontal-screen-framing.md` (NEW) | reference-doc | file-I/O | `cinematographer/references/vertical-screen-framing.md` (twin) | exact-mirror |
| `kais-hermes-skills/skills/kais-movie-pipeline/templates/ltx_msr_batch_render.py` (MODIFY argparse) | utility/script | batch | same file `--msr-fc` argparse at line 613-616 | exact |
| 5 MSR_FC=17→41 doc locations (MODIFY) | documentation | file-I/O | `ltx_msr_batch_render.py:67` (canonical `MSR_FC_DEFAULT = 41`) | exact |
| `kais-hermes-skills/skills/kais-movie-pipeline/tests/test_form_factor.py` (NEW) | test | CRUD | `tests/test_p09_unit.py` (delegate spy + captured["goal"] assertion) + `conftest.py:tmp_state_store` fixture | exact |
| `kais-hermes-skills/skills/movie-experts/cinematographer/SKILL.md` (MODIFY Step 3 + Tier 1 section) | skill-body | request-response | `cinematographer/SKILL.md:178` (current Step 3 hardcoded vertical) | exact |
| 15 active movie-expert SKILL.md files (MODIFY append `## Form Factor Adaptation`) | skill-body | request-response | `_shared/SKILL-LAYOUT.md` H2-section convention + v9.0 additive pattern (Step 0 in kais-movie-pipeline/SKILL.md) | role-match |
| `kais-hermes-skills/skills/kais-movie-pipeline/references/platform-master-slicing.md` (MODIFY +4-cell matrix section) | reference-doc | request-response | same file's D1-D4 decision-point sections (lines 60-166) | exact |
| `kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py` (MODIFY — add `_FORM_FACTOR_INSTRUCTION`) | service/orchestration | event-driven | `p09_shot_breakdown.py:51 _CROSS_CUTTING_INSTRUCTION` + `p04_character_design.py:48 _GROWTH_CHAIN_INSTRUCTION` | exact |
| `kais-hermes-skills/skills/kais-movie-pipeline/tests/test_step14_reframe_matrix.py` (NEW) | test | request-response | `tests/test_p09_unit.py` (goal-content assertion pattern) | role-match |
| `kais-hermes-skills/_eval/form_factor_step14/` (NEW dir, 8 sample frames) | fixture | file-I/O | `_eval/` sibling dirs (none read in detail — check at execution time) | role-match |
| `.planning/phases/71-form/71-smoke.sh` (NEW — bash smoke runner) | test/smoke | request-response | `.planning/phases/70-foundation-audit/70-smoke.sh` | exact |

## Pattern Assignments

### `plugins/pipeline_state/store.py` (model, CRUD — +1 dataclass field)

**Analog:** `store.py` itself (the `phases` / `current_phase_id` / `trace_id` fields all use the same additive-with-default pattern)

**Imports pattern** (lines 29-38):
```python
from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
```
**Plan A adds:** `from typing import Literal` after the `from dataclasses` import.

**Dataclass field-addition pattern** (lines 58-74 current):
```python
@dataclass
class PipelineState:
    episode: str
    phases: dict[str, dict] = field(default_factory=dict)
    current_phase_id: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    last_resumed_at: str | None = None
    trace_id: str | None = None
    # Plan A appends:
    # form_factor: Literal["landscape", "portrait"] = "portrait"  # NEW v14.0 (FORM-01)
```

**Auto-whitelist pattern** (line 88 — NO CHANGE REQUIRED):
```python
_STATE_FIELDS = frozenset(PipelineState.__dataclass_fields__.keys())
```
Adding `form_factor` to the dataclass automatically extends `_STATE_FIELDS`. The forward-compat filter at line 183 (`filtered = {k: v for k, v in raw.items() if k in _STATE_FIELDS}`) accepts the new key from new JSON AND silently drops it when absent from old JSON — falling back to the `"portrait"` default via the dataclass constructor. **Zero migration script needed.**

---

### `skills/kais-movie-pipeline/SKILL.md:40` (config/skill-body, request-response — drop hardcoded form assumption)

**Analog:** same file's Step 0 additive section (lines 71-120) — established the "additive section that doesn't renumber V8.6 13 steps" pattern.

**Current text** (line 40):
```markdown
**Pipeline form:** Chinese-market 短剧 / 微电影 (vertical 9:16, 60–180s per episode, 10–30 episodes typical). All 15 movie-experts assume this form; this orchestration skill does not override form-level assumptions.
```

**Plan A edit direction:** Replace "All 15 movie-experts assume this form" with form_factor dispatch prose:
```markdown
**Pipeline form:** `PipelineState.form_factor` declares the project form (`portrait` 9:16 default | `landscape` 16:9). Each movie-expert reads `form_factor` from the delegate_task context and applies its `## Form Factor Adaptation` rules.
```

---

### `skills/movie-experts/cinematographer/references/horizontal-screen-framing.md` (reference-doc, file-I/O — NEW)

**Analog (twin):** `cinematographer/references/vertical-screen-framing.md` (199 lines, full read)

**Header / copyright block to mirror** (vertical ref lines 1-6):
```markdown
# Vertical Screen Framing — 9:16 短剧 Framing Rules + Per-Platform Divergence

**Source:** CN 平台 公开 framing 统计(...); TikTok Creator Academy public guides; ...
**Copyright:** Fair Use — framing rules paraphrased from public creator guides + ...
**Last-verified:** 2026-06-15
verified_date: 2026-06
```
**Horizontal twin substitutes:** Blain Brown *Cinematography: Theory and Practice* (3rd ed, 2016); Gustavo Mercado *The Filmmaker's Eye* (2010); Bordwell & Thompson *Film Art* (11th ed, 2020); Netflix Timed Text Style Guide; YouTube Creator Academy horizontal guides.

**5-section structure to mirror EXACTLY (FORM-03 literal success criteria):**
1. `## 16:9 Power Points` — standard rule-of-thirds (1/3,1/3)/(2/3,1/3)/(1/3,2/3)/(2/3,2/3) + golden ratio; per-shot-scale table EWS→BCU
2. `## Headroom 标准` — 8-15% horizontal headroom; lead room (nose room) for profiles
3. `## 字幕 Safe Area` — 3-zone horizontal (top 0-10% / center 10-80% / bottom 80-100%)
4. `## Per-Platform Framing Divergence` — YouTube vs B站长 vs 抖音横屏 vs Netflix
5. `## Horizontal Camera Move 修正` — pan/tracking/dolly preferred; tilt de-emphasized

Plus mirrored trailing sections: `## Horizontal Framing JSON Schema`, `## Anti-Patterns`, `## Glossary`.

**Per-section content depth** — see RESEARCH.md §horizontal-screen-framing.md Authoring Spec for the full table with film citations (Grand Budapest Hotel, Revenant, 1917, Drive, Shining).

---

### `skills/kais-movie-pipeline/templates/ltx_msr_batch_render.py` (utility/script, batch — +`--form-factor` switch)

**Analog:** same file's `--msr-fc` argparse (lines 613-616):
```python
parser.add_argument(
    "--msr-fc", type=int, default=MSR_FC_DEFAULT,
    help="MSR conditioning frame count (default: 41, per A/B test. Plugin allows [17, 25, 33, 41])",
)
```
And `--width` / `--height` (lines 605-612):
```python
parser.add_argument(
    "--width", type=int, default=1280,
    help="Output video width (default: 1280 for 16:9)",
)
parser.add_argument(
    "--height", type=int, default=704,
    help="Output video height (default: 704 for 16:9)",
)
```

**Plan A adds near MSR_FC_DEFAULT (line 67 area):**
```python
_FORM_FACTOR_RESOLUTION = {
    "portrait": (704, 1280),    # width, height — 9:16 vertical 短剧
    "landscape": (1280, 704),   # current template default — 16:9
}
```

**Plan A adds to `parse_args()` (after `--height`):**
```python
parser.add_argument(
    "--form-factor", choices=["landscape", "portrait"], default=None,
    help="Form factor override. If set, derives --width/--height defaults "
         "from form factor unless explicitly overridden. (FORM-01 v14.0)",
)
```

**Plan A adds to `main()` before workflow build loop:** resolution derivation that does NOT override explicit `--width`/`--height` operator flags (see RESEARCH.md §Code Examples for the exact guard logic).

---

### 5 MSR_FC=17→41 doc locations (documentation, file-I/O — doc sweep)

**Canonical source of truth:** `templates/ltx_msr_batch_render.py:67` — `MSR_FC_DEFAULT = 41  # Default conditioning frames (was 17 before A/B test)`

**Files to sweep** (from RESEARCH.md §MSR_FC=17→41 Propagation Audit, verified grep):

| File | Line | Action |
|------|------|--------|
| `skills/kais-movie-pipeline/SKILL.md` | 446 | FIX `MSR_FC=17` → 41 |
| `skills/kais-movie-pipeline/references/p11-single-shot-orchestration.md` | 75, 85 | FIX both (recompute num_frames example at line 85) |
| `skills/kais-movie-pipeline/references/post-production-audit.md` | 156 | FIX → 41 |
| `skills/kais-movie-pipeline/references/ltx-msr-workflow-spec.md` | 121 | FIX `Trim MSR_FC=17` → 41 |
| `skills/kais-movie-pipeline/references/ltx-msr-single-shot-prompt-construction.md` | 1602, 1610, 1616, 1618 | **LEAVE** — this is the A/B test transition historical narrative (correct as-is) |

---

### `skills/kais-movie-pipeline/tests/test_form_factor.py` (test, CRUD — NEW)

**Analog 1:** `tests/test_p09_unit.py` — delegate spy + `captured["goal"]` assertion convention

**Delegate spy pattern** (test_p09_unit.py lines 56-63):
```python
def _make_delegate_spy(captured: dict):
    def _mock(goal: str, context: str, toolsets: list[str]) -> dict:
        captured["goal"] = goal
        captured["context"] = context
        captured["toolsets"] = toolsets
        return {"summary": _ok_summary()}
    return _mock
```

**Goal-content assertion pattern** (test_p09_unit.py lines 159-184):
```python
def test_p09_goal_includes_cross_cutting_injection_instruction():
    captured: dict = {}
    p09.run(..., delegate_task=_make_delegate_spy(captured), ...)
    assert "CROSS-CUTTING PARAMETER INJECTION" in captured["goal"]
    assert "character_refs" in captured["goal"]
    # ... one assert per MUST keyword
```
**Plan A XCUT-02 test mirrors this pattern:**
```python
def test_p09_goal_includes_form_factor_instruction():
    captured: dict = {}
    p09.run(..., delegate_task=_make_delegate_spy(captured), ...)
    assert "form_factor" in captured["goal"]
    assert "MUST read form_factor" in captured["goal"]
```

**Analog 2:** `tests/conftest.py:tmp_state_store` fixture (lines 104-111) — for backward-compat round-trip test:
```python
@pytest.fixture
def tmp_state_store(tmp_path):
    from plugins.pipeline_state.store import PipelineStateStore
    workdir = str(tmp_path)
    store = PipelineStateStore(workdir)
    return store, workdir
```
**Plan A FORM-01 backward-compat test uses this fixture directly:**
```python
def test_old_episode_json_without_form_factor_loads_as_portrait(tmp_state_store):
    store, workdir = tmp_state_store
    # write pre-v14.0 JSON (no form_factor key)
    # store.load() → state.form_factor == "portrait" (dataclass default)
```

**sys.path bootstrap pattern** (test_p09_unit.py lines 27-29):
```python
_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))
```

---

### `skills/movie-experts/cinematographer/SKILL.md` (skill-body, request-response — Step 3 dispatch + Tier 1 section)

**Analog:** same file's Step 3 (line 178) — current hardcoded vertical dispatch:
```markdown
3. **Composition per Shot** — Apply vertical 9:16 power points + headroom per shot scale
```
**Plan C edit direction (branch on form_factor):**
```markdown
3. **Composition per Shot** — Branch on `form_factor` from pipeline_state context:
   - `portrait`: load [`references/vertical-screen-framing.md`](./references/vertical-screen-framing.md); apply 9:16 power points (1/3, 1/4)
   - `landscape`: load [`references/horizontal-screen-framing.md`](./references/horizontal-screen-framing.md); apply 16:9 rule-of-thirds (1/3, 1/3)
```

**Tier 1 `## Form Factor Adaptation` section** — append at end of body (after §Cross-References), do NOT mutate frontmatter (FOUND-08 freeze). Depth: ~15-30 lines with dual-branch power points / headroom / subtitle safe area / camera-move priority per RESEARCH.md tier table.

---

### 15 active movie-expert SKILL.md files (skill-body, request-response — Plan B per-tier append)

**Analog:** `_shared/SKILL-LAYOUT.md` H2-section convention (per RESEARCH.md §Project Constraints, frontmatter is FROZEN — body append only). Also mirrors the Step 0 additive section pattern in `kais-movie-pipeline/SKILL.md:71-120` (additive content that doesn't renumber existing structure).

**Tier 1 (form-critical, ~15-30 lines dual-branch):** `cinematographer`, `visual_executor`, `editor`, `character_designer` (4 files)
**Tier 2 (form-aware, ~5-10 lines dual-branch):** `continuity_auditor`, `hook_retention`, `screenplay`, `prompt_injector`, `compliance_gate` (5 files)
**Tier 3 (form-agnostic, ~3-line stub):** `style_genome`, `script_auditor`, `creative_source`, `colorist`, `theory_critic`, `audio_pipeline` (6 files)

**Tier 3 stub template (use verbatim per CONTEXT.md decision):**
```markdown
## Form Factor Adaptation

This expert is form-agnostic; no form-specific rules required.
```

**Per-tier commit granularity:** 3 commits in Plan B (Tier 1 / Tier 2 / Tier 3 separately).

**CRITICAL — deprecated expert stubs to NOT patch** (per RESEARCH.md §Pitfall 3): `drawer`, `scene_builder`, `storyboard_designer`, `performer`, `animator`, `voicer`, `composer`, `foley`, `mixer`, `spatial_audio`, `lip_sync` are 654-byte redirect stubs (`status: merged_into`). Patch only the 15 canonical active experts listed above.

---

### `skills/kais-movie-pipeline/references/platform-master-slicing.md` (reference-doc, request-response — +4-cell matrix section)

**Analog:** same file's D1 section (lines 60-82) — current vertical-master-only aspect-ratio adaptation algorithm.

**Current D1 algorithm excerpt** (lines 66-75):
```markdown
**Algorithm:**
- 从 `master.mp4` 提取 native aspect(典型 16:9 master 或 9:16 master,取决于 Step 12 composition 输出)。
- 对 9:16 vertical variants:若 master 是 16:9,执行 center-crop;safe-area = top 2/3 + bottom 1/3 的关键信息分布...
- 对 16:9 horizontal variants:若 master 是 9:16,执行 letterbox(上下黑边)或 reframe...
```

**Plan C additive section** — insert as a new H2 AFTER the existing D1-D4 decision-point block (after line ~167, before §variants[] Schema). Content: the 4-cell matrix table from RESEARCH.md §Code Examples (portrait→portrait / landscape→landscape / portrait→landscape / landscape→portrait) + saliency-scan requirement for Cell D. **DO NOT rewrite D1** — high regression risk (per CONTEXT.md locked decision).

**Saliency-scan contract** (already in vertical-master D1 lines 72-75): extend to Cell D explicitly. Implementation choice (ffmpeg `cropdetect` zero-dep default vs GLM-4.6V semantic scan) deferred to plan-phase per CONTEXT.md.

---

### `skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py` (service/orchestration, event-driven — +`_FORM_FACTOR_INSTRUCTION`)

**Analog 1 (constant definition):** same file's `_CROSS_CUTTING_INSTRUCTION` (lines 51-70):
```python
_CROSS_CUTTING_INSTRUCTION = (
    "CROSS-CUTTING PARAMETER INJECTION (mandatory — every shot entry MUST have):\n"
    "1. character_refs: array of {name, turnaround_path, role} — ...\n"
    "2. scene_ref: path to the angle-matched scene reference image from p08.\n"
    "3. style_prefix: from style-vector (p07) — injected verbatim into each shot.\n"
    "4. color_guidance: from color-intent (p07) — CxSxZ color tokens for the shot.\n"
    "5. physics_state: enum describing the reference image's physical state — ...\n"
    "If any of these cannot be resolved, the shot entry MUST set the field to null ..."
)
```

**Analog 2 (alternative style):** `p04_character_design.py:48-70` — three sibling constants (`_GROWTH_CHAIN_INSTRUCTION`, `_SCENE_FITTING_INSTRUCTION`, `_FOUR_D_INSTRUCTION`), each a single-paragraph string with MUST/MANDATORY keyword.

**Plan A XCUT-02 adds** (near other `_INSTRUCTION` constants in p09, before the `run()` function):
```python
_FORM_FACTOR_INSTRUCTION = (
    "FORM FACTOR ADAPTATION (mandatory — MUST read form_factor from pipeline_state "
    "and propagate it to every shot_intent.power_point and framing decision): "
    "portrait uses vertical power points (1/3, 1/4); landscape uses horizontal "
    "rule-of-thirds (1/3, 1/3). See cinematographer/references/{vertical,horizontal}-screen-framing.md."
)
```

**Injection into goal f-string** — mirror the `.task(steps=[...])` block at p09 lines 348-359:
```python
.task(steps=[
    "Load both experts via skill_view",
    "cinematographer decomposes each selected scene into shot list ...",
    f"{_DURATION_DECISION_INSTRUCTION}",
    f"{_CAMERA_MOVE_SELECTION_INSTRUCTION}",
    f"{_PACING_SHOTTYPE_INSTRUCTION}",
    f"{_LTX_PROMPT_WRITING_GUIDE}",
    f"{_FORM_FACTOR_INSTRUCTION}",   # NEW Plan A XCUT-02
    ...
])
```
And add a constraint line in `.constraints([...])` at p09 lines 376-384 with MUST keyword.

**Why both .task() and .constraints() (META-RULE X-2):** Subagents see only the `goal` string. The `.task()` block lists execution steps; the `.constraints()` block enforces MUST rules. Both are scanned by `count_constraints()` per `references/prompt-design-standards.md`. If `_FORM_FACTOR_INSTRUCTION` lives only in `.task()`, it's advisory; adding a MUST constraint makes it enforceable. Test via `test_p09_goal_includes_form_factor_instruction` (see test pattern above).

---

### `skills/kais-movie-pipeline/tests/test_step14_reframe_matrix.py` (test, request-response — NEW)

**Analog:** `tests/test_p09_unit.py` goal-content assertion pattern (same as test_form_factor.py above). Additionally, the reframe-math unit tests (crop coordinates per cell) use plain pytest functions with no mocks — just `assert cell_a_passthrough(...) == expected`.

---

### `kais-hermes-skills/_eval/form_factor_step14/` (fixture, file-I/O — NEW dir with 8 sample frames)

**Analog:** `_eval/` sibling directories under `skills/kais-movie-pipeline/` (convention: one dir per eval dimension, before/after sample pairs). Planner should `ls _eval/` at execution time to enumerate existing siblings and match the directory-naming + sample-file-naming convention.

**8 sample frames (4 cells × before/after)** — exact fixtures are Claude's Discretion per CONTEXT.md (use existing project assets where possible).

---

### `.planning/phases/71-form/71-smoke.sh` (test/smoke, request-response — NEW bash runner)

**Analog:** `.planning/phases/70-foundation-audit/70-smoke.sh` (full read, 80 lines)

**Smoke script skeleton to mirror** (70-smoke.sh lines 1-18):
```bash
#!/usr/bin/env bash
# Phase 71 FORM smoke runner — N assertions. Usage: bash .planning/phases/71-form/71-smoke.sh
set -euo pipefail
# Exits 0 only if all sub-claims pass. Hard-fails on first error.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
KHS_ROOT="/data/workspace/kais-hermes-skills"

echo "Phase 71 FORM smoke — N assertions"
echo "Repo root: $REPO_ROOT"
echo ""
```

**Per-assertion block pattern** (70-smoke.sh lines 20-25):
```bash
# XCUT-XXa: <description>
if [ ! -f "$TARGET_FILE" ]; then
    echo "FAIL: XCUT-XXa — <reason>"
    exit 1
fi
echo "OK: XCUT-XXa — <success>"
```

**Grep-count assertion pattern** (70-smoke.sh lines 28-33):
```bash
COUNT=$(grep -c 'skills/.*SKILL\.md' "$INVENTORY" || true)
if [ "$COUNT" -lt 6 ]; then
    echo "FAIL: XCUT-XXb — expected >=6, got $COUNT"
    exit 1
fi
echo "OK: XCUT-XXb — $COUNT entries (>= 6)"
```

**Phase 71 smoke assertions to draft** (from RESEARCH.md §Validation Architecture Test Map):
- XCUT-F02: `grep -l "## Form Factor Adaptation" $KHS_ROOT/skills/movie-experts/{15 experts}/SKILL.md | wc -l == 15`
- XCUT-F03: `grep -c "^## " $KHS_ROOT/skills/movie-experts/cinematographer/references/horizontal-screen-framing.md` returns `>= 5`
- XCUT-F04: `grep -c "portrait → portrait\|landscape → landscape\|portrait → landscape\|landscape → portrait" $KHS_ROOT/skills/kais-movie-pipeline/references/platform-master-slicing.md == 4`
- XCUT-F05: `grep -rn "MSR_FC=17" $KHS_ROOT/skills/kais-movie-pipeline/ | grep -v "must be updated\|historical\|was 17"` returns 0 lines
- XCUT-F01: `python -c "import sys; sys.path.insert(0,'$KHS_ROOT/plugins/pipeline_state'); from store import PipelineState; import dataclasses; assert 'form_factor' in {f.name for f in dataclasses.fields(PipelineState)}"`

---

## Shared Patterns

### Schema Migration with Defaults (FORM-01)
**Source:** `plugins/pipeline_state/store.py` lines 58-88
**Apply to:** Any new PipelineState field addition
**Core invariant:** `field(default=...)` + `_STATE_FIELDS = frozenset(PipelineState.__dataclass_fields__.keys())` auto-derivation = zero migration script. Verified safe.

### `_INSTRUCTION` Constant Injection (META-RULE X-2 / XCUT-02)
**Source:** `pipeline/phases/p09_shot_breakdown.py:51-70` (`_CROSS_CUTTING_INSTRUCTION`) + `pipeline/phases/p04_character_design.py:48-70` (3 sibling constants)
**Apply to:** Every MUST added to a SKILL.md that the subagent must act on
**Core invariant:** (1) Define `_SOME_INSTRUCTION = "..."` constant with MUST/MANDATORY keyword at module top; (2) inject via `.task(steps=[f"{_SOME_INSTRUCTION}", ...])` AND `.constraints(["MUST ..."])`; (3) assert via `captured["goal"]` test. Without all three, the rule is invisible to the subagent at runtime.

### Ref Twin Authoring (FORM-03)
**Source:** `cinematographer/references/vertical-screen-framing.md` (199 lines, full 5-section structure)
**Apply to:** `horizontal-screen-framing.md` (NEW)
**Core invariant:** Mirror section structure EXACTLY (5 H2 sections in same order) + same trailing sections (JSON Schema / Anti-Patterns / Glossary) + same header block format (Source / Copyright / Last-verified / verified_date). Content is Claude's Discretion but depth must match.

### SKILL.md Body Append (FOUND-08 frontmatter freeze)
**Source:** `_shared/SKILL-LAYOUT.md` + CLAUDE.md §Skill File Conventions
**Apply to:** All 15 Plan B SKILL.md edits
**Core invariant:** Frontmatter (name/description/tags/related_skills/expert_id/metrics) is FROZEN byte-identical. Only append a new `## Form Factor Adaptation` H2 section to the body. Insert location: end of body (after §Cross-References or equivalent trailing section) to minimize diff risk.

### Goal-Content Test Assertion
**Source:** `tests/test_p09_unit.py:56-63, 159-184`
**Apply to:** All XCUT-02 unit tests in `test_form_factor.py`
**Core invariant:** `_make_delegate_spy(captured)` captures goal/context/toolsets → `assert "MUST keyword" in captured["goal"]` per MUST rule. One test function per MUST keyword.

### Smoke Script grep Assertions
**Source:** `.planning/phases/70-foundation-audit/70-smoke.sh`
**Apply to:** `.planning/phases/71-form/71-smoke.sh`
**Core invariant:** `set -euo pipefail` + REPO_ROOT/KHS_ROOT resolution via `BASH_SOURCE` + per-assertion block (grep-count check or file-existence check) + final `echo "ALL N ASSERTIONS PASSED"`. Exits non-zero on first failure.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `horizontal-screen-framing.md` (content body) | reference-doc | file-I/O | Twin-by-spec (`vertical-screen-framing.md` IS the analog for structure, but the CONTENT has no existing source — researcher cited `[ASSUMED]` film examples). Planner uses RESEARCH.md §horizontal-screen-framing.md Authoring Spec table directly. |
| `_eval/form_factor_step14/` 8 sample frames | fixture | file-I/O | Greenfield fixtures; no existing `_eval/` dir was read in detail. Planner should `ls _eval/` at execution time to match sibling conventions. |

## Metadata

**Analog search scope:**
- `/data/workspace/kais-hermes-skills/plugins/pipeline_state/store.py` (full read, 268 lines)
- `/data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/references/vertical-screen-framing.md` (full read, 199 lines)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/platform-master-slicing.md` (full read, 347 lines)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/templates/ltx_msr_batch_render.py` (targeted reads: lines 1-120, 595-675)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p09_unit.py` (full read, 259 lines)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/conftest.py` (full read, 215 lines)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py` (full read, 471 lines)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p04_character_design.py` (targeted read: lines 1-120)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/SKILL.md` (targeted read: lines 1-120)
- `/data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/SKILL.md` (targeted read: lines 170-199; grep for section structure)
- `/data/workspace/hermes-agent/.planning/phases/70-foundation-audit/70-smoke.sh` (full read, 80 lines)
- Grep for `_INSTRUCTION = ` across `pipeline/phases/` (8 hits across 3 files)

**Files scanned:** 11 primary + 8 grep hits
**Pattern extraction date:** 2026-07-09
