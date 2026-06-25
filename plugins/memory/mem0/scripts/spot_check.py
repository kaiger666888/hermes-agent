"""5-query spot-check for ingested openclaw memories in the mem0 backend.

Issues 5 hardcoded queries (mixed CN/EN to match the openclaw memory corpus
shape) and prints the top-3 results for each. Run after
``batch_ingest.py`` to verify the migration succeeded.

Usage::

    # Inspect the 5 queries without API access
    python3 plugins/memory/mem0/scripts/spot_check.py --list-queries

    # Live spot-check (requires MEM0_API_KEY)
    python3 plugins/memory/mem0/scripts/spot_check.py
    python3 plugins/memory/mem0/scripts/spot_check.py --top-k 5 --quiet
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

# --- sys.path bootstrap so the script runs standalone AND as a module ---------
_REPO_ROOT = Path(__file__).resolve().parents[4]  # scripts -> mem0 -> memory -> plugins -> root
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

logger = logging.getLogger("mem0.spot_check")

# --- The 5 spot-check queries -------------------------------------------------
# Mixed CN/EN keywords chosen to match the corpus shape observed in
# ~/.openclaw/workspace/memory/*.md (e.g. 2026-05-26.md). Each entry is a
# (topic, query) pair. Topics are the SC#3 named coverage areas.
QUERIES: list[tuple[str, str]] = [
    ("AIGC deployment", "ComfyUI systemd 配置 RTX 3090 GPU 部署 AIGC"),
    ("ComfyUI", "ComfyUI 工作流参数 CUDA_VISIBLE_DEVICES workflow"),
    ("Trellis", "Trellis 项目结构 测试"),
    ("ACE-Step", "ACE-Step 音频生成 music generation"),
    ("CosyVoice", "CosyVoice TTS 模型 voice cloning"),
]


# --- Config + client helpers (mirrors batch_ingest.py) ------------------------
def _load_config_safe() -> dict:
    """Load mem0 provider config (env vars + ~/.hermes/mem0.json precedence).

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
            "'python3 plugins/memory/mem0/scripts/spot_check.py'."
        ) from exc
    return _load_config()


def _build_client(config: dict):
    """Construct a mem0 MemoryClient. Raises RuntimeError if api_key is empty."""
    api_key = config.get("api_key", "")
    if not api_key:
        raise RuntimeError(
            "MEM0_API_KEY not set. Run with --list-queries, or set MEM0_API_KEY in ~/.hermes/.env"
        )
    from mem0 import MemoryClient  # lazy import

    return MemoryClient(api_key=api_key)


def _unwrap_results(response: Any) -> list:
    """Normalize Mem0 API response — v2 wraps results in {"results": [...]}."""
    if isinstance(response, dict):
        return response.get("results", [])
    if isinstance(response, list):
        return response
    return []


# --- Core spot-check ----------------------------------------------------------
def run_spot_check(client, user_id: str, *, rerank: bool = True, top_k: int = 3) -> list[dict]:
    """Issue each of the 5 hardcoded queries against the mem0 backend.

    Returns a list of ``{"topic", "query", "results", "error"}`` dicts. One
    failed query does not abort the rest — its error string is recorded in the
    result dict (so the operator can see partial-failure states).
    """
    out: list[dict] = []
    for topic, query in QUERIES:
        result: dict[str, Any] = {"topic": topic, "query": query, "results": [], "error": None}
        try:
            response = client.search(
                query=query,
                filters={"user_id": user_id},
                rerank=rerank,
                top_k=top_k,
            )
            entries = _unwrap_results(response)
            result["results"] = [
                {
                    "memory": e.get("memory", ""),
                    "score": e.get("score", 0),
                }
                for e in entries
            ]
        except Exception as exc:  # noqa: BLE001 — per-query continue
            result["error"] = str(exc)
            logger.warning("Query '%s' failed: %s", topic, exc)
        out.append(result)
    return out


# --- CLI ----------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Spot-check 5 hardcoded queries against the mem0 backend. "
            "Verifies openclaw memory ingestion succeeded (run after batch_ingest.py). "
            "Topics: AIGC deployment / ComfyUI / Trellis / ACE-Step / CosyVoice."
        ),
    )
    parser.add_argument(
        "--list-queries",
        action="store_true",
        help="Print the 5 (topic, query) pairs and exit. No API access required.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Max results per query (default: 3).",
    )
    parser.add_argument(
        "--no-rerank",
        action="store_true",
        help="Disable reranking (faster, less precise).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-result detail; print summary line only.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.list_queries:
        for topic, query in QUERIES:
            print(f"{topic}\t{query}")
        return 0

    config = _load_config_safe()
    if not config.get("api_key"):
        print(
            "MEM0_API_KEY not set. Run with --list-queries, or set MEM0_API_KEY in ~/.hermes/.env",
            file=sys.stderr,
        )
        return 1

    client = _build_client(config)
    user_id = config.get("user_id", "hermes-user")
    rerank = not args.no_rerank

    results = run_spot_check(client, user_id, rerank=rerank, top_k=args.top_k)

    total_returned = 0
    for i, r in enumerate(results, 1):
        if args.quiet:
            total_returned += len(r["results"])
            continue
        print(f"=== [{i}/{len(QUERIES)}] {r['topic']} ===")
        print(f"Query: {r['query']}")
        if r["error"]:
            print(f"--- ERROR: {r['error']} ---")
            print()
            continue
        print(f"--- top {len(r['results'])} results ---")
        for entry in r["results"]:
            mem = entry["memory"]
            score = entry["score"]
            print(f"  - {mem} (score={score})")
        total_returned += len(r["results"])
        print()

    print(
        f"Spot-check complete: {len(QUERIES)} queries issued, "
        f"{total_returned} total results returned"
    )
    if total_returned == 0:
        print(
            "Hint: empty result sets suggest either ingestion has not run yet, "
            "or the topics are not in the ingested corpus. Run batch_ingest.py first."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
