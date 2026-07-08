# Requirements: Hermes Agent — v13.0

**Defined:** 2026-07-08
**Core Value:** 把 v11.0 设计套件 + v12.0 hardening 留下的 4 项 scope deferrals 全部落地 —— 12 expert agent YAML 全量 transform + 3 项 deferred operator smoke tests + curator self-evolution dry-run → live + operator dashboard。完成后 v10.0-v13.0 四 milestone 架构弧线收官。

## v13.0 Requirements

### EXPERT — EXPERT-COMPLETION (12 active expert agent YAML 全量 transform)

- [x] **EXPERT-01**: 12 active expert SKILL.md → `~/.hermes/agents/{name}.agent.yaml` 全量 transform,严格按 v10.0 `.planning/research/v10-orchestrator-design/04-MIGRATION-PATH.md` §2 75-cell table 规则
  - 待转(12): `animation_studio / colorist / compliance_gate / creative_source / documentary_maker / performer / production / prompt_injector / scene_builder / script_auditor / storyboard_designer / visual_executor`
  - SKILL.md 在 kais-hermes-skills repo,**只读**(per Phase 48-49 lineage invariants L1-L6)
- [x] **EXPERT-02**: 12 个新 YAML 全部 byte-pass `agents-schema.yaml` Draft 2020-12 验证(`jsonschema.Draft202012Validator.validate()`)
- [x] **EXPERT-03**: 12 个新 YAML lineage 字段必须 populated(source SHA + transform rule ID + timestamp),支持审计回溯到原 SKILL.md
- [x] **EXPERT-04**: Agent registry 启动时加载 21 agents(9 已 ship + 12 新增)无 schema/lifecycle 错误,missing-expert 告警逻辑就绪
- [x] **EXPERT-05**: 至少 1 个新 agent(选 `visual_executor` —— 最复杂,带 sub_steps)通过 7 MCP tools 中的 `open_round_table` 实际调用并产生非空响应

### EVAL — LIVE-EVAL-EXEC (3 deferred operator smoke tests)

- [ ] **EVAL-01**: 跑 Phase 57 SC#2 live GLM synthesis endpoint latency smoke —— 真实 GLM API key 链路,捕获 p50/p95 latency;验证 ENDPOINT-01 routing(long-prompt → anthropic-compat)在 live load 下工作
- [ ] **EVAL-02**: 跑 Phase 60 EVAL-01 live mem0 p95 benchmark(`MEM0_API_KEY`)—— 捕获 read/write p95;produce decision feed for v14 物理分区 evaluation(per v10.0 OQ-12 threshold check)
- [ ] **EVAL-03**: 跑 Phase 60 EVAL-02 real-mode fitness battery(`GLM_AUX_API_KEY_1..4`)—— 8 scenarios × real GLM calls;capture production-grade accuracy + latency numbers
- [ ] **EVAL-04**: 3 smoke 结果聚合到 `.planning/research/v13-live-eval/live-eval-report.md`,显式触发或不触发 v14 决策条件(物理分区 / 异步并发)

### CURATE — CURATOR-LIVE (curator self-evolution dry-run → live)

- [x] **CURATE-01**: 给 curator self-evolution CLI 加 `--live` opt-in flag(**默认仍 dry-run** per v11.0 EVAL-06 invariant)
- [x] **CURATE-02**: Pre-tick bias canary check —— 必须 catch ≥ 4/5 known-bad records(per v12.0 EVAL-03 baseline);canary fail 时 abort live tick,记录原因
- [x] **CURATE-03**: Post-tick 审计日志 —— 记录每个 live tick 的所有 memory writes(sha256-tagged),支持 operator 手工 rollback(不要求自动 rollback —— 太复杂,operator 24h 内 review)
- [ ] **CURATE-04**: 1st live tick 端到端跑通 —— capture before/after memory diff + bias canary 结果 + token cost,作为 v14+ live-tick baseline
- [ ] **CURATE-05**: Live-tick operator runbook + safety policy 文档(`.planning/research/v13-live-eval/curator-live-runbook.md`)—— 何时用 live、何时保留 dry-run、operator 监控 checklist

### OBSRV — OBSERVABILITY (operator dashboard)

- [x] **OBSRV-01**: Agent registry health collector —— 21 agents loaded · schema validation status · missing-expert 告警 · lineage integrity check;wire 进 `hermes dashboard` FastAPI server `/orchestrator/agents/status` endpoint
- [x] **OBSRV-02**: Round table metrics collector —— latency p50/p95 · token cost · state transitions · serial-lock wait time · early-stop trigger rate;wire 进现有 round table executor(`agent/open_round_table.py` 或同等模块)
- [x] **OBSRV-03**: Memory backend metrics collector —— mem0 p95 read/write · conflict arbitration rate · compaction trigger rate · error rate;wire 进 mem0 backend adapter(v12.0 Phase 60 shipped)
- [x] **OBSRV-04**: CLI 命令 `hermes orchestrator status` —— rich tables 展示 3 个维度(mirrors v6.0 P33 OBS-01 pattern);支持 `--json` flag 给脚本消费
- [x] **OBSRV-05**: Dashboard web view —— minimal Jinja2 panel surface 3 个维度的实时状态(基于现有 `hermes dashboard` FastAPI server 扩展,不引入新框架)

### VALIDATE — Close-out

- [ ] **VALIDATE-01**: v13.0 milestone audit + close-out report at `.planning/milestones/v13.0-MILESTONE-AUDIT.md`,包含 4-track traceability + 3 operator-action handoffs 状态 + verdict(pass / tech_debt / fail)。**Strictly LAST phase**(mirror v11.0 P56 / v12.0 P61 single-phase close-out pattern)

## v2+ Requirements (Deferred)

(无 —— v13.0 是 v10.0 设计弧线收官,后续 milestone 由 v13 live data 驱动决策)

## Out of Scope (v14+)

| Feature | Reason |
|---------|--------|
| **Option B → 物理分区 migration** | v13.0 EVAL-02 mem0 p95 数据决定是否触发;若 p95 < 500ms 可保留单 backend + agent_id filter(per v10.0 OQ-12) |
| **Round table 异步并发(INFRA-04 解除)** | GLM upstream capacity 扩容前保留串行约束(per MEMORY.md `feedback-glm-overload-reduce-concurrency.md`) |
| **15-expert 全量 production hardening tuning** | v13.0 完成 12-expert transform + smoke;threshold tuning 用 prod 数据留 v14+(per v11.0 EVAL-05) |
| **kais-hermes-skills repo SKILL.md 改动** | Lineage invariants L1-L6(Phase 48-49)v13.0 仍只读 SKILL.md |
| **新 repo 创建(如 kais-orchestrator)** | 单 repo 收敛决策保留;v13.0 全在 hermes-agent |
| **Automated rollback for curator live tick** | 太复杂;v13.0 用 operator 24h review + 手工 rollback(CURATE-03) |
| **OBSRV Prometheus/Grafana integration** | 范围控制;v13.0 用 rich tables + minimal Jinja2 panel,不引入新 observability stack |
| **15 expert 之外的新 agent(例如 coding-agent-as-agent)** | v13.0 收口于 movie-experts 全量覆盖;非-movie-expert 的 agent 化是 v14+ 候选 |

## Traceability

(由 roadmapper 在 roadmap 创建阶段填充 — 2026-07-08)

| Requirement | Phase | Status |
|-------------|-------|--------|
| EXPERT-01 | Phase 62 | Complete |
| EXPERT-02 | Phase 62 | Complete |
| EXPERT-03 | Phase 62 | Complete |
| EXPERT-04 | Phase 63 | Complete |
| EXPERT-05 | Phase 63 | Complete |
| EVAL-01 | Phase 64 | Pending |
| EVAL-02 | Phase 64 | Pending |
| EVAL-03 | Phase 64 | Pending |
| EVAL-04 | Phase 64 | Pending |
| CURATE-01 | Phase 65 | Complete |
| CURATE-02 | Phase 65 | Complete |
| CURATE-03 | Phase 65 | Complete |
| CURATE-04 | Phase 66 | Pending |
| CURATE-05 | Phase 66 | Pending |
| OBSRV-01 | Phase 67 | Complete |
| OBSRV-02 | Phase 67 | Complete |
| OBSRV-03 | Phase 67 | Complete |
| OBSRV-04 | Phase 68 | Complete |
| OBSRV-05 | Phase 68 | Complete |
| VALIDATE-01 | Phase 69 | Pending |

**Coverage:**
- v13.0 requirements: 20 total
- Mapped to phases: 20 / 20 ✓
- Unmapped: 0
- Phase count: 8 (Phases 62-69, standard granularity)
- Orphaned requirements: 0
- Duplicate mappings: 0

**Phase-requirement distribution:**
- Phase 62 (EXPERT-YAML-TRANSFORM): EXPERT-01..03 (3 reqs)
- Phase 63 (EXPERT-REGISTRY-INTEGRATION): EXPERT-04..05 (2 reqs)
- Phase 64 (LIVE-EVAL-EXEC): EVAL-01..04 (4 reqs)
- Phase 65 (CURATOR-LIVE-GUARDS): CURATE-01..03 (3 reqs)
- Phase 66 (CURATOR-LIVE-TICK): CURATE-04..05 (2 reqs)
- Phase 67 (OBSERVABILITY-BACKEND): OBSRV-01..03 (3 reqs)
- Phase 68 (OBSERVABILITY-PRESENTATION): OBSRV-04..05 (2 reqs)
- Phase 69 (VALIDATE): VALIDATE-01 (1 req)

---
*Requirements defined: 2026-07-08*
*Last updated: 2026-07-08 — traceability filled by roadmapper. 8 phases (62-69), 20/20 reqs mapped, VALIDATE-01 strictly LAST.*
