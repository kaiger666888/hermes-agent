# Phase 78: TRANS-07 LTX-FLF Validation Runner - Context

**Gathered:** 2026-07-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Operator-action handoff closure for TRANS-07: deliver a ComfyUI workflow JSON + runner script + verdict-doc update mechanism that turns the LTX-2.3 FLF+ICLoRA combined workflow validation into a 5-minute operator task. Captured verdict (ready / deferred-to-v16+) flows back to `references/ltx-flf-iclora-validation.md` and gates TRANS-11 v16+ production rollout.

**In scope:**
- `references/workflows/ltx-flf-iclora-validation.json` — ComfyUI workflow JSON (LiconMSR Loader + FLF Loader + LTXVConditioning + SamplerCustomAdvanced + VAEDecode + SaveVideo node graph per `ltx-flf-iclora-validation.md` §ComfyUI Node Graph Setup).
- `scripts/run_ltx_flf_validation.py` — async runner that submits 1-2 reference shots through the workflow, captures gen_status + latency + identity-continuity via `vision_verify.verify_image_content()`, writes structured JSON report with `operator_decision` placeholder.
- Verdict update mechanism — either a separate `scripts/update_ltx_flf_verdict.py` script OR `--update-verdict-doc` flag on the runner (Claude's Discretion). Reads `operator_decision` from report + writes verdict section to `references/ltx-flf-iclora-validation.md`.
- Unit tests covering happy path + vision_verify mock + verdict-doc update.

**Out of scope (per REQUIREMENTS.md):**
- TRANS-11 production rollout (gated by this phase's verdict — v16+ scope if validation passes).
- TRANS-08 AI-generated whip pan transitions (v16+ scope).
- TRANS-09 custom transition types beyond 12-value taxonomy (industry-standard sufficient).
- TRANS-10 per-transition runtime LLM routing decisions (INFRA-04 risk).
- The actual validation execution + results (operator-action handoff — v15.0 delivers tooling only, operator runs validation on 1-2 reference shots).
- SKILL.md body changes (L1-L6 read-only invariant reverts post-v14.0 — not touched in this phase).

**Cross-repo topology:** workflow JSON + scripts + tests in kais-hermes-skills repo; planning artifacts in hermes-agent repo. Cross-repo pin recorded at milestone close.

</domain>

<decisions>
## Implementation Decisions

### Runner I/O & Invocation
- `--reference-shots` input format: directory with per-shot subdirs — `shots/{shot_id}/` containing `first_frame.png`, `last_frame.png`, `ref1.png`...`ref5.png`. Clear structure; operator drops files in. Runner validates each shot subdir has required files.
- Default output directory: `runs/ltx-flf-validation/{YYYYMMDD-HHMMSS}/` under kais-hermes-skills repo root. Matches Phase 77 pattern + existing `runs/ep-*` convention.
- Video file naming: `{shot_id}_validation.mp4` + extracted `{shot_id}_frame_{N}.png` for vision_verify. Sortable + self-documenting; extracted frames enable per-frame identity checks.
- Runner async pattern: **async runner with serial awaits** (`async def main()` + `asyncio.run(main())`). Cleanest `vision_verify` integration (its functions are async); matches v14.0 IMG pattern (`dreamina_manager.py`). No `asyncio.gather` for GLM-coupled calls (INFRA-04 compliant — serial `await` only).

### Workflow JSON Design
- FLF model choice: `ltx/fflf` (lightweight) — recommended for validation per `ltx-video-workflows.md` §Workflow Selection Guide ("fflf = lightweight"). Operator can switch to `singularityFFLF` via `--flf-model` flag if desired.
- Reference image count: configurable via `--num-refs` flag, default 5 (max per ICLoRA spec). Operator can pass 2-5; runner validates count matches workflow JSON inputs.
- Sampler settings: 8-step distilled (speed) — matches production LTX-MSR defaults per `ltx-video-workflows.md` line 218 (39/39 success at 8 steps). Operator can override via `--steps` flag.
- Workflow JSON parameterization: static JSON template with placeholder values + runner dynamically swaps `model_dir` / `ref_image` paths / `first_frame` / `last_frame` per shot. Mirrors Phase 77 `build_comfyui_workflow()` pattern. Single template, N submissions.

### Report Schema & Verdict Capture
- Report schema: `{metadata, shots[], operator_decision}` — mirror Phase 77 pattern. `operator_decision: {verdict: null, rationale: null, lock_ready: false}`. Operator edits JSON to fill verdict between runner + verdict-doc update.
- vision_verify call timing: first frame + last frame + middle frame (3 calls per shot) — catches identity drift at boundaries + midpoint. ~6 GLM-4.6V calls for 2 shots (acceptable cost per IMG-03 precedent).
- Verdict capture mechanism: operator edits JSON `operator_decision.verdict` + `rationale` (like Phase 77 lock script). Runner does NOT auto-recommend verdict — operator judgment required (identity drift is qualitative, not score-based). Verdict values: `ready` | `deferred-to-v16+` | `partial`.
- Verdict doc update: separate `update_ltx_flf_verdict.py` script OR `--update-verdict-doc` flag on runner (Claude's Discretion — planner picks based on complexity). Reads `operator_decision` from report + writes verdict section to `references/ltx-flf-iclora-validation.md`. Mirrors Phase 77 lock script pattern.

### Claude's Discretion
- **Verdict update mechanism (1 script vs 2):** Planner decides between (a) separate `update_ltx_flf_verdict.py` script that reads `--benchmark-report <path>` + writes to markdown (mirrors Phase 77 lock script pattern), OR (b) `--update-verdict-doc` flag on the runner that does the same. Recommend (a) for single-responsibility + consistency with Phase 77 two-script design, but (b) is acceptable if it simplifies the plan.
- **ComfyUI workflow JSON construction:** Base the JSON on the LiconMSR Workflow JSON Template (line 506 of `ltx-video-workflows.md`, validated 2026-06-28 3/3 success) + add FLF Loader node + LTXVConditioning node per the node graph in `ltx-flf-iclora-validation.md`. The combined workflow is NOT turnkey (per PITFALL T-1 orthogonality) — the JSON is the community-reported combination, operator validates.
- **vision_verify integration:** Call `vision_verify.verify_image_content()` for each of the 3 frames (first/middle/last) per shot. Pass the character identity reference (ref1.png) as the "expected" image + the generated frame as the "actual" image. Parse the returned confidence + match description into the report's `shots[].frames[].identity_continuity` field.
- **Video frame extraction:** Use `ffmpeg` to extract first/middle/last frames from the generated `.mp4` (same ffmpeg dependency as Phase 77's silent-output detection). If ffmpeg missing, skip vision_verify with `identity_continuity: null` + warning log.
- **Error handling:** If ComfyUI unreachable at startup, fail fast. If a single shot fails (gen_status != success), log error in that shot's report entry but continue with other shots. Partial results are useful for operator review.
- **Tests:** Mock ComfyUI HTTP + vision_verify + ffmpeg. Test: (a) runner produces report for 1 dummy shot with mocked ComfyUI; (b) vision_verify called 3 times per shot (first/middle/last); (c) verdict update writes correct section to markdown; (d) verdict update refuses if `operator_decision.verdict` is null; (e) verdict update refuses if `lock_ready` is false.
- **CLI ergonomics:** `--help` output follows Phase 77 argparse style. Rich tables for terminal summary (per-shot gen_status + latency + identity-continuity confidence).
- **Documentation:** Extend existing `ltx-flf-iclora-validation.md` with a `## Runner Usage` section (like Phase 77's cosyvoice-benchmark.md extension) showing example invocation + JSON I/O samples + verdict update flow.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`skills/kais-movie-pipeline/references/ltx-flf-iclora-validation.md`** — existing validation template (v14.0 created). Has ComfyUI Node Graph Setup + Reference Shots placeholders + Production-Readiness Decision section. Phase 78 extends with `## Runner Usage` section + operator fills verdict.
- **`skills/kais-movie/kais-aigc-platform/references/ltx-video-workflows.md`** — authoritative LTX workflow reference. Line 506+ has validated LiconMSR Workflow JSON Template (3/3 success 2026-06-28). Line 298-301 has 4 LTX workflow variants table (`/ltx/msr`, `/ltx/fflf`, `/ltx/singularityFFLF`).
- **`skills/movie-experts/audio_pipeline/scripts/run_cosyvoice_benchmark.py`** (Phase 77 output) — ComfyUI /prompt + /history poll pattern, Pydantic v2 report schema, Rich summary table, `build_comfyui_workflow()` parameterization pattern. Direct template for Phase 78 runner.
- **`skills/movie-experts/audio_pipeline/scripts/lock_cosyvoice_default.py`** (Phase 77 output) — read-report + validate + write-pattern for verdict update script. 3-check validation + overwrite guard pattern.
- **`plugins/kais_aigc/vision_verify.py`** — async `verify_image_content()` + `verify_batch()` functions. Uses `async_call_llm(task="vision", ...)` for GLM-4.6V. SHA256-keyed cache (24h TTL). Returns confidence + match description.
- **`skills/kais-movie-pipeline/references/comfyui-ltx-video-api.md`** — ComfyUI LTX integration pointer. Container `comfyui-primary`, URL `http://127.0.0.1:8188`, model paths under `/root/ComfyUI/models/diffusion_models/`.

### Established Patterns
- **Pydantic v2 BaseModel** for report schema — `dreamina_stats.DreaminaTaskMetrics` + Phase 77 `BenchmarkReport` precedent.
- **ComfyUI HTTP flow** (sync or async) — `/prompt` to submit, `/history/{prompt_id}` to poll, `/view?filename=...` to download outputs. Phase 77 uses `requests` (sync); Phase 78 may use `httpx.AsyncClient` (async) since runner is async.
- **vision_verify async integration** — `asyncio.run()` bridge from sync OR direct `await` from async. Phase 78 runner is async, so direct `await verify_image_content(...)`.
- **Rich table for CLI output** — Phase 77 `emit_rich_summary()` pattern.
- **`encoding="utf-8"`** on every `open()` call (Ruff PLW1514).
- **`from __future__ import annotations`** at module top.

### Integration Points
- **ComfyUI** at `http://127.0.0.1:8188` (container `comfyui-primary`) — submit workflow JSON via `/prompt`, poll `/history/{prompt_id}`, fetch outputs via `/view?filename=...`.
- **vision_verify** via `plugins.kais_aigc.vision_verify.verify_image_content()` — async function, returns `{confidence, match_description, cached}`.
- **ffmpeg** for video frame extraction — `ffmpeg -i {input.mp4} -vf "select=eq(n\,{frame_num})" -vframes 1 {output.png}`. Same ffmpeg dependency as Phase 77.
- **`ltx-flf-iclora-validation.md`** — existing template at `skills/kais-movie-pipeline/references/ltx-flf-iclora-validation.md`. Phase 78 extends with `## Runner Usage` section + operator fills verdict via update script.

</code_context>

<specifics>
## Specific Ideas

- **Two-script design (mirrors Phase 77):** runner produces report with `operator_decision: null`; operator edits JSON to fill verdict + rationale + set `lock_ready: true`; verdict update script reads JSON + writes verdict section to markdown. Single source of truth (JSON report), clean separation (validation vs verdict commit).
- **3-frame vision_verify (not all frames):** identity drift is most detectable at boundaries (first/last) + midpoint (middle). 3 calls per shot × 2 shots = 6 GLM-4.6V calls — acceptable cost per IMG-03 precedent (~178 calls per 213-shot episode in production; 6 calls for validation is negligible).
- **`lock_ready` guard (mirrors Phase 77):** operator sets `lock_ready: true` when verdict is finalized. Verdict update script refuses if `lock_ready` is false. Extra guard against premature verdict commit.
- **Verdict values: `ready` | `deferred-to-v16+` | `partial`:** `ready` → TRANS-11 v16+ production rollout greenlit. `deferred-to-v16+` → TRANS-11 deferred to v17+ or later (needs more work). `partial` → identity continuity holds for landscape-only match-cuts but not character match-cuts (fallback routing per `ltx-flf-iclora-validation.md` §Background).

</specifics>

<deferred>
## Deferred Ideas

- **TRANS-11 production rollout** — gated by this phase's verdict. v16+ scope if validation passes; v17+ if deferred.
- **TRANS-08 AI-generated whip pan transitions** — v16+ scope (current generation engines unreliable for cross-shot motion-vector continuity).
- **TRANS-09 custom transition types beyond 12-value taxonomy** — industry-standard taxonomy sufficient; avoid over-engineering.
- **TRANS-10 per-transition runtime LLM routing** — INFRA-04 serial constraint violation risk; v14.0 uses declarative rules only.
- **Automated verdict recommendation** — runner does NOT auto-recommend verdict based on vision_verify confidence. Identity drift is qualitative (confidence ≠ drift severity). Operator judgment required. v16+ scope if pattern emerges.
- **Multi-shot batch validation (>2 shots)** — success criterion specifies 1-2 reference shots. Larger batches are v16+ scope if production rollout happens.
- **singularityFFLF 76-node mega-workflow support** — `--flf-model` flag allows operator to switch, but the default JSON template uses `ltx/fflf` (lightweight). Full singularityFFLF template is v16+ scope if needed.

</deferred>
