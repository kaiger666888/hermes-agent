---
phase: 02-expert-hook-commercial-engine
fixed_at: 2026-06-15T00:00:00Z
review_path: .planning/phases/02-expert-hook-commercial-engine/02-REVIEW.md
iteration: 1
findings_in_scope: 8
fixed: 7
resolved_by_other: 1
skipped: 0
status: all_fixed
---

# Phase 2: Code Review Fix Summary

**Fixed at:** 2026-06-15
**Source review:** `.planning/phases/02-expert-hook-commercial-engine/02-REVIEW.md`
**Iteration:** 1
**Scope:** Critical + Warning (default; 4 Info findings out of scope)

**Summary:**
- Findings in scope: 8 (2 Critical + 6 Warning)
- Fixed: 7
- Resolved by another fix: 1 (WR-05 resolved implicitly by CR-01)
- Skipped: 0
- Status: all_fixed

## Fixed Issues

### CR-01: 100% of glossary anchor links broken (109/109)

**Files modified:**
- `skills/movie-experts/hook_retention/references/three-second-hooks.md`
- `skills/movie-experts/hook_retention/references/conflict-escalation.md`
- `skills/movie-experts/hook_retention/references/paywall-design.md`
- `skills/movie-experts/hook_retention/references/vertical-pacing.md`

**Commit:** `e0a78ef9e`
**Applied fix:** Python one-pass script collapsed every `--` inside `#` anchor fragments to `-`. After fix: all 109 glossary anchor links resolve correctly (verified with custom validator).

### CR-02: HOOK composer one-directional edge undocumented

**Files modified:**
- `skills/movie-experts/hook_retention/SKILL.md`

**Commit:** `31d416664`
**Applied fix:** Added inline comment to `related_skills:` line in YAML frontmatter: `# composer is one-directional (HOOK→composer for BGM sync); composer does not reciprocate by design (CONTEXT D-7)`. Keeps composer in the list (per architecture intent) but documents the asymmetry.

### WR-01: 4 broken `#≤3s-dead-air-rule` anchors

**Files modified:**
- `skills/movie-experts/hook_retention/references/paywall-design.md` (heading rename)
- `skills/movie-experts/hook_retention/references/vertical-pacing.md` (4 anchor + prose refs)

**Commit:** `f6f8a23f2`
**Applied fix:** Option (a) — renamed `### ≤3s Dead Air Rule` heading to `### 3-Second Dead Air Rule` (cleaner). Updated all 4 link anchors in vertical-pacing.md to `#3-second-dead-air-rule`, and 4 prose `§≤3s Dead Air Rule` references to `§3-Second Dead Air Rule`.

### WR-02: Path typo double-slash

**Files modified:**
- `skills/movie-experts/hook_retention/references/three-second-hooks.md`

**Commit:** `17593d897`
**Applied fix:** Replaced `../../../..//.planning` with `../../../../.planning` (line 269).

### WR-03: Hanzi typo 暴力血辛 → 暴力血腥

**Files modified:**
- `skills/movie-experts/_eval/prompts/hook_retention_demo.yaml`

**Commit:** `d7100d4a4`
**Applied fix:** Replaced `暴力血辛` (spicy/bitter — not a word) with `暴力血腥` (blood/gore — the canonical §2 红线 category name, consistent with 5+ other repo occurrences).

### WR-04: Invented 90% BGM-sync KPI

**Files modified:**
- `skills/movie-experts/hook_retention/SKILL.md`

**Commit:** `cf8437989`
**Applied fix:** Option (b) — replaced `BGM coupled_beat 同步率 ≥ 90% *estimated*` with delegation language pointing to `references/paywall-design.md §BGM-Driven Sync`, noting that quantitative measurement is deferred to Phase 6. The 90% threshold appeared nowhere in canonical sources.

### WR-06: hook-001 pace rule misstatement

**Files modified:**
- `skills/movie-experts/_eval/prompts/hook_retention_demo.yaml`

**Commit:** `b846ad7e6`
**Applied fix:** Changed `≤ 1.5s avg shot length` (ceiling) to `average shot length ≈ 1.5s; ~60 cuts per 90s episode` (matches canonical paywall-design.md §1.5x Pace Rule — the 60-cuts-per-90s derivation treats 1.5s as the average, not the ceiling).

## Resolved by Another Fix

### WR-05: 5 intra-doc §1.5x Pace Rule references in vertical-pacing.md

**Resolution:** Resolved implicitly by CR-01 (commit `e0a78ef9e`). The finding noted that vertical-pacing.md uses anchor-text like `§1.5x Pace Rule` referring to "its own body — but no `## 1.5x Pace Rule` heading exists in vertical-pacing.md". However, inspection of all 5 references (lines 22, 31, 41, 49, 179, 223) shows they are **link-style references** of the form `[`paywall-design.md`](./paywall-design.md#15x-pace-rule) §1.5x Pace Rule` — they point to paywall-design.md, not to an intra-doc heading. The underlying problem was that the anchor mechanism was broken (CR-01's `--` vs `-` issue). After CR-01, all 5 link references now resolve correctly to `paywall-design.md#15x-pace-rule` (GitHub's algorithm lowercases `### 1.5x Pace Rule`, strips the `.`, and replaces spaces with hyphens → `#15x-pace-rule`).

Validation confirms: 240 `.md` anchor links checked, 0 broken.

No separate commit required.

## Validation Results

| Check | Result |
|-------|--------|
| `python3 scripts/verify_skill_references.py --strict` | exit 0 — 0 phantom refs, allowlist size=77 |
| Custom anchor validator (240 links across 5 files) | 0 broken |
| YAML frontmatter parse (hook_retention_demo.yaml) | valid |
| Markdown heading consistency | all §-references resolve to existing headings |

## Out of Scope

The following Info-tier findings were NOT addressed (default scope = critical + warning only):

- IN-01: conflict-escalation.md "2-3 示例" → "3 示例" heading cleanup
- IN-02: `verified_date:` ambiguous placement outside YAML frontmatter
- IN-03: SKILL.md inconsistent compliance_marketing catalog path naming
- IN-04: hook_retention_demo.yaml path-correctness meta-note placement

These are cosmetic / readability concerns only and do not affect correctness.

---

_Fixed: 2026-06-15_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
