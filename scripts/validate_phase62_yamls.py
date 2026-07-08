#!/usr/bin/env python3
"""Phase 62 Wave 0 batch validator for agent YAML files.

Implements SC#2 (byte-pass ``jsonschema.Draft202012Validator.validate()``)
as a standalone CLI so Plans 02 / 03 / 04 can cite a single command
(``python3 scripts/validate_phase62_yamls.py --batch {A|B}`` or no-flag
for the full sweep) in their acceptance criteria.

The validator loads ``.planning/research/v10-orchestrator-design/agents-schema.yaml``
(the v10.0 18-field Draft 2020-12 schema) and validates every
``$HERMES_HOME/agents/*.agent.yaml`` against it. Mirrors the canonical
pattern in ``agent/registry_loader.py`` (``_load_schema`` + sorted
``iter_errors`` for deterministic error ordering) but as a CLI surface
so Wave 1 transform tasks become single-command verifiable.

Threat mitigations:
  - T-62-01 (YAML tag injection): uses ``yaml.safe_load`` exclusively —
    refuses arbitrary Python object tags (mirrors registry_loader.py:227).
  - T-62-02 (undeclared field injection): ``Draft202012Validator`` enforces
    ``additionalProperties: false`` at the top level + Lineage $def.
  - T-62-03/04 (path traversal, info disclosure): accepted — hardcoded
    repo-relative SCHEMA_PATH; jsonschema error messages contain no
    secrets.
  - T-62-SC (supply chain): zero new package installs — PyYAML + jsonschema
    both pre-existing in pyproject.toml core deps.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
import jsonschema
from jsonschema import Draft202012Validator

from hermes_constants import get_hermes_home

# ──────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────

# Repo-relative path to the v10.0 18-field Draft 2020-12 schema.
# Resolved relative to the current working directory (executor runs from
# repo root). See .planning/research/v10-orchestrator-design/agents-schema.yaml
SCHEMA_PATH = Path(".planning/research/v10-orchestrator-design/agents-schema.yaml")

# Agent YAML directory. Resolved dynamically via get_hermes_home() at
# each call (NOT cached at module import) — the HERMES_HOME env var can
# be redirected per-test by conftest's _hermetic_environment fixture, and
# caching at import time would leak state across tests. Mirrors the
# registry_loader.py:305 resolve-on-use pattern.
def _agents_dir() -> Path:
    """Resolve the agents dir from the current HERMES_HOME.

    Uses ``get_hermes_home()`` (NOT ``Path.home() / ".hermes"``) per
    CLAUDE.md Anti-Patterns rule.
    """
    return get_hermes_home() / "agents"

# Wave 1 batch constants — locked by Plan 62-02 / 62-03 acceptance criteria.
# Order is preserved as authored (alphabetical within each batch for
# determinism in error output).
BATCH_A = [
    "animation_studio",
    "colorist",
    "compliance_gate",
    "creative_source",
    "documentary_maker",
    "performer",
]
BATCH_B = [
    "production",
    "prompt_injector",
    "scene_builder",
    "script_auditor",
    "storyboard_designer",
    "visual_executor",
]


# ──────────────────────────────────────────────────────────────────────
# Schema loader
# ──────────────────────────────────────────────────────────────────────


def load_schema() -> dict:
    """Load and parse agents-schema.yaml.

    Uses ``yaml.safe_load`` (never ``yaml.load``) — T-62-01 tag-injection
    mitigation. Encoding explicit per CLAUDE.md PLW1514 (Windows default
    cp1252 silently corrupts non-ASCII content).

    Raises:
        FileNotFoundError: if the schema file is missing.
        yaml.YAMLError: if the schema file has invalid YAML syntax.
    """
    content = SCHEMA_PATH.read_text(encoding="utf-8")
    return yaml.safe_load(content)


# ──────────────────────────────────────────────────────────────────────
# Per-file validator
# ──────────────────────────────────────────────────────────────────────


def validate_one(name: str, schema: dict) -> tuple[bool, str]:
    """Validate a single agent YAML against ``schema``.

    Args:
        name: agent name (filename stem, without ``.agent.yaml``).
        schema: parsed Draft 2020-12 schema dict (from ``load_schema()``).

    Returns:
        ``(ok, message)`` tuple. ``message`` is one of:
          - ``"MISSING {name}: {path}"``  — file does not exist
          - ``"FAIL {name}: {json_path}: {first_error_message}"`` — schema
            violation (first error in sorted-by-path order, mirroring
            ``registry_loader.py`` lines 246-257)
          - ``"PASS {name}"``  — file is schema-valid

    Notes:
        - Uses ``Draft202012Validator.iter_errors()`` to surface ALL
          errors per file (sorted by JSON path for deterministic output).
          Mirrors ``registry_loader.py:246`` — do NOT replace with the
          single-shot ``jsonschema.validate()`` which raises on first error.
        - Uses ``yaml.safe_load`` (T-62-01 mitigation).
    """
    path = _agents_dir() / f"{name}.agent.yaml"
    if not path.exists():
        return (False, f"MISSING {name}: {path}")

    doc = yaml.safe_load(path.read_text(encoding="utf-8"))

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path))
    if errors:
        first = errors[0]
        json_path = ".".join(str(p) for p in first.absolute_path) or "$"
        return (False, f"FAIL {name}: {json_path}: {first.message}")

    return (True, f"PASS {name}")


# ──────────────────────────────────────────────────────────────────────
# CLI entry
# ──────────────────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validate_phase62_yamls.py",
        description=(
            "Phase 62 Wave 0 validator. Validates ~/.hermes/agents/*.agent.yaml "
            "against the v10.0 agents-schema.yaml (Draft 2020-12)."
        ),
    )
    parser.add_argument(
        "--batch",
        choices=("A", "B"),
        default=None,
        help=(
            "Validate only the named batch. A = 6 Wave-1-A names "
            "(animation_studio, colorist, compliance_gate, creative_source, "
            "documentary_maker, performer). B = 6 Wave-1-B names "
            "(production, prompt_injector, scene_builder, script_auditor, "
            "storyboard_designer, visual_executor). If omitted, validates "
            "every *.agent.yaml found under $HERMES_HOME/agents/."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry. Returns process exit code (0 = all pass, 1 = any fail).

    Args:
        argv: optional argv list (defaults to ``sys.argv[1:]``).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    schema = load_schema()

    if args.batch == "A":
        targets = list(BATCH_A)
    elif args.batch == "B":
        targets = list(BATCH_B)
    else:
        # No --batch: glob the agents directory (do NOT hardcode 21).
        # At Wave 0 execution time only 9 exist; the script must work
        # against current state. sorted() for deterministic output.
        agents_dir = _agents_dir()
        if agents_dir.is_dir():
            targets = sorted(
                p.stem.removesuffix(".agent")
                for p in agents_dir.glob("*.agent.yaml")
            )
            # ``stem`` of "foo.agent.yaml" is "foo.agent"; strip the
            # trailing ".agent" to recover the agent name.
        else:
            targets = []

    total = len(targets)
    pass_n = 0
    fail_n = 0
    for name in targets:
        ok, msg = validate_one(name, schema)
        print(msg)
        if ok:
            pass_n += 1
        else:
            fail_n += 1

    if fail_n == 0:
        print(f"OK: {pass_n}/{total}")
        return 0
    print(f"FAILED: {fail_n}/{total}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
