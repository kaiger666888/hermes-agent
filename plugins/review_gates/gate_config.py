"""gate_config.py — gates.yaml loader + validator (Phase 34-02, SC#2).

Loads ``gates.yaml`` once at import time. Exposes:

- ``GATE_REGISTRY: dict[str, dict]`` — raw YAML entries keyed by gate_id.
- ``load_gates() -> dict[str, dict]`` — re-reads + validates; idempotent.
- ``to_gate_config(gate_id) -> GateConfig`` — converts a raw entry into the
  frozen ``GateConfig`` dataclass defined by Plan 34-01 (``gate.py``).
- ``GateConfigError`` — raised on missing file, malformed YAML, or failed
  validation.

Phase 40 Plan 02 (GATE-04) expanded the registry 8 -> 11 additive: the 8
V8.6 gates are byte-preserved, and 3 Phase 40 redline gates (R1/R3/R4)
are appended. The count check enforces exactly 11. See
``.planning/phases/40-gate-redlines/40-02-PLAN.md`` Task 2.

Architectural decisions (CONTEXT.md):
- D-34-02: YAML is loaded eagerly at import. Hot-reload is NOT supported;
  changing a gate definition requires restarting the hermes-agent process.
- D-34-03: ``pyyaml`` is the ONE third-party dep added in Phase 34. It is
  already a transitive dep of hermes-agent (the plugin loader uses it for
  ``plugin.yaml`` parsing), so no ``pyproject.toml`` change is needed.
- D-34-04: ``GateConfig`` (from YAML) is ``@dataclass(frozen=True)`` for
  hashability + immutability. Runtime ``Gate`` instances are mutable.

Deviation note (Rule 3 — blocking issue):
The plan's reference listing performs ``from plugins.review_gates.gate import
GateConfig, GateMode`` at module top. In Wave 1 parallel execution, Plan 34-01
(which owns ``gate.py``) may not yet have landed. A top-level import would
``ImportError`` the entire module, breaking the YAML loader and validation
tests that do NOT depend on ``GateConfig``. The import is therefore deferred
to inside ``to_gate_config()``, preserving the plan's API contract while
allowing ``load_gates()`` to work standalone. Once 34-01 lands, behavior is
identical to the plan's reference listing.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml  # pyyaml — already transitive dep (plugin loader uses it for plugin.yaml)

if TYPE_CHECKING:  # pragma: no cover — typing only, no runtime import
    from plugins.review_gates.gate import GateConfig

logger = logging.getLogger(__name__)


class GateConfigError(Exception):
    """Raised when gates.yaml is missing, malformed, or fails validation."""


_YAML_PATH: Path = Path(__file__).parent / "gates.yaml"


# Required fields on every gate entry (per ROADMAP SC#2 + CF-02).
# NOTE: ``callback_url`` is intentionally OPTIONAL — webhook-mode gates wire
# it at runtime (runner_hooks, Phase 34-03); blocking/polling gates leave null.
REQUIRED_FIELDS: tuple[str, ...] = (
    "gate_id",
    "phase",
    "asset_bus_slots_to_lock",
    "reviewer_role",
    "timeout_sec",
    "default_mode",
    "retry_policy",
)

_VALID_MODES = frozenset({"blocking", "webhook", "polling"})


def load_gates() -> dict[str, dict]:
    """Load and validate ``gates.yaml``.

    Returns a fresh ``{gate_id: raw_yaml_dict}`` mapping on every call
    (idempotent — re-reads the file; no caching at this layer).

    Raises:
        GateConfigError: if the file is missing, the YAML is unparseable,
            the top-level shape is wrong, the gate count is not exactly 11
            (Phase 40 Plan 02 GATE-04 bumped 8 -> 11 additive), or any
            entry fails field-level validation.
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
        raise GateConfigError("gates.yaml missing top-level 'gates' list")
    gate_list = doc["gates"]
    if not isinstance(gate_list, list):
        raise GateConfigError(
            f"gates.yaml 'gates' must be a list, got {type(gate_list).__name__}"
        )
    if len(gate_list) != 11:
        # Phase 40 Plan 02 (GATE-04): bumped 8 -> 11 additive. The 8 V8.6
        # gates are byte-preserved; 3 Phase 40 redline gates (R1/R3/R4)
        # appended. See ``.planning/phases/40-gate-redlines/40-02-PLAN.md``.
        raise GateConfigError(
            f"gates.yaml must contain exactly 11 gates (found {len(gate_list)})"
        )

    registry: dict[str, dict] = {}
    for entry in gate_list:
        _validate_entry(entry)
        gate_id = entry["gate_id"]
        if gate_id in registry:
            raise GateConfigError(f"duplicate gate_id in gates.yaml: {gate_id}")
        registry[gate_id] = entry
    return registry


def _validate_entry(entry: Any) -> None:
    """Validate one gate entry in isolation. Raises GateConfigError on failure."""
    if not isinstance(entry, dict):
        raise GateConfigError(f"gate entry is not a mapping: {entry!r}")

    gate_id = entry.get("gate_id", "<unknown>")
    for field in REQUIRED_FIELDS:
        if field not in entry:
            raise GateConfigError(
                f"gate '{gate_id}' missing required field '{field}'"
            )

    slots = entry["asset_bus_slots_to_lock"]
    if not isinstance(slots, list) or not slots:
        raise GateConfigError(
            f"gate '{gate_id}': asset_bus_slots_to_lock must be a non-empty list"
        )
    for s in slots:
        if not isinstance(s, str) or not s:
            raise GateConfigError(
                f"gate '{gate_id}': asset_bus_slots_to_lock entries must be non-empty str"
            )

    rr = entry["reviewer_role"]
    if isinstance(rr, list):
        if not rr or not all(isinstance(x, str) and x for x in rr):
            raise GateConfigError(
                f"gate '{gate_id}': reviewer_role list must be non-empty list of non-empty str"
            )
    elif not isinstance(rr, str) or not rr:
        raise GateConfigError(
            f"gate '{gate_id}': reviewer_role must be a non-empty str or list of str"
        )

    timeout_sec = entry["timeout_sec"]
    if not isinstance(timeout_sec, int) or isinstance(timeout_sec, bool) or timeout_sec <= 0:
        raise GateConfigError(
            f"gate '{gate_id}': timeout_sec must be a positive int (got {timeout_sec!r})"
        )

    mode = entry["default_mode"]
    if mode not in _VALID_MODES:
        raise GateConfigError(
            f"gate '{gate_id}': default_mode must be one of "
            f"blocking/webhook/polling (got {mode!r})"
        )

    callback_url = entry.get("callback_url")
    if callback_url is not None and not isinstance(callback_url, str):
        raise GateConfigError(
            f"gate '{gate_id}': callback_url must be str or null"
        )

    rp = entry["retry_policy"]
    if not isinstance(rp, dict):
        raise GateConfigError(
            f"gate '{gate_id}': retry_policy must be a mapping"
        )
    for sub in ("max_retries", "backoff_sec"):
        v = rp.get(sub)
        if not isinstance(v, int) or isinstance(v, bool) or v <= 0:
            raise GateConfigError(
                f"gate '{gate_id}': retry_policy.{sub} must be a positive int (got {v!r})"
            )


def to_gate_config(gate_id: str) -> "GateConfig":
    """Convert a raw YAML entry to a frozen ``GateConfig`` dataclass.

    Imports ``plugins.review_gates.gate`` lazily so the YAML loader remains
    usable in Wave 1 parallel execution before Plan 34-01 lands.

    ``reviewer_role`` (which may be a list in the YAML for multi-reviewer
    gates) is normalized to a comma-joined string on the dataclass field.

    Raises:
        GateConfigError: if ``gate_id`` is unknown, or if ``gate.py`` (Plan
            34-01) is not yet importable.
    """
    registry = load_gates()
    if gate_id not in registry:
        raise GateConfigError(f"Unknown gate_id: {gate_id}")
    entry = registry[gate_id]

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
        gate_id=entry["gate_id"],
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
