# Bind Workflow

把"用户的自然语言描述"(如"接管 hermes dev 群的 v8 topic")转换成 manifest 里的一条 binding 记录。这是四个阶段里最复杂的一步,因为要做候选识别和确认。

## 输入:用户给的标识

用户可能给出以下任意组合(从最精确到最模糊):

1. **精确**:`chat_id=-1001234567890` + `thread_id=42`(很少见,用户通常不记数字)
2. **半精确**:group 名("Hermes Dev")+ topic 名("v8.0 migration")
3. **模糊**:group 简称("hermes")+ topic 关键词("v8 那个")
4. **只有其一**:只给 group 或只给 topic(需要进一步追问)

## 关键约束(经实测验证)

**`origin.chat_topic` 当前是 null** —— `gateway/platforms/telegram.py:558` 构造 SessionSource 时未填 `chat_topic` 字段。所以:

- ❌ 不能假设 `display_name` 含 topic 名(实际只有 group 名,如 "Hermes-Agent")
- ❌ 不能假设 `chat_topic` 字段有值
- ✅ **可以**用 `chat_id` + `thread_id` 精确匹配
- ✅ **可以**用"最后一条消息的内容预览"作为 topic 识别依据(用户视觉判断)
- ✅ **可以**用 `updated_at` 排序找最近活跃的 topic

如果用户给的是"topic 名",对该 topic 名做**消息内容搜索**(在 messages_read 拉到的消息里找关键词),而不是对 session 元数据搜索。

## 步骤

### Step 1 — 列出候选 session(服务端过滤 group)

调用 `conversations_list` 拿到所有 telegram active session:

```
mcp__hermes__conversations_list(platform="telegram", search="<group 名>", limit=50)
```

`search` 是在 `display_name` / `chat_name` / `session_key` 上做大小写不敏感子串匹配(`mcp_serve.py:500-505`)。注意 `search` 对 forum topic 不太有效 —— `display_name` 通常是 group 名(如 "Hermes-Agent"),所有 topic 的 `display_name` 都一样,所以 search 主要过滤 group。

返回结构(`mcp_serve.py:521-524`):

```json
{
  "count": 51,
  "conversations": [
    {
      "session_key": "agent:main:telegram:group:-1004378251055:1",
      "session_id": "...",
      "platform": "telegram",
      "chat_type": "group",
      "display_name": "Hermes-Agent",
      "chat_name": "Hermes-Agent",
      "user_name": "Kai",
      "updated_at": "2026-07-06T07:07:34Z"
    },
    ...
  ]
}
```

### Step 2 — 客户端过滤 + 排序

拿到列表后,客户端做:

1. **过滤有 thread_id 的**:从 `session_key` 末段或 `conversation_get` 拿 thread_id,只保留有 thread_id 的(`origin.thread_id != null`)
2. **按 `updated_at` 倒序**:最近活跃的优先
3. **取 top 10**(避免候选过多)

如果用户给了 topic 名关键词,继续 Step 3 拉消息预览做识别;如果用户给了 thread_id,直接 Step 4。

### Step 3 — 拉每个候选的最后消息预览

对每个候选(最多 top 10),调:

```
mcp__hermes__messages_read(session_key="<候选的 session_key>", limit=3)
```

取最后一条 user message 的前 60-80 字符作为"预览"。

如果用户给了 topic 关键词(如 "v8"),在消息内容里 fuzzy match,优先级提到最前。

### Step 4 — 列候选让用户选

输出形如:

```
找到 8 个 Hermes-Agent group 下的活跃 topic,选一个:

  [1] thread_id=1     | 最后: "停止" (Kai, 07-06 07:07)
  [2] thread_id=1501  | 最后: "看看 v7 openclaw 迁移的进度" (Kai, 06-29 14:40)
  [3] thread_id=1618  | 最后: "ep-cat-boss 管线后台还在跑..." (glm-5.2, 06-29 20:28)
  [4] thread_id=1542  | 最后: "GLM 过载降并发..." (Kai, 06-27 22:03)
  ...

回复编号(或精确给 thread_id):
```

**单候选**(filter 后只剩 1 个):

```
找到 1 个匹配:
  thread_id=42 | 最后: "<预览>" (Kai, 07-06 10:00)
是这个吗?(yes / no)
```

**零候选**:告诉用户没找到,可能原因 + 建议:

```
没找到匹配 "hermes dev / v8" 的 topic。可能原因:
  - hermes-agent gateway 没在跑(systemctl --user status hermes-gateway)
  - 该 topic 还没有任何消息(hermes-agent 还没创建 session)
  - group 名拼写不一致(实际 group 名是 "Hermes-Agent")
建议:在该 topic 里发一条消息让 hermes-agent 创建 session,再重试。
```

### Step 5 — 拿 chat_id + thread_id(确认后)

用户选定后,调:

```
mcp__hermes__conversation_get(session_key="<选中的 session_key>")
```

返回(`mcp_serve.py:542-557`):

```json
{
  "session_key": "agent:main:telegram:group:-1004378251055:1",
  "platform": "telegram",
  "chat_type": "group",
  "display_name": "Hermes-Agent",
  "chat_id": "-1004378251055",
  "thread_id": "1",
  ...
}
```

记下 `chat_id` 和 `thread_id` —— Push 阶段拼 `target="telegram:{chat_id}:{thread_id}"` 时要用。

### Step 6 — 写 manifest

读 `~/.hermes/topic_takeover_bindings.json`(不存在则初始化 `{"version": 1, "bindings": []}`)。

检查当前 `project_path` + 新 `thread_id` 的组合是否已有 binding(2026-07-14 v1.1 起,去重键是 `project_path + thread_id`,不再用 `project_path` 唯一):

- **该 project 下没有该 thread_id 的 binding**:append 新 binding(同一 project 允许累积多个 topic binding)
- **该 project 下已有该 thread_id 的 binding**:提示"已接管过 thread_id=X,要刷新 last_synced_cursor 重置 cursor 吗?" → 用户 yes 则更新该 binding 的 `last_synced_cursor` + `bound_at`,不新增
- **该 project 下已有别的 thread_id binding**:不视为冲突,直接 append;session 端自行决定 active 哪个

新 binding 记录:

```json
{
  "project_path": "<当前 cwd>",
  "session_key": "agent:main:telegram:group:-1004378251055:1",
  "chat_id": "-1004378251055",
  "thread_id": "1",
  "group_name": "Hermes-Agent",
  "topic_name": null,
  "last_message_preview": "<预览,帮助下次会话识别>",
  "display_name": "Hermes-Agent / thread 1",
  "bound_at": "<ISO 8601 UTC,如 2026-07-06T10:30:00Z>",
  "last_synced_cursor": 0,
  "default_push_format": "standard"
}
```

注意:`topic_name` 留 null(当前数据无值),`display_name` 拼成 `"<group_name> / thread <thread_id>"` 形式方便人眼区分。

写回 JSON 文件,`encoding="utf-8"`,indent=2。

### Step 7 — 拿初始 cursor

调一次:

```
mcp__hermes__events_poll(session_key="<新 binding 的 session_key>", limit=1)
```

返回的 `next_cursor` 就是当前最新的 cursor 位置(之后新消息才会被 Sync 阶段拉到)。把这个值写回 manifest 的 `last_synced_cursor`,这样"接管之后才发生的新消息"才会被同步 —— 接管之前的历史已经通过 Load 阶段拉过了,不重复。

### Step 8 — 立即 Load

绑定完成后立即走 Load 阶段(`messages_read`),把历史上下文加载到当前会话,告诉用户"已接管 thread X,准备开始"。

## Manifest 文件操作约束

- **读写都用 `encoding="utf-8"`**(对齐 Ruff `PLW1514`,Windows 安全)
- **写回时保留 indent=2**(可读性,便于 git diff)
- **并发**:多个 Claude Code 会话可能同时读写 manifest,v1 不做锁(乐观:各会话 project_path 不同,改的 binding 记录不同);失败时整体重读再写
- **路径**:`~/.hermes/topic_takeover_bindings.json`,通过 `HERMES_HOME` 环境变量可改根(对齐 `hermes_constants.get_hermes_home()`)
- **manifest 损坏**(JSON parse 失败):**不要 crash**。提示用户"manifest 损坏,备份到 `.bak-<timestamp>` 后重置",然后初始化空 manifest 继续

## 边界情况

- **forum topic vs DM topic**:本 skill 默认指 forum topic(`chat_type: "forum"`)。DM topic(`chat_type: "dm"`)在 hermes-agent 里也是 session_key 一部分,但语义不同(DM topic 是私聊话题),v1 不强制区分 — 用户给的 topic 名能匹配上就用
- **group 是普通 group(非 forum)**:没有 topic 概念,session_key 里 `thread_id` 段为空。本 skill 不适用(用户不会"接管普通 group",直接用 `messages_send` 即可)
- **chat_id 是用户自己的 DM**:`conversations_list` 也会列出。如果用户给的"group 名"匹配到 DM,提示"这是 DM 不是 group topic,确认?"
