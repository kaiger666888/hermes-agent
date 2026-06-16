# 05 — Comparison vs kais-movie-agent V1-V8 Phases

> **Document status:** design-2026-06-16-prfp · supersedes: none · superseded_by: TBD
> **Phase:** 11 of v2.0 PRFP · **Source:** compares new DAG (`nodes.yaml`) vs kais-movie-agent historical V1/V2/V4.1/V6/V8 architectures
> **Binding:** `non_binding_recommendation` per HANDOFF-01 + PITFALLS §3.1
> **Stability:** stable (post-derivation delta analysis per Phase 7 §3.5)

---

## §0 — 阅读指南

本文档比较 v2.0 PRFP 新 DAG(15 linear + 1 consultative)与 kais-movie-agent V1-V8 历史架构的 **delta**。per HANDOFF-08(收敛日志),本文档同时记录 **收敛**(新 DAG 同意 V1-V8 的部分,带理由)和 **divergence**(新 DAG 不同意的部分,带 V1-V8 具体 failure mode)。

**前置阅读:** `00-FIRST-PRINCIPLES.md` §3(推导链)+ `02-NODE-SPECS.md`(新 DAG)

**kais-movie-agent baseline_ref:** `734dc71c9d5ff20d55dbd0255f367030962cf329`(per HANDOFF-04)

---

## §1 — V1-V8 历史架构回顾(per STACK §3.2)

| 版本 | 日期 | Phases/Steps | 关键架构动作 |
|---|---|---|---|
| V1 | 2026-05-18 | 10 phases | Pipeline-as-code + Git stage manager + HMAC callback + 10 phases |
| V2 | 2026-05-18 | 11 phases | AI 熔断 + voice 前置 + structured asset bus + camera split |
| V4.1 | pre-2026-05-25 | 10 phases | 哲学命名 (soul / geometry-bed / spatio-temporal) |
| V6 | 2026-05-25 | 20 steps (2 halves) | kais-soul-radar + Seedance + CosyVoice2 + consistency-agent + GPU Manager V5.1 |
| V8 | 2026-05-28 | 20 steps (preserved) | OpenClaw 唯一 LLM 收编 + gold-team direct + Toonflow |

---

## §2 — Convergence Log(新 DAG 同意 V1-V8,带理由)

per HANDOFF-08 + PITFALLS §1.4(divergence-for-divergence 警告),新 DAG 在以下点 **同意** V1-V8 的设计:

| 收敛点 | 新 DAG | V1-V8 出处 | 理由 |
|---|---|---|---|
| Pipeline root 必须有创意起源节点 | `creative_source` (Layer 0) | V6 Step 1 `kais-soul-radar` | Phase 7 §3.4 D4.1 推导出创意意图人类起源不可还原 |
| Storyboard 是显式 spec 层 | (folded into `cinematographer` composition_lock) | V1-V8 storyboard phase | 收敛:层是必要的;divergence 在 §3 |
| Storyboard 必须先于 visual generation | (作为 `cinematographer` 子任务 + `prompt_injector`) | V1-V8 linear ordering | Phase 7 §3.3 D3.4 + D3.5 推导 |
| 多 shot 一致性是 explicit concern | `continuity_auditor` + cross-cutting identity/style invariants | V6 `kais-consistency-agent` | Phase 7 §3.2 D2.4 invariant ownership |
| 配音 + 唇同步是显式节点 | (in `audio_pipeline` merged) | V6 CosyVoice2 + voice locking | Phase 7 §3.3 D3.1(a) AI 加速程序化操作 |
| 平台合规在 final gate | `compliance_gate` (Layer 6) | V1-V8 quality-gate + platform-check | Phase 7 §3.2 D2.6 CN 平台形态 |
| Hook + retention 是短剧关键 | `hook_retention` (Layer 5) | V6 短剧 pacing + 爆款 | Phase 7 §3.2 D2.6 短剧生死线 |
| Review / 审核门模式 | 2 human gates (post-screenplay + post-editor) | V1-V8 review gates | Phase 7 §3.2 PITFALLS §2.9 — 部分保留 |

---

## §3 — Divergence Log(新 DAG 不同意 V1-V8,带具体 failure mode)

per HANDOFF-08 + PITFALLS §1.4:divergence 必须有 V1-V8 具体 failure mode,不能 divergence-for-divergence。

| Divergence 点 | 新 DAG 设计 | V1-V8 设计 | V1-V8 具体 failure mode |
|---|---|---|---|
| **Linear DAG assumption** | Hybrid topology (6 layers + vertical + parallel branches + 2 loops) | V1-V8 假设 strict linear sequence | Phase 7 §3.1 D1.2:V1-V8 把 scenario/storyboard/shots 当 sequential 阶段,但整合体验是 joint property — sequential 分离是 workflow 偶然不是体验本质 |
| **JSON asset bus** | Cross-cutting invariants (style_genome + character_designer 显式 ownership,所有下游消费) | V1-V8 structured asset bus (art-bible / character / voice-timeline / shot-list / scene-assets 分散 JSON) | Phase 7 §3.2 D2.3+D2.4:独立 JSON 独立优化损害跨节点 coherence;invariant 需显式 owner |
| **20-step granularity** | 16 pipeline-roles (15 linear + 1 consultative) | V6/V8 20 steps (10 创意 + 10 生产) | Phase 7 §3.5 + PITFALLS §2.6:更多节点 ≠ 更严谨;20 步粒度从 V1 10 phases 演化而来,缺第一性原理重新推导 |
| **Full LLM orchestration** | Layered execution (root → intent → visual → exec → gates);LLM 不编排一切 | V8 OpenClaw Agent 唯一 LLM 收编编排 | Phase 7 §3.1 D1.4:当前 LLM 不能端到端一次产出整合体验;V8 假设足够,但 2026-Q2 模型不够 |
| **Sketch-then-render 两阶段** | `composition_lock` 是 user-value 层;sketch-then-render 是 instantiation(dated annex) | V8 Phase 5.3/5.5 强制两阶段 | Phase 7 §3.3 D3.4 + PITFALLS §1.3:sketch-then-render 是当前模型 workaround,不是第一性原理必要 |
| **Theory-critic blocking gate** | Consultative vertical edge (META-06,creator-pulled) | V8 审核门 as blocking in linear sequence | Phase 7 §3.4 D4.4 + AF-12:theory_critic blocking 杀短剧 throughput |
| **Model name in node spec** | Capability-spec canonical;model names ONLY in dated annex (§2.17) | V1-V8 hard-codes Sora/Kling/Veo/CosyVoice in specs | Phase 7 §3.3 D3.4 + PITFALLS §1.3 + §2.7:v1 已被 wan22_video phantom 烧过;v2.0 必须避免 |
| **每 visual phase 后 human review** | 2 explicit human gates (high-leverage seams only) | V1-V8 review gate after every visual phase | Phase 7 §3.2 PITFALLS §2.9:过度 review 杀 throughput;只高 leverage seam 保留 |
| **10 phases → 16 pipeline-roles** | 16 (15 linear + 1 consultative),复杂度加权 | V1 10 phases | Phase 7 §3.5:新 DAG 包括 V1 缺的 critic 配对(script_auditor + continuity_auditor + quality_gate)+ AI-native (prompt_injector)+ 形态特定 (hook_retention)+ 咨询 (theory_critic) |

---

## §4 — 收敛 vs Divergence 统计

| 类型 | 数量 | 说明 |
|---|---|---|
| Convergence (同意 V1-V8) | 8 | 新 DAG 在 root / storyboard / 一致性 / 配音 / 平台 / hook / review 等点收敛 |
| Divergence (不同意 V1-V8,有 failure mode) | 9 | 新 DAG 在 linear / JSON bus / 20-step / full-LLM / sketch-then-render / blocking critic / 模型名 / 每 phase review / 节点数 等点 divergence |

**8:9 平衡** — 新 DAG 既不是 V1-V8 的翻版(纯 convergence),也不是 divergence-for-divergence(纯 divergence)。

---

## §5 — V8 Architecture 残留(Phase 11 决定保留 / 弃用)

per PITFALLS Open Question #3(V8 审核门 survival):

| V8 元素 | 新 DAG 决定 | 理由 |
|---|---|---|
| Git stage manager | 保留(implementation detail,kais 决定) | 不影响 DAG 形态 |
| HMAC callback server | 保留(impl detail) | 不影响 DAG 形态 |
| GPU Runtime Manager V5.1 (3090/3060Ti split) | 保留(impl detail) | 不影响 DAG 形态 |
| OpenClaw Agent 唯一 LLM | 弃用 | Divergence #4 |
| Toonflow review platform | 弃用(per-direction:不在 v2.0 DAG 内) | 不在 v2.0 范围 |
| gold-team direct connect | 保留(impl detail — visual_executor instantiation) | 在 §2.17 dated annex |
| Sketch-then-render 两阶段 | 作为 instantiation 弃用;作为 capability 保留 | Divergence #5 |
| 20 steps | 弃用 | Divergence #3 |

---

## §6 — 给 kais-movie-agent 团队的建议

per HANDOFF-01 non-binding:

1. **不要直接重写 V8 → v2.0** — v2.0 是 design-doc;V8 是 working code。建议渐进迁移(per §7 HANDOFF-PLAN)。
2. **Divergence 优先级排序** — Divergence #4 (full-LLM orchestration) 和 #6 (blocking theory_critic) 是 throughput 杀手,优先实施。Divergence #3 (节点数) 是 organizational,可后置。
3. **Convergence 不要折腾** — 8 个收敛点保留 V8 已有实现,不要重写。
4. **Model-name cleanup** — Divergence #7 是技术债清理,可与 divergence 其他项并行。

---

*Document version: design-2026-06-16-prfp*
*kais-movie-agent baseline_ref: 734dc71c9d5ff20d55dbd0255f367030962cf329*
*Phase 11 of v2.0 PRFP milestone*
