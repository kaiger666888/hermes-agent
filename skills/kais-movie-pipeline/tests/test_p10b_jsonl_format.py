"""test_p10b_jsonl_format.py — Phase 40-04 Task 2: rapid-preview-clips JSONL format.

RAPID-PREVIEW-04 + RAPID-PREVIEW-07c contract verification:

  - file extension is .jsonl
  - one JSON object per non-blank line
  - 6 required fields present: shot_id, variant_id, structure_delta,
    clip_path, generation_time_ms, engine
  - field types correct (generation_time_ms strictly int, NOT float)
  - engine value domain {"slideshow", "ltx"}
  - structure_delta is single-key with valid param name (Notion 红线 #6)
  - variant_id naming follows "{shot_id}__v{N}_{param_name}" pattern
  - append semantics preserve insertion order (no reorder/dedup)
  - empty slot reads as []
  - p10b output integration: real run produces records matching the contract

BLOCKER #4 (Test 11): 4-shot fixture cycling matrix coverage —
turning_points_sec MUST appear in >=1 variant across the episode
(proves the cycling matrix from plan 03 covers all 4 params at the
JSONL file level, not just the unit-test level).

Imports both AssetBus (from plugins.pipeline_state) AND p10b_rapid_preview
(from pipeline.phases). Uses the sys.path manipulation pattern from
test_p11_unit.py to make both importable. The integration tests create a
real AssetBus(tmp_path), wrap its read/write methods as the callables
passed to p10b.run(), runs p10b, then re-opens AssetBus(tmp_path) to read
what was written (simulating a fresh process reading the same files).
"""

from __future__ import annotations

import json
import re
import sys
import threading
from pathlib import Path

import pytest

# Make the skill-local ``pipeline`` package importable (mirror test_p11_unit).
_SKILL_DIR = Path(__file__).resolve().parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from pipeline.phases import p10b_rapid_preview as p10b  # noqa: E402
from plugins.kais_aigc.preview_engine import PreviewEngine  # noqa: E402
from plugins.pipeline_state.asset_bus import ASSET_SCHEMA, AssetBus  # noqa: E402


# ---------------------------------------------------------------------------
# Constants — the format contract
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = {
    "shot_id": str,
    "variant_id": str,
    "structure_delta": dict,
    "clip_path": str,
    "generation_time_ms": int,
    "engine": str,
}
VALID_ENGINE_VALUES = {"slideshow", "ltx"}
VALID_DELTA_KEYS = {
    "hook_position_sec",
    "emotion_sequence",
    "turning_points_sec",
    "ending_state",
}

#: variant_id pattern: {shot_id}__v{N}_{param_name}
#: - shot_id: any non-empty string (test uses "shot_001" etc.)
#: - N: 1-based position within the shot (1, 2, or 3)
#: - param_name: one of VALID_DELTA_KEYS
VARIANT_ID_PATTERN = re.compile(
    r"^(?P<shot_id>.+)__v(?P<position>[1-3])_(?P<param_name>" +
    "|".join(re.escape(k) for k in VALID_DELTA_KEYS) +
    r")$"
)


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class _RecordingEngine(PreviewEngine):
    """PreviewEngine test double that always succeeds.

    Returns the engine tag passed at construction (so the same engine can
    exercise both slideshow and ltx paths in different tests).
    """

    def __init__(self, *, engine_tag: str = "slideshow"):
        self._engine_tag = engine_tag

    def generate(
        self,
        *,
        shot_id: str,
        prompt: str,
        structure_delta: dict,
        keyframe_image_path: str | None = None,
        voice_clip_path: str | None = None,
        output_path: str | None = None,
    ) -> dict:
        return {
            "clip_path": output_path or f"/preview/{shot_id}.mp4",
            "generation_time_ms": 1234,
            "engine": self._engine_tag,
        }


# ---------------------------------------------------------------------------
# Fixtures — minimal input data
# ---------------------------------------------------------------------------


def _voice_clips(n_shots: int) -> list[dict]:
    return [
        {
            "shot_id": f"shot_{i:03d}",
            "clip_path": f"/voice/shot_{i:03d}.wav",
            "intent": f"shot {i} intent",
            "duration_ms": 3000,
        }
        for i in range(n_shots)
    ]


def _full_slots(n_shots: int = 2) -> dict:
    return {
        "voice-clips": _voice_clips(n_shots),
        "voice-timeline": {
            "shots": [{"shot_id": f"shot_{i:03d}"} for i in range(n_shots)]
        },
        "e-konte-sheets": {
            "shots": [
                {"shot_id": f"shot_{i:03d}", "keyframe": f"/kf/{i}.png"}
                for i in range(n_shots)
            ]
        },
    }


@pytest.fixture
def patched_engine(monkeypatch):
    """Monkeypatch p10b.select_engine to return a _RecordingEngine("slideshow").

    Returns the engine instance (tests can swap engine_tag if needed).
    """
    engine = _RecordingEngine(engine_tag="slideshow")
    monkeypatch.setattr(p10b, "select_engine", lambda *a, **kw: engine)
    return engine


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPreviewClipsJsonlFormat:
    """Verify the rapid-preview-clips JSONL format contract (RAPID-PREVIEW-04+07c)."""

    # -------------------------------------------------------------------
    # Tests 1-9: AssetBus-level format verification (no p10b involvement)
    # -------------------------------------------------------------------

    def test_rapid_preview_clips_file_extension_is_jsonl(self, tmp_path):
        """Test 1: After writing at least 1 record, the slot file ends in .jsonl.

        AssetBus stores files under ``tmp_path/.pipeline-assets/`` (the
        ``ASSETS_DIR`` constant). Use ``bus._dir`` to locate the actual
        file rather than assuming it sits at tmp_path root.
        """
        bus = AssetBus(tmp_path)
        bus.append_line("rapid-preview-clips", {
            "shot_id": "s1", "variant_id": "s1__v1_hook_position_sec",
            "structure_delta": {"hook_position_sec": 5},
            "clip_path": "/p.mp4", "generation_time_ms": 100, "engine": "slideshow",
        })
        # The schema-declared file path ends in .jsonl.
        assert ASSET_SCHEMA["rapid-preview-clips"]["file"].endswith(".jsonl")
        # The actual written file exists (under .pipeline-assets/) and ends
        # in .jsonl.
        expected_path = bus._dir / "rapid-preview-clips.jsonl"
        assert expected_path.exists(), (
            f"rapid-preview-clips.jsonl not found at {expected_path}; "
            f"bus._dir contents: {list(bus._dir.iterdir()) if bus._dir.exists() else 'dir missing'}"
        )
        assert expected_path.name.endswith(".jsonl")

    def test_each_line_parses_as_json(self, tmp_path):
        """Test 2: each non-blank line parses as a JSON object."""
        bus = AssetBus(tmp_path)
        for i in range(3):
            bus.append_line("rapid-preview-clips", {
                "shot_id": f"s{i}", "variant_id": f"s{i}__v1_hook_position_sec",
                "structure_delta": {"hook_position_sec": i},
                "clip_path": f"/p{i}.mp4", "generation_time_ms": i * 100,
                "engine": "slideshow",
            })
        # Read raw file content and verify each non-blank line parses.
        # AssetBus stores under tmp_path/.pipeline-assets/.
        raw_path = bus._dir / "rapid-preview-clips.jsonl"
        raw = raw_path.read_text(encoding="utf-8")
        lines = [ln for ln in raw.split("\n") if ln.strip()]
        assert len(lines) == 3, f"expected 3 non-blank lines; got {len(lines)}"
        for i, line in enumerate(lines):
            obj = json.loads(line)  # raises on invalid JSON
            assert isinstance(obj, dict), f"line {i} is not a JSON object"

    def test_each_record_has_all_six_required_fields(self, tmp_path):
        """Test 3: every record carries all 6 required fields."""
        bus = AssetBus(tmp_path)
        bus.append_line("rapid-preview-clips", {
            "shot_id": "s1", "variant_id": "s1__v1_hook_position_sec",
            "structure_delta": {"hook_position_sec": 5},
            "clip_path": "/p.mp4", "generation_time_ms": 100, "engine": "slideshow",
        })
        records = bus.read_lines("rapid-preview-clips")
        assert len(records) == 1
        missing = set(REQUIRED_FIELDS.keys()) - set(records[0].keys())
        assert not missing, f"missing fields: {missing}"

    def test_field_types_match_contract(self, tmp_path):
        """Test 4: strict type checks for each field.

        generation_time_ms MUST be int (not float — strict).
        """
        bus = AssetBus(tmp_path)
        bus.append_line("rapid-preview-clips", {
            "shot_id": "s1", "variant_id": "s1__v1_hook_position_sec",
            "structure_delta": {"hook_position_sec": 5},
            "clip_path": "/p.mp4", "generation_time_ms": 100, "engine": "slideshow",
        })
        records = bus.read_lines("rapid-preview-clips")
        rec = records[0]
        assert isinstance(rec["shot_id"], str)
        assert isinstance(rec["variant_id"], str)
        assert isinstance(rec["structure_delta"], dict)
        assert isinstance(rec["clip_path"], str)
        # STRICT: int, NOT float (bool is a subclass of int — also reject).
        assert isinstance(rec["generation_time_ms"], int), (
            f"generation_time_ms must be int; got {type(rec['generation_time_ms'])}"
        )
        assert not isinstance(rec["generation_time_ms"], bool), (
            "generation_time_ms must NOT be bool (Python bool subclasses int)"
        )
        assert isinstance(rec["engine"], str)

    def test_engine_value_is_in_valid_domain(self, tmp_path):
        """Test 5: engine field is in {"slideshow", "ltx"} — nothing else."""
        bus = AssetBus(tmp_path)
        bus.append_line("rapid-preview-clips", {
            "shot_id": "s1", "variant_id": "s1__v1_hook_position_sec",
            "structure_delta": {"hook_position_sec": 5},
            "clip_path": "/p.mp4", "generation_time_ms": 100, "engine": "slideshow",
        })
        bus.append_line("rapid-preview-clips", {
            "shot_id": "s2", "variant_id": "s2__v1_hook_position_sec",
            "structure_delta": {"hook_position_sec": 7},
            "clip_path": "/p2.mp4", "generation_time_ms": 200, "engine": "ltx",
        })
        records = bus.read_lines("rapid-preview-clips")
        for rec in records:
            assert rec["engine"] in VALID_ENGINE_VALUES, (
                f"engine {rec['engine']!r} not in valid domain {VALID_ENGINE_VALUES}"
            )

    def test_structure_delta_is_single_key_with_valid_param(self, tmp_path):
        """Test 6: structure_delta has exactly 1 key, and that key is a valid param."""
        bus = AssetBus(tmp_path)
        for param in VALID_DELTA_KEYS:
            bus.append_line("rapid-preview-clips", {
                "shot_id": "sx", "variant_id": f"sx__v1_{param}",
                "structure_delta": {param: 1},
                "clip_path": "/p.mp4", "generation_time_ms": 100,
                "engine": "slideshow",
            })
        records = bus.read_lines("rapid-preview-clips")
        assert len(records) == len(VALID_DELTA_KEYS)
        for rec in records:
            delta = rec["structure_delta"]
            assert len(delta) == 1, (
                f"structure_delta must be single-key; got {len(delta)}: {delta}"
            )
            only_key = next(iter(delta.keys()))
            assert only_key in VALID_DELTA_KEYS, (
                f"delta key {only_key!r} not in valid params {VALID_DELTA_KEYS}"
            )

    def test_variant_id_follows_naming_convention(self, tmp_path):
        """Test 7: variant_id matches "{shot_id}__v{N}_{param_name}" pattern."""
        bus = AssetBus(tmp_path)
        bus.append_line("rapid-preview-clips", {
            "shot_id": "shot_001", "variant_id": "shot_001__v2_emotion_sequence",
            "structure_delta": {"emotion_sequence": ["x"]},
            "clip_path": "/p.mp4", "generation_time_ms": 100, "engine": "slideshow",
        })
        records = bus.read_lines("rapid-preview-clips")
        rec = records[0]
        match = VARIANT_ID_PATTERN.match(rec["variant_id"])
        assert match is not None, (
            f"variant_id {rec['variant_id']!r} does not match naming convention"
        )
        assert match.group("shot_id") == "shot_001"
        assert match.group("position") == "2"
        assert match.group("param_name") == "emotion_sequence"

    def test_append_semantics_preserve_insertion_order(self, tmp_path):
        """Test 8: read_lines returns records in insertion order (no reorder/dedup)."""
        bus = AssetBus(tmp_path)
        for i in range(3):
            bus.append_line("rapid-preview-clips", {
                "shot_id": f"s{i}", "variant_id": f"s{i}__v1_hook_position_sec",
                "structure_delta": {"hook_position_sec": i},
                "clip_path": f"/p{i}.mp4", "generation_time_ms": i,
                "engine": "slideshow",
            })
        records = bus.read_lines("rapid-preview-clips")
        assert [r["shot_id"] for r in records] == ["s0", "s1", "s2"], (
            f"insertion order not preserved: {[r['shot_id'] for r in records]}"
        )

    def test_empty_slot_reads_as_empty_list(self, tmp_path):
        """Test 9: read_lines on a slot with no file returns []."""
        bus = AssetBus(tmp_path)
        records = bus.read_lines("rapid-preview-clips")
        assert records == [], (
            f"empty slot should return []; got {records}"
        )

    # -------------------------------------------------------------------
    # Test 10: integration with real p10b output
    # -------------------------------------------------------------------

    def test_p10b_output_records_match_contract(self, tmp_path, monkeypatch):
        """Test 10: run p10b with a mocked engine producing 2 records; then
        re-open AssetBus(tmp_path) (fresh instance) and read the slot —
        verify the 6-field + single-delta contract on the actual written records.

        This proves p10b's writes are persisted to a real file that a fresh
        process could read (no in-memory-only state leak).
        """
        # Inject the mocked engine.
        engine = _RecordingEngine(engine_tag="slideshow")
        monkeypatch.setattr(p10b, "select_engine", lambda *a, **kw: engine)

        # Use a real AssetBus for p10b's writes.
        bus = AssetBus(tmp_path)
        slots = _full_slots(n_shots=1)  # 1 shot → 3 variants expected

        p10b.run(
            episode_id="ep-integration",
            asset_bus_read=lambda slot: slots.get(slot),
            asset_bus_write=lambda slot, entry: bus.write(slot, entry, envelope=True)
            if ASSET_SCHEMA.get(slot, {}).get("format") != "jsonl"
            else bus.append_line(slot, entry),
            delegate_task=lambda g, c, t: {},
            trigger_gate=None,
            parallel_shots=1,
        )

        # Re-open the AssetBus from tmp_path (simulating a fresh process).
        fresh_bus = AssetBus(tmp_path)
        records = fresh_bus.read_lines("rapid-preview-clips")
        assert len(records) == 3, (
            f"expected 3 records from p10b run; got {len(records)}"
        )
        # Apply the full contract to each record.
        for i, rec in enumerate(records):
            missing = set(REQUIRED_FIELDS.keys()) - set(rec.keys())
            assert not missing, f"record {i} missing fields: {missing}"
            for field, expected_type in REQUIRED_FIELDS.items():
                assert isinstance(rec[field], expected_type), (
                    f"record {i} field {field!r}: expected {expected_type.__name__}, "
                    f"got {type(rec[field]).__name__}"
                )
                if expected_type is int:
                    assert not isinstance(rec[field], bool), (
                        f"record {i} field {field!r} must NOT be bool"
                    )
            assert rec["engine"] in VALID_ENGINE_VALUES
            assert len(rec["structure_delta"]) == 1
            only_key = next(iter(rec["structure_delta"].keys()))
            assert only_key in VALID_DELTA_KEYS
            # variant_id naming convention.
            match = VARIANT_ID_PATTERN.match(rec["variant_id"])
            assert match is not None, (
                f"record {i} variant_id {rec['variant_id']!r} does not match pattern"
            )

    # -------------------------------------------------------------------
    # Test 11 (BLOCKER #4): cycling matrix coverage at the JSONL file level
    # -------------------------------------------------------------------

    def test_cycling_matrix_covers_turning_points_sec_across_four_shots(
        self, tmp_path, monkeypatch
    ):
        """Test 11 (BLOCKER #4): run p10b across a 4-shot fixture; collect all
        records; assert ``turning_points_sec`` appears as a structure_delta key
        in >=1 variant across the episode (proves the cycling matrix from plan
        03 covers all 4 params at the JSONL file level).

        Same invariant as plan 03 Task 1 Test 3, but here verified via the
        rapid-preview-clips JSONL file after a real p10b run (not via
        _build_variants unit test).
        """
        engine = _RecordingEngine(engine_tag="slideshow")
        monkeypatch.setattr(p10b, "select_engine", lambda *a, **kw: engine)

        bus = AssetBus(tmp_path)
        slots = _full_slots(n_shots=4)  # 4 shots → 12 variants expected

        p10b.run(
            episode_id="ep-cycling",
            asset_bus_read=lambda slot: slots.get(slot),
            asset_bus_write=lambda slot, entry: bus.write(slot, entry, envelope=True)
            if ASSET_SCHEMA.get(slot, {}).get("format") != "jsonl"
            else bus.append_line(slot, entry),
            delegate_task=lambda g, c, t: {},
            trigger_gate=None,
            parallel_shots=4,
        )

        fresh_bus = AssetBus(tmp_path)
        records = fresh_bus.read_lines("rapid-preview-clips")
        assert len(records) == 12, (
            f"expected 12 records (4 shots × 3 variants); got {len(records)}"
        )
        # Collect all structure_delta keys across the episode.
        all_keys: set[str] = set()
        for rec in records:
            all_keys.update(rec["structure_delta"].keys())
        # BLOCKER #4 explicit assertion.
        assert "turning_points_sec" in all_keys, (
            f"BLOCKER #4: turning_points_sec MUST appear in >=1 variant across "
            f"a 4-shot episode (cycling matrix); got keys: {all_keys}"
        )
        # Sanity: cycling matrix covers ALL 4 params across shots 0..3.
        assert all_keys == VALID_DELTA_KEYS, (
            f"cycling matrix union mismatch; expected {VALID_DELTA_KEYS}, "
            f"got {all_keys}"
        )
