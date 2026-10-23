"""BilibiliCreatorAdapter — 哔哩哔哩创作者 platform adapter stub (DATA-01).

Platform: 哔哩哔哩创作者中心 / Bilibili Creator Center
(member.bilibili.com/x2/creative/h5-author).

Auth model: OAuth2. Bilibili exposes a documented OAuth2 flow for
creator-side analytics (member.bilibili.com platform). Operator registers
an app, obtains ``app_id`` + ``app_secret``, exchanges for an
``access_token`` via the OAuth2 endpoint, then calls the video-analysis
endpoint. The Bilibili open API exposes per-video play-count, like /
share / coin / favorite counts, and average-watch-duration buckets.

DATA-01 env var: ``BILIBILI_API_KEY``. Format: app_id:app_secret or a
pre-issued access_token; Plan 42-04 documents the format in
``.env.example``.

API endpoints (documented for V9-FUTURE-01 implementer; v9.0 stub does
NOT call these URLs):
  - ``OAUTH_TOKEN_URL``: OAuth2 client-token exchange.
  - ``VIDEO_ANALYSIS_URL``: Per-video play / engagement metrics.

V9-FUTURE-01 deferral: see ``douyin.py`` docstring — same operator-
action-handoff pattern. Live HTTP path raises ``NotImplementedError``.

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` before any other import.
  - Double-quoted strings throughout.
  - ``import logging, os`` — pure stdlib.
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
OAUTH_TOKEN_URL = "https://api.bilibili.com/x/account-oauth-client/v2/token"
VIDEO_ANALYSIS_URL = "https://member.bilibili.com/x2/creative/h5-author/data/video"


class BilibiliCreatorAdapter(BasePlatformAdapter):
    """Platform adapter for 哔哩哔哩创作者中心 / Bilibili Creator Center.

    Subclass of ``BasePlatformAdapter`` (Plan 42-01). Activation gate
    is the ``BILIBILI_API_KEY`` env var; live HTTP call is V9-FUTURE-01
    deferred.
    """

    name: ClassVar[str] = "bilibili"
    env_key: ClassVar[str] = "BILIBILI_API_KEY"

    async def fetch(self, variant_id: str) -> PlatformMetrics:
        """Fetch fresh ``PlatformMetrics`` for ``variant_id`` from Bilibili.

        V9-FUTURE-01 deferred: this stub raises ``NotImplementedError``
        after the env-key check passes.
        """
        self._require_activated()

        _has_key = bool(os.environ.get(self.env_key))
        logger.debug(
            "BilibiliCreatorAdapter.fetch activated=%s variant_id=%s",
            _has_key,
            variant_id,
        )

        raise NotImplementedError(
            f"BilibiliCreatorAdapter live fetch not shipped in v9.0 — "
            f"V9-FUTURE-01 deferred. Adapter activated (env var "
            f"{self.env_key!r} is set), but the HTTP call to "
            f"{OAUTH_TOKEN_URL!r} + {VIDEO_ANALYSIS_URL!r} requires "
            f"operator-side platform API access (app_id + app_secret from "
            f"member.bilibili.com). See references/data-convergence.md "
            f"§Operator Setup."
        )
        # V9-FUTURE-01 live path (pseudo — implementer fills in):
        #   async with httpx.AsyncClient(timeout=self._timeout) as client:
        #       token_resp = await client.post(
        #           OAUTH_TOKEN_URL,
        #           json={
        #               "client_id": app_id,
        #               "client_secret": app_secret,
        #               "grant_type": "client_credentials",
        #           },
        #       )
        #       token_resp.raise_for_status()
        #       access_token = token_resp.json()["access_token"]
        #       data_resp = await client.get(
        #           VIDEO_ANALYSIS_URL,
        #           params={"aid": variant_id, "access_token": access_token},
        #       )
        #       data_resp.raise_for_status()
        #       raw = data_resp.json()["data"]
        #       return PlatformMetrics(
        #           platform="bilibili",
        #           variant_id=variant_id,
        #           completion_rate=...,
        #           hook_dropoff_rate=...,
        #           engagement_rate=...,
        #           save_rate=...,
        #           comment_rate=...,
        #           fetched_at=datetime.now(timezone.utc),
        #       )


# Self-registration (mirror tools/registry.py pattern).
register_adapter("bilibili", BilibiliCreatorAdapter)
