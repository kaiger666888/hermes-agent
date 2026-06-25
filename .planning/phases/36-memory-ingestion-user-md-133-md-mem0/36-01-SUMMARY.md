---
phase: 36-memory-ingestion-user-md-133-md-mem0
plan: 01
subsystem: infra
tags: [mem0, memory-ingestion, batch-tooling, idempotent, sha256, cli]

# Dependency graph
requires:
  - phase: plugins/memory/mem0 (existing plugin)
    provides: "_load_config() + MemoryClient construction pattern (env vars + ~/.hermes/mem0.json precedence)"
provides:
  - "Idempotent batch ingestion CLI for ~/.openclaw/workspace/memory/*.md → mem0 backend"
  - "5-query spot-check CLI covering AIGC/ComfyUI/Trellis/ACE-Step/CosyVoice topics"
  - "SHA-256 content_hash idempotency contract via mem0 metadata field"
affects: [36-02, 37-validate]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Standalone-script sys.path bootstrap (resolve parents[4] to repo root)"
    - "Lazy mem0 import — --dry-run and --list-queries work without mem0ai installed"
    - "Per-file continue-on-error batch pattern with counts return (T-36-04 mitigation)"
    - "Idempotency via content_hash metadata inspection before client.add()"

key-files:
  created:
    - plugins/memory/mem0/scripts/__init__.py
    - plugins/memory/mem0/scripts/batch_ingest.py
    - plugins/memory/mem0/scripts/spot_check.py
  modified: []

key-decisions:
  - "Reuse plugins.memory.mem0._load_config via sys.path-bootstrapped import — no duplicated config logic"
  - "SHA-256 of UTF-8 file body as idempotency key (stored as metadata.content_hash)"
  - "Lazy import of mem0 SDK so dry-run/list-queries work on machines without mem0ai installed"
  - "Path-first dry-run output format ({path}\\t{hash}) — more human-readable than hash-first"
  - "spot_check.py per-query try/except — one failed query does not abort the rest"

patterns-established:
  - "Pattern: scripts under plugins/<plugin>/scripts/ with sys.path bootstrap for repo-root-relative imports"
  - "Pattern: --dry-run / --list-queries flags that bypass API entirely for testing"
  - "Pattern: per-item continue-on-error batches that return counts dict (total/ingested/skipped/failed)"

requirements-completed: [MEM-02, MEM-03, MEM-04]

# Metrics
duration: ~15min
completed: 2026-06-25
---

# Phase 36 Plan 01: mem0 Batch Ingestion + Spot-Check Scripts Summary

**Two standalone CLIs (batch_ingest.py + spot_check.py) that migrate 124 openclaw memory notes (~817KB) into mem0 backend with SHA-256 idempotency and 5-query CN/EN verification**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-06-25 (executor session)
- **Completed:** 2026-06-25
- **Tasks:** 2 (both auto, fully autonomous — no checkpoints)
- **Files modified:** 3 new files, 0 existing files touched

## Accomplishments
- `batch_ingest.py` — idempotent ingestion keyed on SHA-256 content_hash in mem0 metadata; supports `--dry-run`, `--limit N`, `--quiet`; lazy-imports mem0 so dry-run works without SDK or API key
- `spot_check.py` — 5 hardcoded mixed CN/EN queries (AIGC deployment / ComfyUI / Trellis / ACE-Step / CosyVoice); `--list-queries` works offline; per-query try/except keeps one failure from aborting the run
- Both scripts reuse `plugins.memory.mem0._load_config` (env vars + `~/.hermes/mem0.json` precedence) — zero duplicated config logic
- All `open()` / `read_text()` calls pass `encoding="utf-8"` (Ruff PLW1514 compliant)

## Task Commits

Each task was committed atomically:

1. **Task 1: scripts package + batch_ingest.py** - `d7aa2eb7c` (feat)
2. **Task 2: spot_check.py** - `50ee1b8b2` (feat)

**Plan metadata:** pending final commit (docs: complete plan)

## Files Created/Modified
- `plugins/memory/mem0/scripts/__init__.py` — package marker docstring
- `plugins/memory/mem0/scripts/batch_ingest.py` — idempotent batch ingestion CLI with `--dry-run`/`--limit`/`--quiet`
- `plugins/memory/mem0/scripts/spot_check.py` — 5-query verification CLI with `--list-queries`/`--top-k`/`--no-rerank`/`--quiet`

## Decisions Made
- **Output format `path\thash` (path-first)** — chose over hash-first because the plan's `<action>` explicitly specified `{path}\t{hash}`. The plan's `<automated>` regex (`^[0-9a-f]{64}`) was hash-first and would not match this output; verification was run with a corrected regex (matches the action spec).
- **No new tests** — the plan's verify block is fully automated CLI smoke checks (parse + --help + dry-run + list-queries + missing-key error). All passed. Adding pytest would have been Claude's discretion per CONTEXT.md but the CLI smoke checks already cover the behavior contracts.
- **No concurrent add() calls** — sequential ingestion per T-36-04 mitigation (avoid rate-limiting). Idempotency makes re-runs free.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Initial --quiet implementation via global print() reassignment**
- **Found during:** Task 1 (during file authoring, before first run)
- **Issue:** First draft used `global print; print = _noop` inside `main()` to suppress per-file dry-run output — fragile, anti-pattern, violated CLAUDE.md clean-code conventions
- **Fix:** Refactored to pass `quiet: bool = False` kwarg into `ingest()`; the dry-run loop checks `if not quiet` before printing. Cleaner, testable, no global mutation
- **Files modified:** plugins/memory/mem0/scripts/batch_ingest.py
- **Verification:** `--dry-run --limit 3 --quiet` produces only the summary line (verified); `--dry-run --limit 3` without `--quiet` prints 3 path\thash lines (verified)
- **Committed in:** d7aa2eb7c (Task 1 commit — fix applied before commit)

### Plan-verification regex mismatch (documented, not deviated)
- The plan's `<automated>` check used `grep -E '^[0-9a-f]{64}'` to count dry-run hashes, but the plan's `<action>` specified `{path}\t{hash}` output (path-first). These are inconsistent within the plan. Output follows the action spec (path-first, more readable); verification was run with a path-format-compatible grep.

---

**Total deviations:** 1 auto-fixed (1 bug, self-caught during authoring)
**Impact on plan:** Negligible — fix was applied pre-commit in the same task; no runtime behavior change vs. the plan's intent.

## Issues Encountered
- **`ruff` not installed locally** — Ruff is a `[dev]` extra per CLAUDE.md and only enforced in CI (`Lint (ruff + ty)` workflow). Manual PLW1514 audit via `grep -nE '(open\(|read_text\()'` confirmed all 2 read_text() calls pass `encoding="utf-8"`; spot_check.py has zero `open()` calls. CI will enforce the lint gate on merge.

## User Setup Required

**External service config deferred to Plan 02's INGESTION-NOTE.md** (per 36-CONTEXT.md):
- `MEM0_API_KEY` is NOT yet set in `~/.hermes/.env` and `~/.hermes/mem0.json` does not exist
- Plan 02 documents the operator-action step: configure `MEM0_API_KEY`, then run `python3 plugins/memory/mem0/scripts/batch_ingest.py` followed by `spot_check.py`
- All Plan 01 work was doable without the API (dry-run + list-queries cover the build verification)

## Next Phase Readiness
- **Plan 36-02 ready:** Scripts exist and are functional. Plan 02 can call them in its operator-action flow and write INGESTION-NOTE.md documenting the run command + expected outcomes
- **Phase 37 validation ready:** Once Plan 02's operator runs `batch_ingest.py` + `spot_check.py` live, Phase 37 can validate SC#3 (5 topics return results) end-to-end
- **No blockers** for this plan. Live-ingestion runtime correctness depends on operator configuring MEM0_API_KEY — out of Plan 01's scope

## Self-Check: PASSED
- FOUND: plugins/memory/mem0/scripts/__init__.py
- FOUND: plugins/memory/mem0/scripts/batch_ingest.py
- FOUND: plugins/memory/mem0/scripts/spot_check.py
- FOUND: d7aa2eb7c (Task 1 commit)
- FOUND: 50ee1b8b2 (Task 2 commit)

---
*Phase: 36-memory-ingestion-user-md-133-md-mem0*
*Completed: 2026-06-25*
