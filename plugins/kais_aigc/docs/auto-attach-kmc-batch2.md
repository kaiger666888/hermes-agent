# auto-attach KMC 消费端 — 批次2 交付文档 (2026-09-28)

> 工单: `/data/workspace/auto-attach-kmc-workorder.md`（批次2：KMC 侧 camera_move →
> auto_attach 消费端）。基线 commit `b4d589e5`（建树时 HEAD，写死）。批次1（KAP 仓
> `8c794fcf`）已上库，本批是它的 KMC 消费端，纯本仓改动。

## 0. 摘要

KMC 渲染引擎 `H3VideoEngine` 在**无显式 h3_lora 配置**时，把 P09 中文运镜意图
（crash_zoom 族白名单，4 键）解析为 KAP trigger 语义，经 multipart `camera_move`
字段透传 KAP；由批次1 的 registry `auto_attach.trigger === "camera_move:<trigger>"`
查表自动挂载 production LoRA（首例 crash-zoom@0.8）。优先级 **显式 lora >
auto_attach > 无 LoRA**；装配任何失败由 KAP 侧降级 prompt-only 继续渲染，引擎侧
零 fail-loud。未命中意图的 shot multipart 与改动前逐字节等价。

## 1. 改动清单

| 文件 | 性质 | 内容 |
|---|---|---|
| `plugins/kais_aigc/camera_move_intent.py` | 新增 | 意图映射层：`CAMERA_MOVE_TRIGGERS`（4 键白名单，每键注释映射理由）+ `resolve_camera_move_trigger`（纯函数，无 raise 路径） |
| `plugins/kais_aigc/video_engine.py` | 修改（2 处，最小侵入） | ① 顶部 import `resolve_camera_move_trigger`（同 `tools.py`/`canvas_sync.py` 的包内绝对导入先例）；② `_build_multipart` lora 装配段之后、blockCache 之前加 `if lora is None:` 意图分支（append `camera_move` + 一条 INFO 日志）。**未碰** `_route_lora`/`_resolve_vdn`/rh/final-shot 路由族（红线1） |
| `plugins/kais_aigc/tests/test_camera_move_intent.py` | 新增 | 46 测试：映射表契约（4）/ resolve 解析（约 30，参数化）/ `_build_multipart` 集成（6） |
| `plugins/kais_aigc/docs/auto-attach-kmc-batch2.md` | 新增 | 本文档 |

## 2. 语义

### 2.1 映射表（宁缺毋滥的落点）

| 键（中文枚举） | 564 镜频次 | → trigger | 理由 |
|---|---|---|---|
| 变焦推 | 31 | crash_zoom | 「冲向镜头」字面对应，crash_zoom 名义主项 |
| 快速推进 | 18 | crash_zoom | 推近+快速 = 冲击感推近族正成员（r6 定谳增益域） |
| 快速拉远 | 1 | crash_zoom | 反向冲击（whip-out），冲击感运镜两向同享 |
| 甩镜 | 2 | crash_zoom | whip-pan 高速甩动，冲击感运镜族横移近亲 |

**刻意不收**（工单红线4，测试逐项钉死）：固定/手持/跟随/缓慢推进/缓慢拉远/
上仰/下俯/环绕/斯坦尼康/平稳跟随/推移——日常运镜 prompt 本来就能执行，挂 LoRA
反而引入风格漂移。词表边界内另有三态不收，理由：`变焦拉`(3)/`变焦拉远`(3) 是
**无速度限定词**的拉出（同「缓慢拉远」口径，不收），`推移`(2) 是缓推语义——
凡拿不准的一律不收，等 KAP 侧盲测定谳后再扩表（扩表标准：确定语义 + 逐键补
理由注释 + 同步 `test_keys_are_exact_whitelist` 断言）。

### 2.2 resolve 契约（`camera_move_intent.py`）

- 字段口径：`camera_move`（P09 L2 产出口径）优先，`camera_movement` 旧拼写
  or-兜底（同形先例 `p09_shot_breakdown.py:946`）。
- **精确匹配**，无模糊/包含/去空白逻辑——模糊匹配会把「缓慢推进」误升级成
  crash_zoom，正是决策律要防的事（测试 `test_no_fuzzy_matching` 钉死）。
- 空 shot / 非 dict / 空/非 str 值 / 未命中 → 一律 None。纯函数：不改入参、
  不读盘、不打日志、无 raise 路径。

### 2.3 装配契约（`video_engine.py::_build_multipart`）

- **快路径跳过**：`lora is None`（= render() 侧 `_route_lora` 未命中显式配置）
  才解析意图——显式 > 自动，也省一次查表。显式在场时即使 camera_move 命中也
  **不发**该字段（测试 `test_explicit_lora_suppresses_camera_move`）。
- **位置**：紧邻既有 lora 三字段 append 之后、blockCache 之前（同族字段同一
  装配区，仿 blockCache 追加先例）。
- **不发未命中**：trigger 为 None 时 multipart 与改动前逐字节等价（红线，
  同 test_video_engine_lora T1 口径；基线字段序列锚在测试 `LEGACY_NAMES`）。
- 日志一条：`h3_engine: %s camera_move=%s → auto_attach trigger（装配失败由
  KAP 侧降级）`。

## 3. 边界披露

1. **`_route_lora` 返回 None 的两义性**：无显式配置，或 registry 读不了但显式
   配置在场。后者按工单 C2 字面 gate（None 即走 auto 路径）仍会评估意图——
   此时引擎未发任何 lora 字段，KAP 侧「显式 > auto_attach」按字段在场与否
   裁决，auto 生效。该 edge 已在 `_route_lora` loader 侧打过 warning，不新增
   日志。
2. **无臂门控**：vdn/rh/final-shot 臂上 camera_move 照发（红线1——引擎侧臂
   判定只服务于显式 lora 预检，不外溢到 auto 路径）。装配可行性归 KAP 侧
   降级（工单 §0 契约：条目不在/overlay 条目/引擎不可见 = prompt-only，绝不
   400、绝不 fail 镜）。测试 `test_no_arm_gating_vdn_profile_still_forwards`
   钉住该口径。
3. **异常路径零 fail-loud 的实现方式**：resolve 是纯函数（isinstance 守卫 +
   dict.get），被证明无 raise 路径，故装配分支**刻意不包 try/except**——
   不可证伪的死代码不写（红线3 的「异常路径一律降级」由函数构造保证而非
   捕获保证）。
4. **运行口径自纠偏（工单 §2 预留条款的兑现）**：工单命令2 原文在
   `plugins/kais_aigc` 目录起跑，实测结构性 collection error，且**既有套件
   同病**（test_qwen_eye / test_canvas_graph 等同目录同报错，非本批引入）。
   三层机理：① 本机 venv（hermes-agent/.venv）带 hermes-agent editable 安装，
   `plugins` 命名空间落到 `/data/workspace/hermes-agent` 拷贝；② pytest 以
   `kais_aigc.tests.*` 包路径导入测试 → `kais_aigc/__init__.py` → `tools.py`
   → `from tools.registry import ...` 被 **cwd 的 tools.py 文件**（顶级名
   `tools` 的模块遮蔽）顶炸；③ 模块级 sys.path 自举在 `__init__` 之后执行，
   救不了，修 conftest / `__init__` 均越本批白名单。**修正口径：仓根起跑**
   （§6 命令2'）。新套件自带仓根自举，从任何不遮蔽 `tools` 的 cwd 起跑均
   解析到本仓拷贝。
5. **基线命令1 的实测对象**：skills/kais-movie-pipeline 目录起跑时
   `import plugins.kais_aigc` 落 hermes-agent 侧拷贝（与 b4d589e5 的本仓
   video_engine.py `diff` SAME）——命令1 实测的是那份同内容拷贝。为闭环
   另跑仓根口径 35 passed（真正测改动后代码）；且新套件 46 passed 本身即是
   canary：若仓根口径也落到 hermes 未接线拷贝，camera_move 字段断言必挂。
6. **生产行为（operator 割接时实测勘误，推翻本条初版「vendored 拷贝」论）**：
   hermes-agent 侧 `plugins/kais_aigc` 实为 **symlink → 主仓 checkout**
   （`/home/kai/workspace/kais-hermes-skills` → `/data/workspace/kais-hermes-skills`）。
   即：**merge 进主仓 = 运行时立即生效**，不存在 vendored 同步步骤；
   hermes-agent 路径是链接勿当拷贝改。初版判断依据（venv import 解析到
   hermes-agent 路径）正确，但把链尾误读了拷贝——`readlink -f` 即证。

## 4. operator 割接序列

1. merge 本分支（单 commit，收割归 operator；工单红线5：本批未 push）。
2. 本仓是 Python 源仓：**管线进程按需重启即生效**（module import 时读）。
3. hermes-agent 侧若走 venv editable 数据流：同步整个 `plugins/kais_aigc/`
   目录（含新增 `camera_move_intent.py`；缺文件 = ImportError，同步粒度必须
   整目录），随后重启管线进程。
4. **生产自证（建议下一轮 P11b 批）**：挑 camera_move ∈ 白名单的镜头渲染，
   KAP 日志查 auto_attach 挂载行（`trigger=camera_move:crash_zoom` 挂
   crash-zoom@0.8）；同批抽查日常运镜镜头确认无 camera_move 字段发出
   （引擎日志无 `auto_attach trigger` 行）。
5. 回滚：revert 单 commit 即可——未命中路径本就逐字节等价，回滚零迁移成本。

## 5. 设计律四条执行自检表（工单 §0）

| 设计律 | 执行点 | 证据 |
|---|---|---|
| prompt 先行 | 意图只透传 trigger 语义，prompt 照发；日常运镜（prompt 可执行）不入表 | 映射表仅 4 键；`test_daily_moves_excluded` |
| LoRA 按需升格 | 仅 crash_zoom 族确定语义才升格，宁缺毋滥 | `test_keys_are_exact_whitelist` + 每键理由注释 |
| 显式配置永远最高优先 | `lora is None` gate：显式 h3_lora 在场跳过意图解析、不发 camera_move | `test_explicit_lora_suppresses_camera_move` |
| 装配失败降级不致命 | 引擎侧纯函数无 raise、未命中逐字节等价；装配失败归 KAP 降级 prompt-only | `test_non_string_values_return_none` / `test_miss_keeps_legacy_field_sequence` / 日志文案「装配失败由 KAP 侧降级」 |

## 6. 验收实测（2026-09-28，本 worktree `wt/auto-attach-kmc`）

```
# 命令1（工单原文口径，skills 目录 —— 实测对象为 hermes 同内容拷贝，见 §3.5）
cd skills/kais-movie-pipeline && python3 -m pytest tests/test_video_engine_lora.py -q
→ 35 passed

# 命令1'（仓根口径 —— 真正测改动后代码的零回归）
python3 -m pytest skills/kais-movie-pipeline/tests/test_video_engine_lora.py -q
→ 35 passed

# 命令2'（自纠偏口径；工单原文 plugins/kais_aigc 目录起跑见 §3.4）
python3 -m pytest plugins/kais_aigc/tests/test_camera_move_intent.py -q
→ 46 passed

# 命令3
python3 -m py_compile plugins/kais_aigc/camera_move_intent.py plugins/kais_aigc/video_engine.py
→ 零输出（通过）

# 命令4
git diff --name-only b4d589e5..HEAD
→ 恰为白名单 4 文件（本批单 commit，无夹带；建树时 git status 干净，无 M 态存量）
```
