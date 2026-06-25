"""PipelineStateStore — Python port of the state-management extract from
``kais-movie-agent/lib/pipeline.js`` (Phase 33-01, SC#1).

Reference Node.js source:
- ``pipeline.js:217-249``  — ``_loadState`` / ``_saveState`` (file shape + load
  fallback to empty on missing/corrupt).
- ``pipeline.js:611-618``  — ``_findResumeIndex`` (first phase whose status is
  NOT in the done-set is the resume point).
- ``pipeline.js:553,612,668`` — ``DONE_STATUSES = {completed, approved,
  awaiting_review}``.

This module is the **data layer only**. The full run/resume orchestration loop
(launching phase handlers, parallelism, retries) belongs to Phase 35
(HERMES-SKILL-02). Here we provide:

- ``PipelineState`` frozen-ish dataclass representing the on-disk state file.
- ``PipelineStateStore`` with: ``load``, ``save``, ``save_checkpoint``,
  ``load_latest_checkpoint``, ``find_resume_phase``.

Design decisions (see ``CONTEXT.md``):
- D-33-01: pure stdlib, no third-party deps.
- D-33-02: atomic write via ``tempfile.mkstemp`` + ``os.replace`` (Node.js
  uses raw ``writeFile`` for state — we harden because a half-written state
  file corrupts an entire episode).
- CF-06: state file is ``.pipeline-state.json`` at the workdir **root**, NOT
  under ``.pipeline-assets/`` (the latter is owned by AssetBus, Plan 33-02).
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Phases whose status is one of these are considered "done" — re-running them
# would duplicate work. ``awaiting_review`` is in this set because the work is
# already submitted; the human-review loop is owned by Phase 34 (Gate).
# Matches Node.js pipeline.js:553,612,668.
DONE_STATUSES = frozenset({"completed", "approved", "awaiting_review"})


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass
class PipelineState:
    """On-disk pipeline state for a single episode/workdir.

    Mirrors the JSON shape documented in CONTEXT CF-06. Fields with
    ``None`` default are omitted-on-the-wire visually (serialized as null)
    but forward compatibly — ``load`` filters to known keys so new fields
    added later don't break old code.
    """

    episode: str
    phases: dict[str, dict] = field(default_factory=dict)
    current_phase_id: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    last_resumed_at: str | None = None
    trace_id: str | None = None

    # Expose DONE_STATUSES on the class too for ergonomic access from
    # callers that already hold a state instance. Kept as a class attribute
    # so it is shared (frozenset is immutable).
    DONE_STATUSES = DONE_STATUSES


# ---------------------------------------------------------------------------
# Atomic write helper
# ---------------------------------------------------------------------------

# Known PipelineState field names — used by ``load`` to filter forward-compat
# keys. Computed once at import time.
_STATE_FIELDS = frozenset(PipelineState.__dataclass_fields__.keys())


def _atomic_write_text(path: Path, data: str) -> None:
    """Atomic write via ``tempfile.mkstemp`` + ``os.replace``.

    Mirrors Node.js ``write-tmp-then-rename`` (asset-bus.js:160-165) per
    D-33-02. Tmp filename includes pid + ms timestamp + random hex so
    concurrent writers don't collide. ``os.replace`` is atomic on POSIX
    (single-filesystem rename(2)).

    Notable: no explicit ``fsync``. Node.js doesn't fsync the state file
    either; matching behavior preserves the perf profile and the durability
    contract callers already rely on.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_name = (
        f"{path.name}.tmp.{os.getpid()}.{int(time.time() * 1000)}"
        f".{os.urandom(3).hex()}"
    )
    tmp_path = path.parent / tmp_name
    fd, tmp_str = tempfile.mkstemp(
        prefix=f"{path.name}.tmp.", suffix=".tmp", dir=str(path.parent)
    )
    # mkstemp already picked a unique name — close our pre-generated one and
    # use the fd mkstemp returned (avoids race between two writers generating
    # identical pid+ms+rand names).
    try:
        os.close(fd)
    except OSError:
        pass
    # Use the mkstemp-provided path for the actual write.
    with open(tmp_str, "w", encoding="utf-8") as f:
        f.write(data)
    os.replace(tmp_str, str(path))


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------


class PipelineStateStore:
    """Persists pipeline state per workdir.

    File location: ``<workdir>/.pipeline-state.json`` (workdir ROOT, not
    under ``.pipeline-assets/`` — see CONTEXT CF-06).
    """

    STATE_FILE = ".pipeline-state.json"

    def __init__(self, workdir: str | Path):
        self._workdir = Path(workdir)
        self._path = self._workdir / self.STATE_FILE

    # -- load / save -------------------------------------------------------

    def load(self) -> PipelineState:
        """Load state, falling back to empty on missing/corrupt file.

        Mirrors Node.js ``_loadState`` (pipeline.js:217-224): a missing or
        unparseable state file is treated as a fresh episode rather than an
        error — the pipeline simply starts over.
        """
        try:
            raw_text = self._path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return PipelineState(episode="")
        except OSError as exc:
            logger.warning(
                "PipelineStateStore.load: unreadable state file %s: %s",
                self._path,
                exc,
            )
            return PipelineState(episode="")

        try:
            raw = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.warning(
                "PipelineStateStore.load: corrupt state file %s: %s",
                self._path,
                exc,
            )
            return PipelineState(episode="")

        if not isinstance(raw, dict):
            logger.warning(
                "PipelineStateStore.load: state file %s is not a JSON object",
                self._path,
            )
            return PipelineState(episode="")

        # Forward-compat filter: keep only known keys. Lets us add fields
        # without breaking older code that round-trips through the file.
        filtered = {k: v for k, v in raw.items() if k in _STATE_FIELDS}
        if "episode" not in filtered:
            filtered["episode"] = ""
        try:
            return PipelineState(**filtered)
        except TypeError:
            # Defensive — should be unreachable given the filter above.
            return PipelineState(episode=str(filtered.get("episode", "")))

    def save(self, state: PipelineState) -> None:
        """Atomically write state to ``.pipeline-state.json``.

        D-33-02: deviates from Node.js (which uses raw ``writeFile``) by
        using tmp-then-rename atomicity. Half-written state = corrupt
        episode; we harden.
        """
        data = json.dumps(
            asdict(state), indent=2, ensure_ascii=False
        )
        _atomic_write_text(self._path, data)

    # -- checkpoint helpers ------------------------------------------------

    def save_checkpoint(
        self,
        episode_id: str,
        phase: str,
        payload: dict,
    ) -> None:
        """Persist one phase's checkpoint (the SC#1 tool operation).

        - Sets ``state.episode`` only if empty (an episode is bound to its
          state file for its lifetime — a later call with a different
          ``episode_id`` does NOT silently flip it).
        - Records ``state.phases[phase]`` with ``status=completed`` + ISO
          ``completed_at`` + ``result=payload``.
        - Advances ``current_phase_id`` to ``phase``.
        """
        from datetime import datetime, timezone

        state = self.load()
        if not state.episode:
            state.episode = episode_id
        state.phases[phase] = {
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "result": payload,
        }
        state.current_phase_id = phase
        self.save(state)

    def load_latest_checkpoint(
        self, episode_id: str
    ) -> dict | None:
        """Most-recent phase checkpoint for the episode (SC#1 resume op).

        Returns ``None`` when:
        - The episode id doesn't match the state file's bound episode.
        - No checkpoint has been saved yet (``current_phase_id`` is None).
        """
        state = self.load()
        if state.episode != episode_id:
            return None
        if state.current_phase_id is None:
            return None
        return state.phases.get(state.current_phase_id)

    def find_resume_phase(
        self, phase_order: list[str]
    ) -> str | None:
        """First phase NOT in ``DONE_STATUSES``, or ``None`` if all done.

        Mirrors ``pipeline.js:611-618``. A phase is "done" if its recorded
        status is ``completed`` / ``approved`` / ``awaiting_review`` (the
        last counts as done because re-running would duplicate submitted
        work awaiting human review).
        """
        state = self.load()
        for phase_id in phase_order:
            phase_state = state.phases.get(phase_id)
            if phase_state is None:
                return phase_id
            if phase_state.get("status") not in DONE_STATUSES:
                return phase_id
        return None
