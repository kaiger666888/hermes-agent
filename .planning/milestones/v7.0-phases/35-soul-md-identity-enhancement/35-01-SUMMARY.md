---
phase: 35-soul-md-identity-enhancement
plan: 01
subsystem: operator-identity
tags: [soul-md, migration, openclaw, routing, identity, non-destructive]
requires:
  - openclaw-SOUL.md-source
  - hermes-SOUL.md-target
provides:
  - integrated-hermes-SOUL.md
  - openclaw-backup-2026-06-25
  - phase-35-transformation-note
affects:
  - operator-identity-behavior
  - future-AIGC-routing-prompts
tech-stack:
  added: []
  patterns:
    - non-destructive-additive-integration
    - natural-language-routing-rewrite (regex/MCP → skill-discovery + memory + curator)
    - operator-state-vs-repo-commit-split (only audit note is git-committed)
key-files:
  created:
    - path: .planning/phases/35-soul-md-identity-enhancement/35-01-TRANSFORMATION-NOTE.md
      type: repo-commit
      bytes: 120-lines-inserted
    - path: ~/.hermes/SOUL.md.openclaw-backup-2026-06-25
      type: operator-state
      bytes: 975
    - path: ~/.hermes/SOUL.md
      type: operator-state-modified
      bytes: 4519 (was 513)
  modified: []
decisions:
  - Dropped openclaw "手/脑" two-agent identity framing (no single-agent analog); hermes Section A identity remains authoritative
  - Genericized GLM-4-flash to "configured local LLM (per cli-config.yaml model:)" — hermes is model-agnostic
  - Adapted 5 mcp:hermes_* targets to natural-language routing (skill-discovery + mem0 + curator) — hermes' MCP server speaks a different vocabulary
  - Treated SC #3 (non-destructive) as non-trivial after CONTEXT.md baseline correction (513 bytes, not 0)
metrics:
  duration: 3min
  completed: 2026-06-25T15:00:08Z
  tasks_total: 3
  tasks_completed: 3
  files_repo_committed: 1
  files_operator_state: 2
---

# Phase 35 Plan 01: SOUL.md Identity Enhancement Summary

Non-destructively integrated openclaw's AIGC routing intelligence (24-line `~/.openclaw/SOUL.md`: identity + 4 routing categories) into `~/.hermes/SOUL.md` while preserving the original 513-byte Hermes identity byte-for-byte, tagging every openclaw-origin rule with source attribution, adapting regex/MCP routing to hermes' single-agent skill-discovery + memory + curator model, and producing a verbatim backup plus a repo-commit transformation note (the only git artifact).

## Tasks Completed

| Task | Name | Commit | Key files |
|------|------|--------|-----------|
| 1 | Backup openclaw SOUL.md verbatim + confirm hermes-target content | (no commit — operator-state only) | `~/.hermes/SOUL.md.openclaw-backup-2026-06-25` (975 bytes, mtime preserved via `cp -p`) |
| 2 | Write integrated `~/.hermes/SOUL.md` (preserve Hermes default + add openclaw 迁移 section) | (no commit — operator-state only) | `~/.hermes/SOUL.md` (4519 bytes, was 513) |
| 3 | Author transformation note (repo-commit audit artifact) | `0191f5589` | `.planning/phases/35-soul-md-identity-enhancement/35-01-TRANSFORMATION-NOTE.md` |

## Verification Results

All 7 end-to-end phase checks passed:

1. **Backup integrity** — `cmp` returns identical (975 bytes both sides, mtime `2026-05-12 14:15:12` preserved)
2. **Non-destructive integration** — `head -n 1` of integrated file matches the pre-integration 513-byte Hermes identity
3. **Source tagging** — 9 `openclaw 迁移` occurrences + 10 `2026-06-25` occurrences (both ≥ 5)
4. **Routing categories** — 即时执行 / 认知 / 专家管理 / 默认 all present
5. **Adaptation enforcement** — `GLM-4-flash` absent, `你是"手"` framing absent from integrated SOUL.md
6. **Transformation note completeness** — all 5 `mcp:hermes_*` targets + identity 手 + `GLM-4-flash` documented
7. **Repo vs operator-state split** — only the transformation note is git-committed; `~/.hermes/SOUL.md*` files are outside the repo worktree

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Rephrased GLM-4-flash reference in integrated SOUL.md to satisfy verify gate**

- **Found during:** Task 2 (verify step failed first run)
- **Issue:** Plan's Section C routing-adaptation map for the `### 默认` category instructed verbatim inclusion of the phrase "The openclaw `GLM-4-flash` hard reference is dropped" in the integrated `~/.hermes/SOUL.md`. However, the plan's own verify step (g) enforced `! grep -q "GLM-4-flash"` on that same file. The two instructions were mutually contradictory.
- **Fix:** Reworded the integrated SOUL.md line to "The openclaw fixed-model hard reference is dropped" — preserves the audit intent without the literal `GLM-4-flash` string. The transformation note (Task 3) still records the literal `GLM-4-flash` reference name in Sections 6 and 8 with full audit detail.
- **Files modified:** `~/.hermes/SOUL.md` (1 line in `### 默认` section)
- **Commit:** Operator-state, not git-committed (per plan `<output>` block). Fix happened before Task 2 verify passed.

No other deviations. Plan executed as written otherwise.

## Authentication Gates

None.

## Known Stubs

None. All routing rules are wired to concrete hermes surfaces (skill-discovery paths, mem0 plugin, curator.py). No placeholder data.

## Threat Flags

None. The plan's `<threat_model>` register (T-35-01 through T-35-05, T-35-SC) is fully satisfied:

- T-35-01 (Tampering of operator-state SOUL.md) — accept; mitigated by T-35-04 audit trail
- T-35-02 (Info disclosure: "Kais AIGC Director" naming) — accept; identity statement dropped from integrated file, preserved only in operator-only backup
- T-35-03 (Repudiation: operator-state changes leave no repo trail) — mitigated by Task 3 transformation note (this commit)
- T-35-04 (Tampering: forced provider/MCP topology) — mitigated; GLM-4-flash genericized, `mcp:hermes_*` adapted
- T-35-05 (Spoofing: missing source tags) — mitigated; 9 source-tag occurrences (≥ 5 required)
- T-35-SC (supply-chain) — N/A, no package installs

No new security-relevant surface introduced beyond what the threat model anticipated.

## Requirements Closed

- **SOUL-01** (non-destructive integration) — original 513-byte Hermes identity preserved byte-for-byte as Section A
- **SOUL-02** (trigger-mode adaptation + source tagging) — regex/MCP routing rewritten as natural-language skill-discovery + memory + curator guidance; every category carries `> **Source:** openclaw 迁移 (2026-06-25)`
- **SOUL-03** (backup + transformation note) — `cp -p` verbatim backup at `~/.hermes/SOUL.md.openclaw-backup-2026-06-25` (mtime preserved); transformation note committed at `0191f5589`

## Self-Check: PASSED

Files verified to exist:
- FOUND: `.planning/phases/35-soul-md-identity-enhancement/35-01-TRANSFORMATION-NOTE.md` (120 lines inserted)
- FOUND (operator-state): `~/.hermes/SOUL.md.openclaw-backup-2026-06-25` (975 bytes)
- FOUND (operator-state): `~/.hermes/SOUL.md` (4519 bytes)

Commits verified:
- FOUND: `0191f5589` — `docs(35): SOUL.md identity enhancement — transformation note (SOUL-01..03)`

(Operator-state files outside worktree are not expected to appear in `git log` — verified via `wc -c` and `cmp` instead.)
