# Phase 31: Knowledge Evolution Pipeline - Context

**Gathered:** 2026-06-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Accumulated feedback (Phase 29 FeedbackStore) is transformed by an LLM aggregation pass into structured candidate insights, each carrying an evidence chain. Insights become candidate patches (unified diffs against `SKILL.md` / `references/*.md`). Patches pass through the Phase 30 eval gate before entering a review queue. The operator reviews via CLI, approves/rejects by ID, and approved patches apply atomically with FOUND-08 byte-intact verification + automatic git commit + rollback machinery. **Bundled skills NEVER auto-apply** — human-in-loop is non-bypassable per SC-3.

Covers requirements EVOL-01, EVOL-03, EVOL-04, EVOL-05. (EVOL-02 — the candidate-patch diff generator — is mapped to Phase 32 per STATE.md; P32's Curator invokes it. Phase 31 builds the review queue + approve/apply mechanics but uses a placeholder generator if EVOL-02 is not yet available.)

**Depends on:** Phase 29 (FeedbackStore for feedback aggregation) + Phase 30 (gate.py for patch scoring). Hermes-core touch: Mixed — new pipeline orchestration code under `agent/` + `hermes_cli/`; patches it produces target bundled SKILL.md / refs (additive only per SC-5/SC-6).

</domain>

<decisions>
## Implementation Decisions

### LLM Aggregation Trigger (EVOL-01)
- **CLI subcommand `hermes feedback evolve --skill <id>`** — operator-invoked, synchronous. Reads `FeedbackStore.query(skill_id=<id>)` + `summary(skill_id=<id>)`, passes to LLM with an aggregation prompt, emits structured candidate insights to stdout + appends to `~/.hermes/skills/.feedback/evolution/insights.jsonl`.
- Each insight record: `{insight_id, skill_id, theme, evidence_chain: [feedback_id, ...], rationale, proposed_patch_summary, ts}`.
- Default model: agent's configured model (`agent.model_name` or equivalent). Override via `--model <name>`.
- No background daemon (scope discipline — daemon is P32 Curator scope). No per-feedback streaming (too granular for LLM).

### Patch Review Queue Format (EVOL-03)
- **`~/.hermes/skills/.feedback/evolution/queue.jsonl`** — append-only JSONL. One line per pending patch.
- Patch record schema:
  ```json
  {
    "patch_id": "screenplay_20260624_193000_a1b2c3d4e5f6g7h8",
    "skill_id": "screenplay",
    "insight_id": "...",
    "unified_diff": "--- a/.../SKILL.md\n+++ b/.../SKILL.md\n...",
    "feedback_chain": ["fb_id_1", "fb_id_2", ...],
    "llm_rationale": "Operators consistently noted X is missing...",
    "eval_gate_score": {"verdict": "pass", "mean_delta": 0.15, "per_prompt_max_drop": -0.3},
    "status": "pending",
    "ts_queued": "2026-06-24T19:30:00Z"
  }
  ```
- On approve → move to `applied.jsonl` with `commit_sha` + `ts_applied`.
- On reject → move to `rejected.jsonl` with `reason` + `ts_rejected`.
- SQLite rejected (overkill for ~10-100 pending patches). One-JSON-per-patch rejected (file proliferation).

### Patch Review UI (EVOL-03)
- **CLI viewer + approve/reject commands:**
  - `hermes feedback review-queue [--skill <id>] [--status pending|applied|rejected]` — prints table with patch_id, skill, verdict, mean_delta, feedback count, summary.
  - `hermes feedback show-patch <patch_id>` — prints full unified diff + LLM rationale + feedback chain.
  - `hermes feedback approve <patch_id>` — applies patch atomically (FOUND-08 check + git commit). Confirms with `--yes` flag for non-interactive; otherwise prompts.
  - `hermes feedback reject <patch_id> <reason>` — moves to rejected.jsonl with reason.
- No markdown report (passive, no inline action). No web dashboard (P33 scope).

### Patch Apply Git Workflow (EVOL-04)
- **Direct commit to current branch**, atomic transaction:
  1. Apply unified diff via `git apply` (subprocess, no shell=True)
  2. Verify FOUND-08 byte-intact: `git diff --name-only HEAD -- skills/movie-experts/ | grep -v _eval | grep -v _shared | wc -l` returns 0 (or, per-patch: parse `+++` lines and check each path is allowed)
  3. Verify additive-only for v4/v5 refs: parse diff, reject any `-` lines that remove content from `snowflake-method.md` / `e-konte-format.md` / `scamper-variations.md` / `dreamina-cli-baseline.md` / `v86-pipeline-mapping.md`
  4. Stage modified files
  5. Commit with message: `feat(evolution): <insight_summary> | feedback: <ids> | eval: <score>`
  6. On ANY step failure: abort, restore working tree, exit non-zero
- Rollback via `git revert <commit_sha>` (operator-invoked, not automatic)
- Branch + PR rejected (overhead — operator is the reviewer). Dedicated evolution branch rejected (complexity without benefit for single-operator v6).

### Claude's Discretion
- LLM aggregation prompt template — Claude designs; recommend structured output (JSON with `insights: [...]` field).
- Insight ID format — Claude's call (recommend `f"{skill_id}_{ts_unix}_{sha256[:8]}"`).
- Patch ID format — same as Phase 30 (`f"{skill_id}_{ts_unix}_{sha256[:16]}"` per P30 WR-04 fix).
- Operator approval prompt UI — `--yes` flag for scripted automation; default interactive prompt with `[y/N]` confirmation.
- Concurrent patch application — single-process assumed; document in module docstring.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `agent/feedback_store.py:FeedbackStore` (Phase 29) — `query()`, `summary()`, `get_record()` for reading accumulated feedback
- `skills/movie-experts/_eval/gate.py:run_gate()` (Phase 30) — Score candidate patches before they enter review queue
- `agent/feedback_ingest.py:write_feedback_record` (Phase 28/29) — Atomic write pattern template
- `utils.atomic_json_write` — Atomic JSONL append for queue.jsonl
- `hermes_cli/feedback.py` (Phase 28/29) — Existing CLI subcommand dispatcher; add `evolve`, `review-queue`, `show-patch`, `approve`, `reject` subcommands
- `agent/curator.py:load_state/save_state` — Persistence pattern template

### Established Patterns
- Pydantic for record schemas (`agent/feedback_schema.py`)
- `encoding="utf-8"` on every `open()` (Ruff PLW1514)
- `from __future__ import annotations`
- `get_hermes_home()` from `hermes_constants`
- `subprocess.run([...], argv-list)` — no `shell=True` (per Phase 30 T-30-02 pattern)
- Lazy %-logging, specific exceptions bound

### Integration Points
- **Input:** Phase 29 FeedbackStore → `evolve` command reads feedback
- **Input:** Phase 30 gate.py → patches must pass `run_gate()` before queue insertion (EVOL-05)
- **Output:** Phase 32 Curator will invoke the same `evolve` machinery automatically; P31 ships the building blocks
- **Hermes runtime:** Evolution pipeline is operator-invoked, NOT imported by runtime (similar to `_eval/`). Document isolation.
- **Git state:** Patch apply performs commits — operator's working tree must be clean before apply (verify in `approve` command)

</code_context>

<specifics>
## Specific Ideas

- The LLM aggregation prompt MUST instruct the model to:
  1. Group feedback by theme (e.g., "missing X method", "unclear Y section", "wrong Z example")
  2. Cite specific feedback IDs in each insight (evidence chain)
  3. Propose additive-only changes (never delete or restructure existing content)
  4. Preserve expert_id + related_skills frontmatter byte-for-byte (FOUND-08)
  5. Output structured JSON with `insights` array
- The patch queue MUST require eval gate passage (EVOL-05). A patch that fails the gate is logged to `~/.hermes/skills/.feedback/evolution/failed_gate.jsonl` with the rejection reason; it never enters `queue.jsonl`.
- Operator approve flow MUST do FOUND-08 check + additive-only check at apply time (defense in depth — even if the patch was correct at queue time, a concurrent edit could have changed the baseline).
- The commit message format MUST be machine-parseable for the audit trail: `feat(evolution): <subject> | feedback: <comma-separated-ids> | eval: <verdict>:<mean_delta>`.

</specifics>

<deferred>
## Deferred Ideas

- **EVOL-02 diff generator** — Mapped to Phase 32 (Curator invokes it). P31 uses a placeholder if EVOL-02 not yet shipped; tests mock the generator.
- **Background daemon** — P32 Curator scope. P31 ships operator-invoked only.
- **Web dashboard for review queue** — P33 Observability scope. P31 ships CLI only.
- **Multi-skill patches in a single insight** — Out of scope; one insight = one skill patch. Multi-skill coordination is operator's manual responsibility.
- **Auto-rollback on regression detection** — Future work. v6 requires manual `git revert`.
- **Cross-operator patch sharing** — v6 is single-operator. FUTURE-V6.
- **Patch dependency graph** — Patches applied independently; dependency tracking is future work.

</deferred>
