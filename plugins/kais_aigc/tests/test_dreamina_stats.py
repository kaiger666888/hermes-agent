"""test_dreamina_stats.py — unit test for IMG-05 MetricsBuffer JSONL.

Covers:
  - VALIDATION 73-01-08 (IMG-05): record_metric writes JSONL, read_metrics
    returns the written record. NO GLM calls during write or read
    (INFRA-04 preservation — zero asyncio).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from plugins.kais_aigc.dreamina_stats import (
    DreaminaTaskMetrics,
    _aggregate_glm_metrics,
    _glm_command,
    _cmd_glm_stats,
    read_metrics,
    record_metric,
    register_glm_cli,
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_metrics_buffer_persist(tmp_path):
    """VALIDATION 73-01-08 (IMG-05): MetricsBuffer JSONL persistence.

    Write a metric dict via record_metric, read back via read_metrics.
    Assert the returned list has 1 entry matching the written dict.
    Assert the JSONL file exists at the expected path.
    """
    metrics_file = tmp_path / "metrics" / "dreamina_stats.jsonl"

    metric = {
        "submit_id": "test-uuid-0001",
        "stratum": "text2image",
        "latency_ms": 12500,
        "success": True,
        "retries": 0,
        "vision_verified": True,
        "vision_confidence": 0.92,
        "ts": "2026-07-09T14:00:00Z",
    }

    record_metric(metrics_file, metric)

    # File exists.
    assert metrics_file.exists()

    # Read back.
    results = read_metrics(metrics_file)
    assert len(results) == 1
    assert results[0]["submit_id"] == "test-uuid-0001"
    assert results[0]["success"] is True
    assert results[0]["latency_ms"] == 12500


def test_dreamina_task_metrics_schema():
    """DreaminaTaskMetrics Pydantic schema validates + rejects invalid stratum."""
    m = DreaminaTaskMetrics(
        submit_id="abc",
        stratum="3-ref",
        latency_ms=5000,
        success=True,
        retries=2,
        vision_verified=True,
        vision_confidence=0.85,
        ts="2026-07-09T14:00:00Z",
    )
    assert m.stratum == "3-ref"

    # Invalid stratum should raise.
    with pytest.raises(Exception):
        DreaminaTaskMetrics(
            submit_id="abc",
            stratum="invalid",
            latency_ms=5000,
            success=True,
            retries=0,
            vision_verified=False,
            vision_confidence=None,
            ts="2026-07-09T14:00:00Z",
        )


def test_read_metrics_handles_missing_file(tmp_path):
    """read_metrics returns [] for non-existent file (no crash)."""
    missing = tmp_path / "nonexistent.jsonl"
    assert read_metrics(missing) == []


# ---------------------------------------------------------------------------
# Phase 82-01: token/cost fields on DreaminaTaskMetrics (XCUT-04c-INSTRUMENT)
# ---------------------------------------------------------------------------


class TestTokenFields:
    """Phase 82: input_tokens + output_tokens + estimated_cost_usd fields."""

    def test_metrics_with_token_fields(self):
        """DreaminaTaskMetrics accepts all 3 new token/cost fields."""
        m = DreaminaTaskMetrics(
            submit_id="token-uuid-0001",
            stratum="1-ref",
            latency_ms=5000,
            success=True,
            retries=1,
            vision_verified=True,
            vision_confidence=0.88,
            ts="2026-07-10T00:00:00Z",
            input_tokens=100,
            output_tokens=50,
            estimated_cost_usd=0.0007,
        )
        assert m.input_tokens == 100
        assert m.output_tokens == 50
        assert m.estimated_cost_usd == 0.0007

    def test_metrics_backward_compat_defaults(self):
        """Constructing without new fields defaults to 0/0.0 (D-01 backward compat)."""
        m = DreaminaTaskMetrics(
            submit_id="x",
            stratum="1-ref",
            latency_ms=100,
            success=True,
            retries=0,
            vision_verified=False,
            ts="2026-07-10T00:00:00Z",
        )
        assert m.input_tokens == 0
        assert m.output_tokens == 0
        assert m.estimated_cost_usd == 0.0

    def test_record_metric_with_tokens(self, tmp_path):
        """record_metric writes JSONL containing the 3 new fields."""
        metrics_file = tmp_path / "metrics" / "stats.jsonl"
        record_metric(metrics_file, {
            "submit_id": "rec-token-0001",
            "stratum": "3-ref",
            "latency_ms": 2000,
            "success": True,
            "retries": 0,
            "vision_verified": True,
            "vision_confidence": 0.9,
            "ts": "2026-07-10T00:00:00Z",
            "input_tokens": 250,
            "output_tokens": 120,
            "estimated_cost_usd": 0.00171,
        })
        results = read_metrics(metrics_file)
        assert len(results) == 1
        assert results[0]["input_tokens"] == 250
        assert results[0]["output_tokens"] == 120
        assert results[0]["estimated_cost_usd"] == 0.00171

    def test_record_metric_legacy_dict(self, tmp_path):
        """record_metric without new fields still works (backward compat)."""
        metrics_file = tmp_path / "metrics" / "legacy.jsonl"
        record_metric(metrics_file, {
            "submit_id": "legacy-0001",
            "stratum": "text2image",
            "latency_ms": 1000,
            "success": True,
            "retries": 0,
            "vision_verified": False,
            "ts": "2026-07-10T00:00:00Z",
        })
        results = read_metrics(metrics_file)
        assert len(results) == 1
        # Pydantic default=0 fills in missing fields on write.
        assert results[0]["input_tokens"] == 0
        assert results[0]["output_tokens"] == 0


# ---------------------------------------------------------------------------
# Phase 82-02: GLM stats CLI (XCUT-04c-CLI)
# ---------------------------------------------------------------------------


class TestGlmCli:
    """Phase 82-02: register_glm_cli + _glm_command + _aggregate_glm_metrics."""

    def test_register_glm_cli_adds_stats_subparser(self):
        """register_glm_cli creates a 'stats' subcommand with --json and --month flags."""
        import argparse

        parser = argparse.ArgumentParser(prog="hermes glm")
        register_glm_cli(parser)
        # Parse "stats" subcommand.
        args = parser.parse_args(["stats"])
        assert args.glm_command == "stats"

        # Parse --json and --month.
        args_json = parser.parse_args(["stats", "--json"])
        assert args_json.json is True

        args_month = parser.parse_args(["stats", "--month", "2026-07"])
        assert args_month.month == "2026-07"

    def test_glm_command_no_subcommand_prints_help(self, capsys):
        """_glm_command with no glm_command attr prints help, returns 0."""
        import argparse

        args = argparse.Namespace()
        # No glm_command attribute.
        result = _glm_command(args)
        captured = capsys.readouterr()
        assert result == 0
        assert "hermes glm" in captured.out

    def test_aggregate_glm_metrics_monthly(self):
        """_aggregate_glm_metrics groups by month and sums tokens + cost."""
        metrics = [
            {
                "submit_id": "a", "stratum": "1-ref", "latency_ms": 1000,
                "success": True, "retries": 0, "vision_verified": True,
                "ts": "2026-07-10T12:00:00Z",
                "input_tokens": 100, "output_tokens": 50,
                "estimated_cost_usd": 0.0007,
            },
            {
                "submit_id": "b", "stratum": "3-ref", "latency_ms": 2000,
                "success": True, "retries": 1, "vision_verified": True,
                "ts": "2026-07-15T12:00:00Z",
                "input_tokens": 200, "output_tokens": 80,
                "estimated_cost_usd": 0.00124,
            },
        ]
        monthly, stratum_agg, no_token = _aggregate_glm_metrics(metrics)
        assert "2026-07" in monthly
        m = monthly["2026-07"]
        assert m["task_count"] == 2
        assert m["input_tokens"] == 300
        assert m["output_tokens"] == 130
        assert abs(m["estimated_cost_usd"] - 0.00194) < 1e-9
        assert no_token == 0

    def test_aggregate_glm_metrics_stratum(self):
        """_aggregate_glm_metrics groups by stratum and sums total_tokens."""
        metrics = [
            {
                "submit_id": "a", "stratum": "1-ref", "latency_ms": 1000,
                "success": True, "retries": 0, "vision_verified": True,
                "ts": "2026-07-10T12:00:00Z",
                "input_tokens": 100, "output_tokens": 50,
                "estimated_cost_usd": 0.0007,
            },
            {
                "submit_id": "b", "stratum": "1-ref", "latency_ms": 2000,
                "success": True, "retries": 1, "vision_verified": True,
                "ts": "2026-07-15T12:00:00Z",
                "input_tokens": 200, "output_tokens": 80,
                "estimated_cost_usd": 0.00124,
            },
            {
                "submit_id": "c", "stratum": "3-ref", "latency_ms": 1500,
                "success": False, "retries": 2, "vision_verified": True,
                "ts": "2026-07-20T12:00:00Z",
                "input_tokens": 150, "output_tokens": 60,
                "estimated_cost_usd": 0.00093,
            },
        ]
        monthly, stratum_agg, no_token = _aggregate_glm_metrics(metrics)
        assert stratum_agg["1-ref"]["task_count"] == 2
        assert stratum_agg["1-ref"]["total_tokens"] == 430  # (100+50)+(200+80)
        assert abs(stratum_agg["1-ref"]["estimated_cost_usd"] - 0.00194) < 1e-9
        assert stratum_agg["3-ref"]["task_count"] == 1
        assert stratum_agg["3-ref"]["total_tokens"] == 210  # 150+60

    def test_aggregate_glm_metrics_legacy_entries(self):
        """Entries without input_tokens key counted in task_count, contribute 0 tokens."""
        metrics = [
            {
                "submit_id": "legacy", "stratum": "text2image", "latency_ms": 5000,
                "success": True, "retries": 0, "vision_verified": False,
                "ts": "2026-06-01T00:00:00Z",
                # No input_tokens/output_tokens/estimated_cost_usd keys.
            },
            {
                "submit_id": "new", "stratum": "1-ref", "latency_ms": 1000,
                "success": True, "retries": 0, "vision_verified": True,
                "ts": "2026-07-01T00:00:00Z",
                "input_tokens": 100, "output_tokens": 50,
                "estimated_cost_usd": 0.0007,
            },
        ]
        monthly, stratum_agg, no_token = _aggregate_glm_metrics(metrics)
        assert no_token == 1  # the legacy entry
        # Legacy entry counted in task_count.
        assert monthly["2026-06"]["task_count"] == 1
        assert monthly["2026-06"]["input_tokens"] == 0
        assert monthly["2026-06"]["output_tokens"] == 0
        # New entry has tokens.
        assert monthly["2026-07"]["input_tokens"] == 100

    def test_aggregate_glm_metrics_empty(self):
        """Empty metrics list → empty dicts, no_token_count=0."""
        monthly, stratum_agg, no_token = _aggregate_glm_metrics([])
        assert monthly == {}
        assert stratum_agg == {}
        assert no_token == 0

    def test_cmd_glm_stats_rich(self, monkeypatch, capsys):
        """_cmd_glm_stats without --json renders Rich tables without crashing."""
        mock_metrics = [
            {
                "submit_id": "x", "stratum": "1-ref", "latency_ms": 1000,
                "success": True, "retries": 0, "vision_verified": True,
                "ts": "2026-07-10T12:00:00Z",
                "input_tokens": 100, "output_tokens": 50,
                "estimated_cost_usd": 0.0007,
            },
        ]
        import argparse
        import plugins.kais_aigc.dreamina_stats as ds

        monkeypatch.setattr(ds, "read_metrics", lambda path: mock_metrics)
        monkeypatch.setattr(ds, "_metrics_file", lambda: Path("/fake/path.jsonl"))
        args = argparse.Namespace(glm_command="stats", json=False, month=None)
        result = _cmd_glm_stats(args)
        assert result == 0
        captured = capsys.readouterr()
        # Rich table should contain the dashboard title (fixbatch-007:
        # "Vision Judge", not a specific engine brand).
        assert "Vision Judge" in captured.out

    def test_cmd_glm_stats_json(self, monkeypatch, capsys):
        """_cmd_glm_stats with --json emits valid JSON with monthly + stratum keys."""
        mock_metrics = [
            {
                "submit_id": "x", "stratum": "1-ref", "latency_ms": 1000,
                "success": True, "retries": 0, "vision_verified": True,
                "ts": "2026-07-10T12:00:00Z",
                "input_tokens": 100, "output_tokens": 50,
                "estimated_cost_usd": 0.0007,
            },
        ]
        import argparse
        import plugins.kais_aigc.dreamina_stats as ds

        monkeypatch.setattr(ds, "read_metrics", lambda path: mock_metrics)
        monkeypatch.setattr(ds, "_metrics_file", lambda: Path("/fake/path.jsonl"))
        args = argparse.Namespace(glm_command="stats", json=True, month=None)
        result = _cmd_glm_stats(args)
        assert result == 0
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert "monthly" in parsed
        assert "stratum" in parsed
        assert "2026-07" in parsed["monthly"]
        assert "1-ref" in parsed["stratum"]

    def test_cmd_glm_stats_month_filter(self, monkeypatch, capsys):
        """--month=2026-07 filters to only that month's entries."""
        mock_metrics = [
            {
                "submit_id": "jun", "stratum": "1-ref", "latency_ms": 1000,
                "success": True, "retries": 0, "vision_verified": True,
                "ts": "2026-06-15T12:00:00Z",
                "input_tokens": 50, "output_tokens": 20,
                "estimated_cost_usd": 0.00031,
            },
            {
                "submit_id": "jul", "stratum": "1-ref", "latency_ms": 1000,
                "success": True, "retries": 0, "vision_verified": True,
                "ts": "2026-07-10T12:00:00Z",
                "input_tokens": 100, "output_tokens": 50,
                "estimated_cost_usd": 0.0007,
            },
        ]
        import argparse
        import plugins.kais_aigc.dreamina_stats as ds

        monkeypatch.setattr(ds, "read_metrics", lambda path: mock_metrics)
        monkeypatch.setattr(ds, "_metrics_file", lambda: Path("/fake/path.jsonl"))
        args = argparse.Namespace(glm_command="stats", json=True, month="2026-07")
        result = _cmd_glm_stats(args)
        assert result == 0
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert "2026-07" in parsed["monthly"]
        assert "2026-06" not in parsed["monthly"]

    def test_cmd_glm_stats_no_token_warning(self, monkeypatch, capsys):
        """Legacy entries (no token fields) trigger warning printed to stderr."""
        mock_metrics = [
            {
                "submit_id": "legacy", "stratum": "text2image", "latency_ms": 5000,
                "success": True, "retries": 0, "vision_verified": False,
                "ts": "2026-07-01T00:00:00Z",
                # No token keys.
            },
        ]
        import argparse
        import plugins.kais_aigc.dreamina_stats as ds

        monkeypatch.setattr(ds, "read_metrics", lambda path: mock_metrics)
        monkeypatch.setattr(ds, "_metrics_file", lambda: Path("/fake/path.jsonl"))
        args = argparse.Namespace(glm_command="stats", json=True, month=None)
        result = _cmd_glm_stats(args)
        assert result == 0
        captured = capsys.readouterr()
        # Warning to stderr.
        assert "no token data" in captured.err

