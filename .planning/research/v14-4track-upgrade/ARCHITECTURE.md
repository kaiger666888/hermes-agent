# Architecture Patterns

**Domain:** v14.0 kais-movie-pipeline 4-track upgrade (FORM + DUB + IMG + TRANSITION)
**Researched:** 2026-07-09
**Confidence:** HIGH (all claims verified against live repo code: PipelineState dataclass, E-Konte schema, asset-bus slots, agent YAML lineage fields, SKILL.md bodies)

## Cross-Repo Topology (non-negotiable context)

v14.0 touches TWO repos with a strict responsibility split. Every integration point must declare which repo owns it.

| Repo | Path | Owns | v14.0 Role |
|------|------|------|------------|
| **hermes-agent** | `/data/workspace/hermes-agent` | GSD planning (`.planning/`), `~/.hermes/agents/*.agent.yaml` runtime | Orchestrator impact: lineage bump workflow, schema version bump coordination |
| **kais-hermes-skills** | `/data/workspace/kais-hermes-skills` | All SKILL.md + references + Python plugins | All 4 tracks' code/schema/content lives here |

**Rule:** hermes-agent holds no movie-pipeline business logic. kais-hermes-skills holds no GSD planning artifacts. The only hermes-agent-side change in v14.0 is regenerating agent YAML lineages (because the underlying SKILL.md content changed).

---

## Recommended Architecture: 4-Track Integration

```text
                    ┌─────────────────────────────────────────────┐
                    │   kais-movie-pipeline/SKILL.md (orchestrator) │
                    │   V8.6 13-step pipeline, owns PipelineState    │
                    └──────────────────┬──────────────────────────┘
                                       │
        ┌──────────────────┬───────────┼───────────┬──────────────────┐
        │ FORM             │ DUB       │ IMG       │ TRANSITION       │
        │ form_factor      │ CosyVoice │ dreamina  │ transition_      │
        │ propagates       │ TTS +     │ 10-par +  │ design.json +    │
        │ downstream       │ LTX audio │ verify    │ E-Konte L5 ext   │
        └──────────────────┴───────────┴───────────┴──────────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                │              15 movie-experts                  │
                │  Each consumes form_factor + transition data   │
                │  via refs/* + asset-bus slots                  │
                └───────────────────────────────────────────────┘
```

### Component Boundaries

| Component | Repo | File/Dir | Responsibility | v14.0 Change |
|-----------|------|----------|----------------|--------------|
| Pipeline orchestrator | kais-hermes-skills | `skills/kais-movie-pipeline/SKILL.md` | 13-step V8.6 flow, form_factor dispatch | MODIFY (FORM + DUB + IMG + TRANSITION sections) |
| Pipeline state | kais-hermes-skills | `plugins/pipeline_state/store.py` | `PipelineState` dataclass, episode-level state | MODIFY (add `form_factor` field) |
| Asset bus schema | kais-hermes-skills | `skills/kais-movie-pipeline/references/asset-bus-schema.md` | 31 slot definitions, envelope V3 | MODIFY (add transition_design slot, document form_factor invariants) |
| Pipeline DAG | kais-hermes-skills | `skills/kais-movie-pipeline/references/pipeline-dag.md` | 13-step graph + slot flow per edge | MODIFY (p09→p10 transition_design flow, TRANSITION generation routing) |
| E-Konte format | kais-hermes-skills | `skills/movie-experts/cinematographer/references/e-konte-format.md` | 5-layer shot sheet schema | MODIFY (extend Layer 5, refactor next_shot_link) |
| Cinematographer | kais-hermes-skills | `skills/movie-experts/cinematographer/SKILL.md` | Shot intent, E-Konte authoring | MODIFY (TRANSITION creative layer, form_factor propagation) |
| Editor | kais-hermes-skills | `skills/movie-experts/editor/SKILL.md` | Cut decisions, FxRxT matrix | MODIFY (TRANSITION data layer input, form_factor-aware transitions) |
| Audio pipeline | kais-hermes-skills | `skills/movie-experts/audio_pipeline/SKILL.md` | 6 sub-steps incl. voicer (TTS) | MODIFY (CosyVoice re-add to voicer, LTX native audio coordination) |
| Voicer model matrix | kais-hermes-skills | `skills/movie-experts/audio_pipeline/references/voicer/cn-tts-model-matrix.md` | TTS provider capability table | MODIFY (add CosyVoice row, mark IndexTTS2 deprecated) |
| Drawer (image gen) | kais-hermes-skills | `skills/movie-experts/drawer/SKILL.md` | Image generation dispatch | MODIFY (dreamina production-grade path) |
| kais-jimeng-cli (dreamina) | kais-hermes-skills | `skills/kais-jimeng-cli/` | dreamina CLI wrapper skill | MODIFY (vision-verify gate, SLA tracker, reference backfill) |
| Agent YAML lineages | hermes-agent → `~/.hermes/agents/` | `*.agent.yaml` (15 active) | v10.0 transformed agent personas | REGENERATE (lineage bump for modified SKILL.md) |

---

## Data Flow: form_factor Propagation (FORM track)

**Source of truth:** `PipelineState.form_factor` (new field on the episode-level dataclass).

```text
PipelineState.form_factor (enum: "landscape" | "portrait")
    │
    ├─→ kais-movie-pipeline/SKILL.md reads state at pipeline boot
    │     └─→ passes form_factor into each expert invocation context
    │
    ├─→ cinematographer (shot_intent.json, e_konte.json)
    │     └─→ selects 9:16 power-points vs 16:9 rule-of-thirds grid
    │
    ├─→ drawer (character-assets, scene-images)
    │     └─→ dreamina CLI image dims: 1080×1920 vs 1920×1080
    │
    ├─→ animator / LTX-MSR render (video gen)
    │     └─→ width/height params: 720×1280 (portrait) vs 1280×704 (landscape)
    │
    ├─→ editor (edit_decision_list.json)
    │     └─→ cut rhythm baselines differ by form factor
    │
    └─→ composer, colorist, mixer, spatial_audio
          └─→ mostly form_factor-agnostic but receive context
```

**Backwards compatibility:** `form_factor` defaults to `"portrait"` (current behavior — all existing 短剧 are 9:16). Old `PipelineState` JSON without the field loads cleanly because `store.py`'s `_STATE_FIELDS = frozenset(PipelineState.__dataclass_fields__.keys())` is dataclass-derived; adding the field auto-extends the whitelist. Episodes started before v14.0 implicitly get portrait.

**Anti-pattern:** Do NOT make `form_factor` per-shot. It is an EPISODE-LEVEL invariant. A landscape episode cannot contain portrait shots. Mixing breaks LTX-MSR ICLoRA reference conditioning.

---

## Data Flow: transition_design.json (TRANSITION track, creative layer)

```text
Cinematographer (E-Konte authoring, p09)
    │  extends Layer 5 with transition intent
    │
    ├─→ transition_design.json (NEW asset-bus slot, Phase 36 category)
    │     schema: {
    │       transitions: [{
    │         from_shot, to_shot,
    │         transition_type,        # extended enum (12 types)
    │         intent,                 # creative rationale
    │         duration_frames,
    │         match_anchor            # optional: match-cut anchor ref
    │       }],
    │       form_factor,              # episode-level, inherited
    │       schema_version: "1.0"
    │     }
    │
    ├─→ Editor (p10, cut decisions)
    │     reads transition_design.json
    │     validates against FxRxT matrix
    │     refines: data_layer
    │
    └─→ Animator / LTX-MSR / Wan2.2-FLF2V (p11, generation)
          reads refined transition_data
          routes by transition_type:
            ├── hard_cut      → no generation (straight cut in editor)
            ├── dissolve/wipe/fade → LTX native time-based (no new gen)
            ├── match_cut     → LTX-MSR with reference frames
            └── complex_transition → Wan2.2 14B FLF2V (first/last frame gen)
```

**E-Konte Layer 5 schema migration:**
- Current `cut_transition_type: "hard_cut" | "dissolve" | "wipe" | "fade"` (4 values, thin)
- Current `next_shot_link: "shot_02"` (string id, no metadata)
- **v14.0 extends** `cut_transition_type` to 12-value enum (see FEATURES.md §TRANSITION taxonomy)
- **v14.0 refactors** `next_shot_link` from string → structured object `{shot_id, transition_intent, duration_frames}`

**Schema versioning:** `schema_version: "1.0"` on transition_design.json. E-Konte format ref bumps `references/e-konte-format.md` version tag. Old E-Konte files (pre-v14.0) parse via fallback: missing `transition_intent` field defaults to `"hard_cut"`.

---

## Data Flow: CosyVoice + LTX Native Audio (DUB track)

```text
audio_pipeline/SKILL.md → voicer sub-step (Step 7B.i)
    │
    ├─→ Reads line-level voice preset from character-bible
    │     (character_bible.json → voice_profile per character)
    │
    ├─→ Voice preset library (NEW ref, audio_pipeline/references/voicer/)
    │     cosyvoice-presets.md
    │       - per-character prompt template (age, timbre, emotion baseline)
    │       - cross-lingual mode (CN ↔ EN) parameters
    │       - emotion control tags (sad, neutral, excited, whisper)
    │
    ├─→ ComfyUI workflow: ComfyUI_FL-CosyVoice3 node
    │     NOT a CLI call. Workflow JSON in audio_pipeline/references/workflows/
    │     Inputs: text, voice_prompt, emotion, reference_audio (optional)
    │     Output: WAV clip per line
    │
    └─→ LTX 2.3 native audio coordination
          LTX-MSR can generate video WITH audio (native).
          Two paths per shot:
            Path A (lip_sync heavy): CosyVoice → lip_sync sub-step → LTX video-only
            Path B (ambient/BGM): LTX native audio → mixer sub-step blends
          audio_pipeline/SKILL.md documents routing rules.
```

**IndexTTS2 disposition:** Marked DEPRECATED in voicer model matrix. Not removed (existing episodes may reference it). New episodes default to CosyVoice. Voicer sub-step provider selection gains CosyVoice as first-choice; IndexTTS2 remains as fallback for backward compatibility.

**Phantom strip context:** v13.0 Phase 5 stripped a "CosyVoice phantom" (referenced but not implemented). v14.0 CosyVoice is a RE-ADD with full implementation path (ComfyUI node + presets + workflow), not a revival of the phantom.

---

## Data Flow: dreamina Production-Grade Orchestration (IMG track)

```text
drawer/SKILL.md → image generation dispatch
    │
    ├─→ dreamina_manager.py (NEW Python module)
    │     Location: kais-hermes-skills/plugins/ OR skills/kais-jimeng-cli/scripts/
    │     (RECOMMENDED: skills/kais-jimeng-cli/scripts/dreamina_manager.py — co-located with CLI skill)
    │     Responsibilities:
    │       - asyncio.Semaphore(MAX_CONCURRENT_GL=3) — GLM rate limit protection
    │       - tenacity retry_on_429 with jittered backoff
    │       - 10-parallel batch submission (validated: 100% success rate)
    │       - per-image SLA tracking (start_ts, complete_ts, retry_count)
    │       - reference image backfill queue (see below)
    │
    ├─→ Vision-verify gate (GLM-4.6V)
    │     Placement: BEFORE ComfyUI upload (post-dreamina, pre-asset-bus)
    │     For each generated image:
    │       1. GLM-4.6V analyzes: "Does this match the prompt intent?"
    │       2. FAIL → retry with tightened prompt (max 3 retries)
    │       3. PASS → emit to asset-bus
    │
    └─→ Reference image backfill
          When dreamina produces a character/scene image that becomes canonical,
          backfill it as a reference for LTX-MSR ICLoRA conditioning.
          Backfill queue: list of (image_path, character_id, scene_id, form_factor)
          Drained at p11 pre-render.
```

**Why dreamina manager lives in kais-jimeng-cli skill (not a new plugin):** The skill already wraps the dreamina CLI. The manager is a Python helper invoked from the skill's prompt instructions. Creating a new plugin would fragment ownership. The skill is the natural integration surface — `SKILL.md` instructs the agent to call `python scripts/dreamina_manager.py`.

---

## Patterns to Follow

### Pattern 1: Schema Migration with Defaults (FORM track)

**What:** Add `form_factor` to `PipelineState` dataclass with a default value.
**When:** Any episode-level field addition.
**Example:**
```python
# plugins/pipeline_state/store.py — BEFORE
@dataclass
class PipelineState:
    episode: str
    phases: dict[str, dict] = field(default_factory=dict)
    # ... existing fields ...
    trace_id: str | None = None

# AFTER
@dataclass
class PipelineState:
    episode: str
    phases: dict[str, dict] = field(default_factory=dict)
    # ... existing fields ...
    trace_id: str | None = None
    form_factor: str = "portrait"   # NEW: "landscape" | "portrait"
```
**Why safe:** `_STATE_FIELDS` is derived from `__dataclass_fields__`, so it auto-includes the new field. Old JSON missing the field loads with the default. No migration script needed.

### Pattern 2: Asset-Bus Slot Addition (TRANSITION track)

**What:** Add `transition_design` slot to asset-bus schema doc.
**When:** Any new artifact type needs pipeline-wide visibility.
**Convention:** Document in `references/asset-bus-schema.md` under the appropriate Phase category (Phase 36 — generation inputs). Slot name matches the JSON filename root: `transition_design.json`.

### Pattern 3: Reference Doc Mirror (all tracks)

**What:** When a SKILL.md body change references new schema/format, update the corresponding `references/*.md` doc in parallel.
**Why:** SKILL.md is the prompt; references are the knowledge base. Drift between them produces hallucinated outputs. The SKILL.md → references relationship is 1:many and must stay synchronized.

### Pattern 4: Agent YAML Lineage Bump (orchestrator impact)

**What:** After SKILL.md content changes, regenerate the corresponding `~/.hermes/agents/*.agent.yaml` lineage fields.
**Procedure (from v10.0 04-MIGRATION-PATH.md):**
1. Read modified `SKILL.md`
2. Compute `skill_sha256` (sha256 of full file content)
3. If sha256 matches existing lineage → no bump needed
4. If different → regenerate persona body, update `lineage.transform_date`, `lineage.skill_sha256`, append `transform_notes` entry
5. Write updated `*.agent.yaml`

**v14.0 scope:** Only experts whose SKILL.md actually changes get lineage bumps. Expected: cinematographer, editor, audio_pipeline, drawer, kais-movie-pipeline (orchestrator is also an agent). Other 10 experts: no change, no bump.

### Pattern 5: Plugin Extension via Co-location (IMG track)

**What:** New Python helper modules live alongside the skill that invokes them, not as standalone plugins.
**When:** A skill needs procedural logic that doesn't fit in markdown (batch orchestration, retry loops, SLA tracking).
**Example:** `skills/kais-jimeng-cli/scripts/dreamina_manager.py` is invoked by the kais-jimeng-cli SKILL.md prompt instructions.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Per-Shot form_factor

**What:** Letting each shot declare its own form_factor.
**Why bad:** LTX-MSR ICLoRA requires consistent aspect ratio across reference frames. Mixed-form episodes break conditioning. Editor's cut rhythm matrix assumes one form factor.
**Instead:** `form_factor` is episode-level. Pipeline boot validates the invariant. Drawer/animator reject per-shot overrides.

### Anti-Pattern 2: CosyVoice as CLI subprocess

**What:** Shelling out to `cosyvoice-cli` or similar.
**Why bad:** CosyVoice 2.0-0.5B is deployed via ComfyUI custom node (`ComfyUI_FL-CosyVoice3`). CLI invocation would bypass the ComfyUI workflow, lose GPU sharing, and duplicate model loading.
**Instead:** ComfyUI workflow JSON with the CosyVoice3 node. audio_pipeline SKILL.md documents the workflow file path and input schema.

### Anti-Pattern 3: Wholesale IndexTTS2 Removal

**What:** Deleting all IndexTTS2 references from audio_pipeline.
**Why bad:** Existing episodes may have IndexTTS2-generated clips in their asset-bus. Removal breaks replay/debugging of old episodes.
**Instead:** Mark IndexTTS2 as DEPRECATED in the voicer model matrix. New episodes default to CosyVoice. IndexTTS2 remains as an explicit fallback provider. Document deprecation date and removal target (v15.0+).

### Anti-Pattern 4: Unbounded dreamina Concurrency

**What:** Submitting all image gen requests simultaneously.
**Why bad:** GLM rate limits (MAX_CONCURRENT_GL=3 enforced globally). Blind parallelism → 429 storm → wasted retries.
**Instead:** `dreamina_manager.py` uses `asyncio.Semaphore(3)` + `tenacity.retry_on_429`. Validated 10-parallel batch = 100% success (the 10 is total batch size, not concurrency).

### Anti-Pattern 5: transition_design.json as Editor-Only Artifact

**What:** Treating transition design as a purely editorial concern, authored and consumed only by the editor.
**Why bad:** Transitions have a GENERATION component (Wan2.2 FLF2V for complex types). The creative layer (cinematographer) and data layer (editor) must be separate from the generation layer (animator/LTX/Wan2.2). Collapsing them loses the generation routing signal.
**Instead:** 3-layer collaboration: creative (cinematographer, p09) → data (editor, p10) → generation (animator, p11). Each layer reads the previous layer's output and adds its own.

---

## Integration Points Matrix (Per-Track File-Level)

### FORM track

| File | Repo | Status | Change |
|------|------|--------|--------|
| `plugins/pipeline_state/store.py` | kais-hermes-skills | MODIFY | Add `form_factor: str = "portrait"` to `PipelineState` dataclass |
| `skills/kais-movie-pipeline/SKILL.md` | kais-hermes-skills | MODIFY | Line 40 "vertical 9:16" hardcoded assumption → form_factor dispatch; propagation to each expert invocation |
| `skills/kais-movie-pipeline/references/asset-bus-schema.md` | kais-hermes-skills | MODIFY | Document form_factor as episode-level invariant propagated to all slots |
| `skills/movie-experts/cinematographer/SKILL.md` | kais-hermes-skills | MODIFY | 9:16 power points table → conditional on form_factor (add 16:9 rule-of-thirds grid) |
| `skills/movie-experts/drawer/SKILL.md` | kais-hermes-skills | MODIFY | dreamina image dims switch on form_factor |
| LTX-MSR render params (in kais-movie-pipeline/SKILL.md ~line 446) | kais-hermes-skills | MODIFY | `width=1280 height=704` → `width/height from form_factor` |
| `~/.hermes/agents/cinematographer.agent.yaml` | hermes-agent | REGENERATE | Lineage bump (sha256 changed) |
| `~/.hermes/agents/drawer.agent.yaml` | hermes-agent | REGENERATE | Lineage bump |
| `~/.hermes/agents/kais-movie-pipeline.agent.yaml` | hermes-agent | REGENERATE | Lineage bump |

### DUB track

| File | Repo | Status | Change |
|------|------|--------|--------|
| `skills/movie-experts/audio_pipeline/SKILL.md` | kais-hermes-skills | MODIFY | Voicer sub-step: add CosyVoice as primary TTS provider; document LTX native audio coordination (Path A/B routing) |
| `skills/movie-experts/audio_pipeline/references/voicer/cn-tts-model-matrix.md` | kais-hermes-skills | MODIFY | Add CosyVoice 2.0-0.5B row; mark IndexTTS2 as DEPRECATED |
| `skills/movie-experts/audio_pipeline/references/voicer/cosyvoice-presets.md` | kais-hermes-skills | NEW | Voice preset library (per-character prompt templates, emotion control tags, cross-lingual mode) |
| `skills/movie-experts/audio_pipeline/references/workflows/cosyvoice-comfyui.json` | kais-hermes-skills | NEW | ComfyUI workflow JSON using `ComfyUI_FL-CosyVoice3` node |
| `~/.hermes/agents/audio_pipeline.agent.yaml` | hermes-agent | REGENERATE | Lineage bump |

### IMG track

| File | Repo | Status | Change |
|------|------|--------|--------|
| `skills/movie-experts/drawer/SKILL.md` | kais-hermes-skills | MODIFY | Document dreamina production-grade path (vision-verify gate, SLA tracking, reference backfill) |
| `skills/kais-jimeng-cli/SKILL.md` | kais-hermes-skills | MODIFY | Reference `dreamina_manager.py` in prompt instructions; document 10-parallel validated pattern |
| `skills/kais-jimeng-cli/scripts/dreamina_manager.py` | kais-hermes-skills | NEW | asyncio.Semaphore(3) + tenacity retry + 10-parallel batch + SLA tracker + reference backfill queue |
| `~/.hermes/agents/drawer.agent.yaml` | hermes-agent | REGENERATE | Lineage bump (merged with FORM track bump) |
| `~/.hermes/agents/kais-jimeng-cli.agent.yaml` | hermes-agent | REGENERATE | Lineage bump |

### TRANSITION track

| File | Repo | Status | Change |
|------|------|--------|--------|
| `skills/movie-experts/cinematographer/SKILL.md` | kais-hermes-skills | MODIFY | TRANSITION creative layer: author transition_design.json in E-Konte Layer 5 |
| `skills/movie-experts/cinematographer/references/e-konte-format.md` | kais-hermes-skills | MODIFY | Extend `cut_transition_type` to 12-value enum; refactor `next_shot_link` string → structured object; bump schema version |
| `skills/movie-experts/editor/SKILL.md` | kais-hermes-skills | MODIFY | TRANSITION data layer: read transition_design.json, validate against FxRxT matrix, refine |
| `skills/kais-movie-pipeline/SKILL.md` | kais-hermes-skills | MODIFY | TRANSITION generation layer: routing rules for Wan2.2 FLF2V (complex) vs LTX native (dissolve/wipe/fade) vs no-gen (hard_cut) |
| `skills/kais-movie-pipeline/references/pipeline-dag.md` | kais-hermes-skills | MODIFY | Document transition_design slot flow on p09→p10 and p10→p11 edges |
| `skills/kais-movie-pipeline/references/asset-bus-schema.md` | kais-hermes-skills | MODIFY | Add `transition_design` slot (Phase 36 category, generation input) |
| `~/.hermes/agents/cinematographer.agent.yaml` | hermes-agent | REGENERATE | Lineage bump (merged with FORM track bump) |
| `~/.hermes/agents/editor.agent.yaml` | hermes-agent | REGENERATE | Lineage bump |
| `~/.hermes/agents/kais-movie-pipeline.agent.yaml` | hermes-agent | REGENERATE | Lineage bump (merged with FORM track bump) |

---

## Build Order (Dependency-Aware)

### Phase ordering rationale

FORM is foundational — `form_factor` propagates to all other tracks' render params and schema. TRANSITION depends on FORM (transitions are form-factor-sensitive). DUB and IMG are independent of each other and of TRANSITION, but both consume form_factor.

```
Phase A: FORM (foundational)
    │
    ├─→ Phase B1: DUB (parallel-eligible)
    │
    ├─→ Phase B2: IMG (parallel-eligible)
    │
    └─→ Phase C: TRANSITION (depends on FORM + benefits from IMG's vision-verify pattern)
```

### Recommended Phase Structure

1. **FORM** — `form_factor` parameterization
   - Rationale: Everything else reads form_factor. Must land first.
   - Files: `store.py` dataclass, kais-movie-pipeline SKILL.md dispatch, cinematographer/drawer form_factor branches
   - Risk: LOW (additive dataclass field, default preserves current behavior)

2. **DUB** — CosyVoice + LTX audio (parallel with IMG)
   - Rationale: Independent of IMG/TRANSITION. Depends only on FORM (voice presets may vary by form factor for spatial audio placement).
   - Files: audio_pipeline SKILL.md, voicer matrix, new preset + workflow refs
   - Risk: MEDIUM (ComfyUI node availability, CosyVoice2 model deployment)

3. **IMG** — dreamina production-grade (parallel with DUB)
   - Rationale: Independent of DUB/TRANSITION. Vision-verify pattern is reusable by TRANSITION generation layer.
   - Files: drawer SKILL.md, kais-jimeng-cli SKILL.md + scripts, dreamina_manager.py
   - Risk: MEDIUM (GLM-4.6V rate limits compound with dreamina's GLM limits — need separate semaphore)

4. **TRANSITION** — 3-layer collaboration
   - Rationale: Depends on FORM (form_factor-aware transition taxonomy). Benefits from IMG's vision-verify precedent. Most architecturally invasive (E-Konte schema change + new slot + generation routing).
   - Files: cinematographer + editor SKILL.md, e-konte-format.md, pipeline-dag.md, asset-bus-schema.md
   - Risk: HIGH (schema migration on E-Konte, generation routing logic, 12-type taxonomy validation)

5. **Lineage Bump** (after all 4 tracks)
   - Rationale: SKILL.md changes must be finalized before regenerating agent YAMLs. Bumping mid-track would create stale lineages.
   - Files: `~/.hermes/agents/*.agent.yaml` (5-6 agents affected: cinematographer, editor, audio_pipeline, drawer, kais-movie-pipeline, kais-jimeng-cli)
   - Risk: LOW (mechanical transform, documented 5-step procedure)

---

## Cross-Repo Coordination Sequence

**Constraint:** hermes-agent and kais-hermes-skills are separate git repos. No cross-repo atomic commits. Order matters.

```text
Step 1: kais-hermes-skills — implement all 4 tracks (FORM → DUB → IMG → TRANSITION)
          Commit per track (4 commits) or per phase (5+ commits).
          All SKILL.md + refs + Python changes land here.

Step 2: kais-hermes-skills — tag release (e.g. v14.0-skills)

Step 3: hermes-agent — pull/sync kais-hermes-skills at v14.0-skills tag
          (skills are loaded from /data/workspace/kais-hermes-skills/ — path already wired)

Step 4: hermes-agent — run lineage bump procedure
          For each modified SKILL.md:
            - Read new SKILL.md content
            - Compute sha256
            - Compare to ~/.hermes/agents/<expert>.agent.yaml lineage.skill_sha256
            - If different: regenerate persona, update lineage fields
          This is a Hermes-side operation (does NOT touch kais-hermes-skills repo)

Step 5: hermes-agent — commit lineage bumps + .planning/ milestone artifacts
          GSD planning docs (roadmap, requirements, phase results) live in hermes-agent.

Step 6: hermes-agent — tag v14.0
```

**Critical synchronization point:** Between Step 2 and Step 4, the running Hermes instance has NEW SKILL.md content but OLD agent YAML lineages. This is acceptable — lineage drift is ADVISORY per v10.0 design (drift detection warns but does not block). The bump in Step 4 reconciles.

---

## Hermes Orchestrator Impact

### Lineage Bump Workflow (v13.0 P62 procedure, re-run)

v10.0 established the SKILL.md → agent.yaml transform. v13.0 P62 executed it for 15 active experts. v14.0 re-runs the bump ONLY for experts whose SKILL.md content changed.

**Affected agents (expected 6):**
- `cinematographer.agent.yaml` (FORM + TRANSITION)
- `editor.agent.yaml` (TRANSITION)
- `audio_pipeline.agent.yaml` (DUB)
- `drawer.agent.yaml` (FORM + IMG)
- `kais-movie-pipeline.agent.yaml` (FORM + TRANSITION — orchestrator is also an agent)
- `kais-jimeng-cli.agent.yaml` (IMG)

**Unaffected agents (9):** screenplay, scene_builder, performer, continuity, colorist, composer, foley, spatial_audio, mixer, style_genome — no SKILL.md changes in v14.0.

**Bump procedure (per agent):**
1. `sha256sum` the new SKILL.md
2. Compare to `lineage.skill_sha256` in existing `*.agent.yaml`
3. If unchanged → skip
4. If changed → regenerate persona body from new SKILL.md content (using the v10.0 transform rubric), update `lineage.transform_date`, `lineage.skill_sha256`, append `lineage.transform_notes` with "v14.0: <track> changes"

### v10.0 Invariant Exception (explicitly declared in PROJECT.md)

v10.0 established SKILL.md as read-only source for agent personas (invariants L1-L6). v14.0 EXPLICITLY BREAKS this invariant for SKILL.md modifications. PROJECT.md declares this exception. The lineage bump procedure is the reconciliation mechanism — it's not a violation, it's the designed escape hatch.

### Orchestrator Code Changes

**None.** The Hermes orchestrator Python code (`run_agent.py`, `agent/*`, `gateway/*`) is NOT modified in v14.0. All changes are in skill content (kais-hermes-skills) and agent YAML personas (`~/.hermes/agents/`). This respects the v1.0 constraint: "仅 skill 内容,不改 Hermes 核心 Python/JS 代码".

---

## Schema Migrations Summary

| Schema | Location | Migration | Backwards Compat |
|--------|----------|-----------|------------------|
| `PipelineState` | `plugins/pipeline_state/store.py` | Add `form_factor: str = "portrait"` | YES — default preserves current 短剧 behavior; `_STATE_FIELDS` auto-derives |
| E-Konte Layer 5 | `cinematographer/references/e-konte-format.md` | Extend `cut_transition_type` enum (4→12); refactor `next_shot_link` (string→object) | PARTIAL — old files parse via fallback (missing fields default to `"hard_cut"`) |
| Asset-bus schema | `kais-movie-pipeline/references/asset-bus-schema.md` | Add `transition_design` slot (Phase 36 category) | YES — additive slot, old episodes don't have it |
| Voicer model matrix | `audio_pipeline/references/voicer/cn-tts-model-matrix.md` | Add CosyVoice row; mark IndexTTS2 DEPRECATED | YES — provider selection is per-episode, old episodes keep their choice |
| transition_design.json | (new artifact, not in repo) | `schema_version: "1.0"` at creation | N/A — new artifact |
| Agent YAML lineage | `~/.hermes/agents/*.agent.yaml` | Update `lineage.skill_sha256` + `lineage.transform_date` for 6 agents | YES — advisory field, drift doesn't break runtime |

---

## Scalability Considerations

| Concern | Current (v13.0) | At v14.0 (4 tracks integrated) | At scale (100+ episodes) |
|---------|-----------------|-------------------------------|--------------------------|
| Pipeline state size | ~2KB JSON per episode | ~2.2KB (form_factor adds ~20 bytes) | No concern — SQLite-backed |
| Asset-bus slots per episode | 31 slots | 32 slots (transition_design) | 31→32 is negligible |
| E-Konte file size | ~50KB (thin Layer 5) | ~70KB (structured next_shot_link + 12-type enum) | Acceptable — still JSON-parseable |
| Agent YAML regeneration | 15 files (v13.0 baseline) | 6 files per v14.0 ship | Linear with SKILL.md change count |
| ComfyUI workflow count | ~5 (LTX-MSR + variants) | ~7 (+ CosyVoice + LTX-audio variant) | ComfyUI handles workflow dispatch fine |
| dreamina image throughput | ~10 per batch (sequential batches) | ~10 per batch (same, with vision-verify gate) | Vision-verify adds ~2s/image (GLM-4.6V) — batch wallclock +20s, acceptable |

---

## Sources

- `kais-hermes-skills/plugins/pipeline_state/store.py` (lines 1-90) — PipelineState dataclass, `_STATE_FIELDS` derivation (HIGH confidence)
- `kais-hermes-skills/skills/kais-movie-pipeline/SKILL.md` (lines 1-650) — pipeline form assumption line 40, LTX params line 446, TTS line 456, PITFALLS 560-575, dreamina validation 621 (HIGH)
- `kais-hermes-skills/skills/kais-movie-pipeline/references/asset-bus-schema.md` (202 lines) — 31 slots, envelope V3, Phase categories (HIGH)
- `kais-hermes-skills/skills/kais-movie-pipeline/references/pipeline-dag.md` (225 lines) — 13-step DAG, slot flow per edge (HIGH)
- `kais-hermes-skills/skills/movie-experts/cinematographer/SKILL.md` (337 lines) — E-Konte 5-layer, Layer 5 schema (HIGH)
- `kais-hermes-skills/skills/movie-experts/cinematographer/references/e-konte-format.md` (372 lines) — thin transition schema confirmed (HIGH)
- `kais-hermes-skills/skills/movie-experts/editor/SKILL.md` (306 lines) — FxRxT matrix, transition params (HIGH)
- `kais-hermes-skills/skills/movie-experts/audio_pipeline/SKILL.md` (1017 lines) — voicer sub-step, multi-provider TTS, IndexTTS2 current (HIGH)
- `hermes-agent/.planning/research/v10-orchestrator-design/04-MIGRATION-PATH.md` (lines 1-250) — lineage transform 5-step procedure, 15-expert table (HIGH)
- `hermes-agent/.planning/PROJECT.md` (599 lines) — v14.0 milestone definition, invariant exception, cross-repo mode (HIGH)
- `hermes-agent/.planning/research/v14-4track-upgrade/FEATURES.md` — 12-type transition taxonomy, LTX first/last frame clarification (HIGH)
- `hermes-agent/.planning/research/v14-4track-upgrade/STACK.md` — CosyVoice ComfyUI node, Wan2.2 FLF2V local primary, dreamina tenacity pattern (HIGH)
