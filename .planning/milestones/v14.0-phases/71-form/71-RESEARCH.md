# Phase 71: FORM - Research

**Researched:** 2026-07-09
**Domain:** kais-movie-pipeline `form_factor` parameterization (landscape 16:9 / portrait 9:16 dual-default) — foundational v14.0 track
**Confidence:** HIGH (all code claims verified against live kais-hermes-skills repo at HEAD `d9620369e48eec51c31ee72ac8827c288eaccf71`; all CONTEXT.md decisions cross-checked against actual file contents)

## Summary

Phase 71 (FORM) parameterizes the kais-movie-pipeline so users can author projects in either landscape 16:9 or portrait 9:16 form factor. The pipeline reads `form_factor` as a first-class project-level meta on `PipelineState`, each of the 15 active DAG experts emits form-aware creative rules instead of hardcoded `9:16` assumptions, a new `horizontal-screen-framing.md` ref mirrors the existing vertical-only ref, Step 14 platform-master-slicing gains an explicit 4-cell reframe matrix, and a stale `MSR_FC=17` default is corrected to `41` across the docs that still carry it.

The work is **low-risk, additive schema migration** at the Python layer (`PipelineState.form_factor` with a `"portrait"` default that preserves all existing 短剧 behavior) plus **content authoring** at the markdown layer (15 SKILL.md `## Form Factor Adaptation` sections + 1 new ref + 1 ref extension + incidental doc fixes). The single hardest piece is authoring `horizontal-screen-framing.md` with the same 5-section depth as its vertical twin (power points / headroom / subtitle safe area / shot scale distribution / eye-trace region) — this ref is load-bearing because PITFALL F-1 documents that 16:9 is NOT "just resize 9:16"; multiple creative assumptions (power points, headroom, subtitle zones, camera-move priority, shot-scale distribution, eye-trace) differ between the two forms, and a naive width/height swap silently regresses landscape output quality.

**Primary recommendation:** Three plans in order — Plan A (Foundation: dataclass + new ref + LTX template resolution switch + MSR_FC doc sweep), Plan B (15 SKILL.md `## Form Factor Adaptation` sections tiered by form-criticality), Plan C (Step 14 4-cell reframe matrix + cinematographer Step 3 dispatch + unit tests). Phase 71 touches the kais-hermes-skills repo ONLY; hermes-agent `.planning/` lineage bump is Phase 75.

**Critical research correction to CONTEXT.md:** the Tier 1/2/3 expert lists in CONTEXT.md contain **deprecated expert_ids** that must NOT be patched. The canonical 15 active DAG experts (verified against `04-MIGRATION-PATH.md §1.6` and live SKILL.md frontmatter) are: `hook_retention, creative_source, screenplay, script_auditor, character_designer, cinematographer, style_genome, prompt_injector, visual_executor, continuity_auditor, audio_pipeline, editor, colorist, compliance_gate, theory_critic`. `drawer`, `scene_builder`, `storyboard_designer`, `performer`, `animator`, `voicer`, `composer`, `foley`, `mixer`, `spatial_audio`, `lip_sync` are all DEPRECATED stubs (merged into `visual_executor` / `audio_pipeline` / `cinematographer` during v3.0 Phase 14-17). Patching their 654-byte redirect-stub SKILL.md files with a `## Form Factor Adaptation` section is wasted work and risks confusing the loader. The planner MUST remap CONTEXT.md's tier lists onto the 15 active experts before Plan B.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Field name:** `form_factor` on `PipelineState` dataclass in `kais-hermes-skills/plugins/pipeline_state/store.py`. Reject alternatives (`aspect_ratio`, `frame_orientation`).
- **Enum values:** `Literal["landscape", "portrait"]` — semantic-clean, dimensions derived downstream. REJECT verbose `"landscape_16_9"` / `"portrait_9:16"`.
- **Default:** `"portrait"` — backwards-compatible with all existing 短剧 projects.
- **Validation:** Pydantic `Literal["landscape", "portrait"]` strict enum. Unknown values raise `ValidationError` at parse time.
- **Plan shape:** 3 plans (Plan A Foundation, Plan B 15 SKILL.md patches, Plan C Step 14 matrix). NOT 1 mega-plan, NOT 5+ micro-plans.
- **Plan A scope:** PipelineState migration + `horizontal-screen-framing.md` authoring + LTX-MSR template `form_factor → resolution` switch + MSR_FC=17→41 doc fix at `kais-movie-pipeline/SKILL.md:446`.
- **Plan B tiering:** Tier 1 (form-critical, ~15-30 lines), Tier 2 (form-aware, ~5-10 lines), Tier 3 (form-agnostic, ~3-line stub). Per-tier commit granularity (3 commits).
- **Plan C scope:** 4-cell reframe matrix in `platform-master-slicing.md` + cinematographer Step 3 dispatch + unit tests. 8 sample-frame fixtures (4 cells × before/after).
- **horizontal-screen-framing.md structure:** Mirror `vertical-screen-framing.md` 5-section structure exactly (power points / headroom / subtitle safe area / shot scale distribution / eye-trace region).
- **Step 14 4-cell matrix:** portrait→portrait (pass-through), landscape→landscape (pass-through), portrait→landscape (letterbox OR reframe), landscape→portrait (center-crop + saliency scan). Existing vertical-master tests preserved.
- **MSR_FC fix scope:** Single-line at `SKILL.md:446` is the floor; Plan A executor greps for other MSR_FC=17 occurrences and fixes together.
- **Cinematographer Step 3 dispatch:** Step 3 (Composition per Shot) branches on `form_factor` and loads either `vertical-screen-framing.md` or `horizontal-screen-framing.md`.
- **Atomic commit granularity:** Per-tier commit in Plan B (3 commits). Plan A and Plan C commit per logical unit.

### Claude's Discretion
- Exact wording of each SKILL.md `## Form Factor Adaptation` section body (within tier depth guidelines).
- Choice of which 3 of the 15 active experts land in Tier 3 (form-agnostic) — researcher verifies each expert's output has zero frame-geometry dependence before classifying as Tier 3.
- Exact 8 sample-frame fixtures for Step 14 matrix verification (use existing project assets where possible).
- Test framework (pytest vs standalone script) — match existing `_eval/` conventions.
- Whether to add an integration test that runs one shot landscape + one portrait through cinematographer and checks different `power_point` values — RECOMMENDED per PITFALL F-1 mitigation #4.

### Deferred Ideas (OUT OF SCOPE)
- **FORM-06** per-shot form_factor override (anti-pattern — cross-shot consistency collapse risk). v15+.
- **FORM-07** auto-form_factor inference from screenplay (unreliable ~40% wrong). v15+.
- **LTX-MSR landscape-template evaluation:** whether landscape_16_9 needs different sigmas / sampler / cfg values. v15+ tuning concern. v14.0 reuses current LTX params with only `width`/`height` swapped.
- **Step 14 saliency-scan implementation details:** algorithm choice (GLM-4.6V vs OpenCV vs simple histogram) is plan-phase researcher's call.
- **15-expert production tuning post-rollout:** real-world data on which Tier 2/3 experts need promotion. v15+ via EVAL-06.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FORM-01 | User can specify project-level `form_factor` (`landscape` / `portrait`) via `PipelineState.form_factor`, defaulting to `portrait` | `## PipelineState Migration Mechanics` — exact dataclass diff; `_STATE_FIELDS` auto-derivation verified; old JSON round-trips without migration script |
| FORM-02 | Each of 15 active movie-expert skills has `## Form Factor Adaptation` section with dual-branch rules | `## 15-Expert Tier Classification` — canonical 15 active DAG experts enumerated with per-expert form-criticality rationale; CONTEXT.md tier lists corrected (deprecated experts removed) |
| FORM-03 | User can read `references/horizontal-screen-framing.md` for landscape creative rules mirroring `vertical-screen-framing.md` | `## horizontal-screen-framing.md Authoring Spec` — 5-section structure verified against live vertical ref; citation list with film examples per section |
| FORM-04 | Step 14 platform-master-slicing handles 4-cell reframe matrix without quality degradation | `## Step 14 4-Cell Matrix Insertion` — current D1 algorithm analyzed (lines 60-82); 4-cell extension patch sketch; saliency-scan requirement documented |
| FORM-05 | Stale `MSR_FC=17` corrected to canonical `MSR_FC=41` | `## MSR_FC=17→41 Propagation Audit` — grep found 5 doc locations with stale 17; template script already defaults to 41 (only docs need fixing) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

Phase 71 operates under the cross-repo topology: the project root CLAUDE.md is the hermes-agent one; kais-hermes-skills may have its own. Load-bearing directives for this phase:

- **Skill File Conventions:** `tags` / `related_skills` / `expert_id` / `metrics` frontmatter fields are mandatory and FROZEN for existing experts (FOUND-08). Plan B MUST NOT mutate frontmatter — only append a `## Form Factor Adaptation` H2 section to the SKILL.md body. `[VERIFIED: live SKILL.md frontmatter on 15 experts]`
- **Deliverable form:** "仅 skill 内容(refs + SKILL.md + eval scripts),不改 Hermes 核心 Python/JS 代码". Plan A's `PipelineState.form_factor` field is in `kais-hermes-skills/plugins/pipeline_state/store.py` — a skill-bundled plugin, NOT Hermes core. Compliant. `[VERIFIED: plugins/pipeline_state/ is under kais-hermes-skills, not hermes-agent]`
- **Compatibility:** "不破坏现有 14 专家的 expert_id 与 related_skills 协作图". Plan B MUST preserve all frontmatter byte-identical; only body appends allowed. `[CITED: CLAUDE.md Constraints section]`
- **Language:** SKILL.md bilingual (EN YAML structure + CN prose/examples). `horizontal-screen-framing.md` follows the same bilingual convention as `vertical-screen-framing.md`. `[CITED: CLAUDE.md Constraints section]`
- **Copyright:** All refs must cite source + copyright status; fair-use only. `horizontal-screen-framing.md` citations follow the `Source / Copyright / Last-verified` header block convention from `SKILL-LAYOUT.md`. `[CITED: CLAUDE.md Constraints + _shared/SKILL-LAYOUT.md lines 119-132]`

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| `form_factor` storage & validation | Python dataclass (`PipelineState`) | Pydantic `Literal` enum | Episode-level invariant; single source of truth; dataclass default preserves backward compat |
| `form_factor` propagation to experts | Pipeline orchestrator SKILL.md (kais-movie-pipeline) | Phase module `goal` f-string injection (PITFALL X-2) | Orchestrator reads state at boot and passes form_factor into each `delegate_task` context; META-RULE X-2 requires it also be in the goal f-string or subagents ignore it |
| Landscape framing creative rules | `horizontal-screen-framing.md` ref | Cinematographer Step 3 dispatch | Ref is the knowledge base; Step 3 branches on form_factor to load the right ref |
| Portrait framing creative rules | `vertical-screen-framing.md` ref (EXISTING — unchanged) | Cinematographer Step 3 dispatch | Already exists and is load-bearing for current 短剧 output; v14.0 does NOT modify it |
| LTX render resolution | `ltx_msr_batch_render.py` argparse (`--width`/`--height`) | `form_factor → resolution` mapping switch (NEW, Plan A) | Template already parameterizes width/height; switch derives them from form_factor so operator doesn't pass raw pixels |
| Step 14 reframe math | `platform-master-slicing.md` ref (D1 algorithm) | Editor + cinematographer consultation on reframe | Ref documents the 4-cell matrix; editor executes cuts; cinematographer consulted on saliency-driven reframe |
| Per-expert form adaptation rules | Each expert's `## Form Factor Adaptation` body section | — | Subagents read the section at delegation time; tier depth varies by form-criticality |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `dataclasses` | 3.11+ stdlib | `PipelineState` dataclass + `field(default=...)` | Already in use (`store.py:36`); no new dep `[VERIFIED: store.py:36]` |
| Python stdlib `typing.Literal` | 3.8+ stdlib | `form_factor: Literal["landscape", "portrait"]` strict enum | Already used in the codebase (CLAUDE.md type hints convention); zero new dep `[VERIFIED: Python 3.11+ target]` |
| Python stdlib `json` | stdlib | `PipelineStateStore.load/save` round-trip | Already in use (`store.py:31`) `[VERIFIED: store.py:31]` |
| pytest | (kais-hermes-skills has no root pyproject — tests run via direct invocation) | Unit tests for Step 14 reframe math + PipelineState migration | Existing convention (`skills/kais-movie-pipeline/tests/`) `[VERIFIED: tests/ dir with conftest.py]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ffmpeg (CLI) | already in stack | Step 14 reframe execution (center-crop / letterbox) | Plan C sample-frame fixture generation; not a Python dep |
| GLM-4.6V (via existing zai provider) | already wired | Saliency scan for landscape→portrait reframe cell | Plan C: detect primary-info zone before crop; MEMORY.md glm-5.2-only constraint is NOT violated (vision tool call, not a model switch) `[CITED: MEMORY.md feedback-glm-5-2-only.md]` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `Literal["landscape", "portrait"]` enum | `str` + runtime validator | Literal is stricter (Pydantic/mypy enforce at parse time); str is looser. Literal wins for the "no fuzzy matching, no warnings-and-continue" CONTEXT.md decision. |
| Pydantic BaseModel for PipelineState | stdlib `@dataclass` (current) | Current code uses dataclass; migrating to Pydantic is out of scope and would touch every consumer. Keep dataclass; add Literal type hint for validation at the `_STATE_FIELDS` filter boundary. |

**Installation:**
```bash
# Zero new packages. Phase 71 installs nothing.
# All dependencies are stdlib or already pinned.
```

**Version verification:** Not applicable — zero new packages. Existing stdlib (`dataclasses`, `typing`, `json`) and existing pytest conventions are reused.

## Package Legitimacy Audit

Phase 71 installs **zero external packages**. The Package Legitimacy Gate protocol is therefore satisfied trivially — no packages to audit. slopcheck is not invoked because there are no `npm install` / `pip install` / `cargo add` operations in any Plan A/B/C task.

*No packages removed, no packages flagged, no packages tagged `[ASSUMED]`.*

## Architecture Patterns

### System Architecture Diagram

```text
Episode JSON (.pipeline-state.json)
    │
    ▼
PipelineStateStore.load() ──▶ PipelineState(form_factor="portrait"|"landscape")
    │                              │
    │                              │ _STATE_FIELDS auto-derivation
    │                              │ (frozenset(__dataclass_fields__))
    │                              ▼
    │                         Forward-compat filter keeps known keys
    │                         (old JSON missing form_factor → defaults to "portrait")
    │
    ├─▶ kais-movie-pipeline/SKILL.md reads state.form_factor at boot
    │     └─▶ injects form_factor into each delegate_task context dict
    │           (PITFALL X-2: also inject as _FORM_FACTOR_INSTRUCTION in goal f-string)
    │
    ├─▶ cinematographer Step 3 (Composition per Shot)
    │     ├─▶ if form_factor == "portrait":  load vertical-screen-framing.md
    │     └─▶ if form_factor == "landscape": load horizontal-screen-framing.md  [NEW]
    │
    ├─▶ visual_executor (drawer sub-step) ── dreamina CLI image dims
    │     ├─▶ portrait:  1080×1920
    │     └─▶ landscape: 1920×1080
    │
    ├─▶ LTX-MSR render (ltx_msr_batch_render.py)
    │     ├─▶ portrait:  --width 704  --height 1280
    │     └─▶ landscape: --width 1280 --height 704  (current default)
    │
    └─▶ Step 14 platform-master-slicing (4-cell matrix) [NEW section in ref]
          ├─▶ portrait  → portrait:   pass-through (lossless)
          ├─▶ landscape → landscape:  pass-through (lossless)
          ├─▶ portrait  → landscape:  letterbox OR reframe from 9:16 keyframe
          └─▶ landscape → portrait:   center-crop + saliency scan
                                        (preserve top-2/3 primary info per existing ref line 74)
```

### Recommended Project Structure
```
kais-hermes-skills/
├── plugins/pipeline_state/
│   └── store.py                          # Plan A: +1 field on PipelineState
├── skills/
│   ├── kais-movie-pipeline/
│   │   ├── SKILL.md                      # Plan A: line 40 dispatch, line 446 MSR_FC fix
│   │   ├── references/
│   │   │   ├── platform-master-slicing.md # Plan C: +4-cell matrix section
│   │   │   ├── p11-single-shot-orchestration.md  # Plan A: MSR_FC=17→41 doc fix
│   │   │   ├── ltx-msr-single-shot-prompt-construction.md  # Plan A: MSR_FC doc fix
│   │   │   ├── post-production-audit.md  # Plan A: MSR_FC doc fix
│   │   │   └── ltx-msr-workflow-spec.md  # Plan A: MSR_FC doc fix (line 121)
│   │   ├── templates/
│   │   │   └── ltx_msr_batch_render.py   # Plan A: +form_factor→resolution switch helper
│   │   └── tests/
│   │       └── test_form_factor.py       # Plan C: NEW unit tests
│   └── movie-experts/
│       ├── cinematographer/
│       │   ├── SKILL.md                  # Plan B Tier 1 + Plan C Step 3 dispatch
│       │   └── references/
│       │       ├── vertical-screen-framing.md       # UNCHANGED (portrait authority)
│       │       └── horizontal-screen-framing.md     # Plan A: NEW (landscape authority)
│       ├── visual_executor/SKILL.md      # Plan B Tier 1 (drawer sub-step lives here)
│       ├── editor/SKILL.md               # Plan B Tier 1
│       ├── character_designer/SKILL.md   # Plan B Tier 1/2 (turnaround sheets)
│       ├── continuity_auditor/SKILL.md   # Plan B Tier 2
│       ├── hook_retention/SKILL.md       # Plan B Tier 2
│       ├── screenplay/SKILL.md           # Plan B Tier 2/3
│       ├── script_auditor/SKILL.md       # Plan B Tier 3
│       ├── creative_source/SKILL.md      # Plan B Tier 3
│       ├── style_genome/SKILL.md         # Plan B Tier 3
│       ├── prompt_injector/SKILL.md      # Plan B Tier 2 (prompt tokens differ)
│       ├── colorist/SKILL.md             # Plan B Tier 3 (color is form-agnostic)
│       ├── compliance_gate/SKILL.md      # Plan B Tier 2 (platform rules differ)
│       ├── theory_critic/SKILL.md        # Plan B Tier 3
│       └── audio_pipeline/SKILL.md       # Plan B Tier 3 (audio is form-agnostic)
└── (hermes-agent repo: NO CHANGES in Phase 71 — lineage bump is Phase 75)
```

### Pattern 1: Schema Migration with Defaults (FORM-01)
**What:** Add `form_factor` to `PipelineState` dataclass with a default value so old JSON round-trips cleanly.
**When:** Any episode-level field addition where backward compatibility is required.
**Example:**
```python
# Source: /data/workspace/kais-hermes-skills/plugins/pipeline_state/store.py lines 58-74 (verified)
# BEFORE (current):
from dataclasses import dataclass, field

@dataclass
class PipelineState:
    episode: str
    phases: dict[str, dict] = field(default_factory=dict)
    current_phase_id: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    last_resumed_at: str | None = None
    trace_id: str | None = None

# AFTER (Plan A):
from typing import Literal

@dataclass
class PipelineState:
    episode: str
    phases: dict[str, dict] = field(default_factory=dict)
    current_phase_id: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    last_resumed_at: str | None = None
    trace_id: str | None = None
    form_factor: Literal["landscape", "portrait"] = "portrait"  # NEW v14.0
```
**Why safe (verified):** `_STATE_FIELDS = frozenset(PipelineState.__dataclass_fields__.keys())` at `store.py:88` is computed at import time from the dataclass. Adding `form_factor` auto-extends the whitelist, so `load()`'s forward-compat filter (`store.py:183`: `filtered = {k: v for k, v in raw.items() if k in _STATE_FIELDS}`) accepts the new key from new JSON files AND silently drops it when absent from old JSON files (falling back to the `"portrait"` default via the dataclass constructor). No migration script needed. `[VERIFIED: store.py:88, 183]`

### Pattern 2: Ref Mirror (FORM-03)
**What:** When parameterizing a dimension that was previously hardcoded, author the alternative-case reference doc BEFORE editing the SKILL.md bodies that consume it.
**When:** Any "hardcoded assumption → parameterized switch" migration where the assumption encodes domain expertise (not just a config value).
**Why:** SKILL.md is the prompt; references are the knowledge base. If the landscape ref doesn't exist when cinematographer Step 3 dispatches to it, the subagent has no grounding and hallucinates landscape framing rules. PITFALL F-1 documents exactly this failure mode. `[CITED: PITFALLS.md F-1]`

### Pattern 3: Goal f-string Instruction Injection (XCUT-02 / META-RULE X-2)
**What:** Every MUST added to SKILL.md must also be encoded as a `_FORM_FACTOR_INSTRUCTION` constant injected into the relevant phase module's `goal` f-string, with a test asserting the keyword appears in `captured["goal"]`.
**When:** Any SKILL.md rule that requires the subagent to DO something with form_factor.
**Why:** Subagents see only the goal string passed to `delegate_task`. They never read SKILL.md at runtime. This is the #1 documented bug pattern (`PITFALLS.md X-2`). `[CITED: PITFALLS.md X-2]`
**Example (from existing test convention, `test_p09_unit.py:83`):**
```python
# Source: /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p09_unit.py lines 83-96 (verified)
_FORM_FACTOR_INSTRUCTION = (
    "MUST read form_factor from pipeline_state and propagate it to every "
    "shot_intent.power_point and framing decision. Landscape uses horizontal "
    "rule-of-thirds (1/3, 1/3); portrait uses vertical power points (1/3, 1/4)."
)

# In the phase module's goal builder:
goal = f"""
... existing goal text ...
[CONSTRAINTS]
{_FORM_FACTOR_INSTRUCTION}
"""

# Test asserts the instruction is present:
def test_goal_includes_form_factor_instruction():
    captured: dict = {}
    p09.run(..., delegate_task=_make_delegate_spy(captured))
    assert "form_factor" in captured["goal"]
    assert "MUST read form_factor" in captured["goal"]
```

### Anti-Patterns to Avoid
- **Per-shot form_factor override:** BREAKS LTX-MSR ICLoRA reference conditioning (requires consistent aspect ratio across reference frames). `form_factor` is episode-level ONLY. `[CITED: ARCHITECTURE.md Anti-Pattern 1]`
- **Naive width/height swap for landscape:** 16:9 ≠ "just resize 9:16". Power points, headroom, subtitle safe area, camera-move priority, shot-scale distribution, and eye-trace ALL differ. Must author `horizontal-screen-framing.md` first. `[CITED: PITFALLS.md F-1]`
- **Patching deprecated expert stubs:** `drawer`, `scene_builder`, `storyboard_designer`, `animator`, `voicer`, `composer`, etc. are 654-byte redirect stubs (`status: merged_into`). Patching them with `## Form Factor Adaptation` is wasted work — the loader follows the alias to the parent expert (`visual_executor` / `audio_pipeline` / `cinematographer`). Patch the PARENT. `[VERIFIED: drawer/SKILL.md is a 654-byte stub; visual_executor/SKILL.md is the 39KB parent]`
- **Assuming MSR_FC=17 is only at SKILL.md:446:** grep found 5 doc locations. Plan A must sweep all of them or the docs contradict each other. `[VERIFIED: grep results below]`

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| form_factor enum validation | Custom `if form_factor not in {"landscape", "portrait"}` checker | `typing.Literal["landscape", "portrait"]` on the dataclass field | Literal is enforced by Pydantic/mypy at parse time; runtime checker is advisory-only and easy to forget on new call sites |
| Step 14 reframe (center-crop / letterbox) | Custom Python image-processing code | ffmpeg CLI (`-vf "crop=W:H:X:Y"` / `-vf "pad=W:H:X:Y"`) | ffmpeg is already in the stack; battle-tested for aspect-ratio transforms; writing custom crop math risks off-by-one pixel errors |
| Saliency scan for landscape→portrait crop | Custom OpenCV histogram analysis | GLM-4.6V vision call (existing zai provider) or ffmpeg `cropdetect` filter | GLM-4.6V understands "primary subject" semantically; histogram analysis only finds brightness clusters. ffmpeg cropdetect is a zero-dep fallback. `[CITED: MEMORY.md glm-5.2-only.md — vision tool call allowed]` |
| form_factor → width/height mapping | Per-call-site `if/else` on form_factor | Single `_RESOLUTION_MAP = {"portrait": (704, 1280), "landscape": (1280, 704)}` helper in the template | Centralizes the mapping; avoids drift when resolution defaults change |

**Key insight:** Phase 71 is almost entirely content authoring (markdown) + one dataclass field. The "code" surface is tiny — the risk surface is in the creative-rule correctness of `horizontal-screen-framing.md` and the completeness of the 15-expert rollout. Don't over-engineer the Python; invest the effort in the ref depth and the SKILL.md section quality.

## 15-Expert Tier Classification

> **CRITICAL CORRECTION to CONTEXT.md:** The CONTEXT.md tier lists include deprecated expert_ids (`drawer`, `scene_builder`, `storyboard_designer`, `performer`, `composer`, `voicer`, `foley`, `mixer`, `spatial_audio`, `lip_sync`, `animator`). These are NOT active experts — they are 654-byte redirect stubs merged into `visual_executor` / `audio_pipeline` / `cinematographer` during v3.0 Phases 14-17. The canonical 15 active DAG experts (verified against `04-MIGRATION-PATH.md §1.6` and live SKILL.md frontmatter `status:` field) are listed below. The planner MUST remap CONTEXT.md's tier examples onto these 15 before Plan B execution.

### Verified Canonical 15 Active DAG Experts
`[VERIFIED: 04-MIGRATION-PATH.md §1.6 lines 200-214; live SKILL.md frontmatter on all 15 — none have status: deprecated]`

| # | expert_id | SKILL.md bytes | form-criticality | Tier | Rationale |
|---|-----------|----------------|------------------|------|-----------|
| 1 | `cinematographer` | 40780 | **form-critical** | Tier 1 | Owns power points, headroom, subtitle safe area, camera-move priority — ALL differ between forms. Step 3 dispatch is the primary integration point for FORM-03. 28 vertical/9:16 refs in SKILL.md. `[VERIFIED: SKILL.md lines 122, 134, 162, 166, 178, 256]` |
| 2 | `visual_executor` | 39608 | **form-critical** | Tier 1 | Owns dreamina image dims (1080×1920 vs 1920×1080) + LTX render resolution. The `drawer` and `animator` sub-steps live HERE (not in deprecated stubs). `[VERIFIED: visual_executor/SKILL.md sub_steps: [drawer, animator]]` |
| 3 | `editor` | 30364 | **form-critical** | Tier 1 | Owns cut rhythm baselines (Murch Rule of Six eye-trace ~27% vertical vs ~30% horizontal) + Step 14 reframe execution + FxRxT matrix. `[CITED: PITFALLS.md F-1 table row "Eye-trace"]` |
| 4 | `character_designer` | 32963 | **form-aware** | Tier 1 | Turnaround sheet layout (L1 anchor) differs by aspect ratio; character framing in vertical vs horizontal close-ups differs. `[ASSUMED — based on L1-L4 asset library spec]` |
| 5 | `continuity_auditor` | 11691 | **form-aware** | Tier 2 | 4-dim audit (face_identity / wardrobe_figure / color_temperature / scene_environment) is mostly form-agnostic, but axis compliance checks assume one frame geometry. `[VERIFIED: SKILL.md audit dimensions]` |
| 6 | `hook_retention` | 33917 | **form-aware** | Tier 2 | First-3-seconds hook assumes vertical phone-scroll dynamic; landscape YouTube/TV delivery has different hook structure (longer establishing, 5-10s ramp). `[CITED: PITFALLS.md F-3]` |
| 7 | `screenplay` | 35049 | **form-aware** | Tier 2 | Scene description prose is mostly form-agnostic, but blocking/staging notes implicitly assume frame geometry. Snyder beat sheet is form-neutral but scene visualization is not. `[ASSUMED]` |
| 8 | `prompt_injector` | 27883 | **form-aware** | Tier 2 | Translates camera-move intent → dreamina/Runway/Kling prompt tokens; token sets differ for vertical vs horizontal compositions (e.g., "vertical tilt up" vs "horizontal pan right"). `[VERIFIED: SKILL.md is the bilingual prompt translator]` |
| 9 | `compliance_gate` | 24042 | **form-aware** | Tier 2 | Platform rules differ by form (抖音 vertical vs horizontal have different cold-start thresholds per `platform-master-slicing.md` D2). `[VERIFIED: platform-master-slicing.md D2 cold-start rules]` |
| 10 | `style_genome` | 22517 | **form-agnostic** | Tier 3 | 5D style vector (color/composition/tone/rhythm/texture) is form-neutral; style-blending is cross-form. `[VERIFIED: SKILL.md 5D vector definition]` |
| 11 | `script_auditor` | 21678 | **form-agnostic** | Tier 3 | 5-dim critique (completion %, exposition dumps, etc.) evaluates screenplay text, not frame geometry. `[VERIFIED: SKILL.md is a text critic]` |
| 12 | `creative_source` | 24329 | **form-agnostic** | Tier 3 | Snowflake Method + SCAMPER ideation; outputs StoryKernel JSON scaffold with no frame-geometry fields. `[VERIFIED: SKILL.md outputs StoryKernel]` |
| 13 | `colorist` | 16492 | **form-agnostic** | Tier 3 | CxSxZ color intent + LUT plan; color grading is form-neutral (a LUT applies identically to any resolution). `[VERIFIED: SKILL.md CxSxZ definition]` |
| 14 | `theory_critic` | 18723 | **form-agnostic** | Tier 3 | Artistic critic (McKee/Tan/classical film theory); advisory soft-gate that evaluates narrative, not framing. `[VERIFIED: SKILL.md is advisory only]` |
| 15 | `audio_pipeline` | 72251 | **form-agnostic** | Tier 3 | 6-sub-step audio (voicer/lip_sync/composer/foley/mixer/spatial_audio). Audio is form-neutral EXCEPT spatial_audio (HRTF/binaural differs slightly by listening context), but v14.0 treats it as form-agnostic per CONTEXT.md deferred-items. `[VERIFIED: SKILL.md 6 sub-steps; spatial_audio is a sub-step, not a separate expert]` |

**Tier counts:** Tier 1 = 4 experts (cinematographer, visual_executor, editor, character_designer); Tier 2 = 5 experts (continuity_auditor, hook_retention, screenplay, prompt_injector, compliance_gate); Tier 3 = 6 experts (style_genome, script_auditor, creative_source, colorist, theory_critic, audio_pipeline).

**Note on CONTEXT.md tier-count discrepancy:** CONTEXT.md specified "Tier 1 = 5, Tier 2 = 7, Tier 3 = 3". This sums to 15 but includes deprecated experts (`drawer`, `scene_builder`, `storyboard_designer`) in Tier 1/2 and lists `audio_pipeline` + sub-steps as separate Tier 3 entries. The researcher's reclassification (4/5/6) respects the actual active-expert set. The planner should treat this research's tier table as authoritative and flag the CONTEXT.md discrepancy for discuss-phase reconciliation if needed — but NOT block planning on it, since the total is still 15 and the tier boundaries are Claude's Discretion per CONTEXT.md.

## Runtime State Inventory

> Phase 71 is a content/schema migration phase, not a rename/refactor. However, it touches `PipelineState` which persists to disk. The relevant question: what existing runtime state stores form-factor-adjacent data?

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Existing `.pipeline-state.json` files in `kais-hermes-skills/skills/kais-movie-pipeline/episodes/*/` — NONE have a `form_factor` field today | None — `load()` forward-compat filter drops unknown keys and dataclass default kicks in. Old episodes implicitly become `form_factor: "portrait"`. `[VERIFIED: store.py:183 filter logic]` |
| Live service config | ComfyUI `:8188` (LTX-MSR render) — no form_factor config; width/height passed per-request via `--width`/`--height` argparse | None — template already accepts these params; Plan A adds a `form_factor`→resolution helper but doesn't change the ComfyUI contract |
| OS-registered state | None — Phase 71 registers no OS-level services, cron jobs, or systemd units | None |
| Secrets/env vars | None — form_factor is not a secret; no env var rename | None |
| Build artifacts | `kais-hermes-skills/skills/kais-movie-pipeline/episodes/formc-test-01/assets/P11/render_*.py` — 16 episode render scripts that hardcode `MSR_FC = 41` (already correct) and pixel dims | None for MSR_FC (already 41). Pixel dims in these scripts are episode-specific (already rendered); Plan A's form_factor switch is in the TEMPLATE (`templates/ltx_msr_batch_render.py`), not in already-generated episode scripts. `[VERIFIED: grep showed all 16 render_*.py use MSR_FC = 41]` |

**Nothing found that blocks execution.** The migration is forward-compatible by construction.

## Common Pitfalls

### Pitfall 1: 16:9 ≠ "just resize 9:16" (PITFALL F-1, BLOCKER)
**What goes wrong:** Multiple creative assumptions baked into the vertical-only pipeline do not survive a width/height swap: power points (1/3,1/4 vertical vs 1/3,1/3 horizontal), headroom (5-10% vs 8-15%), subtitle safe area (5 vertical zones vs 3 horizontal zones), camera-move priority (tilt/crane vs pan/tracking), shot-scale distribution (MCU 30-40% vertical bias vs standard WS+FS higher share horizontal), eye-trace (~27% vertical tightening vs ~30% horizontal).
**Why it happens:** `cinematographer/references/vertical-screen-framing.md` is explicitly vertical-only ("不适用于横屏 cinema"). No horizontal companion exists.
**How to avoid:** Author `horizontal-screen-framing.md` BEFORE parameterizing form_factor (Plan A ordering). Cinematographer Step 3 MUST branch on form_factor and load the correct ref (Plan C).
**Warning signs:** Landscape output looks "off" to a human cinematographer but passes all unit tests (because all tests are vertical-only). Add landscape eval variants under `_eval/`. `[CITED: PITFALLS.md F-1]`

### Pitfall 2: Step 14 reframe math inverts when master is landscape (PITFALL F-2, BLOCKER)
**What goes wrong:** Current `platform-master-slicing.md` D1 algorithm assumes `master.mp4 = vertical 9:16`. Vertical variants are lossless; horizontal variants (抖音横屏) are reframe-with-crop. If master becomes landscape, the reframe math inverts: horizontal variants are lossless, vertical variants now need crop-and-scale that may cut off subjects framed for horizontal.
**How to avoid:** Step 14 contract MUST branch on `master_form_factor × target_platform_form_factor` (4 combinations). Each of 7 platforms has a known expected form — re-derive per cell. `[CITED: PITFALLS.md F-2; platform-master-slicing.md lines 66-75]`
**Warning signs:** Vertical platform variants from landscape master have subject heads cropped. Smoke test comparing variant aspect ratios vs platform specs.

### Pitfall 3: Deprecated expert stubs patched instead of parents (CONTEXT.md discrepancy, WARNING)
**What goes wrong:** CONTEXT.md Tier 1 lists `drawer` and Tier 2 lists `scene_builder` — both are DEPRECATED redirect stubs (654 bytes each, `status: merged_into`). Patching them adds a `## Form Factor Adaptation` section to a stub that the loader follows to the parent (`visual_executor` / `cinematographer`). The section is invisible at runtime.
**How to avoid:** Patch ONLY the 15 canonical active DAG experts listed in the tier table above. `visual_executor` owns the drawer sub-step; `cinematographer` owns the scene_builder absorbed territory; `audio_pipeline` owns all 6 audio sub-steps.
**Warning signs:** A SKILL.md file under 2KB is a redirect stub, not an active expert. `[VERIFIED: drawer/SKILL.md = 654 bytes]`

### Pitfall 4: MSR_FC=17 appears in 5 doc locations, not just SKILL.md:446 (FORM-05 scope creep risk)
**What goes wrong:** CONTEXT.md says MSR_FC fix is "single-line at SKILL.md:446". Grep found MSR_FC=17 in 5 doc files: `SKILL.md:446`, `p11-single-shot-orchestration.md:75,85`, `ltx-msr-single-shot-prompt-construction.md:1602,1616`, `post-production-audit.md:156`, `ltx-msr-workflow-spec.md:121`. Fixing only SKILL.md:446 leaves 4 contradictory stale references.
**How to avoid:** Plan A executor runs `grep -rn "MSR_FC=17\|MSR_FC = 17" kais-hermes-skills/` and fixes ALL occurrences in one commit. Note: some refs (e.g., `ltx-msr-single-shot-prompt-construction.md:1602-1618`) already document the 17→41 transition as a historical note — those are correct and should NOT be changed. `[VERIFIED: grep results]`

### Pitfall 5: "文档有规则,代码没执行" META-RULE X-2 regression (BLOCKER)
**What goes wrong:** 15 SKILL.md files get a `## Form Factor Adaptation` section, but if the pipeline phase modules (p09 shot_breakdown, p11 video_render) don't inject `form_factor` into the `goal` f-string, subagents keep generating vertical-only output. Documentation is advisory without code backing.
**How to avoid:** Every MUST added to SKILL.md → extract as `_FORM_FACTOR_INSTRUCTION` constant → inject into `goal` via f-string `[CONSTRAINTS]` segment → test asserts keyword present in `captured["goal"]`. `[CITED: PITFALLS.md X-2]`
**Warning signs:** `grep MUST kais-movie-pipeline/SKILL.md | wc -l` != `count_constraints(goal)` in the phase module.

### Pitfall 6: ltx_msr_batch_render.py already defaults to MSR_FC=41 and width=1280/height=704
**What goes wrong:** If Plan A "fixes" the template script's MSR_FC, it's a no-op — the template is already correct (`MSR_FC_DEFAULT = 41` at line 67). The stale 17 lives ONLY in documentation. Similarly, the template already defaults to 16:9 (1280×704); the form_factor switch adds a convenience helper but doesn't change existing behavior.
**How to avoid:** Plan A's MSR_FC scope is DOC-ONLY. Plan A's resolution switch adds a `--form-factor` argparse option that maps to `--width`/`--height` defaults but does NOT override explicit operator flags. `[VERIFIED: ltx_msr_batch_render.py line 67, 606-611]`

## Code Examples

### PipelineState Migration (FORM-01) — exact diff
```python
# Source: /data/workspace/kais-hermes-skills/plugins/pipeline_state/store.py (verified lines 36, 58-88)
# The ONLY code change in Plan A. Everything else is markdown.

# Line 36 — add Literal import (already imports from typing via __future__ annotations):
from typing import Literal  # ADD THIS

# Lines 58-74 — add form_factor field after trace_id:
@dataclass
class PipelineState:
    episode: str
    phases: dict[str, dict] = field(default_factory=dict)
    current_phase_id: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    last_resumed_at: str | None = None
    trace_id: str | None = None
    form_factor: Literal["landscape", "portrait"] = "portrait"  # NEW v14.0 (FORM-01)

# Line 88 — _STATE_FIELDS auto-derives; NO CHANGE NEEDED:
# _STATE_FIELDS = frozenset(PipelineState.__dataclass_fields__.keys())
# This already picks up form_factor because __dataclass_fields__ is populated at class definition.
```

### Backward-compat round-trip test (verified-safe pattern)
```python
# Source: derived from store.py:145-190 load() forward-compat filter (verified)
def test_old_episode_json_without_form_factor_loads_as_portrait(tmp_path):
    """Pre-v14.0 .pipeline-state.json (no form_factor key) must load cleanly
    and default to 'portrait' for backward compatibility (FORM-01)."""
    state_file = tmp_path / ".pipeline-state.json"
    state_file.write_text(json.dumps({
        "episode": "volvo-v1",
        "phases": {},
        # NO form_factor key — simulates pre-v14.0 episode
    }), encoding="utf-8")

    store = PipelineStateStore(tmp_path)
    state = store.load()
    assert state.form_factor == "portrait"  # dataclass default kicks in
    assert state.episode == "volvo-v1"
```

### LTX-MSR form_factor → resolution switch (Plan A, template helper)
```python
# Source: /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/templates/ltx_msr_batch_render.py
# Add a helper near MSR_FC_DEFAULT (line 67 area):

# Form factor → default resolution map (FORM-01 Plan A)
# Portrait = 9:16 (vertical 短剧 — current implicit default via 704×1280)
# Landscape = 16:9 (horizontal cinema — current template default via 1280×704)
_FORM_FACTOR_RESOLUTION = {
    "portrait": (704, 1280),    # width, height
    "landscape": (1280, 704),   # current template default
}

# In parse_args(), add:
parser.add_argument(
    "--form-factor", choices=["landscape", "portrait"], default=None,
    help="Form factor override. If set, derives --width/--height defaults "
         "from form factor unless explicitly overridden. (FORM-01 v14.0)",
)

# In main(), before submitting:
if args.form_factor and not args.width_was_overridden:
    w, h = _FORM_FACTOR_RESOLUTION[args.form_factor]
    args.width, args.height = w, h
```

### Step 14 4-cell matrix ref extension (Plan C, patch sketch)
```markdown
## 4-Cell Reframe Matrix (FORM-04 v14.0)

When `PipelineState.form_factor` parameterizes the master, Step 14 D1 algorithm
branches on `master_form_factor × target_platform_form_factor`:

| Master → Target | Cell | Algorithm | Quality |
|-----------------|------|-----------|---------|
| portrait → portrait | A (pass-through) | Direct copy; no reframe | Lossless |
| landscape → landscape | B (pass-through) | Direct copy; no reframe | Lossless |
| portrait → landscape | C (letterbox/reframe) | Letterbox (pillarbox bars) OR reframe from 9:16 vertical keyframe via saliency scan of B-roll candidates | Minor quality loss (letterbox) or re-composition (reframe) |
| landscape → portrait | D (center-crop + saliency) | Center-crop to 9:16 with mandatory saliency scan preserving top-2/3 primary info (swipe gesture zone avoidance per platform-specs.md) | Moderate quality loss; cinematographer consultation if primary info concentrated at bottom |

**Regression note:** Existing vertical-master behavior = Cell A (now made explicit).
Existing tests for vertical-master slicing are preserved as Cell A tests — do NOT
rewrite them as a matrix abstraction (high regression risk for low abstraction value).

**Saliency scan requirement (Cell D):** Per platform-specs.md 刚性约束 行为层
"划走手势触发区": screen bottom 1/3 is swipe gesture zone; primary visual info
must not land ONLY in bottom 1/3. Cell D crop MUST verify post-crop info
distribution is top-2/3 + bottom-1/3 before emitting the variant. Implementation
choice (GLM-4.6V semantic scan vs ffmpeg cropdetect brightness scan) is deferred
to plan-phase per CONTEXT.md.
```

## horizontal-screen-framing.md Authoring Spec

### Verified 5-section structure (from `vertical-screen-framing.md`)
`[VERIFIED: /data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/references/vertical-screen-framing.md — read in full, 199 lines]`

The vertical ref has these sections (in order):
1. **9:16 Power points 修正** — power points (1/3, 1/4) and (2/3, 1/4) with per-shot-scale table (EWS through BCU)
2. **Headroom 标准** — 5-10% vertical headroom + "haircut" anti-pattern for BCU
3. **字幕 Safe Area** — 5-zone table (Top 0-15% / Upper-center 15-35% / Center 35-65% face zone / Lower-center 65-85% / Bottom 85-100%) + per-platform subtitle divergence
4. **Per-Platform Framing Divergence** — 7 platforms with framing preferences + 抖音/小程序剧 3 铁律 each
5. **Vertical Camera Move 修正** — tilt/crane/vertical-tracking preferred; horizontal pan limited

Plus: Vertical Framing JSON Schema output example + 6 anti-patterns + glossary.

### horizontal-screen-framing.md mirror structure (required by FORM-03 literal success criteria)
`[ASSUMED — structure is mandated by CONTEXT.md "mirror vertical-screen-framing.md 5-section structure"; content is Claude's Discretion but must have real film citations]`

| Section | Horizontal counterpart content | Citation candidates |
|---------|-------------------------------|---------------------|
| 1. 16:9 Power points | Standard rule-of-thirds (1/3, 1/3) / (2/3, 1/3) / (1/3, 2/3) / (2/3, 2/3) + golden ratio intersections; per-shot-scale table for horizontal | Blain Brown *Cinematography: Theory and Practice* (3rd ed); Gustavo Mercado *The Filmmaker's Eye* `[ASSUMED — standard cinematography texts]` |
| 2. Headroom 标准 | 8-15% horizontal headroom; lead room (nose room) for profile shots; "rule of thirds" horizontal eye-line at 1/3 from top | Blain Brown; Bordwell & Thompson *Film Art* 11th ed `[CITED: vertical-screen-framing.md Source line]` |
| 3. Subtitle Safe Area | 3-zone horizontal (top 0-10% / center 10-80% action zone / bottom 80-100%); lower-center 80-95% preferred; per-platform divergence (YouTube vs B站 vs Netflix) | Netflix Timed Text Style Guide; YouTube subtitle specs `[ASSUMED — needs verification]` |
| 4. Per-Platform Framing Divergence | YouTube (cinematic + retention curve) vs B站长 (longer establishing tolerated) vs 抖音横屏 (5-10s hook); horizontal cinema is NOT "one size fits all" | Platform public creator academies `[ASSUMED — mirror vertical ref's citation pattern]` |
| 5. Horizontal Camera Move 修正 | Pan/tracking/dolly preferred; vertical tilt de-emphasized; crane for establishing; whip pan for transitions | Mascellian 12 camera moves; `camera-motion-catalog.md` cross-ref `[VERIFIED: cinematographer/SKILL.md references camera-motion-catalog.md]` |

**Real film citations per section (CONTEXT.md "consistent with v1-v5 methodology of citing real films"):**
- Power points / symmetry: *Grand Budapest Hotel* (Wes Anderson centered symmetry)
- Wide landscape shot-scale: *The Revenant* (Lubezki wide landscapes) + *Lawrence of Arabia*
- Long-take horizontal track (eye-trace): *1917* (Mendes/Deakins continuous track)
- Horizontal headroom / lead room: *Drive* (Refn/Winding) profile shots
- Horizontal pan: *The Shining* (Kubrick Steadicam tracking)

`[ASSUMED — these are well-known cinematography examples; researcher did not verify against re-viewing the films]`

### Copyright header (required per SKILL-LAYOUT.md)
```markdown
# Horizontal Screen Framing — 16:9 Cinema + YouTube/B站 Framing Rules

**Source:** Blain Brown *Cinematography: Theory and Practice* (3rd ed, 2016);
Gustavo Mercado *The Filmmaker's Eye* (2010); Bordwell & Thompson *Film Art: An
Introduction* (11th ed, 2020); Netflix Timed Text Style Guide (public); YouTube
Creator Academy horizontal guides; film analysis of cited titles under fair use.
**Copyright:** Fair Use — framing rules paraphrased from public cinematography
texts + creator guides; film citations are analytical references, not reproductions.
**Last-verified:** 2026-07-09
```

## MSR_FC=17→41 Propagation Audit

`[VERIFIED: grep -rn "MSR_FC=17\|MSR_FC = 17" /data/workspace/kais-hermes-skills/ — run 2026-07-09]`

| File | Line(s) | Current value | Action |
|------|---------|---------------|--------|
| `skills/kais-movie-pipeline/SKILL.md` | 446 | `MSR_FC=17` (ALWAYS 17) | **FIX → 41** (FORM-05 primary) |
| `skills/kais-movie-pipeline/references/p11-single-shot-orchestration.md` | 75 | `MSR_FC = 17  # or 41` | **FIX → `MSR_FC = 41  # canonical per 2026-07-01 A/B test`** |
| `skills/kais-movie-pipeline/references/p11-single-shot-orchestration.md` | 85 | `MSR_FC=17 → num_frames=105` | **FIX → 41, recompute num_frames example** |
| `skills/kais-movie-pipeline/references/ltx-msr-single-shot-prompt-construction.md` | 1602 | `MSR_FC=17 → must be updated to 41` | **LEAVE (already documents the transition as a historical note — correct)** |
| `skills/kais-movie-pipeline/references/ltx-msr-single-shot-prompt-construction.md` | 1610, 1616, 1618 | Mixed 41 (correct) + historical 17 references in narrative | **LEAVE (narrative of the A/B test transition — correct as-is)** |
| `skills/kais-movie-pipeline/references/post-production-audit.md` | 156 | `MSR_FC=17` | **FIX → 41** |
| `skills/kais-movie-pipeline/references/ltx-msr-workflow-spec.md` | 67 | `# With MSR_FC=41` | LEAVE (already correct) |
| `skills/kais-movie-pipeline/references/ltx-msr-workflow-spec.md` | 121 | `Trim MSR_FC=17` | **FIX → 41** |
| `skills/kais-movie-pipeline/templates/ltx_msr_batch_render.py` | 67 | `MSR_FC_DEFAULT = 41` | LEAVE (already correct — template is the source of truth) |
| `skills/kais-movie-pipeline/episodes/formc-test-01/assets/P11/render_*.py` | 16 files | `MSR_FC = 41` | LEAVE (already correct; episode-generated, not template) |

**Actionable fixes: 5 locations across 4 doc files.** Plan A sweeps these in one commit. The `ltx-msr-single-shot-prompt-construction.md` narrative (lines 1602-1618) is the A/B test transition record and is correct — do NOT edit it.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `MSR_FC=17` hardcoded | `MSR_FC=41` (A/B test 2026-07-01) | 2026-07-01 | Template already fixed; 5 doc references still stale. Plan A closes the doc gap. `[VERIFIED: template line 67; grep results]` |
| `width=1280 height=704` (16:9 only) hardcoded in SKILL.md prose | `--width`/`--height` argparse in template (already exists); `--form-factor` switch NEW | v14.0 Plan A | Operator can pass `--form-factor portrait` instead of raw pixels; resolution helper centralizes the mapping |
| Vertical 9:16 hardcoded in 5+ SKILL.md prose locations | `form_factor` parameter with `"portrait"` default | v14.0 Plan A/B | Backward-compatible (default = current behavior); landscape is opt-in per project |
| 7-variant Step 14 assumes vertical master | 4-cell reframe matrix parameterizes master form | v14.0 Plan C | Landscape masters supported; vertical-master regression covered by Cell A |

**Deprecated/outdated:**
- `MSR_FC=17` default: superseded by 41 per 2026-07-01 A/B test. Template fixed; docs lagging.
- `"All 15 movie-experts assume this form"` claim at `kais-movie-pipeline/SKILL.md:40`: must be updated in Plan A to read `form_factor` from PipelineState instead of assuming vertical 9:16. `[VERIFIED: SKILL.md line 40]`

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | character_designer is Tier 1 (form-critical) because turnaround sheet layout differs by aspect ratio | 15-Expert Tier Classification | If wrong (turnaround sheets are form-neutral), character_designer drops to Tier 2; minor — section content is Claude's Discretion |
| A2 | screenplay is Tier 2 (form-aware) because blocking/staging notes implicitly assume frame geometry | 15-Expert Tier Classification | If wrong (screenplay is fully form-neutral), screenplay drops to Tier 3; minor |
| A3 | Real film citations (Grand Budapest Hotel, Revenant, 1917, Drive, Shining) are appropriate horizontal-framing examples | horizontal-screen-framing.md Authoring Spec | If operator prefers different films, content is Claude's Discretion per CONTEXT.md |
| A4 | Netflix/YouTube subtitle style guides are public and citable for horizontal subtitle safe area | horizontal-screen-framing.md Authoring Spec | If not public, use Bordwell & Thompson general framing principles instead; verify before citing |
| A5 | GLM-4.6V saliency scan for Cell D is allowed under MEMORY.md glm-5.2-only constraint | Standard Stack Supporting | CONFIRMED via MEMORY.md: glm-5.2-only restricts MODEL switches, not vision TOOL calls. GLM-4.6V is a vision tool, not a model swap. `[CITED: MEMORY.md feedback-glm-5-2-only.md]` |
| A6 | kais-hermes-skills has no root pyproject.toml (tests run via direct pytest invocation on skills/kais-movie-pipeline/tests/) | Validation Architecture | If a pyproject exists elsewhere, test command changes; verified via find — none found at repo root |

## Open Questions

1. **Does `prompt_injector` need landscape-specific prompt tokens?**
   - What we know: prompt_injector translates camera-move intent → dreamina/Runway/Kling prompt tokens. Vertical compositions use tokens like "vertical tilt up"; horizontal uses "horizontal pan right".
   - What's unclear: whether the token VOCABULARY differs or only the token SELECTION differs. If vocabulary is identical and only selection changes, Tier 2 stub suffices. If vocabulary differs (e.g., dreamina has separate `--aspect 16:9` vs `--aspect 9:16` flags), Tier 1 depth needed.
   - Recommendation: Plan B executor reads `prompt_injector/SKILL.md` in full before writing the section; default to Tier 2 unless vocabulary divergence found.

2. **Is the Step 14 saliency scan GLM-4.6V or ffmpeg cropdetect?**
   - What we know: CONTEXT.md defers the implementation choice to plan-phase.
   - Recommendation: Plan C uses ffmpeg `cropdetect` as zero-dep default; GLM-4.6V semantic scan is an enhancement if operator reports cropdetect misses semantic subjects. Keeps Plan C dependency-free.

3. **Should Plan A add a `form_factor` validator that rejects per-shot overrides?**
   - What we know: ARCHITECTURE Anti-Pattern 1 says pipeline boot validates the invariant (no per-shot mixing). CONTEXT.md specifics section endorses this.
   - Recommendation: Plan A includes a `validate_form_factor_invariant(state)` function that scans `state.phases` for per-shot `form_factor` keys and rejects if found. Low cost, high defense value.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | PipelineState dataclass (`Literal` in `typing`) | ✓ | 3.13 (per CLAUDE.md) | — |
| pytest | Plan C unit tests (Step 14 reframe math) | ✓ | (in hermes-agent venv; kais-hermes-skills tests run via `python -m pytest`) | standalone script if pytest unavailable |
| ffmpeg CLI | Step 14 reframe execution (crop/letterbox) + sample-frame generation | ✓ | (in Docker stack per CLAUDE.md) | — |
| GLM-4.6V (zai provider) | Saliency scan for Cell D (optional, deferred to plan-phase) | ✓ | already wired | ffmpeg `cropdetect` filter (zero-dep) |
| ComfyUI :8188 | LTX-MSR render (NOT exercised in Phase 71 — only template helper added) | N/A | N/A | N/A — Plan A adds the `--form-factor` flag but does not run renders |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None — all required deps available.

## Validation Architecture

> `workflow.nyquist_validation: true` in `.planning/config.json`. This section is REQUIRED.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (stdlib, no separate pyproject on kais-hermes-skills side) |
| Config file | `skills/kais-movie-pipeline/tests/conftest.py` (shared fixtures: `mock_delegate_factory`, `tmp_asset_bus`, `tmp_state_store`, `fake_registry`, `make_fake_phase`) |
| Quick run command | `cd /data/workspace/kais-hermes-skills && python -m pytest skills/kais-movie-pipeline/tests/test_form_factor.py -x` |
| Full suite command | `cd /data/workspace/kais-hermes-skills && python -m pytest skills/kais-movie-pipeline/tests/ -x` |

`[VERIFIED: conftest.py exists at skills/kais-movie-pipeline/tests/conftest.py with the documented fixtures; test_p09_unit.py demonstrates the delegate_task injection + captured["goal"] assertion pattern]`

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FORM-01 | Old JSON without form_factor loads as "portrait" (backward compat) | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_form_factor.py::test_old_json_defaults_to_portrait -x` | ❌ Wave 0 |
| FORM-01 | New JSON with form_factor="landscape" round-trips | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_form_factor.py::test_landscape_round_trip -x` | ❌ Wave 0 |
| FORM-01 | Invalid form_factor value raises (no fuzzy matching) | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_form_factor.py::test_invalid_form_factor_raises -x` | ❌ Wave 0 |
| FORM-01 | Per-shot form_factor override is rejected (invariant validator) | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_form_factor.py::test_rejects_per_shot_override -x` | ❌ Wave 0 |
| FORM-02 | Each of 15 active SKILL.md has `## Form Factor Adaptation` section | smoke | `grep -l "## Form Factor Adaptation" skills/movie-experts/{cinematographer,visual_executor,editor,...}/SKILL.md \| wc -l == 15` | ❌ Wave 0 (bash one-liner) |
| FORM-03 | `horizontal-screen-framing.md` exists with 5 sections | smoke | `grep -c "^## " skills/movie-experts/cinematographer/references/horizontal-screen-framing.md` returns >= 5 | ❌ Wave 0 |
| FORM-04 | Step 14 4-cell matrix present in platform-master-slicing.md | smoke | `grep -c "portrait → portrait\|landscape → landscape\|portrait → landscape\|landscape → portrait" skills/kais-movie-pipeline/references/platform-master-slicing.md == 4` | ❌ Wave 0 |
| FORM-04 | Cell D saliency-scan requirement documented | smoke | `grep "saliency scan" skills/kais-movie-pipeline/references/platform-master-slicing.md` | ❌ Wave 0 |
| FORM-05 | No MSR_FC=17 remains as a default (only in historical narrative) | smoke | `grep -rn "MSR_FC=17" skills/kais-movie-pipeline/ \| grep -v "must be updated\|historical\|was 17"` returns 0 | ❌ Wave 0 |
| FORM-05 | Template defaults to MSR_FC=41 | unit | `python -c "import sys; sys.path.insert(0,'skills/kais-movie-pipeline/templates'); from ltx_msr_batch_render import MSR_FC_DEFAULT; assert MSR_FC_DEFAULT == 41"` | ❌ Wave 0 (already true — regression guard) |
| XCUT-02 | `_FORM_FACTOR_INSTRUCTION` injected into p09 goal | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_form_factor.py::test_p09_goal_includes_form_factor -x` | ❌ Wave 0 |

### Sampling Rate (Nyquist Dimension 8)
- **Per task commit:** `python -m pytest skills/kais-movie-pipeline/tests/test_form_factor.py -x` (quick — ~2s, 4-6 unit tests)
- **Per wave merge:** Full pipeline test suite `python -m pytest skills/kais-movie-pipeline/tests/ -x` (catches regression in p09/p11 phase modules that consume form_factor)
- **Phase gate (before `/gsd:verify-work`):** Full suite green + smoke grep assertions (FORM-02 section presence, FORM-03 ref existence, FORM-04 matrix presence, FORM-05 MSR_FC sweep) all pass. The grep-based smoke checks are the Nyquist high-frequency samples that prove the markdown content actually landed; the pytest unit tests are the low-frequency samples that prove the Python behavior.

**Nyquist rationale:** The FORM phase has two distinct signal types — (1) Python behavior (form_factor field, validation, goal injection) sampled by pytest unit tests at task-commit rate, and (2) markdown content presence (15 SKILL.md sections, 1 new ref, 1 ref extension) sampled by grep smoke checks at wave-merge rate. Sampling only one type would alias the other — e.g., all pytest green but a SKILL.md section missing means FORM-02 fails silently. Both sampling rates are required.

### Wave 0 Gaps
- [ ] `skills/kais-movie-pipeline/tests/test_form_factor.py` — NEW file covering FORM-01 backward-compat + landscape round-trip + invalid-value rejection + per-shot override rejection + p09 goal injection (XCUT-02). ~6 tests.
- [ ] No framework install needed — pytest already available via hermes-agent venv; kais-hermes-skills tests invoke it directly.

*(If no other gaps: existing `conftest.py` fixtures cover PipelineState round-trip testing via `tmp_state_store` — reuse it.)*

## Security Domain

> Phase 71 has no authentication, session, or network-input surface. `form_factor` is an internal enum with two values; no user-supplied input reaches it (operator declares it at project creation via Python code or direct JSON edit). The only security-relevant concern is input validation (FORM-01 strict enum).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — no auth in this phase |
| V3 Session Management | no | N/A — no sessions |
| V4 Access Control | no | N/A — no privileged operations |
| V5 Input Validation | yes | `Literal["landscape", "portrait"]` strict enum; unknown values raise `ValidationError` at parse time. No fuzzy matching, no warnings-and-continue (CONTEXT.md locked decision). |
| V6 Cryptography | no | N/A — no crypto |

### Known Threat Patterns for FORM stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Invalid form_factor string in episode JSON (typo or injection) | Tampering | `Literal` enum + Pydantic-style validation at `PipelineState.__post_init__` or the `load()` filter boundary; reject unknown values |
| Per-shot form_factor override (consistency-collapse attack on LTX ICLoRA conditioning) | Tampering | `validate_form_factor_invariant()` scans phases dict for per-shot keys; rejects if found (Plan A deliverable per ARCHITECTURE Anti-Pattern 1) |

## Sources

### Primary (HIGH confidence)
- `/data/workspace/kais-hermes-skills/plugins/pipeline_state/store.py` — PipelineState dataclass (lines 58-74), `_STATE_FIELDS` auto-derivation (line 88), `load()` forward-compat filter (lines 145-190). Read in full (268 lines).
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/SKILL.md` — line 40 ("All 15 movie-experts assume this form" — hardcoded vertical), line 446 (`MSR_FC=17` STALE), Step 14 contract (~line 283), form assumption prose. Read key sections.
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/templates/ltx_msr_batch_render.py` — `MSR_FC_DEFAULT = 41` (line 67, already correct), `--width`/`--height` argparse (lines 606-611), `--msr-fc` default (line 614). Read argparse section in full.
- `/data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/SKILL.md` — 28 vertical/9:16 refs, Step 3 "Composition per Shot" (line 178), Step 9 orchestration procedure. Read key sections + grep for form refs.
- `/data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/references/vertical-screen-framing.md` — full 199-line ref with 5-section structure (power points / headroom / subtitle safe area / platform divergence / camera move). Read in full — this is the template for horizontal-screen-framing.md.
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/platform-master-slicing.md` — D1 aspect-ratio adaptation algorithm (lines 60-82), 7-variant emission matrix (lines 36-44), saliency-scan requirement for vertical crop (line 74). Read first 120 lines.
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p09_unit.py` — delegate_task injection pattern, `captured["goal"]` assertion convention. Read in full (120 lines).
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/conftest.py` — `mock_delegate_factory`, `tmp_state_store` fixtures. Read in full (50 lines).
- `/data/workspace/kais-hermes-skills/skills/movie-experts/_shared/SKILL-LAYOUT.md` — frontmatter schema, reference file anatomy (`Source / Copyright / Last-verified` header block), 15-expert FOUND-08 freeze rule. Read in full (136 lines).
- `/data/workspace/hermes-agent/.planning/research/v14-4track-upgrade/SUMMARY.md` — reconciliation #5 (MSR_FC canonical = 41), reconciliation #6 (lineage bump scope = 6 SKILL.md / 3 agent.yaml). Read in full.
- `/data/workspace/hermes-agent/.planning/research/v14-4track-upgrade/ARCHITECTURE.md` — Pattern 1 (Schema Migration with Defaults), FORM touch points table (lines 296-308), Anti-Pattern 1 (Per-Shot form_factor). Read in full.
- `/data/workspace/hermes-agent/.planning/research/v14-4track-upgrade/PITFALLS.md` — F-1 (vertical-only ref), F-2 (Step 14 matrix), F-3 (form-agnostic experts), X-1 (lineage cascade), X-2 (META-RULE _INSTRUCTION). Read in full.
- `/data/workspace/hermes-agent/.planning/research/v10-orchestrator-design/04-MIGRATION-PATH.md` §1.6 — canonical 15 active DAG expert table (lines 200-214). Read §1.6 in full.
- `/data/workspace/hermes-agent/.planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md` — 6 SKILL.md baseline sha256, canonical field-name mapping (`lineage.skill_sha256` not `source_sha`). Read in full.

### Secondary (MEDIUM confidence)
- `/data/workspace/hermes-agent/.planning/research/v14-4track-upgrade/FEATURES.md` — FORM feature landscape, anti-features (per-shot mixing, auto-inference). Read in full.
- `/data/workspace/kais-hermes-skills/skills/movie-experts/drawer/SKILL.md` — 654-byte DEPRECATED stub confirming `drawer` is merged into `visual_executor`. Read in full.
- `/data/workspace/kais-hermes-skills/skills/movie-experts/visual_executor/SKILL.md` frontmatter — `sub_steps: [drawer, animator]` confirming visual_executor owns the drawer sub-step. Read frontmatter.
- `/data/workspace/kais-hermes-skills/skills/movie-experts/composer/SKILL.md` — DEPRECATED stub confirming composer is merged into audio_pipeline. Read in full.
- `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/SKILL.md` frontmatter — `aliases: [voicer, lip_sync, composer, foley, mixer, spatial_audio]` confirming audio_pipeline owns all 6 sub-steps. Read frontmatter.

### Tertiary (LOW confidence — needs validation)
- Film citations for `horizontal-screen-framing.md` (Grand Budapest Hotel, Revenant, 1917, Drive, Shining) — `[ASSUMED]` based on training knowledge of cinematography; researcher did not re-verify by viewing the films. Operator may substitute preferred examples.
- Blain Brown / Gustavo Mercado textbook page references — `[ASSUMED]`; researcher cited the book titles but did not verify specific edition page numbers. Plan A executor should verify against the actual text before citing page numbers.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new packages; all stdlib. Verified against `store.py` imports and template argparse.
- Architecture: HIGH — PipelineState migration pattern verified against live `store.py:58-88`; `_STATE_FIELDS` auto-derivation confirmed. Step 14 matrix insertion point verified against `platform-master-slicing.md` D1 algorithm.
- Pitfalls: HIGH — all 6 pitfalls cross-verified against live code (deprecated stubs confirmed at 654 bytes; MSR_FC=17 grep found exactly 5 actionable doc locations; template MSR_FC_DEFAULT=41 confirmed at line 67).
- 15-expert tier classification: HIGH for the canonical list (verified against `04-MIGRATION-PATH.md §1.6` + live frontmatter); MEDIUM for individual tier assignments (character_designer/screenplay Tier 1/2 classification is `[ASSUMED]` based on output analysis, not exhaustively verified by reading full SKILL.md bodies — planner should have Plan B executor do a full read of each Tier 1/2 expert before writing the section).
- horizontal-screen-framing.md content: MEDIUM — 5-section structure is HIGH confidence (verified against vertical twin); citation content is `[ASSUMED]`.

**Research date:** 2026-07-09
**Valid until:** 2026-08-08 (30 days — stable; no fast-moving dependencies. The only currency risk is if someone edits the 6 baseline SKILL.md files between now and Phase 71 execution, which would shift the sha256 and require Phase 70 inventory refresh — but Phase 70 curator freeze blocks this.)
