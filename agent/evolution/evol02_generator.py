"""EVOL-02 — LLM-driven multi-instruction bilingual unified-diff generator.

Extends the Phase 31 placeholder (:mod:`agent.evolution.diff_generator`) to
support multiple structured instructions per call, each producing a
bilingual (EN-structure + CN-prose) content block that is spliced into the
target file at a validated anchor section. The LLM emits structured
instructions; :func:`difflib.unified_diff` generates the actual diff
(research A1 — LLMs are unreliable at ``@@ -A,B +C,D @@`` hunk syntax).

Build-final-state-then-diff-once approach (RESEARCH §"EVOL-02 Generator
Extension"): for each instruction we mutate a working copy of the file
content sequentially, then emit ONE ``difflib.unified_diff`` per file. This
handles anchor-offset shifts when multiple instructions target the same
file. Multi-file patches join per-file diffs with ``"\\n"``.

Per CLAUDE.md conventions:
  - Bilingual format: EN heading + body, blank line, CN heading + body.
  - ``from __future__ import annotations`` for PEP 604 unions.
  - Reuse :func:`_frontmatter_end_offset` from :mod:`diff_generator`
    (RESEARCH "Don't Hand-Roll" row 2 — do not fork the helper).
  - Additive-only by construction (splicing never modifies existing bytes).
  - Frontmatter (between leading ``---`` fences) is NEVER touched (Pitfall #3).
"""

from __future__ import annotations

import difflib
import json
import logging
from typing import Any

from agent.evolution.diff_generator import _frontmatter_end_offset
from agent.evolution.insights import AggregationError, InsightRecord

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

EVOL02_SYSTEM_PROMPT = """\
You are generating structured patch instructions for a movie-expert skill in
the Hermes short-film production suite. An aggregation insight has identified
an improvement theme; your job is to emit concrete ADD-CONTENT instructions
that a downstream difflib generator will turn into a unified diff.

CRITICAL RULES:
1. ADDITIVE-ONLY. Never modify, delete, or restructure existing content.
   Every instruction ADDS a new content block after an existing anchor.
2. PRESERVE FRONTMATTER byte-for-byte. Never target an anchor inside the
   YAML frontmatter block (between the leading --- fences).
3. BILINGUAL CONTENT per CLAUDE.md convention. Each instruction's content
   MUST contain BOTH:
   - An EN heading (## ...) + EN body
   - A CN heading (### 中文标题 or similar) + CN body
   The EN block comes first, then a blank line, then the CN block.
4. ANCHOR SECTIONS must be existing unique section headers in the target
   file (e.g., "## Three-Act Structure"). The addition is inserted
   immediately AFTER the anchor's heading line.
5. OUTPUT STRICT JSON with this schema:
   {
     "instructions": [
       {
         "file": "skills/movie-experts/<expert>/references/<file>.md",
         "anchor_section": "## Existing Section Heading",
         "add_after": true,
         "content_en": "# EN Heading\\nEN body paragraphs...",
         "content_zh": "### 中文标题\\n中文正文段落..."
       }
     ]
   }
6. Emit 1-5 instructions per insight. If the insight does not map to a
   concrete addition, emit an empty instructions array.

The downstream generator validates every anchor and rejects instructions
whose anchor is missing, duplicate, or inside frontmatter.
"""


# --------------------------------------------------------------------------- #
# Bilingual block composition
# --------------------------------------------------------------------------- #


def _compose_bilingual_block(content_en: str, content_zh: str) -> str:
    """Compose an EN-then-CN bilingual content block.

    Per CLAUDE.md §"Skill File Conventions": EN heading + body first, then
    a blank line separator, then CN heading + body. Both inputs are
    stripped so leading/trailing whitespace from the LLM does not produce
    double blank lines.

    Args:
        content_en: EN-structure content (must start with a ``#`` heading).
        content_zh: CN-prose content (must start with a ``### 中文`` marker).

    Returns:
        The composed block with a trailing newline for clean splicing.
    """
    en = content_en.strip()
    zh = content_zh.strip()
    return f"{en}\n\n{zh}\n"


# --------------------------------------------------------------------------- #
# Core generator — build-final-state-then-diff
# --------------------------------------------------------------------------- #


def _validate_anchor(
    *,
    lines: list[str],
    anchor_section: str,
    file_path: str,
) -> int:
    """Validate the anchor section exists exactly once, outside frontmatter.

    Returns the 0-based line index of the anchor line (insertion happens
    AFTER this line).

    Raises:
        ValueError: anchor not found, anchor duplicate, or anchor inside
            the YAML frontmatter block (Pitfall #3).
    """
    matches = [
        i for i, line in enumerate(lines) if anchor_section in line
    ]
    if not matches:
        raise ValueError(
            f"anchor_section {anchor_section!r} not found in {file_path}"
        )
    if len(matches) > 1:
        raise ValueError(
            f"anchor_section {anchor_section!r} not unique in {file_path} "
            f"({len(matches)} matches) — provide a longer unique context"
        )
    insert_idx = matches[0]

    fm_end = _frontmatter_end_offset(lines)
    if fm_end is not None and (insert_idx + 1) <= fm_end:
        raise ValueError(
            f"anchor_section {anchor_section!r} is inside the YAML "
            f"frontmatter block of {file_path} (line {insert_idx + 1} is "
            f"at or before the closing '---' at line {fm_end}) — "
            f"frontmatter is immutable (SC-5, Pitfall #3)"
        )
    return insert_idx


def generate_patch_from_knowledge_point(
    *,
    insight: InsightRecord,
    current_files: dict[str, str],
    instructions: list[dict[str, Any]],
) -> str:
    """Generate a multi-instruction bilingual unified diff.

    Uses the build-final-state-then-diff-once approach: for each file
    touched, apply all its instructions sequentially to a working copy,
    then emit ONE ``difflib.unified_diff`` for that file. Multi-file
    patches join per-file diffs with ``"\\n"``.

    Args:
        insight: The InsightRecord motivating this patch (used for logging).
        current_files: Map of repo-relative path -> current file content.
        instructions: List of instruction dicts with keys ``file``,
            ``anchor_section``, ``add_after`` (bool), ``content_en``,
            ``content_zh``.

    Returns:
        Unified diff string (git-compatible, applies cleanly via P31
        :func:`apply_patch_transaction`).

    Raises:
        ValueError: on any validation failure (unknown file, missing/
            duplicate/frontmatter anchor, empty content_en/content_zh,
            idempotent no-op).
    """
    if not instructions:
        raise ValueError(
            "generate_patch_from_knowledge_point requires >= 1 instruction"
        )

    # Group instructions by file so we can build final state per file.
    by_file: dict[str, list[dict[str, Any]]] = {}
    for inst in instructions:
        file_path = inst.get("file")
        if not isinstance(file_path, str) or not file_path:
            raise ValueError(
                f"instruction missing 'file' key: {inst!r}"
            )
        if file_path not in current_files:
            raise ValueError(
                f"instruction targets unknown file {file_path!r} "
                f"(not in current_files)"
            )
        by_file.setdefault(file_path, []).append(inst)

    per_file_diffs: list[str] = []
    for file_path, file_instructions in by_file.items():
        original = current_files[file_path].replace("\r\n", "\n")
        original_lines = original.splitlines(keepends=True)
        working = list(original_lines)  # mutable copy

        for inst in file_instructions:
            anchor = inst.get("anchor_section")
            if not isinstance(anchor, str) or not anchor:
                raise ValueError(
                    f"instruction for {file_path} missing 'anchor_section'"
                )
            content_en = inst.get("content_en")
            content_zh = inst.get("content_zh")
            if not isinstance(content_en, str) or not content_en.strip():
                raise ValueError(
                    f"instruction for {file_path} has empty content_en"
                )
            if not isinstance(content_zh, str) or not content_zh.strip():
                raise ValueError(
                    f"instruction for {file_path} has empty content_zh"
                )
            add_after = inst.get("add_after", True)
            if not add_after:
                # add_after=False means insert BEFORE the anchor — currently
                # unsupported (would complicate frontmatter validation).
                # Surface as an explicit ValueError rather than silently
                # defaulting.
                raise ValueError(
                    f"instruction for {file_path} has add_after=False — "
                    f"only add_after=True is supported (additive-only)"
                )

            insert_idx = _validate_anchor(
                lines=working,
                anchor_section=anchor,
                file_path=file_path,
            )
            block = _compose_bilingual_block(content_en, content_zh)
            block_lines = block.splitlines(keepends=True)
            # Ensure separation if the preceding line lacks a trailing newline.
            if working and not working[insert_idx].endswith("\n"):
                block_lines = ["\n"] + block_lines

            # Idempotent guard: if the block is already present immediately
            # after the anchor, raise (no-op). This catches re-running the
            # same instruction against an already-patched file.
            existing_tail = working[insert_idx + 1: insert_idx + 1 + len(block_lines)]
            if existing_tail == block_lines:
                raise ValueError(
                    f"proposed addition for {file_path} at anchor "
                    f"{anchor!r} already present at insertion site "
                    f"— no diff generated (idempotent)"
                )

            working = (
                working[:insert_idx + 1]
                + block_lines
                + working[insert_idx + 1:]
            )

        # Idempotent guard: if nothing actually changed, raise.
        if working == original_lines:
            raise ValueError(
                f"proposed additions for {file_path} already present "
                f"— no diff generated (idempotent)"
            )

        diff = "".join(
            difflib.unified_diff(
                original_lines,
                working,
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
                lineterm="\n",
            )
        )
        if not diff.strip():
            raise ValueError(
                f"generated diff for {file_path} is empty — no net change"
            )
        per_file_diffs.append(diff)

    logger.info(
        "generated EVOL-02 patch for insight %s across %d file(s)",
        insight.insight_id, len(by_file),
    )
    return "\n".join(per_file_diffs)


# --------------------------------------------------------------------------- #
# LLM instruction emission (separate pass — does NOT modify aggregate_feedback)
# --------------------------------------------------------------------------- #


def emit_evol02_instructions(
    *,
    insight: InsightRecord,
    current_files: dict[str, str],
    client: Any,
    model: str,
) -> list[dict[str, Any]]:
    """Invoke the LLM to emit structured EVOL-02 instructions for one insight.

    SEPARATE pass from P31 :func:`aggregate_feedback` — does not modify it.
    Mirrors the LLM-call pattern from :func:`aggregate_feedback`:
    ``response_format={"type": "json_object"}`` with one retry without it.

    Args:
        insight: The InsightRecord to convert into patch instructions.
        current_files: Map of repo-relative path -> current content (only
            keys are sent to the LLM — content bodies are NOT, to bound
            token cost and avoid leaking skill body text).
        client: OpenAI-shaped client.
        model: Model name.

    Returns:
        List of validated instruction dicts (each has keys ``file``,
        ``anchor_section``, ``add_after``, ``content_en``, ``content_zh``).

    Raises:
        AggregationError: on malformed LLM JSON output, missing
            ``instructions`` key, non-list instructions, or any instruction
            missing required keys / wrong types.
    """
    user_prompt = (
        f"Insight theme: {insight.theme}\n"
        f"Insight rationale: {insight.rationale}\n"
        f"Proposed addition (aggregation output):\n{insight.proposed_addition}\n"
        f"Insert-after marker (aggregation output): {insight.insert_after_marker}\n\n"
        f"Target files available (repo-relative paths):\n"
        f"{json.dumps(sorted(current_files.keys()), indent=2)}\n\n"
        f"Emit structured instructions for the difflib generator. Each "
        f"instruction's 'file' MUST be one of the paths listed above. Each "
        f"'anchor_section' MUST be an existing unique heading in that file."
    )
    messages: list[dict[str, str]] = [
        {"role": "system", "content": EVOL02_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    content: str | None = None
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
    except Exception as exc:
        logger.warning(
            "evol02 LLM call with response_format failed (%s); "
            "retrying without response_format",
            exc,
        )
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        content = resp.choices[0].message.content

    if content is None:
        raise AggregationError("evol02 LLM returned None content")

    # Strip markdown fences (reuse insights pattern).
    import re
    fence_re = re.compile(r"^```(?:json)?\s*\n?|\n?```\s*$", re.MULTILINE)
    stripped = fence_re.sub("", content)

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise AggregationError(
            f"evol02 LLM returned malformed JSON: {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise AggregationError(
            f"evol02 JSON top-level must be an object, got {type(payload).__name__}"
        )
    raw_instructions = payload.get("instructions")
    if raw_instructions is None:
        raise AggregationError("evol02 JSON missing 'instructions' key")
    if not isinstance(raw_instructions, list):
        raise AggregationError(
            f"'instructions' must be a list, got {type(raw_instructions).__name__}"
        )

    # Validate each instruction has required keys with correct types.
    required_keys = {
        "file", "anchor_section", "add_after", "content_en", "content_zh",
    }
    validated: list[dict[str, Any]] = []
    errors: list[str] = []
    for i, raw in enumerate(raw_instructions):
        if not isinstance(raw, dict):
            errors.append(f"instruction[{i}] not an object: {type(raw).__name__}")
            continue
        missing = required_keys - set(raw.keys())
        if missing:
            errors.append(f"instruction[{i}] missing keys: {sorted(missing)}")
            continue
        if not isinstance(raw["file"], str) or not raw["file"]:
            errors.append(f"instruction[{i}].file must be non-empty str")
            continue
        if not isinstance(raw["anchor_section"], str) or not raw["anchor_section"]:
            errors.append(f"instruction[{i}].anchor_section must be non-empty str")
            continue
        if not isinstance(raw["add_after"], bool):
            errors.append(f"instruction[{i}].add_after must be bool")
            continue
        if not isinstance(raw["content_en"], str) or not raw["content_en"].strip():
            errors.append(f"instruction[{i}].content_en must be non-empty str")
            continue
        if not isinstance(raw["content_zh"], str) or not raw["content_zh"].strip():
            errors.append(f"instruction[{i}].content_zh must be non-empty str")
            continue
        validated.append(dict(raw))

    if errors:
        raise AggregationError(
            f"{len(errors)} evol02 instruction(s) failed validation: "
            + "; ".join(errors)
        )

    logger.info(
        "emitted %d evol02 instruction(s) for insight %s",
        len(validated), insight.insight_id,
    )
    return validated
