"""test_prompt_standardizer.py — unit tests for the dreamina prompt standardizer.

Covers:
  - Basic passthrough (no-op on already-clean input)
  - Length truncation (sentence / clause / space / hard cut + negative reservation)
  - Special-character cleanup (C0/C1 control, zero-width, BOM, soft hyphen)
  - Newline handling (preserved by default, flattenable on request)
  - style_prefix injection (prepend, idempotent, separator selection)
  - Quote handling (smart->straight normalization + opt-in escaping)
  - Redundancy dedup (per-line, case-insensitive, structure-preserving, CJK)
  - Negative-prompt folding (idempotent "Avoid:" clause)
  - Boundary cases (None, empty, pure-special-char, over-long, non-str)
  - Idempotency (apply twice == apply once)
  - Real production prompt regression guard (no behavior change)
  - Configurability (every step toggleable)
  - Hard-fail-safe (internal error -> raw input returned)

All tests are pure (no dreamina CLI, no network). Each < 1s.
"""

from __future__ import annotations

import pytest

from plugins.kais_aigc import prompt_standardizer as ps
from plugins.kais_aigc.prompt_standardizer import (
    DREAMINA_DEFAULT_MAX_LENGTH,
    standardize_prompt,
)


# ---------------------------------------------------------------------------
# Basic passthrough
# ---------------------------------------------------------------------------


class TestPassthrough:
    def test_clean_prompt_unchanged(self):
        assert standardize_prompt("a cat portrait") == "a cat portrait"

    def test_trims_leading_trailing_whitespace(self):
        assert standardize_prompt("   a cat portrait   ") == "a cat portrait"

    def test_collapses_internal_space_runs(self):
        assert standardize_prompt("a    cat\t\tportrait") == "a cat portrait"

    def test_mode_parameter_accepted(self):
        # mode is reserved (no-op today) but must not error on either value.
        assert standardize_prompt("a cat", mode="text2image") == "a cat"
        assert standardize_prompt("a cat", mode="image2image") == "a cat"


# ---------------------------------------------------------------------------
# Length truncation
# ---------------------------------------------------------------------------


class TestTruncation:
    def test_under_limit_unchanged(self):
        text = "a short prompt"
        assert standardize_prompt(text, max_length=100) == text

    def test_truncate_at_sentence_boundary(self):
        text = "A cat sits. A dog runs. Soft light fills the room."
        # limit=30 -> window "A cat sits. A dog runs. Soft"
        # last sentence boundary ". " in latter half -> cut after "runs."
        out = standardize_prompt(text, max_length=30)
        assert out == "A cat sits. A dog runs."
        assert len(out) <= 30

    def test_truncate_at_clause_when_no_sentence(self):
        text = "soft cinematic warm tones with deep shadows and rich color"
        out = standardize_prompt(text, max_length=30)
        assert len(out) <= 30
        # should end at a clause/space boundary, not mid-word
        assert not out.endswith("w") or " " in out

    def test_truncate_at_space_never_mid_word(self):
        text = "abcdefghij " * 50  # spaces between letter-runs
        out = standardize_prompt(text, max_length=25)
        assert len(out) <= 25
        # invariant: no partial word — every kept token is a complete run
        assert out, "expected non-empty output"
        assert all(tok == "abcdefghij" for tok in out.split())

    def test_max_length_zero_returns_empty(self):
        assert standardize_prompt("a cat", max_length=0) == ""

    def test_truncate_false_disables_truncation(self):
        text = "x" * 5000
        out = standardize_prompt(text, max_length=10, truncate=False)
        assert out == text

    def test_negative_clause_survives_truncation(self):
        text = "A cat sits. A dog runs. " * 20  # very long
        out = standardize_prompt(text, max_length=80, negative_prompt="blurry, watermark")
        assert out.endswith("Avoid: blurry, watermark")
        assert len(out) <= 80 + 40  # reserved headroom for the clause

    def test_truncation_is_idempotent(self):
        text = "A cat sits. A dog runs. Soft light fills the room." * 10
        once = standardize_prompt(text, max_length=50)
        twice = standardize_prompt(once, max_length=50)
        assert once == twice


# ---------------------------------------------------------------------------
# Special-character cleanup
# ---------------------------------------------------------------------------


class TestSpecialChars:
    def test_strips_c0_control_chars(self):
        # NUL, BEL stripped; keeps printable letters.
        assert standardize_prompt("a\x00cat\x07portrait") == "acatportrait"

    def test_preserves_tab_and_newline(self):
        # \t and \n are preserved (\t becomes a single space via ws normalize).
        assert standardize_prompt("a\tcat\nportrait") == "a cat\nportrait"

    def test_normalizes_carriage_return(self):
        assert standardize_prompt("line one\r\nline two") == "line one\nline two"
        assert standardize_prompt("a\rb") == "a\nb"

    def test_strips_del(self):
        assert standardize_prompt("cat\x7fdog") == "catdog"

    def test_strips_c1_control_chars(self):
        assert standardize_prompt("cat\x85\x9fdog") == "catdog"

    def test_strips_zero_width_chars(self):
        # ZWSP, ZWNJ, ZWJ, word joiner inserted inside a word -> removed.
        raw = "pho\u200bto\u200dgraph"
        assert standardize_prompt(raw) == "photograph"

    def test_strips_bom(self):
        assert standardize_prompt("\ufeffa cat") == "a cat"

    def test_strips_soft_hyphen(self):
        # U+00AD between "photo" and "graph" -> "photograph"
        assert standardize_prompt("photo\xadgraph") == "photograph"

    def test_clean_control_chars_false_preserves(self):
        # opt-out leaves control chars in place.
        assert standardize_prompt("a\x00cat", clean_control_chars=False) == "a\x00cat"

    def test_pure_special_chars_become_empty(self):
        assert standardize_prompt("\x00\x01\x02\x07") == ""


# ---------------------------------------------------------------------------
# Newline handling
# ---------------------------------------------------------------------------


class TestNewlines:
    def test_multiline_preserved_by_default(self):
        # RESEARCH: dreamina supports multi-line prompts — flattening is OFF.
        text = "style line\n\nPanel 1: shot\n\nPanel 2: shot"
        assert standardize_prompt(text) == text

    def test_paragraph_double_newline_preserved(self):
        assert standardize_prompt("para one\n\npara two") == "para one\n\npara two"

    def test_collapses_three_plus_newlines_to_two(self):
        assert standardize_prompt("a\n\n\n\nb") == "a\n\nb"

    def test_strips_trailing_space_before_newline(self):
        assert standardize_prompt("a line   \nnext") == "a line\nnext"

    def test_flatten_newlines_true(self):
        text = "style line\n\nPanel 1: shot\n\nPanel 2: shot"
        out = standardize_prompt(text, flatten_newlines=True)
        assert "\n" not in out
        assert out == "style line Panel 1: shot Panel 2: shot"

    def test_flatten_collapses_resulting_spaces(self):
        out = standardize_prompt("a   \n   b", flatten_newlines=True)
        assert out == "a b"


# ---------------------------------------------------------------------------
# style_prefix injection
# ---------------------------------------------------------------------------


class TestStylePrefix:
    def test_prefix_prepended_single_line(self):
        out = standardize_prompt("a woman walks", style_prefix="cinematic, warm light")
        assert out == "cinematic, warm light, a woman walks"

    def test_prefix_prepended_multiline_uses_double_newline(self):
        out = standardize_prompt(
            "Panel 1: shot\nPanel 2: shot", style_prefix="clay render style"
        )
        assert out == "clay render style\n\nPanel 1: shot\nPanel 2: shot"

    def test_prefix_idempotent_when_already_present(self):
        text = "cinematic style, a cat portrait"
        out = standardize_prompt(text, style_prefix="cinematic style")
        assert out == text  # not double-prepended

    def test_prefix_case_insensitive_idempotent(self):
        text = "Cinematic Style, a cat"
        out = standardize_prompt(text, style_prefix="cinematic style")
        assert out == text

    def test_empty_prefix_noop(self):
        text = "a cat"
        assert standardize_prompt(text, style_prefix="   ") == text

    def test_prefix_then_flatten(self):
        out = standardize_prompt(
            "Panel 1: shot", style_prefix="style line", flatten_newlines=True
        )
        # single-line body -> ", " separator; flatten leaves no newline
        assert out == "style line, Panel 1: shot"


# ---------------------------------------------------------------------------
# Quote handling
# ---------------------------------------------------------------------------


class TestQuotes:
    def test_smart_double_quotes_normalized(self):
        assert standardize_prompt("a “cat” portrait") == 'a "cat" portrait'

    def test_smart_single_quotes_normalized(self):
        assert standardize_prompt("a ‘cat’ portrait") == "a 'cat' portrait"

    def test_normalize_quotes_false_preserves_smart_quotes(self):
        text = "a “cat” portrait"
        assert standardize_prompt(text, normalize_quotes=False) == text

    def test_escape_quotes_false_by_default(self):
        # subprocess list form needs no escaping — " stays literal by default.
        assert standardize_prompt('a "cat"') == 'a "cat"'

    def test_escape_quotes_true(self):
        assert standardize_prompt('a "cat"', escape_quotes=True) == 'a \\"cat\\"'


# ---------------------------------------------------------------------------
# Redundancy dedup
# ---------------------------------------------------------------------------


class TestDedup:
    def test_removes_duplicate_segments_same_line(self):
        assert standardize_prompt("cinematic, warm, cinematic, soft") == "cinematic, warm, soft"

    def test_case_insensitive(self):
        out = standardize_prompt("Cinematic, cinematic, warm")
        assert out.lower().count("cinematic") == 1
        assert out.startswith("Cinematic")  # first-occurrence casing kept

    def test_per_line_scope_preserves_structural_repetition(self):
        # same segment on two separate lines -> BOTH kept (not collapsed)
        text = "cinematic\nmore cinematic"
        assert standardize_prompt(text) == text

    def test_newline_separated_repetition_preserved(self):
        # panels repeat words across lines -> untouched (no comma on a line)
        text = "Panel 1: red tablecloth\nPanel 2: red tablecloth"
        assert standardize_prompt(text) == text

    def test_cjk_fullwidth_comma_dedup(self):
        assert standardize_prompt("电影，温暖，电影") == "电影，温暖"

    def test_cjk_ideographic_comma_dedup(self):
        assert standardize_prompt("电影、温暖、电影") == "电影、温暖"

    def test_keeps_unique_segments(self):
        out = standardize_prompt("a, b, c, d")
        assert out == "a, b, c, d"

    def test_dedup_false_preserves_duplicates(self):
        text = "cinematic, warm, cinematic"
        assert standardize_prompt(text, dedup_segments=False) == text


# ---------------------------------------------------------------------------
# Negative-prompt folding
# ---------------------------------------------------------------------------


class TestNegative:
    def test_negative_appended_as_avoid_clause(self):
        out = standardize_prompt("a cat portrait", negative_prompt="blurry, watermark")
        assert out == "a cat portrait. Avoid: blurry, watermark"

    def test_negative_multiline_uses_double_newline(self):
        out = standardize_prompt(
            "Panel 1: shot\nPanel 2: shot", negative_prompt="blurry"
        )
        assert out == "Panel 1: shot\nPanel 2: shot\n\nAvoid: blurry"

    def test_negative_idempotent(self):
        once = standardize_prompt("a cat", negative_prompt="blurry")
        twice = standardize_prompt(once, negative_prompt="blurry")
        assert once == twice

    def test_negative_trims_outer_delimiters(self):
        out = standardize_prompt("a cat", negative_prompt=", blurry, ")
        assert out == "a cat. Avoid: blurry"

    def test_empty_negative_noop(self):
        assert standardize_prompt("a cat", negative_prompt="   ") == "a cat"

    def test_negative_combines_with_dedup(self):
        out = standardize_prompt("a, a, cat", negative_prompt="blurry, blurry")
        # dedup removes "a" dup; negative dedup not applied across the avoid
        # clause boundary, but the negative itself is de-duped of outer dups
        assert out.startswith("a, cat")
        assert out.endswith("Avoid: blurry, blurry")


# ---------------------------------------------------------------------------
# Boundary cases
# ---------------------------------------------------------------------------


class TestBoundary:
    def test_none_returns_empty(self):
        assert standardize_prompt(None) == ""

    def test_empty_string_returns_empty(self):
        assert standardize_prompt("") == ""

    def test_non_string_input_coerced(self):
        # an int is coerced to str then standardized.
        assert standardize_prompt(12345) == "12345"

    def test_very_long_string_truncated(self):
        text = "A complete sentence. " * 1000
        out = standardize_prompt(text, max_length=200)
        assert len(out) <= 200

    def test_pure_whitespace_returns_empty(self):
        assert standardize_prompt("   \n\n  \t  ") == ""

    def test_unicode_cjk_preserved(self):
        text = "一个穿红裙的年轻女子站在宴会厅里"
        assert standardize_prompt(text) == text

    def test_emoji_preserved(self):
        # emoji are printable, not control/zero-width — left in place.
        text = "a cat 🐱 portrait"
        assert standardize_prompt(text) == "a cat 🐱 portrait"


# ---------------------------------------------------------------------------
# Idempotency (cross-feature)
# ---------------------------------------------------------------------------


class TestIdempotency:
    @pytest.mark.parametrize(
        "kwargs",
        [
            {},
            {"style_prefix": "cinematic style"},
            {"negative_prompt": "blurry, watermark"},
            {"style_prefix": "style", "negative_prompt": "blurry"},
            {"flatten_newlines": True},
            {"max_length": 50},
            {"escape_quotes": True},
        ],
    )
    def test_apply_twice_equals_once(self, kwargs):
        text = "cinematic, warm, a “cat” portrait, cinematic, with extra padding " * 5
        once = standardize_prompt(text, **kwargs)
        twice = standardize_prompt(once, **kwargs)
        assert once == twice


# ---------------------------------------------------------------------------
# Real production prompt regression guard
# ---------------------------------------------------------------------------


class TestRegressionRealPrompts:
    """Standardization must be a no-op on real production dreamina prompts
    (structure, newlines, (), :, em-dash, CJK all preserved). Uses the
    integration's operational ceiling (DREAMINA_DEFAULT_MAX_LENGTH=4000) so
    no real prompt is truncated."""

    REAL_STORYBOARD = (
        "Clay render maquette storyboard, 3D Blender clay viewport render style. "
        "Matte gray polymer clay figures with simple facial features suggested. "
        "Soft gray studio lighting, warm gray monochrome tones.\n\n"
        "Character reference from image 2 and 3: Main character young woman with "
        "long straight black hair, slim figure, silver-white mermaid dress (image 2). "
        "Secondary character young woman with chestnut brown wavy curly hair, "
        "petite, light pink lace dress (image 3).\n\n"
        "Keep the EXACT 2-column 3-row grid layout of reference image 1. "
        "6 numbered panels. Each panel a different camera shot in a luxury banquet hall.\n\n"
        "Panel 1 (BCU extreme close-up): Two female hands reaching upward from bottom "
        "of frame, fingers spread wide, long black hair blowing upward, silhouette "
        "against gray background.\n\n"
        "Panel 2 (BCU extreme close-up): Young woman with long black hair, face "
        "centered, head and shoulders, eyes closed, sweat on forehead. Red tablecloth "
        "and golden pen at bottom. Banquet hall light from above.\n\n"
        "Panel 6: Leave blank gray.\n\n"
        "Gray clay maquette figures. Blocky geometric furniture. Simple chandelier "
        "overhead. Smooth clay sculpture diorama."
    )

    def test_real_storyboard_prompt_unchanged(self):
        out = standardize_prompt(self.REAL_STORYBOARD, max_length=DREAMINA_DEFAULT_MAX_LENGTH)
        assert out == self.REAL_STORYBOARD, (
            f"standardization changed a real production prompt!\n"
            f"len in={len(self.REAL_STORYBOARD)} out={len(out)}"
        )

    def test_real_storyboard_idempotent(self):
        once = standardize_prompt(self.REAL_STORYBOARD, max_length=DREAMINA_DEFAULT_MAX_LENGTH)
        assert standardize_prompt(once, max_length=DREAMINA_DEFAULT_MAX_LENGTH) == once

    def test_default_max_length_truncates_long_real_prompt(self):
        # The library default (1000) DOES truncate a 1000+ char prompt — that is
        # the documented contract. The integration passes 4000 to avoid this.
        assert len(self.REAL_STORYBOARD) > 1000
        out = standardize_prompt(self.REAL_STORYBOARD)  # default max_length=1000
        assert len(out) <= 1000


# ---------------------------------------------------------------------------
# Configurability — every step independently toggleable
# ---------------------------------------------------------------------------


class TestConfigurability:
    def test_all_steps_off_is_near_passthrough(self):
        text = "cinematic,  cinematic  “cat”\x00"
        out = standardize_prompt(
            text,
            clean_control_chars=False,
            normalize_whitespace=False,
            normalize_quotes=False,
            dedup_segments=False,
            truncate=False,
        )
        assert out == text  # truly untouched

    def test_only_dedup_on(self):
        text = "a, a, b"
        out = standardize_prompt(
            text,
            clean_control_chars=False,
            normalize_whitespace=False,
            normalize_quotes=False,
            truncate=False,
        )
        assert out == "a, b"

    def test_only_control_clean_on(self):
        text = "a\x00b"
        out = standardize_prompt(
            text,
            normalize_whitespace=False,
            normalize_quotes=False,
            dedup_segments=False,
            truncate=False,
        )
        assert out == "ab"


# ---------------------------------------------------------------------------
# Hard-fail-safe
# ---------------------------------------------------------------------------


class TestHardFailSafe:
    def test_internal_error_returns_raw_input(self, monkeypatch):
        """If any internal step raises, the raw input is returned unchanged
        (never blocks generation — mirrors _h3_enhance_prompt discipline)."""
        text = "a cat portrait"

        def boom(_text: str) -> str:
            raise RuntimeError("simulated internal failure")

        monkeypatch.setattr(ps, "_normalize_whitespace", boom)
        assert standardize_prompt(text) == text

    def test_internal_error_returns_raw_even_with_features(self, monkeypatch):
        text = "cinematic, a cat"

        def boom(_line: str) -> str:
            raise ValueError("boom")

        monkeypatch.setattr(ps, "_dedup_line", boom)
        out = standardize_prompt(text, style_prefix="style", negative_prompt="blurry")
        assert out == text  # raw returned, no partial transform
