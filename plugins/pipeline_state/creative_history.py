"""creative_history.py — CreativeHistoryTracker port.

Reference (direct port source):
    kais-movie-agent/lib/creative-history-tracker.js (272 lines, v3.0 flagship)

This is the v3.0 flagship capability — "Git-for-AIGC-movies MVP". Implements
B4-03/04/05 of v3.0-REQUIREMENTS.md:

* B4-03: DAG + reverse BFS — given a changed upstream content_hash, find all
  downstream derived assets that transitively depend on it.
* B4-04: Blast radius cap (max_blast_radius=20) + depth cap (max_depth=5) +
  performance budget (BFS over 1000-asset chain in <500ms).
* B4-05: Hash-stamping downstream lineage — every stamp records its upstream
  source_hashes so the reverse DAG can be reconstructed.

Stamp record schema (mirrors creative-history-tracker.js:81-87):
    {
        "asset_slot":   str,            # e.g. "final-shots"
        "asset_id":     str,            # e.g. "shot-001"
        "source_hashes": list[str],     # upstream content_hashes
        "content_hash": str,            # this asset's hash
        "timestamp":    str,            # ISO 8601 (UTC)
    }

Pure stdlib. Sync API throughout (D-07 — Phase 32 locked sync for state
modules). No third-party deps, no async.
"""
from __future__ import annotations

import hashlib
import json
import logging
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---- Module constants (mirror creative-history-tracker.js:30-31) ------------
DEFAULT_MAX_BLAST_RADIUS = 20
DEFAULT_MAX_DEPTH = 5


def _compute_hash(value: Any) -> str:
    """SHA-256 hex of canonical JSON.

    Uses ``sort_keys=True`` so hashes are deterministic across runs regardless
    of dict construction order (matches AssetBus._compute_content_hash — the
    two implementations MUST stay in sync so content_hashes are interchangeable
    across modules). NOTE: this function is duplicated from asset_bus.py to
    avoid module-load coupling (AssetBus may not be importable in all test
    environments during Wave 1 parallel execution). If you change the algorithm
    here, change it in asset_bus.py too.
    """
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


class CreativeHistoryTracker:
    """Track creative-asset lineage as a DAG of hash-stamped records.

    The DAG is stored implicitly: every stamp record carries its upstream
    ``source_hashes`` (parent edges) and its own ``content_hash`` (node id).
    A reverse index ``{source_hash: [record, ...]}`` is built lazily on first
    ``find_affected`` call and invalidated on every ``stamp``.

    Mirrors ``kais-movie-agent/lib/creative-history-tracker.js`` class
    ``CreativeHistoryTracker`` (lines 33-233).
    """

    # Class constants (also mirrored as module-level for convenience)
    DEFAULT_MAX_BLAST_RADIUS = DEFAULT_MAX_BLAST_RADIUS
    DEFAULT_MAX_DEPTH = DEFAULT_MAX_DEPTH

    def __init__(
        self,
        *,
        asset_bus: "AssetBus",
        max_blast_radius: int = DEFAULT_MAX_BLAST_RADIUS,
        max_depth: int = DEFAULT_MAX_DEPTH,
    ) -> None:
        if asset_bus is None:
            raise ValueError("CreativeHistoryTracker: asset_bus required")
        self._bus = asset_bus
        self._max_blast_radius = max_blast_radius
        self._max_depth = max_depth
        # Lazy reverse-index cache; invalidated on every stamp().
        self._index_cache: dict[str, list[dict]] | None = None

    # ---- hashing -----------------------------------------------------------

    @staticmethod
    def hash(value: Any) -> str:
        """Static hash helper — same algorithm as AssetBus._compute_content_hash."""
        return _compute_hash(value)

    # ---- stamp -------------------------------------------------------------

    def stamp(self, entry: dict) -> bool:
        """Append a stamp record to the ``creative-history`` slot.

        Mirrors creative-history-tracker.js:74-102.

        ``entry`` keys:
            * ``asset_slot`` (required)
            * ``asset_id`` (required)
            * ``source_hashes`` (optional, list[str])
            * ``content_hash`` (optional, computed from entry if omitted)
            * ``timestamp`` (optional, defaults to now-UTC ISO 8601)

        Returns ``True`` on success, ``False`` on degraded mode (AssetBus
        unreachable). Programmer errors (missing required keys) raise
        ``ValueError``.
        """
        if not entry or not entry.get("asset_id") or not entry.get("asset_slot"):
            raise ValueError(
                "CreativeHistoryTracker.stamp: asset_slot and asset_id required"
            )

        source_hashes = entry.get("source_hashes") or []
        if not isinstance(source_hashes, list):
            source_hashes = list(source_hashes)
        content_hash = entry.get("content_hash") or self.hash(entry)

        record = {
            "asset_slot": entry["asset_slot"],
            "asset_id": entry["asset_id"],
            "source_hashes": source_hashes,
            "content_hash": content_hash,
            "timestamp": entry.get("timestamp")
            or datetime.now(timezone.utc).isoformat(),
        }

        try:
            current = self._bus.read("creative-history") or {
                "shots": [],
                "version": 1,
            }
            if not isinstance(current, dict):
                current = {"shots": [], "version": 1}
            if not isinstance(current.get("shots"), list):
                current["shots"] = []
            current["shots"].append(record)
            self._bus.write("creative-history", current, envelope=True)
            self._index_cache = None  # invalidate
            return True
        except Exception as e:
            # Degraded mode: AssetBus unreachable. Fire-and-forget (warn, no throw).
            logger.warning("CreativeHistoryTracker stamp degraded: %s", e)
            return False

    # ---- reverse BFS -------------------------------------------------------

    def find_affected(self, changed_hash: str) -> dict:
        """Reverse BFS — find all downstream assets transitively dependent on ``changed_hash``.

        Mirrors creative-history-tracker.js:118-176.

        Algorithm:
            1. Build (or reuse cached) reverse index ``{source_hash: [records]}``.
            2. Seed BFS queue with ``changed_hash`` at depth 0.
            3. For each hash, look up records whose ``source_hashes`` contains it.
            4. Each hit's ``content_hash`` becomes the next BFS layer (depth + 1).
            5. Cap by ``max_blast_radius`` (sets ``truncated=True``) and
               ``max_depth`` (stops BFS expansion).

        Returns dict (keys preserved as camelCase where Node.js uses camelCase
        for report compatibility):
            {
                "affected":     list[dict],     # records with depth annotation
                "truncated":    bool,
                "blast_radius": int,            # == len(affected)
                "max_depth":    int,            # deepest layer actually reached
                "cap":          {"maxBlastRadius": int, "maxDepth": int},
            }
        """
        index = self._build_index()

        affected: list[dict] = []
        seen_hashes: set[str] = {changed_hash}
        seen_asset_ids: set[str] = set()
        truncated = False
        max_depth_reached = 0

        # collections.deque.popleft() is O(1); list.pop(0) is O(N).
        queue: deque[tuple[str, int]] = deque([(changed_hash, 0)])

        while queue:
            h, depth = queue.popleft()
            if depth >= self._max_depth:
                continue
            derived_records = index.get(h, [])
            for record in derived_records:
                asset_key = f"{record['asset_slot']}:{record['asset_id']}"
                if asset_key in seen_asset_ids:
                    continue
                seen_asset_ids.add(asset_key)
                if len(affected) >= self._max_blast_radius:
                    truncated = True
                    break
                affected.append(
                    {
                        "asset_slot": record["asset_slot"],
                        "asset_id": record["asset_id"],
                        "content_hash": record["content_hash"],
                        "source_hashes": record["source_hashes"],
                        "timestamp": record["timestamp"],
                        "depth": depth + 1,
                    }
                )
                if depth + 1 > max_depth_reached:
                    max_depth_reached = depth + 1
                if record["content_hash"] not in seen_hashes:
                    seen_hashes.add(record["content_hash"])
                    queue.append((record["content_hash"], depth + 1))
            if truncated:
                break

        return {
            "affected": affected,
            "truncated": truncated,
            "blast_radius": len(affected),
            "max_depth": max_depth_reached,
            "cap": {
                "maxBlastRadius": self._max_blast_radius,
                "maxDepth": self._max_depth,
            },
        }

    # ---- batch diff --------------------------------------------------------

    def diff(self, changed_hashes: list[str]) -> dict:
        """Batch diff: union of affected across multiple changed hashes.

        Mirrors creative-history-tracker.js:183-201.

        Returns dict:
            {
                "affected":  list[dict],    # union, deduplicated by asset_key
                "truncated": bool,          # True if ANY per-hash result truncated
                "per_hash":  dict[str, dict],  # changed_hash -> find_affected result
            }
        """
        if not changed_hashes:
            return {"affected": [], "truncated": False, "per_hash": {}}

        all_map: dict[str, dict] = {}  # asset_key -> record (union, dedup)
        truncated = False
        per_hash: dict[str, dict] = {}

        for h in changed_hashes:
            r = self.find_affected(h)
            per_hash[h] = r
            if r["truncated"]:
                truncated = True
            for a in r["affected"]:
                key = f"{a['asset_slot']}:{a['asset_id']}"
                if key not in all_map:
                    all_map[key] = a

        return {
            "affected": list(all_map.values()),
            "truncated": truncated,
            "per_hash": per_hash,
        }

    # ---- reverse-index build -----------------------------------------------

    def _build_index(self) -> dict[str, list[dict]]:
        """Build reverse index ``{source_hash: [record, ...]}`` from creative-history.

        Mirrors creative-history-tracker.js:209-233. Cached; invalidated on
        every ``stamp()``.
        """
        if self._index_cache is not None:
            return self._index_cache

        try:
            data = self._bus.read("creative-history") or {"shots": []}
        except Exception as e:
            logger.warning("CreativeHistoryTracker _build_index read failed: %s", e)
            data = {"shots": []}

        records = data.get("shots") if isinstance(data, dict) else None
        if not isinstance(records, list):
            records = []

        by_source: dict[str, list[dict]] = {}
        for record in records:
            if not isinstance(record, dict) or not record.get("content_hash"):
                continue
            sources = record.get("source_hashes") or []
            if not isinstance(sources, list):
                continue
            for src in sources:
                by_source.setdefault(src, []).append(record)

        self._index_cache = by_source
        return by_source


def write_blast_radius_report(
    find_affected_result: dict,
    output_path: str | Path,
    changed_hash: str | None = None,
) -> str:
    """Write a blast-radius-report JSON for operator review.

    Mirrors creative-history-tracker.js:253-272 (``writeBlastRadiusReport``).

    Report keys: ``generated_at``, ``changed_hash``, ``affected_count``,
    ``truncated``, ``blast_radius``, ``max_depth``, ``cap``, ``affected``,
    ``note``.
    """
    cap = find_affected_result.get("cap") or {}
    truncated = bool(find_affected_result.get("truncated"))
    if truncated:
        note = (
            f"Scope exceeded maxBlastRadius={cap.get('maxBlastRadius')}. "
            "Review manually or re-run tracker.find_affected(hash, "
            "max_blast_radius=N)."
        )
    else:
        note = "All affected assets captured."

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "changed_hash": changed_hash,
        "affected_count": len(find_affected_result.get("affected") or []),
        "truncated": truncated,
        "blast_radius": find_affected_result.get("blast_radius", 0),
        "max_depth": find_affected_result.get("max_depth", 0),
        "cap": cap,
        "affected": find_affected_result.get("affected") or [],
        "note": note,
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return str(path)
