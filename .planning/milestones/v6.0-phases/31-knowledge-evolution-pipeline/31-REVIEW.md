---
phase: 31-knowledge-evolution-pipeline
reviewed: 2026-06-24T22:50:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - agent/evolution/insights.py
  - agent/evolution/diff_generator.py
  - agent/evolution/queue.py
  - agent/evolution/apply.py
  - hermes_cli/feedback.py
findings:
  critical: 5
  warning: 7
  info: 4
  total: 16
status: issues_found
---

# Phase 31: Code Review Report

**Reviewed:** 2026-06-24T22:50:00Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

The Phase 31 Knowledge Evolution Pipeline (`agent/evolution/*` + CLI handlers in `hermes_cli/feedback.py`) is well-documented and structurally sound on the runtime-isolation axis (no Hermes runtime module imports `agent.evolution`). The atomic-transaction design and the non-bypassable human-in-loop story (sole-caller structural invariant) are correct on paper.

However, the implementation has **two P0 integration defects that make the primary user-facing path non-functional**, plus several correctness gaps that silently weaken the security invariants the module claims to enforce (SC-5 byte-intact, SC-6 additive-only, EVOL-04 non-bypassable). The most damaging:

1. **`_run_eval_gate` never passes the required `--baseline-answers` / `--candidate-answers` to gate.py.** Every gate invocation hits `parser.error()` → exit code 2 → verdict="fail". The pipeline can never produce a queue-able patch — the entire EVOL-03 queue is dead on arrival.
2. **`FeedbackStore.query()` returns `list[FeedbackRecord]` (Pydantic objects), but `insights.py` and `feedback.py` consume it as `list[dict]`.** The live LLM aggregation path serializes Pydantic objects with `json.dumps()` (which raises `TypeError`) and reads fields via `.get("record_id")` (which raises `AttributeError`). The aggregation prompt and dry-run path both crash.

Beyond these, the FOUND-08 byte-intact check is run against the wrong baseline (see CR-03), the additive-only check runs AFTER the working tree is mutated (CR-04), and the commit-message builder does not sanitize feedback IDs (CR-05 — git commit-message injection).

## Critical Issues

### CR-01: `_run_eval_gate` omits required gate.py args → pipeline cannot produce patches

**File:** `hermes_cli/feedback.py:451-463`
**Issue:** `_run_eval_gate` builds the argv list as:
```python
result = subprocess.run(
    [
        sys.executable,
        str(gate_path),
        "--patch", str(patch_path),
        "--skill", skill_id,
        "--reports-dir", str(reports_dir),
    ],
    ...
)
```
But `gate.py:1459-1462` requires `--baseline-answers` AND `--candidate-answers` for any non-`--rebuild-baseline` run, and calls `parser.error(...)` (which exits with code 2) when they are missing. As a result **every** `_run_eval_gate` call returns non-zero, every insight lands in `failed_gate.jsonl`, and `passed` in `_cmd_evolve` is permanently 0. The entire EVOL-03 queue lifecycle (`queue.jsonl`, `applied.jsonl`, `approve`, `reject`) can never be exercised from the CLI.

There is a secondary defect here: gate.py uses exit-code 2 for `fail_regression` (`VERDICT_TO_EXIT` line 61-65), but `argparse` `parser.error()` ALSO exits with code 2. The `else: verdict = "fail"` branch in `_run_eval_gate` therefore masks the missing-args case as a normal gate failure — operators will see "patches failed gate" in logs rather than the real cause (missing args).

**Fix:**
The gate needs baseline + candidate answers. Either pre-generate them inside `_cmd_evolve` (calling the gate's answer-generation path) or add explicit CLI args the operator must supply. Minimum-viable fix that surfaces the real cause:

```python
# _run_eval_gate — fail loudly if the caller hasn't supplied answers.
if baseline_answers_path is None or candidate_answers_path is None:
    raise SystemExit(
        "eval gate requires pre-generated answers; pass "
        "--baseline-answers / --candidate-answers to `hermes feedback evolve`"
    )
result = subprocess.run(
    [
        sys.executable,
        str(gate_path),
        "--patch", str(patch_path),
        "--skill", skill_id,
        "--reports-dir", str(reports_dir),
        "--baseline-answers", str(baseline_answers_path),
        "--candidate-answers", str(candidate_answers_path),
    ],
    ...
)
```
And the caller (`_cmd_evolve`) must either generate candidate answers by applying the patch + invoking the runner, or refuse to gate until the operator supplies them. Without this, the whole phase is non-functional.

---

### CR-02: `FeedbackStore.query()` returns Pydantic objects but callers treat them as dicts

**File:** `agent/evolution/insights.py:217-218, 268, 277`; `hermes_cli/feedback.py:526, 554`
**Issue:** `FeedbackStore.query()` is typed `list[FeedbackRecord]` (Pydantic BaseModel instances — see `agent/feedback_store.py:919-988` and `agent/feedback_schema.py:184`). But:

- `insights.py:217-218` builds the user prompt with `json.dumps(feedback_details, indent=2, ensure_ascii=False)`. `json.dumps` on a list of Pydantic models raises `TypeError: Object of type FeedbackRecord is not JSON serializable`. The live LLM aggregation path is unreachable.
- `feedback.py:526-529` passes `store.query(...)` straight into `aggregate_feedback`, which (per above) will crash inside `build_aggregation_user_prompt`.
- `feedback.py:554` does `feedback[0].get("record_id", ...)` on the dry-run path — Pydantic models have no `.get()` method; this raises `AttributeError`.
- `insights.py:268-273` also calls `store.summary(skill_id=...)` — that returns `dict[str, dict[str, Any]]` which is fine, but the `feedback_details` payload definitely is not.

`FeedbackRecord` also does not expose a `record_id` field at all — it is computed by `FeedbackStore._make_record_id()` (`feedback_store.py:273`) and is not stored on the model. So even after fixing the dict/object confusion, the evidence_chain IDs the LLM is told to cite cannot be extracted from the records passed to it.

**Fix:**
1. Serialize records to dicts before prompt construction. In `aggregate_feedback`:
   ```python
   records = store.query(skill_id=skill_id)
   if not records:
       return []
   records_as_dicts = [
       {**r.model_dump(), "record_id": store._make_record_id(r)}
       for r in records
   ]
   summary = store.summary(skill_id=skill_id)
   user_prompt = build_aggregation_user_prompt(
       skill_id=skill_id, feedback_summary=summary, feedback_details=records_as_dicts,
   )
   ```
2. In `feedback.py:554`, replace the dict access with the typed object: `feedback[0].skill_id` (or use `store._make_record_id(feedback[0])` if a record_id is genuinely needed for the stub evidence_chain).
3. Consider exposing `record_id` as a property on `FeedbackRecord` or as a sibling tuple returned by `query()` to avoid leaking the private `_make_record_id` helper across module boundaries.

---

### CR-03: FOUND-08 byte-intact check is run against post-apply state, but the "before" block for patch-added files is wrong

**File:** `agent/evolution/apply.py:379-416`
**Issue:** The pre-apply frontmatter extraction loop:
```python
for f in files:
    abs_path = repo_root / f
    if abs_path.exists():
        content_before = abs_path.read_text(encoding="utf-8")
        frontmatter_before[f] = _extract_frontmatter_block(content_before)
    else:
        # Patch-added file — no prior frontmatter to preserve.
        frontmatter_before[f] = ""
```
For a patch that CREATES a new file, `frontmatter_before[f] = ""`. After apply, `verify_found08_byte_intact("", abs_after)` calls `_extract_frontmatter_block(after_content)` and compares to `""`. If the new file contains a frontmatter block, the check **fails** (correctly preventing frontmatter on new files). If the new file has no frontmatter, the check passes (correctly). But there is a worse case:

For an EXISTING file with NO frontmatter (e.g., a non-`SKILL.md` ref like `references/notes.md`), `_extract_frontmatter_block` returns `""`. After a patch that adds a `---\nkey: value\n---\n` frontmatter block to the top of that file, `verify_found08_byte_intact("", after_path)` will fail with a confusing "frontmatter bytes drifted" error — even though no frontmatter existed before, so SC-5 (preserve existing frontmatter bytes) is trivially satisfied for that file. This is a false-positive that will reject legitimate additions to files that previously had no frontmatter.

The deeper issue: the FOUND-08 invariant ("frontmatter bytes must not drift") is only meaningful for files that HAD frontmatter. Applying it to files without frontmatter is incorrect.

**Fix:**
```python
def verify_found08_byte_intact(
    frontmatter_block_before: str, skill_md_path_after: Path,
) -> bool:
    # If the file had no frontmatter before, there is nothing to preserve.
    # SC-5 only constrains files that had frontmatter to begin with.
    if not frontmatter_block_before:
        return True
    after_content = skill_md_path_after.read_text(encoding="utf-8")
    after_block = _extract_frontmatter_block(after_content)
    return frontmatter_block_before == after_block
```

---

### CR-04: Additive-only check runs AFTER `git apply` mutates the working tree

**File:** `agent/evolution/apply.py:394-438`
**Issue:** The transaction ordering is:
1. `git apply --check` (step 3, no mutation)
2. extract frontmatter (no mutation)
3. **`git apply`** (step 4 — **WORKING TREE NOW MUTATED**)
4. FOUND-08 check (step 5a)
5. **`verify_additive_only` check (step 5b — runs AFTER mutation)**

The additive-only check is a pure text analysis of the patch — there is no reason it cannot run BEFORE `git apply`. Running it after means a non-additive patch (e.g., one that rewrites protected ref bytes) actually mutates the working tree and must then be reverted via `git checkout --` / `git clean -f`. While the revert path exists, this is needlessly risky:

- If the revert itself fails (`revert_files` raises), the working tree is left dirty with the offending bytes already written — a real data-integrity risk for protected refs (SC-6). The operator now has a corrupted v4/v5 ref checked out, and the "manual recovery required" message does not tell them the protected ref was mutated.
- The early-out `git apply --check` only validates patch SYNTAX, not content semantics — it does not catch removals.

**Fix:** Move `verify_additive_only` to BEFORE step 4:
```python
# Step 3.5: additive-only check (pure text analysis — no mutation risk).
patch_text = patch_path.read_text(encoding="utf-8")
is_additive = verify_additive_only(patch_text)
if not is_additive:
    touches_protected = any(
        any(protected in f for protected in protected_refs) for f in files
    )
    if touches_protected:
        raise ApplyError(
            f"SC-6 violation: patch is not additive-only and touches a "
            f"protected v4/v5 ref (files={files})"
        )
    raise ApplyError(
        f"patch is not additive-only (EVOL-02 scope discipline — "
        f"evolution patches only ADD content; files={files})"
    )

# Step 4: NOW mutate the working tree.
applied = False
try:
    subprocess.run(["git", "apply", str(patch_path)], ...)
```
This preserves the transaction semantics (still atomic via the revert-on-failure path) while ensuring SC-6 is enforced BEFORE any byte of a protected ref is touched.

---

### CR-05: Commit-message builder does not sanitize feedback IDs / insight summary → git commit-message injection

**File:** `agent/evolution/apply.py:284-308`; consumed at `hermes_cli/feedback.py:834-843`
**Issue:** `build_commit_message` interpolates operator- and LLM-controlled strings directly into the commit subject:
```python
subject = insight_summary[:72]
feedback_str = ",".join(feedback_ids) if feedback_ids else "none"
eval_str = f"{eval_verdict}:{eval_mean_delta:.2f}"
return (
    f"feat(evolution): {subject} | "
    f"feedback: {feedback_str} | "
    f"eval: {eval_str}"
)
```
- `insight_summary` is `match.llm_rationale[:72]` — LLM-controlled text. An LLM that emits a rationale containing `\n` would break the commit into a multi-line message (git would reject it via `--allow-empty-message` semantics, but `git commit -m "...\n..."` happily accepts embedded newlines, producing a forged commit body).
- `feedback_ids` come from `insight.evidence_chain`, which the LLM populated from feedback `record_id`s. A malicious or malformed feedback record whose `record_id` contains `|` or `\n` would corrupt the machine-parseable format that P32's audit log + P33's observability dashboard rely on. Worse, a feedback_id containing shell-significant bytes (the commit runs via `subprocess.run(["git", "commit", "-m", msg], ...)` — argv, not shell — so shell injection is contained, but git's own message parsing is not).
- `eval_verdict` is `str(...)` of a dict value — could be arbitrary text if gate.py's report JSON is malformed.

There is no validation that `feedback_ids` matches the expected `fb_<skill>_<ts>_<sha>` shape, and no rejection of `\n`, `|`, or other structural bytes.

**Fix:**
```python
import re

_FEEDBACK_ID_RE = re.compile(r"^[A-Za-z0-9_\-:]{1,64}$")
_SUBJECT_SANITIZED_RE = re.compile(r"[\r\n]")

def build_commit_message(
    *, insight_summary, feedback_ids, eval_verdict, eval_mean_delta,
) -> str:
    # Sanitize subject: strip newlines, truncate to 72 chars.
    subject = _SUBJECT_SANITIZED_RE.sub(" ", insight_summary)[:72].strip()
    # Validate feedback_ids against a strict pattern; drop violators.
    safe_ids = [fid for fid in feedback_ids if _FEEDBACK_ID_RE.match(fid)]
    feedback_str = ",".join(safe_ids) if safe_ids else "none"
    # eval_verdict must be one of the known gate verdicts.
    if eval_verdict not in ("pass", "fail_mean", "fail_regression",
                            "inconclusive", "internal_error", "unknown"):
        eval_verdict = "unknown"
    eval_str = f"{eval_verdict}:{eval_mean_delta:.2f}"
    return f"feat(evolution): {subject} | feedback: {feedback_str} | eval: {eval_str}"
```

---

## Warnings

### WR-01: `_resolve_repo_root` matches ANY `.git` directory — could target the wrong repo

**File:** `hermes_cli/feedback.py:373-386`
**Issue:** `_resolve_repo_root` walks up from `cwd` looking for `(candidate / ".git").exists()`. On systems where the operator runs the CLI from a subdirectory of an unrelated git repo (e.g., a dotfiles repo containing `~/.config`), the walk would stop at the wrong `.git`. More importantly, `.git` can also be a FILE (git worktree / submodule) pointing elsewhere — `exists()` returns True for both, but the semantics differ.

**Fix:** Use `git rev-parse --show-toplevel` instead, which is authoritative:
```python
def _resolve_repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        raise SystemExit(
            "must run inside the hermes-agent git repo "
            "(git rev-parse --show-toplevel failed)"
        )
    return Path(result.stdout.strip())
```

---

### WR-02: `move_patch` non-atomic across the two files (append + rewrite)

**File:** `agent/evolution/queue.py:253-258`
**Issue:** The function does:
1. `_append_jsonl(evolution_dir / dest_filename, raw)` — append to applied/rejected
2. `_atomic_rewrite_jsonl(queue_path, remaining)` — rewrite queue

If the process crashes between steps 1 and 2, the patch appears in BOTH `queue.jsonl` AND `applied.jsonl`. On the next `read_queue(status="pending")` the operator sees a patch that has already been applied — re-approving it would call `apply_patch_transaction` again, which would fail the dirty-tree guard (since the prior apply committed), but the queue state is corrupt. The single-process assumption (RESEARCH Pitfall 5) does not save you from a Ctrl+C between two filesystem writes.

**Fix:** Reverse the order — remove from queue FIRST, then append to destination. That way a crash leaves the patch "in flight" (neither pending nor applied), which the operator can recover from manually by re-running. Better still: wrap both writes in a single transactional helper that writes the new queue + new destination atomically via temp + rename.

```python
# Safer order: remove from queue first. If we crash before the append,
# the patch is "lost" from the queue but recoverable from insights.jsonl
# + git history. A duplicate is worse than a loss here.
_remaining = [r for j, r in enumerate(records) if j != target_idx]
_atomic_rewrite_jsonl(queue_path, _remaining)
_append_jsonl(evolution_dir / dest_filename, raw)
```

---

### WR-03: `_read_jsonl` swallows malformed lines silently at WARNING — data loss risk for applied.jsonl

**File:** `agent/evolution/queue.py:138-167`
**Issue:** `_read_jsonl` logs malformed lines at WARNING and skips them. For `queue.jsonl` this is acceptable (operator can re-queue). But for `applied.jsonl`, a malformed line means a patch that WAS applied (and committed to git) is now invisible to `read_queue(status="applied")` — the operator cannot rollback what they cannot see. The audit trail silently loses entries.

**Fix:** For audit-critical files (`applied.jsonl`, `rejected.jsonl`, `insights.jsonl`), either raise on malformed lines, or move malformed lines to a sidecar `<filename>.corrupt` rather than silently skipping.

---

### WR-04: `generate_additive_diff` marker search can match inside frontmatter

**File:** `agent/evolution/diff_generator.py:63-77`
**Issue:** The marker search walks all lines, including the YAML frontmatter block. If the LLM proposes `insert_after_marker: "expert_id"` (a frontmatter key), the marker will match inside the frontmatter, the addition will be inserted INTO the frontmatter block, and SC-5 (frontmatter bytes preserved) will trip in `apply_patch_transaction` — but only AFTER the working tree is mutated (see CR-04). The LLM prompt in `insights.py:69-70` says "do NOT propose changes to the YAML frontmatter block", but there is no programmatic enforcement that the marker lands OUTSIDE the frontmatter.

**Fix:** In `generate_additive_diff`, after locating `insert_idx`, assert that the insertion point is AFTER the closing frontmatter `---`:
```python
# Reject insertions that would land inside the frontmatter block.
fm_end = _frontmatter_end_offset(current_lines)  # line index after closing ---
if fm_end is not None and insert_idx <= fm_end:
    raise ValueError(
        f"insert_after_marker {insert_after_marker!r} matches inside the "
        f"YAML frontmatter block — frontmatter is immutable (SC-5)"
    )
```

---

### WR-05: `verify_additive_only` accepts `\ No newline at end of file` lines as additions

**File:** `agent/evolution/apply.py:107-132`
**Issue:** Unified diffs use `\ No newline at end of file` as a marker line. This line starts with `\`, which does not match any of the skip rules (`---`, `+++`, `@@`, `-`, `+`, ` `). It falls through to the implicit "context" branch and is silently accepted. This is mostly harmless (the line is metadata, not content), but if a future change adds a `\\` prefix to actual content lines, they would also be silently accepted as context.

More importantly, the check at line 126 (`if line.startswith("-")`) runs BEFORE the check at line 129 (`if line.startswith("+")`). A line like `+++` was already skipped at line 113 — that is fine. But a line starting with `--` (a markdown horizontal rule in a diff context line that was somehow mis-prefixed) would be treated as a removal. The ordering is correct but fragile.

**Fix:** Add an explicit skip for `\` metadata lines:
```python
# Skip "\ No newline at end of file" metadata markers.
if line.startswith("\\"):
    continue
```

---

### WR-06: `_ensure_git_author` writes config without checking git version support for `--local`

**File:** `agent/evolution/apply.py:491-514`
**Issue:** The function calls `git config user.email <value>` without an explicit `--local`. While `git config <key> <value>` without a scope defaults to `--local` when inside a repo, this is implicit behavior. Combined with the dirty-tree check running `git status --porcelain` first (which guarantees we're in a repo), this is probably safe — but if `GIT_CONFIG_GLOBAL` or `GIT_CONFIG_NOSYSTEM` env vars are set in unusual ways, the implicit scope could surprise the operator.

**Fix:** Make the scope explicit:
```python
subprocess.run(
    ["git", "config", "--local", "user.email", _FALLBACK_AUTHOR_EMAIL],
    cwd=str(repo_root), check=True, ...
)
```

---

### WR-07: `_run_eval_gate` does not pass `--config` — uses built-in defaults that may diverge from gate_config.yaml

**File:** `hermes_cli/feedback.py:451-463`
**Issue:** `_run_eval_gate` does not pass `--config`, so gate.py uses built-in defaults from `gate.py` constants rather than the committed `skills/movie-experts/_eval/gate_config.yaml`. If the operator tunes thresholds in `gate_config.yaml`, those tunings are silently ignored by the evolution pipeline. (This is moot given CR-01, but worth flagging for the post-fix state.)

**Fix:** Auto-discover `gate_config.yaml` next to `gate.py` and pass it explicitly, or accept a `--gate-config` arg on `hermes feedback evolve`.

---

## Info

### IN-01: `apply_patch_transaction` catches bare `Exception` — masks ApplyError-vs-other distinction

**File:** `agent/evolution/apply.py:462-483`
**Issue:** The `except Exception as exc` clause catches all exceptions including `ApplyError` (which is then re-raised at line 481-482). The CLAUDE.md anti-patterns list calls out bare `except:` but permits `except Exception:` for best-effort paths — this is borderline because the transaction's correctness depends on EVERY exception triggering a revert. The re-raise logic is correct, but the code reads as if non-`ApplyError` exceptions get wrapped twice in error messages.

**Fix:** Split into two handlers:
```python
except ApplyError:
    # Already an ApplyError — revert + re-raise unchanged.
    if applied:
        revert_files(files, repo_root)
    raise
except Exception as exc:
    # Wrap unknown failures (subprocess errors, etc.) — revert + raise ApplyError.
    if applied:
        revert_files(files, repo_root)
    raise ApplyError(f"patch apply failed: {exc}") from exc
```

---

### IN-02: `_cmd_evolve` writes insights to insights.jsonl directly rather than via `append_insights` helper

**File:** `hermes_cli/feedback.py:585-589, 562-565`
**Issue:** The dry-run path (562-565) and live path (585-589) both open `insights.jsonl` and write JSON lines inline. The queue module exposes dedicated helpers (`append_patch`, `append_failed_gate`) for the other files but there is no `append_insight` for `insights.jsonl`. This leads to duplicated `with ... open("a", encoding="utf-8") as fh: fh.write(json.dumps(...) + "\n")` patterns and a subtle inconsistency: the queue helpers `mkdir(parents=True, exist_ok=True)`, but the inline writes assume the directory exists (which `_resolve_evolution_dir` does guarantee — so this is correct, just fragile).

**Fix:** Add `append_insight(record: dict, evolution_dir: Path) -> None` to `queue.py` and call it from both paths.

---

### IN-03: `_cmd_watch` swallows `KeyboardInterrupt` and returns 0, but never returns non-zero on watcher errors

**File:** `hermes_cli/feedback.py:267-274`
**Issue:** If `watch_inbox_kais` raises a non-`KeyboardInterrupt` exception (e.g., the inbox directory disappears mid-watch), the handler propagates it as an uncaught exception rather than returning a clean non-zero exit code. The `import` of `watch_inbox_kais` is also lazy inside the function — if the import itself fails (missing dep), the user sees a traceback rather than a clean error.

**Fix:** Wrap in try/except and surface errors cleanly:
```python
try:
    watch_inbox_kais(interval=args.interval)
except KeyboardInterrupt:
    return 0
except Exception as exc:
    print(f"watcher error: {exc}", file=sys.stderr)
    return 1
```

---

### IN-04: `_resolve_evolution_dir` uses `get_hermes_home()` correctly, but the lazy import inside the function is inconsistent with module-level style

**File:** `hermes_cli/feedback.py:389-399`
**Issue:** `_resolve_evolution_dir` imports `get_hermes_home` inside the function body to preserve the runtime-isolation invariant — but `get_hermes_home` lives in `hermes_constants`, which is a Hermes-runtime module that the CLI already imports unconditionally elsewhere. The lazy import here is cargo-culted from the `agent.evolution` lazy-import pattern, which IS necessary (those modules must not be loaded at CLI startup). For `hermes_constants` the lazy import adds complexity without benefit.

**Fix:** Move `from hermes_constants import get_hermes_home` to module top-level in `feedback.py`. (Verify no circular-import risk first — but `hermes_constants` is a leaf utility module with no inbound dependencies from `agent.evolution`.)

---

_Reviewed: 2026-06-24T22:50:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
