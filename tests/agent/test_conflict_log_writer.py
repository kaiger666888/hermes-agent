"""Tests for ``agent.memory_arbitration.append_conflict_record`` (Phase 53 Task 2).

The JSONL writer must be:
- line-delimited (one record per line; each line is self-contained JSON)
- parent-creating (mkdir parents=True)
- fsync'd (one ``os.fsync`` per append, for durability)
- UTF-8 faithful (no ``\\uXXXX`` escape corruption of Chinese / Δ / etc.)
- path-aligned to ``.runtime/{slug}/round_tables/{round_id}/conflicts.jsonl``
  relative to ``HERMES_HOME / "agents"`` (CONTEXT.md decision #5)

Per ``02-ROUND-TABLE-PROTOCOL.md §3.5`` + ``06-CROSS-REPO-IMPACT.md §5.1``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def memory_module():
    from agent import memory_arbitration
    return memory_arbitration


# ── Test 1: parent dir creation ─────────────────────────────────────────────


class TestAppendConflictRecord:
    def test_append_creates_file_with_parents(self, memory_module, tmp_path):
        target = tmp_path / "x" / "y" / "z" / "round_abc" / "conflicts.jsonl"
        memory_module.append_conflict_record(target, {"a": 1})
        assert target.exists()
        assert target.parent.is_dir()
        # The parent of the .jsonl must be the deep round_tables dir
        assert target.parent.name == "round_abc"

    def test_append_writes_one_jsonl_line_per_record(self, memory_module, tmp_path):
        target = tmp_path / "rt" / "conflicts.jsonl"
        for i in range(3):
            memory_module.append_conflict_record(
                target, {"i": i, "note": f"record {i}"}
            )
        text = target.read_text(encoding="utf-8")
        lines = text.splitlines()
        assert len(lines) == 3
        for idx, ln in enumerate(lines):
            parsed = json.loads(ln)
            assert parsed["i"] == idx

    def test_append_is_atomic_per_line(self, memory_module, tmp_path):
        """Each appended line is self-contained JSON (no half-record states)."""
        target = tmp_path / "atom" / "conflicts.jsonl"
        memory_module.append_conflict_record(target, {"first": True})
        # Without "closing" anything (each append opens/writes/closes its own
        # handle), append another record.
        memory_module.append_conflict_record(target, {"second": True})
        lines = target.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 2
        # Both lines parse cleanly and independently
        first = json.loads(lines[0])
        second = json.loads(lines[1])
        assert first == {"first": True}
        assert second == {"second": True}

    def test_record_preserves_unicode_and_non_ascii(self, memory_module, tmp_path):
        """Critical: conflict records may contain Chinese / Δ / em-dash;
        ensure_ascii=False keeps these intact rather than emitting ``\\uXXXX``."""
        target = tmp_path / "uni" / "conflicts.jsonl"
        record = {
            "note": "中文字符 — Δconfidence < 0.05",
            "rationale": "Tie at project scope; deferred to operator.",
        }
        memory_module.append_conflict_record(target, record)
        raw = target.read_text(encoding="utf-8")
        # The Chinese chars + Δ + em-dash MUST appear verbatim (no \uXXXX escape)
        assert "中文字符" in raw
        assert "Δconfidence" in raw
        assert "—" in raw
        parsed = json.loads(raw.strip())
        assert parsed["note"] == record["note"]

    def test_path_convention_under_hermes_home(self, memory_module, tmp_path, monkeypatch):
        """When caller uses the canonical path convention (CONTEXT.md #5),
        the file lands at HERMES_HOME/agents/.runtime/{slug}/round_tables/{round_id}/conflicts.jsonl."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        from hermes_constants import get_hermes_home
        hh = get_hermes_home()
        target = (
            hh
            / "agents"
            / ".runtime"
            / "volvo-2026"
            / "round_tables"
            / "round-xyz"
            / "conflicts.jsonl"
        )
        memory_module.append_conflict_record(target, {"resolution": "deferred-to-operator"})
        assert target.exists()
        # Sanity: resolve against the redirected HERMES_HOME, not real ~/.hermes
        assert str(target).startswith(str(tmp_path))

    def test_fsync_called(self, memory_module, tmp_path, monkeypatch):
        """Each append invokes os.fsync exactly once for durability."""
        target = tmp_path / "fsync" / "conflicts.jsonl"
        with patch("agent.memory_arbitration.os.fsync") as mock_fsync:
            memory_module.append_conflict_record(target, {"a": 1})
        assert mock_fsync.call_count == 1
