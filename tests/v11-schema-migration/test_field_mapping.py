"""Per-field mapping tests for the 17-row Phase 49 §4.3 mapping table.

Tests import the script as a Python module (not subprocess) so they can
unit-test the ``map_record`` pure function directly without going through
CLI plumbing. This is the unit-test surface; the integration tests live in
``test_dry_run_zero_writes.py`` + ``test_zero_silent_drops.py``.

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 / 585 forward-compat.
  - ``encoding="utf-8"`` on every ``open()`` (Ruff PLW1514).
  - Double-quoted strings throughout.
  - Pydantic v2 syntax (``model_validate``).
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Load the migration script as a module (its filename has hyphens, so we use
# spec_from_file_location rather than a normal import).
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "migrate_v6_feedback_to_memory_schema.py"

_spec = importlib.util.spec_from_file_location(
    "migrate_v6_feedback_to_memory_schema", SCRIPT_PATH
)
assert _spec is not None and _spec.loader is not None, "failed to load script spec"
_migration = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_migration)
map_record = _migration.map_record


# ── Fixtures ─────────────────────────────────────────────────────────────


def _make_record(
    *,
    skill_id: str = "screenplay",
    source: str = "cli",
    verdict: str = "good",
    correction: str = "test correction",
    revised_output: str | None = None,
    ts: str = "2026-06-01T10:05:00+00:00",
) -> dict:
    """Build a minimal valid FeedbackRecord dict (decoded-JSON form)."""
    return {
        "skill_id": skill_id,
        "expert_id": skill_id,
        "source": source,
        "verdict": verdict,
        "correction": correction,
        "revised_output": revised_output,
        "output_snapshot": {
            "sha256": "a" * 64,
            "output_text": "test output",
            "prompt": "test prompt",
            "model": "glm-5.2",
            "provider": "zai",
            "api_mode": "chat_completions",
            "params": {"temperature": 0.7},
            "captured_at": "2026-06-01T10:00:00+00:00",
        },
        "ts": ts,
    }


def _map(record_dict: dict) -> dict:
    """Run map_record on a record dict, returning the target memory-record."""
    # Use the from_dict classmethod to parse the dict into a FeedbackRecord.
    from agent.feedback_schema import FeedbackRecord

    source = FeedbackRecord.model_validate(record_dict)
    return map_record(source, agent_persona_sha256={})


# ── Identity + routing ──────────────────────────────────────────────────


class TestSkillIdMapsToAgentId:
    def test_skill_id_becomes_agent_id_verbatim(self) -> None:
        target = _map(_make_record(skill_id="screenplay"))
        assert target["agent_id"] == "screenplay"

    def test_cinematographer_skill_id_preserved(self) -> None:
        target = _map(_make_record(skill_id="cinematographer"))
        assert target["agent_id"] == "cinematographer"


class TestTsMapsToCreatedAt:
    def test_ts_verbatim_to_created_at(self) -> None:
        ts = "2026-06-01T10:05:00+00:00"
        target = _map(_make_record(ts=ts))
        assert target["created_at"] == ts


# ── Verdict → status mapping (P14 mitigation core) ──────────────────────


class TestVerdictMapsToStatus:
    """Per §4.3 table: good → active; needs_work → active; bad → quarantined.

    Code is authoritative (NOT doc): agent/feedback_schema.py:206 defines
    verdict enum as ``good | needs_work | bad``, NOT ``positive | negative
    | neutral`` as 04-MIGRATION-PATH.md §4.1 doc claims.
    """

    def test_verdict_good_to_status_active(self) -> None:
        target = _map(_make_record(verdict="good"))
        assert target["status"] == "active"

    def test_verdict_needs_work_to_status_active(self) -> None:
        target = _map(_make_record(verdict="needs_work"))
        assert target["status"] == "active"

    def test_verdict_bad_to_status_quarantined(self) -> None:
        """P14 mitigation — never auto-activate negative-feedback records."""
        target = _map(_make_record(verdict="bad"))
        assert target["status"] == "quarantined"


# ── Safe defaults (§4.6 + spec §5) ──────────────────────────────────────


class TestSafeDefaults:
    def test_default_scope_is_project(self) -> None:
        target = _map(_make_record())
        assert target["scope"] == "project"

    def test_default_confidence_is_0_5(self) -> None:
        """OQ-4 neutral baseline."""
        target = _map(_make_record())
        assert target["confidence"] == 0.5

    def test_default_confidentiality_is_confidential(self) -> None:
        """P14 mitigation 2 — safest not most permissive. Never ``"public"``."""
        target = _map(_make_record())
        assert target["confidentiality"] == "confidential"

    def test_default_schema_version_1_0_0(self) -> None:
        target = _map(_make_record())
        assert target["schema_version"] == "1.0.0"

    def test_default_half_life_180_days(self) -> None:
        target = _map(_make_record())
        assert target["half_life_days"] == 180

    def test_default_expires_at_created_plus_180(self) -> None:
        """``expires_at == created_at + timedelta(days=180)``."""
        from datetime import timedelta

        target = _map(_make_record(ts="2026-06-01T10:05:00+00:00"))
        created = datetime.fromisoformat(target["created_at"])
        expires = datetime.fromisoformat(target["expires_at"])
        assert expires == created + timedelta(days=180)

    def test_default_verified_at_equals_created_at(self) -> None:
        target = _map(_make_record())
        assert target["verified_at"] == target["created_at"]

    def test_default_supersedes_memory_id_null(self) -> None:
        target = _map(_make_record())
        assert target["supersedes_memory_id"] is None

    def test_default_project_id_unknown(self) -> None:
        """P14 — never null, always trackable."""
        target = _map(_make_record())
        assert target["project_id"] == "unknown"

    def test_default_session_id_null(self) -> None:
        target = _map(_make_record())
        assert target["session_id"] is None

    def test_default_persona_sha256_zero_hash_when_no_yaml(self) -> None:
        """When agent YAML persona not found, persona_sha256 = ``"0" * 64``."""
        target = _map(_make_record())
        assert target["persona_sha256"] == "0" * 64
        # And a mapping warning should flag it (checked in zero-drops tests).

    def test_default_persona_sha256_from_yaml_lookup(self) -> None:
        """When agent_persona_sha256 dict has the agent_id, use it."""
        from agent.feedback_schema import FeedbackRecord

        source = FeedbackRecord.model_validate(_make_record(skill_id="screenplay"))
        target = map_record(
            source,
            agent_persona_sha256={"screenplay": "a" * 64},
        )
        assert target["persona_sha256"] == "a" * 64


# ── Evidence chain construction ─────────────────────────────────────────


class TestEvidenceChain:
    def test_evidence_chain_constructed_from_source(self) -> None:
        """``evidence_chain=[{source_type, evidence_sha256, evidence_text, ts}]``.

        Length=1 from FeedbackRecord (below P5 ≥3 threshold — flagged as
        mapping warning in compute_metrics).
        """
        target = _map(_make_record(source="cli"))
        assert isinstance(target["evidence_chain"], list)
        assert len(target["evidence_chain"]) == 1
        ev = target["evidence_chain"][0]
        assert "source_type" in ev
        assert "timestamp" in ev
        # source_type mapping: cli/manual → operator; kais_aigc → auto_eval
        assert ev["source_type"] == "operator"

    def test_source_cli_to_evidence_type_operator(self) -> None:
        target = _map(_make_record(source="cli"))
        assert target["evidence_chain"][0]["source_type"] == "operator"

    def test_source_manual_to_evidence_type_operator(self) -> None:
        target = _map(_make_record(source="manual"))
        assert target["evidence_chain"][0]["source_type"] == "operator"

    def test_source_kais_aigc_to_evidence_type_auto_eval(self) -> None:
        target = _map(_make_record(source="kais_aigc"))
        assert target["evidence_chain"][0]["source_type"] == "auto_eval"

    def test_evidence_operator_ids_default_unknown(self) -> None:
        """FeedbackRecord has no operator_id field (divergence from doc).

        Default to ``["unknown"]`` per spec §3.2 mapping table.
        """
        target = _map(_make_record())
        assert target["evidence_operator_ids"] == ["unknown"]


# ── Content derivation ──────────────────────────────────────────────────


class TestContentDerivation:
    def test_content_from_correction_when_present(self) -> None:
        target = _map(_make_record(correction="fix the pacing"))
        assert "fix the pacing" in target["content"]

    def test_content_includes_revised_output_when_present(self) -> None:
        target = _map(
            _make_record(
                correction="see revision",
                revised_output="INT. SCENE - DAY\n\nNew version.",
            )
        )
        assert "see revision" in target["content"]
        assert "New version" in target["content"]

    def test_content_placeholder_when_correction_empty_and_verdict_bad(self) -> None:
        """Edge case: empty correction + verdict=bad → ambiguous.

        Content defaults to a placeholder (NOT empty string). This is the
        case that generates a mapping warning per spec §3.1.
        """
        target = _map(_make_record(correction="", verdict="bad"))
        # Content must be non-empty — never silently blank.
        assert target["content"]
        assert len(target["content"]) > 0


# ── record_id determinism (UUIDv5 from content hash) ───────────────────


class TestRecordIdDeterministic:
    def test_record_id_is_deterministic_uuid5(self) -> None:
        """Same source line → same record_id across runs.

        The script computes ``record_id = uuid.uuid5(NAMESPACE_OID,
        sha256(source_line_bytes))``. Calling map_record twice on the same
        record must produce the same record_id.

        NOTE: map_record itself does not compute record_id (that happens at
        the source-line level in run_dry_run). This test is therefore on the
        script-level helper ``compute_record_id`` if exposed, else skipped.
        """
        if not hasattr(_migration, "compute_record_id"):
            pytest.skip("compute_record_id helper not exposed by script")
        compute = _migration.compute_record_id
        line = '{"foo": "bar"}'
        rid1 = compute(line)
        rid2 = compute(line)
        assert rid1 == rid2
        # And it should be a valid UUID string.
        import uuid as _uuid

        _uuid.UUID(rid1)  # raises ValueError if malformed
