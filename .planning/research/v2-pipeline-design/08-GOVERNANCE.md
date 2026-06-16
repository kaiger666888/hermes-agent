# 08 — Governance Rules

> **Document status:** design-2026-06-16-prfp · supersedes: none · superseded_by: TBD
> **Phase:** 12 of v2.0 PRFP · **Stability:** stable

---

## §0 — 阅读指南

本文档定义 v2.0 PRFP 设计套件的 **living-doc governance rules**(G1-G7)。规则由 `scripts/validate_design.py` (~30 行 lint)强制执行(GOV-02)。

---

## §1 — G1: Node-count governance

**Rule:** linear node count 必须 `8 ≤ count ≤ 25`(target 8-15,hard ceiling 25)。

**Modification trigger:** 添加节点需重新推导(per Phase 7 §3 derivation discipline)。
- 超过 15 需 §5.2 over-target justification
- 超过 25 = milestone-level 决定,不是 phase-level

**Lint check:** `validate_design.py G1`

---

## §2 — G2: Per-node field governance

**Rule:** 每个 node 必须有 15 spec fields 全部 populated(per NODE-02/03/04):
- 4 core: core_task / io_contract / aigc_transformation / traditional_anchor
- 8 STACK: success_criteria (≥1 quantified) / fail_modes / fallback_strategy / dependencies / complexity_class / ai_capability_assumption / non_ai_alternative / rationale_for_existence
- 3 budget: cost_budget / latency_budget / model_horizon

**Modification trigger:** 字段变更需 sign-off(per HANDOFF-05 ownership matrix)。

**Lint check:** `validate_design.py G2`

---

## §3 — G3: Model-name isolation governance (NODE-08)

**Rule:** model names (Claude / GPT / Sora / Kling / Veo / FLUX / CosyVoice / Suno / Udio / Gemini / GLM / Stable Diffusion) **只在** `02-NODE-SPECS.md §2.17 Global Model Annex` 出现。

**Rationale:** 防 PITFALLS §1.3 + §2.7 过早模型承诺;canonical capability-spec 必须 model-agnostic。

**Modification trigger:** 模型 instantiation 变化只更新 §2.17(季度 refresh),不动 §2.1-§2.16 canonical spec。

**Lint check:** `validate_design.py G3`(regex 扫 §2.17 之外的内容)

---

## §4 — G4: Version stamp governance

**Rule:** 每个 doc 必须声明:
- `design_version: design-2026-06-16-prfp`
- `supersedes: <previous-version> | none`
- `superseded_by: <next-version> | TBD`

**Modification trigger:** 任何 design revision 需新 dated version(per HANDOFF-06);旧版本 frozen 一旦 impl target 它。

**Lint check:** `validate_design.py G4`

---

## §5 — G5: Stability marker governance

**Rule:** 每个 doc 必须声明 Stability:`stable` / `evolving` / `experimental`。

| Stability | 修改门槛 |
|---|---|
| `stable` | design-revision milestone + cross-repo sign-off |
| `evolving` | v2.0 PRFP 内迭代 + CHANGELOG entry |
| `experimental` | 自由编辑 |

**Lint check:** `validate_design.py G5`

---

## §6 — G6: Forbidden-phrase governance

**Rule:** 以下短语 **不允许** 出现在 derivation 章节(`00-FIRST-PRINCIPLES.md §3`):
- "obviously"
- "every pipeline has"
- "traditionally"

**Rationale:** 防 PITFALLS §1.1 第一性原理剧场。

**Modification trigger:** 如果出现 = design 失败,必须重新推导。

**Lint check:** `validate_design.py G6`

---

## §7 — G7: Status transition governance

**Rule:** design 状态转换需通过 review gates:

```
draft → review → stable → frozen (when impl targets) → superseded (when new version ships)
```

每个 transition 需:
- CHANGELOG entry(`10-CHANGELOG.md`)
- Decision / Rationale / Outcome 三段式记录(per PITFALLS §7.4)
- 若 structural change:cross-repo sign-off(per HANDOFF-05)

**Lint check:** 手动 review + CHANGELOG grep。

---

## §8 — Governance enforcement

`scripts/validate_design.py` 是 pre-commit hook(本里程碑唯一的代码,per META-02 exception)。

运行:
```bash
cd .planning/research/v2-pipeline-design
python3 scripts/validate_design.py
```

Exit 0 = pass;Exit 1 = violations + 列表。

每次 design 修改必须 lint pass 才能 commit。Phase 12 verification 后,本 lint 成为 living-doc governance 的强制层。

---

*Document version: design-2026-06-16-prfp*
*Phase 12 of v2.0 PRFP milestone*
