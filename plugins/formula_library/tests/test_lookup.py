"""Lookup engine tests for formula_library (Plan 39-01, Task 2 RED).

Tests cover ranking, filtering, top_k, and handler dispatch. Uses synthetic
in-memory libraries (does NOT depend on Plan 02 seed data).
"""

from __future__ import annotations

from datetime import date

import plugins.formula_library.lookup as L
from plugins.formula_library.lookup import load_library, lookup_formulas
from plugins.formula_library.schema import (
    Citation,
    Formula,
    FormulaLibrary,
    PlatformFit,
)
from plugins.formula_library.tools import _handle_formula_lookup
from tools.registry import tool_error, tool_result


def _make_formula(
    formula_id: str,
    genre: str,
    mood: str,
    douyin_score: float = 0.5,
    hook_pattern: str = "contrast",
) -> Formula:
    return Formula(
        formula_id=formula_id,
        genre=genre,
        mood=mood,
        pacing="fast-cut",
        hook_pattern=hook_pattern,
        characters=["hero"],
        runtime_sec=90,
        platform_fit=[PlatformFit(platform="抖音", fit_score=douyin_score)],
        citation=Citation(
            source="Notion test",
            source_type="notion",
            fair_use_status="verbatim-spec",
            verified_date=date(2026, 6, 26),
        ),
        verified_date=date(2026, 6, 26),
        eval_score=None,
    )


class TestLookupRanking:
    def setup_method(self) -> None:
        # Reset cache before each test so the in-memory library is fresh.
        L._LIBRARY_CACHE = None

    def teardown_method(self) -> None:
        L._LIBRARY_CACHE = None

    def test_lookup_returns_ranked_by_platform_fit(self) -> None:
        f_hi = _make_formula("t-hi", "都市奇幻", "轻喜剧", douyin_score=0.9)
        f_mid = _make_formula("t-mid", "都市奇幻", "轻喜剧", douyin_score=0.7)
        f_lo = _make_formula("t-lo", "都市奇幻", "轻喜剧", douyin_score=0.5)
        L._LIBRARY_CACHE = FormulaLibrary(formulas=[f_lo, f_hi, f_mid])
        res = lookup_formulas(
            genre="都市奇幻", mood="轻喜剧", platform="抖音", top_k=3
        )
        assert [f.formula_id for f in res] == ["t-hi", "t-mid", "t-lo"]

    def test_lookup_filters_strict_on_genre_mood(self) -> None:
        f_match = _make_formula("t-match", "悬疑反转", "虐心", douyin_score=0.9, hook_pattern="suspense")
        f_other_genre = _make_formula("t-other-g", "都市奇幻", "虐心", douyin_score=0.99)
        f_other_mood = _make_formula("t-other-m", "悬疑反转", "轻喜剧", douyin_score=0.99, hook_pattern="suspense")
        L._LIBRARY_CACHE = FormulaLibrary(formulas=[f_match, f_other_genre, f_other_mood])
        res = lookup_formulas(genre="悬疑反转", mood="虐心", platform="B站", top_k=3)
        # No B站 platform_fit entry in any → all 0.0 fit; but filter still
        # passes only f_match. Ranking among 0.0 ties broken by formula_id.
        assert [f.formula_id for f in res] == ["t-match"]

    def test_lookup_empty_when_no_match(self) -> None:
        L._LIBRARY_CACHE = FormulaLibrary(formulas=[
            _make_formula("t", "都市奇幻", "轻喜剧")
        ])
        res = lookup_formulas(genre="悬疑反转", mood="虐心", platform="抖音")
        assert res == []

    def test_lookup_empty_library(self) -> None:
        L._LIBRARY_CACHE = FormulaLibrary(formulas=[])
        res = lookup_formulas(genre="都市奇幻", mood="轻喜剧", platform="抖音")
        assert res == []

    def test_lookup_respects_top_k(self) -> None:
        formulas = [
            _make_formula(f"t-{i}", "都市奇幻", "轻喜剧", douyin_score=1.0 - i * 0.1)
            for i in range(5)
        ]
        L._LIBRARY_CACHE = FormulaLibrary(formulas=formulas)
        res = lookup_formulas(
            genre="都市奇幻", mood="轻喜剧", platform="抖音", top_k=2
        )
        assert len(res) == 2
        assert [f.formula_id for f in res] == ["t-0", "t-1"]

    def test_lookup_default_top_k_is_3(self) -> None:
        formulas = [
            _make_formula(f"t-{i}", "都市奇幻", "轻喜剧", douyin_score=1.0 - i * 0.1)
            for i in range(5)
        ]
        L._LIBRARY_CACHE = FormulaLibrary(formulas=formulas)
        res = lookup_formulas(genre="都市奇幻", mood="轻喜剧", platform="抖音")
        assert len(res) == 3

    def test_lookup_ties_broken_by_formula_id_ascending(self) -> None:
        # Two formulas with identical platform_fit score — tie broken by id asc.
        f_b = _make_formula("t-bbb", "都市奇幻", "轻喜剧", douyin_score=0.8)
        f_a = _make_formula("t-aaa", "都市奇幻", "轻喜剧", douyin_score=0.8)
        L._LIBRARY_CACHE = FormulaLibrary(formulas=[f_b, f_a])
        res = lookup_formulas(genre="都市奇幻", mood="轻喜剧", platform="抖音")
        assert [f.formula_id for f in res] == ["t-aaa", "t-bbb"]

    def test_lookup_missing_platform_entry_treated_as_zero(self) -> None:
        # Formula has no 抖音 entry — fit_score for 抖音 lookup is 0.0.
        f_no_douyin = Formula(
            formula_id="t-no-d",
            genre="都市奇幻",
            mood="轻喜剧",
            pacing="slow",
            hook_pattern="emotional",
            characters=["x"],
            runtime_sec=90,
            platform_fit=[PlatformFit(platform="B站", fit_score=0.95)],
            citation=Citation(
                source="x", source_type="notion",
                fair_use_status="verbatim-spec",
                verified_date=date(2026, 6, 26),
            ),
            verified_date=date(2026, 6, 26),
        )
        f_with_douyin = _make_formula("t-with-d", "都市奇幻", "轻喜剧", douyin_score=0.1)
        L._LIBRARY_CACHE = FormulaLibrary(formulas=[f_no_douyin, f_with_douyin])
        res = lookup_formulas(genre="都市奇幻", mood="轻喜剧", platform="抖音")
        # f-with-d has 0.1; f-no-d has 0.0 (no 抖音 entry). 0.1 > 0.0.
        assert [f.formula_id for f in res] == ["t-with-d", "t-no-d"]


class TestLoadLibrary:
    def setup_method(self) -> None:
        L._LIBRARY_CACHE = None

    def teardown_method(self) -> None:
        L._LIBRARY_CACHE = None

    def test_load_library_explicit_dir(self, tmp_path) -> None:
        """load_library with explicit dir bypasses cache."""
        import json

        kw = {
            "formula_id": "test-01",
            "genre": "都市奇幻",
            "mood": "轻喜剧",
            "pacing": "fast-cut",
            "hook_pattern": "contrast",
            "characters": ["x"],
            "runtime_sec": 60,
            "platform_fit": [{"platform": "抖音", "fit_score": 0.5}],
            "citation": {
                "source": "x",
                "source_type": "notion",
                "fair_use_status": "verbatim-spec",
                "verified_date": "2026-06-26",
            },
            "verified_date": "2026-06-26",
            "eval_score": None,
        }
        (tmp_path / "formula_test_01.json").write_text(
            json.dumps(kw, ensure_ascii=False), encoding="utf-8"
        )
        lib = load_library(tmp_path)
        assert len(lib.formulas) == 1
        assert lib.formulas[0].formula_id == "test-01"

    def test_load_library_missing_default_dir_returns_empty(self, tmp_path, monkeypatch) -> None:
        """Default library/ dir missing → empty FormulaLibrary (graceful)."""
        # Point load_library at a non-existent path via monkeypatching
        # __file__-derived default is hard; instead call with explicit nonexistent.
        empty = tmp_path / "no_such_dir"
        lib = load_library(empty)
        assert lib.formulas == []


class TestHandlerDispatch:
    def setup_method(self) -> None:
        L._LIBRARY_CACHE = None

    def teardown_method(self) -> None:
        L._LIBRARY_CACHE = None

    def test_handler_returns_tool_result_envelope(self) -> None:
        f = _make_formula("t-1", "都市奇幻", "轻喜剧", douyin_score=0.9)
        L._LIBRARY_CACHE = FormulaLibrary(formulas=[f])
        raw = _handle_formula_lookup({
            "genre": "都市奇幻",
            "mood": "轻喜剧",
            "platform": "抖音",
        })
        # tool_result returns a JSON string
        import json
        envelope = json.loads(raw)
        assert "error" not in envelope
        assert "formulas" in envelope
        assert len(envelope["formulas"]) == 1
        assert envelope["formulas"][0]["formula_id"] == "t-1"
        assert envelope["count"] == 1

    def test_handler_missing_required_arg_returns_tool_error(self) -> None:
        raw = _handle_formula_lookup({"mood": "轻喜剧", "platform": "抖音"})  # missing genre
        import json
        envelope = json.loads(raw)
        assert "error" in envelope
        assert "genre" in envelope["error"]

    def test_handler_top_k_override(self) -> None:
        formulas = [
            _make_formula(f"t-{i}", "都市奇幻", "轻喜剧", douyin_score=0.9 - i * 0.1)
            for i in range(5)
        ]
        L._LIBRARY_CACHE = FormulaLibrary(formulas=formulas)
        raw = _handle_formula_lookup({
            "genre": "都市奇幻",
            "mood": "轻喜剧",
            "platform": "抖音",
            "top_k": 2,
        })
        import json
        envelope = json.loads(raw)
        assert envelope["count"] == 2

    def test_handler_empty_result_returns_empty_list(self) -> None:
        L._LIBRARY_CACHE = FormulaLibrary(formulas=[])
        raw = _handle_formula_lookup({
            "genre": "都市奇幻",
            "mood": "轻喜剧",
            "platform": "抖音",
        })
        import json
        envelope = json.loads(raw)
        assert "error" not in envelope
        assert envelope["formulas"] == []
        assert envelope["count"] == 0
