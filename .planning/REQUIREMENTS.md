# Requirements: Movie-Experts Suite v2 — Milestone v3.0 Skills-to-DAG Alignment

**Defined:** 2026-06-16
**Core Value:** 把 hermes-agent `skills/movie-experts/` 从 26 experts 对齐到 v2.0 PRFP 设计的 16 pipeline-roles,执行 `skills-mapping.yaml` 锁定的 rename / merge / new / deprecate 决定,让 skills 知识层与新 DAG 干净映射。

> **Scope reminder:** 本次里程碑执行 v2.0 PRFP 设计决策(已在 `.planning/research/v2-pipeline-design/skills-mapping.yaml` 锁定),仅修改 `skills/movie-experts/`。kais-movie-agent 实施是 parallel milestone(在该 repo)。

---

## v3.0 Requirements

### RENAME — Expert Rename(2 reqs)

- [x] **RENAME-01**: `continuity` expert 改名为 `continuity_auditor`,更新 SKILL.md frontmatter `name` + `expert_id` + `metadata.hermes.expert_id` + `metadata.hermes.related_skills` 协作图(双向 edge 同步)。保留 `continuity` 作为 alias(per FOUND-08 backward-compat)。
- [x] **RENAME-02**: `compliance_marketing` expert 改名为 `compliance_gate`,聚焦 pure compliance(分离 marketing 到独立 ref 或 sub-skill)。保留 `compliance_marketing` 作为 alias。

### MERGE — Expert Merge(2 reqs)

- [x] **MERGE-01**: `drawer` + `animator` 合并为 `visual_executor` 新 expert。保留原 expert_id 作为 sub-step 名(`visual_executor` SKILL.md 内部声明 `sub_steps: [drawer, animator]`)。`related_skills` 协作图更新:visual_executor 继承 drawer + animator 的全部 edge。
- [x] **MERGE-02**: 5 个 audio experts(`voicer` + `composer` + `foley` + `mixer` + `spatial_audio`)合并为 `audio_pipeline` 新 expert。`audio_pipeline` SKILL.md 内部声明 `sub_steps: [voicer, lip_sync, composer, foley, mixer]`(lip_sync 是新增显式 sub-step)。`related_skills` 协作图更新。

### NEW — New Expert(1 req)

- [ ] **NEW-01**: 新增 `prompt_injector` expert — AI-native 节点,无 v1 对应。SKILL.md 包含:core_task(intent → model tokens + cross-call consistency context)、4 refs(prompt engineering patterns + cross-call consistency)、`metadata.hermes.expert_id: prompt_injector`、`metadata.hermes.related_skills: [creative_source, cinematographer, visual_executor, audio_pipeline]`、接入协作图(per Phase 7 §4.7 + Phase 8 §2.7)。

### DEPRECATE — Expert Deprecation(3 reqs)

- [ ] **DEPRECATE-01**: `performer` expert deprecate。理由(per `06-COMPARISON-VS-26-SKILLS.md`):表演真实折叠进 character_designer(voice + behavioral tics)+ screenplay(dialogue subtext),无独立节点必要。处理方式:SKILL.md 标 `status: deprecated` + redirect 注释指向 character_designer + screenplay;保留 expert_id 文件以免破坏向后兼容(FOUND-08)。
- [ ] **DEPRECATE-02**: `scene_builder` expert deprecate。理由:场景设计折叠进 cinematographer(mise-en-scène as composition_lock 子任务)+ style_genome。处理方式同上。
- [ ] **DEPRECATE-03**: `storyboard_designer` expert deprecate。理由(per Phase 7 §3.4 D3.4):storyboard 折叠进 cinematographer composition_lock。处理方式同上。

### VALIDATE — Frozen Rule + Backward Compat(2 reqs)

- [ ] **VALIDATE-01**: FOUND-08 frozen rule compliance check — 所有保留的 expert_id 不变量维护;rename + merge 显式 mapping 记录在 `.planning/research/v2-pipeline-design/skills-mapping.yaml`(已有,本里程碑 sign_off 状态从 `pending` → `signed_off`);deprecate 不静默。验证方法:grep 26 → 21 个 active expert_id(16 pipeline-roles + 5 alias 兼容 + 3 deprecated-but-present)。
- [ ] **VALIDATE-02**: Backward compatibility alias — 所有 rename / merge / deprecate 操作保留旧 expert_id 作为 alias(`metadata.hermes.aliases: [old_id]`)。验证方法:现有创作者 workflow 不破坏;旧 expert_id 引用仍能找到对应 SKILL.md。

### DOC — Documentation + Collaboration Graph(2 reqs)

- [ ] **DOC-01**: 更新 `skills/movie-experts/README.md` 26-expert inventory → 21-expert inventory(16 active + 5 aliases 注释)。更新 18-expert collaboration DAG → 新 DAG 拓扑(per `01-NODE-DAG.md` Mermaid)。更新 RAG usage guide + Phase 6 live-run procedure(指向新 DAG)。
- [ ] **DOC-02**: 更新 `_shared/glossary.md` 添加新术语(`visual_executor`, `audio_pipeline`, `prompt_injector`, `continuity_auditor`, `compliance_gate`)+ EN↔CN 映射。更新 `_shared/known-external-models.yaml` 添加 Phase 8 §2.17 dated annex 的模型清单。

---

## Future Requirements(v3 后续里程碑 / 不在 v3.0)

> 这些是合理的下一步,但不在 v3.0 范围。后续里程碑承接。

- **FUTURE-06**: 把 `_shared/project-corpus/` refs 重新 align 到 v3.0 expert inventory(deprecated experts 的 corpus refs 重定向到继承者)
- **FUTURE-07**: 更新 `_eval/` benchmark prompts 从 26-expert 到 21-expert(deprecated experts 的 prompts 重定向)
- **FUTURE-08**: 设计 v3.0 live run 对比 v2.0 PRFP DAG 与 v1 18-expert 实际效果差异
- **FUTURE-09**: production expert 处理(per v2.0 §6 deferred;超 v3.0 范围)
- **FUTURE-10**: skills 团队与 kais-movie-agent 团队的 cross-repo ADR 治理流程落地(per HANDOFF-05 co-owned DAG)

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| kais-movie-agent/lib/ 任何 .js / .py 编辑 | kais-movie-agent impl 是 parallel milestone,在该 repo 处理 |
| `_eval/` benchmark prompts 全面重写 | FUTURE-07;spot-check 即可 |
| live run 执行 | FUTURE-08;需要 OPENROUTER_API_KEY + budget |
| production expert 处理 | FUTURE-09;v3.0 范围只覆盖 16 pipeline-roles,production 超出 |
| v2.0 PRFP 设计文档修改 | 设计 frozen-pending-impl;只在 impl 团队 challenge 时通过 cross-repo ADR 修订 |
| 新的 SKILL.md 内容写作 | 本里程碑是 inventory 重构 + rename + merge + deprecate,不是 refs 内容重写 |
| 全 26-expert SKILL.md 双语 lint | spot-check 即可;v1 经验显示完整 lint 边际收益低 |

---

## Traceability

> Phase 映射由 roadmapper 在 2026-06-16 生成。Phase 编号沿用 v2.0 后续(v2.0 结束于 phase 12,所以 v3.0 从 phase 13 起步)。

| Requirement | Phase | Status |
|-------------|-------|--------|
| RENAME-01 | 13 | Complete |
| RENAME-02 | 13 | Complete |
| MERGE-01 | 14 | Complete |
| MERGE-02 | 15 | Complete |
| NEW-01 | 16 | Pending |
| DEPRECATE-01 | 17 | Pending |
| DEPRECATE-02 | 17 | Pending |
| DEPRECATE-03 | 17 | Pending |
| VALIDATE-01 | 18 | Pending |
| VALIDATE-02 | 18 | Pending |
| DOC-01 | 18 | Pending |
| DOC-02 | 18 | Pending |

**Coverage:**
- v3.0 requirements: **12 total** (RENAME × 2 + MERGE × 2 + NEW × 1 + DEPRECATE × 3 + VALIDATE × 2 + DOC × 2)
- Mapped to phases: **12 / 12** ✓
- Unmapped: **0**

**Per-phase summary:**

| Phase | Name | Requirements | Count |
|-------|------|--------------|-------|
| 13 | Expert Rename + Alias Scaffolding | RENAME-01, RENAME-02 | 2 |
| 14 | Visual Executor Merge (drawer + animator) | MERGE-01 | 1 |
| 15 | Audio Pipeline Merge (5 audio experts) | MERGE-02 | 1 |
| 16 | New AI-Native Expert (prompt_injector) | NEW-01 | 1 |
| 17 | Deprecate 3 Candidates (performer / scene_builder / storyboard_designer) | DEPRECATE-01, DEPRECATE-02, DEPRECATE-03 | 3 |
| 18 | Validation + Documentation + Collaboration Graph Update | VALIDATE-01, VALIDATE-02, DOC-01, DOC-02 | 4 |

---

*Requirements defined: 2026-06-16*
*Last updated: 2026-06-16 — v3.0 requirements traceability populated (12/12 mapped to 6 phases 13-18)*
