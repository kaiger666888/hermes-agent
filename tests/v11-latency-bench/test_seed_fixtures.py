"""Tests for the seed fixtures + benchmark script integration (Phase 54 plan 02 Task 2).

Covers the 3 behaviors from ``54-02-PLAN.md`` Task 2:

1. ``scripts/run_latency_benchmark.py --fixture 100 --out <tmp>`` writes
   a JSON file with keys ``record_count``, ``samples_ms``,
   ``percentiles``, ``slo_verdict``.
2. SLO verdict logic: pass if p95 < 500ms, fail if p95 >= 500ms with at
   least one ``ok`` status, skip if all calls ``unavailable``/``error``.
3. ``seed_500_records.build_fixture_backend()`` returns a FakeBackend
   with 500 records pre-loaded.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_FIXTURES_DIR = _REPO_ROOT / "tests" / "v11-latency-bench" / "fixtures"


def _load_fixture_module(name: str):
    """Load a fixture module by file path to avoid sys.path ambiguity.

    pytest's auto-conftest discovery + multiple test directories can leave
    `sys.modules` with stale entries or have path-ordering issues. Loading
    by file path (importlib.util) is unambiguous.
    """
    import importlib.util as _ilu
    fp = _FIXTURES_DIR / f"{name}.py"
    spec = _ilu.spec_from_file_location(f"_v11_fixture_{name}", fp)
    assert spec is not None and spec.loader is not None, f"cannot load {fp}"
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Test 1: seed fixtures return correct record counts ──────────────────────


class TestSeedFixtures:
    """All 3 seed modules build a backend with the claimed record count."""

    def test_seed_100_records(self):
        m = _load_fixture_module("seed_100_records")
        backend = m.build_fixture_backend()
        assert len(backend) == 100
        # All records belong to the same agent_id (scoped filter target).
        assert all(r["agent_id"] == "ag1" for r in backend.records)

    def test_seed_500_records(self):
        m = _load_fixture_module("seed_500_records")
        backend = m.build_fixture_backend()
        assert len(backend) == 500
        assert all(r["agent_id"] == "ag1" for r in backend.records)

    def test_seed_1000_records(self):
        m = _load_fixture_module("seed_1000_records")
        backend = m.build_fixture_backend()
        assert len(backend) == 1000
        assert all(r["agent_id"] == "ag1" for r in backend.records)

    def test_fixtures_are_deterministic(self):
        """Two builds of the same fixture must produce identical record lists."""
        m = _load_fixture_module("seed_500_records")
        b1 = m.build_fixture_backend()
        b2 = m.build_fixture_backend()
        assert (
            [r["content"] for r in b1.records]
            == [r["content"] for r in b2.records]
        )


# ── Test 2: SLO verdict logic ───────────────────────────────────────────────


class TestSLOVerdictLogic:
    """Direct tests of ``_compute_slo_verdict``."""

    def test_pass_when_p95_below_threshold_and_at_least_one_ok(self):
        # Import via the script's module path.
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
        import run_latency_benchmark as bench
        verdict = bench._compute_slo_verdict(
            statuses=["ok"] * 100, p95=499.99,
        )
        assert verdict == "pass"

    def test_fail_when_p95_at_or_above_threshold_and_at_least_one_ok(self):
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
        import run_latency_benchmark as bench
        verdict = bench._compute_slo_verdict(
            statuses=["ok"] * 100, p95=500.0,
        )
        assert verdict == "fail"
        verdict = bench._compute_slo_verdict(
            statuses=["ok", "unavailable", "error"], p95=1234.5,
        )
        assert verdict == "fail"

    def test_skip_when_no_ok_status(self):
        """Even if p95 is "low", if no call succeeded, SLO cannot be measured."""
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
        import run_latency_benchmark as bench
        verdict = bench._compute_slo_verdict(
            statuses=["unavailable"] * 100, p95=10.0,
        )
        assert verdict == "skip"
        verdict = bench._compute_slo_verdict(
            statuses=["error"] * 100, p95=10.0,
        )
        assert verdict == "skip"


# ── Test 3: benchmark script end-to-end on FakeBackend ──────────────────────


class TestBenchmarkScriptEndToEnd:
    """Run the script as a subprocess on all 3 fixtures; verify JSON output."""

    @pytest.mark.parametrize("fixture_count", [100, 500, 1000])
    def test_script_produces_valid_json(self, tmp_path, fixture_count):
        out_path = tmp_path / f"bench_{fixture_count}.json"
        import subprocess
        result = subprocess.run(
            [
                sys.executable,
                str(_REPO_ROOT / "scripts" / "run_latency_benchmark.py"),
                "--fixture", str(fixture_count),
                "--out", str(out_path),
            ],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
            timeout=60,
        )
        assert result.returncode == 0, (
            f"benchmark failed fixture={fixture_count}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert out_path.exists(), "output JSON not written"
        with open(out_path, encoding="utf-8") as f:
            data = json.load(f)
        # Schema contract per 54-02-PLAN.md Task 2 Test 1.
        assert data["record_count"] == fixture_count
        assert len(data["samples_ms"]) == 100
        assert set(["p50", "p95", "p99"]).issubset(data["percentiles"].keys())
        assert data["slo_verdict"] in ("pass", "fail", "skip")
        # On FakeBackend (deterministic, fast), verdict must be "pass".
        # This locks the CI contract: the FakeBackend must NOT trip the
        # SLO — it is structurally sub-ms.
        assert data["slo_verdict"] == "pass", (
            f"FakeBackend fixture={fixture_count} unexpectedly tripped SLO "
            f"(p95={data['percentiles']['p95']}ms) — fixture-only benchmark "
            f"must stay sub-ms by construction."
        )
