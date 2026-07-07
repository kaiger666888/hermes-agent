"""Integration tests for EVAL-03 bias canary (54-03 Task 2).

Behavior per 54-03-PLAN.md Task 2:
  - Test 1 (acceptance — 4/5 caught): 5 bad fixtures → ≥4 flagged
  - Test 2 (false positive): good_record_multi_operator → not flagged
  - Test 3 (CLI subprocess): produces JSON report with acceptance_verdict=pass
  - Test 4 (audit chain): run_bias_canary(audit_chain=True) appends an entry
    to the curator_audit chain; verify_chain returns no breaks
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_fixture(name: str) -> dict:
    path = FIXTURES_DIR / name
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


BAD_FIXTURE_NAMES = [
    "bad_record_single_operator.json",
    "bad_record_low_evidence.json",
    "bad_record_unsupported_claim.json",
    "bad_record_low_confidence.json",
    "bad_record_no_operator_id.json",
]


async def _stub_claim_check(record: dict) -> tuple[bool, str]:
    """Mock LLM claim-check: returns 'no' for unsupported_claim fixture only.

    All other records (including the unsupported_claim in CLI default mode)
    are handled by the deterministic checks anyway; this stub demonstrates
    that the LLM pass is wired through the run_bias_canary signature.
    Signature must match ``run_bias_canary``'s ``claim_check_llm`` contract:
    ``async (record) -> (supported, reason)``.
    """
    rid = record.get("record_id", "")
    if rid == "bad-unsupported-claim":
        return False, "claim includes anamorphic-lens rule absent from evidence"
    return True, "claim supported by evidence"


# --------------------------------------------------------------------------- #
# Test 1 — acceptance (4/5 bad records caught)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_acceptance_four_of_five_bad_records_caught():
    """5 bad-record fixtures → ≥4 flagged by run_bias_canary."""
    from agent.curator_bias_canary import run_bias_canary

    bad_records = [_load_fixture(n) for n in BAD_FIXTURE_NAMES]
    reports = await run_bias_canary(
        bad_records,
        claim_check_llm=_stub_claim_check,
        audit_chain=False,
    )
    flagged = sum(1 for r in reports if r.flagged)
    assert flagged >= 4, (
        f"acceptance threshold is 4/5, only {flagged}/5 flagged — "
        f"failed_record_ids={[r.record_id for r in reports if not r.flagged]}"
    )


@pytest.mark.asyncio
async def test_each_bad_record_triggers_expected_check():
    """Each bad fixture triggers its targeted check (per _canary_expected_failure)."""
    from agent.curator_bias_canary import run_bias_canary

    bad_records = [_load_fixture(n) for n in BAD_FIXTURE_NAMES]
    reports = await run_bias_canary(
        bad_records,
        claim_check_llm=_stub_claim_check,
        audit_chain=False,
    )
    by_id = {r.record_id: r for r in reports}
    expectations = {
        "bad-single-operator": {"operator_diversity"},
        "bad-low-evidence": {"evidence_coverage"},
        "bad-unsupported-claim": {"claim_support"},
        "bad-low-confidence": {"confidence_threshold"},
        "bad-no-operator-id": {"operator_diversity"},
    }
    for rid, expected_checks in expectations.items():
        assert rid in by_id, f"missing report for {rid}"
        report = by_id[rid]
        # Each expected check must be in the failed list.
        for chk in expected_checks:
            assert chk in report.checks_failed, (
                f"{rid}: expected {chk} in checks_failed, "
                f"got checks_failed={report.checks_failed}"
            )


# --------------------------------------------------------------------------- #
# Test 2 — false positive (good record accepted)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_good_record_multi_operator_not_flagged():
    """good_record_multi_operator.json passes ALL checks (no false positive)."""
    from agent.curator_bias_canary import run_bias_canary

    good_record = _load_fixture("good_record_multi_operator.json")
    reports = await run_bias_canary(
        [good_record],
        claim_check_llm=_stub_claim_check,
        audit_chain=False,
    )
    assert len(reports) == 1
    report = reports[0]
    assert report.flagged is False, (
        f"good record flagged (false positive): checks_failed={report.checks_failed} "
        f"details={report.details}"
    )
    assert "evidence_coverage" in report.checks_passed
    assert "operator_diversity" in report.checks_passed
    assert "confidence_threshold" in report.checks_passed
    assert "claim_support" in report.checks_passed


def test_check_record_deterministic_only_on_good_fixture():
    """check_record (no LLM) on good fixture passes all deterministic checks."""
    from agent.curator_bias_canary import check_record

    good_record = _load_fixture("good_record_multi_operator.json")
    report = check_record(good_record)
    assert report.flagged is False
    assert set(report.checks_passed) >= {
        "evidence_coverage",
        "operator_diversity",
        "confidence_threshold",
    }


# --------------------------------------------------------------------------- #
# Test 3 — CLI subprocess end-to-end
# --------------------------------------------------------------------------- #


def test_cli_run_bias_canary_acceptance_pass(tmp_path):
    """python scripts/run_bias_canary.py → JSON report with acceptance_verdict=pass."""
    out_path = tmp_path / "canary_report.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "run_bias_canary.py"),
            "--fixtures",
            str(FIXTURES_DIR),
            "--out",
            str(out_path),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=60,
    )
    assert result.returncode == 0, (
        f"CLI failed (rc={result.returncode}):\nstdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    assert out_path.exists(), f"output file not written: {out_path}"
    with out_path.open("r", encoding="utf-8") as f:
        report = json.load(f)
    assert report["total_records"] == 6, f"expected 6 records, got {report['total_records']}"
    assert 4 <= report["flagged_count"] <= 5, (
        f"expected 4-5 flagged, got {report['flagged_count']}"
    )
    assert report["acceptance_verdict"] == "pass", (
        f"expected verdict=pass, got {report['acceptance_verdict']}"
    )


def test_cli_run_bias_canary_emits_per_record_flags(tmp_path):
    """CLI JSON report contains per-record details with checks_failed lists."""
    out_path = tmp_path / "canary_report.json"
    subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "run_bias_canary.py"),
            "--fixtures",
            str(FIXTURES_DIR),
            "--out",
            str(out_path),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=60,
        check=True,
    )
    with out_path.open("r", encoding="utf-8") as f:
        report = json.load(f)
    assert "records" in report
    assert len(report["records"]) == 6
    # Each record entry has the required fields.
    for entry in report["records"]:
        assert "record_id" in entry
        assert "flagged" in entry
        assert "checks_failed" in entry
        assert "checks_passed" in entry


# --------------------------------------------------------------------------- #
# Test 4 — audit chain (T-54-09 mitigation)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_audit_chain_appended_on_run(tmp_path, monkeypatch):
    """run_bias_canary(audit_chain=True) appends to curator_audit chain."""
    from agent import curator_audit
    from agent.curator_bias_canary import run_bias_canary

    # Redirect HERMES_HOME to a tmp dir so the audit log lands there.
    hermes_home = tmp_path / "hermes"
    hermes_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    bad_records = [_load_fixture(n) for n in BAD_FIXTURE_NAMES]
    reports = await run_bias_canary(
        bad_records,
        claim_check_llm=_stub_claim_check,
        audit_chain=True,
    )
    assert len(reports) == 5

    # Verify the audit log exists and chain is intact.
    breaks = curator_audit.verify_chain()
    assert breaks == [], f"audit chain has breaks: {breaks}"

    # At least one entry should be present with our bias_canary marker.
    # curator_audit writes to <HERMES_HOME>/skills/.audit/log.jsonl.
    audit_path = hermes_home / "skills" / ".audit" / "log.jsonl"
    assert audit_path.exists(), f"audit log not written at {audit_path}"
    found_bias_canary_entry = False
    with audit_path.open("r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            if entry.get("action") == "auto_apply" and entry.get("operator") == "system":
                eval_score = entry.get("eval_score") or {}
                if "bias_canary" in eval_score:
                    found_bias_canary_entry = True
                    bc = eval_score["bias_canary"]
                    assert bc["total_records"] == 5
                    assert bc["flagged_count"] >= 4
                    break
    assert found_bias_canary_entry, "no bias_canary entry in audit chain"


# --------------------------------------------------------------------------- #
# Test 5 — CLI smoke flag is wired (does NOT actually invoke GLM in unit test)
# --------------------------------------------------------------------------- #


def test_cli_smoke_flag_documented():
    """--smoke flag exists in CLI help text (operator-action handoff marker)."""
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "run_bias_canary.py"),
            "--help",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=30,
    )
    assert result.returncode == 0
    assert "--smoke" in result.stdout, "CLI --smoke flag not documented in help"
