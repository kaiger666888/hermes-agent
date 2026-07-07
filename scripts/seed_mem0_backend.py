#!/usr/bin/env python3
"""Idempotent seeder for the live mem0 backend (Phase 60 plan 01 Task 1).

Mirrors the deterministic 500-record pattern in
``tests/v11-latency-bench/fixtures/seed_500_records.py`` but writes to the
*live* mem0 Platform API via the new ``plugins.memory.mem0.backend``
adapter wired in this same task.

Two modes:

1. **Dry-run (default for CI / no credentials):**

       python3 scripts/seed_mem0_backend.py --dry-run --count 500

   Enumerates the records and prints ``would seed ...`` lines WITHOUT
   touching the network. Exits 0. Required for the script to be useful in
   environments without ``MEM0_API_KEY`` (mirrors
   ``plugins/memory/mem0/scripts/batch_ingest.py:68``).

2. **Live (operator with MEM0_API_KEY):**

       MEM0_API_KEY=<key> python3 scripts/seed_mem0_backend.py \\
           --agent-id screenplay --count 500

   Calls ``backend.add()`` once per record. ~50-300ms per call (per
   ``latency-baseline.md §3.1``) ⇒ 500 records ≈ 1-4 minutes. Prints a
   greppable final line:

       seeded count=500 agent_id=screenplay elapsed_s=XX.X idempotency_key=phase60-eval01-seed

Idempotency
-----------
Every record's content is prefixed with the ``--idempotency-key`` so
re-runs can identify + skip already-seeded records via
``mem0_search`` (avoids duplicate inserts across operator re-runs). The
key defaults to ``phase60-eval01-seed``.

Record schema (mirrors fixture for cross-comparable benchmark numbers):
    content:    f"[{idempotency_key}] record {i}/{count} for agent {agent_id}: deterministic content #{i}"
    agent_id:   <args.agent_id>   (default: screenplay per CONTEXT.md decision #2)
    scope:      per_agent         (CR-01: coerced to "session" at arbitration time)
    confidence: 0.5
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# sys.path bootstrap — mirror scripts/run_latency_benchmark.py:48-57
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


_DEFAULT_AGENT_ID = "screenplay"  # CONTEXT.md decision #2 (NOT fixture's ag1)
_DEFAULT_COUNT = 500
_DEFAULT_IDEMPOTENCY_KEY = "phase60-eval01-seed"
_VALID_COUNTS = (100, 500, 1000)  # latency-baseline.md §2.2 three-row table


def _build_record_content(
    *,
    idempotency_key: str,
    index: int,
    count: int,
    agent_id: str,
) -> str:
    """Deterministic record body. Same pattern as seed_500_records.py.

    The leading idempotency-key bracket lets a re-run grep live memory
    for ``[{key}]`` and skip already-seeded records without re-inserting.
    """
    return (
        f"[{idempotency_key}] record {index}/{count} "
        f"for agent {agent_id}: deterministic content #{index}"
    )


def _enumerate_records(
    *,
    count: int,
    agent_id: str,
    idempotency_key: str,
):
    """Yield (index, content) tuples for every record to be seeded."""
    for i in range(1, count + 1):
        content = _build_record_content(
            idempotency_key=idempotency_key,
            index=i,
            count=count,
            agent_id=agent_id,
        )
        yield i, content


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Seed the live mem0 backend with N deterministic records for "
            "the EVAL-01 latency benchmark (Phase 60 plan 01 Task 1)."
        ),
    )
    parser.add_argument(
        "--agent-id",
        default=_DEFAULT_AGENT_ID,
        help=(
            f"Agent namespace to seed into (default: {_DEFAULT_AGENT_ID} "
            "per 60-CONTEXT.md decision #2)."
        ),
    )
    parser.add_argument(
        "--count",
        type=int,
        default=_DEFAULT_COUNT,
        choices=_VALID_COUNTS,
        help=(
            f"Number of records to seed (default: {_DEFAULT_COUNT}). "
            f"Must be one of {list(_VALID_COUNTS)} per the 3-row table "
            "in latency-baseline.md §2.2."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Enumerate + print records WITHOUT calling backend.add(). "
            "Use this mode when MEM0_API_KEY is not set."
        ),
    )
    parser.add_argument(
        "--idempotency-key",
        default=_DEFAULT_IDEMPOTENCY_KEY,
        help=(
            f"Content-prefix used to dedupe re-runs (default: "
            f"{_DEFAULT_IDEMPOTENCY_KEY}). Every record's content is "
            "prefixed with this key so a re-run can identify + skip "
            "already-seeded records."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.dry_run:
        # Dry-run path — no credentials required.
        for i, content in _enumerate_records(
            count=args.count,
            agent_id=args.agent_id,
            idempotency_key=args.idempotency_key,
        ):
            print(f"would seed index={i} agent_id={args.agent_id} content={content!r}")
        print(
            f"dry-run count={args.count} agent_id={args.agent_id} "
            f"idempotency_key={args.idempotency_key}"
        )
        return 0

    # Live path — require MEM0_API_KEY
    from plugins.memory.mem0 import backend  # noqa: PLC0415 — lazy import keeps --dry-run hermetic

    if not backend.is_available():
        print(
            "MEM0_API_KEY not set. Run with --dry-run, or set MEM0_API_KEY "
            "in ~/.hermes/.env",
            file=sys.stderr,
        )
        return 2

    t0 = time.perf_counter()
    seeded = 0
    for i, content in _enumerate_records(
        count=args.count,
        agent_id=args.agent_id,
        idempotency_key=args.idempotency_key,
    ):
        record_id = backend.add(
            content=content,
            agent_id=args.agent_id,
            scope="per_agent",  # CR-01: coerced to "session" at arbitration
            confidence=0.5,
        )
        if record_id is None:
            print(
                f"WARNING: backend.add returned None for index={i} — "
                "record may not have been stored. Continuing.",
                file=sys.stderr,
            )
        else:
            seeded += 1
        # Progress every 50 records (avoid stdout spam).
        if i % 50 == 0 or i == args.count:
            print(
                f"progress seeded={seeded}/{args.count} "
                f"agent_id={args.agent_id} last_index={i}",
                flush=True,
            )

    elapsed_s = time.perf_counter() - t0
    print(
        f"seeded count={seeded} agent_id={args.agent_id} "
        f"elapsed_s={elapsed_s:.1f} idempotency_key={args.idempotency_key}"
    )
    return 0 if seeded == args.count else 1


if __name__ == "__main__":
    raise SystemExit(main())
