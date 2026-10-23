"""library_writer.py — apply/reject TuningSuggestions to formula_library.

This is the write-back half of the feedback loop: after the operator
approves a pending :class:`feedback_translator.schema.TuningSuggestion`,
:func:`apply_suggestion` locates the target formula file in
``library/*.json``, nudges ``eval_score`` by ±0.05 based on the Chinese
keywords in ``suggested_action``, atomically writes it back (temp +
os.replace), then moves the suggestion pending → applied.

Cross-plugin import note: this module needs to read the
``feedback_translator.queue`` functions (``read_pending`` /
``move_suggestion``). Because ``plugins/`` is not on ``sys.path`` by
default, this module injects its own parent directory into ``sys.path``
at import time so that ``import feedback_translator.queue`` resolves.
Tests must do the same (see ``tests/test_library_writer.py`` which uses
``parents[2]`` to locate the ``plugins/`` dir).

eval_score delta rule (中文 keyword match):
  - suggested_action contains 加强 / 提升 / 增加 → +0.05
  - suggested_action contains 减弱 / 降低 / 删除 / 太 → -0.05
  - neither → no change (eval_score stays as-is)
  - clamped to [0.0, 1.0]; None is treated as 0.5 baseline

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 unions.
  - ``encoding="utf-8"`` on every ``open()`` (Ruff PLW1514).
  - Atomic file writes (tempfile + os.replace).
"""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# sys.path injection so ``import feedback_translator.queue`` resolves.
# --------------------------------------------------------------------------- #
# This file lives at plugins/formula_library/library_writer.py.
# parents[0] = formula_library/, parents[1] = plugins/.
_PLUGINS_DIR = str(Path(__file__).resolve().parents[1])
if _PLUGINS_DIR not in sys.path:
    sys.path.insert(0, _PLUGINS_DIR)

from feedback_translator.queue import (  # noqa: E402 — sys.path mutated above
    move_suggestion as _move_suggestion,
    read_pending as _read_pending,
)


# --------------------------------------------------------------------------- #
# eval_score delta keywords (中文)
# --------------------------------------------------------------------------- #

_INCREASE_KEYWORDS: tuple[str, ...] = ("加强", "提升", "增加")
_DECREASE_KEYWORDS: tuple[str, ...] = ("减弱", "降低", "删除", "太")
_EVAL_SCORE_DELTA: float = 0.05
_EVAL_SCORE_BASELINE: float = 0.5  # used when eval_score is None


def _delta_for_action(suggested_action: str) -> float:
    """Return +0.05 / -0.05 / 0.0 based on 中文 keywords in *suggested_action*."""
    if any(kw in suggested_action for kw in _INCREASE_KEYWORDS):
        return _EVAL_SCORE_DELTA
    if any(kw in suggested_action for kw in _DECREASE_KEYWORDS):
        return -_EVAL_SCORE_DELTA
    return 0.0


# --------------------------------------------------------------------------- #
# Low-level file I/O (mirror platform_metrics.library_writer helpers)
# --------------------------------------------------------------------------- #


def _load_formula_file(path: Path) -> dict[str, Any]:
    """Read + parse a formula JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def _write_formula_file_atomic(path: Path, data: dict[str, Any]) -> None:
    """Atomically write *data* as JSON to *path* (temp + os.replace)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent), prefix=".formula.", suffix=".tmp"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _find_formula_file(
    library_dir: Path, formula_id: str
) -> tuple[Path, dict[str, Any]] | None:
    """Locate the formula dict with ``formula_id`` under *library_dir*.

    Handles BOTH single-object (``{...}``) and JSON-array
    (``[{...}, ...]``) file formats. Returns ``(path, formula_dict)`` for
    the first match, or None if not found.
    """
    if not library_dir.is_dir():
        return None
    for json_path in sorted(library_dir.glob("*.json")):
        try:
            raw = json_path.read_text(encoding="utf-8")
            obj = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("skipped unreadable formula file %s: %s", json_path, exc)
            continue
        if isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict) and item.get("formula_id") == formula_id:
                    # NOTE: array format cannot be written back as a single
                    # object — but for the apply path we write the matched
                    # item as a standalone object to *json_path* (the only
                    # writer in this module). Callers using arrays should
                    # pre-split them.
                    return json_path, item
        elif isinstance(obj, dict) and obj.get("formula_id") == formula_id:
            return json_path, obj
    return None


# --------------------------------------------------------------------------- #
# apply_suggestion
# --------------------------------------------------------------------------- #


def apply_suggestion(
    suggestion_id: str,
    tuning_dir: Path | str,
    library_dir: Path | str,
) -> dict[str, Any]:
    """Apply a pending TuningSuggestion by nudging eval_score ±0.05.

    Pipeline:
      1. Read pending suggestions from ``tuning_dir/queue.jsonl``.
      2. Find the one with matching *suggestion_id*.
      3. Resolve its ``formula_id`` (raises ValueError if None).
      4. Locate the formula file in *library_dir* (single-object or array).
      5. Nudge ``eval_score`` by ``_delta_for_action(suggested_action)``,
         clamped to [0.0, 1.0]. None baseline = 0.5.
      6. Atomically write the formula JSON.
      7. move_suggestion pending → applied (with commit_sha = post-write sha).
      8. Return the updated formula dict.

    Args:
        suggestion_id: The ID of the pending suggestion to apply.
        tuning_dir: Directory containing queue.jsonl / applied.jsonl.
        library_dir: Directory containing formula_*.json files.

    Returns:
        The updated formula dict (with the new eval_score).

    Raises:
        ValueError: if the suggestion is not found, or its formula_id is None.
        FileNotFoundError: if the formula file is not found in library_dir.
    """
    tuning_dir = Path(tuning_dir)
    library_dir = Path(library_dir)
    queue_path = tuning_dir / "queue.jsonl"
    applied_path = tuning_dir / "applied.jsonl"

    pending = _read_pending(queue_path)
    target = next(
        (s for s in pending if s.suggestion_id == suggestion_id), None
    )
    if target is None:
        raise ValueError(
            f"apply_suggestion: suggestion {suggestion_id!r} not found in "
            f"{queue_path} (or not pending)"
        )

    if target.formula_id is None:
        raise ValueError(
            f"apply_suggestion: suggestion {suggestion_id!r} has "
            f"formula_id=None — cannot apply generic feedback"
        )

    found = _find_formula_file(library_dir, target.formula_id)
    if found is None:
        available = sorted(p.name for p in library_dir.glob("*.json"))
        raise FileNotFoundError(
            f"formula file for {target.formula_id!r} not found under "
            f"{library_dir}; available: {available}"
        )
    formula_path, formula = found

    # Compute new eval_score.
    current = formula.get("eval_score")
    baseline = current if current is not None else _EVAL_SCORE_BASELINE
    delta = _delta_for_action(target.suggested_action)
    new_score = max(0.0, min(1.0, baseline + delta))
    formula["eval_score"] = new_score

    # Atomic write. Preserve the array-layout shape when the source file is a
    # JSON array (seed library format) — update the matched entry in place
    # rather than collapsing the file to a single object. Single-object files
    # are written back as before.
    try:
        raw_obj = json.loads(formula_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raw_obj = None
    if isinstance(raw_obj, list):
        for i, item in enumerate(raw_obj):
            if isinstance(item, dict) and item.get("formula_id") == target.formula_id:
                raw_obj[i] = formula
                break
        _write_formula_file_atomic(formula_path, raw_obj)
    else:
        _write_formula_file_atomic(formula_path, formula)

    # Compute a commit_sha from the post-write content (deterministic).
    import hashlib
    commit_sha = hashlib.sha256(
        json.dumps(formula, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()

    # Move suggestion pending → applied.
    _move_suggestion(
        suggestion_id,
        from_queue=queue_path,
        to_path=applied_path,
        commit_sha=commit_sha,
    )

    logger.info(
        "applied suggestion %s → %s (eval_score=%s, delta=%+.2f)",
        suggestion_id, formula_path.name, new_score, delta,
    )
    return formula


# --------------------------------------------------------------------------- #
# reject_suggestion
# --------------------------------------------------------------------------- #


def reject_suggestion(
    suggestion_id: str,
    tuning_dir: Path | str,
    reason: str,
) -> Any:
    """Reject a pending TuningSuggestion (move queue → rejected with reason).

    Args:
        suggestion_id: The ID of the pending suggestion to reject.
        tuning_dir: Directory containing queue.jsonl / rejected.jsonl.
        reason: The rejection reason (recorded on the suggestion). MUST be
            non-empty — an empty/whitespace reason is rejected with
            ValueError so the audit trail always carries an explanation.

    Returns:
        The updated TuningSuggestion (status='rejected'), or None if the
        suggestion was not found in queue.jsonl.

    Raises:
        ValueError: if *reason* is empty/whitespace-only.
    """
    if not reason or not str(reason).strip():
        raise ValueError(
            "reject_suggestion requires a non-empty reason — audit trail "
            "must explain why the suggestion was rejected"
        )
    tuning_dir = Path(tuning_dir)
    queue_path = tuning_dir / "queue.jsonl"
    rejected_path = tuning_dir / "rejected.jsonl"
    return _move_suggestion(
        suggestion_id,
        from_queue=queue_path,
        to_path=rejected_path,
        reason=reason,
    )


__all__ = [
    "apply_suggestion",
    "reject_suggestion",
]
