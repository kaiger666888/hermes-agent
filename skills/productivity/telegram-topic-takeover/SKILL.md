---
name: telegram-topic-takeover
description: "Take over a Telegram group's forum topic as a Claude Code dev session: pull topic history as context via hermes-agent MCP, push commits/decisions back to the topic. Bidirectional sync through conversations_list/messages_read/messages_send/events_poll."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [telegram, topic, forum, takeover, handoff, claude-code, sync, mcp, dev-session]
    related_skills: [thinking-partner, plan, hermes-agent-skill-authoring]
---

# Telegram Topic Takeover

把 Telegram 群组里某个 forum topic 的开发讨论"接管"到 Claude Code 会话里继续推进。Claude Code 通过 hermes-agent 暴露的 MCP 工具,**双向同步**:拉取 topic 历史作为开发上下文,完成后把 commit / 决策 / 问题推回 topic。

## When to use this skill

触发条件(任一即可):

- 用户说"接管 telegram 的 X group 的 Y topic"、"把这个 topic 拉到 Claude Code"、"继续 topic 里的开发任务"
- 用户提到某个 Telegram topic 上的讨论,希望基于它继续做代码工作
- 用户希望 Claude Code 完成的产物能自动同步回 Telegram topic(而不是手工 paste)

不要用于:

- 简单的一次性问答(直接在 hermes-agent gateway 里答即可,不需要"接管")
- 跨多个 topic / 群的广播式推送(本 skill 是一对一绑定)
- 在 topic 里反向触发 Claude Code(本 skill 是 Claude Code 端发起,v1 不做 TG 端触发)

## CRITICAL: How It Works

**永远不要 paste 历史消息**。hermes-agent 已经把每个 Telegram topic 当作独立 session 持久化了完整历史,通过 MCP 工具可以按需拉取。Paste 不仅冗余,还会丢失时间戳 / 角色 / 附件元数据。

工作流是四个阶段,每阶段对应一个 MCP 工具调用:

| 阶段 | 何时做 | MCP 工具 | 写 manifest? |
|------|--------|----------|--------------|
| **Bind** | 首次接管 / 切换 topic | `conversations_list` + `conversation_get` | 写入新 binding |
| **Load** | 会话开始 / 用户要"加载上下文" | `messages_read` | 读 `last_synced_cursor` |
| **Push** | 完成阶段性产物 | `messages_send` (target=`platform:chat_id:thread_id`) | 不动 |
| **Sync** | 用户说"看看 TG 新消息" | `events_poll` | 更新 `last_synced_cursor` |

详见 `references/bind-workflow.md`、`references/sync-protocol.md`、`references/tool-reference.md`。

## Bind Manifest

绑定信息存在 `~/.hermes/topic_takeover_bindings.json`(skill 自己读写,JSON 文件,跟 `channel_directory.json`、`gateway_state.json` 同级惯例)。

结构:

```json
{
  "version": 1,
  "bindings": [
    {
      "project_path": "/data/workspace/hermes-agent",
      "session_key": "agent:main:telegram:group:-1004378251055:1",
      "chat_id": "-1004378251055",
      "thread_id": "1",
      "group_name": "Hermes-Agent",
      "topic_name": null,
      "last_message_preview": "停止 (Kai, 07-06 07:07)",
      "display_name": "Hermes-Agent / thread 1",
      "bound_at": "2026-07-06T10:30:00Z",
      "last_synced_cursor": 12345,
      "default_push_format": "standard"
    }
  ]
}
```

规则:

- **一个 `project_path` 可以绑多个 topic**(2026-07-14 起 v1.1,支持同一 dev session 在不同 topic 之间切换;之前版本是单 topic 覆盖)
- **去重键**:`project_path + thread_id` —— 同一 project 同一 thread_id 已存在则视为重复接管,不新增,只问是否刷新 cursor
- **一个 topic 可被多个 project 绑**(不同 dev session 接管同一个 topic 是合法的)
- **active binding**:每个 Claude Code session 同一时间只把一个 binding 当作"当前接管"。manifest 不强制记录 active 状态,由 session 内存决定;若需持久化,在 binding 记录里加 `is_active: true` 字段(v1.1 可选,不强求)
- 没绑定时,所有 Load / Push / Sync 都先要求用户走 Bind 流程

读写 manifest 用普通 file 工具(`read_file` / `write_file` / `edit`),`encoding="utf-8"`(Windows 安全,对齐 Ruff `PLW1514` 规则)。

## Standard Push Message Format

推回 topic 的消息统一用以下格式(`default_push_format: "standard"`),让 Telegram 端用户一眼能看出是 Claude Code 接管产物:

```
🤖 [Claude Code 接管] <阶段标签>
📍 <project_name> @ <commit sha 短 or "no-commit">
✅ <完成了什么,1-3 行,动词开头>
🔗 <相关文件 / PR / issue 链接>(可选,无则省略整行)
💬 <下一步问题 / 选项 / 阻塞>(可选,无则省略整行)
```

阶段标签(从中选一个,语义最贴近的):

- `Plan` — 设计方案 / 拆解任务
- `Fix` — 修 bug
- `Feature` — 新增功能
- `Review` — 代码审查 / 自检报告
- `Investigate` — 调研结论(无代码改动)
- `Block` — 遇到阻塞,需要用户决策

**绝不贴大段代码**。代码改动用 commit sha + GitHub link 表达;如果必须贴,只贴 1-3 行关键 diff,超出用"详见 commit xxx"。

## Common Patterns

- **初次绑定**:用户给"group 名 + topic 关键词" → `conversations_list(platform="telegram", search=...)` 过滤 group → `messages_read(session_key, limit=3)` 拉每个候选 topic 的最近 1-2 条消息作为"预览" → 列出 `(thread_id, last_message_preview, updated_at)` 让用户视觉选(当前 telegram adapter 未填 `chat_topic`,无法按 topic 名直接匹配) → `conversation_get` 拿 `chat_id` / `thread_id` → 写 manifest → `events_poll(session_key=...)` 拿初始 cursor
- **会话开始加载**:读 manifest 拿 `session_key` → `messages_read(session_key, limit=50)` → 摘要成"开发任务上下文"(角色 / 决策 / 待办 / 阻塞)注入会话
- **推送 commit**:取最近 commit 的 short sha + message + 影响文件 → 套 standard format → `messages_send(target="telegram:{chat_id}:{thread_id}", message=...)`
- **增量同步**:`events_poll(after_cursor=last_synced_cursor, session_key=...)` → 把新增 user message 注入会话;若有 `@ Claude` 或明确请求,主动响应 → 写回新的 `last_synced_cursor`
- **问 TG 用户问题**:遇到需要用户决策的阻塞,用 Push 推一条 `💬 <问题>` 消息(阶段标签 `Block`),而不是停下等
- **切换 topic**:用户说"换成 Y topic" → 重走 Bind(同一 project 下追加新 binding;session 端把 active 切到新的 thread_id)
- **解绑**:用户说"解绑" / "停止接管" → 从 manifest 删 binding(不删 topic 本身的任何东西)
- **manifest 损坏 / 缺失**:不要 crash;告诉用户"未绑定,先走 Bind 流程"

## Tools Quick Reference

| 工具 | 关键参数 | 用途 |
|------|----------|------|
| `mcp__hermes__conversations_list` | `platform="telegram"`, `search=<group/topic 名>`, `limit=50` | Bind 阶段:列出匹配的 active session |
| `mcp__hermes__conversation_get` | `session_key=<from conversations_list>` | Bind 阶段:拿 `chat_id` / `thread_id` |
| `mcp__hermes__messages_read` | `session_key`, `limit=50` | Load 阶段:拉历史消息 |
| `mcp__hermes__messages_send` | `target="telegram:{chat_id}:{thread_id}"`, `message=...` | Push 阶段:推回 topic |
| `mcp__hermes__events_poll` | `after_cursor=<last_synced_cursor>`, `session_key=...`, `limit=20` | Sync 阶段:增量拉新事件 |

完整调用示例见 `references/tool-reference.md`。

## Don't

- **不要 paste 历史消息**进会话。用 `messages_read` 拉摘要,不要把 TG 上的原始消息文本贴进 Claude Code 上下文(冗余 + 丢元数据)。
- **不要在 topic 里贴大段代码**。用 commit sha + link。最多 1-3 行关键 diff。
- **不要 spam 推送**。每个阶段产物推 1 条 `standard` 消息即可,不要每改一行就推。
- **不要自动定时同步**。v1 只做用户触发的 Sync(用户说"看看新消息"才拉),避免 spam / 死循环。
- **不要绕过 manifest 直接调 messages_send**。所有 Push 都应该通过 manifest 里的 binding 拿 `chat_id` / `thread_id`,避免硬编码。
- **不要假设 topic 名字精确**。用户给的"group 名 / topic 名"经常是模糊的(简写、别名),必须列出候选让用户视觉选。当前 telegram adapter 未填 `chat_topic`(`origin.chat_topic` 是 null),所以**用每个候选 topic 的最后一条消息预览做识别**,而不是 topic 名。
- **不要在 Push 消息里暴露绝对路径、API key、token、内部 IP** 等。Push 消息是会发到 Telegram 群的,假设它会泄漏。

## Edge Cases

- **topic 还没有任何消息**(刚建的 forum topic):`conversations_list` 可能找不到(没 active session)。这种情况让用户先在 topic 里发一条消息触发 hermes-agent 创建 session,然后再 Bind。
- **`chat_topic` 字段为 null**:`gateway/platforms/telegram.py:558` 构造 SessionSource 时未填 `chat_topic`,所以 `origin.chat_topic` 一直是 null。v1 不依赖此字段,改用"最后消息预览"识别 topic。如果未来 hermes-agent 填充了此字段,可以加 fuzzy-by-name 路径。
- **chat_id 是负数**(supergroup ID 形如 `-1001234567890`):`target` 里直接用负数字符串,不要加引号转义。`-` 是 chat_id 的一部分。
- **thread_id 是数字字符串**:Telegram 的 `message_thread_id` 是整数,但 manifest 和 target 字符串里都按字符串处理,统一惯例。
- **多个 Claude Code 会话同时接管同一个 topic**:合法,但 Push 时各自独立,不会去重(用户自己协调)。
- **gateway 没运行**:MCP 工具调用会失败。提示用户检查 `systemctl --user status hermes-gateway`。
- **`Platform 'telegram' is not configured` 报错**:说明 send_message_tool 读不到 telegram bot token。两种情况:(1) gateway 没在跑 — 启动它(`systemctl --user restart hermes-gateway`);(2) 直接用 Python 调底层(非经 MCP)时没加载 `.env` — `send_message_tool` 依赖 `~/.hermes/.env` 里的 `TELEGRAM_BOT_TOKEN`(由 `gateway/config.py:1311` 映射,行 1371 读取)。MCP server 进程通过 `hermes_bootstrap.py` 自动加载 .env,所以走 MCP 路径不会遇到此问题。

## Implementation Notes

底层基础设施(已就绪,不动):

- `gateway/session.py:618` `build_session_key` 已把 `thread_id` 纳入路由 key,每个 topic 是独立 session
- `tools/send_message_tool.py:154` 已原生支持 `platform:chat_id:thread_id` 格式
- `mcp_serve.py:528` `conversation_get` 已返回 `thread_id`(`mcp_serve.py:551`)
- `mcp_serve.py:670` `events_poll` 已支持按 `session_key` 过滤

本 skill 只新增 markdown 内容 + 1 处 `mcp_serve.py` `messages_send` docstring 增强(让 Claude Code 知道可以用 `chat_id:thread_id` 格式),不改任何核心逻辑。
