---
phase: 01-expert-compli-legal-gate
fixed_at: 2026-06-15T14:30:00Z
review_path: .planning/phases/01-expert-compli-legal-gate/01-REVIEW.md
iteration: 1
findings_in_scope: 11
fixed: 11
skipped: 0
status: all_fixed
---

# Phase 1: Code Review Fix Report — EXPERT-COMPLI (Legal Gate)

**Fixed at:** 2026-06-15T14:30:00Z
**Source review:** `.planning/phases/01-expert-compli-legal-gate/01-REVIEW.md`
**Iteration:** 1
**Scope:** critical_warning (4 Critical + 7 Warning = 11 findings; 4 Info deferred as out-of-scope)

**Summary:**
- Findings in scope: 11
- Fixed: 11
- Skipped: 0

## Fixed Issues

### CR-01: 备案 trigger thresholds disagree across three files in the same expert

**Files modified:** `skills/movie-experts/compliance_marketing/SKILL.md`, `skills/movie-experts/compliance_marketing/references/platform-specs-douyin.md`, `skills/movie-experts/compliance_marketing/references/platform-specs-kuaishou.md`, `skills/movie-experts/compliance_marketing/references/platform-specs-miniprogram.md`
**Commit:** `deba52486`
**Applied fix:** Standardized the 真人+AIG 真人主演备案 trigger on the canonical cn-content-rules.md global value `*estimated* 10 集 / *estimated* 60 分钟`. The previous 8集/24分钟 (SKILL.md) and the 6集/30分钟 连续短剧 (network-drama program type, distinct category) values are now explicitly annotated as different classification calibers. Added a global-threshold authority note to SKILL.md §备案 触发阈值 pointing at cn-content-rules.md §备案触发矩阵 as the canonical source, with platform-specs-{N}.md §备案要求 listed for platform-specific overrides. The 3 `*estimated*` annotations in cn-content-rules.md §备案触发矩阵 (lines 108-110) are preserved per "What NOT to do" §SKILL.md:188.

### CR-02: C2PA metadata field names in SKILL.md contradict the canonical JSON-LD example in cn-content-rules.md

**Files modified:** `skills/movie-experts/compliance_marketing/SKILL.md`, `skills/movie-experts/_eval/prompts/compliance_marketing_demo.yaml`
**Commit:** `39cb1c34d`
**Applied fix:** Replaced the non-canonical `dcterms:created` / `aigc:generated` / `aigc:method` field names in SKILL.md §Key Parameters (line 78) and §AIGC Labeling Workflow step 3 (line 131), plus the compli-001 eval prompt expected field list, with the canonical `digi:source` / `digi:provenance` / `digi:ai_disclosure_present` names used by the JSON-LD example in cn-content-rules.md §隐式标识 (the file SKILL.md cites as its source of truth). The eval harness now rewards outputs that agree with the canonical ref. C2PA-compliant platform审核 systems can verify the file's metadata.

### CR-03: SKILL.md body violates its own "What NOT to do" rule — embeds `fact_store` / `mem0_search` / `cosyvoice_api` as concrete tokens

**Files modified:** `skills/movie-experts/compliance_marketing/SKILL.md`
**Commit:** `5071e46a1`
**Applied fix:** Replaced the illustrative `fact_store` / `mem0_search` mentions at SKILL.md line 48 (Role & Philosophy) and line 154 (RAG Invocation conditional) with provider-agnostic `<memory_plugin>` / `<rag_search>` placeholders, matching the file's own What NOT to do rule and the `_shared/RAG-INVOCATION-PATTERN.md` canonical pattern. The forbidden-token names remain ONLY in the What NOT to do section (line 185/188), wrapped in explicit conditional phrasing ("以本 SKILL.md 历史出现过的 ... 为反例 —— 这些只是历史警示,不允许在 body 其它任何位置复用") so they serve as historical warning examples, not direct invocations. `verify_skill_references.py --strict` still exits 0.

### CR-04: 9 dangling `cn-content-rules.md §X` cross-references across all platform-spec refs + SKILL.md

**Files modified:** `skills/movie-experts/compliance_marketing/SKILL.md`, `skills/movie-experts/compliance_marketing/references/platform-specs-douyin.md`, `skills/movie-experts/compliance_marketing/references/platform-specs-kuaishou.md`, `skills/movie-experts/compliance_marketing/references/platform-specs-miniprogram.md`
**Commit:** `0439c65ed`
**Applied fix:** Rewrote the dangling §X cross-references to point at headers that actually exist in cn-content-rules.md and viral-element-catalog.md:
- `§红线` → `§8-Category 内容审核红线 Checklist` (6 places across 3 platform-specs)
- `§备案要求 §X.N` → `§备案触发矩阵` (12 places across 3 platform-specs)
- `§AIGC 标识` → `§AI 标识办法` (3 places across 3 platform-specs)
- `§爆款元素交叉表` → `viral-element-catalog.md §Catalog` (3 places)
- `§AI 漫剧 备案 regime 触发矩阵` (SKILL.md) → `§备案触发矩阵 under ## AI 漫剧 备案 Regime`
- Also normalized short-form category refs in platform-spec 红线 tables (`§虚假宣传` → `§7 虚假宣传`, etc.) so they unambiguously resolve to `### §N <name>` headers in cn-content-rules.md.

Verified via narrow pattern-match audit: all 9 originally-flagged dangling patterns are resolved.

### WR-01: `hook_retention` listed in `related_skills` but the expert does not exist yet (Phase 2)

**Files modified:** `skills/movie-experts/compliance_marketing/SKILL.md`
**Commit:** `f13f6d87a`
**Applied fix:** Converted the frontmatter `related_skills:` from inline list `[screenplay, editor, hook_retention, style_genome, drawer]` to YAML block style and added an inline comment `# Phase 2 — pending (directory does not yet exist; edge documented at line 183)` next to `hook_retention`. The body mention at line 183 (`-> hook_retention (Phase 2)`) already documents the deferred edge in detail. The `related_skills` array contents are unchanged to preserve the stable contract for downstream consumers. YAML frontmatter parses cleanly.

### WR-02: SKILL.md §备案 trigger thresholds differ in commercial-intent wording across rows

**Files modified:** `skills/movie-experts/compliance_marketing/SKILL.md`
**Commit:** `11c697f4d`
**Applied fix:** The cn-content-rules.md 备案触发矩阵 has 5 factors (内容类型 × 集数 × 总时长 × 商业意图 × 付费机制) but SKILL.md previously dropped 付费机制. The CR-01 fix added a 付费机制 bullet row (paying to unlock any 1 episode / platform revenue-share / any form of distribution). This follow-up commit clarifies the 5-factor structure in the section header note so the factor coverage is explicit. SKILL.md §备案 触发阈值 is now consistent with the canonical cn-content-rules.md §备案触发矩阵.

### WR-03: `T-01-09` threat-model reference has no visible definition

**Files modified:** `skills/movie-experts/_shared/platform-comparison.md`
**Commit:** `0537337af`
**Applied fix:** T-01-04 and T-01-07 are explained inline at their use sites; T-01-09 was the lone unexplained threat ID. Added an inline gloss matching the existing pattern: `威胁模型 T-01-09 缓解:跨阶段 contract 漂移可能破坏下游 HOOK 消费者 —— 详见本文件 §Stable Contract for Phase 2 HOOK 节的 additive-only 政策`. The pointer to §Stable Contract for Phase 2 HOOK section gives operators the additive-only policy context.

### WR-04: `LICENSE.md` `Last-verified` and `verified_date` use different key formats than the other 6 refs

**Files modified:** `skills/movie-experts/compliance_marketing/references/LICENSE.md`
**Commit:** `5880859d1`
**Applied fix:** LICENSE.md was the only ref that bolded `verified_date:` (as `**verified_date:**`). All other refs use plain `verified_date:` to look like a YAML-ish machine-readable stamp. A scanner matching `^verified_date:` would have failed on LICENSE.md. Now consistent.

### WR-05: cn-content-rules.md claims `*estimated*` for statute citations that have verifiable public text

**Files modified:** `skills/movie-experts/compliance_marketing/references/cn-content-rules.md`
**Commit:** `3da23b821`
**Applied fix:** The `CAC Order No. 17` enumeration (`国家互联网信息办公室令 第17号`) is part of the regulation's official publication title — it is verifiable public statute, not an uncertain numeric threshold requiring estimation. Annotating it `*estimated*` undermined the ref's stated discipline of reserving `*estimated*` for unverified thresholds (file header line 9). Now uses the canonical Chinese form (`国家互联网信息办公室令 第17号`) alongside the English alias `CAC Order No. 17`. All other 16 `*estimated*` annotations in cn-content-rules.md and 4 in SKILL.md remain — they mark genuinely uncertain thresholds per the file header rule.

### WR-06: `compliance_coverage` metric "≥ 8/8 红线 categories 每集检查" is unverifiable from outputs

**Files modified:** `skills/movie-experts/compliance_marketing/SKILL.md`
**Commit:** `27f2fdab4`
**Applied fix:** The `compliance_coverage` Quality Threshold previously had no observable output field — an agent could emit "no 红线 triggered" without enumerating all 8 categories and the metric could not detect the omission. Added an explicit JSON schema sketch to §Output Format requiring 8 §N keys (`§1 政治敏感` .. `§8 版权侵权`), each with `verdict` / `evidence` / `降级方案` fields. Updated the Quality Threshold row to state: "`compliance_review.json` 必须包含全部 8 个 §N 键,缺失任一 = 自动 fail(`coverage = 已检 §N 键数 / 8`,目标 ≥ 8/8)". The metric is now mechanically verifiable from the output artifact. `verify_skill_references.py --strict` still exits 0.

### WR-07: Eval prompt `compli-005` §4 severity may be mis-stated as "context-dependent" when §4 is "🔴 一律拒绝"

**Files modified:** `skills/movie-experts/_eval/prompts/compliance_marketing_demo.yaml`
**Commit:** `530057333`
**Applied fix:** cn-content-rules.md §4 未成年人保护 is 🔴 一律拒绝 with NO 🟡 middle tier for 未成年人 as 剧情角色 entering 危险/暧昧 场景. The original compli-005 prompt invited a "clearance certificate (with stated conditions)" which contradicts §4 — both "rewrite" and "conditional-clearance" answers would look plausible to a judge, producing noisy eval scores. Rewrote the expected_outcome to require: (b) clear yes/no §4 verdict with explicit "conditional clearance NOT acceptable per §4" note; (c) explicit §4 risk enumeration (AI-generated minor faces = 🔴, 校服 + 暧昧镜头 = 🔴, 校园暴力展示 = 🔴, etc.); (d) rewrite recommendation shifting setting above 18+ threshold while preserving ≥ 70% 题材钩 strength. Aligns the eval with the canonical ref.

## Skipped Issues

None — all 11 in-scope findings were fixed.

## Post-Fix Verification

- `python3 scripts/verify_skill_references.py --strict` → **exit 0** (0 phantom references across 15 skill files; allowlist size=77)
- All 9 originally-flagged dangling §X patterns resolved (verified via narrow pattern-match audit script)
- `*estimated*` annotations: **16 remain in cn-content-rules.md** (down from 17 — only the CAC Order No. 17 verifiable-statute annotation was removed; all uncertain-threshold annotations preserved per "What NOT to do" §SKILL.md:188)
- **No** `dcterms:created` / `aigc:generated` / `aigc:method` non-canonical C2PA field names remain anywhere in the corpus
- `fact_store` / `mem0_search` / `cosyvoice_api` remain only in the "What NOT to do" section, wrapped in explicit conditional phrasing as historical warning examples (not direct invocations)
- YAML frontmatter in SKILL.md parses cleanly (`related_skills` array unchanged)
- Eval prompt YAML parses cleanly (5 prompts, compli-005 tightened)
- CN legal content accuracy is not worse than before — the CAC Order No. 17 reference now uses the canonical Chinese statute title (`国家互联网信息办公室令 第17号`) instead of the hedged English alias

## Info Findings Deferred (out of scope for default fix_scope=critical_warning)

- **IN-01:** cn-content-rules.md anchor-unfriendly headers (no immediate action — only matters if cross-refs become markdown links)
- **IN-02:** viral-element-catalog.md anchor validation CI step (additive improvement, no broken links currently)
- **IN-03:** 01-CONTEXT.md filename mismatch (planning-doc historical record; harmless)
- **IN-04:** SKILL.md §RAG Invocation missing platform-comparison.md tag (additive improvement)

---

_Fixed: 2026-06-15T14:30:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
