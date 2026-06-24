---
phase: 28-feedback-ingestion-mvp
verified: 2026-06-24T16:05:00Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: n/a
  gaps_closed: []
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Live REPL smoke test of /feedback slash command"
    expected: "Inside an actual `hermes` REPL conversation, after invoking a movie-expert skill (e.g. /screenplay), type `/feedback good nice work` and observe (a) a confirmation message naming the written file path and (b) a JSON file appear under ~/.hermes/skills/.feedback/incoming/ with source=cli, verdict=good, correction='nice work', and a populated output_snapshot containing the real assistant output's sha256."
    why_human: "The slash-command handler reads live REPL state (self.agent + self.conversation_history) that cannot be faithfully reproduced outside an interactive session. The unit test test_slash_feedback_persists covers the logic with a stub, but the end-to-end live-REPL path (real AIAgent instance, real conversation_history, real skill-invocation marker injected by the skill loader) can only be exercised by a human typing into the REPL."
---

# Phase 28: Feedback Ingestion MVP — Verification Report

**Phase Goal:** Users (CLI operators + kais-aigc-platform审核系统 + 手工标注者) can submit structured feedback against any movie-expert output, and all feedback lands in a single normalized schema ready for downstream storage and learning.
**Verified:** 2026-06-24T16:05:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| #   | Truth (SC) | Status | Evidence |
| --- | ---------- | ------ | -------- |
| SC-1 | Operator can submit feedback inside a Hermes CLI conversation against any movie-expert output — verdict + free-text correction + optional revised output accepted and persisted to disk | ✓ VERIFIED | `hermes_cli/cli_commands_mixin.py:2295 _handle_feedback_command` reads `self.conversation_history`, scans backward for assistant message, resolves `skill_id` via `_SKILL_INVOCATION_PREFIX` regex, calls `build_output_snapshot`, constructs `FeedbackRecord(source="cli")`, calls `write_feedback_record`. Wired via `cli.py:7705 elif canonical == "feedback"` + `hermes_cli/commands.py:190 CommandDef("feedback", ...)`. Test `test_slash_feedback_persists` PASSES (17/17 CLI tests green). |
| SC-2 | kais-aigc-platform review feedback is ingestible via file exchange | ✓ VERIFIED | `agent/feedback_ingest.py:378 watch_inbox_kais` + `:189 _scan_once` implement portable `os.scandir` polling. Anti-spoofing `raw["source"] = "kais_aigc"` override at `:270`. 2-poll stability check at `:262`. Path-traversal defense via `Path(entry.name).name` at `:275`. Symlink rejection at `:239` (WR-03). `HERMES_FEEDBACK_INBOX_KAIS` env override at `:183`. `TestWatchInboxKais` — 7 tests PASS. |
| SC-3 | Manual-labeling CLI subcommand supports batch import of historical outputs + labels (cold-start on ≥10 sample outputs) | ✓ VERIFIED | `agent/feedback_ingest.py:110 import_jsonl` — atomic all-or-nothing (parses+validates ALL lines before ANY write). `hermes_cli/feedback.py:122 _cmd_import` wraps it. `tests/fixtures/feedback/valid_10.jsonl` has exactly 10 records. `test_import_jsonl_cold_start_10` PASSES. Cold-start smoke: `import_jsonl(valid_10.jsonl, dry_run=True)` returns `(10, [])`. Atomic reject: `import_jsonl(invalid_verdict.jsonl)` returns `count=0` with line-2 + verdict error. |
| SC-4 | All three sources emit the SAME JSON schema — schema validation rejects malformed payloads with clear error | ✓ VERIFIED | `agent/feedback_schema.py:184 FeedbackRecord` with `Literal["cli","kais_aigc","manual"]` source + 3 field validators (`_known_expert`, `_ts_has_tz`, `_sha256_is_64_hex`). `test_source_enum_same_schema` PASSES — asserts model_dump differs ONLY in source field across the 3 enum values. All three ingestion paths construct `FeedbackRecord` and converge on `write_feedback_record`. |
| SC-5 | Every feedback record carries `output_snapshot` with sha256 + prompt + model + params metadata | ✓ VERIFIED | `agent/feedback_snapshot.py:128 build_output_snapshot` captures sha256 (deterministic via `output_text.encode("utf-8", errors="surrogatepass")` at `:167`), prompt (backward scan for user message), model/provider/api_mode (via `getattr`), and params iterating `("max_tokens", "reasoning_config", "service_tier", "request_overrides")` at `:175` with `_safe_param` + `_filter_serializable` JSON-safety filtering (CR-01 fix). `test_sha256_deterministic` + `test_captures_agent_params` + `test_drops_non_serializable_request_overrides` PASS. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `agent/feedback_schema.py` | FeedbackRecord + OutputSnapshot + _KNOWN_EXPERT_IDS + validators | ✓ VERIFIED | 228 lines. `class FeedbackRecord` + `class OutputSnapshot` + 3 `field_validator` decorators + `_discover_expert_ids` (def + call site). Auto-discovered 31 experts (≥28 required); includes v3/v4/v5 additions (hook_retention, cinematographer, compliance_gate, lip_sync). |
| `agent/feedback_snapshot.py` | `build_output_snapshot` + `_extract_text` + sha256 determinism | ✓ VERIFIED | 207 lines. `def build_output_snapshot` + `def _extract_text` + `hashlib.sha256` + `_safe_param` (CR-01) + `_filter_serializable`. |
| `agent/feedback_ingest.py` | `write_feedback_record` + `import_jsonl` + `watch_inbox_kais` + `_scan_once` | ✓ VERIFIED | 463 lines. All 4 functions present. `atomic_json_write` + `get_hermes_home` imported and used. `source="kais_aigc"` override present. `HERMES_FEEDBACK_INBOX_KAIS` honored. Zero `Path.home()` usage. |
| `hermes_cli/feedback.py` | `register_cli` + `_cmd_import` + `_cmd_watch` + `_cmd_submit` | ✓ VERIFIED | 238 lines. All 4 functions present. `register_cli` builds import/watch/submit subparsers. |
| `hermes_cli/main.py` | feedback_parser + register_cli wiring | ✓ WIRED | `:11981 feedback_parser = subparsers.add_parser("feedback", ...)` + `:11993 from hermes_cli.feedback import register_cli` + `:11995 _register_feedback_cli(feedback_parser)`. Wrapped in try/except (never crashes main). |
| `hermes_cli/commands.py` | CommandDef entry for /feedback | ✓ WIRED | `:190 CommandDef("feedback", "Submit feedback on the most recent movie-expert output", ...)` present in COMMAND_REGISTRY. |
| `cli.py` | `_handle_feedback_command` dispatch branch | ✓ WIRED | `:7705 elif canonical == "feedback": self._handle_feedback_command(cmd_original)`. Method resolved via MRO to `hermes_cli/cli_commands_mixin.py:2295`. |
| `hermes_cli/cli_commands_mixin.py` | `_handle_feedback_command` method body | ✓ VERIFIED | 138-line method at `:2295`. Full pipeline: verdict parse → conversation_history scan → skill_id resolution via `_SKILL_INVOCATION_PREFIX` regex → `build_output_snapshot` → `FeedbackRecord(source="cli")` → `write_feedback_record`. Uses `shlex.split` for `--revised` flag (WR-02 fix). Catches `ValidationError` + broad `Exception` (REPL never crashes). |
| `tests/agent/test_feedback_schema.py` | 13 schema tests | ✓ VERIFIED | 197 lines, 13 tests PASS. |
| `tests/agent/test_feedback_snapshot.py` | 13 snapshot tests | ✓ VERIFIED | 227 lines, 13 tests PASS. |
| `tests/agent/test_feedback_ingest.py` | write + import + watch tests | ✓ VERIFIED | 631 lines, 33 tests PASS (TestWriteFeedbackRecord + TestImportJsonl + TestWatchInboxKais). |
| `tests/hermes_cli/test_feedback_cli.py` | CLI + slash-command tests | ✓ VERIFIED | 497 lines, 17 tests PASS (TestRegisterCli + TestCmdImport + TestCmdWatch + TestCmdSubmit + TestSlashFeedback + TestCommandRegistry + TestProcessCommandWiring). |
| `tests/fixtures/feedback/valid_10.jsonl` | 10 valid records (cold-start) | ✓ VERIFIED | 10 lines, all valid JSON, validates as FeedbackRecord. |
| `tests/fixtures/feedback/invalid_verdict.jsonl` | 3 lines, line 2 invalid verdict | ✓ VERIFIED | 3 lines; atomic-reject verified. |
| `tests/fixtures/feedback/invalid_skill.jsonl` | 3 lines, line 2 invalid skill_id | ✓ VERIFIED | 3 lines; atomic-reject verified. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `hermes_cli/main.py` | `hermes_cli/feedback.py` | `register_cli` call | ✓ WIRED | `:11993 from hermes_cli.feedback import register_cli as _register_feedback_cli` + `:11995 _register_feedback_cli(feedback_parser)`. |
| `cli.py process_command` | `cli.py _handle_feedback_command` | `elif canonical == feedback` | ✓ WIRED | `:7705` branch present; method resolves via MRO to mixin. |
| `cli.py _handle_feedback_command` | `agent/feedback_snapshot.build_output_snapshot` | snapshot capture | ✓ WIRED | `cli_commands_mixin.py:1320 snapshot = build_output_snapshot(agent=self.agent, ...)`. |
| `hermes_cli/feedback.py _cmd_import` | `agent/feedback_ingest.import_jsonl` | batch import | ✓ WIRED | `:124 from agent.feedback_ingest import import_jsonl` + `:132 import_jsonl(file_path, dry_run=...)`. |
| `hermes_cli/feedback.py _cmd_watch` | `agent/feedback_ingest.watch_inbox_kais` | watcher loop | ✓ WIRED | `:164 from agent.feedback_ingest import watch_inbox_kais` + `:170 watch_inbox_kais(interval=args.interval)`. |
| `agent/feedback_ingest.import_jsonl` | `agent/feedback_ingest.write_feedback_record` | single write path | ✓ WIRED | `:167 write_feedback_record(record)` inside the post-validation loop. |
| `agent/feedback_snapshot.py` | `agent/feedback_schema.py` | imports OutputSnapshot | ✓ WIRED | `:33 from agent.feedback_schema import OutputSnapshot`. |
| `agent/feedback_ingest.py` | `agent/feedback_schema.py` | imports FeedbackRecord | ✓ WIRED | `:44 from agent.feedback_schema import FeedbackRecord`. |
| `agent/feedback_ingest.py` | `utils.atomic_json_write` | atomic persistence | ✓ WIRED | `:46 from utils import atomic_json_write` + `:90 atomic_json_write(target, ...)`. |
| `agent/feedback_ingest.py` | `hermes_constants.get_hermes_home` | path resolution | ✓ WIRED | `:45 from hermes_constants import get_hermes_home` + `:82 get_hermes_home() / "skills" / ".feedback" / "incoming"`. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `_handle_feedback_command` | `conversation_history` | `self.conversation_history` (live REPL state) | Yes — real assistant/user messages | ✓ FLOWING |
| `_handle_feedback_command` | `skill_id` | regex extraction from `_SKILL_INVOCATION_PREFIX` marker in prior user message | Yes — verified format from `skill_commands.py:550-553` | ✓ FLOWING |
| `build_output_snapshot` | `output_text` | `_extract_text(assistant_msg["content"])` from real conversation | Yes — handles str/list/None shapes | ✓ FLOWING |
| `build_output_snapshot` | `params` | `getattr(agent, attr)` for 4 param attrs | Yes — real agent attributes; non-serializable filtered (CR-01) | ✓ FLOWING |
| `write_feedback_record` | `record` | FeedbackRecord constructed upstream | Yes — validated Pydantic model | ✓ FLOWING |
| `import_jsonl` | `records` | `FeedbackRecord(**json.loads(line))` per JSONL line | Yes — real fixture data (10 valid records) | ✓ FLOWING |
| `watch_inbox_kais._scan_once` | `record` | `FeedbackRecord(**raw)` from inbox file with source override | Yes — anti-spoofing forced source | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| All 76 feedback tests pass | `.venv/bin/python -m pytest tests/agent/test_feedback_schema.py tests/agent/test_feedback_snapshot.py tests/agent/test_feedback_ingest.py tests/hermes_cli/test_feedback_cli.py` | 76 passed in 1.41s | ✓ PASS |
| SC-1 slash command persists | `pytest tests/hermes_cli/test_feedback_cli.py::TestSlashFeedback::test_slash_feedback_persists -x` | 1 passed | ✓ PASS |
| SC-2 watcher ingests | `pytest tests/agent/test_feedback_ingest.py::TestWatchInboxKais -x` | 7 passed | ✓ PASS |
| SC-3 cold-start 10 records | `pytest tests/agent/test_feedback_ingest.py::TestImportJsonl::test_import_jsonl_cold_start_10 -x` | 1 passed | ✓ PASS |
| SC-4 cross-source parity | `pytest tests/agent/test_feedback_schema.py::TestFeedbackRecordSchema::test_source_enum_same_schema -x` | 1 passed | ✓ PASS |
| Cold-start smoke (dry-run) | `python -c "...import_jsonl(valid_10.jsonl, dry_run=True)"` | `(10, [])` | ✓ PASS |
| Atomic reject smoke | `python -c "...import_jsonl(invalid_verdict.jsonl, dry_run=True)"` | `count=0, errors=1`, mentions line 2 + verdict | ✓ PASS |
| Auto-discovery count | `python -c "..._KNOWN_EXPERT_IDS; print(len(...))"` | 31 experts (≥28 required) | ✓ PASS |
| `hermes feedback --help` lists subcommands | `cli_main(['--help'])` | Lists `import`, `watch`, `submit` | ✓ PASS |
| Ruff PLW1514 on new modules | `.venv/bin/ruff check agent/feedback_*.py hermes_cli/feedback.py` | All checks passed | ✓ PASS |
| FOUND-08 byte-intact | `git diff --name-only v5.0 -- skills/movie-experts/ \| grep -v _eval \| grep -v _shared \| wc -l` | 0 | ✓ PASS |

### Probe Execution

No conventional `scripts/*/tests/probe-*.sh` probes declared for this phase. Phase 28 verification relies on the pytest suite + behavioral spot-checks above.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| INGEST-01 | 28-02 | CLI in-conversation feedback submission | ✓ SATISFIED | `/feedback` slash command in `cli_commands_mixin.py:2295`; verdict + correction + optional `--revised` accepted; persists via `write_feedback_record`. Test `test_slash_feedback_persists` + 5 sibling tests PASS. |
| INGEST-02 | 28-02 | kais-aigc-platform接入 (file exchange chosen at plan-phase) | ✓ SATISFIED | File-exchange transport chosen per CONTEXT.md D-INGEST-02. `watch_inbox_kais` + `_scan_once` in `feedback_ingest.py`. 7 TestWatchInboxKais tests PASS covering ingest, stability, path-traversal, malformed-resilience, env override. |
| INGEST-03 | 28-01 + 28-02 | Single normalized JSON schema across all sources | ✓ SATISFIED | `FeedbackRecord` Pydantic model is the single contract. `test_source_enum_same_schema` verifies 3 sources differ only in `source` field. All three paths converge on `write_feedback_record`. JSONL batch importer validates each line against the same schema. |
| INGEST-04 | 28-01 | output_snapshot with sha256 + prompt/model/params metadata | ✓ SATISFIED | `OutputSnapshot` model with `sha256` (64-hex validator), `output_text`, `prompt`, `model`, `provider`, `api_mode`, `params` (max_tokens + reasoning_config + service_tier + request_overrides, JSON-filtered per CR-01). `build_output_snapshot` captures all fields deterministically. |
| INGEST-05 | 28-02 | Manual labeling CLI subcommand for cold-start | ✓ SATISFIED | `hermes feedback import <file.jsonl>` (atomic all-or-nothing) + `hermes feedback submit` (single-record scripting). Cold-start verified on `valid_10.jsonl` (10 records). |

**Orphaned requirements:** None. All 5 INGEST requirements mapped to Phase 28 in REQUIREMENTS.md are claimed by Plan 01 and/or Plan 02 and have implementation evidence.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | — | — | — | No TBD/FIXME/XXX, no TODO/HACK/PLACEHOLDER, no empty implementations, no `Path.home()` usage, no console.log-only handlers found in any of the 4 new modules or 4 modified wiring files. |

### Code Review Fixes (CR-01 + WR-01 through WR-06)

All 7 in-scope review findings are fixed with commits verified to exist in git history:

| Finding | Commit | Verified in Code |
| ------- | ------ | --------------- |
| CR-01 (non-serializable params crash) | `29d2f155b` | `_safe_param` helper at `feedback_snapshot.py:44`; applied to all 4 agent params |
| WR-01 (orphaned source on unlink fail) | `6d05c00f4` | Relocate-to-errors-with-.unlink-failed-suffix branch at `feedback_ingest.py:302-322` |
| WR-02 (--revised flag collision) | `0b436ee5c` | `shlex.split(tail)` tokenization at `cli_commands_mixin.py:431` |
| WR-03 (symlinks followed) | `32a03694b` | `entry.is_symlink()` guard at `feedback_ingest.py:239` |
| WR-04 (dead validator branch) | `d5274894a` | `isinstance` branch removed from `_sha256_is_64_hex` at `feedback_schema.py:168-178` |
| WR-05 (double signal-handler install) | `e9e60d01e` | `_cmd_watch` no longer passes `stop_event=` (lets watcher install own handlers) |
| WR-06 (UnicodeDecodeError shadowed) | `d22724e33` | Explicit `except UnicodeDecodeError` branch at `feedback_ingest.py:328` |

### FOUND-08 Preservation

- **Check:** `git diff --name-only v5.0 -- skills/movie-experts/ | grep -v _eval | grep -v _shared | wc -l`
- **Result:** `0`
- **Status:** ✓ PASS — zero bundled SKILL.md or `references/*.md` bytes modified across Phase 28.

### Dependency Discipline

- `git diff --name-only v5.0 -- pyproject.toml uv.lock` returns 2 files, BUT the diffs are from earlier v6.0 baseline work (`python-multipart` for NS-501 dashboard, `concurrent-log-handler` for Windows log rotation #44873) — NOT introduced by Phase 28.
- Phase 28 added zero new dependencies (pydantic 2.13.4 was already pinned). ✓ PASS.

### Human Verification Required

### 1. Live REPL smoke test of /feedback slash command

**Test:** Inside an actual `hermes` REPL conversation, invoke a movie-expert skill (e.g. `/screenplay` with a prompt), then type `/feedback good nice work` and observe the output. Also test the negative paths: `/feedback` with no prior skill output, `/feedback excellent` (unknown verdict), and `/feedback bad "wrong" --revised "fixed text"`.
**Expected:** (a) A confirmation message naming the written file path under `~/.hermes/skills/.feedback/incoming/`. (b) The JSON file contains `source=cli`, `verdict=good`, `correction='nice work'`, and a populated `output_snapshot` with the real assistant output's sha256, the real prompt, the real model name, and real params. (c) Negative paths print clear errors and write nothing.
**Why human:** The slash-command handler reads live REPL state (`self.agent` + `self.conversation_history`) that cannot be faithfully reproduced outside an interactive session. The unit test `test_slash_feedback_persists` covers the logic with a stub agent + stub conversation, but the end-to-end live-REPL path (real `AIAgent` instance, real conversation_history populated by the conversation loop, real `_SKILL_INVOCATION_PREFIX` marker injected by the skill loader) can only be exercised by a human typing into the REPL. This is the single source of truth for "INGEST-01 actually works for users."

### Gaps Summary

No gaps found. All 5 observable truths (SC-1 through SC-5) are VERIFIED with codebase evidence. All 15 required artifacts exist, are substantive (no stubs), and are wired. All 10 key links are connected. Data-flow trace confirms real data flows through every dynamic-data path. All 5 INGEST requirements are satisfied with no orphans. All 76 tests pass. All 7 code-review findings are fixed with verified commits. FOUND-08 preserved. Zero new dependencies.

The single human-verification item (live REPL smoke test) is inherent to the slash-command delivery surface — it cannot be automated without a full REPL harness, and the unit tests already cover the handler logic with high fidelity. Status is `human_needed` (not `passed`) per the verifier decision tree: human verification items take priority over a clean automated score.

---

_Verified: 2026-06-24T16:05:00Z_
_Verifier: Claude (gsd-verifier)_
