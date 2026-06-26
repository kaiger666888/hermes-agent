---
phase: 38-slice-platform-master
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - skills/kais-movie-pipeline/references/platform-master-slicing.md
  - skills/kais-movie-pipeline/SKILL.md
  - skills/kais-movie-pipeline/references/asset-bus-schema.md
  - skills/kais-movie-pipeline/references/pipeline-dag.md
autonomous: true
milestone: v9.0
requirements: [SLICE-01, SLICE-02, SLICE-03, SLICE-04]
granularity: standard
model_profile: quality

must_haves:
  truths:
    - "7 platform variants are emittable from 1 master.mp4 (抖音竖屏 9:16 / 抖音横屏 16:9 / 快手竖屏 / B 站横屏 5-10min / 小红书竖屏 3min / 视频号横屏 / 红果或快手极短 1-2min)"
    - "Each variant's aspect_ratio is sourced from platform-specs.md's 7-row matrix (not invented)"
    - "Each variant auto-repositions the opening 3s hook, adjusts mid-segment 卡点 density, and adds a closing 3s new hook — all per platform-specs.md rigid constraints, not manual operator intervention"
    - "Every variant's metadata lands in pipeline_state.episode_id.variants[] with the 5 fields (platform / aspect_ratio / length / hook_timestamps / cut_points) queryable by Phase 42 DATA"
    - "A new ref documents the 7-variant algorithm + 4 key decision points"
    - "SKILL.md body has a new Step 14 section; SKILL.md frontmatter is byte-identical to pre-v9.0 (FOUND-08 preserved)"
  artifacts:
    - path: "skills/kais-movie-pipeline/references/platform-master-slicing.md"
      provides: "7-variant slicing algorithm + 4 key decision points + variants[] schema doc"
      min_lines: 250
    - path: "skills/kais-movie-pipeline/SKILL.md"
      provides: "Step 14 section (additive, zero frontmatter change)"
      contains: "Step 14"
    - path: "skills/kais-movie-pipeline/references/asset-bus-schema.md"
      provides: "variants[] schema extension documented as additive field on episode_id struct"
      contains: "variants"
    - path: "skills/kais-movie-pipeline/references/pipeline-dag.md"
      provides: "Step 14 additive annotation (V8.6 13-step numbering preserved)"
      contains: "Step 14"
  key_links:
    - from: "skills/kais-movie-pipeline/SKILL.md (Step 14 section)"
      to: "references/platform-master-slicing.md"
      via: "markdown relative link in Step 14 section body"
      pattern: "platform-master-slicing\\.md"
    - from: "references/platform-master-slicing.md"
      to: "references/platform-specs.md (7-row matrix + rigid constraints)"
      via: "explicit citation in 7-variant algorithm section"
      pattern: "platform-specs\\.md"
    - from: "references/asset-bus-schema.md (variants[] row)"
      to: "references/platform-master-slicing.md (variants[] schema section)"
      via: "See Also cross-link"
      pattern: "platform-master-slicing\\.md"
---

<objective>
Encode Step 14 (平台母版切片) into the `kais-movie-pipeline` skill: a new ref documenting the 7-variant slicing algorithm + 4 key decision points, a SKILL.md body section wiring Step 14 as an additive extension after Step 13, and schema/DAG doc patches so `variants[]` is a first-class queryable field for Phase 42 DATA.

Purpose: Close the "创意→生产→分发" loop's missing 分发 step. Today the pipeline ends at 1 master.mp4 (Step 13); operators manually re-cut per platform. This phase makes 7-platform emission a deterministic, doc'd algorithm whose output is structured metadata — the contract Phase 42 DATA consumes to attach per-platform metrics.

Output:
- 1 NEW ref: `references/platform-master-slicing.md` (~250-400 lines, bilingual EN headings + 中文 body, format-matched to `pipeline-dag.md`)
- 1 SKILL.md body patch: new `## Step 14 — Platform Master Slicing (Additive)` section (zero frontmatter change — FOUND-08)
- 2 ref patches: `asset-bus-schema.md` (variants[] schema doc) + `pipeline-dag.md` (Step 14 additive annotation, V8.6 13-step numbering preserved)
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@/data/workspace/hermes-agent/CLAUDE.md
@/data/workspace/hermes-agent/.planning/PROJECT.md
@/data/workspace/hermes-agent/.planning/ROADMAP.md
@/data/workspace/hermes-agent/.planning/STATE.md
@/data/workspace/hermes-agent/skills/kais-movie-pipeline/SKILL.md
@/data/workspace/hermes-agent/skills/kais-movie-pipeline/references/platform-specs.md
@/data/workspace/hermes-agent/skills/kais-movie-pipeline/references/pipeline-dag.md
@/data/workspace/hermes-agent/skills/kais-movie-pipeline/references/asset-bus-schema.md
@/data/workspace/hermes-agent/skills/kais-movie-pipeline/references/creative-redlines.md

<format_conventions>
**Reference file format — match `references/pipeline-dag.md` and `references/platform-specs.md` exactly:**
- H1 title with ` — ` separator: `# Platform Master Slicing — 7-Variant Algorithm (Step 14)`
- Top metadata block (3 lines): `**Source:**` (Notion page_id + anchor_block_id + brief attribution), `**Copyright:**` (Fair Use — factual algorithm structure; brief operational definitions reproduced with attribution), `**Last-verified:**` 2026-06-26
- `---` horizontal rule separating sections
- Tables for the 7-variant matrix and the 4-decision-point matrix
- `## See Also` footer with cross-links to sibling refs (`platform-specs.md`, `pipeline-dag.md`, `asset-bus-schema.md`, `creative-redlines.md`)
- Bilingual: EN headings + 中文 body (per CLAUDE.md "Skill File Conventions"); refs are 中文-primary with EN glosses for key terms only

**SKILL.md body patch format:**
- Insert a NEW `## Step 14 — Platform Master Slicing (Additive)` H2 section. Insertion point: after `## Review Gates` (which ends ~line 172) and before `## Asset Bus Schema` (starts ~line 174). This places Step 14 logically between the V8.6 8-gate review structure and the asset bus it extends — clean narrative flow.
- The section MUST declare additivity up front: "*Step 14 is an ADDITIVE extension introduced in v9.0 Phase 38. The V8.6 13-step numbering is preserved (Step 1–13 unchanged). Step 14 fires AFTER Step 13 delivery.*"
- Do NOT modify the existing `## Phase ↔ Expert Mapping` table (V8.6 13-step table is frozen). Step 14 gets its own self-contained mapping in the new section.
- Do NOT modify YAML frontmatter. FOUND-08 frozen rule: `expert_id`, `related_skills`, `metrics`, `metadata.hermes.*` all byte-identical to pre-v9.0 (verified against commit `a2a20d2be`).

**Ref patch format (asset-bus-schema.md / pipeline-dag.md):**
- APPEND-only. Do not edit or reorder existing rows. Add new sections clearly marked as Phase 38 / v9.0 additions.
- In `asset-bus-schema.md`: add a new `## Phase 38 Slots (Additive — variants[])` section after the existing `## Phase 36 Slots` section, documenting the variants[] schema.
- In `pipeline-dag.md`: add a new `## Step 14 — Additive Extension (Phase 38 v9.0)` section after the existing `## Slot Flow Per Edge` section, with a single-row ASCII annotation showing Step 13 → Step 14 (additive, V8.6 13-step numbering preserved).

Forbidden:
- YAML frontmatter edits on SKILL.md (FOUND-08)
- Python / JS code changes (this phase is skill + ref only)
- Editing any of the 15 movie-experts SKILL.md files (Phase 38 touches only `kais-movie-pipeline/SKILL.md` + 3 refs under it)
- Renaming or deleting any existing DAG step, gate, slot, or table row
- Inventing aspect ratios or hook timestamps that contradict `platform-specs.md` — every numeric value in the 7-variant table MUST trace to either platform-specs.md's 7-row matrix or its 刚性约束 section
</format_conventions>

<interfaces>
No new code interfaces. This plan is refs + SKILL.md body patch only. All "interfaces" are markdown link targets + a JSON schema shape documented in markdown.

**Ref path created (relative to repo root):**
- skills/kais-movie-pipeline/references/platform-master-slicing.md

**Files patched (body only):**
- skills/kais-movie-pipeline/SKILL.md (insert new `## Step 14` H2 section)
- skills/kais-movie-pipeline/references/asset-bus-schema.md (append `## Phase 38 Slots` section)
- skills/kais-movie-pipeline/references/pipeline-dag.md (append `## Step 14 — Additive Extension` section)

**variants[] schema shape (the contract Phase 42 DATA consumes — documented in markdown, not enforced by code in this phase):**

```json
{
  "episode_id": "ep-001",
  "variants": [
    {
      "platform": "douyin_vertical_916",
      "aspect_ratio": "9:16",
      "length_sec": 60,
      "hook_timestamps": {
        "opening_hook_start_sec": 0,
        "opening_hook_end_sec": 3,
        "closing_hook_start_sec": 57,
        "closing_hook_end_sec": 60
      },
      "cut_points": [
        { "timestamp_sec": 3, "reason": "opening_hook_boundary" },
        { "timestamp_sec": 8, "reason": "first_emotional_turn" },
        { "timestamp_sec": 30, "reason": "memory_closure" },
        { "timestamp_sec": 57, "reason": "closing_hook_boundary" }
      ],
      "source_master_hash": "sha256:<master-mp4-slot-hash>"
    }
    // ... 6 more variant objects, one per platform row in platform-specs.md 7-row matrix
  ]
}
```

The 7 `platform` enum values (per platform-specs.md rigid-constraint layer + ROADMAP SC#1 enumeration):
1. `douyin_vertical_916` (抖音竖屏 9:16)
2. `douyin_horizontal_169` (抖音横屏 16:9)
3. `kuaishou_vertical` (快手竖屏)
4. `bilibili_horizontal_long` (B 站横屏 5-10min)
5. `xiaohongshu_vertical_short` (小红书竖屏 3min)
6. `shipinhao_horizontal` (视频号横屏)
7. `hongguo_kuaishou_micro` (红果或快手极短 1-2min)
</interfaces>
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Author new ref `references/platform-master-slicing.md` (7-variant algorithm + 4 key decision points + variants[] schema)</name>
  <files>skills/kais-movie-pipeline/references/platform-master-slicing.md</files>
  <behavior>
  Ref must satisfy all 4 grep-checked invariants in <verify>:
  - Cites Notion source page 32811082-af8e-8009-b097-d19a5027b46f
  - Contains all 7 platform enum names from the variants[] interface contract
  - Contains all 5 variants[] schema field names (platform / aspect_ratio / length / hook_timestamps / cut_points)
  - Contains the 4 key decision points (D1 aspect-ratio source / D2 hook repositioning / D3 卡点 density / D4 closing hook)
  - Cross-links platform-specs.md, pipeline-dag.md, asset-bus-schema.md in See Also
  - ≥250 non-empty content lines (substantive, not stub)
  </behavior>
  <action>
Create the NEW ref file at `skills/kais-movie-pipeline/references/platform-master-slicing.md`. Match the format of existing `references/pipeline-dag.md` + `references/platform-specs.md` exactly (H1 title with ` — ` separator, top metadata block with Notion source citation, `---` separator, EN headings + 中文 body, `## See Also` footer).

**File structure (use these exact H2 sections in this order):**

`# Platform Master Slicing — 7-Variant Algorithm (Step 14)`

Top metadata block (3 lines):
- `**Source:** Notion page 32811082-af8e-8009-b097-d19a5027b46f (anchor block 38211082-af8e-800e-b464-c65441cf8e6e, "心流♥ → aigc开发 → 创作方向" §平台策略). Tier A ref `platform-specs.md` is the canonical 7-row matrix source; this ref encodes the slicing algorithm that consumes it.`
- `**Copyright:** Fair Use — factual algorithm structure + brief operational definitions reproduced with attribution; no copyrighted creative content.`
- `**Last-verified:** 2026-06-26`

`---`

`## Summary` — 1-paragraph scope statement: 本 ref 是 **Step 14 平台母版切片算法**的权威源。它把 1 个 master.mp4 (Step 13 交付)切成 7 个平台 variants,每个 variant 自动调整 aspect ratio / hook position / 卡点密度 / 结尾钩子,所有数值参数都来自 `platform-specs.md` 7-row 硬性规格矩阵 + 12-row 刚性约束。Phase 38 (v9.0) 引入;Phase 42 (DATA) 消费 variants[] metadata 接入平台 API metrics。

`## 7-Variant Emission Matrix (SLICE-01)` — A 7-row table, one row per platform. Columns: `平台 enum` | `中文名 + 形态` | `aspect_ratio` | `length_sec` | `hook_position` | `Source row in platform-specs.md`. Reproduce values verbatim from `platform-specs.md` 硬性规格对照表 (the 2-column 竖屏滑动 vs 横屏主动 table) and 刚性约束 section. The 7 rows MUST be (in this exact order):
  1. `douyin_vertical_916` | 抖音竖屏 9:16 (竖屏滑动) | 9:16 | 15-60 | 第 1-3 秒 | platform-specs.md 硬性规格对照表 竖屏滑动列
  2. `douyin_horizontal_169` | 抖音横屏 16:9 (横屏主动, 抖音横屏短剧) | 16:9 | 90-300 | 第 5-10 秒 | platform-specs.md 硬性规格对照表 横屏主动列
  3. `kuaishou_vertical` | 快手竖屏 (竖屏滑动) | 9:16 | 15-60 | 第 1-3 秒 | platform-specs.md 硬性规格对照表 竖屏滑动列 (快手与抖音同形态)
  4. `bilibili_horizontal_long` | B 站横屏长 (横屏主动, 5-10min) | 16:9 | 300-600 | 第 5-10 秒 + 30 秒信任死亡线 | platform-specs.md 硬性规格对照表 横屏主动列 (上限放宽至 5-10min per ROADMAP SC#1)
  5. `xiaohongshu_vertical_short` | 小红书竖屏短 (竖屏滑动, 3min) | 9:16 | 60-180 | 第 1-3 秒 | platform-specs.md 硬性规格对照表 竖屏滑动列 (小红书 3min 上限 per ROADMAP SC#1)
  6. `shipinhao_horizontal` | 视频号横屏 (横屏主动) | 16:9 | 90-300 | 第 5-10 秒 | platform-specs.md 硬性规格对照表 横屏主动列
  7. `hongguo_kuaishou_micro` | 红果/快手极短 (竖屏滑动, 1-2min) | 9:16 | 60-120 | 第 1-3 秒 | platform-specs.md 硬性规格对照表 竖屏滑动列 (红果/快手极短 1-2min per ROADMAP SC#1)

  Note explicitly under the table: "aspect_ratio 与 length_sec 全部源自 `platform-specs.md` 硬性规格对照表 + ROADMAP Phase 38 SC#1 枚举。本 ref 不发明数值;仅做算法编排。"

`## Slicing Algorithm — 4 Key Decision Points (SLICE-02)` — The core algorithmic section. Explain that the slicing pipeline walks 4 decision points PER variant (7 variants × 4 decisions = 28 deterministic transformations, all sourced from `platform-specs.md`). For each decision point, use this template:

  ```
  ### D{n}. {Decision name (EN)} — {中文}

  **Input:** {what feeds this decision from master.mp4 + Step 13 metadata}
  **Source rule:** {which row of platform-specs.md hard-spec matrix or rigid-constraint layer governs this}
  **Algorithm:** {step-by-step transformation, 2-4 bullets}
  **Output field:** {which variants[] schema field this decision populates}
  ```

  The 4 decision points:
  - **D1. Aspect-Ratio Adaptation (画幅适配)** — Input: master.mp4 native aspect. Source rule: 7-Variant Emission Matrix `aspect_ratio` column (above) + platform-specs.md 硬性规格对照表. Algorithm: crop/pad master to target aspect (9:16 vertical → center-crop with safe-area = top 2/3 + bottom 1/3 for swipe-gesture zone avoidance per 刚性约束 行为层 "划走手势触发区"; 16:9 horizontal → letterbox or reframe). Output field: `aspect_ratio`.
  - **D2. Opening Hook Repositioning (开头钩子重定位)** — Input: master.mp4 timeline + Step 1 hook-design slot. Source rule: platform-specs.md 硬性规格对照表 "钩子位置" row (竖屏 第 1-3 秒 / 横屏 第 5-10 秒) + 刚性约束 平台层 "冷启动秒级审判". Algorithm: detect master's existing opening hook (via hook-design slot's `timestamp_sec`), then for vertical variants force-hook at 0-3s (if master opens with exposition, re-cut to bring conflict forward — per `creative-redlines.md` R3 零背景铺垫); for horizontal variants allow 5-10s ramp but ensure 30s 信任死亡线 has first emotional turn. Output field: `hook_timestamps.opening_hook_{start,end}_sec`.
  - **D3. Mid-Segment 卡点 Density Adjustment (中段卡点密度)** — Input: master.mp4 emotion-tagged beat sheet (from `spatio-temporal-script` slot, Step 6). Source rule: platform-specs.md 硬性规格对照表 "情绪单元间隔" row (竖屏 ≤ 8s / 横屏 ≤ 60-90s) + 刚性约束 行为层 "重复观看触发条件 每 15s/60s ≥ 1 个异常点". Algorithm: compute emotion-unit density of master; if vertical variant has gap > 8s, insert additional 卡点 (re-cut from B-roll or speed-ramp); if horizontal variant gap > 90s, likewise. Output field: `cut_points[]` (entries with `reason: emotion_unit_gap_fill`).
  - **D4. Closing Hook Injection (结尾新钩子注入)** — Input: master.mp4 ending timeline. Source rule: `creative-redlines.md` R4 结尾未完成 + platform-specs.md 刚性约束 行为层 "收藏/转发 决策窗口 结尾前 3 秒". Algorithm: detect master's ending; if closure-only, synthesize new open-question cut (from B-roll or next-episode teaser) in the final 3s (vertical) / 10s (horizontal); emit closing hook timestamps. Output field: `hook_timestamps.closing_hook_{start,end}_sec` + `cut_points[]` entries with `reason: closing_hook_boundary`.

`## variants[] Schema (SLICE-03)` — Document the JSON shape (reproduce the `<interfaces>` schema verbatim above). 5-field table:

  | Field | Type | Source decision | Consumer |
  |-------|------|-----------------|----------|
  | `platform` | enum (7 values) | D1 | Phase 42 DATA bucketing |
  | `aspect_ratio` | string "W:H" | D1 | Phase 42 rendering validation |
  | `length_sec` | int | D1 (matrix) | Phase 42 completion-rate denominator |
  | `hook_timestamps` | {opening_{start,end}, closing_{start,end}} | D2 + D4 | Phase 42 hook_dropoff_rate window |
  | `cut_points` | [{timestamp_sec, reason}] | D2 + D3 + D4 | Phase 42 per-cut retention analysis |

  Add a paragraph: "variants[] 是 `pipeline_state.episode_id` 上的 ADDITIVE 字段(Phase 38 引入)。它不替换现有 13-step 任何 slot;在 master-mp4 slot 写入后由 Step 14 追加。Schema enforcement 由 Phase 42 DATA 在消费侧做 Pydantic 校验;Phase 38 只产出 schema 文档,不写 Python 校验代码。"

`## Slicing Pipeline I/O Contract` — A diagram showing inputs (master-mp4 slot + hook-design slot + spatio-temporal-script slot + scene-images slot) → Step 14 algorithm → outputs (variants[] metadata + 7 per-platform mp4 paths in delivery-package slot extension). ASCII or markdown bullets. Make explicit which existing slots are READ (no slot writes outside variants[] extension + delivery-package per-platform paths).

`## Per-Expert Consultation Guide` — short bullet list:
  - `editor` — executes the actual cut decisions (D2/D3/D4); this ref is editor's primary Step 14 input
  - `hook_retention` — owns hook-design slot that D2 consumes; consulted when D2 must re-cut a non-conflict opening
  - `cinematographer` — owns composition; consulted when D1 aspect-ratio adaptation requires reframe decision (center-crop safe-area)
  - `compliance_gate` — final sign-off on each variant (per platform AIGC 标识 requirement in 刚性约束 平台层)

`## See Also` — cross-link `platform-specs.md` (canonical 7-row source) + `pipeline-dag.md` (Step 14 DAG position) + `asset-bus-schema.md` (variants[] slot doc) + `creative-redlines.md` (R3/R4 invariants the algorithm enforces) + `genre-anchor-urban-fantasy.md` (v1 per-platform content form alignment).

**CRITICAL — do NOT:**
- Invent aspect ratios. Every value in the 7-Variant Emission Matrix must trace to either `platform-specs.md` 硬性规格对照表 or ROADMAP Phase 38 SC#1 enumeration. If a value is unclear, write `<verify against platform-specs.md>` rather than fabricate.
- Add YAML frontmatter (refs are plain markdown per `pipeline-dag.md` precedent).
- Touch SKILL.md or any other ref in this task — that's Tasks 2 and 3.
- Translate 中文 verbatim values from platform-specs.md into English (refs are 中文-primary per CLAUDE.md).
- Document Python implementation. This is an algorithm spec; Phase 42 writes the adapter code.
  </action>
  <verify>
    <automated>
cd /data/workspace/hermes-agent
F=skills/kais-movie-pipeline/references/platform-master-slicing.md
test -f "$F" || { echo "MISSING: $F"; exit 1; }

# Must cite Notion source
grep -q "32811082-af8e-8009-b097-d19a5027b46f" "$F" || { echo "NO NOTION CITATION"; exit 1; }

# Must have all required H2 sections
for h in "## Summary" "## 7-Variant Emission Matrix" "## Slicing Algorithm" "## variants\[\] Schema" "## Slicing Pipeline I/O Contract" "## Per-Expert Consultation Guide" "## See Also"; do
  grep -q "$h" "$F" || { echo "MISSING SECTION: $h"; exit 1; }
done

# Must contain all 7 platform enum values (the contract)
for p in douyin_vertical_916 douyin_horizontal_169 kuaishou_vertical bilibili_horizontal_long xiaohongshu_vertical_short shipinhao_horizontal hongguo_kuaishou_micro; do
  grep -q "$p" "$F" || { echo "MISSING PLATFORM ENUM: $p"; exit 1; }
done

# Must contain all 5 variants[] schema field names
for f in platform aspect_ratio length hook_timestamps cut_points; do
  grep -q "$f" "$F" || { echo "MISSING SCHEMA FIELD: $f"; exit 1; }
done

# Must contain all 4 decision points
for d in "D1. Aspect-Ratio Adaptation" "D2. Opening Hook Repositioning" "D3. Mid-Segment" "D4. Closing Hook Injection"; do
  grep -q "$d" "$F" || { echo "MISSING DECISION POINT: $d"; exit 1; }
done

# Must cross-link the 4 sibling refs
for r in platform-specs.md pipeline-dag.md asset-bus-schema.md creative-redlines.md; do
  grep -q "$r" "$F" || { echo "MISSING CROSS-LINK: $r"; exit 1; }
done

# Minimum substantive content (≥250 non-empty lines, excluding pure-blank lines and --- separators)
lines=$(grep -cv '^[[:space:]]*$' "$F")
[ "$lines" -ge 250 ] || { echo "TOO SHORT: $lines non-empty lines (need ≥250)"; exit 1; }

echo "TASK 1 OK ($lines non-empty lines)"
    </automated>
  </verify>
  <done>
New ref `skills/kais-movie-pipeline/references/platform-master-slicing.md` exists with:
- ≥250 non-empty lines of substantive content
- All 7 required H2 sections in order
- All 7 platform enum values present
- All 5 variants[] schema fields present
- All 4 decision points (D1-D4) present with Input/Source rule/Algorithm/Output field structure
- Notion source cited; format matches `pipeline-dag.md` (H1 + metadata block + `---` + body + See Also)
- Cross-links to all 4 sibling refs (platform-specs / pipeline-dag / asset-bus-schema / creative-redlines)
- No fabricated numbers — every numeric value traces to platform-specs.md or ROADMAP SC#1
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Patch SKILL.md body — add `## Step 14 — Platform Master Slicing (Additive)` section (zero frontmatter change)</name>
  <files>skills/kais-movie-pipeline/SKILL.md</files>
  <action>
Insert a NEW `## Step 14 — Platform Master Slicing (Additive)` H2 section into `skills/kais-movie-pipeline/SKILL.md`. Insertion point: AFTER the existing `## Review Gates` section (which ends around the line containing "Gate resolution outcomes are written to the AssetBus `review-outcomes` slot") and BEFORE the existing `## Asset Bus Schema` section.

Use the Edit tool surgically — do NOT rewrite the file. Anchor the edit on the existing `## Asset Bus Schema` heading and insert the new section above it.

**Section content (use this exact structure):**

```markdown
## Step 14 — Platform Master Slicing (Additive)

*Step 14 is an ADDITIVE extension introduced in v9.0 Phase 38. The V8.6 13-step numbering is preserved (Step 1–13 unchanged). Step 14 fires AFTER Step 13 delivery completes.*

**Purpose:** Turn 1 master.mp4 (Step 13 output) into 7 platform-specific variants — 抖音竖屏 9:16 / 抖音横屏 16:9 / 快手竖屏 / B 站横屏 5-10min / 小红书竖屏 3min / 视频号横屏 / 红果或快手极短 1-2min. Each variant auto-adapts aspect ratio + opening hook position + mid-segment 卡点 density + closing hook, all per `references/platform-specs.md` rigid constraints (not manual).

**Algorithm source:** [`references/platform-master-slicing.md`](references/platform-master-slicing.md) — canonical 7-variant algorithm + 4 key decision points (D1 aspect-ratio / D2 opening hook / D3 卡点 density / D4 closing hook).

**Inputs (READ from existing slots — Step 14 does NOT write to these):**
- `master-mp4` (p13 output) — source master render
- `hook-design` (p01 output) — opening hook timestamp for D2 repositioning
- `spatio-temporal-script` (p06 output) — emotion-tagged beat sheet for D3 卡点 density
- `scene-images` (p07 output) — B-roll candidates for D2/D4 re-cut injection

**Outputs (WRITE — additive):**
- `pipeline_state.episode_id.variants[]` — 7-element array, schema documented in `references/platform-master-slicing.md` §variants[] Schema and `references/asset-bus-schema.md` §Phase 38 Slots. Fields: `platform` / `aspect_ratio` / `length` / `hook_timestamps` / `cut_points`.
- `delivery-package` slot extension — 7 per-platform mp4 paths (additive to existing p13 delivery-package manifest)

**Expert involvement:** editor (executes cuts), hook_retention (consults on D2/D4 hook repositioning), cinematographer (consults on D1 aspect-ratio reframe), compliance_gate (final per-variant AIGC 标识 sign-off per `references/platform-specs.md` 刚性约束 平台层).

**Phase 42 contract:** variants[] is the data contract Phase 42 DATA consumes to attach per-platform metrics (完播率 / 卡点跳出率 / 互动率 / 收藏率 / 评论率). Schema enforcement happens consumer-side in Phase 42; Phase 38 only produces the schema doc + the algorithm spec.
```

**CRITICAL — do NOT:**
- Modify YAML frontmatter. FOUND-08 frozen rule: `expert_id: kais-movie-pipeline`, `metadata.hermes.*`, `related_skills`, `metrics` all byte-identical to pre-v9.0 (verified against commit `a2a20d2be`).
- Edit, reorder, or delete any existing section of SKILL.md. INSERT ONLY.
- Add Step 14 as a row to the existing `## Phase ↔ Expert Mapping` table — that table is the V8.6 13-step canonical table and stays frozen. Step 14 gets its own self-contained section.
- Add Step 14 to the Mermaid DAG block in `## Pipeline DAG` — the V8.6 13-step DAG diagram stays frozen. Step 14's DAG annotation lives in `references/pipeline-dag.md` (Task 3).
- Use Edit to rewrite the whole file — use Edit with surgical scope anchored on the `## Asset Bus Schema` heading.
  </action>
  <verify>
    <automated>
cd /data/workspace/hermes-agent
F=skills/kais-movie-pipeline/SKILL.md

# 1. FOUND-08: frontmatter byte-identical to pre-v9.0 (commit a2a20d2be)
# Extract frontmatter from working tree and from v9.0-start commit, diff them
git show a2a20d2be:skills/kais-movie-pipeline/SKILL.md > /tmp/skill_v9_start.md 2>/dev/null
python3 -c "
import re
def fm(path):
    with open(path, encoding='utf-8') as fh:
        c = fh.read()
    m = re.match(r'^---\n(.*?)\n---\n', c, re.DOTALL)
    return m.group(1) if m else ''
fm_now = fm('$F')
fm_start = fm('/tmp/skill_v9_start.md')
assert fm_now == fm_start, f'FRONTMATER CHANGED:\n--- now ---\n{fm_now}\n--- v9.0 start ---\n{fm_start}'
# Key fields intact
for k in ['expert_id: kais-movie-pipeline', 'name: kais-movie-pipeline']:
    assert k in fm_now, f'MISSING frontmatter key: {k}'
print('FRONTMATTER BYTE-IDENTICAL OK')
"

# 2. New section present
grep -q "^## Step 14 — Platform Master Slicing (Additive)" "$F" || { echo "MISSING Step 14 SECTION"; exit 1; }

# 3. Step 14 section links the new ref
grep -q "platform-master-slicing.md" "$F" || { echo "MISSING LINK TO NEW REF"; exit 1; }

# 4. Step 14 section declares additivity
grep -q "ADDITIVE extension" "$F" || { echo "MISSING ADDITIVITY DECLARATION"; exit 1; }

# 5. Step 14 section references all 5 schema fields
for f in platform aspect_ratio length hook_timestamps cut_points; do
  grep -q "$f" "$F" || { echo "MISSING SCHEMA FIELD IN SKILL.md: $f"; exit 1; }
done

# 6. V8.6 13-step Mermaid block still intact (Step 1 through p13 unchanged)
grep -q "p13\[p13 delivery" "$F" || { echo "DAG CORRUPTED — p13 node missing"; exit 1; }
grep -q "gate_count: 8" "$F" || { echo "FRONTMATER pipeline.gate_count CHANGED — FOUND-08 violation"; exit 1; }
grep -q "step_count: 13" "$F" || { echo "FRONTMATER pipeline.step_count CHANGED — FOUND-08 violation"; exit 1; }

# 7. Insertion is between Review Gates and Asset Bus Schema
sec14=$(grep -n "^## Step 14" "$F" | cut -d: -f1)
abs=$(grep -n "^## Asset Bus Schema" "$F" | cut -d: -f1)
rg=$(grep -n "^## Review Gates" "$F" | cut -d: -f1)
[ -n "$sec14" ] && [ -n "$abs" ] && [ -n "$rg" ] && [ "$rg" -lt "$sec14" ] && [ "$sec14" -lt "$abs" ] || {
  echo "INSERTION ORDER WRONG: Review Gates=$rg Step14=$sec14 AssetBus=$abs (expected RG < Step14 < ABS)"; exit 1;
}

echo "TASK 2 OK"
    </automated>
  </verify>
  <done>
`skills/kais-movie-pipeline/SKILL.md` patched (body-only):
- New `## Step 14 — Platform Master Slicing (Additive)` H2 section inserted between `## Review Gates` and `## Asset Bus Schema`
- Section declares additivity, links `references/platform-master-slicing.md`, lists 4 input slots + 2 outputs + 4 involved experts
- Frontmatter byte-identical to commit `a2a20d2be` (verified by Python diff)
- V8.6 13-step DAG (Mermaid block + Phase ↔ Expert Mapping table) untouched
- `pipeline.step_count: 13` + `pipeline.gate_count: 8` frontmatter values unchanged (Step 14 is additive, does NOT bump the V8.6 counter)
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 3: Patch asset-bus-schema.md (variants[] schema) + pipeline-dag.md (Step 14 additive annotation)</name>
  <files>skills/kais-movie-pipeline/references/asset-bus-schema.md, skills/kais-movie-pipeline/references/pipeline-dag.md</files>
  <action>
APPEND new sections to both existing refs. Use Edit tool surgically — do NOT rewrite either file. APPEND ONLY (no edits to existing rows/sections).

**File 1: `skills/kais-movie-pipeline/references/asset-bus-schema.md`**

Insert a NEW `## Phase 38 Slots (Additive — variants[])` section AFTER the existing `## Phase 36 Slots (Complete — 36-01..36-04 Wave 1)` section and BEFORE the existing `## Envelope Schema` section.

Section content:

```markdown
## Phase 38 Slots (Additive — variants[])

> Added in Phase 38 (v9.0). Per CONTEXT D-38-01: variants[] is an ADDITIVE field on the `pipeline_state.episode_id` struct, NOT a new top-level AssetBus slot. It is written by Step 14 (Platform Master Slicing) after the existing `master-mp4` slot (p13 output) is populated.

**Lifecycle:** write-once per episode (after Step 14 slicing completes). Read by Phase 42 DATA adapters for per-platform metric bucketing.

| Field | Format | Writer | Reader | Purpose |
|-------|--------|--------|--------|---------|
| `variants[]` | JSON (array on episode_id) | Step 14 (Platform Master Slicing, v9.0 Phase 38) | Phase 42 DATA adapter (per-platform metric attachment) | 7-element array, one per platform variant. Schema: `{platform, aspect_ratio, length, hook_timestamps, cut_points, source_master_hash}`. Canonical algorithm + field semantics: [`platform-master-slicing.md`](./platform-master-slicing.md) §variants[] Schema |

**Schema (reproduced from `platform-master-slicing.md`):**

```json
{
  "variants": [
    {
      "platform": "<one of 7 enum values per platform-master-slicing.md>",
      "aspect_ratio": "<W:H per platform-specs.md 7-row matrix>",
      "length": <int, seconds>,
      "hook_timestamps": {
        "opening_hook_start_sec": <float>,
        "opening_hook_end_sec": <float>,
        "closing_hook_start_sec": <float>,
        "closing_hook_end_sec": <float>
      },
      "cut_points": [
        {"timestamp_sec": <float>, "reason": "<opening_hook_boundary|first_emotional_turn|memory_closure|emotion_unit_gap_fill|closing_hook_boundary>"}
      ],
      "source_master_hash": "sha256:<master-mp4 slot content_hash>"
    }
  ]
}
```

**Naming note:** `variants[]` is a field on the existing `episode_id` struct in `pipeline_state`, NOT a new slot in `ASSET_SCHEMA`. It is documented here alongside slot schemas because it follows the same envelope + atomic-write + creative-history-DAG conventions. Phase 42 DATA will add consumer-side Pydantic validation; Phase 38 ships the schema doc only (no Python code).
```

**File 2: `skills/kais-movie-pipeline/references/pipeline-dag.md`**

Insert a NEW `## Step 14 — Additive Extension (Phase 38 v9.0)` section AFTER the existing `## Slot Flow Per Edge` section and BEFORE the existing `## Refresh Cadence` section.

Section content:

```markdown
## Step 14 — Additive Extension (Phase 38 v9.0)

> Added in Phase 38 (v9.0). Step 14 is ADDITIVE — the V8.6 13-step numbering is preserved (Step 1–13 unchanged, `step_count: 13` in frontmatter unchanged). Step 14 fires AFTER Step 13 delivery completes.

**Purpose:** Platform master slicing — turn 1 master.mp4 into 7 platform-specific variants (抖音竖屏 / 抖音横屏 / 快手竖屏 / B 站横屏 5-10min / 小红书竖屏 3min / 视频号横屏 / 红果或快手极短). Algorithm + 4 decision points: [`platform-master-slicing.md`](./platform-master-slicing.md).

**DAG position (ASCII):**

```
[Step 13 delivery] ──(writes master-mp4)──▶ [Step 14 platform slicing] ──(writes variants[])──▶ (Phase 42 DATA consumes)
                                                  │
                                                  └── READS: master-mp4, hook-design, spatio-temporal-script, scene-images
```

**Step 14 does NOT:**
- Modify any of the 13 V8.6 Steps or their slot writes
- Add a new gate (the existing 8-gate V8.6 review structure is unchanged; per-variant compliance sign-off happens via the existing `final-delivery` Gate 8 + per-variant AIGC labeling)
- Appear in the frontmatter `pipeline.step_count` (stays 13) or `pipeline.gate_count` (stays 8)

**Phase 42 contract:** variants[] is the data contract Phase 42 DATA consumes to attach per-platform metrics. See [`asset-bus-schema.md`](./asset-bus-schema.md) §Phase 38 Slots for schema.
```

**CRITICAL — do NOT:**
- Edit, reorder, or delete any existing row of either ref. APPEND ONLY.
- Add YAML frontmatter (refs are plain markdown).
- Change the `step_count: 13` or `gate_count: 8` mentions anywhere — they are V8.6 frozen counters.
- Document Python implementation — schema + algorithm spec only.
  </action>
  <verify>
    <automated>
cd /data/workspace/hermes-agent

# === File 1: asset-bus-schema.md ===
F1=skills/kais-movie-pipeline/references/asset-bus-schema.md
grep -q "^## Phase 38 Slots" "$F1" || { echo "MISSING Phase 38 SECTION in asset-bus-schema.md"; exit 1; }
grep -q "variants\[\]" "$F1" || { echo "MISSING variants[] mention"; exit 1; }
grep -q "platform-master-slicing.md" "$F1" || { echo "MISSING cross-link to new ref"; exit 1; }
# Must contain all 5 schema field names in the JSON block
for f in platform aspect_ratio length hook_timestamps cut_points; do
  grep -q "\"$f\"" "$F1" || grep -q "$f" "$F1" || { echo "MISSING SCHEMA FIELD: $f"; exit 1; }
done
# Insertion order: Phase 36 < Phase 38 < Envelope Schema
p36=$(grep -n "^## Phase 36 Slots" "$F1" | cut -d: -f1)
p38=$(grep -n "^## Phase 38 Slots" "$F1" | cut -d: -f1)
env=$(grep -n "^## Envelope Schema" "$F1" | cut -d: -f1)
[ -n "$p36" ] && [ -n "$p38" ] && [ -n "$env" ] && [ "$p36" -lt "$p38" ] && [ "$p38" -lt "$env" ] || {
  echo "ORDER WRONG in asset-bus-schema.md: P36=$p36 P38=$p38 Env=$env"; exit 1;
}

# === File 2: pipeline-dag.md ===
F2=skills/kais-movie-pipeline/references/pipeline-dag.md
grep -q "^## Step 14 — Additive Extension" "$F2" || { echo "MISSING Step 14 SECTION in pipeline-dag.md"; exit 1; }
grep -q "platform-master-slicing.md" "$F2" || { echo "MISSING cross-link to new ref"; exit 1; }
grep -q "asset-bus-schema.md" "$F2" || { echo "MISSING cross-link to asset-bus-schema"; exit 1; }
grep -q "ADDITIVE" "$F2" || { echo "MISSING ADDITIVE declaration"; exit 1; }
# V8.6 counters mentioned as preserved
grep -q "step_count: 13" "$F2" || grep -q "13-step numbering is preserved" "$F2" || { echo "MISSING step_count preservation note"; exit 1; }
# Insertion order: Slot Flow Per Edge < Step 14 < Refresh Cadence
sfe=$(grep -n "^## Slot Flow Per Edge" "$F2" | cut -d: -f1)
s14=$(grep -n "^## Step 14 — Additive Extension" "$F2" | cut -d: -f1)
rc=$(grep -n "^## Refresh Cadence" "$F2" | cut -d: -f1)
[ -n "$sfe" ] && [ -n "$s14" ] && [ -n "$rc" ] && [ "$sfe" -lt "$s14" ] && [ "$s14" -lt "$rc" ] || {
  echo "ORDER WRONG in pipeline-dag.md: SFE=$sfe Step14=$s14 RC=$rc"; exit 1;
}

echo "TASK 3 OK"
    </automated>
  </verify>
  <done>
Both ref files patched (append-only):
- `asset-bus-schema.md`: new `## Phase 38 Slots (Additive — variants[])` section between Phase 36 Slots and Envelope Schema; documents variants[] schema with all 5 fields + JSON example + cross-link to platform-master-slicing.md
- `pipeline-dag.md`: new `## Step 14 — Additive Extension (Phase 38 v9.0)` section between Slot Flow Per Edge and Refresh Cadence; ASCII DAG diagram showing Step 13 → Step 14 → Phase 42; explicit "V8.6 13-step numbering preserved" + "step_count stays 13" declarations
- All existing rows/sections in both refs byte-identical (Edit used surgically, append-only)
  </done>
</task>

<task type="auto" tdd="false">
  <name>Task 4: Phase-level verification — FOUND-08 byte-diff + Step 14 I/O contract + cross-link integrity</name>
  <files>(no file changes — verification only)</files>
  <action>
Run the consolidated phase-level verification script below. This is the gating check before the phase commit. The script is read-only (no file mutations except /tmp scratch). If any check fails, fix the underlying issue in the relevant Task 1/2/3 file and re-run until all checks pass.

The script covers 4 dimensions: (1) FOUND-08 byte-diff of kais-movie-pipeline SKILL.md frontmatter against v9.0 start commit a2a20d2be; (2) Step 14 I/O contract (all 7 platform enums + 4 decision points + 5 schema fields present); (3) cross-link integrity (all referenced sibling refs exist on disk); (4) scope discipline (no Python/JS code changes in working tree).
  </action>
  <verify>
    <automated>
cd /data/workspace/hermes-agent

echo "=== 1. FOUND-08 byte-diff against v9.0 start commit a2a20d2be ==="
# kais-movie-pipeline SKILL.md frontmatter must be byte-identical
git show a2a20d2be:skills/kais-movie-pipeline/SKILL.md > /tmp/kmp_v9start.md
python3 -c "
import re
def fm(p):
    with open(p, encoding='utf-8') as fh: c = fh.read()
    m = re.match(r'^---\n(.*?)\n---\n', c, re.DOTALL)
    return m.group(1) if m else ''
a, b = fm('skills/kais-movie-pipeline/SKILL.md'), fm('/tmp/kmp_v9start.md')
assert a == b, 'FRONTMATTER DRIFT DETECTED'
print('  OK — kais-movie-pipeline SKILL.md frontmatter byte-identical')
"

# All 15 movie-experts SKILL.md frontmatter byte-identical (Phase 38 must not touch any of them)
for d in skills/movie-experts/*/; do
  skill="$d/SKILL.md"
  [ -f "$skill" ] || continue
  python3 -c "
import re, sys
def fm(p):
    with open(p, encoding='utf-8') as fh: c = fh.read()
    m = re.match(r'^---\n(.*?)\n---\n', c, re.DOTALL)
    return m.group(1) if m else ''
" "$skill" 2>/dev/null
done
echo "  OK — Phase 38 touches ZERO movie-experts SKILL.md files (found $(git diff --name-only a2a20d2be..HEAD -- skills/movie-experts/ | wc -l) changed vs v9.0 start; expect 0 in this phase's working tree)"
git status --porcelain skills/movie-experts/ | grep -q . && echo "  WARN — movie-experts has uncommitted changes (investigate)" || echo "  OK — no movie-experts changes in working tree"

echo ""
echo "=== 2. Step 14 I/O contract check (SLICE-01..04 structural coverage) ==="
# SLICE-01: 7-variant emission
F=skills/kais-movie-pipeline/references/platform-master-slicing.md
for p in douyin_vertical_916 douyin_horizontal_169 kuaishou_vertical bilibili_horizontal_long xiaohongshu_vertical_short shipinhao_horizontal hongguo_kuaishou_micro; do
  grep -q "$p" "$F" && echo "  OK — variant $p documented" || { echo "  FAIL — variant $p MISSING"; exit 1; }
done

# SLICE-02: 4 decision points (aspect / hook / 卡点 / closing)
for d in "Aspect-Ratio" "Opening Hook" "Mid-Segment" "Closing Hook"; do
  grep -q "$d" "$F" && echo "  OK — decision $d documented" || { echo "  FAIL — decision $d MISSING"; exit 1; }
done

# SLICE-03: 5 variants[] schema fields
for f in platform aspect_ratio length hook_timestamps cut_points; do
  grep -q "$f" "$F" && echo "  OK — schema field $f documented" || { echo "  FAIL — field $f MISSING"; exit 1; }
done

# SLICE-04: new ref exists + SKILL.md Step 14 section + frontmatter byte-identical
test -f "$F" && echo "  OK — new ref exists"
grep -q "^## Step 14" skills/kais-movie-pipeline/SKILL.md && echo "  OK — SKILL.md Step 14 section present"

echo ""
echo "=== 3. Cross-link integrity (no dangling relative paths) ==="
for ref in platform-specs.md pipeline-dag.md asset-bus-schema.md creative-redlines.md platform-master-slicing.md; do
  test -f "skills/kais-movie-pipeline/references/$ref" && echo "  OK — $ref exists" || { echo "  FAIL — $ref MISSING"; exit 1; }
done

echo ""
echo "=== 4. Scope discipline (no Python/JS code changes in this phase) ==="
git status --porcelain | grep -E '\.(py|js|ts)$' | grep -q . && echo "  WARN — code files changed (investigate; Phase 38 should be docs-only)" || echo "  OK — no code files changed in working tree"

echo ""
echo "=== ALL PHASE-LEVEL CHECKS PASSED ==="
    </automated>
  </verify>
  <done>
All automated checks print OK. Operator spot-check at commit time: open `references/platform-master-slicing.md` 7-Variant Emission Matrix and confirm every `aspect_ratio` traces to platform-specs.md 硬性规格对照表 (9:16 verticals / 16:9 horizontals) and every `length_sec` range matches ROADMAP Phase 38 SC#1 enumeration (15-60 / 90-300 / 15-60 / 300-600 / 60-180 / 90-300 / 60-120). If any number looks invented, flag it before merge.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| operator → pipeline_state | Operator triggers Step 14 slicing by approving Step 13 delivery (Gate 8). No untrusted external input crosses into Step 14. |
| Step 14 → Phase 42 DATA | variants[] metadata crosses this boundary downstream. Phase 42 applies Pydantic validation consumer-side. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-38-01 | Tampering | variants[] metadata integrity | mitigate | `source_master_hash` field (sha256 of master-mp4 slot content_hash) ties every variant to its source master — Phase 42 can reject variants whose hash doesn't match |
| T-38-02 | Information Disclosure | variants[] may leak master.mp4 internal cut points | accept | variants[] is operator-local pipeline_state; not exposed to platforms (only the rendered variant mp4s are uploaded). Low risk. |
| T-38-03 | Spoofing | Platform enum spoofing (a variant claims `douyin_vertical_916` but is rendered 16:9) | mitigate | D1 algorithm enforces aspect-ratio from platform-specs.md matrix; `aspect_ratio` field must match the platform enum's matrix row (consistency check documented in platform-master-slicing.md) |
| T-38-04 | Repudiation | Operator disputes which variant was emitted | accept | variants[] is write-once per episode with atomic write semantics (per AssetBus V3 envelope convention); creative-history DAG records provenance. Existing v6.0 audit log pattern applies. |
| T-38-SC | Tampering | (N/A — no npm/pip/cargo installs in this phase; pure markdown authoring) | accept | Phase 38 is docs-only. No supply-chain risk. |
</threat_model>

<verification>
**Phase verification (all 4 tasks complete):**

1. **SLICE-01 (7-variant emission):** `platform-master-slicing.md` 7-Variant Emission Matrix contains all 7 platform enum values with correct aspect_ratio per `platform-specs.md` 7-row matrix. (Task 1 + Task 4 verify)
2. **SLICE-02 (auto adjustments):** `platform-master-slicing.md` documents all 4 decision points (D1 aspect / D2 opening hook / D3 卡点 density / D4 closing hook), each with explicit source rule from `platform-specs.md` rigid constraints. (Task 1 + Task 4 verify)
3. **SLICE-03 (variants[] persistence):** `asset-bus-schema.md` §Phase 38 Slots + `platform-master-slicing.md` §variants[] Schema document the 5-field schema. (Task 1 + Task 3 + Task 4 verify)
4. **SLICE-04 (new ref + SKILL.md body section + FOUND-08):** New ref exists, SKILL.md has Step 14 section, SKILL.md frontmatter byte-identical to commit `a2a20d2be`. (Task 1 + Task 2 + Task 4 verify)
5. **Scope discipline:** Zero Python/JS code changes. Zero movie-experts SKILL.md changes. Zero frontmatter changes anywhere. (Task 4 verify)

Run the Task 4 `<how-to-verify>` script end-to-end. All checks MUST print OK.
</verification>

<success_criteria>
- [ ] `references/platform-master-slicing.md` exists, ≥250 non-empty lines, all 7 platform enums + 4 decision points + 5 schema fields + Notion citation + 4 sibling cross-links
- [ ] `SKILL.md` has new `## Step 14 — Platform Master Slicing (Additive)` section between Review Gates and Asset Bus Schema; frontmatter byte-identical to commit `a2a20d2be`
- [ ] `asset-bus-schema.md` has new `## Phase 38 Slots (Additive — variants[])` section with JSON schema + cross-link to platform-master-slicing.md
- [ ] `pipeline-dag.md` has new `## Step 14 — Additive Extension (Phase 38 v9.0)` section with ASCII DAG diagram + V8.6 13-step preservation declaration
- [ ] All 4 SLICE requirements structurally satisfied at the documentation layer (Phase 42 enforces schema consumer-side)
- [ ] FOUND-08 preserved: zero frontmatter changes on kais-movie-pipeline SKILL.md + zero changes to any movie-experts SKILL.md
- [ ] Zero Python/JS code changes (docs-only phase)
- [ ] Task 4 human-verify checkpoint approved
</success_criteria>

<output>
Create `.planning/phases/38-slice-platform-master/38-01-SUMMARY.md` when done, documenting:
- 1 new ref created (path + line count)
- 3 files patched (SKILL.md + 2 refs — sections touched, append-only confirmed)
- All 4 SLICE reqs mapped to deliverables (coverage table)
- FOUND-08 verification result (frontmatter byte-diff against a2a20d2be = identical)
- Verification commands run + pass status
- Commit SHAs (atomic commits per task recommended; docs-only)
- Operator-action-handoff: NONE (Phase 38 is pure docs; Phase 42 has the operator-action-handoff for live API keys)
</output>
