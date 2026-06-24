"""Tests for write_feedback_record() atomic persistence (INGEST-01/02/03 foundation).

Verifies that validated FeedbackRecord instances land under
``<HERMES_HOME>/skills/.feedback/incoming/`` with sortable collision-resistant
filenames, that the directory chain is created lazily, and that round-trip
JSON persistence preserves the record. Also covers the JSONL fixtures
(``valid_10.jsonl`` etc.) used by Plan 02's batch importer tests.

The ``feedback_env`` fixture isolates HERMES_HOME via monkeypatch +
``importlib.reload`` — same pattern as ``tests/agent/test_curator_reports.py``.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


@pytest.fixture
def feedback_env(tmp_path, monkeypatch):
    """Isolated HERMES_HOME + reloaded feedback_ingest module.

    Mirrors the ``curator_env`` pattern in ``tests/agent/test_curator_reports.py``:
    monkeypatch HERMES_HOME to a tmp_path, reload hermes_constants so its
    home cache picks up the new path, then reload agent.feedback_ingest so
    its ``get_hermes_home`` import rebinds.
    """
    home = tmp_path / ".hermes"
    home.mkdir()
    (home / "skills").mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    # Reload hermes_constants so get_hermes_home picks up the new env var.
    import hermes_constants
    importlib.reload(hermes_constants)
    # Reload the ingest module so its ``from hermes_constants import get_hermes_home``
    # rebinds to the reloaded function (which now reads the new HERMES_HOME).
    from agent import feedback_ingest
    importlib.reload(feedback_ingest)
    yield {
        "home": home,
        "feedback_ingest": feedback_ingest,
        "hermes_constants": hermes_constants,
    }


def _make_record(
    feedback_ingest_module,
    *,
    skill_id: str = "screenplay",
    source: str = "cli",
    verdict: str = "good",
    correction: str = "x",
    ts: datetime | None = None,
):
    """Build a minimal valid FeedbackRecord for write tests."""
    from agent.feedback_schema import FeedbackRecord, OutputSnapshot

    snap = OutputSnapshot(
        sha256="0" * 64,
        output_text="assistant output",
        prompt="user prompt",
        model="test-model",
        provider="openai",
        api_mode="chat_completions",
        params={"max_tokens": 1024},
        captured_at=datetime.now(timezone.utc),
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


class TestWriteFeedbackRecord:
    """write_feedback_record() behavior tests."""

    def test_write_creates_file_under_hermes_home(self, feedback_env):
        write_feedback_record = feedback_env["feedback_ingest"].write_feedback_record
        record = _make_record(feedback_env["feedback_ingest"])
        target = write_feedback_record(record)

        # File exists under <home>/skills/.feedback/incoming/
        expected_dir = feedback_env["home"] / "skills" / ".feedback" / "incoming"
        assert target.parent == expected_dir
        assert target.is_file()

    def test_filename_format(self, feedback_env):
        """Filename is ``{skill_id}_{source}_{ts_compact}.json`` sortable."""
        write_feedback_record = feedback_env["feedback_ingest"].write_feedback_record
        ts = datetime(2026, 6, 24, 12, 0, 0, 123456, tzinfo=timezone.utc)
        record = _make_record(
            feedback_env["feedback_ingest"],
            skill_id="screenplay",
            source="cli",
            ts=ts,
        )
        target = write_feedback_record(record)
        # Filename pattern: screenplay_cli_<sortable-ts>.json
        assert target.name.startswith("screenplay_cli_")
        assert target.name.endswith(".json")
        # ts_compact must be sortable ASCII (letters/digits only between prefix/suffix)
        ts_part = target.name[len("screenplay_cli_"):-len(".json")]
        assert all(c.isalnum() or c == "T" or c == "Z" for c in ts_part), (
            f"ts_compact must be sortable ASCII, got: {ts_part}"
        )

    def test_directory_created_lazily(self, feedback_env):
        """Clean HERMES_HOME with no .feedback/ tree doesn't crash."""
        write_feedback_record = feedback_env["feedback_ingest"].write_feedback_record
        record = _make_record(feedback_env["feedback_ingest"])
        # Directory doesn't exist yet (only skills/ was pre-created)
        feedback_dir = feedback_env["home"] / "skills" / ".feedback"
        assert not feedback_dir.exists()
        # Write succeeds and creates the chain
        target = write_feedback_record(record)
        assert target.is_file()
        assert feedback_dir.exists()

    def test_file_content_matches_model_dump(self, feedback_env):
        """Written JSON content matches record.model_dump(mode='json')."""
        write_feedback_record = feedback_env["feedback_ingest"].write_feedback_record
        record = _make_record(feedback_env["feedback_ingest"])
        target = write_feedback_record(record)
        with open(target, "r", encoding="utf-8") as f:
            on_disk = json.load(f)
        assert on_disk == record.model_dump(mode="json")

    def test_no_tmp_files_left(self, feedback_env):
        """Atomic write leaves no .tmp files in the directory."""
        write_feedback_record = feedback_env["feedback_ingest"].write_feedback_record
        record = _make_record(feedback_env["feedback_ingest"])
        write_feedback_record(record)
        incoming = feedback_env["home"] / "skills" / ".feedback" / "incoming"
        files = list(incoming.iterdir())
        tmp_files = [f for f in files if f.suffix == ".tmp" or f.name.startswith(".")]
        assert not tmp_files, f"unexpected tmp files left: {tmp_files}"

    def test_round_trip_jsonl_compat(self, feedback_env):
        """Write -> read -> reconstruct equals original record."""
        write_feedback_record = feedback_env["feedback_ingest"].write_feedback_record
        from agent.feedback_schema import FeedbackRecord

        record = _make_record(feedback_env["feedback_ingest"])
        target = write_feedback_record(record)
        with open(target, "r", encoding="utf-8") as f:
            parsed = json.load(f)
        reconstructed = FeedbackRecord(**parsed)
        assert reconstructed == record, "round-trip must preserve the record"

    def test_uses_atomic_json_write(self, feedback_env):
        """Implementation MUST call utils.atomic_json_write (not open().write())."""
        # Source inspection — atomic_json_write must be referenced in the module.
        import agent.feedback_ingest as mod
        source = open(mod.__file__, encoding="utf-8").read()
        assert "atomic_json_write" in source, (
            "write_feedback_record must use utils.atomic_json_write "
            "(source inspection — Pattern 3 from RESEARCH)"
        )

    def test_no_path_home_usage(self, feedback_env):
        """Path.home() is forbidden in feedback_ingest (CLAUDE.md anti-pattern)."""
        import agent.feedback_ingest as mod
        source = open(mod.__file__, encoding="utf-8").read()
        # Strip comment lines before checking
        stripped = "\n".join(
            line for line in source.splitlines()
            if not line.strip().startswith("#")
        )
        assert "Path.home()" not in stripped, (
            "Path.home() is forbidden — use get_hermes_home() instead"
        )

    def test_uses_get_hermes_home(self, feedback_env):
        """Implementation must resolve paths via get_hermes_home()."""
        import agent.feedback_ingest as mod
        source = open(mod.__file__, encoding="utf-8").read()
        assert "get_hermes_home" in source, (
            "paths must resolve via get_hermes_home() per CLAUDE.md"
        )

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="POSIX permission test — Windows has no chmod 0500",
    )
    def test_rejects_when_hermes_home_unwritable(self, feedback_env, monkeypatch):
        """Unwritable parent dir raises OSError, not silent failure."""
        # Make skills/ read-only so mkdir under it fails
        skills_dir = feedback_env["home"] / "skills"
        try:
            os.chmod(skills_dir, 0o500)  # r-x for owner
            write_feedback_record = feedback_env["feedback_ingest"].write_feedback_record
            record = _make_record(feedback_env["feedback_ingest"])
            with pytest.raises((OSError, PermissionError)):
                write_feedback_record(record)
        finally:
            # Restore so tmp_path cleanup works
            os.chmod(skills_dir, 0o700)


class TestJsonlFixtures:
    """Validate the JSONL fixtures created for Plan 02 batch importer tests."""

    FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "feedback"

    def test_valid_10_has_10_lines(self):
        path = self.FIXTURES_DIR / "valid_10.jsonl"
        assert path.is_file(), f"missing fixture: {path}"
        lines = [
            l for l in path.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")
        ]
        assert len(lines) == 10, f"expected 10 valid records, got {len(lines)}"

    def test_valid_10_each_line_is_json(self):
        path = self.FIXTURES_DIR / "valid_10.jsonl"
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip() or line.startswith("#"):
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                pytest.fail(f"valid_10.jsonl line {i}: invalid JSON: {exc}")

    def test_valid_10_each_line_validates_as_feedback_record(self):
        """Each record must pass Pydantic validation (full cold-start check)."""
        from agent.feedback_schema import FeedbackRecord

        path = self.FIXTURES_DIR / "valid_10.jsonl"
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip() or line.startswith("#"):
                continue
            raw = json.loads(line)
            try:
                FeedbackRecord(**raw)
            except Exception as exc:
                pytest.fail(f"valid_10.jsonl line {i} failed validation: {exc}")

    def test_invalid_verdict_has_3_lines(self):
        path = self.FIXTURES_DIR / "invalid_verdict.jsonl"
        assert path.is_file(), f"missing fixture: {path}"
        lines = path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 3, f"expected 3 lines, got {len(lines)}"

    def test_invalid_verdict_line_2_has_bad_verdict(self):
        """Line 2 must be JSON-parseable but fail verdict validation."""
        path = self.FIXTURES_DIR / "invalid_verdict.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines()
        # Line 2 (index 1) must parse as JSON but have verdict != the enum
        parsed = json.loads(lines[1])
        assert parsed.get("verdict") not in {"good", "needs_work", "bad"}, (
            f"line 2 verdict must be invalid, got: {parsed.get('verdict')}"
        )

    def test_invalid_skill_has_3_lines(self):
        path = self.FIXTURES_DIR / "invalid_skill.jsonl"
        assert path.is_file(), f"missing fixture: {path}"
        lines = path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 3, f"expected 3 lines, got {len(lines)}"

    def test_invalid_skill_line_2_has_unknown_skill_id(self):
        """Line 2 must be JSON-parseable but fail skill_id validation."""
        path = self.FIXTURES_DIR / "invalid_skill.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines()
        parsed = json.loads(lines[1])
        from agent.feedback_schema import _KNOWN_EXPERT_IDS

        assert parsed.get("skill_id") not in _KNOWN_EXPERT_IDS, (
            f"line 2 skill_id must be unknown, got: {parsed.get('skill_id')}"
        )

    def test_invalid_verdict_lines_1_and_3_are_valid(self):
        """Lines 1 and 3 must validate cleanly (only line 2 is bad)."""
        from agent.feedback_schema import FeedbackRecord

        path = self.FIXTURES_DIR / "invalid_verdict.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines()
        for idx in (0, 2):
            raw = json.loads(lines[idx])
            try:
                FeedbackRecord(**raw)
            except Exception as exc:
                pytest.fail(
                    f"invalid_verdict.jsonl line {idx + 1} should be valid: {exc}"
                )

    def test_invalid_skill_lines_1_and_3_are_valid(self):
        """Lines 1 and 3 must validate cleanly (only line 2 is bad)."""
        from agent.feedback_schema import FeedbackRecord

        path = self.FIXTURES_DIR / "invalid_skill.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines()
        for idx in (0, 2):
            raw = json.loads(lines[idx])
            try:
                FeedbackRecord(**raw)
            except Exception as exc:
                pytest.fail(
                    f"invalid_skill.jsonl line {idx + 1} should be valid: {exc}"
                )
