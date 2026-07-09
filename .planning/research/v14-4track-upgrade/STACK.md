# Stack Research — v14.0 kais-movie-pipeline 4-Track Upgrade

**Domain:** kais-movie-pipeline 4 项升级(横竖双 default 参数化 / CosyVoice 配音 / dreamina cli 深度集成 / 三层转场协作)
**Researched:** 2026-07-09
**Confidence:** HIGH for FORM/IMG (no new stack); MEDIUM for DUB (CosyVoice 版本选择 + ComfyUI node 生态实测有限); MEDIUM for TRANSITION (engine APIs 验证度高,但真实集成 cost 需 Phase 73 spike)

**Cross-repo convention (unchanged from v9.0+):**
- Plan + research artifacts → `hermes-agent/.planning/` (this file lives here)
- SKILL.md + refs + Python + ComfyUI workflow JSON → `kais-hermes-skills/skills/kais-movie-pipeline/`
- Plugins → `kais-hermes-skills/plugins/` (kais_aigc / pipeline_state / formula_library / platform_metrics / review_gates)

---

## TL;DR — 4 Tracks × Stack Additions

| Track | New Stack? | Recommendation | Integration Point (kais-hermes-skills) |
|-------|-----------|----------------|----------------------------------------|
| **FORM** | ❌ 无新栈 | 纯 Python dataclass + schema migration; `form_factor` enum | `plugins/pipeline_state/` schema; per-expert SKILL.md 条件分支; `templates/ltx_msr_*.py` 已支持 16:9 (line 446) 只需加 9:16 switch |
| **DUB** | ✅ 新 TTS 模型 | **CosyVoice 2.0-0.5B** via ComfyUI `ComfyUI_FL-CosyVoice3` node (filliptm, supports v2+v3 instruct2 mode); **NOT CosyVoice CLI 直跑** (Docker container CosyVoice 依赖灾难, `comfyui-indextts2-setup.md` 已验证); IndexTTS2 保留 fallback | `references/comfyui-cosyvoice-setup.md` (新); `templates/tts_batch.py` (重写); `SKILL.md` §P10 TTS 段 (line 456-457) |
| **IMG** | ⚠️ 极小新栈 | **复用现有 `tenacity==9.1.4`** (Hermes 已 pin) + stdlib `asyncio.Semaphore` + `concurrent.futures.ThreadPoolExecutor` (已在 `dreamina_gen_image.py` validated); vision-verify 用 **GLM-4.6V** (本机主 model, 免新增 key) | `plugins/kais_aigc/dreamina_orchestrator.py` (新文件); `templates/dreamina_gen_image.py` (升级); SKILL.md line 561/570 RHD/LHD pitfall 升级为 mandatory gate |
| **TRANSITION** | ⚠️ 新 engine clients (per-selection) | **GO:** Wan2.2 14B FLF2V (本地 ComfyUI 已具备) + Hailuo 02 / Vidu API (REST, 无 SDK); **NO-GO:** Runway Gen-3 (region/价格)、Pika (fal.ai 中转, 加 hop)、Kling (轻雀文档区域限制) | `references/transition-design.md` (新); `references/video-engine-comparison.md` (扩); `templates/wan_flf2v_batch_render.py` (新, 模式参照 `ltx_msr_batch_render.py`); `templates/hailuo_flf_client.py` (新, REST) |

---

## FORM — 横竖双 default 参数化

### 推荐: 零新栈, 纯 dataclass + schema migration

**Why no new stack:**
1. `form_factor` 是 1 字段枚举 (`landscape_16_9` / `portrait_9:16`) + per-shot `aspect_ratio` 字段。stdlib `enum.Enum` + `dataclasses` 完全够用。
2. 15 个 movie-experts 已有 SKILL.md, 改造是**文本条件分支** (把 `9:16 power points` 替换为 `{{form_factor_safe_area}}` 模板), 不需要任何新库。
3. LTX-MSR render params: `templates/ltx_msr_batch_render.py` 当前硬编码 `width=1280 height=704` (16:9)。9:16 只需 `width=704 height=1280` (或 `896×512` fast draft)。

**Python 库验证 (HIGH confidence, 本 repo 已有):**
- `pydantic==2.13.4` — schema validation for `pipeline_state.form_factor`
- `ruamel.yaml==0.18.17` — agent YAML / pipeline config 序列化

**数据资产迁移路径:**
- `pipeline_state.form_factor` 新顶层字段 (default `landscape_16_9`)
- 每个 shot 增 `aspect_ratio: "16:9" | "9:16"` 字段 (default = pipeline form_factor)
- 7 平台 variants 已有 `aspect_ratio` (`references/platform-master-slicing.md`), 兼容

**Anti-pattern (避免):**
- ❌ 引入 `pydantic-anticache` 或类似 form-factor cache lib —— per-shot form_factor 不会热切换, 无需缓存
- ❌ 引入 `pillow-simd` 做实时 aspect-ratio 校验 —— PIL 已在 stack (见 IMG), thumbnail 校验用现成 `Image.open().size`

### Sources
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/SKILL.md` line 40, 268-269, 294, 446 — form-level hardcoded references (HIGH, 本地验证)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/ltx-msr-workflow-spec.md` — `width × height 1280 × 704 (16:9) or 896 × 512 (fast draft)` (HIGH)

---

## DUB — CosyVoice default + LTX 2.3 native audio 协调

### 核心决策: **CosyVoice 2.0-0.5B** via ComfyUI 自定义节点

#### CosyVoice 版本对比 (2026-07 snapshot)

| 维度 | CosyVoice 1.0 (300M) | **CosyVoice 2.0 (0.5B)** ✅ | Fun-CosyVoice 3.0 (0.5B-2512) |
|------|---------------------|----------------------------|-------------------------------|
| Release date | 2024-07 | 2024-12 | **2025-12-15** |
| GitHub README 推荐 | ❌ (已淘汰) | ✅ (README 列第二) | ✅ (README 主推 "We strongly recommend") |
| test-zh CER (%) | 1.7+ | 1.45 | 1.21 (RL: 0.81) |
| test-zh SS (%) | ~70 | 75.7 | 78.0 (RL: 77.4) |
| 中文情感控制 | 300M-Instruct 基础 | instruct mode + 方言 | instruct2 增强 + 18+ 中文方言 |
| 模型大小 | 300M | 0.5B | 0.5B |
| ComfyUI node 成熟度 | AIFSH/CosyVoice-ComfyUI 支持 | filliptm + AIFSH 均支持 | filliptm `ComfyUI_FL-CosyVoice3` 主推 |
| 与 IndexTTS2 对比 (IndexTTS2-1.5B) | 弱 | **基本持平** (SS 75.7 vs 76.5) | **超越 IndexTTS2** (SS 78.0 vs 76.5) |
| 生态成熟度 | 老 | **大量 production 案例 + vLLM/TensorRT-LLM 部署** | 新 (7 个月), 生态仍 building |

**选 CosyVoice 2.0 (不是 3.0) 的理由 (MEDIUM confidence):**
1. **生态成熟度**: vLLM 0.9.0 / 0.11.x 都支持 CosyVoice2 (官方 README 明示), TensorRT-LLM 4x 加速方案已落地; v3 才 7 个月大, ComfyUI 节点实测反馈少
2. **ComfyUI 节点支持稳健**: `filliptm/ComfyUI_FL-CosyVoice3` 同时支持 v2/v3 (`CosyVoice2-0.5B` 模型与 `Fun-CosyVoice3-0.5B-2512` 同一节点路径), v3 出问题可秒切回 v2
3. **LTX 2.3 native audio 不竞争**: LTX 同步对白 + 唇形同步走 native path (已有路径保留); CosyVoice 接管**后期 TTS overlay** (旁白 / voiceover / emotion prosody 重场景) —— 这正是 PROJECT.md 明确的分工
4. **IndexTTS2 emotion slider 映射路径清晰**: IndexTTS2 的 `sad/calm/happy/melancholic` 8-emotion → CosyVoice 2 `instruct mode` 文本指令 (`[ sadness=0.3 ]`, `[ calm=0.2 ]`)。`filliptm/ComfyUI_FL-CosyVoice3` 的 `FLCosyVoice3Instruct2` 节点支持

**Phase 73 触发条件切 v3**: 如果 v2 中文 SS 低于 IndexTTS2 当前实测值, 直接换 v3 模型 checkpoint (同一 ComfyUI 节点), 无需重写集成代码。

#### 集成路径对比 (决定走 ComfyUI 节点, 不走 CLI/API)

| 路径 | Pros | Cons | Verdict |
|------|------|------|---------|
| **(a) ComfyUI `ComfyUI_FL-CosyVoice3` (filliptm)** ✅ | 与 LTX-MSR 共享 :8188 endpoint; 复用 `ltx_msr_batch_render.py` 的 non-blocking batch submit 模式; Canvas/Docker 隔离; 依赖管理统一 | 首次依赖安装繁琐 (参考 `comfyui-indextts2-setup.md` 9 步) | **GO** |
| (b) CosyVoice CLI 直跑 (`FunAudioLLM/CosyVoice`) | 官方原生 | Docker container CosyVoice 依赖灾难 (`comfyui-indextts2-setup.md` "Gold-team TTS" section 已警告: `permission denied on /home/kais`); 无 ComfyUI 节点协调; 独立 GPU 占用 | NO-GO |
| (c) Aliyun Model Studio CosyVoice API | REST + SDK 简单 | 网络依赖 + 按调用计费 + 不能 zero-shot clone 角色 voice preset 不在 Aliyun preset 列表 | NO-GO (voice clone 是核心需求) |

**Why ComfyUI 节点 win:**
- 与现有 IndexTTS2 节点同一 container (`comfyui-primary`), GPU 资源共享
- Non-blocking batch submission 模式与 `templates/ltx_msr_batch_render.py` 完全同构 (`/prompt` 提交 → 轮询 `/history`)
- `filliptm/ComfyUI_FL-CosyVoice3` **同时支持 CosyVoice 2 和 3** (模型 checkpoint 切换即可, 代码不改)

**Integration point (kais-hermes-skills):**
- **新 ref:** `references/comfyui-cosyvoice-setup.md` (模式完全 mirror 现有 `comfyui-indextts2-setup.md`: Node Overview + Voice Presets + Emotion 控制映射 + Working API workflow JSON + Dependency Setup + Docker fix sequence)
- **重写:** `templates/tts_batch.py` (从 `tts_zh` Qwen3-TTS → CosyVoice ComfyUI 调用)
- **SKILL.md patch:** line 456-457 `P10 voice generation` 段 CosyVoice default + IndexTTS2 fallback
- **数据资产:** `pipeline_state.episode_id.voice_preset` per-character + `tts_engine` field (`cosyvoice` / `ltx_native` / `indextts2_fallback`)

#### Voice preset 迁移路径

| IndexTTS2 preset | IndexTTS2 emotion sliders | CosyVoice 2 等效 |
|------------------|--------------------------|------------------|
| `Female_HQ` | `sad/calm/happy/melancholic` | `zero_shot` mode + 角色 ref audio 3-30s + `instruct` 文本 ("用悲伤的语气说" / "平静地") |
| `Male_HQ` | 同上 | 同上 + Male 角色 ref audio |
| `Female` / `Male` | 同上 | 同上, ref audio 质量决定 SS |

**关键差异:** CosyVoice 没有 "slider" 概念, emotion 通过 `instruct` 文本指令控制 (更自然, 但 prompt engineering 要求高)。`ComfyUI_FL-CosyVoice3` 的 `FLCosyVoice3Instruct2` 节点是首选 (支持 v2 instruct mode + v3 instruct2)。

### LTX 2.3 native audio 协调 (分工规则, 无新栈)

复用 `references/ltx-msr-workflow-spec.md` §Audio Output 已有规则:
- **LTX native:** 同步对白 + 唇形同步 (`LTXVEmptyLatentAudio` 节点填充, 基于 prompt 文本)
- **CosyVoice 后期 overlay:** 旁白 / voiceover / emotion prosody 重场景 / 需要换 voice 但不重新生成视频的场景
- **P12 mix rule:** `amix` blend native + CosyVoice (不是 `-map 1:a:0` replace, 见 ltx-msr-workflow-spec.md "CRITICAL PITFALL")

### Sources
- [FunAudioLLM/CosyVoice GitHub](https://github.com/FunAudioLLM/CosyVoice) — README + 评测表 + Roadmap (HIGH, 官方)
- [filliptm/ComfyUI_FL-CosyVoice3](https://github.com/filliptm/ComfyUI_FL-CosyVoice3) — ComfyUI 节点 (HIGH, 官方 GitHub)
- [CosyVoice2-0.5B HuggingFace](https://huggingface.co/FunAudioLLM/CosyVoice2-0.5B) — 模型卡 (HIGH)
- [Aliyun CosyVoice API docs](https://help.aliyun.com/zh/model-studio/cosyvoice-large-model-for-speech-synthesis/) — 2026-06-22 更新 (MEDIUM, 作为对比项 NO-GO 依据)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/comfyui-indextts2-setup.md` — Docker 依赖灾难记录 (HIGH, 本地)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/ltx-msr-workflow-spec.md` §Audio Output — LTX native audio 规则 (HIGH, 本地)

---

## IMG — dreamina cli 集成深度升级

### 核心决策: 复用现有 stack (`tenacity` + `asyncio.Semaphore` + `ThreadPoolExecutor`), 新增一个 production-grade orchestrator 文件

#### 推荐栈 (全部已在 Hermes repo pin 或 stdlib)

| 技术 | 版本 | 来源 | 用途 |
|------|------|------|------|
| **`tenacity`** | `9.1.4` | `hermes-agent/pyproject.toml:51` 已 pin | 装饰器式 retry + exponential backoff + jitter; `@retry` + `AsyncRetrying` + `retry_if_exception_type` |
| **`asyncio.Semaphore`** | stdlib | Python 3.11+ | 控制并发到 10-12 (已有 benchmark 数据) |
| **`concurrent.futures.ThreadPoolExecutor`** | stdlib | Python 3.11+ | `dreamina_gen_image.py` 已使用 (`max_workers=4` 默认, 可调) |
| **`httpx`** | `0.28.1` | `hermes-agent/pyproject.toml:35` 已 pin | 下载 dreamina 返回的 byteimg.com URL (取代 aria2c, 见 SKILL.md line 441-460 陷阱) |
| **`Pillow` (PIL)** | 已 installed | 已在 stack | brightness check (过暗检测, RHD/LHD 后的 vision-verify 前置) |
| **`pydantic`** | `2.13.4` | 已 pin | SLA tracking dataclass (`DreaminaTaskMetrics` schema) |

**Anti-pattern (避免引入):**
- ❌ `backoff` library —— 与 `tenacity` 功能重叠, Hermes 已用 tenacity, 不要再装 backoff
- ❌ `aiolimiter` —— `asyncio.Semaphore` 完全够用, dreamina 不是 token bucket 限流 (是 server-side concurrency cap)
- ❌ `celery` / `rq` —— 任务持久化不需要, Pipeline state plugin 已经是 persistence layer
- ❌ 重写 `subprocess.Popen` 调用为 dreamina Python SDK —— **dreamina 没有 Python SDK**, 只有 CLI (`/home/kai/.local/bin/dreamina`), `subprocess.Popen` 是唯一方式

#### Vision-verify mandatory gate

**推荐模型: GLM-4.6V**

| 维度 | GLM-4.6V ✅ | Qwen-VL-Max | Local (ComfyUI) |
|------|-----------|-------------|----------------|
| 本机主 model | ✅ (MEMORY.md `feedback-glm-5-2-only.md` 限制; 但 GLM-4.6V 是 vision, **不是 model switch**, 是 vision tool call) | ❌ (切 Qwen 是 model 切换) | ❌ (本地无 VL model) |
| API 已 wired | ✅ (zai provider profile 已存在) | ❌ | N/A |
| 中文理解 | ✅ (本机训练中文场景强) | ✅ | ❌ |
| 128K context | ✅ | 部分 | N/A |
| 多图对比 | ✅ | 部分 | ❌ |
| 成本 | 已付 | 需新 key | 免费 (GPU 时间) |

**Why GLM-4.6V (不是 GLM-5.2 vision):**
- MEMORY.md `feedback-glm-5-2-only.md` 限制的是主 model 用于 chat / orchestration; vision-verify 是**vision tool call**, 不是 model switch
- GLM-4.6V 是专门训练的 vision-language MoE, 在 richly formatted page / 场景理解上 SoTA
- GLM-5.2 vision 能力尚未在 docs.z.ai 文档化为本机可用 vision API

**Vision-verify gate 流程 (新 mandatory gate, SKILL.md line 561 升级):**
```
dreamina 生成图 → PIL brightness check (过暗) → GLM-4.6V vision_analyze ("Is this LHD or RHD? Is baby in rear seat?") →
  ✅ pass → upload 到 ComfyUI :8188 /upload/image
  ❌ fail → log + 自动 retry dreamina (改 prompt 加 "view from passenger seat, driver on LEFT") → 最多 3 次 → 失败 raise
```

**Integration point:**
- **新文件:** `plugins/kais_aigc/dreamina_orchestrator.py` —— production-grade manager class `DreaminaOrchestrator`
  - `batch_submit(prompts: list[dict], max_concurrency: int = 10)` → 返回 `list[DreaminaTaskResult]`
  - 内部: `asyncio.Semaphore` + `tenacity.retry` + `httpx.AsyncClient` 下载
  - SLA tracking: `DreaminaTaskMetrics(submit_id, latency_ms, success, retries, brightness, vision_verified)`
- **升级:** `templates/dreamina_gen_image.py` —— 从 standalone script 改为 import orchestrator
- **SKILL.md patch:** line 561 RHD/LHD pitfall → mandatory gate; line 619 manual-gen backfill → orchestrator 自动写 pipeline_state

#### RHD/LHD bug 系统性缓解

**无新 lib; 是 prompt 模板 + verify-retry 循环:**

1. **Prompt engineering pattern (无新 lib):**
   ```
   # 坏: "left-hand drive" (dreamina 不理解标签)
   # 好: "view from passenger seat looking toward driver, driver sits on LEFT side, steering wheel on the left"
   ```
2. **Verify-retry loop (用 tenacity):**
   ```python
   @retry(stop=stop_after_attempt(3), retry=retry_if_result(lambda r: not r.lhd_confirmed))
   async def generate_lhd_with_verify(prompt: str) -> VisionResult:
       sid = await submit_dreamina(prompt)
       result = await poll_until_done(sid)
       download_with_httpx(result.url, path)
       return await glm46v_vision_verify(path, "Is this left-hand drive?")
   ```
3. **结构化 prompt helper (新, 纯 Python):** `plugins/kais_aigc/dreamina_prompts.py` —— `build_lhd_prompt()`, `build_rhd_prompt()`, `build_rear_facing_prompt()` 等模板函数

### Sources
- `/data/workspace/hermes-agent/pyproject.toml:51` — `tenacity==9.1.4` (HIGH, 本地)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/templates/dreamina_gen_image.py` — 现有 batch 模式 (HIGH, 本地)
- `/data/workspace/kais-hermes-skills/skills/kais-creative/kais-jimeng-cli/SKILL.md` §并行生成模式 — 12 parallel 100% validated (HIGH, 本地 benchmark)
- `/data/workspace/kais-hermes-skills/plugins/kais_aigc/jimeng.py` — 现有 retry/backoff 模式 (HIGH, 本地)
- [GLM-4.6V docs.z.ai](https://docs.z.ai/guides/vlm/glm-4.6v) — 128K + SoTA vision (HIGH, 官方)
- [tenacity async support docs](https://tessl.io/registry/tessl/pypi-tenacity/9.1.0/files/docs/async-support.md) — AsyncRetrying (HIGH, 官方)
- [jd/tenacity GitHub](https://github.com/jd/tenacity) — 9.1.4 release (HIGH, 官方)

---

## TRANSITION — 创作+数据+生成三层协作

### Step A 验证: **LTX-MSR first/last frame capability = NO**

LTX-MSR 的 ICLoRA conditioning (41 帧) 是 **identity preservation** (character + scene + vehicle 多 ref 注入), **不是** first/last frame transition conditioning。`references/ltx-msr-workflow-spec.md` 明确:
- `LiconMSR` 节点输入是 `ref1, ref2, ref3, ref4 + background image`
- `LTXAddVideoICLoRAGuide` 是把 ref 注入到 conditioning frames (MSR_FC=41 帧)
- 输出是把 ref identity 混合到生成视频中, **不是** first frame → last frame 的过渡生成

**Conclusion:** LTX-MSR **不能**做 first/last frame transition。需要其他 engine。

### Step B 引擎 Survey (2026-07 snapshot)

| Engine | First+Last Frame | API Access | Python Client | 中文内容 | Batch | 成本 | VRAM | Verdict |
|--------|------------------|-----------|---------------|---------|-------|------|------|---------|
| **Wan2.2 14B FLF2V** | ✅ Native (`WanFirstLastFrameToVideo` 节点) | ComfyUI 本地 | ✅ ComfyUI :8188 (已 wired) | ✅ Alibaba 训练含中文 | ✅ (non-blocking 提交, 同 LTX-MSR) | 免费 (GPU 时间) | ~21GB (同 Wan2.2-I2V) | **GO** ✅ |
| **Hailuo 02 (MiniMax)** | ✅ First + optional Last frame | REST API | ⚠️ 无官方 Python SDK, REST + httpx | ✅ MiniMax 国内厂商 | ✅ (task ID 轮询) | $0.056/秒 | 云端 | **GO** ✅ (云 backup) |
| **Vidu (Alibaba)** | ✅ Keyframe-to-Video | REST API (Aliyun Model Studio) | ⚠️ 阿里 SDK 通配, vendor-specific | ✅ Alibaba | ✅ | 按 token | 云端 | **GO** ✅ (云 backup) |
| Runway Gen-3 Alpha | ✅ position=first/last | REST API + [runwayml/sdk-python](https://github.com/runwayml/sdk-python) 官方 | ✅ 官方 SDK | ⚠️ 英文优化, 中文内容弱 | ✅ | ~$0.05/秒 | 云端 | **NO-GO** (中文内容弱 + 区域访问 + 美元计费) |
| Pika 2.2 Pikaframes | ✅ 2-5 keyframes | fal.ai 中转 | ✅ `fal-client` Python | ⚠️ 英文优化 | ✅ | fal 计费 | 云端 | **NO-GO** (fal.ai 中转加 hop + 中文弱 + 多 hop 调试复杂) |
| Kling 2.5 Turbo Pro | ✅ First+Last Frame | 轻雀文档 (qingque) 区域受限 | ⚠️ TechWithTy/kling 社区 SDK (非官方) | ✅ Kuaishou 国内厂商 | ✅ | 按 token | 云端 | **NO-GO** (轻雀文档 docs 在 CN 区域外打不开, SDK 非官方 + API key 申请流程不透明) |
| Dreamina/Jimeng video (seedance) | ✅ `frames2video` (SKILL.md 已有 line 126-135) | ✅ CLI `/home/kai/.local/bin/dreamina` | ✅ 本地 CLI | ✅✅ 中文最优 | ✅ (并行 validated) | Maestro 免费 | 云端 | **NO-GO** (默认关闭 per Kai directive 2026-07-03; 可在 Step D fallback 时显式 opt-in `allow_video=True` 试用) |
| HunyuanVideo variants | ⚠️ HunyuanImageToVideo 单 I2V; 无原生 first+last | ComfyUI 本地 | ✅ | ⚠️ Tencent 训练 | ✅ | 免费 | ~30GB+ | **NO-GO** (无原生 first+last frame 节点; VRAM 需求高) |

#### Selection Rule (per-transition routing, 扩展 `video-engine-comparison.md` §Selection Rules)

```
IF transition 需要 first+last frame 一致性 (identity match ~98%) →
    IF 本地 GPU 可用 + 单 GPU VRAM ≥ 21GB → Wan2.2 14B FLF2V (ComfyUI :8188)
    ELSE → Hailuo 02 i2v Pro API (云, $0.056/sec)
IF transition 需要云端 + 中文内容 + 低延迟 → Vidu keyframe-to-video
IF 所有生成路径都不合适 → editor 后期 fallback (ffmpeg dissolve/wipe/fade + match-cut manual)
IF 用户显式要求 jimeng video → dreamina frames2video (opt-in)
NEVER → Runway/Pika/Kling (中文内容弱 + 集成成本高 + 无 batch)
NEVER → HunyuanVideo (无原生 first+last frame)
```

### Step C 推荐栈

#### 1. Wan2.2 14B FLF2V (主引擎, 本地 ComfyUI)

**Workflow JSON 来源:**
- 官方: [comfy.org Wan2.2 14B FLF2V workflow](https://comfy.org/workflows/video_wan2_2_14B_flf2v-7016f027bcf1/) (HIGH, 官方)
- 社区: [GegenDenTag/comfyui-wan-video-2.2-t2v-first-last-frame-workflow](https://huggingface.co/GegenDenTag/comfyui-wan-video-2.2-t2v-first-last-frame-workflow) — 含 `First-Last-Frame.json` ready-to-use (HIGH, HuggingFace)
- 节点: `WanFirstLastFrameToVideo` (原生 ComfyUI Wan2.2 集成, 非第三方)

**集成路径:**
- **新文件:** `templates/wan_flf2v_batch_render.py` —— 完全 mirror `ltx_msr_batch_render.py` 结构:
  - `build_flf_workflow(first_frame, last_frame, prompt, duration)` → JSON
  - `submit_all(shots)` → list of prompt_ids
  - `poll_history(prompt_ids)` → list of outputs
  - 下载 + 校验 + trim
- **新 ref:** `references/wan-flf2v-workflow-spec.md` —— 完全 mirror `ltx-msr-workflow-spec.md` 结构
- **依赖:** 复用 `comfyui-primary` Docker container (已 Wan2.2-I2V validated per `video-engine-comparison.md`)

**Cost:** ~21GB VRAM (RTX 3090 24GB OK, 同 Wan2.2-I2V); 每 5s 视频 ~4 min (参考 `video-engine-comparison.md` Wan2.2-Animate benchmark)

#### 2. Hailuo 02 i2v Pro (云 backup)

**集成路径:**
- **新文件:** `templates/hailuo_flf_client.py` —— REST client (无官方 SDK, 直接 httpx)
  - `submit(first_frame_url, last_frame_url, prompt) → task_id`
  - `poll(task_id) → video_url`
  - `download(video_url) → local_path`
- **新 ref:** `references/hailuo-flf-setup.md` —— API key 配置 + pricing 摘要
- **依赖:** `httpx==0.28.1` (已 pin); 无新 lib

**API endpoint:** [platform.minimax.io/docs/guides/video-generation](https://platform.minimax.io/docs/guides/video-generation) (HIGH, 官方)

**Cost:** $0.056/sec generated video

#### 3. Vidu keyframe-to-video (中文内容云 backup)

**集成路径:**
- **新文件:** `templates/vidu_flf_client.py` —— 同 Hailuo 模式 (REST + httpx)
- **新 ref:** `references/vidu-flf-setup.md`
- **API endpoint:** [help.aliyun.com Vidu keyframe-to-video](https://help.aliyun.com/en/model-studio/vidu-keyframe-to-video-api-reference) (HIGH, 官方 Aliyun)

**Why 同时支持 Hailuo + Vidu:** 中文内容场景两家互补 (MiniMax vs Alibaba 训练数据不同); 如果一家 API 故障/限流, 秒切另一家; 成本结构两家相近。

### Step D Fallback path (editor 后期)

如果所有 generation 不合适, 退到 editor 后期 (已有路径):
- `references/p12-composition-workflow.md` ffmpeg dissolve/wipe/fade 已有
- match-cut via manual cut (editor workflow step 7 已有)

**无新栈**, 纯复用 ffmpeg subprocess (已在 stack)

### 创作层 + 数据层 (无新栈)

**创作层 (cinematographer E-Konte Layer 5 schema 扩展):**
- `transition_method: montage_cut / match_cut_via_shared_object / match_cut_via_shared_landscape / motion_vector_match / color_match / none` — enum
- `visual_hook: str` — 具体连接元素
- `camera_continuity: pan_to / zoom_to / dolly_through / whip_pan / match_cut_on_motion / none` — enum

纯 pydantic schema 扩展, 无新 lib。

**数据层 (first-class asset `transition_design.json`):**
- per-shot transition design + cross-shot chain
- 扩展 `next_shot_link` 从 string id → structured object

纯 pydantic dataclass, 无新 lib。

**Integration point:**
- **新 ref:** `references/transition-design.md` — creative taxonomy + data schema + execution paths
- **更新:** `references/video-engine-comparison.md` — 新增 transition-capable engine 矩阵 + per-transition routing rules

### Sources
- [comfy.org Wan2.2 14B FLF2V workflow](https://comfy.org/workflows/video_wan2_2_14B_flf2v-7016f027bcf1/) — 官方 ComfyUI workflow (HIGH)
- [GegenDenTag HuggingFace Wan2.2 FLF workflow JSON](https://huggingface.co/GegenDenTag/comfyui-wan-video-2.2-t2v-first-last-frame-workflow) — ready-to-use JSON (HIGH)
- [ComfyUI Wan2.1 FLF2V native docs](https://docs.comfy.org/tutorials/video/wan/wan-flf) — 98% 匹配率 (HIGH, 官方)
- [MiniMax Hailuo 02 i2v Pro](https://www.atlascloud.ai/models/minimax/hailuo-02/i2v-pro) — $0.056/sec pricing (HIGH)
- [MiniMax platform video-generation docs](https://platform.minimax.io/docs/guides/video-generation) — First-and-Last-Frame API (HIGH, 官方)
- [Aliyun Vidu keyframe-to-video](https://help.aliyun.com/en/model-studio/vidu-keyframe-to-video-api-reference) — REST API (HIGH, 官方)
- [Aliyun Wan 2.2 first-last-frame API](https://www.alibabacloud.com/help/en/model-studio/legacy-image-to-video-by-first-and-last-frame-api-reference) — 备选云端 (HIGH, 官方)
- [Pika 2.2 Pikaframes (fal.ai)](https://fal.ai/models/fal-ai/pika/v2.2/pikaframes/api) — 2-5 keyframes (HIGH, fal.ai 官方)
- [RunwayML sdk-python](https://github.com/runwayml/sdk-python) — 官方 Python SDK (HIGH)
- [Runway Keyframes on Gen-3](https://help.runwayml.com/hc/en-us/articles/34170748696595-Creating-with-Keyframes-on-Gen-3) — position=first/last (HIGH, 官方)
- [ImagineArt Kling 2.5 Turbo Pro First+Last Frame](https://www.imagine.art/features/kling-2-5-turbo-pro-first-and-last-frame) — 功能确认 (MEDIUM, vendor page)
- [轻雀 Kling 官方 docs](https://docs.qingque.cn/d/home/eZQCQxBrX8eeImjK6Ddz5iOi5) — 区域访问受限 (MEDIUM, CN-only)
- `/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/references/video-engine-comparison.md` — 现有 Selection Rules 模式 (HIGH, 本地)

---

## Alternatives Considered

| Category | Recommended | Alternative | When to Use Alternative |
|----------|-------------|-------------|-------------------------|
| TTS engine | CosyVoice 2.0 via ComfyUI | IndexTTS2 (current default) | 当 CosyVoice 依赖安装失败 or voice clone 质量 < IndexTTS2 (保留 fallback path) |
| TTS engine | CosyVoice 2.0 | CosyVoice 3.0 (Fun-CosyVoice3-0.5B-2512) | 如果 v2 中文 SS 实测 < IndexTTS2, 直接切 v3 checkpoint (同节点路径) |
| TTS 集成路径 | ComfyUI 自定义节点 | CosyVoice CLI 直跑 | **永远不要** (Docker 依赖灾难已验证) |
| TTS 集成路径 | ComfyUI 自定义节点 | Aliyun Model Studio API | 如果未来需要 scale + 不在乎 voice clone quality (目前 NO) |
| Vision-verify model | GLM-4.6V | Qwen-VL-Max | 如果 GLM-4.6V 中文场景理解不足 (目前 docs.z.ai 称 SoTA) |
| Vision-verify model | GLM-4.6V | 本地 ComfyUI VL | 永远不要 (无 production-ready 本地 VL) |
| Retry / orchestration | tenacity + asyncio.Semaphore | backoff library | 永远不要 (功能重叠, Hermes 已 pin tenacity) |
| First/last frame engine (主) | Wan2.2 14B FLF2V (本地) | Hailuo 02 API | 当本地 GPU 不可用 or VRAM < 21GB |
| First/last frame engine (云) | Hailuo 02 + Vidu (双 backup) | 单家 | 当其中一家 API 故障/限流 (两家互补) |
| First/last frame engine (NO-GO) | — | Runway / Pika / Kling / HunyuanVideo | 中文内容弱 + 集成 cost 高 + 无 batch 优势 |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `backoff` library | 与 `tenacity` 功能重叠, Hermes 已 pin tenacity; 混用造成两套 retry 模式 | `tenacity==9.1.4` |
| `aiolimiter` | dreamina 是 server-side concurrency cap, 不是 token bucket; `asyncio.Semaphore` 完全够 | `asyncio.Semaphore` (stdlib) |
| `celery` / `rq` | 任务持久化 layer 已有 `pipeline_state` plugin; 新增 task queue 重复造轮子 | `pipeline_state.episode_id.tasks[]` |
| CosyVoice CLI 直跑 (Docker container) | 已有 IndexTTS2 在 comfyui-primary Docker 9 步依赖灾难记录; CosyVoice 同等复杂 | ComfyUI `ComfyUI_FL-CosyVoice3` 节点 (共享 container) |
| `aria2c` 下载 dreamina image | SKILL.md line 441-460 已警告: 多连接分片下载 byteimg.com 偶发 broken data stream | `curl -sL -o file <url>` 或 `httpx` |
| Runway Gen-3 / Pika / Kling | 中文内容弱 + 集成 cost 高 + 无 batch 优势 + 区域访问限制 | Wan2.2 FLF2V / Hailuo / Vidu |
| HunyuanVideo first-last-frame | 无原生 first+last frame 节点 + VRAM 30GB+ 需求过高 | Wan2.2 14B FLF2V |
| `Pillow-simd` 做 form_factor cache | per-shot form_factor 不会热切换, 无需缓存 | stdlib `enum.Enum` |
| Local FLUX for image gen | Kai directive 2026-06-27 明确禁止 (SKILL.md line 519) | dreamina CLI |

---

## Stack Patterns by Variant

**If form_factor = landscape_16_9 (default):**
- LTX-MSR render: `width=1280 height=704`
- dreamina image: `--ratio=16:9`
- 平台切片: 7 variants 全部基于 16:9 master

**If form_factor = portrait_9:16:**
- LTX-MSR render: `width=704 height=1280` (MSR_FC=41 不变)
- dreamina image: `--ratio=9:16`
- 平台切片: 7 variants 基于竖屏 master (抖音竖屏 / 快手竖屏 / 小红书竖屏 / 视频号横屏 special case)

**If TTS 场景 = 同步对白 + 唇形同步:**
- 走 LTX 2.3 native audio (`LTXVEmptyLatentAudio` 节点填充, prompt 含 dialogue)
- **不调** CosyVoice (浪费 native audio 能力 + 唇形不同步)

**If TTS 场景 = 后期旁白 / voiceover / emotion prosody:**
- 走 CosyVoice 后期 overlay
- P12 composition 用 `amix` blend native + CosyVoice (不是 replace)

**If transition 需要 first/last frame identity 一致:**
- 路由到 Wan2.2 FLF2V (本地 GPU OK) or Hailuo 02 API (云端)
- **不调** LTX-MSR (ICLoRA 是 identity preservation, 不是 first/last transition)

**If transition 可用 editor 后期 dissolve/wipe/fade:**
- 不需要生成层, 直接 ffmpeg (editor workflow step 7 已有)

**If vision-verify 失败 3 次:**
- raise + log, prompt operator 手动检查 (不做无限 retry, 避免 quota 浪费)

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `tenacity==9.1.4` | Python 3.11+ | Hermes 已 pin, 无冲突 |
| `httpx==0.28.1` | Python 3.11+ | Hermes 已 pin, async mode 支持 |
| CosyVoice2-0.5B | ComfyUI `ComfyUI_FL-CosyVoice3` (filliptm) | 同节点支持 v3, 可秒切 |
| CosyVoice2-0.5B | vLLM 0.9.0 / 0.11.x | 高并发场景 (目前我们用 ComfyUI, 不走 vLLM) |
| Wan2.2 14B FLF2V | ComfyUI Wan2.2 集成 (原生) | 需要 fp8 checkpoint (RTX 3090 24GB OK) |
| GLM-4.6V | zai provider profile (已 wired) | 无新 key 需求 |

---

## Installation

**核心: 零新 Python 包安装** (全部已 pin 在 hermes-agent `pyproject.toml`)

**Docker container 层 (一次性, 模式同 IndexTTS2):**
```bash
# ComfyUI CosyVoice 节点依赖 (模式同 comfyui-indextts2-setup.md)
docker exec comfyui-primary bash -c "
cd /root/ComfyUI/custom_nodes && \
git clone https://github.com/filliptm/ComfyUI_FL-CosyVoice3.git && \
cd ComfyUI_FL-CosyVoice3 && \
pip3.13 install -r requirements.txt --proxy http://172.17.0.1:7890
"

# CosyVoice 2 模型下载 (模式同 IndexTTS2 模型下载)
docker exec comfyui-primary python3.13 -c "
from modelscope import snapshot_download
snapshot_download('iic/CosyVoice2-0.5B', local_dir='/root/ComfyUI/models/CosyVoice2-0.5B')
"
docker restart comfyui-primary
```

**Wan2.2 FLF2V 工作流加载 (已具备):**
- ComfyUI Wan2.2 集成原生节点 `WanFirstLastFrameToVideo` 已在 comfyui-primary container
- 工作流 JSON 从 [GegenDenTag HuggingFace](https://huggingface.co/GegenDenTag/comfyui-wan-video-2.2-t2v-first-last-frame-workflow) 下载到 `templates/wan_flf2v_workflow.json`

**云端 API key (可选, 云 backup):**
```bash
# Hailuo 02 (MiniMax)
export MINIMAX_API_KEY=xxx

# Vidu (Aliyun Model Studio)
export VIDU_API_KEY=xxx
```

---

## 研究缺口 (Phase 73+ 时再补)

- **CosyVoice 2 ComfyUI 节点中文 emotion 实测数据**: 目前只有 GitHub README 表 (test-zh SS 75.7%), 没有 ComfyUI 节点端到端中文短剧对白 benchmark。Phase 72/73 需要 A/B 对比 IndexTTS2 与 CosyVoice 2 在 kais-movie-pipeline 实际场景的 SS + emotion 自然度
- **Wan2.2 FLF2V 在中文场景的 prompt-following**: `video-engine-comparison.md` 表显示 Wan2.1/2.2 prompt-following 为 "Moderate", FLF2V mode 在中文复杂动作描述下的表现未实测
- **Hailuo 02 / Vidu API pricing 在 production batch 的真实成本**: 目前只有 $0.056/sec 标价, 没有 30-shot batch 的真实月度成本数据
- **GLM-4.6V vision-verify LHD/RHD 准确率**: docs.z.ai 称 SoTA, 但 dreamina 生成的汽车内饰图 (部分 RHD 部分镜像) 的实测准确率未验证

---

*Stack research for: v14.0 kais-movie-pipeline 4-track upgrade (FORM / DUB / IMG / TRANSITION)*
*Researched: 2026-07-09*
*Cross-repo: hermes-agent/.planning/ (this file) + kais-hermes-skills/ (code)*
