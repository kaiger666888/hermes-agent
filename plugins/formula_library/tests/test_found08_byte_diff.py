"""FOUND-08 byte-diff audit test for SKILL.md frontmatter (Plan 39-03).

Enforces the foundational FOUND-08 rule: YAML frontmatter blocks (between
the first pair of ``---`` markers) of patched SKILL.md files must be
byte-identical to the pre-v9.0 baseline.

Baseline anchor: commit ``a2a20d2be`` (last commit before v9.0 milestone).
This is the same anchor that Phase 43 VALIDATE-02 will use for its
milestone-wide byte-diff audit. This test is the per-phase guard that
catches drift early; Phase 43's audit is authoritative.

Relationship to VALIDATE-02:
  - Phase 43 VALIDATE-02 will diff every v9.0-touched file's frontmatter
    against ``a2a20d2be``.
  - This test runs in CI on every commit (per Phase 39 PLAN), catching
    drift at PR-review time rather than at milestone audit time.

Per CLAUDE.md conventions:
  - ``from __future__ import annotations``.
  - Double-quoted strings, ``encoding="utf-8"`` on every read.
  - ``class Test<Thing>:`` grouping, snake_case test names.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Targets — SKILL.md files patched in Phase 39 v9.0 (frontmatter frozen)
# ---------------------------------------------------------------------------

_SKILL_PATHS = (
    "skills/kais-movie-pipeline/SKILL.md",
    "skills/movie-experts/theory_critic/SKILL.md",
)

# Pre-v9.0 baseline anchor. Same commit Phase 43 VALIDATE-02 will use.
_BASELINE_REF = "a2a20d2be"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _repo_root() -> Path:
    """Walk up from this file until a ``.git`` entry is found."""
    p = Path(__file__).resolve()
    for parent in [p.parent, *p.parents]:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("could not locate repo root (.git/ not found)")


def _extract_frontmatter(text: str) -> str:
    """Return the YAML frontmatter block (inclusive of ``---`` markers).

    The frontmatter is the content between the first pair of ``---`` lines.
    Raises ``ValueError`` if fewer than 2 markers found.
    """
    lines = text.split("\n")
    if not lines or lines[0] != "---":
        raise ValueError(
            f"expected frontmatter to start with '---'; got: {lines[0]!r}"
        )
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i] == "---":
            end_idx = i
            break
    if end_idx is None:
        raise ValueError("frontmatter not terminated by second '---' marker")
    # Include both markers + the lines in between (join with \n, no trailing newline).
    return "\n".join(lines[: end_idx + 1])


def _git_show_text(rel_path: str, ref: str = _BASELINE_REF) -> str:
    """Return the textual content of ``rel_path`` at git ``ref``.

    Uses UTF-8 decoding per CLAUDE.md PLW1514 rule. On non-zero git exit,
    ``pytest.skip`` so the test degrades gracefully outside a git checkout
    (e.g. installed wheel without .git history).
    """
    repo = _repo_root()
    proc = subprocess.run(
        ["git", "show", f"{ref}:{rel_path}"],
        cwd=str(repo),
        capture_output=True,
        # text=True + encoding ensures cross-platform UTF-8 decoding.
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        pytest.skip(
            f"git show {ref}:{rel_path} failed (rc={proc.returncode}); "
            f"run from a git checkout with {ref} in history. stderr: {proc.stderr}"
        )
    return proc.stdout


# ---------------------------------------------------------------------------
# FOUND-08 enforcement tests
# ---------------------------------------------------------------------------


class TestFound08Preserved:
    """Frontmatter byte-identical to pre-v9.0 (commit a2a20d2be).

    See module docstring for relationship to Phase 43 VALIDATE-02.
    """

    @pytest.mark.parametrize("rel_path", _SKILL_PATHS)
    def test_frontmatter_byte_identical_to_baseline(self, rel_path: str) -> None:
        """Frontmatter (between ``---`` markers) must be byte-identical to a2a20d2be."""
        repo = _repo_root()
        current_text = (repo / rel_path).read_text(encoding="utf-8")
        baseline_text = _git_show_text(rel_path)

        current_fm = _extract_frontmatter(current_text)
        baseline_fm = _extract_frontmatter(baseline_text)

        current_hash = hashlib.sha256(current_fm.encode("utf-8")).hexdigest()
        baseline_hash = hashlib.sha256(baseline_fm.encode("utf-8")).hexdigest()

        if current_hash != baseline_hash:
            # Compute line-level diff for operator triage.
            import difflib
            diff_lines = list(difflib.unified_diff(
                baseline_fm.split("\n"),
                current_fm.split("\n"),
                fromfile=f"a2a20d2be:{rel_path} (frontmatter)",
                tofile=f"HEAD:{rel_path} (frontmatter)",
                lineterm="",
            ))
            diff_text = "\n".join(diff_lines) if diff_lines else "<no unified diff output>"
            raise AssertionError(
                f"FOUND-08 violation: frontmatter drifted for {rel_path}\n"
                f"  baseline sha256 ({_BASELINE_REF}): {baseline_hash}\n"
                f"  current  sha256 (HEAD):           {current_hash}\n"
                f"  diff:\n{diff_text}"
            )

    @pytest.mark.parametrize("rel_path", _SKILL_PATHS)
    def test_body_grew_not_shrank(self, rel_path: str) -> None:
        """Body length should be >= baseline body length (additive patches only).

        Catches accidental truncation. v9.0 patches only ADD content to bodies;
        any shrinkage is suspicious.
        """
        repo = _repo_root()
        current_text = (repo / rel_path).read_text(encoding="utf-8")
        baseline_text = _git_show_text(rel_path)

        # Body = everything after the frontmatter (after the second '---' line).
        def _body(text: str) -> str:
            lines = text.split("\n")
            end_idx = None
            for i in range(1, len(lines)):
                if lines[i] == "---":
                    end_idx = i
                    break
            if end_idx is None:
                return ""
            return "\n".join(lines[end_idx + 1:])

        current_body = _body(current_text)
        baseline_body = _body(baseline_text)

        assert len(current_body) >= len(baseline_body), (
            f"FOUND-08 sanity: body shrunk for {rel_path} "
            f"(baseline {len(baseline_body)} chars → current {len(current_body)} chars); "
            "v9.0 patches are additive — body should grow, not shrink"
        )
