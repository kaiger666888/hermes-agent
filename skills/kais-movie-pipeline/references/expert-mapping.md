# Expert Mapping — 13 Phase ↔ 15 Movie-Expert Mapping

**Source:** `_shared/v86-pipeline-mapping.md` §"The 13-Step V8.6 Pipeline → expert_id Mapping" + `movie-experts/README.md` §"Active Expert Inventory" Bucket 1.
**Copyright:** Fair Use — phase ↔ expert mapping is factual integration architecture.
**Last-verified:** 2026-06-26 (Phase 36-05 Wave 2 refinement — per-phase module paths + goal templates added)

---

## Summary

This document maps each of the 13 V8.6 pipeline phases to its primary + collaborating movie-experts. It answers "which movie-expert is invoked at each step, and what they produce" for the `kais-movie-pipeline` orchestration skill. Expert IDs sourced from `_shared/v86-pipeline-mapping.md`; expert roles from `movie-experts/README.md`.

**Phase 36-05 Wave 2 refinement:** The Scope column now references actual phase module file paths (Phase 36 Complete) + a new §"Per-Phase delegate_task Goal Templates" section documents the verb + skill_view shape per phase.

---

## 13 Phase ↔ 15 Expert Mapping

| Phase ID | V8.6 Step | Primary Expert(s) | Collaborating Experts | Phase 35/36 Scope | Module File | Reference |
|----------|-----------|--------------------|-----------------------|--------------------|-------------|-----------|
| `p01_hook_topic` | Step 1 (atomic §1) | `hook_retention` | — | **Phase 35 Complete** | `pipeline/phases/p01_hook_topic.py` | row 1 |
| `p02_outline` | Step 2 (atomic §2) | `creative_source` + `screenplay` | — | **Phase 35 Complete** | `pipeline/phases/p02_outline.py` | row 2 |
| `p03_script_audit` | Step 3 (atomic §3) | `screenplay` + `script_auditor` | — | **Phase 35 Complete** | `pipeline/phases/p03_script_audit.py` | row 3 |
| `p04_character_design` | Step 4 | `character_designer` | `visual_executor` (drawer) | **Phase 36 Complete (36-01)** | `pipeline/phases/p04_character_design.py` | row 4 |
| `p05_pain_discovery` | Step 5 | `creative_source` | `theory_critic` | **Phase 36 Complete (36-01)** | `pipeline/phases/p05_pain_discovery.py` | row 5 (repurposed — V8.6 Step 5 "scene design" is split: pain discovery stays here, scene design moves to p07) |
| `p06_spatio_temporal_script` | Step 6 (atomic §5) | `screenplay` | `cinematographer` + `script_auditor` | **Phase 36 Complete (36-01)** | `pipeline/phases/p06_spatio_temporal_script.py` | row 6 |
| `p07_scene_generation` | Step 7 (atomic §4) | `visual_executor` | `prompt_injector` + `style_genome` + `colorist` | **Phase 36 Complete (36-02)** | `pipeline/phases/p07_scene_generation.py` | row 7 |
| `p08_scene_selection` | Step 8 | `cinematographer` | `editor` | **Phase 36 Complete (36-02)** | `pipeline/phases/p08_scene_selection.py` | row 9 (V8.6 Step 7B audio skeleton is collapsed into p10; we keep 13-module shape per CONTEXT D-36-02) |
| `p09_shot_breakdown` | Step 9 | `cinematographer` | `continuity_auditor` | **Phase 36 Complete (36-02)** | `pipeline/phases/p09_shot_breakdown.py` | row 10 |
| `p10_voice` | Step 7B + Step 10 partial | `audio_pipeline` (voicer sub-step) | — | **Phase 36 Complete (36-03)** | `pipeline/phases/p10_voice.py` | row 8 (V8.6 Step 7B audio skeleton lives here) |
| `p11_video_render` | Step 10 + Step 11 video half | `visual_executor` (animator) | `audio_pipeline` (lip_sync) | **Phase 36 Complete (36-03)** | `pipeline/phases/p11_video_render.py` | row 11 (D-36-08 parallel_shots exercised here) |
| `p12_composition` | Step 11 audio half + Step 12 (atomic §6) | `audio_pipeline` (6 sub-steps) | `editor` | **Phase 36 Complete (36-04)** | `pipeline/phases/p12_composition.py` | row 12 |
| `p13_delivery` | Step 13 | `colorist` | `compliance_gate` + `editor` | **Phase 36 Complete (36-04)** | `pipeline/phases/p13_delivery.py` | row 13 (Gate 8 final-delivery) |

**Cross-cutting / on-demand experts** (not fixed to a phase — invoked per project need):
- `theory_critic` — consultative, creator-pulled from any Step (typical after Step 2 / 6 / 9)
- `compliance_gate` — fires at 4 gates (Step 1 / 3 / 6 / 11 后)
- `production` — FUTURE-09 deferred (not in V8.6 mainline DAG)
- `documentary_maker` / `animation_studio` — corpus verticals, parallel to linear pipeline

---

## 15 Active Movie-Experts

> Sourced from `movie-experts/README.md` §"Bucket 1 — Active DAG pipeline-roles (15)".

| expert_id | Chinese Name | Role (one-line) |
|-----------|--------------|-----------------|
| `creative_source` | 创意源头专家 | Story Kernel mining from 6 social strata (L0 root) |
| `style_genome` | 风格基因专家 | 5D director/genre style encoding + blend protocol + cross-module alignment |
| `screenplay` | 剧本专家 | Scene-level script + dialogue + emotion_curve design (HOOK-09 schema) |
| `script_auditor` | 剧本审计专家 | 5-dim quantitative script audit (narrative / emotion / hook / character / completion-forecast) |
| `character_designer` | 角色设计专家 | Character Bible 2.0 authoring with 4D-Anchor + layered STYLE_PREFIX + consistency stress test |
| `cinematographer` | 镜头专家 | Shot intent layer (shot scale + composition + axis + camera move) + vertical 9:16 + composition_lock |
| `prompt_injector` | 提示注入专家 | AI-native node: visual_intent + style_genome + character_assets → model_prompts + consistency_context |
| `visual_executor` | 视觉执行专家 | Unified FLUX 2 image gen (drawer sub-step) + Hermes-catalog video gen (animator sub-step) |
| `continuity_auditor` | 连续性专家 | 4-dimension cross-shot audit (face/wardrobe/color/object) + eyeline match + 180° axis |
| `audio_pipeline` | 音频管线专家 | Unified 6-sub-step audio: voicer + lip_sync + composer + foley + mixer + spatial_audio |
| `editor` | 剪辑专家 | FxRxT editing matrix + Murch Rule of Six + 180° axis compliance |
| `colorist` | 色彩专家 | CxSxZ 28-combination color intent + LUT design + Bellantoni color psychology |
| `hook_retention` | 钩子与留存专家 | 3-second hook design + 付费卡点 placement + per-platform 爆款公式 + marker schema |
| `compliance_gate` | 合规与宣发专家 | CN content-rules gate + AIGC labeling + per-platform distribution + 爆款 vs 红线 review |
| `theory_critic` | 理论批评专家 | 电影理论 (形式/写实/精神分析) + 作者研究 + 电影史方法 + 学术批评方法 |

---

## Invocation Pattern

Each phase module (`p01_hook_topic.py` etc.) invokes the assigned expert via `delegate_task`. Per Phase 35 CONTEXT D-35-07 (delegate_task invocation contract):

- **Synchronous** (`background=false`) — runner blocks on each phase
- **`goal`** = complete, self-contained instruction derived from the expert's SKILL.md `## When to use this skill` section; instructs subagent to first call `skill_view(name="<expert_id>")` then apply the expert
- **`context`** = asset-bus inputs (JSON-serialized upstream slot values)
- **`toolsets`** = `["skills", "file"]` minimum (expert needs `skill_view` to load its own SKILL.md, and `file` for I/O if it mediates directly)
- **Return shape** — delegate_task returns a summary string; phase module instructs expert to emit JSON in a fenced block at end of summary, then parses it

Schema reference: `tools/delegate_tool.py`. Per Phase 35 PATTERNS.md, phase modules expose internal functions accepting injected dispatch callables for test mocking.

---

## Per-Phase delegate_task Goal Templates

> Added in Phase 36-05 Wave 2 (refinement spec). Each entry summarizes the `goal` string shape constructed by the phase module — the verb + skill_view mentions + output JSON shape. Sourced from Wave 1 SUMMARYs (36-01..36-04) + Phase 35 reference modules.

Every goal follows Pattern 2 (PATTERNS.md): **verb** ("Apply the X expert skill in a V8.6 §Y operation") → **skill_view mention** for every assigned expert → **upstream slot inputs** named + JSON-serialized → **output shape** specified ("Emit the final output as a single fenced JSON block...").

| Phase | Goal Template Summary (verb + skill_views + output shape) |
|-------|-------------------------------------------------------------|
| `p01_hook_topic` | "Apply the `hook_retention` expert skill in a V8.6 §1 atomic operation" → `skill_view(name='hook_retention')` → output `{topic_kernel, hook_design}` |
| `p02_outline` | "Apply the `creative_source` AND `screenplay` expert skills in a V8.6 §2 atomic operation" → `skill_view(name='creative_source')` + `skill_view(name='screenplay')` → output `{story_framework}` |
| `p03_script_audit` | "Apply the `screenplay` AND `script_auditor` expert skills in a V8.6 §3 atomic operation" → `skill_view(name='screenplay')` + `skill_view(name='script_auditor')` → output `{script_draft, audit_report}` |
| `p04_character_design` | "Apply the `character_designer` AND `visual_executor` expert skills in a V8.6 Step 4 atomic operation" → `skill_view(name='character_designer')` + `skill_view(name='visual_executor')` → output `{character_bible, character_assets}` (Character Bible 2.0 + L1-L4 manifest) |
| `p05_pain_discovery` | "Apply the `creative_source` AND `theory_critic` expert skills in a V8.6 Step 5 operation" → `skill_view(name='creative_source')` + `skill_view(name='theory_critic')` → output `{pain_points, escalation_ladder}` (L1-L6 strata + escalation) |
| `p06_spatio_temporal_script` | "Apply the `screenplay`, `cinematographer`, AND `script_auditor` expert skills in a V8.6 §5 atomic operation" → 3 skill_views → output `{spatio_temporal_script, final_audit}` (atomic §5 invariant — 3 experts, 1 delegate_task call) |
| `p07_scene_generation` | "Apply the `visual_executor`, `prompt_injector`, `style_genome`, AND `colorist` expert skills in a V8.6 §4 atomic operation" → 4 skill_views → output `{scene_images, style_vector, color_intent}` (atomic §4 invariant — 4 experts, 1 delegate_task call) |
| `p08_scene_selection` | "Apply the `cinematographer` AND `editor` expert skills in a V8.6 Step 8 operation" → 2 skill_views → output `{scene_selection, geometry_bed}` |
| `p09_shot_breakdown` | "Apply the `cinematographer` AND `continuity_auditor` expert skills in a V8.6 Step 9 operation" → 2 skill_views → output `{shot_list, e_konte_sheets}` (5-layer decomposition) |
| `p10_voice` | "Apply the `audio_pipeline` expert skill (voicer sub-step) in a V8.6 Step 7B operation" → `skill_view(name='audio_pipeline')` → output `{voice_clips, voice_timeline}` |
| `p11_video_render` | Per-shot goal: "Apply the `visual_executor` (animator) AND `audio_pipeline` (lip_sync) expert skills in a V8.6 Step 10 operation" → 2 skill_views per shot → aggregated output `{video_clips, lip_sync_reports}` (D-36-08 parallel fan-out, `parallel_shots` kwarg) |
| `p12_composition` | "Apply the `audio_pipeline` expert skill (6 sub-steps: composer + foley + mixer + spatial + lip_sync final + dialog cleanup) AND `editor` expert skill in a V8.6 §6 atomic operation" → `skill_view(name='audio_pipeline')` + `skill_view(name='editor')` → output `{master_timeline, audio_stems}` (atomic §6 invariant — 6 internal sub-steps, 1 delegate_task call) |
| `p13_delivery` | "Apply the `colorist`, `compliance_gate`, AND `editor` expert skills in a V8.6 Step 13 operation" → 3 skill_views → output `{master_mp4, delivery_package}` (Gate 8 final-delivery) |

**Anti-pattern reminder (D-35-07):** phase modules do NOT call `skill_view` in parent (orchestration) context. Each `skill_view(name='...')` mention lives INSIDE the goal string — the subagent executes it after `delegate_task` spawns. Calling skill_view in the parent would burn parent context (15 experts × 5-15KB = exhaustion across 13 phases).

---

## See Also

- [`pipeline-dag.md`](./pipeline-dag.md) — 13-step DAG (where each phase sits)
- [`review-gates.md`](./review-gates.md) — gate timing per phase
- [`asset-bus-schema.md`](./asset-bus-schema.md) — slot I/O contracts per phase
- `_shared/v86-pipeline-mapping.md` — canonical source ref (single source of truth)
- `movie-experts/README.md` — full 15-expert inventory (Bucket 1 active DAG)
