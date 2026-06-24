"""Audit log module tests (CURATE-04) — sha256 chain append/verify/query.

Covers the LOCKED formula from CONTEXT.md §"Audit Trail Format":
``entry_sha256 = sha256(prev_sha256 + json.dumps({k:v for k,v in entry.items()
if k != "entry_sha256"}, sort_keys=True, separators=(",",":"),
ensure_ascii=False))``

Pitfall #2 (serialization drift) is mitigated by the single
``_serialize_entry_for_sha256`` helper used by both append and verify.
Pitfall #8 (``ensure_ascii`` consistency) is verified by the CN-content
round-trip test.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agent.curator_audit import (
    GENESIS_PREV_SHA256,
    AuditChainError,
    _compute_entry_sha256,
    _serialize_entry_for_sha256,
    append_audit,
    read_audit,
    verify_chain,
)


FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "curator"
VALID_FIXTURE = FIXTURES_DIR / "audit_chain_valid.jsonl"
TAMPERED_FIXTURE = FIXTURES_DIR / "audit_chain_tampered.jsonl"


# --------------------------------------------------------------------------- #
# Genesis + serialization helpers
# --------------------------------------------------------------------------- #


class TestGenesisAndSerialization:
    def test_genesis_prev_sha256_is_empty_byte_hash(self):
        expected = hashlib.sha256(b"").hexdigest()
        assert GENESIS_PREV_SHA256 == expected
        assert expected == (
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )

    def test_serialize_drops_entry_sha256(self):
        entry = {"a": 1, "entry_sha256": "deadbeef", "b": 2}
        out = _serialize_entry_for_sha256(entry)
        assert "entry_sha256" not in out
        assert "deadbeef" not in out

    def test_serialize_is_deterministic_sorted_compact(self):
        entry1 = {"b": 2, "a": 1, "c": 3}
        entry2 = {"c": 3, "a": 1, "b": 2}
        assert _serialize_entry_for_sha256(entry1) == _serialize_entry_for_sha256(entry2)
        # Compact separators (no spaces).
        assert _serialize_entry_for_sha256(entry1) == '{"a":1,"b":2,"c":3}'

    def test_serialize_ensure_ascii_false_preserves_cn(self):
        entry = {"skill_id": "编剧", "feedback_ids": ["反馈1"]}
        out = _serialize_entry_for_sha256(entry)
        assert "编剧" in out
        assert "反馈1" in out


# --------------------------------------------------------------------------- #
# append_audit — basic behavior
# --------------------------------------------------------------------------- #


class TestAppendAudit:
    def test_first_entry_uses_genesis_prev(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        entry_id = append_audit(
            action="propose", patch_id="p1", skill_id="screenplay",
        )
        assert isinstance(entry_id, str)
        assert len(entry_id) == 32  # uuid4 hex

        # Read the file back and verify the chain.
        log_path = tmp_path / "skills" / ".audit" / "log.jsonl"
        lines = log_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["prev_sha256"] == GENESIS_PREV_SHA256
        assert entry["action"] == "propose"
        assert entry["patch_id"] == "p1"
        assert entry["skill_id"] == "screenplay"
        assert entry["operator"] == "system"

        # Verify the entry_sha256 matches the LOCKED formula.
        expected = _compute_entry_sha256(GENESIS_PREV_SHA256, entry)
        assert entry["entry_sha256"] == expected

    def test_second_entry_chains_to_first(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        first_id = append_audit(
            action="propose", patch_id="p1", skill_id="screenplay",
        )
        second_id = append_audit(
            action="apply", patch_id="p1", skill_id="screenplay",
            operator="kai", commit_sha="abc123",
        )
        assert first_id != second_id

        log_path = tmp_path / "skills" / ".audit" / "log.jsonl"
        lines = log_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 2
        e1, e2 = json.loads(lines[0]), json.loads(lines[1])
        assert e2["prev_sha256"] == e1["entry_sha256"]

    def test_invalid_action_raises_value_error(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        with pytest.raises(ValueError, match="action must be one of"):
            append_audit(action="bogus", patch_id="p1", skill_id="s")

    def test_audit_chain_error_on_corrupt_tail(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        log_path = tmp_path / "skills" / ".audit" / "log.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("{not valid json}\n", encoding="utf-8")

        with pytest.raises(AuditChainError, match="audit log tail is malformed"):
            append_audit(
                action="propose", patch_id="p1", skill_id="s",
            )

    def test_cn_content_round_trips_cleanly(self, tmp_path, monkeypatch):
        """Pitfall #8: ensure_ascii=False preserves CN feedback_ids."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        append_audit(
            action="propose", patch_id="p1", skill_id="编剧",
            feedback_ids=["反馈1", "反馈2"],
        )
        log_path = tmp_path / "skills" / ".audit" / "log.jsonl"
        raw = log_path.read_text(encoding="utf-8")
        assert "编剧" in raw
        assert "反馈1" in raw
        # And verify_chain must accept it.
        assert verify_chain() == []


# --------------------------------------------------------------------------- #
# verify_chain — tamper detection
# --------------------------------------------------------------------------- #


class TestVerifyChain:
    def test_empty_log_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        assert verify_chain() == []

    def test_missing_log_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        assert verify_chain() == []

    def test_valid_fixture_no_breaks(self):
        breaks = verify_chain(path=VALID_FIXTURE)
        assert breaks == [], f"expected no breaks, got: {breaks}"

    def test_tampered_fixture_detects_break(self):
        breaks = verify_chain(path=TAMPERED_FIXTURE)
        assert len(breaks) >= 1, "tampered fixture must produce >= 1 break"
        # The middle entry (line 2) has a mutated action field — its
        # recomputed entry_sha256 won't match the stated one.
        line_nums = [b["line"] for b in breaks]
        assert 2 in line_nums, f"line 2 must be flagged, got {line_nums}"

    def test_prev_sha256_mismatch_on_edit(self, tmp_path, monkeypatch):
        """Editing an interior entry's prev_sha256 breaks the chain."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        # Build a 3-entry chain.
        for action in ("propose", "apply", "rollback"):
            append_audit(
                action=action, patch_id="p1", skill_id="s",
                commit_sha="abc" if action != "propose" else None,
            )
        log_path = tmp_path / "skills" / ".audit" / "log.jsonl"
        lines = log_path.read_text(encoding="utf-8").splitlines()
        # Mutate line 2's prev_sha256 to a bogus value.
        e2 = json.loads(lines[1])
        e2["prev_sha256"] = "0" * 64
        lines[1] = json.dumps(e2, ensure_ascii=False)
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        breaks = verify_chain()
        assert any(b["line"] == 2 and "prev_sha256 mismatch" in b["error"] for b in breaks)

    def test_interior_deletion_breaks_chain(self, tmp_path, monkeypatch):
        """Deleting an interior line produces prev_sha256 mismatches downstream."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        for action in ("propose", "apply", "rollback"):
            append_audit(
                action=action, patch_id="p1", skill_id="s",
                commit_sha="abc" if action != "propose" else None,
            )
        log_path = tmp_path / "skills" / ".audit" / "log.jsonl"
        lines = log_path.read_text(encoding="utf-8").splitlines()
        # Delete line 2 (the apply entry) — line 3's prev_sha256 no longer
        # chains correctly.
        del lines[1]
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        breaks = verify_chain()
        assert len(breaks) >= 1


# --------------------------------------------------------------------------- #
# read_audit — filtering
# --------------------------------------------------------------------------- #


class TestReadAudit:
    def test_read_all_from_valid_fixture(self):
        entries = read_audit(path=VALID_FIXTURE)
        assert len(entries) == 3
        actions = [e["action"] for e in entries]
        assert actions == ["propose", "apply", "rollback"]

    def test_filter_by_action(self):
        applies = read_audit(action="apply", path=VALID_FIXTURE)
        assert len(applies) == 1
        assert applies[0]["action"] == "apply"
        assert applies[0]["commit_sha"] == "abc123"

    def test_filter_by_skill(self):
        entries = read_audit(skill="screenplay", path=VALID_FIXTURE)
        assert len(entries) == 3
        empty = read_audit(skill="nonexistent", path=VALID_FIXTURE)
        assert empty == []

    def test_filter_by_since(self):
        # The fixture has dates 2026-06-01, 2026-06-02, 2026-06-03.
        # since=2026-06-02 should exclude the propose entry.
        entries = read_audit(since="2026-06-02T00:00:00+00:00", path=VALID_FIXTURE)
        assert len(entries) == 2
        assert all(e["action"] != "propose" for e in entries)

    def test_filter_by_naive_since_normalizes_to_utc(self):
        """CR-02 regression: ``--since 2026-06-02`` (naive, no tzinfo)
        used to silently drop every entry because the aware entry_ts
        raised TypeError on comparison and was caught as "unparseable
        ts". After the fix, naive since is promoted to UTC midnight and
        the comparison works correctly.
        """
        # Should behave identically to the aware variant above.
        entries = read_audit(since="2026-06-02", path=VALID_FIXTURE)
        assert len(entries) == 2
        assert all(e["action"] != "propose" for e in entries)

    def test_filter_by_naive_since_date_only(self):
        """CR-02 regression: ``--since 2026-06-01`` (the exact example
        from the CLI help text) used to silently drop every entry. After
        the fix, it correctly returns all 3 fixture entries.
        """
        entries = read_audit(since="2026-06-01", path=VALID_FIXTURE)
        assert len(entries) == 3

    def test_filter_by_since_naive_entry_ts_promoted(self, tmp_path, monkeypatch):
        """CR-02 defensive: a hand-edited legacy entry with a naive ts
        (no tzinfo) is promoted to UTC rather than dropping the entry.
        """
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        log_path = tmp_path / "skills" / ".audit" / "log.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        # Naive-ts entry + aware-ts entry, both after 2026-06-01 UTC.
        naive_entry = {
            "entry_id": "naive1",
            "prev_sha256": GENESIS_PREV_SHA256,
            "action": "propose",
            "ts": "2026-06-15T10:00:00",  # naive — no +00:00
            "operator": "t",
            "patch_id": "p1",
            "skill_id": "s1",
            "feedback_ids": [],
            "eval_score": {},
            "commit_sha": None,
        }
        payload = {k: v for k, v in naive_entry.items() if k != "entry_sha256"}
        naive_entry["entry_sha256"] = hashlib.sha256(
            (GENESIS_PREV_SHA256 + json.dumps(payload, sort_keys=True,
                                              separators=(",", ":"),
                                              ensure_ascii=False)).encode("utf-8")
        ).hexdigest()
        log_path.write_text(
            json.dumps(naive_entry, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        # Naive since + naive entry ts: both promoted to UTC, comparison works.
        entries = read_audit(since="2026-06-01", path=log_path)
        assert len(entries) == 1
        assert entries[0]["entry_id"] == "naive1"

    def test_invalid_since_raises(self):
        with pytest.raises(ValueError, match="since must be ISO-8601"):
            read_audit(since="not-a-date", path=VALID_FIXTURE)

    def test_empty_log_returns_empty_list(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        assert read_audit() == []
