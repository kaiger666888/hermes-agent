#!/usr/bin/env python3
"""Milestone Audit Coverage Matrix Producer (v11.0 + v12.0 aware).

Automates the audit evidence walk for the v11.0 PoC implementation milestone
AND the v12.0 Production Hardening milestone. This script reads a requirements
traceability table + the prior-phase VERIFICATION.md frontmatter blocks,
cross-references REQ-ID to its phase's verification status, and emits a JSON
coverage matrix that drives the milestone verdict.

Inputs (read-only, must exist relative to repo root):
- v11.0 mode: `.planning/milestones/v11.0-REQUIREMENTS.md` (frozen 15-row table)
  + 4 prior-phase VERIFICATION.md (Phases 52-55)
- v12.0 mode: `.planning/REQUIREMENTS.md` (live 8-row table)
  + 4 prior-phase VERIFICATION.md (Phases 57-60)

Output (JSON to stdout, optionally to `--out <path>`):
- `milestone`: "v11.0" | "v12.0"
- `audited_at`: ISO8601 UTC
- `total_reqs`: int
- `satisfied_reqs`: int (reqs whose phase verification_status == "passed")
- `human_needed_reqs`: int (reqs whose phase verification_status == "human_needed")
- `failed_reqs`: int (reqs whose phase verification_status == "failed" or unknown)
- `operator_action_count`: int (total human_verification entries aggregated)
- `verdict_logic`: object with recommended_verdict + boolean sub-checks
- `reqs`: list of per-req row objects

Verdict logic (per Phase 56 / Phase 61 CONTEXT.md verdict strategy):
- `passed` if all reqs have verification_status in {passed, human_needed} AND
  all human_needed items have documented operator-action runbook entries
  (i.e. NOT silently missing).
- `tech_debt` if any req has partial verification but no fundamental gap.
- `gaps_found` if any req lacks automated verification entirely.
- `fail` if any req fundamentally unmet (would require milestone rework).

Operator-action handling convention: per the autonomous workflow, an item
marked `human_needed` is NOT a blocking design gap. It is a runtime validation
of code that is fully implemented and automated-test-verified.

CLI:
- `python3 scripts/run_milestone_audit.py` — v11.0 default (backward compat).
- `python3 scripts/run_milestone_audit.py --milestone v11.0` — explicit v11.0.
- `python3 scripts/run_milestone_audit.py --milestone v12.0` — v12.0 mode.
- `--out <path>` — also write JSON to file.
- `--help` — usage banner.

Stdlib-only (no third-party deps) per CLAUDE.md conventions; Python 3.11+.
Every `open()` passes `encoding="utf-8"` (Ruff PLW1514 rule).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path
from typing import Any

# Repo root = directory containing this script's parent (scripts/ at repo top).
# Resolve lazily so the script remains location-independent.
REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Milestone-scoped data tables
# ---------------------------------------------------------------------------
#
# Each milestone (v11.0, v12.0) has its own:
#   - requirements file (where the traceability table lives)
#   - set of prior-phase VERIFICATION.md files to parse
#   - REQ-ID regex matching that milestone's req namespace
#   - human-verification map (phase -> list of req-ids in declared order)
#   - audit self-phase (the phase number of the audit itself, e.g. 56 / 61)
#   - operator-action floor (minimum handoffs expected for verdict=passed)
#
# v11.0 behavior MUST remain byte-identical when invoked with `--milestone v11.0`
# (or no flag). The v11.0 audit shipped as `.planning/milestones/v11.0-MILESTONE-AUDIT.md`
# must remain reproducible from the frozen v11.0-REQUIREMENTS.md snapshot.

MILESTONE_REQUIREMENTS_FILES: dict[str, Path] = {
    # v11.0 requirements were frozen at milestone tag — live REQUIREMENTS.md
    # has been overwritten by v12.0. Frozen snapshot is authoritative.
    "v11.0": REPO_ROOT / ".planning" / "milestones" / "v11.0-REQUIREMENTS.md",
    # v12.0 is the live milestone — read the current REQUIREMENTS.md.
    "v12.0": REPO_ROOT / ".planning" / "REQUIREMENTS.md",
}

MILESTONE_PHASE_VERIFICATION_FILES: dict[str, dict[str, Path]] = {
    "v11.0": {
        "52": REPO_ROOT / ".planning" / "phases" / "52-infra-foundation" / "52-VERIFICATION.md",
        "53": REPO_ROOT / ".planning" / "phases" / "53-creative-slice" / "53-VERIFICATION.md",
        "54": REPO_ROOT / ".planning" / "phases" / "54-eval-harness-1" / "54-VERIFICATION.md",
        "55": REPO_ROOT / ".planning" / "phases" / "55-eval-harness-2" / "55-VERIFICATION.md",
    },
    "v12.0": {
        "57": REPO_ROOT / ".planning" / "phases" / "57-endpoint-routing" / "57-VERIFICATION.md",
        "58": REPO_ROOT / ".planning" / "phases" / "58-rpm-throttling" / "58-VERIFICATION.md",
        "59": REPO_ROOT / ".planning" / "phases" / "59-aux-pool-isolation" / "59-VERIFICATION.md",
        "60": REPO_ROOT / ".planning" / "phases" / "60-live-eval" / "60-VERIFICATION.md",
    },
}

MILESTONE_REQ_ID_PATTERNS: dict[str, re.Pattern[str]] = {
    "v11.0": re.compile(
        r"^(INFRA-0[1-4]|CREATIVE-0[1-2]|EVAL-0[1-7]|MIGR-01|VALIDATE-01)$"
    ),
    "v12.0": re.compile(
        r"^(ENDPOINT-01|THROTTLE-0[1-2]|POOL-0[1-2]|EVAL-0[1-2]|VALIDATE-01)$"
    ),
}

# Regex used in `_parse_req_coverage_table` to early-filter candidate rows
# (must start with `| <REQ-ID>` where REQ-ID ends in 2 digits). Cheaper than
# the full row_re.match below. Tolerates markdown bold (`**REQ-ID**`).
REQ_ID_PATTERN_END = re.compile(r"^\|\s*\*{0,2}[A-Z]+-[0-9]{2}\*{0,2}\s*\|")

# Traceability table row regex: `| REQ-ID | Phase | Category | PD | Status |`
TRACE_ROW_PATTERN = re.compile(
    r"^\|\s*([A-Z]+-[0-9]{2})\s*\|\s*([0-9]{2})\s*\|\s*([A-Z]+)\s*\|"
)

MILESTONE_HUMAN_VERIFICATION_REQ_MAP: dict[str, dict[str, list[str]]] = {
    "v11.0": {
        # Phase 53: 1 handoff — screenplay_step3_roundtable → SC#2 / CREATIVE-01
        "53": ["CREATIVE-01"],
        # Phase 54: 3 handoffs in order — fitness / latency / bias_canary
        "54": ["EVAL-01", "EVAL-02", "EVAL-03"],
        # Phase 55: 1 handoff — compaction → EVAL-04
        "55": ["EVAL-04"],
    },
    "v12.0": {
        # Phase 57: 1 handoff — SC#2 live GLM smoke (deferred to P61 per ROADMAP).
        # Phase 57 owns only ENDPOINT-01; SC#2 is its production smoke.
        "57": ["ENDPOINT-01"],
        # Phase 60: 2 handoffs — mem0 benchmark + fitness battery real-mode
        # (order matches 60-VERIFICATION.md frontmatter human_verification:).
        "60": ["EVAL-01", "EVAL-02"],
    },
}

MILESTONE_AUDIT_SELF_PHASE: dict[str, str] = {
    "v11.0": "56",  # Phase 56 = v11.0 audit (VALIDATE-01 self-confirming)
    "v12.0": "61",  # Phase 61 = v12.0 audit (VALIDATE-01 self-confirming)
}

MILESTONE_OPERATOR_ACTION_FLOOR: dict[str, int] = {
    "v11.0": 5,   # 1 from P53 + 3 from P54 + 1 from P55 = 5 expected
    "v12.0": 3,   # 1 from P57 + 2 from P60 = 3 expected
}

# Audit-self-phase status: VALIDATE-01 always maps to this script's output
# (mirror Phase 56 precedent).
AUDIT_SELF_PHASE_STATUS = "passed"


def _parse_requirements(req_file: Path, req_id_pattern: re.Pattern[str]) -> list[dict[str, str]]:
    """Parse the traceability table from a requirements file.

    Returns a list of dicts: ``{"req_id": ..., "phase": ..., "category": ...}``.
    """
    if not req_file.exists():
        raise FileNotFoundError(f"Requirements file missing: {req_file}")
    text = req_file.read_text(encoding="utf-8")
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        m = TRACE_ROW_PATTERN.match(line)
        if not m:
            continue
        req_id, phase, category = m.group(1), m.group(2), m.group(3)
        if not req_id_pattern.match(req_id):
            continue
        rows.append(
            {"req_id": req_id, "phase": phase, "category": category}
        )
    return rows


def _extract_frontmatter(text: str) -> dict[str, Any]:
    """Hand-rolled parser for the limited YAML frontmatter we emit.

    Handles the small subset actually used in VERIFICATION.md files:
    - top-level `key: value` pairs (string / int / bool / "n/a")
    - nested list-of-dicts under `human_verification:` (each entry has
      `test`, `expected`, `why_human`)

    Anything else is captured under `extras` for forward-compat. Malformed
    lines log to stderr and are skipped (never raise) — per T-56-01 mitigation.
    """
    if not text.startswith("---"):
        return {}
    # Find the closing frontmatter delimiter.
    end_idx = text.find("\n---", 3)
    if end_idx < 0:
        return {}
    block = text[3:end_idx]
    data: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[dict[str, str]] | None = None
    current_dict: dict[str, str] | None = None
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        # List-item under human_verification: "  - test: ..."
        m = re.match(r"^\s+-\s+([a-z_]+):\s*(.*)$", line)
        if m and current_key and isinstance(data.get(current_key), list):
            field_name, field_value = m.group(1), m.group(2).strip()
            # Strip surrounding quotes if present.
            if field_value.startswith('"') and field_value.endswith('"'):
                field_value = field_value[1:-1]
            # Flush prior in-progress dict before starting a new one.
            if current_dict is not None and current_list is not None:
                current_list.append(current_dict)
            current_dict = {field_name: field_value}
            continue
        # Nested key continuation: "    why_human: ..."
        m = re.match(r"^\s+([a-z_]+):\s*(.*)$", line)
        if m and current_dict is not None:
            field_name, field_value = m.group(1), m.group(2).strip()
            if field_value.startswith('"') and field_value.endswith('"'):
                field_value = field_value[1:-1]
            current_dict[field_name] = field_value
            continue
        # Top-level key: "key: value"
        m = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if m:
            # Flush any in-progress list-of-dicts entry.
            if current_dict is not None and current_list is not None:
                current_list.append(current_dict)
                current_dict = None
            key, value = m.group(1), m.group(2).strip()
            if value == "":
                # Start of a nested structure (likely human_verification:).
                current_list = []
                data[key] = current_list
                current_key = key
            else:
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                data[key] = value
                current_key = key
                current_list = None
    # Flush trailing.
    if current_dict is not None and current_list is not None:
        current_list.append(current_dict)
    return data


def _parse_verification(phase: str, path: Path, req_id_pattern: re.Pattern[str]) -> dict[str, Any]:
    """Parse a VERIFICATION.md frontmatter + per-req Coverage rows.

    Returns a dict with keys: ``status`` (phase-level), ``score``, ``score_num``,
    ``score_den``, ``human_verification`` (list of dicts), ``req_coverage``
    (dict of {req_id: {status: SATISFIED | NEEDS_HUMAN | UNKNOWN, evidence: str}}),
    ``parse_error`` (set if anything went wrong). Never raises — per T-56-01 mitigation.
    """
    result: dict[str, Any] = {
        "phase": phase,
        "path": str(path.relative_to(REPO_ROOT)) if path.exists() else str(path),
        "status": "unknown",
        "score": "",
        "score_num": 0,
        "score_den": 0,
        "human_verification": [],
        "req_coverage": {},
        "parse_error": None,
    }
    if not path.exists():
        result["parse_error"] = f"verification file missing: {path}"
        print(f"[audit] WARNING: {result['parse_error']}", file=sys.stderr)
        return result
    try:
        text = path.read_text(encoding="utf-8")
        fm = _extract_frontmatter(text)
        result["status"] = fm.get("status", "unknown")
        score = str(fm.get("score", ""))
        result["score"] = score
        # Split "4/4 must-haves verified" → num=4, den=4
        m = re.match(r"^\s*(\d+)\s*/\s*(\d+)", score)
        if m:
            result["score_num"] = int(m.group(1))
            result["score_den"] = int(m.group(2))
        hv = fm.get("human_verification", [])
        if isinstance(hv, list):
            result["human_verification"] = hv
        # Parse the Requirements Coverage table (per-req rows).
        result["req_coverage"] = _parse_req_coverage_table(text, req_id_pattern)
    except Exception as exc:  # noqa: BLE001 — best-effort parser per T-56-01
        result["parse_error"] = f"{type(exc).__name__}: {exc}"
        result["status"] = "unknown"
        print(f"[audit] WARNING: parse error in {path}: {exc}", file=sys.stderr)
    return result


def _parse_req_coverage_table(text: str, req_id_pattern: re.Pattern[str]) -> dict[str, dict[str, str]]:
    """Parse `| REQ-ID | plan | desc | status | evidence |` rows.

    Returns {req_id: {"status": "SATISFIED" | "NEEDS_HUMAN" | "UNKNOWN",
    "evidence": str}}. The `status` column text we look for:
    - "✓ SATISFIED" → SATISFIED
    - "⚠ NEEDS HUMAN" / "⚠ HUMAN_NEEDED" → NEEDS_HUMAN
    - anything else → UNKNOWN
    """
    out: dict[str, dict[str, str]] = {}
    # Match table rows whose first column is a REQ-ID. Capture: req_id, status
    # cell (4th column), and 5th column (evidence). Tolerate the leading
    # emoji or symbol.
    row_re = re.compile(
        r"^\|\s*\*{0,2}([A-Z]+-[0-9]{2})\*{0,2}\s*\|"  # req_id (tolerate **bold**)
        r"[^|]*\|"                       # plan column
        r"[^|]*\|"                       # description column
        r"\s*([^|]*?)\s*\|"              # status column (4th)
        r"\s*([^|]*)\|",                 # evidence column (5th) — remainder of row
    )
    for line in text.splitlines():
        if not REQ_ID_PATTERN_END.match(line):
            continue
        m = row_re.match(line)
        if not m:
            continue
        req_id = m.group(1)
        # Filter to req-ids belonging to the current milestone namespace.
        if not req_id_pattern.match(req_id):
            continue
        status_cell = m.group(2).strip()
        evidence = m.group(3).strip()
        if "SATISFIED" in status_cell.upper():
            parsed_status = "SATISFIED"
        elif "NEEDS HUMAN" in status_cell.upper() or "HUMAN_NEEDED" in status_cell.upper():
            parsed_status = "NEEDS_HUMAN"
        else:
            parsed_status = "UNKNOWN"
        out[req_id] = {"status": parsed_status, "evidence": evidence}
    return out


def _build_coverage_matrix(
    milestone: str,
    reqs: list[dict[str, str]],
    verifications: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Cross-reference REQ-ID to its phase's verification status.

    Per-req status resolution:
    1. Look up the req in its phase's `req_coverage` table (parsed from
       Requirements Coverage section). If SATISFIED → `passed`.
    2. If the req_id is in `MILESTONE_HUMAN_VERIFICATION_REQ_MAP[ms][phase]`
       → `human_needed` AND attach the corresponding `human_verification`
       entry as an operator-action handoff.
    3. Audit-self phase (e.g. Phase 56 / 61) is hard-coded to `passed` for
       VALIDATE-01.
    """
    req_rows: list[dict[str, Any]] = []
    satisfied = 0
    human_needed = 0
    failed = 0
    operator_action_count = 0

    audit_self_phase = MILESTONE_AUDIT_SELF_PHASE[milestone]
    handoff_map = MILESTONE_HUMAN_VERIFICATION_REQ_MAP[milestone]

    for req in reqs:
        req_id = req["req_id"]
        phase = req["phase"]
        if phase == audit_self_phase:
            # Audit-self phase — VALIDATE-01 maps to this script's output.
            v_status = AUDIT_SELF_PHASE_STATUS
            audit_doc = (
                "v11.0-MILESTONE-AUDIT.md" if milestone == "v11.0"
                else "v12.0-MILESTONE-AUDIT.md"
            )
            evidence = (
                f".planning/milestones/{audit_doc} §2 VALIDATE-01 row "
                "(this audit)"
            )
            operator_actions: list[dict[str, str]] = []
            plan = f"{phase}-01"
        else:
            ver = verifications.get(phase, {})
            req_cov = ver.get("req_coverage", {})
            plan = f"{phase}-01"
            # Resolve per-req status.
            cov = req_cov.get(req_id, {})
            cov_status = cov.get("status", "UNKNOWN")
            handoff_reqs = handoff_map.get(phase, [])
            hv_entries = ver.get("human_verification", [])
            if not isinstance(hv_entries, list):
                hv_entries = []

            if req_id in handoff_reqs:
                # Find the corresponding human_verification entry by index
                # (stable ordering per handoff_map docstring).
                try:
                    idx = handoff_reqs.index(req_id)
                    op_action = (
                        hv_entries[idx] if idx < len(hv_entries) else {}
                    )
                except (ValueError, IndexError):
                    op_action = {}
                operator_actions = [op_action] if op_action else []
                v_status = "human_needed"
            elif cov_status == "SATISFIED":
                operator_actions = []
                v_status = "passed"
            elif cov_status == "NEEDS_HUMAN":
                operator_actions = []
                v_status = "human_needed"
            elif cov_status == "UNKNOWN":
                # Fallback to phase-level status if per-req parsing failed.
                operator_actions = []
                v_status = ver.get("status", "unknown")
            else:
                operator_actions = []
                v_status = ver.get("status", "unknown")
            evidence = (
                f".planning/phases/{phase}-*/{phase}-VERIFICATION.md "
                f"Requirements Coverage row {req_id}"
            )
        req_rows.append(
            {
                "req_id": req_id,
                "phase": phase,
                "plan": plan,
                "verification_status": v_status,
                "evidence_pointer": evidence,
                "operator_actions": operator_actions,
            }
        )
        operator_action_count += len(operator_actions)
        if v_status == "passed":
            satisfied += 1
        elif v_status == "human_needed":
            human_needed += 1
        else:
            failed += 1

    all_reqs_have_automated_verification = (satisfied + human_needed) == len(reqs)
    operator_actions_documented = (
        operator_action_count >= MILESTONE_OPERATOR_ACTION_FLOOR[milestone]
    )
    any_req_failed = failed > 0

    if any_req_failed:
        recommended = "fail"
    elif not all_reqs_have_automated_verification:
        recommended = "gaps_found"
    elif human_needed > 0 and not operator_actions_documented:
        recommended = "tech_debt"
    else:
        recommended = "passed"

    return {
        "milestone": milestone,
        "audited_at": _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_reqs": len(reqs),
        "satisfied_reqs": satisfied,
        "human_needed_reqs": human_needed,
        "failed_reqs": failed,
        "operator_action_count": operator_action_count,
        "verdict_logic": {
            "all_reqs_have_automated_verification": all_reqs_have_automated_verification,
            "operator_actions_documented": operator_actions_documented,
            "any_req_failed": any_req_failed,
            "recommended_verdict": recommended,
        },
        "reqs": req_rows,
    }


def run_audit(milestone: str = "v11.0", out_path: Path | None = None) -> dict[str, Any]:
    """Top-level audit entry. Reads inputs, builds matrix, optionally writes."""
    if milestone not in MILESTONE_REQUIREMENTS_FILES:
        raise ValueError(
            f"Unknown milestone: {milestone!r}. "
            f"Expected one of: {sorted(MILESTONE_REQUIREMENTS_FILES)}"
        )
    req_file = MILESTONE_REQUIREMENTS_FILES[milestone]
    req_id_pattern = MILESTONE_REQ_ID_PATTERNS[milestone]
    phase_files = MILESTONE_PHASE_VERIFICATION_FILES[milestone]

    reqs = _parse_requirements(req_file, req_id_pattern)
    expected_counts = {"v11.0": 15, "v12.0": 8}
    expected = expected_counts.get(milestone)
    if expected is not None and len(reqs) != expected:
        print(
            f"[audit] WARNING: expected {expected} reqs in {milestone} "
            f"traceability table, found {len(reqs)}",
            file=sys.stderr,
        )
    verifications = {
        phase: _parse_verification(phase, path, req_id_pattern)
        for phase, path in phase_files.items()
    }
    matrix = _build_coverage_matrix(milestone, reqs, verifications)
    payload = json.dumps(matrix, indent=2, ensure_ascii=False)
    print(payload)
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload + "\n", encoding="utf-8")
        print(f"[audit] wrote matrix to {out_path}", file=sys.stderr)
    return matrix


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns exit code (0 on success)."""
    parser = argparse.ArgumentParser(
        prog="run_milestone_audit.py",
        description=(
            "Milestone audit coverage matrix producer. Parses a requirements "
            "traceability table + prior-phase VERIFICATION.md frontmatter "
            "blocks; emits JSON matrix with recommended verdict to stdout. "
            "Supports v11.0 (default, backward compat) and v12.0."
        ),
    )
    parser.add_argument(
        "--milestone",
        choices=["v11.0", "v12.0"],
        default="v11.0",
        help="Milestone version to audit. v11.0 (default) reads the frozen "
        "v11.0-REQUIREMENTS.md snapshot + Phase 52-55 VERIFICATIONs. v12.0 "
        "reads the live REQUIREMENTS.md + Phase 57-60 VERIFICATIONs.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional path to also write the JSON matrix (e.g. "
        ".planning/research/v11-poc-eval/audit-matrix.json).",
    )
    args = parser.parse_args(argv)
    run_audit(milestone=args.milestone, out_path=args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
