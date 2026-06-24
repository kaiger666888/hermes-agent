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


# ---------------------------------------------------------------------------
# TestRecordFeedback
# ---------------------------------------------------------------------------


class TestRecordFeedback:
    """record_feedback bucket layout + append semantics + index update."""

    def test_bucket_layout(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        store = feedback_store.FeedbackStore()
        store.record_feedback(
            _make_record(skill_id="screenplay", source="cli", verdict="good")
        )

        bucket = home / "skills" / ".feedback" / "buckets" / "screenplay" / "cli.jsonl"
        assert bucket.is_file()
        lines = bucket.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1

    def test_append_only_semantics(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        store = feedback_store.FeedbackStore()

        store.record_feedback(_make_record(sha256="a" * 64))
        bucket = home / "skills" / ".feedback" / "buckets" / "screenplay" / "cli.jsonl"
        first_bytes = bucket.read_text(encoding="utf-8")

        store.record_feedback(_make_record(sha256="b" * 64))
        store.record_feedback(_make_record(sha256="c" * 64))

        contents = bucket.read_text(encoding="utf-8")
        # First line is unchanged (append-only).
        assert contents.startswith(first_bytes)
        assert len(contents.splitlines()) == 3

    def test_returns_record_id_format(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        record_id = store.record_feedback(_make_record())
        # Format: ^\d{16}_[0-9a-f]{8}$ (microsecond ts + 8-hex sha prefix)
        import re

        assert re.match(r"^\d{16}_[0-9a-f]{8}$", record_id), (
            f"record_id {record_id!r} does not match expected format"
        )

    def test_bucket_key_uses_colon_separator(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        store = feedback_store.FeedbackStore()
        store.record_feedback(
            _make_record(skill_id="screenplay", source="cli", verdict="good")
        )

        index = json.loads(
            (home / "skills" / ".feedback" / "index.json").read_text(encoding="utf-8")
        )
        assert "screenplay:cli:good" in index["buckets"]
        # _ separator would collide with skill_ids containing underscores.
        assert "screenplay_cli_good" not in index["buckets"]

    def test_index_updated_atomic(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        index_path = home / "skills" / ".feedback" / "index.json"
        store = feedback_store.FeedbackStore()
        mtime_before = index_path.stat().st_mtime_ns

        store.record_feedback(_make_record())

        mtime_after = index_path.stat().st_mtime_ns
        assert mtime_after > mtime_before

    def test_weighted_count_differs_from_count_for_old_record(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        store = feedback_store.FeedbackStore()
        old_ts = datetime.now(timezone.utc) - timedelta(days=100)
        store.record_feedback(_make_record(ts=old_ts, sha256="1" * 64))

        index = json.loads(
            (home / "skills" / ".feedback" / "index.json").read_text(encoding="utf-8")
        )
        bucket = index["buckets"]["screenplay:cli:good"]
        assert bucket["count"] == 1
        # 100-day-old at 180-day window: weight = 1 - 100/180 = 0.444
        assert 0.1 < bucket["weighted_count"] < 0.5

    def test_weighted_count_equals_count_for_fresh_record(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        store = feedback_store.FeedbackStore()
        store.record_feedback(_make_record(ts=datetime.now(timezone.utc)))

        index = json.loads(
            (home / "skills" / ".feedback" / "index.json").read_text(encoding="utf-8")
        )
        bucket = index["buckets"]["screenplay:cli:good"]
        assert bucket["count"] == 1
        assert abs(bucket["weighted_count"] - 1.0) < 0.01

    def test_multiple_verdicts_same_bucket_file(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        store = feedback_store.FeedbackStore()
        store.record_feedback(
            _make_record(skill_id="screenplay", source="cli", verdict="good", sha256="1" * 64)
        )
        store.record_feedback(
            _make_record(
                skill_id="screenplay", source="cli", verdict="needs_work", sha256="2" * 64
            )
        )

        bucket = home / "skills" / ".feedback" / "buckets" / "screenplay" / "cli.jsonl"
        lines = bucket.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 2  # verdict is a record attribute, not a file split


# ---------------------------------------------------------------------------
# TestQuery
# ---------------------------------------------------------------------------


class TestQuery:
    """query() filters by skill_id / source / verdict / since / until."""

    def test_query_by_skill_id(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        store.record_feedback(_make_record(skill_id="screenplay", sha256="1" * 64))
        store.record_feedback(_make_record(skill_id="drawer", sha256="2" * 64))

        results = store.query(skill_id="screenplay")
        assert len(results) == 1
        assert all(r.skill_id == "screenplay" for r in results)

    def test_query_by_source(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        store.record_feedback(
            _make_record(skill_id="screenplay", source="cli", sha256="1" * 64)
        )
        store.record_feedback(
            _make_record(skill_id="screenplay", source="kais_aigc", sha256="2" * 64)
        )

        results = store.query(skill_id="screenplay", source="kais_aigc")
        assert len(results) == 1
        assert results[0].source == "kais_aigc"

    def test_query_by_verdict(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        store.record_feedback(
            _make_record(skill_id="screenplay", verdict="good", sha256="1" * 64)
        )
        store.record_feedback(
            _make_record(skill_id="screenplay", verdict="needs_work", sha256="2" * 64)
        )
        store.record_feedback(
            _make_record(skill_id="screenplay", verdict="bad", sha256="3" * 64)
        )

        results = store.query(skill_id="screenplay", verdict="needs_work")
        assert len(results) == 1
        assert results[0].verdict == "needs_work"

    def test_query_composed_filters(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        t0 = datetime.now(timezone.utc) - timedelta(days=10)
        t1 = datetime.now(timezone.utc) - timedelta(days=5)
        t2 = datetime.now(timezone.utc)
        store.record_feedback(
            _make_record(
                skill_id="screenplay",
                source="cli",
                verdict="good",
                sha256="1" * 64,
                ts=t0,
            )
        )
        store.record_feedback(
            _make_record(
                skill_id="screenplay",
                source="cli",
                verdict="good",
                sha256="2" * 64,
                ts=t1,
            )
        )
        store.record_feedback(
            _make_record(
                skill_id="screenplay",
                source="kais_aigc",
                verdict="good",
                sha256="3" * 64,
                ts=t2,
            )
        )

        results = store.query(
            skill_id="screenplay",
            source="cli",
            verdict="good",
            since=t0 - timedelta(seconds=1),
            until=t1 + timedelta(seconds=1),
        )
        assert len(results) == 2
        assert all(r.source == "cli" for r in results)
        assert all(r.verdict == "good" for r in results)

    def test_query_since_until(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        t0 = datetime.now(timezone.utc) - timedelta(days=10)
        t1 = datetime.now(timezone.utc) - timedelta(days=5)
        t2 = datetime.now(timezone.utc)
        store.record_feedback(_make_record(sha256="1" * 64, ts=t0))
        store.record_feedback(_make_record(sha256="2" * 64, ts=t1))
        store.record_feedback(_make_record(sha256="3" * 64, ts=t2))

        assert len(store.query(skill_id="screenplay", since=t1)) == 2
        assert len(store.query(skill_id="screenplay", until=t1)) == 2
        assert (
            len(store.query(skill_id="screenplay", since=t1, until=t2)) == 2
        )

    def test_query_returns_pydantic_instances(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        from agent.feedback_schema import FeedbackRecord

        store = feedback_store.FeedbackStore()
        store.record_feedback(_make_record())
        results = store.query(skill_id="screenplay")
        assert len(results) == 1
        assert isinstance(results[0], FeedbackRecord)

    def test_query_empty_bucket(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        # screenplay has no records; query returns []
        assert store.query(skill_id="screenplay") == []

    def test_query_include_superseded_default_false(self, feedback_env):
        feedback_env_mod = feedback_env["feedback_store"]
        store = feedback_env_mod.FeedbackStore()
        store.record_feedback(_make_record(sha256="1" * 64))
        # Plan 01 has no superseded records yet — default returns all.
        results = store.query(skill_id="screenplay", include_superseded=False)
        assert len(results) == 1


# ---------------------------------------------------------------------------
# TestSummary
# ---------------------------------------------------------------------------


class TestSummary:
    """summary() returns per-bucket count/weighted_count/first_ts/last_ts."""

    def test_summary_returns_per_bucket_counts(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        for i in range(3):
            store.record_feedback(
                _make_record(verdict="good", sha256=hex(i + 1)[2:] * 64)
            )
        for i in range(2):
            store.record_feedback(
                _make_record(
                    verdict="needs_work", sha256=hex(i + 10)[2:] * 64
                )
            )

        summary = store.summary()
        assert "screenplay:cli:good" in summary
        assert summary["screenplay:cli:good"]["count"] == 3
        assert "screenplay:cli:needs_work" in summary
        assert summary["screenplay:cli:needs_work"]["count"] == 2

    def test_summary_weighted_count(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        store.record_feedback(_make_record(sha256="1" * 64))
        summary = store.summary()
        assert summary["screenplay:cli:good"]["weighted_count"] > 0

    def test_summary_first_last_ts(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        t0 = datetime.now(timezone.utc) - timedelta(days=10)
        t1 = datetime.now(timezone.utc)
        store.record_feedback(_make_record(sha256="1" * 64, ts=t0))
        store.record_feedback(_make_record(sha256="2" * 64, ts=t1))

        summary = store.summary()
        bucket = summary["screenplay:cli:good"]
        first = datetime.fromisoformat(bucket["first_ts"])
        last = datetime.fromisoformat(bucket["last_ts"])
        assert abs((first - t0).total_seconds()) < 1
        assert abs((last - t1).total_seconds()) < 1

    def test_summary_filter_by_skill_id(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        store.record_feedback(
            _make_record(skill_id="screenplay", sha256="1" * 64)
        )
        store.record_feedback(_make_record(skill_id="drawer", sha256="2" * 64))

        summary = store.summary(skill_id="screenplay")
        assert all(k.startswith("screenplay:") for k in summary)

    def test_summary_filter_by_source(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        store.record_feedback(
            _make_record(source="cli", sha256="1" * 64)
        )
        store.record_feedback(
            _make_record(source="kais_aigc", sha256="2" * 64)
        )

        summary = store.summary(source="cli")
        assert all(":cli:" in k for k in summary)

    def test_summary_empty_store(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        assert store.summary() == {}


# ---------------------------------------------------------------------------
# TestGetRecord
# ---------------------------------------------------------------------------


class TestGetRecord:
    """get_record() returns matching record or None."""

    def test_get_record_returns_match(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        ts = datetime.now(timezone.utc)
        sha = "f" * 64
        record = _make_record(sha256=sha, ts=ts)
        rid = store.record_feedback(record)

        found = store.get_record(rid)
        assert found is not None
        assert found.output_snapshot.sha256 == sha

    def test_get_record_unknown_returns_none(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        assert store.get_record("nonexistent_record_id") is None


# ---------------------------------------------------------------------------
# TestMigration
# ---------------------------------------------------------------------------


class TestMigration:
    """Lazy migration from Phase 28 flat incoming/ layout."""

    def test_migrate_incoming_routes_to_buckets(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        # Pre-populate incoming/ with a Phase 28 flat-layout JSON file.
        incoming = home / "skills" / ".feedback" / "incoming"
        incoming.mkdir(parents=True, exist_ok=True)
        record = _make_record(sha256="1" * 64)
        src_file = incoming / "screenplay_cli_20260624T120000000000Z.json"
        src_file.write_text(record.model_dump_json(), encoding="utf-8")

        # Trigger migration by re-initializing the store. (The fixture's
        # reload already created a store without incoming/ populated; we
        # construct a new one now that incoming/ has files.)
        store = feedback_store.FeedbackStore()

        bucket = home / "skills" / ".feedback" / "buckets" / "screenplay" / "cli.jsonl"
        assert bucket.is_file()
        lines = bucket.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        assert json.loads(lines[0])["output_snapshot"]["sha256"] == "1" * 64

    def test_migration_idempotent(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        incoming = home / "skills" / ".feedback" / "incoming"
        incoming.mkdir(parents=True, exist_ok=True)
        record = _make_record(sha256="2" * 64)
        src_file = incoming / "screenplay_cli_20260624T120000000000Z.json"
        src_file.write_text(record.model_dump_json(), encoding="utf-8")

        # First init migrates.
        feedback_store.FeedbackStore()
        # Second init should find incoming/ empty — no-op.
        feedback_store.FeedbackStore()

        # incoming/ should be empty.
        assert list(incoming.glob("*.json")) == []

    def test_migration_archives_originals(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        incoming = home / "skills" / ".feedback" / "incoming"
        incoming.mkdir(parents=True, exist_ok=True)
        record = _make_record(sha256="3" * 64)
        src_name = "screenplay_cli_20260624T120000000000Z.json"
        src_file = incoming / src_name
        src_file.write_text(record.model_dump_json(), encoding="utf-8")

        feedback_store.FeedbackStore()

        archive = home / "skills" / ".feedback" / "archive" / "phase-28-migration"
        archived = archive / src_name
        assert archived.is_file()

    def test_migration_no_incoming_noop(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        # No incoming/ dir or empty — no archive/phase-28-migration/ files.
        store = feedback_store.FeedbackStore()
        archive = home / "skills" / ".feedback" / "archive" / "phase-28-migration"
        # Archive dir may exist (FeedbackStore creates it), but no files in it.
        if archive.is_dir():
            assert list(archive.glob("*.json")) == []

    def test_migration_handles_malformed(self, feedback_env, caplog):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        incoming = home / "skills" / ".feedback" / "incoming"
        incoming.mkdir(parents=True, exist_ok=True)
        good = _make_record(sha256="4" * 64)
        (incoming / "screenplay_cli_20260624T120000000000Z.json").write_text(
            good.model_dump_json(), encoding="utf-8"
        )
        (incoming / "malformed.json").write_text(
            "{not valid json", encoding="utf-8"
        )

        with caplog.at_level("WARNING"):
            # Should NOT raise — migration logs + continues.
            store = feedback_store.FeedbackStore()

        # Valid record migrated; malformed still in incoming/.
        bucket = home / "skills" / ".feedback" / "buckets" / "screenplay" / "cli.jsonl"
        assert bucket.is_file()
        assert (incoming / "malformed.json").is_file()
        # Valid one moved out of incoming/.
        assert not (incoming / "screenplay_cli_20260624T120000000000Z.json").exists()

    def test_migration_partial_recovery(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        incoming = home / "skills" / ".feedback" / "incoming"
        incoming.mkdir(parents=True, exist_ok=True)
        archive = home / "skills" / ".feedback" / "archive" / "phase-28-migration"
        archive.mkdir(parents=True, exist_ok=True)

        r1 = _make_record(sha256="5" * 64)
        r2 = _make_record(sha256="6" * 64)
        f1 = incoming / "screenplay_cli_20260624T120000000001Z.json"
        f2 = incoming / "screenplay_cli_20260624T120000000002Z.json"
        f1.write_text(r1.model_dump_json(), encoding="utf-8")
        f2.write_text(r2.model_dump_json(), encoding="utf-8")

        # Simulate partial migration: manually archive f1 (as if a prior run
        # migrated it but crashed before handling f2).
        (archive / f1.name).write_text(r1.model_dump_json(), encoding="utf-8")
        f1.unlink()

        # Second init migrates only the remaining file (f2).
        feedback_store.FeedbackStore()

        # f2 is now archived; archive has both files.
        assert (archive / f1.name).is_file()
        assert (archive / f2.name).is_file()
        assert list(incoming.glob("*.json")) == []
        # Bucket has both records (f1 re-appended; f2 newly appended —
        # harmless duplicate per RESEARCH Pitfall #4).
        bucket = home / "skills" / ".feedback" / "buckets" / "screenplay" / "cli.jsonl"
        assert bucket.is_file()


# ---------------------------------------------------------------------------
# TestConfig
# ---------------------------------------------------------------------------


class TestConfig:
    """feedback.decay_window_days config override + fallback."""

    def test_config_override_decay_window(self, feedback_env, monkeypatch):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]

        # Monkeypatch the config loader used by _load_decay_window_days_from_config
        # to return 90 days.
        import hermes_cli.config

        monkeypatch.setattr(
            hermes_cli.config,
            "load_config",
            lambda: {"feedback": {"decay_window_days": 90}},
        )

        # 60-day-old record at 90-day window: weight = 1 - 60/90 = 0.333.
        store = feedback_store.FeedbackStore()
        assert store._decay_window_days == 90
        ts = datetime.now(timezone.utc) - timedelta(days=60)
        store.record_feedback(_make_record(ts=ts, sha256="7" * 64))

        index = json.loads(
            (home / "skills" / ".feedback" / "index.json").read_text(encoding="utf-8")
        )
        bucket = index["buckets"]["screenplay:cli:good"]
        assert abs(bucket["weighted_count"] - 0.33) < 0.02

    def test_config_missing_uses_default(self, feedback_env, monkeypatch):
        feedback_store = feedback_env["feedback_store"]

        import hermes_cli.config

        monkeypatch.setattr(hermes_cli.config, "load_config", lambda: {})

        store = feedback_store.FeedbackStore()
        assert store._decay_window_days == 180

    def test_config_invalid_value_uses_default(self, feedback_env, monkeypatch):
        feedback_store = feedback_env["feedback_store"]

        import hermes_cli.config

        monkeypatch.setattr(
            hermes_cli.config,
            "load_config",
            lambda: {"feedback": {"decay_window_days": "not-a-number"}},
        )

        # Must NOT crash — should fall back to 180.
        store = feedback_store.FeedbackStore()
        assert store._decay_window_days == 180


# ---------------------------------------------------------------------------
# TestDedup (STORE-04 — Plan 02 Task 1)
# ---------------------------------------------------------------------------


class TestDedup:
    """Same sha256 + same verdict → DUPLICATE (rejected, returns existing id)."""

    def test_duplicate_rejected(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        store = feedback_store.FeedbackStore()
        sha = "a" * 64
        ts0 = datetime(2026, 6, 24, 12, 0, 0, tzinfo=timezone.utc)
        ts1 = datetime(2026, 6, 24, 13, 0, 0, tzinfo=timezone.utc)
        rid_a = store.record_feedback(_make_record(sha256=sha, verdict="good", ts=ts0))
        rid_b = store.record_feedback(_make_record(sha256=sha, verdict="good", ts=ts1))

        # B is a DUPLICATE — same sha + same verdict. Must return A's id.
        assert rid_b == rid_a
        # Bucket file has only 1 line (A). B was rejected before append.
        bucket = home / "skills" / ".feedback" / "buckets" / "screenplay" / "cli.jsonl"
        lines = bucket.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1

    def test_duplicate_no_double_count(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        sha = "b" * 64
        ts0 = datetime(2026, 6, 24, 12, 0, 0, tzinfo=timezone.utc)
        ts1 = datetime(2026, 6, 24, 13, 0, 0, tzinfo=timezone.utc)
        store.record_feedback(_make_record(sha256=sha, verdict="good", ts=ts0))
        summary_after_a = store.summary()
        wc_a = summary_after_a["screenplay:cli:good"]["weighted_count"]

        store.record_feedback(_make_record(sha256=sha, verdict="good", ts=ts1))
        summary_after_b = store.summary()
        wc_b = summary_after_b["screenplay:cli:good"]["weighted_count"]

        # weighted_count must NOT have doubled.
        assert abs(wc_b - wc_a) < 0.01, (
            f"duplicate should not change weighted_count: {wc_a} -> {wc_b}"
        )

    def test_duplicate_returns_existing_record_id(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        sha = "c" * 64
        ts0 = datetime(2026, 6, 24, 12, 0, 0, tzinfo=timezone.utc)
        ts1 = datetime(2026, 6, 24, 13, 0, 0, tzinfo=timezone.utc)
        rid_a = store.record_feedback(_make_record(sha256=sha, ts=ts0))
        rid_b = store.record_feedback(_make_record(sha256=sha, ts=ts1))
        assert rid_b == rid_a

    def test_duplicate_does_not_append_registry(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        store = feedback_store.FeedbackStore()
        sha = "d" * 64
        ts0 = datetime(2026, 6, 24, 12, 0, 0, tzinfo=timezone.utc)
        ts1 = datetime(2026, 6, 24, 13, 0, 0, tzinfo=timezone.utc)
        store.record_feedback(_make_record(sha256=sha, ts=ts0))
        store.record_feedback(_make_record(sha256=sha, ts=ts1))

        registry = home / "skills" / ".feedback" / "dedup" / "sha256-registry.jsonl"
        lines = [
            l for l in registry.read_text(encoding="utf-8").splitlines() if l.strip()
        ]
        # Only 1 regular record line for this sha (no duplicate line appended).
        record_lines = [l for l in lines if '"event"' not in l]
        assert len(record_lines) == 1, (
            f"registry must have exactly 1 record line, got {len(record_lines)}: {record_lines}"
        )

    def test_new_sha256_always_writes(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        store = feedback_store.FeedbackStore()
        sha_x = "1" * 64
        sha_y = "2" * 64
        store.record_feedback(_make_record(sha256=sha_x, verdict="good"))
        store.record_feedback(_make_record(sha256=sha_y, verdict="good"))

        bucket = home / "skills" / ".feedback" / "buckets" / "screenplay" / "cli.jsonl"
        lines = bucket.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 2
        summary = store.summary()
        assert summary["screenplay:cli:good"]["count"] == 2


# ---------------------------------------------------------------------------
# TestCorrection (STORE-04 — Plan 02 Task 1)
# ---------------------------------------------------------------------------


class TestCorrection:
    """Same sha256 + DIFFERENT verdict → CORRECTION (older demoted, newer wins)."""

    def test_correction_demotes_older(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        sha = "e" * 64
        ts0 = datetime(2026, 6, 24, 12, 0, 0, tzinfo=timezone.utc)
        ts1 = datetime(2026, 6, 24, 13, 0, 0, tzinfo=timezone.utc)
        rid_a = store.record_feedback(
            _make_record(sha256=sha, verdict="good", ts=ts0)
        )
        rid_b = store.record_feedback(
            _make_record(sha256=sha, verdict="needs_work", ts=ts1)
        )

        # by_sha256[sha] now points at B (active) with A superseded.
        entry = store._sha256_index[sha]
        assert entry["record_id"] == rid_b
        assert entry["verdict"] == "needs_work"
        assert entry["status"] == "active"
        # A is in the superseded set.
        assert rid_a in store._superseded_record_ids

    def test_correction_weighted_count_older_bucket_drops(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        sha = "f" * 64
        ts0 = datetime(2026, 6, 24, 12, 0, 0, tzinfo=timezone.utc)
        ts1 = datetime(2026, 6, 24, 13, 0, 0, tzinfo=timezone.utc)
        store.record_feedback(_make_record(sha256=sha, verdict="good", ts=ts0))
        summary_after_a = store.summary()
        assert summary_after_a["screenplay:cli:good"]["weighted_count"] > 0
        # Now correct to needs_work.
        store.record_feedback(
            _make_record(sha256=sha, verdict="needs_work", ts=ts1)
        )
        summary_after_b = store.summary()
        # Older (good) bucket weighted_count dropped to 0 (only record superseded).
        assert summary_after_b["screenplay:cli:good"]["weighted_count"] == 0
        # Raw count UNCHANGED (audit).
        assert summary_after_b["screenplay:cli:good"]["count"] == 1

    def test_correction_weighted_count_newer_bucket_gains(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        sha = "10" + "0" * 62  # 64 chars
        ts0 = datetime(2026, 6, 24, 12, 0, 0, tzinfo=timezone.utc)
        ts1 = datetime(2026, 6, 24, 13, 0, 0, tzinfo=timezone.utc)
        store.record_feedback(_make_record(sha256=sha, verdict="good", ts=ts0))
        store.record_feedback(
            _make_record(sha256=sha, verdict="needs_work", ts=ts1)
        )
        summary = store.summary()
        # Newer bucket gains the new record's weight (~1.0 for fresh record).
        assert summary["screenplay:cli:needs_work"]["weighted_count"] > 0
        assert summary["screenplay:cli:needs_work"]["count"] == 1

    def test_correction_query_excludes_superseded_by_default(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        sha = "11" + "0" * 62
        ts0 = datetime(2026, 6, 24, 12, 0, 0, tzinfo=timezone.utc)
        ts1 = datetime(2026, 6, 24, 13, 0, 0, tzinfo=timezone.utc)
        store.record_feedback(_make_record(sha256=sha, verdict="good", ts=ts0))
        store.record_feedback(
            _make_record(sha256=sha, verdict="needs_work", ts=ts1)
        )

        # good bucket: A is superseded → empty.
        good_results = store.query(skill_id="screenplay", verdict="good")
        assert good_results == []
        # needs_work bucket: B active → 1 record.
        nw_results = store.query(skill_id="screenplay", verdict="needs_work")
        assert len(nw_results) == 1

    def test_correction_query_include_superseded(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        sha = "12" + "0" * 62
        ts0 = datetime(2026, 6, 24, 12, 0, 0, tzinfo=timezone.utc)
        ts1 = datetime(2026, 6, 24, 13, 0, 0, tzinfo=timezone.utc)
        store.record_feedback(_make_record(sha256=sha, verdict="good", ts=ts0))
        store.record_feedback(
            _make_record(sha256=sha, verdict="needs_work", ts=ts1)
        )

        results = store.query(skill_id="screenplay", include_superseded=True)
        assert len(results) == 2

    def test_correction_chain_three_records(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        store = feedback_store.FeedbackStore()
        sha = "13" + "0" * 62
        t0 = datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)
        t1 = datetime(2026, 6, 24, 11, 0, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 6, 24, 12, 0, 0, tzinfo=timezone.utc)
        rid_a = store.record_feedback(_make_record(sha256=sha, verdict="good", ts=t0))
        rid_b = store.record_feedback(
            _make_record(sha256=sha, verdict="needs_work", ts=t1)
        )
        rid_c = store.record_feedback(_make_record(sha256=sha, verdict="bad", ts=t2))

        # by_sha256[sha] points at C (active); A and B both superseded.
        entry = store._sha256_index[sha]
        assert entry["record_id"] == rid_c
        assert entry["verdict"] == "bad"
        assert rid_a in store._superseded_record_ids
        assert rid_b in store._superseded_record_ids
        # query verdicts: each verdict bucket returns only the latest active one.
        assert store.query(skill_id="screenplay", verdict="good") == []
        assert store.query(skill_id="screenplay", verdict="needs_work") == []
        assert len(store.query(skill_id="screenplay", verdict="bad")) == 1

    def test_correction_supersession_persists_across_reload(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        sha = "14" + "0" * 62
        t0 = datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)
        t1 = datetime(2026, 6, 24, 11, 0, 0, tzinfo=timezone.utc)
        store1 = feedback_store.FeedbackStore()
        rid_a = store1.record_feedback(_make_record(sha256=sha, verdict="good", ts=t0))
        rid_b = store1.record_feedback(
            _make_record(sha256=sha, verdict="needs_work", ts=t1)
        )

        # Fresh store simulates a process restart.
        store2 = feedback_store.FeedbackStore()
        entry = store2._sha256_index[sha]
        assert entry["record_id"] == rid_b
        assert entry["verdict"] == "needs_work"
        assert entry["status"] == "active"
        assert rid_a in store2._superseded_record_ids
        # query() on fresh store reflects correction.
        assert store2.query(skill_id="screenplay", verdict="good") == []
        assert len(store2.query(skill_id="screenplay", verdict="needs_work")) == 1


# ---------------------------------------------------------------------------
# TestRebuildIndex (STORE-02 — Plan 02 Task 1)
# ---------------------------------------------------------------------------


class TestRebuildIndex:
    """rebuild_index() regenerates index.json from buckets + registry."""

    def test_rebuild_index_idempotent(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        store = feedback_store.FeedbackStore()
        store.record_feedback(_make_record(sha256="1" * 64, verdict="good"))
        store.record_feedback(_make_record(sha256="2" * 64, verdict="good"))
        store.record_feedback(
            _make_record(skill_id="drawer", sha256="3" * 64, verdict="needs_work")
        )

        # Manually corrupt index.json (wipe buckets).
        index_path = home / "skills" / ".feedback" / "index.json"
        idx = json.loads(index_path.read_text(encoding="utf-8"))
        idx["buckets"] = {}
        idx["by_sha256"] = {}
        atomic_write_to(index_path, idx)

        store.rebuild_index()

        rebuilt = json.loads(index_path.read_text(encoding="utf-8"))
        # Two good in screenplay, one needs_work in drawer.
        assert rebuilt["buckets"]["screenplay:cli:good"]["count"] == 2
        assert rebuilt["buckets"]["drawer:cli:needs_work"]["count"] == 1
        assert rebuilt["buckets"]["screenplay:cli:good"]["weighted_count"] > 0

    def test_rebuild_index_clears_by_sha256(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        store = feedback_store.FeedbackStore()
        store.record_feedback(_make_record(sha256="4" * 64))
        store.record_feedback(_make_record(sha256="5" * 64))

        store.rebuild_index()

        registry = home / "skills" / ".feedback" / "dedup" / "sha256-registry.jsonl"
        index_path = home / "skills" / ".feedback" / "index.json"
        rebuilt = json.loads(index_path.read_text(encoding="utf-8"))
        # by_sha256 has both shas (from registry).
        assert "4" * 64 in rebuilt["by_sha256"]
        assert "5" * 64 in rebuilt["by_sha256"]

    def test_rebuild_index_empty_store(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        store = feedback_store.FeedbackStore()
        # No records yet.
        store.rebuild_index()
        index_path = home / "skills" / ".feedback" / "index.json"
        rebuilt = json.loads(index_path.read_text(encoding="utf-8"))
        assert rebuilt["version"] == 1
        assert rebuilt["buckets"] == {}
        assert rebuilt["by_sha256"] == {}

    def test_rebuild_index_preserves_supersession(self, feedback_env):
        feedback_store = feedback_env["feedback_store"]
        home = feedback_env["home"]
        store = feedback_store.FeedbackStore()
        sha = "15" + "0" * 62
        t0 = datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)
        t1 = datetime(2026, 6, 24, 11, 0, 0, tzinfo=timezone.utc)
        rid_a = store.record_feedback(_make_record(sha256=sha, verdict="good", ts=t0))
        rid_b = store.record_feedback(
            _make_record(sha256=sha, verdict="needs_work", ts=t1)
        )

        store.rebuild_index()

        index_path = home / "skills" / ".feedback" / "index.json"
        rebuilt = json.loads(index_path.read_text(encoding="utf-8"))
        entry = rebuilt["by_sha256"][sha]
        assert entry["record_id"] == rid_b
        assert entry["verdict"] == "needs_work"
        assert entry["status"] == "active"
        # The supersession event is in the registry.
        registry = home / "skills" / ".feedback" / "dedup" / "sha256-registry.jsonl"
        reg_lines = [
            l for l in registry.read_text(encoding="utf-8").splitlines() if l.strip()
        ]
        events = [json.loads(l) for l in reg_lines if '"event"' in l]
        assert any(
            e.get("event") == "superseded" and e.get("older_record_id") == rid_a
            for e in events
        )


# ---------------------------------------------------------------------------
# Helper: atomic write to index.json for test setup (corrupt-then-rebuild).
# ---------------------------------------------------------------------------


def atomic_write_to(path: Path, data: dict) -> None:
    """Test helper: atomic JSON write (mirrors utils.atomic_json_write)."""
    import tempfile

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
