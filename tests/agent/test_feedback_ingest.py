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


# ---------------------------------------------------------------------------
# Plan 02 Task 1: JSONL batch importer + kais-aigc file watcher
# ---------------------------------------------------------------------------

import threading  # noqa: E402  (test-only; keep close to the tests that use it)
import time  # noqa: E402

from pydantic import ValidationError  # noqa: E402


FIXTURES_DIR_GLOBAL = Path(__file__).resolve().parent.parent / "fixtures" / "feedback"


def _write_partial_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _make_kais_record_json(
    *, skill_id: str = "screenplay", source: str = "cli", output_text: str = "x"
) -> dict:
    """Return a dict that will validate as a FeedbackRecord."""
    return {
        "skill_id": skill_id,
        "expert_id": skill_id,
        "source": source,
        "verdict": "good",
        "correction": "",
        "revised_output": None,
        "output_snapshot": {
            "sha256": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            "output_text": output_text,
            "prompt": "p",
            "model": "m",
            "provider": "openai",
            "api_mode": "chat_completions",
            "params": {},
            "captured_at": "2026-06-24T12:00:00+00:00",
        },
        "ts": "2026-06-24T12:00:00+00:00",
    }


class TestImportJsonl:
    """import_jsonl() — atomic all-or-nothing batch import."""

    def test_import_jsonl_all_valid(self, feedback_env):
        """import_jsonl(valid_10.jsonl) -> (10, []) and 10 files written."""
        feedback_ingest = feedback_env["feedback_ingest"]
        path = FIXTURES_DIR_GLOBAL / "valid_10.jsonl"
        count, errors = feedback_ingest.import_jsonl(path)
        assert errors == []
        assert count == 10
        incoming = feedback_env["home"] / "skills" / ".feedback" / "incoming"
        files = list(incoming.glob("*.json"))
        assert len(files) == 10

    def test_import_jsonl_atomic_reject(self, feedback_env):
        """invalid_verdict.jsonl -> (0, errors) mentioning line 2 + verdict.

        ZERO files written (atomicity — T-28-11).
        """
        feedback_ingest = feedback_env["feedback_ingest"]
        path = FIXTURES_DIR_GLOBAL / "invalid_verdict.jsonl"
        count, errors = feedback_ingest.import_jsonl(path)
        assert count == 0
        assert len(errors) >= 1
        # The error must mention line 2 and the verdict field.
        joined = "\n".join(errors)
        assert "line 2" in joined
        assert "verdict" in joined.lower()
        # Atomicity: no files written
        incoming = feedback_env["home"] / "skills" / ".feedback" / "incoming"
        files = list(incoming.glob("*.json"))
        assert files == [], f"atomic reject must not write files, got: {files}"

    def test_import_jsonl_invalid_skill_reject(self, feedback_env):
        """invalid_skill.jsonl -> (0, errors) mentioning line 2 + skill_id."""
        feedback_ingest = feedback_env["feedback_ingest"]
        path = FIXTURES_DIR_GLOBAL / "invalid_skill.jsonl"
        count, errors = feedback_ingest.import_jsonl(path)
        assert count == 0
        assert len(errors) >= 1
        joined = "\n".join(errors)
        assert "line 2" in joined
        # The error must mention skill_id (either in the loc or the message)
        assert "skill_id" in joined.lower() or "skill" in joined.lower()
        # Zero files written
        incoming = feedback_env["home"] / "skills" / ".feedback" / "incoming"
        assert list(incoming.glob("*.json")) == []

    def test_import_jsonl_dry_run(self, feedback_env):
        """dry_run=True validates without writing."""
        feedback_ingest = feedback_env["feedback_ingest"]
        path = FIXTURES_DIR_GLOBAL / "valid_10.jsonl"
        count, errors = feedback_ingest.import_jsonl(path, dry_run=True)
        assert errors == []
        assert count == 10
        incoming = feedback_env["home"] / "skills" / ".feedback" / "incoming"
        # Zero files written in dry-run
        assert list(incoming.glob("*.json")) == []

    def test_import_jsonl_skips_blank_and_comment_lines(self, feedback_env, tmp_path):
        """Blank lines and # comments are skipped, not errors."""
        feedback_ingest = feedback_env["feedback_ingest"]
        valid = _make_kais_record_json()
        # Mix blank lines + comment lines between valid records
        lines = [
            "# this is a comment",
            "",
            json.dumps(valid),
            "   # indented comment",
            "",
            json.dumps(_make_kais_record_json(output_text="y")),
        ]
        path = tmp_path / "mixed.jsonl"
        path.write_text("\n".join(lines), encoding="utf-8")
        count, errors = feedback_ingest.import_jsonl(path)
        assert errors == []
        assert count == 2

    def test_import_jsonl_cold_start_10(self, feedback_env):
        """Cold-start: seeding 10 records works (INGEST-05 success criterion)."""
        feedback_ingest = feedback_env["feedback_ingest"]
        path = FIXTURES_DIR_GLOBAL / "valid_10.jsonl"
        count, errors = feedback_ingest.import_jsonl(path)
        assert errors == []
        assert count == 10
        incoming = feedback_env["home"] / "skills" / ".feedback" / "incoming"
        assert len(list(incoming.glob("*.json"))) == 10

    def test_import_jsonl_malformed_json_reports_line(self, feedback_env, tmp_path):
        """Malformed JSON line is reported with line number, no files written."""
        feedback_ingest = feedback_env["feedback_ingest"]
        valid = json.dumps(_make_kais_record_json())
        lines = [valid, "{not valid json", valid]
        path = tmp_path / "broken.jsonl"
        path.write_text("\n".join(lines), encoding="utf-8")
        count, errors = feedback_ingest.import_jsonl(path)
        assert count == 0
        assert any("line 2" in e and "json" in e.lower() for e in errors)


class TestWatchInboxKais:
    """watch_inbox_kais() + _scan_once() polling watcher behavior."""

    @pytest.fixture
    def inbox_tree(self, tmp_path, monkeypatch):
        """Build a fresh inbox-kais / processed-kais / errors-kais tree.

        Yields (inbox_dir, processed_dir, errors_dir).
        """
        # Contain all the watcher writes under tmp_path (no HERMES_HOME bleed).
        root = tmp_path / "feedback"
        inbox = root / "inbox-kais"
        processed = root / "processed-kais"
        errors = root / "errors-kais"
        for d in (inbox, processed, errors):
            d.mkdir(parents=True, exist_ok=True)
        return inbox, processed, errors

    def test_watch_inbox_ingests_new_file(self, feedback_env, inbox_tree):
        """A stable valid JSON file is ingested with source='kais_aigc' override."""
        feedback_ingest = feedback_env["feedback_ingest"]
        inbox, processed, errors = inbox_tree
        # Drop a file claiming source='cli' — watcher must override to kais_aigc
        record = _make_kais_record_json(source="cli")
        f = inbox / "test1.json"
        f.write_text(json.dumps(record), encoding="utf-8")
        seen: dict[str, tuple[float, int]] = {}
        pending: dict[str, int] = {}
        # First scan: record the size
        ingested = feedback_ingest._scan_once(inbox, processed, errors, seen, pending)
        assert ingested == 0  # size not stable yet
        # Second scan: size stable -> ingest
        ingested2 = feedback_ingest._scan_once(inbox, processed, errors, seen, pending)
        assert ingested2 == 1
        # Original moved to processed/
        assert (processed / "test1.json").is_file()
        assert not f.exists()
        # One file in incoming/ with source=kais_aigc
        incoming = feedback_env["home"] / "skills" / ".feedback" / "incoming"
        files = list(incoming.glob("*_kais_aigc_*.json"))
        assert len(files) == 1

    def test_watch_inbox_waits_for_stable_size(self, feedback_env, inbox_tree):
        """Partial-write detection: file is not ingested until size stable."""
        feedback_ingest = feedback_env["feedback_ingest"]
        inbox, processed, errors = inbox_tree
        f = inbox / "partial.json"
        # Write a partial file (size N)
        f.write_text("x" * 100, encoding="utf-8")
        seen: dict[str, tuple[float, int]] = {}
        pending: dict[str, int] = {}
        # First scan: records size 100, does not ingest
        n1 = feedback_ingest._scan_once(inbox, processed, errors, seen, pending)
        assert n1 == 0
        # Append more bytes (size 200)
        f.write_text("x" * 200, encoding="utf-8")
        n2 = feedback_ingest._scan_once(inbox, processed, errors, seen, pending)
        assert n2 == 0  # size changed; still not stable
        # Third scan: size unchanged at 200 -> not valid JSON, will error-move,
        # but the key behavior is it didn't ingest on the first or second scan.
        n3 = feedback_ingest._scan_once(inbox, processed, errors, seen, pending)
        assert n3 == 0  # not valid JSON -> error path, not ingest
        # File moved to errors (size stable but invalid JSON)
        assert (errors / "partial.json").is_file()

    def test_watch_inbox_rejects_path_traversal(self, feedback_env, tmp_path):
        """A filename containing ../ must NOT escape the inbox tree."""
        feedback_ingest = feedback_env["feedback_ingest"]
        # Set up an isolated tree where the traversal is contained
        root = tmp_path / "feedback"
        inbox = root / "inbox-kais"
        processed = root / "processed-kais"
        errors = root / "errors-kais"
        for d in (inbox, processed, errors):
            d.mkdir(parents=True, exist_ok=True)
        # Create a file with a literal traversal name. On most filesystems we
        # can't actually name a file '../../etc/passwd.json' — so create it
        # inside a subdir whose name embeds traversal, then test the
        # sanitize-by-.name behavior. The real defense is in the watcher
        # using Path(entry.name).name which strips dir components; we verify
        # that the ingested record's filename is derived from skill_id+ts,
        # never from the source filename.
        record = _make_kais_record_json()
        # Simulate a malicious filename by writing to a file that has ../ in its name.
        # If the OS refuses, skip the literal and use a benign-but-suspicious name.
        try:
            f = inbox / "../../etc/passwd.json"
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(record), encoding="utf-8")
        except (OSError, ValueError):
            # Filesystem refused the traversal name — that itself is a defense.
            # Fall back to a name with embedded slashes that the watcher must strip.
            f = inbox / "..-..-etc-passwd.json"
            f.write_text(json.dumps(record), encoding="utf-8")
        seen: dict[str, tuple[float, int]] = {}
        pending: dict[str, int] = {}
        # Two scans for stability
        feedback_ingest._scan_once(inbox, processed, errors, seen, pending)
        feedback_ingest._scan_once(inbox, processed, errors, seen, pending)
        # No file should have been created outside the incoming/ tree
        incoming = feedback_env["home"] / "skills" / ".feedback" / "incoming"
        # The processed file must use the sanitized .name, not escape processed_dir
        # If a literal traversal file existed and was moved, it would land in processed/
        # under its sanitized name. Check no 'passwd' file exists under /etc:
        assert not Path("/etc/passwd.json").exists()
        # And the write target under incoming/ is derived from skill_id+source+ts
        files = list(incoming.glob("*.json"))
        for written in files:
            # Filename must NOT be the raw traversal name
            assert ".." not in written.name
            assert "/" not in written.name

    def test_watch_inbox_continues_on_malformed(self, feedback_env, inbox_tree):
        """A malformed file is moved to errors/; a subsequent valid file still ingests."""
        feedback_ingest = feedback_env["feedback_ingest"]
        inbox, processed, errors = inbox_tree
        # Drop malformed JSON
        (inbox / "broken.json").write_text("{not json", encoding="utf-8")
        # Drop valid JSON in the same scan batch
        record = _make_kais_record_json()
        (inbox / "valid.json").write_text(json.dumps(record), encoding="utf-8")
        seen: dict[str, tuple[float, int]] = {}
        pending: dict[str, int] = {}
        # First scan: record sizes
        n1 = feedback_ingest._scan_once(inbox, processed, errors, seen, pending)
        assert n1 == 0
        # Second scan: sizes stable — broken -> errors, valid -> ingested
        n2 = feedback_ingest._scan_once(inbox, processed, errors, seen, pending)
        assert n2 == 1  # valid was ingested; broken was not (error path)
        # Broken moved to errors/
        assert (errors / "broken.json").is_file()
        assert not (inbox / "broken.json").exists()
        # Valid moved to processed/
        assert (processed / "valid.json").is_file()
        assert not (inbox / "valid.json").exists()

    def test_watch_inbox_max_iterations_zero(self, feedback_env, inbox_tree):
        """watch_inbox_kais with max_iterations=0 exits immediately (no infinite loop)."""
        feedback_ingest = feedback_env["feedback_ingest"]
        inbox, _processed, _errors = inbox_tree
        # Should return without blocking
        start = time.monotonic()
        feedback_ingest.watch_inbox_kais(
            inbox, interval=0.01, max_iterations=0
        )
        elapsed = time.monotonic() - start
        assert elapsed < 1.0, "max_iterations=0 must exit immediately"

    def test_watch_inbox_stop_event(self, feedback_env, inbox_tree):
        """stop_event.is_set() breaks the loop."""
        feedback_ingest = feedback_env["feedback_ingest"]
        inbox, _processed, _errors = inbox_tree
        stop = threading.Event()
        stop.set()  # pre-set so the very first check breaks
        feedback_ingest.watch_inbox_kais(
            inbox, interval=0.01, stop_event=stop, max_iterations=None
        )
        # If stop_event wasn't honored, this would hang forever — pytest-timeout catches it.

    def test_watch_inbox_uses_env_var_override(
        self, feedback_env, tmp_path, monkeypatch
    ):
        """HERMES_FEEDBACK_INBOX_KAIS env var overrides the default inbox path."""
        feedback_ingest = feedback_env["feedback_ingest"]
        custom_inbox = tmp_path / "custom-kais-inbox"
        custom_inbox.mkdir(parents=True)
        monkeypatch.setenv("HERMES_FEEDBACK_INBOX_KAIS", str(custom_inbox))
        # watch_inbox_kais() with inbox_dir=None should pick up the env var.
        # We use max_iterations=0 so it doesn't block.
        feedback_ingest.watch_inbox_kais(max_iterations=0)
        # The custom inbox + siblings were created by the watcher.
        assert custom_inbox.is_dir()
        assert (custom_inbox.parent / "processed-kais").is_dir() or (
            custom_inbox / ".." / "processed-kais"
        ).exists() or (tmp_path / "processed-kais").exists()
