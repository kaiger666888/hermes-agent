"""Abstract base class for the 5 platform API adapters (DATA-01).

Subclasses set ``name`` + ``env_key`` ClassVars and implement
``fetch(variant_id) -> PlatformMetrics``. The base class enforces
operator-side env-key activation: missing env var →
``AdapterNotActivatedError`` (clean failure for V9-FUTURE-01 deferred
live ingestion).

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 / 585 forward-compat.
  - Double-quoted strings throughout.
  - ``import abc, os`` — no third-party deps (pure stdlib).
  - Lazy import of ``ADAPTER_REGISTRY`` inside ``get_adapter`` body to
    avoid circular import (adapters/__init__.py imports from base.py for
    the ``issubclass`` check in ``register_adapter``).
"""

from __future__ import annotations

import abc
import os
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from plugins.platform_metrics.schema import PlatformMetrics

__all__ = ["BasePlatformAdapter", "AdapterNotActivatedError", "get_adapter"]


# ── Exception ────────────────────────────────────────────────────────────


class AdapterNotActivatedError(RuntimeError):
    """Raised when an adapter ``fetch`` is called without its env key.

    Subclasses inherit from ``RuntimeError`` (NOT the bare ``Exception``
    base) so operators can catch this specific failure mode separately
    from generic adapter exceptions. The env-key name is always included
    in the message so the operator knows exactly which ``~/.hermes/.env``
    var to set.

    Operator-action-handoff: V9-FUTURE-01 live ingestion requires the
    operator to obtain + configure the platform API key first. v9.0 ships
    only the activation scaffold + schema validation.
    """

    def __init__(self, env_key: str, platform: str = "<unknown>") -> None:
        self.env_key = env_key
        self.platform = platform
        super().__init__(
            f"Platform adapter {platform!r} requires env var {env_key} "
            f"(operator-action-handoff: set in ~/.hermes/.env per "
            f"data-convergence.md §Operator Setup)"
        )


# ── ABC ──────────────────────────────────────────────────────────────────


class BasePlatformAdapter(abc.ABC):
    """Abstract base class for all platform API adapters (DATA-01).

    Subclasses MUST override:
      - ``name``: ClassVar[str] — the platform identifier (e.g. ``"douyin"``).
      - ``env_key``: ClassVar[str] — env var name (e.g. ``"DOUYIN_API_KEY"``).
      - ``fetch``: async coroutine returning a ``PlatformMetrics``.

    The base class provides:
      - ``is_activated`` — concrete bool check on env var presence.
      - ``_require_activated`` — raises ``AdapterNotActivatedError`` if
        env var is missing. Subclasses call this at the top of ``fetch``.

    Operator-action-handoff: live HTTP calls are deferred to V9-FUTURE-01.
    Plan 42-02's 5 stubs raise ``NotImplementedError`` on the HTTP path
    (after the env-key check + schema validation passes). v9.0 ships
    activation scaffolding only.
    """

    # ClassVar contracts — subclass overrides.
    name: ClassVar[str] = ""
    env_key: ClassVar[str] = ""

    def __init__(self, *, timeout: float = 30.0) -> None:
        # Keyword-only — forces explicit calls + future-proof against
        # positional-arg drift in subclasses.
        self._timeout = timeout

    # ── Concrete helpers ─────────────────────────────────────────────────

    def is_activated(self) -> bool:
        """Return True iff the env var for this adapter is non-empty.

        Per T-42-01 (Information Disclosure): only the bool result is
        returned — never the env var value. The adapter reads the key
        later (in ``fetch``) for its HTTP path; ``is_activated`` is the
        safe pre-flight check.
        """
        return bool(os.environ.get(self.env_key))

    def _require_activated(self) -> None:
        """Raise ``AdapterNotActivatedError`` if env var is missing.

        Subclasses call this at the top of their ``fetch`` implementation
        so the activation gate fires BEFORE any HTTP call.
        """
        if not self.is_activated():
            raise AdapterNotActivatedError(self.env_key, platform=self.name)

    # ── Abstract API ─────────────────────────────────────────────────────

    @abc.abstractmethod
    async def fetch(self, variant_id: str) -> "PlatformMetrics":
        """Fetch fresh ``PlatformMetrics`` for the given ``variant_id``.

        Async because all 5 platforms are HTTP-based (``httpx.AsyncClient``
        in V9-FUTURE-01). Subclasses MUST call ``self._require_activated()``
        at the top — this gates on the operator-supplied env var.

        Args:
            variant_id: opaque variant identifier from
                ``variants[].source_master_hash`` (Phase 38 SLICE output).
                Treat as untrusted input (T-42-02 Tampering) — never
                interpolate into URLs without ``urllib.parse.quote``.

        Returns:
            ``PlatformMetrics`` Pydantic instance validated against the
            DATA-01 schema.

        Raises:
            AdapterNotActivatedError: env var for this adapter is unset.
            NotImplementedError: V9-FUTURE-01 deferred live HTTP path
                (Plan 42-02 stub behavior).
        """
        raise NotImplementedError


# ── Factory ─────────────────────────────────────────────────────────────


def get_adapter(name: str) -> "BasePlatformAdapter":
    """Instantiate + return the adapter registered under ``name``.

    Lazy import of ``ADAPTER_REGISTRY`` (avoids the circular import —
    ``adapters/__init__.py`` imports ``BasePlatformAdapter`` from this
    module for the ``issubclass`` check in ``register_adapter``).

    Args:
        name: platform identifier (e.g. ``"douyin"``). Must match a key
            in ``ADAPTER_REGISTRY``.

    Returns:
        A fresh instance of the registered adapter subclass.

    Raises:
        KeyError: unknown ``name``. Message lists all registered names
            so the operator sees what's available.
    """
    from plugins.platform_metrics.adapters import ADAPTER_REGISTRY

    if name not in ADAPTER_REGISTRY:
        raise KeyError(
            f"unknown platform adapter: {name!r}; "
            f"registered: {sorted(ADAPTER_REGISTRY)}"
        )
    return ADAPTER_REGISTRY[name]()
