"""test_skill_discovery.py — verifies SC#4: skill discovered by hermes-agent loader.

Per CRITICAL-FINDING-35-01, skills are discovered via path-based recursive scan
for ``SKILL.md`` files — NOT plugin registration. The scan searches:

1. ``SKILLS_DIR`` (``~/.hermes/skills/``)
2. External dirs from ``~/.hermes/config.yaml`` (``skills.external_dirs``)

Tests MUST NOT depend on ``~/.hermes/`` runtime state. They monkeypatch:

- ``tools.skills_tool.SKILLS_DIR`` → an empty tmp_path (neutralize local dir)
- ``agent.skill_utils.get_external_skills_dirs`` → ``[<real skills dir>]``

This lets the real discovery scan run against the real on-disk SKILL.md without
touching any config file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

# Real skill location — kais-movie-pipeline ships here (D-35-01).
SKILL_DIR = Path("/data/workspace/hermes-agent/skills/kais-movie-pipeline")
HERMES_SKILLS_ROOT = Path("/data/workspace/hermes-agent/skills")
SKILL_MD = SKILL_DIR / "SKILL.md"


# ---------------------------------------------------------------------------
# Test 1: SKILL.md frontmatter parses + has mandatory fields (SC#1)
# ---------------------------------------------------------------------------


class TestSkillMDFrontmatter:
    """SC#1 — SKILL.md is valid YAML frontmatter with all required fields."""

    def test_skill_md_exists(self):
        assert SKILL_MD.exists(), f"SKILL.md missing at {SKILL_MD}"

    def test_skill_md_frontmatter_valid(self):
        """Parse frontmatter via yaml.safe_load and verify mandatory fields."""
        content = SKILL_MD.read_text(encoding="utf-8")
        # Parse frontmatter (between leading --- and the next ---)
        assert content.startswith("---"), "SKILL.md must start with YAML frontmatter"
        _, fm_str, _body = content.split("---", 2)
        fm = yaml.safe_load(fm_str)

        # Mandatory scalar fields
        assert fm["name"] == "kais-movie-pipeline"
        assert isinstance(fm["description"], str)
        assert len(fm["description"]) <= 1024, "description must be ≤1024 chars"
        assert "version" in fm

        # metadata.hermes block
        hermes = fm["metadata"]["hermes"]
        assert "tags" in hermes and isinstance(hermes["tags"], list)
        assert "related_skills" in hermes
        assert "expert_id" in hermes
        assert hermes["expert_id"] == "kais-movie-pipeline"
        assert "metrics" in hermes and isinstance(hermes["metrics"], list)

    def test_related_skills_lists_15_movie_experts(self):
        """related_skills MUST list the 15 movie-experts (per SC#1)."""
        content = SKILL_MD.read_text(encoding="utf-8")
        _, fm_str, _ = content.split("---", 2)
        fm = yaml.safe_load(fm_str)
        related = fm["metadata"]["hermes"]["related_skills"]
        assert isinstance(related, list)
        assert len(related) == 15, (
            f"related_skills must list 15 experts, got {len(related)}: {related}"
        )
        # Spot-check a few canonical expert names
        expected_subset = {
            "hook_retention", "creative_source", "screenplay",
            "script_auditor", "colorist", "compliance_gate",
        }
        assert expected_subset.issubset(set(related)), (
            f"missing experts: {expected_subset - set(related)}"
        )


# ---------------------------------------------------------------------------
# Test 2: SKILL.md body has the required orchestration sections
# ---------------------------------------------------------------------------


class TestSkillMDBody:
    """Body must have the 8 orchestration-specific sections (per PATTERNS.md)."""

    REQUIRED_SECTIONS = [
        "## When to use",
        "## References",
        "## Pipeline DAG",
        "## Phase ↔ Expert Mapping",
        "## Review Gates",
        "## Runner",
        "## Operator Setup",
        "## What NOT to do",
    ]

    def test_skill_md_has_required_body_sections(self):
        body = SKILL_MD.read_text(encoding="utf-8")
        missing = [s for s in self.REQUIRED_SECTIONS if s not in body]
        assert not missing, f"SKILL.md body missing sections: {missing}"


# ---------------------------------------------------------------------------
# Test 3: skills_list() discovers the skill (SC#4 — discovery)
# ---------------------------------------------------------------------------


class TestSkillsListDiscovery:
    """SC#4 — skill appears in skills_list() when external_dirs includes the
    hermes-agent skills tree."""

    def test_skill_discoverable_in_external_dirs(
        self, tmp_path, monkeypatch,
    ):
        """Monkeypatch SKILLS_DIR to neutral tmp + external_dirs to the real
        hermes-agent skills tree; skills_list() must include
        'kais-movie-pipeline'."""
        # Import the discovery module
        import tools.skills_tool as skills_tool

        # Neutralize the local skills dir with an EXISTING EMPTY dir
        # (skills_list short-circuits with "no skills" if SKILLS_DIR doesn't
        # exist, so we create the dir but leave it empty).
        empty_local = tmp_path / "empty-skills"
        empty_local.mkdir()
        monkeypatch.setattr(skills_tool, "SKILLS_DIR", empty_local)

        # Point external dirs at the real skills tree
        import agent.skill_utils as skill_utils
        monkeypatch.setattr(
            skill_utils, "get_external_skills_dirs",
            lambda: [HERMES_SKILLS_ROOT],
        )

        # Run discovery
        result_json = skills_tool.skills_list()
        result = json.loads(result_json)

        assert result["success"] is True, f"skills_list failed: {result}"
        names = [s["name"] for s in result["skills"]]
        assert "kais-movie-pipeline" in names, (
            f"kais-movie-pipeline not discovered; found: {names[:20]}"
        )


# ---------------------------------------------------------------------------
# Test 4: skill_view() returns content (SC#4 — loadable)
# ---------------------------------------------------------------------------


class TestSkillViewContent:
    """SC#4 — skill_view('kais-movie-pipeline') returns the SKILL.md content."""

    def test_skill_view_returns_content(
        self, tmp_path, monkeypatch,
    ):
        import tools.skills_tool as skills_tool

        empty_local = tmp_path / "empty-skills"
        empty_local.mkdir()
        monkeypatch.setattr(skills_tool, "SKILLS_DIR", empty_local)
        import agent.skill_utils as skill_utils
        monkeypatch.setattr(
            skill_utils, "get_external_skills_dirs",
            lambda: [HERMES_SKILLS_ROOT],
        )

        result_json = skills_tool.skill_view("kais-movie-pipeline", preprocess=False)
        result = json.loads(result_json)

        assert result["success"] is True, (
            f"skill_view failed: {json.dumps(result, ensure_ascii=False)[:400]}"
        )
        assert result["name"] == "kais-movie-pipeline"
        assert len(result["content"]) > 1000, (
            "skill_view content should be substantial (>1000 chars); "
            f"got {len(result['content'])}"
        )
        # Spot-check content includes a canonical section
        assert "## Pipeline DAG" in result["content"]
