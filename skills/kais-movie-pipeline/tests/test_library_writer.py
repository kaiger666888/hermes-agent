"""Tests for formula_library.library_writer (Phase 42 DATA — Plan 42-03).

Covers the write-back path of the data-convergence loop:
- apply_suggestion positive/negative eval_score nudge (±0.05)
- eval_score clamp at the [0.0, 1.0] bounds
- ValueError when the suggestion has no formula_id
- reject_suggestion moves the record into rejected.jsonl
- apply_suggestion removes the record from queue.jsonl and surfaces it in
  applied.jsonl

These tests consume the REAL sibling feedback_translator queue API
(init_queue / append_suggestion / move_suggestion) — no mock queue. That way we
exercise the full pending → applied/rejected lifecycle end to end and would
catch any drift between library_writer's assumptions and the queue contract.

Layout note: the plugins/ package is not on sys.path in the default pytest
invocation, so we inject it explicitly (mirrors the bootstrap
library_writer.py does at import time).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import bootstrap: put the plugins dir on sys.path so we can import both
# formula_library.library_writer and (transitively) feedback_translator.
# ---------------------------------------------------------------------------
_PLUGINS = Path(__file__).resolve().parents[1] / "plugins"
if str(_PLUGINS) not in sys.path:
    sys.path.insert(0, str(_PLUGINS))

from formula_library import library_writer as lw  # noqa: E402
from feedback_translator import queue as q  # noqa: E402
from feedback_translator.schema import TuningSuggestion  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tuning_dir(tmp_path: Path) -> Path:
    """Empty tuning dir with the 3 JSONL queue files initialized (all empty)."""
    d = tmp_path / "tuning"
    q.init_queue(d)
    return d


@pytest.fixture
def library_dir(tmp_path: Path) -> Path:
    """Empty formula library dir."""
    d = tmp_path / "library"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _suggestion(
    *,
    suggestion_id: str = "sug-1",
    formula_id: str | None = "f1",
    trigger: str = "OPERATOR_FEEDBACK",
    suggested_action: str = "加强 hook 强度",
    status: str = "pending",
    observed_metric: float | None = None,
    threshold: float | None = None,
) -> TuningSuggestion:
    """Build a minimal schema-valid TuningSuggestion."""
    return TuningSuggestion(
        suggestion_id=suggestion_id,
        formula_id=formula_id,
        trigger=trigger,
        observed_metric=observed_metric,
        threshold=threshold,
        suggested_action=suggested_action,
        rationale="test rationale",
        evidence=[],
        status=status,
        ts_queued="2026-06-27T00:00:00+00:00",
    )


def _enqueue(tuning_dir: Path, suggestion: TuningSuggestion) -> None:
    """Append a suggestion to queue.jsonl via the real queue API."""
    q.append_suggestion(suggestion, tuning_dir / lw.QUEUE_FILENAME)


def _write_formula(library_dir: Path, formula_id: str, eval_score: float) -> Path:
    """Write a formula JSON file (single-object layout). Returns path."""
    p = library_dir / f"{formula_id}.json"
    obj = {"formula_id": formula_id, "eval_score": eval_score, "mood": "轻喜剧"}
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    return p


def _write_formula_array(
    library_dir: Path, filename: str, formulas: list[dict]
) -> Path:
    """Write a formula JSON file as an ARRAY of formula objects (the seed layout)."""
    p = library_dir / filename
    p.write_text(json.dumps(formulas, ensure_ascii=False), encoding="utf-8")
    return p


def _read_jsonl(path: Path) -> list[dict]:
    """Read a JSONL file into a list of dicts (raw, no schema validation).

    Used to inspect applied.jsonl / rejected.jsonl directly — the queue's
    read_pending validates + filters by status, but here we want to see the raw
    moved records regardless of their (now non-pending) status.
    """
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


# ---------------------------------------------------------------------------
# apply_suggestion — eval_score nudge
# ---------------------------------------------------------------------------


def test_apply_positive_action_increases_eval_score(tuning_dir, library_dir):
    """OPERATOR_FEEDBACK + 加强 keyword → eval_score +0.05."""
    _write_formula(library_dir, "f1", eval_score=0.50)
    _enqueue(tuning_dir, _suggestion(suggested_action="加强 hook 强度"))

    updated = lw.apply_suggestion("sug-1", tuning_dir, library_dir)

    assert updated["formula_id"] == "f1"
    assert updated["eval_score"] == pytest.approx(0.55)
    # Persisted to disk too.
    on_disk = json.loads((library_dir / "f1.json").read_text(encoding="utf-8"))
    assert on_disk["eval_score"] == pytest.approx(0.55)


def test_apply_positive_action_variants(tuning_dir, library_dir):
    """All positive keywords should nudge +0.05."""
    for i, kw in enumerate(["加强", "提升", "增加"]):
        _write_formula(library_dir, f"f{i}", eval_score=0.40)
        _enqueue(
            tuning_dir,
            _suggestion(
                suggestion_id=f"s{i}",
                formula_id=f"f{i}",
                suggested_action=f"{kw} 一些东西",
            ),
        )
        updated = lw.apply_suggestion(f"s{i}", tuning_dir, library_dir)
        assert updated["eval_score"] == pytest.approx(0.45)


def test_apply_negative_action_decreases_eval_score(tuning_dir, library_dir):
    """OPERATOR_FEEDBACK + 减弱 keyword → eval_score -0.05."""
    _write_formula(library_dir, "f1", eval_score=0.50)
    _enqueue(tuning_dir, _suggestion(suggested_action="减弱 节奏"))

    updated = lw.apply_suggestion("sug-1", tuning_dir, library_dir)

    assert updated["eval_score"] == pytest.approx(0.45)


def test_apply_negative_action_variants(tuning_dir, library_dir):
    """All negative keywords should nudge -0.05, including '太'."""
    for i, kw in enumerate(["减弱", "降低", "删除", "太"]):
        _write_formula(library_dir, f"f{i}", eval_score=0.60)
        _enqueue(
            tuning_dir,
            _suggestion(
                suggestion_id=f"s{i}",
                formula_id=f"f{i}",
                suggested_action=f"这个 {kw} 多了",
            ),
        )
        updated = lw.apply_suggestion(f"s{i}", tuning_dir, library_dir)
        assert updated["eval_score"] == pytest.approx(0.55)


def test_apply_non_operator_trigger_uses_same_keyword_logic(tuning_dir, library_dir):
    """HIGH_HOOK_DROPOFF / LOW_COMPLETION etc. use the same ±keyword rule (§5)."""
    # §5 HIGH_HOOK_DROPOFF suggested action contains 加 (positive).
    _write_formula(library_dir, "fh", eval_score=0.30)
    _enqueue(
        tuning_dir,
        _suggestion(
            suggestion_id="sh",
            formula_id="fh",
            trigger="HIGH_HOOK_DROPOFF",
            observed_metric=0.30,
            threshold=0.20,
            suggested_action="加 hook 强度,升级 hook_pattern",
        ),
    )
    assert lw.apply_suggestion("sh", tuning_dir, library_dir)["eval_score"] == pytest.approx(0.35)

    # §5 LOW_COMPLETION suggested action contains 压缩 (negative).
    _write_formula(library_dir, "fl", eval_score=0.70)
    _enqueue(
        tuning_dir,
        _suggestion(
            suggestion_id="sl",
            formula_id="fl",
            trigger="LOW_COMPLETION",
            observed_metric=0.25,
            threshold=0.30,
            suggested_action="压缩铺垫,减少冗余",
        ),
    )
    assert lw.apply_suggestion("sl", tuning_dir, library_dir)["eval_score"] == pytest.approx(0.65)


def test_apply_neutral_action_is_noop_on_score(tuning_dir, library_dir):
    """An ambiguous action with no pos/neg keyword → eval_score unchanged,
    but the suggestion still moves to applied (audit trail preserved)."""
    _write_formula(library_dir, "f1", eval_score=0.50)
    _enqueue(tuning_dir, _suggestion(suggested_action="观察一段时间再说"))
    updated = lw.apply_suggestion("sug-1", tuning_dir, library_dir)
    assert updated["eval_score"] == pytest.approx(0.50)
    # Still moved to applied.
    applied = _read_jsonl(tuning_dir / lw.APPLIED_FILENAME)
    assert len(applied) == 1 and applied[0]["suggestion_id"] == "sug-1"


# ---------------------------------------------------------------------------
# eval_score clamp
# ---------------------------------------------------------------------------


def test_eval_score_clamped_at_upper_bound(tuning_dir, library_dir):
    """+0.05 when already at 0.98 → clamped to 1.0 (not 1.03)."""
    _write_formula(library_dir, "f1", eval_score=0.98)
    _enqueue(tuning_dir, _suggestion(suggested_action="加强 hook"))
    assert lw.apply_suggestion("sug-1", tuning_dir, library_dir)["eval_score"] == pytest.approx(1.0)


def test_eval_score_clamped_at_lower_bound(tuning_dir, library_dir):
    """-0.05 when already at 0.02 → clamped to 0.0 (not -0.03)."""
    _write_formula(library_dir, "f1", eval_score=0.02)
    _enqueue(tuning_dir, _suggestion(suggested_action="减弱 节奏"))
    assert lw.apply_suggestion("sug-1", tuning_dir, library_dir)["eval_score"] == pytest.approx(0.0)


def test_eval_score_at_exact_bounds_unchanged_by_same_sign_nudge(tuning_dir, library_dir):
    """Already at 1.0, positive nudge stays at 1.0; at 0.0, negative stays at 0.0."""
    _write_formula(library_dir, "f1", eval_score=1.0)
    _enqueue(tuning_dir, _suggestion(suggested_action="加强"))
    assert lw.apply_suggestion("sug-1", tuning_dir, library_dir)["eval_score"] == pytest.approx(1.0)

    _write_formula(library_dir, "f2", eval_score=0.0)
    _enqueue(tuning_dir, _suggestion(suggestion_id="sug-2", formula_id="f2", suggested_action="降低"))
    assert lw.apply_suggestion("sug-2", tuning_dir, library_dir)["eval_score"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# formula_id missing → ValueError
# ---------------------------------------------------------------------------


def test_apply_raises_when_formula_id_is_none(tuning_dir, library_dir):
    _write_formula(library_dir, "f1", eval_score=0.50)
    _enqueue(tuning_dir, _suggestion(formula_id=None))

    with pytest.raises(ValueError, match="suggestion has no formula_id"):
        lw.apply_suggestion("sug-1", tuning_dir, library_dir)


def test_apply_raises_when_suggestion_not_in_queue(tuning_dir, library_dir):
    """Applying an unknown suggestion_id should raise (not silently pass)."""
    _write_formula(library_dir, "f1", eval_score=0.50)
    with pytest.raises(ValueError, match="not found in pending queue"):
        lw.apply_suggestion("does-not-exist", tuning_dir, library_dir)


# ---------------------------------------------------------------------------
# reject_suggestion
# ---------------------------------------------------------------------------


def test_reject_suggestion_moves_to_rejected(tuning_dir, library_dir):
    _write_formula(library_dir, "f1", eval_score=0.50)
    _enqueue(tuning_dir, _suggestion())

    moved = lw.reject_suggestion("sug-1", tuning_dir, reason="指标噪声,不适用")

    assert moved.status == "rejected"
    assert moved.reason == "指标噪声,不适用"
    assert moved.ts_rejected is not None
    # Surfaces in rejected.jsonl
    rejected = _read_jsonl(tuning_dir / lw.REJECTED_FILENAME)
    assert len(rejected) == 1
    assert rejected[0]["suggestion_id"] == "sug-1"
    assert rejected[0]["reason"] == "指标噪声,不适用"
    # And removed from queue.jsonl
    assert q.read_pending(tuning_dir / lw.QUEUE_FILENAME) == []
    # Formula untouched
    assert json.loads((library_dir / "f1.json").read_text(encoding="utf-8"))["eval_score"] == pytest.approx(0.50)


def test_reject_requires_non_empty_reason(tuning_dir, library_dir):
    _enqueue(tuning_dir, _suggestion())
    with pytest.raises(ValueError, match="non-empty reason"):
        lw.reject_suggestion("sug-1", tuning_dir, reason="")
    with pytest.raises(ValueError, match="non-empty reason"):
        lw.reject_suggestion("sug-1", tuning_dir, reason="   ")


def test_reject_unknown_suggestion_raises(tuning_dir, library_dir):
    with pytest.raises(ValueError, match="not found in pending queue"):
        lw.reject_suggestion("nope", tuning_dir, reason="x")


# ---------------------------------------------------------------------------
# apply → queue/applied movement
# ---------------------------------------------------------------------------


def test_apply_removes_from_queue_and_adds_to_applied(tuning_dir, library_dir):
    _write_formula(library_dir, "f1", eval_score=0.50)
    _enqueue(tuning_dir, _suggestion())
    # sanity: present before
    assert len(q.read_pending(tuning_dir / lw.QUEUE_FILENAME)) == 1
    assert _read_jsonl(tuning_dir / lw.APPLIED_FILENAME) == []

    lw.apply_suggestion("sug-1", tuning_dir, library_dir)

    # Removed from queue
    assert q.read_pending(tuning_dir / lw.QUEUE_FILENAME) == []
    # Present in applied with the right status + no commit_sha (caller fills)
    applied = _read_jsonl(tuning_dir / lw.APPLIED_FILENAME)
    assert len(applied) == 1
    rec = applied[0]
    assert rec["suggestion_id"] == "sug-1"
    assert rec["status"] == "applied"
    assert rec["commit_sha"] is None
    assert rec["ts_applied"] is not None


def test_apply_does_not_touch_other_pending_suggestions(tuning_dir, library_dir):
    """Applying one suggestion must leave unrelated pending records in place."""
    _write_formula(library_dir, "f1", eval_score=0.50)
    _write_formula(library_dir, "f2", eval_score=0.50)
    _enqueue(tuning_dir, _suggestion(suggestion_id="sug-1", formula_id="f1"))
    _enqueue(tuning_dir, _suggestion(suggestion_id="sug-2", formula_id="f2", suggested_action="降低"))

    lw.apply_suggestion("sug-1", tuning_dir, library_dir)

    remaining = q.read_pending(tuning_dir / lw.QUEUE_FILENAME)
    assert len(remaining) == 1
    assert remaining[0].suggestion_id == "sug-2"
    applied = _read_jsonl(tuning_dir / lw.APPLIED_FILENAME)
    assert len(applied) == 1 and applied[0]["suggestion_id"] == "sug-1"


# ---------------------------------------------------------------------------
# Array-layout library support (matches the seed urban-fantasy-light.json)
# ---------------------------------------------------------------------------


def test_apply_works_with_array_layout_library(tuning_dir, library_dir):
    """The seed library stores formulas as a JSON ARRAY in one file.
    library_writer must update the right entry in-place and preserve the array shape."""
    _write_formula_array(
        library_dir,
        "urban-fantasy-light.json",
        [
            {"formula_id": "fa", "eval_score": 0.40, "mood": "轻喜剧"},
            {"formula_id": "fb", "eval_score": 0.60, "mood": "虐心"},
            {"formula_id": "fc", "eval_score": 0.50, "mood": "轻喜剧"},
        ],
    )
    _enqueue(tuning_dir, _suggestion(formula_id="fb", suggested_action="加强"))

    updated = lw.apply_suggestion("sug-1", tuning_dir, library_dir)

    # Only fb changed, +0.05.
    assert updated["formula_id"] == "fb"
    assert updated["eval_score"] == pytest.approx(0.65)
    # File still an array, with fa/fc untouched.
    on_disk = json.loads((library_dir / "urban-fantasy-light.json").read_text(encoding="utf-8"))
    assert isinstance(on_disk, list)
    assert len(on_disk) == 3
    assert on_disk[0]["eval_score"] == pytest.approx(0.40)  # fa untouched
    assert on_disk[1]["eval_score"] == pytest.approx(0.65)  # fb updated
    assert on_disk[2]["eval_score"] == pytest.approx(0.50)  # fc untouched


def test_apply_finds_formula_across_multiple_files(tuning_dir, library_dir):
    """A formula may live in any *.json file in the library dir."""
    _write_formula(library_dir, "fx", eval_score=0.70)
    _write_formula_array(
        library_dir,
        "group.json",
        [{"formula_id": "fy", "eval_score": 0.30, "mood": "虐心"}],
    )
    _enqueue(tuning_dir, _suggestion(formula_id="fy", suggested_action="降低"))

    updated = lw.apply_suggestion("sug-1", tuning_dir, library_dir)
    assert updated["formula_id"] == "fy"
    assert updated["eval_score"] == pytest.approx(0.25)
    # fx untouched.
    assert json.loads((library_dir / "fx.json").read_text(encoding="utf-8"))["eval_score"] == pytest.approx(0.70)


# ---------------------------------------------------------------------------
# Atomic write + edge cases
# ---------------------------------------------------------------------------


def test_apply_atomic_write_leaves_no_tmp_file(tuning_dir, library_dir):
    """After apply, no .tmp litter should remain in the library dir."""
    _write_formula(library_dir, "f1", eval_score=0.50)
    _enqueue(tuning_dir, _suggestion())

    lw.apply_suggestion("sug-1", tuning_dir, library_dir)

    litter = [p for p in library_dir.iterdir() if p.name.startswith(".f1.json")]
    assert litter == []
    # And the real file is valid JSON (not half-written).
    json.loads((library_dir / "f1.json").read_text(encoding="utf-8"))


def test_apply_raises_when_no_formula_file_matches(tuning_dir, library_dir):
    _write_formula(library_dir, "other", eval_score=0.50)
    _enqueue(tuning_dir, _suggestion(formula_id="missing"))

    with pytest.raises(FileNotFoundError):
        lw.apply_suggestion("sug-1", tuning_dir, library_dir)


def test_apply_raises_when_library_dir_missing(tuning_dir, tmp_path):
    _enqueue(tuning_dir, _suggestion())
    missing = tmp_path / "no-such-dir"
    with pytest.raises(FileNotFoundError):
        lw.apply_suggestion("sug-1", tuning_dir, missing)
