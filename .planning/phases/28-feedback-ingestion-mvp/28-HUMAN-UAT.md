---
status: partial
phase: 28-feedback-ingestion-mvp
source: [28-VERIFICATION.md]
started: 2026-06-24T13:30:00Z
updated: 2026-06-24T13:30:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Live REPL smoke test of `/feedback` slash command

**Expected:** Inside an actual `hermes` REPL conversation, the operator invokes any movie-expert skill (e.g., `/screenplay`), waits for the skill's output, then types `/feedback good "nice work"`. The REPL should:
- Print a confirmation message (e.g., "Feedback recorded: <filename>")
- Persist a JSON file to `~/.hermes/skills/.feedback/incoming/` with:
  - `skill_id` matching the invoked skill
  - `expert_id` resolved via `_SKILL_INVOCATION_PREFIX` scan
  - `source: "cli"`
  - `verdict: "good"`
  - `correction: "nice work"`
  - `output_snapshot` containing real `sha256` (64-char hex), `prompt` (the user's last message), `model` (current agent's model), `params` (max_tokens, reasoning_config, service_tier, request_overrides)
  - `ts` in ISO 8601 UTC

**Why manual:** The `/feedback` handler reads live REPL state (`self.agent` + `self.conversation_history`) at `cli.py` and `hermes_cli/cli_commands_mixin.py:2295`. Unit tests stub these attributes but cannot faithfully reproduce the interactive session state.

**Result:** [pending]

**Steps:**
1. Launch `hermes chat` (or `python cli.py`)
2. Invoke any movie-expert skill (e.g., `/screenplay` for a 30-second short scene)
3. Wait for the skill output to complete
4. Type: `/feedback good "nice work"`
5. Verify confirmation message appears
6. Verify JSON file written: `ls ~/.hermes/skills/.feedback/incoming/`
7. Inspect JSON: `cat ~/.hermes/skills/.feedback/incoming/*.json | jq .`
8. Verify fields are populated with real data (not stubs)

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps
