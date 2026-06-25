"""Idempotent batch ingestion of openclaw memory notes into mem0 backend.

Enumerates ``~/.openclaw/workspace/memory/*.md`` (124 files as of 2026-06-25),
computes a SHA-256 content hash per file, and ingests each file into the
configured mem0 backend unless an entry with the same ``content_hash`` is
already present in the user's memory scope (idempotent re-run).

Reuses ``plugins.memory.mem0._load_config`` so this script inherits the same
env-var + ``~/.hermes/mem0.json`` precedence as the runtime plugin.

Usage::

    # Dry-run (no API key needed) — enumerate + hash only
    python3 plugins/memory/mem0/scripts/batch_ingest.py --dry-run
    python3 plugins/memory/mem0/scripts/batch_ingest.py --dry-run --limit 3

    # Live ingestion (requires MEM0_API_KEY or ~/.hermes/mem0.json)
    python3 plugins/memory/mem0/scripts/batch_ingest.py
    python3 plugins/memory/mem0/scripts/batch_ingest.py --limit 5
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import sys
from pathlib import Path
from typing import Any

# --- sys.path bootstrap so the script runs standalone AND as a module ---------
_REPO_ROOT = Path(__file__).resolve().parents[4]  # scripts -> mem0 -> memory -> plugins -> root
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

logger = logging.getLogger("mem0.batch_ingest")

# --- Constants ----------------------------------------------------------------
DEFAULT_SOURCE_DIR = Path.home() / ".openclaw" / "workspace" / "memory"
MIGRATED_AT = "2026-06-25"
EXPECTED_FILE_COUNT = 124  # 36-CONTEXT.md correction: actual count, not ROADMAP's 133


# --- Config + client helpers --------------------------------------------------
def _load_config_safe() -> dict:
    """Load the mem0 provider config (env vars + ~/.hermes/mem0.json precedence).

    Imports the existing loader from the plugin module so config logic is never
    duplicated. Wrapped in try/except to give a clean error if invoked outside
    the repo tree or with a broken install.
    """
    try:
        from plugins.memory.mem0 import _load_config
    except ImportError as exc:
        raise RuntimeError(
            "Could not import plugins.memory.mem0._load_config. "
            "Run from the hermes-agent repo root, e.g. "
            "'python3 plugins/memory/mem0/scripts/batch_ingest.py'."
        ) from exc
    return _load_config()


def _build_client(config: dict):
    """Construct a mem0 MemoryClient. Raises RuntimeError if api_key is empty."""
    api_key = config.get("api_key", "")
    if not api_key:
        raise RuntimeError(
            "MEM0_API_KEY not set. Run with --dry-run, or set MEM0_API_KEY in ~/.hermes/.env"
        )
    from mem0 import MemoryClient  # lazy import — only needed for live runs

    return MemoryClient(api_key=api_key)


# --- Ingestion primitives -----------------------------------------------------
def _compute_hash(text: str) -> str:
    """SHA-256 hex digest of the file body (UTF-8 encoded)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _enumerate_files(source_dir: Path) -> list[Path]:
    """Return sorted *.md paths under source_dir. Warns if count != expected."""
    files = sorted(source_dir.glob("*.md"))
    if len(files) != EXPECTED_FILE_COUNT:
        logger.warning(
            "Expected %d .md files under %s, found %d. Proceeding anyway.",
            EXPECTED_FILE_COUNT, source_dir, len(files),
        )
    return files


def _get_existing_hashes(client, user_id: str) -> set[str]:
    """Pull all current memory entries for the user and extract their content_hash metadata.

    Used for idempotency: any file whose hash is already in this set is skipped.
    """
    response = client.get_all(filters={"user_id": user_id})
    # Normalize the v1/v2 response shape (dict wrapper vs plain list).
    if isinstance(response, dict):
        entries = response.get("results", [])
    elif isinstance(response, list):
        entries = response
    else:
        entries = []

    hashes: set[str] = set()
    legacy_count = 0
    for entry in entries:
        meta = entry.get("metadata", {}) or {}
        h = meta.get("content_hash")
        if h:
            hashes.add(h)
        else:
            legacy_count += 1
    if legacy_count:
        logger.info(
            "Found %d existing memory entries without content_hash metadata (legacy).",
            legacy_count,
        )
    return hashes


def _unwrap_response(response: Any) -> Any:
    """Pass-through helper for normalizing mem0 add() responses (kept for symmetry)."""
    if isinstance(response, dict):
        return response.get("results", response)
    return response


# --- Core ingest function -----------------------------------------------------
def ingest(
    source_dir: Path,
    *,
    dry_run: bool,
    limit: int | None,
    client=None,
    config: dict | None = None,
    quiet: bool = False,
) -> dict:
    """Run the batch ingestion. Returns a counts dict.

    Counts: ``total`` (files examined), ``ingested``, ``skipped`` (already present),
    ``failed`` (raised during add).

    In dry-run mode each file's ``{path}\\t{sha256}`` line is printed to stdout
    unless ``quiet`` is set (operator log / audit trail — T-36-03 mitigation).
    """
    files = _enumerate_files(source_dir)
    if limit is not None:
        files = files[:limit]

    counts = {"total": len(files), "ingested": 0, "skipped": 0, "failed": 0}

    if dry_run:
        for path in files:
            body = path.read_text(encoding="utf-8")
            h = _compute_hash(body)
            if not quiet:
                print(f"{path}\t{h}")
        return counts

    # Live path: build client if not supplied by caller
    if client is None:
        if config is None:
            config = _load_config_safe()
        client = _build_client(config)

    user_id = (config or {}).get("user_id", "hermes-user")
    agent_id = (config or {}).get("agent_id", "hermes")

    existing_hashes = _get_existing_hashes(client, user_id)
    logger.info("Loaded %d existing content_hash entries from backend.", len(existing_hashes))

    for path in files:
        try:
            body = path.read_text(encoding="utf-8")
            h = _compute_hash(body)
            if h in existing_hashes:
                counts["skipped"] += 1
                continue
            client.add(
                messages=[{"role": "user", "content": body}],
                user_id=user_id,
                agent_id=agent_id,
                metadata={
                    "content_hash": h,
                    "source_path": str(path),
                    "migrated_at": MIGRATED_AT,
                },
            )
            existing_hashes.add(h)
            counts["ingested"] += 1
        except Exception as exc:  # noqa: BLE001 — per-file continue is intentional (T-36-04 mitigation)
            logger.warning("Failed to ingest %s: %s", path, exc)
            counts["failed"] += 1

    return counts


# --- CLI ----------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Idempotent batch ingestion of openclaw memory notes into mem0 backend. "
            "Re-runs produce zero new entries when files are unchanged (keyed on SHA-256 "
            "content_hash stored in mem0 metadata)."
        ),
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help=f"Directory of *.md source files (default: {DEFAULT_SOURCE_DIR}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Enumerate + hash only. No mem0 API calls; works without MEM0_API_KEY.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N files (sorted by name). Useful for testing.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-file output in dry-run mode.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Load config up front so we can fail fast on missing api_key for live runs
    config = _load_config_safe()

    if not args.dry_run and not config.get("api_key"):
        print(
            "MEM0_API_KEY not set. Run with --dry-run, or set MEM0_API_KEY in ~/.hermes/.env",
            file=sys.stderr,
        )
        return 1

    if not args.source_dir.exists():
        print(f"Source directory does not exist: {args.source_dir}", file=sys.stderr)
        return 1

    client = None
    if not args.dry_run:
        client = _build_client(config)

    counts = ingest(
        args.source_dir,
        dry_run=args.dry_run,
        limit=args.limit,
        client=client,
        config=config,
        quiet=args.quiet,
    )

    if args.dry_run:
        print(
            f"DRY-RUN: would ingest {counts['total']} files "
            f"(backend presence unknown without API access)",
            file=sys.stderr,
        )
    else:
        print(
            f"Ingestion complete: total={counts['total']} "
            f"ingested={counts['ingested']} skipped={counts['skipped']} "
            f"failed={counts['failed']}"
        )

    return 0 if counts["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
