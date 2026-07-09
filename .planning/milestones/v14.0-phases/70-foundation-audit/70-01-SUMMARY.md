---
phase: 70
plan: 01
subsystem: planning-artifacts (lineage baseline)
tags: [v14.0, foundation-audit, lineage, sha256, cross-repo, documentation-only]
requires:
  - "Phase 62 (v13.0): original transform produced the agent.yaml lineage.skill_sha256 values this inventory captures"
  - "Phase 14 (v3.0): drawer merged into visual_executor (drawer SKILL.md is a 654-byte DEPRECATED stub)"
provides:
  - "Pre-v14.0 working-tree sha256 baseline for all 6 target SKILL.md files (consumed by Phase 75 to distinguish v14.0-introduced drift from pre-existing drift)"
  - "Current agent.yaml lineage.skill_sha256 capture for the 3 existing agent YAMLs (Phase 75 overwrites these; Phase 76 asserts post-bump match)"
  - "Cross-repo commit pins (Phase 76 asserts the kais-hermes-skills pin still resolves and that post-v14.0 commits are descendants)"
  - "Canonical field-name reference for Phase 75/76 (lineage.skill_sha256 NOT source_sha, etc.)"
affects:
  - "Phase 71 (FORM) — SKILL.md edits invalidate the working-tree baseline captured here"
  - "Phase 72 (DUB) — may edit audio_pipeline / kais-movie-pipeline SKILL.md"
  - "Phase 73 (IMG) — may edit kais-jimeng-cli / kais-movie-pipeline SKILL.md"
  - "Phase 74 (TRANSITION) — may edit cinematographer / editor SKILL.md"
  - "Phase 75 (LINEAGE-BUMP) — re-runs transform_skill_to_agent.py against the captured agent.yaml files; consults this inventory to distinguish pre-existing drift (cinematographer + audio_pipeline) from v14.0-introduced drift"
  - "Phase 76 (VALIDATE) — re-hashes SKILL.md from the pinned kais-hermes-skills commit and compares against post-bump agent.yaml.lineage.skill_sha256"
tech-stack:
  added: []
  patterns:
    - "Markdown table + embedded JSON dual-format (human-readable + machine-parseable)"
    - "Canonical sha256 algorithm (LF-normalize UTF-8) replicated byte-for-byte from scripts/transform_skill_to_agent.py:232-240"
key-files:
  created:
    - path: .planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md
      purpose: "Pre-v14.0 lineage baseline covering XCUT-01 sub-rows a (inventory exists) / b (6 SKILL.md with sha256) / c (cross-repo commit pins)"
      lines: 171
  modified: []
decisions:
  - "Inventory hashes working-tree bytes (NOT git-committed blobs) so Phase 71-74 edits are measurable against what they actually touch"
  - "Used canonical field names lineage.skill_sha256 / transform_date / transform_notes throughout (NOT roadmap shorthand source_sha / transform_rule_id / transform_timestamp); documented the mapping explicitly in the file so downstream phases cannot grep for nonexistent fields"
  - "Captured pre-existing drift (cinematographer + audio_pipeline MISMATCH) as a documented callout, NOT fixed mid-Phase-70 — Phase 75 closes it as a side effect of re-transform"
  - "Lineage bump scope = 3 existing agent.yaml files only (drawer/kais-movie-pipeline/kais-jimeng-cli remain skill-only per FOUND-08 frozen 15-expert set)"
  - "Live cross-repo pins captured (hermes-agent=8f70fcf7, kais-hermes-skills=d9620369); research notes' older pin 846a8d7e was stale, the live git rev-parse value superseded it"
metrics:
  duration: ~6 min
  completed_date: 2026-07-09
  tasks_completed: 1
  tasks_total: 1
  files_created: 1
  files_modified: 0
---

# Phase 70 Plan 01: Foundation-Audit Lineage Baseline Summary

Captured the pre-v14.0 lineage baseline (6 SKILL.md working-tree hashes + 3 agent.yaml lineage captures + 2 cross-repo commit pins) in a single dual-format markdown file with embedded machine-readable JSON for Phase 76.

## What was built

**Deliverable:** `.planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md` (171 lines)

Structure:
1. Header with capture date + cross-repo pins (live `git rev-parse HEAD` for both repos).
2. Canonical field-name note (maps roadmap shorthand `source_sha` → `lineage.skill_sha256` etc.) — guards against Phase 75/76 grep-for-nonexistent-field silent-pass bugs.
3. 6-row SKILL.md baseline table: `skill_id`, path, working-tree sha256 (LF-norm UTF-8), byte count, agent.yaml existence, agent.yaml `lineage.skill_sha256`, `lineage.transform_date`, `lineage_match`.
4. Pre-existing drift callout block + delta decomposition table so Phase 75 can separate v14.0-introduced drift from pre-existing drift.
5. Per-agent.yaml lineage detail (3 subsections with all canonical fields including `transform_notes`).
6. Machine-readable fenced JSON block at the bottom for Phase 76 programmatic parsing.

**Algorithm:** canonical `hashlib.sha256(content.replace("\r\n","\n").encode("utf-8")).hexdigest()` from `scripts/transform_skill_to_agent.py:232-240`, replicated byte-for-byte via a `/tmp/` Python one-shot (not committed to the repo per plan instructions).

## Key captured values (verified against research-expected, all 6 match)

| skill_id | working-tree sha256 | lineage_match |
|----------|---------------------|---------------|
| cinematographer | `ebe9d3fa...` | **MISMATCH** (agent.yaml has `b4bcc9c6...`) |
| editor | `bd5bf4a1...` | OK |
| audio_pipeline | `e0470105...` | **MISMATCH** (agent.yaml has `fe59f7fa...`) |
| drawer | `2c21f234...` | N/A (skill-only, DEPRECATED stub merged into visual_executor) |
| kais-movie-pipeline | `bf8b7f5a...` | N/A (skill-only) |
| kais-jimeng-cli | `3a9576a6...` | N/A (skill-only) |

**Cross-repo pins:**
- hermes-agent HEAD = `8f70fcf7f0604db21158f86f8495f3d9ce3c9ab1` (live; supersedes the `3d8b723b...` / `846a8d7e...` in older research notes)
- kais-hermes-skills HEAD = `d9620369e48eec51c31ee72ac8827c288eaccf71`

## Deviations from Plan

None — plan executed exactly as written. All 8 acceptance criteria passed on first run; no auto-fix rules triggered; no out-of-scope work required.

## Self-Check: PASSED

- File exists: `test -f .planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md` → FOUND
- SKILL.md row count: 13 (>= 6 required) → FOUND
- Canonical field name `lineage.skill_sha256` present → FOUND
- `MISMATCH` captured for cinematographer + audio_pipeline → FOUND
- `cross_repo_pins` JSON block present → FOUND
- Cross-repo pins for both repos present → FOUND
- No `transform_timestamp:` or `transform_rule_id:` field-name usage → CONFIRMED (only prose mentions explaining the canonicalization)
- Commit `a0a15e2ce` exists in git log → FOUND
