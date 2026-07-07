"""Generate the 600_record_store.json fixture (deterministic, no real data).

Distribution per 55-01-PLAN.md Task 2:
  - 10 records: status=active, scope=global, confidence 0.85-0.95 (core-tier seed)
  - 100 records: status=active, scope=project, confidence 0.5-0.7, recent (working-tier)
  - 490 records: status=active, varied scope, confidence 0.3-0.5, older (archival-tier)

All 600 records belong to ``agent_id="screenplay"`` because compaction
operates PER-AGENT (per ``05-POC-PLAN.md §4.4`` "per-agent memory budget
cap"). The §4.4 acceptance check compacts at exactly the screenplay
namespace; spreading records across 5 agents would leave each under the
500-record threshold and the compaction would never trigger. The "varied
agent_id" suggestion in 55-01-PLAN.md Task 2 is superseded by the
SC#1 contract which compacts one agent namespace against a 600-record
total.

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

# All records belong to the screenplay agent namespace (compaction is
# per-agent per §4.4 — see module docstring for rationale).
AGENT_ID = "screenplay"
PERSONA_SHA256 = "a" * 64
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
        records.append(
            _make_record(
                record_id=str(uuid.uuid4()),
                agent_id=AGENT_ID,
                scope="global",
                status="active",
                confidence=0.85 + (i % 11) * 0.01,  # 0.85..0.95
                evidence_chain=[f"ev_core_{i}_{j}" for j in range(3)],
                created_at=ANCHOR_DATE.isoformat(),
                content=f"Core-tier global fact #{i} for {AGENT_ID}: stable project-wide convention.",
                persona_sha256=PERSONA_SHA256,
            )
        )

    # 100 working-tier records: project scope, mid confidence, recent (within 30 days).
    for i in range(100):
        days_ago = (i % 30) + 1
        created = ANCHOR_DATE - timedelta(days=days_ago)
        records.append(
            _make_record(
                record_id=str(uuid.uuid4()),
                agent_id=AGENT_ID,
                scope="project",
                status="active",
                confidence=0.50 + (i % 21) * 0.01,  # 0.50..0.70
                evidence_chain=[f"ev_work_{i}_{j}" for j in range(2)],
                created_at=created.isoformat(),
                content=f"Working-tier project note #{i} for {AGENT_ID}: mid-confidence recent observation.",
                persona_sha256=PERSONA_SHA256,
            )
        )

    # 490 archival-tier records: varied scope, lower confidence, older (60-180 days).
    for i in range(490):
        days_ago = 60 + (i % 121)  # 60..180
        created = ANCHOR_DATE - timedelta(days=days_ago)
        scope = "session" if (i % 3 == 0) else "project"
        records.append(
            _make_record(
                record_id=str(uuid.uuid4()),
                agent_id=AGENT_ID,
                scope=scope,
                status="active",
                confidence=0.30 + (i % 21) * 0.01,  # 0.30..0.50
                evidence_chain=[f"ev_arch_{i}_{j}" for j in range(1)],
                created_at=created.isoformat(),
                content=f"Archival-tier {scope} observation #{i} for {AGENT_ID}: low-confidence historical note.",
                persona_sha256=PERSONA_SHA256,
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
