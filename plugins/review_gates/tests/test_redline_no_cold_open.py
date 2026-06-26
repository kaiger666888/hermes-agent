"""test_redline_no_cold_open.py — Phase 40-01 R3 detector behavior.

Covers the R3 zero-backstory-preamble detector
(``plugins.review_gates.gates.redline_no_cold_open.detect``):

- Test 5 (positive): beats[0].label == "exposition" -> reject.
- Test 6 (positive): beats[0].label == "narration" -> reject.
- Test 7 (positive): beats[0].label == "setup" -> reject.
- Test 8 (negative): beats[0].label == "active_conflict" -> approve.
- Test 9 (edge): empty beats -> approve.
- Test 17 (structural): reject-branch action matches ^formula:[a-z][a-z0-9-]*$.
- Test 18 (determinism): same payload twice -> identical result.
"""

from __future__ import annotations

import re

import pytest

from plugins.review_gates.gates.redline_no_cold_open import (
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


class TestRedlineNoColdOpenIdentity:
    def test_gate_id_matches_yaml_gate_id(self) -> None:
        assert GATE_ID == "redline_no_cold_open"

    def test_redline_ref_cites_r3_section(self) -> None:
        assert "§R3" in REDLINE_REF
        assert "creative-redlines" in REDLINE_REF


# ---------------------------------------------------------------------------
# Tests 5-7: positive — first beat labeled exposition / narration / setup
# ---------------------------------------------------------------------------


class TestRedlineNoColdOpenPositive:
    @pytest.mark.parametrize("bad_label", ["exposition", "narration", "setup"])
    def test_first_beat_preamble_label_rejects(self, bad_label: str) -> None:
        """Tests 5/6/7 — R3 violation: first beat is preamble-type.

        Per creative-redlines.md §R3: first beat must be active conflict;
        exposition / narration / setup labels trigger R3 violation.
        """
        payload = {
            "episode_id": "EP_R3_POS",
            "beats": [
                _beat(0, label=bad_label),
                _beat(1, label="active_conflict"),
                _beat(2, label="active_conflict"),
            ],
            "platform": "douyin_vertical",
            "runtime_sec": 6.0,
        }
        decision, action = detect(payload)
        assert decision == "reject", (
            f"first beat label={bad_label!r} must trigger R3 reject"
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
# Test 8: negative — first beat labeled active_conflict -> approve
# ---------------------------------------------------------------------------


class TestRedlineNoColdOpenNegative:
    @pytest.mark.parametrize("good_label", ["active_conflict", "other", "cliffhanger"])
    def test_first_beat_non_preamble_label_approves(self, good_label: str) -> None:
        """Test 8 — R3 compliant: first beat is NOT a preamble label.

        Only exposition / narration / setup are violations; any other
        label (active_conflict, other, cliffhanger, ...) approves.
        """
        payload = {
            "episode_id": "EP_R3_NEG",
            "beats": [
                _beat(0, label=good_label),
                _beat(1, label="active_conflict"),
            ],
        }
        decision, action = detect(payload)
        assert decision == "approve"
        assert action is None


# ---------------------------------------------------------------------------
# Test 9: edge — empty beats -> approve (defensive)
# ---------------------------------------------------------------------------


class TestRedlineNoColdOpenEdge:
    def test_empty_beats_approves(self) -> None:
        """Test 9 — defensive: no beats means no first beat, no violation."""
        payload = {"episode_id": "EP_R3_EMPTY", "beats": []}
        decision, action = detect(payload)
        assert decision == "approve"
        assert action is None

    def test_missing_beats_key_approves(self) -> None:
        """T-40-01 hardening: missing "beats" key -> defensive approve."""
        payload = {"episode_id": "EP_R3_NOBEATS"}  # no beats key
        decision, action = detect(payload)
        assert decision == "approve"
        assert action is None

    def test_beat_missing_label_key_is_safe(self) -> None:
        """T-40-01 hardening: first beat missing "label" must not crash.

        ``beats[0].get("label")`` returns None, which is not in the
        violation set -> approve. No KeyError raised.
        """
        payload = {
            "episode_id": "EP_R3_NOLABEL",
            "beats": [
                {"index": 0},  # no label key
                {"index": 1, "label": "active_conflict"},
            ],
        }
        decision, action = detect(payload)
        assert decision == "approve"
        assert action is None

    def test_single_beat_preamble_rejects(self) -> None:
        """Single-beat clip with preamble label still rejects (no length gate)."""
        payload = {
            "episode_id": "EP_R3_SINGLE",
            "beats": [_beat(0, label="exposition")],
        }
        decision, action = detect(payload)
        assert decision == "reject"
        assert action is not None and action.startswith("formula:")


# ---------------------------------------------------------------------------
# Test 18: determinism
# ---------------------------------------------------------------------------


class TestRedlineNoColdOpenDeterminism:
    def test_repeated_call_returns_identical_result_positive(self) -> None:
        payload = {
            "episode_id": "EP_R3_DETERM_POS",
            "beats": [_beat(0, label="exposition"), _beat(1, label="active_conflict")],
        }
        assert detect(payload) == detect(payload)

    def test_repeated_call_returns_identical_result_negative(self) -> None:
        payload = {
            "episode_id": "EP_R3_DETERM_NEG",
            "beats": [_beat(0, label="active_conflict")],
        }
        assert detect(payload) == detect(payload)
