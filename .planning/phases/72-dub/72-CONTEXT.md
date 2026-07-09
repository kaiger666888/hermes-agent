# Phase 72: DUB - Context

**Gathered:** 2026-07-09
**Status:** Ready for planning
**Mode:** Auto-generated (user skipped smart-discuss, dispatched plan-phase directly; Claude's analyzed defaults below)

<domain>
## Phase Boundary

Users can generate TTS via CosyVoice 2.0-0.5B as the P10 default (replacing IndexTTS2), with a strict schema-enforced division rule preventing CosyVoice overlay AND LTX 2.3 native audio from both firing on the same shot, and with a benchmark-locked default variant recorded in `VERSION.json`.

Requirements covered: DUB-01 (CosyVoice 2.0-0.5B as P10 default), DUB-02 (schema-enforced division rule), DUB-03 (voice_clone_reference_wav per character), DUB-04 (IndexTTS2 DEPRECATED fallback), DUB-05 (A/B benchmark + VERSION.json default lock).

**Parallel with Phase 73 (IMG):** DUB and IMG are independent surfaces both depending only on Phase 71 (FORM — voice presets may vary by form_factor for spatial placement). They can execute in parallel.

**Out of scope (v15+ per REQUIREMENTS):** DUB-06 real-time TTS streaming; DUB-07 CosyVoice 2 instruct2 fine-grained per-line control; DUB-08 cross-shot voice_identity dimension in continuity_auditor.

</domain>

<decisions>
## Implementation Decisions

### CosyVoice ComfyUI Integration (DUB-01)
- **ComfyUI node:** `filliptm/ComfyUI_FL-CosyVoice3` (per ROADMAP / STACK research). Supports CosyVoice 2.0-0.5B + 3.0 variants via same node path.
- **Workflow JSON:** New `kais-hermes-skills/skills/movie-experts/audio_pipeline/references/workflows/cosyvoice-comfyui.json` mirroring existing IndexTTS2 workflow JSON pattern at `references/comfyui-indextts2-setup.md:33-50`.
- **Deployment doc:** New `kais-hermes-skills/skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-deployment.md` (9-step install mirroring `comfyui-indextts2-setup.md`, node loader paths, GPU VRAM budget, first-run healthcheck verification). Per audio_pipeline GAP-REPORT.md:58.
- **Pre-flight healthcheck gate:** `GET http://localhost:8188/object_info/FLCosyVoice3Instruct2` — if missing, log warning + auto-fallback to IndexTTS2 (per D-3 mitigation #2). NOT hard fail (operator friction too high on first run).
- **GPU VRAM budget:** Document CosyVoice 2.0-0.5B (~1.5GB VRAM) vs CosyVoice 3.0 (~3GB) requirements; concurrent LTX-2.3 video render budget guidance in deployment doc.

### Schema-Enforced Division Rule (DUB-02)
- **Validator location:** Dataclass-level validator on `Shot` Pydantic model: `@model_validator(mode='after')` asserting `not (shot.ltx_native_dialogue AND shot.cosyvoice_overlay)`. Per D-1 mitigation #1 (data-driven rule).
- **Engine selection rule (declarative):** `tts_engine` field on Shot:
  - `if shot.has_dialogue AND shot.lip_sync_required: tts_engine = "ltx_native"`
  - `if shot.is_voiceover OR shot.no_on_screen_character: tts_engine = "cosyvoice"`
  - `indextts2_fallback` only on CosyVoice failure
- **Error behavior:** `ValidationError` with explicit message: `"Shot {id}: cannot enable both ltx_native_dialogue AND cosyvoice_overlay (DUB-02 / PITFALL D-1)"` — strict reject (mirrors FORM-01 form_factor strict enum pattern). NO fuzzy matching, NO warning-and-continue.
- **Test coverage:** Unit test asserting validator rejects both-on, allows each-on-individually, allows both-off. NO integration test running both engines (operator-action handoff territory).

### Voice Clone Reference Wav Schema (DUB-03)
- **Storage pattern:** `voice_clone_reference_wav` field in `character_bible.json` per REQUIREMENTS prose (`pipeline_state.episode_id.character_voice_presets`); value = relative path to wav file at `assets/<episode>/voice_refs/<character>.wav` (mirrors v9.0+ platform API keys pattern).
- **Fail-fast on missing + CosyVoice clone mode:** `templates/tts_batch.py` raises `ValueError("voice_clone_reference_wav missing for character_id=X. Operator action: provide 3-10s clean sample at <path>. See DUB phase operator-action checklist.")` Per D-2 mitigation #2. NO silent fallback to predefined voice (defeats cloning purpose).
- **Validation helper:** `validate_voice_clone_ref(path)` function — 3-10s length, wav format, ≥16kHz sample rate; rejects unqualified samples before submission.
- **Migration mapping:** IndexTTS2 `voice_preset` (sad/calm/happy/melancholic) → CosyVoice voice profile mapping table at `references/voicer/indextts2-to-cosyvoice-migration.md` — operator-auditable. Per D-2 mitigation #3.

### A/B Benchmark + Fallback Chain (DUB-04 + DUB-05)
- **DUB-04 fallback trigger:** CosyVoice generation failure (timeout / garbage output / GPU OOM) OR `/object_info` healthcheck fail → auto-fallback to IndexTTS2 with DEPRECATED warning. NO manual-only fallback (operator bottleneck).
- **DEPRECATED labeling:** Log warning + workflow metadata tag + visible in `hermes dreamina stats` CLI dashboard (mirrors IMG-05 SLA dashboard). NOT log-warning-only (gets ignored).
- **DUB-05 benchmark reference lines:** Operator-provided 3-5 representative Chinese dialogue lines (emotional / voiceover / fast / slow / technical mix) — documented as operator-action handoff per ROADMAP research flag. NOT pre-existing fixtures (lower representativeness).
- **DUB-05 default lock:** Operator manual decision after reviewing side-by-side audio samples; recorded as `cosyvoice_default_variant` field in `VERSION.json` + benchmark report at `audio_pipeline/references/voicer/cosyvoice-benchmark.md`. NOT auto-pick-lower-WER (audio quality ≠ WER).

### XCUT-02 _INSTRUCTION Injection
- Per FORM phase precedent: define `_TTS_ENGINE_INSTRUCTION` module constant in p10_voice.py (or equivalent P10 phase module); inject via `.task(steps=[f"{_TTS_ENGINE_INSTRUCTION}"])` AND `.constraints(["MUST propagate tts_engine selection from Shot model"]); assert via goal-content test. Same MAX_CONSTRAINTS=7 budget rule as FORM.

### Claude's Discretion
- Exact wording of CosyVoice workflow JSON node graph
- Exact deployment doc structure (mirrors comfyui-indextts2-setup.md but adapted for CosyVoice specifics)
- Which 3-5 reference dialogue lines the operator picks for DUB-05 benchmark
- GPU VRAM budget numbers (verify against CosyVoice 2.0-0.5B actual usage)
- Test framework for `validate_voice_clone_ref()` (pytest vs standalone script)
- Whether to extend existing `_eval/` directory or create new `_eval/dub_voice_clone/` for voice clone sample fixtures

</decisions>

<canonical_refs>
## Canonical Refs (Phase 72 downstream agents MUST read)

**Hermes-agent repo (GSD planning context):**
- `.planning/ROADMAP.md` — Phase 72 section (lines 56-72)
- `.planning/REQUIREMENTS.md` — DUB-01..05 (lines 28-36)
- `.planning/research/v14-4track-upgrade/SUMMARY.md` — DUB research flags (line 146), CosyVoice variant benchmark gap (line 201)
- `.planning/research/v14-4track-upgrade/ARCHITECTURE.md` — Data Flow: TTS routing (P10 voice layer integration)
- `.planning/research/v14-4track-upgrade/PITFALLS.md` — D-1 (CosyVoice + LTX doubled audio BLOCKER), D-2 (operator wavs BLOCKER), D-3 (ComfyUI dep hell WARNING), D-5 (GPU contention), D-6 (project reconstruction backward-compat)
- `.planning/research/v14-4track-upgrade/STACK.md` — CosyVoice node selection rationale
- `.planning/phases/71-form/71-PATTERNS.md` — XCUT-02 _INSTRUCTION injection pattern (mirror for DUB)

**Kais-hermes-skills repo (code + refs — READ before editing):**
- `skills/kais-movie-pipeline/SKILL.md` — line 457 (IndexTTS2 reference, must demote); line 433 (kais-aigc-platform authoritative source rule)
- `skills/kais-movie-pipeline/references/comfyui-indextts2-setup.md` — template for new cosyvoice-deployment.md (9-step install pattern)
- `skills/kais-movie-pipeline/templates/tts_batch.py` — current IndexTTS2 TTS batch script (extend with CosyVoice path + tts_engine routing)
- `skills/movie-experts/audio_pipeline/SKILL.md` — line 78 (existing voicer/cn-tts-model-matrix.md ref); line 100 (TTS prompt engineering)
- `skills/movie-experts/audio_pipeline/references/voicer/cn-tts-model-matrix.md` — existing Hermes 6-provider TTS matrix; extend with CosyVoice primary
- `skills/movie-experts/audio_pipeline/GAP-REPORT.md` — pre-existing gap notes (CosyVoice 300M stale version; missing deployment doc)
- `skills/movie-experts/audio_pipeline/scripts/probe-tts-routing.sh` — existing TTS routing probe (extend for CosyVoice healthcheck)
- `skills/movie-experts/voicer/` — voicer sub-step (CosyVoice integration target)
- `plugins/pipeline_state/store.py` — Shot dataclass + `character_voice_presets` field (DUB-03 schema target); verify form_factor precedent for adding new fields

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`comfyui-indextts2-setup.md` (176 lines):** 9-step install pattern, node loader paths, GPU VRAM documentation, first-run verification — direct template for cosyvoice-deployment.md.
- **Existing IndexTTS2 workflow JSON pattern (`comfyui-indextts2-setup.md:33-50`):** Node graph structure for TTS generation workflow — base for cosyvoice-comfyui.json.
- **PipelineState dataclass extension pattern (FORM-01 precedent):** Adding `voice_clone_reference_wav` to character_voice_presets uses same Literal/strict-enum approach.
- **`probe-tts-routing.sh`:** Bash probe pattern for TTS provider healthchecks — extend for CosyVoice `/object_info/FLCosyVoice3Instruct2`.
- **XCUT-02 _INSTRUCTION injection pattern (FORM phase):** Defined in p09_shot_breakdown.py; same pattern applies to p10_voice.py for tts_engine propagation.

### Established Patterns
- **Dataclass schema migration with defaults:** Adding `tts_engine: Literal["ltx_native", "cosyvoice", "indextts2_fallback"] = "cosyvoice"` to Shot model — backward-compat with v1-v13 (defaults to new CosyVoice default for new projects; existing projects auto-migrate on next load).
- **Cross-repo split:** Code + refs in `kais-hermes-skills`, GSD planning in `hermes-agent`. Hermes-agent touches NOTHING except `.planning/`.
- **Operator-action handoff documentation:** Per DUB-03 voice_clone_reference_wav + DUB-05 benchmark lines — documented in operator-action-handoff section of milestone audit (Phase 76).

### Integration Points
- `Shot.tts_engine` propagates to:
  - `templates/tts_batch.py` (P10 voice layer — selects CosyVoice vs IndexTTS2 vs LTX native)
  - `pipeline/phases/p10_voice.py` (P10 phase module goal f-string — receives `_TTS_ENGINE_INSTRUCTION`)
  - `references/voicer/cn-tts-model-matrix.md` (selection guidance updated)
  - Pre-flight healthcheck in `scripts/probe-tts-routing.sh` (CosyVoice `/object_info` check added)
- `character_voice_presets[<character_id>].voice_clone_reference_wav` read by:
  - `templates/tts_batch.py` (validate path exists + 3-10s length before submitting CosyVoice clone mode)

</code_context>

<specifics>
## Specific Ideas

- **DEPRECATED warning visibility:** Per DUB-04, the DEPRECATED flag must be visible in operator-facing CLI dashboard. Reuse the `hermes dreamina stats` CLI infrastructure from IMG-05 if possible, OR add a parallel `hermes tts stats` command.
- **Cross-engine GPU contention:** Per PITFALL D-5, document GPU memory budget for CosyVoice + LTX-2.3 concurrent execution. Operator must know if they can run P10 (voice) and P11 (video) in parallel or must serialize.
- **VERSION.json schema:** `cosyvoice_default_variant` field added with values like `"cosyvoice_2.0_0.5B"` or `"fun_cosyvoice_3.0"`. Benchmark report at `cosyvoice-benchmark.md` MUST cite the specific dialogue lines tested + MOS/WER numbers + operator preference rationale.
- **Backward-compat for old projects (PITFALL D-6):** Existing projects with IndexTTS2 voice_preset values must load cleanly. Migration: `voice_preset` field preserved as legacy; new `tts_engine` defaults to `"cosyvoice"` for new projects but remains `"indextts2_fallback"` for projects with existing IndexTTS2 audio.

</specifics>

<deferred>
## Deferred Ideas

- **DUB-06 (real-time TTS streaming during video gen):** Race-condition architecture; current sync queue model sufficient. v15+ if use case emerges.
- **DUB-07 (CosyVoice 2 instruct2 fine-grained per-line control):** P2 differentiator; defer until CosyVoice 2 baseline proven in v14.0 production.
- **DUB-08 (cross-shot voice_identity dimension in continuity_auditor):** 5th dimension addition; needs production voice data to calibrate. v15+.
- **Full retirement of IndexTTS2 ComfyUI node:** Per DUB-04, kept as DEPRECATED fallback indefinitely. v15+ if CosyVoice uptime proves stable for 6+ months.
- **Multi-voice SRT dubbing (IndexTTS2ScriptDubbing equivalent for CosyVoice):** Currently CosyVoice handles one character per workflow invocation. Batch SRT dubbing wrapper deferred to v15+.

</deferred>
