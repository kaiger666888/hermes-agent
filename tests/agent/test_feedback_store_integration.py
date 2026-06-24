"""Integration tests for Phase 28→29 delegation.

Verifies that ``write_feedback_record`` (Phase 28 entry point) delegates
correctly to :class:`agent.feedback_store.FeedbackStore` (Phase 29), and
that every Phase 28 caller (/feedback slash command, kais watcher, JSONL
importer, hermes feedback submit) continues to work via the delegation.

These tests complement the unit tests in ``test_feedback_store.py`` and
``test_feedback_ingest.py`` by exercising the FULL delegation path
end-to-end (Phase 28 caller → write_feedback_record wrapper →
FeedbackStore.record_feedback → on-disk persistence).

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 unions.
  - ``encoding="utf-8"`` on every ``open()`` (Ruff PLW1514).
  - ``get_hermes_home()`` for path resolution.
"""

from __future__ import annotations

import argparse
import importlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Shared fixture (mirrors test_feedback_ingest.py feedback_env — Phase 29
# reloads BOTH feedback_ingest AND feedback_store so the delegation chain
# resolves get_hermes_home against the isolated HERMES_HOME).
# ---------------------------------------------------------------------------


@pytest.fixture
def feedback_env(tmp_path, monkeypatch):
    """Isolated HERMES_HOME + reloaded feedback_ingest + feedback_store."""
    home = tmp_path / ".hermes"
    home.mkdir()
    (home / "skills").mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    import hermes_constants
    importlib.reload(hermes_constants)
    # CRITICAL: feedback_store MUST be reloaded before feedback_ingest so
    # the delegation chain picks up the new HERMES_HOME.
    from agent import feedback_store
    importlib.reload(feedback_store)
    from agent import feedback_ingest
    importlib.reload(feedback_ingest)
    yield {
        "home": home,
        "feedback_ingest": feedback_ingest,
        "feedback_store": feedback_store,
        "hermes_constants": hermes_constants,
    }


def _make_record(
    *,
    skill_id: str = "screenplay",
    source: str = "cli",
    verdict: str = "good",
    correction: str = "x",
    sha256: str = "0" * 64,
    ts: datetime | None = None,
):
    """Build a minimal valid FeedbackRecord for integration tests."""
    from agent.feedback_schema import FeedbackRecord, OutputSnapshot

    snap = OutputSnapshot(
        sha256=sha256,
        output_text="assistant output",
        prompt="user prompt",
        model="test-model",
        provider="openai",
        api_mode="chat_completions",
        params={"max_tokens": 1024},
        captured_at=ts or datetime.now(timezone.utc),
    )
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
# TestDelegation — Phase 28 write_feedback_record → FeedbackStore
# ---------------------------------------------------------------------------


class TestDelegation:
    """Phase 28 write_feedback_record delegates to FeedbackStore.record_feedback.

    Covers STORE-02 delegation contract: signature preserved, callers
    unchanged, records land in buckets/<skill_id>/<source>.jsonl.
    """

    def test_write_feedback_record_returns_path(self, feedback_env):
        """Return type is Path (backward compat with Phase 28 callers)."""
        feedback_ingest = feedback_env["feedback_ingest"]
        record = _make_record()
        target = feedback_ingest.write_feedback_record(record)
        assert isinstance(target, Path), (
            f"write_feedback_record must return Path for backward compat, got {type(target)}"
        )

    def test_write_feedback_record_routes_to_store(self, feedback_env):
        """Record lands in buckets/<skill_id>/<source>.jsonl (NOT incoming/)."""
        feedback_ingest = feedback_env["feedback_ingest"]
        home = feedback_env["home"]
        record = _make_record(skill_id="screenplay", source="cli")
        feedback_ingest.write_feedback_record(record)

        bucket = (
            home / "skills" / ".feedback" / "buckets" / "screenplay" / "cli.jsonl"
        )
        assert bucket.is_file(), f"bucket file must exist: {bucket}"
        lines = [
            l for l in bucket.read_text(encoding="utf-8").splitlines() if l.strip()
        ]
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["skill_id"] == "screenplay"
        assert parsed["source"] == "cli"

    def test_write_feedback_record_no_incoming_file(self, feedback_env):
        """Delegation abandons Phase 28 incoming/ layout — no file created there."""
        feedback_ingest = feedback_env["feedback_ingest"]
        home = feedback_env["home"]
        feedback_ingest.write_feedback_record(_make_record())

        incoming = home / "skills" / ".feedback" / "incoming"
        # Either the dir doesn't exist OR it's empty — delegation never writes
        # to incoming/ (the Phase 28 flat layout is abandoned).
        if incoming.is_dir():
            assert list(incoming.glob("*.json")) == [], (
                f"delegation must NOT write to incoming/, found: {list(incoming.glob('*.json'))}"
            )

    def test_phase28_import_jsonl_works(self, feedback_env, tmp_path):
        """import_jsonl routes through delegation; records land in buckets/.

        Phase 28's JSONL batch importer loops ``write_feedback_record``.
        After delegation, each record lands in buckets/ — the loop is
        transparent to the importer.
        """
        feedback_ingest = feedback_env["feedback_ingest"]
        home = feedback_env["home"]
        # Build a 3-record JSONL fixture inline.
        records = [
            _make_record(skill_id="screenplay", source="cli", sha256=f"{i}" * 64)
            for i in range(1, 4)
        ]
        fixture = tmp_path / "test.jsonl"
        fixture.write_text(
            "\n".join(r.model_dump_json() for r in records), encoding="utf-8"
        )

        count, errors = feedback_ingest.import_jsonl(fixture)
        assert errors == []
        assert count == 3

        bucket = home / "skills" / ".feedback" / "buckets" / "screenplay" / "cli.jsonl"
        assert bucket.is_file()
        lines = [l for l in bucket.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(lines) == 3

    def test_phase28_watcher_scan_once_works(self, feedback_env, tmp_path):
        """_scan_once routes through delegation; record lands in buckets/.

        Phase 28's kais-aigc watcher _scan_once helper calls
        write_feedback_record. After delegation, the record lands in
        buckets/<skill_id>/kais_aigc.jsonl. Anti-spoofing source override
        (T-28-07) still applies.
        """
        feedback_ingest = feedback_env["feedback_ingest"]
        home = feedback_env["home"]
        # Build watcher tree.
        watcher_root = tmp_path / "watcher"
        inbox = watcher_root / "inbox-kais"
        processed = watcher_root / "processed-kais"
        errors = watcher_root / "errors-kais"
        for d in (inbox, processed, errors):
            d.mkdir(parents=True, exist_ok=True)

        # Drop a file claiming source='cli' — watcher must override to kais_aigc.
        record_dict = {
            "skill_id": "screenplay",
            "expert_id": "screenplay",
            "source": "cli",  # will be overridden
            "verdict": "good",
            "correction": "",
            "revised_output": None,
            "output_snapshot": {
                "sha256": "9" * 64,
                "output_text": "x",
                "prompt": "p",
                "model": "m",
                "provider": "openai",
                "api_mode": "chat_completions",
                "params": {},
                "captured_at": "2026-06-24T12:00:00+00:00",
            },
            "ts": "2026-06-24T12:00:00+00:00",
        }
        (inbox / "test.json").write_text(json.dumps(record_dict), encoding="utf-8")

        seen: dict[str, tuple[float, int]] = {}
        pending: dict[str, int] = {}
        # Two scans for stability.
        feedback_ingest._scan_once(inbox, processed, errors, seen, pending)
        feedback_ingest._scan_once(inbox, processed, errors, seen, pending)

        # Record landed in buckets/screenplay/kais_aigc.jsonl with source override.
        bucket = (
            home / "skills" / ".feedback" / "buckets" / "screenplay" / "kais_aigc.jsonl"
        )
        assert bucket.is_file(), f"bucket must exist: {bucket}"
        lines = [l for l in bucket.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["source"] == "kais_aigc"  # anti-spoofing override
        # Original moved to processed/.
        assert (processed / "test.json").is_file()

    def test_phase28_tests_still_pass(self, feedback_env):
        """Regression: Phase 28 ingest test file runs green after delegation.

        This is a meta-test: we run a representative Phase 28 test
        (test_write_creates_file_under_hermes_home) via the delegation
        path. The test file itself has been updated to assert buckets/
        layout (Plan 02 Task 2). This integration test serves as a
        canary: if the delegation breaks, this fails before the regression
        test file does.
        """
        feedback_ingest = feedback_env["feedback_ingest"]
        home = feedback_env["home"]
        feedback_ingest.write_feedback_record(_make_record())

        # The updated Phase 28 test asserts the bucket layout. Mirror its
        # key invariants here so a delegation regression is caught locally.
        bucket = (
            home / "skills" / ".feedback" / "buckets" / "screenplay" / "cli.jsonl"
        )
        assert bucket.is_file()
        assert bucket.parent.name == "screenplay"
        assert bucket.name == "cli.jsonl"


# ---------------------------------------------------------------------------
# TestRebuildIndexCLI — hermes feedback rebuild-index subcommand
# ---------------------------------------------------------------------------


class TestRebuildIndexCLI:
    """``hermes feedback rebuild-index`` CLI subcommand.

    Mirrors the TestCmdImport pattern: build an argparse.Namespace, call
    _cmd_rebuild_index directly. Avoids the full HermesCLI boot.
    """

    def test_rebuild_index_subcommand_present(self):
        """register_cli adds a 'rebuild-index' subparser."""
        from hermes_cli.feedback import register_cli

        parser = argparse.ArgumentParser(prog="hermes feedback")
        register_cli(parser)
        assert parser._subparsers is not None
        subs_action = parser._subparsers._group_actions[0]
        names = set(subs_action.choices.keys())
        assert "rebuild-index" in names, (
            f"rebuild-index must be registered, got: {names}"
        )

    def test_rebuild_index_runs(self, feedback_env):
        """Populate buckets + run _cmd_rebuild_index; index.json has correct counts."""
        import argparse as ap  # noqa: F401 (shadowed by arg below)
        feedback_ingest = feedback_env["feedback_ingest"]
        home = feedback_env["home"]

        # Write 3 records across 2 buckets.
        feedback_ingest.write_feedback_record(
            _make_record(skill_id="screenplay", source="cli", verdict="good", sha256="1" * 64)
        )
        feedback_ingest.write_feedback_record(
            _make_record(skill_id="screenplay", source="cli", verdict="good", sha256="2" * 64)
        )
        feedback_ingest.write_feedback_record(
            _make_record(
                skill_id="drawer", source="cli", verdict="needs_work", sha256="3" * 64
            )
        )

        # Manually corrupt index.json (wipe buckets).
        index_path = home / "skills" / ".feedback" / "index.json"
        idx = json.loads(index_path.read_text(encoding="utf-8"))
        idx["buckets"] = {}
        idx["by_sha256"] = {}
        # Atomic write helper (same pattern as test_feedback_store.py).
        import os
        import tempfile

        fd, tmp = tempfile.mkstemp(dir=str(index_path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(idx, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, index_path)
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass

        # Run rebuild-index CLI.
        from hermes_cli.feedback import _cmd_rebuild_index

        ns = argparse.Namespace()
        rc = _cmd_rebuild_index(ns)
        assert rc == 0

        rebuilt = json.loads(index_path.read_text(encoding="utf-8"))
        # Counts should match what we wrote.
        assert rebuilt["buckets"]["screenplay:cli:good"]["count"] == 2
        assert rebuilt["buckets"]["drawer:cli:needs_work"]["count"] == 1
        assert rebuilt["buckets"]["screenplay:cli:good"]["weighted_count"] > 0

    def test_rebuild_index_empty_store(self, feedback_env):
        """rebuild-index on empty store returns 0 + valid empty index."""
        from hermes_cli.feedback import _cmd_rebuild_index

        ns = argparse.Namespace()
        rc = _cmd_rebuild_index(ns)
        assert rc == 0

        index_path = feedback_env["home"] / "skills" / ".feedback" / "index.json"
        rebuilt = json.loads(index_path.read_text(encoding="utf-8"))
        assert rebuilt["version"] == 1
        assert rebuilt["buckets"] == {}
        assert rebuilt["by_sha256"] == {}

    def test_rebuild_index_idempotent(self, feedback_env):
        """Running rebuild-index twice produces identical index.json."""
        feedback_ingest = feedback_env["feedback_ingest"]
        home = feedback_env["home"]
        feedback_ingest.write_feedback_record(
            _make_record(sha256="1" * 64)
        )
        feedback_ingest.write_feedback_record(
            _make_record(sha256="2" * 64)
        )

        from hermes_cli.feedback import _cmd_rebuild_index

        ns = argparse.Namespace()
        rc1 = _cmd_rebuild_index(ns)
        assert rc1 == 0
        index_path = home / "skills" / ".feedback" / "index.json"
        first = index_path.read_text(encoding="utf-8")

        rc2 = _cmd_rebuild_index(ns)
        assert rc2 == 0
        second = index_path.read_text(encoding="utf-8")

        # Bucket counts + by_sha256 keys identical (timestamps may differ).
        first_idx = json.loads(first)
        second_idx = json.loads(second)
        assert first_idx["buckets"] == second_idx["buckets"]
        assert set(first_idx["by_sha256"].keys()) == set(
            second_idx["by_sha256"].keys()
        )
