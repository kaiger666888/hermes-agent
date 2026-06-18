# dreamina CLI Baseline — kais-movie-agent V8.5+ Canonical Image/Video Tool

**Source:** kais-movie-agent V8.5 SKILL.md (commit `c22867d`, 2026-06-18) + V8.6 SKILL.md (commit `e41fa68`, 2026-06-18), both at `/data/workspace/kais-movie-agent/SKILL.md`. Primary source sections: §"V8.5 更新" + §"工具映射" + §"L1/L2 双参考角色一致性系统" + §"图片生成默认引擎" + §"关键文件" (jimeng-client.js deprecation).
**Copyright:** Fair Use — (1) dreamina CLI command signatures (command name + CLI flags + parameter values) are factual API surface of an external tool, not copyrightable expression; (2) the L1/L2/L3/L4 asset library strategy is an original Hermes Agent analytical encoding layer; (3) async poll pattern + gold-team fallback are factual integration descriptions of the open-source kais-movie-agent pipeline; (4) jimeng-client.js deprecation notice references the upstream project's own @deprecated annotation.
**Last-verified:** 2026-06-19
**verified_date:** 2026-06

---

## Summary

`dreamina` CLI 是 kais-movie-agent V8.5 起对**所有图片/视频生成**的唯一规范工具,取代废弃的 `jimeng-client.js`(后者在 `lib/` 中仅作兼容参考保留)。gold-team 容器不再处理图片生成 —— gold-team 现仅服务 video/TTS/3D;图片生成走 gold-team `image_draw` 只在即梦限流/超时降级时启用。

本 ref 是 hermes-agent 16 个 active movie-expert 的**跨专家共享知识基线**,所有需要发出"生成图片/视频"指令的专家(visual_executor drawer sub-step / character_designer / cinematographer / prompt_injector / audio_pipeline 的 multimodal2video audio binding 等)都必须按本基线的 6 个 CLI 子命令组装调用。

**This ref unblocks:** Phase 23 VISUAL-02(visual_executor dreamina CLI 集成)+ Phase 25 AUDIO-02(multimodal2video 音频绑定)+ Phase 27 INTEGRATION-01(canonical tool registry)。

---

## V-Version Provenance

| 版本 | commit | 关键变化 | 对本 ref 的影响 |
|------|--------|---------|---------------|
| V8.5 | `c22867d` (2026-06-18 22:17) | dreamina CLI 取代 jimeng-client.js;Step 7 角色资产库完整化(L1-L4);image2image 最多 10 张参考图 | **本 ref 主源** —— 6 个 CLI 签名 + L1-L4 策略均出自此版本 |
| V8.6 | `e41fa68` (2026-06-18 22:56) | 管线精简 25→13 步,审核门 12→8 个;Expert 调用 15→10 次 | dreamina CLI 工具地位不变;Step 编号更新(本 ref 的"何时使用"列已同步 V8.6 编号) |

---

## The 6 dreamina CLI Sub-Commands

下面 6 个子命令的签名**逐字转录**自 kais-movie-agent V8.5 SKILL.md §工具映射,不做改写。每个子命令附 CN 用途说明与 V8.6 Step 映射。

### dreamina text2image

```bash
dreamina text2image --prompt "..." --model_version 5.0 --ratio 16:9 --resolution_type 2k --poll 0
```

- **用途:** 文本生成图片(无参考图)
- **何时使用(V8.6 Step 映射):**
  - Step 4A 生成 L1 身份锚点候选(6 张选 1,黄金标准检测)
  - Step 5 场景俯视图 / 主视觉种子
  - Step 7 视觉种子生成(style_genome → visual_executor → prompt_injector → dreamina text2image)
- **关键参数:**
  - `--prompt` 文本提示(prompt_injector 组装的 dreamina-compatible model_prompts)
  - `--model_version 5.0` 当前推荐图片模型版本
  - `--ratio` 宽高比(16:9 / 9:16 / 3:4 / 1:1,根据短剧竖屏/横屏决定)
  - `--resolution_type 2k` 默认 2k;关键海报级可升 4k
  - `--poll 0` **必填** —— 不阻塞等待,立即返回 submit_id(详见 §Async Poll Pattern)

### dreamina image2image

```bash
dreamina image2image --images L1_face.png,L2_costume.png --prompt "..." --model_version 5.0 --ratio 3:4 --resolution_type 2k --poll 0
```

- **用途:** 图生图(基于参考图生成,核心角色一致性工具)
- **何时使用(V8.6 Step 映射):**
  - Step 4C 生成 L2 造型卡片(每套服装正面+侧面,各 3 变体 = 36 张候选)
  - Step 4E/4F 生成 L3 姿势包 / L4 表情标定
  - Step 5 场景侧面变体(基于 L1+L2 锁定角色,换场景)
- **关键参数:**
  - `--images` 参考图列表(逗号分隔,**最多 10 张**)—— L1+L2 双参考用法:第一张是 L1 面部锚点,第二张是 L2 服装/造型
  - 其他参数同 text2image
  - **重要:** V8.5 起 `image2image` 完全替代废弃的 jimeng-client.js `compositions()` API

### dreamina multimodal2video

```bash
dreamina multimodal2video --image L1_01.png --image L1_02.png --image scene.png --prompt "@Image1 provides identity..." --model_version seedance2.0fast --duration 5 --ratio 16:9 --poll 0
```

- **用途:** 全能参考视频生成(最强角色一致性,Seedance 2.0 omni_reference 模式)
- **何时使用(V8.6 Step 映射):**
  - Step 10 视频模式 B(全能参考)—— 需要多张 L1 身份锚点 + 场景图绑定时
  - 关键镜头(主角特写、情绪戏)首选此模式
- **关键参数:**
  - `--image` 多次重复传入(最多 9 图 + 3 视频 + 3 音频 per Seedance 2.0 spec)
  - `--prompt` 中用 `@Image1` `@Image2` `@Image3` 显式绑定身份("Image1 provides identity...")
  - `--model_version seedance2.0fast` 视频生成模型(快速版;质量版为 `seedance2.0`)
  - `--duration 5` 视频时长(秒,典型 5-10s)
  - **音频绑定:** `@Audio N` 语法(详见 Phase 25 audio_pipeline SKILL.md AUDIO-02)

### dreamina multiframe2video

```bash
dreamina multiframe2video --images frame1.png,frame2.png,frame3.png --transition-prompt "A to B" --transition-prompt "B to C" --poll 0
```

- **用途:** 多帧故事视频(关键帧之间生成过渡动画)
- **何时使用(V8.6 Step 映射):**
  - Step 10 视频模式 A(多帧故事)—— 多场景串联,帧间生成流畅过渡
  - 蒙太奇段落 / 时间跳跃场景
- **关键参数:**
  - `--images` 关键帧列表(逗号分隔,N ≥ 2)
  - `--transition-prompt` 每对相邻帧一个过渡描述(可多次重复)

### dreamina frames2video

```bash
dreamina frames2video --first ./start.png --last ./end.png --prompt "..." --model_version seedance2.0fast --duration 5 --poll 0
```

- **用途:** 首尾帧视频(给起始帧+结束帧,中间自动补帧)
- **何时使用(V8.6 Step 映射):**
  - Step 10 视频模式 C(首尾帧)—— 已知开始/结束画面,需中间过渡时
  - 简单镜头运动(推拉摇移,起止画面已确定)
- **关键参数:**
  - `--first` 起始帧
  - `--last` 结束帧
  - 其他参数同 multimodal2video

### dreamina image_upscale

```bash
dreamina image_upscale --image ./photo.png --resolution_type 4k --poll 0
```

- **用途:** 图片超分辨率(2k → 4k)
- **何时使用:** 任意 Step 需要超分时(关键海报 / 主视觉 / 高分辨率成片画面)
- **关键参数:**
  - `--image` 待超分图片
  - `--resolution_type 4k` 目标分辨率

---

## L1/L2/L3/L4 Character Asset Library Strategy

> 来源:kais-movie-agent V8.5 SKILL.md §"L1/L2 双参考角色一致性系统" + §"Step 7 角色资产库完整化"

V8.5 起,kais-movie-agent 角色一致性策略升级为**双参考系统 + 脸图分离**:角色一致性 80% 取决于参考图质量,20% 取决于提示词。4 层资产库 L1-L4 各自锁定的内容不同,API 入口也不同 —— **不可混放**。

### 4-Tier Asset Library

| 层级 | 名称 | 内容 | API 入口 | 用途 |
|------|------|------|---------|------|
| **L1** | 身份锚点 | 1-3 张面部/半身特写 | 角色参考 (Character Ref) | 锁定五官/骨相/发型/肤色,**永不更换** |
| **L2** | 造型卡片 | 每套服装全身正面+侧面 | 智能参考 (Smart Ref) | 锁定服装/道具/造型 |
| **L3** | 姿势包 | 坐/站/走/跑等姿态 | 智能参考 (Smart Ref) | 动作参考 |
| **L4** | 表情标定 | 微笑/怒/惊/泪 | 智能参考 (Smart Ref) | 表情戏时使用 |

### 核心原则 (Core Principles)

- **角色参考只传脸,智能参考传衣服/姿势. 不要混放!** —— L1(角色参考)只放面部/半身特写,L2/L3/L4(智能参考)才放服装/姿势/表情
- **prompt 零面部描述** —— 面部特征通过 L1 参考图传递,prompt 只写动作/场景/镜头(避免 prompt 与参考图冲突)
- **一造型一卡片** —— L2 一张卡片只对应一套服装,不混放多套服装(防止模型混淆)
- **L1 永不更换** —— 一旦审核通过注册到 CharacterAssetManager,L1 在整个项目内不变;L2/L3/L4 可按场景需要增补

### 参考图黄金标准 (Golden Standard for Reference Images)

L1 候选图必须满足以下标准,不合格需重生成(每轮 ≤ 3 张候选,Step 4A 流程):

- 光线柔和均匀(避免强烈阴影遮蔽五官)
- 正面微侧 < 30°(保留骨相信息)
- 中性表情(避免极端情绪锁死表情空间)
- 浅灰背景 `#D3D3D3`(减少背景干扰)
- 高清无滤镜(保留真实肤色/纹理)
- 无遮挡(无眼镜/口罩/手部遮挡五官)

### V8.6 Step Mapping (4 层资产在管线中的位置)

- **L1 → Step 4A:** `dreamina text2image` × 6 张候选 → 黄金标准检测 → 不合格重生 ≤ 3 轮 → 审核通过注册到 `CharacterAssetManager` 作为永久身份锚点
- **L2 → Step 4C:** `dreamina image2image --images L1.png` with 服装 prompt → 每套服装正面 + 侧面各 3 变体 = 36 张候选/套
- **L3 → Step 4E:** `dreamina image2image --images L1.png,L2.png` with 姿势 prompt(按需,动作戏前生成)
- **L4 → Step 4F:** `dreamina image2image --images L1.png,L2.png` with 表情 prompt(按需,表情戏前生成)

---

## Async Poll Pattern

> 来源:kais-movie-agent V8.5 SKILL.md §"图片生成默认引擎" §"dreamina CLI 用法"

所有 dreamina CLI 命令**必须使用 `--poll 0` 异步模式** —— 不阻塞等待,立即返回 submit_id。然后由调用方轮询结果状态,拿到 URL 后多线程下载。

### 3-Step Flow

1. **提交 (Submit):** `dreamina <command> ... --poll 0` —— `--poll 0` 表示"不阻塞等待",立即返回 submit_id
2. **轮询 (Poll):** `dreamina query_result --submit_id <ID>` —— 重复调用直到 status 返回最终 asset URL
3. **下载 (Download):** `aria2c <URL>` —— 多线程下载最终图片/视频

### 完整代码示例

```bash
# Step 1: Submit (does not block)
RESULT=$(dreamina image2image \
  --images L1.png,L2.png \
  --prompt "..." \
  --model_version 5.0 \
  --ratio 3:4 \
  --resolution_type 2k \
  --poll 0)
SUBMIT_ID=$(echo "$RESULT" | jq -r '.submit_id')

# Step 2: Poll until ready (typical 15-90s for images, 60-300s for videos)
while true; do
  STATUS=$(dreamina query_result --submit_id "$SUBMIT_ID")
  STATE=$(echo "$STATUS" | jq -r '.status')
  if [ "$STATE" = "succeeded" ]; then
    IMAGE_URL=$(echo "$STATUS" | jq -r '.image_url')
    break
  elif [ "$STATE" = "failed" ]; then
    echo "Generation failed: $(echo "$STATUS" | jq -r '.error')" >&2
    exit 1
  fi
  sleep 5
done

# Step 3: Download (multi-threaded)
aria2c "$IMAGE_URL" -o output.png
```

### 积分查询 (Credit Query)

```bash
dreamina user_credit
```

查询当前积分余额 —— 用于预算感知。但 kais-movie-agent V8 原则 §4 **"积分不设限 —— 质量优先"**,所以积分查询是观察性指标,不是触发降级的阈值。

---

## Gold-Team Fallback Path

> 来源:kais-movie-agent V8.5 SKILL.md §"图片生成默认引擎" + §工具映射 §"GPU 渲染"

V8.5 起,gold-team 容器**职责严格收口** —— 只处理 video/TTS/3D,**不再处理图片生成**。图片生成默认走 dreamina CLI,gold-team `image_draw` 仅作为即梦限流/超时降级路径。

### Tool Responsibility Matrix

| 任务类型 | 工具 | 何时 |
|---------|------|------|
| 文生图 / 图生图 / 超分 (image generation) | dreamina CLI | **DEFAULT** —— 图片生成**不走** gold-team |
| 视频生成 (video) | dreamina CLI multimodal2video / multiframe2video / frames2video | **DEFAULT** |
| TTS 语音合成 | gold-team `:8002/api/v1/tasks` (type: `tts`) | **DEFAULT** |
| 3D (image_to_3d) | gold-team `:8002/api/v1/tasks` (type: `image_to_3d`) | **DEFAULT** |
| 即梦限流/超时降级 (image degrade) | gold-team `:8002/api/v1/tasks` (type: `image_draw`, engine: `comfyui-local` / `cloud-jimeng`) | **DEGRADE ONLY** |

### Load-Bearing Statement

> **图片生成默认走 dreamina CLI,不走 gold-team。gold-team `image_draw` 是即梦限流/超时时的降级路径,不是主路径。**

### Hermes Expert Guidance

当 movie-expert(visual_executor drawer sub-step / cinematographer / character_designer)发出图片生成 prompt 时:
- ✅ 正确:prompt 路由到 dreamina CLI(text2image / image2image / image_upscale)
- ❌ 错误:prompt 路由到 gold-team `image_draw` 作为主路径
- ❌ 错误:推荐 gold-team `image_draw` 作为默认图片工具

gold-team `image_draw` **仅**作为即梦限流/超时的 DEGRADE 路径,且需在 prompt 上下文中明确标注降级触发条件。

---

## jimeng-client.js Deprecation Notice

> 来源:kais-movie-agent V8.5 SKILL.md §"V8.5 更新" §5 + §"关键文件"

> ⚠️ **DEPRECATED** — `jimeng-client.js` 在 kais-movie-agent V8.5 标记为 **@deprecated / 废弃**,已被 dreamina CLI 完全取代。`lib/jimeng-client.js` 文件保留仅做兼容参考,**不可用于新代码**。

### V8.5 Deprecation Statement

V8.5 commit `c22867d` §"V8.5 更新" §1 明确:

> dreamina CLI 取代 jimeng-client.js — 所有图片/视频生成统一使用 dreamina CLI(text2image / image2image / multimodal2video / multiframe2video / frames2video / image_upscale)

`lib/jimeng-client.js` 仍保留在仓库中,仅作历史兼容参考(用于理解 V8.4 之前的代码路径)。**禁止在新代码中 import 或调用 jimeng-client.js 的任何方法。**

### 迁移映射 (Migration Mapping)

| jimeng-client.js(废弃) | dreamina CLI(canonical) |
|------------------------|---------------------------|
| `jimengClient.text2image(prompt, opts)` | `dreamina text2image --prompt "..." --model_version 5.0 --ratio 16:9 --resolution_type 2k --poll 0` |
| `jimengClient.compositions(refs[], prompt)` | `dreamina image2image --images L1.png,L2.png --prompt "..." --poll 0` |
| `jimengClient.imageUpscale(image, ratio)` | `dreamina image_upscale --image photo.png --resolution_type 4k --poll 0` |
| `jimengClient.videoGeneration(prompt, frames)` | `dreamina multimodal2video --image L1.png --prompt "..." --poll 0`(全能参考) |
| `jimengClient.framesToVideo(first, last, prompt)` | `dreamina frames2video --first start.png --last end.png --prompt "..." --poll 0` |

### Hermes Expert Guidance

当 movie-expert(visual_executor / prompt_injector / character_designer)发出涉及 consumer pipeline 的指导时:
- ✅ 正确:指导中引用 `dreamina` CLI 命令
- ❌ 错误:指导中引用 `jimengClient.*` 方法或 `jimeng-client.js` 模块

任何 SKILL.md body 中提到 `jimengClient.*` 或 `jimeng-client.js` 的文本都是 **pre-V8.5 残留**,应在 V8.6 sync(Phase 23-26)中标记为修复候选。

---

## Refresh Cadence

本 ref **每季度复核一次**(per `_shared/` convention)。Drift triggers(任一发生即需更新本 ref):

1. **dreamina CLI 新增子命令** —— kais-movie-agent Vn+1 引入第 7 个 sub-command
2. **kais-movie-agent V-number 升级** —— V8.6 → V8.7+ 可能调整 Step 编号或审核门结构
3. **gold-team task-type 目录变化** —— 新增图片相关 task-type(将弱化"图片不走 gold-team"原则)
4. **jimeng-client.js 从 kais-movie-agent lib/ 完全删除** —— 届时"废弃"措辞可升级为"已删除"

复核动作:
- 重读 kais-movie-agent/SKILL.md 最新版本,对比 6 个 CLI 签名是否变化
- 重读 §工具映射,确认 V8.6 Step 映射是否仍准确
- 更新 `Last-verified:` 与 `verified_date:` 时间戳

---

## See Also

- [`_shared/glossary.md`](./glossary.md) —— L1-L4 canonical terms(L1 身份锚点 / L2 造型卡片 / L3 姿势包 / L4 表情标定)的 EN↔CN 词典(Phase 27 INTEGRATION-05 将新增 V8.6 术语 H3 词条)
- [`_shared/RAG-INVOCATION-PATTERN.md`](./RAG-INVOCATION-PATTERN.md) —— 专家如何调用共享 ref 的通用模式
- [`_shared/SKILL-LAYOUT.md`](./SKILL-LAYOUT.md) —— `_shared/` ref 标准文件结构与头块规范

---

## Source Citation

- **Primary:** kais-movie-agent V8.5 SKILL.md @ commit `c22867d` (2026-06-18 22:17:46 +0800) —— 6 CLI 签名 + L1-L4 策略 + async poll + gold-team 收口 + jimeng-client 废弃
- **Secondary:** kais-movie-agent V8.6 SKILL.md @ commit `e41fa68` (2026-06-18 22:56:46 +0800) —— Step 编号同步(25→13);dreamina CLI 工具地位不变
- **Tertiary:** kais-movie-agent V8.4 SKILL.md @ commit `4fb57b4` (2026-06-18 21:36:04 +0800) —— 历史 V8.4 expert 映射背景(本 ref 不直接引用,但 Phase 23-26 SKILL.md 更新会使用)

---

*Owned by Phase 22 plan 22-01 (dreamina CLI 知识基线). No parallel plan touches this file. Downstream consumers: Phase 23 visual_executor SKILL.md (VISUAL-02) + Phase 25 audio_pipeline SKILL.md (AUDIO-02) + Phase 27 _shared/v86-pipeline-mapping.md (INTEGRATION-01).*
