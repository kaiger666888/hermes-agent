# Benchmark Prompts — Manual Verification

v1 不上 LLM-as-judge(对齐 movie-experts v2"轻量起步"原则)。这套 prompt 集用于手工 E2E 验证:每个 prompt 对应一个核心能力,跑完后人工判断是否符合预期。

## 跑法

1. 准备:在某个 Telegram forum topic 里至少有 5-10 条历史消息(hermes-agent gateway 在跑,session 已创建)
2. 在 Claude Code 里依次跑下面的 prompt,每个 prompt 后观察:
   - Claude Code 是否调对了 MCP 工具?
   - 是否写对了 manifest?
   - 是否生成了合理的 Telegram 推送消息?
   - 是否在会话里给出了有用的摘要?

## Prompts

### B1 — Bind(精确)

```
接管 telegram hermes dev 群的 v8.0 migration topic
```

**期望**:
- 调 `conversations_list(platform="telegram", search="hermes" 或 "v8")`
- 列出候选,可能需要让用户确认
- 用户确认后调 `conversation_get` 拿 chat_id + thread_id
- 写 `~/.hermes/topic_takeover_bindings.json`
- 调一次 `events_poll` 拿初始 cursor
- 立即调 `messages_read` 加载历史
- 在 topic 里推一条 Takeover 通知(可选,skill 里写了"Bind 末尾可推一次")

### B2 — Bind(模糊)

```
我那个 hermes 群里 v8 什么的 topic,接管一下
```

**期望**:
- `conversations_list` 拉到多个候选(含 "v7 openclaw" / "v8 migration" / "random-chat")
- fuzzy match 选出含 "v8" 的
- 多候选时**列出来让用户选**,不擅自决定

### B3 — Bind(零候选)

```
接管 telegram foo 群的 bar topic
```

(假设 foo/bar 不存在)

**期望**:
- `conversations_list` 返回空 / 无匹配
- 友好提示:"没找到匹配 ... 的 topic"
- 给可能原因 + 建议(检查 gateway / 让 topic 先有消息 / 拼写)

### B4 — Bind(覆盖)

(先跑 B1,然后再跑:)

```
换成 hermes dev 的 v7 openclaw topic
```

**期望**:
- 检测到当前 project 已绑定到 "v8.0 migration"
- 提示"已绑定到 <display_name>,要覆盖吗?"
- 用户 yes 才覆盖,更新 manifest

### L1 — Load(默认)

(先跑 B1,然后在**新会话**里:)

```
加载 topic 上下文
```

**期望**:
- 读 manifest
- 调 `messages_read(session_key, limit=50)`
- 输出结构化摘要(关键决策 / 待办 / 阻塞 / 最近几条)
- 不 paste 原始消息文本

### L2 — Load(大 limit)

```
加载 topic 历史,100 条
```

**期望**:
- 同 L1,但 `limit=100`
- 摘要时更详细(更多决策点)

### P1 — Push(Feature)

(做完一个小改动并 commit 后:)

```
把这个变更推回 topic
```

**期望**:
- 读 manifest 拿 chat_id + thread_id
- 取当前 commit short sha
- 拼 standard format(🤖 [Claude Code 接管] Feature)
- 调 `messages_send(target="telegram:-100...:42", message=...)`
- Telegram 端能看到带 emoji 头的消息

### P2 — Push(Block)

(故意制造一个需要用户决策的分支:)

```
我卡在 X 选择了,在 topic 里问一下
```

**期望**:
- 阶段标签用 `Block`
- 用 `💬` 行写清楚问题 + 选项

### P3 — Push(不要 spam)

(连续说 3 次:)

```
推一下进度
推一下进度
推一下进度
```

**期望**:
- 第一次正常推
- 第二次应该问"刚才已经推过一次了,要再推吗?"(不擅自重复推)
- 第三次同上

### S1 — Sync(无新消息)

(在 Bind 后,topic 里没新消息:)

```
看看 TG 有什么新消息
```

**期望**:
- 调 `events_poll(after_cursor=last_synced_cursor, ...)`
- 返回空 / 少量 assistant 自己之前的回复
- 汇报"无新用户消息"或"0 条新消息"

### S2 — Sync(有新消息)

(在 topic 里发几条新消息后:)

```
同步一下 topic
```

**期望**:
- 调 `events_poll`
- 拉到新 user message
- 摘要注入会话(角色 / 时间 / 内容)
- 更新 manifest 的 `last_synced_cursor`

### S3 — Sync(有指向 CC 的请求)

(在 topic 里发 "@ Claude 看一下 a1b2c3d 这个 commit":)

```
看看 TG 有没有人 @ 我
```

**期望**:
- 调 `events_poll`
- 识别 "@ Claude" 模式
- 主动取出 commit a1b2c3d 的信息
- 像用户直接问一样响应

### U1 — Unbind

```
解绑这个 project
```

**期望**:
- 从 manifest 删当前 project 的 binding
- 不删 topic / 不发消息到 topic
- 提示"已解绑"

### U2 — 未绑定时调任何 Load/Push/Sync

(在 U1 之后,或新环境没绑定时:)

```
加载 topic 上下文
```

**期望**:
- 检测到 manifest 无 binding
- 不 crash
- 提示"未绑定,先说'接管 telegram ...'"

### E1 — Manifest 损坏

(手工把 `topic_takeover_bindings.json` 改成无效 JSON,然后:)

```
加载 topic 上下文
```

**期望**:
- 读 manifest 失败(JSON parse error)
- 备份原文件到 `.bak-<timestamp>`
- 初始化空 manifest
- 提示"manifest 损坏已重置,请重新 Bind"

## 评分维度(手工 rubric)

每个 prompt 跑完后,从以下维度打 1-5 分:

| 维度 | 5 分 | 1 分 |
|------|------|------|
| 工具调用正确性 | 调对了所有 MCP 工具,参数对 | 调错工具或参数 |
| 摘要质量 | 结构化、信息密度高、不 paste 原文 | 平铺直叙 paste / 漏关键信息 |
| 推送消息格式 | 严格遵循 standard format | 自由发挥、漏 emoji 头、贴大段代码 |
| 用户确认节点 | 模糊匹配后让用户选 / 覆盖 binding 前确认 | 擅自决定 |
| 边界处理 | 零候选 / 未绑定 / manifest 损坏时优雅处理 | crash 或编造 |
| 推送频率 | 用户请求才推,不 spam | 自动重复推 |

整体 skill 通过标准:每个 prompt 总分 ≥ 4/5,所有 prompt 平均 ≥ 4.2/5。

## v2 升级目标

如果 v1 跑下来评分稳定 ≥ 4.5/5,可以考虑 v2:

- 加 LLM-as-judge harness(对齐 movie-experts eval 模式)
- 加"自动定时 Sync"模式(用户开启后周期拉)
- 加 Telegram 端反向触发(在 topic 里 `/claude` 唤起)
- 推广到 Discord thread / Slack thread
