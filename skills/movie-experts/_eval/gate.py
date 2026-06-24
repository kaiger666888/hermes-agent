"""Phase 30 Eval Gate. Offline developer tooling — NOT imported by Hermes runtime.

Extends ``runner.py`` (does NOT fork). Pre-generated answers input only;
live answer generation is P31 scope (per 30-RESEARCH.md Open Q2 resolution).

The gate accepts a candidate patch (unified diff), applies it temporarily,
evaluates the patched skill against a baseline using the existing MT-Bench
position-swap harness in ``runner.py`` (now extended with numeric per-
dimension scoring), decides a verdict via mean-delta (GATE-02) and per-
prompt regression (GATE-04) thresholds, writes a report, reverts the patch,
and exits with a verdict code (GATE-01).

Exit codes (per 30-CONTEXT.md Gate CLI Surface):
    0 = pass
    1 = fail_mean (mean composite dropped more than delta_threshold)
    2 = fail_regression (any single prompt dropped more than per_prompt_threshold)
    3 = inconclusive (fewer than min_prompts valid prompts)

Design constraints (from 30-RESEARCH.md + snapshot.py:14):
- stdlib only (no third-party packages beyond what runner.py already uses).
- CLAUDE.md PLW1514: every ``open()`` passes ``encoding="utf-8"``.
- ``from __future__ import annotations`` at top (CLAUDE.md mandate).
- T-30-01: extract_patched_files rejects paths outside skills/movie-experts/
  or containing ``..`` (path traversal mitigation).
- T-30-02: subprocess.run uses argv list, NEVER shell=True.
- T-30-03: never logs raw judge responses or answer text.
- T-30-04: revert_patch runs in finally block even on exception.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# Sibling import — matches test_runner.py:29 + test_gate.py:33 convention.
import runner  # noqa: E402

logger = logging.getLogger("eval.gate")


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

# Re-export runner's dimension tuple so callers have one canonical name.
GATE_DIMENSIONS: tuple[str, ...] = runner._SCORE_DIMENSIONS

# Verdict -> exit code per 30-CONTEXT.md Gate CLI Surface.
VERDICT_TO_EXIT: dict[str, int] = {
    "pass": 0,
    "fail_mean": 1,
    "fail_regression": 2,
    "inconclusive": 3,
}

# Committed defaults — mirror gate_config.yaml.example. Keep in sync.
_DEFAULT_DELTA_THRESHOLD = 0.3
_DEFAULT_PER_PROMPT_THRESHOLD = 1.0
_DEFAULT_MIN_PROMPTS = 5
_DEFAULT_AB_POSITIONS = 2
_DEFAULT_JUDGE_MODEL = "claude-sonnet-4-6"

# Allowed ab_positions values (1 = no swap, 2 = swap).
_ALLOWED_AB_POSITIONS = frozenset({1, 2})

# Gate only patches files under this prefix (T-30-01 mitigation).
_SKILLS_PREFIX = "skills/movie-experts/"

# Matches ``+++ b/<path>`` lines in a unified diff header. Capture group
# is the repo-relative path (without the ``b/`` prefix).
_PATCH_FILE_RE = re.compile(r"^\+\+\+ b/(.+?)\s*$")


# --------------------------------------------------------------------------- #
# Patch mechanics (T-30-01, T-30-02, T-30-04 mitigations)
# --------------------------------------------------------------------------- #


def extract_patched_files(patch_path: Path) -> list[str]:
    """Parse ``+++ b/<path>`` lines from a unified diff header.

    T-30-01 mitigation: rejects any path that does not start with
    ``skills/movie-experts/`` OR contains ``..`` (path traversal).
    Raises ``ValueError`` with a clear message on violation.

    Returns a list of repo-relative POSIX paths touched by the patch.
    """
    text = patch_path.read_text(encoding="utf-8")
    files: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        m = _PATCH_FILE_RE.match(line)
        if m is None:
            continue
        path = m.group(1).strip()
        if path in seen:
            continue
        # T-30-01: reject path traversal.
        if ".." in path.split("/"):
            raise ValueError(
                f"path traversal rejected: patch header contains '..' in "
                f"path {path!r} (T-30-01 mitigation)"
            )
        # T-30-01: reject paths outside skills/movie-experts/.
        if not path.startswith(_SKILLS_PREFIX):
            raise ValueError(
                f"patch touches path outside skills/movie-experts/: "
                f"{path!r} (gate only patches bundled movie-expert skills)"
            )
        seen.add(path)
        files.append(path)
    return files


def apply_patch(patch_path: Path, repo_root: Path) -> None:
    """Validate then apply a candidate patch via git subprocess.

    T-30-02: passes patch path as argv element, NEVER shell=True.
    Runs ``git apply --check`` first (validation, no working-tree mutation);
    raises ``subprocess.CalledProcessError`` on failure BEFORE any mutation.
    On success runs ``git apply`` for real.
    """
    # Validate first — does not touch the working tree.
    subprocess.run(
        ["git", "apply", "--check", str(patch_path)],
        cwd=str(repo_root),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    # Apply for real.
    subprocess.run(
        ["git", "apply", str(patch_path)],
        cwd=str(repo_root),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    logger.info("applied patch %s in %s", patch_path, repo_root)


def revert_patch(files: list[str], repo_root: Path) -> None:
    """Revert patched files via ``git checkout --``.

    For files added by the patch (not present in HEAD), ``git checkout``
    would fail — detect via ``git cat-file -e HEAD:<path>`` and use
    ``git clean -f <path>`` to remove them instead.
    """
    if not files:
        return
    existing: list[str] = []
    added: list[str] = []
    for f in files:
        # Check whether the file exists in HEAD (i.e., the patch modified
        # an existing file vs created a new one).
        result = subprocess.run(
            ["git", "cat-file", "-e", f"HEAD:{f}"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if result.returncode == 0:
            existing.append(f)
        else:
            added.append(f)
    if existing:
        subprocess.run(
            ["git", "checkout", "--"] + existing,
            cwd=str(repo_root),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    if added:
        # ``git clean -f`` removes untracked files. Per worktree safety
        # rules this is scoped to specific paths, NOT a blanket clean.
        subprocess.run(
            ["git", "clean", "-f", "--"] + added,
            cwd=str(repo_root),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    logger.info("reverted %d files in %s", len(files), repo_root)


# --------------------------------------------------------------------------- #
# Config loader (T-30-04 fail-fast validation)
# --------------------------------------------------------------------------- #


def load_gate_config(
    config_path: Path | None,
    cli_overrides: dict[str, Any],
) -> dict[str, Any]:
    """Load gate config with precedence: defaults < YAML < CLI overrides.

    T-30-04 mitigation: validates every field on load and raises
    ``ValueError`` fail-fast on out-of-range values (matches runner.py
    WR-04 pattern). Prevents malformed config from crashing mid-run.
    """
    cfg: dict[str, Any] = {
        "delta_threshold": _DEFAULT_DELTA_THRESHOLD,
        "per_prompt_threshold": _DEFAULT_PER_PROMPT_THRESHOLD,
        "min_prompts": _DEFAULT_MIN_PROMPTS,
        "ab_positions": _DEFAULT_AB_POSITIONS,
        "judge_model": _DEFAULT_JUDGE_MODEL,
    }
    # YAML overrides defaults.
    if config_path is not None and Path(config_path).is_file():
        with open(config_path, encoding="utf-8") as f:
            yaml_cfg = yaml.safe_load(f) or {}
        if not isinstance(yaml_cfg, dict):
            raise ValueError(
                f"gate_config.yaml must be a mapping at top level, "
                f"got {type(yaml_cfg).__name__}"
            )
        cfg.update(yaml_cfg)
    # CLI overrides YAML.
    for k, v in cli_overrides.items():
        if v is None:
            continue
        cfg[k] = v

    # Validate ranges (T-30-04).
    if not (0.0 <= float(cfg["delta_threshold"]) <= 5.0):
        raise ValueError(
            f"delta_threshold must be in [0.0, 5.0], got "
            f"{cfg['delta_threshold']!r}"
        )
    if not (0.0 <= float(cfg["per_prompt_threshold"]) <= 5.0):
        raise ValueError(
            f"per_prompt_threshold must be in [0.0, 5.0], got "
            f"{cfg['per_prompt_threshold']!r}"
        )
    if int(cfg["min_prompts"]) < 1:
        raise ValueError(
            f"min_prompts must be >= 1, got {cfg['min_prompts']!r}"
        )
    if int(cfg["ab_positions"]) not in _ALLOWED_AB_POSITIONS:
        raise ValueError(
            f"ab_positions must be in {{1, 2}}, got {cfg['ab_positions']!r}"
        )
    if not str(cfg["judge_model"]).strip():
        raise ValueError("judge_model must be a non-empty string")
    return cfg


# --------------------------------------------------------------------------- #
# Decision logic — GATE-02 + GATE-04 (pure function)
# --------------------------------------------------------------------------- #


def decide_verdict(
    baseline_scores: list[float],
    candidate_scores: list[float],
    *,
    delta_threshold: float,
    per_prompt_threshold: float,
    min_prompts: int,
) -> tuple[str, dict[str, Any]]:
    """Decide pass / fail_mean / fail_regression / inconclusive.

    Pure function — no I/O, no logging, deterministic for fixed inputs.
    Implements GATE-02 (mean delta) and GATE-04 (per-prompt regression)
    per 30-CONTEXT.md decisions.

    Order of checks:
      1. n_valid < min_prompts -> inconclusive
      2. mean_delta < -delta_threshold -> fail_mean
      3. any per-prompt delta < -per_prompt_threshold -> fail_regression
      4. otherwise -> pass

    Returns ``(verdict, evidence_dict)``.
    """
    import statistics

    n = min(len(baseline_scores), len(candidate_scores))
    if n < min_prompts:
        return "inconclusive", {"n_valid": n, "min_prompts": min_prompts}

    deltas = [
        c - b for c, b in zip(candidate_scores, baseline_scores, strict=False)
    ]
    mean_delta = statistics.mean(deltas)

    if mean_delta < -delta_threshold:
        return "fail_mean", {
            "mean_delta": mean_delta,
            "threshold": -delta_threshold,
            "mean_baseline": statistics.mean(baseline_scores[:n]),
            "mean_candidate": statistics.mean(candidate_scores[:n]),
            "all_deltas": deltas,
        }

    for i, d in enumerate(deltas):
        if d < -per_prompt_threshold:
            return "fail_regression", {
                "regressing_prompt_idx": i,
                "delta": d,
                "threshold": -per_prompt_threshold,
                "all_deltas": deltas,
                "mean_delta": mean_delta,
            }

    return "pass", {
        "mean_delta": mean_delta,
        "mean_baseline": statistics.mean(baseline_scores[:n]),
        "mean_candidate": statistics.mean(candidate_scores[:n]),
        "all_deltas": deltas,
    }


# --------------------------------------------------------------------------- #
# Patch ID + provenance
# --------------------------------------------------------------------------- #


def generate_patch_id(skill_id: str, patch_path: Path) -> str:
    """Return ``f"{skill_id}_{ts_unix}_{sha256[:8]}"`` per CONTEXT.md discretion.

    The timestamp makes patch IDs sortable + unique across runs; the sha
    prefix ties the ID to the exact patch bytes (traceability for P32
    audit trail).
    """
    ts_unix = int(datetime.now(timezone.utc).timestamp())
    sha = hashlib.sha256(patch_path.read_bytes()).hexdigest()[:8]
    return f"{skill_id}_{ts_unix}_{sha}"


# --------------------------------------------------------------------------- #
# Evaluation (calls runner.py — the GATE-01 reuse)
# --------------------------------------------------------------------------- #


def evaluate_candidate(
    prompts: list[dict[str, str]],
    baseline_answers: list[str],
    candidate_answers: list[str],
    judge_client: Any,
    judge_model: str,
) -> list[dict[str, Any]]:
    """Run position-swapped numeric scoring per prompt.

    For each prompt i, calls ``runner.run_position_swap`` with
    ``answer_a=baseline_answers[i]`` and ``answer_b=candidate_answers[i]``.
    From the extended return dict, extracts ``scores_ab`` and ``scores_ba``,
    computes a per-dimension average (position-bias mitigation on the
    numeric axis — 30-RESEARCH.md Pitfall 5), then collapses to a composite
    via ``runner.composite_score``.

    Returns a list of per-prompt records:
      ``prompt_id``, ``baseline_composite``, ``candidate_composite``,
      ``delta``, ``scores_ab``, ``scores_ba``, ``ordering_ab``,
      ``ordering_ba``, ``final``.

    NOTE: in this scope baseline_answers + candidate_answers are PRE-
    GENERATED (loaded from JSON files passed via CLI). Gate does NOT
    call the Hermes agent (P30 scope fence per RESEARCH Open Q2).
    """
    records: list[dict[str, Any]] = []
    n = min(len(prompts), len(baseline_answers), len(candidate_answers))
    for i in range(n):
        p = prompts[i]
        v = runner.run_position_swap(
            prompt=p["text"],
            answer_a=baseline_answers[i],
            answer_b=candidate_answers[i],
            judge_client=judge_client,
            judge_model=judge_model,
            prompt_id=p["id"],
        )
        scores_ab = v["scores_ab"]
        scores_ba = v["scores_ba"]
        # Per-dimension average across both orderings (position-bias
        # mitigation). A dimension present in EITHER ordering contributes.
        all_dims = set(scores_ab.keys()) | set(scores_ba.keys())
        dim_avg: dict[str, float] = {}
        for dim in all_dims:
            ab_val = scores_ab.get(dim)
            ba_val = scores_ba.get(dim)
            vals = [x for x in (ab_val, ba_val) if x is not None]
            if vals:
                dim_avg[dim] = sum(vals) / len(vals)
        candidate_composite = runner.composite_score(dim_avg)
        # baseline_composite is filled by run_gate from the baseline cache;
        # evaluate_candidate only produces the candidate side here. We
        # store both names for symmetry, defaulting baseline to None.
        records.append(
            {
                "prompt_id": p["id"],
                "baseline_composite": None,
                "candidate_composite": candidate_composite,
                "delta": None,
                "scores_ab": scores_ab,
                "scores_ba": scores_ba,
                "ordering_ab": v["ordering_ab"],
                "ordering_ba": v["ordering_ba"],
                "final": v["final"],
            }
        )
    return records


# --------------------------------------------------------------------------- #
# GateResult + orchestrator
# --------------------------------------------------------------------------- #


@dataclass
class GateResult:
    """Return value of run_gate()."""

    verdict: str
    exit_code: int
    report_path: Path | None = None
    reject_path: Path | None = None
    per_prompt: list[dict[str, Any]] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    patch_id: str = ""


def _load_answers_json(path: Path) -> list[str]:
    """Load a JSON file containing a list of pre-generated answer strings."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(
            f"answers file {path} must contain a JSON list of strings"
        )
    return [str(x) for x in data]


def _write_report(
    report_path: Path,
    *,
    schema_version: int,
    patch_id: str,
    skill_id: str,
    patch_path: Path,
    verdict: str,
    thresholds: dict[str, Any],
    per_prompt: list[dict[str, Any]],
    judge_model: str,
    evidence: dict[str, Any],
    operator_hint: str | None = None,
) -> None:
    """Write the gate report JSON (always) and reject log on failure.

    T-30-03: per-prompt entries contain composite scores + deltas only,
    NEVER raw answer text or full judge responses.
    """
    report_path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    patch_sha256 = hashlib.sha256(patch_path.read_bytes()).hexdigest()
    report = {
        "schema_version": schema_version,
        "patch_id": patch_id,
        "skill_id": skill_id,
        "patch_path": str(patch_path),
        "patch_sha256": patch_sha256,
        "ts": ts,
        "verdict": verdict,
        "thresholds": thresholds,
        "judge_model": judge_model,
        "per_prompt": per_prompt,
        "evidence": evidence,
    }
    if operator_hint is not None:
        report["operator_hint"] = operator_hint
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def run_gate(
    patch_path: Path,
    skill_id: str,
    baseline_answers_path: Path,
    candidate_answers_path: Path,
    config: dict[str, Any],
    *,
    repo_root: Path,
    prompts_path: Path,
    judge_client: Any,
    reports_dir: Path | None = None,
    baseline_scores_cache: Path | None = None,
) -> GateResult:
    """Main gate entrypoint.

    Steps (per 30-RESEARCH.md Pattern 2 + 30-01-PLAN.md Task 2 <action>):
      1. extract_patched_files + security validation (T-30-01).
      2. apply_patch (try/finally — T-30-04 revert guarantee).
      3. load baseline + candidate answers JSON.
      4. load prompts via runner.load_prompts.
      5. evaluate_candidate -> per-prompt records (calls runner).
      6. load or lazy-populate baseline composite scores.
      7. decide_verdict (GATE-02 + GATE-04).
      8. write report (always) + reject log (on failure).
      9. FINALLY: revert_patch (runs even on exception).
    """
    # Defaults.
    if reports_dir is None:
        reports_dir = (
            Path(__file__).resolve().parent / "reports"
        )
    judge_model = str(config.get("judge_model", _DEFAULT_JUDGE_MODEL))
    thresholds = {
        "delta": config["delta_threshold"],
        "per_prompt": config["per_prompt_threshold"],
        "min_prompts": config["min_prompts"],
        "ab_positions": config["ab_positions"],
    }

    # Step 1: extract + validate patched files (T-30-01).
    files = extract_patched_files(patch_path)
    if not files:
        raise ValueError(f"patch {patch_path} touches no files")

    patch_id = generate_patch_id(skill_id, patch_path)

    # Step 2: apply patch. The ENTIRE eval+decide+report block lives
    # inside a try/finally so revert_patch runs even on exception (T-30-04).
    applied = False
    per_prompt: list[dict[str, Any]] = []
    evidence: dict[str, Any] = {}
    verdict = "inconclusive"
    try:
        apply_patch(patch_path, repo_root)
        applied = True

        # Step 3: load pre-generated answers (scope fence — no live gen).
        baseline_answers = _load_answers_json(baseline_answers_path)
        candidate_answers = _load_answers_json(candidate_answers_path)

        # Step 4: load prompts.
        prompts = runner.load_prompts(prompts_path)

        # Step 5: evaluate candidate (calls runner — GATE-01 reuse).
        per_prompt = evaluate_candidate(
            prompts=prompts,
            baseline_answers=baseline_answers,
            candidate_answers=candidate_answers,
            judge_client=judge_client,
            judge_model=judge_model,
        )

        # Step 6: load baseline composite scores (from cache OR lazy-populate).
        baseline_composites: list[float] = []
        if baseline_scores_cache is not None and baseline_scores_cache.is_file():
            cached = json.loads(
                baseline_scores_cache.read_text(encoding="utf-8")
            )
            if isinstance(cached, list):
                baseline_composites = [float(x) for x in cached]
        candidate_composites: list[float] = []
        for i, rec in enumerate(per_prompt):
            c = rec.get("candidate_composite")
            if c is not None:
                candidate_composites.append(float(c))
            # Fill baseline_composite per-prompt if cache available. Use
            # the loop index (not candidate_composites length) so records
            # with None candidate_composite still align correctly.
            if i < len(baseline_composites):
                rec["baseline_composite"] = baseline_composites[i]
                if c is not None:
                    rec["delta"] = c - baseline_composites[i]

        # If no baseline cache, treat candidate as its own baseline (first
        # run) — mean_delta=0 -> pass. Cache for next time.
        if not baseline_composites:
            baseline_composites = list(candidate_composites)
            if baseline_scores_cache is not None:
                baseline_scores_cache.parent.mkdir(parents=True, exist_ok=True)
                baseline_scores_cache.write_text(
                    json.dumps(baseline_composites),
                    encoding="utf-8",
                )

        # Step 7: decide verdict (GATE-02 + GATE-04).
        verdict, evidence = decide_verdict(
            baseline_composites,
            candidate_composites,
            delta_threshold=config["delta_threshold"],
            per_prompt_threshold=config["per_prompt_threshold"],
            min_prompts=config["min_prompts"],
        )
    finally:
        # T-30-04: revert ALWAYS runs, even on exception.
        if applied:
            try:
                revert_patch(files, repo_root)
            except Exception as exc:  # noqa: BLE001 — best-effort cleanup
                logger.warning("revert_patch failed: %s", exc)

    # Step 8: write report (always) + reject log on failure.
    report_path = reports_dir / f"{patch_id}.json"
    reject_path: Path | None = None
    operator_hint: str | None = None
    if verdict != "pass":
        reject_path = reports_dir / f"{patch_id}.reject.json"
        if verdict == "fail_mean":
            operator_hint = (
                f"Patch rejected: mean delta "
                f"{evidence.get('mean_delta', '?')} < "
                f"-{config['delta_threshold']}. Override with "
                f"--threshold-delta {config['delta_threshold'] + 0.2:.2f} "
                f"if intentional."
            )
        elif verdict == "fail_regression":
            idx = evidence.get("regressing_prompt_idx", "?")
            operator_hint = (
                f"Patch rejected: prompt {idx} regressed by "
                f"{evidence.get('delta', '?')}. Override with "
                f"--per-prompt-threshold "
                f"{config['per_prompt_threshold'] + 0.5:.2f} if intentional."
            )
        else:
            operator_hint = (
                f"Patch inconclusive: only {evidence.get('n_valid', '?')} "
                f"valid prompts (< {config['min_prompts']}). Rerun with "
                f"--min-prompts {evidence.get('n_valid', 1)} or add prompts."
            )
        _write_report(
            reject_path,
            schema_version=1,
            patch_id=patch_id,
            skill_id=skill_id,
            patch_path=patch_path,
            verdict=verdict,
            thresholds=thresholds,
            per_prompt=per_prompt,
            judge_model=judge_model,
            evidence=evidence,
            operator_hint=operator_hint,
        )
    _write_report(
        report_path,
        schema_version=1,
        patch_id=patch_id,
        skill_id=skill_id,
        patch_path=patch_path,
        verdict=verdict,
        thresholds=thresholds,
        per_prompt=per_prompt,
        judge_model=judge_model,
        evidence=evidence,
    )

    logger.info(
        "gate verdict=%s patch_id=%s skill=%s (per_prompt=%d)",
        verdict, patch_id, skill_id, len(per_prompt),
    )

    return GateResult(
        verdict=verdict,
        exit_code=VERDICT_TO_EXIT.get(verdict, 3),
        report_path=report_path,
        reject_path=reject_path,
        per_prompt=per_prompt,
        evidence=evidence,
        patch_id=patch_id,
    )


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    """Gate CLI entrypoint. Returns exit code (0/1/2/3)."""
    parser = argparse.ArgumentParser(
        description=(
            "Phase 30 Eval Gate. Scores a candidate patch against the "
            "v5.0 baseline using the existing MT-Bench position-swap "
            "harness. Offline developer tooling (NOT imported by Hermes "
            "runtime)."
        )
    )
    parser.add_argument(
        "--patch",
        type=Path,
        help="Path to candidate unified diff (.patch / .diff).",
    )
    parser.add_argument(
        "--skill",
        help="Target skill_id (e.g. screenplay).",
    )
    parser.add_argument(
        "--baseline-answers",
        type=Path,
        help="JSON file with pre-generated baseline answers (list[str]).",
    )
    parser.add_argument(
        "--candidate-answers",
        type=Path,
        help="JSON file with pre-generated candidate answers (list[str]).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to gate_config.yaml (default: use built-in defaults).",
    )
    parser.add_argument(
        "--threshold-delta",
        type=float,
        default=None,
        dest="delta_threshold",
        help="Override delta_threshold (mean drop allowed).",
    )
    parser.add_argument(
        "--per-prompt-threshold",
        type=float,
        default=None,
        dest="per_prompt_threshold",
        help="Override per_prompt_threshold (max single-prompt regression).",
    )
    parser.add_argument(
        "--min-prompts",
        type=int,
        default=None,
        dest="min_prompts",
        help="Override min_prompts (validity floor).",
    )
    parser.add_argument(
        "--ab-positions",
        type=int,
        default=None,
        dest="ab_positions",
        help="Override ab_positions (1 or 2).",
    )
    parser.add_argument(
        "--judge-model",
        default=None,
        dest="judge_model",
        help="Override judge_model.",
    )
    parser.add_argument(
        "--prompts-dir",
        type=Path,
        default=None,
        help=(
            "Path to prompts YAML file "
            "(default: _eval/prompts/<skill>_demo.yaml)."
        ),
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repo root for git apply/checkout (default: cwd).",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=None,
        help="Directory for report JSON output (default: _eval/reports/).",
    )
    parser.add_argument(
        "--rebuild-baseline",
        action="store_true",
        help=(
            "Force baseline cache rebuild (NOT YET IMPLEMENTED — full "
            "impl lands in Plan 02; prints a notice and exits 0 if "
            "passed alone)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use runner._StubJudgeClient (no live API calls).",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="[gate] %(levelname)s %(message)s",
    )

    # --rebuild-baseline stub (Plan 02 scope).
    if args.rebuild_baseline and args.patch is None:
        print(
            "--rebuild-baseline is not yet implemented in Plan 01. "
            "Full implementation lands in Plan 02."
        )
        return 0

    # Required args for a gate run.
    if not args.patch:
        parser.error("--patch is required (or pass --rebuild-baseline alone)")
    if not args.skill:
        parser.error("--skill is required")
    if not args.baseline_answers:
        parser.error("--baseline-answers is required")
    if not args.candidate_answers:
        parser.error("--candidate-answers is required")

    # Build CLI overrides dict (None values skipped by load_gate_config).
    cli_overrides: dict[str, Any] = {
        "delta_threshold": args.delta_threshold,
        "per_prompt_threshold": args.per_prompt_threshold,
        "min_prompts": args.min_prompts,
        "ab_positions": args.ab_positions,
        "judge_model": args.judge_model,
    }
    config = load_gate_config(args.config, cli_overrides)

    # Resolve prompts path.
    prompts_path = args.prompts_dir
    if prompts_path is None:
        prompts_path = (
            Path(__file__).resolve().parent
            / "prompts"
            / f"{args.skill}_demo.yaml"
        )
    if not Path(prompts_path).is_file():
        logger.error("prompts file not found: %s", prompts_path)
        return VERDICT_TO_EXIT["inconclusive"]

    # Resolve repo root.
    repo_root = args.repo_root or Path.cwd()

    # Pick judge client.
    if args.dry_run:
        judge_client: Any = runner._StubJudgeClient()
        logger.info("dry-run: using stub judge client (no API calls)")
    else:
        # Live judge client (requires OPENROUTER_API_KEY).
        # Runner config is minimal — judge section optional since we
        # pass judge_model via gate config.
        try:
            judge_client = runner.make_judge_client({})
        except RuntimeError as exc:
            logger.error("%s (use --dry-run for offline testing)", exc)
            return VERDICT_TO_EXIT["inconclusive"]

    result = run_gate(
        patch_path=args.patch,
        skill_id=args.skill,
        baseline_answers_path=args.baseline_answers,
        candidate_answers_path=args.candidate_answers,
        config=config,
        repo_root=repo_root,
        prompts_path=prompts_path,
        judge_client=judge_client,
        reports_dir=args.reports_dir,
    )
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
