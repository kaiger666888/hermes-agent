"""Baseline snapshot tool for movie-experts skill refactors.

Captures byte-exact copies of all 14 expert SKILL.md files along with a
cryptographic provenance record (sha256, git sha, ISO 8601 timestamp).
The `verify` subcommand detects any drift between the captured baseline
and the current state of the source skills, enabling before/after
ablation comparisons across Phase 3/5/6 refactors (RESEARCH.md
PITFALLS #8, Phase 3 REFACTOR-06/07).

Design notes:
- stdlib only (no third-party packages). Uses ``subprocess`` to invoke
  ``git rev-parse`` for provenance; degrades gracefully to the literal
  string ``"uncommitted"`` if git is unavailable or the cwd is not a
  git repo (T-00-06 accept disposition).
- Hardcoded EXPERT_DIRS list prevents synthetic-injection spoofing
  (T-00-08 in the threat model).
- All `open()` calls pass `encoding="utf-8"` (CLAUDE.md PLW1514).
- Byte-level hashing (`.read_bytes()`) avoids any encoding ambiguity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

BASELINE_TAG = "eval-baseline-v1"

# Frozen list of the 14 existing expert IDs. Unknown directories are
# silently skipped — this is a deliberate anti-spoofing measure
# (T-00-08). New experts added in later waves must explicitly extend
# this list after their plan lands.
EXPERT_DIRS: list[str] = [
    "animator",
    "colorist",
    "composer",
    "continuity",
    "drawer",
    "editor",
    "foley",
    "mixer",
    "performer",
    "scene_builder",
    "screenplay",
    "spatial_audio",
    "style_genome",
    "voicer",
]

_REQUIRED_PROVENANCE_KEYS = frozenset(
    {
        "expert_id",
        "tag",
        "source_path",
        "sha256",
        "git_sha",
        "captured_at",
        "byte_size",
    }
)


# --------------------------------------------------------------------------- #
# Provenance computation
# --------------------------------------------------------------------------- #


def compute_provenance(
    skill_path: Path,
    expert_id: str,
    git_sha: str,
    *,
    repo_root: Path | None = None,
) -> dict:
    """Compute provenance metadata for a single SKILL.md file.

    Reads the file in binary mode (no encoding ambiguity) so sha256 is
    a true content hash. The returned dict matches the PROVENANCE.json
    schema documented in 00-02-PLAN.md.

    If ``repo_root`` is provided, ``source_path`` is recorded as a
    repo-relative POSIX path (portable across clones / CI runs).
    Otherwise the absolute path is used.
    """
    if not skill_path.is_file():
        raise FileNotFoundError(f"skill file not found: {skill_path}")

    raw = skill_path.read_bytes()
    sha256 = hashlib.sha256(raw).hexdigest()
    captured_at = datetime.now(timezone.utc).isoformat()

    if repo_root is not None:
        try:
            rel = skill_path.resolve().relative_to(repo_root.resolve())
            source_path_str = rel.as_posix()
        except ValueError:
            # skill is outside repo_root — fall back to absolute.
            source_path_str = str(skill_path)
    else:
        source_path_str = str(skill_path)

    return {
        "expert_id": expert_id,
        "tag": BASELINE_TAG,
        "source_path": source_path_str,
        "sha256": sha256,
        "git_sha": git_sha,
        "captured_at": captured_at,
        "byte_size": len(raw),
    }


# --------------------------------------------------------------------------- #
# git helpers
# --------------------------------------------------------------------------- #


def _current_git_sha(repo_root: Path) -> str:
    """Return the short-form HEAD sha of the repo at ``repo_root``.

    Falls back to the literal string ``"uncommitted"`` if git is
    unavailable, the directory is not a repo, or HEAD is unborn.
    This preserves the provenance record without crashing the capture
    (T-00-06 accept disposition).
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
    except (
        FileNotFoundError,
        subprocess.SubprocessError,
        OSError,
    ) as exc:
        print(
            f"[snapshot] warning: git rev-parse failed ({exc}); "
            "marking baseline as 'uncommitted'",
            file=sys.stderr,
        )
        return "uncommitted"

    if result.returncode != 0 or not result.stdout.strip():
        return "uncommitted"
    return result.stdout.strip()


# --------------------------------------------------------------------------- #
# Capture + verify
# --------------------------------------------------------------------------- #


def capture_baselines(
    skills_dir: Path,
    baseline_dir: Path,
    git_sha: str | None = None,
    *,
    repo_root: Path | None = None,
) -> list[Path]:
    """Snapshot all 14 expert SKILL.md files into ``baseline_dir``.

    For each expert in EXPERT_DIRS:
      1. Read ``skills_dir/<expert>/SKILL.md`` as bytes.
      2. Write the byte-exact copy to ``baseline_dir/<expert>/SKILL.md``.
      3. Compute provenance and write ``baseline_dir/<expert>/PROVENANCE.json``.

    Returns the list of created baseline directories (length == 14).
    Raises FileNotFoundError if any of the 14 source skills is missing.

    If ``repo_root`` is None, it defaults to ``skills_dir.parents[1]``
    (so source_path in provenance is repo-relative).
    """
    if repo_root is None:
        repo_root = skills_dir.parents[1]
    if git_sha is None:
        git_sha = _current_git_sha(repo_root)

    missing: list[str] = []
    for expert_id in EXPERT_DIRS:
        if not (skills_dir / expert_id / "SKILL.md").is_file():
            missing.append(expert_id)
    if missing:
        raise FileNotFoundError(
            f"missing SKILL.md for experts: {', '.join(missing)}"
        )

    # CR-02: Symmetric check — detect live expert subdirectories under
    # skills_dir that are NOT in EXPERT_DIRS. Without this, a contributor
    # who adds ``skills/movie-experts/cinematographer/SKILL.md`` without
    # extending EXPERT_DIRS would silently get their baseline skipped,
    # and Phase 3/5/6 ablation comparisons would compare against a
    # stale/absent baseline for that expert. Fail loud so the operator
    # must extend EXPERT_DIRS explicitly.
    live_experts = {
        p.name
        for p in skills_dir.iterdir()
        if p.is_dir()
        and (p / "SKILL.md").is_file()
        and not p.name.startswith("_")
    }
    known = set(EXPERT_DIRS)
    untracked = live_experts - known
    if untracked:
        raise RuntimeError(
            f"Untracked expert directories found: {sorted(untracked)}. "
            f"Add them to EXPERT_DIRS in snapshot.py before capturing, "
            f"or prefix with '_' if they are not movie-expert skills."
        )

    created: list[Path] = []
    for expert_id in EXPERT_DIRS:
        source = skills_dir / expert_id / "SKILL.md"
        target_dir = baseline_dir / expert_id
        target_dir.mkdir(parents=True, exist_ok=True)

        raw = source.read_bytes()
        (target_dir / "SKILL.md").write_bytes(raw)

        provenance = compute_provenance(
            source,
            expert_id=expert_id,
            git_sha=git_sha,
            repo_root=repo_root,
        )
        (target_dir / "PROVENANCE.json").write_text(
            json.dumps(provenance, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        created.append(target_dir)

    return created


def verify_baselines(
    skills_dir: Path, baseline_dir: Path
) -> tuple[bool, list[dict]]:
    """Compare every source SKILL.md against its captured baseline.

    Returns ``(ok, drifts)`` where ``drifts`` is a list of dicts, one
    per drifted expert, each containing:
      - expert_id
      - expected (baseline sha256)
      - actual (current source sha256)
      - source_path
    """
    drifts: list[dict] = []
    for expert_id in EXPERT_DIRS:
        baseline_prov_path = baseline_dir / expert_id / "PROVENANCE.json"
        if not baseline_prov_path.is_file():
            drifts.append(
                {
                    "expert_id": expert_id,
                    "expected": "<missing baseline>",
                    "actual": "<no baseline>",
                    "source_path": str(
                        skills_dir / expert_id / "SKILL.md"
                    ),
                }
            )
            continue

        try:
            provenance = json.loads(
                baseline_prov_path.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError) as exc:
            drifts.append(
                {
                    "expert_id": expert_id,
                    "expected": f"<unreadable baseline: {exc}>",
                    "actual": "<no baseline>",
                    "source_path": str(
                        skills_dir / expert_id / "SKILL.md"
                    ),
                }
            )
            continue

        expected_sha = provenance["sha256"]

        source_path = skills_dir / expert_id / "SKILL.md"
        if not source_path.is_file():
            drifts.append(
                {
                    "expert_id": expert_id,
                    "expected": expected_sha,
                    "actual": "<source missing>",
                    "source_path": str(source_path),
                }
            )
            continue

        actual_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if actual_sha != expected_sha:
            drifts.append(
                {
                    "expert_id": expert_id,
                    "expected": expected_sha,
                    "actual": actual_sha,
                    "source_path": str(source_path),
                }
            )

    return (len(drifts) == 0, drifts)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _default_skills_dir(script_file: Path) -> Path:
    # <repo>/skills/movie-experts/_eval/snapshot.py -> <repo>/skills/movie-experts
    return script_file.resolve().parent.parent


def _default_baseline_dir(script_file: Path) -> Path:
    return script_file.resolve().parent / "baseline"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Capture or verify byte-exact baselines of the 14 "
            "movie-experts SKILL.md files."
        )
    )
    parser.add_argument(
        "mode",
        choices=("capture", "verify"),
        help="capture -> write baselines; verify -> diff against baselines",
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default=None,
        help=(
            "Root movie-experts skills directory "
            "(default: <snapshot.py parent>/..)"
        ),
    )
    parser.add_argument(
        "--baseline-dir",
        type=Path,
        default=None,
        help=(
            "Baseline output directory "
            "(default: <snapshot.py parent>/baseline)"
        ),
    )
    args = parser.parse_args(argv)

    script_file = Path(__file__)
    skills_dir = args.skills_dir or _default_skills_dir(script_file)
    baseline_dir = args.baseline_dir or _default_baseline_dir(script_file)

    if args.mode == "capture":
        # Pre-flight: assert all 14 source skills exist.
        missing = [
            expert_id
            for expert_id in EXPERT_DIRS
            if not (skills_dir / expert_id / "SKILL.md").is_file()
        ]
        if missing:
            print(
                f"[snapshot] FATAL: missing SKILL.md for: {', '.join(missing)}",
                file=sys.stderr,
            )
            return 2

        git_sha = _current_git_sha(skills_dir.parents[1])
        created = capture_baselines(
            skills_dir,
            baseline_dir,
            git_sha=git_sha,
            repo_root=skills_dir.parents[1],
        )
        print(
            f"[snapshot] Captured {len(created)} baselines "
            f"(git_sha={git_sha}, tag={BASELINE_TAG}) -> {baseline_dir}"
        )
        return 0

    # verify
    ok, drifts = verify_baselines(skills_dir, baseline_dir)
    if ok:
        print(
            f"[snapshot] OK: all {len(EXPERT_DIRS)} baselines match "
            f"current sources."
        )
        return 0

    print(
        f"[snapshot] DRIFT: {len(drifts)} of {len(EXPERT_DIRS)} "
        f"baselines diverge from current sources:",
        file=sys.stderr,
    )
    for d in drifts:
        print(
            f"  - {d['expert_id']}: expected={d['expected']} "
            f"actual={d['actual']}",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
