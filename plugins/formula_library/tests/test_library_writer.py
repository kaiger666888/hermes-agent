"""Tests for plugins.formula_library.library_writer (apply/reject).

Covers:
  - apply_suggestion: +0.05 / -0.05 / clamp [0.0, 1.0] / None baseline 0.5
  - apply_suggestion: unknown suggestion_id → ValueError
  - apply_suggestion: formula_id=None → ValueError
  - apply_suggestion: formula file not found → FileNotFoundError
  - apply_suggestion: atomic write (no .tmp leftover)
  - apply_suggestion: moves suggestion pending → applied
  - reject_suggestion: moves suggestion pending → rejected with reason

Path note: this file is at
``plugins/formula_library/tests/test_library_writer.py``. To import the
``feedback_translator`` package (a sibling of ``formula_library``), we add
``parents[2]`` (= ``plugins/``) to sys.path. ``parents[3]`` would be the
repo root which is too high — the SKILL.md pitfall calls this out.
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

# parents[2] = plugins/ — adds feedback_translator + formula_library to path.
_PLUGINS_DIR = Path(__file__).resolve().parents[2]
if str(_PLUGINS_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGINS_DIR))


# Real seed library lives under plugins/formula_library/library/.
_REAL_LIBRARY = Path(__file__).resolve().parents[1] / "library"
_REAL_FORMULA_FILENAME = "formula_urban_fantasy_light_01.json"
_REAL_FORMULA_ID = "urban-fantasy-light-01"


# ──────────────────────────────────────────────────────────────────────────
# Fixture helpers
# ──────────────────────────────────────────────────────────────────────────


def _seed_library(tmp_path: Path) -> Path:
    """Copy the real formula_*.json into tmp/library/ (no mutation of source)."""
    library_dir = tmp_path / "library"
    library_dir.mkdir()
    shutil.copy(
        _REAL_LIBRARY / _REAL_FORMULA_FILENAME,
        library_dir / _REAL_FORMULA_FILENAME,
    )
    return library_dir


def _seed_queue_with_pending(
    tuning_dir: Path,
    *,
    suggestion_id: str = "feedback_1700000000",
    formula_id: str | None = _REAL_FORMULA_ID,
    suggested_action: str = "加强前3秒冲突",
    status: str = "pending",
) -> None:
    """Seed tuning_dir/queue.jsonl with one pending suggestion.

    Uses feedback_translator.queue.append_suggestion (the canonical writer)
    so the JSONL is well-formed and read_pending will find it.
    """
    from feedback_translator import init_queue, append_suggestion
    from feedback_translator.schema import (
        OPERATOR_FEEDBACK_TRIGGER,
        TuningSuggestion,
    )

    init_queue(tuning_dir)
    s = TuningSuggestion(
        suggestion_id=suggestion_id,
        formula_id=formula_id,
        trigger=OPERATOR_FEEDBACK_TRIGGER,
        suggested_action=suggested_action,
        rationale="测试",
        evidence=[],
        status=status,
        ts_queued=datetime.now(timezone.utc).isoformat(),
    )
    append_suggestion(s, tuning_dir / "queue.jsonl")


# ──────────────────────────────────────────────────────────────────────────
# apply_suggestion: +0.05 for 加强/提升/增加
# ──────────────────────────────────────────────────────────────────────────


def test_apply_suggestion_increase_delta(tmp_path: Path) -> None:
    """suggested_action 含 '加强' → eval_score +0.05."""
    from formula_library.library_writer import apply_suggestion

    library_dir = _seed_library(tmp_path)
    tuning_dir = tmp_path / "tuning"
    # Pre-set eval_score to a known value.
    formula_path = library_dir / _REAL_FORMULA_FILENAME
    data = json.loads(formula_path.read_text(encoding="utf-8"))
    data["eval_score"] = 0.5
    formula_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    _seed_queue_with_pending(
        tuning_dir,
        suggestion_id="inc_1",
        suggested_action="加强前3秒冲突",
    )
    result = apply_suggestion("inc_1", tuning_dir, library_dir)
    assert result["eval_score"] == pytest.approx(0.55)


# ──────────────────────────────────────────────────────────────────────────
# apply_suggestion: -0.05 for 减弱/降低/删除/太
# ──────────────────────────────────────────────────────────────────────────


def test_apply_suggestion_decrease_delta(tmp_path: Path) -> None:
    """suggested_action 含 '降低' → eval_score -0.05."""
    from formula_library.library_writer import apply_suggestion

    library_dir = _seed_library(tmp_path)
    tuning_dir = tmp_path / "tuning"
    formula_path = library_dir / _REAL_FORMULA_FILENAME
    data = json.loads(formula_path.read_text(encoding="utf-8"))
    data["eval_score"] = 0.5
    formula_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    _seed_queue_with_pending(
        tuning_dir,
        suggestion_id="dec_1",
        suggested_action="降低铺垫",
    )
    result = apply_suggestion("dec_1", tuning_dir, library_dir)
    assert result["eval_score"] == pytest.approx(0.45)


def test_apply_suggestion_decrease_keyword_ta(tmp_path: Path) -> None:
    """suggested_action 含 '太' → eval_score -0.05 (e.g. '节奏太快')."""
    from formula_library.library_writer import apply_suggestion

    library_dir = _seed_library(tmp_path)
    tuning_dir = tmp_path / "tuning"
    formula_path = library_dir / _REAL_FORMULA_FILENAME
    data = json.loads(formula_path.read_text(encoding="utf-8"))
    data["eval_score"] = 0.6
    formula_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    _seed_queue_with_pending(
        tuning_dir,
        suggestion_id="ta_1",
        suggested_action="节奏太快了",
    )
    result = apply_suggestion("ta_1", tuning_dir, library_dir)
    assert result["eval_score"] == pytest.approx(0.55)


# ──────────────────────────────────────────────────────────────────────────
# apply_suggestion: clamp + None baseline
# ──────────────────────────────────────────────────────────────────────────


def test_apply_suggestion_clamp_high(tmp_path: Path) -> None:
    """eval_score clamps to 1.0 when +0.05 would exceed it."""
    from formula_library.library_writer import apply_suggestion

    library_dir = _seed_library(tmp_path)
    tuning_dir = tmp_path / "tuning"
    formula_path = library_dir / _REAL_FORMULA_FILENAME
    data = json.loads(formula_path.read_text(encoding="utf-8"))
    data["eval_score"] = 0.98
    formula_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    _seed_queue_with_pending(
        tuning_dir, suggestion_id="clamp_hi", suggested_action="提升"
    )
    result = apply_suggestion("clamp_hi", tuning_dir, library_dir)
    assert result["eval_score"] == pytest.approx(1.0)


def test_apply_suggestion_clamp_low(tmp_path: Path) -> None:
    """eval_score clamps to 0.0 when -0.05 would go negative."""
    from formula_library.library_writer import apply_suggestion

    library_dir = _seed_library(tmp_path)
    tuning_dir = tmp_path / "tuning"
    formula_path = library_dir / _REAL_FORMULA_FILENAME
    data = json.loads(formula_path.read_text(encoding="utf-8"))
    data["eval_score"] = 0.02
    formula_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    _seed_queue_with_pending(
        tuning_dir, suggestion_id="clamp_lo", suggested_action="降低"
    )
    result = apply_suggestion("clamp_lo", tuning_dir, library_dir)
    assert result["eval_score"] == pytest.approx(0.0)


def test_apply_suggestion_none_baseline(tmp_path: Path) -> None:
    """eval_score=None is treated as baseline 0.5 before applying delta."""
    from formula_library.library_writer import apply_suggestion

    library_dir = _seed_library(tmp_path)
    tuning_dir = tmp_path / "tuning"
    # The real seed has eval_score=None already — no need to mutate.

    _seed_queue_with_pending(
        tuning_dir, suggestion_id="none_1", suggested_action="加强"
    )
    result = apply_suggestion("none_1", tuning_dir, library_dir)
    assert result["eval_score"] == pytest.approx(0.55)


# ──────────────────────────────────────────────────────────────────────────
# apply_suggestion: error cases
# ──────────────────────────────────────────────────────────────────────────


def test_apply_suggestion_unknown_id_raises(tmp_path: Path) -> None:
    """apply_suggestion raises ValueError for an unknown suggestion_id."""
    from formula_library.library_writer import apply_suggestion

    library_dir = _seed_library(tmp_path)
    tuning_dir = tmp_path / "tuning"
    _seed_queue_with_pending(tuning_dir, suggestion_id="real_one")

    with pytest.raises(ValueError, match="not found"):
        apply_suggestion("bogus_id", tuning_dir, library_dir)


def test_apply_suggestion_null_formula_id_raises(tmp_path: Path) -> None:
    """apply_suggestion raises ValueError when formula_id is None."""
    from formula_library.library_writer import apply_suggestion

    library_dir = _seed_library(tmp_path)
    tuning_dir = tmp_path / "tuning"
    _seed_queue_with_pending(
        tuning_dir,
        suggestion_id="generic_1",
        formula_id=None,
        suggested_action="减少铺垫",
    )

    with pytest.raises(ValueError, match="formula_id=None"):
        apply_suggestion("generic_1", tuning_dir, library_dir)


def test_apply_suggestion_unknown_formula_raises(tmp_path: Path) -> None:
    """apply_suggestion raises FileNotFoundError when formula not in library."""
    from formula_library.library_writer import apply_suggestion

    library_dir = _seed_library(tmp_path)
    tuning_dir = tmp_path / "tuning"
    _seed_queue_with_pending(
        tuning_dir,
        suggestion_id="miss_1",
        formula_id="nonexistent-formula",
        suggested_action="加强",
    )

    with pytest.raises(FileNotFoundError, match="not found"):
        apply_suggestion("miss_1", tuning_dir, library_dir)


# ──────────────────────────────────────────────────────────────────────────
# apply_suggestion: atomic write + queue move
# ──────────────────────────────────────────────────────────────────────────


def test_apply_suggestion_atomic_no_tmp_leftover(tmp_path: Path) -> None:
    """After apply, no .formula.*.tmp file lingers in the library dir."""
    from formula_library.library_writer import apply_suggestion

    library_dir = _seed_library(tmp_path)
    tuning_dir = tmp_path / "tuning"
    _seed_queue_with_pending(
        tuning_dir, suggestion_id="atom_1", suggested_action="加强"
    )
    apply_suggestion("atom_1", tuning_dir, library_dir)

    leftovers = list(library_dir.glob(".formula.*.tmp"))
    assert leftovers == [], f"unexpected temp leftover: {leftovers}"


def test_apply_suggestion_moves_to_applied(tmp_path: Path) -> None:
    """apply_suggestion moves the suggestion pending → applied.jsonl."""
    from feedback_translator import read_pending
    from formula_library.library_writer import apply_suggestion

    library_dir = _seed_library(tmp_path)
    tuning_dir = tmp_path / "tuning"
    _seed_queue_with_pending(
        tuning_dir, suggestion_id="mv_1", suggested_action="加强"
    )
    apply_suggestion("mv_1", tuning_dir, library_dir)

    # queue.jsonl no longer has it.
    queue_path = tuning_dir / "queue.jsonl"
    assert read_pending(queue_path) == []
    # applied.jsonl has it with a commit_sha.
    applied_path = tuning_dir / "applied.jsonl"
    applied_lines = [
        json.loads(line)
        for line in applied_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(applied_lines) == 1
    assert applied_lines[0]["suggestion_id"] == "mv_1"
    assert applied_lines[0]["status"] == "applied"
    assert applied_lines[0]["commit_sha"]  # non-empty


def test_apply_suggestion_preserves_other_fields(tmp_path: Path) -> None:
    """Every field EXCEPT eval_score is preserved after apply."""
    from formula_library.library_writer import apply_suggestion

    library_dir = _seed_library(tmp_path)
    tuning_dir = tmp_path / "tuning"
    formula_path = library_dir / _REAL_FORMULA_FILENAME
    original = json.loads(formula_path.read_text(encoding="utf-8"))
    original["eval_score"] = 0.4
    formula_path.write_text(
        json.dumps(original, ensure_ascii=False), encoding="utf-8"
    )

    _seed_queue_with_pending(
        tuning_dir, suggestion_id="keep_1", suggested_action="加强"
    )
    apply_suggestion("keep_1", tuning_dir, library_dir)

    rewritten = json.loads(formula_path.read_text(encoding="utf-8"))
    assert rewritten["eval_score"] == pytest.approx(0.45)
    for key, value in original.items():
        if key == "eval_score":
            continue
        assert rewritten[key] == value, f"field {key!r} mutated"


# ──────────────────────────────────────────────────────────────────────────
# reject_suggestion
# ──────────────────────────────────────────────────────────────────────────


def test_reject_suggestion_moves_to_rejected(tmp_path: Path) -> None:
    """reject_suggestion moves a suggestion queue → rejected with reason."""
    from feedback_translator import read_pending
    from formula_library.library_writer import reject_suggestion

    tuning_dir = tmp_path / "tuning"
    _seed_queue_with_pending(tuning_dir, suggestion_id="rej_1")

    moved = reject_suggestion("rej_1", tuning_dir, reason="不适用此题材")
    assert moved is not None
    assert moved.status == "rejected"
    assert moved.reason == "不适用此题材"

    # queue.jsonl no longer has it.
    queue_path = tuning_dir / "queue.jsonl"
    assert read_pending(queue_path) == []
    # rejected.jsonl has it.
    rejected_path = tuning_dir / "rejected.jsonl"
    rejected_lines = [
        json.loads(line)
        for line in rejected_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rejected_lines) == 1
    assert rejected_lines[0]["suggestion_id"] == "rej_1"
    assert rejected_lines[0]["reason"] == "不适用此题材"


def test_reject_suggestion_unknown_id_returns_none(tmp_path: Path) -> None:
    """reject_suggestion returns None for an unknown suggestion_id."""
    from formula_library.library_writer import reject_suggestion

    tuning_dir = tmp_path / "tuning"
    _seed_queue_with_pending(tuning_dir, suggestion_id="real_one")
    result = reject_suggestion("bogus", tuning_dir, reason="x")
    assert result is None
