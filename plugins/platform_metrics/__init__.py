"""platform_metrics plugin — Phase 42 DATA scaffold (Plan 01).

Phase 42 DATA — Option A new plugin (scope discipline: no Hermes core
edits).

  - Plan 01 ships scaffold + schemas + adapter base.
  - Plan 02 fills 5 adapter stubs (douyin / kuaishou / weixin_video /
    xiaohongshu / bilibili).
  - Plan 03 ships ``tuning_loop.py`` + ``library_writer.py``
    (DATA-03 formula-tuning suggestion engine).
  - Plan 04 ships ``cli.py`` (``hermes formula stats`` subcommand) +
    ``references/data-convergence.md`` + ``SKILL.md`` Step 15 body patch.

Plan 01 ``register(ctx)`` is a no-op — ``provides_tools: []`` in
plugin.yaml. Plan 04 adds ``ctx.register_cli_command(name="formula",
...)`` here.

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` for PEP 604 / 585 forward-compat.
  - Double-quoted strings throughout.
  - ``logger = logging.getLogger(__name__)`` defensive (unused in Plan 01).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

__all__ = ["register"]


def register(ctx) -> None:
    """Register platform_metrics plugin hooks.

    Called once by the hermes-agent plugin loader when
    ``platform_metrics`` appears in ``plugins.enabled`` (kind: standalone
    — opt-in per plugin.yaml manifest).

    Plan 01: shipped scaffold + schemas + adapter base (DATA-01/02).
    Plan 02: shipped 5 adapter stubs (DATA-01).
    Plan 03: ships tuning_loop + library_writer (DATA-03).
    Plan 04 (THIS PLAN): registers the ``hermes formula stats`` CLI
    subcommand via the plugin CLI hook
    (``ctx.register_cli_command``). Auto-discovered at
    ``hermes_cli/main.py:11942``. Zero edits to ``hermes_cli/main.py``.
    """
    # Defensive log — if a misconfigured host loads this plugin without
    # enabling it, the operator sees a trace.
    logger.debug("platform_metrics.register(ctx) called (Plan 04 CLI hook)")

    # Register the CLI subcommand. Auto-discovered at
    # hermes_cli/main.py:11942 via PluginManager._cli_commands.
    from plugins.platform_metrics.cli import (
        _formula_command,
        register_formula_cli,
    )

    ctx.register_cli_command(
        name="formula",
        help="Formula library + platform metrics observability (stats)",
        setup_fn=register_formula_cli,
        handler_fn=_formula_command,
        description=(
            "Inspect formula_library contents + platform-metrics tuning "
            "queue. Subcommand: stats — show per-formula / per-platform "
            "metrics + tuning suggestion queue depth. --json emits "
            "counts-only JSON for scripting."
        ),
    )
