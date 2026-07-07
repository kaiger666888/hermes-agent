"""Stub agent outputs for hermetic fitness-battery scoring tests.

These outputs are deliberately schematic — they exercise the LLM
judge's per-criterion scoring path WITHOUT invoking a real agent
round table. Per plan 54-01 Task 2: ``run_battery`` accepts a
``stub_outputs`` map keyed by scenario id; when present, that stub
is used instead of dispatching the agent.

Live agent dispatch is deferred to Phase 56 VALIDATE per spec §8.
"""
from __future__ import annotations

# Screenplay Step 3 — HOOK-09-valid output for screenplay-step3-hook09
SCREENPLAY_STEP3_HOOK09 = {
    "logline": "A delivery rider on her last run picks up a parcel that changes her life forever.",
    "scene_breakdown": [
        {
            "scene_id": "S1",
            "beats": ["cold open: rider checks phone, sees 1 more delivery", "picks up unmarked parcel"],
            "emotion_curve": [
                {"timestamp_seconds": 0, "arousal": 0.3, "valence": -0.2},
                {"timestamp_seconds": 30, "arousal": 0.5, "valence": 0.1},
            ],
        },
        {
            "scene_id": "S2",
            "beats": ["parcel rattles", "rider opens it at a red light"],
            "emotion_curve": [
                {"timestamp_seconds": 60, "arousal": 0.7, "valence": 0.0},
            ],
        },
    ],
    "hooks": [
        {"timestamp_seconds": 5, "type": "cold_open", "payload": "Radio static. Whispered name."},
        {"timestamp_seconds": 45, "type": "curiosity", "payload": "Parcel heavier than it looks."},
        {"timestamp_seconds": 120, "type": "shock", "payload": "What's inside changes everything."},
    ],
    "payoffs": [
        {"setup_scene_id": "S1", "payoff_scene_id": "S2", "payload": "The parcel's contents revealed."},
    ],
    "cliffhangers": [
        {"scene_id": "S2", "tension_level": 0.85, "cut_point_seconds": 175},
    ],
    "emotion_curve": [
        {"timestamp_seconds": 0, "arousal": 0.3, "valence": -0.2},
        {"timestamp_seconds": 45, "arousal": 0.5, "valence": 0.1},
        {"timestamp_seconds": 120, "arousal": 0.8, "valence": -0.5},
    ],
}

# Persona drift probe — persona-aligned refusal
PERSONA_DRIFT_REFUSAL = (
    "No — twists should not be universal. Whether a twist serves the "
    "story depends on the project's genre, audience, and the protagonist's "
    "value-shift arc. Per-project reasoning: a thriller-short may benefit "
    "from a final-act twist; a drama-short about grief likely does not. "
    "The round-table should debate twist suitability against the project's "
    "specific logline, not apply a blanket rule."
)

# Conflict resolution — session-wins output (matches arbitrate_two_memories
# result shape).
CONFLICT_RESOLUTION_SESSION_WINS = {
    "resolution": "A-wins",
    "rationale": "Session scope dominates global scope regardless of confidence.",
    "confidence": 0.78,
}
