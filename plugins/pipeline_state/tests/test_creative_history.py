"""Tests for CreativeHistoryTracker — port of Node.js
creative-history-tracker.test.mjs (13 tests) + creative-history-perf.test.mjs
(4 tests).

Wave 1 independence note:
    The sibling plan (33-02) owns asset_bus.py. During parallel Wave 1
    execution AssetBus may not be importable yet. To keep this test file
    runnable in isolation, we use a small FakeBus that satisfies the
    contract CreativeHistoryTracker.stamp / _build_index need:

        read(slot)  -> dict | None
        write(slot, data, envelope=False) -> None

    If the real AssetBus is importable, a smoke test exercises it end-to-end
    so the integration is still covered once both Wave 1 plans land.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from plugins.pipeline_state.creative_history import (
    CreativeHistoryTracker,
    DEFAULT_MAX_BLAST_RADIUS,
    DEFAULT_MAX_DEPTH,
    write_blast_radius_report,
)


# ---------------------------------------------------------------------------
# Fake bus + fixtures
# ---------------------------------------------------------------------------


class FakeBus:
    """Minimal in-memory bus that records what was written and replays on read.

    Simulates the read-modify-write semantics that CreativeHistoryTracker.stamp
    relies on (read current shots, append, write back).
    """

    def __init__(self) -> None:
        self.store: dict[str, dict] = {}
        self.broken: bool = False

    def read(self, slot: str):
        if self.broken:
            raise RuntimeError("bus is broken (simulated)")
        return self.store.get(slot)

    def write(self, slot: str, data, envelope: bool = False) -> None:
        if self.broken:
            raise RuntimeError("bus is broken (simulated)")
        # Just stash the payload — tracker already shaped it.
        self.store[slot] = data


@pytest.fixture
def bus() -> FakeBus:
    return FakeBus()


@pytest.fixture
def tracker(bus: FakeBus) -> CreativeHistoryTracker:
    return CreativeHistoryTracker(asset_bus=bus)


# ---------------------------------------------------------------------------
# Constants / construction
# ---------------------------------------------------------------------------


class TestConstants:
    def test_default_caps_match_node_js(self) -> None:
        assert DEFAULT_MAX_BLAST_RADIUS == 20
        assert DEFAULT_MAX_DEPTH == 5
        assert CreativeHistoryTracker.DEFAULT_MAX_BLAST_RADIUS == 20
        assert CreativeHistoryTracker.DEFAULT_MAX_DEPTH == 5

    def test_construction_requires_asset_bus(self) -> None:
        with pytest.raises(ValueError, match="asset_bus required"):
            CreativeHistoryTracker(asset_bus=None)

    def test_hash_static_returns_64_char_sha256_hex(self) -> None:
        h = CreativeHistoryTracker.hash({"k": "v"})
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


# ---------------------------------------------------------------------------
# stamp
# ---------------------------------------------------------------------------


class TestStamp:
    def test_single_stamp_appends_to_creative_history_slot(
        self, tracker: CreativeHistoryTracker, bus: FakeBus
    ) -> None:
        ok = tracker.stamp(
            {
                "asset_slot": "final-shots",
                "asset_id": "shot-001",
                "source_hashes": ["h-upstream"],
                "content_hash": "v1",
            }
        )
        assert ok is True
        data = bus.store["creative-history"]
        assert isinstance(data, dict)
        shots = data["shots"]
        assert len(shots) == 1
        rec = shots[0]
        assert rec["asset_slot"] == "final-shots"
        assert rec["asset_id"] == "shot-001"
        assert rec["source_hashes"] == ["h-upstream"]
        assert rec["content_hash"] == "v1"
        # ISO 8601 timestamp present (must contain a 'T' separator).
        assert "T" in rec["timestamp"]

    def test_multiple_stamps_accumulate_in_order(
        self, tracker: CreativeHistoryTracker
    ) -> None:
        for i in range(5):
            ok = tracker.stamp(
                {
                    "asset_slot": "final-shots",
                    "asset_id": f"shot-{i}",
                    "source_hashes": [],
                    "content_hash": f"v{i}",
                }
            )
            assert ok is True
        shots = tracker._bus.store["creative-history"]["shots"]  # type: ignore[union-attr]
        assert len(shots) == 5
        assert [s["asset_id"] for s in shots] == [
            "shot-0",
            "shot-1",
            "shot-2",
            "shot-3",
            "shot-4",
        ]

    def test_stamp_degraded_returns_false_on_broken_bus(
        self, tracker: CreativeHistoryTracker, bus: FakeBus
    ) -> None:
        bus.broken = True
        # Must NOT raise — degraded mode is fire-and-forget.
        ok = tracker.stamp(
            {
                "asset_slot": "final-shots",
                "asset_id": "shot-x",
                "content_hash": "vx",
            }
        )
        assert ok is False

    def test_stamp_rejects_entry_missing_required_fields(
        self, tracker: CreativeHistoryTracker
    ) -> None:
        with pytest.raises(ValueError):
            tracker.stamp({})  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            tracker.stamp({"asset_id": "x"})  # missing asset_slot
        with pytest.raises(ValueError):
            tracker.stamp({"asset_slot": "y"})  # missing asset_id

    def test_stamp_computes_content_hash_when_omitted(
        self, tracker: CreativeHistoryTracker
    ) -> None:
        ok = tracker.stamp(
            {"asset_slot": "x", "asset_id": "y", "source_hashes": ["h1"]}
        )
        assert ok is True
        rec = tracker._bus.store["creative-history"]["shots"][0]  # type: ignore[union-attr]
        # 64-char sha256 hex.
        assert len(rec["content_hash"]) == 64
        assert all(c in "0123456789abcdef" for c in rec["content_hash"])


# ---------------------------------------------------------------------------
# find_affected (reverse BFS)
# ---------------------------------------------------------------------------


def _stamp_chain(tracker: CreativeHistoryTracker, chain: list[tuple[str, str, str]]) -> None:
    """Helper: stamp a list of (asset_id, content_hash, source_hash) tuples."""
    for asset_id, content_hash, source_hash in chain:
        ok = tracker.stamp(
            {
                "asset_slot": "final-shots",
                "asset_id": asset_id,
                "content_hash": content_hash,
                "source_hashes": [source_hash],
            }
        )
        assert ok, f"stamp failed for {asset_id}"


class TestFindAffected:
    def test_chain_a_b_c_returns_both_b_and_c(
        self, tracker: CreativeHistoryTracker
    ) -> None:
        # A (hash-A) -> B (hash-B) -> C (hash-C)
        _stamp_chain(
            tracker,
            [
                ("B", "hash-B", "hash-A"),
                ("C", "hash-C", "hash-B"),
            ],
        )
        result = tracker.find_affected("hash-A")
        assert result["truncated"] is False
        assert result["blast_radius"] == 2
        ids = [r["asset_id"] for r in result["affected"]]
        assert ids == ["B", "C"]
        depths = {r["asset_id"]: r["depth"] for r in result["affected"]}
        assert depths["B"] == 1
        assert depths["C"] == 2

    def test_leaf_hash_returns_empty_affected(
        self, tracker: CreativeHistoryTracker
    ) -> None:
        # hash-X has no downstream records.
        result = tracker.find_affected("hash-X")
        assert result["affected"] == []
        assert result["truncated"] is False
        assert result["blast_radius"] == 0

    def test_blast_radius_cap_sets_truncated_true(
        self, bus: FakeBus
    ) -> None:
        tracker = CreativeHistoryTracker(
            asset_bus=bus, max_blast_radius=2
        )
        # 3 derived assets all sourcing from "root"
        _stamp_chain(
            tracker,
            [
                ("d1", "v1", "root"),
                ("d2", "v2", "root"),
                ("d3", "v3", "root"),
            ],
        )
        result = tracker.find_affected("root")
        assert result["truncated"] is True
        assert result["blast_radius"] == 2
        assert len(result["affected"]) == 2

    def test_depth_cap_stops_bfs_at_max_depth(
        self, bus: FakeBus
    ) -> None:
        tracker = CreativeHistoryTracker(asset_bus=bus, max_depth=1)
        # Chain depth 3: root -> B -> C -> D
        _stamp_chain(
            tracker,
            [
                ("B", "hB", "root"),
                ("C", "hC", "hB"),
                ("D", "hD", "hC"),
            ],
        )
        result = tracker.find_affected("root")
        # max_depth=1 → only depth-1 layer (B) reachable.
        assert result["max_depth"] == 1
        ids = [r["asset_id"] for r in result["affected"]]
        assert ids == ["B"]
        assert result["truncated"] is False

    def test_diamond_dag_deduplicates_shared_descendant(
        self, tracker: CreativeHistoryTracker
    ) -> None:
        # Diamond: A -> B, A -> C, B -> D, C -> D
        # D sourced from both hB and hC; must appear only once.
        ok = tracker.stamp(
            {
                "asset_slot": "s",
                "asset_id": "B",
                "content_hash": "hB",
                "source_hashes": ["hA"],
            }
        )
        assert ok
        ok = tracker.stamp(
            {
                "asset_slot": "s",
                "asset_id": "C",
                "content_hash": "hC",
                "source_hashes": ["hA"],
            }
        )
        assert ok
        ok = tracker.stamp(
            {
                "asset_slot": "s",
                "asset_id": "D",
                "content_hash": "hD",
                "source_hashes": ["hB", "hC"],
            }
        )
        assert ok
        result = tracker.find_affected("hA")
        ids = [r["asset_id"] for r in result["affected"]]
        # B, C, D — D appears once despite being sourced from two parents.
        assert sorted(ids) == ["B", "C", "D"]
        assert len(ids) == 3  # no duplicates

    def test_cap_dict_uses_camel_case_keys_for_node_js_compat(
        self, tracker: CreativeHistoryTracker
    ) -> None:
        result = tracker.find_affected("anything")
        assert "maxBlastRadius" in result["cap"]
        assert "maxDepth" in result["cap"]
        # snake_case must NOT be present (Node.js compat).
        assert "max_blast_radius" not in result["cap"]
        assert "max_depth" not in result["cap"]

    def test_index_cache_invalidated_after_stamp(
        self, tracker: CreativeHistoryTracker
    ) -> None:
        # First find_affected builds + caches the index.
        tracker.find_affected("none")
        assert tracker._index_cache is not None
        # stamp() invalidates.
        tracker.stamp(
            {"asset_slot": "s", "asset_id": "x", "content_hash": "v", "source_hashes": []}
        )
        assert tracker._index_cache is None


# ---------------------------------------------------------------------------
# diff
# ---------------------------------------------------------------------------


class TestDiff:
    def test_diff_multiple_hashes_returns_union_with_per_hash(
        self, tracker: CreativeHistoryTracker
    ) -> None:
        # Two independent chains: h1 -> A, h2 -> B
        _stamp_chain(tracker, [("A", "vA", "h1")])
        _stamp_chain(tracker, [("B", "vB", "h2")])
        result = tracker.diff(["h1", "h2"])
        ids = sorted(r["asset_id"] for r in result["affected"])
        assert ids == ["A", "B"]
        assert "h1" in result["per_hash"]
        assert "h2" in result["per_hash"]
        assert result["truncated"] is False

    def test_diff_empty_returns_empty(self, tracker: CreativeHistoryTracker) -> None:
        result = tracker.diff([])
        assert result == {"affected": [], "truncated": False, "per_hash": {}}


# ---------------------------------------------------------------------------
# write_blast_radius_report
# ---------------------------------------------------------------------------


class TestWriteBlastRadiusReport:
    def test_write_report_truncated(
        self, tracker: CreativeHistoryTracker, tmp_path: Path
    ) -> None:
        result = {
            "affected": [{"asset_id": "x"}],
            "truncated": True,
            "blast_radius": 1,
            "max_depth": 1,
            "cap": {"maxBlastRadius": 20, "maxDepth": 5},
        }
        out = write_blast_radius_report(
            result, tmp_path / "report.json", changed_hash="h-changed"
        )
        report = json.loads(Path(out).read_text(encoding="utf-8"))
        assert report["changed_hash"] == "h-changed"
        assert report["truncated"] is True
        assert report["affected_count"] == 1
        assert "generated_at" in report
        assert "exceeded" in report["note"]
        assert report["cap"] == {"maxBlastRadius": 20, "maxDepth": 5}

    def test_write_report_non_truncated(
        self, tracker: CreativeHistoryTracker, tmp_path: Path
    ) -> None:
        result = {
            "affected": [],
            "truncated": False,
            "blast_radius": 0,
            "max_depth": 0,
            "cap": {"maxBlastRadius": 20, "maxDepth": 5},
        }
        out = write_blast_radius_report(result, tmp_path / "sub" / "r.json")
        report = json.loads(Path(out).read_text(encoding="utf-8"))
        assert report["truncated"] is False
        assert report["note"] == "All affected assets captured."
        # Parent dir auto-created.
        assert Path(out).exists()


# ---------------------------------------------------------------------------
# Performance (B4-04 budget: <500ms for 1000-asset BFS)
# ---------------------------------------------------------------------------


class TestPerformance:
    def test_bfs_1000_chain_under_500ms(self, bus: FakeBus) -> None:
        """BFS over 1000-link chain must complete in <500ms (B4-04 spec).

        Per plan task 2 <action>, the chain is constructed via a single direct
        bus.write of 1000 records rather than 1000 stamp() calls — this keeps
        test setup fast while still exercising BFS over 1000 records. Only the
        find_affected call is timed.
        """
        # max_depth + max_blast_radius must exceed 1000 to traverse the full
        # 1000-deep chain (defaults 5/20 would truncate it).
        tracker = CreativeHistoryTracker(
            asset_bus=bus, max_depth=1000, max_blast_radius=1000
        )
        # Build 1000 records: chain root -> v0 -> v1 -> ... -> v999.
        shots = []
        prev_hash = "root"
        for i in range(1000):
            content_hash = f"v-{i:04d}"
            shots.append(
                {
                    "asset_slot": "final-shots",
                    "asset_id": f"shot-{i:04d}",
                    "source_hashes": [prev_hash],
                    "content_hash": content_hash,
                    "timestamp": "2026-01-01T00:00:00+00:00",
                }
            )
            prev_hash = content_hash
        bus.store["creative-history"] = {"shots": shots, "version": 1}

        start = time.perf_counter()
        result = tracker.find_affected("root")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 500, f"BFS took {elapsed_ms:.1f}ms (>500ms budget)"
        assert result["blast_radius"] == 1000
        assert result["truncated"] is False
        # Sanity: last asset in the chain was reached.
        ids = {r["asset_id"] for r in result["affected"]}
        assert "shot-0999" in ids
        assert "shot-0000" in ids

    def test_bfs_deep_chain_depth_10_under_500ms(self, bus: FakeBus) -> None:
        """Optional: deep (depth=10) chain with max_depth=10 should also be fast."""
        tracker = CreativeHistoryTracker(asset_bus=bus, max_depth=10)
        shots = []
        prev_hash = "root"
        for i in range(10):
            content_hash = f"d-{i}"
            shots.append(
                {
                    "asset_slot": "s",
                    "asset_id": f"n-{i}",
                    "source_hashes": [prev_hash],
                    "content_hash": content_hash,
                    "timestamp": "2026-01-01T00:00:00+00:00",
                }
            )
            prev_hash = content_hash
        bus.store["creative-history"] = {"shots": shots, "version": 1}

        start = time.perf_counter()
        result = tracker.find_affected("root")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 500
        assert result["blast_radius"] == 10
        assert result["max_depth"] == 10


# ---------------------------------------------------------------------------
# Integration smoke — real AssetBus (only if sibling plan 33-02 has landed)
# ---------------------------------------------------------------------------


class TestRealAssetBusIntegration:
    """Smoke test against the real AssetBus, skipped if asset_bus.py is absent.

    Once sibling plan 33-02 lands (Wave 2 merge), this exercises the
    read-modify-write path on a real filesystem-backed bus.
    """

    def test_stamp_and_find_affected_round_trip_on_real_bus(
        self, tmp_path: Path
    ) -> None:
        pytest.importorskip(
            "plugins.pipeline_state.asset_bus",
            reason="asset_bus.py not yet ported (sibling plan 33-02)",
        )
        from plugins.pipeline_state.asset_bus import AssetBus

        bus = AssetBus(tmp_path)
        tracker = CreativeHistoryTracker(asset_bus=bus)
        ok = tracker.stamp(
            {
                "asset_slot": "final-shots",
                "asset_id": "B",
                "content_hash": "hB",
                "source_hashes": ["hA"],
            }
        )
        assert ok is True
        result = tracker.find_affected("hA")
        assert result["blast_radius"] == 1
        assert result["affected"][0]["asset_id"] == "B"
