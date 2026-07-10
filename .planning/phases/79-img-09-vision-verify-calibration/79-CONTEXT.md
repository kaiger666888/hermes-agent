# Phase 79: IMG-09 Vision-Verify Calibration - Context

**Gathered:** 2026-07-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Operator-action handoff closure for IMG-09: deliver a calibration script + threshold application script + per-stratum threshold override in `vision_verify.py` that turns false-positive rate analysis into a 5-minute operator task. Captured thresholds flow back to `~/.hermes/config.yaml` with audit log.

**In scope:**
- `scripts/calibrate_vision_verify.py` — analyzes `~/.hermes/metrics/dreamina_stats.jsonl` production data, computes confidence distribution per stratum, identifies bimodal valley as threshold candidate, estimates FP rate using `success` field as weak proxy, recommends threshold per stratum (1-ref/3-ref/5-ref), writes structured JSON report with `operator_decision` placeholder.
- `scripts/apply_vision_verify_thresholds.py` — reads `operator_decision.thresholds` from calibration report, validates (non-null + valid strata + `lock_ready: true`), writes to `~/.hermes/config.yaml` `vision_verify.thresholds` block, appends to audit log at `~/.hermes/metrics/vision_verify_threshold_audit.jsonl`.
- `plugins/kais_aigc/vision_verify.py` modification — add `get_threshold(stratum)` function that reads config first, falls back to `_CONFIDENCE_THRESHOLD = 0.7`. Update `verify_image_content()` + `verify_batch()` to accept optional `stratum` param; if not passed, use default 0.7. Zero breaking changes to existing callers.
- Unit tests covering calibration math + apply script validation + vision_verify backward compat.

**Out of scope (per REQUIREMENTS.md):**
- IMG-09-AUTO-TUNE closed-loop auto-threshold adjustment based on rolling production data (v16+ scope — operator review still required).
- IMG-07 auto-scaling concurrency (v16+ scope — current 10-parallel is validated stable).
- IMG-08 multi-model routing (v16+ scope — defer until dreamina_manager pattern proven).
- The actual production MetricsBuffer data (operator-action handoff — v15.0 delivers analyzer script, NOT the production data. Operator must have run v14.0 IMG stack in production first).
- SKILL.md body changes (L1-L6 read-only invariant reverts post-v14.0 — not touched in this phase).
- New expert_id (FOUND-08 frozen 15-expert set — not touched).

**Cross-repo topology:** calibration script + apply script + tests + vision_verify.py modification in kais-hermes-skills repo; planning artifacts in hermes-agent repo. Cross-repo pin recorded at milestone close.

</domain>

<decisions>
## Implementation Decisions

### Calibration Method & I/O
- `--metrics-buffer` input: default `~/.hermes/metrics/dreamina_stats.jsonl` (via `hermes_constants.get_hermes_home()` — anti-pattern: `Path.home()`) + `--metrics-buffer <path>` flag override. Matches dreamina_stats.py convention.
- Calibration method: **statistical distribution analysis without ground truth** — compute confidence histogram per stratum (buckets at 0.05 intervals from 0.0-1.0), identify bimodal valley as threshold candidate (local minimum between two peaks), estimate FP rate using `success` field as weak proxy (task failed + high confidence → likely FP). Best-effort without operator-labeled ground truth.
- Insufficient data handling: if < 30 entries per stratum, output `"insufficient_data"` recommendation + keep current 0.7 threshold. Documents why (sample size too small for statistical significance). Script does NOT refuse to run — produces report with `insufficient_data` strata + exits 0.
- Output format: JSON report `{metadata, strata[], operator_decision}` + Rich table to terminal. Mirror Phase 77/78 pattern. `operator_decision: {thresholds: null, rationale: null, lock_ready: false}`.

### Threshold Application & Audit Log
- How thresholds are applied: modify `vision_verify.py` to read per-stratum thresholds from `~/.hermes/config.yaml` (new `vision_verify.thresholds` block). Falls back to `_CONFIDENCE_THRESHOLD = 0.7` if stratum not in config. Backward-compatible — existing callers without stratum param use default.
- Config schema: YAML block in `~/.hermes/config.yaml`:
  ```yaml
  vision_verify:
    thresholds:
      1-ref: 0.75
      3-ref: 0.70
      5-ref: 0.65
    default: 0.7
    last_updated: 2026-07-10
  ```
- Audit log format: JSONL at `~/.hermes/metrics/vision_verify_threshold_audit.jsonl` — one entry per threshold change: `{ts, stratum, old_threshold, new_threshold, rationale, calibration_report_path}`. Append-only, ring-buffer style (last 1000 entries). Mirrors dreamina_stats MetricsBuffer pattern.
- Application mechanism: separate `apply_vision_verify_thresholds.py` script (mirrors Phase 77/78 verdict/lock pattern) — reads `operator_decision` from calibration report + writes to `~/.hermes/config.yaml` + appends to audit log. Operator edits JSON between calibrate + apply.

### Report Schema & Backward Compatibility
- Calibration report schema: `{metadata, strata[], operator_decision}` — mirror Phase 77/78. `strata[]` has per-stratum `{stratum, sample_size, confidence_distribution, recommended_threshold, estimated_fp_rate, current_threshold, rationale}`. `operator_decision: {thresholds: null, rationale: null, lock_ready: false}`.
- Stratum coverage: 3 strata — `1-ref`, `3-ref`, `5-ref` (per IMG-09 success criterion). `text2image` stratum excluded — no vision-verify for text2image (no reference image to verify against). Script documents this exclusion in report metadata.
- Backward compatibility: `vision_verify.py` keeps `_CONFIDENCE_THRESHOLD = 0.7` as module-level fallback. New `get_threshold(stratum: str | None = None) -> float` function reads config first, falls back to 0.7. Existing callers (`verify_image_content`, `verify_batch`) updated to accept optional `stratum` param; if not passed, use default 0.7. Zero breaking changes to existing callers.
- Calibration re-run: operator can re-run calibrator with new MetricsBuffer data at any time. Each run produces a new report with timestamp. Apply script refuses if config already has thresholds from a more recent run (overwrite guard, `--force` to override). Mirrors Phase 77/78 pattern.

### Claude's Discretion
- **Bimodal valley detection algorithm:** Use a simple histogram-based approach — bucket confidences at 0.05 intervals (20 buckets from 0.0-1.0), find the local minimum between the two highest peaks. If no clear bimodal distribution (single peak), fall back to 0.7 default + document "no clear bimodal distribution detected" in rationale. Do NOT use scipy/numpy — stdlib only (keeps dependency footprint minimal).
- **FP rate estimation formula:** `estimated_fp_rate = (count of entries where success=False AND vision_confidence >= candidate_threshold) / (count of entries where vision_confidence >= candidate_threshold)`. This is a rough proxy — document the assumption clearly in the report. Operator reviews before applying.
- **Config file read/write:** Use `ruamel.yaml` (already in pyproject.toml deps) for YAML round-trip preservation (comments, formatting). Write to `~/.hermes/config.yaml` atomically via temp file + `os.replace()` (mirrors Phase 78 verdict-doc atomic write). If config file doesn't exist, create it with the `vision_verify:` block only.
- **vision_verify.py modification scope:** Minimal changes — add `get_threshold()` function + update `verify_image_content()` + `verify_batch()` signatures to accept optional `stratum` param + replace `_CONFIDENCE_THRESHOLD` references with `get_threshold(stratum)` calls. Do NOT refactor existing logic. Do NOT remove `_CONFIDENCE_THRESHOLD` constant (keep as fallback default).
- **Error handling:** If MetricsBuffer file missing, fail fast with clear error. If config file parse fails, refuse to apply + warn operator. If audit log dir missing, create it (`~/.hermes/metrics/`).
- **Tests:** Mock MetricsBuffer data (realistic distributions for each stratum). Test: (a) calibration produces report for 3 strata; (b) insufficient_data when <30 entries; (c) bimodal valley detection on synthetic bimodal distribution; (d) apply script refuses null thresholds; (e) apply script refuses lock_ready=false; (f) apply script writes config + audit log; (g) vision_verify backward compat (callers without stratum still work); (h) get_threshold reads config + falls back to 0.7.
- **CLI ergonomics:** `--help` follows Phase 77/78 argparse style. Rich tables for terminal summary (per-stratum recommended threshold + estimated FP rate + sample size).

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`plugins/kais_aigc/vision_verify.py`** — existing vision-verify module. Line 66: `_CONFIDENCE_THRESHOLD = 0.7` (single global threshold). Line 73: `async def verify_image_content(...)` (async function). Line 136: `async def verify_batch(...)`. Line 240: `_extract_confidence()` parses confidence from GLM-4.6V response. Phase 79 adds `get_threshold(stratum)` + optional stratum param.
- **`plugins/kais_aigc/dreamina_stats.py`** — MetricsBuffer schema + read pattern. Line 67: `stratum: str` field (1-ref/3-ref/5-ref/text2image). Line 71-72: `vision_verified: bool` + `vision_confidence: float | None`. Line 156: `stats` CLI subcommand pattern. `_metrics_file()` returns `~/.hermes/metrics/dreamina_stats.jsonl`.
- **`plugins/kais_aigc/dreamina_stats.py` `read_metrics()`** — reads MetricsBuffer JSONL, returns list of dicts. Reuse for calibration script input.
- **`skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py`** (Phase 77) — Pydantic v2 report schema + Rich summary table + argparse pattern.
- **`skills/movie-experts/audio_pipeline/scripts/lock_cosyvoice_default.py`** (Phase 77) — read-report + validate + write pattern + overwrite guard. Direct template for apply script.
- **`skills/kais-movie-pipeline/scripts/update_ltx_flf_verdict.py`** (Phase 78) — atomic write pattern (temp file + os.replace) + 4-check validation.

### Established Patterns
- **Pydantic v2 BaseModel** for report schema — `dreamina_stats.DreaminaTaskMetrics` + Phase 77 `BenchmarkReport` + Phase 78 `ValidationReport` precedent.
- **`hermes_constants.get_hermes_home()`** for `~/.hermes/` paths (anti-pattern: `Path.home() / ".hermes"`).
- **`encoding="utf-8"`** on every `open()` call (Ruff PLW1514).
- **`from __future__ import annotations`** at module top.
- **Sync-only execution for calibration script** (no GLM calls — just reads MetricsBuffer data). Apply script is sync-only (writes config + audit log).
- **Rich table for CLI output** — Phase 77/78 `emit_rich_summary()` pattern.
- **Atomic file write** — temp file + `os.replace()` (Phase 78 verdict-doc pattern).

### Integration Points
- **`~/.hermes/metrics/dreamina_stats.jsonl`** — MetricsBuffer JSONL. Read by calibrator. Written by dreamina_stats.py (existing, not modified).
- **`~/.hermes/config.yaml`** — Hermes config file. Read + written by apply script (new `vision_verify.thresholds` block). Read by `vision_verify.py` `get_threshold()` at runtime.
- **`~/.hermes/metrics/vision_verify_threshold_audit.jsonl`** — new audit log. Appended by apply script. Ring-buffer style (last 1000 entries).
- **`plugins/kais_aigc/vision_verify.py`** — modified in place. New `get_threshold()` function. Updated `verify_image_content()` + `verify_batch()` signatures. Existing callers (dreamina_manager.py, etc.) continue to work without changes (optional stratum param).

</code_context>

<specifics>
## Specific Ideas

- **Two-script design (mirrors Phase 77/78):** calibrator produces report with `operator_decision: null`; operator edits JSON to fill thresholds + rationale + set `lock_ready: true`; apply script reads JSON + writes config + appends audit log. Single source of truth (JSON report), clean separation (calibration vs threshold commit).
- **Statistical method without ground truth:** bimodal valley detection on confidence histogram. If distribution is unimodal (single peak), fall back to 0.7 + document "no clear bimodal distribution". Operator reviews the confidence distribution in the Rich table before deciding.
- **`success` field as weak FP proxy:** if dreamina task failed (`success=False`) but vision-verify returned high confidence (`vision_confidence >= threshold`), likely a false positive. Document this assumption clearly — it's a rough proxy, not ground truth.
- **`lock_ready` guard (mirrors Phase 77/78):** operator sets `lock_ready: true` when thresholds are finalized. Apply script refuses if `lock_ready` is false. Extra guard against premature threshold commit.
- **Backward compat is non-negotiable:** existing `verify_image_content(image_path, expected_content)` callers MUST continue to work without changes. The new `stratum` param is optional with default `None` → uses 0.7 fallback. This means dreamina_manager.py + other existing callers don't need modification.
- **`text2image` stratum excluded:** no reference image to verify against for text2image. Script documents this in report metadata: `"excluded_strata": ["text2image"], "exclusion_rationale": "no reference image for vision-verify"`.

</specifics>

<deferred>
## Deferred Ideas

- **IMG-09-AUTO-TUNE** — closed-loop auto-threshold adjustment based on rolling production data (v16+ scope — operator review still required per REQUIREMENTS.md deferral).
- **Operator-labeled ground truth** — calibration script uses statistical method only. If operator labels a sample of entries as TP/FP, calibration could compute actual FP rate. v16+ scope if labeling workflow emerges.
- **Per-image-stratum thresholds** — current 3 strata (1-ref/3-ref/5-ref). Finer granularity (e.g., per-character, per-episode) is v16+ scope.
- **Threshold A/B testing** — run two thresholds in parallel + compare outcomes. v16+ scope.
- **Real-time threshold monitoring** — dashboard showing FP rate over time post-calibration. v16+ scope.
- **Multi-model threshold routing** — different thresholds for different GLM models. v16+ scope (requires multi-model support first).

</deferred>
