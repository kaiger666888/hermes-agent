"""XCUT-05-AUTO — bump_all_agent_lineage.py correctness tests.

Covers the 8 sub-tests per 82-03-PLAN.md Task 1 <behavior>:

1. ``test_active_experts_15_count`` — ACTIVE_EXPERTS_15 has 15 names.
2. ``test_track_a_equals_experts_9`` — TRACK_A_EXPERTS == EXPERTS_9.
3. ``test_track_b_count`` — TRACK_B_EXPERTS has 6 names.
4. ``test_no_overlap_track_a_b`` — Track A + Track B are disjoint.
5. ``test_all_15_have_skill_md`` — all 15 SKILL.md sources exist.
6. ``test_transform_track_b_one_structure`` — 18-field shape for one
   Track B expert.
7. ``test_transform_track_b_tools`` — per-expert tools match
   TRACK_B_TOOLS.
8. ``test_transform_track_b_lineage`` — lineage block populated.
9. ``test_validate_all_success`` — end-to-end bump + validate in tmpdir.
10. ``test_main_returns_0_on_full_success`` — main() exit code.

Skip guards: each source-dependent test calls ``pytest.skip()`` if the
kais-hermes-skills repo is not present. This keeps the test suite
hermetic on contributor machines without the source skills repo.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make scripts/ importable as a package-less module path (matches the
# pattern in tests/agent/test_transform_skill_to_agent.py).
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from transform_skill_to_agent import EXPERTS_9  # noqa: E402

from bump_all_agent_lineage import (  # noqa: E402
    ACTIVE_EXPERTS_15,
    TRACK_A_EXPERTS,
    TRACK_B_EXPERTS,
    TRACK_B_PANEL,
    TRACK_B_TOOLS,
    TRACK_B_TRANSFORM_NOTES,
    transform_track_b_one,
)

KIAS_SKILLS = Path("/data/workspace/kais-hermes-skills/skills/movie-experts")

#: The 18 fields every agent YAML must have (agents-schema.yaml).
_REQUIRED_FIELDS = {
    "name",
    "description",
    "version",
    "persona",
    "tools",
    "memory_scope",
    "lineage",
    "refs",
    "tags",
    "expert_id",
    "metrics",
    "prerequisites",
    "related_agents",
    "evolution_log",
    "fitness_score",
    "platforms",
    "round_table_eligible",
    "default_invocation",
}


def _skill_path(expert: str) -> Path:
    """Return the source SKILL.md path for ``expert``."""
    return KIAS_SKILLS / expert / "SKILL.md"


def _require_kias_skills():
    """Skip the calling test if kais-hermes-skills source is unavailable."""
    if not KIAS_SKILLS.is_dir():
        pytest.skip(
            f"kais-hermes-skills source unavailable at {KIAS_SKILLS} — "
            "XCUT-05-AUTO bump tests require the operator machine"
        )


# --------------------------------------------------------------------------- #
# Test 1 — ACTIVE_EXPERTS_15 count
# --------------------------------------------------------------------------- #


def test_active_experts_15_count():
    """ACTIVE_EXPERTS_15 contains exactly 15 expert names (9 Track A + 6 Track B)."""
    assert len(ACTIVE_EXPERTS_15) == 15, (
        f"expected 15 active experts, got {len(ACTIVE_EXPERTS_15)}: "
        f"{ACTIVE_EXPERTS_15}"
    )


# --------------------------------------------------------------------------- #
# Test 2 — TRACK_A_EXPERTS == EXPERTS_9
# --------------------------------------------------------------------------- #


def test_track_a_equals_experts_9():
    """TRACK_A_EXPERTS equals EXPERTS_9 from transform_skill_to_agent."""
    assert TRACK_A_EXPERTS == list(EXPERTS_9), (
        f"TRACK_A_EXPERTS {TRACK_A_EXPERTS} != EXPERTS_9 {list(EXPERTS_9)}"
    )


# --------------------------------------------------------------------------- #
# Test 3 — TRACK_B_EXPERTS count
# --------------------------------------------------------------------------- #


def test_track_b_count():
    """TRACK_B_EXPERTS contains exactly 6 expert names."""
    assert len(TRACK_B_EXPERTS) == 6, (
        f"expected 6 Track B experts, got {len(TRACK_B_EXPERTS)}: "
        f"{TRACK_B_EXPERTS}"
    )


# --------------------------------------------------------------------------- #
# Test 4 — no overlap between Track A + Track B
# --------------------------------------------------------------------------- #


def test_no_overlap_track_a_b():
    """Track A and Track B are disjoint sets."""
    overlap = set(TRACK_A_EXPERTS) & set(TRACK_B_EXPERTS)
    assert not overlap, (
        f"Track A / Track B overlap: {sorted(overlap)} — "
        "an expert appears in both tracks"
    )
    # The union of the two tracks equals ACTIVE_EXPERTS_15.
    assert set(ACTIVE_EXPERTS_15) == set(TRACK_A_EXPERTS) | set(
        TRACK_B_EXPERTS
    ), "ACTIVE_EXPERTS_15 != Track A ∪ Track B"


# --------------------------------------------------------------------------- #
# Test 5 — all 15 source SKILL.md files exist
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("expert_name", ACTIVE_EXPERTS_15)
def test_all_15_have_skill_md(expert_name):
    """Each of the 15 active experts has a SKILL.md at the kais-hermes-skills source."""
    _require_kias_skills()
    skill_path = _skill_path(expert_name)
    assert skill_path.exists(), (
        f"{expert_name}: SKILL.md missing at {skill_path}"
    )


# --------------------------------------------------------------------------- #
# Test 6 — transform_track_b_one 18-field structure
# --------------------------------------------------------------------------- #


def test_transform_track_b_one_structure():
    """transform_track_b_one produces a dict with all 18 required fields."""
    _require_kias_skills()
    skill_path = _skill_path("colorist")
    if not skill_path.exists():
        pytest.skip("colorist SKILL.md missing")
    result = transform_track_b_one("colorist", skill_path)
    missing = _REQUIRED_FIELDS - set(result.keys())
    assert not missing, f"colorist: missing fields {sorted(missing)}"
    # Spot-check a few field types.
    assert isinstance(result["tools"], list)
    assert isinstance(result["lineage"], dict)
    assert isinstance(result["related_agents"], list)
    assert isinstance(result["tags"], list)


# --------------------------------------------------------------------------- #
# Test 7 — transform_track_b_one tools match TRACK_B_TOOLS
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("expert_name", TRACK_B_EXPERTS)
def test_transform_track_b_tools(expert_name):
    """Each Track B expert's transform produces the correct tools whitelist."""
    _require_kias_skills()
    skill_path = _skill_path(expert_name)
    if not skill_path.exists():
        pytest.skip(f"{expert_name} SKILL.md missing")
    result = transform_track_b_one(expert_name, skill_path)
    assert result["tools"] == TRACK_B_TOOLS[expert_name], (
        f"{expert_name}: expected tools {TRACK_B_TOOLS[expert_name]}, "
        f"got {result['tools']}"
    )


# --------------------------------------------------------------------------- #
# Test 8 — lineage block populated (SHA-256, transform_notes, date)
# --------------------------------------------------------------------------- #


def test_transform_track_b_lineage():
    """transform_track_b_one populates the lineage block correctly."""
    _require_kias_skills()
    skill_path = _skill_path("visual_executor")
    if not skill_path.exists():
        pytest.skip("visual_executor SKILL.md missing")
    result = transform_track_b_one("visual_executor", skill_path)
    lineage = result["lineage"]
    # Required lineage sub-fields.
    assert "derived_from_skill_id" in lineage
    assert "derived_from_repo" in lineage
    assert lineage["derived_from_repo"] == "kais-hermes-skills"
    assert "transform_date" in lineage
    assert "transform_notes" in lineage
    assert "skill_sha256" in lineage
    # SHA-256 is 64 lowercase hex chars.
    sha = lineage["skill_sha256"]
    assert len(sha) == 64, f"skill_sha256 wrong length: {len(sha)}"
    assert all(c in "0123456789abcdef" for c in sha), (
        f"skill_sha256 not hex: {sha}"
    )
    # transform_notes cites the v15.0 Phase 82 automation provenance.
    assert "v15.0 Phase 82" in lineage["transform_notes"], (
        f"transform_notes missing v15.0 Phase 82 provenance: "
        f"{lineage['transform_notes']!r}"
    )


# --------------------------------------------------------------------------- #
# Test 9 — TRACK_B_TRANSFORM_NOTES has entries for all 6 Track B experts
# --------------------------------------------------------------------------- #


def test_track_b_transform_notes_complete():
    """Every Track B expert has a non-empty entry in TRACK_B_TRANSFORM_NOTES."""
    for expert in TRACK_B_EXPERTS:
        assert expert in TRACK_B_TRANSFORM_NOTES, (
            f"{expert} missing from TRACK_B_TRANSFORM_NOTES"
        )
        assert TRACK_B_TRANSFORM_NOTES[expert], (
            f"{expert} has empty transform notes"
        )


# --------------------------------------------------------------------------- #
# Test 10 — TRACK_B_PANEL preserves non-expert agent peers
# --------------------------------------------------------------------------- #


def test_track_b_panel_includes_non_expert_peers():
    """TRACK_B_PANEL includes the 3 non-expert agent peers that appear in
    the existing v13.0 P62 Track B related_agents arrays. Stripping them
    would regress the collaboration graph."""
    for peer in ("compliance_gate", "production", "prompt_injector", "scene_builder"):
        assert peer in TRACK_B_PANEL, (
            f"{peer!r} missing from TRACK_B_PANEL — collaboration graph "
            "regression risk"
        )


# --------------------------------------------------------------------------- #
# Test 11 — end-to-end: bump all 15 + validate in a tmpdir HERMES_HOME
# --------------------------------------------------------------------------- #


def test_validate_all_success(tmp_path, monkeypatch):
    """bump_track_a + bump_track_b + validate_all produces 15 valid YAMLs.

    Redirects HERMES_HOME to a tmpdir so the test is hermetic. Requires
    the kais-hermes-skills source repo to be present.
    """
    _require_kias_skills()
    # Skip if any of the 15 SKILL.md files are missing.
    for expert in ACTIVE_EXPERTS_15:
        if not _skill_path(expert).exists():
            pytest.skip(f"{expert} SKILL.md missing — cannot run end-to-end")

    # Import bump functions + registry loader here (after the skip guard).
    from bump_all_agent_lineage import (
        bump_track_a,
        bump_track_b,
        validate_all,
    )

    # Redirect HERMES_HOME to the tmpdir.
    fake_home = tmp_path / "hermes"
    (fake_home / "agents").mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HERMES_HOME", str(fake_home))

    # Bump both tracks.
    results_a = bump_track_a()
    results_b = bump_track_b()
    results = {**results_a, **results_b}

    bumped_count = sum(1 for v in results.values() if v)
    assert bumped_count == 15, (
        f"expected 15 bumped, got {bumped_count}: {results}"
    )

    # Validate all 15.
    success, failure = validate_all(results)
    assert success == 15, (
        f"expected 15 validated, got {success} (failures: {failure})"
    )
    assert failure == 0


# --------------------------------------------------------------------------- #
# Test 12 — main() returns 0 on full success (end-to-end CLI exit code)
# --------------------------------------------------------------------------- #


def test_main_returns_0_on_full_success(tmp_path, monkeypatch):
    """main() exits 0 when all 15 agents bump + validate successfully."""
    _require_kias_skills()
    for expert in ACTIVE_EXPERTS_15:
        if not _skill_path(expert).exists():
            pytest.skip(f"{expert} SKILL.md missing — cannot run end-to-end")

    from bump_all_agent_lineage import main

    fake_home = tmp_path / "hermes"
    (fake_home / "agents").mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HERMES_HOME", str(fake_home))

    exit_code = main()
    assert exit_code == 0, (
        f"main() returned {exit_code} — expected 0 (full success)"
    )


# --------------------------------------------------------------------------- #
# Test 13 — all 15 generated YAMLs pass load_one_agent_yaml individually
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("expert_name", ACTIVE_EXPERTS_15)
def test_all_15_validate_individually(expert_name, tmp_path, monkeypatch):
    """Each of the 15 generated YAMLs passes load_one_agent_yaml when written
    to a tmpdir with the correct filename stem."""
    _require_kias_skills()
    skill_path = _skill_path(expert_name)
    if not skill_path.exists():
        pytest.skip(f"{expert_name} SKILL.md missing")

    import yaml
    from agent.registry_loader import load_one_agent_yaml

    if expert_name in TRACK_A_EXPERTS:
        from transform_skill_to_agent import transform_one
        data = transform_one(expert_name, skill_path)
    else:
        data = transform_track_b_one(expert_name, skill_path)

    target = tmp_path / f"{expert_name}.agent.yaml"
    target.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    # MUST NOT raise.
    loaded = load_one_agent_yaml(target)
    assert loaded["name"] == expert_name
