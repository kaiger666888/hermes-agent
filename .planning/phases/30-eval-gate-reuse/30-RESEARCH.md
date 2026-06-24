# Phase 30: Eval Gate Reuse - Research

**Researched:** 2026-06-24
**Domain:** LLM-as-judge eval harness extension; patch-vs-baseline gating; statistical significance for paired comparisons
**Confidence:** HIGH

## Summary

Phase 30 extends the existing `skills/movie-experts/_eval/runner.py` MT-Bench position-swap harness into a **patch-vs-baseline gate** that automatically rejects candidate patches to bundled movie-expert skills before they reach a human reviewer. The locked decisions in `30-CONTEXT.md` are clear and well-scoped: unified-diff input, cached v5.0 baseline, configurable thresholds (δ=0.3 mean / 1.0 per-prompt / min 5 prompts), and 2-round A/B position swap. The `_eval/` tree is confirmed **fully isolated** from the Hermes runtime (zero `from _eval` / `import _eval` imports outside `_eval/` itself), so extending it does NOT constitute a Hermes-core touch.

**The single most important finding for the planner:** The current v1 harness (`runner.py`) is **comparative-only** — it parses the `<decision>A|B|tie</decision>` tag from the judge and emits win/tie/lose verdicts. It does **NOT** parse or aggregate the per-dimension numeric scores (1-5 on each of `industry_accuracy` / `professional_depth` / `actionability` / `language_quality`) that `judge_prompt.md` explicitly asks the judge to emit. **GATE-02 and GATE-04 are expressed in NUMERIC terms** ("mean score drops more than δ=0.3 on the 4-point rubric", "any single prompt's score drops more than 1.0"). Therefore Phase 30 cannot simply wrap the existing `run_ablation` / `run_position_swap` functions — it **must add numeric score extraction** to the judge response parsing. This is the core extension point. The research below recommends a thin `gate.py` wrapper that (a) calls a new `parse_judge_scores()` helper in `runner.py` to lift the per-dimension numbers, (b) aggregates them per-prompt into a 1-5 composite, and (c) applies the δ / per-prompt / min-prompts thresholds. The position-swap mechanics (`run_position_swap`, `build_judge_messages`) are reused as-is for the A/B double-blind pass (GATE-03), but the final verdict derives from the numeric deltas, not from the A/B/tie tag.

Secondary findings: (1) `git apply --check` + `git apply` + `git checkout -- <files>` is the recommended patch-apply/revert mechanics (stdlib `subprocess`, no new deps). (2) `scipy` is **available** in the env (transitively via numpy/openai stack) but is **NOT a direct dependency** and violates the `_eval/` "stdlib only" convention from `snapshot.py:14` — the gate should compute the paired-t `t_stat` via `statistics.stdev` + manual formula and either ship a small hardcoded t-table for p-value lookup OR omit p-value and report only `t_stat` + `n` + `df` (letting the operator interpret). (3) The main pytest run (`testpaths = ["tests"]` in `pyproject.toml:349`) does **NOT** collect `_eval/tests/` — the gate's tests run via a separate `python -m pytest skills/movie-experts/_eval/tests/` invocation, matching the existing `_eval` test pattern.

**Primary recommendation:** Build a new `skills/movie-experts/_eval/gate.py` (thin orchestrator) + add a `parse_judge_scores()` numeric-extraction function to `runner.py` + add `gate_config.yaml.example` alongside the existing `config.yaml.example`. Reuse `run_position_swap`, `build_judge_messages`, `make_judge_client`, `load_prompts` verbatim. Gate logic = config load → patch apply → baseline lookup → candidate eval (position-swapped, numeric) → paired-t + threshold check → verdict + reject-log emit → patch revert → exit code.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Patch apply/revert (git subprocess) | Offline tooling (`_eval/gate.py`) | — | Mutates working tree temporarily; `_eval/` is offline dev tooling, not runtime |
| Baseline score lookup | Offline tooling (`_eval/baseline/`) | — | Cached v5.0 baseline per CONTEXT.md; `--rebuild-baseline` refreshes |
| LLM judge invocation | Offline tooling (`runner.py` + OpenAI SDK) | — | Reuses v1 `make_judge_client` / `_call_judge` verbatim; position-swap + numeric scoring |
| Threshold / regression decision | Offline tooling (`gate.py`) | — | Pure function over numeric scores; deterministic for fixed inputs |
| Paired-t significance | Offline tooling (`gate.py`) | — | stdlib `statistics`; p-value via t-table or omitted |
| Reject-log emission | Offline tooling (`_eval/reports/<patch_id>.reject.json`) | — | Append-only JSON; consumed by P31 review queue + P32 audit |
| Exit code propagation | Offline tooling (`gate.py` `sys.exit`) | — | 0/1/2/3 contract per CONTEXT.md; consumed by P31 EVOL invoker |
| Hermes runtime integration | — | — | **ZERO** — confirmed by grep; `_eval/` not imported by runtime |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `openai` (SDK) | `==2.24.0` (pyproject.toml:34) | LLM judge calls via OpenRouter base_url | Already used by `runner.py:make_judge_client`; no new dep |
| `pyyaml` (yaml) | `==6.0.3` (pyproject.toml) | `gate_config.yaml` + prompts YAML loading | Already used by `runner.py:load_config` / `load_prompts` |
| `jinja2` | `==3.1.6` (pyproject.toml) | Judge prompt template rendering | Already used by `runner.py:build_judge_messages` |
| `statistics` (stdlib) | Python 3.11+ | Paired-t `t_stat` computation (`mean`, `stdev`) | `_eval/` stdlib-only convention (`snapshot.py:14`) |
| `subprocess` (stdlib) | Python 3.11+ | `git apply` / `git checkout` patch mechanics | Matches `snapshot.py:_current_git_sha` pattern |
| `argparse` (stdlib) | Python 3.11+ | CLI surface for `gate.py` | Matches `runner.py:main` + `snapshot.py:main` |
| `hashlib` (stdlib) | Python 3.11+ | Patch ID generation + baseline sha256 | Matches `snapshot.py:compute_provenance` |
| `pathlib` (stdlib) | Python 3.11+ | All path handling | Matches `_eval/` convention |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `json` (stdlib) | Python 3.11+ | Reject-log + report serialization | Every gate run |
| `re` (stdlib) | Python 3.11+ | Numeric score extraction from judge response (`parse_judge_scores`) | Extends existing `_DECISION_RE` pattern in `runner.py:53` |
| `datetime` (stdlib) | Python 3.11+ | ISO 8601 timestamps in reject-log | Matches `snapshot.py:compute_provenance` |
| `logging` (stdlib) | Python 3.11+ | Gate diagnostics | Matches `runner.py:logger` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `subprocess` + `git apply` | Python `patch` library | **Rejected** — `patch` lib adds a third-party dep; repo is always a git repo; `git apply --check` gives free validation. CONTEXT.md locked this. |
| `scipy.stats.ttest_rel` | stdlib `statistics` + t-table | **Rejected for production path** — `scipy` is NOT a direct dependency (only transitively present); violates `_eval/` stdlib-only convention. stdlib t-stat + hardcoded critical-t table for df=1..30 at α=0.05 (two-tailed) is sufficient for a fixed prompt set. `[VERIFIED: pyproject.toml:175 shows numpy direct, scipy absent]` |
| Forking `runner.py` | Thin `gate.py` wrapper | **Rejected** — CONTEXT.md locks "extends (does NOT fork)". Wrapper calls `runner.py` as a library. |
| In-memory patch dict | Unified diff file | **Rejected** — CONTEXT.md locks unified diff; matches `git format-patch` conventions + P31 EVOL output. |

**Installation:**
```bash
# NO new packages. All dependencies already pinned in pyproject.toml.
# The gate uses: openai, pyyaml, jinja2 (existing) + stdlib (statistics, subprocess, argparse, hashlib, json, re, datetime, pathlib, logging).
```

**Version verification:**
```bash
# Confirmed in pyproject.toml during research:
# - openai==2.24.0 (line 34)
# - PyYAML==6.0.3
# - Jinja2==3.1.6
# - numpy==2.4.3 (line 175, direct dep — scipy is transitive only, NOT used by gate)
```

## Package Legitimacy Audit

> **No new packages installed in this phase.** Phase 30 uses only packages already pinned in `pyproject.toml` (openai, pyyaml, jinja2) + Python stdlib (`statistics`, `subprocess`, `argparse`, `hashlib`, `json`, `re`, `datetime`, `pathlib`, `logging`). The stdlib-only constraint for new `_eval/` code is documented at `snapshot.py:14`. slopcheck gate N/A — zero net-new registry dependencies.

## Architecture Patterns

### System Architecture Diagram

```
                    ┌─────────────────────────────────────────┐
                    │  Phase 31 EVOL / Phase 32 Curator        │
                    │  (invokes gate via subprocess OR import) │
                    └──────────────────┬──────────────────────┘
                                       │  candidate.patch (unified diff)
                                       ▼
        ┌──────────────────────────────────────────────────────────┐
        │  gate.py: main()                                          │
        │  1. Load gate_config.yaml (thresholds, judge_model)       │
        │  2. Apply CLI overrides (--threshold-delta etc.)          │
        │  3. Generate patch_id = f"{skill}_{ts_unix}_{sha[:8]}"   │
        └──────────────────┬───────────────────────────────────────┘
                           │
          ┌────────────────┼─────────────────────────┐
          ▼                ▼                          ▼
   ┌─────────────┐  ┌──────────────┐         ┌─────────────────┐
   │ PATCH APPLY │  │ BASELINE     │         │ PROMPTS         │
   │ git apply   │  │ LOOKUP       │         │ load_prompts()  │
   │ --check     │  │ _eval/       │         │ (runner.py)     │
   │ + git apply │  │ baseline/    │         │ <skill>_demo    │
   │             │  │ <skill>/     │         │ .yaml           │
   │ (subprocess)│  │ scores.json  │         │                 │
   └──────┬──────┘  │ (lazy build) │         └────────┬────────┘
          │         └──────┬───────┘                  │
          │                │                          │
          │    ┌───────────┘                          │
          │    │                                      │
          ▼    ▼                                      ▼
   ┌────────────────────────────────────────────────────────────┐
   │  EVALUATE CANDIDATE (patched SKILL.md)                      │
   │  For each prompt:                                           │
   │    1. Invoke patched skill → candidate_answer              │
   │    2. run_position_swap(prompt, baseline_ans, candidate_ans)│
   │       ──► 2 judge calls (A-first, B-first) [runner.py reuse]│
   │    3. parse_judge_scores() + parse_judge_decision()         │
   │       ──► per-dimension scores (1-5) + A/B/tie             │
   │    4. composite_score = mean(4 dimensions)                  │
   └────────────────────┬───────────────────────────────────────┘
                        │
                        ▼
   ┌────────────────────────────────────────────────────────────┐
   │  DECIDE (pure function over numeric scores)                 │
   │  - n_valid = count(prompts with both scores)                │
   │  - if n_valid < min_prompts → verdict="inconclusive"       │
   │  - mean_delta = mean(candidate) − mean(baseline)            │
   │  - if mean_delta < −delta_threshold → verdict="fail_mean"  │
   │  - per_prompt_deltas[i] = candidate[i] − baseline[i]        │
   │  - if any |delta| > per_prompt_threshold (candidate side)   │
   │    → verdict="fail_regression"                             │
   │  - else → verdict="pass"                                    │
   │  - paired_t: t_stat via statistics.stdev (p-value optional) │
   └────────────────────┬───────────────────────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
   ┌──────────┐  ┌────────────┐  ┌─────────────────────────┐
   │ PATCH    │  │ REPORT     │  │ REVERT                  │
   │ REVERT   │  │ WRITE      │  │ git checkout -- <files> │
   │ (always) │  │ reports/   │  │ (enumerated from patch  │
   │          │  │ <patch_id> │  │  header)                │
   │          │  │ .json      │  │                         │
   │          │  │ (+.reject  │  │                         │
   │          │  │  .json if  │  │                         │
   │          │  │  rejected) │  │                         │
   └──────────┘  └────────────┘  └─────────────────────────┘
                        │
                        ▼
   ┌────────────────────────────────────────────────────────────┐
   │  EXIT CODE: 0=pass, 1=fail_mean, 2=fail_regression,         │
   │             3=inconclusive                                  │
   │  sys.exit(N)  ← consumed by P31 EVOL invoker                │
   └────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure
```
skills/movie-experts/_eval/
├── runner.py              # EXTENDED: add parse_judge_scores() + score-aggregation helpers
├── snapshot.py            # UNCHANGED (baseline capture/verify — reused as-is)
├── gate.py                # NEW: thin orchestrator (patch apply → eval → decide → revert → report)
├── gate_config.yaml.example  # NEW: committed default thresholds (δ=0.3, per_prompt=1.0, min_prompts=5)
├── gate_config.yaml       # NEW, operator-local (gitignored if diverges)
├── config.yaml.example    # UNCHANGED (existing runner config)
├── judge_prompt.md        # UNCHANGED (already asks for per-dimension scores; gate parses them)
├── baseline/              # EXTENDED: add per-skill scores.json (cached numeric baselines)
│   └── <skill>/
│       ├── SKILL.md       # existing byte-exact snapshot
│       ├── PROVENANCE.json # existing
│       └── scores.json    # NEW: cached numeric baseline scores per prompt
├── prompts/               # UNCHANGED (existing MT-Bench prompt set)
├── reports/               # EXTENDED: add <patch_id>.json + <patch_id>.reject.json
│   ├── <expert>_phase<N>.{json,md}  # existing
│   └── <patch_id>.json              # NEW: gate report (always written)
└── tests/
    ├── test_runner.py     # EXTENDED: add TestParseJudgeScores
    ├── test_snapshot.py   # UNCHANGED
    ├── test_gate.py       # NEW: gate logic (config, thresholds, verdict, reject-log)
    └── test_gate_integration.py  # NEW: end-to-end with MockJudgeClient + synthetic patch
```

### Pattern 1: Thin Wrapper Over Existing Library (NOT Fork)
**What:** `gate.py` imports `runner` as a module and calls its public functions (`run_position_swap`, `build_judge_messages`, `make_judge_client`, `load_prompts`, `_call_judge`). It does NOT copy or reimplement them.
**When to use:** Whenever the locked decision is "extend, not fork" (CONTEXT.md `<decisions>` + `<code_context>` "runner.py:1-400+ (v1 MT-Bench harness) — REUSE per GATE-01. Phase 30 extends (does NOT fork)").
**Example:**
```python
# Source: skills/movie-experts/_eval/runner.py (existing public API)
# gate.py — thin orchestrator
from __future__ import annotations
import runner  # noqa: E402 — sibling import, matches test_runner.py:29 pattern

def evaluate_candidate(
    prompts: list[dict[str, str]],
    baseline_answers: list[str],
    candidate_answers: list[str],
    judge_client: runner.JudgeClient,
    judge_model: str,
) -> list[dict]:
    """Run position-swapped numeric scoring per prompt. Returns per-prompt
    score records with baseline_score, candidate_score, delta, verdict."""
    results = []
    for i, p in enumerate(prompts):
        v = runner.run_position_swap(
            prompt=p["text"],
            answer_a=baseline_answers[i],
            answer_b=candidate_answers[i],
            judge_client=judge_client,
            judge_model=judge_model,
            prompt_id=p["id"],
        )
        # v has ordering_ab, ordering_ba, final (A_wins/B_wins/tie)
        # gate.py extracts numeric scores from the SAME judge responses
        # by re-parsing — OR runner.run_position_swap is extended to also
        # return raw judge texts for numeric extraction (recommended).
        results.append({"prompt_id": p["id"], "verdict": v["final"], ...})
    return results
```

**Recommended extension to `runner.py`:** Add a `parse_judge_scores(raw_text: str) -> dict[str, float]` function that lifts the 4 per-dimension numeric scores from the judge response (the judge_prompt.md already instructs the judge to emit `<dimension_name>: <score 1-5> — <justification>`). Extend `run_position_swap` to ALSO return `scores_ab` and `scores_ba` dicts alongside the existing `ordering_ab` / `ordering_ba`. The gate then averages the two orderings' scores per dimension (position-bias mitigation on the numeric axis, mirroring the existing A/B/tie collapse).

### Pattern 2: Patch Apply + Revert via git subprocess
**What:** Apply a candidate unified diff with `git apply --check` (dry-run validation) then `git apply` (actual). Revert with `git checkout -- <files>` where `<files>` is enumerated from the patch header (`+++ b/path` lines).
**When to use:** Every gate run. The gate MUST always revert, even on exception (use `try/finally`).
**Example:**
```python
# Source: git(1) man page + verified in /tmp/gate_test during research
import subprocess
from pathlib import Path

def extract_patched_files(patch_path: Path) -> list[str]:
    """Parse '+++ b/<path>' lines from unified diff header."""
    text = patch_path.read_text(encoding="utf-8")
    files = []
    for line in text.splitlines():
        if line.startswith("+++ b/"):
            files.append(line[6:])  # strip "+++ b/" prefix
        elif line.startswith("+++ ") and not line.startswith("+++ /dev/null"):
            # Handle '+++ <path>' without b/ prefix (rare)
            files.append(line[4:].split("\t")[0])
    return files

def apply_patch(patch_path: Path, repo_root: Path) -> None:
    """Validate + apply. Raises subprocess.CalledProcessError on failure."""
    # Validate first (does not touch working tree)
    subprocess.run(
        ["git", "apply", "--check", str(patch_path)],
        cwd=str(repo_root), check=True, capture_output=True, text=True, encoding="utf-8",
    )
    # Apply for real
    subprocess.run(
        ["git", "apply", str(patch_path)],
        cwd=str(repo_root), check=True, capture_output=True, text=True, encoding="utf-8",
    )

def revert_patch(files: list[str], repo_root: Path) -> None:
    """Revert via git checkout. Simpler than 'git apply -R' (no patch file dep)."""
    if not files:
        return
    subprocess.run(
        ["git", "checkout", "--"] + files,
        cwd=str(repo_root), check=True, capture_output=True, text=True, encoding="utf-8",
    )
```

### Pattern 3: Deterministic Numeric Scoring (the GATE-02/04 core)
**What:** Convert the judge's per-dimension scores into a single composite per-prompt score, then apply mean-delta and per-prompt-regression thresholds.
**When to use:** This is the heart of GATE-02 and GATE-04.
**Example:**
```python
# Source: derived from CONTEXT.md GATE-02/04 thresholds + judge_prompt.md dimensions
import statistics

DIMENSIONS = ("industry_accuracy", "professional_depth", "actionability", "language_quality")

def composite_score(scores: dict[str, float]) -> float:
    """Mean of the 4 dimension scores (each 1-5). Range [1.0, 5.0]."""
    return statistics.mean(scores[d] for d in DIMENSIONS)

def decide_verdict(
    baseline_scores: list[float],
    candidate_scores: list[float],
    *,
    delta_threshold: float,      # 0.3
    per_prompt_threshold: float, # 1.0
    min_prompts: int,            # 5
) -> tuple[str, dict]:
    """Returns (verdict, evidence_dict). Deterministic for fixed inputs."""
    n = min(len(baseline_scores), len(candidate_scores))
    if n < min_prompts:
        return "inconclusive", {"n_valid": n, "min_prompts": min_prompts}

    deltas = [c - b for c, b in zip(candidate_scores, baseline_scores)]
    mean_delta = statistics.mean(deltas)

    if mean_delta < -delta_threshold:
        return "fail_mean", {
            "mean_delta": mean_delta, "threshold": -delta_threshold,
            "mean_baseline": statistics.mean(baseline_scores),
            "mean_candidate": statistics.mean(candidate_scores),
        }

    for i, d in enumerate(deltas):
        if d < -per_prompt_threshold:
            return "fail_regression", {
                "regressing_prompt_idx": i, "delta": d,
                "threshold": -per_prompt_threshold,
                "all_deltas": deltas,
            }

    return "pass", {
        "mean_delta": mean_delta,
        "mean_baseline": statistics.mean(baseline_scores),
        "mean_candidate": statistics.mean(candidate_scores),
        "all_deltas": deltas,
    }
```

### Anti-Patterns to Avoid
- **Forking `runner.py`** — CONTEXT.md explicitly forbids ("extends, does NOT fork"). Any logic duplicated into `gate.py` is a maintenance liability. If `runner.py` needs a new function (e.g., `parse_judge_scores`), add it there and import from `gate.py`.
- **Relying on the `<decision>A|B|tie</decision>` tag alone for GATE-02/04** — The v1 harness only emits comparative verdicts, not numeric scores. GATE-02 ("mean score drops more than δ=0.3") and GATE-04 ("single prompt score drops more than 1.0") are **numeric** requirements. The gate MUST parse the per-dimension scores from the judge response, not just the decision tag. This is the #1 trap.
- **Adding `scipy` as a gate dependency** — `scipy` is transitively present but NOT a direct dependency (`pyproject.toml:175` shows only `numpy` direct). The `_eval/` tree has a documented stdlib-only convention (`snapshot.py:14`). Use `statistics.stdev` + manual t-formula; ship a small hardcoded t-table for p-value lookup if p-value is required (see Open Questions).
- **Not reverting the patch on exception** — If the LLM judge throws mid-run, the working tree is left with the candidate patch applied. Use `try/finally` to guarantee `revert_patch()` runs even on `Exception`. Log the revert outcome.
- **`from __future__ import annotations` omission** — CLAUDE.md mandates this for new modules (`gate.py`, any new `runner.py` additions). `runner.py:25` and `snapshot.py:20` already follow it.
- **`open()` without `encoding="utf-8"`** — Ruff PLW1514 blocks the merge. Every new `open()` in `gate.py` + `runner.py` additions must pass it explicitly.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM judge invocation + position swap | Custom judge client | `runner.run_position_swap` + `runner.make_judge_client` + `runner._call_judge` | v1 harness already handles OpenAI SDK v1/v2 normalization, swap flag, temperature hard-pin (EVAL-03), fail-fast on missing key (WR-04) |
| Position-swap message construction | Custom message builder | `runner.build_judge_messages(prompt, answer_a, answer_b, swap)` | Already renders Jinja2 judge_prompt.md template, labels answers "Answer 1/2" (blind), passes swap via extra_body |
| Baseline byte-exact capture + verify | Custom snapshot logic | `snapshot.capture_baselines` + `snapshot.verify_baselines` + `snapshot.compute_provenance` | Already anti-spoofs via hardcoded EXPERT_DIRS, handles git-unavailable fallback, WR-08 schema validation |
| Patch apply/revert | Custom diff parser | `git apply --check` + `git apply` + `git checkout --` (subprocess) | git is always present (repo is a git repo); `--check` gives free validation; `patch` lib adds a dep CONTEXT.md rejected |
| Prompts loading | Custom YAML loader | `runner.load_prompts(prompts_path)` | Already validates YAML schema (`expert_id` + `prompts[].id/text`), handles encoding |
| Decision-tag parsing | Custom regex | `runner.parse_judge_decision(raw_text)` | Already case-insensitive, T-00-11 fail-safe to "tie", logs warning on missing tag |
| Paired-t t-statistic | Custom from scratch | `statistics.mean(diffs)` + `statistics.stdev(diffs)` + `t = mean / (std / sqrt(n))` | stdlib, no dep. p-value is the only piece stdlib can't compute — see Open Questions |

**Key insight:** The gate is an **orchestrator**, not a reimplementation. Every primitive it needs (judge client, position swap, prompts, baseline, decision parse) already exists in `runner.py` + `snapshot.py`. The ONLY genuinely new logic is: (1) `parse_judge_scores()` numeric extraction (because v1 discarded the numbers), (2) threshold decision function, (3) patch apply/revert subprocess wrappers, (4) reject-log serialization, (5) exit-code mapping. Everything else is composition.

## Runtime State Inventory

> Phase 30 is a **new-feature / extension** phase, NOT a rename/refactor/migration phase. This section is included for completeness per the protocol; the phase creates new files and extends existing ones, it does not rename or migrate existing state.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — gate reports are written to `_eval/reports/<patch_id>.json` (new files, no existing data migrated) | None |
| Live service config | None — `_eval/` is offline tooling, not a live service | None |
| OS-registered state | None — no cron tasks, systemd units, or launchd plists | None |
| Secrets/env vars | `OPENROUTER_API_KEY` (existing, used by `runner.make_judge_client:438`). Gate reuses the SAME env var; no new secrets. | None — key unchanged |
| Build artifacts | None — `_eval/` has no compiled artifacts; `__pycache__/` auto-regenerated | None |

**Nothing found in any category.** Verified by: (a) `_eval/` directory inspection (no DB, no service files), (b) grep confirming `_eval` is not imported by runtime, (c) `OPENROUTER_API_KEY` is the only secret and it is pre-existing.

## Common Pitfalls

### Pitfall 1: Numeric Score Gap (CRITICAL — highest priority)
**What goes wrong:** A planner/implementer assumes `runner.py` already produces numeric scores and that the gate can simply aggregate `run_ablation` verdicts. In reality, `runner.py` parses ONLY the `<decision>A|B|tie</decision>` tag (`_DECISION_RE` at `runner.py:53`) and emits comparative verdicts. The judge_prompt.md *asks* for per-dimension scores (`industry_accuracy: 4 — justification`) but the harness **discards** them.
**Why it happens:** The judge prompt and the harness parser are misaligned — the prompt was written for a richer harness that was never implemented in v1 (Phase 0 skeleton). The `<decision>` tag was the minimal viable parse.
**How to avoid:** Phase 30 MUST add a `parse_judge_scores(raw_text: str) -> dict[str, float]` function to `runner.py` that lifts the 4 dimension scores via a new regex (e.g., `r"industry_accuracy:\s*([1-5](?:\.\d+)?)"`). Extend `run_position_swap` to return `scores_ab` + `scores_ba` alongside the existing fields. The gate averages the two orderings' scores per dimension (position-bias mitigation on the numeric axis). Tests must cover: well-formed response, missing dimension, out-of-range score, non-numeric score.
**Warning signs:** Gate reports show only `final: tie` with no numeric `mean_baseline` / `mean_candidate` / `delta` fields; GATE-02/04 cannot be evaluated; tests pass but gate is a no-op.

### Pitfall 2: LLM Judge Non-Determinism
**What goes wrong:** Even with `temperature=0.0` hard-pinned (EVAL-03, `runner.py:47`), LLM judges are not perfectly deterministic across runs (provider-side batching, minor floating-point variance). The same patch + baseline + prompt set can produce slightly different scores on re-run, flipping a borderline verdict.
**Why it happens:** OpenAI/OpenRouter providers do not guarantee bit-exact reproducibility at temp=0. This is a known limitation of LLM-as-judge methodologies (MT-Bench paper discusses it).
**How to avoid:** (a) Document that gate verdicts are "deterministic for a given judge response set, not for a given patch" — i.e., re-running may flip borderline cases. (b) The position-swap (2 rounds) partially mitigates by averaging out position bias. (c) The `min_prompts` floor (5) ensures single-prompt variance doesn't dominate. (d) Operators can use `--rebuild-baseline` to refresh if they suspect drift. (e) Reject-log includes `judge_model` + `ts` so re-runs are traceable.
**Warning signs:** Same patch gets `pass` then `fail_mean` on re-run with δ margin < 0.1. Expected for borderline patches; document as known limitation, not a bug.

### Pitfall 3: git apply Partial-Failure Leaves Dirty Working Tree
**What goes wrong:** `git apply` succeeds for some hunks but fails for others (e.g., patch was generated against a slightly different base). The working tree is left half-patched, and the revert (`git checkout -- <files>`) may not cleanly restore if the patch added new files.
**Why it happens:** Unified diffs are base-sensitive. If the candidate patch was generated against a SKILL.md that has since drifted (e.g., another patch landed first), hunks may not apply cleanly.
**How to avoid:** (a) ALWAYS run `git apply --check` first (validation, no working-tree mutation). If `--check` fails, exit early with `inconclusive` (exit 3) and a clear "patch does not apply cleanly against current base" message. (b) If `--check` passes but `git apply` still fails (race condition), the `try/finally` ensures `git checkout -- <files>` runs. (c) For patches that ADD new files, `git checkout -- <new_file>` will fail (file doesn't exist in HEAD) — handle by deleting new files explicitly if they don't exist in HEAD. (d) Document: gate assumes patches are generated against the current `HEAD` of the target skill.
**Warning signs:** `git apply --check` returns non-zero; `git status` shows untracked files after a failed run.

### Pitfall 4: Baseline Cache Staleness
**What goes wrong:** The cached baseline scores (in `_eval/baseline/<skill>/scores.json`) were generated against an older SKILL.md / judge_model. A candidate patch is scored against this stale baseline, producing misleading deltas.
**Why it happens:** Baseline scores are expensive to regenerate (~30 min for full benchmark per CONTEXT.md). Operators cache them and forget to refresh when the underlying SKILL.md or judge model changes.
**How to avoid:** (a) Baseline `scores.json` MUST record the `baseline_skill_sha256` (from `snapshot.py:compute_provenance`) + `judge_model` + `generated_at` it was built against. (b) On gate run, compare current target SKILL.md sha256 against the cached `baseline_skill_sha256`. If they differ, the baseline is stale — emit a warning + suggestion to run `--rebuild-baseline`. (c) Optionally: refuse to run (exit 3 inconclusive) if baseline is stale, forcing operator to refresh. CONTEXT.md marks cache invalidation mechanism as "plan-phase decides" — recommend the warning + suggest path (non-blocking) to avoid friction.
**Warning signs:** `baseline_skill_sha256` in `scores.json` doesn't match current SKILL.md sha256; deltas look implausibly large.

### Pitfall 5: Position-Swap Order Bias on Numeric Scores
**What goes wrong:** The judge gives slightly different numeric scores to the same answer depending on whether it appears as "Answer 1" or "Answer 2" (primacy effect). Averaging only one ordering biases the composite.
**Why it happens:** Position bias is the core problem MT-Bench's position-swap design solves for the A/B/tie axis. The same bias exists on the numeric axis but v1 didn't address it (v1 only parsed the decision tag).
**How to avoid:** `run_position_swap` already calls the judge TWICE (swap=False then swap=True). The gate MUST extract numeric scores from BOTH orderings and average them per dimension: `composite_score = mean(scores_ab[dim], scores_ba[dim])` for each dimension, then `prompt_score = mean(4 dimensions)`. This mirrors the existing `_final_verdict` collapse but for numbers. Document this in `gate.py` docstring.
**Warning signs:** `scores_ab` and `scores_ba` differ by more than 0.5 on any dimension for the same answer.

### Pitfall 6: pyproject.toml testpaths Excludes _eval/tests
**What goes wrong:** Developer runs `pytest` (or CI runs the default suite) and the gate tests are silently skipped because `testpaths = ["tests"]` (`pyproject.toml:349`) only collects from the repo-root `tests/` directory, not from `skills/movie-experts/_eval/tests/`.
**Why it happens:** The `_eval/` tests predate the v6.0 work and were designed to run standalone (`python -m pytest skills/movie-experts/_eval/tests/`), matching the existing `test_runner.py` + `test_snapshot.py` pattern.
**How to avoid:** (a) Document the explicit test invocation in the plan + Validation Architecture section below. (b) Do NOT add `_eval/tests` to `testpaths` globally — that would couple offline tooling tests to the main suite (slowdown + potential import side-effects). (c) The gate tests follow the EXISTING `_eval/tests/` convention (`test_runner.py:25-29` uses `sys.path.insert` to import `runner` as a sibling). Match this pattern for `test_gate.py`.
**Warning signs:** CI passes but gate tests never ran; local `pytest` shows 0 tests for gate.

## Code Examples

### Numeric Score Extraction (the GATE-02/04 enabler)
```python
# Source: derived from judge_prompt.md dimension format + runner.py _DECISION_RE pattern
import re
from typing import Any

_DIMENSIONS = ("industry_accuracy", "professional_depth", "actionability", "language_quality")
# Matches "industry_accuracy: 4 — ..." or "industry_accuracy: 4.5 - ..." (em-dash or hyphen)
_SCORE_RE_TEMPLATE = r"{dim}:\s*([1-5](?:\.\d+)?)"

def parse_judge_scores(raw_text: str) -> dict[str, float]:
    """Extract the 4 per-dimension numeric scores from a judge response.

    Returns a dict mapping each dimension name to its float score (1.0-5.0).
    Missing dimensions are omitted from the dict; the caller decides whether
    to treat absence as a hard error or impute a neutral score (recommend:
    hard error — a judge that ignores the output format is unreliable).

    Fail-safe: if NO dimensions are found, returns an empty dict. The gate
    treats an empty dict as a failed prompt (excluded from n_valid, counts
    toward the min_prompts floor).
    """
    scores: dict[str, float] = {}
    for dim in _DIMENSIONS:
        pattern = _SCORE_RE_TEMPLATE.format(dim=re.escape(dim))
        m = re.search(pattern, raw_text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            if 1.0 <= val <= 5.0:
                scores[dim] = val
            # Out-of-range scores are silently dropped (treated as missing)
    return scores

def composite_score(scores: dict[str, float]) -> float | None:
    """Mean of available dimension scores, or None if none present."""
    if not scores:
        return None
    vals = list(scores.values())
    return sum(vals) / len(vals)
```

### Paired-t Computation (stdlib only, no scipy)
```python
# Source: paired t-test formula + statistics module docs
import math
import statistics

def paired_t_stats(baseline: list[float], candidate: list[float]) -> dict[str, float | int | None]:
    """Compute paired t-test statistics using stdlib only.

    Returns dict with: t_stat, n, df, mean_diff, std_diff.
    p_value is NOT computed (stdlib lacks t-distribution CDF). Caller
    may look up critical-t from a hardcoded table OR interpret t_stat
    heuristically (|t| > 2 is a common rough significance threshold for
    small n).
    """
    n = min(len(baseline), len(candidate))
    if n < 2:
        return {"t_stat": None, "n": n, "df": n - 1, "mean_diff": None, "std_diff": None, "p_value": None}
    diffs = [c - b for c, b in zip(candidate, baseline)]
    mean_diff = statistics.mean(diffs)
    if n < 2:
        std_diff = 0.0
    else:
        std_diff = statistics.stdev(diffs)  # sample std (n-1 denominator)
    if std_diff == 0:
        t_stat = 0.0 if mean_diff == 0 else float("inf")
    else:
        t_stat = mean_diff / (std_diff / math.sqrt(n))
    return {
        "t_stat": round(t_stat, 4),
        "n": n,
        "df": n - 1,
        "mean_diff": round(mean_diff, 4),
        "std_diff": round(std_diff, 4),
        "p_value": None,  # stdlib cannot compute; operator interprets t_stat
    }

# Hardcoded critical-t table (two-tailed, alpha=0.05) for small df —
# ships in gate.py as a module constant. Source: standard t-table.
_CRITICAL_T_05_TWO_TAILED = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
    6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
    15: 2.131, 20: 2.086, 25: 2.060, 30: 2.042,
}

def is_significant(t_stat: float, df: int, alpha: float = 0.05) -> bool:
    """Approximate significance check via critical-t lookup."""
    if alpha != 0.05:
        return False  # table only has alpha=0.05; extend if needed
    # Find nearest df in table (round down to be conservative)
    crit = _CRITICAL_T_05_TWO_TAILED.get(df)
    if crit is None:
        # For df > 30, use the asymptotic normal value
        crit = 1.960 if df > 30 else _CRITICAL_T_05_TWO_TAILED[max(k for k in _CRITICAL_T_05_TWO_TAILED if k <= df)]
    return abs(t_stat) > crit
```

### Exit Code Mapping
```python
# Source: CONTEXT.md <decisions> Gate CLI Surface
import sys

VERDICT_TO_EXIT = {
    "pass": 0,
    "fail_mean": 1,
    "fail_regression": 2,
    "inconclusive": 3,
}

def emit_exit(verdict: str) -> int:
    """Map verdict to exit code and sys.exit."""
    code = VERDICT_TO_EXIT.get(verdict, 3)  # unknown verdict → inconclusive
    sys.exit(code)
```

### Reject-Log JSON Shape (refined from CONTEXT.md)
```json
{
  "schema_version": 1,
  "patch_id": "screenplay_20260624_191230_a1b2c3d4",
  "skill_id": "screenplay",
  "patch_path": "candidate.patch",
  "patch_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "ts": "2026-06-24T19:12:30Z",
  "verdict": "fail_regression",
  "thresholds": {
    "delta": 0.3,
    "per_prompt": 1.0,
    "min_prompts": 5,
    "ab_positions": 2
  },
  "judge_model": "claude-sonnet-4-6",
  "baseline": {
    "skill_sha256": "96293f1c5778ed3bec7ab81505e1e15b551370b9a5a863e528f52ad8a3976c33",
    "scores_generated_at": "2026-06-15T04:16:10Z",
    "mean_composite": 3.2
  },
  "candidate": {
    "skill_sha256": "<patched-skill-sha256>",
    "mean_composite": 3.0,
    "mean_delta": -0.2
  },
  "per_prompt": [
    {
      "prompt_id": "sc-001",
      "baseline_composite": 3.5,
      "candidate_composite": 3.0,
      "delta": -0.5,
      "regression": false,
      "scores_ab": {"industry_accuracy": 3, "professional_depth": 4, "actionability": 3, "language_quality": 4},
      "scores_ba": {"industry_accuracy": 3, "professional_depth": 3, "actionability": 3, "language_quality": 3},
      "decision_ab": "A",
      "decision_ba": "B",
      "final": "tie"
    },
    {
      "prompt_id": "sc-002",
      "baseline_composite": 2.8,
      "candidate_composite": 1.5,
      "delta": -1.3,
      "regression": true,
      "scores_ab": {"industry_accuracy": 2, "professional_depth": 1, "actionability": 1, "language_quality": 2},
      "scores_ba": {"industry_accuracy": 2, "professional_depth": 2, "actionability": 1, "language_quality": 2},
      "decision_ab": "A",
      "decision_ba": "A",
      "final": "A_wins"
    }
  ],
  "paired_t": {
    "t_stat": -2.411,
    "n": 5,
    "df": 4,
    "mean_diff": -0.5,
    "p_value": null,
    "significant_at_0.05": false,
    "note": "p_value not computed (stdlib only); |t_stat|=2.411 < critical_t(df=4)=2.776"
  },
  "n_valid_prompts": 5,
  "operator_hint": "Patch rejected: prompt sc-002 regressed by -1.3 (threshold -1.0). Override with --per-prompt-threshold 1.5 if intentional."
}
```

**Refinements over the CONTEXT.md draft:**
- Added `patch_path`, `patch_sha256`, `baseline.skill_sha256`, `candidate.skill_sha256` for full provenance (enables P32 audit trail to trace reject to exact patch bytes).
- Added per-prompt `scores_ab` / `scores_ba` / `decision_ab` / `decision_ba` / `final` for full debuggability (operator can see WHY a prompt regressed).
- Added `paired_t.significant_at_0.05` (boolean from t-table lookup) + `note` explaining the p_value omission — operators get an interpretable significance signal without scipy.
- Added `operator_hint` — a human-readable one-liner suggesting the override flag if the rejection is borderline. This closes the "patch auto-tuning" deferred idea halfway (CONTEXT.md deferred full auto-tuning but a hint is cheap).
- `schema_version: 1` for forward-compat (CONTEXT.md discretion item).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| v1 harness: A/B/tie comparative only | Gate: numeric per-dimension scores (1-5) + composite + thresholds | Phase 30 (this phase) | Enables GATE-02 (mean δ) + GATE-04 (per-prompt regression) which are numeric by definition |
| Manual baseline rebuild | Cached baseline `scores.json` + `--rebuild-baseline` flag | Phase 30 | Cuts LLM cost ~50% per gate run (baseline not re-evaluated each time) |
| No patch-vs-baseline automation | `gate.py` orchestrator: apply → eval → decide → revert → report | Phase 30 | Enables P31 EVOL + P32 Curator to auto-reject bad patches pre-review |
| Single-ordering scoring | Position-swapped numeric averaging (scores_ab + scores_ba) | Phase 30 | Mitigates numeric position bias (mirrors existing A/B/tie swap) |

**Deprecated/outdated:**
- `runner.py:run_ablation` for gate purposes: still valid for multi-condition research ablation, but the gate uses a focused 2-condition (baseline vs candidate) path via `run_position_swap` directly. Do NOT remove `run_ablation` (it's reused by future research phases).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The judge (claude-sonnet-4-6 or qwen3-235b) reliably emits per-dimension scores in the `<dimension>: <score> — <justification>` format when asked by judge_prompt.md | Standard Stack / Pitfall 1 | If the judge omits scores, `parse_judge_scores` returns empty dict, composite is None, all prompts fail → gate always returns `inconclusive`. Mitigation: test with real judge early; if unreliable, fall back to mapping A/B/tie to numeric (A_win=+1, tie=0, B_win=-1) as a degraded mode. |
| A2 | `git apply --check` + `git apply` + `git checkout --` is sufficient for all candidate patches P31/P32 will generate | Architecture Patterns / Pattern 2 | If P31 generates patches that add new files, `git checkout -- <new_file>` fails (file not in HEAD). Mitigation: detect new files via `+++ /dev/null` absence in patch header and `git clean -f <new_file>` them instead. Handle in `revert_patch()`. |
| A3 | A hardcoded t-table (df 1-30, α=0.05 two-tailed) is sufficient for significance reporting | Code Examples / Pitfall (p-value) | If prompt set grows beyond 31 prompts (df>30), the table falls back to asymptotic normal (1.960). Slight inaccuracy for 30<df<∞. Acceptable for a gate (significance is advisory, not load-bearing — the δ and per-prompt thresholds are the actual gate). |
| A4 | `_eval/tests/` remaining outside `testpaths` is acceptable (run via explicit invocation) | Pitfall 6 / Validation Architecture | If CI only runs `pytest` (default testpaths), gate tests are skipped. Mitigation: document explicit invocation in plan + add a CI step OR a make target. Confirm with operator. |
| A5 | Baseline scores cache (`scores.json`) can be lazily populated on first gate run per skill | Architecture / Pattern 2 | First gate run for a skill with no cached baseline triggers a full baseline eval (~30 min). If P31 invokes gate automatically, this blocks the pipeline. Mitigation: `--rebuild-baseline` is operator-initiated; lazy-populate logs a clear "building baseline, this takes ~30 min" message. |
| A6 | The position-swap numeric averaging (mean of scores_ab + scores_ba per dimension) is a sound bias-mitigation strategy | Pitfall 5 | If numeric position bias is asymmetric (e.g., Answer 1 always scores 0.5 higher regardless of content), averaging still leaves residual bias. Mitigation: this matches the A/B/tie collapse philosophy; document as known limitation; multi-judge ensemble (FUTURE-V6-05) is the long-term fix. |

## Open Questions (RESOLVED at plan-phase 2026-06-24)

> All four open questions resolved during `/gsd:plan-phase 30`. Decisions encoded into `30-01-PLAN.md` + `30-02-PLAN.md`.

1. **p-value: compute or omit? — RESOLVED: Ship hardcoded t-table (boolean significance). p_value field is null in stdlib path.**
   - Decision: Ship the hardcoded t-table approach (boolean `significant_at_0.05` + `t_stat` + `n` + `df` + `mean_diff` + `std_diff`) as the default AND only path. `p_value` field is present in the reject-log JSON but always `null`, with a `note` explaining the stdlib-only constraint. NO optional scipy path — keeps `_eval/` stdlib-only convention uncompromised (avoids "two code paths" maintenance cost). Operators interpret significance via `significant_at_0.05` boolean + raw `t_stat` + `df`.
   - Encoded in: `30-02-PLAN.md` Task 1 (`paired_t_stats` + `is_significant` + `_CRITICAL_T_05_TWO_TAILED` constant).

2. **Answer generation: who produces baseline_answers / candidate_answers? — RESOLVED: Phase 30 assumes pre-generated answers (JSON file input). P31 bridges runtime.**
   - Decision: Phase 30 ships the gate logic assuming answers are pre-generated, passed via `--baseline-answers <path.json>` + `--candidate-answers <path.json>` CLI flags. NO live answer generation in P30 — keeps `_eval/` pure offline tooling (no Hermes runtime touch, preserves parallel-eligibility with P31). P31 (Knowledge Evolution Pipeline) bridges the runtime: it invokes the Hermes agent to generate candidate answers from the patched SKILL.md, then calls `gate.run_gate()`. This is the lower-risk alternative identified in research.
   - Encoded in: `30-01-PLAN.md` Task 2 (`run_gate` signature accepts `baseline_answers_path` + `candidate_answers_path` JSON inputs; module docstring states "Pre-generated answers input only; live answer generation is P31 scope").

3. **Gate invocation: subprocess or import? — RESOLVED: Support both. `run_gate()` importable function + `main()` CLI.**
   - Decision: `gate.py` exposes BOTH a `run_gate(patch_path, skill_id, baseline_answers_path, candidate_answers_path, config, ...) -> GateResult` function (importable — P31/P32 may `from gate import run_gate`) AND a `main(argv) -> int` CLI (subprocess-invocable via `python skills/movie-experts/_eval/gate.py ...`). Both paths share the same implementation (`main` calls `run_gate` internally). Documented in the gate's module docstring.
   - Encoded in: `30-01-PLAN.md` Task 2 (both `run_gate` and `main` specified in the public API list).

4. **Multi-skill patch detection — RESOLVED: Detect-and-warn via patch-header parse, exit 3 if multi-skill without --multi-skill.**
   - Decision: `detect_multi_skill_patch(patch_path) -> set[str]` parses `+++ b/skills/movie-experts/<skill>/` paths and returns the set of distinct skill directory names. When >1 skill detected and `--multi-skill` flag is absent, `run_gate()` early-exits with `verdict="inconclusive"`, `exit_code=3`, warning message naming the skills touched, and the patch is NOT applied (no working-tree mutation on early exit). With `--multi-skill` flag, gate proceeds (operator takes responsibility for per-skill interpretation).
   - Encoded in: `30-02-PLAN.md` Task 2 (`detect_multi_skill_patch` + multi-skill guard in `run_gate` + `--multi-skill` CLI flag).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | Gate runtime | ✓ | 3.12.3 (env) / 3.13 (ty) | — |
| git | Patch apply/revert (`gate.py`) | ✓ | 2.43.0 | — |
| `OPENROUTER_API_KEY` env var | LLM judge calls (live mode) | ✓ (operator-local) | — | `--dry-run` stub judge for tests |
| `openai` SDK | Judge client (`runner.make_judge_client`) | ✓ | 2.24.0 (pyproject:34) | — |
| `pyyaml` | Config + prompts loading | ✓ | 6.0.3 | — |
| `jinja2` | Judge prompt template | ✓ | 3.1.6 | — |
| `scipy` (optional) | Precise p-value (if operator opts in) | ✓ (transitive) | 1.17.1 | Hardcoded t-table (stdlib path) |
| `pytest` | Gate tests | ✓ | 9.0.2 | — |

**Missing dependencies with no fallback:** None — all required deps available.

**Missing dependencies with fallback:** None material. `scipy` is optional (t-table fallback covers the default path).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 (existing) |
| Config file | `pyproject.toml:[tool.pytest.ini_options]` (line 348) — BUT `testpaths = ["tests"]` EXCLUDES `_eval/tests/` |
| Quick run command | `python -m pytest skills/movie-experts/_eval/tests/ -x -q` |
| Full suite command | `python -m pytest skills/movie-experts/_eval/tests/ -v` (gate + runner + snapshot) |

> **Critical:** The main `pytest` invocation (no path arg) does NOT collect `_eval/tests/` due to `testpaths = ["tests"]`. Gate tests MUST be run via the explicit path above. This matches the existing `test_runner.py` + `test_snapshot.py` convention (they already run this way). Do NOT modify `testpaths` to include `_eval/tests/` — that couples offline tooling tests to the main suite. Document the explicit invocation in the plan.

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GATE-01 | Gate applies candidate patch, runs eval against baseline, reverts | integration | `python -m pytest skills/movie-experts/_eval/tests/test_gate_integration.py::TestPatchApplyRevert -x` | ❌ Wave 0 |
| GATE-01 | `--rebuild-baseline` regenerates cached scores | unit | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestRebuildBaseline -x` | ❌ Wave 0 |
| GATE-01 | Baseline lazy-populates on first run if missing | unit | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestLazyBaseline -x` | ❌ Wave 0 |
| GATE-02 | Patch with mean_delta < -0.3 → verdict=fail_mean, exit 1 | unit | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestDecideVerdict::test_fail_mean -x` | ❌ Wave 0 |
| GATE-02 | Patch with mean_delta >= -0.3 (and no per-prompt regression) → verdict=pass, exit 0 | unit | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestDecideVerdict::test_pass -x` | ❌ Wave 0 |
| GATE-02 | CLI `--threshold-delta` overrides config | unit | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestConfigOverride -x` | ❌ Wave 0 |
| GATE-03 | Position-swap runs 2 rounds (A-first, B-first) per prompt | unit | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestPositionSwapNumeric -x` | ❌ Wave 0 |
| GATE-03 | Paired-t stats computed (t_stat, n, df) | unit | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestPairedT -x` | ❌ Wave 0 |
| GATE-03 | Reject-log JSON has required fields (schema_version, verdict, paired_t, per_prompt) | unit | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestRejectLogSchema -x` | ❌ Wave 0 |
| GATE-04 | Patch with any per-prompt delta < -1.0 → verdict=fail_regression, exit 2 | unit | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestDecideVerdict::test_fail_regression -x` | ❌ Wave 0 |
| GATE-04 | Per-prompt threshold overridable via `--per-prompt-threshold` | unit | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestConfigOverride::test_per_prompt_override -x` | ❌ Wave 0 |
| GATE-* | n_valid < min_prompts → verdict=inconclusive, exit 3 | unit | `python -m pytest skills/movie-experts/_eval/tests/test_gate.py::TestDecideVerdict::test_inconclusive -x` | ❌ Wave 0 |
| GATE-* | `parse_judge_scores` extracts 4 dimensions from well-formed response | unit | `python -m pytest skills/movie-experts/_eval/tests/test_runner.py::TestParseJudgeScores -x` | ❌ Wave 0 (extends existing test_runner.py) |
| GATE-* | `parse_judge_scores` handles missing/malformed dimensions gracefully | unit | `python -m pytest skills/movie-experts/_eval/tests/test_runner.py::TestParseJudgeScores::test_malformed -x` | ❌ Wave 0 |
| GATE-* | End-to-end with MockJudgeClient + synthetic patch (no real API) | integration | `python -m pytest skills/movie-experts/_eval/tests/test_gate_integration.py::TestEndToEnd -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest skills/movie-experts/_eval/tests/ -x -q` (gate + runner + snapshot, ~28 existing + ~30 new tests, < 5s with mocks)
- **Per wave merge:** Same as above + `ruff check skills/movie-experts/_eval/` (PLW1514 encoding rule)
- **Phase gate:** Full `_eval/tests/` green + one live `--dry-run` gate invocation on a synthetic patch (proves CLI surface end-to-end)

### Wave 0 Gaps
- [ ] `skills/movie-experts/_eval/tests/test_gate.py` — gate logic unit tests (config load, threshold decision, reject-log emit, paired-t, exit codes). Covers GATE-02/03/04 + min_prompts.
- [ ] `skills/movie-experts/_eval/tests/test_gate_integration.py` — end-to-end with MockJudgeClient + synthetic patch + temp git repo (apply/revert mechanics). Covers GATE-01.
- [ ] Extend `skills/movie-experts/_eval/tests/test_runner.py` — add `TestParseJudgeScores` class (numeric extraction, the GATE-02/04 enabler).
- [ ] `skills/movie-experts/_eval/gate_config.yaml.example` — committed default config (δ=0.3, per_prompt=1.0, min_prompts=5, ab_positions=2, judge_model).
- [ ] No framework install needed — pytest 9.0.2 already available.

## Security Domain

> `_eval/` is offline developer tooling (confirmed by grep — zero runtime imports). Security exposure is limited to: (a) patch file handling (path traversal via crafted patch header), (b) judge API key handling, (c) subprocess invocation (`git apply`). No network-facing surface, no user-input-facing surface in production.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — offline tooling |
| V3 Session Management | no | N/A — offline tooling |
| V4 Access Control | yes (path traversal guard) | Patch header parsing MUST reject paths escaping `_eval/` or `skills/` (e.g., `+++ b/../../../etc/passwd`). Validate extracted paths are under `skills/movie-experts/`. |
| V5 Input Validation | yes | `gate_config.yaml` validated against expected schema (δ in [0,5], per_prompt in [0,5], min_prompts >= 1, ab_positions in {1,2}). Patch file validated via `git apply --check` before mutation. |
| V6 Cryptography | yes (sha256 provenance) | `hashlib.sha256` for patch_id + skill sha256 (matches `snapshot.py`). Never hand-roll. |
| V7 Error Handling & Logging | yes | `OPENROUTER_API_KEY` never logged (T-00-09, enforced by `runner.make_judge_client`). Subprocess errors captured + logged. |
| V8 Data Protection | yes (reject-log may contain skill content snippets) | Reject-log per-prompt entries contain composite scores only, NOT full answer text (avoid persisting potentially-sensitive model output). Full answers stay in transient memory. |

### Known Threat Patterns for `_eval/` gate

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Crafted patch header escapes skills/ dir (path traversal) | Tampering | `extract_patched_files()` rejects any path not starting with `skills/movie-experts/`. `git apply --check` fails on such paths anyway. |
| Malformed gate_config.yaml causes crash | Denial of Service | Pydantic-style validation (or manual) on config load; fail-fast with clear error (matches `runner.py` WR-04 pattern). |
| `OPENROUTER_API_KEY` leaked in logs | Information Disclosure | `runner.make_judge_client:441-444` raises if missing; never logs key value. Gate inherits this. |
| Subprocess injection via patch filename | Tampering | Patch path passed as separate argv element to `subprocess.run([...])`, NOT shell-interpolated. No `shell=True`. |
| Judge response injection (crafted scores) | Tampering | `parse_judge_scores` validates score range [1.0, 5.0]; out-of-range silently dropped. Regex is bounded, no ReDoS risk (fixed pattern per dimension). |

## Sources

### Primary (HIGH confidence)
- `skills/movie-experts/_eval/runner.py` (full read, 648 lines) — confirmed comparative-only parsing (`_DECISION_RE:53`), position-swap mechanics (`run_position_swap:241`), ablation (`run_ablation:280`), fail-fast patterns (WR-03/04), temperature hard-pin (EVAL-03), stub client
- `skills/movie-experts/_eval/snapshot.py` (full read, 466 lines) — confirmed stdlib-only convention (`:14`), EXPERT_DIRS anti-spoofing (`:40-55`), provenance schema, git-unavailable fallback
- `skills/movie-experts/_eval/judge_prompt.md` (full read) — confirmed 4-dimension scoring instruction (industry_accuracy/professional_depth/actionability/language_quality, 1-5 each) + `<decision>` tag. **Critical: prompt asks for numeric scores but harness only parses the decision tag.**
- `skills/movie-experts/_eval/tests/test_runner.py` (full read, 323 lines) — confirmed MockJudgeClient pattern, sibling-import convention (`sys.path.insert` at line 26), test class structure
- `.planning/phases/30-eval-gate-reuse/30-CONTEXT.md` — locked decisions (patch format, baseline source, thresholds, A/B scope)
- `.planning/REQUIREMENTS.md` — GATE-01..04 definitions
- `.planning/ROADMAP.md` — Phase 30 success criteria (5 criteria including v5/v4 refs byte-intact check)
- `pyproject.toml:349` — `testpaths = ["tests"]` confirmed (excludes `_eval/tests/`)
- `pyproject.toml:34,175` — `openai==2.24.0` direct, `numpy==2.4.3` direct; `scipy` NOT direct (transitive only)
- `agent/feedback_schema.py:149-210` — FeedbackRecord + OutputSnapshot schema (P28 contract that P31 consumes; gate reports are a separate schema)
- `grep -rn "from _eval\|import _eval"` — ZERO matches outside `_eval/`; confirms `_eval/` isolation from Hermes runtime

### Secondary (MEDIUM confidence)
- `_eval/reports/phase3-go-nogo.json` — Phase 3 GO/NOGO report structure (precedent for statistical-significance reporting format; used the dry-run stub signature "all_tie")
- `_eval/reports/screenplay_phase3.json` — sample verdict JSON shape (comparative-only, confirmed the numeric gap)
- `_eval/baseline/animator/PROVENANCE.json` — baseline provenance schema (sha256, git_sha, captured_at, tag)
- `git apply` / `git checkout` mechanics — verified end-to-end in `/tmp/gate_test` during research (apply → revert via both `git apply -R` and `git checkout --` both work)
- Python `statistics` module — verified `mean`, `stdev` available; `t_stat` computable; p-value NOT computable in stdlib

### Tertiary (LOW confidence)
- `scipy.stats.ttest_rel` behavior — verified available in env (1.17.1) but NOT a direct dependency; recommendation is to avoid for stdlib-only compliance (t-table fallback)
- Paired-t significance interpretation (|t|>2 rough threshold) — standard statistical heuristic, not project-specific

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages already pinned in pyproject.toml; no new deps; stdlib-only convention documented at `snapshot.py:14`
- Architecture: HIGH — `_eval/` structure fully mapped; runner.py + snapshot.py public APIs identified; integration points (P31/P32) documented in CONTEXT.md
- Pitfalls: HIGH — critical numeric-score gap verified by direct code read (runner.py:53 `_DECISION_RE` only parses decision tag, not dimension scores); git mechanics verified empirically; testpaths exclusion verified in pyproject.toml
- Validation: MEDIUM — test invocation path (explicit `_eval/tests/`) confirmed, but answer-generation strategy (Open Question 2) is unresolved and affects integration test design

**Research date:** 2026-06-24
**Valid until:** 2026-07-24 (30 days — stable domain, no fast-moving deps)

## RESEARCH COMPLETE

**Phase:** 30 - Eval Gate Reuse
**Confidence:** HIGH

### Key Findings
- **CRITICAL: Numeric score gap** — The v1 `runner.py` harness parses ONLY the `<decision>A|B|tie</decision>` tag and discards the per-dimension numeric scores (1-5) that `judge_prompt.md` explicitly requests. GATE-02 (mean δ=0.3) and GATE-04 (per-prompt 1.0) are **numeric** requirements. Phase 30 MUST add a `parse_judge_scores()` function to `runner.py` to lift the 4 dimension scores; this is the core extension point, not a wrapper-only change.
- **`_eval/` is fully isolated** from Hermes runtime — zero `from _eval` / `import _eval` matches outside `_eval/`. Extending it is offline-tooling work, NOT a Hermes-core touch (confirms CONTEXT.md + ROADMAP P30 SC #5).
- **Patch mechanics verified** — `git apply --check` (validate) + `git apply` (apply) + `git checkout -- <files>` (revert, files enumerated from patch header) all work end-to-end. No `patch` library needed.
- **scipy available but should be avoided** — `scipy` is transitively installed (1.17.1) but NOT a direct dependency (`pyproject.toml:175` shows only `numpy` direct). The `_eval/` stdlib-only convention (`snapshot.py:14`) recommends stdlib `statistics` + a hardcoded t-table for the paired-t, with scipy as an optional graceful-degradation path.
- **Test invocation is non-default** — `pyproject.toml:349` sets `testpaths = ["tests"]`, which EXCLUDES `_eval/tests/`. Gate tests run via `python -m pytest skills/movie-experts/_eval/tests/` (matching the existing `test_runner.py` + `test_snapshot.py` convention). Do NOT modify `testpaths`.

### File Created
`/data/workspace/hermes-agent/.planning/phases/30-eval-gate-reuse/30-RESEARCH.md`

### Confidence Assessment
| Area | Level | Reason |
|------|-------|--------|
| Standard Stack | HIGH | All packages already pinned; stdlib-only convention documented; no new deps |
| Architecture | HIGH | `_eval/` fully mapped; runner.py + snapshot.py public APIs identified; integration points documented |
| Pitfalls | HIGH | Numeric-score gap verified by direct code read; git mechanics verified empirically; testpaths exclusion confirmed |
| Validation | MEDIUM | Test invocation path confirmed, but answer-generation strategy (Open Question 2) unresolved |

### Open Questions (for discuss/plan-phase)
1. **p-value: compute or omit?** — Ship hardcoded t-table (boolean significance) as default; optional scipy path if operator needs precise p-value. Needs confirmation.
2. **Answer generation: who produces baseline/candidate answers?** — v1 `runner.py` does NOT implement live answer generation (`:601-606` errors out). Recommend Phase 30 assumes pre-generated answers (passed via JSON), with P31 bridging runtime. Alternative: P30 implements minimal answer-gen. **Needs plan-phase decision.**
3. **Gate invocation: subprocess or import?** — Recommend supporting both (`run_gate()` function + `main()` CLI). P31/P32 pick.
4. **Multi-skill patch detection** — Recommend detect-and-warn (cheap patch-header parse), exit 3 if multi-skill without `--multi-skill` flag.

### Ready for Planning
Research complete. The single load-bearing finding for the planner is the **numeric score extraction gap** — the plan MUST include a task to add `parse_judge_scores()` to `runner.py` before the gate logic can evaluate GATE-02/04. The position-swap mechanics, baseline caching, patch apply/revert, and reject-log serialization are all straightforward compositions over existing primitives. The planner should also resolve Open Question 2 (answer generation) before finalizing the task list, as it determines whether P30 stays pure offline tooling or bridges into Hermes runtime.
