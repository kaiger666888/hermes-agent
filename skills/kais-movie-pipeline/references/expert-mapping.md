# Expert Mapping — 13 Phase ↔ 15 Movie-Expert Mapping

**Source:** `_shared/v86-pipeline-mapping.md` §"The 13-Step V8.6 Pipeline → expert_id Mapping" + `movie-experts/README.md` §"Active Expert Inventory" Bucket 1.
**Copyright:** Fair Use — phase ↔ expert mapping is factual integration architecture.
**Last-verified:** 2026-06-25

---

## Summary

This document maps each of the 13 V8.6 pipeline phases to its primary + collaborating movie-experts. It answers "which movie-expert is invoked at each step, and what they produce" for the `kais-movie-pipeline` orchestration skill. Expert IDs sourced from `_shared/v86-pipeline-mapping.md`; expert roles from `movie-experts/README.md`.

This is **skeleton form** (per ROADMAP SC#5). Phase 36 refines with actual port experience (delegate_task `goal` templates, asset-bus slot I/O per expert invocation).

---

## 13 Phase ↔ 15 Expert Mapping

| Phase ID | V8.6 Step | Primary Expert(s) | Collaborating Experts | Phase 35/36 Scope | Reference |
|----------|-----------|--------------------|-----------------------|--------------------|-----------|
| `p01_hook_topic` | Step 1 (atomic §1) | `hook_retention` | — | **Phase 35** | v86-pipeline-mapping.md row 1 |
| `p02_outline` | Step 2 (atomic §2) | `creative_source` + `screenplay` | — | **Phase 35** | row 2 |
| `p03_script_audit` | Step 3 (atomic §3) | `screenplay` + `script_auditor` | — | **Phase 35** | row 3 |
| `p04_character_design` | Step 4 | `character_designer` + `visual_executor` (drawer) | — | Phase 36 | row 4 |
| `p05_scene_design` | Step 5 | `cinematographer` + `style_genome` + `visual_executor` (drawer) | — | Phase 36 | row 5 |
| `p06_spatio_temporal_script` | Step 6 (atomic §5) | `screenplay` + `cinematographer` + `script_auditor` | — | Phase 36 | row 6 |
| `p07_visual_seed` | Step 7 (atomic §4) | `visual_executor` + `prompt_injector` + `style_genome` + `colorist` | — | Phase 36 | row 7 |
| `p07b_audio_skeleton` | Step 7B | `audio_pipeline` (voicer + composer + foley) | — | Phase 36 | row 8 |
| `p08_shot_pacing` | Step 8 | `cinematographer` + `editor` | — | Phase 36 | row 9 |
| `p09_continuity_check` | Step 9 | `continuity_auditor` | — | Phase 36 | row 10 |
| `p10_video_gen` | Step 10 | (dreamina CLI — no expert_id call) | `visual_executor` (animator 监督) | Phase 36 | row 11 |
| `p11_audio_master` | Step 11 (atomic §6) | `audio_pipeline` (6 sub-steps) | — | Phase 36 | row 12 |
| `p12_p13_delivery` | Step 12-13 | TBD | — | Phase 36 | row 13 |

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

## See Also

- [`pipeline-dag.md`](./pipeline-dag.md) — 13-step DAG (where each phase sits)
- [`review-gates.md`](./review-gates.md) — gate timing per phase
- [`asset-bus-schema.md`](./asset-bus-schema.md) — slot I/O contracts per phase
- `_shared/v86-pipeline-mapping.md` — canonical source ref (single source of truth)
- `movie-experts/README.md` — full 15-expert inventory (Bucket 1 active DAG)
