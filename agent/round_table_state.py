"""Round-table state machine (INFRA-03).

Persists per-project round-table state to
``~/.hermes/agents/.runtime/{project_slug}/round_tables/{round_id}.json``
with crash-safe atomic writes (``utils.atomic_json_write``) plus read-time
crash recovery for 3 failure modes per ``06-CROSS-REPO-IMPACT.md §6.4``:

    (a) Partial-write corruption → archive to ``{state_path}.corrupt`` +
        re-raise ``json.JSONDecodeError`` (defense-in-depth — the atomic
        write contract already guarantees no partial body)
    (b) Mid-turn crash (status=open + lastUpdatedAt > threshold) → flip
        status to ``"stalled"`` via atomic write
    (c) Orphaned session (same recovery path as (b))

State-enum authority
--------------------
``.planning/research/v10-orchestrator-design/round-table-state-schema.yaml``
lines 127-141 lock the status enum as::

    open | completed | aborted | stalled

CONTEXT.md / INFRA-03 prose occasionally uses ``open → in_progress → closed``
as informal shorthand; that is *shorthand only* and MUST NOT be serialized
to the state file (52-CONTEXT.md "Resolved by Kai" point 2). The schema
YAML is the wire-format authority.

Design sources (cite, do not re-derive)
---------------------------------------
- ``.planning/research/v10-orchestrator-design/round-table-state-schema.yaml``
  — Draft 2020-12 JSON Schema for state files (``additionalProperties: false``,
  camelCase property names, required-field list, status enum)
- ``.planning/research/v10-orchestrator-design/06-CROSS-REPO-IMPACT.md §5.1``
  — path layout (``agents/.runtime/{slug}/round_tables/``); ``§6`` — 3
  crash-recovery failure modes
- ``.planning/phases/52-infra-foundation/52-RESEARCH.md`` §"Atomic State
  Persistence Pattern" + §"Crash Recovery Read-Time Pattern" — canonical
  function skeletons
- ``utils.py:111`` ``atomic_json_write`` — temp + fsync + ``os.replace``
  (the entire defense for SC#3a partial-write recovery by construction)
- ``agent/turn_retry_state.py`` — dataclass-as-state idiom (here adapted
  to plain ``dict[str, Any]`` for schema-faithful camelCase key emission)
- ``hermes_constants.get_hermes_home()`` — canonical HERMES_HOME resolution
  (never ``Path.home() / ".hermes"``)

Public exports
--------------
- ``RoundTableStatus`` — ``str, Enum`` with values open / completed /
  aborted / stalled
- ``RoundTableStateError`` — invariant-violation exception
- ``open_round_table`` — create state file with ``status="open"``
- ``append_turn`` — read-modify-write a Turn atomically
- ``submit_round_table_result`` — terminal transition to ``status="completed"``
- ``read_and_recover_state`` — read + apply SC#3 a/b/c recovery
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from hermes_constants import get_hermes_home
from utils import atomic_json_write

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Path-traversal validation (T-52-09 mitigation, CR-01 fix)
# --------------------------------------------------------------------------- #
# round_id is the literal filename stem of a state file; project_slug is a
# path component of the state dir. Both MUST be validated before being
# concatenated into a filesystem path — otherwise a malicious MCP client
# can pass ``round_id="../../etc/passwd"`` to read/write arbitrary files
# under ``~/.hermes/`` (CR-01).
#
# Validation rules:
#   - Reject empty strings.
#   - Reject any value containing ``..`` substring (covers ``../``, ``..\\``).
#   - Reject path separators (``/``, ``\\``) explicitly — defense-in-depth
#     even though the regex below already excludes them.
#   - Match the full string against a strict allow-list regex:
#       * round_id: UUID v4 hex (32 lowercase hex) OR canonical UUID form
#         (8-4-4-4-12 lowercase hex, 36 chars). The ``round_table_open``
#         docstring promises "CC-generated UUID v4" — enforce it.
#       * project_slug: kebab/snake/camel slug chars (alphanumeric + ``_``,
#         ``-``, ``.``, ``:``); max 64 chars.

_PATH_SEP_RE = re.compile(r"[\\/]")
_ROUND_ID_RE = re.compile(r"^[a-f0-9]{32}$|^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$")
_PROJECT_SLUG_RE = re.compile(r"^[A-Za-z0-9_.:\-]{1,64}$")


def validate_round_id(round_id: str) -> str | None:
    """Return ``None`` if ``round_id`` is path-safe, else an error code string.

    A path-safe ``round_id`` is a UUID v4 hex (32 lowercase hex digits) or
    the canonical UUID form (36 chars, lowercase). Anything else — including
    path separators, ``..`` substrings, or non-hex chars — is rejected.

    The return value is a short error code suitable for inclusion in an MCP
    400 response body (e.g. ``"invalid_round_id"``). Callers should map
    non-None returns to a 400 status response without further processing.
    """
    if not isinstance(round_id, str) or not round_id:
        return "invalid_round_id"
    if ".." in round_id or _PATH_SEP_RE.search(round_id):
        return "invalid_round_id"
    if not _ROUND_ID_RE.fullmatch(round_id):
        return "invalid_round_id"
    return None


def validate_project_slug(project_slug: str) -> str | None:
    """Return ``None`` if ``project_slug`` is path-safe, else an error code.

    A path-safe slug is 1-64 chars of ``[A-Za-z0-9_.:-]`` with no ``..``
    substring and no path separators. Anything else is rejected.
    """
    if not isinstance(project_slug, str) or not project_slug:
        return "invalid_project_slug"
    if ".." in project_slug or _PATH_SEP_RE.search(project_slug):
        return "invalid_project_slug"
    if not _PROJECT_SLUG_RE.fullmatch(project_slug):
        return "invalid_project_slug"
    return None


# --------------------------------------------------------------------------- #
# Status enum — schema YAML is authoritative
# --------------------------------------------------------------------------- #


class RoundTableStatus(str, Enum):
    """Lifecycle status for a round-table state file.

    Authority: ``round-table-state-schema.yaml:127-141`` locks the enum as
    ``open | completed | aborted | stalled``.

    DO NOT add ``in_progress`` or ``closed`` — those values appear in
    CONTEXT.md / INFRA-03 prose as informal shorthand for the open-but-active
    and completed states, but they are NOT in the schema enum and serializing
    them would break the Draft 2020-12 ``additionalProperties: false``
    validation. See 52-CONTEXT.md "Resolved by Kai" point 2.
    """

    OPEN = "open"
    COMPLETED = "completed"
    ABORTED = "aborted"
    STALLED = "stalled"


class RoundTableStateError(Exception):
    """Raised on round-table state invariant violations.

    Examples: status transition outside the enum, structural corruption that
    defies read-time recovery, panelist-id mismatch on turn append. Callers
    that want soft 409 handling should catch this and map to a structured
    response; lower-level ``json.JSONDecodeError`` /
    ``FileNotFoundError`` propagate as-is per the SC#3 contract.
    """


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _now_iso() -> str:
    """ISO-8601 UTC timestamp, second precision (matches schema date-time)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _state_file_path(project_slug: str, round_id: str) -> Path:
    """Resolve the canonical state file path.

    Per ``round-table-state-schema.yaml`` header comment lines 1-4 +
    ``06-CROSS-REPO-IMPACT.md §5.1``, state files live at::

        ~/.hermes/agents/.runtime/{project_slug}/round_tables/{round_id}.json

    The ``agents/`` parent is load-bearing — it is omitted from some informal
    docs but present in the schema YAML header (the authoritative source).

    NOTE: does NOT create parent directories. ``open_round_table`` calls
    ``mkdir(parents=True, exist_ok=True)`` at the appropriate moment.
    """
    return (
        get_hermes_home()
        / "agents"
        / ".runtime"
        / project_slug
        / "round_tables"
        / f"{round_id}.json"
    )


def _read_state_sync(state_path: Path) -> dict[str, Any]:
    """Read + json.load a state file. Encoding explicit per CLAUDE.md PLW1514."""
    with open(state_path, encoding="utf-8") as f:
        return json.load(f)


def _fsync_parent_dir(dir_path: Path) -> None:
    """Fsync ``dir_path`` so recent renames / creations inside it are durable.

    CR-03 fix: POSIX ``rename(2)`` atomically swaps the name but does NOT
    guarantee the parent directory's metadata change is flushed to disk.
    On a crash between ``rename`` and the implicit dir-metadata flush, both
    the source and target files can vanish on ext4 / XFS default mount
    options. Calling ``fsync(dir_fd)`` after the rename closes that window.

    Linux supports directory fsync. Windows (where ``os.open`` on a
    directory may not be available) raises ``OSError`` — we swallow it
    because the rename has already logically succeeded; the fsync is
    defense-in-depth, not load-bearing for correctness on this happy path.

    Used by ``read_and_recover_state``'s corrupt-archive rename and by any
    other path that renames state files outside ``utils.atomic_json_write``
    (which already fsyncs its temp-file body — the body's parent-dir
    durability is the more subtle property this helper guarantees).
    """
    try:
        dir_fd = os.open(str(dir_path), os.O_RDONLY)
    except OSError as exc:
        logger.warning(
            "round_table_state: cannot open dir %s for fsync: %s",
            dir_path,
            exc,
        )
        return
    try:
        os.fsync(dir_fd)
    except OSError as exc:
        # Not all platforms / filesystems support directory fsync. The
        # rename has already succeeded; this fsync is best-effort.
        logger.warning(
            "round_table_state: parent-dir fsync failed for %s: %s",
            dir_path,
            exc,
        )
    finally:
        os.close(dir_fd)


# --------------------------------------------------------------------------- #
# Lifecycle primitives — SC#2 atomicity contract
# --------------------------------------------------------------------------- #


def open_round_table(
    state_dir: Path,
    round_id: str,
    project_id: str,
    question: str,
    panelist_agent_ids: list[str],
    caller: str,
) -> dict[str, Any]:
    """SC#2 step 1: create a new round-table state file with ``status="open"``.

    Idempotent: if a state file at ``{state_dir}/{round_id}.json`` already
    exists, returns a 409 Conflict dict (does NOT raise). This makes the
    lifecycle safe under CC retry.

    Args:
        state_dir: Directory that should hold the state file (the MCP tool
            computes it; this function trusts the caller's slug-validated
            path). ``mkdir(parents=True, exist_ok=True)`` runs before write.
        round_id: CC-generated UUID v4. Used as the filename stem.
        project_id: Project slug for ``.runtime/{slug}/`` routing.
        question: Free-text topic being debated.
        panelist_agent_ids: List of agent IDs; minItems 2 per schema.
        caller: CC session ID / operator handle for audit trail.

    Returns:
        The newly-created state dict (camelCase keys per schema YAML),
        OR ``{"error": "round_already_open", "status": 409, "round_id": ...}``
        on duplicate open.
    """
    state_path = state_dir / f"{round_id}.json"
    if state_path.exists():
        return {"error": "round_already_open", "status": 409, "round_id": round_id}

    now_iso = _now_iso()

    # Build minimal PanelistSnapshot list per $defs.PanelistSnapshot required
    # fields: agentId / personaSha256 / fitnessScore / tools / memoryScope.
    # The MCP tool layer (Phase 52-03) will enrich persona snapshots from the
    # registry; the state machine here only needs schema-valid placeholders.
    panelists = [
        {
            "agentId": agent_id,
            "personaSha256": "0" * 64,
            "fitnessScore": None,
            "tools": [],
            "memoryScope": "per_agent",
        }
        for agent_id in panelist_agent_ids
    ]

    state: dict[str, Any] = {
        # Identity & routing (schema required)
        "roundId": round_id,
        "projectId": project_id,
        "question": question,
        # Panelists — open-time snapshot (OQ-5)
        "panelists": panelists,
        # Turn order — strategy + seed + currentIndex (OQ-2)
        "turnOrder": {
            "strategy": "round-robin",
            "currentIndex": 0,
            "seed": list(panelist_agent_ids),
        },
        # Lifecycle status — schema YAML:127-141 authoritative enum
        "status": RoundTableStatus.OPEN.value,
        # Append-only turn log
        "turns": [],
        # Conflict log — sealed at submit time
        "conflicts": [],
        # Atomic open event (ARCHITECTURE §8.3 anti-pattern: returns immediately)
        "roundTableOpen": {
            "caller": caller,
            "openedAt": now_iso,
            "project": project_id,
            "question": question,
        },
        # Persona drift detection network anchor (PITFALLS §P1 mitigation 4)
        "personaSnapshots": {},
        # Schema migration safety (PITFALLS §P14 mitigation 1)
        "schemaVersion": "1.0.0",
        # Timestamps
        "createdAt": now_iso,
        "lastUpdatedAt": None,  # NULL until first turn append (per schema YAML:246-253)
    }

    state_dir.mkdir(parents=True, exist_ok=True)
    # atomic_json_write = temp + fsync + os.replace — partial-write safe.
    atomic_json_write(state_path, state, indent=2)
    logger.info(
        "round_table opened: round_id=%s project=%s panelists=%d caller=%s",
        round_id,
        project_id,
        len(panelist_agent_ids),
        caller,
    )
    return state


def append_turn(state_path: Path, turn: dict[str, Any]) -> dict[str, Any]:
    """SC#2 step 2: append a Turn atomically (read-modify-write).

    Caller (the per-``roundId`` asyncio.Lock in
    ``agent/round_table_executor``) is responsible for serializing concurrent
    ``append_turn`` calls. This function is sync because it does no I/O
    blocking beyond a single file read + atomic write.

    Args:
        state_path: State file path (typically ``state_dir / f"{round_id}.json"``).
        turn: Turn dict matching ``$defs.Turn`` (turnIndex / panelistId /
            opinion / citedMemoryIds / submittedAt). Caller builds this.

    Returns:
        The updated state dict after the turn append.
    """
    state = _read_state_sync(state_path)
    state["turns"].append(turn)
    state["lastUpdatedAt"] = _now_iso()
    atomic_json_write(state_path, state, indent=2)
    return state


def submit_round_table_result(
    state_path: Path,
    conclusion: str,
    cited_memories: list[str],
    closed_by: str,
) -> dict[str, Any]:
    """SC#2 step 3: terminal transition. Flips ``status`` to ``"completed"``
    and adds the ``submitRoundTableResult`` block.

    Idempotent: if status is not ``"open"`` (already completed / aborted /
    stalled), returns ``{"error": "round_not_open", "status": 409}`` instead
    of mutating the state.

    Args:
        state_path: State file path.
        conclusion: CC's synthesis of the round-table discussion.
        cited_memories: All memory record_ids cited across turns + conclusion.
        closed_by: CC session ID / operator handle for audit trail.

    Returns:
        The sealed state dict (``status="completed"``) OR a 409 conflict dict.
    """
    state = _read_state_sync(state_path)
    if state.get("status") != RoundTableStatus.OPEN.value:
        return {"error": "round_not_open", "status": 409}

    now_iso = _now_iso()
    state["status"] = RoundTableStatus.COMPLETED.value
    state["submitRoundTableResult"] = {
        "conclusion": conclusion,
        "citedMemories": list(cited_memories),
        "closedAt": now_iso,
        "closedBy": closed_by,
    }
    state["lastUpdatedAt"] = now_iso
    atomic_json_write(state_path, state, indent=2)
    logger.info(
        "round_table completed: round_id=%s closed_by=%s cited_memories=%d",
        state.get("roundId"),
        closed_by,
        len(cited_memories),
    )
    return state


def abort_round_table(
    state_path: Path,
    *,
    reason: str,
    aborted_by: str,
) -> dict[str, Any]:
    """Operator / CC cancellation transition (CR-04 fix).

    Mirrors ``submit_round_table_result``'s shape but flips status to
    ``"aborted"`` instead of ``"completed"``. ``RoundTableStatus.ABORTED``
    is in the schema enum (round-table-state-schema.yaml:127-141) but no
    function previously produced it — operators / CC could not represent
    cancellation in the state file, leaving cancelled rounds looking
    identical to open rounds until stall timeout kicked in 30 minutes
    later. The audit trail for cancellations was lost.

    Allowed transition: ``open → aborted``. Rejects if already in a
    terminal state (``completed`` or ``aborted``). Also rejects ``stalled``
    because stalled rounds should be resumed (``stalled → open`` via
    ``open_round_table``'s idempotent re-open) or explicitly resumed-then-
    aborted by the operator, not silently flipped to aborted from stalled.

    Idempotent: re-aborting an already-aborted round returns 409 Conflict
    (the round is already terminal). This mirrors the
    ``submit_round_table_result`` contract.

    Not wired into MCP tools (Phase 52 deliberately ships no
    ``round_table_abort`` MCP tool — that is v11.1+ scope per
    ``02-ROUND-TABLE-PROTOCOL.md §5.0``). This is a programmatic API for
    operator scripts / curator hooks / future MCP wiring.

    Args:
        state_path: State file path.
        reason: Operator-supplied cancellation reason (free text). Sealed
            in the ``abortRoundTable.reason`` audit field.
        aborted_by: Operator handle / CC session ID. Sealed in the
            ``abortRoundTable.abortedBy`` audit field.

    Returns:
        The aborted state dict (``status="aborted"``) OR
        ``{"error": "round_not_open", "status": 409}`` on terminal conflict.
    """
    state = _read_state_sync(state_path)
    current = state.get("status")
    if current != RoundTableStatus.OPEN.value:
        # Already terminal (completed / aborted) or stalled. Reject.
        return {
            "error": "round_not_open",
            "status": 409,
            "current_status": current,
        }

    now_iso = _now_iso()
    state["status"] = RoundTableStatus.ABORTED.value
    state["abortRoundTable"] = {
        "reason": reason,
        "abortedAt": now_iso,
        "abortedBy": aborted_by,
    }
    state["lastUpdatedAt"] = now_iso
    atomic_json_write(state_path, state, indent=2)
    logger.info(
        "round_table aborted: round_id=%s aborted_by=%s reason=%s",
        state.get("roundId"),
        aborted_by,
        reason,
    )
    return state


# --------------------------------------------------------------------------- #
# Read-time crash recovery — SC#3 a / b / c
# --------------------------------------------------------------------------- #


def read_and_recover_state(
    state_path: Path,
    *,
    stall_threshold_minutes: int = 30,
) -> dict[str, Any]:
    """Read a round-table state file and apply 3 failure-mode recovery per
    ``06-CROSS-REPO-IMPACT.md §6.4``:

    (a) Partial-write corruption → ``json.JSONDecodeError``. ``atomic_json_write``
        guarantees this CANNOT happen to the file body, but defense-in-depth:
        archive to ``{state_path}.corrupt`` and re-raise.
    (b) Mid-turn crash → process died between turn append and status flip.
        State shows ``status="open"`` + ``lastUpdatedAt`` older than
        ``stall_threshold_minutes``. Recovery: flip status to ``"stalled"``
        via atomic write.
    (c) Orphaned session → state file exists but the calling process is gone.
        Recovery: same as (b) — stall detection on read.

    Args:
        state_path: State file path.
        stall_threshold_minutes: Stall threshold in minutes (default 30 per
            schema YAML default + ``05-POC-PLAN.md``).

    Returns:
        The recovered state dict. May have ``status="stalled"`` if recovery
        triggered (b/c). For (a), the function raises.

    Raises:
        FileNotFoundError: state file missing.
        json.JSONDecodeError: state file corrupt (after archiving).
    """
    if not state_path.exists():
        raise FileNotFoundError(state_path)

    # ── (a) Partial-write recovery: archive + raise ────────────────────────
    try:
        state = _read_state_sync(state_path)
    except json.JSONDecodeError as exc:
        # atomic_json_write guarantees no partial body — this branch is
        # defense-in-depth for kernel/fs-level corruption (EXT4-fsync race on
        # ancient kernels, NFS misconfiguration, etc.). Archive the corrupt
        # file so operator can triage, then re-raise so callers know state is
        # unavailable (rather than silently masking with a default).
        archive = state_path.with_suffix(".json.corrupt")
        state_path.rename(archive)
        # CR-03 fix: fsync the parent dir so the rename (POSIX rename(2)) is
        # durable across power loss. Without this, a crash between rename and
        # the implicit directory metadata flush can lose BOTH files on ext4 /
        # XFS default mount options. Linux supports directory fsync; on
        # platforms that don't (Windows), the OSError is swallowed.
        _fsync_parent_dir(state_path.parent)
        logger.error(
            "round_table_state corrupt at %s, archived to %s: %s",
            state_path,
            archive,
            exc,
        )
        raise

    # ── (b)/(c) Mid-turn crash + orphaned session: stall detection ────────
    if state.get("status") == RoundTableStatus.OPEN.value and state.get(
        "lastUpdatedAt"
    ):
        try:
            last_updated = datetime.fromisoformat(state["lastUpdatedAt"])
        except (ValueError, TypeError) as exc:
            # Malformed lastUpdatedAt — log + skip stall detection (don't
            # block reads on a field that may have been hand-edited).
            logger.warning(
                "round_table %s has malformed lastUpdatedAt=%r; skipping stall detection: %s",
                state.get("roundId"),
                state.get("lastUpdatedAt"),
                exc,
            )
        else:
            # Make naive datetimes UTC-aware so the comparison is well-defined.
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=timezone.utc)
            age_minutes = (
                datetime.now(timezone.utc) - last_updated
            ).total_seconds() / 60
            if age_minutes > stall_threshold_minutes:
                logger.warning(
                    "round_table %s stalled (age=%dm > %dm); flipping status",
                    state.get("roundId"),
                    int(age_minutes),
                    stall_threshold_minutes,
                )
                state["status"] = RoundTableStatus.STALLED.value
                atomic_json_write(state_path, state, indent=2)

    return state
