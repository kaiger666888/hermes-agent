"""Tests for ``scripts/run_latency_benchmark.py`` ``--backend mem0`` flag
(Phase 60 plan 01 Task 2).

Three behaviors pinned:

1. ``--fixture`` path regression: existing JSON shape still works, p95
   stays sub-ms on FakeBackend, ``slo_verdict == "pass"``.
2. ``--backend mem0`` without ``MEM0_API_KEY`` exits 2 with the
   documented ``MEM0_API_KEY not set`` stderr message (the
   ``_load_live_backend`` gate fires before the benchmark loop).
3. ``--fixture`` and ``--backend`` are mutually exclusive — argparse
   rejects both with ``not allowed with argument``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_script(args: list[str], *, env_override: dict | None = None):
    """Invoke the benchmark script as a subprocess; return CompletedProcess."""
    env = os.environ.copy()
    if env_override:
        env.update(env_override)
    return subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "run_latency_benchmark.py")] + args,
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
        timeout=60,
        env=env,
    )


# ---------------------------------------------------------------------------
# Test 1: fixture-path regression (Phase 54 behavior preserved)
# ---------------------------------------------------------------------------


class TestFixturePathRegression:
    """The ``--fixture`` path must produce the same JSON shape + verdict
    as Phase 54. This is the load-bearing regression test: Task 2 must
    NOT change fixture-mode behavior.
    """

    def test_fixture_500_still_passes_slo(self, tmp_path):
        out = tmp_path / "bench.json"
        result = _run_script([
            "--fixture", "500",
            "--runs", "5",
            "--out", str(out),
        ])
        assert result.returncode == 0, (
            f"fixture 500 failed\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert out.exists()
        with open(out, encoding="utf-8") as f:
            data = json.load(f)
        # Phase 54 contract: record_count == fixture_count.
        assert data["record_count"] == 500
        # Phase 54 contract: 5 runs.
        assert data["runs"] == 5
        # Phase 54 contract: percentiles dict has p50/p95/p99.
        assert set(["p50", "p95", "p99"]).issubset(data["percentiles"].keys())
        # Phase 54 contract: FakeBackend is structurally sub-ms → verdict pass.
        assert data["slo_verdict"] == "pass", (
            f"fixture regression: expected pass, got {data['slo_verdict']} "
            f"(p95={data['percentiles']['p95']}ms)"
        )
        # Phase 54 contract: samples_ms length == runs.
        assert len(data["samples_ms"]) == 5
        # Phase 60 Task 2 contract: new ``backend`` field == "fixture".
        assert data["backend"] == "fixture"
        # Phase 60 Task 2 contract: ``agent_id`` field present.
        assert "agent_id" in data

    def test_fixture_100_sub_ms(self, tmp_path):
        """Smallest fixture — confirms the FakeBackend floor."""
        out = tmp_path / "bench100.json"
        result = _run_script([
            "--fixture", "100",
            "--runs", "3",
            "--out", str(out),
        ])
        assert result.returncode == 0
        with open(out, encoding="utf-8") as f:
            data = json.load(f)
        assert data["slo_verdict"] == "pass"
        assert data["percentiles"]["p95"] < 1.0  # sub-ms floor


# ---------------------------------------------------------------------------
# Test 2: --backend mem0 missing-key gate
# ---------------------------------------------------------------------------


class TestLiveBackendMissingKeyGate:
    """Without ``MEM0_API_KEY``, the live-mode path must exit 2 with the
    documented stderr message — never start the benchmark loop.
    """

    def test_backend_mem0_without_key_exits_2(self, tmp_path):
        out = tmp_path / "would-not-be-written.json"
        result = _run_script(
            [
                "--backend", "mem0",
                "--record-count", "500",
                "--out", str(out),
            ],
            env_override={"MEM0_API_KEY": ""},  # explicit empty
        )
        assert result.returncode == 2, (
            f"expected exit 2, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "MEM0_API_KEY not set" in result.stderr
        # Output file must NOT have been written (gate fires before benchmark).
        assert not out.exists()

    def test_backend_mem0_with_no_fixture_arg_works_via_gate(self, tmp_path):
        """``--backend mem0`` without ``--fixture`` reaches the
        ``_load_live_backend`` gate (argparse mutually-exclusive group
        accepts it; the gate is what fails)."""
        out = tmp_path / "x.json"
        result = _run_script(
            ["--backend", "mem0", "--out", str(out)],
            env_override={"MEM0_API_KEY": ""},
        )
        assert result.returncode == 2
        assert "MEM0_API_KEY not set" in result.stderr


# ---------------------------------------------------------------------------
# Test 3: mutual-exclusion of --fixture and --backend
# ---------------------------------------------------------------------------


class TestMutualExclusion:
    """``--fixture`` and ``--backend`` are mutually exclusive. argparse
    must reject both with ``not allowed with argument``."""

    def test_both_flags_rejected(self, tmp_path):
        out = tmp_path / "x.json"
        result = _run_script([
            "--fixture", "100",
            "--backend", "mem0",
            "--out", str(out),
        ])
        assert result.returncode == 2  # argparse error
        assert "not allowed with argument" in result.stderr

    def test_neither_flag_rejected(self, tmp_path):
        """argparse mutually-exclusive group with required=True also
        rejects the case where neither flag is given."""
        out = tmp_path / "x.json"
        result = _run_script([
            "--out", str(out),
        ])
        assert result.returncode == 2
        # argparse emits "one of the arguments --fixture --backend is required"
        assert "--fixture" in result.stderr and "--backend" in result.stderr


# ---------------------------------------------------------------------------
# Test 4: --backend mem0 JSON shape (mocked backend; no real API)
# ---------------------------------------------------------------------------


class TestLiveBackendJsonShape:
    """Confirm the JSON output for ``--backend mem0`` includes the new
    ``backend`` field == "mem0" + the ``record_count`` from
    ``--record-count``. Uses a mock to avoid real API calls."""

    def test_backend_field_in_output_when_live_mode(self, monkeypatch):
        """Run ``_run_benchmark`` directly with a fake backend object so
        we don't need a real mem0 connection. The backend kwarg flow is
        the same as production — only the loader is bypassed.
        """
        # Defer import until after sys.path is set.
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
        sys.path.insert(0, str(_REPO_ROOT))
        import asyncio
        import run_latency_benchmark as bench

        # Monkey-patch the loader so we never touch real mem0.
        monkeypatch.setattr(bench, "_load_live_backend", lambda: _FastBackendBackend())

        result = asyncio.run(bench._run_benchmark(
            fixture_count=None,
            backend_mode="mem0",
            agent_id="screenplay",
            record_count=500,
            runs=3,
        ))
        assert result["backend"] == "mem0"
        assert result["record_count"] == 500
        assert result["agent_id"] == "screenplay"
        assert result["runs"] == 3
        assert result["slo_verdict"] == "pass"


class _FastBackendBackend:
    """Stand-in returned by the monkeypatched ``_load_live_backend``."""

    def search(self, *, query, agent_id, top_k):
        return [{"memory": "x", "agent_id": agent_id}]
