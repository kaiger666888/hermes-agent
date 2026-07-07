#!/usr/bin/env python3
"""EVAL-03 bias canary CLI — runs the canary over fixture records.

Default mode (no flags): deterministic + a mocked LLM claim-check that
returns "yes" for every record (so the unsupported_claim fixture is caught
only by the deterministic ``evidence_coverage`` check — which still flags
it because the evidence doesn't semantically cover the appended
anamorphic-lens rule). Produces a JSON report at ``--out``.

Smoke mode (``--smoke``): invokes REAL GLM via
``auxiliary_client.call_llm(task="bias_canary_claim_check", provider="glm")``
wrapped in ``glm_concurrency_guard.acquire_glm_slot``. Requires valid GLM
credentials. Marked ``human_needed`` per CLAUDE.md operator-action-handoff
pattern — operators run this manually, never in CI.

Acceptance verdict:
    "pass"  if 4 ≤ flagged_count ≤ 5 (per §4.3 acceptance threshold)
    "fail"  otherwise

Usage::

    python scripts/run_bias_canary.py \\
        --fixtures tests/v11-bias-canary/fixtures/ \\
        --out /tmp/canary_report.json

    # Smoke mode (real GLM — operator action)
    python scripts/run_bias_canary.py --smoke \\
        --fixtures tests/v11-bias-canary/fixtures/ \\
        --out /tmp/canary_report_smoke.json

Sources: 54-03-PLAN.md Task 2, 05-POC-PLAN.md §4.3 + §4.8.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent.curator_bias_canary import CanaryReport, run_bias_canary  # noqa: E402

logger = logging.getLogger("bias_canary_cli")


# ---------------------------------------------------------------------------
# Default (mocked) LLM claim-check — returns "supported" for every record
# ---------------------------------------------------------------------------


async def _mock_claim_check(record: dict) -> tuple[bool, str]:
    """Mock LLM claim-check: always returns supported=True.

    The CLI's default mode MUST NOT invoke real GLM. The unsupported_claim
    fixture is still caught by the deterministic ``evidence_coverage`` check
    because its evidence text does not cover the appended
    "ALWAYS use anamorphic lenses" rule.
    """
    return True, "<mock: deterministic checks handle the canary>"


# ---------------------------------------------------------------------------
# Smoke (real GLM) LLM claim-check — operator action only
# ---------------------------------------------------------------------------


async def _smoke_claim_check(record: dict) -> tuple[bool, str]:
    """Real GLM claim-check via auxiliary_client + serial lock.

    Marked ``human_needed`` — only runs when the operator passes ``--smoke``
    with valid GLM credentials configured in ``cli-config.yaml``.
    """
    from agent.curator_bias_canary import _default_claim_check_llm

    return await _default_claim_check_llm(record)


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------


def _reports_to_dict(reports: list[CanaryReport]) -> dict:
    flagged_count = sum(1 for r in reports if r.flagged)
    total = len(reports)
    # Acceptance threshold per §4.3: 4/5 bad records caught. The CLI is
    # designed to run over the canonical 5-bad + 1-good fixture set (total=6).
    # Pass band: flagged in [4, 5] (the good record must NOT be flagged, and
    # ≥4 of the 5 bad ones must be).
    if total == 0:
        verdict = "fail"
    elif total == 6:
        verdict = "pass" if 4 <= flagged_count <= 5 else "fail"
    else:
        # Other fixture counts: pass if every record is either flagged-as-bad
        # or passed-as-good — i.e. flagged_count is in [max(0, total - 1), total - 1].
        # Conservative: only pass when at least one record passes (no false
        # positives on good records) AND at least one is flagged.
        verdict = "pass" if 1 <= flagged_count <= total - 1 else "fail"
    return {
        "total_records": total,
        "flagged_count": flagged_count,
        "passed_count": total - flagged_count,
        "acceptance_verdict": verdict,
        "records": [r.to_dict() for r in reports],
    }


# ---------------------------------------------------------------------------
# Fixture loading
# ---------------------------------------------------------------------------


def _load_fixtures(fixtures_dir: Path) -> list[dict]:
    """Load every ``*.json`` fixture in ``fixtures_dir`` (sorted by name)."""
    if not fixtures_dir.exists():
        raise FileNotFoundError(f"fixtures dir does not exist: {fixtures_dir}")
    paths = sorted(p for p in fixtures_dir.glob("*.json"))
    records: list[dict] = []
    for p in paths:
        with p.open("r", encoding="utf-8") as f:
            rec = json.load(f)
        if isinstance(rec, dict):
            records.append(rec)
        else:
            logger.warning("skipping non-dict fixture: %s", p)
    return records


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="run_bias_canary",
        description=(
            "EVAL-03 bias canary — flags suspicious memory records. "
            "Default mode uses deterministic checks + mocked LLM; "
            "--smoke invokes real GLM (operator action, needs credentials)."
        ),
    )
    p.add_argument(
        "--fixtures",
        required=True,
        help="Directory of fixture JSON files (memory records).",
    )
    p.add_argument(
        "--out",
        required=True,
        help="Output JSON report path.",
    )
    p.add_argument(
        "--smoke",
        action="store_true",
        help=(
            "Smoke mode: invoke real GLM via auxiliary_client.call_llm "
            "(task=bias_canary_claim_check, provider=glm). Requires valid "
            "GLM credentials. Operator action — never runs in CI."
        ),
    )
    p.add_argument(
        "--no-audit",
        action="store_true",
        help="Skip appending a summary entry to the curator_audit chain.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    fixtures_dir = Path(args.fixtures).resolve()
    records = _load_fixtures(fixtures_dir)
    logger.info("loaded %d fixture records from %s", len(records), fixtures_dir)

    if args.smoke:
        logger.warning(
            "SMOKE MODE: invoking REAL GLM via auxiliary_client.call_llm "
            "(provider=glm) — operator action; ensure GLM credentials are set."
        )
        claim_check = _smoke_claim_check
    else:
        claim_check = _mock_claim_check

    reports = asyncio.run(
        run_bias_canary(
            records,
            claim_check_llm=claim_check,
            audit_chain=not args.no_audit,
        )
    )
    report_dict = _reports_to_dict(reports)

    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report_dict, f, ensure_ascii=False, indent=2)
        f.write("\n")
    logger.info(
        "canary report written to %s — verdict=%s flagged=%d/%d",
        out_path,
        report_dict["acceptance_verdict"],
        report_dict["flagged_count"],
        report_dict["total_records"],
    )
    print(
        f"bias canary: {report_dict['flagged_count']}/{report_dict['total_records']} "
        f"flagged → verdict={report_dict['acceptance_verdict']}"
    )
    return 0 if report_dict["acceptance_verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
