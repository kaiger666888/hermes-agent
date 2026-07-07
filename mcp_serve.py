"""
Hermes MCP Server — expose messaging conversations as MCP tools.

Starts a stdio MCP server that lets any MCP client (Claude Code, Cursor, Codex,
etc.) list conversations, read message history, send messages, poll for live
events, and manage approval requests across all connected platforms.

Matches OpenClaw's 9-tool MCP channel bridge surface:
  conversations_list, conversation_get, messages_read, attachments_fetch,
  events_poll, events_wait, messages_send, permissions_list_open,
  permissions_respond

Plus: channels_list (Hermes-specific extra)

Usage:
    hermes mcp serve
    hermes mcp serve --verbose

MCP client config (e.g. claude_desktop_config.json):
    {
        "mcpServers": {
            "hermes": {
                "command": "hermes",
                "args": ["mcp", "serve"]
            }
        }
    }
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("hermes.mcp_serve")

# ---------------------------------------------------------------------------
# Lazy MCP SDK import
# ---------------------------------------------------------------------------

_MCP_SERVER_AVAILABLE = False
try:
    from mcp.server.fastmcp import FastMCP

    _MCP_SERVER_AVAILABLE = True
except ImportError:
    FastMCP = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_sessions_dir() -> Path:
    """Return the sessions directory using HERMES_HOME."""
    try:
        from hermes_constants import get_hermes_home
        return get_hermes_home() / "sessions"
    except ImportError:
        return Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")) / "sessions"


def _get_session_db():
    """Get a SessionDB instance for reading message transcripts."""
    try:
        from hermes_state import SessionDB
        return SessionDB()
    except Exception as e:
        logger.debug("SessionDB unavailable: %s", e)
        return None


def _load_sessions_index() -> dict:
    """Load the gateway sessions.json index directly.

    Returns a dict of session_key -> entry_dict with platform routing info.
    This avoids importing the full SessionStore which needs GatewayConfig.
    """
    sessions_file = _get_sessions_dir() / "sessions.json"
    if not sessions_file.exists():
        return {}
    try:
        with open(sessions_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.debug("Failed to load sessions.json: %s", e)
        return {}


def _load_channel_directory() -> dict:
    """Load the cached channel directory for available targets."""
    try:
        from hermes_constants import get_hermes_home
        directory_file = get_hermes_home() / "channel_directory.json"
    except ImportError:
        directory_file = Path(
            os.environ.get("HERMES_HOME", Path.home() / ".hermes")
        ) / "channel_directory.json"

    if not directory_file.exists():
        return {}
    try:
        with open(directory_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.debug("Failed to load channel_directory.json: %s", e)
        return {}


def _coerce_int(
    value,
    *,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    """Coerce value to int with fallback and clamping.

    Used at MCP tool boundaries to handle invalid types from external clients.
    Returns default if value cannot be converted to int.
    """
    try:
        coerced = int(value)
    except (TypeError, ValueError):
        coerced = default
    return max(minimum, min(coerced, maximum))


def _extract_message_content(msg: dict) -> str:
    """Extract text content from a message, handling multi-part content."""
    content = msg.get("content", "")
    if isinstance(content, list):
        text_parts = [
            p.get("text", "") for p in content
            if isinstance(p, dict) and p.get("type") == "text"
        ]
        return "\n".join(text_parts)
    return str(content) if content else ""


def _extract_attachments(msg: dict) -> List[dict]:
    """Extract non-text attachments from a message.

    Finds: multi-part image/file content blocks, MEDIA: tags in text,
    image URLs, and file references.
    """
    attachments = []
    content = msg.get("content", "")

    # Multi-part content blocks (image_url, file, etc.)
    if isinstance(content, list):
        for part in content:
            if not isinstance(part, dict):
                continue
            ptype = part.get("type", "")
            if ptype == "image_url":
                url = part.get("image_url", {}).get("url", "") if isinstance(part.get("image_url"), dict) else ""
                if url:
                    attachments.append({"type": "image", "url": url})
            elif ptype == "image":
                url = part.get("url", part.get("source", {}).get("url", ""))
                if url:
                    attachments.append({"type": "image", "url": url})
            elif ptype not in {"text",}:
                # Unknown non-text content type
                attachments.append({"type": ptype, "data": part})

    # MEDIA: tags in text content
    text = _extract_message_content(msg)
    if text:
        media_pattern = re.compile(r'MEDIA:\s*(\S+)')
        for match in media_pattern.finditer(text):
            path = match.group(1)
            attachments.append({"type": "media", "path": path})

    return attachments


# ---------------------------------------------------------------------------
# Event Bridge — polls SessionDB for new messages, maintains event queue
# ---------------------------------------------------------------------------

QUEUE_LIMIT = 1000
POLL_INTERVAL = 0.2  # seconds between DB polls (200ms)


@dataclass
class QueueEvent:
    """An event in the bridge's in-memory queue."""
    cursor: int
    type: str  # "message", "approval_requested", "approval_resolved"
    session_key: str = ""
    data: dict = field(default_factory=dict)


class EventBridge:
    """Background poller that watches SessionDB for new messages and
    maintains an in-memory event queue with waiter support.

    This is the Hermes equivalent of OpenClaw's WebSocket gateway bridge.
    Instead of WebSocket events, we poll the SQLite database for changes.
    """

    def __init__(self):
        self._queue: List[QueueEvent] = []
        self._cursor = 0
        self._lock = threading.Lock()
        self._new_event = threading.Event()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_poll_timestamps: Dict[str, float] = {}  # session_key -> unix timestamp
        # In-memory approval tracking (populated from events)
        self._pending_approvals: Dict[str, dict] = {}
        # mtime cache — skip expensive work when files haven't changed
        self._sessions_json_mtime: float = 0.0
        self._state_db_mtime: float = 0.0
        self._cached_sessions_index: dict = {}

    def start(self):
        """Start the background polling thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.debug("EventBridge started")

    def stop(self):
        """Stop the background polling thread."""
        self._running = False
        self._new_event.set()  # Wake any waiters
        if self._thread:
            self._thread.join(timeout=5)
        logger.debug("EventBridge stopped")

    def poll_events(
        self,
        after_cursor: int = 0,
        session_key: Optional[str] = None,
        limit: int = 20,
    ) -> dict:
        """Return events since after_cursor, optionally filtered by session_key."""
        with self._lock:
            events = [
                e for e in self._queue
                if e.cursor > after_cursor
                and (not session_key or e.session_key == session_key)
            ][:limit]

        next_cursor = events[-1].cursor if events else after_cursor
        return {
            "events": [
                {"cursor": e.cursor, "type": e.type,
                 "session_key": e.session_key, **e.data}
                for e in events
            ],
            "next_cursor": next_cursor,
        }

    def wait_for_event(
        self,
        after_cursor: int = 0,
        session_key: Optional[str] = None,
        timeout_ms: int = 30000,
    ) -> Optional[dict]:
        """Block until a matching event arrives or timeout expires."""
        deadline = time.monotonic() + (timeout_ms / 1000.0)

        while time.monotonic() < deadline:
            with self._lock:
                for e in self._queue:
                    if e.cursor > after_cursor and (
                        not session_key or e.session_key == session_key
                    ):
                        return {
                            "cursor": e.cursor, "type": e.type,
                            "session_key": e.session_key, **e.data,
                        }

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            self._new_event.clear()
            self._new_event.wait(timeout=min(remaining, POLL_INTERVAL))

        return None

    def list_pending_approvals(self) -> List[dict]:
        """List approval requests observed during this bridge session."""
        with self._lock:
            return sorted(
                self._pending_approvals.values(),
                key=lambda a: a.get("created_at", ""),
            )

    def respond_to_approval(self, approval_id: str, decision: str) -> dict:
        """Resolve a pending approval (best-effort without gateway IPC)."""
        with self._lock:
            approval = self._pending_approvals.pop(approval_id, None)

        if not approval:
            return {"error": f"Approval not found: {approval_id}"}

        self._enqueue(QueueEvent(
            cursor=0,  # Will be set by _enqueue
            type="approval_resolved",
            session_key=approval.get("session_key", ""),
            data={"approval_id": approval_id, "decision": decision},
        ))

        return {"resolved": True, "approval_id": approval_id, "decision": decision}

    def _enqueue(self, event: QueueEvent) -> None:
        """Add an event to the queue and wake any waiters."""
        with self._lock:
            self._cursor += 1
            event.cursor = self._cursor
            self._queue.append(event)
            # Trim queue to limit
            while len(self._queue) > QUEUE_LIMIT:
                self._queue.pop(0)
        self._new_event.set()

    def _poll_loop(self):
        """Background loop: poll SessionDB for new messages."""
        db = _get_session_db()
        if not db:
            logger.warning("EventBridge: SessionDB unavailable, event polling disabled")
            return

        while self._running:
            try:
                self._poll_once(db)
            except Exception as e:
                logger.debug("EventBridge poll error: %s", e)
            time.sleep(POLL_INTERVAL)

    def _poll_once(self, db):
        """Check for new messages across all sessions.

        Uses mtime checks on sessions.json and state.db to skip work
        when nothing has changed — makes 200ms polling essentially free.
        """
        # Check if sessions.json has changed (mtime check is ~1μs)
        sessions_file = _get_sessions_dir() / "sessions.json"
        try:
            sj_mtime = sessions_file.stat().st_mtime if sessions_file.exists() else 0.0
        except OSError:
            sj_mtime = 0.0

        if sj_mtime != self._sessions_json_mtime:
            self._sessions_json_mtime = sj_mtime
            self._cached_sessions_index = _load_sessions_index()

        # Check if state.db has changed
        try:
            from hermes_constants import get_hermes_home
            db_file = get_hermes_home() / "state.db"
        except ImportError:
            db_file = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")) / "state.db"

        try:
            db_mtime = db_file.stat().st_mtime if db_file.exists() else 0.0
        except OSError:
            db_mtime = 0.0

        if db_mtime == self._state_db_mtime and sj_mtime == self._sessions_json_mtime:
            return  # Nothing changed since last poll — skip entirely

        self._state_db_mtime = db_mtime
        entries = self._cached_sessions_index

        for session_key, entry in entries.items():
            session_id = entry.get("session_id", "")
            if not session_id:
                continue

            last_seen = self._last_poll_timestamps.get(session_key, 0.0)

            try:
                messages = db.get_messages(session_id)
            except Exception:
                continue

            if not messages:
                continue

            # Normalize timestamps to float for comparison
            def _ts_float(ts) -> float:
                if isinstance(ts, (int, float)):
                    return float(ts)
                if isinstance(ts, str) and ts:
                    try:
                        return float(ts)
                    except ValueError:
                        # ISO string — parse to epoch
                        try:
                            from datetime import datetime
                            return datetime.fromisoformat(ts).timestamp()
                        except Exception:
                            return 0.0
                return 0.0

            # Find messages newer than our last seen timestamp
            new_messages = []
            for msg in messages:
                ts = _ts_float(msg.get("timestamp", 0))
                role = msg.get("role", "")
                if role not in {"user", "assistant"}:
                    continue
                if ts > last_seen:
                    new_messages.append(msg)

            for msg in new_messages:
                content = _extract_message_content(msg)
                if not content:
                    continue
                self._enqueue(QueueEvent(
                    cursor=0,
                    type="message",
                    session_key=session_key,
                    data={
                        "role": msg.get("role", ""),
                        "content": content[:500],
                        "timestamp": str(msg.get("timestamp", "")),
                        "message_id": str(msg.get("id", "")),
                    },
                ))

            # Update last seen to the most recent message timestamp
            all_ts = [_ts_float(m.get("timestamp", 0)) for m in messages]
            if all_ts:
                latest = max(all_ts)
                if latest > last_seen:
                    self._last_poll_timestamps[session_key] = latest


# ---------------------------------------------------------------------------
# Round-table + memory tools — module-level Phase 53 surface
# ---------------------------------------------------------------------------
#
# Phase 53 (CREATIVE-SLICE): the 5 Phase 52 round-table / memory MCP tools
# were originally defined as nested functions inside ``create_mcp_server()``,
# making them unimportable. Plan 53-03 lifted them to module level so:
#
#   - The driver script ``scripts/run_screenplay_step3_roundtable.py`` can
#     call them directly via ``from mcp_serve import round_table_open,
#     get_agent_opinion, submit_round_table_result`` (Wave 0 contract).
#   - Unit tests in ``tests/agent/test_run_screenplay_step3.py`` can invoke
#     them directly (including the concurrent-gather serial-violation test).
#   - ``create_mcp_server`` simply re-registers them via ``mcp.tool()(fn)``.
#
# Phase 52 contract preserved verbatim:
#   - Signatures, docstrings, error responses, status codes unchanged.
#   - The FastMCP server still exposes the same 5 tool names.
#   - T-52-15 try/finally lock contract in ``get_agent_opinion`` intact.
#
# Phase 53 contract addition:
#   - ``get_agent_opinion`` no longer returns the Phase 52 placeholder
#     opinion string — it now performs real GLM dispatch via
#     ``auxiliary_client.call_llm(task="round_table_opinion", provider="glm")``
#     and routes memory through ``memory_arbitration.memory_retrieve_scoped``
#     with the ``_scoped_agent_id`` ContextVar set + cleared in finally.


async def round_table_open(
    round_id: str,
    project_slug: str,
    question: str,
    panelist_agent_ids: list[str],
    caller: str = "cc",
) -> str:
    """Open a new round-table discussion (lifecycle step 1 of 3).

    Creates a state file at
    ``~/.hermes/agents/.runtime/{project_slug}/round_tables/{round_id}.json``
    with ``status="open"``. Idempotent — re-calling with the same
    ``round_id`` returns 409 Conflict (does NOT mutate).

    Follow with ``get_agent_opinion`` (one or more times) and terminate
    with ``submit_round_table_result``.

    Args:
        round_id: CC-generated UUID v4. Filename stem for the state file.
        project_slug: Project identifier for per-project state isolation
            (``.runtime/{slug}/round_tables/``). Validated against
            ``^[a-zA-Z0-9_.:-]+$``; ``..`` substrings rejected (T-52-09).
        question: Free-text topic being debated.
        panelist_agent_ids: List of agent IDs; minItems=2 per
            round-table-state-schema.yaml $defs.PanelistSnapshot.
        caller: CC session ID / operator handle for audit trail.
    """
    # T-52-09 mitigation + CR-01 fix: validate both project_slug AND
    # round_id before they are concatenated into a filesystem path.
    # Without round_id validation, a malicious MCP client could pass
    # round_id="../../etc/passwd" to read/write arbitrary files.
    from agent.round_table_state import (
        validate_project_slug,
        validate_round_id,
    )

    slug_err = validate_project_slug(project_slug)
    if slug_err is not None:
        return json.dumps(
            {"error": slug_err, "status": 400},
            indent=2,
        )
    round_err = validate_round_id(round_id)
    if round_err is not None:
        return json.dumps(
            {"error": round_err, "status": 400, "round_id": round_id},
            indent=2,
        )

    # Schema minItems=2 enforcement at open-time
    if not isinstance(panelist_agent_ids, list) or len(panelist_agent_ids) < 2:
        return json.dumps(
            {"error": "panelists_min_2_required", "status": 400},
            indent=2,
        )

    # WR-03 fix: item-level validation. The previous check only verified
    # "is a list of length >= 2" — it did NOT verify each item is a
    # non-empty string matching the agent-id pattern, nor that the list
    # has no duplicates. Without this, None / empty-string / duplicate
    # IDs silently land on disk via open_round_table's
    # panelists[].agentId + turnOrder.seed writes (and the loader does
    # NOT re-validate persisted state against the schema).
    import re as _panel_re
    _AGENT_ID_RE = _panel_re.compile(r"^[a-z0-9_-]+$")
    for pid in panelist_agent_ids:
        if not isinstance(pid, str) or not pid:
            return json.dumps(
                {"error": "invalid_panelist_id", "status": 400,
                 "detail": "panelist_agent_ids items must be non-empty strings"},
                indent=2,
            )
        if not _AGENT_ID_RE.fullmatch(pid):
            return json.dumps(
                {"error": "invalid_panelist_id", "status": 400,
                 "detail": f"panelist_agent_ids item {pid!r} must match ^[a-z0-9_-]+$",
                 "invalid_value": pid},
                indent=2,
            )
    if len(set(panelist_agent_ids)) != len(panelist_agent_ids):
        return json.dumps(
            {"error": "duplicate_panelist_id", "status": 400,
             "detail": "panelist_agent_ids must be unique — duplicates would "
                       "violate the 'different panelists' contract of minItems=2"},
            indent=2,
        )

    from hermes_constants import get_hermes_home
    from agent.registry_loader import RegistryValidationError
    from agent.round_table_state import open_round_table

    state_dir = (
        get_hermes_home()
        / "agents"
        / ".runtime"
        / project_slug
        / "round_tables"
    )
    try:
        state = open_round_table(
            state_dir=state_dir,
            round_id=round_id,
            project_id=project_slug,
            question=question,
            panelist_agent_ids=panelist_agent_ids,
            caller=caller,
        )
    except RegistryValidationError as exc:
        # WR-02 fix: surface typed 400 with the structured json_path /
        # invalid_field so callers can debug schema violations without
        # parsing the human-readable message.
        logger.warning(
            "round_table_open: registry validation failed: %s", exc
        )
        return json.dumps(
            {
                "error": "registry_validation_failed",
                "status": 400,
                "detail": str(exc),
                "json_path": exc.json_path,
                "invalid_field": exc.invalid_field,
            },
            indent=2,
        )
    except Exception as exc:
        logger.warning(
            "round_table_open: open_round_table failed: %s", exc
        )
        return json.dumps(
            {"error": "open_failed", "status": 500, "detail": str(exc)},
            indent=2,
        )

    if "error" in state:
        # open_round_table returns a dict-with-error on 409 Conflict
        return json.dumps(state, indent=2)

    return json.dumps(
        {"roundId": round_id, "status": "open", "state": state},
        indent=2,
    )


# -- get_agent_opinion --------------------------------------------------
#
# Phase 53 (plan 53-03 Task 1) replaces the Phase 52 placeholder opinion
# with real GLM dispatch + scoped memory retrieval. The T-52-15 try/finally
# lock contract is preserved verbatim — the only structural change is the
# nested try/finally for ``set_scoped_agent_id`` cleanup (RESEARCH Pitfall 5).


def _format_memory_context(hits: list) -> str:
    """Format memory hits as a prior-memory preamble for the panelist prompt.

    Returns an empty string when no hits — the caller should omit the
    section entirely rather than emit a "no prior memory" line (which
    tends to confuse the LLM into apologizing for forgetting things).
    """
    if not hits:
        return ""
    lines = ["Prior memory (from this agent's namespace):"]
    for hit in hits:
        if isinstance(hit, dict):
            content = hit.get("content") or hit.get("text") or ""
            rid = hit.get("record_id") or hit.get("id") or "?"
        else:
            content = str(hit)
            rid = "?"
        if content:
            lines.append(f"- [{rid}] {content}")
    return "\n".join(lines) if len(lines) > 1 else ""


def _load_persona_for_agent(agent_id: str) -> str:
    """Load the persona field from the agent's YAML, fallback to generic.

    Used by ``get_agent_opinion`` as the system-prompt persona for the GLM
    call. Falls back to a generic directive if the YAML is missing (e.g.
    registry not seeded) so the round table can still proceed.
    """
    try:
        from hermes_constants import get_hermes_home
        from agent.registry_loader import load_one_agent_yaml

        yaml_path = get_hermes_home() / "agents" / f"{agent_id}.agent.yaml"
        if yaml_path.exists():
            record = load_one_agent_yaml(yaml_path)
            persona = record.get("persona")
            if isinstance(persona, str) and persona.strip():
                return persona
        logger.debug(
            "get_agent_opinion: no persona for agent_id=%s (yaml missing or empty)",
            agent_id,
        )
    except Exception as exc:  # noqa: BLE001 — persona lookup is best-effort
        logger.debug(
            "get_agent_opinion: persona lookup failed for %s: %s",
            agent_id,
            exc,
        )
    return f"You are {agent_id}. Contribute your expert slice on the round-table topic."


def _extract_cited_memory_ids(hits: list) -> list:
    """Pull record IDs out of memory hits for the Turn dict's citedMemoryIds."""
    ids: list = []
    for hit in hits or []:
        if isinstance(hit, dict):
            rid = hit.get("record_id") or hit.get("id")
            if rid and rid not in ids:
                ids.append(rid)
    return ids


async def get_agent_opinion(
    round_id: str,
    project_slug: str,
    agent_id: str,
    topic: str,
    panel_context: Optional[str] = None,
) -> str:
    """Get one panelist's opinion on a topic within an open round table.

    Phase 53 (plan 53-03): performs real GLM dispatch via
    ``auxiliary_client.call_llm(task="round_table_opinion", provider="glm")``
    + scoped memory retrieval via ``memory_arbitration.memory_retrieve_scoped``.

    Lifecycle step 2 of 3 — call between ``round_table_open`` and
    ``submit_round_table_result``.

    Args:
        round_id: The roundId from round_table_open.
        project_slug: Same slug passed to round_table_open.
        agent_id: The panelist's agent name.
        topic: Topic/question this turn addresses.
        panel_context: Optional prior-turn context for the panelist.
    """
    # INFRA-04 (Phase 52-04): per-roundId asyncio.Lock serializes
    # get_agent_opinion so concurrent calls for the same roundId are
    # REJECTED with 429 + MEMORY.md citation (NOT queued). This is the
    # GLM concurrency safety layer — queueing would violate the 4-key
    # rotation compatibility constraint locked by user-memory policy
    # feedback-glm-overload-reduce-concurrency.md.
    from agent.round_table_executor import (
        _serial_violation_response,
        acquire_round_or_reject,
        release_round_lock,
    )
    from hermes_constants import get_hermes_home
    from agent.round_table_state import (
        _now_iso as _state_now_iso,
        append_turn,
        read_and_recover_state,
        validate_project_slug,
        validate_round_id,
    )
    # Phase 53 wiring: real memory routing + real GLM dispatch.
    from agent.memory_arbitration import (
        memory_retrieve_scoped,
        set_scoped_agent_id,
    )
    from agent.auxiliary_client import call_llm

    # CR-01 fix: validate BOTH inputs before they touch the filesystem.
    # Order matters — reject before acquiring the lock so a rejected
    # call doesn't pollute the per-roundId lock registry.
    slug_err = validate_project_slug(project_slug)
    if slug_err is not None:
        return json.dumps(
            {"error": slug_err, "status": 400},
            indent=2,
        )
    round_err = validate_round_id(round_id)
    if round_err is not None:
        return json.dumps(
            {"error": round_err, "status": 400, "round_id": round_id},
            indent=2,
        )

    lock = await acquire_round_or_reject(round_id)
    if lock is None:
        return _serial_violation_response(round_id)

    try:
        state_path = (
            get_hermes_home()
            / "agents"
            / ".runtime"
            / project_slug
            / "round_tables"
            / f"{round_id}.json"
        )

        if not state_path.exists():
            return json.dumps(
                {
                    "error": "round_not_found",
                    "status": 404,
                    "round_id": round_id,
                },
                indent=2,
            )

        try:
            state = read_and_recover_state(state_path)
        except FileNotFoundError:
            return json.dumps(
                {
                    "error": "round_not_found",
                    "status": 404,
                    "round_id": round_id,
                },
                indent=2,
            )
        except Exception as exc:
            logger.warning(
                "get_agent_opinion: state read failed for %s: %s",
                round_id,
                exc,
            )
            return json.dumps(
                {"error": "state_read_failed", "detail": str(exc)},
                indent=2,
            )

        if state.get("status") != "open":
            return json.dumps(
                {
                    "error": "round_not_open",
                    "status": 409,
                    "round_id": round_id,
                    "current_status": state.get("status"),
                },
                indent=2,
            )

        # Phase 53: real GLM dispatch + scoped memory retrieval.
        #
        # Nested try/finally: the OUTER finally releases the per-roundId
        # lock (T-52-15 DoS mitigation preserved verbatim from Phase 52).
        # The INNER finally clears ``_scoped_agent_id`` so the ContextVar
        # does not leak into the next panelist's turn (RESEARCH Pitfall 5).
        set_scoped_agent_id(agent_id)
        try:
            # memory_retrieve_scoped honors the ContextVar we just set; it
            # falls back to the explicit agent_id if the ContextVar is unset
            # (defensive — never blocks the round on missing scope).
            try:
                mem_result = await memory_retrieve_scoped(
                    query=topic, agent_id=agent_id, top_k=5,
                )
            except Exception as exc:  # noqa: BLE001 — memory degrade, never crash
                logger.warning(
                    "get_agent_opinion: memory_retrieve_scoped failed for %s: %s",
                    agent_id,
                    exc,
                )
                mem_result = {"status": "unavailable", "hits": []}

            memory_context = _format_memory_context(mem_result.get("hits", []))
            cited_memory_ids = _extract_cited_memory_ids(mem_result.get("hits", []))

            persona = _load_persona_for_agent(agent_id)

            # Build the opinion query: topic + panel_context + memory + story
            # context (driver script passes StoryKernel JSON via panel_context).
            user_parts = [f"# Round-table topic\n{topic}"]
            if panel_context:
                user_parts.append(
                    f"\n# Prior panel discussion (chain)\n{panel_context}"
                )
            if memory_context:
                user_parts.append(f"\n# {memory_context}")
            user_parts.append(
                "\n# Your task\nContribute your expert slice on this topic. "
                "Be concrete and actionable; cite specific moments from "
                "the topic or panel discussion. Limit to ~200 words."
            )
            user_prompt = "\n".join(user_parts)

            # CRITICAL (MEMORY.md feedback-glm-5-2-only.md): explicit
            # provider="glm" — never rely on the auto-chain (which could
            # pick OpenRouter and violate the user's GLM-only policy).
            response = call_llm(
                task="round_table_opinion",
                provider="glm",
                messages=[
                    {"role": "system", "content": persona},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=2048,
            )
            # WR-02: defensive content extraction — same pattern as
            # ``agent.memory_arbitration._extract_content`` + driver's
            # synthesis pass. If the LLM returns a malformed shape (None
            # response, empty choices, missing message), return a structured
            # JSON error rather than propagating AttributeError up through
            # the asyncio task (which would crash the MCP server / daemon).
            try:
                opinion_text = str(response.choices[0].message.content)
            except (AttributeError, IndexError, TypeError) as exc:
                logger.warning(
                    "get_agent_opinion: malformed LLM response for %s: %s",
                    agent_id,
                    exc,
                )
                return json.dumps(
                    {
                        "error": "llm_malformed_response",
                        "agent_id": agent_id,
                        "detail": str(exc),
                    },
                    indent=2,
                )

            # Build the Turn dict per round-table-state-schema.yaml $defs.Turn.
            turn = {
                "turnIndex": len(state.get("turns", [])) + 1,
                "panelistId": agent_id,
                "opinion": opinion_text,
                "citedMemoryIds": cited_memory_ids,
                "submittedAt": _state_now_iso(),
            }

            try:
                append_turn(state_path, turn)
            except Exception as exc:
                logger.warning(
                    "get_agent_opinion: append_turn failed for %s: %s",
                    round_id,
                    exc,
                )
                return json.dumps(
                    {"error": "append_turn_failed", "detail": str(exc)},
                    indent=2,
                )

            return json.dumps(
                {
                    "round_id": round_id,
                    "agent_id": agent_id,
                    "opinion": opinion_text,
                    "cited_memory_ids": cited_memory_ids,
                    "status": "ok",
                },
                indent=2,
            )
        finally:
            # RESEARCH Pitfall 5 mitigation: clear the ContextVar on EVERY
            # exit path (happy, error, asyncio.CancelledError). Without this,
            # the scope leaks into the next panelist's turn and memory calls
            # hit the wrong namespace.
            set_scoped_agent_id(None)
    finally:
        # T-52-15 (DoS): lock MUST be released on every path — happy,
        # error, AND asyncio.CancelledError. Without finally, an
        # exception in read_and_recover_state or append_turn would
        # permanently block that roundId.
        await release_round_lock(round_id)


async def submit_round_table_result(
    round_id: str,
    project_slug: str,
    conclusion: str,
    cited_memories: Optional[list[str]] = None,
    closed_by: str = "cc",
) -> str:
    """Submit the round-table conclusion (terminal lifecycle step 3 of 3).

    Flips state file ``status`` from ``"open"`` to ``"completed"`` and
    seals the ``submitRoundTableResult`` block. Idempotent: re-calling
    on a completed round returns 409 Conflict.

    Args:
        round_id: The roundId from round_table_open.
        project_slug: Same slug passed to round_table_open.
        conclusion: CC's synthesis of the round-table discussion.
        cited_memories: Memory record_ids cited across turns + conclusion.
        closed_by: CC session ID / operator handle for audit trail.
    """
    from hermes_constants import get_hermes_home
    from agent.round_table_state import (
        submit_round_table_result as _submit,
        validate_project_slug,
        validate_round_id,
    )

    # CR-01 fix: validate BOTH inputs before they touch the filesystem.
    slug_err = validate_project_slug(project_slug)
    if slug_err is not None:
        return json.dumps(
            {"error": slug_err, "status": 400},
            indent=2,
        )
    round_err = validate_round_id(round_id)
    if round_err is not None:
        return json.dumps(
            {"error": round_err, "status": 400, "round_id": round_id},
            indent=2,
        )

    state_path = (
        get_hermes_home()
        / "agents"
        / ".runtime"
        / project_slug
        / "round_tables"
        / f"{round_id}.json"
    )

    if not state_path.exists():
        return json.dumps(
            {
                "error": "round_not_found",
                "status": 404,
                "round_id": round_id,
            },
            indent=2,
        )

    try:
        result = _submit(
            state_path,
            conclusion=conclusion,
            cited_memories=cited_memories or [],
            closed_by=closed_by,
        )
    except Exception as exc:
        logger.warning(
            "submit_round_table_result: submit failed for %s: %s",
            round_id,
            exc,
        )
        return json.dumps(
            {"error": "submit_failed", "detail": str(exc)},
            indent=2,
        )

    if "error" in result:
        # _submit returns a dict-with-error on 409 round_not_open
        return json.dumps(result, indent=2)

    return json.dumps(
        {"roundId": round_id, "status": "completed"},
        indent=2,
    )


# -- memory_retrieve_scoped / memory_submit_record ----------------------
#
# Phase 52 stubs replaced by Phase 53 routing in plan 53-02. These thin
# MCP wrappers forward to the (now-real) agent.memory_arbitration functions.


async def memory_retrieve_scoped(
    query: str,
    agent_id: str,
    top_k: int = 5,
) -> str:
    """Retrieve scoped memories for an agent.

    Forwards to ``agent.memory_arbitration.memory_retrieve_scoped`` which
    routes to the mem0 backend (or returns ``{"status": "unavailable",
    "hits": []}`` when the backend is not configured).

    Args:
        query: Free-text recall query.
        agent_id: The agent whose memory namespace to consult.
        top_k: Max results to return.
    """
    from agent.memory_arbitration import memory_retrieve_scoped as _retrieve

    result = await _retrieve(query, agent_id, top_k=top_k)
    return json.dumps(result, indent=2)


async def memory_submit_record(
    agent_id: str,
    content: str,
    scope: str = "per_agent",
    confidence: float = 0.5,
) -> str:
    """Submit a memory record for an agent.

    Forwards to ``agent.memory_arbitration.memory_submit_record`` which
    routes to the mem0 backend (or returns ``{"status": "unavailable",
    "record_id": null}`` when the backend is not configured).

    Args:
        agent_id: The agent whose memory namespace to write into.
        content: Free-text memory content to persist.
        scope: One of ``shared`` / ``per_agent`` / ``project_scoped``.
        confidence: Optional confidence score in [0.0, 1.0].
    """
    from agent.memory_arbitration import memory_submit_record as _submit_record

    result = await _submit_record(
        agent_id, content, scope=scope, confidence=confidence
    )
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

def create_mcp_server(event_bridge: Optional[EventBridge] = None) -> "FastMCP":
    """Create and return the Hermes MCP server with all tools registered."""
    if not _MCP_SERVER_AVAILABLE:
        raise ImportError(
            "MCP server requires the 'mcp' package. "
            f"Install with: {sys.executable} -m pip install 'mcp'"
        )

    mcp = FastMCP(
        "hermes",
        instructions=(
            "Hermes Agent messaging bridge. Use these tools to interact with "
            "conversations across Telegram, Discord, Slack, WhatsApp, Signal, "
            "Matrix, and other connected platforms."
        ),
    )

    bridge = event_bridge or EventBridge()

    # -- conversations_list ------------------------------------------------

    @mcp.tool()
    def conversations_list(
        platform: Optional[str] = None,
        limit: int = 50,
        search: Optional[str] = None,
    ) -> str:
        """List active messaging conversations across connected platforms.

        Returns conversations with their session keys (needed for messages_read),
        platform, chat type, display name, and last activity time.

        Args:
            platform: Filter by platform name (telegram, discord, slack, etc.)
            limit: Maximum number of conversations to return (default 50)
            search: Optional text to filter conversations by name
        """
        limit = _coerce_int(limit, default=50, minimum=1, maximum=200)
        entries = _load_sessions_index()
        conversations = []

        for key, entry in entries.items():
            origin = entry.get("origin", {})
            entry_platform = entry.get("platform") or origin.get("platform", "")

            if platform and entry_platform.lower() != platform.lower():
                continue

            display_name = entry.get("display_name", "")
            chat_name = origin.get("chat_name", "")
            if search:
                search_lower = search.lower()
                if (search_lower not in display_name.lower()
                        and search_lower not in chat_name.lower()
                        and search_lower not in key.lower()):
                    continue

            conversations.append({
                "session_key": key,
                "session_id": entry.get("session_id", ""),
                "platform": entry_platform,
                "chat_type": entry.get("chat_type", origin.get("chat_type", "")),
                "display_name": display_name,
                "chat_name": chat_name,
                "user_name": origin.get("user_name", ""),
                "updated_at": entry.get("updated_at", ""),
            })

        conversations.sort(key=lambda c: c.get("updated_at", ""), reverse=True)
        conversations = conversations[:limit]

        return json.dumps({
            "count": len(conversations),
            "conversations": conversations,
        }, indent=2)

    # -- conversation_get --------------------------------------------------

    @mcp.tool()
    def conversation_get(session_key: str) -> str:
        """Get detailed info about one conversation by its session key.

        Args:
            session_key: The session key from conversations_list
        """
        entries = _load_sessions_index()
        entry = entries.get(session_key)

        if not entry:
            return json.dumps({"error": f"Conversation not found: {session_key}"})

        origin = entry.get("origin", {})
        return json.dumps({
            "session_key": session_key,
            "session_id": entry.get("session_id", ""),
            "platform": entry.get("platform") or origin.get("platform", ""),
            "chat_type": entry.get("chat_type", origin.get("chat_type", "")),
            "display_name": entry.get("display_name", ""),
            "user_name": origin.get("user_name", ""),
            "chat_name": origin.get("chat_name", ""),
            "chat_id": origin.get("chat_id", ""),
            "thread_id": origin.get("thread_id"),
            "updated_at": entry.get("updated_at", ""),
            "created_at": entry.get("created_at", ""),
            "input_tokens": entry.get("input_tokens", 0),
            "output_tokens": entry.get("output_tokens", 0),
            "total_tokens": entry.get("total_tokens", 0),
        }, indent=2)

    # -- messages_read -----------------------------------------------------

    @mcp.tool()
    def messages_read(
        session_key: str,
        limit: int = 50,
    ) -> str:
        """Read recent messages from a conversation.

        Returns the message history in chronological order with role, content,
        and timestamp for each message.

        Args:
            session_key: The session key from conversations_list
            limit: Maximum number of messages to return (default 50, most recent)
        """
        limit = _coerce_int(limit, default=50, minimum=1, maximum=200)
        entries = _load_sessions_index()
        entry = entries.get(session_key)
        if not entry:
            return json.dumps({"error": f"Conversation not found: {session_key}"})

        session_id = entry.get("session_id", "")
        if not session_id:
            return json.dumps({"error": "No session ID for this conversation"})

        db = _get_session_db()
        if not db:
            return json.dumps({"error": "Session database unavailable"})

        try:
            all_messages = db.get_messages(session_id)
        except Exception as e:
            return json.dumps({"error": f"Failed to read messages: {e}"})

        filtered = []
        for msg in all_messages:
            role = msg.get("role", "")
            if role in {"user", "assistant"}:
                content = _extract_message_content(msg)
                if content:
                    filtered.append({
                        "id": str(msg.get("id", "")),
                        "role": role,
                        "content": content[:2000],
                        "timestamp": msg.get("timestamp", ""),
                    })

        messages = filtered[-limit:]

        return json.dumps({
            "session_key": session_key,
            "count": len(messages),
            "total_in_session": len(filtered),
            "messages": messages,
        }, indent=2)

    # -- attachments_fetch -------------------------------------------------

    @mcp.tool()
    def attachments_fetch(
        session_key: str,
        message_id: str,
    ) -> str:
        """List non-text attachments for a message in a conversation.

        Extracts images, media files, and other non-text content blocks
        from the specified message.

        Args:
            session_key: The session key from conversations_list
            message_id: The message ID from messages_read
        """
        entries = _load_sessions_index()
        entry = entries.get(session_key)
        if not entry:
            return json.dumps({"error": f"Conversation not found: {session_key}"})

        session_id = entry.get("session_id", "")
        if not session_id:
            return json.dumps({"error": "No session ID for this conversation"})

        db = _get_session_db()
        if not db:
            return json.dumps({"error": "Session database unavailable"})

        try:
            all_messages = db.get_messages(session_id)
        except Exception as e:
            return json.dumps({"error": f"Failed to read messages: {e}"})

        # Find the target message
        target_msg = None
        for msg in all_messages:
            if str(msg.get("id", "")) == message_id:
                target_msg = msg
                break

        if not target_msg:
            return json.dumps({"error": f"Message not found: {message_id}"})

        attachments = _extract_attachments(target_msg)

        return json.dumps({
            "message_id": message_id,
            "count": len(attachments),
            "attachments": attachments,
        }, indent=2)

    # -- events_poll -------------------------------------------------------

    @mcp.tool()
    def events_poll(
        after_cursor: int = 0,
        session_key: Optional[str] = None,
        limit: int = 20,
    ) -> str:
        """Poll for new conversation events since a cursor position.

        Returns events that have occurred since the given cursor. Use the
        returned next_cursor value for subsequent polls.

        Event types: message, approval_requested, approval_resolved

        Args:
            after_cursor: Return events after this cursor (0 for all)
            session_key: Optional filter to one conversation
            limit: Maximum events to return (default 20)
        """
        after_cursor = _coerce_int(after_cursor, default=0, minimum=0, maximum=10**18)
        limit = _coerce_int(limit, default=20, minimum=1, maximum=200)
        result = bridge.poll_events(
            after_cursor=after_cursor,
            session_key=session_key,
            limit=limit,
        )
        return json.dumps(result, indent=2)

    # -- events_wait -------------------------------------------------------

    @mcp.tool()
    def events_wait(
        after_cursor: int = 0,
        session_key: Optional[str] = None,
        timeout_ms: int = 30000,
    ) -> str:
        """Wait for the next conversation event (long-poll).

        Blocks until a matching event arrives or the timeout expires.
        Use this for near-real-time event delivery without polling.

        Args:
            after_cursor: Wait for events after this cursor
            session_key: Optional filter to one conversation
            timeout_ms: Maximum wait time in milliseconds (default 30000)
        """
        after_cursor = _coerce_int(after_cursor, default=0, minimum=0, maximum=10**18)
        timeout_ms = _coerce_int(
            timeout_ms,
            default=30000,
            minimum=0,
            maximum=300000,
        )  # Cap at 5 minutes
        event = bridge.wait_for_event(
            after_cursor=after_cursor,
            session_key=session_key,
            timeout_ms=timeout_ms,
        )
        if event:
            return json.dumps({"event": event}, indent=2)
        return json.dumps({"event": None, "reason": "timeout"}, indent=2)

    # -- messages_send -----------------------------------------------------

    @mcp.tool()
    def messages_send(
        target: str,
        message: str,
    ) -> str:
        """Send a message to a platform conversation.

        The target format is ``platform:chat_id`` — or, for platforms that
        support threaded delivery, ``platform:chat_id:thread_id``.

        Threaded targets:
            - **Telegram forum topics / supergroups**:
              ``telegram:-1001234567890:17585`` (chat_id:topic_id)
            - **Telegram private-topic DMs**: same format; the gateway will
              resolve the private topic and attach a reply anchor.
            - **Discord threads**: ``discord:999888777:555444333``
              (channel_id:thread_id)

        Other supported formats:
            - ``telegram`` (uses home channel)
            - ``telegram:6308981865``
            - ``discord:#general``
            - ``slack:#engineering``

        Args:
            target: Platform target in ``platform:identifier[:thread_id]`` format
            message: The message text to send
        """
        if not target or not message:
            return json.dumps({"error": "Both target and message are required"})

        try:
            from tools.send_message_tool import send_message_tool
            result_str = send_message_tool(
                {"action": "send", "target": target, "message": message}
            )
            return result_str
        except ImportError:
            return json.dumps({"error": "Send message tool not available"})
        except Exception as e:
            return json.dumps({"error": f"Send failed: {e}"})

    # -- channels_list -----------------------------------------------------

    @mcp.tool()
    def channels_list(platform: Optional[str] = None) -> str:
        """List available messaging channels and targets across platforms.

        Returns channels that you can send messages to. The target strings
        returned here can be used directly with the messages_send tool.

        Args:
            platform: Filter by platform name (telegram, discord, slack, etc.)
        """
        directory = _load_channel_directory()
        if not directory:
            entries = _load_sessions_index()
            targets = []
            seen = set()
            for key, entry in entries.items():
                origin = entry.get("origin", {})
                p = entry.get("platform") or origin.get("platform", "")
                chat_id = origin.get("chat_id", "")
                if not p or not chat_id:
                    continue
                if platform and p.lower() != platform.lower():
                    continue
                target_str = f"{p}:{chat_id}"
                if target_str in seen:
                    continue
                seen.add(target_str)
                targets.append({
                    "target": target_str,
                    "platform": p,
                    "name": entry.get("display_name") or origin.get("chat_name", ""),
                    "chat_type": entry.get("chat_type", origin.get("chat_type", "")),
                })
            return json.dumps({"count": len(targets), "channels": targets}, indent=2)

        channels = []
        for plat, entries_list in directory.get("platforms", {}).items():
            if platform and plat.lower() != platform.lower():
                continue
            if isinstance(entries_list, list):
                for ch in entries_list:
                    if isinstance(ch, dict):
                        chat_id = ch.get("id", ch.get("chat_id", ""))
                        channels.append({
                            "target": f"{plat}:{chat_id}" if chat_id else plat,
                            "platform": plat,
                            "name": ch.get("name", ch.get("display_name", "")),
                            "chat_type": ch.get("type", ""),
                        })

        return json.dumps({"count": len(channels), "channels": channels}, indent=2)

    # -- permissions_list_open ---------------------------------------------

    @mcp.tool()
    def permissions_list_open() -> str:
        """List pending approval requests observed during this bridge session.

        Returns exec and plugin approval requests that the bridge has seen
        since it started. Approvals are live-session only — older approvals
        from before the bridge connected are not included.
        """
        approvals = bridge.list_pending_approvals()
        return json.dumps({
            "count": len(approvals),
            "approvals": approvals,
        }, indent=2)

    # -- permissions_respond -----------------------------------------------

    @mcp.tool()
    def permissions_respond(
        id: str,
        decision: str,
    ) -> str:
        """Respond to a pending approval request.

        Args:
            id: The approval ID from permissions_list_open
            decision: One of "allow-once", "allow-always", or "deny"
        """
        if decision not in {"allow-once", "allow-always", "deny"}:
            return json.dumps({
                "error": f"Invalid decision: {decision}. "
                         f"Must be allow-once, allow-always, or deny"
            })

        result = bridge.respond_to_approval(id, decision)
        return json.dumps(result, indent=2)

    # ── v11.0 round-table tools (Phase 52 INFRA-02) ───────────────────────
    #
    # 7 new MCP tools implementing the v11.0 PoC round-table surface.
    # Tool names LOCKED by 52-CONTEXT.md "Resolved by Kai" point 1 — this
    # list intentionally diverges from the stale 02-ROUND-TABLE-PROTOCOL.md
    # §5 list (which is the v10.0 broader vision, not v11.0 PoC scope).
    #
    # Tool contracts (delegating modules):
    #   agents_list / agent_describe  → agent.registry_loader
    #   round_table_open / get_agent_opinion /
    #   submit_round_table_result     → agent.round_table_state
    #   memory_retrieve_scoped /
    #   memory_submit_record          → agent.memory_arbitration (Phase 52 stub)
    #
    # All closures use lazy imports for agent.* modules to avoid coupling
    # mcp_serve startup to registry_loader / round_table_state (mirrors the
    # lazy-import pattern in channels_list above).

    # -- agents_list --------------------------------------------------------

    @mcp.tool()
    def agents_list(
        category: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> str:
        """List registered Hermes agents (~/.hermes/agents/*.agent.yaml).

        Returns each agent's name, description, version, tags, fitness_score,
        and memory_scope. Use ``agent_describe`` for full details on a
        specific agent.

        Args:
            category: Optional category filter (reserved — Phase 53)
            tag: Optional tag filter; matches any tag in the agent's
                ``tags`` list (agents-schema.yaml §2.9).
        """
        from agent.registry_loader import (
            RegistryValidationError,
            load_agent_registry,
        )

        try:
            entries = load_agent_registry()
        except RegistryValidationError as exc:
            # WR-02: surface typed 400 with json_path / invalid_field so
            # callers can debug schema violations without parsing the
            # human-readable message.
            logger.warning("agents_list: registry validation failed: %s", exc)
            return json.dumps(
                {
                    "error": "registry_validation_failed",
                    "status": 400,
                    "detail": str(exc),
                    "json_path": exc.json_path,
                    "invalid_field": exc.invalid_field,
                },
                indent=2,
            )
        except Exception as exc:
            logger.warning("agents_list: registry load failed: %s", exc)
            return json.dumps(
                {"error": "registry_load_failed", "status": 500, "detail": str(exc)},
                indent=2,
            )

        filtered = entries
        if tag:
            filtered = [e for e in filtered if tag in e.get("tags", [])]
        # category filter reserved for Phase 53 (agents-schema.yaml has no
        # top-level "category" field yet — only "tags").

        return json.dumps(
            {
                "count": len(filtered),
                "agents": [
                    {
                        "name": e.get("name", ""),
                        "description": e.get("description", ""),
                        "version": e.get("version", ""),
                        "tags": e.get("tags", []),
                        "fitness_score": e.get("fitness_score"),
                        "memory_scope": e.get("memory_scope"),
                    }
                    for e in filtered
                ],
            },
            indent=2,
        )

    # -- agent_describe -----------------------------------------------------

    @mcp.tool()
    def agent_describe(name: str) -> str:
        """Return the full agent YAML for one named agent.

        Use ``agents_list`` to discover names. Returns the complete agent
        dict (persona, tools, memory_scope, lineage, etc.) — broader than
        just the persona block.

        Args:
            name: The agent's ``name`` field (must match a filename stem
                under ``~/.hermes/agents/``).
        """
        from agent.registry_loader import (
            RegistryValidationError,
            load_agent_registry,
        )

        try:
            entries = load_agent_registry()
        except RegistryValidationError as exc:
            # WR-02: surface typed 400 with structured fields.
            logger.warning("agent_describe: registry validation failed: %s", exc)
            return json.dumps(
                {
                    "error": "registry_validation_failed",
                    "status": 400,
                    "detail": str(exc),
                    "json_path": exc.json_path,
                    "invalid_field": exc.invalid_field,
                },
                indent=2,
            )
        except Exception as exc:
            logger.warning("agent_describe: registry load failed: %s", exc)
            return json.dumps(
                {"error": "registry_load_failed", "status": 500, "detail": str(exc)},
                indent=2,
            )

        for entry in entries:
            if entry.get("name") == name:
                return json.dumps({"agent": entry}, indent=2)

        return json.dumps(
            {
                "error": "agent_not_found",
                "status": 404,
                "name": name,
            },
            indent=2,
        )

    # -- Phase 53 round-table + memory tools (module-level, registered here) --
    #
    # Phase 53 (plan 53-03) lifted these 5 Phase 52 tools from nested
    # functions inside create_mcp_server() to module-level async functions
    # (see ``async def round_table_open`` etc. above). This makes them
    # importable for the driver script + directly unit-testable. The
    # FastMCP ``mcp.tool()`` decorator simply re-registers each module
    # function under the same tool name — the MCP surface is unchanged.
    mcp.tool()(round_table_open)
    mcp.tool()(get_agent_opinion)
    mcp.tool()(submit_round_table_result)
    mcp.tool()(memory_retrieve_scoped)
    mcp.tool()(memory_submit_record)

    return mcp


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_mcp_server(verbose: bool = False) -> None:
    """Start the Hermes MCP server on stdio."""
    if not _MCP_SERVER_AVAILABLE:
        print(
            "Error: MCP server requires the 'mcp' package.\n"
            f"Install with: {sys.executable} -m pip install 'mcp'",
            file=sys.stderr,
        )
        sys.exit(1)

    if verbose:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
    else:
        logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

    bridge = EventBridge()
    bridge.start()

    server = create_mcp_server(event_bridge=bridge)

    import asyncio

    async def _run():
        try:
            await server.run_stdio_async()
        finally:
            bridge.stop()

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        bridge.stop()
