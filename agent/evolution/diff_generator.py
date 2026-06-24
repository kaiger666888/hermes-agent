"""EVOL-02 placeholder — difflib-based additive unified-diff generator.

Converts an LLM-proposed "add this content after section X" into a real
git-compatible unified diff using stdlib :func:`difflib.unified_diff`.
This is the Phase 31 placeholder for EVOL-02; Phase 32 will extend with
LLM-generated rewrites. This module ONLY appends — it never modifies or
deletes existing bytes, satisfying SC-6 (v4/v5 refs byte-intact) by
construction.

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 unions.
  - No ``open()`` in this module (pure string transformation).
  - Specific exceptions (``ValueError``) raised on edge cases.
"""

from __future__ import annotations

import difflib
import logging

logger = logging.getLogger(__name__)


def _frontmatter_end_offset(lines: list[str]) -> int | None:
    """WR-04: return the 1-based line index of the closing ``---`` of the
    YAML frontmatter block, or None if the file has no frontmatter.

    ``lines`` is expected to be the output of ``splitlines(keepends=True)``.
    The frontmatter block starts at line 1 (``---``) and ends at the next
    ``---`` line. Returns the index of the closing ``---`` line such that
    any insertion at ``insert_idx <= fm_end`` would land inside the block.
    """
    if not lines or not lines[0].startswith("---"):
        return None
    for i, line in enumerate(lines[1:], start=2):
        if line.startswith("---"):
            return i
    # Opening --- with no closing — malformed; treat as no frontmatter
    # so we don't spuriously block insertions in a corrupt file.
    return None


def generate_additive_diff(
    *,
    current_content: str,
    proposed_addition: str,
    insert_after_marker: str,
    skill_md_path: str,
) -> str:
    """Generate a unified diff that ADDS content after a marker line.

    EVOL-02 placeholder. This function ONLY appends — never modifies or
    deletes existing bytes. Satisfies SC-6 by construction.

    Args:
        current_content: The current SKILL.md (or ref) full text.
        proposed_addition: The new content to append (multi-line string).
        insert_after_marker: A substring identifying where to insert
            (e.g., "## References"). The addition is inserted immediately
            AFTER the line containing this marker.
        skill_md_path: Repo-relative path for diff headers (a/... b/...).

    Returns:
        Unified diff string (git-compatible).

    Raises:
        ValueError: If ``insert_after_marker`` is not found in
            ``current_content`` (refuse blind append per Pitfall 2).
        ValueError: If ``insert_after_marker`` appears more than once
            (Pitfall 2 mitigation #2 — force the LLM to be specific).
        ValueError: If ``proposed_addition`` is already present at the
            insertion site (idempotent guard — per plan-checker Warning 5,
            raise ValueError; do NOT return empty string).
    """
    # Pitfall 2 #1: normalize CRLF before diffing so the generated patch
    # has consistent \n line endings (Windows-authored content would
    # otherwise produce a confusing multi-hunk diff).
    normalized = current_content.replace("\r\n", "\n")
    current_lines = normalized.splitlines(keepends=True)

    # Pitfall 2 #2: marker must be unique to avoid ambiguity.
    matches = [
        i for i, line in enumerate(current_lines)
        if insert_after_marker in line
    ]
    if not matches:
        raise ValueError(
            f"insert_after_marker {insert_after_marker!r} not found in "
            f"current content — refusing to generate blind-append diff"
        )
    if len(matches) > 1:
        raise ValueError(
            f"insert_after_marker {insert_after_marker!r} not unique "
            f"({len(matches)} matches) — provide a longer unique context"
        )
    insert_idx = matches[0] + 1

    # WR-04: reject insertions that would land INSIDE the YAML frontmatter
    # block. The LLM is instructed (insights.py:69-70) to not propose
    # frontmatter changes, but the marker substring search could still
    # match a frontmatter key (e.g., insert_after_marker="expert_id").
    # Inserting into frontmatter would trip the SC-5 byte-intact check
    # AFTER mutating the tree (CR-04 hardens the ordering, but we still
    # refuse here for defense-in-depth + clearer error messages).
    fm_end = _frontmatter_end_offset(current_lines)
    if fm_end is not None and insert_idx <= fm_end:
        raise ValueError(
            f"insert_after_marker {insert_after_marker!r} matches inside "
            f"the YAML frontmatter block (line {matches[0] + 1} is at or "
            f"before the closing '---' at line {fm_end}) — frontmatter is "
            f"immutable (SC-5)"
        )

    addition_lines = proposed_addition.replace("\r\n", "\n").splitlines(keepends=True)
    # Ensure the addition starts with a newline if the preceding line lacks one.
    if current_lines and not current_lines[insert_idx - 1].endswith("\n"):
        addition_lines = ["\n"] + addition_lines

    new_lines = (
        current_lines[:insert_idx]
        + addition_lines
        + current_lines[insert_idx:]
    )

    # Idempotent guard (plan-checker Warning 5): raise ValueError when
    # the addition is already present at the insertion site.
    if new_lines == current_lines:
        raise ValueError(
            "proposed_addition already present at insertion site — "
            "no diff generated (idempotent)"
        )

    diff = "".join(
        difflib.unified_diff(
            current_lines,
            new_lines,
            fromfile=f"a/{skill_md_path}",
            tofile=f"b/{skill_md_path}",
            lineterm="\n",
        )
    )

    # Pitfall 2 #3: assert the generated diff is non-empty AND contains
    # at least one `+` content line. An empty diff would mean the LLM
    # proposed adding content that somehow already exists (shouldn't
    # happen after the idempotent guard above, but defense-in-depth).
    if not diff.strip():
        raise ValueError(
            "generated diff is empty — proposed_addition produced no "
            "net change after normalization"
        )
    if not any(
        line.startswith("+") and not line.startswith("+++")
        for line in diff.splitlines()
    ):
        raise ValueError(
            "generated diff contains no addition lines — refusing to "
            "emit a no-op patch"
        )

    logger.debug(
        "generated additive diff for %s: %d bytes, inserted after %r",
        skill_md_path, len(diff), insert_after_marker,
    )
    return diff
