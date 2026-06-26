"""test_redline_emotion_desensitize.py — Phase 40-01 R1 detector behavior.

Covers the R1 emotion-desensitization detector
(``plugins.review_gates.gates.redline_emotion_desensitize.detect``):

- Test 1 (positive): 3 consecutive same-emotion beats -> reject + formula: action.
- Test 2 (negative): 2 same + 1 different -> approve.
- Test 3 (edge): exactly 2 same consecutive -> approve (R1 spec: ≤2 OK).
- Test 4 (edge): empty beats -> approve (defensive).
- Test 17 (structural): reject-branch action matches ^formula:[a-z][a-z0-9-]*$.
- Test 18 (determinism): same payload twice -> identical result (pure fn).

All payloads use the shape from Plan 40-01 <interfaces>:
``{"episode_id": str, "beats": [{"index": int, "label": str, "emotion":
str, "duration_sec": float, "text": str}], ...}``.
"""

from __future__ import annotations

import re

import pytest

from plugins.review_gates.gates.redline_emotion_desensitize import (
    GATE_ID,
    REDLINE_REF,
    detect,
)

_FORMULA_RE = re.compile(r"^formula:[a-z][a-z0-9-]*$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _beat(index: int, *, label: str = "active_conflict", emotion: str = "anger",
          duration_sec: float = 2.0, text: str = "") -> dict:
    """Build a single beat dict matching the Plan 40-01 payload shape."""
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


class TestRedlineEmotionDesensitizeIdentity:
    def test_gate_id_matches_yaml_gate_id(self) -> None:
        assert GATE_ID == "redline_emotion_desensitize"

    def test_redline_ref_cites_r1_section(self) -> None:
        assert "§R1" in REDLINE_REF
        assert "creative-redlines" in REDLINE_REF


# ---------------------------------------------------------------------------
# Test 1: positive — 3 consecutive same-emotion beats -> reject
# ---------------------------------------------------------------------------


class TestRedlineEmotionDesensitizePositive:
    def test_three_consecutive_same_emotion_beats_reject(self) -> None:
        """Test 1 — R1 violation: 3 consecutive "anger" beats.

        Per creative-redlines.md §R1: "第 3 个连续同类型即触发脱敏".
        Detector must return ("reject", action) where action starts
        with "formula:" (Phase 39 formula_library read-side lookup).
        """
        payload = {
            "episode_id": "EP01",
            "beats": [
                _beat(0, emotion="anger"),
                _beat(1, emotion="anger"),
                _beat(2, emotion="anger"),
            ],
            "platform": "douyin_vertical",
            "runtime_sec": 6.0,
        }
        decision, action = detect(payload)
        assert decision == "reject"
        assert action is not None
        assert action.startswith("formula:"), (
            f"suggested_action must start with 'formula:' (GATE-04 #4); got {action!r}"
        )
        # Test 17 structural half: regex match
        assert _FORMULA_RE.match(action), (
            f"suggested_action {action!r} does not match ^formula:[a-z][a-z0-9-]*$"
        )

    def test_three_consecutive_same_emotion_any_taxonomy(self) -> None:
        """R1 fires on ANY emotion taxonomy, not just "anger"."""
        payload = {
            "episode_id": "EP02",
            "beats": [
                _beat(0, emotion="sadness"),
                _beat(1, emotion="sadness"),
                _beat(2, emotion="sadness"),
            ],
        }
        decision, action = detect(payload)
        assert decision == "reject"
        assert action is not None and action.startswith("formula:")

    def test_violation_anywhere_in_sequence_rejects(self) -> None:
        """The 3-consecutive run can appear anywhere — not just at start."""
        payload = {
            "episode_id": "EP03",
            "beats": [
                _beat(0, emotion="shock"),
                _beat(1, emotion="joy"),
                _beat(2, emotion="anger"),
                _beat(3, emotion="anger"),
                _beat(4, emotion="anger"),  # 3rd consecutive anger
                _beat(5, emotion="relief"),
            ],
        }
        decision, action = detect(payload)
        assert decision == "reject"
        assert action is not None and action.startswith("formula:")


# ---------------------------------------------------------------------------
# Test 2: negative — mixed emotions -> approve
# ---------------------------------------------------------------------------


class TestRedlineEmotionDesensitizeNegative:
    def test_two_same_then_one_different_approves(self) -> None:
        """Test 2 — R1 compliant: 2 anger + 1 shock -> no desensitization."""
        payload = {
            "episode_id": "EP04",
            "beats": [
                _beat(0, emotion="anger"),
                _beat(1, emotion="anger"),
                _beat(2, emotion="shock"),  # different — breaks the run
            ],
        }
        decision, action = detect(payload)
        assert decision == "approve"
        assert action is None


# ---------------------------------------------------------------------------
# Test 3: edge — exactly 2 consecutive same -> approve (boundary)
# ---------------------------------------------------------------------------


class TestRedlineEmotionDesensitizeEdge:
    def test_exactly_two_consecutive_same_approves(self) -> None:
        """Test 3 — boundary: ≤2 consecutive is OK (R1 spec: 第 3 个 triggers).

        This pins the off-by-one boundary: the 3rd consecutive beat is
        the trigger, not the 2nd.
        """
        payload = {
            "episode_id": "EP05",
            "beats": [
                _beat(0, emotion="anger"),
                _beat(1, emotion="anger"),
            ],
        }
        decision, action = detect(payload)
        assert decision == "approve"
        assert action is None

    # -----------------------------------------------------------------------
    # Test 4: edge — empty beats -> approve (defensive, T-40-01 mitigation)
    # -----------------------------------------------------------------------

    def test_empty_beats_approves(self) -> None:
        """Test 4 — defensive: no beats means no violation (T-40-01)."""
        payload = {"episode_id": "EP06", "beats": []}
        decision, action = detect(payload)
        assert decision == "approve"
        assert action is None

    def test_missing_beats_key_approves(self) -> None:
        """T-40-01 hardening: missing "beats" key -> defensive approve.

        Detectors MUST NOT raise KeyError on malformed payloads; missing
        keys fall through to ("approve", None).
        """
        payload = {"episode_id": "EP07"}  # no "beats" key
        decision, action = detect(payload)
        assert decision == "approve"
        assert action is None

    def test_beats_missing_emotion_key_is_safe(self) -> None:
        """T-40-01 hardening: a beat missing "emotion" must not crash.

        Such beats contribute None to the run-comparison; two Nones are
        treated as same (which is conservative — the upstream pipeline
        should always emit emotion, but if it doesn't, the detector
        degrades safely without raising).
        """
        payload = {
            "episode_id": "EP08",
            "beats": [
                {"index": 0, "label": "active_conflict"},  # no emotion
                {"index": 1, "label": "active_conflict"},  # no emotion
                {"index": 2, "label": "active_conflict"},  # no emotion
            ],
        }
        # Must not raise — either approves (None != str) or rejects
        # (None == None); the contract is "doesn't crash". Either
        # outcome is acceptable; we assert only no-exception.
        decision, action = detect(payload)
        assert decision in {"approve", "reject"}


# ---------------------------------------------------------------------------
# Test 18: determinism — same payload twice -> identical result
# ---------------------------------------------------------------------------


class TestRedlineEmotionDesensitizeDeterminism:
    def test_repeated_call_returns_identical_result_positive(self) -> None:
        """Test 18 — pure function: detect(p) == detect(p) for violating payload."""
        payload = {
            "episode_id": "EP09",
            "beats": [_beat(i, emotion="anger") for i in range(3)],
        }
        r1 = detect(payload)
        r2 = detect(payload)
        assert r1 == r2

    def test_repeated_call_returns_identical_result_negative(self) -> None:
        """Test 18 — pure function: detect(p) == detect(p) for clean payload."""
        payload = {
            "episode_id": "EP10",
            "beats": [
                _beat(0, emotion="anger"),
                _beat(1, emotion="shock"),
            ],
        }
        r1 = detect(payload)
        r2 = detect(payload)
        assert r1 == r2
