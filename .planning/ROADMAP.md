# Roadmap: Hermes Agent — Kai's Personal Agent Platform

## Overview

**Current milestone:** v9.0 — kais-movie-pipeline 闭环深化 (Phases 38-43, in planning).

v9.0 returns to movie-experts deepening after v7.0 (openclaw migration) + v8.0 (quick-task batch). Source: Notion page "心流♥ → aigc开发 → 创作方向" (page_id 32811082-af8e-8009-b097-d19a5027b46f). Tier A shipped as quick task 260626-vzl (3 refs + 3 SKILL.md patches, 2026-06-26). v9.0 implements Tier B + Tier C — closing the 创意→生产→分发→反馈 loop via 4 new pipeline capabilities + 3 cross-platform redline gates.

**Scope discipline (load-bearing):**
- Only `skills/kais-movie-pipeline/` + `skills/movie-experts/` + new plugin `plugins/formula_library/`
- **No Hermes core Python/JS changes** — new plugin lives in `plugins/` namespace; new gates register into existing `plugins/review_gates/` framework (Phase 34-shipped state machine)
- **FOUND-08 frozen rule continues:** zero expert_id / frontmatter changes across all 16 active movie-experts
- **V8.6 13-step numbering preserved** — Step 6.5 / 14 / 15 are additive
- **Bilingual SKILL.md** (EN structure + 中文 body); refs 中文为主

---

## Milestones

- ✅ **v1 Movie-Experts Suite v2** — Phases 0-6 (shipped 2026-06-15)
- ✅ **v2.0 PRFP** — Phases 7-12 (shipped 2026-06-16)
- ✅ **v3.0 Skills-to-DAG Alignment** — Phases 13-18 (shipped 2026-06-17)
- ✅ **v4.0 Methodology Backfill** — Phases 19-21 (shipped 2026-06-18)
- ✅ **v5.0 kais-movie-agent V8.6 Adaptation** — Phases 22-27 (shipped 2026-06-19)
- ✅ **v6.0 Self-Evolution & Feedback Loop** — Phases 28-33 (shipped 2026-06-24)
- ✅ **v7.0 openclaw → hermes-agent Primary Agent Migration** — Phases 34-37 (shipped 2026-06-25)
- ⏳ **v8.0** — quick-task batch only (P0+P1 openclaw skills, 2026-06-26); label consumed to avoid version collision, not a formal milestone
- 🚧 **v9.0 kais-movie-pipeline 闭环深化** — Phases 38-43 (started 2026-06-26, in planning)

<details>
<summary>✅ v1 through v7.0 (Phases 0-37) — SHIPPED</summary>

For completed milestone phase details, see:
- `.planning/milestones/v1-ROADMAP.md`
- `.planning/milestones/v3.0-ROADMAP.md`
- `.planning/milestones/v4.0-ROADMAP.md`
- `.planning/milestones/v5.0-ROADMAP.md`
- `.planning/milestones/v6.0-ROADMAP.md`
- `.planning/milestones/v7.0-ROADMAP.md`
- `.planning/milestones/v7.0-MIGRATION-REPORT.md` (v7.0 canonical close-out)

</details>

---

## v9.0 — kais-movie-pipeline 闭环深化

**Granularity:** standard (6 phases derived from 6 requirement categories — no compression or padding needed)
**Coverage:** 22 / 22 v1 requirements mapped ✓ (no orphans, no duplicates)
**Model profile:** quality

### Phases

- [x] **Phase 38: SLICE — 平台母版切片 (Step 14)** — 1 master.mp4 → 7 平台 variants with per-platform aspect/hook/length (shipped 2026-06-27)
- [x] **Phase 39: FORM — 配方库 v0 (new plugin)** — `plugins/formula_library/` with 10 seed formulas + `formula_lookup` Step 0 (shipped 2026-06-27)
- [x] **Phase 40: GATE — 3 新审核门** — redline_emotion_desensitize / redline_no_cold_open / redline_unfinished_ending registered as gate 9/10/11 (completed 2026-06-26)
- [x] **Phase 41: PREVIEW — LTX2.3 预览闭环 (Step 6.5)** — fast-preview between storyboard (Step 6) and final render (Step 11), failure → re-storyboard (shipped 2026-06-27)
- [x] **Phase 42: DATA — 数据收敛 (Step 15)** — 5 平台 API adapters → FeedbackStore schema extension → formula tuning loop (shipped 2026-06-27)
- [x] **Phase 43: VALIDATE — 集成验证 + close-out** — cross-phase integration + FOUND-08 audit + canonical v9.0-MILESTONE-AUDIT.md (shipped 2026-06-27)

### Critical Path

```
            ┌── Phase 38 (SLICE)  ───────┐
            │                            ├──→ Phase 42 (DATA)  ──┐
Parallel    ├── Phase 39 (FORM)   ───────┤                      │
wave  ──────┤                            │                      │
(can start  ├── Phase 40 (GATE)   ───────┘                      ├──→ Phase 43 (VALIDATE)
 disjoint)  │                            (DATA needs variants[]  │      strictly LAST
            │                             from SLICE + formulas  │
            │                             from FORM; GATE        │
            │                             suggested_action       │
            │                             references formula)    │
            │                                                    │
            └── Phase 41 (PREVIEW)  ────────────────────────────┘
                  (independent — touches Step 6.5 only)
```

**Dependency rules:**

- **Parallel-eligible wave:** Phase 38 + 39 + 40 + 41 all touch disjoint paths (SLICE → Step 14 in SKILL.md + new ref; FORM → new `plugins/formula_library/` + Step 0 patch; GATE → review_gates registration; PREVIEW → Step 6.5 + new ref). All four may start concurrently.
- **Phase 42 (DATA) depends on Phase 38 + Phase 39.** DATA needs (a) variants[] schema from SLICE to attach per-platform metrics, and (b) formula_library from FORM as the tuning-loop write-back target. GATE is NOT a hard dependency for DATA (GATE's suggested_action references formula as a read-side lookup only).
- **Phase 43 (VALIDATE) strictly LAST.** It runs the cross-5-phase integration-checker + FOUND-08 byte-diff audit + writes the canonical milestone audit. Mirrors v5.0 Phase 27 / v6.0 Phase 33 / v7.0 Phase 37 close-out pattern.
- **FOUND-08 frozen rule preserved milestone-wide.** Zero expert_id / frontmatter changes across all 16 active movie-experts (byte-diff verified at Phase 43 against start commit `a2a20d2be`).

### Coverage Table

| Phase | Requirements | Count |
|-------|--------------|-------|
| 38 — SLICE | SLICE-01, SLICE-02, SLICE-03, SLICE-04 | 4 |
| 39 — FORM | FORM-01, FORM-02, FORM-03, FORM-04 | 4 |
| 40 — GATE | GATE-01, GATE-02, GATE-03, GATE-04 | 4 |
| 41 — PREVIEW | PREVIEW-01, PREVIEW-02, PREVIEW-03 | 3 |
| 42 — DATA | DATA-01, DATA-02, DATA-03, DATA-04 | 4 |
| 43 — VALIDATE | VALIDATE-01, VALIDATE-02, VALIDATE-03 | 3 |
| **Total** | | **22 / 22 ✓** |

### Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 38. SLICE | 1/1 | Complete (Plan 01 shipped 2026-06-27) | 2026-06-27 |
| 39. FORM | 3/3 | Complete (Plans 01+02+03 shipped 2026-06-26 → 2026-06-27) | 2026-06-27 |
| 40. GATE | 3/3 | Complete (Plans 01+02+03 shipped 2026-06-26) | 2026-06-26 |
| 41. PREVIEW | 1/1 | Complete (Plan 01 shipped 2026-06-27) | 2026-06-27 |
| 42. DATA | 4/4 | Complete (Plans 01+02+03+04 shipped 2026-06-27) | 2026-06-27 |
| 43. VALIDATE | 1/1 | Complete (Plan 01 shipped 2026-06-27 — v9.0-MILESTONE-AUDIT.md authored) | 2026-06-27 |

---

## Phase Details

### Phase 38: SLICE — 平台母版切片 (Step 14)

**Goal:** Users can produce 7 platform-specific variants from a single master render, each conforming to that platform's aspect-ratio / hook-position / length rigid constraints, with variant metadata persisted for downstream data tracking.
**Depends on:** Nothing (parallel-eligible wave)
**Requirements:** SLICE-01, SLICE-02, SLICE-03, SLICE-04
**Success Criteria** (what must be TRUE):
1. Given master.mp4 + 7 platform targets (抖音竖屏 9:16 / 抖音横屏 16:9 / 快手竖屏 / B 站横屏 5-10min / 小红书竖屏 3min / 视频号横屏 / 红果或快手极短 1-2min), the pipeline emits 7 variants — each with the correct `aspect_ratio` from `platform-specs.md`'s 7-row matrix.
2. Each variant automatically repositions the opening 3s hook, adjusts mid-segment 卡点 (pinch-point) density, and adds a new closing 3s hook — all per `platform-specs.md` rigid constraints (not manual).
3. Every variant's metadata lands in `pipeline_state.episode_id.variants[]` with fields `platform` / `aspect_ratio` / `length` / `hook_timestamps` / `cut_points`, queryable by the downstream DATA phase.
4. New ref `references/platform-master-slicing.md` documents the 7-variant algorithm + 4 key decision points; `SKILL.md` body contains a new Step 14 section (frontmatter byte-identical to pre-v9.0).
**Plans:** 1 plan
- [x] 38-01-PLAN.md — SLICE: 7-variant algorithm ref + SKILL.md Step 14 body section + variants[] schema doc (4 tasks, 4 reqs) — shipped 2026-06-27 (1 new ref + 3 ref/SKILL patches, FOUND-08 byte-identical)
**UI hint**: no

### Phase 39: FORM — 配方库 v0 (new plugin)

**Goal:** Users can look up proven 爆款 formulas by genre × mood × platform, getting back top-3 matches with full citation + schema, integrated as Step 0 of the pipeline so every episode starts from a verified formula instead of a blank page.
**Depends on:** Nothing (parallel-eligible wave)
**Requirements:** FORM-01, FORM-02, FORM-03, FORM-04
**Success Criteria** (what must be TRUE):
1. New plugin `plugins/formula_library/` is discoverable via existing `hermes_cli/plugins.py` registry — `plugin.yaml` + `__init__.py` + Pydantic `schema.py` + `library/` directory holding 10 seed formula JSON files. No Hermes core code changes (plugin lives in `plugins/` namespace).
2. Each of the 10 seed formulas covers one cell of the 5-genre × 2-mood matrix (都市奇幻 / 悬疑反转 / 家庭情感 / 校园青春 / 职场商战 × 轻喜剧 / 虐心), with every required schema field populated: `formula_id` / `genre` / `mood` / `pacing` / `hook_pattern` / `characters` / `runtime_sec` / `platform_fit[]` / `citation` (fair-use source tag) / `verified_date`.
3. Given a `formula_lookup(genre=都市奇幻, mood=轻喜剧, platform=抖音)` call, the plugin returns the top-3 matching formulas ranked by platform_fit; `kais-movie-pipeline/SKILL.md` exposes this as Step 0 (前置); `theory_critic/SKILL.md` accepts an optional `formula_reference` input. Both SKILL.md changes are body-only (FOUND-08 frontmatter preserved).
4. All 10 formulas carry fair-use citations (Notion 创作方向 / 公开爆款公式书 / kais-movie-agent 历史 benchmark) — no formula lands without a verifiable source.
**Plans:** 3 plans
- [x] 39-01-PLAN.md — Plugin scaffold + Pydantic schema + lookup engine (FORM-01, FORM-02, FORM-04 lookup half) — SHIPPED 2026-06-26 (34 tests)
- [x] 39-02-PLAN.md — 10 seed formulas (5×2 matrix) + LICENSE.md + bilingual README.md (FORM-03) — SHIPPED 2026-06-26
- [x] 39-03-PLAN.md — SKILL.md body patches (Step 0 + formula_reference) + tests + FOUND-08 byte-diff audit (FORM-04) — SHIPPED 2026-06-27 (15 tests; 49 total in plugin)
**UI hint**: no

### Phase 40: GATE — 3 新审核门

**Goal:** The V8.6 review-gate sequence automatically rejects cuts that violate the 3 cross-platform redlines from `creative-redlines.md` (R1 情绪脱敏 / R3 零背景铺垫 / R4 结尾必释放新钩子), with concrete suggested_actions that point operators at the fix.
**Depends on:** Nothing (parallel-eligible wave) — Phase 34 review_gates state machine confirmed stable
**Requirements:** GATE-01, GATE-02, GATE-03, GATE-04
**Success Criteria** (what must be TRUE):
1. Three new gates (`redline_emotion_desensitize` / `redline_no_cold_open` / `redline_unfinished_ending`) are registered on the existing `plugins/review_gates/gate.py` state machine and load via `gates.yaml` — no replacement of the existing 8 gates (additive only).
2. Given a cut with ≥3 consecutive frames at the same emotional valence, `redline_emotion_desensitize` returns `reject` with a `suggested_action` describing how to break it up (per `creative-redlines.md` R1). Given a cut whose first 3s contains 背景铺垫, `redline_no_cold_open` rejects with suggested_action (per R3). Given a cut whose final 3s releases no new hook, `redline_unfinished_ending` rejects with suggested_action (per R4).
3. Gate 9 / 10 / 11 fire in the correct sequence: after the existing 8 gates pass, gates 9-11 do one final scan before final delivery — documented in `references/review-gates.md` (additive; V8.6 8-gate numbering unchanged).
4. The `suggested_action` field on each new gate is structured so it can reference a `formula_library` entry (read-side lookup) for the operator to apply a proven fix pattern.
**Plans:** 3/3 plans complete
- [x] 40-01-PLAN.md — 3 pure-stdlib redline detectors (R1/R3/R4) + test suite (TDD) — shipped 2026-06-27 (54 tests, DETECTOR_REGISTRY wired)
- [x] 40-02-PLAN.md — gates.yaml 8→11 additive + gate_config.py count bump + runner_hooks auto-detect + tools.py dispatch (TDD)
- [x] 40-03-PLAN.md — references/review-gates.md 8→11 doc + plugin README update
**UI hint**: no

### Phase 41: PREVIEW — LTX2.3 预览闭环 (Step 6.5)

**Goal:** Users can catch composition / framing / pacing problems in ~5 seconds (LTX2.3 fast-preview) right after storyboard, before committing GPU budget to the full final render — with an automatic re-storyboard fallback on miss.
**Depends on:** Nothing (parallel-eligible wave — touches Step 6.5 only)
**Requirements:** PREVIEW-01, PREVIEW-02, PREVIEW-03
**Success Criteria** (what must be TRUE):
1. New ref `references/ltx2-preview-loop.md` documents the LTX2.3 baseline: model selection (LTX2.3 / CausVid / Kling 1.6 fast), ~5s generation budget, 3-dimension check thresholds (composition / framing / pacing), and the prompt template.
2. `kais-movie-pipeline/SKILL.md` wires a new Step 6.5: after storyboard (Step 6) passes, the pipeline automatically invokes LTX2.3 fast-preview; preview must pass before Step 7 (dreamina CLI final render) is invoked. Frontmatter byte-identical to pre-v9.0 (FOUND-08).
3. Failure path is deterministic: pacing deviation > 15% OR framing deviation > 10% triggers automatic fallback to Step 6 (re-storyboard), max 2 retries; exhausting 2 retries routes to operator review via the existing `plugins/review_gates/` BLOCKING mode (no silent skip).
4. **Operator-action-handoff:** live GPU generation testing is operator-side — v9.0 ships the baseline doc + adapter skeleton only. V9-FUTURE-02 (real LTX2.3 model generation validation) is explicitly deferred.
Plans:
- [x] 41-01-PLAN.md — Step 6.5 LTX2.3 fast-preview wiring (4 tasks: new ref + SKILL.md body patch + DAG annotation + FOUND-08 verification) — SHIPPED 2026-06-27 (3 commits + SUMMARY; FOUND-08 byte-verified; V8.6 13-step + 8-gate preserved)
**UI hint**: no

### Phase 42: DATA — 数据收敛 (Step 15)

**Goal:** Users can wire platform performance metrics (完播率 / 卡点跳出率 / 互动率 / 收藏率 / 评论率) back into the v6.0 FeedbackStore, per-platform bucketed, with an automatic tuning loop that suggests formula_library improvements and a CLI dashboard for inspection.
**Depends on:** Phase 38 (SLICE — needs `variants[]` to attach per-platform metrics) + Phase 39 (FORM — needs formula_library as tuning-loop write-back target)
**Requirements:** DATA-01, DATA-02, DATA-03, DATA-04
**Success Criteria** (what must be TRUE):
1. Five platform API adapter stubs exist (抖音开放平台 / 快手开放平台 / 视频号 / 小红书薯条 / B 站创作者), each emitting a unified `PlatformMetrics` Pydantic schema; activating any adapter requires only an operator-supplied `~/.hermes/.env` key (e.g. `DOUYIN_API_KEY`) — no code change. Live ingestion itself is operator-side (V9-FUTURE-01 deferred).
2. The v6.0 `FeedbackRecord` schema gains a `platform_metrics` field bucketed per platform with `completion_rate` / `hook_dropoff_rate` / `engagement_rate` / `save_rate` / `comment_rate`; existing v6.0 records remain backward-compatible (additive field).
3. The `formula_tuning_loop` converts convergent metrics into suggestions: high hook-dropoff → suggest stronger hook; high completion but low engagement → suggest CTA. Suggestions land in a JSONL review queue (reusing the v6.0 EVOL-02 queue pattern); after operator approval they write back to `plugins/formula_library/`.
4. `hermes formula stats` prints rich per-formula / per-platform tables; `--json` flag emits counts-only for scripting.
5. New ref `references/data-convergence.md` documents the data flow + dashboard usage. **Operator-action-handoff:** 5 平台 API keys 由 operator 配置后激活; v9.0 提供 schema + adapter 骨架 only.
**Plans:** 4 plans
- [x] 42-01-PLAN.md — Plugin scaffold + PlatformMetrics + FeedbackRecordExtension + adapter base class + tests (DATA-01 schema + DATA-02 composition) — SHIPPED 2026-06-27
- [x] 42-02-PLAN.md — 5 platform adapter stubs (douyin/kuaishou/weixin_video/xiaohongshu/bilibili) + adapter registry + tests (DATA-01 adapter half) — SHIPPED 2026-06-27
- [x] 42-03-PLAN.md — tuning_loop + library_writer + JSONL review queue integration tests (DATA-03) — SHIPPED 2026-06-27 (35/35 tests; HIL invariant via SuggestionNotApprovedError + AST-walk single-caller; 4 MetricTrigger rules; atomic eval_score write-back; v6.0 EVOL-02 pattern mirrored, not imported)
- [x] 42-04-PLAN.md — hermes formula stats CLI + data-convergence.md ref + SKILL.md Step 15 + pipeline-dag.md annotation + .env.example patch (DATA-04) — SHIPPED 2026-06-27
**UI hint**: yes

### Phase 43: VALIDATE — 集成验证 + close-out

**Goal:** Cross-5-phase integration-checker passes end-to-end, FOUND-08 is verified preserved milestone-wide via byte-diff, and the canonical v9.0-MILESTONE-AUDIT.md is published as the milestone's permanent close-out record.
**Depends on:** Phase 38, 39, 40, 41, 42 (strictly LAST)
**Requirements:** VALIDATE-01, VALIDATE-02, VALIDATE-03
**Success Criteria** (what must be TRUE):
1. The cross-5-phase integration-checker all-pass: SLICE outputs `variants[]` → DATA adapter consumes them; FORM `formula_lookup` → GATE `suggested_action` references the returned formula; PREVIEW failure fallback to Step 6 does NOT break the existing 13-step I/O contract.
2. FOUND-08 preserved milestone-wide: byte-diff of all 16 active movie-experts' `expert_id` + frontmatter against v9.0 start commit `a2a20d2be` shows zero changes. Any SKILL.md body patch is body-only.
3. Canonical `.planning/milestones/v9.0-MILESTONE-AUDIT.md` published with: 22/22 req coverage table + 6/6 phase outcome summary + integration matrix + FOUND-08 evidence chain + operator-action-handoffs documented (Phase 41 LTX2.3 GPU testing + Phase 42 platform API keys).
4. Operator-action-handoffs explicitly enumerated in the audit (NOT gaps, per scoped-boundary design): (a) LTX2.3 live GPU generation validation; (b) 5 平台 API key 配置 + live data ingestion.
**Plans:** TBD
**UI hint**: no

---

*Last updated: 2026-06-27 — Phase 43 VALIDATE complete. v9.0 milestone 6/6 phases done, 13/13 plans done, 22/22 reqs satisfied. FOUND-08 preserved milestone-wide (30 SKILL.md frontmatter byte-identical to `a2a20d2be`). Audit: `.planning/milestones/v9.0-MILESTONE-AUDIT.md`. Ready for `git tag v9.0` + `/gsd:complete-milestone v9.0` (operator actions).*
