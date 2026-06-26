"""test_redline_unfinished_ending.py — Phase 40-01 R4 detector behavior.

Covers the R4 unresolved-ending detector
(``plugins.review_gates.gates.redline_unfinished_ending.detect``):

- Test 10 (positive): beats[-1].label == "resolution" -> reject.
- Test 11 (positive): beats[-1].label == "closure" -> reject.
- Test 12 (positive): beats[-1].label == "epilogue" -> reject.
- Test 13 (negative): beats[-1].label == "open_question" / "cliffhanger" -> approve.
- Test 14 (edge): empty beats -> approve.
- Test 17 (structural): reject-branch action matches ^formula:[a-z][a-z0-9-]*$.
- Test 18 (determinism): same payload twice -> identical result.
"""

from __future__ import annotations

import re

import pytest

from plugins.review_gates.gates.redline_unfinished_ending import (
    GATE_ID,
    REDLINE_REF,
    detect,
)

_FORMULA_RE = re.compile(r"^formula:[a-z][a-z0-9-]*$")


def _beat(index: int, *, label: str, emotion: str = "anger",
          duration_sec: float = 2.0, text: str = "") -> dict:
    return {
        "index": index,
        "label": label,
        "emotion": emotion,
        "duration_sec": duration_sec,
        "text": text,
    }


# ---------------------------------------------------------------------------
# Module identity
# ---------------------------------------------------------------------------


class TestRedlineUnfinishedEndingIdentity:
    def test_gate_id_matches_yaml_gate_id(self) -> None:
        assert GATE_ID == "redline_unfinished_ending"

    def test_redline_ref_cites_r4_section(self) -> None:
        assert "§R4" in REDLINE_REF
        assert "creative-redlines" in REDLINE_REF


# ---------------------------------------------------------------------------
# Tests 10-12: positive — last beat labeled resolution / closure / epilogue
# ---------------------------------------------------------------------------


class TestRedlineUnfinishedEndingPositive:
    @pytest.mark.parametrize("bad_label", ["resolution", "closure", "epilogue"])
    def test_last_beat_closure_label_rejects(self, bad_label: str) -> None:
        """Tests 10/11/12 — R4 violation: last beat is closure-type.

        Per creative-redlines.md §R4: last beat must release a new hook,
        not a tidy closure. resolution / closure / epilogue labels
        trigger R4 violation.
        """
        payload = {
            "episode_id": "EP_R4_POS",
            "beats": [
                _beat(0, label="active_conflict"),
                _beat(1, label="active_conflict"),
                _beat(2, label=bad_label),  # LAST beat is closure-type
            ],
            "platform": "douyin_vertical",
            "runtime_sec": 6.0,
        }
        decision, action = detect(payload)
        assert decision == "reject", (
            f"last beat label={bad_label!r} must trigger R4 reject"
        )
        assert action is not None
        assert action.startswith("formula:"), (
            f"suggested_action must start with 'formula:' (GATE-04 #4); got {action!r}"
        )
        # Test 17 structural half
        assert _FORMULA_RE.match(action), (
            f"suggested_action {action!r} does not match ^formula:[a-z][a-z0-9-]*$"
        )


# ---------------------------------------------------------------------------
# Test 13: negative — last beat labeled open_question / cliffhanger -> approve
# ---------------------------------------------------------------------------


class TestRedlineUnfinishedEndingNegative:
    @pytest.mark.parametrize(
        "good_label", ["open_question", "cliffhanger", "active_conflict", "other"]
    )
    def test_last_beat_non_closure_label_approves(self, good_label: str) -> None:
        """Test 13 — R4 compliant: last beat releases a hook (not closure).

        Only resolution / closure / epilogue are violations; any other
        label approves.
        """
        payload = {
            "episode_id": "EP_R4_NEG",
            "beats": [
                _beat(0, label="active_conflict"),
                _beat(1, label=good_label),  # LAST beat — hook, not closure
            ],
        }
        decision, action = detect(payload)
        assert decision == "approve"
        assert action is None

    def test_only_last_beat_matters(self) -> None:
        """R4 checks beats[-1] only — earlier closure beats are fine."""
        payload = {
            "episode_id": "EP_R4_MID",
            "beats": [
                _beat(0, label="closure"),  # closure in the middle — OK
                _beat(1, label="active_conflict"),
                _beat(2, label="open_question"),  # last beat is a hook
            ],
        }
        decision, action = detect(payload)
        assert decision == "approve"
        assert action is None


# ---------------------------------------------------------------------------
# Test 14: edge — empty beats -> approve (defensive)
# ---------------------------------------------------------------------------


class TestRedlineUnfinishedEndingEdge:
    def test_empty_beats_approves(self) -> None:
        """Test 14 — defensive: no beats means no last beat, no violation."""
        payload = {"episode_id": "EP_R4_EMPTY", "beats": []}
        decision, action = detect(payload)
        assert decision == "approve"
        assert action is None

    def test_missing_beats_key_approves(self) -> None:
        """T-40-01 hardening: missing "beats" key -> defensive approve."""
        payload = {"episode_id": "EP_R4_NOBEATS"}  # no beats key
        decision, action = detect(payload)
        assert decision == "approve"
        assert action is None

    def test_last_beat_missing_label_key_is_safe(self) -> None:
        """T-40-01 hardening: last beat missing "label" must not crash."""
        payload = {
            "episode_id": "EP_R4_NOLABEL",
            "beats": [
                {"index": 0, "label": "active_conflict"},
                {"index": 1},  # no label key
            ],
        }
        decision, action = detect(payload)
        assert decision == "approve"
        assert action is None

    def test_single_beat_closure_rejects(self) -> None:
        """Single-beat clip with closure label still rejects."""
        payload = {
            "episode_id": "EP_R4_SINGLE",
            "beats": [_beat(0, label="resolution")],
        }
        decision, action = detect(payload)
        assert decision == "reject"
        assert action is not None and action.startswith("formula:")


# ---------------------------------------------------------------------------
# Test 18: determinism
# ---------------------------------------------------------------------------


class TestRedlineUnfinishedEndingDeterminism:
    def test_repeated_call_returns_identical_result_positive(self) -> None:
        payload = {
            "episode_id": "EP_R4_DETERM_POS",
            "beats": [_beat(0, label="active_conflict"), _beat(1, label="epilogue")],
        }
        assert detect(payload) == detect(payload)

    def test_repeated_call_returns_identical_result_negative(self) -> None:
        payload = {
            "episode_id": "EP_R4_DETERM_NEG",
            "beats": [_beat(0, label="cliffhanger")],
        }
        assert detect(payload) == detect(payload)
