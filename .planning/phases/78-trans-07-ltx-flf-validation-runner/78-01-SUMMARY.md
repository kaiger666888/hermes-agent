---
phase: 78-trans-07-ltx-flf-validation-runner
plan: 01
subsystem: kais-movie-pipeline/transition
tags: [ltx, flf, iclora, comfyui, validation-runner, vision-verify, trans-07]
requires:
  - "Phase 77 runner pattern (ComfyUI /prompt + /history + /view flow, Pydantic v2 schema)"
provides:
  - "ComfyUI workflow JSON template for LTX-2.3 FLF+ICLoRA combined validation"
  - "Async validation runner script (run_ltx_flf_validation.py)"
  - "12 unit tests for validation runner (mocked ComfyUI + vision_verify + ffmpeg)"
affects:
  - "TRANS-07 operator-action handoff closure (1-2 reference shot validation)"
  - "TRANS-11 v16+ production rollout gate (verdict from operator)"
tech-stack:
  added:
    - "httpx.AsyncClient (async HTTP for ComfyUI API)"
    - "Pydantic v2 BaseModel with ConfigDict(extra='forbid')"
  patterns:
    - "Async runner with serial awaits (INFRA-04 compliant — no concurrent task dispatch)"
    - "Static JSON workflow template + placeholder find-and-replace per shot (mirrors Phase 77 build_comfyui_workflow)"
    - "vision_verify injection via function parameter for testability"
    - "Graceful degradation: ffmpeg missing -> skip vision_verify with null identity_continuity"
key-files:
  created:
    - path: "skills/kais-movie-pipeline/references/workflows/ltx-flf-iclora-validation.json"
      repo: kais-hermes-skills
      commit: 536c9a7
    - path: "skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py"
      repo: kais-hermes-skills
      commit: ba23bed
    - path: "skills/kais-movie-pipeline/tests/test_run_ltx_flf_validation.py"
      repo: kais-hermes-skills
      commit: ba23bed
decisions:
  - "Two-script design (runner + verdict updater) mirrors Phase 77 lock pattern — runner produces report with null operator_decision, operator edits JSON, verdict update script (Plan 02) writes to markdown"
  - "vision_verify_fn injected as function parameter for testability — production imports lazily from plugins.kais_aigc"
  - "INFRA-04 compliance: all source comments/docstrings avoid the literal concurrent-dispatch string to satisfy the test_no_asyncio_gather check"
metrics:
  duration: 366s
  completed: "2026-07-10"
  tasks: 2
  files: 3
---

# Phase 78 Plan 01: LTX-FLF Validation Runner Summary

Async validation runner + ComfyUI workflow JSON that turns the TRANS-07 operator-action handoff (LTX-2.3 FLF+ICLoRA combined workflow validation) into a 5-minute CLI task with automated ComfyUI submission + frame extraction + vision_verify identity-continuity assessment.

## What Was Built

### 1. ComfyUI Workflow JSON Template (Task 1, commit `536c9a7`)

`references/workflows/ltx-flf-iclora-validation.json` — a 25-node ComfyUI API-format workflow that combines:

- **LiconMSR ICLoRA identity conditioning** (nodes 28+9): multi-reference identity compositing via LiconMSR + LTXAddVideoICLoRAGuide, injecting character identity from ref1-ref5 + background images
- **FLF first/last frame conditioning** (nodes 52+53): LTXVImgToVideoInplace replaces leading latent frames with the first-frame image; LTXVAddGuide appends the last-frame image as a keyframe at frame_idx=40
- **Joint audio-video sampling** (nodes 23+16+24): LTXVConcatAVLatent + SamplerCustomAdvanced + LTXVSeparateAVLatent for combined video+audio generation
- **8-step distilled sigma schedule** (node 27): ManualSigmas with 9 values matching the validated LiconMSR production default

All placeholder values (`PLACEHOLDER_REF1`, `PLACEHOLDER_FIRST_FRAME`, etc.) are string literals the runner swaps per shot. The `_meta` key documents defaults: `flf_model_default: "ltx/fflf"`, `num_refs_default: 5`, `steps_default: 8`.

Based on the validated LiconMSR template from `ltx-video-workflows.md` line 506-592 (3/3 success 2026-06-28) with FLF additions per the FFLF workflow description at line 300.

### 2. Async Validation Runner Script (Task 2, commit `ba23bed`)

`scripts/run_ltx_flf_validation.py` — async runner with serial awaits (INFRA-04 compliant):

- **Pydantic v2 schema**: `ValidationReport` with `metadata`, `shots[]`, `operator_decision` (defaults: `verdict: null`, `rationale: null`, `lock_ready: false`)
- **ComfyUI flow**: `submit_comfyui` (POST /prompt) → `poll_comfyui` (GET /history/{pid}, 600s timeout) → `download_video` (GET /view, checks "videos" key FIRST per SaveVideo behavior)
- **Frame extraction**: `extract_frames` uses ffmpeg to extract first/middle/last frames; gracefully degrades (returns empty list) if ffmpeg missing
- **vision_verify integration**: `verify_identity_continuity` calls `vision_verify_fn` (injected for testability) on each of the 3 frames per shot; serial `await` per frame (INFRA-04)
- **Partial failure handling**: single-shot failure (ComfyUI error, timeout) is recorded in `ShotResult.error` and execution continues with other shots
- **Rich summary table**: per-shot gen_status + latency + identity confidence for first/middle/last frames
- **CLI**: `--reference-shots` (required), `--comfyui-url` (default :8188), `--flf-model` (default ltx/fflf), `--num-refs` (default 5), `--steps` (default 8), `--output-dir`, `--workflow-template`
- **Entry**: `asyncio.run(main_async())` per D-01 async pattern

### 3. Unit Tests (Task 2, commit `ba23bed`)

`tests/test_run_ltx_flf_validation.py` — 12 tests covering:

1. Schema defaults (operator_decision null/false)
2. Reference shots loading (valid)
3. Reference shots loading (missing file)
4. Workflow placeholder replacement (all 10 placeholders)
5. ComfyUI submit success (HTTP 200 → prompt_id)
6. ComfyUI submit failure (HTTP 500 → RuntimeError)
7. Full run_validation with mocked ComfyUI (1 shot, 3 vision_verify calls, gen_status=success)
8. Partial failure (shot 1 fails, shot 2 succeeds — both in report)
9. ffmpeg missing → empty frame list (graceful degradation)
10. vision_verify success (pass=True, confidence=0.9)
11. vision_verify failure (exception → pass=None, error message captured)
12. INFRA-04 compliance (no concurrent-dispatch string in source)

All 12 tests pass. Mocks: httpx.AsyncClient (async context manager), subprocess.run (ffmpeg), shutil.which, extract_frames.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed error return key mismatch in verify_identity_continuity**
- **Found during:** Task 2 (test run)
- **Issue:** The error path returned `{"passed": None, ...}` but the success path returned the raw vision_verify dict which uses `{"pass": None, ...}`. The key name was inconsistent.
- **Fix:** Changed error return to use `"pass"` key (matching vision_verify API contract)
- **Files modified:** `scripts/run_ltx_flf_validation.py`
- **Commit:** ba23bed

**2. [Rule 3 - Blocking] Fixed async context manager mock setup**
- **Found during:** Task 2 (test run)
- **Issue:** `httpx.AsyncClient` is used as `async with httpx.AsyncClient() as client:` — the mock needed `__aenter__` to return the client itself, not a new mock. Initial mock setup returned default MagicMock from `__aenter__`, causing all post/get calls to go to the wrong object.
- **Fix:** Added `mock_client.__aenter__ = AsyncMock(return_value=mock_client)` and `mock_client.__aexit__ = AsyncMock(return_value=None)` to both test methods
- **Files modified:** `tests/test_run_ltx_flf_validation.py`
- **Commit:** ba23bed

**3. [Rule 3 - Blocking] Removed literal string from docstrings/comments**
- **Found during:** Task 2 (test run)
- **Issue:** The `test_no_asyncio_gather_in_source` test asserts the literal string `"asyncio.gather"` does NOT appear in the runner source. The runner docstring + 2 comments contained the string when explaining INFRA-04 compliance.
- **Fix:** Rephrased docstring/comments to use "concurrent task dispatch" and "concurrent dispatch" instead of the literal function name
- **Files modified:** `scripts/run_ltx_flf_validation.py`
- **Commit:** ba23bed

## Verification Results

| Check | Result |
|-------|--------|
| Workflow JSON valid + all node types present | PASS (25 nodes, all acceptance criteria met) |
| Runner starts with `from __future__ import annotations` | PASS |
| Runner uses `httpx.AsyncClient` | PASS |
| `ValidationReport` schema matches D-03 | PASS (metadata + shots[] + operator_decision) |
| `OperatorDecision` defaults (null/null/false) | PASS |
| `--help` shows all required flags with correct defaults | PASS |
| `--comfyui-url` default = `http://127.0.0.1:8188` | PASS |
| `--flf-model` default = `ltx/fflf` | PASS |
| `--num-refs` default = 5 | PASS |
| `--steps` default = 8 | PASS |
| No concurrent-dispatch string in source (INFRA-04) | PASS |
| `main()` calls `asyncio.run(main_async())` | PASS |
| All `open()` calls include `encoding="utf-8"` (Ruff PLW1514) | PASS (2 text-mode opens, 1 binary) |
| Report JSON uses `ensure_ascii=False` | PASS |
| `extract_frames` returns empty list when ffmpeg missing | PASS |
| `run_validation` catches per-shot errors | PASS |
| Rich Table has correct columns | PASS |
| `download_video` checks "videos" key FIRST | PASS |
| pytest exits 0 (all 12 tests pass) | PASS |
| vision_verify called 3 times per shot | PASS (mock_vision_fn.call_count == 3) |
| Partial failure: both shots in report | PASS |

## Commits

| Commit | Repo | Message |
|--------|------|---------|
| `536c9a7` | kais-hermes-skills | feat(78-01): add ComfyUI workflow JSON for LTX-FLF+ICLoRA validation |
| `ba23bed` | kais-hermes-skills | feat(78-01): add async LTX-FLF validation runner + unit tests |

## Known Stubs

None. All functionality is fully wired:
- ComfyUI submission uses real httpx.AsyncClient HTTP calls
- Frame extraction uses real ffmpeg/ffprobe subprocess calls
- vision_verify uses real plugins.kais_aigc.vision_verify (lazily imported)
- Report JSON is fully structured with all fields populated

## Threat Flags

None. All threats from the plan's `<threat_model>` are mitigated as specified:
- T-78-01 (Tampering): `load_reference_shots` validates each shot subdir has required files
- T-78-04 (Tampering): `--flf-model` validates against `choices=["ltx/fflf", "singularityFFLF"]`
- T-78-06 (Tampering): `build_validation_workflow` deep-copies template before parameterization
- T-78-02/03/05 (DoS/Info Disclosure): accepted per plan (validation tool, operator-private, negligible cost)

## Self-Check: PASSED

- [x] `skills/kais-movie-pipeline/references/workflows/ltx-flf-iclora-validation.json` exists (FOUND)
- [x] `skills/kais-movie-pipeline/scripts/run_ltx_flf_validation.py` exists (FOUND)
- [x] `skills/kais-movie-pipeline/tests/test_run_ltx_flf_validation.py` exists (FOUND)
- [x] Commit `536c9a7` exists in kais-hermes-skills repo (FOUND)
- [x] Commit `ba23bed` exists in kais-hermes-skills repo (FOUND)
