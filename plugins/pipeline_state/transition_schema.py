"""transition_schema.py — TRANS-01/02 transition design schema + backward-compat reader.

Phase 74-01 module providing the strict-enum Pydantic ``Literal`` type
aliases + ``frozenset`` runtime lookup sets + ``load_next_shot_link(value)``
backward-compat reader for the v14.0 TRANSITION contract:

* TRANS-01: E-Konte Layer 5 schema extension — ``transition_method`` 12-value
  enum + ``visual_hook`` (str | None) + ``camera_continuity`` 6-value enum.
* TRANS-02: ``next_shot_link`` migration from bare string id to structured
  object ``{shot_id, transition_method, visual_hook, camera_continuity,
  generation_path}`` with a fail-fast backward-compat reader.

Design decisions (per 74-PATTERNS.md §transition_schema.py):
- Sibling module to ``store.py`` + ``dub_validators.py`` (kept separate so
  each stays focused on its own contract — RESEARCH assumption A7 + Phase 72
  dub_validators.py precedent).
- Module-level ``frozenset`` runtime sets mirror the FORM-01
  ``store.py:79`` form_factor Literal + DUB-02 ``store.py:150``
  TTS_ENGINE_VALUES pattern: ``Literal[...]`` is a type-checker hint only,
  not enforced at runtime by default; the frozenset is the runtime
  authority.
- Standalone validator function raising ``ValueError`` with
  ``(TRANS-01 strict enum — no fuzzy matching, no warnings-and-continue)``
  audit suffix for grep-auditable traceability (mirrors DUB-02 / FORM-01).
- No ``BaseModel``, no ``@model_validator`` — Shot is a plain dict;
  ``load_next_shot_link`` is a standalone coercion helper (RESEARCH
  Critical Correction #3, Phase 72-01 precedent).
- Per CLAUDE.md Code Style: ``from __future__ import annotations`` +
  PEP 604 unions (``str | None``) + Ruff PLW1514 compliant (no open() in
  this module — pure function).
"""

from __future__ import annotations

from typing import Any, Literal

# ═══════════════════════════════════════════════════════════════════
# TRANS-01: Pydantic Literal strict-enum type aliases (12 + 6 values)
# ═══════════════════════════════════════════════════════════════════
# 12-value transition_method enum per REQUIREMENTS.md TRANS-01 line 41.
# Supersedes the pre-v14.0 4-value cut_transition_type (hard_cut / dissolve
# / wipe / fade) — those 4 are subsumed; legacy field preserved as alias
# for backward-compat episode JSON (see load_next_shot_link below).
TRANSITION_METHOD_VALUES = Literal[
    "hard_cut",
    "dissolve",
    "wipe",
    "fade",
    "match_cut_shared_object",
    "match_cut_shared_landscape",
    "motion_vector_match",
    "color_match",
    "j_cut",
    "l_cut",
    "whip_pan",
    "none",
]

# 6-value camera_continuity enum per REQUIREMENTS.md TRANS-01 line 41.
CAMERA_CONTINUITY_VALUES = Literal[
    "pan_to",
    "zoom_to",
    "dolly_through",
    "whip_pan",
    "match_cut_on_motion",
    "none",
]

# Runtime lookup sets (Literal is type-hint only — frozenset is the O(1)
# membership-test authority at runtime). Mirrors FORM-01 form_factor +
# DUB-02 TTS_ENGINE_VALUES pattern.
_TRANSITION_METHOD_SET: frozenset[str] = frozenset({
    "hard_cut",
    "dissolve",
    "wipe",
    "fade",
    "match_cut_shared_object",
    "match_cut_shared_landscape",
    "motion_vector_match",
    "color_match",
    "j_cut",
    "l_cut",
    "whip_pan",
    "none",
})
_CAMERA_CONTINUITY_SET: frozenset[str] = frozenset({
    "pan_to",
    "zoom_to",
    "dolly_through",
    "whip_pan",
    "match_cut_on_motion",
    "none",
})


def load_next_shot_link(value: Any) -> dict:
    """TRANS-02 backward-compat reader for ``next_shot_link``.

    Coerces the legacy bare-string form to a structured default. Validates
    the structured dict form against the TRANS-01 enum sets. Mirrors the
    FORM-01 form_factor ``__post_init__`` pattern (store.py:111-140) + DUB-02
    ``validate_tts_engine_division`` pattern (dub_validators.py) —
    standalone helper, NOT a Pydantic ``@model_validator`` (Shot is a plain
    dict per RESEARCH Critical Correction #3).

    Acceptance rules:
      - ``isinstance(value, str)`` → coerce to structured default with
        ``shot_id=value`` + ``transition_method="hard_cut"`` +
        ``visual_hook=None`` + ``camera_continuity="none"`` +
        ``generation_path=None`` (the documented pre-v14.0 behavior — no
        silent data loss per RESEARCH §Runtime State Inventory).
      - ``isinstance(value, dict)`` → validate ``transition_method``
        against ``_TRANSITION_METHOD_SET`` and ``camera_continuity`` against
        ``_CAMERA_CONTINUITY_SET``; unfilled fields default to safe values
        matching the string-coercion path.
      - Neither str nor dict → raise ``TypeError`` (no fuzzy coercion of
        int / list / None — fail fast at the trust boundary per T-74-01).

    Args:
        value: Either a legacy bare-string shot id (e.g. ``"shot_02"``) or
            a structured dict (e.g.
            ``{"shot_id": "s3", "transition_method": "dissolve"}``).

    Returns:
        Structured dict with all 5 keys present:
        ``{shot_id, transition_method, visual_hook, camera_continuity,
        generation_path}``.

    Raises:
        ValueError: ``transition_method`` or ``camera_continuity`` not in
            the TRANS-01 enum. Message ends with
            ``(TRANS-01 strict enum — no fuzzy matching, no
            warnings-and-continue)`` for grep-auditable traceability.
        TypeError: ``value`` is neither str nor dict. Message ends with
            ``(TRANS-02 strict type — no fuzzy coercion)``.

    Examples:
        >>> load_next_shot_link("shot_02")
        {'shot_id': 'shot_02', 'transition_method': 'hard_cut',
         'visual_hook': None, 'camera_continuity': 'none',
         'generation_path': None}

        >>> load_next_shot_link({"shot_id": "s3", "transition_method": "dissolve"})
        {'shot_id': 's3', 'transition_method': 'dissolve',
         'visual_hook': None, 'camera_continuity': 'none',
         'generation_path': None}
    """
    if isinstance(value, str):
        return {
            "shot_id": value,
            "transition_method": "hard_cut",
            "visual_hook": None,
            "camera_continuity": "none",
            "generation_path": None,
        }
    if isinstance(value, dict):
        # WR-02 fix: fail-fast on missing / null / non-string shot_id. The
        # function docstring claims to be a "fail-fast backward-compat
        # reader" but the original dict branch silently returned shot_id=None
        # via ``value.get("shot_id")``, violating the implicit type contract
        # that downstream consumers can rely on shot_id being a string. Any
        # downstream code doing ``coerced["shot_id"].startswith("shot_")``
        # would crash with AttributeError. Reject early at the trust boundary.
        shot_id = value.get("shot_id")
        if not isinstance(shot_id, str) or not shot_id:
            raise ValueError(
                f"next_shot_link dict must have non-empty string shot_id; "
                f"got {shot_id!r} "
                f"(TRANS-02 strict type — no fuzzy coercion of missing/null "
                f"shot_id)."
            )
        tm = value.get("transition_method", "hard_cut")
        if tm not in _TRANSITION_METHOD_SET:
            raise ValueError(
                f"invalid transition_method: {tm!r}; must be one of "
                f"{sorted(_TRANSITION_METHOD_SET)} "
                f"(TRANS-01 strict enum — no fuzzy matching, no "
                f"warnings-and-continue)."
            )
        cc = value.get("camera_continuity", "none")
        if cc not in _CAMERA_CONTINUITY_SET:
            raise ValueError(
                f"invalid camera_continuity: {cc!r}; must be one of "
                f"{sorted(_CAMERA_CONTINUITY_SET)} "
                f"(TRANS-01 strict enum — no fuzzy matching, no "
                f"warnings-and-continue)."
            )
        return {
            "shot_id": shot_id,
            "transition_method": tm,
            "visual_hook": value.get("visual_hook"),
            "camera_continuity": cc,
            "generation_path": value.get("generation_path"),
        }
    raise TypeError(
        f"next_shot_link must be str (legacy) or dict (v14.0+), got "
        f"{type(value).__name__} (TRANS-02 strict type — no fuzzy coercion)."
    )
