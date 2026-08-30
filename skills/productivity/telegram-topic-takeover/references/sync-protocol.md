# Sync Protocol

接管后的双向同步协议。三个阶段:Load / Push / Sync。

## Load — 加载历史上下文

### 何时触发

- Bind 完成后立即触发一次
- 用户在后续会话里说:"加载 topic 上下文"、"看看 topic 历史"、"重新拉一下"
- 长会话中,用户感觉"上下文不够了"时

### 步骤

1. 读 manifest 拿当前 `project_path` 的 binding(没有就要求 Bind)
2. 调用:

```
mcp__hermes__messages_read(session_key="<binding.session_key>", limit=50)
```

3. 解析返回(消息按时间正序):

```json
{
  "session_key": "...",
  "messages": [
    {
      "role": "user",
      "content": "...",
      "timestamp": "2026-07-06T09:00:00Z",
      "user_name": "kai"
    },
    {
      "role": "assistant",
      "content": "...",
      "timestamp": "2026-07-06T09:01:00Z",
      "model": "glm-5.2"
    },
    ...
  ]
}
```

4. 摘要成结构化上下文(不要 paste 原文),输出给当前会话:

```
## Topic 上下文:Hermes Dev / v8.0 migration

**最近 50 条消息摘要**(截至 2026-07-06 10:00):

**关键决策**:
- 决定走 plugin-only 路线,不改 core(kai, 09:15)
- 用 platform:chat_id:thread_id 格式,不改 send_message_tool(glm-5.2, 09:20)

**待办 / Open Questions**:
- [ ] benchmark-prompts 集要 8 个还是 10 个?(kai, 09:45)
- [ ] docstring 修补要不要单独 commit?(kai, 09:50)

**当前阻塞**:无

**最近 5 条**:
- kai (09:55): "SKILL.md 主体写完了,接下来 references"
- glm-5.2 (09:56): "建议先写 bind-workflow,因为..."
- kai (09:58): "OK,继续"
- ...
```

5. 注入到当前 Claude Code 会话,作为"开发任务背景"。**不更新 manifest**(Load 不改 cursor)。

### Limit 选择

- 默认 `limit=50`(对齐 peer 惯例)
- 长会话 / 上下文复杂时可以 `limit=100`(最大 200,`mcp_serve.py:575`)
- 注意:`limit` 越大,注入会话的 token 越多。Claude Code 会话有 context 上限,Large limit 可能挤占代码上下文。**优先用 50,不够再加**

## Push — 推回 topic

### 何时触发

**用户明确请求**时:

- "把这个改动推回 topic"
- "在 topic 里同步一下进度"
- "告诉 topic 我搞定了 X"

**不要自动 Push**(避免 spam):
- 不要每改一行就 Push
- 不要每次 commit 都 Push(用户没说就别推)
- 不要在思考过程中 Push(只在用户请求或阶段结束时)

**例外**:**Bind 完成后可以推一条"已接管"通知**(让 Telegram 端用户知道 Claude Code 接管了)。但只推一次,在 Bind 阶段末尾。

### 步骤

1. 读 manifest 拿 binding
2. 准备 message(按 standard format,见下)
3. 调用:

```
mcp__hermes__messages_send(
  target="telegram:{binding.chat_id}:{binding.thread_id}",
  message="<formatted message>"
)
```

注意:

- `target` 里的 `chat_id` 是负数(supergroup ID 形如 `-100...`)直接拼字符串,不要加引号转义
- `thread_id` 是数字字符串(如 `"42"`),拼到 target 末尾
- 完整 target 形如:`"telegram:-1001234567890:42"`

### Standard Format

```
🤖 [Claude Code 接管] <阶段标签>
📍 <project_name> @ <commit sha 短 or "no-commit">
✅ <完成了什么,1-3 行,动词开头>
🔗 <相关文件 / PR / issue 链接>(可选,无则省略整行)
💬 <下一步问题 / 选项 / 阻塞>(可选,无则省略整行)
```

**阶段标签**(选最贴近的):

| 标签 | 何时用 |
|------|--------|
| `Plan` | 设计方案 / 拆解任务 / 写 plan |
| `Fix` | 修 bug |
| `Feature` | 新增功能 |
| `Review` | 代码审查 / 自检报告 |
| `Investigate` | 调研结论(无代码改动) |
| `Block` | 遇到阻塞,需要用户决策 |
| `Takeover` | Bind 完成通知(只在 Bind 末尾用一次) |

**示例 1 — Takeover 通知**:

```
🤖 [Claude Code 接管] Takeover
📍 hermes-agent @ no-commit
✅ 已接管这个 topic 的开发任务,后续代码改动会从这里同步过来
💬 直接在这里 @ 我或者回复本消息即可触发同步
```

**示例 2 — Feature 推送**:

```
🤖 [Claude Code 接管] Feature
📍 hermes-agent @ a1b2c3d
✅ 新增 telegram-topic-takeover skill(SKILL.md + 3 个 references + eval),支持 Bind/Load/Push/Sync 四阶段双向同步
🔗 skills/productivity/telegram-topic-takeover/
💬 接下来要加 LLM-as-judge eval 吗?v2 再加?
```

**示例 3 — Block 询问**:

```
🤖 [Claude Code 接管] Block
📍 hermes-agent @ no-commit
✅ 实现到一半,遇到一个选择需要你定
💬 benchmark-prompts 集:
  A) 8 个最小集
  B) 10 个完整覆盖
  C) 不写,以后用 LLM-as-judge
回复 A/B/C:
```

### Push 的内容禁忌

- **绝不贴大段代码**(超出 3 行就用 commit sha + GitHub link)
- **绝不贴绝对路径**(用相对路径,如 `skills/productivity/telegram-topic-takeover/`)
- **绝不贴 secret / token / API key / 内部 IP / 用户隐私数据**
- **绝不在 Push 消息里写"我做不到 X"**(那是 claude-code 会话内部的话,Push 只发"我做到了 Y"或"我需要 Z")

## Sync — 增量拉新消息

### 何时触发

**用户明确请求**时:

- "看看 TG 有什么新消息"
- "同步一下 topic"
- "看看 topic 里有没有人回复"

**不要自动定时 Sync**(v1 约束):
- 不调 cron
- 不在会话 idle 时自动拉
- 不在每次工具调用后拉

理由:避免 spam / 死循环 / 漏读。用户触发最稳。

### 步骤

1. 读 manifest 拿 binding(包括 `last_synced_cursor`)
2. 调用:

```
mcp__hermes__events_poll(
  after_cursor=<binding.last_synced_cursor>,
  session_key="<binding.session_key>",
  limit=20
)
```

3. 解析返回:

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
      ...
    },
    ...
  ],
  "next_cursor": 12350,
  "has_more": false
}
```

4. 把新增 user message 注入会话(摘要格式,不 paste 原文):

```
## Topic 新消息(3 条新,user 角色优先)

- kai (10:15): "想想 eval 要不要 LLM-as-judge"
- kai (10:20): "@ Claude 看一下 a1b2c3d 这个 commit 怎么样"
- glm-5.2 (10:21): "<assistant 回复,可作为上下文>"
```

5. 检查是否有指向 Claude Code 的请求:
   - `@ Claude` / `@claude` / "@CC" 等
   - "claude 看一下"、"cc 帮我看"
   - 回复之前 Push 的 `💬` 问题(编号 / 选项)
6. 有则**主动响应**(像用户直接问一样处理);无则只汇报"3 条新消息,无指向 CC 的请求"
7. 更新 manifest 的 `last_synced_cursor = next_cursor`,写回文件

### 处理 `has_more: true`

如果一次拉不完(返回 `has_more: true`):

- 循环再调一次,`after_cursor` 用刚拿到的 `next_cursor`
- 直到 `has_more: false`
- 全部新消息汇总后一次性注入会话(不要每条都单独 inject)

### cursor 一致性

- `last_synced_cursor` 是 manifest 里的关键字段,**必须持久化**(每次 Sync 末尾写回 manifest)
- 多个 Claude Code 会话同时接管同一个 topic:各自维护自己的 cursor(每个 binding 自带 last_synced_cursor;v1.1 起一个 project 可绑多个 topic,manifest 里同 project 下多条 binding 各持独立 cursor)
- cursor 是单调递增的整数(`mcp_serve.py:688` 限制在 `[0, 10^18)`)
- 跨会话恢复时,从 manifest 读 `last_synced_cursor` 继续即可

## 节奏总览

| 阶段 | 频率 | 触发 |
|------|------|------|
| Load | 每次 Bind 后 + 用户请求 | 一次性,~50 条历史 |
| Push | 用户请求 + Bind 末尾通知 | 单条,standard format |
| Sync | 用户请求 | 一次拉完所有新事件 |

**核心原则**:用户触发 > 自动触发。v1 不做任何自动同步。
