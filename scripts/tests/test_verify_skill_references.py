"""Tests for the phantom-reference detector in scripts/verify_skill_references.py.

RED phase: module + functions do not exist yet. These tests MUST fail at
import/collection time until Task 2 implements the scanner.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Make the scripts/ directory importable so `import verify_skill_references`
# resolves without packaging it as a module.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# Import target — currently MISSING. Every test below depends on this import
# succeeding, so the whole file fails to collect in the RED phase.
from verify_skill_references import (  # noqa: E402
    Finding,
    build_allowlist,
    format_report,
    scan_skill_file,
)


# ---------------------------------------------------------------------------
# Allowlist builder
# ---------------------------------------------------------------------------


class TestBuildAllowlist:
    """Verify allowlist derives from plugins/*/*/plugin.yaml + overrides YAML."""

    def _write_plugin_yaml(
        self, path: Path, name: str, description: str
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"name: {name}\n"
            f"version: 1.0.0\n"
            f'description: "{description}"\n'
            f"kind: backend\n",
            encoding="utf-8",
        )

    def _write_override_yaml(self, path: Path, models: list[str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["models:"]
        for m in models:
            lines.append(f"  - name: {m}")
            lines.append(f'    provenance: "test override for {m}"')
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_build_allowlist_from_plugins(self) -> None:
        """Plugin-derived names + description tokens are added to allowlist."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            plugins_root = tmp_root / "plugins"
            self._write_plugin_yaml(
                plugins_root / "video_gen" / "xplug" / "plugin.yaml",
                "xplug",
                "Xplug video gen backend (veo 3.1, kling v3)",
            )
            self._write_plugin_yaml(
                plugins_root / "image_gen" / "ypaint" / "plugin.yaml",
                "ypaint",
                "Ypaint image gen (flux-2-pro)",
            )
            override_yaml = tmp_root / "empty-overrides.yaml"
            self._write_override_yaml(override_yaml, [])

            allowlist = build_allowlist(plugins_root, override_yaml)

            # Plugin name field is always included (lowercased).
            assert "xplug" in allowlist, f"xplug missing: {sorted(allowlist)}"
            assert "ypaint" in allowlist, f"ypaint missing: {sorted(allowlist)}"

            # Description tokens: split on non-alphanumeric, lowercase, len>=3.
            # From "Xplug video gen backend (veo 3.1, kling v3)" we get: veo,
            # kling, etc. From "Ypaint image gen (flux-2-pro)" we get: flux,
            # pro, etc.
            assert "veo" in allowlist, f"veo missing: {sorted(allowlist)}"
            assert "kling" in allowlist, f"kling missing: {sorted(allowlist)}"

    def test_build_allowlist_merges_manual_overrides(self) -> None:
        """Override YAML `models:` entries are merged with plugin tokens."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            plugins_root = tmp_root / "plugins"
            # Empty plugins dir — no plugin.yaml files.
            override_yaml = tmp_root / "known-external-models.yaml"
            self._write_override_yaml(
                override_yaml, ["sora", "veo", "kling_v3", "runway_gen3"]
            )

            allowlist = build_allowlist(plugins_root, override_yaml)

            assert "sora" in allowlist
            assert "veo" in allowlist
            assert "kling_v3" in allowlist
            assert "runway_gen3" in allowlist

    def test_build_allowlist_handles_missing_override_yaml(self) -> None:
        """Missing override YAML is not fatal — returns plugin-derived set only.

        Even with no plugins and no overrides, the function still returns
        the always-safe stopwords (``model``, ``video``, ``turbo``) so the
        scanner never false-positives on those generic words. The contract
        is therefore "no plugin or override content escapes", not "empty
        set".
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            plugins_root = tmp_root / "plugins"
            missing_override = tmp_root / "does_not_exist.yaml"

            # Should not raise; should return a set.
            allowlist = build_allowlist(plugins_root, missing_override)

            assert isinstance(allowlist, set)
            # No plugin or override tokens leaked in — only always-safe stopwords.
            # (The scanner needs these to mask generic words like "model: ...".)
            assert "wan22_video" not in allowlist
            assert "sora" not in allowlist
            assert "kling" not in allowlist


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


class TestScanSkillFile:
    """Verify scanner flags known phantom references in real skill files."""

    def test_scan_flags_wan22_video_phantom(self) -> None:
        """Synthetic SKILL.md with `wan22_video` surfaces a finding.

        Originally asserted against the live animator/SKILL.md, but Phase 0
        plan 00-04 strips that phantom from production — so a synthetic
        fixture is the correct contract (detection capability, not current
        file state).
        """
        with tempfile.TemporaryDirectory() as tmp:
            phantom_skill = Path(tmp) / "SKILL.md"
            phantom_skill.write_text(
                "---\nname: animator\ndescription: test\n---\n\n"
                "# Animator Expert\n\n"
                "### Wan2.2 Generation\n\n"
                "- **model**: `wan22_video` (primary), `wan22_video_turbo` (preview)\n",
                encoding="utf-8",
            )
            findings = scan_skill_file(phantom_skill, allowlist=set())
            tokens = {f.matched_token for f in findings}
            assert "wan22_video" in tokens, (
                f"wan22_video not flagged; got tokens: {sorted(tokens)}"
            )
            wan = next(f for f in findings if f.matched_token == "wan22_video")
            assert wan.line >= 1
            assert wan.path.endswith("SKILL.md")

    def test_scan_flags_168k_tokens_phantom(self) -> None:
        """Synthetic SKILL.md with the 168K fabrication surfaces a finding.

        Originally asserted against the live performer/SKILL.md, but Phase 0
        plan 00-04 strips that fabrication from production — synthetic
        fixture is the correct contract.
        """
        with tempfile.TemporaryDirectory() as tmp:
            phantom_skill = Path(tmp) / "SKILL.md"
            phantom_skill.write_text(
                "---\nname: performer\n"
                'description: "Performer Expert: matrix with 168K controlled tokens."'
                "\n---\n\n"
                "# Performer Expert\n\n"
                "Performance matrix with 168K controlled tokens for action design.\n",
                encoding="utf-8",
            )
            findings = scan_skill_file(phantom_skill, allowlist=set())
            contexts = {f.matched_token.lower() for f in findings}
            joined = " ".join(f.context_line for f in findings).lower()
            assert "168k" in joined.lower() or "168k" in contexts, (
                f"168K fabrication not flagged; findings={findings[:3]}"
            )

    def test_scan_passes_clean_file(self) -> None:
        """A SKILL.md containing only allowlisted tokens yields zero findings."""
        with tempfile.TemporaryDirectory() as tmp:
            clean_skill = Path(tmp) / "SKILL.md"
            clean_skill.write_text(
                "---\nname: clean\ndescription: test\n---\n\n"
                "# Clean Expert\n\nUses sora and veo for shots.\n",
                encoding="utf-8",
            )
            allowlist = {"sora", "veo"}
            findings = scan_skill_file(clean_skill, allowlist=allowlist)
            assert findings == [], (
                f"Expected zero findings on clean file; got: {findings}"
            )

    def test_scan_returns_finding_datatype(self) -> None:
        """scan_skill_file returns Finding instances with the required fields."""
        with tempfile.TemporaryDirectory() as tmp:
            phantom_skill = Path(tmp) / "SKILL.md"
            phantom_skill.write_text(
                "---\nname: test\ndescription: test\n---\n\n"
                "# Test\n\nUses wan22_video for shots.\n",
                encoding="utf-8",
            )
            findings = scan_skill_file(phantom_skill, allowlist=set())
            assert len(findings) == 1
            f = findings[0]
            assert isinstance(f, Finding)
            assert f.matched_token == "wan22_video"
            assert f.line >= 1
            assert isinstance(f.context_line, str)
            assert "wan22_video" in f.context_line


# ---------------------------------------------------------------------------
# Reporter
# ---------------------------------------------------------------------------


class TestFormatReport:
    """Verify format_report produces dual JSON + Markdown output."""

    def test_report_json_and_markdown(self) -> None:
        """format_report returns (json_dict, markdown_str) with findings content."""
        findings = [
            Finding(
                path="skills/movie-experts/animator/SKILL.md",
                line=42,
                matched_token="wan22_video",
                context_line="- **model**: `wan22_video` (primary)",
            ),
            Finding(
                path="skills/movie-experts/performer/SKILL.md",
                line=20,
                matched_token="168K controlled tokens",
                context_line="Performance matrix with 168K controlled tokens.",
            ),
        ]
        json_dict, markdown = format_report(findings)

        # JSON shape
        assert isinstance(json_dict, dict)
        assert json_dict["total"] == 2
        assert len(json_dict["findings"]) == 2
        first = json_dict["findings"][0]
        assert first["token"] == "wan22_video"
        assert first["line"] == 42
        assert "animator" in first["file"]

        # JSON is serializable (no datetime, no Path objects).
        serialized = json.dumps(json_dict)
        assert "wan22_video" in serialized

        # Markdown shape
        assert isinstance(markdown, str)
        assert "wan22_video" in markdown
        assert "168K controlled tokens" in markdown
        assert "animator" in markdown
        assert "performer" in markdown
        assert "42" in markdown  # line number rendered

    def test_report_empty_findings(self) -> None:
        """Empty findings list produces total=0 / non-error output."""
        json_dict, markdown = format_report([])
        assert json_dict["total"] == 0
        assert json_dict["findings"] == []
        assert isinstance(markdown, str)


# Run as `python -m pytest scripts/tests/test_verify_skill_references.py`.
if __name__ == "__main__":
    pytest.main([__file__, "-x", "--tb=short"])
