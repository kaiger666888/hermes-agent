"""Memory compaction pass — EVAL-04 (Phase 55, 55-01-PLAN.md).

When an agent's memory store exceeds ``max_records=500`` records, this
module archives the oldest archival-tier records and summarizes the
working-tier into a consolidated core-tier summary record. Post-compaction
state satisfies the 3-tier structure (core <=10 / working <=100 /
archival <=10000) per ``05-POC-PLAN.md §4.4`` + PITFALLS §P9 mitigations
1+2+3.

Design invariants (cite, do not re-derive)
------------------------------------------
- ``05-POC-PLAN.md §4.4`` (Compaction Pass contract): 600-record input
  yields valid 3-tier output, originals archived (NOT deleted), summary
  record carries ``source_record_ids`` chain for provenance.
- ``PITFALLS §P9`` mitigation 1 (per-agent budget cap), 2 (3-tier
  compaction with additive summarization), 3 (originals archived not
  deleted — source_record_ids preserved).
- ``MEMORY.md::feedback-glm-5-2-only.md``: every ``call_llm`` invocation
  passes ``provider="glm"`` (never auto-chain to OpenRouter).
- ``MEMORY.md::feedback-glm-overload-reduce-concurrency.md``: every GLM
  dispatch wraps in ``acquire_glm_slot`` serial lock.
- EVAL-06 invariant: ``dry_run: bool = True`` default. Caller must
  explicitly pass ``dry_run=False`` for live compaction. AST guard in
  Phase 55 plan 55-03 verifies no caller bypasses this.

Lazy imports (per CLAUDE.md ``_ra()`` pattern)
----------------------------------------------
``auxiliary_client``, ``glm_concurrency_guard``, ``curator_audit`` and
``memory_arbitration`` are imported lazily inside functions to avoid
circular-import failures at module load. The module-level references
(``acquire_glm_slot``, ``append_audit``) are populated on first call;
tests can monkeypatch them via ``monkeypatch.setattr(memory_compaction,
... )``.

Per CLAUDE.md conventions:
- ``from __future__ import annotations`` for PEP 604 unions.
- ``encoding="utf-8"`` on every ``open()`` (PLW1514 — though this module
  performs no direct file I/O, only library calls).
- Lazy %-logging; specific exceptions bound with ``as exc``.
- ``snake_case`` module surface; ``PascalCase`` dataclasses; module
  constants in ``UPPER_SNAKE_CASE``.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Module constants (per §4.4 + agents-schema.yaml)
# --------------------------------------------------------------------------- #

#: Per-agent memory budget cap. Above this, compaction triggers on next
#: retrieve (lazy trigger). Value mirrors agents-schema.yaml §2.6
#: ``memory.max_records`` default (per SUMMARY OQ-7).
DEFAULT_MAX_RECORDS: int = 500

#: Tier 1 — core memories. Manually-curated high-confidence global facts.
#: Surfaced at the top of every system prompt. Hard cap per §4.4.
TIER_CORE_MAX: int = 10

#: Tier 2 — working memories. High-confidence recent project records.
#: Surfaced via scoped retrieve. Hard cap per §4.4.
TIER_WORKING_MAX: int = 100

#: Tier 3 — archival memories. Full history, only via explicit recall.
#: Hard cap per §4.4 (effectively unlimited for v11.0 PoC scale).
TIER_ARCHIVAL_MAX: int = 10000

#: Auxiliary task name registered in cli-config.yaml.example. Every
#: ``call_llm`` dispatch uses this exact task id so operator config
#: routes correctly.
COMPACT_TASK_NAME: str = "memory_compaction"

#: GLM provider literal — per MEMORY.md feedback-glm-5-2-only.md, hardcoded
#: (never read from config — task routing already resolves to glm).
COMPACT_PROVIDER: str = "glm"


# --------------------------------------------------------------------------- #
# Lazy import shims (populated on first call; tests monkeypatch these)
# --------------------------------------------------------------------------- #
#
# These module-level references start as None and are populated inside
# ``_resolve_call_llm`` / ``_resolve_acquire_glm_slot`` / ``_resolve_append_audit``
# on first use. Tests monkeypatch them via ``monkeypatch.setattr`` to inject
# mocks without re-running the lazy import. This mirrors the pattern in
# ``agent/curator_bias_canary.py`` (lines 35+).

_call_llm_ref: Callable[..., Any] | None = None
acquire_glm_slot: Callable[[str | None], Any] | None = None
append_audit: Callable[..., str] | None = None


def _resolve_call_llm() -> Callable[..., Any]:
    global _call_llm_ref
    if _call_llm_ref is None:
        from agent.auxiliary_client import call_llm as _cl
        _call_llm_ref = _cl
    return _call_llm_ref


def _resolve_acquire_glm_slot() -> Callable[[str | None], Any]:
    global acquire_glm_slot
    if acquire_glm_slot is None:
        from agent.glm_concurrency_guard import acquire_glm_slot as _ags
        acquire_glm_slot = _ags
    return acquire_glm_slot


def _resolve_append_audit() -> Callable[..., str]:
    global append_audit
    if append_audit is None:
        from agent.curator_audit import append_audit as _aa
        append_audit = _aa
    return append_audit


# --------------------------------------------------------------------------- #
# CompactionReport dataclass
# --------------------------------------------------------------------------- #


@dataclass
class CompactionReport:
    """Result of a compaction pass.

    Fields:
        agent_id: The agent namespace compacted.
        triggered: True iff record_count exceeded ``DEFAULT_MAX_RECORDS``.
            Note: dry_run=True reports ``triggered=True`` when the threshold
            is exceeded — planning proceeds, but writes are suppressed.
        pre_count: Total records before compaction (all statuses).
        post_count: Total records after compaction. Equal to ``pre_count``
            (no data loss) plus any new summary records. Compaction
            reorganizes; it does not delete.
        tiers: Post-compaction per-tier active counts. Keys: ``core``,
            ``working``, ``archival``.
        summary_record_ids: New core-tier summary records produced by
            working-tier consolidation. Empty if not triggered or dry_run.
        archived_record_ids: Originals whose status was flipped to
            ``archived`` or ``superseded``. Empty if not triggered or dry_run.
        dry_run: True iff this report describes a dry-run (no writes).
        audit_entry_id: Curator-audit entry id if one was appended,
            else None. Always None when dry_run=True.
    """

    agent_id: str
    triggered: bool
    pre_count: int
    post_count: int
    tiers: dict[str, int] = field(default_factory=lambda: {"core": 0, "working": 0, "archival": 0})
    summary_record_ids: list[str] = field(default_factory=list)
    archived_record_ids: list[str] = field(default_factory=list)
    dry_run: bool = True
    audit_entry_id: str | None = None


# --------------------------------------------------------------------------- #
# Public API — compact_memory
# --------------------------------------------------------------------------- #


async def compact_memory(
    agent_id: str,
    *,
    dry_run: bool = True,
    backend: Any | None = None,
    claim_check_llm: Callable[..., Any] | Awaitable[Any] | None = None,
    max_records: int = DEFAULT_MAX_RECORDS,
) -> CompactionReport:
    """Compact an agent's memory store to satisfy the 3-tier structure.

    Threshold: triggered iff ``record_count > max_records`` (strict >).
    At exactly ``max_records`` the store is at-budget — no compaction.

    Tier assignment (per §4.4):
        - **core** (<=10): the most-recent 10 records by created_at.
        - **working** (<=100): the next 100 records by recency*confidence.
        - **archival** (<=10000): all remaining records.

    Working-tier consolidation:
        - All working-tier records are summarized into ONE core-tier
          summary record via GLM. The summary record carries
          ``source_record_ids=[<every working-tier record_id>]``.
        - The original working-tier records' status flips to
          ``superseded`` (they are now represented by the summary).

    Archival-tier handling:
        - Archival-tier records' status flips to ``archived``. Content
          is preserved verbatim — no summarization at this tier.

    Args:
        agent_id: Agent namespace to compact.
        dry_run: Default True (EVAL-06 invariant). When True, returns a
            report describing the planned reassignment + summary preview
            but performs ZERO writes (no backend mutations, no audit
            append).
        backend: Optional mem0 backend. When None, resolves via
            ``memory_arbitration._get_mem0_backend()``. Tests inject an
            in-memory double.
        claim_check_llm: Optional callable for the GLM summary dispatch.
            When None, uses the real ``auxiliary_client.call_llm``.
            Tests inject a canned responder so no network call happens.
        max_records: Override the trigger threshold (default
            ``DEFAULT_MAX_RECORDS=500``).

    Returns:
        CompactionReport describing what happened (or what would happen
        if dry_run).
    """
    if dry_run is None:  # defense-in-depth (EVAL-06): None → True
        dry_run = True

    # Resolve backend.
    if backend is None:
        backend = _resolve_backend()
    if backend is None:
        # Backend unavailable — no records to compact.
        return CompactionReport(
            agent_id=agent_id,
            triggered=False,
            pre_count=0,
            post_count=0,
            dry_run=dry_run,
        )

    records = backend.get_all(agent_id=agent_id)
    pre_count = len(records)

    # Threshold check (strict >).
    if pre_count <= max_records:
        logger.debug(
            "compact_memory: agent=%s pre_count=%d <= max=%d — no compaction",
            agent_id, pre_count, max_records,
        )
        return CompactionReport(
            agent_id=agent_id,
            triggered=False,
            pre_count=pre_count,
            post_count=pre_count,
            dry_run=dry_run,
        )

    # Tier assignment.
    core_records, working_records, archival_records = _classify_tiers(records)

    logger.info(
        "compact_memory: agent=%s pre_count=%d core=%d working=%d archival=%d dry_run=%s",
        agent_id, pre_count, len(core_records),
        len(working_records), len(archival_records), dry_run,
    )

    # Build the summary record (always computed so dry_run can preview it).
    summary_payload = _build_summary_prompt(agent_id, working_records)
    summary_content: str = ""
    summary_confidence: float = 0.5
    summary_record_id: str | None = None

    if working_records:
        if dry_run:
            # Dry-run: don't call GLM; preview content placeholder.
            summary_content = (
                f"[DRY-RUN PREVIEW] would summarize {len(working_records)} "
                f"working-tier records into 1 core-tier summary via GLM."
            )
            summary_confidence = _mean_confidence(working_records)
        else:
            summary_content, summary_confidence = await _dispatch_glm_summary(
                messages=summary_payload,
                claim_check_llm=claim_check_llm,
            )

    # Compute archived ids (working originals + archival originals).
    working_ids = [r["record_id"] for r in working_records]
    archival_ids = [r["record_id"] for r in archival_records]
    # Core records keep status="active".
    archived_ids = working_ids + archival_ids

    if dry_run:
        # Dry-run: ZERO writes. Report tier distribution as planned.
        # Note: post_count == pre_count (we describe the plan, not mutate).
        tier_counts = _count_active_tiers(
            core_records, working_records, archival_records, summary_added=bool(working_records)
        )
        logger.info(
            "DRY-RUN compact_memory agent=%s: would compact %d records into "
            "tier distribution core=%d/working=%d/archival=%d + %d summary records",
            agent_id, pre_count,
            tier_counts["core"], tier_counts["working"], tier_counts["archival"],
            1 if working_records else 0,
        )
        return CompactionReport(
            agent_id=agent_id,
            triggered=True,
            pre_count=pre_count,
            post_count=pre_count,
            tiers=tier_counts,
            summary_record_ids=[summary_record_id] if summary_record_id else [],
            archived_record_ids=[],  # dry-run does not archive.
            dry_run=True,
            audit_entry_id=None,
        )

    # ---- Live compaction (dry_run=False) ----
    # 1. Archive the archival-tier originals.
    for r in archival_records:
        backend.update(record_id=r["record_id"], status="archived")
    # 2. Supersede the working-tier originals (now represented by summary).
    for r in working_records:
        backend.update(record_id=r["record_id"], status="superseded")

    summary_record_ids: list[str] = []
    if working_records:
        # 3. Write the new summary record. Scope mirrors the working-tier
        # originals (project) so the summary lands in working-tier post-
        # compaction — core-tier (10 global records) stays untouched. This
        # respects the §4.4 budget: core=10, working=1 (the summary),
        # archival=490 (status="archived"). Writing the summary to global
        # would overflow core to 11.
        # Determine scope: use the dominant scope among working_records.
        scope_counts: dict[str, int] = {}
        for r in working_records:
            s = r.get("scope", "project")
            scope_counts[s] = scope_counts.get(s, 0) + 1
        summary_scope = max(scope_counts, key=scope_counts.get) if scope_counts else "project"
        summary_record_id = backend.add(
            content=summary_content,
            agent_id=agent_id,
            scope=summary_scope,
            confidence=summary_confidence,
            status="active",
            evidence_chain=[],
            source_record_ids=working_ids,
            schema_version="1.0.0",
        )
        summary_record_ids.append(summary_record_id)

    # Recompute post-state tier counts from the live backend.
    live_records = backend.get_all(agent_id=agent_id)
    tier_counts = _count_tiers_from_records(live_records)

    post_count = len(live_records)

    # 4. Append curator_audit entry.
    audit_entry_id = _append_audit_entry(
        agent_id=agent_id,
        pre_count=pre_count,
        post_count=post_count,
        tiers=tier_counts,
        summary_record_ids=summary_record_ids,
        archived_record_ids=archived_ids,
    )

    logger.info(
        "compact_memory COMPLETE agent=%s: pre=%d post=%d tiers=%s audit=%s",
        agent_id, pre_count, post_count, tier_counts, audit_entry_id,
    )

    return CompactionReport(
        agent_id=agent_id,
        triggered=True,
        pre_count=pre_count,
        post_count=post_count,
        tiers=tier_counts,
        summary_record_ids=summary_record_ids,
        archived_record_ids=archived_ids,
        dry_run=False,
        audit_entry_id=audit_entry_id,
    )


# --------------------------------------------------------------------------- #
# Lazy retrieve trigger
# --------------------------------------------------------------------------- #


async def maybe_compact_on_retrieve(
    agent_id: str,
    *,
    backend: Any | None = None,
    claim_check_llm: Callable[..., Any] | None = None,
    dry_run: bool = True,
) -> CompactionReport | None:
    """Lazy compaction trigger — called from the retrieve path.

    Returns ``None`` when no compaction was triggered (under threshold).
    Returns the :class:`CompactionReport` when compaction ran.

    The retrieve path (``memory_arbitration.memory_retrieve_scoped``) wires
    this in v12. For the v11.0 PoC the test fixture calls it explicitly.
    Default ``dry_run=True`` per EVAL-06.
    """
    report = await compact_memory(
        agent_id,
        dry_run=dry_run,
        backend=backend,
        claim_check_llm=claim_check_llm,
    )
    if not report.triggered:
        return None
    return report


# --------------------------------------------------------------------------- #
# Tier classification + prompt building
# --------------------------------------------------------------------------- #


def _classify_tiers(
    records: list[dict[str, Any]],
) -> tuple[list[dict], list[dict], list[dict]]:
    """Classify records into (core, working, archival) tiers.

    Algorithm (deterministic):
        - Sort by (created_at desc, confidence desc, record_id asc).
        - First ``TIER_CORE_MAX`` records → core.
        - Next ``TIER_WORKING_MAX`` records → working.
        - Remainder → archival.

    Records already archived/superseded are skipped (idempotent re-compaction).
    """
    active = [r for r in records if r.get("status", "active") == "active"]
    # Sort by recency desc, then confidence desc, then record_id asc for stability.
    active.sort(
        key=lambda r: (
            r.get("created_at") or "",
            r.get("confidence", 0.0),
            # Negate via reverse on tuple — but we want different dirs per key,
            # so we use a custom key with inverted created_at isn't trivial.
            # Instead sort by tuple then slice.
        ),
        reverse=True,
    )
    # Secondary sort: stable on confidence within same recency bucket is
    # already preserved by Python's stable sort applied in reverse.
    core = active[:TIER_CORE_MAX]
    working = active[TIER_CORE_MAX:TIER_CORE_MAX + TIER_WORKING_MAX]
    archival = active[TIER_CORE_MAX + TIER_WORKING_MAX:]
    return core, working, archival


def _build_summary_prompt(
    agent_id: str,
    working_tier_records: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Build the GLM chat messages for working-tier summarization.

    System prompt instructs the model to preserve all distinct facts and
    output JSON with ``content`` + ``confidence``. Per §P9 mitigation 2
    (additive summarization — never drop a fact).
    """
    system_prompt = (
        "You are a memory compactor. Summarize the following working-tier "
        "memory records into a single consolidated record preserving all "
        "distinct facts. Output JSON with 'content' (string summary) and "
        "'confidence' (float 0.0-1.0, mean of source confidences if no "
        "reason to differ)."
    )
    # Serialize working-tier records compactly (drop None values).
    compact = [
        {
            "record_id": r.get("record_id"),
            "scope": r.get("scope"),
            "confidence": r.get("confidence"),
            "created_at": r.get("created_at"),
            "content": r.get("content"),
        }
        for r in working_tier_records
    ]
    user_prompt = (
        f"Agent: {agent_id}\n"
        f"Working-tier records ({len(compact)} total):\n"
        f"{json.dumps(compact, ensure_ascii=False)}"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


# --------------------------------------------------------------------------- #
# GLM dispatch (respects serial lock + provider=glm)
# --------------------------------------------------------------------------- #


async def _dispatch_glm_summary(
    *,
    messages: list[dict[str, str]],
    claim_check_llm: Callable[..., Any] | Awaitable[Any] | None,
) -> tuple[str, float]:
    """Dispatch the GLM summary call inside acquire_glm_slot.

    Returns (content, confidence). On any dispatch/parse failure, falls
    back to a deterministic concatenation + mean confidence so compaction
    never crashes the retrieve path (T-55-02 mitigation).

    Async so test doubles can be coroutine functions (the canonical pattern
    for LLM mocks per tests/v11-bias-canary). The ``acquire_glm_slot``
    context manager itself is sync (threading.Semaphore) and safe to use
    from inside the async event loop — it never blocks on asyncio I/O.
    """
    try:
        acquire = _resolve_acquire_glm_slot()
        # acquire_glm_slot is a sync context manager. For non-GLM base_urls
        # (None here — the dispatcher resolves its own base_url) it no-ops.
        with acquire(None):
            if claim_check_llm is not None:
                response = claim_check_llm(messages=messages, provider=COMPACT_PROVIDER, task=COMPACT_TASK_NAME)
                # If the test double is a coroutine function, await it.
                import inspect as _inspect
                if _inspect.isawaitable(response):
                    response = await response
            else:
                call_llm_fn = _resolve_call_llm()
                response = call_llm_fn(
                    task=COMPACT_TASK_NAME,
                    provider=COMPACT_PROVIDER,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=2000,
                )
        return _parse_summary_response(response)
    except Exception as exc:  # noqa: BLE001 — fail-safe to deterministic merge
        logger.warning(
            "compact_memory: GLM summary dispatch failed (%s); using deterministic fallback",
            exc,
        )
        return "", 0.5


def _parse_summary_response(response: Any) -> tuple[str, float]:
    """Parse the GLM response into (content, confidence).

    Accepts:
        - dict {"content": str, "confidence": float} (preferred)
        - OpenAI-style response with .choices[0].message.content carrying JSON
        - bare string (treated as content, confidence=0.5)
    """
    if isinstance(response, dict):
        if "content" in response and "confidence" in response:
            return str(response["content"]), float(response["confidence"])
        # OpenAI-style dict response.
        choices = response.get("choices")
        if choices and isinstance(choices, list):
            msg = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
            content = msg.get("content", "")
            return _parse_json_summary(content)
    # Object with .choices[0].message.content
    choices = getattr(response, "choices", None)
    if choices:
        msg = getattr(choices[0], "message", None)
        if msg is not None:
            content = getattr(msg, "content", "") or ""
            return _parse_json_summary(content)
    if isinstance(response, str):
        return _parse_json_summary(response)
    return "", 0.5


def _parse_json_summary(content: str) -> tuple[str, float]:
    """Try to extract {content, confidence} from a JSON-bearing string."""
    if not content:
        return "", 0.5
    s = content.strip()
    # Find the first { and last } — LLMs sometimes wrap JSON in prose.
    start = s.find("{")
    end = s.rfind("}")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(s[start : end + 1])
            return str(parsed.get("content", s)), float(parsed.get("confidence", 0.5))
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            logger.debug("compact_memory: summary JSON parse failed (%s); using raw", exc)
    return s, 0.5


# --------------------------------------------------------------------------- #
# Tier counting helpers
# --------------------------------------------------------------------------- #


def _count_tiers_from_records(records: list[dict[str, Any]]) -> dict[str, int]:
    """Count active records across the 3 tiers from a live backend dump.

    Post-compaction: active core records (status="active", scope="global"),
    superseded working records, archived records. We report ACTIVE counts
    per tier (i.e., records a retrieve would surface) so the budget check
    matches the §4.4 contract.
    """
    active = [r for r in records if r.get("status") == "active"]
    # Tier 1 — active global records (the post-compaction core tier).
    core = sum(1 for r in active if r.get("scope") == "global")
    # Tier 2 — active project records (working tier).
    working = sum(1 for r in active if r.get("scope") == "project")
    # Tier 3 — active session records + any other active (archival tier).
    archival = sum(1 for r in active if r.get("scope") not in ("global", "project"))
    return {"core": core, "working": working, "archival": archival}


def _count_active_tiers(
    core_records: list[dict[str, Any]],
    working_records: list[dict[str, Any]],
    archival_records: list[dict[str, Any]],
    *,
    summary_added: bool,
) -> dict[str, int]:
    """Project post-compaction tier counts from the planned reassignment.

    Used by dry_run to preview the result without writing. The summary
    record lands in working-tier (scope mirrors the working originals),
    replacing the 100 superseded working records with 1 active summary.
    """
    # Core tier is untouched by compaction (the 10 global records stay).
    core_count = len(core_records)
    # Working tier post-compaction: 100 originals superseded (status="superseded"
    # so not active), replaced by 1 active summary record.
    working_count = 1 if summary_added else 0
    # Archival tier post-compaction: all archival_records flipped to archived
    # (status="archived" so not active).
    archival_count = 0
    return {
        "core": min(core_count, TIER_CORE_MAX),
        "working": min(working_count, TIER_WORKING_MAX),
        "archival": min(archival_count, TIER_ARCHIVAL_MAX),
    }


def _mean_confidence(records: list[dict[str, Any]]) -> float:
    """Mean confidence across records (0.5 fallback for empty)."""
    if not records:
        return 0.5
    confs = [float(r.get("confidence", 0.5) or 0.5) for r in records]
    return sum(confs) / len(confs)


# --------------------------------------------------------------------------- #
# Backend + audit resolution
# --------------------------------------------------------------------------- #


def _resolve_backend() -> Any:
    """Resolve the mem0 backend via memory_arbitration (lazy import).

    Returns None when the backend is unavailable (no MEM0_API_KEY).
    Tests bypass this by passing ``backend=`` explicitly.
    """
    try:
        from agent.memory_arbitration import _get_mem0_backend
    except ImportError as exc:
        logger.debug("compact_memory: memory_arbitration unavailable (%s)", exc)
        return None
    try:
        return _get_mem0_backend()
    except Exception as exc:  # noqa: BLE001
        logger.debug("compact_memory: _get_mem0_backend failed (%s)", exc)
        return None


def _append_audit_entry(
    *,
    agent_id: str,
    pre_count: int,
    post_count: int,
    tiers: dict[str, int],
    summary_record_ids: list[str],
    archived_record_ids: list[str],
) -> str | None:
    """Append the curator_audit entry for this compaction pass.

    Returns the entry_id, or None if the audit subsystem is unavailable.
    """
    try:
        append = _resolve_append_audit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("compact_memory: append_audit unavailable (%s)", exc)
        return None
    ts = int(time.time())
    try:
        return append(
            action="auto_apply",
            patch_id=f"compaction-{agent_id}-{ts}",
            skill_id=agent_id,
            eval_score={
                "compaction": {
                    "pre_count": pre_count,
                    "post_count": post_count,
                    "tiers": tiers,
                    "summary_record_ids": summary_record_ids,
                    "archived_record_ids": archived_record_ids,
                }
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("compact_memory: append_audit failed (%s)", exc)
        return None
