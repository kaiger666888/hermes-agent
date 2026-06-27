"""p10b_rapid_preview.py — Phase 10b: rapid preview tier (V8.6 insertion).

Per CONTEXT D-35-04 this module is PURE ORCHESTRATION — no LLM calls, no
prompt templates, no business logic. Unlike p10/p11 (which delegate to an
expert skill), p10b replaces expert delegation with a ``PreviewEngine``
strategy (LTX-Video real GPU or slideshow FFmpeg) composed from
``plugins.kais_aigc.preview_engine.select_engine``.

Behavioral contract (per CONTEXT.md "Variant Generation Strategy" +
"Variant Matrix"):
  - For each shot, generate exactly 3 rapid preview variants.
  - Each variant changes exactly ONE structure parameter from baseline
    (Notion 红线 #6 — control variable). ``structure_delta`` records which.
  - BLOCKER #4 fix — CYCLING MATRIX: across consecutive shots, the 3
    variant params are selected by ``[STRUCTURE_PARAMS[N mod 4],
    STRUCTURE_PARAMS[(N+1) mod 4], STRUCTURE_PARAMS[(N+2) mod 4]]`` from
    the 4-param list ``(hook_position_sec, emotion_sequence,
    turning_points_sec, ending_state)``. This ensures all 4 params are
    deterministically covered across a multi-shot episode (verified by an
    explicit test).
  - Generation fans out per-shot via ``ThreadPoolExecutor(max_workers=
    parallel_shots=4)`` — matches p11 pattern (D-36-08).

Inputs (asset bus READ):
  - ``voice-clips`` — output of p10 (TTS voice clips per shot; iterated
    as the shot list)
  - ``voice-timeline`` — output of p10 (per-shot start/end + lip-sync cues)
  - ``e-konte-sheets`` — output of p09 (keyframes for slideshow engine)

Outputs (asset bus WRITE):
  - ``rapid-preview-clips`` — JSONL append-only, one line per SUCCESSFUL
    variant (degraded variants are NOT appended — they are counted in
    outputs.variants_degraded). Fields: shot_id / variant_id /
    structure_delta / clip_path / generation_time_ms / engine.
  - ``episode-meta`` — JSON, episode-level metadata flags. The
    ``preview_skipped: True`` flag is written here on episode-level
    full-degrade (BLOCKER #1 fix — NOT ``pipeline-state`` which is a
    separate PipelineStateStore file).

Gate triggered: None — p10b has no review gate (RAPID-PREVIEW-06 inherits
the 4 red-line gates via existing consistency-guard / asset-envelope
mechanisms, NOT via a new gate).

Degrade semantics (RAPID-PREVIEW-05):
  - Per-variant degrade is silent (counted in outputs.variants_degraded).
  - Episode-level full-degrade (all variants of all shots degraded)
    triggers WARN log + ``preview_skipped=True`` flag written to the
    ``episode-meta`` AssetBus slot (BLOCKER #1 fix — NOT pipeline-state,
    which is a separate PipelineStateStore file). This is the inherited
    v4.0 'no silent swallow' semantics — episode-level fail is visible;
    per-variant fail is recoverable.
"""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from plugins.kais_aigc.preview_engine import PreviewEngine, select_engine

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
# Variant generation constants (per CONTEXT "Variant Matrix" decision)
# ---------------------------------------------------------------------------

#: The 4 valid structure params varied across variants. Each variant's
#: structure_delta changes EXACTLY ONE of these (Notion 红线 #6).
STRUCTURE_PARAMS = (
    "hook_position_sec",
    "emotion_sequence",
    "turning_points_sec",
    "ending_state",
)

#: Variants per shot (CONTEXT "Variant count: exactly 3" decision).
VARIANTS_PER_SHOT = 3

#: Cycle of ending_state values used by _derive_new_value.
_ENDING_STATE_CYCLE = ("new_suspense", "cliffhanger", "twist")


# ---------------------------------------------------------------------------
# Helpers — variant construction (BLOCKER #4 cycling matrix + 红线 #6 single-delta)
# ---------------------------------------------------------------------------


def _derive_new_value(param_name: str, baseline_value: Any) -> Any:
    """Derive a deterministic new value for ``param_name``.

    Operator-tunable. Defaults are deterministic for testability — tests can
    assert against the exact transformations below. The key constraints are
    documented in CONTEXT.md "Variant Matrix"; the actual new_value
    derivation is mechanical (no creative decision — that happened upstream
    in p01-p09).
    """
    if param_name == "hook_position_sec":
        # Numeric shift by +2 sec.
        return baseline_value + 2
    if param_name == "emotion_sequence":
        # Rotate list by 1 — last element moves to front.
        if not isinstance(baseline_value, list) or not baseline_value:
            return baseline_value
        return baseline_value[-1:] + baseline_value[:-1]
    if param_name == "turning_points_sec":
        # Shift each timestamp by +2 sec. p10b doesn't know episode duration,
        # so no capping (operator-side concern per blueprint Out of Scope).
        if not isinstance(baseline_value, list):
            return baseline_value
        return [t + 2 for t in baseline_value]
    if param_name == "ending_state":
        # Cycle to next from the canonical tuple.
        if baseline_value in _ENDING_STATE_CYCLE:
            idx = _ENDING_STATE_CYCLE.index(baseline_value)
            return _ENDING_STATE_CYCLE[(idx + 1) % len(_ENDING_STATE_CYCLE)]
        # Unknown baseline → fall back to first canonical value.
        return _ENDING_STATE_CYCLE[0]
    # Should never reach here — _validate_structure_delta rejects unknown
    # params before this helper is called. Defensive raise.
    raise ValueError(f"invalid structure_delta param: {param_name!r}; valid: {STRUCTURE_PARAMS}")


def _validate_structure_delta(delta: dict) -> None:
    """Validate that ``delta`` is a single-key dict whose key is a valid param.

    Notion 红线 #6 enforcement — control variable rule. Each variant changes
    EXACTLY ONE structure parameter from baseline. Multi-key deltas are
    rejected at construction time (BEFORE the engine call) to prevent
    smuggled multi-param changes that would confound A/B 赛马 downstream.
    """
    if not isinstance(delta, dict):
        raise ValueError(
            f"single-delta violation (Notion 红线 #6): structure_delta must be a dict, "
            f"got {type(delta).__name__}"
        )
    if len(delta) != 1:
        raise ValueError(
            f"single-delta violation (Notion 红线 #6): structure_delta must have exactly "
            f"one key, got {len(delta)}: {list(delta.keys())}"
        )
    key = next(iter(delta.keys()))
    if key not in STRUCTURE_PARAMS:
        raise ValueError(
            f"invalid structure_delta param: {key!r}; valid: {STRUCTURE_PARAMS}"
        )


def _build_variants(
    shot_id: str,
    shot_index: int,
    baseline_structure: dict,
) -> list[dict]:
    """Build the VARIANTS_PER_SHOT variants for one shot.

    BLOCKER #4 fix — CYCLING MATRIX:
        For ``shot_index`` N (0-based), select params at indices
        ``[(N + offset) % len(STRUCTURE_PARAMS) for offset in range(VARIANTS_PER_SHOT)]``.
        Yields ``[N % 4, (N+1) % 4, (N+2) % 4]`` for VARIANTS_PER_SHOT=3
        and len(STRUCTURE_PARAMS)=4.

        Concrete cycling:
          shot 0: [hook_position_sec, emotion_sequence, turning_points_sec]
          shot 1: [emotion_sequence, turning_points_sec, ending_state]
          shot 2: [turning_points_sec, ending_state, hook_position_sec]
          shot 3: [ending_state, hook_position_sec, emotion_sequence]
          shot 4: same as shot 0 (cycles)

        Across shots 0..3 ALL 4 params are covered (each appears in exactly
        3 of the 4 shots).

    Each returned variant is ``{"variant_id": str, "structure_delta": dict}``
    where ``structure_delta`` is a single-key dict (validated).
    """
    indices = [
        (shot_index + offset) % len(STRUCTURE_PARAMS)
        for offset in range(VARIANTS_PER_SHOT)
    ]
    variants: list[dict] = []
    for position, idx in enumerate(indices):
        param_name = STRUCTURE_PARAMS[idx]
        baseline_value = baseline_structure.get(param_name)
        new_value = _derive_new_value(param_name, baseline_value)
        structure_delta = {param_name: new_value}
        # Validate at construction time (Notion 红线 #6 enforcement).
        _validate_structure_delta(structure_delta)
        variant_id = f"{shot_id}__v{position + 1}_{param_name}"
        variants.append({
            "variant_id": variant_id,
            "structure_delta": structure_delta,
        })
    return variants


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

    Args:
        episode_id: Episode identifier.
        asset_bus_read: Callable(slot) -> data (injected; tests pass mock).
        asset_bus_write: Callable(slot, entry) -> None (injected). For the
            JSONL slot ``rapid-preview-clips`` the runner-injected callable
            dispatches to ``AssetBus.append_line``; for the JSON slot
            ``episode-meta`` it dispatches to ``AssetBus.write``.
        delegate_task: Callable(goal, context, toolsets) -> dict. ACCEPTED
            for signature compatibility with the runner's uniform phase
            dispatch (D-35-02) but NOT CALLED — p10b is pure orchestration
            over PreviewEngine, no expert delegation (CONTEXT D-35-04).
        trigger_gate: Optional Callable(gate_id, episode_id) -> dict. Ignored
            for p10b — GATE_ID is None (CF-36-04 conditional skip).
        parallel_shots: Max worker count for ThreadPoolExecutor fan-out
            (D-36-08 — mirrors p11 contract). Defaults to 4.

    Returns:
        ``{"phase": "p10b_rapid_preview", "outputs": {...}, "gate": None}``
        where ``outputs`` carries ``variants_generated`` (success count) and
        ``variants_degraded`` (degrade envelope count). On episode-level
        full-degrade, ``preview_skipped`` is set in the ``episode-meta``
        AssetBus slot (BLOCKER #1 — NOT pipeline-state).

    Raises:
        Nothing on engine degrade or engine constructor failure — both paths
        emit WARN + write the ``preview_skipped`` flag and return cleanly.
        Only truly unexpected errors propagate (runner retry loop handles
        them via the existing max_retries contract — RAPID-PREVIEW-06).
    """
    # Wrap the entire body in a try/except so engine constructor failures
    # (defensive — plan 02's select_engine should not raise) and other
    # unexpected exceptions are caught at the phase boundary. On catch:
    # emit WARN + write preview_skipped flag + return degrade envelope.
    try:
        return _run_body(
            episode_id, asset_bus_read, asset_bus_write,
            delegate_task, trigger_gate, parallel_shots,
        )
    except Exception as exc:
        # Defensive: plan 02's select_engine should not raise in practice,
        # but p10b must be robust. Episode-level fail is visible (WARN +
        # episode-meta flag); the runner's existing retry loop handles
        # truly unexpected errors via max_retries (RAPID-PREVIEW-06).
        logger.warning(
            "preview_skipped: episode=%s error=%s: %s — falling back to p11 direct Seedance",
            episode_id, type(exc).__name__, exc,
        )
        asset_bus_write("episode-meta", {
            "episode_id": episode_id,
            "preview_skipped": True,
            "skip_reason": f"{type(exc).__name__}: {exc}",
        })
        return {
            "phase": PHASE_ID,
            "outputs": {
                "variants_generated": 0,
                "variants_degraded": 0,
                "error": str(exc),
            },
            "gate": None,
        }


def _run_body(
    episode_id: str,
    asset_bus_read: Callable[[str], Any],
    asset_bus_write: Callable[[str, dict], None],
    delegate_task: Callable[[str, str, list[str]], dict],
    trigger_gate: Callable[[str, str], dict] | None,
    parallel_shots: int,
) -> dict:
    """Body of run(), extracted so the top-level try/except can wrap it cleanly.

    Implements the per-shot fan-out + episode-level degrade WARN semantics.
    See ``run()`` docstring for the full behavioral contract.
    """
    # 1. Gather inputs (graceful when slot empty — first run / tests).
    voice_clips = asset_bus_read("voice-clips") or []
    voice_timeline = asset_bus_read("voice-timeline") or {}
    e_konte = asset_bus_read("e-konte-sheets") or {}

    # Derive shot_list from voice_clips (each clip has shot_id; p10b iterates).
    shot_list = voice_clips if isinstance(voice_clips, list) else []

    # 2. Engine selection (env-var-driven; defaults to slideshow per plan 02).
    # Phase 40 CR-02 fix: enter the engine's context manager so resources
    # are released when the fan-out completes (or raises). ``PreviewEngine``
    # declares no-op ``__enter__`` / ``__exit__`` / ``close`` on the ABC;
    # ``LTXVideoEngine`` overrides them to close its ``httpx.Client``
    # connection pool. Without ``with``, long-running daemons (gateway /
    # cron) leaked one ``httpx.Client`` per episode until FD exhaustion.
    # ``SlideshowEngine`` inherits the no-op defaults (no resources).
    with select_engine() as engine:

        # 3. Per-shot fan-out via ThreadPoolExecutor (D-36-08 pattern from p11).
        total_variants = len(shot_list) * VARIANTS_PER_SHOT
        degraded_count = 0
        generated_count = 0

        def _generate_variant(
            shot: dict,
            shot_index: int,
            variant: dict,
        ) -> dict:
            """Call engine.generate() for one variant; return the engine envelope."""
            shot_id = shot.get("shot_id", f"shot_{shot_index:03d}")
            # Derive engine.generate() inputs from the shot + asset-bus data.
            prompt = shot.get("intent", f"shot {shot_index}")
            keyframe_image_path = _resolve_keyframe(e_konte, shot_id)
            voice_clip_path = shot.get("clip_path")
            output_path = f"/preview/{episode_id}/{variant['variant_id']}.mp4"
            return engine.generate(
                shot_id=shot_id,
                prompt=prompt,
                structure_delta=variant["structure_delta"],
                keyframe_image_path=keyframe_image_path,
                voice_clip_path=voice_clip_path,
                output_path=output_path,
            )

        # Fan out across shots (each shot submits its 3 variants sequentially
        # within the per-shot thread; shots fan out across threads). This mirrors
        # the p11 dispatch pattern — one pool.submit per shot.
        #
        # Pair each future with its (shot, variant) context so success records
        # can carry all 6 required fields (3 from the engine envelope: clip_path
        # / generation_time_ms / engine; 3 from the per-variant inputs: shot_id
        # / variant_id / structure_delta).
        if shot_list:
            paired: list[tuple[Any, dict, dict]] = []
            with ThreadPoolExecutor(max_workers=parallel_shots) as pool:
                for shot_index, shot in enumerate(shot_list):
                    shot_id = shot.get("shot_id", f"shot_{shot_index:03d}")
                    baseline_structure = _derive_baseline_structure(
                        shot, voice_timeline, shot_id
                    )
                    variants = _build_variants(
                        shot_id=shot_id,
                        shot_index=shot_index,
                        baseline_structure=baseline_structure,
                    )
                    for variant in variants:
                        fut = pool.submit(_generate_variant, shot, shot_index, variant)
                        paired.append((fut, shot, variant))
                for fut, shot, variant in paired:
                    result = fut.result()
                    if isinstance(result, dict) and result.get("degraded"):
                        degraded_count += 1
                        continue
                    shot_id = shot.get("shot_id", "")
                    record = {
                        "shot_id": shot_id,
                        "variant_id": variant["variant_id"],
                        "structure_delta": variant["structure_delta"],
                        "clip_path": result.get("clip_path", ""),
                        "generation_time_ms": result.get("generation_time_ms", 0),
                        "engine": result.get("engine", ""),
                    }
                    asset_bus_write("rapid-preview-clips", record)
                    generated_count += 1

    # 4. Episode-level full-degrade check (RAPID-PREVIEW-05 + BLOCKER #1).
    #    Triggers ONLY when ALL variants across ALL shots degraded. Partial
    #    degrades are silently counted above (recoverable — the generated
    #    successes still flow to rapid-preview-clips).
    if total_variants > 0 and degraded_count == total_variants:
        skip_reason = f"all_variants_degraded: {degraded_count}/{total_variants}"
        logger.warning(
            "preview_skipped: episode=%s %s — falling back to p11 direct Seedance",
            episode_id, skip_reason,
        )
        asset_bus_write("episode-meta", {
            "episode_id": episode_id,
            "preview_skipped": True,
            "skip_reason": skip_reason,
        })

    # 5. No gate for p10b (GATE_ID is None — CF-36-04 conditional skip).
    return {
        "phase": PHASE_ID,
        "outputs": {
            "variants_generated": generated_count,
            "variants_degraded": degraded_count,
        },
        "gate": None,
    }


# ---------------------------------------------------------------------------
# Helpers — input derivation (used by run(); defined after for readability)
# ---------------------------------------------------------------------------


def _resolve_keyframe(e_konte: dict, shot_id: str) -> str | None:
    """Resolve the keyframe image path for ``shot_id`` from e-konte-sheets."""
    if not isinstance(e_konte, dict):
        return None
    shots = e_konte.get("shots", [])
    if isinstance(shots, list):
        for shot in shots:
            if isinstance(shot, dict) and shot.get("shot_id") == shot_id:
                return shot.get("keyframe")
    return None


def _derive_baseline_structure(
    shot: dict,
    voice_timeline: dict,
    shot_id: str,
) -> dict:
    """Derive the baseline structure{} dict for one shot.

    Per CONTEXT "Variant Matrix" — the 4 structure params come from the
    shot's intent + voice timeline. For v6.0 we use a deterministic default
    baseline (since the upstream p01-p09 baseline structure{} fields are
    not yet finalized — Phase 41 will wire the real structure{} fields).
    Tests can override this default by injecting their own baseline via
    the shot dict (key ``baseline_structure``).
    """
    # Operator/test override: if the shot carries its own baseline, use it.
    if isinstance(shot, dict) and isinstance(shot.get("baseline_structure"), dict):
        return shot["baseline_structure"]
    # Default baseline (deterministic; per CONTEXT structure{} fields).
    return {
        "hook_position_sec": 3,
        "emotion_sequence": ["suppress", "thrill"],
        "turning_points_sec": [3, 15],
        "ending_state": "new_suspense",
    }
