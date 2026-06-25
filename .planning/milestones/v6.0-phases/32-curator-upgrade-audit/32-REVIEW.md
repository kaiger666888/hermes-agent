---
phase: 32-curator-upgrade-audit
reviewed: 2026-06-25T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - agent/curator.py
  - agent/curator_audit.py
  - agent/evolution/evol02_generator.py
  - hermes_cli/curator.py
  - hermes_cli/feedback.py
findings:
  critical: 3
  warning: 7
  info: 6
  total: 16
status: issues_found
---

# Phase 32: Code Review Report

**Reviewed:** 2026-06-25
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Reviewed the CURATE-04 audit log, CURATE-05 auto-apply path, EVOL-02 multi-instruction
generator, and the CLI wrappers. The structural invariants are largely honored:

- **P31 `TestNonBypassableHumanInLoop` PRESERVED** — `apply_patch_transaction` is called
  ONLY from `hermes_cli/feedback.py:894` (`_cmd_approve`). `hermes_cli/curator.py` routes
  every apply through `_cmd_approve` (verified via grep — zero direct callers).
- **Runtime isolation PRESERVED** — `agent/curator.py` and `agent/curator_audit.py` have
  ZERO module-level `from agent.evolution` / `import agent.evolution` imports. All
  evolution imports are lazy, inside function bodies.
- **SC-6 regression** — pre-v6 prune/consolidate behavior preserved in the no-feedback
  case; feedback-scan is additive and gated by `not dry_run`.

However, three BLOCKER defects ship in this implementation:

1. **CURATE-05 is dead code** — no production path ever sets `auto_apply_eligible=True`,
   so `hermes curator auto-apply-eligible` can never apply anything.
2. **`hermes curator audit-log --since 2026-06-01` silently drops every entry** — naive
   vs aware datetime `TypeError` is caught as "unparseable ts" and the entry is skipped.
3. **`current_files` keys are HERMES_HOME-relative paths**, but EVOL-02 LLM is told these
   are "repo-relative paths" — semantically wrong prompt that produces diffs against
   `.hermes/skills/...` instead of `skills/movie-experts/...`.

Multiple WARNINGs around audit-log atomicity, broad exception catching, dead defensive
code, and missing CLI `retract` choice round out the findings.

## Critical Issues

### CR-01: CURATE-05 auto-apply is unreachable — `auto_apply_eligible` is never True

**File:** `agent/curator.py:1784` and `hermes_cli/feedback.py:694-706`
**Issue:**
`PatchRecord.auto_apply_eligible` defaults to `False` (queue.py:116). The two producers
of pending patches are:

1. `_feedback_scan_phase` in `agent/curator.py:1773-1786` — unconditionally sets
   `auto_apply_eligible=False` (commented "Bundled NEVER auto-apply eligible (T-32-05)",
   but the code applies this to ALL skills including agent-created).
2. `_cmd_evolve` in `hermes_cli/feedback.py:694-706` — does not pass `auto_apply_eligible`,
   so it inherits the schema default `False`.

The CURATE-05 consumer `_cmd_auto_apply_eligible` (`hermes_cli/curator.py:707-711`) filters:
```python
if not p.auto_apply_eligible:
    skipped.append((p.patch_id, p.skill_id, "not marked eligible"))
    continue
```
Therefore `hermes curator auto-apply-eligible` will ALWAYS print `eligible for auto-apply (0)`
and skip every pending patch with reason "not marked eligible".

Compounding this: even if `auto_apply_eligible` were True, `_feedback_scan_phase` writes
`eval_gate_score={}` (no gate is run), so `_cmd_auto_apply_eligible:725` reads
`mean_delta=0.0` and skips on the second signal too.

The VALIDATION.md for CURATE-05 is marked "pending" — the requirement was never
exercised end-to-end. CURATE-05 is effectively unimplemented.

**Fix:**
The feedback-scan phase needs to (a) compute a real confidence score and (b) set
`auto_apply_eligible=True` for agent-created skills that pass both signals. Sketch:

```python
# In _feedback_scan_phase, after generating the diff and BEFORE PatchRecord construction:
bundled = is_bundled(skill_id)
confidence = None
auto_apply = False
if not bundled:
    # CURATE-05 requires the eval gate; the scan currently skips it. Either
    # invoke _run_eval_gate here or compute a stub-score from insight.evidence_chain.
    evidence_count = len(insight.evidence_chain)
    confidence = _compute_confidence(
        eval_score={},  # gate not run — signal will fail until wired
        evidence_count=evidence_count,
        min_delta=get_auto_apply_min_delta(),
        min_evidence=get_auto_apply_min_evidence(),
    )
    # Until the gate is wired, auto_apply stays False even for agent-created.
    auto_apply = False

record = PatchRecord(
    ...
    auto_apply_eligible=auto_apply,
    confidence_score=confidence,
)
```

The deeper fix is to either (a) wire the eval gate into `_feedback_scan_phase` so
`eval_gate_score` is populated, or (b) document that CURATE-05 only consumes patches
produced by `hermes feedback evolve` (which runs the gate) AND patch the `evolve`
handler to set `auto_apply_eligible=True` when the agent-created skill's signals pass.

### CR-02: `audit-log --since <naive-date>` silently drops every entry

**File:** `agent/curator_audit.py:380-390`
**Issue:**
The CLI help (curator.py:971) suggests `--since 2026-06-01`. That string parses via
`datetime.fromisoformat` to a NAIVE datetime (no tzinfo). Audit entries always have
AWARE timestamps (`datetime.now(timezone.utc).isoformat()` → `+00:00` suffix).

At line 389 `if entry_ts < since_dt:` raises `TypeError: can't compare offset-naive and
offset-aware datetimes`. The broad `except (ValueError, TypeError):` at line 383
catches this and logs `"audit entry %s has unparseable ts=%r — skipping"` — but the
timestamp IS parseable (line 382 succeeded); only the comparison failed. The entry is
silently dropped.

Result: `hermes curator audit-log --since 2026-06-01` returns an empty list for EVERY
operator regardless of actual log contents. Reproduced:

```
$ python -c "from datetime import datetime
since_dt = datetime.fromisoformat('2026-06-01')  # naive
entry_ts = datetime.fromisoformat('2026-06-25T14:30:00+00:00')  # aware
entry_ts < since_dt  # TypeError"
```

**Fix:**
Normalize both sides to aware (UTC) before comparison:

```python
if since_dt is not None:
    if since_dt.tzinfo is None:
        since_dt = since_dt.replace(tzinfo=timezone.utc)
    try:
        entry_ts = datetime.fromisoformat(entry.get("ts", ""))
    except (ValueError, TypeError):
        logger.warning("audit entry %s has unparseable ts=%r — skipping", ...)
        continue
    if entry_ts.tzinfo is None:
        entry_ts = entry_ts.replace(tzinfo=timezone.utc)
    if entry_ts < since_dt:
        continue
```

### CR-03: `_feedback_scan_phase` builds `current_files` with HERMES_HOME-relative paths but tells the LLM they are "repo-relative"

**File:** `agent/curator.py:1747` and `agent/evolution/evol02_generator.py:325-335`
**Issue:**
`_feedback_scan_phase:1747` computes the dict key as:
```python
rel = str(f.relative_to(get_hermes_home().parent))
```
For the default `~/.hermes`, this yields paths like `.hermes/skills/movie-experts/screenplay/SKILL.md`
— paths INTO `~/.hermes`, NOT into the git repo.

Meanwhile `emit_evol02_instructions:330-334` tells the LLM:
> "Target files available (repo-relative paths): ... Each instruction's 'file' MUST be one of the paths listed above."

The LLM dutifully emits `file=".hermes/skills/movie-experts/screenplay/SKILL.md"`.
`generate_patch_from_knowledge_point` then generates a diff with
`fromfile=f"a/{file_path}"` → `a/.hermes/skills/movie-experts/screenplay/SKILL.md`.
That diff will NOT apply cleanly via `apply_patch_transaction` (which expects
`skills/movie-experts/...`).

Worse: `get_hermes_home().parent` is a fragile assumption. If `HERMES_HOME` is set to
e.g. `/var/lib/hermes`, then `.parent` is `/var/lib` and the relative path becomes
`hermes/skills/...` — still not the repo layout. If `HERMES_HOME` is set to a path
whose parent is the filesystem root (e.g. `/hermes`), `relative_to("/")` yields
`hermes/skills/...` but with no leading `.hermes`.

**Fix:**
Resolve paths against the actual git repo root (like `hermes_cli/feedback.py:557-563`
does for the `evolve` CLI). The repo root is the canonical reference frame for unified
diffs. For bundled skills, this is `<repo>/skills/movie-experts/<skill>/...`. For
agent-created skills under HERMES_HOME, they should not be patched via the EVOL-02
generator at all (different deployment topology).

```python
# Replace the relative_to(get_hermes_home().parent) logic with:
from hermes_cli.feedback import _resolve_repo_root
repo_root = _resolve_repo_root()
# For bundled skills, read from the repo:
skill_dir = repo_root / "skills" / "movie-experts" / skill_id
...
rel = str(f.relative_to(repo_root))  # e.g. "skills/movie-experts/screenplay/SKILL.md"
```

If the design intent is to propose patches against the operator's writable copy
under `~/.hermes/skills/` (not the git tree), then `apply_patch_transaction` must
also be told to apply there — but that conflicts with the git-commit semantics
`apply_patch_transaction` is built around. This needs design clarification.

## Warnings

### WR-01: Audit log append is not crash-atomic

**File:** `agent/curator_audit.py:230-231`
**Issue:**
```python
with path.open("a", encoding="utf-8") as f:
    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
```
A single `write()` of a string longer than `PIPE_BUF` (4KB on POSIX) is NOT guaranteed
atomic. Audit entries with rich `eval_score` dicts and CN content in `feedback_ids` can
easily exceed 4KB. A crash or power loss mid-write leaves a partial JSON line, which
the NEXT `append_audit` will reject as `AuditChainError` ("audit log tail is malformed").
The chain becomes unappendable until an operator manually repairs the tail.

The docstring acknowledges "Single-process assumption" and defers file locking, but
crash-atomicity is a different concern from concurrency.

**Fix:**
Write to a temp file and `os.replace`, OR write the line then `f.flush()` + `os.fsync(f.fileno())`
before close. For a chain that derives its integrity from append-only semantics, fsync
is the minimum.

```python
line = json.dumps(entry, ensure_ascii=False) + "\n"
with path.open("a", encoding="utf-8") as f:
    f.write(line)
    f.flush()
    os.fsync(f.fileno())
```

(Note: `os.fsync` requires importing `os` — currently not imported in curator_audit.py.)

### WR-02: Broad `except (ValueError, TypeError)` masks the real failure in `read_audit`

**File:** `agent/curator_audit.py:383`
**Issue:**
The `try: entry_ts = datetime.fromisoformat(...)` block catches `ValueError, TypeError`,
but the `TypeError` can come from EITHER:
- `fromisoformat` actually failing to parse (legitimate "unparseable ts"), OR
- The subsequent `entry_ts < since_dt` comparison (naive vs aware — see CR-02).

The log message "has unparseable ts" is misleading for the second case. Split the
parse from the comparison so the diagnostic is accurate even after CR-02 is fixed.

**Fix:**
```python
try:
    entry_ts = datetime.fromisoformat(entry.get("ts", ""))
except (ValueError, TypeError):
    logger.warning("audit entry %s has unparseable ts=%r — skipping", ...)
    continue
# Comparison is now its own statement; CR-02 fix normalizes timezones first.
if entry_ts < since_dt:
    continue
```

### WR-03: `_scan_for_hot_skills` has dead defensive code and inconsistent key parsing

**File:** `agent/curator.py:1540-1544, 1556`
**Issue:**
Two concerns:

1. Lines 1540-1544 use an elaborate `getattr(getattr(store, "_index", {}), "get", lambda *a: {})("buckets", {})`
   chain that suggests `_index` might be something other than a dict. `FeedbackStore._index`
   is ALWAYS a `dict[str, Any]` after `__init__` (feedback_store.py:263, 707, 716, 720, 725,
   839). The defensive chain is dead code. The fallback at 1543-1544 is similarly dead.
   Just write `buckets = store._index.get("buckets", {})`.

2. Line 1556: `skill_id = ":".join(parts[:-2])` parses the bucket key by joining all
   but the last two `:`-separated parts. This DISAGREES with the canonical parsing in
   `feedback_store.py:508` (`b_skill, b_source, b_verdict = parts` — exactly 3 parts).
   The docstring at curator.py:1550 says the key is `"{skill_id}:{source}:{verdict}"`
   which is also 3 parts. If a skill_id ever contained a `:`, the two implementations
   would diverge. The lenient parse in curator.py would silently merge `skill_id:source`
   into the skill_id and treat the real source as part of the verdict — wrong counts.

**Fix:**
```python
buckets = store._index.get("buckets", {})
...
parts = key.split(":")
if len(parts) != 3:
    continue  # match feedback_store.py:508 strict parse
skill_id, _source, verdict = parts
```

### WR-04: Markdown-fence regex in `emit_evol02_instructions` over-strips content

**File:** `agent/evolution/evol02_generator.py:365-367`
**Issue:**
```python
import re
fence_re = re.compile(r"^```(?:json)?\s*\n?|\n?```\s*$", re.MULTILINE)
stripped = fence_re.sub("", content)
```
With `re.MULTILINE`, `^` and `$` match at every line boundary. This regex will strip
` ``` ` from ANY line that starts with backticks OR ends with backticks — including
backticks that appear legitimately inside JSON string values for `content_en` /
`content_zh` (e.g., when the LLM embeds a code sample in the proposed addition).

The fix is to ONLY strip the OUTER wrapping fences (first line and last line of the
whole content), not every line that matches.

Also: `import re` is inside the function body. Module-level imports are the convention.

**Fix:**
```python
# Top of module:
import re

# In the function:
_FENCE_WRAP_RE = re.compile(r"\A\s*```(?:json)?\s*\n(.*?)\n```\s*\Z", re.DOTALL)
m = _FENCE_WRAP_RE.match(content.strip())
stripped = m.group(1) if m else content
```

### WR-05: `_feedback_scan_phase` swallows ALL exceptions with a single broad `except Exception`

**File:** `agent/curator.py:1671, 1809-1815`
**Issue:**
The outer try/except at 1671 wraps the ENTIRE 140-line function body. The catch at
1809-1815 logs WARNING and returns an error dict. This catches:
- Legitimate setup failures (FeedbackStore init, LLM client init) — correctly logged.
- `KeyboardInterrupt`? No — `Exception` excludes `BaseException` subclasses.
- Logic bugs in the inner per-skill loop — but those are already caught by the
  per-insight try/except at 1801.

The concern: the broad outer catch makes it impossible to distinguish "the whole phase
failed because config is broken" from "a single insight failed inside the loop." The
per-skill and per-insight handlers already exist; the outer catch is too wide and hides
programming errors as "scan phase failed (non-fatal)."

**Fix:**
Narrow the outer try to just the setup (FeedbackStore, client, threshold read). Let
unexpected exceptions propagate to the caller (`_llm_pass`), which already has its own
try/except wrapper.

```python
def _feedback_scan_phase(start):
    # Setup: narrow exceptions
    try:
        from agent.feedback_store import FeedbackStore
        ...
        store = FeedbackStore(hermes_home=get_hermes_home())
    except Exception as exc:
        logger.warning("curator feedback-scan: init failed: %s", exc)
        return {"scanned": 0, "proposed": [], "error": str(exc)}

    hot_skills = _scan_for_hot_skills(...)
    if not hot_skills:
        return {"scanned": 0, "proposed": []}

    # Main loop: per-skill try/except (already exists at 1720-1730).
    # No outer catch needed — caller (_llm_pass) wraps this whole call.
```

### WR-06: `_resolve_skill_from_patch` scans `pending` first after a reject moves the patch to `rejected`

**File:** `hermes_cli/curator.py:553, 593-618`
**Issue:**
In `_cmd_reject_curator`, `_cmd_reject` is called FIRST (which moves the patch from
`pending.jsonl` to `rejected.jsonl`). Then `_resolve_skill_from_patch` is called to
recover the `skill_id` for the audit entry. It scans `pending`, then `applied`, then
`rejected` (3 file reads).

For the just-rejected patch, the first two reads return zero matches; only the third
read finds the record. This works but is wasteful (3 JSONL parses for one lookup).

More importantly: if `_cmd_reject` ever changes to move patches elsewhere (e.g., a
`retracted.jsonl`), this resolver will silently return `"unknown"` and the audit entry
will be recorded with a useless `skill_id`. The audit trail would still chain correctly
(sha256 is over the bytes), but the `skill_id` filter (`hermes curator audit-log --skill X`)
would never match.

**Fix:**
Either:
1. Re-order the scan to check `rejected` first when called from `_cmd_reject_curator`.
2. Better: have `_cmd_reject` return the `skill_id` directly so no resolver is needed.
3. Best: have `_cmd_approve` / `_cmd_reject` accept an audit callback that receives the
   full PatchRecord before it's mutated.

### WR-07: `git revert <commit_sha>` does not guard against option-injection

**File:** `hermes_cli/feedback.py:957-974`
**Issue:**
`args.commit_sha` comes from the CLI. The pre-check `git rev-parse --verify <commit_sha>`
validates that git can resolve the rev, but a value like `--help` would be parsed by
git as an option flag rather than a rev. `git rev-parse --verify --help` returns 0
(because `--help` short-circuits), then `git revert --help --no-edit` prints help and
exits 0 (no revert performed, but rc=0 is misleading).

Lower severity because the operator IS the user supplying the SHA (no privilege
boundary crossed), but it's still a defense-in-depth gap.

**Fix:**
Pass `--` to terminate option parsing:
```python
verify = subprocess.run(
    ["git", "rev-parse", "--verify", "--", args.commit_sha],
    ...
)
revert_result = subprocess.run(
    ["git", "revert", "--no-edit", "--", args.commit_sha],
    ...
)
```
Note the order: `--no-edit` BEFORE `--` so `--no-edit` is still parsed as an option,
and `--` ensures `args.commit_sha` is treated as a rev even if it starts with `-`.

## Info

### IN-01: CLI `--action` choices omit `retract`

**File:** `hermes_cli/curator.py:965-966`
**Issue:**
```python
choices=["propose", "approve", "reject", "apply", "rollback", "auto_apply"]
```
The `ACTION_VALUES` frozenset in `agent/curator_audit.py:68` also includes `"retract"`.
An operator who retracts a patch cannot filter the audit log for retractions via CLI —
argparse rejects `--action retract` as an invalid choice.

**Fix:**
Either add `"retract"` to the choices list, or drop `choices=` and let any string
through (forward-compat with new actions).

### IN-02: `hashlib`, `datetime as _dt`, `timezone as _tz` imported inline inside a loop

**File:** `agent/curator.py:1766-1767`
**Issue:**
```python
for insight in insights:
    try:
        ...
        import hashlib
        from datetime import datetime as _dt, timezone as _tz
```
`hashlib` and `datetime`/`timezone` are already imported at module top (line 29 imports
`datetime, timedelta, timezone`). The inline imports shadow the top imports with aliases
that only exist inside the loop body. Python caches module imports so this isn't a
performance issue, but it's confusing and inconsistent with the module's existing
top-level imports.

**Fix:**
Use the module-level imports directly:
```python
# At top of module (already there): from datetime import datetime, timedelta, timezone
# Inside the loop:
import hashlib  # add to module top
ts_unix = int(datetime.now(timezone.utc).timestamp())
```

### IN-03: `f.relative_to(get_hermes_home().parent)` swallows `ValueError` silently

**File:** `agent/curator.py:1747-1749`
**Issue:**
```python
try:
    rel = str(f.relative_to(get_hermes_home().parent))
    current_files[rel] = f.read_text(encoding="utf-8")
except (OSError, ValueError):
    pass
```
If a skill file lives OUTSIDE `get_hermes_home().parent` (e.g., HERMES_HOME is
`~/.hermes` but the file is a symlink to `/usr/share/...`), `relative_to` raises
`ValueError` and the file is silently skipped. The LLM never sees the file, never
proposes a patch for it, and no log records the skip. This is a quality issue — silent
data loss in the `current_files` map.

**Fix:**
Log at DEBUG when the skip happens:
```python
except (OSError, ValueError) as exc:
    logger.debug("feedback-scan: skipping %s (%s)", f, exc)
```

### IN-04: `re` imported twice in `agent/curator.py`

**File:** `agent/curator.py:27, 768`
**Issue:**
`import re` is at the top of the module (line 27). Inside `_parse_structured_summary`
(line 768), there's another `import re`. The inner one is dead — it shadows the
top-level import with the same module object.

**Fix:**
Remove the inner `import re` at line 768.

### IN-05: `_compute_confidence` is exported but never called by production code

**File:** `agent/curator.py:1597-1638`
**Issue:**
`_compute_confidence` is defined but a grep for callers shows it's only used in tests.
Per the CURATE-05 spec, this is the function that should compute the two-signal score
when proposing a patch for auto-apply. As implemented (see CR-01), `_feedback_scan_phase`
hard-codes `auto_apply_eligible=False` and `confidence_score=None` without ever calling
`_compute_confidence`.

**Fix:**
Wire `_compute_confidence` into the patch-creation path (part of the CR-01 fix). Until
then, the function is dead code masquerading as a feature.

### IN-06: `curator_audit.py` docstring says `retract` is a valid action but no API emits one

**File:** `agent/curator_audit.py:68-70`
**Issue:**
`ACTION_VALUES` includes `"retract"`. The module docstring (line 21-23) says "Retraction
= append a new entry with `action="retract"` referencing the original `entry_id`."
But no caller in the reviewed files ever invokes `append_audit(action="retract", ...)`.
The action is reserved-but-unused. This is fine if it's a forward-compat hook, but
should be documented as "reserved" rather than implied to be wired.

**Fix:**
Either add a `retract_audit(entry_id, ...)` helper that wraps `append_audit`, or add a
comment to `ACTION_VALUES` noting that `retract` is reserved for future use and currently
has no producer.

---

## Structural Findings (fallow)

None provided — no `<structural_findings>` block in the prompt.

## Narrative Findings (AI reviewer)

See Critical / Warning / Info sections above. The most actionable items:

1. **CR-01 (CURATE-05 dead code)** is the headline defect. Either wire the eval gate
   into `_feedback_scan_phase` and set `auto_apply_eligible=True` for passing
   agent-created skills, or document that CURATE-05 is pending a follow-up phase and
   mark `_cmd_auto_apply_eligible` as experimental.
2. **CR-02 (`--since` bug)** is a one-line fix (normalize tz) that unblocks the
   documented operator workflow.
3. **CR-03 (path resolution)** requires design clarification: is the EVOL-02 generator
   meant to patch the git tree, the HERMES_HOME tree, or both?

The structural invariants (P31 non-bypassable human-in-loop, runtime isolation, SC-6
regression) are intact. The defects are in the new v6 logic, not in regressions of
existing behavior.

---

_Reviewed: 2026-06-25_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
