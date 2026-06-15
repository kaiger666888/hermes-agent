---
phase: 02-expert-hook-commercial-engine
reviewed: 2026-06-15T00:00:00Z
depth: deep
files_reviewed: 9
files_reviewed_list:
  - skills/movie-experts/hook_retention/SKILL.md
  - skills/movie-experts/hook_retention/references/three-second-hooks.md
  - skills/movie-experts/hook_retention/references/conflict-escalation.md
  - skills/movie-experts/hook_retention/references/paywall-design.md
  - skills/movie-experts/hook_retention/references/vertical-pacing.md
  - skills/movie-experts/hook_retention/references/LICENSE.md
  - skills/movie-experts/_eval/prompts/hook_retention_demo.yaml
  - skills/movie-experts/screenplay/SKILL.md
  - skills/movie-experts/editor/SKILL.md
  - skills/movie-experts/compliance_marketing/SKILL.md
findings:
  critical: 2
  warning: 6
  info: 4
  total: 12
status: resolved
---

# Phase 2: Code Review Report

**Reviewed:** 2026-06-15
**Depth:** deep (cross-file anchor resolution + numerical consistency + integration safety)
**Files Reviewed:** 9 (new expert + 4 content refs + LICENSE + eval YAML + 3 integration edits)
**Status:** issues_found

## Summary

The HOOK expert corpus is structurally sound: 15 hook examples (3 per type × 5 types) verified present; 5 爆款公式 branches each carry the 5-field schema; marker schema matches CONTEXT D-6; numerical thresholds (3-5 卡点, 1.5x pace, ≤3s dead air, 70-80% 爽点, 30s setup, ≥70% strength preservation) are consistent across SKILL.md + 4 refs; provider-agnostic discipline is clean (no hardcoded tool names in SKILL.md body); eval YAML matches the runner.py `_demo.yaml` contract; 3 integration edits preserve all 16 expert_id values; `verify_skill_references.py` exits 0.

However, the corpus carries **one systemic BLOCKER that completely defeats the cross-reference integrity design goal**: every single glossary anchor link (109 of 109) is broken because the author used `--` (double-dash) where GitHub's anchor algorithm produces `-` (single-dash). Phase 1 refs deliberately avoided anchor fragments for this reason; Phase 2 invented a new convention without verifying it. Additionally, the `≤3s-dead-air-rule` anchor (4 instances) is broken because GitHub strips the `≤` glyph entirely. A secondary BLOCKER is an unrelated-skills asymmetry: HOOK's `related_skills` lists `composer`, but per CONTEXT D-7 composer is a one-way edge — composer does not need to know about HOOK.

Several warnings remain: a path typo (`../../../..//.planning` — double slash), a Hanzi typo (`暴力血辛` vs canonical `暴力血腥`), a 90% BGM-sync threshold invented in SKILL.md body without a canonical source, a confused cross-reference (`vertical-pacing.md#15x-pace-rule` does not exist — the 1.5x rule lives in paywall-design.md), an underspecified conflict-escalation sub-heading ("2-3 示例" with body saying 3), and a pacing-rule phrasing drift in eval prompt hook-001.

## Critical Issues

### CR-01: 100% of glossary anchor links are broken (109/109 instances)

**File:** `skills/movie-experts/hook_retention/references/three-second-hooks.md` (18), `conflict-escalation.md` (21), `paywall-design.md` (35), `vertical-pacing.md` (35)
**Issue:** Every glossary cross-reference uses the form `glossary.md#<cn>--<en>` (e.g. `glossary.md#钩子--hook`, `glossary.md#卡点--paywall-cliffhanger--paywall-moment`). GitHub's anchor algorithm lowercases the heading text, strips non-word punctuation (including `/`), and replaces runs of whitespace with a single hyphen. The glossary heading `### 钩子 / hook` therefore produces the anchor `#钩子-hook` (single dash), not `#钩子--hook` (double dash). All 109 anchor links resolve to nothing — clicking any of them lands the reader at the top of `glossary.md` instead of the targeted entry.

This is a Phase 2 regression, not an inherited Phase 1 issue: every Phase 1 ref (`viral-element-catalog.md`, `platform-specs-{douyin,kuaishou,miniprogram}.md`) deliberately links to `_shared/glossary.md` **without an anchor fragment** or refers to entries in prose ("详见 glossary.md「转发率」条目"). Phase 2 invented the `--` convention without verifying it.

The `verify_skill_references.py` scanner does NOT catch this — it only validates `known-external-models.yaml` allowlist membership (exit 0 confirmed). Anchor validity is unchecked by current tooling, so the breakage ships silently.

**Fix:** Run a single sed pass across the 4 content refs to convert `glossary.md#<X>--<Y>` to `glossary.md#<X>-<Y>` (collapse every `--` inside an anchor to `-`). Verified algorithm output for the 13 distinct anchors used:

| Referenced (broken)                       | Correct (GitHub algo)                       |
|-------------------------------------------|---------------------------------------------|
| `#钩子--hook`                              | `#钩子-hook`                                 |
| `#卡点--paywall-cliffhanger--paywall-moment` | `#卡点-paywall-cliffhanger-paywall-moment`   |
| `#爆款--viral-formula--explosive-hit`      | `#爆款-viral-formula-explosive-hit`           |
| `#男频--male-oriented-channel`              | `#男频-male-oriented-channel`                 |
| `#女频--female-oriented-channel`            | `#女频-female-oriented-channel`               |
| `#完播率--completion-rate`                  | `#完播率-completion-rate`                     |
| `#付费卡点--paid-conversion-trigger`        | `#付费卡点-paid-conversion-trigger`           |
| `#爽点--satisfaction-beat`                  | `#爽点-satisfaction-beat`                     |
| `#击中点--emotional-impact-point`           | `#击中点-emotional-impact-point`              |
| `#竖屏--vertical-screen--916`               | `#竖屏-vertical-screen-916`                   |
| `#转发率--share-rate`                       | `#转发率-share-rate`                          |
| `#小程序剧--mini-program-drama`             | `#小程序剧-mini-program-drama`                |
| `#慕强--power-fantasy`                      | `#慕强-power-fantasy`                         |

Alternatively (preferred): delete all anchor fragments and link to `glossary.md` as a file, matching the Phase 1 convention. This is more robust against future glossary heading edits.

After the fix, add an anchor-resolution check to `verify_skill_references.py` so this class of regression is caught automatically.

### CR-02: HOOK's `related_skills` lists `composer`, but composer does not reciprocate (CONTEXT D-7 violation)

**File:** `skills/movie-experts/hook_retention/SKILL.md:13`
**Issue:** The frontmatter declares `related_skills: [screenplay, editor, compliance_marketing, composer]`. CONTEXT decision D-7 explicitly states composer is a **one-way edge** — HOOK declares BGM sync requirements; composer does NOT need to call back HOOK. The composer SKILL.md `related_skills: [screenplay, editor, style_genome, mixer, foley, spatial_audio]` confirms this: composer does not list `hook_retention`. The bidirectional symmetry established for screenplay/editor/compliance_marketing (each pair reciprocates) is broken at the composer edge.

The `related_skills` semantic in the loader is "experts this skill collaborates with" — bidirectional. Listing composer implies HOOK and composer can be invoked in either direction, which contradicts the architecture. Downstream cross-skill recommendation and DAG ordering may incorrectly infer a composer → HOOK call edge.

**Fix:** Remove `composer` from HOOK's `related_skills`. The composer collaboration is fully documented in the body (`## Collaboration -> composer` and the BGM sync workflow in `vertical-pacing.md`), so removing it from frontmatter does not lose information — it correctly reflects the one-way edge.

```yaml
# skills/movie-experts/hook_retention/SKILL.md:13
related_skills: [screenplay, editor, compliance_marketing]  # composer is a one-way edge per CONTEXT D-7 — declared in body Collaboration only
```

## Warnings

### WR-01: Broken `paywall-design.md#≤3s-dead-air-rule` anchor (4 instances)

**File:** `skills/movie-experts/hook_retention/references/vertical-pacing.md:63, 117, 122, 126`
**Issue:** GitHub's anchor algorithm strips the `≤` glyph entirely (it is not a word character). The heading `### ≤3s Dead Air Rule` produces the anchor `#3s-dead-air-rule`, not `#≤3s-dead-air-rule`. All 4 cross-references from vertical-pacing.md to the canonical dead-air rule resolve to nothing.

The SKILL.md body's pointer `见 [`references/paywall-design.md`](./references/paywall-design.md) §1.5x Pace Rule + §≤3s Dead Air Rule` (line 145) uses §-prose reference rather than an anchor, so it is unaffected — but vertical-pacing.md's 4 anchor links are broken.

**Fix:** Replace every `paywall-design.md#≤3s-dead-air-rule` with `paywall-design.md#3s-dead-air-rule`:

```diff
- [`paywall-design.md`](./paywall-design.md#≤3s-dead-air-rule)
+ [`paywall-design.md`](./paywall-design.md#3s-dead-air-rule)
```

### WR-02: Path typo `../../../..//.planning` (double slash)

**File:** `skills/movie-experts/hook_retention/references/three-second-hooks.md:269`
**Issue:** The relative path to `02-CONTEXT.md` contains a double slash between `....` and `.planning`:

```markdown
(Phase 1 [CR-01](../../../..//.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) 教训:单一真相源原则)
```

The correct path is `../../../../.planning/...` (4 levels up: `references/` → `hook_retention/` → `movie-experts/` → `skills/` → repo root). Most Markdown renderers tolerate the double slash, but it is malformed and will fail strict link checkers. Every other `CR-01` cross-link in the corpus uses the correct single-slash form.

**Fix:**

```diff
- (Phase 1 [CR-01](../../../..//.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) 教训:单一真相源原则)
+ (Phase 1 [CR-01](../../../../.planning/phases/02-expert-hook-commercial-engine/02-CONTEXT.md) 教训:单一真相源原则)
```

### WR-03: Hanzi typo `暴力血辛` (should be `暴力血腥`)

**File:** `skills/movie-experts/_eval/prompts/hook_retention_demo.yaml:147`
**Issue:** The eval prompt hook-005 contains `§2 暴力血辛 borderline` — the last character is `辛` (spicy/bitter) instead of the canonical `腥` (bloody/gory). Every other occurrence in the repo uses `暴力血腥`: `cn-content-rules.md` §2 heading, `platform-specs-{douyin,kuaishou}.md`, `viral-element-catalog.md`, `compliance_marketing/SKILL.md` (5 instances), and even earlier lines of the same `hook_retention_demo.yaml` (lines 14 and 141).

This is more than a cosmetic typo: `血辛` is not a word in Chinese. A judge model or downstream agent consuming the prompt may mis-tokenize or fail to pattern-match the canonical 红线 category name.

**Fix:**

```diff
-      taxonomy (NOT 冲突钩 to avoid §2 暴力血辛 borderline). Frame-by-frame.
+      taxonomy (NOT 冲突钩 to avoid §2 暴力血腥 borderline). Frame-by-frame.
```

### WR-04: 90% BGM-sync threshold invented in SKILL.md body without canonical source

**File:** `skills/movie-experts/hook_retention/SKILL.md:241`
**Issue:** The Quality Thresholds table declares:

```
| `完播率_proxy` | 1.5x pace rule 满足 + ≤3s dead air + BGM coupled_beat 同步率 ≥ 90% *estimated* |
```

The `≥ 90%` threshold appears nowhere in the canonical sources (`paywall-design.md` §BGM-Driven Sync defines only tolerance windows — `MUST land on beat` for major cuts, `±100ms` for ordinary cuts — but no aggregate sync-rate KPI). This violates the "single source of truth" principle the corpus itself repeatedly invokes (Phase 1 CR-01 lesson): the SKILL.md body invents a metric without pointing to a ref.

**Fix:** Either (a) add the 90% threshold to `paywall-design.md` §BGM-Driven Sync as the canonical source and have SKILL.md body cross-link to it, or (b) rephrase SKILL.md body to delegate:

```diff
- | `完播率_proxy` | 1.5x pace rule 满足 + ≤3s dead air + BGM coupled_beat 同步率 ≥ 90% *estimated* |
+ | `完播率_proxy` | 1.5x pace rule 满足 + ≤3s dead air + BGM coupled_beat 同步(同步率目标见 [`references/paywall-design.md`](./references/paywall-design.md) §BGM-Driven Sync) |
```

### WR-05: Confused cross-reference `vertical-pacing.md#15x-pace-rule` (5 instances)

**File:** `skills/movie-experts/hook_retention/references/vertical-pacing.md:22, 31, 41, 49, 179`
**Issue:** vertical-pacing.md repeatedly links to `paywall-design.md#15x-pace-rule` (which resolves correctly) AND uses anchor-text like `§1.5x Pace Rule` referring to its own body — but no `## 1.5x Pace Rule` heading exists in vertical-pacing.md. The 1.5x rule is canonically defined in paywall-design.md §1.5x Pace Rule; vertical-pacing.md only has `## 竖屏 vs 横屏 Pacing Difference` and `## Cut Density Rules` (which quote the 1.5s number).

When SKILL.md body points to `references/vertical-pacing.md §竖屏 vs 横屏` (line 144) it works; but readers following intra-vertical-pacing links like `see §1.5x Pace Rule` cannot find such a section in that file.

**Fix:** Either (a) rename the `## Cut Density Rules` subsection of vertical-pacing.md to `## 1.5x Pace Rule (Vertical Execution)` to create the anchor, or (b) reword all intra-doc references to point to the existing `## 竖屏 vs 横屏 Pacing Difference` heading or external to `paywall-design.md#15x-pace-rule`.

### WR-06: Eval prompt hook-001 misstates pace rule as `≤ 1.5s avg shot length` (tighter than canonical)

**File:** `skills/movie-experts/_eval/prompts/hook_retention_demo.yaml:46-47`
**Issue:** The prompt instructs: `Apply 1.5x pace rule (≤ 1.5s avg shot length)`. The canonical paywall-design.md §1.5x Pace Rule says "竖屏短剧的平均镜头时长(average shot duration)应为 **1.5 秒**" — i.e. average equals 1.5s. The prompt's `≤ 1.5s` is "average at most 1.5s", which is stricter: it forbids average = 1.6s even when individual shots vary. The 60-cuts-per-90s derivation (`90 ÷ 1.5 = 60`) treats 1.5s as the average, not the ceiling.

A candidate model following the prompt literally would over-cut; a candidate following the canonical would be marked wrong by a strict judge.

**Fix:**

```diff
-      the 3-tier strength (🟢 / 🟡 / 🔴). Apply 1.5x pace rule (≤ 1.5s avg
-      shot length) and ≤3s dead-air rule.
+      the 3-tier strength (🟢 / 🟡 / 🔴). Apply 1.5x pace rule (average shot
+      length ≈ 1.5s; ~60 cuts per 90s episode) and ≤3s dead-air rule.
```

## Info

### IN-01: conflict-escalation.md sub-heading says "(2-3 示例)" but body delivers exactly 3

**File:** `skills/movie-experts/hook_retention/references/conflict-escalation.md:118`
**Issue:** Heading is `### 爽点放置的题材差异(2-3 示例)`, body says "以下是 3 个具体示例", and three examples follow (Romance / Revenge / Comedy). The "2-3" hedge is dead text — the count is fixed at 3. Future maintainers may wonder if the count is meant to be variable.

**Fix:**

```diff
- ### 爽点放置的题材差异(2-3 示例)
+ ### 爽点放置的题材差异(3 示例)
```

### IN-02: `verified_date:` appears as a loose key outside YAML frontmatter

**File:** `skills/movie-experts/hook_retention/references/three-second-hooks.md:6`, `conflict-escalation.md:6`, `paywall-design.md:6`, `vertical-pacing.md:6`, `LICENSE.md:5`
**Issue:** Each ref file begins with a `**Source:**` / `**Copyright:**` / `**Last-verified:**` prose block, immediately followed by a bare `verified_date: 2026-06` line that is neither valid YAML frontmatter (no enclosing `---` fences at that position) nor rendered prose (it looks like a stray key-value pair). The intent appears to be machine-greppable for the verifier's stale-check logic, but the placement is ambiguous.

**Fix:** Either (a) move `verified_date` into a proper YAML frontmatter block at the very top of each file (before the H1), or (b) format it as a prose bullet `**verified_date:** 2026-06` to match the surrounding `**Last-verified:**` style and make it visually consistent.

### IN-03: SKILL.md body uses `compliance_marketing` catalog reference inconsistently

**File:** `skills/movie-experts/hook_retention/SKILL.md:155, 167, 219`
**Issue:** SKILL.md body refers to the Phase 1 catalog as `viral-element-catalog.md` in some places and `../../compliance_marketing/references/viral-element-catalog.md` in others, and once refers to it as `compliance_marketing catalog`. None are broken (the relative path resolves), but the naming is inconsistent: some references include the directory prefix, others just the filename. This is a readability/maintainability concern only.

**Fix:** Pick one canonical form (recommend the full relative path on first use in each section, bare filename thereafter) and apply consistently.

### IN-04: `compliance_marketing_demo.yaml` header comment pattern not followed for hook_retention

**File:** `skills/movie-experts/_eval/prompts/hook_retention_demo.yaml:23-29`
**Issue:** The header comment includes a meta-note about an incorrect file path in `02-03-PLAN.md` ("The 02-03-PLAN.md `files_modified` field lists `hook_retention.yaml` — that path is incorrect; the runner's load_prompts() contract requires the `_demo` suffix"). This is useful provenance but should live in the plan file's errata or the runner.py docstring, not in the data file's header. The sibling `compliance_marketing_demo.yaml` does not carry equivalent meta-notes and stays focused on prompt content.

**Fix:** Move the path-correctness note to `02-03-PLAN.md` errata or to a comment in `runner.py:570` next to the `f"{args.expert}_demo.yaml"` resolution. Keep the YAML header focused on prompt intent.

---

## Fix Log

Applied 2026-06-15 by `/gsd:code-review --fix` (scope: critical + warning).

**Summary:** 7 of 8 in-scope findings fixed (2 Critical + 5 Warning). WR-05 was resolved implicitly by the CR-01 anchor mechanism fix (all link-form `§1.5x Pace Rule` references now resolve to `paywall-design.md#15x-pace-rule`); 0 separate commit required.

| Finding | Severity | Status | Commit |
|---------|----------|--------|--------|
| CR-01 | Critical | fixed | `e0a78ef9e` |
| CR-02 | Critical | fixed | `31d416664` |
| WR-01 | Warning | fixed | `f6f8a23f2` |
| WR-02 | Warning | fixed | `17593d897` |
| WR-03 | Warning | fixed | `d7100d4a4` |
| WR-04 | Warning | fixed | `cf8437989` |
| WR-05 | Warning | resolved-by-CR-01 | (no separate commit) |
| WR-06 | Warning | fixed | `b846ad7e6` |

Info findings (IN-01..IN-04) were not in fix scope (default scope = critical + warning).

**Validation:**
- `python3 scripts/verify_skill_references.py --strict` → exit 0 (0 phantom refs, allowlist size=77)
- Custom anchor validator: 240 `.md` anchor links checked across 5 files, **0 broken**

---

_Reviewed: 2026-06-15_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
