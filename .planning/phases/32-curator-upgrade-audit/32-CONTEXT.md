# Phase 32: Curator Upgrade + Audit - Context

**Gathered:** 2026-06-24
**Status:** Ready for planning

<domain>
## Phase Boundary

The Curator (currently limited to archiving agent-created skills per `agent/curator.py` module docstring) gains the ability to:
1. Scan accumulated feedback in Phase 29 FeedbackStore for bundled skills crossing the negative-feedback threshold
2. Automatically trigger the EVOL pipeline (using the EVOL-02 unified-diff generator) to produce candidate patches
3. Land patches in the Phase 31 review queue (still subject to human-in-loop approve per EVOL-04)
4. Log every patch action (propose/approve/reject/apply/rollback) to a tamper-evident sha256-chained audit trail at `~/.hermes/skills/.audit/log.jsonl`
5. Expose operator CLI commands `hermes curator queue|approve|reject|audit-log`
6. Take a semi-automatic path for high-confidence agent-created skill patches (config-gated; bundled NEVER auto)

Covers requirements CURATE-01, CURATE-02, CURATE-03, CURATE-04, CURATE-05, EVOL-02.

**Hermes-core touch: Yes** — direct modification of `agent/curator.py` (extending `run_curator_review` + new proposal path) + implementation of EVOL-02 diff generator (invoked by Curator). This is the unavoidable scope expansion flagged in PROJECT.md.

**Depends on:** Phase 29 (FeedbackStore for feedback scan), Phase 31 (EVOL review queue + apply machinery + queue.py + apply.py).

**Critical regression constraint (SC-6):** The pre-v6 deterministic inactivity transitions + consolidation pass for agent-created skills MUST continue to work unchanged. Phase 32's bundled-skill proposal capability is ADDITIVE. Regression test against pre-v6 curator behavior required.

</domain>

<decisions>
## Implementation Decisions

### Audit Trail Format (CURATE-04)
- **JSONL append-only with sha256 chain** at `~/.hermes/skills/.audit/log.jsonl`. Each line:
  ```json
  {
    "entry_id": "<uuid4>",
    "prev_sha256": "<previous entry's entry_sha256; genesis entry uses sha256('')>",
    "action": "propose|approve|reject|apply|rollback|auto_apply",
    "ts": "2026-06-24T19:30:00Z",
    "operator": "<username or 'system'>",
    "patch_id": "<evolution patch_id>",
    "skill_id": "<target skill>",
    "feedback_ids": ["fb_id_1", "fb_id_2"],
    "eval_score": {"verdict": "pass", "mean_delta": 0.15},
    "commit_sha": "<git sha after apply; null for propose/reject>",
    "entry_sha256": "<sha256(prev_sha256 + json.dumps(rest, sort_keys=True))>"
  }
  ```
- `entry_sha256 = sha256((prev_sha256 + json.dumps({k:v for k,v in entry.items() if k != "entry_sha256"}, sort_keys=True)).encode("utf-8")).hexdigest()`
- Verification: `hermes curator audit-log --verify` walks the chain, recomputes each `entry_sha256`, reports breaks.
- Queryable: `hermes curator audit-log [--action apply] [--since 2026-06-01] [--skill <id>]`.

### EVOL-02 Generator Design (EVOL-02)
- **LLM emits structured patch instructions; difflib generates unified diff.** Matches Phase 31 placeholder pattern (extend, do not fork).
- Instruction schema (LLM output):
  ```json
  {
    "instructions": [
      {
        "file": "skills/movie-experts/screenplay/references/<file>.md",
        "anchor_section": "## Three-Act Structure",
        "add_after": true,
        "content_en": "...EN structure...",
        "content_zh": "...CN prose..."
      }
    ]
  }
  ```
- `agent/evolution/evol02_generator.py:generate_patch_from_knowledge_point(kp, current_files) -> str`:
  1. Validate instruction (file exists, anchor_section exists in current content)
  2. Compose new content block: bilingual (EN heading + body, then CN heading + body) per CLAUDE.md convention
  3. Use `difflib.unified_diff` to generate the unified diff
  4. Return diff string (compatible with `apply_patch_transaction` from P31)
- LLM prompt explicitly enforces: EN-structure + CN-prose bilingual style, preserve frontmatter byte-for-byte, additive-only.

### Confidence Score for Auto-Apply (CURATE-05)
- **Two signals required:**
  1. Eval gate passes AND `mean_delta >= +0.1` (positive improvement, not just pass)
  2. Aggregation insight's evidence chain has >= 3 unique feedback records
- Both must meet thresholds for "high confidence."
- Configurable: `feedback.curator.auto_apply_min_delta: 0.1`, `auto_apply_min_evidence: 3`, `auto_apply_enabled: false` (default OFF; operator opt-in).
- **Bundled skills NEVER auto-apply** regardless of confidence (SC-3 from P31 still holds; auto-apply only for agent-created skills).
- LLM self-score rejected (calibration issues). Single gate margin rejected (too loose).

### Curator Trigger Integration (CURATE-01)
- **Extend existing `run_curator_review`** with a feedback-scan phase:
  1. Existing pre-v6 behavior: deterministic inactivity transitions + consolidation pass for agent-created skills (UNCHANGED)
  2. NEW post-v6 phase: scan FeedbackStore for bundled skills with negative feedback crossing threshold
  3. For each hot skill: invoke EVOL pipeline (insights → diff → queue). Patches land in P31 queue.
  4. Log propose event to audit trail.
- Trigger thresholds: `feedback.curator.feedback_threshold_count: 3`, `feedback_threshold_sessions: 2`.
- Backward-compatible: if no feedback exists OR no skill crosses threshold, existing curator behavior is unchanged (regression test required).

### Curator CLI Surface

```bash
# List pending patches (delegates to P31 review-queue)
hermes curator queue [--skill <id>] [--status pending|applied|rejected]

# Approve a pending patch (delegates to P31 approve)
hermes curator approve <patch_id> [--yes]

# Reject a pending patch (delegates to P31 reject)
hermes curator reject <patch_id> <reason>

# Inspect audit trail
hermes curator audit-log [--action apply] [--since <date>] [--skill <id>] [--verify]
```

- `queue`/`approve`/`reject` are thin wrappers around P31 commands (single source of truth).
- `audit-log` is new — reads `~/.hermes/skills/.audit/log.jsonl`, applies filters, optionally verifies sha256 chain.

### Claude's Discretion
- Genesis entry `prev_sha256` — `sha256("").hexdigest()` = `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (document in module docstring).
- Audit log entry ordering — strictly append-only; no reorder, no edit. Deletions = chain break (detectable via `--verify`).
- LLM client construction for EVOL-02 — reuse `agent/evolution/insights.py` pattern (dependency injection).
- Auto-apply scope fence — single-process; if multi-process becomes a concern, add file locking (deferred).

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `agent/curator.py:run_curator_review` (existing Hermes runtime) — extend with feedback-scan phase. MUST preserve pre-v6 behavior per SC-6.
- `agent/curator.py:71-117` — `_state_file()`, `load_state`, `save_state` persistence pattern.
- `agent/evolution/insights.py:aggregate_feedback` (P31) — invoke for each hot skill
- `agent/evolution/queue.py:append_patch` (P31) — destination for curator-proposed patches
- `agent/evolution/apply.py:apply_patch_transaction` (P31) — invoked via `approve` (single caller per P31 invariant; P32 curator `approve` command is a wrapper, not a new caller)
- `agent/feedback_store.py:FeedbackStore.summary` (P29) — query for hot skills
- `skills/movie-experts/_eval/gate.py:run_gate` (P30) — invoke for candidate scoring
- `utils.atomic_json_write` — for audit log append (atomic)
- `hermes_cli/curator.py:register_cli` — existing subcommand pattern (extend with `queue`/`approve`/`reject`/`audit-log`)

### Established Patterns
- `encoding="utf-8"` on every `open()` (Ruff PLW1514)
- `from __future__ import annotations` at top
- `get_hermes_home()` (NEVER `Path.home() / ".hermes"`)
- subprocess argv-list, no shell=True
- Lazy %-logging, specific exceptions bound with `as exc:`
- Pydantic v2 for record schemas

### Integration Points
- **Input:** P29 FeedbackStore → curator feedback-scan phase
- **Input:** P31 evolution pipeline → curator invokes `aggregate_feedback` + EVOL-02 generator
- **Output:** P31 review queue → curator-proposed patches land here
- **Output:** `~/.hermes/skills/.audit/log.jsonl` → tamper-evident audit trail
- **Hermes runtime:** `agent/curator.py` IS runtime code — the extension must preserve deterministic inactivity transitions + consolidation pass (regression test required).

</code_context>

<specifics>
## Specific Ideas

- The audit log MUST be append-only — no edit, no delete. The sha256 chain makes silent tampering detectable. If an operator needs to "retract" an entry, they append a new entry with `action: retract` referencing the original `entry_id`.
- The EVOL-02 generator MUST preserve bilingual EN-structure + CN-prose style per CLAUDE.md. LLM prompt explicitly requires both languages. Verify via heuristic: new content block contains both `## ` (EN heading) AND `### 中文标题` or similar CN marker.
- The semi-automatic path (CURATE-05) MUST default OFF — operator must explicitly enable via config. Even when enabled, bundled skills NEVER auto-apply (SC-3 from P31 holds globally).
- The curator trigger threshold (≥3 needs_work/bad across ≥2 sessions) MUST be configurable. Operators with sparser feedback may lower; operators with denser feedback may raise.

</specifics>

<deferred>
## Deferred Ideas

- **Multi-operator audit log merge** — v6 is single-operator. FUTURE-V6.
- **Cryptographic audit log signing** (e.g., GPG-signed entries) — sha256 chain is sufficient for v6 trust model (single-operator). FUTURE-V6.
- **Audit log retention policy** — v6 keeps everything. Auto-prune deferred.
- **EVOL-02 inline rewrite** (not just additive) — v6 EVOL-02 is additive-only per FOUND-08 + SC-6 (P31). Inline rewrite is FUTURE-V6.
- **Curator proactive insight surfacing** (e.g., "skill X has 5 bad verdicts, consider manual review") — operators can run `hermes curator queue` manually. Proactive notifications deferred.
- **Cross-skill curator proposals** (one insight → multi-skill patches) — out of scope; curator proposes per-skill.

</deferred>
