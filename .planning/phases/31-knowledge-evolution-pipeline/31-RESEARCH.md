# Phase 31: Knowledge Evolution Pipeline - Research

**Researched:** 2026-06-24
**Domain:** LLM aggregation pipeline + unified-diff patch lifecycle + CLI review queue + git-backed atomic apply
**Confidence:** HIGH (all claims verified against codebase or stdlib docs)

## Summary

Phase 31 wires the self-learning loop end-to-end: feedback accumulated in Phase 29's `FeedbackStore` is aggregated by an LLM into structured insights, converted into unified-diff candidate patches, scored by Phase 30's `gate.py`, queued for operator review, and applied atomically with git-commit + rollback. The architecture reuses three shipped pieces directly — `agent/feedback_store.py:FeedbackStore` (P29), `skills/movie-experts/_eval/gate.py:run_gate` (P30), and the CLI registration pattern in `hermes_cli/feedback.py:register_cli` (P28). New code lives in a new `agent/evolution/` subpackage + 5 new subcommands appended to the existing `feedback` CLI.

**Primary recommendation:** Build four small modules under `agent/evolution/` (`insights.py` for LLM aggregation, `diff_generator.py` for stdlib `difflib`-based additive patches as the EVOL-02 placeholder, `queue.py` for the JSONL queue lifecycle, `apply.py` for the atomic git-backed apply with FOUND-08 byte-intact + additive-only verification). Wire them into `hermes_cli/feedback.py:register_cli` with 5 new subcommands. **Reuse Phase 30's `gate.py` subprocess patterns verbatim** (argv-list, never `shell=True`; `git apply --check` before `git apply`; try/finally revert) — they were hardened by T-30-01..T-30-04 mitigations and are the right primitives.

**Critical design decisions validated:**

1. **LLM emits "structured insight with proposed change description", NOT raw unified diff.** LLMs are unreliable at precise `@@ -A,B +C,D @@` hunk syntax; the pipeline uses stdlib `difflib.unified_diff` to convert "add this content after section X" into a real unified diff (CONTEXT.md Claude's Discretion, this research confirms option (b) from the objective).
2. **Additive-only verification is a pure-function regex pass over hunk headers + line prefixes.** No git operations needed for the verification itself — `@@ -1,X +1,Y @@` with `Y >= X` and zero lines starting with `-` (excluding `---`) is the contract. This is fast, deterministic, testable.
3. **FOUND-08 per-patch check uses `agent.skill_utils.parse_frontmatter` (agent/skill_utils.py:123)** — already shipped, already tested. Extract `expert_id` + `related_skills` from the SKILL.md *before* patch apply, extract again *after*, assert equal. ~5 lines of code.
4. **Atomic apply transaction = git apply → FOUND-08 check → additive check → git add → git commit → revert on any failure.** Mirrors Phase 30's `revert_patch` pattern (skills/movie-experts/_eval/gate.py:201) exactly, extended with the commit step.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**LLM Aggregation Trigger (EVOL-01):**
- CLI subcommand `hermes feedback evolve --skill <id>` — operator-invoked, synchronous. Reads `FeedbackStore.query(skill_id=<id>)` + `summary(skill_id=<id>)`, passes to LLM with an aggregation prompt, emits structured candidate insights to stdout + appends to `~/.hermes/skills/.feedback/evolution/insights.jsonl`.
- Each insight record: `{insight_id, skill_id, theme, evidence_chain: [feedback_id, ...], rationale, proposed_patch_summary, ts}`.
- Default model: agent's configured model (`agent.model_name` or equivalent). Override via `--model <name>`.
- No background daemon (scope discipline — daemon is P32 Curator scope). No per-feedback streaming.

**Patch Review Queue Format (EVOL-03):**
- `~/.hermes/skills/.feedback/evolution/queue.jsonl` — append-only JSONL. One line per pending patch.
- Patch record schema (see CONTEXT.md for full fields): `patch_id`, `skill_id`, `insight_id`, `unified_diff`, `feedback_chain`, `llm_rationale`, `eval_gate_score`, `status`, `ts_queued`.
- On approve → move to `applied.jsonl` with `commit_sha` + `ts_applied`.
- On reject → move to `rejected.jsonl` with `reason` + `ts_rejected`.
- SQLite rejected (overkill for ~10-100 pending patches).

**Patch Review UI (EVOL-03):**
- CLI viewer + approve/reject commands:
  - `hermes feedback review-queue [--skill <id>] [--status pending|applied|rejected]`
  - `hermes feedback show-patch <patch_id>`
  - `hermes feedback approve <patch_id>` (applies atomically; `--yes` for non-interactive)
  - `hermes feedback reject <patch_id> <reason>`
- No markdown report, no web dashboard (P33 scope).

**Patch Apply Git Workflow (EVOL-04):**
- Direct commit to current branch, atomic transaction:
  1. Apply unified diff via `git apply` (subprocess, no `shell=True`)
  2. Verify FOUND-08 byte-intact
  3. Verify additive-only for v4/v5 refs
  4. Stage modified files
  5. Commit with message: `feat(evolution): <insight_summary> | feedback: <ids> | eval: <score>`
  6. On ANY step failure: abort, restore working tree, exit non-zero
- Rollback via `git revert <commit_sha>` (operator-invoked, not automatic)
- Branch + PR rejected; dedicated evolution branch rejected.

### Claude's Discretion

- LLM aggregation prompt template (structured JSON output with `insights` array)
- Insight ID format (`f"{skill_id}_{ts_unix}_{sha256[:8]}"` recommended)
- Patch ID format (same as Phase 30: `f"{skill_id}_{ts_unix}_{sha256[:16]}"` per P30 WR-04)
- Operator approval prompt UI (`--yes` for scripted; default interactive `[y/N]`)
- Concurrent patch application (single-process assumed; document in module docstring)

### Deferred Ideas (OUT OF SCOPE)

- **EVOL-02 diff generator** — Mapped to Phase 32 (Curator invokes it). P31 uses a placeholder if EVOL-02 not yet shipped; tests mock the generator.
- **Background daemon** — P32 Curator scope.
- **Web dashboard for review queue** — P33 Observability scope.
- **Multi-skill patches in a single insight** — One insight = one skill patch.
- **Auto-rollback on regression detection** — v6 requires manual `git revert`.
- **Cross-operator patch sharing** — v6 is single-operator.
- **Patch dependency graph** — Patches applied independently.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EVOL-01 | 反馈→可执行知识点抽取 — LLM-based aggregation,跨多条反馈识别共性"应该改进什么",输出 candidate insights(结构化 JSON,带证据链指向具体反馈 IDs) | `agent/evolution/insights.py` (new) — `aggregate_feedback(skill_id, client) -> list[InsightRecord]`. Reuses `FeedbackStore.query(skill_id=...)` for input; LLM call via direct `OpenAI` SDK construction (pattern from `skills/movie-experts/_eval/runner.py:524 make_judge_client`). Output schema in CONTEXT.md. |
| EVOL-03 | Patch review queue — operator 可视化查看 pending patches,每条带 source 反馈链 + LLM 抽取理由 + 影响 skill 列表 | `agent/evolution/queue.py` (new) — JSONL queue at `~/.hermes/skills/.feedback/evolution/queue.jsonl`; `review-queue` / `show-patch` / `approve` / `reject` CLI subcommands appended to `hermes_cli/feedback.py:register_cli`. |
| EVOL-04 | Human-in-loop approve workflow — 所有 bundled movie-expert skill 的 patch 必须经 operator 审批才能 apply | ENFORCED BY ABSENCE OF AUTO-APPLY PATH. The `approve` subcommand is the ONLY entry point to the apply transaction; there is no programmatic auto-apply. The operator gate is non-bypassable because no code path calls `apply_patch_transaction()` except the `approve` CLI handler. |
| EVOL-05 | Patch apply + rollback — apply 前自动 git-commit(带 feedback IDs + eval score 在 commit message);rollback 子命令可回滚到任意历史版本 | `agent/evolution/apply.py` (new) — `apply_patch_transaction(patch_record, repo_root) -> ApplyResult`. Atomic steps per CONTEXT.md D-EVOL-04. Rollback via `git revert <sha>` exposed as `hermes feedback rollback <commit_sha>` subcommand. |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

The following CLAUDE.md directives are load-bearing for this phase and MUST be honored by the planner:

- **Tech stack**: SKILL.md + `references/*.md` pure markdown patches only; no Hermes Python/JS core modification (except new `agent/evolution/` modules + `hermes_cli/feedback.py` extension, which are explicitly in scope per CONTEXT.md domain boundary).
- **Ruff PLW1514**: Every `open()` MUST pass `encoding="utf-8"`. Phase 30 gate.py + Phase 29 feedback_store.py are exemplars.
- **`from __future__ import annotations`** at top of every new module (PEP 604 unions on 3.11+).
- **Specific exceptions bound with `as exc`**; no bare `except:`.
- **Lazy %-logging**: `logger.warning("...: %s", exc)`, never f-strings in log calls.
- **`get_hermes_home()`** from `hermes_constants` — never raw `Path.home() / ".hermes"`.
- **`subprocess.run([...], argv-list)`** — never `shell=True`. Phase 30 gate.py:172 `apply_patch` is the canonical pattern.
- **Pydantic for record schemas** (Phase 28/29 pattern; `agent/feedback_schema.py:FeedbackRecord`).
- **`snake_case.py` modules**, `snake_case` functions, `PascalCase` classes, `UPPER_SNAKE_CASE` constants.
- **Test files at `tests/<area>/test_<topic>.py`** mirroring source layout.
- **FOUND-08 frozen rule** (carried from v3.0): expert_id cannot silently rename; this phase MUST preserve expert_id + related_skills byte-for-byte per patch (SC-5).
- **v4/v5 refs byte-intact (additive-only)**: snowflake-method.md / e-konte-format.md / scamper-variations.md / dreamina-cli-baseline.md / v86-pipeline-mapping.md — existing bytes preserved, new knowledge appended (SC-6).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| LLM aggregation (EVOL-01) | Operator CLI (`hermes_cli/feedback.py`) | API / Backend (`agent/evolution/insights.py`) | Operator-invoked synchronous command; LLM call is a backend operation invoked from the CLI tier |
| Unified-diff generation (EVOL-02 placeholder) | API / Backend (`agent/evolution/diff_generator.py`) | — | Pure stdlib `difflib` transformation; no I/O, no tier above it |
| Patch review queue (EVOL-03) | Database / Storage (`~/.hermes/skills/.feedback/evolution/queue.jsonl`) | Operator CLI (viewer) | JSONL files under HERMES_HOME are the storage tier; CLI is read/write surface |
| Eval gate invocation (EVOL-05 precondition) | API / Backend (`agent/evolution/queue.py` → `gate.run_gate`) | — | Patches MUST pass gate before queue insertion; gate is invoked from the pipeline, not by the operator |
| Atomic apply + git commit (EVOL-05) | Operator CLI (`hermes_cli/feedback.py:approve`) | API / Backend (`agent/evolution/apply.py`) | Operator approves; backend executes the git transaction. The human-in-loop gate LIVES in the CLI tier — there is no programmatic auto-apply path. |
| FOUND-08 byte-intact verification | API / Backend (`agent/evolution/apply.py`) | — | Pure-function check inside the apply transaction; reuses `agent.skill_utils.parse_frontmatter` |
| Additive-only verification (v4/v5 refs) | API / Backend (`agent/evolution/apply.py`) | — | Pure-function regex pass over hunk headers; no I/O |
| Rollback (`git revert`) | Operator CLI (`hermes_cli/feedback.py:rollback`) | — | Operator-invoked restoration; thin wrapper over git subprocess |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `openai` | 2.24.0 (pinned in `pyproject.toml:34`) | LLM aggregation call in `agent/evolution/insights.py` | Every LLM call in Hermes routes through the OpenAI SDK (`CLAUDE.md` Technology Stack). `make_judge_client` at `skills/movie-experts/_eval/runner.py:524` is the canonical OpenRouter-via-OpenAI-SDK construction. `[VERIFIED: codebase grep — pyproject.toml:34, runner.py:537]` |
| `pydantic` | 2.13.4 (pinned in `pyproject.toml:44`) | Schema for `InsightRecord`, `PatchRecord`, `ApplyResult` dataclasses | Phase 28/29 established Pydantic for all feedback records (`agent/feedback_schema.py:FeedbackRecord`). `[VERIFIED: codebase grep — agent/feedback_schema.py:184]` |
| `difflib` | stdlib (Python 3.11+) | `unified_diff()` to convert LLM-proposed additions into unified diffs (EVOL-02 placeholder) | Already used in `tools/patch_parser.py:496`, `tools/skills_sync.py:948`, `tools/write_approval.py:486`. stdlib convention (snapshot.py:14) forbids third-party diff libs. `[VERIFIED: codebase grep]` |
| `subprocess` | stdlib | `git apply`, `git add`, `git commit`, `git checkout`, `git clean`, `git revert` | Phase 30 `gate.py:172 apply_patch` + `gate.py:201 revert_patch` are the canonical argv-list patterns. `[VERIFIED: codebase — skills/movie-experts/_eval/gate.py]` |
| `hashlib` | stdlib | sha256 for insight_id + patch_id generation; patch content addressing | Phase 30 `gate.generate_patch_id` (gate.py:525) uses `f"{skill_id}_{ts_unix}_{sha256[:16]}"`. `[VERIFIED: codebase]` |
| `argparse` | stdlib | CLI subcommand dispatch | `hermes_cli/feedback.py:40 register_cli` pattern; main.py:11993 wires it. `[VERIFIED: codebase]` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `yaml` (PyYAML) | 6.0.3 | Parsing SKILL.md frontmatter via `parse_frontmatter` for FOUND-08 check | Reuse `agent.skill_utils.parse_frontmatter` (skill_utils.py:123) — do NOT re-implement YAML parsing. `[CITED: agent/skill_utils.py:123]` |
| `logging` | stdlib | Lazy %-formatted diagnostics | Per CLAUDE.md Logging conventions; `_NOISY_LOGGERS` at `hermes_logging.py:54`. |
| `tempfile` | stdlib | Atomic patch file writing (mkstemp + os.replace) | Phase 30 `gate.rebuild_baseline` (gate.py:721) uses `tempfile.mkstemp(dir=..., prefix="scores.", suffix=".tmp")` for atomic writes. `[VERIFIED: codebase]` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Direct `openai.OpenAI()` construction in `insights.py` | `agent/auxiliary_client` existing machinery | Auxiliary client is async + thread-pool-based for the conversation loop — overkill for a single synchronous aggregation call. The `runner.make_judge_client` pattern (runner.py:524) is the right precedent: minimal, synchronous, OpenAI SDK direct. `[VERIFIED: codebase — simpler than auxiliary_client for one-shot LLM calls]` |
| JSONL append-only queue | SQLite | CONTEXT.md explicitly rejected SQLite as overkill for ~10-100 pending patches. JSONL aligns with Phase 28/29 feedback storage pattern. `[VERIFIED: CONTEXT.md D-EVOL-03]` |
| LLM emits raw unified diff | LLM emits structured "add X after section Y"; `difflib` generates diff | **Use the latter.** LLMs are unreliable at `@@ -A,B +C,D @@` syntax (research question #2). `difflib.unified_diff(current_lines, new_lines)` is deterministic, testable, and produces git-compatible output. `[ASSUMED — based on LLM behavior observation, not formal verification]` |
| `git apply` subprocess | Python `patch` library | Phase 30 already established the `git apply` subprocess pattern (gate.py:172). Using git directly is more robust (git handles edge cases), already tested, and the revert path (`git checkout --`) mirrors it. `[VERIFIED: codebase — gate.py]` |

**Installation:**
```bash
# No new packages to install — all dependencies already pinned in pyproject.toml.
# openai==2.24.0, pydantic==2.13.4, PyYAML==6.0.3 all present.
uv sync  # or: pip install -e .[dev]
```

**Version verification:**
```bash
# Already pinned in pyproject.toml — verify no drift:
grep -E "^(openai|pydantic|PyYAML)==" /data/workspace/hermes-agent/pyproject.toml
# openai==2.24.0
# pydantic==2.13.4
# PyYAML==6.0.3
```

## Package Legitimacy Audit

> **This phase installs ZERO new packages.** All dependencies (`openai`, `pydantic`, `PyYAML`, `difflib`, `subprocess`, `hashlib`, `argparse`, `tempfile`) are already pinned in `pyproject.toml` and shipped with prior phases. No slopcheck verification needed — nothing new to verify.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| (no new packages) | — | — | — | — | — | N/A — all reused from existing pins |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
Operator
   │
   │ 1. `hermes feedback evolve --skill screenplay`
   ▼
┌──────────────────────────────────────────────────────────────────┐
│  hermes_cli/feedback.py:_cmd_evolve                              │
│  ─────────────────────────────────────                           │
│  1. FeedbackStore.query(skill_id="screenplay")                   │
│  2. FeedbackStore.summary(skill_id="screenplay")                 │
│  3. construct OpenAI client (runner.make_judge_client pattern)   │
│  4. agent/evolution/insights.py:aggregate_feedback(...)          │
│     └─> LLM call → parse JSON → list[InsightRecord]              │
│  5. For each InsightRecord:                                      │
│     a. diff_generator.generate_diff(insight, current_skill) ──┐  │
│        └─> difflib.unified_diff → unified_diff string          │  │
│     b. Write diff to temp .patch file                          │  │
│     c. gate.run_gate(patch, skill, ...) ───────────────┐       │  │
│        └─> GateResult(verdict, ...)                     │       │  │
│     d. If verdict == "pass":                            │       │  │
│        queue.append(PatchRecord) → queue.jsonl          │       │  │
│     e. Else:                                            │       │  │
│        failed_gate.jsonl.append(rejection)              │       │  │
│                                                          │       │  │
│  6. stdout: insights summary + queue count               │       │  │
└──────────────────────────────────────────────────────────┼───────┘  │
                                                           │          │
                                                           ▼          │
                                              ┌──────────────────────┐ │
                                              │ Phase 30 gate.py     │ │
                                              │ (SHIPPED — reused)   │ │
                                              └──────────────────────┘ │
                                                                       │
Operator reviews queue:                                                │
   hermes feedback review-queue                                        │
   hermes feedback show-patch <patch_id>                               │
   │                                                                  │
   │ 2. Approves                                                      │
   ▼                                                                  │
┌──────────────────────────────────────────────────────────────────┐  │
│  hermes_cli/feedback.py:_cmd_approve                              │  │
│  ───────────────────────────────────────                          │  │
│  1. Load PatchRecord from queue.jsonl                             │  │
│  2. Write unified_diff to temp .patch                             │  │
│  3. agent/evolution/apply.py:apply_patch_transaction(...)         │  │
│     ┌─────────────────────────────────────────────────────┐       │  │
│     │ ATOMIC TRANSACTION (try/finally):                   │       │  │
│     │  1. git apply --check (validate)                    │       │  │
│     │  2. git apply (mutate working tree)                 │       │  │
│     │  3. FOUND-08 check: parse_frontmatter before/after  │       │  │
│     │  4. Additive-only check: regex over hunks           │       │  │
│     │  5. git add <files>                                 │       │  │
│     │  6. git commit -m "feat(evolution): ..."            │       │  │
│     │  ON FAILURE:                                        │       │  │
│     │    git checkout -- <files>  (existing files)        │       │  │
│     │    git clean -f <files>     (patch-added files)     │       │  │
│     │    raise ApplyError(evidence)                       │       │  │
│     └─────────────────────────────────────────────────────┘       │  │
│  4. queue.move(patch_id, "applied", commit_sha=<sha>)             │  │
│  5. stdout: commit_sha + success message                          │  │
└───────────────────────────────────────────────────────────────────┘  │
                                                                       │
Operator rolls back (sometime later):                                  │
   hermes feedback rollback <commit_sha>                               │
   └─> git revert <commit_sha> --no-edit                              │
```

A reader can trace the primary use case (feedback → insight → patch → gate → queue → approve → commit) by following the arrows from top to bottom. The two reused shipped components (FeedbackStore, gate.py) are explicitly boxed.

### Recommended Project Structure

```
agent/
├── evolution/                          # NEW — Phase 31 subpackage
│   ├── __init__.py                     # Public API re-exports
│   ├── insights.py                     # EVOL-01: LLM aggregation → InsightRecord
│   ├── diff_generator.py               # EVOL-02 placeholder: difflib-based additive diff
│   ├── queue.py                        # EVOL-03: JSONL queue lifecycle (append/move/read)
│   └── apply.py                        # EVOL-05: atomic git apply + commit + rollback
├── feedback_store.py                   # EXISTING (P29) — input source
├── feedback_schema.py                  # EXISTING (P28) — FeedbackRecord
└── skill_utils.py                      # EXISTING — parse_frontmatter (reuse for FOUND-08)

hermes_cli/
└── feedback.py                         # EXISTING (P28/29) — extend register_cli with 5 new subcommands

skills/movie-experts/_eval/
└── gate.py                             # EXISTING (P30) — run_gate reused as-is

tests/
├── agent/
│   └── evolution/                      # NEW — test directory
│       ├── __init__.py
│       ├── conftest.py                 # Shared fixtures: feedback_env, tmp_git_repo, mock_llm_client
│       ├── test_insights.py            # EVOL-01 aggregation logic (mock LLM)
│       ├── test_diff_generator.py      # difflib additive-only generation
│       ├── test_queue.py              # Queue append/move/read lifecycle
│       └── test_apply.py              # Atomic apply + FOUND-08 + additive + git commit
└── hermes_cli/
    └── test_evolution_cli.py           # CLI subcommand smoke tests (5 new commands)
```

### Pattern 1: LLM Client Construction (sync, one-shot)

**What:** Construct an `openai.OpenAI` client pointing at OpenRouter (or configured provider) for a single synchronous aggregation call.
**When to use:** Any operator-invoked LLM call from a CLI subcommand where async/thread-pool machinery is overkill.
**Example:**
```python
# Source: skills/movie-experts/_eval/runner.py:524 (make_judge_client) — VERIFIED
from __future__ import annotations

import os
from typing import Any


def make_aggregation_client(*, model_override: str | None = None) -> tuple[Any, str]:
    """Build a sync OpenAI client for feedback aggregation (EVOL-01).

    Mirrors runner.make_judge_client (runner.py:524) — fail-fast on missing
    API key, never log the key, return (client, model_name).

    Raises RuntimeError if OPENROUTER_API_KEY (or configured provider key)
    is absent — operators should see the error at construction time, not
    deep in a chat.completions.create call.
    """
    from openai import OpenAI

    base_url = os.environ.get(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Set it in ~/.hermes/.env "
            "or your shell, or pass --dry-run for offline testing."
        )
    client = OpenAI(base_url=base_url, api_key=api_key)
    model = model_override or os.environ.get(
        "HERMES_EVOLUTION_MODEL", "claude-sonnet-4-6"
    )
    return client, model
```

### Pattern 2: difflib-Based Additive Diff Generation (EVOL-02 Placeholder)

**What:** Convert an LLM-proposed "append this content to section X" into a real unified diff using stdlib `difflib`.
**When to use:** P31's placeholder for EVOL-02 (which P32 will extend with LLM-generated rewrites).
**Example:**
```python
# Source: tools/patch_parser.py:496 + tools/skills_sync.py:948 — VERIFIED difflib usage
from __future__ import annotations

import difflib
from pathlib import Path


def generate_additive_diff(
    *,
    current_content: str,
    proposed_addition: str,
    insert_after_marker: str,
    skill_md_path: str,  # repo-relative, e.g. "skills/movie-experts/screenplay/SKILL.md"
) -> str:
    """Generate a unified diff that ADDS content after a marker line.

    EVOL-02 placeholder (P32 will extend with LLM-generated rewrites).
    This function ONLY appends — it never modifies or deletes existing
    bytes, satisfying SC-6 (v4/v5 refs byte-intact) by construction.

    Args:
        current_content: The current SKILL.md (or ref) full text.
        proposed_addition: The new content to append (multi-line string).
        insert_after_marker: A substring identifying where to insert
            (e.g., "## References" or a unique line). The addition is
            inserted immediately AFTER the line containing this marker.
        skill_md_path: Repo-relative path for diff headers (a/... b/...).

    Returns:
        Unified diff string (git-compatible). If the marker is not found,
        raises ValueError — never silently appends to the wrong place.
    """
    current_lines = current_content.splitlines(keepends=True)
    # Find the insertion point.
    insert_idx = None
    for i, line in enumerate(current_lines):
        if insert_after_marker in line:
            insert_idx = i + 1
            break
    if insert_idx is None:
        raise ValueError(
            f"insert_after_marker {insert_after_marker!r} not found in "
            f"current content — refusing to generate blind-append diff"
        )

    addition_lines = proposed_addition.splitlines(keepends=True)
    # Ensure the addition starts with a newline if the previous line
    # doesn't end with one.
    if current_lines and not current_lines[insert_idx - 1].endswith("\n"):
        addition_lines = ["\n"] + addition_lines

    new_lines = (
        current_lines[:insert_idx]
        + addition_lines
        + current_lines[insert_idx:]
    )

    diff = "".join(
        difflib.unified_diff(
            current_lines,
            new_lines,
            fromfile=f"a/{skill_md_path}",
            tofile=f"b/{skill_md_path}",
            lineterm="\n",
        )
    )
    return diff
```

### Pattern 3: Atomic Patch Apply Transaction (EVOL-05)

**What:** Apply a candidate patch with full FOUND-08 + additive verification, git-commit on success, full revert on any failure.
**When to use:** The ONLY code path that mutates bundled SKILL.md / refs. Called exclusively from `hermes_cli/feedback.py:_cmd_approve` — never invoked programmatically.
**Example:**
```python
# Source: skills/movie-experts/_eval/gate.py:172 (apply_patch) +
#         skills/movie-experts/_eval/gate.py:201 (revert_patch) +
#         skills/movie-experts/_eval/gate.py:913 (run_gate try/finally) — VERIFIED
from __future__ import annotations

import subprocess
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ApplyResult:
    commit_sha: str
    files_modified: list[str]


def apply_patch_transaction(
    *,
    patch_path: Path,
    repo_root: Path,
    commit_message: str,
    protected_refs: tuple[str, ...] = (
        "snowflake-method.md",
        "e-konte-format.md",
        "scamper-variations.md",
        "dreamina-cli-baseline.md",
        "v86-pipeline-mapping.md",
    ),
) -> ApplyResult:
    """Apply a patch atomically: validate → apply → verify → commit.

    Mirrors Phase 30 gate.py:913 run_gate try/finally pattern. ANY
    failure in steps 2-5 triggers a full revert (steps from gate.py:201
    revert_patch). The working tree is NEVER left dirty on failure.

    Raises ApplyError on any failure (FOUND-08 violation, additive-only
    violation, git error). The error message is safe to show operators.
    """
    from agent.evolution.apply import (
        revert_files,
        verify_found08_byte_intact,
        verify_additive_only,
    )
    from skills.movie_experts._eval.gate import extract_patched_files  # reuse

    # Step 1: validate (no working-tree mutation yet).
    subprocess.run(
        ["git", "apply", "--check", str(patch_path)],
        cwd=str(repo_root), check=True, capture_output=True,
        text=True, encoding="utf-8",
    )

    # Pre-extract FOUND-08 baseline (frontmatter BEFORE patch).
    files = extract_patched_files(patch_path)
    frontmatter_before = {
        f: _extract_found08_fields(repo_root / f) for f in files
    }

    applied = False
    try:
        # Step 2: apply for real.
        subprocess.run(
            ["git", "apply", str(patch_path)],
            cwd=str(repo_root), check=True, capture_output=True,
            text=True, encoding="utf-8",
        )
        applied = True

        # Step 3: FOUND-08 byte-intact check (SC-5).
        for f in files:
            after = _extract_found08_fields(repo_root / f)
            if after != frontmatter_before[f]:
                raise ApplyError(
                    f"FOUND-08 violation: frontmatter drifted in {f} "
                    f"(before={frontmatter_before[f]}, after={after})"
                )

        # Step 4: additive-only check for protected refs (SC-6).
        for f in files:
            if any(protected in f for protected in protected_refs):
                if not verify_additive_only(patch_path, target_file=f):
                    raise ApplyError(
                        f"SC-6 violation: patch to protected ref {f} "
                        f"is not additive-only"
                    )

        # Step 5: stage + commit.
        subprocess.run(
            ["git", "add", "--"] + files,
            cwd=str(repo_root), check=True, capture_output=True,
            text=True, encoding="utf-8",
        )
        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=str(repo_root), check=True, capture_output=True,
            text=True, encoding="utf-8",
        )
        # Extract commit sha.
        sha_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root), check=True, capture_output=True,
            text=True, encoding="utf-8",
        )
        commit_sha = sha_result.stdout.strip()
        logger.info(
            "evolution patch applied: commit=%s files=%s",
            commit_sha[:12], files,
        )
        return ApplyResult(commit_sha=commit_sha, files_modified=files)
    except Exception as exc:
        # ALWAYS revert on any failure (T-30-04 pattern from gate.py:1084).
        logger.error(
            "apply_patch_transaction failed: %s — reverting working tree",
            exc,
        )
        if applied:
            try:
                revert_files(files, repo_root)
            except Exception as revert_exc:
                logger.error(
                    "revert ALSO failed: %s — WORKING TREE LEFT DIRTY "
                    "(files=%s). Manual `git checkout -- %s` required.",
                    revert_exc, files, " ".join(files),
                )
                raise ApplyError(
                    f"apply failed ({exc}) AND revert failed ({revert_exc}); "
                    f"working tree dirty — manual recovery required"
                ) from exc
        raise ApplyError(f"patch apply failed: {exc}") from exc


def _extract_found08_fields(skill_md_path: Path) -> dict[str, str]:
    """Extract expert_id + related_skills from SKILL.md frontmatter.

    Reuses agent.skill_utils.parse_frontmatter (skill_utils.py:123).
    Returns {"expert_id": ..., "related_skills": ...} or raises if the
    file is not a valid SKILL.md.
    """
    from agent.skill_utils import parse_frontmatter

    content = skill_md_path.read_text(encoding="utf-8")
    frontmatter, _body = parse_frontmatter(content)
    metadata = frontmatter.get("metadata", {}).get("hermes", {})
    return {
        "expert_id": str(metadata.get("expert_id", "")),
        "related_skills": str(sorted(metadata.get("related_skills", []))),
    }


class ApplyError(Exception):
    """Raised when the atomic apply transaction fails (auto-reverted)."""
```

### Pattern 4: CLI Subcommand Extension

**What:** Extend `hermes_cli/feedback.py:register_cli` with 5 new subcommands.
**When to use:** Adding the `evolve`, `review-queue`, `show-patch`, `approve`, `reject`, `rollback` subparsers.
**Example:**
```python
# Source: hermes_cli/feedback.py:40 (register_cli) — VERIFIED pattern
def register_cli(parent: argparse.ArgumentParser) -> None:
    """Attach ``feedback`` subcommands to *parent*."""
    parent.set_defaults(func=lambda a: (parent.print_help(), 0)[1])
    subs = parent.add_subparsers(dest="feedback_command")

    # ... existing import / watch / submit / rebuild-index subparsers ...

    # ── evolve (EVOL-01) ────────────────────────────────────────────
    p_evolve = subs.add_parser(
        "evolve",
        help="Run LLM aggregation on accumulated feedback for a skill",
    )
    p_evolve.add_argument("--skill", required=True, help="Target skill_id")
    p_evolve.add_argument(
        "--model", default=None, help="Override LLM model (default: configured)"
    )
    p_evolve.add_argument(
        "--dry-run", action="store_true",
        help="Skip the LLM call; emit a stub insight for pipeline testing",
    )
    p_evolve.set_defaults(func=_cmd_evolve)

    # ── review-queue (EVOL-03) ──────────────────────────────────────
    p_queue = subs.add_parser(
        "review-queue",
        help="List pending/approved/rejected patches in the review queue",
    )
    p_queue.add_argument("--skill", default=None, help="Filter by skill_id")
    p_queue.add_argument(
        "--status", choices=["pending", "applied", "rejected"],
        default="pending", help="Filter by status (default: pending)",
    )
    p_queue.set_defaults(func=_cmd_review_queue)

    # ── show-patch (EVOL-03) ────────────────────────────────────────
    p_show = subs.add_parser(
        "show-patch",
        help="Show the full diff + rationale + feedback chain for a patch",
    )
    p_show.add_argument("patch_id", help="Patch ID to inspect")
    p_show.set_defaults(func=_cmd_show_patch)

    # ── approve (EVOL-04 + EVOL-05) ─────────────────────────────────
    p_approve = subs.add_parser(
        "approve",
        help="Apply a pending patch atomically (git commit + FOUND-08 check)",
    )
    p_approve.add_argument("patch_id", help="Patch ID to approve + apply")
    p_approve.add_argument(
        "--yes", action="store_true",
        help="Skip interactive confirmation (scripted automation)",
    )
    p_approve.set_defaults(func=_cmd_approve)

    # ── reject (EVOL-03) ────────────────────────────────────────────
    p_reject = subs.add_parser(
        "reject", help="Reject a pending patch with a reason"
    )
    p_reject.add_argument("patch_id", help="Patch ID to reject")
    p_reject.add_argument("reason", help="Rejection reason")
    p_reject.set_defaults(func=_cmd_reject)

    # ── rollback (EVOL-05) ──────────────────────────────────────────
    p_rollback = subs.add_parser(
        "rollback",
        help="Revert an applied patch via git revert <commit_sha>",
    )
    p_rollback.add_argument("commit_sha", help="Commit SHA to revert")
    p_rollback.add_argument(
        "--yes", action="store_true", help="Skip confirmation"
    )
    p_rollback.set_defaults(func=_cmd_rollback)
```

### Anti-Patterns to Avoid

- **LLM emits raw unified diff:** LLMs fail at `@@ -A,B +C,D @@` hunk syntax. ALWAYS use `difflib.unified_diff` over the LLM's "add this content" proposal. `[ASSUMED — based on observation]`
- **Auto-apply path anywhere except `_cmd_approve`:** EVOL-04 non-bypassable human-in-loop is enforced structurally — no code path may call `apply_patch_transaction()` except the CLI handler. If P32 Curator needs to propose patches, it writes to `queue.jsonl`; the operator still runs `hermes feedback approve`. `[VERIFIED: CONTEXT.md D-EVOL-04]`
- **`shell=True` in any subprocess call:** Phase 30 T-30-02 mitigation. ALWAYS argv-list. `[VERIFIED: skills/movie-experts/_eval/gate.py:172]`
- **`open()` without `encoding="utf-8"`:** Ruff PLW1514 will block merge. `[VERIFIED: CLAUDE.md Code Style]`
- **Mutation of `_cached_system_prompt`:** Evolution code is operator-invoked and does not touch the runtime prompt cache. `[VERIFIED: CLAUDE.md Architectural Constraints]`
- **Importing evolution code from runtime path:** Evolution modules are NOT imported by `run_agent.py`, `agent/conversation_loop.py`, or any Hermes runtime module. Isolation verified by grep (see Isolation from Runtime section).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML frontmatter parsing | Custom regex for `expert_id:` / `related_skills:` | `agent.skill_utils.parse_frontmatter` (skill_utils.py:123) | Already handles YAML nesting (`metadata.hermes.expert_id`), has fallback parser, tested. Custom regex would miss the nested path. `[VERIFIED: agent/skill_utils.py:123]` |
| Unified diff generation | Custom string concatenation | `difflib.unified_diff` (stdlib) | Produces git-compatible output; handles line termination; already used in 4 codebase modules. `[VERIFIED: tools/patch_parser.py:496]` |
| Patch application / revert | Python `patch` lib or manual hunk parser | `subprocess.run(["git", "apply", ...])` | git handles edge cases (whitespace, context fuzzing); Phase 30 established this pattern; revert via `git checkout --` is symmetric. `[VERIFIED: skills/movie-experts/_eval/gate.py:172, 201]` |
| Atomic JSONL append | Custom file lock + write | Direct append (Phase 29 FeedbackStore pattern at `feedback_store.py:336`) | Append-only JSONL is O(1) per write; `atomic_json_write` would be O(N). Single-process assumption documented. `[VERIFIED: agent/feedback_store.py:336]` |
| Atomic JSON write (for index files) | Custom temp + rename | `utils.atomic_json_write` (utils.py:111) | Phase 29 uses this for `index.json`. Handles fsync, os.replace, mode preservation. `[VERIFIED: agent/feedback_store.py:686]` |
| Feedback query / summary | Direct bucket file scan | `FeedbackStore.query()` + `FeedbackStore.summary()` | Phase 29 already optimized this with index.json; handles superseded records, decay weighting. `[VERIFIED: agent/feedback_store.py:919, 990]` |
| Eval gate scoring | New eval harness | `skills/movie-experts/_eval/gate.run_gate()` | Phase 30 shipped this with GATE-01..04. Reusing is a hard requirement (EVOL-05 precondition). `[VERIFIED: skills/movie-experts/_eval/gate.py:913]` |

**Key insight:** Phase 31 is primarily an INTEGRATION phase. The hard primitives (feedback storage, eval gating, frontmatter parsing, difflib, git subprocess patterns) are all shipped. P31's novelty is the *pipeline wiring* + *atomic apply transaction* + *CLI surface* — not new algorithms.

## Runtime State Inventory

> Phase 31 is not a rename/refactor/migration, but it DOES create new runtime state under `~/.hermes/skills/.feedback/evolution/`. Documenting for completeness.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | NEW: `~/.hermes/skills/.feedback/evolution/queue.jsonl` (pending patches), `applied.jsonl`, `rejected.jsonl`, `insights.jsonl`, `failed_gate.jsonl` | Create directory + files lazily on first write (mirror FeedbackStore pattern at feedback_store.py:245) |
| Live service config | None — no daemon, no service registration | None |
| OS-registered state | None — no Task Scheduler / launchd / systemd | None |
| Secrets/env vars | `OPENROUTER_API_KEY` (already required by P30 gate.py:546) — read by `make_aggregation_client` | None (already in `.env.example` per P30) |
| Build artifacts | None — pure Python, no compiled artifacts | None |

**Migration risks:** None. The new `evolution/` subdirectory is additive. Existing `~/.hermes/skills/.feedback/` structure (buckets/, dedup/, archive/, incoming/, index.json) is untouched.

## Common Pitfalls

### Pitfall 1: LLM JSON Parsing Failures

**What goes wrong:** The aggregation LLM returns malformed JSON, JSON with trailing commas, JSON wrapped in markdown fences (` ```json ... ``` `), or partial JSON that cuts off mid-record.
**Why it happens:** LLMs are probabilistic; structured-output contracts are not guaranteed even with `response_format={"type": "json_object"}` on all providers (OpenRouter routes to heterogeneous backends).
**How to avoid:**
1. Use `response_format={"type": "json_object"}` when the provider supports it (catch the SDK error and retry without if unsupported).
2. Strip markdown fences (```` ```json ... ``` ````) before `json.loads`.
3. On parse failure, log the raw response at DEBUG (never INFO — may contain feedback snippets) and retry once with a "Please output valid JSON only" system message. If the retry also fails, raise `AggregationError` — do NOT silently emit an empty insights list.
4. Validate each insight with Pydantic (`InsightRecord.model_validate`). Reject the entire batch if ANY insight is malformed (atomicity — matches Phase 28 atomic JSONL import pattern).
**Warning signs:** Empty `insights.jsonl` after `evolve` runs; "JSON parse error" in logs; insights count always 0.

### Pitfall 2: difflib Edge Cases

**What goes wrong:** `difflib.unified_diff` produces an empty string if `current_lines == new_lines` (no-op patch); produces a confusing diff if line endings differ (`\n` vs `\r\n`); produces multi-hunk diffs if the insertion point appears multiple times.
**Why it happens:** `difflib` is a general-purpose sequence matcher, not a semantic-aware patch generator.
**How to avoid:**
1. Normalize line endings BEFORE diffing: `current_content.replace("\r\n", "\n")`.
2. If the insertion marker appears multiple times, require the LLM to provide a longer unique context (raise `ValueError("marker not unique")` — force the LLM to be specific).
3. Assert the resulting diff is non-empty and contains at least one `+` line (additions). An empty diff means the LLM proposed adding content that already exists.
**Warning signs:** Empty unified_diff string; "marker not unique" errors; patches that apply but add zero lines.

### Pitfall 3: git apply Partial Failures

**What goes wrong:** `git apply` succeeds for some hunks but fails for others (e.g., context lines don't match due to a concurrent edit), leaving the working tree in a partial state. `git apply --check` passed but `git apply` failed.
**Why it happens:** Between `--check` and apply, no time passes — but `--check` is a heuristic. If the patch was generated against a stale baseline (e.g., another patch was applied between queue insertion and approve), the context lines drift.
**How to avoid:**
1. ALWAYS run `git apply --check` immediately before `git apply` in the same transaction (not at queue-insert time only).
2. If `git apply` fails after `--check` passed, the working tree MAY be partially mutated. The `try/finally` revert (Pattern 3) handles this: `revert_files` runs `git checkout -- <files>` + `git clean -f <files>` which restores to HEAD regardless of partial mutation.
3. Before apply, check `git status --porcelain` — refuse to apply if the working tree is already dirty (operator must commit or stash first). This is CONTEXT.md D-EVOL-04's "operator's working tree must be clean before apply" invariant.
**Warning signs:** `git apply` non-zero exit; working tree dirty after a failed apply; `git status` shows partial changes.

### Pitfall 4: Frontmatter Drift via Non-Byte-Identical Re-serialization

**What goes wrong:** The LLM proposes a change that, when converted to a diff and applied, re-serializes the YAML frontmatter (e.g., reorders keys, changes quote style, changes list indentation). `parse_frontmatter` returns the same logical values, but the BYTES differ — violating FOUND-08's "byte-for-byte" contract.
**Why it happens:** `difflib` operates on lines; if the LLM's proposed addition includes a frontmatter re-serialization (even unintentionally), the diff will contain frontmatter changes.
**How to avoid:**
1. The diff_generator (Pattern 2) ONLY inserts content AFTER a marker in the body — it never touches frontmatter by construction.
2. The FOUND-08 check (Pattern 3, Step 3) extracts frontmatter fields BEFORE and AFTER apply and asserts equality. If they differ, the transaction fails and reverts.
3. For belt-and-suspenders: also assert that the frontmatter BLOCK (lines between the opening `---` and closing `---`) is byte-identical before/after, not just the parsed values. This catches re-serialization that preserves values but changes bytes.
**Warning signs:** FOUND-08 check fails on a patch that "should" pass; frontmatter bytes differ but values are equal.

### Pitfall 5: Concurrent Queue Writes

**What goes wrong:** Two `hermes feedback evolve` processes run concurrently and both append to `queue.jsonl`, interleaving their writes.
**Why it happens:** JSONL append is NOT atomic across processes on all OSes; two `open(..., "a")` + `write()` + `close()` sequences can interleave at the byte level.
**How to avoid:**
1. Document single-process assumption in module docstring (CONTEXT.md Claude's Discretion).
2. Use `fcntl.flock` (POSIX) / `msvcrt.locking` (Windows) on the queue file for belt-and-suspenders. Phase 29 FeedbackStore deferred this ("worst case is a duplicate that Plan 02's dedup catches"); P31 should follow the same discipline but document the risk.
3. Each `PatchRecord` has a unique `patch_id` (content-addressed), so even if two writes interleave, the records are distinguishable on read. A corrupt line (partial JSON from interleaving) is caught by `json.loads` and logged + skipped (mirror Phase 29 `_read_bucket_records` at feedback_store.py:654).
**Warning signs:** Malformed JSON lines in queue.jsonl; patch_ids appearing twice; queue length != expected count.

### Pitfall 6: Additive-Only Verification False Positives

**What goes wrong:** A legitimate additive patch is rejected because the verification regex is too strict (e.g., it flags context lines starting with `-` in the diff metadata, or it flags the `---` header line).
**Why it happens:** Unified diff format uses `-` for both "removed line" and "old file header" (`--- a/...`). A naive regex `^-` matches both.
**How to avoid:** The verification algorithm (see Code Examples) MUST:
1. Skip the first two header lines (`--- ...` and `+++ ...`).
2. For each hunk, skip the `@@ -A,B +C,D @@` header line.
3. For each remaining line: if it starts with `-` (and is not `---`), it's a removal — REJECT.
4. If it starts with `+` (and is not `+++`), it's an addition — ALLOW.
5. If it starts with ` ` (space), it's a context line — ALLOW.
6. Assert hunk header `+C,D` has `D >= B` (additions only, no shrinkage).
**Warning signs:** Legitimate patches rejected; verification passes patches that delete content.

### Pitfall 7: Git Commit Author Identity

**What goes wrong:** `git commit` fails in environments where `user.email` / `user.name` are not configured globally (common in Docker containers, CI, fresh clones).
**Why it happens:** git refuses to commit without an author identity.
**How to avoid:**
1. Before the commit step, check `git config user.email`. If empty, set a local (repo-scoped) identity: `git config user.email "hermes-evolution@local"` + `git config user.name "Hermes Evolution Pipeline"`. This matches the test fixture pattern at `test_gate.py:111-118`.
2. Document that operators can override via global git config.
3. NEVER set `--global` config from a pipeline — only repo-local.
**Warning signs:** `git commit` exits non-zero with "Author identity unknown"; commits attributed to wrong author.

## Code Examples

### Additive-Only Verification Algorithm (SC-6)

```python
# Source: stdlib difflib format + codebase gate.py:117 extract_patched_files
# Algorithm verified against git diff format spec.
from __future__ import annotations

import re

_HUNK_HEADER_RE = re.compile(r"^@@ -(\d+),(\d+) \+(\d+),(\d+) @@")


def verify_additive_only(diff_text: str) -> bool:
    """Return True iff the diff is purely additive (no removals).

    Verification rules (Pitfall 6):
      1. Skip file headers (--- / +++).
      2. For each hunk header @@ -A,B +C,D @@: assert D >= B.
      3. For each content line:
         - ` ` (space) = context → ALLOW
         - `+`         = addition → ALLOW
         - `-`         = removal  → REJECT (return False)
      4. An empty diff returns False (no-op patches are suspicious).

    Edge cases:
      - File header `--- a/...` is NOT a removal (starts with `---`).
      - File header `+++ b/...` is NOT an addition we care about.
      - Hunk header line is skipped.
    """
    if not diff_text.strip():
        return False  # empty diff = no-op = suspicious

    lines = diff_text.splitlines()
    i = 0
    saw_addition = False
    while i < len(lines):
        line = lines[i]
        # Skip file headers.
        if line.startswith("--- ") or line.startswith("+++ "):
            i += 1
            continue
        # Hunk header: validate D >= B.
        m = _HUNK_HEADER_RE.match(line)
        if m:
            _, b, _, d = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
            if d < b:
                return False  # hunk shrinks the file
            i += 1
            continue
        # Content line.
        if line.startswith("-"):
            # Not a file header (those were skipped above) → it's a removal.
            return False
        if line.startswith("+"):
            saw_addition = True
        # Context lines (start with " ") are fine.
        i += 1

    return saw_addition
```

### FOUND-08 Per-Patch Check (SC-5)

```python
# Source: agent/skill_utils.py:123 parse_frontmatter — VERIFIED
from __future__ import annotations

from pathlib import Path


def verify_found08_byte_intact(
    skill_md_path_before: str, skill_md_path_after: Path
) -> bool:
    """Return True iff expert_id + related_skills are byte-identical.

    SC-5 check. Extract the frontmatter block (everything between the
    opening --- and closing ---) and compare bytes. This is STRICTER
    than comparing parsed values — it catches re-serialization that
    preserves values but changes bytes (Pitfall 4).

    Args:
        skill_md_path_before: Frontmatter block text BEFORE patch apply.
        skill_md_path_after: Path to the SKILL.md AFTER patch apply.

    Returns:
        True iff the frontmatter bytes match exactly.
    """
    after_content = skill_md_path_after.read_text(encoding="utf-8")
    # Extract frontmatter block: text between first --- and next ---.
    after_fm = _extract_frontmatter_block(after_content)
    return skill_md_path_before == after_fm


def _extract_frontmatter_block(content: str) -> str:
    """Return the raw frontmatter block (including --- delimiters).

    Returns empty string if no frontmatter present.
    """
    if not content.startswith("---"):
        return ""
    # Find the closing ---.
    end_match = re.search(r"\n---\s*\n", content[3:])
    if not end_match:
        return ""
    # Include the opening --- through the closing --- line.
    end_idx = end_match.start() + 3 + end_match.end()
    return content[:end_idx]


import re  # module-level per CLAUDE.md
```

### Commit Message Format (EVOL-05)

```python
# Source: CONTEXT.md specifics line 113 — VERIFIED locked decision
def build_commit_message(
    *,
    insight_summary: str,
    feedback_ids: list[str],
    eval_verdict: str,
    eval_mean_delta: float,
) -> str:
    """Build the machine-parseable commit message per CONTEXT.md.

    Format: feat(evolution): <subject> | feedback: <ids> | eval: <verdict>:<mean_delta>

    The format MUST be machine-parseable so P32's audit log + P33's
    observability dashboard can extract feedback IDs + eval score from
    git history.
    """
    # Truncate insight summary to 72 chars (git commit subject convention).
    subject = insight_summary[:72]
    feedback_str = ",".join(feedback_ids) if feedback_ids else "none"
    eval_str = f"{eval_verdict}:{eval_mean_delta:.2f}"
    return (
        f"feat(evolution): {subject} | "
        f"feedback: {feedback_str} | "
        f"eval: {eval_str}"
    )
```

### LLM Aggregation Prompt Template (EVOL-01)

```python
# Source: CONTEXT.md specifics lines 105-110 + Claude's Discretion — DESIGN
AGGREGATION_SYSTEM_PROMPT = """\
You are reviewing operator feedback for a movie-expert skill in the Hermes
short-film production suite. Your job is to identify COMMON THEMES across
multiple feedback records and propose ADDITIVE improvements.

CRITICAL RULES:
1. Group feedback by theme (e.g., "missing X method", "unclear Y section").
2. Cite specific feedback IDs in each insight (evidence chain).
3. Propose ADDITIVE-ONLY changes — never delete or restructure existing
   content. New sections, new examples, new methods only.
4. Preserve expert_id and related_skills frontmatter byte-for-byte.
5. Output STRICT JSON with this schema:
   {
     "insights": [
       {
         "theme": "short description of the improvement theme",
         "evidence_chain": ["fb_id_1", "fb_id_2"],
         "rationale": "why this improvement matters, citing feedback",
         "proposed_addition": "the exact markdown content to append",
         "insert_after_marker": "a unique substring identifying where to insert"
       }
     ]
   }
6. Emit 1-5 insights. If feedback is sparse or contradictory, emit fewer.
7. NEVER propose changes to v4/v5 protected refs (snowflake-method.md,
   e-konte-format.md, scamper-variations.md, dreamina-cli-baseline.md,
   v86-pipeline-mapping.md) — only propose additions to SKILL.md or
   non-protected refs.
"""


def build_aggregation_user_prompt(
    *, skill_id: str, feedback_summary: dict, feedback_details: list[dict]
) -> str:
    """Build the user message with feedback context for the LLM."""
    import json
    return (
        f"Skill under review: {skill_id}\n\n"
        f"Feedback summary (counts by verdict):\n"
        f"{json.dumps(feedback_summary, indent=2, ensure_ascii=False)}\n\n"
        f"Feedback details (most recent first, max 50):\n"
        f"{json.dumps(feedback_details, indent=2, ensure_ascii=False)}\n\n"
        f"Identify improvement themes and propose additive changes."
    )
```

## Isolation from Runtime (Verified)

**Claim:** Evolution code (`agent/evolution/*.py`) is NOT imported by the Hermes runtime.

**Verification command:**
```bash
# After P31 ships, run this to verify zero runtime imports:
grep -rn "from agent.evolution\|import agent.evolution" \
  /data/workspace/hermes-agent/run_agent.py \
  /data/workspace/hermes-agent/agent/conversation_loop.py \
  /data/workspace/hermes-agent/agent/prompt_builder.py \
  /data/workspace/hermes-agent/agent/system_prompt.py \
  /data/workspace/hermes-agent/agent/tool_executor.py \
  /data/workspace/hermes-agent/agent/curator.py \
  /data/workspace/hermes-agent/cli.py \
  /data/workspace/hermes-agent/gateway/ \
  2>/dev/null
# Expected: zero matches.
```

**Design enforcement:**
1. Evolution modules are imported ONLY by `hermes_cli/feedback.py` (the CLI subcommand handlers) and by tests under `tests/agent/evolution/`.
2. `agent/curator.py` does NOT import evolution code in P31 — P32 will wire the Curator to *invoke* the evolution pipeline via subprocess or lazy import, but even then the runtime agent loop never touches it.
3. Evolution modules MUST NOT call `registry.register(...)` (per the `_eval/` offline-tooling invariant at gate.py:1).
4. The plan-checker should add a verification task that runs the grep above + asserts zero matches.

`[VERIFIED: Current codebase has no agent/evolution/ module; the isolation will hold by construction if the planner scopes imports correctly.]`

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| LLM emits raw unified diff | LLM emits structured "add this content"; `difflib` generates diff | P31 design decision | Reliable, deterministic, testable diffs; LLM unreliability confined to content proposal, not format |
| Branch + PR for patch apply | Direct commit to current branch | CONTEXT.md D-EVOL-04 | Matches single-operator v6 workflow; PR overhead unjustified for ~10-100 patches/quarter |
| SQLite queue | JSONL append-only queue | CONTEXT.md D-EVOL-03 | Matches Phase 28/29 pattern; O(1) writes; no schema migrations |
| Separate evolution daemon | Operator-invoked synchronous CLI | CONTEXT.md D-EVOL-01 | P31 scope discipline; P32 adds the daemon (Curator) |

**Deprecated/outdated:**
- Custom YAML frontmatter parsers: replaced by `agent.skill_utils.parse_frontmatter` (shipped in earlier milestones).
- `os.kill(pid, 0)`: replaced by `psutil` per CLAUDE.md (not relevant to P31, but noted for completeness).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | LLMs are unreliable at `@@ -A,B +C,D @@` hunk syntax, so `difflib` should generate diffs | Architecture Patterns / Anti-Patterns; Pattern 2 | LOW — if wrong, the `difflib` approach still works (it's a superset of what an LLM could do). If right (expected), we avoid a whole class of bugs. |
| A2 | `response_format={"type": "json_object"}` is supported by OpenRouter for the configured judge model | Pitfall 1 | MEDIUM — if unsupported, the SDK raises an error; we catch + retry without it. No correctness impact, just a minor latency hit on retry. |
| A3 | Single-process assumption for queue writes is acceptable for v6 | Pitfall 5 | LOW — CONTEXT.md Claude's Discretion explicitly allows this. Worst case is a duplicate patch_id (caught on read by json.loads failure → skip). |

**All other claims in this research are `[VERIFIED]` via codebase grep or `[CITED]` via CONTEXT.md / CLAUDE.md.**

## Open Questions

1. **Should the aggregation LLM call be retryable on transient failure?**
   - What we know: `agent/retry_utils.py:jittered_backoff` exists for the conversation loop. `tenacity==9.1.4` is pinned.
   - What's unclear: whether to add retry to the aggregation call or surface the error immediately (operator can re-run `evolve`).
   - Recommendation: Surface immediately for P31 (operator can re-run). P32 Curator's automated path can add retry. This keeps P31 scope tight.

2. **How should the queue handle a patch whose eval gate verdict was "pass" at insertion time but the baseline has since been rebuilt?**
   - What we know: Phase 30 gate.py `load_cached_baseline` (gate.py:741) warns on staleness but returns cached composites anyway.
   - What's unclear: whether to re-run the gate at approve time (could be slow) or trust the insertion-time verdict.
   - Recommendation: Trust the insertion-time verdict for P31. Document in `approve` help text that operators can `hermes feedback reject <id> stale_baseline` if they suspect drift. P33 observability can surface stale patches.

3. **Should the `evolve` command accept `--insights-only` (skip patch generation + gate)?**
   - What we know: EVOL-01 is purely about insight extraction; EVOL-03 is about the queue.
   - What's unclear: whether operators want to inspect insights before committing to the full pipeline.
   - Recommendation: Yes — add `--insights-only` flag. It writes to `insights.jsonl` and exits without generating patches or running the gate. Useful for debugging the aggregation prompt. (Claude's Discretion per CONTEXT.md.)

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | All code | ✓ | 3.12.3 (env) + 3.13 (ty) | — |
| git | EVOL-05 apply/commit/revert | ✓ | 2.43.0 | — |
| `openai` SDK | EVOL-01 LLM call | ✓ | 2.24.0 (pyproject) | — |
| OPENROUTER_API_KEY env | EVOL-01 LLM call | Config-dependent | — | `--dry-run` flag (stub client pattern from runner.py:561 _StubJudgeClient) |
| OpenRouter API reachability | EVOL-01 live LLM call | Network-dependent | — | `--dry-run` for offline testing |
| `difflib` / `subprocess` / `hashlib` / `argparse` / `tempfile` | All modules | ✓ | stdlib | — |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** OPENROUTER_API_KEY (use `--dry-run` with a stub aggregation client that returns canned insights — mirrors `_StubJudgeClient` at runner.py:561).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 + pytest-timeout 2.4.0 (`[dev]` extra, pyproject.toml:261) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (30s per-test timeout) |
| Quick run command | `python -m pytest tests/agent/evolution/ -x --timeout=30` |
| Full suite command | `python -m pytest tests/agent/evolution/ tests/hermes_cli/test_evolution_cli.py --timeout=30` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EVOL-01 | LLM aggregation produces structured insights with evidence chains | unit (mock LLM) | `pytest tests/agent/evolution/test_insights.py -x` | ❌ Wave 0 |
| EVOL-01 | Malformed LLM JSON raises AggregationError (no silent empty list) | unit (mock LLM) | `pytest tests/agent/evolution/test_insights.py::TestMalformedJson -x` | ❌ Wave 0 |
| EVOL-03 | Queue append/move/read lifecycle (pending → applied/rejected) | unit | `pytest tests/agent/evolution/test_queue.py -x` | ❌ Wave 0 |
| EVOL-03 | review-queue / show-patch CLI commands work | smoke (CLI) | `pytest tests/hermes_cli/test_evolution_cli.py::TestReviewQueue -x` | ❌ Wave 0 |
| EVOL-04 | No code path calls apply_patch_transaction except _cmd_approve | unit (grep invariant) | `pytest tests/agent/evolution/test_apply.py::TestIsolation -x` | ❌ Wave 0 |
| EVOL-05 | Atomic apply: git apply + FOUND-08 + additive + commit | integration (tmp git repo) | `pytest tests/agent/evolution/test_apply.py::TestAtomicApply -x` | ❌ Wave 0 |
| EVOL-05 | Atomic apply reverts on FOUND-08 violation | integration (tmp git repo) | `pytest tests/agent/evolution/test_apply.py::TestRevertOnFound08 -x` | ❌ Wave 0 |
| EVOL-05 | Atomic apply reverts on additive-only violation | integration (tmp git repo) | `pytest tests/agent/evolution/test_apply.py::TestRevertOnAdditive -x` | ❌ Wave 0 |
| EVOL-05 | git revert rollback subcommand | smoke (CLI + tmp git repo) | `pytest tests/hermes_cli/test_evolution_cli.py::TestRollback -x` | ❌ Wave 0 |
| SC-5 | FOUND-08 byte-intact per patch | unit (pure function) | `pytest tests/agent/evolution/test_apply.py::TestFound08 -x` | ❌ Wave 0 |
| SC-6 | Additive-only verification rejects removals | unit (pure function) | `pytest tests/agent/evolution/test_apply.py::TestAdditiveOnly -x` | ❌ Wave 0 |
| SC-6 | Additive-only verification accepts pure additions | unit (pure function) | `pytest tests/agent/evolution/test_apply.py::TestAdditiveOnly::test_accepts_pure_addition -x` | ❌ Wave 0 |
| Isolation | Evolution code not imported by runtime | grep invariant | `pytest tests/agent/evolution/test_isolation.py -x` (or shell check) | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/agent/evolution/ -x --timeout=30`
- **Per wave merge:** `python -m pytest tests/agent/evolution/ tests/hermes_cli/test_evolution_cli.py skills/movie-experts/_eval/tests/ --timeout=30`
- **Phase gate:** Full suite green + manual smoke (`hermes feedback evolve --skill screenplay --dry-run` produces an insight; `hermes feedback review-queue` lists it) before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tests/agent/evolution/__init__.py` — new test package marker
- [ ] `tests/agent/evolution/conftest.py` — shared fixtures: `feedback_env` (copy from test_feedback_store.py:36), `tmp_git_repo` (copy from test_gate.py:94), `mock_llm_client` (stub returning canned JSON)
- [ ] `tests/agent/evolution/test_insights.py` — EVOL-01 coverage (aggregation, malformed JSON, empty feedback)
- [ ] `tests/agent/evolution/test_diff_generator.py` — difflib additive generation + edge cases
- [ ] `tests/agent/evolution/test_queue.py` — JSONL queue lifecycle
- [ ] `tests/agent/evolution/test_apply.py` — atomic apply, FOUND-08, additive-only, revert-on-failure
- [ ] `tests/hermes_cli/test_evolution_cli.py` — 5 new CLI subcommands smoke tests
- Framework install: none needed (pytest already pinned)

## Security Domain

> `security_enforcement` not explicitly set in `.planning/config.json` → treat as enabled. Include this section.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — operator-invoked CLI, no auth surface |
| V3 Session Management | no | N/A — no sessions |
| V4 Access Control | yes | Operator-only invocation; EVOL-04 non-bypassable human-in-loop is the access control. No programmatic auto-apply path. |
| V5 Input Validation | yes | Pydantic schema validation on all LLM JSON output (`InsightRecord.model_validate`); `gate.extract_patched_files` path-traversal guard reused (T-30-01); unified_diff validated as additive-only before apply |
| V6 Cryptography | no | N/A — no crypto operations (sha256 is for content-addressing, not security) |
| V7 Error Handling | yes | All git subprocess failures caught + reverted; ApplyError surfaces safe messages (no secrets, no full diffs in error text) |
| V8 Data Protection | yes | OPENROUTER_API_KEY never logged (T-00-09 pattern from runner.py:528); feedback details logged at DEBUG only (may contain operator corrections); commit messages contain feedback IDs (not feedback text) |
| V9 Communications | yes | LLM call over HTTPS (OpenAI SDK default); no custom TLS needed |
| V10 Business Logic | yes | Atomic apply transaction prevents partial state; FOUND-08 + additive-only are business-logic invariants enforced per-patch |

### Known Threat Patterns for LLM Aggregation + Git Apply Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| LLM injects malicious content into proposed addition (prompt injection from feedback text) | Tampering / Elevation of Privilege | Pydantic schema validation + additive-only check + operator review (EVOL-04) + eval gate (EVOL-05). The proposed addition is never executed as code — it's markdown appended to SKILL.md. Worst case: a malformed SKILL.md section that the next skill invocation surfaces, which the operator would notice. |
| Path traversal via crafted `+++ b/../../../etc/passwd` in unified diff | Tampering | Reuse `gate.extract_patched_files` (gate.py:117) which rejects `..` paths and non-`skills/movie-experts/` paths (T-30-01). |
| Deletion patch disguised as addition (`+++ /dev/null`) | Tampering / Information Disclosure | Reuse `gate.extract_patched_files` WR-07 fix (gate.py:142) which explicitly rejects deletion patches. |
| git apply succeeds but leaves working tree dirty on partial failure | DoS | try/finally revert pattern (gate.py:1084) — `revert_files` always runs, escalates to `internal_error` verdict if revert also fails. |
| Queue.jsonl corruption from concurrent writes | Tampering / Repudiation | Single-process assumption (documented); patch_id is content-addressed so duplicates are detectable; malformed lines skipped + logged (feedback_store.py:670 pattern). |
| Commit author identity spoofing | Repudiation | Use repo-local `git config user.email` if global is unset (Pitfall 7); commit message includes feedback IDs for audit trail. |

## Sources

### Primary (HIGH confidence)
- **Codebase (verified via Read tool):**
  - `agent/feedback_store.py` — FeedbackStore P29 (query, summary, record_feedback, dedup)
  - `agent/feedback_schema.py` — FeedbackRecord P28 schema
  - `skills/movie-experts/_eval/gate.py` — run_gate P30, apply_patch, revert_patch, extract_patched_files
  - `skills/movie-experts/_eval/runner.py:524` — make_judge_client LLM client pattern
  - `hermes_cli/feedback.py:40` — register_cli CLI subcommand pattern
  - `agent/skill_utils.py:123` — parse_frontmatter for FOUND-08 check
  - `agent/curator.py:87` — load_state / save_state persistence pattern
  - `utils.py:111` — atomic_json_write utility
  - `tools/patch_parser.py:496` — difflib.unified_diff codebase precedent
  - `skills/movie-experts/_eval/tests/test_gate.py:94` — tmp_git_repo test fixture pattern
- **CONTEXT.md** — all locked decisions cited verbatim in User Constraints
- **CLAUDE.md** — project conventions (encoding=, %-logging, argv-list, etc.)
- **Python stdlib docs** — `difflib.unified_diff`, `subprocess.run`, `hashlib`, `tempfile.mkstemp` (stable APIs since Python 3.6+)

### Secondary (MEDIUM confidence)
- **STATE.md** — v6.0 milestone progress, decisions table, carried-forward context
- **ROADMAP.md** — Phase 31 success criteria, critical path, parallel-eligibility notes
- **REQUIREMENTS.md** — EVOL-01/03/04/05 definitions + traceability

### Tertiary (LOW confidence)
- None — all claims are codebase-verified or stdlib-documented.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages already pinned in pyproject.toml, verified via grep.
- Architecture: HIGH — reuses 3 shipped components (FeedbackStore, gate.py, feedback.py CLI); new code is pipeline wiring + atomic transaction.
- Pitfalls: HIGH — derived from observed patterns in Phase 28/29/30 codebase + git/diff format specs.
- LLM reliability claims: MEDIUM — based on observation, not formal verification (tagged `[ASSUMED]`).

**Research date:** 2026-06-24
**Valid until:** 2026-07-24 (30 days — stable domain: stdlib + shipped codebase; no fast-moving dependencies)
