"""Shared fixtures for EVAL-03 bias canary tests."""
from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Directory of bias canary fixture JSON files."""
    return FIXTURES_DIR


@pytest.fixture()
def deterministic_embed():
    """Deterministic bag-of-words embed_fn for unit tests (no LLM, no network).

    Mirrors the default ``_default_embed`` in ``agent.curator_bias_canary`` —
    kept in sync so tests exercise the same fallback shape.
    """
    import re
    from collections import Counter

    def _embed(text: str) -> list[float]:
        # Hashed bag-of-words: deterministic + zero external deps.
        tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
        if not tokens:
            return [0.0] * 16
        counts: Counter[str] = Counter(tokens)
        vec = [0.0] * 16
        for tok, c in counts.items():
            # Hash into 16 buckets; Python's hash is salted per-run so use a
            # stable polynomial rolling hash instead.
            h = 0
            for ch in tok:
                h = (h * 31 + ord(ch)) & 0xFFFF
            vec[h % 16] += float(c)
        # L2-normalize for cosine.
        norm = sum(v * v for v in vec) ** 0.5
        if norm == 0.0:
            return vec
        return [v / norm for v in vec]

    return _embed
