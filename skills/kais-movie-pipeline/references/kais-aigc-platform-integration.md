# kais-aigc-platform Integration — Service Topology + Canvas Type Mapping

**Created:** 2026-06-27 (canvas_sync node type fix session)
**Last-verified:** 2026-06-27

---

## Service Topology

| Port | Process | Role | Status |
|------|---------|------|--------|
| **10588** | kais-aigc-platform Node.js (`tsx src/app.ts`) | **Current** — canvas v2 API + Asset Registry + infinite-canvas | ✅ Live |
| **8000** | Docker container `kais-core-backend` | **Legacy** — old Toonflow instance, still running | ⚠️ Should be decommissioned |
| **8002** | gold-team | GPU task scheduler (RTX 3090) | ✅ Live |
| **5173** | Vite dev server | Infinite canvas frontend (React Flow) | ✅ Live (dev) |

**Key:** Python pipeline talks to **10588** via `KAIS_CANVAS_URL` env var. The legacy `agent-sync.js` was hardcoded to 8000 — fixed to read `KAIS_CANVAS_URL` (commit `48f3ae3` in kais-aigc-platform).

## Canvas API v2 Endpoints (on 10588)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/canvas/v2/save-v2` | POST | Save FlowGraph (`{projectId, episodesId, graph}`) |
| `/api/canvas/v2/load-v2` | POST | Load FlowGraph (`{projectId, episodesId}`) |
| `/api/v1/assets-registry` | POST | Register asset (type/name required) |
| `/health` | GET | Health check |

## React Flow Node Types (FlowCanvas.tsx)

The canvas frontend registers 7 node types for visual rendering:

| `type` | Component | Render |
|--------|-----------|--------|
| `script` | ScriptNodeComponent | Text content, score, review status |
| `asset` | AssetNodeComponent | Images (character/scene/prop) |
| `storyboard` | StoryboardNodeComponent | Shot frames, duration |
| `video` | VideoNodeComponent | Video player, preview |
| `audio` | AudioNodeComponent | Audio waveform, playback |
| `zone` | ZoneNodeComponent | Grouping zone |
| `default` | FallbackNodeComponent | Unknown types |

## Phase → Node Type Mapping (_PHASE_TYPE_MAP)

Fixed in `canvas_sync.py` (commit `8dd613749` in hermes-agent). Previously all nodes were hardcoded `type: "script"`.

| Phase | Canvas `type` | `data.assetType` | Rationale |
|-------|---------------|-------------------|-----------|
| p01 hook_topic | `script` | `topic` | Text content |
| p02 outline | `script` | `outline` | Text content |
| p03 script_audit | `script` | `script_phase` | Text content |
| p04 character_design | `asset` | `character` | Character images |
| p05 pain_discovery | `script` | `script_phase` | Research text |
| p06 spatio_temporal | `script` | `script_phase` | Complex text |
| p07 scene_generation | `asset` | `scene` | Scene images |
| p08 scene_selection | `asset` | `scene` | Scene images |
| p09 shot_breakdown | `storyboard` | `storyboard` | E-Konte 5-layer |
| p10 voice | `audio` | `voice` | Audio clips |
| p10b rapid_preview | `video` | `clip` | Preview clips |
| p11 video_render | `video` | `video` | Final video |
| p12 composition | `video` | `clip` | Master mix |
| p13 delivery | `script` | `delivery` | Delivery report |

## Asset Registry Types

POST `/api/v1/assets-registry` accepts these `type` values:

```
character | scene | prop | clip | voice | video | storyboard | script_phase | outline | topic | delivery
```

## Integration Chain

```
Python pipeline (14 phases)
  ├─ canvas_sync.py → CanvasClient → 10588 /api/canvas/v2/save-v2
  │   └─ _build_phase_node() → _PHASE_TYPE_MAP → correct node type
  │   └─ _ensure_project_exists() → o_project SQLite (known tech debt: sqlite refs)
  ├─ gold_team.py → 8002 /api/v1/tasks
  ├─ review_platform.py → review platform (JWT + HMAC)
  └─ agent-sync.js (Node.js, manual) → 10588 /api/v1/assets-registry
```

## Known Issues

1. **Port 8000 Docker container still running** — harmless but confusing. Should be stopped.
2. **sqlite references in canvas_sync.py** — `_ensure_project_exists()` does direct SQLite INSERT to create o_project records. This trips the "no sqlite in Phase 37 deliverables" test. Known pre-existing tech debt.
3. **o_project auto-creation** — the canvas frontend reads its project selector from `o_project` table, but `save-v2` stores FlowGraph in `o_agentWorkData` (independent). Without `_ensure_project_exists()`, data is saved but invisible in the UI.
