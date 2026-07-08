# Phase 65: CURATOR-LIVE-GUARDS - Research

**Researched:** 2026-07-08
**Domain:** Curator self-evolution safety guards (CLI + bias canary + audit chain)
**Confidence:** HIGH

## Summary

Phase 65 给 curator self-evolution 加 3 个安全护栏,为 Phase 66 的首个 live tick 铺路。核心实现是:**新增** `hermes curator evolve` 子命令(默认 dry-run,`--live` opt-in),**复用**已有的 `agent.curator_bias_canary.check_record()` 做 pre-tick 检查,**扩展**已有的 `agent.curator_audit.append_audit()` 加 `tick_mode` 字段。所有改动都是 additive 的——不破坏现有 12 个 curator 子命令、不破坏 v12.0 已 ship 的 bias canary API、不破坏现有审计链向后兼容。

**Primary recommendation:** 3 个 plan/wave:(1) Wave 0 验证 + canary pre-check 模块 + 5 fixture records,(2) `evolve` CLI 子命令 + `--live`/`--skip-canary` flag wiring + audit `tick_mode` 字段扩展,(3) VALIDATION.md 全量测试 + 端到端 smoke。Phase 65 **不执行**任何 live tick——只提供 guards,真正的 live tick 在 Phase 66。

**关键发现:** v11.0 (Phase 54-03) 已经 ship 了完整的 bias canary(`agent.curator_bias_canary` 模块)+ 5 个 bad-record fixtures(`tests/v11-bias-canary/fixtures/`)+ 集成测试 + audit chain append。Phase 65 主要工作是 **wiring**(CLI + pre-check function + audit field 扩展),不是重新实现 canary。这意味着 Phase 65 的实际代码量比表面看小很多。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **dry_run default:** `True` (curator.py:1942, v11.0 EVAL-06 invariant) — Phase 65 preserves this default; only adds opt-in `--live` path
- **Bias canary API:** `agent.curator_bias_canary.check_record(record: dict) -> CanaryReport` (line 261) — Phase 65 reuses, does not modify
- **Audit chain:** `agent.curator_audit` with sha256-chained entries (GENESIS_PREV_SHA256 at line 63, `_audit_log_path()` at line 95) — Phase 65 extends with live-tick tag
- **Audit log location:** `~/.hermes/skills/.audit/log.jsonl` (confirmed exists with 5 entries from v12.0 bias canary runs)
- **Curator CLI pattern:** `hermes_cli/curator.py:register_cli` adds subcommands via `subs.add_parser(name, ...).set_defaults(func=_cmd_xxx)` — Phase 65 follows this pattern
- **Live tick precondition:** `dry_run=False AND bias_canary_pass=True` — only then proceed to live writes
- **G1 (locked):** NEW standalone `hermes curator evolve` 子命令 — distinct from `hermes curator run`(run stays dry-run/status-only;evolve --live is the mutation path)
- **G2 (locked):** Bundle 5 known-bad fixture records in `tests/fixtures/curator_bias_canary/known_bad_records.jsonl` — version-controlled, test-reproducible
- **G3 (locked):** Audit log entry extension — add `tick_mode: "live"` field(单 chain 保留;sha256 仍 chain)
- **G4 (locked):** Canary failure UX — exit code 2 + structured `BIAS_CANARY_FAILED: caught N/5 (threshold: 4)` message

### Claude's Discretion

(已全部在 CONTEXT.md decisions 中给出推荐并被 adopt — 见 G1-G4 locked)

### Deferred Ideas (OUT OF SCOPE)

- **1st actual live tick** — Phase 66 (CURATOR-LIVE-TICK)
- **Automated rollback** — too complex; v13.0 uses operator 24h review + manual rollback
- **Bias canary tuning** — v12.0 EVAL-03 baseline retained as-is (≥4/5)
- **Prometheus/Grafana audit dashboards** — v14+ scope
- **Multi-operator audit chain** — v13 assumes single-operator (PROJECT.md v6 decision)
- **`--skip-canary` escape hatch** — CONTEXT.md specifics 提到但 Phase 65 scope 之外(留 Phase 66 operator runbook 决定是否 ship)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CURATE-01 | 给 curator self-evolution CLI 加 `--live` opt-in flag(默认仍 dry-run) | `hermes_cli/curator.py:register_cli` (line 1238) + `_cmd_run` pattern (line 187); 新增 `_cmd_evolve` + `evolve` subparser;`run_curator_review(dry_run=False)` (curator.py:1942) 已存在,只是从未被 CLI 调用过 |
| CURATE-02 | Pre-tick bias canary check —— 必须 catch ≥4/5 known-bad records;canary fail 时 abort live tick | `agent.curator_bias_canary.check_record` (line 261) 已 ship + 5 fixtures 已存在 at `tests/v11-bias-canary/fixtures/`;Phase 65 加 wrapper fn `run_bias_canary_pre_check(seed_records_path) -> (pass, caught, failed_ids)` + abort logic |
| CURATE-03 | Post-tick 审计日志 —— 记录每个 live tick 的 memory writes(sha256-tagged) | `agent.curator_audit.append_audit` (line 158) 已 ship;Phase 65 扩展 `tick_mode` 字段(向后兼容:旧 entries 无此字段,新 entries 有 `tick_mode: "live"`) |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| `evolve` CLI 子命令(argparse + dispatch) | CLI Layer (`hermes_cli/curator.py`) | — | 所有 curator 子命令都 register 在 CLI;thin shell pattern |
| `--live` flag 解析 + dry_run 传递 | CLI Layer | Runtime (`agent/curator.py`) | CLI 解析 flag,Runtime 执行 mutation;`run_curator_review(dry_run=False)` 已是 Runtime API |
| Bias canary pre-check function | Runtime (`agent/curator.py` 新 helper) | Bias Canary Module (`agent/curator_bias_canary.py`) | 新 helper 是 Runtime-side orchestration;调用 canary module 的 `check_record` API |
| Known-bad fixture records | Test Fixtures (`tests/fixtures/curator_bias_canary/`) | — | Version-controlled 测试资产,与 canary fixtures 分开(phase 65 owned) |
| Audit chain `tick_mode` 字段 | Audit Module (`agent/curator_audit.py`) | Runtime (`agent/curator.py` 调用方) | append_audit 在 Audit Module;新字段由 caller 传入 |
| Exit code 2(canary fail) | CLI Layer | — | Exit code 是 CLI process 层概念;Runtime 不关心 |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (argparse, json, hashlib, pathlib) | 3.11+ | CLI subparser, fixture load, sha256 verify | Hermes 已 pinned `requires-python = ">=3.11"`;curator 全栈已用 stdlib |
| `agent.curator_bias_canary` | 已 ship (v11.0 Phase 54-03) | `check_record(record) -> CanaryReport` 三个 deterministic checks | v12.0 baseline 已 EVAL-03 verified at ≥4/5 catch rate `[VERIFIED: codebase agent/curator_bias_canary.py:261]` |
| `agent.curator_audit` | 已 ship (v6.0 Phase 32) | `append_audit(action, patch_id, skill_id, ...)` sha256-chained writer | `~/.hermes/skills/.audit/log.jsonl` 已有 5 entries,向后兼容 `[VERIFIED: codebase agent/curator_audit.py:158 + on-disk log]` |
| `agent.curator.run_curator_review` | 已 ship (v6.0+ refined through v11.0) | `run_curator_review(dry_run=False)` 执行 live tick | dry_run kwarg 已 wired through entire pipeline `[VERIFIED: codebase agent/curator.py:1942]` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.0.2 (pyproject.toml) | CLI subcommand tests, canary pre-check tests, audit chain tests | 已有 30+ curator test 文件,Phase 65 沿用 pattern |
| pytest-asyncio | 1.3.0 | bias canary `run_bias_canary` 是 async(若 Phase 65 直接调用);`check_record` 本身是 sync | `check_record` 是 sync,所以 Phase 65 pre-check function 可以保持 sync |
| rich | 14.3.3 | Optional:`evolve` 命令的 rich-formatted 输出(canary 结果 table) | 现有 curator CLI 大多用 plain print(`_cmd_run`,`_cmd_status`);rich 仅 stats 用了 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| NEW `evolve` subcommand | Extend existing `run --live` | G1 locked 选 NEW(separation of concerns);`run` 保留 dry-run preview 语义 |
| Bundle fixture JSONL | Runtime-generated fuzz records | G2 locked 选 bundle(test-reproducible + 可读) |
| Extend audit chain with `tick_mode` field | Separate `live_ticks.jsonl` | G3 locked 选 extend(单 chain 完整性) |

**Installation:**
```bash
# 无新增依赖 — Phase 65 100% 复用已有 stdlib + agent modules
```

**Version verification:** N/A — 无新增 package。所有 referenced 模块已在 `pyproject.toml` pinned。

## Package Legitimacy Audit

Phase 65 **不安装**任何外部 package。100% stdlib + 已有 internal modules。

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| (none) | — | — | — | — | — | N/A — phase 安装零外部包 |

*Packages removed due to slopcheck [SLOP] verdict:* none
*Packages flagged as suspicious [SUS]:* none

## Architecture Patterns

### System Architecture Diagram

```
                        ┌─────────────────────────────────┐
                        │   Operator (Kai)                │
                        │   $ hermes curator evolve --live│
                        └──────────────┬──────────────────┘
                                       │
                                       ▼
                        ┌─────────────────────────────────┐
                        │   CLI Layer                     │
                        │   hermes_cli/curator.py         │
                        │   _cmd_evolve(args)             │
                        │   ─ parse --live, --skip-canary │
                        └──────┬────────────────┬─────────┘
                               │                │
              ┌────────────────┘                └───────────────┐
              │ dry_run path                                    │ --live path
              ▼                                                 ▼
   ┌──────────────────────┐                    ┌──────────────────────────────┐
   │ run_curator_review   │                    │ STEP 1: Bias Canary Pre-check│
   │ (dry_run=True)       │                    │ run_bias_canary_pre_check()  │
   │ → report only        │                    │  └ check_record() x 5        │
   │ → exit 0             │                    │     over known_bad.jsonl     │
   └──────────────────────┘                    │  └ count caught / 5          │
                                               └──────────┬───────────────────┘
                                                          │
                                              ┌───────────┴───────────┐
                                              │                       │
                                              ▼ caught < 4            ▼ caught >= 4
                                   ┌──────────────────┐   ┌────────────────────────┐
                                   │ ABORT            │   │ STEP 2: Live Tick      │
                                   │ exit 2           │   │ run_curator_review     │
                                   │ BIAS_CANARY_FAIL │   │ (dry_run=False)        │
                                   │ message          │   │  → mutations happen    │
                                   └──────────────────┘   │  → snapshot taken      │
                                                          └──────────┬─────────────┘
                                                                     │
                                                                     ▼
                                                          ┌────────────────────────┐
                                                          │ STEP 3: Audit Append   │
                                                          │ append_audit(          │
                                                          │   action="auto_apply", │
                                                          │   tick_mode="live",    │
                                                          │   canary_pass=True,    │
                                                          │   caught_count=N,      │
                                                          │   ...                  │
                                                          │ )                      │
                                                          │ → ~/.hermes/skills/    │
                                                          │   .audit/log.jsonl     │
                                                          └────────────────────────┘
```

### Recommended Project Structure

```
agent/
├── curator.py                    # [MODIFY] 加 run_bias_canary_pre_check helper
│                                 #         (在 _feedback_scan_phase 之后,run_curator_review 之前)
└── curator_audit.py              # [MODIFY] append_audit 加 tick_mode 等可选字段
                                  #         (向后兼容:旧 callers 不传则默认 None)

hermes_cli/
└── curator.py                    # [MODIFY] 加 _cmd_evolve + register_cli 加 p_evolve subparser

tests/
├── fixtures/
│   └── curator_bias_canary/      # [NEW] Phase 65 owned fixture dir
│       └── known_bad_records.jsonl  # [NEW] 5 records (one per line, JSONL)
├── agent/
│   └── test_curator_live_guards.py   # [NEW] bias canary pre-check + audit tick_mode tests
└── hermes_cli/
    └── test_curator_evolve_cli.py    # [NEW] evolve subcommand parsing + exit code tests

.planning/phases/65-curator-live-guards/
├── 65-CONTEXT.md                 # [EXISTS]
├── 65-RESEARCH.md                # [THIS FILE]
├── 65-PLAN-01.md                 # [WAVE 0+1: canary pre-check + fixtures]
├── 65-PLAN-02.md                 # [WAVE 2: evolve CLI + audit extension]
├── 65-PLAN-03.md                 # [WAVE 3: VALIDATION.md + e2e smoke]
└── 65-VALIDATION.md              # [Wave 3 output]
```

### Pattern 1: Curator CLI Subcommand Pattern (LOCKED — CONTEXT.md G1)

**What:** 每个 curator 子命令是一个 `_cmd_xxx(args) -> int` 函数,在 `register_cli` 中通过 `subs.add_parser(name, ...) + set_defaults(func=_cmd_xxx)` 注册。

**When to use:** 任何新增 curator 子命令。

**Example:**
```python
# Source: hermes_cli/curator.py:1238 (register_cli) + :187 (_cmd_run) [VERIFIED: codebase]

# 1. Handler function (returns int exit code)
def _cmd_evolve(args) -> int:
    """``hermes curator evolve [--live] [--skip-canary] [--sync]``."""
    from agent import curator
    if not curator.is_enabled():
        print("curator: disabled via config")
        return 1

    live = bool(getattr(args, "live", False))
    skip_canary = bool(getattr(args, "skip_canary", False))

    if not live:
        # Default path: dry-run preview (mirrors `run --dry-run`)
        print("curator evolve: running DRY-RUN preview (no mutations)")
        result = curator.run_curator_review(
            dry_run=True,
            synchronous=True,
        )
        print("dry-run: no changes. Re-run with --live to apply.")
        return 0

    # --live path: pre-tick canary check
    if not skip_canary:
        passed, caught, failed_ids = curator.run_bias_canary_pre_check()
        if not passed:
            print(
                f"BIAS_CANARY_FAILED: caught {caught}/5 (threshold: 4); "
                f"live tick aborted; run 'hermes curator evolve' "
                f"(no --live) for dry-run preview",
                file=sys.stderr,
            )
            return 2  # G4 locked: exit code 2 = canary failure

    # Canary passed (or skipped) — proceed to live tick
    print(f"curator evolve: running LIVE tick (canary: {caught}/5 caught)")
    result = curator.run_curator_review(
        dry_run=False,
        synchronous=True,
        # v13: tick metadata threaded via state2 / audit extension
    )
    return 0

# 2. Register in register_cli() AFTER existing subcommands
p_evolve = subs.add_parser(
    "evolve",
    help="Run curator self-evolution (default: dry-run preview; "
         "--live performs actual memory writes with bias canary pre-check)",
)
p_evolve.add_argument(
    "--live", dest="live", action="store_true",
    help="Perform LIVE memory writes (default: dry-run preview). "
         "Runs bias canary pre-check; aborts on <4/5 catch rate.",
)
p_evolve.add_argument(
    "--skip-canary", dest="skip_canary", action="store_true",
    help="DANGEROUS: skip bias canary pre-check. Operator-only escape hatch.",
)
p_evolve.add_argument(
    "--sync", "--synchronous", dest="synchronous", action="store_true",
    help="Wait for the LLM pass to finish (default for evolve)",
)
p_evolve.set_defaults(func=_cmd_evolve)
```

### Pattern 2: Bias Canary Pre-Check Function

**What:** 一个 sync helper 包装 `check_record` × 5,返回 (pass, caught_count, failed_record_ids)。

**When to use:** `evolve --live` 调用前。

**Example:**
```python
# Source: NEW — pattern derived from agent/curator_bias_canary.py:261 [VERIFIED: codebase]
#         + tests/v11-bias-canary/test_bias_canary_integration.py:61 [VERIFIED: codebase]

# In agent/curator.py (after _feedback_scan_phase, before run_curator_review):

_BIAS_CANARY_THRESHOLD: int = 4  # v12.0 EVAL-03 baseline — frozen per CURATE-02

def _bias_canary_fixtures_path() -> Path:
    """Resolve the known-bad fixture records path.

    Bundled at ``tests/fixtures/curator_bias_canary/known_bad_records.jsonl``
    in the repo; for installed-wheel use, fall back to a bundled package
    data path. Phase 65 ships the fixtures in-tree only (operator runs
    `hermes` from the repo checkout).
    """
    # Resolve relative to the hermes-agent repo root.
    # FUTURE: if shipped as package data, use importlib.resources.
    return Path(__file__).resolve().parents[1] / "tests" / "fixtures" / \
           "curator_bias_canary" / "known_bad_records.jsonl"


def run_bias_canary_pre_check(
    *,
    fixtures_path: Path | None = None,
    threshold: int = _BIAS_CANARY_THRESHOLD,
) -> tuple[bool, int, list[str]]:
    """Pre-tick bias canary: load 5 known-bad fixtures, count caught.

    Loads the JSONL fixture file (one record per line), runs
    ``check_record()`` on each, counts how many are flagged.
    Deterministic — no LLM call (sync only, safe to run from CLI).

    Args:
        fixtures_path: Override path to fixture JSONL (for testing).
        threshold: Minimum catch count to pass (default 4).

    Returns:
        (passed, caught_count, failed_record_ids) where:
        - passed: True iff caught_count >= threshold
        - caught_count: N of 5 records flagged by check_record
        - failed_record_ids: list of record_ids that did NOT get flagged
          (canary false-negatives — should be empty in practice)
    """
    from agent.curator_bias_canary import check_record  # lazy import

    path = fixtures_path or _bias_canary_fixtures_path()
    if not path.exists():
        logger.warning(
            "bias canary fixtures not found at %s — failing safe", path,
        )
        return False, 0, ["<fixtures-missing>"]

    caught = 0
    not_caught: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    logger.warning(
                        "bias canary fixture line unparseable: %s", exc,
                    )
                    continue
                report = check_record(record)
                if report.flagged:
                    caught += 1
                else:
                    not_caught.append(report.record_id)
    except OSError as exc:
        logger.warning("bias canary fixtures read failed: %s", exc)
        return False, 0, ["<read-error>"]

    passed = caught >= threshold
    logger.info(
        "bias canary pre-check: caught %d/%d (threshold: %d) — %s",
        caught, caught + len(not_caught), threshold,
        "PASS" if passed else "FAIL",
    )
    return passed, caught, not_caught
```

### Pattern 3: Audit Chain `tick_mode` Field Extension

**What:** `append_audit` 加 `tick_mode` 可选 kwarg。旧 callers 不传 → 字段缺失 → 向后兼容。新 callers(`evolve --live` post-tick)传 `tick_mode="live"`。

**When to use:** Any live-tick audit entry(CURATE-03)。

**Example:**
```python
# Source: extends agent/curator_audit.py:158 [VERIFIED: codebase]

# In agent/curator_audit.py — extend append_audit signature:
def append_audit(
    *,
    action: str,
    patch_id: str,
    skill_id: str,
    operator: str = "system",
    feedback_ids: list[str] | None = None,
    eval_score: dict[str, Any] | None = None,
    commit_sha: str | None = None,
    # ── Phase 65 (CURATE-03) extensions ──────────────────────────────
    tick_mode: str | None = None,        # "live" | "dry_run" | None (legacy)
    canary_pass: bool | None = None,     # True/False/None (not set)
    caught_count: int | None = None,     # 0..5
    mutation_summary: dict[str, Any] | None = None,  # skill_ids affected + verbs
) -> str:
    """...(docstring updated)...

    New Phase 65 kwargs are OPTIONAL. Existing callers (v6 feedback-scan,
    bias canary summary, approve/reject wrappers) continue to work without
    modification — their entries simply have these fields absent (which
    audit readers treat as "legacy / not from a live tick").

    Validation:
        - ``tick_mode`` must be one of {"live", "dry_run"} if not None.
        - ``canary_pass=True`` requires ``tick_mode="live"``.
    """
    if action not in ACTION_VALUES:
        raise ValueError(...)
    if tick_mode is not None and tick_mode not in ("live", "dry_run"):
        raise ValueError(f"tick_mode must be 'live' or 'dry_run', got {tick_mode!r}")
    if canary_pass is True and tick_mode != "live":
        raise ValueError("canary_pass=True requires tick_mode='live'")

    # ... existing logic ...

    entry: dict[str, Any] = {
        "entry_id": entry_id,
        "prev_sha256": prev_sha256,
        "action": action,
        "ts": ts,
        "operator": operator,
        "patch_id": patch_id,
        "skill_id": skill_id,
        "feedback_ids": feedback_ids or [],
        "eval_score": eval_score or {},
        "commit_sha": commit_sha,
    }
    # Phase 65 extensions — only add fields that are set (keeps entries compact)
    if tick_mode is not None:
        entry["tick_mode"] = tick_mode
    if canary_pass is not None:
        entry["canary_pass"] = canary_pass
    if caught_count is not None:
        entry["caught_count"] = caught_count
    if mutation_summary is not None:
        entry["mutation_summary"] = mutation_summary

    entry["entry_sha256"] = _compute_entry_sha256(prev_sha256, entry)
    # ... rest unchanged (write + fsync) ...
```

**Critical note on chain integrity:** Adding new fields to the entry dict does NOT break existing chain verification. `verify_chain()` (line 257) recomputes sha256 from whatever fields are present in each entry — adding fields to NEW entries doesn't affect OLD entries' hashes. Forward compatibility is preserved. `[VERIFIED: codebase agent/curator_audit.py:102-133 (_serialize_entry_for_sha256 drops entry_sha256, includes everything else)]`

### Pattern 4: Known-Bad Fixture Records (5 Distinct Failure Modes)

**What:** `tests/fixtures/curator_bias_canary/known_bad_records.jsonl` — JSONL, 1 record per line, 5 lines total. Each record triggers a DIFFERENT canary check failure.

**When to use:** Loaded by `run_bias_canary_pre_check()` at every `evolve --live` invocation.

**The 5 records (distinct failure modes — Phase 65 NEW copies):**

> **Note:** v11.0 already ships 5 individual `.json` fixtures at `tests/v11-bias-canary/fixtures/` — Phase 65 could either (a) reuse them or (b) bundle a single JSONL. Per CONTEXT.md G2 locked decision, Phase 65 bundles a NEW JSONL at `tests/fixtures/curator_bias_canary/known_bad_records.jsonl` (separate from v11.0's individual JSONs to keep Phase 65 self-contained and decoupled from v11.0 test asset layout).

| # | record_id | Failure Mode | Canary Check Triggered | Field That Causes Failure |
|---|-----------|--------------|------------------------|---------------------------|
| 1 | `bad-low-confidence` | Curator confidence < 0.3 | `confidence_threshold` | `confidence: 0.15` (< 0.3 default) |
| 2 | `bad-single-operator` | Evidence from only 1 distinct operator | `operator_diversity` | `evidence_operator_ids: ["op1", "op1"]` (1 distinct, < 2 required) |
| 3 | `bad-no-operator-id` | Empty operator IDs list | `operator_diversity` | `evidence_operator_ids: []` (0 distinct) |
| 4 | `bad-low-evidence` | Evidence text unrelated to claim (cosine < 0.7) | `evidence_coverage` | `evidence_records` text about cooking, but `text` about cinematography → cosine ~0.0 |
| 5 | `bad-unsupported-claim` | Claim references content absent from evidence | `claim_support` (LLM-only — deterministic checks may pass) | `text` mentions "anamorphic-lens rule" but evidence only mentions "three-act structure"; LLM check catches this |

**Important design note:** Record #5 (`bad-unsupported-claim`) only fails via the **LLM** claim-support check, which runs in `run_bias_canary()` (async, GLM call) but NOT in `check_record()` (sync, deterministic-only). The pre-check wrapper uses `check_record()` (sync), so record #5 may NOT be caught. **This is acceptable** — the v12.0 EVAL-03 baseline threshold is "≥4/5 caught", which means 4 deterministic-caught records suffice; the LLM-only 5th is a bonus that the actual `run_bias_canary()` (invoked separately during the live tick itself) would catch. `[VERIFIED: codebase agent/curator_bias_canary.py:261-323 (check_record runs 3 deterministic checks, NOT claim_support) + :434-497 (run_bias_canary adds claim_support via LLM)]`

**Recommended JSONL content (5 records):**
```jsonl
{"record_id":"bad-low-confidence","agent_id":"colorist","confidence":0.15,"evidence_operator_ids":["op1","op2"],"evidence_records":[{"text":"colorist prefers teal and orange color grading for action scenes"},{"text":"colorist prefers teal and orange color grading for action scenes"}],"text":"colorist prefers teal and orange color grading for action scenes","_canary_expected_failure":"confidence_threshold"}
{"record_id":"bad-single-operator","agent_id":"screenplay","confidence":0.8,"evidence_operator_ids":["op1","op1"],"evidence_records":[{"text":"screenplay expert prefers three-act structure for short dramas"},{"text":"screenplay expert prefers three-act structure for short dramas"}],"text":"screenplay expert prefers three-act structure for short dramas","_canary_expected_failure":"operator_diversity"}
{"record_id":"bad-no-operator-id","agent_id":"scene_builder","confidence":0.8,"evidence_operator_ids":[],"evidence_records":[{"text":"scene builder prefers wide establishing shots"},{"text":"scene builder prefers wide establishing shots"}],"text":"scene builder prefers wide establishing shots","_canary_expected_failure":"operator_diversity"}
{"record_id":"bad-low-evidence","agent_id":"editor","confidence":0.8,"evidence_operator_ids":["op1","op2"],"evidence_records":[{"text":"recipe calls for two cups of flour and pinch of salt"},{"text":"preheat oven to 350 degrees and bake 30 minutes"}],"text":"editor uses jump cuts for tension in action sequences","_canary_expected_failure":"evidence_coverage"}
{"record_id":"bad-unsupported-claim","agent_id":"storyboard_designer","confidence":0.8,"evidence_operator_ids":["op1","op2"],"evidence_records":[{"text":"storyboard expert uses three-act structure for plot beats"},{"text":"storyboard expert uses three-act structure for plot beats"}],"text":"storyboard expert applies anamorphic-lens rule for cinematic framing","_canary_expected_failure":"claim_support"}
```

### Anti-Patterns to Avoid

- **Calling `run_bias_canary` (async, GLM dispatch) in the pre-check** — pre-check must be sync and deterministic (no network). Use `check_record()` only. The async LLM pass belongs in the live tick body itself, not the pre-check gate. `[CITED: agent/curator_bias_canary.py:261 docstring — "Does NOT call any LLM"]`
- **Modifying `run_curator_review` signature to add `tick_mode`** — pollutes the Runtime API with audit-layer concerns. Pass tick metadata via a separate `append_audit` call AFTER `run_curator_review` returns. The Runtime function stays generic. `[ASSUMED — based on single-responsibility principle; no existing precedent for threading audit fields through Runtime]`
- **Hardcoding fixture paths with `Path.home() / ".hermes"`** — CLAUDE.md anti-pattern. Use repo-root-relative resolution or `get_hermes_home()` for HERMES_HOME-scoped paths. Fixtures live in the repo, not in HERMES_HOME. `[CITED: CLAUDE.md "Anti-Patterns to Avoid"]`
- **Breaking `append_audit` backward compat** — v6 callers (feedback-scan, approve wrappers, bias canary summary) MUST continue to work without modification. New kwargs must be optional with `None` defaults. Existing audit log entries (5 on disk) MUST still verify. `[VERIFIED: agent/curator_audit.py:158 existing signature has no tick_mode field]`

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Bias canary checks (3 deterministic + 1 LLM) | Custom evidence-coverage / operator-diversity / confidence logic | `agent.curator_bias_canary.check_record(record)` (shipped v11.0 Phase 54-03) | Already battle-tested, v12.0 EVAL-03 baseline ≥4/5 catch rate verified |
| Audit chain sha256 + append + verify | Custom JSONL writer + hash chain | `agent.curator_audit.append_audit(action=..., tick_mode=...)` | Already handles fsync, genesis entry, malformed-tail detection, verify_chain |
| Curator live tick pipeline | Re-implement snapshot + transitions + LLM pass | `agent.curator.run_curator_review(dry_run=False)` | dry_run flag already wired through entire pipeline (v6→v11 refined) |
| Known-bad fixture records | Generate via fuzzer at runtime | `tests/fixtures/curator_bias_canary/known_bad_records.jsonl` (static file) | Deterministic, version-controlled, human-readable |
| CLI argparse subcommand registration | Manual argv parsing | `subs.add_parser("evolve", ...) + set_defaults(func=_cmd_evolve)` | Established pattern across 13 existing curator subcommands |

**Key insight:** Phase 65 is primarily a **wiring** phase, not a **building** phase. The hard parts (canary checks, audit chain, live tick pipeline) already exist from v6/v11/v12. Phase 65's job is to (a) connect them via a new CLI subcommand, (b) add a pre-check wrapper, (c) extend the audit schema with one new field. Estimated diff: ~200-400 lines across 3 source files + 1 fixture JSONL + 2-3 test files.

## Runtime State Inventory

> Phase 65 涉及 audit log schema 扩展,需考虑向后兼容。

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | 5 existing entries in `~/.hermes/skills/.audit/log.jsonl` (from v12.0 bias canary runs) — all use `action="auto_apply"`, `patch_id="bias-canary-summary"`, NO `tick_mode` field | **No migration needed** — new `tick_mode` field is optional; old entries remain valid (verify_chain still passes) `[VERIFIED: on-disk log read 2026-07-08]` |
| Live service config | `~/.hermes/config.yaml` may have `curator.*` / `feedback.curator.*` sections — Phase 65 adds NO new config keys | None — Phase 65 reads no new config |
| OS-registered state | None — curator is in-process, no systemd units / launchd / pm2 | None |
| Secrets/env vars | None — Phase 65 uses no new secrets (canary `check_record` is deterministic, no LLM) | None |
| Build artifacts | None — Phase 65 adds no compiled artifacts | None |

**The canonical question answered:** After Phase 65 ships, what runtime systems still have the old audit schema cached? **Answer: none that matter.** The 5 existing entries remain readable by the extended `read_audit()` (new fields are simply absent in old entries — readers treat absence as "legacy"). `verify_chain()` recomputes sha256 from whatever fields exist per entry, so mixed-schema entries verify correctly.

## Common Pitfalls

### Pitfall 1: Audit Chain Fork from Concurrent Live Ticks
**What goes wrong:** Two `evolve --live` invocations running simultaneously both read the same `prev_sha256` from the last line, both append entries with the same `prev_sha256`, producing a forked chain.
**Why it happens:** `append_audit` has no file locking (curator_audit.py:24-26 acknowledges this: "Single-process assumption. If a future version allows concurrent curator + CLI writes, add file locking (deferred).").
**How to avoid:** Phase 65 ships with INFRA-04 serial execution preserved (v13.0 hard constraint). Operator runbook (Phase 66 CURATE-05) must document "do not run two `evolve --live` concurrently". Phase 65 should add a soft guard: check `.curator_state` for `live_tick_in_progress` flag and refuse if set.
**Warning signs:** `verify_chain` reports "prev_sha256 mismatch" after a live tick.

### Pitfall 2: `dry_run=None` vs `dry_run=True` Ambiguity
**What goes wrong:** `run_curator_review(dry_run=None)` — passing `None` explicitly — is treated as `True` (dry-run) by curator.py:1986-1987. A caller who passes `None` thinking it means "use default" gets dry-run, which is SAFE but may surprise.
**Why it happens:** EVAL-06 invariant (v11.0) deliberately treats `None` as `True` for defense-in-depth — a caller who omits the kwarg or passes `None` must NOT trigger live writes.
**How to avoid:** Phase 65 `_cmd_evolve` ALWAYS passes an explicit `dry_run=True` or `dry_run=False` boolean — never `None`. Document this in the handler comment.
**Warning signs:** Live tick silently becomes dry-run (no error, just no mutations).

### Pitfall 3: Canary False-Negative on LLM-Only Failure Mode
**What goes wrong:** Record #5 (`bad-unsupported-claim`) only fails via the LLM `claim_support` check. `check_record()` (sync, deterministic) may NOT flag it because the 3 deterministic checks all pass. Pre-check reports "caught 4/5" — which still meets the ≥4 threshold, so it passes. But if records #1-4 were ever weakened (e.g., confidence raised above 0.3), the pre-check would drop to "caught 0/5" because #5 can't be caught deterministically.
**Why it happens:** `check_record()` deliberately excludes the LLM pass (docstring at curator_bias_canary.py:272: "Does NOT call any LLM (the claim-support LLM pass lives in `run_bias_canary` so unit tests stay deterministic)").
**How to avoid:** Keep the 4 deterministic-fail records (#1-4) stable. If tuning is needed, do it in Phase 66 (CURATE-05 runbook), not Phase 65. Document this dependency in the fixture file header comment.
**Warning signs:** Pre-check catches <4 after a "harmless" fixture edit.

### Pitfall 4: Audit Field Validation Too Strict
**What goes wrong:** Adding validation like `if tick_mode not in ("live", "dry_run", None): raise ValueError` to `append_audit` could break existing callers if they pass unexpected values.
**Why it happens:** Over-engineering validation in a module that historically accepted any dict for `eval_score`.
**How to avoid:** Validate ONLY `tick_mode` (enum-like) and the `canary_pass + tick_mode` consistency invariant. Leave `mutation_summary` as free-form dict (like `eval_score`). Existing callers pass no new args → no validation triggered.
**Warning signs:** Existing v6 caller (`_feedback_scan_phase` calling `append_audit(action="propose", ...)`) suddenly raises after Phase 65 merge.

### Pitfall 5: `--skip-canary` Escape Hatch Abuse
**What goes wrong:** Operator routinely uses `--skip-canary` because "canary keeps failing" — defeats the entire safety guard.
**Why it happens:** The flag exists (CONTEXT.md specifics mention it), and operators reach for it under pressure.
**How to avoid:** Phase 65 ships `--skip-canary` but logs EVERY use to audit chain with `canary_pass=None, tick_mode="live"` (distinct from canary-passed entries). Operator runbook (Phase 66) greps for these entries in 24h review. Help text says "DANGEROUS".
**Warning signs:** Audit log shows multiple `canary_pass=None` entries from the same operator in a week.

## Code Examples

### Existing `run_curator_review` Signature (VERIFIED — do not modify)

```python
# Source: agent/curator.py:1939-1979 [VERIFIED: codebase]
def run_curator_review(
    on_summary: Optional[Callable[[str], None]] = None,
    synchronous: bool = False,
    dry_run: bool = True,                    # ← EVAL-06 invariant: default True
    consolidate: Optional[bool] = None,
) -> Dict[str, Any]:
    """Execute a single curator review pass.

    Default is dry_run=True (dry-run-first invariant per
    05-POC-PLAN.md §4.6 + planning_context contract #4). Callers MUST
    pass dry_run=False explicitly to perform live writes. ...
    """
    # Line 1986-1987: None → True (defense-in-depth)
    if dry_run is None:
        dry_run = True
    # Line 1989-2006: dry_run branch (count only, no mutation)
    # Line 2007-2023: live branch (snapshot + apply_automatic_transitions)
    # Line 2098-2119 / 2226-2240: feedback_scan_phase (only if not dry_run)
```

### Existing `check_record` Signature (VERIFIED — reuse as-is)

```python
# Source: agent/curator_bias_canary.py:261-323 [VERIFIED: codebase]
def check_record(
    record: dict,
    *,
    embed_fn: Callable[[str], list[float]] | None = None,
    min_distinct_operators: int = DEFAULT_MIN_DISTINCT_OPERATORS,        # 2
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,          # 0.3
    evidence_coverage_threshold: float = DEFAULT_EVIDENCE_COVERAGE_THRESHOLD,  # 0.7
) -> CanaryReport:
    """Run all deterministic checks on a single memory record.

    Does NOT call any LLM (the claim-support LLM pass lives in
    run_bias_canary so unit tests stay deterministic).

    Inspected fields (per memory-record-schema.yaml §3):
      - record_id (str)
      - text (str): the candidate memory claim
      - evidence_records (list[dict]): resolved evidence text
      - evidence_operator_ids (list[str]): operator provenance
      - confidence (float): curator certainty

    Returns a CanaryReport with one entry per check name in
    checks_passed / checks_failed.
    """
```

### Existing `append_audit` Signature (VERIFIED — extend with optional kwargs)

```python
# Source: agent/curator_audit.py:158-249 [VERIFIED: codebase]
def append_audit(
    *,
    action: str,                          # REQUIRED — must be in ACTION_VALUES
    patch_id: str,                        # REQUIRED
    skill_id: str,                        # REQUIRED
    operator: str = "system",             # optional
    feedback_ids: list[str] | None = None,
    eval_score: dict[str, Any] | None = None,
    commit_sha: str | None = None,
    # Phase 65 additions (all optional, default None — backward compat):
    # tick_mode: str | None = None,
    # canary_pass: bool | None = None,
    # caught_count: int | None = None,
    # mutation_summary: dict[str, Any] | None = None,
) -> str:
    """Append one entry to the audit log and return its entry_id.

    Computes prev_sha256 from the last line of the existing log
    (or GENESIS_PREV_SHA256 for the first entry), then computes
    entry_sha256 via _compute_entry_sha256.

    Raises:
        ValueError: if action is not in ACTION_VALUES.
        AuditChainError: if the existing log's final line is malformed JSON.
    """
```

### Existing Audit Log Entry Format (VERIFIED — read from disk)

```json
{
  "entry_id": "a742c71ec5304bf7a1ebfafdda7098de",
  "prev_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "action": "auto_apply",
  "ts": "2026-07-07T09:33:34.532712+00:00",
  "operator": "system",
  "patch_id": "bias-canary-summary",
  "skill_id": "<bias-canary>",
  "feedback_ids": [],
  "eval_score": {
    "bias_canary": {
      "total_records": 6,
      "flagged_count": 5,
      "passed_count": 1,
      "flagged_record_ids": ["bad-low-confidence", "bad-low-evidence", ...],
      "passed_record_ids": ["good-multi-operator"],
      "flagged_details": [...]
    }
  },
  "commit_sha": null,
  "entry_sha256": "b032be63b70cc29ddab692e7f4570cbbfe878c22955fb0c77f7fbda5f7052ec6"
}
```
`[VERIFIED: /home/kai/.hermes/skills/.audit/log.jsonl line 1 — read 2026-07-08]`

**Phase 65 extended entry (NEW — for live ticks):**
```json
{
  "entry_id": "<uuid4>",
  "prev_sha256": "<previous entry_sha256>",
  "action": "auto_apply",
  "ts": "2026-07-15T12:00:00.000000+00:00",
  "operator": "kai",
  "patch_id": "live-tick-20260715-120000",
  "skill_id": "<live-tick>",
  "feedback_ids": [],
  "eval_score": {},
  "commit_sha": null,
  "tick_mode": "live",
  "canary_pass": true,
  "caught_count": 5,
  "mutation_summary": {
    "skills_archived": ["old-utility"],
    "skills_consolidated": [{"from": "pdf-extract", "into": "document-tools"}],
    "feedback_patches_proposed": 3
  },
  "entry_sha256": "<sha256(prev_sha256 + canonical_json)>"
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Curator always dry-run (v11.0 EVAL-06) | Curator dry-run by default + opt-in `--live` (Phase 65) | v13.0 Phase 65 (2026-07) | Operators can now run live ticks with safety guards |
| Bias canary runs only in test harness (v11.0/v12.0) | Bias canary wired into CLI pre-check (Phase 65) | v13.0 Phase 65 | Canary gates every live tick, not just CI |
| Audit log entries have no tick-mode marker (v6.0) | Audit log entries mark `tick_mode: "live"` for live ticks (Phase 65) | v13.0 Phase 65 | Operators can `grep tick_mode` to find live-tick entries |

**Deprecated/outdated:**
- Nothing deprecated — Phase 65 is purely additive.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `check_record()` deterministic checks alone catch ≥4/5 of the Phase 65 fixtures (because record #5 needs LLM) | Pattern 4 / Pitfall 3 | If wrong (deterministic catches <4), need to either (a) redesign fixture #5 to fail a deterministic check, or (b) call `run_bias_canary` async in pre-check (adds GLM dependency + 30s latency). Mitigation: Wave 0 test verifies catch count before wiring CLI. |
| A2 | `append_audit` extension with optional kwargs preserves backward compat (old callers unaffected) | Pattern 3 | If wrong, v6 feedback-scan / approve wrappers break. Mitigation: existing test suite `tests/agent/test_curator*.py` + `tests/hermes_cli/test_curator_cli.py` (30+ files) will catch regressions before merge. |
| A3 | `run_curator_review(dry_run=False)` performs the live mutation path correctly (snapshot + transitions + LLM pass + feedback-scan) | Standard Stack | If wrong, Phase 66 live tick fails. Mitigation: this function has been refined across v6→v11 with 30+ test files covering it; risk is low. Phase 65 does NOT modify this function. |
| A4 | The repo-root-relative path resolution for fixtures (`Path(__file__).resolve().parents[1] / "tests" / "fixtures" / ...`) works in operator's checkout | Pattern 2 | If operator runs `hermes` from a wheel install (no `tests/` dir), pre-check fails with "fixtures not found". Mitigation: Phase 65 documents "run from repo checkout"; Phase 66 runbook covers wheel-install case (bundle fixtures as package data). `[ASSUMED — based on CONTEXT.md not mentioning wheel-install support]` |

## Open Questions

1. **Should `run_bias_canary_pre_check` live in `agent/curator.py` or a new `agent/curator_live_guards.py` module?**
   - What we know: `agent/curator.py` is already 2486 lines. Adding ~50 lines for pre-check is marginal but adds to file length.
   - What's unclear: No existing precedent for sub-modules — curator has been a monolith since v6.
   - Recommendation: Keep in `agent/curator.py` (near `run_curator_review` which it guards). If Phase 66 adds more live-tick helpers, extract to `agent/curator_live.py` then.

2. **Should the `mutation_summary` field in audit entries be a free-form dict or a typed schema?**
   - What we know: `eval_score` is already free-form dict (varies by caller). `mutation_summary` could follow the same pattern.
   - What's unclear: Phase 66's runbook may want structured queries (e.g., "how many skills were archived across all live ticks?").
   - Recommendation: Free-form dict for Phase 65 (matches `eval_score` precedent). Phase 66 runbook can document expected keys.

3. **Should `--skip-canary` actually ship in Phase 65, or defer to Phase 66?**
   - What we know: CONTEXT.md `specifics` section mentions it. CONTEXT.md `decisions` section doesn't lock it.
   - What's unclear: Shipping it in Phase 65 means Phase 66 operator can use it immediately; deferring means Phase 66 must add it.
   - Recommendation: Ship in Phase 65 (low cost, documents the escape hatch in help text, audit logs its use). Phase 66 runbook governs when to use it.

## Environment Availability

> Phase 65 has no external dependencies beyond what curator already uses.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | All curator code | ✓ | 3.13 (per pyproject.toml + Dockerfile) | — |
| `~/.hermes/skills/.audit/log.jsonl` | Audit chain append (CURATE-03) | ✓ | 5 entries (v12.0 bias canary runs) | Auto-created if missing (curator_audit.py:97-99 `mkdir(parents=True, exist_ok=True)`) |
| `tests/fixtures/curator_bias_canary/` (NEW) | Canary pre-check (CURATE-02) | ✗ (Wave 0 creates) | — | Wave 0 task creates the directory + JSONL |
| GLM API key | NOT required by Phase 65 (pre-check uses deterministic `check_record`, not `run_bias_canary`) | N/A | N/A | N/A — Phase 65 is GLM-free |

**Missing dependencies with no fallback:** none.

**Missing dependencies with fallback:** none.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 (pyproject.toml `[dev]`) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (line 261, `addopts`, 30s timeout) |
| Quick run command | `python -m pytest tests/hermes_cli/test_curator_evolve_cli.py tests/agent/test_curator_live_guards.py -x -q` |
| Full suite command | `python -m pytest tests/agent/test_curator*.py tests/hermes_cli/test_curator*.py tests/v11-bias-canary/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CURATE-01 | `hermes curator evolve` (no flag) → dry-run preview, exit 0 | unit | `pytest tests/hermes_cli/test_curator_evolve_cli.py::TestEvolveCommand::test_default_is_dry_run -x` | ❌ Wave 0 |
| CURATE-01 | `hermes curator evolve --live` → calls `run_curator_review(dry_run=False)` | unit | `pytest tests/hermes_cli/test_curator_evolve_cli.py::TestEvolveCommand::test_live_flag_triggers_live_path -x` | ❌ Wave 0 |
| CURATE-01 | `evolve` subcommand registered in `register_cli` alongside existing 13 | unit | `pytest tests/hermes_cli/test_curator_cli.py::TestRegisterCliPreservesExistingSubcommands -x` (extend existing) | ✅ (existing, extend) |
| CURATE-02 | `run_bias_canary_pre_check()` catches ≥4/5 known-bad records | unit | `pytest tests/agent/test_curator_live_guards.py::test_pre_check_catches_four_of_five -x` | ❌ Wave 0 |
| CURATE-02 | `evolve --live` aborts with exit 2 when canary catches <4 | unit | `pytest tests/hermes_cli/test_curator_evolve_cli.py::TestEvolveCommand::test_live_aborts_on_canary_failure -x` | ❌ Wave 0 |
| CURATE-02 | Canary failure message format: `BIAS_CANARY_FAILED: caught N/5 (threshold: 4)` | unit | `pytest tests/hermes_cli/test_curator_evolve_cli.py::TestEvolveCommand::test_canary_failure_message_format -x` | ❌ Wave 0 |
| CURATE-03 | `append_audit(tick_mode="live", ...)` writes entry with `tick_mode` field | unit | `pytest tests/agent/test_curator_live_guards.py::test_append_audit_with_tick_mode -x` | ❌ Wave 0 |
| CURATE-03 | `append_audit(...)` without `tick_mode` (legacy caller) still works | unit | `pytest tests/agent/test_curator_live_guards.py::test_append_audit_backward_compat -x` | ❌ Wave 0 |
| CURATE-03 | `verify_chain()` passes on mixed-schema log (old entries without `tick_mode` + new entries with) | unit | `pytest tests/agent/test_curator_live_guards.py::test_verify_chain_mixed_schema -x` | ❌ Wave 0 |
| CURATE-03 | Live tick appends audit entry within 24h rollback window (timestamp ISO-8601 UTC) | unit | `pytest tests/agent/test_curator_live_guards.py::test_live_tick_audit_timestamp -x` | ❌ Wave 0 |
| Cross | `--skip-canary` flag bypasses pre-check, still writes audit with `canary_pass=None` | unit | `pytest tests/hermes_cli/test_curator_evolve_cli.py::TestEvolveCommand::test_skip_canary_bypasses_pre_check -x` | ❌ Wave 0 |
| Cross | Existing curator subcommands (status/run/pin/etc) still work unchanged | regression | `pytest tests/hermes_cli/test_curator_cli.py tests/agent/test_curator.py -x` | ✅ (existing) |
| Cross | Existing v11.0 bias canary tests still pass | regression | `pytest tests/v11-bias-canary/ -x` | ✅ (existing) |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/hermes_cli/test_curator_evolve_cli.py tests/agent/test_curator_live_guards.py -x -q` (< 10s)
- **Per wave merge:** `python -m pytest tests/agent/test_curator*.py tests/hermes_cli/test_curator*.py tests/v11-bias-canary/ -x -q` (< 30s)
- **Phase gate:** Full curator + bias canary suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/fixtures/curator_bias_canary/known_bad_records.jsonl` — 5 records (CURATE-02 fixture)
- [ ] `tests/agent/test_curator_live_guards.py` — covers `run_bias_canary_pre_check` + `append_audit` tick_mode (CURATE-02, CURATE-03)
- [ ] `tests/hermes_cli/test_curator_evolve_cli.py` — covers `_cmd_evolve` parsing + exit codes (CURATE-01, CURATE-02)
- [ ] Extend `tests/hermes_cli/test_curator_cli.py::NEW_V6_SUBCOMMANDS` to include `"evolve"` — regression guard

*(Existing test infrastructure covers regression side — pytest config, fixtures, conftest all in place.)*

## Security Domain

> Config: `security_enforcement` not explicitly set in `.planning/config.json` → treat as enabled.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | CLI runs as local OS user; no new auth surface |
| V3 Session Management | no | Curator is in-process; no sessions |
| V4 Access Control | yes | `--live` flag is the access control for state mutation; `--skip-canary` is the escape hatch (must be logged to audit) |
| V5 Input Validation | yes | `append_audit` validates `action` against `ACTION_VALUES` frozenset (existing); Phase 65 adds `tick_mode` enum validation |
| V6 Cryptography | yes (sha256 chain — existing) | `agent.curator_audit` uses stdlib `hashlib.sha256` — never hand-roll. Phase 65 extends entries but reuses existing hash computation. |
| V7 Error Handling & Logging | yes | Canany failure → exit 2 + structured stderr message; `--skip-canary` use logged to audit chain |
| V9 Communications | no | No network calls in Phase 65 (deterministic canary only) |

### Known Threat Patterns for Curator Live Guards

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Audit chain tampering (rewrite history) | Tampering | sha256 chain + `verify_chain()` (existing v6); Phase 65 preserves chain mechanics |
| Canary bypass via `--skip-canary` abuse | Elevation of Privilege | Audit-log every `--skip-canary` use with `canary_pass=None`; Phase 66 runbook reviews |
| Concurrent live ticks fork the chain | Tampering | Phase 65 soft guard (`live_tick_in_progress` flag in `.curator_state`); INFRA-04 serial execution preserved |
| Operator runs live tick without understanding scope | Repudiation | `BIAS_CANARY_FAILED` structured message + dry-run-first default + help text warnings |
| Bias canary regression (fixture edited, catch rate drops silently) | Information Disclosure | Wave 0 test `test_pre_check_catches_four_of_five` runs on every commit |

## Sources

### Primary (HIGH confidence)

- `agent/curator.py` (lines 1939-2259 `run_curator_review`, 1503-1936 `_feedback_scan_phase`) — full code read
- `agent/curator_bias_canary.py` (lines 1-569 full module) — full code read
- `agent/curator_audit.py` (lines 1-424 full module) — full code read
- `hermes_cli/curator.py` (lines 1-1486 full module) — full code read
- `~/.hermes/skills/.audit/log.jsonl` (5 entries, read 2026-07-08) — verified on-disk format
- `tests/v11-bias-canary/test_bias_canary_integration.py` (285 lines) — verified existing test pattern
- `tests/v11-bias-canary/fixtures/*.json` (5 bad + 1 good fixtures) — verified schema
- `.planning/config.json` — `workflow.nyquist_validation: true` (Validation Architecture required)

### Secondary (MEDIUM confidence)

- `.planning/phases/65-curator-live-guards/65-CONTEXT.md` — locked decisions G1-G4
- `.planning/REQUIREMENTS.md` — CURATE-01/02/03 verbatim
- `.planning/STATE.md` — v13.0 milestone context, deferred items
- `CLAUDE.md` — Curator CLI conventions, encoding rule, lazy %-logging, `get_hermes_home()` rule

### Tertiary (LOW confidence)

- (none — all findings verified against codebase)

## Recommended Plan Structure

**3 plans / 3 waves** (typical for infrastructure+wiring phase):

| Wave | Plan | Scope | SCs Addressed | Estimated Tasks |
|------|------|-------|---------------|-----------------|
| 1 | `65-PLAN-01.md` | **Foundation:** fixture JSONL + `run_bias_canary_pre_check` helper + `append_audit` tick_mode extension + Wave 0 tests | CURATE-02 (pre-check fn), CURATE-03 (audit extension) | 4-5 tasks |
| 2 | `65-PLAN-02.md` | **CLI wiring:** `_cmd_evolve` handler + `register_cli` `evolve` subparser + `--live`/`--skip-canary`/`--sync` flags + exit code 2 + BIAS_CANARY_FAILED message | CURATE-01 (CLI flag), CURATE-02 (abort path) | 3-4 tasks |
| 3 | `65-PLAN-03.md` | **Validation + smoke:** VALIDATION.md full test suite + CLI smoke test (subprocess `hermes curator evolve --live` with mocked canary) + regression run | All 3 SCs verified end-to-end | 2-3 tasks |

**Rationale for 3-wave split:** Wave 1 establishes the test-verifiable primitives (pre-check function + audit extension) BEFORE the CLI wiring depends on them. Wave 2 wires the CLI (depends on Wave 1 helpers). Wave 3 does end-to-end validation (depends on Wave 2 CLI). This matches the project's standard granularity and the `code_review: true` gate between waves.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — 100% reuse of existing modules; no new packages
- Architecture: HIGH — follows established curator CLI pattern (13 existing subcommands); bias canary + audit chain already shipped
- Pitfalls: HIGH — all 5 pitfalls derived from codebase reading (not hypothetical)
- Fixture records: HIGH — 4 of 5 mirror existing v11.0 fixtures exactly (verified schema); 5th is LLM-only (documented limitation)

**Research date:** 2026-07-08
**Valid until:** 2026-08-07 (30 days — stable internal codebase, no external API dependencies)
