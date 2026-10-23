"""qwen_ear.py — DEPRECATED 兼容 shim → kais_ear (2026-09-27 更名批).

Kai 0927 架构令: qwen-ear 更名 kais-ear (统一语音引擎, 双后端:
hybrid-asr :8012 转写 + Omni :8126 听审)。实现真源已全部迁
``plugins/kais_aigc/kais_ear.py``; 本文件仅为消费方零破坏保留
(ENGINE_NAME 已随真源变为 "kais-ear")。

新代码一律 ``from plugins.kais_aigc.kais_ear import KaisEar``;
消费面清零后本 shim 由后续批移除。禁在本文件加任何实现。
"""

from plugins.kais_aigc.kais_ear import *  # noqa: F401,F403
from plugins.kais_aigc.kais_ear import (  # noqa: F401 — 显式重导出
    ENGINE_NAME,
    HYBRID_SCRIPT_TIMEOUT_S,
    HYBRID_TRANSCRIBE_API,
    HYBRID_TRANSCRIBE_TIMEOUT_S,
    HYBRID_HEALTH_URL,
    KAP_ALLOCATE_URL,
    KAP_EAR_SH,
    KAP_HYBRID_SH,
    KAP_HYBRID_STATUS_URL,
    KAP_HYBRID_TRANSCRIBE_URL,
    KAP_RELEASE_URL,
    EAR_API,
    EAR_CALL_TIMEOUT_S,
    EAR_HEALTH,
    EAR_START_TIMEOUT_S,
    SERVER_LOG,
    KaisEar,
    QwenEar,
)
