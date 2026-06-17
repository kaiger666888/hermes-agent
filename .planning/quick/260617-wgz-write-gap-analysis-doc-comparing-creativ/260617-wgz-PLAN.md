---
phase: quick
plan: 260617-wgz
type: execute
wave: 1
depends_on: []
files_modified:
  - .planning/research/methodology-gap-analysis-2026-06-17.md
autonomous: true
requirements: [QUICK-DOC]
user_setup: []
must_haves:
  truths:
    - ".planning/research/methodology-gap-analysis-2026-06-17.md exists with all 8 required sections"
    - "6-row §7.2 blueprint matrix present with verified coverage symbols (✅/⚠️/❌)"
    - "3 top-ROI gaps (Snowflake / E-Konte / SCAMPER) each have report-location + vacuum-reason + integration-point"
    - "Independent-methodology inventory lists all 6 (Tan / McMahon / Smith / Bourdieu / Auteur / 爆款公式)"
    - "Non-action decision section explicitly declares no new phase is launched"
  artifacts:
    - path: .planning/research/methodology-gap-analysis-2026-06-17.md
      provides: "Methodology gap analysis between source research report's 6-stage AI video pipeline blueprint and current skills/movie-experts/ coverage"
      min_lines: 280
  key_links: []
---

<objective>
Produce a single decision-basis document at `.planning/research/methodology-gap-analysis-2026-06-17.md` that compares the source research report's §7.2 6-stage AI video creation pipeline blueprint against the actual methodology coverage in `skills/movie-experts/`.

Purpose: Give the developer (Kai) a verified decision-basis document so he can decide the next path (write spec / enter `/gsd:explore` / refactor `creative_source` directly) based on factual coverage state rather than the report's "McKee-as-baseline" framing. This document explicitly DOES NOT launch a new phase.

Output: One markdown file with 8 required sections, written in Chinese (matching `.planning/research/` existing style) with English methodology names preserved.
</objective>

<execution_context>
@/home/kai/.claude/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/STATE.md
@./CLAUDE.md
@.planning/quick/260617-wgz-write-gap-analysis-doc-comparing-creativ/source-research-report.md

# Verified current-state evidence (planner已读 SKILL.md 验证,executor可直接引用,无需重新读取)

The following reconciliation has been VERIFIED by reading every cited SKILL.md during planning (2026-06-17). The executor should TRUST these cells — they are not the orchestrator's pre-computation, they are confirmed against actual files. If the executor wants to spot-check, the source SKILL.md paths are listed; but full re-reading is wasteful.

## Verified: 6-Stage §7.2 Coverage Matrix

| Report §7.2 Stage | Report's named methodology | Current skill + actual methodology used | Coverage |
|---|---|---|---|
| **1. 创意种子** | Story Spine + CPS | `creative_source` uses **Bourdieu 6-strata (L1-L6) + Foucault + Lefebvre** — NOT Story Spine / CPS | ❌ 路径不同(更强,但非报告设想路径) |
| **2. 故事大纲** | Snowflake + Snyder 15-beat + Vogler 12阶段 | `screenplay` uses **Snyder 15-beat + McKee scene-design** — NO Snowflake, NO Vogler | ⚠️ 1/3 covered (Snyder only) |
| **3. 角色深度** | Truby 四角对立 + Lisa Cron + Vogler 8原型 | `character_designer` uses **4D-Anchor + 3-layer STYLE_PREFIX + CLIP-I/DINO-I stress test** — NOT Truby / Cron / Vogler | ❌ 路径完全不同(更偏视觉身份,缺心理结构) |
| **4. 分镜设计** | E-Konte + Bruce Block | `cinematographer` uses **Mascelli 8-level shot scale + Arijon composition + 180°/30° axis + Runway/Kling/Veo/Sora prompt tokens** — NO E-Konte, NO Bruce Block. `storyboard_designer` is `status: deprecated` (Phase 17 v3.0, 2026-06-17, folded into cinematographer.composition_lock) | ❌ E-Konte 真空 |
| **5. 创意变换** | SCAMPER + 六顶思考帽 + 横向思维 | `style_genome.style_blend_protocol` is manual 0.7/0.3 dominant-recessive protocol (not variant engine); `script_auditor` is 5-dim scoring (Snyder + McKee + Plutchik + 疲劳曲线), NOT SCAMPER | ❌ 真空 |
| **6. 迭代优化** | 设计思维五阶段 / 双钻 + Story Grid | No explicit meta-process. `script_auditor ↔ screenplay` iteration loop exists but is informal | ❌ 真空 |

## Verified: Independent Methodologies (current skills use but report doesn't cover)

- **Tan Interest Structure (1996)** — `screenplay/references/emotion-curve-academic.md` — interest = concern × uncertainty × anticipation ≥ 0.6
- **McMahon 6 Emotional Arcs (2016)** — same ref — 85% coverage of story shapes
- **Smith Engaging Characters (1995)** — referenced indirectly via emotion-curve ref (character engagement dimension)
- **Bourdieu 场域理论** — `creative_source/references/strata-guide.md` — 6 strata + field/habitus/capital
- **Auteur Theory (Sarris 1962/1968 + Truffaut + Bordwell)** — `style_genome/references/auteur-theory.md` — 3-criteria rubric + Style Coherence Doctrine
- **短剧爆款公式** — `hook_retention/SKILL.md` — 5 platform × audience branches (抖音-男频 / 抖音-女频 / 快手-草根 / 小程序剧-长集数 / 通用 fallback)
- **Plutchik 八维情绪** — `script_auditor/references/emotion-arc-audit.md` — used in Dimension 2 audit
- **疲劳曲线物理模型** — `script_auditor/references/completion-rate-forecast.md` — attention(t) = base × e^(-decay×t) × conflict_gain(t)

## Verified: 3 Top-ROI Gaps

### Gap 1: Snowflake Method (雪花法)
- **Report location:** §2.1, AI化适合度 ⭐⭐⭐⭐⭐
- **Current vacuum reason:** `creative_source` outputs `StoryKernel` (one-line structural_formula + strata_layers[]). `screenplay` jumps directly to Snyder 15-beat sheet. There is NO intermediate "kernel → paragraph → character summary → one-page outline → 4-page outline → scene list" recursive expansion. The pipeline collapses kernel → beat_sheet in one hop.
- **Integration difficulty estimate:** LOW. Snowflake is a pure process method (prompt chain), requires no new skill, no new schema. Can be added as a sub-step inside `screenplay` OR as an independent `snowflake_expander` skill between `creative_source` and `screenplay`.
- **Integration point:** `screenplay/references/` new file `snowflake-expansion.md` OR new skill `snowflake_expander/` between `creative_source` and `screenplay` in the DAG.

### Gap 2: E-Konte (絵コンテ)
- **Report location:** §4.1, AI化适合度 ⭐⭐⭐⭐⭐ — report calls this "AI 视频管线的直接蓝图"
- **Current vacuum reason:** `cinematographer` uses Western axis tradition (180° rule, 30° rule, Mascelli shot scale). `storyboard_designer` (which could have carried E-Konte) is **`status: deprecated`** as of Phase 17 v3.0 (2026-06-17), folded into `cinematographer.composition_lock` sub-task. The deprecated `storyboard_designer` did NOT use E-Konte either (it used shot-decomposition rules + camera params + 4D anchoring). So E-Konte is completely absent.
- **Integration difficulty estimate:** MEDIUM. E-Konte is a format/spec (time/frame per shot, layout/composition/angle/movement/action/dialogue/sfx annotations). Needs new ref file documenting the E-Konte format + decision: either extend `cinematographer.composition_lock` to emit E-Konte-style intermediate format, OR introduce Kon Satoshi-style "publishable storyboard" as a separate artifact type.
- **Integration point:** `cinematographer/references/e-konte-format.md` (new file) + extend `composition_lock` sub-task output OR add `e_konte_storyboard.json` as additional output artifact.

### Gap 3: SCAMPER
- **Report location:** §6.1, AI化适合度 ⭐⭐⭐⭐⭐ — "每个动词都可以直接作为 AI prompt 的变换维度"
- **Current vacuum reason:** `style_genome.style_blend_protocol` is a parametric 0.7/0.3 dominant-recessive weight blend (NOT a variant generator — it produces ONE blended result, not 7 variants). `script_auditor` is a scorer (evaluates ONE script), not a variant engine. So no current skill generates "what if we Substitute/Combine/Adapt/Modify/Put-to-other-use/Eliminate/Reverse" story variants.
- **Integration difficulty estimate:** LOW-MEDIUM. SCAMPER is 7 prompt templates. Can be added as `screenplay` self-iteration tool OR as a new sub-step in `creative_source` (generate 7 variants of a kernel before committing). Needs decision: does it run pre-screenplay (kernel variants) or post-screenplay (script variants)?
- **Integration point:** `creative_source/references/scamper-variants.md` (new file, kernel-stage variants) OR `screenplay/references/scamper-iteration.md` (script-stage variants) OR new skill `variant_generator/`.

## Verified: Secondary-priority gaps (for the simple table)

- **Vogler 12阶段 + 8原型** — report §1.4 ⭐⭐⭐⭐⭐. Current: nowhere. Vacuum.
- **Truby 22步 + 四角对立** — report §1.3 ⭐⭐⭐⭐. Current: nowhere. Vacuum.
- **设计思维五阶段** — report §5.1 ⭐⭐⭐⭐⭐. Current: no explicit meta-process. Vacuum.
- **Story Grid** — report §2.2 ⭐⭐⭐⭐. Current: `script_auditor` covers adjacent territory (5-dim scoring) but uses Snyder/McKee/Plutchik/疲劳曲线, NOT Coyne's Story Grid 5-commandments. Partial vacuum.
- **起承转合 (Kishōtenketsu)** — report §3.3 ⭐⭐⭐⭐. Current: nowhere. This is a CN/JP traditional structure — notable absence for 治愈向 / 氛围型 short videos. Vacuum with CN cultural relevance.

## Critical fact correction (MUST appear in §4 of the document)

The source report repeatedly frames McKee as the methodology baseline ("与麦基方法的异同" appears 9 times). But current `skills/movie-experts/screenplay/` actually uses **McKee + Snyder jointly**:
- McKee (`references/mckee-scene-design.md`): value-shift rate ≥ 1/scene, beat decomposition 3-5/90s, turning point vs plot point (~25%/~75% runtime)
- Snyder (`references/save-the-cat-beat-sheet.md`): 15-beat structure with % positions adapted to 短剧 60-180s

Plus independent additions (Tan / McMahon / Smith / Plutchik / Bourdieu / Auteur). So any future planning that assumes "we still need to introduce McKee from scratch" is wrong — McKee is already in. The actual gap is the methodologies the report LISTS that are NOT yet in (Snowflake / E-Konte / SCAMPER / Vogler / Truby / etc.).
</context>

<tasks>

<task type="auto">
  <name>Task 1: Write methodology-gap-analysis-2026-06-17.md with all 8 required sections</name>
  <files>.planning/research/methodology-gap-analysis-2026-06-17.md</files>
  <action>
Create the file with the following 8 sections IN ORDER. Language: Chinese prose, English methodology names preserved (matches `.planning/research/ARCHITECTURE.md` / `FEATURES.md` style).

**Section 1 — Executive Summary(一句话结论)**
One paragraph (3-5 sentences). State: (a) current movie-experts 实际用了什么(Snyder + McKee + Tan + McMahon + Bourdieu + Auteur + 短剧爆款公式 + Plutchik + 疲劳曲线);(b) 报告 §7.2 6 阶段中实际覆盖 1/6(Snyder-only partial),路径不同 2/6,完全真空 3/6;(c) 报告的"麦基基准"框架已过时 — 当前是 McKee + Snyder 联用;(d) 最高 ROI 三个缺口是 Snowflake / E-Konte / SCAMPER(都是 ⭐⭐⭐⭐⭐);(e) 本文档只是决策依据,不启动新 phase。

**Section 2 — 当前实际覆盖(实测 skills/movie-experts/ 各 skill 的方法论清单)**
按 skill 分小节列出。每个 skill 给 2-4 行:用的方法论名 + 出处 ref 文件。Cover at minimum:
- `screenplay` — Snyder 15-beat (`save-the-cat-beat-sheet.md`) + McKee scene-design (`mckee-scene-design.md`) + Tan Interest Structure + McMahon 6 arcs (`emotion-curve-academic.md`) + CN 短剧结构 (`cn-shortdrama-structure.md`) + 对白工艺 (`dialogue-craft.md`) + 维基·金/芦苇/奥班农 (`_shared/project-corpus/screenwriting-chinese-and-supplementary.md`)
- `creative_source` — Bourdieu 6 strata + Foucault + Lefebvre (`strata-guide.md`) + multi-strata resonance + unspeakability 10-point protocol
- `character_designer` — 4D-Anchor system + 3-layer STYLE_PREFIX + CLIP-I/DINO-I stress test (NO Truby/Vogler/Cron — visual identity focus)
- `cinematographer` — Mascelli 8-level shot scale + Arijon composition + 180°/30° axis rules + 12 camera moves + Runway/Kling/Veo/Sora prompt-token mapping (NO E-Konte, NO Bruce Block)
- `style_genome` — Sarris 3-criteria Auteur Theory + Truffaut + Bordwell (`auteur-theory.md`) + 35 director 5D DNA archive + 12-genre taxonomy + cross-cultural hybrid encoding (0.65/0.35)
- `hook_retention` — 5-type hook taxonomy + 3-tier 卡点 strength + per-platform 5-branch 爆款公式 (抖音-男频/女频 / 快手-草根 / 小程序剧-长集数 / 通用 fallback)
- `script_auditor` — Snyder + McKee (Dim 1) + Plutchik 8-dim emotion (Dim 2) + 3秒Hook 10-point (Dim 3) + 角色网络 (Dim 4) + 疲劳曲线物理模型 (Dim 5) — 5-dim total 100 score
- `storyboard_designer` — **DEPRECATED** (Phase 17 v3.0, 2026-06-17), folded into `cinematographer.composition_lock`; original used shot-decomposition + camera params + 4D anchoring

**Section 3 — 报告蓝图 §7.2 六阶段对照矩阵**
Render as a 6-row markdown table with columns: 阶段 / 报告点名方法论 / 当前实现 / 覆盖度 / 缺口描述. Use the verified matrix from `<context>` above verbatim (already corrected). Add a short paragraph below the table summarizing: 1/6 partial (Snyder-only), 2/6 path-divergent (creative_source Bourdieu 路径 / character_designer 视觉身份路径), 3/6 vacuum (E-Konte / SCAMPER / meta-process).

**Section 4 — 关键事实校正**
Explain the McKee-baseline framing error. Quote: 报告 §7.2 + 9 处 "与麦基方法的异同" assumes McKee is the baseline. Reality: current `screenplay/references/mckee-scene-design.md` + `save-the-cat-beat-sheet.md` are jointly used. So future planning must NOT assume "introduce McKee from scratch" — that work is done. The real gaps are the OTHER listed methodologies (Snowflake / E-Konte / SCAMPER / Vogler / Truby / Story Grid / etc.).

**Section 5 — 高 ROI 缺口排序(3 个最高优先级)**
One subsection per gap (Snowflake / E-Konte / SCAMPER), each with 4 fields: (a) 报告位置(section ref + AI化适合度星级); (b) 当前为何真空(verified reason from `<context>`); (c) 接入难度估算(LOW / MEDIUM / LOW-MEDIUM with rationale); (d) 对应的现有 skill 接入点(specific ref file path + sub-task name or new skill name suggestion).

**Section 6 — 次优先级缺口(简表)**
One markdown table: 方法论 / 报告位置 / AI化适合度 / 当前状态(Vacuum / Partial) / 一句话说明. Include: Vogler 12阶段+8原型 / Truby 22步+四角对立 / 设计思维五阶段 / Story Grid / 起承转合(Kishōtenketsu,治愈向盲区) / 六顶思考帽 / 横向思维 / CPS / Story Spine / 模块化叙事.

**Section 7 — 独创方法论清单(当前 skills 引入但报告未覆盖)**
Bulleted list of 8 entries with citation to ref file path: Tan Interest Structure (1996) / McMahon 6 emotional arcs (2016) / Smith Engaging Characters (1995) / Bourdieu 场域理论(L1-L6 strata)/ Sarris-Truffaut-Bordwell Auteur Theory / 短剧爆款公式 5-branch / Plutchik 八维情绪 / 疲劳曲线物理模型(attention decay). For each, one sentence on what dimension it adds that the report doesn't cover.

**Section 8 — 不动作决策(non-action decision)**
Explicit declaration (3-5 sentences): 本文档不启动新 phase,不创建 PLAN.md,不修改任何 skills/ 代码。只是决策依据。后续路径(由 Kai 决定):选项 A 写 spec 后走 `/gsd:plan-phase`; 选项 B 进入 `/gsd:explore` 做更深的 Snowflake/E-Konte/SCAMPER 选型调研; 选项 C 直接重构 `creative_source` 把 Snowflake 折叠进 StoryKernel→Screenplay 中间步骤。引用 `.planning/research/v2-pipeline-design/` 已有的 pipeline design 文档作为后续路径的入口。

Document header: include title `# 方法论 Gap Analysis:报告 §7.2 蓝图 vs 当前 movie-experts 实际覆盖`, date `2026-06-17`, source-report path `.planning/quick/260617-wgz-write-gap-analysis-doc-comparing-creativ/source-research-report.md`, and a "本文档定位:决策依据,非 phase 启动" banner at the top.
  </action>
  <verify>
    <automated>test -f .planning/research/methodology-gap-analysis-2026-06-17.md && wc -l .planning/research/methodology-gap-analysis-2026-06-17.md | awk '$1 >= 280 {exit 0} {exit 1}'</automated>
  </verify>
  <done>
File exists at `.planning/research/methodology-gap-analysis-2026-06-17.md`, ≥ 280 lines, contains all 8 sections (Executive Summary / 当前覆盖 / 6-阶段矩阵 / McKee 校正 / 3 高 ROI 缺口 / 次优先级简表 / 独创方法论 / 不动作决策). The 6-row matrix uses verified coverage symbols. The 3 top-ROI gaps each have report-location + vacuum-reason + integration-difficulty + integration-point. Section 8 explicitly declares no new phase is launched.
  </done>
</task>

</tasks>

<verification>
- File exists at the exact path: `.planning/research/methodology-gap-analysis-2026-06-17.md`
- Line count ≥ 280 (the 8 sections + tables cannot fit in fewer)
- `grep -c '^## ' .planning/research/methodology-gap-analysis-2026-06-17.md` returns ≥ 8 (the 8 required H2 sections)
- `grep -c '✅\|⚠️\|❌' .planning/research/methodology-gap-analysis-2026-06-17.md` returns ≥ 6 (the matrix symbols)
- `grep -E 'Snowflake|E-Konte|SCAMPER' .planning/research/methodology-gap-analysis-2026-06-17.md | wc -l` returns ≥ 9 (3 gaps × 3 mentions minimum)
- Section 8 contains the phrase "不启动新 phase" or equivalent explicit non-action declaration
</verification>

<success_criteria>
- One markdown file produced at `.planning/research/methodology-gap-analysis-2026-06-17.md`
- All 8 sections present and complete with verified content
- 6-stage matrix reflects ACTUAL current state (not the orchestrator's pre-computation — verified against SKILL.md files)
- 3 top-ROI gaps actionable: each names a specific ref file path as integration point
- McKee-baseline-framing error explicitly corrected
- No code changes, no new phase, no PLAN.md created — pure decision-basis document
</success_criteria>

<output>
Return: ## PLANNING COMPLETE with the plan path `.planning/quick/260617-wgz-write-gap-analysis-doc-comparing-creativ/260617-wgz-PLAN.md`. Do NOT create a SUMMARY.md (this is a quick task, not a phase plan).
</output>
