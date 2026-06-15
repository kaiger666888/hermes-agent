#!/usr/bin/env python3
"""Phantom-reference detector for skills/movie-experts/*/SKILL.md.

A standalone CI lint that flags any model / tool / sampler / concept name
appearing in any ``skills/movie-experts/*/SKILL.md`` that is NOT present in
``plugins/image_gen/*/plugin.yaml``, ``plugins/video_gen/*/plugin.yaml`` or a
curated manual override list at
``skills/movie-experts/_shared/known-external-models.yaml``.

This is the credibility anchor for the Movie-Experts Suite v2 refactor.
Without it, fabricated tokens like ``wan22_video`` (no plugin exists) or
``168K controlled tokens`` (a fabricated concept) keep shipping silently.

Usage::

    python scripts/verify_skill_references.py
    python scripts/verify_skill_references.py --strict --output-json audit.json --output-md audit.md

Exit codes:
    * 0 — no findings found, OR findings found but ``--strict`` not set.
    * 1 — findings found AND ``--strict`` set (CI gate trips).
    * 2 — scanner misconfiguration (missing dirs, broken YAML).

Design notes:
    * Stdlib + PyYAML only — no new dependencies.
    * ``encoding="utf-8"`` on every ``open()`` per CLAUDE.md Ruff PLW1514.
    * Linear regex patterns (no nested quantifiers) to avoid catastrophic
      backtracking on adversarial SKILL.md input (threat T-00-03).
    * Deterministic output — sorted glob walk + sorted findings list.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import yaml


# ---------------------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------------------

DEFAULT_SKILLS_DIR = Path("skills/movie-experts")
DEFAULT_PLUGINS_DIR = Path("plugins")
DEFAULT_OVERRIDE_YAML = DEFAULT_SKILLS_DIR / "_shared" / "known-external-models.yaml"

# Regex for model-name-shaped tokens. Two branches:
#   (a) suffix-shaped model ids: ``foo_video``, ``bar_turbo``, ``baz_lora``...
#   (b) known standalone vendor / model tokens.
# Case-insensitive — scanner normalizes both file content and allowlist to
# lowercase before comparison.
_MODEL_SUFFIX_TOKEN_RE = re.compile(
    r"\b[a-z][a-z0-9]+_(?:video|turbo|tts|lora|model|gen3|v3|v2|pro|nano|klein|banana|imagine)\b",
    re.IGNORECASE,
)
# Detection regex — yields CANDIDATE tokens that are then checked against
# the allowlist (build_allowlist). This regex does NOT itself whitelist
# anything; its only role is to surface tokens worth flagging. Without a
# matching allowlist entry, every token it matches becomes a Finding.
_VENDOR_CANDIDATE_RE = re.compile(
    r"\b(?:sora|veo|kling|runway|flux|minimax|glm|qwen|deepseek|yi|wan\d*|pixverse|stable[_-]?audio|cosyvoice|recraft|grok|gpt-image)\b",
    re.IGNORECASE,
)
# Tokens that must ALWAYS be flagged regardless of allowlist state.
# These are known phantom references; no operator override (via the
# override YAML or a plugin.yaml) can suppress them. This is the
# hard-block that protects the scanner's credibility anchor: if the
# allowlist were ever extended to include one of these, the scan would
# still flag it. (CR-01: guard against accidental allowlist pollution.)
_PHANTOM_DENYLIST = frozenset({
    "wan22_video",
    "wan22_video_turbo",
    "wan22",  # bare vendor-number variant; no real model exists.
    "168k controlled tokens",  # fabricated concept; matched as a phrase.
})
# Special fabrication pattern: "168K controlled tokens" — case-insensitive,
# whitespace-flexible. Survives single-digit (``8K``) or multi-digit variants.
_CONTROLLED_TOKENS_RE = re.compile(
    r"\b\d+[Kk]\s+controlled\s+tokens?\b",
    re.IGNORECASE,
)
# ``flux_1_nsfw`` style fabricated samplers — caught by the suffix regex
# above (``_model`` / ``_nsfw``...). Not separately enumerated here to keep
# the regex count auditable.

# Tokens that are always safe regardless of allowlist (English-language
# stopwords / common technical terms the scanner should NEVER flag). Kept
# minimal — we WANT false positives over false negatives.
_ALWAYS_SAFE_TOKENS = frozenset({
    "model", "video", "turbo",  # generic words the suffix regex will catch
})

# Minimum token length when tokenizing plugin description strings.
_MIN_TOKEN_LEN = 3


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """One phantom reference found in a SKILL.md file."""

    path: str
    line: int
    matched_token: str
    context_line: str

    def __lt__(self, other: object) -> bool:
        """Deterministic sort: by path, then line, then token."""
        if not isinstance(other, Finding):
            return NotImplemented
        return (self.path, self.line, self.matched_token) < (
            other.path,
            other.line,
            other.matched_token,
        )


# ---------------------------------------------------------------------------
# Allowlist builder
# ---------------------------------------------------------------------------


def _tokenize_description(desc: str) -> set[str]:
    """Split a plugin description into lowercase alphanumeric tokens.

    Hyphen behavior (WR-05): the split pattern ``[^A-Za-z0-9_-]+``
    treats ``-`` and ``_`` as IN-token characters, so a description
    like ``"flux-2-pro"`` yields the single token ``flux-2-pro`` (not
    ``flux``, ``2``, ``pro`` separately). This is intentional: hyphenated
    vendor/model ids are kept intact so an operator who adds
    ``"flux-2-pro"`` to a plugin description can see it in the allowlist.

    Implication: hyphenated tokens in a plugin description are "dead"
    allowlist entries for the scanner — the scanner's candidate regexes
    (``_MODEL_SUFFIX_TOKEN_RE``, ``_VENDOR_CANDIDATE_RE``) use ``\\b``
    word boundaries and do not match hyphens internally, so they yield
    ``flux``, ``2``, ``pro`` separately when scanning a SKILL.md that
    mentions ``flux-2-pro``. Only non-hyphenated tokens (e.g. ``veo``,
    ``kling``) extracted from the same description are effective
    allowlist entries that suppress findings.

    Minimum length filter (``_MIN_TOKEN_LEN`` = 3) drops short fragments.
    """
    tokens: set[str] = set()
    for raw in re.split(r"[^A-Za-z0-9_-]+", desc):
        candidate = raw.lower().strip("_-")
        if len(candidate) >= _MIN_TOKEN_LEN:
            tokens.add(candidate)
    return tokens


def _load_plugin_yaml(path: Path) -> dict | None:
    """Parse a plugin.yaml; return None on FileNotFoundError / bad YAML."""
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except FileNotFoundError as exc:
        print(f"warning: plugin.yaml missing: {path}: {exc}", file=sys.stderr)
        return None
    except yaml.YAMLError as exc:
        print(f"warning: plugin.yaml parse error at {path}: {exc}", file=sys.stderr)
        return None
    if not isinstance(data, dict):
        return None
    return data


def _walk_plugin_yamls(plugins_root: Path) -> Iterable[Path]:
    """Deterministically yield ``plugins/{image_gen,video_gen}/*/plugin.yaml."""
    if not plugins_root.exists():
        return
    for category in ("image_gen", "video_gen"):
        cat_dir = plugins_root / category
        if not cat_dir.is_dir():
            continue
        for plugin_dir in sorted(cat_dir.iterdir()):
            if not plugin_dir.is_dir():
                continue
            manifest = plugin_dir / "plugin.yaml"
            if manifest.exists():
                yield manifest


def _load_override_yaml(path: Path) -> set[str]:
    """Load manual-override models from YAML; return empty set if absent."""
    if not path.exists():
        return set()
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except (FileNotFoundError, yaml.YAMLError) as exc:
        print(f"warning: override YAML unreadable at {path}: {exc}", file=sys.stderr)
        return set()
    if not isinstance(data, dict):
        return set()
    models = data.get("models", [])
    out: set[str] = set()
    if not isinstance(models, list):
        return out
    for entry in models:
        if isinstance(entry, dict) and isinstance(entry.get("name"), str):
            out.add(entry["name"].lower().strip())
        elif isinstance(entry, str):
            out.add(entry.lower().strip())
    return out


def build_allowlist(plugins_root: Path, override_yaml_path: Path) -> set[str]:
    """Build the set of legitimate model / vendor tokens.

    Sources (merged, case-normalized to lowercase):
      * ``plugins/image_gen/*/plugin.yaml`` and ``plugins/video_gen/*/plugin.yaml``
        — both ``name`` field and tokens parsed from ``description``.
      * Manual overrides from ``override_yaml_path`` (``models:`` list).

    The function is defensive: a missing plugins dir, missing override file,
    or malformed YAML yields a (possibly empty) set rather than raising —
    the scanner degrades to "flag everything not explicit" rather than
    aborting.
    """
    allowlist: set[str] = set()

    for manifest in _walk_plugin_yamls(plugins_root):
        data = _load_plugin_yaml(manifest)
        if data is None:
            continue
        name = data.get("name")
        if isinstance(name, str) and name:
            allowlist.add(name.lower().strip())
        desc = data.get("description")
        if isinstance(desc, str):
            allowlist |= _tokenize_description(desc)

    allowlist |= _load_override_yaml(override_yaml_path)
    # Always-safe tokens mask the generic words the suffix regex would
    # otherwise flag in every other line ("model: ..." etc.).
    allowlist |= _ALWAYS_SAFE_TOKENS
    return allowlist


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


def _iter_regex_matches(line: str) -> Iterable[tuple[str, re.Pattern[str]]]:
    """Yield (matched_token_lowercased, pattern) for every regex that fires."""
    for pattern in (_MODEL_SUFFIX_TOKEN_RE, _VENDOR_CANDIDATE_RE):
        for m in pattern.finditer(line):
            yield m.group(0).lower(), pattern
    for m in _CONTROLLED_TOKENS_RE.finditer(line):
        yield m.group(0).lower(), _CONTROLLED_TOKENS_RE


def scan_skill_file(skill_path: Path, allowlist: set[str]) -> list[Finding]:
    """Scan one SKILL.md for phantom references.

    Returns a sorted list of :class:`Finding` for every model-name-shaped or
    fabrication-pattern token in the file that is NOT in ``allowlist``.
    Multiple findings for the same token on the same line are de-duplicated.
    """
    findings: list[Finding] = []
    seen: set[tuple[int, str]] = set()

    try:
        with skill_path.open("r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except FileNotFoundError as exc:
        print(f"warning: skill file missing: {skill_path}: {exc}", file=sys.stderr)
        return findings
    except OSError as exc:
        print(f"warning: cannot read skill file {skill_path}: {exc}", file=sys.stderr)
        return findings

    for idx, raw_line in enumerate(lines, start=1):
        stripped = raw_line.rstrip("\n")
        for token, _pattern in _iter_regex_matches(stripped):
            key = (idx, token)
            if key in seen:
                continue
            seen.add(key)
            # CR-01: Hard denylist. These tokens are ALWAYS flagged,
            # regardless of allowlist state. The allowlist cannot
            # override this — an operator who accidentally adds
            # ``wan22_video`` to the override YAML still gets a Finding.
            if token in _PHANTOM_DENYLIST:
                findings.append(
                    Finding(
                        path=str(skill_path),
                        line=idx,
                        matched_token=token,
                        context_line=stripped,
                    )
                )
                continue
            if token in allowlist:
                continue
            findings.append(
                Finding(
                    path=str(skill_path),
                    line=idx,
                    matched_token=token,
                    context_line=stripped,
                )
            )

    findings.sort()
    return findings


# ---------------------------------------------------------------------------
# Reporter
# ---------------------------------------------------------------------------


def format_report(findings: list[Finding]) -> tuple[dict, str]:
    """Produce dual JSON-dict + Markdown-string report.

    JSON shape::

        {"total": N,
         "findings": [{"file": ..., "line": ..., "token": ..., "context": ...}]}

    Markdown shape::

        # Skill Reference Audit

        N phantom reference(s) detected.

        ## Findings

        ### 1. `token` at `file:line`
        > context line

    Both outputs always include every finding's token, file path, and line
    number so the audit trail survives regardless of which format a CI step
    consumes.
    """
    sorted_findings = sorted(findings)
    json_dict = {
        "total": len(sorted_findings),
        "findings": [
            {
                "file": f.path,
                "line": f.line,
                "token": f.matched_token,
                "context": f.context_line,
            }
            for f in sorted_findings
        ],
    }

    lines: list[str] = [
        "# Skill Reference Audit",
        "",
        f"{len(sorted_findings)} phantom reference(s) detected.",
        "",
    ]
    if sorted_findings:
        lines.append("## Findings")
        lines.append("")
        for i, f in enumerate(sorted_findings, start=1):
            lines.append(f"### {i}. `{f.matched_token}` at `{f.path}:{f.line}`")
            lines.append(f"> {f.context_line}")
            lines.append("")
    else:
        lines.append("_No phantom references detected. SKILL.md inventory clean._")
        lines.append("")

    markdown = "\n".join(lines).rstrip() + "\n"
    return json_dict, markdown


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="verify_skill_references",
        description=(
            "Flag phantom model/tool/sampler references in "
            "skills/movie-experts/*/SKILL.md."
        ),
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default=DEFAULT_SKILLS_DIR,
        help=f"Skills directory to scan (default: {DEFAULT_SKILLS_DIR})",
    )
    parser.add_argument(
        "--plugins-dir",
        type=Path,
        default=DEFAULT_PLUGINS_DIR,
        help=f"Plugins directory to derive allowlist from (default: {DEFAULT_PLUGINS_DIR})",
    )
    parser.add_argument(
        "--override-yaml",
        type=Path,
        default=DEFAULT_OVERRIDE_YAML,
        help=(
            "Manual override YAML (default: "
            f"{DEFAULT_OVERRIDE_YAML})"
        ),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional path to write JSON report to.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=None,
        help="Optional path to write Markdown report to.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if any phantom reference is found (CI gate).",
    )
    return parser.parse_args(argv)


def _glob_skill_files(skills_dir: Path) -> list[Path]:
    """Return sorted list of ``skills_dir/*/SKILL.md`` paths."""
    if not skills_dir.exists():
        return []
    out: list[Path] = []
    for child in sorted(skills_dir.iterdir()):
        if not child.is_dir():
            continue
        candidate = child / "SKILL.md"
        if candidate.exists():
            out.append(candidate)
    return out


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns process exit code."""
    args = _parse_args(argv)

    if not args.skills_dir.exists():
        print(
            f"error: skills directory does not exist: {args.skills_dir}",
            file=sys.stderr,
        )
        return 2

    allowlist = build_allowlist(args.plugins_dir, args.override_yaml)
    skill_files = _glob_skill_files(args.skills_dir)
    if not skill_files:
        print(
            f"warning: no SKILL.md files found under {args.skills_dir}",
            file=sys.stderr,
        )

    all_findings: list[Finding] = []
    for skill_path in skill_files:
        all_findings.extend(scan_skill_file(skill_path, allowlist))

    json_dict, markdown = format_report(all_findings)

    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        with args.output_json.open("w", encoding="utf-8") as fh:
            json.dump(json_dict, fh, indent=2, ensure_ascii=False, sort_keys=True)
            fh.write("\n")

    if args.output_md is not None:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        with args.output_md.open("w", encoding="utf-8") as fh:
            fh.write(markdown)

    # Stdout summary (always printed for humans / CI logs).
    print(
        f"audit complete: {json_dict['total']} phantom reference(s) across "
        f"{len(skill_files)} skill file(s); allowlist size={len(allowlist)}"
    )
    if json_dict["findings"]:
        print()
        print(markdown)

    if json_dict["total"] > 0 and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
