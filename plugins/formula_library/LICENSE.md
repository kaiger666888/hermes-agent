# License — Formula Library Plugin

**Plugin:** `plugins/formula_library/`
**Milestone:** v9.0 Phase 39 FORM (FORM-03 seed formulas)
**Last-verified:** 2026-06-26

---

## Fair Use Declaration

All formula content in `plugins/formula_library/library/*.json` is **fair-use** material. No copyrighted script, dialogue, character likeness, or protected creative work is reproduced.

Concretely:

- **Factual strategy specs** from Notion page `32811082-af8e-8009-b097-d19a5027b46f` (Kai's canonical "心流♥ → aigc开发 → 创作方向" doc) are reproduced with attribution. These are factual roadmap / spec statements (platform 内容形态, runtime specs, monetization coefficients), not creative writing. `fair_use_status: verbatim-spec`.
- **Methodology patterns** from public 短剧 创作指南 / 爆款公式书 (e.g. 《短视频爆款公式》、《短剧创作指南》) are **paraphrased** into our own analytical wording. No verbatim chapter text, example cases, or chart reproductions. `fair_use_status: paraphrased`.
- **Historical benchmark analyses** from `kais-movie-agent` benchmark runs (kais-bench-*-01) are **derived analyses** — our original interpretation of aggregated run data. No reproduction of any third-party benchmark. `fair_use_status: derived-analysis`.
- **3-second hook references** cite `three-second-hooks.md` (Hermes Agent's own ref, itself fair-use aggregated observation) by example number + type — no verbatim hook scripts reproduced here.

Per `CLAUDE.md` §Copyright rule and REQUIREMENTS.md §FORM-03 fair-use citation discipline (SC#4), every formula JSON carries a non-null `citation.source` from one of three allowed source types: `notion` / `public-book` / `kais-benchmark`. No uncited formulas ship.

---

## Source List

| Source | Type | Fair-Use Status | Used By Formulas |
|--------|------|-----------------|------------------|
| Notion page `32811082-af8e-8009-b097-d19a5027b46f` ("心流♥ → aigc开发 → 创作方向") | `notion` | `verbatim-spec` + `paraphrased` | `urban-fantasy-light-01`, `urban-fantasy-angst-01`, `family-emotion-light-01`, `workplace-light-01`, `workplace-angst-01` |
| 公开爆款公式书《短视频爆款公式》 | `public-book` | `paraphrased` | `mystery-twist-light-01`, `family-emotion-light-01`, `campus-youth-light-01`, `campus-youth-angst-01`, `workplace-light-01` |
| 公开爆款公式书《短剧创作指南》 | `public-book` | `paraphrased` | `mystery-twist-light-01`, `family-emotion-light-01`, `family-emotion-angst-01`, `urban-fantasy-angst-01` |
| `three-second-hooks.md` (Hermes Agent own ref, fair-use aggregated observation) | `kais-benchmark` (downstream) | `paraphrased` (example references only) | `mystery-twist-angst-01` (示例 4), `family-emotion-angst-01` (示例 14), `workplace-angst-01` (示例 7) |
| `kais-movie-agent` historical benchmark (`kais-bench-campus-01`, `kais-bench-campus-angst-01`, `kais-bench-mystery-angst-01`) | `kais-benchmark` | `derived-analysis` | `campus-youth-light-01`, `campus-youth-angst-01`, `mystery-twist-angst-01` |

> **Note on multi-source formulas:** several formulas cite 2 sources (e.g. Notion + public-book). The `citation.source_type` field picks the *primary* source type per formula. Multi-source citations are visible in the verbatim `citation.source` string in the Per-Formula Attribution section below.

---

## Per-Formula Attribution

This is the audit trail. Each formula_id is listed with its **verbatim** `citation.source` string (exactly as it appears in the JSON file). If any string below fails to match the corresponding JSON, that is a Rule 1 bug — fix the LICENSE (not the JSON) to match.

### 轻喜剧 (light) — 5 formulas

- **`urban-fantasy-light-01`** (都市奇幻 × 轻喜剧):
  `Notion 创作方向 page 32811082-af8e-8009-b097-d19a5027b46f §核心 DNA + §per-platform 内容形态 (抖音 超能力高光切片 15-60s 竖屏)`
  — source_type: `notion`, fair_use_status: `verbatim-spec`

- **`mystery-twist-light-01`** (悬疑反转 × 轻喜剧):
  `公开爆款公式书《短视频爆款公式》§悬疑反转章 (轻量悬疑 + 喜剧性揭底, 60s 抖音/B站适用)`
  — source_type: `public-book`, fair_use_status: `paraphrased`

- **`family-emotion-light-01`** (家庭情感 × 轻喜剧):
  `Notion 创作方向 page 32811082-af8e-8009-b097-d19a5027b46f §家庭情感 + 公开爆款公式书《短剧创作指南》§家庭和解章 (母子和解 60s 视频号-optimized)`
  — source_type: `notion`, fair_use_status: `paraphrased`

- **`campus-youth-light-01`** (校园青春 × 轻喜剧):
  `kais-movie-agent historical benchmark kais-bench-campus-01 (run 2026-Q1; 学霸vs学渣 反差钩 + 校园 60s 快手-optimized) + 公开爆款公式书《短视频爆款公式》§校园青春章`
  — source_type: `kais-benchmark`, fair_use_status: `derived-analysis`

- **`workplace-light-01`** (职场商战 × 轻喜剧):
  `Notion 创作方向 page 32811082-af8e-8009-b097-d19a5027b46f §职场商战 + 公开爆款公式书《短视频爆款公式》§职场逆袭章 (underdog 董事会打脸 60s 抖音-optimized)`
  — source_type: `notion`, fair_use_status: `paraphrased`

### 虐心 (angst) — 5 formulas

- **`urban-fantasy-angst-01`** (都市奇幻 × 虐心):
  `Notion 创作方向 page 32811082-af8e-8009-b097-d19a5027b46f §题材禁忌 (negative example — what NOT to do: 重口狗血/悲剧收尾) + 公开爆款公式书《短剧创作指南》§超能力代价章 (超能力读心揭穿背叛, 90s 视频号-optimized)`
  — source_type: `notion`, fair_use_status: `paraphrased`

- **`mystery-twist-angst-01`** (悬疑反转 × 虐心):
  `three-second-hooks.md §悬念钩 示例 4 死亡后第一通电话 (revenge 重生题材 0-1s 反常规切入) + kais-movie-agent historical benchmark kais-bench-mystery-angst-01 (run 2026-Q1; 悬疑揭痛 60s 抖音-optimized)`
  — source_type: `kais-benchmark`, fair_use_status: `derived-analysis`

- **`family-emotion-angst-01`** (家庭情感 × 虐心):
  `three-second-hooks.md §情绪爆点钩 示例 14 母亲最后的语音 (family 题材 0-1s 强音效+内容冲击) + 公开爆款公式书《短剧创作指南》§家庭失去章 (母亲牺牲/最后语音 60s 抖音-optimized)`
  — source_type: `public-book`, fair_use_status: `paraphrased`

- **`campus-youth-angst-01`** (校园青春 × 虐心):
  `公开爆款公式书《短视频爆款公式》§校园青春虐心章 (青春友谊背叛/失去) + kais-movie-agent historical benchmark kais-bench-campus-angst-01 (run 2026-Q1; 校园虐心 90s 快手-optimized)`
  — source_type: `kais-benchmark`, fair_use_status: `derived-analysis`

- **`workplace-angst-01`** (职场商战 × 虐心):
  `three-second-hooks.md §冲突钩 示例 7 董事会逼宫 (revenge 商战 0-1s 同步推信) + Notion 创作方向 page 32811082-af8e-8009-b097-d19a5027b46f §职场商战 (悲剧转向: 职场陷害坠落 60s 抖音-optimized)`
  — source_type: `notion`, fair_use_status: `paraphrased`

---

## Cross-References

- [`skills/kais-movie-pipeline/references/genre-anchor-urban-fantasy.md`](../../skills/kais-movie-pipeline/references/genre-anchor-urban-fantasy.md) — V1 题材锚定 (都市奇幻·轻喜剧); primary source for `urban-fantasy-light-01`
- [`skills/movie-experts/hook_retention/references/three-second-hooks.md`](../../skills/movie-experts/hook_retention/references/three-second-hooks.md) — 3 秒钩子 5-type taxonomy (hook_pattern 字段源 + angst formulas 示例 4/14/7 引用源)
- [`skills/movie-experts/style_genome/references/scamper-variations.md`](../../skills/movie-experts/style_genome/references/scamper-variations.md) — SCAMPER variation engine (formula variation patterns, V9-FUTURE-03 expansion reference)
- [`skills/movie-experts/compliance_gate/references/cn-content-rules.md`](../../skills/movie-experts/compliance_gate/references/cn-content-rules.md) — CN content compliance baseline (formulas respect §题材禁忌 + 8-category red lines; 虐心 = emotional weight, NOT graphic content)

---

## Refresh Cadence

- **常规复审周期:** 每 90 天 (mirrors `three-second-hooks.md` cadence).
- **下次复审日期:** 2026-09-26.
- **责任方:** `formula_library` plugin (no human owner — this is a Hermes Agent plugin, not a team responsibility).
- **复审动作:**
  1. 跟踪 抖音 / 快手 / B站 / 小红书 / 视频号 / 红果 6 平台短剧榜 top 10,识别新兴题材 × 情绪 组合。
  2. 复核 10 个 seed formulas 的 `platform_fit` scores 是否仍准确(平台算法权重变化会影响这些分数)。
  3. 复核 `citation.source` 链接是否仍有效(Notion page / 公开书版本 / benchmark run 可访问性)。
  4. 在 V9-FUTURE-03 (50+ formulas 扩展) 启动时,新增的 formula 必须遵循同样的 fair-use + citation 强约束。
- **过期处理:** 若 LICENSE.md 超过 90 天未更新,`formula_library` plugin 在启动时 log warning(待 Plan 01 schema.py 添加此 check)。

---

*License authored: 2026-06-26 — v9.0 Phase 39 Plan 39-02 (FORM-03 seed formulas).*
*All 10 formula_ids attributed. Zero uncited formulas.*
