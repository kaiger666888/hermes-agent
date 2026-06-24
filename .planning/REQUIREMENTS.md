# Requirements: v6.0 Self-Evolution & Feedback Loop

**Milestone:** v6.0 — Self-Evolution & Feedback Loop
**Started:** 2026-06-24
**Predecessor:** v5.0 kais-movie-agent V8.6 Adaptation (shipped 2026-06-19, 30/30 reqs, audit PASSED)

**Core functional guarantee:** 每个 movie-expert skill 在给出意见后,都能接收到调用者的反馈,反馈经 eval-gated pipeline 驱动 SKILL.md / refs 持续改进。

---

## v1 Requirements (this milestone)

### Feedback Ingestion (INGEST) ⭐ MVP 核心

- [ ] **INGEST-01**: Hermes CLI 用户可在 conversation 内对 movie-expert 的输出提交反馈 —— verdict (`good` / `needs_work` / `bad`) + 自由文本 correction + 可选修订后的输出
- [ ] **INGEST-02**: kais-aigc-platform 审核反馈自动 ingest(至少一种接入路径 —— 文件交换 / HTTP endpoint / webhook,在 plan-phase 决定),含审核 verdict + retry 信号 + 修改 diff
- [ ] **INGEST-03**: 反馈数据结构标准化为单一 JSON schema,所有源(CLI / kais-aigc / 手工)走同一 schema,字段含 `skill_id, expert_id, source, verdict, correction, output_snapshot, ts`
- [ ] **INGEST-04**: 反馈含 `output_snapshot`(原始 LLM 输出 sha256 + 元数据:prompt / model / params),用于后续 eval 对比与去重
- [ ] **INGEST-05**: 手工标注工具(CLI 子命令)支持批量导入历史输出 + 标注,用于冷启动 / baseline 构建

### Feedback Store (STORE)

- [ ] **STORE-01**: `~/.hermes/skills/.feedback/` 持久化目录结构,按 `skill_id/source/` 分子目录,jsonl 格式追加写入
- [ ] **STORE-02**: 反馈索引文件 `index.json`(按 skill_id / verdict / source / timestamp 可查询),Curator 与 dashboard 共用
- [ ] **STORE-03**: 时间衰减权重 —— 超过 N 天(默认 90,可配置)的反馈权重降低,避免陈旧反馈主导学习方向
- [ ] **STORE-04**: 反馈去重(同 `output_snapshot.sha256` + `verdict` 不重复计入;同 sha256 不同 verdict 视为修正,旧记录降权)

### Knowledge Evolution (EVOL)

- [ ] **EVOL-01**: 反馈→可执行知识点抽取 —— LLM-based aggregation,跨多条反馈识别共性"应该改进什么",输出 candidate insights(结构化 JSON,带证据链指向具体反馈 IDs)
- [ ] **EVOL-02**: 知识点→候选 patch 生成 —— 针对 SKILL.md 或 `references/*.md`,生成 unified diff(非整文件改写),保留原文风格与双语结构
- [ ] **EVOL-03**: Patch review queue —— operator 可视化查看 pending patches,每条带 source 反馈链 + LLM 抽取理由 + 影响 skill 列表
- [ ] **EVOL-04**: Human-in-loop approve workflow —— **所有 bundled movie-expert skill 的 patch 必须经 operator 审批才能 apply**(agent-created skill 可走半自动,见 CURATE-05)
- [ ] **EVOL-05**: Patch apply + rollback —— apply 前自动 git-commit(带 feedback IDs + eval score 在 commit message);rollback 子命令可回滚到任意历史版本

### Eval Gate (GATE) — 防退化

- [ ] **GATE-01**: Patch 进入 review queue 前必须经过 LLM-as-judge 对比 baseline(复用 `skills/movie-experts/_eval/runner.py` 既有 harness)
- [ ] **GATE-02**: 通过阈值 —— patch 在 benchmark prompts 上的平均得分不得低于 baseline − δ(默认 δ=0.3,4 分制),否则直接拒绝,不进入 review queue
- [ ] **GATE-03**: A/B 双盲对比工具 —— 候选 patch vs baseline 在同一 prompt 集上位置交换评分,输出统计显著性报告
- [ ] **GATE-04**: Regression detection —— patch 不能让任何单一 prompt 的 score 下降超过 per-prompt 阈值(默认 1.0),否则整体拒绝

### Curator Upgrade (CURATE)

- [ ] **CURATE-01**: 扩展 `agent/curator.py` 作用域 —— 从「只 archive agent-created skill」扩展为「能对 bundled movie-expert skill propose patch」(沿用 human-in-loop gate)
- [ ] **CURATE-02**: Curator 周期扫描累积反馈,当某 skill 负反馈达阈值(可配置,默认 ≥3 条 `needs_work`/`bad` 且跨 ≥2 个 session)自动触发 EVOL 流程
- [ ] **CURATE-03**: Patch audit log —— `~/.hermes/skills/.audit/` 记录每次 patch 的 operator / 时间 / 关联反馈 IDs / eval score / commit sha,可追溯
- [ ] **CURATE-04**: Operator 命令 `hermes curator queue` —— 列出待审批 patches;`hermes curator approve <id>` / `hermes curator reject <id> <reason>` 完成审批
- [ ] **CURATE-05**: Agent-created skill 半自动路径 —— eval gate 通过 + confidence score ≥ 阈值(默认 0.8)时可自动 apply(仍写 audit log),operator 可全局关闭此行为

### Observability (OBS)

- [ ] **OBS-01**: 每 skill dashboard(`hermes curator stats [skill_id]`)—— 反馈计数按 verdict 分桶 + patch 历史 + eval score 趋势(最近 N 次)
- [ ] **OBS-02**: Cross-skill 视图(`hermes curator stats --all`)—— 哪些 skill 收到最多负反馈 / 哪些 patch 提升最大 / 哪些 skill 长期无反馈(可能 prompt 覆盖不足)
- [ ] **OBS-03**: 反馈源 breakdown —— 按 source(CLI / kais-aigc-platform / 手工)统计反馈量与 verdict 分布,辅助判断 kais-aigc 接入是否实际工作

---

## Future Requirements (deferred to v7+)

- **FUTURE-V6-01**: Vector DB 集成(chromadb / faiss)用于反馈语义聚类 —— 发现「相同 fail mode 的不同表述」
- **FUTURE-V6-02**: 全自动 bundled-skill patch agent-in-loop —— eval gate confidence 极高时跳过 human approve(v6 保留 human-in-loop 是安全网)
- **FUTURE-V6-03**: 跨 repo 反馈同步 —— kais-movie-agent 那边的反馈也走相同 schema 同步过来
- **FUTURE-V6-04**: Real-time feedback streaming(websocket)—— 替代当前 batch / file-based 接入
- **FUTURE-V6-05**: Multi-judge ensemble for eval gate —— 单 judge 易 biased,v7 引入 ensemble + statistical GO/NO-GO(继承 v1 deferred 的 statistical verdict 工作)
- **FUTURE-V6-06**: 反馈 PII / 合规自动脱敏 —— 短剧样本 + 用户修改可能含敏感内容,v6 假设操作环境可信,v7 加自动脱敏
- **FUTURE-V6-07**: Web UI for feedback / patch management —— v6 用 CLI + 文件够了,大规模 operator 团队时再上 UI

---

## Out of Scope (explicit exclusions)

- **全自动 skill 改写(无 human-in-loop)** —— v6 保留 operator 审批为 bundled-skill 安全网;agent-created skill 可半自动,但 bundled 必须人审
- **新增 vector DB 基础设施** —— 沿用 v1 决定,不引入 chromadb/qdrant 等新依赖(留 v7)
- **跨 repo 反馈同步** —— 单向 ingest(kais→hermes)够 v6 用,双向同步留 v7
- **基于反馈 fine-tune LLM** —— 这是 RAG / 知识层项目,不是 training 项目(沿用 v1 决定)
- **新 Web/Desktop UI** —— CLI + 文件 + 可选 HTTP endpoint 够 v6 用(沿用 v1 决定)
- **新增 expert_id 或 DAG 节点改动** —— 沿用 v5.0 scope 纪律,v6 不动拓扑
- **重构 v5.0 / v4.0 / v3.0 既有 refs** —— byte-intact 保留;v6 只新增/修改反馈驱动发现的 patch
- **Hermes memory plugin 修改** —— 反馈系统独立于 memory plugin;不修改 plugin 本身(沿用 v1 决定)

---

## Traceability

Filled by roadmapper — every REQ-ID maps to exactly one phase (see `.planning/ROADMAP.md` for full phase details).

| REQ-ID | Phase | Notes |
|--------|-------|-------|
| INGEST-01 | Phase 28 | CLI in-conversation feedback submission |
| INGEST-02 | Phase 28 | kais-aigc-platform接入 (transport choice at plan-phase) |
| INGEST-03 | Phase 28 | Single normalized JSON schema across all sources |
| INGEST-04 | Phase 28 | output_snapshot with sha256 + prompt/model/params metadata |
| INGEST-05 | Phase 28 | Manual labeling CLI subcommand for cold-start |
| STORE-01 | Phase 29 | `~/.hermes/skills/.feedback/` layout, jsonl append |
| STORE-02 | Phase 29 | index.json queryable by skill_id/verdict/source/ts |
| STORE-03 | Phase 29 | Time-decay weight (default 90 days, configurable) |
| STORE-04 | Phase 29 | Dedup by sha256+verdict; correction demotion |
| GATE-01 | Phase 30 | Reuse `_eval/runner.py` for patch-vs-baseline |
| GATE-02 | Phase 30 | Pass threshold δ=0.3 on 4-point rubric |
| GATE-03 | Phase 30 | A/B double-blind position-swap + significance report |
| GATE-04 | Phase 30 | Per-prompt regression detection (threshold 1.0) |
| EVOL-01 | Phase 31 | LLM feedback→candidate insight aggregation |
| EVOL-02 | Phase 32 | Unified-diff patch generator (invoked by Curator proposal path) |
| EVOL-03 | Phase 31 | Patch review queue with evidence chains |
| EVOL-04 | Phase 31 | Human-in-loop approve for bundled skills (non-bypassable) |
| EVOL-05 | Phase 31 | Git-commit-on-apply + rollback subcommand |
| CURATE-01 | Phase 32 | Extend `agent/curator.py` to propose bundled-skill patches |
| CURATE-02 | Phase 32 | Auto-trigger EVOL on negative-feedback threshold |
| CURATE-03 | Phase 32 | `~/.hermes/skills/.audit/` tamper-evident log |
| CURATE-04 | Phase 32 | `hermes curator queue/approve/reject` CLI |
| CURATE-05 | Phase 32 | Agent-created skill semi-automatic path (confidence ≥ 0.8) |
| OBS-01 | Phase 33 | Per-skill dashboard (`hermes curator stats [skill_id]`) |
| OBS-02 | Phase 33 | Cross-skill view (`hermes curator stats --all`) |
| OBS-03 | Phase 33 | Source breakdown (CLI/kais-aigc/manual) |

**Totals:** 26 requirements across 6 categories · 26 / 26 mapped to phases (100%, no orphans, no duplicates)

**Coverage by phase:**
- Phase 28 (Feedback Ingestion MVP): INGEST-01..05 (5 reqs)
- Phase 29 (Feedback Store): STORE-01..04 (4 reqs)
- Phase 30 (Eval Gate Reuse): GATE-01..04 (4 reqs)
- Phase 31 (Knowledge Evolution Pipeline): EVOL-01, EVOL-03, EVOL-04, EVOL-05 (4 reqs)
- Phase 32 (Curator Upgrade + Audit): CURATE-01..05 + EVOL-02 (6 reqs)
- Phase 33 (Observability + Integration Close-out): OBS-01..03 (3 reqs)

**EVOL-02 mapping note:** Placed in Phase 32 (not Phase 31) because the candidate-patch generator is invoked by the Curator's proposal path in practice. Phase 31 builds the review queue + approve/apply mechanics; Phase 32 implements the EVOL-02 diff generator as the engine that the Curator calls to populate that queue.
