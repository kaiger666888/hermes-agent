# Phase 65: CURATOR-LIVE-GUARDS - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous smart-discuss — infrastructure + new CLI flag + canary wiring)

<domain>
## Phase Boundary

Add safety guards to curator self-evolution enabling a future live tick (Phase 66). Default behavior UNCHANGED — `dry_run=True` per v11.0 EVAL-06 invariant. New opt-in `--live` flag + pre-tick bias canary check + post-tick audit log chain.

**In scope:**
1. NEW `hermes curator evolve` subcommand (no existing `evolve` subcommand; existing `curator.py:run_curator_review(dry_run=True)` is the target function)
2. NEW `--live` flag on `evolve` subcommand (default: dry-run; opt-in live)
3. Pre-tick bias canary check: run `agent.curator_bias_canary.check_record` against 5 seeded known-bad records; abort live tick if <4/5 caught (per v12.0 EVAL-03 baseline)
4. Post-tick audit log: every live write emits sha256-tagged entry to `~/.hermes/skills/.audit/log.jsonl` (existing audit chain in `agent/curator_audit.py`)

**Strictly out of scope:**
- 1st actual live tick (Phase 66)
- Automated rollback (operator 24h review + manual rollback only, per STATE.md deferred)
- Bias canary threshold tuning (use v12.0 EVAL-03 baseline ≥4/5 as-is)
- New audit chain format (extend existing sha256 chain)

</domain>

<decisions>
## Implementation Decisions

### Locked-from-prior-phases

- **dry_run default:** `True` (curator.py:1942, v11.0 EVAL-06 invariant) — Phase 65 preserves this default; only adds opt-in `--live` path
- **Bias canary API:** `agent.curator_bias_canary.check_record(record: dict) -> CanaryReport` (line 261) — Phase 65 reuses, does not modify
- **Audit chain:** `agent.curator_audit` with sha256-chained entries (GENESIS_PREV_SHA256 at line 63, `_audit_log_path()` at line 95) — Phase 65 extends with live-tick tag
- **Audit log location:** `~/.hermes/skills/.audit/log.jsonl` (confirmed exists)
- **Curator CLI pattern:** `hermes_cli/curator.py:register_cli` adds subcommands via `subs.add_parser(name, ...).set_defaults(func=_cmd_xxx)` — Phase 65 follows this pattern
- **Live tick precondition:** `dry_run=False AND bias_canary_pass=True` — only then proceed to live writes

### Claude's Discretion

**G1: `evolve` subcommand design**
- **Option A (recommended):** NEW standalone subcommand `hermes curator evolve` — distinct from `hermes curator run` (which is dry-run status-only). `evolve --live` does the actual memory mutation; `evolve` (no flag) is the dry-run preview.
- **Option B:** Extend existing `hermes curator run` with `--live` flag — overload existing command
- Recommendation: A — cleaner separation; `run` stays dry-run preview, `evolve --live` is the explicit mutation path. Matches MEMORY.md "feedback-glm-overload-reduce-concurrency" pattern (explicit opt-in for state mutation).

**G2: Bias canary seed records source**
- **Option A (recommended):** Bundle 5 known-bad fixture records in `tests/fixtures/curator_bias_canary/known_bad_records.jsonl` — test-reproducible, version-controlled
- **Option B:** Generate at runtime via deterministic fuzzer — no fixture files needed but harder to reason about
- **Option C:** Use v12.0 EVAL-03 baseline records from `.planning/research/v12-*` — reuse existing artifacts
- Recommendation: A — fixtures make canary semantics explicit; C means coupling Phase 65 to v12.0 research artifacts which may move

**G3: Audit log entry extension**
Existing audit chain entries have sha256 + timestamp. Phase 65 needs to mark "this entry came from a live tick". Options:
- **Option A (recommended):** Add `tick_mode: "live"` field to entry dict — sha256 still chains; field is informational
- **Option B:** Use separate `live_ticks.jsonl` for live ticks only — split audit trail
- Recommendation: A — single chain preserves integrity; `tick_mode` field makes filtering trivial

**G4: Canary failure UX**
When bias canary fails (<4/5 caught) on a `--live` invocation, what happens?
- **Option A (recommended):** Exit code 2 + structured error message `BIAS_CANARY_FAILED: caught N/5 (threshold: 4); live tick aborted; run 'hermes curator evolve' (no --live) for dry-run preview`
- **Option B:** Exit code 1 + plain error message
- **Option C:** Interactive prompt to proceed anyway
- Recommendation: A — exit code 2 distinguishes canary failure from generic error; structured message is grep-friendly for runbook automation

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- **`agent/curator.py:1942`** — `run_curator_review(dry_run: bool = True, ...)` existing function. Phase 65 calls with `dry_run=False` when `--live` passed AND canary passes.
- **`agent/curator_bias_canary.py:261`** — `check_record(record) -> CanaryReport` function. Phase 65 calls 5 times against seed records, counts caught.
- **`agent/curator_bias_canary.py:237`** — `CanaryReport` dataclass with `to_dict()` serialization
- **`agent/curator_audit.py`** — full audit chain module (genesis, append, verify)
- **`hermes_cli/curator.py:1238`** — `register_cli` function — Phase 65 adds `evolve` subcommand here

### Established Patterns

- **Curator CLI convention:** `p_xxx = subs.add_parser("xxx", ...); p_xxx.set_defaults(func=_cmd_xxx)` (curator.py:1247+)
- **Lazy %-formatting** in all logger calls
- **`from __future__ import annotations`** at module top
- **`get_hermes_home()`** for path resolution (NEVER `Path.home() / ".hermes"`)
- **`encoding="utf-8"`** on every open()
- **Specific exceptions** (no bare `except:`)

### Integration Points

- **Bias canary threshold:** `>= 4/5 catch rate` (v12.0 EVAL-03 baseline — frozen)
- **Audit log path:** `~/.hermes/skills/.audit/log.jsonl` (existing — extend with `tick_mode` field)
- **EXIT codes:** 0 (success), 1 (generic error), 2 (canary failure — Phase 65 introduces)
- **Phase 66 handoff:** Phase 66 runs the actual 1st live tick — Phase 65 ships the guards but does NOT invoke live mode itself

</code_context>

<specifics>
## Specific Ideas

- Canary check should be a separate function `run_bias_canary_pre_check(seed_records_path: Path) -> tuple[bool, int, list[str]]` returning (pass, caught_count, failed_record_ids). Called by `evolve` CLI when `--live` is set.
- `--live` flag should also accept `--skip-canary` for emergency use (operator-only escape hatch), documented in help text as "DANGEROUS: skip bias canary pre-check"
- Audit log entries for live ticks should include: `sha256`, `prev_sha256`, `timestamp`, `tick_mode: "live"`, `dry_run: false`, `canary_pass: true`, `caught_count: N`, `agent_id` (if applicable), `mutation_summary` (skill_ids affected + action verb)

</specifics>

<deferred>
## Deferred Ideas

- **1st actual live tick** — Phase 66 (CURATOR-LIVE-TICK)
- **Automated rollback** — too complex; v13.0 uses operator 24h review + manual rollback
- **Bias canary tuning** — v12.0 EVAL-03 baseline retained as-is
- **Prometheus/Grafana audit dashboards** — v14+ scope (v13 uses grep + manual inspection)
- **Multi-operator audit chain** — v13 assumes single-operator (PROJECT.md v6 decision)

</deferred>
