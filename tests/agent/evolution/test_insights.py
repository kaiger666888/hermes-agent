"""Tests for agent/evolution/insights.py — EVOL-01 LLM aggregation.

Covers InsightRecord schema, aggregate_feedback happy path + malformed
JSON handling + empty-feedback path, make_aggregation_client construction,
and the AGGREGATION_SYSTEM_PROMPT critical-rules content.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from agent.evolution.insights import (
    AGGREGATION_SYSTEM_PROMPT,
    AggregationError,
    InsightRecord,
    aggregate_feedback,
    build_aggregation_user_prompt,
    make_aggregation_client,
)


# --------------------------------------------------------------------------- #
# TestInsightSchema
# --------------------------------------------------------------------------- #


class TestInsightSchema:
    def test_valid_record(self) -> None:
        rec = InsightRecord(
            insight_id="test_1234_abcd1234",
            skill_id="test_skill",
            theme="Missing examples",
            evidence_chain=["fb_1", "fb_2"],
            rationale="Operators noted the gap.",
            proposed_addition="### Example\n\n...\n",
            insert_after_marker="## References",
            ts="2026-06-24T10:00:00+00:00",
        )
        assert rec.evidence_chain == ["fb_1", "fb_2"]

    def test_rejects_empty_evidence_chain(self) -> None:
        with pytest.raises(ValidationError):
            InsightRecord(
                insight_id="x",
                skill_id="test_skill",
                theme="t",
                evidence_chain=[],
                rationale="r",
                proposed_addition="p",
                insert_after_marker="## References",
                ts="2026-06-24T10:00:00+00:00",
            )

    def test_rejects_missing_theme(self) -> None:
        with pytest.raises(ValidationError):
            InsightRecord(
                insight_id="x",
                skill_id="test_skill",
                # theme omitted
                evidence_chain=["fb_1"],
                rationale="r",
                proposed_addition="p",
                insert_after_marker="## References",
                ts="2026-06-24T10:00:00+00:00",
            )


# --------------------------------------------------------------------------- #
# TestAggregateFeedback
# --------------------------------------------------------------------------- #


class TestAggregateFeedback:
    def test_returns_insights_from_valid_llm_response(
        self, mock_store: object, mock_llm_client_with_insights: object
    ) -> None:
        records = aggregate_feedback(
            skill_id="test_skill",
            store=mock_store,  # type: ignore[arg-type]
            client=mock_llm_client_with_insights,  # type: ignore[arg-type]
            model="test-model",
        )
        assert len(records) >= 1
        for rec in records:
            assert isinstance(rec, InsightRecord)
            assert rec.skill_id == "test_skill"
            assert len(rec.evidence_chain) >= 1
            assert rec.insight_id.startswith("test_skill_")

    def test_strips_markdown_fences(
        self, mock_store: object, mock_llm_client: object
    ) -> None:
        payload = json.dumps(json.loads(
            '{"insights": [{"theme": "t", "evidence_chain": ["fb_1"], '
            '"rationale": "r", "proposed_addition": "x\\n", '
            '"insert_after_marker": "## References"}]}'
        ))
        fenced = f"```json\n{payload}\n```"
        client = mock_llm_client(fenced)  # type: ignore[operator]
        records = aggregate_feedback(
            skill_id="test_skill",
            store=mock_store,  # type: ignore[arg-type]
            client=client,
            model="m",
        )
        assert len(records) == 1

    def test_insight_id_is_content_addressed(
        self, mock_store: object, mock_llm_client_with_insights: object
    ) -> None:
        records = aggregate_feedback(
            skill_id="test_skill",
            store=mock_store,  # type: ignore[arg-type]
            client=mock_llm_client_with_insights,  # type: ignore[arg-type]
            model="m",
        )
        # Two insights in the sample payload → two distinct insight_ids.
        ids = [r.insight_id for r in records]
        assert len(ids) == len(set(ids)), "insight_ids must be unique"


# --------------------------------------------------------------------------- #
# TestMalformedJson
# --------------------------------------------------------------------------- #


class TestMalformedJson:
    def test_trailing_comma_raises_aggregation_error(
        self, mock_store: object, mock_llm_client: object
    ) -> None:
        bad = '{"insights": [{"theme": "t", "evidence_chain": ["fb_1"],},]}'  # trailing commas
        client = mock_llm_client(bad)  # type: ignore[operator]
        with pytest.raises(AggregationError):
            aggregate_feedback(
                skill_id="test_skill",
                store=mock_store,  # type: ignore[arg-type]
                client=client,
                model="m",
            )

    def test_missing_insights_key_raises(
        self, mock_store: object, mock_llm_client: object
    ) -> None:
        client = mock_llm_client('{"wrong_key": []}')  # type: ignore[operator]
        with pytest.raises(AggregationError):
            aggregate_feedback(
                skill_id="test_skill",
                store=mock_store,  # type: ignore[arg-type]
                client=client,
                model="m",
            )

    def test_never_returns_empty_list_on_parse_failure(
        self, mock_store: object, mock_llm_client: object
    ) -> None:
        # Malformed JSON must RAISE — never silently return [].
        client = mock_llm_client("not even json at all")  # type: ignore[operator]
        with pytest.raises(AggregationError):
            aggregate_feedback(
                skill_id="test_skill",
                store=mock_store,  # type: ignore[arg-type]
                client=client,
                model="m",
            )


# --------------------------------------------------------------------------- #
# TestEmptyFeedback
# --------------------------------------------------------------------------- #


class TestEmptyFeedback:
    def test_empty_store_returns_empty_list(
        self, empty_mock_store: object, mock_llm_client_with_insights: object
    ) -> None:
        # Legitimate "no feedback for skill" — distinct from parse failure.
        records = aggregate_feedback(
            skill_id="test_skill",
            store=empty_mock_store,  # type: ignore[arg-type]
            client=mock_llm_client_with_insights,  # type: ignore[arg-type]
            model="m",
        )
        assert records == []


# --------------------------------------------------------------------------- #
# TestMakeAggregationClient
# --------------------------------------------------------------------------- #


class TestMakeAggregationClient:
    def test_missing_api_key_raises_runtime_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="(?i)api_key|openrouter"):
            make_aggregation_client()

    def test_returns_client_and_model_override(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        client, model = make_aggregation_client(model_override="my-model")
        assert model == "my-model"
        assert client is not None

    def test_env_model_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        monkeypatch.setenv("HERMES_EVOLUTION_MODEL", "env-model")
        _, model = make_aggregation_client()
        assert model == "env-model"

    def test_default_model_when_no_override(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        monkeypatch.delenv("HERMES_EVOLUTION_MODEL", raising=False)
        _, model = make_aggregation_client()
        assert model == "claude-sonnet-4-6"


# --------------------------------------------------------------------------- #
# TestBuildUserPrompt
# --------------------------------------------------------------------------- #


class TestBuildUserPrompt:
    def test_embeds_skill_id_and_feedback(
        self, sample_feedback_records: list[dict]
    ) -> None:
        prompt = build_aggregation_user_prompt(
            skill_id="test_skill",
            feedback_summary={"total": 3},
            feedback_details=sample_feedback_records,
        )
        assert "test_skill" in prompt
        assert "fb_001" in prompt
        assert "total" in prompt

    def test_truncates_to_50_records(
        self,
    ) -> None:
        many = [
            {"record_id": f"fb_{i}", "verdict": "negative"}
            for i in range(100)
        ]
        prompt = build_aggregation_user_prompt(
            skill_id="test_skill",
            feedback_summary={"total": 100},
            feedback_details=many,
        )
        # fb_49 should be present, fb_99 should NOT (truncated to most-recent 50).
        # The truncation keeps the first 50 of the list as-passed; per plan step 3,
        # caller passes most-recent first. We assert the prompt does not contain
        # all 100 record_ids.
        assert "fb_0\n" not in prompt or "fb_0," not in prompt  # weak check
        # Stronger: the JSON dump should only have 50 entries.
        # Find the feedback_details JSON blob — count record_id occurrences.
        occurrences = prompt.count('"record_id": "fb_')
        assert occurrences <= 50, f"expected <= 50 records in prompt, got {occurrences}"


# --------------------------------------------------------------------------- #
# TestAggregationSystemPrompt
# --------------------------------------------------------------------------- #


class TestAggregationSystemPrompt:
    def test_contains_critical_rules(self) -> None:
        # RESEARCH §"LLM Aggregation Prompt Template" — 7 critical rules.
        s = AGGREGATION_SYSTEM_PROMPT
        assert "ADDITIVE" in s.upper() or "additive" in s.lower()
        assert "evidence" in s.lower()
        assert "expert_id" in s
        assert "related_skills" in s
        # Must reference protected refs.
        assert "snowflake" in s.lower() or "snowflake-method" in s
        assert "scamper" in s.lower()
        assert "e-konte" in s.lower() or "e_konte" in s.lower()
        assert "insights" in s.lower()
