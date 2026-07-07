#!/usr/bin/env python3
"""Latency SLO benchmark runner (Phase 54 plan 02 Task 2 — EVAL-02;
extended Phase 60 plan 01 Task 2 to add live mem0 backend mode).

Implements ``05-POC-PLAN.md §4.2`` task (c) — 3-record-count benchmark.
Two mutually-exclusive modes:

**Fixture mode (CI, default since Phase 54):**

    python scripts/run_latency_benchmark.py --fixture 100 --out /tmp/bench.json
    python scripts/run_latency_benchmark.py --fixture 500 --out /tmp/bench.json
    python scripts/run_latency_benchmark.py --fixture 1000 --out /tmp/bench.json

Loads a fixture-only in-memory backend (NO real mem0 dependency — per
CONTEXT.md decision #2 the CI benchmark is deterministic; the live
mem0 Platform API benchmark is an operator-action handoff documented
in ``.planning/research/v11-poc-eval/latency-baseline.md``).

**Live-backend mode (operator validation, Phase 60 plan 01):**

    MEM0_API_KEY=<key> python scripts/run_latency_benchmark.py \\
        --backend mem0 --record-count 500 --runs 100 --out /tmp/bench-live.json

Resolves the production mem0 backend via the ``plugins.memory.mem0.backend``
adapter (Phase 60 plan 01 Task 1). Requires ``MEM0_API_KEY`` to be set.

The script:
1. Loads either a fixture-only in-memory backend OR the live mem0 backend
   based on the mutually-exclusive ``--fixture`` / ``--backend`` flag.
2. Runs N (default 100) sequential ``timed_retrieval()`` calls.
3. Computes p50/p95/p99 of the per-call latencies.
4. Emits a JSON result file with ``record_count``, ``samples_ms``,
   ``percentiles``, ``slo_verdict`` (``pass`` / ``fail`` / ``skip``).

SLO verdict logic per §4.2 acceptance check:
    - ``pass`` — p95 < 500.0 ms (the formal SLO threshold).
    - ``fail`` — p95 >= 500.0 ms AND at least one call returned ``status="ok"``.
      Triggers 物理分区 evaluation per Phase 48 §3 + baseline doc.
    - ``skip`` — every call returned ``status="unavailable"`` or
      ``status="error"`` (the SLO cannot be measured on this run; the
      operator must configure a live backend and re-run).

Excludes LLM-bound calls by construction: ``timed_retrieval`` measures
only ``backend.search()`` cost; it does NOT dispatch any LLM (per
STACK §7.4 — LLM call = 2-15s, not in 500ms budget).

Usage:
    # Fixture path (CI default — no credentials)
    python scripts/run_latency_benchmark.py --fixture 500 --out /tmp/bench.json
    python scripts/run_latency_benchmark.py --fixture 500 --runs 50 --out /tmp/bench.json

    # Live-backend path (operator validation — requires MEM0_API_KEY)
    MEM0_API_KEY=<key> python scripts/run_latency_benchmark.py \\
        --backend mem0 --record-count 500 --runs 100 --out /tmp/bench-live.json
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import sys
from pathlib import Path

# Add repo root to sys.path so ``from agent.memory_scoped_retrieval import ...``
# works when the script is run as ``python scripts/run_latency_benchmark.py``
# (no package install required — mirrors cron/scheduler.py invocation pattern).
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Fixture dir is not a normal package (parent ``v11-latency-bench`` has a
# hyphen). We add it to sys.path and import by bare module name.
_FIXTURES_DIR = _REPO_ROOT / "tests" / "v11-latency-bench" / "fixtures"
if str(_FIXTURES_DIR) not in sys.path:
    sys.path.insert(0, str(_FIXTURES_DIR))

#: Map ``--fixture`` CLI arg to the seed-fixture module name + record count.
#: Both must stay in sync; the assertion in ``main`` guards drift.
_FIXTURE_TABLE = {
    100: ("seed_100_records", 100),
    500: ("seed_500_records", 500),
    1000: ("seed_1000_records", 1000),
}

#: p95 threshold (ms) per §4.2 acceptance check.
SLO_P95_THRESHOLD_MS: float = 500.0

#: Default number of sequential retrievals per §4.2 task (c).
DEFAULT_RUNS: int = 100


def _load_fixture_backend(fixture_count: int):
    """Import the seed fixture module by name; return its built backend."""
    if fixture_count not in _FIXTURE_TABLE:
        raise ValueError(
            f"unsupported --fixture {fixture_count}; "
            f"choose one of {sorted(_FIXTURE_TABLE)}"
        )
    module_name, expected_count = _FIXTURE_TABLE[fixture_count]
    module = importlib.import_module(module_name)
    backend = module.build_fixture_backend()
    actual = len(backend)
    if actual != expected_count:
        raise RuntimeError(
            f"fixture {module_name} returned backend with {actual} records; "
            f"expected {expected_count}"
        )
    return backend


def _load_live_backend():
    """Resolve the live mem0 backend via the Phase 60 plan 01 adapter.

    Returns the module-level singleton from
    ``plugins.memory.mem0.backend``. Raises ``SystemExit(2)`` with a
    clear stderr message if the backend is not available (no
    ``MEM0_API_KEY`` set), mirroring the convention from
    ``plugins/memory/mem0/scripts/batch_ingest.py:68``.
    """
    try:
        from plugins.memory.mem0 import backend as _backend
    except ImportError as exc:
        print(
            f"plugins.memory.mem0.backend adapter not importable: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(2)

    if not _backend.is_available():
        print(
            "MEM0_API_KEY not set. Set it in ~/.hermes/.env "
            "or use --fixture for CI runs.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return _backend


async def _run_benchmark(
    *,
    fixture_count: int | None,
    backend_mode: str | None,
    agent_id: str,
    record_count: int,
    runs: int,
) -> dict:
    """Run ``runs`` sequential retrievals against the configured backend.

    Two mutually-exclusive modes (per Task 2 plan):
    - ``backend_mode == "mem0"`` — live mem0 Platform API via
      ``_load_live_backend()``.
    - ``fixture_count is not None`` — deterministic fixture backend
      via ``_load_fixture_backend(fixture_count)``.

    Returns the result dict that gets JSON-serialized to ``--out``.
    """
    # Local import (after sys.path setup above) so the script fails late
    # and clearly if the agent module is missing.
    from agent.memory_scoped_retrieval import compute_percentiles, timed_retrieval

    if backend_mode == "mem0":
        backend = _load_live_backend()
        # record_count is supplied by the operator to disambiguate which
        # row of latency-baseline.md §2.2 the run corresponds to
        # (100/500/1000). The benchmark loop does NOT pre-seed; the
        # operator seeds separately via scripts/seed_mem0_backend.py.
        effective_record_count = record_count
    else:
        assert fixture_count is not None  # argparse mutually-exclusive group guarantees this
        backend = _load_fixture_backend(fixture_count)
        effective_record_count = fixture_count

    samples_ms: list[float] = []
    statuses: list[str] = []
    for _i in range(runs):
        sample = await timed_retrieval(
            query="benchmark query",
            agent_id=agent_id,
            backend=backend,
            top_k=5,
        )
        samples_ms.append(float(sample.latency_ms))
        statuses.append(sample.status)

    percentiles = compute_percentiles(samples_ms)
    slo_verdict = _compute_slo_verdict(statuses=statuses, p95=percentiles["p95"])

    return {
        "record_count": effective_record_count,
        "backend": backend_mode or "fixture",
        "agent_id": agent_id,
        "runs": runs,
        "samples_ms": samples_ms,
        "statuses": statuses,
        "percentiles": percentiles,
        "slo_threshold_ms": SLO_P95_THRESHOLD_MS,
        "slo_verdict": slo_verdict,
    }


def _compute_slo_verdict(*, statuses: list[str], p95: float) -> str:
    """Pick ``pass`` / ``fail`` / ``skip`` per §4.2 acceptance check.

    - If ANY call returned ``"ok"``: we have measurable latency data.
      Verdict is ``pass`` if p95 < threshold, else ``fail``.
    - If NO call returned ``"ok"`` (all ``unavailable`` or ``error``):
      verdict is ``skip`` — the SLO cannot be measured on this run.
      Operator must configure a live backend and re-run.
    """
    if any(s == "ok" for s in statuses):
        return "pass" if p95 < SLO_P95_THRESHOLD_MS else "fail"
    return "skip"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "EVAL-02 latency SLO benchmark (05-POC-PLAN.md §4.2 task c). "
            "Runs N sequential retrievals against a fixture or live mem0 "
            "backend and emits p50/p95/p99 JSON + SLO verdict."
        ),
    )
    # Mutually-exclusive backend selection (Phase 60 plan 01 Task 2).
    # ``required=True`` ensures exactly one of --fixture / --backend is passed.
    backend_group = parser.add_mutually_exclusive_group(required=True)
    backend_group.add_argument(
        "--fixture",
        type=int,
        choices=sorted(_FIXTURE_TABLE),
        default=None,
        help=(
            "Record count of the seed fixture: 100 (baseline), "
            "500 (SLO threshold), or 1000 (stress test). "
            "Mutually exclusive with --backend."
        ),
    )
    backend_group.add_argument(
        "--backend",
        choices=["mem0"],
        default=None,
        help=(
            "Live backend to benchmark (requires MEM0_API_KEY). "
            "Mutually exclusive with --fixture. Use --backend mem0 for "
            "production mem0 Platform API runs (Phase 60 plan 01 Task 2)."
        ),
    )
    parser.add_argument(
        "--agent-id",
        type=str,
        default="screenplay",
        help=(
            "Agent namespace to query (default: screenplay per "
            "60-CONTEXT.md decision #2; only used with --backend mem0)."
        ),
    )
    parser.add_argument(
        "--record-count",
        type=int,
        default=500,
        help=(
            "When --backend mem0, the record count of the pre-seeded "
            "store (100/500/1000 per latency-baseline.md §2.2). "
            "Default 500 (the formal SLO gate)."
        ),
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Output JSON path (will be written atomically).",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=DEFAULT_RUNS,
        help=f"Number of sequential retrievals (default {DEFAULT_RUNS} per §4.2).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    result = asyncio.run(
        _run_benchmark(
            fixture_count=args.fixture,
            backend_mode=args.backend,
            agent_id=args.agent_id,
            record_count=args.record_count,
            runs=args.runs,
        )
    )

    # Atomic write via utils.atomic_json_write (per CONTEXT.md
    # established patterns — temp file + fsync + os.replace). Falls back
    # to direct write only if utils is unavailable (e.g. script run from
    # outside the repo).
    out_path = Path(args.out)
    try:
        from utils import atomic_json_write
        atomic_json_write(out_path, result)
    except ImportError:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    # Human-readable summary on stdout. Includes backend token so the
    # operator can grep the run log for fixture vs live runs.
    pct = result["percentiles"]
    print(
        f"benchmark backend={result['backend']} "
        f"record_count={result['record_count']} runs={result['runs']} "
        f"p50={pct['p50']:.3f}ms p95={pct['p95']:.3f}ms p99={pct['p99']:.3f}ms "
        f"slo_verdict={result['slo_verdict']} "
        f"(threshold={result['slo_threshold_ms']}ms)"
    )
    print(f"results written to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
