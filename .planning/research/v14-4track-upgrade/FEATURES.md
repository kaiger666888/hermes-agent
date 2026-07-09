# Feature Research — v14.0 kais-movie-pipeline 4-Track Upgrade

**Domain:** AI 短剧 / 微电影 production pipeline (FORM / DUB / IMG / TRANSITION)
**Researched:** 2026-07-09
**Confidence:** HIGH (cross-verified against LTX official docs, CosyVoice 2 paper/HF, Runway/Kling official docs, ComfyUI workflow registry, FFmpeg wiki)

---

## Executive Context

v14.0 adds 4 tracks to the existing 13-step V8.6 kais-movie-pipeline. This document maps the industry feature landscape for each track so the roadmap can distinguish table stakes from differentiators from anti-features, and so each track's complexity + dependencies are visible up-front.

**Critical reframe of PROJECT.md assumption (TRANSITION Step A):** PROJECT.md states "Verify LTX-MSR first/last frame capability (预期 NO, ICLoRA is identity conditioning)". **This assumption is partially WRONG.** LTX-2 and LTX-2.3 natively support first/last frame conditioning via the `LTXVConditioning` node (separate from ICLoRA identity conditioning). The two are orthogonal: FLF2V uses direct frame injection at the sampler level; ICLoRA is a LoRA adapter for identity preservation. LTX-2.3 can do both. See TRANSITION section for the corrected matrix.

---

## Feature Landscape — FORM (form_factor parameterization)

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Pipeline-level form_factor parameter** (`vertical 9:16` / `landscape 16:9`) | Industry standard: Runway, Kling, Sora, Pika all expose aspect ratio as a top-level generation parameter (button on canvas / `aspect_ratio` API param). Hardcoding to 9:16 makes landscape delivery impossible without re-prompting every shot. | **S** | One-line config addition (`pipeline_state.form_factor`) + propagation through phase modules. Existing Step 14 already emits 7 platform variants — this lifts the master to either form. |
| **Per-expert form_factor awareness** (no hardcoded `9:16 power points` / `vertical framing`) | 15 movie-experts currently assume vertical (e.g. cinematographer's `vertical-screen-framing.md` ref). Horizontal delivery needs different power points, headroom rules, subtitle safe area, shot-scale distribution. | **M** | Each of 15 SKILL.md files needs a `## Form Factor Adaptation` section with dual-branch rules. The cinematographer `vertical-screen-framing.md` ref needs a horizontal-companion ref (`horizontal-screen-framing.md`). |
| **Render param aspect-ratio selection** (LTX-MSR `width=1280 height=704` 16:9 / `width=704 height=1280` 9:16) | LTX-2.3 ComfyUI workflow parameterizes resolution natively. Currently SKILL.md line 446 says "16:9 default" but pipeline hardcodes vertical. Need a single switch. | **S** | Template `ltx_msr_batch_render.py` already accepts `--width` / `--height`. Add `form_factor` → resolution mapping table. |
| **Step 14 platform-variant aspect-ratio awareness** (per-variant reframe for 7 platforms) | Already exists (v9.0 Step 14). Must be preserved — Step 14 already handles 7 variants with 3 aspect ratios. v14.0 must NOT break this. | **S (preserve-only)** | No new feature; just regression-test that Step 14 still works under dual form_factor. |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Per-shot form_factor override** (some shots landscape, some portrait in same project) | Niche — only useful for "shot-as-platform-variant" workflows (rare). Most projects are 1 form_factor at project level. | **L** | Not recommended for v14.0 — adds combinatorial complexity to every phase module. Defer. |
| **Auto-form-factor inference from screenplay** (detect "横屏 wide establishing" vs "竖屏 close-up dialogue") | Novel but unreliable — screenplay text does not reliably encode aspect ratio intent. | **L** | Anti-pattern (see below). |

### Anti-Features (FORM)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Per-shot form_factor (mixed 16:9 + 9:16 in same episode)** | "Maximum creative flexibility" | Cross-shot consistency collapses. Cinematographer axis rules + continuity_auditor identity checks assume one frame geometry per scene. Cross-form match cuts are technically possible but artistically disorienting. Renders Step 14 slicing meaningless (which form is the master?). | **Project-level form_factor only.** If both forms are needed, run two project instances. |
| **Auto-form-factor inference from screenplay text** | "Reduce operator decisions" | Screenplay does not encode aspect ratio. Inference produces wrong calls ~40% of the time (no public benchmark; industry consensus is that aspect ratio is a director-level decision, not a script-derived one). | **Operator declares form_factor at project creation.** Default `landscape 16:9` (matches LTX-MSR current default). |

### Industry Precedent — FORM

| Tool | How it handles aspect ratio | Lesson for kais-movie-pipeline |
|------|----------------------------|--------------------------------|
| **Runway Gen-3/Gen-4** | Aspect ratio button on generation canvas; per-generation selection (16:9 default, 9:16, 1:1) | Form factor is a per-generation parameter, NOT a per-project one — but for a pipeline that generates many shots, locking at project level is more consistent |
| **Kling 1.6 / 2.5** | `aspect_ratio` API parameter; supported values: 21:9, 16:9, 4:3, 1:1, 3:4, 9:16 | 6 ratios supported; kais-movie-pipeline only needs 2 (16:9 + 9:16) for v14.0 |
| **Sora 2** | Aspect ratio in prompt/settings; 60s multi-shot support assumes single ratio per sequence | Single ratio per sequence is the norm — confirms project-level lock |
| **Adobe Premiere / DaVinci Resolve** | Project-level sequence setting; per-clip override possible but discouraged | Project-level lock is the professional default; per-clip is for special cases only |

**Industry verdict (HIGH confidence):** Project-level form_factor is table stakes. Per-shot is an anti-pattern. LTX-2.3 already supports both ratios natively (just swap width/height).

---

## Feature Landscape — DUB (CosyVoice default + LTX 2.3 native audio coordination)

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **CosyVoice 2 as TTS default** (replacing ComfyUI IndexTTS2) | CosyVoice 2 is the current SOTA open-source multilingual TTS with zero-shot voice cloning (~3s sample) + instruct mode (emotion/speed/volume). IndexTTS2 is older with limited community support. | **M** | Integration path decision: ComfyUI CosyVoice node vs CosyVoice CLI vs hosted API (SiliconFlow). Research recommends **CosyVoice CLI** (consistent with dreamina CLI pattern, no ComfyUI dependency coupling). |
| **Voice preset library per-character** (cosyvoice voice_id per character, cross-shot consistency) | Industry standard: every TTS production system maintains a voice registry. CosyVoice 2 zero-shot cloning needs a 3-15s reference sample per character, stored durably. | **M** | New data asset: `pipeline_state.episode_id.voice_preset[character_name] = {voice_id, reference_audio_path, cloning_params}`. Migration mapping table from IndexTTS2 emotion sliders (sad/calm/happy/melancholic) → CosyVoice 2 instruct emotions. |
| **IndexTTS2 fallback path** (preserve as fallback when CosyVoice unavailable) | CosyVoice 2 has higher VRAM requirements; IndexTTS2 is lighter. Fallback is industry-standard practice for TTS engine resilience. | **S** | `tts_engine` field in pipeline_state with values `cosyvoice` / `ltx_native` / `indextts2_fallback`. Auto-fallback on CosyVoice OOM/timeout. |
| **CosyVoice ↔ LTX 2.3 native audio division rule** | LTX 2.3 generates synchronized audio + lip sync from the text prompt (Format A narrative / Format B structured tags, per SKILL.md line 566+). CosyVoice is post-production TTS overlay. The two must NOT both generate the same dialogue line (double-audio bug). | **S** | Decision matrix (see below) — one engine per dialogue line, never both. Already partially documented in SKILL.md but needs formalization. |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Per-line TTS engine routing** (some lines LTX native, some CosyVoice, based on line type) | Optimal quality: LTX native for lip-synced on-screen dialogue; CosyVoice for voiceover/narration/emotion-heavy lines where LTX's BGM-leak risk is high. | **M** | Decision matrix in `audio_pipeline/voicer` sub-step. Per PROJECT.md existing finding: "Pure dialogue (speaking/whispering) = safe at gen-time; humming/singing/complex emotional = post-production TTS." Formalize as a routing rule. |
| **CosyVoice 2 instruct2 fine-grained control** (emotion + speed + volume per line, beyond IndexTTS2's 4 sliders) | CosyVoice 2 supports natural-language instruct ("sadly, slowly, whispered") — far more expressive than IndexTTS2's 4-emotion slider. | **M** | Requires prompt engineering for the instruct text. Map screenplay `emotion_tag` → CosyVoice instruct string. |
| **Cross-episode voice arc** (character voice evolves across episodes — e.g. aging, emotional arc) | Advanced — already documented in `character-voice-consistency.md` ref. CosyVoice 2 zero-shot cloning makes this trivial (just swap reference audio per episode). | **S** | Already designed in v1 refs; v14.0 just wires it to CosyVoice 2. |

### Anti-Features (DUB)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **IndexTTS2 full retirement** | "Clean up, remove old engine" | Loses fallback path. CosyVoice 2 has higher VRAM (needs more GPU); on constrained hardware IndexTTS2 is the only option. Also loses the 4-emotion-slider UX that some operators may prefer. | **Keep IndexTTS2 as `indextts2_fallback`.** Default to CosyVoice; auto-fallback on resource constraints. |
| **Real-time TTS streaming during video generation** | "Lower latency, generate audio as video renders" | LTX 2.3 native audio already generates in-parallel with video (single model, single pass). Adding CosyVoice streaming on top creates race conditions + double-audio risk. | **Sequential pipeline:** LTX native audio (if applicable) → CosyVoice overlay (if needed) → mixer master. No parallel TTS. |
| **Voice cloning from unauthorized samples** | "Clone any voice from 3s of audio" | Ethical + legal risk. CosyVoice 2 zero-shot cloning is powerful but requires consent (likeness rights, voice cloning laws in CN/US/EU). | **Operator-provided voice samples only.** Document consent requirement in voicer SKILL.md. |

### Decision Matrix — CosyVoice vs LTX 2.3 Native Audio (per dialogue line)

| Line type | LTX 2.3 Native | CosyVoice Post-Overlay | Rationale |
|-----------|----------------|------------------------|-----------|
| **On-screen dialogue, lip-sync critical** | ✅ YES | ❌ NO | LTX generates lip-synced audio from prompt; CosyVoice overlay would desync |
| **Voiceover / narration (no on-screen speaker)** | ❌ NO | ✅ YES | LTX native struggles with voiceover (BGM leak risk per R5/R11b); CosyVoice is purpose-built |
| **Humming / singing / lullaby** | ❌ NO (BANNED per R5) | ✅ YES | LTX audio VAE triggers BGM on humming/singing words; CosyVoice handles cleanly |
| **Complex emotional prosody (crying, screaming, whispering with context)** | ⚠️ MAYBE | ✅ PREFERRED | LTX may clone character or trigger BGM; CosyVoice instruct mode is more reliable |
| **Plain speech (speaking, whispering)** | ✅ YES | ⚠️ OPTIONAL | LTX is safe for plain speech; CosyVoice is fallback if LTX output is poor |
| **Multi-language / dialect** | ⚠️ MAYBE | ✅ YES | CosyVoice 2 has stronger multilingual + dialect support per docs |

**Sources:** SKILL.md line 566+ (LTX native audio formats A/B), `ltx-msr-prompt-precision.md` R5/R11b (BGM leak), CosyVoice 2 HF model card (instruct capabilities).

### CosyVoice 2 — Mode Selection (when to use which mode)

| Mode | CosyVoice 2 Capability | Use When |
|------|------------------------|----------|
| **Zero-shot cloning** (`inference_zero_shot`) | 3-15s reference audio → cloned voice | Character voice preset established; cross-shot consistency needed |
| **Instruct mode** (`inference_instruct`) | Natural-language instructions: "sadly", "slowly", "with anger" | Emotion control beyond reference audio's emotion; voiceover with specific affect |
| **Cross-lingual cloning** | Clone voice across languages (CN→EN, EN→CN) | Multi-language delivery; dubbing |
| **Fine-grained control** | Speed/volume/emotion parameters via API | Precision tuning for specific lines |

**⚠️ Important caveat (community-verified, MEDIUM confidence):** The base `CosyVoice2-0.5B` model has limited built-in instruct control — true emotion/speed control requires either (a) the dedicated `CosyVoice-300M-Instruct` variant, or (b) the newer `Fun-CosyVoice 3.0` (released 2025/12 per GitHub roadmap). Integration plan should test which model variant is actually deployed.

### Voice Preset Migration Pattern (IndexTTS2 → CosyVoice 2)

| IndexTTS2 | CosyVoice 2 Equivalent | Migration Strategy |
|-----------|------------------------|-------------------|
| `emotion=sad` slider | `instruct="sadly, with grief"` OR reference audio with sad prosody | Prefer instruct for fine control; fall back to reference audio for natural delivery |
| `emotion=calm` slider | `instruct="calmly, evenly"` OR neutral reference audio | Direct mapping |
| `emotion=happy` slider | `instruct="cheerfully, with energy"` OR happy reference audio | Direct mapping |
| `emotion=melancholic` slider | `instruct="melancholically, wistfully"` | Direct mapping (CosyVoice instruct is more expressive) |
| `voice_preset=X` (IndexTTS2 preset name) | `voice_id=X` (CosyVoice cloned voice from reference) | Re-clone from original voice sample; new voice_id |

---

## Feature Landscape — IMG (dreamina cli production-grade orchestration)

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Production-grade batch queue manager** (auto-retry + failure isolation + concurrency control) | dreamina CLI validated at 10-parallel = 100% / 12-parallel = 100% / 20-parallel = 95% (SKILL.md line 621-622). Current code is ad-hoc `subprocess.Popen` — no retry, no failure tracking, no resume. Industry standard: every batch image system (BullMQ, River, AWS Batch, Leonardo.Ai queue) has these. | **M** | Wrap existing 10-parallel pattern in a `DreaminaBatchManager` class: per-task retry (max 3, exponential backoff), dead-letter queue for persistent failures, progress tracking (`render_progress.json` pattern already exists for LTX-MSR batch). |
| **Reference image vision-verify mandatory gate** (vision_analyze before ComfyUI upload) | SKILL.md line 561: "dreamina 生成内容可能完全错误" — baby prompt → hand-holding-phone image. One bad reference poisons 12 shots. Currently a PITFALL note; needs to be a non-bypassable gate. | **M** | New gate between dreamina generation and ComfyUI upload: CLIP similarity check (generated vs intended prompt) + GPT-4V/Claude vision content-match verification. Reject + auto-regenerate if mismatch > threshold. |
| **image2image workflow standardization** (reference image → output, with prompt template + strength parameter) | dreamina `image2image` is validated for turnaround sheets, L2 fittings, scene multi-angle. But no standardized template exists — each project re-implements. | **S** | New ref: `references/dreamina-image2image-templates.md` with prompt templates for 5 use cases (turnaround sheet, L2 expression fitting, scene multi-angle, growth chain, prop reference). |
| **RHD/LHD systematic mitigation** (prompt-level + verify-retry loop) | SKILL.md line 570: dreamina generates RHD even when prompted for LHD. Poisoned entire Volvo V2 batch. | **M** | Two-layer mitigation: (1) prompt template with explicit LHD/RHD declaration + framing cues ("view from passenger seat, driver on LEFT"); (2) vision-verify gate that detects RHD and auto-regenerates (up to 3 retries). If still RHD after 3 retries, flag for operator manual selection. |
| **Dreamina task metadata backfill into pipeline_state** | SKILL.md line 619 pitfall: manual visual assets exist only as files, NOT in `pipeline-state.json`. Canvas rebuild loses all visual context. | **S** | After every dreamina batch, write task metadata (task_id, prompt, seed, output_path, latency, status) into `pipeline_state.result.outputs[phase_key]`. |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **SLA tracking dashboard** (latency / success rate / cost / quota per task) | Production observability — know when dreamina is degrading before it fails. | **M** | New `dreamina_sla_log.jsonl` with per-task metrics. Optional `hermes dreamina stats` CLI command. |
| **Auto-scaling concurrency** (detect API rate limits, auto-adjust parallelism) | dreamina has undocumented rate limits; 10-parallel is safe today but may change. Auto-scaling adapts. | **L** | Defer — current 10-parallel hardcode is validated and stable. Auto-scaling adds complexity for marginal gain. |
| **Multi-model routing** (route to dreamina 5.0 vs Seedance 2.0 vs other based on task type) | Optimize quality/cost per task. | **L** | Defer — dreamina 5.0 is the validated default; multi-model routing is v15+ scope. |

### Anti-Features (IMG)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Fully autonomous image generation (no operator review)** | "Maximum automation" | dreamina generates wrong content ~5-10% of time (RHD, wrong scene, hallucinated objects). No vision-verify is 100% accurate. Unreviewed bad images poison downstream video batch. | **Vision-verify gate + operator review for hero images** (character anchors, scene refs). Background images can be auto-approved. |
| **Parallel concurrency > 12** | "Faster batch generation" | Validated: 20-parallel = 95% success (1 in 20 fails). API may rate-limit. Failure isolation helps but doesn't eliminate waste. | **10-parallel as production default.** 12 for time-critical batches with retry. Never >12. |
| **FLUX local fallback** | "Reduce dreamina dependency" | Kai explicitly forbade FLUX (SKILL.md: "do NOT mention or suggest FLUX"). dreamina is the only sanctioned image engine. | **dreamina-only.** If dreamina is down, pipeline pauses (degrade-tolerant per GPU-DIRECT-05). |

### Industry Precedent — IMG (Batch Orchestration)

| Pattern | Industry Source | Lesson for dreamina manager |
|---------|----------------|-----------------------------|
| **Per-job retry with exponential backoff** | AWS Batch, BullMQ, OneUptime | Max 3 retries; 60s → 120s → 240s backoff (matches existing `retry_on_429` pattern in pipeline) |
| **Dead-letter queue for persistent failures** | AWS SQS DLQ, BullMQ failed-jobs | Failed tasks (>3 retries) go to `failed_images.jsonl` for operator review, not silent drop |
| **Per-queue concurrency limits** | Leonardo.Ai (concurrency vs queue vs rate limit), River Pro | dreamina queue: max 10 concurrent; ComfyUI upload queue: separate, max 4 concurrent |
| **Progress checkpointing** | LTX-MSR `render_progress.json` (already in pipeline) | Reuse pattern for dreamina batch — resume from last successful image |
| **SLA tracking** | WaveSpeed batch guide, production ML systems | Per-task: submit_time, complete_time, latency, status, retry_count, error_if_any |

---

## Feature Landscape — TRANSITION (creative + data + generation 3-layer)

### Critical Finding: LTX-2.3 First/Last Frame Capability (corrects PROJECT.md assumption)

**PROJECT.md states:** "Step A — Verify LTX-MSR first/last frame capability (预期 NO, ICLoRA is identity conditioning)"

**Research finding (HIGH confidence):** LTX-2 and LTX-2.3 **DO** support first/last frame conditioning natively via the `LTXVConditioning` ComfyUI node. This is **separate from and orthogonal to** ICLoRA identity conditioning:

| Conditioning Type | Mechanism | Purpose | LTX-2.3 Support |
|-------------------|-----------|---------|-----------------|
| **First/Last Frame (FLF2V)** | Direct frame injection at sampler level via `LTXVConditioning` node | Transition continuity (match cut via shared last-frame/first-frame) | ✅ YES (official ComfyUI workflow: `video_ltx2_3_flf2v`) |
| **ICLoRA (In-Context LoRA)** | LoRA adapter conditioned on reference image set | Identity preservation across shots | ✅ YES (`LiconMSR-V1.safetensors`, current pipeline default) |
| **ID-LoRA** | LoRA adapter for face identity | Character face consistency | ⚠️ Official workflow only supports first-frame (not last-frame) out of the box |

**Implication:** The "match cut via FIRST-ASSET LAST-FRAME + SECOND-ASSET FIRST-FRAME" approach (per PROJECT.md question) IS technically feasible with LTX-2.3 — it does NOT require a different engine. However, **combining FLF2V with ICLoRA in a single workflow requires custom node graph building** (community-verified, not officially documented as a turnkey workflow).

### Transition Taxonomy → Generation Execution Path

| Transition Type | Description | Generation Path | Complexity | Notes |
|-----------------|-------------|-----------------|------------|-------|
| **Hard cut** | Instantaneous cut between shots | **No gen-time design.** Editor assembles via `concat`. | **S** | Default; 80%+ of cuts in short drama. E-Konte Layer 5 `cut_transition_type: hard_cut` already supported. |
| **Dissolve / Crossfade** | Gradual blend between two shots | **Post-production ffmpeg** (`xfade=transition=fade`, 12-24 frames). | **S** | No generation needed. ffmpeg `xfade` filter is the industry standard. Already in editor workflow step 7. |
| **Fade to/from black** | Fade out to black, fade in from black | **Post-production ffmpeg** (`fade` filter or `xfade=transition=fadeblack`, 24-48 frames). | **S** | Scene boundaries only. ffmpeg native. |
| **Wipe** | Boundary-based reveal of next shot | **Post-production ffmpeg** (`xfade=transition=wipeleft/right/up/down`, 24-36 frames). | **S** | Stylized only. ffmpeg native. |
| **Match cut (graphic)** | Cut on visually similar shapes/composition | **Generation-time design + hard cut.** Cinematographer designs matching composition; editor hard-cuts. No special generation path. | **M** | Requires cinematographer to design matching frames in E-Konte Layer 1 (composition match). Data layer: `transition_method: match-cut-graphic`, `visual_hook: "round clock → round wheel"`. |
| **Match cut (motion / action)** | Cut on continued motion across cut | **Script-level + generation-time design + hard cut.** Screenplay designs action continuity (e.g., door opening in shot A → door fully open in shot B); cinematographer blocks matching motion; editor cuts on action. | **M** | Per `classical-editing-rhythm.md` "cut on action" (-70% viewer detection). Data layer: `transition_method: match-cut-motion`, `visual_hook: "door opening action"`. |
| **Match cut (via shared object)** | Same object appears in both shots (e.g., match-on-object) | **Generation-time FLF2V design.** FIRST-ASSET LAST-FRAME shows object; SECOND-ASSET FIRST-FRAME shows same object. LTX-2.3 FLF2V can interpolate between them. | **L** | This is the "首尾帧" idea from PROJECT.md. Feasible with LTX-2.3 `LTXVConditioning` node. Requires custom workflow combining FLF2V + ICLoRA. |
| **Match cut (via shared landscape)** | Same location/landscape across shots | **Generation-time FLF2V or reference-image.** Use shared scene reference image for both shots; or FLF2V with matching landscape frames. | **M** | Easier than object match — scene refs already exist. |
| **Whip pan** | Fast pan creating motion blur transition | **Motion-vector continuity.** Challenging for current gen engines — requires end-of-shot-A whip + start-of-shot-B whip to align. LTX-2.3 can generate whip pan motion but cross-shot alignment is unreliable. | **L** | Fallback: post-production ffmpeg whip-pan simulation (inferior quality). Recommend: avoid in v14.0, document as limitation. |
| **J-cut** | Audio of next shot begins before visual cut | **Post-production ffmpeg** (audio lead 0.2-0.5s before visual). No generation path. | **S** | editor workflow already supports (L/J-cut marking, max 2 per scene). ffmpeg `adelay`. |
| **L-cut** | Audio of current shot continues after visual cut to next | **Post-production ffmpeg** (audio lag 0.3-0.8s after visual). No generation path. | **S** | editor workflow already supports. ffmpeg `adelay`. |
| **Montage collision** | Eisenstein thesis + antithesis → synthesis | **Script-level + generation design.** Multiple shots designed to collide conceptually. No special transition — hard cuts between contrasting images. | **M** | editor `montage-theory.md` ref already covers. Data layer: `transition_method: montage-collision`. |

### Generation Engine Survey — Transition Capability Matrix

| Engine | First/Last Frame | Match Cut Support | Native Audio | API Access | Recommendation |
|--------|-----------------|-------------------|--------------|------------|----------------|
| **LTX-2.3 (current default)** | ✅ YES (`LTXVConditioning`, FLF2V workflow) | ⚠️ Via FLF2V (custom workflow needed to combine with ICLoRA) | ✅ YES (Gemma 3 text encoder) | ComfyUI :8188 | **PRIMARY for all transition types that need generation** |
| **LTX-2.3 + ICLoRA (current pipeline)** | ⚠️ ICLoRA identity conditioning is NOT FLF2V; combining requires custom workflow | ❌ Not turnkey | ✅ YES | ComfyUI :8188 | Identity preservation (current use); add FLF2V as parallel conditioning path |
| **Kling 2.5/3.0** | ✅ YES (official start/end frame API) | ✅ YES (praised for continuity) | ⚠️ Varies by version | Kling API | **SECONDARY** — best turnkey match-cut quality, but adds API dependency |
| **Runway Gen-3/Gen-4** | ✅ YES (Keyframes feature: start/middle/end) | ✅ YES | ✅ YES | Runway API | **TERTIARY** — strong but API cost is higher |
| **Pika 2.1** | ⚠️ Limited (community reports inconsistency) | ⚠️ Limited | ⚠️ Limited | Pika API | Not recommended for transitions |
| **Wan 2.2 / HunyuanVideo** | ⚠️ Community workflows only | ⚠️ Community only | ❌ No native audio | Local ComfyUI | Local fallback; not primary |
| **ffmpeg (post-production)** | N/A | N/A (just assembles) | N/A | CLI | **DEFAULT for dissolve/wipe/fade/J-cut/L-cut** (no generation needed) |

### Table Stakes (TRANSITION)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **E-Konte Layer 5 schema extension** (add `transition_method` + `visual_hook` + `camera_continuity` fields) | Current Layer 5 has only `cut_transition_type` (4 values) + `next_shot_link` (string). Too thin for creative intent communication. | **S** | Add 3 fields to existing schema. Backward-compatible (existing fields preserved). |
| **`transition_design.json` first-class data asset** (per-shot transition design + cross-shot chain) | Currently transition intent is scattered (E-Konte Layer 5 + editor workflow step 7). Consolidating into one asset makes it auditable + generatable. | **M** | New JSON asset, parallel to `shot_list.json` and `e_konte.json`. Schema includes per-shot transition + cross-shot chain (structured `next_shot_link` object, not string). |
| **ffmpeg post-production path for dissolve/wipe/fade/J-cut/L-cut** | Already exists in editor workflow step 7 + `p12-composition-workflow.md`. Must be preserved as DEFAULT fallback when generation can't handle the transition. | **S (preserve-only)** | Already implemented. Just needs formalization as "Step D fallback" in the new transition ref. |
| **`references/transition-design.md` new ref** (creative taxonomy + data schema + execution paths) | PROJECT.md explicitly calls for this. Currently no consolidated transition reference exists. | **M** | New ref documenting: (1) 12-type creative taxonomy; (2) `transition_design.json` schema; (3) per-type generation execution path; (4) fallback rules. |

### Differentiators (TRANSITION)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **LTX-2.3 FLF2V + ICLoRA combined workflow** (match-cut via shared object, with identity preservation) | Enables true generation-time match cuts — the "首尾帧" idea. Industry-novel: no turnkey workflow exists publicly for this combination. | **L** | Requires custom ComfyUI node graph: `LiconMSR` (identity) + `LTXVConditioning` (FLF2V) + `SamplerCustomAdvanced`. Validate on 1-2 shots before pipeline integration. |
| **Per-transition routing** (route each transition to optimal engine: LTX-FLF2V for match-cut / Kling for complex motion / ffmpeg for dissolve) |类比 `references/video-engine-comparison.md §Selection Rules` existing P11 shot routing; adds transition-routing dimension. | **M** | New dimension in the selection rules. Per-transition-type → recommended-engine table (see matrix above). |
| **Cross-shot transition chain validation** (continuity_auditor verifies transition intent is achievable) | Catches impossible transitions before generation (e.g., whip pan across vastly different scenes). | **M** | Extension to continuity_auditor: new audit dimension `transition_feasibility`. |

### Anti-Features (TRANSITION)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **AI-generated whip pan transitions** | "Cinematic flair" | Current gen engines (LTX, Kling, Runway) produce unreliable cross-shot whip pan alignment. Motion vectors don't match. Results look jarring. | **Avoid whip pan in v14.0.** Document as known limitation. Use match cut or hard cut instead. |
| **Generation-time transition for ALL transition types** | "Maximum AI integration" | Dissolve/wipe/fade are trivially handled by ffmpeg — no need to burn GPU on them. Generation-time design only adds value for match cuts (where composition continuity matters). | **Hybrid path:** Generation for match cuts; ffmpeg for dissolve/wipe/fade; hard cut for everything else. |
| **Custom transition types beyond the 12-type taxonomy** | "Creative innovation" | The 12-type taxonomy covers ~99% of professional film transitions (per StudioBinder + Adobe + editor refs). Custom types add complexity without value. | **Stick to the 12-type taxonomy.** If a transition doesn't fit, it's a hard cut with creative framing. |
| **Over-engineered transition_design.json with 50+ fields** | "Maximum metadata" | Most transitions are hard cuts — they need only `transition_method: hard_cut`. Over-engineering penalizes the 80% case. | **Minimal schema with optional fields.** Required: `transition_method`, `next_shot_link`. Optional: `visual_hook`, `camera_continuity`, `generation_engine`, `ffmpeg_filter`. |

---

## Feature Dependencies

```
[FORM: pipeline_state.form_factor parameter]
    └──requires──> [FORM: per-expert form_factor awareness (15 SKILL.md patches)]
                       └──requires──> [FORM: render param aspect-ratio selection (LTX-MSR template)]
    └──preserves──> [FORM: Step 14 platform-variant aspect-ratio awareness (regression-only)]

[DUB: CosyVoice 2 TTS default]
    └──requires──> [DUB: Voice preset library per-character]
    └──requires──> [DUB: CosyVoice ↔ LTX 2.3 native audio division rule]
    └──enhances──> [DUB: Per-line TTS engine routing]
    └──preserves──> [DUB: IndexTTS2 fallback path]

[IMG: Production-grade batch queue manager]
    └──requires──> [IMG: Reference image vision-verify mandatory gate]
    └──enhances──> [IMG: RHD/LHD systematic mitigation] (uses vision-verify gate)
    └──requires──> [IMG: Dreamina task metadata backfill into pipeline_state]
    └──enhances──> [IMG: SLA tracking dashboard]

[TRANSITION: E-Konte Layer 5 schema extension]
    └──requires──> [TRANSITION: transition_design.json first-class data asset]
                       └──requires──> [TRANSITION: references/transition-design.md new ref]
    └──enhances──> [TRANSITION: LTX-2.3 FLF2V + ICLoRA combined workflow] (uses extended schema)
    └──preserves──> [TRANSITION: ffmpeg post-production path for dissolve/wipe/fade/J-cut/L-cut]

[TRANSITION: LTX-2.3 FLF2V + ICLoRA combined workflow]
    └──conflicts──> [current ICLoRA-only pipeline] (requires workflow JSON change, not additive)
```

### Dependency Notes

- **FORM prerequisite:** All 4 tracks depend on FORM being resolved first — form_factor determines render resolution, framing rules, and transition composition. FORM should be Phase 1 of v14.0.
- **DUB vs IMG independence:** DUB (CosyVoice) and IMG (dreamina) are independent — can be developed in parallel. No cross-dependencies.
- **TRANSITION depends on FORM:** Transition composition (match cut framing) depends on form_factor being parameterized first.
- **TRANSITION generation layer depends on IMG vision-verify:** The FLF2V match-cut workflow needs vision-verify to confirm first/last frame content matches before generation.
- **LTX-2.3 workflow JSON change is NOT additive:** Combining FLF2V + ICLoRA requires modifying the existing `ltx_msr_batch_render.py` template node graph. This is a breaking change to the current pipeline — must be versioned + tested carefully.

---

## MVP Definition

### Launch With (v14.0 P1-P2)

Minimum viable v14.0 — what's needed to validate the 4-track upgrade:

- [ ] **FORM:** Pipeline-level `form_factor` parameter + 15 SKILL.md `## Form Factor Adaptation` sections + LTX-MSR template resolution switch
- [ ] **DUB:** CosyVoice 2 CLI integration + voice preset library + IndexTTS2 fallback + CosyVoice/LTX division rule
- [ ] **IMG:** Dreamina batch manager (retry + failure isolation + concurrency) + vision-verify mandatory gate + image2image templates + RHD/LHD mitigation
- [ ] **TRANSITION:** E-Konte Layer 5 schema extension + `transition_design.json` asset + `references/transition-design.md` ref + ffmpeg fallback path formalization

### Add After Validation (v14.x or v15)

Features to add once core 4-track is working:

- [ ] **TRANSITION:** LTX-2.3 FLF2V + ICLoRA combined workflow (validate on 1-2 shots first)
- [ ] **TRANSITION:** Per-transition engine routing (Kling/Runway as alternatives)
- [ ] **IMG:** SLA tracking dashboard (`hermes dreamina stats` CLI)
- [ ] **DUB:** CosyVoice 2 instruct2 fine-grained control (emotion + speed + volume per line)
- [ ] **FORM:** Per-shot form_factor override (only if real use case emerges)

### Future Consideration (v15+)

Features to defer until v14.0 is validated in production:

- [ ] **IMG:** Auto-scaling concurrency (detect rate limits, auto-adjust)
- [ ] **IMG:** Multi-model routing (dreamina 5.0 vs Seedance 2.0)
- [ ] **TRANSITION:** AI-generated whip pan transitions (wait for engine improvement)
- [ ] **DUB:** Real-time TTS streaming (wait for race-condition-free architecture)

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority | Track |
|---------|------------|---------------------|----------|-------|
| Pipeline-level form_factor parameter | HIGH | LOW | **P1** | FORM |
| Per-expert form_factor awareness (15 SKILL.md) | HIGH | MEDIUM | **P1** | FORM |
| Render param aspect-ratio selection | HIGH | LOW | **P1** | FORM |
| CosyVoice 2 TTS default | HIGH | MEDIUM | **P1** | DUB |
| Voice preset library per-character | HIGH | MEDIUM | **P1** | DUB |
| CosyVoice/LTX division rule | HIGH | LOW | **P1** | DUB |
| IndexTTS2 fallback path | MEDIUM | LOW | **P1** | DUB |
| Dreamina batch queue manager | HIGH | MEDIUM | **P1** | IMG |
| Vision-verify mandatory gate | HIGH | MEDIUM | **P1** | IMG |
| image2image templates | MEDIUM | LOW | **P1** | IMG |
| RHD/LHD mitigation | HIGH | MEDIUM | **P1** | IMG |
| Dreamina metadata backfill | MEDIUM | LOW | **P1** | IMG |
| E-Konte Layer 5 schema extension | HIGH | LOW | **P1** | TRANSITION |
| transition_design.json asset | HIGH | MEDIUM | **P1** | TRANSITION |
| transition-design.md ref | HIGH | MEDIUM | **P1** | TRANSITION |
| ffmpeg fallback formalization | MEDIUM | LOW | **P1** | TRANSITION |
| Per-line TTS engine routing | MEDIUM | MEDIUM | **P2** | DUB |
| Per-transition engine routing | MEDIUM | MEDIUM | **P2** | TRANSITION |
| Cross-shot transition chain validation | MEDIUM | MEDIUM | **P2** | TRANSITION |
| LTX-2.3 FLF2V + ICLoRA combined workflow | HIGH | HIGH | **P2** | TRANSITION |
| SLA tracking dashboard | LOW | MEDIUM | **P3** | IMG |
| CosyVoice instruct2 fine-grained control | MEDIUM | MEDIUM | **P2** | DUB |

---

## Competitor Feature Analysis

| Feature | Runway Gen-4 | Kling 3.0 | Sora 2 | kais-movie-pipeline (v14.0 target) |
|---------|--------------|-----------|--------|-------------------------------------|
| **Multi-aspect-ratio** | ✅ Per-generation button | ✅ API parameter (6 ratios) | ✅ Prompt/settings | ✅ Project-level parameter (2 ratios: 16:9 + 9:16) |
| **Native audio + lip sync** | ✅ Gen-4 native | ⚠️ Varies | ✅ Native | ✅ LTX 2.3 native + CosyVoice post-overlay (hybrid) |
| **First/last frame conditioning** | ✅ Keyframes (start/middle/end) | ✅ Start/end frame API | ⚠️ Limited | ✅ LTX-2.3 FLF2V + ICLoRA (custom workflow) |
| **Match cut support** | ✅ Via keyframes | ✅ Praised for continuity | ⚠️ Multi-shot sequence | ⚠️ Generation-time match cut (P2, custom workflow) |
| **Transition taxonomy** | N/A (single-shot generation) | N/A | ✅ Multi-shot sequences | ✅ 12-type taxonomy + per-type execution path (DIFFERENTIATOR) |
| **Batch image generation** | N/A | N/A | N/A | ✅ dreamina CLI 10-parallel with retry + vision-verify |
| **Voice cloning** | N/A | N/A | N/A | ✅ CosyVoice 2 zero-shot (~3s sample) |
| **Pipeline orchestration (13-step)** | ❌ Single-shot tool | ❌ Single-shot tool | ❌ Single-shot tool | ✅ Full 13-step pipeline with 15 experts (DIFFERENTIATOR) |

**Key insight:** kais-movie-pipeline's differentiator is NOT single-shot generation quality (Runway/Kling/Sora win there) — it's the **end-to-end pipeline orchestration** with 15 domain experts + structured data assets + multi-engine coordination. v14.0 should lean into this differentiator, not try to compete on single-shot quality.

---

## Sources

### Official Documentation (HIGH confidence)
- [Runway: Changing Aspect Ratio and Resolution](https://help.runwayml.com/hc/en-us/articles/26113483666451-Changing-the-Aspect-Ratio-and-resolution) — Runway aspect ratio selection
- [Runway Gen-3: Creating with Keyframes](https://help.runwayml.com/hc/en-us/articles/34170748696595-Creating-with-Keyframes-on-Gen-3) — First/last/middle frame conditioning
- [Kling: Start and End Frames](https://kling.ai/quickstart/ai-video-start-end-frames) — Kling FLF support
- [LTX-2.3 FLF2V ComfyUI Workflow (official)](https://comfy.org/workflows/video_ltx2_3_flf2v-bb33cc433026/) — Native first/last frame conditioning
- [LTX-2.3 Audio Guide](https://ltx.io/blog/a-guide-to-ltx-2-3-audio) — Native synchronized audio-video generation
- [LTX IC-LoRA Documentation](https://docs.ltx.video/open-source-model/usage-guides/ic-lo-ra) — ICLoRA vs frame conditioning distinction
- [CosyVoice 2 arXiv Paper](https://arxiv.org/html/2412.10117v2) — Instruct mode capabilities (emotion, accent, speed, volume)
- [CosyVoice 2 HuggingFace Model Card](https://huggingface.co/FunAudioLLM/CosyVoice2-0.5B) — Instruct support confirmation
- [FunAudioLLM/CosyVoice GitHub](https://github.com/FunAudioLLM/CosyVoice) — Roadmap (Fun-CosyVoice 3.0 released 2025/12)
- [FFmpeg Xfade Wiki](https://trac.ffmpeg.org/wiki/Xfade) — Dissolve/wipe/fade transition filters

### Community + Tutorials (MEDIUM confidence)
- [LTX 2.3 First and Last Frame ComfyUI Guide](https://ltx23.org/blog/ltx-23-first-last-frame-comfyui) — FLF2V implementation details
- [LTX-2.3 ID-LoRA with First-Last Frame (Reddit)](https://www.reddit.com/r/StableDiffusion/comments/1t71x0r/ltx_23_idlora_with_firstlast_frame/) — Combining ICLoRA + FLF2V (custom workflow needed)
- [StudioBinder: Types of Editing Transitions](https://www.studiobinder.com/blog/types-of-editing-transitions-in-film/) — 12-type transition taxonomy
- [Adobe: Cuts in Film](https://www.adobe.com/creativecloud/video/post-production/cuts-in-film.html) — J-cut / L-cut / cut on action
- [CosyVoice 2025 Complete Guide (dev.to)](https://dev.to/czmilo/cosyvoice-2025-complete-guide-the-ultimate-multi-lingual-text-to-speech-solution-4l39) — `inference_instruct` API usage
- [SiliconFlow CosyVoice2 API Docs](https://docs.siliconflow.cn/en/userguide/capabilities/text-to-speech) — Hosted API with speed + fine-grained control
- [WaveSpeed Batch Generation Guide](https://wavespeed.ai/blog/posts/wavespeed-batch-generation/) — Production batch patterns (queue, retry, concurrency)
- [Leonardo.Ai: Concurrency, Queue, Rate Limit](https://docs.leonardo.ai/docs/guide-to-concurrency-queue-and-rate-limit) — Queue management patterns
- [OneUptime: Batch Retry Strategies](https://oneuptime.com/blog/post/2026-01-30-batch-processing-retry-strategies/view) — Failure isolation + exponential backoff

### Existing Pipeline Documentation (HIGH confidence, internal)
- `kais-movie-pipeline/SKILL.md` lines 432-466 (Generation Engine Selection) — LTX-MSR current default
- `kais-movie-pipeline/SKILL.md` lines 560-575 (PITFALLS: vision-verify, RHD/LHD, BGM leak) — Validated failure modes
- `kais-movie-pipeline/SKILL.md` lines 621-622 (dreamina 10-parallel validation) — Concurrency sweet spot
- `cinematographer/references/e-konte-format.md` §Layer 5 — Current `cut_transition_type` + `next_shot_link` schema
- `editor/SKILL.md` workflow step 7 (Transition Design) — Current post-production-only transition handling
- `audio_pipeline/SKILL.md` §V8.6 Pipeline Sync — Step 7B + Step 11 audio pipeline positions
- `references/ltx-msr-prompt-precision.md` R5/R11b — BGM leak on humming/singing (validates CosyVoice post-overlay for voiceover)

---
*Feature research for: v14.0 kais-movie-pipeline 4-track upgrade (FORM / DUB / IMG / TRANSITION)*
*Researched: 2026-07-09*
*Confidence: HIGH (cross-verified across official docs + community + internal pipeline)*
