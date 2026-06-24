# V6.0 Feedback-Loop Architecture — Canonical Reference for Self-Evolution & Feedback-Driven Learning

**Source:** Hermes Agent v6.0 Self-Evolution & Feedback Loop (internally authored; synthesizes `.planning/REQUIREMENTS.md` + `.planning/ROADMAP.md` Phases 28-33 + shipped implementations `agent/feedback_ingest.py` / `agent/feedback_schema.py` / `agent/feedback_store.py` / `skills/movie-experts/_eval/runner.py` / `skills/movie-experts/_eval/gate.py` / `agent/evolution/*` / `agent/curator.py` / `agent/curator_audit.py` / `hermes_cli/feedback.py` / `hermes_cli/curator.py`).
**Copyright:** Original Hermes Agent analytical work — no upstream external source (unlike v4/v5 `_shared/` refs which paraphrased external books or the kais-movie-agent V8.x SKILL.md). The feedback-loop architecture is an original Hermes Agent design; the MT-Bench position-swap eval pattern was inherited from v1 `_eval/runner.py` and reused as the gate.
**Last-verified:** 2026-06-25
**verified_date:** 2026-06

---

## Overview & Goal / 概览与目标

本 ref 是 hermes-agent movie-experts skill suite **v6.0 范式跃迁**的 canonical architecture reference:从 v1-v5 的「人工 curate 静态知识层」转为「带反馈闭环的自学习系统」。v6.0 是 movie-experts 第一次真正具备 self-improvement 能力 —— 专家给出意见后,调用者(含 kais-aigc-platform 审核系统)能反馈结果,反馈驱动 eval-gated 的 SKILL.md / refs 改进。

The architecture spans six phases (P28-P33), each owning one stage of the ingest → store → gate → evolve → curate → observe pipeline. Every stage has a single ownership module and a documented contract; every cross-stage boundary is a Pydantic schema or a JSONL file format. The human-in-loop boundary is structural: bundled-skill patches NEVER auto-apply (the `apply_patch_transaction` call is only reachable from `hermes_cli/feedback.py:_cmd_approve`, enforced by the P31 `TestNonBypassableHumanInLoop` ast-walk).

**核心设计原则:**
- **反馈是 first-class data:** FeedbackRecord 不是日志,是结构化数据(skill_id / source / verdict / correction / output_snapshot / ts),持久化在 `~/.hermes/skills/.feedback/`,可查询、可加权、可去重。
- **eval gate 是唯一的 merge 路径:** 任何 candidate patch 必须先通过 patch-vs-baseline MT-Bench position-swap gate(δ=0.3 mean + 1.0 per-prompt)才能进入 review queue。
- **human-in-loop 不可绕过:** bundled skill 的 patch 永远需要 operator `hermes feedback approve`;agent-created skill 可走半自动路径(confidence ≥ 0.8 + gate pass)。
- **可观测性是 first-class surface:** `hermes curator stats` 暴露反馈计数 / patch 历史 / eval 趋势,让 operator 看到学习健康度。

---

## Data Flow / 反馈闭环数据流

下图展示 v6.0 反馈闭环的完整数据流。Operator 在 CLI / kais-aigc-platform / 手工标注三种渠道反馈 → FeedbackRecord 经 P29 存储去重 → P30 eval gate 验证 candidate patch → P31 生成 unified-diff 并入 review queue → P32 Curator 自动扫描 + operator 审批 → apply + commit + audit log → P33 `hermes curator stats` 暴露学习健康度。

```
Operator feedback (3 sources)
   │
   │  (1) /feedback slash cmd (cli)
   │  (2) kais-aigc file-exchange inbox (kais_aigc)
   │  (3) hermes feedback import <jsonl> (manual)
   ▼
┌──────────────────────────────────────────────────────────────────┐
│ P28 Feedback Ingestion (agent/feedback_ingest.py +                │
│                       agent/feedback_schema.py)                   │
│   - OutputSnapshot capture (sha256 of output_text bytes)          │
│   - FeedbackRecord Pydantic validation (skill_id allowlist +      │
│     path-safety defense)                                          │
│   - Atomic per-record write to incoming/                          │
└──────────────────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────────────────┐
│ P29 Feedback Store (agent/feedback_store.py)                      │
│   - FeedbackStore.summary() -> per-verdict counts/weighted/first/ │
│     last_ts with bucket key "<skill>:<source>:<verdict>"          │
│   - sha256 dedup (supersession tracked via _superseded_record_ids)│
│   - Time-decay weighting (weight = exp(-age_days / decay_days))   │
│   - index.json + buckets/<skill>/<source>.jsonl                   │
└──────────────────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────────────────┐
│ P30 Eval Gate (skills/movie-experts/_eval/runner.py + gate.py)    │
│   - parse_judge_scores() extracts 4-dim scores from MT-Bench      │
│     position-swap output                                          │
│   - decide_verdict(mean_delta_threshold=0.3,                      │
│                   per_prompt_threshold=1.0,                       │
│                   min_prompts=5)                                  │
│   - paired_t_stats() via stdlib statistics (no scipy)             │
│   - rebuild_baseline() + load_cached_baseline() (scores.json)     │
│   - multi-skill guard (exit 3 without applying patch)             │
└──────────────────────────────────────────────────────────────────┘
   │
   │ gate PASS -> candidate advances
   │ gate FAIL -> patch rejected with score delta logged
   ▼
┌──────────────────────────────────────────────────────────────────┐
│ P31 Knowledge Evolution (agent/evolution/*)                       │
│   - insights.py: LLM aggregation of feedback -> candidate         │
│     insights                                                      │
│   - diff_generator.py: difflib-based unified-diff generation      │
│     (stdlib only — LLMs unreliable at @@ hunk syntax)             │
│   - apply.py: additive-only check + path-traversal guard          │
│   - queue.py: JSONL review queue (pending / applied / rejected)   │
│   - TestNonBypassableHumanInLoop ast-walk: apply_patch_transaction│
│     ONLY callable from _cmd_approve                               │
└──────────────────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────────────────┐
│ P32 Curator Upgrade + Audit (agent/curator.py +                   │
│                            agent/curator_audit.py +               │
│                            agent/evolution/evol02_generator.py)   │
│   - _feedback_scan_phase: lazy-import P31 engine, scan FeedbackStore│
│     for hot skills, generate candidate patches via EVOL-02        │
│   - CURATE-05 Option A: bundled-never-auto; agent-created         │
│     conditional on confidence >= 0.8                              │
│   - curator_audit.py: sha256-chained JSONL audit log (append /    │
│     verify / read)                                                │
│   - hermes_cli/curator.py: queue / approve / reject / audit-log / │
│     auto-apply-eligible subparsers                                │
└──────────────────────────────────────────────────────────────────┘
   │
   │ operator runs `hermes curator approve <patch_id>`
   ▼
   apply_patch_transaction -> git commit -> append_audit(action="apply")
   │
   ▼
┌──────────────────────────────────────────────────────────────────┐
│ P33 Observability (hermes_cli/curator.py _cmd_stats + helpers)    │
│   - hermes curator stats <skill_id>  (per-skill dashboard)        │
│   - hermes curator stats --all       (cross-skill top-N + zero)   │
│   - hermes curator stats --by-source (verdict × source matrix)    │
│   - --json emits COUNTS ONLY (no correction text — T-33-01)       │
│   - read-only: never mutates FeedbackStore / queue / audit        │
└──────────────────────────────────────────────────────────────────┘
```

---

## JSON Schema Reference / JSON 结构定义

v6.0 的反馈闭环有三个核心 data structures。所有结构都用 Pydantic v2 定义在 `agent/feedback_schema.py`,序列化为 JSONL 持久化。

### FeedbackRecord (`agent/feedback_schema.py:184`)

| 字段 | 类型 | 用途 |
|------|------|------|
| `skill_id` | `str` (validated against auto-discovered expert_ids) | 反馈目标的 movie-expert skill。Path-safety defense: 不允许 `:` `/` `\\` 字符 |
| `expert_id` | `str` (same validation) | 通常等于 skill_id;保留为未来 one-skill-multi-expert 场景 |
| `source` | `Literal["cli", "kais_aigc", "manual"]` | 反馈来源:CLI slash cmd / kais-aigc file-exchange / 手工 JSONL import |
| `verdict` | `Literal["good", "needs_work", "bad"]` | operator 的定性评级 |
| `correction` | `str` (default `""`) | 自由文本解释 —— operator-authored,可能含 PII,所以 stats --json 只输出 counts |
| `revised_output` | `str \| None` | 可选的完整替换输出(用于 P30 ablation) |
| `output_snapshot` | `OutputSnapshot` | 被评价的 LLM 输出的 provenance(sha256 + prompt + model 等) |
| `ts` | `datetime` (timezone-aware required) | 反馈提交时间;用于时间衰减权重 |

### OutputSnapshot (`agent/feedback_schema.py:149`)

| 字段 | 类型 | 用途 |
|------|------|------|
| `sha256` | `str` (regex `^[0-9a-fA-F]{64}$`) | `output_text` UTF-8 bytes 的 sha256 —— P29 dedup + P30 cache key 的单一契约 |
| `output_text` | `str` | 被评价的 LLM 原始输出 |
| `prompt` | `str` | 触发该输出的 user prompt |
| `model` / `provider` / `api_mode` | `str` | 模型 provenance,用于跨模型对比 |
| `params` | `dict[str, Any]` | 生成参数(temperature / max_tokens 等) |
| `captured_at` | `datetime` | 输出捕获时间 |

### Audit Log Entry (`agent/curator_audit.py`)

audit log 是 sha256-chained JSONL,每条 entry 包含前一条的 sha256 形成 tamper-evident chain。

| 字段 | 类型 | 用途 |
|------|------|------|
| `action` | `Literal["propose", "apply", "reject", "rollback"]` | 审批生命周期事件 |
| `patch_id` | `str` | 关联 P31 PatchRecord 的 id |
| `skill_id` | `str` | 受影响的 skill |
| `operator` | `str` | 执行操作的 operator 标识 |
| `commit_sha` | `str` (apply action) | apply 后的 git commit SHA |
| `eval_score` | `dict` (optional, apply action) | P30 gate verdict + mean_delta + evidence_count —— `hermes curator stats` trend 列的数据源 |
| `prev_hash` | `str` | 前一条 entry 的 sha256(chain integrity) |
| `ts` | `datetime` (UTC) | 事件时间戳 |

---

## Eval-Gate Thresholds / 评估闸门阈值

P30 eval gate 复用 v1 `_eval/runner.py` 的 MT-Bench position-swap harness 做 patch-vs-baseline 对比。阈值定义在 `gate_config.yaml`(可配置),default 值如下:

| 阈值 | Default | 含义 | 可配置? | 配置位置 |
|------|---------|------|---------|---------|
| `mean_delta_threshold` | **0.3** | candidate vs baseline 的 composite score 平均差必须 >= 0.3(scale 0-10) | yes | `gate_config.yaml: mean_delta_threshold` |
| `per_prompt_threshold` | **1.0** | 任何单 prompt 的 score drop 不能超过 1.0(strict-less-than: drop == 1.0 passes, drop > 1.0 fails) | yes | `gate_config.yaml: per_prompt_threshold` |
| `min_prompts` | **5** | 参与 gate 的 valid prompt 数必须 >= 5,否则 verdict = inconclusive(数据不足) | yes | `gate_config.yaml: min_prompts` |
| `significant_at_0.05` | (computed) | paired-t 双尾检验 α=0.05;stdlib statistics + 硬编码 t-table(无 scipy 依赖) | no (固定 α) | `gate.py: _CRITICAL_T_05_TWO_TAILED` |

**gate verdict 决策逻辑(`gate.py:decide_verdict`):**
- 若 `mean_delta < mean_delta_threshold` → `fail_mean_drop`
- 若任何 prompt 的 `delta < -per_prompt_threshold` → `fail_regression`
- 若 `n_valid < min_prompts` → `inconclusive`
- 否则 → `pass`

**baseline cache 行为:** 首次运行时 candidate composites 被 lazy-cache 为下次的 baseline(`scores.json`,含 per-prompt composites + sha256 provenance)。后续运行若 sha 匹配则用 cache;sha 不匹配则发出 staleness warning 但仍返回 cache(non-blocking —— operator 决定是否 `--rebuild-baseline`)。

---

## Human-in-Loop Boundaries / 人工审核边界

v6.0 的人工审核边界是**结构性不变量**,不是 runtime 检查 —— 通过 ast-walk 测试 `TestNonBypassableHumanInLoop` 强制执行。

### Bundled Skills(NEVER auto-apply)

`apply_patch_transaction` 是修改 bundled SKILL.md 的唯一入口。该函数**只**从 `hermes_cli/feedback.py:_cmd_approve` 调用 —— 即 operator 必须显式运行 `hermes curator approve <patch_id>`。P32 CURATE-05 Option A 把 Curator 的 auto-apply 路径**委托**给 `_cmd_approve`,而不是直接调用 `apply_patch_transaction`,从而保留 ast-walk 不变量。

结构性强制:`tests/agent/evolution/test_non_bypassable_human_in_loop.py::TestNonBypassableHumanInLoop` 遍历 `hermes_cli/curator.py` + `hermes_cli/feedback.py` AST,断言 `apply_patch_transaction` 的 Call nodes 只出现在 `_cmd_approve` 函数体内。

### Agent-Created Skills(conditional auto-apply)

Agent-created skills(Curator 在 v1-v5 已经能管理的动态 skill)可走半自动路径:P32 `auto-apply-eligible` 子命令列出 `PatchRecord.auto_apply_eligible == True` 且 `confidence_score >= 0.8` 且 gate verdict == pass 的 candidate。Operator 可批量 approve,但仍需显式 approve —— 不是静默应用。

### Operator CLI Surface

| 命令 | 用途 | 涉及阶段 |
|------|------|---------|
| `hermes feedback import <jsonl>` | 批量导入反馈(atomic all-or-nothing) | P28 |
| `hermes feedback watch [--inbox <dir>]` | 启动 kais-aigc file-exchange watcher | P28 |
| `hermes feedback evolve [--skill <id>]` | 触发 P31 LLM aggregation + diff 生成 | P31 |
| `hermes feedback review-queue [--status <s>]` | 查看 review queue | P31 |
| `hermes feedback show-patch <patch_id>` | 查看 candidate patch detail | P31 |
| `hermes feedback approve <patch_id>` | 批准并 apply patch(唯一 apply 入口) | P31/P32 |
| `hermes feedback reject <patch_id>` | 拒绝 patch | P31 |
| `hermes feedback rollback <commit_sha>` | 回滚已 apply 的 patch | P30/P31 |
| `hermes curator queue [--status <s>]` | 查看 Curator 提案队列 | P32 |
| `hermes curator approve <patch_id>` | 批准 Curator 提案(委托给 feedback approve) | P32 |
| `hermes curator reject <patch_id>` | 拒绝 Curator 提案 | P32 |
| `hermes curator audit-log [--verify]` | 查看 / 验证审计日志(sha256 chain) | P32 |
| `hermes curator auto-apply-eligible` | 列出可半自动应用的 agent-created patches | P32 |
| `hermes curator stats [skill_id] [--runs N] [--json]` | per-skill 反馈统计(OBS-01) | P33 |
| `hermes curator stats --all [--top N] [--json]` | cross-skill top-N + zero-feedback(OBS-02) | P33 |
| `hermes curator stats --by-source [--skill <id>] [--json]` | source × verdict 分布(OBS-03) | P33 |

### Audit Log Tamper-Evidence

`agent/curator_audit.py` 的 JSONL audit log 是 **sha256-chained**:每条 entry 包含 `prev_hash`(前一条 entry 的 sha256)。`hermes curator audit-log --verify` 重算 chain,任何篡改(插入 / 修改 / 删除历史 entry)都会破坏 chain 并被检测出。Stats CLI(`hermes curator stats`)**不**做 chain 验证 —— 那是 `audit-log --verify` 的职责(concern separation)。

---

## Module Ownership Map / 模块归属表

每个 v6.0 组件有唯一的 ownership module 和明确的 shipped phase。

| 文件 | 用途 | Shipped Phase |
|------|------|--------------|
| `agent/feedback_schema.py` | FeedbackRecord + OutputSnapshot Pydantic schema;auto-discovered expert_id registry | P28 Plan 01 |
| `agent/feedback_ingest.py` | `write_feedback_record` atomic per-record write to incoming/ | P28 Plan 01 |
| `agent/feedback_snapshot.py` | OutputSnapshot capture helper(sha256 + sanitization) | P28 Plan 01 |
| `hermes_cli/feedback.py` | `/feedback` slash cmd + `hermes feedback {import,watch,submit,evolve,review-queue,show-patch,approve,reject,rollback}` CLI | P28 Plan 02 + P31 Plan 02 |
| `agent/feedback_store.py` | `FeedbackStore` —— summary/query/record_feedback/sha256-dedup/time-decay/rebuild-index | P29 Plan 01 + Plan 02 |
| `skills/movie-experts/_eval/runner.py` | MT-Bench position-swap harness;`parse_judge_scores` + `run_position_swap` + composite scoring | v1 (P0) + P30 Plan 01 extension |
| `skills/movie-experts/_eval/gate.py` | P30 eval gate orchestrator —— patch mechanics + decide_verdict + paired-t + rebuild_baseline + multi-skill guard + revert_patch | P30 Plan 01 + Plan 02 |
| `agent/evolution/__init__.py` | P31 subpackage public API;runtime-isolation invariant(forbidden for agent runtime to import) | P31 Plan 01 |
| `agent/evolution/insights.py` | LLM aggregation of feedback → candidate insights | P31 Plan 01 |
| `agent/evolution/diff_generator.py` | difflib-based unified-diff generation(P31 placeholder;P32 extends via evol02_generator) | P31 Plan 01 |
| `agent/evolution/apply.py` | `apply_patch_transaction` + additive-only check + path-traversal guard | P31 Plan 01 |
| `agent/evolution/queue.py` | JSONL review queue(pending/applied/rejected) + `read_queue` | P31 Plan 01 |
| `agent/evolution/evol02_generator.py` | EVOL-02 multi-instruction bilingual diff generator(build-final-state-then-diff-once) | P32 Plan 01 |
| `agent/curator.py` | Curator —— `_feedback_scan_phase` additive extension(lazy imports, try/except isolation, bundled-never-auto) | v1 + P32 Plan 01 extension |
| `agent/curator_audit.py` | sha256-chained JSONL audit log(append_audit / verify_chain / read_audit) | P32 Plan 01 |
| `hermes_cli/curator.py` | `register_cli` —— queue/approve/reject/audit-log/auto-apply-eligible/stats subparsers + `_cmd_stats` + `_render_*` helpers | v1 + P32 Plan 02 + P33 Plan 01 extensions |
| `skills/movie-experts/_shared/v6-feedback-loop-architecture.md` | **本文件** —— v6.0 canonical architecture reference | P33 Plan 02 |

---

## Roadmap References / 路线图引用

v6.0 的完整 phase / requirement / milestone 交叉引用见:

- **`.planning/ROADMAP.md`** —— 6 phases (P28-P33) 的 critical path + per-phase success criteria。P28 (Feedback Ingestion MVP) 必须先 ship;P29 (Feedback Store) 依赖 P28;P30 (Eval Gate) 与 P31 (Knowledge Evolution) parallel-eligible(disjoint file ownership);P32 (Curator Upgrade + Audit) 消费 P29 + P31 review queue;P33(Observability + Close-out)必须最后运行。
- **`.planning/REQUIREMENTS.md`** —— 26 requirements 跨 6 categories:INGEST-01..05 (P28) / STORE-01..04 (P29) / GATE-01..04 (P30) / EVOL-01/02/03/04/05 (P31+P32) / CURATE-01..05 (P32) / OBS-01/02/03 (P33)。Traceability table 在文末。
- **`.planning/MILESTONES.md`** —— v6.0 milestone 条目(执行中);完成后归档到 `.planning/milestones/v6.0-ROADMAP.md` + `.planning/milestones/v6.0-REQUIREMENTS.md` + `.planning/milestones/v6.0-MILESTONE-AUDIT.md`,镜像 v5.0 归档模式。
- **`.planning/STATE.md`** —— 实时进度(per-phase % + decisions table + blockers)。v6.0 Decisions 表记录了所有 plan-phase 决策(如 "stdlib os.scandir polling for kais-aigc watcher (no watchdog dep)" / "EVOL-02 placeholder uses stdlib difflib" / "Phase 33 stats --json emits COUNTS ONLY" 等)。
- **`.planning/phases/33-observability-integration-close-out/33-01-SUMMARY.md`** —— P33 Plan 01 stats CLI 的交付记录,本 ref 的 Module Ownership Map 中 `hermes_cli/curator.py: _cmd_stats` 行指向该 plan。

---

## Refresh Cadence / 复核节奏

本 ref **每季度复核一次**(per `_shared/` convention)。Drift triggers:

1. **FeedbackRecord schema 字段变化** —— 新增 / 移除字段会打破 P29 store + P30 gate + P31 evolution 的消费链。
2. **eval-gate 阈值变化** —— `mean_delta_threshold` / `per_prompt_threshold` / `min_prompts` 的 default 调整需要在本文档同步更新。
3. **新增 ingest source** —— 当前 3 源(cli / kais_aigc / manual);若新增(如 webhook / HTTP endpoint)需更新 Data Flow 图 + JSON Schema Reference 的 `source` Literal。
4. **Curator scope 再扩张** —— 若 v7+ 把 auto-apply 范围从 agent-created 扩展到更多场景,Human-in-Loop Boundaries section 需同步更新,且 `TestNonBypassableHumanInLoop` ast-walk 需重新评估。
5. **新增 observability surface** —— 若 v7+ 新增 web dashboard 或 Prometheus export(P33 deferred items),需更新 Data Flow 图的最下游 box。

复核动作:
- 重读 P28-P32 shipped 实现的 module docstrings,确认本 ref 的字段列表 / 阈值 / CLI surface 与代码一致
- 运行 `python3 -m pytest tests/hermes_cli/test_curator_stats.py::TestArchitectureDoc -x` 验证结构不变量
- 更新本 ref 的 `Last-verified:` 与 `verified_date:` 时间戳

---

## See Also

- [`v86-pipeline-mapping.md`](./v86-pipeline-mapping.md) — v5.0 canonical V8.6 13-Step pipeline → expert_id mapping(结构性模板来源;本 ref 的 header block + See Also + Source Citation + footer ownership 约定均镜像 v86)
- [`dreamina-cli-baseline.md`](./dreamina-cli-baseline.md) — v5.0 dreamina CLI 6 sub-commands baseline(v6 不触碰;仅 cross-reference)
- [`glossary.md`](./glossary.md) — V8.6 + v6.0 术语 EN↔CN 词典(v6.0 新增 Feedback Ingestion / Knowledge Evolution / Eval Gate / Curator Proposal 4 词条,P33 Plan 03 ships)
- [`RAG-INVOCATION-PATTERN.md`](./RAG-INVOCATION-PATTERN.md) — 专家如何调用共享 ref 的通用模式(v6 feedback loop 不改变此模式;EVOL-02 生成的 patch 必须遵循 additive-only 约定)
- [`SKILL-LAYOUT.md`](./SKILL-LAYOUT.md) — `_shared/` ref 标准文件结构与头块规范(本 ref 遵循)

---

## Source Citation

- **Primary:** Hermes Agent v6.0 codebase —— 本 ref 是 internally authored,无 upstream external source。synthesizes 以下 shipped 实现:
  - `agent/feedback_schema.py` (P28 Plan 01 — FeedbackRecord + OutputSnapshot Pydantic schema)
  - `agent/feedback_ingest.py` (P28 Plan 01 — atomic per-record write)
  - `agent/feedback_store.py` (P29 Plan 01 + Plan 02 — FeedbackStore + sha256 dedup + time-decay)
  - `skills/movie-experts/_eval/runner.py` (v1 + P30 — MT-Bench position-swap + parse_judge_scores)
  - `skills/movie-experts/_eval/gate.py` (P30 Plan 01 + Plan 02 — eval gate orchestrator)
  - `agent/evolution/*` (P31 Plan 01 — insights + diff_generator + apply + queue)
  - `agent/evolution/evol02_generator.py` (P32 Plan 01 — EVOL-02 multi-instruction diff)
  - `agent/curator.py` (v1 + P32 Plan 01 — `_feedback_scan_phase` additive extension)
  - `agent/curator_audit.py` (P32 Plan 01 — sha256-chained JSONL audit log)
  - `hermes_cli/feedback.py` (P28 Plan 02 + P31 Plan 02 — feedback CLI surface)
  - `hermes_cli/curator.py` (v1 + P32 Plan 02 + P33 Plan 01 — curator CLI surface including stats)
- **Secondary:** `.planning/REQUIREMENTS.md` —— 26 requirements 跨 INGEST/STORE/GATE/EVOL/CURATE/OBS 6 categories,每条 requirement 的 Acceptance Criteria 是本 ref 字段列表 / 阈值 / CLI surface 的 spec source。
- **Tertiary:** `.planning/ROADMAP.md` —— P28-P33 critical path + per-phase success criteria;`.planning/STATE.md` —— v6.0 Decisions 表(plan-phase 决策记录)。

---

*Owned by Phase 33 plan 33-02. Canonical v6.0 feedback-loop architecture reference. Cross-references Phase 28-32 implementations + Phase 33 plan 33-01 stats CLI. No parallel plan touches this file.*
