"""Tests for scripts/run_screenplay_step3_roundtable.py — Phase 58 THROTTLE-01.

Validates that the v11.0 hardcoded ``asyncio.sleep(2.5)`` (between panelists)
and ``asyncio.sleep(5.0)`` (pre-synthesis) RPM-pacing patches have been
removed. Per-task RPM pacing is now handled by ``agent/glm_throttle.py``
inside ``auxiliary_client.call_llm`` (Phase 58 THROTTLE-01).

Context: see .planning/phases/58-rpm-throttling/58-01-PLAN.md Task 3
         and smoke-test-report.md §3.1 (v11.0 evidence).
"""
from __future__ import annotations

from pathlib import Path

_DRIVER = Path(__file__).resolve().parent.parent / "scripts" / "run_screenplay_step3_roundtable.py"


class TestDriverScriptThrottleMigration:
    """Phase 58 THROTTLE-01 — confirm hardcoded sleeps are gone."""

    def test_driver_script_has_no_hardcoded_2_5s_sleep(self):
        """The v11.0 ``await asyncio.sleep(2.5)`` patch must be removed.

        Phase 58 THROTTLE-01 replaces it with per-task RPM token bucket
        pacing in agent/glm_throttle.py (acquire_slot invoked inside
        auxiliary_client.call_llm before dispatch).
        """
        source = _DRIVER.read_text(encoding="utf-8")
        assert "await asyncio.sleep(2.5)" not in source, (
            "Phase 58 must remove hardcoded 'await asyncio.sleep(2.5)' RPM "
            "pacing — agent/glm_throttle.py handles it now."
        )

    def test_driver_script_has_no_hardcoded_5s_pre_synthesis_sleep(self):
        """The v11.0 ``await asyncio.sleep(5.0)`` pre-synthesis patch must
        be removed (same reason as the 2.5s panelist sleep)."""
        source = _DRIVER.read_text(encoding="utf-8")
        assert "await asyncio.sleep(5.0)" not in source, (
            "Phase 58 must remove hardcoded 'await asyncio.sleep(5.0)' "
            "pre-synthesis pacing — agent/glm_throttle.py handles it now."
        )

    def test_driver_script_documents_phase_58_migration(self):
        """Module docstring must cross-reference Phase 58 THROTTLE-01 so
        future readers understand why the v11.0 sleeps were removed."""
        source = _DRIVER.read_text(encoding="utf-8")
        assert "Phase 58 THROTTLE-01" in source, (
            "Driver script module docstring must mention Phase 58 "
            "THROTTLE-01 migration."
        )
        assert "agent/glm_throttle.py" in source, (
            "Driver script must point readers at the new throttle module."
        )
