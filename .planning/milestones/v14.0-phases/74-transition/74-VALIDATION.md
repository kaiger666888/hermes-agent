---
phase: 74
slug: transition
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-09
---

# Phase 74 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (python 3.11+); bash smoke script for asset-bus + canvas sync + schema assertions |
| **Config file** | `kais-hermes-skills/pyproject.toml` `[tool.pytest.ini_options]` (existing) |
| **Quick run command** | `cd /data/workspace/kais-hermes-skills && python -m pytest plugins/pipeline_state/tests/test_transition_schema.py skills/kais-movie-pipeline/tests/test_p09_transition_unit.py -x -q` |
| **Full suite command** | `cd /data/workspace/kais-hermes-skills && python -m pytest plugins/pipeline_state/tests/ skills/kais-movie-pipeline/tests/test_p09_unit.py skills/kais-movie-pipeline/tests/test_p09_transition_unit.py -x -q && bash .planning/phases/74-transition/74-smoke.sh` |
| **Estimated runtime** | ~20 seconds (quick); ~50 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run quick command
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite green AND `74-smoke.sh` exits 0
- **Max feedback latency:** 20s (quick) / 50s (full)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 74-01-01 | 01 (Foundation) | 1 | TRANS-01 | — | Pydantic schema for transition_method (12-enum Literal) + visual_hook (str\|None) + camera_continuity (6-enum Literal) enforces strict enum validation | unit | `python -m pytest plugins/pipeline_state/tests/test_transition_schema.py::test_transition_method_enum_strict -xvs` | ❌ W0 | ⬜ pending |
| 74-01-02 | 01 | 1 | TRANS-01 | — | Schema defaults: transition_method="hard_cut", visual_hook=None, camera_continuity="none" (preserves backward compat) | unit | `python -m pytest plugins/pipeline_state/tests/test_transition_schema.py::test_schema_defaults -xvs` | ❌ W0 | ⬜ pending |
| 74-01-03 | 01 | 1 | TRANS-02 | T-74-01 | `load_next_shot_link(value)` helper coerces string form to structured default `{shot_id: value, transition_method: "hard_cut", visual_hook: None, camera_continuity: "none", generation_path: None}` | unit | `python -m pytest plugins/pipeline_state/tests/test_transition_schema.py::test_load_string_next_shot_link -xvs` | ❌ W0 | ⬜ pending |
| 74-01-04 | 01 | 1 | TRANS-02 | — | `load_next_shot_link(value)` accepts structured dict form; validates via Pydantic | unit | `python -m pytest plugins/pipeline_state/tests/test_transition_schema.py::test_load_structured_next_shot_link -xvs` | ❌ W0 | ⬜ pending |
| 74-01-05 | 01 | 1 | TRANS-03 | — | `transition_design` slot added to ASSET_SCHEMA in asset_bus.py; writer phase P09; reader phase P13; format json envelope V3 | unit | `python -m pytest plugins/pipeline_state/tests/test_transition_schema.py::test_asset_bus_slot_registered -xvs` | ❌ W0 | ⬜ pending |
| 74-01-06 | 01 | 1 | TRANS-03 | T-74-02 | Canvas sync `_PHASE_OUTPUT_MAP` at canvas_sync.py has `transition_design` in p09 entry (additive to existing shot_intent + e_konte) | grep | `grep -A 5 "p09" plugins/pipeline_state/canvas_sync.py \| grep -c "transition_design"` ≥ 1 | ❌ W0 | ⬜ pending |
| 74-01-07 | 01 | 1 | TRANS-03 | — | Frontend zod canvasAssetSchema.ts accepts `transition_design` asset type (via reuse of `storyboard` canvas_type per RESEARCH Open Question #1) | grep | `grep -c "storyboard\|transition_design" kais-aigc-platform/src/lib/canvasAssetSchema.ts` ≥ 1 (existing) | ❌ W0 | ⬜ pending |
| 74-02-01 | 02 (SKILL.md + Routing Refs) | 2 | TRANS-04 | T-74-03 | Cinematographer SKILL.md Step 9 has "Field Ownership" subsection citing TRANS-04 + listing transition_method / visual_hook / camera_continuity as creative-intent fields | grep | `grep -A 10 "Step 9" skills/movie-experts/cinematographer/SKILL.md \| grep -c "Field Ownership\|TRANS-04"` ≥ 1 | ❌ W0 | ⬜ pending |
| 74-02-02 | 02 | 2 | TRANS-04 | — | Editor SKILL.md Workflow Step 7 (Transition Design) + p13_delivery.py document cut_duration_frames / dissolve_curve / match_cut_alignment_point as editor-owned execution fields | grep | `grep -c "cut_duration_frames\|dissolve_curve\|match_cut_alignment_point" skills/movie-experts/editor/SKILL.md` ≥ 1 | ❌ W0 | ⬜ pending |
| 74-02-03 | 02 | 2 | TRANS-05 | — | `transition-design.md` ref exists with 12-type taxonomy mapped to execution paths (generation-time / post-production / hybrid) with concrete film examples | bash | `test -f skills/movie-experts/cinematographer/references/transition-design.md && grep -c "^## " skills/movie-experts/cinematographer/references/transition-design.md` ≥ 12 | ❌ W0 | ⬜ pending |
| 74-02-04 | 02 | 2 | TRANS-06 | — | `transition-engine-routing.md` ref exists with per-transition routing rules (Wan2.2 / Hailuo / Vidu / ffmpeg / LTX-2.3 FLF evaluation) | bash | `test -f skills/kais-movie-pipeline/references/transition-engine-routing.md && grep -c "Wan2.2\|Hailuo\|Vidu\|ffmpeg\|LTX-2.3 FLF" skills/kais-movie-pipeline/references/transition-engine-routing.md` ≥ 4 | ❌ W0 | ⬜ pending |
| 74-02-05 | 02 | 2 | TRANS-06 | T-74-04 | All transition engine routing rules declared as declarative constants (NOT runtime LLM decisions — INFRA-04 / PITFALL X-5 compliance) | grep | `grep -c "ROUTING_RULES\|declarative" skills/kais-movie-pipeline/references/transition-engine-routing.md` ≥ 1 | ❌ W0 | ⬜ pending |
| 74-02-06 | 02 | 2 | XCUT-02 | — | `_TRANSITION_DESIGN_INSTRUCTION` constant injected into p09_shot_breakdown.py `.task(steps=)` AND `.constraints()` (consolidated with form_factor per RESEARCH MAX_CONSTRAINTS=7 budget) | grep | `grep -c "_TRANSITION_DESIGN_INSTRUCTION" skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py` ≥ 2 | ❌ W0 | ⬜ pending |
| 74-02-07 | 02 | 2 | XCUT-02 | — | Editor p13_delivery.py (or equivalent) has `_EDITOR_TRANSITION_EXECUTION_INSTRUCTION` constant + `.task(steps=)` + `.constraints()` injection | grep | `grep -c "_EDITOR_TRANSITION_EXECUTION_INSTRUCTION\|_TRANSITION_DESIGN_INSTRUCTION" skills/kais-movie-pipeline/pipeline/phases/p13_delivery.py` ≥ 2 | ❌ W0 | ⬜ pending |
| 74-03-01 | 03 (LTX-FLF Validation + Smoke) | 2 | TRANS-07 | — | `ltx-flf-iclora-validation.md` exists with ComfyUI node graph setup (LiconMSR + LTXVConditioning + SamplerCustomAdvanced) + 1-2 reference shot placeholders + production-readiness verdict template | bash | `test -f skills/kais-movie-pipeline/references/ltx-flf-iclora-validation.md && wc -l skills/kais-movie-pipeline/references/ltx-flf-iclora-validation.md` ≥ 80 | ❌ W0 | ⬜ pending |
| 74-03-02 | 03 | 2 | TRANS-02 | — | Backward-compat smoke test: pre-v14.0 episode JSON with string next_shot_link loads cleanly via load_next_shot_link coercion | unit | `python -m pytest plugins/pipeline_state/tests/test_transition_schema.py::test_backward_compat_string_next_shot_link -xvs` | ❌ W0 | ⬜ pending |
| 74-03-03 | 03 | 2 | XCUT-02 | — | Goal-content test for p09 asserts `_TRANSITION_DESIGN_INSTRUCTION` keyword in `captured["goal"]` (delegate-spy pattern per test_p09_unit.py) | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_p09_transition_unit.py::test_goal_includes_transition_design_instruction -xvs` | ❌ W0 | ⬜ pending |
| 74-03-04 | 03 | 2 | TRANS-01..07 | — | Top-level smoke script `74-smoke.sh` runs all XCUT-01 style assertions; exits 0 | bash | `bash .planning/phases/74-transition/74-smoke.sh` exits 0 | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `kais-hermes-skills/plugins/pipeline_state/tests/test_transition_schema.py` — NEW; TRANS-01 + TRANS-02 schema tests
- [ ] `kais-hermes-skills/skills/kais-movie-pipeline/tests/test_p09_transition_unit.py` — NEW or extend; XCUT-02 goal-content assertion for _TRANSITION_DESIGN_INSTRUCTION
- [ ] `kais-hermes-skills/plugins/pipeline_state/transition_schema.py` — NEW module; Pydantic schema for TransitionMethod enum + NextShotLink structured object + load_next_shot_link helper
- [ ] `.planning/phases/74-transition/74-smoke.sh` — top-level smoke script

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| LTX-2.3 FLF + ICLoRA combined workflow on actual reference shots | TRANS-07 | Requires operator to run ComfyUI workflow with actual model files + visual quality assessment | Operator follows ltx-flf-iclora-validation.md setup; runs 1-2 reference shots; documents results + production-readiness verdict |
| Wan2.2 14B FLF2V local engine availability | TRANS-06 | Requires operator to install Wan2.2 model + ComfyUI custom node in comfyui-primary container | Operator verifies `curl http://127.0.0.1:8188/object_info/Wan2_2_FLF2V` (or equivalent node name) returns 200; documents in transition-engine-routing.md |
| Hailuo 02 i2v Pro + Vidu keyframe-to-video API access | TRANS-06 + XCUT-04b | Requires operator-provided API keys (opt-in for cloud transition engines) | Operator sources Hailuo + Vidu API keys; configures per transition-engine-routing.md; documents monthly cost estimate |
| ffmpeg xfade whip-pan simulation visual quality | TRANS-06 (whip_pan engine routing) | ffmpeg whip-pan is a simulation (per TRANS-08 AI whip-pan deferred); operator must visually verify acceptable quality | Operator runs whip_pan test transition via ffmpeg; reviews output; accepts or overrides manually |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 50s (full suite)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
