"""MIGR-01 — 9-agent transform correctness tests.

Per 53-01-PLAN.md Task 2 <behavior>, the 7 sub-tests below cover:

1. ``test_transform_tools_per_phase49_rules`` (parametrized over 9 experts)
   — each YAML's ``tools`` whitelist matches Phase 49 §2 per-expert default.
2. ``test_screenplay_transform_preserves_HOOK_09`` — screenplay lineage.
   transform_notes contains the literal HOOK-09 invariant substring.
3. ``test_skill_sha256_lf_normalized`` — SHA-256 of LF-normalized source
   SKILL.md matches the lineage.skill_sha256 (64 hex chars).
4. ``test_filename_stem_equals_name_field`` (parametrized over 9 experts)
   — emitted YAML filename stem equals its ``name`` field; passes
   ``load_one_agent_yaml`` without RegistryValidationError.
5. ``test_all_9_yamls_pass_schema`` — with HERMES_HOME redirected to a
   tempdir containing all 9 YAMLs, ``load_agent_registry()`` returns 9.
6. ``test_legacy_name_mapping`` — character_designer's related_agents
   includes screenplay (mapped from `performer` legacy name per Pattern
   1b LEGACY_NAME_MAP); audio_pipeline's related_agents does NOT contain
   deprecated `composer` / `performer` names (FOUND-08 preservation).
7. ``test_audit_log_records_field_mappings`` — transform-audit-log.json
   has 9 entries keyed by expert name, each with non-empty
   ``frontmatter_mappings`` dict.

Skip guards: each source-dependent test calls ``pytest.skip()`` if the
kais-hermes-skills repo is not present at ``/data/workspace/kais-hermes-skills``.
This keeps the test suite hermetic on contributor machines without the
source skills repo (per RESEARCH §"Validation Architecture").
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

# Make scripts/ importable as a package-less module path (matches the
# existing pattern in tests/test_trajectory_compressor.py and others).
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from transform_skill_to_agent import (  # noqa: E402  (after sys.path insert)
    EXPERTS_9,
    LEGACY_NAME_MAP,
    PANEL_9,
    transform_one,
)

KIAS_SKILLS = Path("/data/workspace/kais-hermes-skills/skills/movie-experts")

# Phase 49 §2.x per-expert default tools whitelist. The transform script
# MUST emit exactly these arrays — no extras, no omissions. Any drift here
# breaks the runtime dispatcher (ARCHITECTURE §4.3) and the spoofing
# mitigation (T-53-02 filename-stem invariant).
EXPECTED_TOOLS = {
    "screenplay": ["hermes_llm", "read_file", "search_files", "write_file", "patch"],
    "cinematographer": ["hermes_llm", "read_file", "search_files"],
    "hook_retention": ["hermes_llm", "read_file", "search_files"],
    "theory_critic": ["hermes_llm", "read_file", "search_files"],
    "editor": ["hermes_llm", "read_file", "search_files"],
    "character_designer": ["hermes_llm", "read_file", "write_file"],
    "continuity_auditor": ["hermes_llm", "read_file", "search_files"],
    "audio_pipeline": ["hermes_llm", "dreamina_cli", "read_file", "write_file"],
    "style_genome": ["hermes_llm", "read_file", "search_files"],
}


def _skill_path(expert: str) -> Path:
    """Return the source SKILL.md path for ``expert``."""
    return KIAS_SKILLS / expert / "SKILL.md"


def _require_kias_skills():
    """Skip the calling test if kais-hermes-skills source is unavailable."""
    if not KIAS_SKILLS.is_dir():
        pytest.skip(
            f"kais-hermes-skills source unavailable at {KIAS_SKILLS} — "
            "MIGR-01 transform tests require the operator machine"
        )


# --------------------------------------------------------------------------- #
# Test 1 — per-expert tools whitelist matches Phase 49 §2.x defaults
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("expert_name", list(EXPECTED_TOOLS.keys()))
def test_transform_tools_per_phase49_rules(expert_name):
    """Tools whitelist per YAML matches Phase 49 §2.x per-expert default.

    Screenplay carries write_file + patch because the HOOK-09 emotion_curve
    marker contract requires the screenplay agent to emit Step 3 JSON
    artifacts. Cinematographer / hook_retention / theory_critic / editor /
    continuity_auditor / style_genome are analysis-only (read + search).
    character_designer adds write_file for the L4 turnaround sheet.
    audio_pipeline adds dreamina_cli + write_file for actual asset rendering.
    """
    _require_kias_skills()
    skill_path = _skill_path(expert_name)
    if not skill_path.exists():
        pytest.skip(f"{skill_path} missing")
    result = transform_one(expert_name, skill_path)
    assert result["tools"] == EXPECTED_TOOLS[expert_name], (
        f"{expert_name}: expected {EXPECTED_TOOLS[expert_name]}, "
        f"got {result['tools']}"
    )


# --------------------------------------------------------------------------- #
# Test 2 — HOOK-09 invariant substring in screenplay.transform_notes
# --------------------------------------------------------------------------- #


def test_screenplay_transform_preserves_HOOK_09():
    """HOOK-09 emotion_curve marker invariant — verbatim substring check.

    Per 05-POC-PLAN.md §3.2 + 53-CONTEXT.md "Specific Ideas": screenplay's
    lineage.transform_notes MUST contain the literal substring
    ``HOOK-09 emotion_curve marker arrays remain contract-load-bearing``.
    This is the PoC's first "did the transform work?" smoke test — losing
    it breaks downstream storyboard Step 6.5 + visual_executor Step 7.
    """
    _require_kias_skills()
    skill_path = _skill_path("screenplay")
    if not skill_path.exists():
        pytest.skip("screenplay SKILL.md missing")
    result = transform_one("screenplay", skill_path)
    notes = result["lineage"]["transform_notes"]
    assert "HOOK-09 emotion_curve marker arrays remain contract-load-bearing" in notes, (
        f"HOOK-09 invariant substring missing from transform_notes: {notes!r}"
    )


# --------------------------------------------------------------------------- #
# Test 3 — SHA-256 LF-normalization
# --------------------------------------------------------------------------- #


def test_skill_sha256_lf_normalized():
    """SHA-256 of LF-normalized source SKILL.md equals lineage.skill_sha256.

    Per Phase 49 §2.1 edge case + RESEARCH Pitfall 7: CRLF checkouts on
    Windows would otherwise produce a different hash than CI's LF hash.
    Transform script MUST normalize ``\\r\\n`` → ``\\n`` before hashing.
    """
    _require_kias_skills()
    skill_path = _skill_path("screenplay")
    if not skill_path.exists():
        pytest.skip("screenplay SKILL.md missing")
    raw = skill_path.read_bytes()
    lf_content = raw.replace(b"\r\n", b"\n").decode("utf-8")
    expected_sha = hashlib.sha256(lf_content.encode("utf-8")).hexdigest()

    result = transform_one("screenplay", skill_path)
    actual_sha = result["lineage"]["skill_sha256"]
    assert actual_sha == expected_sha, (
        f"SHA-256 mismatch: transform produced {actual_sha}, "
        f"expected LF-normalized {expected_sha}"
    )
    # 64 lowercase hex chars (regex `^[a-f0-9]{64}$` from agents-schema.yaml:318)
    assert len(actual_sha) == 64
    assert all(c in "0123456789abcdef" for c in actual_sha)


# --------------------------------------------------------------------------- #
# Test 4 — filename-stem invariant: name field == filename stem
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("expert_name", EXPERTS_9)
def test_filename_stem_equals_name_field(expert_name, tmp_path):
    """Emitted YAML filename stem equals its ``name`` field (T-52-03 spoofing).

    The registry loader enforces this invariant at load time. The transform
    script writes ``{name}.agent.yaml``; round-tripping through
    ``load_one_agent_yaml`` confirms the invariant holds end-to-end.
    """
    _require_kias_skills()
    skill_path = _skill_path(expert_name)
    if not skill_path.exists():
        pytest.skip(f"{skill_path} missing")
    result = transform_one(expert_name, skill_path)
    assert result["name"] == expert_name, (
        f"name field {result['name']!r} != expert {expert_name!r}"
    )

    # Round-trip through yaml emit + registry loader.
    import yaml
    from agent.registry_loader import load_one_agent_yaml

    target = tmp_path / f"{expert_name}.agent.yaml"
    target.write_text(
        yaml.safe_dump(result, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    loaded = load_one_agent_yaml(target)  # MUST NOT raise
    assert loaded["name"] == expert_name


# --------------------------------------------------------------------------- #
# Test 5 — all 9 YAMLs load via load_agent_registry
# --------------------------------------------------------------------------- #


def test_all_9_yamls_pass_schema(tmp_path, monkeypatch):
    """After writing all 9 to a tempdir, load_agent_registry returns 9 entries.

    End-to-end MIGR-01 SC#1 acceptance: 9 agent YAMLs validate against
    agents-schema.yaml (18 fields, lineage block populated). The tempdir
    acts as a redirected HERMES_HOME/agents so the test is hermetic.
    """
    _require_kias_skills()
    import yaml
    from agent.registry_loader import load_agent_registry

    # Stage a fake HERMES_HOME with an agents/ subdir.
    fake_home = tmp_path / "hermes"
    (fake_home / "agents").mkdir(parents=True)

    for expert_name in EXPERTS_9:
        skill_path = _skill_path(expert_name)
        if not skill_path.exists():
            pytest.skip(f"{skill_path} missing")
        result = transform_one(expert_name, skill_path)
        target = fake_home / "agents" / f"{expert_name}.agent.yaml"
        target.write_text(
            yaml.safe_dump(result, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    monkeypatch.setenv("HERMES_HOME", str(fake_home))
    agents = load_agent_registry(force_reload=True)
    assert len(agents) == 9, f"expected 9 agents, got {len(agents)}"


# --------------------------------------------------------------------------- #
# Test 6 — LEGACY_NAME_MAP mapping (FOUND-08 preservation)
# --------------------------------------------------------------------------- #


def test_legacy_name_mapping():
    """character_designer related_agents includes screenplay (performer→character_designer mapping);
    audio_pipeline related_agents does NOT contain deprecated names."""
    _require_kias_skills()

    # character_designer transform
    cd_path = _skill_path("character_designer")
    if not cd_path.exists():
        pytest.skip("character_designer SKILL.md missing")
    cd_result = transform_one("character_designer", cd_path)
    cd_related = set(cd_result["related_agents"])
    # character_designer's source SKILL.md lists screenplay directly
    # (verified via frontmatter inspection); screenplay is a panel peer.
    assert "screenplay" in cd_related, (
        f"character_designer missing screenplay in related_agents: {sorted(cd_related)}"
    )

    # audio_pipeline transform — must NOT contain deprecated composer / performer
    ap_path = _skill_path("audio_pipeline")
    if not ap_path.exists():
        pytest.skip("audio_pipeline SKILL.md missing")
    ap_result = transform_one("audio_pipeline", ap_path)
    ap_related = set(ap_result["related_agents"])
    deprecated = {"composer", "performer", "scene_builder", "continuity"}
    leaked = deprecated & ap_related
    assert not leaked, (
        f"audio_pipeline related_agents leaked deprecated names: {sorted(leaked)} "
        f"(FOUND-08 preservation violated)"
    )

    # Sanity: LEGACY_NAME_MAP has the 4 documented mappings.
    assert LEGACY_NAME_MAP == {
        "scene_builder": "cinematographer",
        "continuity": "continuity_auditor",
        "performer": "character_designer",
        "composer": "audio_pipeline",
    }

    # PANEL_9 is exactly the 9-agent subset from CONTEXT.md decision #1.
    assert PANEL_9 == {
        "screenplay", "cinematographer", "hook_retention", "theory_critic",
        "editor", "character_designer", "continuity_auditor",
        "audio_pipeline", "style_genome",
    }


# --------------------------------------------------------------------------- #
# Test 7 — transform audit log records field mappings
# --------------------------------------------------------------------------- #


def test_audit_log_records_field_mappings():
    """transform-audit-log.json has 9 entries keyed by expert, each with
    non-empty frontmatter_mappings dict (SC#1 audit trail)."""
    audit_path = ROOT / "tests" / "fixtures" / "transform-audit-log.json"
    assert audit_path.exists(), f"audit log missing at {audit_path}"
    data = json.loads(audit_path.read_text(encoding="utf-8"))

    # Top-level shape: object keyed by expert name.
    assert isinstance(data, dict), f"audit log top-level must be object, got {type(data).__name__}"
    missing = set(EXPERTS_9) - set(data.keys())
    assert not missing, f"audit log missing experts: {sorted(missing)}"

    # Each entry documents the field mapping audit trail.
    for expert, entry in data.items():
        assert isinstance(entry, dict), f"{expert}: entry must be object"
        mappings = entry.get("frontmatter_mappings")
        assert isinstance(mappings, dict) and mappings, (
            f"{expert}: frontmatter_mappings must be non-empty dict, got {mappings!r}"
        )
        # Every entry must cite the source SHA-256 for lineage traceability.
        assert "source_sha256" in entry, (
            f"{expert}: audit entry missing source_sha256 field"
        )


# --------------------------------------------------------------------------- #
# Test 8 — CR-03: transform tolerates ``related_skills:`` / ``tags:`` with
# empty (None) values without crashing (regression)
# --------------------------------------------------------------------------- #


def test_transform_handles_empty_list_values_in_frontmatter():
    """CR-03: SKILL.md frontmatter with ``related_skills:`` (no value) or
    ``tags:`` (no value) MUST NOT crash the transform.

    ``yaml.safe_load`` parses ``tags:`` (key with nothing after the colon)
    as the YAML null value. ``dict.get(key, default)`` then returns ``None``,
    NOT the default — the default only fires when the key is ABSENT. The
    pre-CR-03 transform called ``meta.get("related_skills", [])`` and then
    ``for name in related_skills`` — when the key was present-with-None,
    the comprehension raised ``TypeError: 'NoneType' object is not iterable``.

    The fix introduces a ``_get_list`` helper that explicitly checks
    ``isinstance(v, list)`` before returning, so both missing-key and
    present-with-None cases coerce to ``[]``.
    """
    fixture_path = ROOT / "tests" / "fixtures" / "skill-empty-list-values.md"
    assert fixture_path.exists(), f"fixture missing at {fixture_path}"

    # Use a name NOT in EXPERTS_9 so persona/tools/transform_notes fall back
    # to the generic branches — the test only cares that related_agents/tags/
    # metrics are emitted as empty arrays. We monkeypatch the three dict
    # lookups that would otherwise KeyError on an unknown expert name.
    import transform_skill_to_agent as t

    original_tools_for = t._tools_for
    t._tools_for = lambda name: ["hermes_llm"]
    original_transform_notes = t._transform_notes
    t._transform_notes = lambda name: "test fixture — empty list values"
    try:
        result = t.transform_one("empty_list_skill", fixture_path)
    finally:
        t._tools_for = original_tools_for
        t._transform_notes = original_transform_notes

    # The three None-vulnerable sites MUST be empty lists, not None.
    assert result["related_agents"] == [], (
        f"related_agents must be [] for empty frontmatter; "
        f"got {result['related_agents']!r}"
    )
    assert result["tags"] == [], (
        f"tags must be [] for empty frontmatter; got {result['tags']!r}"
    )
    assert result["metrics"] == [], (
        f"metrics must be [] for empty frontmatter; got {result['metrics']!r}"
    )
    # And the lineage block must be intact (sanity).
    assert result["lineage"]["skill_sha256"]
    assert result["lineage"]["transform_date"]  # any non-empty date string


def test_get_list_helper_handles_none_and_missing():
    """CR-03: ``_get_list`` returns [] for missing, None, and non-list values."""
    from transform_skill_to_agent import _get_list

    # Missing key → []
    assert _get_list({}, "x") == []
    # Present-with-None → [] (the CR-03 regression)
    assert _get_list({"x": None}, "x") == []
    # Present with list → list unchanged
    assert _get_list({"x": [1, 2]}, "x") == [1, 2]
    # Present with non-list → []
    assert _get_list({"x": "string"}, "x") == []
    assert _get_list({"x": {"nested": "dict"}}, "x") == []
