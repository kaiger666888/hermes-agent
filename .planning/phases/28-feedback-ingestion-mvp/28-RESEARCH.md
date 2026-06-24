# Phase 28: Feedback Ingestion MVP - Research

**Researched:** 2026-06-24
**Domain:** Python CLI extension + Pydantic schema validation + filesystem-based ingestion (multi-source feedback normalization)
**Confidence:** HIGH

## Summary

Phase 28 ships the core functional guarantee of v6.0: a normalized feedback-ingestion pipeline that accepts structured feedback from three sources (CLI `/feedback` slash command, kais-aigc-platform file-exchange inbox, manual JSONL batch import) and emits a single validated `FeedbackRecord` JSON schema. The phase is a **Hermes-core touch** — it adds new CLI subcommands (`hermes feedback import`), a new slash command (`/feedback`), a Pydantic schema module, and a portable filesystem watcher. It does NOT touch any bundled SKILL.md or `references/*.md` bytes (FOUND-08 preservation), does NOT add new expert_ids, and does NOT modify the existing Curator (P32 does that).

The codebase already provides every primitive this phase needs. The `hermes_cli/curator.py` subcommand-registration pattern (`register_cli(parent)` + `set_defaults(func=_cmd_xxx)`) is the exact template for `hermes feedback`. The `cli.py` `process_command()` if/elif chain + `hermes_cli/commands.py` `COMMAND_REGISTRY` is where `/feedback` slots in. The `agent/curator.py` `load_state`/`save_state` + `utils.atomic_json_write` pattern is the exact persistence template. The `skills/movie-experts/_eval/snapshot.py` `EXPERT_DIRS` frozen list + sha256 + ISO 8601 pattern is the exact `output_snapshot` template. Pydantic 2.13.4 is already pinned in the stack.

**Primary recommendation:** Build four new modules — `hermes_cli/feedback.py` (CLI subcommands + slash-command handler), `agent/feedback_schema.py` (Pydantic `FeedbackRecord` + validators), `agent/feedback_ingest.py` (watcher + batch import + write path), and `agent/feedback_snapshot.py` (output_snapshot capture from conversation state). Wire the CLI via the `register_cli` pattern and the slash command via the `process_command` elif chain + `COMMAND_REGISTRY` entry. Use **stdlib polling** (1s interval, `os.scandir`) for the kais-aigc file watcher — no new deps, portable across Linux/macOS/Windows/Termux.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **INGEST-02 transport:** **File exchange** — kais-aigc-platform writes JSON files to `~/.hermes/skills/.feedback/inbox-kais/`; Hermes watches this directory and ingests new files. HTTP endpoint and webhook transports are explicitly DEFERRED (FUTURE-V6 scope).
- **INGEST-01 CLI UX:** **Slash command `/feedback`** — operator types `/feedback <verdict> [correction]` against the most recent movie-expert output. Verdict ∈ {`good`, `needs_work`, `bad`}; correction is free-text; optional revised output via `/feedback <verdict> --revised "<text>"`. `output_snapshot` auto-captured from current conversation state. Natural-language trigger and inline post-output prompts are REJECTED.
- **INGEST-03 batch import format:** **JSONL** — one feedback record per line, identical schema to live feedback. CLI: `hermes feedback import <file.jsonl>`. Auto-detect `skill_id` from snapshot path when possible; validate all records before any are written (atomic batch). CSV and YAML rejected.
- **INGEST-04 validation:** **Pydantic `FeedbackRecord` model** with field validators. Already in stack (`==2.13.4` per `pyproject.toml`). Rejects malformed payloads with field-level error messages. Validators enforce: `verdict` enum, `skill_id` against known expert list (`_eval/snapshot.py` `EXPERT_DIRS`), `ts` is ISO 8601, `output_snapshot.sha256` is 64-char hex.

### Claude's Discretion
- File-watcher implementation detail (inotify vs polling) — prefer stdlib `watchdog`-free polling for portability (Hermes ships on Linux/macOS/Windows/Termux).
- `/feedback` slash-command registration mechanism — follow existing `agent/skill_commands.py` pattern (file path is suggestive, exact integration at plan-phase discretion).
- JSONL batch import failure handling — all-or-nothing vs partial-success; recommend all-or-nothing with clear error listing for MVP simplicity.

### Deferred Ideas (OUT OF SCOPE)
- HTTP endpoint and webhook transports for kais-aigc-platform (INGEST-02 alternatives) — deferred to FUTURE-V6 scope.
- Auto-redaction of PII in feedback corrections (FUTURE-V6-06).
- Feedback deduplication logic (P29 STORE scope). P28 only ensures `output_snapshot.sha256` is captured so dedup is possible later.
- Cross-source feedback provenance tracking beyond the `source` enum (operator identity, session ID). `source` enum {`cli`, `kais_aigc`, `manual`} is sufficient for v6.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INGEST-01 | Hermes CLI 用户可在 conversation 内对 movie-expert 的输出提交反馈 —— verdict + 自由文本 correction + 可选修订后的输出 | `/feedback` slash command integrates via `cli.py:process_command()` elif chain (line 7265+) + `hermes_cli/commands.py` `COMMAND_REGISTRY` (line 64). Handler reads `self.conversation_history` (cli.py:3496) for most recent assistant message + `self.agent` for model/params. |
| INGEST-02 | kais-aigc-platform 审核反馈自动 ingest (file exchange), 含 verdict + retry 信号 + 修改 diff | File watcher polls `~/.hermes/skills/.feedback/inbox-kais/` via stdlib `os.scandir` at 1s interval. No existing watcher in codebase (verified — grep for `watchdog`/`inotify` returned nothing). New files validated by `FeedbackRecord` Pydantic model, then moved to `processed/`. |
| INGEST-03 | 反馈数据结构标准化为单一 JSON schema, 所有源走同一 schema | `agent/feedback_schema.py` defines `FeedbackRecord` Pydantic v2 BaseModel with `field_validator` decorators. All three ingest paths (CLI / kais file watcher / manual JSONL import) construct the same model before persistence. |
| INGEST-04 | 反馈含 `output_snapshot` (原始 LLM 输出 sha256 + 元数据: prompt / model / params) | `agent/feedback_snapshot.py` captures snapshot. sha256 pattern lifted from `skills/movie-experts/_eval/snapshot.py:96` (`hashlib.sha256(raw).hexdigest()`). Model/provider/params read from `agent` attributes (`agent.model`, `agent.provider`, `agent.api_mode`, `agent.max_tokens`, `agent.reasoning_config`, `agent.service_tier`, `agent.request_overrides` — all set in `agent/agent_init.py:486-489`). |
| INGEST-05 | 手工标注工具 (CLI 子命令) 支持批量导入历史输出 + 标注 | `hermes feedback import <file.jsonl>` subcommand via `hermes_cli/feedback.py` `register_cli(parent)` pattern (mirrors `hermes_cli/curator.py:495`). JSONL parsed line-by-line with `json.loads`; all records validated before any written (all-or-nothing). |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| `/feedback` slash command UX | CLI REPL (cli.py) | — | Slash commands are dispatched in `cli.py:process_command()` — this is the only tier with read access to live `conversation_history` + `agent` state needed for `output_snapshot` capture. |
| `FeedbackRecord` schema + validation | Core Python (agent/) | — | Pydantic model is a pure data contract shared by all three ingest paths. Lives under `agent/` alongside `error_classifier.py:ClassifiedError` — same "structured record" pattern. |
| kais-aigc file watcher | Background / CLI-invoked | — | Polling loop is a long-running task. Invoked via `hermes feedback watch` subcommand OR optionally wired into the gateway run loop later. NOT inside the conversation loop (would block REPL). |
| JSONL batch import | CLI subcommand (hermes_cli/) | — | `hermes feedback import` is a one-shot CLI invocation — same tier as `hermes sessions import`, `hermes curator run`. Reads file, validates, writes, exits. |
| `output_snapshot` capture | Core Python (agent/) | CLI (cli.py) | The snapshot *builder* lives in `agent/feedback_snapshot.py` (pure function, testable). The CLI handler *calls* it with the live agent + conversation state. |
| Persistence (write to disk) | Core Python (agent/) | — | `agent/feedback_ingest.py` owns the write path. Uses `utils.atomic_json_write` (already exists, `utils.py:111`). P28 writes raw validated records; P29 builds the index/dedup/decay layer on top. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | ==2.13.4 | `FeedbackRecord` schema + field validators | Already pinned in `pyproject.toml:60` (bumped for pydantic-core 2.46.4 to fix Responses-API thread crash). The ONLY validation library used in the stack. `[VERIFIED: pyproject.toml:60 + python3 -c "import pydantic; print(pydantic.VERSION)" → 2.13.4]` |

### Supporting (stdlib only — no new deps)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `hashlib` | stdlib | sha256 of LLM output for `output_snapshot` | Pattern lifted from `skills/movie-experts/_eval/snapshot.py:96` (`hashlib.sha256(raw).hexdigest()`). `[CITED: skills/movie-experts/_eval/snapshot.py:96]` |
| `json` | stdlib | JSONL parsing + JSON serialization | `json.loads` line-by-line for batch import; `json.dump` for atomic write via `utils.atomic_json_write`. `[CITED: agent/curator.py:92,102-105]` |
| `pathlib.Path` | stdlib | Directory + file path manipulation | All paths via `get_hermes_home() / "skills" / ".feedback" / ...` — NEVER `Path.home() / ".hermes"` (CLAUDE.md anti-pattern). `[CITED: hermes_constants.py:53 get_hermes_home()]` |
| `os.scandir` | stdlib | Filesystem polling for kais-aigc watcher | Portable across Linux/macOS/Windows/Termux (inotify is Linux-only). 1s poll interval is the lowest-common-denominator approach. `[ASSUMED — no existing watcher in codebase to cite; stdlib portability is well-known]` |
| `argparse` | stdlib | CLI subparser registration | Via `hermes_cli/curator.py:register_cli(parent)` pattern (`curator.py:495-603`). `[CITED: hermes_cli/curator.py:495-603]` |
| `datetime.datetime` | stdlib | ISO 8601 timestamps for `ts` field | `datetime.now(timezone.utc).isoformat()` — exact pattern from `snapshot.py:97`. `[CITED: skills/movie-experts/_eval/snapshot.py:97]` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib `os.scandir` polling | `watchdog` package | `watchdog` adds a new dependency for zero MVP benefit — polling at 1s is fast enough for file-exchange (kais-aigc writes are batch, not realtime). `watchdog`'s cross-platform Observer abstraction is nice but not worth the dep. DEFERRED. |
| Pydantic `FeedbackRecord` | stdlib `@dataclass` + manual validation | `ClassifiedError` (`error_classifier.py:69`) uses `@dataclass` — but it has no validation logic. `FeedbackRecord` MUST reject malformed payloads with field-level errors (INGEST-04). Pydantic v2 `field_validator` gives this for free; hand-rolling would be 50+ lines of regex/enum checks per field. |
| JSONL batch import | CSV / YAML | REJECTED per CONTEXT.md — CSV loses nested `output_snapshot`; YAML too slow for batches. JSONL is one `json.loads` per line. |

**Installation:**
```bash
# NO NEW PACKAGES — pydantic already pinned at ==2.13.4 in pyproject.toml:60
# All other dependencies are Python stdlib (hashlib, json, pathlib, os, argparse, datetime)
```

**Version verification:**
```bash
# Verified during research:
python3 -c "import pydantic; print(pydantic.VERSION)"
# → 2.13.4  [VERIFIED via direct import on target machine]
```

## Package Legitimacy Audit

> This phase installs **zero new packages**. The only dependency (`pydantic`) is already pinned in `pyproject.toml:60` and verified present at version 2.13.4 on the target machine. No slopcheck run needed for new packages.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| pydantic (already in stack) | PyPI | 6+ yrs | 150M+/mo | github.com/pydantic/pydantic | N/A (pre-existing) | Pre-approved — already in `pyproject.toml:60` |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none
**New packages introduced by this phase:** none — all work uses stdlib + pre-existing pydantic pin.

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        THREE FEEDBACK SOURCES                        │
└─────────────────────────────────────────────────────────────────────┘

  ┌──────────────────┐   ┌──────────────────────┐   ┌────────────────┐
  │  CLI operator    │   │  kais-aigc-platform  │   │  Manual labeler│
  │  types /feedback │   │  writes JSON files   │   │  has JSONL file│
  │  in REPL         │   │  to inbox-kais/ dir  │   │  (cold-start)  │
  └────────┬─────────┘   └──────────┬───────────┘   └───────┬────────┘
           │                        │                       │
           ▼                        ▼                       ▼
  ┌──────────────────┐   ┌──────────────────────┐   ┌────────────────┐
  │ cli.py           │   │ agent/feedback_ingest│   │ hermes feedback│
  │ process_command  │   │ .py                  │   │ import <f.jsonl│
  │ elif canonical   │   │ _watch_loop()        │   │ > (CLI invoke) │
  │ == "feedback"    │   │ polls os.scandir @1s │   │                │
  └────────┬─────────┘   └──────────┬───────────┘   └───────┬────────┘
           │                        │                       │
           │   ┌────────────────────┘                       │
           │   │                                            │
           ▼   ▼                                            ▼
  ┌──────────────────────────────────────────────────────────────────┐
  │  agent/feedback_snapshot.py                                      │
  │  build_output_snapshot(agent, conversation_history)              │
  │  → reads agent.model/provider/api_mode/max_tokens/...            │
  │  → reads most recent assistant msg from conversation_history     │
  │  → computes sha256 of output text                                │
  │  → returns OutputSnapshot pydantic model                         │
  └────────────────────────────┬─────────────────────────────────────┘
                               │
                               ▼
  ┌──────────────────────────────────────────────────────────────────┐
  │  agent/feedback_schema.py  (THE CONTRACT — all sources converge) │
  │  class FeedbackRecord(BaseModel):                                │
  │      skill_id: str        # validated against EXPERT_DIRS        │
  │      expert_id: str       # == skill_id for movie-experts        │
  │      source: Literal["cli","kais_aigc","manual"]                 │
  │      verdict: Literal["good","needs_work","bad"]                 │
  │      correction: str                                             │
  │      output_snapshot: OutputSnapshot                             │
  │      ts: datetime          # ISO 8601, auto-validated            │
  │  class OutputSnapshot(BaseModel):                                │
  │      sha256: str           # 64-char hex, field_validator         │
  │      output_text: str                                            │
  │      prompt: str           # the user msg that triggered it      │
  │      model: str                                                  │
  │      provider: str                                               │
  │      params: dict          # max_tokens, reasoning_config, ...   │
  │      captured_at: datetime # ISO 8601                            │
  └────────────────────────────┬─────────────────────────────────────┘
                               │
                  pydantic.ValidationError
                  (rejects malformed →
                   clear field-level error)
                               │
                               ▼
  ┌──────────────────────────────────────────────────────────────────┐
  │  agent/feedback_ingest.py  (PERSISTENCE — single write path)     │
  │  write_feedback_record(record: FeedbackRecord) -> Path           │
  │  → target = get_hermes_home()/"skills"/".feedback"/"incoming"/   │
  │             f"{record.skill_id}_{record.source}_{ts}.json"       │
  │  → utils.atomic_json_write(target, record.model_dump())          │
  │  → returns written path                                         │
  └────────────────────────────┬─────────────────────────────────────┘
                               │
                               ▼
              ~/.hermes/skills/.feedback/incoming/
                  (P29 builds index.json + dedup + decay
                   on top of this raw store)
```

The diagram shows the primary use case: trace from any of the three sources (left) through schema validation (middle) to the single persistence path (right). The key contract boundary is `FeedbackRecord` — all three sources MUST produce the same Pydantic model instance before persistence is allowed.

### Recommended Project Structure
```
agent/
├── feedback_schema.py      # FeedbackRecord + OutputSnapshot Pydantic models + validators
├── feedback_snapshot.py    # build_output_snapshot(agent, conversation_history) — pure function
└── feedback_ingest.py      # write_feedback_record() + watch_inbox_kais() + import_jsonl()
hermes_cli/
├── feedback.py             # register_cli(parent) — `hermes feedback import|watch|submit` subcommands
└── (existing) main.py      # +1 line: `feedback_parser = subparsers.add_parser("feedback", ...)` + register call
└── (existing) commands.py  # +1 CommandDef entry for `/feedback` slash command alias
cli.py                      # +1 elif branch in process_command() — handles /feedback inside REPL
tests/
├── agent/test_feedback_schema.py      # Pydantic validator tests (accept/reject cases)
├── agent/test_feedback_snapshot.py    # output_snapshot capture tests (sha256 determinism, param extraction)
├── agent/test_feedback_ingest.py      # write path + watcher polling + JSONL import (atomic batch)
└── hermes_cli/test_feedback_cli.py    # CLI subcommand smoke tests + slash command integration
```

### Pattern 1: Subcommand Registration via `register_cli(parent)`
**What:** New CLI subcommands are registered by a `register_cli(parent: argparse.ArgumentParser)` function in a dedicated `hermes_cli/<name>.py` module, called from `main.py`'s `main()` after `subparsers.add_parser("<name>", ...)`.
**When to use:** Every new top-level `hermes <name>` subcommand.
**Example:**
```python
# Source: hermes_cli/curator.py:495-603 (exact pattern to mirror)
# hermes_cli/feedback.py
from __future__ import annotations
import argparse

def register_cli(parent: argparse.ArgumentParser) -> None:
    """Attach `feedback` subcommands to *parent*.
    main.py calls this with the ArgumentParser returned by
    subparsers.add_parser("feedback", ...).
    """
    parent.set_defaults(func=lambda a: (parent.print_help(), 0)[1])
    subs = parent.add_subparsers(dest="feedback_command")

    p_import = subs.add_parser("import", help="Batch-import feedback records from a JSONL file")
    p_import.add_argument("file", help="Path to .jsonl file (one FeedbackRecord per line)")
    p_import.add_argument("--dry-run", action="store_true", help="Validate without writing")
    p_import.set_defaults(func=_cmd_import)

    p_watch = subs.add_parser("watch", help="Watch inbox-kais/ for new kais-aigc feedback files")
    p_watch.add_argument("--interval", type=float, default=1.0, help="Poll interval (seconds)")
    p_watch.set_defaults(func=_cmd_watch)

    p_submit = subs.add_parser("submit", help="Submit a single feedback record (scripting-friendly)")
    p_submit.add_argument("skill_id", help="Target skill (e.g. 'screenplay')")
    p_submit.add_argument("verdict", choices=["good", "needs_work", "bad"])
    p_submit.add_argument("--correction", default="", help="Free-text correction")
    p_submit.set_defaults(func=_cmd_submit)
```

### Pattern 2: Slash Command Dispatch in `process_command()`
**What:** The `/feedback` slash command is handled inside `cli.py:process_command()` (line 7265+) via the existing if/elif chain on `canonical` (the resolved command name). It reads `self.conversation_history` (cli.py:3496) + `self.agent` (cli.py:3490) to build the output_snapshot, then calls the shared ingest write path.
**When to use:** Any command that needs live REPL state (conversation history, agent instance).
**Example:**
```python
# Source: cli.py:7265-7415 (existing process_command structure)
# cli.py — add this elif branch inside process_command()
elif canonical == "feedback":
    self._handle_feedback_command(cmd_original)

def _handle_feedback_command(self, cmd_original: str) -> None:
    """Handle /feedback <verdict> [correction] [--revised <text>]."""
    from agent.feedback_schema import FeedbackRecord, OutputSnapshot
    from agent.feedback_snapshot import build_output_snapshot
    from agent.feedback_ingest import write_feedback_record

    parts = cmd_original.split(None, 1)  # ["/feedback", "needs_work the ending felt rushed"]
    if len(parts) < 2:
        _cprint(f"  {_DIM}Usage: /feedback <good|needs_work|bad> [correction] [--revised \"text\"]{_RST}")
        return

    args_text = parts[1].strip()
    # Parse verdict + correction + optional --revised flag
    # ... (argparse or manual split)

    if not self.agent or not self.conversation_history:
        _cprint(f"  {_DIM}No active conversation to attach feedback to.{_RST}")
        return

    # Find most recent assistant message
    last_assistant_idx = None
    for i in range(len(self.conversation_history) - 1, -1, -1):
        if self.conversation_history[i].get("role") == "assistant":
            last_assistant_idx = i
            break
    if last_assistant_idx is None:
        _cprint(f"  {_DIM}No assistant output found to attach feedback to.{_RST}")
        return

    snapshot = build_output_snapshot(
        agent=self.agent,
        conversation_history=self.conversation_history,
        assistant_idx=last_assistant_idx,
    )
    # TODO: skill_id detection — infer from conversation (which skill was invoked)
    #       For MVP, accept as /feedback arg or prompt user.
    record = FeedbackRecord(
        skill_id=skill_id,  # resolved by helper
        expert_id=skill_id,
        source="cli",
        verdict=verdict,
        correction=correction,
        output_snapshot=snapshot,
    )
    written = write_feedback_record(record)
    _cprint(f"  {_DIM}Feedback saved → {written}{_RST}")
```

### Pattern 3: Atomic JSON Write (for feedback persistence)
**What:** All feedback records are written via `utils.atomic_json_write` (temp file + fsync + `os.replace`). This guarantees the target file is never left partially written — if the process crashes mid-write, the previous version remains intact.
**When to use:** Every feedback persistence write (CLI, watcher, batch import).
**Example:**
```python
# Source: utils.py:111-153 (atomic_json_write) + agent/curator.py:102-107 (usage)
from utils import atomic_json_write
from hermes_constants import get_hermes_home

def write_feedback_record(record: FeedbackRecord) -> Path:
    target_dir = get_hermes_home() / "skills" / ".feedback" / "incoming"
    target_dir.mkdir(parents=True, exist_ok=True)
    # Filename: skill_id_source_timestamp.json — sortable + collision-resistant
    ts_compact = record.ts.strftime("%Y%m%dT%H%M%S%fZ")
    target = target_dir / f"{record.skill_id}_{record.source}_{ts_compact}.json"
    atomic_json_write(
        target,
        record.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
    )
    return target
```

### Pattern 4: Portable Filesystem Polling (no `watchdog` dep)
**What:** The kais-aigc inbox watcher uses stdlib `os.scandir` + `time.sleep` in a loop. It tracks seen filenames (by mtime + size + name) to detect new files. When a new file appears, it waits for write completion (size stable across 2 polls), then validates + ingests + moves to `processed/`.
**When to use:** The kais-aigc file-exchange watcher (INGEST-02). Also suitable for any future file-based ingestion.
**Why not `watchdog`:** Adds a dependency for zero MVP value. `watchdog`'s cross-platform Observer is nice but polling at 1s is fast enough for file-exchange (kais-aigc writes are batch, not realtime). Portability: `os.scandir` works identically on Linux, macOS, Windows, Termux. `[ASSUMED — stdlib portability is well-known but no in-codebase precedent to cite]`
**Example:**
```python
# Source: stdlib pattern (no in-codebase precedent — Hermes has no existing file watcher)
import os
import time
from pathlib import Path

def watch_inbox_kais(inbox_dir: Path, *, interval: float = 1.0, stop_event=None) -> None:
    """Poll inbox_dir for new .json files, validate + ingest them."""
    inbox_dir.mkdir(parents=True, exist_ok=True)
    processed_dir = inbox_dir.parent / "processed-kais"
    processed_dir.mkdir(parents=True, exist_ok=True)

    seen: dict[str, tuple[float, int]] = {}  # name -> (mtime, size)
    pending: dict[str, int] = {}  # name -> last observed size (write-in-progress detection)

    while True:
        if stop_event and stop_event.is_set():
            break
        for entry in os.scandir(inbox_dir):
            if not entry.name.endswith(".json") or entry.is_dir():
                continue
            stat = entry.stat()
            key = entry.name
            current = (stat.st_mtime, stat.st_size)
            if key in seen and seen[key] == current:
                continue  # already processed or stable-seen
            # Write-in-progress detection: size must be stable across 2 polls
            if pending.get(key) != stat.st_size:
                pending[key] = stat.st_size
                continue  # wait for next poll to confirm stability
            # File is stable — ingest
            try:
                _ingest_kais_file(Path(entry.path))
                seen[key] = current
                # Move to processed/ (atomic rename)
                target = processed_dir / entry.name
                Path(entry.path).rename(target)
            except Exception as exc:
                logger.warning("kais inbox ingest failed for %s: %s", entry.name, exc)
                seen[key] = current  # don't retry endlessly; move to errors/
        time.sleep(interval)
```

### Anti-Patterns to Avoid
- **`Path.home() / ".hermes"` in feedback code** — use `get_hermes_home()` from `hermes_constants` (CLAUDE.md anti-pattern; conftest.py redirects HERMES_HOME per-test and `Path.home()` bypasses that).
- **`open()` without `encoding="utf-8"`** — Ruff PLW1514 will block the merge. Every JSON read/write must pass `encoding="utf-8"` explicitly.
- **Bare `except:` in watcher loop** — catch specific exceptions (`OSError`, `json.JSONDecodeError`, `pydantic.ValidationError`) and log with `%s` positional args.
- **Modifying `conversation_history` from `/feedback` handler** — the snapshot builder reads but must NOT mutate the live conversation list.
- **Adding `watchdog` as a new dependency** — CONTEXT.md deferred decision allows polling; stdlib is portable and adds zero install risk.
- **Writing feedback files with non-atomic `open().write()`** — use `utils.atomic_json_write` always (prevents partial files on crash).
- **Hand-rolling sha256 of text with `.encode("utf-8")`** — for reproducibility, hash the EXACT output text bytes. Document the encoding in the snapshot schema so P29/P30 dedup is deterministic.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atomic file writes | `open().write()` + manual fsync | `utils.atomic_json_write` (`utils.py:111`) | Already handles temp-file + fsync + os.replace + mode preservation. Battle-tested in curator state writes. |
| JSON schema validation | Manual regex/enum/if-else checks | Pydantic v2 `FeedbackRecord` with `field_validator` | Hand-rolling 6+ validated fields with clear error messages is 50+ lines. Pydantic gives field-level `ValidationError` messages for free (INGEST-04 requirement). |
| sha256 + ISO 8601 provenance | Custom hashing function | `hashlib.sha256(raw).hexdigest()` + `datetime.now(timezone.utc).isoformat()` | Exact pattern from `skills/movie-experts/_eval/snapshot.py:96-97` — already proven in the eval harness. |
| CLI subparser registration | Manual `argparse` boilerplate in main.py | `hermes_cli/<name>.py:register_cli(parent)` pattern | Mirrors `hermes_cli/curator.py:495`. Keeps main.py god-file from growing. |
| Slash command alias resolution | Manual if/elif on raw command string | `hermes_cli/commands.py:COMMAND_REGISTRY` + `resolve_command()` | Already handles aliases + canonical name resolution (`cli.py:7281-7284`). Add one `CommandDef` entry. |
| HERMES_HOME path resolution | `Path.home() / ".hermes"` | `hermes_constants.get_hermes_home()` | Respects `HERMES_HOME` env var + active_profile. CLAUDE.md mandates this. |

**Key insight:** This phase is almost entirely assembly of existing primitives. The only genuinely new logic is (1) the Pydantic model definition, (2) the output_snapshot builder, (3) the polling watcher loop, and (4) the JSONL batch parser. Everything else (atomic write, path resolution, CLI registration, slash dispatch) reuses proven patterns.

## Runtime State Inventory

> This phase is **greenfield-additive**, not a rename/refactor/migration. No existing runtime state is renamed. However, the phase DOES create new runtime state (the `~/.hermes/skills/.feedback/` directory tree), so we inventory what gets created.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None existing. P28 CREATES `~/.hermes/skills/.feedback/incoming/*.json` (raw feedback records), `~/.hermes/skills/.feedback/inbox-kais/*.json` (kais drop zone), `~/.hermes/skills/.feedback/processed-kais/*.json` (ingested kais files), `~/.hermes/skills/.feedback/manual-import/*.json` (optional staging). | Create directories lazily on first write (`mkdir(parents=True, exist_ok=True)`). No migration. |
| Live service config | None. The kais-aigc inbox path is configurable via `HERMES_FEEDBACK_INBOX_KAIS` env var (CONTEXT.md specifics line 74). | Read env var in watcher startup; default to `get_hermes_home()/"skills"/".feedback"/"inbox-kais"`. |
| OS-registered state | None. No systemd units, no launchd plists, no Task Scheduler entries. The watcher is a CLI-invoked foreground process (`hermes feedback watch`) or optionally wired into the gateway loop later (out of P28 scope). | None. |
| Secrets/env vars | New optional env var `HERMES_FEEDBACK_INBOX_KAIS` (path override for kais inbox). No secrets — feedback content is assumed trusted (FUTURE-V6-06 PII redaction deferred). | Document in `.env.example` (additive — one line). |
| Build artifacts | None. No compiled artifacts, no egg-info changes (no `pyproject.toml` changes — no new packages). | None. |

## Common Pitfalls

### Pitfall 1: Ruff PLW1514 blocks merge on every `open()`
**What goes wrong:** Developer writes `open(path, "w")` without `encoding="utf-8"`. Ruff CI step (`ruff check .`) fails.
**Why it happens:** Python defaults to platform encoding (cp1252 on Windows), which silently corrupts non-ASCII feedback content (Chinese corrections are common in this project).
**How to avoid:** Pass `encoding="utf-8"` to EVERY `open()`, `read_text()`, `write_text()` call. Use `utils.atomic_json_write` (which already does this internally at `utils.py:151`).
**Warning signs:** CI lint step fails with `PLW1514 unspecified-encoding`.

### Pitfall 2: File watcher reads partially-written files
**What goes wrong:** kais-aigc-platform writes a 50KB JSON file; the watcher polls mid-write, reads a truncated file, `json.loads` raises `JSONDecodeError`, feedback is lost.
**Why it happens:** Filesystem writes are not atomic from the reader's perspective. A 50KB write may span multiple syscalls.
**How to avoid:** Two-poll stability check (Pattern 4 above): record file size on first sighting, only ingest when size is identical on the next poll. This guarantees the writer has finished.
**Warning signs:** Intermittent `JSONDecodeError` in watcher logs when kais-aigc writes large files.

### Pitfall 3: sha256 non-determinism across encoding boundaries
**What goes wrong:** The same LLM output produces different sha256 hashes on different runs, breaking dedup (P29 STORE-04 depends on stable sha256).
**Why it happens:** Hashing `text.encode("utf-8")` vs hashing raw bytes from the API response vs hashing after JSON serialization all produce different hashes. Surrogate characters (`\ud800-\udfff`) survive in Python strings but may be sanitized differently.
**How to avoid:** Pick ONE canonical encoding path and document it in `OutputSnapshot`. Recommended: hash `output_text.encode("utf-8")` where `output_text` is the exact string from `conversation_history[i]["content"]`. Run `agent/message_sanitization.py` sanitization BEFORE hashing for surrogate safety. Document this in the schema docstring.
**Warning signs:** Same feedback submitted twice produces two records with different `output_snapshot.sha256`.

### Pitfall 4: `/feedback` fails when no movie-expert skill was invoked
**What goes wrong:** Operator types `/feedback good` after a normal chat turn (no skill invoked). The handler can't determine `skill_id` because no skill was active.
**Why it happens:** `skill_id` validation requires the value to be in `EXPERT_DIRS` (INGEST-04). If no skill was invoked, there's no skill_id to attach.
**How to avoid:** Detect whether the most recent assistant turn was skill-invoked (check for `_SKILL_INVOCATION_PREFIX` marker from `agent/skill_commands.py:47` in the preceding user message). If not, print a clear error: "No movie-expert output found in this conversation. /feedback attaches to the most recent skill output." Do NOT silently default to a random skill.
**Warning signs:** Feedback records with wrong `skill_id` because the handler guessed.

### Pitfall 5: `conversation_history` missing content field
**What goes wrong:** The snapshot builder reads `conversation_history[i]["content"]` but some messages use the `parts` / `tool_calls` structure instead of plain string `content`.
**Why it happens:** OpenAI tool-call messages have `content=None` with `tool_calls=[...]`. Anthropic messages may use `content=[{"type": "text", ...}]` list form.
**How to avoid:** Defensive extraction — handle (a) `content` as string, (b) `content` as list of dicts (extract `text` parts), (c) `content=None` (skip — this is a tool-call turn, not a feedback target). Add a unit test for each shape.
**Warning signs:** `TypeError` or empty `output_text` in snapshot when operator gives feedback on a tool-heavy turn.

### Pitfall 6: Watcher process orphaned on Ctrl+C
**What goes wrong:** Operator runs `hermes feedback watch` in one terminal, opens another, forgets, the watcher runs forever.
**Why it happens:** Polling loops have no built-in lifecycle management.
**How to avoid:** Install SIGINT/SIGTERM handler in the watcher that sets a `stop_event`. Print a PID + log path on startup so operator can `kill` it. Document `hermes feedback watch --foreground` vs future background mode (background is out of P28 scope).
**Warning signs:** Zombie watcher processes in `ps aux | grep feedback`.

### Pitfall 7: JSONL import crashes on line N, writes lines 1..N-1
**What goes wrong:** Batch import validates 10 records, record 7 is malformed, but records 1-6 are already written. The operator now has a partial import with no clear rollback.
**Why it happens:** Naive implementation writes each record as it parses.
**How to avoid:** CONTEXT.md recommends all-or-nothing. Parse + validate ALL records into a list first; only if all pass, write all. If any fails, print the line number + validation error and exit without writing.
**Warning signs:** Operator reports "import said it failed but I see some files in incoming/".

### Pitfall 8: `agent.request_overrides` contains non-serializable values
**What goes wrong:** `request_overrides` is `Dict[str, Any]` and may contain callables or custom objects that `json.dump` can't serialize.
**Why it happens:** `agent_init.py:489` sets `agent.request_overrides = dict(request_overrides or {})` with no type constraint.
**How to avoid:** In the snapshot builder, filter `request_overrides` to JSON-serializable primitives (str/int/float/bool/None/list/dict). Use `pydantic.model_dump(mode="json")` which handles this automatically. Log a warning if any keys are dropped.
**Warning signs:** `TypeError: Object of type function is not JSON serializable` during feedback write.

## Code Examples

Verified patterns from the codebase:

### Pydantic v2 Model with Field Validators (the `FeedbackRecord` contract)
```python
# Source: pydantic v2 docs (field_validator) + codebase pattern from
# hermes_cli/web_server.py:85 (BaseModel import). Pydantic 2.13.4 verified installed.
# agent/feedback_schema.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, field_validator, ValidationError

# Reuse the frozen expert list — single source of truth for skill_id validation.
# Source: skills/movie-experts/_eval/snapshot.py:40-55
# NOTE: import path may need sys.path adjustment since _eval/ is not a Python package.
# Alternative: copy the list into feedback_schema.py with a comment pointing to snapshot.py.
_KNOWN_EXPERT_IDS: frozenset[str] = frozenset({
    "animator", "colorist", "composer", "continuity", "drawer", "editor",
    "foley", "mixer", "performer", "scene_builder", "screenplay",
    "spatial_audio", "style_genome", "voicer",
    # v4/v5 additions (verify against current skills/movie-experts/ at plan-phase):
    "animation_studio", "audio_pipeline", "character_designer", "cinematographer",
    "compliance_gate", "compliance_marketing", "creative_source", "documentary_maker",
    "hook_retention", "lip_sync",
})


class OutputSnapshot(BaseModel):
    """Provenance for the LLM output being reviewed."""
    sha256: str               # 64-char hex of output_text.encode("utf-8")
    output_text: str          # the exact assistant output being reviewed
    prompt: str               # the user msg that triggered the output
    model: str
    provider: str
    api_mode: str = ""
    params: dict              # {max_tokens, reasoning_config, service_tier, request_overrides, ...}
    captured_at: datetime     # ISO 8601 — when snapshot was built

    @field_validator("sha256")
    @classmethod
    def _sha256_is_64_hex(cls, v: str) -> str:
        if len(v) != 64 or not all(c in "0123456789abcdef" for c in v.lower()):
            raise ValueError("sha256 must be 64 lowercase hex characters")
        return v.lower()


class FeedbackRecord(BaseModel):
    """Normalized feedback record — the single schema all three sources emit."""
    skill_id: str
    expert_id: str
    source: Literal["cli", "kais_aigc", "manual"]
    verdict: Literal["good", "needs_work", "bad"]
    correction: str = ""
    revised_output: str | None = None
    output_snapshot: OutputSnapshot
    ts: datetime              # ISO 8601 — when feedback was submitted

    @field_validator("skill_id", "expert_id")
    @classmethod
    def _known_expert(cls, v: str) -> str:
        if v not in _KNOWN_EXPERT_IDS:
            raise ValueError(
                f"skill_id '{v}' is not a known movie-expert. "
                f"Known: {sorted(_KNOWN_EXPERT_IDS)}"
            )
        return v

    @field_validator("ts")
    @classmethod
    def _ts_has_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("ts must be timezone-aware (ISO 8601 with offset)")
        return v


# Usage — validation rejects malformed payloads with field-level errors:
try:
    record = FeedbackRecord(
        skill_id="screenplay",
        expert_id="screenplay",
        source="cli",
        verdict="needs_work",
        correction="the ending felt rushed",
        output_snapshot=snapshot,
        ts=datetime.now(timezone.utc),
    )
except ValidationError as exc:
    # exc.errors() returns [{type, loc, msg, input, url}, ...] — clear + actionable
    for err in exc.errors():
        logger.warning("feedback validation failed: loc=%s msg=%s", err["loc"], err["msg"])
```

### Output Snapshot Builder (reads agent + conversation state)
```python
# Source: agent/agent_init.py:486-489 (param attrs) + cli.py:3496 (conversation_history)
#         + skills/movie-experts/_eval/snapshot.py:96-97 (sha256 + ISO 8601 pattern)
# agent/feedback_snapshot.py
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from agent.feedback_schema import OutputSnapshot


def build_output_snapshot(
    agent: Any,
    conversation_history: list[dict[str, Any]],
    assistant_idx: int,
) -> OutputSnapshot:
    """Build an OutputSnapshot from live conversation state.

    Called by the /feedback slash-command handler (cli.py) and by the
    `hermes feedback submit` CLI subcommand.
    """
    assistant_msg = conversation_history[assistant_idx]
    output_text = _extract_text(assistant_msg.get("content"))

    # The prompt is the most recent user message BEFORE this assistant turn.
    prompt_text = ""
    for i in range(assistant_idx - 1, -1, -1):
        if conversation_history[i].get("role") == "user":
            prompt_text = _extract_text(conversation_history[i].get("content"))
            break

    sha = hashlib.sha256(output_text.encode("utf-8")).hexdigest()

    # Collect params actually used — these matter for P30 eval-gate ablation.
    params: dict[str, Any] = {}
    for attr in ("max_tokens", "reasoning_config", "service_tier", "request_overrides"):
        val = getattr(agent, attr, None)
        if val is not None:
            params[attr] = val

    return OutputSnapshot(
        sha256=sha,
        output_text=output_text,
        prompt=prompt_text,
        model=getattr(agent, "model", "") or "",
        provider=getattr(agent, "provider", "") or "",
        api_mode=getattr(agent, "api_mode", "") or "",
        params=params,
        captured_at=datetime.now(timezone.utc),
    )


def _extract_text(content: Any) -> str:
    """Handle string / list-of-dicts / None content shapes."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Anthropic-style: [{"type": "text", "text": "..."}, ...]
        parts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"]
        return "".join(parts)
    return str(content)
```

### Atomic JSONL Batch Import (all-or-nothing)
```python
# Source: json stdlib + CONTEXT.md "all-or-nothing with clear error listing" recommendation
# agent/feedback_ingest.py
from __future__ import annotations

import json
from pathlib import Path

from agent.feedback_schema import FeedbackRecord
from agent.feedback_ingest import write_feedback_record  # the single write path


def import_jsonl(file_path: Path, *, dry_run: bool = False) -> tuple[int, list[str]]:
    """Import feedback records from a JSONL file. All-or-nothing.

    Returns (count_written, errors). If errors is non-empty, NOTHING was written.
    """
    errors: list[str] = []
    records: list[FeedbackRecord] = []

    lines = file_path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines, start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {i}: invalid JSON: {exc}")
            continue
        try:
            records.append(FeedbackRecord(**raw))
        except Exception as exc:  # pydantic.ValidationError
            errors.append(f"line {i}: validation failed: {exc}")

    if errors:
        return (0, errors)
    if dry_run:
        return (len(records), [])

    for record in records:
        write_feedback_record(record)
    return (len(records), [])
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@dataclass` for structured records (e.g., `ClassifiedError`) | Pydantic v2 `BaseModel` for validated records | Pydantic 2.x (current pin 2.13.4) | `FeedbackRecord` uses Pydantic (needs validation); `ClassifiedError` stays `@dataclass` (no validation needed — internal only). Mixed is acceptable per CLAUDE.md. |
| Manual `open().write()` for persistence | `utils.atomic_json_write` (temp + fsync + replace) | Established in `utils.py:111` | All feedback writes use atomic write — no partial files on crash. |
| `Path.home() / ".hermes"` (v0-v1) | `hermes_constants.get_hermes_home()` (v2+) | Early project history | CLAUDE.md mandates `get_hermes_home()`. conftest.py redirects HERMES_HOME per-test; `Path.home()` bypasses that and leaks. |

**Deprecated/outdated:**
- None relevant to this phase. The codebase is current.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `os.scandir` polling at 1s is portable across Linux/macOS/Windows/Termux | Architecture Patterns (Pattern 4) | LOW — stdlib portability is well-established. If Termux has a quirk, fall back to `os.listdir` + `os.stat`. |
| A2 | `_KNOWN_EXPERT_IDS` list in `feedback_schema.py` can be synced manually from `skills/movie-experts/_eval/snapshot.py:EXPERT_DIRS` | Code Examples (Pydantic model) | MEDIUM — the two lists can drift. Mitigation: at plan-phase, decide whether to (a) copy with comment pointer, (b) make `_eval/` importable, or (c) auto-discover from `skills/movie-experts/*/SKILL.md` frontmatter. Recommend (a) for MVP simplicity, (c) for P29+. |
| A3 | `conversation_history[i]["content"]` is always present on assistant messages | Pitfall 5 + Code Examples | MEDIUM — some message shapes use `content=None` (tool calls) or `content=[{...}]` (Anthropic). The `_extract_text` helper handles all three, but untested shapes may exist. Mitigation: unit test each shape. |
| A4 | The `temperature` / `top_p` LLM params are NOT stored as agent attributes (only inside `request_overrides`) | Code Examples (snapshot builder) | LOW — confirmed via grep: no `self.temperature` in `agent/` or `run_agent.py`. If a provider profile injects them, they'd appear in `request_overrides`. The snapshot captures `request_overrides`, so they're covered. |
| A5 | `hermes feedback watch` is a foreground CLI process (not wired into gateway loop) | Runtime State Inventory | LOW — the gateway integration is a P29+ concern. P28 ships the foreground watcher as the MVP ingestion path. Operator runs it in a separate terminal or tmux pane. |
| A6 | `/feedback` slash command should resolve `skill_id` from the most recent skill invocation in conversation_history | Pitfall 4 | MEDIUM — the exact detection logic (checking for `_SKILL_INVOCATION_PREFIX` marker) needs validation at plan-phase. If the skill invocation expanded into multiple turns, "most recent" may be ambiguous. Mitigation: for MVP, require operator to specify skill_id if ambiguous (`/feedback screenplay needs_work ...`). |

## Open Questions

1. **`skill_id` resolution for `/feedback`** — How does the slash command know WHICH skill the operator is giving feedback on?
   - What we know: `agent/skill_commands.py:47` defines `_SKILL_INVOCATION_PREFIX = "[IMPORTANT: The user has invoked the "` marker that gets prepended to the user message when a skill is invoked. We can scan backward in `conversation_history` for the most recent user message starting with this marker to identify the skill.
   - What's unclear: Does the marker contain the skill name in an extractable position? What if multiple skills were invoked in sequence? What if the operator used `/bundle` (multi-skill)?
   - Recommendation: For MVP, scan for the marker, extract skill name, fall back to prompting the operator if ambiguous. Plan-phase should verify the exact marker format by reading `_build_skill_message` in `skill_commands.py`.

2. **Watcher lifecycle** — Is `hermes feedback watch` foreground-only, or should P28 wire it into the gateway run loop?
   - What we know: CONTEXT.md does not specify. The gateway run loop (`gateway/run.py`) is the natural long-running host, but wiring into it is more invasive.
   - Recommendation: Ship foreground-only for MVP (`hermes feedback watch`). Document that gateway integration is a P29+ enhancement. Operator runs watcher in a separate terminal. This keeps P28 scope minimal.

3. **JSONL `import` atomic batch + `--dry-run`** — Should the import command also support `--dry-run` (validate-only)?
   - What we know: CONTEXT.md recommends all-or-nothing. A `--dry-run` flag is a trivial addition that helps operators test their JSONL before committing.
   - Recommendation: Yes — include `--dry-run` (shown in the `register_cli` Pattern 1 example above). Zero extra complexity.

4. **`_KNOWN_EXPERT_IDS` source of truth** — Copy from `snapshot.py:EXPERT_DIRS`, or auto-discover?
   - What we know: `snapshot.py:40-55` has a frozen 14-element list (the original v1 experts). But `skills/movie-experts/` now has 20+ directories (verified via `ls` during research). The snapshot.py list is STALE — it doesn't include v3/v4/v5 additions.
   - Recommendation: At plan-phase, auto-discover from `skills/movie-experts/*/SKILL.md` frontmatter `name` field at module load. This is the single source of truth. Cache the result. If discovery fails (e.g., running outside the repo), fall back to a hardcoded list + warning.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | All code | ✓ | 3.13 (target per CLAUDE.md) | — |
| pydantic | `FeedbackRecord` schema (INGEST-04) | ✓ | 2.13.4 | — |
| stdlib `hashlib` | sha256 for output_snapshot (INGEST-04) | ✓ | stdlib | — |
| stdlib `json` | JSONL parse + persistence (INGEST-03, INGEST-05) | ✓ | stdlib | — |
| stdlib `argparse` | CLI subparser registration | ✓ | stdlib | — |
| stdlib `os.scandir` | kais-aigc file watcher (INGEST-02) | ✓ | stdlib | `os.listdir` + `os.stat` (marginally slower) |
| `~/.hermes/skills/` writable dir | Feedback persistence root | ✓ | — | — |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** None — all dependencies are stdlib or already-pinned pydantic.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 + pytest-timeout 2.4.0 (`[dev]` extra, `pyproject.toml`) |
| Config file | `pyproject.toml:348` (`[tool.pytest.ini_options]`, testpaths=["tests"], 30s per-test timeout) |
| Quick run command | `python -m pytest tests/agent/test_feedback_schema.py -x` |
| Full suite command | `python -m pytest tests/agent/test_feedback_*.py tests/hermes_cli/test_feedback_cli.py -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INGEST-01 | `/feedback good` persists a valid FeedbackRecord with source="cli" | unit + integration | `python -m pytest tests/hermes_cli/test_feedback_cli.py::test_slash_feedback_persists -x` | Wave 0 |
| INGEST-01 | `/feedback` with no prior skill output prints clear error, does not crash | unit | `python -m pytest tests/hermes_cli/test_feedback_cli.py::test_slash_feedback_no_skill_output -x` | Wave 0 |
| INGEST-02 | kais-aigc file dropped in inbox-kais/ is ingested + moved to processed-kais/ | integration | `python -m pytest tests/agent/test_feedback_ingest.py::test_watch_inbox_ingests_new_file -x` | Wave 0 |
| INGEST-02 | Partially-written file is NOT ingested until size stabilizes (2-poll check) | unit | `python -m pytest tests/agent/test_feedback_ingest.py::test_watch_inbox_waits_for_stable_size -x` | Wave 0 |
| INGEST-03 | `hermes feedback import valid.jsonl` writes all records | integration | `python -m pytest tests/agent/test_feedback_ingest.py::test_import_jsonl_all_valid -x` | Wave 0 |
| INGEST-03 | `hermes feedback import invalid.jsonl` writes NOTHING, lists all errors | integration | `python -m pytest tests/agent/test_feedback_ingest.py::test_import_jsonl_atomic_reject -x` | Wave 0 |
| INGEST-04 | FeedbackRecord rejects unknown verdict with field-level error | unit | `python -m pytest tests/agent/test_feedback_schema.py::test_reject_bad_verdict -x` | Wave 0 |
| INGEST-04 | FeedbackRecord rejects unknown skill_id with field-level error | unit | `python -m pytest tests/agent/test_feedback_schema.py::test_reject_unknown_skill_id -x` | Wave 0 |
| INGEST-04 | FeedbackRecord rejects non-ISO-8601 ts | unit | `python -m pytest tests/agent/test_feedback_schema.py::test_reject_naive_datetime -x` | Wave 0 |
| INGEST-04 | OutputSnapshot rejects non-64-char sha256 | unit | `python -m pytest tests/agent/test_feedback_schema.py::test_reject_bad_sha256 -x` | Wave 0 |
| INGEST-04 | All three sources (cli/kais_aigc/manual) produce identical JSON for same input | unit | `python -m pytest tests/agent/test_feedback_schema.py::test_source_enum_same_schema -x` | Wave 0 |
| INGEST-05 | Batch import of 10 sample records succeeds (cold-start path) | integration | `python -m pytest tests/agent/test_feedback_ingest.py::test_import_jsonl_cold_start_10 -x` | Wave 0 |
| INGEST-04/05 | output_snapshot sha256 is deterministic for same input text | unit | `python -m pytest tests/agent/test_feedback_snapshot.py::test_sha256_deterministic -x` | Wave 0 |
| INGEST-04 | output_snapshot captures model/provider/params from agent | unit | `python -m pytest tests/agent/test_feedback_snapshot.py::test_captures_agent_params -x` | Wave 0 |
| INGEST-04 | output_snapshot handles all content shapes (str/list/None) | unit | `python -m pytest tests/agent/test_feedback_snapshot.py::test_extract_text_all_shapes -x` | Wave 0 |
| encoding | Every `open()` in new modules passes `encoding="utf-8"` (Ruff PLW1514) | lint | `ruff check agent/feedback_schema.py agent/feedback_snapshot.py agent/feedback_ingest.py hermes_cli/feedback.py` | Wave 0 |
| FOUND-08 | No bundled SKILL.md or references/*.md bytes changed | smoke | `git diff --name-only v5.0 -- skills/movie-experts/ \| grep -v _eval \| grep -v _shared` (must be empty) | Phase gate |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/agent/test_feedback_schema.py -x` (fast schema tests, <5s)
- **Per wave merge:** `python -m pytest tests/agent/test_feedback_*.py tests/hermes_cli/test_feedback_cli.py -x` (full feedback suite, <30s)
- **Phase gate:** Full feedback suite green + `ruff check .` green + FOUND-08 byte-intact check passes + manual smoke (`hermes feedback import sample.jsonl` on 10-record file)

### Wave 0 Gaps
- [ ] `tests/agent/test_feedback_schema.py` — Pydantic validator tests (accept/reject cases for each field)
- [ ] `tests/agent/test_feedback_snapshot.py` — output_snapshot capture tests (sha256 determinism, param extraction, content-shape handling)
- [ ] `tests/agent/test_feedback_ingest.py` — write path + watcher polling (2-poll stability) + JSONL atomic import
- [ ] `tests/hermes_cli/test_feedback_cli.py` — CLI subcommand smoke tests + `/feedback` slash command integration
- [ ] `tests/fixtures/feedback/` — sample JSONL files (valid_10.jsonl, invalid_verdict.jsonl, invalid_skill.jsonl, cold_start.jsonl)

*(No framework install needed — pytest already in `[dev]` extra)*

## Security Domain

> `security_enforcement` is not explicitly set in `.planning/config.json`, so this section is included per the "absent = enabled" rule. However, this phase has a minimal security surface — it ingests operator-provided feedback into a local directory under `~/.hermes/`. No network endpoints, no auth, no secrets beyond the existing HERMES_HOME trust boundary.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth in P28 — feedback ingestion is local-only, operator-trusted. |
| V3 Session Management | no | No sessions created. |
| V4 Access Control | no | Filesystem permissions on `~/.hermes/` are the only access control (existing). |
| V5 Input Validation | yes | Pydantic `FeedbackRecord` with `field_validator` on every field. Rejects malformed payloads with field-level errors (INGEST-04). This IS the input validation layer. |
| V6 Cryptography | partial | sha256 used for output fingerprinting (dedup, not security). Not a security control — just a content hash. No encryption needed. |

### Known Threat Patterns for feedback ingestion

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed JSON in inbox-kais/ crashes watcher | Denial of Service | `try/except json.JSONDecodeError` per file; log + move to `errors/` dir; continue watching. Never crash the loop. |
| Path traversal via crafted filename in inbox-kais/ (e.g. `../../etc/passwd.json`) | Tampering / Elevation | Sanitize filename: use `Path(entry.name).name` (strips directory components). Never use user-supplied filename as the write target — always generate from `skill_id + source + ts`. |
| Feedback file grows unbounded | Denial of Service (disk fill) | Out of P28 scope (P29 STORE-03 time-decay). Document that operator can manually prune `~/.hermes/skills/.feedback/`. |
| Pydantic ValidationError reveals internal schema to attacker | Information Disclosure | LOW risk — schema is not secret (it's in the repo). Error messages help operators fix their JSON. Acceptable. |
| Watcher process orphaned, consumes CPU | Denial of Service | SIGINT/SIGTERM handler + stop_event (Pitfall 6). Print PID on startup. |

## Sources

### Primary (HIGH confidence)
- `skills/movie-experts/_eval/snapshot.py:40-55,75-117` — EXPERT_DIRS frozen list, sha256 + git_sha + ISO 8601 provenance pattern, anti-spoofing rationale (T-00-08). Directly informs `OutputSnapshot` schema.
- `hermes_cli/curator.py:495-603` — `register_cli(parent)` subcommand registration pattern. Exact template for `hermes_cli/feedback.py`.
- `agent/curator.py:71-117` — `_state_file()`, `load_state`, `save_state`, `atomic_json_write` persistence pattern. Exact template for feedback persistence.
- `utils.py:111-153` — `atomic_json_write` (temp + fsync + os.replace). Use for every feedback write.
- `cli.py:7265-7415` — `process_command()` slash-command dispatch (if/elif canonical chain). Where `/feedback` slots in.
- `cli.py:3490,3496` — `self.agent` + `self.conversation_history` — the REPL state the `/feedback` handler reads.
- `hermes_cli/commands.py:42,64` — `CommandDef` + `COMMAND_REGISTRY` — where `/feedback` alias is registered.
- `agent/agent_init.py:486-489` — `agent.max_tokens`, `agent.reasoning_config`, `agent.service_tier`, `agent.request_overrides` — the params captured in `OutputSnapshot`.
- `agent/skill_commands.py:47` — `_SKILL_INVOCATION_PREFIX` marker — used to detect which skill was invoked for `skill_id` resolution.
- `hermes_constants.py:53` — `get_hermes_home()` — canonical HERMES_HOME resolution (CLAUDE.md mandates this over `Path.home()`).
- `pyproject.toml:60` — `pydantic==2.13.4` pin (verified present via `python3 -c "import pydantic"`).

### Secondary (MEDIUM confidence)
- `tests/agent/test_curator_reports.py:16-33` — `curator_env` fixture pattern (isolated HERMES_HOME via monkeypatch + importlib.reload). Template for `feedback_env` test fixture.
- `tests/conftest.py:57-73,496-560` — `_CREDENTIAL_SUFFIXES`, `_live_system_guard` autouse fixture. Test hermeticity invariants.
- `agent/error_classifier.py:69-89` — `@dataclass ClassifiedError` (stdlib dataclass, not Pydantic). Shows the "structured record" pattern; `FeedbackRecord` uses Pydantic instead because it needs validation.
- `hermes_cli/subcommands/skills.py:12-80` — `build_skills_parser(subparsers, *, cmd_skills=...)` alternative registration pattern (handler injection). Either this or `register_cli(parent)` works.

### Tertiary (LOW confidence)
- stdlib `os.scandir` portability across Termux — `[ASSUMED]` based on general stdlib portability knowledge. No in-codebase precedent (Hermes has no existing file watcher). Validate on Termux during execution.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pydantic verified installed at 2.13.4; all other deps are stdlib. Zero new packages.
- Architecture: HIGH — every integration point verified via direct file reads (cli.py:7265, curator.py:495, snapshot.py:40, agent_init.py:486). No guessing.
- Pitfalls: HIGH — 8 pitfalls identified, all grounded in codebase-specific patterns (Ruff PLW1514, atomic write, content shapes, watcher stability).
- Slash command integration: MEDIUM — the `process_command` elif chain is verified, but the exact `skill_id` resolution logic (marker parsing) needs plan-phase verification against `_build_skill_message` in `skill_commands.py`.

**Research date:** 2026-06-24
**Valid until:** 2026-07-24 (30 days — stable codebase, no fast-moving dependencies)
