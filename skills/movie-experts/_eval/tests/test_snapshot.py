"""Pytest coverage for skill snapshot baseline capture + verification.

RED phase of TDD: these tests import the not-yet-implemented `snapshot`
module and therefore fail at collection time until Task 2 lands the
implementation.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pytest

# Module under test — must be importable as a top-level path.
_EVAL_DIR = Path(__file__).resolve().parent.parent
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

from snapshot import (  # noqa: E402  -- intentional late import for sys.path shim
    EXPERT_DIRS,
    capture_baselines,
    compute_provenance,
    verify_baselines,
)


_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$|^uncommitted$")


def _build_synthetic_skills_tree(tmp_root: Path) -> tuple[Path, dict[str, str]]:
    """Create a tmp skills/ tree with all 14 expert dirs each holding a SKILL.md.

    Returns the skills_dir and a dict {expert_id: content}.
    """
    skills_dir = tmp_root / "skills" / "movie-experts"
    contents: dict[str, str] = {}
    for expert_id in EXPERT_DIRS:
        expert_dir = skills_dir / expert_id
        expert_dir.mkdir(parents=True, exist_ok=True)
        body = (
            "---\n"
            f"name: {expert_id}\n"
            f"metadata:\n"
            f"  hermes:\n"
            f"    expert_id: {expert_id}\n"
            "---\n"
            f"# {expert_id} body {expert_id}\n"
        )
        (expert_dir / "SKILL.md").write_text(body, encoding="utf-8")
        contents[expert_id] = body
    return skills_dir, contents


class TestComputeProvenance:
    def test_returns_required_fields(self, tmp_path: Path) -> None:
        skill_path = tmp_path / "animator" / "SKILL.md"
        skill_path.parent.mkdir(parents=True)
        skill_path.write_text("# animator\nbody\n", encoding="utf-8")

        provenance = compute_provenance(
            skill_path, expert_id="animator", git_sha="abc123def456"
        )

        required_keys = {
            "expert_id",
            "tag",
            "source_path",
            "sha256",
            "git_sha",
            "captured_at",
            "byte_size",
        }
        assert required_keys.issubset(provenance.keys()), (
            f"missing keys: {required_keys - set(provenance.keys())}"
        )
        assert provenance["expert_id"] == "animator"
        assert provenance["tag"] == "eval-baseline-v1"
        assert provenance["git_sha"] == "abc123def456"
        assert _SHA256_HEX_RE.match(provenance["sha256"]), (
            f"sha256 not 64 lowercase hex: {provenance['sha256']}"
        )
        # captured_at parses as ISO 8601.
        datetime.fromisoformat(provenance["captured_at"])
        assert provenance["source_path"].endswith("SKILL.md")
        assert isinstance(provenance["byte_size"], int)
        assert provenance["byte_size"] > 0

    def test_hash_is_deterministic_across_calls(self, tmp_path: Path) -> None:
        skill_path = tmp_path / "screenplay" / "SKILL.md"
        skill_path.parent.mkdir(parents=True)
        body = "# screenplay\nSAME CONTENT\n"
        skill_path.write_text(body, encoding="utf-8")

        p1 = compute_provenance(skill_path, expert_id="screenplay", git_sha="x")
        p2 = compute_provenance(skill_path, expert_id="screenplay", git_sha="x")
        assert p1["sha256"] == p2["sha256"]

    def test_hash_changes_when_content_mutates(self, tmp_path: Path) -> None:
        skill_path = tmp_path / "drawer" / "SKILL.md"
        skill_path.parent.mkdir(parents=True)
        skill_path.write_text("original content\n", encoding="utf-8")
        before = compute_provenance(skill_path, expert_id="drawer", git_sha="x")

        skill_path.write_text("mutated content\n", encoding="utf-8")
        after = compute_provenance(skill_path, expert_id="drawer", git_sha="x")

        assert before["sha256"] != after["sha256"]


class TestCaptureBaselines:
    def test_creates_14_dirs_with_skill_md_and_provenance(
        self, tmp_path: Path
    ) -> None:
        skills_dir, _ = _build_synthetic_skills_tree(tmp_path)
        baseline_dir = tmp_path / "baseline"

        # 40-char hex git sha matches real format.
        created = capture_baselines(
            skills_dir, baseline_dir, git_sha="deadbeef" * 5
        )

        assert len(created) == 14
        assert len(EXPERT_DIRS) == 14
        for expert_id in EXPERT_DIRS:
            sub = baseline_dir / expert_id
            assert sub.is_dir(), f"missing baseline dir: {expert_id}"
            assert (sub / "SKILL.md").is_file()
            prov_path = sub / "PROVENANCE.json"
            assert prov_path.is_file()
            prov = json.loads(prov_path.read_text(encoding="utf-8"))
            assert prov["expert_id"] == expert_id
            assert prov["tag"] == "eval-baseline-v1"
            assert _GIT_SHA_RE.match(prov["git_sha"])
            assert _SHA256_HEX_RE.match(prov["sha256"])

    def test_baseline_skill_md_is_byte_exact(self, tmp_path: Path) -> None:
        skills_dir, contents = _build_synthetic_skills_tree(tmp_path)
        baseline_dir = tmp_path / "baseline"

        capture_baselines(
            skills_dir, baseline_dir, git_sha="0123456789abcdef" * 4
        )

        for expert_id, expected_body in contents.items():
            captured_bytes = (
                baseline_dir / expert_id / "SKILL.md"
            ).read_bytes()
            assert captured_bytes == expected_body.encode("utf-8"), (
                f"byte drift in {expert_id}"
            )

    def test_capture_fails_on_untracked_expert_dir(self, tmp_path: Path) -> None:
        """CR-02: a live expert dir NOT in EXPERT_DIRS raises RuntimeError.

        Without this guard, a contributor who adds
        ``skills/movie-experts/<new>/SKILL.md`` without extending
        EXPERT_DIRS would silently have their baseline skipped, then
        verify_baselines would silently pass — masking the drift in
        Phase 3/5/6 ablation comparisons.
        """
        skills_dir, _ = _build_synthetic_skills_tree(tmp_path)
        baseline_dir = tmp_path / "baseline"

        # Add an untracked expert dir (not in EXPERT_DIRS).
        extra = skills_dir / "cinematographer"
        extra.mkdir(parents=True, exist_ok=True)
        (extra / "SKILL.md").write_text(
            "---\nname: cinematographer\n---\n# Cinematographer\n",
            encoding="utf-8",
        )

        with pytest.raises(RuntimeError, match="Untracked expert"):
            capture_baselines(skills_dir, baseline_dir, git_sha="x")

    def test_capture_ignores_underscore_prefixed_dirs(self, tmp_path: Path) -> None:
        """CR-02: dirs prefixed with '_' (e.g. ``_eval``, ``_shared``) are
        NOT treated as untracked experts — they are infrastructure.
        """
        skills_dir, _ = _build_synthetic_skills_tree(tmp_path)
        baseline_dir = tmp_path / "baseline"

        # _eval already exists in the synthetic tree, but add _shared too.
        (skills_dir / "_shared").mkdir(parents=True, exist_ok=True)
        (skills_dir / "_shared" / "SKILL.md").write_text(
            "# shared infra — not an expert\n", encoding="utf-8"
        )

        # Must NOT raise — underscore-prefixed dirs are not experts.
        created = capture_baselines(skills_dir, baseline_dir, git_sha="x")
        assert len(created) == 14


class TestVerifyBaselines:
    def test_returns_clean_when_unchanged(self, tmp_path: Path) -> None:
        skills_dir, _ = _build_synthetic_skills_tree(tmp_path)
        baseline_dir = tmp_path / "baseline"
        capture_baselines(skills_dir, baseline_dir, git_sha="x")

        ok, drifts = verify_baselines(skills_dir, baseline_dir)

        assert ok is True
        assert drifts == []

    def test_detects_drift_after_mutation(self, tmp_path: Path) -> None:
        skills_dir, _ = _build_synthetic_skills_tree(tmp_path)
        baseline_dir = tmp_path / "baseline"
        capture_baselines(skills_dir, baseline_dir, git_sha="x")

        # Mutate one source file.
        target = skills_dir / "colorist" / "SKILL.md"
        target.write_text("# mutated\n", encoding="utf-8")

        ok, drifts = verify_baselines(skills_dir, baseline_dir)

        assert ok is False
        assert len(drifts) >= 1
        drift = next(d for d in drifts if d["expert_id"] == "colorist")
        assert drift["expected"] != drift["actual"]
        assert _SHA256_HEX_RE.match(drift["expected"])
        assert _SHA256_HEX_RE.match(drift["actual"])
        assert "source_path" in drift

    def test_verify_flags_missing_provenance_keys(self, tmp_path: Path) -> None:
        """WR-08: a PROVENANCE.json missing required keys is flagged as drift.

        Without this guard, a tampered baseline (e.g. an attacker
        replaced PROVENANCE.json with ``{"sha256": "<current source hash>"}``
        to mask drift) would pass verification silently.
        """
        skills_dir, _ = _build_synthetic_skills_tree(tmp_path)
        baseline_dir = tmp_path / "baseline"
        capture_baselines(skills_dir, baseline_dir, git_sha="x")

        # Tamper: drop the captured_at key from one expert's provenance.
        prov_path = baseline_dir / "editor" / "PROVENANCE.json"
        prov = json.loads(prov_path.read_text(encoding="utf-8"))
        del prov["captured_at"]
        prov_path.write_text(
            json.dumps(prov, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        ok, drifts = verify_baselines(skills_dir, baseline_dir)
        assert ok is False
        drift = next(d for d in drifts if d["expert_id"] == "editor")
        assert "missing keys" in drift["expected"]
        assert "captured_at" in drift["expected"]

    def test_verify_flags_wrong_tag(self, tmp_path: Path) -> None:
        """WR-08: a PROVENANCE.json with a stale tag is flagged as drift.

        A baseline captured under ``eval-baseline-v0`` must not silently
        pass verification when the current cycle expects
        ``eval-baseline-v1`` — otherwise drift across cycles would be
        masked.
        """
        skills_dir, _ = _build_synthetic_skills_tree(tmp_path)
        baseline_dir = tmp_path / "baseline"
        capture_baselines(skills_dir, baseline_dir, git_sha="x")

        # Tamper: change tag on one expert.
        prov_path = baseline_dir / "foley" / "PROVENANCE.json"
        prov = json.loads(prov_path.read_text(encoding="utf-8"))
        prov["tag"] = "eval-baseline-v0"
        prov_path.write_text(
            json.dumps(prov, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        ok, drifts = verify_baselines(skills_dir, baseline_dir)
        assert ok is False
        drift = next(d for d in drifts if d["expert_id"] == "foley")
        assert "wrong tag" in drift["expected"]
        assert "eval-baseline-v0" in drift["expected"]


if __name__ == "__main__":
    pytest.main([__file__, "-x", "--tb=short"])
