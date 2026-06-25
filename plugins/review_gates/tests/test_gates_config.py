"""pytest unit tests for gates.yaml loader + validator (Phase 34-02, SC#2).

Covers the 8 V8.6 review gate definitions and the ``gate_config.py`` loader:

- ``load_gates()`` returns exactly 8 entries keyed by gate_id (CF-02 table)
- every entry exposes all required fields with sane types/values
- specific gate values match CF-02 (topic/script/render/delivery spot-checks)
- ``to_gate_config()`` returns the frozen ``GateConfig`` dataclass from
  Plan 34-01 (tests skip if ``gate.py`` is not yet present — Wave 1 parallel)
- malformed YAML is rejected with ``GateConfigError``

Reference: ``.planning/phases/34-review-gate-framework/CONTEXT.md`` (CF-02)
and ``.planning/phases/34-review-gate-framework/PATTERNS.md`` (gates.yaml format).
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

import pytest

# Reload-friendly: ensure a fresh gate_config module state per test that touches
# the YAML on disk. ``gate_config`` reads gates.yaml at import time (D-34-02), so
# tests that swap the YAML file must be able to force a re-import.
REVIEW_GATES_DIR = Path(__file__).resolve().parent.parent


def _reload_gate_config() -> Any:
    """Force reload of plugins.review_gates.gate_config (re-reads gates.yaml)."""
    mod_name = "plugins.review_gates.gate_config"
    if mod_name in sys.modules:
        return importlib.reload(sys.modules[mod_name])
    return importlib.import_module(mod_name)


# ---------------------------------------------------------------------------
# TestLoadGates
# ---------------------------------------------------------------------------

class TestLoadGates:
    """``load_gates()`` shape contract: dict of exactly 8 entries keyed by id."""

    EXPECTED_GATE_IDS = {
        "topic-gate",
        "outline-gate",
        "script-gate",
        "character-gate",
        "scene-select-gate",
        "shot-breakdown-gate",
        "render-gate",
        "delivery-gate",
    }

    def test_load_gates_returns_dict_with_exactly_8_entries(self) -> None:
        gate_config = _reload_gate_config()
        registry = gate_config.load_gates()
        assert isinstance(registry, dict)
        assert len(registry) == 8, f"expected 8 gates, got {len(registry)}"

    def test_load_gates_keys_match_the_8_gate_ids_from_cf02(self) -> None:
        gate_config = _reload_gate_config()
        registry = gate_config.load_gates()
        assert set(registry.keys()) == self.EXPECTED_GATE_IDS, (
            f"registry keys {set(registry.keys())} != expected {self.EXPECTED_GATE_IDS}"
        )

    def test_load_gates_is_idempotent(self) -> None:
        """Two calls return equal dicts (no in-place mutation)."""
        gate_config = _reload_gate_config()
        first = gate_config.load_gates()
        second = gate_config.load_gates()
        assert first == second
        assert first is not second  # fresh dict each call

    def test_registry_top_level_version_is_one(self) -> None:
        """Raw YAML doc carries version: 1 (D-34-02 immutable schema marker)."""
        import yaml
        yaml_path = REVIEW_GATES_DIR / "gates.yaml"
        with open(yaml_path, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        assert doc["version"] == 1

    def test_all_gate_ids_are_unique(self) -> None:
        import yaml
        yaml_path = REVIEW_GATES_DIR / "gates.yaml"
        with open(yaml_path, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        ids = [g["gate_id"] for g in doc["gates"]]
        assert len(ids) == len(set(ids)), f"duplicate gate_ids: {ids}"


# ---------------------------------------------------------------------------
# TestGateFieldsComplete
# ---------------------------------------------------------------------------

class TestGateFieldsComplete:
    """Every entry has all required fields with valid types/values."""

    REQUIRED_FIELDS = (
        "gate_id",
        "phase",
        "asset_bus_slots_to_lock",
        "reviewer_role",
        "timeout_sec",
        "default_mode",
        "retry_policy",
    )

    def test_every_entry_has_all_required_fields_with_valid_values(self) -> None:
        gate_config = _reload_gate_config()
        registry = gate_config.load_gates()
        for gate_id, entry in registry.items():
            for field in self.REQUIRED_FIELDS:
                assert field in entry, f"{gate_id} missing {field}"
            # asset_bus_slots_to_lock: non-empty list
            slots = entry["asset_bus_slots_to_lock"]
            assert isinstance(slots, list) and len(slots) > 0, (
                f"{gate_id}.asset_bus_slots_to_lock must be non-empty list"
            )
            # reviewer_role: non-empty (str or list)
            rr = entry["reviewer_role"]
            assert rr, f"{gate_id}.reviewer_role must be non-empty"
            assert isinstance(rr, (str, list)), (
                f"{gate_id}.reviewer_role must be str or list, got {type(rr)}"
            )
            # timeout_sec: positive int
            assert isinstance(entry["timeout_sec"], int) and entry["timeout_sec"] > 0, (
                f"{gate_id}.timeout_sec must be positive int"
            )
            # callback_url: str or null
            cu = entry.get("callback_url")
            assert cu is None or isinstance(cu, str), (
                f"{gate_id}.callback_url must be str or null"
            )
            # default_mode: valid enum
            assert entry["default_mode"] in {"blocking", "webhook", "polling"}, (
                f"{gate_id}.default_mode invalid: {entry['default_mode']}"
            )
            # retry_policy: dict with max_retries>0 and backoff_sec>0
            rp = entry["retry_policy"]
            assert isinstance(rp, dict), f"{gate_id}.retry_policy must be dict"
            assert isinstance(rp.get("max_retries"), int) and rp["max_retries"] > 0, (
                f"{gate_id}.retry_policy.max_retries must be positive int"
            )
            assert isinstance(rp.get("backoff_sec"), int) and rp["backoff_sec"] > 0, (
                f"{gate_id}.retry_policy.backoff_sec must be positive int"
            )


# ---------------------------------------------------------------------------
# TestSpecificGateValues
# ---------------------------------------------------------------------------

class TestSpecificGateValues:
    """Spot-checks anchoring CF-02 values (catches silent YAML drift)."""

    def test_topic_script_render_delivery_values_match_cf02(self) -> None:
        gate_config = _reload_gate_config()
        registry = gate_config.load_gates()

        topic = registry["topic-gate"]
        assert topic["phase"] == "p01_hook_topic"
        assert topic["reviewer_role"] == "creative_source"
        assert topic["default_mode"] == "blocking"
        assert topic["retry_policy"]["max_retries"] == 2

        render = registry["render-gate"]
        assert render["default_mode"] == "webhook"
        assert render["retry_policy"]["max_retries"] == 1
        assert render["retry_policy"]["backoff_sec"] == 1800

        # delivery-gate: reviewer_role includes compliance_marketing (list form)
        delivery = registry["delivery-gate"]
        rr = delivery["reviewer_role"]
        rr_items = rr if isinstance(rr, list) else [rr]
        assert "compliance_marketing" in rr_items, (
            f"delivery-gate reviewer_role must include compliance_marketing: {rr}"
        )

    def test_script_gate_has_two_reviewers_and_longer_timeout(self) -> None:
        """script-gate: script_auditor + compliance_gate, timeout 7200, 3 retries."""
        gate_config = _reload_gate_config()
        registry = gate_config.load_gates()
        script = registry["script-gate"]
        rr = script["reviewer_role"]
        rr_items = rr if isinstance(rr, list) else [rr]
        assert "script_auditor" in rr_items
        assert "compliance_gate" in rr_items
        assert script["timeout_sec"] == 7200
        assert script["retry_policy"]["max_retries"] == 3


# ---------------------------------------------------------------------------
# TestGateConfigConversion
# ---------------------------------------------------------------------------

# Plan 34-01 owns gate.py; in Wave 1 parallel execution it may not yet exist.
# These conversion tests skip cleanly until 34-01 lands, then enforce the
# frozen-dataclass contract. We use a per-class skip guard (NOT a module-level
# importorskip, which would skip the entire file and hide YAML/loader failures).
def _gate_module_available() -> bool:
    try:
        importlib.import_module("plugins.review_gates.gate")
        return True
    except ImportError:
        return False


@pytest.mark.skipif(
    not _gate_module_available(),
    reason="Plan 34-01 gate.py not yet landed (Wave 1 parallel)",
)
class TestGateConfigConversion:
    """``to_gate_config()`` returns the frozen GateConfig dataclass."""

    def test_to_gate_config_returns_frozen_gateconfig(self) -> None:
        gate_config = _reload_gate_config()
        gc = gate_config.to_gate_config("topic-gate")
        # GateConfig dataclass from Plan 34-01 (frozen=True)
        assert gc.gate_id == "topic-gate"
        assert gc.phase == "p01_hook_topic"
        assert gc.default_mode.value == "blocking"
        assert gc.max_retries == 2

    def test_gateconfig_is_immutable_and_slots_are_tuple(self) -> None:
        gate_config = _reload_gate_config()
        gc = gate_config.to_gate_config("render-gate")
        # immutability: setattr must raise (frozen=True)
        with pytest.raises((AttributeError, TypeError)):
            gc.timeout_sec = 0  # type: ignore[misc]
        # asset_bus_slots_to_lock is tuple, not list
        assert isinstance(gc.asset_bus_slots_to_lock, tuple), (
            f"expected tuple, got {type(gc.asset_bus_slots_to_lock)}"
        )

    def test_to_gate_config_normalizes_reviewer_role_list_to_string(self) -> None:
        """script-gate reviewer_role list -> comma-joined string on GateConfig."""
        gate_config = _reload_gate_config()
        gc = gate_config.to_gate_config("script-gate")
        assert isinstance(gc.reviewer_role, str)
        assert "script_auditor" in gc.reviewer_role
        assert "compliance_gate" in gc.reviewer_role


# ---------------------------------------------------------------------------
# TestYAMLValidationRejects
# ---------------------------------------------------------------------------

class TestYAMLValidationRejects:
    """Malformed YAML must raise GateConfigError with a helpful message."""

    def _write_temp_gates_yaml(self, tmp_path: Path, content: str) -> Path:
        """Stage a fake review_gates package dir with a substituted gates.yaml.

        We swap the module-level ``_YAML_PATH`` via monkeypatch instead of
        touching the real file, so parallel plans are not affected.
        """
        yaml_path = tmp_path / "gates.yaml"
        yaml_path.write_text(content, encoding="utf-8")
        return yaml_path

    def test_missing_required_field_raises_gateconfigerror(self, tmp_path: Path, monkeypatch) -> None:
        gate_config = _reload_gate_config()
        bad_yaml = (
            "version: 1\n"
            "gates:\n"
            "  - gate_id: broken-gate\n"
            "    phase: p01_hook_topic\n"
            "    # missing asset_bus_slots_to_lock, reviewer_role, etc.\n"
        )
        # Pad to 8 entries so the count check passes and we reach field check
        for i in range(7):
            bad_yaml += (
                f"  - gate_id: pad-{i}\n"
                f"    phase: p0{i}_x\n"
                f"    asset_bus_slots_to_lock: ['x']\n"
                f"    reviewer_role: r\n"
                f"    timeout_sec: 60\n"
                f"    default_mode: blocking\n"
                f"    retry_policy: {{max_retries: 1, backoff_sec: 30}}\n"
            )
        yaml_path = self._write_temp_gates_yaml(tmp_path, bad_yaml)
        monkeypatch.setattr(gate_config, "_YAML_PATH", yaml_path)
        with pytest.raises(gate_config.GateConfigError) as exc_info:
            gate_config.load_gates()
        assert "missing required field" in str(exc_info.value)

    def test_bad_mode_enum_raises_gateconfigerror(self, tmp_path: Path, monkeypatch) -> None:
        gate_config = _reload_gate_config()
        entries = []
        for i in range(8):
            mode = "blocking" if i > 0 else "bogus_mode"
            entries.append(
                f"  - gate_id: g{i}\n"
                f"    phase: p{i}\n"
                f"    asset_bus_slots_to_lock: ['x']\n"
                f"    reviewer_role: r\n"
                f"    timeout_sec: 60\n"
                f"    default_mode: {mode}\n"
                f"    retry_policy: {{max_retries: 1, backoff_sec: 30}}\n"
            )
        bad_yaml = "version: 1\ngates:\n" + "".join(entries)
        yaml_path = self._write_temp_gates_yaml(tmp_path, bad_yaml)
        monkeypatch.setattr(gate_config, "_YAML_PATH", yaml_path)
        with pytest.raises(gate_config.GateConfigError) as exc_info:
            gate_config.load_gates()
        assert "default_mode" in str(exc_info.value)

    def test_negative_timeout_raises_gateconfigerror(self, tmp_path: Path, monkeypatch) -> None:
        gate_config = _reload_gate_config()
        entries = []
        for i in range(8):
            timeout = 60 if i > 0 else -1
            entries.append(
                f"  - gate_id: g{i}\n"
                f"    phase: p{i}\n"
                f"    asset_bus_slots_to_lock: ['x']\n"
                f"    reviewer_role: r\n"
                f"    timeout_sec: {timeout}\n"
                f"    default_mode: blocking\n"
                f"    retry_policy: {{max_retries: 1, backoff_sec: 30}}\n"
            )
        bad_yaml = "version: 1\ngates:\n" + "".join(entries)
        yaml_path = self._write_temp_gates_yaml(tmp_path, bad_yaml)
        monkeypatch.setattr(gate_config, "_YAML_PATH", yaml_path)
        with pytest.raises(gate_config.GateConfigError) as exc_info:
            gate_config.load_gates()
        assert "timeout_sec" in str(exc_info.value)
