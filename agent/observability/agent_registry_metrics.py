"""OBSRV-01: Agent registry health collector (Plan 67-01 Task 2).

Exposes :func:`get_agent_registry_metrics` -- a pure data-shaping function
that converts the ``(entries, missing_experts, schema_ok)`` triple returned
by :func:`agent.registry_loader.load_agent_registry_with_warnings` into the
6-key snapshot dict consumed by the ``/orchestrator/agents/status`` endpoint
(Plan 67-04) and the CLI ``hermes orchestrator status`` command (Phase 68).

Design notes
------------
* **Pure function.** No I/O, no caching -- the loader already caches via
  ``_REGISTRY_CACHE`` (RESEARCH "Pattern 3 -- on-demand computation").
  The endpoint calls this function live on each HTTP request with a fresh
  ``(entries, missing)`` tuple from the loader.
* **Defensive accessors.** ``e.get("lineage") or {}`` handles three failure
  modes: missing ``lineage`` key, ``lineage: None``, and ``lineage: {}``.
  An entry without a ``name`` key contributes ``""`` rather than crashing.
* **Lineage integrity** is vacuously ``True`` on an empty entries list (no
  entries to fail). Tested by ``test_empty_entries_graceful``.
* **No percentile math here.** This collector emits a *snapshot*, not a
  time-series sample -- the OBSRV-02/03 collectors are the ones that need
  ring-buffer + p50/p95 logic. OBSRV-01's "snapshot" is computed fresh on
  every call (one-shot dict), so the ring-buffer primitive is not used
  inside this module.

Entry shape contract (returned by :func:`get_agent_registry_metrics`):

    {
        "agents_loaded": int,           # len(entries)
        "schema_validation_ok": bool,   # passthrough of schema_ok arg
        "missing_experts": list[str],   # passthrough (order preserved)
        "lineage_integrity_ok": bool,   # _check_lineage(entries)
        "agent_names": list[str],       # sorted names
        "snapshot_at_iso": str,         # ISO-8601 UTC timestamp
    }
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

__all__ = ["get_agent_registry_metrics", "_check_lineage"]


def _now_iso_utc() -> str:
    """Return the current UTC time as an ISO-8601 string.

    Mirrors the codebase convention (see ``agent/credential_pool.py:1164``,
    ``agent/verification_evidence.py:51``). The format is
    ``YYYY-MM-DDTHH:MM:SS.ffffff+00:00`` (the stdlib
    ``datetime.isoformat()`` output for a timezone-aware ``datetime``).
    """
    return datetime.now(timezone.utc).isoformat()


def _check_lineage(entries: list[dict[str, Any]]) -> bool:
    """Return ``True`` iff every entry has complete lineage.

    An entry's lineage is "complete" when both:
        1. ``lineage.source_sha256`` is non-empty (truthy)
        2. ``lineage.transform_rule_id`` is non-empty (truthy)

    Defensive against missing/None lineage fields:
        * ``e.get("lineage")`` returns ``None`` for a missing key
        * ``... or {}`` substitutes an empty dict for ``None``
        * The empty dict then fails both ``.get(...)`` truthiness checks
          -> ``_check_lineage`` returns ``False`` for that entry

    Args:
        entries: List of agent registry entry dicts (parsed YAML from the
            loader). Each entry MAY have a ``lineage`` sub-dict.

    Returns:
        ``True`` if every entry has complete lineage, OR if ``entries`` is
        empty (vacuous truth -- no entries to fail). ``False`` otherwise.
    """
    for entry in entries:
        lineage = entry.get("lineage") or {}
        if not lineage.get("source_sha256") or not lineage.get("transform_rule_id"):
            return False
    return True


def get_agent_registry_metrics(
    entries: list[dict[str, Any]],
    missing_experts: list[str],
    schema_ok: bool,
) -> dict[str, Any]:
    """Build the OBSRV-01 agent-registry health snapshot dict.

    Args:
        entries: The ``entries`` list returned by
            :func:`agent.registry_loader.load_agent_registry_with_warnings`.
            Each entry is a parsed agent YAML dict (has ``name``, optional
            ``lineage`` sub-dict, etc.).
        missing_experts: The ``missing_expert_warnings`` list returned by
            the loader. Propagated verbatim into the snapshot -- order and
            duplicates are preserved (the loader already sorts/dedupes).
        schema_ok: ``True`` if the loader returned without raising
            ``RegistryValidationError``; ``False`` if the caller caught
            such an exception. Propagated verbatim.

    Returns:
        Dict with the 6 OBSRV-01 keys (see module docstring for shape).
        The dict is a fresh object on every call (no shared mutable state).
    """
    # agent_names: sorted alphabetically. Entries without a "name" key
    # contribute "" (defensive .get with default).
    agent_names = sorted(str(entry.get("name", "")) for entry in entries)

    return {
        "agents_loaded": len(entries),
        "schema_validation_ok": bool(schema_ok),
        # Defensive copy -- caller might mutate the missing_experts list
        # after passing it in; we don't want the snapshot to alias it.
        "missing_experts": list(missing_experts),
        "lineage_integrity_ok": _check_lineage(entries),
        "agent_names": agent_names,
        "snapshot_at_iso": _now_iso_utc(),
    }
