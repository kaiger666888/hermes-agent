# Review Gates — 11-Gate Per-Phase Mapping (8 V8.6 + 3 Phase 40 Redline, additive)

**Source:** `_shared/v86-pipeline-mapping.md` §"V8.6 8-Gate Review Structure" (Phase 27 canonical ref); gate lifecycle semantics from `plugins/review_gates/gate.py` (Phase 34); Phase 40 redline gates from `creative-redlines.md` §R1/§R3/§R4.
**Copyright:** Fair Use — gate trigger phase + reviewer role is factual integration architecture.
**Last-verified:** 2026-06-26 (Phase 40 — 3 redline gates 9/10/11 appended additively; V8.6 8-gate table unchanged)

---

## Summary

This document specifies the **11 review gates** (8 V8.6 + 3 Phase 40 redline) and their per-phase mapping. It answers "which gates fire when, and what reviewer role / mode each uses" for the `kais-movie-pipeline` orchestration skill. Gate numbering, trigger phases, and reviewer composition sourced from `_shared/v86-pipeline-mapping.md` (V8.6 gates 1-8) and `creative-redlines.md` §R1/§R3/§R4 (redline gates 9-11).

**Phase 36-05 Wave 2 refinement:** All 8 V8.6 gates are now mapped to the actual module `GATE_ID` constants (Phase 35 + Phase 36 Wave 1 modules). The V8.6 gate→step table below is augmented with the actual module wiring (gates 4-8 no longer "Future").

**Phase 40 additive extension:** 3 redline gates (R1 emotion desensitization / R3 zero-backstory preamble / R4 unresolved ending) are appended as gates 9/10/11. The V8.6 8-gate numbering is preserved unchanged — the 3 new gates fire **after** Gate 8 (delivery) passes and **before** final `master.mp4` release, as one last structural scan. Each redline gate auto-resolves via a detector in `plugins/review_gates/gates/` (Plan 40-01) — no human signoff needed (redline violations are structural / deterministic, not creative-judgment). See §"Phase 40 Redline Gates" and §"Gate Implementation" below.

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

## Phase 40 Redline Gates (9-11, additive)

> Appended in Phase 40 (GATE-04). V8.6 numbering (gates 1-8) is preserved unchanged — these 3 gates are **additive**, registered as 9/10/11 in the same `gates.yaml` config. They fire **after** Gate 8 (final delivery) passes and **before** final `master.mp4` release, as one last structural scan per `ROADMAP.md` Phase 40 SC#3 ("gates 9/10/11 fire after existing 8 pass, before final delivery").
>
> Unlike the 8 V8.6 gates (HIL — human operator resolves via `gate_resolve`), the 3 redline gates **auto-resolve** via detectors in `plugins/review_gates/gates/` (Plan 40-01). Rationale: redline violations are structural / deterministic (consecutive-emotion count / first-beat label / last-beat label) — no human creative judgment needed. See §"Gate Implementation" below for the auto-detect path contract.

| # | Phase 40 Gate | Triggers After Gate | Reviewer | Decision Mode | Source |
|---|---------------|---------------------|----------|---------------|--------|
| 9 | `redline_emotion_desensitize` | Gate 8 (delivery-gate) passes, before final `master.mp4` release | `redline_scanner` (auto-detect) | Auto-reject on violation | `creative-redlines.md §R1` |
| 10 | `redline_no_cold_open` | Gate 8 passes | `redline_scanner` | Auto-reject | `creative-redlines.md §R3` |
| 11 | `redline_unfinished_ending` | Gate 8 passes | `redline_scanner` | Auto-reject | `creative-redlines.md §R4` |

### Gate 9 — R1 情绪脱敏 (Emotion Desensitization)

**Operational definition** (from [`creative-redlines.md §R1`](./creative-redlines.md)): 同类型情绪连续出现不得超过 2 次;第 3 个连续同类型即触发脱敏。English: "no more than 2 consecutive beats of the same emotion taxonomy within any 60s window; the 3rd consecutive same-emotion beat triggers desensitization."

- **Detector:** `plugins/review_gates/gates/redline_emotion_desensitize.py::detect(payload)` — walks `payload["beats"]` with a 3-element sliding window; if all 3 beats in any window share the same `emotion` value → `("reject", "formula:emotion-break-up")`.
- **suggested_action:** `formula:emotion-break-up` — references the Phase 39 `formula_library` entry (read-side lookup) that instructs screenplay / editor to break up the desensitizing run by inserting a contrasting emotion beat (e.g. anger→anger→anger becomes anger→anger→shock). The operator applies this proven fix pattern.
- **Boundary:** <3 beats → approve (cannot form a 3-window); exactly 2 consecutive same-emotion is OK (R1 spec permits ≤2).

### Gate 10 — R3 零背景铺垫 (Zero Backstory Preamble)

**Operational definition** (from [`creative-redlines.md §R3`](./creative-redlines.md)): 切入即冲突,禁止"从前有个…"。竖屏前 3 秒 / 横屏前 10 秒必须包含 active conflict,不可出现纯 exposition。English: "cold-open with conflict; the first beat must NOT be labeled exposition / narration / setup — it must be an active-conflict beat to lock attention within the platform's skip window."

- **Detector:** `plugins/review_gates/gates/redline_no_cold_open.py::detect(payload)` — reads `payload["beats"][0]["label"]`; if in `{"exposition", "narration", "setup"}` → `("reject", "formula:cold-open-conflict-hook")`.
- **suggested_action:** `formula:cold-open-conflict-hook` — references the Phase 39 `formula_library` entry (read-side lookup) that instructs screenplay + hook_retention to rewrite the cold open with an in-frame active conflict (e.g. character collision, sudden noise, visual rupture) replacing any pure-narration preamble. The operator applies this proven fix pattern.

### Gate 11 — R4 结尾未完成 (Unresolved Ending)

**Operational definition** (from [`creative-redlines.md §R4`](./creative-redlines.md)): 最后 3 秒(竖屏)/ 最后 10 秒(横屏)必须释放新钩子,禁止大团圆;不可出现冲突闭合 / 情绪舒缓 / "未完待续"静止字幕。English: "the final beat must release a new hook, not a tidy closure; the last beat must NOT be labeled resolution / closure / epilogue — it must seed an open question (cliffhanger / twist / new information) to drive the next-episode play."

- **Detector:** `plugins/review_gates/gates/redline_unfinished_ending.py::detect(payload)` — reads `payload["beats"][-1]["label"]`; if in `{"resolution", "closure", "epilogue"}` → `("reject", "formula:open-question-cliffhanger")`.
- **suggested_action:** `formula:open-question-cliffhanger` — references the Phase 39 `formula_library` entry (read-side lookup) that instructs screenplay + editor + hook_retention to replace the closing beat with an open-question seed (e.g. phone rings mid-hug, new character name on screen, unanswered visual cue). The operator applies this proven fix pattern.

### 11-Gate Sequence Diagram

```
Step 1-11 pipeline execution (V8.6 gates 1-8 fire inline, HIL manual resolution)
  │
  ├─ Step 1  ──► Gate 1 (selection-topic-hook)        ──► [HIL] operator confirms
  ├─ Step 2  ──► Gate 2 (story-framework)             ──► [HIL]
  ├─ Step 3  ──► Gate 3 (script-audit)                ──► [HIL]
  ├─ Step 4-5──► Gate 4 (shot-prep)                   ──► [HIL]
  ├─ Step 6  ──► Gate 6 (spatio-temporal)             ──► [HIL]
  ├─ Step 7  ──► Gate 5 (scene-design)                ──► [HIL]
  ├─ Step 9  ──► Gate 7 (render-preview)              ──► [HIL soft, operator can bypass]
  ├─ Step 11 ──► Gate 8 (final-delivery)              ──► [HIL] operator confirms final master
  │
  ▼ (Gate 8 passes — V8.6 HIL path complete)
  │
  ┌─────────────────────────────────────────────────────────┐
  │  Phase 40 redline scan (auto-detect, no human signoff)  │
  │                                                         │
  │  Gate 9  redline_emotion_desensitize  (R1)              │
  │     └─► detector ──► approve ─────────────► continue    │
  │     └─► detector ──► reject + formula: ──► rollback     │
  │                                                         │
  │  Gate 10 redline_no_cold_open          (R3)             │
  │     └─► detector ──► approve ─────────────► continue    │
  │     └─► detector ──► reject + formula: ──► rollback     │
  │                                                         │
  │  Gate 11 redline_unfinished_ending     (R4)             │
  │     └─► detector ──► approve ─────────────► continue    │
  │     └─► detector ──► reject + formula: ──► rollback     │
  └─────────────────────────────────────────────────────────┘
  │
  ▼ (Gates 9-11 all approve)
  │
  Final master.mp4 release (Step 14 platform slicing proceeds)
```

---

## Gate Implementation

Gate lifecycle (submit → wait → resolve) is implemented in `plugins/review_gates/gate.py` (Phase 34). The `kais-movie-pipeline` runner (`pipeline/runner.py`, Phase 35-02) triggers gates via Phase 34's `runner_hooks`:

- `pause_for_review` — submit gate, block runner (blocking mode)
- `resolve_direct` — auto-resolve gate from in-pipeline decision (e.g. script_auditor score)
- `resume_from_callback` — webhook/HMAC callback drives runner resume
- `mark_episode_failed` — gate `max_retries` exhausted → episode-level fail (preserves v4.0 `PIPE-GUARD-01` CONSISTENCY_BLOCKED semantics — no silent error swallowing)

Gate YAML config: `plugins/review_gates/gates.yaml` (Phase 34) defines per-gate `gate_id` / `phase` / asset-bus slots to lock / reviewer role / `timeout_sec` / `callback_url` / `retry_policy`. Phase 40 expanded this config 8 → 11 gates (additive — see Plan 40-02).

### Two resolution paths (V8.6 HIL vs Phase 40 auto-detect)

The 8 V8.6 gates and the 3 Phase 40 redline gates use **different resolution paths** in `runner_hooks.py`:

| Path | Applies to | Resolution flow | Reviewer |
|------|------------|-----------------|----------|
| **V8.6 HIL (manual)** | gate_ids NOT starting with `redline_` (gates 1-8) | `pause_for_review` submits gate → operator calls `gate_resolve` via tool / webhook → runner resumes | Human operator (creative judgment) |
| **Phase 40 auto-detect** | gate_ids starting with `redline_` (gates 9-11) | `auto_detect_and_resolve` looks up detector in `DETECTOR_REGISTRY`, runs `detect(payload)`, calls `gate.resolve(decision, suggested_action)` immediately — **no human signoff** | `redline_scanner` (deterministic detector) |

**Phase 40 auto-detect contract** (Plan 40-02):

```python
# plugins/review_gates/runner_hooks.py
def is_redline_gate(gate_id: str) -> bool: ...
    # True iff gate_id.startswith("redline_")

def auto_detect_and_resolve(gate_id: str, episode_id: str, payload: dict) -> dict: ...
    # 1. Build Gate via _build_gate(gate_id, episode_id) — reuse existing helper.
    # 2. gate.submit(payload) — may raise GateMaxRetriesExceeded.
    # 3. Look up detector in DETECTOR_REGISTRY (Plan 40-01); run detect(payload).
    # 4. gate.resolve(decision, suggested_action) — Phase 34 public API.
    # 5. Write outcome to asset-bus review-outcomes slot; advance state.
    # Returns: {"decision", "suggested_action", "rollback_to", ...}
```

**Rationale for the split:** redline violations (R1/R3/R4) are structural / deterministic — a 3-beat same-emotion run, a first-beat exposition label, a last-beat closure label. No human creative judgment is needed to identify them, so blocking the pipeline for HIL signoff would add latency without value. The 8 V8.6 gates involve creative / aesthetic / compliance decisions where operator confirmation is load-bearing, so they keep the manual HIL path. The two paths share the same Phase 34 `Gate` state machine (`gate.submit` + `gate.resolve`) — only the resolution trigger differs.

**T-40-09 mitigation (elevation of privilege):** only gate_ids present in both `GATE_REGISTRY` (gates.yaml) AND `DETECTOR_REGISTRY` can auto-resolve. A `redline_*` gate_id with no matching detector raises `KeyError` rather than silently auto-approving — misconfiguration fails closed.

---

## All 11 Gates (Phase 35+36 Complete, Phase 40 Redline Added)

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
| **Gate 9** | R1 情绪脱敏 (emotion desensitization) | `runner_hooks.auto_detect_and_resolve` (Plan 40-02) | `"redline_emotion_desensitize"` | Auto-detect (blocking w/ detector — no HIL) | `redline_scanner` (`DETECTOR_REGISTRY`, Plan 40-01) | **Complete** (Phase 40) |
| **Gate 10** | R3 零背景铺垫 (no cold open) | `runner_hooks.auto_detect_and_resolve` | `"redline_no_cold_open"` | Auto-detect (blocking w/ detector) | `redline_scanner` (`DETECTOR_REGISTRY`) | **Complete** (Phase 40) |
| **Gate 11** | R4 结尾未完成 (unresolved ending) | `runner_hooks.auto_detect_and_resolve` | `"redline_unfinished_ending"` | Auto-detect (blocking w/ detector) | `redline_scanner` (`DETECTOR_REGISTRY`) | **Complete** (Phase 40) |

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
- [`creative-redlines.md`](./creative-redlines.md) — **Phase 40 redline gates 9-11 implement R1 / R3 / R4 from this ref** (the authoritative source for the 3 redline operational definitions)
- `plugins/review_gates/gates.yaml` — Phase 34 canonical gate config (Phase 40 expanded 8 → 11 gates)
- `plugins/review_gates/gates/` (Plan 40-01) — redline detector modules (R1/R3/R4), pure-stdlib, registered in `DETECTOR_REGISTRY`
- `plugins/review_gates/runner_hooks.auto_detect_and_resolve` (Plan 40-02) — auto-detect dispatch path for `redline_*` gate_ids
- `_shared/v86-pipeline-mapping.md` — canonical source ref (V8.6 8-gate table)
