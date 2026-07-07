"""EVAL-03 bias canary — gates P5 (curator failure modes) mitigations.

Three deterministic checks per ``05-POC-PLAN.md §4.3`` + ``PITFALLS §P5``:

1. ``_check_evidence_coverage`` (P5 mitigation 2): cosine ≥ 0.7 between new
   memory text and each cited evidence record's text. Below threshold → flag.
2. ``_check_operator_diversity`` (P5 mitigation 3): ≥2 distinct operator IDs
   in evidence_operator_ids. Below threshold → flag.
3. ``_check_confidence_threshold`` (P5/P2 mitigation): confidence ≥ 0.3 per
   §4.5 safe-defaults. Below threshold → flag (signals low curator certainty).

Plus an optional LLM claim-support pass via ``auxiliary_client.call_llm`` that
asks GLM whether ``record["text"]`` is supported by ``record["evidence_chain"]``.

Design invariants (cite, do not re-derive):
- Module is SEPARATE from ``agent/curator.py`` main path (CONTEXT.md decision
  #3). Curator reads canary output; canary never modifies curator's writes.
- GLM-only enforcement: every ``call_llm`` invocation passes ``provider="glm"``
  (MEMORY.md ``feedback-glm-5-2-only.md``).
- Serial lock respected: ``acquire_glm_slot`` wraps every GLM dispatch
  (MEMORY.md ``feedback-glm-overload-reduce-concurrency.md``).
- Default ``embed_fn`` is a deterministic bag-of-words fallback (no LLM, no
  network) so unit tests stay deterministic without monkey-patching globals.
- ``encoding="utf-8"`` on every text-mode ``open()`` (PLW1514).
- Dry-run default: ``run_bias_canary`` writes NOTHING to the memory store —
  EVAL-06 invariant inherited by EVAL-03 even though EVAL-06 ships in Phase 55.

Threat register (T-54-07..SC) mitigated:
- T-54-07 (fixture tampering): ``json.load`` only (no eval / unsafe yaml).
- T-54-08 (LLM DoS): try/except around LLM dispatch, fail-safe to flag.
- T-54-09 (audit chain): uses existing ``curator_audit.append_audit`` (sha256).
- T-54-10 (repudiation): per-record flags persisted in JSON report + audit.
- T-54-SC (no new packages): stdlib math + json only.
"""
from __future__ import annotations

import json
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tunables (per PITFALLS §P5 + §4.5 safe-defaults)
# ---------------------------------------------------------------------------

#: P5 mitigation 2 — minimum cosine similarity between new memory text and
#: each cited evidence record's text. Below → flag the record.
DEFAULT_EVIDENCE_COVERAGE_THRESHOLD: float = 0.7

#: P5 mitigation 3 — minimum number of distinct operator IDs in the evidence
#: chain. Single-operator insight cannot drive automated memory writes.
DEFAULT_MIN_DISTINCT_OPERATORS: int = 2

#: §4.5 safe-defaults — minimum curator confidence for promotion. Below → flag
#: (low curator certainty, suspicious for an auto-promote candidate).
DEFAULT_CONFIDENCE_THRESHOLD: float = 0.3

#: Auxiliary task name registered in ``cli-config.yaml.example``.
CANARY_TASK_NAME: str = "bias_canary_claim_check"

#: GLM provider id — every LLM dispatch must pass this (feedback-glm-5-2-only.md).
CANARY_PROVIDER: str = "glm"


# ---------------------------------------------------------------------------
# Deterministic bag-of-words embed_fn (default — no LLM, no network)
# ---------------------------------------------------------------------------

_EMBED_DIM: int = 16


def _default_embed(text: str) -> list[float]:
    """Deterministic bag-of-words embed_fn.

    Hashed tokens into ``_EMBED_DIM`` buckets with a stable polynomial
    rolling hash (NOT Python's salted ``hash()``), then L2-normalized.
    Returns a zero vector for empty / whitespace-only input.

    Used as the default for ``_check_evidence_coverage`` so unit tests stay
    deterministic without monkey-patching globals. Production code can swap
    in a real embedding model via ``embed_fn=``.
    """
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    if not tokens:
        return [0.0] * _EMBED_DIM
    counts: Counter[str] = Counter(tokens)
    vec = [0.0] * _EMBED_DIM
    for tok, c in counts.items():
        h = 0
        for ch in tok:
            h = (h * 31 + ord(ch)) & 0xFFFF
        vec[h % _EMBED_DIM] += float(c)
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        return vec
    return [v / norm for v in vec]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity. Returns 0.0 for empty / zero vectors."""
    if not a or not b:
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for i in range(min(len(a), len(b))):
        dot += a[i] * b[i]
        na += a[i] * a[i]
        nb += b[i] * b[i]
    if na == 0.0 or nb == 0.0:
        return 0.0
    denom = math.sqrt(na) * math.sqrt(nb)
    if denom == 0.0:
        return 0.0
    return dot / denom


# ---------------------------------------------------------------------------
# Public API — deterministic checks
# ---------------------------------------------------------------------------


def _check_evidence_coverage(
    new_memory_text: str,
    evidence_records: list[dict],
    *,
    threshold: float = DEFAULT_EVIDENCE_COVERAGE_THRESHOLD,
    embed_fn: Callable[[str], list[float]] | None = None,
) -> dict:
    """P5 mitigation 2 — cosine coverage check.

    For each evidence record, compute cosine similarity between
    ``embed_fn(new_memory_text)`` and ``embed_fn(record["text"])``.
    Flag any record whose cosine < ``threshold``.

    Args:
        new_memory_text: The candidate memory's text (claim being promoted).
        evidence_records: Resolved evidence records (list of dicts with a
            ``text`` key; missing key treated as empty string).
        threshold: Minimum cosine for coverage. Default 0.7.
        embed_fn: Embedding function (text → vector). Defaults to the
            deterministic bag-of-words fallback (no LLM).

    Returns:
        ``{"passed": bool, "low_cosine_records": list[int], "min_cosine": float}``
        where ``low_cosine_records`` holds 0-based indices of records below
        threshold, and ``min_cosine`` is the lowest observed cosine (or 1.0
        for an empty evidence list — vacuously passes).
    """
    embed = embed_fn or _default_embed
    new_vec = embed(new_memory_text or "")
    low_cosine_records: list[int] = []
    min_cosine = 1.0
    for idx, rec in enumerate(evidence_records):
        ev_text = ""
        if isinstance(rec, dict):
            ev_text = rec.get("text") or ""
        elif isinstance(rec, str):
            ev_text = rec
        ev_vec = embed(ev_text)
        cos = _cosine_similarity(new_vec, ev_vec)
        if cos < min_cosine:
            min_cosine = cos
        if cos < threshold:
            low_cosine_records.append(idx)
    return {
        "passed": len(low_cosine_records) == 0,
        "low_cosine_records": low_cosine_records,
        "min_cosine": min_cosine,
    }


def _check_operator_diversity(
    evidence_operator_ids: list[str],
    *,
    min_distinct_operators: int = DEFAULT_MIN_DISTINCT_OPERATORS,
) -> dict:
    """P5 mitigation 3 — operator diversity check.

    Args:
        evidence_operator_ids: List of operator IDs from the evidence chain.
            ``None`` and empty-string entries are filtered out.
        min_distinct_operators: Minimum distinct count required. Default 2.

    Returns:
        ``{"passed": bool, "distinct_count": int, "distinct_operators": list[str]}``
    """
    if evidence_operator_ids is None:
        evidence_operator_ids = []
    distinct = sorted({oid for oid in evidence_operator_ids if oid})
    return {
        "passed": len(distinct) >= min_distinct_operators,
        "distinct_count": len(distinct),
        "distinct_operators": distinct,
    }


def _check_confidence_threshold(
    confidence: float | None,
    *,
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> dict:
    """§4.5 safe-defaults — confidence threshold check.

    Low curator certainty on a memory-upgrade candidate is suspicious. The
    §4.5 default floor is 0.3; below that the curator is signaling it is not
    sure the record should be promoted.

    Args:
        confidence: Curator-assigned confidence in [0.0, 1.0]. ``None`` is
            treated as a fail (no confidence asserted).
        threshold: Minimum required confidence. Default 0.3.

    Returns:
        ``{"passed": bool, "confidence": float | None, "threshold": float}``
    """
    if confidence is None:
        return {"passed": False, "confidence": None, "threshold": threshold}
    return {
        "passed": float(confidence) >= threshold,
        "confidence": float(confidence),
        "threshold": threshold,
    }


# ---------------------------------------------------------------------------
# CanaryReport
# ---------------------------------------------------------------------------


@dataclass
class CanaryReport:
    """Per-record canary verdict.

    ``flagged`` is the aggregate signal — any failed check flips it.
    Persisted to ``curator_audit`` chain (action ``auto_apply`` with a
    ``bias_canary`` marker in ``eval_score``) when ``audit_chain=True``.
    """

    record_id: str
    checks_passed: list[str] = field(default_factory=list)
    checks_failed: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)
    flagged: bool = False

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "checks_passed": list(self.checks_passed),
            "checks_failed": list(self.checks_failed),
            "details": dict(self.details),
            "flagged": bool(self.flagged),
        }


def check_record(
    record: dict,
    *,
    embed_fn: Callable[[str], list[float]] | None = None,
    min_distinct_operators: int = DEFAULT_MIN_DISTINCT_OPERATORS,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    evidence_coverage_threshold: float = DEFAULT_EVIDENCE_COVERAGE_THRESHOLD,
) -> CanaryReport:
    """Run all deterministic checks on a single memory record.

    Does NOT call any LLM (the claim-support LLM pass lives in
    :func:`run_bias_canary` so unit tests stay deterministic).

    Inspected fields (per memory-record-schema.yaml §3):
      - ``record_id`` (str): identifier
      - ``text`` (str): the candidate memory claim
      - ``evidence_records`` (list[dict]): resolved evidence text
      - ``evidence_operator_ids`` (list[str]): operator provenance
      - ``confidence`` (float): curator certainty

    Returns a :class:`CanaryReport` with one entry per check name in
    ``checks_passed`` / ``checks_failed``.
    """
    record_id = record.get("record_id") or "<missing-record-id>"
    report = CanaryReport(record_id=record_id)

    # Deterministic check #1 — evidence coverage.
    cov = _check_evidence_coverage(
        new_memory_text=record.get("text") or "",
        evidence_records=record.get("evidence_records") or [],
        threshold=evidence_coverage_threshold,
        embed_fn=embed_fn,
    )
    report.details["evidence_coverage"] = cov
    if cov["passed"]:
        report.checks_passed.append("evidence_coverage")
    else:
        report.checks_failed.append("evidence_coverage")

    # Deterministic check #2 — operator diversity.
    div = _check_operator_diversity(
        evidence_operator_ids=record.get("evidence_operator_ids") or [],
        min_distinct_operators=min_distinct_operators,
    )
    report.details["operator_diversity"] = div
    if div["passed"]:
        report.checks_passed.append("operator_diversity")
    else:
        report.checks_failed.append("operator_diversity")

    # Deterministic check #3 — confidence threshold.
    conf = _check_confidence_threshold(
        record.get("confidence"),
        threshold=confidence_threshold,
    )
    report.details["confidence_threshold"] = conf
    if conf["passed"]:
        report.checks_passed.append("confidence_threshold")
    else:
        report.checks_failed.append("confidence_threshold")

    report.flagged = len(report.checks_failed) > 0
    return report


# ---------------------------------------------------------------------------
# LLM claim-support pass (async — respects GLM serial lock)
# ---------------------------------------------------------------------------

#: Default LLM prompt template. Returns a single token: YES or NO.
_CLAIM_SUPPORT_PROMPT = """You are a memory-curator bias canary. Assess whether the candidate memory claim is supported by the cited evidence.

Candidate memory text:
\"\"\"
{claim}
\"\"\"

Evidence chain (resolved excerpts):
{evidence}

Reply with exactly one line, starting with YES or NO, then a short reason.
YES = claim is fully supported by the evidence above.
NO  = claim contains content not present in or contradicted by the evidence.
"""


def _format_evidence_for_llm(record: dict) -> str:
    """Render the evidence_chain / evidence_records as a flat list of excerpts."""
    evidence_records = record.get("evidence_records") or []
    if not evidence_records and record.get("evidence_chain"):
        # Fallback — if only IDs are present, list them verbatim.
        evidence_records = [{"text": str(sid)} for sid in record["evidence_chain"]]
    lines = []
    for idx, rec in enumerate(evidence_records):
        text = rec.get("text") if isinstance(rec, dict) else str(rec)
        lines.append(f"  [{idx}] {text}")
    return "\n".join(lines) if lines else "  (no evidence provided)"


def _parse_claim_supported(content: str | None) -> tuple[bool, str]:
    """Parse the LLM's YES/NO response. Defaults to False (fail-safe).

    Returns ``(supported, reason)``. Any parse failure → ``(False, "<raw>")``
    so the caller flags the record rather than accepting it (T-54-08 mitigation).
    """
    if not content:
        return False, "<empty LLM response>"
    text = content.strip()
    first_line = text.splitlines()[0] if text else ""
    head = first_line.lstrip().upper()[:6]
    if head.startswith("YES"):
        return True, text
    if head.startswith("NO"):
        return False, text
    # Ambiguous response → fail-safe to "not supported" (T-54-08).
    return False, text


async def _default_claim_check_llm(record: dict) -> tuple[bool, str]:
    """Dispatch the GLM claim-support check.

    Respects the GLM serial lock via ``acquire_glm_slot`` (no-op on non-GLM
    hosts, but always honored because provider is GLM-only).

    Returns ``(supported, reason)``. Failures → ``(False, "<error>")``
    (T-54-08 fail-safe).
    """
    from agent import auxiliary_client, glm_concurrency_guard  # local import — circular-safe

    prompt = _CLAIM_SUPPORT_PROMPT.format(
        claim=record.get("text") or "",
        evidence=_format_evidence_for_llm(record),
    )
    messages = [
        {"role": "system", "content": "You are a memory bias canary."},
        {"role": "user", "content": prompt},
    ]
    try:
        # Serial lock first — MEMORY.md feedback-glm-overload-reduce-concurrency.md.
        # acquire_glm_slot is a sync context manager; safe to use from async
        # because the underlying GLM call itself is synchronous (auxiliary_client.call_llm).
        with glm_concurrency_guard.acquire_glm_slot(base_url=None):
            response = auxiliary_client.call_llm(
                task=CANARY_TASK_NAME,
                provider=CANARY_PROVIDER,  # GLM-only — MEMORY.md feedback-glm-5-2-only.md
                messages=messages,
                temperature=0.0,
                max_tokens=120,
                timeout=30.0,
            )
    except Exception as exc:  # noqa: BLE001 — must never crash the canary
        logger.warning(
            "bias_canary: GLM claim-check dispatch failed for record=%s: %s — "
            "defaulting to claim_supported=False (T-54-08 fail-safe)",
            record.get("record_id"),
            exc,
        )
        return False, f"<dispatch error: {exc}>"

    content = None
    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as exc:
        logger.warning(
            "bias_canary: malformed LLM response for record=%s: %r — "
            "defaulting to claim_supported=False (T-54-08 fail-safe)",
            record.get("record_id"),
            response,
        )
        return False, f"<malformed response: {exc}>"
    return _parse_claim_supported(content)


async def run_bias_canary(
    records: list[dict],
    *,
    claim_check_llm: Callable[[dict], Awaitable[tuple[bool, str]]] | None = None,
    audit_chain: bool = True,
    embed_fn: Callable[[str], list[float]] | None = None,
) -> list[CanaryReport]:
    """Run the full bias canary over a batch of memory records.

    For each record:
      1. Run deterministic checks (``check_record``).
      2. Run the LLM claim-support check (``claim_check_llm`` or default
         GLM dispatch).
      3. Aggregate into a :class:`CanaryReport`.

    Args:
        records: Memory records (dicts) conforming to memory-record-schema.yaml.
        claim_check_llm: Optional async callable ``record -> (supported, reason)``.
            Defaults to :func:`_default_claim_check_llm` which dispatches via
            ``auxiliary_client.call_llm`` with ``provider="glm"`` wrapped in
            ``acquire_glm_slot``. Unit tests pass a stub here to avoid GLM.
        audit_chain: If True (default), append a single summary entry to the
            ``curator_audit`` chain via :func:`curator_audit.append_audit`
            with ``action="auto_apply"`` and ``eval_score={"bias_canary": {...}}``.
        embed_fn: Embedding function override (defaults to bag-of-words).

    Returns:
        List of :class:`CanaryReport`, one per input record (same order).
    """
    dispatch = claim_check_llm or _default_claim_check_llm
    reports: list[CanaryReport] = []

    for record in records:
        report = check_record(record, embed_fn=embed_fn)

        # LLM claim-support pass (async).
        try:
            supported, reason = await dispatch(record)
        except Exception as exc:  # noqa: BLE001 — never crash on LLM dispatch
            logger.warning(
                "bias_canary: claim_check_llm raised for record=%s: %s — "
                "defaulting to supported=False (T-54-08 fail-safe)",
                record.get("record_id"),
                exc,
            )
            supported, reason = False, f"<dispatcher raised: {exc}>"

        report.details["claim_support"] = {
            "supported": bool(supported),
            "reason": reason,
        }
        if supported:
            report.checks_passed.append("claim_support")
        else:
            report.checks_failed.append("claim_support")

        # Recompute aggregate flag (LLM check may flip).
        report.flagged = len(report.checks_failed) > 0
        reports.append(report)

    if audit_chain and reports:
        _append_audit_summary(reports)

    return reports


# ---------------------------------------------------------------------------
# Audit chain append (T-54-09 mitigation — uses existing sha256-chained writer)
# ---------------------------------------------------------------------------


def _append_audit_summary(reports: list[CanaryReport]) -> None:
    """Append one summary entry to the curator_audit chain.

    Uses ``action="auto_apply"`` (the closest ACTION_VALUES entry for a
    curator-side automated decision) and stuffs the per-record flags into
    ``eval_score`` under a ``bias_canary`` key.

    Failures here are logged but do not propagate — the canary's verdict
    has already been computed and the caller (CLI / test) will see it in the
    returned reports. Audit chain integrity is best-effort for the canary.
    """
    try:
        from agent import curator_audit  # local import — circular-safe
    except Exception as exc:  # noqa: BLE001 — module missing in minimal env
        logger.warning("bias_canary: curator_audit module unavailable: %s", exc)
        return

    flagged = [r.to_dict() for r in reports if r.flagged]
    passed = [r.record_id for r in reports if not r.flagged]
    summary = {
        "bias_canary": {
            "total_records": len(reports),
            "flagged_count": len(flagged),
            "passed_count": len(passed),
            "flagged_record_ids": [r["record_id"] for r in flagged],
            "passed_record_ids": passed,
            "flagged_details": flagged,
        }
    }
    try:
        curator_audit.append_audit(
            action="auto_apply",
            patch_id="bias-canary-summary",
            skill_id="<bias-canary>",
            operator="system",
            eval_score=summary,
        )
    except (ValueError, OSError) as exc:
        logger.warning(
            "bias_canary: append_audit failed (chain may need verify): %s", exc
        )


__all__ = [
    "DEFAULT_EVIDENCE_COVERAGE_THRESHOLD",
    "DEFAULT_MIN_DISTINCT_OPERATORS",
    "DEFAULT_CONFIDENCE_THRESHOLD",
    "CANARY_TASK_NAME",
    "CANARY_PROVIDER",
    "CanaryReport",
    "_check_evidence_coverage",
    "_check_operator_diversity",
    "_check_confidence_threshold",
    "check_record",
    "run_bias_canary",
    # Aliases per PLAN must_haves artifact spec
    "check_evidence_coverage",
    "check_operator_diversity",
]


# Plan-required aliases (must_haves exports list).
check_evidence_coverage = _check_evidence_coverage
check_operator_diversity = _check_operator_diversity
