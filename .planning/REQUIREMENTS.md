# Requirements: Movie-Experts Suite v2 — Milestone v2.0 PRFP

**Defined:** 2026-06-16
**Core Value:** 从第一性原理推导出 kais-movie-agent 的新工作流节点集 —— 每节点明确核心任务 + I/O + AIGC 转化点 + 传统经验锚点,作为双 repo 实施的理论蓝本。

> **Scope reminder:** 本里程碑交付**仅设计文档**,零代码改动(hermes-agent/skills/ + kais-movie-agent/lib/ 都不动)。唯一允许的"代码"是 `scripts/validate_design.py` governance lint(本里程碑自身用的开发工具,不交付给下游)。

---

## v2.0 Requirements

### DERIVATION — Phase A · 第一性原理推导记录

- [ ] **DERIV-01**: 读者可以从"观众最终拿到什么"这一根本问题出发,读到一条**无逻辑跳跃**的 Musk-style 第一性原理推导链,推导结论是**候选节点集**(非从现有 8 phases / 26 skills 类比套出来)。
- [ ] **DERIV-02**: 每个候选节点携带 `derivation` 字段,显示该节点如何从第一性原理推导而来(非"传统就是这样"的类比)。
- [ ] **DERIV-03**: 每条核心论断都有 **epistemic-status 标签**(physical / psychological / platform-algorithmic / tool-capability),区分稳定真理 vs 易变假设。
- [ ] **DERIV-04**: 每个节点都有 **steelman-the-elimination 段落**(最强的"该节点不该存在"论点 + 我方回应)。
- [ ] **DERIV-05**: 每个节点都有 **alternatives-considered 日志**(本位置原本可放什么节点,为何被拒)。
- [ ] **DERIV-06**: 每个节点把核心假设分类为 **contingent vs validated-invariant**(决定后续 AIGC 转化能否修改它)。
- [ ] **DERIV-07**: 推导过程**明确引用 STACK §1.4 corpus 子集**(每个第一性问题对应具体书目),不是 corpus-blind。
- [ ] **DERIV-08**: 推导明确**显式避免 PITFALLS §1 + §5 列出的 Musk 方法误用**(6 个 failure modes 逐条 check)。

### NODES — Phase B · 节点 DAG + 每节点规格

- [ ] **NODE-01**: 读者能看到一个节点 DAG,**目标节点数 8-15**,硬上限 ≤25(超出需逐节点说明)。
- [ ] **NODE-02**: 每个节点声明 4 个核心字段:`core_task` / `I/O 契约` / `AIGC transformation point` / `traditional experience anchor`。
- [ ] **NODE-03**: 每个节点额外声明 8 个 STACK 补充字段:`success_criteria` (≥1 量化指标) / `fail_modes` / `fallback_strategy` / `dependencies` / `complexity_class` / `ai_capability_assumption` / `non_ai_alternative` / `rationale_for_existence`。
- [ ] **NODE-04**: 每个节点声明 `cost_budget`(¥-range,受 META-05 ceiling 约束)/ `latency_budget` / `model_horizon`(stable_2026 / evolving / research_bet)。
- [ ] **NODE-05**: DAG 同时有 **3 种表示**:YAML canonical(规范层)/ Markdown 渲染(人类可读)/ Mermaid 可视化(DAG 图)。
- [ ] **NODE-06**: 节点入选必须 **C1-C7 全部通过**(FEATURES §5 列出的 7 条 selection criteria 显式 check;未通过则不能进 DAG)。
- [ ] **NODE-07**: `theory_critic` 出现为 **consultative 垂直边**(垂直 invoke,非主 DAG 节点)。
- [ ] **NODE-08**: `capability-spec` 是规范层;**具体模型名只在 dated annex 出现**(不在 node spec 主体硬编码,避免 v1 `wan22_video` 类型 phantom 错误重演)。
- [ ] **NODE-09**: 每个生成型节点都有**配对的 critic 节点或 self-critic 步骤**,携带量化指标(无 critic 节点的生成节点需显式说明理由)。

### CORPUS — Phase C · 102 本书传统经验锚点对照

- [ ] **CORPUS-01**: 读者能看到一个**双向 102-book ↔ node 覆盖矩阵**(`corpus-trace.yaml`:正查节点→书目,反查书目→节点)。
- [ ] **CORPUS-02**: 每个 corpus anchor 标 `applicable_form`(长片 / 微电影 / 短剧 / universal),避免 genre conflation。
- [ ] **CORPUS-03**: 对每个节点,**至少 1 个 corpus 来源对该节点设计持"反对/不同"立场被引入并回应**(challenge-source engagement,防 cherry-picking)。
- [ ] **CORPUS-04**: **principle vs workflow 分离**(把 "Murch Rule of Six" 作为 principle 与 "某具体剪辑序列" 作为 workflow 分开标注)。
- [ ] **CORPUS-05**: **中文原术语保留**(汉字与英文 gloss 并存),防 translation loss。
- [ ] **CORPUS-06**: **0 强 corpus 引用的节点必须明确标记为 AIGC-native**(并解释为何无传统对应,避免"假传统"伪装)。
- [ ] **CORPUS-07**: 每个 corpus 引用记录 `Last-verified` 戳(与 v1 LICENSE 模式一致),便于后续 corpus drift 检测。

### CREATIVE — Phase D · LLM 创意凝练专题

- [ ] **CREATIVE-01**: 读者能读到**独立子文档**,覆盖 LLM 创意凝练 4 个维度:创意定义 / 自洽机制 / prompt 策略 / fail modes。
- [ ] **CREATIVE-02**: 创意被**操作性定义为"在不可侵犯约束内的 novelty"**,不是 randomness(明确区分 creative vs random)。
- [ ] **CREATIVE-03**: 自洽性检验机制被明确指定:**consistency-context input + logic-critic**(防 hallucinated logic)。
- [ ] **CREATIVE-04**: LLM 凝练 prompt 策略引用 STACK §5 中 **≥3 篇 LLM-story-gen 论文**(防凭空发明)。
- [ ] **CREATIVE-05**: 平台-艺术张力被**显式处理**(短剧 convention vs 艺术价值,不做 dogmatic 选边)。
- [ ] **CREATIVE-06**: 采用 **template library**(多种叙事弧模板库),非单一 Save-the-Cat / Hero's Journey 模板。
- [ ] **CREATIVE-07**: **链接回 `creative_source` 节点的 novelty-pressure mechanism**(把"创意"接到 DAG 上,非独立浮空)。

### HANDOFF — Phase E · 跨对照 + 双 repo 交接

- [ ] **HANDOFF-01**: 读者能读到 **non-binding 交接计划**,明确标注 `binding: non_binding_recommendation`。
- [ ] **HANDOFF-02**: `skills-mapping.yaml` 把新 DAG 节点 ↔ 现有 26 个 movie-experts skills 对应(**保留 expert_ids**,v1 FOUND-08 frozen rule 不破坏)。
- [ ] **HANDOFF-03**: `kais-migration-matrix.yaml` 把新 DAG 节点 ↔ 现有 kais-movie-agent phases + lib/ 模块对应。
- [ ] **HANDOFF-04**: kais-movie-agent 的 **baseline_ref (git SHA)** 被记录,作为设计-实现 drift 的对比基准。
- [ ] **HANDOFF-05**: **ownership matrix 明确**:design-intent 层(hermes-agent)/ implementation 层(kais-movie-agent)/ co-owned DAG(变更需双方 sign-off)。
- [ ] **HANDOFF-06**: **versioning scheme 是 date-stamped** (e.g., `design-2026-06-16-prfp`)with `supersedes` / `superseded_by`(防 design-impl drift)。
- [ ] **HANDOFF-07**: 附 **1-2 页 impl-cheatsheet** 给 kais-movie-agent 团队上手实施(不是完整 spec,是入口 cheat-sheet)。
- [ ] **HANDOFF-08**: **convergence log**(新 DAG 与现有 pipeline 同意的部分,解释为什么同意,而不只解释分歧)。
- [ ] **HANDOFF-09**: 对照产物包含 `COMPARISON-VS-8-PHASES.md` + `COMPARISON-VS-26-SKILLS.md`(非 binding delta 分析,必须在 Phase A-D 完成后才写,防污染推导)。

### GOVERNANCE — Phase F · 治理 + Finalization

- [ ] **GOV-01**: 读者能读到 **G1-G7 living-doc governance rules**(node 新增需重新推导;AIGC 更新需 marginal-value delta;corpus 变更需 source 验证;status 转换需通过所有 review gates)。
- [ ] **GOV-02**: `validate_design.py` (~30 行 lint) **强制执行 governance rules**(本里程碑唯一代码,作为 pre-commit hook)。
- [ ] **GOV-03**: **README 含 3 页 executive summary**(非作者也能看懂;包含设计核心结论 + 关键决策 + 如何读这份设计)。
- [ ] **GOV-04**: **OPEN-QUESTIONS.md 强制存在**(已知 gap 不藏;SUMMARY.md §"Gaps to Address" 全部落到这里,喂给下游 research phase)。
- [ ] **GOV-05**: **CHANGELOG.md 是 append-only 审计 trail**(每次设计变更记录 what/why/who/when)。
- [ ] **GOV-06**: 每个关键设计决策记录 **Decision / Rationale / Outcome**(v1 PROJECT.md 模式,v1 RETROSPECTIVE 验证有效)。

### META — 元约束(贯穿全里程碑)

- [ ] **META-01**: 本里程碑**零 SKILL.md 编辑**(hermes-agent/skills/movie-experts/ 完全不动)。
- [ ] **META-02**: 本里程碑**零 .js/.py 代码编辑**(kais-movie-agent/ 完全不动,except `scripts/validate_design.py` 这一个例外)。
- [ ] **META-03**: **双语策略**:EN 结构 + CN 段落 / 示例(与 v1 SKILL.md 一致)。
- [ ] **META-04**: 设计文档物理位置在 `.planning/research/v2-pipeline-design/`(或 roadmapper 选定子目录,但必须在 hermes-agent/.planning/ 内,不跨 repo)。
- [ ] **META-05**: **cost ceiling 假设 ¥1000-10000/episode**(约束所有节点 cost_budget 字段;超出范围的节点需显式说明)。
- [ ] **META-06**: **theory_critic 触发模式:创作者手动拉**(非自动 invoke;不在主 DAG 触发条件里)。

---

## Future Requirements(v2 后续里程碑 / 不在本里程碑)

> 这些是合理的下一步,但不在 v2.0 范围。后续里程碑承接。

- **FUTURE-01**: 把设计落地到 kais-movie-agent/lib/(kais-movie-agent/.planning/ 开独立 phase)
- **FUTURE-02**: 把设计映射到 hermes-agent/skills/movie-experts/(本 repo 开 v2.1 里程碑做 skills 对齐)
- **FUTURE-03**: 对高成本节点(cinematographer / screenplay / animation)各跑 per-node research-phase
- **FUTURE-04**: 设计 live statistical GO/NO-GO(实际跑设计 vs 现有 pipeline,量化对比)
- **FUTURE-05**: Musk 第一性原理主源校验(把 PITFALLS §5 转述的 Musk 故事比对 Isaacson 原书精确措辞)

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| hermes-agent/skills/movie-experts/ 任何 SKILL.md 编辑 | 用户明确选择"只做设计文档";skills 重构是后续里程碑 |
| kais-movie-agent/lib/ 任何 .js/.py 编辑 | 同上;pipeline 实施是后续里程碑 |
| Hermes 核心 Python/JS 代码改动 | 范围控制;本里程碑与 Hermes 核心解耦 |
| 新的 LLM provider / adapter | 与设计文档无关 |
| Web/desktop UI 展示设计文档 | 通过现有 Markdown + Mermaid 阅读即可 |
| 自动化 corpus ingestion pipeline | 本里程碑靠人工策展,质量优先 |
| 设计的 live-run 统计验证 | 需要 kais-movie-agent 实施 + 运行 budget,后续里程碑 |
| 完整 bilingual consistency lint | spot-check 即可;v1 经验显示完整 lint 边际收益低 |
| Auto-distribution / auto-upload 节点设计 | TOS 风险,明确排除(AF-9) |
| Theory-critic 作为主 DAG blocking gate | AF-12;明确咨询式(META-06) |
| >25 节点的设计 | AF-1;硬上限 |
| 把现有 8 phases 当作起点 | PROJECT.md 明确"从 0 推",Phase A 必须独立推导 |
| 把现有 26 skills 当作起点 | 同上;HANDOFF-02 是事后对照,不是设计输入 |

---

## Traceability

> Phase 映射由 roadmapper 在下一步生成。Phase 编号沿用 v1 后续(v1 结束于 phase 6,所以 v2.0 从 phase 7 起步)。

| Requirement | Phase | Status |
|-------------|-------|--------|
| (待 roadmapper 填充) | TBD | Pending |

**Coverage:**
- v2.0 requirements: **51 total**(DERIV × 8 + NODES × 9 + CORPUS × 7 + CREATIVE × 7 + HANDOFF × 9 + GOV × 6 + META × 6 - 1 因 HANDOFF-09 与 HANDOFF-01 重叠部分 - 待 roadmapper 验证)
- Mapped to phases: 0
- Unmapped: 51 ⚠️(等 roadmapper 填)

---

*Requirements defined: 2026-06-16*
*Last updated: 2026-06-16 after v2.0 PRFP requirements scoping*
