"""Tests for FeedbackStore (STORE-01..03 foundation).

Verifies the durable storage layer introduced in Phase 29 Plan 01:
  - TestFeedbackStoreInit: directory creation on first init
  - TestIndex: index.json schema after first record_feedback
  - TestDecay: compute_weight linear-decay math (STORE-03)
  - TestRecordFeedback: bucket layout + append semantics + record_id format
  - TestQuery: skill_id / source / verdict / since / until filters
  - TestSummary: per-bucket count / weighted_count / first_ts / last_ts
  - TestGetRecord: record_id lookup
  - TestMigration: lazy migration from Phase 28 incoming/
  - TestConfig: feedback.decay_window_days override

The ``feedback_env`` fixture mirrors ``tests/agent/test_feedback_ingest.py``
(monkeypatch HERMES_HOME + reload hermes_constants + reload the module under
test so its ``get_hermes_home`` import rebinds).
"""

from __future__ import annotations

import importlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixtures + helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def feedback_env(tmp_path, monkeypatch):
    """Isolated HERMES_HOME + reloaded feedback_store module.

    Mirrors the ``curator_env`` / ``feedback_env`` pattern in existing
    Phase 28 tests: monkeypatch HERMES_HOME to a tmp_path, reload
    hermes_constants so its home cache picks up the new path, then reload
    agent.feedback_store so its ``get_hermes_home`` import rebinds.
    """
    home = tmp_path / ".hermes"
    home.mkdir()
    (home / "skills").mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    import hermes_constants
    importlib.reload(hermes_constants)
    from agent import feedback_store
    importlib.reload(feedback_store)
    yield {
        "home": home,
        "feedback_store": feedback_store,
        "hermes_constants": hermes_constants,
    }


def _make_snapshot(*, sha256: str = "0" * 64, captured_at: datetime | None = None):
    """Build a minimal OutputSnapshot for tests."""
    from agent.feedback_schema import OutputSnapshot

    return OutputSnapshot(
        sha256=sha256,
        output_text="assistant output",
        prompt="user prompt",
        model="test-model",
        provider="openai",
        api_mode="chat_completions",
        params={"max_tokens": 1024},
        captured_at=captured_at or datetime.now(timezone.utc),
    )


def _make_record(
    *,
    skill_id: str = "screenplay",
    source: str = "cli",
    verdict: str = "good",
    correction: str = "x",
    sha256: str = "0" * 64,
    ts: datetime | None = None,
):
    """Build a minimal valid FeedbackRecord for store tests."""
    from agent.feedback_schema import FeedbackRecord

    snap = _make_snapshot(sha256=sha256, captured_at=ts)
    return FeedbackRecord(
        skill_id=skill_id,
        expert_id=skill_id,
        source=source,
        verdict=verdict,
        correction=correction,
        output_snapshot=snap,
        ts=ts or datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# TestFeedbackStoreInit
# ---------------------------------------------------------------------------


class TestFeedbackStoreInit:
    """FeedbackStore() creates directory layout on first init."""

    def test_init_creates_layout_dirs(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        root = home / "skills" / ".feedback"

        feedback_store.FeedbackStore()

        assert (root / "buckets").is_dir()
        assert (root / "dedup").is_dir()
        assert (root / "archive").is_dir()

    def test_init_uses_hermes_home(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]

        store = feedback_store.FeedbackStore()

        # _root must be under HERMES_HOME/skills/.feedback (not the real
        # ~/.hermes).
        assert store._root == home / "skills" / ".feedback"

    def test_init_creates_index_json(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        index_path = home / "skills" / ".feedback" / "index.json"

        feedback_store.FeedbackStore()

        assert index_path.is_file()


# ---------------------------------------------------------------------------
# TestIndex
# ---------------------------------------------------------------------------


class TestIndex:
    """index.json schema after first record_feedback."""

    def test_index_schema(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        store = feedback_store.FeedbackStore()
        record = _make_record()
        store.record_feedback(record)

        index_path = home / "skills" / ".feedback" / "index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))

        assert index["version"] == 1
        assert index["decay_window_days"] == 180
        assert "updated_ts" in index
        assert isinstance(index["buckets"], dict)
        assert isinstance(index["by_sha256"], dict)

    def test_index_bucket_key_uses_colon(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        store = feedback_store.FeedbackStore()
        store.record_feedback(_make_record(skill_id="screenplay", source="cli", verdict="good"))

        index = json.loads((home / "skills" / ".feedback" / "index.json").read_text(encoding="utf-8"))
        assert "screenplay:cli:good" in index["buckets"]

    def test_index_by_sha256_populated(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        store = feedback_store.FeedbackStore()
        sha = "a" * 64
        store.record_feedback(_make_record(sha256=sha))

        index = json.loads((home / "skills" / ".feedback" / "index.json").read_text(encoding="utf-8"))
        assert sha in index["by_sha256"]
        assert index["by_sha256"][sha]["status"] == "active"
        assert index["by_sha256"][sha]["verdict"] == "good"


# ---------------------------------------------------------------------------
# TestDecay (STORE-03)
# ---------------------------------------------------------------------------


class TestDecay:
    """compute_weight linear decay (STORE-03)."""

    def test_weight_at_birth(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        ts = datetime.now(timezone.utc)
        w = feedback_store.compute_weight(ts, now=ts)
        assert w == 1.0

    def test_weight_at_half(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        ts = datetime.now(timezone.utc)
        now = ts + timedelta(days=90)
        w = feedback_store.compute_weight(ts, now=now, decay_window_days=180)
        assert abs(w - 0.5) < 0.01

    def test_weight_floor_at_window(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        ts = datetime.now(timezone.utc)
        now = ts + timedelta(days=180)
        w = feedback_store.compute_weight(ts, now=now, decay_window_days=180)
        # 1.0 - 180/180 = 0.0 -> floored at 0.1
        assert w == 0.1

    def test_weight_floor_beyond_window(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        ts = datetime.now(timezone.utc)
        now = ts + timedelta(days=365)
        w = feedback_store.compute_weight(ts, now=now, decay_window_days=180)
        assert w == 0.1

    def test_weight_floor_default_window(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        ts = datetime.now(timezone.utc)
        now = ts + timedelta(days=180)
        # default decay_window_days=180
        w = feedback_store.compute_weight(ts, now=now)
        assert w == 0.1

    def test_weight_rejects_naive_ts(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        naive = datetime(2026, 6, 24, 12, 0, 0)  # no tzinfo
        with pytest.raises(TypeError):
            feedback_store.compute_weight(naive)

    def test_weight_rejects_naive_now(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        ts = datetime.now(timezone.utc)
        naive_now = datetime(2026, 6, 24, 12, 0, 0)
        with pytest.raises(TypeError):
            feedback_store.compute_weight(ts, now=naive_now)

    def test_recompute_bucket_weighted_count_simple(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        now = datetime.now(timezone.utc)
        records = [
            _make_record(ts=now),
            _make_record(ts=now - timedelta(days=90), sha256="1" * 64),
            _make_record(ts=now - timedelta(days=180), sha256="2" * 64),
        ]
        # weights: 1.0 + 0.5 + 0.1 = 1.6
        total = feedback_store.recompute_bucket_weighted_count(
            records, now=now, decay_window_days=180
        )
        assert abs(total - 1.6) < 0.01

    def test_recompute_bucket_weighted_count_skips_superseded(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        now = datetime.now(timezone.utc)
        r_active = _make_record(ts=now)
        # Attach a status attribute to simulate supersession (FeedbackRecord has
        # no status field; recompute uses getattr default).
        r_superseded = _make_record(ts=now, sha256="3" * 64)
        object.__setattr__(r_superseded, "status", "superseded")
        records = [r_active, r_superseded]
        # Only r_active counts: weight 1.0
        total = feedback_store.recompute_bucket_weighted_count(
            records, now=now, decay_window_days=180
        )
        assert abs(total - 1.0) < 0.01

    def test_config_override_decay_window(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        # decay_window_days=90 instead of 180: 60-day-old record weighs
        # 1.0 - 60/90 = 0.333
        store = feedback_store.FeedbackStore(decay_window_days=90)
        ts = datetime.now(timezone.utc) - timedelta(days=60)
        record = _make_record(ts=ts, sha256="9" * 64)
        store.record_feedback(record)

        index = json.loads((home / "skills" / ".feedback" / "index.json").read_text(encoding="utf-8"))
        bucket = index["buckets"]["screenplay:cli:good"]
        # weighted_count should be ~0.33 (60-day-old at 90-day window)
        assert abs(bucket["weighted_count"] - 0.33) < 0.02
