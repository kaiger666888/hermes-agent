# Formula Library Plugin (配方库插件)

> v9.0 Phase 39 FORM — persists proven 爆款 (hit) formulas as JSON; lookup tool returns top-k by `genre × mood × platform`. Integrated as Step 0 of `kais-movie-pipeline` (per FORM-04).

---

## What This Is

**EN:** The Formula Library is a standalone Hermes Agent plugin that ships 10 seed short-drama formulas covering a 5-genre × 2-mood matrix. Each formula is a JSON record validated by a Pydantic schema (Plan 39-01). The plugin exposes a `formula_lookup` tool that ranks formulas by per-platform fit score and returns the top-k. It is wired in as **Step 0** of `kais-movie-pipeline` (before p01 hook_topic) and as an optional `formula_reference` input to `theory_critic`.

**中文:** 配方库插件以 JSON 文件持久化已验证的短剧爆款公式。当前 v9.0 ship 10 条种子公式,覆盖 5 题材 × 2 情绪的完整矩阵。每条公式由 Pydantic schema(Plan 39-01)严格校验,字段包括 `formula_id` / `genre` / `mood` / `pacing` / `hook_pattern` / `characters` / `runtime_sec` / `platform_fit` / `citation` / `verified_date` / `eval_score`。插件提供 `formula_lookup` 工具,按平台契合度(fit_score)降序返回 top-k 公式。该工具作为 `kais-movie-pipeline` 的 **Step 0**(在 p01 hook_topic 之前)和 `theory_critic` 的可选 `formula_reference` 输入接入(per FORM-04)。

---

## Schema

每条 formula JSON 包含以下 11 个字段(详见 Plan 39-01 `schema.py::Formula`):

| Field | Type | Description |
|-------|------|-------------|
| `formula_id` | str | 唯一 kebab-case 标识符 (e.g. `urban-fantasy-light-01`) |
| `genre` | enum (5) | 题材: 都市奇幻 / 悬疑反转 / 家庭情感 / 校园青春 / 职场商战 |
| `mood` | enum (2) | 情绪基调: 轻喜剧 / 虐心 |
| `pacing` | str | 节奏: `fast-cut` (快剪) / `mid-tempo` (中速) / `slow-burn` (慢炖) |
| `hook_pattern` | enum (5) | 3 秒钩子类型 (per `three-second-hooks.md`): `emotional` / `suspense` / `conflict` / `contrast` / `emotional_peak` |
| `characters` | list[str] | 2-5 个 archetype slugs (e.g. `hidden-boss`, `underdog-rookie`, `tragic-mentor`) |
| `runtime_sec` | int | 单集时长(秒), 范围 [60, 600] |
| `platform_fit` | list[{platform, fit_score}] | 2-6 个平台契合度评分; platform ∈ 6 平台枚举; fit_score ∈ [0.0, 1.0] |
| `citation` | object | 公平使用来源标注: `{source, source_type, fair_use_status, verified_date}` — `source_type` ∈ `notion` / `public-book` / `kais-benchmark` |
| `verified_date` | date | 顶层 ISO 日期 (YYYY-MM-DD); seed formulas = `2026-06-26` |
| `eval_score` | float \| null | 可选,从 v6.0 eval gate 回填; seed formulas = `null` |

---

## Library

10 seed formulas 覆盖 5 × 2 矩阵(v9.0 ship no eval scores — V9-FUTURE-03 扩展到 50+ 时再回填):

### 都市奇幻 (Urban Fantasy)

- **`urban-fantasy-light-01`** — 超能力 + 轻喜剧 + 主线悬念; 90s; 抖音-top 0.92. Source: Notion §核心 DNA verbatim-spec.
- **`urban-fantasy-angst-01`** — 超能力读心揭穿背叛; 90s; 视频号-top 0.88. Source: Notion §题材禁忌 + 公开书 paraphrased.

### 悬疑反转 (Mystery / Twist)

- **`mystery-twist-light-01`** — 轻量悬疑 + 喜剧性揭底; 60s; B站-top 0.88. Source: 公开爆款公式书 paraphrased.
- **`mystery-twist-angst-01`** — 死亡后第一通电话(重生复仇); 60s; 抖音-top 0.90. Source: three-second-hooks 示例 4 + kais-bench derived-analysis.

### 家庭情感 (Family Emotion)

- **`family-emotion-light-01`** — 母子和解轻喜剧; 60s; 视频号-top 0.90. Source: Notion §家庭情感 + 公开书 paraphrased.
- **`family-emotion-angst-01`** — 母亲最后的语音; 60s; 抖音-top 0.89. Source: three-second-hooks 示例 14 + 公开书 paraphrased.

### 校园青春 (Campus / Youth)

- **`campus-youth-light-01`** — 学霸 vs 学渣 反差; 60s; 快手-top 0.88. Source: kais-bench-campus-01 + 公开书 derived-analysis.
- **`campus-youth-angst-01`** — 校园友谊背叛; 90s; 快手-top 0.86. Source: 公开书 + kais-bench-campus-angst-01 derived-analysis.

### 职场商战 (Workplace / Corporate)

- **`workplace-light-01`** — Underdog 董事会打脸; 60s; 抖音-top 0.87. Source: Notion §职场商战 + 公开书 paraphrased.
- **`workplace-angst-01`** — 职场陷害坠落(董事会逼宫悲剧转向); 60s; 抖音-top 0.88. Source: three-second-hooks 示例 7 + Notion paraphrased.

---

## Usage

`formula_lookup` 工具的调用契约(由 Plan 39-01 `tools.py` 注册,Plan 39-03 在 SKILL.md 中文档化):

```python
# Top-3 都市奇幻 × 轻喜剧 公式 for 抖音
result = formula_lookup(
    genre="都市奇幻",      # required, 5-value enum
    mood="轻喜剧",         # required, 2-value enum
    platform="抖音",       # required, 6-value enum
    top_k=3,               # optional, default 3
)
```

返回 shape(由 Plan 39-01 `_handle_formula_lookup` 包装为 tool_result envelope):

```json
{
  "formulas": [
    {
      "formula_id": "urban-fantasy-light-01",
      "genre": "都市奇幻",
      "mood": "轻喜剧",
      "pacing": "fast-cut",
      "hook_pattern": "contrast",
      "characters": ["hidden-boss", "everyman-sidekick", "foiled-rival"],
      "runtime_sec": 90,
      "platform_fit": [
        {"platform": "抖音", "fit_score": 0.92},
        {"platform": "快手", "fit_score": 0.82}
      ],
      "citation": { "source": "...", "source_type": "notion", "fair_use_status": "verbatim-spec", "verified_date": "2026-06-26" },
      "verified_date": "2026-06-26",
      "eval_score": null
    }
  ]
}
```

排序规则:严格匹配 `genre + mood`,然后按 `platform_fit[platform].fit_score` 降序;并列时按 `formula_id` 升序(确定性排序,测试稳定)。

---

## Adding Formulas

向 `library/` 目录添加新公式:

1. 创建新 JSON 文件,文件名遵循 `formula_{genre_slug}_{mood_slug}_{NN}.json` convention (e.g. `formula_urban_fantasy_light_02.json`)。Genre slug 映射: `都市奇幻→urban-fantasy` / `悬疑反转→mystery-twist` / `家庭情感→family-emotion` / `校园青春→campus-youth` / `职场商战→workplace`. Mood slug: `轻喜剧→light` / `虐心→angst`.
2. 填入所有 11 个 schema-required 字段(参见上方 §Schema 表)。`citation.source` 必须非空,`source_type` 必须是 `notion` / `public-book` / `kais-benchmark` 之一。
3. 运行 Plan 39-03 的 schema 验证测试: `python -m pytest plugins/formula_library/tests/test_schema.py -v`。Pydantic 会拒绝缺字段 / 越界值 / 非法 enum。
4. 在 `LICENSE.md` §Per-Formula Attribution 添加新 `formula_id` + 完整 `citation.source` 字符串(逐字复制)。
5. 在本 README §Library 添加一行,格式 `[formula_id] — 简短描述; Xs; platform-top Y.YY. Source: ...`.
6. Commit 时确保 JSON + LICENSE + README 三处一致(Plan 39-03 byte-diff 测试会校验)。

> **重要:** 不允许 ship 任何 `citation.source` 为空的公式。Fair-use 是法律强约束,不是可选 metadata。

---

## Integration

### kais-movie-pipeline Step 0 (FORM-04)

`formula_lookup` 作为 `kais-movie-pipeline` 的 **Step 0** 接入(由 Plan 39-03 在 SKILL.md body 添加新 `## Step 0 — Formula Lookup (Phase 39 v9.0)` section,frontmatter byte-frozen per FOUND-08)。Step 0 在所有 V8.6 13 步之前执行,产出 `formulas[0]` (top-1) 作为:
- **Step 1 (p01 hook_topic)** 的可选输入 —— `hook_retention` 专家可参考公式 `hook_pattern` + `characters` 设计本集 3 秒钩子。
- **theory_critic** 的可选 `formula_reference` 输入(见下)。

Step 0 是 **additive** —— 不重排 V8.6 13-step 编号;即使 library 加载失败 / 无匹配公式,管线仍可从 Step 1 正常启动。

### theory_critic formula_reference (FORM-04)

`theory_critic/SKILL.md` body 新增 `## Formula Reference Integration (Phase 39 v9.0)` section(同样 frontmatter byte-frozen per FOUND-08),接受可选输入 `formula_reference: Formula | None`(默认 None)。当非 None 时,theory_critic 在批评输出中:
1. 比对作品与公式契合度(genre + mood + pacing + hook_pattern 区间)
2. 标注偏离公式的创新点,评估理论合理性
3. 透传 `formula_reference.eval_score` 作为 baseline 参考

---

## License

See [LICENSE.md](./LICENSE.md) for full fair-use attribution. Tl;dr: all 10 formulas are fair-use (factual specs verbatim with attribution / paraphrased methodology / derived analyses); no copyrighted script or dialogue reproduced.

---

## References

- [`skills/kais-movie-pipeline/references/genre-anchor-urban-fantasy.md`](../../skills/kais-movie-pipeline/references/genre-anchor-urban-fantasy.md) — V1 题材锚定 (都市奇幻·轻喜剧); primary source for `urban-fantasy-light-01`.
- [`skills/movie-experts/hook_retention/references/three-second-hooks.md`](../../skills/movie-experts/hook_retention/references/three-second-hooks.md) — 3 秒钩子 5-type taxonomy; source for `hook_pattern` field + angst formulas 示例 4/14/7 引用.
- [`skills/movie-experts/style_genome/references/scamper-variations.md`](../../skills/movie-experts/style_genome/references/scamper-variations.md) — SCAMPER variation engine; reference for V9-FUTURE-03 expansion methodology.
- [`skills/movie-experts/compliance_gate/references/cn-content-rules.md`](../../skills/movie-experts/compliance_gate/references/cn-content-rules.md) — CN content compliance; formulas respect §题材禁忌 + 8-category red lines (虐心 = emotional weight, not graphic content).
- [`skills/kais-movie-pipeline/references/v86-pipeline-mapping.md`](../../skills/kais-movie-pipeline/references/v86-pipeline-mapping.md) — V8.6 13-step pipeline mapping; Step 0 wiring context.

---

*Plugin authored: 2026-06-26 — v9.0 Phase 39 Plan 39-02 (FORM-03 seed formulas).*
*Bilingual convention per CLAUDE.md: EN headings + structural keywords; 中文 paragraphs for body prose.*
