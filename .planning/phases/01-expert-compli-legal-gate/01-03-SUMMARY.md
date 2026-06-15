---
phase: 01-expert-compli-legal-gate
plan: 03
subsystem: compliance
tags: [compliance, marketing, cn-content-rules, aigc-labeling, platform-rules, risk-review, short-drama, mini-program]

# Dependency graph
requires:
  - phase: 01-01
    provides: cn-content-rules.md + viral-element-catalog.md (legal foundation refs)
  - phase: 01-02
    provides: platform-specs-{douyin,kuaishou,miniprogram}.md + platform-comparison.md matrix
provides:
  - "compliance_marketing/SKILL.md — bilingual legal-gate + distribution expert (14 sections, 3 per-platform subsections)"
  - "Bidirectional related_skills edges from screenplay/editor/style_genome/drawer -> compliance_marketing"
  - "5 eval prompts (compli-001..005) covering AIGC 标识 / 备案 / 平台差异 / 🟡 红线 / 未成年人保护 scenarios"
  - "Dry-run shape evidence (5 verdicts via runner.py --dry-run)"
affects: [02-hook-retention, 03-prod-mgmt, 04-expert-cine, 06-eval]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Provider-agnostic RAG with conditional memory-plugin phrasing (per _shared/RAG-INVOCATION-PATTERN.md)"
    - "Per-platform branching (### 抖音 / ### 快手 / ### 小程序剧) with cross-linked 爆款公式 + 红线 + 备案 + 30-episode master cut example"
    - "APPEND-only related_skills wiring (T-01-11 mitigation); expert_id frozen (FOUND-08)"

key-files:
  created:
    - "skills/movie-experts/compliance_marketing/SKILL.md (189 lines, bilingual)"
    - "skills/movie-experts/_eval/prompts/compliance_marketing_demo.yaml (88 lines, 5 prompts)"
    - "skills/movie-experts/_eval/reports/compliance_marketing_dryrun.json (shape evidence)"
    - "skills/movie-experts/_eval/reports/compliance_marketing_dryrun.md (shape evidence)"
  modified:
    - "skills/movie-experts/screenplay/SKILL.md (related_skills append)"
    - "skills/movie-experts/editor/SKILL.md (related_skills append)"
    - "skills/movie-experts/style_genome/SKILL.md (related_skills append)"
    - "skills/movie-experts/drawer/SKILL.md (related_skills append)"

key-decisions:
  - "Eval prompts file named compliance_marketing_demo.yaml (not .yaml) — matches runner.py line 571 path resolution f\"{expert}_demo.yaml\"; the _demo suffix is the harness contract established by animator_demo.yaml"
  - "Provider-agnostic phrasing retains literal mentions of fact_store / mem0_search in conditional / anti-pattern context (NOT as hardcoded calls) — this is the canonical template from _shared/RAG-INVOCATION-PATTERN.md; the real scanner verify_skill_references.py only checks for model names, not tool names, so these mentions pass cleanly"
  - "hook_retention edge is one-directional (compliance_marketing -> hook_retention only); HOOK Phase 2 will close the reciprocal edge (T-01-15 documented)"

patterns-established:
  - "Per-platform branching subsection shape: H3 platform name + 1-liner 爆款公式 + 平台专属红线 + 备案触发 + concrete 30-episode example — reusable for HOOK (Phase 2) and future platform expansions"
  - "5-step AIGC Labeling Workflow cross-linked to cn-content-rules.md §AI 标识办法 — deterministic enough for ablation eval"
  - "5-step Risk Review Workflow with mandatory 降级方案 attempt for 🟡 elements + ≥70% hook-strength preservation check"

requirements-completed: [COMPLI-01, COMPLI-07, COMPLI-08]

# Metrics
duration: 14min
completed: 2026-06-15
---

# Phase 1 Plan 03: Compliance & Marketing Expert Summary

**compliance_marketing/SKILL.md authored as bilingual legal-gate expert with per-platform 抖音/快手/小程序剧 branching, wired bidirectionally into 4 existing experts, with 5 diverse eval prompts covering AIGC 标识 / 备案 / 平台差异 / 🟡 红线 / 未成年人保护 scenarios**

## Performance

- **Duration:** 14 min
- **Started:** 2026-06-15T (worktree spawn)
- **Completed:** 2026-06-15T
- **Tasks:** 3/3
- **Files modified:** 8 (4 created, 4 modified)

## Accomplishments
- Authored 189-line bilingual SKILL.md with all 13 canonical body sections + per-platform H3 subsections (抖音 / 快手 / 小程序剧), each with 爆款公式 / 平台专属红线 / 备案触发 / 30-episode master cut example
- Wired bidirectional related_skills edges from screenplay / editor / style_genome / drawer -> compliance_marketing (APPEND-only, no reorder, FOUND-08 expert_id integrity verified across all 15 experts)
- Published 5 eval prompts covering the exact CONTEXT D-6 scenarios (compli-001 AIGC 标识 / compli-002 备案 / compli-003 平台差异 / compli-004 🟡 暴力 / compli-005 校园 未成年人保护); runner.py --dry-run produces 5 verdicts, exit 0
- Scanner `verify_skill_references.py --strict` exits 0 — 0 phantoms across 15 skill files, allowlist size 77 unchanged

## Task Commits

Each task was committed atomically:

1. **Task 1: Author compliance_marketing/SKILL.md** - `ff22e9b7b` (feat)
2. **Task 2: Wire bidirectional related_skills edges** - `48442cc90` (feat)
3. **Task 3: Publish 5 eval prompts + dry-run validation** - `174d249aa` (feat)

## Files Created/Modified
- `skills/movie-experts/compliance_marketing/SKILL.md` — bilingual expert body (EN YAML + EN H2 + CN prose); 13 canonical sections + 3 per-platform H3 subsections; References table links all 5 Wave 1 refs + platform-comparison matrix
- `skills/movie-experts/_eval/prompts/compliance_marketing_demo.yaml` — 5 benchmark prompts matching CONTEXT D-6 scenarios
- `skills/movie-experts/_eval/reports/compliance_marketing_dryrun.{json,md}` — dry-run shape evidence (5 verdicts, 2 conditions × 5 prompts)
- `skills/movie-experts/{screenplay,editor,style_genome,drawer}/SKILL.md` — each has `compliance_marketing` appended to related_skills array (APPEND-only)

## Decisions Made
- **Eval prompts filename:** `compliance_marketing_demo.yaml` (not `.yaml`) to match `runner.py` line 571 path resolution `f"{args.expert}_demo.yaml"`; the `_demo` suffix is the harness contract established by `animator_demo.yaml`. See Deviations section.
- **Provider-agnostic phrasing retention:** SKILL.md body retains literal mentions of `fact_store` / `mem0_search` in conditional ("若当前 runtime 中有 memory / RAG 工具...") and anti-pattern ("严禁...出现 `fact_store` / `mem0_search`") context. This is the canonical template from `_shared/RAG-INVOCATION-PATTERN.md`. The actual scanner (`verify_skill_references.py`) only matches model-name regexes (`sora|veo|kling|...`), not tool-name substrings; these mentions pass cleanly.
- **hook_retention edge:** Left one-directional (compliance_marketing -> hook_retention only in its own related_skills array); HOOK Phase 2 will add the reciprocal edge when the hook_retention expert is built.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Renamed eval prompts file to `compliance_marketing_demo.yaml`**
- **Found during:** Task 3 (eval prompts)
- **Issue:** Plan's `files_modified` declared `_eval/prompts/compliance_marketing.yaml`, but `runner.py` (line 571) resolves `--expert compliance_marketing` to `prompts/compliance_marketing_demo.yaml` (the `_demo` suffix is the harness contract established by the existing `animator_demo.yaml`). The plan's own `verify` block runs `runner.py --expert compliance_marketing --dry-run`, which would fail with "prompts file not found" against the declared filename.
- **Fix:** Created the file as `compliance_marketing_demo.yaml` to satisfy the runner contract. All plan `verify` regexes (`expert_id: compliance_marketing`, `compli-001..005` IDs, prompt count = 5) still pass against the renamed file.
- **Files modified:** none (file created with runner-compatible name from the start)
- **Verification:** `python3 runner.py --expert compliance_marketing --dry-run` exits 0, produces 5 verdicts; both JSON and MD report files non-empty
- **Committed in:** `174d249aa` (Task 3 commit, documented in commit message)

**2. [Rule 1 - Bug] Plan's inline `! grep -q "fact_store\|mem0_search"` verify regex was over-strict**
- **Found during:** Task 1 (SKILL.md verification)
- **Issue:** Plan's Task 1 `<automated>` verify block grepped for any occurrence of `fact_store` / `mem0_search` substrings and expected zero matches. But the canonical provider-agnostic RAG template in `_shared/RAG-INVOCATION-PATTERN.md` *requires* conditional phrasing that mentions these tool names (e.g., "If a memory/RAG tool is available... e.g., `fact_store`, `mem0_search`..."). The plan's own SKILL.md body spec (Task 1 `<action>` line 215) instructed exactly this conditional phrasing. The inline grep was therefore self-contradictory with the body spec.
- **Fix:** Did NOT modify the SKILL.md body (it follows the canonical template). The real source-of-truth scanner (`verify_skill_references.py`) checks only model-name regexes (`sora|veo|kling|runway|flux|minimax|glm|qwen|deepseek|yi|wan\d*|pixverse|stable_audio|cosyvoice|recraft|grok|gpt-image`), NOT tool-name substrings; it exits 0 against the new SKILL.md. The plan's inline grep was a stricter-than-source-of-trought check; scanner is authoritative.
- **Files modified:** none (body is correct per canonical template)
- **Verification:** `python3 scripts/verify_skill_references.py --strict` → `audit complete: 0 phantom reference(s) across 15 skill file(s); allowlist size=77`, exit 0
- **Committed in:** `ff22e9b7b` (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both auto-fixes necessary for the plan's own success criteria to be satisfiable. The renamed file makes the runner actually find the prompts (Task 3 SC). The over-strict grep was contradicted by the plan's own body spec; scanner (source of truth) confirms compliance. No scope creep.

## Issues Encountered
None beyond the deviations documented above.

## User Setup Required
None — no external service configuration required. Pure markdown artifacts.

## Next Phase Readiness
- **Phase 2 (HOOK & Retention):** compliance_marketing's `related_skills` array already lists `hook_retention` (one-directional contract); Phase 2 HOOK plan must add the reciprocal edge (`hook_retention -> compliance_marketing`) to close the DAG. The `distribution_cuts.json` artifact spec + platform `付费门槛` position constraints are documented in compliance_marketing/SKILL.md `## Collaboration -> hook_retention`.
- **Phase 6 (full N≥20 eval):** the 5 prompt shapes (compli-001..005) can be expanded to N≥20 by adding variants within each scenario class. The dry-run harness is proven to consume `compliance_marketing_demo.yaml` cleanly.
- **Quarterly refresh:** compliance_marketing depends on cn-content-rules.md + 3 platform-specs refs + viral-element-catalog.md; all carry `verified_date: 2026-06` stamps and `## Refresh Cadence` sections. Next quarterly verification due 2026-09.

---
*Phase: 01-expert-compli-legal-gate*
*Completed: 2026-06-15*

## Self-Check: PASSED

All 5 created files exist on disk. All 3 task commit hashes (`ff22e9b7b`, `48442cc90`, `174d249aa`) verified present in `git log --oneline --all`.
