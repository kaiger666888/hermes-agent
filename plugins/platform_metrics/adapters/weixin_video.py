"""WeixinVideoAdapter — 微信视频号 platform adapter stub (DATA-01).

Platform: 微信视频号 / WeChat Channels (channels.weixin.qq.com creator
center).

Auth model: **cookie-based**. As of 2026-06, WeChat Channels does NOT
expose a public OAuth2 API for creator-side analytics. Operators extract
the cookie string from the channels.weixin.qq.com creator center (login
→ DevTools → Application → Cookies) and pass it via ``WEIXIN_VIDEO_API_KEY``.
The cookie authorizes calls to the creator-center JSON endpoints (which
are reverse-engineered from the web UI; not officially documented).

Cookie-rotation caveat: WeChat Channels cookies expire (typically 7-30
days depending on session activity). The V9-FUTURE-01 implementer MUST
add cookie-expiry detection + a clear re-extraction handoff message.

DATA-01 env var: ``WEIXIN_VIDEO_API_KEY``. Format: full cookie string
(e.g. ``"sess_cookie=...; sess_key=..."``); Plan 42-04 documents the
format in ``.env.example``.

API endpoint (documented for V9-FUTURE-01 implementer; v9.0 stub does
NOT call this URL):
  - ``CREATOR_BASE_URL``: creator-center reverse-engineered JSON endpoint.

V9-FUTURE-01 deferral: see ``douyin.py`` docstring — same operator-
action-handoff pattern. Live HTTP path raises ``NotImplementedError``.

Per CLAUDE.md conventions:
  - ``from __future__ import annotations`` before any other import.
  - Double-quoted strings throughout.
  - ``import logging, os`` — pure stdlib.
  - Lazy %-logging; no env var value (cookie) ever logged (T-42-05).
"""

from __future__ import annotations

import logging
import os
from typing import ClassVar

from plugins.platform_metrics.adapters import register_adapter
from plugins.platform_metrics.adapters.base import BasePlatformAdapter
from plugins.platform_metrics.schema import PlatformMetrics

logger = logging.getLogger(__name__)


# V9-FUTURE-01 live target URL (documented only; not called by v9.0 stub).
CREATOR_BASE_URL = "https://channels.weixin.qq.com/cgi-bin/mmcreatorassistant"


class WeixinVideoAdapter(BasePlatformAdapter):
    """Platform adapter for 微信视频号 / WeChat Channels.

    Subclass of ``BasePlatformAdapter`` (Plan 42-01). Activation gate
    is the ``WEIXIN_VIDEO_API_KEY`` env var; live HTTP call is V9-FUTURE-01
    deferred. Cookie-based auth (cookie-rotation caveat documented above).
    """

    name: ClassVar[str] = "weixin_video"
    env_key: ClassVar[str] = "WEIXIN_VIDEO_API_KEY"

    async def fetch(self, variant_id: str) -> PlatformMetrics:
        """Fetch fresh ``PlatformMetrics`` for ``variant_id`` from 视频号.

        V9-FUTURE-01 deferred: this stub raises ``NotImplementedError``
        after the env-key check passes. Cookie-based auth means the
        V9-FUTURE-01 implementer MUST handle cookie-expiry / rotation
        before this can ship live.
        """
        self._require_activated()

        _has_key = bool(os.environ.get(self.env_key))
        logger.debug(
            "WeixinVideoAdapter.fetch activated=%s variant_id=%s",
            _has_key,
            variant_id,
        )

        raise NotImplementedError(
            f"WeixinVideoAdapter live fetch not shipped in v9.0 — "
            f"V9-FUTURE-01 deferred. Adapter activated (env var "
            f"{self.env_key!r} is set, cookie-based auth), but the HTTP "
            f"call to {CREATOR_BASE_URL!r} requires operator-side cookie "
            f"extraction from channels.weixin.qq.com creator center. "
            f"Cookie-expiry detection + re-extraction handoff must be "
            f"implemented. See references/data-convergence.md §Operator Setup."
        )
        # V9-FUTURE-01 live path (pseudo — implementer fills in):
        #   cookie = os.environ.get(self.env_key)
        #   async with httpx.AsyncClient(timeout=self._timeout) as client:
        #       resp = await client.get(
        #           f"{CREATOR_BASE_URL}/cgi-bin/assistant/GetVideoAnalysis",
        #           params={"video_id": variant_id},
        #           headers={"Cookie": cookie},
        #       )
        #       resp.raise_for_status()
        #       raw = resp.json()["data"]
        #       return PlatformMetrics(
        #           platform="weixin_video",
        #           variant_id=variant_id,
        #           completion_rate=...,
        #           hook_dropoff_rate=...,
        #           engagement_rate=...,
        #           save_rate=...,
        #           comment_rate=...,
        #           fetched_at=datetime.now(timezone.utc),
        #       )


# Self-registration (mirror tools/registry.py pattern).
register_adapter("weixin_video", WeixinVideoAdapter)
