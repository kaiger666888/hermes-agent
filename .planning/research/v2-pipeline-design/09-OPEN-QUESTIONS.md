# 09 — Open Questions

> **Document status:** design-2026-06-16-prfp · supersedes: none · superseded_by: TBD
> **Phase:** 12 of v2.0 PRFP · **Stability:** experimental
> **Purpose:** per GOV-04, all known gaps surfaced for downstream research feeding

---

## §0 — 阅读指南

本文档汇总 v2.0 PRFP 设计套件揭示的 **未解问题**。每个 gap 标注:来源 phase + 描述 + 推荐处理阶段 + confidence。

诚实记录是 design 质量的核心 — 不藏 gap,不假完成。

---

## §1 — 来自 Phase 7 (First-Principles Derivation) 的 gaps

### OQ-7.1 — Musk 引文主源分页
- **描述:** STACK §4.1 给 URL 但 Isaacson 2023 不同版次页码不同。本设计按章节上下文引用。
- **Confidence:** HIGH on gist,LOW on exact wording
- **推荐阶段:** Phase 12 finalization(此里程碑后,如 impl 团队挑战特定引文)

### OQ-7.2 — 平台波动性分类 borderline 案例
- **描述:** "前 3 秒 hook" 是 `psychological`(注意力衰减)还是 `platform-algorithmic`(完播率加权)?Phase 7 判双标签。其他 borderline 需 case-by-case。
- **Confidence:** MEDIUM
- **推荐阶段:** 后续研究 milestone(超 v2.0 PRFP)

### OQ-7.3 — Theory_critic 触发模式具体设计
- **描述:** META-06 锁定 manual-pulled;具体 trigger UI / heuristic 建议 / always-available-but-optional 等 = Phase 8 决定。Phase 8 §2.16 已声明 `trigger_mode: creator_pulled` 但 UI 层未设计。
- **Confidence:** HIGH (constraint is clear; UI is open)
- **推荐阶段:** kais-movie-agent impl milestone

---

## §2 — 来自 Phase 9 (Corpus Traceability) 的 gaps

### OQ-9.1 — 短剧特定 corpus 缺口
- **描述:** 102 书目以长片为主;短剧特定质量驱动(前 3 秒 hook / 付费卡点 / 竖屏 framing)语料弱。Phase 9 §3 corpus-trace.yaml 标 3 个 AIGC-native 节点(prompt_injector / hook_retention / compliance_gate)零强 corpus 引用。
- **Confidence:** HIGH
- **推荐阶段:** FUTURE milestone(短剧 corpus 独立构建)

### OQ-9.2 — AIGC 边际价值分析 corpus 缺口
- **描述:** 102 书目 pre-AIGC;无 ref 直接回答 "AI 加速哪些操作"。Phase 7 §2.3 Q3 答案从 craft-execution refs + kais V8 推断。
- **Confidence:** MEDIUM
- **推荐阶段:** 后续 AIGC-specific 研究

### OQ-9.3 — 微电影特定 corpus 弱
- **描述:** 微电影介于短剧和长片之间,corpus 覆盖最弱。Phase 9 标 GAP-09-03。
- **Confidence:** MEDIUM
- **推荐阶段:** 后续微电影 specific milestone

---

## §3 — 来自 Phase 10 (LLM-Creative Distillation) 的 gaps

### OQ-10.1 — Trope-catalog embedding 数据库不存在
- **描述:** Phase 10 §1.4 假设 Save-the-Cat + 爆款公式 + Kishōtenketsu 的 embedding database 存在,用于 novelty_score 计算。实际需独立构建。
- **Confidence:** HIGH (assumption is documented)
- **推荐阶段:** FUTURE milestone(trope catalog codification)

### OQ-10.2 — Novelty-score 阈值(0.6 / 0.8)实证校准
- **描述:** Phase 10 §1.4 给阈值是初步值,需创作者实际反馈校准。
- **Confidence:** MEDIUM
- **推荐阶段:** v2.0 PRFP 之后 pilot

### OQ-10.3 — Consistency-context schema 完整性
- **描述:** Phase 10 §2.1 schema 是初步设计,实战可能需更多/更少字段。
- **Confidence:** MEDIUM
- **推荐阶段:** Phase 11 handoff 时 kais-movie-agent 团队 review

### OQ-10.4 — Template library 实际可用性
- **描述:** Phase 10 §6 6 模板中部分(尤其 anti_structure)需进一步 operational 定义。
- **Confidence:** MEDIUM
- **推荐阶段:** Phase 11 handoff + 后续 milestone

### OQ-10.5 — Logic-critic LLM 模型选择
- **描述:** script_auditor 当前用 Haiku(cost-optimized)。是否够用需 live run 验证。
- **Confidence:** MEDIUM
- **推荐阶段:** FUTURE-04 live run

### OQ-10.6 — Commercial_mode flag 滥用风险
- **描述:** 创作者可能滥用 commercial_mode flag 作为 cliché 的借口。
- **Confidence:** MEDIUM
- **推荐阶段:** Phase 12 GOV-01 G7 governance

### OQ-10.7 — 平台 convention drift 对 novelty_score 影响
- **描述:** 短剧爆款公式漂移时,novelty_score 阈值是否需要调整?
- **Confidence:** MEDIUM
- **推荐阶段:** 后续 milestone

---

## §4 — 来自 Phase 11 (Handoff) 的 gaps

### OQ-11.1 — 7 experts → 2 nodes 合并的实施决定
- **描述:** visual_executor (drawer+animator) + audio_pipeline (5 audio) 是 design-level 合并决定。skills 实际是否合并是 v2.1+ 决定。
- **Confidence:** HIGH (design 合理;impl 开放)
- **推荐阶段:** v2.1+ skills milestone

### OQ-11.2 — 3-4 deprecate candidates 的最终决定
- **描述:** performer / scene_builder / storyboard_designer(+ production deferred)是 deprecate candidate,非最终决定。
- **Confidence:** HIGH
- **推荐阶段:** v2.1+ skills milestone

### OQ-11.3 — 2 rename sign-offs
- **描述:** continuity_auditor + compliance_gate rename 需 skills 团队 sign-off。
- **Confidence:** HIGH
- **推荐阶段:** v2.1+ skills milestone(per `skills-mapping.yaml` sign_off_status: pending)

### OQ-11.4 — Cost validation ¥8000/episode
- **描述:** Phase 8 cost budgets 是 estimate;live validation 需要 kais-movie-agent 实施 + 实际运行。
- **Confidence:** MEDIUM
- **推荐阶段:** FUTURE-04 live run

---

## §5 — 来自 META / 跨阶段 的 gaps

### OQ-M.1 — Cost ceiling (META-05) 假设验证
- **描述:** ¥1000-10000/episode ceiling 假设未验证 against current platform economics。
- **Confidence:** MEDIUM
- **推荐阶段:** Phase 11 handoff 时 kais 团队验证

### OQ-M.2 — 短剧 platform convention drift monitoring
- **描述:** 平台规则季度更新;refs 已带 `verified_date` + 90-day refresh cadence,但 monitoring 不是自动。
- **Confidence:** HIGH (mechanism exists; discipline required)
- **推荐阶段:** 后续 milestone(drift monitoring)

### OQ-M.3 — V8 审核门 survival 决定
- **描述:** V8 architecture 有 review gates;v2.0 automates 部分。Phase 11 §5 决定保留哪些。具体实施决定在 kais。
- **Confidence:** HIGH
- **推荐阶段:** kais impl milestone

### OQ-M.4 — Live statistical GO/NO-GO
- **描述:** 本设计为 design doc,无 live run。设计的实际效果(对比 V8 的量化提升)需要实施 + budget。
- **Confidence:** HIGH
- **推荐阶段:** FUTURE-04 per REQUIREMENTS.md

---

## §6 — Open Questions 统计

| Source phase | Count |
|---|---|
| Phase 7 | 3 |
| Phase 9 | 3 |
| Phase 10 | 7 |
| Phase 11 | 4 |
| META / cross | 4 |
| **Total** | **21** |

**Confidence 分布:**
- HIGH (assumption documented, just deferred): 11
- MEDIUM (needs validation): 10

**推荐阶段分布:**
- 后续 v2.1+ skills milestone: 5
- kais-movie-agent impl milestone: 4
- FUTURE-04 (live run): 3
- 后续独立 research milestone: 5
- Phase 12 finalization: 1
- 平台 drift monitoring: 3

---

## §7 — Research feeding 喂给下游

本文档的 21 个 OQ 是 v2.0 PRFP 之后的 **研究 backlog**。后续 milestone 启动时应优先:

1. **HIGH confidence + blocking:** OQ-10.1 (trope-catalog), OQ-11.4 (cost validation), OQ-M.4 (live run)
2. **HIGH confidence + non-blocking:** OQ-9.1 (短剧 corpus), OQ-11.1/11.2/11.3 (skills 决定)
3. **MEDIUM confidence:** 需要 pilot data 才能校准的(OQ-10.2 novelty 阈值, OQ-10.3 schema 完整性, 等)

---

*Document version: design-2026-06-16-prfp*
*Phase 12 of v2.0 PRFP milestone*
*Stability: experimental (open questions evolve freely)*
