---
phase: 33-observability-integration-close-out
reviewed: 2026-06-25T00:00:00Z
depth: quick
files_reviewed: 1
files_reviewed_list:
  - hermes_cli/curator.py
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 33: Code Review Report

**Reviewed:** 2026-06-25
**Depth:** quick
**Files Reviewed:** 1 (`hermes_cli/curator.py` — `stats` subcommand additions, lines 807-1231 + argparse wiring 1434-1469)
**Status:** issues_found

## Summary

Reviewed the read-only `hermes curator stats` subcommand (OBS-01/02/03) added in Phase 33 Plan 01. Quick pattern scan found no secrets, no dangerous functions, no empty catch blocks, no `open()` calls without `encoding=` (the module has zero direct `open()` calls — it delegates to FeedbackStore / read_queue / read_audit). Sparkline normalization is verified robust against empty list, single value, all-identical values, and negative spans.

`--json` information-disclosure invariant (T-33-01) is correctly honored in OBS-01: the JSON payload includes only `verdict_buckets`, `patch_count`, `eval_trend_count`, `recent_commit_shas` — no correction text, no `feedback_ids`, no `output_snapshot`. Good.

Three warnings and three info items found. No blockers.

## Warnings

### WR-01: `--all` and `--by-source` silently ignored when both passed alongside `skill_id`

**File:** `hermes_cli/curator.py:1198-1221`
**Issue:** The dispatch order in `_cmd_stats` checks `--all` first, then `--by-source`, then `skill_id`. If a user runs `hermes curator stats foo --all`, the `--all` branch wins and `skill_id="foo"` is silently dropped. Likewise `hermes curator stats foo --by-source` drops `skill_id` and routes to source breakdown with no `skill_filter` (the `--skill` flag is separate from the positional `skill_id`). This is a UX bug: a positional arg the user typed has no effect and no warning is emitted.

**Fix:**
```python
skill_id = getattr(args, "skill_id", None)
all_skills = bool(getattr(args, "all_skills", False))
by_source = bool(getattr(args, "by_source", False))
# Detect ambiguity and warn rather than silently drop.
selected_modes = sum([all_skills, by_source, bool(skill_id)])
if selected_modes > 1:
    print(
        "curator stats: ambiguous — pick ONE of <skill_id>, --all, or "
        "--by-source (got multiple). Ignoring extras.",
        file=sys.stderr,
    )
# Then proceed with current dispatch order, but at least the operator is warned.
```
Alternatively, argparse `mutually_exclusive_group()` would reject this at parse time — cleaner but changes the CLI contract.

### WR-02: `--all` cross-skill view zero-feedback list is hardcoded to `movie-experts/` only

**File:** `hermes_cli/curator.py:1047-1060`
**Issue:** `_render_cross_skill_view` only scans `hermes_home / "skills" / "movie-experts"` for the zero-feedback list. Bundled skills under other categories (`software-development/`, `creative/`, `agent-operations/`, etc. — present in the codebase per CLAUDE.md) are never considered, so the "Zero-feedback bundled skills" report is structurally incomplete and the count is misleading. A user auditing observability across the whole skill catalog will see only the movie-experts subset.

**Fix:** Walk all category directories under `skills/`:
```python
bundled: list[str] = []
skills_root = hermes_home / "skills"
try:
    if skills_root.is_dir():
        for cat_dir in skills_root.iterdir():
            if not cat_dir.is_dir() or cat_dir.name.startswith((".", "_")):
                continue
            for p in cat_dir.iterdir():
                if p.is_dir() and not p.name.startswith(("_", ".")):
                    bundled.append(p.name)
        bundled = sorted(set(bundled))
except OSError as exc:
    logger.warning("failed to scan bundled skills for zero-feedback list: %s", exc)
```
If the project genuinely scopes feedback to movie-experts only, document the assumption in the help text and the table caption.

### WR-03: `_render_source_breakdown` queries `store.summary()` once per source — `_collapse_verdicts` called 3 times

**File:** `hermes_cli/curator.py:1116-1121`
**Issue:** OBS-03 loops over the three known `_SOURCES` and calls `store.summary(source=source, skill_id=skill_filter)` three separate times, each of which re-reads and re-aggregates from disk (FeedbackStore.summary is not cached per call). Then `_collapse_verdicts` runs on each result. While this is "out of scope for v1" on performance grounds, it is also a **correctness concern**: if FeedbackStore mutates between the three calls (a `/feedback` write happens concurrently), the three rows can be inconsistent — counts that should sum to a known total won't. A single `store.summary(skill_id=skill_filter)` call (with no `source` filter) would return all sources in one snapshot and the per-source split could be computed from the bucket keys without re-querying.

**Fix:** Issue one summary call, then partition by `parts[1]` (the source segment) client-side:
```python
full = store.summary(skill_id=skill_filter)
per_source: dict[str, dict[str, int]] = {s: {"good":0,"needs_work":0,"bad":0} for s in _SOURCES}
for key, bucket in full.items():
    parts = key.split(":")
    if len(parts) != 3:
        continue
    skill, source, verdict = parts
    if source in per_source and verdict in per_source[source]:
        per_source[source][verdict] += int(bucket.get("count", 0))
```

## Info

### IN-01: `_VERDICT_STYLES` lookup in OBS-03 uses dict but verdicts come from a fixed tuple

**File:** `hermes_cli/curator.py:1148-1156`
**Issue:** Each row constructs `style_good`, `style_nw`, `style_bad` inside the loop body (3 dict lookups × 3 sources = 9 lookups) when they are loop-invariant constants. Minor; hoist them above the `for source in _SOURCES:` loop for clarity. No bug, just cleanup.

### IN-02: `recent_commit_shas` in JSON payload unbounded

**File:** `hermes_cli/curator.py:940-943`
**Issue:** `recent_commits` collects every `commit_sha` from `trend_entries`, which is itself bounded by `runs` (default 10). So in practice the list is small. But the name `recent_commit_shas` promises "recent" without bounding — if `runs` is set very large via flag, the JSON array grows unbounded. Consider capping to e.g. `recent_commits[:5]` and renaming to `last_5_commit_shas` for explicit semantics. Documentation nit, not a bug.

### IN-03: `_cmd_stats` no-args path returns exit 0 with usage hint to stdout

**File:** `hermes_cli/curator.py:1222-1231`
**Issue:** When `stats` is invoked with no mode argument, the code prints a usage hint to **stdout** and returns 0. Conventional CLI behavior for "ambiguous / missing required arg" is to print usage to **stderr** and return non-zero (typically 2). Returning 0 may fool shell scripts (`hermes curator stats > /dev/null && echo ok`) into thinking stats succeeded. Minor UX consistency issue.

**Fix:**
```python
import sys
print(
    "usage: hermes curator stats [<skill_id>] [--all] [--by-source] ...",
    file=sys.stderr,
)
return 2
```

---

_Reviewed: 2026-06-25_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: quick_
