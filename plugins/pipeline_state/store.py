"""PipelineStateStore — Python port of the state-management extract from
``kais-movie-agent/lib/pipeline.js`` (Phase 33-01, SC#1).

Reference Node.js source:
- ``pipeline.js:217-249``  — ``_loadState`` / ``_saveState`` (file shape + load
  fallback to empty on missing/corrupt).
- ``pipeline.js:611-618``  — ``_findResumeIndex`` (first phase whose status is
  NOT in the done-set is the resume point).
- ``pipeline.js:553,612,668`` — ``DONE_STATUSES = {completed, approved,
  awaiting_review}``.

This module is the **data layer only**. The full run/resume orchestration loop
(launching phase handlers, parallelism, retries) belongs to Phase 35
(HERMES-SKILL-02). Here we provide:

- ``PipelineState`` frozen-ish dataclass representing the on-disk state file.
- ``PipelineStateStore`` with: ``load``, ``save``, ``save_checkpoint``,
  ``load_latest_checkpoint``, ``find_resume_phase``.

Design decisions (see ``CONTEXT.md``):
- D-33-01: pure stdlib, no third-party deps.
- D-33-02: atomic write via ``tempfile.mkstemp`` + ``os.replace`` (Node.js
  uses raw ``writeFile`` for state — we harden because a half-written state
  file corrupts an entire episode).
- CF-06: state file is ``.pipeline-state.json`` at the workdir **root**, NOT
  under ``.pipeline-assets/`` (the latter is owned by AssetBus, Plan 33-02).
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Phases whose status is one of these are considered "done" — re-running them
# would duplicate work. ``awaiting_review`` is in this set because the work is
# already submitted; the human-review loop is owned by Phase 34 (Gate).
# Matches Node.js pipeline.js:553,612,668.
DONE_STATUSES = frozenset({"completed", "approved", "awaiting_review"})


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass
class PipelineState:
    """On-disk pipeline state for a single episode/workdir.

    Mirrors the JSON shape documented in CONTEXT CF-06. Fields with
    ``None`` default are omitted-on-the-wire visually (serialized as null)
    but forward compatibly — ``load`` filters to known keys so new fields
    added later don't break old code.
    """

    episode: str
    phases: dict[str, dict] = field(default_factory=dict)
    current_phase_id: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    last_resumed_at: str | None = None
    trace_id: str | None = None
    # v14.0 FORM-01: episode-level form factor. Literal["landscape","portrait"]
    # strict enum; unknown values raise ValueError via __post_init__. Default
    # "portrait" preserves all existing 短剧 (9:16) projects — backward compat.
    # Per CONTEXT.md D-01: no fuzzy matching, no warnings-and-continue.
    form_factor: Literal["landscape", "portrait"] = "portrait"
    # v15.0 GENOME-01 (M1 genome core, Kai 0915 拍板): runtime gene profile id.
    # None = 零行为（不加载档案、不做存在性检查、管线行为与无基因完全一致
    # ——「剥离 = genome_id 置空」契约）。form_factor (FORM-01) 同款 episode
    # 级不变量先例。这里**只验格式不验存在性**：state 是纯数据层，档案存在性
    # 由 pipeline/genome_loader.py 在使用点验证（load 失败在 runner/bridge 侧
    # 显式 fail-loud），避免 state 读写路径引入文件系统依赖。格式校验规则与
    # genome_loader.validate_genome_id 双侧同源——此处防落盘 episode JSON
    # 被篡改，loader 侧防 requirement.json 直读绕过 state 的路径。
    genome_id: str | None = None
    # NC-VAR-01 (2026-08-26 B1): pipeline variant selector — episode-level
    # invariant, same rank as form_factor. "drama" (default) = V8.6 短剧 DAG;
    # "narration_comic" = 解说漫 8-phase variant DAG. The runner writes it
    # into a fresh episode's state and fail-fast validates it on resume
    # (switching types mid-episode would misalign the checkpoint cursor).
    # Old state files lack the key — ``load``'s _STATE_FIELDS forward-compat
    # filter fills the dataclass default "drama", so legacy episodes resume
    # unchanged.
    # MV-VAR (2026-10-15): "mv" = MV 变体 13-phase DAG（5 mv* 新相 + 8 复用
    # p* 相，mv-variant-dag/DESIGN.md §5.2）。旧 state 前向兼容同由
    # _STATE_FIELDS 补默认机制承接，零额外代码。
    pipeline_type: Literal["drama", "narration_comic", "mv"] = "drama"

    def __post_init__(self) -> None:
        """Validate form_factor + pipeline_type against their strict enums.

        stdlib ``Literal`` is NOT enforced at runtime by default — it's a
        type-checker hint only. We enforce at construction time per
        CONTEXT.md D-01 (strict enum, no fuzzy matching). This catches
        typos and tampering in episode JSON (T-71-01 threat mitigation).
        """
        if self.form_factor not in ("landscape", "portrait"):
            raise ValueError(
                f"PipelineState.form_factor must be 'landscape' or 'portrait', "
                f"got {self.form_factor!r} (FORM-01 v14.0 strict enum — "
                "no fuzzy matching, no warnings-and-continue)."
            )
        # GENOME-01: format-only validation. Path separators / '..' are
        # rejected so a tampered state file can never steer the genome
        # loader outside <genome_dir>/<genome_id>/ (path-traversal guard).
        # Existence is deliberately NOT checked here — a missing archive
        # raises at the point of use (genome_loader.load_genome), keeping
        # this dataclass filesystem-free.
        if self.genome_id is not None:
            gid = self.genome_id
            if not isinstance(gid, str) or not gid.strip():
                raise ValueError(
                    f"PipelineState.genome_id must be a non-empty str or None, "
                    f"got {gid!r} (GENOME-01 v15.0 format guard — "
                    "None means zero behavior; an explicit id must be real)."
                )
            if "/" in gid or "\\" in gid or ".." in gid:
                raise ValueError(
                    f"PipelineState.genome_id contains a path separator or "
                    f"'..': {gid!r} (GENOME-01 v15.0 path-traversal guard — "
                    "genome ids are flat directory names)."
                )
        if self.pipeline_type not in ("drama", "narration_comic", "mv"):
            raise ValueError(
                f"PipelineState.pipeline_type must be one of 'drama', "
                f"'narration_comic', 'mv', got {self.pipeline_type!r} "
                "(NC-VAR-01 strict enum — no fuzzy matching, no "
                "warnings-and-continue)."
            )

    # Expose DONE_STATUSES on the class too for ergonomic access from
    # callers that already hold a state instance. Kept as a class attribute
    # so it is shared (frozenset is immutable).
    DONE_STATUSES = DONE_STATUSES


# ---------------------------------------------------------------------------
# Atomic write helper
# ---------------------------------------------------------------------------

# Known PipelineState field names — used by ``load`` to filter forward-compat
# keys. Computed once at import time.
_STATE_FIELDS = frozenset(PipelineState.__dataclass_fields__.keys())


def validate_form_factor_invariant(state: PipelineState) -> bool:
    """Reject per-shot ``form_factor`` overrides in ``state.phases``.

    ``form_factor`` is an EPISODE-LEVEL invariant (ARCHITECTURE Anti-Pattern
    1 / FORM-06 deferred anti-feature). Allowing per-shot overrides would
    break LTX-MSR ICLoRA reference conditioning, which requires a consistent
    aspect ratio across reference frames within one episode.

    This function recursively scans ``state.phases`` (a nested dict tree)
    for any key named ``"form_factor"`` appearing below the episode level.
    The episode-level field on the dataclass itself is the ONLY legitimate
    location.

    Returns ``True`` if the invariant holds (no per-shot overrides), ``False``
    if a per-shot ``form_factor`` key was found anywhere in the phases tree.
    """
    def _scan(obj) -> bool:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "form_factor":
                    return False
                if not _scan(v):
                    return False
        elif isinstance(obj, list):
            for item in obj:
                if not _scan(item):
                    return False
        return True

    return _scan(state.phases)


# ---------------------------------------------------------------------------
# DUB-02 TTS engine division rule (v14.0 Phase 72)
# ---------------------------------------------------------------------------

# Valid tts_engine values per CONTEXT.md D-01 / DUB-02. Stored as frozenset for
# O(1) membership tests. Mirrors the ``_STATE_FIELDS = frozenset(...)`` pattern
# at line 108 above.
#
# v15.0 Qwen3-TTS 适配 (2026-07-12): 新增 ``qwen_tts`` 作为默认引擎;旧值
# ``cosyvoice`` / ``indextts2_fallback`` 保留为向后兼容别名 (实际请求会被
# 路由到 Qwen3-TTS)。See ``templates/tts_batch.py`` DEFAULT_TTS_ENGINE 注释。
#
# v15.1 (2026-07-19): ``ltx_native`` 已废弃移除 — LTX 2.3 自生成对白不可靠
# (BGM bias + 嘴型不同步)。所有对白走 TTS + 5stage_pipeline,或后期配音(silent)。
#
# v15.2 IndexTTS 2.5 适配 (2026-08-13): 新增 ``indextts25`` 作为可选引擎。
#
# v15.3 (2026-08-16 Kai 决策): ``indextts25`` (VoiceDesign→IndexTTS 2.5 经
# KAP API) 成为**默认引擎** — KMC 管线创作音频唯一链路; ``qwen_tts`` 降级为
# legacy 显式可选 (老项目 resume 不炸)。枚举保留全部值 (严格枚举不禁 legacy),
# 只有缺省值变化。
#
# v15.4 (2026-09-04 feat/tts-breeze): ``indextts25`` 链的合成后端切换为
# Breeze TTS 2 (经 KAP 兼容层) — 枚举值/缺省值/本模块零行为变化，路由键语义
# = KAP 兼容链。详见 plugins/kais_aigc/tts_engine.py IndexTTS25Engine。
TTS_ENGINE_VALUES = frozenset({
    "qwen_tts", "cosyvoice", "indextts2_fallback", "indextts25",
})
# v15.3: 缺省引擎 (shot 未声明 tts_engine 字段时)
TTS_ENGINE_DEFAULT = "indextts25"


def validate_tts_engine_division(shot_list: list[dict]) -> None:
    """Validate that every shot's ``tts_engine`` is in the legal enum.

    Original DUB-02 was a division rule (forbid ltx_native + qwen_tts on the
    same shot to prevent doubled audio). With ltx_native removed (v15.1),
    the rule simplifies to enum validation only — kept as a pre-flight guard
    so bad shot-lists fail fast with an actionable error rather than crashing
    downstream in tts_batch.generate_tts().

    Each shot dict MAY declare:
      - ``tts_engine``: Literal["qwen_tts", "cosyvoice", "indextts2_fallback",
        "indextts25"]
        (defaults to ``TTS_ENGINE_DEFAULT`` = ``"indextts25"`` per the v15.3
        2026-08-16 decision — the VoiceDesign→IndexTTS 2.5 chain via KAP is
        the default and only creative-audio link; ``qwen_tts`` / ``cosyvoice``
        / ``indextts2_fallback`` remain LEGACY values accepted for old-project
        resume and route to the Qwen3-TTS backend — see IndexTTS25Engine)

    Backward compat: old shot-lists without the key load cleanly via
    ``.get(..., default)`` — zero migration script needed.

    Raises:
        ValueError: if any shot entry is not a dict, or has an invalid enum value.
    """
    for i, shot in enumerate(shot_list):
        if not isinstance(shot, dict):
            # WR-07: previously silently skipped non-dict entries. The strict-
            # enum philosophy of DUB-02 (no fuzzy matching, no warnings-and-
            # continue) is undercut by silent skip — a shot_list containing
            # None (common JSON-decode artifact) would be silently accepted,
            # then crash later with a less actionable error. Reject explicitly.
            raise ValueError(
                f"validate_tts_engine_division: shot_list[{i}] is not a dict "
                f"(got {type(shot).__name__}: {shot!r}). Possible asset-bus "
                f"corruption — every shot entry must be a dict with optional "
                f"key tts_engine. (DUB-02 strict enum)"
            )
        # WR-07 / IN-06: include shot index in the fallback sid so error
        # messages are traceable when shot_id is absent.
        sid = shot.get("shot_id") or f"<index {i}>"
        # v15.3 (2026-08-16): default 升级为 ``indextts25`` (Kai 唯一链路决策)
        tts_engine = shot.get("tts_engine", TTS_ENGINE_DEFAULT)

        if tts_engine not in TTS_ENGINE_VALUES:
            raise ValueError(
                f"Shot {sid}: tts_engine must be one of "
                f"{sorted(TTS_ENGINE_VALUES)}, got {tts_engine!r} "
                f"(DUB-02 strict enum — no fuzzy matching, no "
                f"warnings-and-continue)."
            )


def _atomic_write_text(path: Path, data: str) -> None:
    """Atomic write via ``tempfile.mkstemp`` + ``os.replace``.

    Mirrors Node.js ``write-tmp-then-rename`` (asset-bus.js:160-165) per
    D-33-02. ``mkstemp`` guarantees a unique fd+path atomically — no
    pre-generation needed (an earlier revision pre-computed a pid+ms+rand
    tmp name, but never used it; that dead code is removed here).
    ``os.replace`` is atomic on POSIX (single-filesystem rename(2)).

    Notable: no explicit ``fsync``. Node.js doesn't fsync the state file
    either; matching behavior preserves the perf profile and the durability
    contract callers already rely on.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_str = tempfile.mkstemp(
        prefix=f"{path.name}.tmp.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        os.close(fd)
    except OSError:
        pass
    with open(tmp_str, "w", encoding="utf-8") as f:
        f.write(data)
    os.replace(tmp_str, str(path))


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------


class PipelineStateStore:
    """Persists pipeline state per workdir.

    File location: ``<workdir>/.pipeline-state.json`` (workdir ROOT, not
    under ``.pipeline-assets/`` — see CONTEXT CF-06).
    """

    STATE_FILE = ".pipeline-state.json"

    def __init__(self, workdir: str | Path):
        self._workdir = Path(workdir)
        self._path = self._workdir / self.STATE_FILE

    # -- load / save -------------------------------------------------------

    def load(self) -> PipelineState:
        """Load state, falling back to empty on missing/corrupt file.

        Mirrors Node.js ``_loadState`` (pipeline.js:217-224): a missing or
        unparseable state file is treated as a fresh episode rather than an
        error — the pipeline simply starts over.
        """
        try:
            raw_text = self._path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return PipelineState(episode="")
        except OSError as exc:
            logger.warning(
                "PipelineStateStore.load: unreadable state file %s: %s",
                self._path,
                exc,
            )
            return PipelineState(episode="")

        try:
            raw = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.warning(
                "PipelineStateStore.load: corrupt state file %s: %s",
                self._path,
                exc,
            )
            return PipelineState(episode="")

        if not isinstance(raw, dict):
            logger.warning(
                "PipelineStateStore.load: state file %s is not a JSON object",
                self._path,
            )
            return PipelineState(episode="")

        # Forward-compat filter: keep only known keys. Lets us add fields
        # without breaking older code that round-trips through the file.
        filtered = {k: v for k, v in raw.items() if k in _STATE_FIELDS}
        if "episode" not in filtered:
            filtered["episode"] = ""
        try:
            return PipelineState(**filtered)
        except TypeError:
            # Defensive — should be unreachable given the filter above.
            return PipelineState(episode=str(filtered.get("episode", "")))

    def save(self, state: PipelineState) -> None:
        """Atomically write state to ``.pipeline-state.json``.

        D-33-02: deviates from Node.js (which uses raw ``writeFile``) by
        using tmp-then-rename atomicity. Half-written state = corrupt
        episode; we harden.
        """
        data = json.dumps(
            asdict(state), indent=2, ensure_ascii=False
        )
        _atomic_write_text(self._path, data)

    # -- checkpoint helpers ------------------------------------------------

    def save_checkpoint(
        self,
        episode_id: str,
        phase: str,
        payload: dict,
        status: str = "completed",
    ) -> None:
        """Persist one phase's checkpoint (the SC#1 tool operation).

        - Sets ``state.episode`` only if empty (an episode is bound to its
          state file for its lifetime — a later call with a different
          ``episode_id`` does NOT silently flip it).
        - Records ``state.phases[phase]`` with ``status=<status>`` + ISO
          ``completed_at`` + ``result=payload``. Default status is
          ``"completed"``; the runner passes ``"incomplete"`` when the
          manifest count gate fails (RUNTIME-03 / Phase 11 / 11-03).
        - Advances ``current_phase_id`` to ``phase``.

        ``status`` kwarg (added in Phase 11 / 11-03 for RUNTIME-03) is
        optional and defaults to ``"completed"`` so legacy callers
        (e.g. ``tools.py``'s ``save_checkpoint`` tool) that don't pass it
        observe zero behavior change.
        """
        from datetime import datetime, timezone

        state = self.load()
        if not state.episode:
            state.episode = episode_id
        state.phases[phase] = {
            "status": status,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "result": payload,
        }
        state.current_phase_id = phase
        self.save(state)

    def load_latest_checkpoint(
        self, episode_id: str
    ) -> dict | None:
        """Most-recent phase checkpoint for the episode (SC#1 resume op).

        Returns ``None`` when:
        - The episode id doesn't match the state file's bound episode.
        - No checkpoint has been saved yet (``current_phase_id`` is None).
        """
        state = self.load()
        if state.episode != episode_id:
            return None
        if state.current_phase_id is None:
            return None
        return state.phases.get(state.current_phase_id)

    def find_resume_phase(
        self, phase_order: list[str]
    ) -> str | None:
        """First phase NOT in ``DONE_STATUSES``, or ``None`` if all done.

        Mirrors ``pipeline.js:611-618``. A phase is "done" if its recorded
        status is ``completed`` / ``approved`` / ``awaiting_review`` (the
        last counts as done because re-running would duplicate submitted
        work awaiting human review).
        """
        state = self.load()
        for phase_id in phase_order:
            phase_state = state.phases.get(phase_id)
            if phase_state is None:
                return phase_id
            if phase_state.get("status") not in DONE_STATUSES:
                return phase_id
        return None
