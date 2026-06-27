# Evolution & Feedback Loop — Gap Analysis

**Created:** 2026-06-27 (session: Kimi feedback-translator discussion)
**Last updated:** 2026-06-27 (post-implementation — Path B now implemented)

---

## 1. Current State: What's Designed vs What Exists

| Component | Design Doc | Code Status |
|-----------|-----------|-------------|
| `plugins/formula_library/` (Step 0 lookup) | SKILL.md §Step 0, `references/data-convergence.md` §2 | ✅ **Implemented** (2026-06-27) — schema.py + lookup.py + library_writer.py + 3 seed formulas. 12 lookup tests + 10 writer tests pass. |
| `plugins/feedback_translator/` (NL feedback → TuningSuggestion) | §2 below | ✅ **Implemented** (2026-06-27) — schema.py + queue.py + translator.py. 12 tests pass. `translate_feedback()` delegates LLM work via `delegate_task`. |
| JSONL queue (`queue.jsonl` / `applied.jsonl` / `rejected.jsonl`) | `references/data-convergence.md` §6 | ✅ **Implemented** — `feedback_translator/queue.py` manages full lifecycle. Default path: `~/.hermes/skills/.feedback/tuning/`. |
| `kais-feedback` skill (Telegram operator interface) | §3 below | ✅ **Implemented** (2026-06-27) — skill at `~/.hermes/skills/kais-feedback/SKILL.md`. Provides NL feedback submission + approve/reject/pending-list/formula-ranking commands. |
| `plugins/platform_metrics/` (5 platform adapters) | `references/data-convergence.md` §4 | ❌ **Not implemented** — adapter stubs described but .py files don't exist. Deferred to V9-FUTURE-01. |
| `tuning_loop.py` (MetricTrigger → TuningSuggestion) | `references/data-convergence.md` §5 | ❌ **Not implemented** — numeric metric triggers deferred. Path B (NL feedback) is the active path. |
| `hermes formula stats` CLI dashboard | `references/data-convergence.md` §7 | ❌ **Not implemented** — operator uses `kais-feedback` skill commands instead (查看pending / formula排行). |
| Step 14 platform master slicing | SKILL.md §Step 14, `references/platform-master-slicing.md` | ❌ **Not implemented** — algorithm doc exists. Deferred per operator decision (2026-06-27). |
| Step 15 data convergence | SKILL.md §Step 15, `references/data-convergence.md` | Partial: Path B (NL feedback) implemented. Path A (platform API metrics) deferred to V9-FUTURE-01. |

**Conclusion:** The **operator NL feedback loop (Path B)** is fully implemented and tested (35/35 tests pass). The **platform API metric loop (Path A)** remains designed-but-unimplemented, gated on operator API key configuration.

---

## 2. Two-Path Architecture

```
Path A (platform API metrics — V9-FUTURE-01, NOT yet implemented):
  Platform API → PlatformMetrics → tuning_loop.classify_metrics() → TuningSuggestion → queue.jsonl

Path B (operator NL feedback — IMPLEMENTED):
  Operator critique (Telegram / text)
    → kais-feedback skill
    → feedback_translator.translate_feedback() (LLM-backed)
    → TuningSuggestion
    → queue.jsonl

Both paths converge:
  queue.jsonl → operator approve → library_writer.apply_suggestion() → formula_library eval_score ±0.05 → next Step 0 lookup
```

**Why two paths:** Platform API requires key configuration the operator hasn't done yet. Operator NL feedback works immediately — no API keys needed, just text input. The two paths are parallel and independent; adding Path A later requires no changes to Path B.

---

## 3. Architecture Decisions (Anti-patterns to avoid)

When external advice (e.g., from other AI assistants) suggests building evolution infrastructure, map suggestions to existing design before building anything new:

| External Suggestion | Existing Equivalent | Action |
|---|---|---|
| "Create `evolution/` directory with `feedback_raw/`, `feedback_parsed/`, `creative_configs/`" | Already designed: `<HERMES_HOME>/skills/.feedback/tuning/{queue,applied,rejected}.jsonl` + AssetBus slots | **Don't create new directories.** Use the designed JSONL queue. |
| "Create `expert_knowledge.jsonl`" | Already designed: `formula_library/library/*.json` — each formula carries `citation`, `verified_date`, `eval_score`, `scope` | **Don't create a second knowledge base.** Formulas ARE the expert knowledge. |
| "Give hermes-agent `update_creative_config` tool" | Already implemented: `library_writer.apply_suggestion()` is the controlled mutation path | **Don't add a new mutation tool.** Use the JSONL queue → approve → library_writer path. |
| "Write a feedback_translator System Prompt" | Now implemented as a **Python module** (`plugins/feedback_translator/translator.py`) + **hermes skill** (`kais-feedback`), not a bare prompt | **Correct.** The module delegates LLM work via `delegate_task` AND manages JSONL I/O. |
| "Don't do auto-scoring" | Already aligned: the system is trigger-based (keyword/threshold → action), not a scoring system | ✅ Already correct. |

---

## 4. eval_score Delta Logic (Implemented)

`library_writer.apply_suggestion()` adjusts `eval_score` by ±0.05 based on Chinese keyword detection in `suggested_action`:

- **Positive (+0.05):** 加强 / 提升 / 增加
- **Negative (−0.05):** 减弱 / 降低 / 删除 / 太
- Clamped to [0.0, 1.0]
- Multiple sequential applies accumulate (e.g., two positive = +0.10)
- Delta is `EVAL_SCORE_DELTA = 0.05` constant — simple and predictable; parameterization is a follow-up

---

## 5. Relationship to kais-evolve

`kais-evolve` (orchestration skill) is a general-purpose autonomous experiment loop. It inspired the evolution thinking but is **not the right tool for this job**:

- kais-evolve operates on **code** (git commit → run test → parse metric → keep/discard)
- The pipeline evolution operates on **creative parameters** (formula configs, hook patterns, pacing templates)
- kais-evolve's `project.md` + `results.tsv` pattern doesn't map to the JSONL queue + TuningSuggestion flow

The pipeline's evolution loop is purpose-built inside `formula_library` + `feedback_translator` plugins, not via kais-evolve.

---

## 6. Remaining Gap: Path A (Platform API Metrics)

To activate Path A, the operator needs to:

1. Configure 5 platform API keys in `~/.hermes/.env` (DOUYIN_API_KEY / KUAISHOU_API_KEY / etc.)
2. Implement `plugins/platform_metrics/` — 5 adapters + schema + tuning_loop
3. Implement `hermes formula stats` CLI (or extend kais-feedback skill to show platform metrics)

The adapter stubs, schema, and MetricTrigger rules are fully specified in `references/data-convergence.md` §3-5.

---

## 7. See Also

- [`references/data-convergence.md`](./data-convergence.md) — Canonical architecture: Step 15 data flow, schema, adapter details, JSONL queue lifecycle
- [`references/feedback-loop-implementation.md`](./feedback-loop-implementation.md) — Implementation session record (module layout, test infrastructure, operator decisions)
- [`references/platform-master-slicing.md`](./platform-master-slicing.md) — Step 14 variants[] algorithm (upstream of Step 15)
- [`references/pipeline-dag.md`](./pipeline-dag.md) — Full 13-step + additive steps dependency graph
