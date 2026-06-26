"""KuaishouOpenAdapter — 快手开放平台 platform adapter stub (DATA-01).

Platform: 快手开放平台 / Kuaishou Open Platform (open.kuaishou.com).

Auth model: OAuth2 ``access_token`` flow. Operator registers an app at
open.kuaishou.com, obtains ``app_id`` + ``app_secret``, generates an
``access_token`` via the OAuth2 endpoint, then calls the video-data
endpoint. The Kuaishou open API exposes per-video play-count, like /
comment / share counts, and average-watch-duration buckets.

DATA-01 env var: ``KUAISHOU_API_KEY``. Operator-side credential reference
(app_id:app_secret or pre-issued access_token); format documented in
Plan 42-04 ``.env.example``.

API endpoints (documented for V9-FUTURE-01 implementer; v9.0 stub does
NOT call these URLs):
  - ``OAUTH_TOKEN_URL``: OAuth2 access_token exchange.
  - ``VIDEO_DATA_URL``: Per-video play / engagement metrics.

V9-FUTURE-01 deferral: see ``douyin.py`` docstring — same operator-
action-handoff pattern. Live HTTP path raises ``NotImplementedError``.

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` before any other import.
  - Double-quoted strings throughout.
  - ``import logging, os`` — pure stdlib.
  - Lazy %-logging; no env var value logged (T-42-05).
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
OAUTH_TOKEN_URL = "https://open.kuaishou.com/oauth2/access_token"
VIDEO_DATA_URL = "https://open.kuaishou.com/openapi/video_data/get"


class KuaishouOpenAdapter(BasePlatformAdapter):
    """Platform adapter for 快手开放平台 / Kuaishou Open Platform.

    Subclass of ``BasePlatformAdapter`` (Plan 42-01). Activation gate
    is the ``KUAISHOU_API_KEY`` env var; live HTTP call is V9-FUTURE-01
    deferred.
    """

    name: ClassVar[str] = "kuaishou"
    env_key: ClassVar[str] = "KUAISHOU_API_KEY"

    async def fetch(self, variant_id: str) -> PlatformMetrics:
        """Fetch fresh ``PlatformMetrics`` for ``variant_id`` from Kuaishou.

        V9-FUTURE-01 deferred: this stub raises ``NotImplementedError``
        after the env-key check passes.
        """
        self._require_activated()

        _has_key = bool(os.environ.get(self.env_key))
        logger.debug(
            "KuaishouOpenAdapter.fetch activated=%s variant_id=%s",
            _has_key,
            variant_id,
        )

        raise NotImplementedError(
            f"KuaishouOpenAdapter live fetch not shipped in v9.0 — "
            f"V9-FUTURE-01 deferred. Adapter activated (env var "
            f"{self.env_key!r} is set), but the HTTP call to "
            f"{OAUTH_TOKEN_URL!r} + {VIDEO_DATA_URL!r} requires "
            f"operator-side platform API access (app_id + access_token "
            f"from open.kuaishou.com). See references/data-convergence.md "
            f"§Operator Setup."
        )
        # V9-FUTURE-01 live path (pseudo — implementer fills in):
        #   async with httpx.AsyncClient(timeout=self._timeout) as client:
        #       token_resp = await client.post(
        #           OAUTH_TOKEN_URL,
        #           json={
        #               "app_id": app_id,
        #               "app_secret": app_secret,
        #               "grant_type": "client_credential",
        #           },
        #       )
        #       token_resp.raise_for_status()
        #       access_token = token_resp.json()["access_token"]
        #       data_resp = await client.get(
        #           VIDEO_DATA_URL,
        #           params={"video_id": variant_id, "access_token": access_token},
        #       )
        #       data_resp.raise_for_status()
        #       raw = data_resp.json()
        #       return PlatformMetrics(
        #           platform="kuaishou",
        #           variant_id=variant_id,
        #           completion_rate=...,
        #           hook_dropoff_rate=...,
        #           engagement_rate=...,
        #           save_rate=...,
        #           comment_rate=...,
        #           fetched_at=datetime.now(timezone.utc),
        #       )


# Self-registration (mirror tools/registry.py pattern).
register_adapter("kuaishou", KuaishouOpenAdapter)
