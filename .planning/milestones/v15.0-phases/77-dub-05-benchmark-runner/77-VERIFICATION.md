---
phase: 77-dub-05-benchmark-runner
verified: 2026-07-10T12:00:00Z
status: passed
score: 9/9 must-haves verified
overrides_applied: 0
---

# Phase 77: DUB-05 Benchmark Runner Verification Report

**Phase Goal:** Operator can execute a side-by-side A/B benchmark of CosyVoice 2.0-0.5B vs Fun-CosyVoice 3.0 on representative dialogue lines, review structured output, and lock the chosen variant in VERSION.json with captured rationale.
**Verified:** 2026-07-10T12:00:00Z
**Status:** passed
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | Operator can run `python scripts/run_cosyvoice_benchmark.py --dialogue-lines <file> --variants cosyvoice_2_0_0_5b,fun_cosyvoice_3_0` and get structured JSON report + audio files | VERIFIED | `--help` output shows `--dialogue-lines` (required) + `--variants` (required) + `--comfyui-url` + `--reference-audio` + `--output-dir` flags. Script is 951 lines, substantive implementation. `main()` writes `benchmark_report.json` + audio files to output dir. `run_benchmark_mocked_comfyui` test verifies end-to-end flow produces report with audio_path set. |
| 2 | Report has top-level structure {metadata, lines[], operator_decision} with operator_decision starting as {variant: null, rationale: null, lock_ready: false} | VERIFIED | Pydantic v2 models: `BenchmarkReport` has `metadata`, `lines`, `operator_decision` fields. `OperatorDecision` has `variant: str \| None = None`, `rationale: str \| None = None`, `lock_ready: bool = False`. `test_benchmark_report_schema_defaults` asserts all 3 defaults. Behavioral spot-check confirmed schema instantiation works. |
| 3 | Audio files are named {line_id}_{variant}.wav in runs/cosyvoice-benchmarks/{timestamp}/ directory | VERIFIED | `run_benchmark()` line 639: `audio_filename = f"{line_id}_{variant_id}.wav"`. `main()` default output dir: `Path("runs/cosyvoice-benchmarks") / timestamp` where timestamp = `datetime.now().strftime("%Y%m%d-%H%M%S")`. |
| 4 | WER is computed via Whisper CN if whisper CLI available, else wer: null (graceful skip) | VERIFIED | `compute_wer()` line 451: `if shutil.which("whisper") is None: return None`. Character-level Levenshtein via `_char_levenshtein()` stdlib DP. `test_compute_wer_no_whisper` asserts None return when whisper missing. |
| 5 | If a single variant fails for a single line, error is logged in that cell and execution continues | VERIFIED | `run_benchmark()` lines 723-728: `except Exception as exc: error_msg = str(exc); logger.error(...)`. VariantResult recorded with error set, loop continues. `test_run_benchmark_partial_failure` verifies one variant fails (error set, audio_path None) while other succeeds (error None, audio_path set). |
| 6 | Runner prints Rich summary table (per-variant WER/latency comparison) after completion | VERIFIED | `emit_rich_summary()` lines 766-823: Rich Table with columns "Variant", "Lines OK", "Avg Latency (ms)", "Avg WER %", "Errors". `main()` calls `emit_rich_summary(report)` at line 938. |
| 7 | Operator can run `python scripts/lock_cosyvoice_default.py --benchmark-report <path>` to lock chosen variant in VERSION.json | VERIFIED | `--help` output shows `--benchmark-report` (required) + `--version-json` (default to repo VERSION.json) + `--force` flags. Script is 381 lines, substantive. `main()` calls `validate_lock()` then `write_lock()`. Behavioral spot-check: write_lock writes mapped variant ID + ISO date + rationale to VERSION.json. |
| 8 | Lock script refuses if variant is null, not in alternative_tested[], not actually benchmarked, or lock_ready is false | VERIFIED | `validate_lock()` implements 4 checks: (0) lock_ready guard, (1) non-null variant, (2) in alternative_tested, (3) actually benchmarked. All-null operator_decision produces 3 errors (verified by behavioral spot-check + `test_validate_lock_refuses_null_variant`). Separate tests cover each refusal path. |
| 9 | Lock script does NOT auto-pick-lower-WER -- operator decision required | VERIFIED | No `--variant` CLI flag (confirmed via --help output). `validate_lock()` reads variant from `report["operator_decision"]["variant"]` only. Source code scan for auto-pick patterns (`min(`, `sort by wer`, `lowest wer`, `auto.pick`, `best_wer`, `min_wer`) found zero matches. DESCRIPTION in argparse states "Does NOT auto-pick-lower-WER -- operator decision is required." |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `scripts/run_cosyvoice_benchmark.py` | CosyVoice A/B benchmark runner | VERIFIED | 951 lines. Exists, substantive (full implementation: Pydantic schema, ComfyUI submit/poll/download, gold-team adapter, WER, Rich table, argparse CLI). Wired (main entry point, test imports). |
| `scripts/lock_cosyvoice_default.py` | VERSION.json lock script | VERIFIED | 381 lines. Exists, substantive (load_benchmark_report, load_version_json, validate_lock with 4 checks, check_overwrite_guard, write_lock with 3-field scope, main). Wired (main entry point, test imports). |
| `tests/test_run_cosyvoice_benchmark.py` | Unit tests for runner | VERIFIED | 338 lines, 9 tests in TestRunCosyVoiceBenchmark class. All pass. |
| `tests/test_lock_cosyvoice_default.py` | Unit tests for lock script | VERIFIED | 359 lines, 11 tests in TestLockCosyVoiceDefault class. All pass. |
| `references/voicer/cosyvoice-benchmark.md` | Extended with Runner Usage section | VERIFIED | `## Runner Usage` section exists (1 match). Contains 4 step subsections (Step 1-4) + Report JSON Schema subsection. Positioned after `## Default Lock Decision` (line 88) and before `## Open Questions (v15+)` (line 224). |
| `VERSION.json` | Lock fields still null (operator-action handoff) | VERIFIED | `cosyvoice_default_variant: null`, `lock_date: null`, `lock_rationale: null`. Operator must run benchmark + lock script to populate. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `run_cosyvoice_benchmark.py` | ComfyUI /prompt endpoint | `requests.post` to `{url}/prompt` | WIRED | Line 312: `requests.post(f"{url}/prompt", json={"prompt": workflow}, ...)`. Returns prompt_id. |
| `run_cosyvoice_benchmark.py` | cosyvoice-comfyui.json workflow template | parameterized model_dir per variant | WIRED | `build_comfyui_workflow()` sets node "1" inputs.model_dir. VARIANTS dict maps each variant to its model_dir. `test_build_comfyui_workflow_parameterizes_model_dir` verifies. |
| `run_cosyvoice_benchmark.py` | VERSION.json alternative_tested[] | variant IDs must match | WIRED | `_VARIANT_TO_VERSION_JSON` maps CLI IDs to VERSION.json IDs. All 3 mapped IDs verified present in VERSION.json alternative_tested[] via behavioral spot-check. |
| `lock_cosyvoice_default.py` | benchmark_report.json operator_decision.variant | reads JSON report | WIRED | `validate_lock()` reads `report["operator_decision"]["variant"]`. No `--variant` flag. |
| `lock_cosyvoice_default.py` | VERSION.json tts.cosyvoice_default_variant | writes lock block | WIRED | `write_lock()` line 275: `version_json["tts"]["cosyvoice_default_variant"] = mapped_id`. Behavioral spot-check confirmed write. |
| `lock_cosyvoice_default.py` | VERSION.json tts.alternative_tested[] | validates variant is in list | WIRED | `validate_lock()` Check 2: `if mapped_id not in alternative_tested: errors.append(...)`. `test_validate_lock_refuses_variant_not_in_alternative_tested` verifies. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `run_cosyvoice_benchmark.py` | BenchmarkReport | ComfyUI /prompt + /history + /view HTTP calls | Yes (mocked in tests, real ComfyUI at runtime) | FLOWING |
| `lock_cosyvoice_default.py` | variant_id + rationale | benchmark_report.json operator_decision | Yes (operator fills after audio review) | FLOWING |
| `lock_cosyvoice_default.py` | VERSION.json lock block | write_lock() writes 3 fields | Yes (verified via behavioral spot-check) | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Runner --help shows required flags | `python3 run_cosyvoice_benchmark.py --help` | Shows --dialogue-lines, --variants, --comfyui-url, --reference-audio, --output-dir | PASS |
| Lock --help shows required flags | `python3 lock_cosyvoice_default.py --help` | Shows --benchmark-report, --version-json, --force (no --variant) | PASS |
| Report schema defaults correct | Python instantiation + assertion | operator_decision.variant=None, rationale=None, lock_ready=False | PASS |
| Variant IDs match VERSION.json alternative_tested[] | Python cross-check | All 3 CLI IDs map to IDs present in alternative_tested[] | PASS |
| All-null operator_decision produces 3+ errors | validate_lock() call | 3 errors (lock_ready, variant, rationale) | PASS |
| Valid decision passes validation | validate_lock() call | errors == [] | PASS |
| No auto-pick-lower-WER logic | Source code scan | Zero matches for auto-pick patterns | PASS |
| write_lock writes exactly 3 fields | Temp VERSION.json write + re-read | 3 fields written, alternative_tested + benchmark_report_path unchanged | PASS |
| VERSION.json lock fields still null | JSON load + print | cosyvoice_default_variant=null, lock_date=null, lock_rationale=null | PASS |
| All 20 unit tests pass | `python3 -m pytest` | 20 passed in 0.23s | PASS |

### Probe Execution

No probes declared in PLAN or SUMMARY. Step 7c SKIPPED (no probe scripts in this phase).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| DUB-05-RUNNER | 77-01 | User can run `python scripts/run_cosyvoice_benchmark.py --dialogue-lines <file> --variants cosyvoice_2_0_0_5b,fun_cosyvoice_3_0` to execute side-by-side A/B benchmark; outputs structured JSON report + audio files | SATISFIED | Script exists, --help confirms flags, 9 unit tests pass, behavioral spot-checks confirm schema + variant ID alignment + partial failure handling + WER graceful skip |
| DUB-05-LOCK | 77-02 | User can run `python scripts/lock_cosyvoice_default.py --benchmark-report <path>` to lock chosen variant in VERSION.json with rationale (NOT auto-pick-lower-WER) | SATISFIED | Script exists, --help confirms flags (no --variant), 11 unit tests pass, behavioral spot-checks confirm 4-check validation + overwrite guard + 3-field write scope + no auto-pick-WER |

No orphaned requirements. REQUIREMENTS.md traceability table maps DUB-05-RUNNER and DUB-05-LOCK to Phase 77, both marked Complete.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | - | - | - | No TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER found in any phase-modified file. No async/await keywords (INFRA-04 compliant). All open() calls have encoding="utf-8" (Ruff PLW1514 compliant). |

### Human Verification Required

No human verification items blocking this phase. The phase delivers tooling for an operator-action handoff -- the actual benchmark execution + audio quality judgment + lock decision are operator actions that occur AFTER this phase ships, not verification gates for the phase itself. The scripts are verified to work correctly via mocked tests; real ComfyUI execution is an operator runtime action.

### Gaps Summary

No gaps found. All 9 must-have truths verified. All 6 artifacts exist, are substantive, and are wired. All 6 key links connected. Both requirement IDs (DUB-05-RUNNER, DUB-05-LOCK) satisfied. 20/20 tests pass. No anti-patterns detected.

The phase goal -- "Operator can execute a side-by-side A/B benchmark... review structured output, and lock the chosen variant in VERSION.json with captured rationale" -- is fully achieved at the tooling level. The actual benchmark execution + lock decision are operator runtime actions that depend on ComfyUI availability and human audio quality judgment, which are by design out of scope for automated verification.

---

_Verified: 2026-07-10T12:00:00Z_
_Verifier: Claude (gsd-verifier)_
