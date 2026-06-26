# Data Convergence — 平台数据回流与公式调优闭环 (Phase 42 DATA, Step 15)

**Last-verified:** 2026-06-27 (Phase 42 v9.0 additive)
**Phase:** 42 (DATA — 数据收敛, Step 15)
**Depends on:**
- Phase 38 (SLICE — `variants[]` schema, shipped 2026-06-27)
- Phase 39 (FORM — `plugins/formula_library/`, shipped)
- v6.0 FeedbackStore (`agent/feedback_store.py` — READ ONLY via public API)
- Phase 28 (INGEST — `agent/feedback_schema.py:FeedbackRecord` — composed via `feedback_id` string FK, NEVER imported)

**Operator-action-handoff:** 5 平台 API keys 配置后激活;v9.0 提供 schema + adapter 骨架 + CLI 仪表盘 + 本文档 only。V9-FUTURE-01 deferred。

---

## 1. 概述 / Overview

Phase 42 DATA closes the 创意→生产→分发→反馈 loop:把分发后平台返回的完播率 / 卡点跳出率 / 互动率 / 收藏率 / 评论率 等指标,接回 `plugins/formula_library/`,作为下一集 Step 0 lookup 的调优信号。

**v9.0 deliverable scope:**
- ✅ `PlatformMetrics` + `FeedbackRecordExtension` + `TuningSuggestion` Pydantic schemas(Plan 42-01)
- ✅ 5 平台 adapter 骨架(douyin / kuaishou / weixin_video / xiaohongshu / bilibili),env_key 激活,fetch() 在 live HTTP 路径上 raise `NotImplementedError`(Plan 42-02)
- ✅ `tuning_loop.py` + `library_writer.py` + JSONL 审核队列(Plan 42-03)
- ✅ `hermes formula stats` CLI 仪表盘 + 本文档(Plan 42-04)

**V9-FUTURE-01 deferred:** Live platform API ingestion — operator 配置 5 个 API keys 后 adapter 激活,但实际的 live HTTP 调用 + response schema 校验 + retry/backoff 由 V9-FUTURE-01 实现。

---

## 2. 数据流架构 / Data Flow Architecture

```
[Step 13 master.mp4]
        ↓
[Step 14 variants[]]                 (Phase 38 SLICE — 7 per-platform variants)
        ↓
[Platform upload — operator-side]
        ↓
[Platform API] ──(adapter)──▶ [PlatformMetrics] ──(extension)──▶ [FeedbackRecordExtension]
        │                                                                  ↓
        │                                              [tuning_loop] ◀─── (feedback_id FK)
        │                                                      ↓
        │                                  [JSONL queue (pending)] under
        │                                  <HERMES_HOME>/skills/.feedback/tuning/
        │                                                      ↓
        │                                          [operator approve]
        │                                                      ↓
        │                                  [library_writer.apply_suggestion]
        │                                                      ↓
        │                                  [formula_library/library/*.json:eval_score updated]
        │                                                      ↓
        └──────────────────────────────────────▶ [Step 0 formula_lookup — next episode]
```

### Node-by-node explanation

| Node | Implementation | Phase |
|------|----------------|-------|
| `Step 13 master.mp4` | V8.6 主线 Step 13 `final-audit + final-delivery` 产出 | Phase 36 |
| `Step 14 variants[]` | `references/platform-master-slicing.md` 7-variant 算法 + 4 决策点 | Phase 38 |
| Platform upload | Operator 在 5 个平台上传 variants — operator-side,非自动化 | (manual) |
| Platform API | 平台开放接口(douyin/kuaishou/bilibili OAuth2;weixin_video/xiaohongshu cookie-based) | V9-FUTURE-01 |
| adapter | `plugins/platform_metrics/adapters/{douyin,kuaishou,...}.py` — `BasePlatformAdapter` 子类 | Plan 42-02 |
| `PlatformMetrics` | `plugins/platform_metrics/schema.py:PlatformMetrics` — 5 metrics clamped [0.0, 1.0] | Plan 42-01 |
| `FeedbackRecordExtension` | `plugins/platform_metrics/schema.py:FeedbackRecordExtension` — 通过 `feedback_id` 字符串外键组合 WITH v6.0 `FeedbackRecord`(Option A — 不 import FeedbackRecord 类) | Plan 42-01 |
| `tuning_loop` | `plugins/platform_metrics/tuning_loop.py:run_tuning_loop()` — 扫描 extensions → 按 MetricTrigger 规则分类 → emit TuningSuggestion 到 JSONL 队列 | Plan 42-03 |
| JSONL queue | `<HERMES_HOME>/skills/.feedback/tuning/{queue,applied,rejected}.jsonl` — mirror v6.0 EVOL-02 pattern | Plan 42-03 |
| `library_writer` | `plugins/platform_metrics/library_writer.py:apply_suggestion()` — 原子写入 `formula_library/library/*.json:eval_score` | Plan 42-03 |
| `Step 0 formula_lookup` | 下一集 Step 0 `plugins/formula_library/lookup.py:lookup_formulas()` 读取更新后的 eval_score 作为 ranking 信号 | Phase 39 |

---

## 3. Schema 引用 / Schema Reference

完整 Pydantic 源码见 `plugins/platform_metrics/schema.py`。此处仅列字段摘要:

### PlatformMetrics (DATA-01)
```python
class PlatformMetrics(BaseModel):
    platform: Literal["douyin", "kuaishou", "weixin_video",
                      "xiaohongshu", "bilibili", "红果", "视频号"]
    variant_id: str                      # FK to variants[].source_master_hash
    completion_rate: float               # 完播率    [0.0, 1.0]
    hook_dropoff_rate: float             # 卡点跳出率 [0.0, 1.0]
    engagement_rate: float               # 互动率    [0.0, 1.0]
    save_rate: float                     # 收藏率    [0.0, 1.0]
    comment_rate: float                  # 评论率    [0.0, 1.0]
    fetched_at: datetime                 # tz-aware ISO 8601
```

### FeedbackRecordExtension (DATA-02 — Option A composition)
```python
class FeedbackRecordExtension(BaseModel):
    feedback_id: str                     # STRING FK to v6.0 FeedbackRecord.record_id
    platform_metrics: dict[str, PlatformMetrics] = {}  # default empty (backward-compat)
    ts_created: datetime                 # tz-aware
```

**Scope discipline (load-bearing):** `FeedbackRecordExtension` NEVER imports `agent.feedback_schema.FeedbackRecord`。组合通过 `feedback_id` 字符串外键实现 — v6.0 `FeedbackStore` 拥有原始 record,本 extension 是 sibling document。两条 grep 测试在 test-time 强制此 invariant。

### TuningSuggestion (DATA-03 — JSONL queue record)
```python
class TuningSuggestion(BaseModel):
    suggestion_id: str                   # f"{formula_id}_{trigger}_{ts_unix}"
    formula_id: str                      # FK to formula_library/library/*.json
    trigger: MetricTrigger               # 4-value enum (see §5)
    observed_metric: float
    threshold: float
    suggested_action: str                # 中文为主
    rationale: str
    evidence: list[str] = []             # feedback_ids + variant_ids
    status: Literal["pending", "applied", "rejected"] = "pending"
    ts_queued: str                       # ISO 8601 UTC
    # Optional status-transition metadata
    commit_sha: str | None = None        # set when status == "applied"
    ts_applied: str | None = None
    reason: str | None = None            # set when status == "rejected"
    ts_rejected: str | None = None
```

---

## 4. 5 平台 Adapter 详情 / Platform Adapter Details

每个 adapter 是 `BasePlatformAdapter` 的子类,通过 `register_adapter(name, cls)` 在 module import 时自注册到 `ADAPTER_REGISTRY`。

### 4.1 抖音开放平台 (DouyinOpenAdapter)
- **Auth model:** OAuth2 (`client_credentials` grant)
- **env_key:** `DOUYIN_API_KEY`
- **Planned endpoints (V9-FUTURE-01):**
  - `OAUTH_TOKEN_URL = "https://open.douyin.com/oauth/client_token/"`
  - `VIDEO_DATA_URL = "https://open.douyin.com/video/data/"`
- **v9.0 status:** `fetch()` raise `NotImplementedError`(V9-FUTURE-01 message + endpoint URL)
- **Quirks:** rate limit 分级(500/小时 默认),scope 需要 `video.data.r`

### 4.2 快手开放平台 (KuaishouOpenAdapter)
- **Auth model:** OAuth2 (`access_token` from app_id + app_secret)
- **env_key:** `KUAISHOU_API_KEY`
- **Planned endpoints (V9-FUTURE-01):**
  - `OAUTH_TOKEN_URL = "https://open.kuaishou.com/oauth2/access_token"`
  - `VIDEO_DATA_URL = "https://open.kuaishou.com/openapi/video_data/get"`
- **v9.0 status:** `fetch()` raise `NotImplementedError`
- **Quirks:** token 1 小时过期,需 refresh

### 4.3 视频号 (WeixinVideoAdapter)
- **Auth model:** cookie-based(无官方开放 API;V9-FUTURE-01 使用创作者后台 cookie)
- **env_key:** `WEIXIN_VIDEO_API_KEY`
- **Planned endpoint (V9-FUTURE-01):**
  - `CREATOR_BASE_URL = "https://channels.weixin.qq.com"`
- **v9.0 status:** `fetch()` raise `NotImplementedError`
- **Quirks:** cookie 一周左右过期 → operator 需手动轮换。V9-FUTURE-01 应实现 cookie 失效检测 + 通知 operator 的机制。

### 4.4 小红书薯条 (XiaohongshuShutiaoAdapter)
- **Auth model:** cookie-based(薯条推广后台)
- **env_key:** `XIAOHONGSHU_API_KEY`
- **Planned endpoint (V9-FUTURE-01):**
  - `CREATOR_BASE_URL = "https://creator.xiaohongshu.com"`
- **v9.0 status:** `fetch()` raise `NotImplementedError`
- **Quirks:** 同 weixin_video,cookie 轮换。小红书无官方 metrics API — V9-FUTURE-01 必须 scrape 创作者后台( brittle,需 operator 监控)。

### 4.5 B 站创作者 (BilibiliCreatorAdapter)
- **Auth model:** OAuth2 (`client_credentials`)
- **env_key:** `BILIBILI_API_KEY`
- **Planned endpoints (V9-FUTURE-01):**
  - `OAUTH_TOKEN_URL = "https://member.bilibili.com/x/oauth2/access_token"`
  - `VIDEO_ANALYSIS_URL = "https://member.bilibili.com/x/web/data/video_analysis"`
- **v9.0 status:** `fetch()` raise `NotImplementedError`
- **Quirks:** 完播率字段需要 BV→CID 双查询;B 站 API 返回 nested JSON

---

## 5. Metric 触发规则 / Metric Trigger Rules

`tuning_loop.classify_metrics()` 应用以下 4 个 MetricTrigger 规则。阈值通过 `TuningThresholds` 参数化(默认值如下),operator 可调:

| Trigger | Threshold (default) | 含义 | Suggested Action |
|---------|---------------------|------|------------------|
| `HIGH_HOOK_DROPOFF` | `hook_dropoff_rate > 0.20` | 卡点跳出率高 — opening hook 没留住观众 | 加 hook 强度:升级 `hook_pattern` 从 `contrast` → `emotional_peak`;前 3 秒加矛盾 |
| `HIGH_COMPLETION_LOW_ENGAGEMENT` | `completion_rate >= 0.70 AND engagement_rate < 0.05` | 看完但不互动 — 缺 CTA / 情感 payoff | 加结尾 CTA(号召关注 + 评论);加 emotional callback 收束 |
| `LOW_COMPLETION` | `completion_rate < 0.30` | 完播率低 — 整体节奏问题 | 前置冲突(前 3 秒加矛盾);压缩铺垫;提升 卡点 密度 |
| `LOW_SAVE_RATE` | `save_rate < 0.01` | 收藏率低 — 内容缺可保存价值 | 加 collectible 钩子(列表、教程、彩蛋、关键术语卡) |

**阈值参数化:** `TuningThresholds` 是 `@dataclass(frozen=True)`,所有 4 个阈值都可独立 override。默认值经过 5-平台 公开数据调研 + 短剧行业 baseline 校准。

---

## 6. JSONL Queue 生命周期 / JSONL Queue Lifecycle

Mirror v6.0 `agent/evolution/queue.py:PatchRecord` 模式。3 个 JSONL 文件 under `<HERMES_HOME>/skills/.feedback/tuning/`:

| 文件 | 含义 | 写入者 |
|------|------|--------|
| `queue.jsonl` | pending TuningSuggestion 记录(每行 1 个 JSON 对象) | `tuning_loop.run_tuning_loop()` append |
| `applied.jsonl` | applied 记录 + `commit_sha`(apply commit 的 git SHA) | `move_suggestion(pending→applied)` 原子 rewrite + append |
| `rejected.jsonl` | rejected 记录 + `reason` | `move_suggestion(pending→rejected)` 原子 rewrite + append |

**Operator workflow:**
1. `hermes formula stats` → 看 pending 数量
2. `hermes formula stats --json` → 程序化读取
3. (v9.0) operator 用 Python API 审阅 + approve:
   ```python
   from plugins.platform_metrics.library_writer import apply_suggestion
   apply_suggestion(suggestion_id="<id>", tuning_dir=..., library_dir=...)
   ```
4. (V9-FUTURE) `hermes formula approve <suggestion_id>` CLI 子命令

**HIL invariant(load-bearing):** NOTHING 自动 apply。Operator 必须显式 approve — mirror v6.0 EVOL-02 模式。这避免了"指标噪声触发 formula 漂移"的事故路径。

---

## 7. Dashboard 使用 / Dashboard Usage

### Rich mode(默认)
```bash
hermes formula stats
```
输出 2 个 rich 表:

```
                       Formula Library Overview
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━┓
┃ Formula ID                 ┃ Genre    ┃ Mood   ┃ Pacing   ┃ Eval  ┃ # Pending ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━┩
│ urban-fantasy-light-01     │ 都市奇幻 │ 轻喜剧 │ fast-cut │ 0.85  │         0 │
│ urban-fantasy-angst-01     │ 都市奇幻 │ 虐心   │ mid-temp │ 0.78  │         0 │
│ ...                                                                              
└────────────────────────────┴──────────┴────────┴──────────┴───────┴───────────┘

                       Tuning Queue Summary
┏━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Status   ┃ Count ┃ Notes                                 ┃
┡━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ pending  │     0 │ awaiting operator review              │
│ applied  │     0 │ eval_score written back to formula_…  │
│ rejected │     0 │ operator declined with reason         │
└──────────┴───────┴───────────────────────────────────────┘
```

### JSON mode(`--json`)
```bash
hermes formula stats --json | jq .
```
输出 counts-only JSON(无 ANSI escape codes,适合脚本):

```json
{
  "formulas": [
    {"formula_id": "urban-fantasy-light-01", "genre": "都市奇幻",
     "mood": "轻喜剧", "pacing": "fast-cut", "eval_score": 0.85},
    ...
  ],
  "queue": {"pending": 0, "applied": 0, "rejected": 0}
}
```

### 与 monitoring stack 集成
JSON 模式可以直接 pipe 到 `jq` / `prometheus-textfile` / `grafana` 等。示例 cron:

```bash
# 每 10 分钟快照 queue 深度到 prometheus textfile collector
*/10 * * * * hermes formula stats --json \
    | jq '.queue | "formula_tuning_pending \(.pending)\nformula_tuning_applied \(.applied)\nformula_tuning_rejected \(.rejected)"' \
    > /var/lib/node_exporter/textfile/formula_tuning.prom
```

---

## 8. Operator Setup (5 平台 API keys)

Step-by-step for each platform:

### 通用步骤(每个平台)
1. 注册开发者账号 at the platform's developer portal(见下表)
2. Create an app / obtain credentials(app_id + app_secret OR cookie string)
3. 在 `~/.hermes/.env` 中设置 env var — 取消 `.env.example` 中对应行的注释 + 填入实际 token
4. 重启 hermes(或 gateway)
5. 验证激活:运行 `python3 -c "from plugins.platform_metrics.adapters.base import get_adapter; print(get_adapter('douyin').is_activated())"`
6. (V9-FUTURE-01) 配置 live API 访问 — 实现每个 adapter 的 live HTTP path,跑 smoke test with real variant_id

### 平台特定入口

| Platform | Developer Portal | Auth Model | env_key |
|----------|------------------|------------|---------|
| douyin | https://developer.open-douyin.com | OAuth2 | `DOUYIN_API_KEY` |
| kuaishou | https://open.kuaishou.com | OAuth2 | `KUAISHOU_API_KEY` |
| weixin_video | https://channels.weixin.qq.com (creator backend) | cookie | `WEIXIN_VIDEO_API_KEY` |
| xiaohongshu | https://creator.xiaohongshu.com | cookie | `XIAOHONGSHU_API_KEY` |
| bilibili | https://member.bilibili.com (creator platform) | OAuth2 | `BILIBILI_API_KEY` |

### Cookie 轮换(weixin_video + xiaohongshu)
cookie-based 平台 cookie 约 1 周过期。Operator 需要:
1. 监控 `hermes formula stats` 中 adapter 状态(V9-FUTURE 会加 `--adapters` flag 显示激活/失效)
2. cookie 失效后,登录创作者后台,提取新 cookie,更新 `~/.hermes/.env`
3. 重启 hermes

V9-FUTURE-01 计划实现 cookie 失效自动检测 + operator 通知(通过 `hermes` 通知系统)。

---

## 9. Scope discipline (Option A)

**为什么 Phase 42 不修改 `agent/feedback_schema.py`?**

`agent/feedback_schema.py:FeedbackRecord` 是 v6.0 核心数据契约,已被 `agent/feedback_store.py`、`agent/evolution/queue.py`、多个 v6.0 phase 依赖。直接修改它会:
1. 破坏 v6.0 backward-compat 承诺(已 shipped milestone)
2. 引入难以定位的回归风险
3. 违反 v9.0 PROJECT.md 的 scope 约束("仅 skills/ + 新 plugin plugins/formula_library/,不碰 Hermes 核心 Python/JS 代码")

**Option A 决策(STATE.md + PLAN.md 记录):**
- 新建 `plugins/platform_metrics/` plugin
- 新建 `FeedbackRecordExtension` Pydantic model,通过 `feedback_id` 字符串外键组合 WITH v6.0 `FeedbackRecord`
- `FeedbackRecordExtension` NEVER imports `agent.feedback_schema.FeedbackRecord` 类 — 它是 sibling document,通过字符串 FK 关联
- v6.0 `FeedbackStore` 拥有原始 record;extension 存在单独路径 `<HERMES_HOME>/skills/.feedback/platform_metrics/`

这个决策让 Phase 42 完全独立于 v6.0 milestone,可独立测试、独立 ship、独立回滚。Phase 43 VALIDATE 会 grep-enforce 此 invariant。

---

## 10. See Also

- [`platform-master-slicing.md`](./platform-master-slicing.md) — Phase 38 variants[] 源算法 + 4 决策点
- [`asset-bus-schema.md`](./asset-bus-schema.md) — variants[] 字段 schema + AssetBus envelope 规则
- [`pipeline-dag.md`](./pipeline-dag.md) — Step 14 + Step 15 additive annotation rows
- [`ltx2-preview-loop.md`](./ltx2-preview-loop.md) — Phase 41 Step 6.5 fast-preview 阈值
- [`_shared/v6-feedback-loop-architecture.md`](../movie-experts/_shared/v6-feedback-loop-architecture.md) — v6.0 FeedbackStore 架构(public API consume-only)
- `plugins/formula_library/README.md` — formula_library plugin 文档
- `plugins/platform_metrics/README.md` — platform_metrics plugin 文档(本 plugin)
- `.planning/PROJECT.md` — v9.0 scope discipline 约束(source of Option A decision)
- `.planning/STATE.md` — Phase 42 决策记录

---

## LICENSE Note

本文档是 Hermes Agent 原创文档,无第三方版权素材引用。所有平台 API endpoint URLs 是公开开发者文档引用(fair use),非代码抄录。Metric 阈值基于公开短剧行业 baseline 校准,非机密数据。

---

*Phase 42 DATA — Plan 42-04 — Created: 2026-06-27 — Operator-action-handoff: V9-FUTURE-01 tracks live API ingestion.*
