# Phase 42 — DATA 数据收敛 (Step 15) Plan Overview

**Phase goal:** Platform API metrics (完播率 / 卡点跳出率 / 互动率 / 收藏率 / 评论率) flow back into a v6.0 FeedbackStore-compatible store, per-platform bucketed, with a formula tuning loop that suggests `plugins/formula_library/` improvements and a `hermes formula stats` CLI dashboard for inspection.

**Depends on:** Phase 38 (SLICE — `variants[]` schema shipped 2026-06-27) + Phase 39 (FORM — `plugins/formula_library/` shipped). Both complete; Phase 42 unblocked.

**Requirements covered:** DATA-01, DATA-02, DATA-03, DATA-04 (4 requirements, 4 plans).

---

## Scope Discipline — Option A (load-bearing)

v9.0 PROJECT.md mandates: **"仅 skills/kais-movie-pipeline/ + skills/movie-experts/ + 新 plugin plugins/formula_library/, 不碰 Hermes 核心 Python/JS 代码"**. Phase 42 has a structural tension with this rule: DATA-02 calls for "FeedbackRecord gains a `platform_metrics` field", but `agent/feedback_schema.py` (where `FeedbackRecord` lives) IS Hermes core.

**Decision (recorded in STATE.md and applied here):** Use **Option A — NEW plugin `plugins/platform_metrics/`** (parallel to `formula_library`). The new plugin:

- Owns the `PlatformMetrics` Pydantic schema (DATA-01)
- Owns a `FeedbackRecordExtension` Pydantic model that **composes with** the v6.0 `FeedbackRecord` via a `feedback_id` FK (DATA-02) — does NOT modify `FeedbackRecord` itself
- Owns the 5 platform adapter stubs (DATA-01)
- Owns `formula_tuning_loop` (DATA-03) — reads from existing v6.0 `FeedbackStore` via **public API only** (`query()`, `summary()`, `get_record()`)
- Owns `hermes formula stats` CLI subcommand (DATA-04) — registered via `ctx.register_cli_command(name="formula", ...)` (auto-discovered at `hermes_cli/main.py:11942`)

**Option B (rejected):** Extend `FeedbackRecord` in `agent/feedback_schema.py` — violates scope discipline and risks regressions on the v6.0 backward-compat contract.

**Forbidden touchpoints (READ ONLY):**
- `agent/feedback_schema.py` (v6.0 core)
- `agent/feedback_store.py` (v6.0 core)
- `agent/evolution/queue.py` (v6.0 core; consume-only via public API)
- `hermes_cli/main.py` (Hermes core CLI — plugin `register_cli_command` hook is the only path)
- All previously shipped v9.0 work (Phases 38/39/40/41)
- All 16 active `movie-experts/*/SKILL.md` (FOUND-08 byte-frozen milestone-wide)

---

## Coverage Table

| Plan | Requirements | Wave | Objective |
|------|--------------|------|-----------|
| 42-01 | DATA-01 (schema half) + DATA-02 | 1 | Plugin scaffold + `PlatformMetrics` + `FeedbackRecordExtension` + adapter base class + tests |
| 42-02 | DATA-01 (adapter half) | 1 (parallel with 42-01) | 5 platform adapter stubs (douyin / kuaishou / weixin_video / xiaohongshu / bilibili) + adapter registry + tests |
| 42-03 | DATA-03 | 2 | `tuning_loop.py` + `library_writer.py` + JSONL review queue integration tests |
| 42-04 | DATA-04 | 2 (parallel with 42-03) | `hermes formula stats` CLI + `references/data-convergence.md` ref + `SKILL.md` Step 15 + `pipeline-dag.md` annotation |

**Wave structure:**

```
Wave 1 (parallel, no file overlap):
  ├── Plan 42-01  (plugins/platform_metrics/{plugin.yaml,__init__.py,schema.py,adapters/base.py,adapters/__init__.py} + tests/test_schema.py + tests/test_adapter_base.py)
  └── Plan 42-02  (plugins/platform_metrics/adapters/{douyin,kuaishou,weixin_video,xiaohongshu,bilibili}.py + tests/test_adapters.py)
Wave 2 (depends on Wave 1; 42-03 + 42-04 parallel):
  ├── Plan 42-03  (plugins/platform_metrics/{tuning_loop,library_writer}.py + tests/test_tuning_loop.py + tests/test_library_writer.py)
  └── Plan 42-04  (plugins/platform_metrics/cli.py + references/data-convergence.md + SKILL.md + pipeline-dag.md patch + tests/test_cli.py + .env.example patch)
```

---

## Multi-Source Coverage Audit

| Source | Item | Covered by Plan | Status |
|--------|------|-----------------|--------|
| **GOAL** | Platform API metrics flow back into FeedbackStore per-platform bucketed | 42-01 (schema) + 42-02 (adapters) + 42-03 (tuning) + 42-04 (CLI/ref) | COVERED |
| **GOAL** | `formula_tuning_loop` suggests formula_library improvements | 42-03 (tuning_loop + library_writer + JSONL queue) | COVERED |
| **GOAL** | `hermes formula stats` CLI dashboard | 42-04 (cli.py subcommand + rich tables + --json) | COVERED |
| **REQ DATA-01** | 5 platform API adapter stubs (douyin/kuaishou/weixin_video/xiaohongshu/bilibili) | 42-01 (base class) + 42-02 (5 stub files) | COVERED |
| **REQ DATA-01** | Operator `~/.hermes/.env` key activation (`DOUYIN_API_KEY` etc.) | 42-04 (.env.example patch) + 42-01 (base class env-var check) | COVERED |
| **REQ DATA-01** | Unified `PlatformMetrics` Pydantic schema | 42-01 (schema.py) | COVERED |
| **REQ DATA-02** | `FeedbackRecord` extension with `platform_metrics` field, backward-compat | 42-01 (FeedbackRecordExtension with feedback_id FK — composes WITH FeedbackRecord, no schema modification) | COVERED (Option A composition) |
| **REQ DATA-03** | Tuning loop metric→suggestion conversion (hook dropoff / low-engagement triggers) | 42-03 (tuning_loop.py suggestion rules) | COVERED |
| **REQ DATA-03** | JSONL review queue (mirror v6.0 EVOL-02 pattern) | 42-03 (TuningSuggestion schema + JSONL queue under HERMES_HOME/skills/.feedback/tuning/) | COVERED |
| **REQ DATA-03** | Operator approve → write back to formula_library | 42-03 (library_writer.py + atomic write) | COVERED |
| **REQ DATA-04** | `references/data-convergence.md` ref | 42-04 (new ref ~300-500 lines bilingual) | COVERED |
| **REQ DATA-04** | `hermes formula stats` rich tables per-formula/per-platform | 42-04 (cli.py with rich.Table) | COVERED |
| **REQ DATA-04** | `--json` counts-only flag | 42-04 (cli.py argparse flag) | COVERED |
| **RESEARCH** | v6.0 FeedbackStore public API surface (consume-only) | 42-01/42-03 (uses `query()`, `summary()`, `get_record()` only) | COVERED |
| **RESEARCH** | EVOL-02 JSONL queue pattern (queue/applied/rejected.jsonl + atomic rewrite) | 42-03 (mirrors agent/evolution/queue.py structure exactly) | COVERED |
| **RESEARCH** | Plugin CLI registration (`ctx.register_cli_command`) | 42-04 (mirrors google_meet pattern) | COVERED |
| **RESEARCH** | httpx for adapter stubs (Hermes core dependency) | 42-01/42-02 (adapters use httpx.AsyncClient; no platform-specific SDKs) | COVERED |
| **CONTEXT** | Operator-action-handoff: 5 platform API keys operator-side | 42-01 base class + 42-04 .env.example doc + ref handoff section | COVERED |
| **CONTEXT** | V9-FUTURE-01 deferred (live ingestion) | 42-02 stubs only (raise `NotImplementedError` on live call without key; documented in ref) | COVERED |
| **CONTEXT** | FOUND-08 byte-frozen rule continues | 42-04 SKILL.md patch is body-only (zero frontmatter touch) | COVERED |
| **CONTEXT** | V8.6 13-step numbering preserved (Step 15 additive) | 42-04 SKILL.md Step 15 is additive (after Step 14; zero step_count bump) | COVERED |

**Audit result:** 0 unplanned items. 0 gaps.

---

## Plan-Level Constraints (apply to ALL plans in this phase)

1. **No Hermes core edits.** `agent/feedback_schema.py`, `agent/feedback_store.py`, `agent/evolution/queue.py`, `hermes_cli/main.py` are READ ONLY. Consume v6.0 FeedbackStore via public API only.
2. **Option A composition.** `FeedbackRecordExtension` has `feedback_id: str` FK to v6.0 `record_id` — it never imports or extends the `FeedbackRecord` class.
3. **Pure stdlib + httpx.** Adapter stubs use `httpx.AsyncClient` (Hermes core dep) + `os.environ.get` for env-key activation. NO platform-specific SDK (no `tencentcloud-sdk-python`, no `bilibili-api-python`).
4. **FOUND-08 byte-frozen rule continues.** Zero `expert_id` / frontmatter changes on any of the 16 active movie-experts. SKILL.md Step 15 patch is body-only.
5. **V8.6 13-step numbering preserved.** Step 15 is ADDITIVE — `pipeline.step_count` stays 13, `pipeline.gate_count` stays 8. Step 15 fires AFTER Step 14 (which fires after Step 13).
6. **Bilingual docs.** `data-convergence.md` is 中文为主 + English code identifiers. Plugin README bilingual. Pydantic docstrings in English.
7. **CLAUDE.md conventions.** `from __future__ import annotations` at top of every `.py`; `encoding="utf-8"` on every `open()` (Ruff PLW1514); lazy %-logging; specific exceptions bound with `as exc`.
8. **TDD where it fits.** Suggestion-rule logic (DATA-03) + schema validation + adapter registry are pure functions with defined I/O → use `tdd="true"` + `<behavior>` blocks. CLI argparse / ref doc / SKILL.md patch are not TDD.

---

## Execution Wave Order

1. **Wave 1:** Run Plan 42-01 and Plan 42-02 in parallel (zero file overlap — 42-01 owns `schema.py`/`base.py`/`__init__.py`/`plugin.yaml`; 42-02 owns the 5 adapter files).
2. **Wave 2:** Run Plan 42-03 and Plan 42-04 in parallel (zero file overlap — 42-03 owns `tuning_loop.py`/`library_writer.py`; 42-04 owns `cli.py` + the ref + SKILL.md patch + pipeline-dag.md patch + `.env.example`).

---

## Success Criteria ↔ Plan Mapping (from ROADMAP.md Phase 42)

| ROADMAP SC | Description | Plan(s) |
|------------|-------------|---------|
| SC#1 | 5 adapter stubs unified on `PlatformMetrics`; env-key activation; live ingestion deferred (V9-FUTURE-01) | 42-01 (schema) + 42-02 (stubs) + 42-04 (ref handoff doc) |
| SC#2 | FeedbackRecord gains `platform_metrics` per-platform bucketed; v6.0 records backward-compatible | 42-01 (FeedbackRecordExtension + feedback_id FK composition) |
| SC#3 | `formula_tuning_loop` converts metrics → JSONL suggestions; operator approve → formula_library write-back | 42-03 (tuning_loop + library_writer + JSONL queue) |
| SC#4 | `hermes formula stats` rich per-formula / per-platform tables + `--json` flag | 42-04 (cli.py) |
| SC#5 | New ref `references/data-convergence.md` + operator-action-handoff doc | 42-04 (ref + .env.example patch) |

---

*Phase 42 plan created: 2026-06-27 — 4 plans in 2 waves. Source audit clean (0 gaps). Option A scope decision applied (new `plugins/platform_metrics/` plugin; no Hermes core edits).*
