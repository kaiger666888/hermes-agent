"""canvas_sync.py — Python port of Node.js ``lib/canvas-sync-hook.js``.

Phase 37 Plan 02 — the subscriber half of the canvas-sync migration.

Scope (D-37-03 split architecture):
  - ``canvas_graph.py`` (this plan's sibling module) holds the **pure**
    FlowGraph mutation logic — no I/O.
  - ``canvas_sync.py`` (this module) holds the **subscriber** — it does
    HTTP I/O via the Phase 32 ``CanvasClient`` (reused, not duplicated,
    per CF-37-01) and delegates graph mutation to ``canvas_graph``.

Trigger points:
  - ``on_phase_complete(episode_id, phase_id, result)`` — fires when the
    v5.0 runner finishes a phase (Phase 37-01 wires this into
    ``RunnerConfig.on_phase_complete``).
  - ``on_gate_resolved(episode_id, gate_id, decision, payload)`` — fires
    when a review gate is approved/rejected (Phase 37-01 wires this into
    ``runner_hooks.set_gate_resolved_hook``).

Degrade-tolerant contract (CANVAS-IN-HERMES-03):
  Every public method wraps its body in ``try/except Exception``. Canvas
  is observability tooling — pipeline correctness MUST NOT depend on
  canvas availability. The ``CanvasClient`` already returns degrade
  envelopes on connect/timeout/5xx; this layer adds defense-in-depth so
  even unforeseen bugs (KeyError, malformed graph) never crash the
  episode.

No Node.js runtime dependency (D-37-05): pure Python + httpx via
``CanvasClient``. No ``openclaw`` / ``Toonflow`` / sqlite references.
"""
from __future__ import annotations

import functools
import json
import logging
import os
import re
import subprocess
import time
from typing import Any, Optional

import httpx

from plugins.kais_aigc import canvas_graph
from plugins.kais_aigc.canvas import CanvasClient, CanvasClientError

logger = logging.getLogger(__name__)


class CanvasSyncValidationError(Exception):
    """Post-sync validator (node-count / round-trip) failed.

    Raised inside ``on_phase_complete`` *after* ``save_canvas`` returns 2xx,
    when a post-sync check detects the persisted canvas state does not match
    what we just built (P2-2). Propagates through ``on_phase_complete`` →
    ``runner._try_canvas_sync`` → stops the pipeline, on the same tier as
    ``CanvasClientError`` (P0-3).

    Distinct from ``CanvasClientError`` (HTTP 4xx — the server *rejected* our
    payload): this signals the save *succeeded at the transport layer* yet the
    persisted result is wrong — a silent partial persist or dropped node (the
    failure modes canvas_sync's fire-and-forget design previously hid).
    """


# ── Generated field-map loader ────────────────────────────────────
# The single source of truth lives at
# ``/data/workspace/kais-aigc-platform/schema/pipeline-field-map.yaml``.
# ``generate_mappings.py`` emits ``canvas_sync_mappings.py`` next to it.
# We load that file via importlib with an absolute path so this module
# works regardless of cwd / sys.path — the schema dir is not on the
# Python path inside the hermes-agent runtime.
_SCHEMA_MAPPINGS_PATH = os.environ.get(
    "KAIS_FIELD_MAP_GENERATED",
    "/data/workspace/kais-aigc-platform/schema/generated/canvas_sync_mappings.py",
)


def _load_generated_mappings() -> Any:
    """Import the generated ``canvas_sync_mappings`` module by file path.

    Falls back to an empty mappings module on any failure so canvas_sync
    remains degrade-tolerant — a missing/stale generated file logs a
    WARNING but does not crash the subscriber.
    """
    import importlib.util

    try:
        spec = importlib.util.spec_from_file_location(
            "kais_canvas_sync_mappings", _SCHEMA_MAPPINGS_PATH,
        )
        if spec is None or spec.loader is None:
            raise FileNotFoundError(f"cannot load spec for {_SCHEMA_MAPPINGS_PATH}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        logger.warning(
            "canvas_sync: failed to load generated field map at %s — "
            "structured-field mapping will be a no-op. Run "
            "`python schema/generate_mappings.py` in kais-aigc-platform.",
            _SCHEMA_MAPPINGS_PATH,
            exc_info=True,
        )
        return None


_MAPPINGS = _load_generated_mappings()


# ── save-v2 结构化字段类型表（2026-08-19 p07 400 修复）─────────────────
# KAP 服务端（canvasAssetSchema.ts）对资产节点 data 做 zod 校验：
#   * 基础字段表：audio/video/storyboard/asset/script 各自的 z.object 基座
#     （canvasAssetSchema.ts:51-119）
#   * 扩展字段表：pipeline-field-map.yaml（SSOT）按 canvas_type 生成的
#     YAML_OPTIONAL_FIELDS（frontend-zod-extensions.ts）
# 声明为 string 的字段收到 number（或反之）→ 整图 400 拒收。p07
# style_vector 的 5D 数值（composition=0.45 float）撞上 script 类型表
# 的 composition:string 即此症（管线因「同步失败就停」终止）。
#
# 本表 = SSOT yaml 的 per-canvas_type zod_type 分组 + 基础字段表的镜像。
# 供 _coerce_graph_schema_types 在 save 前把穿透字段的类型对齐 schema。

_SCHEMA_YAML_PATH = os.environ.get(
    "KAIS_FIELD_MAP_YAML",
    "/data/workspace/kais-aigc-platform/schema/pipeline-field-map.yaml",
)

# canvasAssetSchema.ts 基础 z.object 字段镜像（score 是 z.any() 不列）。
_BASE_SCHEMA_FIELD_TYPES: dict[str, dict[str, str]] = {
    "audio": {
        "filePath": "string", "shot_id": "string", "engine": "string",
        "duration_sec": "number", "text": "string", "clip_type": "string",
    },
    "video": {
        "filePath": "string", "shot_id": "string", "engine": "string",
        "duration_sec": "number", "resolution": "string",
        "codec": "string", "thumbnailUrl": "string",
    },
    "storyboard": {
        "label": "string", "shot_id": "string", "shot_type": "string",
        "duration_sec": "number", "filePath": "string", "scene_ref": "string",
    },
    "asset": {
        "filePath": "string", "label": "string", "assetType": "string",
        "prompt": "string", "description": "string", "scene_id": "string",
        "turnaround_path": "string",
    },
    "script": {
        "label": "string", "description": "string", "assetType": "string",
        "filePath": "string", "content": "string",
    },
}


@functools.lru_cache(maxsize=1)
def _load_schema_field_types() -> dict[str, dict[str, str]]:
    """canvas_type → {canvas_key: "string"|"number"}（SSOT yaml + 基座镜像）。

    Degrade-tolerant：yaml 缺失/坏损 → 只用基座镜像（save-v2 基础字段
    仍然受保护），并 WARNING 一次。
    """
    types: dict[str, dict[str, str]] = {
        ct: dict(fields) for ct, fields in _BASE_SCHEMA_FIELD_TYPES.items()
    }
    try:
        import yaml as _yaml
        with open(_SCHEMA_YAML_PATH, "r", encoding="utf-8") as _f:
            y = _yaml.safe_load(_f) or {}
        for _pid, _pdef in (y.get("phases") or {}).items():
            if not isinstance(_pdef, dict):
                continue
            ct = _pdef.get("canvas_type")
            if not isinstance(ct, str) or not ct:
                continue
            bucket = types.setdefault(ct, {})
            for _fd in (_pdef.get("fields") or {}).values():
                if not isinstance(_fd, dict):
                    continue
                ck = _fd.get("canvas_key")
                zt = _fd.get("zod_type")
                if isinstance(ck, str) and ck and zt in ("string", "number"):
                    bucket.setdefault(ck, zt)
    except Exception:
        logger.warning(
            "canvas_sync: failed to load %s — schema type coercion "
            "falls back to base-schema table only",
            _SCHEMA_YAML_PATH, exc_info=True,
        )
    return types


def _coerce_scalar_to_schema(value: Any, zod_type: str) -> Any:
    """Coerce one scalar to the schema-declared zod type.

    规则（只动标量；对象/数组保持原样——那类错配让服务端大声拒绝，
    不做静默 json 化掩盖）：
      * declared string + int/float → str(v)
      * declared string + bool → "true"/"false"
      * declared number + 数字字符串 → int/float
      * 其余 → 原样返回
    """
    if zod_type == "string":
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        return value
    if zod_type == "number":
        if isinstance(value, str):
            s = value.strip()
            if s:
                try:
                    return int(s) if s.lstrip("-").isdigit() else float(s)
                except ValueError:
                    return value
            return value
        return value
    return value


def _coerce_graph_schema_types(graph: dict[str, Any]) -> dict[str, Any]:
    """Graph-wide pre-save pass: align node.data scalar types to the save-v2
    schema table so a numeric passthrough can't 400 the whole graph.

    只处理受校验的资产类型（audio/video/asset/storyboard/script）；
    zone/phase/variant/reference 等结构类型服务端不校验，跳过。未声明
    的字段 zod 默认 strip 不报错，保持原样。幂等：str(0.45)="0.45" 再跑
    还是 "0.45"。
    """
    field_types = _load_schema_field_types()
    nodes = graph.get("nodes")
    if not isinstance(nodes, list):
        return graph
    for node in nodes:
        if not isinstance(node, dict):
            continue
        table = field_types.get(str(node.get("type") or ""))
        if not table:
            continue
        data = node.get("data")
        if not isinstance(data, dict):
            continue
        for k, v in list(data.items()):
            zt = table.get(k)
            if zt is None:
                continue
            coerced = _coerce_scalar_to_schema(v, zt)
            if coerced is not v and type(coerced) is not type(v):
                data[k] = coerced
    return graph


# Extracts the full phase prefix from a phase_id, preserving any trailing
# letter: p09b_shot_audit → "p09b", p10c_quality_audit → "p10c", p10_voice → "p10".
# Use this instead of phase_id[:3], which truncates p09b→p09 / p10c→p10.
_PHASE_PREFIX_RE = re.compile(r"^(p\d+[a-z]?)")

# 2026-08-25 (PRG-02): 承载真实工件槽的数字后缀相位不折叠。p11a5_preview_audio
# 若被 _PHASE_PREFIX_RE 折叠成 'p11a'，_PHASE_OUTPUT_MAP.get('p11a') 会漏掉
# p11a5 的全部四工件（ambient_stems/preview_mix_path/roughcut_path/
# roughcut_meta），画布零节点、kap DAG P11a.5 恒 pending（review F23）。
# 对照：p11a0 仍折叠（advisory micro-gate 不独立占 lane，A2 裁定不变）。
_PHASE_NO_FOLD = ("p11a5",)


def _phase_prefix(phase_id: str) -> str:
    """Return the full phase prefix of ``phase_id`` (e.g. ``"p09b"``).

    Falls back to ``""`` when ``phase_id`` is empty / None / unparseable.
    Mirrors the helper in ``canvas_graph.py`` so the two modules compute
    prefixes identically without crossing import boundaries.
    """
    pid = phase_id or ""
    for nf in _PHASE_NO_FOLD:
        if pid == nf or pid.startswith(nf + "_"):
            return nf
    m = _PHASE_PREFIX_RE.match(pid)
    return m.group(1) if m else ""


# Filesystem roots the episode workdir may live under. Hard-coding
# "/data/workspace/runs/" broke every other deployment (laptops, other
# servers). Override with KAIS_RUN_ROOTS=":sep:" — empty entries are
# discarded. Keep the canonical /data/workspace/runs first so matches
# prefer it when multiple roots hit.
_RUN_ROOTS: tuple[str, ...] = tuple(
    p for p in os.environ.get(
        "KAIS_RUN_ROOTS",
        "/data/workspace/runs:/home/kai/workspace/runs:/home/kai/runs",
    ).split(":") if p
)


# ── Canvas sync error log ──────────────────────────────────────
# Instead of swallowing sync errors silently, write them to a
# JSONL file so the operator can see exactly what failed and why.
# The file lives at {workdir}/.pipeline-assets/canvas-sync-errors.jsonl
# and is also surfaced via the phase-execution-log.

def _sync_error_log_path() -> str | None:
    """Find the canvas-sync-errors.jsonl path from env or workdir."""
    workdir = os.environ.get("KAIS_RUN_WORKDIR", "")
    if workdir and os.path.isdir(workdir):
        d = os.path.join(workdir, ".pipeline-assets")
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, "canvas-sync-errors.jsonl")
    return None


def _log_sync_error(
    phase_id: str,
    episode_id: str,
    error_type: str,
    detail: str,
    *,
    exc_info: Optional[BaseException] = None,
) -> None:
    """Write a structured sync error to JSONL + log ERROR.

    This replaces the old silent swallow-all. The episode still
    continues (degrade-tolerant), but the failure is now VISIBLE:
    - ERROR level log (was WARNING before — easy to miss)
    - Structured JSONL entry for programmatic inspection
    """
    entry = {
        "ts": time.time(),
        "episode_id": episode_id,
        "phase_id": phase_id,
        "error_type": error_type,
        "detail": detail,
    }
    if exc_info is not None:
        entry["exception"] = f"{type(exc_info).__name__}: {exc_info}"

    # ERROR level — this is a real failure, not a debug detail
    logger.error(
        "canvas sync FAILED: phase=%s episode=%s type=%s detail=%s",
        phase_id, episode_id, error_type, detail,
        exc_info=exc_info is not None,
    )

    # Write to JSONL
    path = _sync_error_log_path()
    if path:
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            # Last resort: if even the error log fails, at least we
            # have the ERROR log line above.
            pass


# ── Structured field mapping (NODE_SCHEMA alignment) ──────────
# Translates raw phase-result fields into the camelCase English-enum
# keys that the frontend StructuredFieldPanel expects (see constants.ts
# NODE_SCHEMA). Handles snake_case→camelCase rename, Chinese→English
# enum translation, and semantic derivation (role text → archetype).
#
# The mapping tables (ENUM_MAPS, ENUM_DEFAULTS, PHASE_FIELDS) are
# generated from /data/workspace/kais-aigc-platform/schema/pipeline-field-map.yaml
# by generate_mappings.py. Do NOT hand-edit those values — edit the YAML
# and re-run the generator.

# ── Occam's razor: fields to drop from canvas node data (2026-07-14) ──
# Each snake_case field here has a camelCase counterpart that the frontend
# actually reads (constants.ts:191-226 NODE_SCHEMA). Keeping both bloats
# JSON without informational value. Schema-required snake_case fields
# (shot_id, engine, duration_sec, resolution per canvasAssetSchema.ts:64-73)
# are NOT in this set — they stay.
_CANONICAL_DROP_FIELDS: frozenset[str] = frozenset({
    # video/shot snake_case duplicates (frontend reads camelCase via constants.ts)
    "camera_movement",    # -> cameraMovement
    "audio_cue",          # -> audioCue
    "ltx_prompt",         # -> ltxPrompt
    "axis_line",          # -> axisLine
    "murch_grade",        # -> murchGrade
    # script (P01 hook) snake_case duplicates
    "hook_type",          # -> hookType
    "hook_intensity",     # -> hookIntensity
    # asset (P04 character) snake_case duplicates
    "age_range",          # -> ageRange
    # Pure log noise — not creation-relevant, clutters node data
    "scene_ref_warning",  # P09 warning log, diagnostic only
    # Absolute FS path; filePath (OSS URL) is the canonical web-playable path
    "video_path",         # use filePath instead
})


def _translate_enum(raw_value: Any, mapping: dict[str, str], default: str) -> str:
    """Chinese enum value → English enum value via substring match."""
    if not raw_value:
        return default
    raw = str(raw_value)
    for cn, en in mapping.items():
        if cn in raw:
            return en
    return default


def _coerce_float(val: Any, default: float = 0.5) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _is_numeric_raw(raw: Any) -> bool:
    """True when ``raw`` is a real number (or numeric string).

    2026-08-19 数值守卫：``coerce_float_0_1`` 对非数值源返回默认 0.5 —
    p07 的 ``color`` 是描述串（"warm amber with..."），映射层会把伪造的
    0.5 写进 style_color，前端 0-1 数值条显示假数据。非数值源应跳过，
    让该字段保持缺席（面板该条为空）而非显示错值。
    """
    if isinstance(raw, bool):
        return False
    if isinstance(raw, (int, float)):
        return True
    if isinstance(raw, str):
        try:
            float(raw.strip())
            return True
        except ValueError:
            return False
    return False


# Keyword map for the ``derive_archetype`` transform. Lives here (not in
# the YAML) because it's a derivation heuristic, not a Chinese→English
# enum translation.
_ROLE_KEYWORD_MAP = {
    "主角": "protagonist", "男主": "protagonist", "女主": "protagonist",
    "第二主角": "deuteragonist", "副主角": "deuteragonist", "配角": "deuteragonist",
    "反派": "antagonist", "敌": "antagonist",
    "导师": "mentor", "师父": "mentor", "师傅": "mentor",
    "催化": "catalyst", "第三": "catalyst",
    "守护": "guardian", "伙伴": "sidekick", "跟班": "sidekick", "助手": "sidekick",
    "恋人": "love_interest", "爱人": "love_interest", "妻子": "love_interest",
    "丈夫": "love_interest", "情人": "love_interest",
    "旁白": "narrator", "叙述": "narrator",
}


def _derive_archetype(role_text: Any) -> str:
    if not role_text:
        return "protagonist"
    for kw, enum_val in _ROLE_KEYWORD_MAP.items():
        if kw in str(role_text):
            return enum_val
    return "protagonist"


def _derive_age_range(age_variants: Any) -> str:
    """age_variants: [{age: 25, ...}, ...] → ageRange enum."""
    if not isinstance(age_variants, list) or not age_variants:
        return "young_adult"
    ages: list[int] = []
    for av in age_variants:
        if isinstance(av, dict):
            a = av.get("age")
            if isinstance(a, (int, float)):
                ages.append(int(a))
        elif isinstance(a := av, (int, float)):
            ages.append(int(a))
    if not ages:
        return "young_adult"
    ages.sort()
    primary = ages[len(ages) // 2]
    if primary < 13:
        return "child"
    if primary < 20:
        return "teen"
    if primary < 35:
        return "young_adult"
    if primary < 60:
        return "middle_aged"
    return "elderly"


def _normalize_resolution(res_text: Any) -> str:
    if not res_text:
        return "720p"
    s = str(res_text).lower()
    if "x" in s:
        try:
            h = int(s.split("x")[1])
            if h >= 1080:
                return "1080p"
            if h >= 720:
                return "720p"
            if h >= 540:
                return "540p"
            if h >= 480:
                return "480p"
            return "360p"
        except (ValueError, IndexError):
            pass
    if "1080" in s or "2k" in s:
        return "1080p"
    if "720" in s:
        return "720p"
    if "480" in s:
        return "480p"
    return "720p"


def _normalize_engine(raw: Any) -> str:
    if not raw:
        return ""
    return str(raw).lower().replace(" ", "").replace("-", "").replace(".", "")


def _murch_numeric_to_string(raw: Any) -> str | None:
    """Translate a Murch-grade value (string keyword or 0-10 numeric) to
    the frontend enum: excellent | pass | weak | fail."""
    if not raw:
        return None
    s = str(raw).lower()
    if s in ("excellent", "pass", "weak", "fail"):
        return s
    try:
        score = float(raw)
    except (ValueError, TypeError):
        return None
    if score >= 7:
        return "excellent"
    if score >= 5:
        return "pass"
    if score >= 3:
        return "weak"
    return "fail"


def _hook_intensity(raw: Any) -> int | None:
    """Scale a 0-1 hook-strength float to a 1-5 integer."""
    if raw is None:
        return None
    try:
        return max(1, min(5, round(float(raw) * 5)))
    except (ValueError, TypeError):
        return None


def _get_nested(artifact: dict[str, Any], dotted_key: str) -> Any:
    """Resolve ``"style_vector.color"`` → ``artifact["style_vector"]["color"]``."""
    cur: Any = artifact
    for part in dotted_key.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def _apply_transform(name: str, raw: Any) -> Any:
    """Dispatch a YAML-declared transform by name."""
    if name == "to_string":
        return str(raw) if raw is not None else None
    if name == "hook_intensity":
        return _hook_intensity(raw)
    if name == "derive_archetype":
        return _derive_archetype(raw)
    if name == "derive_age_range":
        return _derive_age_range(raw)
    if name == "coerce_float_0_1":
        v = _coerce_float(raw)
        return v if 0 <= v <= 1 else None
    if name == "murch_numeric_to_string":
        return _murch_numeric_to_string(raw)
    logger.warning("canvas_sync: unknown transform %r — passing raw value", name)
    return raw


def _apply_schema_mappings(
    data: dict[str, Any],
    phase_prefix: str,
    artifact: dict[str, Any],
) -> None:
    """Mutate ``data`` in-place: add NODE_SCHEMA-compatible fields derived
    from raw artifact data, driven by the generated PHASE_FIELDS table.

    Each field in PHASE_FIELDS[phase_prefix] carries:
      - ``python_key``: source key (dotted path allowed, e.g. ``style_vector.color``)
      - ``canvas_key``: destination camelCase key
      - ``enum`` (optional): enum map name; if present, raw value is
        translated via substring match against ENUM_MAPS[enum].
      - ``transform`` (optional): transform name; if present, raw value
        is run through ``_apply_transform``.

    Phase-specific aliases (e.g. P10 reading from both ``audio_type`` and
    ``type``) are preserved by checking known fallback keys.
    """
    if _MAPPINGS is None:
        return  # Generated map missing — degrade-tolerant no-op.

    # Micro-gate phases (p09b, p10b, p10c) share their parent's field
    # mapping. _PHASE_TYPE_MAP assigns them different canvas_types, but
    # the structured-field derivation is inherited.
    lookup_prefix = phase_prefix
    if lookup_prefix in ("p09b",):
        lookup_prefix = "p09"
    elif lookup_prefix in ("p10b", "p10c"):
        lookup_prefix = "p10"

    fields = _MAPPINGS.PHASE_FIELDS.get(lookup_prefix) or {}
    if not fields:
        return

    for _field_name, fdef in fields.items():
        ckey = fdef.get("canvas_key")
        if not ckey or ckey in data:
            continue  # Already set by upstream passthrough.

        # Phase-specific source-key fallbacks (preserved from the
        # handwritten implementation).
        pkey = fdef.get("python_key", "")
        raw: Any = None
        if lookup_prefix == "p10" and pkey == "audio_type":
            raw = artifact.get("audio_type") or artifact.get("type")
        elif lookup_prefix == "p10" and pkey == "emotion":
            raw = artifact.get("emotion") or artifact.get("emotional_tag")
        elif lookup_prefix == "p10" and pkey == "speaker":
            sp = artifact.get("speaker") or artifact.get("character_name")
            raw = sp
        elif lookup_prefix == "p11" and pkey == "murch_grade":
            raw = artifact.get("murch_grade") or artifact.get("murch")
        elif lookup_prefix == "p01" and pkey == "hook_strength":
            raw = artifact.get("hook_strength") or artifact.get("hook_intensity")
        elif lookup_prefix in ("p01", "p02", "p03") and pkey == "duration_sec":
            raw = artifact.get("duration_sec") or artifact.get("total_duration")
        elif lookup_prefix == "p04" and pkey == "age_variants":
            av = artifact.get("age_variants") or artifact.get("ages")
            # Direct age_range string field also valid.
            if not av:
                ar = artifact.get("age_range")
                if ar in ("child", "teen", "young_adult", "middle_aged",
                          "elderly", "ageless"):
                    data[ckey] = ar
                    continue
            raw = av
        elif lookup_prefix == "p04" and pkey == "role":
            raw = artifact.get("role") or artifact.get("character_role")
        elif "." in pkey:
            raw = _get_nested(artifact, pkey)
        else:
            raw = artifact.get(pkey)

        # ── "Always set" fields with defaults (preserved behaviour) ──
        # These were unconditionally written in the handwritten code,
        # even when the source value was missing.
        if lookup_prefix in ("p10",) and ckey == "engine":
            data[ckey] = _normalize_engine(raw)
            continue
        if lookup_prefix == "p11" and ckey == "engine":
            # Defaults to "ltx" when source missing.
            raw_engine = raw if raw is not None else "ltx"
            data[ckey] = "ltx" if "ltx" in str(raw_engine).lower() else _normalize_engine(raw_engine)
            continue
        if lookup_prefix == "p11" and ckey == "resolution":
            data[ckey] = _normalize_resolution(raw)
            continue

        if raw is None or raw == "":
            continue

        # Transform first — handles English-keyword + numeric values
        # (e.g. murch_grade). When the transform returns None (e.g. it
        # cannot parse a Chinese string), fall through to enum translation.
        transform = fdef.get("transform")
        if transform == "coerce_float_0_1" and not _is_numeric_raw(raw):
            # 数值守卫（2026-08-19）：非数值源直接跳过 — 否则 coerce 的
            # 0.5 默认值会把描述串伪造成都市传说数值条假数据。
            continue
        if transform:
            v = _apply_transform(transform, raw)
            if v is not None:
                data[ckey] = v
                continue

        # Enum translation.
        enum_name = fdef.get("enum")
        if enum_name:
            mapping = _MAPPINGS.ENUM_MAPS.get(enum_name, {})
            default = _MAPPINGS.ENUM_DEFAULTS.get(enum_name, "")
            data[ckey] = _translate_enum(raw, mapping, default)
            continue

        # Default: passthrough as string (skip None and missing).
        if isinstance(raw, (dict, list)):
            # Don't stringify complex types — skip them.
            continue
        data[ckey] = str(raw) if not isinstance(raw, (int, float, bool)) else raw


# ── 缩略图压缩 (PIL + ffmpeg) ──────────────────────────────────
# 每个图片/视频资产生成两路径：
#   thumbnailUrl → 压缩 WebP（max 400px, q80, ~50KB）用于节点卡片
#   filePath     → 原图/原视频用于详情面板
# 节点卡片用 thumbnailUrl（快加载），详情面板用 filePath（全质量）。

_OSS_DIR = "/data/workspace/kais-aigc-platform/data/oss"
_THUMB_MAX_WIDTH = 400
_THUMB_QUALITY = 80
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff", ".tif"}
_VIDEO_EXTS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}
_AUDIO_EXTS = {".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a"}

# Pipeline-wide shared assets root. When a per-run asset file is missing on
# disk (e.g. a stale run dir that lost its P04 assets), ``_fs_to_oss_url``
# searches this tree for a same-named replacement so the canvas node still
# renders instead of 404'ing.
_SHARED_ASSETS_ROOT = "/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/assets"
# ``basename`` -> resolved replacement path (or ``None``). Memoized so we
# ``os.walk`` the shared tree at most once per distinct missing filename.
_FALLBACK_CACHE: dict[str, str | None] = {}


def _find_in_dir(root: str, filename: str) -> str | None:
    """Recursively search ``root`` for a file named ``filename``.

    Returns the first matching absolute path, or ``None`` when ``root`` is
    missing or no same-named file exists anywhere beneath it. Used by
    ``_fs_to_oss_url`` to recover a replacement asset from the pipeline
    shared assets tree when the referenced run file is gone.
    """
    if not os.path.isdir(root):
        return None
    for dirpath, _dirs, files in os.walk(root):
        if filename in files:
            return os.path.join(dirpath, filename)
    return None


def _flf_variant_of(path: str) -> str:
    """Extract the ``v{N}`` variant tag from an iframe file path.

    gen_iframes ``--variants N`` writes ``first_frame_v1.png`` / ``_v2`` /
    ``_v3``; ``--variants 1`` (default) writes plain ``first_frame.png``
    with no suffix — that lone frame is still variant ``v1`` for node-id
    purposes (``a-flf-{shot}-first-v1``), keeping ids stable across
    re-runs with different variant counts.
    """
    import re as _re
    m = _re.search(r"_v(\d+)\.(?:png|jpe?g|webp)$", path, _re.IGNORECASE)
    return f"v{m.group(1)}" if m else "v1"


def _faststart_copy(src: str, dst: str) -> None:
    """Copy ``src`` to ``dst`` remuxed with the ``moov`` atom first.

    2026-08-19: pipeline 视频产物（KAP/H3/ffmpeg concat）moov 全在文件尾，
    浏览器 ``<video>`` 拿不到索引无法流播——画布上表现为点不开/一直转。
    容器级 ``-c copy`` 重封装（秒级，不动编码）。幂等：dst 已是真实文件则跳过；
    dst 是旧 symlink 则重做（老同步留下的直通链接）。
    """
    if os.path.exists(dst) and not os.path.islink(dst):
        return
    import subprocess
    tmp = dst + ".fs.tmp.mp4"
    if os.path.exists(tmp) or os.path.islink(tmp):
        os.unlink(tmp)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", src, "-c", "copy",
         "-movflags", "+faststart", tmp],
        check=True, timeout=300,
    )
    os.replace(tmp, dst)


def _ffprobe_media_meta(fpath: str) -> dict[str, Any]:
    """ffprobe 提取 duration/resolution/codec（目录扫描路径的 Gate B 补齐）。

    2026-08-26：scan 兜底/并入只拿得到文件名，video/audio 节点缺
    shot_id/engine/duration_sec/resolution 会被 Gate B 降级成 script 文本卡
    （ep-zhongkui-v2-ep01 实锤：14 个 preview 节点全变 script）。这里补齐
    探测得出的字段；shot_id/engine 由调用方按文件名/未知填充。
    任何失败返回空 dict（调用方宁可降级也不要炸同步）。
    """
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-print_format", "json",
             "-show_format", "-show_streams", fpath],
            capture_output=True, text=True, timeout=30,
        )
        j = json.loads(out.stdout or "{}")
    except Exception:  # noqa: BLE001 — OSError / JSON / timeout 全容忍
        return {}
    meta: dict[str, Any] = {}
    try:
        streams = j.get("streams") or []
        video = next(
            (s for s in streams if s.get("codec_type") == "video"), None,
        )
        audio = next(
            (s for s in streams if s.get("codec_type") == "audio"), None,
        )
        src = video or audio
        if video and video.get("width") and video.get("height"):
            meta["resolution"] = f"{video['width']}x{video['height']}"
        dur = (j.get("format") or {}).get("duration") or (
            (src or {}).get("duration")
        )
        if dur is not None:
            meta["duration_sec"] = round(float(dur), 3)
        codec = (src or {}).get("codec_name")
        if codec:
            meta["codec"] = str(codec)
    except Exception:  # noqa: BLE001
        return meta
    return meta


def _fs_to_oss_url(fs_path: str) -> str | None:
    """Convert an absolute filesystem path to a ``/oss/`` URL.

    If the file lives outside ``_OSS_DIR``, create a symlink inside
    ``_OSS_DIR/pipeline/<episode_hash>/`` so the frontend can serve it.
    Returns ``None`` if the path is not a media file or conversion fails.
    """
    if not isinstance(fs_path, str) or not fs_path:
        return None
    ext = _media_ext(fs_path)
    if ext not in _IMAGE_EXTS and ext not in _VIDEO_EXTS and ext not in _AUDIO_EXTS:
        return None

    # Already inside OSS?
    try:
        rel = os.path.relpath(fs_path, _OSS_DIR)
        if not rel.startswith(".."):
            return f"/oss/{rel}"
    except ValueError:
        pass

    # File missing on disk — before emitting a placeholder URL, try to
    # recover a replacement from the pipeline shared assets tree so the
    # canvas node still renders. We keep the media type (asset/video/audio)
    # either way: a recovered file is symlinked like a normal file below;
    # if nothing is found we return a placeholder /oss/ path (frontend
    # shows a broken-image placeholder) and warn loudly.
    if not os.path.exists(fs_path):
        basename = os.path.basename(fs_path)
        if basename not in _FALLBACK_CACHE:
            _FALLBACK_CACHE[basename] = _find_in_dir(_SHARED_ASSETS_ROOT, basename)
        fallback_path = _FALLBACK_CACHE[basename]
        if fallback_path and os.path.exists(fallback_path):
            # Recovered a same-named replacement — fall through to the
            # symlink-creation block with the fallback as the source.
            fs_path = fallback_path
        else:
            import hashlib
            digest = hashlib.md5(os.path.dirname(fs_path).encode()).hexdigest()[:8]
            logger.warning(
                "canvas_sync: media file not found %r (oss hash=%s), "
                "no fallback in shared assets",
                fs_path,
                digest,
            )
            return f"/oss/pipeline/{digest}/{os.path.basename(fs_path)}"

    # Create symlink under _OSS_DIR/pipeline/
    import hashlib
    digest = hashlib.md5(os.path.dirname(fs_path).encode()).hexdigest()[:8]
    oss_subdir = os.path.join(_OSS_DIR, "pipeline", digest)
    os.makedirs(oss_subdir, exist_ok=True)
    filename = os.path.basename(fs_path)
    link_path = os.path.join(oss_subdir, filename)

    # 2026-08-19: mp4/mov 不再 symlink 直通——落 +faststart 真实副本（见
    # _faststart_copy 注释）。ffmpeg 失败回退 symlink（旧行为，宁可不能流播
    # 也不断图）。图片/音频维持 symlink（无 moov 问题）。
    if ext in (".mp4", ".mov") and os.path.isfile(fs_path):
        try:
            _faststart_copy(fs_path, link_path)
            return f"/oss/pipeline/{digest}/{filename}"
        except Exception:
            logger.warning(
                "canvas_sync: faststart remux failed for %r — symlink fallback",
                fs_path, exc_info=True,
            )

    # Create symlink if it doesn't exist (or is stale)
    if not os.path.exists(link_path):
        try:
            os.symlink(fs_path, link_path)
        except OSError:
            # Fallback: don't symlink, just return path relative to oss
            # This won't serve, but at least filePath is populated
            pass

    return f"/oss/pipeline/{digest}/{filename}"


def _normalize_media_fields(item: dict[str, Any], workdir: str = "") -> dict[str, Any]:
    """Map pipeline-internal field names to canvas-expected field names.

    Pipeline phases output media paths under various key names:
      - ``path``, ``audio_path`` → ``filePath``
      - ``views.front`` / ``views.side`` etc → ``thumbnailUrl`` (first available)
      - ``filePath`` / ``thumbnailUrl`` already present → pass through

    Also converts filesystem paths to ``/oss/`` URLs so the
    frontend can load them. Relative paths are resolved against
    ``workdir`` when provided.
    """
    # filePath: check explicit, then aliases
    if not item.get("filePath"):
        for alias in ("path", "audio_path", "file_path", "video_path", "clip_path",
                      "image_path", "turnaround_sheet"):
            val = item.get(alias)
            if val and isinstance(val, str):
                item["filePath"] = val
                break

    # storyboard 兜底：scene_ref（场景参考图）与嵌套 character_refs[].turnaround_path
    # 是分镜节点的画面来源，但用独立字段名未被上面 alias 覆盖（alias 表按 P07/P11 媒体
    # 产出的 path/video_path 命名写，没覆盖 P09 的 scene_ref 词汇）。仅当扩展名是已知
    # 媒体类型时才视作文件路径（避免把纯引用 token 当路径），让下面的相对→绝对、绝对
    # →/oss/ 两趟转换自动处理——与 video 的 video_path 走同一路径。
    if not item.get("filePath"):
        scene_ref = item.get("scene_ref")
        if isinstance(scene_ref, str):
            _ext = _media_ext(scene_ref)
            if _ext in _IMAGE_EXTS or _ext in _VIDEO_EXTS:
                item["filePath"] = scene_ref
        if not item.get("filePath"):
            char_refs = item.get("character_refs")
            if isinstance(char_refs, list):
                for _cr in char_refs:
                    if isinstance(_cr, dict):
                        _tp = _cr.get("turnaround_path")
                        if isinstance(_tp, str):
                            _ext = _media_ext(_tp)
                            if _ext in _IMAGE_EXTS or _ext in _VIDEO_EXTS:
                                item["filePath"] = _tp
                                break

    # thumbnailUrl: check explicit, then views/crops dict, then filePath
    if not item.get("thumbnailUrl"):
        for dict_key in ("views", "crops"):
            views = item.get(dict_key)
            if isinstance(views, dict):
                # Pick the first view that exists
                for view_key in ("front", "side", "side_left", "zoom", "top", "rear",
                                 "three_quarter", "back"):
                    vpath = views.get(view_key)
                    if vpath and isinstance(vpath, str):
                        item["thumbnailUrl"] = vpath
                        break
            if item.get("thumbnailUrl"):
                break

    # Resolve workdir: env KAIS_RUN_WORKDIR takes highest priority (A-3),
    # then the explicitly passed workdir argument.
    resolved_wd = os.environ.get("KAIS_RUN_WORKDIR", "")
    if not resolved_wd or not os.path.isdir(resolved_wd):
        resolved_wd = workdir

    # Resolve relative paths against workdir.
    # CRITICAL FIX (2026-07-11): Previously, when the file didn't exist
    # on disk (e.g. jimeng CLI generated a JSON reference but the image
    # wasn't downloaded yet), the path was left as a relative string.
    # This caused _build_artifact_node to see an empty filePath (because
    # the relative path never got converted to an /oss/ URL), which then
    # triggered the media→script type downgrade — losing all asset/video/
    # audio nodes from the canvas.
    #
    # Fix: Always resolve the relative path to absolute using workdir,
    # regardless of whether the file currently exists on disk. The OSS
    # URL conversion below will still produce a valid URL path even if
    # the file is missing (the frontend shows a placeholder). This is
    # strictly better than silently downgrading to script type.
    if resolved_wd:
        for key in ("filePath", "thumbnailUrl"):
            val = item.get(key)
            if val and isinstance(val, str) and not os.path.isabs(val):
                resolved = os.path.join(resolved_wd, val)
                # Always set the absolute path — even if file doesn't
                # exist yet. The _fs_to_oss_url call below will still
                # produce a valid /oss/ path for the frontend.
                item[key] = resolved

    # Convert absolute paths to /oss/ URLs
    for key in ("filePath", "thumbnailUrl"):
        val = item.get(key)
        if val and isinstance(val, str) and os.path.isabs(val):
            oss_url = _fs_to_oss_url(val)
            if oss_url:
                item[key] = oss_url

    # If filePath is a media /oss/ URL but no thumbnailUrl, set a
    # _thumbs placeholder. The _ensure_thumbnail pass (filesystem scan)
    # will generate the actual WebP via ffmpeg/sharp. Without this,
    # dict-output videos (e.g. P13 master_mp4) have no thumbnail and
    # the canvas frontend shows a blank card.
    fp = item.get("filePath")
    if fp and not item.get("thumbnailUrl") and _is_media_oss_url(fp):
        item["thumbnailUrl"] = _to_thumbnail_url(fp)

    # ── 辅助媒体字段 OSS 化（2026-08-19 审计修复 #5）─────────────────
    # turnaround_sheet / crops{} / views / path / audio_path 等次级路径字段
    # 此前只做穿透 — 画布节点 data 里保留裸 FS 绝对路径（/data/...），
    # 浏览器无法加载。与主 filePath 同规则：相对→绝对（against workdir）
    # → /oss/ URL。_fs_to_oss_url 对非媒体扩展名返回 None → 原值保留
    # （path 指向 manifest.json 之类的非媒体不受影响）。
    def _norm_path_val(val: Any) -> Any:
        if not isinstance(val, str) or not val:
            return val
        p = val
        if resolved_wd and not os.path.isabs(p):
            p = os.path.join(resolved_wd, p)
        if os.path.isabs(p):
            oss_url = _fs_to_oss_url(p)
            if oss_url:
                return oss_url
        return val

    for _pkey in ("turnaround_sheet", "turnaround_path", "path", "audio_path",
                  "ref_audio_path", "first_frame_path", "last_frame_path"):
        if _pkey in item:
            item[_pkey] = _norm_path_val(item[_pkey])
    for _dkey in ("crops", "views", "ref_images"):
        _dval = item.get(_dkey)
        if isinstance(_dval, dict):
            item[_dkey] = {k: _norm_path_val(v) for k, v in _dval.items()}
        elif isinstance(_dval, list):
            item[_dkey] = [
                _norm_path_val(v) if isinstance(v, str) else v for v in _dval
            ]
    _cr = item.get("character_refs")
    if isinstance(_cr, list):
        for _cr_item in _cr:
            if isinstance(_cr_item, dict) and "turnaround_path" in _cr_item:
                _cr_item["turnaround_path"] = _norm_path_val(
                    _cr_item["turnaround_path"]
                )

    return item


def _media_ext(path: str) -> str:
    """Lowercased extension including the dot, or ''."""
    _, ext = os.path.splitext(path)
    return ext.lower()


def _is_media_oss_url(url: str) -> bool:
    """True iff url is a /oss/ path pointing at an image/video (not _thumbs)."""
    if not isinstance(url, str) or not url.startswith("/oss/"):
        return False
    if "/_thumbs/" in url:
        return False
    ext = _media_ext(url)
    return ext in _IMAGE_EXTS or ext in _VIDEO_EXTS


def _to_thumbnail_url(source_url: str) -> str:
    """Map an /oss/ URL to its _thumbs WebP counterpart."""
    rel = source_url[len("/oss/"):]
    root, _ = os.path.splitext(rel)
    return f"/oss/_thumbs/{root}.webp"


def _oss_url_to_fs(oss_url: str) -> str:
    rel = oss_url[len("/oss/"):]
    return os.path.join(_OSS_DIR, rel)


def _is_newer(thumb_fs: str, src_fs: str) -> bool:
    try:
        return (
            os.path.exists(thumb_fs)
            and os.path.getsize(thumb_fs) > 0
            and os.path.getmtime(thumb_fs) >= os.path.getmtime(src_fs)
        )
    except OSError:
        return False


def _ensure_thumbnail(source_url: str) -> str:
    """Generate a compressed WebP thumbnail for an /oss/ media URL.

    Idempotent: returns the cached thumbnail if it exists and is newer than
    the source. Falls back to the original URL on any failure (never raises).

    Returns the thumbnailUrl (``/oss/_thumbs/...``) or the original URL if
    generation was skipped/failed.
    """
    if not _is_media_oss_url(source_url):
        return source_url

    src_fs = _oss_url_to_fs(source_url)
    if not os.path.exists(src_fs):
        return source_url  # source not present yet — try next sync

    thumb_url = _to_thumbnail_url(source_url)
    thumb_fs = _oss_url_to_fs(thumb_url)

    if _is_newer(thumb_fs, src_fs):
        return thumb_url  # cache hit

    os.makedirs(os.path.dirname(thumb_fs), exist_ok=True)
    ext = _media_ext(source_url)
    try:
        if ext in _IMAGE_EXTS:
            from PIL import Image
            # Pillow 10+ moved resampling constants under Image.Resampling;
            # fall back to the legacy Image.LANCZOS for older versions.
            try:
                resample = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
            except AttributeError:
                resample = Image.LANCZOS  # type: ignore[attr-defined]
            with Image.open(src_fs) as im:
                im = im.convert("RGB") if im.mode in ("RGBA", "P") else im
                w = _THUMB_MAX_WIDTH
                if im.width > w:
                    h = max(1, round(im.height * (w / im.width)))
                    im = im.resize((w, h), resample)
                im.save(thumb_fs, "WEBP", quality=_THUMB_QUALITY)
        elif ext in _VIDEO_EXTS:
            # ffmpeg: extract frame at ~1s (fallback 0s), scale to 400 wide.
            cmd = [
                "ffmpeg", "-y", "-ss", "1", "-i", src_fs,
                "-frames:v", "1", "-vf", "scale=400:-1",
                "-f", "webp", thumb_fs,
            ]
            try:
                subprocess.run(cmd, capture_output=True, timeout=30, check=True)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                # retry at t=0 for clips shorter than 1s
                cmd[3] = "0"
                subprocess.run(cmd, capture_output=True, timeout=30, check=True)
        else:
            return source_url
        return thumb_url
    except Exception as exc:  # noqa: BLE001 — degrade-tolerant
        logger.warning("thumbnail gen failed for %s: %s", source_url, exc)
        return source_url


class CanvasSyncSubscriber:
    """Subscriber that mirrors pipeline progress to the kais-aigc canvas.

    Python port of Node.js ``createCanvasSync()`` (canvas-sync-hook.js).
    One instance per episode — instance state (``_prev_phase_id``) tracks
    the previous phase for link drawing (PATTERN 6).

    Public methods (``on_phase_complete``, ``on_gate_resolved``) are
    degrade-tolerant: they log a WARNING on any failure and return
    without raising.
    """

    def __init__(self, canvas: CanvasClient, agent_name: str = ""):
        """
        Args:
            canvas: Phase 32 ``CanvasClient`` configured with
                project_id + episodes_id. HTTP I/O is delegated to it
                (CF-37-01: reused, not duplicated).
            agent_name: Optional label prefix (mirrors Node.js agentName).
        """
        self._client = canvas
        self._agent_name = agent_name
        # Tracks the previous phase id so consecutive phase nodes get
        # linked. Per-instance → safe for concurrent episodes.
        self._prev_phase_id: Optional[str] = None
        # Tracks child-node positions per parent phase for grid layout.
        self._child_counters: dict[str, int] = {}

    # ─── public trigger handlers ───────────────────────

    def on_phase_complete(
        self,
        episode_id: str,
        phase_id: str,
        result: dict[str, Any],
    ) -> Optional[bool]:
        """Phase-completion handler.

        Full pipeline-to-canvas mirror:
        1. Ensure zone (ellipse) node for this phase exists.
        2. Create sequential zone→zone chain links.
        3. Upsert phase summary node + link zone→summary.
        4. Extract artifact children from ``result.outputs`` and create
           child nodes (selected + unselected).
        5. Extract multi-choice candidates (variants/options).
        6. Extract gate/review outcome as a review node.
        7. Link previous phase → current phase.

        Degrade-tolerant — never raises. Returns ``False`` when the sync
        degraded at the network layer (load/save envelope — B-1/B-2),
        ``None`` otherwise (success / non-network degrade-tolerant paths),
        so ``sync_phase_result`` can honor its "returns False on any
        failure" contract. 4xx / validation errors still RE-RAISE.
        """
        try:
            loaded = self._client.load_canvas()
            # B-1: load 降级 envelope（网络瞬断 / 5xx 重试耗尽）必须拦截。
            # envelope 会被 normalize 成空图，随后 save 的 delete-absent 语义
            # 会把整个画布上先前所有 phase 的节点/边不可逆清空。网络类失败
            # 按 runner 分层约定不停管线（与下方 httpx 网络异常同语义：
            # _log_sync_error + return）。
            if isinstance(loaded, dict) and loaded.get("degraded"):
                _log_sync_error(
                    phase_id, episode_id,
                    error_type="CanvasLoadDegraded",
                    detail=(
                        f"on_phase_complete: load_canvas returned degrade "
                        f"envelope ({loaded.get('reason')}) — sync skipped to "
                        f"avoid wiping the canvas with an empty graph"
                    ),
                )
                return False
            graph = canvas_graph.normalize_loaded_graph(
                loaded, self._client._project_id, self._client._episodes_id
            )

            phase_prefix = _phase_prefix(phase_id)

            # ── 1. Ensure zone ellipse node ──────────────────────────
            if phase_prefix:
                canvas_graph.ensure_zone_node(graph, phase_prefix)
                # ── 2. Zone chain ────────────────────────────────────
                canvas_graph.ensure_zone_chain(graph)

            # ── 3. Phase summary node ────────────────────────────────
            node_data = self._build_phase_node(phase_id, result)
            canvas_graph.upsert_node(graph, f"n-{phase_id}", node_data)

            # Link zone → phase node.
            if phase_prefix:
                canvas_graph.ensure_zone_to_child(
                    graph, phase_prefix, f"n-{phase_id}",
                )

            # Link previous phase → current phase (pipeline flow).
            if self._prev_phase_id is not None:
                canvas_graph.ensure_link(
                    graph,
                    f"l-{self._prev_phase_id}-{phase_id}",
                    f"n-{self._prev_phase_id}",
                    f"n-{phase_id}",
                )

            # ── 4. Extract artifact children ────────────────────────
            # B-4: On retry, remove old artifact nodes for this phase so
            # stale/duplicate nodes from a previous run don't accumulate.
            # We identify this phase's artifact nodes as those linked from
            # n-{phase_id} via an "la-" link, whose id starts with "a-".
            # Also clean up the stale links referencing those nodes.
            _phase_node_id = f"n-{phase_id}"
            _old_art_ids: set[str] = set()
            for _l in graph.get("links", []):
                if (isinstance(_l, dict)
                        and isinstance(_l.get("source"), str)
                        and _l["source"] == _phase_node_id
                        and isinstance(_l.get("target"), str)
                        and _l["target"].startswith("a-")):
                    _old_art_ids.add(_l["target"])
            # 71-01 (v3.2 F05/COX-01,裁决点2a 画布为配方真值):删建前抢救
            # 用户画布编辑——旧节点 data.prompt ≠ data._kmc_prompt 即用户在
            # 52 PromptSection 改过配方,删建会静默蒸发(生产已发生)。抢救后
            # 在重建的同 id 节点上恢复用户 prompt(配方真值归画布),kmc 新值
            # 只进 _kmc_prompt 哨兵供下次判别。
            _user_prompt_edits: dict[str, str] = {}
            for _n in graph.get("nodes", []):
                if not (isinstance(_n, dict)
                        and isinstance(_n.get("id"), str)
                        and _n["id"] in _old_art_ids):
                    continue
                _nd = _n.get("data") if isinstance(_n.get("data"), dict) else {}
                _p, _kp = _nd.get("prompt"), _nd.get("_kmc_prompt")
                if (isinstance(_p, str) and _p
                        and isinstance(_kp, str) and _p != _kp):
                    _user_prompt_edits[_n["id"]] = _p
            if _old_art_ids:
                graph["nodes"] = [
                    n for n in graph.get("nodes", [])
                    if not (isinstance(n, dict)
                            and isinstance(n.get("id"), str)
                            and n["id"] in _old_art_ids)
                ]
                graph["links"] = [
                    l for l in graph.get("links", [])
                    if not (isinstance(l, dict) and (
                        l.get("source") in _old_art_ids
                        or l.get("target") in _old_art_ids
                    ))
                ]

            # Resolve workdir for relative path resolution
            workdir = ""
            # 1. Explicit env var (set by runner.py)
            env_wd = os.environ.get("KAIS_RUN_WORKDIR", "")
            if env_wd and os.path.isdir(env_wd):
                workdir = env_wd
            # 2. Try common patterns from episode_id across all configured
            # run roots (env-overridable via KAIS_RUN_ROOTS).
            if not workdir:
                import glob
                ep_glob = episode_id.replace("ep-", "").replace("-", "*")
                for root in _RUN_ROOTS:
                    pattern = f"{root}/*{ep_glob}*"
                    matches = glob.glob(pattern)
                    if matches:
                        workdir = matches[0]
                        break
            # 3. Extract from first absolute media path in result
            if not workdir:
                outputs = result.get("outputs", {})
                if isinstance(outputs, dict):
                    for v in outputs.values():
                        if isinstance(v, list):
                            for item in v:
                                if isinstance(item, dict):
                                    for pkey in ("path", "audio_path", "filePath"):
                                        pv = item.get(pkey, "")
                                        if isinstance(pv, str) and any(
                                            pv.startswith(r + "/") for r in _RUN_ROOTS
                                        ):
                                            workdir = pv.split("/assets/")[0]
                                            break
                                    if workdir:
                                        break
                            if workdir:
                                break
            artifacts = self._extract_artifacts(
                phase_id, result, workdir=workdir, episode_id=episode_id,
            )

            # storyboard_board o_assets 落库摘除 (2026-09-28 分镜板退役批,
            # 三视图审计 §3.3 ~/shared/2026-09-28/glm-three-views-audit.md):
            # _persist_storyboard_board 与其 p09c/p11a 触发条件同批移除 —
            # 唯一消费者 (StoryboardBoard 视图 + GET /api/v1/storyboard 路由)
            # 由 KAP 批A 删除。

            art_node_ids: list[tuple[str, dict[str, Any]]] = []  # For V4 reference links
            for art in artifacts:
                art_node_id = f"a-{art['id']}"
                art_node_ids.append((art_node_id, art))
                art_data = self._build_artifact_node(phase_id, art)

                # Auto-register reusable assets (character/scene) into the
                # global asset registry (o_assets) so they surface in the asset
                # manager.  This was previously only done in
                # sync_artifact_nodes() — the on_phase_complete path (used by
                # the runner's subscriber) bypassed registration entirely,
                # leaving o_assets empty even after a full pipeline run.
                # Idempotent by name+projectId; degrade-tolerant (returns
                # None on any failure — the canvas node is still synced).
                reg = self._register_pipeline_asset(art, art.get("type", "asset"))
                if reg:
                    if reg.get("uuid"):
                        art_data.setdefault("data", {})["uuid"] = reg["uuid"]
                    if reg.get("assetId"):
                        art_data.setdefault("data", {})["assetId"] = reg["assetId"]

                # Three-layer sync: register image-bearing assets (incl. keyframe,
                # which the assets-registry API enum excludes) into o_image +
                # o_assets so they surface in the asset manager. Degrade-tolerant.
                # 反向引用回填（2026-08-19 审计 #7）：直写路径此前不回填
                # uuid/assetId（只有 HTTP 注册路径回填）→ 线上 33 个资产
                # 节点仅 2 个带反向引用，画布↔资产中心无法互查。因此本调用
                # 安排在 upsert 之前，回填随 art_data 一并入图。
                reg3 = self._sync_asset_to_oassets_oimage(art, art_data)
                if reg3:
                    _nd = art_data.setdefault("data", {})
                    if reg3.get("uuid"):
                        _nd.setdefault("uuid", reg3["uuid"])
                    # 返回键是 o_assets_id（直写路径），画布侧字段名是 assetId
                    if reg3.get("o_assets_id"):
                        _nd.setdefault("assetId", reg3["o_assets_id"])

                canvas_graph.upsert_node(graph, art_node_id, art_data)
                # 71-01 后半:重建节点恢复用户画布编辑(同 id 抢救的 prompt
                # 优先于 kmc 新值;_kmc_prompt 保持 kmc 新值供下次判别)。
                if art_node_id in _user_prompt_edits:
                    _nd = next(
                        (n.get("data") for n in graph.get("nodes", [])
                         if isinstance(n, dict) and n.get("id") == art_node_id),
                        None,
                    )
                    if isinstance(_nd, dict):
                        _nd["prompt"] = _user_prompt_edits[art_node_id]
                # Link phase node → artifact.
                canvas_graph.ensure_link(
                    graph,
                    f"la-{phase_id}-{art['id']}",
                    f"n-{phase_id}",
                    art_node_id,
                )
                # Link zone → artifact (so every node has incoming).
                if phase_prefix:
                    canvas_graph.ensure_zone_to_child(
                        graph, phase_prefix, art_node_id,
                    )

            # ── 4b. Cross-phase reference links (V4) ────────────────
            self._add_reference_links(
                graph, phase_id, phase_prefix, art_node_ids, result,
            )

            # ── 4c. Asset-level reference links (2026-07-14) ─────────
            # Reads video assets' inline character_refs/scene_ref/audio_path
            # fields and draws reference edges to P04/P07/P10 sources. Catches
            # the ep-hamster-demolition case where _CROSS_PHASE_REF_KEYS
            # doesn't cover inline asset fields → 0 reference links drawn.
            self._link_asset_level_references(graph, art_node_ids)

            # ── 5. Extract multi-choice candidates ──────────────────
            candidates = self._extract_candidates(phase_id, result)
            # 落选候选兜底（问题3）：generation_config 冗余生成（P01 hook K=3、
            # P03 script K=3）产出的非 winner 候选不会进 result.outputs，只落盘
            # 到 .pipeline-assets/ 候选文件。从磁盘恢复，使落选候选也在画布渲染
            # （winner 由文件 chosen_variant_id 标记 selected）。
            candidates.extend(
                self._load_candidate_variants(phase_id, workdir)
            )
            for cand in candidates:
                canvas_graph.add_candidate_node(
                    graph,
                    phase_id=phase_id,
                    candidate_id=cand["id"],
                    label=cand["label"],
                    selected=cand.get("selected", False),
                    description=cand.get("description", ""),
                    thumbnail_url=cand.get("thumbnailUrl"),
                    file_path=cand.get("filePath"),
                    # 落选候选的结构化字段透传（2026-08-18）：variant 节点
                    # 详情靠穿透字段呈现 hook_type/visual_concept 等。
                    extra_data=cand.get("data"),
                )

            # ── 6. Extract gate/review result ───────────────────────
            gate = result.get("gate")
            if isinstance(gate, dict) and gate.get("gate_id"):
                canvas_graph.add_review_node(
                    graph,
                    phase_id=phase_id,
                    gate_id=gate["gate_id"],
                    decision=gate.get("decision", gate.get("action", "approve")),
                    note=gate.get("note", ""),
                )

            # Sanitize all node/branch fields to v2-valid values before save.
            # Schema-type coercion 先行：穿透字段的 number/string 必须对齐
            # save-v2 zod 表（p07 style_vector composition=0.45 → 400 修复）。
            _coerce_graph_schema_types(graph)
            canvas_graph.sanitize_v2_graph(graph)

            saved = self._client.save_canvas(graph)
            # B-2: save 降级 envelope（网络 / 5xx 重试耗尽）不抛异常——
            # 必须显式检查，否则 save 失败完全静默（无 error log、sync
            # 上层返回成功），唯一痕迹是 canvas.py 的一条 WARNING。
            # 网络类失败按 runner 分层约定不停管线：error log + return。
            if isinstance(saved, dict) and saved.get("degraded"):
                _log_sync_error(
                    phase_id, episode_id,
                    error_type="CanvasSaveDegraded",
                    detail=(
                        f"on_phase_complete: save_canvas returned degrade "
                        f"envelope ({saved.get('reason')}) — sync not "
                        f"persisted"
                    ),
                )
                return False
            # ── P2-2: post-sync 校验 — 把 fire-and-forget 变可校验 ─────
            # A: 节点计数断言（零成本，默认启用）。验证 graph 含本 phase
            #    的 summary 节点 + 全部 artifact 节点。
            self._assert_node_count(graph, art_node_ids, phase_id)
            # C: save-v2 round-trip 探针（env gate）。每次 save 多一次 load
            #    会增加延迟，故默认关闭；staging / 严格模式显式开启
            #    （KAIS_CANVAS_ROUNDTRIP=1）。
            if os.environ.get("KAIS_CANVAS_ROUNDTRIP", "0") == "1":
                self._roundtrip_probe(
                    phase_id,
                    saved_counts={
                        "nodes": len(graph.get("nodes", [])),
                        "links": len(graph.get("links", [])),
                    },
                )
            self._prev_phase_id = phase_id

            # ── AI Review Hook: extract scores → feedback API ──────
            try:
                from .ai_review_hook import extract_and_submit
                extract_and_submit(
                    phase_id=phase_id,
                    phase_result=result,
                    project_id=self._client._project_id,
                    base_url=self._client._base_url,
                )
            except Exception:  # noqa: BLE001 — hook must never block
                logger.debug(
                    "ai_review_hook degraded for %s",
                    phase_id,
                    exc_info=True,
                )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            # 网络层错误：canvas 不可达 → degrade-tolerant（不阻塞管线）
            _log_sync_error(
                phase_id, episode_id,
                error_type=type(exc).__name__,
                detail=str(exc),
                exc_info=exc,
            )
            return False
        except CanvasClientError as exc:
            # 4xx = 数据问题（graph 格式/内容不符合 canvas schema）。
            # P0-3: RE-RAISE per runner 契约（"同步失败就停，不掩盖问题"）。
            # A-2: 4xx 降级策略已废弃——让 CanvasClientError 传播到
            # runner._try_canvas_sync 的独占 re-raise，由其决定停管线。
            # 日志仍写以便 P15 追溯。
            _log_sync_error(
                phase_id, episode_id,
                error_type=f"CanvasClientError:{type(exc).__name__}",
                detail=f"phase_complete: {exc}",
                exc_info=exc,
            )
            raise
        except CanvasSyncValidationError as exc:
            # P2-2: post-sync 校验失败（节点计数 / round-trip 不符）→ RE-RAISE
            # 停管线。必须在此显式捕获并 re-raise：否则会被下面的
            # ``except Exception``（degrade-tolerant）吞掉，
            # CanvasSyncValidationError 永远传不到 runner._try_canvas_sync，
            # 校验形同虚设——与 P0-3 修复前同款的「runner re-raise 是死代码」。
            _log_sync_error(
                phase_id, episode_id,
                error_type=f"CanvasSyncValidationError:{type(exc).__name__}",
                detail=f"phase_complete: {exc}",
                exc_info=exc,
            )
            raise
        except Exception as exc:
            # 意料之外的错误：记录后继续，不阻塞管线。
            _log_sync_error(
                phase_id, episode_id,
                error_type=f"Unexpected:{type(exc).__name__}",
                detail=f"phase_complete: {exc}",
                exc_info=exc,
            )

    # ── P2-2: post-sync validators ────────────────────────────────

    def _assert_node_count(
        self,
        graph: dict[str, Any],
        art_node_ids: list[tuple[str, dict[str, Any]]],
        phase_id: str,
    ) -> None:
        """A: 节点计数断言 — save 后验证本 phase 的节点已落在 graph。

        expected = ``n-{phase_id}`` (phase summary) ∪ 每个 artifact 节点
        (``a-{id}``)。这些节点在 ``on_phase_complete`` 内由 ``upsert_node``
        刚刚创建，故正常路径恒通过。零成本（只扫本地 graph，无网络），默认启用。

        价值是结构不变量 tripwire：若未来 ``upsert_node`` / artifact 提取
        语义变化、或 ``save_canvas`` 异常地剥除节点，立即 fail-loud 而非
        静默放过（与 round-trip 探针 C 互补：A 抓本地构建错位，C 抓 server
        端 silent partial persist）。
        """
        expected_ids = {nid for nid, _ in art_node_ids}
        expected_ids.add(f"n-{phase_id}")
        actual_nodes = {
            node["id"]
            for node in graph.get("nodes", [])
            if isinstance(node, dict) and isinstance(node.get("id"), str)
        }
        missing = expected_ids - actual_nodes
        if missing:
            raise CanvasSyncValidationError(
                f"Post-sync node-count assertion failed for {phase_id}: "
                f"{len(missing)} expected node(s) missing from canvas: "
                f"{sorted(missing)[:5]}"
            )

    def _roundtrip_probe(
        self,
        phase_id: str,
        saved_counts: dict[str, int],
    ) -> None:
        """C: save-v2 round-trip 探针 — save 后立即 load → diff 节点/边数。

        验证 server 真正持久化了我们刚 save 的全部节点/边，抓 silent partial
        persist（save 返 2xx 但部分节点未落盘）。env-gated
        （``KAIS_CANVAS_ROUNDTRIP=1``）—— 每次 save 多一次 load 会增加延迟，
        故默认关闭，仅 staging / 严格模式显式开启。

        load 自身降级（degrade envelope = 网络瞬断 / 5xx）时 *跳过* 比较：网络
        错误是瞬时的，与 partial-persist 这种数据问题不同，不应误停管线。
        （真 4xx 会从 ``load_canvas`` 抛 ``CanvasClientError``，由 on_phase_complete
        的对应 except 处理。）
        """
        reloaded_raw = self._client.load_canvas()
        if isinstance(reloaded_raw, dict) and reloaded_raw.get("degraded"):
            logger.warning(
                "canvas round-trip probe skipped for %s: load degraded (%s)",
                phase_id, reloaded_raw.get("reason"),
            )
            return
        reloaded = canvas_graph.normalize_loaded_graph(
            reloaded_raw,
            self._client._project_id,
            self._client._episodes_id,
        )
        reloaded_nodes = len(reloaded.get("nodes", []))
        reloaded_links = len(reloaded.get("links", []))
        if (saved_counts.get("nodes") != reloaded_nodes
                or saved_counts.get("links") != reloaded_links):
            raise CanvasSyncValidationError(
                f"Round-trip probe failed for {phase_id}: saved "
                f"{saved_counts} vs reloaded nodes={reloaded_nodes} "
                f"links={reloaded_links} (silent partial persist suspected)"
            )

    def on_gate_resolved(
        self,
        episode_id: str,
        gate_id: str,
        decision: str,
        payload: dict[str, Any],
    ) -> None:
        """Gate-resolution handler.

        On ``decision == "approve"``: writes/updates a gate-resolution
        canvas node (``g-{gate_id}``) with ``reviewStatus=approved``.
        On reject/contest: marks the associated phase node as ``error``
        state so the canvas UI reflects the rejection.

        Degrade-tolerant — never raises.

        Args:
            episode_id: Episode identifier (for logging).
            gate_id: Gate identifier.
            decision: ``"approve"`` / ``"reject"`` / ``"contest"``.
            payload: Gate outcome payload. ``payload["phase_id"]`` (if
                present) identifies the phase node to mark on reject.
        """
        try:
            loaded = self._client.load_canvas()
            # B-1: load 降级 envelope 拦截（同 on_phase_complete）——空图
            # save 会不可逆清空画布。网络类失败不停管线：error log + return。
            if isinstance(loaded, dict) and loaded.get("degraded"):
                _log_sync_error(
                    gate_id, episode_id,
                    error_type="CanvasLoadDegraded",
                    detail=(
                        f"gate_resolved({decision}): load_canvas returned "
                        f"degrade envelope ({loaded.get('reason')}) — sync "
                        f"skipped to avoid wiping the canvas"
                    ),
                )
                return
            graph = canvas_graph.normalize_loaded_graph(
                loaded, self._client._project_id, self._client._episodes_id
            )

            if decision == "approve":
                node_data = self._build_gate_node(gate_id, payload, approved=True)
                canvas_graph.upsert_node(graph, f"g-{gate_id}", node_data)
            else:
                # reject / contest — mark the associated phase node error.
                phase_id = payload.get("phase_id") or gate_id
                # Read existing node tags and append "rejected" instead of
                # overwriting — preserves review/audit context tags (B-2).
                existing_node = next(
                    (n for n in graph.get("nodes", [])
                     if isinstance(n, dict) and n.get("id") == f"n-{phase_id}"),
                    None,
                )
                existing_tags: list[str] = []
                if existing_node and isinstance(existing_node.get("data"), dict):
                    et = existing_node["data"].get("tags")
                    if isinstance(et, list):
                        existing_tags = [str(t) for t in et]
                if "rejected" not in existing_tags:
                    existing_tags.append("rejected")
                canvas_graph.upsert_node(
                    graph,
                    f"n-{phase_id}",
                    {
                        "state": "error",
                        "data": {
                            "state": "error",
                            "tags": existing_tags,
                        },
                    },
                )

            # Sanitize all node/branch fields to v2-valid values before save
            # (prevents legacy type/state from causing HTTP 400 on save-v2).
            _coerce_graph_schema_types(graph)
            canvas_graph.sanitize_v2_graph(graph)

            self._client.save_canvas(graph)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            # 网络层错误：canvas 不可达 → degrade-tolerant
            _log_sync_error(
                gate_id, episode_id,
                error_type=type(exc).__name__,
                detail=f"gate_resolved({decision}): {exc}",
                exc_info=exc,
            )
        # CanvasClientError 和其他 Exception 不捕获 → 传播停管线

        # ── Mirror the gate decision into the Asset Feedback Layer ──
        # PATTERN (asset-feedback-layer): every gate resolution also
        # becomes a feedback entry on the phase node (``n-{phase_id}``)
        # so human and AI feedback share one timeline. Degrade-tolerant
        # — must never raise (CANVAS-IN-HERMES-03).
        try:
            from .feedback_client import FeedbackClient

            fb = FeedbackClient()
            phase_id = payload.get("phase_id") or gate_id
            fb.create_degraded(
                asset_id=f"n-{phase_id}",
                project_id=self._client._project_id,
                verdict=decision,  # approve / reject / contest
                content=payload.get("note") or f"Gate {gate_id}: {decision}",
                source="pipeline_self",
                reviewer=f"gate:{gate_id}",
                context={
                    "gate_id": gate_id,
                    "episode_id": episode_id,
                    "payload": payload,
                },
            )
        except Exception:  # noqa: BLE001 — feedback write must never block
            logger.debug(
                "feedback write degraded for gate %s (%s)",
                gate_id,
                decision,
                exc_info=True,
            )

    def sync_artifact_nodes(
        self,
        episode_id: str,
        phase_id: str,
        artifacts: list[dict[str, Any]],
    ) -> None:
        """Sync artifact files (images/videos/audio) as child canvas nodes.

        Each artifact becomes a child node (type=asset/video/audio) linked
        to the parent phase node (``n-{phase_id}``). The node carries
        ``thumbnailUrl`` and ``filePath`` so the frontend renders the media
        inline.

        This method is NOT auto-invoked by the runner — the orchestrating
        agent or a phase module must call it explicitly after generating
        artifacts (e.g. after P04 character images, P07 scene images,
        P11 video clips).

        Degrade-tolerant — never raises.

        Args:
            episode_id: Episode identifier (for logging).
            phase_id: Parent phase identifier (e.g. ``"p04_character_design"``).
            artifacts: List of artifact dicts. Each dict should have:
                - ``label`` (str, required): Display label.
                - ``type`` (str): "asset" | "video" | "audio" | "storyboard".
                  Defaults to "asset".
                - ``thumbnailUrl`` (str): WebP/PNG thumbnail path for display.
                - ``filePath`` (str): Full-res media path (must start with
                  ``/oss/`` or ``http`` for frontend detail panel).
                - ``assetType`` (str): "role" | "scene" | "clip" | etc.
                - ``id`` (str): Unique artifact id. If omitted, one is
                  generated from phase_id + index.
        """
        if not artifacts:
            return

        try:
            parent_node_id = f"n-{phase_id}"
            loaded = self._client.load_canvas()
            # B-1: load 降级 envelope 拦截（同 on_phase_complete）——空图
            # save 会不可逆清空画布。网络类失败不停管线：error log + return。
            if isinstance(loaded, dict) and loaded.get("degraded"):
                _log_sync_error(
                    phase_id, episode_id,
                    error_type="CanvasLoadDegraded",
                    detail=(
                        f"sync_artifact_nodes: load_canvas returned degrade "
                        f"envelope ({loaded.get('reason')}) — sync skipped "
                        f"to avoid wiping the canvas"
                    ),
                )
                return
            graph = canvas_graph.normalize_loaded_graph(
                loaded, self._client._project_id, self._client._episodes_id
            )

            # Ensure parent phase node exists.
            parent_exists = any(
                n.get("id") == parent_node_id
                for n in graph.get("nodes", [])
                if isinstance(n, dict)
            )
            if not parent_exists:
                logger.debug(
                    "sync_artifact_nodes: parent %s not found — "
                    "creating a minimal parent",
                    parent_node_id,
                )
                # Create a minimal parent so children have something to link to.
                phase_prefix = _phase_prefix(phase_id)
                ptype, _ = self._PHASE_TYPE_MAP.get(
                    phase_prefix, ("script", "script_phase")
                )
                pidx = self._PHASE_INDEX_MAP.get(phase_prefix, 0)
                parent_data = self._build_phase_node(phase_id, {})
                canvas_graph.upsert_node(graph, parent_node_id, parent_data)

            # Grid layout for children: 3 columns, 30px gap.
            phase_prefix = _phase_prefix(phase_id)
            parent_pidx = self._PHASE_INDEX_MAP.get(phase_prefix, 0)
            base_x = 100 + parent_pidx * 350 + 350  # right of parent lane
            base_y = 100

            for i, art in enumerate(artifacts):
                col = i % 3
                row = i // 3
                art_id = art.get("id") or f"{phase_id}-art-{i}"
                node_id = f"a-{art_id}"

                art_type = art.get("type", "asset")
                # Validate against v2 enum.
                if art_type not in ("asset", "video", "audio", "storyboard",
                                     "script", "reference"):
                    art_type = "asset"

                child_data: dict[str, Any] = {
                    "type": art_type,
                    "position": {
                        "x": base_x + col * 280,
                        "y": base_y + row * 300,
                    },
                    "size": {"width": 240, "height": 260},
                    "state": "success",
                    "branchId": "main",
                    "phaseIndex": parent_pidx,
                    "phaseName": art.get("label", art_id),
                    "data": {
                        "label": art.get("label", art_id),
                        "state": "success",
                        "assetType": art.get("assetType", ""),
                    },
                }
                # Conditionally write thumbnailUrl/filePath — canvas save-v2
                # rejects None-valued keys (HTTP 400).
                for _k in ("thumbnailUrl", "filePath"):
                    _v = art.get(_k)
                    if _v:
                        child_data["data"][_k] = _v

                # Copy optional fields.
                for opt_key in ("score", "reviewStatus", "duration", "prompt",
                                 "characterId", "viewAngle", "provenance"):
                    val = art.get(opt_key)
                    if val is not None:
                        child_data["data"][opt_key] = val

                # Auto-register reusable assets (character/scene) into the global
                # asset registry (o_assets) so they surface in the asset manager
                # without manual sync. Idempotent by name+projectId; writes the
                # returned uuid/assetId back onto the canvas node data. Degrade-
                # tolerant — returns None on any registry failure (canvas node is
                # still synced below; only the registry link is skipped).
                reg = self._register_pipeline_asset(art, art_type)
                if reg:
                    if reg.get("uuid"):
                        child_data["data"]["uuid"] = reg["uuid"]
                    if reg.get("assetId"):
                        child_data["data"]["assetId"] = reg["assetId"]

                # Three-layer sync: register image-bearing assets (incl. keyframe,
                # which the assets-registry API enum excludes) into o_image +
                # o_assets so they surface in the asset manager. Degrade-tolerant.
                # 反向引用回填（2026-08-19 审计 #7，同 on_phase_complete 路径）：
                # 安排在 upsert 之前，uuid/assetId 随 child_data 入图。
                reg3 = self._sync_asset_to_oassets_oimage(art, child_data)
                if reg3:
                    if reg3.get("uuid"):
                        child_data["data"].setdefault("uuid", reg3["uuid"])
                    # 返回键是 o_assets_id（直写路径），画布侧字段名是 assetId
                    if reg3.get("o_assets_id"):
                        child_data["data"].setdefault("assetId", reg3["o_assets_id"])

                canvas_graph.upsert_node(graph, node_id, child_data)

                # Link parent → child.
                link_id = f"l-{parent_node_id}-{node_id}"
                canvas_graph.ensure_link(graph, link_id, parent_node_id, node_id)

            # Sanitize before save.
            _coerce_graph_schema_types(graph)
            canvas_graph.sanitize_v2_graph(graph)
            self._client.save_canvas(graph)

            logger.info(
                "sync_artifact_nodes: %d artifacts synced for phase %s "
                "(episode=%s)",
                len(artifacts),
                phase_id,
                episode_id,
            )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            # 网络层错误：canvas 不可达 → degrade-tolerant
            _log_sync_error(
                phase_id, episode_id,
                error_type=f"sync_artifact_nodes:{type(exc).__name__}",
                detail=str(exc),
                exc_info=exc,
            )
        # CanvasClientError 和其他 Exception 不捕获 → 传播停管线

    # canvas-node assetType → registry (o_assets) type. Only reusable visual
    # assets are auto-registered; clips/generic props stay canvas-only for now.
    _REGISTRY_TYPE_MAP: dict[str, str] = {
        "character": "character",
        "role": "character",
        "scene": "scene",
    }

    def _register_pipeline_asset(
        self,
        art: dict[str, Any],
        art_type: str,
    ) -> dict[str, Any] | None:
        """Register a character/scene artifact into the global asset registry.

        Called from :meth:`sync_artifact_nodes` for each ``type=asset`` artifact
        whose ``assetType`` is character/role/scene. Idempotent — if an
        ``o_assets`` row with the same name+type+projectId exists, reuse its
        uuid/assetId instead of creating a duplicate. Degrade-tolerant: returns
        ``None`` on any registry failure (the canvas node is still synced; only
        the registry link is skipped).

        Args:
            art: Artifact dict (has ``label``/``assetType``/``prompt``/...).
            art_type: Canvas node type (``"asset"`` for registerable artifacts).

        Returns:
            ``{"uuid", "assetId"}`` on success or existing match, else ``None``.
        """
        if art_type != "asset":
            return None
        reg_type = self._REGISTRY_TYPE_MAP.get(art.get("assetType") or "")
        if not reg_type:
            return None
        project_id = self._client._project_id
        if project_id is None:
            return None

        name = art.get("label") or art.get("id") or "未命名资产"

        # Idempotency: reuse an existing registry asset with same name+type+project.
        found = self._client.raw_post(
            "/api/v1/assets-registry/search",
            {"projectId": project_id, "query": name, "limit": 20},
        )
        if isinstance(found, dict):
            for it in found.get("assets", []) or []:
                if it.get("name") == name and it.get("type") == reg_type:
                    if it.get("uuid"):
                        logger.debug(
                            "register_asset: reuse %s (%s) for %r",
                            it["uuid"], reg_type, name,
                        )
                        return {"uuid": it["uuid"], "assetId": it.get("id")}

        # Create a new registry asset. uuid is generated server-side.
        payload: dict[str, Any] = {
            "name": name,
            "type": reg_type,
            "projectId": project_id,
            "describe": art.get("describe") or name,
            "prompt": art.get("prompt") or "",
            "viewAngle": art.get("viewAngle"),
            "characterId": art.get("characterId"),
            "createdBy": "pipeline-sync",
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        created = self._client.raw_post("/api/v1/assets-registry", payload)
        if not isinstance(created, dict) or not created.get("uuid"):
            logger.warning(
                "register_asset: registry create failed for %r (type=%s)",
                name, reg_type,
            )
            return None
        logger.info(
            "register_asset: registered %r → %s (type=%s, id=%s)",
            name, created.get("uuid"), reg_type, created.get("id"),
        )
        return {"uuid": created.get("uuid"), "assetId": created.get("id")}

    # ── F-1 subtype 推导表（2026-08-16）────────────────────────────────
    # 值空间 = 前端 assetManagerData.ts AssetSubtype 联合类型的子集。
    # 判定顺序刻意与前端 inferSubtype 的语义一致但按「显式标记优先」：
    #   1. data 里已带显式 subtype / frame_type → 原样透传；
    #   2. turnaround_sheet 字段（P04 l1_anchors 携带）→ turnaround_sheet；
    #   3. viewAngle ∈ 拆分视角 → turnaround_view；
    #   4. l2 场景合身 / costume 标记 → costume 类；
    #   5. 按 o_assets type 归大类（voice/scene_base/keyframe_first/last…）。
    _TURNAROUND_VIEW_ANGLES = frozenset(
        {"front", "side", "back", "three_quarter"},
    )

    @classmethod
    def _infer_asset_subtype(
        cls,
        artifact: dict[str, Any],
        data: dict[str, Any],
        asset_type: str | None,
    ) -> str | None:
        """Derive the frontend ``meta.subtype`` from artifact / node data.

        Frontend consumption (assetManagerData.ts): ``parseMetaSubtype``
        short-circuits BEFORE every per-type branch, so a written subtype
        is authoritative for grouping (getGroupKey) and classification
        (inferSubtype). Unknown / underivable → ``None`` (meta written
        without a subtype — frontend falls back to its heuristic chain,
        exactly the pre-F-1 behavior).

        Keys read (in priority order):
          * explicit ``subtype`` / ``frame_type`` on the artifact or node
            data (downstream phases already stamping a subtype win);
          * ``turnaround_sheet`` (P04 l1_anchors carry the base-sheet path);
          * ``viewAngle`` in the four canonical turnaround view angles;
          * ``costume_set`` / a costume-ish filePath (l2 fittings and
            costume turnarounds);
          * the o_assets ``type`` column for the coarse buckets
            (voice / scene / keyframe), mirroring how the KAP manual
            scripts stamp their rows.
        """
        # 1. Explicit marker — pass through verbatim.
        for src in (artifact, data):
            explicit = src.get("subtype") or src.get("frame_type")
            if isinstance(explicit, str) and explicit.strip():
                return explicit.strip()

        # 2. P04 base turnaround sheet (l1_anchors carry turnaround_sheet).
        if artifact.get("turnaround_sheet") or data.get("turnaround_sheet"):
            return "turnaround_sheet"

        # 3. Turnaround split views (crops: front/side/back/three_quarter).
        va = artifact.get("viewAngle") or data.get("viewAngle")
        if isinstance(va, str) and va.lower() in cls._TURNAROUND_VIEW_ANGLES:
            return "turnaround_view"

        # 4. Costume fittings / costume turnarounds (P04 l2_* sublists —
        #    filePath like l2_amao_S1.png / costume_turnaround_*.png).
        fp = str(artifact.get("filePath") or data.get("filePath") or "")
        fp_l = fp.lower()
        if (
            artifact.get("costume_set") or data.get("costume_set")
            or "costume_turnaround" in fp_l or "costume-tr" in fp_l
        ):
            return "costume_turnaround"
        if "/l2_" in fp_l or fp_l.rsplit("/", 1)[-1].startswith("l2_"):
            return "costume_temporal_variant"

        # 5. Coarse buckets by the o_assets type column.
        if asset_type == "voice":
            # P04 声纹参考行（区别于 P10 TTS 片段——后者经三层同步时
            # meta 已带 shot_id，由步骤 1 之前的调用方路径覆盖或保持
            # 前端 tags 启发式）。
            return "voice_print"
        if asset_type in ("scene", "scene_image", "scene_variant"):
            return "scene_base"
        if asset_type == "keyframe":
            # keyframe 节点名/label 形如 S01_B01_first / _last（gen_iframes
            # 帧链路约定）；推断不出时返回 null 让前端按 name 兜底。
            name_l = str(
                artifact.get("label") or data.get("label")
                or artifact.get("id") or "",
            ).lower()
            if "last" in name_l or "tail" in name_l:
                return "keyframe_last"
            if "first" in name_l or "head" in name_l:
                return "keyframe_first"
            return None

        # character 概念图等其余类型：前端已有完整启发式链
        # （characterId+filePath+name 推 concept/bible），不越权标注。
        return None

    def _sync_asset_to_oassets_oimage(
        self,
        artifact: dict[str, Any],
        node_data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Sync an image-bearing asset artifact to ``o_image`` + ``o_assets``.

        Three-layer integrity: every ``canvas_nodes`` asset with a ``filePath``
        must also exist in ``o_image`` (image registry) and ``o_assets`` (asset
        registry, queried by AssetLibrary). The HTTP assets-registry API's
        ``type`` enum **excludes** ``keyframe`` — so iframe/keyframe assets (and
        any image asset whose type isn't in the enum) can only be registered via
        direct sqlite3. This method is that direct-DB path.

        Called after :meth:`_register_pipeline_asset` + ``upsert_node``. It
        complements the API path: if ``_register_pipeline_asset`` already
        created an ``o_assets`` row (character/scene, no image yet), this method
        reuses it by ``name+type+projectId`` and just attaches the image — no
        duplicate. For keyframe/other image types it creates both rows.

        Idempotent (``o_image`` by filePath, ``o_assets`` by imageId then
        name+type+projectId) and degrade-tolerant (returns ``None`` on any
        failure; the canvas node is still synced). Sets the
        ``o_image.assetsId`` back-reference.

        Args:
            artifact: Artifact dict (``label``/``assetType``/``filePath``/...).
                Also reads ``node_data["data"]`` as a fallback source.

        Returns:
            ``{"o_image_id", "o_assets_id", "uuid"?, "created": bool}`` or ``None``.
        """
        import sqlite3
        import time as _time
        import random as _random

        project_id = self._client._project_id
        if project_id is None:
            return None

        data = (node_data or {}).get("data") or {}
        # 源字段优先取 artifact，回退 node.data。
        file_path = (artifact.get("filePath") or data.get("filePath")
                     or artifact.get("thumbnailUrl") or data.get("thumbnailUrl"))
        if not file_path:
            return None  # 无图——交给 _register_pipeline_asset（HTTP 路径）
        # 规范化：剥离 ?v= 缓存破坏后缀（o_image 存的是干净路径）。
        file_path = str(file_path).strip()
        if "?" in file_path:
            file_path = file_path.split("?", 1)[0]
        asset_type = artifact.get("assetType") or data.get("assetType")
        if not asset_type:
            return None

        db_path = _locate_canvas_db()
        if db_path is None:
            logger.debug("sync_oassets_oimage: db2.sqlite not found — skip")
            return None

        name = artifact.get("label") or data.get("label") or artifact.get("id") or "未命名资产"
        prompt = (artifact.get("generation_prompt") or data.get("generation_prompt")
                  or artifact.get("prompt") or data.get("prompt") or "")
        is_primary = artifact.get("isPrimaryView")
        if is_primary is None:
            is_primary = data.get("isPrimaryView")
        is_primary_int = 1 if is_primary else 0
        curation = artifact.get("curationState") or data.get("curationState")
        # curationState → o_assets.state：eliminated/archived 显式映射，其余 active。
        if curation in ("eliminated", "archived"):
            state = curation
        else:
            state = "active"
        character_id = artifact.get("characterId") or data.get("characterId")
        view_angle = artifact.get("viewAngle") or data.get("viewAngle")
        tags = artifact.get("tags") or data.get("tags")
        tags_str = json.dumps(tags, ensure_ascii=False) if isinstance(tags, (list, dict)) else (tags or None)
        provenance = artifact.get("provenance") or data.get("provenance")
        episodes_id = self._client._episodes_id
        meta_obj: dict[str, Any] = {}
        for k in ("shot_id", "frame_type", "variant", "groupKey", "provenance", "thumbnailUrl"):
            v = artifact.get(k) or data.get(k)
            if v is not None:
                meta_obj[k] = v
        # ── F-1 subtype 生产者（2026-08-16）────────────────────────────
        # 前端 assetManager 的 getGroupKey / inferSubtype 都先读
        # ``meta.subtype``（assetManagerData.ts parseMetaSubtype 短路在
        # 所有按 type 分支之前）——但 KMC 自动链路此前从不写它（审计
        # F-1：o_assets 由 canvas-sync 写的行 subtype 全空，角色资产塌缩
        # 进 concept 大组）。这里从 artifact/node data 推导 subtype，值
        # 空间对齐前端 AssetSubtype 联合类型与 KAP 手工脚本
        # （register_turnaround_b2.py 写 "turnaround_sheet"）。仅在能推导
        # 出时写入——已有 meta.subtype（历史行 / 别的路径）绝不覆盖
        # （UPDATE 用 COALESCE(?,meta)，meta 整体 NULL 才生效）。
        _subtype = self._infer_asset_subtype(artifact, data, asset_type)
        if _subtype:
            meta_obj.setdefault("subtype", _subtype)
        meta_str = json.dumps(meta_obj, ensure_ascii=False) if meta_obj else None
        now_ms = int(_time.time() * 1000)

        try:
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA busy_timeout=10000")
            conn.execute("BEGIN IMMEDIATE")
            created = False
            try:
                # ── o_image：按 filePath upsert ──
                row = conn.execute(
                    "SELECT id FROM o_image WHERE filePath=?", (file_path,)
                ).fetchone()
                if row:
                    o_image_id = row[0]
                    conn.execute(
                        "UPDATE o_image SET type=COALESCE(NULLIF(type,''),?), state='success' WHERE id=?",
                        (asset_type, o_image_id),
                    )
                else:
                    cur = conn.execute(
                        """INSERT INTO o_image (filePath, type, state)
                           VALUES (?, ?, 'success')""",
                        (file_path, asset_type),
                    )
                    o_image_id = cur.lastrowid

                # ── o_assets：先按 imageId，再按 name+type+projectId 找 ──
                arow = conn.execute(
                    "SELECT id, uuid FROM o_assets WHERE imageId=? AND projectId=?",
                    (o_image_id, project_id),
                ).fetchone()
                if arow is None:
                    arow = conn.execute(
                        "SELECT id, uuid FROM o_assets WHERE name=? AND type=? AND projectId=?",
                        (name, asset_type, project_id),
                    ).fetchone()
                    # ── 2026-08-26 名字撞行防护 ──────────────────────────
                    # name+type 命中的行若已挂着「别的文件」（imageId ≠ 当前
                    # o_image），说明是同名不同资产（preview 与 final 同 shot
                    # 名、目录扫描空格名跨 phase 撞名），不能劫持改挂——否则
                    # 先到的文件被夺走 o_assets 行变孤儿，o_image JOIN 断链，
                    # 资产管理中心缺条目（ep-zhongkui-v2-ep01 实锤：p11a
                    # preview 行被 p11b final 扫描劫持）。置 None 走 INSERT
                    # 新行。仅 imageId 为空/0 的 HTTP 预建行可复用（原语义）。
                    if arow is not None:
                        _xi = conn.execute(
                            "SELECT imageId FROM o_assets WHERE id=?",
                            (arow[0],),
                        ).fetchone()
                        _xiv = _xi[0] if _xi else None
                        if _xiv not in (None, 0, "", o_image_id):
                            arow = None
                if arow:
                    o_assets_id = arow[0]
                    uuid_val = arow[1]
                    # ── name/type 刷新（2026-08-19）────────────────────────
                    # pipeline 自有行（createdBy='canvas-sync'）跟随源头标签/
                    # 类型演进——p04 首考发现两处陈旧：服装行名
                    # 「角色资产.scene_costume_turnarounds 1」（标签合成修复
                    # 后应为「xiaozhou·chashuijian_S1-S5」）和道具行
                    # type=character（assetType 修复后应为 prop）。用户手工
                    # 改过名的行（createdBy ≠ canvas-sync）绝不覆盖。
                    conn.execute(
                        """UPDATE o_assets SET
                             name=CASE WHEN createdBy='canvas-sync' THEN ?
                                       ELSE name END,
                             type=CASE WHEN createdBy='canvas-sync' THEN ?
                                       ELSE type END,
                             imageId=?, prompt=COALESCE(NULLIF(?,''),prompt),
                             isPrimaryView=?, state=?, characterId=COALESCE(?,characterId),
                             viewAngle=COALESCE(?,viewAngle), tags=COALESCE(?,tags),
                             meta=COALESCE(?,meta), episodesId=COALESCE(?,episodesId)
                           WHERE id=?""",
                        (name, asset_type, o_image_id, prompt, is_primary_int, state,
                         character_id, view_angle, tags_str, meta_str, episodes_id,
                         o_assets_id),
                    )
                else:
                    uuid_val = f"ast-{now_ms:x}-{_random.random().hex()[2:8]}"
                    cur = conn.execute(
                        """INSERT INTO o_assets
                             (name, prompt, type, imageId, projectId, characterId,
                              viewAngle, isPrimaryView, tags, state, meta, uuid,
                              createdAt, createdBy, episodesId)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (name, prompt, asset_type, o_image_id, project_id, character_id,
                         view_angle, is_primary_int, tags_str, state, meta_str, uuid_val,
                         now_ms, "canvas-sync", episodes_id),
                    )
                    o_assets_id = cur.lastrowid
                    created = True

                # ── o_image.assetsId 反向引用回填 ──
                conn.execute(
                    "UPDATE o_image SET assetsId=? WHERE id=? AND (assetsId IS NULL OR assetsId='' OR assetsId=0)",
                    (o_assets_id, o_image_id),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        except Exception as exc:  # noqa: BLE001 — degrade-tolerant
            logger.debug("sync_oassets_oimage: failed for %r — %s", name, exc, exc_info=True)
            return None

        logger.info(
            "sync_oassets_oimage: %r → o_image=%s o_assets=%s (type=%s, created=%s)",
            name, o_image_id, o_assets_id, asset_type, created,
        )
        return {"o_image_id": o_image_id, "o_assets_id": o_assets_id,
                "uuid": uuid_val, "created": created}

    # ─── private node builders ─────────────────────────

    # Phase index lookup (maps phase_id prefix to V8.6 step number).
    # Used to populate the Canvas API v2 required `phaseIndex` field.
    #
    # W6: every phase gets a UNIQUE phaseIndex. The micro-gates (p09b/p10b/p10c)
    # previously shared their parent's index (p09b=9; p10b/p10c=10), leaning on
    # depends_on for ordering — but the frontend sorts by phaseIndex alone, so
    # ties were unstable and p10b/p10c artifact grids overlapped (base_x at
    # L1260 is `100 + parent_pidx * 350`, identical for equal indices). Integer
    # phaseIndex can't express "between", so the order follows
    # canvas_graph.ZONE_PHASES (p09 < p09b < p10 < p10c < p10b < p11 …) and the
    # majors after the first micro-gate shift up by the micro-gates inserted
    # before them. compute_zone_position falls back for unknown indices, so this
    # only re-spaces the layout — it does not break it.
    _PHASE_INDEX_MAP: dict[str, int] = {
        "p01": 1, "p02": 2, "p03": 3, "p04": 4, "p05": 5,
        "p06": 6, "p07": 7, "p08": 8, "p09": 9,
        # P03.5 86ke 戏剧事件打磨 — shares the p03 lane (integer phaseIndex
        # can't express "between"; same convention as p09b/p11a/p12a).
        "p035": 3,
        # ICA M2 (2026-08-25): p036 钩子再实例化 — shares the p03 lane
        # （integer phaseIndex 无法表达"之间"，与 p035 同 lane，ZONE_PHASES
        # 顺序决定 lane 内布局）。
        "p036": 3,
        "p09b": 10,  # micro-gate between p09 and p10
        "p09c": 10,  # white-model storyboard sub-step (shares p09 lane)
        "p10": 11,
        "p10c": 12,  # micro-gate between p10 and p10b (语音审计)
        "p10b": 13,  # between p10c and p11 (快速预览)
        "p11": 14, "p12": 15, "p13": 16,
        "p11a": 14,  # preview-clips sub-step (shares p11 lane)
        # P11a.5 预演音频+成片 (2026-08-24 a046d47) — shares p11 lane with
        # p11a/p11b/p11c (integer phaseIndex can't express "between").
        # _PHASE_NO_FOLD 保证前缀不折叠（见 _phase_prefix）。
        "p11a5": 14,
        "p11b": 14,  # final-render sub-step (shares p11 lane)
        # P11c 视频智能质检 (qwen-eye, 2026-08-15) — shares the p11 lane
        # (integer phaseIndex can't express "between"; same convention as
        # p11a/p11b). ZONE_PHASES 顺序 (p11b < p11c < p12a) 决定 lane 内布局。
        "p11c": 14,
        # P12 split (2026-08-09): p12_composition → p12a (timeline EDL) +
        # p12b (audio synthesis). Both share the P12 lane (integer
        # phaseIndex can't express "between" — same as p11a/p11b).
        "p12a": 15,  # timeline-EDL sub-step (shares p12 lane)
        "p12b": 15,  # audio-synthesis sub-step (shares p12 lane)
        "p14": 17,
        "p15": 18,
    }

    # Phase → canvas node type + asset type mapping.
    # canvas_type must be one of the React Flow nodeTypes registered in
    # FlowCanvas.tsx: default | script | asset | storyboard | video | audio | zone.
    # asset_type aligns with the kais-aigc-platform frontend expectation:
    # role | scene | prop | clip | voice | video | storyboard | script_phase | outline | topic | delivery.
    _PHASE_TYPE_MAP: dict[str, tuple[str, str]] = {
        "p01": ("script", "topic"),
        "p02": ("script", "outline"),
        "p03": ("script", "script_phase"),
        # P03.5 86ke 打磨 — script 产出（打磨后剧本 + 报告），script_phase 一致。
        "p035": ("script", "script_phase"),
        # ICA M2 (2026-08-25): p036 钩子再实例化 — script 产出（hook-spec），
        # script_phase 类型（与 p03/p035 同 lane）。
        "p036": ("script", "script_phase"),
        "p04": ("asset", "character"),
        "p05": ("script", "script_phase"),
        "p06": ("script", "script_phase"),
        "p07": ("asset", "scene"),
        "p08": ("asset", "scene"),
        "p09": ("storyboard", "storyboard"),
        # 分镜审计微门 —— 它是「审计报告」而非「分镜」：产出的是对 P09
        # 分镜的审计意见（findings），不是分镜本身。若保留 storyboard 类型，
        # _build_artifact_node 会把 P09b 节点建成 storyboard，与 P09 的分镜
        # 节点混淆。改为 script 类型，与 p03/p14 等审计阶段一致。
        "p09b": ("script", "script_phase"),
        # P09c 分镜故事板（clay maquette storyboard board）—— 产出分镜板
        # dict（scenes/shots/stats）+ storyboard_sheets 图片。与 P09b 审计报告
        # 不同：P09c 是真正的分镜视觉产出，故用 storyboard 类型（此前缺映射
        # → 回落 script → 分镜板/分镜图全丢，画布分镜板为空）。
        "p09c": ("storyboard", "storyboard"),
        "p10": ("audio", "voice"),
        "p10b": ("video", "clip"),
        "p10c": ("audio", "voice"),  # voice audit micro-gate
        "p11": ("video", "video"),
        # P11a 预览片段 / P11b 最终渲染 —— 二者都产出视频 artifact（rapid_
        # preview_clips / video_clips）。此前 p11a/p11b 不在 _PHASE_TYPE_MAP，
        # _phase_prefix 把它们解析成 "p11a"/"p11b"（非 "p11"），回落 script →
        # 时间轴所需的视频 a-* 节点从不生成（时间轴为空）。
        "p11a": ("video", "video"),
        # P11a.5 预演音频+成片 — 核心交付 roughcut mp4（video 类型与 p11a/p11b
        # 一致）；ambient_stems/preview_mix 等音频工件经 _PHASE_OUTPUT_MAP
        # per-output 类型覆盖为 audio。
        "p11a5": ("video", "video"),
        "p11b": ("video", "video"),
        # P11c 视频智能质检 — 产出 video-qc dict（per_shot 判定 + summary）。
        # 审计报告非媒体，与 p09b/p10c/p14 审计微门一致用 script 类型。
        "p11c": ("script", "script_phase"),
        "p12": ("video", "clip"),
        # P12 split (2026-08-09): p12a 产 master_timeline dict（EDL，script
        # 类型与旧 p12 master_timeline 条目一致）；p12b 产 audio_stems
        # （bgm/sfx/voice/mix 音轨，audio 类型）。此前两前缀缺映射 → P12
        # 阶段产物在画布上整体静默消失（A-1 回归）。
        "p12a": ("script", "clip"),
        "p12b": ("audio", "voice"),
        "p13": ("script", "delivery"),
        "p14": ("script", "script_phase"),  # post-delivery quality audit
        # P15 跨集反思 —— p15_feedback.py 产出 feedback-log（跨集反思 dict，
        # 含 rejected_phases / rejection_events / lesson_count）。canvas_type
        # 用 script：反思报告非媒体，且 script 的 save-v2 必填仅需
        # label+description，零 400 风险。assetType "feedback" 为自定义 label。
        "p15": ("script", "feedback"),
    }

    # Human-readable phase labels (maps phase_id prefix → Chinese label).
    _PHASE_LABELS: dict[str, str] = {
        "p01": "Step 1 · 爆款选题+钩子",
        "p02": "Step 2 · 故事框架+大纲",
        "p03": "Step 3 · 剧本+审计",
        "p035": "Step 3.5 · 戏剧事件打磨",
        # ICA M2 (2026-08-25): p036 钩子再实例化 — C4b 派生失效协议
        "p036": "Step 3.6 · 钩子再实例化",
        "p04": "Step 4 · 角色设计",
        "p05": "Step 5 · 痛点发现",
        "p06": "Step 6 · 运镜+终审",
        "p07": "Step 7 · 视觉+风格化",
        "p08": "Step 8 · 场景选择",
        "p09": "Step 9 · 分镜拆解",
        "p09b": "Step 9.5 · 分镜审计",
        "p09c": "Step 9.6 · 分镜故事板",
        "p10": "Step 10 · 语音生成",
        "p10b": "Step 10.5 · 快速预览",
        "p10c": "Step 10.4 · 语音审计",
        "p11": "Step 11 · 视频渲染",
        "p11a": "Step 11.1 · 预览片段",
        "p11a5": "Step 11.15 · 预演音频+成片",
        "p11b": "Step 11.2 · 最终渲染",
        "p11c": "Step 11.3 · 视频质检",
        "p12": "Step 12 · 音视频合成",
        "p12a": "Step 12.1 · 时间线合成",
        "p12b": "Step 12.2 · 音频合成",
        "p13": "Step 13 · 交付",
        "p14": "Step 14 · 质量审计",
        "p15": "Step 15 · 跨集反思",
    }

    def _build_phase_node(
        self,
        phase_id: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Translate ``phase_id`` + ``result`` into canvas ``node_data``.

        The V8.6 runner calls ``on_phase_complete(episode_id, phase_id, result)``
        where ``result`` has the shape::

            {"phase": "p04_character_design", "outputs": {...}, "gate": dict|None}

        ``outputs`` is the parsed JSON the expert emitted (varies per phase —
        e.g. p01 has ``topic_kernel`` / ``hook_design``, p04 has
        ``character_bible`` / ``character_assets``, p11 has ``video_clips``, etc.).
        This method extracts a human-readable description, a score (if
        available), and the review status from that shape.

        Args:
            phase_id: Phase identifier (e.g. ``"p01_hook_topic"``).
            result: Phase result dict ``{"phase", "outputs", "gate"}``.

        Returns:
            ``node_data`` dict ready for ``canvas_graph.upsert_node``.
        """
        outputs = result.get("outputs") or {}
        if not isinstance(outputs, dict):
            outputs = {}
        gate = result.get("gate")
        # Gate is None for non-gated phases, or a dict like
        # {"action": "awaiting_review"} / {"gate_id": ..., "status": ...}.
        gate_awaiting = (
            isinstance(gate, dict)
            and (gate.get("action") == "awaiting_review"
                 or gate.get("status") == "awaiting_review")
        )
        # Error result (runner.py exception-handler paths: delegate timeout,
        # parse failure, schema validation). When present, the phase failed
        # — surface as an error-state node so operators can see WHICH phase
        # broke on the canvas (rather than a misleading "success" node).
        error_info = result.get("error")
        if not isinstance(error_info, dict):
            error_info = None

        stage = _infer_stage(phase_id)
        phase_prefix = _phase_prefix(phase_id)
        phase_index = self._PHASE_INDEX_MAP.get(phase_prefix, 0)
        canvas_type, asset_type = self._PHASE_TYPE_MAP.get(
            phase_prefix, ("script", "script_phase")
        )

        mapped = canvas_graph.default_phase_mapper({
            "id": phase_id,
            "name": phase_id,
            "stage": stage,
            "stage_order": phase_index,
            "review": gate_awaiting,
        })
        phase_group = mapped["phase"] or "production"
        # Use zone lane coordinates so the phase summary node aligns
        # directly under its zone ellipse (same x column).
        position = canvas_graph.compute_zone_position(phase_prefix)
        position = {"x": position["x"] + 150, "y": position["y"] + 100}

        # ── Build description from actual outputs dict ──────────────
        desc_parts: list[str] = []

        # Extract top-level scalar fields that many phases share.
        for key in ("title", "name", "selectedTopic", "topic", "logline",
                     "synopsis", "description"):
            val = outputs.get(key)
            if val and isinstance(val, str):
                desc_parts.append(val[:200])
                break

        # Count list/dict artifacts to show what was produced.
        artifact_counts: list[str] = []
        for key, val in outputs.items():
            if isinstance(val, list) and val:
                artifact_counts.append(f"{key}: {len(val)}")
            elif isinstance(val, dict):
                # Count nested items (e.g. character_bible.characters)
                for sub_key in ("characters", "shots", "clips", "tracks",
                                "scenes", "variants", "stems"):
                    sub_val = val.get(sub_key)
                    if isinstance(sub_val, list) and sub_val:
                        artifact_counts.append(f"{key}.{sub_key}: {len(sub_val)}")

        if artifact_counts:
            desc_parts.append("产物: " + ", ".join(artifact_counts[:5]))

        # Extract score if present (phases like p03 audit, p05 pain).
        # P03 audit-report emits total_score (not score/overall_score), so we
        # check that key too — without it the phase head node shows no score
        # even though the audit clearly scored the script.
        score = outputs.get("score") or outputs.get("overall_score")
        if score is None:
            # Check nested dicts for score fields. Keys are checked in
            # priority order: score → overall_score → total_score.
            for val in outputs.values():
                if isinstance(val, dict):
                    score = (
                        val.get("score")
                        or val.get("overall_score")
                        or val.get("total_score")
                    )
                    if score is not None:
                        break
        if score is not None:
            desc_parts.append(f"评分: {score}")

        if gate_awaiting:
            desc_parts.append("⏳ 等待审核")
        # Surface error info at the top of the description so it's visible
        # in the canvas detail panel. error_info shape (from runner.py):
        # {"type": "delegate_timeout"|"delegate_parse_failure"|
        #          "schema_validation", "message": str}
        if error_info is not None:
            err_type = error_info.get("type") or "error"
            err_msg = error_info.get("message") or ""
            tag = {
                "delegate_timeout": "⏱ 委派超时",
                "delegate_parse_failure": "❌ 解析失败",
                "schema_validation": "❌ 校验失败",
            }.get(err_type, f"❌ {err_type}")
            desc_parts.append(f"{tag}: {err_msg[:200]}")

        label = self._PHASE_LABELS.get(phase_prefix, mapped["label"])
        description = "\n".join(desc_parts) or f"{label} (已完成)"
        # Error takes precedence over gate-awaiting — a phase that errored
        # should never display as merely "pending" (waiting for review).
        if error_info is not None:
            node_state = "error"
        elif gate_awaiting:
            node_state = "pending"
        else:
            node_state = "success"
        review_status = "pending" if gate_awaiting else None

        # Collect output file paths from outputs.
        file_paths: list[str] = []
        for val in outputs.values():
            if isinstance(val, dict):
                fp = val.get("filePath") or val.get("path")
                if fp and isinstance(fp, str):
                    file_paths.append(fp)

        # Phase summary nodes are always "script" type — the canvas server
        # requires non-empty filePath for asset/media/video node types, which
        # phase summary nodes don't have (they represent the phase itself, not
        # a media file). The canvas_type from _PHASE_TYPE_MAP applies to
        # ARTIFACT child nodes, not the phase summary.
        node_data: dict[str, Any] = {
            "type": "script",
            "position": position,
            "size": {"width": 260, "height": 180},
            "state": node_state,
            "branchId": "main",
            "phaseIndex": phase_index,
            "phaseName": label,
            "data": {
                "label": label,
                "phase": phase_group,
                "description": description,
                "tags": mapped["tags"] or [],
                # score: only include when it's a real number (None would
                # create a "score": null key that some validators reject).
                "content": description,
                "state": node_state,
                "phaseName": label,
                "assetType": asset_type,
            },
        }
        # Conditionally write score — only when it's a real number.
        if isinstance(score, (int, float)):
            node_data["data"]["score"] = score
        # Only write filePath when at least one real file path exists.
        # The save-v2 schema (canvasAssetSchema.ts:108-118) marks filePath
        # OPTIONAL for script nodes; phase summary nodes are always script
        # type, so writing "" pollutes the canvas detail panel with an
        # empty file row for every text-only phase.
        if file_paths:
            node_data["data"]["filePath"] = ", ".join(file_paths)

        # ── 平铺标量兜底（2026-08-19 审计 #1 遗留面）──────────────────
        # outputs 顶层的平铺标量（旧版 p01 的 hook_type/hook_intensity/
        # opening_line、未来任何未嵌套 phase 输出）此前在 summary 节点上
        # 无处落地 — _enrich_p01_summary 只认嵌套 dict 形状。合并进
        # summary data（跳过保留键与簿记键，上限 16 个），再跑一遍 schema
        # 映射让 camelCase 键（hookType/hookIntensity…）出现在 summary 上。
        _RESERVED_DATA_KEYS = frozenset({
            "label", "description", "content", "state", "tags", "assetType",
            "phase", "phaseName", "score", "filePath", "reviewStatus",
            "provenance", "type",
        })
        _flat_merged = 0
        for _fk, _fv in outputs.items():
            if _flat_merged >= 16:
                break
            if _fk in _RESERVED_DATA_KEYS or _fk in self._SKIP_KEYS:
                continue
            if not isinstance(_fv, (str, int, float, bool)) or _fv in ("", None):
                continue
            if _fk not in node_data["data"]:
                node_data["data"][_fk] = _fv
                _flat_merged += 1
        if _flat_merged:
            _apply_schema_mappings(
                node_data["data"], phase_prefix, node_data["data"],
            )

        # ── Provenance Chain: embed phase-level provenance ──────────
        # The promoted provenance dict (set by _extract_and_promote_provenance
        # in runner.py) carries prompt/tool/model/seed from the subagent.
        # We embed it in the phase node data so the canvas detail panel can
        # display how this phase's outputs were generated.
        prov = result.get("provenance")
        if isinstance(prov, dict):
            node_data["data"]["provenance"] = prov
        if review_status is not None:
            node_data["data"]["reviewStatus"] = review_status
            # C3: KAP's contract field is the TOP-LEVEL ``reviewStatus``
            # (flowgraph-v2-schema.ts:42 → canvasRelationalStore maps it to the
            # canvas_nodes.review_status column). Writing it only under
            # data.reviewStatus left the column NULL, so review badges/filters
            # never saw "awaiting" phases. Write BOTH: top-level (contract,
            # consumed by review_status column) + nested data.reviewStatus
            # (kept as a frontend fallback — do not remove).
            node_data["reviewStatus"] = review_status
        return node_data

    # ─── cross-phase reference linking (V4) ──────────────────

    # Maps phase prefix → list of output keys that carry reference source
    # ids pointing to artifacts from an EARLIER phase. Each entry:
    # (output_key, source_phase_prefix, ref_type).
    #
    # When a phase's outputs contain one of these keys, the subscriber
    # looks up the referenced artifact node(s) in the already-built graph
    # and draws ``dataType="reference"`` dashed links.
    _CROSS_PHASE_REF_KEYS: dict[str, list[tuple[str, str, str]]] = {
        # NOTE: p07 ghost entries removed (2026-07-31 P07 audit).
        # p07 NEVER emits top-level ``character_references`` or
        # ``scene_references`` keys (its real outputs are scene_images /
        # style_vector / color_intent), so these two specs could never
        # resolve → dead config that drew 0 edges. The real cross-phase
        # reference edges into P07 scene images are drawn by the
        # ``_TEXT_PHASE_CHAIN`` (P06 spatio_temporal_script → P07 scene_images)
        # and inline asset fields handled by ``_link_asset_level_references``.
        # As a result this table is now empty; retained (empty) for the
        # ``.get(phase_prefix, [])`` lookup in ``_add_reference_links``.
        # NOTE: p09/p11 ghost entries removed (2026-07-30 full-stack audit).
        # The previous p09 (starting_images / reference_images → p07) and p11
        # (shot_references → p09) entries watched top-level output keys that
        # P09/P11 NEVER emit — P09 expert_output has {shot_list, e_konte_sheets,
        # transition_design}; P11 aggregated has {video_clips, lip_sync_reports}.
        # Those keys therefore never resolved → dead code that drew 0 edges.
        # The real cross-phase references for P09 storyboards and P11 videos
        # are carried INLINE in each asset (character_refs / scene_ref /
        # audio_path) and are drawn by _link_asset_level_references below.
    }

    # ── Text-phase dependency chain (P01→P07) ─────────────────────────────
    # The pre-production phases (P01-P07) emit TEXT artifacts (topic_kernel,
    # script, character_bible, ...) that have a clear linear dependency on the
    # previous phase's output, but none of them populate
    # ``provenance.input_refs`` or any top-level reference key — so without an
    # explicit declaration the canvas shows ZERO reference edges across the
    # entire first half of the pipeline. This chain declares those edges so
    # ``_add_reference_links`` can draw ``dataType="reference"`` dashed links.
    #
    # Each entry: (target_phase, target_out_key, source_phase, source_out_key,
    #              ref_type). When the current phase == target_phase, we look
    # up all nodes belonging to source_phase whose origin is source_out_key
    # and draw an edge from each source node → each target node.
    _TEXT_PHASE_CHAIN: list[tuple[str, str, str, str, str]] = [
        ("p02", "story_framework", "p01", "topic_kernel", "topic_ref"),
        ("p03", "script", "p02", "story_framework", "outline_ref"),
        # P03.5 86ke 打磨链：script-draft(p03) + beat event_type(p02) → 打磨剧本
        ("p035", "script_draft_polished", "p03", "script", "script_ref"),
        ("p035", "script_draft_polished", "p02", "story_framework", "outline_ref"),
        # ICA M2 (2026-08-25): p036 钩子再实例化链
        # hook-spec 从打磨剧本 + hook-intent 派生（C4b 承诺/实例分离）。
        ("p036", "hook_spec", "p035", "script_draft_polished", "script_ref"),
        ("p036", "hook_spec", "p01", "hook_design", "intent_ref"),
        # P04 主输入仍是打磨剧本（p035）——hook-spec 不直接 feed P04，
        # 消费方是 p09b / p14（见 FIX-6 读序切换）。
        ("p04", "character_bible", "p035", "script_draft_polished", "script_ref"),
        ("p06", "spatio_temporal_script", "p04", "character_bible", "character_ref"),
        ("p07", "scene_images", "p06", "spatio_temporal_script", "script_ref"),
        ("p08", "scene_selection", "p07", "scene_images", "scene_ref"),
    ]

    def _add_reference_links(
        self,
        graph: dict[str, Any],
        phase_id: str,
        phase_prefix: str,
        art_node_ids: list[tuple[str, dict[str, Any]]],
        result: dict[str, Any],
    ) -> None:
        """Draw ``dataType="reference"`` dashed links between artifacts.

        Handles four reference patterns (V4 canvas spec):

        1. **P04 internal**: character_bible sheets → character_assets L2
           crops. Triggered when both ``character_bible`` and
           ``character_assets`` exist in P04 outputs.

        2. **P04 → P07**: P04 character sheets referenced by P07 scene
           images. Triggered when P07 outputs contain
           ``character_references`` listing P04 artifact ids.

        3. **P07 internal**: scene_references → individual scene_multi_angle
           images. Triggered when both exist in P07 outputs.

        4. **P07 → P09**: P07 scene images referenced by P09 shots as
           ``starting_images``. Triggered when P09 outputs contain
           ``starting_images`` listing P07 artifact ids.

        All links use ``ensure_reference_link`` (idempotent). Missing
        source/target nodes are silently skipped (degrade-tolerant).
        """
        outputs = result.get("outputs") or {}
        if not isinstance(outputs, dict):
            return

        # Build a lookup of all artifact nodes currently in the graph
        # for quick reference resolution.
        all_nodes = {
            n.get("id"): n
            for n in graph.get("nodes", [])
            if isinstance(n, dict)
        }

        # ── Phase-internal references ─────────────────────────────
        # P03: script → audit_report. The audit is derived from the script
        # (script_auditor reads the screenplay), but without an explicit edge
        # the canvas shows the 16 weakness child nodes as orphans with 0
        # in-edges — operators can't tell which script was audited. Draw a
        # reference link from the script head node (a-script-summary) to each
        # audit_report node (summary + weaknesses) so the derivation chain is
        # visible. Head-to-head only (MODERATE #3: avoid combinatorial blowup).
        if phase_prefix == "p03":
            # Source: the script head node. With expand=True the script dict
            # produces a-script-summary plus a-script-{sub_key}-{j} children.
            # Only link the head — linking every scene to every weakness is
            # noise (the audit is against the WHOLE script, not per-scene).
            for src_nid, _ in art_node_ids:
                if src_nid == "a-script-summary":
                    src_node_id = src_nid
                    break
            else:
                src_node_id = None
            if src_node_id:
                for tgt_nid, _ in art_node_ids:
                    if not tgt_nid.startswith("a-audit_report"):
                        continue
                    if tgt_nid == src_node_id:
                        continue
                    canvas_graph.ensure_reference_link(
                        graph, src_node_id, tgt_nid,
                        ref_type="script_audit_ref",
                    )

        # P04: character_bible → character_assets.
        # 2026-07-31 P04 audit: the old group_key join failed because the
        # child nodes expand with numeric indices (character_bible-characters[i]
        # vs character_assets-l1_anchors[i]) that don't share a group_key.
        # Draw a head-to-head edge (a-character_bible-summary →
        # a-character_assets-summary) like the P03 script→audit_report pattern
        # so the derivation chain is visible without per-character fan-out.
        # The dead l1_multi_angle link was also removed here (the node never
        # exists, so the call was no-op dead code).
        if phase_prefix == "p04":
            cb_head = next(
                (nid for nid, _ in art_node_ids
                 if nid in ("a-character_bible", "a-character_bible-summary")),
                None,
            )
            ca_head = next(
                (nid for nid, _ in art_node_ids
                 if nid in ("a-character_assets", "a-character_assets-summary")),
                None,
            )
            if cb_head and ca_head and cb_head != ca_head:
                canvas_graph.ensure_reference_link(
                    graph, cb_head, ca_head,
                    ref_type="char_sheet_ref",
                )

        # ── Cross-phase references ────────────────────────────────
        # Look for explicit reference keys in this phase's outputs
        # (e.g. P09 outputs["starting_images"] = ["scene-01"]).
        ref_specs = self._CROSS_PHASE_REF_KEYS.get(phase_prefix, [])
        for ref_key, src_prefix, ref_type in ref_specs:
            ref_val = outputs.get(ref_key)
            if ref_val is None:
                continue

            # ref_val can be a list of artifact ids, or a list of dicts
            # with an "id" or "source_id" field.
            ref_ids: list[str] = []
            if isinstance(ref_val, list):
                for item in ref_val:
                    if isinstance(item, str):
                        ref_ids.append(item)
                    elif isinstance(item, dict):
                        rid = item.get("source_id") or item.get("id")
                        if rid:
                            ref_ids.append(str(rid))
            elif isinstance(ref_val, dict):
                # Dict of phase_prefix → list of ids.
                for sub_list in ref_val.values():
                    if isinstance(sub_list, list):
                        for item in sub_list:
                            if isinstance(item, str):
                                ref_ids.append(item)

            # Resolve each ref_id to a source node id.
            # Try multiple strategies: exact match, a-{id}, a-{key}-{id},
            # and characterId/characterCanonical search.
            resolved_sources: list[str] = []
            for ref_id in ref_ids:
                src_node_id = self._resolve_ref_to_node(
                    ref_id, src_prefix, all_nodes,
                )
                if src_node_id:
                    resolved_sources.append(src_node_id)

            # Draw reference links from each resolved source to each
            # artifact created in THIS phase.
            for src_node_id in resolved_sources:
                for tgt_node_id, _ in art_node_ids:
                    canvas_graph.ensure_reference_link(
                        graph, src_node_id, tgt_node_id,
                        ref_type=ref_type,
                    )

        # ── Provenance-based dependency links (V2 asset management) ──
        # Each artifact may carry a ``provenance.input_refs`` list pointing
        # to upstream asset node ids. We draw ``dataType="dependency"`` links
        # from each referenced upstream node → this artifact node, creating
        # the full provenance chain across phases.
        #
        # Unlike the legacy _CROSS_PHASE_REF_KEYS pattern above (which maps
        # fixed output keys to source phases), this reads the subagent-
        # populated input_refs directly — so ANY phase that reports its
        # inputs automatically gets dependency links drawn.
        for tgt_node_id, art_data in art_node_ids:
            prov = art_data.get("provenance") if isinstance(art_data, dict) else None
            if not isinstance(prov, dict):
                continue
            input_refs = prov.get("input_refs")
            if not isinstance(input_refs, list):
                continue
            for ref_id in input_refs:
                if not isinstance(ref_id, str) or not ref_id:
                    continue
                # Resolve ref_id to a graph node id (try same strategies
                # as cross-phase refs — the ref might be an artifact id
                # from any earlier phase).
                src_node_id = self._resolve_ref_to_node(
                    ref_id, "", all_nodes,
                )
                if src_node_id and src_node_id != tgt_node_id:
                    canvas_graph.ensure_reference_link(
                        graph, src_node_id, tgt_node_id,
                        ref_type="provenance",
                    )

        # ── Text-phase dependency chain (P01→P07) ─────────────────────
        # Pre-production text artifacts (topic_kernel → story_framework →
        # script → ...) form a linear dependency chain that no phase reports
        # via input_refs. _TEXT_PHASE_CHAIN declares those edges explicitly.
        # For each chain entry where the CURRENT phase is the target, resolve
        # source nodes from the already-built graph and draw reference edges
        # source → each target artifact.
        for (
            tgt_phase, tgt_key, src_phase, src_key, ref_type,
        ) in self._TEXT_PHASE_CHAIN:
            if tgt_phase != phase_prefix:
                continue
            # Resolve the target side: the current phase's artifacts whose
            # origin output key matches tgt_key. art_node_ids are tuples of
            # (node_id, artifact_dict); the artifact id (after the "a-" prefix)
            # is either "{tgt_key}" (non-expand dict), "{tgt_key}-summary"
            # (expand dict summary), or "{tgt_key}-{i}" (list). Match any of
            # these so the edge is drawn from the summary node.
            src_lc = src_phase.lower()
            _src_prefix = f"a-{src_key}"

            def _is_source(node: Any) -> bool:
                """Node belongs to src_phase and its origin is src_key."""
                if not isinstance(node, dict):
                    return False
                pn = node.get("phaseName")
                if not (isinstance(pn, str) and pn.split("_", 1)[0].lower() == src_lc):
                    return False
                return True  # phase gate is sufficient; id filter applied below

            # Collect source nodes whose id starts with a-{src_key}.
            source_nodes: list[str] = [
                nid for nid, node in all_nodes.items()
                if isinstance(nid, str)
                and nid.startswith(_src_prefix)
                and _is_source(node)
            ]
            # MODERATE #3: restrict to HEAD nodes only to avoid combinatorial
            # edge blowup. The chain represents a PHASE-LEVEL dependency
            # (story_framework → script), not per-element. Linking every
            # source child (e.g. every beat) to every target child (every
            # scene) creates N×M edges — the audit saw 104 edges including
            # _agent_name / episode_id noise nodes. Head = the bare output
            # key (non-expand dict) or its "{key}-summary" (expand dict).
            source_nodes = self._restrict_to_head_nodes(source_nodes, src_key)
            if not source_nodes:
                continue
            # Collect target nodes: current-phase artifacts whose id token
            # starts with tgt_key (covers "{tgt_key}", "{tgt_key}-summary",
            # "{tgt_key}-{i}"). Keep the existing art_node_ids target set but
            # restrict to those originating from tgt_key to avoid over-linking.
            target_nodes: list[str] = [
                nid for nid, _ in art_node_ids
                if isinstance(nid, str) and nid.startswith(f"a-{tgt_key}")
            ]
            target_nodes = self._restrict_to_head_nodes(target_nodes, tgt_key)
            for src_node_id in source_nodes:
                for tgt_node_id in target_nodes:
                    if src_node_id == tgt_node_id:
                        continue
                    canvas_graph.ensure_reference_link(
                        graph, src_node_id, tgt_node_id,
                        ref_type=ref_type,
                    )

    @staticmethod
    def _restrict_to_head_nodes(
        node_ids: list[str],
        out_key: str,
    ) -> list[str]:
        """Restrict a node-id list to the HEAD/summary node(s) of an output.

        Used by ``_TEXT_PHASE_CHAIN`` linking to avoid combinatorial edge
        blowup (MODERATE #3): the chain is a phase-level dependency
        (story_framework → script), so only the summary node should be
        linked — not every expanded child (which also filters out
        ``_agent_name`` / ``episode_id`` / ``_seq`` noise nodes that share
        the ``a-{out_key}-`` prefix).

        A head node is either:
          - ``a-{out_key}``         (non-expand dict / single summary)
          - ``a-{out_key}-summary`` (expand dict summary node)

        If neither exists, fall back to the full list (degrade-tolerant —
        some phases use list outputs without a summary node).
        """
        bare = f"a-{out_key}"
        summary = f"a-{out_key}-summary"
        heads = [
            nid for nid in node_ids
            if nid in (bare, summary)
        ]
        if heads:
            return heads
        # Fallback: filter out obvious child/noise suffixes. A head node's
        # id token after "a-{out_key}" is empty or "-summary"; children carry
        # "-{sub_key}-{i}" or "-{i}". Keep only those matching the head pattern,
        # and drop any metadata-key children that survived the _SKIP filter.
        _noise_suffixes = (
            "-episode_id", "-_agent_name", "-_seq", "-_error",
            "-_retry_count", "-_delegate_trace", "-_source_skill",
            "-_delegate_id", "-_parse_warnings", "-timestamp", "-run_id",
        )
        filtered = [
            nid for nid in node_ids
            if not any(nid.endswith(s) for s in _noise_suffixes)
        ]
        return filtered if filtered else node_ids

    def _link_asset_level_references(
        self,
        graph: dict[str, Any],
        art_node_ids: list[tuple[str, dict[str, Any]]],
    ) -> None:
        """P1-canvas-topology (2026-07-14): draw dataType="reference" links
        based on asset-level fields the LLM populates inline.

        Unlike ``_add_reference_links`` (which reads phase outputs.ref_key
        top-level lists), this method reads each video asset node's own data
        fields — ``character_refs``, ``scene_ref``, ``audio_path`` — and
        resolves them to upstream source nodes (P04 character turnaround /
        P07 scene / P10 voice).

        Root cause being fixed: ep-hamster-demolition P11 video nodes all
        carry character_refs/scene_ref/audio_path inline, but the existing
        ``_CROSS_PHASE_REF_KEYS`` table only watches specific output list
        keys (``shot_references`` / ``starting_images``). Without this
        method, the canvas shows 0 reference edges — operators can't trace
        "which character is in this shot" or "which scene image drove this
        render" from the graph topology.

        Idempotent: uses ensure_reference_link. Missing source/target
        silently skipped (degrade-tolerant).
        """
        all_nodes = {
            n.get("id"): n
            for n in graph.get("nodes", [])
            if isinstance(n, dict)
        }
        links_added = 0

        for tgt_node_id, art_data in art_node_ids:
            if not isinstance(art_data, dict):
                continue
            # Accept video (P11) AND storyboard (P09) nodes — both carry
            # inline character_refs / scene_ref fields that need to be drawn
            # as cross-phase reference links. The original code only checked
            # video, causing P09 storyboard nodes' rich reference data to be
            # silently skipped (canvas showed 0 reference edges).
            _atype = art_data.get("assetType") or art_data.get("type", "")
            # P10 voice/audio nodes carry ``speaker`` + ``shot_id`` that link
            # back to P04 characters and P09 shots. Handle them in a dedicated
            # branch before the video/storyboard gate — otherwise audio nodes
            # are skipped entirely and P04→P10 / P09→P10 edges never appear
            # (canvas-topology 断链 3).
            if _atype in ("audio", "voice"):
                links_added += self._link_audio_node_references(
                    graph, tgt_node_id, art_data, all_nodes,
                )
                continue
            if _atype not in ("video", "storyboard"):
                continue

            # ── character_refs[] → P04 character turnaround ──────────
            char_refs = art_data.get("character_refs")
            if isinstance(char_refs, list):
                for char_ref in char_refs:
                    if not isinstance(char_ref, dict):
                        continue
                    ref_id = (
                        char_ref.get("characterId")
                        or char_ref.get("characterCanonical")
                        or char_ref.get("character_id")
                        or char_ref.get("character_label")
                        or char_ref.get("name")
                    )
                    if not ref_id:
                        continue
                    src = self._resolve_ref_to_node(
                        str(ref_id), "p04", all_nodes,
                    )
                    if src and src != tgt_node_id:
                        canvas_graph.ensure_reference_link(
                            graph, src, tgt_node_id,
                            ref_type="character_ref",
                        )
                        links_added += 1

            # ── scene_ref → P07 scene asset ──────────────────────────
            # Resolve the scene IDENTITY for a P07 scene-image link. We derive
            # a clean scene TOKEN ("S1") rather than reading scene_ref verbatim,
            # because (a) P09 shots frequently leave scene_ref=null — the token
            # is recovered from shot_id ("S1-01" → "S1") or scene_label — and
            # (b) a scene_ref PATH like "assets/S07/S1_front.png" corrupts the
            # ordinal fallback below (its "S07" directory prefix parses as
            # scene 7). Scene tokens resolve to P07 nodes by ORDINAL position,
            # never by id substring (canvas-topology 断链 2).
            scene_ref = self._derive_scene_ref(art_data)
            if scene_ref:
                src = None
                # Ordinal fallback: parse S<n> / S0n → a-scene_images-(n-1)
                # CRITICAL: use findall and take the LAST match to avoid
                # matching the S07 directory prefix in paths like
                # "assets/S07/S1_front.png" (S07 → wrong, S1 → correct).
                all_s_matches = re.findall(r"S0*(\d+)", scene_ref, re.IGNORECASE)
                if all_s_matches:
                    sidx = int(all_s_matches[-1]) - 1
                    # Try both "a-scene_images-{idx}" and
                    # "a-scene_images-scene_images-{idx}" ID formats.
                    for candidate in (
                        f"a-scene_images-{sidx}",
                        f"a-scene_images-scene_images-{sidx}",
                    ):
                        if candidate in all_nodes:
                            src = candidate
                            break
                if src and src != tgt_node_id:
                    canvas_graph.ensure_reference_link(
                        graph, src, tgt_node_id,
                        ref_type="scene_ref",
                    )
                    links_added += 1

            # ── audio_path → P10 voice clip asset ────────────────────
            # Resolve by file path tail match — P10 voice nodes currently
            # don't expose audio_path at the node level, but shot_id-based
            # path matching works (audio/p10_voice/SH01.wav ← SH01 voice).
            audio_path = art_data.get("audio_path")
            if isinstance(audio_path, str) and audio_path:
                # Extract shot id from audio_path (e.g. SH01 from p10_voice/SH01.wav)
                ap_match = re.search(r"(SH\d+)", audio_path, re.IGNORECASE)
                ap_shot = ap_match.group(1) if ap_match else None
                tgt_shot = art_data.get("shot_id")
                # Find any P10/voice-related node and link to it
                for node_id, node in all_nodes.items():
                    if node_id == tgt_node_id or not isinstance(node, dict):
                        continue
                    node_data = node.get("data", {}) if isinstance(node.get("data"), dict) else node
                    node_asset = node_data.get("assetType", "")
                    node_phase = (
                        node_data.get("phase", "")
                        or node_data.get("phaseName", "")
                    )
                    # Match P10 voice / audio_stems / voice_timeline script nodes
                    is_voice_node = (
                        "p10" in str(node_id).lower()
                        or "voice" in str(node_id).lower()
                        or "audio" in node_asset.lower()
                    )
                    if not is_voice_node:
                        continue
                    # If shot-id matching is possible, require it
                    if ap_shot and tgt_shot and ap_shot != tgt_shot:
                        continue
                    canvas_graph.ensure_reference_link(
                        graph, node_id, tgt_node_id,
                        ref_type="audio_ref",
                    )
                    links_added += 1
                    break  # one voice source per video is enough

        if links_added:
            logger.info(
                "canvas_sync: _link_asset_level_references drew %d "
                "reference links for video assets",
                links_added,
            )

    def _link_audio_node_references(
        self,
        graph: dict[str, Any],
        tgt_node_id: str,
        art_data: dict[str, Any],
        all_nodes: dict[str, Any],
    ) -> int:
        """Draw reference links for a P10 voice/audio node.

        canvas-topology 断链 3 (2026-07-27): P10 voice clips carry ``speaker``
        (e.g. "阿毛(旁白)") and ``shot_id`` ("S1-01"), but the legacy
        ``_link_asset_level_references`` only handled video/storyboard nodes —
        audio nodes were skipped, so P04→P10 (角色配音) and P09→P10 (镜头对齐)
        edges never appeared.

        This draws:
        * ``characterId`` / parsed ``speaker`` → P04 character turnaround
          (``character_ref``).
        * ``shot_id`` → P09 shot storyboard (``shot_ref``).

        Returns the number of reference links drawn. Idempotent; missing
        sources are silently skipped (degrade-tolerant).
        """
        added = 0
        # ── speaker/characterId → P04 character ─────────────────────
        char_id = (
            art_data.get("characterId")
            or art_data.get("characterCanonical")
            or self._parse_speaker_character(art_data.get("speaker"))
        )
        if char_id:
            src = self._resolve_ref_to_node(str(char_id), "p04", all_nodes)
            if src and src != tgt_node_id:
                canvas_graph.ensure_reference_link(
                    graph, src, tgt_node_id, ref_type="character_ref",
                )
                added += 1
        # ── shot_id → P09 shot storyboard ───────────────────────────
        shot_id = art_data.get("shot_id")
        if isinstance(shot_id, str) and shot_id:
            src = self._resolve_ref_to_node(shot_id, "p09", all_nodes)
            if src and src != tgt_node_id:
                canvas_graph.ensure_reference_link(
                    graph, src, tgt_node_id, ref_type="shot_ref",
                )
                added += 1
        return added

    @staticmethod
    def _parse_speaker_character(speaker: Any) -> str | None:
        """Reduce a speaker string to a bare character name.

        "阿毛(旁白)" → "阿毛"; "阿毛（画外音）" → "阿毛"; "阿毛" → "阿毛";
        "" / None / "旁白" → the stripped value or None. Strips parenthetical
        role qualifiers (both full-width （…） and ASCII (…)) so a P10 speaker
        resolves to the same ``characterId`` P04 emits.
        """
        if not isinstance(speaker, str) or not speaker.strip():
            return None
        s = re.sub(r"[（(].*?[）)]", "", speaker).strip()
        return s or None

    @staticmethod
    def _derive_scene_ref(art_data: dict[str, Any]) -> str | None:
        """Extract a clean scene TOKEN ("S1") for linking a shot to its P07 scene.

        Priority order (first non-empty wins):
        1. ``scene_id`` — already a clean token when P09 carries it.
        2. ``shot_id`` leading component — "S1-01" → "S1".
        3. ``scene_label`` leading component — "S1·枯叶卷棚…" → "S1".
        4. ``scene_ref`` — ONLY when it is a bare token (no path separator,
           no file extension). A scene_ref PATH is deliberately skipped
           because its directory prefix (e.g. "S07" in "assets/S07/…")
           corrupts the ordinal fallback downstream.

        Returns ``None`` when no token can be derived.
        """
        def _first_token(val: Any) -> str | None:
            if not isinstance(val, str) or not val:
                return None
            m = re.search(r"S\d+", val.strip(), re.IGNORECASE)
            return m.group(0).upper() if m else None

        for key in ("scene_id", "shot_id", "scene_label"):
            tok = _first_token(art_data.get(key))
            if tok:
                return tok
        sr = art_data.get("scene_ref")
        if isinstance(sr, str) and sr and "/" not in sr and "." not in sr:
            return _first_token(sr)
        return None

    @staticmethod
    def _resolve_ref_to_node(
        ref_id: str,
        src_prefix: str,
        all_nodes: dict[str, Any],
    ) -> str | None:
        """Resolve a reference id to an actual graph node id.

        Tries multiple strategies in order:
        1. Exact match (``ref_id`` is already a node id).
        2. ``a-{ref_id}`` (artifact node id form).
        3. ``a-{src_prefix}_{...}-{ref_id}`` (phase-prefixed artifact). When
           ``src_prefix`` is given, only nodes whose ``phaseName`` belongs to
           that phase qualify — prevents short tokens ("S10") mis-resolving
           across phases.
        4. Search by ``characterId`` / ``characterCanonical`` /
           ``characterSlug`` data field (canonical Chinese name OR pinyin slug).

        Returns the first matching node id, or ``None`` if not found.

        When ``src_prefix`` is non-empty, EVERY strategy restricts matches to
        nodes whose ``phaseName`` belongs to that phase. This prevents short
        tokens from mis-resolving across phases — e.g. ``a-{ref_id}`` for
        ``ref_id="S1-01"`` would otherwise return a P06 node ``a-S1-01`` when
        the caller asked for the P09 storyboard (canvas-topology 断链 4).
        """
        src_lc = src_prefix.lower() if src_prefix else ""

        def _phase_ok(node: Any) -> bool:
            """True when no phase hint given, or node belongs to that phase."""
            if not src_lc:
                return True
            if isinstance(node, dict):
                pn = node.get("phaseName")
                if isinstance(pn, str) and pn:
                    return pn.split("_", 1)[0].lower() == src_lc
            return False

        # Strategy 1: exact match.
        if ref_id in all_nodes and _phase_ok(all_nodes[ref_id]):
            return ref_id

        # Strategy 2: a-{ref_id}.
        candidate = f"a-{ref_id}"
        if candidate in all_nodes and _phase_ok(all_nodes[candidate]):
            return candidate

        # Strategy 3: search for nodes whose id ends with the ref_id
        # and belongs to the source phase (e.g. "a-character_assets-laolin"
        # for ref_id="laolin" from p04).
        for node_id, node in all_nodes.items():
            if not node_id.startswith("a-"):
                continue
            # Check if the node id contains the ref_id as a suffix or token.
            # Be conservative: only match if ref_id is at least 3 chars.
            if len(ref_id) >= 3 and ref_id in node_id:
                if not _phase_ok(node):
                    continue
                return node_id

        # Strategy 4: search by characterId / characterCanonical /
        # characterSlug data field. characterId/characterCanonical hold the
        # canonical (Chinese) name; characterSlug holds the pinyin slug. Both
        # are valid join keys depending on which phase emitted the reference.
        normalized = canvas_graph.normalize_character_name(ref_id)
        for node_id, node in all_nodes.items():
            if not isinstance(node, dict):
                continue
            if not _phase_ok(node):
                continue
            data = node.get("data", {})
            if not isinstance(data, dict):
                continue
            for char_field in ("characterId", "characterCanonical", "characterSlug"):
                char_val = data.get(char_field)
                if char_val:
                    char_normalized = canvas_graph.normalize_character_name(char_val)
                    if char_normalized == normalized:
                        return node_id

        # Strategy 5: match by label field (pinyin slug bridge).
        # P04 character assets carry the pinyin slug in their ``label`` field
        # (e.g. label="amao") while characterId holds the Chinese name (阿毛).
        # P09 character_refs[].name uses the same pinyin slug. Without this
        # strategy, _resolve_ref_to_node("amao", "p04") fails because no node
        # has characterId/characterCanonical="amao" — they have "阿毛".
        if src_lc and len(ref_id) >= 2:
            ref_lc = ref_id.lower()
            for node_id, node in all_nodes.items():
                if not isinstance(node, dict):
                    continue
                if not _phase_ok(node):
                    continue
                data = node.get("data", {})
                if not isinstance(data, dict):
                    continue
                label_val = data.get("label")
                if isinstance(label_val, str) and label_val.lower() == ref_lc:
                    return node_id

        return None

    def _link_internal_references(
        self,
        graph: dict[str, Any],
        outputs: dict[str, Any],
        src_key: str,
        tgt_key: str,
        all_nodes: dict[str, Any],
        ref_type: str,
    ) -> None:
        """Draw reference links between two output groups within the same phase.

        Links each source artifact (from ``src_key``) to all target
        artifacts (from ``tgt_key``) that share a ``characterId`` or
        ``sceneId`` grouping key. This ensures character sheets link
        only to their own L2 crops, not to other characters' crops.
        """
        src_val = outputs.get(src_key)
        tgt_val = outputs.get(tgt_key)
        if src_val is None or tgt_val is None:
            return

        # Extract source items.
        src_items: list[tuple[str, str | None]] = []  # (id, group_key)
        self._collect_ref_items(src_val, src_key, src_items)

        # Extract target items.
        tgt_items: list[tuple[str, str | None]] = []
        self._collect_ref_items(tgt_val, tgt_key, tgt_items)

        # Link by group_key when possible, otherwise link all-to-all.
        for src_id, src_group in src_items:
            src_node = f"a-{src_id}"
            if src_node not in all_nodes:
                continue
            for tgt_id, tgt_group in tgt_items:
                tgt_node = f"a-{tgt_id}"
                if tgt_node not in all_nodes:
                    continue
                # Only link if groups match (or both have no group).
                if src_group and tgt_group:
                    src_canonical = canvas_graph.normalize_character_name(src_group)
                    tgt_canonical = canvas_graph.normalize_character_name(tgt_group)
                    if src_canonical != tgt_canonical:
                        continue
                canvas_graph.ensure_reference_link(
                    graph, src_node, tgt_node,
                    ref_type=ref_type,
                )

    @staticmethod
    def _collect_ref_items(
        val: Any,
        key_prefix: str,
        out: list[tuple[str, str | None]],
    ) -> None:
        """Extract (artifact_id, group_key) pairs from an output value.

        Handles lists of dicts, dicts of lists, and dicts of dicts.
        """
        if isinstance(val, list):
            for i, item in enumerate(val):
                if isinstance(item, str):
                    out.append((f"{key_prefix}-{i}", None))
                elif isinstance(item, dict):
                    aid = str(
                        item.get("id") or item.get("shot_id")
                        or item.get("name") or f"{key_prefix}-{i}",
                    )
                    group = (
                        item.get("characterId")
                        or item.get("character_id")
                        or item.get("character")
                        or item.get("sceneId")
                        or item.get("scene_id")
                        or item.get("scene")
                    )
                    out.append((aid, str(group) if group else None))
        elif isinstance(val, dict):
            for sub_key, sub_val in val.items():
                if isinstance(sub_val, list):
                    for i, item in enumerate(sub_val):
                        if isinstance(item, dict):
                            aid = str(
                                item.get("id") or item.get("shot_id")
                                or item.get("name")
                                or f"{key_prefix}-{sub_key}-{i}",
                            )
                            group = (
                                item.get("characterId")
                                or item.get("character")
                                or sub_key  # Use the dict key as group
                            )
                            out.append((aid, str(group)))


    # Per-phase output key → artifact metadata.
    # Each entry: (output_key, label, canvas_type, expand_subkeys)
    # expand_subkeys: if the value is a dict, create child nodes from
    #   its top-level keys/sublists.
    #
    # ── D-06 canvas_type reuse decision (Phase 74 TRANS-03 system 3) ──────
    # The frontend zod schema (kais-aigc-platform/src/lib/canvasAssetSchema.ts)
    # defines 5 React Flow nodeTypes: audio / video / asset / storyboard /
    # script. There is NO distinct "transition" type. Phase 74 TRANS-03
    # system 3 reuses the storyboard canvas_type for the new transition_design
    # p09 output because:
    #   1. transition_design shares p09's pre-production design semantic
    #      (no media artifact yet — structured design data only).
    #   2. Zero frontend change is required in v14.0 (the existing storyboard
    #      zod schema accepts arbitrary structured fields via withYamlOptional).
    #   3. A distinct "transition" React Flow nodeType can be added in v15+
    #      if the operator requests visual separation on the canvas.
    # Verified 2026-07-09: grep -c "storyboard" canvasAssetSchema.ts == 6.
    _PHASE_OUTPUT_MAP: dict[str, list[tuple[str, str, str, bool]]] = {
        "p01": [
            ("topic_kernel", "选题核", "script", True),
            ("hook_design", "钩子设计", "script", True),
            # retention_engineering removed (2026-07-30 full-stack audit):
            # P01's run() returns only {"topic_kernel", "hook_design"} in
            # result["outputs"] — it never emits retention_engineering, so
            # this entry always resolved to None (a silent no-op).
        ],
        "p02": [
            ("story_framework", "故事框架", "script", True),
            ("outline_beats", "大纲节拍", "script", False),
            ("snowflake_artifacts", "雪花法产出", "script", True),
            ("emotion_curve_summary", "情感弧线", "script", False),
            # ICA M1 (2026-08-25): 创作契约清单 — P02 flag
            # (generation_config.consistency.layer=v2) 开启且提取成功时才
            # emit creative_contracts key；off/失败时 key 缺失 → dormant
            # 安全（本映射解析为 None 即 silent no-op，先例 retention_
            # engineering）。expand=False：契约条目经 params 平铺展示。
            ("creative_contracts", "创作契约", "script", False),
        ],
        "p03": [
            ("script", "剧本", "script", True),
            ("audit_report", "审计报告", "script", True),
        ],
        # P03.5 (86ke, 2026-08-15) — 戏剧性事件二次打磨。run() returns
        # result["outputs"] = {"script_draft_polished": dict, "dramatic_polish_report":
        # dict} (snake_case keys, mirrors p09b's shot-audit contract). The report
        # is the load-bearing canvas artifact (which scenes polished / gap_score
        # before-after / degraded mode); the polished script renders as a single
        # script node. canvas_type=script for both — neither is a shot, and
        # script's save-v2 required fields are just label+description (零 400 风险).
        "p035": [
            ("script_draft_polished", "打磨剧本", "script", True),
            ("dramatic_polish_report", "戏剧事件打磨报告", "script", True),
        ],
        # ICA M2 (2026-08-25): p036 钩子再实例化 — C4b 派生失效协议。
        # hook_spec 是 flag-gated 产出（consistency.layer=v2 时才写入），
        # dormant=False 以确保在 v2 模式下正常展示；旧 episode 缺 key →
        # _extract_artifacts 遇 None 直接跳过（零节点、零报错）。
        "p036": [
            ("hook_spec", "钩子规格", "script", False),
        ],
        "p04": [
            ("character_bible", "角色设定集", "asset", True),
            ("character_assets", "角色资产", "asset", True),
            # 2026-07-31 P04 audit: removed 3 phantom output keys
            # (l1_multi_angle / style_core_global / cross_character_consistency)
            # that P04 never actually produces — they caused orphan phase-row
            # slots and confused downstream reference resolution.
            # P04 声纹设计占位（Notion § 声纹设计）：phase 尚未在 result.outputs emit
            # voice_design key（声纹数据实际通过 VoiceDesign API
            # :10588/api/production/qwenTts/voiceId/voice-id 产出，独立于 KMC phase 输出），
            # _extract_artifacts 遇 val=None 直接跳过（不产生节点）。待 phase 实装生成、
            # emit 对应 key 后画布节点自动出现。canvas_type=audio（声纹是音频数据）。
            ("voice_design", "声纹设计", "audio", False),
        ],
        "p05": [
            ("pain_points", "痛点分析", "script", True),
            ("escalation_ladder", "情感阶梯", "script", False),
        ],
        "p06": [
            ("spatio_temporal_script", "时空剧本", "script", True),
            ("final_audit", "终审报告", "script", True),
            # P06 audit CRITICAL #1 (2026-07-31): emotion_curve was nested
            # inside spatio_temporal_script and never reached the canvas.
            # Now promoted to a top-level output key in p06 run(), so it
            # can be rendered as its own phase-row node.
            ("emotion_curve", "情感弧线", "script", False),
        ],
        "p07": [
            # Phase 75 P07 audit: p07 only emits scene_images/style_vector/
            # color_intent with content. Removed dead/alias keys: images,
            # scene_references, scene_multi_angle, scene_turnarounds, style.
            ("scene_images", "场景图", "asset", False),
            ("style_vector", "风格设定", "script", False),
            ("color_intent", "色彩意图", "script", False),
            # Notion《首尾帧设计》新资产占位（§1.2a/§1.2b）—— phase 尚未在
            # result.outputs emit 这些 key，_extract_artifacts 遇 val=None 直接
            # 跳过（不产生节点）。待 phase 实装生成、emit 对应 key 后画布节点
            # 自动出现。canvas_type 用 asset（场景视觉数据，同 scene_images）。
            ("scene_blueprint", "场景蓝图", "asset", False),
            ("scene_temporal_variants", "场景时空变体", "asset", False),
        ],
        "p08": [
            ("scene_selection", "场景选择", "asset", True),
            # 几何布局（geometry_bed）已于 2026-08 移除：P08 不再产出 geometry_bed
            # 节点，KMC P08 OUTPUT_SLOTS 仅 scene-selection，model.ts 同步移除。
        ],
        "p09": [
            ("shot_list", "分镜列表", "storyboard", False),
            # E-konte and transition_design are text/metadata nodes, not shot
            # nodes — they lack shot_type/duration_sec which the storyboard zod
            # schema requires. Use "script" type so canvas validation passes.
            ("e_konte_sheets", "Eコンテ", "script", False),
            # Phase 74 TRANS-03 — transition design (cinematographer creative intent → editor post-production)
            ("transition_design", "转场设计", "script", False),
            # W4: continuity_report (p09_shot_breakdown.py:1534 schema → flows
            # out at :1745). It is a DICT, not a list, and was not declared →
            # _extract_artifacts silently dropped it. Declare it as a script
            # node (expand=False): a dict with expand=False becomes a single
            # summary script node. canvas_type=script because it is a report,
            # not a shot (avoids storyboard Gate B fields).
            ("continuity_report", "连续性报告", "script", False),
        ],
        "p09b": [
            # 分镜审计微门 —— 实际 output key 是 ``shot-audit``（一个 dict，
            # 含 findings / critical_count / pass 等子键），不是 audit_findings。
            # 旧配置查 audit_findings/audit_report 两个不存在的 key，导致
            # P09b 的审计产出被整包丢弃（画布上看不到任何审计节点）。
            # canvas_type 固定 script：审计报告不是分镜，不应占用 storyboard
            # 类型位（避免 save-v2 的 storyboard schema 校验报 400）。
            ("shot-audit", "分镜审计", "script", True),
        ],
        "p09c": [
            # P09c 分镜故事板（clay maquette）—— 产出 storyboard_board dict
            # （scenes/shots/stats）。canvas_type=storyboard，expand=False：作为
            # 单个分镜板概览节点（2026-09-28 分镜板退役批后 board 槽唯一在册
            # 产出者；engine 缺省 off → 空板概览）。
            # 6 张分镜板图片由 _extract_artifacts 的目录扫描兜底（phase_dir_map
            # p09c → storyboard_sheets），无需在此声明。
            ("storyboard_board", "分镜故事板", "storyboard", False),
            # storyboard-qc (qwen-eye, 2026-08-16) — advisory 板面 QC（sheets[]
            # per-sheet 判定 + summary）。JSON 类 slot，与 P09b ("shot-audit",
            # ...) 契约同构：单 dict → 单 script 概览节点。
            ("storyboard-qc", "分镜板质检", "script", True),
        ],
        "p10": [
            ("voice_clips", "语音片段", "audio", False),
            ("voice_timeline", "语音时间线", "script", False),
            # bgm_cues / sfx_cues / voice_character_mapping were removed
            # (2026-07-30): the P10 audio_pipeline expert emits only voice_clips
            # + voice_timeline (confirmed across execution/prompt logs of
            # ep-maojianghu-ep01). BGM/SFX cues are produced by P12 composition,
            # not P10 voice. These phantom keys always resolved to None → a
            # silent no-op, so the canvas showed nothing for them regardless.
        ],
        "p10b": [
            # P10b rapid_preview emits scalar counts (variants_generated /
            # variants_degraded) AND a list of per-variant preview clip records
            # (rapid_preview_clips — CRITICAL #4 audit fix). The clip records
            # are dicts with shot_id / variant_id / clip_path / engine, so each
            # becomes a video child node on the canvas. Scalars produce no
            # child node (_extract_artifacts has no scalar branch).
            ("variants_generated", "预览生成数", "script", False),
            ("variants_degraded", "预览降级数", "script", False),
            ("rapid_preview_clips", "快速预览片段", "video", False),
            # storyboard_board entry removed 2026-09-28 分镜板退役批 (p10b
            # legacy section retained for its still-mapped preview keys).
        ],
        "p10c": [
            # Voice audit micro-gate — p10c_voice_audit.py returns
            # {"voice-audit": audit} where audit = {phase, findings[],
            # critical_count, warning_count, total_clips, empty_text_count,
            # pass}. The old audit_findings/audit_report keys never matched the
            # emitted key, so the entire voice audit was dropped from the canvas
            # (0 nodes — verified ep-maojianghu-ep01). Mirrors P09b's
            # ("shot-audit", ...) contract.
            ("voice-audit", "语音审计", "script", True),
        ],
        "p11": [
            ("video_clips", "视频片段", "video", False),
            ("lip_sync_reports", "口型同步报告", "script", False),
            # Notion §2d 关键中间帧占位（phase 尚未 emit → 跳过）。
            # canvas_type=asset（关键帧是图像，非 video）。task 草案写的
            # canvas_type="keyframe" 不是合法 React Flow nodeType，已校正。
            ("midframes", "关键中间帧", "asset", False),
        ],
        "p11a": [
            # P11a 预览片段 —— rapid_preview_clips（每条 shot 的快速预览）。
            # storyboard_board 已随 2026-09-28 分镜板退役批摘除（组装链 +
            # o_assets 落库同批退役）；本 phase 不再产出/消费 board，画布上的
            # 分镜板概览节点仅由 p09c 白模链渲染（engine 缺省 off）。
            ("rapid_preview_clips", "预览片段", "video", False),
            # preview-qc (qwen-eye, 2026-08-16) — advisory variant 首帧 QC
            # （variants[] 判定 + summary）。JSON 类 slot，与 P11c video-qc
            # 契约同构：单 dict → 单 script 概览节点。
            ("preview-qc", "预览质检", "script", True),
        ],
        # P11a.5 预演音频+成片 (2026-08-24 a046d47 落地; 2026-08-25 PRG-02 补
        # 画布映射)。四工件槽 — 此前 _phase_prefix 折叠成 'p11a' 导致全部漏挂:
        #   ambient_stems  dict(scene→stem path) → audio + expand 每场一子节点
        #   preview_mix_path  str → 单 audio 节点
        #   roughcut_path  str → 单 video 节点(kap 管线监控 DAG P11a.5 预演成片
        #                        节点 match idIncludes 'roughcut' 的数据源)
        #   roughcut_meta  dict(mix/bed 统计) → script 概览 + expand
        "p11a5": [
            ("ambient_stems", "环境音床", "audio", True),
            ("preview_mix_path", "预演混音", "audio", False),
            ("roughcut_path", "预演成片", "video", False),
            ("roughcut_meta", "预演元数据", "script", True),
        ],
        "p11b": [
            # P11b 最终渲染 —— video_clips（20 个 shot 的成片）。这是时间轴
            # StoryboardTimeline 渲染所需的 mp4 artifact 来源。lip_sync_reports
            # 为口型同步审计（script 类型）。
            ("video_clips", "最终视频", "video", False),
            ("lip_sync_reports", "口型同步报告", "script", False),
        ],
        "p11c": [
            # P11c 视频智能质检 (qwen-eye) —— p11c_video_qc.py run() 返回
            # result["outputs"] = {"video-qc": slot}（dict：per_shot 判定 +
            # summary）。JSON 类 slot（非文件），与 P09b ("shot-audit", ...)
            # 契约同构：单 dict → 单 script 概览节点。
            ("video-qc", "视频质检", "script", True),
        ],
        "p12": [
            ("master_timeline", "时间线 EDL", "script", False),
            ("audio_stems", "音轨", "audio", False),
            # Notion §5c/§5d 独立音轨占位（phase 尚未 emit → 跳过）。
            ("foley_stems", "Foley音轨", "audio", False),
            ("bgm_tracks", "BGM音轨", "audio", False),
        ],
        # P12 split (2026-08-09) — p12a/p12b 实际 output 结构（对照
        # p12a_timeline_composition.py / p12b_audio_composition.py 的
        # result["outputs"]）：
        #   p12a: master_timeline dict {edl, total_duration_sec, resolution,
        #         video_concat_path} + 可能的 video_concat/final_video 等占位
        #   p12b: audio_stems dict {bgm, sfx, voice, mix} + final_video
        #         {video_path, resolution}（成片视频路径）
        # 此前仅旧 "p12" 条目存在 → _phase_prefix("p12a_...") = "p12a" 查表
        # 落空，P12 全部产物在画布上静默消失（review A-1 回归）。
        "p12a": [
            ("master_timeline", "时间线 EDL", "script", False),
            # video_concat 是确定性 ffmpeg 产物（assets/P12/video_concat.mp4）
            # ——p12b 混音的视频床。
            ("video_concat", "视频拼接床", "video", False),
        ],
        "p12b": [
            # mix.master_path 指向 master.mp4（含音轨的成片），p12b 的核心
            # 交付物；master_timeline 是只读输入（不重复建节点）。
            ("audio_stems", "音轨", "audio", False),
            ("final_video", "合成成片", "video", False),
        ],
        "p13": [
            ("master_mp4", "成片", "video", False),
            ("delivery_package", "交付包", "script", False),
            # master-qc (qwen-eye, 2026-08-16) — advisory 母带终审（五维判定
            # dims + verdict）。JSON 类 slot，与 P11c video-qc 契约同构：
            # 单 dict → 单 script 概览节点。advisory——不加 GATE_EDGES。
            ("master-qc", "母带终审", "script", True),
        ],
        "p14": [
            # Post-delivery quality audit. P14's run() returns
            # result["outputs"] = {"quality-audit": audit_report} — a single
            # dict key (mirrors the P09b/P10c micro-gate ``*-audit`` pattern).
            # The previous three keys (audit_findings / audit_report /
            # recommendations) never matched the emitted key, so the entire
            # quality audit was silently dropped from the canvas (0 nodes).
            # Verified against p14_quality_audit.py run() return value.
            ("quality-audit", "质量审计", "script", True),
        ],
        "p15": [
            # P15 跨集反思 —— p15_feedback.py run() 返回
            # result["outputs"] = {"feedback-log": reflection}（dict：含
            # rejected_phases / rejection_events / lesson_count 等）。
            # _PHASE_OUTPUT_MAP 此前无 p15 键 → 整个跨集反思产出被丢弃、
            # 画布不可见（C1 audit）。expand=True：除概览节点外，把
            # rejected_phases / rejection_events / lessons 等 sublist 各展开
            # 为子节点，反思细节逐条可见。
            ("feedback-log", "跨集反思", "script", True),
        ],
    }

    # Per-output assetType override (additive on top of _PHASE_TYPE_MAP).
    # Keyed by (phase_prefix, output_key) so a single phase can emit artifacts
    # with different assetType values (e.g. P01 emits both "topic" and "hook"
    # artifacts). When absent, fall back to the phase-level assetType from
    # _PHASE_TYPE_MAP. The save-v2 schema (canvasAssetSchema.ts:114) accepts
    # any non-empty string for script-node assetType — no enum constraint.
    _PHASE_ASSET_TYPE_OVERRIDE: dict[tuple[str, str], str] = {
        ("p01", "topic_kernel"): "topic",
        ("p01", "hook_design"): "hook",
        # ("p01", "retention_engineering") removed alongside its
        # _PHASE_OUTPUT_MAP entry (see audit note above).
    }

    # Keys whose values are lists of artifacts (images, clips, etc.).
    _ARTIFACT_LIST_KEYS: tuple[str, ...] = (
        "characters", "scenes", "shots", "clips", "tracks",
        "stems", "images", "videos", "audios", "voice_clips",
        "bgm_cues", "sfx_cues", "storyboards",
    )

    # ── W3: fallback dedup of alias list keys ─────────────────────────
    # When the generic fallback (step 2 below) expands a list key that is a
    # SYNONYM of a key already declared in _PHASE_OUTPUT_MAP, it produced
    # duplicate child nodes. Concretely: p07_scene_generation emits an
    # ``images`` list as a filesystem-fallback alias of ``scene_images``; both
    # ``images`` (in _ARTIFACT_LIST_KEYS) and ``scene_images`` (declared in the
    # p07 output map) then became canvas nodes for the same underlying images.
    # Map (phase_prefix, alias_list_key) → canonical output key. The fallback
    # skips the alias when its canonical key is already declared for the phase.
    _ALIAS_SKIP: dict[tuple[str, str], str] = {
        ("p07", "images"): "scene_images",
    }

    # ── C4: save-v2 Gate B field-name normalization + required-field guard ──
    # Pipeline domain field names that map to the canonical param names the
    # canvas save-v2 Gate B schema (canvasAssetSchema.ts) validates. Applied in
    # _build_artifact_node so media nodes carry the right keys before the
    # required-field check. Aliases only FILL a canonical key when it is absent
    # (never overwrite a real canonical value).
    _FIELD_ALIASES: dict[str, str] = {
        "shot_intent": "shot_type",
        "shot_scale": "shot_type",
        "framing": "shot_type",
        "dur": "duration_sec",
        "duration": "duration_sec",
        "res": "resolution",
    }

    # save-v2 Gate B required params per media node type (canvasAssetSchema.ts).
    # audio/video filePath is already guaranteed by the media-node guard in
    # _build_artifact_node; this map covers the OTHER required structured
    # fields. A media node missing any of these is degraded to "script"
    # (label+description only) to avoid save-v2 rejecting the ENTIRE graph
    # (save-v2.ts:50-57 — any single node failing fails the whole batch). The
    # original type is preserved in data._original_type for frontend reference.
    _GATE_B_REQUIRED: dict[str, list[str]] = {
        "audio": ["shot_id", "engine", "duration_sec"],
        "video": ["shot_id", "engine", "duration_sec", "resolution"],
        "storyboard": ["shot_id", "shot_type", "duration_sec"],
    }

    # Keys to skip when expanding dict outputs (metadata, not content).
    _SKIP_KEYS: frozenset[str] = frozenset({
        "expert", "episode", "created_at", "skill_version",
        "skill_versions", "methodology_note", "type", "version",
        "format_note", "metadata", "generation_notes",
        "tts_engine", "voice_quality_targets",
        "downstream_consumers", "film_title", "film_brand",
        "timeline_structure", "snyder_validation",
        "car_as_character", "style",
    })

    # Metadata noise keys to filter from artifact node data.
    # These are residual ``_parse_delegate_output`` / runner bookkeeping keys
    # (``_agent_name``, ``episode_id``, ``_error``, ``_seq``, ...) that leak
    # into phase outputs and create noise child nodes + combinatorial edge
    # blowup in _TEXT_PHASE_CHAIN (MODERATE #3). They carry no creative value
    # and clutter the canvas — filter them during child-node expansion AND
    # when matching reference-link endpoints.
    _METADATA_KEY_FILTER: frozenset[str] = frozenset({
        "_agent_name", "_seq", "_error", "_retry_count",
        "_delegate_trace", "_source_skill", "_delegate_id",
        "_parse_warnings", "episode_id", "episode",
        "phase_id", "phase", "timestamp", "ts", "run_id",
        "_node_id", "_origin_phase",
        # 生成溯源 bookkeeping（p02 story-framework 槽 value 顶层带
        # provenance{model,session,…}——dict 展开会产纯噪音子节点）。
        "provenance",
    })

    @staticmethod
    def _synthesize_child_label(
        sub_item: dict[str, Any],
        default_label: str,
        sub_key: str,
        j: int,
    ) -> str:
        """Derive a human-readable label for a list child item.

        背景（ep-ccport-test01 p04 首考）：scene_costume_turnarounds /
        l3_costumes 子项只有 {character, scene/costume, path}，没有
        name/label → 兜底标签「角色资产.scene_costume_turnarounds 1」
        直接进了画布节点 label 和 o_assets.name（资管页面显示裸键名）。

        合成链：name/label/title → character·{costume|scene} 预览 →
        媒体路径 basename → 序号兜底（原行为）。仅用通用语义键，不写
        phase 专属 if-else。
        """
        for k in ("name", "label", "title"):
            v = sub_item.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()[:60]
        ch = sub_item.get("character")
        if isinstance(ch, str) and ch.strip():
            ch = ch.strip()
            for ctx_key, cap in (("costume", 24), ("scene", 20)):
                ctx = sub_item.get(ctx_key)
                if isinstance(ctx, str) and ctx.strip():
                    preview = ctx.strip().split("（")[0][:cap]
                    return f"{ch}·{preview}"[:60]
            return ch[:60]
        for pk in ("path", "filePath", "turnaround_sheet", "audio_path"):
            p = sub_item.get(pk)
            if isinstance(p, str) and p.strip():
                base = os.path.basename(p.strip())
                if base:
                    return os.path.splitext(base)[0][:60]
        return f"{default_label}.{sub_key} {j+1}"

    def _synthesize_child_description(
        self,
        out_key: str,
        item: dict[str, Any],
    ) -> str:
        """Synthesize a human-readable description for a child artifact node.

        Child nodes (e.g. hook candidates, character anchors) often carry
        rich structured fields but no ``description`` key. Without this,
        the canvas detail panel falls back to showing the label text twice.

        This extracts the most informative fields based on ``out_key`` and
        builds a concise description string (max ~200 chars).
        """
        parts: list[str] = []

        # Hook candidates: hook_type + opening_line + visual_concept
        if out_key == "hook_design" or "hook_type" in item:
            ht = item.get("hook_type", "")
            ol = item.get("opening_line", "")
            vc = item.get("visual_concept", "")
            hs = item.get("hook_strength", 0)
            if ht:
                parts.append(f"类型: {ht}")
            if hs:
                parts.append(f"力量: {hs}")
            if ol:
                parts.append(f"台词: {str(ol)[:60]}")
            if vc:
                parts.append(f"视觉: {str(vc)[:80]}")

        # Character anchors: archetype + role + age_range
        elif "archetype" in item or "role" in item:
            ar = item.get("archetype", "")
            rl = item.get("role", "")
            ag = item.get("age_range", "")
            desc = item.get("description", "")
            if ar:
                parts.append(f"原型: {ar}")
            if rl:
                parts.append(f"角色: {rl}")
            if ag:
                parts.append(f"年龄: {ag}")
            if desc:
                parts.append(str(desc)[:80])

        # Generic fallback: try common description-like fields
        else:
            for k in ("description", "title", "logline", "content",
                       "prompt", "summary", "text"):
                v = item.get(k)
                if v and isinstance(v, str) and len(v) > 5:
                    parts.append(v[:150])
                    break

        return " · ".join(parts)

    @staticmethod
    def _derive_ai_score(val: Any) -> dict[str, Any] | None:
        """72-02 (v3.2 F28/QVR-03):slot 体的审计分数 → V2 aiScore。

        识别两形(真实 ep-zhongkui-ep01 样本实证):
          - p03 audit-report:顶层 ``scores{dim: 0..1}`` + ``total_score``(0..1);
          - p14 quality-audit:nested ``quality_audit.dimensions{dim: {score: 0..100}}``
            + ``overall_score``(0..100)。
        分值统一钳制 0..1(p14 /100)。不识别返回 None(非审计 slot 零污染,
        不伪造 overall)。
        """
        if not isinstance(val, dict):
            return None
        scores = val.get("scores")
        if isinstance(scores, dict) and scores:
            dims: dict[str, float] = {}
            for k, v in scores.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    dims[str(k)] = max(0.0, min(1.0, float(v)))
            if len(dims) >= 3:
                total = val.get("total_score")
                overall = (
                    max(0.0, min(1.0, float(total)))
                    if isinstance(total, (int, float)) and not isinstance(total, bool)
                    else sum(dims.values()) / len(dims)
                )
                return {"overall": round(overall, 4), "dimensions": dims}
        qa = val.get("quality_audit")
        if isinstance(qa, dict):
            d2 = qa.get("dimensions")
            if isinstance(d2, dict) and d2:
                dims2: dict[str, float] = {}
                for k, v in d2.items():
                    s = v.get("score") if isinstance(v, dict) else v
                    if isinstance(s, (int, float)) and not isinstance(s, bool):
                        dims2[str(k)] = max(0.0, min(1.0, float(s) / 100.0))
                if len(dims2) >= 3:
                    ov = qa.get("overall_score")
                    overall2 = (
                        max(0.0, min(1.0, float(ov) / 100.0))
                        if isinstance(ov, (int, float)) and not isinstance(ov, bool)
                        else sum(dims2.values()) / len(dims2)
                    )
                    return {"overall": round(overall2, 4), "dimensions": dims2}
        return None

    def _build_output_summary_description(
        self,
        out_key: str,
        default_label: str,
        val: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """Build description + structured fields for an expanded-dict summary node.

        The default ``val.get("description")`` path returns an empty string
        for P03 outputs (script / audit_report) because neither carries a
        ``description`` key — the script carries ``title`` and the audit
        carries ``total_score`` / ``predicted_completion_band``. This helper
        extracts those fields into a concise description so the canvas
        detail panel renders meaningful content instead of the bare label.

        MODERATE #1 (audit_report score visible) + MODERATE #2 (script title
        visible) are both addressed here.

        2026-08-18 同形化：改为与 ``_enrich_p01_summary`` 一致地返回
        ``(description, extra_fields)``。此前概览节点 _sum_extra={}——
        P03 script 产出 mcmahon_arc/total_duration_sec/format、映射表也有
        mcmahon_arc→mcmahonArc 条目，但概览 artifact 不带任何字段，映射层
        无从翻译 → 前端 StructuredFieldPanel（script 6 字段）永远空。
        extra 里的 snake_case 原字段进 artifact 后由 _apply_schema_mappings
        翻译成 camelCase；camelCase 双写仅加在映射错位（python_key 与产出
        键名不一致）的 totalDuration 上（同 p01 修复 #4 根因）。
        """
        parts: list[str] = []
        extra: dict[str, Any] = {}

        # Start from an explicit description/title/logline if present.
        for k in ("description", "title", "logline"):
            v = val.get(k)
            if isinstance(v, str) and v.strip():
                parts.append(v.strip()[:120])
                break

        # P03 script: show title + structural metadata.
        if out_key == "script":
            title = val.get("title")
            if isinstance(title, str) and title.strip():
                extra["title"] = title
            genre = val.get("genre")
            if genre:
                parts.append(f"类型: {genre}")
                extra["genre"] = genre
            fmt = val.get("format")
            if isinstance(fmt, str) and fmt.strip():
                extra["format"] = fmt
            scenes = val.get("scenes")
            if isinstance(scenes, list) and scenes:
                parts.append(f"{len(scenes)} 场戏")
            dur = val.get("total_duration_sec")
            if isinstance(dur, (int, float)):
                parts.append(f"{dur}s")
                extra["total_duration_sec"] = str(dur)
                # camelCase 双写：生成映射表 totalDuration 的 python_key 是
                # total_duration / duration_sec，与产出键 total_duration_sec
                # 永远 miss（p01 修复 #4 同根因）。
                extra["totalDuration"] = str(dur)
            arc = val.get("mcmahon_arc") or val.get("story_arc")
            if arc:
                parts.append(f"弧线: {arc}")
                # raw 字段进 artifact → _apply_schema_mappings 翻译成
                # mcmahonArc（p03 映射表有条目）。story_arc 变体没有映射
                # 条目，统一挂在 mcmahon_arc 键下让它也被翻译。
                extra["mcmahon_arc"] = arc

        # P03 audit_report: show total_score + completion band.
        elif out_key == "audit_report":
            ts = val.get("total_score")
            if isinstance(ts, (int, float)):
                parts.append(f"总分: {ts}")
                extra["total_score"] = ts
                extra["score"] = ts
            band = val.get("predicted_completion_band")
            if band:
                parts.append(f"完成度: {band}")
                extra["predicted_completion_band"] = band
            scores = val.get("scores")
            if isinstance(scores, dict) and scores:
                # Compact: drama=0.7,rhythm=0.6,...
                score_strs = [
                    f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}"
                    for k, v in scores.items()
                    if isinstance(v, (int, float))
                ]
                if score_strs:
                    parts.append(", ".join(score_strs[:5]))
            weaknesses = val.get("weaknesses")
            if isinstance(weaknesses, list):
                parts.append(f"问题: {len(weaknesses)} 项")

        description = " · ".join(parts)[:200] if parts else str(
            val.get("description") or val.get("title") or default_label,
        )[:200]
        return description, extra

    # ── dict 子节点展开护栏（2026-08-18）──────────────────────────────
    # description 参与拼接的最大叶子数（超过截断，防超长 description）。
    _DICT_DESC_MAX_FIELDS = 8
    # description 单值截断长度。
    _DICT_DESC_VAL_CAP = 60
    # data.content 全文上限（script 节点 content 无 schema 长度限制，但
    # 要防 LLM 输出极端长时把 canvas_nodes.data 行撑爆）。
    _DICT_CONTENT_CAP = 4000
    # data 透出的最大标量字段数（防 data 膨胀）。
    _DICT_DATA_MAX_FIELDS = 12
    # 嵌套数值 dict（score map）在 description 里展示的前 N 项。
    _DICT_NUMERIC_MAP_PREVIEW = 5

    def _summarize_structured_dict(
        self, d: dict[str, Any],
    ) -> tuple[list[str], str, dict[str, Any]]:
        """Flatten one structured dict into description/content/data parts.

        背景（ep-ccport-test01 p01 审计）：_extract_artifacts 的子键展开
        只有 list / str / 纯数值 dict 三个分支，嵌套 str dict
        （emotion_spectrum / platform_fit / charlie_selection /
        reversal_blueprint / frame_breakdown_3sec …）被静默丢弃——
        ep-ccport-test01 p01 丢了 10 个结构化字段。

        深度护栏：本层标量叶子直接展示；一层嵌套 dict 只做压缩摘要
        （数值映射取前 N 项、str 映射取首条预览、更深结构取计数），
        绝不递归产节点——每个 dict key 只产 1 个子节点，节点数上界 =
        输出 key 数，无爆炸面。嵌套结构全文进 content（供详情面板
        「正文」区完整查看），标量叶子同时透传进 node data（前端
        RawDataSection 渲染穿透字段，但不渲染嵌套 dict）。

        Returns:
            (desc_parts, content_text, scalar_fields)
        """
        desc_parts: list[str] = []
        content_parts: list[str] = []
        scalars: dict[str, Any] = {}
        for k, v in d.items():
            if k in self._METADATA_KEY_FILTER or k in self._SKIP_KEYS:
                continue
            if isinstance(v, str):
                vs = v.strip()
                if not vs:
                    continue
                desc_parts.append(f"{k}: {vs[:self._DICT_DESC_VAL_CAP]}")
                content_parts.append(f"{k}: {vs}")
                if len(scalars) < self._DICT_DATA_MAX_FIELDS:
                    scalars[k] = v
            elif isinstance(v, bool):
                desc_parts.append(f"{k}={'是' if v else '否'}")
                content_parts.append(f"{k}: {'是' if v else '否'}")
            elif isinstance(v, (int, float)):
                desc_parts.append(f"{k}={v}")
                content_parts.append(f"{k}={v}")
                if len(scalars) < self._DICT_DATA_MAX_FIELDS:
                    scalars[k] = v
            elif isinstance(v, dict) and v:
                if all(
                    isinstance(nv, (int, float)) and not isinstance(nv, bool)
                    for nv in v.values()
                ):
                    # 数值映射（e.g. emotion_spectrum.scores）：
                    # desc 取前 N 项，content 全量。
                    _pairs = [
                        f"{dk}={dv}"
                        for dk, dv in list(v.items())[
                            :self._DICT_NUMERIC_MAP_PREVIEW
                        ]
                    ]
                    _more = "…" if len(v) > self._DICT_NUMERIC_MAP_PREVIEW else ""
                    desc_parts.append(
                        f"{k}: {', '.join(_pairs)}{_more}"
                    )
                    content_parts.append(
                        f"{k}: "
                        + ", ".join(f"{dk}={dv}" for dk, dv in v.items())
                    )
                elif all(
                    isinstance(nv, str) and nv.strip() for nv in v.values()
                ):
                    # str 映射（e.g. top_axes_rationale）：
                    # desc 取首条预览，content 全量。
                    _fk, _fv = next(iter(v.items()))
                    desc_parts.append(
                        f"{k}({len(v)}条): {_fk} {_fv[:40]}"
                    )
                    content_parts.append(
                        f"{k}: " + "; ".join(
                            f"{dk}={dv}" for dk, dv in v.items()
                        )
                    )
                else:
                    # 更深结构（dict-of-dict，e.g. frame_breakdown_3sec）：
                    # desc 只报段数，content JSON 全量。
                    desc_parts.append(f"{k}: {len(v)} 段")
                    content_parts.append(
                        f"{k}: {json.dumps(v, ensure_ascii=False)}"
                    )
            elif isinstance(v, list):
                desc_parts.append(f"{k}: {len(v)} 项")
                content_parts.append(
                    f"{k}: {json.dumps(v, ensure_ascii=False)}"
                )
        return desc_parts, "\n".join(content_parts), scalars

    def _enrich_p01_summary(
        self,
        out_key: str,
        val: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """Synthesize a meaningful description + structured fields for P01
        summary nodes.

        P01's expert output has rich nested fields (creative_constraints,
        hook_type, hook_strength, opening_line) that the generic
        ``val.get("description")`` path silently drops. This helper
        extracts those fields and builds a human-readable description so
        the canvas detail panel renders useful content instead of an
        empty "(概览)" placeholder.

        Three-layer fix per Kai's principle (reference 有框架但 goal
        template 不引用 → 输出退化): this is the runtime-extraction layer
        that protects against LLM output format variance — the expert
        sometimes embeds creative_constraints under topic_kernel and
        sometimes emits it at the top level. We handle both.

        Args:
            out_key: Output key (``"topic_kernel"`` or ``"hook_design"``).
            val: The dict value from result.outputs.

        Returns:
            ``(description, extra_fields)`` where description is a
            guaranteed-non-empty string and extra_fields carries
            structured params to attach to the summary artifact.
        """
        extra: dict[str, Any] = {}

        if out_key == "topic_kernel":
            # creative_constraints may be embedded (P01 manifest writer
            # nests it) OR top-level in the expert output.
            cc = val.get("creative_constraints")
            if not isinstance(cc, dict):
                cc = {}
            genre = cc.get("genre") or val.get("genre") or ""
            tone = cc.get("tone") or val.get("tone") or ""
            duration = (
                cc.get("total_duration_sec")
                or val.get("total_duration_sec")
                or 0
            )
            comedy_subtype = (
                cc.get("comedy_subtype")
                or val.get("comedy_subtype")
                or ""
            )
            topic_nucleus = val.get("topic_nucleus") or ""

            parts: list[str] = []
            if genre:
                parts.append(f"类型: {genre}")
                extra["genre"] = genre
            if tone:
                parts.append(f"基调: {tone}")
                extra["tone"] = tone
            if duration:
                parts.append(f"时长: {duration}s")
                extra["total_duration_sec"] = str(duration)
                # camelCase 双写（2026-08-18）：前端 script 结构化字段表
                # （constants.ts NODE_SCHEMA.script）读 totalDuration，而生成
                # 映射表里 totalDuration 的 python_key 是 total_duration
                # （管线产出的是 total_duration_sec，identity 占位让映射
                # 永远 miss）→ 双写保证前端「总时长」字段有值；
                # snake_case 副本保留（save-v2 数值转 str 契约 + 既有读取方）。
                extra["totalDuration"] = str(duration)
            if comedy_subtype:
                parts.append(f"喜剧亚型: {comedy_subtype}")
                extra["comedy_subtype"] = comedy_subtype
            if topic_nucleus:
                parts.append(f"选题核: {str(topic_nucleus)[:80]}")

            description = " · ".join(parts) or str(
                val.get("description") or "选题核 (topic-kernel)"
            )
            # Pass through any additional structured scalar fields the expert
            # emits (narrative_structure, etc.) so the schema mapping layer
            # can translate them to canvas_keys (mcmahonArc). Skip the
            # fields we already extracted + _SKIP_KEYS metadata + dict/list
            # values that are handled by the expand path.
            _already_extracted = {
                "creative_constraints", "genre", "tone",
                "total_duration_sec", "comedy_subtype", "topic_nucleus",
                "description", "title", "logline",
            }
            for k, v in val.items():
                if k in _already_extracted or k in self._SKIP_KEYS:
                    continue
                if v is None or v == "":
                    continue
                if isinstance(v, (dict, list)):
                    continue
                extra.setdefault(k, v)
            return description, extra

        if out_key == "hook_design":
            # The expert output has 3 format variants:
            #   1. flat: hook_type/opening_line at top level
            #   2. candidates[]: array of hooks, selected_hook_index picks one
            #   3. selected_hook + alternative_hooks: split structure
            # Extract the selected/primary hook from any variant.
            selected_hook: dict[str, Any] = {}
            candidates = val.get("candidates") or []
            if isinstance(candidates, list) and candidates:
                sel_idx = val.get("selected_hook_index", 0)
                if isinstance(sel_idx, int) and 0 <= sel_idx < len(candidates):
                    selected_hook = candidates[sel_idx] or {}
                if not selected_hook:
                    # Fallback: first candidate
                    selected_hook = candidates[0] or {}
            if not selected_hook:
                # Variant 3: selected_hook is an ID string + alternative_hooks
                sel_id = val.get("selected_hook", "")
                alts = val.get("alternative_hooks") or []
                if isinstance(sel_id, str) and sel_id and isinstance(alts, list):
                    for alt in alts:
                        if isinstance(alt, dict) and alt.get("id") == sel_id:
                            selected_hook = alt
                            break
            if not selected_hook:
                # Variant 1: flat — treat val itself as the hook
                # (only if it has hook_type or opening_line)
                if val.get("hook_type") or val.get("opening_line"):
                    selected_hook = val

            hook_type = selected_hook.get("hook_type") or val.get("hook_type") or ""
            hook_intensity = selected_hook.get("hook_intensity") or val.get("hook_intensity") or 0
            hook_strength = selected_hook.get("hook_strength") or val.get("hook_strength") or 0
            opening_line = selected_hook.get("opening_line") or val.get("opening_line") or ""
            visual_concept = selected_hook.get("visual_concept") or val.get("visual_concept") or ""

            parts: list[str] = []
            if hook_type:
                parts.append(f"类型: {hook_type}")
                extra["hook_type"] = hook_type
            if hook_intensity:
                parts.append(f"强度: {hook_intensity}")
                extra["hook_intensity"] = hook_intensity
            if hook_strength:
                parts.append(f"力量: {hook_strength}")
                extra["hook_strength"] = hook_strength
            if opening_line:
                parts.append(f"开场: {str(opening_line)[:80]}")
                extra["opening_line"] = opening_line
            if visual_concept:
                parts.append(f"视觉: {str(visual_concept)[:80]}")

            description = " · ".join(parts) or str(
                val.get("description") or "钩子设计 (hook-design)"
            )
            # Same passthrough for unknown scalar fields (e.g. narrative_structure).
            _already_extracted = {
                "hook_type", "hook_intensity", "hook_strength",
                "opening_line", "visual_concept",
                "description", "title", "logline",
            }
            for k, v in val.items():
                if k in _already_extracted or k in self._SKIP_KEYS:
                    continue
                if v is None or v == "":
                    continue
                if isinstance(v, (dict, list)):
                    continue
                extra.setdefault(k, v)
            return description, extra

        # Fallback for other P01 output keys (e.g. retention_engineering).
        description = str(
            val.get("description")
            or val.get("title")
            or val.get("logline", "")
        )[:200]
        return description, extra

    def _extract_artifacts(
        self,
        phase_id: str,
        result: dict[str, Any],
        workdir: str = "",
        episode_id: str = "",
    ) -> list[dict[str, Any]]:
        """Extract artifact items from ``result.outputs``.

        Uses ``_PHASE_OUTPUT_MAP`` to find phase-specific output keys,
        then expands each output into one or more artifact nodes.

        For list outputs: each list item becomes a child node.
        For dict outputs with ``expand_subkeys=True``: top-level keys
        that contain lists become child nodes, and the dict itself
        becomes a summary node.
        For scalar/dict outputs without expansion: the output becomes
        a single summary node.

        Each artifact dict has:
            ``{id, label, type, thumbnailUrl?, filePath?, selected?, description?}``
        """
        outputs = result.get("outputs") or {}
        if not isinstance(outputs, dict):
            outputs = {}

        phase_prefix = _phase_prefix(phase_id)
        output_specs = self._PHASE_OUTPUT_MAP.get(phase_prefix, [])

        # ── P04 bible lookup: merge structured fields from character_bible ──
        # character_assets sublists (l1_anchors, l4_props, etc.) only contain
        # {name, turnaround_sheet/path, crops/description}.  The structured
        # fields (archetype, role, age_range) live in character_bible.characters.
        # Build a lookup by index (bible order == anchor order) and by fuzzy
        # name match (English slug in assets vs. Chinese name in bible).
        bible_lookup: dict[str, dict[str, Any]] = {}  # slug → {archetype, role, age_range, characterId}
        if phase_prefix == "p04":
            cb = outputs.get("character_bible")
            if isinstance(cb, dict):
                chars = cb.get("characters")
                if isinstance(chars, list):
                    import re as _re
                    for idx, ch in enumerate(chars):
                        if not isinstance(ch, dict):
                            continue
                        ch_name = ch.get("name", f"char{idx}")
                        # Build slug from role English name in parentheses,
                        # falling back to index-based slug.
                        role_text = ch.get("role", "")
                        slug: str = f"char{idx}"
                        if isinstance(role_text, str):
                            m = _re.search(r"[a-z_]+", role_text)
                            if m:
                                slug = m.group(0).strip("_")
                        # Also try pinyin/slug from name
                        slug_alt = ch_name.replace(" ", "_").replace("/", "_")[:30].lower()
                        entry = {
                            "archetype": ch.get("archetype", ""),
                            "role": ch.get("role", ""),
                            "age_range": ch.get("age_range", ""),
                            "characterId": ch_name,
                            "characterCanonical": ch_name,
                            "style_prefix": ch.get("style_prefix", ""),
                            "l1_anchor": ch.get("l1_anchor", {}),
                            "species": ch.get("species", ""),
                            "_index": idx,
                            "_slug": slug,
                            "_slug_alt": slug_alt,
                        }
                        # Index multiple lookup keys
                        for key in (slug, slug_alt, ch_name, f"char{idx}"):
                            bible_lookup[key] = entry
                        # Also index by partial slug parts
                        for part in slug.split("_"):
                            if len(part) > 2:
                                bible_lookup.setdefault(part, entry)
                # ── pinyin 别名索引（2026-08-19）─────────────────────────
                # 真实 bible role 常是纯枚举（"protagonist"/"antagonist"，
                # 无括号拼音）→ slug 提取拿不到 "xiaozhou"/"coffeemachine"。
                # 拼音名只出现在 l1_anchors[].name。anchors 与 bible 按序
                # 对齐是既有契约（下方 index fallback 同一假设），据此把
                # anchor name 建为 bible 别名——服装子项（无 name 只有
                # character="coffeemachine"）才能正确归属角色。
                ca = outputs.get("character_assets")
                anchors = (
                    ca.get("l1_anchors") if isinstance(ca, dict) else None
                )
                if isinstance(anchors, list):
                    for ai, anchor in enumerate(anchors):
                        aname = (
                            anchor.get("name") if isinstance(anchor, dict)
                            else None
                        )
                        if not (isinstance(aname, str) and aname.strip()):
                            continue
                        alias_entry = bible_lookup.get(f"char{ai}")
                        if alias_entry:
                            bible_lookup.setdefault(aname.strip(), alias_entry)

        artifacts: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        def _add_artifact(art_id: str, label: str, art_type: str = "asset",
                          **extra: Any) -> None:
            if art_id in seen_ids:
                # Kai 2026-08-16: 冗余变体后缀标准化 _v{n}（替代旧 -N 去重后缀）
                n = 2
                while f"{art_id}_v{n}" in seen_ids:
                    n += 1
                art_id = f"{art_id}_v{n}"
            seen_ids.add(art_id)
            art: dict[str, Any] = {"id": art_id, "label": label[:100], "type": art_type}
            art.update(extra)
            artifacts.append(art)

        # ── 0. P04 声纹资产同步：从 o_assets 表读取 type='voice' 的声纹资产 ──
        # 声纹通过 VoiceDesign API 独立产出（非 KMC phase output），需要显式同步。
        if phase_prefix == "p04":
            try:
                db_path = _locate_canvas_db()
                _proj = self._client._project_id if self._client else None
                if db_path and _proj:
                    import sqlite3 as _sql
                    _conn = _sql.connect(db_path)
                    _conn.row_factory = _sql.Row
                    # D-4 声纹扇出修复（2026-08-16）：type='voice' 在 o_assets 里
                    # 混住两类行——VoiceDesign 参考音频（meta 带 voice_print）
                    # 和 P10 TTS 台词片段（meta 带 shot_id，每 shot 一条）。
                    # 旧查询无去重，demo-pixar 23 条 TTS 片段全部进 P04 fanout
                    # （_add_artifact 的 _v{n} 防撞后缀把它们变成
                    # a-voice_design-amao-1…-13），每节点 filePath 是该 shot 的
                    # 台词 wav——「声纹设计」语义完全失真且随 TTS 片段数线性膨胀。
                    # 修法：按 characterId 去重取首条（isPrimaryView DESC, id ASC），
                    # 每角色只产 1 个声纹节点。SQL 窗口不可用（sqlite 版本差异）
                    # 用 ORDER BY + Python 侧首见去重，语义等价且保留 JOIN 结构。
                    _rows = _conn.execute(
                        # filePath lives on o_image (joined via o_assets.imageId),
                        # NOT on o_assets — the pre-JOIN query raised
                        # "no such column: filePath" on every P04 sync
                        # (ep-demo-pixar B.3). NULL filePath falls back to
                        # meta.ref_audio_path below.
                        "SELECT a.id, a.name, a.characterId, a.type, a.meta, "
                        "i.filePath, a.isPrimaryView, a.state "
                        "FROM o_assets a "
                        "LEFT JOIN o_image i ON a.imageId = i.id "
                        "WHERE a.projectId = ? AND a.type = 'voice' "
                        "AND a.episodesId = ? "
                        "ORDER BY a.isPrimaryView DESC, a.id ASC",
                        (_proj, self._client._episodes_id),
                    ).fetchall()
                    _conn.close()
                    _seen_chars: set[str] = set()
                    _synced = 0
                    for _r in _rows:
                        _meta = {}
                        if _r["meta"]:
                            try:
                                _meta = json.loads(_r["meta"])
                            except Exception:
                                pass
                        _char = _r["characterId"] or "unknown"
                        if _char in _seen_chars:
                            continue  # D-4: 同角色只保留首条（isPrimaryView 优先）
                        _seen_chars.add(_char)
                        _synced += 1
                        _add_artifact(
                            f"voice_design-{_char}",
                            f"{_char} 声纹",
                            "audio",
                            assetType="voice",
                            # 72-04 (v3.2 F30/QVR-07):metaSub 键对齐——剧场
                            # 双击判定读 d.metaSub(voice_print/voice_profile →
                            # 声纹两级试听),此前节点 data 不带该键,生产库
                            # metaSub 命中恒 0。
                            metaSub=_meta.get("subtype"),
                            characterId=_char,
                            filePath=_r["filePath"] or _meta.get("ref_audio_path"),
                            voiceId=_meta.get("voice_id"),
                            instruct=_meta.get("instruct"),
                            modality="audio",
                            isPrimaryView=_r["isPrimaryView"],
                            state=_r["state"] or "active",
                        )
                    logger.info(
                        "canvas_sync: synced %d/%d voice assets from o_assets "
                        "for P04 (deduped per characterId)",
                        _synced, len(_rows),
                    )
            except Exception as _e:
                logger.warning("canvas_sync: voice asset sync failed: %s", _e)

        # ── 1. Phase-specific outputs from _PHASE_OUTPUT_MAP ────────
        for out_key, default_label, canvas_type, expand in output_specs:
            val = outputs.get(out_key)
            if val is None:
                continue

            # ── p12b audio_stems 四轨展开（2026-08-19）────────────────
            # audio_stems 是 dict {bgm, sfx, voice, mix}，此前走「dict 不
            # 展开」分支只落 1 个容器节点 —— BGM/环境音效/人声合轨/混音母带
            # 从不成为独立 audio 节点，bgm/foley/mix 泳道、时间线音轨列、
            # 资产库树入口永远空转（bgm.wav/master.mp4 明明在盘上）。
            # 这里拆成 per-stem audio 子节点，audioType 精确落
            # bgm/foley/voice/mix（前端 migrate 按此拆 stage/泳道）。
            # duration_sec=0 = 未探测时长（schema 已放行）。
            if (isinstance(val, dict) and out_key == "audio_stems"
                    and phase_prefix in ("p12", "p12b")):
                # BGM 音轨（ComfyUI/ACE-Step 产，全片单曲）
                _bgm = val.get("bgm")
                if isinstance(_bgm, dict) and _bgm.get("path"):
                    _bgm_n = _normalize_media_fields(dict(_bgm), workdir=workdir)
                    _add_artifact(
                        "audio_stems-bgm", "BGM 音轨", "audio",
                        filePath=_bgm_n.get("filePath"),
                        audioType="bgm",
                        shot_id="master", engine="comfyui",
                        duration_sec=0,
                        clip_type="bgm",
                        description=" · ".join(filter(None, [
                            "BGM 音轨",
                            str(_bgm.get("mood") or ""),
                            f"{_bgm['bpm']} BPM" if _bgm.get("bpm") else "",
                        ])),
                    )
                # 环境音效 stems（LTX V2A 产，逐 shot）
                _sfx = val.get("sfx")
                if isinstance(_sfx, list):
                    for _i, _s in enumerate(_sfx):
                        if not isinstance(_s, dict) or not _s.get("path"):
                            continue
                        _sn = _normalize_media_fields(dict(_s), workdir=workdir)
                        _sid = str(_sn.get("shot_id") or f"{_i}")
                        _add_artifact(
                            f"audio_stems-sfx-{_sid}", f"环境音效 {_sid}", "audio",
                            filePath=_sn.get("filePath"),
                            audioType="foley",
                            shot_id=_sid, engine="ltx-v2a",
                            duration_sec=0,
                            clip_type="sfx",
                            description=" · ".join(filter(None, [
                                "环境音效", str(_sn.get("effect") or ""),
                            ])),
                        )
                # 人声合轨（p10 旁白/对白 pairwise 混成 voice_track）
                _voice = val.get("voice")
                if isinstance(_voice, dict) and _voice.get("path"):
                    _vn = _normalize_media_fields(dict(_voice), workdir=workdir)
                    _add_artifact(
                        "audio_stems-voice", "人声合轨", "audio",
                        filePath=_vn.get("filePath"),
                        audioType="voice",
                        shot_id="master", engine="ffmpeg",
                        duration_sec=0,
                        clip_type="voice_mix",
                        description="人声合轨" + (
                            f" · mix_level {_voice['mix_level']}"
                            if _voice.get("mix_level") is not None else ""),
                    )
                # 混音母带（两步 pairwise 的终产物；master_path 优先）
                _mix = val.get("mix")
                if isinstance(_mix, dict):
                    _mixd = dict(_mix)
                    _mp = _mixd.get("master_path") or _mixd.get("path")
                    if _mp:
                        _mixd["path"] = _mp
                        _mixd = _normalize_media_fields(_mixd, workdir=workdir)
                        _add_artifact(
                            "audio_stems-mix", "混音母带", "audio",
                            filePath=_mixd.get("filePath"),
                            audioType="mix",
                            shot_id="master", engine="ffmpeg",
                            duration_sec=0,
                            clip_type="mix",
                            description=" · ".join(filter(None, [
                                "混音母带",
                                f"LUFS {_mix['lufs']}"
                                if _mix.get("lufs") is not None else "",
                                f"DR {_mix['dynamic_range']}"
                                if _mix.get("dynamic_range") is not None else "",
                            ])),
                        )
                # 汇总容器节点仍由下方通用 dict 分支产出（bgm/sfx/voice/
                # mix 嵌套数据保留给详情面板），不在此 continue。

            if isinstance(val, list):
                # List output: each item becomes a child node.
                for i, item in enumerate(val):
                    if isinstance(item, str):
                        _add_artifact(
                            f"{out_key}-{i}",
                            f"{default_label} {i+1}",
                            canvas_type,
                        )
                    elif isinstance(item, dict):
                        # Normalize media field aliases → filePath/thumbnailUrl
                        item = _normalize_media_fields(dict(item), workdir=workdir)
                        # ── 跨 phase ID 防撞 ──────────────────────────
                        # 多个 phase 的 list output 共享同一个 artifact ID
                        # 空间 ``a-{shot_id}``。如果不加 output_key 命名空间，
                        # 后执行的 phase（如 P10 voice_clips、P11 video_clips）
                        # 会用 shot_id 覆盖先前 phase（P09 storyboard）的节点
                        # —— upsert 按 ID 替换整个节点（含 type），导致 P09 的
                        # cameraMovement / ltxPrompt / scene_ref 等丰富字段
                        # 被精简的 audio/video 数据覆盖。
                        # 修复：artifact ID 用 ``{out_key}-{shot_id}`` 格式，
                        # 保证全局唯一。shot_id 仍随 passthrough 写进 data。
                        _raw_id = (
                            item.get("shot_id") or item.get("id")
                            or item.get("name") or f"{out_key}-{i}"
                        )
                        item_id = f"{out_key}-{_raw_id}"
                        item_label = str(
                            item.get("shot_id") or item.get("label")
                            or item.get("name")
                            or item.get("title")
                            or f"{default_label} {i+1}",
                        )
                        # Passthrough ALL fields from the item dict —
                        # structured fields (camera_movement, archetype,
                        # engine, etc.) must reach _build_artifact_node
                        # so the mapping layer can translate them.
                        #
                        # NOTE: ``shot_id`` is KEPT here (not excluded) —
                        # it's used as the artifact id above, but it's ALSO
                        # a required field in the canvas storyboard schema
                        # (data.shot_id). The id/name/label fields are
                        # excluded because they map to the node's display
                        # fields, not structured params.
                        _item_extra = {
                            k: v for k, v in item.items()
                            if k not in ("id", "name", "label", "title")
                            and v is not None
                        }
                        _add_artifact(
                            item_id,
                            item_label, canvas_type,
                            _origin_key=out_key,
                            **_item_extra,
                        )

            elif isinstance(val, dict) and expand:
                # Dict output with expansion: summary node + sub-list nodes.
                # ── P01 enrichment ──
                # P01's topic_kernel/hook_design carry rich structured fields
                # that the generic ``val.get("description")`` path drops.
                # _enrich_p01_summary extracts those fields and synthesizes
                # a meaningful description. For other phases, fall back to
                # the existing logic (val.description / title / logline).
                if phase_prefix == "p01":
                    _sum_desc, _sum_extra = self._enrich_p01_summary(
                        out_key, val,
                    )
                else:
                    # 2026-08-18：概览节点此前 _sum_extra={}——即使 phase 产出
                    # 了 mcmahon_arc/total_duration_sec 等字段、映射表也有
                    # 对应条目，概览节点也一个结构化字段都不带（前端
                    # StructuredFieldPanel 空）。让 summary builder 与
                    # _enrich_p01_summary 同形，一并返回结构化字段。
                    _sum_desc, _sum_extra = (
                        self._build_output_summary_description(
                            out_key, default_label, val,
                        )
                    )
                # 72-01 (v3.2 F26/QVR-01,裁决点5a):判定数组整块保留——
                # p10c fidelity_check(含 clips[])/p11c per_shot({sid:rec})
                # 此前只走下方 sublist 展开被打散,父概览节点 data 只剩标签,
                # kap 侧 qcVerdict join(眼/耳角标)因此恒零命中(生产库
                # aud_voice-audit-summary data 无任何判定字段实证)。整块挂
                # 概览节点 data;findings 等子节点展开照旧(UI 行保留)。
                for _vk in ("fidelity_check", "per_shot"):
                    _vv = val.get(_vk)
                    if _vv is not None and not _sum_extra.get(_vk):
                        _sum_extra[_vk] = _vv
                # 72-02 (v3.2 F28/QVR-03):审计分数 → aiScore(节点顶层字段,
                # _build_artifact_node 提升)——雷达图数据链的生产者。此前
                # canvas_nodes.ai_score 全库 0 行,ScoreRadar 对真实数据
                # 恒无图。
                _ai = self._derive_ai_score(val)
                if _ai is not None and not _sum_extra.get("aiScore"):
                    _sum_extra["aiScore"] = _ai
                _add_artifact(
                    f"{out_key}-summary",
                    f"{default_label}（概览）",
                    canvas_type,
                    description=_sum_desc,
                    _origin_key=out_key,
                    **_sum_extra,
                )
                # Expand sublists.
                for sub_key, sub_val in val.items():
                    if sub_key in self._SKIP_KEYS:
                        continue
                    # MODERATE #3: skip residual metadata bookkeeping keys
                    # (_agent_name / episode_id / _seq / _error / ...) that
                    # leak through _parse_delegate_output and create noise
                    # child nodes with 0 creative value.
                    if sub_key in self._METADATA_KEY_FILTER:
                        continue
                    if isinstance(sub_val, list) and sub_val:
                        for j, sub_item in enumerate(sub_val):
                            if isinstance(sub_item, dict):
                                sub_label = self._synthesize_child_label(
                                    sub_item, default_label, sub_key, j,
                                )
                            elif isinstance(sub_item, str):
                                sub_label = sub_item[:60]
                            else:
                                continue
                            # Passthrough ALL fields from sub_item dict.
                            _extra: dict[str, Any] = {}
                            if isinstance(sub_item, dict):
                                # Normalize media field aliases first
                                sub_item = _normalize_media_fields(dict(sub_item), workdir=workdir)
                                _extra = {
                                    k: v for k, v in sub_item.items()
                                    if k not in ("id", "shot_id", "name", "label")
                                    and v is not None
                                }
                                # ── P04: merge structured fields from bible ──
                                # l1_anchors/l4_props only have {name, path, ...}.
                                # Inject archetype/role/age_range/characterId by
                                # matching name against the bible lookup built above.
                                if bible_lookup:
                                    # 匹配键：name 优先，服装/道具子项退到
                                    # character 字段（scene_costume_turnarounds
                                    # 的归属角色）。空串必须短路——子串匹配
                                    # 「"" in lk_key」恒真会把无键子项全部
                                    # 错挂到第一个 bible 角色（ep-ccport-
                                    # test01 o_assets 1660 coffeemachine 服装
                                    # 被挂 characterId=小周 实证）。
                                    raw_name = str(
                                        sub_item.get("name")
                                        or sub_item.get("character")
                                        or "",
                                    ).strip()
                                    # canvas-topology (2026-07-27): preserve the
                                    # pinyin slug (e.g. "amao") as ``characterSlug``.
                                    # P04 nodes get ``characterId`` = the Chinese
                                    # name ("阿毛") via the bible merge below, but
                                    # P09/P06 ``character_refs[].name`` carry the
                                    # PINYIN slug ("amao"). Without ``characterSlug``
                                    # on the P04 node, those pinyin refs can never
                                    # resolve back to P04 — every P04→P09 character
                                    # edge silently fails (canvas-topology 断链 1).
                                    if raw_name:
                                        _extra.setdefault("characterSlug", raw_name)
                                    # Try direct match, then partial substring
                                    # （raw_name 为空时跳过——见上面的短路注释）。
                                    matched = bible_lookup.get(raw_name) if raw_name else None
                                    if not matched and raw_name:
                                        for lk_key, lk_entry in bible_lookup.items():
                                            if lk_key.startswith("_"):
                                                continue
                                            if lk_key in raw_name or raw_name in lk_key:
                                                matched = lk_entry
                                                break
                                    # Fallback: index-based match (l1_anchors
                                    # and bible characters are in the same order).
                                    if not matched and sub_key == "l1_anchors":
                                        idx_entry = f"char{j}"
                                        matched = bible_lookup.get(idx_entry)
                                    if matched:
                                        for bk in ("archetype", "role", "age_range",
                                                    "characterId", "characterCanonical",
                                                    "style_prefix", "l1_anchor", "species"):
                                            if bk not in _extra and matched.get(bk):
                                                _extra[bk] = matched[bk]
                                # ── P04 assetType 标记（2026-08-19 提出 matched 块）──
                                # 原先 l4_props 的 assetType=prop setdefault 嵌在
                                # 「if matched:」内——道具匹配不到角色 bible
                                # （道具本来就不在 character_bible 里）→ matched
                                # 恒 None → setdefault 永不执行 → 咖啡杯谱系表
                                # 以 assetType=character 注册进 o_assets
                                # （ep-ccport-test01 o_assets 1661 实证）。类型
                                # 标记只依赖 sub_key，不依赖 bible 命中。
                                if sub_key == "l4_props":
                                    _extra.setdefault("assetType", "prop")
                                elif sub_key == "l1_anchors":
                                    _extra.setdefault("assetType", "character")
                            # Use the item's id/shot_id when available so
                            # downstream reference resolution can find it.
                            if isinstance(sub_item, dict):
                                # ── P09b shot-audit id 防撞 ──────────────
                                # 审计 findings 通过 ``shot_id`` *引用* P09 的
                                # 分镜节点（如 s01）。若照常拿 shot_id 当节点
                                # id，会生成 a-s01 —— 与 P09 的 storyboard 节点
                                # a-s01 完全相同，upsert 会用精简的审计数据
                                # 覆盖 P09 的丰富分镜字段（cameraMovement /
                                # ltxPrompt / scene_ref / composition …）。
                                # 这里为 shot-audit 子项强制加 output-key
                                # 命名空间，保证 id 唯一、不覆盖 P09 分镜。
                                # shot_id 仍随 passthrough 写进节点 data，下游
                                # 引用 P09 分镜走的是 P09 自身的 a-{shot_id}。
                                if out_key == "shot-audit":
                                    _audit_ref = (
                                        sub_item.get("shot_id")
                                        or sub_item.get("id")
                                        or j
                                    )
                                    sub_id = f"{out_key}-{sub_key}-{_audit_ref}"
                                else:
                                    sub_id = str(
                                        sub_item.get("id")
                                        or sub_item.get("shot_id")
                                        or f"{out_key}-{sub_key}-{j}",
                                    )
                            else:
                                sub_id = f"{out_key}-{sub_key}-{j}"
                            # ── Synthesize description for child nodes ──
                            # Sub-items (e.g. hook candidates) often carry
                            # rich fields (hook_type, opening_line,
                            # visual_concept) but no ``description`` key.
                            # Without this, the canvas detail panel shows
                            # the label as description (e.g. "钩子设计.candidates 1"
                            # repeated) — Kai flagged this as a quality bug.
                            if isinstance(sub_item, dict) and not _extra.get("description"):
                                _syn_desc = self._synthesize_child_description(
                                    out_key, sub_item,
                                )
                                if _syn_desc:
                                    _extra["description"] = _syn_desc
                            _add_artifact(
                                sub_id,
                                sub_label,
                                "asset" if canvas_type == "asset" else "script",
                                **_extra,
                            )
                    elif isinstance(sub_val, str) and len(sub_val) > 5:
                        # Scalar content → summary node.
                        # description 保持 200 截断（节点卡片/列表视图用），
                        # 全文双写 data.content（script 节点 content 无 schema
                        # 限制，NodeDetailPanel 正文区优先渲染 content）——
                        # 此前 [:200] 截断即永久丢失，ep-ccport-test01 p01 的
                        # topic_nucleus/audience_pain 长文案在详情面板看不全。
                        _add_artifact(
                            f"{out_key}-{sub_key}",
                            f"{default_label} · {sub_key}",
                            "script",
                            description=sub_val[:200],
                            content=sub_val[:self._DICT_CONTENT_CAP],
                        )
                    elif (
                        isinstance(sub_val, dict)
                        and sub_val
                        and all(
                            isinstance(v, (int, float)) for v in sub_val.values()
                        )
                    ):
                        # Numeric score map (e.g. P03 audit_report.scores =
                        # {drama: 0.7, rhythm: 0.6, ...}). Without this branch
                        # the scores dict is silently dropped (only lists/strings
                        # are expanded), so the canvas never shows the 5-dim
                        # breakdown — operators can't see WHY total_score=0.66.
                        # Expand each dimension into a child node carrying its
                        # numeric score so the detail panel renders it.
                        _score_dim_parts = [
                            f"{dk}={dv:.2f}" if isinstance(dv, float) else f"{dk}={dv}"
                            for dk, dv in sub_val.items()
                            if isinstance(dv, (int, float))
                        ]
                        _score_desc = " · ".join(_score_dim_parts)[:200] or "—"
                        _score_extra: dict[str, Any] = {
                            dk: dv for dk, dv in sub_val.items()
                            if isinstance(dv, (int, float))
                        }
                        # Expose the dimension scores under camelCase aliases
                        # the frontend StructuredFieldPanel recognizes.
                        _score_extra["score"] = sum(
                            v for v in sub_val.values()
                            if isinstance(v, (int, float))
                        ) / max(
                            1, sum(
                                1 for v in sub_val.values()
                                if isinstance(v, (int, float))
                            )
                        )
                        _add_artifact(
                            f"{out_key}-{sub_key}",
                            f"{default_label} · {sub_key}",
                            "script",
                            description=_score_desc,
                            **_score_extra,
                        )
                    elif isinstance(sub_val, dict) and sub_val:
                        # ── dict 子节点展开（2026-08-18）─────────────────
                        # 嵌套结构化 dict（非纯数值——那些已被上面的 score-map
                        # 分支处理）此前被静默丢弃：_extract_artifacts 只展开
                        # list / str / 纯数值 dict 三种。ep-ccport-test01 p01
                        # 的 emotion_spectrum / platform_fit / charlie_selection
                        # / reversal_blueprint / creative_constraints、hook 的
                        # frame_breakdown_3sec 共 10 个字段全部落空，画布上
                        # 无从查看。
                        #
                        # 每个 dict key 只产 1 个子节点（节点数上界 = 输出
                        # key 数，无爆炸面）；标量叶子透传 node data（前端
                        # RawDataSection 渲染），description 拼接摘要，全文
                        # 写 data.content。护栏见 _summarize_structured_dict。
                        _ddesc, _dcontent, _dfields = (
                            self._summarize_structured_dict(sub_val)
                        )
                        if not _ddesc:
                            continue
                        _add_artifact(
                            f"{out_key}-{sub_key}",
                            f"{default_label} · {sub_key}",
                            "asset" if canvas_type == "asset" else "script",
                            description=" · ".join(_ddesc)[:200],
                            content=_dcontent[:self._DICT_CONTENT_CAP],
                            **_dfields,
                        )

            elif isinstance(val, dict):
                # Dict output without expansion: single summary node.
                val = _normalize_media_fields(dict(val), workdir=workdir)
                if phase_prefix == "p01":
                    _sum_desc, _sum_extra = self._enrich_p01_summary(
                        out_key, val,
                    )
                else:
                    # 同形化：见 expand 分支注释（2026-08-18）。本分支另有
                    # 全量标量 _passthrough，_sum_extra 起补充作用。
                    _sum_desc, _sum_extra = (
                        self._build_output_summary_description(
                            out_key, default_label, val,
                        )
                    )
                # Pass through ALL scalar fields from the dict (not just
                # thumbnailUrl/filePath). This is critical for media-type dict
                # outputs like P13 master_mp4 — the save-v2 video schema
                # requires shot_id, engine, duration_sec, resolution, and
                # dropping them causes HTTP 400. Only pass scalars (str/int/
                # float/bool) — nested dicts/lists would pollute the node data
                # and are not in the canvas schema.
                _passthrough = {
                    k: v for k, v in val.items()
                    if k not in ("description", "title", "logline")
                    and isinstance(v, (str, int, float, bool))
                    and v not in ("", None)
                }
                # ── 结构化子键白名单保留（2026-08-19 审计 #3）──────────
                # master_timeline.edl（每 clip 的 in/out_frame/rate/
                # transition/duration_sec）与 audio_stems 的 bgm/sfx/voice/
                # mix 子 dict 此前因「只穿透标量」被整体丢弃 — a-master_
                # timeline 节点仅剩 resolution/total_duration_sec 兜底字段，
                # EDL 细节在画布无处可查。node.data 是 z.record(z.string(),
                # z.any())，列表/嵌套 dict 合法。白名单防任意 blob 污染。
                for _sk in ("edl", "bgm", "sfx", "voice", "mix"):
                    _sv = val.get(_sk)
                    if isinstance(_sv, (list, dict)) and _sv:
                        _passthrough[_sk] = _sv
                _add_artifact(
                    out_key,
                    default_label,
                    canvas_type,
                    description=_sum_desc,
                    _origin_key=out_key,
                    **_sum_extra,
                    **_passthrough,
                )
            elif isinstance(val, str) and len(val) > 5:
                _add_artifact(out_key, default_label, canvas_type,
                              description=val[:200])

        # ── 2. Fallback: generic artifact lists not in _PHASE_OUTPUT_MAP ─
        for key in self._ARTIFACT_LIST_KEYS:
            if key in {spec[0] for spec in output_specs}:
                continue  # Already handled.
            # W3: skip alias list keys whose canonical key is already declared
            # for this phase — e.g. p07 ``images`` is a filesystem-fallback
            # alias of ``scene_images``; expanding both duplicated the nodes.
            _canonical = self._ALIAS_SKIP.get((phase_prefix, key))
            if _canonical and _canonical in {spec[0] for spec in output_specs}:
                continue
            val = outputs.get(key)
            if not isinstance(val, list):
                continue
            for i, item in enumerate(val):
                if isinstance(item, str):
                    _add_artifact(f"{key}-{i}", item[:80])
                elif isinstance(item, dict):
                    _add_artifact(
                        str(item.get("id") or f"{key}-{i}"),
                        str(
                            item.get("label") or item.get("name")
                            or item.get("title") or f"{key} {i+1}",
                        ),
                        "asset",
                        **{k: item[k] for k in
                           ("thumbnailUrl", "filePath", "selected")
                           if k in item},
                    )

        # ── 2b. Filesystem scan fallback ────────────────────────────
        # If the phase's artifacts have no filePath (e.g. P11 was killed
        # mid-render before writing outputs), recover them. Two layers:
        #   2a. Pipeline manifest (preferred) — carries shot_id/
        #       duration_sec/codec/... the canvas API requires.
        #   2b. Directory scan (last resort) — filenames only, so only
        #       used when no manifest exists for the phase.
        # ── 2026-08-26 修复：manifest 从「无媒体产物才兜底」改为「恒并入」──
        # 附：manifest/目录映射用数字感知前缀（p11a5、p11b 等带数字尾段的
        # phase 不能折叠到 p11a/p11b——否则 p11a5 会误并 preview 台账、p11a5
        # 的目录映射永远 miss）。_phase_prefix 的 [a-z]? 是 zone 链语义，不
        # 动它，这里单独算 map_prefix。
        _pfx_m = re.match(r"^(p\d+[a-z]*\d*)", phase_id)
        map_prefix = _pfx_m.group(1) if _pfx_m else phase_prefix
        # 旧语义 `if workdir and not media_artifact_ids:` 只在 result 完全没有
        # filePath 产物时才读 manifest/扫目录。QC 拒收 → rollback 只重渲被拒
        # 子集 → 最后一轮 attempt 的 result 只含子集（其余完好的磁盘产物不在
        # 内）→ 同步永久丢条目（ep-zhongkui-v2-ep01 p11a：18 镜预览最终只同步
        # 了 attempt-3 重渲的 4 个，14 个完好在盘）。新语义：manifest 是 phase
        # 跨 attempt 的累积 SSOT，恒并入，按规范化 filePath 去重——result 条目
        # 优先（字段更富），manifest 只补缺。目录扫描（2b）仍仅无 manifest 时
        # 兜底，但同样按 filePath 去重防重。
        def _norm_media_key(fp: Any) -> str | None:
            if not isinstance(fp, str) or not fp.strip():
                return None
            fp = fp.strip().split("?", 1)[0]
            if fp.startswith("/oss/"):
                return fp
            return _fs_to_oss_url(fp) or fp

        _existing_media_keys: set[str] = set()
        for _a in artifacts:
            _k = _norm_media_key(
                _a.get("filePath") or _a.get("thumbnailUrl")
            )
            if _k:
                _existing_media_keys.add(_k)

        if workdir:
            # ── 2a. Pipeline manifest union ─────────────────────────
            # When a phase ran manually (P11/P12/P13) but was never
            # registered back into .pipeline-state.json, sync_phase_result
            # has no phase result to read outputs from. The directory scan
            # below yields only filenames — it cannot supply the
            # shot_id/duration_sec/etc. fields the canvas API requires, so
            # the canvas POST returns HTTP 400. Prefer the phase's manifest
            # JSON in workdir/.pipeline-assets/, which carries full item
            # dicts (the SSOT P11/P12/P13 phases write).
            #   (manifest_name, out_key, canvas_type, default_label, format)
            phase_manifest_map = {
                "p11": ("video-clips.json", "video_clips", "video", "视频片段", "json"),
                # P11b 最终渲染 —— sub-step 的 checkpoint 不存 result.result
                # （只有 {phase,status,rollback_to}），on_phase_complete 拿不到
                # outputs.video_clips。manifest 兜底从 video-clips.json 恢复 20 个
                # shot 的成片节点（时间轴所需）。
                "p11b": ("video-clips.json", "video_clips", "video", "最终视频", "json"),
                # 2026-08-26：p11a 预览片段台账（rapid-preview-clips 槽位，逐变体
                # 追加 jsonl）。QC 拒收重跑只重渲子集时，从这里把其余完好的
                # 预览片段并回同步（clip_path 别名 → filePath 在循环内兜底）。
                "p11a": ("rapid-preview-clips.jsonl", "rapid_preview_clips", "video", "预览片段", "jsonl"),
                "p12": ("master-timeline.json", "master_timeline", "script", "时间线 EDL", "json"),
                # P12 split: p12a 的 manifest 兜底与旧 p12 相同（master-
                # timeline.json，asset_bus "master-timeline" 槽位未改名）。
                # p12b 的核心产物是 video_concat/master.mp4（ffmpeg 落盘），
                # manifest audio-stems.json 只是元数据——经 manifest 恢复的
                # 音轨节点走 audio 类型。
                "p12a": ("master-timeline.json", "master_timeline", "script", "时间线 EDL", "json"),
                "p12b": ("audio-stems.json", "audio_stems", "audio", "音轨", "json"),
                "p13": ("delivery-package.json", "delivery_package", "script", "交付包", "json"),
            }
            manifest_spec = phase_manifest_map.get(map_prefix)
            manifest_loaded = False
            if manifest_spec:
                manifest_name, out_key, canvas_type, default_label, manifest_fmt = manifest_spec
                manifest_path = os.path.join(
                    workdir, ".pipeline-assets", manifest_name,
                )
                if os.path.isfile(manifest_path):
                    manifest_loaded = True
                    if manifest_fmt == "jsonl":
                        # jsonl 槽位（rapid-preview-clips）：逐行解析，坏行跳过。
                        items = []
                        try:
                            with open(manifest_path, "r", encoding="utf-8") as _mf:
                                for _ln in _mf:
                                    _ln = _ln.strip()
                                    if not _ln:
                                        continue
                                    try:
                                        items.append(json.loads(_ln))
                                    except json.JSONDecodeError:
                                        continue
                        except OSError:
                            logger.warning(
                                "canvas_sync: failed to read manifest %s",
                                manifest_path, exc_info=True,
                            )
                            items = []
                    else:
                        manifest = {}
                        try:
                            with open(manifest_path, "r", encoding="utf-8") as _mf:
                                manifest = json.load(_mf)
                        except (OSError, json.JSONDecodeError):
                            logger.warning(
                                "canvas_sync: failed to read manifest %s",
                                manifest_path, exc_info=True,
                            )
                        items = (
                            manifest.get("value")
                            if isinstance(manifest, dict) else None
                        )
                    if isinstance(items, list):
                        for i, item in enumerate(items):
                            if not isinstance(item, dict):
                                continue
                            # Normalize media aliases (video_path/
                            # audio_path/file_path → filePath) and convert
                            # to /oss/ URLs via _fs_to_oss_url.
                            # clip_path（rapid-preview-clips 台账的别名）兜底。
                            if not item.get("filePath") and item.get("clip_path"):
                                item["filePath"] = item["clip_path"]
                            item = _normalize_media_fields(
                                dict(item), workdir=workdir,
                            )
                            # 2026-08-26 并入去重：result 已含同文件条目（字段
                            # 更富）则跳过 manifest 条目；否则并入并登记 key。
                            _mk = _norm_media_key(item.get("filePath"))
                            if _mk and _mk in _existing_media_keys:
                                continue
                            if _mk:
                                _existing_media_keys.add(_mk)
                            _raw_id = (
                                item.get("shot_id") or item.get("id")
                                or item.get("name")
                                or f"{out_key}-{i}"
                            )
                            item_id = f"{out_key}-{_raw_id}"
                            item_label = str(
                                item.get("shot_id") or item.get("label")
                                or item.get("name") or item.get("title")
                                or f"{default_label} {i+1}",
                            )
                            # Node type: derive from the resolved media
                            # extension (matches the dir-scan below), so a
                            # video clip always renders as "video" even when
                            # the declared canvas_type is "script".
                            _fp = item.get("filePath") or ""
                            _ext = _media_ext(_fp)
                            if _ext in _VIDEO_EXTS:
                                node_type = "video"
                            elif _ext in _AUDIO_EXTS:
                                node_type = "audio"
                            elif _ext in _IMAGE_EXTS:
                                node_type = "asset"
                            else:
                                node_type = canvas_type
                            # Passthrough all scalar fields (shot_id,
                            # duration_sec, resolution, codec, engine,
                            # murch_grade, ...) so _build_artifact_node and
                            # the mapping layer receive the full payload.
                            _item_extra = {
                                k: v for k, v in item.items()
                                if k not in ("id", "name", "label", "title")
                                and v is not None
                            }
                            _add_artifact(
                                item_id, item_label, node_type,
                                _origin_key=out_key,
                                **_item_extra,
                            )

            # ── 2b. Directory scan fallback (last resort) ──────────
            # Only scan the filesystem when no manifest was available —
            # the manifest is strictly richer; fall back to filenames only
            # when the phase has no manifest at all. (p11b 渲染中途无
            # video-clips.json——逐镜增量同步靠这里扫 assets/P11 落已渲镜头。)
            # 2026-08-26 例外：p11a 的 preview 目录不受此门控——
            # rapid-preview-clips.jsonl 是逐变体追加的 jsonl，QC 拒收回滚/
            # 崩溃中会丢行（实测 18 镜只余 6 行），目录才是最终真相层。
            _scan_always = (map_prefix == "p11a")
            if not manifest_loaded or _scan_always:
                # Determine the phase's asset directory.
                phase_dir_map = {
                    "p07": "S07", "p10": "audio", "p11": "P11",
                    "p11b": "P11",
                    # p11a5 预演成片（roughcut_v1 / preview_mix）——预览人工门
                    # 的审核对象，补进资产库便于预览 vs 终渲对比。
                    "p11a5": "P11a5",
                    "p12": "P12",
                    # P12 split: p12a/p12b 都落 assets/P12/（video_concat.mp4、
                    # mix_a.wav、master.mp4 等共享同一目录）。
                    "p12a": "P12",
                    "p12b": "P12",
                    # P09c clay-maquette 分镜板图片（6 张）—— phase 输出只有
                    # storyboard_board dict，图片走目录扫描兜底。
                    "p09c": "storyboard_sheets",
                }
                asset_subdir = phase_dir_map.get(map_prefix)
                # 2026-08-26：p11a 预览片段目录带 episode 名（assets/preview/
                # <episode_id>/），静态映射表达不了——特判展开。台账
                # rapid-preview-clips.jsonl 是逐变体追加的 jsonl，崩溃中会丢
                # 行（ep-zhongkui-v2-ep01 实测 18 镜只余 6 行）——目录扫描是
                # preview 片段的最终真相层。
                if map_prefix == "p11a" and episode_id:
                    _pv_dir = os.path.join(
                        workdir, "assets", "preview", episode_id,
                    )
                    _scan_dirs = [_pv_dir] if os.path.isdir(_pv_dir) else []
                elif asset_subdir:
                    _scan_dirs = [os.path.join(workdir, "assets", asset_subdir)]
                else:
                    _scan_dirs = []
                for asset_dir in _scan_dirs:
                    if os.path.isdir(asset_dir):
                        for fname in sorted(os.listdir(asset_dir)):
                            fpath = os.path.join(asset_dir, fname)
                            if not os.path.isfile(fpath):
                                continue
                            ext = _media_ext(fname)
                            if ext not in _IMAGE_EXTS and ext not in _VIDEO_EXTS and ext not in _AUDIO_EXTS:
                                continue
                            # Determine node type from extension.
                            if ext in _VIDEO_EXTS:
                                node_type = "video"
                            elif ext in _AUDIO_EXTS:
                                node_type = "audio"
                            else:
                                node_type = "asset"
                            # Label: strip extension, replace underscores.
                            label = os.path.splitext(fname)[0].replace("_", " ")
                            # Prefix the artifact id with the phase so scan-
                            # recovered nodes (a-{phase}-scan-{stem}) NEVER
                            # collide with structured artifact ids. Bare
                            # a-{stem} ids clash with, e.g., the p06 spatio-
                            # temporal-script shot nodes whose legitimate id
                            # is exactly a-S{N}-A{M} (e.g. leftover S1-A2.wav
                            # → a-S1-A2 audio would overwrite the p06 script
                            # node a-S1-A2 on upsert). See ep-xiaojianghu-
                            # demo1 p11_video_render HTTP 400.
                            art_id = f"{phase_prefix}-scan-{os.path.splitext(fname)[0]}"
                            oss_url = _fs_to_oss_url(fpath)
                            # 2026-08-26：并入去重——result/manifest 已覆盖的文件
                            # 不再生成 scan 节点（防止同文件双节点）。
                            if oss_url and oss_url in _existing_media_keys:
                                continue
                            _existing_media_keys.add(oss_url)
                            # Gate B 补齐：video/audio 节点缺
                            # shot_id/engine/duration_sec/resolution 会被降级
                            # 成 script 文本卡。shot_id 取文件名 stem，
                            # duration/resolution 用 ffprobe 探测，engine 目录
                            # 扫描无法得知（填 unknown，phase 完成时的正式
                            # 同步会带真值覆盖）。
                            _scan_extra: dict[str, Any] = {}
                            if node_type in ("video", "audio"):
                                _scan_extra["shot_id"] = os.path.splitext(fname)[0]
                                _scan_extra["engine"] = "unknown"
                                _scan_extra.update(_ffprobe_media_meta(fpath))
                            _add_artifact(
                                art_id, label, node_type,
                                filePath=oss_url,
                                thumbnailUrl=oss_url if (ext in _IMAGE_EXTS or ext in _VIDEO_EXTS) else None,
                                description=f"文件系统扫描: {fname}",
                                **_scan_extra,
                            )

        # ── 2c. keyframe(首尾帧) manifest 注入（审计 #9, 2026-08-17）────
        # p11a：iframe-manifest.json 是帧 SSOT（gen_iframes 落盘），phase
        # outputs 不携带帧（gen_iframes 是独立脚本）。从磁盘读 manifest 产
        # a-flf-{shot}-{first|last}-v{N} 变体节点，消灭手工 SQL 环节。
        # 幂等：节点 id 确定（shot×frame×variant）；重跑经
        # _load_iframe_curation_snapshot 继承用户三态选择。
        if phase_prefix == "p11a":
            for art in self._load_iframe_flf_artifacts(result, workdir=workdir):
                _add_artifact(
                    art.pop("id"), art.pop("label"), art.pop("type"), **art,
                )

        # ── 3. 生成压缩缩略图 ────────────────────────────────────
        # 每个 artifact 的 thumbnailUrl 若指向原图/原视频，则生成 WebP
        # 压缩版（max 400px, q80），并把原路径保留到 filePath。
        # 幂等：已是 _thumbs/ 或源文件缺失则跳过。
        for art in artifacts:
            thumb = art.get("thumbnailUrl")
            if not isinstance(thumb, str) or not _is_media_oss_url(thumb):
                continue
            compressed = _ensure_thumbnail(thumb)
            if compressed != thumb:
                if not art.get("filePath"):
                    art["filePath"] = thumb
                art["thumbnailUrl"] = compressed

        return artifacts

    def _build_artifact_node(
        self,
        phase_id: str,
        artifact: dict[str, Any],
    ) -> dict[str, Any]:
        """Build a canvas node_data dict for an artifact child node.

        Uses the V4 semantic layout (``compute_grouped_position``) when
        the artifact carries a ``characterId`` or ``sceneId`` grouping
        key. Falls back to the legacy hash-based scatter when no grouping
        key is present.
        """
        phase_prefix = _phase_prefix(phase_id)
        _, asset_type = self._PHASE_TYPE_MAP.get(
            phase_prefix, ("asset", "scene"),
        )
        # Per-output assetType override takes precedence over the phase-level
        # default. _origin_key is set in _extract_artifacts when the artifact
        # is created from a known output key (e.g. "topic_kernel" vs "hook_design"
        # in P01 — both should not share the same assetType).
        origin_key = artifact.get("_origin_key")
        if isinstance(origin_key, str) and origin_key:
            override = self._PHASE_ASSET_TYPE_OVERRIDE.get(
                (phase_prefix, origin_key),
            )
            if override:
                asset_type = override
        canvas_type, _ = self._PHASE_TYPE_MAP.get(
            phase_prefix, ("asset", asset_type),
        )
        # B-13: Use _PHASE_INDEX_MAP (1-based) for phaseIndex to stay
        # consistent with _build_phase_node. Previously this used
        # enumerate(ZONE_PHASES) (0-based), causing phaseIndex mismatch
        # between phase summary nodes and their artifact children.
        phase_idx = self._PHASE_INDEX_MAP.get(phase_prefix, 0)
        # 0-based zone index for position layout (must match
        # compute_zone_position's enumerate).
        _zone_idx = next(
            (i for i, (p, _, _) in enumerate(canvas_graph.ZONE_PHASES)
             if p == phase_prefix),
            len(canvas_graph.ZONE_PHASES),
        )

        # ── V4 semantic layout ──────────────────────────────────────
        # Group by characterId or sceneId when available. This puts all
        # angles/views of the same character (or scene) on the same row.
        group_key = artifact.get("characterId") or artifact.get("sceneId")
        if group_key:
            # Use the per-phase child counter to assign group/item indices.
            # Each unique group_key gets its own group_index; items within
            # a group advance item_index.
            group_counter_key = f"{phase_prefix}:__groups__"
            if not hasattr(self, "_v4_group_state"):
                self._v4_group_state: dict[str, Any] = {}
            groups: dict[str, int] = self._v4_group_state.setdefault(
                group_counter_key, {},
            )
            if group_key not in groups:
                groups[group_key] = len(groups)
            group_index: int = groups[group_key]
            item_key = f"{phase_prefix}:{group_key}:items"
            item_index: int = self._v4_group_state.get(item_key, 0)
            self._v4_group_state[item_key] = item_index + 1
            position = canvas_graph.compute_grouped_position(
                phase_prefix, group_index, item_index,
            )
        else:
            # Deterministic scatter within the parent zone's lane.
            # Uses a per-phase child counter for stable, sequential layout.
            counter_key = f"{phase_prefix}:__scatter__"
            idx = self._child_counters.get(counter_key, 0)
            self._child_counters[counter_key] = idx + 1
            col = idx % canvas_graph.V4_MAX_NODES_PER_ROW
            row = idx // canvas_graph.V4_MAX_NODES_PER_ROW
            position = {
                "x": _zone_idx * canvas_graph._ZONE_X_STEP + col * canvas_graph.V4_COL_SPACING + 100,
                "y": canvas_graph.V4_BASE_Y + row * canvas_graph.V4_ROW_SPACING,
            }

        selected = artifact.get("selected", True)
        tags = ["✅ 已选"] if selected else ["未选"]
        # Canvas save-v2 rejects nodes where ``description`` is missing
        # or None ("script node requires description" / "expected string,
        # got undefined" → HTTP 400). We initialize it here to the label
        # as a guaranteed-string fallback; the passthrough loop below
        # overwrites it with the real description when one is available.
        #
        # filePath / thumbnailUrl are NOT pre-initialized: the save-v2
        # schema (canvasAssetSchema.ts:108-118) marks them OPTIONAL for
        # script nodes and REQUIRED (min length 1) only for media nodes.
        # Pre-initializing them to "" pollutes script nodes with empty
        # fields and causes the canvas detail panel to render empty
        # file rows. The passthrough loop below adds them when the
        # artifact actually carries a non-empty value. The media-node
        # guard further down (canvas_type in asset/video/audio) coerces
        # nodes without a real filePath back to "script" type.
        label = artifact.get("label", artifact["id"])
        data: dict[str, Any] = {
            "label": label,
            "description": str(label),  # non-None fallback; overwritten below if present
            "state": "success" if selected else "idle",
            "tags": tags,
            "assetType": asset_type,
        }

        # Passthrough: copy ALL fields from artifact dict (not just a
        # fixed whitelist). This ensures structured fields produced by
        # phase modules (cameraMovement, archetype, engine, etc.) reach
        # the frontend StructuredFieldPanel without being silently
        # dropped by an outdated opt_key list.
        for k, v in artifact.items():
            if k in ("id", "label", "type", "selected", "_origin_key"):
                continue
            # 72-02 (v3.2 F28/QVR-03):aiScore 是 V2 节点顶层字段(非 data
            # 袋),在 return 段提升——不进 data。
            if k == "aiScore":
                continue
            if v is None:
                continue
            # MODERATE #3: filter residual metadata bookkeeping keys that
            # leak through _parse_delegate_output (_agent_name / episode_id /
            # _seq / _error / ...). These are runner internals with zero
            # creative value; keeping them pollutes every node's data panel.
            # EXEMPTION — "provenance": commit 66bb30c (2026-08-18) added
            # "provenance" to _METADATA_KEY_FILTER to stop the p02
            # story-framework slot-value top-level provenance{model,session}
            # dict from expanding into noise child nodes — but this same
            # filter also runs in the artifact passthrough loop here, which
            # silently stripped ARTIFACT-level provenance from node data.
            # Artifact provenance must survive: the input_refs canvas link
            # consumer (~L2867-2896) reads art_data.get("provenance") to
            # draw dataType="dependency" edges, and the frontend renders the
            # provenance chain from it. The filter's other two usage points
            # (~L4036 slot-value dict expansion, ~L4653 sub_key expansion)
            # stay unexempted — those are exactly the noise paths 66bb30c
            # was guarding.
            if k in self._METADATA_KEY_FILTER and k != "provenance":
                continue
            # Skip empty-string filePath/thumbnailUrl — keep the data dict
            # clean for script nodes (the save-v2 schema marks these
            # optional for script type). Media nodes still get them via
            # the passthrough when the artifact actually has a non-empty
            # value.
            if k in ("filePath", "thumbnailUrl") and isinstance(v, str) and not v.strip():
                continue
            data[k] = v

        # Structured field mapping: derive frontend NODE_SCHEMA fields
        # from the raw phase result data. This handles:
        # - snake_case → camelCase rename (camera_movement → cameraMovement)
        # - Chinese enum → English enum translation (固定 → static)
        # - Derivation from semantic fields (role text → archetype enum)
        _apply_schema_mappings(data, phase_prefix, artifact)

        # 71-01 (F05/COX-01):配方哨兵——kmc 侧配方真值快照(generation_prompt
        # 或 prompt)。用户画布改 data.prompt 后 != 哨兵,B-4 删建据此抢救。
        # 71-02 (F05/COX-02):kmc 重同步 = 新真值,data.stale 一并清除
        # (deep-merge 会永久保留旧 stale 键——n-*/a-* 残留的根因)。
        data.setdefault(
            "_kmc_prompt",
            str(data.get("generation_prompt") or data.get("prompt") or ""),
        )
        data.pop("stale", None)

        # Normalize characterId for cross-set consistency.
        char_id = data.get("characterId")
        if char_id:
            normalized = canvas_graph.normalize_character_name(char_id)
            if normalized:
                data["characterId"] = normalized
                data["characterCanonical"] = normalized

        # ── Occam's razor field sanitization (2026-07-14) ─────────────
        # Drop fields that are pure noise or redundant duplicates of their
        # camelCase counterpart. ep-hamster-demolition audit showed video
        # nodes carried 6 snake_case/camelCase duplicate pairs (camera_movement
        # + cameraMovement, audio_cue + audioCue, etc.) — every value was
        # identical. Frontend reads camelCase only (constants.ts:191-226), so
        # the snake_case copies just bloat the JSON without informational value.
        # Schema-required snake_case fields (shot_id/engine/duration_sec/
        # resolution per canvasAssetSchema.ts:64-73) are PRESERVED.
        for drop_key in _CANONICAL_DROP_FIELDS:
            data.pop(drop_key, None)

        # ── Per-artifact type override ──────────────────────────────
        # _PHASE_OUTPUT_MAP declares a canvas_type per output key (e.g.
        # P13 master_mp4 → "video").  _add_artifact stores it in
        # artifact["type"].  However canvas_type above was overwritten by
        # _PHASE_TYPE_MAP (phase-level default, e.g. P13 → "script").
        # Prefer the per-artifact type when it is a media type; this lets
        # a single phase emit both video and script nodes.
        art_type_override = artifact.get("type")
        if art_type_override in ("video", "audio", "asset", "storyboard"):
            canvas_type = art_type_override
        elif (
            art_type_override == "script"
            and canvas_type == "storyboard"
            and not data.get("shot_id")
        ):
            # Report-family slot under a storyboard phase (p09/p09c):
            # storyboard-qc / continuity_report are advisory TEXT reports
            # declared "script" in _PHASE_OUTPUT_MAP, but the phase-level
            # storyboard default used to swallow that declaration → Gate B
            # degraded them back to script with _original_type="storyboard" →
            # the kap frontend restore flipped them into storyboard-stage
            # nodes → QC report cards leaked into the canvas timeline as
            # shot rows (钟馗夜馒 2026-08-23: 7 「分镜板质检 · …」 rows before
            # S01_B01). A storyboard row's identity is shot_id — no shot_id
            # means it's a report: honor the declared script and skip the
            # degrade/restore round-trip entirely. (e_konte_sheets /
            # transition_design items DO carry shot_id → still storyboard.)
            canvas_type = "script"

        # ── Node type safety: media types require non-empty filePath ──
        # The canvas save-v2 API rejects asset/video/audio nodes with an
        # empty filePath ("filePath is required for media nodes"). Text
        # artifacts (character descriptions, scene notes, summary nodes)
        # legitimately have no file — they must be ``script`` type, which
        # treats filePath as optional.
        final_fp = data.get("filePath", "")
        if canvas_type in ("asset", "video", "audio"):
            if not isinstance(final_fp, str) or not final_fp.strip():
                canvas_type = "script"

        # ── C4 (a): Gate B field-name normalization ──────────────────
        # Map pipeline domain aliases (shot_intent / duration / ...) onto the
        # canonical param names save-v2 Gate B validates. Only fills a
        # canonical key when it is absent (a real canonical value wins).
        for _alias, _canonical in self._FIELD_ALIASES.items():
            if _alias in data and _canonical not in data:
                data[_canonical] = data[_alias]

        # ── C4 (b): Gate B required-field degradation ────────────────
        # A media node (audio/video/storyboard) that survived the media-node
        # guard — i.e. has a real filePath for audio/video, or is a storyboard
        # (filePath optional) — but is still missing a required structured
        # param would make save-v2 reject the WHOLE graph (save-v2.ts:50-57).
        # Degrade it to "script" (label+description only, all params optional)
        # and record the original type so the frontend can still hint at it.
        if canvas_type in self._GATE_B_REQUIRED:
            # 0 / 0.0 是合法值（duration_sec=0 = 引擎未回报时长，H3 渲染
            # 的常态）。falsy 判断（`not data.get(f)`）曾把 duration_sec=0
            # 误判为缺失，ep-ccport-test01 一跑 37 个媒体节点全量降级
            # script（video 9 / storyboard 26 / audio 2，画布上视频全变
            # 文本卡）。只对真缺失（None / 空串）降级。
            _missing = [
                f for f in self._GATE_B_REQUIRED[canvas_type]
                if data.get(f) is None or data.get(f) == ""
            ]
            if _missing:
                data["_original_type"] = canvas_type
                logger.debug(
                    "canvas_sync: degrade %s node (missing Gate B fields %s) "
                    "→ script to avoid save-v2 400",
                    canvas_type, _missing,
                )
                canvas_type = "script"

        # ── 源头 schema 类型 coerce（2026-08-19 深化）─────────────────────
        # save 收口点的 _coerce_graph_schema_types 是最后防线（也修 load 回
        # 的旧节点），这里在产出源头再对齐一次最终 canvas_type 的类型表：
        # 纯映射消费者（_build_node_from_phase_result 的调用方分析/测试）
        # 拿到的即是已类型化 data，且未来新增 save 路径天然受保护。
        # Gate B 降级后再 coerce——type 已终局。
        _type_table = _load_schema_field_types().get(canvas_type)
        if _type_table:
            for _k, _v in list(data.items()):
                _zt = _type_table.get(_k)
                if _zt is None:
                    continue
                _cv = _coerce_scalar_to_schema(_v, _zt)
                if _cv is not _v and type(_cv) is not type(_v):
                    data[_k] = _cv

        # ── subtype 双写进 node.data（2026-08-19 审计 #5）────────────
        # _infer_asset_subtype 此前只在 _sync_asset_to_oassets_oimage 里写
        # o_assets.meta.subtype，画布节点 data 不带 → 画布侧（条件帧分组、
        # 卡片角标）拿不到子类型。与 meta 同源同值双写；显式已有 subtype
        # 的节点（下游 phase 已标记）不覆盖。
        if canvas_type == "asset":
            _subtype = self._infer_asset_subtype(
                artifact, data, data.get("assetType"),
            )
            if _subtype:
                data.setdefault("subtype", _subtype)

        # 72-02 (v3.2 F28/QVR-03):aiScore 提升为 V2 节点顶层字段——adapter
        # L215-216 读顶层 n.aiScore → V3 asset.aiScore → save-v2 落
        # canvas_nodes.ai_score 列(雷达图 ScoreRadar 的数据链从此有真实
        # 生产者,全库 0 行成为历史)。
        _ai_score = artifact.get("aiScore")
        node_out: dict[str, Any] = {
            "type": canvas_type,
            "position": position,
            "size": {"width": 240, "height": 260},
            "state": "success" if selected else "idle",
            "branchId": "main",
            "phaseIndex": phase_idx,
            "phaseName": phase_id,
            "data": data,
        }
        if isinstance(_ai_score, dict) and _ai_score:
            node_out["aiScore"] = _ai_score
        return node_out

    def _extract_candidates(
        self,
        phase_id: str,
        result: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Extract multi-choice candidates from ``result.outputs``.

        Looks for ``variants``, ``candidates``, ``options``, ``choices``
        keys in outputs. Each becomes a candidate node with
        ``selected`` marking.

        Returns a list of candidate dicts:
            ``{id, label, selected, description?, thumbnailUrl?, filePath?}``
        """
        outputs = result.get("outputs") or {}
        if not isinstance(outputs, dict):
            outputs = {}

        candidates: list[dict[str, Any]] = []
        candidate_keys = ("variants", "candidates", "options", "choices")

        for key in candidate_keys:
            val = outputs.get(key)
            if not isinstance(val, list):
                continue
            # Determine the selected index/name if available.
            selected_name = outputs.get(f"selected_{key.rstrip('s')}")
            if not isinstance(selected_name, str):
                selected_name = outputs.get("selection")
            for i, item in enumerate(val):
                if isinstance(item, str):
                    cand = {
                        "id": f"{key}-{i}",
                        "label": item[:80],
                        "selected": (i == 0),
                    }
                elif isinstance(item, dict):
                    name = str(
                        item.get("name") or item.get("label")
                        or item.get("title") or f"{key} {i+1}",
                    )
                    cand = {
                        "id": str(item.get("id") or name),
                        "label": name,
                        "selected": (
                            name == selected_name
                            or item.get("selected", i == 0)
                        ),
                    }
                    for fk in ("thumbnailUrl", "filePath", "description", "score"):
                        fv = item.get(fk)
                        if fv is not None:
                            cand[fk] = fv
                else:
                    continue
                candidates.append(cand)

        return candidates

    # 落选候选文件 → (filename) 映射。每个候选文件是 SSOT wrapper：
    #   {value: {variants: [...], chosen_variant_id: "...", ...}, ...}
    # value.variants 每项形如 {variant_id, candidate: {...}, provenance}。
    _CANDIDATE_FILES: dict[str, str] = {
        "p01": "hook-candidates.json",
        # 69-02 (v3.2 WBI-02/F35):五源注册补齐——p03 N-best(p03 选优后
        # 落盘 script-candidates)/p11a 预览变体(选优后落盘
        # preview-candidates,rank=1 即 chosen)/p11b take(take-log slot,
        # 27-03 起含 render_variants)。
        "p03": "script-candidates.json",
        "p11a": "preview-candidates.json",
        "p11b": "take-log.json",
    }

    def _load_candidate_variants(
        self,
        phase_id: str,
        workdir: str = "",
    ) -> list[dict[str, Any]]:
        """Load non-winner candidate variants from on-disk candidate files.

        问题3（落选候选 / redundant variants）：generation_config 冗余机制
        （P01 hook K=3、P03 script K=3）产出 N 个候选并选定一个 winner。
        Winner 进入 ``result.outputs``（如 ``hook_design``），但落选候选不会
        被传播到 outputs —— 只持久化到 ``workdir/.pipeline-assets/`` 的候选
        文件。因此 ``_extract_candidates``（读 ``outputs["variants"/...]``）
        什么也找不到，画布只显示 winner。

        本方法读取 phase 的候选文件，返回标准 candidate dict
        （``{id, label, selected, description, score?}``），让既有的
        ``add_candidate_node`` 渲染路径把每个变体都画出来 —— winner 由文件的
        ``chosen_variant_id`` 标记 ``selected=True``。

        Degrade-tolerant：文件缺失/形状不符 → 返回 ``[]``。

        Args:
            phase_id: Phase identifier (e.g. ``"p01_hook_topic"``).
            workdir: Episode workdir（``KAIS_RUN_WORKDIR``）；候选文件位于
                ``workdir/.pipeline-assets/`` 下。

        Returns:
            Candidate dict 列表；无可渲染内容时为空。
        """
        phase_prefix = _phase_prefix(phase_id)
        fname = self._CANDIDATE_FILES.get(phase_prefix)
        if not fname or not workdir:
            return []
        path = os.path.join(workdir, ".pipeline-assets", fname)
        if not os.path.isfile(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as _f:
                wrapper = json.load(_f)
        except (OSError, json.JSONDecodeError):
            logger.warning(
                "canvas_sync: candidate file unreadable %s — skipping variants",
                path, exc_info=True,
            )
            return []
        value = wrapper.get("value") if isinstance(wrapper, dict) else wrapper
        if not isinstance(value, dict):
            return []
        variants = value.get("variants")
        if not isinstance(variants, list):
            return []
        chosen = (
            value.get("chosen_variant_id")
            or value.get("selected_variant_id")
            or value.get("winner")
        )
        out: list[dict[str, Any]] = []
        for var in variants:
            if not isinstance(var, dict):
                continue
            vid = str(var.get("variant_id") or var.get("id") or "")
            # 候选 payload 可能嵌套在 .candidate（P01 hook）或扁平。
            cand = (
                var.get("candidate")
                if isinstance(var.get("candidate"), dict)
                else var
            )
            label = str(
                cand.get("opening_line") or cand.get("logline")
                or cand.get("name") or cand.get("label")
                or cand.get("title") or vid or "候选"
            )[:80]
            # 从候选定义字段合成描述。白名单扩容（2026-08-18）：
            # ep-ccport-test01 hook 候选的核心差异字段是 visual_concept /
            # hook_strength / frame_breakdown_3sec，原 5 键白名单
            # （hook_type/genre/tone/premise/synopsis）只拼得出类型一行，
            # 落选候选之间在画布上无从对比。
            desc_parts: list[str] = []
            for fk in (
                "hook_type", "genre", "tone", "premise", "synopsis",
                "tier_label",
            ):
                fv = cand.get(fk)
                if fv:
                    desc_parts.append(f"{fk}: {str(fv)[:60]}")
            _hs = cand.get("hook_strength")
            if isinstance(_hs, (int, float)):
                desc_parts.append(f"hook_strength: {_hs}")
            _vc = cand.get("visual_concept")
            if isinstance(_vc, str) and _vc.strip():
                desc_parts.append(f"visual_concept: {_vc[:100]}")
            _fb = cand.get("frame_breakdown_3sec")
            if isinstance(_fb, dict) and _fb:
                # 摘要：段数 + 首段 content 预览（全文进 extra data 前先
                # 拍平 —— RawDataSection 不渲染嵌套 dict）。
                desc_parts.append(
                    f"frame_breakdown_3sec: {len(_fb)} 段"
                )
            description = "  ·  ".join(desc_parts) if desc_parts else label
            entry: dict[str, Any] = {
                "id": f"variant-{vid}" if vid else f"variant-{len(out)}",
                "label": label,
                "selected": (bool(chosen) and vid == str(chosen)),
                "description": description,
            }
            score = cand.get("hook_strength") or cand.get("score")
            if score is not None:
                entry["score"] = score
            # 结构化字段透传（2026-08-18）：variant 节点无 NODE_SCHEMA，
            # StructuredFieldPanel 不渲染；详情面板的 RawDataSection 渲染
            # 穿透标量。把候选自身的标量字段（含 frame_breakdown_3sec 的
            # 拍平预览）带过去，落选候选才有可对比的结构化信息。
            _extra_data: dict[str, Any] = {}
            for ck, cv in cand.items():
                if ck in ("id", "name", "label", "title"):
                    continue
                if isinstance(cv, (str, int, float, bool)) and cv not in ("", None):
                    if len(str(cv)) > 500:
                        continue
                    _extra_data[ck] = cv
                elif ck == "frame_breakdown_3sec" and isinstance(cv, dict):
                    for fbk, fbv in list(cv.items())[:3]:
                        if isinstance(fbv, dict):
                            _mode = str(fbv.get("mode") or "").strip()
                            _content = str(fbv.get("content") or "").strip()
                            _preview = (
                                f"{_mode} — {_content}" if _mode and _content
                                else (_mode or _content)
                            )[:200]
                            if _preview:
                                _extra_data[fbk] = _preview
                        elif isinstance(fbv, (str, int, float)):
                            _extra_data[fbk] = str(fbv)[:200]
            if _extra_data:
                entry["data"] = _extra_data
            out.append(entry)
        return out

    # ── 审计 #9（2026-08-17）：keyframe(首尾帧) 自动同步 ──────────────────
    #
    # iframe-canvas-sync skill 此前是纯手工操作手册（备份 DB → DELETE 旧
    # a-flf-* → INSERT 新节点），KMC 自动链路零 a-flf 生产者（08-16 审计 F
    # 节）。本方法把该 SQL 契约搬进 p11a 的 on_phase_complete 路径：
    # gen_iframes.py 落盘的 assets/P11/iframe-manifest.json 是帧 SSOT，
    # p11a 完成时读取它并为每个 shot × {first,last} × v{N} 产出一个
    # a-flf-{shot}-{first|last}-v{N} asset 节点。
    #
    # 字段契约（iframe-canvas-sync SKILL.md §2，与深渊项目 90 个手工节点
    # 逐字段对齐）：
    #   data = {label, assetType: "keyframe", frame_type, variant, groupKey,
    #           shot_id, filePath(/oss/), generation_prompt, isPrimaryView,
    #           state, tags:["○ 待选"]}
    #
    # 三态 curation 契约（护栏——StoryboardTimeline.tsx deriveInitialCuration
    # + patchFrameNode）：所有变体默认待选 candidate（不自动选 v1）；用户
    # 点选后 patchFrameNode 把 isPrimaryView/curationState 写回节点 data。
    # 重跑幂等通过 _load_iframe_curation_snapshot 继承旧值，不覆盖用户选择。

    def _load_iframe_flf_artifacts(
        self,
        result: dict[str, Any],
        workdir: str = "",
    ) -> list[dict[str, Any]]:
        """Load first/last-frame variant artifacts from ``iframe-manifest.json``.

        Called on p11a completion. The manifest is the on-disk SSOT written
        by ``templates/gen_iframes.py`` (one entry per shot: variants list +
        all_first_frames/all_last_frames + prompts). Each variant becomes an
        ``a-flf-{shot_id}-{first|last}-v{N}`` artifact.

        Degrade-tolerant: missing manifest / unreadable / bad shape → ``[]``
        (the pipeline's own artifacts still sync; frames simply stay off the
        canvas, matching today's behavior).

        Args:
            result: The p11a phase result (unused for now — manifest is the
                SSOT, not the phase payload; kept for signature symmetry).
            workdir: Episode workdir; manifest at
                ``{workdir}/assets/P11/iframe-manifest.json``.

        Returns:
            Artifact dicts for ``_extract_artifacts``' standard pipeline
            (``_add_artifact`` shape + keyframe data fields).
        """
        if not workdir:
            return []
        manifest_path = os.path.join(workdir, "assets", "P11", "iframe-manifest.json")
        if not os.path.isfile(manifest_path):
            return []
        try:
            with open(manifest_path, "r", encoding="utf-8") as _f:
                entries = json.load(_f)
        except (OSError, json.JSONDecodeError):
            logger.warning(
                "canvas_sync: iframe-manifest unreadable %s — skipping flf nodes",
                manifest_path, exc_info=True,
            )
            return []
        if not isinstance(entries, list):
            return []

        # 用户已做过的三态 curation 决策（重跑前快照），按 oss filePath 索引。
        curation_snapshot = self._load_iframe_curation_snapshot()

        artifacts: list[dict[str, Any]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            shot_id = str(entry.get("shot_id") or "").strip()
            if not shot_id:
                continue
            for frame_type, all_key, prompt_key in (
                ("first", "all_first_frames", "first_frame_prompt"),
                ("last", "all_last_frames", "last_frame_prompt"),
            ):
                paths = entry.get(all_key)
                if not isinstance(paths, list):
                    paths = []
                # 单变体形态：manifest 只带 first_frame_path 无 all_* 列表。
                if not paths:
                    single = entry.get(
                        "first_frame_path" if frame_type == "first"
                        else "last_frame_path",
                    )
                    if isinstance(single, str) and single:
                        paths = [single]
                prompt = entry.get(prompt_key) or ""
                for path in paths:
                    if not isinstance(path, str) or not path:
                        continue
                    abs_path = path if os.path.isabs(path) else os.path.join(workdir, path)
                    oss_url = _fs_to_oss_url(abs_path)
                    if not oss_url:
                        continue
                    variant = _flf_variant_of(path)  # "v1" / "v2" / …
                    group_key = f"{shot_id}_{frame_type}"
                    # 继承用户 curation（无快照 → 待选 candidate 契约）。
                    prior = curation_snapshot.get(oss_url)
                    is_primary = bool(prior and prior.get("isPrimaryView"))
                    curation_state = (
                        prior.get("curationState")
                        if prior and prior.get("curationState")
                        else "active"
                    )
                    if curation_state == "eliminated":
                        tags = ["✕ 淘汰"]
                    elif is_primary:
                        tags = ["★ 选定"]
                    else:
                        tags = ["○ 待选"]
                    artifacts.append({
                        "id": f"flf-{shot_id}-{frame_type}-{variant}",
                        "label": f"{shot_id} {frame_type} {variant}",
                        "type": "asset",
                        "assetType": "keyframe",
                        "frame_type": frame_type,
                        "variant": variant,
                        "groupKey": group_key,
                        "shot_id": shot_id,
                        "filePath": oss_url,
                        "generation_prompt": prompt,
                        "isPrimaryView": is_primary,
                        "curationState": curation_state,
                        "state": "success",
                        "tags": tags,
                        "description": (
                            f"{'首帧' if frame_type == 'first' else '尾帧'}"
                            f"（I-frame）变体 {variant} for shot {shot_id}"
                        ),
                    })
        return artifacts

    def _load_iframe_curation_snapshot(self) -> dict[str, dict[str, Any]]:
        """Read existing a-flf-* node curation state from db2.sqlite.

        Before a p11a re-sync rebuilds the a-flf-* nodes, capture each
        existing node's user-curation fields (``isPrimaryView`` +
        ``curationState``, the StoryboardTimeline patchFrameNode contract)
        keyed by ``filePath`` — so a re-run preserves the operator's
        variant selections instead of resetting every frame to 待选.

        Read-only + degrade-tolerant: any failure → ``{}`` (fresh-canvas
        semantics; all variants render candidate).
        """
        db_path = _locate_canvas_db()
        _proj = self._client._project_id if self._client else None
        _ep = self._client._episodes_id if self._client else None
        if not db_path or _proj is None:
            return {}
        try:
            import sqlite3 as _sql
            conn = _sql.connect(db_path)
            conn.row_factory = _sql.Row
            rows = conn.execute(
                "SELECT data FROM canvas_nodes "
                "WHERE project_id = ? AND episodes_id = ? AND id LIKE 'a-flf-%'",
                (_proj, _ep),
            ).fetchall()
            conn.close()
        except Exception:
            return {}
        snapshot: dict[str, dict[str, Any]] = {}
        for r in rows:
            try:
                data = json.loads(r["data"]) if r["data"] else {}
            except (json.JSONDecodeError, TypeError):
                continue
            fp = data.get("filePath")
            if isinstance(fp, str) and fp:
                snapshot[fp] = {
                    "isPrimaryView": bool(data.get("isPrimaryView")),
                    "curationState": data.get("curationState") or "active",
                }
        return snapshot

    def _build_gate_node(
        self,
        gate_id: str,
        payload: dict[str, Any],
        approved: bool,
    ) -> dict[str, Any]:
        """Build a gate-resolution canvas node (``g-{gate_id}``).

        On approve the node carries ``reviewStatus=approved`` + a
        ``success`` state; the canvas UI renders it as a confirmed
        milestone.

        Args:
            gate_id: Gate identifier.
            payload: Gate outcome payload (may carry ``note`` / ``judge``).
            approved: True on approve, False otherwise.

        Returns:
            ``node_data`` dict for ``canvas_graph.upsert_node``.
        """
        note = payload.get("note", "")
        description = f"✅ Gate {gate_id} approved" if approved else f"⛔ Gate {gate_id} rejected"
        if note:
            description += f": {note}"
        return {
            "type": "suggestion",
            "position": {"x": 1500, "y": 200},
            "size": {"width": 200, "height": 100},
            "state": "success" if approved else "error",
            "branchId": "main",
            "phaseIndex": 0,
            "phaseName": f"Gate: {gate_id}",
            # C3: write TOP-LEVEL reviewStatus (the contract field) so the
            # canvas_nodes.review_status column is set. data.reviewStatus is
            # kept below as a frontend fallback (do not remove).
            "reviewStatus": "approved" if approved else "rejected",
            "data": {
                "label": f"Gate: {gate_id}",
                "description": description,
                "content": description,
                "tags": ["gate", "approved" if approved else "rejected"],
                "state": "success" if approved else "error",
                "reviewStatus": "approved" if approved else "rejected",
                "gateId": gate_id,
                "category": "gate",
            },
        }


# ─── helpers ───────────────────────────────────────────────────────────


def _infer_stage(phase_id: str) -> str:
    """Best-effort stage inference from a phase id.

    The Node.js path receives an explicit ``stage`` field; the v5.0
    runner currently passes only ``phase_id``. This helper extracts the
    suffix after the first underscore (``"p01_hook_topic" → "hook_topic"``)
    so ``default_phase_mapper``'s prefix match still works. Falls back
    to the full id.
    """
    if "_" in phase_id:
        # Drop the leading p01_ / p02_ prefix, keep the rest.
        return phase_id.split("_", 1)[1]
    return phase_id


def _build_node_from_phase_result(
    phase_id: str,
    result: dict[str, Any],
    *,
    subscriber: Optional["CanvasSyncSubscriber"] = None,
) -> list[dict[str, Any]]:
    """Single testable mapping entry point: ``phase_result`` → canvas nodes.

    This is the ONE function both ``sync_phase_result()`` (standalone API)
    and ``CanvasSyncSubscriber.on_phase_complete()`` funnel through for
    node construction. It builds the list of ``node_data`` dicts that
    would be POSTed to ``/api/v2/canvas/nodes`` — without performing any
    HTTP I/O — so tests can drive the mapping directly.

    Contract (Phase 43 SYNCSIDE-03):
        Every key from the input artifact's ``params.*`` dict is forwarded
        into the returned ``node_data["data"]`` field. ``test_canvas_sync_
        params_forwarding.py`` asserts this for a representative param set.

    Args:
        phase_id: Phase identifier (e.g. ``"p04_character_design"``).
        result: Phase result dict ``{"phase", "outputs", "gate", ...}``.
            Accepts the persisted-checkpoint wrapper shape too:
            ``{"status", "result": {...}}`` is unwrapped automatically.
        subscriber: Optional subscriber whose mapping methods to use. If
            ``None``, a fresh subscriber is constructed with a no-op
            ``CanvasClient`` — sufficient for pure mapping, no canvas I/O.

    Returns:
        List of ``node_data`` dicts ready for canvas POST. The first item
        is always the phase summary node; subsequent items are artifact
        child nodes extracted from ``result["outputs"]``.

    Raises:
        Nothing on mapping failure — degrades to an empty list (or just
        the phase summary node) and logs a warning, mirroring
        ``on_phase_complete``'s degrade-tolerant contract.
    """
    # Unwrap persisted-checkpoint wrapper if present (mirrors
    # sync_phase_result's shape guard — single source of truth).
    if isinstance(result, dict) and isinstance(result.get("result"), dict) \
            and not isinstance(result.get("outputs"), dict):
        result = result["result"]

    if subscriber is None:
        # No-op client for pure-mapping use cases. CanvasClient is only
        # needed for actual POST/load; the mapping helpers don't call it.
        subscriber = CanvasSyncSubscriber(_NullCanvasClient())

    # Reuse the same extraction + building path as on_phase_complete.
    # We deliberately do NOT replicate the logic here — criteria 2 forbids
    # forked mapping. The subscriber methods remain the authoritative
    # implementation; this function is the named entry point.
    outputs = result.get("outputs") or {}
    if not isinstance(outputs, dict):
        outputs = {}

    nodes: list[dict[str, Any]] = []
    try:
        nodes.append(subscriber._build_phase_node(phase_id, result))
    except Exception:  # noqa: BLE001 — degrade-tolerant, mirror on_phase_complete
        logger.warning(
            "_build_node_from_phase_result: phase node build failed for %s",
            phase_id, exc_info=True,
        )

    try:
        artifacts = subscriber._extract_artifacts(phase_id, result)
        for artifact in artifacts:
            try:
                nodes.append(subscriber._build_artifact_node(phase_id, artifact))
            except Exception:  # noqa: BLE001 — one bad artifact shouldn't sink the rest
                logger.warning(
                    "_build_node_from_phase_result: artifact build failed "
                    "for %s / %s",
                    phase_id, artifact.get("id", "?"), exc_info=True,
                )
    except Exception:  # noqa: BLE001 — degrade-tolerant
        logger.warning(
            "_build_node_from_phase_result: artifact extraction failed "
            "for %s",
            phase_id, exc_info=True,
        )
    return nodes


class _NullCanvasClient:
    """No-op CanvasClient for pure-mapping tests of _build_node_from_phase_result.

    The mapping helpers (_build_phase_node / _build_artifact_node /
    _extract_artifacts) do not call any CanvasClient methods — they only
    read/write the in-memory graph and return node_data dicts. This stub
    satisfies the constructor signature so a subscriber can be created
    without spinning up HTTP.
    """

    _project_id = 0
    _episodes_id = 0

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass


def _locate_canvas_db() -> str | None:
    """Locate the kais-aigc-platform ``db2.sqlite`` for direct sqlite3 access.

    Used by three-layer sync (``_sync_asset_to_oassets_oimage``) and the
    integrity audit, which bypass the HTTP API (the assets-registry ``type``
    enum excludes ``keyframe``, so iframe/keyframe assets must be written
    directly). Tries the canonical path, then ``KAIS_CANVAS_DB``.
    """
    for candidate in (
        "/data/workspace/kais-aigc-platform/data/db2.sqlite",
        os.environ.get("KAIS_CANVAS_DB", ""),
    ):
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


def audit_three_layer_integrity(project_id: int | None = None) -> dict[str, Any]:
    """Standalone three-layer integrity audit (read-only).

    Checks ``canvas_nodes(type=asset, has filePath)`` ↔ ``o_image`` ↔
    ``o_assets`` for ``project_id`` (defaults to the env/default project).
    FilePath matching is query-string-normalized (``?v=…`` cache busters
    stripped) because canvas nodes cache-bust display URLs while ``o_image``
    stores the clean path.

    Runnable standalone::

        python3 -c "from plugins.kais_aigc.canvas_sync import \
audit_three_layer_integrity as a; import json; print(json.dumps(a(1785508691757),ensure_ascii=False,indent=2))"

    Returns a findings dict: per-layer counts, missing-link lists, and an
    ``isprimary_mismatch`` list (canvas ``isPrimaryView`` vs ``o_assets``).
    """
    import sqlite3

    db_path = _locate_canvas_db()
    if db_path is None:
        return {"error": "db2.sqlite not found", "db": None}

    if project_id is None:
        # 兜底：用环境/默认项目。
        env_pid = os.environ.get("KAIS_PROJECT_ID") or os.environ.get("PROJECT_ID")
        project_id = int(env_pid) if (env_pid and str(env_pid).isdigit()) else 1785508691757

    def _norm(fp: str | None) -> str | None:
        if not fp:
            return None
        fp = fp.strip()
        return fp.split("?", 1)[0] or None

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        nodes = []
        for r in conn.execute(
            "SELECT id, data FROM canvas_nodes WHERE project_id=? AND type='asset'",
            (project_id,),
        ):
            try:
                d = json.loads(r["data"] or "{}")
            except Exception:
                d = {}
            fp = _norm(d.get("filePath") or d.get("thumbnailUrl"))
            nodes.append({
                "id": r["id"], "fp": fp,
                "ip": 1 if d.get("isPrimaryView") else 0,
                "assetType": d.get("assetType"),
                "curationState": d.get("curationState"),
            })

        oimage_by_fp: dict[str, sqlite3.Row] = {}
        for r in conn.execute("SELECT * FROM o_image").fetchall():
            fp = _norm(r["filePath"])
            if fp:
                oimage_by_fp[fp] = r
        oassets_by_iid: dict[int, sqlite3.Row] = {}
        for r in conn.execute(
            "SELECT * FROM o_assets WHERE projectId=?", (project_id,)
        ).fetchall():
            if r["imageId"] is not None:
                oassets_by_iid.setdefault(r["imageId"], r)

        missing_oimage: list[str] = []
        missing_oassets: list[str] = []
        isprimary_mismatch: list[dict[str, Any]] = []
        backref_empty = 0
        matched = 0
        for n in nodes:
            if not n["fp"]:
                continue
            oi = oimage_by_fp.get(n["fp"])
            if not oi:
                missing_oimage.append(n["id"])
                continue
            oa = oassets_by_iid.get(oi["id"])
            if not oa:
                missing_oassets.append(n["id"])
                continue
            matched += 1
            if oi["assetsId"] in (None, 0, ""):
                backref_empty += 1
            if (oa["isPrimaryView"] or 0) != n["ip"]:
                isprimary_mismatch.append({
                    "canvas": n["id"], "o_assets": oa["id"],
                    "canvas_isPrimaryView": n["ip"],
                    "o_assets_isPrimaryView": oa["isPrimaryView"],
                    "curationState": n["curationState"],
                })
    finally:
        conn.close()

    return {
        "db": db_path,
        "project_id": project_id,
        "canvas_asset_nodes_with_filePath": sum(1 for n in nodes if n["fp"]),
        "three_layer_matched": matched,
        "missing_oimage": missing_oimage,
        "missing_oassets": missing_oassets,
        "isprimary_mismatch": isprimary_mismatch,
        "oimage_assetsId_backref_empty": backref_empty,
        "ok": not (missing_oimage or missing_oassets or isprimary_mismatch or backref_empty),
    }


def _ensure_project_exists(base_url: str, project_id: int) -> None:
    """Ensure the project exists in the canvas platform's o_project table.

    The Canvas API v2 ``save-v2`` endpoint stores FlowGraph data in
    ``o_agentWorkData`` — completely independent of the ``o_project`` table.
    The frontend canvas UI populates its project selector from ``o_project``.
    If a FlowGraph is saved with a projectId that doesn't exist in o_project,
    the data is stored correctly but **invisible** in the UI.

    This function first checks via the HTTP project list API. If the project
    is missing, it inserts a record directly into the SQLite database (the
    ``addProject`` HTTP endpoint uses ``Date.now()`` as the ID, which won't
    match our projectId — so direct DB insertion is the only reliable path).

    Degrade-tolerant: if the check or creation fails, it logs a WARNING and
    returns — the subscriber still works (data can be loaded via load-v2,
    just not visible in the project selector).
    """
    try:
        import httpx as _httpx

        # Check if project already exists via HTTP project list API.
        r = _httpx.post(
            f"{base_url}/api/canvas/projects",
            json={},
            timeout=5,
        )
        if r.status_code == 200:
            projects = r.json().get("data", []) or []
            for p in projects:
                if p.get("id") == project_id:
                    return  # Already exists — nothing to do.

        # Project not found — insert directly into SQLite.
        # We can't use /api/project/addProject because it generates its own
        # id via Date.now(), which won't match our project_id.
        logger.info(
            "canvas sync: projectId=%s not in o_project — inserting record",
            project_id,
        )

        import sqlite3
        import time as _time

        # Locate the database — try common paths relative to the canvas server.
        db_candidates = [
            "/data/workspace/kais-aigc-platform/data/db2.sqlite",
            os.environ.get("KAIS_CANVAS_DB", ""),
        ]
        db_path = None
        for candidate in db_candidates:
            if candidate and os.path.isfile(candidate):
                db_path = candidate
                break

        if db_path is None:
            logger.warning(
                "canvas sync: cannot locate db2.sqlite for projectId=%s — "
                "set KAIS_CANVAS_DB env var or create the o_project record "
                "manually. Canvas data will exist but not be visible in the "
                "project selector.",
                project_id,
            )
            return

        now_ms = int(_time.time() * 1000)
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                """INSERT OR IGNORE INTO o_project
                   (id, name, intro, type, mode, createTime, userId)
                   VALUES (?, ?, ?, ?, ?, ?, 1)""",
                (
                    project_id,
                    f"Pipeline Project {project_id}",
                    "Auto-created by canvas sync",
                    "movie-pipeline",
                    "canvas-v2",
                    now_ms,
                ),
            )
            conn.commit()
            logger.info(
                "canvas sync: created o_project record for projectId=%s in %s",
                project_id,
                db_path,
            )
        finally:
            conn.close()
    except Exception:
        logger.warning(
            "canvas sync: _ensure_project_exists failed for projectId=%s "
            "— canvas data will exist but may not be visible in the "
            "project selector",
            project_id,
            exc_info=True,
        )


def create_new_project(
    *,
    base_url: Optional[str] = None,
    name: str = "",
    intro: str = "Auto-created by kais-movie-pipeline",
) -> dict[str, Any]:
    """Create a brand-new project in the canvas platform and return its IDs.

    This is the **root fix** for the "all projects share the same project_id"
    problem. Instead of relying on a single hardcoded ``KAIS_CANVAS_PROJECT_ID``
    env var, this function allocates a fresh project with a unique ID (based on
    ``int(time.time() * 1000)`` — matches the platform's own ID generation
    pattern) and inserts it into ``o_project`` directly.

    The returned dict contains everything the runner needs to wire canvas sync
    for this specific project:

        {"project_id": 1782600000000, "episodes_id": 1, "name": "新项目"}

    Usage in runner CLI::

        python -m pipeline.runner --episode ep-001 --project-name "新项目"

    The runner calls this function, gets back a fresh project_id, and passes
    it to ``register_canvas_sync()`` — each project gets its own isolated
    canvas graph.

    Degrade-tolerant: if project creation fails, logs a WARNING and returns
    a fallback dict with the env-var default project_id (so the pipeline
    still runs, just on the shared project).

    Args:
        base_url: Canvas platform URL. Falls back to ``KAIS_CANVAS_URL``.
        name: Human-readable project name. Required — appears in the
            frontend project selector.
        intro: Optional project description.

    Returns:
        ``{"project_id": int, "episodes_id": int, "name": str}``.
    """
    resolved_url = base_url or os.environ.get("KAIS_CANVAS_URL", "")
    try:
        import sqlite3
        import time as _time

        # ── Dedup: reuse existing project with same name if one exists ──
        # This prevents duplicate project IDs when the pipeline is restarted
        # multiple times with the same --project-name. The previous behavior
        # unconditionally created a new project_id on every invocation.
        db_candidates = [
            "/data/workspace/kais-aigc-platform/data/db2.sqlite",
            os.environ.get("KAIS_CANVAS_DB", ""),
        ]
        db_path = None
        for candidate in db_candidates:
            if candidate and os.path.isfile(candidate):
                db_path = candidate
                break

        if db_path:
            conn = sqlite3.connect(db_path)
            try:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id FROM o_project WHERE name = ? ORDER BY id DESC LIMIT 1",
                    (name,),
                )
                row = cur.fetchone()
                if row:
                    project_id = row[0]
                    logger.info(
                        "create_new_project: reusing existing project id=%s name=%r",
                        project_id, name,
                    )
                    return {
                        "project_id": project_id,
                        "episodes_id": 1,
                        "name": name,
                    }
            finally:
                conn.close()

        # Generate a unique project ID (same pattern as the platform's
        # addProject which uses Date.now()).
        project_id = int(_time.time() * 1000)

        # Locate the database.
        db_candidates = [
            "/data/workspace/kais-aigc-platform/data/db2.sqlite",
            os.environ.get("KAIS_CANVAS_DB", ""),
        ]
        db_path = None
        for candidate in db_candidates:
            if candidate and os.path.isfile(candidate):
                db_path = candidate
                break

        if db_path is None:
            logger.warning(
                "create_new_project: cannot locate db2.sqlite — "
                "falling back to env-var project_id"
            )
            return {
                "project_id": _env_int_safe("KAIS_CANVAS_PROJECT_ID", 1),
                "episodes_id": 1,
                "name": name,
            }

        now_ms = int(_time.time() * 1000)
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                """INSERT OR IGNORE INTO o_project
                   (id, name, intro, type, mode, createTime, userId)
                   VALUES (?, ?, ?, ?, ?, ?, 1)""",
                (
                    project_id,
                    name or f"Pipeline Project {project_id}",
                    intro,
                    "movie-pipeline",
                    "canvas-v2",
                    now_ms,
                ),
            )
            conn.commit()
            logger.info(
                "create_new_project: created o_project id=%s name=%r in %s",
                project_id, name, db_path,
            )
        finally:
            conn.close()

        return {
            "project_id": project_id,
            "episodes_id": 1,
            "name": name,
        }
    except Exception:
        logger.warning(
            "create_new_project failed — falling back to env-var project_id",
            exc_info=True,
        )
        return {
            "project_id": _env_int_safe("KAIS_CANVAS_PROJECT_ID", 1),
            "episodes_id": 1,
            "name": name,
        }


def _env_int_safe(key: str, default: int) -> int:
    """Read an integer from an env var, returning default if absent/invalid."""
    val = os.environ.get(key)
    if not val:
        return default
    try:
        return int(val)
    except ValueError:
        return default


# ─── ad-hoc sync API (for agent-driven execution) ──────────────────────


def sync_phase_result(
    *,
    episode_id: str,
    phase_id: str,
    result: dict[str, Any],
    base_url: Optional[str] = None,
    project_id: Optional[int] = None,
    episodes_id: Optional[int] = None,
) -> bool:
    """Sync a single phase result to the canvas **without** a running runner.

    This is the **root fix** for the "ad-hoc execution doesn't sync" problem.
    When an agent executes pipeline phases manually via ``delegate_task``
    (instead of through ``python -m pipeline.runner``), the
    ``CanvasSyncSubscriber`` is never registered — phase results exist on
    disk but the canvas shows zero nodes.

    This function creates a **standalone** ``CanvasSyncSubscriber`` on the
    fly, calls its ``on_phase_complete`` method once, then discards it. No
    ``RunnerConfig`` needed, no runner loop needed.

    Usage from an agent session::

        from plugins.kais_aigc.canvas_sync import sync_phase_result

        sync_phase_result(
            episode_id="ep-001",
            phase_id="p04_character_design",
            result={
                "phase": "p04_character_design",
                "outputs": {...},
                "gate": None,
            },
        )

    Or equivalently via the hermes ``kais_canvas_sync`` tool::

        kais_canvas_sync(action="sync_phase",
            episode_id="ep-001",
            phase_id="p04_character_design",
            result={...},
            project_id=1782600000000,
        )

    Degrade-tolerant: returns ``False`` on any failure (canvas unreachable,
    schema mismatch, etc.) without raising. The agent can check the return
    value and decide whether to retry or proceed.

    Args:
        episode_id: Episode identifier.
        phase_id: Phase identifier (e.g. ``"p04_character_design"``).
        result: Phase result dict with shape
            ``{"phase": ..., "outputs": {...}, "gate": ...}``.
        base_url: Canvas platform URL. Falls back to ``KAIS_CANVAS_URL``
            env var.
        project_id: Canvas project ID. Falls back to
            ``KAIS_CANVAS_PROJECT_ID`` env var.
        episodes_id: Canvas episodes ID. Falls back to
            ``KAIS_CANVAS_EPISODES_ID`` env var.

    Returns:
        ``True`` if the sync succeeded, ``False`` if it degraded.
    """
    resolved_url = base_url or os.environ.get("KAIS_CANVAS_URL", "")
    resolved_pid = project_id or _env_int_safe("KAIS_CANVAS_PROJECT_ID", 0)
    resolved_eid = episodes_id or _env_int_safe("KAIS_CANVAS_EPISODES_ID", 1)

    if not resolved_url or not resolved_pid:
        logger.warning(
            "sync_phase_result: missing canvas config "
            "(url=%r project_id=%s) — sync skipped",
            resolved_url, resolved_pid,
        )
        return False

    # ─── Shape guard (2026-07-15) ───────────────────────────────────
    # ``on_phase_complete`` expects the LIVE phase result shape
    # ``{phase, outputs, gate, ...}``. Callers sometimes pass the
    # persisted wrapper instead:
    #   - PipelineStateStore checkpoint: ``{status, completed_at, result: {...}}``
    #   - run_episode checkpoint:        ``{phase, result: {...}}``
    # Both have a ``result`` key whose value is the real phase result.
    # Without unwrapping, ``_extract_artifacts`` finds no ``outputs`` key,
    # builds an empty artifact set, and ``save_canvas`` UPSERTS the whole
    # graph without this phase's artifact nodes — silently DELETING them.
    # Detect the wrapper and unwrap before delegating.
    if isinstance(result, dict) and isinstance(result.get("result"), dict) \
            and not isinstance(result.get("outputs"), dict):
        result = result["result"]

    try:
        client = CanvasClient(
            base_url=resolved_url,
            project_id=resolved_pid,
            episodes_id=resolved_eid,
        )
        sub = CanvasSyncSubscriber(client)
        # The mapping logic itself runs through _build_node_from_phase_result
        # (Phase 43 SYNCSIDE-02 single-path contract). on_phase_complete
        # orchestrates the I/O (load → build → save); the node construction
        # inside it delegates to the same _build_phase_node /
        # _build_artifact_node methods that _build_node_from_phase_result
        # calls explicitly. No forked mapping logic.
        saved_ok = sub.on_phase_complete(episode_id, phase_id, result)
        # B-2: on_phase_complete 对网络类失败（load/save 降级 envelope）是
        # degrade-tolerant 的（不抛异常、返回 None）——此前无条件 return True，
        # 破坏 "returns False on any failure" 契约，agent 手动补同步会误报
        # 成功。让 on_phase_complete 显式返回 bool（降级 → False）。
        if saved_ok is False:
            logger.warning(
                "sync_phase_result: phase %s sync degraded (load/save "
                "envelope) — returning False (project=%s episodes=%s)",
                phase_id, resolved_pid, resolved_eid,
            )
            return False
        logger.info(
            "sync_phase_result: synced phase %s for episode %s "
            "(project=%s episodes=%s)",
            phase_id, episode_id, resolved_pid, resolved_eid,
        )
        return True
    except Exception as exc:
        _log_sync_error(
            phase_id, episode_id,
            error_type=type(exc).__name__,
            detail=str(exc),
            exc_info=exc,
        )
        return False
    finally:
        # B-7: 每次调用 new 出来的 CanvasClient 用完必须 close——否则
        # httpx 连接池泄漏（每次调用泄漏一个连接）。
        try:
            client.close()
        except Exception:  # noqa: BLE001 — close must not mask the result
            pass


# ─── registration API ─────────────────────────────────────────────────


def register_canvas_sync(
    *,
    base_url: Optional[str],
    project_id: int,
    episodes_id: int,
    runner_config: Any,
    transport: Optional[httpx.BaseTransport] = None,
    agent_name: str = "",
) -> CanvasSyncSubscriber:
    """Construct client + subscriber and wire both trigger callbacks.

    Single registration call wires both trigger paths (PATTERN 7):
      1. ``runner_config.on_phase_complete`` ← subscriber handler
      2. ``runner_config.on_gate_resolved`` ← subscriber handler
      3. ``runner_hooks.set_gate_resolved_hook(...)`` ← same handler
         (module-level gate hook — D-37-07).

    Args:
        base_url: Canvas platform base URL. ``None`` falls back to
            ``KAIS_CANVAS_URL`` env var then ``CanvasClient.DEFAULT_BASE_URL``.
        project_id: Canvas project id.
        episodes_id: Canvas episodes id.
        runner_config: Object with settable ``on_phase_complete`` /
            ``on_gate_resolved`` attributes (duck-typed to avoid the
            circular import with the runner module).
        transport: Optional ``httpx.BaseTransport`` for test injection.
        agent_name: Optional label prefix.

    Returns:
        The constructed ``CanvasSyncSubscriber``. Callers should hold
        the reference (prevents GC of the callback target).
    """
    client = CanvasClient(
        base_url=base_url,
        project_id=project_id,
        episodes_id=episodes_id,
        transport=transport,
    )

    # Ensure the project exists in o_project so the frontend canvas UI can see
    # it in the project selector. save-v2 stores FlowGraph data independently of
    # the o_project table — without this check, the data exists but is invisible.
    _ensure_project_exists(client._base_url, project_id)

    sub = CanvasSyncSubscriber(client, agent_name=agent_name)
    runner_config.on_phase_complete = sub.on_phase_complete
    runner_config.on_gate_resolved = sub.on_gate_resolved
    # Module-level gate hook (D-37-07). Imported lazily so this module
    # remains importable even when review_gates isn't installed.
    try:
        from plugins.review_gates import runner_hooks

        runner_hooks.set_gate_resolved_hook(sub.on_gate_resolved)
    except ImportError:
        logger.debug(
            "review_gates.runner_hooks not importable — "
            "gate-resolved hook not registered (canvas sync still wired "
            "for phase completion via runner_config)"
        )
    return sub
