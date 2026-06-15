---
phase: 01-expert-compli-legal-gate
reviewed: 2026-06-15T14:05:00Z
depth: deep
files_reviewed: 11
files_reviewed_list:
  - skills/movie-experts/compliance_marketing/SKILL.md
  - skills/movie-experts/compliance_marketing/references/cn-content-rules.md
  - skills/movie-experts/compliance_marketing/references/viral-element-catalog.md
  - skills/movie-experts/compliance_marketing/references/LICENSE.md
  - skills/movie-experts/compliance_marketing/references/platform-specs-douyin.md
  - skills/movie-experts/compliance_marketing/references/platform-specs-kuaishou.md
  - skills/movie-experts/compliance_marketing/references/platform-specs-miniprogram.md
  - skills/movie-experts/_shared/platform-comparison.md
  - skills/movie-experts/_eval/prompts/compliance_marketing_demo.yaml
  - skills/movie-experts/screenplay/SKILL.md
  - skills/movie-experts/editor/SKILL.md
  - skills/movie-experts/style_genome/SKILL.md
  - skills/movie-experts/drawer/SKILL.md
findings:
  critical: 4
  warning: 7
  info: 4
  total: 15
status: resolved
---

# Phase 1: Code Review Report — EXPERT-COMPLI (Legal Gate)

**Reviewed:** 2026-06-15T14:05:00Z
**Depth:** deep (per-file + cross-file reference tracing)
**Files Reviewed:** 11 source + 4 integration-edited sibling skills = 13 files
**Status:** issues_found

## Summary

The Phase 1 deliverable is substantively strong: the SKILL.md is bilingual and provider-agnostic in spirit, all 6 reference files carry the required Source/Copyright/Last-verified/Refresh Cadence/Drift Signals headers, the 3 platform specs share an identical 5 H2 structure, the 26 viral elements cover all 5 taxonomy types at ≥5-per-type density, the scanner (`verify_skill_references.py --strict`) exits 0, the integration to 4 sibling skills is genuinely APPEND-only (verified via `git diff HEAD~3 HEAD`), and the 5 eval prompts cover the 5 CONTEXT D-6 scenarios. The legal-caution discipline is good: every uncertain threshold is annotated `*estimated*`, fabricated 备案号 strings are explicitly forbidden (T-01-07 mitigation), and 🔴 badges never apply to 政治敏感 elements.

However, four BLOCKER-level defects require fixes before this code ships. The most serious: **three different 备案 trigger thresholds** for the same condition exist across SKILL.md / cn-content-rules.md / platform-specs-*.md, and the **C2PA metadata field names in SKILL.md disagree with the canonical JSON-LD example** in cn-content-rules.md that SKILL.md cites as its source of truth. Both defects directly contradict the SKILL.md's own Quality Threshold "platform_fit: 0 unresolved platform-specific 红线 violations" because the agent cannot reach a consistent compliance verdict when consuming its own refs. The eval prompt compli-001 hardcodes the wrong field names, meaning the eval harness will reward answers that disagree with the canonical ref.

Cross-file reference integrity is poor: 9 of 13 `cn-content-rules.md §X` cross-references are dangling — they cite section headers (`§备案要求 §X.1`, `§AIGC 标识`, `§爆款元素交叉表`, `§红线`, `§AI 标识办法`) that do not exist in cn-content-rules.md's actual H2/H3 inventory (`## AI 标识办法`, `### 显式标识`, `### 隐式标识`, `### 文本披露`, `### 备案触发矩阵`, `### §1`..`### §8`).

## Structural Findings (fallow)

No structural pre-pass was supplied with this review request. Cross-module facts below were discovered by the reviewer directly via grep/git-diff.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: 备案 trigger thresholds disagree across three files in the same expert

**File:** `skills/movie-experts/compliance_marketing/SKILL.md:84,108,186` vs `references/cn-content-rules.md:108` vs `references/platform-specs-douyin.md:104` / `platform-specs-kuaishou.md:115`
**Issue:** The "连续短剧 / 真人+AIG 备案 trigger" threshold is stated three different ways in three places, all in the same expert:

| Source | Episode threshold | Total-runtime threshold |
|--------|-------------------|--------------------------|
| `SKILL.md:84` ("真人 + AIG 混合短剧") | ≥ 8 集 | ≥ 24 分钟 |
| `SKILL.md:108` (抖音 §备案 触发) | ≥ 8 集 | ≥ 24 分钟 |
| `SKILL.md:186` (未触发理由示例) | < 8 集 | < 24 分钟 |
| `cn-content-rules.md:108` (备案触发矩阵) | ≥ 10 集 `*estimated*` | ≥ 60 分钟 `*estimated*` |
| `platform-specs-douyin.md:104` (连续短剧) | ≥ 6 集 | ≥ 30 分钟 |
| `platform-specs-kuaishou.md:115` (连续短剧) | ≥ 6 集 | ≥ 30 分钟 |

An agent that reads SKILL.md will tell a user "8 集 / 24 分钟 触发"; if it then consults cn-content-rules.md to fill in 备案 materials, it will compute "10 集 / 60 分钟". The downstream `filing_decision.json` artifact will be inconsistent depending on which ref the agent weights highest. Since 备案 false-negatives carry the legal consequence of "平台下架 + 信用扣分 + 出品方 6 个月内禁止新节目备案" (cn-content-rules.md:120), this is a load-bearing compliance correctness bug, not a documentation polish issue.

**Fix:** Pick ONE authoritative threshold and propagate it everywhere. The cn-content-rules.md matrix is the designated ground truth ("所有下游合规检查必须以本文件 §1..§8 红线为唯一来源", line 9). Reconcile by either:
(a) Update SKILL.md:84, :108, :186 to read `≥ 10 集 / ≥ 60 分钟` and `≥ 6 集 / ≥ 30 分钟` for 连续短剧 (the platform-spec value, which is broader than the 真人+AIG row in cn-content-rules.md — they are different categories and must be labelled distinctly), OR
(b) Reconcile platform-specs-douyin.md:104 and platform-specs-kuaishou.md:115 to align with cn-content-rules.md and add an explicit note that "连续短剧 (≥ 6 集, 总时长 ≥ 30 分钟)" is the *network-drama* threshold, distinct from the "真人 + AIG 混合" threshold of 10/60. The current text conflates them.

Either way, the three `*estimated*` annotations in cn-content-rules.md:108-110 should be preserved (per "What NOT to do" §SKILL.md:188).

---

### CR-02: C2PA metadata field names in SKILL.md contradict the canonical JSON-LD example in cn-content-rules.md

**File:** `skills/movie-experts/compliance_marketing/SKILL.md:78,131` vs `references/cn-content-rules.md:53-76`
**Issue:** SKILL.md tells the agent (twice) to embed these C2PA fields:

```
dc:creator / dcterms:created / aigc:generated / aigc:method
```

But the canonical JSON-LD example in cn-content-rules.md §隐式标识 (the file SKILL.md cites as "字段示例见 cn-content-rules.md §隐式标识") uses different names:

```
dc:creator / digi:source / digi:provenance / digi:ai_disclosure_present
```

There is no `dcterms:created`, `aigc:generated`, or `aigc:method` anywhere in cn-content-rules.md. The eval prompt `compliance_marketing_demo.yaml:33-34` also hardcodes the wrong names, so the harness will reward outputs that disagree with the canonical ref and penalize outputs that get it right.

This is a contract violation. C2PA field names are machine-readable — `digi:source` is part of the C2PA digital-source type vocabulary, while `aigc:generated` is not a recognized field. Embedding wrong metadata means C2PA-compliant platform审核 systems cannot verify the file (抖音 upload channel "2025-Q4 已支持自动检测", per platform-specs-douyin.md:122). A compliance expert whose own metadata field names disagree with its own reference cannot be trusted to gate distribution.

**Fix:**
1. In `SKILL.md:78`, change:
   ```
   隐式标识字段:必须包含 `dc:creator` / `dcterms:created` / `aigc:generated` / `aigc:method` 等 C2PA 风格字段
   ```
   to:
   ```
   隐式标识字段:必须包含 `dc:creator` / `digi:source` / `digi:provenance` / `digi:ai_disclosure_present` 等 C2PA 风格字段
   ```
2. Apply the identical change to `SKILL.md:131`.
3. In `compliance_marketing_demo.yaml:33-34`, change the prompt's expected field list from `dc:creator, dcterms:created, aigc:generated, aigc:method` to `dc:creator, digi:source, digi:provenance, digi:ai_disclosure_present` so the eval harness rewards the correct names.

---

### CR-03: SKILL.md body violates its own "What NOT to do" rule — embeds `fact_store` / `mem0_search` / `cosyvoice_api` as concrete tokens

**File:** `skills/movie-experts/compliance_marketing/SKILL.md:48,154,185`
**Issue:** SKILL.md §What NOT to do (line 185) states:

> **不要硬编码 provider 专属工具名。** 严禁在 SKILL.md body 中出现 `fact_store` / `mem0_search` / `cosyvoice_api` 等具体调用

The same file then violates this rule in two places:

- Line 48: `本专家不假设客户端一定有 `fact_store` 或 `mem0_search``
- Line 154: `**若当前 runtime 中有 memory / RAG 工具**(例如 `fact_store` / `mem0_search` 或类似检索工具)`

The `verify_skill_references.py --strict` scanner exits 0 because it appears to allowlist these specific tokens (the scanner reported "0 phantom reference(s)"). But the project rule is explicit that these names must NOT appear in the body. Even if they are illustrative ("例如 ..."), they set a precedent that future model-call edits will copy. The CLAUDE.md "Anti-Patterns to Avoid" lists "Inline string-matching for API errors" as a violation for the same reason — patterns spread.

**Fix:** Replace the illustrative names with provider-agnostic placeholders consistent with the NOTE on line 163:
- Line 48: `本专家不假设客户端一定有 `<memory_plugin>` 或 `<rag_search>` 工具`
- Line 154: `**若当前 runtime 中有 memory / RAG 工具**(例如 `<memory_plugin>` / `<rag_search>` 或类似检索工具)`

Then either (a) extend `verify_skill_references.py` to also flag body mentions of `fact_store`/`mem0_search`/`cosyvoice_api` even when allowlisted as illustrative, OR (b) tighten the What NOT to do rule to "严禁在 RAG Invocation 段之外出现" if these tokens are intentionally documented as illustrations.

---

### CR-04: 9 dangling `cn-content-rules.md §X` cross-references across all platform-spec refs + SKILL.md

**File:** `skills/movie-experts/compliance_marketing/SKILL.md:107,131,132` + `references/platform-specs-douyin.md:8,43,103-106,126,180` + `references/platform-specs-kuaishou.md:8,45,114-117,137,188` + `references/platform-specs-miniprogram.md:8,48,125-128,149,205`
**Issue:** Many `§X` cross-references point at headers that do not exist in `cn-content-rules.md`. The actual H2/H3 inventory in cn-content-rules.md is:

```
## AI 标识办法 (2025-09-01)
  ### 显式标识 (Visible Mark)
  ### 隐式标识 (Metadata)
  ### 文本披露 (Script Disclosure)
## AI 漫剧 备案 Regime (2026-04-01)
  ### 备案触发矩阵
## 8-Category 内容审核红线 Checklist
  ### §1 政治敏感 ... ### §8 版权侵权
## AIGC Labeling Workflow
```

The dangling references:

| Cited in | Cited section | Actual target |
|----------|---------------|---------------|
| `platform-specs-{douyin,kuaishou,miniprogram}.md:8` (3 places) | `cn-content-rules.md §红线` | no `## 红线` H2 — actual is `## 8-Category 内容审核红线 Checklist` |
| `platform-specs-{douyin,kuaishou,miniprogram}.md:43/45/48` (3 places) | same `§红线` | same problem |
| `platform-specs-{douyin,kuaishou,miniprogram}.md:103-106/114-117/125-128` (12 places) | `§备案要求 §X.1` through `§X.6` | no `## 备案要求` H2 exists; no §X.N sub-numbering exists anywhere in cn-content-rules.md |
| `platform-specs-{douyin,kuaishou,miniprogram}.md:126/137/149` (3 places) | `cn-content-rules.md §AIGC 标识` | no `## AIGC 标识` H2 — actual is `## AI 标识办法` (missing `办` character and missing `法`) |
| `platform-specs-{douyin,kuaishou,miniprogram}.md:180/188/205` (3 places) | `cn-content-rules.md §爆款元素交叉表` | no such section exists in cn-content-rules.md |
| `SKILL.md:107` (1 place) | `cn-content-rules.md §AI 标识办法` | correct (matches `## AI 标识办法 (2025-09-01)`) |
| `SKILL.md:131` (1 place) | `cn-content-rules.md §隐式标识` | correct (matches `### 隐式标识`) |
| `SKILL.md:132` (1 place) | `cn-content-rules.md §文本披露` | correct (matches `### 文本披露`) |
| `SKILL.md:129` (1 place) | `cn-content-rules.md §AI 漫剧 备案 regime 触发矩阵` | close but actual H3 is `### 备案触发矩阵` (no "regime" in header) |

A RAG agent that takes these `§X` references literally will search cn-content-rules.md and fail to resolve them, falling back to the entire document. The §备案要求 §X.N references are particularly bad — they suggest a numbered sub-section structure that does not exist.

**Fix:** Two options:
(a) **Update the cross-references to point at actual headers.** For example, change `§备案要求 §X.1` to `§备案触发矩阵 row 1` (or `### 备案触发矩阵`); change `§AIGC 标识` to `§AI 标识办法`; change `§红线` to `§8-Category 内容审核红线 Checklist`; change `§爆款元素交叉表` to `viral-element-catalog.md §Catalog`(since the catalog itself is the cross-reference table, not a section of cn-content-rules.md).
(b) **Add the missing H2 headers to cn-content-rules.md** (e.g., add `## 备案要求` as an alias, or split the `## AI 漫剧 备案 Regime` into numbered subsections `### X.1` ... `### X.6`). This is more work but gives the agent machine-resolvable anchors.

Option (a) is preferred — it is a smaller diff and aligns with the existing actual headers.

## Warnings

### WR-01: `hook_retention` listed in `related_skills` but the expert does not exist yet (Phase 2)

**File:** `skills/movie-experts/compliance_marketing/SKILL.md:13`
**Issue:** The `related_skills` array includes `hook_retention`, but no `skills/movie-experts/hook_retention/` directory exists (verified via `ls`). The scanner `verify_skill_references.py` does NOT validate `related_skills` target existence — only model/tool name validity — so this slips through silently. CONTEXT line 28 acknowledges HOOK is Phase 2, and SKILL.md:180 explicitly says "HOOK Phase 2 将补回反向 edge". But until Phase 2 ships, every consumer of `related_skills` will see a dangling edge.

This is not strictly a bug (the contract is "leave a stable contract for HOOK" per CONTEXT line 28), but it is a quality issue: the Hermes skill loader (per CLAUDE.md "Skill File Conventions") treats `related_skills` as a DAG. A dangling target may surface as a warning in the dashboard or break cross-skill recommendation.

**Fix:** Either (a) leave the entry but add an inline annotation `hook_retention  # Phase 2 — not yet implemented` (if the YAML schema permits comments), OR (b) document the deferred edge in SKILL.md body (which it already does at line 180 — sufficient) AND confirm the Hermes skill loader tolerates a missing `related_skills` target. If the loader strictly requires existence, remove `hook_retention` from `related_skills` until Phase 2 ships and re-add it then.

---

### WR-02: SKILL.md §备案 trigger thresholds differ in commercial-intent wording across rows

**File:** `skills/movie-experts/compliance_marketing/SKILL.md:83-86`
**Issue:** The 4 trigger rules in §备案 (Filing) 触发阈值 use inconsistent commercial-intent predicates:
- Line 83 (拟人化动画): `商业意图 + 任意付费机制` — both required
- Line 84 (真人+AIG 混合): `集数 ≥ 8 或总时长 ≥ 24 分钟 + 商业意图` — size OR + commercial
- Line 85 (全 AIG): `任意商业意图即触发` — commercial only, no size gate
- Line 86 (小程序剧 加成): `除广电 备案 外,触发 微信小程序 内容 备案(双重)` — does not restate commercial gate

The cn-content-rules.md matrix (line 108-110) gives different size thresholds (see CR-01) AND adds a separate 付费机制 column (`付费解锁任何 1 集 → 触发`, `平台分账即触发`, `任何 → 触发`). SKILL.md drops this 付费机制 column entirely, even though §53 says "内容类型 × 集数 × 总时长 × 商业意图 × 付费机制" — five factors, only four of which are restated.

**Fix:** Either restore the 付费机制 column in SKILL.md §备案 触发阈值 (5-column table matching cn-content-rules.md), OR explicitly note "本节为简化摘要,完整 5-factor 矩阵见 cn-content-rules.md §备案触发矩阵". Either way, the size thresholds must match CR-01's fix.

---

### WR-03: `T-01-09` threat-model reference has no visible definition

**File:** `skills/movie-experts/_shared/platform-comparison.md:45`
**Issue:** Line 45 says "列重命名 / 列删除需在 Phase 2 与 HOOK 团队同步后方可进行(威胁模型 T-01-09 缓解)". But no `T-01-09` definition appears anywhere in the compliance_marketing corpus (verified via `grep -rn "T-01-09"`). T-01-04 and T-01-07 are referenced and at least contextually explained inline (T-01-04 = "无提权路径"; T-01-07 = "禁止编造真实备案号 字符串"). T-01-09 has no inline gloss.

**Fix:** Either (a) add an inline gloss `(威胁模型 T-01-09 缓解:跨阶段 contract 漂移可能破坏下游消费者)` or (b) point at a centralized threat-model doc if one exists in `_shared/`.

---

### WR-04: `LICENSE.md` `Last-verified` and `verified_date` use different key formats than the other 6 refs

**File:** `skills/movie-experts/compliance_marketing/references/LICENSE.md:5-6`
**Issue:** LICENSE.md uses:
```
**Last-verified:** 2026-06-15
**verified_date:** 2026-06
```
The `verified_date:` here is bold-formatted (`**verified_date:**`) like the surrounding prose. Every other ref (`cn-content-rules.md:6-7`, `viral-element-catalog.md:5-6`, all 3 platform-specs:5-6, `platform-comparison.md:5-6`) uses:
```
**Last-verified:** 2026-06-15
verified_date: 2026-06
```
where `verified_date:` is unbolded (looks like a YAML-ish machine-readable stamp).

A machine parser scanning for `^verified_date:` would fail on LICENSE.md (where the line starts with `**`).

**Fix:** In `LICENSE.md:6`, change `**verified_date:** 2026-06` to `verified_date: 2026-06` (drop the bold).

---

### WR-05: cn-content-rules.md claims `*estimated*` for statute citations that have verifiable public text

**File:** `skills/movie-experts/compliance_marketing/references/cn-content-rules.md:19`
**Issue:** Line 19 cites `网信办《人工智能生成合成内容标识办法》(CAC Order No. 17 *estimated*)`. The "CAC Order No. 17" enumeration (`国家互联网信息办公室令 第17号`) is part of the regulation's official publication title — it is not a threshold requiring estimation. Marking it `*estimated*` undermines the document's stated discipline of using `*estimated*` only for unverified numeric thresholds (line 9: "文中带 `*estimated*` 的阈值为基于公开通告的最佳推断"). A reviewer or downstream operator may distrust the entire ref if they notice a verifiable fact being hedged.

This is a low-severity accuracy issue (the regulation number IS correct), but it conflates "I'm guessing" with "this is the official title" and weakens the `*estimated*` signal's meaning.

**Fix:** Remove the `*estimated*` annotation from `CAC Order No. 17`: `网信办《人工智能生成合成内容标识办法》(国家互联网信息办公室令 第17号)`. If unsure whether Order No. 17 is correct, verify against the official 网信办 publication and either drop the number or drop the `*estimated*`.

---

### WR-06: `compliance_coverage` metric "≥ 8/8 红线 categories 每集检查" is unverifiable from outputs

**File:** `skills/movie-experts/compliance_marketing/SKILL.md:169`
**Issue:** The Quality Threshold `compliance_coverage` says "≥ 8/8 红线 categories 每集检查(不可跳过任一类)". The Output Format section (line 65) says the agent produces `compliance_review.json` with "红线扫描结果 + 风险徽章 + 降级方案 清单". But neither SKILL.md nor cn-content-rules.md specifies the JSON schema of `compliance_review.json` — specifically, whether it MUST contain 8 keys (one per §1..§8) so the metric can be checked mechanically.

Without a schema contract, an agent can produce a `compliance_review.json` that says "no 红线 triggered" without enumerating all 8 categories, and the metric cannot detect the omission.

**Fix:** Add to SKILL.md §Output Format a schema sketch, e.g.:
```
compliance_review.json:
  §1 政治敏感: { verdict: 🟢|🟡|🔴, evidence: [...] }
  §2 暴力血腥: { ... }
  ... (all 8 §N keys required)
```
And update Quality Threshold to: `compliance_review.json` MUST contain all 8 §N keys (absence = automatic fail).

---

### WR-07: Eval prompt `compli-005` §4 severity may be mis-stated as "context-dependent" when §4 is "🔴 一律拒绝"

**File:** `skills/movie-experts/_eval/prompts/compliance_marketing_demo.yaml:76-88` + `references/cn-content-rules.md:194`
**Issue:** Eval prompt compli-005 asks the agent to assess a 校园 setup with implied teen characters and "produce either a clearance certificate (with stated conditions) OR a rewrite recommendation". The wording implies the agent may issue a clearance if conditions are met.

But cn-content-rules.md §4 (line 194) classifies 未成年人 as 🔴 一律拒绝 — "未成年人作为剧情角色进入危险/暧昧场景 = 🔴" with NO 🟡 middle tier. The only allowed 降级 is rewriting the setting to 大学/职场/培训机构 (line 197). There is no path to "clearance certificate (with stated conditions)" if the characters remain teen.

The eval prompt thus creates ambiguity: a candidate answer that issues a "conditional clearance" for teen characters would be **wrong per §4**, but the prompt's "(with stated conditions)" clause invites it. This will produce noisy eval scores — both "rewrite" and "conditional-clearance" answers may look plausible to a judge.

**Fix:** Tighten the prompt to: "(c) produce a §4 verdict (🔴 一律拒绝 for teen characters per cn-content-rules.md §4) AND a rewrite recommendation that shifts the setting above the 18+ threshold (e.g., 大学, 培训机构, 职场 flashback) while preserving ≥ 70% of the original 题材钩 strength. A 'conditional clearance' for teen characters is NOT acceptable per §4". This aligns the eval with the canonical ref.

## Info

### IN-01: cn-content-rules.md uses Markdown headers that contain spaces and parentheses (anchor-unfriendly)

**File:** `skills/movie-experts/compliance_marketing/references/cn-content-rules.md:17,98,124,285`
**Issue:** H2 headers like `## AI 标识办法 (2025-09-01)` and `## AI 漫剧 备案 Regime (2026-04-01)` contain spaces, parentheses, and CJK characters. GitHub-flavored Markdown auto-generates anchors by lowercasing, replacing spaces with hyphens, and stripping most punctuation — but CJK + parentheses interaction is unreliable across renderers. Cross-file links like `[§AI 标识办法](./cn-content-rules.md#ai-标识办法-2025-09-01)` would be fragile.

Currently the cross-references are textual (not markdown links), so this is not breaking. But if a future PR converts them to links (recommended for navigation), the anchors will need testing.

**Fix:** No immediate action. If/when cross-refs become links, prefer GitHub's anchor preview tool to verify each one.

---

### IN-02: `viral-element-catalog.md` cross-references use HTML anchor names that don't match GitHub Markdown auto-generated anchors

**File:** `skills/movie-experts/compliance_marketing/references/viral-element-catalog.md:36,42,48,54,60,68,74,80,86,92,100,106,112,118,124,132,138,144,150,156,162,170,176,182,188,194`
**Issue:** Many catalog entries link to cn-content-rules.md via anchors like:
```
[§6 歧视侮辱](./cn-content-rules.md#6-歧视侮辱)
[§2 暴力血腥](./cn-content-rules.md#2-暴力血腥)
```

The actual H3 headers in cn-content-rules.md are `### §6 歧视侮辱` and `### §2 暴力血腥`. GitHub's anchor algorithm converts `### §6 歧视侮辱` to `#6-歧视侮辱` (it strips the `§` character and keeps the digit and CJK). So these anchors DO resolve correctly on GitHub. Good.

But the catalog entry for `§3 色情低俗` (line 124, 176, 194) uses `#3-色情低俗` — verify this resolves against `### §3 色情低俗` → GitHub anchor `#3-色情低俗`. Yes, resolves.

So this is actually mostly working. But because there is no automated test, a future header rename (e.g., `### §3 色情低俗` → `### §3 色情 / 低俗`) would silently break 3+ links. A CI check for markdown link integrity would prevent this.

**Fix:** Add a markdown-link-check CI step (or extend `verify_skill_references.py` to validate intra-repo markdown links).

---

### IN-03: Phase plan (`01-CONTEXT.md`) calls for `compliance_marketing.yaml` but actual file is `compliance_marketing_demo.yaml`

**File:** `.planning/phases/01-expert-compli-legal-gate/01-CONTEXT.md:92` vs `skills/movie-experts/_eval/prompts/compliance_marketing_demo.yaml`
**Issue:** CONTEXT line 92 says the new prompt file should be named `compliance_marketing.yaml`. The actual delivered file is `compliance_marketing_demo.yaml`. The eval YAML file's own header comment (line 22) justifies this: "The `_demo` suffix is the harness contract, matching animator_demo.yaml" — and `ls skills/movie-experts/_eval/prompts/` confirms `animator_demo.yaml` uses the same suffix.

So the delivered filename is CORRECT (matches harness contract), and the CONTEXT.md is the stale artifact. This is harmless (CONTEXT is a planning doc, not a runtime input), but worth flagging so future planning docs use the harness contract name.

**Fix:** Either (a) update CONTEXT.md line 92 to read `compliance_marketing_demo.yaml`, or (b) leave CONTEXT as historical record and document the `_demo` suffix convention in `_shared/SKILL-LAYOUT.md`.

---

### IN-04: SKILL.md §RAG Invocation lists only 4 memory tags, missing `_shared/platform-comparison.md`

**File:** `skills/movie-experts/compliance_marketing/SKILL.md:155-159`
**Issue:** The RAG Invocation memory-tag block lists 3 tag patterns:
```
tags="expert:compliance_marketing,domain:cn-content-rules"
tags="expert:compliance_marketing,domain:viral-element-catalog"
tags="expert:compliance_marketing,domain:platform-specs-<platform>"
```
But the §References table (line 40) lists `_shared/platform-comparison.md` as a 4th ref the agent should consult for "选台决策树" decisions. There is no `domain:platform-comparison` tag. An agent using memory/RAG retrieval via these tags would miss the comparison matrix entirely when answering "which platform should I target" questions — exactly the case compli-003 exercises.

**Fix:** Add a 4th tag pattern:
```
tags="expert:compliance_marketing,domain:platform-comparison"
```
Or note that platform-comparison.md is a synthesis of the 3 platform-spec refs and does not need its own tag (in which case this should be stated explicitly in §RAG Invocation).

---

_Reviewed: 2026-06-15T14:05:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_

## Fix Log

Applied 2026-06-15 by `gsd:code-review --fix`. All 4 Critical + 7 Warning findings fixed; 4 Info findings deferred (out of scope for default fix_scope=critical_warning).

| Finding | Severity | Status | Commit |
|---------|----------|--------|--------|
| CR-01 备案 trigger thresholds disagree across files | Critical | fixed | `deba52486` |
| CR-02 C2PA metadata field names contradict canonical JSON-LD | Critical | fixed | `39cb1c34d` |
| CR-03 SKILL.md body embeds hardcoded tool names | Critical | fixed | `5071e46a1` |
| CR-04 9 dangling §X cross-references | Critical | fixed | `0439c65ed` |
| WR-01 hook_retention referenced before Phase 2 ships | Warning | fixed | `f13f6d87a` |
| WR-02 Missing 付费机制 column in SKILL.md §备案 | Warning | fixed | `11c697f4d` |
| WR-03 T-01-09 threat-model undefined | Warning | fixed | `0537337af` |
| WR-04 LICENSE.md verified_date bold-format mismatch | Warning | fixed | `5880859d1` |
| WR-05 *estimated* mis-applied to verifiable CAC Order No. 17 | Warning | fixed | `3da23b821` |
| WR-06 compliance_coverage metric unverifiable | Warning | fixed | `27f2fdab4` |
| WR-07 compli-005 "conditional clearance" outcome violates §4 | Warning | fixed | `530057333` |

**Post-fix verification:**
- `python3 scripts/verify_skill_references.py --strict` → exit 0 (0 phantom references across 15 skill files; allowlist size=77)
- All 9 originally-flagged dangling §X patterns resolved (verified via narrow pattern-match audit)
- `*estimated*` annotations: 16 remain in cn-content-rules.md (down from 17 — only the CAC Order No. 17 verifiable-statute annotation was removed; all uncertain-threshold annotations preserved)
- No `dcterms:created` / `aigc:generated` / `aigc:method` non-canonical C2PA field names remain anywhere in the corpus
- `fact_store` / `mem0_search` / `cosyvoice_api` remain only in the "What NOT to do" section, wrapped in explicit conditional phrasing as historical warning examples (not direct invocations)
- YAML frontmatter in SKILL.md and eval prompt YAML both parse cleanly

**Info findings deferred (not in default scope):**
- IN-01: cn-content-rules.md anchor-unfriendly headers (no immediate action — only matters if cross-refs become markdown links)
- IN-02: viral-element-catalog.md anchor validation CI step (additive improvement, no broken links currently)
- IN-03: 01-CONTEXT.md filename mismatch (planning-doc historical record; harmless)
- IN-04: SKILL.md §RAG Invocation missing platform-comparison.md tag (additive improvement)
