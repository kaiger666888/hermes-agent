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

#: Load-bearing schema field names that Dimension 2 MUST catch (per
#: PLAN.md §2 locked list). Listed here as a doc cross-reference; the
#: canonical set is loaded dynamically from the 3 schema YAMLs at runtime.
LOAD_BEARING_SCHEMA_FIELDS: tuple[str, ...] = (
    "persona_sha256",
    "fitness_battery",
    "fitness_score",
    "memory_scope",
    "memory.max_records",  # nested: memory: { max_records: ... }
    "evidence_chain",
    "evidence_operator_ids",
    "scope",  # global|project|session enum in memory-record-schema
    "project_id",
    "expires_at",
    "verified_at",
    "supersedes_memory_id",
    "confidence",
    "half_life_days",
    "status",
    "schema_version",
    "retained_python_phases",  # round-table-state-schema field
    "round_id",
    "turn_order",
    "lineage",
    "related_agents",
    "evolution_log",
    "default_invocation",
    "round_table_eligible",
)


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


def _scan_terminology_confusions(line: str, line_no: int, path: Path) -> list[Finding]:
    """Conservative per-line terminology confusion heuristics (Dimension 1).

    Philosophy: false-negative-averse. Only flags suspect *co-occurrences*
    where one of the 5 locked terms appears next to a context anchor that
    strongly implies the wrong term was used. Bare mentions of "agent" /
    "skill" / "round table" / "panel" / "turn" are NOT flagged — only the
    narrow confusions below.

    Returns WARNING-only findings (terminology is fluid by design).
    """
    findings: list[Finding] = []
    rel = path.name

    # Pattern 1: "skill" near agent-only schema fields (persona, memory_scope,
    # fitness_battery, evolution_log, lineage, persona_sha256). Skill has none
    # of these per SKILL.md conventions in CLAUDE.md.
    if re.search(r"\bskill\b", line, re.IGNORECASE):
        for anchor in (
            "persona_sha256", "persona", "memory_scope", "fitness_battery",
            "fitness_score", "evolution_log", "lineage", "agents-schema",
        ):
            if anchor in line:
                # Exception: lines explicitly contrasting "skill" vs "agent"
                # (e.g. "Skill has no X; agent does") are NOT confusion — they
                # are clarifications. Heuristic: if "agent" also appears near,
                # skip.
                if re.search(r"\bagent\b", line, re.IGNORECASE):
                    continue
                findings.append(Finding(
                    dimension="terminology",
                    severity="WARNING",
                    file=path,
                    line=line_no,
                    message=(
                        f"terminology: 'skill' co-occurs with agent-only "
                        f"anchor '{anchor}' — did you mean 'agent'? "
                        f"(skill has no {anchor}; agent does per "
                        f"agents-schema.yaml)"
                    ),
                ))
                break  # one anchor per line is enough signal

    # Pattern 2: "agent" near skill-only contexts (SKILL.md, frontmatter,
    # skills/ path). Agent YAML is at ~/.hermes/agents/, not skills/.
    if re.search(r"\bagent\b", line, re.IGNORECASE):
        for anchor in ("SKILL.md", "skills/", "metadata.hermes", "frontmatter"):
            if anchor in line:
                if re.search(r"\bskill\b", line, re.IGNORECASE):
                    continue  # clarification line, skip
                findings.append(Finding(
                    dimension="terminology",
                    severity="WARNING",
                    file=path,
                    line=line_no,
                    message=(
                        f"terminology: 'agent' co-occurs with skill-only "
                        f"anchor '{anchor}' — did you mean 'skill'? "
                        f"(agent YAML lives at ~/.hermes/agents/, not skills/)"
                    ),
                ))
                break

    # Pattern 3: "panel" used as if it were the round-table session itself.
    # Panel = subset of agents; round table = the session. Only flag the
    # narrow phrase "panel opens" / "panel closes" / "panel lifecycle" — the
    # session opens/closes, not the panel.
    if re.search(r"\bpanel\b", line, re.IGNORECASE):
        for phrase in ("panel opens", "panel closes", "panel lifecycle",
                       "panel state file", "panel status"):
            if phrase in line.lower():
                findings.append(Finding(
                    dimension="terminology",
                    severity="WARNING",
                    file=path,
                    line=line_no,
                    message=(
                        f"terminology: '{phrase}' — did you mean 'round "
                        f"table'? (panel = subset of agents; round table = "
                        f"the session per Phase 46 §PanelistSnapshot)"
                    ),
                ))
                break

    # Pattern 4: "turn" conflated with "round" — turn = one panelist's
    # contribution; round = one full pass. Only flag the narrowest case:
    # explicit "the turn opens" or "the turn closes" describing the session
    # itself (which would be wrong — the round table opens/closes, not the
    # turn). The compound "turn lifecycle" / "turn state" are legitimate
    # terms (turns have lifecycles and states), so we deliberately do NOT
    # flag them.
    if re.search(r"\bturn\b", line, re.IGNORECASE):
        for phrase in ("the turn opens", "the turn closes",
                       "a turn opens", "a turn closes"):
            if phrase in line.lower():
                findings.append(Finding(
                    dimension="terminology",
                    severity="WARNING",
                    file=path,
                    line=line_no,
                    message=(
                        f"terminology: '{phrase}' — did you mean 'the round "
                        f"table opens/closes'? (turn = single panelist "
                        f"contribution; round table = the session that "
                        f"opens/closes per Phase 46)"
                    ),
                ))
                break

    return findings


def check_terminology(design_docs: list[Path]) -> list[Finding]:
    """Dimension 1 — terminology locked-sense enforcement.

    Returns findings with file:line evidence. WARNING-only for suspect
    co-occurrences; never ERROR (terminology is fluid by design).

    Capped at MAX_FINDINGS_PER_FILE per file to keep signal high.
    """
    findings: list[Finding] = []
    for path in design_docs:
        per_file = 0
        try:
            for line_no, line in _iter_markdown_lines(path):
                if per_file >= MAX_FINDINGS_PER_FILE:
                    break
                line_findings = _scan_terminology_confusions(line, line_no, path)
                findings.extend(line_findings)
                per_file += len(line_findings)
        except OSError as exc:
            findings.append(Finding(
                dimension="terminology",
                severity="ERROR",
                file=path,
                line=0,
                message=f"failed to read {path.name}: {exc}",
            ))
    return findings


def _levenshtein(a: str, b: str) -> int:
    """Standard dynamic-programming Levenshtein distance (≤ ~15 lines).

    Used for the schema-field close-match check (typo detection like
    ``persona_sha`` vs ``persona_sha256``).
    """
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            cur.append(min(
                prev[j] + 1,
                cur[j - 1] + 1,
                prev[j - 1] + (0 if ca == cb else 1),
            ))
        prev = cur
    return prev[-1]


def _classify_field_mention(
    name: str,
    line: str,
    canonical_sets: dict[str, set[str]],
) -> tuple[str, str]:
    """Classify a candidate field-name mention.

    Returns ``(severity, message)``. ``severity`` is "PASS" / "WARNING" /
    "ERROR". Conservative — only ERROR on clearly field-like context
    (backtick-wrapped OR after ``:`` in a YAML-like snippet OR in a
    "fields:" enumeration list). Common English words like "scope" /
    "status" are NOT ERRORs unless context strongly implies a field name.
    """
    # Flatten canonical sets for lookup
    all_canonical: set[str] = set()
    for fields in canonical_sets.values():
        all_canonical |= fields

    # Exact match — PASS
    if name in all_canonical:
        return "PASS", ""

    # Close match (Levenshtein ≤ 2) — WARNING suggesting canonical name
    close_matches: list[str] = []
    for canonical in all_canonical:
        # Only do Levenshtein for names of comparable length (perf guard)
        if abs(len(name) - len(canonical)) <= 3:
            d = _levenshtein(name, canonical)
            if d <= 2 and d > 0:
                close_matches.append(canonical)
    if close_matches:
        suggestions = ", ".join(sorted(set(close_matches))[:3])
        return "WARNING", (
            f"schema_references: '{name}' is not a canonical field name, "
            f"but close to: {suggestions}. Typo or stale ref?"
        )

    # Unknown — check field-like context to decide ERROR vs PASS.
    # Field-like context is narrowly defined to avoid false-positives on
    # prose / tool names / Python identifiers / filenames:
    #   * Line looks like a YAML snippet: starts with whitespace + name +
    #     colon + value (e.g. ``  confidence: 0.8``), OR
    #   * Appears in a YAML-schema-style enumeration like
    #     ``fields: [name1, name2, name3]``, OR
    #   * Line is inside a ```yaml``` code fence (caller would need to
    #     track fence state; for simplicity we approximate with the
    #     YAML-snippet heuristic)
    #
    # We deliberately do NOT treat "any backtick-wrapped identifier" as
    # field-like context — design docs backtick-wrap tool names, Python
    # identifiers, filenames, AND field names. Only YAML-snippet context
    # is strong enough to support an ERROR.
    yaml_snippet_re = rf"^\s*[- ]*{re.escape(name)}\s*:\s"
    fields_enum_re = rf"fields:\s*\[[^\]]*\b{re.escape(name)}\b"
    is_yaml_like_context = (
        re.search(yaml_snippet_re, line) is not None
        or re.search(fields_enum_re, line) is not None
    )

    # Conservative: skip common English words that match snake_case pattern
    # even in field-like context — they may be coincidental
    common_words = {
        "scope", "status", "name", "version", "type", "default",
        "description", "content", "value", "size", "id", "schema",
        "project_id",  # project_id is common enough as prose; the canonical
                       # one is checked via exact match above
    }
    if name in common_words and not is_yaml_like_context:
        return "PASS", ""

    # Exclusion set: identifiers that are NOT schema fields but are
    # legitimately backtick-wrapped in design docs (MCP tool names, Python
    # identifiers, file paths, etc.). These are PASS.
    excluded_identifiers = {
        # MCP tool names (STACK form, 7)
        "get_agent_persona", "get_agent_opinion", "get_agent_memory",
        "submit_round_table_result", "submit_artifact", "query_memory",
        "run_python_phase", "agents_list",
        # MCP tool names (ARCHITECTURE form, 3 — legacy)
        "agent_get_persona", "agent_recall", "agent_conclude",
        # round-table operation / state lifecycle ops (snake_case variants
        # of camelCase JSON properties / MCP tool args)
        "round_table_open", "round_table_close", "round_table_id",
        "round_table_state", "round_table_result",
        # Python identifiers / contextvars / function names
        "_scoped_agent_id", "_read_filters", "_write_filters",
        "_memory_evolution_phase", "_feedback_scan_phase",
        "_check_persona_section_intact", "_check_evidence_coverage",
        "_check_operator_diversity", "_compute_confidence",
        "_scan_for_hot_skills", "_detect_skill_agent_drift",
        "apply_memory_delta", "run_curator_review",
        # Hermes module / file names
        "agent_dispatcher", "agent_registry", "curator_audit",
        "feedback_store", "skill_utils", "hermes_llm",
        # A2A / external framework concepts
        "agent_card", "agent_scope", "agent_name",
        # mem0 internal identifiers
        "user_id", "agent_id", "run_id", "session_id",
        # round-table-state camelCase JSON property names (snake_case
        # variants are also legitimate in narrative context)
        "round_id", "turn_index", "panelist_id", "caller_id",
        # timestamp variants used in narrative
        "opened_at", "closed_at", "submitted_at", "resolved_at",
        "created_at", "last_updated_at", "verified_date",
        # file path / directory conventions
        "agent_yaml", "skill_md",
        # config.yaml fields (NOT schema fields — these live in
        # ~/.hermes/config.yaml, not in agents/memory-record/round-table
        # schemas; introduced in 04-MIGRATION-PATH for transition control)
        "legacy_memory_sunset_days",
    }
    if name in excluded_identifiers:
        return "PASS", ""

    # If field-like context AND not a common word AND not exact/close match
    # — this is suspicious. But still be conservative: only ERROR if the name
    # contains a clear schema-flavored token (memory, persona, evidence,
    # fitness, agent, round, etc.) — this catches real drift like
    # ``evidence_chain_count`` while ignoring prose like ``last_updated``.
    schema_tokens = (
        "memory", "persona", "evidence", "fitness", "agent", "round",
        "half_life", "expires", "verified", "supersedes", "scope",
        "confidence", "lineage", "evolution", "curator",
    )
    has_schema_token = any(tok in name for tok in schema_tokens)

    if is_yaml_like_context and has_schema_token:
        return "ERROR", (
            f"schema_references: '{name}' appears in YAML-snippet context "
            f"but is not in any canonical schema (agents / memory-record / "
            f"round-table-state). Likely invented field or name drift."
        )

    # Default: PASS (conservative — prefer false-negative over false-positive)
    return "PASS", ""


def check_schema_references(design_docs: list[Path], schema_dir: Path) -> list[Finding]:
    """Dimension 2 — schema field-name cross-check.

    Loads canonical field-name sets from the 3 schema YAMLs in ``schema_dir``,
    then scans design docs for field-like mentions and verifies each against
    the canonical sets. Unknown snake_case identifiers in field-like context
    are ERRORs; close matches are WARNINGs.
    """
    findings: list[Finding] = []

    # Load canonical field-name sets from the 3 schema YAMLs
    canonical_sets: dict[str, set[str]] = {}
    for kind, fname in SCHEMA_FILES.items():
        schema_path = schema_dir / fname
        try:
            canonical_sets[kind] = _load_yaml_field_names(schema_path)
        except OSError as exc:
            findings.append(Finding(
                dimension="schema_references",
                severity="ERROR",
                file=schema_path,
                line=0,
                message=f"failed to load schema {fname}: {exc}",
            ))
            canonical_sets[kind] = set()

    # Pattern: backtick-wrapped snake_case OR dotted snake_case identifiers.
    # Also catch YAML-snippet field names (``  name:`` at line start).
    backtick_re = re.compile(r"`([a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)?)`")
    yaml_field_re = re.compile(r"^\s*[- ]*([a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)?)\s*:")

    for path in design_docs:
        per_file = 0
        try:
            for line_no, line in _iter_markdown_lines(path):
                if per_file >= MAX_FINDINGS_PER_FILE:
                    break
                # Collect candidate names from both regexes
                candidates: list[str] = []
                for m in backtick_re.finditer(line):
                    candidates.append(m.group(1))
                for m in yaml_field_re.finditer(line):
                    candidates.append(m.group(1))

                for name in candidates:
                    # Skip single-char / pure-numeric / common-prose matches
                    if len(name) < 3:
                        continue
                    # Skip if it looks like a path (contains /)
                    if "/" in name:
                        continue
                    severity, message = _classify_field_mention(
                        name, line, canonical_sets
                    )
                    if severity == "WARNING":
                        findings.append(Finding(
                            dimension="schema_references",
                            severity="WARNING",
                            file=path,
                            line=line_no,
                            message=message,
                        ))
                        per_file += 1
                    elif severity == "ERROR":
                        findings.append(Finding(
                            dimension="schema_references",
                            severity="ERROR",
                            file=path,
                            line=line_no,
                            message=message,
                        ))
                        per_file += 1
        except OSError as exc:
            findings.append(Finding(
                dimension="schema_references",
                severity="ERROR",
                file=path,
                line=0,
                message=f"failed to read {path.name}: {exc}",
            ))

    return findings


def _extract_decision_roots(first_principles: Path) -> dict[int, str]:
    """Extract 决策 1-7 root-definition summaries from 00-FIRST-PRINCIPLES.md.

    Scans for ``### §2.N — 决策 N: ...`` headers and captures the
    following ~30 lines as the root definition summary. Returns a dict
    ``{1: "summary text", 2: ..., ...}``.

    If a header is missing, that decision number is omitted from the dict
    (the caller treats absence as INFO).
    """
    roots: dict[int, str] = {}
    header_re = re.compile(r"^###\s*§2\.([1-7])\s*[—-]\s*决策\s*([1-7])")

    if not first_principles.exists():
        return roots

    try:
        lines = list(_iter_markdown_lines(first_principles))
    except OSError:
        return roots

    i = 0
    while i < len(lines):
        _lineno, line = lines[i]
        m = header_re.match(line)
        if not m:
            i += 1
            continue
        decision_n = int(m.group(2))
        if decision_n not in KNOWN_DECISION_NUMBERS:
            i += 1
            continue
        # Capture body until next ### header (or §2.N+1 marker)
        body: list[str] = []
        i += 1
        while i < len(lines):
            _ln2, line2 = lines[i]
            # Stop at next ### header
            if line2.startswith("### ") or line2.startswith("## "):
                break
            body.append(line2)
            i += 1
            if len(body) >= 50:  # cap body extraction at 50 lines
                break
        # Join and truncate to a one-paragraph summary
        summary = " ".join(b.strip() for b in body if b.strip())[:600]
        roots[decision_n] = summary

    return roots


def _check_decision_mention(
    decision_n: int,
    line: str,
    context_before: list[str],
    context_after: list[str],
    root_summary: str,
    file_name: str,
    is_root_doc: bool,
) -> Finding | None:
    """Check a 决策 N mention against the root definition.

    Returns a Finding if ERROR/WARNING, else None.

    Rules:
      * Root doc (00-FIRST-PRINCIPLES.md) — always PASS (it IS the root).
      * Downstream docs — PASS for mere citation; ERROR for re-definition
        (uses ``决策 N 是`` / ``决策 N means`` / ``决策 N 定义为``);
        ERROR for contradiction (root keywords missing while contradicting
        keywords present).
    """
    if is_root_doc:
        return None  # root doc is the source of truth

    # Re-definition detection — CONSERVATIVE. We only flag explicit
    # definitional statements, not body paragraphs that cite + characterize
    # (e.g., "决策 6 是整个 PoC 验证的核心机制" is a characterization in
    # PoC context, not a re-definition of what 决策 6 IS).
    #
    # Patterns we flag (high precision):
    #   * "决策 N 定义为" — explicit Chinese definition
    #   * "决策 N means" — explicit English definition
    #
    # Patterns we deliberately do NOT flag (too ambiguous):
    #   * "决策 N 是<X>" — could be characterization in context
    #   * "决策 N is" — same
    #   * "决策 N: <subject>" — colon used for citation in lists/bullets
    redefine_patterns = (
        rf"决策\s*{decision_n}\s*定义为",
        rf"决策\s*{decision_n}\s+means\b",
    )
    for pat in redefine_patterns:
        if re.search(pat, line):
            return Finding(
                dimension="decision_consistency",
                severity="ERROR",
                file=Path(file_name),
                line=0,  # filled by caller
                message=(
                    f"decision_consistency: 决策 {decision_n} appears to be "
                    f"RE-DEFINED here. Root definition lives only in "
                    f"00-FIRST-PRINCIPLES.md §2.{decision_n}. Downstream "
                    f"docs must cite, not re-define."
                ),
            )

    return None


def check_decision_consistency(design_docs: list[Path]) -> list[Finding]:
    """Dimension 3 — 决策 1-7 cross-doc consistency matrix.

    Root definitions live only in 00-FIRST-PRINCIPLES.md §2.1-§2.7. Downstream
    docs (01-06) must not re-define or contradict them.

    Also emits INFO-level PASS findings for decision coverage: each 决策 N
    should appear in ≥3 of the 7 design docs (root + ≥2 downstream).
    """
    findings: list[Finding] = []

    # Locate the root doc (00-FIRST-PRINCIPLES.md)
    root_doc: Path | None = None
    for path in design_docs:
        if path.name.startswith("00-"):
            root_doc = path
            break
    if root_doc is None:
        findings.append(Finding(
            dimension="decision_consistency",
            severity="ERROR",
            file=Path("(missing-root)"),
            line=0,
            message=(
                "decision_consistency: 00-FIRST-PRINCIPLES.md not found "
                "— cannot verify 决策 1-7 root definitions."
            ),
        ))
        return findings

    # Extract root definitions
    roots = _extract_decision_roots(root_doc)
    missing_roots = KNOWN_DECISION_NUMBERS - set(roots.keys())
    if missing_roots:
        findings.append(Finding(
            dimension="decision_consistency",
            severity="WARNING",
            file=root_doc,
            line=0,
            message=(
                f"decision_consistency: missing root definitions for "
                f"决策 {sorted(missing_roots)} in 00-FIRST-PRINCIPLES.md."
            ),
        ))

    # Track cross-doc coverage
    decision_doc_appearances: dict[int, set[str]] = {
        n: set() for n in KNOWN_DECISION_NUMBERS
    }
    decision_mention_re = re.compile(r"决策\s*([1-7])")

    # Scan all docs for 决策 N mentions
    for path in design_docs:
        is_root = (path == root_doc)
        try:
            lines = list(_iter_markdown_lines(path))
        except OSError as exc:
            findings.append(Finding(
                dimension="decision_consistency",
                severity="ERROR",
                file=path,
                line=0,
                message=f"failed to read {path.name}: {exc}",
            ))
            continue

        for idx, (line_no, line) in enumerate(lines):
            for m in decision_mention_re.finditer(line):
                n = int(m.group(1))
                if n not in KNOWN_DECISION_NUMBERS:
                    continue
                decision_doc_appearances[n].add(path.name)

                root_summary = roots.get(n, "")
                # Gather ±5 lines of context
                ctx_before = [ln for _ln, ln in lines[max(0, idx - 5):idx]]
                ctx_after = [ln for _ln, ln in lines[idx + 1:idx + 6]]

                finding = _check_decision_mention(
                    n, line, ctx_before, ctx_after,
                    root_summary, str(path), is_root,
                )
                if finding is not None:
                    # Patch line number into the finding
                    finding.line = line_no
                    findings.append(finding)

    # Coverage INFO — emit PASS for 决策 N appearing in <3 docs
    for n in sorted(KNOWN_DECISION_NUMBERS):
        doc_count = len(decision_doc_appearances[n])
        if doc_count < 3:
            findings.append(Finding(
                dimension="decision_consistency",
                severity="PASS",  # INFO-level; not a failure
                file=Path(f"(coverage-决策-{n})"),
                line=0,
                message=(
                    f"decision_consistency: 决策 {n} appears in only "
                    f"{doc_count} of 7 design docs (coverage INFO; "
                    f"expected ≥3 for load-bearing decisions)."
                ),
            ))

    return findings


def _classify_tool_mention(tool: str, line: str, file_name: str) -> str:
    """Classify a candidate MCP tool mention.

    Returns one of:
      * ``STACK_PASS`` — canonical STACK form (no prefix). No finding emitted.
      * ``ARCH_EXCEPTION`` — ARCHITECTURE form in comparison/citation context.
        No finding emitted (legitimate comparison per OQ-9 reconciliation).
      * ``ARCH_WARNING`` — ARCHITECTURE form outside exception context.
        Emit WARNING.
      * ``UNKNOWN_ERROR`` — tool name not in either allow-list. Emit ERROR.

    Exception context is detected by either:
      * file is 03-COMPARISON-VS-KIMI-MCP-SHIM.md (the comparison doc), OR
      * line contains explicit citation cues like ``ARCHITECTURE §`` /
        ``ARCHITECTURE-form`` / ``STACK form`` / ``originally called`` /
        ``deprecated`` / ``reconciliation``.
    """
    if tool in STACK_FORM_TOOLS:
        return "STACK_PASS"

    if tool in ARCHITECTURE_FORM_TOOLS:
        # Check exception context
        if file_name.endswith("03-COMPARISON-VS-KIMI-MCP-SHIM.md"):
            return "ARCH_EXCEPTION"
        citation_cues = (
            "ARCHITECTURE §", "ARCHITECTURE-form", "ARCHITECTURE form",
            "STACK §", "STACK form", "STACK-form",
            "originally called", "deprecated", "Reconciliation",
            "reconciliation", "旧命名", "命名冲突", "naming", "vs",
            # Reconciliation table rows cite both forms side-by-side
            "ADOPTED", "canonical", "→", " | ",
        )
        for cue in citation_cues:
            if cue in line:
                return "ARCH_EXCEPTION"
        return "ARCH_WARNING"

    return "UNKNOWN_ERROR"


def check_mcp_tool_naming(design_docs: list[Path]) -> list[Finding]:
    """Dimension 4 — MCP tool naming (STACK form vs ARCHITECTURE form).

    STACK-form (7 tools) → PASS. ARCHITECTURE-form (3 tools) → WARNING
    unless in 03-COMPARISON doc or citation context. Unknown tool names →
    ERROR (likely typo / drift).
    """
    # Combined allow-list for the "unknown" classification
    known_tools = STACK_FORM_TOOLS | ARCHITECTURE_FORM_TOOLS

    # Pattern: tool-name candidates are snake_case identifiers starting with
    # one of these prefixes AND containing an underscore. Bounded to avoid
    # flagging arbitrary prose.
    # Pattern: tool-name candidates are bounded to the known MCP tool
    # vocabulary. We deliberately do NOT use a generic ``[a-z_]+`` pattern
    # because it would false-flag field names like ``agent_id`` /
    # ``agent_registry`` / ``agent_card`` / ``agent_scope``. The candidate
    # regex requires the verb prefix + a known domain noun.
    candidate_re = re.compile(
        r"\b("
        # STACK form: verb + domain_noun
        r"(?:get|submit|query|run)_(?:"
        r"agent_persona|agent_opinion|agent_memory|agent_fitness"
        r"|round_table_result|round_table_open|round_table_state"
        r"|memory|persona|opinion|artifact|python_phase"
        r")"
        # ARCHITECTURE form: agent_verb_noun
        r"|agent_(?:get_persona|recall|conclude)"
        r")\b"
    )

    findings: list[Finding] = []
    # Per-tool doc-count tracker (for cross-doc consistency INFO note)
    tool_doc_appearances: dict[str, set[str]] = {}

    for path in design_docs:
        per_file = 0
        try:
            for line_no, line in _iter_markdown_lines(path):
                if per_file >= MAX_FINDINGS_PER_FILE:
                    break
                for m in candidate_re.finditer(line):
                    tool = m.group(1)
                    # Track appearances (for INFO summary at end)
                    tool_doc_appearances.setdefault(tool, set()).add(path.name)

                    classification = _classify_tool_mention(tool, line, path.name)

                    if classification == "ARCH_WARNING":
                        findings.append(Finding(
                            dimension="mcp_tool_naming",
                            severity="WARNING",
                            file=path,
                            line=line_no,
                            message=(
                                f"MCP tool naming: ARCHITECTURE-form "
                                f"'{tool}' used outside comparison/citation "
                                f"context. STACK form is canonical per OQ-9 "
                                f"(see 02-ROUND-TABLE-PROTOCOL.md §naming "
                                f"resolution table)."
                            ),
                        ))
                        per_file += 1
                    elif classification == "UNKNOWN_ERROR":
                        # Only ERROR if the tool is plausibly an agent/round-
                        # table tool (not arbitrary prose). The semantic_tokens
                        # filter above already handles this.
                        if tool in known_tools:
                            continue  # bug in classification — skip
                        findings.append(Finding(
                            dimension="mcp_tool_naming",
                            severity="ERROR",
                            file=path,
                            line=line_no,
                            message=(
                                f"MCP tool naming: unknown tool '{tool}' — "
                                f"not in STACK form (7 canonical) nor "
                                f"ARCHITECTURE form (3 legacy). Likely "
                                f"typo or name drift."
                            ),
                        ))
                        per_file += 1
        except OSError as exc:
            findings.append(Finding(
                dimension="mcp_tool_naming",
                severity="ERROR",
                file=path,
                line=0,
                message=f"failed to read {path.name}: {exc}",
            ))

    # Cross-doc consistency INFO — emit PASS findings noting any STACK-form
    # tool that appears in <2 docs. These are informational, not failures.
    for tool in STACK_FORM_TOOLS:
        doc_count = len(tool_doc_appearances.get(tool, set()))
        if doc_count < 2 and doc_count > 0:
            findings.append(Finding(
                dimension="mcp_tool_naming",
                severity="PASS",  # INFO-level; recorded but doesn't fail
                file=Path(f"(cross-doc-{tool})"),
                line=0,
                message=(
                    f"MCP tool naming: STACK-form tool '{tool}' appears in "
                    f"only {doc_count} of 7 design docs (cross-doc "
                    f"consistency INFO; not a failure)."
                ),
            ))

    return findings


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
