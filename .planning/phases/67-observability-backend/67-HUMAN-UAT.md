---
status: partial
phase: 67-observability-backend
source: [67-VERIFICATION.md]
started: 2026-07-08T14:30:00Z
updated: 2026-07-08T14:30:00Z
---

## Current Test

[awaiting human testing — deferred per /gsd-autonomous Continue decision 2026-07-08]

## Tests

### 1. Live dashboard curl smoke (operator-confidence only, NON-BLOCKING)

**expected:** `curl /orchestrator/agents/status` against live `hermes dashboard` returns 200 with `agents_loaded==21` and real expert names in `agent_names` list.

**why manual:** Requires starting the dashboard server (long-running process); CI uses FastAPI TestClient which validates routing + auth + JSON shape but not real bind + middleware chain + live runtime data fill.

**why non-blocking:** TestClient integration tests (5) cover routing, auth gate, response shape, registry-failure graceful degrade. Live curl is operator-confidence validation that the full server stack works end-to-end.

**test command:**
```bash
hermes dashboard --port 8765 &
DASH_PID=$!
sleep 2  # wait for server bind
TOKEN=$(hermes dashboard token 2>/dev/null || echo "test-token")
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8765/orchestrator/agents/status | jq .
kill $DASH_PID
```

**expected output:**
```json
{
  "agent_registry": {
    "agents_loaded": 21,
    "agent_names": ["animation_studio", "audio_pipeline", ...],
    "schema_validation_ok": true,
    "missing_experts": [],
    "lineage_integrity_ok": true,
    "last_updated": "2026-07-08T..."
  },
  "round_table": {...},
  "memory_backend": {...},
  "snapshot_at": "2026-07-08T..."
}
```

**result:** [pending]

---

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps

[none — automated verification fully satisfies OBSRV-01 + OBSRV-02 + OBSRV-03 SCs]
