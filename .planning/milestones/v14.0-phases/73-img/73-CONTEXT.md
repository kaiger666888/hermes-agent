# Phase 73: IMG - Context

**Gathered:** 2026-07-09
**Status:** Ready for planning
**Mode:** Auto-generated (user prefers direct plan-phase dispatch; Claude's analyzed defaults below)

<domain>
## Phase Boundary

Users can submit dreamina batch image generation through a production-grade orchestrator with retry + concurrency cap + sync queue semantics, where reference images are vision-verified via GLM-4.6V before ComfyUI upload, RHD/LHD-type failures are systematically mitigated, and the operator has an SLA dashboard.

Requirements covered: IMG-01 (dreamina_manager.py orchestrator with asyncio.Semaphore(10) + tenacity + sync queue), IMG-02 (block pipeline_state write until retries resolve), IMG-03 (GLM-4.6V vision-verify mandatory gate), IMG-04 (RHD/LHD 3-attempt budget), IMG-05 (`hermes dreamina stats` SLA CLI), IMG-06 (image2image workflow standardization with ref-count stratification).

**Parallel with Phase 72 (DUB):** DUB and IMG are independent surfaces both depending only on Phase 71 (FORM — image2image reference counts may vary by form_factor for shot scale). Executing after Phase 72 per autonomous serial mode.

**Out of scope (v15+ per REQUIREMENTS):** IMG-07 auto-scaling concurrency; IMG-08 multi-model routing; IMG-09 vision-verify false-positive threshold calibration.

</domain>

<decisions>
## Implementation Decisions

### dreamina_manager.py Orchestrator (IMG-01 + IMG-02)
- **Location:** `kais-hermes-skills/plugins/kais_aigc/dreamina_manager.py` (NEW; co-located with existing kais_aigc plugin per PITFALL I-5 cross-ref). Alternative: `skills/kais-creative/kais-jimeng-cli/scripts/dreamina_manager.py` — REJECTED because kais_aigc is the Python plugin layer and orchestrator belongs there.
- **Concurrency primitive:** `asyncio.Semaphore(10)` (10-parallel = 100% sweet spot per SKILL.md line 621-622 validated). NOT auto-scaling (IMG-07 deferred).
- **Retry strategy:** `tenacity` (already pinned in pyproject.toml); exponential backoff (1s, 2s, 4s, 8s, max 4 retries); retry on `TimeoutError`, `ConnectionError`, dreamina-specific transient errors (per existing batch-generation-quality-control.md).
- **Sync queue semantics:** Block on `asyncio.gather(*tasks)` poll-all-before-deadline. Pipeline state write ONLY after all retries resolve (IMG-02). NO async write order (fixes SKILL.md line 619 pitfall).
- **Deadline:** Configurable per-batch; default 600s (10 min) for 10-parallel batch of 39 reference images per existing pipeline benchmarks.

### GLM-4.6V Vision-Verify Mandatory Gate (IMG-03)
- **Implementation:** New `kais-hermes-skills/plugins/kais_aigc/vision_verify.py` module with `verify_image_content(image_path, expected_content, directional_check=None)` function.
- **Batched calls:** Per PITFALL I-1 mitigation #1 — batch N images per GLM-4.6V call (multi-image message) — 4-8 images per call cuts overhead 4-8x.
- **Confidence-gated enforcement:** Per PITFALL I-1 mitigation #2 — vision-verify flags "low confidence" cases (ambiguous response, content mismatch > 30%) for human review; high-confidence passes auto.
- **Mandatory gate semantic:** Per PITFALL I-2 mitigation #4 — mandatory gate = "vision-verify has RUN", NOT "vision-verify has APPROVED". The artifact is the audit trail; the decision is operator's.
- **Cache:** Per PITFALL I-1 mitigation #4 — sha256-keyed cache so re-running same image doesn't re-verify.
- **Directional check (RHD/LHD):** Explicit `"left_hand_drive? yes/no"` question per PITFALL I-4 mitigation #2.

### RHD/LHD 3-Attempt Budget (IMG-04)
- **3-attempt budget per PITFALL I-4 mitigation:**
  1. **Attempt 1:** Prompt with LHD emphasis (e.g., "left-hand drive car, steering wheel on the left, driver sits on the left")
  2. **Attempt 2 (verify-retry):** If vision says RHD or low-confidence, retry with stronger LHD emphasis + negative prompt "right-hand drive, steering wheel on right"
  3. **Attempt 3 (image2image fallback):** If still RHD, fall back to image2image from a confirmed LHD reference image
- **Documented expected success rate:** Per PITFALL I-4 mitigation — target ≥95% LHD success rate after 3 attempts (vs ~80% single-attempt per v13.0 Volvo V2 lesson). Empirical number to be validated during IMG-05 SLA dashboard data collection.
- **Pattern generalization:** Per PITFALL I-4 mitigation #4 — the prompt + vision-verify + image2image retry pattern generalizes to other dreamina unreliability cases (gender, age, scene type). Documented in dreamina_manager.py docstring + SKILL.md pitfall update.

### `hermes dreamina stats` SLA CLI (IMG-05)
- **Implementation:** New CLI command at `kais-hermes-skills/plugins/kais_aigc/dreamina_stats.py` registered via `hermes_cli` plugin context (`ctx.register_command("dreamina_stats", ...)`).
- **Output:** Per-task latency / success rate / cost dashboard (formatted table via `rich` library already pinned).
- **Storage:** Local MetricsBuffer ring buffer (per PITFALL I-5 mitigation — v13.0 P67 observability backend is the model; sync `@contextmanager`, no `asyncio.gather`). NO GLM calls per metric (per IMG-05 success criterion explicit).
- **Location:** Persisted at `~/.hermes/metrics/dreamina_stats.jsonl` (HERMES_HOME convention).

### image2image Workflow Standardization (IMG-06)
- **Stratification by ref count:** Per STACK.md / FEATURES research recommendation — retry budget + strength parameter vary by ref-count stratum:
  - **1-ref stratum:** strength=0.75, retry budget=3 (high template fidelity; minimal creative deviation)
  - **3-ref stratum:** strength=0.65, retry budget=4 (balanced)
  - **5-ref stratum:** strength=0.55, retry budget=5 (low template fidelity per ref; creative deviation expected)
- **Standardization location:** New `references/image2image-stratification.md` in kais-jimeng-cli/skills with per-stratum parameters + rationale.
- **Validation:** Per-stratum success rate tracked in MetricsBuffer; IMG-05 dashboard reports per-stratum.

### XCUT-02 _INSTRUCTION Injection
- Per FORM/DUB precedent: define `_VISION_VERIFY_INSTRUCTION` module constant in p07_scene_images.py (P07 scene images phase module — where dreamina batch is invoked); inject via `.task(steps=[f"{_VISION_VERIFY_INSTRUCTION}"])` AND `.constraints(["MUST vision-verify before ComfyUI upload"]); assert via goal-content test. Same MAX_CONSTRAINTS=7 budget rule.

### Claude's Discretion
- Exact retry/backoff parameters (within IMG-01 + IMG-04 guidelines)
- GLM-4.6V API integration details (endpoint, model name, request schema — RESEARCH should verify these against live deployment)
- MetricsBuffer ring buffer size (default 1000 entries? align with v13.0 P67 precedent)
- `hermes dreamina stats` output formatting (table vs JSON vs both)
- Cache TTL for vision-verify sha256-keyed results (default 24h? infinite?)
- Test framework conventions (pytest vs standalone script — match existing kais_aigc plugin tests)

</decisions>

<canonical_refs>
## Canonical Refs (Phase 73 downstream agents MUST read)

**Hermes-agent repo (GSD planning context):**
- `.planning/ROADMAP.md` — Phase 73 section (lines 74-90)
- `.planning/REQUIREMENTS.md` — IMG-01..06 (lines 32-37)
- `.planning/research/v14-4track-upgrade/SUMMARY.md` — IMG research flag (line 153), GLM-4.6V LHD/RHD gap (line 203)
- `.planning/research/v14-4track-upgrade/ARCHITECTURE.md` — Pattern 2: Vision-Verify Pipeline; IMG touch points
- `.planning/research/v14-4track-upgrade/PITFALLS.md` — I-1 (vision-verify bottleneck BLOCKER), I-2 (false positives BLOCKER), I-3 (async write order BLOCKER), I-4 (RHD/LHD WARNING), I-5 (SLA observability overhead)
- `.planning/research/v14-4track-upgrade/STACK.md` — GLM-4.6V model selection, dreamina CLI version pin
- `.planning/phases/71-form/71-PATTERNS.md`, `.planning/phases/72-dub/72-PATTERNS.md` — XCUT-02 _INSTRUCTION injection pattern

**Kais-hermes-skills repo (code + refs — READ before editing):**
- `skills/kais-creative/kais-jimeng-cli/SKILL.md` — current dreamina CLI usage; pitfalls at lines 519 (FLUX forbidden), 561 (vision-verify), 570 (RHD/LHD Volvo V2 lesson), 619 (async write order bug), 621-622 (10-parallel validated), 622 (20-parallel 95%)
- `skills/kais-creative/kais-jimeng-cli/references/batch-generation-quality-control.md` — existing batch pattern (10-parallel, retry strategy, URL signature expiry)
- `plugins/kais_aigc/jimeng.py` — existing dreamina plugin code (CLI invocation, response parsing)
- `plugins/kais_aigc/plugin.yaml` — plugin manifest; add new tools/commands here
- `plugins/kais_aigc/tools.py` — existing tool registration; pattern for new dreamina_stats tool
- `plugins/kais_aigc/tests/` — existing test pattern
- `skills/kais-movie-pipeline/SKILL.md` — P07 scene images section (where _VISION_VERIFY_INSTRUCTION injects)
- `skills/kais-movie-pipeline/pipeline/phases/p07_scene_images.py` (or equivalent) — target for _INSTRUCTION injection

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`plugins/kais_aigc/jimeng.py`:** Existing dreamina CLI invocation patterns, response parsing, error handling — direct base for dreamina_manager.py.
- **`references/batch-generation-quality-control.md`:** Existing batch pattern (10-parallel, retry strategy, URL signature expiry ~30min) — semantic twin for dreamina_manager.py docs.
- **v13.0 P67 MetricsBuffer:** Per PITFALL I-5 — sync `@contextmanager`, no `asyncio.gather`. Pattern template for IMG-05 SLA tracking.
- **tenacity library** — already pinned in pyproject.toml; used by Hermes agent retry_utils.py.

### Established Patterns
- **asyncio.Semaphore concurrency cap:** Phase 71 form_factor precedent for strict-enum validation; this phase uses Semaphore for async concurrency.
- **Pydantic Literal strict enum:** Pattern continues for any new config fields.
- **Cross-repo split:** Code in kais-hermes-skills, planning in hermes-agent.
- **Per-tier commit granularity:** Match Phase 71/72 precedent (orchestrator / vision-verify / CLI / standardization as separate commits).

### Integration Points
- `dreamina_manager.py` orchestrator invoked from:
  - P07 scene images phase module (batch image generation)
  - P11 video render (reference image backfill queue per ARCHITECTURE.md Pattern 2)
- `vision_verify.py` gate invoked BEFORE:
  - ComfyUI upload (`upload_to_comfyui()` helper)
  - Pipeline state write (via dreamina_manager.py block-on-all semantic)
- `hermes dreamina stats` CLI:
  - Reads MetricsBuffer JSONL at `~/.hermes/metrics/dreamina_stats.jsonl`
  - Registered via kais_aigc plugin context

</code_context>

<specifics>
## Specific Ideas

- **Volvo V2 lesson preservation:** The RHD/LHD pattern from v13.0 P65 Volvo V2 lesson (line 570) MUST be referenced in IMG-04 implementation. The 3-attempt budget closes the lesson.
- **Cache TTL for vision-verify:** 24h default — long enough to amortize cost across re-runs of same image in iterative editing; short enough to invalidate stale results if reference image changes.
- **GLM-4.6V model name:** Per STACK.md, GLM-4.6V is the vision model. RESEARCH should verify exact API endpoint + request schema against live deployment (zai provider or Hermes-hosted?).
- **MetricsBuffer ring buffer size:** 1000 entries default — ~1 week of operator data at typical pipeline scale. Configurable via `dreamina_stats_buffer_size` config.
- **`hermes dreamina stats` output format:** Rich-formatted table by default (latency p50/p95, success rate per stratum, cost); `--json` flag for machine-readable.
- **image2image reference paths:** Per ARCHITECTURE.md — backfill queue is `list of (image_path, character_id, scene_id, form_factor)` per Pattern 2.

</specifics>

<deferred>
## Deferred Ideas

- **IMG-07 (auto-scaling concurrency):** Current 10-parallel is validated stable. Auto-tune adds complexity without payoff until quota wall hit. v15+.
- **IMG-08 (multi-model routing — dreamina 5.0 vs Seedance 2.0):** Defer until v14.0 dreamina_manager pattern proven. v15+.
- **IMG-09 (vision-verify false-positive threshold calibration):** Research gap — needs production data to tune. v15+ with IMG-05 dashboard data.
- **Real-time vision-verify streaming during generation:** Race-condition architecture; current sync queue model sufficient.
- **Multi-language vision-verify prompts:** Default Chinese (matches dreamina output language); English support deferred.
- **Vision-verify model upgrade path:** If GLM-4.6V gets deprecated, migration to next vision model is v15+ concern.

</deferred>
