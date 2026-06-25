"""asset_bus.py — AssetBus V3 port (reference: kais-movie-agent/lib/asset-bus.js).

Port of the Node.js AssetBus V3 (332 lines). Pure stdlib, sync API, atomic
writes via ``tempfile.mkstemp`` + ``os.replace``.

Scope (Phase 33, per CONTEXT CF-05 / SC#2):
  - 3 v3.0 typed slots: ``creative-history`` / ``failed-shots`` / ``finetune-dataset``
  - ``review-outcomes`` routed as generic JSON (D-33-03; Phase 34 tightens schema)
  - V3 envelope ``{value, derived_from, content_hash, schema_version}`` with v2.0
    backward compat on unwrap
  - Atomic write (write-tmp-then-rename) for JSON slots; JSONL append via
    ``open(..., "a")`` for the finetune-dataset slot (no fsync — matches Node.js)
  - mtime-based cache keyed on ``st_mtime_ns`` (writes invalidate by slot prefix)

Differences from Node.js (documented in PATTERNS.md):
  - Sync API (no ``async def``); D-07 applies
  - ``json.dumps(sort_keys=True)`` for cross-run hash determinism
  - ``st_mtime_ns`` (ns precision) rather than ``mtimeMs``
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "3.0"
ASSETS_DIR = ".pipeline-assets"

# ASSET_SCHEMA — Phase 33 scope (3 v3.0 typed slots + review-outcomes).
# V2/V4.1 slots (art-bible, character-assets, visual-soul, etc.) are out of
# scope — they belong to other phases per CONTEXT CF-05.
ASSET_SCHEMA: dict[str, dict] = {
    "creative-history": {
        "file": "creative-history.json",
        "format": "json",
        "schema": {
            "shots": "Array<{shot_id, source_hash, derived_from: string[], content_hash, timestamp}>",
            "version": "number",
        },
    },
    "failed-shots": {
        "file": "failed-shots.json",
        "format": "json",
        "schema": {
            "failures": "Array<{shot_id, error, timestamp, run_id, prompt, fingerprints?: {dino?: number[], phash?: string}}>",
            "version": "number",
        },
    },
    "finetune-dataset": {
        "file": "finetune-dataset.jsonl",
        "format": "jsonl",  # append-only — use append_line / read_lines
    },
    # D-33-03: Phase 33 routes this slot as generic JSON; Phase 34 defines the
    # full schema + Gate resolution semantics.
    "review-outcomes": {
        "file": "review-outcomes.json",
        "format": "json",
    },

    # ── Phase 35 additions — phase-output slots (D-35-05) ──────────────
    # Phase 35-02 task 1 registers these 6 slots so phase modules
    # (p01_hook_topic, p02_outline, p03_script_audit — implemented in 35-03)
    # can write their outputs via AssetBus.write(). All are JSON format
    # (envelope-wrapped, atomic write). None are append-only history slots.
    #
    # Slot names mirror the V8.6 Node.js asset-bus slot names where they
    # exist, in kebab-case, so cross-port tracing is easier in Phase 36.
    # Phase 36 will extend this list with the remaining slots
    # (character-bible, scene-design, shot-list, voice-timeline, video-clips,
    # audio-stems, master-mp4, etc.).
    "requirement": {
        "file": "requirement.json",
        "format": "json",
    },
    "topic-kernel": {
        "file": "topic-kernel.json",
        "format": "json",
    },
    "hook-design": {
        "file": "hook-design.json",
        "format": "json",
    },
    "story-framework": {
        "file": "story-framework.json",
        "format": "json",
    },
    "script-draft": {
        "file": "script-draft.json",
        "format": "json",
    },
    "audit-report": {
        "file": "audit-report.json",
        "format": "json",
    },
}


class AssetBusError(Exception):
    """Programmer-error exception (unknown slot, format mismatch, missing required)."""


# ─── Module-level helpers (mirror Node.js exports) ───────────────────


def _compute_content_hash(value: Any) -> str:
    """SHA-256 hex of canonical JSON.

    Uses ``sort_keys=True`` for cross-run determinism (differs from Node.js
    insertion-order JSON.stringify, but removes a class of dict-ordering bugs —
    see PATTERNS.md "Differences From Node.js Reference").
    """
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def wrap_envelope(value: Any, derived_from: list[str] | None = None) -> dict:
    """Wrap raw payload in a v3.0 envelope.

    Mirrors ``asset-bus.js:122-129``. Returns a dict with:
      - ``value``: the raw payload
      - ``derived_from``: list of upstream content_hashes (defaults to [])
      - ``content_hash``: SHA-256 hex of ``value``
      - ``schema_version``: ``"3.0"``
    """
    derived_list = list(derived_from) if derived_from else []
    return {
        "value": value,
        "derived_from": derived_list,
        "content_hash": _compute_content_hash(value),
        "schema_version": SCHEMA_VERSION,
    }


def unwrap_envelope(raw: Any) -> Any:
    """Return ``raw["value"]`` if ``raw`` is a v3.0 envelope, else return ``raw`` unchanged.

    Backward-compatible with v2.0 raw JSON: a plain dict without
    ``schema_version == "3.0"`` and a ``value`` key passes through untouched.
    Arrays are never envelopes. Mirrors ``asset-bus.js:136-143``.
    """
    if (
        isinstance(raw, dict)
        and not isinstance(raw, list)
        and raw.get("schema_version") == SCHEMA_VERSION
        and "value" in raw
    ):
        return raw["value"]
    return raw


def _atomic_write_text(path: Path, data: str) -> None:
    """Atomic write: tmp file + ``os.replace`` (POSIX rename atomicity).

    Mirrors Node.js ``asset-bus.js:160-165`` (``writeFile`` + ``rename``).
    The tmp filename embeds pid + ms timestamp + urandom hex for uniqueness
    across concurrent producers within one process.

    On any exception during write, best-effort clean up the tmp file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_name = (
        f"{path.name}.tmp.{os.getpid()}.{int(time.time() * 1000)}.{os.urandom(3).hex()}"
    )
    tmp_path = path.parent / tmp_name
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(data)
        os.replace(str(tmp_path), str(path))
    except Exception:
        # Best-effort cleanup of tmp residue on failure
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass
        raise


# ─── AssetBus ────────────────────────────────────────────────────────


class AssetBus:
    """Filesystem-backed asset bus over ``.pipeline-assets/``.

    JSON slots round-trip through the v3.0 envelope (``write`` / ``read``).
    JSONL slots (``finetune-dataset``) use ``append_line`` / ``read_lines``.
    All JSON writes are atomic (tmp + ``os.replace``). mtime-based cache
    invalidates on every write for the affected slot.
    """

    # Slots that use append_line/read_lines (Plan 33-04 dispatches on this set)
    JSONL_SLOTS = frozenset({"finetune-dataset"})

    def __init__(self, workdir: str | Path):
        self._dir = Path(workdir) / ASSETS_DIR
        self._cache: dict[str, Any] = {}

    # ── Cache helpers ──────────────────────────────────────────────

    def _cache_key(self, slot: str) -> str | None:
        """Return ``f"{slot}:{mtime_ns}"`` or None if file missing / slot unknown."""
        schema = ASSET_SCHEMA.get(slot)
        if not schema:
            return None
        path = self._dir / schema["file"]
        try:
            st = path.stat()
        except FileNotFoundError:
            return None
        return f"{slot}:{st.st_mtime_ns}"

    def _invalidate_cache(self, slot: str) -> None:
        """Delete all cache entries for ``slot`` (mtime change → next read misses)."""
        prefix = f"{slot}:"
        keys_to_delete = [k for k in self._cache if k.startswith(prefix) or k == slot]
        for k in keys_to_delete:
            del self._cache[k]

    # ── JSON slot API ──────────────────────────────────────────────

    def write(
        self,
        slot: str,
        data: Any,
        *,
        envelope: bool = True,
        derived_from: list[str] | None = None,
    ) -> str:
        """Atomically write a JSON slot, wrapping in the v3.0 envelope by default.

        ``derived_from`` non-empty forces envelope even when ``envelope=False``
        (mirrors ``asset-bus.js:206-213`` — Phase 23 change so that
        ``content_hash`` linkage required by CreativeHistoryTracker is always
        recorded). Returns the absolute path written.
        """
        schema = ASSET_SCHEMA.get(slot)
        if not schema:
            raise AssetBusError(f"Unknown asset: {slot}")
        if schema.get("format") == "jsonl":
            raise AssetBusError(
                f"Slot {slot} is JSONL — use append_line() instead of write()"
            )

        derived_list = list(derived_from) if derived_from else []
        # derived_from non-empty forces envelope (asset-bus.js:210)
        use_envelope = (len(derived_list) > 0) or envelope
        payload = wrap_envelope(data, derived_list) if use_envelope else data

        path = self._dir / schema["file"]
        _atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=False))

        # Invalidate stale entries for this slot (mtime changed → new key)
        self._invalidate_cache(slot)
        # Prime cache with the current mtime key
        key = self._cache_key(slot)
        if key is not None:
            self._cache[key] = payload
        return str(path)

    def read(self, slot: str) -> Any | None:
        """Read a JSON slot, auto-unwrapping the v3.0 envelope.

        Returns None if the file is missing or unparseable. Raises
        ``AssetBusError`` for unknown slots and JSONL slots.
        """
        schema = ASSET_SCHEMA.get(slot)
        if not schema:
            raise AssetBusError(f"Unknown asset: {slot}")
        if schema.get("format") == "jsonl":
            raise AssetBusError(
                f"Slot {slot} is JSONL — use read_lines() instead of read()"
            )

        key = self._cache_key(slot)
        if key is not None and key in self._cache:
            return unwrap_envelope(self._cache[key])

        try:
            raw = (self._dir / schema["file"]).read_text(encoding="utf-8")
            parsed = json.loads(raw)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
        if key is not None:
            self._cache[key] = parsed
        return unwrap_envelope(parsed)

    def read_envelope(self, slot: str) -> dict | None:
        """Read raw parsed content (no unwrap) — useful for inspecting metadata.

        Returns None on missing/unparseable file. Raises AssetBusError for
        unknown or JSONL slots.
        """
        schema = ASSET_SCHEMA.get(slot)
        if not schema:
            raise AssetBusError(f"Unknown asset: {slot}")
        if schema.get("format") == "jsonl":
            raise AssetBusError(
                f"Slot {slot} is JSONL — use read_lines() instead of read_envelope()"
            )
        try:
            raw = (self._dir / schema["file"]).read_text(encoding="utf-8")
            return json.loads(raw)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def require(self, slot: str) -> Any:
        """Read a slot, raising ``AssetBusError`` if the file is missing."""
        data = self.read(slot)
        if data is None:
            raise AssetBusError(f"Required asset '{slot}' not found in {self._dir}")
        return data

    # ── JSONL slot API ─────────────────────────────────────────────

    def append_line(self, slot: str, line_obj: dict) -> str:
        """Append one JSONL line to a jsonl-format slot.

        Uses ``open(..., "a")`` (O_APPEND) — mirrors Node.js ``fs.appendFile``
        without ``fsync``. Returns the absolute path written.
        """
        schema = ASSET_SCHEMA.get(slot)
        if not schema:
            raise AssetBusError(f"Unknown asset: {slot}")
        if schema.get("format") != "jsonl":
            raise AssetBusError(
                f"Slot {slot} is not JSONL — use write() instead of append_line()"
            )
        path = self._dir / schema["file"]
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(line_obj, ensure_ascii=False) + "\n")
        self._invalidate_cache(slot)
        return str(path)

    def read_lines(self, slot: str) -> list[dict]:
        """Read all non-blank lines of a jsonl slot as parsed dicts.

        Returns [] on missing file. Raises AssetBusError for unknown or
        non-JSONL slots.
        """
        schema = ASSET_SCHEMA.get(slot)
        if not schema:
            raise AssetBusError(f"Unknown asset: {slot}")
        if schema.get("format") != "jsonl":
            raise AssetBusError(
                f"Slot {slot} is not JSONL — use read() instead of read_lines()"
            )
        try:
            raw = (self._dir / schema["file"]).read_text(encoding="utf-8")
        except FileNotFoundError:
            return []
        return [json.loads(line) for line in raw.split("\n") if line.strip()]

    # ── Introspection ──────────────────────────────────────────────

    def list_asset_names(self) -> list[str]:
        """Return all registered slot names (copy of ASSET_SCHEMA keys)."""
        return list(ASSET_SCHEMA.keys())
