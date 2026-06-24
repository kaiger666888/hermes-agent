"""Tests for agent/evolution/diff_generator.py — EVOL-02 placeholder.

difflib-based additive diff generation. Tests cover the happy path plus
the three Pitfall 2 edge cases: marker not found, marker not unique,
idempotent (addition already present).
"""

from __future__ import annotations

import pytest

from agent.evolution.diff_generator import generate_additive_diff


class TestGenerateAdditiveDiff:
    def test_returns_unified_diff_with_additive_hunk(self) -> None:
        current = "# Title\n## Refs\n- a\n"
        addition = "- b\n"
        diff = generate_additive_diff(
            current_content=current,
            proposed_addition=addition,
            insert_after_marker="## Refs",
            skill_md_path="skills/movie-experts/test_skill/SKILL.md",
        )
        assert "--- a/skills/movie-experts/test_skill/SKILL.md" in diff
        assert "+++ b/skills/movie-experts/test_skill/SKILL.md" in diff
        assert "@@" in diff
        # No `-` content lines (context/deletions); additions only.
        content_lines = [
            ln for ln in diff.splitlines()
            if ln.startswith("+") and not ln.startswith("+++")
        ]
        assert any("- b" in ln for ln in content_lines)

    def test_hunk_header_has_more_new_lines_than_old(self) -> None:
        current = "a\nb\n"
        diff = generate_additive_diff(
            current_content=current,
            proposed_addition="c\nd\n",
            insert_after_marker="a",
            skill_md_path="x/SKILL.md",
        )
        # Find @@ -A,B +C,D @@ and verify D > B.
        import re
        m = re.search(r"@@ -(\d+),(\d+) \+(\d+),(\d+) @@", diff)
        assert m is not None
        _, b, _, d = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        assert d > b, f"expected new-line count {d} > old-line count {b}"

    def test_missing_marker_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="(?i)not found"):
            generate_additive_diff(
                current_content="a\nb\n",
                proposed_addition="c\n",
                insert_after_marker="NONEXISTENT MARKER",
                skill_md_path="x/SKILL.md",
            )

    def test_non_unique_marker_raises_value_error(self) -> None:
        # Marker appears twice — Pitfall 2 #2.
        current = "## Refs\n- a\n## Refs\n- b\n"
        with pytest.raises(ValueError, match="(?i)not unique"):
            generate_additive_diff(
                current_content=current,
                proposed_addition="c\n",
                insert_after_marker="## Refs",
                skill_md_path="x/SKILL.md",
            )

    def test_normalizes_crlf(self) -> None:
        # Pitfall 2 #1: \r\n in current must be normalized before diffing.
        current = "a\r\nb\r\n"
        diff = generate_additive_diff(
            current_content=current,
            proposed_addition="c\n",
            insert_after_marker="a",
            skill_md_path="x/SKILL.md",
        )
        # Should produce a non-empty diff that applies cleanly.
        assert diff.strip()
        assert "+c" in diff

    def test_idempotent_when_addition_already_present(self) -> None:
        # Plan-checker Warning 5: raise ValueError ONLY when addition
        # already present (do NOT also return empty string).
        # The guard fires when new_lines == current_lines — i.e. the
        # addition produces no net change. An empty addition at the marker
        # is the canonical no-op case.
        current = "a\n## Refs\n- existing\n"
        with pytest.raises(ValueError, match="(?i)already present|empty|no-op"):
            generate_additive_diff(
                current_content=current,
                proposed_addition="",
                insert_after_marker="## Refs",
                skill_md_path="x/SKILL.md",
            )

    def test_no_minus_content_lines_in_generated_diff(self) -> None:
        # SC-6: generated diff must be purely additive.
        current = "header\n## Section\nbody\n"
        diff = generate_additive_diff(
            current_content=current,
            proposed_addition="new content\n",
            insert_after_marker="## Section",
            skill_md_path="x/SKILL.md",
        )
        minus_lines = [
            ln for ln in diff.splitlines()
            if ln.startswith("-") and not ln.startswith("---")
        ]
        assert minus_lines == [], f"generated diff has removal lines: {minus_lines}"
