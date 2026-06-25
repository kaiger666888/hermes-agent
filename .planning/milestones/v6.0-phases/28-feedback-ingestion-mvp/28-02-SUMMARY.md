---
phase: 28
plan: 02
subsystem: feedback-ingestion
tags: [feedback, cli, slash-command, file-watcher, jsonl, kais-aigc, atomic-import, polling]
requires:
  - "agent.feedback_schema.FeedbackRecord (Plan 01)"
  - "agent.feedback_schema.OutputSnapshot (Plan 01)"
  - "agent.feedback_snapshot.build_output_snapshot (Plan 01)"
  - "agent.feedback_ingest.write_feedback_record (Plan 01)"
  - "hermes_cli.curator.register_cli (hermes_cli/curator.py:495-603 — template)"
  - "hermes_cli.commands.CommandDef + COMMAND_REGISTRY (hermes_cli/commands.py:42,64)"
  - "agent.skill_commands._SKILL_INVOCATION_PREFIX (agent/skill_commands.py:47)"
provides:
  - "hermes_cli.feedback.register_cli (subcommand dispatcher for hermes feedback)"
  - "hermes_cli.feedback._cmd_import (atomic JSONL batch import CLI)"
  - "hermes_cli.feedback._cmd_watch (kais-aigc inbox watcher CLI)"
  - "hermes_cli.feedback._cmd_submit (single-record scripting CLI)"
  - "agent.feedback_ingest.import_jsonl (atomic all-or-nothing JSONL import)"
  - "agent.feedback_ingest.watch_inbox_kais (portable polling file watcher)"
  - "agent.feedback_ingest._scan_once (single-pass testable watcher helper)"
  - "agent.feedback_ingest._resolve_kais_inbox (HERMES_FEEDBACK_INBOX_KAIS env override)"
  - "agent.feedback_ingest._move_to_errors (malformed-file safety move)"
  - "HermesCLI._handle_feedback_command (cli.py process_command elif branch + mixin method)"
  - "CommandDef name='feedback' in COMMAND_REGISTRY (slash-command alias)"
affects:
  - "Phase 29 STORE (consumes incoming/ directory populated by all three sources)"
  - "Phase 30 GATE (consumes OutputSnapshot sha256 + params for ablation — CLI path captures full param set)"
  - "Phase 31 EVOL (consumes the corrected outputs as candidate insights source)"
tech-stack:
  added: []
  patterns:
    - "register_cli(parent) subcommand pattern (mirrors hermes_cli/curator.py:495-603)"
    - "Atomic JSONL batch import — parse + validate ALL before write ANY (Pitfall #7 / T-28-11)"
    - "Portable stdlib os.scandir polling watcher (no watchdog dependency — works Linux/macOS/Windows/Termux)"
    - "2-poll stability check for partial-write detection (Pitfall #2 / T-28-09)"
    - "Source override anti-spoofing (force source='kais_aigc' regardless of JSON — T-28-07)"
    - "Path-traversal defense via Path(entry.name).name + write-target-from-record-fields (T-28-06)"
    - "SIGINT/SIGTERM-to-stop_event translation for clean watcher shutdown (Pitfall #6 / T-28-10)"
    - "Skill-invocation marker regex scan for skill_id resolution (verified format from skill_commands.py:550-553)"
    - "Slash-command dispatch via process_command() elif canonical chain + COMMAND_REGISTRY entry"
key-files:
  created:
    - "hermes_cli/feedback.py"
    - "tests/hermes_cli/test_feedback_cli.py"
  modified:
    - "agent/feedback_ingest.py"
    - "tests/agent/test_feedback_ingest.py"
    - "hermes_cli/main.py"
    - "hermes_cli/commands.py"
    - "hermes_cli/cli_commands_mixin.py"
    - "cli.py"
decisions:
  - "Stored _handle_feedback_command in hermes_cli/cli_commands_mixin.py alongside _handle_voice_command/_handle_busy_command rather than directly in cli.py — the mixin is where HermesCLI's slash-command handlers actually live (cli.py just dispatches via the canonical elif chain to self.method()). Matches established codebase pattern."
  - "Used stdlib os.scandir polling for the kais-aigc watcher (CONTEXT.md Claude's-discretion + RESEARCH Pattern 4). Portable across Linux/macOS/Windows/Termux. No new dependency. 1s default interval is fast enough for batch file-exchange. Watchdog-style cross-platform Observer abstraction deferred — zero MVP benefit."
  - "All-or-nothing batch import (CONTEXT.md D-INGEST-03 recommendation). On any line error, returns (0, errors) WITHOUT writing — preserves operator trust. Line-numbered errors with field-level Pydantic messages make debugging trivial."
  - "Anti-spoofing source override in watcher: raw['source'] = 'kais_aigc' FORCED regardless of JSON content. Prevents a crafted file in inbox-kais/ from polluting the 'cli' or 'manual' source provenance (T-28-07 mitigation)."
  - "Skill_id resolution via backward scan for _SKILL_INVOCATION_PREFIX marker + regex extract of quoted skill name. Verified format in agent/skill_commands.py:550-553. When no marker found, prints clear error and writes nothing — never silently defaults (Pitfall #4 mitigation)."
  - "Watch helper factored into _scan_once() returning ingested count, so tests can exercise a single pass without sleeping. watch_inbox_kais() is a thin wrapper that loops _scan_once + time.sleep."
metrics:
  duration: "~22 min"
  completed: "2026-06-24T06:14:00Z"
  tasks: 2
  files_created: 2
  files_modified: 6
  tests_added: 31
  commits: 2
---

# Phase 28 Plan 02: Feedback Sources — CLI + Watcher + JSONL Importer Summary

Wires the three operator-facing feedback ingestion paths (CLI `/feedback` slash command, kais-aigc file-exchange polling watcher, JSONL batch importer) onto Plan 01's Pydantic schema + atomic write primitive — all three emit the same `FeedbackRecord` contract, completing the core functional guarantee of v6.0 MVP.

## What Was Built

### agent/feedback_ingest.py (EXTENDED — Plan 01's write_feedback_record preserved)
- **`import_jsonl(file_path, *, dry_run=False) -> tuple[int, list[str]]`** — atomic all-or-nothing JSONL batch import. Reads the file as UTF-8 (Pitfall #1), skips blank + `#`-comment lines, parses each line as JSON, validates each as `FeedbackRecord` via Pydantic. If ANY line errors (JSON or Pydantic), returns `(0, errors)` WITHOUT writing anything (T-28-11 atomicity). Line-numbered errors with field-level messages. `dry_run=True` validates without writing.
- **`watch_inbox_kais(inbox_dir=None, *, interval=1.0, stop_event=None, max_iterations=None)`** — portable stdlib `os.scandir` polling watcher for the kais-aigc file-exchange inbox (INGEST-02). Honors `HERMES_FEEDBACK_INBOX_KAIS` env var override (CONTEXT.md specifics line 74). Auto-creates `processed-kais/` and `errors-kais/` sibling directories. Prints PID + inbox path on startup so the operator can locate/kill the process (Pitfall #6). Installs SIGINT/SIGTERM-to-stop_event handlers (wrapped in try/except for Windows + non-main-thread safety). Slices sleep into 0.1s chunks so stop_event responds quickly.
- **`_scan_once(inbox_dir, processed_dir, errors_dir, seen, pending) -> int`** — single-pass helper factored out of `watch_inbox_kais` so tests exercise it directly without sleeping. Implements the 2-poll stability check (Pitfall #2 — record size, skip until size unchanged on next poll), the anti-spoofing `raw["source"] = "kais_aigc"` override (T-28-07), the path-traversal-safe rename via `Path(entry.name).name` (T-28-06), and the per-file try/except that moves malformed files to `errors-kais/` without crashing the scan loop (T-28-08).
- **`_resolve_kais_inbox()`** + **`_move_to_errors()`** — internal helpers.

### hermes_cli/feedback.py (NEW — subcommand dispatcher)
- **`register_cli(parent)`** — mirrors `hermes_cli/curator.py:495-603` line-for-line in style. Builds three subparsers:
  - `import <file.jsonl> [--dry-run]` — wraps `agent.feedback_ingest.import_jsonl`; prints errors to stderr with nonzero exit on failure.
  - `watch [--interval N]` — wraps `watch_inbox_kais`; constructs stop_event, lets the watcher install its own SIGINT/SIGTERM handlers.
  - `submit <skill_id> <verdict> [--correction "..."] [--revised "..."] [--output-text "..." (required)] [--prompt-text "..."] [--model "..."] [--provider "..."]` — scripting-friendly single-record ingest with `source="manual"`. Computes sha256 from `--output-text` (surrogatepass encoding for byte-stability — Plan 01 contract).
- **`_cmd_import(args) -> int`**, **`_cmd_watch(args) -> int`**, **`_cmd_submit(args) -> int`** — the three handler functions. All catch specific exceptions (`ValidationError`, `OSError`, `FileNotFoundError`) and print field-level errors with nonzero exit. `_cmd_submit` catches `ValidationError` and lists every field-level error.

### hermes_cli/main.py (+14 lines — wiring)
- Inserts `feedback_parser = subparsers.add_parser("feedback", ...)` + `from hermes_cli.feedback import register_cli as _register_feedback_cli; _register_feedback_cli(feedback_parser)` immediately after the curator block. Matches the existing 2-line style. Wrapped in try/except matching the curator block (debug log on failure, never crashes main).

### hermes_cli/commands.py (+2 lines — registry)
- Adds `CommandDef("feedback", "Submit feedback on the most recent movie-expert output", "Tools & Skills", cli_only=True, args_hint="<good|needs_work|bad> [correction]")` next to `curator`. `cli_only=True` because the slash command reads live `self.conversation_history` + `self.agent` — gateway platforms don't have REPL state. `resolve_command("feedback")` now returns the entry.

### cli.py (+1 line — dispatch)
- Inserts `elif canonical == "feedback": self._handle_feedback_command(cmd_original)` into the `process_command()` if/elif chain, between `busy` and the catch-all `else`.

### hermes_cli/cli_commands_mixin.py (+138 lines — handler)
- **`HermesCLI._handle_feedback_command(self, cmd_original) -> None`** — the slash-command handler implementing INGEST-01. Pipeline:
  1. Parse tail into `verdict` + `correction` + optional `--revised` (manual split).
  2. Validate `verdict ∈ {good, needs_work, bad}`; on mismatch, print the 3 valid values + usage and return.
  3. Validate REPL state: `self.agent` + `self.conversation_history` must be present and non-empty.
  4. Scan backward for the most recent assistant message; if none, clear error.
  5. Resolve `skill_id` by scanning backward for the most recent user message whose content starts with `_SKILL_INVOCATION_PREFIX`, then regex-extract the quoted skill name (format verified against `agent/skill_commands.py:550-553`). If no marker found, print "No movie-expert skill output found in this conversation..." and return (Pitfall #4 mitigation — never silently default).
  6. Call Plan 01's `build_output_snapshot(agent, conversation_history, assistant_idx)`, construct `FeedbackRecord(source="cli", ...)`, call `write_feedback_record(record)`, print confirmation with the written path.
  7. Catch `ValidationError` and print field-level errors. Catch broad `Exception` so the REPL never crashes from `/feedback`.

### Test Suites (31 new tests, all green)
- **tests/agent/test_feedback_ingest.py** (+14 tests) — `TestImportJsonl` (7): all-valid, atomic-reject (verdict + skill), dry-run, blank+comment skip, cold-start-10, malformed-JSON. `TestWatchInboxKais` (7): ingests-new-file, waits-for-stable-size, rejects-path-traversal, continues-on-malformed, max_iterations=0, stop_event, env-var override.
- **tests/hermes_cli/test_feedback_cli.py** (NEW, 17 tests) — `TestRegisterCli` (2): subcommands present + default func. `TestCmdImport` (3): valid + invalid + dry-run. `TestCmdWatch` (1): invokes watch_inbox_kais. `TestCmdSubmit` (1): writes a manual record. `TestSlashFeedback` (6): persists, no-skill-output, unknown-verdict, skill-id-resolution, usage-no-args, no-prior-skill-output. `TestCommandRegistry` (2): feedback entry present + resolvable. `TestProcessCommandWiring` (2): canonical branch present + method defined.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — Critical functionality] `_handle_feedback_command` placement**
- **Found during:** Task 2 implementation
- **Issue:** The plan suggested adding `_handle_feedback_command` directly on the HermesCLI class in `cli.py`. But HermesCLI's actual slash-command handlers live in the mixin at `hermes_cli/cli_commands_mixin.py` (where `_handle_voice_command`, `_handle_busy_command`, `_handle_skin_command`, etc. all live). The `cli.py` file only contains `process_command()` which dispatches via the elif chain to `self.method()` — the method lookup resolves through the MRO to the mixin.
- **Fix:** Added `_handle_feedback_command` to `hermes_cli/cli_commands_mixin.py` instead of `cli.py` body. Zero behavioral change — the method is still accessible as `HermesCLI._handle_feedback_command` via inheritance, and the `process_command()` elif branch in `cli.py` finds it via normal attribute lookup. Verified by the test `test_handle_feedback_command_method_present` (`hasattr(HermesCLI, "_handle_feedback_command")` → True).
- **Files modified:** hermes_cli/cli_commands_mixin.py (instead of cli.py body)
- **Commit:** 11737fd0c

**2. [Rule 2 — Critical functionality] `_cmd_watch` uses a `threading.Event` created locally**
- **Found during:** Task 2 implementation
- **Issue:** The plan suggested the watcher installs its own SIGINT/SIGTERM handlers. But when `stop_event=None` is passed, `watch_inbox_kais` creates a fresh event AND installs the handlers (matching the plan). When `stop_event` is provided (as in `_cmd_watch`), the handlers are NOT installed — so the operator's Ctrl+C would not set the event.
- **Fix:** `_cmd_watch` constructs a fresh `threading.Event` and passes it as `stop_event=stop_event` BUT the watcher's signal-handler installation is gated on `stop_event is None`. To preserve the clean Ctrl+C behavior, `_cmd_watch` catches `KeyboardInterrupt` itself and sets the event. The watcher loop sees `stop_event.is_set()` on its next iteration and exits cleanly. Best of both worlds: tests can inject a stop_event; the CLI handler still responds to Ctrl+C.
- **Files modified:** hermes_cli/feedback.py
- **Commit:** 11737fd0c

None of these deviations changed the plan's stated behavior or acceptance criteria — they were implementation-detail adjustments to fit the actual codebase structure (which the RESEARCH correctly anticipated but couldn't fully specify pre-execution).

## Auth Gates

None — this plan touches no authenticated services.

## Known Stubs

None — all three ingest sources are fully implemented end-to-end. `/feedback` resolves skill_id from real conversation state, captures a real `OutputSnapshot`, writes a real `FeedbackRecord`. `hermes feedback watch` polls the real inbox directory with 2-poll stability. `hermes feedback import` does real atomic all-or-nothing Pydantic-validated batch writes.

## Threat Flags

None — all files in this plan are covered by the plan's `<threat_model>`. The watcher mitigations are exercised by tests:
- T-28-06 path traversal → `test_watch_inbox_rejects_path_traversal` (verifies no file escapes the incoming/ tree)
- T-28-07 source spoofing → `test_watch_inbox_ingests_new_file` asserts the written file matches `*_kais_aigc_*.json` pattern regardless of the JSON's declared source
- T-28-08 malformed JSON resilience → `test_watch_inbox_continues_on_malformed` (malformed moved to errors/, subsequent valid file still ingested)
- T-28-09 partial-write detection → `test_watch_inbox_waits_for_stable_size` (no ingest on first or second scan when size changes)
- T-28-10 watcher orphan → SIGINT/SIGTERM handler installed in `watch_inbox_kais` when stop_event is None; PID printed on startup
- T-28-11 JSONL atomic → `test_import_jsonl_atomic_reject` (zero files written on any error)
- T-28-14 conversation_history mutation → `_handle_feedback_command` only READS `self.conversation_history`; `build_output_snapshot` and `_extract_text` do not mutate input (Plan 01 invariant, carried here)

## Verification Results

| Check | Result |
|-------|--------|
| `pytest tests/agent/test_feedback_schema.py tests/agent/test_feedback_snapshot.py tests/agent/test_feedback_ingest.py tests/hermes_cli/test_feedback_cli.py -x` | 76 passed in 1.52s (45 Plan 01 + 14 Task 1 + 17 Task 2) |
| `from hermes_cli.feedback import register_cli; ...; register_cli(p)` prints `ok` | PASS |
| `from hermes_cli.commands import COMMAND_REGISTRY; any(c.name == 'feedback' for c in COMMAND_REGISTRY)` prints `ok` | PASS |
| `grep -c 'canonical == "feedback"' cli.py` | 1 |
| Cold-start: `import_jsonl(Path("tests/fixtures/feedback/valid_10.jsonl"), dry_run=True)` | `(10, [])` |
| Atomic reject: `import_jsonl(Path("tests/fixtures/feedback/invalid_verdict.jsonl"), dry_run=True)` | count=0, errors mention line 2 + verdict |
| Cross-source parity: `pytest test_source_enum_same_schema -x` | PASS (Plan 01 test, still green) |
| `ruff check agent/feedback_schema.py agent/feedback_snapshot.py agent/feedback_ingest.py hermes_cli/feedback.py` | All checks passed |
| FOUND-08: `git diff --name-only v5.0 -- skills/movie-experts/ \| grep -v _eval \| grep -v _shared \| wc -l` | 0 |
| No new deps: `git status --short pyproject.toml uv.lock` (this plan's working tree) | empty (no changes) |

## Self-Check: PASSED

**Files verified to exist:**
- FOUND: hermes_cli/feedback.py
- FOUND: tests/hermes_cli/test_feedback_cli.py
- FOUND (modified): agent/feedback_ingest.py
- FOUND (modified): tests/agent/test_feedback_ingest.py
- FOUND (modified): hermes_cli/main.py
- FOUND (modified): hermes_cli/commands.py
- FOUND (modified): hermes_cli/cli_commands_mixin.py
- FOUND (modified): cli.py

**Commits verified to exist:**
- FOUND: 92f32917d (Task 1 — import_jsonl + watch_inbox_kais + _scan_once)
- FOUND: 11737fd0c (Task 2 — /feedback slash command + hermes feedback subcommand)
