"""gate_config.py — gates.yaml loader + validator (Phase 34-02, SC#2 + Phase 8 FIX-01).

Phase 8 / Plan 08-01 (FIX-01/A5) refactor: gates.yaml schema is now
**phase_id-keyed** rather than carrying a standalone ``gate_id`` field.
The gate_id is auto-derived at runtime via ``derive_gate_id(phase_id)`` —
single source of truth for both spelling and lookup.

Phase 34-02 originally introduced the loader; Phase 40 Plan 02 (GATE-04)
expanded 8 → 11 gates additively; Phase 8 reconciled the YAML against
PHASE_REGISTRY (deleted p04/p08/p09 spurious entries, added missing
p05/p07 entries).

Exports:
- ``derive_gate_id(phase_id) -> str`` — canonical SSoT rule.
- ``GATE_REGISTRY: dict[str, dict]`` — raw YAML entries keyed by phase_id.
- ``load_gates() -> dict[str, dict]`` — re-reads + validates; idempotent.
- ``to_gate_config(phase_id_or_gate_id) -> GateConfig`` — converts a raw
  entry into the frozen ``GateConfig`` dataclass defined by Plan 34-01
  (``gate.py``). Accepts both phase_id and legacy gate_id forms.
- ``gate_id_to_phase_id(gate_id) -> str`` — reverse lookup.
- ``cross_validate_phase_gates(phases_iterable, gates_yaml_keys)`` —
  bidirectional SSoT validation (runs at runner startup).
- ``GateConfigError`` — raised on missing file, malformed YAML, or failed
  validation.

Architectural decisions:
- D-34-02: YAML is loaded eagerly at import. Hot-reload is NOT supported;
  changing a gate definition requires restarting the hermes-agent process.
- D-34-03: ``pyyaml`` is the ONE third-party dep added in Phase 34. It is
  already a transitive dep of hermes-agent (the plugin loader uses it for
  ``plugin.yaml`` parsing), so no ``pyproject.toml`` change is needed.
- D-34-04: ``GateConfig`` (from YAML) is ``@dataclass(frozen=True)`` for
  hashability + immutability. Runtime ``Gate`` instances are mutable.
- D-08-01: gate_id is derived from phase_id at lookup time; the YAML no
  longer carries a ``gate_id`` field. The dict KEY IS the phase_id. A
  redundant ``phase`` field is kept inside each entry for callers that
  historically read ``entry["phase"]`` (Plan 34-01 GateConfig.phase).

Backward-compat note (Phase 8 / Rule 3 — blocking issue):
``to_gate_config()`` signature nominally changed from ``gate_id`` to
``phase_id`` per plan step 7. To avoid breaking pre-Phase-8 callers and
tests, the function accepts BOTH forms: a direct phase_id OR a legacy
gate_id (resolved via ``gate_id_to_phase_id`` which checks both the
canonical derived form and the static _LEGACY_GATE_ID_TO_PHASE_ID map).
Same for callers in ``runner_hooks.py`` and ``tools.py``.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable

import yaml  # pyyaml — already transitive dep (plugin loader uses it for plugin.yaml)

if TYPE_CHECKING:  # pragma: no cover — typing only, no runtime import
    from plugins.review_gates.gate import GateConfig

logger = logging.getLogger(__name__)


class GateConfigError(Exception):
    """Raised when gates.yaml is missing, malformed, or fails validation."""


_YAML_PATH: Path = Path(__file__).parent / "gates.yaml"

# Exact gate count invariant. 2026-08-18 冗余审核体系: bumps to 12/13/14/15
# in lock-step with each vision-review node's wiring (yaml entry +
# _GATE_PHASES member + trigger_gate_blocking call land in the SAME commit —
# cross_validate direction (a) forbids yaml entries for GATE_ID=None phases).
# 2026-08-19 音频篇: 15 -> 16 (Gate 16 p10c-gate, kais-ear transcription
# fidelity review).
# 2026-08-25 T2: 16 → 17 — Gate 17 p14-gate (quality audit, blocking_policies)
# 2026-08-26 B1 (NC-VAR-01): 17 → 19 — 18=Gate NC-1 nc01 解说词审,
# 19=Gate NC-8 nc08 终审 (narration_comic 变体骨架的两道 HIL 门).
# MV-VAR (2026-10-15): 19 → 21 — 20=Gate MV-1 mv01 歌曲包入料审,
# 21=Gate MV-3 mv03 音乐锚定分镜审 (MV 变体 DAG 的两道 HIL 门,
# mv-variant-dag/DESIGN.md §5.4).
_EXPECTED_GATE_COUNT = 21  # 21 = 17 drama gates + 2 nc gates + 2 mv gates

# Phases that have blocking_policies in gates.yaml for evaluate_gate() usage
# (v2 consistency layer) but do NOT use the trigger_gate_blocking /
# _GATE_PHASES runner injection mechanism. These phases raise
# QualityGateRejection directly and use evaluate_gate() internally in v2 mode.
# cross_validate direction (a) is relaxed for these phases.
_EVALUATE_GATE_ONLY_PHASES: frozenset[str] = frozenset({
    "p14_quality_audit",  # 裁决1: flag=off 时不走 trigger_gate，v2 时内部调 evaluate_gate
})


# ---------------------------------------------------------------------------
# Phase 8 / 08-01 FIX-01: gate_id Single Source of Truth
# ---------------------------------------------------------------------------

# Canonical derivation rule: extract the leading p\d+[a-z0-9]* token (full
# sub-phase id, digits included) from phase_id and append "-gate". Examples:
#   p01_hook_topic      → "p01-gate"
#   p13_delivery        → "p13-gate"
#   p06_spatio_temporal_script → "p06-gate"
#   p11b_final_render   → "p11b-gate"   (2026-08-18 冗余审核体系: full-token
#                       derivation — p11a/p11a0/p11b/p11c previously ALL
#                       collided on "p11-gate"; the legacy alias is kept in
#                       _LEGACY_GATE_ID_TO_PHASE_ID below)
#   p11a0_iframe_qc     → "p11a0-gate"
# Redline sub-keys carry an _redline_* suffix that must be stripped first:
#   p13_delivery_redline_emotion → "p13-gate"
# NC-VAR-01 (2026-08-26 B1): nc\d+ tokens derive the same way (narration_comic
# variant registry — phases/__init__.py 的 GATE_ID SSoT 派生循环对 nc01/
# nc08 也走本函数，不识别会 import 期崩溃):
#   nc01_narration      → "nc01-gate"   (Gate NC-1 解说词审)
#   nc08_qc_delivery    → "nc08-gate"   (Gate NC-8 成片终审)
# MV-VAR (2026-10-15): mv\d+ tokens derive the same way (MV variant registry —
# 同款 import 期崩溃风险):
#   mv01_song_intake          → "mv01-gate"  (Gate MV-1 歌曲包入料审)
#   mv03_music_shot_breakdown → "mv03-gate"  (Gate MV-3 音乐锚定分镜审)
_PHASE_PREFIX_RE = re.compile(r"^(p\d+[a-z0-9]*|nc\d+[a-z0-9]*|mv\d+[a-z0-9]*)")
_REDLINE_SUFFIX_RE = re.compile(r"_redline_[a-z_]+$")


def derive_gate_id(phase_id: str) -> str:
    """Canonical SSoT rule: derive gate_id from phase_id.

    Extracts the leading ``p\\d+`` token (e.g. "p01" from "p01_hook_topic")
    and appends "-gate" (e.g. "p01-gate"). For redline sub-keys, the
    ``_redline_*`` suffix is stripped before deriving, so all three redline
    gates under p13_delivery derive to "p13-gate" (matching the main
    p13_delivery entry). NC-VAR-01 (2026-08-26 B1): ``nc\\d+`` tokens derive
    identically (nc01_narration → "nc01-gate").

    Args:
        phase_id: Phase identifier (e.g. "p01_hook_topic",
            "p13_delivery_redline_emotion").

    Returns:
        Derived gate_id string (e.g. "p01-gate", "p13-gate").

    Raises:
        GateConfigError: if phase_id does not start with a p\\d+ token.
    """
    if not isinstance(phase_id, str) or not phase_id:
        raise GateConfigError(
            f"derive_gate_id: phase_id must be non-empty str, got {phase_id!r}"
        )
    # Strip _redline_* suffix if present (redline gates share the base phase's gate)
    base = _REDLINE_SUFFIX_RE.sub("", phase_id)
    m = _PHASE_PREFIX_RE.match(base)
    if not m:
        raise GateConfigError(
            f"derive_gate_id: phase_id {phase_id!r} does not start with p\\d+ token"
        )
    return f"{m.group(1)}-gate"


# Legacy gate_id → phase_id map for backward compatibility with pre-Phase-8
# callers (runner_hooks, tools, tests). The canonical SSoT is now the derived
# form (derive_gate_id(phase_id) — e.g. "p01-gate"), but legacy callers may
# still pass the historical raw gate_id. This map lets the runtime accept both
# forms without forcing every caller to migrate atomically with the gates.yaml
# schema refactor.
_LEGACY_GATE_ID_TO_PHASE_ID: dict[str, str] = {
    # 8 V8.6 gates (pre-Phase-8 raw gate_ids)
    "topic-gate": "p01_hook_topic",
    "outline-gate": "p02_outline",
    "script-gate": "p03_script_audit",
    # character-gate / scene-select-gate / shot-breakdown-gate were on phases
    # with GATE_ID=None after Phase 8 reconciliation — they no longer have
    # gates.yaml entries, so legacy lookups for them raise (correct).
    "render-gate": "p11_video_render",
    "delivery-gate": "p13_delivery",
    # 2026-08-18 冗余审核体系: derive_gate_id now derives the FULL sub-phase
    # token (p11b_final_render → "p11b-gate"). Historical review-outcomes
    # rows, in-flight webhook callbacks, and older tooling still say
    # "p11-gate" — map them to p11b_final_render (the render gate's home
    # both before and after the change).
    "p11-gate": "p11b_final_render",
    # 3 Phase 40 redline gates (Plan-01 detector names — kept as canonical
    # redline gate_ids since the DETECTOR_REGISTRY keys on them).
    "redline_emotion_desensitize": "p13_delivery_redline_emotion",
    "redline_no_cold_open": "p13_delivery_redline_no_cold_open",
    "redline_unfinished_ending": "p13_delivery_redline_unfinished",
}


def gate_id_to_phase_id(gate_id: str) -> str:
    """Reverse lookup: given a gate_id, return the canonical phase_id
    registered in gates.yaml.

    Phase 8 / 08-01 (FIX-01): the canonical gate_id form is the derived
    value (e.g. "p01-gate" from p01_hook_topic). For backward compatibility
    with pre-Phase-8 callers / tests, this helper ALSO accepts legacy raw
    gate_ids via the static ``_LEGACY_GATE_ID_TO_PHASE_ID`` map (e.g.
    "topic-gate" → "p01_hook_topic").

    Used by runtime callers (runner_hooks, tools) that historically operated
    on gate_id but now need to look up config via phase_id. Linear scan over
    the (small, 11-entry) registry.

    Args:
        gate_id: Derived gate_id (e.g. "p01-gate", "p13-gate") OR legacy raw
            gate_id (e.g. "topic-gate", "render-gate") for backward compat.

    Returns:
        The canonical phase_id key in gates.yaml whose derived gate_id
        matches. For redline gates (which all derive to "p13-gate"), the
        MAIN p13_delivery key is returned (not the redline sub-key) —
        callers that need redline-specific config should look up by
        the sub-key directly.

    Raises:
        GateConfigError: if no phase in gates.yaml derives to ``gate_id``.
    """
    # 1. Legacy raw gate_id → phase_id direct map (backward compat).
    legacy = _LEGACY_GATE_ID_TO_PHASE_ID.get(gate_id)
    if legacy is not None:
        return legacy
    registry = load_gates()
    matches = [
        pid for pid in registry.keys()
        if derive_gate_id(pid) == gate_id
    ]
    if not matches:
        raise GateConfigError(
            f"gate_id_to_phase_id: no gates.yaml entry derives to {gate_id!r}"
        )
    # Prefer non-redline main entry if present (e.g. p13_delivery over
    # p13_delivery_redline_*). Redline sub-keys share the base phase.
    main_entries = [m for m in matches if "_redline_" not in m]
    if main_entries:
        return main_entries[0]
    # All matches are redline sub-keys (shouldn't happen — there's always
    # a main p13_delivery entry). Return the first for determinism.
    return matches[0]


# ---------------------------------------------------------------------------
# Required fields on every gate entry (per ROADMAP SC#2 + CF-02).
# NOTE: ``gate_id`` is NO LONGER required (Phase 8 FIX-01 — derived from key).
# NOTE: ``callback_url`` is intentionally OPTIONAL — webhook-mode gates wire
# it at runtime (runner_hooks, Phase 34-03); blocking/polling gates leave null.
# ---------------------------------------------------------------------------

REQUIRED_FIELDS: tuple[str, ...] = (
    "phase",
    "asset_bus_slots_to_lock",
    "reviewer_role",
    "timeout_sec",
    "default_mode",
    "retry_policy",
)

_VALID_MODES = frozenset({"blocking", "webhook", "polling"})

# Phase key pattern: p\d+[a-z0-9]*_<name>[_redline_<sub>]
# The [a-z0-9]* suffix accommodates sub-phases like p11b, p12a, p09b AND
# digit-suffixed micro-phases like p11a0 (2026-08-18 冗余审核体系).
# NC-VAR-01 (2026-08-26 B1): nc\d+ prefix accommodates narration_comic
# variant phase keys (nc01_narration / nc08_qc_delivery).
# MV-VAR (2026-10-15): mv\d+ prefix accommodates MV variant phase keys
# (mv01_song_intake / mv03_music_shot_breakdown). NOTE: DESIGN.md §5.4 只点名
# _PHASE_PREFIX_RE，但 gates.yaml 顶层 key 还要过本 _PHASE_KEY_RE
# （_validate_phase_key）—— 不扩则 load_gates() 对 mv 条目 GateConfigError，
# 与设计自身的 union SSoT 验证策略（§8.2-5）矛盾，故两处 lock-step 同扩。
_PHASE_KEY_RE = re.compile(
    r"^(?:p\d+[a-z0-9]*|nc\d+[a-z0-9]*|mv\d+[a-z0-9]*)_[a-z_]+(?:_redline_[a-z_]+)?$"
)


def load_gates() -> dict[str, dict]:
    """Load and validate ``gates.yaml``.

    Phase 8 / 08-01 (FIX-01): returns ``{phase_id: raw_yaml_dict}`` where
    ``phase_id`` is the gates.yaml top-level key. Each entry's standalone
    ``gate_id`` field has been removed (the dict key IS the phase_id; the
    derived gate_id is computed at lookup time via ``derive_gate_id``).

    Returns a fresh dict on every call (idempotent — re-reads the file;
    no caching at this layer).

    Raises:
        GateConfigError: if the file is missing, the YAML is unparseable,
            the top-level shape is wrong, the gate count is not exactly
            ``_EXPECTED_GATE_COUNT`` (Phase 40 GATE-04 bumped 8 -> 11;
            2026-08-18 冗余审核体系 bumps toward 15 with each vision-review
            node), any
            phase key is malformed, or any entry fails field-level
            validation.
    """
    if not _YAML_PATH.exists():
        raise GateConfigError(f"gates.yaml not found at {_YAML_PATH}")
    try:
        with open(_YAML_PATH, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise GateConfigError(f"gates.yaml parse error: {exc}") from exc

    if not isinstance(doc, dict):
        raise GateConfigError(
            f"gates.yaml top-level must be a mapping, got {type(doc).__name__}"
        )
    if "gates" not in doc:
        raise GateConfigError("gates.yaml missing top-level 'gates' mapping")
    gates_mapping = doc["gates"]
    if not isinstance(gates_mapping, dict):
        raise GateConfigError(
            f"gates.yaml 'gates' must be a mapping (phase_id -> entry), "
            f"got {type(gates_mapping).__name__}"
        )
    if len(gates_mapping) != _EXPECTED_GATE_COUNT:
        raise GateConfigError(
            f"gates.yaml must contain exactly {_EXPECTED_GATE_COUNT} gates "
            f"(found {len(gates_mapping)})"
        )

    registry: dict[str, dict] = {}
    for phase_key, entry in gates_mapping.items():
        _validate_phase_key(phase_key)
        if not isinstance(entry, dict):
            raise GateConfigError(
                f"gates.yaml entry for {phase_key!r} must be a mapping, "
                f"got {type(entry).__name__}"
            )
        # Per plan: NO standalone gate_id field in YAML. If present, reject
        # (forces clean migration — no stale gate_id lingering).
        if "gate_id" in entry:
            raise GateConfigError(
                f"gates.yaml entry {phase_key!r} still carries a standalone "
                f"'gate_id' field — Phase 8 FIX-01 removed it; the gate_id "
                f"is derived from the phase_id key via derive_gate_id()."
            )
        _validate_entry(phase_key, entry)
        if phase_key in registry:
            raise GateConfigError(f"duplicate phase_key in gates.yaml: {phase_key}")
        registry[phase_key] = entry
    return registry


def _validate_phase_key(key: str) -> None:
    """Ensure a gates.yaml top-level key matches the phase_id pattern."""
    if not isinstance(key, str) or not _PHASE_KEY_RE.match(key):
        raise GateConfigError(
            f"gates.yaml key {key!r} does not match phase_id pattern "
            f"(expected p\\d+_<name>[_redline_<sub>], e.g. 'p01_hook_topic')"
        )


def _validate_entry(phase_key: str, entry: Any) -> None:
    """Validate one gate entry in isolation. Raises GateConfigError on failure.

    Args:
        phase_key: The gates.yaml top-level key (for error messages + as
            fallback for the redundant ``phase`` field inside the entry).
        entry: The raw YAML dict for this gate.
    """
    if not isinstance(entry, dict):
        raise GateConfigError(f"gate entry is not a mapping: {entry!r}")

    for field in REQUIRED_FIELDS:
        if field not in entry:
            raise GateConfigError(
                f"gate {phase_key!r} missing required field {field!r}"
            )

    slots = entry["asset_bus_slots_to_lock"]
    if not isinstance(slots, list) or not slots:
        raise GateConfigError(
            f"gate {phase_key!r}: asset_bus_slots_to_lock must be a non-empty list"
        )
    for s in slots:
        if not isinstance(s, str) or not s:
            raise GateConfigError(
                f"gate {phase_key!r}: asset_bus_slots_to_lock entries must be non-empty str"
            )

    rr = entry["reviewer_role"]
    if isinstance(rr, list):
        if not rr or not all(isinstance(x, str) and x for x in rr):
            raise GateConfigError(
                f"gate {phase_key!r}: reviewer_role list must be non-empty list of non-empty str"
            )
    elif not isinstance(rr, str) or not rr:
        raise GateConfigError(
            f"gate {phase_key!r}: reviewer_role must be a non-empty str or list of str"
        )

    timeout_sec = entry["timeout_sec"]
    if not isinstance(timeout_sec, int) or isinstance(timeout_sec, bool) or timeout_sec <= 0:
        raise GateConfigError(
            f"gate {phase_key!r}: timeout_sec must be a positive int (got {timeout_sec!r})"
        )

    mode = entry["default_mode"]
    if mode not in _VALID_MODES:
        raise GateConfigError(
            f"gate {phase_key!r}: default_mode must be one of "
            f"blocking/webhook/polling (got {mode!r})"
        )

    callback_url = entry.get("callback_url")
    if callback_url is not None and not isinstance(callback_url, str):
        raise GateConfigError(
            f"gate {phase_key!r}: callback_url must be str or null"
        )

    rp = entry["retry_policy"]
    if not isinstance(rp, dict):
        raise GateConfigError(
            f"gate {phase_key!r}: retry_policy must be a mapping"
        )
    for sub in ("max_retries", "backoff_sec"):
        v = rp.get(sub)
        if not isinstance(v, int) or isinstance(v, bool) or v <= 0:
            raise GateConfigError(
                f"gate {phase_key!r}: retry_policy.{sub} must be a positive int (got {v!r})"
            )

    # --- blocking_policies (optional — T2 evaluate_gate feature) ---
    bp = entry.get("blocking_policies")
    if bp is not None:
        _validate_blocking_policies(phase_key, bp)


# ---------------------------------------------------------------------------
# T2: blocking_policies validation (evaluate_gate auto-block rules)
# ---------------------------------------------------------------------------

_VALID_RULE_TYPES = frozenset({
    "critical_count", "score_floor", "pass_ratio", "field_present",
    "stigma_unresolved",
})
_VALID_OPERATORS = frozenset({"gt", "gte", "eq", "lt", "lte"})


def _validate_blocking_policies(phase_key: str, bp: Any) -> None:
    """Validate a ``blocking_policies`` block on one gate entry.

    Schema (T2 / evaluate_gate feature):
        blocking_policies:
          auto_evaluate: bool          # required
          rollback_target_default: str # required — phase_id to roll back to
          rules: list[dict]            # required, non-empty; ANY rule fires → block
            - type: critical_count
              field: str               # dotted path into evaluate_gate() data dict
              threshold: int
              operator: gt|gte|eq|lt|lte
            - type: score_floor
              field: str
              min: number
            - type: pass_ratio
              field: str               # numerator
              total_field: str         # denominator
              min_ratio: float         # 0.0–1.0
            - type: field_present
              field: str

    Raises GateConfigError on any validation failure.
    """
    if not isinstance(bp, dict):
        raise GateConfigError(
            f"gate {phase_key!r}: blocking_policies must be a mapping"
        )

    # auto_evaluate
    if "auto_evaluate" not in bp:
        raise GateConfigError(
            f"gate {phase_key!r}: blocking_policies missing required 'auto_evaluate'"
        )
    if not isinstance(bp["auto_evaluate"], bool):
        raise GateConfigError(
            f"gate {phase_key!r}: blocking_policies.auto_evaluate must be bool"
        )

    # rollback_target_default
    if "rollback_target_default" not in bp:
        raise GateConfigError(
            f"gate {phase_key!r}: blocking_policies missing required "
            f"'rollback_target_default'"
        )
    rtd = bp["rollback_target_default"]
    if not isinstance(rtd, str) or not rtd:
        raise GateConfigError(
            f"gate {phase_key!r}: blocking_policies.rollback_target_default "
            f"must be a non-empty str"
        )

    # rules
    rules = bp.get("rules")
    if not isinstance(rules, list) or not rules:
        raise GateConfigError(
            f"gate {phase_key!r}: blocking_policies.rules must be a non-empty list"
        )

    for i, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise GateConfigError(
                f"gate {phase_key!r}: blocking_policies.rules[{i}] must be a mapping"
            )
        rtype = rule.get("type")
        if rtype not in _VALID_RULE_TYPES:
            raise GateConfigError(
                f"gate {phase_key!r}: blocking_policies.rules[{i}].type "
                f"must be one of {sorted(_VALID_RULE_TYPES)} (got {rtype!r})"
            )
        if "field" not in rule or not isinstance(rule["field"], str) or not rule["field"]:
            raise GateConfigError(
                f"gate {phase_key!r}: blocking_policies.rules[{i}] missing "
                f"required non-empty 'field'"
            )

        if rtype == "critical_count":
            if "threshold" not in rule or not isinstance(rule["threshold"], int):
                raise GateConfigError(
                    f"gate {phase_key!r}: blocking_policies.rules[{i}] "
                    f"(critical_count) requires integer 'threshold'"
                )
            op = rule.get("operator", "gt")
            if op not in _VALID_OPERATORS:
                raise GateConfigError(
                    f"gate {phase_key!r}: blocking_policies.rules[{i}] "
                    f"operator must be one of {sorted(_VALID_OPERATORS)} (got {op!r})"
                )

        elif rtype == "score_floor":
            if "min" not in rule or not isinstance(rule["min"], (int, float)):
                raise GateConfigError(
                    f"gate {phase_key!r}: blocking_policies.rules[{i}] "
                    f"(score_floor) requires numeric 'min'"
                )

        elif rtype == "pass_ratio":
            if "total_field" not in rule or not isinstance(rule["total_field"], str) or not rule["total_field"]:
                raise GateConfigError(
                    f"gate {phase_key!r}: blocking_policies.rules[{i}] "
                    f"(pass_ratio) requires non-empty 'total_field'"
                )
            mr = rule.get("min_ratio")
            if mr is None or not isinstance(mr, (int, float)) or not (0.0 <= mr <= 1.0):
                raise GateConfigError(
                    f"gate {phase_key!r}: blocking_policies.rules[{i}] "
                    f"(pass_ratio) requires 'min_ratio' in [0.0, 1.0]"
                )

        elif rtype == "stigma_unresolved":
            # field is required (already validated above).
            # min_severity is optional; if present, must be a valid severity string.
            ms = rule.get("min_severity")
            if ms is not None:
                if not isinstance(ms, str) or ms not in {
                    "info", "warning", "major", "critical",
                }:
                    raise GateConfigError(
                        f"gate {phase_key!r}: blocking_policies.rules[{i}] "
                        f"(stigma_unresolved) min_severity must be one of "
                        f"info/warning/major/critical (got {ms!r})"
                    )

        # field_present: only 'field' is required (already validated above).


# ---------------------------------------------------------------------------
# Phase 8 / 08-01 FIX-01: cross_validate_phase_gates()
# ---------------------------------------------------------------------------


def cross_validate_phase_gates(
    phases_iterable: Iterable[tuple[str, Any]],
    gates_yaml_keys: set[str],
) -> None:
    """Bidirectional SSoT validation between PHASE_REGISTRY and gates.yaml.

    Phase 8 / 08-01 (FIX-01): runs at runner startup to catch any mismatch
    between a phase module's GATE_ID and gates.yaml's keys. Collects ALL
    violations before raising (operator sees the full picture, not fail-
    fast on first).

    Four assertion directions:
        (a) GATE_ID is None → phase MUST NOT appear in gates.yaml.
        (b) GATE_ID is non-None → MUST match derive_gate_id(phase_id).
        (c) GATE_ID is non-None → phase MUST appear in gates.yaml.
        (d) Every gates.yaml key MUST exist in the phase registry.

    Args:
        phases_iterable: Iterable of ``(phase_id, phase_module)`` tuples
            (typically built from PHASE_REGISTRY: ``[(e["id"], e["module"])
            for e in PHASE_REGISTRY]``).
        gates_yaml_keys: Set of phase_id keys from gates.yaml (typically
            ``set(load_gates().keys())``).

    Raises:
        GateConfigError: listing ALL violations if any direction fails.
    """
    # Materialize the iterable so we can iterate it twice (registry lookup
    # for direction d needs the full set of phase_ids).
    phases_list = list(phases_iterable)
    registry_ids = {pid for pid, _ in phases_list}

    errors: list[str] = []
    for phase_id, phase_mod in phases_list:
        gate_id = getattr(phase_mod, "GATE_ID", None)
        if gate_id is None:
            # Direction (a): phase has no gate → must NOT appear in gates.yaml,
            # EXCEPT for evaluate-gate-only phases (v2 consistency layer uses
            # evaluate_gate() inside the phase instead of trigger_gate_blocking).
            if phase_id in gates_yaml_keys and phase_id not in _EVALUATE_GATE_ONLY_PHASES:
                errors.append(
                    f"{phase_id}: GATE_ID is None but gates.yaml has an entry "
                    f"(spurious entry — delete from gates.yaml, or add to "
                    f"_EVALUATE_GATE_ONLY_PHASES if it's a v2 evaluate-gate phase)"
                )
        else:
            # Direction (b): phase has gate → GATE_ID must match derive_gate_id.
            expected = derive_gate_id(phase_id)
            if gate_id != expected:
                errors.append(
                    f"{phase_id}: GATE_ID={gate_id!r} does not match derived {expected!r}"
                )
            # Direction (c): phase has gate → must appear in gates.yaml
            # (either as the main phase_id key OR via a redline sub-key
            # sharing this phase_id — but for non-p13 phases the exact
            # phase_id must be present).
            if phase_id not in gates_yaml_keys:
                # Check if any gates.yaml key has this phase_id as its base
                # (e.g. p13_delivery_redline_emotion has base p13_delivery).
                has_indirect = any(
                    k.split("_redline_")[0] == phase_id if "_redline_" in k
                    else k == phase_id
                    for k in gates_yaml_keys
                )
                if not has_indirect:
                    errors.append(
                        f"{phase_id}: GATE_ID={gate_id!r} but gates.yaml has no "
                        f"entry (missing entry — add to gates.yaml)"
                    )

    # Direction (d): gates.yaml keys must all exist in PHASE_REGISTRY.
    for key in gates_yaml_keys:
        # Strip _redline_* suffix when checking registry membership, since
        # redline sub-keys belong to a base phase that IS in the registry.
        base_key = key.split("_redline_")[0] if "_redline_" in key else key
        if base_key not in registry_ids:
            errors.append(
                f"gates.yaml references unknown phase {key!r} "
                f"(not in PHASE_REGISTRY)"
            )

    if errors:
        raise GateConfigError(
            "gate_id SSoT validation failed with {} error(s):\n  - {}".format(
                len(errors), "\n  - ".join(errors)
            )
        )


# ---------------------------------------------------------------------------
# to_gate_config() — accepts phase_id OR legacy gate_id (Phase 8 / 08-01)
# ---------------------------------------------------------------------------


def to_gate_config(phase_id_or_gate_id: str) -> "GateConfig":
    """Convert a raw YAML entry to a frozen ``GateConfig`` dataclass.

    Phase 8 / 08-01: signature nominally changed from ``gate_id`` to
    ``phase_id`` per plan step 7. For backward compatibility with pre-Phase-8
    callers / tests, this function accepts BOTH forms:

    - phase_id (e.g. "p01_hook_topic"): looked up directly as a gates.yaml
      top-level key.
    - legacy gate_id (e.g. "topic-gate", "p01-gate"): resolved via
      ``gate_id_to_phase_id`` (which checks both the canonical derived
      form and the static _LEGACY_GATE_ID_TO_PHASE_ID map).

    Imports ``plugins.review_gates.gate`` lazily so the YAML loader remains
    usable in Wave 1 parallel execution before Plan 34-01 lands.

    ``reviewer_role`` (which may be a list in the YAML for multi-reviewer
    gates) is normalized to a comma-joined string on the dataclass field.

    The returned ``GateConfig.gate_id`` is populated via
    ``derive_gate_id(phase_id)`` so callers see the canonical derived
    gate_id from the dataclass.

    Args:
        phase_id_or_gate_id: Either a gates.yaml top-level key (phase_id)
            OR a legacy/raw gate_id (resolved via gate_id_to_phase_id).

    Raises:
        GateConfigError: if the input is unknown, or if ``gate.py``
            (Plan 34-01) is not yet importable.
    """
    registry = load_gates()
    phase_id: str
    if phase_id_or_gate_id in registry:
        phase_id = phase_id_or_gate_id
    else:
        # Try resolving as a gate_id (canonical derived or legacy).
        try:
            phase_id = gate_id_to_phase_id(phase_id_or_gate_id)
        except GateConfigError:
            raise GateConfigError(
                f"Unknown phase_id or gate_id: {phase_id_or_gate_id!r}"
            )
    entry = registry[phase_id]

    # Lazy import — see module docstring (Rule 3 deviation).
    try:
        from plugins.review_gates.gate import GateConfig, GateMode
    except ImportError as exc:
        raise GateConfigError(
            "plugins.review_gates.gate is not importable — "
            "Plan 34-01 (gate.py) must land before to_gate_config() can run"
        ) from exc

    # Normalize reviewer_role: list[str] -> ", "-joined str
    rr = entry["reviewer_role"]
    if isinstance(rr, list):
        rr = ", ".join(rr)

    rp = entry["retry_policy"]
    return GateConfig(
        gate_id=derive_gate_id(phase_id),
        phase=entry["phase"],
        asset_bus_slots_to_lock=tuple(entry["asset_bus_slots_to_lock"]),
        reviewer_role=rr,
        timeout_sec=entry["timeout_sec"],
        callback_url=entry.get("callback_url"),
        max_retries=rp["max_retries"],
        backoff_sec=rp["backoff_sec"],
        default_mode=GateMode(entry["default_mode"]),
    )


# Eager load on import — fails loud if YAML is broken (D-34-02).
GATE_REGISTRY: dict[str, dict] = load_gates()
