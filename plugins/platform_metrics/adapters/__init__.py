"""Adapter registry + registration helper (Plan 42-01 Task 1).

Self-registration pattern (mirror ``tools/registry.py``): each adapter
module under this package calls ``register_adapter(name, cls)`` at
module import time. ``ADAPTER_REGISTRY`` is populated lazily — Plan 01
ships an empty registry; Plan 42-02's 5 adapter stubs populate it.

Per CLAUDE.md: ``from __future__ import annotations``, double-quoted
strings, lazy import of ``BasePlatformAdapter`` inside
``register_adapter`` body to avoid circular import (base.py is in this
same package; importing it at module top would be fine but lazy import
keeps the contract explicit and forward-compatible).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plugins.platform_metrics.adapters.base import BasePlatformAdapter

__all__ = ["ADAPTER_REGISTRY", "register_adapter"]


# Module-level registry. Keys are platform name strings (e.g. ``"douyin"``);
# values are the adapter subclass (NOT an instance). ``get_adapter`` in
# ``base.py`` instantiates lazily on lookup.
ADAPTER_REGISTRY: "dict[str, type[BasePlatformAdapter]]" = {}


def register_adapter(name: str, cls: "type[BasePlatformAdapter]") -> None:
    """Register an adapter subclass under ``name``.

    Contract: ``cls`` MUST inherit from ``BasePlatformAdapter``. A
    ``TypeError`` is raised on non-subclasses — this catches typos like
    registering a schema class instead of an adapter.

    Args:
        name: platform identifier (e.g. ``"douyin"``). Must match the
            ``name`` ClassVar on ``cls`` — but this is NOT enforced here
            (defensive: caller is responsible; mismatch surfaces as a
            KeyError in ``get_adapter`` lookup later).
        cls: the adapter subclass to register.

    Raises:
        TypeError: ``cls`` does not inherit ``BasePlatformAdapter``.
    """
    # Lazy import — avoids circular import at module load time.
    from plugins.platform_metrics.adapters.base import BasePlatformAdapter

    if not issubclass(cls, BasePlatformAdapter):
        raise TypeError(
            f"register_adapter({name!r}, {cls!r}): cls must inherit from "
            f"BasePlatformAdapter; got {cls.__mro__!r}"
        )
    ADAPTER_REGISTRY[name] = cls
