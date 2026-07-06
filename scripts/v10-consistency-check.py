#!/usr/bin/env python3
"""v10.0 cross-doc consistency lint (VALIDATE-02).

Checks 4 consistency dimensions across the 7 v10.0 design docs in
``.planning/research/v10-orchestrator-design/``:

  1. terminology — locked-sense enforcement for the 5 canonical terms
     ``agent`` / ``skill`` / ``round table`` / ``panel`` / ``turn``.
  2. schema_references — every backticked / YAML-style field mention in the
     design docs must match a canonical field name from the 3 schema YAMLs.
  3. decision_consistency — 决策 1-7 root definitions live only in
     ``00-FIRST-PRINCIPLES.md §2.1-§2.7``; downstream docs must not contradict
     or re-define them.
  4. mcp_tool_naming — the STACK form (``get_agent_persona`` /
     ``get_agent_opinion`` / ``get_agent_memory`` /
     ``submit_round_table_result`` / ``submit_artifact`` / ``query_memory`` /
     ``run_python_phase``) dominates. The ARCHITECTURE form
     (``agent_get_persona`` / ``agent_recall`` / ``agent_conclude``) is
     allowed only inside the 03-COMPARISON doc or in explicit citation
     context (per OQ-9 STACK form lock).

Design philosophy (CONS — conservative / false-negative-averse):
  * Design docs have already passed 7 prior verification rounds (Phase 44-50).
    A lint ERROR is suspicious by default — the heuristic is tuned to prefer
    false negatives (silently pass) over false positives (cry wolf).
  * Every WARNING / ERROR carries a ``file:line`` evidence pointer so the
    operator (Kai) and the v11.0 PoC implementer can spot-check the finding.
  * WARNINGs do not fail the exit code; only ERRORs fail (or WARNINGs under
    ``--strict``).

References:
  * REQUIREMENTS.md VALIDATE-02 — defines the 4 dimensions.
  * ROADMAP Phase 51 SC#1 / SC#2 — defines success criteria for this script.
  * SUMMARY.md OQ-9 — STACK-form MCP tool naming locked.
  * CLAUDE.md — Python conventions (snake_case, encoding="utf-8" on every
    open(), type hints on public functions, no bare except).

Usage::

    python3 scripts/v10-consistency-check.py
    python3 scripts/v10-consistency-check.py --root path/to/docs --format json --strict

Exit codes: ``0`` iff zero ERRORs (zero WARNINGs also required under
``--strict``); ``1`` otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

# ──────────────────────────────────────────────────────────────────────────
# Module constants (UPPER_SNAKE_CASE per CLAUDE.md)
# ──────────────────────────────────────────────────────────────────────────

EXIT_OK: int = 0
EXIT_ERROR: int = 1

#: Glob for the 7 v10.0 design docs (00-FIRST-PRINCIPLES through 06-CROSS-REPO-IMPACT).
DESIGN_DOC_GLOB: str = "0[0-6]-*.md"

#: Schema YAMLs — the canonical field-name truth for Dimension 2.
SCHEMA_FILES: dict[str, Path] = {
    "agents": Path("agents-schema.yaml"),
    "memory-record": Path("memory-record-schema.yaml"),
    "round-table-state": Path("round-table-state-schema.yaml"),
}

#: STACK §3.2 canonical MCP tool names (7) — Dimension 4 PASS list.
STACK_FORM_TOOLS: frozenset[str] = frozenset({
    "get_agent_persona",
    "get_agent_opinion",
    "get_agent_memory",
    "submit_round_table_result",
    "submit_artifact",
    "query_memory",
    "run_python_phase",
})

#: ARCHITECTURE §4.2 form (agent_ prefix, 3) — Dimension 4 WARNING list.
#: Legitimately appears in 03-COMPARISON-VS-KIMI-MCP-SHIM.md comparison context.
ARCHITECTURE_FORM_TOOLS: frozenset[str] = frozenset({
    "agent_get_persona",
    "agent_recall",
    "agent_conclude",
})

#: Root-defined decision numbers (决策 1-7 per Phase 44 §2.1-§2.7).
KNOWN_DECISION_NUMBERS: frozenset[int] = frozenset(range(1, 8))

#: Locked terminology senses — Dimension 1 truth.
TERMINOLOGY_LOCKED_SENSES: dict[str, str] = {
    "agent": (
        "registered YAML entity in ~/.hermes/agents/{name}.agent.yaml with "
        "persona + tools + memory_scope + lineage (Phase 44 决策 5 α form)"
    ),
    "skill": (
        "SKILL.md markdown file consumed by the Hermes skills loader — "
        "injected as a USER message (no per-agent memory, no persona field)"
    ),
    "round table": (
        "multi-agent deliberation session with a state file at "
        ".runtime/{slug}/round_tables/{id}.json (Phase 46 protocol)"
    ),
    "panel": (
        "the subset of agents participating in one round table "
        "(Phase 46 §PanelistSnapshot)"
    ),
    "turn": (
        "one panelist's atomic opinion submission within a round table "
        "(Phase 46 §Turn — submit one opinion per turn, serial)"
    ),
}

#: Conservative file-size guard (T-51-03 DoS mitigation).
MAX_FILE_BYTES: int = 5 * 1024 * 1024  # 5 MB

#: Conservative per-line length guard (T-51-03 DoS mitigation).
MAX_LINE_CHARS: int = 10_000

#: Cap findings per file per dimension to avoid runaway (signal, not volume).
MAX_FINDINGS_PER_FILE: int = 50


# ──────────────────────────────────────────────────────────────────────────
# Finding dataclass
# ──────────────────────────────────────────────────────────────────────────


@dataclass(slots=True)
class Finding:
    """One lint finding (PASS / WARNING / ERROR).

    ``severity`` uses the literal strings "PASS" / "WARNING" / "ERROR" so the
    text formatter can render them with fixed width.
    """

    dimension: str
    severity: str
    file: Path
    line: int
    message: str

    def is_error(self) -> bool:
        return self.severity == "ERROR"

    def is_warning(self) -> bool:
        return self.severity == "WARNING"

    def is_pass(self) -> bool:
        return self.severity == "PASS"


# ──────────────────────────────────────────────────────────────────────────
# Helpers (pure stdlib)
# ──────────────────────────────────────────────────────────────────────────


def _iter_markdown_lines(path: Path) -> Iterator[tuple[int, str]]:
    """Yield ``(1-indexed line_number, line_text)`` from a markdown file.

    Refuses over-long lines (T-51-03 DoS guard) by truncating to
    ``MAX_LINE_CHARS`` and appending a ``[truncated]`` marker — preserves
    evidence value without crashing on pathological input.
    """
    with path.open(encoding="utf-8") as handle:
        for idx, raw in enumerate(handle, start=1):
            line = raw.rstrip("\n")
            if len(line) > MAX_LINE_CHARS:
                line = line[:MAX_LINE_CHARS] + "[truncated]"
            yield idx, line


def _load_yaml_field_names(path: Path) -> set[str]:
    """Extract canonical top-level + dotted-nested field names from a YAML file.

    Pure-stdlib line-based parser (no PyYAML dependency per VALIDATE-02 scope).
    Recognises:

      * ``^  field:``         — 2-space top-level field
      * ``^    nested:``      — 4-space nested field
      * synthesises ``parent.child`` dotted names when a parent dict is open

    Comments and ``$schema`` / ``$id`` / ``title`` / ``description`` keys are
    ignored (they are JSON Schema metadata, not field names).
    """
    fields: set[str] = set()
    parent_stack: list[str] = []

    if not path.exists():
        return fields

    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            # Match indentation + key pattern. Top-level JSON-Schema keys like
            # $schema, $id, title, description, type, required, additionalProperties,
            # properties, items, minItems, pattern, format, minimum, maximum,
            # default, enum, description are structural — skip them.
            m = re.match(r"^( +)([a-zA-Z_][a-zA-Z0-9_]*):", line)
            if not m:
                # Pop stack when we de-indent (heuristic — empty/comment lines OK)
                continue
            indent = len(m.group(1))
            key = m.group(2)

            # Skip JSON-Schema structural keywords
            if key in {
                "$schema", "$id", "title", "description", "type", "required",
                "additionalProperties", "properties", "items", "minItems",
                "pattern", "format", "minimum", "maximum", "default", "enum",
                "$ref", "minLength", "minItems",
            }:
                continue

            # Maintain a parent stack by indentation level (2 = top, 4 = nested)
            # For 2-space: top-level field
            if indent == 2:
                parent_stack = [key]
                fields.add(key)
            elif indent >= 4:
                # Nested — synthesise dotted name if we have a parent
                if parent_stack:
                    dotted = f"{parent_stack[0]}.{key}"
                    fields.add(dotted)
                    fields.add(key)  # Also allow short form
                else:
                    fields.add(key)
            else:
                # indent 0 — root level (e.g. $defs:) — reset
                parent_stack = []

    return fields


# ──────────────────────────────────────────────────────────────────────────
# Dimension check signatures (skeletons — Tasks 2-3 fill them in)
# ──────────────────────────────────────────────────────────────────────────


def check_terminology(design_docs: list[Path]) -> list[Finding]:
    """Dimension 1 — terminology locked-sense enforcement.

    Returns findings with file:line evidence. WARNING-only for suspect
    co-occurrences; never ERROR (terminology is fluid by design).
    """
    return []


def check_schema_references(design_docs: list[Path], schema_dir: Path) -> list[Finding]:
    """Dimension 2 — schema field-name cross-check.

    Loads canonical field-name sets from the 3 schema YAMLs in ``schema_dir``,
    then scans design docs for field-like mentions and verifies each against
    the canonical sets. Unknown snake_case identifiers in field-like context
    are ERRORs; close matches are WARNINGs.
    """
    return []


def check_decision_consistency(design_docs: list[Path]) -> list[Finding]:
    """Dimension 3 — 决策 1-7 cross-doc consistency matrix.

    Root definitions live only in 00-FIRST-PRINCIPLES.md §2.1-§2.7. Downstream
    docs (01-06) must not re-define or contradict them.
    """
    return []


def check_mcp_tool_naming(design_docs: list[Path]) -> list[Finding]:
    """Dimension 4 — MCP tool naming (STACK form vs ARCHITECTURE form).

    STACK-form (7 tools) → PASS. ARCHITECTURE-form (3 tools) → WARNING
    unless in 03-COMPARISON doc or citation context. Unknown tool names →
    ERROR (likely typo / drift).
    """
    return []


# ──────────────────────────────────────────────────────────────────────────
# CLI + main()
# ──────────────────────────────────────────────────────────────────────────


def _format_text(findings: list[Finding]) -> str:
    """Format findings as one line each, plus a summary tail.

    ``DIMENSION | SEVERITY | file:line | message``
    """
    lines: list[str] = []
    for f in findings:
        rel = f.file.name  # keep output terse — filename only
        lines.append(
            f"{f.dimension:<22} | {f.severity:<8} | {rel}:{f.line} | {f.message}"
        )
    return "\n".join(lines)


def _count_by_severity(findings: list[Finding]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for f in findings:
        # Treat PASS as informational — only count WARNING / ERROR in summary
        if f.severity in {"WARNING", "ERROR", "PASS", "INFO"}:
            counts[f.severity] += 1
    return dict(counts)


def _format_json(
    findings: list[Finding],
    exit_code: int,
    dimension_counts: dict[str, dict[str, int]],
) -> str:
    """Format findings as a JSON object with summary + per-dimension counts."""
    payload = {
        "findings": [
            {
                "dimension": f.dimension,
                "severity": f.severity,
                "file": str(f.file),
                "line": f.line,
                "message": f.message,
            }
            for f in findings
            if not f.is_pass()  # PASS is implicit; omit to keep payload small
        ],
        "summary": {
            "total": len(findings),
            **{k: v for k, v in _count_by_severity(findings).items()},
            "exit_code": exit_code,
        },
        "dimensions": dimension_counts,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _resolve_design_docs(root: Path, explicit: list[Path] | None = None) -> list[Path]:
    """Resolve the list of design docs to scan.

    Explicit paths win; otherwise glob ``0[0-6]-*.md`` under ``root``.
    Missing files (glob returns <7) are not fatal — Task 4 finalizes the gate.
    """
    if explicit:
        return [p.resolve() for p in explicit if p.exists()]
    return sorted(root.glob(DESIGN_DOC_GLOB))


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Parses args, runs the 4 dimension checks, formats output, returns exit code.
    """
    parser = argparse.ArgumentParser(
        prog="v10-consistency-check",
        description=(
            "v10.0 cross-doc consistency lint (VALIDATE-02). Checks 4 "
            "dimensions across the 7 v10.0 design docs."
        ),
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(".planning/research/v10-orchestrator-design"),
        help="Root directory of the 7 design docs + 3 schema YAMLs.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (text default; json for machine consumption).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat WARNINGs as ERRORs for exit-code purposes.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Optional explicit design-doc paths (overrides --root glob).",
    )
    args = parser.parse_args(argv)

    # Input validation — root exists
    if not args.paths and not args.root.exists():
        sys.stderr.write(
            f"ERROR: --root {args.root} does not exist or is not a directory.\n"
        )
        return EXIT_ERROR

    design_docs = _resolve_design_docs(args.root, args.paths or None)
    if len(design_docs) < 7:
        sys.stderr.write(
            f"WARNING: expected 7 design docs (00-06), found {len(design_docs)}.\n"
        )

    # Run 4 checks
    findings: list[Finding] = []
    findings.extend(check_terminology(design_docs))
    findings.extend(check_schema_references(design_docs, args.root))
    findings.extend(check_decision_consistency(design_docs))
    findings.extend(check_mcp_tool_naming(design_docs))

    # Compute summary
    counts = _count_by_severity(findings)
    pass_count = counts.get("PASS", 0)
    warning_count = counts.get("WARNING", 0)
    error_count = counts.get("ERROR", 0)
    total = len(findings)

    # Per-dimension counts (for JSON output + summary)
    dimension_counts: dict[str, dict[str, int]] = {}
    for f in findings:
        dim = dimension_counts.setdefault(
            f.dimension, {"PASS": 0, "WARNING": 0, "ERROR": 0, "INFO": 0}
        )
        dim[f.severity] = dim.get(f.severity, 0) + 1

    # Exit code logic
    effective_errors = error_count + (warning_count if args.strict else 0)
    exit_code = EXIT_OK if effective_errors == 0 else EXIT_ERROR

    # Output
    if args.format == "json":
        print(_format_json(findings, exit_code, dimension_counts))
    else:
        out = _format_text(findings)
        if out:
            print(out)
        sys.stderr.write(
            f"TOTAL: {total} findings (PASS={pass_count} "
            f"WARNING={warning_count} ERROR={error_count})\n"
        )

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
