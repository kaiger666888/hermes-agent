"""Tests for agent/evolution/apply.py — EVOL-05 atomic apply transaction.

Covers the 6-step atomic transaction (validate → apply → FOUND-08 →
additive → stage → commit) with revert-on-failure, plus the pure
verification functions (verify_additive_only, verify_found08_byte_intact),
revert_files, and build_commit_message.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agent.evolution.apply import (
    ApplyError,
    ApplyResult,
    build_commit_message,
    apply_patch_transaction,
    revert_files,
    verify_additive_only,
    verify_found08_byte_intact,
    _extract_frontmatter_block,
)
from tests.agent.evolution.conftest import (
    ADDITIVE_DIFF,
    SAMPLE_SKILL_MD,
    SKILL_REL_PATH,
    VIOLATING_DELETION_DIFF,
    VIOLATING_FRONTMATTER_DIFF,
)


# --------------------------------------------------------------------------- #
# TestVerifyAdditiveOnly
# --------------------------------------------------------------------------- #


class TestVerifyAdditiveOnly:
    def test_accepts_pure_addition(self) -> None:
        diff = (
            "--- a/x\n+++ b/x\n@@ -1,2 +1,3 @@\n line1\n line2\n+added\n"
        )
        assert verify_additive_only(diff) is True

    def test_rejects_deletion_line(self) -> None:
        diff = (
            "--- a/x\n+++ b/x\n@@ -1,2 +1,2 @@\n line1\n-deleted\n+added\n"
        )
        assert verify_additive_only(diff) is False

    def test_rejects_empty_diff(self) -> None:
        assert verify_additive_only("") is False
        assert verify_additive_only("   \n  ") is False

    def test_rejects_shrinking_hunk(self) -> None:
        # D < B in hunk header — file shrinks.
        diff = (
            "--- a/x\n+++ b/x\n@@ -1,3 +1,2 @@\n a\n b\n-c\n"
        )
        assert verify_additive_only(diff) is False

    def test_skips_file_headers(self) -> None:
        # ``--- a/...`` must NOT be mistaken for a removal line.
        diff = (
            "--- a/skills/movie-experts/test_skill/SKILL.md\n"
            "+++ b/skills/movie-experts/test_skill/SKILL.md\n"
            "@@ -1,1 +1,2 @@\n a\n+b\n"
        )
        assert verify_additive_only(diff) is True

    def test_skips_hunk_headers(self) -> None:
        # Hunk header lines ``@@ ... @@`` are skipped, not treated as
        # content.
        diff = (
            "--- a/x\n+++ b/x\n@@ -1,1 +1,2 @@\n a\n+b\n"
        )
        assert verify_additive_only(diff) is True

    def test_accepts_fixture_additive_diff(self) -> None:
        diff = ADDITIVE_DIFF.read_text(encoding="utf-8")
        assert verify_additive_only(diff) is True

    def test_rejects_fixture_violating_deletion_diff(self) -> None:
        diff = VIOLATING_DELETION_DIFF.read_text(encoding="utf-8")
        assert verify_additive_only(diff) is False


# --------------------------------------------------------------------------- #
# TestExtractFrontmatterBlock
# --------------------------------------------------------------------------- #


class TestExtractFrontmatterBlock:
    def test_returns_block_with_delimiters(self) -> None:
        content = "---\nfoo: bar\n---\nbody\n"
        block = _extract_frontmatter_block(content)
        assert block.startswith("---")
        assert "foo: bar" in block
        assert block.rstrip().endswith("---") or "\n---\n" in block

    def test_returns_empty_when_no_frontmatter(self) -> None:
        assert _extract_frontmatter_block("body only\n") == ""

    def test_returns_empty_when_no_closing_delimiter(self) -> None:
        assert _extract_frontmatter_block("---\nfoo: bar\n") == ""


# --------------------------------------------------------------------------- #
# TestVerifyFound08ByteIntact
# --------------------------------------------------------------------------- #


class TestVerifyFound08ByteIntact:
    def test_passes_on_byte_equal(self, tmp_path: Path) -> None:
        original = SAMPLE_SKILL_MD.read_text(encoding="utf-8")
        before_block = _extract_frontmatter_block(original)
        after_path = tmp_path / "after.md"
        after_path.write_text(original, encoding="utf-8")
        assert verify_found08_byte_intact(before_block, after_path) is True

    def test_fails_on_byte_different_frontmatter(self, tmp_path: Path) -> None:
        # Pitfall 4: frontmatter bytes differ even if parsed values match.
        original = SAMPLE_SKILL_MD.read_text(encoding="utf-8")
        before_block = _extract_frontmatter_block(original)
        # Swap the related_skills list order — same parsed values set-wise,
        # but bytes differ.
        modified = original.replace("[a, b]", "[b, a]")
        after_path = tmp_path / "after.md"
        after_path.write_text(modified, encoding="utf-8")
        assert verify_found08_byte_intact(before_block, after_path) is False

    def test_cr03_passes_when_no_prior_frontmatter(self, tmp_path: Path) -> None:
        # CR-03: a pre-existing file WITHOUT frontmatter (e.g. a refs/notes.md)
        # that gains a frontmatter block via patch should NOT trip the
        # byte-intact check — there was no frontmatter to preserve.
        before_block = ""  # _extract_frontmatter_block returns "" for no-FM
        after_path = tmp_path / "after.md"
        after_path.write_text(
            "---\nkey: value\n---\nbody content\n", encoding="utf-8"
        )
        assert verify_found08_byte_intact(before_block, after_path) is True


# --------------------------------------------------------------------------- #
# TestBuildCommitMessage
# --------------------------------------------------------------------------- #


class TestBuildCommitMessage:
    def test_format_match(self) -> None:
        msg = build_commit_message(
            insight_summary="Add SCAMPER examples",
            feedback_ids=["fb_1", "fb_2"],
            eval_verdict="pass",
            eval_mean_delta=0.15,
        )
        assert msg == (
            "feat(evolution): Add SCAMPER examples | "
            "feedback: fb_1,fb_2 | eval: pass:0.15"
        )

    def test_truncates_to_72_chars(self) -> None:
        long = "x" * 100
        msg = build_commit_message(
            insight_summary=long,
            feedback_ids=["fb_1"],
            eval_verdict="pass",
            eval_mean_delta=0.1,
        )
        # Subject portion is truncated to 72 chars.
        # Find the subject between "feat(evolution): " and " | feedback:".
        subject = msg.split("feat(evolution): ", 1)[1].split(" | feedback:", 1)[0]
        assert len(subject) == 72

    def test_empty_feedback_ids_uses_none(self) -> None:
        msg = build_commit_message(
            insight_summary="x",
            feedback_ids=[],
            eval_verdict="pass",
            eval_mean_delta=0.0,
        )
        assert "feedback: none" in msg

    def test_cr05_strips_newlines_from_subject(self) -> None:
        # CR-05: LLM-controlled insight_summary with embedded newlines
        # must not forge a multi-line commit body.
        msg = build_commit_message(
            insight_summary="line1\nline2",
            feedback_ids=["fb_1"],
            eval_verdict="pass",
            eval_mean_delta=0.1,
        )
        assert "\n" not in msg

    def test_cr05_strips_pipes_from_subject(self) -> None:
        # CR-05: pipes in subject would corrupt the | machine format.
        msg = build_commit_message(
            insight_summary="a|b|c",
            feedback_ids=["fb_1"],
            eval_verdict="pass",
            eval_mean_delta=0.1,
        )
        # Pipe should be replaced with space.
        subject = msg.split("feat(evolution): ", 1)[1].split(" | feedback:", 1)[0]
        assert "|" not in subject

    def test_cr05_drops_invalid_feedback_ids(self) -> None:
        # CR-05: feedback_ids containing newlines / spaces / pipes are
        # dropped; only well-formed IDs survive.
        msg = build_commit_message(
            insight_summary="x",
            feedback_ids=["fb_valid_1", "bad id", "has\nnewline", "fb_valid_2"],
            eval_verdict="pass",
            eval_mean_delta=0.1,
        )
        assert "fb_valid_1" in msg
        assert "fb_valid_2" in msg
        assert "bad id" not in msg
        assert "has\nnewline" not in msg

    def test_cr05_coerces_unknown_verdict(self) -> None:
        # CR-05: unknown eval_verdict coerced to "unknown".
        msg = build_commit_message(
            insight_summary="x",
            feedback_ids=["fb_1"],
            eval_verdict="totally bogus\nwith newline",
            eval_mean_delta=0.1,
        )
        assert "eval: unknown:" in msg


# --------------------------------------------------------------------------- #
# TestRevertFiles
# --------------------------------------------------------------------------- #


class TestRevertFiles:
    def test_reverts_existing_file_via_checkout(
        self, evolution_env: dict
    ) -> None:
        repo = evolution_env["repo_root"]
        skill_abs = evolution_env["skill_abs_path"]
        # Mutate the committed file.
        skill_abs.write_text("dirty\n", encoding="utf-8")
        revert_files([SKILL_REL_PATH], repo)
        # File should be restored to HEAD content.
        assert "expert_id: test_skill" in skill_abs.read_text(encoding="utf-8")

    def test_cleans_added_file_via_git_clean(
        self, evolution_env: dict, tmp_path: Path
    ) -> None:
        repo = evolution_env["repo_root"]
        new_rel = "skills/movie-experts/test_skill/NEW_REF.md"
        new_abs = repo / new_rel
        new_abs.parent.mkdir(parents=True, exist_ok=True)
        new_abs.write_text("new file\n", encoding="utf-8")
        revert_files([new_rel], repo)
        assert not new_abs.exists()


# --------------------------------------------------------------------------- #
# TestApplyPatchTransactionHappyPath
# --------------------------------------------------------------------------- #


class TestApplyPatchTransactionHappyPath:
    def test_applies_and_commits(self, evolution_env: dict, tmp_path: Path) -> None:
        repo = evolution_env["repo_root"]
        # Copy the additive fixture into the repo's skill file location
        # so the patch context lines match.
        patch_path = tmp_path / "additive.patch"
        # Build a patch that matches the sample_skill_md.md content.
        # The sample has lines: ---\nname:...\n...\n---\n# Test...\n## When...\n...\n## References\n- [Sample]...
        # We add after "## References".
        sample_lines = SAMPLE_SKILL_MD.read_text(encoding="utf-8").splitlines(keepends=True)
        # Find the index of "## References"
        ref_idx = next(
            i for i, ln in enumerate(sample_lines) if "## References" in ln
        )
        insert_idx = ref_idx + 1
        addition = "- [New](new.md)\n"
        new_lines = sample_lines[:insert_idx] + [addition] + sample_lines[insert_idx:]
        import difflib
        diff_text = "".join(difflib.unified_diff(
            sample_lines, new_lines,
            fromfile=f"a/{SKILL_REL_PATH}", tofile=f"b/{SKILL_REL_PATH}",
            lineterm="\n",
        ))
        patch_path.write_text(diff_text, encoding="utf-8")

        result = apply_patch_transaction(
            patch_path=patch_path,
            repo_root=repo,
            commit_message="feat(evolution): test apply | feedback: none | eval: pass:0.00",
        )
        assert isinstance(result, ApplyResult)
        assert result.commit_sha
        assert SKILL_REL_PATH in result.files_modified

        # Verify the commit exists in git log.
        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=str(repo), capture_output=True, text=True, encoding="utf-8",
        )
        assert "feat(evolution): test apply" in log.stdout

        # Verify the file content was actually modified.
        after = (repo / SKILL_REL_PATH).read_text(encoding="utf-8")
        assert "[New](new.md)" in after


# --------------------------------------------------------------------------- #
# TestApplyPatchTransactionRevertOnAdditive
# --------------------------------------------------------------------------- #


class TestApplyPatchTransactionRevertOnAdditive:
    def test_reverts_on_deletion_violation(
        self, evolution_env: dict, tmp_path: Path
    ) -> None:
        repo = evolution_env["repo_root"]
        # Build a deletion patch against the sample skill.
        sample_lines = SAMPLE_SKILL_MD.read_text(encoding="utf-8").splitlines(keepends=True)
        # Delete the "- [Sample](sample.md)" line.
        target_idx = next(
            i for i, ln in enumerate(sample_lines) if "[Sample]" in ln
        )
        new_lines = sample_lines[:target_idx] + sample_lines[target_idx + 1:]
        import difflib
        diff_text = "".join(difflib.unified_diff(
            sample_lines, new_lines,
            fromfile=f"a/{SKILL_REL_PATH}", tofile=f"b/{SKILL_REL_PATH}",
            lineterm="\n",
        ))
        patch_path = tmp_path / "del.patch"
        patch_path.write_text(diff_text, encoding="utf-8")

        with pytest.raises(ApplyError):
            apply_patch_transaction(
                patch_path=patch_path,
                repo_root=repo,
                commit_message="should fail",
            )
        # Working tree must be clean after revert.
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo), capture_output=True, text=True, encoding="utf-8",
        )
        assert status.stdout.strip() == "", \
            f"working tree dirty after revert: {status.stdout!r}"


# --------------------------------------------------------------------------- #
# TestApplyPatchTransactionDirtyTree
# --------------------------------------------------------------------------- #


class TestApplyPatchTransactionDirtyTree:
    def test_refuses_dirty_tree(
        self, evolution_env: dict, tmp_path: Path
    ) -> None:
        repo = evolution_env["repo_root"]
        # Dirty the tree.
        (repo / SKILL_REL_PATH).write_text("dirty\n", encoding="utf-8")
        patch_path = tmp_path / "p.patch"
        patch_path.write_text(
            f"--- a/{SKILL_REL_PATH}\n+++ b/{SKILL_REL_PATH}\n@@ -1,1 +1,2 @@\n x\n+y\n",
            encoding="utf-8",
        )
        with pytest.raises(ApplyError, match="(?i)dirty"):
            apply_patch_transaction(
                patch_path=patch_path,
                repo_root=repo,
                commit_message="should fail",
            )


# --------------------------------------------------------------------------- #
# TestApplyPatchTransactionGitAuthor
# --------------------------------------------------------------------------- #


class TestApplyPatchTransactionGitAuthor:
    def test_sets_local_author_if_global_unset(
        self, evolution_env: dict, tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        repo = evolution_env["repo_root"]
        # Isolate from global/system git config so the fallback triggers.
        # Without this, the operator's global user.email leaks into the
        # repo and the fallback never fires.
        monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")
        monkeypatch.setenv("GIT_CONFIG_SYSTEM", "/dev/null")
        # Also unset repo-local config set by the evolution_env fixture.
        subprocess.run(
            ["git", "config", "--unset", "user.email"],
            cwd=str(repo), capture_output=True,
        )
        subprocess.run(
            ["git", "config", "--unset", "user.name"],
            cwd=str(repo), capture_output=True,
        )

        # Build an additive patch.
        sample_lines = SAMPLE_SKILL_MD.read_text(encoding="utf-8").splitlines(keepends=True)
        ref_idx = next(i for i, ln in enumerate(sample_lines) if "## References" in ln)
        addition = "- [Z](z.md)\n"
        new_lines = sample_lines[:ref_idx + 1] + [addition] + sample_lines[ref_idx + 1:]
        import difflib
        diff_text = "".join(difflib.unified_diff(
            sample_lines, new_lines,
            fromfile=f"a/{SKILL_REL_PATH}", tofile=f"b/{SKILL_REL_PATH}",
            lineterm="\n",
        ))
        patch_path = tmp_path / "p.patch"
        patch_path.write_text(diff_text, encoding="utf-8")

        result = apply_patch_transaction(
            patch_path=patch_path,
            repo_root=repo,
            commit_message="feat(evolution): author test",
        )
        assert result.commit_sha

        # Verify the repo-local config was set (reads through to local
        # config even with global/system disabled).
        email = subprocess.run(
            ["git", "config", "user.email"],
            cwd=str(repo), capture_output=True, text=True, encoding="utf-8",
            env={**__import__("os").environ,
                 "GIT_CONFIG_GLOBAL": "/dev/null",
                 "GIT_CONFIG_SYSTEM": "/dev/null"},
        ).stdout.strip()
        assert email == "hermes-evolution@local"
