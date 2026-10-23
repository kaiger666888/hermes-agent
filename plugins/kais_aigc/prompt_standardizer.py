"""prompt_standardizer.py — deterministic dreamina prompt pre-standardization.

NEW LAYER inserted between the prompt author (prompt_injector / visual_executor)
and the dreamina CLI. It is a pure, stdlib-only, idempotent transform that makes
a raw prompt safe + model-effective for the dreamina ``--prompt`` flag WITHOUT
changing its semantic intent.

RESEARCH basis (see ``/tmp/dreamina-prompt-research.md``):
  1. dreamina CLI has NO ``--negative_prompt`` flag -> negative concepts must be
     folded into the main prompt (proven by ``dreamina_manager._escalate_prompt``
     which already uses inline "NOT X" phrasing).
  2. dreamina CLI SUPPORTS multi-line prompts — production logs show ``\\n\\n``
     preserved verbatim in submitted JSON. So newline flattening is OPT-IN
     (default off), NOT the task-spec's original assumption.
  3. No hard length limit in the CLI; model effectiveness degrades past ~600 EN
     words / ~800 CN chars. Truncation is therefore about effectiveness, not
     CLI compliance, and defaults to a conservative ceiling.
  4. dreamina/Seedream 5.0 does NOT use Stable-Diffusion ``(kw:1.5)`` weight
     syntax — it relies on natural-language NLU. This module never emits SD
     weight syntax.
  5. Characters ``() : , . \\n`` and CJK are all accepted and appear in real
     production prompts — the control-char scrub must NOT touch them.

Design principles:
  - Pure function, no side effects (no I/O, no logging), trivially testable.
  - Idempotent: ``standardize_prompt(standardize_prompt(x)) == standardize_prompt(x)``.
  - Hard-fail-safe: any internal error returns the raw input unchanged (mirrors
    the ``p11b_final_render._h3_enhance_prompt`` degrade discipline — never block
    rendering).
  - Each step independently configurable via kwargs.

Public API:
  - ``standardize_prompt(...)`` — the core pure transform.
  - ``DREAMINA_DEFAULT_MAX_LENGTH`` — conservative operational ceiling used by
    the dreamina_manager integration (wide enough that real prompts are a no-op).
"""

from __future__ import annotations

import re

__all__ = ["standardize_prompt", "DREAMINA_DEFAULT_MAX_LENGTH"]


# Operational default used by the dreamina_manager integration. Research found
# real production prompts run ~1500–2500 chars and submit cleanly, while model
# effectiveness degrades well above ~600 EN words. 4000 chars keeps a wide
# safety margin so standardization is a no-op on every observed real prompt
# (preserving existing behavior) while still guarding against pathological
# over-length input. Operators can tune per-call via ``max_length``.
DREAMINA_DEFAULT_MAX_LENGTH = 4000


# ── Character tables (explicit \u escapes — never embed invisible chars) ────

# C0 control chars (keep \t=\x09, \n=\x0a, \r=\x0d), DEL, and C1 control chars.
_CONTROL_CHARS = (
    "\x00\x01\x02\x03\x04\x05\x06\x07\x08"  # NUL–BS
    "\x0b\x0c"                                # VT, FF
    "\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f"  # SO–US
    "\x7f"                                    # DEL
    "\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f"
    "\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f"  # C1
)
# Zero-width / format chars + BOM + soft hyphen (all invisible, all unsafe for
# a CLI prompt). Soft hyphen U+00AD is invisible-by-design; removing it merges
# words correctly (soft hyphen U+00AD between "photo" and "graph" is removed -> "photograph").
_INVISIBLE_CHARS = "\u200b\u200c\u200d\u2060\ufeff\u00ad"
_STRIP_CONTROL = re.compile("[" + re.escape(_CONTROL_CHARS + _INVISIBLE_CHARS) + "]")

# Smart/curly quotes -> straight (normalizes model-inconsistent typography).
# Dashes (– —) are deliberately LEFT ALONE: they appear in real prompts and
# carry meaning; normalizing them is not part of "quote" handling.
_SMART_QUOTES = {
    "‘": "'",  # ‘ LEFT SINGLE QUOTATION MARK
    "’": "'",  # ’ RIGHT SINGLE QUOTATION MARK
    "“": '"',  # “ LEFT DOUBLE QUOTATION MARK
    "”": '"',  # ” RIGHT DOUBLE QUOTATION MARK
}
_SMART_QUOTE_RE = re.compile("[" + re.escape("".join(_SMART_QUOTES)) + "]")

# Delimiters that separate descriptor segments for dedup. Covers ASCII + the
# common CJK fullwidth / ideographic variants so CN prompts are handled too.
_SEG_DELIMS = (
    ","      # ASCII comma
    "，" # FULLWIDTH COMMA ，
    "、" # IDEOGRAPHIC COMMA 、
    ";"      # ASCII semicolon
    "；" # FULLWIDTH SEMICOLON ；
)
_SEG_DELIM_SET = set(_SEG_DELIMS)
_SEG_DELIM_CLASS = re.escape(_SEG_DELIMS)
_SEG_SPLIT = re.compile("([" + _SEG_DELIM_CLASS + "])")

# Whitespace normalization helpers.
_WS_RUN = re.compile(r"[^\S\n]+")  # runs of spaces/tabs (NOT newline)
_WS_BEFORE_NL = re.compile(r" *\n")
_MANY_NL = re.compile(r"\n{3,}")

# Trailing whitespace OR delimiters — stripped after a truncation cut so a
# truncated prompt never ends on a dangling comma/semicolon.
_TRAILING_JUNK = re.compile(r"[\s" + _SEG_DELIM_CLASS + r"]+$")

# Backslash-escape a double quote ONLY when not already escaped (idempotent).
_ESCAPE_DQUOTE = re.compile(r'(?<!\\)"')

# Truncation boundary char sets (used as SETS, not substring needles).
_SENTENCE_BOUNDARY = set("。！？.!?")  # 。！？. ! ?
_CLAUSE_BOUNDARY = set("，；、,;")     # ，；、,;


# ── Internal step helpers ──────────────────────────────────────────────────


def _to_str(raw_prompt: str) -> str:
    """Coerce input to a string; None -> "" (empty-prompt boundary case)."""
    if raw_prompt is None:
        return ""
    if isinstance(raw_prompt, str):
        return raw_prompt
    return str(raw_prompt)


def _normalize_whitespace(text: str) -> str:
    """Normalize line endings + collapse space runs; never drop newlines.

    - ``\\r\\n`` / ``\\r`` -> ``\\n``
    - runs of spaces/tabs -> single space (newlines untouched)
    - trailing spaces before a newline removed
    - 3+ consecutive newlines -> exactly 2 (preserve paragraph break, drop gaps)
    - leading/trailing whitespace stripped
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _WS_RUN.sub(" ", text)
    text = _WS_BEFORE_NL.sub("\n", text)
    text = _MANY_NL.sub("\n\n", text)
    return text.strip()


def _normalize_quotes(text: str) -> str:
    """Smart/curly quotes -> straight quotes (typography consistency)."""
    return _SMART_QUOTE_RE.sub(lambda m: _SMART_QUOTES[m.group(0)], text)


def _dedup_line(line: str) -> str:
    """Remove exact-duplicate comma/semicolon segments WITHIN a single line.

    Scope is deliberately per-line: multi-line structured prompts (e.g. a
    "Panel 1 / Panel 2 / ..." storyboard) are never collapsed across line
    boundaries, so structural repetition is preserved. Within one line,
    repeated descriptor segments (the common token-budget waste case, e.g.
    "cinematic, warm, cinematic") collapse to their first occurrence.

    Comparison is case-insensitive on the stripped segment; the FIRST
    occurrence (original casing + delimiter) is kept.
    """
    if not _SEG_SPLIT.search(line):
        return line
    parts = _SEG_SPLIT.split(line)
    seen: set[str] = set()
    out: list[str] = []
    i = 0
    n = len(parts)
    while i < n:
        seg = parts[i]
        delim = parts[i + 1] if i + 1 < n else None
        key = seg.strip().lower()
        if key == "" or key not in seen:
            if key:
                seen.add(key)
            out.append(seg)
            if delim is not None:
                out.append(delim)
        # else: duplicate segment -> drop segment AND its trailing delimiter
        i += 2
    result = "".join(out)
    # A dropped trailing segment can leave a dangling delimiter on the line.
    result = re.sub(r"[\s" + _SEG_DELIM_CLASS + r"]+$", "", result)
    # Collapse any ", ," style double delimiters left behind.
    result = re.sub(
        r"([" + _SEG_DELIM_CLASS + r"])\s*([" + _SEG_DELIM_CLASS + r"])",
        r"\1 ", result,
    )
    return result


def _dedup_segments(text: str) -> str:
    """Apply per-line segment dedup (see ``_dedup_line``)."""
    return "\n".join(_dedup_line(line) for line in text.split("\n"))


def _pick_separator(body: str, *, for_negative: bool = False) -> str:
    """Choose a join separator between body and an appended clause.

    Structured (multi-line) bodies get ``\\n\\n`` to match the proven
    "style line first, then blank line" layout; short single-line bodies get
    ``", "`` for a prefix or ``". "`` for a trailing negative clause.
    """
    if "\n" in body.strip():
        return "\n\n"
    return ". " if for_negative else ", "


def _inject_prefix(body: str, style_prefix: str) -> str:
    """Prepend a global style prefix if not already present (idempotent).

    Idempotency guard: if the prefix (case-insensitive) is already a substring
    of the body, the concept is already covered -> no-op. This makes repeated
    calls safe (e.g. a retry path that re-standardizes).
    """
    prefix = style_prefix.strip()
    if not prefix or not body:
        return body
    if prefix.lower() in body.lower():
        return body
    sep = _pick_separator(body)
    return f"{prefix}{sep}{body}"


def _last_boundary_index(candidate: str, charset: set[str], floor: int) -> int:
    """Return the largest index of any char in ``charset`` within ``candidate``
    that is >= ``floor``; return -1 if none qualifies.

    (``rfind`` on a multi-char needle would search for the whole substring,
    which is why we scan char-set membership instead.)
    """
    best = -1
    for idx, ch in enumerate(candidate):
        if idx < floor:
            continue
        if ch in charset and idx > best:
            best = idx
    return best


def _truncate_at_boundary(text: str, limit: int) -> str:
    """Truncate to <= ``limit`` chars at the latest sentence/clause/word break.

    Never splits a multi-byte char (Python str indexing is code-point safe).
    Prefers a sentence end, then a clause boundary, then a space — but only
    accepts a cut point in the latter half of the window so we never truncate
    away most of the content just to land on an early boundary. If no usable
    boundary exists, hard-cuts at ``limit``.
    """
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    candidate = text[:limit]
    floor = limit // 2
    for charset in (_SENTENCE_BOUNDARY, _CLAUSE_BOUNDARY, {" "}):
        idx = _last_boundary_index(candidate, charset, floor)
        if idx >= floor:
            # Cut just past the boundary char (kept); strip any trailing
            # whitespace/delimiter so the result never ends on a dangling comma.
            return _TRAILING_JUNK.sub("", text[: idx + 1])
    return _TRAILING_JUNK.sub("", candidate)


def _prep_negative(negative_prompt: str | None) -> str:
    """Clean a negative-prompt clause: coerce + normalize + trim delimiters."""
    if not negative_prompt:
        return ""
    neg = _normalize_whitespace(_to_str(negative_prompt))
    return re.sub(
        r"^[\s" + _SEG_DELIM_CLASS + r"]+|[\s" + _SEG_DELIM_CLASS + r"]+$",
        "", neg,
    )


# ── Public API ─────────────────────────────────────────────────────────────


def standardize_prompt(
    raw_prompt: str,
    *,
    mode: str = "text2image",
    style_prefix: str | None = None,
    negative_prompt: str | None = None,
    max_length: int = 1000,
    clean_control_chars: bool = True,
    normalize_whitespace: bool = True,
    normalize_quotes: bool = True,
    dedup_segments: bool = True,
    flatten_newlines: bool = False,
    escape_quotes: bool = False,
    truncate: bool = True,
) -> str:
    """Standardize a dreamina ``--prompt`` value.

    A deterministic, pure, idempotent transform. See module docstring for the
    research basis. Returns a string that is safe to pass to the dreamina CLI
    and model-effective, without altering semantic intent.

    Args:
        raw_prompt: the prompt as authored by prompt_injector / visual_executor.
        mode: ``"text2image"`` | ``"image2image"``. Currently does not branch
            (both subcommands take the same ``--prompt`` flag); reserved for
            future mode-specific behavior.
        style_prefix: optional global style prefix (e.g. a style_genome 5D
            vector line). Prepended, idempotently, when not already present.
        negative_prompt: optional negative concepts. dreamina has no
            ``--negative_prompt`` flag, so this is folded into the main prompt
            as a trailing ``"Avoid: ..."`` clause (idempotent).
        max_length: soft char ceiling. Truncation cuts at the latest
            sentence/clause/word boundary; the negative clause is reserved so
            it always survives. The CLI enforces no hard limit — this guards
            model effectiveness, not CLI compliance.
        clean_control_chars: strip C0/C1 control chars, zero-width/format
            chars, BOM, soft hyphen (preserves ``\\t \\n \\r`` + printable).
        normalize_whitespace: normalize line endings, collapse space runs,
            drop excessive blank lines.
        normalize_quotes: map smart/curly quotes to straight quotes.
        dedup_segments: remove exact-duplicate comma/semicolon segments
            (per-line, case-insensitive; structural repetition preserved).
        flatten_newlines: replace ``\\n`` with spaces. OFF by default —
            dreamina SUPPORTS multi-line prompts (production-verified).
        escape_quotes: backslash-escape ``"``. OFF by default — the
            dreamina_manager uses subprocess list form (no shell), so quotes
            are already safe; this is for shell/curl contexts.
        truncate: enable length truncation at ``max_length``.

    Returns:
        The standardized prompt string. On any internal error, returns the raw
        input unchanged (hard-fail-safe — never blocks generation).
    """
    original = _to_str(raw_prompt)
    try:
        text = original

        # 1. Control-char scrub (foundation step).
        if clean_control_chars:
            text = _STRIP_CONTROL.sub("", text)

        # 2. Whitespace normalization (line endings, space runs, blank lines).
        if normalize_whitespace:
            text = _normalize_whitespace(text)

        # 3. Smart-quote normalization.
        if normalize_quotes:
            text = _normalize_quotes(text)

        # 4. Exact-duplicate segment dedup (per-line, structure-preserving).
        if dedup_segments:
            text = _dedup_segments(text)

        # 5. Style-prefix injection (prepend, idempotent).
        if style_prefix:
            text = _inject_prefix(text, style_prefix)

        # 6. (optional) Newline flattening — after prefix so its separator
        #    flattens too. Default OFF (dreamina supports multi-line).
        if flatten_newlines:
            text = re.sub(r"\s*\n\s*", " ", text)
            text = re.sub(r" {2,}", " ", text).strip()

        # 7. Truncate the positive text, reserving room for the negative clause
        #    so exclusions always survive truncation.
        neg_text = _prep_negative(negative_prompt)
        append_neg = bool(neg_text) and neg_text.lower() not in text.lower()
        neg_clause = f"Avoid: {neg_text}" if append_neg else ""
        if append_neg:
            # Reserve based on the worst-case separator ("\n\n") + clause.
            neg_reserve = len("\n\n") + len(neg_clause)
            limit = max_length - neg_reserve if truncate else None
        else:
            limit = max_length if truncate else None

        if limit is not None:
            text = _truncate_at_boundary(text, limit)

        # 8. Fold negative prompt as a trailing "Avoid:" clause (idempotent).
        if append_neg:
            sep = _pick_separator(text, for_negative=True)
            text = f"{text}{sep}{neg_clause}"

        # 9. (optional) Quote escaping for shell/curl contexts. OFF by default.
        #    Idempotent: only escapes a double quote not already backslashed.
        if escape_quotes:
            text = _ESCAPE_DQUOTE.sub(r'\\"', text)

        return text
    except Exception:
        # Hard-fail-safe: never let standardization block generation.
        return original
