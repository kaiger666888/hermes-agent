---
status: resolved
trigger: "把 openclaw extensions/telegram/src/draft-stream.ts 的 flood 挂起-恢复机制移植到 hermes-agent gateway/stream_consumer.py + gateway/platforms/telegram.py"
slug: telegram-flood-suspend
created: 2026-06-26
updated: 2026-06-26
goal: find_and_fix
specialist_dispatch_enabled: true
---

# Debug Session: telegram-flood-suspend

## Symptoms (pre-filled by orchestrator)

**Expected behavior:**
Telegram 流式 edit 触发 flood control 后，应进入"挂起-恢复"模式 —— 解析 Telegram 返回的 `retry_after`（秒），在 retry_after 期间停止发任何 API 调用，只更新内存中的 _pending_text；retry_after 过后单次 edit 把最新文本推过去，几乎必成功。参照 openclaw `extensions/telegram/src/draft-stream.ts:339-341, 449-452`。

**Actual behavior:**
hermes 流式 edit 触发 flood 后，仍按 `edit_interval=0.8s` 节流持续尝试 edit，每次都被 Telegram 打回（"Retry in N seconds"），把 30s flood 窗口越拖越长。模型生成完成后最终 `sendRichMessage` 也被同一 flood 窗口拒收，gateway 5 次重试（base.py 2 次 + telegram.py 3 次）总共 ~9 秒，远不够 30s 窗口，全部失败。最终走兜底 "Message delivery failed after multiple attempts"，整条响应丢失。

**Error messages (日志证据, ~/.hermes/logs/gateway.log 2026-06-26):**
```
12:53:58  inbound: platform=telegram user=Kai chat=-1004378251055 msg='我们现在新的skills的状态是什么 在吗？'
12:54:34  WARNING telegram: rich editMessageText transient failure (no legacy resend): Flood control exceeded. Retry in 35 seconds
12:54:35  WARNING telegram: sendRichMessage transient failure (no legacy resend): Flood control exceeded. Retry in 34 seconds
12:54:35  WARNING base: [Telegram] Send failed (attempt 1/2, retrying in 2.9s): Flood control exceeded. Retry in 34 seconds
12:54:39  WARNING base: [Telegram] Send failed (attempt 2/2, retrying in 4.8s): Flood control exceeded. Retry in 31 seconds
12:54:44  ERROR   base: [Telegram] Failed to deliver response after 2 retries: Flood control exceeded. Retry in 26 seconds
12:54:44  WARNING telegram: Telegram flood control on send (attempt 1/3), retrying in 25.0s
```
Telegram Web 端显示的 "This message is currently not supported on Telegram Web" 是最后那次 `editMessageText` 留下的半编辑残骸（含未闭合 markdown 实体 + 残留 `┊` 进度字符），Telegram Desktop 勉强能渲染，Web 端直接报这个错。

**Timeline:**
- 上游问题：`gateway/stream_consumer.py` + `gateway/platforms/telegram.py` 是 NousResearch/hermes-agent 上游代码，Kai 本地 533 commits 一个都没碰过这两个文件（`git log origin/main..HEAD -- gateway/stream_consumer.py gateway/platforms/telegram.py` 为空）
- Kai 配置：`~/.hermes/config.yaml` 顶层 `streaming.enabled: false`，但 `platforms.telegram.streaming: true` 覆盖了全局，导致 Telegram 流式实际开启
- 触发场景：任何生成时间 >2-3 秒的响应都会触发；长响应（>30s 生成）必触发

**Reproduction:**
1. 在 Telegram 给 hermes-agent bot 发送任意会触发长响应的消息（例如"列出所有 skills 的状态"）
2. 等待模型流式输出 ~30 秒
3. 观察日志：先出现 `editMessageText transient failure: Flood control`，之后 `sendRichMessage transient failure`
4. Telegram 客户端：先看到半编辑残骸消息（Web 端报 "not supported"），后看到 "Message delivery failed after multiple attempts" 兜底提示

## Root Cause Hypothesis (pre-diagnosed by orchestrator)

hermes 的 `gateway/stream_consumer.py:166` 用 `_flood_strikes` 计数 + dropedit 策略，flood 期间仍按 0.8s 节流持续尝试 edit；缺 openclaw 那套：
1. **`suspended_until` 时间戳**（openclaw `draft-stream.ts:339-341`）—— flood 期间绝对静默，0 次 API 调用
2. **`retry_after` 解析**（openclaw `draft-stream.ts:449`）—— 用 Telegram 给的精确等待时间，封顶 60s
3. **pending 文本保留**（openclaw `draft-stream.ts:340` 注释明确）—— 恢复时发最新而非最旧文本

致命点：Telegram flood control 是滑动惩罚窗口 —— 持续打 API 会让窗口越拖越长。hermes 的"drop+retry"策略反而激怒 Telegram，把简单 flood 拖成 30s 灾难。

## Current Focus

**Hypothesis:** 在 `gateway/stream_consumer.py` 增加 `_suspended_until_monotonic` 状态字段 + `_extract_retry_after(result)` 方法，flood 期间早退不发 API；同时让 `gateway/platforms/telegram.py:1311-1319` 的 rich editMessageText 错误路径透传 retry_after（从异常的 `retry_after` 属性解析）。保留现有 `_flood_strikes` 作为挂起失败后的兜底链。

**Test:** 新增单元测试 `tests/gateway/test_stream_consumer.py`（或扩展已存在的），mock adapter 返回带 "Flood control exceeded. Retry in 30 seconds" 的 SendResult，断言：
- 检测到 flood 后 `_suspended_until_monotonic` 被设置为 `now + 30s`
- 挂起期间对 `adapter.send`/`adapter.edit` 的调用次数 = 0
- 挂起期过后下一次 on_delta 触发单次 edit，发最新累积文本

**Expecting:** 流式期间触发 flood 后，日志只出现 1 次 "flood detected, suspending for Ns"，之后 N 秒内零 API 调用，N 秒过后单次 edit 成功，整条响应完整送达。最终 `sendRichMessage` 因 chat 已脱离 flood 窗口而正常发送。

**Next action:** gather initial evidence —— 读完整 `gateway/stream_consumer.py` 找到所有 `_flood_strikes` 使用点和 send/edit 调用点；确认 `_extract_retry_after` 应该解析的位置（SendResult.error 字符串 `r"Retry in (\d+) seconds"` 正则）；确认 `_pending_text` 是否已有现成字段（`_accumulated`）。

## Evidence

- timestamp: 2026-06-26T13:00 — Read openclaw `extensions/telegram/src/draft-stream.ts:339-452` confirming the three-mechanism design (suspendedUntilMs timestamp, retry_after parsing, pending text preservation). `MAX_PREVIEW_FLOOD_SUSPEND_MS = 60_000` is the cap constant.
- timestamp: 2026-06-26T13:05 — Mapped all `_flood_strikes` usage sites in `gateway/stream_consumer.py`: declaration at line 166, reset on success at 1468, increment + backoff at 1520-1537. The current code uses adaptive backoff (doubling `edit_interval` up to 10s) but NEVER stops calling the API for a parseable `retry_after` window — that's the bug.
- timestamp: 2026-06-26T13:08 — Confirmed `SendResult.raw_response` is the correct channel for adapter-to-consumer metadata (existing contract: Telegram edit-overflow sets `raw_response["partial_overflow"]`).
- timestamp: 2026-06-26T13:30 — Implemented fix. See Resolution section.

## Eliminated

(hypotheses to be added)

## Resolution

**root_cause:** `gateway/stream_consumer.py` lacked a flood-control suspend window. On flood detection it only doubled `edit_interval` (capped at 10s) and kept issuing edits every cycle, which激怒 Telegram's sliding flood window and extended it from a few seconds to 30+ seconds. The final `sendRichMessage` then collided with the same extended window and failed all 5 retries, dropping the entire response.

**fix:** Ported openclaw's `draft-stream.ts` suspend-and-resume design:

1. New `_suspended_until_monotonic: float` field on `GatewayStreamConsumer` (stamps `time.monotonic() + retry_after`).
2. New `_extract_retry_after_seconds(result)` helper — parses retry_after from (a) `result.raw_response["retry_after"]` (adapter-extracted, the new telegram.py contract), (b) `result.raw_response.retry_after` (PTB RetryAfter attribute form), (c) regex `r"retry\s*(?:in|after)\s+(\d+)\s*seconds?"` on the error string.
3. New `_apply_flood_suspend(result)` — clamps retry_after to `[3s, 60s]`, stamps the field.
4. New `_is_suspended()` predicate.
5. Suspend GATE at the top of `_send_or_edit`: when suspended AND not `finalize`, return False immediately without touching the API. `_accumulated` keeps the latest text; first tick after expiry delivers it as one edit. This is the critical fix — zero API calls during the flood window.
6. `finalize=True` edits BYPASS the gate (mirrors openclaw line 339 comment: "Final flushes still try so the last text has a chance to land").
7. On flood-strike at line ~1540, call `_apply_flood_suspend(result)` to enter the window.
8. On successful edit at line ~1480, reset `_suspended_until_monotonic = 0.0`.
9. `gateway/platforms/telegram.py:_try_edit_rich` now extracts `retry_after` from the PTB exception (`exc.retry_after` or `exc.response.parameters.retry_after`) and surfaces it on `SendResult.raw_response["retry_after"]` so the consumer can parse it.

**verification:**
- 17 new unit tests in `tests/gateway/test_stream_consumer_flood_suspend.py` covering: regex parsing from error string, dict/attribute parsing from raw_response, caps/floors, suspend-gate behavior, finalize bypass, resume-after-expiry delivers latest text, flood-strike sets window, success clears window. ALL PASSING.
- 148 existing stream_consumer tests — ALL STILL PASSING (no regressions).
- 55 telegram rich-message tests — ALL STILL PASSING.
- `ruff check` on all 3 modified files — ALL CLEAN.
- `py_compile` on all 3 modified files — CLEAN.

**files_changed:**
- `gateway/stream_consumer.py` — added constants `_MAX_FLOOD_SUSPEND_SECONDS`, `_MIN_FLOOD_SUSPEND_SECONDS`, `_FLOOD_RETRY_AFTER_RE`; field `_suspended_until_monotonic`; methods `_extract_retry_after_seconds`, `_apply_flood_suspend`, `_is_suspended`; suspend gate in `_send_or_edit`; suspend-stamp on flood-strike; suspend-reset on success.
- `gateway/platforms/telegram.py` — `_try_edit_rich` now surfaces `retry_after` on `SendResult.raw_response`.
- `tests/gateway/test_stream_consumer_flood_suspend.py` — NEW file, 17 unit tests.
