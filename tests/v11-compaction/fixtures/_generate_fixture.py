"""Generate the 600_record_store.json fixture (deterministic, no real data).

Distribution per 55-01-PLAN.md Task 2:
  - 10 records: status=active, scope=global, confidence 0.85-0.95 (core-tier seed)
  - 100 records: status=active, scope=project, confidence 0.5-0.7, recent (working-tier)
  - 490 records: status=active, varied scope, confidence 0.3-0.5, older (archival-tier)

Every record carries the 10 mandated memory-record-schema.yaml fields:
  record_id, agent_id, scope, status, confidence, evidence_chain,
  created_at, persona_sha256, schema_version="1.0.0", content

Run from the repo root:
    python tests/v11-compaction/fixtures/_generate_fixture.py
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

AGENT_IDS = ["screenplay", "cinematographer", "colorist", "editor", "composer"]
PERSONAS = {
    "screenplay": "a" * 64,
    "cinematographer": "b" * 64,
    "colorist": "c" * 64,
    "editor": "d" * 64,
    "composer": "e" * 64,
}
SCHEMA_VERSION = "1.0.0"

# Anchor date — fixed so the fixture is reproducible across runs.
# Tests don't care about absolute dates, only relative recency.
ANCHOR_DATE = datetime(2026, 7, 1, tzinfo=timezone.utc)


def _make_record(
    *,
    record_id: str,
    agent_id: str,
    scope: str,
    status: str,
    confidence: float,
    evidence_chain: list[str],
    created_at: str,
    content: str,
    persona_sha256: str,
) -> dict:
    return {
        "record_id": record_id,
        "agent_id": agent_id,
        "scope": scope,
        "status": status,
        "confidence": confidence,
        "evidence_chain": evidence_chain,
        "created_at": created_at,
        "persona_sha256": persona_sha256,
        "schema_version": SCHEMA_VERSION,
        "content": content,
    }


def main() -> None:
    records: list[dict] = []

    # 10 core-tier seed records: global, high-confidence.
    for i in range(10):
        agent = AGENT_IDS[i % len(AGENT_IDS)]
        records.append(
            _make_record(
                record_id=str(uuid.uuid4()),
                agent_id=agent,
                scope="global",
                status="active",
                confidence=0.85 + (i % 11) * 0.01,  # 0.85..0.95
                evidence_chain=[f"ev_core_{i}_{j}" for j in range(3)],
                created_at=ANCHOR_DATE.isoformat(),
                content=f"Core-tier global fact #{i} for {agent}: stable project-wide convention.",
                persona_sha256=PERSONAS[agent],
            )
        )

    # 100 working-tier records: project scope, mid confidence, recent (within 30 days).
    for i in range(100):
        agent = AGENT_IDS[i % len(AGENT_IDS)]
        days_ago = (i % 30) + 1
        created = ANCHOR_DATE - timedelta(days=days_ago)
        records.append(
            _make_record(
                record_id=str(uuid.uuid4()),
                agent_id=agent,
                scope="project",
                status="active",
                confidence=0.50 + (i % 21) * 0.01,  # 0.50..0.70
                evidence_chain=[f"ev_work_{i}_{j}" for j in range(2)],
                created_at=created.isoformat(),
                content=f"Working-tier project note #{i} for {agent}: mid-confidence recent observation.",
                persona_sha256=PERSONAS[agent],
            )
        )

    # 490 archival-tier records: varied scope, lower confidence, older (60-180 days).
    for i in range(490):
        agent = AGENT_IDS[i % len(AGENT_IDS)]
        days_ago = 60 + (i % 121)  # 60..180
        created = ANCHOR_DATE - timedelta(days=days_ago)
        scope = "session" if (i % 3 == 0) else "project"
        records.append(
            _make_record(
                record_id=str(uuid.uuid4()),
                agent_id=agent,
                scope=scope,
                status="active",
                confidence=0.30 + (i % 21) * 0.01,  # 0.30..0.50
                evidence_chain=[f"ev_arch_{i}_{j}" for j in range(1)],
                created_at=created.isoformat(),
                content=f"Archival-tier {scope} observation #{i} for {agent}: low-confidence historical note.",
                persona_sha256=PERSONAS[agent],
            )
        )

    out_path = Path(__file__).resolve().parent / "600_record_store.json"
    out_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {len(records)} records to {out_path}")


if __name__ == "__main__":
    main()
