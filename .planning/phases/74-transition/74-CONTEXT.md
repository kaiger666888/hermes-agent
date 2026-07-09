# Phase 74: TRANSITION - Context

**Gathered:** 2026-07-09
**Status:** Ready for planning
**Mode:** Auto-generated (user prefers direct plan-phase dispatch; Claude's analyzed defaults below)

<domain>
## Phase Boundary

Users can author structured transition designs as first-class pipeline assets, with creative intent (cinematographer Step 9) cleanly separated from post-production execution (editor Step 13), and with per-transition engine routing evaluated across Wan2.2 FLF2V / Hailuo / Vidu / ffmpeg / LTX-2.3 FLF (evaluated, not assumed incapable).

Requirements covered: TRANS-01 (E-Konte Layer 5 schema extension: transition_method 12-enum + visual_hook + camera_continuity), TRANS-02 (next_shot_link structured object migration with backward-compat), TRANS-03 (transition_design.json first-class asset: asset-bus slot + canvas sync + zod enum), TRANS-04 (field-level ownership split documented in cinematographer + editor SKILL.md — FOUND-08 preserved), TRANS-05 (transition-design.md 12-type taxonomy ref), TRANS-06 (transition-engine-routing.md ref with per-transition routing), TRANS-07 (LTX-2.3 FLF + ICLoRA combined workflow research-scope validation).

**Most invasive v14.0 phase** — touches cinematographer SKILL.md (Step 9), editor SKILL.md (Step 13), asset-bus-schema, canvas sync _PHASE_OUTPUT_MAP, E-Konte Layer 5 schema, next_shot_link data shape.

**Out of scope (v15+ per REQUIREMENTS):** TRANS-08 AI-generated whip pan, TRANS-09 custom transition types beyond 12-value, TRANS-10 runtime LLM routing decisions (INFRA-04 violation risk), TRANS-11 LTX-FLF+ICLoRA production rollout (research-scope only in TRANS-07).

</domain>

<decisions>
## Implementation Decisions

### E-Konte Layer 5 Schema Extension (TRANS-01)
- **Field additions to Layer 5 (timing):**
  - `transition_method: Literal["hard_cut", "dissolve", "wipe", "fade", "match_cut_shared_object", "match_cut_shared_landscape", "motion_vector_match", "color_match", "j_cut", "l_cut", "whip_pan", "none"]` — 12-value enum per REQUIREMENTS
  - `visual_hook: str | None` — 具体连接元素 (e.g., "red mug → next shot red car"); free-text per operator's creative intent
  - `camera_continuity: Literal["pan_to", "zoom_to", "dolly_through", "whip_pan", "match_cut_on_motion", "none"]` — 6-value enum
- **Schema location:** Update `references/e-konte-format.md` (existing 5-layer doc) with Layer 5 extension fields; new Pydantic Literal validator in cinematographer output schema
- **Default values:** `transition_method="hard_cut"`, `camera_continuity="none"`, `visual_hook=None` — preserves backward compat for existing E-Konte JSON without these fields
- **Validation:** Strict Pydantic Literal enum (matches FORM-01 form_factor + DUB-02 tts_engine strict-enum pattern)

### next_shot_link Structured Migration (TRANS-02)
- **Old form (deprecated but read-compatible):** `next_shot_link: "shot_02"` (string id)
- **New form:** `next_shot_link: {shot_id: str, transition_method: str, visual_hook: str | None, camera_continuity: str, generation_path: str | None}`
- **Backward-compat reader:** `load_next_shot_link(value)` helper at store.py (or new transition_schema.py module) — if isinstance(value, str), coerce to `{shot_id: value, transition_method: "hard_cut", visual_hook: None, camera_continuity: "none", generation_path: None}`; if isinstance(value, dict), validate via Pydantic
- **Default for `generation_path`:** `None` (operator or generation layer fills it in)
- **Schema migration test:** Old episode JSON with string next_shot_link loads cleanly + auto-coerces to structured default

### transition_design.json First-Class Asset (TRANS-03)
- **Asset-bus slot registration:** Add `transition_design` slot to ASSET_SCHEMA in `plugins/pipeline_state/asset_bus.py`; writer phase = P09 (cinematographer outputs partial); reader phase = P13 (editor consumes for post-production); format = json envelope V3
- **Canvas sync _PHASE_OUTPUT_MAP:** Add `p09: ["shot_intent", "e_konte", "transition_design"]` entry; mirrors existing cinematographer outputs
- **Zod enum (canvas-renderability per PITFALL T-4):** Add `transition_design` to frontend zod schema enum at canvas_sync.py (or equivalent — RESEARCH should locate exact file); prevents "unknown asset type" rendering failure
- **File location:** `~/.hermes/<episode>/transition_design.json` (HERMES_HOME convention); written by cinematographer at Step 9, read by editor at Step 13

### Field-Level Ownership Split (TRANS-04 — FOUND-08 preservation)
- **Cinematographer Step 9 owns CREATIVE INTENT:**
  - `transition_method` (12-enum)
  - `visual_hook` (free text)
  - `camera_continuity` (6-enum)
- **Editor Step 13 owns POST-PRODUCTION EXECUTION:**
  - `cut_duration_frames` (int)
  - `dissolve_curve` (str: "linear" / "ease_in" / "ease_out" / "ease_in_out")
  - `match_cut_alignment_point` (int frame number, optional)
- **Documentation location:** Both `cinematographer/SKILL.md` Step 9 section AND `editor/SKILL.md` Step 13 section get explicit "Field Ownership" subsection citing TRANS-04
- **FOUND-08 compliance:** NO new `transition_designer` expert_id added; ownership split resolves the architectural gap via field-level boundaries

### transition-design.md Ref (TRANS-05)
- **Structure:** 12-type taxonomy with per-type sections:
  - Definition (what this transition does visually)
  - When to use (creative intent triggers)
  - Execution path classification: generation-time / post-production / hybrid
  - Concrete film examples (e.g., match_cut_shared_object → "2001: A Space Odyssey bone-to-spaceship"; whip_pan → "La La Land" opening)
  - Engine routing recommendation (cross-ref to transition-engine-routing.md)
- **Citation discipline:** Real film examples under fair-use with attribution per CLAUDE.md copyright constraint

### transition-engine-routing.md Ref (TRANS-06)
- **Per-transition routing table:**
  - `hard_cut / j_cut / l_cut` → ffmpeg only (no generation)
  - `dissolve / wipe / fade` → ffmpeg xfade filter (post-production fallback)
  - `match_cut_shared_object` → Wan2.2 14B FLF2V (local match-cut via shared object) + ffmpeg fallback
  - `match_cut_shared_landscape` → Hailuo 02 i2v Pro + Vidu keyframe-to-video (cloud Chinese-content backups, opt-in via operator API key per XCUT-04b) + ffmpeg fallback
  - `motion_vector_match` → Hailuo / Vidu (motion-vector generation is cloud-native strength) + ffmpeg fallback
  - `color_match` → ffmpeg color adjustment (post-production)
  - `whip_pan` → currently AI-unreliable per TRANS-08 deferred; ffmpeg whip-pan simulation + operator manual override
  - `none` → no transition (direct concatenation)
- **LTX-2.3 FLF evaluation (NOT assumed incapable per SUMMARY reconciled conflict #1):** Each transition_type includes an "LTX-2.3 FLF Evaluation" subsection documenting the trade-off (PITFALL T-1: LTX-MSR ICLoRA is identity preservation, NOT first/last frame transition; FLF path exists but no character identity continuity from previous shot — drift risk)
- **INFRA-04 compliance (PITFALL X-5):** All transition engine calls under existing `glm_concurrent` semaphore; NO separate transition semaphore; declarative routing rules only (no runtime LLM decisions per TRANS-10 deferred)

### LTX-2.3 FLF + ICLoRA Combined Workflow Validation (TRANS-07)
- **Scope:** Research-scope validation on 1-2 reference shots ONLY; NOT pipeline-integrated
- **Deliverable:** Validation report at `references/ltx-flf-iclora-validation.md` documenting:
  - Workflow setup (ComfyUI node graph — LiconMSR + LTXVConditioning + SamplerCustomAdvanced per community reports)
  - 1-2 reference shot results (visual examples + identity continuity assessment)
  - Production-readiness verdict: ready / deferred to v15+
- **Operator-action handoff:** Operator runs the actual validation shots (research-scope); this phase produces the report TEMPLATE + setup instructions
- **Decision gate:** If validation passes → potential v15+ production rollout (TRANS-11); if fails → documented as deferred with rationale

### XCUT-02 _INSTRUCTION Injection
- Per FORM/DUB/IMG precedent: define `_TRANSITION_DESIGN_INSTRUCTION` module constant in p09_shot_breakdown.py (cinematographer) AND p13 editor module (or equivalent — RESEARCH verifies exact filename); inject via `.task(steps=[f"{_TRANSITION_DESIGN_INSTRUCTION}"])` AND `.constraints(["MUST emit transition_design.json"]); assert via goal-content test. Same MAX_CONSTRAINTS=7 budget rule.

### Claude's Discretion
- Exact wording of transition-design.md per-type sections (within TRANS-05 structure)
- Exact film citation choices (within fair-use + CLAUDE.md discipline)
- Pydantic schema field names (within TRANS-01 + TRANS-02 identifiers)
- Validation report format for TRANS-07 (within "1-2 reference shots + verdict" scope)
- Whether to extend existing test_p09_unit.py or create new test_p09_transition_unit.py for goal-content test
- ffmpeg xfade vs whippan filter parameter defaults (operator-tunable)

</decisions>

<canonical_refs>
## Canonical Refs (Phase 74 downstream agents MUST read)

**Hermes-agent repo (GSD planning context):**
- `.planning/ROADMAP.md` — Phase 74 section (lines 88-104)
- `.planning/REQUIREMENTS.md` — TRANS-01..07 (lines 41-47) + XCUT-04b Hailuo/Vidu API keys handoff
- `.planning/research/v14-4track-upgrade/SUMMARY.md` — TRANSITION research flag (line 160), LTX FLF+ICLoRA gap (line 202), Wan2.2 prompt-following gap (line 205), Hailuo/Vidu cost gap (line 206)
- `.planning/research/v14-4track-upgrade/ARCHITECTURE.md` — 3-layer model (creative + data + generation)
- `.planning/research/v14-4track-upgrade/PITFALLS.md` — T-1 (LTX-FLF vs ICLoRA critical correction), T-2 (cinematographer vs editor FOUND-08), T-3 (schema migration backward-compat), T-4 (3-system canvas registration), T-5 (API quota operator-action), T-6 (cross-engine routing complexity), T-7 (voice continuity), T-8 (creative exceeds engine capability), X-5 (INFRA-04 serial constraint)
- `.planning/research/v14-4track-upgrade/STACK.md` — Wan2.2 14B FLF2V, Hailuo 02 i2v Pro, Vidu keyframe-to-video, ffmpeg xfade
- `.planning/phases/71-form/71-PATTERNS.md`, `72-dub/72-PATTERNS.md`, `73-img/73-PATTERNS.md` — XCUT-02 _INSTRUCTION injection pattern (3-phase precedent)

**Kais-hermes-skills repo (code + refs — READ before editing):**
- `skills/movie-experts/cinematographer/SKILL.md` — Step 9 section (line 189+); E-Konte Layer 5 schema (line 199 "E-Konte 5-layer sheets" + Layer 5 timing reference); Step 9 "next_shot_link" currently string form
- `skills/movie-experts/cinematographer/references/e-konte-format.md` — existing 5-layer E-Konte schema doc; Layer 5 extension insertion point
- `skills/movie-experts/editor/SKILL.md` — Step 13 section (post-production execution)
- `plugins/pipeline_state/asset_bus.py` — ASSET_SCHEMA dict (Phase 33 origin); add transition_design slot
- `skills/kais-movie-pipeline/references/asset-bus-schema.md` — AssetBus V3 slot schema reference (Phase 36-05 Wave 2 full slot table)
- `plugins/pipeline_state/canvas_sync.py` (or equivalent) — _PHASE_OUTPUT_MAP for canvas registration
- Frontend zod schema location (RESEARCH verifies) — canvas-renderability enum
- `skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py` — P09 cinematographer phase module; target for _TRANSITION_DESIGN_INSTRUCTION
- `skills/kais-movie-pipeline/pipeline/phases/p13_*.py` (RESEARCH verifies exact name) — P13 editor phase module; target for ownership split documentation + _INSTRUCTION

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Pydantic Literal strict enum pattern:** Established in FORM-01 (form_factor), DUB-02 (tts_engine); reused for transition_method 12-enum + camera_continuity 6-enum
- **Backward-compat reader pattern:** Established in DUB-02 (per-shot dict `.get(key, default)`); reused for next_shot_link string → structured coercion
- **Asset-bus slot registration pattern:** Existing 31 slots per asset-bus-schema.md; transition_design becomes slot 32 (or next available slot number)
- **Canvas sync _PHASE_OUTPUT_MAP pattern:** Existing entries for shot_intent / e_konte / character_bible etc.; transition_design mirrors
- **XCUT-02 _INJECTION pattern:** 3-phase precedent (FORM _FORM_FACTOR_INSTRUCTION in p09; DUB _TTS_ENGINE_INSTRUCTION in p10; IMG _VISION_VERIFY_INSTRUCTION in p07); same pattern for _TRANSITION_DESIGN_INSTRUCTION in p09 (cinematographer) AND p13 (editor)

### Established Patterns
- **Cross-repo split:** Code in kais-hermes-skills, planning in hermes-agent
- **FOUND-08 frozen 15-expert set:** NO new expert_id; field-level ownership split resolves architectural gap
- **SKILL.md frontmatter byte-identical:** Body-only patches per Phase 71/72/73 precedent
- **INFRA-04 serial constraint (PITFALL X-5):** All transition engine calls under existing glm_concurrent semaphore; declarative routing only

### Integration Points
- `transition_design.json` written by cinematographer at Step 9; read by editor at Step 13
- `next_shot_link` schema migration affects:
  - cinematographer output (Layer 5 timing)
  - editor input (post-production execution reads shot linkage)
  - canvas sync (frontend renders shot transitions)
- E-Konte Layer 5 schema extension affects:
  - cinematographer SKILL.md Step 9 (Layer 5 sheets generation)
  - e-konte-format.md ref
  - Existing episode JSON round-trips (defaults preserve compat)

</code_context>

<specifics>
## Specific Ideas

- **12-value transition_method taxonomy source:** Industry-standard per FEATURES research (StudioBinder, Adobe); NOT over-engineered per TRANS-09 deferred
- **next_shot_link migration smoke test:** Critical to verify existing v13.0 episodes load cleanly without manual migration. Test fixture: 1 pre-v14.0 episode JSON with string next_shot_link; verify coerces to structured default
- **Wan2.2 FLF2V operator-action dependency:** Requires operator to install Wan2.2 model + ComfyUI custom node; documented as opt-in via operator API key per XCUT-04b
- **Hailuo/Vidu cloud APIs:** Opt-in via operator-provided API keys; documented in transition-engine-routing.md + SUMMARY operator-action handoff section
- **LTX-2.3 FLF+ICLoRA validation:** 1-2 reference shots is RESEARCH scope only — NOT a production integration. Verdict (ready / deferred) gates TRANS-11 v15+ production rollout
- **INFRA-04 semaphore reuse:** Transition engine calls share the existing glm_concurrent semaphore even when the engines themselves aren't GLM (because the routing decision is LLM-made per PITFALL X-5)

</specifics>

<deferred>
## Deferred Ideas

- **TRANS-08 (AI-generated whip pan):** Current engines unreliable for cross-shot motion-vector continuity. v15+.
- **TRANS-09 (custom transition types beyond 12-value):** Industry-standard taxonomy sufficient. Avoid over-engineering.
- **TRANS-10 (per-transition runtime LLM routing):** INFRA-04 serial constraint violation risk. v14.0 uses declarative rules only.
- **TRANS-11 (LTX-FLF+ICLoRA production rollout):** Gated by TRANS-07 validation result. v15+ if validation passes.
- **AI-generated motion-vector transitions (beyond Wan2.2 FLF2V):** v15+ when engine reliability improves
- **Multi-character whip pan continuity:** Niche use case; v15+

</deferred>
