"""EVOL-05 — Atomic patch apply transaction with FOUND-08 + additive-only.

The ONLY mutation path for bundled SKILL.md / refs. Called exclusively
from ``hermes_cli/feedback.py:_cmd_approve`` (Plan 02). There is NO
programmatic auto-apply path — EVOL-04 non-bypassable human-in-loop is
enforced structurally by the absence of any other caller.

Atomic transaction (CONTEXT.md D-EVOL-04, 6 steps):
  1. ``git status --porcelain`` — refuse if working tree dirty
  2. Ensure git author identity (repo-local fallback, Pitfall 7)
  3. ``git apply --check`` — validate patch syntax (no mutation yet)
  4. ``git apply`` — mutate working tree
  5. FOUND-08 byte-intact check (SC-5, Pitfall 4 byte-level) +
     additive-only check for protected refs (SC-6)
  6. ``git add`` + ``git commit`` — persist
On ANY failure: revert working tree (``git checkout --`` for existing
files, ``git clean -f`` for patch-added files) and raise ApplyError.

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 unions.
  - ``encoding="utf-8"`` on every ``open()`` / ``read_text()`` (Ruff PLW1514).
  - argv-list subprocess only (T-30-02 — NEVER ``shell=True``).
  - Lazy %-logging; specific exceptions bound.
  - Error messages are operator-safe (no full unified_diff in error text —
    T-31-08 data protection).
"""

from __future__ import annotations

import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from agent.evolution.queue import PROTECTED_REFS

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

_HUNK_HEADER_RE = re.compile(r"^@@ -(\d+),(\d+) \+(\d+),(\d+) @@")
"""Matches unified-diff hunk headers; captures B (old count) and D (new count)."""

_PATCH_FILE_RE = re.compile(r"^\+\+\+ b/(.+?)\s*$")
"""Matches ``+++ b/<path>`` lines; capture group is repo-relative path."""

# T-31-04 mitigation: reject paths outside skills/movie-experts/.
_SKILLS_PREFIX = "skills/movie-experts/"

# T-31-08 operator-safe author fallback (Pitfall 7).
_FALLBACK_AUTHOR_EMAIL = "hermes-evolution@local"
_FALLBACK_AUTHOR_NAME = "Hermes Evolution Pipeline"


# --------------------------------------------------------------------------- #
# Exceptions + result dataclass
# --------------------------------------------------------------------------- #


class ApplyError(Exception):
    """Raised when the atomic apply transaction fails (auto-reverted).

    The working tree is ALWAYS clean when this surfaces — the transaction
    either commits fully or reverts fully. If the revert ITSELF fails
    (catastrophic), the error message explicitly says "manual recovery
    required" so the operator knows the tree may be dirty.
    """


@dataclass
class ApplyResult:
    """Successful apply result."""

    commit_sha: str
    files_modified: list[str]


# --------------------------------------------------------------------------- #
# Pure verification functions
# --------------------------------------------------------------------------- #


def verify_additive_only(diff_text: str) -> bool:
    """Return True iff the diff is purely additive (no removals).

    Verification rules (Pitfall 6 — false-positive-safe):
      1. Empty/whitespace-only diff → return False (suspicious no-op).
      2. Skip file headers (``--- `` / ``+++ ``).
      3. For each hunk header ``@@ -A,B +C,D @@``: return False if D < B
         (file shrinks).
      4. For each remaining content line:
         - `` `` (space) = context → ALLOW
         - ``+`` = addition → ALLOW (track ``saw_addition``)
         - ``-`` = removal → REJECT (return False)
      5. Return ``saw_addition`` at end.

    Args:
        diff_text: The unified diff text to verify.

    Returns:
        True iff the diff contains at least one addition and zero removals.
    """
    if not diff_text.strip():
        return False

    saw_addition = False
    for line in diff_text.splitlines():
        # Skip file headers (``--- a/...`` / ``+++ b/...``).
        if line.startswith("--- ") or line.startswith("+++ "):
            continue
        # Hunk header: validate D >= B.
        m = _HUNK_HEADER_RE.match(line)
        if m:
            _, b, _, d = (
                int(m.group(1)), int(m.group(2)),
                int(m.group(3)), int(m.group(4)),
            )
            if d < b:
                return False  # hunk shrinks the file
            continue
        # Content line.
        if line.startswith("-"):
            # Not a file header (skipped above) → it's a removal.
            return False
        if line.startswith("+"):
            saw_addition = True
        # Context lines (start with " ") are fine.
    return saw_addition


def _extract_frontmatter_block(content: str) -> str:
    """Return the raw frontmatter block (including --- delimiters).

    Returns empty string if no frontmatter present, or if the opening
    ``---`` has no matching closing ``---``.
    """
    if not content.startswith("---"):
        return ""
    # Find the closing ``---`` line after the opening one.
    # Search in content[3:] to skip the opening "---" prefix.
    end_match = re.search(r"\n---\s*\n", content[3:])
    if not end_match:
        return ""
    # Include opening ``---`` through closing ``---`` line (inclusive).
    # end_match.end() is the offset within content[3:] where the match
    # ends; add 3 to translate back to the full content offset.
    end_idx = 3 + end_match.end()
    return content[:end_idx]


def verify_found08_byte_intact(
    frontmatter_block_before: str,
    skill_md_path_after: Path,
) -> bool:
    """Return True iff the frontmatter bytes match exactly (SC-5).

    Pitfall 4 byte-level check — STRICTER than comparing parsed values.
    Catches re-serialization that preserves values but changes bytes
    (e.g., list reordering, quote-style changes, key reordering).

    Args:
        frontmatter_block_before: The frontmatter block text BEFORE patch
            apply (extracted via :func:`_extract_frontmatter_block`).
        skill_md_path_after: Path to the SKILL.md AFTER patch apply.

    Returns:
        True iff the frontmatter block bytes match exactly.
    """
    after_content = skill_md_path_after.read_text(encoding="utf-8")
    after_block = _extract_frontmatter_block(after_content)
    return frontmatter_block_before == after_block


# --------------------------------------------------------------------------- #
# Patch path extraction (T-30-01 / T-31-04 hardening — local copy)
# --------------------------------------------------------------------------- #


def _extract_patched_files(patch_path: Path) -> list[str]:
    """Parse ``+++ b/<path>`` lines from a unified diff.

    Local copy of ``skills/movie-experts/_eval/gate.extract_patched_files``
    logic — gate.py lives under a hyphenated path and is not importable;
    behavior is identical (T-30-01 path-traversal hardening + WR-07
    deletion-patch rejection).

    Returns a list of repo-relative POSIX paths touched by the patch.

    Raises:
        ValueError: on path traversal (``..``), path outside
            ``skills/movie-experts/``, or deletion patch (``+++ /dev/null``).
    """
    text = patch_path.read_text(encoding="utf-8")
    files: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        # WR-07: detect deletion patches explicitly.
        if line.startswith("+++ /dev/null"):
            raise ValueError(
                "patch contains file deletion (+++ /dev/null); the "
                "evolution pipeline only applies ADDITIVE patches per "
                "EVOL-02 scope discipline."
            )
        m = _PATCH_FILE_RE.match(line)
        if m is None:
            continue
        path = m.group(1).strip()
        if path in seen:
            continue
        # T-31-04: reject path traversal.
        if ".." in path.split("/"):
            raise ValueError(
                f"path traversal rejected: patch header contains '..' in "
                f"path {path!r} (T-31-04 mitigation)"
            )
        # T-31-04: reject paths outside skills/movie-experts/.
        if not path.startswith(_SKILLS_PREFIX):
            raise ValueError(
                f"patch touches path outside skills/movie-experts/: "
                f"{path!r} (evolution pipeline only patches bundled "
                f"movie-expert skills)"
            )
        seen.add(path)
        files.append(path)
    return files


# --------------------------------------------------------------------------- #
# Revert (mirror gate.py:201 revert_patch)
# --------------------------------------------------------------------------- #


def revert_files(files: list[str], repo_root: Path) -> None:
    """Revert patched files via ``git checkout --`` / ``git clean -f``.

    For files added by the patch (not present in HEAD), ``git checkout``
    would fail — detect via ``git cat-file -e HEAD:<path>`` and use
    scoped ``git clean -f <path>`` to remove them instead. NEVER a
    blanket clean (worktree safety per destructive_git_prohibition).

    Mirrors ``skills/movie-experts/_eval/gate.revert_patch`` (gate.py:201).
    """
    if not files:
        return
    existing: list[str] = []
    added: list[str] = []
    for f in files:
        result = subprocess.run(
            ["git", "cat-file", "-e", f"HEAD:{f}"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if result.returncode == 0:
            existing.append(f)
        else:
            added.append(f)
    if existing:
        subprocess.run(
            ["git", "checkout", "--"] + existing,
            cwd=str(repo_root), check=True,
            capture_output=True, text=True, encoding="utf-8",
        )
    if added:
        # Scoped clean — specific paths only, NEVER blanket.
        subprocess.run(
            ["git", "clean", "-f", "--"] + added,
            cwd=str(repo_root), check=True,
            capture_output=True, text=True, encoding="utf-8",
        )
    logger.info("reverted %d files in %s", len(files), repo_root)


# --------------------------------------------------------------------------- #
# Commit message builder
# --------------------------------------------------------------------------- #


def build_commit_message(
    *,
    insight_summary: str,
    feedback_ids: list[str],
    eval_verdict: str,
    eval_mean_delta: float,
) -> str:
    """Build the machine-parseable commit message per CONTEXT.md D-EVOL-04.

    Format:
        ``feat(evolution): <subject> | feedback: <ids> | eval: <verdict>:<delta>``

    The subject is truncated to 72 chars (git commit subject convention).
    The format is machine-parseable so P32's audit log + P33's
    observability dashboard can extract feedback IDs + eval score from
    git history.
    """
    subject = insight_summary[:72]
    feedback_str = ",".join(feedback_ids) if feedback_ids else "none"
    eval_str = f"{eval_verdict}:{eval_mean_delta:.2f}"
    return (
        f"feat(evolution): {subject} | "
        f"feedback: {feedback_str} | "
        f"eval: {eval_str}"
    )


# --------------------------------------------------------------------------- #
# Atomic apply transaction (EVOL-05)
# --------------------------------------------------------------------------- #


def apply_patch_transaction(
    *,
    patch_path: Path,
    repo_root: Path,
    commit_message: str,
    protected_refs: tuple[str, ...] = PROTECTED_REFS,
) -> ApplyResult:
    """Apply a patch atomically: validate → apply → verify → commit.

    6-step atomic transaction per CONTEXT.md D-EVOL-04. ANY failure in
    steps 4-6 triggers a full revert (``revert_files``). The working tree
    is NEVER left dirty on failure (unless the revert itself fails —
    catastrophic case surfaced explicitly).

    Args:
        patch_path: Path to the unified diff file.
        repo_root: Git repository root Path.
        commit_message: Commit message (use :func:`build_commit_message`).
        protected_refs: Filenames that must receive additive-only patches
            (SC-6). Defaults to :data:`PROTECTED_REFS`.

    Returns:
        :class:`ApplyResult` with commit_sha + files_modified.

    Raises:
        ApplyError: on dirty working tree, patch validation failure,
            FOUND-08 violation (SC-5), additive-only violation (SC-6),
            or any git subprocess failure. The working tree is reverted
            before raising (unless revert fails — then the error message
            says "manual recovery required").
    """
    # Step 1: dirty-tree guard (D-EVOL-04 invariant).
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(repo_root), capture_output=True, text=True, encoding="utf-8",
    )
    if status.stdout.strip():
        raise ApplyError(
            "working tree dirty — commit or stash before applying an "
            "evolution patch (D-EVOL-04 invariant)"
        )

    # Step 2: ensure git author identity (Pitfall 7 — repo-local only).
    _ensure_git_author(repo_root)

    # Step 3: validate patch syntax (no working-tree mutation yet).
    try:
        subprocess.run(
            ["git", "apply", "--check", str(patch_path)],
            cwd=str(repo_root), check=True,
            capture_output=True, text=True, encoding="utf-8",
        )
    except subprocess.CalledProcessError as exc:
        raise ApplyError(
            f"patch does not apply cleanly (git apply --check failed)"
        ) from exc

    # Extract patched file paths (T-31-04 hardened).
    files = _extract_patched_files(patch_path)
    if not files:
        raise ApplyError("patch modifies no files")

    # Pre-extract FOUND-08 frontmatter blocks (BEFORE apply).
    frontmatter_before: dict[str, str] = {}
    for f in files:
        abs_path = repo_root / f
        if abs_path.exists():
            content_before = abs_path.read_text(encoding="utf-8")
            frontmatter_before[f] = _extract_frontmatter_block(content_before)
        else:
            # Patch-added file — no prior frontmatter to preserve.
            frontmatter_before[f] = ""

    # Read the patch text once (for additive-only check).
    patch_text = patch_path.read_text(encoding="utf-8")

    applied = False
    try:
        # Step 4: apply for real.
        subprocess.run(
            ["git", "apply", str(patch_path)],
            cwd=str(repo_root), check=True,
            capture_output=True, text=True, encoding="utf-8",
        )
        applied = True

        # Step 5a: FOUND-08 byte-intact check (SC-5).
        for f in files:
            abs_after = repo_root / f
            if not abs_after.exists():
                # File was deleted by the patch? Should have been caught
                # by extract_patched_files (WR-07), but defense-in-depth.
                raise ApplyError(
                    f"file {f!r} missing after apply (deletion patches "
                    f"are out of scope)"
                )
            if not verify_found08_byte_intact(frontmatter_before[f], abs_after):
                raise ApplyError(
                    f"FOUND-08 violation: frontmatter bytes drifted in {f!r} "
                    f"(SC-5 byte-level check — likely YAML re-serialization)"
                )

        # Step 5b: additive-only check — UNIVERSAL (EVOL-02 scope discipline
        # says ALL evolution patches are additive-only). For protected v4/v5
        # refs (SC-6), raise with the explicit SC-6 violation message;
        # for other files, raise with the generic additive-only message.
        is_additive = verify_additive_only(patch_text)
        if not is_additive:
            # Determine if any touched file is a protected ref for the
            # error message specificity.
            touches_protected = any(
                any(protected in f for protected in protected_refs)
                for f in files
            )
            if touches_protected:
                raise ApplyError(
                    f"SC-6 violation: patch is not additive-only and "
                    f"touches a protected v4/v5 ref (files={files})"
                )
            raise ApplyError(
                f"patch is not additive-only (EVOL-02 scope discipline — "
                f"evolution patches only ADD content; files={files})"
            )

        # Step 6: stage + commit.
        subprocess.run(
            ["git", "add", "--"] + files,
            cwd=str(repo_root), check=True,
            capture_output=True, text=True, encoding="utf-8",
        )
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=str(repo_root), check=True,
            capture_output=True, text=True, encoding="utf-8",
        )
        sha_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root), check=True,
            capture_output=True, text=True, encoding="utf-8",
        )
        commit_sha = sha_result.stdout.strip()
        logger.info(
            "evolution patch applied: commit=%s files=%s",
            commit_sha[:12], files,
        )
        return ApplyResult(commit_sha=commit_sha, files_modified=files)
    except Exception as exc:
        # ALWAYS revert on any failure (T-31-05 / gate.py:1084 pattern).
        logger.error(
            "apply_patch_transaction failed: %s — reverting working tree",
            exc,
        )
        if applied:
            try:
                revert_files(files, repo_root)
            except Exception as revert_exc:
                logger.error(
                    "revert ALSO failed: %s — WORKING TREE LEFT DIRTY "
                    "(files=%s). Manual recovery required.",
                    revert_exc, files,
                )
                raise ApplyError(
                    f"apply failed ({exc}) AND revert failed ({revert_exc}); "
                    f"working tree dirty — manual recovery required"
                ) from exc
        if isinstance(exc, ApplyError):
            raise
        raise ApplyError(f"patch apply failed: {exc}") from exc


# --------------------------------------------------------------------------- #
# Internal: git author identity (Pitfall 7)
# --------------------------------------------------------------------------- #


def _ensure_git_author(repo_root: Path) -> None:
    """Set repo-local git author identity if unset (Pitfall 7).

    NEVER uses ``--global``. Checks ``git config user.email`` — if empty,
    sets repo-local fallback values so ``git commit`` succeeds in
    environments without global git config (Docker, CI, fresh clones).
    """
    email_check = subprocess.run(
        ["git", "config", "user.email"],
        cwd=str(repo_root), capture_output=True, text=True, encoding="utf-8",
    )
    if email_check.stdout.strip():
        return  # already set
    subprocess.run(
        ["git", "config", "user.email", _FALLBACK_AUTHOR_EMAIL],
        cwd=str(repo_root), check=True,
        capture_output=True, text=True, encoding="utf-8",
    )
    subprocess.run(
        ["git", "config", "user.name", _FALLBACK_AUTHOR_NAME],
        cwd=str(repo_root), check=True,
        capture_output=True, text=True, encoding="utf-8",
    )
    logger.debug("set repo-local git author fallback: %s", _FALLBACK_AUTHOR_EMAIL)
