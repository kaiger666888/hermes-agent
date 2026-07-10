---
phase: 79-img-09-vision-verify-calibration
reviewed: 2026-07-10T14:30:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/calibrate_vision_verify.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/scripts/apply_vision_verify_thresholds.py
  - /data/workspace/kais-hermes-skills/plugins/kais_aigc/vision_verify.py
  - /data/workspace/kais-hermes-skills/plugins/kais_aigc/dreamina_manager.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_calibrate_vision_verify.py
  - /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/tests/test_apply_vision_verify_thresholds.py
findings:
  critical: 2
  warning: 5
  info: 3
  total: 10
status: issues_found
---

# Phase 79: Code Review Report

**Reviewed:** 2026-07-10T14:30:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Phase 79 (IMG-09 Vision-Verify Calibration) implements two new scripts (calibrate + apply) and modifies two existing files (vision_verify.py + dreamina_manager.py) to support per-stratum confidence thresholds.

The backward-compatibility design in `vision_verify.py` is solid: `get_threshold(None)` returns 0.7, the `stratum` param is optional on all public functions, and config-read failures never break the mandatory gate. The dreamina_manager wiring is a minimal one-line change at the call site. The calibration math (bimodal valley detection) is correct for the intended use case.

However, two BLOCKER-level issues were found:
1. `write_config()` crashes with an unhandled `AttributeError`/`TypeError` when `config.yaml` has `vision_verify` set to a non-mapping value (e.g., a string), and `main()` does not catch these exception types.
2. `estimate_fp_rate()` treats `success=None` (unknown status) as a false positive due to a truthiness check, inflating the estimated FP rate.

Additionally, an empty thresholds dict passes validation silently, and the `total_entries` field in the calibration report undercounts when the metrics buffer exceeds 1000 entries (ring buffer limit).

## Critical Issues

### CR-01: write_config() crashes on malformed config.yaml (unhandled AttributeError/TypeError)

**File:** `apply_vision_verify_thresholds.py:322-344`
**Issue:** The `write_config()` function assumes `config.get("vision_verify")` returns a ruamel CommentedMap (or None). If the existing `config.yaml` has `vision_verify` set to a scalar string, list, or any non-mapping type, the function crashes:

- Line 324: `existing_thresholds = existing_vv.get("thresholds")` raises `AttributeError` (strings have no `.get()` method).
- Line 337: `vv = config["vision_verify"]` returns the string, then line 340: `vv.get("thresholds")` or line 343: `vv["thresholds"] = ...` raises `AttributeError` or `TypeError`.

The `main()` function at line 502 only catches `(OSError, ValueError)`:
```python
except (OSError, ValueError) as exc:
    print(f"ERROR: failed to write config: {exc}", file=sys.stderr)
    return 1
```

`AttributeError` and `TypeError` escape this handler, producing an unhandled traceback instead of a clean error message.

**Fix:** Extend the exception handler in `main()` to catch `AttributeError` and `TypeError`, or add a type check in `write_config()`:

```python
# Option A: Extend main() exception handler (line 502)
except (OSError, ValueError, TypeError, AttributeError) as exc:
    print(f"ERROR: failed to write config: {exc}", file=sys.stderr)
    return 1

# Option B: Add type guard in write_config() after loading config (line 322)
existing_vv = config.get("vision_verify")
if existing_vv is not None and not hasattr(existing_vv, "get"):
    raise ValueError(
        f"config.yaml has 'vision_verify' set to {type(existing_vv).__name__}, "
        f"expected a mapping/dict — please fix config.yaml before applying"
    )
```

### CR-02: estimate_fp_rate() counts success=None as false positive (inflated FP rate)

**File:** `calibrate_vision_verify.py:330`
**Issue:** The FP rate formula uses `if not entry.get("success", True):` to count false positives. The `default=True` only applies when the `success` key is entirely missing. When `success` is explicitly `None` (which the `DreaminaTaskMetrics` schema does NOT prohibit — it's a `bool` field but `read_metrics` does not validate on read), `not None` evaluates to `True`, counting the entry as a false positive.

This inflates the estimated FP rate, which the operator uses to decide whether to apply the recommended threshold. A confidence entry with unknown success status (`None`) should not be counted as a false positive — it should be excluded from both the numerator and denominator.

The same issue applies to other falsy non-boolean values: `success=0` (int), `success=""` (empty string), `success=False` (correct), etc. While the schema says `success: bool`, `read_metrics` skips schema validation on read, so corrupted or manually-edited JSONL entries with non-boolean `success` values can reach this function.

**Fix:** Use explicit `is False` check instead of truthiness:

```python
# Line 330: Replace truthiness check with explicit False check
if entry.get("success") is False:
    fp_count += 1
```

This ensures only explicit `success=False` entries are counted as FPs. Entries with `success=None`, missing `success`, or non-boolean types are excluded from the FP count (but still counted in the denominator if above threshold, which is the conservative choice).

Alternatively, to also exclude `None` from the denominator:

```python
for entry in entries:
    conf = entry.get("vision_confidence")
    success = entry.get("success")
    if conf is None or success is None:
        continue
    if conf >= threshold:
        above_threshold += 1
        if success is False:
            fp_count += 1
```

## Warnings

### WR-01: Empty thresholds dict passes validation silently

**File:** `apply_vision_verify_thresholds.py:175`
**Issue:** When `operator_decision.thresholds` is an empty dict `{}`, the `validate_thresholds()` function passes it through with 0 errors. The `isinstance(thresholds, dict)` check at line 175 succeeds for an empty dict, and the `for key, val in thresholds.items()` loop at line 184 simply doesn't execute. The `coerced` dict stays empty, `thresholds = coerced` (empty), and no errors are appended.

This would result in `write_config()` writing an empty `thresholds:` block to `config.yaml`, which is almost certainly not the operator's intent. An empty thresholds dict should be flagged as a validation error.

**Fix:** Add an emptiness check after the dict type check:

```python
if not isinstance(thresholds, dict):
    errors.append(...)
    thresholds = {}
elif len(thresholds) == 0:
    errors.append(
        "operator_decision.thresholds is an empty dict — operator must "
        "fill at least one stratum -> threshold mapping"
    )
    thresholds = {}
```

### WR-02: total_entries undercounts when metrics buffer exceeds ring buffer limit

**File:** `calibrate_vision_verify.py:435, 448`
**Issue:** `run_calibration()` calls `load_metrics_buffer(metrics_path)` which calls `read_metrics(path)`. The `read_metrics` function (in `dreamina_stats.py:112`) returns only the last `limit=1000` entries (ring buffer semantic). The calibration report then sets `total_entries=len(all_entries)` at line 448, which is `min(actual_file_lines, 1000)`.

If the metrics file has 5000 entries, the report says `total_entries: 1000`, misleading the operator into thinking only 1000 entries exist. The per-stratum sample sizes are also based on only the last 1000 entries, which may not be representative of the full production history.

**Fix:** Either pass `limit=None` (or a large number) to `read_metrics` when loading for calibration, or add a separate field for actual file line count:

```python
# Option A: Read all entries (remove ring buffer limit for calibration)
def load_metrics_buffer(path: Path) -> list[dict[str, Any]]:
    from plugins.kais_aigc.dreamina_stats import read_metrics
    if not path.exists():
        raise FileNotFoundError(...)
    return read_metrics(path, limit=10**9)  # effectively unlimited

# Option B: Add actual_file_entries to metadata
actual_count = sum(1 for _ in path.open("r", encoding="utf-8"))
metadata = CalibrationMetadata(
    ...
    total_entries=actual_count,  # actual file lines
    entries_analyzed=len(all_entries),  # entries loaded (may be < total_entries)
    ...
)
```

### WR-03: Bimodal valley detection picks first zero bucket, not valley midpoint

**File:** `calibrate_vision_verify.py:296-302`
**Issue:** When scanning for the minimum-count bucket between two peaks, if multiple buckets have the same minimum count (typically 0), the algorithm picks the FIRST one encountered (due to `<` comparison, not `<=`). For a distribution with peaks at buckets 0 and 19 (extremes), all intermediate buckets are 0, and the valley is returned as bucket 1 (0.075) rather than the midpoint (bucket 9 or 10, ~0.475).

This produces a threshold that's too close to the left peak, potentially classifying many low-confidence entries as "above threshold" and inflating the FP rate.

**Fix:** When multiple buckets share the minimum count, return the midpoint of the zero-run:

```python
# Find all buckets with the minimum count
min_indices = [idx for idx in range(left_idx + 1, right_idx) if histogram[idx] == min_count]
if min_indices:
    # Return midpoint of the valley region
    mid_idx = min_indices[len(min_indices) // 2]
    return mid_idx * 0.05 + 0.025
```

### WR-04: _threshold_cache poisons on config-read error (process-lifetime)

**File:** `vision_verify.py:135-141`
**Issue:** When `get_threshold()` encounters a config-read error (caught by `except Exception` at line 135), it sets `threshold = _CONFIDENCE_THRESHOLD` (0.7) and then caches this value at line 141: `_threshold_cache[stratum] = threshold`. This means a transient error (e.g., file locked, permission issue) poisons the cache for the entire process lifetime, even if the config becomes readable later.

For short-lived CLI/batch processes this is acceptable (documented in the docstring). But if `vision_verify` is used in a long-running gateway process, a transient config-read failure at startup permanently locks all thresholds to 0.7.

**Fix:** Don't cache on error — only cache successful reads:

```python
    except Exception as exc:
        logger.warning(
            "Failed to read vision_verify thresholds from config: %s", exc
        )
        return _CONFIDENCE_THRESHOLD  # don't cache, retry next call
    # Only cache successful reads
    _threshold_cache[stratum] = threshold
    return threshold
```

### WR-05: Audit log ring-buffer trim is non-atomic (data loss risk on concurrent append)

**File:** `apply_vision_verify_thresholds.py:409-419`
**Issue:** The `append_audit_log()` function performs a read-trim-write cycle: (1) read all lines, (2) trim to last 1000, (3) overwrite the file. If another process appends to the log between step 1 and step 3, that entry is lost because step 3 overwrites the file with only the trimmed entries.

The script is a CLI tool run by the operator, so concurrent appends are unlikely. However, if the operator runs the apply script twice in quick succession (or another tool writes to the same audit log), entries can be silently dropped.

**Fix:** Use file locking or atomic append-and-check:

```python
import fcntl
# During trim, acquire an exclusive lock
with audit_path.open("r+", encoding="utf-8") as f:
    fcntl.flock(f, fcntl.LOCK_EX)
    lines = f.readlines()
    if len(lines) > AUDIT_LOG_MAX_ENTRIES:
        trimmed = lines[-AUDIT_LOG_MAX_ENTRIES:]
        f.seek(0)
        f.truncate()
        f.writelines(trimmed)
    fcntl.flock(f, fcntl.LOCK_UN)
```

## Info

### IN-01: Pre-existing regex can match invalid float strings (uncaught ValueError)

**File:** `vision_verify.py:344`
**Issue:** The regex `([0-9.]+)` in `_parse_vision_response` can match strings like `1.2.3` or `...` that `float()` cannot parse, causing an uncaught `ValueError`. This is a pre-existing issue (not introduced by Phase 79 — the regex line was not modified), but it affects the new threshold-based code path since `_parse_vision_response` is called with the resolved threshold.

**Fix:** Wrap the `float()` call in a try/except:

```python
m = re.search(r"置信度.*?([0-9.]+)", text) or re.search(r"confidence.*?([0-9.]+)", text, re.I)
if m:
    try:
        confidence = float(m.group(1))
    except ValueError:
        confidence = 0.5
else:
    confidence = 0.5
```

### IN-02: calibrate_vision_verify.py get_hermes_home fallback bypasses ContextVar override

**File:** `calibrate_vision_verify.py:523-533`
**Issue:** The `try/except ImportError` fallback for `get_hermes_home` at line 523 uses `os.environ.get("HERMES_HOME", ...)` which bypasses the `ContextVar` override mechanism in `hermes_constants`. This means tests using `set_hermes_home_override()` won't work if the fallback is active. The fallback only activates when `hermes_constants` is not importable, which is an environment issue. The apply script (`apply_vision_verify_thresholds.py`) does NOT have this fallback — it imports `hermes_constants` unconditionally at line 82, which would crash if the module is unavailable.

**Fix:** Ensure `hermes_constants` is always available (it's in the hermes-agent repo which is on sys.path), or make both scripts use the same import strategy.

### IN-03: _infer_stratum treats bool ref_count as int (type confusion)

**File:** `dreamina_manager.py:183`
**Issue:** `isinstance(ref_count, int)` returns `True` for `bool` values in Python (since `bool` is a subclass of `int`). If a caller passes `ref_count=True`, it's treated as `ref_count=1` -> "1-ref". This is unlikely in practice (callers should pass integer ref counts), but the type check doesn't guard against it.

**Fix:** Add explicit bool exclusion:

```python
if isinstance(ref_count, int) and not isinstance(ref_count, bool):
    ...
```

---

_Reviewed: 2026-07-10T14:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
