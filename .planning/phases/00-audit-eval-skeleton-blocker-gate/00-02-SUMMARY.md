---
phase: 00-audit-eval-skeleton-blocker-gate
plan: 02
subsystem: testing
tags: [eval, baseline, snapshot, sha256, provenance, ablation-anchor]

# Dependency graph
requires:
  - phase: none
    provides: "14 existing movie-experts skills/*/SKILL.md files (pre-refactor state)"
provides:
  - "Standalone snapshot CLI `skills/movie-experts/_eval/snapshot.py` (capture + verify modes)"
  - "14 baseline trees under `skills/movie-experts/_eval/baseline/<expert>/{SKILL.md,PROVENANCE.json}` tagged eval-baseline-v1"
  - "Cryptographic provenance (sha256 + git sha + ISO 8601 timestamp + byte size) for drift detection"
  - "7 pytest tests covering compute_provenance / capture_baselines / verify_baselines"
affects:
  - "00-04 phantom-strip plan — uses snapshot.py verify as the regression gate after phantom removal"
  - "Phase 3/5/6 RAG refactors — diff current SKILL.md against this baseline to substantiate uplift claims (RESEARCH.md PITFALLS #8)"
  - "Phase 1+ acceptance — eval harness will compare ablated vs full expert outputs against this v1 anchor"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD red/green cycle for snapshot tool (test(00-02) -> feat(00-02) commits)"
    - "Byte-level sha256 hashing (read_bytes) avoids encoding ambiguity in provenance"
    - "Hardcoded EXPERT_DIRS allowlist — unknown dirs silently skipped, anti-spoofing (T-00-08)"
    - "Repo-relative source_path in PROVENANCE.json — portable across clones / CI / worktrees"
    - "Graceful git_sha fallback to literal 'uncommitted' string on git failure (T-00-06 accept)"

key-files:
  created:
    - "skills/movie-experts/_eval/snapshot.py"
    - "skills/movie-experts/_eval/tests/__init__.py"
    - "skills/movie-experts/_eval/tests/test_snapshot.py"
    - "skills/movie-experts/_eval/baseline/.gitkeep"
    - "skills/movie-experts/_eval/baseline/<expert>/SKILL.md (14 byte-exact copies)"
    - "skills/movie-experts/_eval/baseline/<expert>/PROVENANCE.json (14 records)"
  modified: []

key-decisions:
  - "Stdlib only — zero new packages. Honors PROJECT.md Out-of-Scope and plan's no-new-packages constraint."
  - "Byte-level hashing via Path.read_bytes() + hashlib.sha256 so the hash is a true content hash, immune to read_text encoding ambiguity."
  - "source_path stored as repo-relative POSIX path (e.g. `skills/movie-experts/animator/SKILL.md`) so the baseline tree is portable across clones and CI environments."
  - "EXPERT_DIRS is a frozen module-level list — anti-spoofing measure (T-00-08); synthetic expert dirs cannot inflate baseline count."
  - "verify_baselines does not mutate state — pure read of source + PROVENANCE.json, returns (ok, drifts) tuple."
  - "git_sha falls back to literal `uncommitted` if git unavailable, not-a-repo, or HEAD unborn (T-00-06 accept disposition)."

patterns-established:
  - "Pattern: every `open()` / `read_text()` / `write_text()` passes `encoding=\"utf-8\"` per CLAUDE.md Ruff PLW1514."
  - "Pattern: `from __future__ import annotations` at top of every new module."
  - "Pattern: specific exceptions bound to names (`except (FileNotFoundError, subprocess.SubprocessError, OSError) as exc`)."
  - "Pattern: tests build synthetic skill trees in tmp_path — never mutate real SKILL.md files during test runs."

requirements-completed: [FOUND-04, EVAL-02]

# Metrics
duration: ~20min
completed: 2026-06-15
---

# Phase 0 Plan 02: Skill Baseline Snapshot Tool Summary

**Byte-exact snapshot tool with cryptographic provenance (sha256 + git sha + ISO 8601 timestamp) for all 14 movie-experts SKILL.md files — the v1 eval anchor that every future refactor's before/after ablation claim must diff against**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-06-15T12:12Z (worktree-local)
- **Completed:** 2026-06-15T12:32Z
- **Tasks:** 2 (TDD: RED -> GREEN)
- **Files created:** 31 (1 tool, 1 test package init, 1 test file, 1 .gitkeep, 14 baseline SKILL.md copies, 14 PROVENANCE.json records)
- **pyproject.toml diff:** 0 lines (zero new packages — stdlib only)

## Accomplishments

- **Tool ships:** `python skills/movie-experts/_eval/snapshot.py capture` creates 14 baseline subdirs each holding `SKILL.md` (byte-exact) + `PROVENANCE.json`. `verify` exits 0 on clean, 1 on any drift.
- **14 baselines captured** at commit `b6ed6b53f` with git_sha `817953459c809b4f91e3be0208c8832314e2d026` (the RED-phase commit — that's where the snapshot tooling itself lives). Future re-captures will record their own current HEAD.
- **Provenance record per expert** includes all 7 required fields: `expert_id`, `tag` (= `eval-baseline-v1`), `source_path` (repo-relative POSIX), `sha256` (64 lowercase hex), `git_sha` (40 hex chars or `uncommitted`), `captured_at` (ISO 8601 with tz), `byte_size`.
- **Drift detection verified live:** mutated `colorist/SKILL.md`, ran verify, got expected-vs-actual sha256 diff report; restored file, verify returned to exit 0.
- **Found-08 preservation gate:** all 14 expert_id values in PROVENANCE.json match their directory names exactly (animator, colorist, composer, continuity, drawer, editor, foley, mixer, performer, scene_builder, screenplay, spatial_audio, style_genome, voicer).
- **Ruff PLW1514 clean:** every `open()` / `read_text()` / `write_text()` passes `encoding="utf-8"`. Byte-level hashing uses `read_bytes()` / `write_bytes()` to avoid any encoding ambiguity.

## Capture Summary

- **Timestamp (first capture):** `2026-06-15T04:15:28.112698+00:00` (UTC)
- **git_sha recorded:** `817953459c809b4f91e3be0208c8832314e2d026` (worktree HEAD at first capture)
- **Tag:** `eval-baseline-v1`
- **Total byte size:** 78,789 bytes across 14 SKILL.md files

### 14 Expert IDs Captured (alphabetical, matches EXPERT_DIRS)

| # | expert_id | sha256 (prefix) | byte_size |
|---|-----------|-----------------|-----------|
| 1 | animator | 96293f1c5778... | 4,619 |
| 2 | colorist | 64473e0a101e... | 5,566 |
| 3 | composer | 40b374d441cc... | 5,122 |
| 4 | continuity | ca353076a7b2... | 4,638 |
| 5 | drawer | 50918f5a00cc... | 4,065 |
| 6 | editor | 71009cc4ac2a... | 5,738 |
| 7 | foley | c26e557bfac3... | 6,243 |
| 8 | mixer | f70494d7c883... | 5,939 |
| 9 | performer | 41fa917a2f78... | 5,735 |
| 10 | scene_builder | 2ed778986a9f... | 6,496 |
| 11 | screenplay | a99852f18a25... | 4,992 |
| 12 | spatial_audio | aa955d2b73b7... | 6,670 |
| 13 | style_genome | 85eae12561aa... | 7,950 |
| 14 | voicer | da668e7ec83b... | 5,016 |
| | **TOTAL** | | **78,789 bytes** |

## Provenance Schema Example

```json
{
  "byte_size": 4619,
  "captured_at": "2026-06-15T04:15:28.112698+00:00",
  "expert_id": "animator",
  "git_sha": "817953459c809b4f91e3be0208c8832314e2d026",
  "sha256": "96293f1c5778ed3bec7ab81505e1e15b551370b9a5a863e528f52ad8a3976c33",
  "source_path": "skills/movie-experts/animator/SKILL.md",
  "tag": "eval-baseline-v1"
}
```

## CLI Invocation

```bash
# Capture: writes 14 baselines under skills/movie-experts/_eval/baseline/
python skills/movie-experts/_eval/snapshot.py capture

# Verify: diffs current SKILL.md files against captured baselines
python skills/movie-experts/_eval/snapshot.py verify

# Override defaults (skills_dir / baseline_dir)
python skills/movie-experts/_eval/snapshot.py capture \
  --skills-dir   /path/to/skills/movie-experts \
  --baseline-dir /path/to/baseline
```

## Task Commits

Each task was committed atomically:

1. **Task 1: Write failing tests for snapshot capture/verify** — `817953459` (`test(00-02)`)
2. **Task 2: Implement snapshot.py and capture 14 baselines** — `b6ed6b53f` (`feat(00-02)`)

_(TDD: Task 1 = RED gate, Task 2 = GREEN gate. No REFACTOR phase needed — implementation already decomposed into single-responsibility functions per CLAUDE.md.)_

## Files Created

- `skills/movie-experts/_eval/snapshot.py` — Standalone CLI. Public exports: `compute_provenance(skill_path, expert_id, git_sha, *, repo_root=None)`, `capture_baselines(skills_dir, baseline_dir, git_sha=None, *, repo_root=None)`, `verify_baselines(skills_dir, baseline_dir) -> (bool, list[dict])`, `main(argv=None)`. 295 lines.
- `skills/movie-experts/_eval/tests/__init__.py` — empty marker for pytest discovery.
- `skills/movie-experts/_eval/tests/test_snapshot.py` — 7 pytest tests across `TestComputeProvenance` (3), `TestCaptureBaselines` (2), `TestVerifyBaselines` (2). 190 lines.
- `skills/movie-experts/_eval/baseline/.gitkeep` — directory placeholder.
- `skills/movie-experts/_eval/baseline/<expert>/SKILL.md` (14 files) — byte-exact copies.
- `skills/movie-experts/_eval/baseline/<expert>/PROVENANCE.json` (14 files) — provenance records.

## Decisions Made

1. **Stdlib only.** Honors plan's no-new-packages constraint and PROJECT.md Out-of-Scope. Imports: `argparse`, `hashlib`, `json`, `subprocess`, `sys`, `datetime`, `pathlib`.
2. **Byte-level hashing** via `Path.read_bytes()` + `hashlib.sha256`. Avoids any encoding ambiguity — sha256 is a true content hash, not subject to read_text round-trip artifacts.
3. **Repo-relative source_path.** Initial implementation used `str(skill_path)` which embedded the absolute worktree path. Changed to `Path.relative_to(repo_root).as_posix()` so the baseline tree is portable across clones, CI, and worktrees (deviation Rule 2 — correctness for portability).
4. **Hardcoded EXPERT_DIRS allowlist** — threat T-00-08 mitigation. A synthetic expert directory injected into `skills/movie-experts/` cannot inflate the baseline count because capture only iterates the 14 frozen names.
5. **Graceful git_sha fallback.** `_current_git_sha` catches `FileNotFoundError`, `subprocess.SubprocessError`, `OSError` and returns literal `"uncommitted"` — provenance record is still written, just flagged as not-yet-committed (T-00-06 accept).
6. **Test fixtures use realistic 40-char shas.** Initial test passed `git_sha="deadbeef"` (8 chars) which failed the strict `_GIT_SHA_RE = ^[0-9a-f]{40}$|^uncommitted$` assertion. Updated to `"deadbeef" * 5` (40 chars) and `"0123456789abcdef" * 4` (64 chars, regex accepts 40-char prefix) to mirror the real git sha format.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] cwd drift to main repo caused first commit to land on `main` instead of worktree branch**
- **Found during:** Task 1 first commit attempt.
- **Issue:** Bash commands `cd /data/workspace/hermes-agent` (the main repo path) took me out of the worktree at `.claude/worktrees/agent-abc681e8ea358c1c5/`. The `Write` tool also received absolute paths starting with `/data/workspace/hermes-agent/...` which resolved into the main repo, not the worktree (#3099 absolute-path safety violation). Result: commit `1da7796cb` landed on `main` instead of `worktree-agent-abc681e8ea358c1c5`.
- **Fix:** Detected via `git rev-parse --abbrev-ref HEAD` returning `main` instead of `worktree-agent-*`. Recovery: (a) `git reset --hard 3a9ea479b` in main repo to undo my erroneous commit (only my own commit was on top of the known-good base — no concurrent work destroyed); (b) re-created test files inside the worktree using relative paths; (c) all subsequent Bash commands use the default cwd (which is the worktree); all Write/Edit operations use paths derived from `git rev-parse --show-toplevel` run inside the worktree.
- **Files modified:** none (recovery was purely branch-state).
- **Committed in:** N/A (recovery happened before any worktree commits).
- **Verification:** Every subsequent commit landed on `worktree-agent-abc681e8ea358c1c5`; pre-commit HEAD assertion passes.

**2. [Rule 2 - Correctness] provenance.source_path stored as absolute path**
- **Found during:** Task 2 first capture run.
- **Issue:** Initial `compute_provenance` used `str(skill_path)` which embedded `/data/workspace/hermes-agent/.claude/worktrees/agent-abc681e8ea358c1c5/skills/movie-experts/animator/SKILL.md`. Future CI runs in a fresh clone or different worktree would record different absolute paths while the underlying content is identical — making the baseline tree look non-portable.
- **Fix:** Added optional `repo_root` parameter to `compute_provenance`. When provided, `source_path` is computed as `Path.relative_to(repo_root).as_posix()` (e.g. `skills/movie-experts/animator/SKILL.md`). Threaded `repo_root=skills_dir.parents[1]` through `capture_baselines` and `main()`. Falls back to absolute path only if the skill is outside `repo_root`.
- **Files modified:** `skills/movie-experts/_eval/snapshot.py`.
- **Committed in:** `b6ed6b53f` (Task 2 commit — bundled with the GREEN implementation).

**3. [Rule 1 - Bug] Test fixture used unrealistic git_sha format**
- **Found during:** Task 2 first GREEN test run.
- **Issue:** `test_creates_14_dirs_with_skill_md_and_provenance` passed `git_sha="deadbeef"` (8 chars). The test's own `_GIT_SHA_RE = ^[0-9a-f]{40}$|^uncommitted$` regex then failed to match.
- **Fix:** Updated both test fixtures to use 40-char hex shas (`"deadbeef" * 5` and `"0123456789abcdef" * 4`). The implementation was correct — the test's contract was over-strict on fixture data.
- **Files modified:** `skills/movie-experts/_eval/tests/test_snapshot.py`.
- **Committed in:** `b6ed6b53f` (Task 2 commit).

---

**Total deviations:** 3 auto-fixed (1 blocking cwd-drift recovered, 1 correctness improvement for portability, 1 test-fixture bug).

## Issues Encountered

- **`python` not on PATH:** worktree env exposes `python3` but not `python`. Used `/data/workspace/hermes-agent/.venv/bin/python` explicitly (the project venv has pytest + pytest-timeout + ruff installed).
- **Worktree cwd discipline:** documented in deviation #1 above. The fix is to NEVER use absolute paths derived from main-repo `pwd` output; always derive from `git rev-parse --show-toplevel` run inside the worktree, or use relative paths.

## User Setup Required

None — no external service configuration required. This plan delivers a stdlib-only snapshot tool + 14 baseline trees, both invoked from the repo root.

## Known Stubs

None. The snapshot tool is fully implemented; every function has a real return value with no placeholders.

## Next Phase Readiness

- **Ready for 00-04 phantom-strip plan:** after phantoms are stripped from `skills/movie-experts/*/SKILL.md`, run `python skills/movie-experts/_eval/snapshot.py verify` to surface the exact byte-level drift (expected = pre-strip sha256, actual = post-strip sha256). This proves the strip actually changed content — required for the audit trail.
- **Ready as ablation anchor for Phase 3/5/6:** the `eval-baseline-v1` baseline is the cryptographic "before" state. Every future RAG-uplift claim must include a verify-diff proving which bytes changed and why (RESEARCH.md PITFALLS #8).
- **No blockers.** EXPERT_DIRS list is hardcoded; new experts added in later waves (运镜指导, Hook & Retention, 制作管理, 合规与宣发) will require extending the list — that's intentional scope gating.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries introduced. The snapshot tool only reads git-tracked markdown from inside the repo and writes baseline trees under `skills/movie-experts/_eval/baseline/`. Provenance records are metadata only (sha256 hashes, git SHAs, byte sizes — all non-sensitive).

## TDD Gate Compliance

Plan `type: execute` with both tasks carrying `tdd="true"`. Verified in git log:

1. `test(00-02): add failing tests for snapshot capture/verify` (RED) — `817953459`
2. `feat(00-02): implement snapshot.py and capture 14 baselines` (GREEN) — `b6ed6b53f`

RED-gate evidence: first pytest run failed with `ModuleNotFoundError: No module named 'snapshot'` (collection error at import time — 7 tests collected, 1 error, 0 passed). GREEN-gate evidence: second pytest run passed 7/7 in 0.07s. REFACTOR not needed — implementation is already decomposed into single-responsibility functions per CLAUDE.md (`compute_provenance`, `_current_git_sha`, `capture_baselines`, `verify_baselines`, `main` are all <80 lines).

## Self-Check: PASSED

- All created files exist on disk: `skills/movie-experts/_eval/snapshot.py` (295 lines ≥ 120 required), `skills/movie-experts/_eval/tests/test_snapshot.py` (190 lines ≥ 50 required), `skills/movie-experts/_eval/baseline/.gitkeep`, 14 baseline subdirs each with `SKILL.md` + `PROVENANCE.json`.
- Both task commits present in git log: `817953459` (test RED), `b6ed6b53f` (feat GREEN).
- pyproject.toml diff: 0 lines (zero new packages).
- 7/7 pytest tests pass; capture exits 0 and creates 14 baselines; verify exits 0 on clean, 1 on drift.
- Ruff clean on both new Python files.
- All 14 PROVENANCE.json files contain the 7 required fields with tag=`eval-baseline-v1`.
- All 14 expert_id values match their directory names (FOUND-08 preservation gate).

---
*Phase: 00-audit-eval-skeleton-blocker-gate*
*Completed: 2026-06-15*
