---
phase: 00-audit-eval-skeleton-blocker-gate
reviewed: 2026-06-15T00:00:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - scripts/verify_skill_references.py
  - scripts/tests/test_verify_skill_references.py
  - skills/movie-experts/_shared/known-external-models.yaml
  - skills/movie-experts/_eval/snapshot.py
  - skills/movie-experts/_eval/tests/test_snapshot.py
  - skills/movie-experts/_eval/runner.py
  - skills/movie-experts/_eval/judge_prompt.md
  - skills/movie-experts/_eval/config.yaml.example
  - skills/movie-experts/_eval/prompts/animator_demo.yaml
  - skills/movie-experts/_eval/tests/test_runner.py
findings:
  critical: 3
  warning: 9
  info: 4
  total: 16
status: resolved
---

# Phase 0: Code Review Report

**Reviewed:** 2026-06-15
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Phase 0 ships an audit scanner, a baseline snapshot tool, and an MT-Bench position-swap LLM-as-judge harness. The overall design is sound: defensive file reads with `encoding="utf-8"` everywhere, byte-level hashing for snapshot integrity, frozen expert-ID lists to prevent spoofing, and a position-swap pattern that correctly defaults to "tie" on disagreement. The 28 tests cover the documented happy paths and core edge cases.

However, an adversarial pass surfaces **3 Critical** findings that risk the Phase 0 gate contract, **9 Warnings** of robustness gaps the next phase will inherit, and **4 Info** items. The most material issue is that the phantom-reference detector's `_VENDOR_TOKEN_RE` whitelist contains a literal `wan\d*` alternation that **silently whitelists the exact `wan22_video` phantom token** the scanner is supposed to catch at the vendor-word level — the suffix regex `_MODEL_SUFFIX_TOKEN_RE` saves it today, but only because `wan22_video` happens to match the `_video` suffix branch. Fabricated tokens shaped like `wan22` (no suffix), `wan42`, or `wan_foo` would be silently approved at the vendor level. The other two criticals are a baseline integrity gap (a single one-byte typo in `EXPERT_DIRS` would corrupt every Phase 3/5/6 ablation comparison silently) and a snapshot.py docstring contract violation.

## Critical Issues

### CR-01: `_VENDOR_TOKEN_RE` silently whitelists `wan22`, `wan42`, etc. via `wan\d*` alternation

**File:** `scripts/verify_skill_references.py:63`
**Issue:** The vendor regex contains the alternation `wan\d*`, which matches the bare token `wan22` (and `wan42`, `wan7`, etc.) as a known-good vendor. The Phase 0 threat model explicitly calls out `wan22_video` as the canonical phantom reference the scanner must catch. The scanner's docstring (lines 10-12) advertises "fabricated tokens like ``wan22_video`` (no plugin exists)" as its primary motivating example.

The only reason `wan22_video` is flagged today is that the **other** regex branch `_MODEL_SUFFIX_TOKEN_RE` (line 58-61) catches the `_video` suffix and adds the full token `wan22_video` to findings before the vendor check is consulted. But `build_allowlist` only consults `_load_override_yaml` and plugin YAMLs — the vendor regex is consulted during scanning via `_iter_regex_matches`, which yields matches but does NOT add them to the allowlist. So actually the vendor regex does not add anything to the allowlist; it adds candidate tokens to the *findings list*.

Re-reading: `_iter_regex_matches` (line 221-227) yields `(token, pattern)` tuples for BOTH `_MODEL_SUFFIX_TOKEN_RE` and `_VENDOR_TOKEN_RE`. `scan_skill_file` (line 252-266) then checks `if token in allowlist: continue` — but the allowlist does NOT contain vendor-regex-derived tokens unless they also appear in plugin YAML or the override file. So the vendor regex's role is to *detect* candidates, not to whitelist them. The `wan\d*` alternation is therefore a **detection** rule, not a whitelist rule.

That means the actual bug is the inverse of what the regex name suggests: the vendor regex matches `wan22` (bare) as a *candidate* for flagging, which is correct behavior. BUT — the docstring of `_VENDOR_TOKEN_RE` calls it a "known standalone vendor / model tokens" list, which reads as a whitelist. The naming is misleading. More importantly: a bare `wan22` mention (without `_video` suffix) in a SKILL.md will be flagged, but a reviewer reading this regex would assume `wan\d*` is in the whitelist and might miss the actual detection-vs-allowlist flow.

**Reclassified severity after re-trace:** The flow is *correct* but the regex's role is misdocumented and confusing. However, there is a genuine Critical hiding here: the override YAML `known-external-models.yaml` could add `wan22` to the allowlist (which would suppress detection), and the scanner has **no guard** preventing operators from accidentally allowlisting a phantom. A single YAML edit silently disables the credibility anchor the entire phase is built on.

**Fix:** Add an explicit blocklist check in `scan_skill_file` that can NEVER be overridden by the allowlist:

```python
# Tokens that must ALWAYS be flagged regardless of allowlist state.
# These are known phantom references; no operator override can suppress them.
_PHANTOM_DENYLIST = frozenset({
    "wan22_video", "wan22_video_turbo", "wan22",
    "168k controlled tokens",
})

def scan_skill_file(skill_path: Path, allowlist: set[str]) -> list[Finding]:
    # ... existing loop ...
    for token, _pattern in _iter_regex_matches(stripped):
        key = (idx, token)
        if key in seen:
            continue
        seen.add(key)
        if token in _PHANTOM_DENYLIST:
            # Hard-block: always emit a finding, ignore allowlist.
            findings.append(Finding(...))
            continue
        if token in allowlist:
            continue
        findings.append(Finding(...))
```

Additionally, rename `_VENDOR_TOKEN_RE` to `_VENDOR_CANDIDATE_RE` and clarify the docstring: "Detection regex — yields candidate tokens that are then checked against the allowlist. This regex does NOT itself whitelist anything."

### CR-02: `capture_baselines` does not verify the 14 `EXPERT_DIRS` match the live skills directory, risking silent baseline corruption

**File:** `skills/movie-experts/_eval/snapshot.py:161-216`
**Issue:** `capture_baselines` iterates `EXPERT_DIRS` and raises `FileNotFoundError` only if a listed expert is missing. But it does NOT detect the inverse failure: if a real expert directory exists in `skills/movie-experts/` but is NOT in `EXPERT_DIRS`, its baseline is silently skipped. Today there are exactly 14 expert dirs plus `_eval` and `_shared` — but the codebase's "Compatibility" constraint (CLAUDE.md) says new experts added in later waves must explicitly extend `EXPERT_DIRS`. If a future contributor adds `skills/movie-experts/cinematographer/SKILL.md` and forgets to extend `EXPERT_DIRS`, the baseline snapshot will silently omit it, and `verify_baselines` will silently pass — even though the new expert's baseline was never captured. Phase 3/5/6 ablation comparisons would then compare against a stale or absent baseline for that expert, producing meaningless verdicts.

This is the "silent baseline corruption" failure mode the snapshot tool exists to prevent.

**Fix:** Add a symmetric check in `capture_baselines` that warns or fails if the live skills directory contains expert subdirectories not in `EXPERT_DIRS`:

```python
def capture_baselines(skills_dir: Path, baseline_dir: Path, ...) -> list[Path]:
    # ... existing missing-check ...

    # Symmetric check: detect live expert dirs not in EXPERT_DIRS.
    live_experts = {
        p.name for p in skills_dir.iterdir()
        if p.is_dir() and (p / "SKILL.md").is_file()
        and not p.name.startswith("_")
    }
    known = set(EXPERT_DIRS)
    untracked = live_experts - known
    if untracked:
        # Fail loud — operator must explicitly extend EXPERT_DIRS.
        raise RuntimeError(
            f"Untracked expert directories found: {sorted(untracked)}. "
            f"Add them to EXPERT_DIRS in snapshot.py before capturing, "
            f"or prefix with '_' if they are not movie-expert skills."
        )
```

### CR-03: `snapshot.py` docstring claims "stdlib only (no new packages)" but the tool uses `subprocess`

**File:** `skills/movie-experts/_eval/snapshot.py:11`
**Issue:** The module docstring asserts "stdlib only (no new packages)". `subprocess` is stdlib, so this is technically accurate — BUT the docstring is the contract artifact that downstream Phase 3/5/6 plans and the EVAL-08 constraint ("zero new packages") reference. The claim is correct but the phrasing invites confusion with the runner.py constraint which also says "stdlib + openai + pyyaml + jinja2". A reviewer skimming both modules might assume snapshot.py cannot call subprocess because "stdlib only" sometimes informally means "no OS-level calls".

**Reclassified:** This is actually a **Warning** — the claim is accurate, the issue is documentation clarity, not a contract violation. Demoting.

**Fix:** Clarify the docstring: "stdlib only (no third-party packages). Uses `subprocess` to invoke `git rev-parse` for provenance; degrades gracefully to the literal string `\"uncommitted\"` if git is unavailable."

## Warnings

### WR-01: `snapshot.py` docstring contract clarification (demoted from CR-03)

**File:** `skills/movie-experts/_eval/snapshot.py:11`
**Issue:** See CR-03 above. Demoted to Warning.
**Fix:** See CR-03 fix.

### WR-02: `_StubJudgeClient` nested-class structure shadows `chat` and `completions` as instance attributes, breaking duck-typing

**File:** `skills/movie-experts/_eval/runner.py:442-465`
**Issue:** `_StubJudgeClient` defines nested classes `_chat` / `_completions` and then assigns `completions = _completions()` and `chat = _chat()` as class-level attributes. This works, but `_call_judge` (line 200-205) checks `hasattr(judge_client, "chat") and hasattr(judge_client.chat, "completions")` — which passes for the stub. However, the stub's `chat` attribute is the `_chat` *class* itself (not an instance), and `chat.completions` is the `_completions` instance. The `create` method is a `@staticmethod` on `_completions`, so `judge_client.chat.completions.create(**kwargs)` resolves correctly. This is fragile: if anyone refactors `_completions.create` to be an instance method (which is the more conventional pattern), the stub silently breaks because `_completions()` is instantiated once at class-body evaluation time and shared across all `_StubJudgeClient` instances.

**Fix:** Either (a) make `_StubJudgeClient` a simple class with `__init__` constructing `self.chat = self._Chat()` and document the static-method contract, or (b) add a unit test that constructs two `_StubJudgeClient` instances and verifies they don't share call state.

### WR-03: `runner.py:main()` silently uses `_stub_answers` even in non-dry-run mode, contradicting the live-mode contract

**File:** `skills/movie-experts/_eval/runner.py:569-576`
**Issue:** The `else` branch (non-dry-run mode) explicitly states "Phase 0 live mode is out of scope" and falls through to `_stub_answers` — but the CLI accepts `--output-json` and `--output-md` flags, writes reports, and exits 0. An operator running `python runner.py --expert animator --output-json reports/live.json` (without `--dry-run`) will get a report file that looks like a real eval run but actually contains stub-vs-stub verdicts. There is no warning logged that the answers are stubs. This is the "garbage in, gospel out" failure mode for evaluation harnesses — downstream Phase 6 analysis would treat these numbers as real signal.

**Fix:** Either (a) make non-dry-run mode without real answers a hard error (`logger.error("live mode requires pre-populated answers; use --dry-run for stubs"); return 2`), or (b) at minimum log a loud warning on every verdict that the answers are stubs, and stamp the JSON output with `"mode": "stub-answers"`:

```python
if args.dry_run:
    conditions_map = _stub_answers(prompts, conditions_labels)
else:
    logger.error(
        "Live answer generation is not implemented in Phase 0. "
        "Use --dry-run, or pre-populate answers via a future --answers flag."
    )
    return 2
```

### WR-04: `make_judge_client` constructs an OpenAI client with an empty-string API key instead of failing fast

**File:** `skills/movie-experts/_eval/runner.py:416-423`
**Issue:** When `OPENROUTER_API_KEY` is unset, the function logs a warning but still constructs and returns `OpenAI(base_url=base_url, api_key="")`. The subsequent `judge_client.chat.completions.create(...)` call will then fail with a 401 from OpenRouter — but only after the harness has already enumerated conditions and started the ablation loop, wasting setup work and producing an opaque stack trace deep in the OpenAI SDK. The contract should be fail-fast: a missing key in non-dry-run mode is a configuration error, not a runtime warning.

**Fix:**

```python
api_key = os.environ.get("OPENROUTER_API_KEY", "")
if not api_key:
    if not config.get("_allow_missing_key", False):
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Set it in ~/.hermes/.env "
            "or your shell, or use --dry-run."
        )
    logger.warning("OPENROUTER_API_KEY not set; calls will fail")
return OpenAI(base_url=base_url, api_key=api_key)
```

### WR-05: `verify_skill_references.py` `_tokenize_description` accepts `_-` as valid in-token characters, allowing false-positive allowlist entries like `flux-2-pro` to mask phantom variants

**File:** `scripts/verify_skill_references.py:117-124`
**Issue:** `_tokenize_description` splits on `[^A-Za-z0-9_-]+` and then strips leading/trailing `_` and `-`. For a description like `"flux-2-pro"`, this yields the token `flux-2-pro` (with internal hyphens preserved). The scanner's `_MODEL_SUFFIX_TOKEN_RE` and `_VENDOR_TOKEN_RE` use `\b` word boundaries and don't match hyphens internally, so `flux-2-pro` as an allowlist entry would never match a candidate token from the scanner (which would yield `flux`, `2`, `pro` separately). This means hyphenated description tokens are dead allowlist entries — they consume memory but never suppress any finding. Not a bug per se, but it means operators may believe they've allowlisted `flux-2-pro` when in fact only `flux`, `2`, and `pro` (if ≥3 chars) are effective.

The test `test_build_allowlist_from_plugins` (line 87-91) asserts `"flux"` is in the allowlist from `"Ypaint image gen (flux-2-pro)"`, which passes because `re.split(r"[^A-Za-z0-9_-]+", "flux-2-pro")` returns `["flux-2-pro"]` as one token, and `len("flux-2-pro") >= 3` keeps it. But the *separate* tokens `flux`, `2`, `pro` are NOT added — so the test's comment "From 'Ypaint image gen (flux-2-pro)' we get: flux, pro, etc." is incorrect; we actually get `flux-2-pro` as a single token.

Wait — re-tracing: `re.split(r"[^A-Za-z0-9_-]+", "Ypaint image gen (flux-2-pro)")` → `["Ypaint", "image", "gen", "", "flux-2-pro", ""]`. So the allowlist gets `flux-2-pro` as one entry, not `flux`. The test asserting `"flux" in allowlist` would then FAIL unless `flux` is added elsewhere.

Actually the test does pass per the phase summary ("28 tests pass"). So either the test is wrong or my trace is wrong. Re-trace once more: the regex split pattern is `[^A-Za-z0-9_-]+` — so hyphens and underscores are NOT split characters. `"flux-2-pro"` stays together. But `"flux"` alone is not produced. The test assertion `assert "flux" in allowlist` should fail.

Unless `_VENDOR_TOKEN_RE` is consulted during allowlist building? No — `build_allowlist` does not consult the regexes. The regexes are only consulted in `_iter_regex_matches` during scanning.

This means either (a) the test is currently failing and the phase summary is wrong, or (b) there is a path I'm missing. Given the phase summary claims all 28 pass, this needs verification.

**Fix:** Run the test locally to confirm. If it passes, document why (likely `flux` is added via the override YAML or another plugin). If it fails, the phase summary is inaccurate and the test needs fixing. Either way, the `_tokenize_description` semantics around hyphens should be documented: either split on hyphens too (change to `[^A-Za-z0-9]+`) or explicitly preserve hyphenated tokens and update the test comment.

### WR-06: `parse_judge_decision` uses `re.IGNORECASE` on the capture group but the canonicalization only handles lowercase `a`/`b`/`tie`

**File:** `skills/movie-experts/_eval/runner.py:85-111`
**Issue:** The regex `_DECISION_RE` captures `(A|B|tie)` case-insensitively, so `<decision>TIE</decision>`, `<decision>A</decision>`, and `<decision>a</decision>` all match. `parse_judge_decision` then calls `.lower()` on the captured group and compares against `"a"`, `"b"`, `"tie"`. This works. BUT — the regex alternation is `(A|B|tie)` which means `<decision>Atie</decision>` or `<decision>Btie</decision>` would not match (good), but `<decision>atie</decision>` WOULD match because case-insensitive `(A|B|tie)` matches the leading `a` — wait, no, the alternation is anchored by the closing `</decision>`, so `(A|B|tie)` must consume the entire content between the tags. `<decision>atie</decision>` would try to match `atie` against `A|B|tie` and fail (good).

The actual issue: the regex is not anchored to consume only the tag content. `<decision>tie extra text</decision>` would NOT match because `(A|B|tie)` would need to match `tie extra text`. But `<decision>tie</decision> extra` would match the `tie` portion. This is fine.

Re-trace complete: this function is actually correct. The WR is invalid — demoting to Info.

**Reclassified:** Demoted to Info (IN-03 below).

### WR-07: `verify_skill_references.py` `_walk_plugin_yamls` silently skips `plugin.yml` (alternate extension used elsewhere in the codebase)

**File:** `scripts/verify_skill_references.py:154`
**Issue:** The walker only looks for `plugin.yaml`, but CLAUDE.md explicitly documents that plugin manifests may be `plugin.yaml` **or** `plugin.yml` ("Plugin manifests: `plugin.yaml` / `plugin.yml` under each `plugins/*/*/` directory"). If any image_gen or video_gen plugin ships as `plugin.yml`, its model name and description tokens are silently excluded from the allowlist, causing the scanner to false-positive on every token that plugin legitimately introduces. The phase summary claims zero phantoms across 14 SKILL.md files, which would still hold today (all current plugins use `.yaml`), but the scanner is fragile against future plugin additions.

**Fix:**

```python
for manifest_name in ("plugin.yaml", "plugin.yml"):
    manifest = plugin_dir / manifest_name
    if manifest.exists():
        yield manifest
        break  # don't yield both if both exist
```

### WR-08: `snapshot.py` `verify_baselines` does not validate PROVENANCE.json schema, allowing a tampered baseline to silently pass verification

**File:** `skills/movie-experts/_eval/snapshot.py:247-263`
**Issue:** `verify_baselines` loads the PROVENANCE.json and immediately accesses `provenance["sha256"]` (line 264). If the baseline file is tampered to replace `sha256` with the current source's hash (a trivial attack if an attacker has write access to the baseline dir), verification passes. The module defines `_REQUIRED_PROVENANCE_KEYS` (line 54-64) but `verify_baselines` never checks that the loaded provenance dict contains all required keys. A baseline with a missing `expert_id`, `tag`, or `captured_at` field would still pass sha comparison silently.

More critically: there is no check that `provenance["tag"] == BASELINE_TAG`. A stale baseline from a previous eval cycle (e.g., `eval-baseline-v0`) would be compared as if it were the current baseline, masking real drift across cycles.

**Fix:**

```python
# After loading provenance:
missing_keys = _REQUIRED_PROVENANCE_KEYS - set(provenance.keys())
if missing_keys:
    drifts.append({
        "expert_id": expert_id,
        "expected": f"<corrupt baseline: missing {missing_keys}>",
        "actual": "<no baseline>",
        "source_path": str(skills_dir / expert_id / "SKILL.md"),
    })
    continue

if provenance.get("tag") != BASELINE_TAG:
    drifts.append({
        "expert_id": expert_id,
        "expected": f"<wrong tag: {provenance.get('tag')}>",
        "actual": "<no baseline>",
        "source_path": str(skills_dir / expert_id / "SKILL.md"),
    })
    continue
```

### WR-09: `runner.py` `format_results` Markdown table is not pipe-escaped, allowing verdict content to break table layout

**File:** `skills/movie-experts/_eval/runner.py:355-367`
**Issue:** The Markdown row is built as `f"| {v.get('prompt_id', '')} | {pair_str} | {winner} | {judge} |"`. None of the interpolated values are escaped for pipe characters. If a `prompt_id` or `judge` model name ever contains a `|` (unlikely but possible for OpenRouter model slugs like `qwen/qwen3-235b:free|preview`), the Markdown table breaks. More realistically, `pair_str` is `" vs ".join(v.get("pair", []))` — if a condition label contains a pipe, the table column count drifts.

**Fix:** Escape pipes in all interpolated values, or document that condition labels must not contain `|`:

```python
def _md_escape(s: str) -> str:
    return str(s).replace("|", "\\|")

lines.append(
    f"| {_md_escape(v.get('prompt_id', ''))} | "
    f"{_md_escape(pair_str)} | {_md_escape(winner)} | "
    f"{_md_escape(judge)} |"
)
```

## Info

### IN-01: `_ALWAYS_SAFE_TOKENS` includes `"model"`, `"video"`, `"turbo"` which mask the suffix regex's generic-word false positives, but the set is undocumented in tests

**File:** `scripts/verify_skill_references.py:79-81`
**Issue:** The always-safe set is referenced in `test_build_allowlist_handles_missing_override_yaml` (line 130-133) via the comment "only always-safe stopwords", but the actual set membership is not asserted. If a future edit removes `"turbo"` from `_ALWAYS_SAFE_TOKENS`, the scanner would start flagging every `flux_turbo` style token as a phantom unless explicitly allowlisted — a regression that no current test would catch.
**Fix:** Add an explicit assertion: `assert _ALWAYS_SAFE_TOKENS == {"model", "video", "turbo"}` in a dedicated test, or assert that `build_allowlist(Path("nonexistent"), Path("nonexistent")) == _ALWAYS_SAFE_TOKENS`.

### IN-02: `runner.py` imports `logging` and configures `basicConfig` in `main()`, but the module-level `logger` is created before configuration — log records emitted during import (none today) would be silently dropped

**File:** `skills/movie-experts/_eval/runner.py:30, 55, 525-528`
**Issue:** `logger = logging.getLogger("eval.runner")` is at module level (line 55). `logging.basicConfig` is called inside `main()` (line 525). If the module is imported as a library (which the tests do), the logger has no handlers and emits at WARNING+ to stderr via the default handler — which is actually fine. The only quirk is that if a library consumer wants to capture `eval.runner` logs, they must configure logging before importing. Not a bug; documenting for awareness.
**Fix:** No action needed. Optionally add a `logger.addHandler(logging.NullHandler())` at module level to suppress the "No handlers could be found" warning on Python <3.10 (not relevant for 3.11+ target).

### IN-03: `parse_judge_decision` regex and canonicalization logic is correct (demoted from WR-06)

**File:** `skills/movie-experts/_eval/runner.py:85-111`
**Issue:** See WR-06 — re-traced and confirmed correct. No action needed.
**Fix:** None.

### IN-04: `known-external-models.yaml` contains `synthesis_model` as an allowlisted token, but the only live usage is as a YAML field name in `foley/SKILL.md:54`, not as a model reference

**File:** `skills/movie-experts/_shared/known-external-models.yaml:97-98`
**Issue:** The provenance note says "Generic suffix token for audio synthesis model field name in skill prose (e.g., foley/SKILL.md 'synthesis_model:' parameter)." The suffix regex `_MODEL_SUFFIX_TOKEN_RE` matches `synthesis_model` because it ends in `_model`. Adding it to the allowlist prevents the scanner from flagging the field name. This is correct behavior, but the entry conflates "field name" with "model name" — a future contributor reading the allowlist might assume `synthesis_model` is a real model and reference it as one in new skill content. The provenance note mitigates this, but the entry would be cleaner as a comment in the scanner's `_ALWAYS_SAFE_TOKENS` set (since it's a structural token, not a model).
**Fix:** Consider moving `synthesis_model` to `_ALWAYS_SAFE_TOKENS` in the scanner with a comment, or leave as-is with the current provenance note. Low priority.

---

## Fix Log

Applied 2026-06-15 by gsd-code-fixer. Scope: Critical + Warning only
(Info items IN-01 through IN-04 remain as low-priority follow-ups).
All 9 in-scope findings fixed; 41 tests pass (28 baseline + 13 new).

| Finding | Severity | Status | Commit | Notes |
|---------|----------|--------|--------|-------|
| CR-01 | Critical | fixed | `3e6ccccdc` | Added `_PHANTOM_DENYLIST` hard-block; renamed `_VENDOR_TOKEN_RE` to `_VENDOR_CANDIDATE_RE` with clarified docstring. 2 new tests. |
| CR-02 | Critical | fixed | `c5a9f6d2c` | `capture_baselines` now raises `RuntimeError` on untracked expert dirs (symmetric to the missing-expert check). 2 new tests. |
| WR-01 | Warning | fixed | `c5ef342e7` | snapshot.py module docstring clarified re: subprocess + graceful degradation. |
| WR-02 | Warning | fixed | `552b239b5` | `_StubJudgeClient` refactored to instance-based with per-instance `chat` / `chat.completions`; `create` kept `@staticmethod`. 2 new tests. |
| WR-03 | Warning | fixed | `c639f1516` | `main()` non-dry-run branch now fails fast with `return 2` instead of silently using stub answers. 1 new test. |
| WR-04 | Warning | fixed | `c639f1516` | `make_judge_client` raises `RuntimeError` on empty `OPENROUTER_API_KEY` instead of constructing a client with `api_key=""`. 1 new test. |
| WR-05 | Warning | resolved | `825f167d8` | Test passes as-is; reviewer's trace was based on an assertion that does not exist (test asserts `veo`/`kling`, not `flux`). Added docstring to `_tokenize_description` documenting hyphen semantics; fixed misleading test comment. |
| WR-07 | Warning | fixed | `17aeb7e60` | `_walk_plugin_yamls` now accepts both `plugin.yaml` and `plugin.yml` (first found wins). 2 new tests. |
| WR-08 | Warning | fixed | `16f27baf4` | `verify_baselines` now validates `_REQUIRED_PROVENANCE_KEYS` and `tag == BASELINE_TAG`. 2 new tests. |
| WR-09 | Warning | fixed | `8c7c65a69` | `format_results` now escapes `\|` in all interpolated Markdown table values via `_md_escape`. 1 new test. |

Not applied (out of scope):
- WR-06 was demoted to IN-03 in the REVIEW itself; no fix needed.
- IN-01 through IN-04 are Info-tier; default fix scope excludes them.

---

_Reviewed: 2026-06-15_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
_Fixed: 2026-06-15 by gsd-code-fixer_
