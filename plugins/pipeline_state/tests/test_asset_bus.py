"""test_asset_bus.py — pytest unit tests for AssetBus V3 port.

Mirrors Node.js describe blocks in ``kais-movie-agent/test/phases/asset-bus.test.mjs``
(33 tests) and ``asset-bus-derived-from.test.mjs`` (8 tests). Phase 33 targets the
high-value cases: schema config, content hash, envelope helpers, atomic write,
write/read round-trip, backward compat, mtime cache, JSONL, missing-file semantics.

V2/V4.1 slot tests are deferred (out of scope per CONTEXT CF-05 — only 3 v3.0 typed
slots + ``review-outcomes`` generic routing are ported in Phase 33).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from plugins.pipeline_state.asset_bus import (
    ASSET_SCHEMA,
    SCHEMA_VERSION,
    AssetBus,
    AssetBusError,
    _compute_content_hash,
    unwrap_envelope,
    wrap_envelope,
)


# ═══════════════════════════════════════════════════════════════════
# SCHEMA-01: 4 slots registered (3 v3.0 typed + review-outcomes)
# ═══════════════════════════════════════════════════════════════════
class TestSchemaConfig:
    def test_schema_version_is_3_0(self):
        assert SCHEMA_VERSION == "3.0"

    def test_asset_schema_has_four_required_slots(self):
        for slot in ("creative-history", "failed-shots", "finetune-dataset", "review-outcomes"):
            assert slot in ASSET_SCHEMA, f"missing slot: {slot}"

    def test_finetune_dataset_slot_is_jsonl_format(self):
        assert ASSET_SCHEMA["finetune-dataset"]["format"] == "jsonl"
        assert ASSET_SCHEMA["finetune-dataset"]["file"].endswith(".jsonl")

    def test_json_slots_default_format(self):
        # creative-history / failed-shots / review-outcomes are JSON
        for slot in ("creative-history", "failed-shots", "review-outcomes"):
            assert ASSET_SCHEMA[slot].get("format", "json") == "json"

    def test_list_asset_names_returns_all_four(self):
        names = AssetBus(Path("/tmp")).list_asset_names()
        assert set(names) >= {
            "creative-history", "failed-shots", "finetune-dataset", "review-outcomes"
        }


# ═══════════════════════════════════════════════════════════════════
# Content hash (SHA-256 of canonical JSON, sort_keys=True)
# ═══════════════════════════════════════════════════════════════════
class TestContentHash:
    def test_returns_64_char_lowercase_hex(self):
        h = _compute_content_hash({"a": 1})
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_deterministic_for_same_input(self):
        assert _compute_content_hash({"a": 1}) == _compute_content_hash({"a": 1})

    def test_different_inputs_produce_different_hashes(self):
        assert _compute_content_hash({"a": 1}) != _compute_content_hash({"a": 2})

    def test_canonical_order_invariant(self):
        # sort_keys=True means key order doesn't affect hash
        assert _compute_content_hash({"a": 1, "b": 2}) == _compute_content_hash({"b": 2, "a": 1})


# ═══════════════════════════════════════════════════════════════════
# Envelope helpers (wrap / unwrap)
# ═══════════════════════════════════════════════════════════════════
class TestEnvelopeHelpers:
    def test_wrap_produces_complete_v3_shape(self):
        env = wrap_envelope({"x": 1}, derived_from=["upstream-hash"])
        assert set(env.keys()) == {"value", "derived_from", "content_hash", "schema_version"}
        assert env["value"] == {"x": 1}
        assert env["derived_from"] == ["upstream-hash"]
        assert len(env["content_hash"]) == 64
        assert env["schema_version"] == SCHEMA_VERSION

    def test_wrap_derived_from_defaults_to_empty_list(self):
        env = wrap_envelope({"x": 1})
        assert env["derived_from"] == []

    def test_wrap_derived_from_none_becomes_empty(self):
        env = wrap_envelope({"x": 1}, derived_from=None)
        assert env["derived_from"] == []

    def test_unwrap_detects_v3_envelope(self):
        env = wrap_envelope({"data": 42})
        assert unwrap_envelope(env) == {"data": 42}

    def test_unwrap_passes_v2_raw_dict_through(self):
        raw = {"legacy": "data", "no_schema_version": True}
        assert unwrap_envelope(raw) is raw

    def test_unwrap_passes_arrays_through(self):
        raw = [1, 2, 3]
        assert unwrap_envelope(raw) == [1, 2, 3]


# ═══════════════════════════════════════════════════════════════════
# Atomic write — no .tmp residue (mirrors asset-bus.test.mjs:197)
# ═══════════════════════════════════════════════════════════════════
class TestAtomicWrite:
    def test_no_tmp_residue_after_write(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        bus.write("failed-shots", {"failures": [], "version": 1})
        assets_dir = tmp_path / ".pipeline-assets"
        files = list(assets_dir.iterdir())
        assert not any(".tmp." in f.name for f in files), f"tmp residue: {files}"
        assert any(f.name == "failed-shots.json" for f in files)

    def test_assets_dir_created_when_missing(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        # Directory doesn't exist yet
        assert not (tmp_path / ".pipeline-assets").exists()
        bus.write("failed-shots", {"failures": [], "version": 1})
        assert (tmp_path / ".pipeline-assets" / "failed-shots.json").exists()


# ═══════════════════════════════════════════════════════════════════
# Write + Read round-trip
# ═══════════════════════════════════════════════════════════════════
class TestWriteRead:
    def test_write_then_read_round_trips_with_envelope(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        payload = {"failures": [{"shot_id": "s1", "error": "boom"}], "version": 1}
        bus.write("failed-shots", payload)
        assert bus.read("failed-shots") == payload

    def test_envelope_false_writes_raw_data(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        payload = {"failures": [], "version": 2}
        bus.write("failed-shots", payload, envelope=False)
        # On-disk content should NOT be wrapped
        raw = json.loads(
            (tmp_path / ".pipeline-assets" / "failed-shots.json").read_text(encoding="utf-8")
        )
        assert "schema_version" not in raw
        assert raw == payload

    def test_derived_from_non_empty_forces_envelope(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        payload = {"failures": [], "version": 1}
        bus.write("failed-shots", payload, envelope=False, derived_from=["h1", "h2"])
        raw = json.loads(
            (tmp_path / ".pipeline-assets" / "failed-shots.json").read_text(encoding="utf-8")
        )
        assert raw.get("schema_version") == SCHEMA_VERSION
        assert raw["derived_from"] == ["h1", "h2"]
        assert raw["value"] == payload

    def test_write_rejects_jsonl_slot(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        with pytest.raises(AssetBusError, match="JSONL"):
            bus.write("finetune-dataset", {"x": 1})

    def test_write_rejects_unknown_slot(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        with pytest.raises(AssetBusError, match="Unknown asset"):
            bus.write("unknown-slot", {"x": 1})

    def test_read_rejects_jsonl_slot(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        with pytest.raises(AssetBusError):
            bus.read("finetune-dataset")

    def test_read_rejects_unknown_slot(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        with pytest.raises(AssetBusError):
            bus.read("unknown-slot")


# ═══════════════════════════════════════════════════════════════════
# v2.0 backward compatibility
# ═══════════════════════════════════════════════════════════════════
class TestBackwardCompat:
    def test_v2_raw_file_reads_back_as_is(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        # Simulate a v2.0 file: raw JSON, no envelope
        assets_dir = tmp_path / ".pipeline-assets"
        assets_dir.mkdir(parents=True)
        (assets_dir / "creative-history.json").write_text(
            json.dumps({"legacy": True, "no_envelope": "here"}), encoding="utf-8"
        )
        assert bus.read("creative-history") == {"legacy": True, "no_envelope": "here"}


# ═══════════════════════════════════════════════════════════════════
# mtime cache (write invalidates → next read sees new data)
# ═══════════════════════════════════════════════════════════════════
class TestMtimeCache:
    def test_write_then_read_returns_new_data_after_second_write(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        bus.write("failed-shots", {"failures": [], "version": 1})
        assert bus.read("failed-shots") == {"failures": [], "version": 1}
        # Sleep to ensure mtime_ns changes
        time.sleep(0.001)
        bus.write("failed-shots", {"failures": [{"shot_id": "s1"}], "version": 2})
        assert bus.read("failed-shots") == {"failures": [{"shot_id": "s1"}], "version": 2}

    def test_double_read_returns_same_data(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        payload = {"failures": [], "version": 1}
        bus.write("failed-shots", payload)
        first = bus.read("failed-shots")
        second = bus.read("failed-shots")
        assert first == second == payload

    def test_read_envelope_returns_raw_envelope_with_metadata(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        bus.write("failed-shots", {"failures": [], "version": 1}, derived_from=["src1"])
        env = bus.read_envelope("failed-shots")
        assert env is not None
        assert env["schema_version"] == SCHEMA_VERSION
        assert env["derived_from"] == ["src1"]


# ═══════════════════════════════════════════════════════════════════
# JSONL — append_line + read_lines (finetune-dataset slot)
# ═══════════════════════════════════════════════════════════════════
class TestJSONL:
    def test_append_line_writes_one_jsonl_line(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        bus.append_line("finetune-dataset", {"sample": 1, "label": "ok"})
        lines = bus.read_lines("finetune-dataset")
        assert lines == [{"sample": 1, "label": "ok"}]

    def test_append_line_rejects_non_jsonl_slot(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        with pytest.raises(AssetBusError, match="not JSONL"):
            bus.append_line("failed-shots", {"x": 1})

    def test_append_line_rejects_unknown_slot(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        with pytest.raises(AssetBusError):
            bus.append_line("unknown", {"x": 1})

    def test_read_lines_on_missing_file_returns_empty(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        assert bus.read_lines("finetune-dataset") == []

    def test_read_lines_skips_blank_lines(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        assets_dir = tmp_path / ".pipeline-assets"
        assets_dir.mkdir(parents=True)
        # Manually craft a file with blank lines (trailing newline + extra)
        path = assets_dir / "finetune-dataset.jsonl"
        path.write_text('{"a":1}\n\n{"b":2}\n   \n{"c":3}\n', encoding="utf-8")
        assert bus.read_lines("finetune-dataset") == [{"a": 1}, {"b": 2}, {"c": 3}]

    def test_many_appends_produce_ordered_readable_lines(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        for i in range(100):
            bus.append_line("finetune-dataset", {"i": i})
        lines = bus.read_lines("finetune-dataset")
        assert len(lines) == 100
        assert [entry["i"] for entry in lines] == list(range(100))


# ═══════════════════════════════════════════════════════════════════
# Missing-file / require semantics
# ═══════════════════════════════════════════════════════════════════
class TestReadMissing:
    def test_read_on_missing_file_returns_none(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        assert bus.read("creative-history") is None

    def test_require_on_missing_raises(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        with pytest.raises(AssetBusError, match="Required asset"):
            bus.require("creative-history")

    def test_require_returns_data_when_present(self, tmp_path: Path):
        bus = AssetBus(tmp_path)
        payload = {"shots": [], "version": 1}
        bus.write("creative-history", payload)
        assert bus.require("creative-history") == payload
