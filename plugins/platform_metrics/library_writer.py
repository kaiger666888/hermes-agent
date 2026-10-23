"""library_writer.py — atomic formula_library write-back (DATA-03).

After the operator approves a :class:`TuningSuggestion`,
:func:`apply_suggestion` locates the target formula file in
``plugins/formula_library/library/``, updates ONLY the ``eval_score``
field via a temp+os.replace atomic write, then moves the suggestion
pending → applied in the JSONL queue.

NEVER overwrites any non-eval_score field (write integrity — formulas
are fair-use curated content, not freely editable). A post-write
integrity assertion reloads the file and compares every non-eval_score
key against the pre-write snapshot (T-42-09 mitigation).

HIL invariant (load-bearing): :func:`apply_suggestion` refuses to write
unless ``suggestion.status == "approved"`` — raising
:class:`SuggestionNotApprovedError`. The operator approval step happens
out-of-band (Plan 42-04 CLI); the loop never auto-applies.

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 unions.
  - ``encoding="utf-8"`` on every ``open()`` (Ruff PLW1514).
  - Keyword-only args on public functions.
  - Lazy %-logging; specific exceptions bound.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from plugins.platform_metrics.queue import move_suggestion
from plugins.platform_metrics.schema import TuningSuggestion

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #


class SuggestionNotApprovedError(RuntimeError):
    """Raised when apply_suggestion is called on a non-pending suggestion.

    HIL invariant: the operator approval step is non-bypassable. The
    tuning loop emits suggestions with status="pending"; the operator
    invokes apply_suggestion (via the Plan 42-04 CLI) as the approval
    action — apply_suggestion performs BOTH the formula write AND the
    queue move (pending → applied) in one atomic-by-convention step.

    A suggestion that is already "applied" or "rejected" must NOT be
    re-applied. This guard catches double-apply bugs and ensures the
    only path from pending → applied is through this single function
    (AST-walk-enforced single-caller invariant).

    Note on schema: ``TuningSuggestion.status`` is a 3-value Literal
    (``pending`` / ``applied`` / ``rejected``) — there is no separate
    "approved" status. The operator's "approval" IS the act of calling
    apply_suggestion; the suggestion transitions pending → applied as
    a side effect of the successful write.
    """


# --------------------------------------------------------------------------- #
# Low-level file I/O
# --------------------------------------------------------------------------- #


def load_formula_file(path: Path) -> dict[str, Any]:
    """Read a formula JSON file and return the parsed dict.

    Args:
        path: Path to a ``formula_*.json`` file.

    Returns:
        Parsed JSON as a dict.

    Raises:
        FileNotFoundError: if the file does not exist (re-raised naturally
            from ``read_text``).
    """
    return json.loads(path.read_text(encoding="utf-8"))


def write_formula_file(path: Path, data: dict[str, Any]) -> None:
    """Atomically write *data* as JSON to *path* (temp + os.replace).

    Uses a temp file in the same directory (so os.replace is atomic on
    POSIX — same filesystem). On any exception, the temp file is
    unlinked (mirrors ``agent/evolution/queue.py:_atomic_rewrite_jsonl``
    cleanup pattern).

    ``ensure_ascii=False, indent=2`` preserves the existing formula file
    style (formula_urban_fantasy_light_01.json is indent=2 with non-ASCII
    content like "都市奇幻" preserved verbatim).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent), prefix=".formula.", suffix=".tmp"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")  # trailing newline matches existing files
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        # Clean up the temp file on any failure (T-42-13 mitigation).
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# --------------------------------------------------------------------------- #
# apply_suggestion — the HIL-gated entry point
# --------------------------------------------------------------------------- #


def apply_suggestion(
    *,
    suggestion: TuningSuggestion,
    library_dir: Path,
    tuning_dir: Path,
) -> str:
    """Apply a pending TuningSuggestion by writing eval_score to the formula.

    Single-caller invariant: this is the ONLY function that writes to
    ``library/*.json`` (AST-walk-enforced by
    ``test_library_writer_is_only_caller_to_formula_library``).

    HIL invariant (load-bearing): refuses to write unless
    ``suggestion.status == "pending"``. The operator's "approval" IS the
    act of calling this function — apply_suggestion performs BOTH the
    formula write AND the queue move (pending → applied). Raises
    :class:`SuggestionNotApprovedError` if the suggestion is already
    applied or rejected (double-apply guard).

    Args:
        suggestion: The pending TuningSuggestion to apply.
            ``observed_metric`` becomes the new ``eval_score`` (uniform
            mapping rule; future variants may differentiate by trigger,
            but v9.0 uses uniform). MUST also exist in
            ``tuning_dir/queue.jsonl`` so the post-write move succeeds.
        library_dir: Directory containing ``formula_*.json`` files.
        tuning_dir: Directory containing the JSONL queue (so the
            suggestion can be moved pending → applied after write-back).

    Returns:
        64-character sha256 hex commit_sha (sha256 of the post-write
        JSON content, sort_keys=True). Also passed to move_suggestion
        as the ``commit_sha`` kwarg.

    Raises:
        SuggestionNotApprovedError: if ``suggestion.status`` is not
            ``"pending"`` (already applied / rejected / unknown).
        FileNotFoundError: if the formula file for ``suggestion.formula_id``
            does not exist under ``library_dir``.
        KeyError: from move_suggestion if the suggestion is not in
            queue.jsonl (caller contract violation).
    """
    # HIL gate (load-bearing — check BEFORE any file mutation).
    if suggestion.status != "pending":
        raise SuggestionNotApprovedError(
            f"apply_suggestion requires status='pending' (the operator "
            f"approval IS the act of calling this function), got "
            f"{suggestion.status!r} for suggestion "
            f"{suggestion.suggestion_id!r} — double-apply / "
            f"apply-rejected is non-bypassable (HIL invariant)"
        )

    # Locate the target formula file. Phase 39 convention: filename is
    # ``formula_<slugified_id>.json`` where slugify converts hyphens →
    # underscores. e.g. ``urban-fantasy-light-01`` →
    # ``formula_urban_fantasy_light_01.json``.
    target_filename = f"formula_{suggestion.formula_id.replace('-', '_')}.json"
    target_path = library_dir / target_filename
    if not target_path.exists():
        available = sorted(p.name for p in library_dir.glob("*.json"))
        raise FileNotFoundError(
            f"formula file for {suggestion.formula_id!r} not found at "
            f"{target_path}; available: {available}"
        )

    # Load + snapshot for the post-write integrity assertion.
    original = load_formula_file(target_path)
    original_snapshot = json.loads(json.dumps(original))

    # Mutate ONLY eval_score (T-42-09 mitigation — single field write).
    updated = json.loads(json.dumps(original))
    updated["eval_score"] = suggestion.observed_metric

    # Compute commit_sha from the post-write content (sort_keys for
    # deterministic hashing regardless of dict insertion order).
    commit_sha = hashlib.sha256(
        json.dumps(updated, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()

    # Atomic write.
    write_formula_file(target_path, updated)
    logger.info(
        "applied suggestion %s → %s (eval_score=%s, commit_sha=%s)",
        suggestion.suggestion_id, target_path.name,
        suggestion.observed_metric, commit_sha,
    )

    # Post-write integrity assertion (T-42-09): reload and verify every
    # non-eval_score key matches the pre-write snapshot.
    rewritten = load_formula_file(target_path)
    for key, value in original_snapshot.items():
        if key == "eval_score":
            continue
        if key not in rewritten:
            raise RuntimeError(
                f"integrity violation: key {key!r} missing from {target_path} "
                f"after apply_suggestion — formula file corrupted"
            )
        if rewritten[key] != value:
            raise RuntimeError(
                f"integrity violation: field {key!r} mutated by "
                f"apply_suggestion (before={value!r}, after={rewritten[key]!r}) "
                f"— only eval_score is writable"
            )
    # Confirm eval_score actually changed. Python's json module preserves
    # float precision across round-trip (uses repr(float) which round-trips),
    # so direct == is safe here.
    if rewritten["eval_score"] != updated["eval_score"]:
        raise RuntimeError(
            f"eval_score not updated correctly: expected "
            f"{updated['eval_score']!r}, got {rewritten['eval_score']!r}"
        )

    # Move suggestion pending → applied in the JSONL queue (with commit_sha).
    move_suggestion(
        suggestion_id=suggestion.suggestion_id,
        target_status="applied",
        tuning_dir=tuning_dir,
        commit_sha=commit_sha,
    )

    return commit_sha


__all__ = [
    "SuggestionNotApprovedError",
    "load_formula_file",
    "write_formula_file",
    "apply_suggestion",
]
