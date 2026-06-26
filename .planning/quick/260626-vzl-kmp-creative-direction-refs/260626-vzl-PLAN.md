---
quick_id: 260626-vzl
description: Encode Kai's Notion "创作方向" strategy doc into kais-movie-pipeline references + patch 2 expert SKILL.md bodies + update kais-movie-pipeline SKILL.md References table. Pure refs/docs work — NO Python/JS code changes.
type: quick
scope: refs_only_no_code
context_budget: "~30% — pure markdown authoring + 3 small SKILL.md body patches"
source_notion:
  page_id: 32811082-af8e-8009-b097-d19a5027b46f
  anchor_block: 38211082-af8e-800e-b464-c65441cf8e6e
  page_title: "心流♥ → aigc开发 → 创作方向"
---

<objective>
Encode Kai's Notion "创作方向" strategy doc (4 sections: 平台策略 / 剧集策略 / 启动方案 / 第一性原理分析) into the canonical ref layer under `skills/kais-movie-pipeline/references/`, then wire those refs into 2 expert SKILL.md bodies + the orchestration skill's References table.

Purpose: Give the kais-movie-pipeline + the movie-experts (compliance_gate, theory_critic) a single canonical source for Kai's v1 creative strategy (平台规格 / 跨平台红线 / 题材锚定). Today this knowledge lives only in Notion; this task makes it addressable from the agent at runtime so experts stop improvising.

Output:
- 3 NEW refs under `skills/kais-movie-pipeline/references/` (platform-specs.md, creative-redlines.md, genre-anchor-urban-fantasy.md)
- 3 SKILL.md BODY patches (compliance_gate, theory_critic, kais-movie-pipeline) — zero frontmatter changes
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@/data/workspace/hermes-agent/CLAUDE.md
@/data/workspace/hermes-agent/skills/kais-movie-pipeline/SKILL.md
@/data/workspace/hermes-agent/skills/kais-movie-pipeline/references/pipeline-dag.md
@/data/workspace/hermes-agent/skills/movie-experts/compliance_gate/SKILL.md
@/data/workspace/hermes-agent/skills/movie-experts/theory_critic/SKILL.md

<format_conventions>
Reference file format — match `references/pipeline-dag.md` exactly:
- H1 title with ` — ` separator: `# Platform Specs — V1 Hard Constraints`
- Top metadata block: `**Source:**` (Notion page_id + anchor block id), `**Copyright:**` (Fair Use — factual specs / strategy structure; brief verbatim quotations attributed), `**Last-verified:**` date
- `---` horizontal rule separating sections
- Tables for tabular data (the Notion 硬性规格 table is already table-shaped — reproduce columns verbatim)
- `## See Also` footer with cross-links to sibling refs
- Bilingual: EN headings + 中文 body (per CLAUDE.md "Skill File Conventions")

SKILL.md body patch format — match existing style:
- compliance_gate uses an explicit `## References` table (lines 38-46) with `| Ref | When to Read | Contents |` columns — APPEND new rows there
- theory_critic uses an explicit `## References` table (lines 42-54) with same column format — APPEND new rows there
- kais-movie-pipeline uses an explicit `## References` table (lines 46-51) with same column format — APPEND new rows there
- Do NOT add a separate `@see` block — these skills already have a canonical References table; extend it (single source of truth)

Forbidden:
- YAML frontmatter edits (FOUND-08 frozen; expert_id / related_skills / metrics untouched)
- Python / JS code changes
- New model names in SKILL.md body (use placeholders per `_shared/RAG-INVOCATION-PATTERN.md` if needed — but this task is refs-only so unlikely)
</format_conventions>

<interfaces>
No new code interfaces. This plan is refs + SKILL.md body patches only. All "interfaces" are markdown link targets that downstream experts reference by relative path.

Ref paths created (relative to repo root):
- skills/kais-movie-pipeline/references/platform-specs.md
- skills/kais-movie-pipeline/references/creative-redlines.md
- skills/kais-movie-pipeline/references/genre-anchor-urban-fantasy.md

SKILL.md files patched (body only):
- skills/movie-experts/compliance_gate/SKILL.md  (append 2 rows to ## References table)
- skills/movie-experts/theory_critic/SKILL.md     (append 2 rows to ## References table)
- skills/kais-movie-pipeline/SKILL.md             (append 3 rows to ## References table)
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Author 3 new kais-movie-pipeline refs from Notion "创作方向"</name>
  <files>
skills/kais-movie-pipeline/references/platform-specs.md
skills/kais-movie-pipeline/references/creative-redlines.md
skills/kais-movie-pipeline/references/genre-anchor-urban-fantasy.md
  </files>
  <action>
Create the 3 NEW ref files. Match the format of the existing `references/pipeline-dag.md` exactly (H1 title with `—` separator, top metadata block with `**Source:** Notion page 32811082-af8e-8009-b097-d19a5027b46f, anchor block 38211082-af8e-800e-b464-c65441cf8e6e` + `**Copyright:** Fair Use — factual strategy specs reproduced verbatim with attribution; no copyrighted creative content` + `**Last-verified:** 2026-06-26`, `---` separator, EN headings + 中文 body, `## See Also` footer cross-linking sibling refs).

**File 1: `platform-specs.md` — "Platform Specs — V1 Hard Constraints"**
- `## Summary` — 1-paragraph scope statement: this is the canonical hard-spec ref for v1 platform strategy; per-expert "when to consult" guidance lives at the bottom.
- `## 硬性规格对照表 (Hard-Spec Cross-Platform Matrix)` — TWO-column table reproducing the Notion 硬性规格 table verbatim. Column headers: `竖屏滑动 (抖音 / 快手 / B站 Story Mode)` | `横屏主动 (B站 / 优腾爱 短剧)`. Rows (use exact 中文 labels from Notion as row headers, with EN gloss in parentheses on first occurrence):
  - 用户契约 (user contract): 被动投喂,随时划走 | 主动点击,预付耐心
  - 注意力窗口 (attention window): 0-3 秒(生死线)| 5-10 秒(钩子线)+ 30 秒(信任死亡线)
  - 最优时长 (optimal duration): 15-60 秒 | 90 秒-5 分钟
  - 钩子位置 (hook placement): 第 1-3 秒 | 第 5-10 秒
  - 身份锚定 (identity anchor): 第 3-8 秒 | 第 5-15 秒
  - 首次情绪转折 (first emotional turn): 第 8-15 秒 | 第 30-60 秒
  - 情绪单元间隔 (emotion-unit gap): ≤ 8 秒 | ≤ 60-90 秒
  - 记忆闭环 (memory closure): 30 秒内微型闭环 | 60-90 秒单元闭环
  - 切入点要求 (entry-point rule): 任意秒切入必须自洽 | 前 30 秒允许轻度上下文依赖
  - 算法逻辑 (algorithm logic): 冷启动秒级审判,阶梯流量池 | 完播率+追播率+追番率
- `## 刚性约束 (Hard Constraints by Layer)` — 4-tier table reproducing the Notion 12-row table: layers are 生理 (Physiological) / 行为 (Behavioral) / 平台 (Platform) / 市场 (Market); each row = one constraint with its direct AI 短剧 requirement. Use a 3-column table: `层级` | `约束` | `AI 短剧 要求`. Cover all 12 rows from Notion.
- `## 使用指南 (Per-Expert Consultation Guide)` — short bullet list mapping which expert consults this ref when:
  - `hook_retention` — before designing 0-3s/5-10s hooks (verifies hook falls inside 注意力窗口)
  - `editor` — when pacing emotion-unit gaps (≤8s 竖屏 vs ≤60-90s 横屏)
  - `cinematographer` — when choosing shot duration per platform form
  - `screenplay` — when scripting entry-point (竖屏 arbitrary-second self-consistency vs 横屏 first-30s context)
- `## See Also` — cross-link `creative-redlines.md` + `genre-anchor-urban-fantasy.md` + the compliance_gate SKILL.md.

**File 2: `creative-redlines.md` — "Creative Redlines — 7 Cross-Platform Invariants"**
- `## Summary` — 1-paragraph scope statement: this is the canonical ref for 7 invariant creative red lines that apply across all platforms in the v1 strategy. 5 are per-episode (apply during single-episode compliance review); 2 are process red lines (apply during the A/B convergence loop).
- `## Per-Episode Red Lines (1-5)` — 5 sub-sections, one per red line. Each sub-section uses this template (match the operational-detail style of compliance_gate `references/cn-content-rules.md`):
  ```
  ### R{n}. {中文红线名} ({EN gloss})

  **操作化定义 (Operational definition):** {how to measure/detect in pixels, frames, or seconds}
  **检测提示 (Detection signal for compliance_gate):** {what signal to grep/parse from script / storyboard / EDL}
  **违反示例 (Violation example):** {concrete}
  **合规示例 (Compliant example):** {concrete}
  **关联专家 (Related expert):** {which expert triggers this red line}
  ```
  The 5 per-episode red lines (use exact 中文 labels from Notion):
  1. 情绪脱敏 (Emotion Desensitization) — 同类型情绪连续出现不得超过 2 次. Operationalize as "consecutive same-taxonomy emotion shots ≤ 2 in any 60s window". Detection: parse script_emotion_tags from screenplay; flag runs of ≥3 same-tag consecutive beats. Related: screenplay + editor.
  2. 信息分层 (Information Layering) — 每帧只承载一层主导信息. Operationalize as "single dominant info layer per frame; co-occurring layers count ≤ 1 primary + ≤1 secondary". Detection: scene-level visual audit (scene-images slot). Related: cinematographer + visual_executor.
  3. 零背景铺垫 (Zero Backstory Preamble) — 切入即冲突,禁止"从前有个…". Operationalize as "first 3s (竖屏) / first 10s (横屏) must contain active conflict, not exposition". Detection: parse first-beat of script-draft; flag exposition-only openings. Related: screenplay + hook_retention.
  4. 结尾未完成 (Unresolved Ending) — 最后 3 秒必须释放新钩子,禁止大团圆. Operationalize as "last 3s (竖屏) / last 10s (横屏) must introduce a new open question". Detection: parse final beat; flag closure-only endings. Related: screenplay + editor + hook_retention.
  5. 差异化识别 (Differentiation Marker) — 0.5 秒内存在一个可被识别的异常点. Operationalize as "≥1 recognizably anomalous visual or audio element within the first 0.5s of any cut transition". Detection: shot-boundary + visual saliency audit. Related: cinematographer + visual_executor.
- `## Process Red Lines (6-7) — Apply During A/B Convergence Loop` — 2 sub-sections, each prefixed with `### R{n}. {name} (PROCESS RED LINE — not per-episode)`. Make the "process, not per-episode" status visually distinct (e.g., italicized note under each heading):
  6. 控制变量 (Control Variable) — 一次实验只改一个结构参数. Operationalize as "A/B test variants must differ in exactly one structural parameter; diff log required at gate-submit time". Detection: parse convergence-loop variant diff. Related: kais-movie-pipeline + theory_critic.
  7. 统计显著 (Statistical Significance) — 样本量 N≥10 或置信区间 < ±5% 才做决策. Operationalize as "variant decision requires N≥10 samples OR 95% CI half-width < 5%". Detection: parse convergence-loop decision log. Related: kais-movie-pipeline.
- `## 与 compliance_gate 红线的关系 (Relationship to compliance_gate §1..§8)` — short clarifying paragraph: these 7 red lines are CREATIVE-strategy invariants (-engagement / pacing / structure); they are SEPARATE from compliance_gate's 8 LEGAL 红线 (政治敏感 / 暴力血腥 / etc). Both layers must pass before release; creative lines are pre-publish design constraints, legal lines are pre-distribution compliance gates.
- `## See Also` — cross-link `platform-specs.md` + `genre-anchor-urban-fantasy.md` + compliance_gate/SKILL.md.

**File 3: `genre-anchor-urban-fantasy.md` — "Genre Anchor — V1: 都市奇幻·轻喜剧 (Urban Fantasy / Light Comedy)"**
- `## Summary` — 1-paragraph scope statement: this is the canonical v1 题材锚定 ref. All v1 productions assume this genre unless explicitly overridden by the operator.
- `## 核心 DNA (Core DNA)` — 3 bullets verbatim from Notion: 超能力设定 (superpower setting) + 轻喜剧 (light comedy) + 主线悬念 (ongoing mystery). Add 1-sentence EN gloss per bullet.
- `## Per-Platform Content Form (8 rows)` — table reproducing the Notion 8-row table verbatim. Columns: `平台 (Platform)` | `内容形态 (Content Form)` | `规格/时长 (Specs)`. Rows: B站季番正剧 5-10min / 抖音超能力高光切片 / 小红书角色穿搭+场景美学 / 视频号完整剧+粉丝专属能力解析 / 红果·快手 1-2min 快节奏版 / 腾讯漫画·快看条漫改编 / 淘宝·小红书店铺周边 (3D 手办/数字藏品/联名美妆). Use the exact 中文 spec text from Notion per cell.
- `## 启动方案 3-Month Roadmap` — 3 sub-sections matching Notion's M1/M2/M3 structure. Reproduce bullets verbatim from Notion:
  - `### M1 验证 (Validation)` — verbatim bullets
  - `### M2 平台适配 (Platform Adaptation)` — verbatim bullets
  - `### M3 IP 延伸 (IP Extension)` — verbatim bullets
- `## Per-Platform 变现逻辑 (Monetization Logic)` — table reproducing the Notion monetization table verbatim. Columns: `平台 (Platform)` | `变现机制 (Monetization Mechanism)` | `关键系数/单价 (Key Coefficients)`. Reproduce concrete numbers verbatim where Notion gives them (红果仿真人系数 60 / 广告分账 CPM 30-50 元 / 单剧 50-200 万收入 etc).
- `## 题材禁忌 (Genre Taboos)` — derived list (NOT verbatim from Notion — derive from the 都市奇幻·轻喜剧 DNA). 5-7 bullets covering: no heavy drama (重口狗血), no tragic endings (悲剧收尾), no lore dumps (设定堆砌), no realistic violence (写实暴力), no genre drift to 玄幻修真 or 都市言情 without operator override. Each bullet explains WHY it violates the DNA in 1 sentence.
- `## Why This Genre for V1 (Rationale)` — 3 bullets explaining: (1) FLUX character consistency test case (superpower visual signature = strong character anchor test), (2) 3D asset IP extension path (手办 / 数字藏品 / 联名美妆 monetization downstream), (3) multi-platform reuse (one IP → 8 platform forms, lowering per-platform content cost). Match Notion's "第一性原理分析" framing where applicable.
- `## See Also` — cross-link `platform-specs.md` + `creative-redlines.md` + theory_critic/SKILL.md.

**CRITICAL — do NOT:**
- Translate the 中文 verbatim quotes from Notion tables into English. The 硬性规格 / 刚性约束 / 8-row platform / monetization tables MUST stay 中文 (Kai's source is 中文; CLAUDE.md says refs are 中文-primary with EN glosses for key terms only).
- Invent numbers. If a Notion cell value is unclear, write `<TBD — verify against Notion source>` rather than fabricating. (But the task brief already enumerates the verbatim values for the 硬性规格 table — use those exactly.)
- Add YAML frontmatter to ref files (refs are plain markdown per existing `pipeline-dag.md` precedent).
- Touch any SKILL.md in this task — that's Task 2.
  </action>
  <verify>
    <automated>
cd /data/workspace/hermes-agent
for f in skills/kais-movie-pipeline/references/platform-specs.md skills/kais-movie-pipeline/references/creative-redlines.md skills/kais-movie-pipeline/references/genre-anchor-urban-fantasy.md; do
  test -f "$f" || { echo "MISSING: $f"; exit 1; }
  # Must cite Notion source
  grep -q "32811082-af8e-8009-b097-d19a5027b46f" "$f" || { echo "NO NOTION CITATION in $f"; exit 1; }
  # Must have See Also footer
  grep -q "## See Also" "$f" || { echo "NO See Also in $f"; exit 1; }
  # Must have ≥30 non-empty content lines (real content, not stub)
  lines=$(grep -cv '^[[:space:]]*$' "$f")
  [ "$lines" -ge 30 ] || { echo "TOO SHORT ($lines lines): $f"; exit 1; }
done

# platform-specs.md: must contain the 硬性规格 row labels
grep -q "用户契约" skills/kais-movie-pipeline/references/platform-specs.md
grep -q "注意力窗口" skills/kais-movie-pipeline/references/platform-specs.md
grep -q "情绪单元间隔" skills/kais-movie-pipeline/references/platform-specs.md
grep -q "使用指南" skills/kais-movie-pipeline/references/platform-specs.md

# creative-redlines.md: must contain all 7 red lines + process red line flag
grep -q "情绪脱敏" skills/kais-movie-pipeline/references/creative-redlines.md
grep -q "信息分层" skills/kais-movie-pipeline/references/creative-redlines.md
grep -q "零背景铺垫" skills/kais-movie-pipeline/references/creative-redlines.md
grep -q "结尾未完成" skills/kais-movie-pipeline/references/creative-redlines.md
grep -q "差异化识别" skills/kais-movie-pipeline/references/creative-redlines.md
grep -q "控制变量" skills/kais-movie-pipeline/references/creative-redlines.md
grep -q "统计显著" skills/kais-movie-pipeline/references/creative-redlines.md
grep -q "PROCESS RED LINE" skills/kais-movie-pipeline/references/creative-redlines.md
grep -q "compliance_gate" skills/kais-movie-pipeline/references/creative-redlines.md

# genre-anchor: must contain all 3-month phases + per-platform rows
grep -q "都市奇幻" skills/kais-movie-pipeline/references/genre-anchor-urban-fantasy.md
grep -q "M1 验证" skills/kais-movie-pipeline/references/genre-anchor-urban-fantasy.md
grep -q "M2 平台适配" skills/kais-movie-pipeline/references/genre-anchor-urban-fantasy.md
grep -q "M3 IP 延伸" skills/kais-movie-pipeline/references/genre-anchor-urban-fantasy.md
grep -q "红果" skills/kais-movie-pipeline/references/genre-anchor-urban-fantasy.md
grep -q "题材禁忌" skills/kais-movie-pipeline/references/genre-anchor-urban-fantasy.md
echo "ALL REFS OK"
    </automated>
  </verify>
  <done>
3 new ref files exist under skills/kais-movie-pipeline/references/, each:
- ≥30 non-empty lines of substantive content
- Cites Notion page 32811082-af8e-8009-b097-d19a5027b46f in source block
- Has `## See Also` footer cross-linking sibling refs
- Contains all expected sections (per-file grep checks above)
- Matches format conventions of existing `references/pipeline-dag.md` (H1 + metadata block + `---` + body)
- Preserves 中文 verbatim from Notion tables; no fabrication of numbers
  </done>
</task>

<task type="auto">
  <name>Task 2: Patch 3 SKILL.md body References tables (zero frontmatter changes)</name>
  <files>
skills/movie-experts/compliance_gate/SKILL.md
skills/movie-experts/theory_critic/SKILL.md
skills/kais-movie-pipeline/SKILL.md
  </files>
  <action>
Append new rows to the existing `## References` table in each of the 3 SKILL.md files. Each skill already has a canonical References table — extend it (single source of truth) rather than adding a separate @see block. Zero YAML frontmatter changes (FOUND-08 frozen).

**File 1: `skills/movie-experts/compliance_gate/SKILL.md`**
Locate the existing `## References` table (currently lines 38-46, columns `| Ref | When to Read | Contents |`). APPEND 2 new rows to the table (after the last existing row `_shared/platform-comparison.md`):
- Row A: ``| [`../../kais-movie-pipeline/references/creative-redlines.md`](../../kais-movie-pipeline/references/creative-redlines.md) | Before any creative-structure review (engagement / pacing / ending) | 7 cross-platform creative red lines (情绪脱敏 / 信息分层 / 零背景铺垫 / 结尾未完成 / 差异化识别 + 2 process red lines) — SEPARATE from this expert's §1..§8 legal 红线; both layers must pass |``
- Row B: ``| [`../../kais-movie-pipeline/references/platform-specs.md`](../../kais-movie-pipeline/references/platform-specs.md) | Before per-platform 分发 cut advice | V1 hard-spec matrix: 竖屏滑动 vs 横屏主动 (10-row 硬性规格) + 12-row 刚性约束 by 生理/行为/平台/市场 layer |``

Verify relative path correctness: from `skills/movie-experts/compliance_gate/SKILL.md` to `skills/kais-movie-pipeline/references/*.md` is `../../kais-movie-pipeline/references/*.md` (up from compliance_gate/ → up from movie-experts/ → into kais-movie-pipeline/references/).

**File 2: `skills/movie-experts/theory_critic/SKILL.md`**
Locate the existing `## References` table (currently lines 42-54, same column format). APPEND 2 new rows (after the last existing row `_shared/project-corpus/README.md`):
- Row A: ``| [`../../kais-movie-pipeline/references/genre-anchor-urban-fantasy.md`](../../kais-movie-pipeline/references/genre-anchor-urban-fantasy.md) | When evaluating v1 productions against the canonical 都市奇幻·轻喜剧 DNA | V1 题材锚定:核心 DNA (超能力 + 轻喜剧 + 主线悬念) + 8-row per-platform content form + 3-month 启动方案 + 题材禁忌 |``
- Row B: ``| [`../../kais-movie-pipeline/references/creative-redlines.md`](../../kais-movie-pipeline/references/creative-redlines.md) | When flagging creative-strategy violations in critique | 7 cross-platform invariants (5 per-episode + 2 process) — theory_critic flags these in advisory output, distinct from compliance_gate's legal hard-gate |``

**File 3: `skills/kais-movie-pipeline/SKILL.md`**
Locate the existing `## References` table (currently lines 46-51, columns `| Ref | When to Read | Contents |`). The current intro text says "This skill ships with 4 reference docs under `references/`" — UPDATE that count to 7. APPEND 3 new rows after the `references/expert-mapping.md` row:
- Row A: ``| `references/platform-specs.md` | Before per-platform 分发 / duration / hook placement decisions | V1 hard-spec matrix (竖屏滑动 vs 横屏主动, 10-row 硬性规格) + 12-row 刚性约束 by layer + per-expert consultation guide |``
- Row B: ``| `references/creative-redlines.md` | Before any single-episode compliance review or A/B convergence loop | 7 cross-platform creative invariants (5 per-episode: 情绪脱敏/信息分层/零背景铺垫/结尾未完成/差异化识别 + 2 process: 控制变量/统计显著) |``
- Row C: ``| `references/genre-anchor-urban-fantasy.md` | Before any v1 production (default genre unless operator overrides) | V1 题材锚定 都市奇幻·轻喜剧:核心 DNA + per-platform content form + 3-month 启动方案 + 变现逻辑 + 题材禁忌 |``

**CRITICAL — do NOT:**
- Modify YAML frontmatter (any of the 3 files). FOUND-08 rule: expert_id / related_skills / metrics / aliases / version all frozen.
- Move, rename, or delete existing rows in any References table — APPEND ONLY.
- Touch any other section of the SKILL.md body (the `## V8.6 Pipeline Sync` / `## Role & Philosophy` / `## Core Capabilities` / etc. sections stay byte-identical).
- Use Edit/Write to rewrite the whole file — use Edit with surgical scope (just the References table section).
- Invent paths. Verify each relative path: `../../kais-movie-pipeline/references/...` from a movie-expert SKILL.md, and `references/...` from the kais-movie-pipeline SKILL.md.
  </action>
  <verify>
    <automated>
cd /data/workspace/hermes-agent

# 1. Frontmatter byte-identical (compare frontmatter block only, lines between --- markers)
for f in skills/movie-experts/compliance_gate/SKILL.md skills/movie-experts/theory_critic/SKILL.md skills/kais-movie-pipeline/SKILL.md; do
  # Extract frontmatter (between first two --- lines) and verify it still parses + key fields intact
  python3 -c "
import sys, re
content = open('$f', encoding='utf-8').read()
m = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
if not m:
    print('FRONTmatter PARSE FAIL: $f'); sys.exit(1)
fm = m.group(1)
# expert_id must still be present and unchanged
for required in ['expert_id', 'name:']:
    if required not in fm:
        print(f'MISSING {required} in frontmatter: $f'); sys.exit(1)
"
done

# 2. compliance_gate: 2 new refs linked, both with correct relative path
grep -c "kais-movie-pipeline/references/creative-redlines.md" skills/movie-experts/compliance_gate/SKILL.md | grep -qx "1" || true  # at least 1
grep -c "kais-movie-pipeline/references/platform-specs.md" skills/movie-experts/compliance_gate/SKILL.md
grep -q "kais-movie-pipeline/references/creative-redlines.md" skills/movie-experts/compliance_gate/SKILL.md
grep -q "kais-movie-pipeline/references/platform-specs.md" skills/movie-experts/compliance_gate/SKILL.md

# 3. theory_critic: 2 new refs linked
grep -q "kais-movie-pipeline/references/genre-anchor-urban-fantasy.md" skills/movie-experts/theory_critic/SKILL.md
grep -q "kais-movie-pipeline/references/creative-redlines.md" skills/movie-experts/theory_critic/SKILL.md

# 4. kais-movie-pipeline: 3 new rows + count updated from 4 → 7
grep -q "references/platform-specs.md" skills/kais-movie-pipeline/SKILL.md
grep -q "references/creative-redlines.md" skills/kais-movie-pipeline/SKILL.md
grep -q "references/genre-anchor-urban-fantasy.md" skills/kais-movie-pipeline/SKILL.md
# Count should say 7 now (not 4)
grep -E "ships with [0-9]+ reference docs" skills/kais-movie-pipeline/SKILL.md | grep -q "7 reference docs"

# 5. Relative path correctness from movie-experts/* — the link target must actually exist
for ref in creative-redlines.md platform-specs.md genre-anchor-urban-fantasy.md; do
  test -f "skills/kais-movie-pipeline/references/$ref" || { echo "REF MISSING: $ref"; exit 1; }
done

# 6. No accidental edits outside References section — count of `## V8.6 Pipeline Sync` headings still 1 per file
[ "$(grep -c '^## V8.6 Pipeline Sync' skills/movie-experts/compliance_gate/SKILL.md)" = "1" ]
[ "$(grep -c '^## V8.6 Pipeline Sync' skills/movie-experts/theory_critic/SKILL.md)" = "1" ]

echo "ALL SKILL.md PATCHES OK"
    </automated>
  </verify>
  <done>
3 SKILL.md files patched (body-only, zero frontmatter changes):
- compliance_gate/SKILL.md `## References` table has 2 new rows linking creative-redlines.md + platform-specs.md with correct `../../` relative paths
- theory_critic/SKILL.md `## References` table has 2 new rows linking genre-anchor-urban-fantasy.md + creative-redlines.md with correct `../../` relative paths
- kais-movie-pipeline/SKILL.md `## References` table intro updated from "4 reference docs" → "7 reference docs" and has 3 new rows for all 3 new refs
- All link target files exist (verified in Task 1)
- All other sections of each SKILL.md byte-identical (Edit used surgically on References table only)
  </done>
</task>

</tasks>

<verification>
**Phase-level verification (after both tasks):**

1. The 3 new refs are syntactically valid markdown (no broken tables) and cite the Notion source.
2. The 3 SKILL.md files have their References table extended (rows appended, no other section touched).
3. Frontmatter on all 3 SKILL.md files is byte-identical to pre-task state (FOUND-08 preserved).
4. All cross-reference link targets exist on disk (no dangling relative paths).
5. NO Python / JS / YAML-config files modified (only .md files touched).

Run all `<automated>` blocks above end-to-end:
```bash
cd /data/workspace/hermes-agent
# (Paste the two <automated> blocks here — they are designed to be runnable in sequence.)
```

If any check fails, fix and re-run before declaring the task complete.
</verification>

<success_criteria>
- 3 new ref files created with substantive content (≥30 non-empty lines each) matching the format of `references/pipeline-dag.md`
- 3 SKILL.md files patched (body only, zero frontmatter changes) with new rows in their existing `## References` table
- Notion source cited in every new ref (page_id + anchor_block_id)
- 中文 verbatim values from Notion preserved (no translation, no fabrication)
- Zero Python/JS code changes; zero YAML frontmatter changes; zero changes to non-References sections of any SKILL.md
</success_criteria>

<output>
Create `.planning/quick/260626-vzl-kmp-creative-direction-refs/260626-vzl-SUMMARY.md` when done, documenting:
- 3 refs created (paths + line counts)
- 3 SKILL.md files patched (sections touched)
- Verification commands run + pass status
- Commit SHAs (one atomic commit per task, docs-only)
</output>
