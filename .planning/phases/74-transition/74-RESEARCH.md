# Phase 74: TRANSITION - Research

**Researched:** 2026-07-09
**Domain:** kais-movie-pipeline 3-layer transition collaboration (creative intent + data schema + generation routing) — the most invasive v14.0 phase
**Confidence:** HIGH (all architectural claims verified against live kais-hermes-skills code at HEAD `7904bd0`; engine capabilities cross-verified against SUMMARY/PITFALLS/STACK research docs)

## Summary

Phase 74 implements the 3-layer transition collaboration: (1) **creative layer** — cinematographer Step 9 emits structured transition intent fields; (2) **data layer** — `transition_design.json` registered as a first-class pipeline asset flowing from p09 to p13; (3) **generation layer** — per-transition engine routing documentation covering Wan2.2 FLF2V (local) / Hailuo / Vidu (cloud, opt-in) / ffmpeg xfade (post-production fallback) / LTX-2.3 FLF (research-scope validation per TRANS-07).

The phase is **architecturally invasive but mechanically low-risk**: the existing code is pure orchestration markdown + dict contracts, not enforced Pydantic schemas. The `next_shot_link` field is currently a **documentation contract** (defined in `e-konte-format.md` Layer 5 schema, referenced by SKILL.md prose + glossary + ltx2-preview-loop.md) — **no Python code reads or writes it**, so the string → structured migration is a contract change enforced only at the SKILL.md + ref level, not a code migration. The `transition_design` asset-bus slot addition follows the exact pattern of the 31 existing slots (additive dict entry in `ASSET_SCHEMA`). The canvas sync `_PHASE_OUTPUT_MAP` (canvas_sync.py:1676-1764) and the frontend zod schema (`canvasAssetSchema.ts`) need parallel additions or the new asset is silently invisible on canvas (PITFALL T-4).

**Critical architectural discovery:** The frontend zod schema (`kais-aigc-platform/src/lib/canvasAssetSchema.ts`) defines 5 node types: `audio`, `video`, `asset`, `storyboard`, `script`. There is **no "transition" node type**. The cleanest registration path is to map `transition_design` as a `storyboard` canvas_type sibling to `shot_list` + `e_konte_sheets` (it shares p09's storyboard semantics — no media, pre-production design). This avoids the multi-system cost of inventing a new React Flow nodeType. Alternatively, if the frontend should visually distinguish transitions, a new "transition" type can be added to `_PHASE_TYPE_MAP` + `assetDataSchemas` — but that requires a coordinated frontend PR in kais-aigc-platform. **Recommendation: use storyboard canvas_type for v14.0 (zero frontend change), add distinct transition node type in v15+ if operator requests visual separation.**

**Primary recommendation:** Execute TRANS-01 through TRANS-06 as a coordinated 3-commit sequence: (1) SKILL.md + e-konte-format.md schema extension + transition-design.md + transition-engine-routing.md refs (TRANS-01/02/04/05/06 documentation layer); (2) asset_bus.py slot registration + canvas_sync.py _PHASE_OUTPUT_MAP addition + asset-bus-schema.md doc update (TRANS-03 data layer); (3) XCUT-02 `_TRANSITION_DESIGN_INSTRUCTION` injection in p09 + validation test (enforcement layer). TRANS-07 (LTX-FLF+ICLoRA validation) is a separate research-scope deliverable — validation report template only, operator runs the actual shots.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **TRANS-01**: E-Konte Layer 5 extended with `transition_method` (12-value enum: hard_cut / dissolve / wipe / fade / match_cut_shared_object / match_cut_shared_landscape / motion_vector_match / color_match / j_cut / l_cut / whip_pan / none) + `visual_hook` (str | None) + `camera_continuity` (6-value enum: pan_to / zoom_to / dolly_through / whip_pan / match_cut_on_motion / none). Strict Pydantic Literal enum (mirrors FORM-01 form_factor + DUB-02 tts_engine pattern). Defaults: `transition_method="hard_cut"`, `camera_continuity="none"`, `visual_hook=None` (backward compat).
- **TRANS-02**: `next_shot_link` refactored from string id → structured object `{shot_id, transition_method, visual_hook, camera_continuity, generation_path}`. Backward-compat reader `load_next_shot_link(value)` coerces string to `{shot_id: value, transition_method: "hard_cut", visual_hook: None, camera_continuity: "none", generation_path: None}`. Migration test: old episode JSON loads cleanly.
- **TRANS-03**: `transition_design.json` registered in 3 systems: asset-bus Phase 36 slot + canvas sync `_PHASE_OUTPUT_MAP` + zod enum (canvas-renderability per PITFALL T-4). Writer = P09 (cinematographer partial); reader = P13 (editor post-production).
- **TRANS-04**: Field-level ownership split — cinematographer Step 9 owns CREATIVE INTENT (transition_method / visual_hook / camera_continuity); editor Step 13 owns POST-PRODUCTION EXECUTION (cut_duration_frames / dissolve_curve / match_cut_alignment_point). NO new `transition_designer` expert_id (FOUND-08 preserved).
- **TRANS-05**: `references/transition-design.md` ref with 12-type taxonomy (definition / when-to-use / execution-path classification: generation-time / post-production / hybrid / concrete film examples / engine routing cross-ref). Real film examples under fair-use with attribution per CLAUDE.md.
- **TRANS-06**: `references/transition-engine-routing.md` ref with per-transition routing table. INFRA-04 compliance: all transition engine calls under existing `glm_concurrent` semaphore; NO separate transition semaphore; declarative routing only (no runtime LLM decisions per TRANS-10 deferred).
- **TRANS-07**: LTX-2.3 FLF + ICLoRA combined workflow validated on 1-2 reference shots — **research-scope only**, NOT pipeline-integrated. Deliverable: validation report template at `references/ltx-flf-iclora-validation.md`. Decision gate: if validation passes → v15+ production rollout (TRANS-11); if fails → documented as deferred.
- **XCUT-02**: `_TRANSITION_DESIGN_INSTRUCTION` constant in p09_shot_breakdown.py AND p13_delivery.py, injected via `.task(steps=[...])` AND `.constraints([...])`, asserted via goal-content test. MAX_CONSTRAINTS=7 budget rule.

### Claude's Discretion
- Exact wording of transition-design.md per-type sections (within TRANS-05 structure)
- Exact film citation choices (within fair-use + CLAUDE.md discipline)
- Pydantic schema field names (within TRANS-01 + TRANS-02 identifiers)
- Validation report format for TRANS-07 (within "1-2 reference shots + verdict" scope)
- Whether to extend existing test_p09_unit.py or create new test_p09_transition_unit.py for goal-content test
- ffmpeg xfade vs whippan filter parameter defaults (operator-tunable)

### Deferred Ideas (OUT OF SCOPE)
- **TRANS-08** AI-generated whip pan transitions (v15+)
- **TRANS-09** custom transition types beyond 12-value taxonomy (avoid over-engineering)
- **TRANS-10** per-transition runtime LLM routing decisions (INFRA-04 serial constraint violation risk; v14.0 uses declarative rules only)
- **TRANS-11** LTX-FLF+ICLoRA production rollout (gated by TRANS-07 validation; v15+ if passes)
- AI-generated motion-vector transitions beyond Wan2.2 FLF2V (v15+)
- Multi-character whip pan continuity (niche; v15+)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TRANS-01 | E-Konte Layer 5 schema extension (transition_method 12-enum + visual_hook + camera_continuity 6-enum) | `e-konte-format.md` Layer 5 schema location verified (line 116-130). Extension follows existing 4-value `cut_transition_type` pattern. Pydantic Literal pattern precedents: FORM-01 `form_factor` (store.py), DUB-02 `tts_engine` (dub_validators.py). |
| TRANS-02 | next_shot_link string → structured object with backward-compat coercion | `next_shot_link` is currently a **documentation contract** only (no Python code reads/writes it — grep confirms only `.md` references). Migration is SKILL.md + ref contract change, not a code migration. Backward-compat reader pattern established by DUB-02 `.get(key, default)`. |
| TRANS-03 | transition_design.json first-class asset in 3 systems | Asset-bus slot addition pattern verified (31 existing slots, additive dict entry in `ASSET_SCHEMA`). Canvas sync `_PHASE_OUTPUT_MAP` at canvas_sync.py:1676 (exact dict). Frontend zod at `canvasAssetSchema.ts` — **5 node types, no "transition"** — recommendation: reuse `storyboard` canvas_type (zero frontend change). |
| TRANS-04 | Field-level ownership split cinematographer (Step 9) vs editor (Step 13) | Cinematographer SKILL.md Step 9 verified (line 189-208, sub-step 5 produces Layer 5 timing including next_shot_link). Editor SKILL.md "Transition Design" Workflow step 7 (line 197) + p13_delivery.py (line 89: editor performs final-cut + render). FOUND-08 preserved — no new expert_id. |
| TRANS-05 | transition-design.md 12-type taxonomy ref | New ref under `cinematographer/references/` (mirrors e-konte-format.md structure) OR `kais-movie-pipeline/references/` (mirrors video-engine-comparison.md). Both are valid; CONTEXT.md `canonical_refs` lists cinematographer path. |
| TRANS-06 | transition-engine-routing.md per-transition routing ref | New ref under `kais-movie-pipeline/references/` (sibling to video-engine-comparison.md). ffmpeg xfade availability VERIFIED: ffmpeg 6.1.1 with xfade filter supported. Wan2.2 FLF2V + Hailuo + Vidu integration details from STACK.md. LTX-2.3 FLF evaluation per-transition (NOT assume incapable per SUMMARY reconciled conflict #1). |
| TRANS-07 | LTX-2.3 FLF + ICLoRA combined workflow research-scope validation | Validation report template only — operator runs actual shots. LTX-MSR ICLoRA (identity) vs FLF (first/last frame) orthogonality VERIFIED per PITFALLS T-1. No combined turnkey workflow exists (community reports + LTX official docs). |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Tech stack**: SKILL.md + references/*.md pure markdown; no Hermes Python/JS core code changes
- **Deliverable form**: skill content only (refs + SKILL.md + eval scripts)
- **Language**: SKILL.md bilingual (EN YAML + metadata; EN structure + 中文 body); refs 中文-primary with EN key terms
- **Copyright**: All refs cite source + copyright status; fair-use only
- **Compatibility**: Do NOT break existing 14-expert expert_id + related_skills graph; FOUND-08 frozen 15-expert set
- **Code style**: `from __future__ import annotations` at module top; `encoding="utf-8"` on every `open()`; double-quoted strings; Ruff PLW1514 single-rule enforcement
- **Naming**: snake_case for modules/functions/locals; PascalCase for classes; `UPPER_SNAKE_CASE` for constants; `_`-prefix for private helpers
- **Skill conventions**: `tags` lowercase hyphenated; `related_skills` = expert name list; `expert_id` stable; `metrics` quality dimensions
- **GSD enforcement**: All repo edits via GSD workflow; cross-repo topology (code → kais-hermes-skills, planning → hermes-agent/.planning/)
- **INFRA-04**: `MAX_CONCURRENT_GL=1` serial constraint preserved (per MEMORY.md `feedback-glm-overload-reduce-concurrency.md`)

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Creative transition intent (transition_method, visual_hook, camera_continuity) | Cinematographer Step 9 (p09_shot_breakdown.py) | — | Creative intent belongs to the shot designer, not the cutter. Cinematographer already owns E-Konte Layer 5 `cut_transition_type` + `next_shot_link`. [CITED: cinematographer/SKILL.md:189-208] |
| Post-production transition execution (cut_duration_frames, dissolve_curve, match_cut_alignment_point) | Editor Step 13 (p13_delivery.py) | P12 composition (ffmpeg concat) | Editor owns FxRxT T-dimension (Transition mode) per existing SKILL.md Workflow step 7 + p13 final-cut execution. [CITED: editor/SKILL.md:197; p13_delivery.py:89] |
| Transition design data schema + asset registration | AssetBus (plugins/pipeline_state/asset_bus.py) | Canvas sync (canvas_sync.py) + frontend zod (canvasAssetSchema.ts) | AssetBus is the canonical slot registry (31 slots); canvas sync mirrors to UI; zod validates node data. 3-system registration prevents invisible-asset pitfall (T-4). [CITED: asset_bus.py:40-463; canvas_sync.py:1676] |
| Per-transition engine routing (declarative rules) | references/transition-engine-routing.md (documentation) | — | v14.0 uses declarative rules only (TRANS-10 deferred). Routing logic lives in markdown, NOT runtime LLM decisions (INFRA-04 compliance). [CITED: CONTEXT.md TRANS-06 lock] |
| ffmpeg xfade execution | P12 composition (p12_composition.py) | — | P12 already invokes ffmpeg for concat + audio mix. xfade filter belongs at the same execution site. [VERIFIED: p12_composition.py:113-126 ffmpeg commands] |
| Wan2.2 FLF2V / Hailuo / Vidu generation (opt-in) | P11 video render (p11_video_render.py) | New templates (wan_flf2v_batch_render.py, hailuo_flf_client.py, vidu_flf_client.py) | P11 already dispatches LTX-MSR renders via templates/. Cloud engines follow the same pattern. NOT v14.0 mandatory (operator-action handoff per XCUT-04b). [CITED: STACK.md TRANSITION §Step C] |
| LTX-2.3 FLF + ICLoRA combined workflow validation (TRANS-07) | references/ltx-flf-iclora-validation.md (report template) | Operator (runs actual shots) | Research-scope only. Template + setup instructions live in kais-hermes-skills; operator executes validation. [CITED: CONTEXT.md TRANS-07 lock] |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | 2.13.4 | Literal enum enforcement for transition_method + camera_continuity | Already pinned in hermes-agent pyproject.toml; FORM-01 form_factor + DUB-02 tts_engine precedent [VERIFIED: pyproject.toml] |
| ffmpeg | 6.1.1-3ubuntu5 | xfade filter for dissolve/wipe/fade/J-cut/L-cut post-production fallback | Already in Docker stack; xfade filter confirmed supported via `ffmpeg -h filter=xfade` [VERIFIED: local probe 2026-07-09] |
| httpx | 0.28.1 | REST client for Hailuo 02 + Vidu cloud APIs (opt-in, operator API key) | Already pinned; Phase 73 vision_verify.py + Phase 72 ComfyUI submission both use it [VERIFIED: pyproject.toml] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Wan2.2 14B FLF2V | (ComfyUI native node `WanFirstLastFrameToVideo`) | Local match-cut via shared object generation | Opt-in for match_cut_shared_object transitions; ~21GB VRAM; comfyui-primary container [CITED: STACK.md] |
| Hailuo 02 i2v Pro | (REST API platform.minimax.io) | Cloud backup for Chinese-content match-cut / motion-vector | Opt-in via operator MINIMAX_API_KEY; $0.056/sec [CITED: STACK.md; operator-action handoff XCUT-04b] |
| Vidu keyframe-to-video | (REST API help.aliyun.com) | Cloud backup for Chinese-content transitions | Opt-in via operator VIDU_API_KEY [CITED: STACK.md; operator-action handoff XCUT-04b] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ffmpeg xfade for dissolve/wipe/fade | LTX-2.3 native time-based transitions | ffmpeg is free, deterministic, no GPU; LTX native is generation-time but adds VRAM cost. ffmpeg wins for simple transitions per CONTEXT.md TRANS-06 routing table. |
| Reusing storyboard canvas_type for transition_design | New "transition" React Flow nodeType | Zero frontend change vs coordinated PR in kais-aigc-platform. v14.0 = reuse; v15+ = new type if operator requests visual separation. |
| Extending e-konte-format.md Layer 5 schema | New standalone transition-schema.md ref | Layer 5 already owns `cut_transition_type` + `next_shot_link`; extending keeps schema cohesive. New ref fragments the contract. [VERIFIED: e-konte-format.md:116-130] |

**Installation:** Zero new Python packages (all pinned in pyproject.toml). Zero new Docker dependencies (ffmpeg 6.1.1 already in stack). Wan2.2 FLF2V ComfyUI node already available in comfyui-primary container. Hailuo/Vidu API keys = operator-action handoff (XCUT-04b), not phase deliverable.

**Version verification:** [VERIFIED: local probes 2026-07-09]
- `pydantic==2.13.4` — confirmed via pyproject.toml:44-48
- `httpx==0.28.1` — confirmed via pyproject.toml:35
- `ffmpeg 6.1.1-3ubuntu5` — confirmed via `ffmpeg -version`; xfade filter supported

## Package Legitimacy Audit

> This phase installs **zero external packages**. All libraries are already pinned in `pyproject.toml` (Pydantic, httpx) or available system-wide (ffmpeg). No slopcheck run required — there are no new package recommendations to audit.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| (none — zero new packages) | — | — | — | — | — | — |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```text
                                    ┌─────────────────────────────────────┐
                                    │  Creative Layer (Cinematographer)    │
                                    │  p09_shot_breakdown.py Step 9        │
                                    │  ┌─────────────────────────────────┐ │
                                    │  │ E-Konte Layer 5 (EXTENDED):      │ │
                                    │  │  transition_method (12-enum)  ───┼─┼─┐
                                    │  │  visual_hook (str|None)          │ │ │
                                    │  │  camera_continuity (6-enum)      │ │ │
                                    │  │  next_shot_link (structured obj) │ │ │
                                    │  └─────────────┬───────────────────┘ │ │
                                    └────────────────┼─────────────────────┘ │
                                                     │ writes                │
                                                     ▼                       │
┌──────────────────────────────────────────────────────────────────────────┐ │
│  Data Layer (AssetBus + Canvas)                                          │ │
│  ┌──────────────────────────┐   ┌────────────────────────────────────┐   │ │
│  │ ASSET_SCHEMA["transition │   │ canvas_sync.py                     │   │ │
│  │ _design"] (NEW slot ~32) │   │  _PHASE_OUTPUT_MAP["p09"] +=       │───┼─┤
│  │  writer_phase: p09       │   │    ("transition_design", ...)      │   │ │
│  │  reader_phases: [p13]    │   │  _PHASE_TYPE_MAP["p09"] =          │   │ │
│  └──────────┬───────────────┘   │    ("storyboard","storyboard")     │   │ │
│             │                   └─────────────┬──────────────────────┘   │ │
│             │                                 │ mirrors to UI            │ │
│             ▼                                 ▼                          │ │
│  ┌──────────────────────────┐   ┌────────────────────────────────────┐   │ │
│  │ transition_design.json   │   │ kais-aigc-platform/frontend        │   │ │
│  │  {schema_version:"1.0",  │   │  canvasAssetSchema.ts              │   │ │
│  │   transitions:[...],     │   │  (storyboard type — zero change)   │   │ │
│  │   form_factor, ...}      │   │                                    │   │ │
│  └──────────┬───────────────┘   └────────────────────────────────────┘   │ │
│             │ reads (post-production execution fields)                   │ │
└─────────────┼────────────────────────────────────────────────────────────┘ │
              │                                                              │
              ▼                                                              │
┌──────────────────────────────────────────────────────────────────────────┐ │
│  Generation + Execution Layer                                            │ │
│  ┌─────────────────────┐  ┌──────────────────┐  ┌────────────────────┐   │ │
│  │ P11 video render    │  │ P12 composition  │  │ P13 delivery       │   │ │
│  │ (Wan2.2 FLF2V /     │  │ (ffmpeg xfade    │  │ (editor final-cut  │   │ │
│  │  Hailuo / Vidu)     │  │  dissolve/wipe/  │  │  + cut_duration_   │   │ │
│  │  OPT-IN operator    │  │  fade/J-cut/     │  │  frames +          │   │ │
│  │  API key            │  │  L-cut fallback) │  │  dissolve_curve +  │   │ │
│  │                     │  │                  │  │  match_cut_align)  │   │ │
│  └─────────────────────┘  └──────────────────┘  └────────────────────┘   │ │
│                                                                    ▲     │ │
│  Routing decision (declarative, NOT runtime LLM):                  │     │ │
│    IF transition_method IN {hard_cut, j_cut, l_cut}  ──────────────┼─────┘ │
│    IF transition_method IN {dissolve, wipe, fade}  ──► P12 ffmpeg xfade  ◄─┘
│    IF transition_method == match_cut_shared_object  ──► P11 Wan2.2 FLF2V
│    IF transition_method == match_cut_shared_landscape ──► P11 Hailuo/Vidu
│    IF transition_method == color_match  ──► P12 ffmpeg color adjustment
│    IF transition_method == whip_pan  ──► P12 ffmpeg whippan (AI unreliable per TRANS-08)
└──────────────────────────────────────────────────────────────────────────┘
```

**Reader trace (primary use case — operator authors transition design, pipeline executes):**
1. Cinematographer at Step 9 (p09) reads CONTEXT.md TRANS-01 schema + e-konte-format.md Layer 5 extension
2. Cinematographer emits `transition_design.json` via `_TRANSITION_DESIGN_INSTRUCTION` injected goal (XCUT-02 enforcement)
3. AssetBus.write("transition_design", data) registers the slot (TRANS-03 system 1)
4. Canvas sync subscriber reads `result.outputs.transition_design` via `_PHASE_OUTPUT_MAP["p09"]` (TRANS-03 system 2) and mirrors to frontend as storyboard node
5. Frontend zod `storyboard` schema validates the node (TRANS-03 system 3 — zero change)
6. Editor at Step 13 (p13_delivery.py) reads `transition_design` asset-bus slot + emits `cut_duration_frames` / `dissolve_curve` / `match_cut_alignment_point` execution fields (TRANS-04 ownership split)
7. P12 composition dispatches ffmpeg xfade for dissolve/wipe/fade transitions per the routing rule (TRANS-06)
8. P11 video render dispatches Wan2.2 FLF2V / Hailuo / Vidu for match-cut generation IF operator API keys present (TRANS-06, XCUT-04b opt-in)

### Recommended Project Structure
```
skills/movie-experts/cinematographer/
├── SKILL.md                                  # MODIFY Step 9 (line 189-208): add TRANSITION DESIGN subsection citing TRANS-04
├── references/
│   ├── e-konte-format.md                     # MODIFY Layer 5 schema (line 116-130): extend transition_method 12-enum + refactor next_shot_link
│   ├── transition-design.md                  # NEW (TRANS-05): 12-type taxonomy ref
│   └── (existing refs unchanged)
└── (existing structure unchanged)

skills/movie-experts/editor/
├── SKILL.md                                  # MODIFY Workflow Step 7 (line 197) + add Step 13 ownership subsection: cut_duration_frames / dissolve_curve / match_cut_alignment_point
└── (existing structure unchanged)

skills/kais-movie-pipeline/
├── references/
│   ├── asset-bus-schema.md                   # MODIFY: add transition_design slot to slot table
│   ├── transition-engine-routing.md          # NEW (TRANS-06): per-transition routing table
│   ├── ltx-flf-iclora-validation.md          # NEW (TRANS-07): validation report template
│   └── (existing refs unchanged)
├── pipeline/phases/
│   ├── p09_shot_breakdown.py                 # MODIFY: add _TRANSITION_DESIGN_INSTRUCTION (XCUT-02)
│   └── p13_delivery.py                       # MODIFY: add editor post-production execution fields + _INSTRUCTION (XCUT-02)
└── tests/
    ├── test_p09_unit.py                      # EXTEND (or new test_p09_transition_unit.py per CONTEXT.md discretion): goal-content assertion
    └── test_transition_migration.py          # NEW (TRANS-02): backward-compat reader test

plugins/pipeline_state/
└── asset_bus.py                              # MODIFY: add "transition_design" slot to ASSET_SCHEMA dict

plugins/kais_aigc/
└── canvas_sync.py                            # MODIFY _PHASE_OUTPUT_MAP["p09"] (line 1721-1724): add transition_design entry
```

### Pattern 1: ASSET_SCHEMA Slot Addition (TRANS-03 system 1)
**What:** Add a new slot to the `ASSET_SCHEMA` dict in `asset_bus.py`.
**When:** Any new artifact type needs pipeline-wide visibility.
**Example:**
```python
# Source: asset_bus.py:40-463 (existing 31-slot pattern, verified 2026-07-09)
# Insert after the Phase 36-02 block (shot-list + e-konte-sheets siblings):

# ── Phase 74 additions — transition design slot (TRANS-03) ──────────
# Phase 74 registers this slot so p09_shot_breakdown (cinematographer)
# can write transition design, and p13_delivery (editor) can read it
# for post-production execution. JSON format (envelope-wrapped, atomic
# write). Per-plan asset-bus extension (D-36-05): PRESERVES existing
# slots byte-equivalent — only appends.
"transition-design": {
    "file": "transition-design.json",
    "format": "json",
    "description": "Transition design (creative intent from cinematographer "
                   "Step 9; consumed by editor Step 13 for post-production "
                   "execution). Per-shot transition_method (12-enum) + "
                   "visual_hook + camera_continuity.",
    "writer_phase": "p09_shot_breakdown",
    "reader_phases": ["p13_delivery"],
},
```

### Pattern 2: Canvas Sync _PHASE_OUTPUT_MAP Addition (TRANS-03 system 2)
**What:** Add `transition_design` to the p09 entry in `_PHASE_OUTPUT_MAP`.
**When:** New asset needs canvas visibility (PITFALL T-4 — 3-system registration).
**Example:**
```python
# Source: canvas_sync.py:1676-1764 (verified 2026-07-09)
# Current p09 entry:
"p09": [
    ("shot_list", "分镜列表", "storyboard", False),
    ("e_konte_sheets", "Eコンテ", "storyboard", False),
],
# After Phase 74:
"p09": [
    ("shot_list", "分镜列表", "storyboard", False),
    ("e_konte_sheets", "Eコンテ", "storyboard", False),
    ("transition_design", "转场设计", "storyboard", False),  # NEW TRANS-03
],
```

### Pattern 3: XCUT-02 _INSTRUCTION Constant Injection (enforcement layer)
**What:** Define `_TRANSITION_DESIGN_INSTRUCTION` module constant + inject into `.task(steps=[...])` AND `.constraints([...])`.
**When:** Every MUST/MUST NOT added to SKILL.md (META-RULE X-2 prevention per PITFALL X-2).
**Example:**
```python
# Source: p09_shot_breakdown.py:51-89 precedent (_CROSS_CUTTING_INSTRUCTION + _FORM_FACTOR_INSTRUCTION)
# Source: p07_scene_generation.py Phase 73 precedent (_VISION_VERIFY_INSTRUCTION)

_TRANSITION_DESIGN_INSTRUCTION = (
    "TRANSITION DESIGN (v14.0 TRANS-01..04 — mandatory for every shot):\n"
    "1. Each shot's E-Konte Layer 5 timing MUST include:\n"
    "   - transition_method: one of 12 values (hard_cut / dissolve / wipe / fade / "
    "     match_cut_shared_object / match_cut_shared_landscape / motion_vector_match / "
    "     color_match / j_cut / l_cut / whip_pan / none). Default 'hard_cut'.\n"
    "   - visual_hook: free-text describing the connecting element (e.g., 'red mug → "
    "     next shot red car'); null when not applicable.\n"
    "   - camera_continuity: one of 6 values (pan_to / zoom_to / dolly_through / "
    "     whip_pan / match_cut_on_motion / none). Default 'none'.\n"
    "2. next_shot_link MUST be a structured object {shot_id, transition_method, "
    "   visual_hook, camera_continuity, generation_path} — NOT a bare string. "
    "   Backward-compat: if reading an old episode, coerce string to "
    "   {shot_id: <string>, transition_method: 'hard_cut', ...defaults}.\n"
    "3. Emit transition_design.json as a first-class asset: per-shot entries with "
    "   {shot_id, transition_method, visual_hook, camera_continuity, form_factor}.\n"
    "4. Ownership split (TRANS-04): cinematographer owns creative intent "
    "   (transition_method / visual_hook / camera_continuity); editor Step 13 owns "
    "   post-production execution (cut_duration_frames / dissolve_curve / "
    "   match_cut_alignment_point). DO NOT emit execution fields here."
)
```

**MAX_CONSTRAINTS=7 budget:** Current p09 has 6 constraints (line 396-404). Adding 1 transition constraint brings it to 7 — exactly at the limit. Plan must consolidate the transition MUST with an existing constraint OR replace a redundant one. Recommend merging with the existing form_factor constraint (line 399) since both are Layer 5 fields — OR splitting p09 _INSTRUCTION into 2 goal builders (not recommended; breaks CF-36-03 single-delegate pattern). **Decision for planner: consolidate transition_method + form_factor into one cross-cutting Layer 5 constraint.**

### Anti-Patterns to Avoid
- **Inventing a new "transition" React Flow nodeType for canvas** — requires coordinated frontend PR in kais-aigc-platform; reuse `storyboard` canvas_type for v14.0 (zero frontend change). v15+ if operator requests visual separation.
- **Adding a separate asyncio.Semaphore for transition engine calls** — INFRA-04 violation risk (PITFALL X-5). All routing decisions stay under existing `glm_concurrent` semaphore (`MAX_CONCURRENT_GL=1`).
- **Making Hailuo/Vidu cloud APIs a hard dependency** — must degrade gracefully to post-production ffmpeg fallback if operator hasn't provisioned API keys (XCUT-04b opt-in).
- **Assuming LTX-2.3 FLF can do identity-preserving transitions** — PITFALL T-1 CRITICAL CORRECTION: ICLoRA (identity) and FLF (first/last frame) are separate workflows; no combined turnkey option exists. Per-transition trade-off required.
- **Encoding transition execution fields in cinematographer Step 9** — violates TRANS-04 ownership split. Creative intent only at Step 9; execution fields at editor Step 13.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dissolve/wipe/fade/J-cut/L-cut transitions | Custom Python video processing | ffmpeg xfade filter (6.1.1 already in stack) | ffmpeg is deterministic, free, GPU-free, industry-standard. Custom Python adds VRAM + complexity for trivial transitions. [VERIFIED: `ffmpeg -h filter=xfade` 2026-07-09] |
| Backward-compat next_shot_link coercion | Ad-hoc isinstance checks at each read site | Single `load_next_shot_link(value)` helper (new transition_schema.py module OR inline in store.py) | Centralized coercion prevents drift across read sites. Pattern established by DUB-02 `.get(key, default)`. [CITED: CONTEXT.md TRANS-02 lock] |
| Transition design data schema | Free-form JSON | Pydantic Literal strict enum (12-value transition_method + 6-value camera_continuity) | Type-checker + runtime validation catches typos. FORM-01 form_factor + DUB-02 tts_engine precedent. [VERIFIED: store.py form_factor pattern] |
| Canvas node registration | Manual HTTP calls to canvas API | `_PHASE_OUTPUT_MAP` dict entry (canvas_sync.py:1676) + existing subscriber auto-discovers | Manual HTTP is the documented #1 canvas pitfall (silent failure). Subscriber handles degrade-tolerant dispatch. [CITED: canvas_sync.py:700-900] |
| Per-transition engine routing decisions | Runtime LLM "which engine should I use?" | Declarative routing table in transition-engine-routing.md | INFRA-04 serial constraint violation risk if LLM makes N parallel routing decisions. Declarative rules are deterministic + zero-GLM-cost. [CITED: PITFALL X-5; CONTEXT.md TRANS-06 lock] |

**Key insight:** The transition domain already has industry-standard solutions for every sub-problem (ffmpeg for simple transitions, Wan2.2 for match-cut, Hailuo/Vidu for cloud backup). v14.0's contribution is the **3-layer architecture** (creative / data / generation) + **ownership split** — not new algorithms. The complexity is in the coordination contract, not the execution.

## Runtime State Inventory

> Phase 74 involves a schema migration (next_shot_link string → structured object) + asset-bus slot addition. Applicable.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | **None — `next_shot_link` is a documentation contract, not persisted in Python code.** Grep across kais-hermes-skills `*.py` files: zero Python code reads or writes `next_shot_link`. The field exists only in `e-konte-format.md` (Layer 5 schema doc, line 126 + 332), `glossary.md`, `ltx2-preview-loop.md` (pacing check prose), `visual_executor/SKILL.md` (handoff description), and `cinematographer/SKILL.md` Step 9 sub-step 5. Existing episode JSON (Volvo, silly-cat-30s) may have `next_shot_link` as string in their e-konte-sheets.json asset-bus slot — but no Python consumer breaks because no Python reads it. | Code edit (SKILL.md + ref contract change). No data migration script needed. Backward-compat reader `load_next_shot_link(value)` handles any legacy string-form values in existing episode JSON at read time. |
| Live service config | **None.** No external service stores transition config. Canvas platform renders whatever the sync subscriber sends — adding transition_design to _PHASE_OUTPUT_MAP is purely additive (no existing service config to update). | None |
| OS-registered state | **None.** No OS-level registrations embed transition strings. | None |
| Secrets/env vars | **None new for v14.0 mandatory path.** Potential future env vars (MINIMAX_API_KEY, VIDU_API_KEY) are operator-action handoffs (XCUT-04b), not phase deliverables. | None (operator-action handoff documented in transition-engine-routing.md) |
| Build artifacts | **None.** No compiled artifacts, no installed packages carry the transition schema. ASSET_SCHEMA dict is source-code-level. | None |

**Nothing found in category:** Stored data — verified by `grep -rn "next_shot_link" kais-hermes-skills --include="*.py"` returning zero hits. The field is purely markdown-defined.

## Common Pitfalls

### Pitfall 1: 3-System Canvas Registration Incomplete (PITFALL T-4)
**What goes wrong:** `transition_design.json` is written to disk but invisible on the canvas UI.
**Why it happens:** Asset bus + canvas sync `_PHASE_OUTPUT_MAP` + frontend zod enum are 3 separate systems. Missing any one = silent invisibility.
**How to avoid:** Register in all 3 in the same commit: (1) `ASSET_SCHEMA["transition-design"]` in asset_bus.py; (2) `_PHASE_OUTPUT_MAP["p09"]` += `("transition_design", ...)` in canvas_sync.py; (3) frontend zod — **reuse storyboard canvas_type** so zero frontend change is needed (the existing storyboard schema in canvasAssetSchema.ts accepts arbitrary structured fields via `withYamlOptional`).
**Warning signs:** Canvas shows 0 transition nodes after p09 completes; check canvas-sync-errors.jsonl for schema validation failures.

### Pitfall 2: MAX_CONSTRAINTS=7 Budget Exceeded in p09 (XCUT-02)
**What goes wrong:** Adding `_TRANSITION_DESIGN_INSTRUCTION` as a new `.constraints([...])` entry raises GoalBuilder error: "MAX_CONSTRAINTS=7 exceeded".
**Why it happens:** p09 currently has 6 constraints (p09_shot_breakdown.py:396-404). Adding 1 = 7 (at limit). Adding 2 = 8 (over budget).
**How to avoid:** Consolidate the transition_method MUST with an existing constraint. Recommend merging with the existing form_factor + cross-cutting params constraint (line 399) — both are Layer 5 E-Konte fields, semantically cohesive. Alternative: convert one existing constraint to a `.task(steps=[...])` entry (task steps are not budget-counted).
**Warning signs:** `ValueError: MAX_CONSTRAINTS` at p09 goal construction time. Phase 71-01 hit this exact issue (STATE.md decision log: "Consolidated form_factor constraint with cross-cutting constraint").

### Pitfall 3: LTX-FLF vs ICLoRA Conflation (PITFALL T-1 CRITICAL CORRECTION)
**What goes wrong:** Design assumes "LTX-2.3 can do identity-preserving first/last frame transitions" — it cannot.
**Why it happens:** LTX-2.3 has TWO ORTHOGONAL capabilities: ICLoRA (`ltx/msr` LiconMSR, identity preservation via ref1-ref5) AND FLF (`ltx/fflf` + `ltx/singularityFFLF`, first/last frame conditioning). These are SEPARATE workflows with no merged turnkey option.
**How to avoid:** Per-transition routing rule in transition-engine-routing.md must explicitly state the trade-off: `IF transition needs identity continuity → MSR + post-production match-cut`; `IF transition needs frame-interpolation → FLF + accept identity drift risk OR use post-production match-cut`. TRANS-07 validation report template must document this trade-off with concrete ComfyUI node graph.
**Warning signs:** Generated transition shots show character identity drift (different face/clothing between frames).

### Pitfall 4: Editor Step 7 vs Step 13 Confusion
**What goes wrong:** CONTEXT.md says "editor Step 13 owns post-production execution" but editor SKILL.md Workflow has Step 7 = "Transition Design". Phase implements changes at wrong step.
**Why it happens:** Editor SKILL.md has 13 Workflow steps (line 191-203). Step 7 is "Transition Design" (creative/routing decision); Step 13 is "Output EDL" (final artifact generation). The "Step 13" in CONTEXT.md refers to the **pipeline phase** p13_delivery.py (where editor performs final-cut + render), not editor SKILL.md Workflow Step 13.
**How to avoid:** Document the ownership split in BOTH locations: editor SKILL.md Workflow Step 7 (design decision — reads transition_design.json, validates against FxRxT matrix) AND p13_delivery.py (execution — emits cut_duration_frames / dissolve_curve / match_cut_alignment_point). The "Step 13" in TRANS-04 refers to the pipeline phase, which corresponds to editor SKILL.md Workflow Steps 7-13 collectively.
**Warning signs:** Plan assigns ownership changes to the wrong SKILL.md section.

### Pitfall 5: Frontend Zod Schema Mismatch
**What goes wrong:** Canvas save-v2 returns HTTP 400 with "storyboard node requires shot_type" or similar validation error.
**Why it happens:** transition_design.json doesn't naturally fit the storyboard schema (which expects `shot_id`, `shot_type`, `duration_sec`). Forcing it produces validation failures.
**How to avoid:** Two options: (A) emit transition_design as a dict-of-per-shot-transitions (matching storyboard list semantic) where each entry has `shot_id` + `transition_method` + `visual_hook` + `camera_continuity` — naturally fits storyboard schema; OR (B) emit as a single summary `script` node (which has looser schema: label + description only). Recommend option A for visual granularity on canvas.
**Warning signs:** canvas-sync-errors.jsonl shows "storyboard node requires shot_type" entries after p09.

### Pitfall 6: Runtime LLM Routing Violates INFRA-04 (PITFALL X-5)
**What goes wrong:** Per-transition routing decisions fan out as parallel GLM calls → HTTP 429 storm → pipeline stall masquerading as transition engine failure.
**Why it happens:** "Different engine = different rate limit" is intuitive but wrong: routing decisions are LLM-made, so even non-GLM engines (Wan-FLF2V local render) carry GLM overhead.
**How to avoid:** All routing rules are **declarative** (markdown table in transition-engine-routing.md), NOT runtime LLM decisions. Subagent reads the table at goal-construction time and routes deterministically. TRANS-10 (runtime LLM routing) is explicitly deferred.
**Warning signs:** HTTP 429 retry logs during p11 video render phase.

## Code Examples

### TRANS-01: E-Konte Layer 5 Schema Extension (e-konte-format.md)
```yaml
# Source: e-konte-format.md:116-130 (existing Layer 5 schema, verified 2026-07-09)
# AFTER Phase 74 extension:

layer_5_timing:
  duration_sec: 3.2
  frame_count: 77          # 24fps × 3.2s = 77 frames
  fps: 24
  # ── v14.0 TRANS-01 extension (12-value enum + structured next_shot_link) ──
  transition_method: "match_cut_shared_object"  # 12-value enum (was: cut_transition_type 4-value)
  visual_hook: "red mug on desk → next shot red car passing window"  # str | None
  camera_continuity: "match_cut_on_motion"  # 6-value enum
  # ── v14.0 TRANS-02 structured migration (was: next_shot_link: "shot_02") ──
  next_shot_link:
    shot_id: "ep01_shot_008"
    transition_method: "match_cut_shared_object"  # mirrors layer_5.transition_method
    visual_hook: "red mug → red car"
    camera_continuity: "match_cut_on_motion"
    generation_path: null  # filled by generation layer (p11) or operator
```

### TRANS-02: Backward-Compat Reader (transition_schema.py NEW module)
```python
# Source: DUB-02 validate_tts_engine_division precedent (dub_validators.py)
# Source: FORM-01 validate_form_factor_invariant precedent (store.py:111-140)
from __future__ import annotations

from typing import Any, Literal

# TRANS-01: 12-value enum (REQUIREMENTS.md line 41)
TRANSITION_METHOD_VALUES = Literal[
    "hard_cut", "dissolve", "wipe", "fade",
    "match_cut_shared_object", "match_cut_shared_landscape",
    "motion_vector_match", "color_match",
    "j_cut", "l_cut", "whip_pan", "none",
]
# TRANS-01: 6-value enum (REQUIREMENTS.md line 41)
CAMERA_CONTINUITY_VALUES = Literal[
    "pan_to", "zoom_to", "dolly_through",
    "whip_pan", "match_cut_on_motion", "none",
]

# Allow Python-level set for runtime validation (Literal is type-hint only)
_TRANSITION_METHOD_SET = frozenset({
    "hard_cut", "dissolve", "wipe", "fade",
    "match_cut_shared_object", "match_cut_shared_landscape",
    "motion_vector_match", "color_match",
    "j_cut", "l_cut", "whip_pan", "none",
})
_CAMERA_CONTINUITY_SET = frozenset({
    "pan_to", "zoom_to", "dolly_through",
    "whip_pan", "match_cut_on_motion", "none",
})


def load_next_shot_link(value: Any) -> dict:
    """TRANS-02 backward-compat reader.

    Coerces legacy string form to structured default. Validates dict form
    against TRANS-01 enum. Mirrors FORM-01 form_factor __post_init__ pattern
    (store.py:111-140) + DUB-02 validate_tts_engine_division pattern
    (dub_validators.py).

    Examples:
        >>> load_next_shot_link("shot_02")
        {'shot_id': 'shot_02', 'transition_method': 'hard_cut',
         'visual_hook': None, 'camera_continuity': 'none', 'generation_path': None}

        >>> load_next_shot_link({"shot_id": "s3", "transition_method": "dissolve"})
        {'shot_id': 's3', 'transition_method': 'dissolve',
         'visual_hook': None, 'camera_continuity': 'none', 'generation_path': None}
    """
    if isinstance(value, str):
        return {
            "shot_id": value,
            "transition_method": "hard_cut",
            "visual_hook": None,
            "camera_continuity": "none",
            "generation_path": None,
        }
    if isinstance(value, dict):
        tm = value.get("transition_method", "hard_cut")
        if tm not in _TRANSITION_METHOD_SET:
            raise ValueError(
                f"invalid transition_method: {tm!r}; must be one of "
                f"{sorted(_TRANSITION_METHOD_SET)}"
            )
        cc = value.get("camera_continuity", "none")
        if cc not in _CAMERA_CONTINUITY_SET:
            raise ValueError(
                f"invalid camera_continuity: {cc!r}; must be one of "
                f"{sorted(_CAMERA_CONTINUITY_SET)}"
            )
        return {
            "shot_id": value.get("shot_id"),
            "transition_method": tm,
            "visual_hook": value.get("visual_hook"),
            "camera_continuity": cc,
            "generation_path": value.get("generation_path"),
        }
    raise TypeError(
        f"next_shot_link must be str (legacy) or dict (v14.0+), got {type(value).__name__}"
    )
```

### TRANS-03: Asset-Bus Slot Registration (asset_bus.py)
```python
# Source: asset_bus.py:223-236 (Phase 36-02 precedent — shot-list + e-konte-sheets siblings)
# Insert AFTER e-konte-sheets (keeps p09 outputs grouped):

    # ── Phase 74 additions — transition design slot (TRANS-03) ──────────
    # Phase 74 registers this slot so p09_shot_breakdown (cinematographer)
    # can write transition design, and p13_delivery (editor) can read it
    # for post-production execution. JSON format (envelope-wrapped, atomic
    # write). Per-plan asset-bus extension (D-36-05): PRESERVES existing
    # slots byte-equivalent — only appends.
    "transition-design": {
        "file": "transition-design.json",
        "format": "json",
        "description": "Transition design (creative intent from cinematographer "
                       "Step 9; consumed by editor Step 13 for post-production "
                       "execution). Per-shot transition_method (12-enum) + "
                       "visual_hook + camera_continuity.",
        "writer_phase": "p09_shot_breakdown",
        "reader_phases": ["p13_delivery"],
    },
```

### TRANS-06: Per-Transition Routing Table (transition-engine-routing.md)
```markdown
## Per-Transition Engine Routing (TRANS-06)

| transition_method | Primary Engine | Fallback | LTX-2.3 FLF Evaluation |
|-------------------|----------------|----------|------------------------|
| `hard_cut` | ffmpeg (no generation — direct concat in P12) | — | N/A (no generation) |
| `j_cut` | ffmpeg (audio lead 0.3-0.8s before visual cut) | — | N/A |
| `l_cut` | ffmpeg (visual lead 0.2-0.5s before audio cut) | — | N/A |
| `dissolve` | ffmpeg xfade=fade (12-24 frames @24fps) | — | LTX native time-based exists but adds VRAM cost; ffmpeg wins |
| `wipe` | ffmpeg xfade=wipeleft/wiperight (24-36 frames) | — | N/A |
| `fade` | ffmpeg xfade=fade (24-48 frames, scene boundaries) | — | N/A |
| `match_cut_shared_object` | Wan2.2 14B FLF2V (local, ~21GB VRAM) | ffmpeg manual cut on action | LTX-2.3 FLF viable BUT no identity continuity from previous shot (drift risk per PITFALL T-1) |
| `match_cut_shared_landscape` | Hailuo 02 i2v Pro (cloud, opt-in MINIMAX_API_KEY) | Vidu keyframe-to-video (cloud, opt-in VIDU_API_KEY) → ffmpeg manual cut | LTX-2.3 FLF viable for landscape match; same drift caveat |
| `motion_vector_match` | Hailuo / Vidu (motion-vector generation is cloud-native strength) | ffmpeg motion-based cut | LTX-2.3 not trained for motion-vector matching |
| `color_match` | ffmpeg color adjustment (post-production) | — | N/A |
| `whip_pan` | ffmpeg whippan simulation + operator manual override | — | AI unreliable per TRANS-08 deferred; v15+ candidate |
| `none` | ffmpeg (direct concat, no transition) | — | N/A |

### LTX-2.3 FLF + ICLoRA Combined Workflow Note (PITFALL T-1)

LTX-2.3 has TWO ORTHOGONAL capabilities — they are SEPARATE workflows with no
merged turnkey option today:
- **ICLoRA** (`ltx/msr` LiconMSR): identity preservation via ref1-ref5 multi-reference
- **FLF** (`ltx/fflf` + `ltx/singularityFFLF`): first/last frame conditioning

Per-transition routing MUST state the trade-off explicitly:
- IF transition needs identity continuity → MSR + post-production match-cut
- IF transition needs frame-interpolation → FLF + accept identity drift risk

TRANS-07 validates whether a combined workflow is production-ready. Until then,
this routing table treats LTX-2.3 FLF as a **viable but drift-risky** option,
NOT the default for identity-critical transitions.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `cut_transition_type` 4-value enum (hard_cut/dissolve/wipe/fade) | `transition_method` 12-value enum (+ match_cut_shared_object/match_cut_shared_landscape/motion_vector_match/color_match/j_cut/l_cut/whip_pan/none) | v14.0 Phase 74 | Richer creative vocabulary; aligns with industry-standard taxonomy (StudioBinder, Adobe per FEATURES research) |
| `next_shot_link: "shot_02"` (string id) | `next_shot_link: {shot_id, transition_method, visual_hook, camera_continuity, generation_path}` (structured object) | v14.0 Phase 74 | Generation routing signal embedded in shot chain; backward-compat reader preserves existing episodes |
| Transition design split between cinematographer + editor (blurry boundary) | Field-level ownership split (TRANS-04): creative → cinematographer Step 9; execution → editor Step 13 | v14.0 Phase 74 | FOUND-08 preserved (no new expert); architectural gap resolved via field boundaries |
| ffmpeg-only post-production transitions | 3-layer routing: ffmpeg (simple) / Wan2.2 FLF2V (local match-cut) / Hailuo+Vidu (cloud Chinese-content backup) | v14.0 Phase 74 | Match-cut transitions now have generation-time option; simple transitions stay ffmpeg (cost-efficient) |

**Deprecated/outdated:**
- `cut_transition_type` (4-value): subsumed by `transition_method` (12-value). Old field name preserved as alias in backward-compat reader for legacy episode JSON.
- LTX-MSR as "FLF-incapable" assumption: CORRECTED — LTX-2.3 has separate FLF workflow (`ltx/fflf`), just no combined ICLoRA+FLF turnkey option (PITFALL T-1).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | transition_design reuses `storyboard` canvas_type (zero frontend change) | Standard Stack; Pattern 2; Pitfall 1 | LOW — if frontend rejects storyboard nodes without `shot_type`, fallback to `script` summary node (looser schema). Both paths verified against canvasAssetSchema.ts. |
| A2 | MAX_CONSTRAINTS=7 budget can absorb 1 transition constraint via consolidation with form_factor | Pitfall 2 | LOW — alternative is splitting p09 _INSTRUCTION into 2 goal builders, but that breaks CF-36-03 single-delegate pattern. Consolidation is semantically valid (both are Layer 5 fields). |
| A3 | Wan2.2 14B FLF2V ComfyUI node is already available in comfyui-primary container | Standard Stack | MEDIUM — if not installed, operator-action handoff to install. STACK.md claims it's "already in stack per STACK.md recommendation" but RESEARCH could not verify the actual container state. XCUT-04b documents this as operator-action. |
| A4 | Hailuo 02 + Vidu API pricing ($0.056/sec) is current | Standard Stack; transition-engine-routing.md | LOW — pricing is operator concern (opt-in); even if stale, routing rule still works. Operator-action handoff per XCUT-04b. |
| A5 | Editor SKILL.md "Step 13" in TRANS-04 CONTEXT refers to pipeline phase p13_delivery, not editor Workflow Step 13 | Pitfall 4 | LOW — verified via p13_delivery.py:89 ("editor performs final-cut + render"). Both interpretations point to the same code path. |

## Open Questions

1. **Should transition-design.md live under cinematographer/references/ or kais-movie-pipeline/references/?**
   - What we know: CONTEXT.md `canonical_refs` lists `cinematographer/references/e-konte-format.md` as the Layer 5 extension insertion point. transition-design.md is the taxonomy companion to e-konte-format.md.
   - What's unclear: whether the 12-type taxonomy is cinematographer-specific (creative intent) or pipeline-wide (consumed by editor + visual_executor).
   - Recommendation: Place under `cinematographer/references/` — the taxonomy is creative-intent-primary (editor consumes via transition_design.json asset, not by reading the ref directly). transition-engine-routing.md goes under `kais-movie-pipeline/references/` (pipeline-wide routing consumed by P11/P12).

2. **Should TRANS-07 validation report be authored as a template (operator runs shots) or with placeholder content (researcher fills in setup + operator adds results)?**
   - What we know: CONTEXT.md says "Operator runs the actual validation shots; this phase produces the report TEMPLATE + setup instructions."
   - What's unclear: depth of the template — bare skeleton vs detailed setup with placeholders.
   - Recommendation: Detailed setup (ComfyUI node graph + LiconMSR + LTXVConditioning + SamplerCustomAdvanced per community reports) with explicit "operator fills in results" placeholders. This maximizes operator value while staying within research-scope.

## Environment Availability

> Phase 74 has external dependencies for the generation layer (Wan2.2 / Hailuo / Vidu). The documentation + schema layer has zero external dependencies.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| ffmpeg (xfade filter) | TRANS-06 post-production fallback (dissolve/wipe/fade/J-cut/L-cut/color_match/whip_pan) | ✓ | 6.1.1-3ubuntu5 | — (mandatory for v14.0; already in Docker stack) |
| Pydantic | TRANS-01/02 schema enforcement | ✓ | 2.13.4 | — (already pinned in pyproject.toml) |
| httpx | TRANS-06 Hailuo/Vidu REST clients (future templates, NOT v14.0 deliverable) | ✓ | 0.28.1 | — (already pinned; cloud engines are opt-in via XCUT-04b) |
| Wan2.2 14B FLF2V ComfyUI node | TRANS-06 local match-cut generation (opt-in) | [ASSUMED] | (per STACK.md "already in stack") | ffmpeg manual cut on action (post-production fallback) |
| Hailuo 02 i2v Pro API | TRANS-06 cloud match-cut backup (opt-in) | ✗ | — | ffmpeg fallback (operator hasn't provisioned API key; documented as XCUT-04b handoff) |
| Vidu keyframe-to-video API | TRANS-06 cloud Chinese-content backup (opt-in) | ✗ | — | ffmpeg fallback (operator hasn't provisioned API key; documented as XCUT-04b handoff) |
| LTX-2.3 FLF + ICLoRA combined workflow | TRANS-07 validation (research-scope) | [ASSUMED] | (ComfyUI custom node graph per community reports) | Validation report documents setup; operator executes |

**Missing dependencies with no fallback:** None for v14.0 mandatory scope. All cloud engines + LTX-FLF+ICLoRA validation are opt-in (XCUT-04b / TRANS-07 research-scope).

**Missing dependencies with fallback:** Hailuo/Vidu API keys → ffmpeg post-production fallback (documented in transition-engine-routing.md). Wan2.2 FLF2V → ffmpeg manual cut on action (fallback).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 + pytest-timeout 2.4.0 (already pinned per pyproject.toml:261) |
| Config file | kais-hermes-skills: `skills/kais-movie-pipeline/pyproject.toml` (if exists) OR repo-root `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `cd /data/workspace/kais-hermes-skills && python -m pytest skills/kais-movie-pipeline/tests/test_p09_unit.py skills/kais-movie-pipeline/tests/test_transition_migration.py -x --timeout=30` |
| Full suite command | `cd /data/workspace/kais-hermes-skills && python -m pytest skills/kais-movie-pipeline/tests/ plugins/pipeline_state/tests/ -x --timeout=60` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TRANS-01 | E-Konte Layer 5 schema accepts 12-value transition_method + 6-value camera_continuity; rejects invalid values | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_transition_migration.py::test_transition_method_enum_valid -x` | ❌ Wave 0 |
| TRANS-01 | Invalid transition_method raises ValueError | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_transition_migration.py::test_transition_method_enum_invalid -x` | ❌ Wave 0 |
| TRANS-02 | String next_shot_link coerces to structured default | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_transition_migration.py::test_load_next_shot_link_string -x` | ❌ Wave 0 |
| TRANS-02 | Dict next_shot_link validates against schema | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_transition_migration.py::test_load_next_shot_link_dict -x` | ❌ Wave 0 |
| TRANS-02 | Legacy episode JSON loads cleanly (round-trip) | unit | `python -m pytest skills/kais-movie-pipeline/tests/test_transition_migration.py::test_legacy_episode_loads -x` | ❌ Wave 0 |
| TRANS-03 | ASSET_SCHEMA contains "transition-design" slot | unit | `python -m pytest plugins/pipeline_state/tests/test_asset_bus_phase35_slots.py::test_transition_design_slot_registered -x` | ❌ Wave 0 (extend existing test file) |
| TRANS-03 | Canvas sync _PHASE_OUTPUT_MAP["p09"] contains transition_design | unit | `python -m pytest plugins/kais_aigc/tests/test_canvas_sync.py::test_p09_phase_output_map_has_transition -x` | ❌ Wave 0 |
| TRANS-04 | Cinematographer SKILL.md Step 9 references transition_method/visual_hook/camera_continuity | smoke (grep) | `bash .planning/phases/74-transition/74-smoke.sh` (assertion: grep transition_method cinematographer/SKILL.md returns ≥1) | ❌ Wave 0 |
| TRANS-04 | Editor SKILL.md references cut_duration_frames/dissolve_curve/match_cut_alignment_point | smoke (grep) | `bash .planning/phases/74-transition/74-smoke.sh` (assertion: grep cut_duration_frames editor/SKILL.md returns ≥1) | ❌ Wave 0 |
| TRANS-05 | references/transition-design.md exists with 12-type sections | smoke (file + grep) | `bash .planning/phases/74-transition/74-smoke.sh` (assertion: file exists + grep "match_cut_shared_object" returns ≥1) | ❌ Wave 0 |
| TRANS-06 | references/transition-engine-routing.md exists with routing table | smoke (file + grep) | `bash .planning/phases/74-transition/74-smoke.sh` (assertion: file exists + grep "Wan2.2" + "ffmpeg xfade" return ≥1 each) | ❌ Wave 0 |
| TRANS-07 | references/ltx-flf-iclora-validation.md exists with template structure | smoke (file + grep) | `bash .planning/phases/74-transition/74-smoke.sh` (assertion: file exists + grep "ICLoRA" + "FLF" return ≥1 each) | ❌ Wave 0 |
| XCUT-02 | p09 goal includes _TRANSITION_DESIGN_INSTRUCTION keyword | unit (goal-content) | `python -m pytest skills/kais-movie-pipeline/tests/test_p09_unit.py::test_p09_goal_includes_transition_design_instruction -x` | ❌ Wave 0 (extend existing test file) |
| XCUT-02 | p13 goal includes editor post-production execution fields | unit (goal-content) | `python -m pytest skills/kais-movie-pipeline/tests/test_p13_unit.py::test_p13_goal_includes_transition_execution -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd /data/workspace/kais-hermes-skills && python -m pytest skills/kais-movie-pipeline/tests/test_p09_unit.py skills/kais-movie-pipeline/tests/test_transition_migration.py plugins/pipeline_state/tests/test_asset_bus_phase35_slots.py -x --timeout=30` (< 10s)
- **Per wave merge:** `cd /data/workspace/kais-hermes-skills && python -m pytest skills/kais-movie-pipeline/tests/ plugins/pipeline_state/tests/ plugins/kais_aigc/tests/ -x --timeout=60` (< 60s)
- **Phase gate:** Full suite green before `/gsd:verify-work` + `bash .planning/phases/74-transition/74-smoke.sh` exits 0

### Wave 0 Gaps
- [ ] `skills/kais-movie-pipeline/tests/test_transition_migration.py` — covers TRANS-01 enum validation + TRANS-02 backward-compat reader (5+ test functions per Test Map)
- [ ] `skills/kais-movie-pipeline/pipeline/phases/transition_schema.py` — new module with `load_next_shot_link` + `TRANSITION_METHOD_VALUES` Literal + validation sets
- [ ] Extend `plugins/pipeline_state/tests/test_asset_bus_phase35_slots.py` — add `test_transition_design_slot_registered` (follows existing `test_slot_count_grew` pattern at line 160-167)
- [ ] Extend `skills/kais-movie-pipeline/tests/test_p09_unit.py` — add `test_p09_goal_includes_transition_design_instruction` (follows existing `_make_delegate_spy` pattern at line 56-63)
- [ ] `.planning/phases/74-transition/74-smoke.sh` — bash smoke runner mirroring 70-smoke.sh skeleton (15+ assertions per Test Map)

*(Framework install: none — pytest already pinned per pyproject.toml:261)*

## Security Domain

> Phase 74 is documentation + schema + asset-bus slot addition. `security_enforcement` is enabled (absent in config.json), but this phase has no auth/session/access/crypto/input-validation surfaces.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — no authentication surfaces in this phase |
| V3 Session Management | no | N/A — no session state |
| V4 Access Control | no | N/A — no privileged operations |
| V5 Input Validation | yes | Pydantic Literal strict enum (TRANSITION_METHOD_VALUES + CAMERA_CONTINUITY_VALUES) — rejects invalid transition_method/camera_continuity at runtime. Mirrors FORM-01 form_factor __post_init__ validator. |
| V6 Cryptography | no | N/A — no crypto operations |

### Known Threat Patterns for kais-movie-pipeline transition schema

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Invalid transition_method value in episode JSON (typo / tampering) | Tampering | Pydantic Literal enum + `load_next_shot_link()` ValueError on invalid value (TRANS-01 mitigation) |
| Legacy string next_shot_link silently coerced (data integrity) | Information Disclosure | Backward-compat reader coerces to documented defaults; no silent data loss — `transition_method: "hard_cut"` is the documented pre-v14.0 behavior |
| Cloud API key leakage (Hailuo/Vidu) | Information Disclosure | API keys env vars only (MINIMAX_API_KEY / VIDU_API_KEY); never logged; documented as operator-action handoff (XCUT-04b) |
| Canvas schema injection (malicious transition_design payload) | Tampering | Frontend zod storyboard schema validates structure; canvas save-v2 rejects invalid nodes (canvasAssetSchema.ts:127-151) |

## Sources

### Primary (HIGH confidence — verified against live code 2026-07-09)
- `kais-hermes-skills/skills/movie-experts/cinematographer/SKILL.md` — Step 9 procedure (line 189-208), E-Konte Layer 5 schema reference, Form Factor Adaptation section
- `kais-hermes-skills/skills/movie-experts/cinematographer/references/e-konte-format.md` — Layer 5 schema (line 116-130), Output Schema (line 271-342), next_shot_link string form (line 126 + 332)
- `kais-hermes-skills/skills/movie-experts/editor/SKILL.md` — FxRxT matrix, Transition Design Workflow step 7 (line 197), Step 13 Output EDL (line 203), Transition Parameters (line 126-131)
- `kais-hermes-skills/plugins/pipeline_state/asset_bus.py` — ASSET_SCHEMA dict (line 40-463, 31 existing slots), AssetBus.write/read API, Phase 36-02 precedent for slot addition
- `kais-hermes-skills/plugins/kais_aigc/canvas_sync.py` — _PHASE_OUTPUT_MAP (line 1676-1764), _PHASE_TYPE_MAP (line 1157-1175), CanvasSyncSubscriber (line 700-900), sync_phase_result ad-hoc API (line 2549-2645)
- `kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p09_shot_breakdown.py` — existing _INSTRUCTION constants (line 51-234), GoalBuilder chain (line 352-416), MAX_CONSTRAINTS budget evidence (6 current constraints)
- `kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p13_delivery.py` — editor final-cut role (line 89), 3-expert collaboration pattern (colorist + compliance_gate + editor)
- `kais-hermes-skills/skills/kais-movie-pipeline/pipeline/phases/p12_composition.py` — ffmpeg execution site (line 113-126), audio_pipeline + editor collaboration
- `kais-aigc-platform/src/lib/canvasAssetSchema.ts` — 5 node types (audio/video/asset/storyboard/script), storyboard schema requires shot_id+shot_type+duration_sec
- `hermes-agent/.planning/research/v14-4track-upgrade/SUMMARY.md` — 6 reconciled conflicts (esp. #1 LTX-FLF orthogonality, #4 cinematographer vs editor ownership)
- `hermes-agent/.planning/research/v14-4track-upgrade/PITFALLS.md` — T-1 through T-8 transition pitfalls + X-5 INFRA-04 serial constraint
- `hermes-agent/.planning/research/v14-4track-upgrade/STACK.md` — Wan2.2 FLF2V + Hailuo + Vidu engine survey
- `hermes-agent/.planning/research/v14-4track-upgrade/ARCHITECTURE.md` — 3-layer model (creative + data + generation)
- `hermes-agent/.planning/phases/73-img/73-PATTERNS.md` — XCUT-02 _INSTRUCTION injection 3-phase precedent (FORM/DUB/IMG)
- Local probes 2026-07-09: `ffmpeg -version` (6.1.1-3ubuntu5), `ffmpeg -h filter=xfade` (supported), `grep next_shot_link kais-hermes-skills --include="*.py"` (zero hits — documentation contract only)

### Secondary (MEDIUM confidence)
- [comfy.org Wan2.2 14B FLF2V workflow](https://comfy.org/workflows/video_wan2_2_14B_flf2v-7016f027bcf1/) — official ComfyUI workflow
- [GegenDenTag HuggingFace Wan2.2 FLF workflow JSON](https://huggingface.co/GegenDenTag/comfyui-wan-video-2.2-t2v-first-last-frame-workflow) — ready-to-use JSON
- [MiniMax Hailuo 02 platform docs](https://platform.minimax.io/docs/guides/video-generation) — REST API reference
- [Aliyun Vidu keyframe-to-video](https://help.aliyun.com/en/model-studio/vidu-keyframe-to-video-api-reference) — REST API reference
- [StudioBinder: Types of Editing Transitions](https://www.studiobinder.com/blog/types-of-editing-transitions-in-film/) — 12-type taxonomy source
- [LTX-2.3 IC-LoRA docs](https://docs.ltx.video/open-source-model/usage-guides/ic-lo-ra) — ICLoRA vs FLF orthogonality

### Tertiary (LOW confidence — flagged for validation)
- [LTX 2.3 First and Last Frame ComfyUI Guide (ltx23.org)](https://ltx23.org/blog/ltx-23-first-last-frame-comfyui) — FLF2V implementation details
- [LTX-2.3 ID-LoRA with FLF Reddit](https://www.reddit.com/r/StableDiffusion/comments/1t71x0r/ltx_23_idlora_with_firstlast_frame/) — community custom workflow for ICLoRA + FLF2V combination

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new packages; ffmpeg + Pydantic + httpx all verified available
- Architecture: HIGH — all claims verified against live kais-hermes-skills code at HEAD 7904bd0 (asset_bus.py, canvas_sync.py, p09_shot_breakdown.py, p13_delivery.py, e-konte-format.md, editor SKILL.md)
- Pitfalls: HIGH — cross-verified against SUMMARY reconciled conflicts + PITFALLS T-1 through T-8 + STATE.md decision log (Phase 71/72/73 precedent)
- Validation: HIGH — test framework + patterns verified against existing test files (test_p09_unit.py, test_asset_bus_phase35_slots.py)

**Research date:** 2026-07-09
**Valid until:** 2026-08-09 (30 days — stable documentation/schema phase; no fast-moving dependencies)
