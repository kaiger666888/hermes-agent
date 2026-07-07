"""Shared fixtures for EVAL-04 compaction pass tests (55-01).

Mirrors the patterns established in tests/v11-bias-canary/conftest.py:
  - session-scoped ``fixtures_dir`` resolves the fixtures/ directory.
  - ``hermes_home_tmp`` (autouse) creates a per-test HERMES_HOME under tmp,
    isolated from the real ``~/.hermes`` (per CLAUDE.md live-system-guard).
  - ``mock_mem0_backend`` provides an in-memory dict-backed mem0 client with
    ``add`` / ``search`` / ``get_all`` / ``update`` methods, scoped per agent_id.
    Pre-seeded from the 600-record fixture on demand.
  - ``mock_claim_check_llm`` is an async callable returning a canned summary
    JSON so tests never hit real GLM (operator-action-handoff pattern).
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Directory of compaction-fixture JSON files."""
    return FIXTURES_DIR


@pytest.fixture(autouse=True)
def hermes_home_tmp(tmp_path, monkeypatch) -> Path:
    """Per-test HERMES_HOME under pytest's tmp_path.

    Redirects ``get_hermes_home()`` so curator_audit.append_audit and any
    other HERMES_HOME-resolved path lands in the temp dir, not the real
    ``~/.hermes``. Mirrors the conftest pattern from tests/v11-bias-canary.
    """
    home = tmp_path / "hermes_home"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HERMES_HOME", str(home))
    return home


@pytest.fixture()
def fixture_600_records(fixtures_dir: Path) -> list[dict[str, Any]]:
    """Load the 600-record synthetic memory store fixture."""
    path = fixtures_dir / "600_record_store.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list), f"fixture must be a list, got {type(data).__name__}"
    assert len(data) == 600, f"fixture must have 600 records, got {len(data)}"
    return data


class _InMemoryMem0Backend:
    """Minimal in-memory mem0 backend for compaction tests.

    Implements the subset of methods that ``agent.memory_compaction`` and
    ``agent.memory_arbitration`` need: ``add``, ``search``, ``get_all``,
    ``update``. Records are stored in a list (preserving insertion order)
    and keyed by ``record_id`` for O(1) update.

    This is a TEST DOUBLE — never wired into production. Production goes
    through ``_get_mem0_backend()`` which resolves to the real mem0 plugin.
    """

    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []
        self._index: dict[str, dict[str, Any]] = {}
        # Call log — tests assert on which methods were invoked.
        self.calls: list[tuple[str, tuple, dict]] = []

    def add(
        self,
        *,
        content: str,
        agent_id: str,
        scope: str = "global",
        confidence: float = 0.5,
        **kwargs: Any,
    ) -> str:
        record_id = kwargs.get("record_id") or str(uuid.uuid4())
        record: dict[str, Any] = {
            "record_id": record_id,
            "agent_id": agent_id,
            "scope": scope,
            "status": kwargs.get("status", "active"),
            "confidence": confidence,
            "evidence_chain": kwargs.get("evidence_chain", []),
            "created_at": kwargs.get("created_at"),
            "persona_sha256": kwargs.get("persona_sha256"),
            "schema_version": kwargs.get("schema_version", "1.0.0"),
            "content": content,
        }
        # Optional fields passed through.
        for k in ("source_record_ids", "project_id", "session_id"):
            if k in kwargs:
                record[k] = kwargs[k]
        self._records.append(record)
        self._index[record_id] = record
        self.calls.append(("add", (), {"agent_id": agent_id, "record_id": record_id}))
        return record_id

    def get_all(self, *, agent_id: str | None = None, **kwargs: Any) -> list[dict[str, Any]]:
        self.calls.append(("get_all", (), {"agent_id": agent_id}))
        if agent_id is None:
            return list(self._records)
        return [r for r in self._records if r.get("agent_id") == agent_id]

    def search(
        self,
        *,
        query: str | None = None,
        agent_id: str | None = None,
        top_k: int = 5,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        self.calls.append(("search", (), {"agent_id": agent_id, "top_k": top_k}))
        pool = self.get_all(agent_id=agent_id) if agent_id else list(self._records)
        # Sort by confidence desc then recency — good enough for tests; real
        # mem0 does vector similarity which we deliberately don't emulate.
        pool.sort(key=lambda r: (r.get("confidence", 0.0), r.get("created_at") or ""), reverse=True)
        return pool[:top_k]

    def update(self, *, record_id: str, **fields: Any) -> bool:
        self.calls.append(("update", (), {"record_id": record_id, **fields}))
        record = self._index.get(record_id)
        if record is None:
            return False
        record.update(fields)
        return True

    def count(self, *, agent_id: str | None = None) -> int:
        if agent_id is None:
            return len(self._records)
        return sum(1 for r in self._records if r.get("agent_id") == agent_id)

    def seed_from(self, records: list[dict[str, Any]]) -> None:
        """Bulk-load records (preserving their record_id and fields)."""
        for r in records:
            # Defensive copy so test mutations don't leak back into the fixture.
            r_copy = dict(r)
            self._records.append(r_copy)
            self._index[r_copy["record_id"]] = r_copy


@pytest.fixture()
def mock_mem0_backend():
    """In-memory mem0 backend double. Seed with ``.seed_from(records)``."""
    return _InMemoryMem0Backend()


@pytest.fixture()
def mock_claim_check_llm():
    """Async callable returning a canned summary JSON.

    Injected via ``compact_memory(..., claim_check_llm=mock_claim_check_llm)``
    so tests do not hit real GLM (CLAUDE.md operator-action-handoff pattern).
    Tracks call count + last-seen messages so tests can assert dispatch.
    """

    async def _llm(*, messages: list, **kwargs: Any) -> dict[str, Any]:
        _llm.call_count += 1
        _llm.last_messages = messages
        _llm.last_kwargs = kwargs
        return {
            "content": "Consolidated memory: 100 working-tier records merged. "
                       "Distinct facts: agent preferences for cinematic conventions, "
                       "scene-blocking notes, color-palette decisions.",
            "confidence": 0.55,
        }

    _llm.call_count = 0
    _llm.last_messages: list | None = None
    _llm.last_kwargs: dict | None = None
    return _llm
