"""Unit tests for ``agent.observability.agent_registry_metrics``.

Covers OBSRV-01 (agent registry health collector):
    - happy-path dict shape (6 keys with correct types/values)
    - lineage integrity flagging (missing ``source_sha256`` or
      ``transform_rule_id`` -> ``lineage_integrity_ok = False``)
    - missing-experts passthrough (preserve order, no dedup/sort)
    - schema-fail passthrough (``schema_ok=False`` propagates)
    - empty-entries graceful (agents_loaded=0, lineage_ok=True vacuously)

References: Plan 67-01 Task 2 <behavior>; RESEARCH "Instrumentation Points
§OBSRV-01"; OBSRV-01 requirement spec.
"""

from __future__ import annotations

import re

import pytest

from agent.observability import get_agent_registry_metrics
from agent.observability.agent_registry_metrics import _check_lineage


# ISO-8601 UTC pattern: YYYY-MM-DDTHH:MM:SS[.ffffff][+ZZ:ZZ | Z]
# Accepts the ``datetime.now(timezone.utc).isoformat()`` output shape.
_ISO_8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(\.\d+)?"
    r"([+-]\d{2}:\d{2}|Z)?$"
)


@pytest.fixture
def entries_all_valid() -> list[dict]:
    """Sample registry entries -- all have complete lineage."""
    return [
        {
            "name": "screenplay",
            "lineage": {
                "source_sha256": "abc123",
                "transform_rule_id": "R-01",
            },
        },
        {
            "name": "colorist",
            "lineage": {
                "source_sha256": "def456",
                "transform_rule_id": "R-02",
            },
        },
        {
            "name": "editor",
            "lineage": {
                "source_sha256": "ghi789",
                "transform_rule_id": "R-03",
            },
        },
    ]


@pytest.fixture
def entries_one_missing_lineage() -> list[dict]:
    """Registry entries where one entry's lineage is missing source_sha256."""
    return [
        {
            "name": "screenplay",
            "lineage": {
                "source_sha256": "abc123",
                "transform_rule_id": "R-01",
            },
        },
        {
            "name": "colorist",
            # source_sha256 missing -> lineage integrity fails
            "lineage": {"transform_rule_id": "R-02"},
        },
        {
            "name": "editor",
            "lineage": {
                "source_sha256": "ghi789",
                "transform_rule_id": "R-03",
            },
        },
    ]


@pytest.fixture
def entries_missing_transform_rule() -> list[dict]:
    """Registry entries where one entry's lineage is missing transform_rule_id."""
    return [
        {
            "name": "screenplay",
            "lineage": {
                "source_sha256": "abc123",
                "transform_rule_id": "R-01",
            },
        },
        # transform_rule_id empty -> lineage integrity fails
        {
            "name": "colorist",
            "lineage": {"source_sha256": "def456", "transform_rule_id": ""},
        },
    ]


@pytest.fixture
def entries_no_lineage_key() -> list[dict]:
    """Registry entries where one entry has no ``lineage`` key at all."""
    return [
        {"name": "screenplay"},  # no lineage key
        {
            "name": "colorist",
            "lineage": {
                "source_sha256": "def456",
                "transform_rule_id": "R-02",
            },
        },
    ]


@pytest.fixture
def entries_none_lineage() -> list[dict]:
    """Registry entries where one entry's lineage is explicitly None."""
    return [
        {"name": "screenplay", "lineage": None},
        {
            "name": "colorist",
            "lineage": {
                "source_sha256": "def456",
                "transform_rule_id": "R-02",
            },
        },
    ]


class TestAgentRegistryMetrics:
    """OBSRV-01 unit tests: shape + lineage flagging + passthrough semantics."""

    def test_happy_path_shape(
        self,
        entries_all_valid: list[dict],
    ) -> None:
        """Valid entries, no missing experts, schema_ok=True -> 6-key dict."""
        result = get_agent_registry_metrics(
            entries_all_valid, missing_experts=[], schema_ok=True
        )

        # Contract: 6 keys present.
        expected_keys = {
            "agents_loaded",
            "schema_validation_ok",
            "missing_experts",
            "lineage_integrity_ok",
            "agent_names",
            "snapshot_at_iso",
        }
        assert set(result.keys()) == expected_keys

        # Value semantics.
        assert result["agents_loaded"] == 3
        assert result["schema_validation_ok"] is True
        assert result["missing_experts"] == []
        assert result["lineage_integrity_ok"] is True
        # agent_names is sorted alphabetically.
        assert result["agent_names"] == ["colorist", "editor", "screenplay"]
        # snapshot_at_iso is ISO-8601 shaped.
        assert isinstance(result["snapshot_at_iso"], str)
        assert _ISO_8601_RE.match(result["snapshot_at_iso"]), (
            f"snapshot_at_iso not ISO-8601: {result['snapshot_at_iso']!r}"
        )

    def test_lineage_check_flags_missing_sha(
        self,
        entries_one_missing_lineage: list[dict],
    ) -> None:
        """One entry missing ``source_sha256`` -> lineage_integrity_ok=False."""
        # Direct _check_lineage test.
        assert _check_lineage(entries_one_missing_lineage) is False

        # And via the public collector API.
        result = get_agent_registry_metrics(
            entries_one_missing_lineage, missing_experts=[], schema_ok=True
        )
        assert result["lineage_integrity_ok"] is False
        # Other fields still populated correctly.
        assert result["agents_loaded"] == 3

    def test_lineage_check_flags_missing_transform_rule(
        self,
        entries_missing_transform_rule: list[dict],
    ) -> None:
        """One entry with empty ``transform_rule_id`` -> lineage fails."""
        assert _check_lineage(entries_missing_transform_rule) is False

    def test_lineage_check_flags_missing_lineage_key(
        self,
        entries_no_lineage_key: list[dict],
    ) -> None:
        """Entry without ``lineage`` key at all -> lineage fails."""
        assert _check_lineage(entries_no_lineage_key) is False

    def test_lineage_check_flags_none_lineage(
        self,
        entries_none_lineage: list[dict],
    ) -> None:
        """Entry with ``lineage: None`` -> lineage fails (defensive .get(None) or {})."""
        assert _check_lineage(entries_none_lineage) is False

    def test_lineage_check_empty_entries_vacuously_true(self) -> None:
        """Empty entries list -> lineage check returns True (vacuous truth)."""
        assert _check_lineage([]) is True

    def test_missing_experts_passthrough_preserve_order(self) -> None:
        """missing_experts is propagated verbatim (no dedup, no sort)."""
        # Note the deliberately non-sorted order to verify passthrough.
        missing = ["z_expert", "a_expert", "z_expert"]
        result = get_agent_registry_metrics(
            [], missing_experts=missing, schema_ok=True
        )
        # Order preserved, duplicates NOT removed.
        assert result["missing_experts"] == ["z_expert", "a_expert", "z_expert"]

    def test_schema_fail_passthrough(self) -> None:
        """schema_ok=False propagates even with non-empty entries."""
        entries = [
            {
                "name": "x",
                "lineage": {
                    "source_sha256": "a",
                    "transform_rule_id": "b",
                },
            }
        ]
        result = get_agent_registry_metrics(
            entries, missing_experts=[], schema_ok=False
        )
        assert result["schema_validation_ok"] is False

    def test_empty_entries_graceful(self) -> None:
        """entries=[] -> agents_loaded=0, agent_names=[], lineage_ok=True."""
        result = get_agent_registry_metrics(
            [], missing_experts=[], schema_ok=True
        )
        assert result["agents_loaded"] == 0
        assert result["agent_names"] == []
        assert result["lineage_integrity_ok"] is True

    def test_agent_names_sorted(self) -> None:
        """agent_names is returned in sorted order regardless of input order."""
        entries = [
            {"name": "zeta", "lineage": {"source_sha256": "1", "transform_rule_id": "r"}},
            {"name": "alpha", "lineage": {"source_sha256": "2", "transform_rule_id": "r"}},
            {"name": "mike", "lineage": {"source_sha256": "3", "transform_rule_id": "r"}},
        ]
        result = get_agent_registry_metrics(
            entries, missing_experts=[], schema_ok=True
        )
        assert result["agent_names"] == ["alpha", "mike", "zeta"]

    def test_entry_missing_name_key_uses_empty_string(self) -> None:
        """Entry without a ``name`` key does not crash -- contributes "" to names.

        Defensive: ``.get("name", "")`` per the plan's implementation hint.
        """
        entries = [
            {"lineage": {"source_sha256": "1", "transform_rule_id": "r"}},
            {"name": "real", "lineage": {"source_sha256": "2", "transform_rule_id": "r"}},
        ]
        result = get_agent_registry_metrics(
            entries, missing_experts=[], schema_ok=True
        )
        # Empty string sorts before any real name.
        assert result["agent_names"] == ["", "real"]
        assert result["agents_loaded"] == 2
