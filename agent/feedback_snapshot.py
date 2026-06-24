"""OutputSnapshot builder — captures provenance from live conversation state.

Called by the ``/feedback`` slash-command handler in ``cli.py`` and by
the ``hermes feedback submit`` CLI subcommand. Reads agent attributes
(model, provider, api_mode, max_tokens, ...) and conversation history
(most recent assistant turn + its preceding user prompt) and returns
an :class:`OutputSnapshot` ready for :class:`FeedbackRecord`.

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 unions.
  - ``encoding="utf-8"`` on every ``open()`` (none in this module).
  - Specific exception types bound with ``as exc`` and lazy %-logging.

Per RESEARCH.md pitfalls this module defends against:
  - #3 sha256 determinism: hash ``output_text.encode("utf-8")`` exactly.
    Surrogates are handled via ``errors="surrogatepass"`` so lone
    surrogate code points hash deterministically without crashing.
    Documented at the hash site — this is the P29/P30 dedup contract.
  - #5 content shapes: ``_extract_text`` handles str / list-of-dicts /
    None / unknown shapes defensively. Does NOT mutate input.
  - #8 non-serializable request_overrides: filter to JSON-safe types,
    log dropped keys at debug level, never raise TypeError.
"""

from __future__ import annotations

import hashlib
import json as _json
import logging
from datetime import datetime, timezone
from typing import Any

from agent.feedback_schema import OutputSnapshot

logger = logging.getLogger(__name__)


# JSON-serializable primitive types — used to filter request_overrides so
# callables / custom objects don't crash the snapshot. Kept narrow on
# purpose: anything outside these types is dropped with a debug log.
_JSON_SCALAR_TYPES = (str, int, float, bool, type(None))


def _safe_param(val: Any) -> Any:
    """Coerce a single param value to a JSON-safe shape; drop if not serializable.

    Used for the non-dict agent params (max_tokens, reasoning_config,
    service_tier) where a deep recursive filter is overkill — we just
    probe ``json.dumps`` and drop the value on TypeError/ValueError so
    ``write_feedback_record`` -> ``atomic_json_write`` -> ``json.dump``
    never raises mid-write (defends RESEARCH Pitfall #8 for ALL four
    agent params, not just request_overrides).
    """
    try:
        _json.dumps(val)
        return val
    except (TypeError, ValueError):
        logger.debug("dropped non-serializable agent param value: %r", val)
        return None


def _is_json_serializable(value: Any) -> bool:
    """Return True if *value* is safe to include in OutputSnapshot.params.

    Recursive for dict and list (the only JSON container types). Rejects
    callables, custom objects, sets, bytes — anything json.dump would
    reject or that would surprise the consumer.
    """
    if isinstance(value, _JSON_SCALAR_TYPES):
        return True
    if isinstance(value, dict):
        return all(
            isinstance(k, str) and _is_json_serializable(v)
            for k, v in value.items()
        )
    if isinstance(value, list):
        return all(_is_json_serializable(v) for v in value)
    return False


def _filter_serializable(overrides: dict[str, Any]) -> dict[str, Any]:
    """Return a new dict containing only JSON-serializable values.

    Logs each dropped key at debug level so operators can diagnose
    missing params without the snapshot crashing.
    """
    out: dict[str, Any] = {}
    for key, value in overrides.items():
        if _is_json_serializable(value):
            out[key] = value
        else:
            logger.debug(
                "dropped non-serializable request_overrides key: %s", key
            )
    return out


def _extract_text(content: Any) -> str:
    """Extract text from an OpenAI/Anthropic message ``content`` field.

    Handles three shapes per RESEARCH Pitfall #5:
      (a) ``None`` -> ``""`` (typical for tool-call messages)
      (b) ``str`` -> returned as-is
      (c) ``list`` of dicts -> concatenate ``text`` parts where
          ``isinstance(p, dict) and p.get("type") == "text"``
      (d) anything else -> ``str(content)`` as last resort

    This function MUST NOT mutate the input list.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Anthropic-style content blocks. Only pull text parts —
        # tool_use / image / etc blocks are not feedback targets.
        parts: list[str] = []
        for p in content:
            if isinstance(p, dict) and p.get("type") == "text":
                t = p.get("text", "")
                if isinstance(t, str):
                    parts.append(t)
        return "".join(parts)
    # Unknown shape — best-effort string conversion rather than crash.
    return str(content)


def build_output_snapshot(
    agent: Any,
    conversation_history: list[dict[str, Any]],
    assistant_idx: int,
) -> OutputSnapshot:
    """Build an :class:`OutputSnapshot` from live conversation state.

    Args:
        agent: the active AIAgent (or test double). Reads via ``getattr``:
            ``model``, ``provider``, ``api_mode`` (strings) and the params
            tuple ``("max_tokens", "reasoning_config", "service_tier",
            "request_overrides")``. Missing attrs default gracefully.
        conversation_history: the live conversation message list. Read
            ONLY — never mutated.
        assistant_idx: index of the assistant turn to snapshot.

    Returns:
        A validated :class:`OutputSnapshot` ready for embedding in a
        :class:`FeedbackRecord`.
    """
    assistant_msg = conversation_history[assistant_idx]
    output_text = _extract_text(assistant_msg.get("content"))

    # Scan backward for the most recent user prompt preceding this turn.
    prompt_text = ""
    for i in range(assistant_idx - 1, -1, -1):
        msg = conversation_history[i]
        if msg.get("role") == "user":
            prompt_text = _extract_text(msg.get("content"))
            break

    # ── sha256 — canonical dedup contract for P29 STORE / P30 GATE ──
    #
    # Hash the EXACT output_text bytes. ``errors="surrogatepass"`` keeps
    # lone surrogate code points byte-stable across runs (the default
    # strict mode would raise UnicodeEncodeError on surrogates; "replace"
    # would hash different bytes depending on Python's replacement char).
    # This encoding path is the single source of truth for dedup —
    # do not change it without bumping a schema version flag.
    sha = hashlib.sha256(
        output_text.encode("utf-8", errors="surrogatepass")
    ).hexdigest()

    # ── Collect LLM call params ──
    # These matter for P30 eval-gate ablation: the gate must know which
    # temperature / max_tokens / etc produced the output it's scoring.
    params: dict[str, Any] = {}
    for attr in ("max_tokens", "reasoning_config", "service_tier", "request_overrides"):
        val = getattr(agent, attr, None)
        if val is None:
            continue
        if attr == "request_overrides":
            # Dict[str, Any] — deep filter non-serializable values (Pitfall #8).
            if isinstance(val, dict):
                params[attr] = _filter_serializable(val)
            else:
                # Non-dict shape — shallow probe so a stray dataclass /
                # callable doesn't sneak through this branch either.
                safe = _safe_param(val)
                if safe is not None:
                    params[attr] = safe
        else:
            # Non-dict params — apply the same JSON-safety probe as
            # request_overrides so a custom enum / dataclass / callable
            # set on agent.<attr> doesn't crash write_feedback_record
            # mid-write (RESEARCH Pitfall #8 extended to all four params).
            safe = _safe_param(val)
            if safe is not None:
                params[attr] = safe

    return OutputSnapshot(
        sha256=sha,
        output_text=output_text,
        prompt=prompt_text,
        model=getattr(agent, "model", "") or "",
        provider=getattr(agent, "provider", "") or "",
        api_mode=getattr(agent, "api_mode", "") or "",
        params=params,
        captured_at=datetime.now(timezone.utc),
    )
