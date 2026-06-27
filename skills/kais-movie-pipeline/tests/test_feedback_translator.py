"""test_feedback_translator.py — tests for the feedback_translator plugin.

Covers:
  1. init_queue creates queue.jsonl / applied.jsonl / rejected.jsonl.
  2. append_suggestion → read_pending round-trips a record.
  3. move_suggestion removes the record from the source queue and lands it
     (status mutated) in the destination; queue no longer contains it.
  4. translate_feedback builds a TuningSuggestion via a mock delegate_task
     (no real LLM), writes it to the queue, and returns it. Includes the
     formula-matching path (formula_id pinned from the library).

Pure stdlib + pydantic. pytest-collectible. No network.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure the skill root is importable so ``from plugins...`` works no matter
# where pytest is invoked from.
_SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

from plugins.feedback_translator import (  # noqa: E402
    append_suggestion,
    init_queue,
    move_suggestion,
    read_pending,
    translate_feedback,
)
from plugins.feedback_translator.schema import TuningSuggestion  # noqa: E402


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tuning_dir(tmp_path: Path) -> Path:
    """A fresh 3-file queue directory."""
    d = tmp_path / "tuning"
    init_queue(d)
    return d


def _make_suggestion(
    suggestion_id: str = "feedback_1700000000",
    formula_id: str | None = None,
) -> TuningSuggestion:
    return TuningSuggestion(
        suggestion_id=suggestion_id,
        formula_id=formula_id,
        trigger="OPERATOR_FEEDBACK",
        observed_metric=None,
        threshold=None,
        suggested_action="前 3 秒加矛盾，提升 hook 强度",
        rationale="运营者反馈 hook 太慢，观众在前 3 秒流失",
        evidence=["operator_feedback:feedback_1700000000"],
        status="pending",
        ts_queued="2024-01-01T00:00:00+00:00",
    )


# ---------------------------------------------------------------------------
# 1. init_queue
# ---------------------------------------------------------------------------


def test_init_queue_creates_three_files(tmp_path: Path) -> None:
    d = tmp_path / "tuning"
    assert not d.exists()

    paths = init_queue(d)

    # Directory + all 3 files exist.
    assert d.is_dir()
    for name in ("queue", "applied", "rejected"):
        p = paths[name]
        assert p == d / f"{name}.jsonl"
        assert p.exists()
        assert p.is_file()


def test_init_queue_is_idempotent(tmp_path: Path) -> None:
    """Re-running init_queue must not truncate existing queue contents."""
    d = tmp_path / "tuning"
    init_queue(d)
    queue = d / "queue.jsonl"

    # Seed a line.
    append_suggestion(_make_suggestion(), queue)
    assert queue.read_text(encoding="utf-8").strip() != ""

    # Re-init; content preserved.
    init_queue(d)
    lines = [l for l in queue.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 1


# ---------------------------------------------------------------------------
# 2. append_suggestion + read_pending
# ---------------------------------------------------------------------------


def test_append_then_read_pending_roundtrip(tuning_dir: Path) -> None:
    queue = tuning_dir / "queue.jsonl"
    sug = _make_suggestion(suggestion_id="feedback_111")

    append_suggestion(sug, queue)

    pending = read_pending(queue)
    assert len(pending) == 1
    assert pending[0].suggestion_id == "feedback_111"
    assert pending[0].status == "pending"
    assert pending[0].trigger == "OPERATOR_FEEDBACK"
    # evidence default carries the operator_feedback token.
    assert pending[0].evidence == ["operator_feedback:feedback_1700000000"]


def test_read_pending_filters_out_non_pending(tuning_dir: Path) -> None:
    queue = tuning_dir / "queue.jsonl"
    pending_sug = _make_suggestion(suggestion_id="feedback_p1")
    # Hand-write a record whose status is already 'applied' directly to the
    # queue file (simulating a stale/partial state) — read_pending must skip.
    applied_sug = _make_suggestion(suggestion_id="feedback_a1")
    applied_line = applied_sug.model_dump_json().replace(
        '"status":"pending"', '"status":"applied"'
    )
    # If the replace didn't land (field ordering), patch via dict round-trip.
    obj = json.loads(applied_line)
    obj["status"] = "applied"
    applied_line = json.dumps(obj, ensure_ascii=False)

    append_suggestion(pending_sug, queue)
    with open(queue, "a", encoding="utf-8") as fh:
        fh.write(applied_line + "\n")

    pending = read_pending(queue)
    assert len(pending) == 1
    assert pending[0].suggestion_id == "feedback_p1"


def test_read_pending_skips_malformed_lines(tuning_dir: Path) -> None:
    queue = tuning_dir / "queue.jsonl"
    append_suggestion(_make_suggestion(suggestion_id="feedback_good"), queue)
    with open(queue, "a", encoding="utf-8") as fh:
        fh.write("{not valid json\n")  # corrupt line

    pending = read_pending(queue)
    assert len(pending) == 1
    assert pending[0].suggestion_id == "feedback_good"


def test_read_pending_missing_file_returns_empty(tmp_path: Path) -> None:
    assert read_pending(tmp_path / "nope.jsonl") == []


# ---------------------------------------------------------------------------
# 3. move_suggestion
# ---------------------------------------------------------------------------


def test_move_suggestion_pending_to_applied(tuning_dir: Path) -> None:
    queue = tuning_dir / "queue.jsonl"
    applied = tuning_dir / "applied.jsonl"

    append_suggestion(_make_suggestion(suggestion_id="feedback_move1"), queue)
    assert len(read_pending(queue)) == 1

    moved = move_suggestion(
        "feedback_move1",
        from_queue=queue,
        to_path=applied,
        commit_sha="abc123",
    )

    # Returned record is mutated.
    assert moved is not None
    assert moved.status == "applied"
    assert moved.commit_sha == "abc123"
    assert moved.ts_applied is not None

    # Source queue no longer contains the record.
    assert read_pending(queue) == []
    # Destination gained exactly one line, status applied.
    ap_lines = [
        json.loads(l)
        for l in applied.read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    assert len(ap_lines) == 1
    assert ap_lines[0]["status"] == "applied"
    assert ap_lines[0]["suggestion_id"] == "feedback_move1"
    assert ap_lines[0]["commit_sha"] == "abc123"


def test_move_suggestion_pending_to_rejected(tuning_dir: Path) -> None:
    queue = tuning_dir / "queue.jsonl"
    rejected = tuning_dir / "rejected.jsonl"

    append_suggestion(_make_suggestion(suggestion_id="feedback_rej"), queue)

    moved = move_suggestion(
        "feedback_rej",
        from_queue=queue,
        to_path=rejected,
        reason="建议与运营方向不符",
    )

    assert moved is not None
    assert moved.status == "rejected"
    assert moved.reason == "建议与运营方向不符"
    assert moved.ts_rejected is not None
    assert read_pending(queue) == []


def test_move_suggestion_preserves_other_records(tuning_dir: Path) -> None:
    """Moving one record must not drop its siblings in the source queue."""
    queue = tuning_dir / "queue.jsonl"
    applied = tuning_dir / "applied.jsonl"

    append_suggestion(_make_suggestion(suggestion_id="feedback_keep"), queue)
    append_suggestion(_make_suggestion(suggestion_id="feedback_move2"), queue)

    moved = move_suggestion("feedback_move2", queue, applied)
    assert moved is not None

    remaining = read_pending(queue)
    assert len(remaining) == 1
    assert remaining[0].suggestion_id == "feedback_keep"


def test_move_suggestion_unknown_id_returns_none(tuning_dir: Path) -> None:
    queue = tuning_dir / "queue.jsonl"
    applied = tuning_dir / "applied.jsonl"
    append_suggestion(_make_suggestion(suggestion_id="feedback_real"), queue)

    result = move_suggestion("feedback_nonexistent", queue, applied)
    assert result is None
    # Source untouched.
    assert len(read_pending(queue)) == 1
    # Destination untouched.
    assert applied.read_text(encoding="utf-8") == ""


# ---------------------------------------------------------------------------
# 4. translate_feedback (mock delegate_task — no real LLM)
# ---------------------------------------------------------------------------


def _mock_delegate_factory(payload: dict):
    """Build a mock delegate_task whose 'summary' carries a JSON object."""

    def _mock(goal: str, context: str, toolsets: list[str]) -> dict:
        # Confirm the production call signature is honored.
        assert isinstance(goal, str) and goal
        assert toolsets == ["web"]
        return {"summary": json.dumps(payload, ensure_ascii=False)}

    return _mock


def test_translate_feedback_with_mock_delegate(tmp_path: Path) -> None:
    tuning_d = tmp_path / "tuning"
    init_queue(tuning_d)
    queue = tuning_d / "queue.jsonl"
    formula_dir = tmp_path / "formulas"  # doesn't exist → formula_id=None

    payload = {
        "formula_id": None,
        "suggested_action": "压缩前 3 秒铺垫，前置一个矛盾冲突",
        "rationale": "运营者指出 hook 节奏偏慢，观众在开头流失",
    }

    sug = translate_feedback(
        feedback_text="最近这批都市奇幻的 hook 太慢了，开头没矛盾，观众留不住",
        formula_library_dir=formula_dir,
        output_queue_path=queue,
        delegate_task=_mock_delegate_factory(payload),
    )

    # Returned object is well-formed.
    assert isinstance(sug, TuningSuggestion)
    assert sug.suggestion_id.startswith("feedback_")
    assert sug.trigger == "OPERATOR_FEEDBACK"
    assert sug.status == "pending"
    assert sug.formula_id is None
    assert sug.observed_metric is None
    assert sug.threshold is None
    assert "矛盾" in sug.suggested_action
    assert sug.evidence == [f"operator_feedback:{sug.suggestion_id}"]

    # It was actually written to the queue.
    pending = read_pending(queue)
    assert len(pending) == 1
    assert pending[0].suggestion_id == sug.suggestion_id


def test_translate_feedback_matches_formula(tmp_path: Path) -> None:
    """When the LLM pins a formula_id present in the library, it survives."""
    tuning_d = tmp_path / "tuning"
    init_queue(tuning_d)
    queue = tuning_d / "queue.jsonl"

    # Build a tiny formula library with one known formula.
    formula_dir = tmp_path / "formulas"
    formula_dir.mkdir()
    (formula_dir / "urban-fantasy-light-01.json").write_text(
        json.dumps(
            {
                "formula_id": "urban-fantasy-light-01",
                "genre": "都市奇幻",
                "mood": "轻喜剧",
                "pacing": "fast-cut",
                "keywords": ["都市奇幻", "轻喜剧"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = {
        "formula_id": "urban-fantasy-light-01",
        "suggested_action": "把 hook 从 contrast 升级到 emotional_peak",
        "rationale": "运营者反馈都市奇幻的 hook 不够强",
    }

    sug = translate_feedback(
        feedback_text="都市奇幻这集的 hook 不够抓人，前 3 秒太平",
        formula_library_dir=formula_dir,
        output_queue_path=queue,
        delegate_task=_mock_delegate_factory(payload),
    )

    assert sug.formula_id == "urban-fantasy-light-01"
    assert read_pending(queue)[0].formula_id == "urban-fantasy-light-01"


def test_translate_feedback_handles_fenced_json(tmp_path: Path) -> None:
    """LLM responses often wrap JSON in ``` fences — must still parse."""
    tuning_d = tmp_path / "tuning"
    init_queue(tuning_d)
    queue = tuning_d / "queue.jsonl"

    fenced_summary = (
        "好的，这是结构化建议：\n```json\n"
        '{"formula_id": null, "suggested_action": "加结尾 CTA", '
        '"rationale": "互动率低"}\n'
        "```\n"
    )

    def _mock(goal: str, context: str, toolsets: list[str]) -> dict:
        return {"summary": fenced_summary}

    sug = translate_feedback(
        feedback_text="看完不互动，缺 CTA",
        formula_library_dir=tmp_path / "noformulas",
        output_queue_path=queue,
        delegate_task=_mock,
    )
    assert sug.suggested_action == "加结尾 CTA"


def test_translate_feedback_nullish_formula_id_normalized(tmp_path: Path) -> None:
    """LLM returning 'null' / '' as formula_id must normalize to None."""
    tuning_d = tmp_path / "tuning"
    init_queue(tuning_d)
    queue = tuning_d / "queue.jsonl"

    for nullish in ("null", "None", ""):
        payload = {
            "formula_id": nullish,
            "suggested_action": "x",
            "rationale": "y",
        }
        sug = translate_feedback(
            feedback_text="irrelevant",
            formula_library_dir=tmp_path / "noformulas",
            output_queue_path=queue,
            delegate_task=_mock_delegate_factory(payload),
        )
        assert sug.formula_id is None, f"failed for nullish={nullish!r}"
