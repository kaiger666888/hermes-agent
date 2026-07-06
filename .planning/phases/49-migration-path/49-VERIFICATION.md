---
phase: 49-migration-path
verified: 2026-07-07T02:30:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 49: Migration Path — Verification Report

**Phase Goal:** 定义 Python runner 增量迁移计划 — 15 expert SKILL frontmatter → agent YAML transform + v6.0 FeedbackStore → memory-record-schema 迁移 + retained-phases allowlist
**Verified:** 2026-07-07T02:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth (ROADMAP SC) | Status | Evidence |
| --- | ------------------ | ------- | -------- |
| 1   | **SC#1:** File `04-MIGRATION-PATH.md` exists at `.planning/research/v10-orchestrator-design/` | ✓ VERIFIED | File present, **1,508 lines** (exceeds plan min_lines=800; exceeds §1.3 self-imposed 1,300 lint threshold). Created by 5 atomic task commits (d7c4cc526 + 9afa831a3 + c43c8c4a4 + 4b8c8f721 + c44723422), merged via 7cd63036f. |
| 2   | **SC#2:** 15 expert × 5-field transform 规则表完整 (75 cells, FOUND-08 preserved) | ✓ VERIFIED | §2 spans lines 233-675 (~440 lines, 19 subsections §2.0-§2.19). §2.2-§2.16 each provide a 5-row table for one expert → 15 experts × 5 fields = 75 cells. §2.17 75-cell coverage audit PASSED. All 15 expert_ids match ARCHITECTURE §2 verbatim (expert-diff via awk = identical list). §2.18 cites ARCHITECTURE §2 closing paragraph verbatim with FOUND-08 preservation + additive invariant. §2.19 15-cell edge-case summary. |
| 3   | **SC#3:** `default_invocation: skill_fallback → mcp_tool` 切换机制文档化 | ✓ VERIFIED | §3 spans lines 677-854 (~180 lines, 8 subsections §3.0-§3.7). §3.2 **12-cell failure-mode matrix** (3 failure modes × 4 transition states). §3.3 2 safe-default rules. §3.4 5-step per-agent transition path + recommended switch order (screenplay first, compliance_gate last). §3.5 FOUND-08 backward-compat anchor (6-step dispatcher routing order via `expert_id`). §3.6 14/15 standard + 1/15 special (compliance_gate `disabled` initially) + count reconciliation. §3.7 round_table_eligible consumption + mid-round state change edge case. |
| 4   | **SC#4:** Memory schema 迁移计划 (FeedbackStore → memory-record-schema + `schema_version` + dry-run per P14) | ✓ VERIFIED | §4 spans lines 856-1153 (~300 lines, 10 subsections §4.0-§4.9). §4.1 cites v6.0 `agent/feedback_store.py` ground truth (buckets/<skill_id>/<source>.jsonl + dedup/sha256-registry.jsonl + _INDEX_VERSION=1 + 7 FeedbackRecord fields). §4.2 cites Phase 45 memory-record-schema 10 mandated fields. §4.3 **17-row source→target mapping table** with edge cases. §4.4 cites `schema_version` field verbatim from `memory-record-schema.yaml` line 353 (verified line=353 in actual file). §4.5 dry-run mode with 5-metric output plan + `hermes agent memory migrate --dry-run` (7 mentions of `--dry-run`). §4.6 6 safe-default rules. §4.7 6-step backup-first migration. §4.8 rollback path. §4.9 **P14 RESOLVED** declaration with v11.0 PoC acceptance (<1% shadow discrepancy). |
| 5   | **SC#5:** Retained-phases allowlist (Steps 0/6.5/7/10/11/12/15) + legacy `agent_id=hermes` policy | ✓ VERIFIED | §5 spans lines 1155-1348 (~200 lines, 7 subsections §5.0-§5.6). §5.2 7-step retained-phases table with per-step rationale + 8-step exclusion table. §5.3 allowlist location resolution = `retained_python_phases` field NEW in `round-table-state-schema.yaml` (schema-level constraint; resolves OQ-10). §5.4 dispatcher-layer enforcement with pseudo-code. §5.5 legacy v7.0 `agent_id=hermes` 遗留/不迁移 policy (resolves OQ-3). §5.6 30-day sunset window with operator-extendable config. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | ---------| ------- | -------- |
| `.planning/research/v10-orchestrator-design/04-MIGRATION-PATH.md` | 800+ lines; bilingual EN structure + 中文 prose; deliver (a) 75-cell transform table + (b) skill_fallback → mcp_tool 切换 + (c) FeedbackStore→memory-record migration + (d) retained-phases allowlist + legacy mem0 policy | ✓ VERIFIED | 1,508 lines (1.9× min). All 4 lockable artifacts present + cross-validated. Contains all 56 required terms from plan's `contains:` list (including `--dry-run`, all 15 expert_ids, all 7 step values, all citations). 8 sections (§0-§7) match plan structure. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------- | -------- |
| `04-MIGRATION-PATH.md` | `00-FIRST-PRINCIPLES.md §2.1-§2.7` (决策 1-7) | markdown citation by 决策号 | ✓ WIRED | §1.1 frames 决策 1/2/5/6/7; §6.1 7-row audit table cites all 7 决策 with ✅; 决策 1 (4 mentions), 决策 2 (5+ mentions, "LOAD-BEARING root for SC#5"), 决策 5 (4 mentions), 决策 6 (3 mentions), 决策 7 (4 mentions) |
| `04-MIGRATION-PATH.md` | `ARCHITECTURE.md §1.1, §1.2, §2, §6, §6.1, §6.4` | markdown §reference | ✓ WIRED | §1.6 15-expert table copied verbatim (verified by expert-id diff = identical); §2.0/§2.18 cite §1.2 + §2 closing paragraph; §6.1 audit row 5 cites §1.1+§1.2+§1.3; §1.4 cites §6.4 repo impact. ARCHITECTURE.md §6.1 (line 582) + §6.4 (line 625) confirmed present. |
| `04-MIGRATION-PATH.md` | `agents-schema.yaml` (18 fields) + `memory-record-schema.yaml` (10 fields, line 353) | field-name reference | ✓ WIRED | `default_invocation` enum cited verbatim (mcp_tool\|skill_fallback\|disabled); `memory_scope`, `lineage.skill_sha256`, `round_table_eligible`, `expert_id` all cited by field name. memory-record-schema `schema_version` cited by line (353 — verified). `agents-schema.yaml` field 18 confirmed at line 273 with matching enum. |
| `04-MIGRATION-PATH.md` | `round-table-state-schema.yaml` (`retained_python_phases` field) | markdown §reference + schema field spec | ✓ WIRED | §5.3 declares NEW field spec (lines 1222-1251) with `enum: [step_0, step_6_5, step_7, step_10, step_11, step_12, step_15]` + `default` + `required: true`. Field is forward-declared (not yet in schema YAML — implementation deferred to v11.0 PoC per design-only phase scope). |
| `04-MIGRATION-PATH.md` | `PITFALLS.md §P14` + `STACK.md §3.2 Tool 7` + `STACK.md §11.2` | markdown §reference | ✓ WIRED | §4.0 cites P14 risk; §4.4-§4.6 cite 3 mitigations; §4.9 declares P14 RESOLVED. §5.1 cites STACK §3.2 Tool 7 `run_python_phase` signature; §5.3 cites STACK §11.2 line 1120 verbatim. PITFALLS §P14 confirmed at line 438; STACK §3.2 Tool 7 confirmed at line 538; STACK §11.2 line 1120 confirmed. |
| `04-MIGRATION-PATH.md` | `SUMMARY.md` OQ-3 + OQ-10 | markdown §reference | ✓ WIRED | §5.0 + §6.3 + §7.2 all cite OQ-3 + OQ-10. §5.5 cites OQ-3 verbatim; §5.3 cites OQ-10 resolution. §6.3 resolution table maps both to specific §5 subsections. |

### Data-Flow Trace (Level 4)

Not applicable — this is a **design-only markdown deliverable** with no rendered dynamic data. The "data" in this doc is design rules + cross-doc citations, all of which resolve (Key Links section above). No DB queries, no API calls, no UI rendering.

### Behavioral Spot-Checks

Not applicable — design-only deliverable, no runnable code produced in this phase (per plan objective: "Zero code changes (no SKILL.md / Python / plugin / mcp_serve.py edits)"). The pseudo-code blocks in §3.7 + §5.4 are explicitly labeled `# pseudo-code — actual implementation in v11.0 PoC`.

### Probe Execution

Not applicable — design-only phase. No `scripts/*/tests/probe-*.sh` declared in PLAN or SUMMARY.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| **DESIGN-05** | `49-01-PLAN.md` | Migration Path: 15-expert transform 规则 + skill_fallback 切换 + FeedbackStore→memory-record migration + retained-phases allowlist + schema_version + dry-run | ✓ SATISFIED | All 5 deliverables in DESIGN-05 (REQUIREMENTS.md lines 73-77) map cleanly to SC#2/3/4/5 + §4.4 schema_version + §4.5 dry-run. Mandatory OQ-3 (v7.0 mem0 legacy) + OQ-10 (allowlist location) + P14 avoidance all resolved (§5.5/§5.3/§4.9). |

No orphaned requirements — REQUIREMENTS.md row 146 explicitly maps DESIGN-05 → Phase 49 → `04-MIGRATION-PATH.md` → "OQ-3,10 | P14 | ARCHITECTURE §2,6 + STACK §3.2 Tool 7", all of which this doc delivers.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `04-MIGRATION-PATH.md` | 1037 | `mem0 backend may compress; actual footprint TBD.` | ℹ️ Info | Non-load-bearing note about future mem0 storage measurement after migration — not a debt marker for the migration plan itself. The 5-metric dry-run output plan + 2.4MB estimate above this line are concrete. |

**Debt marker gate:** No `TBD`, `FIXME`, or `XXX` markers in load-bearing positions. The single TBD is a parenthetical about mem0 backend compression behavior (not in scope for this design doc — backend behavior is v11.0 PoC implementation detail). No `placeholder`, `coming soon`, `not yet implemented` strings. No empty implementations (`return null` / `=> {}`).

**Count reconciliation self-correction (§3.6, lines 783-815):** SUMMARY.md flags this as an "auto-fixed issue" — the §2.17 vs §3.6 2/15 vs 1/15 special-handling discrepancy is resolved in-paragraph with a "Count reconciliation" subsection that explains persona-framing perspective (2/15) vs dispatch perspective (1/15, load-bearing). This is a documentation discipline positive, not an anti-pattern.

### Human Verification Required

None. This is a design-only deliverable with no UI, no runtime behavior, no external service integration. The lockable artifacts are markdown rules tables that downstream v11.0 PoC implementer consumes. Human review (Kai as reviewer per §0.2 three-audience guide) is the standard milestone review path, not a gate-stage human verification item.

### Gaps Summary

No gaps. All 5 ROADMAP SCs verified with codebase evidence. All required artifacts exist, are substantive (1.9× min line count), and are fully wired to Phase 44/45/46/47/48 sources. All cross-doc citations resolve. All 5 DESIGN-05 deliverables satisfied. OQ-3 + OQ-10 + P14 explicitly resolved with section pointers (§5.5/§5.3/§4.9). Phase 44 决策 1-7 cross-validation = 7/7 ✅.

The `retained_python_phases` field is forward-declared in §5.3 (NOT yet present in `round-table-state-schema.yaml`) — but this is correct by design: the plan explicitly states "NEW field added by this doc" + implementation is v11.0 PoC scope (Phase 49 is design-only per CLAUDE.md constraint). This is not a gap.

---

_Verified: 2026-07-07T02:30:00Z_
_Verifier: Claude (gsd-verifier)_
