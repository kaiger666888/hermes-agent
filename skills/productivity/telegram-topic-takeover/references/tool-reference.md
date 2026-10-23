# MCP Tool Reference

本 skill 用到的所有 MCP 工具的完整调用示例。所有工具都通过 hermes-agent MCP server 暴露(`mcp_serve.py`),前缀是 `mcp__hermes__`(Claude Code 端的工具命名空间)。

## conversations_list

**用途**:列出 active 的 messaging session(Telegram topic 也是 session)。**Bind 阶段第一步**。

**参数**:

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `platform` | string (optional) | None | 过滤平台,如 `"telegram"` |
| `limit` | int (optional) | 50 | 最大返回数,范围 `[1, 200]` |
| `search` | string (optional) | None | 在 `display_name` / `chat_name` / `session_key` 上做大小写不敏感子串过滤 |

**示例 — Bind 时找 telegram topic**:

```
mcp__hermes__conversations_list(platform="telegram", search="hermes", limit=50)
```

**返回**(节选):

```json
{
  "count": 2,
  "conversations": [
    {
      "session_key": "agent:main:telegram:forum:-1001234567890:42:888999",
      "session_id": "abc123...",
      "platform": "telegram",
      "chat_type": "forum",
      "display_name": "Hermes Dev / v8.0 migration",
      "chat_name": "Hermes Dev",
      "user_name": "kai",
      "updated_at": "2026-07-06T10:00:00Z"
    }
  ]
}
```

**注意**:`search` 是服务端过滤,**还要客户端再做 fuzzy match**(用户给的"group 名 + topic 名"经常分散在 display_name / chat_name 里)。

---

## conversation_get

**用途**:从一个 `session_key` 拿详细信息,包括 `chat_id` 和 `thread_id`。**Bind 阶段第二步**。

**参数**:

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `session_key` | string (required) | — | 从 `conversations_list` 拿到的 session_key |

**示例**:

```
mcp__hermes__conversation_get(session_key="agent:main:telegram:forum:-1001234567890:42:888999")
```

**返回**:

```json
{
  "session_key": "agent:main:telegram:forum:-1001234567890:42:888999",
  "session_id": "abc123...",
  "platform": "telegram",
  "chat_type": "forum",
  "display_name": "Hermes Dev / v8.0 migration",
  "user_name": "kai",
  "chat_name": "Hermes Dev",
  "chat_id": "-1001234567890",
  "thread_id": "42",
  "updated_at": "2026-07-06T10:00:00Z",
  "created_at": "2026-07-01T08:00:00Z",
  "input_tokens": 12345,
  "output_tokens": 6789,
  "total_tokens": 19134
}
```

**关键**:`chat_id` 和 `thread_id` 字段直接可用,Push 时拼 `target="telegram:{chat_id}:{thread_id}"`。

---

## messages_read

**用途**:拉一个 session 的历史消息。**Load 阶段**用。

**参数**:

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `session_key` | string (required) | — | 从 manifest 或 conversations_list 拿 |
| `limit` | int (optional) | 50 | 最大消息数,范围 `[1, 200]` |

**示例**:

```
mcp__hermes__messages_read(
  session_key="agent:main:telegram:forum:-1001234567890:42:888999",
  limit=50
)
```

**返回**:

```json
{
  "session_key": "...",
  "messages": [
    {
      "role": "user",
      "content": "想想 v8.0 要做什么",
      "timestamp": "2026-07-06T09:00:00Z",
      "user_name": "kai"
    },
    {
      "role": "assistant",
      "content": "建议先...",
      "timestamp": "2026-07-06T09:00:30Z",
      "model": "glm-5.2"
    },
    ...
  ],
  "count": 50,
  "has_more": true
}
```

**注意**:`has_more: true` 表示还有更早的历史。一般 50 条够用,不够再调一次(没有 `before` 参数,所以更早的消息只能通过加大 `limit` 拿)。

---

## messages_send

**用途**:发消息到一个平台会话。**Push 阶段**用。

**参数**:

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `target` | string (required) | — | 格式 `platform:chat_id:thread_id`(topic)或 `platform:chat_id`(主聊天) |
| `message` | string (required) | — | 消息文本 |

**target 格式**(完整列表见 `tools/send_message_tool.py:154`):

- `telegram` — home channel(默认)
- `telegram:CHAT_ID` — 主聊天 / 普通群
- `telegram:CHAT_ID:THREAD_ID` — **forum topic**(本 skill 主要用这个)
- `discord:#channel-name` — Discord 频道
- `discord:CHANNEL_ID:THREAD_ID` — Discord thread
- `slack:#channel-name` — Slack 频道
- 其他平台见 schema

**示例 — 推到 forum topic**:

```
mcp__hermes__messages_send(
  target="telegram:-1001234567890:42",
  message="🤖 [Claude Code 接管] Feature\n📍 hermes-agent @ a1b2c3d\n✅ 新增 telegram-topic-takeover skill\n🔗 skills/productivity/telegram-topic-takeover/"
)
```

**chat_id 是负数**(supergroup ID 形如 `-100...`),直接拼字符串。

**thread_id 是数字字符串**(如 `"42"`),拼到 target 末尾。

**返回**:

```json
{
  "status": "sent",
  "platform": "telegram",
  "chat_id": "-1001234567890",
  "thread_id": "42",
  "message_id": 12345
}
```

**失败情况**:

```json
{ "error": "Both target and message are required" }
{ "error": "Send failed: <reason>" }
```

**注意**:本 skill v1 不动 `send_message_tool.py`(已支持 thread_id)。仅在 `mcp_serve.py:734-752` 加了 docstring 示例,告诉 Claude Code 这格式可用。

---

## events_poll

**用途**:拉取指定 cursor 之后的新事件。**Sync 阶段**用。

**参数**:

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `after_cursor` | int (optional) | 0 | 返回此 cursor 之后的事件,`0` = 全部 |
| `session_key` | string (optional) | None | 过滤到单个 session(本 skill 必传) |
| `limit` | int (optional) | 20 | 最大事件数,范围 `[1, 200]` |

**示例**:

```
mcp__hermes__events_poll(
  after_cursor=12345,
  session_key="agent:main:telegram:forum:-1001234567890:42:888999",
  limit=20
)
```

**返回**:

```json
{
  "events": [
    {
      "type": "message",
      "session_key": "...",
      "role": "user",
      "content": "想想 eval 要不要 LLM-as-judge",
      "timestamp": "2026-07-06T10:15:00Z",
      "user_name": "kai"
    },
    {
      "type": "message",
      "session_key": "...",
      "role": "assistant",
      "content": "...",
      "timestamp": "2026-07-06T10:15:30Z"
    },
    {
      "type": "approval_requested",
      "session_key": "...",
      "approval_id": "...",
      ...
    }
  ],
  "next_cursor": 12350,
  "has_more": false
}
```

**事件类型**:`message` / `approval_requested` / `approval_resolved`。本 skill 主要处理 `message`,其他类型可作为上下文展示。

**关键**:`next_cursor` **必须**写回 manifest 的 `last_synced_cursor`。

---

## events_wait(可选,本 skill v1 不强用)

**用途**:长轮询版本 of `events_poll`。阻塞直到有新事件或超时。

**参数**:

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `after_cursor` | int (optional) | 0 | 同 events_poll |
| `session_key` | string (optional) | None | 同 events_poll |
| `timeout_ms` | int (optional) | 30000 | 阻塞最长时间,毫秒 |

**何时用**:本 skill v1 不用(只做用户触发的 Sync,不等)。v2 若要做"等待回复"模式,可用此工具。

---

## 组合示例:完整 Bind 流程

```
# 1. 列出候选
conversations = mcp__hermes__conversations_list(platform="telegram", search="hermes", limit=50)

# 2. 用户选了 [1],拿 chat_id + thread_id
info = mcp__hermes__conversation_get(session_key=conversations[0].session_key)
# info.chat_id = "-1001234567890", info.thread_id = "42"

# 3. 写 manifest(用普通 file 工具)
write_file("~/.hermes/topic_takeover_bindings.json", binding_record)

# 4. 拿初始 cursor
events = mcp__hermes__events_poll(session_key=info.session_key, limit=1)
update_manifest(last_synced_cursor=events.next_cursor)

# 5. 立即 Load
messages = mcp__hermes__messages_read(session_key=info.session_key, limit=50)
summarize_and_inject(messages)
```

## 组合示例:完整 Push 流程

```
# 1. 读 manifest
binding = read_manifest_for_current_project()

# 2. 拿当前 commit
sha = git("rev-parse --short HEAD")  # 或 git log -1 --format=%h

# 3. 拼 standard format 消息
msg = f"""🤖 [Claude Code 接管] Feature
📍 hermes-agent @ {sha}
✅ 新增 telegram-topic-takeover skill (SKILL.md + 3 个 references + eval)
🔗 skills/productivity/telegram-topic-takeover/
💬 接下来要加 LLM-as-judge eval 吗?"""

# 4. 推送
mcp__hermes__messages_send(
  target=f"telegram:{binding.chat_id}:{binding.thread_id}",
  message=msg
)
```

## 组合示例:完整 Sync 流程

```
# 1. 读 manifest
binding = read_manifest_for_current_project()

# 2. 拉新事件
events = mcp__hermes__events_poll(
  after_cursor=binding.last_synced_cursor,
  session_key=binding.session_key,
  limit=20
)

# 3. 处理 has_more
while events.has_more:
  more = mcp__hermes__events_poll(after_cursor=events.next_cursor, ...)
  events.events.extend(more.events)
  events.next_cursor = more.next_cursor
  events.has_more = more.has_more

# 4. 摘要新消息
summary = summarize_new_messages(events.events)
inject_into_session(summary)

# 5. 检查指向 CC 的请求
requests = extract_cc_directed_requests(events.events)
if requests:
  respond_to_requests(requests)

# 6. 更新 manifest
update_manifest(last_synced_cursor=events.next_cursor)
```
