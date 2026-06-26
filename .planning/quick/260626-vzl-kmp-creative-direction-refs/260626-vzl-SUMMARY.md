---
quick_id: 260626-vzl
description: Encode Kai's Notion "创作方向" strategy doc into 3 kais-movie-pipeline refs + patch 3 expert SKILL.md References tables.
type: quick
scope: refs_only_no_code
status: complete
started: 2026-06-26
completed: 2026-06-26
commits:
  - task1: 2e0f72618
  - task2: 10696f3d8
---

# Quick 260626-vzl — Encode Notion "创作方向" into kais-movie-pipeline refs

把 Kai 的 Notion "心流♥ → aigc开发 → 创作方向" 策略文档(4 sections: 平台策略 / 剧集策略 / 启动方案 / 第一性原理分析)编码为 `skills/kais-movie-pipeline/references/` 下的 3 个权威 ref,并通过外科手术式补丁接入 3 个 SKILL.md 的 `## References` 表(compliance_gate / theory_critic / kais-movie-pipeline)。这让 v1 创作策略首次对 agent 可寻址 —— 此前此知识仅存于 Notion。

## What Was Built

### 3 NEW refs (Task 1, commit `2e0f72618`)

| Path | Lines (non-empty) | Sections |
|------|-------------------|----------|
| `skills/kais-movie-pipeline/references/platform-specs.md` | 66 | Summary / 硬性规格对照表 (10 rows 竖屏 vs 横屏) / 刚性约束 (4 layers × 12 rows) / 使用指南 (5 experts) / See Also |
| `skills/kais-movie-pipeline/references/creative-redlines.md` | 78 | Summary / 5 per-episode red lines R1-R5 (情绪脱敏 / 信息分层 / 零背景铺垫 / 结尾未完成 / 差异化识别) / 2 process red lines R6-R7 (控制变量 / 统计显著) / 与 compliance_gate §1..§8 关系 / See Also |
| `skills/kais-movie-pipeline/references/genre-anchor-urban-fantasy.md` | 88 | Summary / 核心 DNA (超能力+轻喜剧+主线悬念) / per-platform content form (8 rows) / 3-month roadmap (M1/M2/M3) / 变现逻辑 / 题材禁忌 (derived) / Why This Genre / See Also |

All 3 refs:
- Cite Notion source `32811082-af8e-8009-b097-d19a5027b46f` + anchor `38211082-af8e-800e-b464-c65441cf8e6e` in top metadata block
- Match format of existing `references/pipeline-dag.md` (H1 with `—` separator, `**Source:**` / `**Copyright:**` / `**Last-verified:**` block, `---` separator, EN headings + 中文 body, `## See Also` footer)
- Preserve 中文 verbatim values from Notion tables per CLAUDE.md "refs 以中文为主" convention
- Mark `<TBD — verify against Notion source>` for one unclear cell (备用第 8 平台 in genre-anchor) — no fabricated numbers

### 3 SKILL.md body patches (Task 2, commit `10696f3d8`)

| SKILL.md | Changes | Scope |
|----------|---------|-------|
| `skills/movie-experts/compliance_gate/SKILL.md` | +2 rows in `## References` table (creative-redlines.md + platform-specs.md) | References table only |
| `skills/movie-experts/theory_critic/SKILL.md` | +2 rows in `## References` table (genre-anchor-urban-fantasy.md + creative-redlines.md) | References table only |
| `skills/kais-movie-pipeline/SKILL.md` | +3 rows in `## References` table + intro count "4 reference docs" → "7 reference docs" (+ source attribution "sub-plan 35-04 + quick task 260626-vzl") | References section only |

All patches:
- Surgical scope verified via `git diff` — only References table rows added; no other body sections touched
- Zero YAML frontmatter changes (FOUND-08 preserved; expert_id / related_skills / metrics / aliases / version all frozen)
- Relative paths verified: `../../kais-movie-pipeline/references/*` from movie-experts/* (up from compliance_gate/ → up from movie-experts/ → into kais-movie-pipeline/references/); `references/*` from kais-movie-pipeline/SKILL.md
- All link target files exist on disk

## Verification

Both `<automated>` verification blocks from PLAN.md ran end-to-end. All checks pass:

**Task 1 (refs) — ALL REFS OK:**
- 3 files exist + cite Notion source + have `## See Also` footer + ≥30 non-empty lines (actual: 66/78/88)
- platform-specs.md contains: 用户契约 / 注意力窗口 / 情绪单元间隔 / 使用指南
- creative-redlines.md contains: 情绪脱敏 / 信息分层 / 零背景铺垫 / 结尾未完成 / 差异化识别 / 控制变量 / 统计显著 / PROCESS RED LINE / compliance_gate mention
- genre-anchor-urban-fantasy.md contains: 都市奇幻 / M1 验证 / M2 平台适配 / M3 IP 延伸 / 红果 / 题材禁忌

**Task 2 (SKILL.md patches) — ALL SKILL.md PATCHES OK:**
- Frontmatter parses + retains `expert_id` + `name:` in all 3 files
- compliance_gate links creative-redlines.md + platform-specs.md
- theory_critic links genre-anchor-urban-fantasy.md + creative-redlines.md
- kais-movie-pipeline links all 3 + count = 7 reference docs
- V8.6 Pipeline Sync heading count unchanged (1 each in compliance_gate / theory_critic) — confirms no accidental edits outside References section

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | `2e0f72618` | `docs(quick-260626-vzl): add 3 creative-direction refs from Notion` (3 files, +340 lines) |
| 2 | `10696f3d8` | `docs(quick-260626-vzl): wire 3 new refs into 3 SKILL.md References tables` (3 files, +8 / -1) |

## Deviations from Plan

None — plan executed exactly as written. No auto-fixes (Rules 1-3) or architectural decisions (Rule 4) triggered.

## Known Stubs

- `genre-anchor-urban-fantasy.md` §Per-Platform Content Form 第 8 行(备用 / 第 8 平台)标注 `<TBD — verify against Notion source>`。Plan 明确允许此处理(plan §CRITICAL: "If a Notion cell value is unclear, write `<TBD — verify against Notion source>` rather than fabricating")。Notion 原文第 8 平台项不明确,故如实标注,不编造。Operator 后续若补充 Notion 源可替换。

## Threat Flags

None — pure markdown refs + body patches; no new network endpoints, auth paths, file access patterns, or schema changes.

## Self-Check: PASSED

**Files created:**
- `skills/kais-movie-pipeline/references/platform-specs.md` — FOUND
- `skills/kais-movie-pipeline/references/creative-redlines.md` — FOUND
- `skills/kais-movie-pipeline/references/genre-anchor-urban-fantasy.md` — FOUND

**Files modified:**
- `skills/movie-experts/compliance_gate/SKILL.md` — FOUND
- `skills/movie-experts/theory_critic/SKILL.md` — FOUND
- `skills/kais-movie-pipeline/SKILL.md` — FOUND

**Commits exist:**
- `2e0f72618` — FOUND
- `10696f3d8` — FOUND
