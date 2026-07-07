"""Dry-run zero-mutation tests (T-55-11, T-55-14, EVAL-06 invariant).

Asserts that:
  - Default invocation (no flags) is dry-run.
  - ``--dry-run`` explicit is identical to default.
  - Dry-run produces zero ``append_audit`` calls.
  - Source FeedbackStore files are byte-identical before vs after.
  - ``--apply`` without ``--no-prompt`` aborts on missing confirmation.
  - ``--apply --no-prompt`` performs writes (exercises live path for coverage).

Per CLAUDE.md conventions:
  - ``encoding="utf-8"`` on every ``open()``.
  - ``monkeypatch.setenv`` for HERMES_HOME redirection.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


def _file_hashes(root: Path) -> dict[Path, str]:
    """Return ``{relative_path: sha256}`` for every file under ``root``."""
    out: dict[Path, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root)
            out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


# ── Default mode is dry-run (EVAL-06 invariant) ──────────────────────────


class TestDefaultModeIsDryRun:
    def test_no_args_runs_dry_run(self, run_migration) -> None:
        """EVAL-06 invariant — default mode is dry-run, never live."""
        result, summary = run_migration()
        assert result.returncode == 0
        assert summary.get("dry_run") is True

    def test_explicit_dry_run_flag_identical_to_default(
        self, run_migration
    ) -> None:
        result_default, summary_default = run_migration()
        result_explicit, summary_explicit = run_migration("--dry-run")
        assert result_explicit.returncode == 0
        assert summary_explicit.get("dry_run") is True
        # Both must produce the same record_id set (deterministic UUIDv5).
        if "source_record_ids_accounted" in summary_default:
            assert (
                summary_default["source_record_ids_accounted"]
                == summary_explicit["source_record_ids_accounted"]
            )


# ── Zero audit entries in dry-run (T-55-14) ─────────────────────────────


class TestDryRunZeroAuditEntries:
    def test_dry_run_zero_audit_calls(
        self, run_migration, mock_audit_chain
    ) -> None:
        """``append_audit`` must NEVER be called in dry-run mode."""
        run_migration("--dry-run")
        assert len(mock_audit_chain) == 0, (
            f"expected 0 audit calls in dry-run, got {len(mock_audit_chain)}: "
            f"{mock_audit_chain}"
        )


# ── Source FeedbackStore unchanged (T-55-11) ────────────────────────────


class TestSourceFeedbackStoreUnchanged:
    def test_source_files_unchanged_after_dry_run(
        self, sample_feedbackstore, run_migration
    ) -> None:
        """All source files must be byte-identical before vs after dry-run."""
        before = _file_hashes(sample_feedbackstore)
        run_migration("--dry-run")
        after = _file_hashes(sample_feedbackstore)
        # Same set of files.
        assert set(before.keys()) == set(after.keys()), (
            "file set changed: "
            f"added={set(after.keys()) - set(before.keys())}, "
            f"removed={set(before.keys()) - set(after.keys())}"
        )
        # Same content per file.
        for rel, h in before.items():
            assert after[rel] == h, f"source file modified during dry-run: {rel}"

    def test_source_files_mtimes_unchanged_after_dry_run(
        self, sample_feedbackstore, run_migration
    ) -> None:
        """mtimes must not change — dry-run opens files read-only."""
        before_mtimes = {
            p.relative_to(sample_feedbackstore): p.stat().st_mtime_ns
            for p in sorted(sample_feedbackstore.rglob("*"))
            if p.is_file()
        }
        run_migration("--dry-run")
        after_mtimes = {
            p.relative_to(sample_feedbackstore): p.stat().st_mtime_ns
            for p in sorted(sample_feedbackstore.rglob("*"))
            if p.is_file()
        }
        assert set(before_mtimes.keys()) == set(after_mtimes.keys())
        for rel, m in before_mtimes.items():
            assert after_mtimes[rel] == m, f"mtime changed: {rel}"


# ── --apply requires confirmation (T-55-15) ─────────────────────────────


class TestApplyRequiresConfirmation:
    def test_apply_without_confirmation_aborts(
        self, run_migration, mock_audit_chain
    ) -> None:
        """``--apply`` without confirmation input must abort with non-zero exit.

        The script prompts: "Type 'apply' to confirm live migration:".
        With stdin closed or wrong input, it must NOT call append_audit.
        """
        # Provide wrong confirmation input.
        result, _ = run_migration(
            "--apply", expect_exit=None, stdin_input="no\n"
        )
        assert result.returncode != 0, (
            "--apply without correct confirmation must abort non-zero"
        )
        # And NO audit entry should have been written.
        assert len(mock_audit_chain) == 0

    def test_apply_with_correct_confirmation_proceeds(
        self,
        run_migration,
        mock_audit_chain,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """With correct confirmation, --apply calls append_audit + writes target.

        This test exercises the live path for coverage. v12+ is when this
        becomes operator-facing per 04-MIGRATION-PATH.md §4.7 Step 4.
        """
        # NOTE: the live path writes to a target path under HERMES_HOME
        # (NOT to mem0 in v11.0 PoC — that's v12+). The mock_audit_chain
        # fixture intercepts append_audit so no real audit log is mutated.
        result, _ = run_migration(
            "--apply", expect_exit=0, stdin_input="apply\n"
        )
        assert result.returncode == 0
        # Audit entry MUST be appended in --apply mode (T-55-15 mitigation).
        assert len(mock_audit_chain) >= 1, (
            "expected ≥1 audit call in --apply mode, got "
            f"{len(mock_audit_chain)}"
        )
        # The audit action should be "auto_apply".
        actions = [c.get("action") for c in mock_audit_chain]
        assert "auto_apply" in actions

    def test_apply_no_prompt_skips_confirmation(
        self,
        run_migration,
        mock_audit_chain,
    ) -> None:
        """``--apply --no-prompt`` skips confirmation (for scripting).

        Useful for CI / batch jobs. Use with care.
        """
        result, _ = run_migration(
            "--apply", "--no-prompt", expect_exit=0
        )
        assert result.returncode == 0
        assert len(mock_audit_chain) >= 1


# ── Mutual exclusion + arg validation ────────────────────────────────────


class TestArgValidation:
    def test_dry_run_and_apply_mutually_exclusive(self, run_migration) -> None:
        """``--dry-run --apply`` together must error."""
        result, _ = run_migration(
            "--dry-run", "--apply", expect_exit=None
        )
        assert result.returncode != 0

    def test_unknown_source_path_errors(self, run_migration, tmp_path) -> None:
        """``--source`` pointing at a nonexistent path must error."""
        bogus = tmp_path / "does-not-exist"
        result, _ = run_migration(
            "--source", str(bogus), expect_exit=None
        )
        assert result.returncode != 0
