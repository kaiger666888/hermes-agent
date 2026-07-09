---
phase: 70-foundation-audit
reviewed: 2026-07-09T15:05:00Z
depth: standard
files_reviewed: 1
files_reviewed_list:
  - .planning/phases/70-foundation-audit/70-smoke.sh
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 70: Code Review Report

**Reviewed:** 2026-07-09T15:05:00Z
**Depth:** standard
**Files Reviewed:** 1
**Status:** issues_found

## Summary

`70-smoke.sh` is a small (80-line) bash smoke-test runner with 6 XCUT-01 assertions. Syntax is clean (`bash -n` passes), `set -euo pipefail` is correctly applied, the `grep -c ... || true` idiom is sound under `set -e`, and the REPO_ROOT resolution via `BASH_SOURCE` correctly handles the symlinked working tree. No shell-injection vectors (all paths are either repo-anchored or `$HOME/.hermes/config.yaml`).

However, three correctness/robustness issues degrade the assertions' fidelity:

1. **XCUT-01d uses a substring grep** (`grep -q "enabled: false"`) that false-positives on values like `enabled: falsey` or `enabled: false_value`. The assertion is currently green only because the actual config happens to read `enabled: false` followed by a comment.
2. **XCUT-01b's regex is too loose** — it matches any markdown line containing `skills/...SKILL.md`, including 3 JSON-block `"skill_path": "..."` echo entries and the Pitfall-5 explanation paragraph. The assertion claims "lists all 6 target SKILL.md files with sha256" but actually only counts lines containing the substring.
3. **XCUT-01c cross-repo pin check is a pure substring existence test** — it cannot detect whether a real git SHA pin exists, only that the repo name string appears somewhere.

Three minor info items: shebang usage hint, no `[ ]` → `[[ ]]` modernization, and the prompt's claimed "python -c call" does not exist in the actual file.

## Warnings

### WR-01: XCUT-01d curator-flag grep false-positives on substring match

**File:** `.planning/phases/70-foundation-audit/70-smoke.sh:53`
**Issue:** The assertion `grep -A1 "^curator:" "$CONFIG_YAML" | grep -q "enabled: false"` matches any line containing the substring `enabled: false`. A YAML value of `enabled: falsey`, `enabled: false_value`, or `enabled: false_positive_flag: true` would all pass the assertion while leaving the curator effectively running. YAML semantics treat `falsey` as a string (truthy in most YAML loaders). The current config happens to read `enabled: false       # FROZEN...` so the test is green by coincidence, not by correctness.

Verified empirically:
```
echo -e "curator:\n  enabled: falsey" | grep -A1 "^curator:" | grep -q "enabled: false"  → MATCH (false positive)
```

**Fix:** Anchor the value with a word boundary or end-of-token:
```bash
# Option A: grep -E with end-of-token boundary
if ! grep -A1 "^curator:" "$CONFIG_YAML" | grep -qE 'enabled:[[:space:]]*false([[:space:]#]|$)'; then
    echo "FAIL: XCUT-01d — curator.enabled is not false in $CONFIG_YAML"
    exit 1
fi

# Option B: robust YAML-aware check via python (the prompt mentions a python -c call exists;
# note: no python call is actually in this file — see IN-03)
```

### WR-02: XCUT-01b regex over-counts (matches echo/JSON/explanation lines, not just inventory rows)

**File:** `.planning/phases/70-foundation-audit/70-smoke.sh:28`
**Issue:** `grep -c 'skills/.*SKILL\.md' "$INVENTORY"` matches **any** line containing the substring `skills/...SKILL.md`. Inspection of the actual `70-LINEAGE-INVENTORY.md` shows 13 matches, of which:
- 6 are real markdown-table rows (the actual inventory) — these carry the `sha256` hash the claim promises.
- 3 are JSON echo entries (`"skill_path": "skills/movie-experts/..."`) in a lineage-snapshot block.
- 4 are explanatory prose / Pitfall-5 paragraph mentions.

So the assertion passes with `INVENTORY_COUNT=13 >= 6` even if 0 of the entries were real hashed inventory rows. The claim "lists all 6 target SKILL.md files with sha256" is not actually validated. A regression that deleted all 6 real rows but left the prose mentions would still pass.

**Fix:** Anchor to the markdown-table row format (leading `|` + expert name) that uniquely identifies inventory entries:
```bash
# Real inventory rows look like: | cinematographer | `skills/.../SKILL.md` | <sha256> | <bytes> | ...
INVENTORY_COUNT=$(grep -cE '^\| [a-z_]+ \| `skills/.*SKILL\.md` \| `[0-9a-f]{64}`' "$INVENTORY" || true)
```
This pins the match to rows that actually carry a 64-hex-char sha256 in the lineage column.

### WR-03: XCUT-01c cross-repo pin check is pure substring existence, not a SHA pin

**File:** `.planning/phases/70-foundation-audit/70-smoke.sh:37-44`
**Issue:** Both `grep -qE 'hermes-agent'` and `grep -qE 'kais-hermes-skills'` only verify the *repo name string* appears somewhere in the inventory. They do not verify that a git commit SHA pin (`hermes-agent=8f70fcf7...`, `kais-hermes-skills=d9620369...`) is present. A regression that removed all SHA pins but left one prose sentence mentioning the repo names would still pass. The comment on line 36 calls these "cross-repo commit pins" — the assertion does not test for pins.

**Fix:** Require the repo-name=SHA pattern:
```bash
if ! grep -qE 'hermes-agent[=: ]+[0-9a-f]{7,40}' "$INVENTORY"; then
    echo "FAIL: XCUT-01c — hermes-agent commit pin missing from inventory"
    exit 1
fi
if ! grep -qE 'kais-hermes-skills[=: ]+[0-9a-f]{7,40}' "$INVENTORY"; then
    echo "FAIL: XCUT-01c — kais-hermes-skills commit pin missing from inventory"
    exit 1
fi
```

## Info

### IN-01: Mixing legacy `[ ]` with `[[ ]]` style

**File:** `.planning/phases/70-foundation-audit/70-smoke.sh:21,29,49,67,72`
**Issue:** All five numeric/string tests use POSIX `[ ]` rather than bash `[[ ]]`. CLAUDE.md does not mandate one over the other for bash (it focuses on Python style), but the file's header `#!/usr/bin/env bash` declares a bash-specific script and the project's bash heritage (per the stack description) is bash 5+. `[[ ]]` is safer (no word-splitting, no path expansion on unquoted vars). Not a bug — POSIX `[ ]` with properly quoted operands works fine — but inconsistent with a bash shebang.

**Fix (optional):** Switch to `[[ ! -f "$INVENTORY" ]]`, `(( INVENTORY_COUNT < 6 ))`, etc., for cleaner bash idiom. Low priority.

### IN-02: No trailing `exit 0` on success path

**File:** `.planning/phases/70-foundation-audit/70-smoke.sh:79`
**Issue:** The script ends with an `echo` after the last passing assertion. In bash, the script's exit code is the exit code of the last command — here `echo`, which returns 0. So behaviorally correct, but relying on this is fragile: if someone appends a `grep` or other command at the bottom later (e.g., a Phase 76 addition), the implicit exit code changes silently.

**Fix (optional):** Add an explicit `exit 0` after the final `echo` to make the success contract explicit:
```bash
echo "Phase 70 smoke status: ALL 6 XCUT-01 ASSERTIONS PASSED"
exit 0
```

### IN-03: Prompt's claimed "python -c call" does not exist in this file

**File:** N/A (reviewer-context mismatch)
**Issue:** The review-prompt context stated: "there's one python -c call" and asked the reviewer to verify CLAUDE.md's `encoding="utf-8"` and `except X as exc:` conventions on it. The actual `70-smoke.sh` contains **no** `python -c` invocation — it is pure bash + `grep` + `[ ]`. This is an info-level note for the orchestrator: the phase's PROMPT/SUMMARY may have a stale reference to a Python call that was removed during implementation, OR the prompt was generated against an earlier draft. No code change required, but Phase 76 VALIDATE that re-runs this smoke should not expect any Python-side behavior.

**Fix:** No code change. Flag for Phase 70 SUMMARY accuracy / Phase 76 planning docs.

---

_Reviewed: 2026-07-09T15:05:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
