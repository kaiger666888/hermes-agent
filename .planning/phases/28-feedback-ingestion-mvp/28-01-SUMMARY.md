---
phase: 28
plan: 01
subsystem: feedback-ingestion
tags: [feedback, pydantic, schema, snapshot, atomic-write, ingestion]
requires:
  - "utils.atomic_json_write (utils.py:111-153)"
  - "hermes_constants.get_hermes_home (hermes_constants.py:53)"
  - "agent.skill_utils.parse_frontmatter (agent/skill_utils.py:123)"
  - "pydantic==2.13.4 (pyproject.toml:60)"
provides:
  - "agent.feedback_schema.FeedbackRecord (Pydantic model, INGEST-04 contract)"
  - "agent.feedback_schema.OutputSnapshot (Pydantic model, INGEST-04 contract)"
  - "agent.feedback_schema._KNOWN_EXPERT_IDS (auto-discovered expert registry)"
  - "agent.feedback_snapshot.build_output_snapshot (INGEST-04 capture)"
  - "agent.feedback_snapshot._extract_text (content-shape defense)"
  - "agent.feedback_ingest.write_feedback_record (atomic write path, INGEST-01/02/03 foundation)"
  - "tests/fixtures/feedback/valid_10.jsonl (cold-start fixture for INGEST-05)"
  - "tests/fixtures/feedback/invalid_verdict.jsonl (atomic-reject fixture for INGEST-04)"
  - "tests/fixtures/feedback/invalid_skill.jsonl (atomic-reject fixture for INGEST-04)"
affects:
  - "Plan 28-02 (consumes FeedbackRecord + write_feedback_record for /feedback, watcher, JSONL importer)"
  - "Phase 29 STORE (consumes FeedbackRecord JSON shape for dedup/decay)"
  - "Phase 30 GATE (consumes OutputSnapshot.sha256 + params for ablation)"
tech-stack:
  added: []
  patterns:
    - "Pydantic v2 BaseModel + field_validator (INGEST-04 validation layer)"
    - "Atomic JSON write via utils.atomic_json_write (temp + fsync + os.replace)"
    - "Auto-discovery of expert IDs from skills/movie-experts/*/SKILL.md frontmatter with hardcoded fallback"
    - "sha256 canonical encoding path (output_text.encode utf-8 surrogatepass) for dedup contract"
    - "HERMES_HOME isolation in tests via monkeypatch + importlib.reload (curator_env pattern)"
key-files:
  created:
    - "agent/feedback_schema.py"
    - "agent/feedback_snapshot.py"
    - "agent/feedback_ingest.py"
    - "tests/agent/test_feedback_schema.py"
    - "tests/agent/test_feedback_snapshot.py"
    - "tests/agent/test_feedback_ingest.py"
    - "tests/fixtures/feedback/valid_10.jsonl"
    - "tests/fixtures/feedback/invalid_verdict.jsonl"
    - "tests/fixtures/feedback/invalid_skill.jsonl"
  modified: []
decisions:
  - "Auto-discover _KNOWN_EXPERT_IDS from skills/movie-experts/*/SKILL.md frontmatter at module load (RESEARCH open Q #4 resolved per CONTEXT.md D-04) — caught all 31 current experts including v3/v4/v5 additions; hardcoded fallback only activates outside the repo"
  - "sha256 encoding path uses errors='surrogatepass' for byte-stable hashing of lone surrogate code points — documented as the canonical dedup contract for P29/P30"
  - "Non-serializable request_overrides values (lambdas, custom objects) filtered to JSON primitives with debug log instead of crashing (RESEARCH Pitfall #8 mitigation)"
metrics:
  duration: "499s"
  completed: "2026-06-24T05:42:41Z"
  tasks: 3
  files_created: 9
  tests_added: 45
  commits: 3
---

# Phase 28 Plan 01: Feedback Schema + Snapshot + Atomic Write Summary

Pydantic FeedbackRecord + OutputSnapshot schema with field-level validators, deterministic sha256 snapshot capture from live conversation state, and atomic JSONL persistence — the shared contract layer for all three Plan 02 ingestion sources.

## What Was Built

### agent/feedback_schema.py
- **`FeedbackRecord(BaseModel)`** — the single schema all three sources (cli/kais_aigc/manual) emit. Fields: `skill_id`, `expert_id`, `source` (Literal), `verdict` (Literal), `correction`, `revised_output`, `output_snapshot`, `ts` (timezone-aware datetime).
- **`OutputSnapshot(BaseModel)`** — provenance for the LLM output: `sha256` (validated 64-char lowercase hex, normalizes uppercase), `output_text`, `prompt`, `model`, `provider`, `api_mode`, `params`, `captured_at`.
- **`_KNOWN_EXPERT_IDS`** — frozenset auto-discovered at import time by walking `skills/movie-experts/*/SKILL.md` YAML frontmatter via `agent.skill_utils.parse_frontmatter`. Discovered all **31 current experts** (including v3/v4/v5 additions: hook_retention, compliance_gate, lip_sync, cinematographer, etc.). Hardcoded fallback of the same 31 names activates only when discovery fails (running outside repo, parse error) and logs a warning.
- **Field validators** — `_known_expert` (skill_id + expert_id against `_KNOWN_EXPERT_IDS`), `_ts_has_tz` (rejects naive datetimes), `_sha256_is_64_hex` (rejects non-64-char or non-hex, normalizes to lowercase).

### agent/feedback_snapshot.py
- **`build_output_snapshot(agent, conversation_history, assistant_idx) -> OutputSnapshot`** — reads agent attrs via `getattr` (model/provider/api_mode/max_tokens/reasoning_config/service_tier/request_overrides), scans backward for the most recent user prompt, computes sha256 over `output_text.encode("utf-8", errors="surrogatepass")`.
- **`_extract_text(content)`** — handles str / list-of-dicts (Anthropic text blocks) / None / unknown shapes defensively, never mutates input.
- **`_filter_serializable`** + **`_is_json_serializable`** — recursively filters `request_overrides` to JSON-safe primitives (str/int/float/bool/None/list/dict), logs dropped keys at debug level. Prevents `TypeError` from lambdas/callables (RESEARCH Pitfall #8).

### agent/feedback_ingest.py
- **`write_feedback_record(record) -> Path`** — atomically writes under `<HERMES_HOME>/skills/.feedback/incoming/{skill_id}_{source}_{ts_compact}.json` where `ts_compact = record.ts.strftime("%Y%m%dT%H%M%S%fZ")`. Filename is sortable and collision-resistant (microsecond precision + source disambiguation). Uses `utils.atomic_json_write` (temp + fsync + os.replace — RESEARCH Pattern 3). Resolves paths via `get_hermes_home()` (CLAUDE.md mandate).

### Test Suites (45 tests total, all green)
- **tests/agent/test_feedback_schema.py** (13 tests) — accept/reject for every validated field, cross-source schema parity (INGEST-04), _KNOWN_EXPERT_IDS v3/v4/v5 coverage guard, optional-field defaults.
- **tests/agent/test_feedback_snapshot.py** (13 tests) — sha256 determinism + manual-hash equality, agent param capture, all content shapes, preceding-prompt discovery, non-serializable request_overrides filtering, missing-attr graceful default, Anthropic list-content handling.
- **tests/agent/test_feedback_ingest.py** (19 tests) — write path under HERMES_HOME, filename format, lazy directory creation, content equality, no-tmp-files-left, round-trip persistence, atomic-write source inspection, no-Path.home() check, get_hermes_home() check, POSIX unwritable-dir rejection, JSONL fixture validation (10 + 3 + 3 lines).

### JSONL Fixtures (3 files for Plan 02)
- **valid_10.jsonl** — 10 valid records varying skill_id (10 experts), source (cli/kais_aigc/manual), verdict (good/needs_work/bad). Cold-start fixture for INGEST-05.
- **invalid_verdict.jsonl** — 3 lines: valid / line 2 has `verdict="excellent"` (invalid enum) / valid. Each line JSON-parseable; only Pydantic validation rejects line 2.
- **invalid_skill.jsonl** — 3 lines: valid / line 2 has `skill_id="not_a_real_skill"` (unknown) / valid. Same atomic-reject pattern.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] atomic_json_write ensure_ascii collision**
- **Found during:** Task 3
- **Issue:** Initial `write_feedback_record` call passed `ensure_ascii=False` to `atomic_json_write`, but utils.py:156 already hardcodes `ensure_ascii=False` internally — passing it again via `**dump_kwargs` raised `TypeError: json.dump() got multiple values for keyword argument 'ensure_ascii'`.
- **Fix:** Removed the redundant `ensure_ascii=False` from my call site. Behavior is unchanged (utf-8 / non-ASCII preserved as before).
- **Files modified:** agent/feedback_ingest.py
- **Commit:** 1744a26f2

**2. [Rule 1 - Bug] Path.home() substring in module docstrings tripped source-inspection test**
- **Found during:** Task 3
- **Issue:** The `test_no_path_home_usage` test (required by the plan's acceptance criterion `grep -v '^ *#' ... | grep -c "Path.home"` returns 0) greps the entire source file, including docstring text. My module docstrings contained the literal string `Path.home()` in the CLAUDE.md convention reminder ("NEVER Path.home()"), which the grep caught even though no actual `Path.home()` call existed.
- **Fix:** Rephrased the docstring reminder to "never the raw home-dir call" instead of quoting the forbidden API literally. Zero behavioral change.
- **Files modified:** agent/feedback_ingest.py
- **Commit:** 1744a26f2

**3. [Rule 1 - Bug] test_correction_defaults_empty initially passed correction=None**
- **Found during:** Task 1 RED phase
- **Issue:** The original test passed `correction=None` to a field typed `str` with default `""`, expecting either acceptance or graceful handling. Pydantic correctly rejected `None` (`Input should be a valid string`), which obscured the test's actual intent (verify that OMITTING correction yields `""`).
- **Fix:** Removed the `correction=None` assertion line; the test now constructs a record without the `correction` kwarg and asserts `record.correction == ""`.
- **Files modified:** tests/agent/test_feedback_schema.py
- **Commit:** f4179e152

## Auth Gates

None — this plan touches no authenticated services.

## Known Stubs

None — all three modules are fully implemented. `write_feedback_record` is the only public write path; Plan 02's `watch_inbox_kais()` and `import_jsonl()` will be added to `agent/feedback_ingest.py` but are explicitly out of Plan 01 scope (the plan's files_modified list does not include them, and the plan objective states "Plan 02 = sources that produce records").

## Threat Flags

None — all files in this plan are covered by the plan's `<threat_model>`. The `_discover_expert_ids` auto-discovery (T-28-02) is mitigated by reading only in-repo trusted SKILL.md files via the hardened `parse_frontmatter`, with hardcoded fallback (T-28-05). The sha256 field validator (T-28-01) enforces 64-char hex before persistence. No new threat surface beyond what the plan anticipated.

## Verification Results

| Check | Result |
|-------|--------|
| Schema tests (`pytest tests/agent/test_feedback_schema.py -x`) | 13 passed in 0.42s |
| Snapshot tests (`pytest tests/agent/test_feedback_snapshot.py -x`) | 13 passed in 0.35s |
| Ingest tests (`pytest tests/agent/test_feedback_ingest.py -x`) | 19 passed in 0.47s |
| Auto-discovery sanity (`_KNOWN_EXPERT_IDS` count) | 31 experts discovered (>= 28 required) |
| FOUND-08 byte-intact (`git diff v5.0 -- skills/movie-experts/` minus _eval/_shared) | PASS — no bundled SKILL.md or references touched |
| Ruff PLW1514 (no `open()` without encoding in new modules) | PASS — zero actual `open()` calls in agent/feedback_*.py (only docstring mentions) |
| Round-trip persistence | Covered by `test_round_trip_jsonl_compat` |

## Self-Check: PASSED

**Files verified to exist:**
- FOUND: agent/feedback_schema.py
- FOUND: agent/feedback_snapshot.py
- FOUND: agent/feedback_ingest.py
- FOUND: tests/agent/test_feedback_schema.py
- FOUND: tests/agent/test_feedback_snapshot.py
- FOUND: tests/agent/test_feedback_ingest.py
- FOUND: tests/fixtures/feedback/valid_10.jsonl
- FOUND: tests/fixtures/feedback/invalid_verdict.jsonl
- FOUND: tests/fixtures/feedback/invalid_skill.jsonl

**Commits verified to exist:**
- FOUND: f4179e152 (Task 1)
- FOUND: 10fe966f4 (Task 2)
- FOUND: 1744a26f2 (Task 3)
