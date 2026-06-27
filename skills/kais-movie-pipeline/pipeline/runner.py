"""runner.py — V8.6 13-phase orchestration runner (Phase 35-02).

Phase 35 scope:
  - Registry iteration (PHASE_REGISTRY)
  - Checkpoint save after each phase + resume from latest checkpoint
  - ``parallel_shots: int = 4`` config plumbing (D-35-06; actual parallel
    dispatch lives in Phase 36 p11 video phase)

Phase 36 will add:
  - Real parallel shot dispatch in the video phase
  - Retry / backoff policies

Production entry point::

    python -m pipeline.runner --episode <id> --workdir <dir>

(when invoked from inside the skill directory; or use the file path with
``python skills/kais-movie-pipeline/pipeline/runner.py``).

D-35-07 contract: phase modules receive four injected callables
(``asset_bus_read``, ``asset_bus_write``, ``delegate_task``,
``trigger_gate``). Production wiring provides real implementations; tests
inject mocks via the ``inject`` parameter (avoids monkeypatching).

D-35-08: tests never spawn real subagents / make real HTTP. ``inject`` exists
precisely so tests can replace ``delegate_task`` and ``trigger_gate`` with
plain Python callables.
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

# Phase modules import their sibling ``phases`` package — same directory.
# When this file is imported via ``from pipeline import runner`` (with the
# skill directory on sys.path), this relative import works.
from pipeline.phases import PHASE_REGISTRY

# Phase 40 CR-01 fix: the runner's injected ``_asset_bus_write`` /
# ``_asset_bus_read`` callables dispatch on slot format (JSON vs JSONL) to
# route writes to the correct AssetBus method. We import ASSET_SCHEMA
# top-level so the dispatch lookup is in the module's globals (cheap).
# Lazy import is unnecessary here — ``asset_bus`` is already pulled in by
# ``_make_production_bus`` when the runner actually runs, and importing the
# module itself is cheap (stdlib-only).
from plugins.pipeline_state.asset_bus import ASSET_SCHEMA

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RunnerConfig
# ---------------------------------------------------------------------------


@dataclass
class RunnerConfig:
    """Runner configuration (D-35-06 + D-35-08 + D-37-01 Phase 37 hooks).

    ``parallel_shots`` defaults to 4 to preserve v2.0 behavior. Phase 35
    plumbs the config; Phase 36 implements actual parallel shot dispatch
    inside the p11 video phase. ``parallel_shots`` is included in the
    ``run_episode`` return payload so callers / operators can audit what
    value was in effect for a given episode.

    ``workdir`` is the working directory the runner operates in. It's passed
    to ``PipelineStateStore(workdir)`` and ``AssetBus(workdir)`` (the
    production defaults for ``store`` / ``bus`` — overridable via ``inject``).

    ``enable_gates`` controls whether the ``trigger_gate`` callable is
    forwarded to phase modules. When ``False``, phase modules receive
    ``None`` and skip gate logic entirely (used in dry-run / re-run scenarios
    where gates have already been approved).

    Phase 37 event hooks (D-37-01 callback injection; D-37-06 default None
    preserves Phase 35/36 regression):

    ``on_phase_complete`` — Optional callback invoked AFTER
    ``store.save_checkpoint`` for each phase, with signature
    ``(episode_id, phase_id, result) -> None``. The subscriber (Phase 37-02
    ``canvas_sync.CanvasSyncSubscriber``) listens here to push the phase's
    canvas node. Invoked only when non-None; the runner wraps the call in
    ``try/except`` (D-37-04) so a buggy/missing subscriber never crashes the
    episode — progress is already checkpointed, so resume still works.

    ``on_gate_resolved`` — Optional callback mirror kept on the config for
    symmetry / audit. The gate-resolution trigger path is module-level in
    ``runner_hooks`` (D-37-07, set via ``set_gate_resolved_hook``), because
    ``pause_for_review`` is invoked from phase modules via ``trigger_gate``
    and threading the callback through would touch all 13 phase modules. This
    field is reserved for future direct invocation paths and is currently
    unused by the runner loop; documenting it here keeps the config the
    single source of truth for subscriber wiring.
    """

    parallel_shots: int = 4
    workdir: str = "."
    enable_gates: bool = True
    # Phase 37 — canvas sync event hooks. Defaults None = no-op, preserves
    # Phase 35/36 test behavior when subscriber not registered (D-37-06).
    on_phase_complete: Callable[[str, str, dict], None] | None = None
    on_gate_resolved: Callable[[str, str, str, dict], None] | None = None


# ---------------------------------------------------------------------------
# Production-wired callable factories
# ---------------------------------------------------------------------------


def _make_production_delegate() -> Callable[..., dict]:
    """Construct the production ``delegate_task`` callable.

    Returns a thin wrapper around ``tools.delegate_task.delegate_task`` so
    phase modules receive a uniform ``(goal, context, toolsets) -> dict``
    signature. The wrapper exists so test code can replace this with a
    plain lambda without monkeypatching the tool registry.

    Import is local so that ``runner.py`` can be imported in test
    environments where ``tools.delegate_task`` isn't on sys.path (the test
    injects a mock via the ``inject`` parameter and never touches this code
    path).
    """

    def _delegate(goal: str, context: str, toolsets: list[str]) -> dict:
        from tools.delegate_task import delegate_task as _real_delegate_task

        return _real_delegate_task(
            goal=goal, context=context, toolsets=toolsets
        )

    return _delegate


def _make_production_trigger_gate() -> Callable[[str, str], dict]:
    """Construct the production ``trigger_gate`` callable.

    Wraps ``plugins.review_gates.runner_hooks.pause_for_review`` so phase
    modules see a uniform ``(gate_id, episode_id) -> dict`` signature.
    """

    def _trigger(gate_id: str, episode_id: str) -> dict:
        from plugins.review_gates import runner_hooks

        return runner_hooks.pause_for_review(
            gate_id, episode_id, payload={}, mode=None
        )

    return _trigger


def _make_production_store(workdir: str):
    """Construct the production ``PipelineStateStore``.

    Local import to avoid hard dependency on Phase 33 module at import time
    (lets tests run without the plugin installed).
    """
    from plugins.pipeline_state.store import PipelineStateStore

    return PipelineStateStore(workdir)


def _make_production_bus(workdir: str):
    """Construct the production ``AssetBus``."""
    from plugins.pipeline_state.asset_bus import AssetBus

    return AssetBus(workdir)


# ---------------------------------------------------------------------------
# Resume helpers
# ---------------------------------------------------------------------------


def _compute_start_index(checkpoint: dict | None) -> int:
    """Map a checkpoint's phase id to the registry index to resume AFTER.

    Returns the index of the phase immediately following the checkpointed
    phase. Returns 0 when:
      - ``checkpoint`` is None (no checkpoint exists for this episode)
      - The checkpointed phase id is not in the registry (orphaned
        checkpoint — start fresh to avoid silently skipping everything)

    Args:
        checkpoint: A dict carrying the completed phase id under key
            ``"phase"``. This matches the payload shape returned by
            ``PipelineStateStore.load_latest_checkpoint`` when augmented
            with the phase id (the runner writes ``{"phase": phase_id}``
            into the checkpoint payload when calling ``save_checkpoint``
            so resume can find the cursor).
    """
    if not checkpoint:
        return 0
    last_phase = checkpoint.get("phase")
    if not last_phase:
        # PipelineStateStore's canonical payload is
        # ``{"status": ..., "completed_at": ..., "result": ...}`` —
        # without the phase id we can't locate the cursor, so start fresh.
        return 0
    for idx, entry in enumerate(PHASE_REGISTRY):
        if entry.get("id") == last_phase:
            return idx + 1
    return 0


def _parallel_shots_kwargs(module, parallel_shots: int) -> dict:
    """Return ``{"parallel_shots": parallel_shots}`` if ``module.run`` accepts
    a ``parallel_shots`` parameter, else ``{}``.

    Only p11_video_render declares ``parallel_shots`` (D-36-08 — keyword-only
    after ``*``). The other 12 phases use the standard 5-arg Phase 35
    signature without ``**kwargs``; blindly forwarding ``parallel_shots``
    would raise ``TypeError`` for them. We introspect the signature once per
    phase invocation to decide.

    Cheap (microseconds): ``inspect.signature`` is cached on the callable.
    """
    import inspect

    try:
        sig = inspect.signature(module.run)
    except (TypeError, ValueError):
        return {}
    if "parallel_shots" in sig.parameters:
        return {"parallel_shots": parallel_shots}
    return {}


# ---------------------------------------------------------------------------
# run_episode — the orchestration loop
# ---------------------------------------------------------------------------


def run_episode(
    episode_id: str,
    config: RunnerConfig | None = None,
    *,
    inject: dict[str, Any] | None = None,
) -> dict:
    """Run the full pipeline for one episode.

    Iterates ``PHASE_REGISTRY`` sequentially, invoking each phase module's
    ``run()`` with four injected callables. Saves a checkpoint after each
    phase so that re-invocation with the same ``episode_id`` resumes at
    the next phase.

    Args:
        episode_id: Stable identifier for this episode (used as the
            checkpoint key). The same id on re-run resumes the same
            pipeline state.
        config: RunnerConfig (defaults: parallel_shots=4, workdir=".",
            enable_gates=True).
        inject: Optional dict overriding production callables. Recognized
            keys (any subset; missing keys use production defaults):
              - ``"store"`` — PipelineStateStore-like (load_latest_checkpoint,
                save_checkpoint)
              - ``"bus"`` — AssetBus-like (read, write)
              - ``"delegate_task"`` — Callable(goal, context, toolsets) -> dict
              - ``"trigger_gate"`` — Callable(gate_id, episode_id) -> dict;
                only forwarded to phases when ``config.enable_gates`` is True

    Returns:
        dict with keys:
          - ``episode_id`` — input echoed back
          - ``phases`` — {phase_id: phase_result, ...} for phases that ran
            this invocation (skipped-on-resume phases are NOT included)
          - ``parallel_shots`` — config value echoed (audit trail)
          - ``resumed_from`` — registry index the run started at (0 = fresh)
    """
    cfg = config or RunnerConfig()
    overrides = inject or {}

    # Wire up callables (production defaults + inject overrides)
    store = overrides.get("store") or _make_production_store(cfg.workdir)
    bus = overrides.get("bus") or _make_production_bus(cfg.workdir)
    delegate = overrides.get("delegate_task") or _make_production_delegate()

    # trigger_gate: when enable_gates is False, phase modules MUST receive
    # None so they skip gate logic. The injected callable (if any) is
    # ignored in that case (otherwise tests that inject a spy would see it
    # called even when gates are nominally disabled, making the config
    # meaningless).
    if cfg.enable_gates:
        trigger_gate = overrides.get("trigger_gate") or _make_production_trigger_gate()
    else:
        trigger_gate = None

    # Asset-bus adapter callables — phase modules receive these, not the
    # raw bus object, so test doubles can be plain callables.
    def _asset_bus_read(slot: str) -> Any:
        # JSONL slots must dispatch to read_lines; JSON slots dispatch to read.
        # Mirrors the write-side dispatch below (Phase 40 CR-01 fix).
        schema = ASSET_SCHEMA.get(slot, {})
        if schema.get("format") == "jsonl":
            return bus.read_lines(slot)
        return bus.read(slot)

    def _asset_bus_write(slot: str, entry: dict) -> None:
        # Phase 40 CR-01 fix: dispatch on slot format. JSONL-format slots
        # (e.g., rapid-preview-clips, finetune-dataset) MUST route through
        # ``append_line`` — ``AssetBus.write()`` explicitly raises
        # ``AssetBusError`` for JSONL slots (asset_bus.py:469-472). Without
        # this dispatch the very first successful p10b variant record would
        # raise inside the runner and be swallowed by p10b's outer
        # ``except Exception``, silently downgrading every episode to
        # ``preview_skipped=True`` regardless of actual engine health.
        # JSON slots use the envelope-wrapped atomic write path.
        schema = ASSET_SCHEMA.get(slot, {})
        if schema.get("format") == "jsonl":
            bus.append_line(slot, entry)
        else:
            bus.write(slot, entry, envelope=True)

    # Resume detection
    checkpoint = store.load_latest_checkpoint(episode_id)
    start_idx = _compute_start_index(checkpoint)

    logger.info(
        "run_episode: episode=%s start_idx=%d (checkpoint=%r)",
        episode_id, start_idx, bool(checkpoint),
    )

    results: dict[str, dict] = {}
    for idx in range(start_idx, len(PHASE_REGISTRY)):
        if idx >= len(PHASE_REGISTRY):
            break
        phase_entry = PHASE_REGISTRY[idx]
        phase_id = phase_entry.get("id")
        module = phase_entry.get("module")
        if not phase_id or module is None:
            logger.warning(
                "run_episode: malformed PHASE_REGISTRY entry at idx %d: %r — skipping",
                idx, phase_entry,
            )
            continue

        logger.info(
            "run_episode: episode=%s phase=%s (idx=%d)",
            episode_id, phase_id, idx,
        )

        result = module.run(
            episode_id=episode_id,
            asset_bus_read=_asset_bus_read,
            asset_bus_write=_asset_bus_write,
            delegate_task=delegate,
            trigger_gate=trigger_gate,
            # Forward parallel_shots via keyword-only injection. Only p11
            # declares this kwarg (D-36-08); other phases ignore it via
            # **kwargs or the standard 5-arg signature. Phases with the
            # Phase 35 base signature (no **kwargs) would TypeError on this
            # extra kwarg, so we inspect the signature first and only pass
            # parallel_shots when the phase module accepts it.
            **_parallel_shots_kwargs(module, cfg.parallel_shots),
        )
        results[phase_id] = result

        # Checkpoint AFTER each phase — even if a later phase crashes, the
        # completed ones are persisted and the next run_episode resumes here.
        # The payload carries the phase id under "phase" so _compute_start_index
        # can locate the cursor on resume (PipelineStateStore also records
        # status + completed_at via save_checkpoint's own bookkeeping).
        store.save_checkpoint(
            episode_id,
            phase_id,
            {"phase": phase_id, "result": result},
        )

        # Phase 37 — phase completion event hook. Guarded so a buggy/missing
        # subscriber never crashes the episode (D-37-04). The callback is
        # invoked AFTER the checkpoint is persisted — if the subscriber
        # crashes, the episode's progress is already saved and resume works
        # on the next run. Default None short-circuits the guard (D-37-06),
        # so Phase 35/36 tests that construct RunnerConfig() without hooks
        # observe zero behavior change.
        if cfg.on_phase_complete is not None:
            try:
                cfg.on_phase_complete(episode_id, phase_id, result)
            except Exception:
                logger.warning(
                    "run_episode: on_phase_complete callback raised "
                    "(episode=%s phase=%s) — swallowed, episode continues",
                    episode_id, phase_id,
                    exc_info=True,
                )

    return {
        "episode_id": episode_id,
        "phases": results,
        "parallel_shots": cfg.parallel_shots,
        "resumed_from": start_idx,
    }


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def _main(argv: list[str] | None = None) -> int:
    """Argparse CLI. NOT exercised by Phase 35 tests (E2E is Phase 39)."""
    parser = argparse.ArgumentParser(
        prog="pipeline.runner",
        description="Run the V8.6 13-phase kais-movie-pipeline for one episode.",
    )
    parser.add_argument(
        "--episode", required=True,
        help="Episode identifier (used as checkpoint key).",
    )
    parser.add_argument(
        "--workdir", default=".",
        help="Working directory for state + asset bus (default: cwd).",
    )
    parser.add_argument(
        "--parallel-shots", type=int, default=4,
        help="Shot-level parallelism (default: 4 per D-35-06).",
    )
    parser.add_argument(
        "--no-gates", action="store_true",
        help="Disable review-gate triggering (phase modules receive None).",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable INFO logging.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    cfg = RunnerConfig(
        parallel_shots=args.parallel_shots,
        workdir=args.workdir,
        enable_gates=not args.no_gates,
    )
    result = run_episode(args.episode, cfg)
    print(f"Episode {result['episode_id']}: "
          f"{len(result['phases'])} phases ran "
          f"(resumed_from={result['resumed_from']}, "
          f"parallel_shots={result['parallel_shots']})")
    return 0


if __name__ == "__main__":
    # Ensure the parent skill directory is on sys.path so that
    # ``from pipeline.phases import PHASE_REGISTRY`` resolves whether the
    # file is invoked as a script or via -m.
    _here = Path(__file__).resolve().parent
    _skill_root = _here.parent
    if str(_skill_root) not in sys.path:
        sys.path.insert(0, str(_skill_root))
    sys.exit(_main())
