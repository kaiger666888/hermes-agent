"""Pydantic schema validation tests for formula_library (Plan 39-01, Task 1 RED).

Covers all FORM-02 fields + edge cases. Mirrors the test class grouping pattern
from ``tests/test_hermes_logging.py`` and the per-file structure of
``plugins/review_gates/tests/``.
"""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from plugins.formula_library.schema import (
    Citation,
    Formula,
    FormulaLibrary,
    PlatformFit,
)


def _valid_formula_kwargs() -> dict:
    """Return a dict that builds a valid Formula (override per-test)."""
    return {
        "formula_id": "urban-fantasy-light-01",
        "genre": "都市奇幻",
        "mood": "轻喜剧",
        "pacing": "fast-cut",
        "hook_pattern": "contrast",
        "characters": ["hidden-boss", "everyman-sidekick"],
        "runtime_sec": 90,
        "platform_fit": [
            PlatformFit(platform="抖音", fit_score=0.9),
            PlatformFit(platform="快手", fit_score=0.7),
        ],
        "citation": Citation(
            source="Notion 创作方向 page 32811082 §核心 DNA",
            source_type="notion",
            fair_use_status="verbatim-spec",
            verified_date=date(2026, 6, 26),
        ),
        "verified_date": date(2026, 6, 26),
        "eval_score": None,
    }


class TestFormulaValidation:
    def test_valid_formula(self) -> None:
        f = Formula.model_validate(_valid_formula_kwargs())
        assert f.formula_id == "urban-fantasy-light-01"
        assert f.genre == "都市奇幻"
        assert f.eval_score is None  # Optional, defaults to None

    def test_missing_citation_raises(self) -> None:
        kw = _valid_formula_kwargs()
        del kw["citation"]
        with pytest.raises(ValidationError) as exc_info:
            Formula.model_validate(kw)
        assert "citation" in str(exc_info.value)

    def test_invalid_genre_raises(self) -> None:
        kw = _valid_formula_kwargs()
        kw["genre"] = "玄幻修真"  # not in the 5-genre Literal
        with pytest.raises(ValidationError):
            Formula.model_validate(kw)

    def test_invalid_mood_raises(self) -> None:
        kw = _valid_formula_kwargs()
        kw["mood"] = "悲情"  # not in the 2-mood Literal
        with pytest.raises(ValidationError):
            Formula.model_validate(kw)

    def test_fit_score_out_of_range_raises(self) -> None:
        kw = _valid_formula_kwargs()
        kw["platform_fit"] = [PlatformFit(platform="抖音", fit_score=1.5)]
        # PlatformFit __init__ should raise (validator on fit_score)
        with pytest.raises(ValidationError):
            Formula.model_validate(kw)

    def test_fit_score_negative_raises(self) -> None:
        with pytest.raises(ValidationError):
            PlatformFit(platform="抖音", fit_score=-0.1)

    def test_eval_score_none_accepted(self) -> None:
        kw = _valid_formula_kwargs()
        kw["eval_score"] = None
        f = Formula.model_validate(kw)
        assert f.eval_score is None

    def test_eval_score_float_accepted(self) -> None:
        kw = _valid_formula_kwargs()
        kw["eval_score"] = 0.87
        f = Formula.model_validate(kw)
        assert f.eval_score == 0.87

    def test_eval_score_defaults_to_none(self) -> None:
        kw = _valid_formula_kwargs()
        del kw["eval_score"]
        f = Formula.model_validate(kw)
        assert f.eval_score is None

    def test_runtime_sec_below_60_raises(self) -> None:
        kw = _valid_formula_kwargs()
        kw["runtime_sec"] = 30
        with pytest.raises(ValidationError):
            Formula.model_validate(kw)

    def test_runtime_sec_above_600_raises(self) -> None:
        kw = _valid_formula_kwargs()
        kw["runtime_sec"] = 900
        with pytest.raises(ValidationError):
            Formula.model_validate(kw)

    def test_invalid_platform_in_platform_fit_raises(self) -> None:
        with pytest.raises(ValidationError):
            PlatformFit(platform="TikTok", fit_score=0.5)

    def test_invalid_hook_pattern_raises(self) -> None:
        kw = _valid_formula_kwargs()
        kw["hook_pattern"] = "random-pattern"
        with pytest.raises(ValidationError):
            Formula.model_validate(kw)


class TestCitationValidation:
    def test_valid_citation(self) -> None:
        c = Citation(
            source="Notion page 32811082",
            source_type="notion",
            fair_use_status="verbatim-spec",
            verified_date=date(2026, 6, 26),
        )
        assert c.source_type == "notion"

    def test_invalid_source_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            Citation(
                source="x",
                source_type="random-blog",  # not in Literal
                fair_use_status="verbatim-spec",
                verified_date=date(2026, 6, 26),
            )

    def test_invalid_fair_use_status_raises(self) -> None:
        with pytest.raises(ValidationError):
            Citation(
                source="x",
                source_type="notion",
                fair_use_status="copied-verbatim-copyrighted",  # not in Literal
                verified_date=date(2026, 6, 26),
            )


class TestFormulaLibrary:
    def test_by_id_lookup_hit(self) -> None:
        f = Formula.model_validate(_valid_formula_kwargs())
        lib = FormulaLibrary(formulas=[f])
        assert lib.by_id("urban-fantasy-light-01") is f
        assert lib.by_id("nonexistent") is None

    def test_filter_by_genre_mood(self) -> None:
        f1 = Formula.model_validate(_valid_formula_kwargs())
        kw2 = _valid_formula_kwargs()
        kw2.update({
            "formula_id": "mystery-twist-angst-01",
            "genre": "悬疑反转",
            "mood": "虐心",
            "hook_pattern": "suspense",
        })
        f2 = Formula.model_validate(kw2)
        lib = FormulaLibrary(formulas=[f1, f2])
        assert lib.filter(genre="都市奇幻", mood="轻喜剧") == [f1]
        assert lib.filter(genre="悬疑反转", mood="虐心") == [f2]
        assert lib.filter(genre="悬疑反转", mood="轻喜剧") == []

    def test_load_from_dir_skips_invalid(
        self, tmp_path, caplog
    ) -> None:
        """load_from_dir degrades gracefully — invalid JSON files are skipped."""
        import json

        valid = _valid_formula_kwargs()
        valid_path = tmp_path / "formula_valid_01.json"
        valid_path.write_text(
            json.dumps(valid, default=str, ensure_ascii=False),
            encoding="utf-8",
        )
        # Invalid JSON — missing required field "genre"
        invalid_path = tmp_path / "formula_invalid_01.json"
        invalid_path.write_text(
            json.dumps({"formula_id": "broken"}, ensure_ascii=False),
            encoding="utf-8",
        )

        lib = FormulaLibrary.load_from_dir(tmp_path)
        assert len(lib.formulas) == 1
        assert lib.formulas[0].formula_id == "urban-fantasy-light-01"

    def test_load_from_dir_missing_dir_returns_empty(self, tmp_path) -> None:
        """Missing dir → empty library (degrade gracefully)."""
        empty_dir = tmp_path / "does_not_exist"
        lib = FormulaLibrary.load_from_dir(empty_dir)
        assert lib.formulas == []
