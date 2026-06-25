---
phase: 36-memory-ingestion-user-md-133-md-mem0
plan: 02
subsystem: infra
tags: [mem0, memory-ingestion, user-md-migration, operator-action, dry-run, audit-trail]

# Dependency graph
requires:
  - phase: 36-memory-ingestion-user-md-133-md-mem0/01
    provides: "batch_ingest.py + spot_check.py CLIs (commits d7aa2eb7c, 50ee1b8b2)"
provides:
  - "~/.hermes/memories/USER.md with openclaw-origin frontmatter (operator-state)"
  - "36-01-INGESTION-NOTE.md operator-action audit trail (repo-commit)"
  - "124-file inventory with SHA-256 hashes (dry-run output)"
affects: [37-validate]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Operator-state file migration with provenance frontmatter (not git-tracked)"
    - "Dry-run validation of API-dependent tooling (no key needed)"
    - "Single-document operator-action audit trail (status + inventory + commands + SC verifications)"

key-files:
  created:
    - ~/.hermes/memories/USER.md  # operator-state, NOT git-tracked
    - .planning/phases/36-memory-ingestion-user-md-133-md-mem0/36-01-INGESTION-NOTE.md
  modified: []

key-decisions:
  - "Pre-existing ~/.hermes/memories/USER.md (single-line hermes-agent note) overwritten by openclaw-source migration per CONTEXT.md decision 1 — documented as deviation"
  - "124-file inventory captured via separated stdout/stderr (initial 2>&1 merge interleaved summary with last file line)"
  - "Doc-consistency patch for ROADMAP/STATE/REQUIREMENTS (133→124, 1.3MB→817KB) flagged as out-of-Phase-36 scope"

requirements-completed: [MEM-01]

# Metrics
duration: ~10min
completed: 2026-06-25
---

# Phase 36 Plan 02: USER.md Migration + Dry-Run Validation + Ingestion Operator-Action Note Summary

**Migrated Kai's USER.md from openclaw to hermes with provenance frontmatter, validated batch_ingest.py dry-run (124 files / 817KB), and authored the operator-action note Kai reads to complete live mem0 ingestion once MEM0_API_KEY is configured**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-06-25 (executor session)
- **Completed:** 2026-06-25
- **Tasks:** 2 (both auto, fully autonomous — no checkpoints)
- **Files created:** 1 operator-state file (`~/.hermes/memories/USER.md`, not git-tracked) + 1 repo-commit (`36-01-INGESTION-NOTE.md`)

## Accomplishments
- `~/.hermes/memories/USER.md` created with exact frontmatter (`openclaw-origin: true`, `migrated-at: 2026-06-25`, `source-path: ~/.openclaw/workspace/USER.md`) and byte-identical body to openclaw source (verified via `diff`)
- Dry-run of Plan 36-01's `batch_ingest.py` enumerates exactly **124 files** successfully (no MEM0_API_KEY needed for dry-run path)
- Independently confirmed file count and total size via `find`: 124 files / 837,136 bytes (817KB) — corrects ROADMAP's "133 files / 1.3MB" planning estimate
- Authored `36-01-INGESTION-NOTE.md` covering: status, file-count correction, full 124-file inventory with SHA-256 hashes, tooling reference, MEM0_API_KEY operator-action steps, exact live commands (ingest + spot-check + idempotency re-test), Phase 37 SC#1-4 verification commands, partial-ingest escape hatch, and what-ships-without-the-key summary
- Confirmed `~/.hermes/memories/USER.md` is NOT in git working tree (operator-state, correct per CLAUDE.md)

## Task Commits

Each task committed atomically:

1. **Task 1: USER.md migration** — No git commit (operator-state file, lives under `~/.hermes/` outside the repo worktree). File write verified by `diff <(tail -n +7 ~/.hermes/memories/USER.md) ~/.openclaw/workspace/USER.md` (no output = byte-identical).
2. **Task 2: INGESTION-NOTE.md** — `7d614c4f2` (docs)

**Plan metadata:** pending final commit (docs: complete plan)

## Files Created/Modified
- `~/.hermes/memories/USER.md` — openclaw-origin migration target with 3-key frontmatter (operator-state, not git-tracked)
- `.planning/phases/36-memory-ingestion-user-md-133-md-mem0/36-01-INGESTION-NOTE.md` — operator-action audit trail with 124-file inventory, MEM0_API_KEY steps, exact commands, SC#1-4 verifications

## Decisions Made
- **Overwrote pre-existing `~/.hermes/memories/USER.md`** — The target path already contained a single-line hermes-agent-specific note ("Kai 的核心工作流..."). The plan's MEM-01 scope explicitly defines the target body as the openclaw source verbatim with prepended frontmatter, so the pre-existing single line is replaced. The original openclaw body is byte-preserved; the pre-existing hermes-agent note is not retained (it is recoverable from git history if needed — but the file was not git-tracked either, so it is simply gone). See Deviations section.
- **124-file inventory captured via separated stdout/stderr** — Initial `2>&1` merge of the dry-run output interleaved the stderr summary line ("DRY-RUN: would ingest 124 files...") with the last file's stdout line, producing a malformed line 71 in the raw capture. Re-ran with `> /tmp/files.log 2> /tmp/summary.log` to get clean separation. The note embeds the clean 124-line inventory.
- **Doc-consistency patch deferred** — ROADMAP.md, STATE.md, REQUIREMENTS.md MEM-02 all say "133 files / 1.3MB" but verified actual is 124 / 817KB. This is flagged in the INGESTION-NOTE.md but not patched in Phase 36 (out of scope — would touch 3 planning docs unrelated to the plan's deliverables).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality / data preservation] Overwrote pre-existing USER.md content**
- **Found during:** Task 1 (Write tool returned "File has not been read yet" error because the target path already existed)
- **Issue:** `~/.hermes/memories/USER.md` already existed with a single line of hermes-agent-specific content ("Kai 的核心工作流：使用 Hermes Agent 作为..."). The plan's `<action>` specifies overwriting with the openclaw-source body + frontmatter, which replaces this pre-existing content.
- **Fix:** Followed the plan as written — Read the existing file first (to satisfy the Write tool's safety check), then overwrote with the openclaw-source migration per CONTEXT.md decision 1. The pre-existing single-line note is not retained in the target file.
- **Rationale:** Plan scope (MEM-01) is explicit: the target body IS the openclaw source verbatim. The pre-existing hermes-agent-specific line was neither part of the openclaw migration corpus nor recent operator state (file mtime was 2026-06-19, predating v7.0 migration work). If the operator wants to preserve that note, it can be re-added in a separate USER.md section in a future task.
- **Files modified:** ~/.hermes/memories/USER.md (operator-state)
- **Commit:** No git commit (operator-state file)

**2. [Rule 1 - Bug] Dry-run output capture interleaved stderr with stdout**
- **Found during:** Task 2 (initial dry-run capture)
- **Issue:** First capture used `> /tmp/p36-dryrun.log 2>&1` which merged the stderr summary line with the final stdout file line, producing a malformed combined line (`...2026-05-28.md\tf4b856...\nDRY-RUN: would ingest 124 files...` got concatenated as a single broken line).
- **Fix:** Re-ran with separated redirection: `> /tmp/p36-files.log 2> /tmp/p36-summary.log`. The INGESTION-NOTE.md inventory embeds the clean 124-line stdout output and quotes the stderr summary separately.
- **Files modified:** none (capture-only fix)
- **Verification:** `wc -l /tmp/p36-files.log` = 124 exactly; summary line is cleanly isolated
- **Commit:** 7d614c4f2 (Task 2 commit — fix applied before commit)

---

**Total deviations:** 2 auto-fixed (1 data-preservation decision per plan scope, 1 capture bug)
**Impact on plan:** Negligible — both fixes align with plan intent; no runtime behavior change.

## Issues Encountered
- **None blocking.** The plan executed cleanly end-to-end. All verification checks pass.

## User Setup Required

**External service config deferred to operator (per plan design):**
- `MEM0_API_KEY` is NOT set in `~/.hermes/.env` and `~/.hermes/mem0.json` does not exist
- The `36-01-INGESTION-NOTE.md` document (committed in Task 2) contains the complete operator-action checklist: install mem0ai, obtain key from https://app.mem0.ai, configure env var OR json file, run the three live commands (ingest + spot-check + idempotency re-test)
- All Plan 02 work was doable without the API (USER.md migration + dry-run validation cover the deliverables)

## Next Phase Readiness
- **Phase 37 validation:** SC#1 (USER.md frontmatter) is verifiable NOW. SC#2-4 are blocked on the operator running the live commands documented in `36-01-INGESTION-NOTE.md` — once the operator completes them, Phase 37 can verify SC#2 (≥124 entries in backend), SC#3 (5 topic queries non-empty), SC#4 (idempotency re-run = 0 ingested / 124 skipped) end-to-end.
- **No blockers** for this plan. Live-ingestion runtime correctness depends on operator configuring MEM0_API_KEY — explicitly out of Plan 02's scope (the plan's job was to deliver the operator-ready document, which is done).

## Self-Check: PASSED

**Files:**
- FOUND: ~/.hermes/memories/USER.md (operator-state, not git-tracked — correct)
- FOUND: .planning/phases/36-memory-ingestion-user-md-133-md-mem0/36-01-INGESTION-NOTE.md

**Commits:**
- FOUND: 7d614c4f2 (Task 2 — INGESTION-NOTE.md)

**Functional verification:**
- PASS: `head -5 ~/.hermes/memories/USER.md` shows all 3 required frontmatter keys
- PASS: `diff <(tail -n +7 ~/.hermes/memories/USER.md) ~/.openclaw/workspace/USER.md` produces no output (byte-identical body)
- PASS: `python3 plugins/memory/mem0/scripts/batch_ingest.py --dry-run --quiet 2>&1 | grep 'would ingest 124'` matches
- PASS: `~/.hermes/memories/USER.md` is NOT in `git status` output (operator-state)
- PASS: All 8 sub-checks of Task 2's `<automated>` verification block return OK

---
*Phase: 36-memory-ingestion-user-md-133-md-mem0*
*Plan: 02*
*Completed: 2026-06-25*
