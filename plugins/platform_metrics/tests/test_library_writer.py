"""Tests for plugins.platform_metrics.library_writer (DATA-03).

Phase 42 Plan 03 Task 3 — TDD RED: tests assert the atomic eval_score
write-back contract. 8 tests cover roundtrip load/write, eval_score-only
mutation, unknown-formula handling, atomic temp cleanup, commit_sha
generation, and the move_suggestion trigger.

Per CLAUDE.md: ``from __future__ import annotations``, double-quoted
strings, ``encoding="utf-8"`` on every ``open()`` (Ruff PLW1514).
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest


# ──────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────


_REAL_LIBRARY = (
    Path(__file__).resolve().parent.parent.parent
    / "formula_library"
    / "library"
)
_REAL_FORMULA_FILENAME = "formula_urban_fantasy_light_01.json"


def _seed_library(tmp_path: Path) -> Path:
    """Copy the real formula_urban_fantasy_light_01.json into tmp/library/.

    Returns the library_dir (tmp_path/library). Tests use this as the
    library_dir argument so they never mutate the real formula_library.
    """
    library_dir = tmp_path / "library"
    library_dir.mkdir()
    shutil.copy(
        _REAL_LIBRARY / _REAL_FORMULA_FILENAME,
        library_dir / _REAL_FORMULA_FILENAME,
    )
    return library_dir


def _make_suggestion(
    *,
    suggestion_id: str = "urban-fantasy-light-01_high_hook_dropoff_1700000000",
    formula_id: str = "urban-fantasy-light-01",
    observed_metric: float = 0.32,
    status: str = "approved",
) -> "object":
    """Build a TuningSuggestion fixture (status='approved' for apply)."""
    from plugins.platform_metrics.schema import (
        MetricTrigger,
        TuningSuggestion,
    )

    return TuningSuggestion(
        suggestion_id=suggestion_id,
        formula_id=formula_id,
        trigger=MetricTrigger.HIGH_HOOK_DROPOFF,
        observed_metric=observed_metric,
        threshold=0.20,
        suggested_action="加 hook 强度",
        rationale="hook_dropoff exceeds threshold",
        evidence=["fb_1", "v1"],
        status=status,
        ts_queued=datetime.now(timezone.utc).isoformat(),
    )


# ──────────────────────────────────────────────────────────────────────────
# Test 1: load_formula_file roundtrip
# ──────────────────────────────────────────────────────────────────────────


def test_load_formula_file_roundtrip(tmp_path: Path) -> None:
    """load_formula_file returns a dict with formula_id + eval_score=None."""
    from plugins.platform_metrics.library_writer import load_formula_file

    library_dir = _seed_library(tmp_path)
    formula_path = library_dir / _REAL_FORMULA_FILENAME

    data = load_formula_file(formula_path)
    assert data["formula_id"] == "urban-fantasy-light-01"
    assert data["eval_score"] is None
    # All other expected fields preserved.
    assert data["genre"] == "都市奇幻"
    assert data["mood"] == "轻喜剧"
    assert data["hook_pattern"] == "contrast"


# ──────────────────────────────────────────────────────────────────────────
# Test 2: write_formula_file atomic (no .tmp leftover)
# ──────────────────────────────────────────────────────────────────────────


def test_write_formula_file_atomic(tmp_path: Path) -> None:
    """write_formula_file leaves no .tmp file in the directory after write."""
    from plugins.platform_metrics.library_writer import (
        load_formula_file,
        write_formula_file,
    )

    library_dir = _seed_library(tmp_path)
    formula_path = library_dir / _REAL_FORMULA_FILENAME

    data = load_formula_file(formula_path)
    data["eval_score"] = 0.42
    write_formula_file(formula_path, data)

    # No .tmp file remaining in the directory.
    leftovers = list(library_dir.glob(".formula.*.tmp"))
    assert leftovers == [], f"unexpected temp leftover: {leftovers}"
    # File written correctly.
    rewritten = json.loads(formula_path.read_text(encoding="utf-8"))
    assert rewritten["eval_score"] == pytest.approx(0.42)


# ──────────────────────────────────────────────────────────────────────────
# Test 3: apply_suggestion updates eval_score to observed_metric
# ──────────────────────────────────────────────────────────────────────────


def test_apply_suggestion_updates_eval_score(tmp_path: Path) -> None:
    """apply_suggestion writes observed_metric to eval_score."""
    from plugins.platform_metrics.library_writer import (
        apply_suggestion,
        load_formula_file,
    )

    library_dir = _seed_library(tmp_path)
    tuning_dir = tmp_path / "tuning"
    tuning_dir.mkdir()

    suggestion = _make_suggestion(observed_metric=0.32)
    commit_sha = apply_suggestion(
        suggestion=suggestion,
        library_dir=library_dir,
        tuning_dir=tuning_dir,
    )

    # Reload and verify eval_score.
    formula_path = library_dir / _REAL_FORMULA_FILENAME
    data = load_formula_file(formula_path)
    assert data["eval_score"] == pytest.approx(0.32)
    # commit_sha returned (length checked in Test 7).
    assert isinstance(commit_sha, str)


# ──────────────────────────────────────────────────────────────────────────
# Test 4: apply_suggestion preserves all non-eval_score fields
# ──────────────────────────────────────────────────────────────────────────


def test_apply_suggestion_preserves_other_fields(tmp_path: Path) -> None:
    """Every field EXCEPT eval_score is byte-identical after apply."""
    from plugins.platform_metrics.library_writer import (
        apply_suggestion,
        load_formula_file,
    )

    library_dir = _seed_library(tmp_path)
    tuning_dir = tmp_path / "tuning"
    tuning_dir.mkdir()

    formula_path = library_dir / _REAL_FORMULA_FILENAME
    original = load_formula_file(formula_path)
    # Deep-copy original for comparison (load_formula_file returns a fresh
    # dict each call, but be explicit).
    original_snapshot = json.loads(json.dumps(original))

    suggestion = _make_suggestion(observed_metric=0.55)
    apply_suggestion(
        suggestion=suggestion,
        library_dir=library_dir,
        tuning_dir=tuning_dir,
    )

    rewritten = load_formula_file(formula_path)
    # eval_score is the ONLY field that changed.
    assert rewritten["eval_score"] == pytest.approx(0.55)
    for key, value in original_snapshot.items():
        if key == "eval_score":
            continue
        assert key in rewritten, f"missing key after apply: {key}"
        assert rewritten[key] == value, (
            f"field {key!r} mutated by apply_suggestion: "
            f"before={value!r} after={rewritten[key]!r}"
        )


# ──────────────────────────────────────────────────────────────────────────
# Test 5: apply_suggestion unknown formula_id raises FileNotFoundError
# ──────────────────────────────────────────────────────────────────────────


def test_apply_suggestion_unknown_formula_id_raises(tmp_path: Path) -> None:
    """apply_suggestion raises FileNotFoundError for unknown formula_id."""
    from plugins.platform_metrics.library_writer import apply_suggestion

    library_dir = _seed_library(tmp_path)
    tuning_dir = tmp_path / "tuning"
    tuning_dir.mkdir()

    suggestion = _make_suggestion(formula_id="nonexistent-formula")
    with pytest.raises(FileNotFoundError, match="not found"):
        apply_suggestion(
            suggestion=suggestion,
            library_dir=library_dir,
            tuning_dir=tuning_dir,
        )


# ──────────────────────────────────────────────────────────────────────────
# Test 6: apply_suggestion cleans up temp file on os.replace failure
# ──────────────────────────────────────────────────────────────────────────


def test_apply_suggestion_atomic_temp_cleanup_on_failure(tmp_path: Path) -> None:
    """If os.replace raises, apply_suggestion cleans up the temp file."""
    from plugins.platform_metrics.library_writer import apply_suggestion

    library_dir = _seed_library(tmp_path)
    tuning_dir = tmp_path / "tuning"
    tuning_dir.mkdir()

    suggestion = _make_suggestion()

    # Monkeypatch os.replace inside library_writer to raise OSError.
    with patch(
        "plugins.platform_metrics.library_writer.os.replace",
        side_effect=OSError("simulated replace failure"),
    ):
        with pytest.raises(OSError, match="simulated replace failure"):
            apply_suggestion(
                suggestion=suggestion,
                library_dir=library_dir,
                tuning_dir=tuning_dir,
            )

    # No temp file leftover.
    leftovers = list(library_dir.glob(".formula.*.tmp"))
    assert leftovers == [], f"temp file not cleaned up: {leftovers}"


# ──────────────────────────────────────────────────────────────────────────
# Test 7: apply_suggestion returns 64-char sha256 hex commit_sha
# ──────────────────────────────────────────────────────────────────────────


def test_apply_suggestion_returns_commit_sha(tmp_path: Path) -> None:
    """Returned commit_sha is a 64-char sha256 hex string."""
    from plugins.platform_metrics.library_writer import apply_suggestion

    library_dir = _seed_library(tmp_path)
    tuning_dir = tmp_path / "tuning"
    tuning_dir.mkdir()

    suggestion = _make_suggestion(observed_metric=0.42)
    commit_sha = apply_suggestion(
        suggestion=suggestion,
        library_dir=library_dir,
        tuning_dir=tuning_dir,
    )

    assert isinstance(commit_sha, str)
    assert len(commit_sha) == 64, (
        f"commit_sha must be 64 hex chars (sha256), got {len(commit_sha)}: "
        f"{commit_sha!r}"
    )
    # All hex.
    int(commit_sha, 16)


# ──────────────────────────────────────────────────────────────────────────
# Test 8: apply_suggestion triggers move_suggestion pending → applied
# ──────────────────────────────────────────────────────────────────────────


def test_apply_suggestion_triggers_move_to_applied(tmp_path: Path) -> None:
    """apply_suggestion calls move_suggestion after a successful write."""
    from plugins.platform_metrics.library_writer import apply_suggestion

    library_dir = _seed_library(tmp_path)
    tuning_dir = tmp_path / "tuning"
    tuning_dir.mkdir()

    suggestion = _make_suggestion()

    with patch(
        "plugins.platform_metrics.library_writer.move_suggestion"
    ) as mock_move:
        commit_sha = apply_suggestion(
            suggestion=suggestion,
            library_dir=library_dir,
            tuning_dir=tuning_dir,
        )

    mock_move.assert_called_once()
    call_kwargs = mock_move.call_args.kwargs
    assert call_kwargs["suggestion_id"] == suggestion.suggestion_id
    assert call_kwargs["target_status"] == "applied"
    assert call_kwargs["tuning_dir"] == tuning_dir
    assert call_kwargs["commit_sha"] == commit_sha


# ──────────────────────────────────────────────────────────────────────────
# HIL invariant tests (load-bearing per execution_protocol)
# ──────────────────────────────────────────────────────────────────────────


def test_apply_suggestion_refuses_non_approved_status(tmp_path: Path) -> None:
    """apply_suggestion raises on status != 'approved' (HIL invariant)."""
    from plugins.platform_metrics.library_writer import (
        SuggestionNotApprovedError,
        apply_suggestion,
    )

    library_dir = _seed_library(tmp_path)
    tuning_dir = tmp_path / "tuning"
    tuning_dir.mkdir()

    # status='pending' — operator has not approved yet.
    suggestion = _make_suggestion(status="pending")
    with pytest.raises(SuggestionNotApprovedError):
        apply_suggestion(
            suggestion=suggestion,
            library_dir=library_dir,
            tuning_dir=tuning_dir,
        )


def test_library_writer_is_only_caller_to_formula_library(tmp_path: Path) -> None:
    """AST-walk: apply_suggestion is the only function writing to library/*.json.

    Single-caller invariant — mirrors the v6.0 EVOL pattern. Guards
    against future regressions where a helper opens a formula file
    directly without going through apply_suggestion (which enforces the
    HIL gate).
    """
    import ast

    source = (
        Path(__file__).resolve().parent.parent / "library_writer.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    # Find every function that opens/writes a file under library_dir.
    # Pattern: any function that calls write_formula_file or invokes
    # Path.write_text / open('w') on a library path. apply_suggestion
    # is the canonical entry; load_formula_file + write_formula_file are
    # the low-level helpers (write_formula_file takes a path arg, so it
    # is the actual writer — but it must only be called by apply_suggestion
    # for library writes).
    write_callers: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for sub in ast.walk(node):
                if (
                    isinstance(sub, ast.Call)
                    and isinstance(sub.func, ast.Name)
                    and sub.func.id == "write_formula_file"
                ):
                    write_callers.append(node.name)

    # write_formula_file may be called only from apply_suggestion.
    assert set(write_callers) <= {"apply_suggestion"}, (
        f"write_formula_file called from unexpected function(s) "
        f"{set(write_callers) - {'apply_suggestion'}}!r — "
        f"HIL invariant: apply_suggestion is the sole entry point"
    )
