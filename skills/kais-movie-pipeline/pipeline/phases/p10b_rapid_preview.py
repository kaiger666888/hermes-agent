"""p10b_rapid_preview.py — Phase 10b: rapid preview tier (V8.6 insertion).

STUB MODULE (Phase 40-01) — registry scaffolding only. The real implementation
arrives in plan 40-03. This module exists so ``phases/__init__.py`` can import
it and register it in PHASE_REGISTRY between ``p10_voice`` and
``p11_video_render``.

Per CONTEXT D-35-04 this module is PURE ORCHESTRATION — no LLM calls, no
prompt templates, no business logic. Unlike p10/p11 (which delegate to an
expert skill), p10b replaces expert delegation with a ``PreviewEngine``
strategy (LTX-Video real GPU or slideshow FFmpeg). Per CONTEXT.md "Engine
Selection & Default" decision: default engine when ``KAIS_PREVIEW_ENGINE``
unset is ``slideshow`` (safer fallback; honors degrade-first red line #1).

Behavioral contract (per CONTEXT.md "Variant Generation Strategy"):
  - For each shot, generate exactly 3 rapid preview variants (predictable
    test surface; matches blueprint "2-3 个" upper bound).
  - Each variant changes exactly ONE structure parameter from baseline
    (Notion 红线 #6 — control variable). ``structure_delta`` records which.
  - Across consecutive shots, cycle through all 4 structure params
    (hook_position_sec / emotion_sequence / turning_points_sec /
    ending_state) so each param gets A/B tested.
  - Generation fans out per-shot via ``ThreadPoolExecutor(max_workers=
    parallel_shots=4)`` — matches p11 pattern (D-36-08).

Inputs (asset bus READ):
  - ``voice-clips`` — output of p10 (TTS voice clips per shot)
  - ``voice-timeline`` — output of p10 (per-shot start/end + lip-sync cues)
  - ``e-konte-sheets`` — output of p09 (keyframes for slideshow engine)

Outputs (asset bus WRITE):
  - ``rapid-preview-clips`` — JSONL append-only, one line per variant
    (fields: shot_id / variant_id / structure_delta / clip_path /
    generation_time_ms / engine)
  - ``episode-meta`` — JSON, episode-level metadata flags (preview_skipped
    on full-degrade)

Gate triggered: None — p10b has no review gate (RAPID-PREVIEW-06 inherits
the 4 red-line gates via existing consistency-guard / asset-envelope
mechanisms, NOT via a new gate).

Degradation signaling (per CONTEXT.md "AssetBus Integration & Degradation"):
  When all preview engines are degraded, p10b writes
  ``episode-meta.preview_skipped = True`` AND ``logger.warning(...)``.
  Never silent.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Phase metadata — referenced by runner.py + tests
# ---------------------------------------------------------------------------

PHASE_ID = "p10b_rapid_preview"
EXPERT = None  # pure orchestration — p10b does NOT delegate to an expert
# skill (per CONTEXT D-35-04). The PreviewEngine strategy (LTX-Video real
# GPU / slideshow FFmpeg) replaces expert delegation. This is the
# documented deviation from p10/p11's pattern.
INPUT_SLOTS = ["voice-clips", "voice-timeline", "e-konte-sheets"]
OUTPUT_SLOTS = ["rapid-preview-clips", "episode-meta"]  # BOTH new slots
GATE_ID = None  # p10b has no review gate


# ---------------------------------------------------------------------------
# run() — the orchestration entry point (D-36-08 parallel_shots extension)
# ---------------------------------------------------------------------------


def run(
    episode_id: str,
    asset_bus_read: Callable[[str], Any],
    asset_bus_write: Callable[[str, dict], None],
    delegate_task: Callable[[str, str, list[str]], dict],
    trigger_gate: Callable[[str, str], dict] | None = None,
    *,
    parallel_shots: int = 4,  # D-36-08 — p10b fans out per-shot like p11
) -> dict:
    """Execute phase p10b (rapid preview tier).

    STUB — real implementation arrives in plan 40-03. Calling this raises
    ``NotImplementedError`` so the registry insertion (plan 01) and engine
    strategy (plan 02) can be built against the contract without coupling
    to the implementation.

    Args:
        episode_id: Episode identifier.
        asset_bus_read: Callable(slot) -> data (injected; tests pass mock).
        asset_bus_write: Callable(slot, entry) -> None (injected).
        delegate_task: Callable(goal, context, toolsets) -> dict. Ignored
            for p10b — EXPERT is None; PreviewEngine replaces delegation.
            Retained in the signature for Phase 35 contract compatibility.
        trigger_gate: Optional Callable(gate_id, episode_id) -> dict. Ignored
            for p10b — GATE_ID is None (CF-36-04 conditional skip).
        parallel_shots: Max worker count for ThreadPoolExecutor fan-out
            (D-36-08 — mirrors p11 contract).

    Raises:
        NotImplementedError: Always — real implementation arrives in
            plan 40-03.
    """
    raise NotImplementedError(
        "p10b_rapid_preview.run() implemented in plan 40-03"
    )
