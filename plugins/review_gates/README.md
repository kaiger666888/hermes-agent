# review_gates plugin

**English headings + bilingual body (EN structure + 中文段落).** 本 plugin 实现 HIL review gate 框架 —— gate 生命周期(submit / wait / resolve)、`delegate_task` 审批回调、以及 11 个 gate 的 YAML 配置(8 V8.6 + 3 Phase 40 redline,additive)。

This plugin registers 4 tools into the `review_gates` toolset. Phase 31 scaffolded the stubs; Phase 34 landed the real gate state machine (`gate.py`) + `delegate_task` approval callback + the 8 V8.6 gate YAML config; **Phase 40 appended 3 cross-platform redline gates (R1/R3/R4) additively** and wired an auto-detect resolution path so redline violations resolve without human signoff.

## Exposed tools

- `gate_submit` — submit a HIL review gate (blocking / webhook / polling). **For `gate_id`s starting with `redline_`** (gates 9-11), the runner auto-resolves via Plan-01 detectors in `plugins/review_gates/gates/` — no manual `gate_resolve` needed. For the 8 V8.6 `gate_id`s, the manual HIL resolution path is preserved (operator confirms via `gate_resolve`).
- `gate_wait` — block until gate resolves or poll until timeout
- `gate_resolve` — resolve a gate with approve / reject / contest decision (used by the V8.6 HIL path; the redline auto-detect path calls `Gate.resolve()` internally and does not require this tool)
- `gates_list` — list all configured gates (**11 gates**: 8 V8.6 + 3 redline) with phase / role / mode

## Phase 40 Additions

Phase 40 (GATE — 3 新审核门) added 3 cross-platform redline gates additively (V8.6 8-gate numbering preserved, new gates registered as 9/10/11):

| `gate_id` | Redline | Detector module | `suggested_action` formula_id |
|-----------|---------|-----------------|-------------------------------|
| `redline_emotion_desensitize` | R1 情绪脱敏 | `gates/redline_emotion_desensitize.py` | `formula:emotion-break-up` |
| `redline_no_cold_open` | R3 零背景铺垫 | `gates/redline_no_cold_open.py` | `formula:cold-open-conflict-hook` |
| `redline_unfinished_ending` | R4 结尾未完成 | `gates/redline_unfinished_ending.py` | `formula:open-question-cliffhanger` |

Each gate implements one creative-redline (R1 / R3 / R4) from [`skills/kais-movie-pipeline/references/creative-redlines.md`](../../skills/kais-movie-pipeline/references/creative-redlines.md). 3 redline 在最终成片前(gate 8 delivery 通过后、`master.mp4` 发布前)再扫一次 —— per `ROADMAP.md` Phase 40 SC#3.

**Detector modules** (`gates/` subpackage, Plan 40-01): pure stdlib (only `typing` + sibling `gates.types` — extends D-34-01 discipline; AST-verified by `tests/test_redline_purity.py`). Each detector emits `(decision, suggested_action)` where `suggested_action` is a `formula:`-prefixed string referencing a Phase 39 `formula_library` entry (read-side lookup — operator applies the proven fix pattern).

**Auto-detect path** (Plan 40-02, `runner_hooks.py`):

- `is_redline_gate(gate_id) -> bool` — True iff `gate_id.startswith("redline_")`.
- `auto_detect_and_resolve(gate_id, episode_id, payload) -> dict` — looks up detector in `DETECTOR_REGISTRY`, runs `detect(payload)`, calls `Gate.resolve(decision, suggested_action)` immediately. Returns `{"decision", "suggested_action", "rollback_to", ...}`. No human signoff.

Routing: `tools._handle_gate_submit` checks `is_redline_gate(gate_id)` at the top — redline_ gates dispatch to `auto_detect_and_resolve` (tool envelope returns `status="auto_resolved"`); all other gate_ids fall through to the existing V8.6 `pause_for_review` HIL path (unchanged).

Rationale: redline violations are structural / deterministic (consecutive-emotion count, first-beat label, last-beat label) — no human creative judgment needed. The 8 V8.6 gates involve creative / aesthetic / compliance decisions where operator confirmation is load-bearing, so they keep manual HIL. The two paths share the same Phase 34 `Gate` state machine; only the resolution trigger differs.

Cross-reference: the 11-gate per-phase mapping is documented in [`skills/kais-movie-pipeline/references/review-gates.md`](../../skills/kais-movie-pipeline/references/review-gates.md).

## Status

- **Phase 31:** scaffolding only — manifest + `register(ctx)` + schemas + stub handlers. `kind: standalone` → opt-in via `plugins.enabled`.
- **Phase 34:** real gate state machine (`gate.py`) + `delegate_task` approval callback + 8 V8.6 gate YAML config land here. Tool schemas unchanged from Phase 31.
- **Phase 40:** 3 redline gates (R1/R3/R4) added additively as gates 9/10/11. Detector modules in `gates/` subpackage (Plan 40-01) + auto-detect path in `runner_hooks.auto_detect_and_resolve` (Plan 40-02). Plugin version bumped 0.1.0 → 0.2.0. V8.6 8-gate path unchanged (zero behavior regression).

See `PATTERNS.md` in the planning root for the full pattern mapping.
