---
gsd_state_version: 1.0
milestone: v6.0
milestone_name: Self-Evolution & Feedback Loop
status: milestone_complete
last_updated: "2026-06-25T23:20:00.000Z"
last_activity: 2026-06-25 -- Phase 33 Plan 03 complete; v6.0 milestone SHIPPED (SC-6/7/8 all PASS, FOUND-08 preserved)
progress:
  total_phases: 6
  completed_phases: 6
  total_plans: 13
  completed_plans: 13
  percent: 100
---

# State: Movie-Experts Suite v2 (MESV2)

## Project Reference

**Project code:** MESV2
**Name:** Movie-Experts Suite v2 — 短剧/微电影创作专家增强
**Core value:** 每个 movie-expert skill 都能用检索增强的方式调用行业知识库,让 AI 生成的短剧/微电影在专业度上接近人类创作者水平。
**Key docs:** `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/MILESTONES.md`, `.planning/REQUIREMENTS.md`, `.planning/research/v2-pipeline-design/skills-mapping.yaml`
**Mode:** yolo (auto-advance, parallelization on)
**Granularity:** standard
**Model profile:** quality
**Current focus:** v6.0 milestone SHIPPED — all 6 phases (P28-P33) complete; ready for tag + archive

## Current Position

Phase: 33 (COMPLETE)
Plan: 03 (DONE — final plan of v6.0 milestone)
Status: v6.0 milestone complete; all 13 plans shipped; SC-1 through SC-8 all PASS
Last activity: 2026-06-25 -- Phase 33 Plan 03 complete (README + glossary + SC-7/SC-8 byte-intact checks); v6.0 milestone SHIPPED

### Progress

```
v1 milestone:                  [██████████] 100% Complete (Phases 0-6, shipped 2026-06-15)
v2.0 PRFP milestone:           [██████████] 100% Complete (Phases 7-12, shipped 2026-06-16)
v3.0 Skills-to-DAG Alignment:  [██████████] 100% Complete (Phases 13-18, shipped 2026-06-17)
v4.0 Methodology Backfill:     [██████████] 100% Complete (Phases 19-21, shipped 2026-06-18)
v5.0 kais-movie-agent V8.6 Adaptation:
                               [██████████] 100% Complete (Phases 22-27, shipped 2026-06-19)

v6.0 Self-Evolution & Feedback Loop:
  Phase 28 (Feedback Ingestion MVP)        [██████████] 100% Complete (Plan 01 schema+snapshot+write; Plan 02 CLI+watcher+JSONL — 76 tests green, FOUND-08 verified)
  Phase 29 (Feedback Store)                [██████████] 100% Complete (Plan 01 FeedbackStore foundation 49 tests; Plan 02 STORE-04 dedup + delegation + rebuild-index CLI — 26 new tests, 150/151 feedback-subsystem green, Phase 29 closed)
  Phase 30 (Eval Gate Reuse)               [██████████] 100% Complete (Plan 01 parse_judge_scores + gate.py orchestrator GATE-02/04 — 43 tests; Plan 02 paired-t significance + rebuild_baseline + multi-skill guard GATE-01/03 — 30 tests; 100/101 eval tests green, FOUND-08 + runtime isolation + scipy-free verified; Phase 30 CLOSED)
  Phase 31 (Knowledge Evolution Pipeline)  [██████████] 100% Complete (Plan 01 engine layer — 60 tests; Plan 02 CLI layer — 27 tests; 87/87 green, EVOL-04 non-bypassable human-in-loop structurally enforced via TestNonBypassableHumanInLoop ast-walk, runtime isolation 0 matches, FOUND-08 byte-intact, RESEARCH 3/3 RESOLVED; Phase 31 CLOSED)
  Phase 32 (Curator Upgrade + Audit)       [██████████] 100% Complete (Plan 01 engine — 55 tests, 4 commits; Plan 02 CLI + CURATE-05 — 34 tests, 2 commits; 328 combined green, Option A preserves P31 TestNonBypassableHumanInLoop UNCHANGED, runtime isolation 0, FOUND-08 byte-intact; Phase 32 CLOSED)
  Phase 33 (Observability + Close-out)     [██████████] 100% Complete (Plan 01 stats CLI + Plan 02 architecture doc + skills-mapping sign-off + Plan 03 README/glossary/byte-intact close-out — 42 tests in test_curator_stats.py, OBS-01/02/03 + SC-4/SC-5/SC-6/SC-7/SC-8 all satisfied; v6.0 milestone SHIPPED)
```

### Phase Statuses (v6.0)

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 28 | Feedback Ingestion MVP | **Complete** | Shipped 2026-06-24. INGEST-01..05 covered. Plan 01 (schema + snapshot + atomic write — 45 tests) + Plan 02 (/feedback slash cmd + hermes feedback {import,watch,submit} + kais file watcher + JSONL atomic batch import — 31 new tests). 76/76 tests green, Ruff clean, FOUND-08 preserved, zero new deps. |
| 29 | Feedback Store | **Complete** | Shipped 2026-06-24. STORE-01..04 satisfied. Plan 01 FeedbackStore foundation (49 tests, 2 Rule 1 bugs auto-fixed). Plan 02 STORE-04 sha256 dedup/correction branch + Phase 28 write_feedback_record delegation + rebuild_index method + hermes feedback rebuild-index CLI (26 new tests across TestDedup/TestCorrection/TestRebuildIndex/TestDelegation/TestRebuildIndexCLI; 150/151 feedback-subsystem green, 1 documented skip; 2 deviations auto-fixed). Phase 29 closed. |
| 30 | Eval Gate Reuse | **Complete** | Shipped 2026-06-24. GATE-01..04 all covered. Plan 01: parse_judge_scores() + composite_score() in runner.py + gate.py orchestrator (patch mechanics + decide_verdict + config + CLI) — 43 new tests. Plan 02: paired_t_stats() + is_significant() via stdlib statistics + hardcoded _CRITICAL_T_05_TWO_TAILED t-table (GATE-03, no scipy) + rebuild_baseline() with scores.json provenance cache + load_cached_baseline() with non-blocking staleness warning + detect_multi_skill_patch() with exit-3 early-exit guard + --rebuild-baseline/--multi-skill CLI flags — 30 new tests. 100/101 eval tests green (1 pre-existing openai-missing skip), FOUND-08 byte-intact, runtime isolation 0, scipy-free. Phase 30 CLOSED. |
| 31 | Knowledge Evolution Pipeline | **Complete** | Shipped 2026-06-24. EVOL-01/03/04/05 fully covered. Plan 01: agent/evolution/ subpackage (insights LLM aggregation + difflib diff generator + JSONL queue + atomic apply transaction + FOUND-08 byte-intact + additive-only verifier) — 60 new tests, 7 commits. Plan 02: hermes_cli/feedback.py extended with 6 new subcommands (evolve / review-queue / show-patch / approve / reject / rollback) + TestNonBypassableHumanInLoop ast-walk structural invariant (only _cmd_approve calls apply_patch_transaction) — 27 new tests, 3 commits. 87/87 combined green, runtime isolation 0 matches, FOUND-08 byte-intact (0 SKILL.md changes), RESEARCH 3/3 Open Questions RESOLVED, VALIDATION nyquist_compliant=true. Phase 31 CLOSED. |
| 32 | Curator Upgrade + Audit | **Complete** | Shipped 2026-06-25. CURATE-01..05 + EVOL-02 fully covered. Plan 01: agent/curator_audit.py (sha256-chained JSONL append/verify/read + 2 fixtures), agent/evolution/evol02_generator.py (multi-instruction bilingual diff generator extending P31 placeholder), agent/curator.py additive _feedback_scan_phase (lazy imports, try/except isolation, bundled-never-auto), PatchRecord additive extension (auto_apply_eligible + confidence_score) — 55 new tests, 4 commits. Plan 02: hermes_cli/curator.py register_cli extended with 5 new subparsers (queue / approve / reject / audit-log / auto-apply-eligible), _cmd_approve in hermes_cli/feedback.py extended to call append_audit(action="apply") on success (single source of truth per RESEARCH A4), CURATE-05 Option A auto-apply (delegates to _cmd_approve — apply_patch_transaction still called only from _cmd_approve) — 34 new tests, 2 commits. 328 combined green (55+34 new + 27 P31 CLI + 267 engine regression - overlap), P31 TestNonBypassableHumanInLoop passes UNCHANGED (Option A — zero test amendment), apply_patch_transaction Call nodes in hermes_cli/curator.py = 0, runtime isolation 0 module-level agent.evolution imports, FOUND-08 byte-intact. Phase 32 CLOSED. |
| 33 | Observability + Integration Close-out | **Complete** | Shipped 2026-06-25. OBS-01/02/03 + SC-4/5/6/7/8 all satisfied. Plan 01 (stats CLI — `hermes curator stats [skill_id|--all|--by-source]` + 18 tests). Plan 02 (`_shared/v6-feedback-loop-architecture.md` 305 lines + skills-mapping.yaml `v6_ref_signoffs:` 1 entry + 14 doc/schema tests). Plan 03 (README corpus tree `_shared/` block lists v6 architecture doc + glossary v6.0 section with 4 EN-first H3 entries: Curator Proposal / Eval Gate / Feedback Ingestion / Knowledge Evolution + footer note + 10 new tests). 42 tests in test_curator_stats.py all green; Ruff clean; runtime isolation 0; FOUND-08 byte-intact milestone-wide (SC-7: 0 lines; SC-8: 5 refs unchanged). **v6.0 milestone SHIPPED.** |

### Critical Path

```
Phase 28 (Feedback Ingestion MVP)  ──→  Phase 29 (Feedback Store)  ──┐
                                                                      │
                                       ┌──────────────────────────────┤
                                       │                              │
                                       ▼                              ▼
                                   Phase 30                      Phase 31     ← parallel wave
                                   (Eval Gate)              (Evolution Pipeline)  (disjoint files,
                                       │                              │          share only P28 schema)
                                       └──────────┬───────────────────┘
                                                  ▼
                                         Phase 32 (Curator Upgrade + Audit)
                                                  │  (extends agent/curator.py +
                                                  │   implements EVOL-02 diff generator)
                                                  ▼
                                         Phase 33 (Observability + Close-out)  ← MUST run last
```

Phase 28 must run first (ships the core functional guarantee). Phase 29 depends on P28. Phases 30 + 31 are parallel-eligible (disjoint file ownership). Phase 32 consumes P29 + P31 review queue + implements EVOL-02. Phase 33 is strictly last (close-out + canonical doc).

## Quick Tasks Completed

| Quick ID | Date | Slug | Description | Deliverable |
|----------|------|------|-------------|-------------|
| 260617-wgz | 2026-06-17 | write-gap-analysis-doc-comparing-creativ | Gap-analysis 对照调研报告 §7.2 6 阶段蓝图 vs movie-experts 实际覆盖;高 ROI 缺口排序(雪花法 / E-Konte / SCAMPER) | `.planning/research/methodology-gap-analysis-2026-06-17.md` |

## Performance Metrics (v6.0)

- v6.0 phases total: 6 (Phases 28-33, continuing from v5.0 phase 27)
- v6.0 phases completed: 6 (Phase 28 — Feedback Ingestion MVP; Phase 29 — Feedback Store; Phase 30 — Eval Gate Reuse; Phase 31 — Knowledge Evolution Pipeline; Phase 32 — Curator Upgrade + Audit; Phase 33 — Observability + Integration Close-out)
- v6.0 requirements total: 26
- v6.0 requirements mapped: 26 / 26 ✓
- v6.0 requirements orphaned: 0
- v6.0 requirements completed: 26 / 26 (INGEST-01..05 + STORE-01..04 + GATE-01..04 + EVOL-01..05 + CURATE-01..05 + OBS-01..03) — ALL COMPLETE
- v6.0 plans completed: 13 / 13 (Phase 28 Plan 01 + Plan 02 + Phase 29 Plan 01 + Plan 02 + Phase 30 Plan 01 + Plan 02 + Phase 31 Plan 01 + Plan 02 + Phase 32 Plan 01 + Plan 02 + Phase 33 Plan 01 + Plan 02 + Plan 03) — ALL COMPLETE
- v6.0 success criteria satisfied: SC-1 through SC-8 all PASS (SC-6/7/8 closed by Phase 33 Plan 03)
- Deliverable form: MIXED — Hermes core touch (agent/curator.py extension + feedback ingestion infra in P28/P29/P32) + pure skill layer (additive SKILL.md / refs patches via P31 + canonical doc in P33). This is the v5→v6 scope expansion explicitly accepted in PROJECT.md.

## Accumulated Context

### v6.0 Goal Restatement

让 movie-experts skill suite 从「静态知识层」进化为「带反馈闭环的自学习系统」:

1. **反馈采集 (INGEST)** ⭐ MVP 核心 —— 多源接入:CLI 用户反馈 + kais-aigc-platform 审核反馈 + 手工标注;标准化 JSON schema `{skill_id, expert_id, source, verdict, correction, output_snapshot, ts}`
2. **反馈存储 (STORE)** —— `~/.hermes/skills/.feedback/` 持久化 + 时间衰减权重 + 按 skill 索引 + 去重
3. **eval 基线复用 (GATE)** —— 复用既有 `_eval/runner.py` MT-Bench position-swap harness 做 patch-vs-baseline gate,δ=0.3 平均阈值 + 1.0 单 prompt regression guard + A/B 双盲
4. **知识抽取 (EVOL)** —— LLM 抽取 candidate insights → unified-diff candidate patch → eval gate → review queue → human-in-loop approve → git-commit-on-apply + rollback
5. **Curator 升级 (CURATE)** —— `agent/curator.py` 从「只 archive agent-created」扩展为「能 propose patch 给 bundled skill」;audit log;operator CLI;agent-created skill 半自动路径
6. **可观测性 (OBS)** —— per-skill dashboard + cross-skill view + source breakdown

**核心范式跃迁:** 从 v1-v5 的「人工 curate 静态知识」转为「反馈驱动动态学习」。这是 movie-experts 第一次真正具备 self-improvement 能力。

**范围扩张 (v5→v6):** v6 不再是「纯 skill 内容交付」,需要触动 Hermes 核心 —— `agent/curator.py` 扩展、新增反馈接入 endpoint 或文件 watcher。这是用户在 PROJECT.md 中明确接受的 scope shift。

### Decisions (v6.0 — entered planning)

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 6 phases continuing from v5.0 phase 27 (28, 29, 30, 31, 32, 33) | Project maintains sequential phase numbering; decimal phases reserved for urgent insertions only. v5.0 ended at P27; `--reset-phase-numbers` NOT passed. | Applied 2026-06-24 — ROADMAP.md phase numbering 28-33 |
| Phase 28 (Feedback Ingestion MVP) runs FIRST | P28 ships the core functional guarantee (every expert can receive feedback after giving opinions). INGEST + STORE must ship before EVOL/CURATE can consume the feedback. MVP-first ordering per instructions. | Applied 2026-06-24 — ROADMAP critical path annotated |
| Phases 30 + 31 are parallel-eligible | Disjoint file ownership: P30 extends `skills/movie-experts/_eval/runner.py` (offline dev tooling, no runtime touch per its module docstring) + adds gate scripts; P31 builds patch-generation pipeline under `~/.hermes/skills/.feedback/` tooling + new modules. They share only the JSON schema contract from P28. Zero file overlap. | Applied 2026-06-24 — ROADMAP critical path notes parallel wave |
| Phase 33 (Integration Close-out) runs LAST | P33 references P28-32 + writes canonical `_shared/v6-feedback-loop-architecture.md` + skills-mapping.yaml `v6_ref_signoffs:` + README + glossary. Must close after all feedback-loop phases ship. Mirrors v5.0 Phase 27 pattern. | Applied 2026-06-24 — ROADMAP critical path annotated |
| EVOL-02 mapped to Phase 32 (not Phase 31) | The candidate-patch generator is invoked BY the Curator's proposal path in practice (CURATE-01 extends curator to propose patches, which uses EVOL-02's diff generator as its engine). Phase 31 builds the review queue + approve/apply mechanics; Phase 32 implements EVOL-02 as the engine Curator calls. Keeps dependency graph clean. | Applied 2026-06-24 — REQUIREMENTS.md traceability + ROADMAP.md coverage table reflect this |
| Hermes core touch accepted (v5→v6 scope expansion) | v6 (unlike v1-v5) modifies `agent/curator.py` (CURATE-01) + adds new ingestion endpoints/watchers (INGEST-02). This is explicitly accepted in PROJECT.md §"Current Milestone: v6.0" Key context. Pure-skill phases still occur but core touch is unavoidable. | Applied 2026-06-24 — P28 + P29 + P32 success criteria all annotate "Hermes-core touch: Yes" |
| FOUND-08 + scope discipline carried from v3.0 onward | Every phase verifies "no new expert_id, no DAG node change, no v5/v4 ref byte-change". P31 SC #5-6 + P33 SC #7-8 explicitly check. | Applied 2026-06-24 — every phase touching bundled SKILL.md has explicit preservation criterion |
| stdlib os.scandir polling for kais-aigc watcher (no watchdog dep) | Portable across Linux/macOS/Windows/Termux (CONTEXT.md Claude's-discretion). 1s default interval fast enough for batch file-exchange. Watchdog-style cross-platform Observer adds zero MVP benefit. | Applied 2026-06-24 — P28 Plan 02 watch_inbox_kais() ships stdlib-only polling |
| Atomic all-or-nothing JSONL batch import | CONTEXT.md D-INGEST-03 recommendation. On any line error returns (0, errors) WITHOUT writing — preserves operator trust. Line-numbered errors with field-level Pydantic messages. | Applied 2026-06-24 — P28 Plan 02 import_jsonl() atomic contract enforced by tests |
| Anti-spoofing source override in kais watcher | Crafted file in inbox-kais/ cannot pollute 'cli' or 'manual' provenance. Watcher FORCES raw['source'] = 'kais_aigc' regardless of JSON content. | Applied 2026-06-24 — P28 Plan 02 T-28-07 mitigation in _scan_once() |
| /feedback skill_id resolution via _SKILL_INVOCATION_PREFIX marker scan | Verified format in agent/skill_commands.py:550-553. Backward scan for most recent user msg starting with the marker, regex-extract quoted skill name. When no marker found, clear error + write nothing — never silently default. | Applied 2026-06-24 — P28 Plan 02 HermesCLI._handle_feedback_command (Pitfall #4 mitigation) |
| Plan 01 ships record_feedback WITHOUT STORE-04 dedup branch | Plan scope split per plan <objective>: Plan 01 = storage foundation; Plan 02 = dedup + wrapper delegation. TODO comment in source marks the exact insertion point for the sha256 dedup check. | Applied 2026-06-24 — P29 Plan 01 record_feedback unconditional write |
| Index bucket count filters by verdict within shared source file | The bucket FILE is keyed by (skill_id, source) but the index bucket KEY is keyed by (skill_id, source, verdict). Auto-fixed Rule 1: filter to verdict_records = [r for r in all_records if r.verdict == record.verdict] before counting. | Applied 2026-06-24 — P29 Plan 01 record_feedback (Rule 1 bug fix) |
| __init__ order: _load_or_init_index BEFORE _maybe_migrate_phase28_incoming | Migration calls record_feedback which needs self._index. Reordered so index loads first. | Applied 2026-06-24 — P29 Plan 01 FeedbackStore.__init__ (Rule 1 bug fix) |
| Supersession tracked via _superseded_record_ids set (record_id-keyed) | by_sha256 is sha-keyed (one active entry per sha), but a sha can be superseded multiple times (chain of 3+ corrections). Set membership handles chains cleanly + supports query() filtering by record_id. | Applied 2026-06-24 — P29 Plan 02 FeedbackStore.__init__ + _load_sha256_index |
| Older bucket weighted_count recomputed on correction | record_feedback only recomputes the newer verdict's bucket; without _recompute_single_bucket(older_bucket_key), the older verdict bucket retains stale weight>0 after its only record is superseded. Auto-fixed Rule 1. | Applied 2026-06-24 — P29 Plan 02 _handle_dedup (Rule 1 bug fix) |
| Phase 28 test_rejects_when_hermes_home_unwritable SKIPPED on delegation path | Phase 29 delegation triggers hermes_cli.config.ensure_hermes_home which resets skills/ mode before the chmod-0500 trick can bite. Invariant tested directly on FeedbackStore in TestFeedbackStoreInit instead. | Applied 2026-06-24 — P29 Plan 02 tests/agent/test_feedback_ingest.py (Rule 3 fix) |
| write_feedback_record return value semantics: bucket path (not per-record path) | Phase 29 delegation returns buckets/<skill_id>/<source>.jsonl, not Phase 28 per-record incoming/*.json. Safe change — callers use path for display only. | Applied 2026-06-24 — P29 Plan 02 agent/feedback_ingest.py |
| parse_judge_scores silently drops out-of-range/non-numeric/missing dims (fail-safe empty dict) | Caller decides how to treat absence. Gate treats empty dict as a failed prompt (excluded from n_valid, counts toward min_prompts floor). No imputation — a judge that ignores the output format is unreliable. | Applied 2026-06-24 — P30 Plan 01 runner.py parse_judge_scores |
| run_position_swap extended additively (raw_ab, raw_ba, scores_ab, scores_ba keys) | Backward-compat: existing prompt_id/ordering_ab/ordering_ba/final keys unchanged. All pre-existing test_runner.py tests still pass. | Applied 2026-06-24 — P30 Plan 01 runner.py run_position_swap |
| decide_verdict per_prompt_threshold boundary is strict-less-than (exact -1.0 passes) | A drop of exactly -1.0 does NOT trigger fail_regression; only drops < -1.0 do. Boundary tested in test_regression_boundary_passes. | Applied 2026-06-24 — P30 Plan 01 gate.py decide_verdict |
| Baseline cache lazy-populates on first run (candidate becomes baseline for next run) | When baseline_scores_cache is missing, candidate composites are cached as the baseline for the next gate run. First run mean_delta=0 -> pass. Avoids blocking the pipeline on first invocation. | Applied 2026-06-24 — P30 Plan 01 gate.py run_gate step 6 |
| revert_patch handles patch-added files via git clean -f <path> (scoped) | git checkout -- fails on files not in HEAD. Detect via git cat-file -e HEAD:<path>; added files get git clean -f <path> (scoped to specific paths, NOT blanket clean — worktree safety). | Applied 2026-06-24 — P30 Plan 01 gate.py revert_patch |
| p_value always None in paired_t block (stdlib cannot compute t-distribution CDF) | stdlib-only convention (snapshot.py:14) forbids scipy. Operators interpret significance via significant_at_0.05 boolean + raw t_stat + df + note explaining the omission. No "two code paths" maintenance cost. | Applied 2026-06-24 — P30 Plan 02 gate.py paired_t_stats |
| is_significant conservative round-down for unlisted df<30 | df=12 uses df=10's critical value 2.228 (the largest listed df <= requested). Errs toward non-significance — avoids false-positive significance claims. df>30 uses asymptotic normal 1.960. | Applied 2026-06-24 — P30 Plan 02 gate.py is_significant |
| Multi-skill guard runs BEFORE apply_patch (no working-tree mutation on early exit) | T-30-07 mitigation. detect_multi_skill_patch() returns set of skills touched; if >1 and --multi-skill absent, run_gate returns inconclusive (exit 3) without applying the patch. Operator passes --multi-skill to bypass. | Applied 2026-06-24 — P30 Plan 02 gate.py run_gate |
| rebuild_baseline evaluates baseline-vs-self (baseline_answers as BOTH inputs) | Produces per-prompt composites for the current skill on the benchmark. evaluate_candidate is called with baseline_answers as both baseline_answers and candidate_answers — the judge sees the same answer in both slots, giving us the baseline's score distribution. | Applied 2026-06-24 — P30 Plan 02 gate.py rebuild_baseline |
| load_cached_baseline NON-BLOCKING on staleness (RESEARCH Pitfall 4) | Warns on sha mismatch (cached vs current SKILL.md sha256) but returns cached composites anyway. Operator decides whether to refresh via --rebuild-baseline. Avoids friction on every gate run. | Applied 2026-06-24 — P30 Plan 02 gate.py load_cached_baseline |
| scores.json atomic write (temp + os.replace) | T-30-09 mitigation against --rebuild-baseline overwrite being destructive on partial write. Temp file written first, then atomically renamed into place. | Applied 2026-06-24 — P30 Plan 02 gate.py rebuild_baseline |
| run_gate step 6 dual-format baseline cache support | Plan 02 scores.json (dict with per_prompt_composites + sha256 provenance) AND Plan 01 legacy plain-list JSON both supported. Backward-compat preserved for existing tests + first-run lazy population. | Applied 2026-06-24 — P30 Plan 02 gate.py run_gate |
| EVOL-02 placeholder uses stdlib difflib (LLM emits structured add-after-marker) | LLMs unreliable at @@ -A,B +C,D @@ hunk syntax (RESEARCH A1). difflib.unified_diff is deterministic, testable, git-compatible. P32 will extend with LLM-generated rewrites. | Applied 2026-06-24 — P31 Plan 01 agent/evolution/diff_generator.py |
| Additive-only check is UNIVERSAL (all evolution patches) not just protected_refs | Plan action step 5d specified protected-only, but behavior bullet + EVOL-02 scope discipline require ALL evolution patches to be additive. Protected refs get explicit SC-6 error message; other files get generic additive-only message. | Applied 2026-06-24 — P31 Plan 01 agent/evolution/apply.py (Rule 2 auto-fix) |
| Deferred openai import in make_aggregation_client | RuntimeError on missing OPENROUTER_API_KEY must surface before SDK import. In envs without openai installed, top-of-function import masked the key-check error. | Applied 2026-06-24 — P31 Plan 01 agent/evolution/insights.py (Rule 1 auto-fix) |
| Local _extract_patched_files copy (gate.py under hyphenated path not importable) | skills/movie-experts/_eval/gate.py cannot be imported via normal Python import (hyphen in path). Reimplemented the T-30-01 path-traversal + WR-07 deletion-patch hardening locally with a code comment pointing to the canonical source. | Applied 2026-06-24 — P31 Plan 01 agent/evolution/apply.py |
| Audit log at agent/curator_audit.py (NOT agent/evolution/audit.py) | agent/curator.py IS Hermes runtime and imports the audit module. P31 invariant forbids agent/evolution/ imports by runtime. Placing the audit module under agent/evolution/ would force curator to import from the forbidden subpackage. | Applied 2026-06-25 — P32 Plan 01 agent/curator_audit.py |
| EVOL-02 build-final-state-then-diff-once | Multi-instruction same-file patches require applying all instructions to a working copy sequentially, then emitting ONE difflib.unified_diff. Otherwise the second instruction's anchor offset is wrong (it's in the pre-mutation content). | Applied 2026-06-25 — P32 Plan 01 agent/evolution/evol02_generator.py |
| EVOL-02 idempotent guard strengthened (block-already-present check) | P31's full-line-set equality guard (`working == original_lines`) never fires when re-running the same instruction because the generator always adds lines. New check compares block lines to existing lines immediately after the anchor. | Applied 2026-06-25 — P32 Plan 01 agent/evolution/evol02_generator.py (Rule 1 auto-fix) |
| Distinct UTC calendar days as session proxy (Open Q #1 RESOLVED) | FeedbackRecord has no session_id field (verified in agent/feedback_schema.py). Using distinct UTC days from record.ts.date() as the session-diversity proxy is the closest available approximation. Documented in _scan_for_hot_skills docstring for reviewability. | Applied 2026-06-25 — P32 Plan 01 agent/curator.py |
| FeedbackStore constructed via hermes_home kwarg (not root) | Plan referenced FeedbackStore(root=...) but P29 actual signature is FeedbackStore(hermes_home=...). Auto-fixed Rule 1. | Applied 2026-06-25 — P32 Plan 01 agent/curator.py (Rule 1 auto-fix) |
| Phase 33 stats CLI mirrors P32 register_cli extension pattern exactly | Plan 01 adds `stats` subparser to the same register_cli P32 extended; all agent.evolution imports live INSIDE _cmd_stats body (lazy). P31 runtime-isolation invariant TestLazyImportIsolation ast-walk passes UNCHANGED. Zero new deps (rich 14.3.3 already pinned). | Applied 2026-06-25 — P33 Plan 01 hermes_cli/curator.py (_cmd_stats + _render_* helpers) |
| Phase 33 stats --json emits COUNTS ONLY (no correction/output_snapshot/feedback_ids) | T-33-01 information-disclosure mitigation: operator-authored correction text may contain PII. --json payload contains only verdict_buckets + patch_count + eval_trend_count + recent_commit_shas. TestJsonOutput asserts no "correction" key anywhere in the JSON tree. | Applied 2026-06-25 — P33 Plan 01 _render_per_skill_dashboard as_json branch |
| Phase 33 empty-store returns exit 0 + friendly message (mirrors P32 _cmd_audit_log) | Read-only observability commands should never error on empty data. Operator sees "no feedback yet — run /feedback in a Hermes conversation or hermes feedback import <jsonl> to seed data" instead of a stack trace or silent pass. | Applied 2026-06-25 — P33 Plan 01 _empty_store_message() |
| Phase 33 architecture doc mirrors v86-pipeline-mapping.md 10-section structure (7 content + 3 footer) | CONTEXT.md "7 sections" was a logical outline; RESEARCH §v86 audit RESOLVED that v86 actually has 10 H2 sections. Doc adopts 7 content sections (Overview / Data Flow / JSON Schema / Thresholds / Human-in-Loop / Module Ownership / Roadmap Refs) + 3 v86 footer sections (Refresh Cadence / See Also / Source Citation). ASCII data flow diagram (no mermaid). Bilingual EN body + CN section headers. | Applied 2026-06-25 — P33 Plan 02 _shared/v6-feedback-loop-architecture.md |
| Phase 33 skills-mapping v6_ref_signoffs uses OBS-01 as anchor requirement (v6 has no INTEGRATION-* reqs) | Research A3 confirmed: v6.0 has no INTEGRATION-* requirement IDs (unlike v5.0 which had INTEGRATION-01). OBS-01 (per-skill dashboard) is the most defensible anchor — the architecture doc covers the full feedback loop that OBS-01 surfaces. | Applied 2026-06-25 — P33 Plan 02 skills-mapping.yaml v6_ref_signoffs entry |
| Phase 33 v6_ref_signoffs notes field explicitly marks internally-authored status | Unlike v4/v5 refs which cite external books (Eberle SCAMPER / kais-movie-agent V8.6 SKILL.md), the v6 architecture doc is original Hermes Agent analytical work with no upstream external source. The notes field makes this provenance explicit to prevent future mis-citation. | Applied 2026-06-25 — P33 Plan 02 skills-mapping.yaml v6_ref_signoffs notes field |
| Phase 33 TestArchitectureDoc upper H2 bound relaxed 9 → 11 (Rule 1 fix) | Plan's own <action> requires 3 v86 footer sections (Refresh Cadence / See Also / Source Citation) on top of 7 CONTEXT.md content sections = 10 minimum. Original test bound of <= 9 contradicted the plan's requirements. Relaxed to 11 (10 expected + 1 tolerance). | Applied 2026-06-25 — P33 Plan 02 tests/hermes_cli/test_curator_stats.py test_minimal_h2_section_count |

### Decisions (carried forward — relevant to v6.0)

| Decision | Rationale | Why relevant to v6.0 |
|----------|-----------|----------------------|
| FOUND-08 frozen rule: expert_id cannot silently rename; aliases required for any rename | v6.0 does NOT rename or create expert_ids, but EVOL pipeline generates patches against bundled SKILL.md — patches must preserve expert_id + related_skills frontmatter byte-for-byte | P31 SC #5 + P33 SC #7 verify "no new expert_id directory created, no frontmatter edit" |
| skills-mapping.yaml is canonical sign-off registry | INTEGRATION-style requirement (P33) targets this file for `v6_ref_signoffs:` section with verified_date + license_status annotations — mirrors v4.0 `v4_ref_signoffs:` + v5.0 `v5_ref_signoffs:` | Phase 33 SC #5 verifies skills-mapping.yaml has new v6 entries with required fields |
| `_eval/runner.py` is offline developer tooling (per its module docstring) | GATE-01 explicitly reuses this harness for patch-vs-baseline; the docstring declares it is NOT imported by Hermes runtime and does NOT call `registry.register`. So extending it for the gate does not constitute Hermes-runtime touch. | Phase 30 is parallel-eligible with P31 on this basis; P30 "Hermes-core touch: No" annotation |
| Curator currently only touches agent-created skills (per `agent/curator.py` module docstring strict invariants) | CURATE-01 extends Curator scope to bundled skills — this breaks the pre-v6 strict invariant. Must be additive (existing agent-created behavior preserved per P32 SC #6 regression test). | Phase 32 SC #6 explicitly requires regression test against pre-v6 curator behavior |
| Glossary H3 bilingual header convention `### Term / 中文术语` | Established in Phase 14 + carried through v4.0 + v5.0. All new v6.0 glossary terms (P33 SC #6: Feedback Ingestion / Knowledge Evolution / Eval Gate / Curator Proposal) must follow bilingual header convention. | Phase 33 SC #6 explicit on convention |
| v4.0 + v5.0 methodology / V8.6 refs are additive knowledge, not replacement | snowflake-method.md / e-konte-format.md / scamper-variations.md (v4.0) + dreamina-cli-baseline.md / v86-pipeline-mapping.md (v5.0) byte-intact across v6.0. EVOL pipeline patches are ADDITIVE only (per EVOL-02 scope discipline). | P31 SC #6 + P33 SC #8 explicitly verify byte-intact preservation |

### Blockers / Risks (v6.0 — new)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **kais-aigc-platform接入方式选择 (file/HTTP/webhook) blocks INGEST-02** | MEDIUM | HIGH (INGEST-02 is must-have MVP) | Decision explicitly deferred to plan-phase per ROADMAP P28 scope note. P28 MUST ship a working ingest path regardless of transport choice. If plan-phase cannot decide, default to file-exchange (simplest). |
| **Curator scope expansion breaks pre-v6 agent-created skill behavior** | MEDIUM | HIGH (regression in shipped v1-v5 curator) | P32 SC #6 requires regression test against pre-v6 curator behavior. Extension is ADDITIVE — existing deterministic inactivity transitions + consolidation pass must continue unchanged. |
| **Eval gate false-rejects valid patches (threshold too tight)** | MEDIUM | MEDIUM (slows learning loop) | δ=0.3 + per-prompt 1.0 thresholds are defaults, configurable. P30 SC #2-4 require rejection logged with score delta so operator can tune. A/B double-blind (GATE-03) gives statistical signal beyond raw threshold. |
| **EVOL-02 unified-diff generation breaks bilingual EN+CN structure** | MEDIUM | HIGH (corrupts shipped SKILL.md style) | P32 SC #2 explicitly requires "preserving EN-structure + CN-prose bilingual style". Human-in-loop approve (EVOL-04, non-bypassable for bundled) catches style breaks before apply. |
| **Feedback PII / sensitive content in user-submitted corrections** | LOW | MEDIUM (v6 assumes trusted operator environment) | FUTURE-V6-06 (deferred to v7) — auto-redaction not in v6 scope. v6 assumes operator environment is trusted per PROJECT.md. |
| **Feedback store grows unbounded over time** | LOW | LOW (jsonl append-only) | Time-decay weighting (STORE-03) downweights old feedback but does not delete. Operator can manually prune `~/.hermes/skills/.feedback/`. Future auto-prune is FUTURE-V6 scope. |
| **v4.0/v5.0 refs accidentally overwritten by EVOL patches** | LOW | HIGH (would break v4.0 + v5.0 audit PASSED state) | P31 SC #6 + P33 SC #8 explicitly verify byte-intact preservation via sha256 snapshot diff. EVOL-02 patches are ADDITIVE only per scope discipline. |

### Blockers / Risks (carried from v1-v5)

**Inherited from v1 (still ongoing):**

- ⚠ Platform guideline drift — refs use `verified_date` + 90-day refresh cadence
- ⚠ 短剧 sample copyright — fair-use + LICENSE.md per ref
- ⚠ LLM-as-judge invalidity — single-judge bias; v6 reuses single-judge for eval gate (multi-judge ensemble deferred to FUTURE-V6-05)

**Inherited from v3.0 audit (deferred items, NOT in v6.0 scope):**

- W-1: creative_source → topic_curator dead ref (pre-existing v2.0)
- W-2: character_designer missing Phase 17 inheritance body annotation
- W-3: 32 pre-existing v2.0 bidirectional asymmetries
- W-4: Frontmatter `status:` field path inconsistency (documentation drift)
- VALIDATE-D1: quality_gate gap — canonical 16th DAG node has no SKILL.md
- FUTURE-09: production expert (disposition: deferred)

These are documented in `.planning/v3.0-MILESTONE-AUDIT.md` and explicitly excluded from v6.0 scope per REQUIREMENTS.md §"Future Requirements" + §"Out of Scope".

## Session Continuity

**If session is lost, restore context by reading:**

1. `.planning/PROJECT.md` §"Current Milestone: v6.0" — milestone goal + scope expansion rationale
2. `.planning/ROADMAP.md` — 6 phases (28-33), success criteria, coverage table, critical path
3. `.planning/REQUIREMENTS.md` — 26 requirements with REQ-IDs + Traceability table (all mapped)
4. `agent/curator.py` (current implementation, lines 1-150 for invariants + lines 1428+ for `run_curator_review`) — v6 extends this
5. `skills/movie-experts/_eval/runner.py` (existing MT-Bench position-swap harness) — Phase 30 reuses this as eval gate
6. `.planning/research/v2-pipeline-design/skills-mapping.yaml` — canonical expert mapping baseline (v3.0 + v4.0 + v5.0 signoffs; v6 adds `v6_ref_signoffs:` in P33)

**Next action:** Execute Phase 33 Plan 03 (`/gsd:execute-phase 33` — README corpus tree + glossary 4 bilingual entries + SC-7/SC-8 milestone-wide byte-intact verification; FINAL plan of v6.0 milestone).

**Resume from interrupted phase:** Read `.planning/phases/33-observability-integration-close-out/33-02-SUMMARY.md` for the latest state.

---

*Last updated: 2026-06-25 — Phase 33 Plan 02 COMPLETE (architecture doc + skills-mapping sign-off shipped — `_shared/v6-feedback-loop-architecture.md` 305 lines / 10 H2 sections / ASCII data flow / bilingual EN+CN; `skills-mapping.yaml` `v6_ref_signoffs:` section with 1 entry mirroring 10-field v5 schema; 14 new TestArchitectureDoc + TestSkillsMappingV6 tests green; SC-4 + SC-5 satisfied; v5_ref_signoffs byte-intact; T-33-07 v5-byte-intact + T-33-08 Source Citation footer + T-33-09 honest license_status + T-33-10 no-mermaid all mitigated; Ruff PLW1514 clean; 209 Phase 28-32 regression tests pass; FOUND-08 byte-intact — no bundled SKILL.md / v4/v5 ref changes). 12/13 v6.0 plans complete. Next: Phase 33 Plan 03 (README + glossary + SC-7/SC-8 — final plan of v6.0 milestone).*

## Operator Next Steps

- Execute Phase 33 Plan 03 (FINAL): `/gsd:execute-phase 33` (README corpus tree update + glossary 4 bilingual entries + milestone-wide SC-7/SC-8 byte-intact verification)
- After Plan 03: v6.0 milestone complete — archive + tag v6.0
