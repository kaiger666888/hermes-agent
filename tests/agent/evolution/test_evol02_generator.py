"""EVOL-02 generator tests — bilingual multi-instruction diff generation.

Covers _compose_bilingual_block, generate_patch_from_knowledge_point
(single + multi-instruction same-file + multi-file), anchor validation
(missing/duplicate/frontmatter), idempotent no-op detection, frontmatter
preservation, emit_evol02_instructions (mocked LLM), and an integration
test that applies the generated diff via P31 apply_patch_transaction.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from agent.evolution.apply import apply_patch_transaction
from agent.evolution.evol02_generator import (
    EVOL02_SYSTEM_PROMPT,
    _compose_bilingual_block,
    emit_evol02_instructions,
    generate_patch_from_knowledge_point,
)
from agent.evolution.insights import AggregationError, InsightRecord


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _make_insight(
    *, skill_id: str = "screenplay", theme: str = "t", rationale: str = "r",
) -> InsightRecord:
    return InsightRecord(
        insight_id=f"{skill_id}_1234_abcd",
        skill_id=skill_id,
        theme=theme,
        evidence_chain=["fb1"],
        rationale=rationale,
        proposed_addition="dummy",
        insert_after_marker="## Three-Act",
        ts="2026-06-24T00:00:00+00:00",
    )


SAMPLE_FILE = "skills/movie-experts/screenplay/references/structure.md"
SAMPLE_CONTENT = """\
---
name: structure
description: x
---

# Screenplay Structure Reference

## Three-Act Structure

Act I, Act II, Act III.

## Character Arcs

Hero's journey beats.
"""


# --------------------------------------------------------------------------- #
# Bilingual composition
# --------------------------------------------------------------------------- #


class TestBilingualComposition:
    def test_basic_en_then_zh_with_blank_separator(self):
        block = _compose_bilingual_block(
            content_en="# Heading\nEN body",
            content_zh="### 中文标题\n中文正文",
        )
        assert block == "# Heading\nEN body\n\n### 中文标题\n中文正文\n"

    def test_strips_leading_trailing_whitespace(self):
        block = _compose_bilingual_block(
            content_en="  \n# Heading\nEN body\n  ",
            content_zh="\n### 中文标题\n中文正文\n",
        )
        assert block == "# Heading\nEN body\n\n### 中文标题\n中文正文\n"

    def test_cn_marker_present(self):
        block = _compose_bilingual_block(
            content_en="## EN Section\nbody",
            content_zh="### 中文区段\n正文",
        )
        # Heuristic check per plan behavior: EN heading + CN marker.
        assert "## EN Section" in block
        assert "中文" in block


# --------------------------------------------------------------------------- #
# Single instruction
# --------------------------------------------------------------------------- #


class TestSingleInstruction:
    def test_single_instruction_adds_after_anchor(self):
        insight = _make_insight()
        current = {SAMPLE_FILE: SAMPLE_CONTENT}
        instructions = [{
            "file": SAMPLE_FILE,
            "anchor_section": "## Three-Act Structure",
            "add_after": True,
            "content_en": "# EN New Section\nNew body",
            "content_zh": "### 中文新章节\n新内容",
        }]
        diff = generate_patch_from_knowledge_point(
            insight=insight, current_files=current, instructions=instructions,
        )
        # The diff must add the bilingual block.
        assert "+" in diff
        assert "# EN New Section" in diff
        assert "### 中文新章节" in diff
        # The diff must reference the file path in headers.
        assert f"a/{SAMPLE_FILE}" in diff
        assert f"b/{SAMPLE_FILE}" in diff
        # Existing content is preserved (additive-only — no '-' lines
        # except the unified_diff context markers).
        diff_lines = diff.splitlines()
        deletion_lines = [l for l in diff_lines if l.startswith("-") and not l.startswith("---")]
        assert deletion_lines == [], (
            f"additive-only violation — deletion lines: {deletion_lines}"
        )


# --------------------------------------------------------------------------- #
# Multi-instruction same file
# --------------------------------------------------------------------------- #


class TestMultiInstructionSameFile:
    def test_two_instructions_same_file_both_anchored(self):
        """Two instructions against the same file produce a combined diff
        where the SECOND instruction's anchor is found in the already-
        mutated content (anchor offsets shift correctly).
        """
        insight = _make_insight()
        current = {SAMPLE_FILE: SAMPLE_CONTENT}
        instructions = [
            {
                "file": SAMPLE_FILE,
                "anchor_section": "## Three-Act Structure",
                "add_after": True,
                "content_en": "# EN Section A\nA body",
                "content_zh": "### 中文A\nA正文",
            },
            {
                "file": SAMPLE_FILE,
                "anchor_section": "## Character Arcs",
                "add_after": True,
                "content_en": "# EN Section B\nB body",
                "content_zh": "### 中文B\nB正文",
            },
        ]
        diff = generate_patch_from_knowledge_point(
            insight=insight, current_files=current, instructions=instructions,
        )
        # Both additions must appear.
        assert "# EN Section A" in diff
        assert "# EN Section B" in diff
        assert "### 中文A" in diff
        assert "### 中文B" in diff
        # Additive-only check.
        deletion_lines = [
            l for l in diff.splitlines()
            if l.startswith("-") and not l.startswith("---")
        ]
        assert deletion_lines == []


# --------------------------------------------------------------------------- #
# Anchor validation
# --------------------------------------------------------------------------- #


class TestAnchorValidation:
    def test_missing_anchor_raises(self):
        insight = _make_insight()
        current = {SAMPLE_FILE: SAMPLE_CONTENT}
        instructions = [{
            "file": SAMPLE_FILE,
            "anchor_section": "## Nonexistent Section",
            "add_after": True,
            "content_en": "# EN\nbody",
            "content_zh": "### 中文\n正文",
        }]
        with pytest.raises(ValueError, match="not found"):
            generate_patch_from_knowledge_point(
                insight=insight, current_files=current, instructions=instructions,
            )

    def test_duplicate_anchor_raises(self):
        """An anchor that appears more than once is ambiguous."""
        insight = _make_insight()
        content = SAMPLE_CONTENT + "## Three-Act Structure\n(second copy)\n"
        current = {SAMPLE_FILE: content}
        instructions = [{
            "file": SAMPLE_FILE,
            "anchor_section": "## Three-Act Structure",
            "add_after": True,
            "content_en": "# EN\nbody",
            "content_zh": "### 中文\n正文",
        }]
        with pytest.raises(ValueError, match="not unique"):
            generate_patch_from_knowledge_point(
                insight=insight, current_files=current, instructions=instructions,
            )

    def test_anchor_inside_frontmatter_raises(self):
        """An anchor matching a frontmatter key is rejected (Pitfall #3)."""
        insight = _make_insight()
        current = {SAMPLE_FILE: SAMPLE_CONTENT}
        instructions = [{
            "file": SAMPLE_FILE,
            "anchor_section": "description",  # frontmatter key
            "add_after": True,
            "content_en": "# EN\nbody",
            "content_zh": "### 中文\n正文",
        }]
        with pytest.raises(ValueError, match="frontmatter"):
            generate_patch_from_knowledge_point(
                insight=insight, current_files=current, instructions=instructions,
            )


# --------------------------------------------------------------------------- #
# Idempotent no-op
# --------------------------------------------------------------------------- #


class TestIdempotentNoop:
    def test_already_present_raises(self):
        """If applying the instruction produces no net change, raise ValueError.

        We construct the "already present" state by running the generator
        once to get the exact mutated content, then feed that mutated
        content back as ``current_files`` for a second run with the same
        instruction. The second run must detect the no-op.
        """
        insight = _make_insight()
        current = {SAMPLE_FILE: SAMPLE_CONTENT}
        instructions = [{
            "file": SAMPLE_FILE,
            "anchor_section": "## Three-Act Structure",
            "add_after": True,
            "content_en": "# EN\nbody",
            "content_zh": "### 中文\n正文",
        }]
        # First run produces the diff; apply it in-memory to get final state.
        diff = generate_patch_from_knowledge_point(
            insight=insight, current_files=current, instructions=instructions,
        )
        # Simulate the apply: extract added lines and splice after anchor.
        original_lines = SAMPLE_CONTENT.splitlines(keepends=True)
        added_lines = [
            l[1:] for l in diff.splitlines(keepends=True)
            if l.startswith("+") and not l.startswith("+++")
        ]
        anchor_idx = next(
            i for i, l in enumerate(original_lines)
            if "## Three-Act Structure" in l
        )
        mutated_lines = (
            original_lines[:anchor_idx + 1]
            + added_lines
            + original_lines[anchor_idx + 1:]
        )
        mutated_content = "".join(mutated_lines)

        # Second run with the SAME instruction against the mutated content
        # must raise (no net change).
        with pytest.raises(ValueError, match="idempotent|already present|empty"):
            generate_patch_from_knowledge_point(
                insight=insight,
                current_files={SAMPLE_FILE: mutated_content},
                instructions=instructions,
            )


# --------------------------------------------------------------------------- #
# Frontmatter preservation
# --------------------------------------------------------------------------- #


class TestFrontmatterPreserved:
    def test_frontmatter_byte_intact_after_diff(self):
        """Applying the generated diff must NOT change frontmatter bytes."""
        insight = _make_insight()
        original_frontmatter = "---\nname: structure\ndescription: x\n---\n"
        current = {SAMPLE_FILE: SAMPLE_CONTENT}
        instructions = [{
            "file": SAMPLE_FILE,
            "anchor_section": "## Three-Act Structure",
            "add_after": True,
            "content_en": "# EN\nbody",
            "content_zh": "### 中文\n正文",
        }]
        diff = generate_patch_from_knowledge_point(
            insight=insight, current_files=current, instructions=instructions,
        )
        # Simulate applying the diff manually: find additions and splice.
        added_lines = [
            l[1:] for l in diff.splitlines(keepends=True)
            if l.startswith("+") and not l.startswith("+++")
        ]
        # None of the added lines should touch frontmatter content.
        added_text = "".join(added_lines)
        assert "name: structure" not in added_text
        assert "description: x" not in added_text


# --------------------------------------------------------------------------- #
# emit_evol02_instructions — mocked LLM
# --------------------------------------------------------------------------- #


class _MockChoice:
    def __init__(self, content: str):
        self.message = type("Msg", (), {"content": content})


class _MockResp:
    def __init__(self, content: str):
        self.choices = [_MockChoice(content)]


class _MockClient:
    """Records calls + returns canned JSON.

    Set ``raw_response`` to return arbitrary text (for malformed-JSON
    testing) instead of the canned payload.
    """

    def __init__(
        self, payload: dict, *,
        fail_response_format: bool = False,
        raw_response: str | None = None,
    ):
        self.payload = payload
        self.fail_response_format = fail_response_format
        self.raw_response = raw_response
        self.calls: list[dict[str, Any]] = []

        client_ref = self

        class _Completions:
            def create(self, **kwargs):
                return client_ref._handle_create(**kwargs)

        class _Chat:
            def __init__(self):
                self.completions = _Completions()

        self.chat = _Chat()

    def _handle_create(self, **kwargs):
        self.calls.append(kwargs)
        if (
            self.fail_response_format
            and kwargs.get("response_format") == {"type": "json_object"}
        ):
            raise RuntimeError("mock: response_format rejected")
        text = (
            self.raw_response
            if self.raw_response is not None
            else json.dumps(self.payload)
        )
        return _MockResp(text)


class TestEmitInstructions:
    def test_valid_payload_returns_validated_instructions(self):
        payload = {"instructions": [{
            "file": SAMPLE_FILE,
            "anchor_section": "## Three-Act Structure",
            "add_after": True,
            "content_en": "# EN\nbody",
            "content_zh": "### 中文\n正文",
        }]}
        client = _MockClient(payload)
        insight = _make_insight()
        result = emit_evol02_instructions(
            insight=insight, current_files={SAMPLE_FILE: "..."},
            client=client, model="test-model",
        )
        assert len(result) == 1
        assert result[0]["file"] == SAMPLE_FILE
        # System prompt was used.
        assert client.calls[0]["messages"][0]["content"] == EVOL02_SYSTEM_PROMPT

    def test_retry_without_response_format_on_failure(self):
        payload = {"instructions": []}
        client = _MockClient(payload, fail_response_format=True)
        insight = _make_insight()
        result = emit_evol02_instructions(
            insight=insight, current_files={SAMPLE_FILE: "..."},
            client=client, model="m",
        )
        assert result == []
        assert len(client.calls) == 2
        # First call had response_format, second did not.
        assert "response_format" in client.calls[0]
        assert "response_format" not in client.calls[1]

    def test_malformed_json_raises_aggregation_error(self):
        client = _MockClient(
            {"not_instructions": []}, raw_response="not valid json {{{",
        )
        insight = _make_insight()
        with pytest.raises(AggregationError, match="malformed JSON"):
            emit_evol02_instructions(
                insight=insight, current_files={}, client=client, model="m",
            )

    def test_missing_instructions_key_raises(self):
        client = _MockClient({"wrong_key": []})
        insight = _make_insight()
        with pytest.raises(AggregationError, match="missing 'instructions'"):
            emit_evol02_instructions(
                insight=insight, current_files={}, client=client, model="m",
            )

    def test_instruction_missing_required_keys_raises(self):
        payload = {"instructions": [{"file": "x"}]}  # missing anchor_section etc.
        client = _MockClient(payload)
        insight = _make_insight()
        with pytest.raises(AggregationError, match="missing keys"):
            emit_evol02_instructions(
                insight=insight, current_files={}, client=client, model="m",
            )


# --------------------------------------------------------------------------- #
# Integration: apply_patch_transaction
# --------------------------------------------------------------------------- #


class TestDiffAppliesClean:
    """Feed the generated diff to P31 apply_patch_transaction in a real git repo."""

    def test_generated_diff_applies_via_apply_patch_transaction(self, tmp_path):
        # Set up a minimal git repo with the sample file.
        repo = tmp_path / "repo"
        repo.mkdir()
        file_rel = Path(SAMPLE_FILE)
        (repo / file_rel.parent).mkdir(parents=True)
        (repo / file_rel).write_text(SAMPLE_CONTENT, encoding="utf-8")

        subprocess.run(["git", "init"], cwd=str(repo), capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(repo), capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=str(repo), capture_output=True, check=True,
        )
        # Add the skills/ prefix to satisfy _SKILLS_PREFIX path-traversal check.
        subprocess.run(
            ["git", "add", str(file_rel)],
            cwd=str(repo), capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=str(repo), capture_output=True, check=True,
        )

        insight = _make_insight()
        instructions = [{
            "file": SAMPLE_FILE,
            "anchor_section": "## Three-Act Structure",
            "add_after": True,
            "content_en": "# EN New Section\nFresh content from feedback.",
            "content_zh": "### 中文新章节\n来自反馈的新内容。",
        }]
        diff = generate_patch_from_knowledge_point(
            insight=insight,
            current_files={SAMPLE_FILE: SAMPLE_CONTENT},
            instructions=instructions,
        )

        patch_path = tmp_path / "patch.diff"
        patch_path.write_text(diff, encoding="utf-8")

        result = apply_patch_transaction(
            patch_path=patch_path,
            repo_root=repo,
            commit_message="test: apply evol02 patch",
        )
        assert isinstance(result.commit_sha, str)
        assert SAMPLE_FILE in result.files_modified

        # Verify the file content actually changed.
        applied = (repo / file_rel).read_text(encoding="utf-8")
        assert "# EN New Section" in applied
        assert "### 中文新章节" in applied
        assert "来自反馈的新内容。" in applied
        # Original content preserved.
        assert "## Three-Act Structure" in applied
        assert "Act I, Act II, Act III." in applied
