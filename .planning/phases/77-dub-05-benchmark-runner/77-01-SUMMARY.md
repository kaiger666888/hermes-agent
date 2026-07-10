---
phase: 77-dub-05-benchmark-runner
plan: 01
subsystem: audio_pipeline
tags: [dub-05, cosyvoice, benchmark, comfyui, tts, operator-action-closure]
requires:
  - VERSION.json tts block (alternative_tested[] + lock site)
  - cosyvoice-comfyui.json workflow template
  - ComfyUI running at http://127.0.0.1:8188 (operator-action)
provides:
  - CosyVoice A/B benchmark runner script (run_cosyvoice_benchmark.py)
  - Structured JSON report schema {metadata, lines[], operator_decision}
  - Per-variant WER/latency comparison Rich table
affects:
  - VERSION.json tts.cosyvoice_default_variant (locked by Plan 77-02 lock script)
  - cosyvoice-benchmark.md (operator fills with audio quality judgment)
tech-stack:
  added:
    - Pydantic v2 BaseModel schema (BenchmarkReport + 4 sub-models)
    - Rich Table CLI summary (mirror dreamina_stats.py pattern)
    - ffmpeg volumedetect silent-output detection (mirror gold-team-tts-batch.py)
    - Whisper CN character-level Levenshtein WER (stdlib, no external NLP lib)
  patterns:
    - Sync-only execution (INFRA-04 compliant — no async/await, uses requests not httpx.AsyncClient)
    - Per-cell error handling (partial results preserved, no crash on single-variant failure)
    - ComfyUI /prompt submit + /history poll + /view download pattern
    - Gold-team HTTP API adapter (backend field in VARIANTS dict)
key-files:
  created:
    - skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py
    - skills/movie-experts/audio_pipeline/tests/test_run_cosyvoice_benchmark.py
  modified: []
decisions:
  - CLI variant IDs use underscores (cosyvoice_2_0_0_5b) for shell-safety; mapped to VERSION.json dots (cosyvoice_2.0_0.5B) via _VARIANT_TO_VERSION_JSON dict
  - Gold-team variant uses backend="gold_team" with HTTP API adapter, not ComfyUI workflow
  - WER computed via character-level Levenshtein (stdlib DP, no external NLP lib)
  - Report JSON uses json.dumps with ensure_ascii=False for Chinese text preservation
metrics:
  duration: 373s
  tasks: 2
  files: 2
  commits: 3
  completed: 2026-07-10
---

# Phase 77 Plan 01: CosyVoice A/B Benchmark Runner Summary

CosyVoice A/B benchmark runner script that submits N dialogue lines x M variants to ComfyUI (or gold-team HTTP API), captures audio + latency + WER, and writes a structured JSON report for operator review — turning the DUB-05 operator-action handoff from a research project into a 5-minute CLI task.

## What Was Built

### Task 1: Benchmark Runner Script (`run_cosyvoice_benchmark.py`)

**951-line sync-only Python script** implementing the full DUB-05-RUNNER contract:

- **VARIANTS dict** — 3 variant IDs mapping to backends:
  - `cosyvoice_2_0_0_5b` → ComfyUI backend, model_dir `cosyvoice_2.0_0.5B` (legacy, verify at run)
  - `fun_cosyvoice_3_0` → ComfyUI backend, model_dir `/root/ComfyUI/models/cosyvoice/Fun-CosyVoice3-0.5B-2512`
  - `cosyvoice_300M_gold_team` → Gold-team HTTP API backend at `http://127.0.0.1:8002`

- **Pydantic v2 report schema** (5 models, all `ConfigDict(extra="forbid")`):
  - `BenchmarkMetadata` — timestamp, variants, comfyui_url, dialogue_lines_file, wer_available
  - `VariantResult` — variant, audio_path, latency_ms, wer, error (per-variant per-line)
  - `LineResult` — line_id, text, emotion, speaker, variants[]
  - `OperatorDecision` — variant (null), rationale (null), lock_ready (false)
  - `BenchmarkReport` — metadata, lines[], operator_decision

- **Core functions**:
  - `load_dialogue_lines()` — validates JSON array with id/text/emotion/speaker keys
  - `build_comfyui_workflow()` — clones cosyvoice-comfyui.json 4-node template, parameterizes model_dir
  - `submit_comfyui()` + `poll_comfyui()` + `download_audio()` — ComfyUI HTTP pattern
  - `check_silent()` — ffmpeg volumedetect, mean_volume < -60 dB = silent
  - `compute_wer()` — Whisper CN transcription + character-level Levenshtein (stdlib DP)
  - `run_benchmark()` — main loop with per-cell error handling (partial results preserved)
  - `emit_rich_summary()` — Rich Table with Variant/Lines OK/Avg Latency/Avg WER/Errors columns
  - `main()` — argparse CLI with --dialogue-lines, --variants, --comfyui-url, --reference-audio, --output-dir

- **Gold-team adapter** — `_submit_gold_team()`, `_poll_gold_team()`, `_download_gold_team_audio()` for the 300M variant; auto-detects reachability and warns if requested but unreachable

### Task 2: Unit Tests (`test_run_cosyvoice_benchmark.py`)

**9 tests in `TestRunCosyVoiceBenchmark` class**, all passing with mocked dependencies (no real network calls):

1. `test_load_dialogue_lines_valid` — accepts valid JSON array with all required keys
2. `test_load_dialogue_lines_missing_key` — raises ValueError with specific missing key name
3. `test_benchmark_report_schema_defaults` — operator_decision.variant=None, lock_ready=False
4. `test_run_benchmark_mocked_comfyui` — full happy path with mocked ComfyUI (1 line x 1 variant)
5. `test_run_benchmark_partial_failure` — 2 variants, one fails, other succeeds (partial results)
6. `test_compute_wer_no_whisper` — returns None when `shutil.which("whisper")` is None
7. `test_check_silent_detects_silent` — mean_volume -65.0 dB → True
8. `test_check_silent_detects_non_silent` — mean_volume -20.0 dB → False
9. `test_build_comfyui_workflow_parameterizes_model_dir` — node "1" model_dir set correctly

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Python 3.12 deprecation warning for datetime.utcnow()**
- **Found during:** Task 2 test run
- **Issue:** `datetime.utcnow()` is deprecated in Python 3.12+ and emits a DeprecationWarning
- **Fix:** Changed to `datetime.now(timezone.utc)` with `from datetime import datetime, timezone` import
- **Files modified:** `scripts/run_cosyvoice_benchmark.py` (2 lines)
- **Commit:** `9f7cde5`

### Implementation Notes

- **sys.path bootstrap for tests:** The `skills/movie-experts/` directory uses a hyphen in its name, making it non-importable as a Python package. The test file adds `scripts/` directory directly to `sys.path` to import `run_cosyvoice_benchmark` as a top-level module (mirrors how `gold-team-tts-batch.py` is a standalone script, not a package module).
- **CLI variant ID mapping:** Runner uses underscored CLI IDs (`cosyvoice_2_0_0_5b`) for shell-safety, mapped to VERSION.json dotted IDs (`cosyvoice_2.0_0.5B`) via `_VARIANT_TO_VERSION_JSON` dict. All 3 runner variant IDs verified against `VERSION.json alternative_tested[]`.

## Commits

| Hash | Message | Files |
|------|---------|-------|
| `8ec6352` | feat(77-01): add CosyVoice A/B benchmark runner script | `scripts/run_cosyvoice_benchmark.py` |
| `9f7cde5` | fix(77-01): replace deprecated datetime.utcnow() with timezone-aware now() | `scripts/run_cosyvoice_benchmark.py` |
| `4f73897` | test(77-01): add unit tests for CosyVoice benchmark runner | `tests/test_run_cosyvoice_benchmark.py` |

## Verification Results

- `--help` output shows all 5 flags (--dialogue-lines, --variants, --comfyui-url, --reference-audio, --output-dir)
- `--comfyui-url` default is `http://127.0.0.1:8188` (env fallback `COMFYUI_URL`)
- No `async`/`await` code keywords in the script (INFRA-04 compliant)
- All text-mode `open()` calls have `encoding="utf-8"` (Ruff PLW1514 compliant)
- Binary-mode `open("wb")` calls correctly omit encoding (binary writes)
- Report JSON uses `ensure_ascii=False` (Chinese text preserved)
- `compute_wer` returns `None` when `shutil.which("whisper")` is `None`
- `check_silent` regex `mean_volume:\s+(-?\d+\.?\d*)\s*dB` matches acceptance criteria
- `run_benchmark` catches per-variant errors and records them in `VariantResult.error`
- Rich Table summary has 5 columns: Variant, Lines OK, Avg Latency (ms), Avg WER %, Errors
- All 3 runner variant IDs match VERSION.json `alternative_tested[]` entries
- All 9 unit tests pass (0.22s, zero warnings)

## Self-Check: PASSED

All created files exist. All 3 commits verified in git log.
