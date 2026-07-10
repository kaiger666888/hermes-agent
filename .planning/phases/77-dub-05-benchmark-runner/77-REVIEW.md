---
phase: 77-dub-05-benchmark-runner
reviewed: 2026-07-10T12:30:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/lock_cosyvoice_default.py
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/test_run_cosyvoice_benchmark.py
  - /data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/test_lock_cosyvoice_default.py
findings:
  critical: 3
  warning: 9
  info: 6
  total: 18
status: issues_found
---

# Phase 77: Code Review Report

**Reviewed:** 2026-07-10T12:30:00Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Two CLI scripts (`run_cosyvoice_benchmark.py` — 951 lines, `lock_cosyvoice_default.py` — 381 lines) plus 2 test files (20 tests total). The implementation is functionally substantive and the Pydantic v2 schema, ComfyUI HTTP flow, and lock validation logic are well-structured. However, the adversarial review found 3 critical issues and 9 warnings.

The most severe finding (CR-01) is a control-flow bug where `check_silent()` or `compute_wer()` raising an exception (e.g. `FileNotFoundError` when ffmpeg is not installed) causes a VariantResult to be recorded with **both** `audio_path` set AND `error` set — an inconsistent state that misleads the operator into thinking the variant failed when the audio was actually generated successfully. Since `check_silent` does not catch `FileNotFoundError` or `subprocess.TimeoutExpired`, and the CLAUDE.md states ffmpeg is an optional dependency, this is a realistic failure path.

Two additional critical issues: (CR-02) `validate_lock()` crashes with `TypeError` when `operator_decision.variant` is a JSON array (unhashable type passed to `dict.get()`), and (CR-03) `write_lock()` performs a non-atomic write of VERSION.json with no backup — a crash mid-write corrupts the file that locks the entire TTS pipeline.

## Critical Issues

### CR-01: check_silent/compute_wer exceptions mark successful audio as failed

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py:647-738`
**Issue:** The `check_silent()` call (line 714) and `compute_wer()` call (line 721) are inside the same `try` block as the ComfyUI/gold-team submission and download. If `check_silent()` raises `FileNotFoundError` (ffmpeg not installed — CLAUDE.md lists ffmpeg as optional) or `subprocess.TimeoutExpired` (ffmpeg hangs), the `except Exception` at line 723 catches it, sets `error_msg = str(exc)`, and the VariantResult is recorded with **both** `audio_path` set (line 684/708 already executed) AND `error` set. This is an inconsistent state: the operator sees an error and may discard the variant, even though the audio file was successfully generated and downloaded.

The same applies to `compute_wer()` — if whisper transcription or `.txt` file reading raises an unexpected exception, the entire variant is marked as errored despite successful audio generation.

`check_silent()` at lines 401-406 does not catch `FileNotFoundError` or `subprocess.TimeoutExpired`:
```python
result = subprocess.run(
    ["ffmpeg", "-i", str(path), "-af", "volumedetect", "-f", "null", "/dev/null"],
    capture_output=True,
    text=True,
    timeout=15,
)  # raises FileNotFoundError if ffmpeg missing, TimeoutExpired if >15s
```

**Fix:** Move `check_silent()` and `compute_wer()` outside the main `try` block, or wrap them in their own try/except so their failures do not contaminate the variant's error status:

```python
# After the main try/except (submission + download):
if audio_path is not None:
    # Silent check — best-effort, does not affect error status
    try:
        if check_silent(audio_dest):
            logger.warning(
                "silent output detected for line=%s variant=%s",
                line_id, variant_id,
            )
    except Exception as exc:
        logger.warning("check_silent failed for %s: %s", audio_dest, exc)

    # WER — best-effort, does not affect error status
    try:
        wer = compute_wer(audio_dest, text)
    except Exception as exc:
        logger.warning("compute_wer failed for %s: %s", audio_dest, exc)
```

### CR-02: validate_lock crashes with TypeError on non-string variant (JSON array)

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/lock_cosyvoice_default.py:186-195`
**Issue:** `validate_lock()` checks `if variant_id is None or (isinstance(variant_id, str) and variant_id == "")` at line 187. If the operator writes `"variant": []` or `"variant": {}` in the JSON report (valid JSON), the check passes (not None, not a string). Then at line 195, `VARIANT_ID_MAP.get(variant_id, variant_id)` is called with an unhashable type (`[]` or `{}`), which raises `TypeError: unhashable type: 'list'`. This crashes the lock script with an unhandled exception instead of a clean validation error.

Similarly, if `variant_id` is an integer (e.g. `"variant": 123`), it passes Check 1 but `VARIANT_ID_MAP.get(123, 123)` works (hashable) and correctly fails Check 2. But list/dict variants crash.

**Fix:** Add a type check at the start of `validate_lock()`:

```python
variant_id = op_decision.get("variant")
if not isinstance(variant_id, (str, type(None))):
    errors.append(
        f"operator_decision.variant must be a string or null, "
        f"got {type(variant_id).__name__}"
    )
    variant_id = ""
elif variant_id is None or variant_id == "":
    errors.append(
        "operator_decision.variant is null — operator must fill the "
        "chosen variant in the report"
    )
    variant_id = variant_id or ""
```

### CR-03: write_lock performs non-atomic write of VERSION.json (data loss risk)

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/lock_cosyvoice_default.py:269-281`
**Issue:** `write_lock()` writes directly to `version_json_path` with `open("w")`. If the process crashes (SIGKILL, OOM, power loss) between truncation and the `json.dump` completing, VERSION.json is left empty or truncated. This file locks the entire TTS pipeline default variant — corruption means the pipeline cannot determine which CosyVoice model to use.

The same non-atomic write pattern exists in the runner at lines 930-935 (`benchmark_report.json`), but that is less critical since the report can be regenerated. VERSION.json corruption is a data-loss risk because it contains the operator's locked decision that cannot be auto-regenerated.

**Fix:** Use the atomic write pattern (write to temp file, then `os.replace`):

```python
import os
import tempfile

def write_lock(version_json_path: Path, variant_id: str, rationale: str) -> None:
    with version_json_path.open("r", encoding="utf-8") as f:
        version_json = json.load(f)

    mapped_id = VARIANT_ID_MAP.get(variant_id, variant_id)
    version_json["tts"]["cosyvoice_default_variant"] = mapped_id
    version_json["tts"]["lock_date"] = datetime.date.today().isoformat()
    version_json["tts"]["lock_rationale"] = rationale

    # Atomic write: temp file + os.replace
    dest_parent = version_json_path.parent
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=dest_parent,
        prefix=version_json_path.name + ".", suffix=".tmp",
        delete=False,
    ) as tmp_f:
        json.dump(version_json, tmp_f, ensure_ascii=False, indent=2)
        tmp_f.write("\n")
        tmp_path = Path(tmp_f.name)
    os.replace(tmp_path, version_json_path)
```

## Warnings

### WR-01: check_silent does not catch FileNotFoundError or TimeoutExpired

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py:401-412`
**Issue:** `subprocess.run(["ffmpeg", ...])` raises `FileNotFoundError` if ffmpeg is not on PATH and `subprocess.TimeoutExpired` if it exceeds 15s. Neither is caught. This is the root cause of CR-01 (the exception propagates to the outer `except Exception` and marks the variant as failed). Even if CR-01 is fixed by moving the call outside the try block, `check_silent` itself should handle these gracefully rather than relying on the caller.

**Fix:**
```python
def check_silent(path: Path) -> bool:
    try:
        result = subprocess.run(
            ["ffmpeg", "-i", str(path), "-af", "volumedetect", "-f", "null", "/dev/null"],
            capture_output=True, text=True, timeout=15,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        logger.warning("ffmpeg volumedetect failed for %s: %s", path, exc)
        return False  # assume non-silent (don't false-positive)
    match = re.search(r"mean_volume:\s+(-?\d+\.?\d*)\s*dB", result.stderr)
    if match:
        mean_vol = float(match.group(1))
        return mean_vol < -60.0
    return False
```

### WR-02: poll_comfyui and _poll_gold_team silently swallow all RequestException

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py:343-353, 527-539`
**Issue:** Both poll functions catch `requests.RequestException` with a bare `pass` — no logging. If ComfyUI or gold-team goes down mid-poll, the operator gets zero visibility. The runner appears to hang for up to 300 seconds with no indication of why. This makes operational troubleshooting very difficult.

**Fix:** Log the exception at debug or warning level:
```python
except requests.RequestException as exc:
    logger.debug("poll request failed (will retry): %s", exc)
```

### WR-03: _VARIANT_TO_VERSION_JSON is dead code (never referenced)

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py:106-112`
**Issue:** The `_VARIANT_TO_VERSION_JSON` dict is defined at module level but never referenced anywhere in the runner script or tests. It duplicates `VARIANT_ID_MAP` in `lock_cosyvoice_default.py` (verified identical). The docstring at line 106 says "Used for validation that runner variant IDs match the lock site" but no such validation is performed — the runner does not import or compare against the lock script's map.

**Fix:** Either remove the dead dict, or use it for cross-script validation (e.g. assert all VARIANTS keys are in the map at import time). If kept for documentation, add a comment explaining it is a reference table, not runtime code.

### WR-04: load_benchmark_report and load_version_json do not validate nested dict types

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/lock_cosyvoice_default.py:80-154`
**Issue:** `load_benchmark_report()` checks that `operator_decision` key exists (line 110) but does not validate it is a dict. If the JSON has `"operator_decision": "not decided yet"`, `validate_lock()` at line 175 calls `report.get("operator_decision", {}).get(...)` which works (`.get` on the string returns the default `{}`), but if the string is non-empty it would try `.get` on the string and raise `AttributeError`. Similarly, `load_version_json()` checks `tts` exists (line 148) but does not validate it is a dict — `write_lock()` at line 275 does `version_json["tts"]["cosyvoice_default_variant"] = ...` which raises `TypeError` if `tts` is a string or list.

**Fix:** Add type validation in both load functions:
```python
# In load_benchmark_report, after the operator_decision check:
if not isinstance(data.get("operator_decision"), dict):
    raise ValueError("operator_decision must be a JSON object")

# In load_version_json, after the tts check:
if not isinstance(data.get("tts"), dict):
    raise ValueError("tts must be a JSON object")
```

### WR-05: Gold-team task_id not unique across re-runs (collides with stale tasks)

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py:507`
**Issue:** `task_id = f"bench_{line_id}"` is deterministic. If the operator re-runs the benchmark with the same dialogue lines (common during iteration), the gold-team API may reject the duplicate task_id or return stale results from the previous run. The script does not handle this case. Additionally, `load_dialogue_lines()` does not check for duplicate `id` values — if two lines share the same `id`, they produce the same task_id.

**Fix:** Include a timestamp or UUID in the task_id:
```python
import uuid
_run_id = uuid.uuid4().hex[:8]

def _submit_gold_team(endpoint, line_id, text, timeout=15):
    task_id = f"bench_{_run_id}_{line_id}"
    ...
```

### WR-06: WER formula can exceed 1.0, contradicting docstring and Rich table display

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py:38-39, 438-494`
**Issue:** The docstring (line 38-39) says `WER = lev_distance(transcribed, reference) / len(reference)` and the `VariantResult.wer` field description (line 138) says "Word Error Rate (0.0-1.0)". But the formula `distance / len(reference)` can exceed 1.0 when the transcription has many extra characters (insertions). Verified: `_char_levenshtein("abcde", "ab") / len("ab") = 3/2 = 1.5`. The Rich summary table at line 819 shows `f"{avg_wer:.1f}%"` which would display "150.0%" — confusing for the operator.

Additionally, this is character-level error rate (CER), not word error rate (WER). For Chinese this is arguably the right metric (no word boundaries), but the naming is misleading.

**Fix:** Either clamp the value to 1.0 and rename to `cer` (Character Error Rate), or update the docstring to acknowledge the range can exceed 1.0:
```python
wer = min(distance / len(reference_text), 1.0)  # clamp to [0.0, 1.0]
```

### WR-07: lock_date uses local date, runner timestamp uses UTC (timezone inconsistency)

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/lock_cosyvoice_default.py:276` vs `run_cosyvoice_benchmark.py:749`
**Issue:** `write_lock()` uses `datetime.date.today().isoformat()` (local date) for `lock_date`, while the runner uses `datetime.now(timezone.utc).strftime(...)` (UTC) for the benchmark `timestamp`. If the operator runs the lock script late in the day in a timezone ahead of UTC, the lock_date may be one day ahead of the benchmark timestamp, creating an inconsistent audit trail.

**Fix:** Use UTC date for consistency:
```python
from datetime import datetime, timezone
version_json["tts"]["lock_date"] = datetime.now(timezone.utc).date().isoformat()
```

### WR-08: metadata.dialogue_lines_file records copied path, not original input path

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py:752`
**Issue:** `BenchmarkMetadata.dialogue_lines_file` is set to `str(output_dir / "dialogue_lines_source.json")` — the path to the copied file inside the output directory, not the original `--dialogue-lines` argument. The operator cannot trace back which input file was used without inspecting the copy's content. The field name suggests it records the source file path.

**Fix:** Record the original input path:
```python
# Pass the original dialogue_lines_path into run_benchmark, or record it in main():
dialogue_lines_file=str(dialogue_lines_path),  # original input, not the copy
```

### WR-09: Gold-team pre-check is redundant — each line re-checks reachability

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py:614-625, 690-693`
**Issue:** The pre-check loop (lines 614-625) calls `_check_gold_team_reachable(endpoint)` once per gold-team variant and logs a warning if unreachable. But it does not skip the variant — the main loop at line 690 calls `_check_gold_team_reachable(endpoint)` **again** for every dialogue line. For N lines x 1 gold-team variant, that's N+1 reachability checks instead of 1. Each check is an HTTP GET to `/api/v1/engines`.

**Fix:** Either cache the reachability result from the pre-check and skip redundant calls, or remove the per-line check and rely solely on the pre-check (raising early if unreachable). The pre-check should set a flag that the main loop consults:
```python
gold_team_unreachable: set[str] = set()
# In pre-check:
if not _check_gold_team_reachable(endpoint):
    gold_team_unreachable.add(variant_id)

# In main loop:
if variant_id in gold_team_unreachable:
    raise RuntimeError(f"gold-team unreachable at {endpoint} (pre-check failed)")
```

## Info

### IN-01: Redundant `import shutil as shutil_mod` inside main()

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py:904`
**Issue:** `shutil` is already imported at module level (line 49). The local `import shutil as shutil_mod` at line 904 is redundant and uses a confusing alias. It works (same module object), but violates the codebase convention of explicit imports without aliasing.
**Fix:** Replace `shutil_mod.copy2(...)` with `shutil.copy2(...)` and remove the local import.

### IN-02: /dev/null hardcoded in ffmpeg command (POSIX-only)

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py:402`
**Issue:** `["ffmpeg", "-i", str(path), "-af", "volumedetect", "-f", "null", "/dev/null"]` hardcodes `/dev/null` which is POSIX-only. On Windows, the equivalent is `NUL` or `-f null -`. However, this mirrors the established pattern in `gold-team-tts-batch.py` (the reference script), and ComfyUI runs on Linux in practice. The CLAUDE.md states cross-platform is first-class, but this subsystem is Linux-specific.
**Fix:** Use `-f null -` (portable across platforms) or document that this script requires POSIX.

### IN-03: prompt_id and filename not URL-encoded in ComfyUI HTTP paths

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py:344, 374`
**Issue:** `f"{url}/history/{prompt_id}"` and `f"{url}/view?filename={filename}&subfolder={subfolder}&type={file_type}"` do not URL-encode `prompt_id`, `filename`, `subfolder`, or `file_type`. These come from ComfyUI API responses (untrusted). If they contain spaces, `&`, `#`, or `/`, the URL is malformed. This is primarily a correctness issue (wrong file fetched), not a security issue, since `requests.get` doesn't shell-execute.
**Fix:** Use `urllib.parse.quote` for path segments and `urllib.parse.urlencode` for query params:
```python
from urllib.parse import quote, urlencode
resp = requests.get(f"{url}/history/{quote(prompt_id, safe='')}", timeout=10)
params = urlencode({"filename": filename, "subfolder": subfolder, "type": file_type})
download_url = f"{url}/view?{params}"
```

### IN-04: _download_gold_team_audio file:// path not validated (path traversal defense-in-depth)

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py:552-554`
**Issue:** `src = audio_url.replace("file://", "")` followed by `shutil.copy2(src, dest_path)` copies whatever path the gold-team API returns. If the API is compromised or returns an unexpected path (e.g. `file:///etc/passwd`), arbitrary files are copied to the output directory. The gold-team API is trusted (localhost:8002), so this is defense-in-depth, not an active vulnerability.
**Fix:** Validate the source path is within an expected directory (e.g. `/tmp/gold-team-outputs/`):
```python
src = audio_url.replace("file://", "")
src_path = Path(src).resolve()
allowed_root = Path("/tmp/gold-team-outputs")  # or wherever gold-team writes
if not str(src_path).startswith(str(allowed_root)):
    raise RuntimeError(f"gold-team audio path outside allowed root: {src_path}")
```

### IN-05: Test coverage gaps — gold-team backend, error paths, and main() entry points untested

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/tests/test_run_cosyvoice_benchmark.py` and `test_lock_cosyvoice_default.py`
**Issue:** The following paths have no test coverage:
1. Gold-team backend (`_submit_gold_team`, `_poll_gold_team`, `_download_gold_team_audio`) — entirely untested
2. `submit_comfyui` error path (non-200 response) — untested
3. `poll_comfyui` timeout (returns None) — untested
4. `check_silent` no-match path (regex fails, returns False) — untested
5. `compute_wer` happy path (whisper available, produces transcription) — untested
6. Both `main()` CLI entry points — no integration tests
7. `load_version_json` — untested directly

**Fix:** Add tests for each listed path. The gold-team backend tests are most critical since they involve HTTP I/O and file copying that could fail silently.

### IN-06: emit_rich_summary avg_wer can display >100% (no clamping)

**File:** `/data/workspace/kais-hermes-skills/skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py:811-819`
**Issue:** If WER values exceed 1.0 (see WR-06), the Rich summary table shows `f"{avg_wer:.1f}%"` which could display "150.0%". This is confusing for the operator. The column header "Avg WER %" implies 0-100%.
**Fix:** Clamp `avg_wer` to 100.0 max for display, or fix the WER formula per WR-06.

---

_Reviewed: 2026-07-10T12:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
