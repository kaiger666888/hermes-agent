"""DouyinOpenAdapter — 抖音开放平台 platform adapter stub (DATA-01).

Platform: 抖音开放平台 / Douyin Open Platform (open.douyin.com).

Auth model: OAuth2 ``client_credentials`` flow for server-to-server calls.
The operator registers an app at open.douyin.com, obtains ``app_id`` +
``app_secret``, exchanges for an ``access_token`` via the OAuth2 endpoint,
then calls the video-data endpoint. As of 2026-06 the open platform
exposes per-video completion-rate, like/comment/share counts, and watch
time buckets for apps that pass scope review.

DATA-01 env var: ``DOUYIN_API_KEY``. The operator sets this to a stable
credential reference (app_id:app_secret or a pre-issued access_token);
Plan 42-04 documents the format in ``.env.example``. The v9.0 stub only
checks the env var is non-empty — actual credential parsing is V9-FUTURE-01.

API endpoints (documented for the V9-FUTURE-01 implementer; v9.0 stub
does NOT call these URLs):
  - ``OAUTH_TOKEN_URL``: OAuth2 client-token exchange.
  - ``VIDEO_DATA_URL``: Per-video completion / engagement metrics.

V9-FUTURE-01 deferral: this stub ships the env-key activation gate +
schema validation contract only. The live HTTP path raises
``NotImplementedError`` so the operator sees a clear handoff message
when activating without the live wiring. See
``references/data-convergence.md`` §Operator Setup (Plan 42-04).

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` before any other import.
  - Double-quoted strings throughout.
  - ``import logging, os`` — no third-party deps (pure stdlib; ``httpx``
    is referenced only in the V9-FUTURE-01 comment block).
  - Lazy %-logging; no env var value ever logged (T-42-05).
"""

from __future__ import annotations

import logging
import os
from typing import ClassVar

from plugins.platform_metrics.adapters import register_adapter
from plugins.platform_metrics.adapters.base import BasePlatformAdapter
from plugins.platform_metrics.schema import PlatformMetrics

logger = logging.getLogger(__name__)


# V9-FUTURE-01 live target URLs (documented only; not called by v9.0 stub).
OAUTH_TOKEN_URL = "https://open.douyin.com/oauth/client_token/"
VIDEO_DATA_URL = "https://open.douyin.com/data/external/item/video/"


class DouyinOpenAdapter(BasePlatformAdapter):
    """Platform adapter for 抖音开放平台 / Douyin Open Platform.

    Subclass of ``BasePlatformAdapter`` (Plan 42-01). Activation gate
    is the ``DOUYIN_API_KEY`` env var; live HTTP call is V9-FUTURE-01
    deferred.
    """

    name: ClassVar[str] = "douyin"
    env_key: ClassVar[str] = "DOUYIN_API_KEY"

    async def fetch(self, variant_id: str) -> PlatformMetrics:
        """Fetch fresh ``PlatformMetrics`` for ``variant_id`` from Douyin.

        V9-FUTURE-01 deferred: this stub raises ``NotImplementedError``
        after the env-key check passes. The HTTP path + response schema
        validation ships in V9-FUTURE-01.
        """
        # Activation gate — raises AdapterNotActivatedError if env var missing.
        self._require_activated()

        # Operator-action-handoff: live HTTP call requires platform-side
        # app approval (app_id + app_secret + scope review). Read the env
        # key presence for log context (DO NOT log the value — T-42-05).
        _has_key = bool(os.environ.get(self.env_key))
        logger.debug(
            "DouyinOpenAdapter.fetch activated=%s variant_id=%s",
            _has_key,
            variant_id,
        )

        raise NotImplementedError(
            f"DouyinOpenAdapter live fetch not shipped in v9.0 — "
            f"V9-FUTURE-01 deferred. Adapter activated (env var "
            f"{self.env_key!r} is set), but the HTTP call to "
            f"{OAUTH_TOKEN_URL!r} + {VIDEO_DATA_URL!r} requires "
            f"operator-side platform API access (app_id + app_secret + "
            f"approved scope). See references/data-convergence.md "
            f"§Operator Setup."
        )
        # V9-FUTURE-01 live path (pseudo — implementer fills in):
        #   async with httpx.AsyncClient(timeout=self._timeout) as client:
        #       token_resp = await client.post(
        #           OAUTH_TOKEN_URL,
        #           json={
        #               "client_key": app_id,
        #               "client_secret": app_secret,
        #               "grant_type": "client_credential",
        #           },
        #       )
        #       token_resp.raise_for_status()
        #       access_token = token_resp.json()["data"]["access_token"]
        #       data_resp = await client.get(
        #           VIDEO_DATA_URL,
        #           params={"item_id": variant_id, "access_token": access_token},
        #       )
        #       data_resp.raise_for_status()
        #       raw = data_resp.json()["data"]
        #       return PlatformMetrics(
        #           platform="douyin",
        #           variant_id=variant_id,
        #           completion_rate=...,
        #           hook_dropoff_rate=...,
        #           engagement_rate=...,
        #           save_rate=...,
        #           comment_rate=...,
        #           fetched_at=datetime.now(timezone.utc),
        #       )


# Self-registration (mirror tools/registry.py pattern).
register_adapter("douyin", DouyinOpenAdapter)
