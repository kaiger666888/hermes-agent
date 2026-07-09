# Project Research Summary

**Project:** v14.0 kais-movie-pipeline 4-Track Upgrade (FORM / DUB / IMG / TRANSITION)
**Domain:** AI 短剧 / 微电影 production pipeline enhancement (brownfield, continues from v13.0)
**Researched:** 2026-07-09
**Confidence:** HIGH (4 tracks cross-verified against live repo code, LTX/CosyVoice/Runway/Kling official docs, ComfyUI workflow registry, FFmpeg wiki, internal MILESTONES history)

## Executive Summary

v14.0 is a brownfield upgrade to the 13-step V8.6 kais-movie-pipeline, adding 4 parallel tracks: (1) FORM — pipeline-level `form_factor` parameterization for landscape 16:9 + portrait 9:16 dual default; (2) DUB — CosyVoice 2 TTS default + LTX 2.3 native audio division rule (replacing IndexTTS2 as primary); (3) IMG — dreamina CLI production-grade orchestration (retry, vision-verify mandatory gate, SLA tracking, RHD/LHD mitigation); (4) TRANSITION — creative + data + generation 3-layer collaboration (cinematographer Layer 5 schema + `transition_design.json` asset + engine routing). The 4 tracks share a common theme: hardening soft rules into enforced schemas, with zero new Python dependencies (all stack already pinned in `pyproject.toml`).

The recommended approach is **FORM-first, then DUB+IMG parallel, then TRANSITION last, then lineage bump**. FORM is foundational because every other track consumes `form_factor` (render resolution, framing rules, transition composition). DUB and IMG are independent of each other and can be developed in parallel. TRANSITION is most architecturally invasive (E-Konte schema migration + new asset-bus slot + 3-system canvas registration + multi-engine routing), so it lands after FORM stabilizes and after IMG's vision-verify pattern provides a reusable precedent. The whole milestone respects the cross-repo split: code + refs in `kais-hermes-skills`, GSD planning in `hermes-agent`; the only hermes-agent-side change is the final lineage bump of ~6 agent YAMLs (down from worst-case 15).

**Critical reconciliation:** The biggest finding across the 4 research docs is that **PROJECT.md's assumption about LTX first/last frame capability is partially wrong**. LTX-2.3 has TWO orthogonal capabilities — ICLoRA (identity, via `ltx/msr`) AND FLF (first-last-frame, via `ltx/fflf` + `ltx/singularityFFLF`). STACK.md was wrong to say "LTX cannot do FLF." They are separate ComfyUI workflows with no merged turnkey option today, but the TRANSITION generation layer must evaluate FLF seriously per-transition rather than assume LTX is FLF-incapable. The other key risk is **the recurring "文档有规则,代码没执行" META-RULE (X-2)** — every MUST added to SKILL.md must also be injected as a `_INSTRUCTION` constant into the phase module's `goal` f-string, or subagents silently ignore it.

## Key Findings

### Reconciled Conflicts (canonical answers)

Research surfaced 6 explicit disagreements. Canonical resolution for each:

| # | Conflict | Canonical Answer |
|---|----------|------------------|
| **1** | LTX first/last frame capability (STACK says NO; FEATURES says YES via FLF2V; PITFALLS says TWO ORTHOGONAL capabilities) | **PITFALLS+FEATURES win.** LTX-2.3 has ICLoRA (`ltx/msr`, identity) AND FLF (`ltx/fflf` + `ltx/singularityFFLF`, first/last frame). Separate workflows, no merged turnkey option today. **STACK was wrong.** TRANSITION generation layer must evaluate FLF path per-transition, not assume LTX cannot do FLF. |
| **2** | Phase count (STACK: 4; ARCHITECTURE: 5; PITFALLS: 7 incl Phase 0 + re-audit) | **Defer to roadmapper; recommend 5-7 range.** ARCHITECTURE's 5-phase structure (FORM → DUB+IMG parallel → TRANSITION → Lineage Bump) is the minimum coherent set. PITFALLS' Phase 0 lineage impact assessment + VALIDATE re-audit are real work — either explicit phases or mandatory sub-steps of FORM/VALIDATE. **Not 4 — TRANSITION needs its own phase.** |
| **3** | CosyVoice variant (STACK: 2.0-0.5B; FEATURES: caveats that 2.0 base has limited instruct, may need CosyVoice-300M-Instruct or Fun-CosyVoice 3.0; PITFALLS: node only 7 months old, install docs missing) | **Default: CosyVoice 2.0-0.5B via `filliptm/ComfyUI_FL-CosyVoice3` (supports v2+v3 same node path).** Flag as open question: A/B test 2.0 vs 3.0 in actual pipeline during DUB phase. If 2.0 SS < IndexTTS2 baseline, switch checkpoint to 3.0 (zero code change). Operator decision recorded in `VERSION.json`. |
| **4** | Cinematographer vs Editor ownership conflict (FOUND-08 risk) — PITFALLS flags as BLOCKER T-2 | **Field-level ownership split, NOT new expert.** Creative intent fields (`transition_method`, `visual_hook`, `camera_continuity`) → cinematographer (Step 9). Post-production execution fields (`cut_duration_frames`, `dissolve_curve`, `match_cut_alignment_point`) → editor (Step 13). `transition_design.json` is emitted by cinematographer, consumed (additively annotated) by editor. **NO new `transition_designer` expert_id (FOUND-08 preservation).** |
| **5** | MSR_FC value (SKILL.md line 446: 17; PROJECT.md: 41; spec: 41) | **Canonical = 41.** SKILL.md line 446 is STALE (pre-2026-07-01 A/B test). Flag as existing tech debt to fix incidentally during FORM or TRANSITION phase. Do not treat as a v14.0 feature — it's a stale-default correction. |
| **6** | Lineage bump scope (ARCHITECTURE: 6 agents; PITFALLS: 15 cascades) | **Use 6.** Only SKILL.md that actually change get bumped: cinematographer, editor, audio_pipeline, drawer, kais-movie-pipeline, kais-jimeng-cli. PITFALLS' "15" is worst-case (every expert touched); ARCHITECTURE narrowed correctly. The 9 untouched experts (screenplay, scene_builder, performer, continuity, colorist, composer, foley, spatial_audio, mixer, style_genome) get no bump. |

### Recommended Stack

**Zero new Python packages.** All needed libraries are already pinned in `hermes-agent/pyproject.toml`. The milestone is pure skill content (markdown refs + SKILL.md patches + 1 new Python orchestrator + 2 new REST clients).

**Core technologies:**
- **CosyVoice 2.0-0.5B** via ComfyUI `filliptm/ComfyUI_FL-CosyVoice3` node — TTS default replacing IndexTTS2; same node path supports v3 fallback if v2 SS underperforms
- **`tenacity==9.1.4`** (already pinned) — dreamina retry/backoff via `AsyncRetrying` + `retry_if_result`
- **`asyncio.Semaphore`** (stdlib) — dreamina concurrency cap at validated 10-parallel sweet spot
- **GLM-4.6V** (zai provider already wired) — vision-verify gate (NOT a model switch; it's a vision tool call, allowed under MEMORY.md glm-5.2-only constraint)
- **Wan2.2 14B FLF2V** (local ComfyUI native node `WanFirstLastFrameToVideo`) — primary transition engine for match-cut via shared object; ~21GB VRAM
- **Hailuo 02 i2v Pro + Vidu keyframe-to-video** (REST APIs, `httpx==0.28.1` already pinned) — cloud backup transition engines for Chinese content; opt-in via operator API key
- **ffmpeg** (already in stack) — post-production dissolve/wipe/fade/J-cut/L-cut fallback for non-generation transitions
- **`pydantic==2.13.4`** (already pinned) — schema migration for `PipelineState.form_factor`, `transition_design.json`, E-Konte Layer 5 extension

**Critical version requirements:** None new. Existing pins are compatible. The only install work is one Docker exec to clone `ComfyUI_FL-CosyVoice3` + download CosyVoice 2 checkpoint (mirrors the existing `comfyui-indextts2-setup.md` 9-step pattern).

**Stack additions per track:**
- **FORM:** Zero new stack. Pure dataclass field + schema migration + SKILL.md conditional branches.
- **DUB:** 1 new ComfyUI custom node (`filliptm/ComfyUI_FL-CosyVoice3`) + CosyVoice 2 model checkpoint. No new Python lib.
- **IMG:** 1 new Python file (`plugins/kais_aigc/dreamina_orchestrator.py` or `skills/kais-jimeng-cli/scripts/dreamina_manager.py`) using existing `tenacity` + `asyncio.Semaphore` + `httpx` + `Pillow`. GLM-4.6V via existing zai provider.
- **TRANSITION:** 1 new local engine integration (`templates/wan_flf2v_batch_render.py` mirroring `ltx_msr_batch_render.py`) + 2 new REST clients (`templates/hailuo_flf_client.py`, `templates/vidu_flf_client.py`) using existing `httpx`. No new lib.

### Expected Features

**Table stakes (P1 — must ship in v14.0):**
- **FORM:** Pipeline-level `form_factor` parameter; per-expert form_factor awareness (15 SKILL.md `## Form Factor Adaptation` sections); render param aspect-ratio selection; Step 14 platform-variant aspect-ratio awareness preserved
- **DUB:** CosyVoice 2 TTS default; voice preset library per-character (`voice_clone_reference_wav`); CosyVoice ↔ LTX 2.3 native audio division rule; IndexTTS2 fallback path (DEPRECATED, not removed)
- **IMG:** Production-grade batch queue manager (retry + failure isolation + concurrency); vision-verify mandatory gate (pre-ComfyUI upload); image2image workflow standardization; RHD/LHD systematic mitigation (prompt + verify-retry + image2image fallback); dreamina task metadata backfill into pipeline_state
- **TRANSITION:** E-Konte Layer 5 schema extension (12-value enum + structured `next_shot_link`); `transition_design.json` first-class asset (asset-bus slot Phase 36); `references/transition-design.md` new ref; ffmpeg post-production path formalization as Step D fallback

**Differentiators (P2 — add after core validation):**
- LTX-2.3 FLF2V + ICLoRA combined workflow for true generation-time match cuts (industry-novel, no turnkey workflow exists; validate on 1-2 shots first)
- Per-transition engine routing (LTX-FLF2V for match-cut / Kling for complex motion / ffmpeg for dissolve)
- Per-line TTS engine routing (LTX native for lip-sync, CosyVoice for voiceover)
- Cross-shot transition chain validation in continuity_auditor (new 5th dimension: voice_identity)
- CosyVoice 2 instruct2 fine-grained control (emotion + speed + volume per line)
- IMG SLA tracking dashboard (`hermes dreamina stats` CLI)

**Defer (v15+):**
- IMG auto-scaling concurrency (current 10-parallel is validated and stable)
- IMG multi-model routing (dreamina 5.0 vs Seedance 2.0)
- TRANSITION AI-generated whip pan transitions (current engines unreliable)
- DUB real-time TTS streaming (race-condition architecture needed)
- FORM per-shot form_factor override (anti-pattern — project-level lock only)

**Anti-features (explicitly do NOT build):**
- FORM: per-shot form_factor mixing (cross-shot consistency collapse); auto-form-factor inference from screenplay (unreliable ~40% wrong)
- DUB: IndexTTS2 full retirement (loses fallback path); real-time TTS streaming during video gen (race conditions); voice cloning from unauthorized samples (legal/ethical)
- IMG: fully autonomous image gen with no operator review (wrong content ~5-10%); parallel concurrency > 12 (20-parallel = 95% success); FLUX local fallback (Kai-forbidden)
- TRANSITION: AI whip pan transitions; generation-time for ALL transition types (ffmpeg handles dissolve/wipe/fade trivially); custom types beyond 12-value taxonomy; over-engineered 50+ field schema (most transitions are hard_cut)

### Architecture Approach

Cross-repo topology is non-negotiable: code + refs + Python plugins in `kais-hermes-skills`; GSD planning + agent YAMLs in `hermes-agent`. The only hermes-agent-side change is the final lineage bump. Each track integrates at well-defined touchpoints — FORM adds a `PipelineState.form_factor` field that propagates to all expert invocation contexts; DUB adds a ComfyUI CosyVoice node parallel to existing IndexTTS2; IMG adds a Python orchestrator co-located with the kais-jimeng-cli skill; TRANSITION adds a new `transition_design` asset-bus slot flowing from cinematographer (p09) → editor (p10) → animator (p11).

**Major components:**
1. **PipelineState dataclass** (`plugins/pipeline_state/store.py`) — add `form_factor: str = "portrait"` field; auto-derived `_STATE_FIELDS` makes this safe
2. **E-Konte Layer 5 schema** (`cinematographer/references/e-konte-format.md`) — extend `cut_transition_type` from 4 → 12 values; refactor `next_shot_link` from string → structured object; backward-compat reader for old projects
3. **Asset-bus slot** (`kais-movie-pipeline/references/asset-bus-schema.md`) — add `transition_design` slot in Phase 36 category; register in 3 systems (asset bus + canvas sync `_PHASE_OUTPUT_MAP` + zod enum if new node type)
4. **dreamina_orchestrator.py** — new Python module; `asyncio.Semaphore(10)` + `tenacity` retry + sync queue model (block on poll-all-before-deadline); writes to pipeline_state only AFTER all retries resolve
5. **CosyVoice ComfyUI workflow JSON** — new artifact in `audio_pipeline/references/workflows/cosyvoice-comfyui.json`; uses `FLCosyVoice3Instruct2` node; shares `comfyui-primary` Docker container with LTX-MSR (GPU contention risk — P10/P11 must not run concurrently)
6. **transition_design.json** — new first-class asset; `schema_version: "1.0"`; per-shot transition + cross-shot chain; provenance field records which engine generated each transition
7. **Agent YAML lineages** (`~/.hermes/agents/*.agent.yaml`) — re-run v13.0 P62 transform flow on 6 affected agents; advisory drift acceptable mid-milestone (per v10.0 design)

**Patterns to follow:**
- Schema migration with defaults (FORM `form_factor` defaults to `"portrait"`, preserving current behavior)
- Asset-bus slot addition with 3-system registration (asset bus + canvas sync + zod enum)
- Reference doc mirror (SKILL.md body change → corresponding `references/*.md` updated in parallel)
- Plugin extension via co-location (`dreamina_manager.py` lives in kais-jimeng-cli skill, not standalone plugin)
- Lineage bump as reconciliation mechanism (v10.0 L1-L6 invariant escape hatch, NOT a violation)

### Critical Pitfalls

Top 5 BLOCKER pitfalls from combined research:

1. **PITFALL X-1: Lineage invalidation cascade (BLOCKER, L1-L6 violation risk)** — every SKILL.md touched by v14.0 (15 for FORM alone, + audio_pipeline + cinematographer + editor + drawer + kais-movie-pipeline + kais-jimeng-cli) must regenerate `source_sha` + update `transform_rule_id` + `transform_timestamp` + propagate to `~/.hermes/agents/*.agent.yaml` by re-running v13.0 P62 transform. **Mitigation:** Phase 0 lineage impact assessment + CI assertion `agent.yaml.source_sha == sha256(SKILL.md)` + lineage-coverage row in milestone audit.

2. **PITFALL X-2: "文档有规则,代码没执行" META-RULE regression (BLOCKER, most-recurring bug pattern)** — every MUST/MUST NOT added to SKILL.md must ALSO be encoded as a `_INSTRUCTION` constant injected into the phase module's `goal` f-string with a test asserting the keyword appears in `captured["goal"]`. Subagents never read SKILL.md at runtime. **Mitigation:** Extract `_INSTRUCTION` constant per MUST; inject via GoalBuilder `[CONSTRAINTS]` segment (MUST-prefixed for `count_constraints()`); CI gate `grep MUST SKILL.md | wc -l == count_constraints(goal)`.

3. **PITFALL F-1: 16:9 ≠ "just resize 9:16" — creative assumptions break silently (BLOCKER)** — power points, headroom, subtitle safe area, camera move priority, shot-scale distribution, eye-trace all differ between vertical and horizontal. Cinematographer's `vertical-screen-framing.md` is explicitly vertical-only; no horizontal companion exists. **Mitigation:** Author `references/horizontal-screen-framing.md` BEFORE parameterizing form_factor; each form-aware SKILL.md gets a `## Form Factor Adaptation` dual-branch section; add landscape eval variants under `_eval/`.

4. **PITFALL D-1: CosyVoice + LTX 2.3 native audio BOTH enabled → doubled audio / phase issues / lip-sync mismatch (BLOCKER)** — LTX native handles synced dialogue + lip sync; CosyVoice handles voiceover/emotion. If both fire for the same shot: phase cancellation, "bad dub" effect, BGM mixing confusion. **Mitigation:** Schema validator rejects `tts_engine = cosyvoice` for shots with `lip_sync_required = true`; P12 composition routes per-shot based on `tts_engine`; unit test asserts no shot has both `ltx_native_dialogue AND cosyvoice_overlay`.

5. **PITFALL T-2: Cinematographer vs editor ownership conflict for transition design (BLOCKER, FOUND-08 risk)** — both currently claim transition design territory; PROJECT.md's proposed expansion worsens the overlap; creating a new `transition_designer` expert is a FOUND-08 violation. **Mitigation:** Field-level ownership split (creative intent → cinematographer Step 9; post-production execution → editor Step 13); `transition_design.json` emitted by cinematographer, additively annotated by editor (editor does NOT modify); update both SKILL.md files in the same phase.

Additional high-severity pitfalls:
- **T-3:** `next_shot_link` string → structured object migration is breaking; need backward-compat reader that coerces old string form to `{"shot_id": value, "transition_method": "hard_cut", ...}` defaults
- **T-4:** `transition_design.json` must be registered in 3 systems (asset bus + canvas sync `_PHASE_OUTPUT_MAP` + zod enum) or canvas silently fails to render
- **I-3:** Async retry vs sync queue — pipeline_state write before async retry completes → P11 video render fails on missing ref; orchestrator MUST block on poll-all-before-deadline, write state only AFTER retries resolve
- **X-5:** INFRA-04 serial constraint — transition engine routing decisions are GLM-made, so even non-GLM generation engines (Wan-FLF2V local) carry GLM overhead; keep ALL routing under existing `glm_concurrent` semaphore (`MAX_CONCURRENT_GL=1`)
- **D-2:** CosyVoice 2 voice cloning needs 3-10s reference audio per character — operator-action handoff; templates must fail-fast with explicit error if `voice_clone_reference_wav` missing
- **F-2:** Changing MASTER form_factor breaks Step 14 platform variant reframe math — must branch on `master_form_factor × target_platform_form_factor` (4 combinations)

## Implications for Roadmap

Based on combined research, suggested phase structure (5-7 phases recommended; final count deferred to roadmapper):

### Phase 0: Lineage Impact Assessment + Foundation Audit
**Rationale:** PITFALLS X-1 + X-4 require enumerating every SKILL.md to be touched BEFORE any edits land; curator `--live` must be frozen; in-flight file registry shared with curator. Without this, lineage cascade silently corrupts agent YAMLs.
**Delivers:** List of SKILL.md files to modify with current `source_sha`; v14.0 in-flight file registry; `STATE.md` cross-repo commit pin baseline; audit checklist for VALIDATE phase.
**Addresses:** Pitfalls X-1 (lineage cascade), X-4 (curator drift), X-3 (cross-repo coordination).
**Avoids:** Silent stale persona load; EVAL-06 mid-milestone regression.

### Phase 1: FORM — form_factor Parameterization
**Rationale:** Foundational — every other track consumes `form_factor`. Must land first. Low risk (additive dataclass field, default preserves current behavior).
**Delivers:** `PipelineState.form_factor` field; `references/horizontal-screen-framing.md` new ref; 15 SKILL.md `## Form Factor Adaptation` sections; LTX-MSR template resolution switch (16:9 default, 9:16 branch); Step 14 4-cell reframe matrix; incidental fix of stale `MSR_FC=17 → 41` at SKILL.md line 446.
**Addresses:** FORM table stakes (all 4).
**Avoids:** Pitfalls F-1 (creative assumptions break), F-2 (Step 14 variant breakage), F-3 (form-agnostic LLM output).
**Research flag:** Standard pattern (dataclass migration is well-documented in ARCHITECTURE.md). Landscape eval variants need light spike but no deep research.

### Phase 2: DUB — CosyVoice + LTX Native Audio Coordination (parallel with Phase 3)
**Rationale:** Independent of IMG/TRANSITION. Depends only on FORM (voice presets may vary by form factor for spatial audio placement). ComfyUI node dependency installation is the main risk.
**Delivers:** ComfyUI CosyVoice node install + healthcheck; `cosyvoice-comfyui.json` workflow; `cosyvoice-presets.md` per-character library; voicer model matrix update (CosyVoice primary, IndexTTS2 DEPRECATED fallback); CosyVoice/LTX division rule enforced via schema validator; `tts_engine` routing; `voice_clone_reference_wav` field + operator-action handoff doc.
**Addresses:** DUB table stakes (all 4).
**Avoids:** Pitfalls D-1 (doubled audio), D-2 (operator wavs), D-3 (ComfyUI dep hell), D-5 (GPU contention), D-6 (project reconstruction backward-compat).
**Research flag:** **Needs research-phase.** CosyVoice variant benchmark (2.0 vs 3.0 in actual kais-movie-pipeline dialogue scenarios) is unresolved; ComfyUI node maturity is MEDIUM confidence (only 7 months old). Run A/B test on 3-5 reference lines before locking default.

### Phase 3: IMG — dreamina Production-Grade Orchestration (parallel with Phase 2)
**Rationale:** Independent of DUB/TRANSITION. Vision-verify pattern is reusable by TRANSITION generation layer (FLF2V match-cut needs vision-verify to confirm first/last frame content).
**Delivers:** `dreamina_manager.py` orchestrator (asyncio.Semaphore + tenacity + sync queue model); vision-verify mandatory gate (GLM-4.6V, batch N images per call, confidence-gated enforcement); RHD/LHD mitigation (prompt + verify-retry + image2image fallback, 3-attempt budget); image2image template standardization; dreamina task metadata backfill; SLA tracking via local MetricsBuffer (no GLM calls per metric).
**Addresses:** IMG table stakes (all 5).
**Avoids:** Pitfalls I-1 (vision-verify bottleneck), I-2 (vision-verify false positives), I-3 (async write order), I-4 (RHD/LHD), I-5 (SLA observability overhead).
**Research flag:** **Needs research-phase.** GLM-4.6V LHD/RHD detection accuracy on dreamina-generated interior shots is unverified; dreamina N-ref tolerance for image2image is WATCH-level (no public data).

### Phase 4: TRANSITION — 3-Layer Creative + Data + Generation
**Rationale:** Depends on FORM (transitions are form-factor-sensitive). Benefits from IMG's vision-verify precedent. Most architecturally invasive (E-Konte schema change + new asset-bus slot + 3-system canvas registration + per-transition engine routing). HIGH risk.
**Delivers:** E-Konte Layer 5 schema extension (4 → 12 values, backward-compat reader for old string `next_shot_link`); `transition_design.json` first-class asset + 3-system canvas registration; `references/transition-design.md` new ref (creative taxonomy + data schema + execution paths); field-level ownership split between cinematographer (creative) and editor (execution); ffmpeg post-production path formalization as Step D fallback; LTX-2.3 FLF path evaluation per-transition (NOT assume LTX cannot do FLF); Wan2.2 14B FLF2V local engine integration; Hailuo/Vidu cloud backup clients (opt-in); per-transition declarative routing rules (no runtime LLM decisions, INFRA-04 safe).
**Addresses:** TRANSITION table stakes (all 4) + P2 differentiator (LTX-FLF2V + ICLoRA combined workflow as research-scope validation on 1-2 shots, NOT immediate pipeline integration).
**Avoids:** Pitfalls T-1 (LTX FLF assumption corrected), T-2 (cinematographer vs editor FOUND-08 conflict), T-3 (schema migration backward-compat), T-4 (3-system canvas registration), T-5 (API quota operator-action), T-6 (cross-engine routing complexity), T-7 (voice continuity across transitions), T-8 (creative exceeds engine capability).
**Research flag:** **Needs research-phase.** LTX FLF+ICLoRA combined workflow has no public turnkey option (community-verified, not officially documented); Wan2.2 FLF2V prompt-following in Chinese complex-action descriptions is unvalidated; Hailuo/Vidu pricing in production batch is single-source data ($0.056/sec list price only).

### Phase 5: Lineage Bump + VALIDATE
**Rationale:** SKILL.md changes must be finalized before regenerating agent YAMLs. VALIDATE runs the cross-cutting audits (lineage coverage, META-RULE test count, cross-repo commit pin, INFRA-04 preservation, EVAL-06 dry-run state, FOUND-08 field-ownership).
**Delivers:** Re-run v13.0 P62 transform flow on 6 affected agents (cinematographer, editor, audio_pipeline, drawer, kais-movie-pipeline, kais-jimeng-cli); milestone audit; v14.0 tag.
**Addresses:** Pitfalls X-1 (lineage cascade close-out), X-2 (META-RULE test count diff), X-3 (cross-repo commit pin assertion).
**Research flag:** Standard pattern (mechanical transform + audit, documented 5-step procedure from v10.0).

### Phase Ordering Rationale

- **FORM first:** Everything else reads `form_factor`. Hard dependency.
- **DUB + IMG parallel:** Independent of each other and of TRANSITION. Both depend only on FORM. Parallel cuts wall time.
- **TRANSITION after DUB+IMG:** Depends on FORM (composition match for form_factor) + benefits from IMG's vision-verify precedent (FLF2V match-cut needs vision-verify). Most invasive, lands last to avoid cascading schema changes mid-milestone.
- **Lineage Bump + VALIDATE at the end:** Bumping mid-track would create stale lineages. VALIDATE must run after all SKILL.md edits are final.
- **PITFALLS' Phase 0 + re-audit:** Phase 0 is folded into Phase 0 (explicit) above; re-audit is folded into Phase 5 VALIDATE. If roadmapper wants explicit, split into 7 phases; if compressed, 5 phases with Phase 0 sub-steps in Phase 1.

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase 2 (DUB):** CosyVoice 2 vs 3.0 A/B benchmark in actual pipeline; ComfyUI node maturity (MEDIUM confidence, 7 months old); emotion mapping fidelity (melancholic composite is lossy)
- **Phase 3 (IMG):** GLM-4.6V LHD/RHD accuracy on dreamina interiors; dreamina N-ref tolerance for image2image; vision-verify false-positive rate threshold calibration
- **Phase 4 (TRANSITION):** LTX FLF+ICLoRA combined workflow (no public turnkey); Wan2.2 FLF2V Chinese prompt-following; Hailuo/Vidu production batch cost; cross-engine voice continuity (T-7)

**Phases with standard patterns (skip research-phase):**
- **Phase 0 (Lineage Impact Assessment):** Well-documented v13.0 P62 procedure; mechanical enumeration
- **Phase 1 (FORM):** Dataclass migration is standard Python; SKILL.md conditional branches are pure text
- **Phase 5 (Lineage Bump + VALIDATE):** Mechanical transform + audit; documented 5-step procedure

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Zero new dependencies; all libs already pinned in pyproject.toml. CosyVoice variant (2.0 vs 3.0) is MEDIUM but same node path enables zero-code switch. |
| Features | HIGH | Cross-verified against Runway/Kling/Sora/LTX official docs + internal pipeline state + 12-type taxonomy from StudioBinder/Adobe. |
| Architecture | HIGH | All claims verified against live repo code (PipelineState dataclass, E-Konte schema, asset-bus slots, agent YAML lineage fields). |
| Pitfalls | HIGH | Cross-verified against kais-movie-pipeline SKILL.md (30+ existing pitfalls), MILESTONES.md v1-v13 history, sibling research docs. |

**Overall confidence:** HIGH

### Gaps to Address

- **CosyVoice variant benchmark:** 2.0-0.5B vs Fun-CosyVoice 3.0 in actual kais-movie-pipeline Chinese dialogue scenarios. Currently only GitHub README SS numbers (75.7% vs 78.0%). Resolve during Phase 2 with 3-5 reference line A/B test before locking default.
- **LTX FLF+ICLoRA combined workflow:** No public turnkey option. Community reports custom node graph is needed (LiconMSR + LTXVConditioning + SamplerCustomAdvanced). Validate on 1-2 shots in Phase 4 before pipeline integration.
- **GLM-4.6V LHD/RHD accuracy on dreamina interiors:** docs.z.ai claims SoTA on richly formatted pages, but dreamina-generated partial-RHD partial-mirrored car interiors are a domain-specific edge case. Validate empirically in Phase 3.
- **dreamina N-ref tolerance for image2image:** No public data on how dreamina's tolerance degrades around 4-5 references. Phase 3 should stratify retry budget by ref count.
- **Wan2.2 FLF2V Chinese prompt-following:** `video-engine-comparison.md` rates Wan2.1/2.2 prompt-following as "Moderate"; FLF2V mode in Chinese complex-action descriptions is unvalidated. Phase 4 spike.
- **Hailuo/Vidu production batch cost:** Only $0.056/sec list price; no 30-shot batch monthly cost data. Phase 4 operator-action-handoff includes budget estimate.
- **Vision-verify false-positive threshold:** 20% wrong becomes 20% friction. Specific threshold for auto-reject vs operator-review needs Phase 3 calibration.
- **Async write order in dreamina orchestrator:** Pattern is clear (block on poll-all-before-deadline, write state only after retries), but failure-injection integration test in Phase 3 must validate.

## Sources

### Primary (HIGH confidence)
- **Official docs:**
  - [FunAudioLLM/CosyVoice GitHub](https://github.com/FunAudioLLM/CosyVoice) + [CosyVoice2-0.5B HuggingFace](https://huggingface.co/FunAudioLLM/CosyVoice2-0.5B) — version comparison, vLLM/TensorRT-LLM deployment
  - [filliptm/ComfyUI_FL-CosyVoice3](https://github.com/filliptm/ComfyUI_FL-CosyVoice3) — ComfyUI node supporting v2+v3 same path
  - [LTX-2.3 FLF2V ComfyUI Workflow](https://comfy.org/workflows/video_ltx2_3_flf2v-bb33cc433026/) + [LTX IC-LoRA docs](https://docs.ltx.video/open-source-model/usage-guides/ic-lo-ra) — FLF vs ICLoRA orthogonality
  - [comfy.org Wan2.2 14B FLF2V workflow](https://comfy.org/workflows/video_wan2_2_14B_flf2v-7016f027bcf1/) + [GegenDenTag HuggingFace workflow JSON](https://huggingface.co/GegenDenTag/comfyui-wan-video-2.2-t2v-first-last-frame-workflow)
  - [MiniMax Hailuo 02 platform docs](https://platform.minimax.io/docs/guides/video-generation) + [Aliyun Vidu keyframe-to-video](https://help.aliyun.com/en/model-studio/vidu-keyframe-to-video-api-reference)
  - [Runway Keyframes on Gen-3](https://help.runwayml.com/hc/en-us/articles/34170748696595-Creating-with-Keyframes-on-Gen-3) + [Kling Start/End Frames](https://kling.ai/quickstart/ai-video-start-end-frames)
  - [GLM-4.6V docs.z.ai](https://docs.z.ai/guides/vlm/glm-4.6v) — 128K vision SoTA
  - [FFmpeg Xfade wiki](https://trac.ffmpeg.org/wiki/Xfade) — dissolve/wipe/fade transitions
- **Internal repo (HIGH confidence, live code):**
  - `kais-hermes-skills/skills/kais-movie-pipeline/SKILL.md` — 30+ existing pitfalls, form_factor hardcoded refs (line 40, 268, 294, 446), LTX params, dreamina 10-parallel validation (line 621-622)
  - `kais-hermes-skills/plugins/pipeline_state/store.py` — PipelineState dataclass, `_STATE_FIELDS` derivation
  - `kais-hermes-skills/skills/movie-experts/cinematographer/references/e-konte-format.md` — Layer 5 schema (thin), `next_shot_link` string form
  - `kais-hermes-skills/skills/movie-experts/cinematographer/references/vertical-screen-framing.md` — vertical-only framing (load-bearing for FORM)
  - `kais-hermes-skills/skills/movie-experts/editor/SKILL.md` — FxRxT matrix, transition design step 7
  - `kais-hermes-skills/skills/movie-experts/audio_pipeline/SKILL.md` — voicer sub-step, multi-provider TTS, LTX native audio formats A/B
  - `kais-hermes-skills/skills/kais-movie-pipeline/references/ltx-msr-workflow-spec.md` — LTX native audio rules, MSR_FC=41 canonical
  - `kais-hermes-skills/skills/kais-movie-pipeline/references/video-engine-comparison.md` — existing selection rules pattern
  - `hermes-agent/.planning/research/v10-orchestrator-design/04-MIGRATION-PATH.md` — lineage transform 5-step procedure
  - `hermes-agent/.planning/MILESTONES.md` — FOUND-08 / INFRA-04 / EVAL-06 history across v1-v13

### Secondary (MEDIUM confidence)
- [LTX 2.3 First and Last Frame ComfyUI Guide (ltx23.org)](https://ltx23.org/blog/ltx-23-first-last-frame-comfyui) — FLF2V implementation details
- [LTX-2.3 ID-LoRA with FLF Reddit](https://www.reddit.com/r/StableDiffusion/comments/1t71x0r/ltx_23_idlora_with_firstlast_frame/) — custom workflow needed for ICLoRA + FLF2V combination
- [StudioBinder: Types of Editing Transitions](https://www.studiobinder.com/blog/types-of-editing-transitions-in-film/) + [Adobe: Cuts in Film](https://www.adobe.com/creativecloud/video/post-production/cuts-in-film.html) — 12-type taxonomy, J/L-cut conventions
- [CosyVoice 2025 Complete Guide (dev.to)](https://dev.to/czmilo/cosyvoice-2025-complete-guide-the-ultimate-multi-lingual-text-to-speech-solution-4l39) — `inference_instruct` API usage
- [WaveSpeed Batch Generation Guide](https://wavespeed.ai/blog/posts/wavespeed-batch-generation/) + [Leonardo.Ai Concurrency docs](https://docs.leonardo.ai/docs/guide-to-concurrency-queue-and-rate-limit) + [OneUptime Retry Strategies](https://oneuptime.com/blog/post/2026-01-30-batch-processing-retry-strategies/view) — production batch orchestration patterns
- [Aliyun CosyVoice API docs](https://help.aliyun.com/zh/model-studio/cosyvoice-large-model-for-speech-synthesis/) — NO-GO rationale (no voice clone)
- [ImagineArt Kling 2.5 Turbo Pro](https://www.imagine.art/features/kling-2-5-turbo-pro-first-and-last-frame) — Kling FLF feature confirmation (MEDIUM, vendor page)

### Tertiary (LOW confidence — needs validation)
- [轻雀 Kling docs](https://docs.qingque.cn/d/home/eZQCQxBrX8eeImjK6Ddz5iOi5) — CN-region-only access, NO-GO for non-CN
- [Pika 2.2 Pikaframes fal.ai](https://fal.ai/models/fal-ai/pika/v2.2/pikaframes/api) — relay adds hop, weak for Chinese content
- [tenacity async support docs](https://tessl.io/registry/tessl/pypi-tenacity/9.1.0/files/docs/async-support.md) — AsyncRetrying pattern (HIGH for tenacity itself; MEDIUM for specific API surface)

---
*Research completed: 2026-07-09*
*Cross-repo: hermes-agent/.planning/ (this file) + kais-hermes-skills/ (code)*
*Ready for roadmap: yes*
