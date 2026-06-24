---
gsd_state_version: 1.0
milestone: v6.0
milestone_name: Self-Evolution & Feedback Loop
status: ready_to_plan
last_updated: 2026-06-24T15:11:22.228Z
last_activity: 2026-06-24 -- Phase 31 COMPLETE (engine + CLI layers shipped; 87 tests green; EVOL-04 non-bypassable human-in-loop structurally enforced)
progress:
  total_phases: 6
  completed_phases: 4
  total_plans: 8
  completed_plans: 8
  percent: 67
stopped_at: Phase 31 complete (2/2) — ready to discuss Phase 32
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
**Current focus:** Phase 32 — curator upgrade + audit

## Current Position

Phase: 32
Plan: Not started
Status: Ready to plan
Last activity: 2026-06-24

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
  Phase 32 (Curator Upgrade + Audit)       [          ] 0% Not started — UNBLOCKED (P29 + P31 both complete)
  Phase 33 (Observability + Close-out)     [          ] 0% Not started — MUST run last
```

### Phase Statuses (v6.0)

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 28 | Feedback Ingestion MVP | **Complete** | Shipped 2026-06-24. INGEST-01..05 covered. Plan 01 (schema + snapshot + atomic write — 45 tests) + Plan 02 (/feedback slash cmd + hermes feedback {import,watch,submit} + kais file watcher + JSONL atomic batch import — 31 new tests). 76/76 tests green, Ruff clean, FOUND-08 preserved, zero new deps. |
| 29 | Feedback Store | **Complete** | Shipped 2026-06-24. STORE-01..04 satisfied. Plan 01 FeedbackStore foundation (49 tests, 2 Rule 1 bugs auto-fixed). Plan 02 STORE-04 sha256 dedup/correction branch + Phase 28 write_feedback_record delegation + rebuild_index method + hermes feedback rebuild-index CLI (26 new tests across TestDedup/TestCorrection/TestRebuildIndex/TestDelegation/TestRebuildIndexCLI; 150/151 feedback-subsystem green, 1 documented skip; 2 deviations auto-fixed). Phase 29 closed. |
| 30 | Eval Gate Reuse | **Complete** | Shipped 2026-06-24. GATE-01..04 all covered. Plan 01: parse_judge_scores() + composite_score() in runner.py + gate.py orchestrator (patch mechanics + decide_verdict + config + CLI) — 43 new tests. Plan 02: paired_t_stats() + is_significant() via stdlib statistics + hardcoded _CRITICAL_T_05_TWO_TAILED t-table (GATE-03, no scipy) + rebuild_baseline() with scores.json provenance cache + load_cached_baseline() with non-blocking staleness warning + detect_multi_skill_patch() with exit-3 early-exit guard + --rebuild-baseline/--multi-skill CLI flags — 30 new tests. 100/101 eval tests green (1 pre-existing openai-missing skip), FOUND-08 byte-intact, runtime isolation 0, scipy-free. Phase 30 CLOSED. |
| 31 | Knowledge Evolution Pipeline | **Complete** | Shipped 2026-06-24. EVOL-01/03/04/05 fully covered. Plan 01: agent/evolution/ subpackage (insights LLM aggregation + difflib diff generator + JSONL queue + atomic apply transaction + FOUND-08 byte-intact + additive-only verifier) — 60 new tests, 7 commits. Plan 02: hermes_cli/feedback.py extended with 6 new subcommands (evolve / review-queue / show-patch / approve / reject / rollback) + TestNonBypassableHumanInLoop ast-walk structural invariant (only _cmd_approve calls apply_patch_transaction) — 27 new tests, 3 commits. 87/87 combined green, runtime isolation 0 matches, FOUND-08 byte-intact (0 SKILL.md changes), RESEARCH 3/3 Open Questions RESOLVED, VALIDATION nyquist_compliant=true. Phase 31 CLOSED. |
| 32 | Curator Upgrade + Audit | Not started | UNBLOCKED — P29 + P31 dependencies both satisfied. Covers CURATE-01..05 + EVOL-02. Directly modifies `agent/curator.py` (unavoidable scope expansion from v5). Implements EVOL-02 diff generator invoked by Curator proposal path. Must still route commits through _cmd_approve (TestNonBypassableHumanInLoop enforces). |
| 33 | Observability + Integration Close-out | Not started | Covers OBS-01..03 + integration deliverables. MUST run last. Writes `_shared/v6-feedback-loop-architecture.md` + skills-mapping.yaml `v6_ref_signoffs:` + README + glossary. Mirrors v5.0 Phase 27 pattern. |

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
- v6.0 phases completed: 4 (Phase 28 — Feedback Ingestion MVP; Phase 29 — Feedback Store; Phase 30 — Eval Gate Reuse; Phase 31 — Knowledge Evolution Pipeline)
- v6.0 requirements total: 26
- v6.0 requirements mapped: 26 / 26 ✓
- v6.0 requirements orphaned: 0
- v6.0 requirements completed: 20 (INGEST-01..05 from Phase 28 + STORE-01..04 from Phase 29 + GATE-01..04 from Phase 30 + EVOL-01/03/04/05 from Phase 31 + ROADMAP-LEVEL annotations to follow)
- v6.0 plans completed: 8 / 8 so far for Phases 28-31 (Phase 28 Plan 01 + Plan 02 + Phase 29 Plan 01 + Plan 02 + Phase 30 Plan 01 + Plan 02 + Phase 31 Plan 01 + Plan 02; Phases 32-33 not yet planned)
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

**Next action:** Execute Phase 31 Plan 02 (`/gsd:execute-phase 31` — CLI layer: hermes_cli/feedback.py extension with 6 new subcommands wiring the agent/evolution/ engine) OR plan Phase 32 (`/gsd:plan-phase 32` — Curator Upgrade, depends on P29 + P31).

**Resume from interrupted phase:** Read `.planning/phases/31-knowledge-evolution-pipeline/31-01-SUMMARY.md` for the latest state.

---

*Last updated: 2026-06-24 — Phase 31 Plan 01 COMPLETE (knowledge evolution engine layer shipped — agent/evolution/ subpackage with EVOL-01/03/04/05 + FOUND-08 byte-intact + additive-only). 20/26 v6.0 requirements satisfied. Next: Phase 31 Plan 02 (CLI layer) OR Phase 32 plan.*

## Operator Next Steps

- Execute Phase 31 Plan 02: `/gsd:execute-phase 31` (CLI layer — hermes_cli/feedback.py extension with evolve / review-queue / show-patch / approve / reject / rollback subcommands; wires the agent/evolution/ engine into operator-invokable commands)
- Plan Phase 32: `/gsd:plan-phase 32` (Curator Upgrade + Audit — covers CURATE-01..05 + EVOL-02; depends on P29 + P31)
- Review ROADMAP.md critical path — Phase 31 Plan 01 done; Plan 02 (CLI) completes P31, then P32 (Curator) + P33 (Observability)
