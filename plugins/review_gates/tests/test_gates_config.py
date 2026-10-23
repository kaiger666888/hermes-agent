"""pytest unit tests for gates.yaml loader + validator.

Phase 34-02 originally introduced this file (SC#2). Phase 40 Plan 02
(GATE-04) expanded 8 → 11 gates additively. Phase 8 / Plan 08-01 (FIX-01)
refactored the schema to be **phase_id-keyed** with no standalone
``gate_id`` field — this file was updated to match.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

import pytest

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
    """``load_gates()`` shape contract: dict of exactly
    ``_EXPECTED_GATE_COUNT`` entries keyed by phase_id (Phase 8 / 08-01
    FIX-01 refactor; 2026-08-18 冗余审核体系 appends vision-review gates
    in lock-step with each node's wiring — count + key set grow together;
    2026-08-25 ICA M4 grows the registry Gate 16 → Gate 17 with
    p14_quality_audit, fixbatch-004 syncs this expected key set)."""

    V86_PHASE_KEYS = {
        "p01_hook_topic",
        "p02_outline",
        "p03_script_audit",
        # DIALOGUE-REFORM (2026-07-28): Gate 4 reverted from p05 (removed
        # from the chain) back to p04.
        "p04_character_design",
        "p06_spatio_temporal_script",
        "p07_scene_generation",
        "p11b_final_render",
        "p13_delivery",
    }

    REDLINE_PHASE_KEYS = {
        "p13_delivery_redline_emotion",
        "p13_delivery_redline_no_cold_open",
        "p13_delivery_redline_unfinished",
    }

    # 2026-08-18 冗余审核体系: vision-review gates, one per wired node task
    # (complete set: p09c / p11a0 / p11a / p11c).
    VISION_REVIEW_PHASE_KEYS = {
        "p09c_storyboard_board",  # Gate 12 (T7)
        "p11a0_iframe_qc",        # Gate 13 (T8)
        "p11a_preview_clips",     # Gate 14 (T9)
        "p11c_video_qc",          # Gate 15 (T10)
    }

    # 2026-08-19 冗余审核体系·音频: Gate 16 (kais-ear transcription fidelity)
    AUDIO_REVIEW_PHASE_KEYS = {
        "p10c_voice_audit",
    }

    # 2026-08-25 ICA M4: Gate 17 p14_quality_audit（质量审计自动阻塞门，
    # 经 blocking_policies 生效）— 期望集合补同步（fixbatch-004）。
    QUALITY_AUDIT_PHASE_KEYS = {
        "p14_quality_audit",
    }

    # NC-VAR-01 (2026-08-26 B1): Gate 18 nc01 解说词审 + Gate 19 nc08 终审。
    # NOTE（2026-10-15 MV-VAR 接线批补记）: nc 接线时本期望集合漏了同步，
    # 三个 count/key 断言自此基线红（19 != 17）—— 本次随 MV-VAR 一并修复
    # （nc 补录 + mv 新增），锁-step 纪律恢复。
    NC_VARIANT_PHASE_KEYS = {
        "nc01_narration",       # Gate 18 (NC-1) 解说词审
        "nc08_qc_delivery",     # Gate 19 (NC-8) 成片终审
    }

    # MV-VAR (2026-10-15): Gate 20 mv01 歌曲包入料审 + Gate 21 mv03 音乐
    # 锚定分镜审（mv-variant-dag/DESIGN.md §5.4/§5.5）。
    MV_VARIANT_PHASE_KEYS = {
        "mv01_song_intake",            # Gate 20 (MV-1) 歌曲包入料审
        "mv03_music_shot_breakdown",   # Gate 21 (MV-3) 音乐锚定分镜审
    }

    EXPECTED_PHASE_KEYS = (
        V86_PHASE_KEYS | REDLINE_PHASE_KEYS | VISION_REVIEW_PHASE_KEYS
        | AUDIO_REVIEW_PHASE_KEYS | QUALITY_AUDIT_PHASE_KEYS
        | NC_VARIANT_PHASE_KEYS | MV_VARIANT_PHASE_KEYS
    )

    def test_load_gates_returns_dict_with_expected_entry_count(self) -> None:
        gate_config = _reload_gate_config()
        registry = gate_config.load_gates()
        assert isinstance(registry, dict)
        expected = gate_config._EXPECTED_GATE_COUNT
        assert len(registry) == expected, (
            f"expected {expected} gates, got {len(registry)}"
        )
        # The expected key set and the count constant must stay in lock-step.
        assert expected == len(self.EXPECTED_PHASE_KEYS)

    def test_load_gates_keys_match_the_expected_phase_ids(self) -> None:
        gate_config = _reload_gate_config()
        registry = gate_config.load_gates()
        assert set(registry.keys()) == self.EXPECTED_PHASE_KEYS, (
            f"registry keys {set(registry.keys())} != expected {self.EXPECTED_PHASE_KEYS}"
        )

    def test_load_gates_preserves_8_v86_phase_keys(self) -> None:
        gate_config = _reload_gate_config()
        registry = gate_config.load_gates()
        assert self.V86_PHASE_KEYS.issubset(set(registry.keys())), (
            f"missing V8.6 phase keys: {self.V86_PHASE_KEYS - set(registry.keys())}"
        )

    def test_load_gates_includes_3_redline_phase_keys(self) -> None:
        gate_config = _reload_gate_config()
        registry = gate_config.load_gates()
        assert self.REDLINE_PHASE_KEYS.issubset(set(registry.keys())), (
            f"missing redline keys: {self.REDLINE_PHASE_KEYS - set(registry.keys())}"
        )

    def test_load_gates_is_idempotent(self) -> None:
        gate_config = _reload_gate_config()
        first = gate_config.load_gates()
        second = gate_config.load_gates()
        assert first == second
        assert first is not second

    def test_registry_top_level_version_is_two(self) -> None:
        """Phase 8 FIX-01 bumped the YAML schema version marker to 2."""
        import yaml
        yaml_path = REVIEW_GATES_DIR / "gates.yaml"
        with open(yaml_path, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        assert doc["version"] == 2

    def test_all_phase_keys_are_unique(self) -> None:
        import yaml
        yaml_path = REVIEW_GATES_DIR / "gates.yaml"
        with open(yaml_path, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        keys = list(doc["gates"].keys())
        assert len(keys) == len(set(keys))
        assert len(keys) == len(self.EXPECTED_PHASE_KEYS)

    def test_entries_have_no_standalone_gate_id_field(self) -> None:
        """Phase 8 FIX-01: gates.yaml entries MUST NOT carry a standalone
        'gate_id' field — it's derived from the phase_id key."""
        gate_config = _reload_gate_config()
        registry = gate_config.load_gates()
        for key, entry in registry.items():
            assert "gate_id" not in entry, (
                f"gates.yaml entry {key!r} carries a stale 'gate_id' field "
                f"(Phase 8 FIX-01 removed it — gate_id derived from key)"
            )


# ---------------------------------------------------------------------------
# TestGateFieldsComplete
# ---------------------------------------------------------------------------

class TestGateFieldsComplete:
    REQUIRED_FIELDS = (
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
        for phase_key, entry in registry.items():
            for field in self.REQUIRED_FIELDS:
                assert field in entry, f"{phase_key} missing {field}"
            slots = entry["asset_bus_slots_to_lock"]
            assert isinstance(slots, list) and len(slots) > 0
            rr = entry["reviewer_role"]
            assert rr
            assert isinstance(rr, (str, list))
            assert isinstance(entry["timeout_sec"], int) and entry["timeout_sec"] > 0
            cu = entry.get("callback_url")
            assert cu is None or isinstance(cu, str)
            assert entry["default_mode"] in {"blocking", "webhook", "polling"}
            rp = entry["retry_policy"]
            assert isinstance(rp, dict)
            assert isinstance(rp.get("max_retries"), int) and rp["max_retries"] > 0
            assert isinstance(rp.get("backoff_sec"), int) and rp["backoff_sec"] > 0


# ---------------------------------------------------------------------------
# TestSpecificGateValues
# ---------------------------------------------------------------------------

class TestSpecificGateValues:
    def test_topic_script_render_delivery_values_match_cf02(self) -> None:
        gate_config = _reload_gate_config()
        registry = gate_config.load_gates()

        topic = registry["p01_hook_topic"]
        assert topic["phase"] == "p01_hook_topic"
        assert topic["reviewer_role"] == "creative_source"
        assert topic["default_mode"] == "blocking"
        assert topic["retry_policy"]["max_retries"] == 2

        render = registry["p11b_final_render"]
        assert render["default_mode"] == "webhook"
        assert render["retry_policy"]["max_retries"] == 1
        assert render["retry_policy"]["backoff_sec"] == 1800

        delivery = registry["p13_delivery"]
        rr = delivery["reviewer_role"]
        rr_items = rr if isinstance(rr, list) else [rr]
        assert "compliance_marketing" in rr_items

    def test_script_gate_has_two_reviewers_and_longer_timeout(self) -> None:
        gate_config = _reload_gate_config()
        registry = gate_config.load_gates()
        script = registry["p03_script_audit"]
        rr = script["reviewer_role"]
        rr_items = rr if isinstance(rr, list) else [rr]
        assert "script_auditor" in rr_items
        assert "compliance_gate" in rr_items
        assert script["timeout_sec"] == 7200
        assert script["retry_policy"]["max_retries"] == 3


# ---------------------------------------------------------------------------
# TestRedlineGates
# ---------------------------------------------------------------------------


class TestRedlineGates:
    REDLINE_PHASE_KEYS = (
        "p13_delivery_redline_emotion",
        "p13_delivery_redline_no_cold_open",
        "p13_delivery_redline_unfinished",
    )

    def test_each_redline_gate_has_valid_default_mode(self) -> None:
        gate_config = _reload_gate_config()
        registry = gate_config.load_gates()
        for phase_key in self.REDLINE_PHASE_KEYS:
            assert registry[phase_key]["default_mode"] == "blocking"

    def test_each_redline_gate_has_redline_scanner_reviewer(self) -> None:
        gate_config = _reload_gate_config()
        registry = gate_config.load_gates()
        for phase_key in self.REDLINE_PHASE_KEYS:
            rr = registry[phase_key]["reviewer_role"]
            assert rr == "redline_scanner"

    def test_each_redline_gate_has_positive_timeout(self) -> None:
        gate_config = _reload_gate_config()
        registry = gate_config.load_gates()
        for phase_key in self.REDLINE_PHASE_KEYS:
            timeout = registry[phase_key]["timeout_sec"]
            assert isinstance(timeout, int) and timeout > 0
            assert timeout <= 300

    def test_each_redline_gate_retry_policy_max_retries_positive(self) -> None:
        gate_config = _reload_gate_config()
        registry = gate_config.load_gates()
        for phase_key in self.REDLINE_PHASE_KEYS:
            rp = registry[phase_key]["retry_policy"]
            assert isinstance(rp, dict)
            assert rp.get("max_retries", 0) > 0
            assert rp.get("backoff_sec", 0) > 0

    def test_each_redline_gate_maps_to_p13_delivery_phase(self) -> None:
        gate_config = _reload_gate_config()
        registry = gate_config.load_gates()
        for phase_key in self.REDLINE_PHASE_KEYS:
            assert registry[phase_key]["phase"] == "p13_delivery"

    def test_each_redline_gate_locks_final_shots_slot(self) -> None:
        gate_config = _reload_gate_config()
        registry = gate_config.load_gates()
        for phase_key in self.REDLINE_PHASE_KEYS:
            slots = registry[phase_key]["asset_bus_slots_to_lock"]
            assert "final-shots" in slots

    def test_each_redline_gate_derives_to_p13_gate(self) -> None:
        """Phase 8 FIX-01: all 3 redline sub-keys derive to 'p13-gate'."""
        gate_config = _reload_gate_config()
        for phase_key in self.REDLINE_PHASE_KEYS:
            derived = gate_config.derive_gate_id(phase_key)
            assert derived == "p13-gate"


# ---------------------------------------------------------------------------
# TestGateConfigConversion
# ---------------------------------------------------------------------------

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
    """``to_gate_config()`` returns the frozen GateConfig dataclass.

    Phase 8: to_gate_config now accepts phase_id OR legacy gate_id (backward
    compat). The returned GateConfig.gate_id is the DERIVED canonical form."""

    def test_to_gate_config_returns_frozen_gateconfig(self) -> None:
        gate_config = _reload_gate_config()
        gc = gate_config.to_gate_config("p01_hook_topic")
        assert gc.gate_id == "p01-gate"
        assert gc.phase == "p01_hook_topic"
        assert gc.default_mode.value == "blocking"
        assert gc.max_retries == 2

    def test_to_gate_config_accepts_legacy_gate_id(self) -> None:
        """Phase 8 backward compat: legacy raw gate_id ('topic-gate')
        resolves to the same entry as phase_id ('p01_hook_topic')."""
        gate_config = _reload_gate_config()
        gc_legacy = gate_config.to_gate_config("topic-gate")
        gc_new = gate_config.to_gate_config("p01_hook_topic")
        assert gc_legacy.gate_id == gc_new.gate_id == "p01-gate"
        assert gc_legacy.phase == gc_new.phase == "p01_hook_topic"

    def test_gateconfig_is_immutable_and_slots_are_tuple(self) -> None:
        gate_config = _reload_gate_config()
        gc = gate_config.to_gate_config("p11b_final_render")
        with pytest.raises((AttributeError, TypeError)):
            gc.timeout_sec = 0  # type: ignore[misc]
        assert isinstance(gc.asset_bus_slots_to_lock, tuple)

    def test_to_gate_config_normalizes_reviewer_role_list_to_string(self) -> None:
        gate_config = _reload_gate_config()
        gc = gate_config.to_gate_config("p03_script_audit")
        assert isinstance(gc.reviewer_role, str)
        assert "script_auditor" in gc.reviewer_role
        assert "compliance_gate" in gc.reviewer_role


# ---------------------------------------------------------------------------
# TestYAMLValidationRejects
# ---------------------------------------------------------------------------

class TestYAMLValidationRejects:
    """Malformed YAML must raise GateConfigError.

    Phase 8 / 08-01: the YAML schema is a phase_id-keyed mapping."""

    def _write_temp_gates_yaml(self, tmp_path: Path, content: str) -> Path:
        yaml_path = tmp_path / "gates.yaml"
        yaml_path.write_text(content, encoding="utf-8")
        return yaml_path

    def test_missing_required_field_raises_gateconfigerror(self, tmp_path: Path, monkeypatch) -> None:
        gate_config = _reload_gate_config()
        entries_yaml = (
            "version: 2\n"
            "gates:\n"
            "  p01_broken:\n"
            "    phase: p01_broken\n"
            "    # missing asset_bus_slots_to_lock, reviewer_role, etc.\n"
        )
        for i in range(gate_config._EXPECTED_GATE_COUNT - 1):
            entries_yaml += (
                f"  p0{i}_pad:\n"
                f"    phase: p0{i}_pad\n"
                f"    asset_bus_slots_to_lock: ['x']\n"
                f"    reviewer_role: r\n"
                f"    timeout_sec: 60\n"
                f"    default_mode: blocking\n"
                f"    retry_policy: {{max_retries: 1, backoff_sec: 30}}\n"
            )
        yaml_path = self._write_temp_gates_yaml(tmp_path, entries_yaml)
        monkeypatch.setattr(gate_config, "_YAML_PATH", yaml_path)
        with pytest.raises(gate_config.GateConfigError) as exc_info:
            gate_config.load_gates()
        assert "missing required field" in str(exc_info.value)

    def test_bad_mode_enum_raises_gateconfigerror(self, tmp_path: Path, monkeypatch) -> None:
        gate_config = _reload_gate_config()
        entries_yaml = "version: 2\ngates:\n"
        for i in range(gate_config._EXPECTED_GATE_COUNT):
            mode = "blocking" if i > 0 else "bogus_mode"
            entries_yaml += (
                f"  p{i:02d}_phase:\n"
                f"    phase: p{i:02d}_phase\n"
                f"    asset_bus_slots_to_lock: ['x']\n"
                f"    reviewer_role: r\n"
                f"    timeout_sec: 60\n"
                f"    default_mode: {mode}\n"
                f"    retry_policy: {{max_retries: 1, backoff_sec: 30}}\n"
            )
        yaml_path = self._write_temp_gates_yaml(tmp_path, entries_yaml)
        monkeypatch.setattr(gate_config, "_YAML_PATH", yaml_path)
        with pytest.raises(gate_config.GateConfigError) as exc_info:
            gate_config.load_gates()
        assert "default_mode" in str(exc_info.value)

    def test_negative_timeout_raises_gateconfigerror(self, tmp_path: Path, monkeypatch) -> None:
        gate_config = _reload_gate_config()
        entries_yaml = "version: 2\ngates:\n"
        for i in range(gate_config._EXPECTED_GATE_COUNT):
            timeout = 60 if i > 0 else -1
            entries_yaml += (
                f"  p{i:02d}_phase:\n"
                f"    phase: p{i:02d}_phase\n"
                f"    asset_bus_slots_to_lock: ['x']\n"
                f"    reviewer_role: r\n"
                f"    timeout_sec: {timeout}\n"
                f"    default_mode: blocking\n"
                f"    retry_policy: {{max_retries: 1, backoff_sec: 30}}\n"
            )
        yaml_path = self._write_temp_gates_yaml(tmp_path, entries_yaml)
        monkeypatch.setattr(gate_config, "_YAML_PATH", yaml_path)
        with pytest.raises(gate_config.GateConfigError) as exc_info:
            gate_config.load_gates()
        assert "timeout_sec" in str(exc_info.value)

    def test_wrong_count_raises_gateconfigerror(self, tmp_path: Path, monkeypatch) -> None:
        gate_config = _reload_gate_config()
        entries_yaml = "version: 2\ngates:\n"
        for i in range(8):
            entries_yaml += (
                f"  p{i:02d}_phase:\n"
                f"    phase: p{i:02d}_phase\n"
                f"    asset_bus_slots_to_lock: ['x']\n"
                f"    reviewer_role: r\n"
                f"    timeout_sec: 60\n"
                f"    default_mode: blocking\n"
                f"    retry_policy: {{max_retries: 1, backoff_sec: 30}}\n"
            )
        yaml_path = self._write_temp_gates_yaml(tmp_path, entries_yaml)
        monkeypatch.setattr(gate_config, "_YAML_PATH", yaml_path)
        with pytest.raises(gate_config.GateConfigError) as exc_info:
            gate_config.load_gates()
        assert "exactly" in str(exc_info.value) and "gates" in str(exc_info.value)

    def test_standalone_gate_id_field_rejected(self, tmp_path: Path, monkeypatch) -> None:
        """Phase 8 FIX-01: any entry still carrying a standalone 'gate_id'
        field must be rejected — forces clean migration."""
        gate_config = _reload_gate_config()
        entries_yaml = "version: 2\ngates:\n"
        entries_yaml += (
            "  p01_hook_topic:\n"
            "    phase: p01_hook_topic\n"
            "    gate_id: topic-gate\n"
            "    asset_bus_slots_to_lock: ['x']\n"
            "    reviewer_role: r\n"
            "    timeout_sec: 60\n"
            "    default_mode: blocking\n"
            "    retry_policy: {max_retries: 1, backoff_sec: 30}\n"
        )
        for i in range(gate_config._EXPECTED_GATE_COUNT - 1):
            entries_yaml += (
                f"  p{i+2:02d}_phase:\n"
                f"    phase: p{i+2:02d}_phase\n"
                f"    asset_bus_slots_to_lock: ['x']\n"
                f"    reviewer_role: r\n"
                f"    timeout_sec: 60\n"
                f"    default_mode: blocking\n"
                f"    retry_policy: {{max_retries: 1, backoff_sec: 30}}\n"
            )
        yaml_path = self._write_temp_gates_yaml(tmp_path, entries_yaml)
        monkeypatch.setattr(gate_config, "_YAML_PATH", yaml_path)
        with pytest.raises(gate_config.GateConfigError) as exc_info:
            gate_config.load_gates()
        assert "standalone" in str(exc_info.value).lower() or "gate_id" in str(exc_info.value)
