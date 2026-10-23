"""test_canvas_sync_field_map.py — Phase 74 WR-01 regression guard for the
canvas_sync data-driven field-map refactor.

The pre-v14.0 handwritten ``_apply_schema_mappings`` was refactored to a
data-driven dispatch over the generated ``canvas_sync_mappings.PHASE_FIELDS``
table. The refactor's correctness depends on the generated table preserving
the old handwritten field coverage for every phase prefix — especially the
p10/p10b/p11 structured fields (audioType / engine / emotion / speaker /
murchGrade / resolution / duration).

WR-01 flagged that no test in the reviewed scope exercised the refactor
end-to-end against the generated PHASE_FIELDS table. The handwritten →
generated handoff was a silent dependency: if a YAML edit dropped the p10
or p11 entry, the refactor would silently regress (degrade-tolerant no-op
at line 380 when ``_MAPPINGS is None``, and silent field-skip when
``PHASE_FIELDS[lookup_prefix]`` is empty at line 392).

This module adds three regression assertions:

1. ``test_phase_fields_table_covers_p10_and_p11`` — the generated
   PHASE_FIELDS table contains ``p10`` and ``p11`` entries with at least
   the structured fields the old handwritten code emitted. Catches a YAML
   regression that drops either entry.
2. ``test_apply_schema_mappings_emits_p10_structured_fields`` — calling
   ``_apply_schema_mappings`` with a p10 artifact dict actually emits the
   4 structured fields (audioType / emotion / engine / speaker). Catches a
   refactor bug in the per-field dispatch loop.
3. ``test_apply_schema_mappings_p10b_inherits_p10_mapping`` — p10b (the
   rapid-preview micro-gate phase) inherits the p10 field mapping via the
   ``lookup_prefix in ("p10b", "p10c")`` alias branch.

Test environment note: ``canvas_sync._MAPPINGS`` is loaded from the real
generated file at ``/data/workspace/kais-aigc-platform/schema/generated/
canvas_sync_mappings.py``. If the file is absent the module-level
``_MAPPINGS`` is ``None`` and ``_apply_schema_mappings`` is a no-op —
those tests will be skipped via the ``skipIf`` guard below.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))

from plugins.kais_aigc import canvas_sync  # noqa: E402
from plugins.kais_aigc.canvas_sync import _apply_schema_mappings  # noqa: E402


# ─── skip guard: if the generated mappings file is absent, the refactor's
# behavior cannot be tested end-to-end (the dispatch becomes a no-op). The
# p10/p11 assertions would spuriously fail in such an environment. ──────
_MAPPINGS_AVAILABLE = canvas_sync._MAPPINGS is not None
pytestmark = pytest.mark.skipif(
    not _MAPPINGS_AVAILABLE,
    reason="canvas_sync_mappings.py not generated — _apply_schema_mappings is a no-op",
)


# ─── p10 / p11 field coverage regression ─────────────────────────────


# The structured fields the pre-refactor handwritten code emitted for p10.
# If the generated PHASE_FIELDS[p10] omits any of these, a regression has
# silently dropped coverage. Keys are canvas_key (destination) — these are
# what the old _SNAKE_CAMEL map produced.
_REQUIRED_P10_CANVAS_KEYS = {"audioType", "engine", "emotion", "speaker"}
_REQUIRED_P11_CANVAS_KEYS = {"engine", "resolution"}


def test_phase_fields_table_covers_p10_and_p11():
    """WR-01: generated PHASE_FIELDS preserves p10/p11 structured coverage.

    Validates that the data-driven refactor did not drop the field entries
    that the old handwritten ``_apply_schema_mappings`` emitted for p10
    (audioType / engine / emotion / speaker) and p11 (engine / resolution).
    A YAML regression that removes either phase entry would silently
    degrade canvas sync to missing structured fields.
    """
    p10 = canvas_sync._MAPPINGS.PHASE_FIELDS.get("p10", {})
    p11 = canvas_sync._MAPPINGS.PHASE_FIELDS.get("p11", {})

    p10_canvas_keys = {fdef.get("canvas_key") for fdef in p10.values()}
    p11_canvas_keys = {fdef.get("canvas_key") for fdef in p11.values()}

    missing_p10 = _REQUIRED_P10_CANVAS_KEYS - p10_canvas_keys
    assert not missing_p10, (
        f"PHASE_FIELDS[p10] is missing structured canvas_keys that the "
        f"old handwritten code emitted: {sorted(missing_p10)}. "
        f"Got: {sorted(p10_canvas_keys)}. "
        f"Check pipeline-field-map.yaml p10 entry."
    )
    missing_p11 = _REQUIRED_P11_CANVAS_KEYS - p11_canvas_keys
    assert not missing_p11, (
        f"PHASE_FIELDS[p11] is missing structured canvas_keys that the "
        f"old handwritten code emitted: {sorted(missing_p11)}. "
        f"Got: {sorted(p11_canvas_keys)}. "
        f"Check pipeline-field-map.yaml p11 entry."
    )


def test_apply_schema_mappings_emits_p10_structured_fields():
    """WR-01: _apply_schema_mappings actually emits p10 structured fields.

    Validates the per-field dispatch loop in _apply_schema_mappings works
    end-to-end: given a p10 artifact with audio_type / emotion / engine /
    speaker values, the function mutates ``data`` to include the camelCase
    canvas_keys. This catches refactor bugs in the dispatch logic that
    PHASE_FIELDS coverage alone would miss.
    """
    data: dict = {}
    artifact = {
        "audio_type": "narration",
        "emotion": "tense",
        "engine": "ltx",
        "speaker": "narrator",
    }
    _apply_schema_mappings(data, "p10", artifact)
    for ckey in _REQUIRED_P10_CANVAS_KEYS:
        assert ckey in data, (
            f"_apply_schema_mappings did not emit {ckey!r} for p10 artifact; "
            f"got data keys={sorted(data.keys())}"
        )


def test_apply_schema_mappings_p10b_inherits_p10_mapping():
    """WR-01: p10b micro-gate inherits p10 field mapping.

    The alias branch at canvas_sync.py:388 maps ``p10b`` → ``p10`` so the
    rapid-preview phase inherits the audio structured fields. This test
    guards against a regression that removes the alias (p10b clips would
    silently lose audioType / engine / emotion / speaker).
    """
    data: dict = {}
    artifact = {
        "audio_type": "narration",
        "emotion": "tense",
        "engine": "ltx",
        "speaker": "narrator",
    }
    _apply_schema_mappings(data, "p10b", artifact)
    # p10b should emit the same structured fields as p10.
    for ckey in _REQUIRED_P10_CANVAS_KEYS:
        assert ckey in data, (
            f"_apply_schema_mappings did not emit {ckey!r} for p10b artifact "
            f"(p10b→p10 alias regression); got data keys={sorted(data.keys())}"
        )


def test_apply_schema_mappings_emits_p11_structured_fields():
    """WR-01: _apply_schema_mappings emits p11 structured fields.

    p11 fields include engine / resolution (always-set with defaults) plus
    murch_grade + duration. This test verifies the always-set branches at
    canvas_sync.py:437-447 still fire for p11.
    """
    data: dict = {}
    artifact = {
        "duration_sec": 3.5,
        "engine": "ltx",
        "resolution": "1080x1920",
        "murch_grade": 5,
    }
    _apply_schema_mappings(data, "p11", artifact)
    for ckey in _REQUIRED_P11_CANVAS_KEYS:
        assert ckey in data, (
            f"_apply_schema_mappings did not emit {ckey!r} for p11 artifact; "
            f"got data keys={sorted(data.keys())}"
        )
