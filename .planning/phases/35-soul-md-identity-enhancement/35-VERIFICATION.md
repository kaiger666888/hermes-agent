---
phase: 35-soul-md-identity-enhancement
verified: 2026-06-25T16:10:00Z
status: human_needed
score: 4/4 must-haves verified (structural); 2 SC require runtime observation
overrides_applied: 0
human_verification:
  - test: "Issue an AIGC immediate-execution prompt from hermes-agent (e.g., 'draw a cat' or 'run queue status') and confirm it routes to local AIGC skill execution rather than being answered as plain LLM chat"
    expected: "Response invokes a local skill (skills/autonomous-ai-agents/* or skills/movie-experts/*) or reports skill-not-found; NOT a free-form LLM answer to the trigger token"
    why_human: "SC #1 explicitly requires routing behavior 'observable on test prompts' — runtime agent invocation required; grep cannot verify behavioral routing"
  - test: "Issue a cognitive-class prompt (e.g., '帮我设计一个剧本' or '记住这个角色') and a default-class prompt (e.g., '今天天气怎么样') from hermes-agent"
    expected: "Cognitive prompt routes to skill-discovery / mem0 / curator surface; default prompt routes to configured LLM chat"
    why_human: "SC #2 requires runtime observation of routing split between cognitive and default classes; cannot be exercised without launching a hermes conversation"
---

# Phase 35: SOUL.md Identity Enhancement Verification Report

**Phase Goal:** Hermes-agent's `~/.hermes/SOUL.md` carries openclaw's AIGC routing intelligence (immediate-execution / cognitive / expert-management / default routes), adapted to hermes trigger modes, while preserving the existing hermes default SOUL content byte-for-byte in its original section.
**Verified:** 2026-06-25T16:10:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth (from ROADMAP SC) | Status | Evidence |
| --- | ----------------------- | ------ | -------- |
| 1   | User issuing an AIGC immediate-execution command sees it route to local execution per integrated openclaw rules | ⚠️ STRUCTURE-VERIFIED / RUNTIME-HUMAN | `~/.hermes/SOUL.md` contains `### 即时执行命令` section listing all 6 tokens (`draw`/`video`/`tts`/`run`/`status`/`queue`) with `Routes to: local AIGC skill execution`. File loaded by `agent/prompt_builder.py`. Behavioral observation requires live agent invocation. |
| 2   | User issuing a cognitive-class command routes to MCP per integrated rules; default-class prompts still go to LLM | ⚠️ STRUCTURE-VERIFIED / RUNTIME-HUMAN | `~/.hermes/SOUL.md` contains `### 认知类命令` (5 sub-routes mapped to skill-discovery/mem0/curator) and `### 默认` (routes to configured LLM). Routing rules well-formed. Behavioral split requires runtime test. |
| 3   | `~/.hermes/SOUL.md` preserves original hermes-default content byte-for-byte; openclaw-origin rules tagged with source + date | ✓ VERIFIED | Pre-H2 content is the original Hermes Nous-Research identity paragraph (verified via `awk '/^## /{p=0} p'` → 515 bytes ending with "...exploration and investigations."). 9 occurrences of `openclaw 迁移` and 10 occurrences of `2026-06-25` (both ≥ 5 required). H2 header `## openclaw 迁移规则 (Source: openclaw SOUL.md, migrated 2026-06-25)` demarcates openclaw-origin content. |
| 4   | Original openclaw SOUL.md preserved verbatim at backup path; transformation note records where each openclaw rule landed | ✓ VERIFIED | `cmp ~/.openclaw/SOUL.md ~/.hermes/SOUL.md.openclaw-backup-2026-06-25` returns 0 (identical, 975 bytes both sides, mtime `5月 12 14:15` preserved). Transformation note `.planning/phases/35-soul-md-identity-enhancement/35-01-TRANSFORMATION-NOTE.md` has dedicated Sections 2-6 covering identity statement, 6 immediate-execution tokens, 5 cognitive MCP routes, 1 expert command, 1 default route — each with explicit Fate (integrated / adapted / dropped). |

**Score:** 4/4 truths structurally verified; 2 require runtime human verification

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `~/.hermes/SOUL.md` (operator-state) | Integrated file with original Hermes identity + 4 openclaw routing categories adapted to hermes | ✓ VERIFIED | 4519 bytes; 515-byte Hermes identity preserved as opening paragraph; 8 trigger groups across 4 H3 categories; source-tagged (9× `openclaw 迁移`, 10× `2026-06-25`); `GLM-4-flash` absent; `你是"手"` framing absent |
| `~/.hermes/SOUL.md.openclaw-backup-2026-06-25` (operator-state) | Verbatim backup of `~/.openclaw/SOUL.md` | ✓ VERIFIED | 975 bytes, mtime preserved, `cmp` returns 0 against source |
| `.planning/phases/35-soul-md-identity-enhancement/35-01-TRANSFORMATION-NOTE.md` (repo-commit) | Audit trail documenting fate of each openclaw rule | ✓ VERIFIED | 8 sections covering baseline correction, identity (dropped), immediate-execution (6 tokens integrated+adapted), cognitive (5 routes integrated+adapted), expert (integrated+adapted), default (integrated+adapted, GLM-4-flash dropped), operator/repo split, SC traceability. Committed at `0191f5589`. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `~/.hermes/SOUL.md` | hermes agent runtime | `agent/prompt_builder.py` SOUL.md loader (per CLAUDE.md §"Prompt builder") | ✓ WIRED | SOUL.md is the canonical operator-identity file loaded at conversation start; no code change required for integrated rules to take effect |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Backup file identical to source | `cmp ~/.openclaw/SOUL.md ~/.hermes/SOUL.md.openclaw-backup-2026-06-25` | exit 0 | ✓ PASS |
| Hermes identity paragraph preserved | `awk '/^## /{p=0} p{print}' ~/.hermes/SOUL.md` | "You are Hermes Agent, an intelligent AI assistant created by Nous Research..." (515 bytes) | ✓ PASS |
| Source attribution present | `grep -c "openclaw 迁移" ~/.hermes/SOUL.md` | 9 (≥ 5 required) | ✓ PASS |
| Date attribution present | `grep -c "2026-06-25" ~/.hermes/SOUL.md` | 10 (≥ 5 required) | ✓ PASS |
| All 4 routing categories present | `grep -E "即时执行\|认知\|专家管理\|默认" ~/.hermes/SOUL.md` | 4 H3 headers matched | ✓ PASS |
| GLM-4-flash genericized | `! grep -q "GLM-4-flash" ~/.hermes/SOUL.md` | absent | ✓ PASS |
| 手/脑 two-agent framing dropped | `! grep -q '你是"手"' ~/.hermes/SOUL.md` | absent | ✓ PASS |
| Transformation note committed | `git log --oneline \| grep 0191f5589` | found: `docs(35): SOUL.md identity enhancement — transformation note (SOUL-01..03)` | ✓ PASS |
| Runtime routing on test prompts | (requires live agent invocation) | not run | ? SKIP — routed to human verification |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| SOUL-01 | 35-01 | openclaw AIGC routing rules extracted + integrated into `~/.hermes/SOUL.md` WITHOUT overwriting hermes defaults | ✓ SATISFIED | Original Hermes identity paragraph preserved byte-for-byte (additive integration); all 4 openclaw routing categories present in integrated file |
| SOUL-02 | 35-01 | Rules adapted from openclaw trigger modes (local skill / MCP) to hermes trigger modes; source + date explicitly tagged | ✓ SATISFIED | Regex/MCP routing rewritten as natural-language skill-discovery + mem0 + curator guidance; 9 source tags + 10 date tags; `GLM-4-flash` and `mcp:hermes_*` literals adapted to hermes-native surfaces |
| SOUL-03 | 35-01 | Original openclaw SOUL.md preserved verbatim as backup; transformation note records each rule's fate | ✓ SATISFIED | `cmp` returns 0 on backup; transformation note Sections 2-6 explicitly document fate (integrated / adapted / dropped) for every openclaw element |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | — | — | — | No debt markers (TBD/FIXME/XXX), no placeholders, no hardcoded empty data in phase artifacts |

Note: The literal string `GLM-4-flash` appears in the transformation note (Sections 6 + 8) — this is **expected and correct** (audit document records what was dropped); it is absent from the operator-state `~/.hermes/SOUL.md` as required.

### Human Verification Required

**1. Immediate-execution routing on live test prompt**

**Test:** From a hermes-agent conversation, issue an AIGC immediate-execution trigger such as `draw a cat`, `run status check`, or `queue list`.
**Expected:** Response invokes a local AIGC skill (`skills/autonomous-ai-agents/*` or `skills/movie-experts/*`) or reports skill-not-found — NOT a free-form LLM answer.
**Why human:** SC #1 explicitly requires routing behavior "observable on test prompts." Structural presence of the rule is verified; behavioral routing requires launching a live agent session.

**2. Cognitive vs default routing split on live test prompts**

**Test:** From a hermes-agent conversation, issue (a) a cognitive-class prompt like `帮我设计一个剧本` or `记住这个角色设定`, and (b) a default-class prompt like `今天天气怎么样`.
**Expected:** (a) routes to skill-discovery / mem0 / curator surface; (b) routes to configured LLM chat. The two classes route differently.
**Why human:** SC #2 requires runtime observation of the cognitive/default routing split. Cannot be exercised without an active conversation.

### Gaps Summary

No structural gaps. All three repo/operator-state artifacts exist, are substantive, and are correctly wired. All three requirements (SOUL-01..03) are satisfied by the structural deliverables. All 8 automated behavioral spot-checks pass.

Two of the four roadmap Success Criteria (SC #1 and SC #2) explicitly require runtime observation of routing behavior on test prompts. These cannot be verified by grep or static inspection — they require a live hermes-agent conversation. The structural preconditions for both SC are fully met (rules present, well-formed, loaded by `prompt_builder.py`), so human verification is the gating step rather than gap closure.

Status is `human_needed` rather than `passed` per the verifier decision tree: human verification items exist, even though all structural must-haves are VERIFIED.

---

_Verified: 2026-06-25T16:10:00Z_
_Verifier: Claude (gsd-verifier)_
