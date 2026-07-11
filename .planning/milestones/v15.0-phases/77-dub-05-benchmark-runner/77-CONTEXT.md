# Phase 77: DUB-05 Benchmark Runner - Context

**Gathered:** 2026-07-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Operator-action handoff closure for DUB-05: deliver two CLI scripts in the kais-hermes-skills repo that turn the CosyVoice A/B benchmark + VERSION.json lock into a 5-minute operator task.

**In scope:**
- `scripts/run_cosyvoice_benchmark.py` — submits N dialogue lines × M variants to ComfyUI, captures audio + latency, optionally computes WER via Whisper CN, writes structured JSON report.
- `scripts/lock_cosyvoice_default.py` — reads operator_decision from benchmark report, validates + locks `VERSION.json.tts.cosyvoice_default_variant` + `lock_date` + `lock_rationale`.
- JSON report schema `{metadata, lines[], operator_decision}` — operator edits JSON to record decision between runner + lock steps.
- Unit tests covering happy path + overwrite guard + validation failures.

**Out of scope (per REQUIREMENTS.md):**
- Auto-pick-lower-WER (DUB-05-AUTO-LOCK deferral — operator judgment required for audio quality).
- Real-time TTS streaming (DUB-06 v16+).
- Per-line emotion/speed/volume fine control (DUB-07 v16+).
- The actual benchmark execution + audio files (operator-action handoff — v15.0 delivers tooling only).
- SKILL.md body changes (L1-L6 read-only invariant reverts post-v14.0; only kais-jimeng-cli SKILL.md may be touched in v15.0 and not for this phase).

**Cross-repo topology:** scripts + workflows + tests in kais-hermes-skills repo; planning artifacts in hermes-agent repo. Cross-repo pin recorded at milestone close.

</domain>

<decisions>
## Implementation Decisions

### Runner I/O & Invocation
- Dialogue-lines file format: JSON array — `[{id, text, emotion, speaker}, ...]`. Structured; lets runner pass `emotion` + `instruct_text` straight into AIIA nodes (no text parsing fragility).
- Default output directory: `runs/cosyvoice-benchmarks/{YYYYMMDD-HHMMSS}/` under kais-hermes-skills repo root. Matches existing `runs/ep-*` convention; timestamped for repeatable benchmarks.
- Audio file naming: `{line_id}_{variant}.wav` (e.g. `01_cosyvoice_2_0_0_5b.wav`). Sortable + self-documenting; matches `gold-team-tts-batch.py` precedent.
- ComfyUI URL source: `--comfyui-url` flag, default `http://127.0.0.1:8188` (env `COMFYUI_URL` as fallback). Matches `probe-tts-routing.sh` convention.

### Report Schema & WER Computation
- JSON report top-level structure: `{metadata, lines[], operator_decision}` — metadata (timestamp, variants, comfyui_url), lines (one per dialogue line, each with per-variant results), operator_decision (null until operator fills).
- WER computation: auto-run Whisper CN if `whisper` CLI available; graceful skip with `wer: null` if missing. Operator can fill manually in cosyvoice-benchmark.md. Automates what's automatable without hard dep.
- operator_decision placement: top-level `operator_decision: {variant: null, rationale: null, lock_ready: false}` in report. Operator edits JSON to fill; lock script reads this field. Single source of truth.
- Gold-team 3rd variant (`cosyvoice_300M_gold_team`): optional via `--variants` flag. Default = 2 per success criterion; operator adds 3rd if gold-team `:8002` available. Runner auto-detects gold-team reachability and warns if requested but unreachable.

### Lock Script Behavior
- Source of chosen variant: read from `operator_decision.variant` in benchmark report. Lock script's only required arg is `--benchmark-report <path>` per success criterion. Operator edits JSON between runner + lock steps.
- Overwrite guard: refuse with error if `VERSION.json.tts.cosyvoice_default_variant` already non-null; require `--force` to overwrite. Prevents accidental re-lock.
- VERSION.json write scope: full lock block — `cosyvoice_default_variant` + `lock_date` (today ISO) + `lock_rationale` (from `operator_decision.rationale`). Does NOT touch `alternative_tested[]` or `benchmark_report_path` (already populated).
- Pre-lock validation: three checks — (a) `operator_decision.variant` non-null + non-empty; (b) variant is in `alternative_tested[]` list in VERSION.json; (c) variant appears in report's `lines[].variants[]` (i.e., was actually benchmarked). Fail with specific error if any check fails.

### Claude's Discretion
- ComfyUI workflow per variant: reuse existing `cosyvoice-comfyui.json` (AIIA nodes) as the template. Parameterize via `model_dir` per variant — `AIIA_CosyVoice_ModelLoader` accepts `model_dir` so the same workflow JSON can be reused with a single field swap. If variant-specific quirks emerge (e.g. `cosyvoice_300M_gold_team` uses HTTP API not ComfyUI), implement a thin adapter rather than separate workflows.
- Variant ID normalization: `cosyvoice_2_0_0_5b` → `cosyvoice_2.0_0.5B` (model_dir at benchmark time, verify at run); `fun_cosyvoice_3_0` → `fun_cosyvoice_3.0_0.5B_2512` (`/root/ComfyUI/models/cosyvoice/Fun-CosyVoice3-0.5B-2512/`); `cosyvoice_300M_gold_team` → gold-team `:8002` HTTP API. Use a `VARIANTS` dict mapping CLI ID → {model_dir, workflow_path or api_endpoint}.
- Whisper CLI invocation: `whisper --model large-v3 --language zh --task transcribe --output_format txt --output_dir <tmp>` or equivalent; parse `.txt` output to compute WER via simple character-level Levenshtein (no external NLP lib dependency). Document the WER formula in script docstring.
- Error handling: if ComfyUI unreachable at startup, fail fast with clear error (no retry loop — this is a benchmark, not production). If a single variant fails for a single line, log the error in that cell of the report (`error: "..."`) but continue with other variants. Partial results are useful for operator review.
- Tests: smoke test that runner produces a report for 1 dummy line with mocked ComfyUI client; smoke test that lock script refuses empty `operator_decision.variant`; smoke test that lock script refuses variant not in `alternative_tested[]`. Use `unittest.mock` for ComfyUI HTTP calls.
- CLI ergonomics: `--help` output follows `dreamina_stats.py` argparse style. Rich tables for terminal summary (per-variant MOS/WER/latency comparison) after runner completes — operator sees results at a glance.
- Documentation: a short `references/cosyvoice-benchmark-runner-usage.md` (or extend existing `cosyvoice-benchmark.md` template with a `## Runner Usage` section) showing example invocation + JSON I/O samples. Keeps operator action ≤5 min.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`skills/movie-experts/audio_pipeline/references/workflows/cosyvoice-comfyui.json`** — existing AIIA CosyVoice ComfyUI workflow (LoadAudio + AIIA_CosyVoice_ModelLoader + AIIA_CosyVoice_TTS + SaveAudio). Template for benchmark runner to parameterize.
- **`skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-benchmark.md`** — existing benchmark protocol template (3 variants, MOS/WER/preference table, default lock decision section). Runner's JSON report should align field names with this template so manual fill-in is straightforward.
- **`skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-deployment.md`** — verified ComfyUI container name (`comfyui-primary`, NOT `comfyui`), ComfyUI URL (`http://127.0.0.1:8188`), gold-team endpoint (`:8002`), VRAM budget notes (PITFALL D-5 LTX-MSR contention).
- **`plugins/kais_aigc/dreamina_stats.py`** — Pydantic v2 schema + Rich table CLI pattern to mirror for benchmark report schema + lock script CLI ergonomics. Sync-only execution (INFRA-04 compliant).
- **`skills/movie-experts/audio_pipeline/scripts/gold-team-tts-batch.py`** — existing TTS batch script with audio file naming + iteration patterns. Reference for runner loop structure.

### Established Patterns
- **Pydantic v2 BaseModel** for structured data (schema validation, JSON serialization) — `dreamina_stats.DreaminaTaskMetrics` precedent.
- **Sync-only execution for GLM-coupled code paths** — INFRA-04 hard constraint; benchmark runner is sync-only (ComfyUI HTTP calls via `requests` or `httpx.Client`, not async).
- **Rich table for CLI output** — `dreamina_stats._emit_rich` pattern; runner prints summary table after completion.
- **`hermes_constants.get_hermes_home()`** for any `~/.hermes/` paths (anti-pattern: `Path.home() / ".hermes"`).
- **`from __future__ import annotations`** at module top (PEP 604 unions on Python 3.11+).
- **`encoding="utf-8"`** on every `open()` call (Ruff PLW1514 rule).

### Integration Points
- **ComfyUI** at `http://127.0.0.1:8188` (container `comfyui-primary`) — submit workflow JSON via `/prompt` endpoint, poll `/history/{prompt_id}` for completion, fetch outputs via `/view?filename=...`.
- **Gold-team API** at `:8002/api/v1/tasks` with `type=tts_zh` — for optional 3rd variant `cosyvoice_300M_gold_team`.
- **VERSION.json** at kais-hermes-skills repo root — top-level `tts` block already has `cosyvoice_default_variant: null`, `lock_date: null`, `lock_rationale: null`, `alternative_tested[]`, `benchmark_report_path`. Lock script writes only the first three fields.
- **Whisper CLI** (optional) — `whisper` binary on PATH. Runner checks `shutil.which("whisper")` and skips WER if missing.

</code_context>

<specifics>
## Specific Ideas

- **Two-script design (not one):** runner + lock are separate scripts per success criterion. Keeps single responsibility; operator can re-lock without re-running benchmark if decision changes.
- **JSON report as single source of truth:** runner writes report with `operator_decision: null`; operator edits JSON to fill decision; lock script reads JSON. No separate `decision.json` file, no `--variant` flag on lock script. This matches the success criterion's "lock script only takes `--benchmark-report <path>`" surface.
- **WER is best-effort, not required:** runner attempts Whisper CN transcription + Levenshtein WER if `whisper` CLI is installed. If not, `wer: null` in report and operator fills `cosyvoice-benchmark.md` manually. Avoids hard Whisper dependency in the v15.0 stack.
- **`lock_ready` flag in operator_decision:** operator sets `lock_ready: true` when ready to lock. Lock script refuses if `lock_ready` is false (extra guard against running lock before decision is finalized).

</specifics>

<deferred>
## Deferred Ideas

- **DUB-05-AUTO-LOCK** — full automation of VERSION.json lock based on benchmark scores (operator-in-loop required for audio quality judgment per REQUIREMENTS.md `DUB-05-AUTO-LOCK` deferral; v16+ scope).
- **DUB-07 per-line emotion/speed/volume fine control** — current runner uses dialogue-lines JSON `emotion` field mapped to AIIA `emotion` enum; per-line `instruct_text` + `speed` + `seed` override is v16+ scope.
- **DUB-08 cross-shot voice_identity dimension in continuity_auditor** — 5th dimension; v16+ scope.
- **Multi-model benchmark harness (CosyVoice + IndexTTS2 + other)** — current runner is CosyVoice-specific per success criterion; generalization to a multi-engine benchmark harness is v16+ scope.
- **Live benchmark dashboard (web UI)** — runner outputs JSON + Rich table to terminal; web dashboard is v16+ scope if operator workflow demands it.

</deferred>
