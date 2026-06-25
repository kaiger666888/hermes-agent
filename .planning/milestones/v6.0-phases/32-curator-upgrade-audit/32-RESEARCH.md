# Phase 32: Curator Upgrade + Audit - Research

**Researched:** 2026-06-24
**Domain:** Hermes runtime extension (`agent/curator.py`) + EVOL-02 diff generator + tamper-evident audit log (sha256 chain) + operator CLI + semi-automatic apply path
**Confidence:** HIGH (all claims verified against in-repo source: `agent/curator.py`, `agent/evolution/*`, `agent/feedback_store.py`, `hermes_cli/curator.py`, `hermes_cli/feedback.py`, `tools/skill_usage.py`, and the P31 structural invariant test)

## Summary

Phase 32 is the most architecturally constrained phase in v6.0 because it is the **only phase that modifies Hermes runtime code** (`agent/curator.py`) AND must comply with a P31-shipped structural invariant (`TestNonBypassableHumanInLoop`) that forbids `apply_patch_transaction` from being called anywhere in `agent/` outside `agent/evolution/`. The planner MUST design around this constraint or the phase will fail the P31 regression test on the first commit.

The five sub-problems are well-separated and map cleanly to files:

1. **Curator feedback-scan phase (CURATE-01/02)** — extend `run_curator_review` with an ADDITIVE post-pass that scans `FeedbackStore` for hot skills, invokes `aggregate_feedback` (P31) + the EVOL-02 generator, and lands patches in the P31 review queue. The existing deterministic inactivity transitions + consolidation gate run UNCHANGED (SC-6).
2. **EVOL-02 generator (EVOL-02)** — extend `agent/evolution/diff_generator.py` with `generate_patch_from_knowledge_point(kp, current_files) -> str` that handles multi-instruction + bilingual content composition. Reuses the P31 placeholder's `difflib.unified_diff` + anchor-uniqueness + frontmatter-immutability guards.
3. **Audit log (CURATE-03)** — new module `agent/curator_audit.py` (NOT under `agent/evolution/` — see Pitfall #1) implementing JSONL append + sha256 chain. Genesis `prev_sha256 = sha256("").hexdigest()`.
4. **Curator CLI (CURATE-04)** — extend `hermes_cli/curator.py:register_cli` with `queue` / `approve` / `reject` / `audit-log` subparsers. The first three are THIN WRAPPERS that delegate to P31's `_cmd_review_queue` / `_cmd_approve` / `_cmd_reject` in `hermes_cli/feedback.py` — single source of truth.
5. **Semi-automatic path (CURATE-05)** — the hard one. See Architectural Constraint #1 below.

**Primary recommendation:** Split into two plans — Plan 01 (engine: curator extension + EVOL-02 generator + audit log module + regression tests) and Plan 02 (CLI: curator subcommands + audit-log query/verify + auto-apply path + CLI smoke tests). This mirrors the P28/P29/P30/P31 two-plan cadence and keeps each plan's test surface under ~50 tests.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Feedback threshold scan (CURATE-02) | Hermes runtime (`agent/curator.py`) | FeedbackStore (P29, read-only) | Curator owns the periodic scan trigger; FeedbackStore owns the data |
| EVOL-02 diff generation | New code under `agent/evolution/` | `agent/evolution/insights.py` (InsightRecord consumer) | Evolution subpackage owns all patch-generation logic per P31 invariant |
| Audit log append + chain (CURATE-03) | New module `agent/curator_audit.py` (runtime) | — | Must be importable from BOTH `agent/curator.py` (propose/auto-apply) AND `hermes_cli/feedback.py:_cmd_approve` (apply/reject) — so it cannot live under `agent/evolution/` (which runtime cannot import per P31 isolation) |
| Audit log query + verify (CURATE-03) | `hermes_cli/curator.py` (CLI) | — | Operator-facing; reads JSONL, applies filters, walks sha256 chain |
| Curator `queue`/`approve`/`reject` CLI (CURATE-04) | `hermes_cli/curator.py` | delegates to `hermes_cli/feedback.py` (P31) | Thin wrappers — P31 owns the queue lifecycle |
| Auto-apply (CURATE-05) | `hermes_cli/feedback.py` (CLI handler) | `agent/curator.py` (proposal + confidence scoring) | The ONLY legitimate caller of `apply_patch_transaction` is `_cmd_approve` per P31 structural test — see Architectural Constraint #1 |

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Audit Trail Format (CURATE-04)**
- JSONL append-only with sha256 chain at `~/.hermes/skills/.audit/log.jsonl`.
- Each line: `{entry_id, prev_sha256, action, ts, operator, patch_id, skill_id, feedback_ids, eval_score, commit_sha, entry_sha256}`.
- `action ∈ {propose, approve, reject, apply, rollback, auto_apply}`.
- `entry_sha256 = sha256((prev_sha256 + json.dumps({k:v for k,v in entry.items() if k != "entry_sha256"}, sort_keys=True)).encode("utf-8")).hexdigest()`.
- Genesis entry uses `prev_sha256 = sha256("").hexdigest()`.
- Verification: `hermes curator audit-log --verify` walks the chain, recomputes each `entry_sha256`, reports breaks.
- Queryable: `hermes curator audit-log [--action apply] [--since 2026-06-01] [--skill <id>]`.

**EVOL-02 Generator Design (EVOL-02)**
- LLM emits structured patch instructions; difflib generates unified diff. Matches P31 placeholder pattern (extend, do not fork).
- Instruction schema (LLM output): `{instructions: [{file, anchor_section, add_after, content_en, content_zh}]}`.
- `agent/evolution/evol02_generator.py:generate_patch_from_knowledge_point(kp, current_files) -> str`:
  1. Validate instruction (file exists, anchor_section exists in current content)
  2. Compose new content block: bilingual (EN heading + body, then CN heading + body) per CLAUDE.md convention
  3. Use `difflib.unified_diff` to generate the unified diff
  4. Return diff string (compatible with `apply_patch_transaction` from P31)
- LLM prompt explicitly enforces: EN-structure + CN-prose bilingual style, preserve frontmatter byte-for-byte, additive-only.

**Confidence Score for Auto-Apply (CURATE-05)**
- Two signals required: (1) eval gate passes AND `mean_delta >= +0.1`; (2) aggregation insight's evidence chain has >= 3 unique feedback records. Both must meet thresholds for "high confidence."
- Configurable: `feedback.curator.auto_apply_min_delta: 0.1`, `auto_apply_min_evidence: 3`, `auto_apply_enabled: false` (default OFF; operator opt-in).
- **Bundled skills NEVER auto-apply** regardless of confidence (SC-3 from P31 still holds; auto-apply only for agent-created skills).
- LLM self-score rejected (calibration issues). Single gate margin rejected (too loose).

**Curator Trigger Integration (CURATE-01)**
- Extend existing `run_curator_review` with a feedback-scan phase:
  1. Existing pre-v6 behavior: deterministic inactivity transitions + consolidation pass for agent-created skills (UNCHANGED)
  2. NEW post-v6 phase: scan FeedbackStore for bundled skills with negative feedback crossing threshold
  3. For each hot skill: invoke EVOL pipeline (insights → diff → queue). Patches land in P31 queue.
  4. Log propose event to audit trail.
- Trigger thresholds: `feedback.curator.feedback_threshold_count: 3`, `feedback_threshold_sessions: 2`.
- Backward-compatible: if no feedback exists OR no skill crosses threshold, existing curator behavior is unchanged (regression test required).

**Curator CLI Surface**
- `hermes curator queue [--skill <id>] [--status pending|applied|rejected]` — delegates to P31 review-queue.
- `hermes curator approve <patch_id> [--yes]` — delegates to P31 approve.
- `hermes curator reject <patch_id> <reason>` — delegates to P31 reject.
- `hermes curator audit-log [--action apply] [--since <date>] [--skill <id>] [--verify]` — new, reads audit JSONL.
- `queue`/`approve`/`reject` are thin wrappers around P31 commands (single source of truth).

### Claude's Discretion
- Genesis entry `prev_sha256` — `sha256("").hexdigest()` = `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (document in module docstring).
- Audit log entry ordering — strictly append-only; no reorder, no edit. Deletions = chain break (detectable via `--verify`).
- LLM client construction for EVOL-02 — reuse `agent/evolution/insights.py` pattern (dependency injection).
- Auto-apply scope fence — single-process; if multi-process becomes a concern, add file locking (deferred).

### Deferred Ideas (OUT OF SCOPE)
- Multi-operator audit log merge — v6 is single-operator. FUTURE-V6.
- Cryptographic audit log signing (e.g., GPG-signed entries) — sha256 chain is sufficient for v6 trust model. FUTURE-V6.
- Audit log retention policy — v6 keeps everything. Auto-prune deferred.
- EVOL-02 inline rewrite (not just additive) — v6 EVOL-02 is additive-only per FOUND-08 + SC-6 (P31). FUTURE-V6.
- Curator proactive insight surfacing — operators can run `hermes curator queue` manually. Proactive notifications deferred.
- Cross-skill curator proposals (one insight → multi-skill patches) — out of scope; curator proposes per-skill.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CURATE-01 | Extend `agent/curator.py` scope to propose bundled-skill patches | `run_curator_review` extension point documented in §"Curator Module Structure"; feedback-scan phase is ADDITIVE after the consolidation-gate branch |
| CURATE-02 | Auto-trigger EVOL on negative-feedback threshold (≥3 needs_work/bad across ≥2 sessions) | FeedbackStore scan pattern in §"Feedback Threshold Scan"; threshold config keys documented |
| CURATE-03 | `~/.hermes/skills/.audit/` tamper-evident log | `agent/curator_audit.py` module design + sha256 chain algorithm in §"Audit Log sha256 Chain" |
| CURATE-04 | `hermes curator queue/approve/reject` CLI | Subparser registration in §"Curator CLI Extension"; thin-wrapper delegation to P31 |
| CURATE-05 | Agent-created skill semi-automatic path (confidence ≥ threshold, default OFF, bundled NEVER auto) | Two-signal confidence + auto_apply flow in §"Auto-Apply Path (CURATE-05)"; **Architectural Constraint #1** governs the call site |
| EVOL-02 | Knowledge-point → candidate patch generation (unified diff, bilingual, additive) | `generate_patch_from_knowledge_point` design in §"EVOL-02 Generator Extension"; extends P31 placeholder |
</phase_requirements>

## Architectural Constraint #1 (CRITICAL — read before planning)

**The P31 structural invariant `TestNonBypassableHumanInLoop` (`tests/hermes_cli/test_evolution_cli.py:846`) FORBIDS any call to `apply_patch_transaction` outside `hermes_cli/feedback.py:_cmd_approve`.** It enforces this via two AST-walk tests:

1. `test_only_cmd_approve_calls_apply_patch_transaction` — walks `hermes_cli/feedback.py`; every `apply_patch_transaction(...)` Call node MUST be enclosed in a FunctionDef named `_cmd_approve`.
2. `test_apply_patch_transaction_not_called_in_agent_or_runtime` — walks `agent/`, `gateway/`, `run_agent.py`, `cli.py`; ZERO `apply_patch_transaction(...)` calls permitted (excluding `agent/evolution/` itself).

**Impact on CURATE-05 auto-apply:** The auto-apply path CANNOT live in `agent/curator.py` (which is runtime code under `agent/`). It MUST be invoked from a CLI handler in `hermes_cli/feedback.py` (or a new `hermes_cli/curator.py` handler that delegates into feedback.py). [VERIFIED: tests/hermes_cli/test_evolution_cli.py:846-953]

**Recommended design:** `agent/curator.py` computes the confidence score and decides "this patch is auto-apply eligible" — but it does NOT call `apply_patch_transaction`. Instead it marks the `PatchRecord` with `auto_apply_eligible=True` + confidence metadata. A new CLI handler `_cmd_curator_auto_apply` (or an extension to `_cmd_approve` that accepts `--auto <patch_id>`) in `hermes_cli/feedback.py` performs the actual apply. This keeps the structural invariant intact.

**Alternative (NOT recommended):** Weakening the structural test to allowlist `agent/curator.py` as a second caller. This reopens the EVOL-04 bypass risk the test was designed to prevent. Reject this unless the operator explicitly trades off the safety guarantee.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| stdlib `hashlib` | (stdlib) | sha256 chain for audit log | Already used by P28/P29/P31 for content addressing. No new dep. [VERIFIED: agent/evolution/insights.py:29, agent/feedback_store.py] |
| stdlib `difflib` | (stdlib) | unified_diff generation for EVOL-02 | Already used by P31 placeholder `generate_additive_diff`. [VERIFIED: agent/evolution/diff_generator.py:18] |
| stdlib `json` | (stdlib) | JSONL audit log append + entry serialization | Already used throughout feedback subsystem. [VERIFIED: agent/feedback_store.py:41] |
| stdlib `uuid` | (stdlib) | `entry_id = str(uuid4())` for audit log entries | Standard for unique IDs. [ASSUMED] — consistent with Hermes' other ID patterns |
| stdlib `argparse` | (stdlib) | subparser registration for curator CLI | Already used by `hermes_cli/curator.py:495`. [VERIFIED: hermes_cli/curator.py:495] |
| `pydantic` | ==2.13.4 | AuditEntry schema (optional — may use dataclass) | Already a core dep. [CITED: pyproject.toml CLAUDE.md stack] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `agent.evolution.insights` | (P31 in-repo) | `aggregate_feedback` + `InsightRecord` + `make_aggregation_client` | Curator feedback-scan phase invokes per hot skill |
| `agent.evolution.queue` | (P31 in-repo) | `PatchRecord` + `append_patch` + `read_queue` + `move_patch` | Curator lands proposed patches here; CLI wrappers delegate here |
| `agent.evolution.apply` | (P31 in-repo) | `apply_patch_transaction` + `build_commit_message` | ONLY from `_cmd_approve` (structural invariant); `build_commit_message` reusable from elsewhere |
| `agent.evolution.diff_generator` | (P31 in-repo) | `generate_additive_diff` (P31 placeholder) — extend, do not fork | EVOL-02 generator builds on this |
| `agent.feedback_store.FeedbackStore` | (P29 in-repo) | `summary()` + `query()` for hot-skill detection | Curator scan reads this; FeedbackStore has NO `list_skill_ids()` — see Pitfall #4 |
| `tools.skill_usage` | (in-repo) | `is_agent_created(skill_name)` + `is_bundled(skill_name)` | CURATE-05 bundled-vs-agent-created check |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| sha256 chain (JSONL) | GPG-signed entries | Rejected as deferred (v6 trust model = single-operator). GPG adds key-management overhead with no v6 benefit. |
| `difflib.unified_diff` (stdlib) | LLM emits raw `@@ -A,B +C,D @@` hunks | Rejected in P31 (RESEARCH A1): LLMs unreliable at hunk syntax. P32 extends the difflib approach. |
| Audit log under `agent/evolution/audit.py` | New `agent/curator_audit.py` | Evolution subpackage is runtime-isolated per P31 invariant. Curator runtime + CLI both need to append → cannot live under `agent/evolution/`. See Pitfall #1. |

**Installation:**
```bash
# No new packages. All dependencies are stdlib or already in pyproject.toml.
# Verify before/after:
uv pip list | grep -i pydantic  # should show 2.13.4
```

**Version verification:** No new packages this phase. All deps verified via P28-P31 shipped code (which itself passed audit).

## Package Legitimacy Audit

> This phase installs ZERO external packages. All work is stdlib + existing in-repo modules. The Package Legitimacy Gate is a no-op.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| (none) | — | — | — | — | — | No new packages |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
                 ┌─────────────────────────────────────────────────────────────┐
                 │                    OPERATOR (CLI)                           │
                 │  hermes curator run | queue | approve | reject | audit-log   │
                 └──────────────┬──────────────────────────┬───────────────────┘
                                │                          │
                                │ trigger                  │ query / verify
                                ▼                          ▼
┌──────────────────────────────────────┐      ┌────────────────────────────────────┐
│  agent/curator.py (RUNTIME EXTENSION)│      │  hermes_cli/curator.py (CLI LAYER)  │
│                                      │      │                                    │
│  run_curator_review():               │      │  _cmd_queue  ──delegate──► P31      │
│   1. apply_automatic_transitions()   │      │  _cmd_approve──delegate──► P31      │
│      (pre-v6, UNCHANGED — SC-6)      │      │  _cmd_reject ──delegate──► P31      │
│   2. consolidation gate              │      │  _cmd_audit_log (NEW — reads JSONL, │
│      (pre-v6, UNCHANGED — SC-6)      │      │   applies filters, --verify walks   │
│   3. NEW feedback-scan phase ────────┼──┐   │   sha256 chain)                     │
│      for each hot skill:             │  │   └────────────────────────────────────┘
│        aggregate_feedback ───────────┼──┼──► agent/evolution/insights.py (P31)
│        generate_patch_from_kp ───────┼──┼──► agent/evolution/diff_generator.py
│        append_patch ─────────────────┼──┼──► agent/evolution/queue.py (P31)
│        append_audit(propose) ────────┼──┼──► agent/curator_audit.py (NEW)
│   4. compute confidence; mark        │  │
│      PatchRecord.auto_apply_eligible │  │
└──────────────────────────────────────┘  │
                                            │
                                ┌───────────▼───────────┐
                                │  agent/curator_audit  │
                                │  (NEW MODULE — not    │
                                │   under evolution/)   │
                                │                       │
                                │  append_audit():      │
                                │    prev = last entry  │
                                │    entry_sha256 =     │
                                │      sha256(prev +    │
                                │      json(entry))     │
                                │    JSONL append       │
                                │                       │
                                │  verify_chain():      │
                                │    walk, recompute,   │
                                │    report breaks      │
                                └───────────┬───────────┘
                                            │ writes
                                            ▼
                          ~/.hermes/skills/.audit/log.jsonl

                                            │ reads
                                            ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  AUTO-APPLY PATH (CURATE-05) — MUST route through _cmd_approve (P31 test)  │
│                                                                            │
│  Option A (RECOMMENDED): operator runs                                     │
│    hermes curator approve <auto_eligible_id> --yes                         │
│  → _cmd_approve in hermes_cli/feedback.py calls apply_patch_transaction    │
│  → append_audit(action=auto_apply) logged                                  │
│                                                                            │
│  Option B (full auto, still CLI-gated):                                    │
│    hermes feedback auto-apply-eligible                                     │
│  → new handler in hermes_cli/feedback.py (NOT agent/) that scans queue     │
│    for auto_apply_eligible patches, checks bundled=NO, invokes             │
│    apply_patch_transaction, appends audit                                  │
└────────────────────────────────────────────────────────────────────────────┘
```

The flow trace for the primary use case (operator triggers curator → bundled skill patch enters queue → operator approves):
1. Operator runs `hermes curator run` → `agent/curator.py:run_curator_review` (sync)
2. Pre-v6 phases run unchanged (inactivity transitions + consolidation gate)
3. NEW feedback-scan phase iterates FeedbackStore buckets, finds hot skill
4. For each hot skill: `aggregate_feedback` → `InsightRecord[]` → `generate_patch_from_knowledge_point` → unified diff → `append_patch` (lands in `queue.jsonl`) + `append_audit(action=propose)`
5. Operator runs `hermes curator queue` → delegates to P31 `_cmd_review_queue` → prints pending patches
6. Operator runs `hermes curator approve <patch_id> --yes` → delegates to P31 `_cmd_approve` → `apply_patch_transaction` → `move_patch(applied)` + `append_audit(action=apply)`

### Recommended Project Structure
```
agent/
├── curator.py                  # EXTEND run_curator_review (additive feedback-scan phase)
├── curator_audit.py            # NEW — JSONL append + sha256 chain + verify_chain
└── evolution/
    ├── diff_generator.py       # EXTEND — add generate_patch_from_knowledge_point
    └── evol02_generator.py     # NEW (optional split) — bilingual composition + multi-instruction
                                #   OR keep in diff_generator.py (simpler — one file)
hermes_cli/
├── curator.py                  # EXTEND register_cli — queue/approve/reject/audit-log
└── feedback.py                 # MAY extend _cmd_approve OR add _cmd_auto_apply (Option B)

tests/
├── agent/
│   ├── test_curator_feedback_scan.py   # NEW — threshold detection + EVOL pipeline invocation
│   ├── test_curator_regression.py      # NEW — pre-v6 curator behavior preserved (SC-6)
│   ├── test_curator_audit.py           # NEW — append + verify + tamper detection
│   └── evolution/
│       └── test_evol02_generator.py    # NEW — bilingual + multi-instruction + anchor validation
└── hermes_cli/
    ├── test_curator_cli.py             # NEW — queue/approve/reject/audit-log smoke tests
    └── test_evolution_cli.py           # EXISTING (P31) — TestNonBypassableHumanInLoop MUST still pass
```

### Pattern 1: Additive Curator Extension (SC-6 preservation)
**What:** The feedback-scan phase runs AFTER the pre-v6 deterministic transitions + consolidation gate, as a SEPARATE step. Pre-v6 code paths are not modified — only appended to.
**When to use:** Always — this is the SC-6 regression contract.
**Example:**
```python
# Source: agent/curator.py:run_curator_review (extension point at the end of _llm_pass)
# AFTER the existing consolidation block + report write:

def _feedback_scan_phase(start: datetime) -> dict[str, Any]:
    """NEW v6 phase — scan FeedbackStore for hot bundled skills.

    ADDITIVE: does NOT touch agent-created skills (pre-v6 territory).
    """
    try:
        from agent.feedback_store import FeedbackStore
        from agent.evolution import aggregate_feedback, append_patch  # lazy
        from agent.curator_audit import append_audit
        store = FeedbackStore()
        hot = _scan_for_hot_skills(store)  # CURATE-02 threshold check
        proposed = []
        for skill_id in hot:
            client, model = make_aggregation_client()
            insights = aggregate_feedback(skill_id=skill_id, store=store, client=client, model=model)
            for insight in insights:
                diff = generate_patch_from_knowledge_point(insight, current_files=...)
                patch = PatchRecord(patch_id=..., skill_id=skill_id, insight_id=insight.insight_id,
                                    unified_diff=diff, feedback_chain=insight.evidence_chain, ...)
                append_patch(patch, evolution_dir=_evolution_dir())
                append_audit(action="propose", patch_id=patch.patch_id, skill_id=skill_id,
                             feedback_ids=insight.evidence_chain, operator="system")
                proposed.append(patch.patch_id)
        return {"scanned": len(hot), "proposed": proposed}
    except Exception as e:
        logger.warning("curator feedback-scan phase failed: %s", e)
        return {"scanned": 0, "proposed": [], "error": str(e)}
```

### Pattern 2: sha256 Chain Append (CURATE-03)
**What:** Each audit entry's `entry_sha256` is computed from the previous entry's `entry_sha256` + the current entry's content (minus its own `entry_sha256` field).
**When to use:** Every `append_audit` call.
**Example:**
```python
# Source: CONTEXT.md decisions §"Audit Trail Format"
import hashlib, json, uuid
from datetime import datetime, timezone
from pathlib import Path

GENESIS_PREV_SHA256 = hashlib.sha256(b"").hexdigest()
# = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

def _audit_log_path() -> Path:
    from hermes_constants import get_hermes_home
    p = get_hermes_home() / "skills" / ".audit" / "log.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def _compute_entry_sha256(prev_sha256: str, entry_data: dict) -> str:
    # CRITICAL: exclude entry_sha256 itself from the payload. Sort keys for
    # deterministic serialization (CONTEXT.md formula). Compact separators
    # to match the verify-chain recompute exactly.
    payload_dict = {k: v for k, v in entry_data.items() if k != "entry_sha256"}
    payload = prev_sha256 + json.dumps(payload_dict, sort_keys=True,
                                       separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def append_audit(*, action: str, patch_id: str, skill_id: str,
                 operator: str = "system", feedback_ids: list[str] | None = None,
                 eval_score: dict | None = None, commit_sha: str | None = None) -> str:
    path = _audit_log_path()
    # Read prev_sha256: last line's entry_sha256, or GENESIS if empty/new file.
    prev = GENESIS_PREV_SHA256
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
        if lines:
            try:
                prev = json.loads(lines[-1])["entry_sha256"]
            except (json.JSONDecodeError, KeyError):
                # Corrupt tail — do NOT silently chain from a broken entry.
                raise AuditChainError(f"audit log tail corrupt at line {len(lines)}")

    entry = {
        "entry_id": str(uuid.uuid4()),
        "prev_sha256": prev,
        "action": action,
        "ts": datetime.now(timezone.utc).isoformat(),
        "operator": operator,
        "patch_id": patch_id,
        "skill_id": skill_id,
        "feedback_ids": feedback_ids or [],
        "eval_score": eval_score or {},
        "commit_sha": commit_sha,  # null for propose/reject
    }
    entry["entry_sha256"] = _compute_entry_sha256(prev, entry)

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry["entry_id"]
```

### Pattern 3: Audit Chain Verification (CURATE-03 `--verify`)
**What:** Walk the JSONL, recompute each `entry_sha256` from the prior entry's `entry_sha256`, compare.
**Example:**
```python
def verify_chain() -> list[dict]:
    """Walk audit log, recompute each entry_sha256, return breaks list."""
    path = _audit_log_path()
    if not path.exists():
        return []  # empty log = valid
    breaks = []
    prev = GENESIS_PREV_SHA256
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            breaks.append({"line": lineno, "error": "malformed JSON"})
            break  # cannot continue — chain broken
        expected_prev = entry.get("prev_sha256")
        if expected_prev != prev:
            breaks.append({"line": lineno, "error": f"prev_sha256 mismatch: expected {prev[:16]}, got {expected_prev[:16] if expected_prev else 'None'}"})
            # do NOT break — keep scanning to enumerate all breaks
        recomputed = _compute_entry_sha256(prev, entry)
        if recomputed != entry.get("entry_sha256"):
            breaks.append({"line": lineno, "error": "entry_sha256 mismatch (tampering detected)"})
        prev = entry.get("entry_sha256", prev)  # advance even on mismatch
    return breaks
```

### Anti-Patterns to Avoid
- **Calling `apply_patch_transaction` from `agent/curator.py`:** Breaks `TestNonBypassableHumanInLoop` (P31). The auto-apply must be CLI-side. See Architectural Constraint #1.
- **Placing audit log code under `agent/evolution/`:** Evolution subpackage is runtime-isolated per P31 invariant + runtime must append audit on propose. Audit module must be importable from runtime. Place at `agent/curator_audit.py`.
- **Using `json.dumps(entry)` WITHOUT `sort_keys=True` + `separators=(",",":")` for sha256 payload:** Chain verification will fail because dict key order / whitespace varies across Python versions / serialization paths. The formula in CONTEXT.md mandates `sort_keys=True, separators=(",",":")` — use EXACTLY these settings for both append and verify.
- **Skipping the feedback-scan phase on `Exception`:** Silent failure means bundled-skill proposals never happen. Log at WARNING, return an error dict, but do NOT abort the curator run (pre-v6 phases already completed).
- **Mutating pre-v6 `run_curator_review` code paths:** SC-6 regression test will fail. The feedback-scan is a NEW step appended at the end of `_llm_pass`, after the consolidation gate returns.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Feedback aggregation (LLM → insights) | New LLM call from curator | `agent.evolution.aggregate_feedback` (P31) | Already handles JSON parsing, Pydantic validation, retry-without-response_format. Reusing keeps one prompt + one schema. |
| Unified diff generation | Manual `@@ -A,B +C,D @@` string building | `difflib.unified_diff` (stdlib) via `generate_additive_diff` / new `generate_patch_from_knowledge_point` | P31 placeholder already solved anchor-uniqueness + frontmatter-immutability + idempotent-guard. Extending is cheaper + safer than forking. |
| Patch apply (atomic git commit + revert) | New git-invocation code in curator | `apply_patch_transaction` (P31) — via `_cmd_approve` delegation | The 6-step atomic transaction (dirty-tree guard, FOUND-08 byte-intact, additive-only check, revert-on-failure) is load-bearing and tested. Never re-implement. |
| Patch queue (JSONL pending/applied/rejected) | New queue in audit module | `agent.evolution.queue.{append_patch, read_queue, move_patch}` (P31) | The audit log records ACTIONS; the P31 queue records PATCHES. They are separate stores — do not conflate. |
| Hot-skill detection | New `list_skill_ids()` on FeedbackStore | Walk `self._index["buckets"]` keys (format `skill_id:source:verdict`) | FeedbackStore has NO `list_skill_ids()` method (see Pitfall #4). |
| Bilingual content composition | Manual string concatenation | A helper `_compose_bilingual_block(content_en, content_zh) -> str` | The CLAUDE.md convention (EN heading + body, then CN heading + body) is load-bearing for skill quality. Centralizing the format prevents drift. |

**Key insight:** Phase 32 is primarily a WIRING phase — it connects existing P29 (store) + P30 (gate) + P31 (evolution) machinery into the Curator runtime + operator CLI. The only genuinely new algorithm is the sha256 chain (15 lines) + the EVOL-02 bilingual composition helper. Everything else is delegation.

## Runtime State Inventory

> Phase 32 involves adding new persistence locations (`~/.hermes/skills/.audit/`) and extending runtime behavior. Answered per category.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | NEW: `~/.hermes/skills/.audit/log.jsonl` (sha256-chained audit entries). Existing: `~/.hermes/skills/.feedback/` (P29, read-only from P32), `~/.hermes/skills/.feedback/evolution/queue.jsonl` (P31, appended by curator-scan). | Create `.audit/` dir on first append. No migration — log starts empty (genesis = no entries). |
| Live service config | `cli-config.yaml` gains optional keys under `feedback.curator.*`: `feedback_threshold_count: 3`, `feedback_threshold_sessions: 2`, `auto_apply_enabled: false`, `auto_apply_min_delta: 0.1`, `auto_apply_min_evidence: 3`. | Code change in `agent/curator._load_config()` (or a new `_load_feedback_config()`). No external service reconfiguration. |
| OS-registered state | None. Curator runs in-process (CLI or gateway), no new OS registrations. | None. |
| Secrets/env vars | Reuses `OPENROUTER_API_KEY` (or `OPENAI_API_KEY` fallback) for EVOL-02 LLM calls — same as P31 `make_aggregation_client`. No new secrets. | None — P31 already validated this env path. |
| Build artifacts | No compiled artifacts. Pure-Python additions. | None — `uv pip install -e .` (standard dev loop) picks up new modules automatically. |

**The canonical question:** *After every file in the repo is updated, what runtime systems still have the old string cached, stored, or registered?*
- **Curator state (`~/.hermes/skills/.curator_state`)** — NOT affected. P32 adds a phase, doesn't change the state schema. `last_run_summary` will include feedback-scan results but that's additive to the string content, not a schema change.
- **FeedbackStore index (`~/.hermes/skills/.feedback/index.json`)** — NOT affected (read-only consumer).
- **P31 evolution queue files** — appended to, not migrated. Existing pending patches remain valid.

## Common Pitfalls

### Pitfall 1: Audit module placement under `agent/evolution/`
**What goes wrong:** Placing audit code at `agent/evolution/audit.py` makes it unreachable from runtime. The P31 invariant declares `agent/evolution/` to be "NOT imported by Hermes runtime (`run_agent.py`, `agent/conversation_loop.py`, `agent/curator.py`, `cli.py`, `gateway/`)" (`agent/evolution/__init__.py:3-5`). If `agent/curator.py` imports from `agent.evolution.audit`, it violates the invariant and `test_apply_patch_transaction_not_called_in_agent_or_runtime` may flag the import path.
**Why it happens:** "Audit log relates to evolution patches, so it belongs under evolution/" is intuitive but wrong.
**How to avoid:** Place audit code at `agent/curator_audit.py` (sibling of `curator.py`). Both runtime (`agent/curator.py`) and CLI (`hermes_cli/curator.py`, `hermes_cli/feedback.py`) can import it without crossing the evolution isolation boundary.
**Warning signs:** `ImportError` during curator run; P31 isolation test failures.

### Pitfall 2: sha256 chain break on JSON re-serialization
**What goes wrong:** The append code computes `entry_sha256` with `json.dumps(entry, sort_keys=True, separators=(",",":"))`, but the verify code uses default `json.dumps` (which adds whitespace) OR omits `sort_keys`. The chain "verifies" on append but fails on verify because the byte sequences differ.
**Why it happens:** `json.dumps` default kwargs differ from the compact form. `ensure_ascii` toggling also changes bytes.
**How to avoid:** Centralize the serialization in ONE function `_serialize_entry_for_sha256(entry: dict) -> str` used by BOTH append and verify. Pin `sort_keys=True, separators=(",",":"), ensure_ascii=False`. Test with a deliberate tamper (mutate one entry's `action` field) and confirm verify detects it.
**Warning signs:** `verify_chain()` returns breaks on a freshly-appended log; `ensure_ascii` mismatch between Python versions.

### Pitfall 3: EVOL-02 generator breaks frontmatter (FOUND-08)
**What goes wrong:** The bilingual composition inserts content into a SKILL.md in a way that shifts the `---` frontmatter block boundaries. `apply_patch_transaction`'s `verify_found08_byte_intact` then rejects the patch.
**Why it happens:** The P31 placeholder `generate_additive_diff` already guards against inserting INTO frontmatter (`_frontmatter_end_offset`), but the new EVOL-02 multi-instruction path may compose content that LOOKS additive but lands in a sensitive spot.
**How to avoid:** Reuse `_frontmatter_end_offset` in `generate_patch_from_knowledge_point`. For multi-instruction outputs, validate EACH instruction's `anchor_section` resolves to a unique site OUTSIDE the frontmatter block before composing the combined diff.
**Warning signs:** `ApplyError("FOUND-08 violation: frontmatter bytes drifted")` from `_cmd_approve`.

### Pitfall 4: FeedbackStore has no `list_skill_ids()` method
**What goes wrong:** CONTEXT.md research question #6 sketched a scan using `store.list_skill_ids()` — that method DOES NOT EXIST. Calling it raises `AttributeError`.
**Why it happens:** Assumption based on common store APIs; P29 FeedbackStore exposes `query` / `summary` / `get_record` only.
**How to avoid:** Iterate the index directly:
```python
def _scan_for_hot_skills(store, *, threshold_count=3, threshold_sessions=2) -> list[str]:
    hot = []
    seen_skills = set()
    for bucket_key in store._index.get("buckets", {}):
        parts = bucket_key.split(":")
        if len(parts) != 3:
            continue
        skill_id, source, verdict = parts
        if verdict not in ("needs_work", "bad"):
            continue
        if skill_id in seen_skills:
            continue
        seen_skills.add(skill_id)
        # Sum negative-verdict counts across ALL sources for this skill.
        neg_total = 0
        for sk2 in ("needs_work", "bad"):
            for src2 in ("cli", "kais_aigc", "manual"):
                k = f"{skill_id}:{src2}:{sk2}"
                b = store._index["buckets"].get(k, {})
                neg_total += b.get("count", 0)
        if neg_total < threshold_count:
            continue
        # Session diversity: count distinct session_ids in raw records.
        records = store.query(skill_id=skill_id, verdict="needs_work")
        records += store.query(skill_id=skill_id, verdict="bad")
        sessions = {getattr(r, "session_id", None) for r in records}
        sessions.discard(None)
        if len(sessions) >= threshold_sessions:
            hot.append(skill_id)
    return hot
```
Note: this reads `store._index` (private). A cleaner path is `store.summary()` which returns the buckets dict. But `summary()` does not expose `session_id` diversity — that requires `query()`. The sketch above combines both.
**Warning signs:** `AttributeError: 'FeedbackStore' object has no attribute 'list_skill_ids'`.

### Pitfall 5: Regression — pre-v6 curator behavior changes (SC-6)
**What goes wrong:** Editing `run_curator_review` to add the feedback-scan phase accidentally changes the order of operations or the state mutations of the pre-v6 path. Existing tests `tests/agent/test_curator*.py` (5 files) fail.
**Why it happens:** The function is 250+ lines with non-obvious state interactions (`save_state` called multiple times, `_llm_pass` closure).
**How to avoid:** The feedback-scan phase is a SEPARATE FUNCTION called from the END of `_llm_pass`, AFTER all pre-v6 state writes + report writes have completed. Do NOT inline it into the existing flow. Write the regression test FIRST (see Validation Architecture).
**Warning signs:** Any test in `tests/agent/test_curator*.py` fails after the change.

### Pitfall 6: Concurrency — curator runs while operator invokes CLI
**What goes wrong:** Curator runs in a daemon thread (`run_curator_review(synchronous=False)`). If the operator simultaneously runs `hermes curator approve`, both may write to `queue.jsonl` / `log.jsonl`. JSONL append is not cross-process atomic (P31 RESEARCH Pitfall 5).
**Why it happens:** Gateway deployments trigger curator in background while operators interact via CLI.
**How to avoid:** v6 is single-operator per CONTEXT.md. Document the limitation in the audit module docstring. If race manifests, the worst case is a duplicate `patch_id` (content-addressed, detectable on read) or a corrupt audit line (caught by `verify_chain`). DO NOT add `fcntl.flock` in v6 — deferred.
**Warning signs:** Corrupt JSONL lines; `verify_chain` reports malformed JSON at a specific line.

### Pitfall 7: CURATE-05 auto-apply on a bundled skill
**What goes wrong:** Auto-apply fires on a bundled skill patch. SC-3 from P31 ("bundled NEVER auto") is violated.
**Why it happens:** The confidence check passes but the bundled-vs-agent-created gate is missing or uses the wrong check.
**How to avoid:** Use `tools.skill_usage.is_agent_created(skill_id)` (returns `True` ONLY for non-bundled, non-hub skills). Auto-apply requires `is_agent_created == True`. Bundled OR hub-installed → never auto, regardless of confidence. Add an explicit test `test_auto_apply_refuses_bundled_skill`.
**Warning signs:** A bundled SKILL.md changes without an operator `approve` in the audit log.

### Pitfall 8: `ensure_ascii` mismatch in audit log sha256
**What goes wrong:** The append path uses `ensure_ascii=False` (so CN content in `feedback_ids` or `eval_score` round-trips), but the verify path uses default `ensure_ascii=True`. The byte sequences differ; chain breaks.
**Why it happens:** `json.dumps` default is `ensure_ascii=True`. Without an explicit pin, the two paths diverge.
**How to avoid:** Pin `ensure_ascii=False` in the centralized `_serialize_entry_for_sha256` helper (see Pitfall #2). Test with a CN-laden `feedback_ids` value.
**Warning signs:** `verify_chain` fails only on entries containing non-ASCII content.

## Code Examples

### EVOL-02 Generator Extension
```python
# Source: extends agent/evolution/diff_generator.py (P31 placeholder)
# File: agent/evolution/diff_generator.py (add to existing module) OR
#       agent/evolution/evol02_generator.py (new sibling module)

from __future__ import annotations
import difflib, logging
from pathlib import Path
from agent.evolution.insights import InsightRecord
from agent.evolution.diff_generator import (
    _frontmatter_end_offset, generate_additive_diff,
)

logger = logging.getLogger(__name__)


def _compose_bilingual_block(content_en: str, content_zh: str) -> str:
    """Compose a bilingual EN+CN block per CLAUDE.md convention.

    EN heading + body, blank line, CN heading + body.
    """
    return f"{content_en.strip()}\n\n{content_zh.strip()}\n"


def generate_patch_from_knowledge_point(
    *,
    insight: InsightRecord,
    current_files: dict[str, str],  # {repo_relative_path: file_content}
    instructions: list[dict],       # LLM-emitted structured instructions
) -> str:
    """Generate a multi-file unified diff from a knowledge point (EVOL-02).

    instructions schema (from LLM):
        [{"file": "skills/.../references/x.md",
          "anchor_section": "## Three-Act Structure",
          "add_after": True,
          "content_en": "...",
          "content_zh": "..."}]

    Returns a combined unified diff string covering all instructions.
    Raises ValueError on: missing file, missing/duplicate anchor, frontmatter
    insertion attempt, idempotent no-op.
    """
    combined_diffs: list[str] = []
    for instr in instructions:
        file_path = instr["file"]
        if file_path not in current_files:
            raise ValueError(f"instruction references unknown file: {file_path!r}")
        current = current_files[file_path]
        anchor = instr["anchor_section"]
        block = _compose_bilingual_block(instr["content_en"], instr["content_zh"])
        # Reuse the P31 placeholder's hardened single-block generator.
        single_diff = generate_additive_diff(
            current_content=current,
            proposed_addition=block,
            insert_after_marker=anchor,
            skill_md_path=file_path,
        )
        combined_diffs.append(single_diff)
        # CRITICAL: update current_files so subsequent instructions against
        # the SAME file see the already-mutated content (anchor offsets shift).
        # Re-derive current by applying the single_diff — or simpler, compose
        # the final-state string and let difflib diff original→final.
        current_files[file_path] = _apply_diff_to_content(current, single_diff, file_path)

    return "\n".join(combined_diffs) if len(combined_diffs) > 1 else combined_diffs[0]
```

**Note:** The multi-instruction-against-same-file case is subtle. The cleanest implementation builds the FINAL file content for each touched file (apply all instructions sequentially in-memory), then generates ONE unified_diff per file from original→final. The sketch above (per-instruction diff + content mutation) works but produces multiple hunks that `git apply` must handle sequentially. The planner should pick one approach and test it.

### Curator CLI Subparser Registration
```python
# Source: extends hermes_cli/curator.py:register_cli
# Add AFTER the existing p_rollback block:

# ── v6 Curator Upgrade subcommands (CURATE-04) ──────────────────────────
p_queue = subs.add_parser(
    "queue",
    help="List pending evolution patches (delegates to `hermes feedback review-queue`)",
)
p_queue.add_argument("--skill", dest="skill", default=None,
                     help="Filter by skill_id")
p_queue.add_argument("--status", dest="status", default="pending",
                     choices=["pending", "applied", "rejected"],
                     help="Patch status filter (default: pending)")
p_queue.set_defaults(func=_cmd_queue)

p_approve = subs.add_parser(
    "approve",
    help="Approve + apply a pending patch (delegates to `hermes feedback approve`)",
)
p_approve.add_argument("patch_id", help="Patch ID from `hermes curator queue`")
p_approve.add_argument("-y", "--yes", action="store_true",
                       help="Confirm apply (required — no default-yes)")
p_approve.set_defaults(func=_cmd_approve_curator)

p_reject = subs.add_parser(
    "reject",
    help="Reject a pending patch (delegates to `hermes feedback reject`)",
)
p_reject.add_argument("patch_id")
p_reject.add_argument("reason", help="Rejection reason (recorded in audit log)")
p_reject.set_defaults(func=_cmd_reject_curator)

p_audit = subs.add_parser(
    "audit-log",
    help="Inspect the patch audit trail (~/.hermes/skills/.audit/log.jsonl)",
)
p_audit.add_argument("--action", dest="action", default=None,
                     choices=["propose", "approve", "reject", "apply",
                              "rollback", "auto_apply"])
p_audit.add_argument("--since", dest="since", default=None,
                     help="ISO date lower bound (e.g., 2026-06-01)")
p_audit.add_argument("--skill", dest="skill", default=None)
p_audit.add_argument("--verify", dest="verify", action="store_true",
                     help="Walk the sha256 chain and report breaks")
p_audit.set_defaults(func=_cmd_audit_log)


def _cmd_queue(args) -> int:
    """Thin wrapper — delegates to P31 _cmd_review_queue."""
    from hermes_cli.feedback import _cmd_review_queue
    return _cmd_review_queue(args)


def _cmd_approve_curator(args) -> int:
    """Thin wrapper — delegates to P31 _cmd_approve.
    Then appends audit-log entry (action=apply) via agent.curator_audit.
    """
    from hermes_cli.feedback import _cmd_approve
    rc = _cmd_approve(args)
    if rc == 0:
        # Append audit entry (best-effort — never block approve on audit failure).
        try:
            from agent.curator_audit import append_audit
            append_audit(action="apply", patch_id=args.patch_id,
                         skill_id="<resolved-from-patch>", operator=_get_operator(),
                         commit_sha="<resolved-from-move-patch>")
        except Exception as e:
            logging.getLogger(__name__).warning("audit log append failed: %s", e)
    return rc


def _cmd_audit_log(args) -> int:
    """CURATE-03 — query and optionally verify the audit trail."""
    from agent.curator_audit import read_audit, verify_chain
    if getattr(args, "verify", False):
        breaks = verify_chain()
        if breaks:
            print(f"audit chain: {len(breaks)} break(s) detected:")
            for b in breaks:
                print(f"  line {b['line']}: {b['error']}")
            return 1
        print("audit chain: OK (all entries verify)")
        return 0
    entries = read_audit(action=args.action, since=args.since, skill=args.skill)
    for e in entries:
        print(f"{e['ts']} {e['action']:10s} {e['patch_id']} skill={e['skill_id']}")
    return 0
```

**Note on the audit-append integration:** The cleanest path is for `_cmd_approve` (in `hermes_cli/feedback.py`) ITSELF to call `append_audit(action="apply")` after a successful `move_patch`. That way every caller (curator wrapper, direct `hermes feedback approve`) gets the audit entry automatically. The planner should decide: modify `_cmd_approve` to call `append_audit` (single source of truth) OR keep audit-logging in the curator wrapper (requires operator to use `hermes curator approve` rather than `hermes feedback approve` to get audit). [RECOMMENDED: modify `_cmd_approve` directly.]

### Pre-v6 Curator Regression Test Pattern
```python
# Source: tests/agent/test_curator_regression.py (NEW)
"""SC-6 regression — pre-v6 curator behavior preserved after P32 extension.

These tests verify the DETERMINISTIC inactivity transitions + consolidation
gate run UNCHANGED when the v6 feedback-scan phase is added. The feedback
scan is ADDITIVE and must not alter:
  - apply_automatic_transitions counts (marked_stale / archived / reactivated)
  - state.last_run_at / run_count increments
  - report generation (REPORT.md still written with pre-v6 structure)
  - consolidate=False path (prune-only, no LLM cost)
"""
import pytest
from datetime import datetime, timezone, timedelta
from agent import curator


class TestPreV6Regression:
    """Every test here MUST pass identically on pre-v6 + post-v6 curator."""

    def test_inactivity_transitions_unchanged(self, tmp_path, monkeypatch):
        """apply_automatic_transitions returns the same counts regardless
        of whether the feedback-scan phase is wired in."""
        # Setup: agent-created skill idle > archive_after_days
        # Assert: counts == expected (same as pre-v6)
        ...

    def test_consolidate_false_skips_llm(self, tmp_path, monkeypatch):
        """consolidate=False → no LLM call, no feedback-scan, prune-only."""
        # Stub _run_llm_review to detect calls
        # Run curator.run_curator_review(consolidate=False, synchronous=True)
        # Assert: LLM not called, feedback-scan not triggered
        ...

    def test_dry_run_no_state_mutation(self, tmp_path, monkeypatch):
        """dry_run=True → state.last_run_at NOT bumped, run_count NOT bumped.
        Pre-v6 behavior: dry-run is preview-only."""
        ...

    def test_no_feedback_no_scan(self, tmp_path, monkeypatch):
        """When FeedbackStore has zero records, feedback-scan is a no-op
        and curator behaves identically to pre-v6."""
        ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Curator = agent-created skill archiver only | Curator = archiver + bundled-skill patch proposer (P32) | v6.0 (this phase) | Curator now writes to P31 review queue + audit log; scope expansion explicitly accepted in PROJECT.md |
| Patch generation = P31 placeholder (single-block additive) | Patch generation = EVOL-02 (multi-instruction, bilingual) | v6.0 (this phase) | `generate_patch_from_knowledge_point` extends placeholder; insights.py prompt may need a companion `EVOL02_SYSTEM_PROMPT` for the instruction-emit call |
| No audit trail | sha256-chained JSONL audit | v6.0 (this phase) | New `~/.hermes/skills/.audit/log.jsonl`; append-only; verifiable |
| `apply_patch_transaction` called only from `_cmd_approve` | SAME (P32 does NOT weaken this) | P31 → P32 | Structural invariant test `TestNonBypassableHumanInLoop` continues to pass |

**Deprecated/outdated:**
- None this phase. P32 extends, does not deprecate.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `entry_id = str(uuid.uuid4())` is the right ID format for audit entries | Code Examples (Pattern 2) | LOW — any unique string works; uuid4 is the Hermes convention |
| A2 | The LLM for EVOL-02 instruction emission reuses `make_aggregation_client` from P31 (same `OPENROUTER_API_KEY`) | EVOL-02 Generator Design | LOW — P31's client works; if a different model is desired, add `HERMES_EVOL02_MODEL` env var (mirrors P31 pattern) |
| A3 | `feedback_threshold_sessions` can be derived from FeedbackRecord having a `session_id` field | Pitfall #4 sketch | MEDIUM — if FeedbackRecord has no `session_id` field, session-diversity check needs a different signal (e.g., distinct `ts` days). Verify in `agent/feedback_schema.py` before planning. |
| A4 | Modifying `_cmd_approve` in `hermes_cli/feedback.py` to call `append_audit` is safer than wrapping in curator CLI | Code Examples note | LOW — single source of truth; the alternative (wrapper-only) creates an audit-gap when operators use `hermes feedback approve` directly |

**Planner action:** Validate A3 early in Plan 01 by reading `agent/feedback_schema.py` for the FeedbackRecord schema. If `session_id` is absent, fall back to "distinct UTC dates" as the session proxy.

## Open Questions (RESOLVED at plan-phase 2026-06-24)

1. **Does `FeedbackRecord` carry a `session_id` field?**
   - What we know: CONTEXT.md research question #6 sketch references `session_id` in raw records.
   - What's unclear: Whether P28/P29 added `session_id` to the Pydantic schema, or whether it lives only in `output_snapshot.metadata`.
   - RESOLVED: FeedbackRecord has NO `session_id` field (verified via Wave 0 read of `agent/feedback_schema.py`). Use distinct UTC calendar days derived from `record.ts.date()` as the session-diversity proxy. Documented in `_scan_for_hot_skills` docstring (Plan 01 Task 4).

2. **Should EVOL-02 LLM instruction emission be a SEPARATE LLM call, or fold into P31's `aggregate_feedback`?**
   - What we know: P31's `aggregate_feedback` returns `InsightRecord` with `proposed_addition` (markdown) + `insert_after_marker`. EVOL-02 needs structured `{file, anchor_section, content_en, content_zh}` instructions.
   - What's unclear: Whether to extend `InsightRecord` with instruction fields OR add a second LLM pass that converts an InsightRecord into instructions.
   - RESOLVED: Add a second LLM pass (`emit_evol02_instructions(insight, current_files) -> list[dict]`) — keeps P31's `aggregate_feedback` unchanged (no P31 regression risk). Implemented in Plan 01 Task 3.

3. **Should the audit log record `propose` actions given they are system-generated and high-volume?**
   - What we know: CONTEXT.md lists `propose` as a valid action.
   - What's unclear: Whether every curator scan logging 10+ `propose` entries pollutes the audit trail.
   - RESOLVED: Log `propose` — it's the only way to trace "why did this patch enter the queue?" Operator can filter via `--action apply` for the common case. Volume is bounded by `feedback_threshold` (scans only fire for hot skills). Implemented in Plan 01 Task 4.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `OPENROUTER_API_KEY` env var | EVOL-02 LLM instruction emission | ✓ (P28-P31 depend on it) | — | `--dry-run` skips LLM (P31 pattern) |
| Git CLI | `apply_patch_transaction` (CURATE-05 auto-apply, via `_cmd_approve`) | ✓ (P31 verified) | — | No fallback — git is required for patch apply |
| `~/.hermes/skills/.audit/` writable path | Audit log append (CURATE-03) | ✓ (HERMES_HOME is writable per P28-P31) | — | None — audit log is required |
| Python 3.11+ stdlib (`hashlib`, `difflib`, `json`, `uuid`, `argparse`) | All P32 code | ✓ (project floor) | 3.13 in `ty` | — |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** None — all required deps are already verified by P28-P31.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 + pytest-timeout 2.4.0 (`[dev]` extra, per `pyproject.toml:261`) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (30s per-test timeout, `addopts` in `pyproject.toml:261`) |
| Quick run command | `python -m pytest tests/agent/test_curator_audit.py tests/agent/evolution/test_evol02_generator.py -x --timeout=30` |
| Full suite command | `python scripts/run_tests_parallel.py` (per-file subprocess parallelism per CLAUDE.md) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CURATE-01 | Curator feedback-scan proposes bundled-skill patches | unit | `pytest tests/agent/test_curator_feedback_scan.py::test_propose_hot_bundled_skill -x` | ❌ Wave 0 |
| CURATE-01 (SC-6) | Pre-v6 curator behavior preserved | unit (regression) | `pytest tests/agent/test_curator_regression.py -x` | ❌ Wave 0 |
| CURATE-02 | Threshold detection (≥3 neg across ≥2 sessions) | unit | `pytest tests/agent/test_curator_feedback_scan.py::test_threshold_detection -x` | ❌ Wave 0 |
| CURATE-02 | Below-threshold skill NOT proposed | unit | `pytest tests/agent/test_curator_feedback_scan.py::test_below_threshold_no_propose -x` | ❌ Wave 0 |
| CURATE-03 | Audit append + sha256 chain | unit | `pytest tests/agent/test_curator_audit.py::TestSha256Chain -x` | ❌ Wave 0 |
| CURATE-03 | `verify_chain` detects tampering | unit | `pytest tests/agent/test_curator_audit.py::test_verify_detects_tamper -x` | ❌ Wave 0 |
| CURATE-03 | `--verify` on empty log returns OK | unit | `pytest tests/agent/test_curator_audit.py::test_verify_empty_log -x` | ❌ Wave 0 |
| CURATE-03 | Query filters (action/since/skill) | unit | `pytest tests/agent/test_curator_audit.py::TestQueryFilters -x` | ❌ Wave 0 |
| CURATE-04 | `hermes curator queue` lists pending | smoke (CLI) | `pytest tests/hermes_cli/test_curator_cli.py::test_queue_lists_pending -x` | ❌ Wave 0 |
| CURATE-04 | `hermes curator approve --yes` applies | smoke (CLI) | `pytest tests/hermes_cli/test_curator_cli.py::test_approve_applies -x` | ❌ Wave 0 |
| CURATE-04 | `hermes curator audit-log --verify` walks chain | smoke (CLI) | `pytest tests/hermes_cli/test_curator_cli.py::test_audit_log_verify -x` | ❌ Wave 0 |
| CURATE-04 | `approve` delegates to P31 `_cmd_approve` (single source of truth) | structural | `pytest tests/hermes_cli/test_curator_cli.py::test_approve_delegates_to_p31 -x` | ❌ Wave 0 |
| CURATE-05 | Auto-apply refuses bundled skill | unit | `pytest tests/agent/test_curator_feedback_scan.py::test_auto_apply_refuses_bundled -x` | ❌ Wave 0 |
| CURATE-05 | Auto-apply fires for agent-created skill when two-signal confidence met | unit | `pytest tests/agent/test_curator_feedback_scan.py::test_auto_apply_agent_created -x` | ❌ Wave 0 |
| CURATE-05 | Auto-apply default OFF | unit | `pytest tests/agent/test_curator_feedback_scan.py::test_auto_apply_default_off -x` | ❌ Wave 0 |
| CURATE-05 (P31 invariant) | `apply_patch_transaction` still only called from `_cmd_approve` | structural (existing) | `pytest tests/hermes_cli/test_evolution_cli.py::TestNonBypassableHumanInLoop -x` | ✅ P31 shipped |
| EVOL-02 | Bilingual content composition (EN + CN headings) | unit | `pytest tests/agent/evolution/test_evol02_generator.py::test_bilingual_composition -x` | ❌ Wave 0 |
| EVOL-02 | Multi-instruction single-file diff | unit | `pytest tests/agent/evolution/test_evol02_generator.py::test_multi_instruction_single_file -x` | ❌ Wave 0 |
| EVOL-02 | Anchor validation (missing / duplicate) | unit | `pytest tests/agent/evolution/test_evol02_generator.py::test_anchor_validation -x` | ❌ Wave 0 |
| EVOL-02 | Frontmatter not touched | unit | `pytest tests/agent/evolution/test_evol02_generator.py::test_frontmatter_preserved -x` | ❌ Wave 0 |
| EVOL-02 | Output compatible with `apply_patch_transaction` | integration | `pytest tests/agent/evolution/test_evol02_generator.py::test_diff_applies_clean -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/agent/test_curator_audit.py tests/agent/evolution/test_evol02_generator.py tests/agent/test_curator_regression.py -x --timeout=30`
- **Per wave merge:** `pytest tests/agent/test_curator*.py tests/agent/evolution/ tests/hermes_cli/test_curator_cli.py tests/hermes_cli/test_evolution_cli.py -x --timeout=60` (includes P31 regression — `TestNonBypassableHumanInLoop` MUST stay green)
- **Phase gate:** Full suite green before `/gsd:verify-work`. Pay special attention to:
  - `tests/agent/test_curator*.py` (5 pre-existing files — SC-6 regression)
  - `tests/hermes_cli/test_evolution_cli.py::TestNonBypassableHumanInLoop` (P31 structural invariant — MUST still pass)

### Wave 0 Gaps
- [ ] `tests/agent/test_curator_feedback_scan.py` — covers CURATE-01, CURATE-02, CURATE-05 (threshold detection, EVOL pipeline invocation, auto-apply refuse/fire)
- [ ] `tests/agent/test_curator_regression.py` — covers SC-6 (pre-v6 curator behavior preserved)
- [ ] `tests/agent/test_curator_audit.py` — covers CURATE-03 (append, verify, tamper, query filters)
- [ ] `tests/agent/evolution/test_evol02_generator.py` — covers EVOL-02 (bilingual, multi-instruction, anchor validation)
- [ ] `tests/hermes_cli/test_curator_cli.py` — covers CURATE-04 (queue/approve/reject/audit-log CLI smoke + delegation)
- [ ] Confirm `agent/feedback_schema.py` has `session_id` (or decide proxy) — resolves Open Question #1

*(If no gaps: N/A — this is a new-feature phase, all test files are new.)*

## Security Domain

> `security_enforcement` is not explicitly set in `.planning/config.json`, so it defaults to enabled. Include this section.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — curator runs as the logged-in operator; no new auth surface |
| V3 Session Management | no | N/A — no new session surface |
| V4 Access Control | yes | Operator CLI gated; auto-apply default OFF; bundled skills NEVER auto-apply (CURATE-05) |
| V5 Input Validation | yes | Pydantic for PatchRecord (P31) + AuditEntry; LLM-output validation via Pydantic (P31 `InsightRecord` pattern) |
| V6 Cryptography | yes | sha256 chain (stdlib `hashlib`) — never hand-roll; genesis prev = `sha256("").hexdigest()` |
| V7 Error Handling & Logging | yes | Lazy %-logging; audit log is append-only; never log `OPENROUTER_API_KEY` (P31 pattern) |
| V8 Data Protection | yes | `feedback_ids` in audit log may contain user corrections; v6 assumes trusted operator environment (FUTURE-V6-06 deferred) |

### Known Threat Patterns for Phase 32 Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Audit log tampering (edit/delete a line to hide an apply) | Tampering | sha256 chain makes silent edits detectable via `--verify`. Append-only — no edit API. |
| LLM injects malicious content into EVOL-02 instructions (prompt injection) | Elevation of Privilege | (1) `apply_patch_transaction` rejects non-additive patches; (2) FOUND-08 byte-intact check rejects frontmatter drift; (3) T-31-04 path-traversal guard rejects `..` and paths outside `skills/movie-experts/`; (4) human-in-loop approve (EVOL-04) for bundled skills |
| Auto-apply fires on bundled skill (SC-3 violation) | Repudiation | Explicit `is_agent_created(skill_id) == True` check before auto-apply; `test_auto_apply_refuses_bundled_skill` regression test |
| Curator feedback-scan phase crashes main curator run | Denial of Service | Feedback-scan wrapped in try/except; logs WARNING, returns error dict, does NOT abort the curator run (pre-v6 phases already completed) |
| `apply_patch_transaction` called outside `_cmd_approve` (EVOL-04 bypass) | Elevation of Privilege | P31 structural invariant test (`TestNonBypassableHumanInLoop`) blocks merge if any new caller appears |

## Sources

### Primary (HIGH confidence)
- `agent/curator.py` — existing runtime; extension point is the END of `_llm_pass` closure (line 1517+) after the consolidation gate
- `agent/evolution/__init__.py:3-5` — runtime isolation declaration ("NOT imported by Hermes runtime")
- `agent/evolution/diff_generator.py` — P31 placeholder to extend
- `agent/evolution/insights.py` — `aggregate_feedback` + `InsightRecord` + `make_aggregation_client` (dependency-injection pattern)
- `agent/evolution/queue.py` — `PatchRecord` + `append_patch` + `read_queue` + `move_patch` (P31 queue lifecycle)
- `agent/evolution/apply.py` — `apply_patch_transaction` (6-step atomic transaction) + `build_commit_message`
- `agent/feedback_store.py:990` (summary), `:919` (query), `:693` (_load_or_init_index — index schema)
- `hermes_cli/curator.py:495` (register_cli — extension point)
- `hermes_cli/feedback.py:828` (_cmd_approve — the SOLE apply caller), `:920` (_cmd_rollback)
- `tools/skill_usage.py:415` (is_agent_created — CURATE-05 bundled check)
- `tests/hermes_cli/test_evolution_cli.py:846-953` (TestNonBypassableHumanInLoop — the governing structural invariant)
- `.planning/phases/32-curator-upgrade-audit/32-CONTEXT.md` — locked decisions

### Secondary (MEDIUM confidence)
- `.planning/ROADMAP.md` Phase 32 success criteria (SC-1 through SC-6)
- `.planning/STATE.md` P31 closure notes (87 tests green, non-bypassable human-in-loop structurally enforced)
- `cli.py:11716` + `gateway/run.py:16550` — confirmed lazy `from agent.curator import maybe_run_curator` (no circular-import risk from P32 extension as long as audit module is not under `agent/evolution/`)

### Tertiary (LOW confidence)
- None — all claims verified against in-repo source.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new deps; all stdlib or existing in-repo modules
- Architecture: HIGH — extension points + integration points verified by reading source; P31 structural invariant is the governing constraint
- Pitfalls: HIGH — 8 pitfalls identified, all grounded in specific code observations (P31 test, FeedbackStore missing method, frontmatter drift, sha256 serialization)
- Auto-apply path: MEDIUM — the routing-through-`_cmd_approve` constraint is HIGH-confidence (test exists), but the exact UX (wrapper vs modify-in-place) is an Open Question for the planner

**Research date:** 2026-06-24
**Valid until:** 2026-07-24 (30 days — stable; P31 test invariant will not change without an explicit milestone decision)
