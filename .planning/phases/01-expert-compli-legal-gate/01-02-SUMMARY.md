---
phase: 01-expert-compli-legal-gate
plan: 02
subsystem: compliance_marketing
tags: [compliance, platform-spec, douyin, kuaishou, miniprogram, 短剧, 爆款, 付费机制, 备案]
requires:
  - "skills/movie-experts/_shared/SKILL-LAYOUT.md (reference anatomy spec)"
  - "skills/movie-experts/_shared/glossary.md (term dictionary)"
  - ".planning/phases/01-expert-compli-legal-gate/01-CONTEXT.md (D-2 platform depth, D-3 drift handling)"
provides:
  - "3 platform-spec reference files (douyin/kuaishou/miniprogram) with identical 5 H2 structure"
  - "_shared/platform-comparison.md cross-platform matrix (3 rows x 4 cols)"
  - "Stable contract for Phase 2 HOOK expert (付费门槛 + 爆款公式 columns)"
affects:
  - "skills/movie-experts/compliance_marketing/SKILL.md (Plan 01-03 will reference these 3 specs)"
  - "skills/movie-experts/hook_retention (Phase 2 will consume matrix)"
tech-stack:
  added: []
  patterns:
    - "Identical H2 structure across 3 platform refs (CONTEXT D-2)"
    - "Quarterly Refresh Cadence + Drift Signals pattern"
    - "*estimated* marker for uncertain CN regulatory thresholds"
    - "Additive-only column stability contract for downstream consumers"
key-files:
  created:
    - "skills/movie-experts/compliance_marketing/references/platform-specs-douyin.md"
    - "skills/movie-experts/compliance_marketing/references/platform-specs-kuaishou.md"
    - "skills/movie-experts/compliance_marketing/references/platform-specs-miniprogram.md"
    - "skills/movie-experts/_shared/platform-comparison.md"
  modified: []
decisions:
  - "Identical 5 H2 sections (分发规则/内容红线/付费机制/备案要求/爆款公式) across all 3 platform refs (CONTEXT D-2)"
  - "Used plain 'verified_date:' (no markdown bold) on header line 6 to match plan verify literal"
  - "Marked ~20+ uncertain CN regulatory thresholds (分账比例, 完播率门槛, 付费转化率) with *estimated* per Claude's Discretion"
  - "Used placeholder 备案号 formats (<广电网剧备案号:一类-XXXX-XXXX>) — never fabricated real备案号 strings (threat T-01-07 mitigation)"
  - "Platform Selection Decision Tree includes 7 content-type scenarios (男频/女频/草根/家庭/长剧/互动剧/AIGC 漫剧)"
  - "Stable Contract for Phase 2 HOOK commits to additive-only column policy (threat T-01-09 mitigation)"
metrics:
  duration: "5 min"
  completed: "2026-06-15"
  tasks: 2
  files: 4
---

# Phase 1 Plan 02: Platform Specs + Cross-Platform Matrix Summary

Authored 3 platform-spec reference files (抖音 / 快手 / 微信小程序剧) with identical 5 H2 structure (分发规则 / 内容红线 / 付费机制 / 备案要求 / 爆款公式), plus a 3-row × 4-column cross-platform comparison matrix under `_shared/` with a stable contract for Phase 2 HOOK expert consumption.

## What Was Built

### Task 1: 3 platform-spec refs with identical H2 structure

- `references/platform-specs-douyin.md` (202 lines) — For You 算法漏斗, 男频/女频 二元明显, 5 平台专属红线 (引流外部/医疗虚假/金融诱导/标题党/版权), 平台抽成 30% *estimated*, 男频爆款公式 (战神/赘婿/修仙/重生) + 女频爆款公式 (豪门/闺蜜/替身/重生), 黄金 7 秒完播率断崖观察
- `references/platform-specs-kuaishou.md` (211 lines) — 发现页+关注页双轨分发, 老铁文化+私域流量, 草根共鸣/家庭伦理主导 (农村逆袭/老铁义气/婆媳大战/父子代沟), 直播带货联动变现模式, 平台抽成 25-30% *estimated* + 创作者激励双轨
- `references/platform-specs-miniprogram.md` (230 lines) — 微信生态裂变 (群分享/朋友圈/公众号/视频号), 长剧集模式 (10-80 集), 双重备案 (广电总局+微信ICP+增值电信业务许可证), 小程序内购 (¥3-10/集), 付费卡点 每3集1个强卡点, 接吻 > 3 秒即风险

All 3 files share: identical header block (Source/Copyright/Last-verified: 2026-06-15/verified_date: 2026-06), identical 5 H2 sections in identical order, identical Refresh Cadence (quarterly, next 2026-09-15) + Drift Signals suffix.

### Task 2: _shared/platform-comparison.md cross-platform matrix (76 lines)

- H1 + verified header (Last-verified/verified_date: 2026-06)
- `## Summary` — 3-sentence overview of platform differentiation
- `## Matrix` — 3 rows (平台) × 4 cols (付费门槛 / 红线差异 / 备案触发 / 推荐时长) per CONTEXT D-2; each cell hyperlinks to corresponding platform-specs-*.md
- `## Platform Selection Decision Tree` — 7 content-type scenarios (男频/女频/草根/家庭/长剧/互动剧/AIGC 漫剧) with primary/secondary platform recommendation
- `## Stable Contract for Phase 2 HOOK` — documents that HOOK consumes 付费门槛 + 爆款公式 columns; commits to additive-only column policy (no rename/delete without Phase 2 sync)
- `## Refresh Cadence` + `## Drift Signals` — quarterly; all 4 artifacts bumped together
- `## Cross-References` — links to 3 platform-specs + cn-content-rules.md + viral-element-catalog.md (Plan 01-01) + glossary.md

## Commits

- `c004da815` — docs(01-02): author 3 platform-spec refs (douyin/kuaishou/miniprogram)
- `449b8e49a` — docs(01-02): author _shared/platform-comparison.md cross-platform matrix

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] verified_date header format mismatch with plan verify literal**
- **Found during:** Task 1 verification
- **Issue:** Plan `<interfaces>` (lines 84-88) showed `**verified_date:** 2026-06` (markdown bold), but plan `<verify>` (line 180) greps for `verified_date: 2026-06` (plain). The bold form `**verified_date:** 2026-06` contains asterisks between colon and space, so the grep literal fails to match.
- **Fix:** Changed header line 6 in all 3 platform-spec files from `**verified_date:** 2026-06` to plain `verified_date: 2026-06`. Kept `**Last-verified:**` bold for visual consistency. All 3 files now match both the interface intent and the verify literal.
- **Files modified:** platform-specs-douyin.md, platform-specs-kuaishou.md, platform-specs-miniprogram.md
- **Commit:** c004da815 (fix landed before commit, not a separate commit)

**2. [Rule 1 - Bug] platform-specs-douyin.md initially under 200-line threshold**
- **Found during:** Task 1 verification
- **Issue:** Initial douyin ref was 192 lines, 8 lines short of the ≥200 plan threshold.
- **Fix:** Added a `### 抖音专属算法陷阱(必须规避)` subsection under `## 爆款公式` with 5 concrete algorithm anti-patterns (重复内容判定, 完播率 vs 时长, 新号冷启动, 过度投流反噬, 互动率虚高). Strengthens COMPLI-03 (抖音 verified rules).
- **Files modified:** platform-specs-douyin.md
- **Commit:** c004da815 (fix landed before commit)

### Threat Model Mitigations Applied

All 5 mitigations from the plan's `<threat_model>` were applied:

| Threat ID | Mitigation | How Applied |
|-----------|------------|-------------|
| T-01-06 | Mark uncertain values `*estimated*` | ~20+ thresholds marked across 3 specs (分账比例, 完播率门槛, 付费转化率, etc.) |
| T-01-07 | Use placeholder 备案号 formats | All 备案 examples use `<广电网剧备案号:一类-XXXX-XXXX>` / `<ICP备案号:京ICP备XXXXXXXX号>` placeholders |
| T-01-08 | Drift Signals section | All 3 specs + matrix carry Drift Signals enumerating off-cycle triggers |
| T-01-09 | Stable Contract additive-only | `## Stable Contract for Phase 2 HOOK` in matrix documents column freeze + additive-only policy |
| T-01-10 | (accepted) | Platform Selection Decision Tree is opinionated advice, no legal repudiation risk |
| T-01-SC | (accepted) | Pure markdown, no packages installed |

## Verification Results

- [x] 3 platform spec files exist, each ≥200 lines (douyin=202, kuaishou=211, miniprogram=230)
- [x] All 3 share identical 5 H2 sections (分发规则/内容红线/付费机制/备案要求/爆款公式) in identical order
- [x] All 3 carry verified_date: 2026-06 + Last-verified: 2026-06-15 + Refresh Cadence + Drift Signals
- [x] _shared/platform-comparison.md has 3 rows × 4 cols matrix, all 3 specs hyperlinked
- [x] Stable Contract for Phase 2 HOOK present
- [x] Scanner `scripts/verify_skill_references.py` exits 0 (0 phantom references, allowlist size 77)

## Known Stubs

None. All numeric thresholds carry either a concrete value or a `*estimated*` marker; no placeholder content is wired as final output.

## Threat Flags

None. No new security-relevant surface beyond what the plan's `<threat_model>` already enumerated (T-01-06 through T-01-10). All platform rule citations are from public platform documentation (Fair Use).

## Self-Check: PASSED

**Created files verified:**
- FOUND: skills/movie-experts/compliance_marketing/references/platform-specs-douyin.md
- FOUND: skills/movie-experts/compliance_marketing/references/platform-specs-kuaishou.md
- FOUND: skills/movie-experts/compliance_marketing/references/platform-specs-miniprogram.md
- FOUND: skills/movie-experts/_shared/platform-comparison.md

**Commits verified:**
- FOUND: c004da815 (docs(01-02): author 3 platform-spec refs)
- FOUND: 449b8e49a (docs(01-02): author _shared/platform-comparison.md)
