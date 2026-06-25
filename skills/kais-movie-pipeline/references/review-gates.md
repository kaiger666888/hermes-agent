# Review Gates — V8.6 8-Gate Per-Phase Mapping

**Source:** `_shared/v86-pipeline-mapping.md` §"V8.6 8-Gate Review Structure" (Phase 27 canonical ref); gate lifecycle semantics from `plugins/review_gates/gate.py` (Phase 34).
**Copyright:** Fair Use — gate trigger phase + reviewer role is factual integration architecture.
**Last-verified:** 2026-06-25

---

## Summary

This document specifies the **8 V8.6 review gates** and their per-phase mapping. It answers "which gates fire when, and what reviewer role / mode each uses" for the `kais-movie-pipeline` orchestration skill. Gate numbering, trigger phases, and reviewer composition sourced from `_shared/v86-pipeline-mapping.md`.

This is **skeleton form** (per ROADMAP SC#5). Phase 36 refines with actual port experience (gate timeout / retry policy / callback URL per gate).

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

## Phase 35 Gates

Only **Gates 1, 2, 3** are reachable in the Phase 35 vertical slice (p01-p03 modules). Gates 4-8 require Phase 36 phase modules.

| Gate | Phase 35 Module | Status |
|------|-----------------|--------|
| Gate 1 | `p01_hook_topic.py` | Phase 35 (skeleton) |
| Gate 2 | `p02_outline.py` | Phase 35 (skeleton) |
| Gate 3 | `p03_script_audit.py` | Phase 35 (skeleton) |
| Gates 4-8 | (p04-p13 Phase 36) | Future |

---

## See Also

- [`pipeline-dag.md`](./pipeline-dag.md) — full 13-step DAG (gate trigger phases)
- [`asset-bus-schema.md`](./asset-bus-schema.md) — `review-outcomes` slot schema (gate decision persistence)
- `plugins/review_gates/gates.yaml` — Phase 34 canonical gate config (8 gates)
- `_shared/v86-pipeline-mapping.md` — canonical source ref
