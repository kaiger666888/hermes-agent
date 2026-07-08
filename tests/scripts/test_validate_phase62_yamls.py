"""Tests for ``scripts/validate_phase62_yamls.py`` (Phase 62 Wave 0 infra).

Plan 62-01 acceptance criteria:
  - ``--help`` exits 0
  - no-arg run validates all ``*.agent.yaml`` under ``$HERMES_HOME/agents``
  - ``--batch A`` / ``--batch B`` validate the 6-name constants from the plan
  - missing files surface as ``MISSING {name}: {path}`` and exit 1
  - schema failures surface as ``FAIL {name}: {json_path}: {msg}`` and exit 1
  - passes print ``PASS {name}`` per file + ``OK: {N}/{N}`` summary, exit 0
  - always uses ``yaml.safe_load`` (never bare ``yaml.load``)

Test strategy:
  - Functional unit tests import the module directly and exercise
    ``load_schema`` + ``validate_one`` against fixture YAMLs written into
    the autouse ``HERMES_HOME`` tmpdir (set by conftest
    ``_hermetic_environment``).
  - One subprocess test pins the CLI ``--help`` contract end-to-end.

The subprocess test must NOT inherit the conftest HERMES_HOME redirect
(subprocess env is captured separately), and the no-arg-runs-against-
9-shipped-YAMLs smoke is deferred to the Plan's own <verify> block
(operator-visible; the script lives in the repo and is run by the
executor). The unit tests below cover behaviors 2-8 against fixtures so
they pass independent of how many YAMLs the operator has shipped.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

# Import the script as a module (scripts/ is a package on sys.path via
# the root conftest; scripts/ has no __init__.py but pytest's rootdir
# insertion makes `import scripts.X` work — mirrors
# test_build_skills_index_health.py pattern).
import scripts.validate_phase62_yamls as v62


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture
def agents_dir(tmp_path, monkeypatch):
    """A HERMES_HOME/agents directory the test can populate.

    Relies on conftest's autouse ``_hermetic_environment`` to set
    HERMES_HOME to ``tmp_path / "hermes_test"``. We expose the agents
    subdir and ensure it exists.
    """
    import hermes_constants

    hermes_home = hermes_constants.get_hermes_home()
    agents = hermes_home / "agents"
    agents.mkdir(parents=True, exist_ok=True)
    # Sanity: confirm HERMES_HOME redirect is in effect (defensive — if a
    # future conftest change stops redirecting we want to fail loud here,
    # not silently write to the real ~/.hermes/agents/).
    assert str(hermes_home) != str(Path.home() / ".hermes"), (
        "HERMES_HOME not redirected — test would pollute real ~/.hermes/"
    )
    return agents


_VALID_AGENT_YAML = """\
name: {name}
description: A minimal valid agent for Phase 62 validator tests.
version: 1.0.0
persona: |
  I am {name}. I do test work.
tools:
  - hermes_llm
memory_scope: per_agent
lineage:
  derived_from_skill_id: {name}
  derived_from_repo: kais-hermes-skills
  transform_date: 2026-07-08
  transform_notes: test fixture
  skill_sha256: {sha}
"""


def _write_valid(agents_dir: Path, name: str) -> Path:
    """Write a schema-valid ``{name}.agent.yaml`` and return its path."""
    import hashlib

    sha = hashlib.sha256(f"src-{name}".encode("utf-8")).hexdigest()
    path = agents_dir / f"{name}.agent.yaml"
    path.write_text(_VALID_AGENT_YAML.format(name=name, sha=sha), encoding="utf-8")
    return path


def _write_invalid_extra_field(agents_dir: Path, name: str) -> Path:
    """Write an agent YAML with an undeclared top-level field (must fail
    ``additionalProperties: false`` at the root)."""
    import hashlib

    sha = hashlib.sha256(f"src-{name}".encode("utf-8")).hexdigest()
    body = _VALID_AGENT_YAML.format(name=name, sha=sha) + textwrap.dedent(
        """
        undeclared_field_should_fail: true
        """
    )
    path = agents_dir / f"{name}.agent.yaml"
    path.write_text(body, encoding="utf-8")
    return path


# ──────────────────────────────────────────────────────────────────────
# Behavior 1: --help exits 0 (subprocess — exercises the real CLI entry)
# ──────────────────────────────────────────────────────────────────────


def test_help_exits_0_subprocess():
    """``python3 scripts/validate_phase62_yamls.py --help`` exits 0.

    Plan behavior 1. Subprocess invocation proves the shebang + argparse
    wiring work end-to-end (not just importable as a module).
    """
    repo_root = Path(__file__).resolve().parents[2]
    proc = subprocess.run(
        [sys.executable, "scripts/validate_phase62_yamls.py", "--help"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"stderr: {proc.stderr}\nstdout: {proc.stdout}"
    assert "--batch" in proc.stdout


# ──────────────────────────────────────────────────────────────────────
# Behavior 8 / acceptance: load_schema uses yaml.safe_load + correct schema
# ──────────────────────────────────────────────────────────────────────


def test_load_schema_returns_dict_with_required_key():
    """``load_schema()`` returns the parsed agents-schema.yaml dict."""
    schema = v62.load_schema()
    assert isinstance(schema, dict)
    # Draft 2020-12 markers
    assert schema.get("type") == "object"
    assert "required" in schema
    assert "additionalProperties" in schema


def test_batch_constants_match_plan():
    """The two batch constants must contain exactly the 6 names each that
    Plan 62-01 specifies."""
    assert sorted(v62.BATCH_A) == sorted([
        "animation_studio", "colorist", "compliance_gate",
        "creative_source", "documentary_maker", "performer",
    ])
    assert sorted(v62.BATCH_B) == sorted([
        "production", "prompt_injector", "scene_builder",
        "script_auditor", "storyboard_designer", "visual_executor",
    ])


# ──────────────────────────────────────────────────────────────────────
# Behavior 5: missing file → (False, "MISSING {name}: {path}")
# ──────────────────────────────────────────────────────────────────────


def test_validate_one_missing_file_returns_missing_message(agents_dir):
    schema = v62.load_schema()
    ok, msg = v62.validate_one("colorist", schema)
    assert ok is False
    assert msg.startswith("MISSING colorist:")
    # Path cited must point under HERMES_HOME/agents
    assert str(agents_dir) in msg


# ──────────────────────────────────────────────────────────────────────
# Behavior 6: schema failure → (False, "FAIL {name}: {path}: {msg}")
# ──────────────────────────────────────────────────────────────────────


def test_validate_one_schema_failure_returns_fail_message(agents_dir):
    _write_invalid_extra_field(agents_dir, "bad_agent")
    schema = v62.load_schema()
    ok, msg = v62.validate_one("bad_agent", schema)
    assert ok is False
    assert msg.startswith("FAIL bad_agent:"), f"got: {msg}"
    # Additional-properties violations surface a specific json path
    # (jsonschema reports undeclared property by name).
    assert ":" in msg[len("FAIL bad_agent:"):]


def test_validate_one_missing_required_field_returns_fail_message(agents_dir):
    """A YAML missing a required field (e.g. ``memory_scope``) must FAIL."""
    body = textwrap.dedent("""\
        name: missingreq
        description: A test agent missing required memory_scope.
        version: 1.0.0
        persona: |
          I am missingreq.
        tools:
          - hermes_llm
        lineage:
          derived_from_skill_id: missingreq
          derived_from_repo: kais-hermes-skills
          transform_date: 2026-07-08
          skill_sha256: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    """)
    (agents_dir / "missingreq.agent.yaml").write_text(body, encoding="utf-8")
    schema = v62.load_schema()
    ok, msg = v62.validate_one("missingreq", schema)
    assert ok is False
    assert msg.startswith("FAIL missingreq:")


# ──────────────────────────────────────────────────────────────────────
# Behavior 7: valid YAML → (True, "PASS {name}")
# ──────────────────────────────────────────────────────────────────────


def test_validate_one_valid_yaml_returns_pass(agents_dir):
    _write_valid(agents_dir, "good_agent")
    schema = v62.load_schema()
    ok, msg = v62.validate_one("good_agent", schema)
    assert ok is True
    assert msg == "PASS good_agent"


# ──────────────────────────────────────────────────────────────────────
# Behavior 2/3/4 + acceptance: main() wiring with --batch and no-batch
# ──────────────────────────────────────────────────────────────────────


def test_main_no_batch_validates_glob_and_reports_ok(agents_dir, capsys, monkeypatch):
    """No ``--batch`` → glob ``*.agent.yaml`` under agents dir; print
    per-file PASS + summary ``OK: {N}/{N}``; exit 0."""
    # Populate 2 valid agents. We don't assert count == 9 (that's the
    # operator-visible smoke from <verify>; here we just need glob wiring).
    _write_valid(agents_dir, "alpha")
    _write_valid(agents_dir, "beta")
    rc = v62.main([])
    out = capsys.readouterr().out
    assert rc == 0, f"exit={rc}, out={out}"
    assert "PASS alpha" in out
    assert "PASS beta" in out
    assert "OK: 2/2" in out


def test_main_batch_a_missing_exits_1_with_missing_message(agents_dir, capsys):
    """``--batch A`` against 0 YAMLs exits 1 with MISSING for all 6 names."""
    rc = v62.main(["--batch", "A"])
    out = capsys.readouterr().out
    assert rc == 1, f"exit={rc}, out={out}"
    for name in v62.BATCH_A:
        assert f"MISSING {name}:" in out
    assert "FAILED" in out


def test_main_batch_a_all_valid_exits_0(agents_dir, capsys):
    """``--batch A`` with all 6 valid YAMLs exits 0 with OK summary."""
    for name in v62.BATCH_A:
        _write_valid(agents_dir, name)
    rc = v62.main(["--batch", "A"])
    out = capsys.readouterr().out
    assert rc == 0, f"exit={rc}, out={out}"
    assert "OK: 6/6" in out
    for name in v62.BATCH_A:
        assert f"PASS {name}" in out


def test_main_batch_b_partial_failure_exits_1(agents_dir, capsys):
    """``--batch B`` with 5 valid + 1 schema-fail exits 1; the 5 passes
    are still reported."""
    for name in v62.BATCH_B[:5]:
        _write_valid(agents_dir, name)
    _write_invalid_extra_field(agents_dir, v62.BATCH_B[5])
    rc = v62.main(["--batch", "B"])
    out = capsys.readouterr().out
    assert rc == 1, f"exit={rc}, out={out}"
    assert f"FAIL {v62.BATCH_B[5]}:" in out
    assert "FAILED" in out


# ──────────────────────────────────────────────────────────────────────
# T-62-01 mitigation: yaml.safe_load only, never yaml.load
# ──────────────────────────────────────────────────────────────────────


def test_no_yaml_load_in_source():
    """Source must contain zero ``yaml.load(`` calls outside comments.

    Plan acceptance criterion. Mirrors T-62-01 mitigation: yaml.load can
    deserialize arbitrary Python objects (tag injection). yaml.safe_load
    refuses them.
    """
    src_path = Path(v62.__file__)
    src = src_path.read_text(encoding="utf-8")
    # Strip full-line comments and trailing comments before checking.
    violations = []
    for lineno, line in enumerate(src.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        # Strip inline comment (best-effort; doesn't handle '#' inside
        # strings, but yaml.load( is the only '#' we care about here).
        code = line.split("#", 1)[0]
        if "yaml.load(" in code:
            violations.append((lineno, line))
    assert not violations, f"forbidden yaml.load( found: {violations}"


def test_draft202012_validator_used():
    """Source must reference Draft202012Validator (not legacy validate())."""
    src = Path(v62.__file__).read_text(encoding="utf-8")
    assert "Draft202012Validator" in src


def test_safe_load_called_at_least_twice():
    """``yaml.safe_load`` must appear at least twice (schema + per-yaml)."""
    src = Path(v62.__file__).read_text(encoding="utf-8")
    assert src.count("yaml.safe_load") >= 2
