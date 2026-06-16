# README — v2.0 PRFP Design Suite

> **kais-movie-agent v2.0 工作流节点集设计套件**
> Version: `design-2026-06-16-prfp`
> Milestone: v2.0 PRFP (Pipeline Redesign from First Principles)
> Phase: Complete (7-12 all passed)
> Reading time: 10 minutes (executive summary);30+ minutes (full design)

---

## 这是什么?

**v2.0 PRFP** 是 kais-movie-agent 短剧/微电影 AIGC 工作流的 **第一性原理重新设计**。它从 4 个不可还原问题("观众消费什么?" / "什么决定质量?" / "AI 能加速什么?" / "AI 不能替代什么?")出发,逐步推导出 16 个 pipeline-roles(15 linear + 1 consultative)的节点集。

**为什么重要:** 现有 kais-movie-agent V8 + hermes-agent 26 experts 是 **演化** 出来的(类比推理),不是 **推导** 出来的。v2.0 PRFP 用 Musk 式第一性原理重新问"为什么是它而不是别的",并显式避免第一性原理剧场(PITFALLS §1)。

**约束:** 本里程碑只产出 **设计文档**,零代码改动(META-01/02)。`scripts/validate_design.py` 是唯一例外。

---

## 给 3 类读者的 10 分钟入口

### A. kais-movie-agent 实施团队
**读这个顺序:**
1. 本 README(10 min)
2. `07-HANDOFF-PLAN.md §4` Impl-Cheatsheet(5 min)
3. `01-NODE-DAG.md` 看 DAG 形态 + Mermaid 图(5 min)
4. `02-NODE-SPECS.md §2.17` 看 dated model annex(2 min)

**关键决策权:** kais 团队有 binding 决定权 — 是否实施 v2.0 设计(non-binding recommendation)。若实施,declare `impl_targets_design: design-2026-06-16-prfp`。

### B. hermes-agent skills 团队
**读这个顺序:**
1. 本 README(10 min)
2. `06-COMPARISON-VS-26-SKILLS.md` 看 26 → 16 压缩(5 min)
3. `skills-mapping.yaml` 看 expert_id 映射(5 min)
4. `00-FIRST-PRINCIPLES.md §3` 看推导链(10 min)

**关键决策权:** skills 团队决定 v2.1+ 是否启动(per FUTURE-02)。3-4 deprecate candidates + 2 rename sign-offs 待定。

### C. 未来设计维护者
**读这个顺序:**
1. 本 README(10 min)
2. `00-FIRST-PRINCIPLES.md` 全文(30 min)
3. `08-GOVERNANCE.md` G1-G7 规则(5 min)
4. `09-OPEN-QUESTIONS.md` 21 个 gap(5 min)
5. `scripts/validate_design.py` 看 lint 实现(5 min)

---

## 设计核心结论(3 句话)

1. **16 节点 DAG**(15 linear + 1 consultative theory_critic)从 4 个第一性问题推导而来,8:9 收敛率 vs kais V1-V8(不是 divergence-for-divergence)。
2. **¥8000/episode** 总成本(META-05 ¥10000 内),复杂度加权分布,visual_executor 最贵(¥3500)。
3. **零代码承诺:** 设计套件不动 hermes-agent/skills/ 或 kais-movie-agent/lib/ 任何文件。impl 是 non-binding recommendation。

---

## 5 个最重要的设计决策(为什么不是别的?)

| 决策 | 为什么不是其他 |
|---|---|
| **`creative_source` 是 root + AI-bounded** | 不是 `auto_story_generator`(违反 D4.1 novelty 来自生活经验);不是 fold into downstream(integration 是 joint property 不能拆) |
| **`theory_critic` 是 consultative 垂直边,不是 blocking gate** | AF-12:阻塞短剧 throughput;META-06:creator-pulled 不 auto-invoke |
| **drawer + animator 合并为 `visual_executor`** | 不是分开(consistency context 统一;PITFALLS §2.1 compression);不是 fold into cinematographer(intent vs execution 层次混淆) |
| **5 个 audio experts 合并为 `audio_pipeline`** | 不是 5 个独立(节点膨胀;PITFALLS §2.6);不是 2-way split(foley 边界模糊) |
| **Model names 只在 §2.17 dated annex** | 不在 canonical spec(v1 wan22_video phantom 已烧过;PITFALLS §1.3) |

---

## 文档清单(13 artifacts)

```
.planning/research/v2-pipeline-design/
├── README.md (本文档 — 3 页 exec summary)
├── 00-FIRST-PRINCIPLES.md (Phase 7 — 4 问题推导 + 16 节点候选)
├── 01-NODE-DAG.md (Phase 8 — DAG 拓扑 + C1-C7 audit + Mermaid)
├── 02-NODE-SPECS.md (Phase 8 — per-node 15 spec fields + dated model annex)
├── 03-CORPUS-TRACEABILITY.md (Phase 9 — 102 书 ↔ 节点双向矩阵)
├── 04-LLM-CREATIVE-DISTILLATION.md (Phase 10 — 创意操作性定义 + 自洽机制)
├── 05-COMPARISON-VS-8-PHASES.md (Phase 11 — vs kais V1-V8 delta)
├── 06-COMPARISON-VS-26-SKILLS.md (Phase 11 — vs hermes 26 experts delta)
├── 07-HANDOFF-PLAN.md (Phase 11 — 非约束交接 + ownership matrix + impl-cheatsheet)
├── 08-GOVERNANCE.md (Phase 12 — G1-G7 living-doc governance)
├── 09-OPEN-QUESTIONS.md (Phase 12 — 21 个 gap feeding downstream research)
├── 10-CHANGELOG.md (Phase 12 — append-only audit trail)
├── nodes.yaml (canonical source of truth — 16 节点)
├── edges.yaml (canonical source — 28 edges 4 types)
├── corpus-trace.yaml (canonical — 16 节点 × 40 书)
├── skills-mapping.yaml (canonical — 节点 ↔ v1 expert_id)
├── kais-migration-matrix.yaml (canonical — 节点 ↔ V8 step + lib/)
└── scripts/
    └── validate_design.py (Phase 12 GOV-02 lint — 唯一代码)
```

**总规模:** 13 docs + 5 YAMLs + 1 Python lint = ~340KB content;1638 行 00-FIRST-PRINCIPLES.md + 1016 行 corpus-trace.yaml 是最大两个文件。

---

## 关键 invariants(META)

| META | 描述 | 状态 |
|---|---|---|
| META-01 | 零 SKILL.md 编辑 | ✓ 全里程碑 0 文件修改 |
| META-02 | 零 .js/.py 编辑(除 validate_design.py) | ✓ 仅 1 个 ~30 行 lint |
| META-03 | 双语 EN structure + CN prose | ✓ 全部 docs |
| META-04 | 物理位置 .planning/research/v2-pipeline-design/ | ✓ 全部 artifacts |
| META-05 | 成本 ceiling ¥1000-10000/episode | ✓ 总 ¥8000 |
| META-06 | theory_critic creator-pulled | ✓ consultative |

---

## 如何检验设计质量

```bash
cd .planning/research/v2-pipeline-design
python3 scripts/validate_design.py
```

应输出:
```
PASS — 15 linear nodes, all 16 spec'd, model names isolated, versions stamped, no forbidden phrases.
```

7 个 governance check(G1-G7):
- G1: 节点数 [8, 25] ✓
- G2: 每节点 15 spec fields ✓
- G3: 模型名只在 §2.17 ✓
- G4: 版本 stamp + supersedes ✓
- G5: Stability markers ✓
- G6: 无 forbidden phrases ✓
- G7: YAML 合法 ✓

---

## 下一步(给操作者)

设计套件 frozen-pending-impl。两个 repo 的下游团队决定是否实施:

1. **kais-movie-agent impl team:** review `07-HANDOFF-PLAN.md §4` cheatsheet → decide impl → declare `impl_targets_design`
2. **hermes-agent skills team:** review `skills-mapping.yaml` → decide v2.1+ milestone → resolve deprecate/rename/merge decisions
3. **未来研究者:** `09-OPEN-QUESTIONS.md` 的 21 个 gap 是研究 backlog;按 confidence + blocking 优先级排序

---

## 联系

设计套件 maintainer:hermes-agent design team
版本:`design-2026-06-16-prfp`
下次 major revision:`TBD`(superseded_by 字段填)

---

*v2.0 PRFP design suite — Pipeline Redesign from First Principles*
*Shipped 2026-06-16*
