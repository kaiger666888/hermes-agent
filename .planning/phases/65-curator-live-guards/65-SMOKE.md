# Phase 65 Integration Smoke — Curator Live Guards

> Wave 2 end-to-end smoke evidence for the 3 Phase 65 success criteria (CURATE-01, CURATE-02, CURATE-03). Captured by Plan 65-03 on 2026-07-08 against worktree base `3452ee914` (post-Wave 1).

---

## SC#1 — `hermes curator evolve` defaults to dry-run (operator-visible DRY RUN marker)

**Requirement:** CURATE-01 — default path is a dry-run preview; operator-visible DRY RUN marker in stdout; exit 0.

**Command:**

```bash
SMOKE_TMP=$(mktemp -d)
HERMES_HOME="$SMOKE_TMP" python3 -m hermes_cli.curator evolve
echo "EXIT=$?"
ls "$SMOKE_TMP/skills/.audit/" 2>/dev/null  # expect: no log.jsonl written
```

**Output (excerpt):**

```
curator evolve: running DRY-RUN preview (no mutations)
═══════════════════════════════════════════════════════════════
DRY-RUN — REPORT ONLY. DO NOT MUTATE THE SKILL LIBRARY.
═══════════════════════════════════════════════════════════════
...
dry-run: no changes applied. Re-run with --live to perform actual memory writes (gated by bias canary pre-check).
EXIT=0
```

**Audit log after dry-run:** empty — no `log.jsonl` file written. Dry-run path correctly does NOT append audit (per Plan 02 design: audit is for successful live ticks only).

**Verdict:** PASS — stdout contains `DRY-RUN` marker (twice), exit code 0, no audit side effects. Operator-visible signal is unambiguous.

---

## SC#2 — Canary gates the `--live` path (≥4/5 catch required)

**Requirement:** CURATE-02 — `hermes curator evolve --live` runs `run_bias_canary_pre_check()`; aborts with exit 2 + structured `BIAS_CANARY_FAILED` stderr message if catch < 4/5.

### SC#2a — Happy path (canary passes → live tick proceeds)

**Command:**

```bash
HERMES_HOME="$SMOKE_TMP" python3 -m hermes_cli.curator evolve --live
echo "EXIT=$?"
```

**Output:**

```
curator evolve: running LIVE tick (canary: 4/5 caught)
curator: snapshot created (2026-07-08T03-53-14Z)
EXIT=0
```

**Interpretation:** Canary pre-check ran against bundled fixtures (`tests/fixtures/curator_bias_canary/known_bad_records.jsonl`), caught 4/5 (the 5th is LLM-only by design — see Plan 01), passed threshold of 4, then proceeded to live tick. Live tick completed against the empty isolated state (no skills to mutate → quick completion, exit 0).

### SC#2b — Abort path (canary fails → exit 2 + structured stderr)

The abort path is exercised authoritatively by 3 unit tests in `tests/hermes_cli/test_curator_evolve_cli.py` (smoke reproduction requires overriding the fixtures_path via monkeypatch, which is what the unit tests already do). Per Plan 65-03 Task 1 `<action>`: "if neither [CLI override] is CLI-accessible, document that unit test covers the abort path authoritatively and the smoke proves the happy canary-pass path."

**Command:**

```bash
python3 -m pytest tests/hermes_cli/test_curator_evolve_cli.py::TestEvolveCommand::test_live_aborts_on_canary_failure \
                 tests/hermes_cli/test_curator_evolve_cli.py::TestEvolveCommand::test_canary_failure_message_format \
                 tests/hermes_cli/test_curator_evolve_cli.py::TestEvolveCommand::test_canary_failure_does_not_append_audit \
                 -x -v
```

**Output:**

```
tests/hermes_cli/test_curator_evolve_cli.py::TestEvolveCommand::test_live_aborts_on_canary_failure        PASSED [ 33%]
tests/hermes_cli/test_curator_evolve_cli.py::TestEvolveCommand::test_canary_failure_message_format        PASSED [ 66%]
tests/hermes_cli/test_curator_evolve_cli.py::TestEvolveCommand::test_canary_failure_does_not_append_audit PASSED [100%]

3 passed in 0.25s
```

The `test_canary_failure_message_format` test asserts the exact stderr regex `^BIAS_CANARY_FAILED: caught 3/5 \(threshold: 4\); live tick aborted; run 'hermes curator evolve' \(no --live\) for dry-run preview$` — grep-friendly for runbook automation.

**Verdict:** PASS — happy path proven by smoke (4/5 caught, live tick proceeded); abort path proven by 3 authoritative unit tests (exit 2 + structured BIAS_CANARY_FAILED message + no audit append on abort).

---

## SC#3 — Audit log emits sha256-tagged writes with `tick_mode` field

**Requirement:** CURATE-03 — after a live tick, audit log entry contains `tick_mode="live"` + `canary_pass` + `caught_count` + `mutation_summary`; sha256 chain still verifies.

### SC#3a — Live tick audit entry (smoke)

**Command:**

```bash
cat "$SMOKE_TMP/skills/.audit/log.jsonl" | python3 -m json.tool --json-lines
python3 -m agent.curator_audit verify "$SMOKE_TMP/skills/.audit/log.jsonl"
echo "EXIT=$?"
```

**Audit entry (from the SC#2a live tick):**

```json
{
    "entry_id": "4744e6d8099b446f8f4c281203f81fb7",
    "prev_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "action": "auto_apply",
    "ts": "2026-07-08T03:53:14.294170+00:00",
    "operator": "kai",
    "patch_id": "live-tick-20260708T035314Z",
    "skill_id": "<live-tick>",
    "feedback_ids": [],
    "eval_score": {},
    "commit_sha": null,
    "tick_mode": "live",
    "canary_pass": true,
    "caught_count": 4,
    "mutation_summary": {
        "checked": 0,
        "archived": 0,
        "marked_stale": 0,
        "reactivated": 0
    },
    "entry_sha256": "7153f7eaa42a7ef54a6964effead9aa7fb0516212d41b2bca22f670b3beb6c7c"
}
```

**`verify_chain` output:** exit 0 (chain verifies clean — entry_sha256 matches recomputed hash, prev_sha256 chains from genesis).

### SC#3b — Mixed-schema chain + backward compat (unit tests)

The critical SC#3 invariant is that legacy audit entries (without `tick_mode`) coexist with new extended entries in the same log file, and `verify_chain` still passes. This is covered by 3 authoritative unit tests.

**Command:**

```bash
python3 -m pytest tests/agent/test_curator_live_guards.py::test_verify_chain_mixed_schema \
                 tests/agent/test_curator_live_guards.py::test_append_audit_with_tick_mode \
                 tests/agent/test_curator_live_guards.py::test_append_audit_backward_compat \
                 -x -v
```

**Output:**

```
tests/agent/test_curator_live_guards.py::test_verify_chain_mixed_schema       PASSED [ 33%]
tests/agent/test_curator_live_guards.py::test_append_audit_with_tick_mode     PASSED [ 66%]
tests/agent/test_curator_live_guards.py::test_append_audit_backward_compat    PASSED [100%]

3 passed in 0.19s
```

**Verdict:** PASS — live-tick audit entry well-formed (all 4 Phase 65 fields populated: `tick_mode`, `canary_pass`, `caught_count`, `mutation_summary`); `verify_chain` exits 0 on the smoke entry; backward-compat + mixed-schema chain integrity proven by 3 unit tests.

---

## Full Phase 65 Regression

**Command:**

```bash
python3 -m pytest tests/agent/test_curator_live_guards.py tests/agent/test_curator.py \
                 tests/hermes_cli/test_curator_evolve_cli.py tests/hermes_cli/test_curator_cli.py \
                 tests/v11-bias-canary/ -q
```

**Output:**

```
........................................................................ [ 48%]
........................................................................ [ 96%]
......                                                                   [100%]
150 passed in 3.16s
```

All 150 canonical Phase 65 tests pass.

> **Out-of-scope note:** 18 pre-existing failures in `tests/hermes_cli/test_curator_stats.py` are unrelated to Phase 65 (they assert v5/v6 doc-tree structure removed in commit `f10495332`). Logged to `deferred-items.md` per executor SCOPE BOUNDARY rule. CURATE-01/02/03 all green.

---

## Operator Runbook — Phase 66 First Live Tick

### Before you begin

Phase 65 ships the **guards** (CLI + canary + audit extension). Phase 66 runs the **first actual live tick** against the operator's real `~/.hermes` state. Use this runbook when Phase 66 kicks off.

### Step 1 — Dry-run preview (always do this first)

```bash
hermes curator evolve
```

Read the printed report. Verify the proposed mutations (archive stale, reactivate, etc.) make sense. **Exit 0 expected.** No audit entry written.

### Step 2 — Live tick with canary gate

```bash
hermes curator evolve --live
```

**Expected happy path:** stdout shows `curator evolve: running LIVE tick (canary: 4/5 caught)`, then the tick runs. Exit 0. Audit log entry appended at `~/.hermes/skills/.audit/log.jsonl` with `tick_mode: "live"`, `canary_pass: true`, `caught_count: 4`.

**On canary failure (exit 2):** stderr prints `BIAS_CANARY_FAILED: caught N/5 (threshold: 4); live tick aborted; run 'hermes curator evolve' (no --live) for dry-run preview`. Investigate the canary fixtures (`tests/fixtures/curator_bias_canary/known_bad_records.jsonl`) and the bias canary module (`agent/curator_bias_canary.py`). Do NOT use `--skip-canary` without operator sign-off.

### Step 3 — Verify audit chain post-tick

```bash
python3 -m agent.curator_audit verify ~/.hermes/skills/.audit/log.jsonl
echo "EXIT=$?"  # expect 0
```

Inspect the last entry:

```bash
tail -1 ~/.hermes/skills/.audit/log.jsonl | python3 -m json.tool
```

Confirm `tick_mode: "live"` + `canary_pass: true` + `caught_count: 4` + `mutation_summary` reflects expected transition counts.

### 24-hour rollback window

If the live tick produced unwanted mutations, the audit log provides the forensic trail:

- **By timestamp:** `grep '"ts": "2026-07-08T03:53' ~/.hermes/skills/.audit/log.jsonl` (adjust to tick timestamp).
- **By tick_mode:** `grep '"tick_mode": "live"' ~/.hermes/skills/.audit/log.jsonl` to find all live ticks.
- **By canary bypass:** `grep '"canary_pass": null' ~/.hermes/skills/.audit/log.jsonl` to find `--skip-canary` escape-hatch uses (Phase 66 24h review should flag these).

The curator also writes a snapshot before each live tick (`curator: snapshot created (...)` in stdout). Use `hermes curator rollback` to restore the pre-tick state if needed.

### Escape hatch (`--skip-canary`) — operator-only

```bash
hermes curator evolve --live --skip-canary
```

Bypasses the canary pre-check. **DANGEROUS** — audit entry has `canary_pass: null` (distinct from `true`/`false`) so the 24h review can grep for bypass attempts. Use only if the canary fixtures are broken AND the operator has signed off on a manual bias review.
