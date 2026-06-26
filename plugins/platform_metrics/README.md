# platform_metrics plugin

**Phase 42 DATA — 数据收敛 (Step 15) plugin scaffold.**

Platform performance metrics (完播率 / 卡点跳出率 / 互动率 / 收藏率 / 评论率)
flow back from 5 short-drama platforms into a v6.0 FeedbackStore-compatible
sidecar, with a formula tuning loop that proposes `plugins/formula_library/`
improvements and a `hermes formula stats` CLI dashboard for inspection.

---

## Scope Discipline — Option A (load-bearing)

v9.0 PROJECT.md mandates: **"仅 skills/kais-movie-pipeline/ +
skills/movie-experts/ + 新 plugin plugins/formula_library/, 不碰 Hermes
核心 Python/JS 代码"**. Phase 42 has a structural tension: DATA-02 calls
for "FeedbackRecord gains a `platform_metrics` field", but
`agent/feedback_schema.py` (where `FeedbackRecord` lives) IS Hermes core.

**Decision (Option A — applied here):** This new plugin
`plugins/platform_metrics/`:

- Owns the `PlatformMetrics` Pydantic schema (DATA-01)
- Owns a `FeedbackRecordExtension` Pydantic model that **composes with**
  the v6.0 `FeedbackRecord` via a `feedback_id` string FK (DATA-02) — does
  NOT modify `FeedbackRecord` itself. The v6.0 schema remains untouched
  (READ ONLY).
- Owns the 5 platform adapter stubs (DATA-01)
- Owns `formula_tuning_loop` (DATA-03) — reads from existing v6.0
  `FeedbackStore` via **public API only** (`query()`, `summary()`,
  `get_record()`)
- Owns the `hermes formula stats` CLI subcommand (DATA-04) — registered
  via `ctx.register_cli_command(name="formula", ...)`

**Forbidden touchpoints (READ ONLY):**

- `agent/feedback_schema.py` (v6.0 core)
- `agent/feedback_store.py` (v6.0 core)
- `agent/evolution/queue.py` (v6.0 core; consume-only via public API)
- `hermes_cli/main.py` (Hermes core CLI)

---

## DATA-01..04 Requirement Mapping

| Req | Description | Plan |
|-----|-------------|------|
| **DATA-01** | 5 平台 API adapter 骨架 (抖音 / 快手 / 视频号 / 小红书薯条 / B 站创作者) + unified `PlatformMetrics` schema | 42-01 (schema + base class) + 42-02 (5 stubs) |
| **DATA-02** | `FeedbackRecordExtension` composes via `feedback_id` FK + `platform_metrics` per-platform bucketed (additive, v6.0 backward-compat) | 42-01 (composition) |
| **DATA-03** | `formula_tuning_loop` + JSONL review queue + `library_writer` (operator approve → formula_library write-back) | 42-03 |
| **DATA-04** | `hermes formula stats` rich tables + `references/data-convergence.md` + SKILL.md Step 15 + `.env.example` patch | 42-04 |

---

## Directory Layout

```
plugins/platform_metrics/
├── plugin.yaml              # Manifest (kind: standalone, provides_tools: [])
├── __init__.py              # register(ctx) entrypoint (no-op in Plan 01)
├── schema.py                # PlatformMetrics + FeedbackRecordExtension + TuningSuggestion (Plan 01)
├── README.md                # This file (bilingual)
├── adapters/
│   ├── __init__.py          # ADAPTER_REGISTRY + register_adapter helper (Plan 01)
│   ├── base.py              # BasePlatformAdapter ABC + AdapterNotActivatedError + get_adapter (Plan 01)
│   ├── douyin.py            # 抖音开放平台 OAuth2 stub (Plan 42-02)
│   ├── kuaishou.py          # 快手开放平台 OAuth2 stub (Plan 42-02)
│   ├── weixin_video.py      # 视频号 cookie-based stub (Plan 42-02)
│   ├── xiaohongshu.py       # 小红书薯条 cookie-based stub (Plan 42-02)
│   └── bilibili.py          # B 站创作者 OAuth2 stub (Plan 42-02)
├── tuning_loop.py           # MetricTrigger → TuningSuggestion engine (Plan 42-03)
├── library_writer.py        # Atomic write-back to formula_library (Plan 42-03)
├── queue.py                 # JSONL review queue (mirror agent/evolution/queue.py) (Plan 42-03)
├── cli.py                   # `hermes formula stats` subcommand (Plan 42-04)
└── tests/
    ├── __init__.py
    ├── test_plugin_registration.py  # Plan 01 Task 1
    ├── test_schema.py               # Plan 01 Task 2
    └── test_adapter_base.py         # Plan 01 Task 3
```

---

## Operator-Action-Handoff

5 platform API keys 由 operator 配置后激活 (`~/.hermes/.env`):

| Platform | Env Var | Auth Model | Documented |
|----------|---------|-----------|------------|
| 抖音开放平台 | `DOUYIN_API_KEY` | OAuth2 (client_credentials) | Plan 42-04 `.env.example` |
| 快手开放平台 | `KUAISHOU_API_KEY` | OAuth2 | Plan 42-04 `.env.example` |
| 视频号 | `WEIXIN_VIDEO_API_KEY` | cookie-based (no public OAuth2) | Plan 42-04 `.env.example` |
| 小红书薯条 | `XIAOHONGSHU_API_KEY` | cookie-based | Plan 42-04 `.env.example` |
| B 站创作者 | `BILIBILI_API_KEY` | OAuth2 | Plan 42-04 `.env.example` |

Without the env var → `AdapterNotActivatedError` (clean failure mode).
With the env var → adapter activates; live HTTP path raises
`NotImplementedError` until V9-FUTURE-01 (live ingestion deferred).

---

## V9-FUTURE-01 Deferral

Live platform API data ingestion (real HTTP calls returning real metrics)
is explicitly deferred to V9-FUTURE-01. v9.0 ships:

- The activation scaffold (env-key check)
- Schema validation (`PlatformMetrics` Pydantic)
- Adapter contract (`BasePlatformAdapter` ABC)
- Tuning loop logic (synthesizes suggestions from any `PlatformMetrics`
  input — works on live OR operator-pasted data)

When the operator obtains platform API access (app_id + app_secret for
OAuth2 platforms; cookie strings for cookie-based platforms), they remove
the `raise NotImplementedError(...)` line in each adapter's `fetch()` and
implement the `httpx.AsyncClient` call per the V9-FUTURE-01 pseudo-code
block documented in each stub file.

---

## Bilingual Notes / 双语说明

- 本 plugin 严格遵循 v9.0 scope discipline: **不修改 Hermes 核心 Python
  代码**。所有 v6.0 `FeedbackRecord` / `FeedbackStore` 的接触面通过公共
  API (`query()` / `summary()` / `get_record()`) 调用,只读不改。
- `FeedbackRecordExtension` 通过 `feedback_id` 字符串外键与 v6.0 记录组合
  (Option A 决策),v6.0 历史记录完全不受影响 (DATA-02 向后兼容)。
- Operator 配置 5 个平台 API key 后,adapter 自动激活;v9.0 不发布 live
  HTTP 调用,仅发布激活脚手架 + schema 校验 + tuning loop 引擎。
- V8.6 13-step 编号保留;Step 15 是 additive(SKILL.md body-only patch,
  Plan 42-04)。

---

*Plan 01 scaffold — 2026-06-27. Plan 02 (5 adapters) + Plan 03 (tuning
loop) + Plan 04 (CLI + ref) ship in Wave 1+2.*
