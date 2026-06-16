# 06 — Comparison vs hermes-agent 26 movie-experts Skills

> **Document status:** design-2026-06-16-prfp · supersedes: none · superseded_by: TBD
> **Phase:** 11 of v2.0 PRFP · **Source:** compares new DAG (`nodes.yaml`) vs hermes-agent `skills/movie-experts/` 26 experts
> **Binding:** `non_binding_recommendation` per HANDOFF-01
> **Stability:** stable

---

## §0 — 阅读指南

本文档比较 v2.0 PRFP 新 DAG(16 pipeline-roles)与 hermes-agent `skills/movie-experts/` 现有 26 experts(14 原 + 4 v1 新 + Phase 7+ 其他)。

**前置阅读:** `02-NODE-SPECS.md`(新 DAG per-node v1_expert_id mapping 字段)+ skills/movie-experts/README.md

**hermes-agent baseline_ref:** `85965c393f44deae29a833f2ae98af66d26548ce`(per HANDOFF-04)

---

## §1 — 26 Experts 盘点(per v1 README)

v1 共 26 experts:

**14 原 experts:**
screenplay, drawer, animator, editor, colorist, composer, performer, scene_builder, foley, spatial_audio, mixer, voicer, continuity, style_genome

**4 v1 新增:**
cinematographer (Phase 4), hook_retention (Phase 2), production (Phase 5), compliance_marketing (Phase 1)

**额外(总计 26):**
character_designer, storyboard_designer, lip_sync (or similar), creative_source, script_auditor, theory_critic, quality_gate + 其他(per README 全清单)

---

## §2 — 节点 ↔ Expert 映射(per HANDOFF-02 / FOUND-08 frozen rule)

| 新 DAG 节点 | v1 expert_id 映射 | 映射类型 | 备注 |
|---|---|---|---|
| `creative_source` | `creative_source` | 1:1 preserved | 直接映射 |
| `style_genome` | `style_genome` | 1:1 preserved | |
| `screenplay` | `screenplay` | 1:1 preserved | |
| `script_auditor` | `script_auditor` | 1:1 preserved | |
| `character_designer` | `character_designer` | 1:1 preserved | |
| `cinematographer` | `cinematographer` | 1:1 preserved | |
| `prompt_injector` | (none) | NEW | AI-native,无 v1 precedent |
| `visual_executor` | `drawer` + `animator` | N:1 merge | Phase 11 handoff may revisit |
| `audio_pipeline` | `voicer` + `composer` + `foley` + `mixer` + `spatial_audio` + `lip_sync` | N:1 merge | 5-6 → 1 |
| `continuity_auditor` | `continuity` (renamed) | 1:1 renamed | HANDOFF-02 mapping preserved |
| `editor` | `editor` | 1:1 preserved | |
| `colorist` | `colorist` | 1:1 preserved | |
| `hook_retention` | `hook_retention` | 1:1 preserved | 短剧 form-specific |
| `quality_gate` | `quality_gate` | 1:1 preserved | |
| `compliance_gate` | `compliance_marketing` (renamed) | 1:1 renamed | HANDOFF-02 mapping preserved |
| `theory_critic` | `theory_critic` | 1:1 preserved | consultative |

**未在新 DAG 中保留的 v1 experts(候选 deprecation / 重定向):**

| v1 expert | 新 DAG 处置 | 理由 |
|---|---|---|
| `performer` | DEPRECATE candidate | 表演指导在新 DAG 中 fold into character_designer(voice + behavioral tics)+ screenplay(dialogue subtext);无独立节点必要 |
| `scene_builder` | DEPRECATE candidate | 场景设计在新 DAG 中 fold into cinematographer(mise-en-scène as composition_lock 子任务)+ style_genome |
| `storyboard_designer` | DEPRECATE candidate | Phase 7 §3.4 D3.4 决定 fold storyboard into cinematographer composition_lock |
| `production` | DEFER to future milestone | 制片管理超出 v2.0 PRFP 范围(本里程碑是 pipeline 设计,不是制作执行) |

**注意:** DEPRECATE 是 **non-binding recommendation**;最终决定由后续 hermes-agent skills 演化里程碑做(per FUTURE-02)。

---

## §3 — Convergence Log(新 DAG 同意 v1 experts 设计)

| 收敛点 | 新 DAG 节点 | v1 出处 | 理由 |
|---|---|---|---|
| 14 原 experts 的核心 craft | (various nodes) | v1 14 experts | Phase 7 §3.4 D4.3 — validated-invariants 保留 |
| 4 v1 新增覆盖短剧缺口 | hook_retention + compliance + cinematographer + production | v1 Phase 1-5 | 短剧生死线 + CN 平台 + 视觉 intent + 资源(后者 deferred) |
| expert_id 不变量(FOUND-08) | 全部 16 节点保留映射 | v1 全部 expert | 创作者 workflow 不破坏 |
| 双语策略(EN+CN) | META-03 锁定 | v1 SKILL.md | 兼容性 |

---

## §4 — Divergence Log(新 DAG 不同意 v1 experts)

| Divergence 点 | 新 DAG | v1 | v1 具体 failure mode |
|---|---|---|---|
| Drawer + Animator 分离 | 合并 `visual_executor` | drawer + animator 独立 | Phase 7 §4.8 + PITFALLS §2.1:一致性 context 统一;分开 drift |
| 5 个 audio experts 分离 | 合并 `audio_pipeline` | voicer + composer + foley + mixer + spatial_audio 独立 | Phase 7 §4.9 + PITFALLS §2.6:节点膨胀 ≠ 严谨;consistency context 重复维护 |
| Continuity 非 critic 角色 | Rename `continuity_auditor` 强调 critic | continuity (supervisor) | Phase 7 §4.10:D2.5 critic 必要;rename 显式化 |
| Compliance 作为 single 节点 | `compliance_gate` (合并 pre + final) | compliance_marketing (mixed marketing + compliance) | Phase 7 §4.15:marketing 与 compliance 是不同关注;合并 pre + final |
| Storyboard 独立 expert | Folded into `cinematographer` composition_lock | storyboard_designer 独立 | Phase 7 §4.5 + §3.4 D3.4:sketch-then-render 是 instantiation;composition_lock 是 user-value |
| Performer 独立 | Folded into character_designer + screenplay | performer 独立 | Phase 7 §3.5 + §3.4 D4.3:表演真实是 character identity + dialogue subtext 的属性 |
| Scene_builder 独立 | Folded into cinematographer + style_genome | scene_builder 独立 | Phase 7 §3.5:scene 是 cinematographer 的 mise-en-scène 子任务 |
| 26 → 16 节点压缩 | 16 pipeline-roles | 26 experts | Phase 7 §3.5 + PITFALLS §2.6:节点压缩通过 invariant ownership + AI-native 合并 |

---

## §5 — 26 → 16 压缩统计

| 处置类型 | 数量 | 说明 |
|---|---|---|
| 1:1 preserved | 9 | 直接映射,expert_id 不变 |
| 1:1 renamed | 2 | continuity_auditor / compliance_gate(role 强调) |
| N:1 merge | 2(7 experts 合并) | visual_executor(2) + audio_pipeline(5-6) |
| NEW (AI-native) | 1 | prompt_injector |
| DEPRECATE candidate | 3-4 | performer / scene_builder / storyboard_designer(+ production deferred) |
| **新 DAG total** | **16** | 15 linear + 1 consultative |

**v1 → 新 DAG:** 26 experts → 16 pipeline-roles。**26 - 9 (1:1 preserved) - 2 (renamed) - 7 (merged into 2) - 1 (NEW adds 1) - 3-4 (deprecate) = -10**(净减少 10 个独立 expert)。

---

## §6 — FOUND-08 Frozen Rule Compliance

per v1 RETROSPECTIVE FOUND-08:**冻结的 expert_id 不可静默重命名**。

✓ 验证:
- 所有 1:1 preserved 节点保留原 expert_id
- Rename 节点(continuity → continuity_auditor, compliance_marketing → compliance_gate)在 `skills-mapping.yaml` 中有显式 mapping
- 合并节点(visual_executor / audio_pipeline)在 `skills-mapping.yaml` 中记录原 expert_id 集合
- 新节点(prompt_injector)标记为 NEW,不破坏现有 expert_id

---

## §7 — 给 hermes-agent skills 团队的建议

per HANDOFF-01 non-binding:

1. **不要立刻 deprecate 3-4 候选 experts** — DEPRECATE 是 v2.1+ 里程碑决定(FUTURE-02);本里程碑只标记
2. **rename 2 个节点需要 skills 团队 sign-off** — continuity_auditor + compliance_gate 的 rename 在 `skills-mapping.yaml` 中需双方 agree
3. **合并 7 个 experts → 2 个节点是 design-level 决定** — skills 实际是否合并是 v2.1+ 决定
4. **prompt_injector 是 AI-native 必要节点** — v2.1+ 应新增此 expert(无 v1 对应)

---

*Document version: design-2026-06-16-prfp*
*hermes-agent baseline_ref: 85965c393f44deae29a833f2ae98af66d26548ce*
*Phase 11 of v2.0 PRFP milestone*
