# Phase 28: Feedback Ingestion MVP - Context

**Gathered:** 2026-06-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Users (CLI operators + kais-aigc-platform审核系统 + 手工标注者) can submit structured feedback against any movie-expert output, and all feedback lands in a single normalized schema (`skill_id, expert_id, source, verdict, correction, output_snapshot, ts`) ready for downstream storage (P29) and learning (P31).

Covers requirements INGEST-01..05. Ships the core functional guarantee of v6.0 — the must-have MVP. Hermes-core touch: Yes (new feedback-ingestion entrypoints / CLI subcommands / file watcher under `~/.hermes/skills/.feedback/` ingest path).

</domain>

<decisions>
## Implementation Decisions

### Kais-aigc-platform Transport (INGEST-02)
- **File exchange** — kais-aigc-platform writes JSON files to `~/.hermes/skills/.feedback/inbox-kais/`; Hermes watches this directory and ingests new files. Simplest, no network surface, default per ROADMAP risk note ("If plan-phase cannot decide, default to file-exchange"). Operator can also drop files manually for testing.
- HTTP endpoint and webhook transports are explicitly DEFERRED — not in P28 scope. If operator needs them later, they layer on top of the same `FeedbackRecord` schema.

### CLI Feedback UX (INGEST-01)
- **Slash command `/feedback`** — operator types `/feedback <verdict> [correction]` against the most recent movie-expert output. Verdict ∈ {`good`, `needs_work`, `bad`}; correction is free-text; optional revised output via `/feedback <verdict> --revised "<text>"`.
- `output_snapshot` auto-captured from current conversation state (most recent assistant message) — no operator action needed.
- Natural-language trigger and inline post-output prompts are REJECTED (non-deterministic / high friction).

### Manual Batch Import Format (INGEST-03)
- **JSONL** — one feedback record per line, identical schema to live feedback. CLI: `hermes feedback import <file.jsonl>`.
- Auto-detect `skill_id` from snapshot path when possible; validate all records before any are written (atomic batch).
- CSV and YAML rejected — CSV loses nested `output_snapshot`; YAML too slow for batches.

### Schema Validation (INGEST-04)
- **Pydantic `FeedbackRecord` model** with field validators. Already in stack (`==2.13.4` per `pyproject.toml`).
- Rejects malformed payloads with field-level error messages (clear actionable errors, not generic "validation failed").
- Validators enforce: `verdict` enum, `skill_id` against known expert list (`_eval/snapshot.py` `EXPERT_DIRS`), `ts` is ISO 8601, `output_snapshot.sha256` is 64-char hex.

### Claude's Discretion
- File-watcher implementation detail (inotify vs polling) — Claude's call, prefer stdlib `watchdog`-free polling for portability (Hermes ships on Linux/macOS/Windows/Termux per CLAUDE.md Platform Requirements).
- `/feedback` slash-command registration mechanism — follow existing `agent/skill_commands.py` pattern (file path is suggestive, exact integration at plan-phase discretion).
- JSONL batch import failure handling — all-or-nothing vs partial-success is at Claude's discretion; recommend all-or-nothing with clear error listing for MVP simplicity.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `skills/movie-experts/_eval/snapshot.py:1-50` — Provenance pattern (sha256 + git sha + ISO 8601 timestamp) with `EXPERT_DIRS` frozen list (anti-spoofing). Directly informs `output_snapshot` schema and `skill_id` validation.
- `hermes_cli/main.py:2135+` — `cmd_*` dispatcher pattern for CLI subcommands. New `cmd_feedback(args)` slots in cleanly alongside `cmd_chat`, `cmd_doctor`, `cmd_status`.
- `agent/curator.py:1388+` — `run_curator_review` background pattern. Informative for how P32 will eventually consume the feedback store, not directly reused in P28.
- `agent/skill_commands.py` — Existing slash-command registration (suggestive — confirm exact pattern at plan-phase).
- `hermes_state.py:364+` — `SessionDB` SQLite pattern. P28 does NOT persist feedback (that's P29); only needs to populate `output_snapshot` from current session state.

### Established Patterns
- `pydantic==2.13.4` — schema validation standard across codebase (`agent/error_classifier.py:69` `ClassifiedError` dataclass pattern).
- `from __future__ import annotations` + PEP 604 unions (`str | None`) — modern type syntax on Python 3.11+.
- `encoding="utf-8"` on every `open()` — Ruff PLW1514 rule (non-negotiable).
- `snake_case.py` module naming; `cmd_<name>(args)` dispatcher convention.
- File-system state under `~/.hermes/` — `get_hermes_home()` from `hermes_constants` (NOT `Path.home() / ".hermes"`).

### Integration Points
- `~/.hermes/skills/.feedback/` — new persistence root (P28 creates ingest path; P29 builds full store).
  - `inbox-kais/` — kais-aigc-platform file drop zone (INGEST-02)
  - `incoming/` — CLI feedback queue (INGEST-01) — processed immediately on receipt
  - `manual-import/` — optional staging area for batch JSONL (INGEST-03)
- CLI command surface: `hermes feedback <submit|import|...>` — subcommand dispatcher under existing `cmd_*` pattern.
- Conversation loop integration: `/feedback` slash command needs read access to current `AIAgent.messages` for `output_snapshot` extraction.

</code_context>

<specifics>
## Specific Ideas

- The kais-aigc-platform file-exchange directory MUST be operator-configurable (env var like `HERMES_FEEDBACK_INBOX_KAIS` overriding the default `~/.hermes/skills/.feedback/inbox-kais/`). Different operators may have different mount points for the kais-aigc-platform export.
- `output_snapshot` MUST include the LLM call params actually used (temperature, top_p, max_tokens, etc.) — not just the model name. This is critical for reproducibility and for the eval-gate ablation (P30) to work correctly.
- For batch import (INGEST-03), cold-start path is a first-class use case: operator has 10+ historical outputs they want to seed as baseline. JSONL format should make this trivial — one file, one record per line, no ceremony.

</specifics>

<deferred>
## Deferred Ideas

- HTTP endpoint and webhook transports for kais-aigc-platform (INGEST-02 alternatives) — deferred to FUTURE-V6 scope. P28 ships file exchange only. If a later phase needs HTTP, it layers on top of the same `FeedbackRecord` schema.
- Auto-redaction of PII in feedback corrections (noted as FUTURE-V6-06 in STATE.md risks). v6 assumes trusted operator environment.
- Feedback deduplication logic (mentioned in P29 STORE scope, not P28). P28 only ensures `output_snapshot.sha256` is captured so dedup is possible later.
- Cross-source feedback provenance tracking beyond the `source` enum (e.g., operator identity, session ID). `source` enum {`cli`, `kais_aigc`, `manual`} is sufficient for v6.

</deferred>
