"""Pytest coverage for the MT-Bench position-swap LLM-as-judge harness.

RED phase of TDD: these tests import the not-yet-implemented ``runner``
module and therefore fail at collection time until Task 2 lands the
implementation.

The harness implements MT-Bench-style position-swap evaluation:
  1. The judge sees two answers in BOTH orderings (A,B) and (B,A).
  2. If the two orderings disagree, the final verdict is "tie"
     (position-bias mitigation per EVAL-03 / CONTEXT.md decisions).
  3. Judge temperature is hard-pinned at 0.0 (EVAL-03).

The tests below use a ``MockJudgeClient`` that returns canned decisions
keyed on the swap flag — NO real OpenRouter / OpenAI API calls are made
in unit tests.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Module under test — must be importable as a top-level path.
_EVAL_DIR = Path(__file__).resolve().parent.parent
if str(_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_EVAL_DIR))

import runner  # noqa: E402  — intended; RED until runner.py exists


# --------------------------------------------------------------------------- #
# Mock judge client
# --------------------------------------------------------------------------- #


class MockJudgeClient:
    """Duck-typed stand-in for an OpenAI client.

    ``decisions`` is a mapping from ``swap`` (bool) -> decision string
    ("A" / "B" / "tie"). The mock records the swap flag seen in the
    last call so tests can introspect ordering.

    If ``decisions`` is missing a key, returns "tie" (safe default).
    """

    def __init__(self, decisions: dict[bool, str] | None = None) -> None:
        self.decisions = decisions or {}
        self.last_swap: bool | None = None
        self.calls: list[dict] = []

    def chat_completions_create(self, **kwargs: object) -> dict:
        swap = bool(kwargs.get("extra_body", {}).get("swap", False))
        self.last_swap = swap
        self.calls.append(kwargs)
        decision = self.decisions.get(swap, "tie")
        return {
            "choices": [
                {"message": {"content": f"<decision>{decision}</decision>"}}
            ]
        }


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #


class TestParseJudgeDecision:
    def test_extracts_tag_A(self) -> None:
        assert runner.parse_judge_decision("...reasoning... <decision>A</decision>") == "A"

    def test_extracts_tag_B(self) -> None:
        assert runner.parse_judge_decision("blah <decision>B</decision> end") == "B"

    def test_extracts_tag_tie(self) -> None:
        assert runner.parse_judge_decision("<decision>tie</decision>") == "tie"

    def test_case_insensitive_tag_value(self) -> None:
        assert runner.parse_judge_decision("<decision>a</decision>") == "A"
        assert runner.parse_judge_decision("<decision>TIE</decision>") == "tie"

    def test_no_tag_defaults_to_tie(self) -> None:
        # T-00-11 mitigation: malformed judge output fails safe.
        assert runner.parse_judge_decision("the judge rambled with no tag") == "tie"


class TestPositionSwap:
    def test_runs_both_orderings_and_disagreement_resolves_to_tie(self) -> None:
        # Judge says "A" when A is first (swap=False), "B" when B is first (swap=True).
        # This is classic position bias — disagreement -> tie.
        judge = MockJudgeClient(decisions={False: "A", True: "B"})
        verdict = runner.run_position_swap(
            prompt="design a camera move",
            answer_a="answer A text",
            answer_b="answer B text",
            judge_client=judge,
            judge_model="qwen/qwen3-235b-a22b:free",
            prompt_id="p-001",
        )
        assert verdict["ordering_ab"] == "A"
        assert verdict["ordering_ba"] == "B"
        assert verdict["final"] == "tie"

    def test_consistent_verdicts_yield_winner(self) -> None:
        # Judge says "A" in both orderings — A wins decisively.
        judge = MockJudgeClient(decisions={False: "A", True: "A"})
        verdict = runner.run_position_swap(
            prompt="design a camera move",
            answer_a="better answer",
            answer_b="weaker answer",
            judge_client=judge,
            judge_model="qwen/qwen3-235b-a22b:free",
            prompt_id="p-002",
        )
        assert verdict["final"] == "A_wins"

    def test_b_consistent_wins(self) -> None:
        judge = MockJudgeClient(decisions={False: "B", True: "B"})
        verdict = runner.run_position_swap(
            prompt="x",
            answer_a="a",
            answer_b="b",
            judge_client=judge,
            judge_model="m",
            prompt_id="p-003",
        )
        assert verdict["final"] == "B_wins"


class TestRunAblation:
    def test_pairwise_over_3_conditions(self) -> None:
        # EVAL-04: runner must accept N>=2 conditions with pairwise comparison.
        # 3 conditions => C(3,2) = 3 pairs. 2 prompts => 3 * 2 = 6 verdicts.
        # Each verdict internally runs 2 orderings => 12 judge calls total.
        conditions = {
            "old": ["old-ans-p1", "old-ans-p2"],
            "new_no_refs": ["new-nr-p1", "new-nr-p2"],
            "new_with_refs": ["new-wr-p1", "new-wr-p2"],
        }
        prompts = [
            {"id": "p1", "text": "prompt 1"},
            {"id": "p2", "text": "prompt 2"},
        ]
        judge = MockJudgeClient(decisions={False: "A", True: "A"})
        verdicts = runner.run_ablation(
            conditions=conditions,
            prompts=prompts,
            judge_client=judge,
            judge_model="qwen/qwen3-235b-a22b:free",
        )
        # 3 pairs * 2 prompts = 6 verdicts
        assert len(verdicts) == 6
        # Each verdict has the required fields
        for v in verdicts:
            assert {"prompt_id", "pair", "ordering_ab", "ordering_ba", "final"} <= set(v.keys())
        # All pairs covered
        pairs = {tuple(v["pair"]) for v in verdicts}
        assert pairs == {
            ("new_no_refs", "new_with_refs"),
            ("new_no_refs", "old"),
            ("new_with_refs", "old"),
        }


class TestFormatResults:
    def test_returns_json_and_markdown(self) -> None:
        # After a mock run, format_results returns a JSON-serializable dict
        # and a Markdown table with columns: prompt_id, pair, winner, judge.
        verdicts = [
            {
                "prompt_id": "p1",
                "pair": ["baseline", "candidate"],
                "ordering_ab": "A",
                "ordering_ba": "A",
                "final": "A_wins",
                "judge": "qwen",
            }
        ]
        json_out, md_out = runner.format_results(verdicts, judge_label="qwen")
        assert json_out["total_comparisons"] == 1
        assert json_out["verdicts"] == verdicts
        # Markdown table has the required header row
        assert "| prompt_id |" in md_out
        assert "| pair |" in md_out
        assert "| winner |" in md_out
        assert "| judge |" in md_out

    def test_format_results_escapes_pipes(self) -> None:
        # WR-09: any ``|`` in an interpolated value must be escaped to
        # ``\\|`` so the Markdown table column count is preserved. Real
        # risk: OpenRouter model slugs like ``qwen/qwen3-235b:free|preview``
        # or a condition label containing a pipe.
        verdicts = [
            {
                "prompt_id": "p|1",  # pipe in prompt_id
                "pair": ["base|line", "candidate"],  # pipe in pair label
                "ordering_ab": "A",
                "ordering_ba": "A",
                "final": "A_wins",
                "judge": "qwen|preview",  # pipe in judge slug
            }
        ]
        _, md_out = runner.format_results(verdicts)
        # Header has exactly 4 columns; each data row must also have
        # exactly 4 cells. Count unescaped pipes in the data row —
        # there should be exactly 5 (the 4 column delimiters plus the
        # trailing one), NOT more.
        data_row = md_out.strip().splitlines()[-1]
        # Unescaped pipe count: split on ``|`` but exclude ``\|``.
        # Easier assertion: the row, after removing escaped ``\|``,
        # should contain exactly 5 ``|`` characters (leading, 3 inner,
        # trailing).
        cleaned = data_row.replace("\\|", "")
        assert cleaned.count("|") == 5, (
            f"column count drift after escaping; cleaned row: {cleaned!r}"
        )
        # And the escaped forms are actually present.
        assert "\\|" in data_row


class TestJudgeTemperature:
    def test_build_judge_messages_marks_swap_flag(self) -> None:
        # build_judge_messages must emit OpenAI chat format and tag swap.
        msgs = runner.build_judge_messages(
            prompt="x", answer_a="a", answer_b="b", swap=False
        )
        assert isinstance(msgs, list)
        assert all(isinstance(m, dict) and "role" in m and "content" in m for m in msgs)

    def test_build_judge_kwargs_pins_temperature_zero(self) -> None:
        # EVAL-03 hard-pin: judge temperature MUST be 0.0 in every code path.
        kwargs = runner.build_judge_kwargs(
            messages=[{"role": "user", "content": "x"}],
            model="qwen/qwen3-235b-a22b:free",
        )
        assert kwargs["temperature"] == 0.0
        # No other temperature key anywhere
        assert "temperature" in kwargs


class TestStubJudgeClient:
    def test_stub_returns_position_bias_pattern(self) -> None:
        # The stub's whole purpose is to demonstrate the classic
        # position-bias pattern: A wins in AB ordering, B wins in BA
        # ordering, collapsing to a "tie" final verdict.
        stub = runner._StubJudgeClient()
        resp_a = stub.chat.completions.create(
            model="m",
            temperature=0.0,
            messages=[],
            extra_body={"swap": False},
        )
        assert "<decision>A</decision>" in resp_a["choices"][0]["message"]["content"]
        resp_b = stub.chat.completions.create(
            model="m",
            temperature=0.0,
            messages=[],
            extra_body={"swap": True},
        )
        assert "<decision>B</decision>" in resp_b["choices"][0]["message"]["content"]

    def test_stub_judge_client_instances_independent(self) -> None:
        # WR-02: two _StubJudgeClient instances must not share call
        # state. Each instance's ``chat`` / ``chat.completions`` are
        # independent objects so a future refactor that adds instance
        # state (e.g. a call counter) does not silently leak across
        # instances.
        a = runner._StubJudgeClient()
        b = runner._StubJudgeClient()
        assert a.chat is not b.chat
        assert a.chat.completions is not b.chat.completions


class TestMainFailFast:
    """WR-03 + WR-04: main() fails loud rather than silently degrading."""

    def _write_minimal_config(self, tmp_path: Path) -> Path:
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "judge:\n"
            "  models:\n"
            "    - qwen/qwen3-235b-a22b:free\n"
            "conditions:\n"
            "  - baseline\n"
            "  - candidate\n",
            encoding="utf-8",
        )
        return config_path

    def test_main_rejects_live_mode_without_dry_run(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # WR-03: main() invoked without --dry-run must exit 2 with an
        # error, NOT silently fall through to stub answers and write a
        # report that looks like a real eval run.
        config_path = self._write_minimal_config(tmp_path)
        # Need a prompts file for the expert resolution step.
        prompts_dir = Path(runner.__file__).resolve().parent / "prompts"
        # animator_demo.yaml ships with the repo — guaranteed to exist.
        rc = runner.main(
            [
                "--config",
                str(config_path),
                "--expert",
                "animator",
                # NO --dry-run
            ]
        )
        assert rc == 2, (
            f"main() without --dry-run must return 2 (WR-03), got {rc}"
        )

    def test_make_judge_client_raises_on_missing_api_key(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # WR-04: when OPENROUTER_API_KEY is unset/empty, make_judge_client
        # must raise RuntimeError (fail-fast), NOT silently construct an
        # OpenAI client with api_key="".
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
            runner.make_judge_client({})
