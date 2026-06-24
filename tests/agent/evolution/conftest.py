"""Shared fixtures for the agent/evolution/ test subpackage.

Fixtures:
  - ``evolution_env``: isolated HERMES_HOME + tmp git repo with a staged
    sample SKILL.md, so apply/FOUND-08 checks have a real file + git
    state to work against.
  - ``mock_llm_client``: stub OpenAI-shaped client whose
    ``chat.completions.create`` returns canned content loaded from a
    fixture file (mirrors runner.py:561 _StubJudgeClient pattern).
  - ``mock_store``: stub FeedbackStore exposing ``query`` + ``summary``.
  - ``sample_feedback_records``: list of FeedbackRecord-shaped dicts.
  - ``sample_skill_content``: text of sample_skill_md.md fixture.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "evolution"


# --------------------------------------------------------------------------- #
# Path constants used by multiple test files
# --------------------------------------------------------------------------- #

SAMPLE_SKILL_MD = FIXTURES_DIR / "sample_skill_md.md"
SAMPLE_INSIGHTS_JSON = FIXTURES_DIR / "sample_insights.json"
ADDITIVE_DIFF = FIXTURES_DIR / "additive.diff"
VIOLATING_DELETION_DIFF = FIXTURES_DIR / "violating_deletion.diff"
VIOLATING_FRONTMATTER_DIFF = FIXTURES_DIR / "violating_frontmatter_diffusion.diff"

SKILL_REL_PATH = "skills/movie-experts/test_skill/SKILL.md"


# --------------------------------------------------------------------------- #
# evolution_env — HERMES_HOME + git repo + staged sample SKILL.md
# --------------------------------------------------------------------------- #


@pytest.fixture
def evolution_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Isolated HERMES_HOME + git repo with a committed sample SKILL.md.

    Returns a dict with:
      - ``hermes_home``: the isolated ~/.hermes root (Path)
      - ``evolution_dir``: <hermes_home>/skills/.feedback/evolution/ (Path)
      - ``repo_root``: the git repo root containing skills/movie-experts/test_skill/SKILL.md
      - ``skill_path``: repo-relative POSIX path of the staged SKILL.md
    """
    hermes_home = tmp_path / "hermes-home"
    evolution_dir = hermes_home / "skills" / ".feedback" / "evolution"
    evolution_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    repo_root = tmp_path / "repo"
    skill_dir = repo_root / "skills" / "movie-experts" / "test_skill"
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        SAMPLE_SKILL_MD.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    # Initialize git repo with REPO-LOCAL author identity (Pitfall 7).
    subprocess.run(
        ["git", "init", "-q"], cwd=str(repo_root), check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@evolution.local"],
        cwd=str(repo_root), check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Evolution Test"],
        cwd=str(repo_root), check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "add", "."], cwd=str(repo_root), check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "init"],
        cwd=str(repo_root), check=True, capture_output=True,
    )

    return {
        "hermes_home": hermes_home,
        "evolution_dir": evolution_dir,
        "repo_root": repo_root,
        "skill_path": SKILL_REL_PATH,
        "skill_abs_path": skill_file,
    }


# --------------------------------------------------------------------------- #
# mock_llm_client — stub OpenAI-shaped client
# --------------------------------------------------------------------------- #


class _MockCompletions:
    """Stub for OpenAI ``chat.completions`` returning canned content."""

    def __init__(self, content: str) -> None:
        self._content = content
        self.last_kwargs: dict[str, Any] = {}
        self.call_count: int = 0

    def create(self, **kwargs: Any) -> Any:
        self.call_count += 1
        self.last_kwargs = kwargs
        outer = self

        class _Choice:
            class _Message:
                content = outer._content

            message = _Message()

        class _Resp:
            choices = [_Choice()]

        return _Resp()


class _MockChat:
    def __init__(self, content: str) -> None:
        self.completions = _MockCompletions(content)


class MockLLMClient:
    """OpenAI-shaped stub. Set ``content`` to the canned response text."""

    def __init__(self, content: str) -> None:
        self.chat = _MockChat(content)


@pytest.fixture
def mock_llm_client() -> Any:
    """Return a factory that builds MockLLMClient with given canned content.

    Usage: ``client = mock_llm_client('{"insights": [...]}')``
    """
    return MockLLMClient


@pytest.fixture
def mock_llm_client_with_insights() -> MockLLMClient:
    """Pre-built stub returning the sample_insights.json payload."""
    payload = SAMPLE_INSIGHTS_JSON.read_text(encoding="utf-8")
    return MockLLMClient(payload)


# --------------------------------------------------------------------------- #
# mock_store — stub FeedbackStore
# --------------------------------------------------------------------------- #


class MockStore:
    """Stub for agent.feedback_store.FeedbackStore."""

    def __init__(self, records: list[dict], summary: dict[str, Any] | None = None) -> None:
        self._records = records
        self._summary = summary or {
            "total": len(records),
            "by_verdict": {"negative": sum(1 for r in records if r.get("verdict") == "negative")},
        }

    def query(self, *, skill_id: str | None = None, **_: Any) -> list[dict]:
        if skill_id is None:
            return list(self._records)
        return [r for r in self._records if r.get("skill_id") == skill_id]

    def summary(self, *, skill_id: str | None = None) -> dict[str, Any]:
        return dict(self._summary)


@pytest.fixture
def sample_feedback_records() -> list[dict]:
    """Canned FeedbackRecord-shaped dicts for LLM prompt input."""
    return [
        {
            "record_id": "fb_001",
            "skill_id": "test_skill",
            "expert_id": "test_skill",
            "source": "cli",
            "verdict": "negative",
            "correction": "Missing SCAMPER worked examples — hard to apply.",
            "output_snapshot": {"sha256": "abc123"},
            "ts": "2026-06-22T10:00:00Z",
        },
        {
            "record_id": "fb_002",
            "skill_id": "test_skill",
            "expert_id": "test_skill",
            "source": "kais_aigc",
            "verdict": "negative",
            "correction": "No concrete SCAMPER substitution example in the output.",
            "output_snapshot": {"sha256": "def456"},
            "ts": "2026-06-23T11:00:00Z",
        },
        {
            "record_id": "fb_003",
            "skill_id": "test_skill",
            "expert_id": "test_skill",
            "source": "manual",
            "verdict": "negative",
            "correction": "Trigger conditions unclear vs sibling skill.",
            "output_snapshot": {"sha256": "ghi789"},
            "ts": "2026-06-24T09:00:00Z",
        },
    ]


@pytest.fixture
def mock_store(sample_feedback_records: list[dict]) -> MockStore:
    """Pre-built MockStore with the canned feedback records."""
    return MockStore(sample_feedback_records)


@pytest.fixture
def empty_mock_store() -> MockStore:
    """MockStore with zero records — for empty-feedback tests."""
    return MockStore(records=[], summary={"total": 0, "by_verdict": {}})


@pytest.fixture
def sample_skill_content() -> str:
    """Text content of the sample_skill_md.md fixture."""
    return SAMPLE_SKILL_MD.read_text(encoding="utf-8")


@pytest.fixture
def sample_insights_payload() -> dict:
    """Parsed sample_insights.json — the expected LLM response shape."""
    return json.loads(SAMPLE_INSIGHTS_JSON.read_text(encoding="utf-8"))
