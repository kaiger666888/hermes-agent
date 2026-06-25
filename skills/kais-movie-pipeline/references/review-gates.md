# Review Gates — V8.6 8-Gate Per-Phase Mapping

**Source:** `_shared/v86-pipeline-mapping.md` §"V8.6 8-Gate Review Structure" (Phase 27 canonical ref); gate lifecycle semantics from `plugins/review_gates/gate.py` (Phase 34).
**Copyright:** Fair Use — gate trigger phase + reviewer role is factual integration architecture.
**Last-verified:** 2026-06-26 (Phase 36-05 Wave 2 refinement — all 8 gates mapped to actual module GATE_ID constants)

---

## Summary

This document specifies the **8 V8.6 review gates** and their per-phase mapping. It answers "which gates fire when, and what reviewer role / mode each uses" for the `kais-movie-pipeline` orchestration skill. Gate numbering, trigger phases, and reviewer composition sourced from `_shared/v86-pipeline-mapping.md`.

**Phase 36-05 Wave 2 refinement:** All 8 gates are now mapped to the actual module `GATE_ID` constants (Phase 35 + Phase 36 Wave 1 modules). The V8.6 gate→step table below is augmented with the actual module wiring (gates 4-8 no longer "Future").

---

## The 8 Gates

> Reproduced verbatim from `_shared/v86-pipeline-mapping.md` §"V8.6 8-Gate Review Structure". V8.6 reduces review gates from 12 to 8 — user wait rounds halved.

| # | V8.6 Gate | Triggers After Step | Reviewer Experts | User Decision Content |
|---|-----------|---------------------|-------------------|----------------------|
| 1 | 选题 + 主题 + hook 候选 | Step 1 | `hook_retention` + `compliance_gate` (red-line check) | Topic Kernel + hook 候选确认 |
| 2 | 故事框架 + 大纲 | Step 2 | `creative_source` + `screenplay` + `style_genome` (5D 向量) | 故事框架 + Snyder 15-beat 确认 |
| 3 | 剧本 + 审计结果 | Step 3 | `screenplay` + `script_auditor` + `compliance_gate` | scene-level 剧本 + 5 维审计报告确认 |
| 4 | 角色资产库 | Step 4 | `character_designer` + `visual_executor` | L1-L4 资产库确认 |
| 5 | 时空剧本 + 运镜 + 终审 | Step 6 | `screenplay` + `cinematographer` + `script_auditor` + `compliance_gate` | 时空化剧本 + 运镜 + 终审报告确认 |
| 6 | 视觉种子 + 风格化 + 声音骨架 | Step 7 (含 7B) | `visual_executor` + `prompt_injector` + `style_genome` + `colorist` + `audio_pipeline` + `compliance_gate` (可选红线复查) | 视觉种子 + 风格化 + 声音骨架确认 |
| 7 | 一致性检查 | Step 9 | `continuity_auditor` | 4 维跨镜头一致性审计报告确认 |
| 8 | 最终成片 + BGM + 音效 + 口型 | Step 11 | `audio_pipeline` + 全专家终审 + `compliance_gate` (distribution compliance) | 最终成片 + 分发合规确认 |

---

## Hard vs Soft Gates

> Reproduced from `_shared/v86-pipeline-mapping.md` §"Hard vs Soft gates".

**Hard gates** (fail blocks pipeline progression):
- `compliance_gate` — red-line / 备案 / AIGC 标识 fail
- `script_auditor` — predicted completion < 65%
- `continuity_auditor` — 4-dimension fail (face / wardrobe / color / object)

**Soft gates** (user can bypass):
- `theory_critic` — artistic critique, advisory only (consultative node, no fixed gate position)

---

## Gate Implementation

Gate lifecycle (submit → wait → resolve) is implemented in `plugins/review_gates/gate.py` (Phase 34). The `kais-movie-pipeline` runner (`pipeline/runner.py`, Phase 35-02) triggers gates via Phase 34's `runner_hooks`:

- `pause_for_review` — submit gate, block runner (blocking mode)
- `resolve_direct` — auto-resolve gate from in-pipeline decision (e.g. script_auditor score)
- `resume_from_callback` — webhook/HMAC callback drives runner resume
- `mark_episode_failed` — gate `max_retries` exhausted → episode-level fail (preserves v4.0 `PIPE-GUARD-01` CONSISTENCY_BLOCKED semantics — no silent error swallowing)

Gate YAML config: `plugins/review_gates/gates.yaml` (Phase 34) defines per-gate `gate_id` / `phase` / asset-bus slots to lock / reviewer role / `timeout_sec` / `callback_url` / `retry_policy`.

---

## All 8 Gates (Phase 35+36 Complete)

> Refined in Phase 36-05 from Wave 1 module `GATE_ID` constants. The V8.6 gate→step table above is the conceptual mapping; this table is the implementation wiring — which phase module actually fires each gate, and under what mode.

| Gate | V8.6 Gate Name | Trigger Module | Module `GATE_ID` | Mode | Reviewer(s) | Status |
|------|----------------|----------------|-------------------|------|-------------|--------|
| **Gate 1** | 选题 + 主题 + hook 候选 | `p01_hook_topic.py` | `"selection-topic-hook"` | Hard (blocking) | `hook_retention` + `compliance_gate` (red-line) | **Complete** (Phase 35) |
| **Gate 2** | 故事框架 + 大纲 | `p02_outline.py` | `"story-framework"` | Hard (blocking) | `creative_source` + `screenplay` + `style_genome` | **Complete** (Phase 35) |
| **Gate 3** | 剧本 + 审计结果 | `p03_script_audit.py` | `"script-audit"` | Hard (blocking) | `screenplay` + `script_auditor` + `compliance_gate` | **Complete** (Phase 35) |
| **Gate 4** | 角色资产库 + pain points | `p05_pain_discovery.py` | `"shot-prep"` | Hard (blocking) | `character_designer` + `visual_executor` + operator (confirms L1-L4 assets + L1-L6 pain strata before visual design) | **Complete** (Phase 36-01) |
| **Gate 5** | 视觉种子 + 风格化 | `p07_scene_generation.py` | `"scene-design"` | Hard (blocking) | `visual_executor` + `prompt_injector` + `style_genome` + `colorist` + operator (confirms 4-dim consistency: scene-images + style-vector + color-intent) | **Complete** (Phase 36-02) |
| **Gate 6** | 时空剧本 + 运镜 + 终审 | `p06_spatio_temporal_script.py` | `"spatio-temporal"` | Hard (blocking) | `screenplay` + `cinematographer` + `script_auditor` + `compliance_gate` | **Complete** (Phase 36-01) |
| **Gate 7** | 视频预览 (parallel-shots) | `p11_video_render.py` | `"render-preview"` | Soft (operator can bypass in async mode) | `visual_executor` (animator) + operator (preview per-shot clips + lip-sync reports before composition) | **Complete** (Phase 36-03) |
| **Gate 8** | 最终成片 + 分发合规 | `p13_delivery.py` | `"final-delivery"` | Hard (blocking — release gate) | `colorist` + `compliance_gate` (CN red-line + AIGC labeling) + operator | **Complete** (Phase 36-04) |

**Phase modules with no gate (`GATE_ID = None`):**
- `p04_character_design.py` — Gate 4 fires after **p05** (not p04) per V8.6 gates.yaml (character bible alone isn't reviewable — operator confirms together with pain points).
- `p08_scene_selection.py` — selection is operator-curated inline (no formal gate).
- `p09_shot_breakdown.py` — E-Konte sheets are deterministic decomposition, no creative review.
- `p10_voice.py` — voicer output is reviewed indirectly via Gate 7 (render preview includes lip-sync).
- `p12_composition.py` — composition feeds Gate 8 (final delivery); no mid-pipeline gate.

**Gate triggering contract (CF-36-04):**
Phase modules trigger gates ONLY when **both** conditions hold:
1. `GATE_ID` module constant is set (not `None`)
2. `trigger_gate` callable is provided (runner passes `None` when `RunnerConfig.enable_gates=False`)

Verified by per-phase unit tests (`test_*_gate_none_even_when_trigger_gate_provided` for non-gating phases; `test_*_triggers_correct_gate_when_configured` for gating phases).

---

## See Also

- [`pipeline-dag.md`](./pipeline-dag.md) — full 13-step DAG (gate trigger phases)
- [`asset-bus-schema.md`](./asset-bus-schema.md) — `review-outcomes` slot schema (gate decision persistence)
- `plugins/review_gates/gates.yaml` — Phase 34 canonical gate config (8 gates)
- `_shared/v86-pipeline-mapping.md` — canonical source ref
